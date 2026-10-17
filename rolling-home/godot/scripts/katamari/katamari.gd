class_name Katamari
extends RigidBody3D
## 塊球本體：滾動、吸附、成長、撞落。
##
## 成長模型：塊球以「體積」累積，直徑 = 由體積反推的球體直徑。
## 吸附條件：物件尺寸 ≤ 直徑 × pickup_ratio，且碰到塊球（或其突出物）。
## 撞落規則：以高速撞上牆或過大的物件時，最外層的幾個物件會掉落並扣回體積。
## 外觀：白色核心加上粉彩彩虹小圓點；最後黏的 10 件會突出在球的外圍，
## 滾動時它們轉到底下就把球撐高一點、往旁邊推一點，形成不規則的滾動。
## 所有數值皆可在檢視器調整，預設值見 docs/01_遊戲設定文件.md 第 4 章。

signal collected(item_id: String, def: Dictionary)
signal diameter_changed(diameter_cm: float)
signal bumped(strength: float, lost: int)
signal dashed
signal jumped
## 空中再跳一次（二段跳，主角會前空翻）
signal double_jumped
## 集氣衝刺撞到比自己大的東西：反彈並掉落 lost 件
signal crashed(strength: float, lost: int)
## 集氣升段（1 黃、2 橘、3 紅、4 藍色火焰）
signal charge_level_changed(level: int)
## 集氣放開衝出去
signal launched(level: int)

## 突出在外圍的最新物件數
const RECENT_COUNT := 10
## 不規則滾動：突出物轉到底下時把球撐高的比例（1 = 完全照突出高度）
const LUMP_GAIN := 0.65
## 吸附範圍的固定餘裕（公分）：物理引擎會在極近距離就停住，小球需要這點餘裕才黏得到 6mm 珠子
const GRAB_EXTRA := 0.2

@export var start_diameter_cm := 5.0
## 可吸附門檻：物件尺寸 ≤ 直徑 × 此比例
@export_range(0.05, 1.5) var pickup_ratio := 0.7
## 物件體積併入塊球的全域倍率（調整整體成長速度）
@export var growth_gain := 1.0
## 最高速度：每秒幾個直徑
@export var max_speed_d := 3.0
## 最高速度下限（公分/秒），避免太小時寸步難行
@export var min_top_speed := 8.0
## 加速度：每秒² 幾個直徑
@export var accel_d := 7.0
## 放開搖桿時的減速度：每秒² 幾個直徑
@export var coast_decel_d := 2.5
@export var dash_speed_mult := 2.1
@export var dash_duration := 0.8
## 撞擊掉落門檻：撞擊速度超過每秒幾個直徑
@export var knock_threshold_d := 2.9
## 吸附偵測球相對於本體半徑的倍率
@export var grab_margin := 1.1
## 台階輔助：推著接觸點低於「半徑 × 此比例」的低矮障礙物或地板落差時自動滾上去。
## 接觸點在球的赤道以上代表是牆或櫃子側面，不觸發（要跳）。
@export var step_up_ratio := 1.0
## 每次撞擊最多掉幾件（給小朋友玩，不宜太多）
@export var max_drop := 2
## 跳躍：往前小跳一段。高度 = 直徑 × jump_height_d + jump_min_cm（公分）
@export var jump_height_d := 0.55
@export var jump_min_cm := 3.0
## 起跳時往前的速度至少是最高速的幾倍（站著不動按跳也會往前跳）
@export var jump_forward := 1.3
## 二段跳（空中再按一次）：更高、更遠，主角前空翻
@export var double_height_d := 1.1
@export var double_min_cm := 5.0
@export var double_forward := 1.75
## 跳在空中時的重力倍率（輕一點，小朋友看得出在空中）
@export var jump_gravity := 0.5

