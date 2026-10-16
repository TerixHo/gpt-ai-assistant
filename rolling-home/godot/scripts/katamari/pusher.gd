class_name Pusher
extends Node3D
## 推球的小角色（原創角色「小滾」，暫名）。站在塊球後方、面向前進方向。
## 外觀暫以基本幾何組成；Blender 管線輸出 assets/models/props/pusher.glb 後會自動替換。

const HEIGHT := 4.5
const MODEL_PATH := "res://assets/models/props/pusher.glb"

var katamari: Katamari
var cam: KatamariCamera

var _walk := 0.0
var _legs: Array[Node3D] = []
var _body: Node3D
var _ray := PhysicsRayQueryParameters3D.new()


func _ready() -> void:
	name = "Pusher"
	_ray.collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM
	_body = Node3D.new()
	add_child(_body)
	if ResourceLoader.exists(MODEL_PATH):
		var model: Node3D = (load(MODEL_PATH) as PackedScene).instantiate()
		_body.add_child(model)
	else:
		_build_placeholder()


func _build_placeholder() -> void:
	var skin := PropFactory.material("#ffd7b5")
	var suit := PropFactory.material("#5bc0eb")
	var leaf := PropFactory.material("#7bc950")
	var dark := PropFactory.material("#2b2d42")
	_add_part(_body, _capsule(0.9, 1.9), suit, Vector3(0, 1.75, 0))
	_add_part(_body, _sphere(1.5), skin, Vector3(0, 3.35, 0))
	_add_part(_body, _sphere(0.22), dark, Vector3(-0.32, 3.45, -0.68))
	_add_part(_body, _sphere(0.22), dark, Vector3(0.32, 3.45, -0.68))
	var sprout := _add_part(_body, _sphere(0.5), leaf, Vector3(0.2, 4.2, 0))
	sprout.scale = Vector3(1.2, 0.35, 0.6)
	sprout.rotation_degrees = Vector3(0, 0, 25)
	for side in [-1.0, 1.0]:
		var arm := _add_part(_body, _capsule(0.35, 1.3), suit, Vector3(0.55 * side, 2.0, -0.55))
		arm.rotation_degrees = Vector3(-70, 0, 0)
		var leg_pivot := Node3D.new()
		leg_pivot.position = Vector3(0.35 * side, 0.9, 0)
		_body.add_child(leg_pivot)
		_add_part(leg_pivot, _capsule(0.38, 1.0), dark, Vector3(0, -0.45, 0))
		_legs.append(leg_pivot)


func _add_part(parent: Node3D, mesh: Mesh, mat: Material, pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


func _capsule(r: float, h: float) -> CapsuleMesh:
	var m := CapsuleMesh.new()
	m.radius = r
	m.height = h
	m.radial_segments = 10
	m.rings = 2
	return m


func _sphere(d: float) -> SphereMesh:
	var m := SphereMesh.new()
	m.radius = d * 0.5
	m.height = d
	m.radial_segments = 12
	m.rings = 6
	return m


func _process(delta: float) -> void:
	if katamari == null or cam == null:
		return
	var k := katamari.get_global_transform_interpolated().origin
	var r := katamari.radius()
	var fwd := Vector3(-sin(cam.yaw), 0.0, -cos(cam.yaw))
	var pos := Vector3(k.x, k.y, k.z) - fwd * (r + 1.0)
	# 腳底貼地：往下找最近的地面
	_ray.from = pos + Vector3.UP * r
	_ray.to = pos - Vector3.UP * (r + 60.0)
	_ray.exclude = [katamari.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(_ray)
	pos.y = (hit["position"] as Vector3).y if not hit.is_empty() else k.y - r
	global_position = pos
	rotation.y = cam.yaw
	var speed := katamari.horizontal_speed()
	_walk += delta * (4.0 + speed * 0.35) * (1.0 if speed > 1.0 else 0.0)
	var swing := sin(_walk) * minf(speed / 20.0, 1.0) * 0.7
	if _legs.size() == 2:
		_legs[0].rotation.x = swing
		_legs[1].rotation.x = -swing
	_body.position.y = absf(sin(_walk)) * 0.25 * minf(speed / 20.0, 1.0)
	_body.rotation.x = -0.25 if katamari.is_dashing() else 0.0
