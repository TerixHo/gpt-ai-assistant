class_name TouchControls
extends Control
## 觸控操作（手機、平板、觸控筆電）：
##   左半邊任意位置按住拖曳 = 虛擬搖桿（往上前進、往下後退、左右轉彎）。
##   右側按鈕 = 跳躍（按住跳更高）、衝刺、轉身、看遠一點（按住）、視角切換、暫停。
## 每根手指自己判斷位置，所以一手推搖桿、一手按按鈕也不會漏掉。
## 有觸控螢幕時一開始就顯示；沒有的話，第一次摸到螢幕才出現。

signal shown

const STICK_RADIUS := 90.0
const KNOB_RADIUS := 38.0
const BUTTON_RADIUS := 50.0

var _stick_index := -1
var _stick_origin := Vector2.ZERO
var _stick_pos := Vector2.ZERO
var _look_index := -1
var _jump_index := -1
var _buttons: Array[Dictionary] = []


func _ready() -> void:
	name = "TouchControls"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = DisplayServer.is_touchscreen_available()
	Controls.touch_active = visible
	resized.connect(_layout)
	_layout()


func _exit_tree() -> void:
	_reset()


func _notification(what: int) -> void:
	# 暫停時收不到放開手指的事件，先把搖桿歸零，免得回來時球自己跑
	if what == NOTIFICATION_PAUSED:
		_reset()


func _reset() -> void:
	_stick_index = -1
	_look_index = -1
	_jump_index = -1
	Controls.touch_stick = Vector2.ZERO
	Controls.touch_look = false
	Controls.touch_jump_held = false
	queue_redraw()


func _layout() -> void:
	var s := size
	_buttons = [
		{"id": "jump", "label": "跳躍", "center": Vector2(s.x - 104.0, s.y - 104.0), "r": BUTTON_RADIUS * 1.2},
		{"id": "dash", "label": "衝刺", "center": Vector2(s.x - 246.0, s.y - 72.0), "r": BUTTON_RADIUS * 0.9},
		{"id": "turn", "label": "轉身", "center": Vector2(s.x - 104.0, s.y - 250.0), "r": BUTTON_RADIUS * 0.9},
		{"id": "look", "label": "看遠", "center": Vector2(s.x - 236.0, s.y - 196.0), "r": BUTTON_RADIUS * 0.75},
		{"id": "pause", "label": "暫停", "center": Vector2(s.x - 84.0, 214.0), "r": 34.0},
		{"id": "view", "label": "視角", "center": Vector2(s.x - 84.0, 300.0), "r": 34.0},
	]
	queue_redraw()


func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		if t.pressed:
			if not visible:
				visible = true
				Controls.touch_active = true
				shown.emit()
			_press(t.index, t.position)
		else:
			_release(t.index)
	elif event is InputEventScreenDrag:
		var dr := event as InputEventScreenDrag
		if dr.index == _stick_index:
			_move_stick(dr.position)


func _press(index: int, pos: Vector2) -> void:
	for b in _buttons:
		if pos.distance_to(b["center"]) <= float(b["r"]) * 1.25:
			match b["id"]:
				"jump":
					_jump_index = index
					Controls.touch_jump = true
					Controls.touch_jump_held = true
				"dash":
					Controls.touch_dash = true
				"turn":
					Controls.touch_turn = true
				"look":
					_look_index = index
					Controls.touch_look = true
				"pause":
					_send_pause()
				"view":
					Controls.touch_view_cycle = true
			queue_redraw()
			return
	if _stick_index == -1 and pos.x < size.x * 0.55:
		_stick_index = index
		_stick_origin = pos
		_move_stick(pos)


func _release(index: int) -> void:
	if index == _stick_index:
		_stick_index = -1
		Controls.touch_stick = Vector2.ZERO
	if index == _look_index:
		_look_index = -1
		Controls.touch_look = false
	if index == _jump_index:
		_jump_index = -1
		Controls.touch_jump_held = false
	queue_redraw()


func _move_stick(pos: Vector2) -> void:
	var off := pos - _stick_origin
	# 手指拉超過範圍時，搖桿中心跟著手指走，往回推時馬上有反應
	if off.length() > STICK_RADIUS:
		_stick_origin = pos - off.normalized() * STICK_RADIUS
		off = pos - _stick_origin
	_stick_pos = pos
	var v := off / STICK_RADIUS
	# 中心附近一點點晃動不算數
	if v.length() < 0.12:
		v = Vector2.ZERO
	Controls.touch_stick = Vector2(v.x, -v.y)
	queue_redraw()


func _send_pause() -> void:
	var down := InputEventAction.new()
	down.action = "pause"
	down.pressed = true
	Input.parse_input_event(down)
	var up := InputEventAction.new()
	up.action = "pause"
	up.pressed = false
	Input.parse_input_event.call_deferred(up)


func _draw() -> void:
	var font := get_theme_default_font()
	if _stick_index >= 0:
		draw_circle(_stick_origin, STICK_RADIUS, Color(1, 1, 1, 0.14))
		draw_arc(_stick_origin, STICK_RADIUS, 0.0, TAU, 48, Color(1, 1, 1, 0.5), 3.0, true)
		var knob := _stick_origin + (_stick_pos - _stick_origin).limit_length(STICK_RADIUS)
		draw_circle(knob, KNOB_RADIUS, Color(1, 1, 1, 0.6))
	else:
		# 沒按住時，在左下角畫一個淡淡的提示
		var c := Vector2(170.0, size.y - 170.0)
		draw_arc(c, STICK_RADIUS, 0.0, TAU, 48, Color(1, 1, 1, 0.22), 3.0, true)
		draw_circle(c, KNOB_RADIUS, Color(1, 1, 1, 0.16))
		_text(font, c + Vector2(0, STICK_RADIUS + 34.0), "按住拖曳", 22, Color(1, 1, 1, 0.55))
	for b in _buttons:
		var held: bool = (b["id"] == "look" and _look_index >= 0) or (b["id"] == "jump" and _jump_index >= 0)
		var r := float(b["r"])
		draw_circle(b["center"], r, Color(0.16, 0.12, 0.1, 0.62 if held else 0.38))
		draw_arc(b["center"], r, 0.0, TAU, 40, Color(1, 1, 1, 0.65), 3.0, true)
		_text(font, b["center"], str(b["label"]), 26 if r >= 40.0 else 20, Color.WHITE)


func _text(font: Font, center: Vector2, text: String, font_size: int, color: Color) -> void:
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	var pos := center + Vector2(-w * 0.5, font.get_ascent(font_size) * 0.5 - font.get_descent(font_size) * 0.5)
	draw_string_outline(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, 6, Color(0.1, 0.07, 0.05, 0.7))
	draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
