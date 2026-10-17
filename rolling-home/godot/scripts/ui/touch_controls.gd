class_name TouchControls
extends Control
## 觸控操作（iPad、手機、觸控筆電）：
##   左半邊任意位置按住拖曳 = 虛擬搖桿（往上前進、往下後退、左右轉彎）。
##   按住槿寶（或前面的球）= 集氣，放開衝出去；滑鼠按住槿寶也可以。
##   右半邊往上滑 = 衝刺。
##   右側按鈕 = 跳躍（按住跳更高）、轉身、看遠一點（按住）、視角切換、暫停。
## 每根手指自己判斷位置，所以一手推搖桿、一手按按鈕或集氣也不會漏掉。
## 有觸控螢幕時一開始就顯示；沒有的話，第一次摸到螢幕才出現。

signal shown

const STICK_RADIUS := 90.0
const KNOB_RADIUS := 38.0
const BUTTON_RADIUS := 50.0
## 往上滑多少距離（畫面單位）、多快（秒）算衝刺
const SWIPE_DISTANCE := 60.0
const SWIPE_TIME := 0.45
const MOUSE_INDEX := -2

var _stick_index := -1
var _stick_origin := Vector2.ZERO
var _stick_pos := Vector2.ZERO
var _look_index := -1
var _jump_index := -1
var _charge_index := -1
var _swipe_index := -1
var _swipe_start := Vector2.ZERO
var _swipe_time := 0.0
var _swipe_flash := 0.0
var _charged_once := false
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
	# 暫停時收不到放開手指的事件，先全部歸零，免得回來時球自己跑
	if what == NOTIFICATION_PAUSED:
		_reset()


func _reset() -> void:
	_stick_index = -1
	_look_index = -1
	_jump_index = -1
	_charge_index = -1
	_swipe_index = -1
	Controls.touch_stick = Vector2.ZERO
	Controls.touch_look = false
	Controls.touch_jump_held = false
	Controls.touch_charge_held = false
	queue_redraw()


func _layout() -> void:
	var s := size
	_buttons = [
		{"id": "jump", "label": "跳躍", "center": Vector2(s.x - 110.0, s.y - 110.0), "r": BUTTON_RADIUS * 1.25},
		{"id": "turn", "label": "轉身", "center": Vector2(s.x - 262.0, s.y - 78.0), "r": BUTTON_RADIUS * 0.9},
		{"id": "look", "label": "看遠", "center": Vector2(s.x - 110.0, s.y - 262.0), "r": BUTTON_RADIUS * 0.8},
		{"id": "pause", "label": "暫停", "center": Vector2(s.x - 84.0, 214.0), "r": 34.0},
		{"id": "view", "label": "視角", "center": Vector2(s.x - 84.0, 300.0), "r": 34.0},
	]
	queue_redraw()


func _process(delta: float) -> void:
	_swipe_time += delta
	_swipe_flash = maxf(_swipe_flash - delta * 3.0, 0.0)
	if visible and (not _charged_once or _swipe_flash > 0.0 or _charge_index != -1):
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
		elif dr.index == _swipe_index:
			_check_swipe(dr.position)
	elif event is InputEventMouseButton:
		# 滑鼠（電腦）：按住槿寶集氣。觸控模擬出來的滑鼠事件不重複處理
		var mb := event as InputEventMouseButton
		if mb.device == InputEvent.DEVICE_ID_EMULATION or mb.button_index != MOUSE_BUTTON_LEFT:
			return
		if mb.pressed and _charge_index == -1 and _character_hit(mb.position):
			_start_charge(MOUSE_INDEX)
		elif not mb.pressed and _charge_index == MOUSE_INDEX:
			_release(MOUSE_INDEX)


