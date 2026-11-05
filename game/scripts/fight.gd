## The pulse room's fight, with no drawing. Time is seconds on the beat clock; positions are
## meters on the ground plane (x, z) held as Vector2. The room and the tests drive it.
class_name Fight
extends RefCounted

var room: Dictionary
var rules: Dictionary
var beast: Dictionary
var t0: float
var period: float
var window_ms: float
var arena: Vector2
var player_shape: String
var passive: bool
var respawn: bool
var rng := RandomNumberGenerator.new()

var events: Array = []
var stats := { "inputs": 0, "perfect": 0, "offsets": [], "hits": 0, "damage_dealt": 0, "longest_chain": 0,
	"parries": 0, "blocks": 0, "hurts": 0, "dodges": 0, "staggers": 0, "wolves_down": 0, "fumbles": 0 }

# The Anchor.
var p_pos := Vector2.ZERO
var p_hp: float
var p_will: float
var p_stance := false
var p_guard := false
var p_fainted := false
var p_down := false
var p_chain := 0
var p_last_action_beat := -999
var p_last_hold_beat := -999
var p_parry_beat := -999
var p_stance_pending := -1
var p_facing := 0.0

# The wolf.
var w_pos := Vector2.ZERO
var w_hp: float
var w_mode := "circle"   # circle, approach, windup, recover, stagger, down, idle
var w_until := 0
var w_strike_beat := -1
var w_angle := 0.0
var w_ready := false
var w_pending := -1

var breaks := CombatRules.BreakMeter.new()
var last_beat := -1
var now := 0.0

func _init(opts: Dictionary = {}) -> void:
	room = Data.room
	rules = Data.rules
	beast = Data.beast(opts.get("beast", "cut-wolf"))
	player_shape = room["player"]["shape"]
	t0 = opts.get("t0", 0.0)
	period = opts.get("period", float(Data.shape(player_shape)["pulseMs"]) / 1000.0)
	window_ms = opts.get("window_ms", Data.beat_window_ms(room["line"]))
	arena = Vector2(room["arena"]["width"], room["arena"]["depth"])
	passive = opts.get("passive", false)
	respawn = opts.get("respawn", true)
	rng.seed = opts.get("seed", 7)
	p_hp = room["player"]["health"]
	p_will = rules["field"]["willMax"]
	p_pos = Vector2(-arena.x * 0.15, arena.y * 0.1)
	_spawn_wolf(-1)
	now = t0

func beat_time(k: int) -> float:
	return t0 + k * period

func breaks_beast() -> bool:
	return Data.opposite(player_shape) == beast["shape"]

func half_window() -> float:
	return window_ms / 2000.0

func _emit(e: Dictionary) -> void:
	events.append(e)

func drain() -> Array:
	var e := events
	events = []
	return e

func dist() -> float:
	return p_pos.distance_to(w_pos)

func _clamp_in(v: Vector2) -> Vector2:
	var h := arena / 2.0 - Vector2(0.6, 0.6)
	return Vector2(clampf(v.x, -h.x, h.x), clampf(v.y, -h.y, h.y))

func _spawn_wolf(k: int) -> void:
	w_hp = beast["health"]
	w_angle = rng.randf() * TAU
	w_pos = _clamp_in(p_pos + Vector2.from_angle(w_angle) * float(beast["circleRadius"]) * 1.4)
	_set_circle(k)
	w_pending = -1
	if k >= 0:
		_emit({ "type": "wolf-up", "t": now })

func _set_circle(k: int) -> void:
	var c: Dictionary = beast["circleBeats"]
	w_mode = "idle" if passive else "circle"
	w_until = k + int(c["min"]) + rng.randi_range(0, int(c["max"]) - int(c["min"]))

func _can_act() -> bool:
	return not p_down and not p_fainted

