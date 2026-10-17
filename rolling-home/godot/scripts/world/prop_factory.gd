class_name PropFactory
## 依物件定義（data/items.json）產生外觀與碰撞形狀。
##
## 優先使用 Blender 管線輸出的 assets/models/props/<model>.glb；
## 沒有模型時，以 dims / parts 定義的低多邊形幾何組合代替，確保專案隨時可執行。
## 物件原點一律在「底面中心」，放置時只要把 y 設成地面高度即可。
##
## 效能（iPad 網頁版）：一般物件的所有零件（或模型的所有材質面）合併成一個頂點色網格，
## 一件物件只要畫一次；同一種物件同一個顏色共用同一份網格。會動的動物保留分開的零件（要做動畫）。
## 另外依物件大小設定可見距離，遠處的小東西不畫。

const MODEL_DIR := "res://assets/models/props/"

static var _materials: Dictionary = {}
static var _meshes: Dictionary = {}
static var _shapes: Dictionary = {}
static var _models: Dictionary = {}
static var _merged: Dictionary = {}
static var _vc_material: StandardMaterial3D


## 吸附尺寸（遊戲用的「大小」，也顯示在收藏目錄）。
## 預設取最長兩邊的幾何平均：細長物（鉛筆）比實際長度好黏，扁平物（硬幣）以面積計。
## 原作的判定公式未公開，這是本專案的設計值；資料可用 "size" 直接覆寫。
## 結束遊戲前釋放快取，避免資源殘留警告。
static func clear_cache() -> void:
	_materials.clear()
	_meshes.clear()
	_shapes.clear()
	_models.clear()
	_merged.clear()
	_vc_material = null


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
## color_override：簡單形狀整個換色；組合形狀只換標記 "tint": true 的零件。
static func build(def: Dictionary, color_override := "") -> Dictionary:
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
	var animated := def.has("critter")
	if model != null and animated:
		visual.add_child(_fit_model(model, def))
	elif model != null:
		var merged := _merged_model(model, def)
		visual.add_child(merged if merged != null else _fit_model(model, def))
	elif not animated:
		var mi := MeshInstance3D.new()
		mi.name = "Merged"
		mi.mesh = _merged_parts(def, parts, color_override)
		mi.material_override = vertex_color_material()
		visual.add_child(mi)
	else:
		for p in parts:
			var shape_type: String = p.get("shape", "box")
			var dims := KMath.vec3(p.get("dims"), Vector3.ONE)
			var mi := MeshInstance3D.new()
			mi.mesh = _mesh(shape_type, dims)
			var hex: String = p.get("color", def.get("color", "#cccccc"))
			if not color_override.is_empty() and (p.get("tint", false) or def.get("shape", "box") != "parts"):
				hex = color_override
			mi.material_override = material(hex)
			mi.transform = _part_xform(p, dims)
			if p.has("name"):
				mi.name = p["name"]
			visual.add_child(mi)
	_apply_visibility(visual, size_of(def))
	return {"visual": visual, "shapes": shapes}


## 合併網格用的共用材質：顏色來自頂點顏色（sRGB），霧面、無高光，和單色零件的材質看起來一樣。
static func vertex_color_material() -> StandardMaterial3D:
	if _vc_material == null:
		_vc_material = StandardMaterial3D.new()
		_vc_material.vertex_color_use_as_albedo = true
		_vc_material.vertex_color_is_srgb = true
		_vc_material.roughness = 1.0
		_vc_material.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	return _vc_material


## 依大小設定可見距離：小東西離鏡頭遠就不畫（鏡頭會跟著球的大小退後，所以只影響相對很小的東西）。
static func _apply_visibility(node: Node, size: float) -> void:
	if node is GeometryInstance3D:
		var gi := node as GeometryInstance3D
		gi.visibility_range_end = size * 220.0 + 300.0
		gi.visibility_range_end_margin = size * 20.0 + 20.0
	for c in node.get_children():
		_apply_visibility(c, size)


