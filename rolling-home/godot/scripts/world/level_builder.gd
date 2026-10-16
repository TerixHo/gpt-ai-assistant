class_name LevelBuilder
## 依關卡配置檔（data/levels/*.json）建出整個場景：
## 地板、牆（含門洞）、斜坡與台階、家具、隨機散布的物件、尺寸門檻、區域名稱。
## 座標與尺寸單位皆為公分；x 往東、z 往南、y 往上。

const WALL_COLOR := "#f3ede0"
const BASEBOARD_COLOR := "#b08a63"


## 回傳 { gates: Array[Dictionary], areas: Array[Dictionary], start: Dictionary, spawned: int }
static func build(level: Dictionary, world_root: Node3D, items_root: Node3D, enabled_zones: Array, seed_value: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var statics := Node3D.new()
	statics.name = "Architecture"
	world_root.add_child(statics)

	for f in level.get("floors", []):
		_build_floor(f, statics)
	for w in level.get("walls", []):
		_build_wall(w, statics)
	for b in level.get("blocks", []):
		_build_block(b, statics)
	for r in level.get("ramps", []):
		_build_ramp(r, statics)

	# 家具與手動擺放的物件
	var footprints: Array[Rect2] = []
	for p in level.get("placements", []):
		var item := _place_item(p, items_root)
		if item != null and p.get("blocks_spawn", true):
			footprints.append(_footprint(item))

	# 隨機散布物件（只啟用本關指定的區塊；空陣列代表全部啟用）
	var spawned := 0
	var occupied: Array[Vector4] = []
	for zone in level.get("spawns", []):
		if not enabled_zones.is_empty() and not enabled_zones.has(zone.get("zone", "")):
			continue
		spawned += _spawn_zone(zone, items_root, footprints, occupied, rng)

	var gates: Array[Dictionary] = []
	for g in level.get("gates", []):
		gates.append(_build_gate(g, statics))

	return {
		"gates": gates,
		"areas": level.get("areas", []),
		"start": level.get("start", {}),
		"spawned": spawned,
	}


static func _static_box(parent: Node3D, size: Vector3, center: Vector3, mat: Material, layer := KMath.LAYER_WORLD, rot_y_deg := 0.0) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	body.position = center
	body.rotation_degrees = Vector3(0, rot_y_deg, 0)
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	cs.shape = shape
	body.add_child(cs)
	var mi := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mi.mesh = mesh
	mi.material_override = mat
	body.add_child(mi)
	parent.add_child(body)
	return body


static func _build_floor(f: Dictionary, parent: Node3D) -> void:
	var rect: Array = f["rect"]
	var top := float(f.get("y", 0.0))
	var thick := float(f.get("thickness", 6.0))
	var size := Vector3(float(rect[2]), thick, float(rect[3]))
	var center := Vector3(float(rect[0]) + size.x * 0.5, top - thick * 0.5, float(rect[1]) + size.z * 0.5)
	var mat := ProcTex.floor_material(f.get("pattern", "plain"), f.get("color", "#c8a878"), float(f.get("repeat", 90.0)))
	var body := _static_box(parent, size, center, mat)
	body.name = "Floor_%s" % f.get("name", "")


## 牆：from/to 為牆中線端點；gaps 為門洞 [起點距離, 終點距離, (門楣高度)]。
static func _build_wall(w: Dictionary, parent: Node3D) -> void:
	var a := Vector3(float(w["from"][0]), 0, float(w["from"][1]))
	var b := Vector3(float(w["to"][0]), 0, float(w["to"][1]))
	var height := float(w.get("height", 240.0))
	var thick := float(w.get("thickness", 10.0))
	var base_y := float(w.get("y", 0.0))
	var length := a.distance_to(b)
	if length < 0.01:
		return
	var dir := (b - a) / length
	var yaw := rad_to_deg(atan2(-dir.z, dir.x))
	var mat := PropFactory.material(w.get("color", WALL_COLOR))
	var trim := PropFactory.material(BASEBOARD_COLOR)
	var gaps: Array = w.get("gaps", [])
	gaps.sort_custom(func(x, y): return float(x[0]) < float(y[0]))
	var cursor := 0.0
	var segments: Array = []
	for g in gaps:
		segments.append([cursor, float(g[0])])
		var lintel := float(g[2]) if g.size() > 2 else 200.0
		if lintel < height:
			_wall_piece(parent, a, dir, yaw, float(g[0]), float(g[1]), base_y + lintel, base_y + height, thick, mat)
		cursor = float(g[1])
	segments.append([cursor, length])
	for s in segments:
		if float(s[1]) - float(s[0]) > 0.5:
			_wall_piece(parent, a, dir, yaw, float(s[0]), float(s[1]), base_y, base_y + height, thick, mat)
			_wall_piece(parent, a, dir, yaw, float(s[0]), float(s[1]), base_y, base_y + 8.0, thick + 1.6, trim)


static func _wall_piece(parent: Node3D, origin: Vector3, dir: Vector3, yaw: float, from_d: float, to_d: float, y0: float, y1: float, thick: float, mat: Material) -> void:
	var len := to_d - from_d
	var mid := origin + dir * (from_d + len * 0.5)
	_static_box(parent, Vector3(len, y1 - y0, thick), Vector3(mid.x, (y0 + y1) * 0.5, mid.z), mat, KMath.LAYER_WORLD, yaw)


## 台階、門檻、玄關落差等純建物方塊。
static func _build_block(b: Dictionary, parent: Node3D) -> void:
	var size := KMath.vec3(b["size"])
	var pos := KMath.vec3(b["pos"])
	var mat: Material
	if b.has("pattern"):
		mat = ProcTex.floor_material(b["pattern"], b.get("color", "#cccccc"), float(b.get("repeat", 90.0)))
	else:
		mat = PropFactory.material(b.get("color", "#cccccc"))
	var body := _static_box(parent, size, pos + Vector3(0, size.y * 0.5, 0), mat, KMath.LAYER_WORLD, float(b.get("rot", 0.0)))
	body.name = "Block_%s" % b.get("name", "")


## 斜坡：從 from 到 to 的傾斜板（例如靠在矮桌邊的尺或雜誌）。
static func _build_ramp(r: Dictionary, parent: Node3D) -> void:
	var a := KMath.vec3(r["from"])
	var b := KMath.vec3(r["to"])
	var width := float(r.get("width", 20.0))
	var thick := float(r.get("thickness", 1.5))
	var length := a.distance_to(b)
	var body := StaticBody3D.new()
	body.name = "Ramp_%s" % r.get("name", "")
	body.collision_layer = KMath.LAYER_WORLD
	body.collision_mask = 0
	var mid := (a + b) * 0.5
	var fwd := (b - a).normalized()
	var side := fwd.cross(Vector3.UP).normalized()
	var up := side.cross(fwd).normalized()
	body.transform = Transform3D(Basis(side, up, -fwd), mid - up * thick * 0.5)
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(width, thick, length)
	cs.shape = shape
	body.add_child(cs)
	var mi := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = shape.size
	mi.mesh = mesh
	mi.material_override = PropFactory.material(r.get("color", "#d9b26f"))
	body.add_child(mi)
	parent.add_child(body)


static func _place_item(p: Dictionary, items_root: Node3D) -> PickupItem:
	var def := Data.get_item(p.get("item", ""))
	if def.is_empty():
		return null
	var item := PickupItem.create(def)
	items_root.add_child(item)
	item.position = KMath.vec3(p.get("pos"))
	item.rotation_degrees = Vector3(0, float(p.get("rot", 0.0)), 0)
	return item


## 物件在地面上的佔地範圍（xz 平面），用來避免隨機物件生成在家具裡。
static func _footprint(item: PickupItem) -> Rect2:
	var dims := PropFactory.dims_of(item.def)
	var basis := item.global_transform.basis if item.is_inside_tree() else item.transform.basis
	var corners := [Vector3(dims.x, 0, dims.z), Vector3(-dims.x, 0, dims.z), Vector3(dims.x, 0, -dims.z), Vector3(-dims.x, 0, -dims.z)]
	var rect := Rect2(Vector2(item.position.x, item.position.z), Vector2.ZERO)
	for c in corners:
		var w: Vector3 = item.position + basis * (c * 0.5)
		rect = rect.expand(Vector2(w.x, w.z))
	return rect


static func _spawn_zone(zone: Dictionary, items_root: Node3D, footprints: Array[Rect2], occupied: Array[Vector4], rng: RandomNumberGenerator) -> int:
	var rect: Array = zone["rect"]
	var area := Rect2(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
	var y := float(zone.get("y", 0.0))
	var avoid: bool = zone.get("avoid_furniture", y <= 0.5)
	var blockers: Array[Rect2] = []
	if avoid:
		blockers.append_array(footprints)
	for ex in zone.get("exclude", []):
		blockers.append(Rect2(float(ex[0]), float(ex[1]), float(ex[2]), float(ex[3])))
	var count := 0
	var items: Dictionary = zone.get("items", {})
	for id in items:
		var def := Data.get_item(id)
		if def.is_empty():
			continue
		var size := PropFactory.size_of(def)
		var half := size * 0.5
		for n in int(items[id]):
			for attempt in 24:
				var pos := Vector2(
					rng.randf_range(area.position.x + half, area.end.x - half),
					rng.randf_range(area.position.y + half, area.end.y - half))
				if _inside_any(pos, half, blockers):
					continue
				if _overlaps(pos, y, half, occupied):
					continue
				var item := PickupItem.create(def)
				items_root.add_child(item)
				item.position = Vector3(pos.x, y, pos.y)
				item.rotation_degrees = Vector3(0, rng.randf_range(0, 360), 0)
				occupied.append(Vector4(pos.x, y, pos.y, half))
				count += 1
				break
	return count


static func _inside_any(p: Vector2, half: float, rects: Array[Rect2]) -> bool:
	for r in rects:
		if r.grow(half).has_point(p):
			return true
	return false


static func _overlaps(p: Vector2, y: float, half: float, occupied: Array[Vector4]) -> bool:
	for o in occupied:
		if absf(o.y - y) > 1.0:
			continue
		var min_d := (o.w + half) * 0.85
		if Vector2(o.x, o.z).distance_squared_to(p) < min_d * min_d:
			return true
	return false


## 尺寸門檻：塊球達到指定直徑前，這道阻擋物會擋住去路。
static func _build_gate(g: Dictionary, parent: Node3D) -> Dictionary:
	var size := KMath.vec3(g["size"])
	var pos := KMath.vec3(g["pos"])
	var body := _static_box(parent, size, pos + Vector3(0, size.y * 0.5, 0), PropFactory.material(g.get("color", "#efe6cf")), KMath.LAYER_GATE, float(g.get("rot", 0.0)))
	body.name = "Gate_%s" % g.get("id", "")
	# 紙門格子裝飾
	if g.get("style", "") == "fusuma":
		var frame := PropFactory.material("#6b4f3a")
		for i in 3:
			var bar := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(size.x + 0.4, 2.0, size.z + 0.6)
			bar.mesh = bm
			bar.material_override = frame
			bar.position = Vector3(0, -size.y * 0.5 + size.y * (0.02 + i * 0.48), 0)
			body.add_child(bar)
	return {
		"id": g.get("id", ""),
		"name": g.get("name", ""),
		"open_at": float(g.get("open_at_cm", 10.0)),
		"slide": KMath.vec3(g.get("slide"), Vector3(0, -size.y - 2.0, 0)),
		"message": g.get("message", ""),
		"body": body,
		"open": false,
	}
