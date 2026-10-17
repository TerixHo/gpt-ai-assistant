class_name Hud
extends CanvasLayer
## 遊戲中介面：尺寸儀表、計時、拾取提示、區域名稱、中央訊息、操作說明、暫停選單。

signal resume_requested
signal restart_requested
signal quit_requested
signal finish_requested
## 卡住時按「回到中間」
signal rescue_requested

var gauge: SizeGauge
var clock: ClockDial
var _toasts: VBoxContainer
var _banner: Label
var _area: Label
var _hint: Label
var _count: Label
var _count_box: Control
var _shown_count := 0
var _pause: PanelContainer
var _banner_tween: Tween
var _speed: ColorRect
var _speed_mat: ShaderMaterial
var _touch: TouchControls
## 電腦版的「回到中間」按鈕（觸控版由 TouchControls 畫）
var _rescue_btn: Button
var _milestone: Label
var _milestone_tween: Tween
## 示範模式（標題畫面背景）不需要觸控按鈕
var with_touch := true


func _ready() -> void:
	layer = 10
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	# 集氣衝刺的速度線（放在最底層，不擋住其他介面）
	_speed = ColorRect.new()
	_speed.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_speed.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_speed_mat = ShaderMaterial.new()
	_speed_mat.shader = preload("res://assets/shaders/speed_lines.gdshader")
	_speed.material = _speed_mat
	_speed.visible = false
	root.add_child(_speed)

	gauge = SizeGauge.new()
	gauge.position = Vector2(16, 12)
	root.add_child(gauge)

	clock = ClockDial.new()
	clock.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	clock.position = Vector2(-166, 12)
	root.add_child(clock)

	_count_box = _build_counter()
	root.add_child(_count_box)

	_area = _label(24, HORIZONTAL_ALIGNMENT_CENTER)
	_area.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_area.position = Vector2(-200, 18)
	_area.size = Vector2(400, 40)
	_area.modulate.a = 0.0
	root.add_child(_area)

	_banner = _label(56, HORIZONTAL_ALIGNMENT_CENTER)
	_banner.set_anchors_preset(Control.PRESET_CENTER)
	_banner.position = Vector2(-500, -120)
	_banner.size = Vector2(1000, 90)
	_banner.modulate.a = 0.0
	root.add_child(_banner)

	_toasts = VBoxContainer.new()
	_toasts.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_toasts.position = Vector2(24, -170)
	_toasts.size = Vector2(520, 150)
	_toasts.alignment = BoxContainer.ALIGNMENT_END
	_toasts.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_toasts)

	_hint = _label(15, HORIZONTAL_ALIGNMENT_RIGHT)
	_hint.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_hint.position = Vector2(-900, -54)
	_hint.size = Vector2(880, 44)
	_hint.modulate.a = 0.8
	root.add_child(_hint)
	refresh_hint()

	_milestone = _label(64, HORIZONTAL_ALIGNMENT_CENTER)
	_milestone.set_anchors_preset(Control.PRESET_CENTER)
	_milestone.position = Vector2(-300, -230)
	_milestone.size = Vector2(600, 90)
	_milestone.add_theme_color_override("font_color", Color(1.0, 0.86, 0.3))
	_milestone.modulate.a = 0.0
	root.add_child(_milestone)

	_rescue_btn = Button.new()
	_rescue_btn.icon = preload("res://assets/ui/icons/rescue.svg")
	_rescue_btn.expand_icon = true
	_rescue_btn.text = "R"
	_rescue_btn.tooltip_text = "回到中間"
	_rescue_btn.add_theme_font_size_override("font_size", 22)
	_rescue_btn.custom_minimum_size = Vector2(120, 84)
	_rescue_btn.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	_rescue_btn.position = Vector2(-150, -42)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1.0, 0.72, 0.2, 0.85)
	sb.set_corner_radius_all(42)
	sb.border_color = Color.WHITE
	sb.set_border_width_all(3)
	for st in ["normal", "hover", "pressed", "focus"]:
		_rescue_btn.add_theme_stylebox_override(st, sb)
	_rescue_btn.focus_mode = Control.FOCUS_NONE
	_rescue_btn.visible = false
	_rescue_btn.pressed.connect(func(): rescue_requested.emit())
	root.add_child(_rescue_btn)

	if with_touch:
		_touch = TouchControls.new()
		root.add_child(_touch)
		_touch.shown.connect(refresh_hint)
	refresh_hint()

	_pause = _build_pause()
	root.add_child(_pause)
	_pause.visible = false


