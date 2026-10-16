class_name Critter
extends PickupItem
## 會動的動物（貓、狗）。資料欄位 critter 範例：
##   {"kind": "cat", "walk": 22, "run": 85, "sight": 160, "paw_cooldown": 5, "sound": "meow"}
##
## 行為（依「塊球直徑 ÷ 黏起牠所需直徑」的比例）：
##   比例 < 0.5：好奇靠近，伸爪或用鼻子推一下塊球，讓它掉 1 件東西（有冷卻時間，對小朋友不嚴苛）。
##   比例 0.75 以上：發現塊球就躲開；比例到 1 時全速逃跑。被碰到就會黏上。
##   其他時候：在自己的活動範圍內閒逛、坐下休息。
## 外觀使用 Blender 模型時，名為 head、tail、leg_fl、leg_fr、leg_bl、leg_br 的節點會自動做動畫。

enum Mode { REST, WANDER, PLAY, FLEE }

const PART_NAMES := ["head", "tail", "leg_fl", "leg_fr", "leg_bl", "leg_br"]

## 活動範圍（x, z, 寬, 深，公分）
var roam := Rect2(0, 0, 400, 400)
var mode := Mode.REST

var _target := Vector3.ZERO
var _timer := 1.0
var _speed := 0.0
var _paw_cooldown := 2.0
var _sound_cooldown := 0.0
var _anim := 0.0
var _parts: Dictionary = {}
var _katamari: Katamari
var _ray := PhysicsRayQueryParameters3D.new()


func setup(item_def: Dictionary, color := "") -> void:
	super.setup(item_def, color)
	freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	freeze = true
	for n in PART_NAMES:
		var node := visual.find_child(n, true, false) as Node3D
		if node != null:
			_parts[n] = {"node": node, "rot": node.rotation}


func _ready() -> void:
	super._ready()
	set_physics_process(true)
	_ray.collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM | KMath.LAYER_GATE
	_ray.exclude = [get_rid()]
	if roam.size.x <= 1.0:
		roam = Rect2(position.x - 200.0, position.z - 200.0, 400.0, 400.0)
	_target = position
	_timer = randf_range(0.5, 2.5)


func _cfg(key: String, fallback: float) -> float:
	return float((def.get("critter", {}) as Dictionary).get(key, fallback))


func _physics_process(delta: float) -> void:
	if pickup_cooldown > 0.0:
		pickup_cooldown -= delta
	if collected or not freeze:
		return
	if _katamari == null or not is_instance_valid(_katamari):
		_katamari = get_tree().get_first_node_in_group("katamari") as Katamari
		if _katamari == null:
			return
	_paw_cooldown -= delta
	_sound_cooldown -= delta
	_think(delta)
	_walk(delta)
	_animate(delta)


func _think(delta: float) -> void:
	var k := _katamari
	var to_k := k.global_position - global_position
	to_k.y = 0.0
	var dist := to_k.length()
	var need := size_cm / maxf(k.pickup_ratio, 0.01)
	var ratio := k.diameter / need
	var same_floor := absf((k.global_position.y - k.radius()) - global_position.y) < 20.0
	var aware := same_floor and roam.grow(40.0).has_point(Vector2(k.global_position.x, k.global_position.z)) \
		and dist < _cfg("sight", 160.0) + k.diameter * 2.0

	if aware and ratio >= 0.75:
		if mode != Mode.FLEE:
			_say(1.3)
		mode = Mode.FLEE
		var away := -to_k.normalized() if dist > 0.01 else Vector3.FORWARD
		_target = _clamp_roam(global_position + away * 150.0)
		_speed = _cfg("run", 80.0) * (1.0 if ratio >= 1.0 else 0.7)
		return

	if aware and ratio < 0.5 and _paw_cooldown <= 0.0:
		mode = Mode.PLAY
		_target = k.global_position
		_speed = _cfg("walk", 22.0) * 1.6
		var reach := k.radius() + PropFactory.dims_of(def).z * 0.55 + 2.0
		if dist < reach:
			k.external_hit(to_k, maxf(k.diameter * 2.5, 12.0), 1)
			_paw_cooldown = _cfg("paw_cooldown", 5.0)
			_say(1.0)
			mode = Mode.REST
			_timer = randf_range(1.5, 3.0)
		return

	if mode == Mode.PLAY or mode == Mode.FLEE:
		mode = Mode.REST
		_timer = randf_range(1.0, 2.5)
	_timer -= delta
	if mode == Mode.REST and _timer <= 0.0:
		mode = Mode.WANDER
		_target = _random_point()
		_speed = _cfg("walk", 22.0)
	elif mode == Mode.WANDER and Vector2(_target.x - position.x, _target.z - position.z).length() < 4.0:
		mode = Mode.REST
		_timer = randf_range(1.5, 4.5)


