extends Node
## 操作與手感測試（在測試用沙盒關卡）：
##   Shift 兩下轉身、Shift 一下衝刺；空白鍵往前小跳、空中再按一次二段跳（較高較遠、主角前空翻）；
##   小台階自動滾上去；E 第一人稱環視；數字鍵 1 到 5 切換視角；
##   按住 Shift 集氣（四段各 1 秒、主角慢慢往前推且越來越快）放開衝出去（黃光 3 倍、藍色火焰 5 倍）；
##   衝刺撞到比自己大的東西會反彈並掉好幾件；R 回到中間。
##
## 用法（專案根目錄）：
##   godot --headless --fixed-fps 60 res://tests/controls_test.tscn

var _stage: Stage
var _fails: Array[String] = []
var _frame := 0
var _script: Array = []
var _vars: Dictionary = {}


func _ready() -> void:
	Game.persist = false
	# 固定亂數：場景裡的貓狗會隨機走動，不固定的話偶爾會擋到測試路線
	seed(20261017)
	_stage = Stage.new()
	_stage.setup("sandbox")
	_stage.skip_intro = true
	add_child(_stage)
	_k().double_jumped.connect(func(): _vars["double"] = true)
	_k().crashed.connect(func(_s: float, lost: int): _vars["crash_lost"] = lost)
	_k().charge_level_changed.connect(func(l: int):
		if _vars.has("levels"):
			_vars["levels"].append([l, _frame]))
	var f := 60
	# 每一步：[第幾個物理幀, 動作]
	_script = [
		[f, func(): _vars["yaw"] = _cam().yaw; Input.action_press("kb_shift")],
		[f + 1, func(): Input.action_release("kb_shift")],
		[f + 8, func(): Input.action_press("kb_shift")],
		[f + 9, func(): Input.action_release("kb_shift")],
		[f + 40, func():
			_check(absf(wrapf(_cam().yaw - _vars["yaw"], -PI, PI)) > 2.8, "Shift 按兩下：轉身半圈")
			_check(not _k().is_dashing(), "Shift 按兩下：不會衝刺")
			_vars["yaw"] = _cam().yaw
			Input.action_press("kb_shift")],
		[f + 41, func(): Input.action_release("kb_shift")],
		[f + 64, func():
			_check(_k().is_dashing(), "Shift 按一下：衝刺")
			_check(absf(wrapf(_cam().yaw - _vars["yaw"], -PI, PI)) < 0.05, "Shift 按一下：不會轉身")],
		# 站著按一下跳：往前小跳，不會跳很高
		[f + 140, func(): _place(Vector3(100, 0, 300), PI)],
		[f + 180, func(): _start_jump("single"); _tap("jump")],
		[f + 260, func():
			var d := _k().diameter
			var dist: float = _vars.get("land_single", 0.0)
			var peak: float = _vars["peak_single"]
			_check(dist > d * 0.6, "站著跳也會往前跳一小段（%.1f 公分，直徑 %.1f）" % [dist, d])
			_check(peak > d * 0.3 and peak < d * 1.6, "跳的高度合理、不會太高（%.1f 公分）" % peak)],
		# 二段跳：空中再按一次，更高更遠，主角前空翻
		[f + 280, func(): _place(Vector3(100, 0, 300), PI)],
		[f + 320, func(): _vars["double"] = false; _start_jump("double"); _tap("jump")],
		[f + 334, func(): _tap("jump")],
		[f + 430, func():
			_check(bool(_vars["double"]), "空中再按一次：二段跳（主角前空翻）")
			_check(float(_vars["peak_double"]) > float(_vars["peak_single"]) * 1.4,
				"二段跳比較高（%.1f 對 %.1f 公分）" % [_vars["peak_double"], _vars["peak_single"]])
			_check(float(_vars.get("land_double", 0.0)) > float(_vars.get("land_single", 0.0)) * 1.3,
				"二段跳比較遠（%.1f 對 %.1f 公分）" % [_vars.get("land_double", 0.0), _vars.get("land_single", 0.0)])],
		# 小台階（3 公分）：推過去自動滾上去，不用跳
		[f + 450, func(): _place(Vector3(300, 0, 330), PI); _vars["step_top"] = 0.0; Input.action_press("kb_forward")],
		[f + 630, func():
			Input.action_release("kb_forward")
			_vars.erase("step_watch")
			_check(float(_vars["step_top"]) > 2.5, "推向 3 公分的台階會自動滾上去（底部最高 %.1f 公分，直徑 %.1f）" % [_vars["step_top"], _k().diameter])],
		# 第一人稱環視
		[f + 650, func(): _place(Vector3(700, 0, 300), PI); Input.action_press("free_look")],
		[f + 651, func(): Input.action_release("free_look"); Input.action_press("kb_forward")],
		[f + 710, func():
			_check(_cam().free_look, "E：進入第一人稱環視")
			_check(_k().horizontal_speed() < 1.0, "環視時按 W 球不會動（%.1f 公分每秒）" % _k().horizontal_speed())
			_check(-_cam().camera.global_transform.basis.z.y > 0.3, "環視時按 W 會抬頭看")
			Input.action_release("kb_forward")
			Input.action_press("free_look")],
		[f + 711, func(): Input.action_release("free_look")],
		[f + 715, func(): _check(not _cam().free_look, "再按 E：回到原本的視角")],
		# 視角 1 到 5
		[f + 720, func(): _tap("view_1")],
		[f + 750, func():
			_check(_cam().view == 1 and _cam().is_first_person(), "數字 1：第一人稱")
			_vars["d1"] = _cam_dist()
			_tap("view_2")],
		[f + 810, func(): _vars["d2"] = _cam_dist(); _tap("view_3")],
		[f + 870, func(): _vars["d3"] = _cam_dist(); _tap("view_4")],
		[f + 930, func():
			_vars["d4"] = _cam_dist()
			_check(_vars["d1"] < _vars["d2"] and _vars["d2"] < _vars["d3"] and _vars["d3"] < _vars["d4"],
				"數字 1 到 4 越來越遠（%.1f、%.1f、%.1f、%.1f 公分）" % [_vars["d1"], _vars["d2"], _vars["d3"], _vars["d4"]])
			_tap("view_5")],
		[f + 990, func():
			var fwd := Vector3(-sin(_cam().yaw), 0.0, -cos(_cam().yaw))
			var rel := _cam().camera.global_position - _k().global_position
			_check(rel.dot(fwd) > 0.0, "數字 5：鏡頭在球的正前方，面對主角")
			_tap("view_3")],
		# 集氣：按住 Shift，四段各 1 秒；主角慢慢往前推、越來越快；放開衝出去
		[f + 1000, func(): _place(Vector3(700, 0, 220), PI)],
		[f + 1040, func():
			_vars["levels"] = []
			_vars["charge_from"] = _frame
			Input.action_press("kb_shift")],
		[f + 1040 + 105, func():
			_check(_k().is_charging(), "按住 Shift：開始集氣")
			_vars["spin_1"] = _k().angular_velocity.length()
			_vars["creep_1"] = _k().horizontal_speed()
			var fx := _stage.charge_fx.get_child(0) as Node3D
			_check(fx.visible, "集氣時球外面有一層光")],
		[f + 1040 + 225, func(): _vars["creep_3"] = _k().horizontal_speed()],
		[f + 1040 + 270, func():
			var top := _top()
			_check(float(_vars["creep_1"]) > top * 0.05 and float(_vars["creep_1"]) < top * 0.35,
				"集氣時主角慢慢往前推（第 1 段 %.1f 公分每秒，最高速 %.1f）" % [_vars["creep_1"], top])
			_check(float(_vars["creep_3"]) > float(_vars["creep_1"]) * 1.3,
				"段數越高推得越快（第 1 段 %.1f、第 3 段 %.1f 公分每秒）" % [_vars["creep_1"], _vars["creep_3"]])
			_check(_k().angular_velocity.length() > float(_vars["spin_1"]) * 1.3,
				"集氣越久球轉得越快（%.0f → %.0f 弧度每秒）" % [_vars["spin_1"], _k().angular_velocity.length()])
			_check(_k().charge_level() == 4, "4 秒後變成藍色火焰（第 %d 段）" % _k().charge_level())
			var lv: Array = _vars["levels"]
			var ok := lv.size() == 4
			var desc := []
			for e in lv:
				var sec := float(int(e[1]) - int(_vars["charge_from"])) / 60.0
				desc.append("%d段 %.2f秒" % [e[0], sec])
				# 從按下 Shift 起算：0.25 秒判定為按住，之後每段 1 秒
				ok = ok and absf(sec - (0.25 + float(e[0]) + 0.02)) < 0.1
			_check(ok, "每一段集氣約 1 秒（%s）" % "、".join(desc))
			_vars["base_top"] = top
			_vars["burst_peak"] = 0.0
			Input.action_release("kb_shift")],
		[f + 1040 + 290, func():
			_check(_k().is_bursting(), "放開後衝出去")
			_check(_stage.cam.camera.fov > 75.0, "衝出去時視野拉寬（%.0f 度）" % _stage.cam.camera.fov)],
		[f + 1040 + 330, func():
			_vars["blue_peak"] = _vars["burst_peak"]
			_vars.erase("burst_peak")
			_check(float(_vars["blue_peak"]) > float(_vars["base_top"]) * 4.5,
				"藍色火焰衝刺是平常最高速的 %.1f 倍" % (float(_vars["blue_peak"]) / float(_vars["base_top"])))],
		# 只集氣 1.3 秒（黃光）就放開：至少 3 倍，比藍色火焰慢
		[f + 1440, func(): _place(Vector3(700, 0, 220), PI)],
		[f + 1480, func(): Input.action_press("kb_shift")],
		[f + 1480 + 93, func():
			_check(_k().charge_level() == 1, "集氣 1 秒後是黃光（第 %d 段）" % _k().charge_level())
			_vars["base_top"] = _top()
			_vars["burst_peak"] = 0.0
			Input.action_release("kb_shift")],
		[f + 1480 + 133, func():
			var peak := float(_vars["burst_peak"])
			_vars.erase("burst_peak")
			_check(peak > float(_vars["base_top"]) * 2.9, "黃光放開也有 %.1f 倍速（至少 3 倍）" % (peak / float(_vars["base_top"])))
			_check(peak < float(_vars["blue_peak"]) * 0.8, "黃光衝刺比藍色火焰慢（%.0f 對 %.0f 公分每秒）" % [peak, _vars["blue_peak"]])],
		# 衝刺撞到比自己大的東西（桌子側面）：反彈，掉好幾件
		[f + 1660, func():
			_place(Vector3(370, 0, 76), -PI / 2.0)
			# 先在球旁邊放幾顆彈珠讓它黏上，撞的時候才有東西掉
			for i in 6:
				var it := PickupItem.spawn(Data.get_item("marble"))
				_stage.items_root.add_child(it)
				it.global_position = Vector3(370.0 + float(i % 3) * 1.5 - 1.5, 0.0, 74.0 + float(i / 3) * 3.0)],
		[f + 1700, func():
			_vars["count_before"] = _k().collected_count
			Input.action_press("kb_shift")],
		[f + 1700 + 150, func(): Input.action_release("kb_shift")],
		[f + 1700 + 240, func():
			_check(_vars.has("crash_lost"), "衝刺撞到桌子：反彈")
			_check(int(_vars.get("crash_lost", 0)) >= 2, "撞擊力道大，掉了 %d 件（撞前黏了 %d 件）" % [_vars.get("crash_lost", 0), _vars["count_before"]])
			_check(_k().global_position.x < 450.0 - _k().radius(), "反彈後在桌子外面（x = %.0f）" % _k().global_position.x)],
		# R：回到中間
		[f + 1960, func(): _tap("rescue")],
		[f + 1970, func():
			var p := _k().global_position
			_check(Vector2(p.x - 400.0, p.z - 300.0).length() < 5.0, "R：回到中間（%.0f, %.0f）" % [p.x, p.z])
			_finish()],
	]


