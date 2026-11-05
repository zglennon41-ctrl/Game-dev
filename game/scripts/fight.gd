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
var pattern_until := -9.0  # the Pattern's Trigger is met until this time
var chain: Dictionary = {} # the Pattern in flight

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

func _init(opts: Dictionary = {}) -> void:
	room = Data.room
	rules = Data.rules
	beast = Data.beast(opts.get("beast", "cut-wolf"))
	player_shape = room["player"]["shape"]
	arena = Vector2(room["arena"]["width"], room["arena"]["depth"])
	passive = opts.get("passive", false)
	respawn = opts.get("respawn", true)
	rng.seed = opts.get("seed", 7)
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

func pattern_ready() -> bool:
	return now <= pattern_until and p_state != "pattern" and p_state != "down"

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
			elif not p_fainted:
				p_stance = true
				_emit({ "type": "stance", "on": true })
		"pattern": _press_pattern()
		"lock":
			p_lock = not p_lock

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
	_emit({ "type": "anim", "who": "player", "name": room["combo"][i]["anim"], "speed": 1.0 })

func _face_target_if_near() -> void:
	if w_state != "down" and w_state != "absent" and dist() < 6.0:
		p_facing = _angle_to(p_pos, w_pos)

func _press_technique(id: String) -> void:
	var t: Dictionary = room["techniques"][id]
	if not _can_start_action():
		return
	if now < float(p_cooldowns.get(id, 0.0)):
		_emit({ "type": "not-ready", "what": t["name"] })
		return
	if p_fainted or p_will < float(t["will"]):
		_emit({ "type": "no-will" })
		return
	p_will -= float(t["will"])
	p_cooldowns[id] = now + float(t["cooldown"])
	p_state = "technique"
	p_technique = id
	p_timer = 0.0
	p_hit_done = false
	_face_target_if_near()
	_emit({ "type": "anim", "who": "player", "name": t["anim"], "speed": 1.0 })
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
	_emit({ "type": "anim", "who": "player", "name": anim, "speed": 1.0 })
	_emit({ "type": "dodge" })

func _press_pattern() -> void:
	var P: Dictionary = room["pattern"]
	if not pattern_ready():
		_emit({ "type": "pattern-locked" })
		return
	if not _can_start_action() and p_state != "flinch":
		return
	var terms: Array = P["terms"]
	var n: int = int(rules["pattern"]["chainBaseBeats"]) + int(rules["pattern"]["beatsPerTerm"]) * terms.size()
	var period := float(Data.shape(player_shape)["pulseMs"]) / 1000.0
	var cues: Array = []
	for k in n:
		cues.append(now + float(P["leadIn"]) + k * period)
	# The Toll is taken when the Pattern is fired, whether it lands or not.
	var toll_will := "all-will" in terms
	if toll_will:
		p_will = 0.0
	chain = { "cues": cues, "next": 0, "hit": 0, "period": period, "window": float(P["cueWindowMs"]) / 1000.0, "multiplier": _pattern_multiplier() }
	p_state = "pattern"
	p_timer = 0.0
	pattern_until = -9.0
	_face_target_if_near()
	if w_state != "down" and w_state != "absent":
		w_state = "pinned"
		w_timer = 0.0
		w_duration = float(cues[-1] - now) + 0.6
	stats["patterns"] += 1
	_emit({ "type": "pattern-start", "cues": cues, "name": P["name"], "multiplier": chain["multiplier"] })
	_emit({ "type": "anim", "who": "player", "name": "Block_Attack", "speed": 1.0 })

func _pattern_multiplier() -> float:
	var P: Dictionary = room["pattern"]
	var m := 1.0
	for id in P["terms"]:
		m *= float(Data.by_id(Data.terms, id)["multiplier"])
	if P["sworn"]:
		m *= float(rules["pattern"]["swornMultiplier"])
	return minf(m, float(rules["pattern"]["multiplierCeiling"]))

func _pattern_press() -> void:
	var cues: Array = chain["cues"]
	var i: int = chain["next"]
	if i >= cues.size():
		return
	var off := now - float(cues[i])
	if absf(off) <= chain["window"] / 2.0:
		chain["next"] = i + 1
		chain["hit"] = int(chain["hit"]) + 1
		var dmg := roundf(float(room["pattern"]["baseDamage"]) * (1.5 if p_stance else 1.0))
		_damage_wolf(dmg, true, false)
		_emit({ "type": "pattern-cue", "k": i, "hit": true, "offset_ms": off * 1000.0 })
		_emit({ "type": "anim", "who": "player", "name": room["combo"][i % room["combo"].size()]["anim"], "speed": 1.6 })
		if chain["next"] >= cues.size():
			_finish_pattern(true)
	else:
		_emit({ "type": "pattern-cue", "k": i, "hit": false, "offset_ms": off * 1000.0 })
		_finish_pattern(false)

func _finish_pattern(landed: bool) -> void:
	if landed:
		var stage := float(rules["field"]["stageOutput"][3])
		var dmg := roundf(float(room["pattern"]["baseDamage"]) * stage * float(chain["multiplier"]))
		_damage_wolf(dmg, true, false)
		_emit({ "type": "pattern-done", "damage": dmg })
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
	if not p_stance and not blocking and p_state != "pattern": dw += float(F["regenOpen"])
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
			if move.length() > 0.05:
				p_pos = _clamp_in(p_pos + move.limit_length(1.0) * speed * dt)
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
	w_pos = _clamp_in(p_pos + Vector2.from_angle(w_angle) * float(beast["circleRadius"]) * 1.5)
	w_facing = _angle_to(w_pos, p_pos)
	w_break = 0
	w_hits_taken = 0
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
	var facing_wolf := absf(angle_difference(p_facing, _angle_to(p_pos, w_pos))) <= deg_to_rad(float(room["block"]["arc"])) / 2.0
	if now <= p_parry_until and facing_wolf:
		var pr: Dictionary = room["parry"]
		p_will = minf(float(rules["field"]["willMax"]), p_will + float(pr["will"]))
		p_parry_until = -9.0
		stats["parries"] += 1
		_wolf_set("stagger", float(pr["staggerSeconds"]))
		pattern_until = now + float(room["pattern"]["availableSeconds"])
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
