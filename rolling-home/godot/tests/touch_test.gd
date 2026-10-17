extends Node
## 觸控操作測試：模擬手指在螢幕上拖曳與按按鈕，確認滾球真的會動、轉身與暫停有反應。
##
## 用法（專案根目錄）：
##   godot --headless --fixed-fps 60 res://tests/touch_test.tscn
## 有畫面時（例如 xvfb-run）會走完整的輸入流程，包含觸控轉滑鼠的模擬。
## 加上 -- --shot PATH（非 headless）可在搖桿按住時截圖。

var _stage: Stage
var _t := 0.0
var _step := 0
var _fails: Array[String] = []
var _start_pos := Vector3.ZERO
var _yaw_before := 0.0
var _shot := ""


func _ready() -> void:
	Game.persist = false
	var args := OS.get_cmdline_user_args()
	var i := args.find("--shot")
	if i >= 0 and i + 1 < args.size():
		_shot = args[i + 1]
	_stage = Stage.new()
	_stage.setup("home_2")
	_stage.skip_intro = true
	add_child(_stage)


func _touch(index: int, pos: Vector2, pressed: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = index
	e.position = pos
	e.pressed = pressed
	_send(e)


func _drag(index: int, pos: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index = index
	e.position = pos
	_send(e)


## 有畫面時走完整的輸入流程；無頭模式不會把模擬事件送進畫面，改成直接交給 viewport
func _send(e: InputEvent) -> void:
	if DisplayServer.get_name() == "headless":
		get_viewport().push_input(e, true)
	else:
		Input.parse_input_event(e)


func _check(ok: bool, what: String) -> void:
	print("[touch] %s：%s" % ["ok" if ok else "失敗", what])
	if not ok:
		_fails.append(what)


func _physics_process(delta: float) -> void:
	_t += delta
	var k := _stage.katamari
	var touch := _stage.hud.find_child("TouchControls", true, false) as Control
	var size := get_viewport().get_visible_rect().size
	match _step:
		0:
			if _t > 1.0:
				_start_pos = k.global_position
				_touch(0, Vector2(200, size.y - 200), true)
				_drag(0, Vector2(200, size.y - 300))
				_step = 1
		1:
			if _t > 3.0:
				_check(touch != null and touch.visible, "第一次觸碰後顯示觸控按鈕")
				_check(Controls.touch_stick.y > 0.9, "往上拖曳＝往前推（%.2f）" % Controls.touch_stick.y)
				var moved := Vector2(k.global_position.x - _start_pos.x, k.global_position.z - _start_pos.z).length()
				_check(moved > 5.0, "按住搖桿 2 秒滾球有前進（%.1f 公分）" % moved)
				if _shot != "":
					_save_shot()
				_touch(0, Vector2(200, size.y - 300), false)
				_yaw_before = _stage.cam.yaw
				# 轉身按鈕（右下）
				_touch(1, Vector2(size.x - 216, size.y - 84), true)
				_touch(1, Vector2(size.x - 216, size.y - 84), false)
				_step = 2
		2:
			if _t > 4.0:
				_check(Controls.touch_stick == Vector2.ZERO, "放開手指搖桿歸零")
				var turned := absf(wrapf(_stage.cam.yaw - _yaw_before, -PI, PI))
				_check(turned > 2.8, "轉身按鈕讓鏡頭轉了約半圈（%.2f 弧度）" % turned)
				# 看遠按鈕要按住才有效
				_touch(2, Vector2(size.x - 96, size.y - 290), true)
				_step = 3
		3:
			if _t > 4.3:
				_check(Controls.touch_look, "按住看遠按鈕")
				_touch(2, Vector2(size.x - 96, size.y - 290), false)
				_touch(3, Vector2(size.x - 84, 214), true)
				_touch(3, Vector2(size.x - 84, 214), false)
				_step = 4
		4:
			if _t > 4.6:
				_check(not Controls.touch_look, "放開看遠按鈕")
				_check(get_tree().paused, "暫停按鈕讓遊戲暫停")
				get_tree().paused = false
				_finish()


func _save_shot() -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(_shot)
	print("[touch] 截圖：", _shot)


func _finish() -> void:
	_step = 99
	if _fails.is_empty():
		print("[touch] PASS")
		get_tree().quit(0)
	else:
		printerr("[touch] FAIL：", ", ".join(_fails))
		get_tree().quit(1)
