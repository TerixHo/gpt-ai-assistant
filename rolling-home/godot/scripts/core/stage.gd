class_name Stage
extends Node3D
## 一個關卡的完整執行期：建場景、讀輸入、計時、尺寸門檻、結算。
## 由 Main 建立並呼叫 setup(stage_id)，結束時發出 finished(result)。

signal finished(result: Dictionary)
signal gate_opened(gate_id: String, diameter_cm: float)
signal quit_requested
signal restart_requested

const INTRO_TIME := 2.2
const OUTRO_TIME := 2.8

var stage_id := ""
var stage_def: Dictionary = {}
var katamari: Katamari
var cam: KatamariCamera
var pusher: Pusher
var charge_fx: ChargeFx
var hud: Hud
var items_root: Node3D
var time_total := 180.0
var time_left := 180.0
var goal := 10.0
var state := "intro"
var time_to_goal := -1.0
## 經過時間（秒）
var elapsed := 0.0
## 不限時間模式：不倒數，玩家從暫停選單結束這一局
var no_limit := false
var spawned_count := 0
## 自動測試與展示用：關閉開場倒數
var skip_intro := false
## 標題畫面背景的示範：自動駕駛在玩，不顯示介面、不計時、場景靜音
var demo := false

var _state_timer := 0.0
var _gates: Array[Dictionary] = []
var _areas: Array = []
var _current_area := ""
var _area_timer := 0.0
var _start_pos := Vector3.ZERO
var _start_yaw := 0.0
var _last_tick := -1
var _sun: DirectionalLight3D
var _env: Environment
## 場景配置檔的 env 區塊：天空顏色、霧
var _env_def: Dictionary = {}
## 卡住時「回到中間」的位置與方向
var _rescue_pos := Vector3.ZERO
var _rescue_yaw := 0.0
## 卡住偵測：一段時間內想動卻幾乎沒移動
var _stuck_timer := 0.0
var _stuck_anchor := Vector3.ZERO
var _stuck_check := 0.0
var _rescue_shown := false
## 成長歡呼：下一個里程碑（公分）與冷卻
var _next_milestone := 0.0
var _cheer_cooldown := 0.0


func setup(id: String) -> void:
	stage_id = id
	stage_def = Data.get_stage(id)


