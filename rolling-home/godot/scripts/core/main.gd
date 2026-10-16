extends Node
## 遊戲流程：標題 → 關卡 → 結算 → 下一關／重玩／標題，另含關卡選擇與收藏目錄。

const BG_TOP := Color("#ffcf56")
const BG_BOTTOM := Color("#ff7f50")

var _current: Node


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--stage")
	if idx >= 0 and idx + 1 < args.size():
		start_stage(args[idx + 1])
	else:
		show_title()


func _swap(node: Node) -> void:
	get_tree().paused = false
	if _current != null and is_instance_valid(_current):
		_current.queue_free()
	_current = node
	add_child(node)


func start_stage(id: String) -> void:
	Game.current_stage_id = id
	var stage := Stage.new()
	stage.setup(id)
	stage.finished.connect(show_results)
	stage.restart_requested.connect(func(): start_stage.call_deferred(id))
	stage.quit_requested.connect(func(): show_title.call_deferred())
	_swap(stage)


# ---------- 畫面工具 ----------

func _screen() -> Control:
	var layer := CanvasLayer.new()
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(root)
	var bg := TextureRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var grad := Gradient.new()
	grad.set_color(0, BG_TOP)
	grad.set_color(1, BG_BOTTOM)
	var gt := GradientTexture2D.new()
	gt.gradient = grad
	gt.fill_from = Vector2(0, 0)
	gt.fill_to = Vector2(0, 1)
	bg.texture = gt
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	root.add_child(bg)
	_swap(layer)
	return root


func _label(text: String, font_size: int, color := Color.WHITE) -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0.25, 0.12, 0.1))
	l.add_theme_constant_override("outline_size", maxi(font_size / 6, 4))
	return l


func _button(text: String, cb: Callable, font_size := 26) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(320, 54)
	b.add_theme_font_size_override("font_size", font_size)
	b.pressed.connect(func():
		Sfx.play("ui")
		cb.call())
	return b


func _column(root: Control, width := 520.0) -> VBoxContainer:
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(center)
	var box := VBoxContainer.new()
	box.custom_minimum_size = Vector2(width, 0)
	box.add_theme_constant_override("separation", 14)
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_child(box)
	return box


# ---------- 標題 ----------

func show_title() -> void:
	var root := _screen()
	var box := _column(root)
	box.add_child(_label("家滾滾", 92))
	box.add_child(_label("從書桌上的小珠珠開始，把家裡的東西滾成一顆大球！", 22, Color(1, 0.98, 0.9)))
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 12)
	box.add_child(spacer)
	var first := _button("開始遊戲", func(): start_stage(Data.stages[0]["id"]))
	box.add_child(first)
	box.add_child(_button("選關卡", show_stage_select))
	box.add_child(_button("收藏圖鑑", show_collection))
	box.add_child(_button("怎麼玩", show_help))
	var settings := HBoxContainer.new()
	settings.alignment = BoxContainer.ALIGNMENT_CENTER
	settings.add_theme_constant_override("separation", 10)
	box.add_child(settings)
	for spec in [["zhuyin", "注音"], ["no_time_limit", "不限時間"]]:
		var key: String = spec[0]
		var label: String = spec[1]
		var b := Button.new()
		b.custom_minimum_size = Vector2(200, 46)
		b.add_theme_font_size_override("font_size", 20)
		b.text = "%s：%s" % [label, "開" if Game.settings.get(key, false) else "關"]
		b.pressed.connect(func():
			Game.toggle_setting(key)
			b.text = "%s：%s" % [label, "開" if Game.settings.get(key, false) else "關"])
		settings.add_child(b)
	var scheme := Button.new()
	scheme.custom_minimum_size = Vector2(260, 46)
	scheme.add_theme_font_size_override("font_size", 20)
	scheme.text = "操作：" + Controls.scheme_label()
	scheme.pressed.connect(func():
		Controls.toggle_scheme()
		scheme.text = "操作：" + Controls.scheme_label())
	settings.add_child(scheme)
	box.add_child(_button("離開", func(): get_tree().quit()))
	first.grab_focus()
	Sfx.play_music("title")


func show_stage_select() -> void:
	var root := _screen()
	var box := _column(root, 680)
	box.add_child(_label("選關卡", 52))
	var first: Button = null
	for s in Data.stages:
		var best := float(Game.best.get(s["id"], 0.0))
		var line := "%s　%s → %s　%s" % [s["name"], KMath.format_size(float(s["start_cm"])), KMath.format_size(float(s["goal_cm"])), KMath.format_time(float(s["time_sec"]))]
		if best > 0.0:
			line += "　最佳 %s" % KMath.format_size(best)
		var id: String = s["id"]
		var b := _button(line, func(): start_stage(id), 20)
		b.custom_minimum_size = Vector2(660, 48)
		if not s.get("playable", false):
			b.disabled = true
			b.text = "%s　（規劃中）" % s["name"]
		box.add_child(b)
		if first == null and not b.disabled:
			first = b
	box.add_child(_button("返回", show_title))
	if first != null:
		first.grab_focus()


