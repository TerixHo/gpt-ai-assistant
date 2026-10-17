extends Node
## 遊戲流程：標題 → 關卡 → 結算 → 下一關／重玩／標題，另含關卡選擇與收藏目錄。

const BG_TOP := Color("#ffcf56")
const BG_BOTTOM := Color("#ff7f50")
## 標題畫面背景輪流播放的示範關卡（自動駕駛在玩），每段秒數；還沒做好的關卡略過，全部沒有時用舊版房子
const DEMO_STAGES := ["home", "street", "station"]
const DEMO_FALLBACK := ["home_1", "home_3"]
const DEMO_SECONDS := 45.0

var _current: Node
var _demo: Stage
var _demo_index := 0
var _demo_timer := 0.0


func _ready() -> void:
	# 標題、選單等介面不需要物理插值（關卡節點會自己開啟）
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--stage")
	if idx >= 0 and idx + 1 < args.size():
		start_stage(args[idx + 1])
	else:
		show_title()


func _process(delta: float) -> void:
	if _demo != null and is_instance_valid(_demo):
		_demo_timer += delta
		if _demo_timer > DEMO_SECONDS:
			_demo_index += 1
			_start_demo(true)


## 標題畫面背景：讓自動駕駛玩一段，畫面就是遊戲裡滾啊滾的樣子
func _start_demo(restart := false) -> void:
	if _demo != null and is_instance_valid(_demo):
		if not restart:
			return
		_demo.queue_free()
	_demo_timer = 0.0
	var stage := Stage.new()
	stage.demo = true
	var ids := DEMO_STAGES.filter(func(id): return Game.is_stage_playable(id))
	if ids.is_empty():
		ids = DEMO_FALLBACK
	stage.setup(ids[_demo_index % ids.size()])
	stage.skip_intro = true
	add_child(stage)
	move_child(stage, 0)
	var pilot := AutoPilot.new()
	pilot.stage = stage
	stage.add_child(pilot)
	stage.cam.view = 2
	_demo = stage


func _stop_demo() -> void:
	if _demo != null and is_instance_valid(_demo):
		_demo.queue_free()
	_demo = null


func _swap(node: Node) -> void:
	get_tree().paused = false
	if _current != null and is_instance_valid(_current):
		_current.queue_free()
	_current = node
	add_child(node)


func start_stage(id: String) -> void:
	_stop_demo()
	Game.current_stage_id = id
	var stage := Stage.new()
	stage.setup(id)
	stage.finished.connect(show_results)
	stage.restart_requested.connect(func(): start_stage.call_deferred(id))
	stage.quit_requested.connect(func(): show_title.call_deferred())
	_swap(stage)


# ---------- 畫面工具 ----------

func _screen(opaque := true) -> Control:
	if opaque:
		_stop_demo()
	var layer := CanvasLayer.new()
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(root)
	if not opaque:
		_swap(layer)
		return root
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


func _button(text: String, cb: Callable, font_size := 26, accent := false) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(320, 54)
	b.add_theme_font_size_override("font_size", font_size)
	_style_button(b, accent)
	b.pressed.connect(func():
		Sfx.play("ui")
		cb.call())
	return b