## 把球放到指定位置、面向 yaw，速度歸零
func _place(pos: Vector3, yaw: float) -> void:
	var k := _k()
	k.linear_velocity = Vector3.ZERO
	k.angular_velocity = Vector3.ZERO
	k.global_position = pos + Vector3.UP * (k.radius() + 0.5)
	k.reset_physics_interpolation()
	_cam().yaw = yaw
	_cam().snap()


func _tap(action: String) -> void:
	Input.action_press(action)
	get_tree().create_timer(0.03, true, true).timeout.connect(func(): Input.action_release(action))


func _top() -> float:
	return maxf(_k().max_speed_d * _k().diameter, _k().min_top_speed)


func _start_jump(tag: String) -> void:
	_vars["jump_tag"] = tag
	_vars["jump_from"] = _k().global_position
	_vars["jump_frames"] = 0
	_vars["peak_" + tag] = 0.0


func _k() -> Katamari:
	return _stage.katamari


func _cam() -> KatamariCamera:
	return _stage.cam


func _cam_dist() -> float:
	return _cam().camera.global_position.distance_to(_k().global_position)


func _flat(v: Vector3) -> float:
	return Vector2(v.x, v.z).length()


func _check(ok: bool, what: String) -> void:
	print("[controls] %s：%s" % ["ok" if ok else "失敗", what])
	if not ok:
		_fails.append(what)