func _press(index: int, pos: Vector2) -> void:
	for b in _buttons:
		if pos.distance_to(b["center"]) <= float(b["r"]) * 1.25:
			match b["id"]:
				"jump":
					_jump_index = index
					Controls.touch_jump = true
					Controls.touch_jump_held = true
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
	if _charge_index == -1 and _character_hit(pos):
		_start_charge(index)
		return
	if pos.x >= size.x * 0.55:
		# 右半邊：可能是往上滑（衝刺）
		_swipe_index = index
		_swipe_start = pos
		_swipe_time = 0.0
		return
	if _stick_index == -1:
		_stick_index = index
		_stick_origin = pos
		_move_stick(pos)


func _start_charge(index: int) -> void:
	_charge_index = index
	_charged_once = true
	Controls.touch_charge_held = true
	queue_redraw()


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
	if index == _charge_index:
		_charge_index = -1
		Controls.touch_charge_held = false
	if index == _swipe_index:
		_swipe_index = -1
	queue_redraw()


func _check_swipe(pos: Vector2) -> void:
	var up := _swipe_start.y - pos.y
	var side := absf(pos.x - _swipe_start.x)
	if up >= SWIPE_DISTANCE and up > side * 1.2 and _swipe_time <= SWIPE_TIME:
		Controls.touch_dash = true
		_swipe_flash = 1.0
		_swipe_index = -1


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


## 槿寶與前面的球在畫面上的位置；按在這個範圍裡就是集氣。
func _character_screen() -> Dictionary:
	var cam := get_viewport().get_camera_3d()
	var p := get_tree().get_first_node_in_group("pusher") as Pusher
	if cam == null or p == null or p.katamari == null or not p.is_inside_tree():
		return {}
	var k := p.katamari
	var h := Pusher.height_for(k.diameter)
	var char_world := p.global_position + Vector3.UP * h * 0.5
	if cam.is_position_behind(char_world) or cam.is_position_behind(k.global_position):
		return {}
	var cs := cam.unproject_position(char_world)
	var bs := cam.unproject_position(k.global_position)
	var edge := cam.unproject_position(k.global_position + cam.global_transform.basis.x * k.radius())
	var ball_r := bs.distance_to(edge)
	var radius := clampf(cs.distance_to(bs) * 0.5 + maxf(ball_r, 45.0), 75.0, 170.0)
	return {"center": (cs + bs) * 0.5, "radius": radius, "char": cs}


func _character_hit(pos: Vector2) -> bool:
	var info := _character_screen()
	return not info.is_empty() and pos.distance_to(info["center"]) <= float(info["radius"])


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
		_text(font, c + Vector2(0, -STICK_RADIUS - 26.0), "按住拖曳", 22, Color(1, 1, 1, 0.7))
	# 右半邊「往上滑：衝刺」提示；滑出衝刺時亮一下
	var sw := Vector2(size.x * 0.78, size.y * 0.42)
	var a := 0.6 + 0.4 * _swipe_flash
	for i in 3:
		var y := sw.y - 24.0 * i - 50.0 * _swipe_flash
		var pts := PackedVector2Array([sw + Vector2(-22, y - sw.y + 12), sw + Vector2(0, y - sw.y - 10), sw + Vector2(22, y - sw.y + 12)])
		draw_polyline(pts, Color(0.1, 0.07, 0.05, 0.45 * a), 9.0, true)
		draw_polyline(pts, Color(1, 1, 1, a * (1.0 - 0.2 * i)), 5.0, true)
	_text(font, sw + Vector2(0, 48), "往上滑 衝刺", 24, Color(1, 1, 1, a))
	# 第一次集氣前，在槿寶旁邊提示
	if not _charged_once:
		var info := _character_screen()
		if not info.is_empty():
			var pulse := 0.5 + 0.5 * sin(Time.get_ticks_msec() * 0.006)
			var c2: Vector2 = info["center"]
			draw_arc(c2, float(info["radius"]) * (0.85 + 0.1 * pulse), 0.0, TAU, 48, Color(1, 0.9, 0.4, 0.35 + 0.35 * pulse), 4.0, true)
			_text(font, c2 + Vector2(0, -float(info["radius"]) - 22.0), "按住槿寶 集氣", 24, Color(1, 0.95, 0.6, 0.85))
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