## 集氣：每一段 1 秒，共四段（黃、橘、紅、藍色火焰）
const CHARGE_STAGE_TIME := 1.0
const CHARGE_LEVELS := 4
## 集氣中主角慢慢往前推的速度（最高速的倍率，依段數越來越快）
const CHARGE_CREEP := [0.12, 0.18, 0.26, 0.34, 0.45]
## 放開時依段數的爆發：[最高速倍率, 持續秒數]（第 0 項是還沒滿 1 秒就放開；滿 1 秒以上至少 3 倍）
const BURST := [[1.8, 0.5], [3.0, 0.8], [3.5, 1.0], [4.0, 1.2], [5.0, 1.5]]

var diameter := 5.0
var volume := 0.0
var collected_count := 0
var collected_by_id: Dictionary = {}
## 撞落物件要放回的父節點（由關卡指定）
var items_parent: Node
var input_enabled := true

var _move := Vector2.ZERO
var _yaw := 0.0
var _dash_left := 0.0
var _grounded := false
var _ground_normal := Vector3.UP
var _last_velocity := Vector3.ZERO
var _knock_cooldown := 0.0
var _pending_knock: Dictionary = {}
var _pending_lift := 0.0
var _step_cooldown := 0.0
var _air_time := 0.0
var _jump_request := false
var _double_request := false
var _double_used := false
var _jump_cooldown := 0.0
var _jump_air := 0.0
var _charging := false
var _charge_time := 0.0
var _burst_request := false
var _burst_left := 0.0
var _burst_total := 0.0
var _burst_mult := 1.0
var _burst_level := 0
var _body_shape := SphereShape3D.new()
var _grab_shape := SphereShape3D.new()
var _query := PhysicsShapeQueryParameters3D.new()
var _core: Node3D
var _stuck_root: Node3D
## 每個黏上的物件：{node, id, def, size, volume, dist, half, dir（本地方向）, basis（本地朝向）, cy（中心離底面的高度）}
var _stuck: Array[Dictionary] = []
## 最新黏上的物件（最多 RECENT_COUNT 件），突出在外圍
var _recent: Array[Dictionary] = []
## 不規則滾動：目前突出物把球撐高的量（公分）與側推方向
var _lump := 0.0
var _lump_lift := 0.0
var _wobble := Vector3.ZERO


func _ready() -> void:
	name = "Katamari"
	add_to_group("katamari")
	collision_layer = KMath.LAYER_KATAMARI
	collision_mask = KMath.LAYER_WORLD | KMath.LAYER_ITEM | KMath.LAYER_GATE
	continuous_cd = true
	can_sleep = false
	contact_monitor = true
	max_contacts_reported = 16
	var pm := PhysicsMaterial.new()
	pm.friction = 1.0
	pm.bounce = 0.0
	physics_material_override = pm

	var cs := CollisionShape3D.new()
	cs.name = "Shape"
	cs.shape = _body_shape
	add_child(cs)
	_core = _build_core()
	add_child(_core)
	_stuck_root = Node3D.new()
	_stuck_root.name = "Stuck"
	add_child(_stuck_root)

	_query.shape = _grab_shape
	_query.collision_mask = KMath.LAYER_ITEM
	_query.collide_with_bodies = true
	_query.collide_with_areas = false

	volume = KMath.sphere_volume(start_diameter_cm)
	_apply_size()


func radius() -> float:
	return diameter * 0.5


func is_grounded() -> bool:
	return _grounded


func horizontal_speed() -> float:
	return Vector2(linear_velocity.x, linear_velocity.z).length()


## move：x 平移、y 前進（相機座標）；yaw：相機水平角（弧度）。
func set_drive(move: Vector2, yaw: float) -> void:
	_move = move.limit_length(1.0) if input_enabled else Vector2.ZERO
	_yaw = yaw


func dash() -> bool:
	if _dash_left > -0.6 or not input_enabled:
		return false
	_dash_left = dash_duration
	dashed.emit()
	return true