## Advance to time t. `move` is the stick on the ground plane.
func update(t: float, move: Vector2 = Vector2.ZERO) -> void:
	var dt := clampf(t - now, 0.0, 0.1)
	now = t
	var F: Dictionary = rules["field"]
	var P: Dictionary = room["player"]
	if not p_down:
		var dw := 0.0
		if p_stance: dw -= float(F["stanceCostPerSecond"])
		if p_guard: dw -= float(P["holdDrainPerSecond"])
		if not p_stance and not p_guard: dw += float(F["regenOpen"])
		p_will = clampf(p_will + dw * dt, 0.0, float(F["willMax"]))
		if p_will == 0.0 and not p_fainted and (p_stance or p_guard):
			p_fainted = true
			p_stance = false
			p_guard = false
			_emit({ "type": "faint", "t": t })
		if p_fainted and p_will >= float(F["faintRecoverAt"]):
			p_fainted = false
		if move.length() > 0.05:
			var s := float(P["moveSpeed"]) * (float(P["stanceMoveFactor"]) if p_stance else 1.0) * (0.5 if p_guard else 1.0)
			p_pos = _clamp_in(p_pos + move.limit_length(1.0) * s * dt)
		p_facing = (w_pos - p_pos).angle()
	_move_wolf(dt)
	_separate()
	var k := floori((t - t0) / period + 1e-9)
	while last_beat < k:
		last_beat += 1
		_on_beat(last_beat)
	# A strike resolves half a window after its beat, so a late parry still counts.
	if w_pending >= 0 and t >= beat_time(w_pending) + half_window():
		_resolve_strike(w_pending)

func _move_wolf(dt: float) -> void:
	var r := float(beast["circleRadius"])
	match w_mode:
		"circle":
			w_angle += float(beast["moveSpeed"]) / r * dt
			_step_toward(p_pos + Vector2.from_angle(w_angle) * r, float(beast["moveSpeed"]) * 1.6 * dt)
		"approach":
			if dist() > float(beast["strikeReach"]) * 0.75:
				_step_toward(p_pos, float(beast["approachSpeed"]) * dt)
			else:
				w_ready = true
		"idle":
			if dist() > float(beast["strikeReach"]) * 0.8:
				_step_toward(p_pos + Vector2(1.2, -0.3), float(beast["moveSpeed"]) * dt)
	w_pos = _clamp_in(w_pos)

## Bodies do not overlap: the wolf is pushed out of the Anchor's space.
func _separate() -> void:
	var m := float(room["player"]["radius"]) + 0.55
	var d := dist()
	if d >= m:
		return
	var a := (w_pos - p_pos).angle() if d > 1e-6 else 0.0
	w_pos = _clamp_in(p_pos + Vector2.from_angle(a) * m)

func _step_toward(target: Vector2, step: float) -> void:
	var d := w_pos.distance_to(target)
	if d < 1e-6:
		return
	w_pos += (target - w_pos) / d * minf(step, d)

func _on_beat(k: int) -> void:
	var t := beat_time(k)
	_emit({ "type": "beat", "beat": k, "t": t })
	if p_stance_pending == k and not p_stance and _can_act():
		p_stance = true
		p_stance_pending = -1
		_emit({ "type": "stance", "on": true, "t": t })
	match w_mode:
		"circle":
			if k >= w_until:
				w_mode = "approach"
		"approach":
			if w_ready:
				w_ready = false
				w_mode = "windup"
				w_strike_beat = k + int(beast["telegraphBeats"])
				_emit({ "type": "windup", "strike_beat": w_strike_beat, "t": t })
		"windup":
			if k == w_strike_beat:
				w_pending = k
		"recover", "stagger":
			if k >= w_until:
				_set_circle(k)
		"down":
			if respawn and k >= w_until:
				_spawn_wolf(k)

## The tutorial asks the yard-wolf to attack now.
func provoke() -> void:
	if w_mode == "idle" or w_mode == "circle":
		w_mode = "approach"
		w_ready = false

func _resolve_strike(k: int) -> void:
	var t := beat_time(k)
	w_pending = -1
	if w_mode != "windup":
		return
	w_mode = "recover"
	w_until = k + int(beast["recoverBeats"])
	if p_down:
		return
	if dist() > float(beast["strikeReach"]):
		stats["dodges"] += 1
		_emit({ "type": "dodge", "t": t })
		return
	if p_parry_beat == k:
		p_will = minf(float(rules["field"]["willMax"]), p_will + float(rules["field"]["perfectHoldRefund"]))
		w_mode = "stagger"
		w_until = k + 1 + int(beast["recoverBeats"])
		stats["parries"] += 1
		_emit({ "type": "parry", "t": t })
		return
	var dmg := float(beast["strikeDamage"])
	var P: Dictionary = room["player"]
	if p_guard:
		dmg *= float(P["blockDamageFactor"])
		p_will = maxf(0.0, p_will - float(P["blockWillCost"]))
		stats["blocks"] += 1
		_emit({ "type": "block", "damage": dmg, "t": t })
	else:
		stats["hurts"] += 1
		_emit({ "type": "hurt", "damage": dmg, "t": t })
		if not p_stance:
			p_pos = _clamp_in(p_pos + (p_pos - w_pos).normalized() * float(beast["knockback"]))
	p_chain = 0
	breaks.slip()
	p_hp = maxf(0.0, p_hp - dmg)
	if p_hp == 0.0:
		p_down = true
		p_stance = false
		p_guard = false
		_emit({ "type": "player-down", "t": t })

