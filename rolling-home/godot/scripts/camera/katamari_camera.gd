class_name KatamariCamera
extends Node3D
## 追蹤塊球的攝影機。左右轉向由雙搖桿差值控制（原作的「繞球轉身」）。
## 自動視角：距離與高度跟著「含外圍突出物的球大小」慢慢往後退（球長大時看得出鏡頭在拉遠），並避免穿牆。
## 視角（數字鍵 1 到 5）：1 第一人稱、2 近、3 自動（預設）、4 遠、5 正面（面對主角，看到後方）。
## 第一人稱環視（E）：球停下來，用 WASD 看上下左右，再按一次 E 回到原本的視角。

signal view_changed(label: String)

const VIEW_NAMES := ["", "第一人稱", "近距離", "自動", "遠距離", "正面"]

@export var turn_speed := 2.2
@export var quick_turn_time := 0.32
@export var follow_sharpness := 9.0

var yaw := 0.0
var target: Katamari
var camera: Camera3D
var look_up := false
var view := 3
var free_look := false
## 集氣衝刺的速度感（0 到 1）：視野拉寬、鏡頭往後拉
var boost := 0.0
## 集氣進度（0 到 1）：視野微微收窄，蓄力的緊張感
var charge := 0.0

var _look_yaw := 0.0
var _look_pitch := 0.0
var _quick_turn_left := 0.0
var _shake := 0.0
var _focus := Vector3.ZERO
var _has_focus := false
var _boost_shown := 0.0
## 鏡頭用的球大小（含外圍突出物），慢慢跟上實際大小
var _size := 0.0
## 成長里程碑時鏡頭往後彈一下
var _pulse := 0.0
var _ray := PhysicsRayQueryParameters3D.new()
# 震動用自己的亂數，避免每秒畫面數不同時打亂遊戲邏輯共用的亂數序列（自動測試需要可重現）
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	name = "KatamariCamera"
	# 每個畫面依插值後的塊球位置更新，不需要再做物理插值
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	camera = Camera3D.new()
	camera.near = 0.08
	camera.far = 8000.0
	camera.fov = 64.0
	add_child(camera)
	camera.current = true
	_ray.collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM | KMath.LAYER_GATE
	_ray.hit_back_faces = false


func apply_drive(d: Controls.Drive, delta: float) -> void:
	if d.free_look_toggle:
		set_free_look(not free_look)
	if d.view == -1:
		set_view(view % 5 + 1)
	elif d.view > 0:
		set_view(d.view)
	if free_look:
		_look_yaw -= d.look.x * 1.9 * delta
		_look_pitch = clampf(_look_pitch + d.look.y * 1.5 * delta, -1.25, 1.25)
		look_up = false
		return
	yaw -= d.turn * turn_speed * float(Game.settings.get("camera_turn_speed", 1.0)) * delta
	if d.quick_turn and _quick_turn_left <= 0.0:
		_quick_turn_left = quick_turn_time
		Sfx.play("turn", 1.0, -3.0)
	if _quick_turn_left > 0.0:
		var step := minf(delta, _quick_turn_left)
		yaw += PI * step / quick_turn_time
		_quick_turn_left -= step
	look_up = d.look_up


func set_view(v: int) -> void:
	view = clampi(v, 1, 5)
	free_look = false
	view_changed.emit("視角：" + VIEW_NAMES[view])


func set_free_look(on: bool) -> void:
	free_look = on
	_look_yaw = 0.0
	_look_pitch = -0.08
	view_changed.emit("第一人稱環視：WASD 看四周，再按 E 回來" if on else "視角：" + VIEW_NAMES[view])


func is_first_person() -> bool:
	return free_look or view == 1


func shake(amount: float) -> void:
	_shake = maxf(_shake, amount)


## 成長里程碑：鏡頭往後拉一下再回來
func pulse_zoom() -> void:
	_pulse = 1.0


func snap() -> void:
	_update(1.0, true)


func _process(delta: float) -> void:
	if target == null or not is_instance_valid(target):
		return
	_update(delta, false)


