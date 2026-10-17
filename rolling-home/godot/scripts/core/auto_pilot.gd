class_name AutoPilot
extends Node
## 自動駕駛：朝最近的可吸附物件滾過去。
## 用途：自動化測試、難度平衡（量測達標時間）、標題畫面展示。
## 只透過 Controls.override_drive 下指令，與真人玩家走同一條輸入路徑。
## 被夾住動不了時會按「回到中間」（真人玩家這時也會看到那顆按鈕）；找不到目標時往中間走。

var stage: Stage
var _drive := Controls.Drive.new()
var _target: PickupItem
var _retarget := 0.0
var _stuck_time := 0.0
var _best_dist := INF
var _escape_time := 0.0
var _escape_turn := 1.0
var _blacklist: Dictionary = {}
var _clock := 0.0
## 被夾住偵測：一段時間內位置幾乎沒變
var _wedge_anchor := Vector3.ZERO
var _wedge_time := 0.0


func _ready() -> void:
	Controls.override_drive = _drive


func _exit_tree() -> void:
	if Controls.override_drive == _drive:
		Controls.override_drive = null


func _physics_process(delta: float) -> void:
	_clock += delta
	if stage == null or stage.katamari == null or stage.state != "playing":
		return
	var k := stage.katamari
	_drive.dash = false
	_drive.quick_turn = false
	_drive.rescue = false
	# 被夾住：6 秒內移動不到 0.3 個直徑（不管目標是什麼），按回到中間
	var moved := k.global_position - _wedge_anchor
	if Vector2(moved.x, moved.z).length() > k.diameter * 0.3:
		_wedge_anchor = k.global_position
		_wedge_time = 0.0
	else:
		_wedge_time += delta
		if _wedge_time > 6.0:
			_wedge_time = 0.0
			_drive.rescue = true
			_target = null
			_escape_time = 0.0
			return
	if _escape_time > 0.0:
		_escape_time -= delta
		_drive.move = Vector2(0, -0.6)
		_drive.turn = _escape_turn
		return
	_retarget -= delta
	if _retarget <= 0.0 or _target == null or not is_instance_valid(_target) or _target.collected:
		var t := _pick_target(k)
		if t != _target:
			_best_dist = INF
			_stuck_time = 0.0
		_target = t
		_retarget = 0.5
	if _target == null:
		# 找不到過得去的目標：往中間（救援點）走，通常就能看到別的房間
		var home: Vector3 = stage.get("_rescue_pos")
		var to_home := home - k.global_position
		if Vector2(to_home.x, to_home.z).length() > k.diameter * 2.0:
			var hy := atan2(-to_home.x, -to_home.z)
			var hd := wrapf(hy - stage.cam.yaw, -PI, PI)
			_drive.turn = clampf(-hd * 2.5, -1.0, 1.0)
			_drive.move = Vector2(0, clampf(cos(hd), 0.2, 1.0))
		else:
			_drive.move = Vector2(0, 0.6)
			_drive.turn = 0.4
		return
	var to := _target.global_position - k.global_position
	var desired_yaw := atan2(-to.x, -to.z)
	var diff := wrapf(desired_yaw - stage.cam.yaw, -PI, PI)
	_drive.turn = clampf(-diff * 2.5, -1.0, 1.0)
	_drive.move = Vector2(0, clampf(cos(diff), 0.0, 1.0))
	# 卡住偵測：一段時間內與目標的距離沒有縮短
	var dist := Vector2(to.x, to.z).length()
	_stuck_time += delta
	if dist < _best_dist - k.diameter * 0.3:
		_best_dist = dist
		_stuck_time = 0.0
	if _stuck_time > 1.5:
		_best_dist = INF
		_stuck_time = 0.0
		_escape_time = 0.8
		_escape_turn = 1.0 if randf() > 0.5 else -1.0
		# 卡住時把目標與附近一整區暫時列為避開，逼自己換地方
		var here := k.global_position
		for child in stage.items_root.get_children():
			var item := child as PickupItem
			if item != null and item.global_position.distance_to(here) < k.diameter * 2.5:
				_blacklist[item.get_instance_id()] = _clock + 12.0
		if _target != null:
			_blacklist[_target.get_instance_id()] = _clock + 12.0
		_target = null


func _pick_target(k: Katamari) -> PickupItem:
	# 先找同一個高度（例如同一張桌面）上的目標，沒有了才往下找
	var same := _pick(k, true)
	return same if same != null else _pick(k, false)


func _pick(k: Katamari, same_level: bool) -> PickupItem:
	var candidates: Array = []
	var p := k.global_position
	var bottom := p.y - k.radius()
	for child in stage.items_root.get_children():
		var item := child as PickupItem
		if item == null or not item.is_pickable():
			continue
		if not KMath.can_pick(item.size_cm, k.diameter, k.pickup_ratio):
			continue
		if _blacklist.get(item.get_instance_id(), 0.0) > _clock:
			continue
		var q := item.global_position
		var dy := q.y - bottom
		# 高於塊球的東西（桌上、架上）通常到不了
		if dy > k.radius() * 0.8:
			continue
		if same_level and dy < -maxf(k.diameter, 3.0):
			continue
		var score := Vector2(q.x - p.x, q.z - p.z).length() + absf(dy) * 3.0
		# 越大的東西越值得去黏；相對太小的東西（米粒之於大球）幾乎不會讓球長大
		score -= item.size_cm * 6.0
		if item.size_cm < k.diameter * 0.1:
			score += 400.0
		candidates.append([score, item])
	candidates.sort_custom(func(a, b): return a[0] < b[0])
	# 只挑整顆球過得去的目標（沒有被牆、門框或還沒打開的門擋住），機器人不會繞路
	var space := k.get_world_3d().direct_space_state
	var cast := PhysicsShapeQueryParameters3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = k.radius() * 0.85
	cast.shape = sphere
	cast.collision_mask = KMath.LAYER_WORLD | KMath.LAYER_GATE
	var start := p + Vector3.UP * k.radius() * 0.2
	cast.transform = Transform3D(Basis.IDENTITY, start)
	# 房間多的場景，分數最高的目標常常在隔壁房間被牆擋住，所以多檢查一些
	for i in mini(candidates.size(), 48):
		var item: PickupItem = candidates[i][1]
		var goal := item.global_position
		goal.y = start.y
		cast.motion = goal - start
		var frac := space.cast_motion(cast)
		if frac.is_empty() or frac[0] >= 0.98:
			return item
	return null
