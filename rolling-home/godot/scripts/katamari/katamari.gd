class_name Katamari
extends RigidBody3D
## 塊球本體：滾動、吸附、成長、撞落。
##
## 成長模型：塊球以「體積」累積，直徑 = 由體積反推的球體直徑。
## 吸附條件：物件尺寸 ≤ 直徑 × pickup_ratio，且碰到塊球（或其突出物）。
## 撞落規則：以高速撞上牆或過大的物件時，最外層的幾個物件會掉落並扣回體積。
## 所有數值皆可在檢視器調整，預設值見 docs/01_遊戲設定文件.md 第 4 章。

signal collected(item_id: String, def: Dictionary)
signal diameter_changed(diameter_cm: float)
signal bumped(strength: float, lost: int)
signal dashed

const MAX_PROTRUSIONS := 10

@export var start_diameter_cm := 5.0
## 可吸附門檻：物件尺寸 ≤ 直徑 × 此比例
@export_range(0.05, 1.5) var pickup_ratio := 0.7
## 物件體積併入塊球的全域倍率（調整整體成長速度）
@export var growth_gain := 1.0
## 最高速度：每秒幾個直徑
@export var max_speed_d := 3.0
## 最高速度下限（公分/秒），避免太小時寸步難行
@export var min_top_speed := 14.0
## 加速度：每秒² 幾個直徑
@export var accel_d := 7.0
## 放開搖桿時的減速度：每秒² 幾個直徑
@export var coast_decel_d := 2.5
@export var dash_speed_mult := 2.1
@export var dash_duration := 0.8
## 撞擊掉落門檻：撞擊速度超過每秒幾個直徑
@export var knock_threshold_d := 2.9
## 吸附偵測球相對於本體半徑的倍率
@export var grab_margin := 1.1

var diameter := 5.0
var volume := 0.0
var collected_count := 0
var collected_by_id: Dictionary = {}
## 撞落物件要放回的父節點（由關卡指定）
var items_parent: Node
var input_enabled := true

var _move := Vector2.ZERO
var _yaw := 0.0
var _dash_left := 0.0
var _grounded := false
var _ground_normal := Vector3.UP
var _last_velocity := Vector3.ZERO
var _knock_cooldown := 0.0
var _pending_knock: Dictionary = {}
var _pending_lift := 0.0
var _body_shape := SphereShape3D.new()
var _grab_shape := SphereShape3D.new()
var _query := PhysicsShapeQueryParameters3D.new()
var _core: Node3D
var _stuck_root: Node3D
## 每個黏上的物件：{node, id, def, size, volume, dist, half}
var _stuck: Array[Dictionary] = []
## 突出點：{node, local, outer, radius}
var _protrusions: Array[Dictionary] = []


func _ready() -> void:
	name = "Katamari"
	collision_layer = KMath.LAYER_KATAMARI
	collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM | KMath.LAYER_GATE
	continuous_cd = true
	can_sleep = false
	contact_monitor = true
	max_contacts_reported = 16
	var pm := PhysicsMaterial.new()
	pm.friction = 1.0
	pm.bounce = 0.0
	physics_material_override = pm

	var cs := CollisionShape3D.new()
	cs.name = "Shape"
	cs.shape = _body_shape
	add_child(cs)
	_core = _build_core()
	add_child(_core)
	_stuck_root = Node3D.new()
	_stuck_root.name = "Stuck"
	add_child(_stuck_root)

	_query.shape = _grab_shape
	_query.collision_mask = KMath.LAYER_ITEM
	_query.collide_with_bodies = true
	_query.collide_with_areas = false

	volume = KMath.sphere_volume(start_diameter_cm)
	_apply_size()


func radius() -> float:
	return diameter * 0.5


func is_grounded() -> bool:
	return _grounded


func horizontal_speed() -> float:
	return Vector2(linear_velocity.x, linear_velocity.z).length()


## move：x 平移、y 前進（相機座標）；yaw：相機水平角（弧度）。
func set_drive(move: Vector2, yaw: float) -> void:
	_move = move.limit_length(1.0) if input_enabled else Vector2.ZERO
	_yaw = yaw


func dash() -> bool:
	if _dash_left > -0.6 or not input_enabled:
		return false
	_dash_left = dash_duration
	dashed.emit()
	return true


func is_dashing() -> bool:
	return _dash_left > 0.0


func forward_dir() -> Vector3:
	return Vector3(-sin(_yaw), 0.0, -cos(_yaw))


func _physics_process(delta: float) -> void:
	_knock_cooldown -= delta
	_dash_left -= delta
	if not _pending_knock.is_empty():
		var k := _pending_knock
		_pending_knock = {}
		_knock(k)
	_grab_check()