func show_collection() -> void:
	var root := _screen()
	var box := _column(root, 900)
	var total := Data.items.size()
	var got := 0
	for id in Data.items:
		if int(Game.collection.get(id, 0)) > 0:
			got += 1
	box.add_child(_label("收藏圖鑑　%d / %d" % [got, total], 44))
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(900, 470)
	box.add_child(scroll)
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 24)
	scroll.add_child(grid)
	var ids := Data.items.keys()
	ids.sort_custom(func(a, b): return PropFactory.size_of(Data.items[a]) < PropFactory.size_of(Data.items[b]))
	for id in ids:
		var def: Dictionary = Data.items[id]
		var n := int(Game.collection.get(id, 0))
		var text := "%s　%s　×%d" % [def.get("name", id), KMath.format_size(PropFactory.size_of(def)), n] if n > 0 else "？？？　%s" % KMath.format_size(PropFactory.size_of(def))
		var l := _label(text, 18, Color.WHITE if n > 0 else Color(1, 1, 1, 0.55))
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		l.custom_minimum_size = Vector2(280, 0)
		grid.add_child(l)
	var back := _button("返回", show_title)
	box.add_child(back)
	back.grab_focus()


func show_help() -> void:
	var root := _screen()
	var box := _column(root, 900)
	box.add_child(_label("怎麼玩", 52))
	var lines := [
		"比滾球小的東西，碰到就會黏上來。滾球越大，就能黏越大的東西！",
		"一開始只黏得起小玻璃珠，慢慢變大以後，橡皮擦、小汽車、恐龍都黏得起來。",
		"鍵盤：W/S 前進後退　A/D 轉彎　Shift 衝刺　Space 轉身　Tab 看遠一點",
		"手把：左搖桿前進和轉彎，右搖桿也可以轉彎　X 衝刺　Y 轉身　RB 看遠一點",
		"小心貓咪和小狗！滾球很小的時候，牠們會把你身上的東西拍掉。",
		"變大以後牠們就會逃跑，再大一點就能把牠們黏起來了！",
		"想用原作的雙搖桿操作，可以在標題畫面切換，或按 F2。",
	]
	for t in lines:
		var l := _label(t, 20)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(880, 0)
		box.add_child(l)
	var back := _button("返回", show_title)
	box.add_child(back)
	back.grab_focus()


# ---------- 結算 ----------

func show_results(result: Dictionary) -> void:
	Game.record_result(result)
	var root := _screen()
	var box := _column(root, 760)
	var ok: bool = result["success"]
	var d: float = result["diameter_cm"]
	var g: float = result["goal_cm"]
	box.add_child(_label("過關！" if ok else "還差一點點！", 64, Color.WHITE if ok else Color(1, 0.92, 0.85)))
	box.add_child(_label("滾球變成 %s 了（目標 %s）" % [KMath.format_size(d), KMath.format_size(g)], 30))
	box.add_child(_label(grade_text(result), 24, Color(1, 1, 0.85)))
	var ttg: float = result["time_to_goal"]
	if ok and ttg >= 0.0:
		var line := "%s 就達成目標" % KMath.format_time(ttg)
		if float(result.get("comet_sec", 0.0)) > 0.0 and ttg <= float(result["comet_sec"]):
			line += "　獲得流星獎勵！"
		box.add_child(_label(line, 22))
	if result.get("no_limit", false):
		box.add_child(_label("這次玩了 %s" % KMath.format_time(float(result.get("elapsed", 0.0))), 22))
	box.add_child(_label("一共黏了 %d 個東西" % int(result["count"]), 22))
	var names: Array = []
	for id in result["top_items"]:
		names.append(Data.get_item(id).get("name", id))
	if not names.is_empty():
		box.add_child(_label("黏到最大的東西：" + "、".join(names), 20))
	var next_id := Game.next_stage_id(result["stage_id"])
	var first: Button
	if ok and not next_id.is_empty() and Game.is_stage_playable(next_id):
		first = _button("下一關", func(): start_stage(next_id))
		box.add_child(first)
	var retry := _button("再玩一次", func(): start_stage(result["stage_id"]))
	box.add_child(retry)
	box.add_child(_button("回到標題", show_title))
	(first if first != null else retry).grab_focus()
	Sfx.play_music("title")


static func grade_text(result: Dictionary) -> String:
	var ratio := float(result["diameter_cm"]) / maxf(float(result["goal_cm"]), 0.01)
	var best_text := "星婆婆：再試一次，一定可以的！"
	var best_min := -1.0
	for g in result.get("grades", []):
		var m := float(g["min_ratio"])
		if ratio >= m and m > best_min:
			best_min = m
			best_text = g["text"]
	return best_text
