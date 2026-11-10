## The balance harness: plays every weapon type, every technique and every temperament
## headlessly and prints tables, so a change to a number can be judged before it is played.
##   npm run balance:game   (godot --headless --path . res://game/tests/balance.tscn)
## Rules are data; this is how the data is read back.
extends Node

const DT := 1.0 / 60.0

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	if OS.get_cmdline_user_args().has("--elites"):
		_elites()
		get_tree().quit()
		return
	print("\n== WEAPON TYPES: a skilled bot, 120 s against cut-wolves that return (seed 5) ==")
	print("%-12s %-14s %6s %7s %7s %7s %6s" % ["type", "weapon", "felled", "dealt", "bitten", "lasted", "shots"])
	var rows := []
	for st in Data.room["styles"]:
		if String(st).begins_with("$"):
			continue
		var w := _weapon_of_type(st)
		var f := _bot(120.0, w["id"])
		rows.append([st, w["name"], f.stats["wolves_down"], int(f.stats["damage_dealt"]), f.stats["hurts"], f.now, int(f.stats.get("shots", 0))])
		print("%-12s %-14s %6d %7d %7d %7.0f %6d" % rows[rows.size() - 1])
	print("\n== TECHNIQUES: damage per Will, against a standing wolf at the technique's best range (hero at Stage 2) ==")
	print("%-12s %-20s %-9s %5s %5s %6s %8s %8s" % ["school", "technique", "effect", "will", "cd", "dmg", "dmg/Will", "dmg/cd-s"])
	var tech_rows := []
	for d in Data.disciplines:
		var kit: Dictionary = Data.discipline_kits[d["id"]]
		for t in kit["techniques"]:
			var dmg := _technique_damage(d, t)
			var per_will := dmg / maxf(1.0, float(t["will"]))
			var per_cd := dmg / maxf(0.5, float(t["cooldown"]))
			tech_rows.append([d["id"], t["id"], t["effect"], int(t["will"]), float(t["cooldown"]), dmg, per_will, per_cd])
			print("%-12s %-20s %-9s %5d %5.1f %6.0f %8.2f %8.2f" % tech_rows[tech_rows.size() - 1])
	# Outliers: damage per Will outside half to double the median, for effects that deal damage.
	var vals: Array = tech_rows.filter(func(r): return r[5] > 0).map(func(r): return r[6])
	vals.sort()
	if not vals.is_empty():
		var med: float = vals[vals.size() / 2]
		print("\nmedian damage per Will %.2f; outliers:" % med)
		for r in tech_rows:
			if r[5] > 0 and (r[6] < med * 0.5 or r[6] > med * 2.0):
				print("  %s %s: %.2f per Will (%s)" % [r[0], r[1], r[6], "weak" if r[6] < med else "strong"])
	print("\n== ZONES: a skilled saber hero at Stage 3 with two classmates, 150 s in each area (the pack at its largest; the elite in its lair) ==")
	print("%-24s %-14s %5s %6s %7s %6s %7s %5s" % ["area", "beast", "pack", "felled", "elite", "hurt", "lasted", "down"])
	for z in Data.zones():
		for a in z["areas"]:
			var r := _zone_run(z, a)
			print("%-24s %-14s %5d %6d %7s %6d %7.0f %5d" % r)
	_elites()
	print("\n== TEMPERAMENTS: two classmates of one temperament, 90 s with the hero standing still, a pack of one beside the locked wolf ==")
	print("%-10s %6s %7s %8s %6s %6s %6s %6s" % ["temper", "felled", "hits", "dealt", "techs", "parry", "retreat", "down"])
	for tp in Data.academy["cohort"]["temperaments"]:
		var r := _cohort(String(tp["id"]))
		print("%-10s %6d %7d %8d %6d %6d %6d %6d" % r)
	get_tree().quit()

## A bite about to land on the hero, from the locked beast or any of the pack.
func _bite_coming(f: Fight) -> bool:
	if f.w_state == "windup" and f.w_duration - f.w_timer <= 0.1 and f.w_duration - f.w_timer > 0.1 - DT:
		return true
	for fo in f.foes:
		if fo.state == "windup" and fo.target == -1 and fo.duration - fo.timer <= 0.1 and fo.duration - fo.timer > 0.1 - DT:
			return true
	return false

func _any_windup(f: Fight) -> bool:
	if f.w_state == "windup":
		return true
	for fo in f.foes:
		if fo.state == "windup" and fo.target == -1:
			return true
	return false

func _weapon_of_type(st: String) -> Dictionary:
	for w in Data.weapons:
		if w["style"] == st:
			return w
	return Data.weapons[0]

