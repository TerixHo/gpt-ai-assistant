extends Node
## 介面截圖：標題與結算畫面（需非 headless 模式）。
## 用法：godot --rendering-driver opengl3 res://tests/screenshot_ui.tscn -- --shot-dir PATH [--title-wait 秒]
## 標題背景是示範關卡，--title-wait 可以等它滾一陣子再拍。

var _main: Node
var _dir := "user://shots"
var _t := 0.0
var _step := 0
var _title_wait := 1.2


func _ready() -> void:
	Game.persist = false
	var args := OS.get_cmdline_user_args()
	var i := args.find("--shot-dir")
	if i >= 0 and i + 1 < args.size():
		_dir = args[i + 1]
	i = args.find("--title-wait")
	if i >= 0 and i + 1 < args.size():
		_title_wait = float(args[i + 1])
	DirAccess.make_dir_recursive_absolute(_dir)
	_main = load("res://scenes/main.tscn").instantiate()
	add_child(_main)


func _process(delta: float) -> void:
	_t += delta
	if _t < (_title_wait if _step == 0 else 1.2):
		return
	_t = 0.0
	match _step:
		0:
			await _shot("ui_title")
			_main.show_results({
				"stage_id": "home", "diameter_cm": 132.0, "goal_cm": 100.0, "success": true,
				"items": {"bead_6": 40, "bead_8": 25, "marble": 3, "eraser": 1, "minicar": 1, "dinosaur": 1}, "count": 168, "time_total": 240.0, "time_to_goal": 105.0,
				"comet_sec": 100.0, "top_items": ["dinosaur", "minicar", "gacha_capsule", "glue_stick", "eraser"],
				"grades": Data.get_stage("home")["grades"]})
		1:
			await _shot("ui_results")
			_main.show_collection()
		2:
			await _shot("ui_collection")
			get_tree().quit()
	_step += 1


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [_dir, name]
	get_viewport().get_texture().get_image().save_png(path)
	print("[shot] ", ProjectSettings.globalize_path(path))