func is_dashing() -> bool:
	return _dash_left > 0.0


## 起跳：接地或剛離地一瞬間是往前小跳；跳起來之後在空中再按一次是二段跳（只能一次）。
func jump() -> bool:
	if not input_enabled:
		return false
	if _air_time <= 0.12 and _jump_cooldown <= 0.0:
		_jump_request = true
		_double_used = false
		return true
	if _jump_air > 0.08 and not _double_used:
		_double_request = true
		_double_used = true
		return true
	return false


## 舊介面（按住跳更高已取消，跳躍高度固定），保留給呼叫端。
func release_jump() -> void:
	pass


func is_jumping() -> bool:
	return _jump_air > 0.0


## 突出物撐高的量（公分），給鏡頭與主角用
func lump() -> float:
	return _lump


## 外觀半徑：含突出在外圍的物件（鏡頭用來決定要退多遠）
func visual_radius() -> float:
	var r := radius()
	for e in _recent:
		r = maxf(r, float(e["dist"]) + float(e["half"]))
	return r


## 開始集氣：主角慢慢往前推，球越轉越快。
func charge_begin() -> bool:
	if not input_enabled or _charging:
		return false
	_charging = true
	_charge_time = 0.0
	return true


func is_charging() -> bool:
	return _charging


## 目前的集氣段數（0 還沒滿 1 秒，1 黃、2 橘、3 紅、4 藍色火焰）
func charge_level() -> int:
	return mini(int(_charge_time / CHARGE_STAGE_TIME), CHARGE_LEVELS) if _charging else 0


func charge_time() -> float:
	return _charge_time if _charging else 0.0


## 放開：依段數瞬間加速衝出去。回傳段數；沒有在集氣時回傳 -1。
func charge_release() -> int:
	if not _charging:
		return -1
	var lvl := charge_level()
	_charging = false
	_charge_time = 0.0
	if not input_enabled:
		return -1
	_burst_level = lvl
	_burst_mult = float(BURST[lvl][0])
	_burst_total = float(BURST[lvl][1])
	_burst_left = _burst_total
	_burst_request = true
	launched.emit(lvl)
	return lvl


func charge_cancel() -> void:
	_charging = false
	_charge_time = 0.0


func is_bursting() -> bool:
	return _burst_left > 0.0


## 衝刺的速度感強度（0 到 1），給鏡頭與畫面特效用
func boost_amount() -> float:
	if _burst_left <= 0.0:
		return 0.0
	return clampf(_burst_left / maxf(_burst_total, 0.01), 0.0, 1.0) * (0.45 + 0.55 * float(_burst_level) / CHARGE_LEVELS)


func burst_level() -> int:
	return _burst_level


## 被外力打到（例如貓咪伸爪）：推開並掉落 drop 件物件。
func external_hit(dir: Vector3, push_speed: float, drop := 1) -> void:
	if _knock_cooldown > 0.0:
		return
	var d := Vector3(dir.x, 0.0, dir.z).normalized()
	apply_central_impulse((d + Vector3.UP * 0.35) * push_speed * mass)
	_pending_knock = {"strength": knock_threshold_d, "ratio": 1.0 + float(drop - 1) * 0.5, "normal": d}
	_knock_cooldown = 0.6


func forward_dir() -> Vector3:
	return Vector3(-sin(_yaw), 0.0, -cos(_yaw))


func _physics_process(delta: float) -> void:
	_knock_cooldown -= delta
	_dash_left -= delta
	_burst_left = maxf(_burst_left - delta, 0.0)
	if _charging:
		var before := charge_level()
		_charge_time = minf(_charge_time + delta, CHARGE_STAGE_TIME * (CHARGE_LEVELS + 1))
		var now := charge_level()
		if now != before:
			charge_level_changed.emit(now)
	if not _pending_knock.is_empty():
		var k := _pending_knock
		_pending_knock = {}
		_knock(k)
	_grab_check()
	_update_lump(delta)


