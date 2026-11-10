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
	"staggers": 0, "breaks": 0, "wolves_down": 0, "patterns": 0, "pattern_fizzles": 0, "longest_combo": 0,
	"g_damage": 0.0, "g_guards": 0, "g_will_spent": 0.0, "g_moves": 0, "g_great": 0, "g_falls": 0 }

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
var w_shape := ""            # the beast's Shape: the room makes it the one the hero counters

# --- The hero: who the character creator made ---
var hero: Dictionary = {}
var kit: Dictionary = {}     # data/shape-kits.json for the hero's Shape
var weapon: Dictionary = {}
var style: Dictionary = {}   # how the weapon fights: a melee combo, or shots
var combo: Array = []
var ranged := false
var p_ammo := 0              # rounds in the magazine (ranged); 0 with no magazine means a quiver that never empties
var p_ammo_max := 0
var p_draw := 0.0            # seconds the bow has been drawn
var p_charge := 1.0          # the last loosed shot's draw, 0..1
var p_reload_t := 0.0
var gear: Dictionary = {}        # the weapon's tier and name
var gear_damage := 1.0
var gear_trait: Dictionary = {}
var tech: Dictionary = {}    # the Shape's technique
var bc: Dictionary = {}      # the blood's combat passives
var w_burn_until := -9.0
var w_burn_tick := 0.0
var w_slow_until := -9.0
var w_slow := 1.0
var crit_until := -9.0
var ward_until := -9.0
var second_heart_used := false
var w_shouted := false
var stage := 2               # the field's Stage: 2 after the rite, 3 once the field is Projected
var p_field_open := false    # the field past the skin (Stage 3, or opened in the Project drill)
var project_training := false
var p_project_t := 0.0
var foes: Array = []         # the rest of the pack (Foe), beside the locked foe in w_*
var allies: Array = []       # the party: classmates fighting beside the hero (see _update_allies)
var w_target := -1           # whom the foe is after: -1 the hero, else an ally's index
var extra_techs: Array = []  # the Discipline's techniques (keys 1, 2, 3), once learned
var p_tech_active: Dictionary = {}
var w_pattern_used := false   # a classmate's Pattern, fired once a bout
var w_mark_until := -9.0
var w_mark_factor := 1.0
var genius: Genius = null   # the hero's genius, if the rite has given it a body
var g_will := 0.0
var g_will_max := 0.0
var g_guard_ready_at := 0.0
var g_hunt_at := 0.0
var g_regen_from := 0.0
var g_up_at := -1.0
var obstacles: Array = []    # Vector3(x, z, radius): pillars and people the hero walks round
var allowed: Array = []      # a lesson may allow only some actions (empty: all)
var mercy := false           # the prologue: the hero cannot fall
var allow_breach := true     # the prologue: a Bar warns, but cannot be broken
var w_floor := 0.0           # the prologue: the beast cannot fall below this until the story is ready

func _init(opts: Dictionary = {}) -> void:
	room = Data.room
	rules = Data.rules
	beast = Data.beast(opts.get("beast", "cut-wolf"))
	if opts.has("foe"):
		beast = student_beast(opts["foe"], float(opts.get("foe_scale", 1.0)))
	hero = opts.get("hero", default_hero())
	player_shape = hero["shape"]
	kit = Data.kits[player_shape]
	weapon = Data.by_id(Data.weapons, hero["weapon"])
	style = room["styles"][weapon["style"]]
	ranged = style["kind"] == "ranged"
	combo = style.get("combo", [style.get("shot", {})])
	p_ammo_max = int(style.get("ammo", 0))
	p_ammo = p_ammo_max
	# The weapon's tier and trait (data/gear.json): a fine or a named weapon hits harder; a
	# trait changes the moveset a little.
	gear = hero.get("gear", { "tier": "plain" })
	var tier: Dictionary = Data.gear["tiers"].get(String(gear.get("tier", "plain")), Data.gear["tiers"]["plain"])
	gear_damage = float(tier.get("damage", 1.0))
	gear_trait = Data.gear["traits"].get(String(gear.get("trait", "")), {})
	if not gear_trait.is_empty():
		combo = combo.map(func(c): return c.duplicate())
		for c in combo:
			if gear_trait.has("reach") and c.has("reach"): c["reach"] = float(c["reach"]) + float(gear_trait["reach"])
			if gear_trait.has("range") and c.has("range"): c["range"] = float(c["range"]) + float(gear_trait["range"])
			if gear_trait.has("recovery"): c["recovery"] = float(c["recovery"]) * float(gear_trait["recovery"])
			if gear_trait.has("knockback"): c["knockback"] = float(c.get("knockback", 0.0)) + float(gear_trait["knockback"])
			if gear_trait.has("burnSeconds"): c["burnSeconds"] = maxf(float(c.get("burnSeconds", 0.0)), float(gear_trait["burnSeconds"]))
	tech = kit["technique"]
	for tid in hero.get("techniques", []):
		var dk: Dictionary = Data.discipline_kits.get(hero.get("discipline", ""), {})
		for t in dk.get("techniques", []):
			if t["id"] == tid:
				extra_techs.append(t)
	if hero.get("blood", "") != "":
		bc = Data.by_id(Data.bloods, hero["blood"]).get("combat", {})
	w_shape = opts.get("beast_shape", beast["shape"] if opts.has("foe") else Data.opposite(player_shape))
	mercy = opts.get("mercy", false)
	allow_breach = opts.get("allow_breach", true)
	if opts.has("beast_health"):
		beast = beast.duplicate(true)
		beast["health"] = opts["beast_health"]
	arena = opts.get("arena", Vector2(room["arena"]["width"], room["arena"]["depth"]))
	passive = opts.get("passive", false)
	respawn = opts.get("respawn", true)
	rng.seed = opts.get("seed", 7)
	pattern = opts.get("pattern", hero.get("pattern", room["pattern"]["default"])).duplicate(true)
	pattern_lost = opts.get("pattern_lost", false)
	p_hp = room["player"]["health"]
	p_will = rules["field"]["willMax"]
	p_pos = Vector2(-2.0, 1.0)
	stage = int(hero.get("stage", 2))
	p_field_open = stage >= 3 or hero.get("projected", false)
	for c in opts.get("allies", []):
		allies.append(make_ally(c, p_pos + Vector2(-1.5, 1.5 * (1 if allies.is_empty() else -1))))
	var gn: Variant = opts.get("genius", null)
	if gn is Genius and (gn as Genius).is_born():
		genius = gn
		for al in allies:
			genius.fought_beside(al["shape"])
		g_will_max = genius.will_max()
		g_will = 0.0 if genius.fallen else g_will_max
		if genius.fallen:
			g_up_at = float(Data.genius()["fall"]["roomRecoverSeconds"])
		if opts.get("post", null) is Vector2:
			g_post = opts["post"]
		_genius_setup()
	_spawn_wolf()
	for bid in opts.get("pack", []):
		spawn_foe(bid, w_pos + Vector2.from_angle(rng.randf() * TAU) * 2.5, float(opts.get("pack_scale", 1.0)))

func _emit(e: Dictionary) -> void:
	e["t"] = now
	events.append(e)

func drain() -> Array:
	var e := events
	events = []
	if genius:
		_record(e)
	return e

# ===================================================================== the genius
# It fights as what it is (data/genius.json, fight; docs/genius-combat.md). Its moves come from
# the kind of body it has and the features it carries; what it can do yet, from its age; where
# it stands and what it attends to, from its order; and on Free, what it chooses, from how its
# partner has played.

var g_pos := Vector2.ZERO        # where it is
var g_order := "guard"           # the order it is carrying out (Free chooses one of the others)
var g_free_why := ""             # why Free chose it, in a few words
var g_kind := "quadruped"        # its body's kind: quadruped, flier, humanoid, construct, object, aspect
var g_age: Dictionary = {}       # what its age lets it do (fight.ages)
var g_moves: Array = []          # the moves it has yet: [{ id, name, when, ... }]
var g_great: Dictionary = {}     # the move only the great have, if it is great
var g_wait: Dictionary = {}      # move id -> when it can again
var g_move_now := ""             # the move it last made, by name (the HUD shows it a moment)
var g_move_until := -9.0
var g_hold_at := Vector2.INF     # the ground it holds
var g_post := Vector2.INF        # the fight's post, where it has one
var g_nips := 0
var g_with := 0
var g_climb_until := -9.0
var g_lit_until := -9.0
var g_lit := 1.0
var g_debt_until := -9.0
var g_debt: Dictionary = {}
var g_called_until := -9.0
var g_called: Dictionary = {}
var g_zone: Dictionary = {}      # { at, until, radius, effect, power, tick }
var g_ward_blows := 0
var g_double_until := -9.0
var g_double := 0.0
var g_think_at := 0.0
var g_great_at := 0.0

## The moves a genius has, from what it is: its kind's, its Expression's, then one for each
## feature that brings one, in that order, no move twice, no more than `count` (and never more
## than fight.movesMax). Pure: the same body always has the same moves.
static func genius_moves(kind: String, expression: String, features: Array, count: int, favours: Array = []) -> Array:
	var F: Dictionary = Data.genius().get("fight", {})
	var ids: Array = []
	for id in F.get("byKind", {}).get(kind, []) + F.get("byExpression", {}).get(expression, []):
		if not ids.has(id):
			ids.append(id)
	for f in features:
		for id in F.get("byFeature", {}).get(String(f), []):
			if not ids.has(id):
				ids.append(id)
	# a companion's role keeps the moves it favours first (data/genius-types.json, roles)
	if not favours.is_empty():
		var first: Array = []
		for fid in favours:
			if ids.has(fid) and not first.has(fid):
				first.append(fid)
		ids = first + ids.filter(func(x): return not first.has(x))
	var out: Array = []
	for id in ids.slice(0, mini(count, int(F.get("movesMax", 3)))):
		var m: Dictionary = (F.get("moves", {}).get(id, {}) as Dictionary).duplicate()
		if m.is_empty():
			continue
		m["id"] = id
		if id == "lay":
			m["effect"] = "burn"
			for f in features:
				if F.get("layBy", {}).has(String(f)):
					m["effect"] = String(F["layBy"][String(f)])
					break
		out.append(m)
	return out

## The move only the great have, for a body of this kind and Expression ({} if none).
static func genius_great(kind: String, expression: String) -> Dictionary:
	var G: Dictionary = Data.genius().get("fight", {}).get("great", {})
	var m: Dictionary = G.get("byExpression", {}).get(expression, G.get("byKind", {}).get(kind, {}))
	return m.duplicate()

func _genius_setup() -> void:
	var F: Dictionary = Data.genius().get("fight", {})
	g_kind = String(Data.genius_bodies()["silhouettes"].get(String(genius.body.get("silhouette", "")), {}).get("kind", "quadruped"))
	g_age = F.get("ages", {}).get(String(genius.age().get("id", "grown")), { "strike": 1.0, "moves": 2, "wait": 1.0, "power": 1.0 })
	g_moves = Fight.genius_moves(g_kind, String(genius.body.get("expression", "")), genius.features(), int(g_age.get("moves", 2)))
	g_great = Fight.genius_great(g_kind, String(genius.body.get("expression", ""))) if float(g_age.get("great", 0.0)) > 0.0 else {}
	g_pos = p_pos + Vector2(-1.0, 0.8)
	g_order = genius.order if genius.order != "free" else "guard"
	g_great_at = float(F.get("great", {}).get("wait", 38.0)) * 0.4
	_genius_type_setup()

func _genius_has(id: String) -> Dictionary:
	for m in g_moves:
		if m["id"] == id:
			return m
	return {}

## Its plain blow's worth: the Hunt's damage, by Expression and Resonance.
func _genius_base() -> float:
	var ex: Dictionary = Data.genius()["byExpression"].get(genius.body.get("expression", ""), { "damage": 1.0, "interval": 1.0 })
	return float(_order("hunt")["hunt"]["damage"]) * float(ex["damage"]) * float(Data.genius()["byResonance"][str(genius.resonance())]) * _role_n("damage")

## Is it where it can guard its partner: beside them, or on the ground it holds with them on it?
func _genius_covers() -> bool:
	if g_order == "guard":
		return g_kind == "object" or g_pos.distance_to(p_pos) <= float(Data.genius()["fight"]["guardReach"])
	if g_order == "hold" and g_hold_at != Vector2.INF:
		var H: Dictionary = _order("hold")["hold"]
		return H.get("guardInside", false) and g_pos.distance_to(g_hold_at) <= 1.2 and p_pos.distance_to(g_hold_at) <= float(H["radius"])
	return false

## Guard: it takes the hit you did not see, out of its own Will.
func _genius_guards(dmg: float) -> bool:
	if not genius or genius.fallen or now < g_guard_ready_at or g_type != "companion" or not _genius_covers():
		return false
	var o := _order("guard")
	var brace := _genius_has("brace")
	var cost := float(o["guard"]["willCost"]) * float(brace.get("guardCost", 1.0)) * _role_n("guardCost")
	# It guards with whatever Will it has left; emptied by the blow, it falls (braced, it does not).
	if g_will <= 0.0:
		return false
	var spent := cost + dmg * 0.5 * float(brace.get("takes", 1.0))
	g_will = maxf(1.0 if not brace.is_empty() else 0.0, g_will - spent)
	stats["g_will_spent"] += spent
	stats["g_guards"] += 1
	g_guard_ready_at = now + float(o["guard"]["cooldown"]) * float(brace.get("guardCooldown", 1.0)) * _role_n("guardCooldown")
	g_regen_from = now + float(Data.genius()["will"]["regenDelayAfterHit"])
	_emit({ "type": "genius-guard", "damage": dmg, "braced": not brace.is_empty() })
	if g_will <= 0.0:
		_genius_fall()
	return true

## A blow at its partner that the genius turns or takes before anything else is asked: the
## wall of a great one, or a strike it called onto itself. True if the partner is untouched.
func _genius_turns(dmg: float, idx: int) -> bool:
	if not genius or genius.fallen:
		return false
	if g_ward_blows > 0:
		g_ward_blows -= 1
		stats["g_guards"] += 1
		_emit({ "type": "genius-ward", "left": g_ward_blows })
		_emit({ "type": "turned" })
		return true
	if idx < 0 and now < g_called_until:
		g_called_until = -9.0
		var spent := dmg * float(g_called.get("takes", 0.5))
		g_will = maxf(0.0, g_will - spent)
		stats["g_will_spent"] += spent
		stats["g_guards"] += 1
		g_regen_from = now + float(Data.genius()["will"]["regenDelayAfterHit"])
		_emit({ "type": "genius-called", "damage": dmg })
		if g_will <= 0.0:
			_genius_fall()
		return true
	return false

## What a blow at its partner is worth after the genius's ground has had its say (a dark
## place weakens what strikes from inside it), and what the foe owes for landing it.
func _genius_on_struck(dmg: float, from_pos: Vector2, idx: int) -> float:
	if not genius or genius.fallen:
		return dmg
	if not g_zone.is_empty() and now < float(g_zone["until"]) and g_zone["effect"] == "dark" and from_pos.distance_to(g_zone["at"]) <= float(g_zone["radius"]):
		dmg *= float(Data.genius()["fight"]["lays"]["dark"]["weaken"])
	return dmg

func _genius_debt_paid(dmg: float, idx: int) -> void:
	if not genius or genius.fallen or idx >= 0 or now >= g_debt_until or w_state in ["down", "absent"]:
		return
	g_debt_until = -9.0
	var owed := roundf(_genius_base() * float(g_debt.get("paid", 3.0)) * float(g_age.get("power", 1.0)) + dmg * float(g_debt.get("share", 0.5)))
	_emit({ "type": "genius-move", "move": "debt-paid", "name": "The debt is paid", "at": w_pos })
	_genius_hits(owed, "debt", true)

## Its damage lands on the locked foe: guarded like any blow out of turn, whole in an opening.
func _genius_hits(dmg: float, what: String, through := false) -> void:
	if w_state in ["down", "absent"]:
		return
	# a Hunter's blow into an opening (the foe staggered, recovering, or its guard brought down)
	var into := _own("opening")
	if into > 0.0 and what != "with" and (w_state in ["stagger", "recover"] or now < w_open_until):
		dmg *= 1.0 + (float(_own_spec("opening").get("damage", 1.5)) - 1.0) * into
	dmg = roundf(dmg if through else _guarded(dmg))
	if w_state == "stagger":
		dmg = roundf(dmg * float(room["break"]["staggerDamageFactor"]))
	if now < w_exposed_until:
		dmg = roundf(dmg * w_exposed)
	dmg = maxf(1.0, dmg)
	w_hp = maxf(w_floor, w_hp - dmg)
	stats["damage_dealt"] += dmg
	stats["g_damage"] += dmg
	_emit({ "type": "genius-hunt", "damage": dmg, "at": w_pos, "move": what })
	if w_hp == 0.0:
		stats["wolves_down"] += 1
		_wolf_set("down", float(beast["respawnSeconds"]))
		_emit({ "type": "wolf-down" })
		_emit({ "type": "anim", "who": "wolf", "name": "Death", "speed": 1.0 })

## Its damage on one of the pack.
func _genius_hits_other(i: int, dmg: float) -> void:
	var fo: Foe = foes[i]
	if not fo.alive():
		return
	dmg = maxf(1.0, roundf(dmg))
	fo.hp = maxf(0.0, fo.hp - dmg)
	stats["damage_dealt"] += dmg
	stats["g_damage"] += dmg
	_emit({ "type": "foe-hit", "foe": i, "damage": dmg, "heavy": false, "dist": fo.pos.distance_to(p_pos), "genius": true })
	if fo.hp == 0.0:
		stats["wolves_down"] += 1
		fo.set_state("down", 99.0)
		_emit({ "type": "foe-down", "foe": i, "name": fo.beast["name"] })

func _genius_spend(m: Dictionary, wait_key: String) -> void:
	var cost := float(m.get("will", 0.0))
	g_will = maxf(0.0, g_will - cost)
	stats["g_will_spent"] += cost
	stats["g_moves"] += 1
	g_wait[wait_key] = now + float(m.get("wait", 0.0)) * float(g_age.get("wait", 1.0))
	g_move_now = String(m.get("name", wait_key))
	g_move_until = now + 1.6

