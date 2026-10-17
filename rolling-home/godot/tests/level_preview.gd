extends Node
## 場景配置檔預覽截圖：載入關卡（不開始遊戲），從指定的鏡頭位置拍照，或拍整張俯視地圖。
## 用來檢查房間佈置、積木樓梯、物件分布，不用實際滾過去。
##
## 用法（需要畫面，在 rolling-home/godot 執行）：
##   godot --rendering-driver opengl3 res://tests/level_preview.tscn -- --stage home --out 資料夾 \
##       [--map] [--cams "名稱:x,y,z>x,y,z;名稱2:..."] [--fov 60] [--size 1280x720] [--hide-ball]
##   --map：從正上方往下拍整個場景（依地板範圍自動決定大小）
##   --cams：鏡頭位置 > 看向的點（公分）

var _stage: Stage
var _out := "user://preview"
var _jobs: Array = []
var _cam: Camera3D
var _frame := 0


func _ready() -> void:
	Game.persist = false
	var args := OS.get_cmdline_user_args()
	_out = _arg(args, "--out", _out)
	DirAccess.make_dir_recursive_absolute(_out)
	var size := _arg(args, "--size", "1280x720").split("x")
	get_window().size = Vector2i(int(size[0]), int(size[1]))
	_stage = Stage.new()
	_stage.setup(_arg(args, "--stage", "home"))
	_stage.skip_intro = true
	_stage.demo = true
	add_child(_stage)
	if args.has("--hide-ball"):
		_stage.katamari.visible = false
		_stage.pusher.visible = false
	_cam = Camera3D.new()
	_cam.far = 200000.0
	_cam.near = 1.0
	_cam.fov = float(_arg(args, "--fov", "60"))
	add_child(_cam)
	if args.has("--map"):
		_jobs.append({"name": "map"})
	for spec in _arg(args, "--cams", "").split(";", false):
		var parts := spec.split(":")
		var pts := parts[1].split(">")
		_jobs.append({"name": parts[0], "from": _v(pts[0]), "to": _v(pts[1])})


func _v(text: String) -> Vector3:
	var a := text.split(",")
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _arg(args: PackedStringArray, key: String, fallback: String) -> String:
	var i := args.find(key)
	return args[i + 1] if i >= 0 and i + 1 < args.size() else fallback


func _process(_delta: float) -> void:
	_frame += 1
	# 前幾幀讓場景與粒子就位
	if _frame < 8:
		return
	if _jobs.is_empty():
		get_tree().quit()
		return
	var job: Dictionary = _jobs[0]
	if not job.has("ready"):
		job["ready"] = true
		_cam.current = true
		if job["name"] == "map":
			_setup_map()
		else:
			_cam.projection = Camera3D.PROJECTION_PERSPECTIVE
			_cam.global_position = job["from"]
			_cam.look_at(job["to"], Vector3.UP if absf((job["to"] - job["from"]).normalized().y) < 0.99 else Vector3.FORWARD)
		return
	_jobs.pop_front()
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [_out, job["name"]])
	print("[preview] 已存 %s/%s.png" % [_out, job["name"]])


## 俯視：涵蓋所有地板的範圍（排除最大那塊室外地面，避免整張圖都是草地）
func _setup_map() -> void:
	var level := Data.get_level(_stage.stage_def.get("level", ""))
	var rect := Rect2()
	var first := true
	var floors: Array = level.get("floors", [])
	var areas: Array[float] = []
	for f in floors:
		areas.append(float(f["rect"][2]) * float(f["rect"][3]))
	areas.sort()
	# 最大那塊比第二大的大很多（整片室外地面）才排除
	var skip_area := areas[-1] if areas.size() > 1 and areas[-1] > areas[-2] * 4.0 else INF
	for f in floors:
		var r := Rect2(float(f["rect"][0]), float(f["rect"][1]), float(f["rect"][2]), float(f["rect"][3]))
		if r.get_area() >= skip_area:
			continue
		rect = r if first else rect.merge(r)
		first = false
	rect = rect.grow(rect.size.length() * 0.03)
	_cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	var aspect := float(get_window().size.x) / float(get_window().size.y)
	_cam.size = maxf(rect.size.y, rect.size.x / aspect)
	var c := rect.get_center()
	_cam.global_position = Vector3(c.x, 20000.0, c.y)
	_cam.look_at(Vector3(c.x, 0, c.y), Vector3.FORWARD)