## 不規則滾動：最新的突出物轉到球底下時，把碰撞球放大（球心被撐高），並往反方向推一點。
func _update_lump(delta: float) -> void:
	var r := radius()
	var basis := global_transform.basis
	var target := 0.0
	var side := Vector3.ZERO
	for e in _recent:
		var out := float(e["dist"]) + float(e["half"]) - r
		if out <= 0.0:
			continue
		var d: Vector3 = basis * (e["dir"] as Vector3)
		var width := clampf(float(e["half"]) / maxf(r, 0.01), 0.2, 0.7)
		var f := smoothstep(cos(width), 1.0, -d.y)
		var lift := out * f * LUMP_GAIN
		if lift > target:
			target = lift
			side = -Vector3(d.x, 0.0, d.z)
	var before := _lump
	# 升降速度有上限，避免一下子彈起來
	_lump = move_toward(_lump, target, maxf(r * 6.0, 6.0) * delta)
	if _grounded and _lump > before:
		_lump_lift += _lump - before
	_wobble = side * (_lump / maxf(r, 0.01))
	_body_shape.radius = r + _lump


func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:
	var dt := state.step
	# 1. 接觸分析：地面法線與撞擊強度
	_grounded = false
	var n_sum := Vector3.ZERO
	var impact := 0.0
	var impact_normal := Vector3.ZERO
	var step_normal := Vector3.ZERO
	var step_height := 0.0
	var bottom := state.transform.origin.y - radius()
	for i in state.get_contact_count():
		var n := state.get_contact_local_normal(i)
		if n.y > 0.55:
			_grounded = true
			n_sum += n
		else:
			# 低矮障礙（黏不起來的鉛筆、蠟筆、積木）：記下來，稍後在推向它時把球抬上去
			var cp := state.get_contact_local_position(i)
			var h := cp.y - bottom
			var obj := state.get_contact_collider_object(i)
			var pickable_now := obj is PickupItem and KMath.can_pick((obj as PickupItem).size_cm, diameter, pickup_ratio)
			if not pickable_now and h < radius() * step_up_ratio and h > diameter * 0.05 and h > step_height:
				step_normal = n
				step_height = h
			# 碰到本來就黏得起來的小東西不算撞擊
			var other := state.get_contact_collider_object(i)
			if other is PickupItem and KMath.can_pick((other as PickupItem).size_cm, diameter, pickup_ratio):
				continue
			# 只算水平方向的撞擊（掉落、跳過障礙後落地不算）
			var nh := Vector3(n.x, 0.0, n.z)
			var into := -Vector3(_last_velocity.x, 0.0, _last_velocity.z).dot(nh)
			if into > impact:
				impact = into
				impact_normal = n
	_ground_normal = n_sum.normalized() if _grounded else Vector3.UP
	_air_time = 0.0 if _grounded else _air_time + dt
	_jump_cooldown -= dt

	if _pending_lift > 0.0 or _lump_lift > 0.0:
		var t := state.transform
		t.origin += Vector3.UP * (_pending_lift + _lump_lift)
		state.transform = t
		_pending_lift = 0.0
		_lump_lift = 0.0

	# 2. 驅動：以速度導向方式控制，接地時沿地面平面移動
	var fwd := forward_dir()
	var right := Vector3(cos(_yaw), 0.0, -sin(_yaw))
	var wish := right * _move.x + fwd * _move.y
	var wish_len := minf(wish.length(), 1.0)
	var top := maxf(max_speed_d * diameter, min_top_speed)
	var base_top := top
	if _dash_left > 0.0:
		wish = fwd
		wish_len = 1.0
		top *= dash_speed_mult
	# 集氣衝刺：一路往前，最高速依段數加成，隨時間慢慢退回
	if _burst_left > 0.0:
		wish = fwd
		wish_len = 1.0
		var k := _burst_left / maxf(_burst_total, 0.01)
		top = base_top * lerpf(1.2, _burst_mult, k)
	# 集氣中：主角慢慢往前推（方向鍵用來轉向），段數越高推得越快
	if _charging:
		wish = fwd
		wish_len = 1.0
		top = base_top * float(CHARGE_CREEP[charge_level()])
	var up := _ground_normal
	var v := state.linear_velocity
	var v_plane := v - up * v.dot(up)
	var target := Vector3.ZERO
	var accel: float
	var dir := Vector3.ZERO
	if wish_len > 0.01:
		dir = (wish - up * wish.dot(up)).normalized()
		target = dir * top * wish_len
		accel = maxf(accel_d * diameter, 25.0) * (1.0 if _grounded else 0.3)
	else:
		accel = maxf(coast_decel_d * diameter, 10.0) if _grounded else 0.0
	var dv := (target - v_plane).limit_length(accel * dt)
	v += dv
	# 突出物在旁邊底下時往反方向推一點（不規則滾動）
	if _grounded and _wobble != Vector3.ZERO and v_plane.length() > base_top * 0.2:
		v += _wobble * base_top * 1.2 * dt
	# 上坡時只抵銷「與前進方向相反」的重力分量，讓上坡手感接近原作。
	# （不能整個抵銷：在台階邊角時接觸法線會傾斜，整個抵銷會把球吸回邊緣。）
	if _grounded and wish_len > 0.01:
		var g := state.total_gravity
		var along := (g - up * g.dot(up)).dot(dir)
		if along < 0.0:
			v -= dir * along * dt
	# 台階輔助：正推著低矮障礙時，給剛好跳過障礙高度的向上速度（v = √(2gh)）
	_step_cooldown -= dt
	if _grounded and _step_cooldown <= 0.0 and step_normal != Vector3.ZERO and wish_len > 0.3 and dir.dot(-step_normal) > 0.3:
		var g_len := state.total_gravity.length()
		v.y = maxf(v.y, sqrt(2.0 * g_len * (step_height + diameter * 0.12)))
		_step_cooldown = 0.3
	# 跳躍：給剛好跳到目標高度的向上速度（v = √(2gh)），並確保往前的速度，站著按跳也會往前跳一小段
	var g_jump := state.total_gravity.length() * jump_gravity
	if _jump_request:
		_jump_request = false
		var h := jump_height_d * diameter + jump_min_cm
		v.y = maxf(v.y, 0.0) + sqrt(2.0 * g_jump * h)
		v = _push_forward(v, fwd, base_top * jump_forward)
		_air_time = 1.0
		_jump_air = 0.0001
		_jump_cooldown = 0.25
		_step_cooldown = 0.3
		jumped.emit.call_deferred()
	# 二段跳：更高、更遠
	if _double_request:
		_double_request = false
		var h2 := double_height_d * diameter + double_min_cm
		v.y = sqrt(2.0 * g_jump * h2)
		v = _push_forward(v, fwd, base_top * double_forward)
		_jump_air = 0.0001
		double_jumped.emit.call_deferred()
	# 跳在空中時抵銷部分重力（落地就恢復）
	if _jump_air > 0.0:
		_jump_air += dt
		if _grounded and _jump_air > 0.1:
			_jump_air = 0.0
		else:
			v.y += state.total_gravity.length() * (1.0 - jump_gravity) * dt
	# 放開集氣：瞬間加速到目標速度
	if _burst_request:
		_burst_request = false
		var burst_v := fwd * top
		v.x = burst_v.x
		v.z = burst_v.z
		_step_cooldown = 0.0
	# 非衝刺時限制水平速度，避免碰撞把彈跳轉成暴衝（跳在空中時放寬，保留跳躍的加速）
	if _dash_left <= 0.0 and _burst_left <= 0.0:
		var vh := Vector3(v.x, 0.0, v.z)
		var cap := base_top * (2.0 if _jump_air > 0.0 else (1.25 if _air_time < 0.5 else 1.6))
		if vh.length() > cap:
			vh = vh.normalized() * cap
			v.x = vh.x
			v.z = vh.z
	state.linear_velocity = v

	# 3. 接地時讓角速度貼近純滾動，外觀上確實在「滾」；集氣時在原地越轉越快
	if _charging:
		var spin := TAU * (2.0 + 10.0 * minf(_charge_time / (CHARGE_STAGE_TIME * CHARGE_LEVELS), 1.0))
		state.angular_velocity = up.cross(fwd).normalized() * spin
	elif _grounded:
		var roll := up.cross(v) / maxf(radius(), 0.01)
		state.angular_velocity = state.angular_velocity.lerp(roll, 0.35)

	# 4. 撞擊偵測（實際掉落在 _physics_process 處理，避免在物理回呼中增刪節點）
	# 撞落門檻至少要比平常最高速度快（衝刺或從高處摔下才會掉東西）
	var knock_at := maxf(knock_threshold_d * diameter, base_top * 1.3)
	if _burst_left > 0.0 and impact > base_top * 0.9 and _knock_cooldown <= 0.0:
		# 集氣衝刺撞到比自己大的東西（牆、大家具）：依撞擊力道反彈，掉下好幾件
		v = _bounce(v, impact, impact_normal, base_top, state.total_gravity.length())
		state.linear_velocity = v
		var drop := clampi(1 + _burst_level + int(impact / maxf(base_top * 2.0, 0.01)), 1, 6)
		_pending_knock = {"strength": impact / diameter, "ratio": impact / knock_at, "normal": impact_normal, "drop": drop, "crash": true}
		_burst_left = 0.0
		_knock_cooldown = 0.7
	elif impact > knock_at and _knock_cooldown <= 0.0:
		_pending_knock = {"strength": impact / diameter, "ratio": impact / knock_at, "normal": impact_normal}
		_knock_cooldown = 0.5
	_last_velocity = v


