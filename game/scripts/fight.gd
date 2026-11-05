## The combat room's fight, with no drawing: real-time action. Time is seconds; positions are
## meters on the ground plane (x, z) held as Vector2; facings are Vector2 angles.
## The timing layer lives only in the parry and the Pattern's chain.
## The room (main.gd) and the tests drive it; the renderer reads its state and its events.
class_name Fight
extends RefCounted

var room: Dictionary
var rules: Dictionary
var beast: Dictionary
var arena: Vector2
var player_shape: String
var passive := false
var respawn := true
var rng := RandomNumberGenerator.new()
var now := 0.0
var events: Array = []
var stats := { "attacks": 0, "hits": 0, "damage_dealt": 0, "parries": 0, "blocks": 0, "hurts": 0, "evades": 0,
	"staggers": 0, "breaks": 0, "wolves_down": 0, "patterns": 0, "pattern_fizzles": 0, "longest_combo": 0 }

# --- The Anchor ---
var p_pos := Vector2.ZERO
var p_facing := 0.0
var p_hp: float
var p_will: float
var p_state := "free"      # free, attack, technique, dodge, flinch, pattern, down
var p_timer := 0.0         # time in the current state
var p_combo := 0           # index of the current combo swing
var p_combo_count := 0     # swings landed in a row, for stats
var p_buffer := false      # attack pressed during a swing: chain the next
var p_hit_done := false    # this swing has already resolved its hit
var p_last_attack_end := -9.0
var p_block_held := false
var p_parry_until := -9.0
var p_stance := false
var p_fainted := false
var p_dodge_dir := Vector2.ZERO
var p_dodge_ready_at := 0.0
var p_cooldowns := {}      # technique id -> time ready
var p_technique := ""
var p_lock := true         # facing the wolf (lock-on)
var p_vel := Vector2.ZERO  # movement, eased so starts and stops have a little weight
var p_queued := ""         # an action pressed while busy, fired as soon as it is allowed
var p_queued_until := 0.0
var pattern: Dictionary = {}  # the character's Pattern: name, form, terms, sworn
var pattern_lost := false     # lost to a breach (for a season, or for good if sworn)
var parried_until := -9.0     # "after a perfect Hold" holds until this time
var breach_armed_until := -9.0 # a Bar warned; pressing again before this is the breach
var chain: Dictionary = {}    # the Pattern in flight
var p_struck_this_foe := false
var p_disarmed := false       # Toll: no weapon for the rest of the run
var p_stance_locked := false  # Toll: a season without my stance
var p_double_cost := 0        # Toll: my next three techniques at double cost
var p_leaking := false        # Toll: leaking for the rest of the run
var p_scars := 0              # Toll: a scar, permanent and visible

# --- The wolf ---
var w_pos := Vector2.ZERO
var w_facing := 0.0
var w_hp: float
var w_state := "prowl"     # prowl, approach, windup, strike, recover, flinch, stagger, pinned, down, idle, absent
var w_timer := 0.0
var w_duration := 0.0
var w_attack: Dictionary = {}
var w_hit_done := false
var w_angle := 0.0
var w_hits_taken := 0
var w_break := 0
var w_dir := 1.0
var w_named := false         # the foe has been named aloud
var w_pattern_hits := 0      # times the Pattern has been used on this foe
var respawn_from_arch := false

func _init(opts: Dictionary = {}) -> void:
	room = Data.room
	rules = Data.rules
	beast = Data.beast(opts.get("beast", "cut-wolf"))
	player_shape = room["player"]["shape"]
	arena = Vector2(room["arena"]["width"], room["arena"]["depth"])
	passive = opts.get("passive", false)
	respawn = opts.get("respawn", true)
	rng.seed = opts.get("seed", 7)
	pattern = opts.get("pattern", room["pattern"]["default"]).duplicate(true)
	pattern_lost = opts.get("pattern_lost", false)
	p_hp = room["player"]["health"]
	p_will = rules["field"]["willMax"]
	p_pos = Vector2(-2.0, 1.0)
	_spawn_wolf()

func _emit(e: Dictionary) -> void:
	e["t"] = now
	events.append(e)

