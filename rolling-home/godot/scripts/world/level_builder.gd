class_name LevelBuilder
## 依關卡配置檔（data/levels/*.json）建出整個場景：
## 地板、牆（含門洞）、斜坡與台階、積木樓梯、家具、隨機散布的物件、尺寸門檻、區域名稱、
## 背景裝飾（不碰撞）、飄落的花瓣。
## 座標與尺寸單位皆為公分；x 往東、z 往南、y 往上。
##
## 配置檔欄位（都可省略）：
##   floors / walls / blocks / ramps：建物（見各 _build_* 說明）
##   stairs：積木樓梯，外觀是一階一階的積木，碰撞是平滑斜坡（任何大小的球都爬得上去）
##   decor：只有外觀、不碰撞的裝飾（遠山、雲、田裡的稻子）
##   petals：花瓣飄落的範圍
##   placements / spawns / gates / areas / start
##   rescue：卡住時「回到中間」的位置 {"pos": [x, y, z], "yaw_deg": 角度}，省略時用 start
##   env：天空與霧 {"sky": "#bfe6ff", "fog_color": "#dfefff", "fog_per_d": 0.0}（由 Stage 讀取）

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
	for st in level.get("stairs", []):
		_build_stairs(st, statics)
	for d in level.get("decor", []):
		_build_decor(d, statics)
	for pt in level.get("petals", []):
		_build_petals(pt, statics)

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
		"rescue": level.get("rescue", level.get("start", {})),
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
	body.set_meta("pattern", f.get("pattern", "plain"))


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
	body.set_meta("pattern", b.get("pattern", "plain"))


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


## 積木樓梯：{"from": 底部起點（地面）, "to": 頂端終點（平台邊緣）, "width": 寬, "step": 每階高度（預設 3）,
##   "colors": [顏色…], "style": "lego"（有凸點的積木，預設）、"books"（一疊書）或 "blocks"（素面木頭積木）}
## 碰撞是一塊實心楔形，斜面剛好通過每一階的前緣，球滾上去時看起來是踩在階梯邊上。
static func _build_stairs(st: Dictionary, parent: Node3D) -> void:
	var a := KMath.vec3(st["from"])
	var b := KMath.vec3(st["to"])
	var width := float(st.get("width", 20.0))
	var rise := b.y - a.y
	var flat := Vector3(b.x - a.x, 0.0, b.z - a.z)
	var run := flat.length()
	if run < 0.5 or absf(rise) < 0.1:
		return
	# 往下走的樓梯：把起終點對調，一律由低往高建
	if rise < 0.0:
		var tmp := a
		a = b
		b = tmp
		rise = -rise
		flat = -flat
	var fwd := flat / run
	var side := Vector3.UP.cross(fwd).normalized()
	var body := StaticBody3D.new()
	body.name = "Stairs_%s" % st.get("name", "")
	body.collision_layer = KMath.LAYER_WORLD
	body.collision_mask = 0
	# 本地座標：x 沿寬度、y 往上、z 沿前進方向（0 在起點）
	body.transform = Transform3D(Basis(side, Vector3.UP, fwd), a)
	var hw := width * 0.5
	var cs := CollisionShape3D.new()
	var wedge := ConvexPolygonShape3D.new()
	wedge.points = PackedVector3Array([
		Vector3(-hw, 0, 0), Vector3(hw, 0, 0),
		Vector3(-hw, 0, run), Vector3(hw, 0, run),
		Vector3(-hw, rise, run), Vector3(hw, rise, run)])
	cs.shape = wedge
	body.add_child(cs)
	var mi := MeshInstance3D.new()
	mi.mesh = _stairs_mesh(run, rise, width, st)
	mi.material_override = _vertex_color_material()
	body.add_child(mi)
	parent.add_child(body)


const LEGO_COLORS := ["#e63946", "#ffd60a", "#3a86ff", "#06d6a0", "#ff8fab", "#f77f00", "#8338ec"]
const BOOK_COLORS := ["#e9c46a", "#f4a261", "#2a9d8f", "#e76f51", "#8ecae6", "#b5838d", "#90be6d"]