## 往 fwd 方向的速度至少要有 want（不夠就補上，原本更快就不變）。
func _push_forward(v: Vector3, fwd: Vector3, want: float) -> Vector3:
	var along := Vector3(v.x, 0.0, v.z).dot(fwd)
	if along < want:
		v += fwd * (want - along)
	return v


## 反彈：水平速度沿撞擊面反射並減弱，再往外推、往上彈一點。
func _bounce(v: Vector3, impact: float, normal: Vector3, base_top: float, g: float) -> Vector3:
	var nh := Vector3(normal.x, 0.0, normal.z)
	if nh.length_squared() < 0.0001:
		nh = -forward_dir()
	nh = nh.normalized()
	var vh := Vector3(_last_velocity.x, 0.0, _last_velocity.z)
	var out := (vh - 2.0 * vh.dot(nh) * nh) * 0.35 + nh * impact * 0.45
	out = out.limit_length(maxf(base_top * 2.2, impact * 0.7))
	return Vector3(out.x, maxf(v.y, sqrt(2.0 * g * diameter * 0.3)), out.z)


func _grab_check() -> void:
	var space := get_world_3d().direct_space_state
	_query.transform = Transform3D(Basis.IDENTITY, global_position)
	# 突出物把球撐高時，吸附範圍也跟著放大，才黏得到地上的東西
	_grab_shape.radius = radius() * grab_margin + GRAB_EXTRA + _lump
	_try_hits(space.intersect_shape(_query, 32))
	# 突出在外圍的大物件也能黏東西（迭代副本：吸附過程可能改變清單）
	var r := radius()
	for e in _recent.duplicate():
		if float(e["size"]) < diameter * 0.26:
			continue
		var tip := float(e["dist"]) + float(e["half"]) * 0.4
		if tip + float(e["half"]) * 0.55 < r * 1.04:
			continue
		_grab_shape.radius = float(e["half"]) * 0.55 * 1.15
		_query.transform = Transform3D(Basis.IDENTITY, global_transform * ((e["dir"] as Vector3) * tip))
		_try_hits(space.intersect_shape(_query, 8))
	_grab_shape.radius = radius() * grab_margin + GRAB_EXTRA