## One of its moves, made on the foe at `at`. False if it could not be made now.
func _genius_move(m: Dictionary) -> bool:
	var power := float(g_age.get("power", 1.0))
	var base := _genius_base()
	match String(m["id"]):
		"hamstring":
			_genius_spend(m, "hamstring")
			_emit({ "type": "genius-move", "move": "hamstring", "name": m["name"], "at": w_pos })
			_genius_hits(base * float(m["damage"]) * power, "hamstring")
			w_slow_until = now + float(m["slowSeconds"])
			w_slow = float(m["slow"])
		"stoop":
			_genius_spend(m, "stoop")
			_emit({ "type": "genius-move", "move": "stoop", "name": m["name"], "at": w_pos })
			_genius_hits(base * float(m["damage"]) * power, "stoop")
			g_climb_until = now + float(m["climb"])
			g_pos = w_pos
		"shot":
			_genius_spend(m, "shot")
			_emit({ "type": "genius-move", "move": "shot", "name": m["name"], "at": w_pos, "from": g_pos })
			_genius_hits(base * float(m["damage"]) * power, "shot")
		"debt":
			if now < g_debt_until:
				return false
			_genius_spend(m, "debt")
			g_debt_until = now + float(m["seconds"])
			g_debt = m
			_emit({ "type": "genius-move", "move": "debt", "name": m["name"], "at": w_pos, "seconds": float(m["seconds"]) })
		"lay":
			_genius_spend(m, "lay")
			g_zone = { "at": w_pos, "until": now + float(m["seconds"]), "radius": float(m["radius"]), "effect": String(m.get("effect", "burn")), "power": power, "tick": now }
			_emit({ "type": "genius-move", "move": "lay", "name": m["name"], "at": w_pos, "effect": g_zone["effect"], "radius": g_zone["radius"], "seconds": float(m["seconds"]) })
		"light":
			_genius_spend(m, "light")
			g_lit_until = now + float(m["seconds"])
			g_lit = float(m["parryWindow"])
			_emit({ "type": "genius-move", "move": "light", "name": m["name"], "at": p_pos, "seconds": float(m["seconds"]) })
		"call":
			_genius_spend(m, "call")
			g_called_until = now + float(m["seconds"])
			g_called = m
			_emit({ "type": "genius-move", "move": "call", "name": m["name"], "at": g_pos })
		_:
			return false
	return true

## The move only the great have.
func _genius_great_move() -> void:
	var G: Dictionary = Data.genius()["fight"]["great"]
	var strength := float(g_age.get("great", 0.0))
	var cost := float(G.get("will", 18.0))
	g_will = maxf(0.0, g_will - cost)
	stats["g_will_spent"] += cost
	stats["g_moves"] += 1
	stats["g_great"] += 1
	g_great_at = now + float(G.get("wait", 38.0)) * float(g_age.get("wait", 1.0)) / maxf(0.5, strength)
	g_move_now = String(g_great.get("name", "its great move"))
	g_move_until = now + 2.4
	_emit({ "type": "genius-great", "name": g_move_now, "effect": g_great.get("effect", ""), "at": w_pos })
	var base := _genius_base()
	match String(g_great.get("effect", "")):
		"stagger":
			if w_state not in ["down", "absent"]:
				_wolf_set("stagger", float(g_great["seconds"]) * strength)
				_emit({ "type": "stagger", "seconds": float(g_great["seconds"]) * strength, "cause": "genius" })
				_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 0.7 })
				_genius_hits(base * float(g_great["damage"]) * strength, "great")
		"ward":
			g_ward_blows = maxi(g_ward_blows, maxi(1, roundi(float(g_great["blows"]) * strength)))
		"double":
			g_double_until = now + float(g_great["seconds"]) * strength
			g_double = float(g_great.get("share", 0.6))
		"flood":
			var lay := _genius_has("lay")
			g_zone = { "at": Vector2.ZERO, "until": now + float(g_great["seconds"]) * strength, "radius": maxf(arena.x, arena.y), "effect": String(lay.get("effect", "burn")), "power": float(g_age.get("power", 1.0)) * 1.3, "tick": now }
		"reckon":
			_genius_hits(base * float(g_great["damage"]) * strength, "great", true)
			g_debt_until = now + 8.0
			g_debt = _genius_has("debt") if not _genius_has("debt").is_empty() else { "paid": 3.0, "share": 0.6 }

## After a blow of its partner's lands: a worn genius adds its own every so many, and for a
## while after the second hand every blow lands twice.
func _genius_after_hit(dmg: float, from_pattern: bool) -> void:
	if not genius or genius.fallen or from_pattern or w_state in ["down", "absent"]:
		return
	var w := _genius_has("with")
	var worth := float(g_age.get("power", 1.0))
	# a weapon genius strikes with its partner from the shoulder from its First Form (in the
	# hand it is the blow itself); so does an item whose path says so
	if g_type == "weapon" and not g_weapon.is_empty():
		w = {} if g_in_hand else (_types()["weapon"]["with"] as Dictionary)
		worth = g_worth
	elif g_type in ["defense", "ritual"]:
		w = g_item.get("always", {}).get("with", {})
		worth = g_worth
	if not w.is_empty():
		g_with += 1
		if g_with % maxi(1, int(w.get("every", 3))) == 0:
			g_move_now = String(w.get("name", "Strikes with you"))
			g_move_until = now + 1.0
			stats["g_moves"] += 1
			_genius_hits(_genius_base() * float(w["damage"]) * worth, "with")
	if now < g_double_until and w_state not in ["down", "absent"]:
		_genius_hits(dmg * g_double, "double", true)

## Free: it chooses among the other orders from how its partner fights, and says why.
func _genius_thinks() -> void:
	var fr: Dictionary = _order("free").get("free", {})
	g_think_at = now + float(fr.get("think", 2.5))
	var lt: Dictionary = genius.lifetime
	var hurts := float(lt.get("fights.hurts", 0.0)) + float(stats["hurts"])
	var parries := float(lt.get("fights.parries", 0.0)) + float(stats["parries"])
	var blocks := float(lt.get("fights.blocks", 0.0)) + float(stats["blocks"])
	var came := hurts + parries + blocks + 1.0
	var rng_line: Dictionary = genius.tally.get("range", {}) if genius.tally.get("range", {}) is Dictionary else {}
	var landed := float(rng_line.get("close", 0.0)) + float(rng_line.get("mid", 0.0)) + float(rng_line.get("far", 0.0)) + 1.0
	var hp_max := float(room["player"]["health"])
	var seen := {
		"base": 1.0, "hurtShare": hurts / came, "parryShare": parries / came,
		"lowHealth": clampf((0.5 - p_hp / hp_max) / 0.5, 0.0, 1.0),
		"close": float(rng_line.get("close", 0.0)) / landed, "far": float(rng_line.get("far", 0.0)) / landed,
		"open": 1.0 if (w_state not in ["down", "absent"] and beast.has("guard") and guard_open()) or w_state == "stagger" else 0.0,
		"post": 1.0 if g_post != Vector2.INF else 0.0, "pack": 1.0 if foes_alive() > 0 else 0.0 }
	var can: Array = genius.orders_available().map(func(o): return o["id"])
	var best := ""
	var best_s := -INF
	var best_why := "base"
	var now_s := -INF
	for id in ["guard", "hunt", "hold"]:
		if not can.has(id) or not fr.get("weights", {}).has(id):
			continue
		var s := 0.0
		var top := "base"
		var top_v := 0.0
		for k in fr["weights"][id]:
			var v := float(fr["weights"][id][k]) * float(seen.get(k, 0.0))
			s += v
			if k != "base" and v > top_v:
				top_v = v
				top = k
		if id == g_order:
			now_s = s
		if s > best_s:
			best_s = s
			best = id
			best_why = top
	if best == "" or best == g_order or best_s < now_s + float(fr.get("margin", 0.25)):
		if g_free_why == "":
			g_free_why = String(fr.get("why", {}).get("base", ""))
		return
	g_order = best
	g_free_why = String(fr.get("why", {}).get(best_why, ""))
	if best == "hold":
		g_hold_at = g_post if g_post != Vector2.INF else p_pos
	_emit({ "type": "free", "order": best, "why": g_free_why })

## The genius's turn: it gets to where its order puts it, and does what it is.
func _update_genius(dt: float) -> void:
	if not genius:
		return
	if genius.fallen:
		if g_up_at > 0.0 and now >= g_up_at:
			genius.recover()
			g_will = g_will_max * 0.5
			g_up_at = -1.0
			_emit({ "type": "genius-up" })
		return
	# held in the hand it gets none of its Will back: it rests at the shoulder
	if now >= g_regen_from and not g_in_hand:
		g_will = minf(g_will_max, g_will + float(Data.genius()["will"]["regenPerSecond"]) * _rest_k() * dt)
	var F: Dictionary = Data.genius()["fight"]
	# a weapon or an item takes no orders: it is with its partner, and does what its type does
	if g_type != "companion":
		_update_typed(dt)
		return
	# its order: what it was told, or on Free what it judges
	if genius.order == "free":
		if now >= g_think_at:
			_genius_thinks()
	elif g_order != genius.order:
		g_order = genius.order
		g_free_why = ""
	if g_order == "hold" and g_hold_at == Vector2.INF:
		g_hold_at = g_post if g_post != Vector2.INF else p_pos
	if g_order != "hold":
		g_hold_at = Vector2.INF
	var foe_up := w_state not in ["down", "absent"]
	var hunting: bool = g_order == "hunt" and foe_up and p_lock and dist() <= float(_order("hunt")["hunt"]["reach"])
	# where it goes
	var side := p_pos + Vector2.from_angle(p_facing + 2.2) * 1.1
	# its role's place beside its partner: a Bulwark between them and the foe, a Lookout behind
	var stands := String(g_role.get("stands", ""))
	var toward := (w_pos - p_pos).normalized() if foe_up and dist() > 0.2 else Vector2.from_angle(p_facing)
	if stands == "front" and foe_up:
		side = p_pos + toward * 1.6
	elif stands == "back":
		side = p_pos - toward * 2.2
	var want := side
	if g_order == "hold":
		want = g_hold_at
	elif hunting:
		# a runner comes round behind the foe; the rest come at it from where they are. A
		# Harrier is always behind it; a Bulwark stands in its face, between it and its partner.
		var away := (w_pos - p_pos).normalized() if g_kind == "quadruped" else (g_pos - w_pos).normalized()
		if stands == "flank":
			away = toward
		elif stands == "front":
			away = -toward
		if away.length() < 0.5:
			away = Vector2.RIGHT
		want = w_pos + away * (float(beast["radius"]) + 0.9)
	var speed := float(F.get("speed", {}).get(g_kind, 6.0)) * _role_n("speed")
	if g_kind == "object" or speed <= 0.0:
		g_pos = p_pos
	else:
		var to := want - g_pos
		g_pos = want if to.length() <= speed * dt else g_pos + to.normalized() * speed * dt
	# what it has laid on the ground
	if not g_zone.is_empty():
		if now >= float(g_zone["until"]):
			g_zone = {}
			_emit({ "type": "genius-zone-end" })
		else:
			_genius_zone()
	# the moves it makes whatever its order: light on the ground when a foe is near
	if foe_up and dist() <= 9.0:
		for m in g_moves:
			if String(m.get("when", "")) == "any" and not m.get("passive", false) and now >= float(g_wait.get(m["id"], 0.0)) and g_will >= float(m.get("will", 0.0)) and now >= g_lit_until:
				_genius_move(m)
				break
	# the move only the great have
	if not g_great.is_empty() and now >= g_great_at and foe_up and g_will >= float(F["great"].get("will", 18.0)) and dist() <= float(F["great"].get("reach", 9.0)):
		# at its partner's side it keeps to what shields them; hunting or holding, it uses what it has
		if g_order != "guard" or String(g_great.get("effect", "")) in ["ward", "double"]:
			_genius_great_move()
	# what only its role does (data/genius-types.json, roles)
	if not g_role.is_empty():
		_role_acts(foe_up)
	match g_order:
		"guard":
			# while it guards: a strike wound up at its partner, it may call onto itself
			var call := _genius_has("call")
			if not call.is_empty() and w_state == "windup" and w_target == -1 and now >= float(g_wait.get("call", 0.0)) and now >= g_called_until and g_will >= float(call.get("will", 0.0)) and _genius_covers():
				_genius_move(call)
		"hunt":
			if hunting:
				_genius_hunts(_order("hunt")["hunt"], g_pos)
		"hold":
			_genius_holds(_order("hold")["hold"])

## Hunt: its moves when they are ready, its plain blow between them.
func _genius_hunts(h: Dictionary, from: Vector2) -> void:
	if now < g_climb_until:
		return
	var F: Dictionary = Data.genius()["fight"]
	var ex: Dictionary = Data.genius()["byExpression"].get(genius.body.get("expression", ""), { "damage": 1.0, "interval": 1.0 })
	var gap := from.distance_to(w_pos) - float(beast["radius"])
	var near := (dist() <= float(F.get("wornReach", 3.4))) if g_kind == "object" else gap <= float(F.get("strikeRange", 1.9))
	for m in g_moves:
		if String(m.get("when", "")) != "hunt" or m.get("passive", false) or now < float(g_wait.get(m["id"], 0.0)) or g_will < float(m.get("will", 0.0)):
			continue
		if near or (m.has("reach") and gap <= float(m["reach"])):
			if _genius_move(m):
				g_hunt_at = maxf(g_hunt_at, now + 0.8)
				return
	if not near or now < g_hunt_at or g_will < float(h["willCost"]):
		return
	g_hunt_at = now + float(h["interval"]) * float(ex["interval"]) * float(g_age.get("wait", 1.0)) * _role_n("interval")
	g_will -= float(h["willCost"])
	stats["g_will_spent"] += float(h["willCost"])
	_genius_hits(_genius_base() * float(g_age.get("strike", 1.0)), "strike")
	# a young one's blow is a nip: now and then the foe flinches from it
	var nip: Dictionary = g_age.get("nip", {})
	if not nip.is_empty():
		g_nips += 1
		if g_nips % maxi(1, int(nip.get("every", 3))) == 0 and w_state in ["prowl", "approach", "recover", "idle"]:
			_wolf_set("flinch", float(nip.get("flinch", 0.4)))
			_emit({ "type": "genius-move", "move": "nip", "name": "A nip", "at": w_pos })
			_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 1.2 })

## Hold: it stays on its ground; what comes onto it is struck and slowed.
func _genius_holds(H: Dictionary) -> void:
	if g_hold_at == Vector2.INF or g_pos.distance_to(g_hold_at) > 1.2:
		return
	var r := float(H["radius"])
	var wolf_in := w_state not in ["down", "absent"] and w_pos.distance_to(g_hold_at) <= r + float(beast["radius"])
	# its own moves, on the locked foe when it is on the ground
	if wolf_in and now >= g_climb_until:
		for m in g_moves:
			if String(m.get("when", "")) == "hunt" and not m.get("passive", false) and now >= float(g_wait.get(m["id"], 0.0)) and g_will >= float(m.get("will", 0.0)):
				if _genius_move(m):
					g_hunt_at = maxf(g_hunt_at, now + 0.8)
					return
	if now < g_hunt_at or g_will < float(H["willCost"]):
		return
	# the nearest thing on its ground
	var best := -2
	var best_d := INF
	if wolf_in:
		best = -1
		best_d = w_pos.distance_to(g_hold_at)
	for i in foes.size():
		var fo: Foe = foes[i]
		if fo.alive() and fo.pos.distance_to(g_hold_at) <= r and fo.pos.distance_to(g_hold_at) < best_d:
			best = i
			best_d = fo.pos.distance_to(g_hold_at)
	if best == -2:
		return
	g_hunt_at = now + float(H["interval"]) * float(g_age.get("wait", 1.0))
	g_will -= float(H["willCost"])
	stats["g_will_spent"] += float(H["willCost"])
	var ex: Dictionary = Data.genius()["byExpression"].get(genius.body.get("expression", ""), { "damage": 1.0, "interval": 1.0 })
	var dmg := float(H["damage"]) * float(ex["damage"]) * float(Data.genius()["byResonance"][str(genius.resonance())]) * maxf(0.4, float(g_age.get("strike", 1.0)))
	_emit({ "type": "genius-hold", "at": g_hold_at, "foe": best })
	if best == -1:
		_genius_hits(dmg, "hold")
		w_slow_until = maxf(w_slow_until, now + float(H["slowSeconds"]))
		w_slow = float(H["slow"])
	else:
		_genius_hits_other(best, dmg)

## What it has laid on the ground does its work on what stands there.
func _genius_zone() -> void:
	var L: Dictionary = Data.genius()["fight"]["lays"]
	var at: Vector2 = g_zone["at"]
	var r := float(g_zone["radius"])
	var wolf_in := w_state not in ["down", "absent"] and w_pos.distance_to(at) <= r + float(beast["radius"])
	match String(g_zone["effect"]):
		"burn":
			if now - float(g_zone["tick"]) >= 0.5:
				g_zone["tick"] = now
				var d := _genius_base() * float(L["burn"]["perSecond"]) * 0.5 * float(g_zone["power"])
				if wolf_in:
					_genius_hits(d, "lay")
				for i in foes.size():
					if (foes[i] as Foe).alive() and (foes[i] as Foe).pos.distance_to(at) <= r:
						_genius_hits_other(i, d)
		"chill":
			if wolf_in:
				w_slow_until = maxf(w_slow_until, now + 0.3)
				w_slow = float(L["chill"]["slow"])

func _genius_fall() -> void:
	genius.fall()
	stats["g_falls"] += 1
	g_called_until = -9.0
	g_will = 0.0
	g_up_at = now + float(Data.genius()["fall"]["roomRecoverSeconds"]) if respawn else -1.0
	_emit({ "type": "genius-fall" })

func _order(id: String) -> Dictionary:
	for o in Data.genius()["orders"]:
		if o["id"] == id:
			return o
	return {}

## What the genius learns from the fight: where hits land, the families used, the orders
## it carried out, the Pattern fired.
func _record(evs: Array) -> void:
	for e in evs:
		match String(e["type"]):
			"hit":
				if not e.get("pattern", false):
					genius.hit_at(float(e.get("dist", 2.0)))
					_typed_learns("hit", e)
			"foe-hit":
				if not e.get("genius", false):
					_typed_learns("hit", e)
			"technique":
				genius.used_family("%s.%s" % [player_shape, String(tech.get("family", ""))])
			"pattern-start":
				genius.pattern_fired()
				genius.used_family(String(pattern["form"]))
			"foe-pattern":
				var made := genius.witness({ "name": e["name"], "form": e["form"], "terms": e["terms"] })
				if not made.is_empty():
					_emit({ "type": "shadow-made", "name": e["name"] })
			"genius-guard": genius.gave_order("guard")
			"genius-hunt":
				if String(e.get("move", "")) in ["strike", "hamstring", "stoop", "shot"]:
					genius.gave_order("hunt")
				elif String(e.get("move", "")) == "with":
					_typed_learns("with", e)
			"genius-hold": genius.gave_order("hold")
			"free": genius.gave_order("free")
			# how its partner meets a blow: what Free judges by
			"parry":
				genius.met_blow("parries")
				_typed_learns("turn", e)
			"hurt": genius.met_blow("hurts")
			"block":
				genius.met_blow("blocks")
				_typed_learns("turn", e)
			"evade":
				if String(e.get("how", "")) == "dodged":
					genius.met_blow("dodges")

