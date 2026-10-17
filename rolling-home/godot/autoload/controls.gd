extends Node
## 操作中樞：把手把／鍵盤輸入轉換為原作風格的「雙搖桿坦克式」指令。
##
## 規則（雙搖桿）：
##   兩桿同推前 = 前進；同推後 = 後退；同推左右 = 平移。
##   左桿前右桿後 = 原地右轉；反之左轉。
##   兩桿上下快速交替 = 王子衝刺；同時按下兩桿（L3+R3）= 180 度迴轉。
## 簡化模式（預設，適合小學生）：鍵盤 W/S 前後、A/D 轉向；手把左桿上下前後、左右轉向，右桿左右也能轉向。
## 簡化模式會先轉成同樣的虛擬雙搖桿，後段邏輯完全共用。
## 其他按鍵：空白鍵跳躍（按住跳比較高）、Shift 輕按衝刺、按住 Shift 集氣（放開衝出去）、連按兩下 Shift 轉身、E 第一人稱環視、
## 數字鍵 1 到 5 切換視角（1 第一人稱、2 近、3 標準、4 遠、5 正面）、Tab 看遠一點、Esc 暫停。

class Drive:
	## x 為向右平移、y 為前進（相機座標），長度不超過 1
	var move := Vector2.ZERO
	## 正值為向右轉（俯視順時針）
	var turn := 0.0
	var dash := false
	var quick_turn := false
	var look_up := false
	var jump := false
	var jump_held := false
	## 集氣中（按住槿寶、按住 Shift 或手把 X），放開時衝出去
	var charge := false
	## 1 到 5：切換到指定視角；-1：切到下一個視角；0：不變
	var view := 0
	var free_look_toggle := false
	## 第一人稱環視時用來看上下左右（x 向右、y 向上）
	var look := Vector2.ZERO
	var left := Vector2.ZERO
	var right := Vector2.ZERO

const DEADZONE := 0.2
const DASH_STICK_THRESHOLD := 0.6
const DASH_FLIPS_NEEDED := 4
const DASH_FLIP_WINDOW := 0.4
## 連按兩下 Shift 的間隔上限（秒）。單按 Shift 要等這段時間確認沒有第二下才衝刺
const DOUBLE_TAP_WINDOW := 0.28
## 按住超過這個時間就開始集氣（輕按是衝刺）
const HOLD_TO_CHARGE := 0.25
## 鍵盤轉向的漸進速度（每秒），避免一按下去鏡頭就瞬間全速轉
const TURN_RAMP_UP := 7.0
const TURN_RAMP_DOWN := 10.0

## 測試與展示用：設定後完全取代硬體輸入
var override_drive: Drive = null

## 觸控（手機、平板）：由 TouchControls 寫入。觸控一律是簡單操作：上下前進後退、左右轉彎
var touch_active := false
var touch_stick := Vector2.ZERO
var touch_dash := false
var touch_turn := false
var touch_look := false
var touch_jump := false
var touch_jump_held := false
var touch_view_cycle := false
## 觸控或滑鼠按住槿寶（由 TouchControls 寫入）
var touch_charge_held := false

var _flip_count := 0
var _flip_timer := 0.0
var _last_flip_sign := 0
var _stick_click_latch := false
## Shift：0 沒按、1 剛按下（還不知道是輕按還是按住）、2 按住集氣中、3 放開等第二下
var _shift_state := 0
var _shift_t := 0.0
var _pad_x_t := -1.0
var _turn := 0.0


func _ready() -> void:
	_register_actions()


