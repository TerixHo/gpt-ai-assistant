class_name ProcTex
## 程式產生的地板材質（木地板、榻榻米、磁磚、地毯），免外部貼圖即可有質感。
## 之後可用 Blender 烘焙或手繪貼圖替換，材質介面不變。

static var _cache: Dictionary = {}


static func clear_cache() -> void:
	_cache.clear()


## repeat_cm：圖樣在世界中重複一次的長度（公分）
static func floor_material(pattern: String, base_hex: String, repeat_cm := 90.0) -> StandardMaterial3D:
	var key := "%s|%s|%.1f" % [pattern, base_hex, repeat_cm]
	if _cache.has(key):
		return _cache[key]
	var base := KMath.color(base_hex)
	var img: Image
	match pattern:
		"wood":
			img = _wood(base)
		"tatami":
			img = _tatami(base)
		"tile":
			img = _tile(base)
		"carpet":
			img = _carpet(base)
		_:
			img = Image.create(4, 4, false, Image.FORMAT_RGB8)
			img.fill(base)
	img.generate_mipmaps()
	var m := StandardMaterial3D.new()
	m.albedo_texture = ImageTexture.create_from_image(img)
	m.roughness = 1.0
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE / repeat_cm
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_cache[key] = m
	return m


static func _wood(base: Color) -> Image:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var planks := 6
	var plank_h := n / planks
	for p in planks:
		var tint := rng.randf_range(-0.06, 0.06)
		var offset := rng.randi_range(0, n)
		for y in range(p * plank_h, (p + 1) * plank_h):
			for x in n:
				var grain := sin((x + offset) * 0.15 + sin(y * 0.9 + p) * 2.0) * 0.03
				var c := base.lightened(tint + grain) if tint + grain > 0 else base.darkened(-(tint + grain))
				if y == p * plank_h or (x + offset) % n == 0:
					c = base.darkened(0.25)
				img.set_pixel(x, y, c)
	return img


static func _tatami(base: Color) -> Image:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var border := Color(0.18, 0.26, 0.2)
	for y in n:
		for x in n:
			var weave := 0.04 if (y / 2) % 2 == 0 else -0.02
			var c := base.lightened(weave) if weave > 0 else base.darkened(-weave)
			if x < 6 or x >= n - 6:
				c = border
			img.set_pixel(x, y, c)
	return img


static func _tile(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	for y in n:
		for x in n:
			var grout := x % 32 < 2 or y % 32 < 2
			img.set_pixel(x, y, base.darkened(0.3) if grout else base)
	return img


static func _carpet(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for y in n:
		for x in n:
			var v := rng.randf_range(-0.05, 0.05)
			var edge := x < 4 or y < 4 or x >= n - 4 or y >= n - 4
			var c := base.darkened(0.2) if edge else (base.lightened(v) if v > 0 else base.darkened(-v))
			img.set_pixel(x, y, c)
	return img