func _ready() -> void:
	name = "Stage"
	# 3D 場景開啟物理插值（螢幕更新率和物理更新率不同時畫面才順）；標題等介面另外關閉
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_ON
	if stage_def.is_empty():
		push_error("關卡設定不存在：%s" % stage_id)
		return
	time_total = float(stage_def.get("time_sec", 180.0))
	time_left = time_total
	no_limit = demo or bool(Game.settings.get("no_time_limit", false))
	if demo:
		Sfx.world_muted = true
	goal = float(stage_def.get("goal_cm", 10.0))
	var level := Data.get_level(stage_def.get("level", ""))
	_env_def = level.get("env", {})
	_build_environment()

	items_root = Node3D.new()
	items_root.name = "Items"
	add_child(items_root)
	var built := LevelBuilder.build(level, self, items_root, stage_def.get("zones", []), int(stage_def.get("seed", 1)))
	spawned_count = built["spawned"]
	_areas = built["areas"]
	var gate_overrides: Dictionary = stage_def.get("gates", {})
	var start_size := float(stage_def.get("start_cm", 5.0))
	for g in built["gates"]:
		if gate_overrides.has(g["id"]):
			g["open_at"] = float(gate_overrides[g["id"]])
		# 起始尺寸就已經達標的門，一開始就打開（不播訊息）
		if float(g["open_at"]) <= start_size:
			g["open"] = true
			var body: StaticBody3D = g["body"]
			body.collision_layer = 0
			body.position += g["slide"] as Vector3
		_gates.append(g)

	var start: Dictionary = stage_def.get("start", built["start"])
	_start_pos = KMath.vec3(start.get("pos"), Vector3(100, 10, 100))
	_start_yaw = deg_to_rad(float(start.get("yaw_deg", 0.0)))
	var rescue: Dictionary = stage_def.get("rescue", built["rescue"])
	_rescue_pos = KMath.vec3(rescue.get("pos"), _start_pos)
	_rescue_yaw = deg_to_rad(float(rescue.get("yaw_deg", rad_to_deg(_start_yaw))))

	katamari = Katamari.new()
	katamari.start_diameter_cm = float(stage_def.get("start_cm", 5.0))
	var tuning: Dictionary = stage_def.get("tuning", {})
	for key in tuning:
		katamari.set(key, tuning[key])
	katamari.items_parent = items_root
	add_child(katamari)
	katamari.global_position = _start_pos + Vector3.UP * katamari.radius()
	katamari.collected.connect(_on_collected)
	katamari.bumped.connect(_on_bumped)
	katamari.dashed.connect(func(): Sfx.play("dash"))
	katamari.jumped.connect(func(): Sfx.play_varied("jump", clampf(1.25 - log(katamari.diameter) / 10.0, 0.8, 1.25), 0.05))
	katamari.double_jumped.connect(_on_double_jumped)
	katamari.crashed.connect(_on_crashed)
	katamari.charge_level_changed.connect(_on_charge_level)
	katamari.launched.connect(_on_launched)

	cam = KatamariCamera.new()
	add_child(cam)
	cam.target = katamari
	cam.view_changed.connect(func(label: String):
		hud.toast(label)
		Sfx.play("ui"))
	cam.yaw = _start_yaw
	cam.snap()

	pusher = Pusher.new()
	pusher.katamari = katamari
	pusher.cam = cam
	add_child(pusher)

	charge_fx = ChargeFx.new()
	charge_fx.katamari = katamari
	add_child(charge_fx)

	hud = Hud.new()
	hud.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	hud.with_touch = not demo
	add_child(hud)
	hud.visible = not demo
	hud.resume_requested.connect(func(): _set_paused(false))
	hud.restart_requested.connect(func():
		_set_paused(false)
		restart_requested.emit())
	hud.finish_requested.connect(func():
		_set_paused(false)
		if state == "playing":
			end_now())
	hud.quit_requested.connect(func():
		_set_paused(false)
		quit_requested.emit())
	hud.rescue_requested.connect(func():
		if get_tree().paused:
			_set_paused(false)
		rescue())

	if not demo:
		var watcher := Node.new()
		watcher.name = "PauseWatcher"
		watcher.process_mode = Node.PROCESS_MODE_ALWAYS
		watcher.set_script(preload("res://scripts/core/pause_watcher.gd"))
		add_child(watcher)
		watcher.toggled.connect(func():
			if state == "playing" or get_tree().paused:
				_set_paused(not get_tree().paused))

	_next_milestone = next_milestone(katamari.diameter)
	katamari.input_enabled = false
	if skip_intro:
		_begin_play()
	else:
		hud.banner(stage_def.get("intro", "預備…"), INTRO_TIME - 0.6)
	_update_hud()
	if not demo:
		Sfx.play_music(stage_def.get("music", "home"))
	# 場景剛擺好，所有東西都是「瞬間就位」，不要從原點補間過來
	reset_physics_interpolation()


func _build_environment() -> void:
	var env := Environment.new()
	_env = env
	env.background_mode = Environment.BG_COLOR
	env.background_color = KMath.color(_env_def.get("sky", stage_def.get("sky", "#bfe6ff")))
	# 霧：濃度隨塊球直徑調整（fog_per_d ÷ 直徑），大場景遠處自然淡出
	if float(_env_def.get("fog_per_d", 0.0)) > 0.0:
		env.fog_enabled = true
		env.fog_light_color = KMath.color(_env_def.get("fog_color", "#dfefff"))
		env.fog_density = float(_env_def["fog_per_d"]) / maxf(float(stage_def.get("start_cm", 5.0)), 1.0)
		env.fog_sky_affect = 0.0
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.97, 0.97, 1.0)
	env.ambient_light_energy = 0.58
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.rotation_degrees = Vector3(-68, 32, 0)
	_sun.light_energy = 0.48
	_sun.light_color = Color(1.0, 0.97, 0.93)
	_sun.shadow_enabled = true
	_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	_sun.directional_shadow_max_distance = 300.0
	_sun.shadow_bias = 0.12
	_sun.shadow_normal_bias = 2.5
	add_child(_sun)


