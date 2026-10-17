extends Node
## 觸控操作測試：模擬手指在螢幕上拖曳與按按鈕，確認滾球真的會動、轉身、跳躍、視角、暫停、
## 往上滑衝刺、搖桿放開後再按住集氣、卡住時「回到中間」按鈕都有反應。
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
var _vars_charge_pos := Vector2.ZERO


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


func _center(touch: Control, id: String) -> Vector2:
	for btn in touch.get("_buttons"):
		if btn["id"] == id:
			return btn["center"]
	return Vector2.ZERO


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
				var turn := _center(touch, "turn")
				_touch(1, turn, true)
				_touch(1, turn, false)
				_step = 2
		2:
			if _t > 4.0:
				_check(Controls.touch_stick == Vector2.ZERO, "放開手指搖桿歸零")
				var turned := absf(wrapf(_stage.cam.yaw - _yaw_before, -PI, PI))
				_check(turned > 2.8, "轉身按鈕讓鏡頭轉了約半圈（%.2f 弧度）" % turned)
				_touch(2, _center(touch, "look"), true)
				_step = 3
		3:
			if _t > 4.3:
				_check(Controls.touch_look, "按住看遠按鈕")
				_touch(2, _center(touch, "look"), false)
				_start_pos = k.global_position
				_touch(4, _center(touch, "jump"), true)
				_step = 4
		4:
			if _t > 4.45:
				_check(k.global_position.y > _start_pos.y + 3.0, "跳躍按鈕讓球跳起來（升高 %.1f 公分）" % (k.global_position.y - _start_pos.y))
				_touch(4, _center(touch, "jump"), false)
				_step = 5
		5:
			if _t > 5.6:
				_check(not Controls.touch_jump_held, "放開跳躍按鈕")
				_touch(5, _center(touch, "view"), true)
				_touch(5, _center(touch, "view"), false)
				_step = 6
		6:
			if _t > 5.8:
				_check(_stage.cam.view == 4, "視角按鈕切到下一個視角（現在 %d）" % _stage.cam.view)
				_check(not Controls.touch_look, "放開看遠按鈕")
				_touch(3, _center(touch, "pause"), true)
				_touch(3, _center(touch, "pause"), false)
				_step = 7
		7:
			if _t > 6.1:
				_check(get_tree().paused, "暫停按鈕讓遊戲暫停")
				get_tree().paused = false
				# 右半邊往上滑：衝刺
				var from := Vector2(size.x * 0.8, size.y * 0.6)
				_touch(6, from, true)
				_drag(6, from + Vector2(5, -40))
				_drag(6, from + Vector2(8, -95))
				_step = 8
		8:
			if _t > 6.25:
				_check(k.is_dashing(), "右半邊往上滑：衝刺")
				_touch(6, Vector2(size.x * 0.8, size.y * 0.6 - 95), false)
				_step = 9
		9:
			if _t > 7.4:
				# 搖桿點一下放開，馬上再按住：集氣
				_vars_charge_pos = Vector2(220, size.y - 220)
				_touch(7, _vars_charge_pos, true)
				_step = 10
		10:
			if _t > 7.5:
				_touch(7, _vars_charge_pos, false)
				_step = 11
		11:
			if _t > 7.6:
				_touch(8, _vars_charge_pos, true)
				_start_pos = k.global_position
				_step = 12
		12:
			if _t > 9.95:
				_check(k.is_charging() and k.charge_level() == 2, "搖桿放開再按住 2.3 秒：集氣到第 2 段橘光（第 %d 段）" % k.charge_level())
				var crept := Vector2(k.global_position.x - _start_pos.x, k.global_position.z - _start_pos.z).length()
				_check(crept > 0.5, "集氣時主角慢慢往前推（%.1f 公分）" % crept)
				_touch(8, _vars_charge_pos, false)
				_step = 13
		13:
			if _t > 10.05:
				_check(k.is_bursting() and not k.is_charging(), "放開搖桿：衝出去")
				# 卡住時出現「回到中間」按鈕，按下去回到救援點
				_stage.hud.show_rescue(true)
				_check(bool(touch.get("rescue_visible")), "卡住時顯示回到中間按鈕")
				var btn: Vector2 = touch.call("button_center", "rescue")
				_touch(9, btn, true)
				_touch(9, btn, false)
				_step = 14
		14:
			if _t > 10.3:
				var p := k.global_position
				var rescue_pos: Vector3 = _stage.get("_rescue_pos")
				_check(Vector2(p.x - rescue_pos.x, p.z - rescue_pos.z).length() < 5.0, "按回到中間：球回到救援點")
				_check(not bool(touch.get("rescue_visible")), "回到中間後按鈕消失")
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