## A bot that knows its weapon: melee closes and strikes in the foe's openings; ranged keeps
## its distance, shoots, and reloads; the bow draws; everyone parries the bite.
func _bot(seconds: float, weapon_id: String) -> Fight:
	var h := Fight.default_hero()
	var w := Data.by_id(Data.weapons, weapon_id)
	h["weapon"] = weapon_id
	h["city"] = w["city"]
	h["discipline"] = Creation.discipline_of(w["city"])
	var f := Fight.new({ "seed": 5, "hero": h })
	var drawing := false
	for i in int(seconds / DT):
		var to_w := f.w_pos - f.p_pos
		var move := Vector2.ZERO
		if _bite_coming(f):
			f.input("block-down")
		if f.p_block_held and not _any_windup(f):
			f.input("block-up")
		if f.pattern_ready():
			f.input("pattern")
		if f.p_state == "pattern" and not f.chain.is_empty():
			var c: float = f.chain["cues"][f.chain["next"]]
			if absf(f.now - c) < DT / 2.0:
				f.input("attack")
		elif f.ranged:
			var want := 7.0
			if f.style.has("draw"):
				if f.p_state == "free" and not drawing and f.w_state not in ["down", "absent"]:
					f.input("attack")
					drawing = true
				elif f.p_state == "draw" and f.p_draw >= float(f.style["draw"]["seconds"]):
					f.input("attack-up")
					drawing = false
				elif f.p_state != "draw":
					drawing = false
			elif f.p_ammo_max > 0 and f.p_ammo == 0 and f.p_state == "free":
				f.input("reload")
			elif f.w_state not in ["down", "absent", "windup"] and f.p_state == "free" and to_w.length() < float(f.combo[0]["range"]):
				f.input("attack")
			if to_w.length() > want + 1.5 and f.w_state != "windup":
				move = to_w.normalized()
			elif to_w.length() < want - 2.0 and f.p_state != "draw":
				move = -to_w.normalized()
		else:
			if f.w_state in ["recover", "stagger", "flinch"] and to_w.length() < 2.4 and (f.w_state != "recover" or f.w_duration - f.w_timer > 0.45):
				if f.p_will > 40 and f.now >= float(f.p_cooldowns.get(f.tech["id"], 0.0)):
					f.input("technique")
				else:
					f.input("attack")
			if to_w.length() > 2.0 and f.w_state != "windup":
				move = to_w.normalized()
		f.update(DT, move)
		f.drain()
		if f.p_state == "down":
			break
	return f

func _technique_damage(d: Dictionary, t: Dictionary) -> float:
	var h := Fight.default_hero()
	h["discipline"] = d["id"]
	h["city"] = d["city"]
	h["weapon"] = d["weapons"][0]
	h["techniques"] = [t["id"]]
	var best := 0.0
	for dist in [2.0, 4.0, 7.0]:
		var f := Fight.new({ "seed": 1, "hero": h, "passive": true })
		f._wolf_set("idle", 99.0)
		f.w_pos = f.p_pos + Vector2(dist, 0)
		f.p_facing = 0.0
		f.p_will = 100.0
		var hp0 := f.w_hp
		f._press_technique(t)
		for i in int(2.5 / DT):
			f.update(DT, Vector2.ZERO)
			f.drain()
		best = maxf(best, hp0 - f.w_hp)
	return best

## The hero, Stage 3, with the first two classmates, against an area's beasts.
func _zone_run(z: Dictionary, a: Dictionary) -> Array:
	var h := Fight.default_hero()
	h["stage"] = 3
	h["projected"] = true
	var cohort := Academy.make_cohort(42, h)
	var which := String(a.get("beast", "common"))
	var beast_id: String = z["beasts"]["common"] if which == "common" else (z["beasts"]["elite"] if which == "elite" else which)
	var pack: Array = []
	if a.has("pack"):
		for i in int(a["pack"]["max"]):
			pack.append(z["beasts"]["common"])
	var f := Fight.new({ "seed": 11, "hero": h, "beast": beast_id, "allies": [cohort[0], cohort[1]], "pack": pack, "respawn": a.get("respawn", true), "arena": Vector2(a["size"][0], a["size"][1]) })
	var elite_down := "-"
	var downs := 0
	for i in int(150.0 / DT):
		var to_w := f.w_pos - f.p_pos
		var move := Vector2.ZERO
		if _bite_coming(f):
			f.input("block-down")
		if f.p_block_held and not _any_windup(f):
			f.input("block-up")
		if f.pattern_ready():
			f.input("pattern")
		if f.p_state == "pattern" and not f.chain.is_empty():
			var c: float = f.chain["cues"][f.chain["next"]]
			if absf(f.now - c) < DT / 2.0:
				f.input("attack")
		elif f.w_state in ["recover", "stagger", "flinch", "idle", "prowl"] and to_w.length() < 2.4 and (f.w_state != "recover" or f.w_duration - f.w_timer > 0.45):
			if f.p_will > 40 and f.now >= float(f.p_cooldowns.get(f.tech["id"], 0.0)):
				f.input("technique")
			else:
				f.input("attack")
		if to_w.length() > 2.0 and f.w_state != "windup" and f.w_state not in ["down", "absent"]:
			move = to_w.normalized()
		f.update(DT, move)
		for e in f.drain():
			if e["type"] == "wolf-down" and which == "elite" and elite_down == "-":
				elite_down = "%.0f s" % f.now
			if e["type"] == "ally-down":
				downs += 1
		if f.p_state == "down":
			break
	return ["%s/%s" % [z["id"], a["id"]], beast_id, pack.size(), f.stats["wolves_down"], elite_down, f.stats["hurts"], f.now, downs]