# ===================================================================== the genius's type
# What a genius does beside its partner follows from the class of its base
# (data/genius-types.json; docs/genius-types.md). A weapon is taken in hand on a switch with
# the main weapon, and strikes with its partner from the shoulder. A defensive or a ritual
# item has something always true of the one who has it, and one thing they do with it. A
# companion has a role laid over its moves and its orders: where it stands, the moves it
# favours, its numbers, and one thing only that role does. One key, the genius's, means what
# its type means. A genius whose base has no type written fights as genii did before types.

const HELD := -2                 # whom the foe is after while a Bulwark holds it: the genius

var g_type := "companion"        # weapon, defense, ritual, companion
var g_base := ""                 # its base (a hybrid's first)
var g_path := ""                 # the path it took ("" while it is only settled)
var g_worth := 1.0               # how much of its function it has at its age (types.ages)
var g_twait := 1.0               # its type's waits, longer or shorter by its age
# --- a weapon
var g_weapon: Dictionary = {}    # what it is in the hand: { style, willPerBlow, held, sig }
var g_in_hand := false
var g_out_at := -99.0            # when it was last let go
var g_cut_until := -9.0          # the cut of the draw: its first blow after it is taken up
var g_cut_blow := false          # the blow in flight is that cut
var g_first_draw := false        # its first arrow from a full draw is still to come
var g_riposte_until := -9.0      # the answer to a parry
var g_score := 0                 # blows its partner has taken, cut into its flat
var g_shots := 0                 # blows in a row since it was taken up
var main: Dictionary = {}        # the weapon put away while the genius is held
var p_startup_k := 1.0           # how much of its startup the swing in flight takes
var p_draw_k := 1.0              # how much of its time the draw in progress takes
var p_moved_at := 0.0            # when its partner last moved (a stand is feet set)
var w_weak_until := -9.0         # a strike with the weight taken out of it
var w_weak := 1.0
# --- an item
var g_item: Dictionary = {}      # { type, worn, always, use, bend } with its path laid over
var g_use_at := 0.0              # when it can be used again
var g_used_at := -9.0            # when it was last used well
var g_set_until := -9.0          # a shield that is set
var g_set_blows := 0
var g_door: Dictionary = {}      # a shield set on the ground: { at, until, radius, blows }
var g_lamp: Dictionary = {}      # lit ground: { at, until, radius, tick }
var g_sight_until := -9.0        # the locked foe is sighted
var g_measure := 0               # measures taken of the locked foe
var g_measures: Dictionary = {}  # beast id -> measures kept of its kind
var g_auto_at := 0.0             # when an hour-bell next tolls of itself
var g_fall_caught := false       # an open hand has caught its partner this fight
var p_slip: Dictionary = {}      # the slip in flight: { dir, distance, iframes }
var p_haste_until := -9.0
var p_haste := 1.0
var p_punish_until := -9.0       # the blow after a blow slipped
var p_punish := 1.0
var p_hurt_at := -9.0            # when its partner was last hurt, and by how much
var p_hurt_dmg := 0.0
var p_struck_at := -9.0          # when a blow last landed on its partner, blocked or not
# --- a companion's role
var g_role: Dictionary = {}      # roles[its role]
var g_role_id := ""
var g_shade: Dictionary = {}     # the role its path shades toward ({} for none, or its own)
var g_shade_id := ""
var g_role_k := 0.0              # the strength of its role's own thing
var g_shade_k := 0.0             # and of its shade's
var g_role_text := ""
var g_held_until := -9.0         # the foe is held on it
var g_mend_at := 0.0
var w_open_until := -9.0         # the foe's guard is down (worried, caught, taken apart)
var w_exposed_until := -9.0      # and every blow on it lands for more
var w_exposed := 1.0
var g_opening_until := -9.0      # the opening a Lookout called
var g_opening := 1.0

func _types() -> Dictionary:
	return Data.genius_types()

## Its type, read off its form, and what that gives it in this fight.
func _genius_type_setup() -> void:
	var what := GeniusTypes.of(genius)
	g_type = String(what["type"])
	g_base = String(what["base"])
	g_path = String(what["path"])
	var row := GeniusTypes.age_row(genius.instar)
	g_worth = float(row.get("worth", 1.0))
	g_twait = float(row.get("wait", 1.0))
	if not what["written"]:
		return
	var is_great := float(g_age.get("great", 0.0)) > 0.0
	match g_type:
		"weapon":
			g_weapon = GeniusTypes.weapon_spec(g_base, g_path)
			g_kind = "object"
			g_moves = []
			var gr: Dictionary = g_weapon.get("great", _types()["weapon"].get("great", {}))
			if is_great and not gr.is_empty():
				g_great = gr.duplicate()
		"defense", "ritual":
			g_item = GeniusTypes.item_spec(g_base, g_path, g_worth)
			g_kind = "object"
			g_moves = []
			if is_great and g_item.has("great"):
				g_great = (g_item["great"] as Dictionary).duplicate()
		"companion":
			var r := GeniusTypes.role_spec(g_base, g_path)
			if r.is_empty():
				return
			g_role = r["role"]
			g_role_id = String(r["id"])
			g_shade = r["shade"]
			g_shade_id = String(r["shade_id"])
			g_role_k = float(r["k"]) * g_worth
			g_shade_k = float(r["shade_k"]) * g_worth
			g_role_text = String(r["text"])
			g_will_max *= _role_n("will")
			if not genius.fallen:
				g_will = g_will_max
			# the moves its role favours are kept first as it ages, and come round sooner
			var fav: Array = (g_role.get("favours", []) as Array) + (g_shade.get("favours", []) as Array)
			g_moves = Fight.genius_moves(g_kind, String(genius.body.get("expression", "")), genius.features(), int(g_age.get("moves", 2)), fav)
			var sooner := float(_types().get("roles", {}).get("favourWait", 1.0))
			for m in g_moves:
				if (g_role.get("favours", []) as Array).has(m["id"]) and m.has("wait"):
					m["wait"] = float(m["wait"]) * sooner

## How much faster a weapon genius's Will comes back at the shoulder (weapon.rest).
func _rest_k() -> float:
	return float(_types().get("weapon", {}).get("rest", 1.0)) if g_type == "weapon" else 1.0

## One of its role's numbers (will, damage, interval, speed, guardCost, guardCooldown): 1 for a
## genius with no role.
func _role_n(key: String) -> float:
	return float(g_role.get("numbers", {}).get(key, 1.0)) if g_type == "companion" else 1.0

## How strongly it has a role's own thing (hold-it, opening, worry, mend, calls): its role's at
## the worth of its age, its shade's at a share of that, 0 if it has neither or has fallen.
func _own(id: String) -> float:
	if g_type != "companion" or genius == null or genius.fallen:
		return 0.0
	if String(g_role.get("own", {}).get("id", "")) == id:
		return g_role_k
	if String(g_shade.get("own", {}).get("id", "")) == id:
		return g_shade_k
	return 0.0

func _own_spec(id: String) -> Dictionary:
	if String(g_role.get("own", {}).get("id", "")) == id:
		return g_role["own"]
	if String(g_shade.get("own", {}).get("id", "")) == id:
		return g_shade["own"]
	return {}

## What the genius's key would do now, for the HUD and the bots: { does (take, use, order),
## label, ready, left (seconds until it is), active (in the hand; set; lit) }.
func genius_key() -> Dictionary:
	if not genius:
		return { "does": "", "label": "", "ready": false, "left": 0.0, "active": false }
	match g_type:
		"weapon":
			var need := g_will_max * float(_types()["weapon"]["take"]["retake"])
			var ok := g_in_hand or (not genius.fallen and not p_disarmed and g_will >= need)
			var per := float(Data.genius()["will"]["regenPerSecond"]) * _rest_k()
			return { "does": "take", "label": "Let it go" if g_in_hand else "Take in hand", "ready": ok, "left": 0.0 if ok else maxf(0.0, (need - g_will) / maxf(0.01, per)), "active": g_in_hand }
		"defense", "ritual":
			var use: Dictionary = g_item.get("use", {})
			var left := maxf(0.0, g_use_at - now)
			return { "does": "use", "label": String(use.get("short", use.get("name", ""))), "ready": left <= 0.0 and g_will >= float(use.get("will", 0.0)) and not genius.fallen, "left": left,
				"active": now < g_set_until or not g_door.is_empty() or not g_lamp.is_empty() or now < g_sight_until }
	return { "does": "order", "label": String(_order(genius.order).get("name", genius.order)), "ready": not genius.fallen, "left": 0.0, "active": false }

## Can the key not be answered this moment? A weapon changes hands from a free hand, the end
## of a swing, a reload or a draw; an item is used out of anything but the Pattern.
func _key_busy() -> bool:
	if not genius or g_type == "companion":
		return false
	if p_state in ["pattern", "down"]:
		return true
	if g_type == "weapon":
		return not (p_state in ["free", "reload", "draw"] or (p_state == "attack" and _can_start_action()))
	return false

func _genius_key_pressed() -> void:
	if not genius:
		return
	match g_type:
		"weapon":
			if g_in_hand:
				_let_go()
			else:
				_take_in_hand()
		"defense", "ritual":
			_genius_use()

# --- a weapon, in the hand and out of it

## Take the genius in hand: the main weapon is put away and its partner fights with it.
func _take_in_hand() -> void:
	var W: Dictionary = _types()["weapon"]
	if genius.fallen or p_disarmed or g_weapon.is_empty() or g_will < g_will_max * float(W["take"]["retake"]):
		_emit({ "type": "genius-not-ready", "why": "disarmed" if p_disarmed else "spent" })
		return
	var st: Dictionary = (room["styles"].get(String(g_weapon["style"]), {}) as Dictionary).duplicate(true)
	if st.is_empty():
		return
	var sig: Dictionary = g_weapon.get("sig", {})
	# the weapon it is: its type's, with what its path lays over it. A gun's rounds are its Will.
	if st.has("shot"):
		for k in sig.get("shot", {}):
			st["shot"][k] = sig["shot"][k]
		st["ammo"] = 0
		st.erase("reload")
	for sw in st.get("combo", []):
		for k in sig.get("swing", {}):
			sw[k] = sig["swing"][k]
	if sig.has("heavyOn") and st.has("combo"):
		var hv: Dictionary = st["combo"][clampi(int(sig["heavyOn"]) - 1, 0, st["combo"].size() - 1)]
		hv["knockback"] = maxf(float(hv.get("knockback", 0.0)), 1.0)
	main = { "style": style, "combo": combo, "ranged": ranged, "ammo": p_ammo, "ammo_max": p_ammo_max, "gear_damage": gear_damage, "gear_trait": gear_trait }
	style = st
	ranged = String(st.get("kind", "melee")) == "ranged"
	combo = st.get("combo", [st.get("shot", {})])
	p_ammo_max = 0
	p_ammo = 0
	gear_damage = float(W["inHand"].get(String(genius.age().get("id", "grown")), 1.0)) * float(sig.get("damage", 1.0))
	gear_trait = {}
	p_state = "free"
	p_combo = 0
	p_buffer = false
	p_draw = 0.0
	p_last_attack_end = -9.0
	g_in_hand = true
	g_shots = 0
	var cut: Dictionary = W["take"]["drawCut"]
	var rested := now - g_out_at
	g_cut_until = now + float(cut["seconds"]) if rested >= float(cut["rest"]) else -9.0
	g_cut_blow = false
	g_first_draw = sig.has("firstFullDraw") and rested >= float(sig["firstFullDraw"]["rest"])
	_emit({ "type": "genius-take", "in": true, "style": String(g_weapon["style"]), "cut": g_cut_until > now })

## Let it go: it is back at the shoulder, and the weapon that was put away is in the hand.
## spent: it left the hand of itself, with too little Will for another blow.
func _let_go(spent := false) -> void:
	if not g_in_hand:
		return
	style = main["style"]
	combo = main["combo"]
	ranged = main["ranged"]
	p_ammo = main["ammo"]
	p_ammo_max = main["ammo_max"]
	gear_damage = main["gear_damage"]
	gear_trait = main["gear_trait"]
	main = {}
	g_in_hand = false
	g_out_at = now
	g_cut_until = -9.0
	g_cut_blow = false
	g_riposte_until = -9.0
	if p_state in ["attack", "draw", "reload"]:
		p_state = "free"
	p_combo = 0
	p_buffer = false
	p_draw = 0.0
	p_startup_k = 1.0
	p_draw_k = 1.0
	p_last_attack_end = -9.0
	g_regen_from = now + float(Data.genius()["will"]["regenDelayAfterHit"]) * 0.5
	_emit({ "type": "genius-take", "in": false, "spent": spent })

## Has it the Will for another blow (or is the blow the answer to a parry, which costs it none)?
func _hand_can_strike() -> bool:
	var sig: Dictionary = g_weapon.get("sig", {})
	if now < g_riposte_until and sig.get("afterParry", {}).get("free", false):
		return true
	return g_will >= float(g_weapon.get("willPerBlow", 0.0))

## The cut of the draw begins with this blow, if it was taken up rested and struck with at
## once. Returns how much of its time the blow's start takes (a bow's draw, or a swing's startup).
func _hand_cut_begins(draw: bool) -> float:
	if not g_in_hand or now >= g_cut_until:
		return 1.0
	g_cut_until = -9.0
	g_cut_blow = true
	return float(_types()["weapon"]["take"]["drawCut"]["startup"]) if draw == style.has("draw") else 1.0

## A swing or a shot begins with the genius in the hand: it costs it its Will.
func _hand_swing_starts() -> void:
	var sig: Dictionary = g_weapon.get("sig", {})
	var free: bool = now < g_riposte_until and sig.get("afterParry", {}).get("free", false)
	if not free:
		var cost := float(g_weapon.get("willPerBlow", 0.0))
		g_will = maxf(0.0, g_will - cost)
		stats["g_will_spent"] += cost
	if not style.has("draw"):
		p_startup_k = _hand_cut_begins(false)

func _startup(s: Dictionary) -> float:
	return float(s.get("startup", 0.0)) * p_startup_k

## How long the draw in progress takes to come to the full.
func draw_seconds() -> float:
	return float(style.get("draw", {}).get("seconds", 1.0)) * p_draw_k

## Is its partner at a stand: feet set, or on the fight's post?
func _stands() -> bool:
	var stand := float(_types().get("tally", {}).get("weapon", {}).get("stand", 0.8))
	if now - p_moved_at >= stand:
		return true
	return g_post != Vector2.INF and p_pos.distance_to(g_post) <= float(_order("hold").get("hold", {}).get("radius", 4.5))

## What the weapon in the hand adds to the blow about to land: the cut of the draw, and the
## one property its path gives it.
func _hand_blow() -> float:
	var sig: Dictionary = g_weapon.get("sig", {})
	var k := 1.0
	if g_cut_blow:
		k *= float(_types()["weapon"]["take"]["drawCut"]["damage"])
	if now < g_riposte_until and sig.has("afterParry"):
		k *= float(sig["afterParry"]["damage"])
	if sig.has("score") and g_score > 0:
		k *= 1.0 + float(sig["score"]["per"]) * g_score
	var full := style.has("draw") and p_charge >= 0.999
	if sig.has("firstFullDraw") and g_first_draw and full:
		k *= float(sig["firstFullDraw"]["damage"])
	if sig.has("far") and w_state not in ["down", "absent"]:
		var fr: Dictionary = sig["far"]
		k *= lerpf(1.0, float(fr["damage"]), clampf((dist() - float(fr["from"])) / maxf(0.1, float(fr["to"]) - float(fr["from"])), 0.0, 1.0))
	if sig.has("everyNth") and (g_shots + 1) % maxi(2, int(sig["everyNth"]["n"])) == 0:
		k *= float(sig["everyNth"]["damage"])
	if sig.has("still") and now - p_moved_at >= float(sig["still"]["seconds"]):
		k *= float(sig["still"]["damage"])
	return k

## After the blow: what landing it (or missing) spends, and what it leaves on the foe.
func _hand_blow_done(landed: bool, on_locked: bool, winding: bool) -> void:
	var sig: Dictionary = g_weapon.get("sig", {})
	var full := style.has("draw") and p_charge >= 0.999
	g_cut_blow = false
	g_shots += 1
	g_riposte_until = -9.0
	if full:
		g_first_draw = false
	if not landed:
		return
	if sig.has("score") and g_score > 0:
		_emit({ "type": "genius-sig", "sig": "score", "name": String(sig.get("name", "")), "at": w_pos, "count": g_score })
		g_score = 0
	if not on_locked:
		return
	if sig.has("onWindup") and winding and w_state == "windup":
		# the strike that follows this wind-up lands with the weight taken out of it
		w_weak_until = now + (w_duration - w_timer) + float(w_attack.get("active", 0.2)) + 0.25
		w_weak = float(sig["onWindup"]["weaken"])
		_emit({ "type": "genius-sig", "sig": "onWindup", "name": String(sig.get("name", "")), "at": w_pos })
	if sig.has("fullDraw") and full and w_state not in ["down", "absent"]:
		w_slow_until = maxf(w_slow_until, now + float(sig["fullDraw"]["seconds"]))
		w_slow = float(sig["fullDraw"]["slow"])
		_emit({ "type": "genius-sig", "sig": "fullDraw", "name": String(sig.get("name", "")), "at": w_pos })

# --- an item: what is always true, and what its partner does with it

## An always-true multiplier of the item's, at the worth of its age (1 if it has none):
## always[key], or always[key][sub].
func _always_k(key: String, sub := "") -> float:
	if genius == null or genius.fallen or g_type not in ["defense", "ritual"]:
		return 1.0
	var v: Variant = g_item.get("always", {}).get(key, null)
	if v is Dictionary and sub != "":
		v = (v as Dictionary).get(sub, null)
	if v == null or v is Dictionary:
		return 1.0
	return GeniusTypes.at_worth(float(v), g_worth)

## An always-true amount of the item's that is added, not multiplied, at the worth of its age.
func _always_add(key: String, sub: String) -> float:
	if genius == null or genius.fallen or g_type not in ["defense", "ritual"]:
		return 0.0
	var v: Variant = g_item.get("always", {}).get(key, null)
	if not (v is Dictionary) or not (v as Dictionary).has(sub):
		return 0.0
	return float(v[sub]) * g_worth