func _label(font_size: int, align: HorizontalAlignment) -> Label:
	var l := Label.new()
	l.horizontal_alignment = align
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_outline_color", Color(0.1, 0.1, 0.2))
	l.add_theme_constant_override("outline_size", maxi(font_size / 5, 4))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func refresh_hint() -> void:
	# 觸控時左下角是搖桿，撿到東西的通知往上移，免得疊在一起
	_toasts.position.y = -390.0 if Controls.touch_active else -170.0
	var common := "按住 Shift 或滑鼠按住槿寶：集氣　E 第一人稱環視　1 到 5 切換視角　R 回到中間　Esc 暫停"
	if Controls.touch_active:
		_hint.text = ""
	elif Controls.is_simple():
		_hint.text = "W/S 前進後退　A/D 轉彎　空白鍵 跳躍（空中再按一次：二段跳）　Shift 衝刺　Shift 按兩下 轉身\n" + common
	else:
		_hint.text = "左桿 WASD　右桿 方向鍵　兩桿交替 衝刺　空白鍵 跳躍　Shift 按兩下 轉身\n" + common
	if _rescue_btn != null and _rescue_btn.visible and Controls.touch_active:
		_rescue_btn.visible = false


func set_status(diameter: float, goal: float, time_left: float, time_total: float, count: int, elapsed := -1.0) -> void:
	gauge.set_values(diameter, goal)
	clock.time_left = time_left
	clock.time_total = time_total
	clock.elapsed = elapsed
	if count != _shown_count:
		_shown_count = count
		_count.text = str(count)


## 衝刺的速度感：強度 0 到 1，顏色跟著集氣段數。
func set_speed_fx(amount: float, tint: Color) -> void:
	_speed.visible = amount > 0.01
	if _speed.visible:
		_speed_mat.set_shader_parameter("intensity", clampf(amount * 1.2, 0.0, 1.0))
		_speed_mat.set_shader_parameter("tint", tint)


## 右上角的「黏了幾個」計數：每黏到一個就彈一下。
func bump_count() -> void:
	_count_box.pivot_offset = _count_box.size * 0.5
	var t := create_tween()
	t.tween_property(_count_box, "scale", Vector2(1.12, 1.12), 0.06)
	t.tween_property(_count_box, "scale", Vector2.ONE, 0.14)


