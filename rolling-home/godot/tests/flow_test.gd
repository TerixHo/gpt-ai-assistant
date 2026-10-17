extends Node
## 完整流程測試：標題 → 關卡 → 結算 → 收藏目錄／關卡選擇／操作說明 → 下一關。
## 用法：godot --headless --fixed-fps 60 res://tests/flow_test.tscn

var _main: Node
var _step := 0
var _timer := 0.0
var _fails: Array[String] = []


func _ready() -> void:
	Game.persist = false
	_main = load("res://scenes/main.tscn").instantiate()
	add_child(_main)


func _process(delta: float) -> void:
	_timer += delta
	if _timer < 0.5:
		return
	_timer = 0.0
	match _step:
		0:
			var logo := get_tree().root.find_child("TitleLogo", true, false)
			_expect(logo != null and str(logo.get("text")) == "Gǔn A Gǔn A", "標題畫面顯示 3D 大標題 Gǔn A Gǔn A")
			_expect(get_tree().root.find_children("Stage", "", true, false).size() > 0, "標題背景有示範關卡在跑")
			_main.start_stage("home")
		1:
			var stage := _main.get_child(_main.get_child_count() - 1) as Stage
			_expect(stage != null and stage.katamari != null, "關卡載入成功")
			if stage != null:
				stage.time_left = 0.3
				stage._begin_play()
		2, 3, 4, 5, 6, 7:
			pass
		8:
			_expect(not Game.last_result.is_empty(), "結算資料已記錄")
			_expect(_find_label("滾球變成"), "結算畫面顯示直徑")
			_main.show_collection()
		9:
			_expect(_find_label("收藏圖鑑"), "收藏圖鑑畫面")
			_main.show_stage_select()
		10:
			_expect(_find_label("選關卡"), "選關卡畫面")
			_main.show_help()
		11:
			_expect(_find_label("怎麼玩"), "怎麼玩畫面")
			_main.start_stage("street")
		12:
			var stage2 := _main.get_child(_main.get_child_count() - 1) as Stage
			_expect(stage2 != null and stage2.spawned_count > 300, "第 2 關載入（物件數 %d）" % (stage2.spawned_count if stage2 else 0))
			_main.show_title()
		13:
			for f in _fails:
				printerr("[flow] FAIL：", f)
			print("[flow] %s" % ("PASS" if _fails.is_empty() else "FAIL"))
			get_tree().quit(0 if _fails.is_empty() else 1)
	_step += 1


func _expect(cond: bool, label: String) -> void:
	if cond:
		print("[flow] ok：", label)
	else:
		_fails.append(label)


func _find_label(text: String, node: Node = null) -> bool:
	if node == null:
		node = _main
	if node is Label and (node as Label).text.contains(text):
		return true
	for c in node.get_children():
		if _find_label(text, c):
			return true
	return false