func _register_actions() -> void:
	_add_keys("kb_forward", [KEY_W])
	_add_keys("kb_back", [KEY_S])
	_add_keys("kb_left", [KEY_A])
	_add_keys("kb_right", [KEY_D])
	_add_keys("kb_r_forward", [KEY_UP, KEY_I])
	_add_keys("kb_r_back", [KEY_DOWN, KEY_K])
	_add_keys("kb_r_left", [KEY_LEFT, KEY_J])
	_add_keys("kb_r_right", [KEY_RIGHT, KEY_L])
	_add_keys("kb_shift", [KEY_SHIFT])
	_add_keys("dash", [], [JOY_BUTTON_X])
	_add_keys("quick_turn", [], [JOY_BUTTON_Y])
	_add_keys("jump", [KEY_SPACE], [JOY_BUTTON_A])
	_add_keys("look_up", [KEY_TAB], [JOY_BUTTON_RIGHT_SHOULDER])
	_add_keys("free_look", [KEY_E], [JOY_BUTTON_LEFT_SHOULDER])
	_add_keys("view_next", [KEY_V], [JOY_BUTTON_BACK])
	for i in 5:
		_add_keys("view_%d" % (i + 1), [KEY_1 + i, KEY_KP_1 + i])
	_add_keys("pause", [KEY_ESCAPE, KEY_P], [JOY_BUTTON_START])
	_add_keys("toggle_scheme", [KEY_F2])


func _add_keys(action: String, keys: Array, buttons: Array = []) -> void:
	if InputMap.has_action(action):
		return
	InputMap.add_action(action, 0.2)
	for k in keys:
		var ev := InputEventKey.new()
		ev.physical_keycode = k
		InputMap.action_add_event(action, ev)
	for b in buttons:
		var jb := InputEventJoypadButton.new()
		jb.button_index = b
		InputMap.action_add_event(action, jb)


func is_simple() -> bool:
	return Game.settings.get("control_scheme", "simple") == "simple"


func scheme_label() -> String:
	return "簡單操作" if is_simple() else "雙搖桿（原作式）"


func toggle_scheme() -> void:
	Game.settings["control_scheme"] = "classic" if is_simple() else "simple"
	Game.save()