func _begin_play() -> void:
	state = "playing"
	katamari.input_enabled = true
	if not skip_intro:
		hud.banner("開始！", 0.7, Color(1.0, 0.9, 0.4))


func _physics_process(delta: float) -> void:
	if katamari == null:
		return
	match state:
		"intro":
			_state_timer += delta
			if _state_timer >= INTRO_TIME:
				_begin_play()
		"playing":
			_play_step(delta)
		"ended":
			katamari.set_drive(Vector2.ZERO, cam.yaw)
			if katamari.is_charging():
				katamari.charge_cancel()
				Sfx.stop_loop()
			_state_timer += delta
			if _state_timer >= OUTRO_TIME and _state_timer - delta < OUTRO_TIME:
				finished.emit(build_result())
	_update_hud()


func _play_step(delta: float) -> void:
	var d := Controls.read(delta)
	cam.apply_drive(d, delta)
	if cam.free_look:
		# 第一人稱環視時球停下來，WASD 用來看四周
		katamari.set_drive(Vector2.ZERO, cam.yaw)
		katamari.release_jump()
		if katamari.is_charging():
			katamari.charge_cancel()
			Sfx.stop_loop()
	else:
		katamari.set_drive(d.move, cam.yaw)
		# 集氣：按住開始，放開衝出去
		if d.charge and not katamari.is_charging():
			if katamari.charge_begin():
				Sfx.start_loop("charge_loop", 0.8)
		elif not d.charge and katamari.is_charging():
			katamari.charge_release()
		if katamari.is_charging():
			Sfx.set_loop_pitch(0.8 + 0.35 * katamari.charge_time())
		if d.dash and not katamari.is_charging():
			katamari.dash()
		if d.jump:
			katamari.jump()
		if d.rescue:
			rescue()
	_check_stuck(delta, d)
	_check_milestone(delta)
	elapsed += delta
	if not no_limit:
		time_left -= delta
	_check_gates()
	_check_area(delta)
	if katamari.global_position.y < _fall_limit():
		rescue()
	if time_to_goal < 0.0 and katamari.diameter >= goal:
		time_to_goal = elapsed
		hud.banner("成功了！繼續滾，可以變得更大喔！", 1.8, Color(0.55, 1.0, 0.6))
		Sfx.play("goal")
	if no_limit:
		return
	var sec := int(ceil(time_left))
	if sec <= 10 and sec != _last_tick and sec > 0:
		_last_tick = sec
		Sfx.play("tick", 1.0 + (10 - sec) * 0.04)
	if time_left <= 0.0:
		time_left = 0.0
		end_now()


## 結束這一局（時間到，或不限時間模式下玩家選擇結束）。
func end_now() -> void:
	state = "ended"
	_state_timer = 0.0
	katamari.input_enabled = false
	var ok := katamari.diameter >= goal
	hud.banner("時間到！" if not no_limit else "完成！", OUTRO_TIME - 0.4, Color(1.0, 0.9, 0.4) if ok else Color(1.0, 0.75, 0.5))
	Sfx.play("timeup")


## 掉出場景的高度：比最低的地板再低一段（大場景地板很厚）
func _fall_limit() -> float:
	return minf(_rescue_pos.y, _start_pos.y) - 300.0 - katamari.diameter * 3.0


## 回到家中間（卡住或掉出場景時）：球的大小不變，從救援點上方落下。
func rescue() -> void:
	if katamari == null or state != "playing":
		return
	if katamari.is_charging():
		katamari.charge_cancel()
		Sfx.stop_loop()
	katamari.linear_velocity = Vector3.ZERO
	katamari.angular_velocity = Vector3.ZERO
	katamari.global_position = _rescue_pos + Vector3.UP * (katamari.radius() + katamari.diameter * 0.3 + 2.0)
	katamari.reset_physics_interpolation()
	cam.yaw = _rescue_yaw
	cam.snap()
	_stuck_timer = 0.0
	_stuck_anchor = katamari.global_position
	_set_rescue_shown(false)
	hud.toast("回到中間囉！")
	Sfx.play("rescue")


