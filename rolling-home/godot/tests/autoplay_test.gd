extends Node
## 自動遊玩測試：由 AutoPilot 實際玩一關，輸出成長曲線並檢查基本行為。
##
## 用法（專案根目錄）：
##   godot --headless --fixed-fps 60 res://tests/autoplay_test.tscn -- --stage home_1
## 選用參數：
##   --seconds N        只跑 N 秒（預設跑完整關）
##   --shots a,b,c      在第 a、b、c 秒截圖（需非 headless 模式）
##   --shot-dir PATH    截圖輸出資料夾（預設 user://shots）
##   --fast             非截圖時段暫停渲染（物理步長不變），加快軟體渲染下的截圖流程
##   --seed N           固定亂數種子，讓測試可重現

var _stage: Stage
var _pilot: AutoPilot
var _elapsed := 0.0
var _limit := -1.0
var _shots: Array[float] = []
var _shot_dir := "user://shots"
var _next_log := 0.0
var _log: Array[String] = []
var _done := false
var _start_diameter := 0.0
var _fast := false


func _ready() -> void:
	Game.persist = false
	var args := OS.get_cmdline_user_args()
	var stage_id := _arg(args, "--stage", "home_1")
	_limit = float(_arg(args, "--seconds", "-1"))
	_shot_dir = _arg(args, "--shot-dir", _shot_dir)
	for s in _arg(args, "--shots", "").split(",", false):
		_shots.append(float(s))
	DirAccess.make_dir_recursive_absolute(_shot_dir)
	_fast = args.has("--fast")
	var rng_seed := int(_arg(args, "--seed", "0"))
	if rng_seed != 0:
		seed(rng_seed)

	_stage = Stage.new()
	_stage.setup(stage_id)
	_stage.skip_intro = true
	_stage.finished.connect(_on_finished)
	_stage.gate_opened.connect(func(id: String, d: float):
		print("[autoplay] t=%5.1fs 門檻開啟：%s（直徑 %s）" % [_elapsed, id, KMath.format_size(d)]))
	add_child(_stage)
	_pilot = AutoPilot.new()
	_pilot.stage = _stage
	add_child(_pilot)
	_start_diameter = _stage.katamari.diameter
	print("[autoplay] 關卡 %s：生成物件 %d 件，起始 %s，目標 %s，時限 %s" % [
		stage_id, _stage.spawned_count, KMath.format_size(_start_diameter),
		KMath.format_size(_stage.goal), KMath.format_time(_stage.time_total)])


func _arg(args: PackedStringArray, key: String, fallback: String) -> String:
	var i := args.find(key)
	return args[i + 1] if i >= 0 and i + 1 < args.size() else fallback


func _physics_process(delta: float) -> void:
	if _done:
		return
	_elapsed += delta
	if _elapsed >= _next_log:
		_next_log += 10.0
		var k := _stage.katamari
		var line := "[autoplay] t=%5.1fs 直徑=%s 件數=%d 速度=%.1fcm/s 位置=(%.0f, %.0f, %.0f) 區域=%s" % [
			_elapsed, KMath.format_size(k.diameter), k.collected_count, k.horizontal_speed(),
			k.global_position.x, k.global_position.y, k.global_position.z, _stage._current_area]
		print(line)
		_log.append(line)
	if _fast:
		RenderingServer.render_loop_enabled = _shots.is_empty() or _shots[0] - _elapsed < 0.4
	if not _shots.is_empty() and _elapsed >= _shots[0]:
		_shots.pop_front()
		_screenshot()
	if _limit > 0.0 and _elapsed >= _limit:
		_finish(_stage.build_result())


func _screenshot() -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "%s/shot_%03d.png" % [_shot_dir, int(_elapsed)]
	img.save_png(path)
	print("[autoplay] 截圖：", ProjectSettings.globalize_path(path))


func _on_finished(result: Dictionary) -> void:
	_finish(result)


func _finish(result: Dictionary) -> void:
	if _done:
		return
	_done = true
	var failures: Array[String] = []
	if float(result["diameter_cm"]) <= _start_diameter + 0.5:
		failures.append("塊球沒有成長")
	if int(result["count"]) < 10:
		failures.append("吸附件數過少：%d" % int(result["count"]))
	print("[autoplay] 結果：直徑 %s／目標 %s，%s，件數 %d，達標用時 %s" % [
		KMath.format_size(result["diameter_cm"]), KMath.format_size(result["goal_cm"]),
		"過關" if result["success"] else "未過關", result["count"],
		KMath.format_time(result["time_to_goal"]) if float(result["time_to_goal"]) >= 0.0 else "未達標"])
	if failures.is_empty():
		print("[autoplay] PASS")
		get_tree().quit(0)
	else:
		for f in failures:
			printerr("[autoplay] FAIL：", f)
		get_tree().quit(1)