## 每個物理幀呼叫一次。
func read(delta: float) -> Drive:
	if override_drive != null:
		return override_drive
	var d := Drive.new()
	var left := Vector2.ZERO
	var right := Vector2.ZERO
	var pads := Input.get_connected_joypads()
	var stick_click := false
	var simple := is_simple()
	if not pads.is_empty():
		var id: int = pads[0]
		var ls := _stick(id, JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
		var rs := _stick(id, JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
		stick_click = Input.is_joy_button_pressed(id, JOY_BUTTON_LEFT_STICK) \
			and Input.is_joy_button_pressed(id, JOY_BUTTON_RIGHT_STICK)
		if simple:
			var turn_pad := clampf(ls.x * 0.8 + rs.x, -1.0, 1.0)
			left += Vector2(0.0, ls.y + turn_pad)
			right += Vector2(0.0, ls.y - turn_pad)
		else:
			left = ls
			right = rs

	if simple:
		var fwd := Input.get_axis("kb_back", "kb_forward")
		var turn := Input.get_axis("kb_left", "kb_right")
		left += Vector2(0.0, fwd + turn)
		right += Vector2(0.0, fwd - turn)
	else:
		left += Vector2(Input.get_axis("kb_left", "kb_right"), Input.get_axis("kb_back", "kb_forward"))
		right += Vector2(Input.get_axis("kb_r_left", "kb_r_right"), Input.get_axis("kb_r_back", "kb_r_forward"))

	if touch_stick != Vector2.ZERO:
		var touch_turn_amount := touch_stick.x * 0.8
		left += Vector2(0.0, touch_stick.y + touch_turn_amount)
		right += Vector2(0.0, touch_stick.y - touch_turn_amount)

	left = left.limit_length(1.0)
	right = right.limit_length(1.0)
	d.left = left
	d.right = right
	d.move = ((left + right) * 0.5).limit_length(1.0)
	var raw_turn := clampf((left.y - right.y) * 0.5, -1.0, 1.0)
	var ramp := TURN_RAMP_UP if absf(raw_turn) > absf(_turn) else TURN_RAMP_DOWN
	_turn = move_toward(_turn, raw_turn, ramp * delta)
	d.turn = _turn
	d.look_up = Input.is_action_pressed("look_up") or touch_look
	d.jump = Input.is_action_just_pressed("jump") or touch_jump
	d.jump_held = Input.is_action_pressed("jump") or touch_jump_held or touch_jump
	touch_jump = false
	d.free_look_toggle = Input.is_action_just_pressed("free_look")
	for i in 5:
		if Input.is_action_just_pressed("view_%d" % (i + 1)):
			d.view = i + 1
	if Input.is_action_just_pressed("view_next") or touch_view_cycle:
		d.view = -1
	touch_view_cycle = false
	d.look = Vector2(
		Input.get_axis("kb_left", "kb_right") + Input.get_axis("kb_r_left", "kb_r_right"),
		Input.get_axis("kb_back", "kb_forward") + Input.get_axis("kb_r_back", "kb_r_forward"))
	if not pads.is_empty():
		d.look += _stick(pads[0], JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y) + _stick(pads[0], JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
	d.look = d.look.limit_length(1.0)

	# 180 度迴轉：同時按兩桿（只在按下瞬間觸發一次）或快捷鍵
	if stick_click and not _stick_click_latch:
		d.quick_turn = true
	_stick_click_latch = stick_click
	if Input.is_action_just_pressed("quick_turn") or touch_turn:
		d.quick_turn = true
	touch_turn = false

	d.dash = touch_dash or _detect_dash_gesture(left, right, delta)
	touch_dash = false
	# 鍵盤 Shift：輕按＝衝刺（等確認沒有第二下才出發）、連按兩下＝轉身、按住＝集氣
	if Input.is_action_just_pressed("kb_shift"):
		if _shift_state == 3:
			d.quick_turn = true
			_shift_state = 0
		else:
			_shift_state = 1
			_shift_t = 0.0
	elif _shift_state == 1:
		_shift_t += delta
		if not Input.is_action_pressed("kb_shift"):
			_shift_state = 3
			_shift_t = 0.0
		elif _shift_t > HOLD_TO_CHARGE:
			_shift_state = 2
	elif _shift_state == 2:
		if not Input.is_action_pressed("kb_shift"):
			_shift_state = 0
	elif _shift_state == 3:
		_shift_t += delta
		if _shift_t > DOUBLE_TAP_WINDOW:
			d.dash = true
			_shift_state = 0
	# 手把 X：輕按＝衝刺、按住＝集氣
	var pad_charge := false
	if Input.is_action_pressed("dash"):
		_pad_x_t = maxf(_pad_x_t, 0.0) + delta
		pad_charge = _pad_x_t > HOLD_TO_CHARGE
	elif _pad_x_t >= 0.0:
		if _pad_x_t <= HOLD_TO_CHARGE:
			d.dash = true
		_pad_x_t = -1.0
	d.charge = _shift_state == 2 or pad_charge or touch_charge_held
	if Input.is_action_just_pressed("toggle_scheme"):
		toggle_scheme()
	return d


func _stick(id: int, ax: JoyAxis, ay: JoyAxis) -> Vector2:
	# 手把 Y 軸往上為負值，這裡轉成往上為正
	var v := Vector2(Input.get_joy_axis(id, ax), -Input.get_joy_axis(id, ay))
	if v.length() < DEADZONE:
		return Vector2.ZERO
	return v.normalized() * inverse_lerp(DEADZONE, 1.0, minf(v.length(), 1.0))


## 王子衝刺：兩桿一上一下快速交替達指定次數。
func _detect_dash_gesture(left: Vector2, right: Vector2, delta: float) -> bool:
	_flip_timer += delta
	var sign_now := 0
	if left.y > DASH_STICK_THRESHOLD and right.y < -DASH_STICK_THRESHOLD:
		sign_now = 1
	elif left.y < -DASH_STICK_THRESHOLD and right.y > DASH_STICK_THRESHOLD:
		sign_now = -1
	if sign_now != 0 and sign_now != _last_flip_sign:
		_flip_count = _flip_count + 1 if _flip_timer < DASH_FLIP_WINDOW else 1
		_flip_timer = 0.0
		_last_flip_sign = sign_now
	if _flip_timer > DASH_FLIP_WINDOW:
		_flip_count = 0
		_last_flip_sign = 0
	if _flip_count >= DASH_FLIPS_NEEDED:
		_flip_count = 0
		_last_flip_sign = 0
		return true
	return false