func _physics_process(_delta: float) -> void:
	_frame += 1
	if _vars.has("burst_peak"):
		_vars["burst_peak"] = maxf(float(_vars["burst_peak"]), _k().horizontal_speed())
	if _vars.has("step_top"):
		var p := _k().global_position
		if p.z > 372.0 and p.z < 428.0:
			_vars["step_top"] = maxf(float(_vars["step_top"]), p.y - _k().radius())
	if _vars.has("jump_tag"):
		var tag := str(_vars["jump_tag"])
		_vars["jump_frames"] = int(_vars["jump_frames"]) + 1
		_vars["peak_" + tag] = maxf(float(_vars["peak_" + tag]), _k().global_position.y - (_vars["jump_from"] as Vector3).y)
		if int(_vars["jump_frames"]) > 6 and _k().is_grounded():
			_vars["land_" + tag] = _flat(_k().global_position - _vars["jump_from"])
			_vars.erase("jump_tag")
	while not _script.is_empty() and _frame >= int(_script[0][0]):
		var step: Array = _script.pop_front()
		(step[1] as Callable).call()


func _finish() -> void:
	if _fails.is_empty():
		print("[controls] PASS")
		get_tree().quit(0)
	else:
		printerr("[controls] FAIL：", ", ".join(_fails))
		get_tree().quit(1)
