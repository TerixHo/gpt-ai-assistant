extends Node
## 資料中心：載入所有資料驅動設定（物件、關卡、場景配置）。
## 所有尺寸單位為公分，世界座標 1 單位 = 1 公分。
##
## 物件定義分成多個檔案：data/items.json 是共用物件，各關卡專屬的物件放在 data/items/*.json，
## 由 stages.json 的 item_files 列出（匯出後的網頁版不一定能列目錄，所以明確列出）。
## 關卡設定可以寫在 stages.json，也可以寫在場景配置檔的 "stage" 區塊；stages.json 有寫的欄位優先。

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
	var stage_data: Variant = load_json(STAGES_PATH)
	var files: Array = [ITEMS_PATH]
	if stage_data is Dictionary:
		for f in stage_data.get("item_files", []):
			if not files.has(f):
				files.append(f)
	for path in files:
		# 還沒做好的關卡物件檔先略過
		if path != ITEMS_PATH and not FileAccess.file_exists(path):
			continue
		var item_data: Variant = load_json(path)
		if item_data is Dictionary:
			for def in item_data.get("items", []):
				if items.has(def["id"]):
					push_warning("物件 id 重複：%s（%s）" % [def["id"], path])
				items[def["id"]] = def
	stages = []
	if stage_data is Dictionary:
		for s in stage_data.get("stages", []):
			stages.append(_merge_stage(s))


## 把場景配置檔裡的 "stage" 區塊併入關卡設定（stages.json 有寫的欄位優先）。
func _merge_stage(s: Dictionary) -> Dictionary:
	var path: String = s.get("level", "")
	if path.is_empty() or not FileAccess.file_exists(path):
		return s
	var level := get_level(path)
	var extra: Dictionary = level.get("stage", {})
	if extra.is_empty():
		return s
	var merged := extra.duplicate(true)
	for k in s:
		merged[k] = s[k]
	return merged


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


## 選關畫面與「下一關」用：不含隱藏的測試關卡。
func visible_stages() -> Array:
	return stages.filter(func(s): return not s.get("hidden", false))


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
