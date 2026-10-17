extends Node
## 集氣特效截圖：按住 Shift，在黃、橘、紅、藍色火焰各拍一張，放開後再拍衝刺。
## 用法（需要畫面）：godot --rendering-driver opengl3 --fixed-fps 60 res://tests/charge_preview.tscn -- --out 資料夾 [--stage home_2]

var _stage: Stage
var _frame := 0
var _out := "user://charge"
var _shots := {150: "1_yellow", 210: "2_orange", 270: "3_red", 335: "4_blue", 352: "5_launch", 375: "6_speed"}


func _ready() -> void:
	Game.persist = false
	var args := OS.get_cmdline_user_args()
	var i := args.find("--out")
	if i >= 0 and i + 1 < args.size():
		_out = args[i + 1]
	var st := "home_2"
	i = args.find("--stage")
	if i >= 0 and i + 1 < args.size():
		st = args[i + 1]
	DirAccess.make_dir_recursive_absolute(_out)
	_stage = Stage.new()
	_stage.setup(st)
	_stage.skip_intro = true
	add_child(_stage)


func _physics_process(_delta: float) -> void:
	_frame += 1
	if _frame == 60:
		Input.action_press("kb_shift")
	if _frame == 340:
		Input.action_release("kb_shift")
	if _shots.has(_frame):
		_shot(_shots[_frame])
	if _frame > 380:
		get_tree().quit()


func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [_out, label])