func drain() -> Array:
	var e := events
	events = []
	return e

func dist() -> float:
	return p_pos.distance_to(w_pos)

func breaks_beast() -> bool:
	return Data.opposite(player_shape) == beast["shape"]

## Can the Pattern fire now (every Trigger met)? Bars are checked when it is pressed.
func pattern_ready() -> bool:
	if pattern_lost or p_state == "pattern" or p_state == "down" or w_state in ["down", "absent"]:
		return false
	return PatternTerms.unmet_trigger(self, pattern["terms"]) == ""

func pattern_form() -> Dictionary:
	return room["pattern"]["forms"][pattern["form"]]

func _clamp_in(v: Vector2) -> Vector2:
	var h := arena / 2.0 - Vector2(0.8, 0.8)
	return Vector2(clampf(v.x, -h.x, h.x), clampf(v.y, -h.y, h.y))

func _angle_to(from: Vector2, to: Vector2) -> float:
	return (to - from).angle()

## Is `target` inside the arc (degrees) in front of `from` facing `facing`, within `reach`?
func _in_arc(from: Vector2, facing: float, target: Vector2, reach: float, arc_deg: float) -> bool:
	var d := target - from
	if d.length() > reach:
		return false
	return absf(angle_difference(facing, d.angle())) <= deg_to_rad(arc_deg) / 2.0

# ===================================================================== inputs

## Actions: attack, technique (ground-strike), dodge, block-down, block-up, stance, pattern, lock.
func input(action: String) -> void:
	if p_state == "down":
		return
	# Pressed a little early (mid-swing, mid-dodge, mid-flinch): remember it briefly and fire
	# it the moment it is allowed, so no press is lost.
	if action in ["attack", "technique", "dodge", "pattern", "block-down"] and _busy(action):
		p_queued = action
		p_queued_until = now + float(room.get("inputBufferSeconds", 0.25))
		if action == "block-down":
			p_block_held = true
		return
	match action:
		"attack": _press_attack()
		"technique": _press_technique("ground-strike")
		"dodge": _press_dodge()
		"block-down":
			p_block_held = true
			# A block cancels the end of a swing, as a dodge does.
			if p_state == "attack" and _can_start_action():
				p_state = "free"
				p_last_attack_end = now
			if p_state == "free" and not p_fainted:
				p_parry_until = now + float(room["parry"]["window"])
		"block-up":
			p_block_held = false
		"stance":
			if p_stance:
				p_stance = false
				_emit({ "type": "stance", "on": false })
			elif p_stance_locked:
				_emit({ "type": "stance-locked" })
			elif not p_fainted:
				p_stance = true
				_emit({ "type": "stance", "on": true })
		"pattern": _press_pattern()
		"name":
			if w_state not in ["down", "absent"]:
				w_named = true
				_emit({ "type": "named", "who": beast["name"] })
		"lock":
			p_lock = not p_lock

func _busy(action: String) -> bool:
	match p_state:
		"free":
			return action == "dodge" and now < p_dodge_ready_at
		"attack":
			# Attack presses chain into the combo; everything else waits for the recovery.
			return action != "attack" and not _can_start_action()
		"pattern":
			return action != "attack"
		"technique", "dodge", "flinch":
			return true
	return false

func _try_queued() -> void:
	if p_queued == "" or now > p_queued_until:
		p_queued = ""
		return
	var a := p_queued
	if _busy(a):
		return
	p_queued = ""
	if a == "block-down" and not p_block_held:
		return
	input(a)

func _can_start_action() -> bool:
	if p_state == "free":
		return true
	# Swings can be cancelled from their recovery.
	if p_state == "attack":
		var s: Dictionary = room["combo"][p_combo]
		return p_timer >= float(s["startup"]) + float(s["active"])
	return false

func _press_attack() -> void:
	if p_state == "pattern":
		_pattern_press()
		return
	if p_state == "attack":
		var s: Dictionary = room["combo"][p_combo]
		if p_timer < float(s["startup"]) + float(s["active"]):
			p_buffer = true
			return
		if p_combo < room["combo"].size() - 1:
			_start_swing(p_combo + 1)
		return
	if p_state != "free":
		return
	var next := 0
	if now - p_last_attack_end <= float(room["comboBufferSeconds"]) and p_combo < room["combo"].size() - 1:
		next = p_combo + 1
	_start_swing(next)