func _try_hits(hits: Array[Dictionary]) -> void:
	for h in hits:
		var body: Object = h.get("collider")
		if body is PickupItem:
			var item := body as PickupItem
			if item.is_pickable() and KMath.can_pick(item.size_cm, diameter, pickup_ratio):
				_attach(item)


func _attach(item: PickupItem) -> void:
	var dims := PropFactory.dims_of(item.def)
	var v := item.take_visual()
	var gt := v.transform
	var item_center := gt * Vector3(0.0, dims.y * 0.5, 0.0)
	var to_item := item_center - global_position
	if to_item.length_squared() < 0.000001:
		to_item = Vector3.UP
	_stuck_root.add_child(v)
	# 換成球的本地座標：方向與朝向都跟著球轉
	var inv := global_transform.basis.inverse()
	var local_basis := (inv * gt.basis).orthonormalized()
	var e := {"node": v, "id": item.item_id, "def": item.def, "size": item.size_cm,
		"half": item.size_cm * 0.5, "dir": (inv * to_item).normalized(), "basis": local_basis,
		"scale": gt.basis.get_scale(), "cy": dims.y * 0.5, "dist": radius() * 0.96, "color": item.color_override}
	var gain := KMath.item_volume(item.size_cm, float(item.def.get("fill", 0.5))) * growth_gain
	volume += gain
	e["volume"] = gain
	_stuck.append(e)
	_recent.append(e)
	# 超過 10 件：最舊的那件慢慢沉回球面
	if _recent.size() > RECENT_COUNT:
		var old_e: Dictionary = _recent.pop_front()
		old_e["dist"] = radius() * 0.96
		_place_stuck(old_e)
	collected_count += 1
	collected_by_id[item.item_id] = int(collected_by_id.get(item.item_id, 0)) + 1
	item.queue_free()
	var old := diameter
	_apply_size()
	if _grounded:
		_pending_lift += maxf(diameter - old, 0.0) * 0.5
	v.reset_physics_interpolation()
	collected.emit(item.item_id, item.def)