## 卡住偵測：想移動（推搖桿或集氣）但 2.5 秒內移動不到半個直徑，就在右邊顯示「回到中間」按鈕。
func _check_stuck(delta: float, d: Controls.Drive) -> void:
	_stuck_check -= delta
	if _stuck_check > 0.0:
		return
	_stuck_check = 0.25
	var p := katamari.global_position
	var trying := d.move.length() > 0.3 or absf(d.turn) > 0.3 or katamari.is_charging()
	if p.distance_to(_stuck_anchor) > katamari.diameter * 0.5:
		_stuck_anchor = p
		_stuck_timer = 0.0
		_set_rescue_shown(false)
	elif trying:
		_stuck_timer += 0.25
		if _stuck_timer >= 2.5:
			_set_rescue_shown(true)


func _set_rescue_shown(on: bool) -> void:
	if on == _rescue_shown:
		return
	_rescue_shown = on
	hud.show_rescue(on)


## 成長里程碑：10 公分以下每 1 公分、1 公尺以下每 5 公分、10 公尺以下每 50 公分、再大每 5 公尺。
static func milestone_step(d: float) -> float:
	if d < 10.0:
		return 1.0
	if d < 100.0:
		return 5.0
	if d < 1000.0:
		return 50.0
	return 500.0


static func next_milestone(d: float) -> float:
	var step := milestone_step(d)
	return (floorf(d / step + 0.0001) + 1.0) * step


func _check_milestone(delta: float) -> void:
	_cheer_cooldown -= delta
	if katamari.diameter < _next_milestone or _cheer_cooldown > 0.0:
		return
	var reached := floorf(katamari.diameter / milestone_step(katamari.diameter) + 0.0001) * milestone_step(katamari.diameter)
	_next_milestone = next_milestone(katamari.diameter)
	_cheer_cooldown = 2.5
	# 剛好達標時已經有過關的歡呼，不重複
	if katamari.diameter >= goal and time_to_goal < 0.0:
		return
	if Sfx.has_method("play_cheer"):
		Sfx.call("play_cheer")
	else:
		Sfx.play("cheer")
	hud.milestone(KMath.format_size(maxf(reached, 0.0)))
	pusher.cheer()
	cam.pulse_zoom()


func _check_gates() -> void:
	for g in _gates:
		if g["open"] or katamari.diameter < float(g["open_at"]):
			continue
		g["open"] = true
		var body: StaticBody3D = g["body"]
		body.collision_layer = 0
		var t := create_tween()
		# 在物理幀推進，搭配物理插值才不會一頓一頓
		t.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
		t.tween_property(body, "position", body.position + (g["slide"] as Vector3), 0.9).set_trans(Tween.TRANS_QUAD)
		var msg: String = g["message"]
		if not msg.is_empty():
			hud.banner(msg, 1.4, Color(1.0, 0.95, 0.6))
		Sfx.play("gate")
		gate_opened.emit(g["id"], katamari.diameter)


func _check_area(delta: float) -> void:
	_area_timer -= delta
	if _area_timer > 0.0:
		return
	_area_timer = 0.3
	var p := katamari.global_position
	for a in _areas:
		var r: Array = a["rect"]
		if Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])).has_point(Vector2(p.x, p.z)):
			if a["name"] != _current_area:
				_current_area = a["name"]
				hud.show_area(_current_area)
			return


func _update_hud() -> void:
	if hud == null:
		return
	var boost := katamari.boost_amount()
	cam.boost = boost
	cam.charge = clampf(katamari.charge_time() / (Katamari.CHARGE_STAGE_TIME * Katamari.CHARGE_LEVELS), 0.0, 1.0)
	hud.set_speed_fx(boost, ChargeFx.LEVEL_COLORS[katamari.burst_level()])
	hud.set_status(katamari.diameter, goal, time_left, time_total, katamari.collected_count, elapsed if no_limit else -1.0)
	_sun.directional_shadow_max_distance = 220.0 + katamari.diameter * 25.0
	if _env != null and _env.fog_enabled:
		_env.fog_density = float(_env_def["fog_per_d"]) / maxf(katamari.diameter, 1.0)


