extends Node
## 操作中樞：把手把／鍵盤輸入轉換為原作風格的「雙搖桿坦克式」指令。
##
## 規則（雙搖桿）：
##   兩桿同推前 = 前進；同推後 = 後退；同推左右 = 平移。
##   左桿前右桿後 = 原地右轉；反之左轉。
##   兩桿上下快速交替 = 王子衝刺；同時按下兩桿（L3+R3）= 180 度迴轉。
## 鍵盤簡化模式會先轉成同樣的虛擬雙搖桿，後段邏輯完全共用。

class Drive:
	## x 為向右平移、y 為前進（相機座標），長度不超過 1
	var move := Vector2.ZERO
	## 正值為向右轉（俯視順時針）
	var turn := 0.0
	var dash := false
	var quick_turn := false
	var look_up := false
	var left := Vector2.ZERO
	var right := Vector2.ZERO

const DEADZONE := 0.2
const DASH_STICK_THRESHOLD := 0.6
const DASH_FLIPS_NEEDED := 4
const DASH_FLIP_WINDOW := 0.4

## 測試與展示用：設定後完全取代硬體輸入
var override_drive: Drive = null

var _flip_count := 0
var _flip_timer := 0.0
var _last_flip_sign := 0
var _stick_click_latch := false


func _ready() -> void:
	_register_actions()


func _register_actions() -> void:
	_add_keys("kb_forward", [KEY_W])
	_add_keys("kb_back", [KEY_S])
	_add_keys("kb_left", [KEY_A])
	_add_keys("kb_right", [KEY_D])
	_add_keys("kb_strafe_left", [KEY_Q])
	_add_keys("kb_strafe_right", [KEY_E])
	_add_keys("kb_r_forward", [KEY_UP, KEY_I])
	_add_keys("kb_r_back", [KEY_DOWN, KEY_K])
	_add_keys("kb_r_left", [KEY_LEFT, KEY_J])
	_add_keys("kb_r_right", [KEY_RIGHT, KEY_L])
	_add_keys("dash", [KEY_SHIFT], [JOY_BUTTON_X])
	_add_keys("quick_turn", [KEY_SPACE], [JOY_BUTTON_Y])
	_add_keys("look_up", [KEY_TAB], [JOY_BUTTON_RIGHT_SHOULDER])
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


func scheme_label() -> String:
	return "鍵盤簡化" if Game.settings["keyboard_scheme"] == "simple" else "鍵盤雙搖桿"


func toggle_scheme() -> void:
	var s: String = Game.settings["keyboard_scheme"]
	Game.settings["keyboard_scheme"] = "classic" if s == "simple" else "simple"
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
	if not pads.is_empty():
		var id: int = pads[0]
		left = _stick(id, JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
		right = _stick(id, JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
		stick_click = Input.is_joy_button_pressed(id, JOY_BUTTON_LEFT_STICK) \
			and Input.is_joy_button_pressed(id, JOY_BUTTON_RIGHT_STICK)

	if Game.settings["keyboard_scheme"] == "simple":
		var fwd := Input.get_axis("kb_back", "kb_forward")
		var turn := Input.get_axis("kb_left", "kb_right")
		var strafe := Input.get_axis("kb_strafe_left", "kb_strafe_right")
		left += Vector2(strafe, fwd + turn)
		right += Vector2(strafe, fwd - turn)
	else:
		left += Vector2(Input.get_axis("kb_left", "kb_right"), Input.get_axis("kb_back", "kb_forward"))
		right += Vector2(Input.get_axis("kb_r_left", "kb_r_right"), Input.get_axis("kb_r_back", "kb_r_forward"))

	left = left.limit_length(1.0)
	right = right.limit_length(1.0)
	d.left = left
	d.right = right
	d.move = ((left + right) * 0.5).limit_length(1.0)
	d.turn = clampf((left.y - right.y) * 0.5, -1.0, 1.0)
	d.look_up = Input.is_action_pressed("look_up")

	# 180 度迴轉：同時按兩桿（只在按下瞬間觸發一次）或快捷鍵
	if stick_click and not _stick_click_latch:
		d.quick_turn = true
	_stick_click_latch = stick_click
	if Input.is_action_just_pressed("quick_turn"):
		d.quick_turn = true

	d.dash = Input.is_action_just_pressed("dash") or _detect_dash_gesture(left, right, delta)
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