## 圓角奶油色按鈕（重點按鈕用黃色），在遊戲畫面或漸層背景上都看得清楚
func _style_button(b: Button, accent := false) -> void:
	var base := Color("#ffc93c") if accent else Color(1.0, 0.97, 0.91, 0.94)
	var ink := Color("#3a2410") if accent else Color("#4a2f6b")
	for state in ["normal", "hover", "pressed", "focus", "disabled"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = base.lightened(0.12) if state == "hover" else (base.darkened(0.08) if state == "pressed" else base)
		sb.set_corner_radius_all(26)
		sb.set_border_width_all(4 if state == "focus" else 3)
		sb.border_color = Color.WHITE if state == "focus" else Color("#8a6ccf")
		sb.content_margin_left = 18
		sb.content_margin_right = 18
		sb.content_margin_top = 6
		sb.content_margin_bottom = 8
		sb.shadow_color = Color(0.15, 0.08, 0.25, 0.35)
		sb.shadow_size = 4
		sb.shadow_offset = Vector2(0, 3)
		if state == "focus":
			sb.bg_color = Color(0, 0, 0, 0)
			sb.shadow_size = 0
		b.add_theme_stylebox_override(state, sb)
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(key, ink)
	b.add_theme_constant_override("outline_size", 0)


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
	_start_demo()
	var root := _screen(false)
	# 上下各一層半透明漸層，讓標題和按鈕在遊戲畫面上看得清楚
	for spec in [[0.0, 0.42, Color(0.12, 0.07, 0.2, 0.55), Color(0.12, 0.07, 0.2, 0.0)],
			[0.45, 1.0, Color(0.12, 0.07, 0.2, 0.0), Color(0.12, 0.07, 0.2, 0.6)]]:
		var shade := TextureRect.new()
		shade.anchor_top = spec[0]
		shade.anchor_bottom = spec[1]
		shade.anchor_right = 1.0
		var g := Gradient.new()
		g.set_color(0, spec[2])
		g.set_color(1, spec[3])
		var gt := GradientTexture2D.new()
		gt.gradient = g
		gt.fill_from = Vector2(0, 0)
		gt.fill_to = Vector2(0, 1)
		shade.texture = gt
		shade.stretch_mode = TextureRect.STRETCH_SCALE
		shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
		root.add_child(shade)
	var logo := TitleLogo.new()
	logo.anchor_right = 1.0
	logo.anchor_bottom = 0.3
	logo.offset_top = 8
	root.add_child(logo)
	var sub := _label("從宜蘭冬山的家出發，跟槿寶一起滾啊滾，一路滾到冬山火車站！", 22, Color(1, 0.98, 0.9))
	sub.anchor_top = 0.3
	sub.anchor_right = 1.0
	sub.offset_bottom = 34
	root.add_child(sub)
	# 按鈕放在下方，畫面中間留給背景裡滾動的球和槿寶
	var bottom := VBoxContainer.new()
	bottom.anchor_top = 1.0
	bottom.anchor_right = 1.0
	bottom.anchor_bottom = 1.0
	bottom.offset_top = -176
	bottom.offset_bottom = -22
	bottom.alignment = BoxContainer.ALIGNMENT_END
	bottom.add_theme_constant_override("separation", 12)
	root.add_child(bottom)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	bottom.add_child(row)
	var first := _button("開始遊戲", func(): start_stage(Data.stages[0]["id"]), 30, true)
	first.custom_minimum_size = Vector2(300, 66)
	row.add_child(first)
	for spec in [["選關卡", show_stage_select], ["收藏圖鑑", show_collection], ["怎麼玩", show_help]]:
		var mb := _button(spec[0], spec[1], 24)
		mb.custom_minimum_size = Vector2(190, 66)
		row.add_child(mb)
	var settings := HBoxContainer.new()
	settings.alignment = BoxContainer.ALIGNMENT_CENTER
	settings.add_theme_constant_override("separation", 10)
	bottom.add_child(settings)
	for spec in [["zhuyin", "注音"], ["no_time_limit", "不限時間"]]:
		var key: String = spec[0]
		var label: String = spec[1]
		var b := Button.new()
		b.custom_minimum_size = Vector2(190, 48)
		b.add_theme_font_size_override("font_size", 20)
		_style_button(b)
		b.text = "%s：%s" % [label, "開" if Game.settings.get(key, false) else "關"]
		b.pressed.connect(func():
			Game.toggle_setting(key)
			b.text = "%s：%s" % [label, "開" if Game.settings.get(key, false) else "關"])
		settings.add_child(b)
	var scheme := Button.new()
	scheme.custom_minimum_size = Vector2(250, 48)
	scheme.add_theme_font_size_override("font_size", 20)
	_style_button(scheme)
	scheme.text = "操作：" + Controls.scheme_label()
	scheme.pressed.connect(func():
		Controls.toggle_scheme()
		scheme.text = "操作：" + Controls.scheme_label())
	settings.add_child(scheme)
	var box := settings
	# 網頁版（iPad、瀏覽器）沒有「離開」：關掉分頁就好
	if OS.get_name() != "Web":
		var quit := _button("離開", func(): get_tree().quit(), 20)
		quit.custom_minimum_size = Vector2(130, 48)
		box.add_child(quit)
	first.grab_focus()
	Sfx.play_music("title")


func show_stage_select() -> void:
	var root := _screen()
	var box := _column(root, 680)
	box.add_child(_label("選關卡", 52))
	var first: Button = null
	for s in Data.visible_stages():
		var id: String = s["id"]
		var playable := Game.is_stage_playable(id)
		var line: String = s["name"]
		if playable:
			line = "%s　%s → %s　%s" % [s["name"], KMath.format_size(float(s["start_cm"])), KMath.format_size(float(s["goal_cm"])), KMath.format_time(float(s["time_sec"]))]
			var best := float(Game.best.get(id, 0.0))
			if best > 0.0:
				line += "　最佳 %s" % KMath.format_size(best)
		var b := _button(line, func(): start_stage(id), 20)
		b.custom_minimum_size = Vector2(660, 48)
		if not playable:
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
		"故事從宜蘭冬山開始：先在槿寶家把東西滾成 1 公尺，再沿著上學的路、小學，一路滾到冬山火車站，變成 100 公尺！",
		"比滾球小的東西，碰到就會黏上來。滾球越大，就能黏越大的東西。最後黏的 10 個東西會突出在球外面，滾起來一顛一顛的。",
		"集氣衝刺：按住集氣，主角慢慢推、球越轉越快，每 1 秒變一個顏色：黃、橘、紅，最後是藍色火焰。放開衝出去，至少 3 倍速！撞到比自己大的東西會彈回來，還會掉東西喔。",
		"跳躍：按一下往前小跳，在空中再按一次是二段跳，槿寶會前空翻。不高的台階會自動滾上去；家具旁邊有積木樓梯可以爬上去。",
		"卡住了？右邊會出現房子按鈕，按下去就回到中間（電腦按 R）。",
		"iPad 與手機：左邊按住拖曳走路；搖桿放開後馬上再按住就是集氣，放開衝出去；右半邊往上滑衝刺；右邊的圖示按鈕是跳躍、轉身、看遠、視角、暫停。",
		"鍵盤：W/S 前進後退　A/D 轉彎　空白鍵 跳躍（空中再按：二段跳）　Shift 衝刺　按住 Shift 集氣　Shift 按兩下 轉身　E 環視　1 到 5 換視角　R 回到中間",
		"手把：左搖桿前進和轉彎　A 跳躍　X 衝刺（按住集氣）　Y 轉身　LB 環視　RB 看遠一點　Back 換視角",
		"小心貓咪和小狗！滾球很小的時候，牠們會把你身上的東西拍掉；變大以後就能把牠們黏起來。",
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