func _start_swing(i: int) -> void:
	p_state = "attack"
	p_timer = 0.0
	p_combo = i
	p_buffer = false
	p_hit_done = false
	_face_target_if_near()
	stats["attacks"] += 1
	var sw: Dictionary = room["combo"][i]
	_emit({ "type": "anim", "who": "player", "name": sw["anim"], "duration": float(sw["startup"]) + float(sw["active"]) + float(sw["recovery"]) })

## Swings go toward the wolf when locked on or when it is close; otherwise where you steer.
func _face_target_if_near() -> void:
	var wolf_there := w_state != "down" and w_state != "absent"
	if wolf_there and (p_lock or dist() < 3.0):
		p_facing = _angle_to(p_pos, w_pos)
	elif p_dodge_dir.length() > 0.3:
		p_facing = p_dodge_dir.angle()

func _press_technique(id: String) -> void:
	var t: Dictionary = room["techniques"][id]
	if not _can_start_action():
		return
	if now < float(p_cooldowns.get(id, 0.0)):
		_emit({ "type": "not-ready", "what": t["name"] })
		return
	var cost := float(t["will"]) * (2.0 if p_double_cost > 0 else 1.0)
	if p_fainted or p_will < cost:
		_emit({ "type": "no-will" })
		return
	p_will -= cost
	p_double_cost = maxi(0, p_double_cost - 1)
	p_cooldowns[id] = now + float(t["cooldown"])
	p_state = "technique"
	p_technique = id
	p_timer = 0.0
	p_hit_done = false
	_face_target_if_near()
	_emit({ "type": "anim", "who": "player", "name": t["anim"], "duration": float(t["startup"]) + float(t["active"]) + float(t["recovery"]) })
	_emit({ "type": "technique", "id": id })

func _press_dodge() -> void:
	var d: Dictionary = room["dodge"]
	if now < p_dodge_ready_at or not (p_state == "free" or _can_start_action()):
		return
	if p_fainted or p_will < float(d["will"]):
		_emit({ "type": "no-will" })
		return
	p_will -= float(d["will"])
	p_state = "dodge"
	p_timer = 0.0
	if p_dodge_dir.length() < 0.1:
		p_dodge_dir = -Vector2.from_angle(p_facing)
	p_dodge_dir = p_dodge_dir.normalized()
	var rel := angle_difference(p_facing, p_dodge_dir.angle())
	var anim := "Dodge_Forward"
	if absf(rel) > PI * 0.75: anim = "Dodge_Backward"
	elif rel > PI * 0.25: anim = "Dodge_Right"
	elif rel < -PI * 0.25: anim = "Dodge_Left"
	_emit({ "type": "anim", "who": "player", "name": anim, "duration": float(d["duration"]) })
	_emit({ "type": "dodge", "dir": p_dodge_dir })

