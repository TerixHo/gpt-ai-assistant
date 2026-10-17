class_name ProcTex
## 程式產生的地板材質，免外部貼圖即可有質感：
## 室內：wood 木地板、tatami 榻榻米、tile 磁磚、carpet 地毯、jointmat 巧拼、terrazzo 磨石子、mosaic 馬賽克小磁磚。
## 室外：asphalt 柏油、gravel 碎石、soil 泥土、sand 沙、grass 草地、paddy 稻田（秧苗與水）、water 水面、
##       concrete 水泥（伸縮縫）、paving 人行道地磚、brick 紅磚、roof_tile 屋瓦。
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
		"jointmat":
			img = _jointmat()
		"terrazzo":
			img = _terrazzo(base)
		"mosaic":
			img = _mosaic(base)
		"asphalt":
			img = _speckle(base, 0.07, 0.02, 21)
		"gravel":
			img = _speckle(base, 0.16, 0.12, 22)
		"soil":
			img = _speckle(base, 0.08, 0.05, 23)
		"sand":
			img = _speckle(base, 0.05, 0.03, 24)
		"grass":
			img = _grass(base)
		"paddy":
			img = _paddy(base)
		"water":
			img = _water(base)
		"concrete":
			img = _concrete(base)
		"paving":
			img = _paving(base)
		"brick":
			img = _brick(base)
		"roof_tile":
			img = _roof_tile(base)
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


## 兒童巧拼地墊：粉彩方塊拼接（一個重複單位含 2×2 塊）。
static func _jointmat() -> Image:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var colors := [Color("#ffadad"), Color("#a0c4ff"), Color("#caffbf"), Color("#fdffb6")]
	for y in n:
		for x in n:
			var c: Color = colors[(x / 64) + (y / 64) * 2]
			var lx := x % 64
			var ly := y % 64
			# 拼接處的鋸齒線
			if lx < 2 or ly < 2 or (lx < 5 and (ly / 8) % 2 == 0) or (ly < 5 and (lx / 8) % 2 == 0):
				c = c.darkened(0.15)
			img.set_pixel(x, y, c)
	return img


## 雜點：柏油、碎石、泥土、沙。amount 是明暗起伏，spots 是較大顆粒的比例。
static func _speckle(base: Color, amount: float, spots: float, seed_value: int) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	for y in n:
		for x in n:
			var v := rng.randf_range(-amount, amount)
			if rng.randf() < spots:
				v += rng.randf_range(-amount, amount) * 2.0
			img.set_pixel(x, y, base.lightened(v) if v > 0 else base.darkened(-v))
	return img


## 磨石子：底色加上大小不一的彩色碎石（台灣老房子的地板）。
static func _terrazzo(base: Color) -> Image:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	img.fill(base)
	var rng := RandomNumberGenerator.new()
	rng.seed = 31
	var chips := [base.darkened(0.35), base.lightened(0.35), Color("#9c6644"), Color("#6c757d"), Color("#e9edc9"), Color("#b08968")]
	for i in 260:
		var cx := rng.randi_range(0, n - 1)
		var cy := rng.randi_range(0, n - 1)
		var r := rng.randf_range(0.8, 3.2)
		var c: Color = chips[rng.randi() % chips.size()]
		for dy in range(-4, 5):
			for dx in range(-4, 5):
				if dx * dx + dy * dy * 1.3 <= r * r:
					img.set_pixel(posmod(cx + dx, n), posmod(cy + dy, n), c)
	return img


## 馬賽克小磁磚（浴室、廁所）：8×8 小方塊，每塊顏色略有不同。
static func _mosaic(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 32
	var cell := 8
	var tints: Array[float] = []
	for i in (n / cell) * (n / cell):
		tints.append(rng.randf_range(-0.08, 0.08))
	for y in n:
		for x in n:
			var t := tints[(y / cell) * (n / cell) + x / cell]
			var c := base.lightened(t) if t > 0 else base.darkened(-t)
			if x % cell == 0 or y % cell == 0:
				c = base.darkened(0.25)
			img.set_pixel(x, y, c)
	return img


static func _grass(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 33
	for y in n:
		for x in n:
			var v := rng.randf_range(-0.06, 0.06) + sin(x * 0.4 + y * 0.13) * 0.03
			img.set_pixel(x, y, base.lightened(v) if v > 0 else base.darkened(-v))
	# 零星的草葉
	for i in 90:
		var x := rng.randi_range(0, n - 1)
		var y := rng.randi_range(0, n - 1)
		for k in 3:
			img.set_pixel(posmod(x + k / 2, n), posmod(y - k, n), base.lightened(0.18))
	return img


## 稻田：一排排秧苗（綠）中間露出水面（藍綠）。一個重複單位含 4 排。
static func _paddy(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var water := Color("#7fb8b0")
	var rng := RandomNumberGenerator.new()
	rng.seed = 34
	for y in n:
		for x in n:
			var row := x % 16
			var c := water.lightened(rng.randf_range(0.0, 0.06))
			if row >= 4 and row <= 11:
				var clump := (y % 8) < 6
				c = base.lightened(rng.randf_range(-0.05, 0.08)) if clump else water
			img.set_pixel(x, y, c)
	return img


static func _water(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	for y in n:
		for x in n:
			var w := sin((x + sin(y * 0.3) * 4.0) * 0.35) * 0.5 + 0.5
			var c := base.lightened(0.18) if w > 0.93 else base.lightened(w * 0.05)
			img.set_pixel(x, y, c)
	return img


## 水泥：一個重複單位兩塊板，板縫顏色深一點。
static func _concrete(base: Color) -> Image:
	var img := _speckle(base, 0.04, 0.03, 35)
	var n := img.get_width()
	for i in n:
		for k in [0, 1, n / 2, n / 2 + 1]:
			img.set_pixel(i, k, base.darkened(0.25))
			img.set_pixel(k, i, base.darkened(0.25))
	return img


## 人行道地磚：交錯的長方形磚，兩種顏色。
static func _paving(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var alt := base.darkened(0.12)
	for y in n:
		for x in n:
			var row := y / 16
			var xx := x + (8 if row % 2 == 1 else 0)
			var c := base if ((xx / 32) + row) % 2 == 0 else alt
			if y % 16 == 0 or xx % 32 == 0:
				c = base.darkened(0.35)
			img.set_pixel(x, y, c)
	return img


static func _brick(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 36
	var mortar := Color("#d8d2c4")
	for y in n:
		for x in n:
			var row := y / 8
			var xx := x + (8 if row % 2 == 1 else 0)
			var c := base.lightened(rng.randf_range(-0.04, 0.04))
			if y % 8 == 0 or xx % 16 == 0:
				c = mortar
			img.set_pixel(x, y, c)
	return img


## 屋瓦：一排排弧形瓦片，下緣有陰影。
static func _roof_tile(base: Color) -> Image:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	for y in n:
		for x in n:
			var t := float(y % 16) / 16.0
			var arc := absf(sin(float(x % 16) / 16.0 * PI))
			var c := base.lightened(0.1 * arc) if t < 0.8 else base.darkened(0.25)
			img.set_pixel(x, y, c)
	return img
