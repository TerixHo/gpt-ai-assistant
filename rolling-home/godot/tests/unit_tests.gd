extends Node
## 單元測試與資料完整性檢查。
## 用法：godot --headless res://tests/unit_tests.tscn

var _fails := 0
var _passes := 0


func _ready() -> void:
	Game.persist = false
	_test_kmath()
	_test_data()
	_test_props()
	print("[unit] 通過 %d 項，失敗 %d 項" % [_passes, _fails])
	get_tree().quit(1 if _fails > 0 else 0)


func check(cond: bool, label: String) -> void:
	if cond:
		_passes += 1
	else:
		_fails += 1
		printerr("[unit] FAIL：", label)


func _test_kmath() -> void:
	check(KMath.format_size(5.0) == "5cm", "format 5cm")
	check(KMath.format_size(12.34) == "12cm3mm", "format 12.34cm")
	check(KMath.format_size(100.0) == "1m", "format 1m")
	check(KMath.format_size(124.0) == "1m24cm", "format 1m24cm")
	check(KMath.format_time(65.2) == "1:06", "format time")
	var v := KMath.sphere_volume(10.0)
	check(absf(KMath.diameter_from_volume(v) - 10.0) < 0.001, "volume round trip")
	check(KMath.can_pick(3.0, 5.0, 0.7), "can pick 3cm with 5cm")
	check(not KMath.can_pick(4.0, 5.0, 0.7), "cannot pick 4cm with 5cm")


func _test_data() -> void:
	check(Data.items.size() >= 40, "物件數量 ≥ 40（目前 %d）" % Data.items.size())
	for id in Data.items:
		var def: Dictionary = Data.items[id]
		check(def.has("name") and def.has("dims"), "物件 %s 缺少 name/dims" % id)
		check(PropFactory.size_of(def) > 0.0, "物件 %s 尺寸需大於 0" % id)
		if def.get("shape", "") == "parts":
			check(not (def.get("parts", []) as Array).is_empty(), "物件 %s 的 parts 為空" % id)
	var playable := 0
	for s in Data.stages:
		check(float(s["goal_cm"]) > float(s["start_cm"]), "關卡 %s 目標需大於起始" % s["id"])
		if not s.get("playable", false):
			continue
		playable += 1
		var level := Data.get_level(s["level"])
		check(not level.is_empty(), "關卡 %s 場景檔可讀" % s["id"])
		var zones: Array = []
		for z in level.get("spawns", []):
			zones.append(z["zone"])
			for item_id in z.get("items", {}):
				check(Data.items.has(item_id), "區塊 %s 引用未定義物件 %s" % [z["zone"], item_id])
		for z in s.get("zones", []):
			check(zones.has(z), "關卡 %s 引用未定義區塊 %s" % [s["id"], z])
		for p in level.get("placements", []):
			check(Data.items.has(p["item"]), "擺放引用未定義物件 %s" % p["item"])
		var gate_ids: Array = []
		for g in level.get("gates", []):
			gate_ids.append(g["id"])
		for g in s.get("gates", {}):
			check(gate_ids.has(g), "關卡 %s 引用未定義門檻 %s" % [s["id"], g])
	check(playable >= 1, "至少一個可玩關卡")


func _test_props() -> void:
	for id in Data.items:
		var built := PropFactory.build(Data.items[id])
		var visual: Node3D = built["visual"]
		check(visual.get_child_count() > 0, "物件 %s 有外觀" % id)
		check(not (built["shapes"] as Array).is_empty(), "物件 %s 有碰撞形狀" % id)
		visual.free()
