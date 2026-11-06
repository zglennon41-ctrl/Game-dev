## One beast of a pack: everything the fight needs to run it. The foe the hero is locked on to
## lives in the Fight's w_* fields (the full behaviour: breaks, counters, the Pattern's marks);
## the rest of the pack are Foes, with the same bites and the same deaths.
class_name Foe
extends RefCounted

var beast: Dictionary = {}
var pos := Vector2.ZERO
var facing := 0.0
var hp := 0.0
var state := "prowl"   # prowl, approach, windup, strike, recover, stagger, down, absent
var timer := 0.0
var duration := 0.0
var attack: Dictionary = {}
var hit_done := false
var angle := 0.0
var dir := 1.0
var target := -1       # -1 the hero, else an ally's index
var burn_until := -9.0
var hits_taken := 0
var breaks := 0
var named := false
var pattern_hits := 0
var shape := ""

func set_state(s: String, d: float) -> void:
	state = s
	timer = 0.0
	duration = d

func alive() -> bool:
	return state not in ["down", "absent"]