func _update(delta: float, instant: bool) -> void:
	var t := target.get_global_transform_interpolated().origin
	# 自動視角：以含突出物的外觀大小決定距離，變大時慢慢跟上（看得出鏡頭在往後退），變小時快一點
	var want := target.visual_radius() * 2.0
	if instant or _size <= 0.0:
		_size = want
	else:
		_size = lerpf(_size, want, 1.0 - exp(-(1.2 if want > _size else 3.0) * delta))
	_pulse = move_toward(_pulse, 0.0, delta * 1.4)
	var dm := _size * (1.0 + 0.18 * sin(_pulse * PI))
	# 遠近裁切面跟著尺寸：小球時近一點才看得到珠子，大球時要看得到遠方
	camera.near = clampf(dm * 0.01, 0.05, 50.0)
	camera.far = maxf(8000.0, dm * 400.0)
	# 衝出去的瞬間視野一下子拉寬，之後慢慢收回
	_boost_shown = boost if boost > _boost_shown else move_toward(_boost_shown, boost, delta * 1.5)
	camera.fov = 64.0 + 26.0 * _boost_shown - 7.0 * charge
	var r := dm * 0.5
	var fwd := Vector3(-sin(yaw), 0.0, -cos(yaw))
	if is_first_person():
		_first_person(t, r, fwd, delta, instant)
		return
	# 焦點平滑：滾過小台階時的上下小彈跳不會直接晃到畫面
	var focus_goal := t + Vector3.UP * dm * 0.35
	if view == 5:
		# 正面：看向球後面的主角（鏡頭拉高越過球，看得到主角的臉和後方）
		var h := Pusher.height_for(dm)
		focus_goal = t - fwd * (r + h * 0.4) + Vector3.UP * (h * 0.6 - r)
	if instant or not _has_focus:
		_focus = focus_goal
		_has_focus = true
	else:
		_focus = _focus.lerp(focus_goal, 1.0 - exp(-16.0 * delta))
	var focus := _focus
	var dist := dm * 3.2 + 4.0
	var height := dm * 1.3 + 1.8
	match view:
		2:
			dist *= 0.62
			height *= 0.75
		4:
			dist *= 1.75
			height *= 1.9
		5:
			dist = dm * 2.2 + 5.0
			height = dm * 2.8 + 3.0
	if look_up:
		dist *= 1.6
		height = dm * 6.0 + 30.0
	dist *= 1.0 + 0.3 * _boost_shown - 0.12 * charge
	var back := fwd if view == 5 else -fwd
	var desired := t + Vector3.UP * height + back * dist
	# 牆壁與大型家具會把鏡頭往前推；小東西忽略，避免鏡頭亂跳
	var space := get_world_3d().direct_space_state
	_ray.from = focus
	_ray.to = desired
	var exclude: Array[RID] = [target.get_rid()]
	_ray.exclude = exclude
	for attempt in 6:
		var hit := space.intersect_ray(_ray)
		if hit.is_empty():
			break
		var col: Object = hit["collider"]
		if col is PickupItem and (col as PickupItem).size_cm < maxf(dm * 2.5, 25.0):
			exclude.append((col as PickupItem).get_rid())
			_ray.exclude = exclude
			continue
		var hit_pos := (hit["position"] as Vector3) + (hit["normal"] as Vector3) * 1.5
		if hit_pos.distance_to(focus) < dm * 1.3:
			# 背後太擠（緊貼牆或大家具）：改成從上方往下看，避免鏡頭穿進球裡
			var over := t + Vector3.UP * (dm * 2.2 + 4.0) + back * (dm * 0.4)
			# 上方也可能有東西（書桌底面、櫃子），碰到就停在它前面
			var up_ray := PhysicsRayQueryParameters3D.new()
			up_ray.from = focus
			up_ray.to = over
			up_ray.collision_mask = _ray.collision_mask
			up_ray.exclude = exclude
			var up_hit := space.intersect_ray(up_ray)
			if not up_hit.is_empty():
				over = (up_hit["position"] as Vector3) + (up_hit["normal"] as Vector3) * 1.0
			desired = over
		else:
			desired = hit_pos
		break
	var w := 1.0 if instant else 1.0 - exp(-follow_sharpness * delta)
	camera.global_position = camera.global_position.lerp(desired, w)
	_apply_shake(dm, delta)
	if camera.global_position.distance_to(focus) > 0.01:
		camera.look_at(focus, Vector3.UP)


## 第一人稱：眼睛在球的前上方（避開黏在球上的東西），往前看；環視時可以轉頭看四周。
func _first_person(t: Vector3, r: float, fwd: Vector3, delta: float, instant: bool) -> void:
	var eye := t + fwd * (r * 1.3 + 0.4) + Vector3.UP * (r * 0.5 + 0.5)
	var w := 1.0 if instant else 1.0 - exp(-20.0 * delta)
	camera.global_position = camera.global_position.lerp(eye, w)
	_apply_shake(r * 2.0, delta)
	var look_yaw := yaw + (_look_yaw if free_look else 0.0)
	var pitch := _look_pitch if free_look else -0.12
	var dir := Vector3(-sin(look_yaw) * cos(pitch), sin(pitch), -cos(look_yaw) * cos(pitch))
	camera.look_at(camera.global_position + dir, Vector3.UP)
	_has_focus = false


func _apply_shake(dm: float, delta: float) -> void:
	if _shake > 0.0:
		camera.global_position += Vector3(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1), _rng.randf_range(-1, 1)) * _shake * dm * 0.06
		_shake = maxf(_shake - delta * 3.0, 0.0)
