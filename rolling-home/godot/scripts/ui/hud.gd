class_name Hud
extends CanvasLayer
## 遊戲中介面：尺寸儀表、計時、拾取提示、區域名稱、中央訊息、操作說明、暫停選單。

signal resume_requested
signal restart_requested
signal quit_requested

var gauge: SizeGauge
var clock: ClockDial
var _toasts: VBoxContainer
var _banner: Label
var _area: Label
var _hint: Label
var _count: Label
var _pause: PanelContainer
var _banner_tween: Tween


func _ready() -> void:
	layer = 10
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	gauge = SizeGauge.new()
	gauge.position = Vector2(16, 12)
	root.add_child(gauge)

	clock = ClockDial.new()
	clock.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	clock.position = Vector2(-166, 12)
	root.add_child(clock)

	_count = _label(18, HORIZONTAL_ALIGNMENT_LEFT)
	_count.position = Vector2(30, 206)
	root.add_child(_count)

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
	_hint.position = Vector2(-760, -34)
	_hint.size = Vector2(740, 24)
	_hint.modulate.a = 0.8
	root.add_child(_hint)
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
	if Game.settings["keyboard_scheme"] == "simple":
		_hint.text = "W/S 前後  A/D 轉向  Q/E 平移  Shift 衝刺  Space 迴轉  Tab 俯瞰  Esc 暫停  F2 雙搖桿鍵位"
	else:
		_hint.text = "左桿 WASD  右桿 方向鍵  兩桿交替=衝刺  Space 迴轉  Tab 俯瞰  Esc 暫停  F2 簡化鍵位"


func set_status(diameter: float, goal: float, time_left: float, time_total: float, count: int) -> void:
	gauge.set_values(diameter, goal)
	clock.time_left = time_left
	clock.time_total = time_total
	_count.text = "已黏 %d 件" % count


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
	panel.position = Vector2(-170, -150)
	panel.size = Vector2(340, 300)
	panel.process_mode = Node.PROCESS_MODE_WHEN_PAUSED
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 14)
	panel.add_child(box)
	var title := _label(34, HORIZONTAL_ALIGNMENT_CENTER)
	title.text = "暫停"
	box.add_child(title)
	for spec in [["Resume", "繼續", resume_requested], ["Restart", "重新開始", restart_requested], ["Quit", "回到標題", quit_requested]]:
		var b := Button.new()
		b.name = spec[0]
		b.text = spec[1]
		b.add_theme_font_size_override("font_size", 24)
		var sig: Signal = spec[2]
		b.pressed.connect(func(): sig.emit())
		box.add_child(b)
	var scheme := Button.new()
	scheme.text = "鍵盤配置：" + Controls.scheme_label()
	scheme.add_theme_font_size_override("font_size", 18)
	scheme.pressed.connect(func():
		Controls.toggle_scheme()
		scheme.text = "鍵盤配置：" + Controls.scheme_label()
		refresh_hint())
	box.add_child(scheme)
	return panel
