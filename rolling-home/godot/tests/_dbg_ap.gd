extends Node
var _stage: Stage
var _pilot: AutoPilot
var _t := 0.0
func _ready() -> void:
	Game.persist = false
	seed(1)
	_stage = Stage.new()
	_stage.setup("home_3")
	_stage.skip_intro = true
	add_child(_stage)
	_pilot = AutoPilot.new()
	_pilot.stage = _stage
	add_child(_pilot)
func _physics_process(delta: float) -> void:
	_t += delta
	var k := _stage.katamari
	if _t > 165.0 and _t < 185.0 and int(_t * 60) % 20 == 0:
		var tgt = _pilot.get("_target")
		print("[dbg] t=%.1f p=(%.0f,%.1f,%.0f) d=%.1f g=%s lump=%.1f lift=%.1f hov=%.2f v=%s tgt=%s esc=%.2f" % [_t, k.global_position.x, k.global_position.y, k.global_position.z, k.diameter, k.is_grounded(), k.lump(), k.get("_step_lift"), k.get("_step_hover"), k.linear_velocity.snapped(Vector3.ONE), (tgt.item_id + "@" + str(tgt.global_position.snapped(Vector3.ONE))) if tgt != null and is_instance_valid(tgt) else "-", _pilot.get("_escape_time")])
	if _t > 186.0:
		get_tree().quit()