static func _stairs_mesh(run: float, rise: float, width: float, st: Dictionary) -> ArrayMesh:
	var style: String = st.get("style", "lego")
	var step_h := float(st.get("step", 3.0))
	var n := maxi(2, int(round(rise / step_h)))
	var colors: Array = st.get("colors", BOOK_COLORS if style == "books" else LEGO_COLORS)
	var hw := width * 0.5
	var surf := SurfaceTool.new()
	surf.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(1, n + 1):
		# 第 i 階：前緣在 run * i / (n + 1) 的位置、高度 rise * i / n。最後一階一路延伸到終點
		var z0 := run * float(i) / float(n + 1)
		var z1 := run * float(i + 1) / float(n + 1) if i < n else run
		var h := rise * float(i) / float(n)
		var c := KMath.color(colors[(i - 1) % colors.size()])
		var inset := 0.0
		if style == "books":
			# 書本大小不一，左右稍微錯開
			inset = width * 0.04 * float((i * 7) % 3)
		_add_box(surf, Vector3(-hw + inset, 0.0, z0), Vector3(hw - inset * 0.5, h, z1), c)
		if style == "lego":
			# 每階頂面兩排凸點
			var stud_r := clampf(minf(z1 - z0, width) * 0.16, 0.25, 4.0)
			var stud_h := stud_r * 0.6
			var cols := clampi(int(width / (stud_r * 4.0)), 1, 6)
			for k in cols:
				var x := -hw + width * (float(k) + 0.5) / float(cols)
				_add_cylinder(surf, Vector3(x, h, (z0 + z1) * 0.5), stud_r, stud_h, c.lightened(0.08))
	surf.generate_normals()
	return surf.commit()


static func _add_box(surf: SurfaceTool, lo: Vector3, hi: Vector3, c: Color) -> void:
	var p := [
		Vector3(lo.x, lo.y, lo.z), Vector3(hi.x, lo.y, lo.z), Vector3(hi.x, hi.y, lo.z), Vector3(lo.x, hi.y, lo.z),
		Vector3(lo.x, lo.y, hi.z), Vector3(hi.x, lo.y, hi.z), Vector3(hi.x, hi.y, hi.z), Vector3(lo.x, hi.y, hi.z)]
	# 每面兩個三角形（逆時針朝外）；側面稍微暗一點，看得出一階一階
	var faces := [[3, 2, 6, 7, 1.0], [0, 3, 7, 4, 0.82], [1, 5, 6, 2, 0.82], [0, 1, 2, 3, 0.9], [4, 7, 6, 5, 0.9]]
	for f in faces:
		var col := c.darkened(1.0 - float(f[4]))
		surf.set_smooth_group(-1)
		for idx in [0, 1, 2, 0, 2, 3]:
			surf.set_color(col)
			surf.add_vertex(p[int(f[idx])])


static func _add_cylinder(surf: SurfaceTool, base: Vector3, r: float, h: float, c: Color) -> void:
	var seg := 8
	for i in seg:
		var a0 := TAU * float(i) / seg
		var a1 := TAU * float(i + 1) / seg
		var p0 := base + Vector3(cos(a0) * r, 0, sin(a0) * r)
		var p1 := base + Vector3(cos(a1) * r, 0, sin(a1) * r)
		var top := Vector3(0, h, 0)
		surf.set_smooth_group(-1)
		for v in [p0, p1 + top, p1, p0, p0 + top, p1 + top]:
			surf.set_color(c.darkened(0.12))
			surf.add_vertex(v)
		for v in [base + top, p1 + top, p0 + top]:
			surf.set_color(c)
			surf.add_vertex(v)


static var _vc_material: StandardMaterial3D


static func _vertex_color_material() -> StandardMaterial3D:
	if _vc_material == null:
		_vc_material = StandardMaterial3D.new()
		_vc_material.vertex_color_use_as_albedo = true
		_vc_material.vertex_color_is_srgb = true
		_vc_material.roughness = 0.85
		_vc_material.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	return _vc_material


