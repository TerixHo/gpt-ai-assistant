class_name PropFactory
## 依物件定義（data/items.json）產生外觀與碰撞形狀。
##
## 優先使用 Blender 管線輸出的 assets/models/props/<model>.glb；
## 沒有模型時，以 dims / parts 定義的低多邊形幾何組合代替，確保專案隨時可執行。
## 物件原點一律在「底面中心」，放置時只要把 y 設成地面高度即可。

const MODEL_DIR := "res://assets/models/props/"

static var _materials: Dictionary = {}
static var _meshes: Dictionary = {}
static var _shapes: Dictionary = {}
static var _models: Dictionary = {}


## 吸附尺寸（遊戲用的「大小」，也顯示在收藏目錄）。
## 預設取最長兩邊的幾何平均：細長物（鉛筆）比實際長度好黏，扁平物（硬幣）以面積計。
## 原作的判定公式未公開，這是本專案的設計值；資料可用 "size" 直接覆寫。
## 結束遊戲前釋放快取，避免資源殘留警告。
static func clear_cache() -> void:
	_materials.clear()
	_meshes.clear()
	_shapes.clear()
	_models.clear()


static func size_of(def: Dictionary) -> float:
	if def.has("size"):
		return float(def["size"])
	var d := dims_of(def)
	var a := [d.x, d.y, d.z]
	a.sort()
	return sqrt(float(a[2]) * float(a[1]))


static func dims_of(def: Dictionary) -> Vector3:
	return KMath.vec3(def.get("dims", [1, 1, 1]), Vector3.ONE)


static func material(hex: String) -> StandardMaterial3D:
	if _materials.has(hex):
		return _materials[hex]
	var m := StandardMaterial3D.new()
	m.albedo_color = KMath.color(hex)
	m.roughness = 1.0
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	_materials[hex] = m
	return m


## 回傳 { "visual": Node3D, "shapes": [ {shape, xform}, ... ] }
static func build(def: Dictionary) -> Dictionary:
	var visual := Node3D.new()
	visual.name = "Visual"
	var shapes: Array = []
	var parts: Array = _parts_of(def)
	for p in parts:
		var shape_type: String = p.get("shape", "box")
		var dims := KMath.vec3(p.get("dims"), Vector3.ONE)
		var xform := _part_xform(p, dims)
		if p.get("collide", true):
			shapes.append({"shape": _collision_shape(shape_type, dims), "xform": xform})
	var model := _model_scene(def)
	if model != null:
		visual.add_child(_fit_model(model, def))
	else:
		for p in parts:
			var shape_type: String = p.get("shape", "box")
			var dims := KMath.vec3(p.get("dims"), Vector3.ONE)
			var mi := MeshInstance3D.new()
			mi.mesh = _mesh(shape_type, dims)
			mi.material_override = material(p.get("color", def.get("color", "#cccccc")))
			mi.transform = _part_xform(p, dims)
			visual.add_child(mi)
	return {"visual": visual, "shapes": shapes}


## 把簡單形狀與組合形狀統一成 parts 陣列。
static func _parts_of(def: Dictionary) -> Array:
	if def.get("shape", "box") == "parts":
		return def.get("parts", [])
	var dims := dims_of(def)
	return [{
		"shape": def.get("shape", "box"),
		"dims": [dims.x, dims.y, dims.z],
		"pos": [0.0, dims.y * 0.5, 0.0],
		"color": def.get("color", "#cccccc"),
	}]


static func _part_xform(p: Dictionary, dims: Vector3) -> Transform3D:
	var pos := KMath.vec3(p.get("pos"), Vector3(0, dims.y * 0.5, 0))
	var rot := KMath.vec3(p.get("rot"), Vector3.ZERO)
	var basis := Basis.from_euler(Vector3(deg_to_rad(rot.x), deg_to_rad(rot.y), deg_to_rad(rot.z)))
	return Transform3D(basis, pos)