## 依方向與距離把黏上的物件放到球上（物件中心在 dir × dist）。
func _place_stuck(e: Dictionary) -> void:
	var node: Node3D = e["node"]
	if not is_instance_valid(node):
		return
	var b: Basis = (e["basis"] as Basis).scaled(e["scale"])
	var center: Vector3 = (e["dir"] as Vector3) * float(e["dist"])
	node.transform = Transform3D(b, center - b * Vector3(0.0, float(e["cy"]), 0.0))


func _apply_size() -> void:
	diameter = KMath.diameter_from_volume(volume)
	var r := radius()
	_body_shape.radius = r + _lump
	_grab_shape.radius = r * grab_margin + GRAB_EXTRA
	_core.scale = Vector3.ONE * diameter * 0.9
	mass = maxf(0.02, volume * 0.0008)
	# 最新的 10 件跟著球面往外移，保持突出在外圍（中心比球面再外面一點，大半截露在外面）
	for e in _recent:
		e["dist"] = r + float(e["half"]) * 0.15
		_place_stuck(e)
	_prune()
	diameter_changed.emit(diameter)


## 被新物件覆蓋、完全埋進核心的物件就移除，維持效能（突出在外圍的最新物件不移除）。
func _prune() -> void:
	var core_r := radius() * 0.9
	var keep: Array[Dictionary] = []
	for e in _stuck:
		if not _recent.has(e) and float(e["dist"]) + float(e["half"]) * 0.6 < core_r:
			var node: Node3D = e["node"]
			if is_instance_valid(node):
				node.queue_free()
		else:
			keep.append(e)
	_stuck = keep