## The guarded elites and the named beasts against three hands (npm run balance:game -- --elites
## prints this table alone). The Academy's own elite, the Warden, is the one a learner must pass.
func _elites() -> void:
	print("\n== ELITES AND NAMED: four hands at the guarded beasts, a First Form genius on guard, %d fights of up to 240 s each ==" % ELITE_SEEDS)
	print("   sure: parries every bite, strikes in the openings.  steady: raises the guard late two times in three, and so sometimes parries.")
	print("   learning: raises it early one time in two (a block), strikes half the time out of turn.  new: no guard, strikes whenever in reach.")
	print("%-14s %-7s %-9s %-6s %7s %7s %10s %12s %6s" % ["beast", "shape", "hand", "party", "felled", "in", "hero left", "if lost, at", "hurts"])
	for z in Data.zones():
		var eb: String = z["beasts"]["elite"]
		var breaker := Data.opposite(String(Data.beast(eb)["shape"]))
		for hand in ["sure", "steady", "learning", "new"]:
			for who in [["anchor", false], ["anchor", true], [breaker, true]]:
				if who[0] == "anchor" and breaker == "anchor" and who[1]:
					continue
				print("%-14s %-7s %-9s %-6s %7s %7s %10s %12s %6s" % _elite_row(eb, eb, 1.0, hand, who[0], who[1]))
		for nb in z["beasts"].get("named", []):
			for hand in ["steady", "learning", "new"]:
				print("%-14s %-7s %-9s %-6s %7s %7s %10s %12s %6s" % _elite_row(String(nb["name"]), String(nb["beast"]), float(nb.get("health", 1.5)), hand, "anchor", true))

const ELITE_SEEDS := 6

## A row of the table: the same fight over several seeds. How many were won, the middle time
## of the wins, the hero's health left in them, and where the beast stood in the losses.
func _elite_row(label: String, beast_id: String, health: float, hand: String, shape: String, with_party: bool) -> Array:
	var wins: Array = []
	var left: Array = []
	var lost_at: Array = []
	var hurts := 0
	for sd in ELITE_SEEDS:
		var r := _elite_run(beast_id, health, hand, shape, with_party, 11 + sd * 17)
		hurts += int(r["hurts"])
		if OS.get_cmdline_user_args().has("--detail"):
			print("      %s %s seed %d: %.0f s, dealt %d, hurts %d, blocks %d, parries %d, hero %d, beast %d%%" % [label, hand, sd, r["t"], r["dealt"], r["hurts"], r["blocks"], r["parries"], r["hero"], r["beast"]])
		if r["felled"] >= 0.0:
			wins.append(r["felled"])
			left.append(r["hero"])
		else:
			lost_at.append(r["beast"])
	wins.sort()
	var mean := func(xs: Array) -> float:
		var t := 0.0
		for x in xs:
			t += float(x)
		return t / maxf(1.0, xs.size())
	return [label, shape, hand, "three" if with_party else "alone", "%d/%d" % [wins.size(), ELITE_SEEDS],
		("%.0f s" % wins[wins.size() / 2]) if not wins.is_empty() else "-", ("%.0f" % mean.call(left)) if not wins.is_empty() else "-",
		("%.0f%%" % mean.call(lost_at)) if not lost_at.is_empty() else "-", "%.1f" % (hurts / float(ELITE_SEEDS))]