func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:
	var dt := state.step
	# 1. 接觸分析：地面法線與撞擊強度
	_grounded = false
	var n_sum := Vector3.ZERO
	var impact := 0.0
	var impact_normal := Vector3.ZERO
	for i in state.get_contact_count():
		var n := state.get_contact_local_normal(i)
		if n.y > 0.55:
			_grounded = true
			n_sum += n
		else:
			# 碰到本來就黏得起來的小東西不算撞擊
			var other := state.get_contact_collider_object(i)
			if other is PickupItem and KMath.can_pick((other as PickupItem).size_cm, diameter, pickup_ratio):
				continue
			var into := -_last_velocity.dot(n)
			if into > impact:
				impact = into
				impact_normal = n
	_ground_normal = n_sum.normalized() if _grounded else Vector3.UP

	if _pending_lift > 0.0:
		var t := state.transform
		t.origin += Vector3.UP * _pending_lift
		state.transform = t
		_pending_lift = 0.0

	# 2. 驅動：以速度導向方式控制，接地時沿地面平面移動
	var fwd := forward_dir()
	var right := Vector3(cos(_yaw), 0.0, -sin(_yaw))
	var wish := right * _move.x + fwd * _move.y
	var wish_len := minf(wish.length(), 1.0)
	var top := maxf(max_speed_d * diameter, min_top_speed)
	if _dash_left > 0.0:
		wish = fwd
		wish_len = 1.0
		top *= dash_speed_mult
	var up := _ground_normal
	var v := state.linear_velocity
	var v_plane := v - up * v.dot(up)
	var target := Vector3.ZERO
	var accel: float
	var dir := Vector3.ZERO
	if wish_len > 0.01:
		dir = (wish - up * wish.dot(up)).normalized()
		target = dir * top * wish_len
		accel = maxf(accel_d * diameter, 35.0) * (1.0 if _grounded else 0.3)
	else:
		accel = maxf(coast_decel_d * diameter, 10.0) if _grounded else 0.0
	var dv := (target - v_plane).limit_length(accel * dt)
	v += dv
	# 上坡時只抵銷「與前進方向相反」的重力分量，讓上坡手感接近原作。
	# （不能整個抵銷：在台階邊角時接觸法線會傾斜，整個抵銷會把球吸回邊緣。）
	if _grounded and wish_len > 0.01:
		var g := state.total_gravity
		var along := (g - up * g.dot(up)).dot(dir)
		if along < 0.0:
			v -= dir * along * dt
	state.linear_velocity = v

	# 3. 接地時讓角速度貼近純滾動，外觀上確實在「滾」
	if _grounded:
		var roll := up.cross(v) / maxf(radius(), 0.01)
		state.angular_velocity = state.angular_velocity.lerp(roll, 0.35)

	# 4. 撞擊偵測（實際掉落在 _physics_process 處理，避免在物理回呼中增刪節點）
	if impact > knock_threshold_d * diameter and _knock_cooldown <= 0.0:
		_pending_knock = {"strength": impact / diameter, "normal": impact_normal}
		_knock_cooldown = 0.5
	_last_velocity = v


func _grab_check() -> void:
	var space := get_world_3d().direct_space_state
	_query.transform = Transform3D(Basis.IDENTITY, global_position)
	_grab_shape.radius = radius() * grab_margin
	_try_hits(space.intersect_shape(_query, 32))
	# 突出的大物件也能黏東西（迭代副本：吸附過程可能新增或移除突出點）
	for p in _protrusions.duplicate():
		_grab_shape.radius = float(p["radius"]) * 1.15
		_query.transform = Transform3D(Basis.IDENTITY, global_transform * (p["local"] as Vector3))
		_try_hits(space.intersect_shape(_query, 8))
	_grab_shape.radius = radius() * grab_margin


func _try_hits(hits: Array[Dictionary]) -> void:
	for h in hits:
		var body: Object = h.get("collider")
		if body is PickupItem:
			var item := body as PickupItem
			if item.is_pickable() and KMath.can_pick(item.size_cm, diameter, pickup_ratio):
				_attach(item)


func _attach(item: PickupItem) -> void:
	var dims := PropFactory.dims_of(item.def)
	var v := item.take_visual()
	var gt := v.transform
	var center := global_position
	var item_center := gt * Vector3(0.0, dims.y * 0.5, 0.0)
	var dir := item_center - center
	if dir.length_squared() < 0.000001:
		dir = Vector3.UP
	dir = dir.normalized()
	var r := radius()
	var half := item.size_cm * 0.5
	var dist := r * 0.96
	_stuck_root.add_child(v)
	v.global_transform = Transform3D(gt.basis, gt.origin + (center + dir * dist - item_center))

	var gain := KMath.item_volume(item.size_cm, float(item.def.get("fill", 0.5))) * growth_gain
	volume += gain
	_stuck.append({"node": v, "id": item.item_id, "def": item.def, "size": item.size_cm,
		"volume": gain, "dist": dist, "half": half})
	if item.size_cm > diameter * 0.26 and _protrusions.size() < MAX_PROTRUSIONS:
		_add_protrusion(v, dir, dist, half)
	collected_count += 1
	collected_by_id[item.item_id] = int(collected_by_id.get(item.item_id, 0)) + 1
	item.queue_free()
	var old := diameter
	_apply_size()
	if _grounded:
		_pending_lift += maxf(diameter - old, 0.0) * 0.5
	collected.emit(item.item_id, item.def)


