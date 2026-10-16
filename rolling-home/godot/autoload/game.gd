extends Node
## 遊戲進度與設定：目前關卡、成績、收藏目錄、玩家設定，存於 user://save.json。

const SAVE_PATH := "user://save.json"

var current_stage_id := "home_1"
var last_result: Dictionary = {}
## 收藏目錄：物件 id -> 累計收集數
var collection: Dictionary = {}
## 各關最佳直徑（公分）
var best: Dictionary = {}
var settings: Dictionary = {
	"control_scheme": "simple",
	"camera_turn_speed": 1.0,
	"sfx_volume": 0.8,
	"music_volume": 0.5,
	## 注音模式：介面改用注音版粉圓字型，方便低年級小朋友閱讀
	"zhuyin": false,
	## 不限時間：練習或年紀較小的小朋友可以慢慢滾
	"no_time_limit": false,
}
## 測試或錄影時可關閉存檔
var persist := true


const FONT_NORMAL := "res://assets/fonts/Huninn-Regular.ttf"
const FONT_ZHUYIN := "res://assets/fonts/BpmfHuninn-Regular.ttf"


func _ready() -> void:
	load_save()
	apply_font.call_deferred()


## 依設定切換全域字型（一般／注音）。
func apply_font() -> void:
	var path := FONT_ZHUYIN if settings.get("zhuyin", false) else FONT_NORMAL
	if not ResourceLoader.exists(path):
		return
	var theme := Theme.new()
	theme.default_font = load(path)
	get_tree().root.theme = theme


func toggle_setting(key: String) -> void:
	settings[key] = not bool(settings.get(key, false))
	if key == "zhuyin":
		apply_font()
	save()


func record_result(result: Dictionary) -> void:
	last_result = result
	var items: Dictionary = result.get("items", {})
	for id in items:
		collection[id] = int(collection.get(id, 0)) + int(items[id])
	var sid: String = result.get("stage_id", "")
	if float(result.get("diameter_cm", 0.0)) > float(best.get(sid, 0.0)):
		best[sid] = result["diameter_cm"]
	save()


func next_stage_id(stage_id: String) -> String:
	var stages: Array = Data.stages
	for i in stages.size():
		if stages[i]["id"] == stage_id and i + 1 < stages.size():
			return stages[i + 1]["id"]
	return ""


func is_stage_playable(stage_id: String) -> bool:
	var stage := Data.get_stage(stage_id)
	return not stage.is_empty() and stage.get("playable", false)


func save() -> void:
	if not persist:
		return
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		push_warning("無法寫入存檔：%s" % error_string(FileAccess.get_open_error()))
		return
	f.store_string(JSON.stringify({
		"version": 1,
		"collection": collection,
		"best": best,
		"settings": settings,
	}, "\t"))


func load_save() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	if data is Dictionary:
		collection = data.get("collection", {})
		best = data.get("best", {})
		var s: Dictionary = data.get("settings", {})
		for k in s:
			if settings.has(k):
				settings[k] = s[k]