func _press_pattern() -> void:
	var P: Dictionary = room["pattern"]
	if pattern_lost:
		_emit({ "type": "pattern-lost" })
		return
	var unmet := PatternTerms.unmet_trigger(self, pattern["terms"])
	if unmet != "":
		_emit({ "type": "pattern-locked", "trigger": unmet })
		return
	if w_state in ["down", "absent"]:
		return
	if not _can_start_action() and p_state != "flinch":
		return
	# A Bar that covers this moment: the Pattern refuses, with a warning. Pressing again
	# while the warning stands fires it anyway, and that is the breach.
	var bars := PatternTerms.covering_bars(self, pattern["terms"])
	var breach := false
	if bars.size() > 0:
		if now > breach_armed_until:
			breach_armed_until = now + float(P["breachConfirmSeconds"])
			_emit({ "type": "bar-warning", "bars": bars, "sworn": pattern["sworn"] })
			return
		breach = true
	breach_armed_until = -9.0
	var terms: Array = pattern["terms"]
	var n: int = int(rules["pattern"]["chainBaseBeats"]) + int(rules["pattern"]["beatsPerTerm"]) * terms.size()
	var period := float(Data.shape(player_shape)["pulseMs"]) / 1000.0
	var cues: Array = []
	for k in n:
		cues.append(now + float(P["leadIn"]) + k * period)
	# The Tolls are taken when the Pattern fires, whether it lands or not.
	var tolls := PatternTerms.take_tolls(self, terms)
	chain = { "cues": cues, "next": 0, "hit": 0, "period": period, "window": float(P["cueWindowMs"]) / 1000.0,
		"multiplier": pattern_multiplier(), "effect": pattern_form()["effect"] }
	p_state = "pattern"
	p_timer = 0.0
	parried_until = -9.0
	w_pattern_hits += 1
	_face_target_if_near()
	if w_state != "down" and w_state != "absent" and chain["effect"] != "guard":
		w_state = "pinned"
		w_timer = 0.0
		w_duration = float(cues[-1] - now) + 0.6
	stats["patterns"] += 1
	_emit({ "type": "pattern-start", "cues": cues, "name": pattern["name"], "multiplier": chain["multiplier"], "effect": chain["effect"], "tolls": tolls })
	_emit({ "type": "anim", "who": "player", "name": "Block_Attack", "speed": 1.0 })
	if breach:
		pattern_lost = true
		_emit({ "type": "breach", "bars": bars, "sworn": pattern["sworn"] })

## The Terms' multiplier, doubled if sworn, capped at the ceiling.
func pattern_multiplier() -> float:
	return multiplier_of(pattern)

static func multiplier_of(spec: Dictionary) -> float:
	var m := 1.0
	for id in spec["terms"]:
		m *= float(Data.by_id(Data.terms, id)["multiplier"])
	if spec.get("sworn", false):
		m *= float(Data.rules["pattern"]["swornMultiplier"])
	return minf(m, float(Data.rules["pattern"]["multiplierCeiling"]))

static func chain_length(spec: Dictionary) -> int:
	return int(Data.rules["pattern"]["chainBaseBeats"]) + int(Data.rules["pattern"]["beatsPerTerm"]) * spec["terms"].size()

func _pattern_press() -> void:
	var cues: Array = chain["cues"]
	var i: int = chain["next"]
	if i >= cues.size():
		return
	var off := now - float(cues[i])
	if absf(off) <= chain["window"] / 2.0:
		chain["next"] = i + 1
		chain["hit"] = int(chain["hit"]) + 1
		var form := pattern_form()
		match chain["effect"]:
			"strikes":
				_damage_wolf(roundf(float(form["base"]) * (1.5 if p_stance else 1.0)), true, false)
			"guard":
				_emit({ "type": "ward-pulse" })
			"mend":
				p_hp = minf(float(room["player"]["health"]), p_hp + float(form["base"]))
				_emit({ "type": "mend", "amount": float(form["base"]) })
		_emit({ "type": "pattern-cue", "k": i, "hit": true, "offset_ms": off * 1000.0 })
		_emit({ "type": "anim", "who": "player", "name": room["combo"][i % room["combo"].size()]["anim"], "speed": 1.6 })
		if chain["next"] >= cues.size():
			_finish_pattern(true)
	else:
		_emit({ "type": "pattern-cue", "k": i, "hit": false, "offset_ms": off * 1000.0 })
		_finish_pattern(false)

## Every cue landed: the Form pays at Stage 4 times the Terms' multiplier.
func _finish_pattern(landed: bool) -> void:
	var form := pattern_form()
	if landed:
		var stage := float(rules["field"]["stageOutput"][3])
		var pay := float(form["base"]) * stage * float(chain["multiplier"])
		match chain["effect"]:
			"strikes":
				_damage_wolf(roundf(pay), true, false)
				_emit({ "type": "pattern-done", "damage": roundf(pay), "effect": "strikes" })
			"guard":
				_damage_wolf(roundf(pay), true, true)
				if w_state not in ["down", "absent"]:
					_wolf_set("stagger", float(form.get("staggerSeconds", 2.0)))
					_emit({ "type": "stagger", "seconds": float(form.get("staggerSeconds", 2.0)), "cause": "pattern" })
				_emit({ "type": "pattern-done", "damage": roundf(pay), "effect": "guard" })
			"mend":
				var heal := roundf(pay * float(form.get("healFactor", 1.0)))
				p_hp = minf(float(room["player"]["health"]), p_hp + heal)
				_emit({ "type": "pattern-done", "heal": heal, "effect": "mend" })
	else:
		stats["pattern_fizzles"] += 1
		_emit({ "type": "pattern-fizzle" })
	chain = {}
	p_state = "free"
	if w_state == "pinned":
		_wolf_set("recover", 0.9)

