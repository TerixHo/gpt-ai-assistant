class_name KatamariCamera
extends Node3D
## 追蹤塊球的攝影機。左右轉向由雙搖桿差值控制（原作的「繞球轉身」）。
## 距離與高度隨塊球直徑放大，並避免穿牆。

@export var turn_speed := 2.2
@export var quick_turn_time := 0.32
@export var follow_sharpness := 9.0

var yaw := 0.0
var target: Katamari
var camera: Camera3D
var look_up := false

var _quick_turn_left := 0.0
var _shake := 0.0
var _ray := PhysicsRayQueryParameters3D.new()
# 震動用自己的亂數，避免每秒畫面數不同時打亂遊戲邏輯共用的亂數序列（自動測試需要可重現）
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	name = "KatamariCamera"
	camera = Camera3D.new()
	camera.near = 0.1
	camera.far = 8000.0
	camera.fov = 64.0
	add_child(camera)
	camera.current = true
	_ray.collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM | KMath.LAYER_GATE
	_ray.hit_back_faces = false


func apply_drive(d: Controls.Drive, delta: float) -> void:
	yaw -= d.turn * turn_speed * float(Game.settings.get("camera_turn_speed", 1.0)) * delta
	if d.quick_turn and _quick_turn_left <= 0.0:
		_quick_turn_left = quick_turn_time
	if _quick_turn_left > 0.0:
		var step := minf(delta, _quick_turn_left)
		yaw += PI * step / quick_turn_time
		_quick_turn_left -= step
	look_up = d.look_up


func shake(amount: float) -> void:
	_shake = maxf(_shake, amount)


func snap() -> void:
	_update(1.0, true)


func _process(delta: float) -> void:
	if target == null or not is_instance_valid(target):
		return
	_update(delta, false)


func _update(delta: float, instant: bool) -> void:
	var t := target.get_global_transform_interpolated().origin
	var dm := target.diameter
	var dist := dm * 3.2 + 4.0
	var height := dm * 1.3 + 1.8
	if look_up:
		dist *= 1.6
		height = dm * 6.0 + 30.0
	var focus := t + Vector3.UP * dm * 0.35
	var desired := t + Basis(Vector3.UP, yaw) * Vector3(0.0, height, dist)
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
			var over := t + Vector3.UP * (dm * 2.2 + 4.0) + Basis(Vector3.UP, yaw) * Vector3(0.0, 0.0, dm * 0.4)
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
	if _shake > 0.0:
		camera.global_position += Vector3(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1), _rng.randf_range(-1, 1)) * _shake * dm * 0.06
		_shake = maxf(_shake - delta * 3.0, 0.0)
	if camera.global_position.distance_to(focus) > 0.01:
		camera.look_at(focus, Vector3.UP)