func _in_lamp(at: Vector2) -> bool:
	return not g_lamp.is_empty() and now < float(g_lamp["until"]) and at.distance_to(g_lamp["at"]) <= float(g_lamp["radius"])

## What a lamp's light does to something standing in it (use[what]; 1 outside it, or if its
## light does no such thing): found (a guard), shelter (a blow), willRegen.
func _lamp_k(what: String, at: Vector2) -> float:
	if g_lamp.is_empty() or genius == null or genius.fallen:
		return 1.0
	var use: Dictionary = g_item.get("use", {})
	if not use.has(what) or not _in_lamp(at):
		return 1.0
	return float(use[what])

## How much longer (or shorter) the moment to parry is for what its genius is and does, never
## more than caps.parryWindow: a blade in the hand, a sure hand, a lamp's light, a sighted
## foe, a Lookout watching.
func _parry_k() -> float:
	if not genius or genius.fallen:
		return 1.0
	var k := 1.0
	match g_type:
		"weapon":
			if g_in_hand:
				k *= float(g_weapon.get("sig", {}).get("parryWindow", 1.0))
		"defense", "ritual":
			var use: Dictionary = g_item.get("use", {})
			k *= _always_k("parryWindow")
			if use.has("parryWindow"):
				match String(use.get("effect", "")):
					"light":
						if _in_lamp(p_pos):
							k *= float(use["parryWindow"])
					"sight":
						if now < g_sight_until:
							k *= float(use["parryWindow"])
		"companion":
			var c := _own("calls")
			if c > 0.0:
				var o := _own_spec("calls")
				if g_pos.distance_to(p_pos) <= float(o.get("reach", 14.0)):
					k *= 1.0 + (float(o.get("parryWindow", 1.0)) - 1.0) * c
	return minf(k, float(_types().get("caps", {}).get("parryWindow", 2.2)))

## Its partner uses it: the one thing done with the key.
func _genius_use() -> void:
	var use: Dictionary = g_item.get("use", {})
	if use.is_empty() or genius.fallen:
		return
	if now < g_use_at or g_will < float(use.get("will", 0.0)):
		_emit({ "type": "genius-not-ready", "why": "wait" if now < g_use_at else "will" })
		return
	match String(use.get("effect", "")):
		"set": _use_set(use)
		"catch": _use_catch(use)
		"slip": _use_slip(use)
		"light": _use_light(use)
		"sight": _use_sight(use)
		"toll": _use_toll(use)

## It was used well: its Will is spent, its wait begins, and the Tally hears of it.
func _use_spent(use: Dictionary, at: Vector2) -> void:
	var cost := float(use.get("will", 0.0))
	g_will = maxf(0.0, g_will - cost)
	stats["g_will_spent"] += cost
	stats["g_moves"] += 1
	stats["g_uses"] = int(stats.get("g_uses", 0)) + 1
	g_use_at = now + float(use.get("wait", 8.0)) * g_twait
	g_used_at = now
	g_regen_from = now + float(Data.genius()["will"]["regenDelayAfterHit"])
	g_move_now = String(use.get("name", ""))
	g_move_until = now + 1.6
	_feeds(String(use.get("feeds", "guard")), float(_types()["tally"]["item"]["use"]))
	_emit({ "type": "genius-use", "effect": String(use.get("effect", "")), "name": g_move_now, "at": at })

## Count an act toward a line of the Tally's orders (a weapon or an item takes no orders, but
## the Reading reads that line still).
func _feeds(line: String, by: float) -> void:
	if genius == null or line == "":
		return
	genius.count("orders", line, by)
	genius.counter("orders." + line, by)

## The shield is set: for a moment the next blow is its own. Or it stands on the ground as a door.
func _use_set(use: Dictionary) -> void:
	_use_spent(use, p_pos)
	if use.has("ground"):
		g_door = { "at": p_pos, "until": now + float(use["ground"]["seconds"]), "radius": float(use["ground"]["radius"]), "blows": int(use.get("blows", 1)) }
		_emit({ "type": "genius-door", "at": p_pos, "radius": float(use["ground"]["radius"]), "seconds": float(use["ground"]["seconds"]) })
	else:
		g_set_until = now + float(use.get("seconds", 1.4))
		g_set_blows = int(use.get("blows", 1))

## A blow the item takes whole before anything else is asked: a shield that is set (for its
## partner, or for a classmate it covers), or one standing as a door while its partner is by it.
func _item_takes(dmg: float, ally: int) -> bool:
	if genius == null or genius.fallen or g_type != "defense":
		return false
	var use: Dictionary = g_item.get("use", {})
	var took := false
	if not g_door.is_empty() and now < float(g_door["until"]) and int(g_door["blows"]) > 0 and p_pos.distance_to(g_door["at"]) <= float(g_door["radius"]):
		g_door["blows"] = int(g_door["blows"]) - 1
		took = true
		if int(g_door["blows"]) <= 0:
			g_door = {}
			_emit({ "type": "genius-door-end" })
	elif now < g_set_until and g_set_blows > 0 and (ally < 0 or (use.has("allies") and (allies[ally]["pos"] as Vector2).distance_to(p_pos) <= float(use["allies"]))):
		g_set_blows -= 1
		took = true
		if g_set_blows <= 0:
			g_set_until = -9.0
	if not took:
		return false
	var spent := dmg * float(use.get("takes", 0.35))
	g_will = maxf(0.0, g_will - spent)
	stats["g_will_spent"] += spent
	stats["g_guards"] += 1
	g_regen_from = now + float(Data.genius()["will"]["regenDelayAfterHit"])
	_emit({ "type": "genius-took", "damage": dmg, "ally": ally })
	_emit({ "type": "turned" })
	return true

## The hand reaches for a strike before it is thrown: the nearest foe winding up within its
## reach (the locked one first; from farther, a strike wound up at a classmate, if it reaches
## for those). Nothing winding up, and it closes on air.
func _use_catch(use: Dictionary) -> void:
	var reach := float(use.get("reach", 3.0))
	var far := float(use.get("allyReach", 0.0))
	var who := -9
	if w_state == "windup":
		var gap := dist() - float(beast["radius"])
		if gap <= reach or (far > 0.0 and w_target >= 0 and gap <= far):
			who = -1
	if who == -9:
		for i in foes.size():
			var fo: Foe = foes[i]
			if fo.state != "windup":
				continue
			var gap2 := fo.pos.distance_to(p_pos) - float(fo.beast["radius"])
			if gap2 <= reach or (far > 0.0 and fo.target >= 0 and gap2 <= far):
				who = i
				break
	if who == -9:
		var miss := float(use.get("missWill", 0.0))
		g_will = maxf(0.0, g_will - miss)
		stats["g_will_spent"] += miss
		g_use_at = now + float(use.get("missWait", 2.5))
		_emit({ "type": "genius-use", "effect": "catch", "name": String(use.get("name", "")), "at": p_pos, "miss": true })
		return
	var at := w_pos if who == -1 else (foes[who] as Foe).pos
	_use_spent(use, at)
	var fl := float(use.get("flinch", 0.9))
	if who == -1:
		_wolf_set("flinch", fl)
		_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 1.1 })
		if use.has("open"):
			w_open_until = now + float(use["open"])
			w_exposed_until = w_open_until
			w_exposed = float(use.get("exposed", 1.0))
		if use.has("strike"):
			_genius_hits(_genius_base() * float(use["strike"]) * g_worth, "catch", true)
			if w_state not in ["down", "absent", "pinned"]:
				w_pos = _clamp_in(w_pos + (w_pos - p_pos).normalized() * float(use.get("knockback", 0.0)))
	else:
		(foes[who] as Foe).set_state("flinch", fl)
		if use.has("strike"):
			_genius_hits_other(who, _genius_base() * float(use["strike"]) * g_worth)
	_emit({ "type": "genius-caught", "foe": who, "at": at })

## The coat pulls its partner out: an instant step, untouchable, out of anything.
func _use_slip(use: Dictionary) -> void:
	_use_spent(use, p_pos)
	# with no direction held it goes round the foe, to its partner's left: out of the strike,
	# and no farther from the answer (straight back would be an invitation to pounce)
	var dir := p_dodge_dir
	if dir.length() < 0.1:
		dir = (w_pos - p_pos).orthogonal() if w_state not in ["down", "absent"] else -Vector2.from_angle(p_facing)
	if dir.length() < 0.01:
		dir = Vector2.LEFT
	p_slip = { "dir": dir.normalized(), "distance": float(use.get("distance", 1.0)), "iframes": float(use.get("iframes", 0.4)) }
	p_state = "dodge"
	p_timer = 0.0
	p_buffer = false
	p_draw = 0.0
	# made just after a blow landed, it takes most of that blow back
	if use.has("late") and now - p_hurt_at <= float(use["late"]["seconds"]) and p_hp > 0.0:
		var back := p_hurt_dmg * float(use["late"]["back"])
		p_hp = minf(float(room["player"]["health"]), p_hp + back)
		p_hurt_at = -9.0
		_emit({ "type": "genius-took-back", "amount": back })
	if use.has("willBack"):
		p_will = minf(float(rules["field"]["willMax"]), p_will + float(use["willBack"]))
	if use.has("haste"):
		p_haste_until = now + float(room["dodge"]["duration"]) + float(use["haste"]["seconds"])
		p_haste = float(use["haste"]["speed"])
	_emit({ "type": "anim", "who": "player", "name": "Dodge_Backward", "duration": float(room["dodge"]["duration"]) })
	_emit({ "type": "dodge", "dir": p_slip["dir"], "slip": true })

## The lantern is set down: lit ground, where its partner stands or at the foe's feet.
func _use_light(use: Dictionary) -> void:
	var at := p_pos
	if String(use.get("at", "partner")) == "foe" and w_state not in ["down", "absent"]:
		at = w_pos
	_use_spent(use, at)
	g_lamp = { "at": at, "until": now + float(use.get("seconds", 8.0)), "radius": float(use.get("radius", 4.5)), "tick": now }
	_emit({ "type": "genius-lamp", "at": at, "radius": float(g_lamp["radius"]), "seconds": float(use.get("seconds", 8.0)) })

## A sight is taken on the locked foe.
func _use_sight(use: Dictionary) -> void:
	if w_state in ["down", "absent"] or dist() > float(use.get("reach", 18.0)):
		_emit({ "type": "genius-not-ready", "why": "no foe" })
		return
	_use_spent(use, w_pos)
	g_sight_until = now + float(use.get("seconds", 7.0))
	_emit({ "type": "genius-sight", "seconds": float(use.get("seconds", 7.0)) })

## The bell tolls: every foe near that is winding up is broken out of its strike, and its
## partner is steadied. auto: it tolled of itself (an hour-bell), at no cost and no wait.
func _use_toll(use: Dictionary, auto := false) -> void:
	if not auto:
		_use_spent(use, p_pos)
	var r := float(use.get("radius", 5.5))
	var fl := float(use.get("flinch", 0.7))
	var broke := 0
	if w_state == "windup" and dist() - float(beast["radius"]) <= r:
		broke += 1
		if use.has("stagger"):
			_wolf_set("stagger", float(use["stagger"]))
			_emit({ "type": "stagger", "seconds": float(use["stagger"]), "cause": "genius" })
		else:
			_wolf_set("flinch", fl)
		_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 1.0 })
		if use.has("strike"):
			_genius_hits(_genius_base() * float(use["strike"]) * g_worth, "toll", true)
	for i in foes.size():
		var fo: Foe = foes[i]
		if fo.state == "windup" and fo.pos.distance_to(p_pos) - float(fo.beast["radius"]) <= r:
			broke += 1
			fo.set_state("stagger" if use.has("stagger") else "flinch", float(use["stagger"]) if use.has("stagger") else fl)
			if use.has("strike"):
				_genius_hits_other(i, _genius_base() * float(use["strike"]) * g_worth)
	p_will = minf(float(rules["field"]["willMax"]), p_will + float(use.get("willBack", 0.0)) * (0.5 if auto else 1.0))
	if use.has("mend") and not auto:
		p_hp = minf(float(room["player"]["health"]), p_hp + float(use["mend"]))
		for al in allies:
			if not al["down"]:
				al["hp"] = minf(float(al["hp_max"]), float(al["hp"]) + float(use["mend"]))
	_emit({ "type": "genius-toll", "at": p_pos, "radius": r, "broke": broke, "auto": auto })

## What its genius's type adds to a blow of its partner's on the locked foe: a foe exposed, an
## opening called, the blow after a slip, the measure taken, a sight.
func _typed_blow_k() -> float:
	var k := 1.0
	if now < w_exposed_until:
		k *= w_exposed
	if now < g_opening_until and w_state == "recover":
		k *= g_opening
	if now < p_punish_until:
		k *= p_punish
		p_punish_until = -9.0
	if genius == null or genius.fallen or g_type not in ["defense", "ritual"]:
		return k
	var al: Dictionary = g_item.get("always", {})
	var use: Dictionary = g_item.get("use", {})
	if al.has("measure") and g_measure > 0:
		k *= 1.0 + float(al["measure"]["per"]) * g_worth * g_measure
	if String(use.get("effect", "")) == "sight" and now < g_sight_until:
		if w_state in ["stagger", "recover"]:
			k *= float(use.get("damage", 1.0))
		elif use.has("far") and dist() >= float(use["far"]["from"]):
			k *= float(use["far"]["damage"])
	# a blow landed just after it was used: the item made the opening
	var af: Dictionary = _types()["tally"]["item"]["after"]
	if now - g_used_at <= float(af.get("seconds", 1.5)):
		_feeds(String(af["line"]), float(af["by"]))
		g_used_at = -9.0
	return k

## Its partner met a blow (parry, block, dodge, hurt): what its genius's type makes of that.
func _typed_met(how: String, idx: int, dmg: float) -> void:
	if how in ["block", "hurt"]:
		p_struck_at = now
	if how == "hurt":
		p_hurt_at = now
		p_hurt_dmg = dmg
	if genius == null or genius.fallen:
		return
	match g_type:
		"weapon":
			var sig: Dictionary = g_weapon.get("sig", {})
			if how == "parry" and g_in_hand and sig.has("afterParry"):
				g_riposte_until = now + float(sig["afterParry"]["seconds"])
			if how == "hurt" and sig.has("score"):
				g_score = mini(int(sig["score"]["max"]), g_score + 1)
		"defense", "ritual":
			var al: Dictionary = g_item.get("always", {})
			var use: Dictionary = g_item.get("use", {})
			var worked := false       # what is always true of it did its work
			match how:
				"parry":
					worked = al.has("parryWindow")
					if al.has("parryWill"):
						p_will = minf(float(rules["field"]["willMax"]), p_will + float(al["parryWill"]) * g_worth)
						worked = true
					# a parry in a lamp's light, or of a sighted foe, staggers it longer
					var more := 0.0
					if use.has("stagger") and String(use.get("effect", "")) == "light" and _in_lamp(p_pos):
						more += float(use["stagger"])
					if use.has("stagger") and String(use.get("effect", "")) == "sight" and now < g_sight_until and idx < 0:
						more += float(use["stagger"])
					if more > 0.0:
						if idx < 0 and w_state == "stagger":
							w_duration += more
						elif idx >= 0 and idx < foes.size() and (foes[idx] as Foe).state == "stagger":
							(foes[idx] as Foe).duration += more
				"block":
					worked = al.has("block")
				"dodge":
					worked = al.has("dodge")
					# a blow slipped leaves the foe looking at where its partner was
					if not p_slip.is_empty() and use.has("punish"):
						p_punish_until = now + float(use["punish"]["seconds"])
						p_punish = float(use["punish"]["damage"])
				"hurt":
					worked = al.has("hurt")
			# an astrolabe takes the measure of a strike that was answered
			if al.has("measure") and idx < 0 and how in ["parry", "block", "dodge"]:
				g_measure = mini(int(al["measure"]["max"]), g_measure + 1)
				worked = true
			if worked:
				_feeds(String(al.get("feeds", "free")), float(_types()["tally"]["item"]["always"]))

## What a weapon genius learns from a fight, in place of orders carried out: blows landed with
## it in the hand (from a stand, or not), blows turned with it, blows it added from the shoulder.
func _typed_learns(what: String, e: Dictionary) -> void:
	if g_type != "weapon" or g_weapon.is_empty():
		return
	var T: Dictionary = _types()["tally"]["weapon"]
	var row: Dictionary = {}
	match what:
		"hit":
			if e.get("hand", false):
				row = T["set"] if e.get("stand", false) else T["hit"]
		"turn":
			if e.get("hand", false):
				row = T["turn"]
		"with":
			row = T["with"]
	if not row.is_empty():
		_feeds(String(row["line"]), float(row["by"]))

## The turn of a genius that takes no orders: it is with its partner.
func _update_typed(_dt: float) -> void:
	g_pos = p_pos
	g_order = "guard"
	var foe_up := w_state not in ["down", "absent"]
	var G: Dictionary = Data.genius()["fight"]["great"]
	# the move only the great have: a weapon's second hand, an item's wall
	if not g_great.is_empty() and now >= g_great_at and foe_up and g_will >= float(G.get("will", 18.0)) and dist() <= float(G.get("reach", 9.0)):
		_genius_great_move()
	if g_type == "weapon":
		return
	var use: Dictionary = g_item.get("use", {})
	# a door stands its time; a lamp burns its time, and what stands in a kept flame burns
	if not g_door.is_empty() and now >= float(g_door["until"]):
		g_door = {}
		_emit({ "type": "genius-door-end" })
	if not g_lamp.is_empty():
		if now >= float(g_lamp["until"]):
			g_lamp = {}
			_emit({ "type": "genius-lamp-end" })
		elif use.has("burn") and now - float(g_lamp["tick"]) >= 0.5:
			g_lamp["tick"] = now
			var d := _genius_base() * float(use["burn"]) * 0.5 * g_worth
			if foe_up and w_pos.distance_to(g_lamp["at"]) <= float(g_lamp["radius"]) + float(beast["radius"]):
				_genius_hits(d, "lamp")
			for i in foes.size():
				if (foes[i] as Foe).alive() and (foes[i] as Foe).pos.distance_to(g_lamp["at"]) <= float(g_lamp["radius"]):
					_genius_hits_other(i, d)
	# an hour-bell tolls of itself when a strike is wound up at its partner
	if use.has("auto") and now >= g_auto_at and w_state == "windup" and w_target == -1 and dist() - float(beast["radius"]) <= float(use.get("radius", 5.5)):
		g_auto_at = now + float(use["auto"]) * g_twait
		_use_toll(use, true)