# ===================================================================== update

## Advance by dt. `move` is the stick on the ground plane, already camera-relative.
func update(dt: float, move: Vector2 = Vector2.ZERO) -> void:
	now += dt
	p_timer += dt
	_update_will(dt)
	_update_player(dt, move)
	if p_state != "free":
		p_vel = Vector2.ZERO
	_try_queued()
	_update_wolf(dt)
	_separate()

func _update_will(dt: float) -> void:
	if p_state == "down":
		return
	var F: Dictionary = rules["field"]
	var blocking := _blocking()
	var dw := 0.0
	if p_stance: dw -= float(room["stance"]["willPerSecond"])
	if blocking: dw -= float(room["block"]["willPerSecond"])
	if not p_stance and not blocking and p_state != "pattern": dw += float(F["regenOpen"]) * (0.5 if p_leaking else 1.0)
	p_will = clampf(p_will + dw * dt, 0.0, float(F["willMax"]))
	if p_will == 0.0 and not p_fainted and (p_stance or blocking):
		p_fainted = true
		p_stance = false
		_emit({ "type": "faint" })
	if p_fainted and p_will >= float(F["faintRecoverAt"]):
		p_fainted = false

func _blocking() -> bool:
	return p_block_held and p_state == "free" and not p_fainted

func _update_player(dt: float, move: Vector2) -> void:
	var P: Dictionary = room["player"]
	p_dodge_dir = move
	match p_state:
		"free":
			var speed := float(P["runSpeed"])
			if _blocking(): speed = float(P["blockMoveSpeed"])
			if p_stance: speed *= float(P["stanceMoveFactor"])
			var target_vel := move.limit_length(1.0) * speed
			var accel := float(P.get("acceleration", 20.0))
			p_vel = p_vel.move_toward(target_vel, accel * speed * dt)
			p_pos = _clamp_in(p_pos + p_vel * dt)
			var want := p_facing
			if p_lock and w_state != "down" and w_state != "absent":
				want = _angle_to(p_pos, w_pos)
			elif move.length() > 0.05:
				want = move.angle()
			p_facing = lerp_angle(p_facing, want, 1.0 - exp(-float(P["turnSpeed"]) * dt))
		"attack":
			var s: Dictionary = room["combo"][p_combo]
			var st := float(s["startup"])
			var ac := float(s["active"])
			if p_timer < st + ac and dist() > float(P["radius"]) + float(beast["radius"]) + 0.3:
				p_pos = _clamp_in(p_pos + Vector2.from_angle(p_facing) * float(s["lunge"]) / (st + ac) * dt)
			if not p_hit_done and p_timer >= st:
				p_hit_done = true
				_resolve_swing(float(s["damage"]), float(s["reach"]), float(s["arc"]), false, 0.0)
			if p_buffer and p_timer >= st + ac and p_combo < room["combo"].size() - 1:
				_start_swing(p_combo + 1)
			elif p_timer >= st + ac + float(s["recovery"]):
				p_state = "free"
				p_last_attack_end = now
		"technique":
			var t: Dictionary = room["techniques"][p_technique]
			if not p_hit_done and p_timer >= float(t["startup"]):
				p_hit_done = true
				_resolve_swing(float(t["damage"]), float(t["reach"]), float(t["arc"]), t.get("breaks", false), float(t.get("knockback", 0.0)))
				_emit({ "type": "quake", "at": p_pos + Vector2.from_angle(p_facing) * 1.2 })
			if p_timer >= float(t["startup"]) + float(t["active"]) + float(t["recovery"]):
				p_state = "free"
		"dodge":
			var d: Dictionary = room["dodge"]
			var dur := float(d["duration"])
			var k := clampf(1.0 - p_timer / dur, 0.0, 1.0)
			p_pos = _clamp_in(p_pos + p_dodge_dir * float(d["distance"]) / dur * 1.6 * k * dt)
			if p_timer >= dur:
				p_state = "free"
				p_dodge_ready_at = now + float(d["cooldown"])
		"flinch":
			if p_timer >= float(P["flinchTime"]):
				p_state = "free"
		"pattern":
			if not chain.is_empty():
				var cues: Array = chain["cues"]
				var i: int = chain["next"]
				if i < cues.size() and now > float(cues[i]) + float(chain["window"]) / 2.0:
					_emit({ "type": "pattern-cue", "k": i, "hit": false, "offset_ms": 999.0 })
					_finish_pattern(false)