## parts 物件：每個零件的基本形狀轉成頂點、套上零件的位置與顏色，合併成一個網格。
static func _merged_parts(def: Dictionary, parts: Array, color_override: String) -> ArrayMesh:
	var key := "%s|%s" % [def.get("id", ""), color_override]
	if _merged.has(key):
		return _merged[key]
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	for p in parts:
		var shape_type: String = p.get("shape", "box")
		var dims := KMath.vec3(p.get("dims"), Vector3.ONE)
		var hex: String = p.get("color", def.get("color", "#cccccc"))
		if not color_override.is_empty() and (p.get("tint", false) or def.get("shape", "box") != "parts"):
			hex = color_override
		var prim := _mesh(shape_type, dims) as PrimitiveMesh
		_append_arrays(prim.get_mesh_arrays(), _part_xform(p, dims), KMath.color(hex), verts, norms, cols, idx)
	var mesh := _commit(verts, norms, cols, idx)
	_merged[key] = mesh
	return mesh


static func _append_arrays(arr: Array, xform: Transform3D, c: Color, verts: PackedVector3Array, norms: PackedVector3Array,
		cols: PackedColorArray, idx: PackedInt32Array) -> void:
	var pv: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var pn: PackedVector3Array = arr[Mesh.ARRAY_NORMAL] if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
	var pc: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
	var base := verts.size()
	var nb := xform.basis.inverse().transposed()
	for i in pv.size():
		verts.append(xform * pv[i])
		norms.append((nb * pn[i]).normalized() if i < pn.size() else Vector3.UP)
		cols.append(c * pc[i] if i < pc.size() else c)
	if arr[Mesh.ARRAY_INDEX] != null:
		for j in (arr[Mesh.ARRAY_INDEX] as PackedInt32Array):
			idx.append(base + j)
	else:
		for j in pv.size():
			idx.append(base + j)


static func _commit(verts: PackedVector3Array, norms: PackedVector3Array, cols: PackedColorArray, idx: PackedInt32Array) -> ArrayMesh:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_COLOR] = cols
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


## Blender 模型：所有材質面合併成一個頂點色網格（材質都是純色）。有貼圖的模型回傳 null，改用原模型。
static func _merged_model(scene: PackedScene, def: Dictionary) -> Node3D:
	var key := "model|%s" % def.get("model", "")
	var mesh: ArrayMesh = _merged.get(key)
	if mesh == null and not _merged.has(key):
		mesh = _merge_scene(scene)
		_merged[key] = mesh
	if mesh == null:
		return null
	var holder := Node3D.new()
	holder.name = "Model"
	var mi := MeshInstance3D.new()
	mi.name = "Merged"
	mi.mesh = mesh
	mi.material_override = vertex_color_material()
	holder.add_child(mi)
	var aabb := mesh.get_aabb()
	if aabb.size.length() < 0.0001:
		return holder
	var dims := dims_of(def)
	var k := maxf(dims.x, maxf(dims.y, dims.z)) / maxf(aabb.size.x, maxf(aabb.size.y, aabb.size.z))
	holder.scale = Vector3.ONE * k
	mi.position = -Vector3(aabb.get_center().x, aabb.position.y, aabb.get_center().z)
	return holder


static func _merge_scene(scene: PackedScene) -> ArrayMesh:
	var inst: Node3D = scene.instantiate()
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	var ok := _collect(inst, Transform3D.IDENTITY, verts, norms, cols, idx)
	inst.free()
	if not ok or verts.is_empty():
		return null
	return _commit(verts, norms, cols, idx)


static func _collect(node: Node, parent_xform: Transform3D, verts: PackedVector3Array, norms: PackedVector3Array,
		cols: PackedColorArray, idx: PackedInt32Array) -> bool:
	var xform := parent_xform
	if node is Node3D:
		xform = parent_xform * (node as Node3D).transform
	if node is MeshInstance3D and (node as MeshInstance3D).mesh != null:
		var mi := node as MeshInstance3D
		for s in mi.mesh.get_surface_count():
			var mat := mi.get_active_material(s)
			var c := Color.WHITE
			if mat is BaseMaterial3D:
				var bm := mat as BaseMaterial3D
				if bm.albedo_texture != null:
					return false
				c = bm.albedo_color
			_append_arrays(mi.mesh.surface_get_arrays(s), xform, c, verts, norms, cols, idx)
	for child in node.get_children():
		if not _collect(child, xform, verts, norms, cols, idx):
			return false
	return true


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