## 突出點：大物件黏上後外露的部分，只用來「黏東西」，不參與實體碰撞。
## （早期版本用實體碰撞做凹凸感，但小尺寸時會像腳架一樣把球撐住，已改為此做法。）
func _add_protrusion(node: Node3D, dir_world: Vector3, dist: float, half: float) -> void:
	var offset := dist + half * 0.4
	var radius_p := half * 0.55
	var local := global_transform.affine_inverse() * (global_position + dir_world * offset)
	_protrusions.append({"node": node, "local": local, "outer": offset + radius_p, "radius": radius_p})


func _apply_size() -> void:
	diameter = KMath.diameter_from_volume(volume)
	var r := radius()
	_body_shape.radius = r
	_grab_shape.radius = r * grab_margin
	_core.scale = Vector3.ONE * diameter * 0.9
	mass = maxf(0.02, volume * 0.0008)
	_prune()
	diameter_changed.emit(diameter)


## 被新物件覆蓋、完全埋進核心的物件就移除，維持效能。
func _prune() -> void:
	var r := radius()
	var core_r := r * 0.9
	var keep: Array[Dictionary] = []
	for e in _stuck:
		if float(e["dist"]) + float(e["half"]) * 0.6 < core_r:
			var node: Node3D = e["node"]
			if is_instance_valid(node):
				node.queue_free()
		else:
			keep.append(e)
	_stuck = keep
	var keep_p: Array[Dictionary] = []
	for p in _protrusions:
		if float(p["outer"]) >= r * 1.04 and is_instance_valid(p["node"]):
			keep_p.append(p)
	_protrusions = keep_p


func _knock(k: Dictionary) -> void:
	var strength: float = k["strength"]
	var normal: Vector3 = k["normal"]
	var drop := clampi(int(strength - knock_threshold_d) + 1, 1, 4)
	var lost := 0
	var min_volume := KMath.sphere_volume(start_diameter_cm)
	for i in drop:
		if _stuck.is_empty() or items_parent == null:
			break
		var e: Dictionary = _stuck.pop_back()
		var node: Node3D = e["node"]
		if not is_instance_valid(node):
			continue
		var gt := node.global_transform
		var keep_p: Array[Dictionary] = []
		for p in _protrusions:
			if p["node"] != node:
				keep_p.append(p)
		_protrusions = keep_p
		node.queue_free()
		var item := PickupItem.create(e["def"])
		items_parent.add_child(item)
		item.global_transform = gt
		var out := (gt.origin - global_position).normalized()
		item.launch((out + normal * 0.6 + Vector3.UP).normalized() * maxf(diameter * 3.0, 30.0))
		volume = maxf(volume - float(e["volume"]), min_volume)
		collected_count = maxi(collected_count - 1, 0)
		var id: String = e["id"]
		collected_by_id[id] = maxi(int(collected_by_id.get(id, 1)) - 1, 0)
		lost += 1
	if lost > 0:
		_apply_size()
	bumped.emit(strength, lost)


## 原創造型的核心：鮭魚橘球體 + 赤道彩帶 + 兩極圓帽（類似手鞠球／小行星）。
func _build_core() -> Node3D:
	var root := Node3D.new()
	root.name = "Core"
	var ball := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.5
	sm.height = 1.0
	sm.radial_segments = 24
	sm.rings = 12
	ball.mesh = sm
	ball.material_override = PropFactory.material("#f79d65")
	root.add_child(ball)
	var band := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.47
	tm.outer_radius = 0.53
	tm.rings = 24
	tm.ring_segments = 8
	band.mesh = tm
	band.material_override = PropFactory.material("#d62839")
	root.add_child(band)
	var band2 := MeshInstance3D.new()
	band2.mesh = tm
	band2.material_override = PropFactory.material("#1d4e89")
	band2.rotation_degrees = Vector3(90, 0, 0)
	root.add_child(band2)
	for y in [-1.0, 1.0]:
		var cap := MeshInstance3D.new()
		var cm := SphereMesh.new()
		cm.radius = 0.16
		cm.height = 0.32
		cm.radial_segments = 12
		cm.rings = 6
		cap.mesh = cm
		cap.material_override = PropFactory.material("#44bba4")
		cap.position = Vector3(0, 0.44 * y, 0)
		root.add_child(cap)
	return root