func p_invulnerable() -> bool:
	if p_state != "dodge":
		return false
	var d: Dictionary = room["dodge"]
	return p_timer >= float(d["iframeStart"]) and p_timer <= float(d["iframeEnd"])

func _resolve_swing(damage: float, reach: float, arc: float, breaks: bool, knockback: float) -> void:
	if w_state in ["down", "absent"] or not _in_arc(p_pos, p_facing, w_pos, reach + float(beast["radius"]), arc):
		_emit({ "type": "whiff" })
		return
	var heavy := breaks or knockback > 0.0
	if p_stance: damage *= float(room["stance"]["damageFactor"])
	if p_disarmed and not breaks: damage *= 0.4
	_damage_wolf(roundf(damage), false, heavy)
	if knockback > 0.0 and w_state not in ["down", "pinned"]:
		w_pos = _clamp_in(w_pos + (w_pos - p_pos).normalized() * knockback)
	if breaks and breaks_beast() and w_state != "stagger" and w_state != "down":
		w_break += 1
		stats["breaks"] += 1
		_emit({ "type": "break", "count": w_break, "needed": int(room["break"]["needed"]) })
		if w_break >= int(room["break"]["needed"]):
			w_break = 0
			stats["staggers"] += 1
			_wolf_set("stagger", float(room["break"]["staggerSeconds"]))
			_emit({ "type": "stagger", "seconds": float(room["break"]["staggerSeconds"]), "cause": "break" })

func _damage_wolf(dmg: float, from_pattern: bool, heavy: bool) -> void:
	if w_state in ["down", "absent"]:
		return
	if w_state == "stagger":
		dmg = roundf(dmg * float(room["break"]["staggerDamageFactor"]))
	w_hp = maxf(0.0, w_hp - dmg)
	stats["hits"] += 1
	stats["damage_dealt"] += dmg
	p_combo_count += 1
	stats["longest_combo"] = maxi(stats["longest_combo"], p_combo_count)
	_emit({ "type": "hit", "damage": dmg, "pattern": from_pattern, "heavy": heavy, "staggered": w_state == "stagger", "combo": p_combo })
	if w_hp == 0.0:
		stats["wolves_down"] += 1
		_wolf_set("down", float(beast["respawnSeconds"]))
		_emit({ "type": "wolf-down" })
		_emit({ "type": "anim", "who": "wolf", "name": "Death", "speed": 1.0 })
		return
	w_hits_taken += 1
	if w_state not in ["prowl", "approach", "recover", "idle"]:
		return
	# Heavy hits make it flinch. Light hits it shrugs off, and after a few it snaps back.
	var every := int(beast.get("flinchEvery", 0))
	if heavy or (every > 0 and w_hits_taken % every == 0):
		_wolf_set("flinch", float(beast["flinchTime"]))
		_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 1.0 })
		return
	var counter := int(beast.get("counterAfterHits", 0))
	if counter > 0 and w_hits_taken % counter == 0 and not passive:
		for a in beast["attacks"]:
			if a["id"] == "snap":
				w_attack = a
				w_facing = _angle_to(w_pos, p_pos)
				_wolf_set("windup", float(a["windup"]))
				_emit({ "type": "windup", "attack": a["id"], "name": a["name"], "seconds": w_duration })