# --- a companion's role: the one thing only it does

func _held() -> bool:
	return genius != null and not genius.fallen and now < g_held_until

func _role_move(o: Dictionary, at: Vector2) -> void:
	var cost := float(o.get("will", 0.0))
	g_will = maxf(0.0, g_will - cost)
	stats["g_will_spent"] += cost
	stats["g_moves"] += 1
	stats["g_own"] = int(stats.get("g_own", 0)) + 1
	g_wait[String(o["id"])] = now + float(o.get("wait", 0.0)) * g_twait
	g_move_now = String(o.get("name", ""))
	g_move_until = now + 1.6
	_emit({ "type": "genius-move", "move": String(o["id"]), "name": g_move_now, "at": at })

func _role_acts(foe_up: bool) -> void:
	# a Bulwark holds the foe: it calls it onto itself, and for a while the foe goes for it
	var k := _own("hold-it")
	if k > 0.0 and foe_up and not passive and now >= g_held_until:
		var o := _own_spec("hold-it")
		if now >= float(g_wait.get("hold-it", 0.0)) and g_will >= float(o.get("will", 0.0)) + 4.0 and g_pos.distance_to(w_pos) <= float(o.get("reach", 9.0)) and w_state in ["prowl", "approach", "windup", "recover"] and w_target != HELD:
			_role_move(o, g_pos)
			g_held_until = now + float(o.get("seconds", 5.0)) * k
			w_target = HELD
			if w_state == "prowl":
				_choose_attack()
	# a Harrier worries it: its guard is down, and every blow on it lands for more
	k = _own("worry")
	if k > 0.0 and foe_up and now >= w_open_until:
		var o2 := _own_spec("worry")
		if now >= float(g_wait.get("worry", 0.0)) and g_will >= float(o2.get("will", 0.0)) and g_pos.distance_to(w_pos) - float(beast["radius"]) <= float(o2.get("reach", 2.6)) and w_state not in ["stagger", "pinned"]:
			_role_move(o2, w_pos)
			w_open_until = now + float(o2.get("seconds", 2.0)) * k
			w_exposed_until = w_open_until
			w_exposed = float(o2.get("exposed", 1.0))
	# a Keeper mends: its partner, or whoever of the party is worst hurt
	k = _own("mend")
	if k > 0.0 and now >= g_mend_at:
		var o3 := _own_spec("mend")
		if g_will >= float(o3.get("will", 0.0)) + 1.0:
			var below := float(o3.get("below", 0.7))
			var reach := float(o3.get("reach", 5.0))
			var hp_max := float(room["player"]["health"])
			var who := -9
			var worst := below
			if p_state != "down" and p_hp / hp_max < worst and now - p_struck_at >= float(o3.get("after", 2.5)) and g_pos.distance_to(p_pos) <= reach:
				who = -1
				worst = p_hp / hp_max
			for i in allies.size():
				var al: Dictionary = allies[i]
				if not al["down"] and float(al["hp"]) / float(al["hp_max"]) < worst and (al["pos"] as Vector2).distance_to(g_pos) <= reach:
					who = i
					worst = float(al["hp"]) / float(al["hp_max"])
			if who != -9:
				var amount := float(o3.get("health", 5.0)) * k
				var cost := float(o3.get("will", 0.0))
				g_will = maxf(0.0, g_will - cost)
				stats["g_will_spent"] += cost
				stats["g_own"] = int(stats.get("g_own", 0)) + 1
				stats["g_mended"] = float(stats.get("g_mended", 0.0)) + amount
				g_mend_at = now + float(o3.get("every", 2.0))
				g_move_now = String(o3.get("name", "Mends"))
				g_move_until = now + 1.0
				if who == -1:
					p_hp = minf(hp_max, p_hp + amount)
				else:
					allies[who]["hp"] = minf(float(allies[who]["hp_max"]), float(allies[who]["hp"]) + amount)
				_emit({ "type": "genius-mend", "amount": amount, "who": who })

## The strike a Bulwark called onto itself lands on it, out of its Will.
func _genius_held_blow(dmg: float) -> void:
	var o := _own_spec("hold-it")
	var spent := dmg * float(o.get("takes", 0.45))
	var braced := not _genius_has("brace").is_empty()
	g_will = maxf(1.0 if braced else 0.0, g_will - spent)
	stats["g_will_spent"] += spent
	stats["g_guards"] += 1
	g_regen_from = now + float(Data.genius()["will"]["regenDelayAfterHit"])
	_emit({ "type": "genius-held-blow", "damage": dmg, "at": g_pos })
	if g_will <= 0.0:
		_genius_fall()

## The locked foe has struck at the hero and begins to recover: a Lookout calls the opening.
func _foe_recovers() -> void:
	var k := _own("calls")
	if k <= 0.0:
		return
	var o := _own_spec("calls")
	if g_pos.distance_to(p_pos) > float(o.get("reach", 14.0)):
		return
	g_opening_until = now + w_duration
	g_opening = 1.0 + (float(o.get("mark", 1.2)) - 1.0) * k
	stats["g_own"] = int(stats.get("g_own", 0)) + 1
	_emit({ "type": "genius-move", "move": "calls", "name": "Now", "at": w_pos })

## Another foe stands under the lock (the next of the pack, or one come back): what was done
## to the last is not on it. An astrolabe that keeps its measures keeps them by kind of beast.
func _foe_changed(was: String) -> void:
	w_open_until = -9.0
	w_exposed_until = -9.0
	w_weak_until = -9.0
	g_opening_until = -9.0
	g_sight_until = -9.0
	g_held_until = -9.0
	var ms: Dictionary = g_item.get("always", {}).get("measure", {})
	if not ms.is_empty():
		var keeps: bool = ms.get("keeps", false)
		if keeps:
			g_measures[was] = maxi(int(g_measures.get(was, 0)), g_measure)
		g_measure = int(g_measures.get(String(beast.get("id", "")), 0)) if keeps else 0

func dist() -> float:
	return p_pos.distance_to(w_pos)

## Bloods with a sense for the break need one fewer.
func breaks_needed() -> int:
	return int(room["break"]["needed"]) - (1 if bc.get("breakSense", false) else 0)

## A person to spar with, as a beast the fight can run: the "student" template from
## data/beasts.json, named and Shaped for the classmate, scaled for the ladder's rung.
static func student_beast(c: Dictionary, scale := 1.0) -> Dictionary:
	var b: Dictionary = Data.beast("student").duplicate(true)
	b["name"] = c.get("name", "Student")
	b["shape"] = c.get("shape", "anchor")
	b["health"] = roundf(float(b["health"]) * scale)
	b["person"] = { "body": c.get("body", "Knight"), "weapon": c.get("weapon", "saber"), "name": c.get("name", ""), "look": c.get("look", {}) }
	# What their city's school taught them, if they have a city.
	var disc: String = c.get("discipline", Creation.discipline_of(c.get("city", "")))
	for a in Data.discipline_kits.get(disc, {}).get("studentAttacks", []):
		b["attacks"].append(a.duplicate(true))
	b["title"] = c.get("title", "of the cohort")
	# Their Pattern: their Shape's first Form, one Trigger (data/academy.json, cohort.patterns).
	if b.has("pattern") and c.has("shape") and Data.kits.has(c["shape"]):
		var forms: Dictionary = Data.kits[c["shape"]]["forms"]
		var fid: String = forms.keys()[0]
		b["pattern"]["id"] = "pattern"
		b["pattern"]["name"] = forms[fid]["name"]
		b["pattern"]["form"] = fid
		b["pattern"]["terms"] = [Data.academy.get("cohort", {}).get("patterns", {}).get("trigger", "below-half")]
		b["pattern"]["weight"] = 0
	return b

## The Anchor the room started with, for the tests and the practice yard.
static func default_hero() -> Dictionary:
	return { "name": "Anchor", "shape": "anchor", "weapon": "saber", "blood": "", "city": "columbia", "body": "alexandria-m",
		"pattern": Data.room["pattern"]["default"] }

func breaks_beast() -> bool:
	return Data.opposite(player_shape) == w_shape

## Can the Pattern fire now (every Trigger met)? Bars are checked when it is pressed.
func pattern_ready() -> bool:
	if pattern_lost or p_state == "pattern" or p_state == "down" or w_state in ["down", "absent"]:
		return false
	return PatternTerms.unmet_trigger(self, pattern["terms"]) == ""

func pattern_form() -> Dictionary:
	if kit["forms"].has(pattern["form"]):
		return kit["forms"][pattern["form"]]
	return room["pattern"]["forms"][pattern["form"]]

func _b(key: String, default_value: float) -> float:
	return float(bc.get(key, default_value))

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
	if not allowed.is_empty() and action not in allowed:
		return
	# The genius's key means what its type means (docs/genius-types.md): a companion's orders,
	# a weapon taken in hand or let go, an item used. A companion's order is never kept waiting.
	if action == "order" and (not genius or g_type == "companion"):
		if genius:
			genius.order = genius.next_order()
			if genius.order == "hold":
				g_hold_at = g_post if g_post != Vector2.INF else p_pos
			if genius.order == "free":
				g_think_at = now
				g_free_why = ""
			_emit({ "type": "order", "order": genius.order })
		return
	# Pressed a little early (mid-swing, mid-dodge, mid-flinch): remember it briefly and fire
	# it the moment it is allowed, so no press is lost.
	if action in ["attack", "technique", "dodge", "pattern", "block-down", "tech1", "tech2", "tech3", "order"] and _busy(action):
		p_queued = action
		p_queued_until = now + float(room.get("inputBufferSeconds", 0.25))
		if action == "block-down":
			p_block_held = true
		return
	match action:
		"order": _genius_key_pressed()
		"attack": _press_attack()
		"attack-up":
			if p_state == "draw":
				_loose()
		"reload":
			if ranged and p_ammo_max > 0 and p_ammo < p_ammo_max and (p_state == "free" or (p_state == "attack" and _can_start_action())):
				_start_reload()
		"technique": _press_technique(tech)
		"tech1", "tech2", "tech3":
			var i := int(action.substr(4)) - 1
			if i < extra_techs.size():
				_press_technique(extra_techs[i])
		"dodge": _press_dodge()
		"block-down":
			p_block_held = true
			# A block cancels the end of a swing, as a dodge does; it cancels a reload or a draw too.
			# Twin blades (quickGuard) can drop any swing for the guard.
			if p_state == "attack" and (_can_start_action() or style.get("quickGuard", false)):
				p_state = "free"
				p_last_attack_end = now
			if p_state in ["reload", "draw"]:
				p_state = "free"
			if p_state == "free" and not p_fainted:
				# on ground its genius has lit, a wind-up is read sooner: the moment is longer; and
				# longer or shorter for what its genius is (a sure hand, a lookout, a blade with no guard)
				p_parry_until = now + float(room["parry"]["window"]) * float(style.get("guard", 1.0)) * (g_lit if now < g_lit_until else 1.0) * _parry_k()
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
				if bc.get("shoutStagger", false) and not w_shouted and w_state in ["windup", "approach", "prowl"]:
					w_shouted = true
					_wolf_set("flinch", 0.8)
					_emit({ "type": "hesitates" })
		"lock":
			# Lock on; locked already with a pack about, pass the lock to the next of them.
			var live: Array = []
			for i in foes.size():
				if (foes[i] as Foe).alive():
					live.append(i)
			if p_lock and not live.is_empty():
				swap_target(live[0])
			else:
				p_lock = not p_lock

func _busy(action: String) -> bool:
	if action == "order":
		return _key_busy()
	match p_state:
		"free":
			return action == "dodge" and now < p_dodge_ready_at
		"attack":
			# Attack presses chain into the combo; everything else waits for the recovery.
			if ranged:
				return not _can_start_action()
			if action == "block-down" and style.get("quickGuard", false):
				return false
			return action != "attack" and not _can_start_action()
		"pattern":
			return action != "attack"
		"technique", "dodge", "flinch":
			return true
		"reload":
			# A dodge or a block cancels the reload; the rest waits.
			return action not in ["dodge", "block-down"]
		"draw":
			return action not in ["dodge", "block-down", "attack"]
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
		var s: Dictionary = combo[p_combo]
		# A shot has no active window: it can be cancelled once it has fired.
		return p_timer >= _startup(s) + float(s.get("active", 0.0))
	return false

func _press_attack() -> void:
	if p_state == "pattern":
		_pattern_press()
		return
	# A weapon genius with too little Will left for a blow leaves the hand of itself, and the
	# press goes to the weapon that was put away.
	if g_in_hand and not _hand_can_strike() and (p_state == "free" or (p_state == "attack" and _can_start_action())):
		_let_go(true)
	if ranged:
		if style.has("draw"):
			if p_state == "free" or (p_state == "attack" and _can_start_action()):
				p_state = "draw"
				p_timer = 0.0
				p_draw = 0.0
				p_draw_k = _hand_cut_begins(true)
				_face_target_if_near()
				_emit({ "type": "draw-start" })
				_emit({ "type": "anim", "who": "player", "name": "2H_Ranged_Aiming", "speed": 1.0 })
			return
		if p_ammo_max > 0 and p_ammo <= 0:
			if p_state == "free" or (p_state == "attack" and _can_start_action()):
				_start_reload()
			return
		if p_state == "free" or (p_state == "attack" and _can_start_action()):
			_start_swing(0)
		elif p_state == "attack":
			p_buffer = true
		return
	if p_state == "attack":
		var s: Dictionary = combo[p_combo]
		if p_timer < _startup(s) + float(s["active"]):
			p_buffer = true
			return
		if p_combo < combo.size() - 1:
			_start_swing(p_combo + 1)
		return
	if p_state != "free":
		return
	var next := 0
	if now - p_last_attack_end <= float(room["comboBufferSeconds"]) and p_combo < combo.size() - 1:
		next = p_combo + 1
	_start_swing(next)

## The bow looses at the draw it has: a full draw hits for the shot's full damage, a snap shot for its least.
func _loose() -> void:
	p_charge = clampf(p_draw / draw_seconds(), 0.0, 1.0)
	p_state = "free"
	_start_swing(0)
	_emit({ "type": "draw-release", "charge": p_charge })

func _start_reload() -> void:
	var r: Dictionary = style["reload"]
	p_state = "reload"
	p_timer = 0.0
	p_reload_t = float(r["seconds"])
	_emit({ "type": "reload", "seconds": p_reload_t })
	_emit({ "type": "anim", "who": "player", "name": String(r.get("anim", "1H_Ranged_Reload")), "duration": p_reload_t })

## What a shot does, by the draw (a bow) or as written.
func _shot_damage(s: Dictionary) -> float:
	if style.has("draw"):
		var d: Dictionary = style["draw"]
		return roundf(lerpf(float(d["min"]), float(d["max"]), p_charge))
	return float(s["damage"])

func _start_swing(i: int) -> void:
	p_state = "attack"
	p_timer = 0.0
	p_combo = i
	p_buffer = false
	p_hit_done = false
	_face_target_if_near()
	stats["attacks"] += 1
	if ranged and p_ammo_max > 0:
		p_ammo -= 1
		stats["shots"] = int(stats.get("shots", 0)) + 1
	p_startup_k = 1.0
	if g_in_hand:
		_hand_swing_starts()
	var sw: Dictionary = combo[i]
	_emit({ "type": "anim", "who": "player", "name": sw["anim"], "duration": _startup(sw) + float(sw.get("active", 0.0)) + float(sw["recovery"]) })

## Swings go toward the wolf when locked on; unlocked, toward whichever foe is close, of the
## pack or the locked one; otherwise where you steer.
func _face_target_if_near() -> void:
	var wolf_there := w_state != "down" and w_state != "absent"
	if wolf_there and p_lock:
		p_facing = _angle_to(p_pos, w_pos)
		return
	var best_d := 3.0
	var best := Vector2.INF
	if wolf_there and dist() < best_d:
		best_d = dist()
		best = w_pos
	for fo in foes:
		if (fo as Foe).alive() and (fo as Foe).pos.distance_to(p_pos) < best_d:
			best_d = (fo as Foe).pos.distance_to(p_pos)
			best = (fo as Foe).pos
	if best != Vector2.INF:
		p_facing = _angle_to(p_pos, best)
	elif p_dodge_dir.length() > 0.3:
		p_facing = p_dodge_dir.angle()

func _press_technique(t: Dictionary) -> void:
	var id: String = t["id"]
	if not _can_start_action():
		return
	if now < float(p_cooldowns.get(id, 0.0)):
		_emit({ "type": "not-ready", "what": t["name"] })
		return
	var cost := float(t["will"]) * (2.0 if p_double_cost > 0 else 1.0) * _b("techniqueCost", 1.0)
	if p_fainted or p_will < cost:
		_emit({ "type": "no-will" })
		return
	p_will -= cost
	p_double_cost = maxi(0, p_double_cost - 1)
	p_cooldowns[id] = now + float(t["cooldown"]) * grade_of(id).get("cooldown", 1.0)
	p_state = "technique"
	p_technique = id
	p_tech_active = t
	p_timer = 0.0
	p_hit_done = false
	_face_target_if_near()
	_emit({ "type": "anim", "who": "player", "name": t["anim"], "duration": float(t["startup"]) + float(t["active"]) + float(t["recovery"]) })
	_emit({ "type": "technique", "id": id, "effect": t["effect"], "dist": dist() })

