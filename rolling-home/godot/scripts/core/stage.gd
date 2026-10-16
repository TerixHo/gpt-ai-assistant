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

var _state_timer := 0.0
var _gates: Array[Dictionary] = []
var _areas: Array = []
var _current_area := ""
var _area_timer := 0.0
var _start_pos := Vector3.ZERO
var _start_yaw := 0.0
var _last_tick := -1
var _sun: DirectionalLight3D


func setup(id: String) -> void:
	stage_id = id
	stage_def = Data.get_stage(id)


func _ready() -> void:
	name = "Stage"
	if stage_def.is_empty():
		push_error("關卡設定不存在：%s" % stage_id)
		return
	time_total = float(stage_def.get("time_sec", 180.0))
	time_left = time_total
	no_limit = bool(Game.settings.get("no_time_limit", false))
	goal = float(stage_def.get("goal_cm", 10.0))
	_build_environment()

	items_root = Node3D.new()
	items_root.name = "Items"
	add_child(items_root)
	var level := Data.get_level(stage_def.get("level", ""))
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

	cam = KatamariCamera.new()
	add_child(cam)
	cam.target = katamari
	cam.yaw = _start_yaw
	cam.snap()

	pusher = Pusher.new()
	pusher.katamari = katamari
	pusher.cam = cam
	add_child(pusher)

	hud = Hud.new()
	add_child(hud)
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

	var watcher := Node.new()
	watcher.name = "PauseWatcher"
	watcher.process_mode = Node.PROCESS_MODE_ALWAYS
	watcher.set_script(preload("res://scripts/core/pause_watcher.gd"))
	add_child(watcher)
	watcher.toggled.connect(func():
		if state == "playing" or get_tree().paused:
			_set_paused(not get_tree().paused))

	katamari.input_enabled = false
	if skip_intro:
		_begin_play()
	else:
		hud.banner(stage_def.get("intro", "預備…"), INTRO_TIME - 0.6)
	_update_hud()
	Sfx.play_music(stage_def.get("music", "home"))


func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = KMath.color(stage_def.get("sky", "#bfe6ff"))
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
			_state_timer += delta
			if _state_timer >= OUTRO_TIME and _state_timer - delta < OUTRO_TIME:
				finished.emit(build_result())
	_update_hud()


func _play_step(delta: float) -> void:
	var d := Controls.read(delta)
	cam.apply_drive(d, delta)
	katamari.set_drive(d.move, cam.yaw)
	if d.dash:
		katamari.dash()
	elapsed += delta
	if not no_limit:
		time_left -= delta
	_check_gates()
	_check_area(delta)
	if katamari.global_position.y < -300.0:
		katamari.linear_velocity = Vector3.ZERO
		katamari.global_position = _start_pos + Vector3.UP * katamari.diameter
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


func _check_gates() -> void:
	for g in _gates:
		if g["open"] or katamari.diameter < float(g["open_at"]):
			continue
		g["open"] = true
		var body: StaticBody3D = g["body"]
		body.collision_layer = 0
		var t := create_tween()
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
	hud.set_status(katamari.diameter, goal, time_left, time_total, katamari.collected_count, elapsed if no_limit else -1.0)
	_sun.directional_shadow_max_distance = 220.0 + katamari.diameter * 25.0


func _on_collected(item_id: String, def: Dictionary) -> void:
	var size := PropFactory.size_of(def)
	if def.has("critter"):
		hud.banner("黏到%s了！" % def.get("name", item_id), 1.6, Color(1.0, 0.85, 0.4))
		Sfx.play(str((def["critter"] as Dictionary).get("sound", "meow")), 1.2)
		Sfx.play("cheer")
	var big := size > katamari.diameter * 0.45
	hud.toast("%s　%s" % [def.get("name", item_id), KMath.format_size(size)], big)
	Sfx.play("pickup_big" if big else "pickup", clampf(1.5 - size / maxf(katamari.diameter, 0.1), 0.7, 1.6))


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
