extends Node3D
## 主角模型預覽：在和遊戲相同的燈光下，從正面、斜側、背面各拍一張。
## 用法（需要畫面）：godot --rendering-driver opengl3 res://tests/character_preview.tscn -- --out 資料夾

var _cam: Camera3D
var _out := "user://preview"


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--out")
	if i >= 0 and i + 1 < args.size():
		_out = args[i + 1]
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("#fbf0df")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(1, 0.97, 0.94)
	e.ambient_light_energy = 0.58
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 35, 0)
	sun.light_energy = 0.48
	sun.shadow_enabled = true
	sun.shadow_bias = 0.12
	sun.shadow_normal_bias = 2.5
	add_child(sun)
	var floor := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(60, 60)
	floor.mesh = pm
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color("#f6eddd")
	floor.material_override = fm
	add_child(floor)
	var pusher := Pusher.new()
	add_child(pusher)
	_cam = Camera3D.new()
	_cam.fov = 30
	add_child(_cam)
	_cam.current = true
	await _shoot(Vector3(0, 2.6, -16), "front")
	await _shoot(Vector3(-10, 4.5, -11), "three_quarter")
	await _shoot(Vector3(0, 3.5, 15), "back")
	get_tree().quit()


func _shoot(pos: Vector3, label: String) -> void:
	_cam.position = pos
	_cam.look_at(Vector3(0, 2.2, 0), Vector3.UP)
	for f in 3:
		await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(_out)
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [_out, label])
