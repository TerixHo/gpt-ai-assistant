class_name ChargeFx
extends Node3D
## 集氣與衝刺的特效：球外面的光殼（黃、橘、紅，最後藍色火焰）、藍色火焰粒子、衝刺尾跡。
## 跟著球的位置走，但不跟著球自轉，火焰才會一直往上冒。

const LEVEL_COLORS := [
	Color(1.0, 1.0, 1.0),        # 還沒滿 1 秒：淡淡的白光
	Color(1.0, 0.82, 0.22),      # 黃
	Color(1.0, 0.55, 0.15),      # 橘
	Color(1.0, 0.22, 0.16),      # 紅
	Color(0.12, 0.42, 1.0),      # 藍色火焰
]
const AURA_SHADER := preload("res://assets/shaders/charge_aura.gdshader")

var katamari: Katamari

var _aura: MeshInstance3D
var _aura_mat: ShaderMaterial
var _flames: CPUParticles3D
var _trail: CPUParticles3D
var _shown := 0.0
var _pulse := 0.0


func _ready() -> void:
	name = "ChargeFx"
	top_level = true
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	_aura = MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 1.0
	sphere.height = 2.0
	sphere.radial_segments = 32
	sphere.rings = 16
	_aura.mesh = sphere
	_aura_mat = ShaderMaterial.new()
	_aura_mat.shader = AURA_SHADER
	_aura.material_override = _aura_mat
	_aura.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_aura.visible = false
	add_child(_aura)


## 粒子第一次需要時才建立：Godot 的粒子系統一建立就會從全域亂數抽種子，
## 一開始就建立會打亂貓狗與自動駕駛的亂數序列（自動測試的結果會跟著變）。
func _ensure_particles() -> void:
	if _flames != null:
		return
	_flames = _make_particles(48, 0.55)
	_flames.direction = Vector3.UP
	_flames.spread = 25.0
	_flames.gravity = Vector3(0, 60, 0)
	_flames.color_ramp = _ramp([Color(0.6, 0.88, 1.0, 0.95), Color(0.2, 0.5, 1.0, 0.85), Color(0.05, 0.15, 0.8, 0.0)])
	add_child(_flames)
	_trail = _make_particles(60, 0.45)
	_trail.gravity = Vector3.ZERO
	_trail.spread = 180.0
	add_child(_trail)


func _make_particles(amount: int, lifetime: float) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	# 固定種子：粒子系統預設每次重新開始都會從全域亂數抽種子，
	# 會打亂貓狗與自動駕駛的亂數序列，讓自動測試的結果改變
	p.use_fixed_seed = true
	p.seed = 20261017 + amount
	p.amount = amount
	p.lifetime = lifetime
	p.emitting = false
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE_SURFACE
	var quad := QuadMesh.new()
	quad.size = Vector2.ONE
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_MIX
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = _soft_dot()
	mat.no_depth_test = false
	quad.material = mat
	p.mesh = quad
	p.scale_amount_curve = _shrink_curve()
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return p


func _soft_dot() -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 64
	t.height = 64
	return t


func _shrink_curve() -> Curve:
	var c := Curve.new()
	c.add_point(Vector2(0, 1))
	c.add_point(Vector2(1, 0.15))
	return c


func _ramp(colors: Array) -> Gradient:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.5, 1.0])
	g.colors = PackedColorArray(colors)
	return g


func _process(delta: float) -> void:
	if katamari == null or not is_instance_valid(katamari):
		return
	var center := katamari.get_global_transform_interpolated().origin
	var r := katamari.radius()
	global_position = center
	var charging := katamari.is_charging()
	var level := katamari.charge_level()
	var t := katamari.charge_time()
	# 光殼：集氣時漸強；每升一段閃一下
	var target := 0.0
	if charging:
		target = 0.35 + 0.65 * clampf(t / Katamari.CHARGE_STAGE_TIME, 0.0, 1.0) if level == 0 else 1.0
	_shown = move_toward(_shown, target, delta * (6.0 if target > _shown else 3.0))
	_pulse = maxf(_pulse - delta * 3.0, 0.0)
	_aura.visible = _shown > 0.01
	if _aura.visible:
		var size := r * (1.28 + 0.06 * sin(Time.get_ticks_msec() * 0.02) + 0.12 * _pulse)
		_aura.scale = Vector3.ONE * size
		_aura_mat.set_shader_parameter("glow_color", LEVEL_COLORS[level])
		_aura_mat.set_shader_parameter("intensity", _shown * (0.85 + 0.5 * _pulse) * (1.3 if level == 4 else 1.0))
		_aura_mat.set_shader_parameter("core_color", Color(0.65, 0.9, 1.0) if level == 4 else Color.WHITE)
		_aura_mat.set_shader_parameter("spin", 0.6 + 0.6 * level)
		_aura_mat.set_shader_parameter("flame", 1.0 if level == 4 else 0.0)
	var bursting := katamari.is_bursting()
	if (charging and level == 4) or bursting:
		_ensure_particles()
	if _flames == null:
		return
	# 藍色火焰粒子
	_flames.emitting = charging and level == 4
	_flames.emission_sphere_radius = r * 1.05
	_flames.initial_velocity_min = r * 1.5
	_flames.initial_velocity_max = r * 3.0
	_flames.scale_amount_min = r * 0.5
	_flames.scale_amount_max = r * 0.9
	# 衝刺尾跡：顏色跟著放開時的段數
	_trail.emitting = bursting
	if bursting:
		var c: Color = LEVEL_COLORS[katamari.burst_level()]
		_trail.color = Color(c.r, c.g, c.b, 0.75)
		_trail.emission_sphere_radius = r * 0.9
		_trail.scale_amount_min = r * 0.6
		_trail.scale_amount_max = r * 1.1
		_trail.initial_velocity_min = 0.0
		_trail.initial_velocity_max = r * 0.5


## 升段時閃一下
func pulse() -> void:
	_pulse = 1.0