# ===================================================================== the wolf

func _spawn_wolf() -> void:
	w_hp = beast["health"]
	w_angle = rng.randf() * TAU
	if respawn_from_arch:
		# A new wolf comes in from the far end of the chamber, where the line enters.
		var side := -1.0 if p_pos.x > 0.0 else 1.0
		w_pos = _clamp_in(Vector2(side * arena.x / 2.0, rng.randf_range(-1.0, 1.0)))
	else:
		w_pos = _clamp_in(p_pos + Vector2.from_angle(w_angle) * float(beast["circleRadius"]) * 1.5)
	w_facing = _angle_to(w_pos, p_pos)
	w_break = 0
	w_hits_taken = 0
	w_named = false
	w_pattern_hits = 0
	p_struck_this_foe = false
	_wolf_prowl()

func _wolf_set(state: String, duration: float) -> void:
	w_state = state
	w_timer = 0.0
	w_duration = duration

func _wolf_prowl() -> void:
	var pr: Dictionary = beast["prowl"]
	_wolf_set("idle" if passive else "prowl", rng.randf_range(float(pr["min"]), float(pr["max"])))
	w_dir = -1.0 if rng.randf() < 0.5 else 1.0

## The tutorial asks the yard-wolf to attack now.
func provoke() -> void:
	if w_state in ["idle", "prowl"]:
		_choose_attack()

func _choose_attack() -> void:
	var options: Array = []
	var total := 0.0
	for a in beast["attacks"]:
		if dist() < float(a.get("minRange", 0.0)) or float(a["weight"]) <= 0.0:
			continue
		options.append(a)
		total += float(a["weight"])
	var r := rng.randf() * total
	w_attack = options[0]
	for a in options:
		r -= float(a["weight"])
		if r <= 0.0:
			w_attack = a
			break
	_wolf_set("approach", 6.0)

func _update_wolf(dt: float) -> void:
	w_timer += dt
	var b := beast
	match w_state:
		"absent":
			return
		"idle":
			if dist() > 2.6:
				_wolf_step_toward(p_pos, float(b["walkSpeed"]) * dt)
			w_facing = lerp_angle(w_facing, _angle_to(w_pos, p_pos), 1.0 - exp(-8.0 * dt))
		"prowl":
			# Circle the Anchor at a distance, then commit.
			w_angle += w_dir * float(b["walkSpeed"]) / float(b["circleRadius"]) * dt
			var target := p_pos + Vector2.from_angle(w_angle) * float(b["circleRadius"])
			var before := w_pos
			_wolf_step_toward(target, float(b["walkSpeed"]) * 1.5 * dt)
			if (w_pos - before).length() > 0.001:
				w_facing = lerp_angle(w_facing, (w_pos - before).angle(), 1.0 - exp(-6.0 * dt))
			if w_timer >= w_duration:
				_choose_attack()
		"approach":
			var rng_a := float(w_attack["range"])
			if dist() > rng_a * 0.85:
				_wolf_step_toward(p_pos, float(b["gallopSpeed"]) * dt)
				w_facing = _angle_to(w_pos, p_pos)
			else:
				_wolf_set("windup", float(w_attack["windup"]))
				w_facing = _angle_to(w_pos, p_pos)
				_emit({ "type": "windup", "attack": w_attack["id"], "name": w_attack["name"], "seconds": w_duration })
			if w_timer > 6.0:
				_wolf_prowl()
		"windup":
			# Track the Anchor until the last fifth of the wind-up, then commit to the line.
			if w_timer < w_duration * 0.8:
				w_facing = lerp_angle(w_facing, _angle_to(w_pos, p_pos), 1.0 - exp(-10.0 * dt))
			if w_timer >= w_duration:
				_wolf_set("strike", float(w_attack["active"]))
				w_hit_done = false
				_emit({ "type": "anim", "who": "wolf", "name": "Attack", "speed": 1.4 })
		"strike":
			var lunge := float(w_attack["lunge"]) / float(w_attack["active"]) * dt
			if dist() > float(room["player"]["radius"]) + float(b["radius"]):
				w_pos = _clamp_in(w_pos + Vector2.from_angle(w_facing) * lunge)
			if not w_hit_done:
				var mouth := w_pos + Vector2.from_angle(w_facing) * (float(b["radius"]) + 0.4)
				if mouth.distance_to(p_pos) <= float(room["player"]["radius"]) + 1.0:
					w_hit_done = true
					_resolve_bite()
			if w_timer >= w_duration:
				if not w_hit_done:
					_emit({ "type": "evade", "how": "out of reach" })
					stats["evades"] += 1
				_wolf_set("recover", float(w_attack["recover"]))
		"recover", "flinch":
			if w_timer >= w_duration:
				_wolf_prowl()
		"stagger":
			if w_timer >= w_duration:
				_wolf_set("recover", 0.4)
		"pinned":
			if w_timer >= w_duration:
				_wolf_set("recover", 0.6)
		"down":
			if respawn and w_timer >= w_duration:
				respawn_from_arch = true
				_spawn_wolf()
				_emit({ "type": "wolf-up" })