func _press_dodge() -> void:
	var d: Dictionary = room["dodge"]
	if now < p_dodge_ready_at or not (p_state == "free" or p_state in ["reload", "draw"] or _can_start_action()):
		return
	var dcost := float(d["will"]) * _b("dodgeCost", 1.0) * (float(kit["stance"].get("dodgeCost", 1.0)) if p_stance else 1.0) * _always_k("dodge", "will")
	if p_fainted or p_will < dcost:
		_emit({ "type": "no-will" })
		return
	p_will -= dcost
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
		if now > breach_armed_until or not allow_breach:
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
	chain = { "cues": cues, "next": 0, "hit": 0, "period": period, "window": float(P["cueWindowMs"]) / 1000.0 * _always_k("chain"),
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
				p_hp = minf(float(room["player"]["health"]), p_hp + float(form["base"]) * _b("healFactor", 1.0))
				_emit({ "type": "mend", "amount": float(form["base"]) })
		_emit({ "type": "pattern-cue", "k": i, "hit": true, "offset_ms": off * 1000.0 })
		_emit({ "type": "anim", "who": "player", "name": combo[i % combo.size()]["anim"], "speed": 1.6 })
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
				var heal := roundf(pay * float(form.get("healFactor", 1.0)) * _b("healFactor", 1.0))
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
	_update_wolf(dt * _wolf_time_scale())
	_update_others(dt * _wolf_time_scale())
	_retarget_if_down()
	_update_burn(dt)
	_update_genius(dt)
	_update_allies(dt)
	_update_project(dt)
	_separate()
	for o in obstacles:
		var c := Vector2(o.x, o.y)
		var d := p_pos - c
		var m: float = o.z + float(room["player"]["radius"])
		if d.length() < m:
			p_pos = c + (d.normalized() if d.length() > 1e-4 else Vector2.RIGHT) * m

## The Shapes that slow the world: Read's stance, Bind's stance near you, Bind's Leash.
func _wolf_time_scale() -> float:
	var k := 1.0
	if now < w_slow_until:
		k *= w_slow
	if p_stance:
		match kit["stance"]["effect"]:
			"slow-world": k *= float(kit["stance"]["factor"])
			"slow-near":
				if dist() < float(kit["stance"]["radius"]): k *= float(kit["stance"]["factor"])
	return k

func _update_burn(dt: float) -> void:
	if now >= w_burn_until or w_state in ["down", "absent"]:
		return
	w_burn_tick += dt
	if w_burn_tick >= 0.5:
		w_burn_tick = 0.0
		w_hp = maxf(w_floor, w_hp - 2.0)
		stats["damage_dealt"] += 2
		_emit({ "type": "burn-tick", "damage": 2 })
		if w_hp == 0.0:
			stats["wolves_down"] += 1
			_wolf_set("down", float(beast["respawnSeconds"]))
			_emit({ "type": "wolf-down" })
			_emit({ "type": "anim", "who": "wolf", "name": "Death", "speed": 1.0 })

func _update_will(dt: float) -> void:
	if p_state == "down":
		return
	var F: Dictionary = rules["field"]
	var blocking := _blocking()
	var dw := 0.0
	if p_stance: dw -= float(room["stance"]["willPerSecond"])
	var regen_factor := _b("willRegen", 1.0) * _lamp_k("willRegen", p_pos)
	if blocking: dw -= float(room["block"]["willPerSecond"])
	if not p_stance and not blocking and p_state != "pattern": dw += float(F["regenOpen"]) * (0.5 if p_leaking else 1.0) * regen_factor
	if _b("regenHealth", 0.0) > 0.0 and p_hp > 0.0:
		p_hp = minf(float(room["player"]["health"]), p_hp + _b("regenHealth", 0.0) * dt)
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
			if p_stance: speed *= float(kit["stance"].get("move", P["stanceMoveFactor"] if kit["stance"]["effect"] == "power" else 1.0))
			if now < p_haste_until:
				speed *= p_haste
			var target_vel := move.limit_length(1.0) * speed
			var accel := float(P.get("acceleration", 20.0))
			p_vel = p_vel.move_toward(target_vel, accel * speed * dt)
			p_pos = _clamp_in(p_pos + p_vel * dt)
			if p_vel.length() > 0.4:
				p_moved_at = now
			var want := p_facing
			if p_lock and w_state != "down" and w_state != "absent":
				want = _angle_to(p_pos, w_pos)
			elif move.length() > 0.05:
				want = move.angle()
			p_facing = lerp_angle(p_facing, want, 1.0 - exp(-float(P["turnSpeed"]) * dt))
		"draw":
			p_draw += dt
			var d: Dictionary = style["draw"]
			if p_lock and w_state not in ["down", "absent"]:
				p_facing = lerp_angle(p_facing, _angle_to(p_pos, w_pos), 1.0 - exp(-8.0 * dt))
			elif move.length() > 0.05:
				p_facing = lerp_angle(p_facing, move.angle(), 1.0 - exp(-4.0 * dt))
			# Drawn, you walk; the bow looses on its own a little past full draw.
			var speed_d := float(P["runSpeed"]) * 0.45
			p_pos = _clamp_in(p_pos + move * speed_d * dt)
			if p_draw >= draw_seconds() + float(d.get("holdAfter", 0.5)):
				_loose()
		"reload":
			if p_timer >= p_reload_t:
				p_ammo = p_ammo_max
				p_state = "free"
				_emit({ "type": "reloaded" })
		"attack":
			var s: Dictionary = combo[p_combo]
			var st := _startup(s)
			var ac := float(s.get("active", 0.0))
			if not ranged and p_timer < st + ac and dist() > float(P["radius"]) + float(beast["radius"]) + 0.3:
				p_pos = _clamp_in(p_pos + Vector2.from_angle(p_facing) * float(s["lunge"]) / (st + ac) * dt)
			if not p_hit_done and p_timer >= st:
				p_hit_done = true
				# a weapon genius in the hand adds what its path gives it to the blow
				var hk := _hand_blow() if g_in_hand else 1.0
				var hp_before := w_hp
				var hits_before: int = stats["hits"]
				var winding := w_state == "windup"
				if ranged and style.get("cone", false):
					# Scatter: everything in the cone takes it, and is thrown back.
					_emit({ "type": "shot", "from": p_pos, "to": p_pos + Vector2.from_angle(p_facing) * float(s["range"]), "hit": true, "cone": true })
					_resolve_swing(_shot_damage(s) * hk, float(s["range"]), float(s["arc"]), false, float(s.get("knockback", 0.0)))
				elif ranged:
					_resolve_shot(_shot_damage(s) * hk, float(s["range"]), float(s["arc"]))
				else:
					var kb := float(s.get("knockback", 0.0))
					_resolve_swing(float(s["damage"]) * hk, float(s["reach"]), float(s["arc"]), s.get("breaks", false), kb)
					if s.has("burnSeconds") and w_state not in ["down", "absent"] and _in_arc(p_pos, p_facing, w_pos, float(s["reach"]) + float(beast["radius"]), float(s["arc"])):
						w_burn_until = maxf(w_burn_until, now) + float(s["burnSeconds"])
				if g_in_hand:
					_hand_blow_done(int(stats["hits"]) > hits_before, w_hp < hp_before, winding)
			if p_buffer and p_timer >= st + ac and (ranged or p_combo < combo.size() - 1):
				_start_swing(0 if ranged else p_combo + 1)
			elif p_timer >= st + ac + float(s["recovery"]):
				p_state = "free"
				p_last_attack_end = now
		"technique":
			var t := p_tech_active if not p_tech_active.is_empty() else tech
			if t["effect"] == "dash" and p_timer < float(t["startup"]) + float(t["active"]) and w_state not in ["down", "absent"]:
				# Closing Strike: the field throws you at the foe.
				if dist() > float(t["reach"]) * 0.7:
					p_facing = _angle_to(p_pos, w_pos)
					p_pos = _clamp_in(p_pos + Vector2.from_angle(p_facing) * float(t["dash"]) / (float(t["startup"]) + float(t["active"])) * dt)
			if not p_hit_done and p_timer >= float(t["startup"]):
				p_hit_done = true
				_resolve_technique(t)
			if p_timer >= float(t["startup"]) + float(t["active"]) + float(t["recovery"]):
				p_state = "free"
		"dodge":
			var d: Dictionary = room["dodge"]
			var dur := float(d["duration"])
			var k := clampf(1.0 - p_timer / dur, 0.0, 1.0)
			if p_slip.is_empty():
				p_pos = _clamp_in(p_pos + p_dodge_dir * float(d["distance"]) * _b("dodgeDistance", 1.0) / dur * 1.6 * k * dt)
			else:
				p_pos = _clamp_in(p_pos + (p_slip["dir"] as Vector2) * float(d["distance"]) * float(p_slip["distance"]) / dur * 1.6 * k * dt)
			p_moved_at = now
			if p_timer >= dur:
				p_state = "free"
				if p_slip.is_empty():
					p_dodge_ready_at = now + float(d["cooldown"])
				p_slip = {}
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

## The field past the skin: a Projected field (Stage 3) puts more into every technique and
## reaches farther with it (rules.json: field.stageOutput, stageReach).
## A technique's grade by how often this hero has used it (data/academy.json, mastery).
func grade_of(id: String) -> Dictionary:
	var grades: Array = Data.academy.get("mastery", {}).get("grades", [])
	var uses := int(hero.get("technique_use", {}).get(id, 0))
	var out: Dictionary = { "id": "learned", "name": "learned", "damage": 1.0, "cooldown": 1.0 }
	for g in grades:
		if uses >= int(g["uses"]):
			out = g
	return out

func staged(t: Dictionary) -> Dictionary:
	var out := t.duplicate()
	var g := grade_of(String(t.get("id", "")))
	if out.has("damage"): out["damage"] = roundf(float(out["damage"]) * float(g.get("damage", 1.0)))
	if not p_field_open:
		return out
	var outs: Array = rules["field"]["stageOutput"]
	var f := float(outs[2]) / float(outs[1])
	if out.has("damage"): out["damage"] = roundf(float(out["damage"]) * f)
	if out.has("reach"): out["reach"] = float(out["reach"]) + 1.0
	if out.has("range"): out["range"] = float(out["range"]) + 2.0
	return out

## The Project drill: the stance held with the field full opens it past the skin.
func _update_project(dt: float) -> void:
	if p_field_open or not project_training:
		return
	if p_stance and p_will >= 60.0:
		p_project_t += dt
		if p_project_t >= 3.0:
			p_field_open = true
			_emit({ "type": "field-open" })
	else:
		p_project_t = maxf(0.0, p_project_t - dt * 2.0)

## The Shape's technique lands. Every technique breaks a beast of the opposite Shape.
func _resolve_technique(t0: Dictionary) -> void:
	var t := staged(t0)
	match t["effect"]:
		"heavy":
			_resolve_swing(float(t["damage"]), float(t["reach"]), float(t["arc"]), true, float(t.get("knockback", 0.0)))
			_emit({ "type": "quake", "at": p_pos + Vector2.from_angle(p_facing) * 1.2 })
		"burst":
			if _resolve_swing(float(t["damage"]), float(t["reach"]), float(t["arc"]), true, 0.0):
				w_burn_until = maxf(w_burn_until, now + float(t["burnSeconds"]))
			_emit({ "type": "burst", "at": p_pos + Vector2.from_angle(p_facing) * 1.4 })
		"dash":
			_resolve_swing(float(t["damage"]), float(t["reach"]), float(t["arc"]), true, 0.0)
		"bolt-crit":
			if _resolve_shot(float(t["damage"]), float(t["range"]), 40.0, true):
				crit_until = now + float(t["critSeconds"])
				_emit({ "type": "crit-open", "seconds": float(t["critSeconds"]) })
		"tether":
			if _resolve_shot(float(t["damage"]), float(t["range"]), 40.0, true):
				w_slow_until = now + float(t["slowSeconds"])
				w_slow = float(t["slow"])
				_emit({ "type": "tether", "seconds": float(t["slowSeconds"]) })
		"ward":
			ward_until = now + float(t["wardSeconds"])
			_emit({ "type": "ward-up", "at": p_pos, "seconds": float(t["wardSeconds"]) })
			_resolve_swing(float(t["damage"]), float(t["reach"]), float(t["arc"]), true, 0.0)
		# The Disciplines' techniques.
		"volley":
			for i in int(t.get("shots", 3)):
				_resolve_shot(float(t["damage"]), float(t["range"]), 50.0, i == 0)
		"mark":
			if w_state not in ["down", "absent"] and dist() <= float(t["range"]):
				w_mark_until = now + float(t["markSeconds"])
				w_mark_factor = float(t["markFactor"])
				w_named = true
				_emit({ "type": "marked", "seconds": float(t["markSeconds"]) })
		"finisher":
			var finish := w_state == "stagger" or w_hp <= float(beast["health"]) * float(t.get("finishBelow", 0.3))
			_resolve_shot(float(t["damage"]) * (float(t.get("finishFactor", 2.0)) if finish else 1.0), float(t["range"]), 40.0, true)
		"sound":
			if w_state not in ["down", "absent"] and dist() <= float(t["range"]):
				w_slow_until = now + float(t["slowSeconds"])
				w_slow = float(t["slow"])
				_emit({ "type": "sounded", "seconds": float(t["slowSeconds"]) })
		"pull":
			if _resolve_shot(float(t["damage"]), float(t["range"]), 40.0, true) and w_state not in ["down", "absent"]:
				var dir := (w_pos - p_pos).normalized()
				w_pos = _clamp_in(p_pos + dir * float(t["pullTo"]))
				if w_state in ["prowl", "approach", "idle", "recover"]:
					_wolf_set("flinch", float(beast["flinchTime"]) * 1.5)
				_emit({ "type": "pulled" })
		"quake":
			if _resolve_swing(float(t["damage"]), float(t["reach"]), float(t["arc"]), true, float(t.get("knockback", 0.0))) and breaks_beast():
				w_break += int(t.get("breakPlus", 0))
			_emit({ "type": "quake", "at": p_pos })

## A shot: straight at the foe if it is in range and roughly in front.
func _resolve_shot(damage: float, rng_m: float, arc: float, breaks := false) -> bool:
	if w_state not in ["down", "absent"] and (p_lock or dist() < rng_m):
		p_facing = _angle_to(p_pos, w_pos)
	var to := p_pos + Vector2.from_angle(p_facing) * rng_m
	var hit := w_state not in ["down", "absent"] and _in_arc(p_pos, p_facing, w_pos, rng_m + float(beast["radius"]), arc)
	if hit:
		to = w_pos
	_emit({ "type": "shot", "from": p_pos, "to": to, "hit": hit })
	if not hit:
		_emit({ "type": "whiff" })
		return false
	_resolve_swing(damage, rng_m + 1.0, 360.0, breaks, 0.0)
	return true

func p_invulnerable() -> bool:
	if p_state != "dodge":
		return false
	# the coat's slip is untouchable from its first moment
	if not p_slip.is_empty():
		return p_timer <= float(p_slip["iframes"])
	var d: Dictionary = room["dodge"]
	return p_timer >= float(d["iframeStart"]) and p_timer <= float(d["iframeEnd"]) + _always_add("dodge", "iframes")

func _resolve_swing(damage: float, reach: float, arc: float, breaks: bool, knockback: float) -> bool:
	damage *= gear_damage
	var heavy := breaks or knockback > 0.0
	if p_stance:
		match kit["stance"]["effect"]:
			"power": damage *= float(kit["stance"]["damage"])
			"blade": damage += float(kit["stance"]["extraDamage"])
			"burn": w_burn_until = maxf(w_burn_until, now) + float(kit["stance"]["burnSeconds"])
	if p_disarmed and not breaks: damage *= 0.4
	# The rest of the pack, in the arc, take the swing too.
	var any_other := false
	for i in foes.size():
		var fo: Foe = foes[i]
		if fo.alive() and _in_arc(p_pos, p_facing, fo.pos, reach + float(fo.beast["radius"]), arc):
			_damage_other(i, roundf(damage), heavy)
			if knockback > 0.0 and fo.alive():
				fo.pos = _clamp_in(fo.pos + (fo.pos - p_pos).normalized() * knockback)
			any_other = true
	if w_state in ["down", "absent"] or not _in_arc(p_pos, p_facing, w_pos, reach + float(beast["radius"]), arc):
		if not any_other:
			_emit({ "type": "whiff" })
		return any_other
	_damage_wolf(roundf(damage), false, heavy)
	if knockback > 0.0 and w_state not in ["down", "pinned"]:
		w_pos = _clamp_in(w_pos + (w_pos - p_pos).normalized() * knockback)
	if breaks and breaks_beast() and w_state != "stagger" and w_state != "down":
		w_break += 1
		stats["breaks"] += 1
		_emit({ "type": "break", "count": w_break, "needed": breaks_needed() })
		if w_break >= breaks_needed():
			w_break = 0
			stats["staggers"] += 1
			_wolf_set("stagger", float(room["break"]["staggerSeconds"]))
			_emit({ "type": "stagger", "seconds": float(room["break"]["staggerSeconds"]), "cause": "break" })
	return true

## An elite's guard: a blow out of turn lands for a fraction. The guard is down while the beast
## is staggered and while it recovers from its own strike (data/combat-room.json, guard.open),
## and a Pattern goes through.
func _guarded(dmg: float, from_pattern := false) -> float:
	if from_pattern or not beast.has("guard") or guard_open():
		return dmg
	return roundf(dmg * minf(1.0, float(beast["guard"]) * _lamp_k("found", w_pos)))

## Is a guarded beast open now? (Always true of a beast with no guard.)
func guard_open() -> bool:
	return not beast.has("guard") or now < w_open_until or (room.get("guard", {}).get("open", ["stagger"]) as Array).has(w_state)

func _damage_wolf(dmg: float, from_pattern: bool, heavy: bool) -> void:
	dmg = _guarded(dmg, from_pattern)
	if w_state in ["down", "absent"]:
		return
	if w_state == "stagger":
		dmg = roundf(dmg * float(room["break"]["staggerDamageFactor"]))
	var crit := now < crit_until and not from_pattern
	if crit:
		dmg = roundf(dmg * float(tech.get("crit", 1.5)))
	if now < w_mark_until:
		dmg = roundf(dmg * w_mark_factor)
	if not from_pattern:
		dmg = roundf(dmg * _typed_blow_k())
	w_hp = maxf(w_floor, w_hp - dmg)
	stats["hits"] += 1
	stats["damage_dealt"] += dmg
	if g_in_hand and p_state == "attack":
		stats["hand_hits"] = int(stats.get("hand_hits", 0)) + 1
		stats["hand_damage"] = float(stats.get("hand_damage", 0.0)) + dmg
	p_combo_count += 1
	stats["longest_combo"] = maxi(stats["longest_combo"], p_combo_count)
	_emit({ "type": "hit", "damage": dmg, "pattern": from_pattern, "heavy": heavy, "staggered": w_state == "stagger", "combo": p_combo, "crit": crit, "dist": dist(), "technique": p_state == "technique", "hand": g_in_hand and p_state == "attack", "stand": _stands() })
	_genius_after_hit(dmg, from_pattern)
	if gear_trait.has("willOnHit"):
		p_will = minf(float(rules["field"]["willMax"]), p_will + float(gear_trait["willOnHit"]))
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
	# A second-molt beast reads the stance: held in it, you are countered a hit sooner.
	if beast.get("readsStance", false) and p_stance and counter > 1:
		counter -= 1
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
	w_shouted = false
	w_burn_until = -9.0
	w_slow_until = -9.0
	w_mark_until = -9.0
	w_pattern_hits = 0
	w_pattern_used = false
	p_struck_this_foe = false
	_foe_changed(String(beast.get("id", "")))
	_wolf_prowl()

func _wolf_set(state: String, duration: float) -> void:
	w_state = state
	w_timer = 0.0
	w_duration = duration
	# a Hunter comes at once when the foe staggers
	if state == "stagger" and _own("opening") > 0.0:
		g_hunt_at = minf(g_hunt_at, now)

func _wolf_prowl() -> void:
	var pr: Dictionary = beast["prowl"]
	_wolf_set("idle" if passive else "prowl", rng.randf_range(float(pr["min"]), float(pr["max"])))
	w_dir = -1.0 if rng.randf() < 0.5 else 1.0

## The tutorial asks the yard-wolf to attack now.
func provoke() -> void:
	if w_state in ["idle", "prowl"]:
		_choose_attack()

## Where the foe is going: the hero, or the ally it has chosen.
func _tpos() -> Vector2:
	if w_target >= 0 and w_target < allies.size() and not allies[w_target]["down"]:
		return allies[w_target]["pos"]
	# held by a Bulwark, it goes for the genius
	if w_target == HELD and _held():
		return g_pos
	return p_pos

func _tdist() -> float:
	return w_pos.distance_to(_tpos())

func _choose_attack() -> void:
	# Now and then it goes for someone else in the party.
	w_target = -1
	var standing: Array = []
	for i in allies.size():
		if not allies[i]["down"]:
			standing.append(i)
	if not standing.is_empty() and rng.randf() < 0.35:
		w_target = standing[rng.randi() % standing.size()]
	if _held():
		w_target = HELD
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
	# a Bulwark's hold has ended (or it has fallen): the foe is after its partner again
	if w_target == HELD and not _held():
		w_target = -1
	match w_state:
		"absent":
			return
		"idle":
			if dist() > 2.6:
				_wolf_step_toward(p_pos, float(b["walkSpeed"]) * dt)
			w_facing = lerp_angle(w_facing, _angle_to(w_pos, p_pos), 1.0 - exp(-8.0 * dt))
		"prowl":
			# A classmate below half health fires their Pattern, once: a heavier blow, witnessed.
			if b.has("pattern") and not w_pattern_used and w_hp <= float(b["health"]) * 0.5:
				w_pattern_used = true
				w_target = -1
				w_attack = b["pattern"]
				_wolf_set("approach", 6.0)
				_emit({ "type": "foe-pattern", "name": b["pattern"]["name"], "form": b["pattern"]["form"], "terms": b["pattern"]["terms"] })
				return
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
			if _tdist() > rng_a * 0.85:
				_wolf_step_toward(_tpos(), float(b["gallopSpeed"]) * dt)
				w_facing = _angle_to(w_pos, _tpos())
			else:
				_wolf_set("windup", float(w_attack["windup"]))
				w_facing = _angle_to(w_pos, _tpos())
				_emit({ "type": "windup", "attack": w_attack["id"], "name": w_attack["name"], "seconds": w_duration })
			if w_timer > 6.0:
				_wolf_prowl()
		"windup":
			# Track the Anchor until the last fifth of the wind-up, then commit to the line.
			if w_timer < w_duration * 0.8:
				w_facing = lerp_angle(w_facing, _angle_to(w_pos, _tpos()), 1.0 - exp(-10.0 * dt))
			if w_timer >= w_duration:
				_wolf_set("strike", float(w_attack["active"]))
				w_hit_done = false
				_emit({ "type": "anim", "who": "wolf", "name": "Attack", "speed": 1.4, "anim": w_attack.get("anim", "") })
		"strike":
			var lunge := float(w_attack["lunge"]) / float(w_attack["active"]) * dt
			if dist() > float(room["player"]["radius"]) + float(b["radius"]):
				w_pos = _clamp_in(w_pos + Vector2.from_angle(w_facing) * lunge)
			if not w_hit_done:
				var mouth := w_pos + Vector2.from_angle(w_facing) * (float(b["radius"]) + 0.4)
				if w_target == HELD and _held() and mouth.distance_to(g_pos) <= 1.4:
					# the strike a Bulwark called onto itself lands on it
					w_hit_done = true
					_genius_held_blow(float(w_attack["damage"]))
				elif mouth.distance_to(p_pos) <= float(room["player"]["radius"]) + 1.0:
					w_hit_done = true
					_resolve_bite()
				else:
					for i in allies.size():
						if not allies[i]["down"] and mouth.distance_to(allies[i]["pos"]) <= 1.3:
							w_hit_done = true
							_hurt_ally(i, float(w_attack["damage"]) * (w_weak if now < w_weak_until else 1.0), -1)
							break
			if w_timer >= w_duration:
				if not w_hit_done and w_target != HELD:
					_emit({ "type": "evade", "how": "out of reach" })
					stats["evades"] += 1
				var struck_at_hero := w_target == -1
				_wolf_set("recover", float(w_attack["recover"]))
				if struck_at_hero:
					_foe_recovers()
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

# ===================================================================== the party

## Classmates beside you: they keep to your flanks, strike the foe when it is near, and take
## the bites meant for them. Down, they stay down until the post.
# ===================================================================== the cohort's own fighting
# A classmate beside you fights on their own (data/academy.json, cohort.fighting): they pick
# a foe (the one hunting them, else, by how much they help, the one you are locked on to,
# else the nearest), close, circle for as long as their temperament lets them, strike with
# their weapon's reach, spend Will on their Shape's technique every few strikes, fire their
# Pattern once a fight when their foe is below half, turn a bite aimed at them with a parry
# or a block by their temperament, and fall back when they are hurt.

static func make_ally(c: Dictionary, at: Vector2) -> Dictionary:
	var F: Dictionary = Data.academy["cohort"].get("fighting", {})
	var style: Dictionary = F.get("styles", {}).get(c.get("temperament", "earnest"), { "aggression": 0.5, "caution": 0.5, "parry": 0.25, "block": 0.4, "help": 0.7 })
	var wid: String = c.get("weapon", "saber")
	var wstyle := "blade"
	for w in Data.weapons:
		if w["id"] == wid:
			wstyle = w["style"]
	var weapon: Dictionary = F.get("weapons", {}).get(wstyle, { "reach": 2.0, "damage": 8, "windup": 0.28, "recover": 0.55 })
	var shape: String = c.get("shape", "anchor")
	var kit: Dictionary = Data.kits.get(shape, Data.kits["anchor"])
	var forms: Dictionary = kit["forms"]
	var fid: String = forms.keys()[0]
	return { "id": c.get("id", ""), "name": c.get("name", "Classmate"), "shape": shape, "body": c.get("body", "Knight"), "weapon": wid, "look": c.get("look", {}),
		"hp": float(F.get("health", 90)), "hp_max": float(F.get("health", 90)), "pos": at, "facing": 0.0, "down": false, "hit_at": 0.0,
		"damage": float(weapon["damage"]), "interval": 1.9, "moving": false,
		"style": style, "reach": float(weapon["reach"]), "ranged": weapon.get("ranged", false), "windup": float(weapon["windup"]), "recover": float(weapon["recover"]),
		"technique": kit["technique"], "pattern": { "name": forms[fid]["name"], "form": fid, "terms": [Data.academy.get("cohort", {}).get("patterns", {}).get("trigger", "below-half")] },
		"state": "ease", "timer": 0.0, "duration": 0.0, "target": -2, "will": float(F.get("will", 60)), "strikes": 0, "pattern_used": false,
		"side": 1.0, "retreat_until": -1.0, "next_strike_at": 0.0 }

## Where a foe is: the locked one (-1) or one of the pack; INF if it is not standing.
func _threat_pos(idx: int) -> Vector2:
	if idx == -1:
		return w_pos if w_state not in ["down", "absent"] else Vector2.INF
	if idx >= 0 and idx < foes.size() and (foes[idx] as Foe).alive():
		return (foes[idx] as Foe).pos
	return Vector2.INF

func _threat_hp_ratio(idx: int) -> float:
	if idx == -1:
		return w_hp / maxf(1.0, float(beast["health"]))
	var fo: Foe = foes[idx]
	return fo.hp / maxf(1.0, float(fo.beast["health"]))

## Is this foe winding up at this ally?
func _threat_aims_at(idx: int, ally: int) -> bool:
	if idx == -1:
		return w_state == "windup" and w_target == ally
	var fo: Foe = foes[idx]
	return fo.state == "windup" and fo.target == ally

func _ally_pick_target(i: int) -> int:
	var al: Dictionary = allies[i]
	var style: Dictionary = al["style"]
	var best := -2
	var best_score := -INF
	var idxs: Array = [-1]
	for j in foes.size():
		idxs.append(j)
	for idx in idxs:
		var tp := _threat_pos(idx)
		if tp == Vector2.INF:
			continue
		var d: float = tp.distance_to(al["pos"])
		if d > 16.0:
			continue
		var score := -d
		if _threat_aims_at(idx, i) or (idx == -1 and w_target == i) or (idx >= 0 and (foes[idx] as Foe).target == i):
			score += 8.0
		if idx == -1 and p_lock:
			score += 6.0 * float(style["help"])
		if score > best_score:
			best_score = score
			best = idx
	return best

func _update_allies(dt: float) -> void:
	var F: Dictionary = Data.academy["cohort"].get("fighting", {})
	var speed := float(F.get("speed", 5.2))
	for i in allies.size():
		var al: Dictionary = allies[i]
		if al["down"]:
			continue
		if not al.has("state"):
			continue
		al["timer"] = float(al["timer"]) + dt
		al["will"] = minf(float(F.get("will", 60)), float(al["will"]) + float(F.get("willRegen", 4.0)) * dt)
		var style: Dictionary = al["style"]
		var side := float(al["side"]) * (1.0 if i % 2 == 0 else -1.0)
		# The target: keep it while it stands, else choose.
		if _threat_pos(int(al["target"])) == Vector2.INF or (int(al["target"]) == -2):
			al["target"] = _ally_pick_target(i)
		var tgt := int(al["target"])
		var tp := _threat_pos(tgt)
		var reach := float(al["reach"])
		# Hurt past their nerve: fall back toward the hero for a while.
		var nerve := float(al["hp_max"]) * (0.15 + 0.35 * float(style["caution"]))
		if tp != Vector2.INF and float(al["hp"]) < nerve and al["state"] not in ["retreat", "pattern", "guard"] and (float(al["retreat_until"]) < 0.0 or now > float(al["retreat_until"]) + 6.0):
			al["state"] = "retreat"
			al["timer"] = 0.0
			al["retreat_until"] = now + float(F.get("retreatSeconds", 3.0))
			_emit({ "type": "ally-retreat", "who": i })
		# A bite coming at them: a parry or a block, by temperament, decided as the wind-up ends.
		if tp != Vector2.INF and _threat_aims_at(tgt, i) and al["state"] in ["approach", "circle", "recover", "ease"]:
			var left := (w_duration - w_timer) if tgt == -1 else ((foes[tgt] as Foe).duration - (foes[tgt] as Foe).timer)
			if left < 0.3:
				var r := rng.randf()
				if r < float(style["parry"]):
					al["state"] = "parry"
					al["timer"] = 0.0
				elif r < float(style["parry"]) + float(style["block"]):
					al["state"] = "block"
					al["timer"] = 0.0
		var want := Vector2.INF
		var facing_target := tp != Vector2.INF
		match String(al["state"]):
			"ease":
				# At ease: ahead of the hero on either side, never behind where the camera sits.
				want = p_pos + Vector2.from_angle(p_facing).rotated(side * 0.85) * 2.3
				facing_target = false
				if tp != Vector2.INF:
					al["state"] = "approach"
					al["timer"] = 0.0
			"approach", "circle":
				if tp == Vector2.INF:
					al["state"] = "ease"
				else:
					var standoff := reach * (0.85 if not al["ranged"] else 0.8)
					var dist_t: float = al["pos"].distance_to(tp)
					if String(al["state"]) == "approach":
						want = tp + (al["pos"] - tp).normalized() * standoff if dist_t > 0.1 else tp
						if dist_t <= standoff + 0.4:
							al["state"] = "circle"
					else:
						var ang := _angle_to(tp, al["pos"]) + side * 1.2 * dt
						want = tp + Vector2.from_angle(ang) * standoff
						if dist_t > reach * 1.6:
							al["state"] = "approach"
					if dist_t <= reach + 0.3 and now >= float(al["next_strike_at"]):
						al["strikes"] = int(al["strikes"]) + 1
						var tech: Dictionary = al["technique"]
						var use_tech: bool = int(al["strikes"]) % int(F.get("techniqueEvery", 3)) == 0 and float(al["will"]) >= float(tech.get("will", 18))
						var below_half := _threat_hp_ratio(tgt) < 0.5
						if below_half and not al["pattern_used"] and float(al["will"]) >= float(F.get("patternWill", 30)):
							al["state"] = "pattern"
							al["timer"] = 0.0
							al["duration"] = 1.1
							al["pattern_used"] = true
							al["will"] = float(al["will"]) - float(F.get("patternWill", 30))
							_emit({ "type": "ally-pattern", "who": i, "name": al["pattern"]["name"], "form": al["pattern"]["form"], "foe": tgt })
							if genius:
								genius.witness(al["pattern"])
						else:
							al["state"] = "technique" if use_tech else "windup"
							al["timer"] = 0.0
							al["duration"] = float(al["windup"]) * (1.3 if use_tech else 1.0)
							if use_tech:
								al["will"] = float(al["will"]) - float(tech.get("will", 18))
							_emit({ "type": "ally-windup", "who": i, "technique": use_tech })
						al["next_strike_at"] = now + float(al["recover"]) + lerpf(1.5, 0.35, float(style["aggression"])) * rng.randf_range(0.7, 1.3)
			"windup", "technique":
				want = al["pos"]
				if float(al["timer"]) >= float(al["duration"]):
					var tech := String(al["state"]) == "technique"
					var dmg := float(al["damage"]) * (float(F.get("techniqueDamage", 2.2)) if tech else 1.0)
					_ally_strike(i, tgt, dmg, tech)
					al["state"] = "recover"
					al["timer"] = 0.0
					al["duration"] = float(al["recover"]) * (1.4 if tech else 1.0)
			"pattern":
				want = al["pos"]
				if float(al["timer"]) >= float(al["duration"]):
					_ally_strike(i, tgt, float(al["damage"]) * float(F.get("patternDamage", 5.0)), true, true)
					al["state"] = "recover"
					al["timer"] = 0.0
					al["duration"] = 0.8
			"recover":
				want = al["pos"]
				if float(al["timer"]) >= float(al["duration"]):
					al["state"] = "approach"
					al["side"] = -1.0 if rng.randf() < 0.3 else 1.0
			"parry", "block":
				want = al["pos"]
				if float(al["timer"]) >= 0.7:
					al["state"] = "approach"
			"retreat":
				var away: Vector2 = (al["pos"] - tp).normalized() if tp != Vector2.INF and al["pos"].distance_to(tp) > 0.1 else Vector2.from_angle(p_facing + PI)
				want = p_pos + away * 3.5
				facing_target = true
				if now >= float(al["retreat_until"]):
					al["state"] = "approach" if float(al["hp"]) >= nerve * 0.8 else "guard"
			"guard":
				# Hurt and staying back: beside the hero, blocking what comes.
				want = p_pos + Vector2.from_angle(p_facing).rotated(side * 1.6) * 1.8
				if tp == Vector2.INF or float(al["hp"]) > nerve * 1.5:
					al["state"] = "ease"
		# Walk there.
		if want != Vector2.INF:
			var d: Vector2 = want - al["pos"]
			var step := speed * dt * (0.8 if String(al["state"]) == "circle" else 1.0)
			al["moving"] = d.length() > 0.3 and String(al["state"]) not in ["windup", "technique", "pattern", "recover", "parry", "block"]
			if al["moving"]:
				al["pos"] = _clamp_in(al["pos"] + (d.normalized() * minf(step, d.length())))
		else:
			al["moving"] = false
		al["facing"] = _angle_to(al["pos"], tp) if facing_target and tp != Vector2.INF else (p_facing if String(al["state"]) == "ease" else al["facing"])
		# Not on top of each other or the hero.
		for k in allies.size():
			if k != i and not allies[k]["down"]:
				var dd: float = al["pos"].distance_to(allies[k]["pos"])
				if dd < 1.1 and dd > 1e-4:
					al["pos"] = _clamp_in(allies[k]["pos"] + (al["pos"] - allies[k]["pos"]) / dd * 1.1)
		var dp: float = al["pos"].distance_to(p_pos)
		if dp < 1.0 and dp > 1e-4:
			al["pos"] = _clamp_in(p_pos + (al["pos"] - p_pos) / dp * 1.0)

## A classmate's blow lands on their foe if it is in reach (a shot if they are ranged).
func _ally_strike(i: int, tgt: int, dmg: float, heavy: bool, pattern := false) -> void:
	var al: Dictionary = allies[i]
	var tp := _threat_pos(tgt)
	if tp == Vector2.INF:
		return
	var in_reach: bool = al["pos"].distance_to(tp) <= float(al["reach"]) + 0.8
	if al["ranged"]:
		_emit({ "type": "ally-shot", "who": i, "from": al["pos"], "to": tp, "hit": in_reach })
	if not in_reach:
		_emit({ "type": "ally-miss", "who": i })
		return
	if tgt == -1:
		if w_state == "stagger":
			dmg = roundf(dmg * float(room["break"]["staggerDamageFactor"]))
		dmg = _guarded(dmg, pattern)
		w_hp = maxf(w_floor, w_hp - dmg)
		stats["damage_dealt"] += dmg
		_emit({ "type": "ally-hit", "who": i, "damage": dmg, "heavy": heavy, "pattern": pattern })
		if heavy and w_state in ["prowl", "approach", "recover", "idle"] and not pattern:
			_wolf_set("flinch", float(beast.get("flinchTime", 0.3)))
		if pattern and w_state not in ["down", "absent"]:
			_wolf_set("stagger", float(room["break"]["staggerSeconds"]) * 0.6)
			_emit({ "type": "stagger", "seconds": float(room["break"]["staggerSeconds"]) * 0.6, "cause": "ally-pattern" })
		if w_hp == 0.0:
			_fell_wolf()
	else:
		_damage_other(tgt, dmg, heavy)
		_emit({ "type": "ally-hit", "who": i, "damage": dmg, "foe": tgt, "heavy": heavy, "pattern": pattern })

## A bite at a classmate: turned if they were parrying (the foe staggers), softened if they
## were blocking, else it lands.
func _hurt_ally(i: int, dmg: float, from_idx := -1) -> void:
	var al: Dictionary = allies[i]
	# a shield set for whoever is struck first, or standing as a door; a lamp's shelter
	if _item_takes(dmg, i):
		return
	dmg = roundf(dmg * _lamp_k("shelter", al["pos"]))
	match String(al.get("state", "")):
		"parry":
			_emit({ "type": "ally-parry", "who": i, "foe": from_idx })
			stats["ally_parries"] = int(stats.get("ally_parries", 0)) + 1
			if from_idx == -1:
				_wolf_set("stagger", float(room["break"]["staggerSeconds"]) * 0.5)
				_emit({ "type": "stagger", "seconds": float(room["break"]["staggerSeconds"]) * 0.5, "cause": "ally-parry" })
			elif from_idx < foes.size():
				(foes[from_idx] as Foe).set_state("stagger", float(room["break"]["staggerSeconds"]) * 0.5)
				_emit({ "type": "foe-stagger", "foe": from_idx })
			return
		"block":
			dmg = roundf(dmg * 0.3)
			_emit({ "type": "ally-block", "who": i, "damage": dmg })
	al["hp"] = maxf(0.0, float(al["hp"]) - dmg)
	_emit({ "type": "ally-hurt", "who": i, "damage": dmg })
	if al["hp"] == 0.0:
		al["down"] = true
		w_target = -1
		_emit({ "type": "ally-down", "who": i })

## At a post the party regroups: whoever is down stands up, and everyone is whole.
func allies_recover() -> void:
	for i in allies.size():
		var al: Dictionary = allies[i]
		if al["down"]:
			_emit({ "type": "ally-up", "who": i })
		al["down"] = false
		al["hp"] = al["hp_max"]
		al["pattern_used"] = false
		al["state"] = "ease"
	p_hp = float(room["player"]["health"])

func allies_standing() -> int:
	var n := 0
	for al in allies:
		if not al["down"]:
			n += 1
	return n

func _fell_wolf() -> void:
	stats["wolves_down"] += 1
	_wolf_set("down", float(beast["respawnSeconds"]))
	_emit({ "type": "wolf-down" })
	_emit({ "type": "anim", "who": "wolf", "name": "Death", "speed": 1.0 })

func _wolf_step_toward(target: Vector2, step: float) -> void:
	var d := w_pos.distance_to(target)
	if d < 1e-6:
		return
	w_pos = _clamp_in(w_pos + (target - w_pos) / d * minf(step, d))

## The bite lands: dodged, parried, blocked, or taken.
func _resolve_bite() -> void:
	_resolve_bite_from(w_attack, w_pos, -1)

## A bite from the locked foe (index -1) or one of the pack: dodged, parried, blocked, or taken.
func _resolve_bite_from(a: Dictionary, from_pos: Vector2, idx: int) -> void:
	if p_state == "down":
		return
	if p_invulnerable():
		stats["evades"] += 1
		_emit({ "type": "evade", "how": "dodged" })
		_typed_met("dodge", idx, 0.0)
		return
	if now < ward_until:
		ward_until = -9.0
		_emit({ "type": "ward-broken" })
		_emit({ "type": "turned" })
		return
	if p_state == "pattern" and not chain.is_empty() and chain["effect"] == "guard":
		_emit({ "type": "turned" })
		if idx < 0:
			_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 1.0 })
		return
	var facing_wolf := absf(angle_difference(p_facing, _angle_to(p_pos, from_pos))) <= deg_to_rad(float(room["block"]["arc"])) / 2.0
	if now <= p_parry_until and facing_wolf:
		var pr: Dictionary = room["parry"]
		p_will = minf(float(rules["field"]["willMax"]), p_will + float(pr["will"]))
		p_parry_until = -9.0
		stats["parries"] += 1
		if idx < 0:
			_wolf_set("stagger", float(pr["staggerSeconds"]))
			_emit({ "type": "anim", "who": "wolf", "name": "HitReact", "speed": 0.8 })
		else:
			(foes[idx] as Foe).set_state("stagger", float(pr["staggerSeconds"]))
			_emit({ "type": "foe-stagger", "foe": idx })
		parried_until = now + float(room["pattern"]["afterParrySeconds"])
		_emit({ "type": "parry", "foe": idx, "hand": g_in_hand })
		_emit({ "type": "anim", "who": "player", "name": "Block_Hit", "speed": 1.3 })
		_typed_met("parry", idx, 0.0)
		return
	var dmg := _genius_on_struck(float(a["damage"]) * _b("damageTaken", 1.0), from_pos, idx)
	# a strike with the weight taken out of it (an arrow in its wind-up), and a lamp's shelter
	if idx < 0 and now < w_weak_until:
		dmg *= w_weak
	dmg *= _lamp_k("shelter", p_pos)
	if _genius_turns(dmg, idx):
		return
	if _item_takes(dmg, -1):
		return
	if not (_blocking() and facing_wolf) and _genius_guards(dmg):
		return
	_genius_debt_paid(dmg, idx)
	if _blocking() and facing_wolf:
		dmg *= float(room["block"]["damageFactor"]) * _always_k("block", "damage")
		p_will = maxf(0.0, p_will - float(room["block"]["willPerBlockedHit"]) * _always_k("block", "will"))
		stats["blocks"] += 1
		_emit({ "type": "block", "damage": dmg, "hand": g_in_hand })
		_emit({ "type": "anim", "who": "player", "name": "Block_Hit", "speed": 1.2 })
		_typed_met("block", idx, dmg)
	else:
		dmg *= _always_k("hurt")
		stats["hurts"] += 1
		p_struck_this_foe = true
		_emit({ "type": "hurt", "damage": dmg })
		_typed_met("hurt", idx, dmg)
		p_combo_count = 0
		if not (p_stance and kit["stance"].get("noFlinch", false)):
			p_pos = _clamp_in(p_pos + (p_pos - from_pos).normalized() * float(a["knockback"]))
			if p_state != "pattern":
				p_state = "flinch"
				p_timer = 0.0
				_emit({ "type": "anim", "who": "player", "name": "Hit_A", "speed": 1.2 })
	p_hp = maxf(0.0, p_hp - dmg)
	if mercy:
		p_hp = maxf(p_hp, 1.0)
	if p_hp == 0.0 and bc.get("secondHeart", false) and not second_heart_used:
		second_heart_used = true
		p_hp = 1.0
		_emit({ "type": "second-heart" })
	# an open hand catches its partner once a fight, when a blow would fell them
	if p_hp == 0.0 and not g_fall_caught and genius and not genius.fallen and g_item.get("always", {}).has("catchFall"):
		g_fall_caught = true
		p_hp = float(g_item["always"]["catchFall"])
		_emit({ "type": "genius-caught-fall" })
	if p_hp == 0.0:
		p_state = "down"
		p_stance = false
		chain = {}
		_emit({ "type": "player-down" })
		_emit({ "type": "anim", "who": "player", "name": "Death_A", "speed": 1.0 })