## An input at time t (already corrected for latency).
## Actions: strike, ground-strike, hold-down, hold-up, stance.
func input(action: String, t: float) -> void:
	if p_down:
		return
	if action == "hold-up":
		p_guard = false
		return
	var j := CombatRules.judge(t, t0, period, window_ms)
	_emit({ "type": "judged", "action": action, "j": j, "t": t })
	stats["inputs"] += 1
	stats["offsets"].append(j["offset_ms"])
	if j["perfect"]:
		stats["perfect"] += 1

	if action == "hold-down":
		if p_fainted:
			_emit({ "type": "no-will", "t": t })
			return
		p_guard = true
		if j["perfect"] and j["beat"] != p_last_hold_beat:
			p_parry_beat = j["beat"]
		p_last_hold_beat = j["beat"]
		return
	if action == "stance":
		if p_stance:
			p_stance = false
			_emit({ "type": "stance", "on": false, "t": t })
			return
		if not _can_act():
			_emit({ "type": "no-will", "t": t })
			return
		if j["perfect"]:
			p_stance = true
			_emit({ "type": "stance", "on": true, "t": t })
		else:
			p_stance_pending = int(j["beat"]) + int(room["stance"]["offBeatEntryDelayBeats"])
		return

	# Project: one per beat. A second press in the same beat is a fumble.
	if j["beat"] <= p_last_action_beat:
		p_chain = 0
		breaks.slip()
		stats["fumbles"] += 1
		_emit({ "type": "fumble", "reason": "twice in one beat" if j["beat"] == p_last_action_beat else "still recovering", "t": t })
		return
	var a: Dictionary = room["actions"][action]
	if float(a["will"]) > 0.0:
		if p_fainted or p_will < float(a["will"]):
			_emit({ "type": "no-will", "t": t })
			return
		p_will -= float(a["will"])
	p_last_action_beat = int(j["beat"]) + int(a["recoveryBeats"])
	var staggered := w_mode == "stagger"
	var perfect: bool = j["perfect"] or staggered
	if w_mode == "down" or dist() > float(room["player"]["reach"]) + 0.6:
		if not perfect:
			p_chain = 0
		_emit({ "type": "whiff", "action": action, "perfect": perfect, "t": t })
		return
	if perfect:
		p_chain = mini(int(room["chain"]["maxLinks"]), p_chain + 1)
	else:
		p_chain = 0
		breaks.slip()
	stats["longest_chain"] = maxi(stats["longest_chain"], p_chain)
	var dmg := float(a["damage"]) * (1.0 if perfect else float(rules["combat"]["offBeatOutput"]))
	if p_stance: dmg *= float(room["stance"]["damageFactor"])
	dmg *= 1.0 + float(room["chain"]["perLink"]) * maxi(0, p_chain - 1)
	if staggered: dmg *= float(room["staggerDamageFactor"])
	dmg = roundf(dmg)
	w_hp = maxf(0.0, w_hp - dmg)
	stats["hits"] += 1
	stats["damage_dealt"] += dmg
	_emit({ "type": "hit", "action": action, "perfect": perfect, "damage": dmg, "chain": p_chain, "staggered": staggered, "t": t })
	if a.has("knockback"):
		w_pos = _clamp_in(w_pos + (w_pos - p_pos).normalized() * float(a["knockback"]))
		if perfect and w_mode == "windup":
			w_mode = "recover"
			w_until = int(j["beat"]) + int(beast["recoverBeats"])
			w_pending = -1
	# Breaks come from techniques of the Shape opposite the beast's, landed on the beat.
	if not staggered and j["perfect"] and a.has("technique"):
		var opened := breaks.hit(breaks_beast())
		if breaks_beast():
			_emit({ "type": "break", "count": breaks.needed if opened > 0 else breaks.count, "t": t })
		if opened > 0:
			w_mode = "stagger"
			w_until = int(j["beat"]) + opened + 1
			w_pending = -1
			stats["staggers"] += 1
			_emit({ "type": "stagger", "beats": opened, "t": t })
	if w_hp == 0.0:
		w_mode = "down"
		w_until = int(j["beat"]) + 4
		w_pending = -1
		stats["wolves_down"] += 1
		_emit({ "type": "wolf-down", "t": t })