## One beast, alone in its lair, against a hero of a given Shape and hand at Stage 3, with or
## without two classmates. Returns the row: when it fell, and how the fight ended.
func _elite_run(beast_id: String, health: float, hand: String, shape: String, with_party: bool, seed_value := 11, seconds := 240.0) -> Dictionary:
	var h := Fight.default_hero()
	h["stage"] = 3
	h["projected"] = true
	h["shape"] = shape
	var cohort := Academy.make_cohort(42, h)
	var opts := { "seed": seed_value, "hero": h, "beast": beast_id, "respawn": false, "arena": Vector2(20, 14), "allies": [cohort[0], cohort[1]] if with_party else [] }
	var ff := Rite.first_form(h, shape, 11)
	opts["genius"] = Rite.birth(h, ff["reading"], ff["name"])
	if health != 1.0:
		opts["beast_health"] = roundf(float(Data.beast(beast_id)["health"]) * health)
	var f := Fight.new(opts)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value * 3 + 7
	var guard_this := true
	var rng_half := true
	var was_windup := false
	var felled := -1.0
	for i in int(seconds / DT):
		var to_w := f.w_pos - f.p_pos
		var move := Vector2.ZERO
		var windup := _any_windup(f)
		if windup and not was_windup:
			guard_this = rng.randf() < 0.67
			rng_half = rng.randf() < 0.5
		was_windup = windup
		match hand:
			"sure":
				if _bite_coming(f):
					f.input("block-down")
				if f.p_block_held and not windup:
					f.input("block-up")
			"steady":
				# late to the guard: it is up a quarter second into the wind-up, and stays up
				if windup and guard_this and not f.p_block_held and f.w_timer > 0.25:
					f.input("block-down")
				if f.p_block_held and not windup and f.w_state != "strike":
					f.input("block-up")
			"learning":
				# the guard goes up as soon as the beast gathers, half the time: too early to parry
				if windup and rng_half and not f.p_block_held:
					f.input("block-down")
				if f.p_block_held and not windup and f.w_state != "strike":
					f.input("block-up")
		if f.pattern_ready():
			f.input("pattern")
		if f.p_state == "pattern" and not f.chain.is_empty():
			var c: float = f.chain["cues"][f.chain["next"]]
			if absf(f.now - c) < DT / 2.0:
				f.input("attack")
		elif to_w.length() < 2.4 and not f.p_block_held and f.w_state not in ["down", "absent"]:
			var opening: bool = f.w_state in ["recover", "stagger", "flinch", "idle", "prowl"] and (f.w_state != "recover" or f.w_duration - f.w_timer > 0.45)
			if opening or hand == "new" or (hand == "learning" and guard_this and not windup):
				if hand in ["sure", "steady"] and f.p_will > 40 and f.now >= float(f.p_cooldowns.get(f.tech["id"], 0.0)):
					f.input("technique")
				else:
					f.input("attack")
		if to_w.length() > 2.0 and (f.w_state != "windup" or hand == "new") and f.w_state not in ["down", "absent"]:
			move = to_w.normalized()
		f.update(DT, move)
		for e in f.drain():
			if e["type"] == "wolf-down" and felled < 0.0:
				felled = f.now
		if f.p_state == "down" or felled >= 0.0:
			break
	return { "t": f.now, "dealt": f.stats["damage_dealt"], "felled": felled, "hero": f.p_hp, "beast": 100.0 * f.w_hp / float(f.beast["health"]), "hurts": f.stats["hurts"], "parries": f.stats["parries"], "blocks": f.stats["blocks"] }

func _cohort(temper: String) -> Array:
	var h := Fight.default_hero()
	var cohort := Academy.make_cohort(42, h)
	var mates: Array = []
	for i in 2:
		var c: Dictionary = cohort[i].duplicate()
		c["temperament"] = temper
		mates.append(c)
	var f := Fight.new({ "seed": 7, "hero": h, "allies": mates, "pack": ["cut-wolf"] })
	var hits := 0
	var techs := 0
	var parries := 0
	var retreats := 0
	var downs := 0
	for i in int(90.0 / DT):
		if _bite_coming(f):
			f.input("block-down")
		if f.p_block_held and not _any_windup(f):
			f.input("block-up")
		f.update(DT, Vector2.ZERO)
		for e in f.drain():
			match e["type"]:
				"ally-hit": hits += 1
				"ally-windup":
					if e.get("technique", false): techs += 1
				"ally-parry": parries += 1
				"ally-retreat": retreats += 1
				"ally-down": downs += 1
		if f.p_state == "down":
			break
	return [temper, f.stats["wolves_down"], hits, int(f.stats["damage_dealt"]), techs, parries, retreats, downs]
