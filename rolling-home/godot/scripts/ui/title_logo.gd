class_name TitleLogo
extends SubViewportContainer
## 標題畫面的 3D 大標題「Gǔn A Gǔn A」：每個字母是有厚度的立體字，輪流上下彈跳、
## 左右擺動，每隔幾秒其中一個字母翻滾一圈（像在滾）。畫在獨立的透明 3D 畫面裡，
## 疊在背景的遊戲畫面上，不會被場景裡的家具擋住。

const TEXT := "Gǔn A Gǔn A"
const FONT := preload("res://assets/fonts/Huninn-Regular.ttf")
## 字母顏色：槿寶的淡紫、藍紫，加上黃、粉，呼應遊戲裡的小玩具
const COLORS := [Color("#ffc93c"), Color("#c9a6ff"), Color("#7fb8ff"), Color("#ff8fb8")]
const FONT_SIZE := 128
const PIXEL := 0.01
const DEPTH := 0.32

var text := TEXT
var _letters: Array[Node3D] = []
var _t := 0.0
var _flip_index := -1
var _flip_t := 0.0
var _next_flip := 1.5
var _cam: Camera3D


func _ready() -> void:
	name = "TitleLogo"
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vp := SubViewport.new()
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_CLEAR_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(1, 0.97, 0.95)
	e.ambient_light_energy = 0.75
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e
	vp.add_child(env)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, -25, 0)
	key.light_energy = 0.9
	vp.add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-10, 140, 0)
	fill.light_energy = 0.35
	fill.light_color = Color(0.8, 0.85, 1.0)
	vp.add_child(fill)
	_cam = Camera3D.new()
	_cam.fov = 30.0
	_cam.position = Vector3(0, 0.15, 6.2)
	vp.add_child(_cam)
	_build_letters(vp)


func _build_letters(parent: Node) -> void:
	var root := Node3D.new()
	parent.add_child(root)
	# 先量好每個字的寬度，整串置中
	var widths: Array[float] = []
	var total := 0.0
	for ch in TEXT:
		var w := FONT.get_string_size(ch, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT_SIZE).x * PIXEL
		if ch == " ":
			w *= 0.8
		widths.append(w)
		total += w + 0.06
	var x := -total * 0.5
	var color_i := 0
	for i in TEXT.length():
		var ch := TEXT[i]
		var w: float = widths[i]
		if ch != " ":
			var pivot := Node3D.new()
			pivot.position = Vector3(x + w * 0.5, 0, 0)
			root.add_child(pivot)
			# 深色的厚底當作描邊與陰影，讓字在任何背景上都清楚
			pivot.add_child(_letter_mesh(ch, Color("#3a2650"), DEPTH * 1.6, Vector3(0.05, -0.06, -0.12), 1.0))
			pivot.add_child(_letter_mesh(ch, COLORS[color_i % COLORS.size()], DEPTH, Vector3.ZERO, 1.0))
			_letters.append(pivot)
			color_i += 1
		x += w + 0.06
	# 依寬度調整鏡頭距離，標題剛好塞滿畫面寬度的九成
	_fit_camera(total)


func _fit_camera(total_width: float) -> void:
	var aspect := maxf(size.x / maxf(size.y, 1.0), 0.5)
	var half_fov := deg_to_rad(_cam.fov * 0.5)
	var need := (total_width * 0.5 / 0.88) / (tan(half_fov) * aspect)
	_cam.position.z = maxf(need, 4.0)


func _letter_mesh(ch: String, color: Color, depth: float, offset: Vector3, _scale: float) -> MeshInstance3D:
	var tm := TextMesh.new()
	tm.text = ch
	tm.font = FONT
	tm.font_size = FONT_SIZE
	tm.pixel_size = PIXEL
	tm.depth = depth
	tm.curve_step = 0.5
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.45
	mat.rim_enabled = true
	mat.rim = 0.4
	mat.rim_tint = 0.3
	tm.material = mat
	var mi := MeshInstance3D.new()
	mi.mesh = tm
	mi.position = offset
	return mi


func _process(delta: float) -> void:
	_t += delta
	_next_flip -= delta
	if _next_flip <= 0.0 and not _letters.is_empty():
		_flip_index = (_flip_index + 1 + int(_t * 7.0) % 3) % _letters.size()
		_flip_t = 0.0
		_next_flip = 1.6
	if _flip_index >= 0:
		_flip_t += delta
	for i in _letters.size():
		var l := _letters[i]
		var phase := _t * 3.2 - i * 0.55
		l.position.y = maxf(sin(phase), 0.0) * 0.22
		l.rotation.z = sin(phase - 0.6) * 0.07
		l.rotation.x = 0.0
		if i == _flip_index and _flip_t < 0.7:
			# 翻滾一圈（往前滾）
			var k := ease(_flip_t / 0.7, -2.0)
			l.rotation.x = -TAU * k
			l.position.y += sin(PI * _flip_t / 0.7) * 0.35
	if size.x > 0.0:
		_fit_camera_from_letters()


func _fit_camera_from_letters() -> void:
	if _letters.size() < 2:
		return
	var span := _letters[-1].position.x - _letters[0].position.x + 0.9
	_fit_camera(span)
