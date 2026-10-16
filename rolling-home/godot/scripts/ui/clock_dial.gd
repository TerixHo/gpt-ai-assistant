class_name ClockDial
extends Control
## 右上角倒數計時：扇形表示剩餘時間比例，最後 30 秒轉紅並閃爍。

var time_left := 180.0
var time_total := 180.0
## 不限時間模式時 >= 0，改成顯示經過時間
var elapsed := -1.0
var _blink := 0.0


func _ready() -> void:
	custom_minimum_size = Vector2(150, 150)
	size = custom_minimum_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(delta: float) -> void:
	_blink += delta
	queue_redraw()


func _draw() -> void:
	var c := size * 0.5
	var r := 58.0
	var counting_up := elapsed >= 0.0
	var ratio := clampf(time_left / maxf(time_total, 0.01), 0.0, 1.0)
	if counting_up:
		ratio = fposmod(elapsed, 60.0) / 60.0
	var warn := time_left <= 30.0 and not counting_up
	draw_circle(c, r + 6, Color(0.08, 0.1, 0.22, 0.72))
	draw_circle(c, r, Color(1, 1, 1, 0.12))
	var col := Color(0.35, 0.75, 1.0)
	if warn:
		col = Color(1.0, 0.35, 0.3) if int(_blink * 4.0) % 2 == 0 or time_left > 10.0 else Color(1.0, 0.75, 0.3)
	if ratio > 0.0:
		var pts := PackedVector2Array([c])
		var steps := maxi(int(48 * ratio), 2)
		for i in steps + 1:
			var a := -PI * 0.5 + TAU * ratio * float(i) / steps
			pts.append(c + Vector2.from_angle(a) * r)
		draw_colored_polygon(pts, col)
	for i in 12:
		var a := TAU * i / 12.0
		draw_line(c + Vector2.from_angle(a) * (r - 6), c + Vector2.from_angle(a) * r, Color(1, 1, 1, 0.6), 2.0)
	var font := get_theme_default_font()
	var txt := KMath.format_time(elapsed if counting_up else time_left)
	var fs := 30
	var w := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	draw_string_outline(font, c + Vector2(-w * 0.5, 11), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 7, Color(0.1, 0.1, 0.2))
	draw_string(font, c + Vector2(-w * 0.5, 11), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color.WHITE)