## Bodies do not overlap.
func _separate() -> void:
	# A little personal space, so the wolf reads clearly beside the Anchor; the pack keeps
	# off the hero and off each other.
	for i in foes.size():
		var fo: Foe = foes[i]
		if not fo.alive():
			continue
		var mf := float(room["player"]["radius"]) + float(fo.beast["radius"]) + 0.3
		var df := fo.pos.distance_to(p_pos)
		if df < mf:
			fo.pos = _clamp_in(p_pos + Vector2.from_angle(_angle_to(p_pos, fo.pos) if df > 1e-6 else float(i)) * mf)
		for j in foes.size():
			if j == i:
				continue
			var g: Foe = foes[j]
			if not g.alive():
				continue
			var dd := fo.pos.distance_to(g.pos)
			var mm := float(fo.beast["radius"]) + float(g.beast["radius"])
			if dd < mm and dd > 1e-6:
				fo.pos = _clamp_in(g.pos + (fo.pos - g.pos) / dd * mm)
		if w_state not in ["absent", "down"]:
			var dw := fo.pos.distance_to(w_pos)
			var mw := float(fo.beast["radius"]) + float(beast["radius"])
			if dw < mw and dw > 1e-6:
				fo.pos = _clamp_in(w_pos + (fo.pos - w_pos) / dw * mw)
	if w_state in ["absent", "down"]:
		return
	var m := float(room["player"]["radius"]) + float(beast["radius"]) + 0.3
	var d := dist()
	if d >= m:
		return
	var a := _angle_to(p_pos, w_pos) if d > 1e-6 else 0.0
	w_pos = _clamp_in(p_pos + Vector2.from_angle(a) * m)

