class_name Pusher
extends Node3D
## 推球的主角：圓滾滾的紫色貓咪（依 Terix 提供的角色圖，由 tools/blender/generate_props.py 的 pusher 配方建模）。
## 站在塊球後方、面向前進方向，雙手往前推球；走路時左右搖擺、雙腳交替，跳躍時舉起雙手。
## 模型的可動部件：body / ear_l / ear_r / arm_l / arm_r / foot_l / foot_r（原點在關節）。

const HEIGHT := 4.5
const MODEL_PATH := "res://assets/models/props/pusher.glb"
const PART_NAMES := ["body", "ear_l", "ear_r", "arm_l", "arm_r", "foot_l", "foot_r"]

var katamari: Katamari
var cam: KatamariCamera

var _walk := 0.0
var _push := 0.4
var _air := 0.0
var _root: Node3D
var _parts: Dictionary = {}
var _ray := PhysicsRayQueryParameters3D.new()


## 主角身高（公分）隨塊球直徑放大：小球時比球矮（鏡頭才看得到球），大球時最高 8 公分仍看得到角色。
static func height_for(diameter: float) -> float:
	return clampf(0.8 * pow(diameter, 0.8), 0.9, 8.0)


func _ready() -> void:
	name = "Pusher"
	add_to_group("pusher")
	# 位置每個畫面依插值後的塊球位置更新，不需要再做物理插值
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	_ray.collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM
	_root = Node3D.new()
	add_child(_root)
	if ResourceLoader.exists(MODEL_PATH):
		var model: Node3D = (load(MODEL_PATH) as PackedScene).instantiate()
		_root.add_child(model)
		for part_name in PART_NAMES:
			var n := model.find_child(part_name, true, false) as Node3D
			if n != null:
				_parts[part_name] = n
		_restyle(model)
	else:
		_build_placeholder()


## 匯入的材質換成霧面絨毛質感：身體顏色來自頂點顏色（淡紫到藍紫漸層），眼睛是亮面黑珠子。
func _restyle(node: Node) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var key := src.resource_name if src != null else ""
			mi.set_surface_override_material(i, _material_for(key))
	for c in node.get_children():
		_restyle(c)


func _material_for(key: String) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	if key.contains("skin"):
		m.vertex_color_use_as_albedo = true
		m.albedo_color = Color.WHITE
		m.roughness = 0.82
		m.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT_WRAP
		m.rim_enabled = true
		m.rim = 0.45
		m.rim_tint = 0.7
		# 角色很小，自己投在自己身上的陰影會出現鋸齒；不接收陰影，但仍會在地上投影
		m.disable_receive_shadows = true
	elif key.contains("eye"):
		m.albedo_color = Color("#141414")
		m.roughness = 0.1
		m.metallic_specular = 0.9
	elif key.contains("ffffff"):
		m.albedo_color = Color.WHITE
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	else:
		m.albedo_color = Color("#2a2030")
		m.roughness = 0.6
	return m


func _build_placeholder() -> void:
	var skin := PropFactory.material("#b8a8f3")
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 1.75
	s.height = 3.9
	mi.mesh = s
	mi.material_override = skin
	mi.position = Vector3(0, 2.25, 0)
	_root.add_child(mi)


func _process(delta: float) -> void:
	if katamari == null or cam == null:
		return
	var k := katamari.get_global_transform_interpolated().origin
	var r := katamari.radius()
	var h := height_for(katamari.diameter)
	scale = Vector3.ONE * (h / HEIGHT)
	var fwd := Vector3(-sin(cam.yaw), 0.0, -cos(cam.yaw))
	var pos := Vector3(k.x, k.y, k.z) - fwd * (r + h * 0.40)
	# 腳底貼地：往下找最近的地面；球跳起來時跟著一起跳
	_ray.from = pos + Vector3.UP * r
	_ray.to = pos - Vector3.UP * (r + 80.0)
	_ray.exclude = [katamari.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(_ray)
	var ground := (hit["position"] as Vector3).y if not hit.is_empty() else k.y - r
	var ball_bottom := k.y - r
	var airborne := not katamari.is_grounded() and ball_bottom > ground + h * 0.15
	pos.y = maxf(ground, ball_bottom) if airborne else ground
	global_position = pos
	rotation.y = cam.yaw
	_animate(delta, airborne)


func _animate(delta: float, airborne: bool) -> void:
	var speed := katamari.horizontal_speed()
	var rel := minf(speed / maxf(katamari.diameter * 2.5, 4.0), 1.0)
	var moving := rel > 0.05
	_walk += delta * (6.0 + rel * 7.0) * (1.0 if moving else 0.0)
	_air = move_toward(_air, 1.0 if airborne else 0.0, delta * 6.0)
	_push = move_toward(_push, 1.0 if moving else 0.45, delta * 4.0)
	var charging := katamari.is_charging()
	if charging:
		# 集氣：雙腳原地快跑、身體壓低前傾，越接近藍色火焰抖得越厲害
		rel = 1.0
		_walk += delta * (14.0 + 4.0 * katamari.charge_level())
		_push = 1.0
	var swing := sin(_walk) * rel
	var bob := absf(sin(_walk)) * rel
	_root.position.y = bob * 0.22
	_root.rotation.z = swing * 0.07
	_root.rotation.x = -0.28 if (katamari.is_dashing() or katamari.is_bursting()) else -0.08 * rel
	_root.position.x = 0.0
	if charging:
		var lvl := float(katamari.charge_level())
		_root.rotation.x = -0.35
		_root.position.y = -0.15
		_root.position.x = sin(Time.get_ticks_msec() * 0.09) * 0.03 * (1.0 + lvl * 1.5)
	if _parts.is_empty():
		return
	var ground_mix := 1.0 - _air
	# 雙腳交替前後擺；在空中時縮起來
	_rot_x("foot_l", swing * 0.55 * ground_mix + 0.4 * _air)
	_rot_x("foot_r", -swing * 0.55 * ground_mix + 0.4 * _air)
	# 雙手往前推球，跟著步伐一推一推；跳起來時舉高
	var arm := lerpf(0.35, 1.25, _push) * ground_mix + 2.6 * _air
	_rot_x("arm_l", arm + swing * 0.18)
	_rot_x("arm_r", arm - swing * 0.18)
	# 耳朵隨著走路輕輕晃
	_rot_x("ear_l", -bob * 0.18 + 0.12 * _air)
	_rot_x("ear_r", -bob * 0.18 + 0.12 * _air)


func _rot_x(part: String, angle: float) -> void:
	var n: Node3D = _parts.get(part)
	if n != null:
		n.rotation.x = angle
