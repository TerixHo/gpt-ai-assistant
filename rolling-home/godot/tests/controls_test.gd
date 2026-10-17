extends Node
## 鍵盤操作測試：Shift 兩下轉身、Shift 一下衝刺、空白鍵跳躍（按住更高、跑越快跳越遠）、
## E 第一人稱環視、數字鍵 1 到 5 切換視角、按住 Shift 集氣（四段各 1 秒）放開衝出去。
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
	_stage = Stage.new()
	_stage.setup("home_2")
	_stage.skip_intro = true
	add_child(_stage)
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
		# 輕按空白鍵
		[f + 160, func(): _vars["y0"] = _k().global_position.y; _vars["peak"] = 0.0; Input.action_press("jump")],
		[f + 161, func(): Input.action_release("jump")],
		[f + 220, func(): _vars["tap"] = _vars["peak"]],
		# 按住空白鍵
		[f + 260, func(): _vars["y0"] = _k().global_position.y; _vars["peak"] = 0.0; Input.action_press("jump")],
		[f + 320, func(): Input.action_release("jump")],
		[f + 340, func():
			_vars["hold"] = _vars["peak"]
			_check(_vars["hold"] > _vars["tap"] * 1.5, "按住空白鍵跳得比輕按高（按住 %.1f 公分、輕按 %.1f 公分）" % [_vars["hold"], _vars["tap"]])],
		# 跑越快跳越遠：一般奔跑中起跳 vs 衝刺中起跳，量起跳到落地的水平距離
		[f + 380, func(): Input.action_press("kb_forward")],
		[f + 470, func(): _start_jump_measure("run"); Input.action_press("jump")],
		[f + 500, func(): Input.action_release("jump")],
		[f + 560, func():
			Input.action_press("kb_shift")],
		[f + 561, func(): Input.action_release("kb_shift")],
		[f + 590, func(): _start_jump_measure("dash"); Input.action_press("jump")],
		[f + 620, func(): Input.action_release("jump")],
		[f + 680, func():
			Input.action_release("kb_forward")
			var run: float = _vars.get("land_run", 0.0)
			var dash: float = _vars.get("land_dash", 0.0)
			_check(run > 3.0, "奔跑中跳躍會往前飛（%.1f 公分，起跳速度 %.0f 公分每秒）" % [run, _vars.get("speed_run", 0.0)])
			_check(dash > run * 1.3, "衝刺時跳得比一般奔跑遠（衝刺 %.1f 公分、起跳速度 %.0f；一般 %.1f 公分）" % [dash, _vars.get("speed_dash", 0.0), run])],
		# 第一人稱環視
		[f + 700, func(): Input.action_press("free_look")],
		[f + 701, func(): Input.action_release("free_look"); Input.action_press("kb_forward")],
		[f + 760, func():
			_check(_cam().free_look, "E：進入第一人稱環視")
			_check(_k().horizontal_speed() < 1.0, "環視時按 W 球不會動（%.1f 公分每秒）" % _k().horizontal_speed())
			_check(-_cam().camera.global_transform.basis.z.y > 0.3, "環視時按 W 會抬頭看")
			Input.action_release("kb_forward")
			Input.action_press("free_look")],
		[f + 761, func(): Input.action_release("free_look")],
		[f + 765, func(): _check(not _cam().free_look, "再按 E：回到原本的視角")],
		# 視角 1 到 5
		[f + 770, func(): Input.action_press("view_1")],
		[f + 771, func(): Input.action_release("view_1")],
		[f + 800, func():
			_check(_cam().view == 1 and _cam().is_first_person(), "數字 1：第一人稱")
			_vars["d1"] = _cam_dist()
			Input.action_press("view_2")],
		[f + 801, func(): Input.action_release("view_2")],
		[f + 860, func(): _vars["d2"] = _cam_dist(); Input.action_press("view_3")],
		[f + 861, func(): Input.action_release("view_3")],
		[f + 920, func(): _vars["d3"] = _cam_dist(); Input.action_press("view_4")],
		[f + 921, func(): Input.action_release("view_4")],
		[f + 980, func():
			_vars["d4"] = _cam_dist()
			_check(_vars["d1"] < _vars["d2"] and _vars["d2"] < _vars["d3"] and _vars["d3"] < _vars["d4"],
				"數字 1 到 4 越來越遠（%.1f、%.1f、%.1f、%.1f 公分）" % [_vars["d1"], _vars["d2"], _vars["d3"], _vars["d4"]])
			Input.action_press("view_5")],
		[f + 981, func(): Input.action_release("view_5")],
		[f + 1040, func():
			var fwd := Vector3(-sin(_cam().yaw), 0.0, -cos(_cam().yaw))
			var rel := _cam().camera.global_position - _k().global_position
			_check(rel.dot(fwd) > 0.0, "數字 5：鏡頭在球的正前方，面對主角")
			Input.action_press("view_3")],
		[f + 1041, func(): Input.action_release("view_3")],
		# 集氣：按住 Shift，四段各 1 秒（黃、橘、紅、藍色火焰），放開衝出去
		[f + 1100, func():
			_vars["levels"] = []
			_k().charge_level_changed.connect(func(l: int): _vars["levels"].append([l, _frame]))
			_vars["charge_from"] = _frame
			Input.action_press("kb_shift")],
		[f + 1100 + 150, func():
			_check(_k().is_charging(), "按住 Shift：開始集氣")
			_vars["spin_mid"] = _k().angular_velocity.length()
			var fx := _stage.charge_fx.get_child(0) as Node3D
			_check(fx.visible, "集氣時球外面有一層光")],
		[f + 1100 + 270, func():
			_check(_k().horizontal_speed() < 1.0, "集氣時球停在原地（%.1f 公分每秒）" % _k().horizontal_speed())
			_check(_k().angular_velocity.length() > float(_vars["spin_mid"]) * 1.3,
				"集氣越久轉得越快（%.0f → %.0f 弧度每秒）" % [_vars["spin_mid"], _k().angular_velocity.length()])
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
			_vars["base_top"] = maxf(_k().max_speed_d * _k().diameter, _k().min_top_speed)
			_vars["burst_peak"] = 0.0
			Input.action_release("kb_shift")],
		[f + 1100 + 290, func():
			_check(_k().is_bursting(), "放開後衝出去")
			_check(_stage.cam.camera.fov > 75.0, "衝出去時視野拉寬（%.0f 度）" % _stage.cam.camera.fov)],
		[f + 1100 + 330, func():
			_vars["blue_peak"] = _vars["burst_peak"]
			_check(float(_vars["blue_peak"]) > float(_vars["base_top"]) * 2.5,
				"藍色火焰衝刺速度是平常最高速的 %.1f 倍" % (float(_vars["blue_peak"]) / float(_vars["base_top"])))],
		# 只集氣 1.3 秒（黃光）就放開，衝得比藍色火焰慢
		[f + 1500, func(): Input.action_press("kb_shift")],
		[f + 1500 + 93, func():
			_check(_k().charge_level() == 1, "集氣 1 秒後是黃光（第 %d 段）" % _k().charge_level())
			_vars["burst_peak"] = 0.0
			Input.action_release("kb_shift")],
		[f + 1500 + 133, func():
			_check(float(_vars["burst_peak"]) < float(_vars["blue_peak"]) * 0.8,
				"黃光衝刺比藍色火焰慢（%.0f 對 %.0f 公分每秒）" % [_vars["burst_peak"], _vars["blue_peak"]])
			_finish()],
	]


func _start_jump_measure(tag: String) -> void:
	_vars["jump_tag"] = tag
	_vars["jump_from"] = _k().global_position
	_vars["jump_frames"] = 0
	_vars["speed_" + tag] = _k().horizontal_speed()


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
	if _vars.has("y0"):
		_vars["peak"] = maxf(float(_vars.get("peak", 0.0)), _k().global_position.y - float(_vars["y0"]))
	if _vars.has("burst_peak"):
		_vars["burst_peak"] = maxf(float(_vars["burst_peak"]), _k().horizontal_speed())
	if _vars.has("jump_tag"):
		_vars["jump_frames"] = int(_vars["jump_frames"]) + 1
		if int(_vars["jump_frames"]) > 6 and _k().is_grounded():
			_vars["land_" + str(_vars["jump_tag"])] = _flat(_k().global_position - _vars["jump_from"])
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
