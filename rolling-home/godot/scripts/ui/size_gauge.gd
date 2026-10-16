class_name SizeGauge
extends Control
## 左上角尺寸儀表：實心圓 = 目前直徑，虛線圈 = 目標直徑，中央顯示數字。
## 造型刻意與原作不同（原作為圓圈內王子剪影），採「同心圓 + 刻度」設計。

var diameter := 5.0
var goal := 10.0
var _shown := 5.0
var _pulse := 0.0


func _ready() -> void:
	custom_minimum_size = Vector2(190, 190)
	size = custom_minimum_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_values(d: float, g: float) -> void:
	if d > diameter + 0.05:
		_pulse = 1.0
	diameter = d
	goal = g


func _process(delta: float) -> void:
	_shown = lerpf(_shown, diameter, 1.0 - exp(-8.0 * delta))
	_pulse = maxf(_pulse - delta * 3.0, 0.0)
	queue_redraw()


func _draw() -> void:
	var c := size * 0.5 - Vector2(0, 8)
	var max_r := 78.0
	var scale_cm := maxf(goal * 1.25, _shown * 1.08)
	var r_goal := max_r * goal / scale_cm
	var r_cur := max_r * _shown / scale_cm
	draw_circle(c, max_r + 6, Color(0.08, 0.1, 0.22, 0.72))
	# 刻度
	for i in 24:
		var a := TAU * i / 24.0
		var inner := max_r - (6.0 if i % 6 == 0 else 3.0)
		draw_line(c + Vector2.from_angle(a) * inner, c + Vector2.from_angle(a) * max_r, Color(1, 1, 1, 0.35), 1.5)
	var reached := diameter >= goal
	var fill := Color(1.0, 0.82, 0.25) if not reached else Color(0.45, 0.9, 0.55)
	draw_circle(c, r_cur * (1.0 + _pulse * 0.06), fill)
	draw_arc(c, r_cur, 0, TAU, 48, fill.darkened(0.35), 2.0)
	# 目標虛線圈
	var seg := 32
	for i in seg:
		if i % 2 == 0:
			draw_arc(c, r_goal, TAU * i / seg, TAU * (i + 1) / seg, 4, Color(1, 1, 1, 0.95), 2.5)
	var font := get_theme_default_font()
	var big := KMath.format_size(diameter)
	var fs := 26
	var w := font.get_string_size(big, HORIZONTAL_ALIGNMENT_CENTER, -1, fs).x
	draw_string_outline(font, c + Vector2(-w * 0.5, 9), big, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 6, Color(0.1, 0.1, 0.2))
	draw_string(font, c + Vector2(-w * 0.5, 9), big, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color.WHITE)
	var sub := "目標 %s" % KMath.format_size(goal)
	var w2 := font.get_string_size(sub, HORIZONTAL_ALIGNMENT_CENTER, -1, 16).x
	draw_string(font, Vector2(size.x * 0.5 - w2 * 0.5, size.y - 2), sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(1, 1, 1, 0.95))