func _build_counter() -> Control:
	var panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.16, 0.11, 0.09, 0.55)
	sb.set_corner_radius_all(18)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 6
	sb.content_margin_bottom = 8
	panel.add_theme_stylebox_override("panel", sb)
	panel.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	panel.position = Vector2(-318, 22)
	panel.custom_minimum_size = Vector2(140, 0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", -6)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(col)
	var title := _label(18, HORIZONTAL_ALIGNMENT_CENTER)
	title.text = "黏了幾個"
	title.modulate.a = 0.85
	col.add_child(title)
	_count = _label(48, HORIZONTAL_ALIGNMENT_CENTER)
	_count.text = "0"
	_count.add_theme_color_override("font_color", Color(1.0, 0.86, 0.35))
	col.add_child(_count)
	return panel


func toast(text: String, big := false) -> void:
	var l := _label(26 if big else 21, HORIZONTAL_ALIGNMENT_LEFT)
	l.text = text
	if big:
		l.add_theme_color_override("font_color", Color(1.0, 0.9, 0.4))
	_toasts.add_child(l)
	while _toasts.get_child_count() > 4:
		var old := _toasts.get_child(0)
		_toasts.remove_child(old)
		old.queue_free()
	var t := create_tween()
	t.tween_interval(1.6)
	t.tween_property(l, "modulate:a", 0.0, 0.6)
	t.tween_callback(l.queue_free)


## 卡住時在右邊顯示「回到中間」按鈕（觸控是房子圖示的圓鈕，電腦是有 R 字的按鈕）。
func show_rescue(on: bool) -> void:
	if _touch != null:
		_touch.rescue_visible = on
	_rescue_btn.visible = on and not Controls.touch_active


## 成長里程碑：畫面上方彈出目前尺寸（配合 Yooo Gin Gin 的歡呼）。
func milestone(text: String) -> void:
	_milestone.text = text + "！"
	_milestone.pivot_offset = _milestone.size * 0.5
	if _milestone_tween != null and _milestone_tween.is_valid():
		_milestone_tween.kill()
	_milestone.modulate.a = 1.0
	_milestone.scale = Vector2(0.3, 0.3)
	_milestone_tween = create_tween()
	_milestone_tween.tween_property(_milestone, "scale", Vector2(1.25, 1.25), 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_milestone_tween.tween_property(_milestone, "scale", Vector2.ONE, 0.12)
	_milestone_tween.tween_interval(0.9)
	_milestone_tween.tween_property(_milestone, "modulate:a", 0.0, 0.4)


func clear_banner() -> void:
	if _banner_tween != null and _banner_tween.is_valid():
		_banner_tween.kill()
	_banner.modulate.a = 0.0


func banner(text: String, hold := 1.4, color := Color.WHITE) -> void:
	_banner.text = text
	_banner.add_theme_color_override("font_color", color)
	if _banner_tween != null and _banner_tween.is_valid():
		_banner_tween.kill()
	_banner.modulate.a = 1.0
	_banner.scale = Vector2.ONE
	_banner_tween = create_tween()
	_banner_tween.tween_interval(hold)
	_banner_tween.tween_property(_banner, "modulate:a", 0.0, 0.5)


func show_area(area_name: String) -> void:
	_area.text = area_name
	var t := create_tween()
	t.tween_property(_area, "modulate:a", 1.0, 0.25)
	t.tween_interval(1.8)
	t.tween_property(_area, "modulate:a", 0.0, 0.6)


func set_paused(paused: bool) -> void:
	_pause.visible = paused
	if paused:
		(_pause.find_child("Resume", true, false) as Button).grab_focus()


func _build_pause() -> PanelContainer:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.position = Vector2(-190, -220)
	panel.size = Vector2(380, 440)
	panel.process_mode = Node.PROCESS_MODE_WHEN_PAUSED
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 14)
	panel.add_child(box)
	var title := _label(34, HORIZONTAL_ALIGNMENT_CENTER)
	title.text = "暫停"
	box.add_child(title)
	for spec in [["Resume", "繼續", resume_requested], ["Rescue", "回到中間（卡住時）", rescue_requested], ["Finish", "結束這一局，看成績", finish_requested], ["Restart", "重新開始", restart_requested], ["Quit", "回到標題", quit_requested]]:
		var b := Button.new()
		b.name = spec[0]
		b.text = spec[1]
		b.add_theme_font_size_override("font_size", 24)
		var sig: Signal = spec[2]
		b.pressed.connect(func(): sig.emit())
		box.add_child(b)
	var scheme := Button.new()
	scheme.text = "操作方式：" + Controls.scheme_label()
	scheme.add_theme_font_size_override("font_size", 18)
	scheme.pressed.connect(func():
		Controls.toggle_scheme()
		scheme.text = "操作方式：" + Controls.scheme_label()
		refresh_hint())
	box.add_child(scheme)
	return panel