## 裝飾：只有外觀、不碰撞。
##   {"shape": "box"/"cylinder"/"cone"/"sphere", "size": [寬, 高, 深], "pos": 底面中心, "color": "#", "rot": 角度或 [x, y, z]}
##   {"item": 物件 id, "pos": [...], "rot": 角度, "scale": 倍率}：借用物件的外觀
static func _build_decor(d: Dictionary, parent: Node3D) -> void:
	var node: Node3D
	if d.has("item"):
		var def := Data.get_item(d["item"])
		if def.is_empty():
			return
		node = PropFactory.build(def, d.get("color", ""))["visual"]
		node.scale = Vector3.ONE * float(d.get("scale", 1.0))
	else:
		var size := KMath.vec3(d.get("size"), Vector3.ONE * 10.0)
		var mi := MeshInstance3D.new()
		mi.mesh = PropFactory._mesh(d.get("shape", "box"), size)
		mi.position = Vector3(0, size.y * 0.5, 0)
		if d.has("pattern"):
			mi.material_override = ProcTex.floor_material(d["pattern"], d.get("color", "#cccccc"), float(d.get("repeat", 90.0)))
		else:
			mi.material_override = PropFactory.material(d.get("color", "#cccccc"))
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if d.get("no_shadow", false) else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		node = Node3D.new()
		node.add_child(mi)
	node.name = "Decor_%s" % d.get("name", "")
	node.position = KMath.vec3(d.get("pos"))
	var rot: Variant = d.get("rot", 0.0)
	node.rotation_degrees = KMath.vec3(rot) if rot is Array else Vector3(0, float(rot), 0)
	parent.add_child(node)


## 花瓣飄落：{"pos": 範圍中心, "size": [寬, 高, 深], "color": "#ffc8dd", "amount": 數量, "petal": 花瓣大小, "fall": 落下速度}
## 粒子固定種子，避免打亂全域亂數（自動測試需要可重現）。
static func _build_petals(pt: Dictionary, parent: Node3D) -> void:
	var p := CPUParticles3D.new()
	p.name = "Petals_%s" % pt.get("name", "")
	p.use_fixed_seed = true
	p.seed = 4242 + int(pt.get("amount", 40))
	var size := KMath.vec3(pt.get("size"), Vector3(200, 150, 200))
	var petal := float(pt.get("petal", 1.6))
	var fall := float(pt.get("fall", 18.0))
	p.amount = int(pt.get("amount", 40))
	p.lifetime = size.y / fall * 1.15
	p.preprocess = p.lifetime
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(size.x * 0.5, 2.0, size.z * 0.5)
	p.position = KMath.vec3(pt.get("pos")) + Vector3(0, size.y, 0)
	p.direction = Vector3(0.3, -1, 0.15)
	p.spread = 25.0
	p.gravity = Vector3(0, -fall * 0.25, 0)
	p.initial_velocity_min = fall * 0.6
	p.initial_velocity_max = fall
	p.angular_velocity_min = -180.0
	p.angular_velocity_max = 180.0
	p.angle_min = 0.0
	p.angle_max = 360.0
	p.scale_amount_min = 0.7
	p.scale_amount_max = 1.2
	p.hue_variation_min = -0.03
	p.hue_variation_max = 0.03
	p.color = KMath.color(pt.get("color", "#ffc8dd"))
	var quad := QuadMesh.new()
	quad.size = Vector2(petal, petal * 0.75)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.albedo_texture = _petal_texture()
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	quad.material = mat
	p.mesh = quad
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(p)


static var _petal_tex: ImageTexture


static func _petal_texture() -> ImageTexture:
	if _petal_tex != null:
		return _petal_tex
	# 花瓣形狀：橢圓，尖端有一個小缺口（櫻花花瓣）
	var n := 32
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var u := (x + 0.5) / n * 2.0 - 1.0
			var v := (y + 0.5) / n * 2.0 - 1.0
			var inside := u * u / 0.8 + v * v / 0.98 < 1.0
			var notch := v < -0.6 and absf(u) < 0.18 * (1.0 + (v + 0.6) * 2.0)
			var shade := 1.0 - 0.15 * (v + 1.0) * 0.5
			img.set_pixel(x, y, Color(shade, shade, shade, 1.0 if inside and not notch else 0.0))
	_petal_tex = ImageTexture.create_from_image(img)
	return _petal_tex


static func _place_item(p: Dictionary, items_root: Node3D) -> PickupItem:
	var def := Data.get_item(p.get("item", ""))
	if def.is_empty():
		return null
	var item := PickupItem.spawn(def, p.get("color", ""))
	items_root.add_child(item)
	item.position = KMath.vec3(p.get("pos"))
	if item is Critter and p.has("roam"):
		var r: Array = p["roam"]
		(item as Critter).roam = Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
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
				var colors: Array = def.get("colors", [])
				var color: String = colors[rng.randi() % colors.size()] if not colors.is_empty() else ""
				var item := PickupItem.spawn(def, color)
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
