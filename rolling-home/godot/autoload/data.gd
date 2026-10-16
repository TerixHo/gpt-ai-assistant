extends Node
## 資料中心：載入所有資料驅動設定（物件、關卡、場景配置）。
## 所有尺寸單位為公分，世界座標 1 單位 = 1 公分。

const ITEMS_PATH := "res://data/items.json"
const STAGES_PATH := "res://data/stages.json"

var items: Dictionary = {}
var stages: Array = []
var _levels: Dictionary = {}


func _ready() -> void:
	reload()


func _exit_tree() -> void:
	PropFactory.clear_cache()
	ProcTex.clear_cache()


func reload() -> void:
	items.clear()
	_levels.clear()
	var item_data: Variant = load_json(ITEMS_PATH)
	if item_data is Dictionary:
		for def in item_data.get("items", []):
			items[def["id"]] = def
	var stage_data: Variant = load_json(STAGES_PATH)
	if stage_data is Dictionary:
		stages = stage_data.get("stages", [])


func get_item(id: String) -> Dictionary:
	if not items.has(id):
		push_warning("未定義的物件：%s" % id)
		return {}
	return items[id]


func get_stage(id: String) -> Dictionary:
	for s in stages:
		if s["id"] == id:
			return s
	push_warning("未定義的關卡：%s" % id)
	return {}


func get_level(path: String) -> Dictionary:
	if not _levels.has(path):
		var level: Variant = load_json(path)
		_levels[path] = level if level is Dictionary else {}
	return _levels[path]


static func load_json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		push_error("找不到資料檔：%s" % path)
		return null
	var text := FileAccess.get_file_as_string(path)
	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		push_error("JSON 格式錯誤 %s 第 %d 行：%s" % [path, json.get_error_line(), json.get_error_message()])
		return null
	return json.data
