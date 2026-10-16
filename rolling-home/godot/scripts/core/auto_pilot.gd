class_name AutoPilot
extends Node
## 自動駕駛：朝最近的可吸附物件滾過去。
## 用途：自動化測試、難度平衡（量測達標時間）、標題畫面展示。
## 只透過 Controls.override_drive 下指令，與真人玩家走同一條輸入路徑。

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
	var best: PickupItem = null
	var best_score := INF
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
		var score := Vector2(q.x - p.x, q.z - p.z).length() + absf(dy) * 3.0
		score -= item.size_cm * 2.0
		if score < best_score:
			best_score = score
			best = item
	return best