func _walk(delta: float) -> void:
	if mode == Mode.REST:
		return
	var to_t := _target - global_position
	to_t.y = 0.0
	if to_t.length() < 2.0:
		return
	var desired_yaw := atan2(-to_t.x, -to_t.z)
	rotation.y = lerp_angle(rotation.y, desired_yaw, 1.0 - exp(-7.0 * delta))
	var fwd := -global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var facing := clampf(fwd.dot(to_t.normalized()), 0.0, 1.0)
	var step := fwd * _speed * facing * delta
	# 前方有障礙（家具、牆）就換個方向
	var dims := PropFactory.dims_of(def)
	var eye := global_position + Vector3.UP * dims.y * 0.35
	_ray.from = eye
	_ray.to = eye + fwd * (dims.z * 0.55 + step.length() + 3.0)
	var hit := get_world_3d().direct_space_state.intersect_ray(_ray)
	if not hit.is_empty() and not (hit["collider"] is Katamari):
		var col: Object = hit["collider"]
		var small := col is PickupItem and (col as PickupItem).size_cm < size_cm * 0.25
		if not small:
			_target = _random_point()
			return
	var next := global_position + step
	next.x = clampf(next.x, roam.position.x, roam.end.x)
	next.z = clampf(next.z, roam.position.y, roam.end.y)
	global_position = next


func _animate(delta: float) -> void:
	var moving := mode != Mode.REST
	_anim += delta * (4.0 + _speed * 0.08) * (1.0 if moving else 0.0)
	var amp := 0.55 if moving else 0.0
	for n in _parts:
		var node: Node3D = _parts[n]["node"]
		var base: Vector3 = _parts[n]["rot"]
		match n:
			"leg_fl", "leg_br":
				node.rotation = base + Vector3(sin(_anim) * amp, 0, 0)
			"leg_fr", "leg_bl":
				node.rotation = base + Vector3(-sin(_anim) * amp, 0, 0)
			"tail":
				var wag := 10.0 if mode == Mode.PLAY else 3.0
				node.rotation = base + Vector3(0, sin(Time.get_ticks_msec() * 0.001 * wag) * 0.5, 0)
			"head":
				node.rotation = base + Vector3(sin(_anim * 0.5) * 0.08, 0, 0)


func _say(pitch: float) -> void:
	if _sound_cooldown > 0.0 or _katamari == null:
		return
	_sound_cooldown = 3.0
	var dist := global_position.distance_to(_katamari.global_position)
	Sfx.play(str((def.get("critter", {}) as Dictionary).get("sound", "meow")), pitch * randf_range(0.92, 1.08), -clampf(dist / 40.0, 0.0, 18.0))


func _random_point() -> Vector3:
	return Vector3(randf_range(roam.position.x, roam.end.x), position.y, randf_range(roam.position.y, roam.end.y))


func _clamp_roam(p: Vector3) -> Vector3:
	return Vector3(clampf(p.x, roam.position.x, roam.end.x), position.y, clampf(p.z, roam.position.y, roam.end.y))