# ===================================================================== the pack

## One more of the pack, at a place, at a fraction of its health.
func spawn_foe(beast_id: String, at: Vector2, health_scale := 1.0) -> Foe:
	var fo := Foe.new()
	fo.beast = Data.beast(beast_id).duplicate(true)
	fo.beast["health"] = roundf(float(fo.beast["health"]) * health_scale)
	fo.hp = fo.beast["health"]
	fo.pos = _clamp_in(at)
	fo.facing = _angle_to(fo.pos, p_pos)
	fo.shape = fo.beast["shape"]
	fo.angle = rng.randf() * TAU
	fo.dir = -1.0 if rng.randf() < 0.5 else 1.0
	fo.set_state("idle" if passive else "prowl", rng.randf_range(0.5, 1.5))
	foes.append(fo)
	_emit({ "type": "foe-spawn", "foe": foes.size() - 1, "name": fo.beast["name"] })
	return fo

func foes_alive() -> int:
	var n := 0
	for fo in foes:
		if (fo as Foe).alive():
			n += 1
	return n

## Everything standing against the hero: the locked foe and the live pack.
func threats() -> int:
	return (1 if w_state not in ["down", "absent"] else 0) + foes_alive()

## The rest of the pack: circle, pick someone, come in, bite, recover.
func _update_others(dt: float) -> void:
	for i in foes.size():
		var fo: Foe = foes[i]
		fo.timer += dt
		var b := fo.beast
		match fo.state:
			"absent", "down":
				continue
			"idle":
				fo.facing = lerp_angle(fo.facing, _angle_to(fo.pos, p_pos), 1.0 - exp(-6.0 * dt))
				if not passive and fo.timer >= fo.duration:
					fo.set_state("prowl", rng.randf_range(float(b["prowl"]["min"]), float(b["prowl"]["max"])))
			"prowl":
				fo.angle += fo.dir * float(b["walkSpeed"]) / float(b["circleRadius"]) * dt
				var want := p_pos + Vector2.from_angle(fo.angle) * (float(b["circleRadius"]) + 1.0)
				var before := fo.pos
				_foe_step(fo, want, float(b["walkSpeed"]) * 1.4 * dt)
				if (fo.pos - before).length() > 0.001:
					fo.facing = lerp_angle(fo.facing, (fo.pos - before).angle(), 1.0 - exp(-6.0 * dt))
				if fo.timer >= fo.duration:
					_foe_choose(fo)
			"approach":
				var tp := _foe_target_pos(fo)
				var rng_a := float(fo.attack["range"])
				if fo.pos.distance_to(tp) > rng_a * 0.85:
					_foe_step(fo, tp, float(b["gallopSpeed"]) * dt)
					fo.facing = _angle_to(fo.pos, tp)
				elif fo.target == -1 and _bites_on_hero() >= int(room.get("pack", {}).get("atOnce", 1)):
					# The pack takes turns at the hero: this one circles close until the bite in
					# flight has landed.
					fo.facing = _angle_to(fo.pos, tp)
					var around := _angle_to(tp, fo.pos) + fo.dir * 0.9 * dt
					_foe_step(fo, tp + Vector2.from_angle(around) * rng_a * 0.9, float(b["walkSpeed"]) * dt)
					if fo.timer > 4.0:
						fo.set_state("prowl", 1.0)
				else:
					fo.set_state("windup", float(fo.attack["windup"]))
					fo.facing = _angle_to(fo.pos, tp)
					_emit({ "type": "foe-windup", "foe": i, "attack": fo.attack["id"], "name": fo.attack["name"], "seconds": fo.duration })
				if fo.timer > 6.0:
					fo.set_state("prowl", 1.0)
			"windup":
				if fo.timer < fo.duration * 0.8:
					fo.facing = lerp_angle(fo.facing, _angle_to(fo.pos, _foe_target_pos(fo)), 1.0 - exp(-10.0 * dt))
				if fo.timer >= fo.duration:
					fo.set_state("strike", float(fo.attack["active"]))
					fo.hit_done = false
					_emit({ "type": "foe-strike", "foe": i, "anim": fo.attack.get("anim", "") })
			"strike":
				var lunge := float(fo.attack["lunge"]) / float(fo.attack["active"]) * dt
				fo.pos = _clamp_in(fo.pos + Vector2.from_angle(fo.facing) * lunge)
				if not fo.hit_done:
					var mouth := fo.pos + Vector2.from_angle(fo.facing) * (float(b["radius"]) + 0.4)
					if mouth.distance_to(p_pos) <= float(room["player"]["radius"]) + 1.0:
						fo.hit_done = true
						var soft := fo.attack.duplicate()
						soft["damage"] = roundf(float(fo.attack["damage"]) * float(room.get("pack", {}).get("damage", 1.0)))
						_resolve_bite_from(soft, fo.pos, i)
					else:
						for k in allies.size():
							if not allies[k]["down"] and mouth.distance_to(allies[k]["pos"]) <= 1.3:
								fo.hit_done = true
								_hurt_ally(k, roundf(float(fo.attack["damage"]) * float(room.get("pack", {}).get("damage", 1.0))), i)
								break
				if fo.timer >= fo.duration:
					fo.set_state("recover", float(fo.attack["recover"]))
			"recover", "stagger", "flinch":
				if fo.timer >= fo.duration:
					fo.set_state("prowl", rng.randf_range(float(b["prowl"]["min"]), float(b["prowl"]["max"])))
					fo.dir = -1.0 if rng.randf() < 0.5 else 1.0

## How many bites are in flight at the hero right now (the locked beast's and the pack's).
func _bites_on_hero() -> int:
	var n := 0
	if w_state in ["windup", "strike"] and w_target == -1:
		n += 1
	for fo in foes:
		if (fo as Foe).state in ["windup", "strike"] and (fo as Foe).target == -1:
			n += 1
	return n

func _foe_target_pos(fo: Foe) -> Vector2:
	if fo.target >= 0 and fo.target < allies.size() and not allies[fo.target]["down"]:
		return allies[fo.target]["pos"]
	return p_pos

func _foe_step(fo: Foe, target: Vector2, step: float) -> void:
	var d := fo.pos.distance_to(target)
	if d < 1e-6:
		return
	fo.pos = _clamp_in(fo.pos + (target - fo.pos) / d * minf(step, d))

func _foe_choose(fo: Foe) -> void:
	# The nearest standing body, mostly; now and then whoever it fancies.
	fo.target = -1
	var standing: Array = []
	var best_d := fo.pos.distance_to(p_pos) / float(room.get("pack", {}).get("heroDraw", 1.0))
	for i in allies.size():
		if not allies[i]["down"]:
			standing.append(i)
			var d: float = fo.pos.distance_to(allies[i]["pos"])
			if d < best_d:
				best_d = d
				fo.target = i
	if not standing.is_empty() and rng.randf() < 0.2:
		fo.target = standing[rng.randi() % standing.size()]
	elif rng.randf() < 0.15:
		fo.target = -1
	var tp := _foe_target_pos(fo)
	var options: Array = []
	var total := 0.0
	for a in fo.beast["attacks"]:
		if fo.pos.distance_to(tp) < float(a.get("minRange", 0.0)) or float(a["weight"]) <= 0.0:
			continue
		options.append(a)
		total += float(a["weight"])
	if options.is_empty():
		fo.set_state("prowl", 1.0)
		return
	var r := rng.randf() * total
	fo.attack = options[0]
	for a in options:
		r -= float(a["weight"])
		if r <= 0.0:
			fo.attack = a
			break
	fo.set_state("approach", 6.0)

## A hit on one of the pack: it flinches from a heavy blow and falls at nothing.
func _damage_other(i: int, dmg: float, heavy: bool) -> void:
	var fo: Foe = foes[i]
	if not fo.alive():
		return
	if fo.state == "stagger":
		dmg = roundf(dmg * float(room["break"]["staggerDamageFactor"]))
	fo.hp = maxf(0.0, fo.hp - dmg)
	fo.hits_taken += 1
	stats["hits"] += 1
	stats["damage_dealt"] += dmg
	p_combo_count += 1
	_emit({ "type": "foe-hit", "foe": i, "damage": dmg, "heavy": heavy, "dist": fo.pos.distance_to(p_pos), "hand": g_in_hand and p_state == "attack", "stand": _stands() })
	if fo.hp == 0.0:
		stats["wolves_down"] += 1
		fo.set_state("down", 99.0)
		_emit({ "type": "foe-down", "foe": i, "name": fo.beast["name"] })
	elif heavy and fo.state in ["prowl", "approach", "recover", "idle"]:
		fo.set_state("flinch", float(fo.beast["flinchTime"]))

## The locked foe fell: the nearest of the pack takes its place under the lock.
func _retarget_if_down() -> void:
	if w_state != "down" or w_timer < 0.6 or foes_alive() == 0:
		return
	var best := -1
	var best_d := INF
	for i in foes.size():
		var fo: Foe = foes[i]
		if fo.alive() and fo.pos.distance_to(p_pos) < best_d:
			best_d = fo.pos.distance_to(p_pos)
			best = i
	if best >= 0:
		swap_target(best)

## Exchange the locked foe (w_*) with one of the pack.
func swap_target(i: int) -> void:
	var fo: Foe = foes[i]
	var old := Foe.new()
	old.beast = beast
	old.pos = w_pos
	old.facing = w_facing
	old.hp = w_hp
	old.state = w_state
	old.timer = w_timer
	old.duration = w_duration
	old.attack = w_attack
	old.hit_done = w_hit_done
	old.angle = w_angle
	old.dir = w_dir
	old.target = w_target
	old.burn_until = w_burn_until
	old.hits_taken = w_hits_taken
	old.breaks = w_break
	old.named = w_named
	old.pattern_hits = w_pattern_hits
	old.shape = w_shape
	beast = fo.beast
	w_pos = fo.pos
	w_facing = fo.facing
	w_hp = fo.hp
	w_state = fo.state
	w_timer = fo.timer
	w_duration = fo.duration
	w_attack = fo.attack
	w_hit_done = fo.hit_done
	w_angle = fo.angle
	w_dir = fo.dir
	w_target = fo.target
	w_burn_until = fo.burn_until
	w_hits_taken = fo.hits_taken
	w_break = fo.breaks
	w_named = fo.named
	w_pattern_hits = fo.pattern_hits
	w_shape = fo.shape if fo.shape != "" else fo.beast["shape"]
	w_slow_until = -9.0
	w_mark_until = -9.0
	foes[i] = old
	_foe_changed(String(old.beast.get("id", "")))
	_emit({ "type": "retarget", "foe": i })