func _knock(k: Dictionary) -> void:
	var strength: float = k["strength"]
	var normal: Vector3 = k["normal"]
	var ratio: float = k.get("ratio", 1.0)
	var drop := int(k["drop"]) if k.has("drop") else clampi(1 + int((ratio - 1.0) * 2.0), 1, max_drop)
	var crash: bool = k.get("crash", false)
	var lost := 0
	var min_volume := KMath.sphere_volume(start_diameter_cm)
	for i in drop:
		if _stuck.is_empty() or items_parent == null:
			break
		var e: Dictionary = _stuck.pop_back()
		_recent.erase(e)
		var node: Node3D = e["node"]
		if not is_instance_valid(node):
			continue
		var gt := node.global_transform
		node.queue_free()
		var item := PickupItem.spawn(e["def"], e.get("color", ""))
		items_parent.add_child(item)
		item.global_transform = gt
		item.reset_physics_interpolation()
		var out := (gt.origin - global_position).normalized()
		var power := maxf(diameter * (4.5 if crash else 3.0), 30.0)
		item.launch((out + normal * 0.6 + Vector3.UP).normalized() * power, 1.2 if crash else 0.8)
		volume = maxf(volume - float(e["volume"]), min_volume)
		collected_count = maxi(collected_count - 1, 0)
		var id: String = e["id"]
		collected_by_id[id] = maxi(int(collected_by_id.get(id, 1)) - 1, 0)
		lost += 1
	if lost > 0:
		_apply_size()
	if crash:
		crashed.emit(strength, lost)
	else:
		bumped.emit(strength, lost)


## 核心：白色球體，外面有一顆顆突起的小圓點，每一點是不同的淡粉彩虹色（合併成一個網格，只有一次繪製）。
const DOT_COLORS := ["#ffc8dd", "#ffd6a5", "#fdffb6", "#caffbf", "#9bf6ff", "#a0c4ff", "#bdb2ff", "#ffadad"]
const DOT_COUNT := 26


func _build_core() -> Node3D:
	var root := Node3D.new()
	root.name = "Core"
	var surf := SurfaceTool.new()
	surf.begin(Mesh.PRIMITIVE_TRIANGLES)
	_append_sphere(surf, Vector3.ZERO, 0.5, Color("#fbfaf7"), 24, 12)
	# 黃金角螺旋把圓點平均分布在球面上
	var golden := PI * (3.0 - sqrt(5.0))
	for i in DOT_COUNT:
		var y := 1.0 - (float(i) + 0.5) / DOT_COUNT * 2.0
		var rr := sqrt(1.0 - y * y)
		var a := golden * i
		var n := Vector3(cos(a) * rr, y, sin(a) * rr)
		_append_sphere(surf, n * 0.49, 0.075, Color(DOT_COLORS[i % DOT_COLORS.size()]), 10, 5)
	surf.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = surf.commit()
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.roughness = 0.45
	m.rim_enabled = true
	m.rim = 0.25
	mi.material_override = m
	root.add_child(mi)
	return root


static func _append_sphere(surf: SurfaceTool, center: Vector3, r: float, c: Color, seg: int, rings: int) -> void:
	var pts: Array[Vector3] = []
	for j in rings + 1:
		var v := float(j) / rings
		var phi := v * PI
		for i in seg + 1:
			var th := float(i) / seg * TAU
			pts.append(center + Vector3(sin(phi) * cos(th), cos(phi), sin(phi) * sin(th)) * r)
	surf.set_smooth_group(0)
	for j in rings:
		for i in seg:
			var a := j * (seg + 1) + i
			var b := a + seg + 1
			# Godot 的正面是順時針（從外面看），三角形依這個順序排
			for idx in [a, b, a + 1, a + 1, b, b + 1]:
				surf.set_color(c)
				surf.add_vertex(pts[idx])