static func _mesh(shape_type: String, dims: Vector3) -> Mesh:
	var key := "%s|%.2f|%.2f|%.2f" % [shape_type, dims.x, dims.y, dims.z]
	if _meshes.has(key):
		return _meshes[key]
	var mesh: Mesh
	match shape_type:
		"cylinder", "cone":
			var c := CylinderMesh.new()
			c.bottom_radius = dims.x * 0.5
			c.top_radius = 0.0 if shape_type == "cone" else dims.x * 0.5
			c.height = dims.y
			c.radial_segments = 14
			c.rings = 1
			mesh = c
		"sphere":
			var s := SphereMesh.new()
			s.radius = dims.x * 0.5
			s.height = dims.y
			s.radial_segments = 14
			s.rings = 7
			mesh = s
		"capsule":
			var cap := CapsuleMesh.new()
			cap.radius = dims.x * 0.5
			cap.height = maxf(dims.y, dims.x)
			cap.radial_segments = 12
			cap.rings = 3
			mesh = cap
		_:
			var b := BoxMesh.new()
			b.size = dims
			mesh = b
	_meshes[key] = mesh
	return mesh


static func _collision_shape(shape_type: String, dims: Vector3) -> Shape3D:
	var key := "%s|%.2f|%.2f|%.2f" % [shape_type, dims.x, dims.y, dims.z]
	if _shapes.has(key):
		return _shapes[key]
	var shape: Shape3D
	match shape_type:
		"cylinder", "cone":
			var c := CylinderShape3D.new()
			c.radius = dims.x * 0.5
			c.height = dims.y
			shape = c
		"sphere":
			var s := SphereShape3D.new()
			s.radius = maxf(dims.x, dims.y) * 0.5
			shape = s
		"capsule":
			var cap := CapsuleShape3D.new()
			cap.radius = dims.x * 0.5
			cap.height = maxf(dims.y, dims.x)
			shape = cap
		_:
			var b := BoxShape3D.new()
			b.size = dims
			shape = b
	_shapes[key] = shape
	return shape


static func _model_scene(def: Dictionary) -> PackedScene:
	var model: String = def.get("model", "")
	if model.is_empty():
		return null
	if _models.has(model):
		return _models[model]
	var path := MODEL_DIR + model + ".glb"
	var scene: PackedScene = load(path) if ResourceLoader.exists(path) else null
	_models[model] = scene
	return scene


## 將 glb 模型等比縮放成資料定義的尺寸，並把底面中心對齊原點。
static func _fit_model(scene: PackedScene, def: Dictionary) -> Node3D:
	var inst: Node3D = scene.instantiate()
	var aabb := _aabb_of(inst, Transform3D.IDENTITY)
	var holder := Node3D.new()
	holder.name = "Model"
	holder.add_child(inst)
	if aabb.size.length() < 0.0001:
		return holder
	var dims := dims_of(def)
	var target := maxf(dims.x, maxf(dims.y, dims.z))
	var longest := maxf(aabb.size.x, maxf(aabb.size.y, aabb.size.z))
	var k := target / longest
	holder.scale = Vector3.ONE * k
	inst.position = -Vector3(aabb.get_center().x, aabb.position.y, aabb.get_center().z)
	return holder


static func _aabb_of(node: Node, parent_xform: Transform3D) -> AABB:
	var result := AABB()
	var first := true
	var xform := parent_xform
	if node is Node3D:
		xform = parent_xform * (node as Node3D).transform
	if node is MeshInstance3D and (node as MeshInstance3D).mesh != null:
		result = xform * (node as MeshInstance3D).mesh.get_aabb()
		first = false
	for child in node.get_children():
		var child_aabb := _aabb_of(child, xform)
		if child_aabb.size.length() < 0.0001:
			continue
		if first:
			result = child_aabb
			first = false
		else:
			result = result.merge(child_aabb)
	return result
