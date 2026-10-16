class_name PickupItem
extends RigidBody3D
## 場景中的任何物件（文具、零食、家具…）。
## 平時凍結為靜態物體以節省效能；從塊球上被撞落時才解凍成動態物體。

var item_id := ""
var def: Dictionary = {}
var size_cm := 1.0
var collected := false
## 撞落後的短暫保護時間，避免剛掉下來又立刻黏回去
var pickup_cooldown := 0.0
var visual: Node3D


static func create(item_def: Dictionary) -> PickupItem:
	var item := PickupItem.new()
	item.setup(item_def)
	return item


func setup(item_def: Dictionary) -> void:
	def = item_def
	item_id = item_def.get("id", "")
	name = item_id
	size_cm = PropFactory.size_of(item_def)
	collision_layer = KMath.LAYER_ITEM
	collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM | KMath.LAYER_KATAMARI
	freeze_mode = RigidBody3D.FREEZE_MODE_STATIC
	freeze = true
	var built := PropFactory.build(item_def)
	visual = built["visual"]
	add_child(visual)
	for s in built["shapes"]:
		var cs := CollisionShape3D.new()
		cs.shape = s["shape"]
		cs.transform = s["xform"]
		add_child(cs)
	var dims := PropFactory.dims_of(item_def)
	mass = maxf(0.001, dims.x * dims.y * dims.z * float(item_def.get("density", 0.0006)))
	var pm := PhysicsMaterial.new()
	pm.friction = 0.9
	pm.bounce = 0.05
	physics_material_override = pm


func is_pickable() -> bool:
	return not collected and pickup_cooldown <= 0.0 and def.get("pickable", true)


## 被吸附時呼叫：把外觀節點交給塊球，本體隨後刪除。
func take_visual() -> Node3D:
	collected = true
	var v := visual
	var gt := v.global_transform
	remove_child(v)
	v.transform = gt
	visual = null
	return v


## 從塊球撞落：以動態物體飛出，靜止後重新凍結。
func launch(impulse: Vector3, cooldown := 0.8) -> void:
	pickup_cooldown = cooldown
	set_physics_process(true)
	freeze = false
	can_sleep = true
	apply_central_impulse(impulse * mass)
	if not sleeping_state_changed.is_connected(_on_sleep):
		sleeping_state_changed.connect(_on_sleep)


func _physics_process(delta: float) -> void:
	if pickup_cooldown > 0.0:
		pickup_cooldown -= delta
	else:
		set_physics_process(false)


func _ready() -> void:
	set_physics_process(pickup_cooldown > 0.0)


func _on_sleep() -> void:
	if sleeping and not collected:
		set_deferred("freeze", true)