func _wolf_step_toward(target: Vector2, step: float) -> void:
	var d := w_pos.distance_to(target)
	if d < 1e-6:
		return
	w_pos = _clamp_in(w_pos + (target - w_pos) / d * minf(step, d))

## The bite lands: dodged, parried, blocked, or taken.
func _resolve_bite() -> void:
	var a := w_attack
	if p_state == "down":
		return
	if p_invulnerable():
		stats["evades"] += 1
		_emit({ "type": "evade", "how": "dodged" })
		return
	if p_state == "pattern" and not chain.is_empty() and chain["effect"] == "guard":
		_emit({ "type": "turned" })
		_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 1.0 })
		return
	var facing_wolf := absf(angle_difference(p_facing, _angle_to(p_pos, w_pos))) <= deg_to_rad(float(room["block"]["arc"])) / 2.0
	if now <= p_parry_until and facing_wolf:
		var pr: Dictionary = room["parry"]
		p_will = minf(float(rules["field"]["willMax"]), p_will + float(pr["will"]))
		p_parry_until = -9.0
		stats["parries"] += 1
		_wolf_set("stagger", float(pr["staggerSeconds"]))
		parried_until = now + float(room["pattern"]["afterParrySeconds"])
		_emit({ "type": "parry" })
		_emit({ "type": "anim", "who": "player", "name": "Block_Hit", "speed": 1.3 })
		_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 0.8 })
		return
	var dmg := float(a["damage"])
	if _blocking() and facing_wolf:
		dmg *= float(room["block"]["damageFactor"])
		p_will = maxf(0.0, p_will - float(room["block"]["willPerBlockedHit"]))
		stats["blocks"] += 1
		_emit({ "type": "block", "damage": dmg })
		_emit({ "type": "anim", "who": "player", "name": "Block_Hit", "speed": 1.2 })
	else:
		stats["hurts"] += 1
		p_struck_this_foe = true
		_emit({ "type": "hurt", "damage": dmg })
		p_combo_count = 0
		if not p_stance:
			p_pos = _clamp_in(p_pos + (p_pos - w_pos).normalized() * float(a["knockback"]))
			if p_state != "pattern":
				p_state = "flinch"
				p_timer = 0.0
				_emit({ "type": "anim", "who": "player", "name": "Hit_A", "speed": 1.2 })
	p_hp = maxf(0.0, p_hp - dmg)
	if p_hp == 0.0:
		p_state = "down"
		p_stance = false
		chain = {}
		_emit({ "type": "player-down" })
		_emit({ "type": "anim", "who": "player", "name": "Death_A", "speed": 1.0 })

## Bodies do not overlap.
func _separate() -> void:
	if w_state in ["absent", "down"]:
		return
	# A little personal space, so the wolf reads clearly beside the Anchor.
	var m := float(room["player"]["radius"]) + float(beast["radius"]) + 0.3
	var d := dist()
	if d >= m:
		return
	var a := _angle_to(p_pos, w_pos) if d > 1e-6 else 0.0
	w_pos = _clamp_in(p_pos + Vector2.from_angle(a) * m)