func _on_collected(item_id: String, def: Dictionary) -> void:
	var size := PropFactory.size_of(def)
	if def.has("critter"):
		hud.banner("黏到%s了！" % def.get("name", item_id), 1.6, Color(1.0, 0.85, 0.4))
		Sfx.play(str((def["critter"] as Dictionary).get("sound", "meow")), 1.2)
		Sfx.play("cheer")
	var big := size > katamari.diameter * 0.45
	hud.toast("%s　%s" % [def.get("name", item_id), KMath.format_size(size)], big)
	hud.bump_count()
	# 黏到東西的聲音依相對大小：小東西「啵」、中等「叮」、快要黏不起來的大東西「啾啾」
	var rel := size / maxf(katamari.diameter * katamari.pickup_ratio, 0.01)
	if rel < 0.35:
		Sfx.play_varied("pop", clampf(1.35 - rel, 0.9, 1.35), 0.06)
	elif rel < 0.7:
		Sfx.play_varied("ding", clampf(1.25 - rel * 0.5, 0.9, 1.2), 0.04)
	else:
		Sfx.play_varied("chirp", 1.0, 0.05)


func _exit_tree() -> void:
	Sfx.stop_loop()
	if demo:
		Sfx.world_muted = false


func _on_charge_level(level: int) -> void:
	charge_fx.pulse()
	if level < Katamari.CHARGE_LEVELS:
		Sfx.play("charge_level", 1.0 + 0.2 * (level - 1))
	else:
		Sfx.play("flame")
		hud.banner("藍色火焰！放開衝出去！", 1.0, Color(0.55, 0.85, 1.0))


func _on_launched(level: int) -> void:
	Sfx.stop_loop()
	hud.clear_banner()
	Sfx.play("launch", 1.15 - 0.08 * level)
	cam.shake(0.35 + 0.15 * level)


func _on_double_jumped() -> void:
	Sfx.play_varied("double_jump", 1.0, 0.04)
	Sfx.play("flip", 1.0, -3.0)
	pusher.flip()


## 集氣衝刺撞到大東西：大震動、反彈，依力道掉好幾件
func _on_crashed(strength: float, lost: int) -> void:
	cam.shake(1.0)
	Sfx.play("impact_big")
	if lost > 0:
		Sfx.play("burst_drop")
		hud.toast("碰！撞到大東西，掉了 %d 個！" % lost, true)
	hud.clear_banner()


func _on_bumped(strength: float, lost: int) -> void:
	cam.shake(clampf(strength / 4.0, 0.3, 1.0))
	Sfx.play("bump", 1.0, -2.0)
	if lost > 0:
		Sfx.play("drop")
		hud.toast("哎呀，掉了 %d 個！" % lost)


func _set_paused(p: bool) -> void:
	get_tree().paused = p
	hud.set_paused(p)


func build_result() -> Dictionary:
	var items: Dictionary = katamari.collected_by_id.duplicate()
	var top: Array = []
	for id in items:
		if int(items[id]) > 0:
			top.append(id)
	top.sort_custom(func(a, b): return PropFactory.size_of(Data.get_item(a)) > PropFactory.size_of(Data.get_item(b)))
	return {
		"stage_id": stage_id,
		"diameter_cm": katamari.diameter,
		"goal_cm": goal,
		"success": katamari.diameter >= goal,
		"items": items,
		"count": katamari.collected_count,
		"time_total": time_total,
		"no_limit": no_limit,
		"elapsed": elapsed,
		"time_to_goal": time_to_goal,
		"comet_sec": float(stage_def.get("comet_sec", 0.0)),
		"top_items": top.slice(0, 6),
		"grades": stage_def.get("grades", []),
	}
