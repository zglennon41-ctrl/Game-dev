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
	if Array(OS.get_cmdline_user_args()).any(func(a): return a == "--genii" or String(a).begins_with("--genii=")):
		_genii()
		get_tree().quit()
		return
	for a in OS.get_cmdline_user_args():
		# --one=form:instar:key:hand:weapon:health  one fight of the types tables, in full (for looking into a row)
		if String(a).begins_with("--one="):
			var q := String(a).trim_prefix("--one=").split(":")
			var r := _type_run({ "form": q[0], "instar": int(q[1]), "key": q[2] == "1", "hand": q[3], "weapon": q[4], "health": float(q[5]) if q.size() > 5 else 1.0, "order": q[6] if q.size() > 6 else "guard" })
			print(r)
			get_tree().quit()
			return
	if Array(OS.get_cmdline_user_args()).any(func(a): return a == "--types" or String(a).begins_with("--types=")):
		_types()
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

## A genius standing at a form of the tree at a given instar, on a given order, with nothing
## else to it: for the table below.
func _genius_of(form_id: String, instar: int, order: String) -> Genius:
	var g := Genius.at_form(form_id, instar)
	g.order = order
	return g

const GENII_SEEDS := 4

## The rows of the table: for every base of the tree (or the one named: -- --genii=wolf), one
## road down it: its settled form young, its first prong grown, its first finish at its apex.
func _genii_rows(only := "") -> Array:
	var rows: Array = []
	for b in Data.bases():
		if only != "" and only != String(b["id"]):
			continue
		var road := Genius.road_of(String(b["id"]))
		if road.size() == 4:
			rows.append({ "label": "%s (%s)" % [b["name"], b["expression"]], "forms": { 1: road[0], 3: road[2], 6: road[3] } })
	return rows

## The genii in a fight (npm run balance:game -- --genii): each base of the tree at three ages
## on each order, beside the same steady hero, alone, against the Green's Warden. What it has,
## its share of the damage, the blows it kept off its partner, the Will it spent, its falls,
## how long the fight took and what was left of the hero. The first row is the hero alone.
func _genii() -> void:
	var only := ""
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--genii="):
			only = String(a).trim_prefix("--genii=")
	var rows := _genii_rows(only)
	print("\n== GENII: what each base has, by age, down its first road (its moves; * the move only the great have) ==")
	for row in rows:
		var line := "%-22s" % String(row["label"])
		for n in [1, 3, 6]:
			var f: Dictionary = row["forms"][n]
			# a weapon and an item make none of a companion's moves: they have a key (-- --types)
			var of := GeniusTypes.of_form(f)
			if of["written"] and String(of["type"]) != "companion":
				line += "  %d %s: %s" % [n, f["name"], GeniusTypes.key_line(String(of["base"]))]
				continue
			var kind := String(Data.genius_bodies()["silhouettes"].get(f["silhouette"], {}).get("kind", "quadruped"))
			var age: Dictionary = Data.genius()["fight"]["ages"][String(Genius.age_at(n)["id"])]
			var mv: Array = Fight.genius_moves(kind, String(f["expression"]), f["features"], int(age.get("moves", 2))).map(func(m): return String(m["id"]) + (":" + String(m["effect"]) if m.has("effect") else ""))
			var gr := Fight.genius_great(kind, String(f["expression"])) if float(age.get("great", 0.0)) > 0.0 else {}
			line += "  %d %s: %s%s" % [n, f["name"], ", ".join(mv) if not mv.is_empty() else "a nip" if n == 1 else "-", ("  *" + String(gr.get("name", ""))) if not gr.is_empty() else ""]
		print(line)
	print("\n== GENII IN A FIGHT: a steady hero alone with one genius against the Warden of the Cutting, %d fights of up to 240 s each ==" % GENII_SEEDS)
	print("%-22s %-6s %-6s %7s %6s %7s %7s %6s %6s %6s %7s" % ["genius", "instar", "order", "felled", "in", "share", "kept off", "Will", "moves", "falls", "hero"])
	var none := _genius_row("(no genius)", { "none": true })
	print("%-22s %-6s %-6s %7s %6s %7s %7s %6s %6s %6s %7s" % none)
	for row in rows:
		for n in [1, 3, 6]:
			var typed := GeniusTypes.of_form(row["forms"][n])
			var keyed: bool = typed["written"] and String(typed["type"]) != "companion"
			for order in ["guard", "hunt", "hold", "free"]:
				if n < 2 and order in ["hold", "free"]:
					continue
				# a weapon or an item takes no orders: one row, its key used as a bot uses it
				if keyed and order != "guard":
					continue
				var r := _genius_row(String(row["label"]), { "form": row["forms"][n]["id"], "instar": n, "order": order })
				if keyed:
					r[2] = "(key)"
				print("%-22s %-6s %-6s %7s %6s %7s %7s %6s %6s %6s %7s" % r)

func _genius_row(label: String, gspec: Dictionary) -> Array:
	var wins: Array = []
	var share := 0.0
	var kept := 0.0
	var will := 0.0
	var moves := 0.0
	var falls := 0.0
	var hero := 0.0
	for sd in GENII_SEEDS:
		var r := _elite_run("green-warden", 1.0, "steady", "anchor", false, 11 + sd * 17, 240.0, gspec)
		if r["felled"] >= 0.0:
			wins.append(r["felled"])
		share += float(r["g_damage"]) / maxf(1.0, float(r["dealt"]))
		kept += float(r["g_guards"])
		will += float(r["g_will"])
		moves += float(r["g_moves"])
		falls += float(r["g_falls"])
		hero += float(r["hero"])
	wins.sort()
	var n := float(GENII_SEEDS)
	return [label, str(gspec.get("instar", "-")), String(gspec.get("order", "-")), "%d/%d" % [wins.size(), GENII_SEEDS], ("%.0f s" % wins[wins.size() / 2]) if not wins.is_empty() else "-",
		"%.0f%%" % (100.0 * share / n), "%.1f" % (kept / n), "%.0f" % (will / n), "%.1f" % (moves / n), "%.1f" % (falls / n), "%.0f" % (hero / n)]

## One beast, alone in its lair, against a hero of a given Shape and hand at Stage 3, with or
## without two classmates. Returns the row: when it fell, and how the fight ended.
func _elite_run(beast_id: String, health: float, hand: String, shape: String, with_party: bool, seed_value := 11, seconds := 240.0, gspec: Dictionary = {}) -> Dictionary:
	var h := Fight.default_hero()
	h["stage"] = 3
	h["projected"] = true
	h["shape"] = shape
	var cohort := Academy.make_cohort(42, h)
	var opts := { "seed": seed_value, "hero": h, "beast": beast_id, "respawn": false, "arena": Vector2(20, 14), "allies": [cohort[0], cohort[1]] if with_party else [] }
	if gspec.is_empty():
		var ff := Rite.first_form(h, shape, 11)
		opts["genius"] = Rite.birth(h, ff["reading"], ff["name"])
	elif gspec.has("form"):
		opts["genius"] = _genius_of(String(gspec["form"]), int(gspec["instar"]), String(gspec["order"]))
		if String(gspec["order"]) == "hold":
			opts["post"] = Vector2.ZERO   # a post in the middle of the ground, for it to keep
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
		# every hand but a new one uses its genius's key as a bot does (GeniusTypes.bot_wants_key)
		if hand != "new" and gspec.get("key", true) and GeniusTypes.bot_wants_key(f, windup and (hand == "sure" or (hand == "steady" and guard_this))):
			f.input("order")
		if f.p_state == "draw" and f.p_draw >= f.draw_seconds():
			f.input("attack-up")       # a bow genius in the hand: loose at the full draw
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
	return { "g_damage": f.stats["g_damage"], "g_guards": f.stats["g_guards"], "g_will": f.stats["g_will_spent"], "g_falls": f.stats["g_falls"], "g_moves": f.stats["g_moves"], "g_great": f.stats["g_great"],
		"t": f.now, "dealt": f.stats["damage_dealt"], "felled": felled, "hero": f.p_hp, "beast": 100.0 * f.w_hp / float(f.beast["health"]), "hurts": f.stats["hurts"], "parries": f.stats["parries"], "blocks": f.stats["blocks"] }

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

# ===================================================================== the three types of genius
# npm run balance:game -- --types   (or --types=wolf for one base's rows)
# What each type and each role is worth beside a hero, so that a number in
# data/genius-types.json can be judged before it is played (docs/genius-types.md).

const TYPE_SEEDS := 6
const LONG := 2.0        # the Warden's health in the long fights of the first two tables, so a genius has time to tell

## The partners the roles are measured beside: how each fights, and what each lacks.
const PARTNERS := [
	{ "id": "far", "weapon": "musket", "hand": "steady", "health": LONG, "says": "a musket, from seven metres: lacks a front" },
	{ "id": "heavy", "weapon": "hammer", "hand": "steady", "health": LONG, "says": "a maul, slow and heavy: lacks the opening" },
	{ "id": "turner", "weapon": "saber", "hand": "sure", "health": LONG, "says": "a saber, every bite parried: lacks the blow" },
	{ "id": "brawler", "weapon": "short-blade", "hand": "learning", "health": 1.0, "says": "twin blades, strikes out of turn and blocks when it remembers, against the Warden at its own health: lacks staying" },
]

## The order a companion of a role is best given.
const ROLE_ORDER := { "bulwark": "guard", "hunter": "hunt", "harrier": "hunt", "keeper": "guard", "lookout": "guard" }

## One fight: a hero with a weapon and a hand, alone with one genius (or none) against a
## beast. o: weapon, hand, form, instar, order, key (use the genius's key as a bot does),
## beast, seed, seconds. A bot that knows the weapon in its hand, the genius's in its turn.
func _type_run(o: Dictionary) -> Dictionary:
	var h := Fight.default_hero()
	h["stage"] = 3
	h["projected"] = true
	var w := Data.by_id(Data.weapons, String(o.get("weapon", "saber")))
	h["weapon"] = w["id"]
	h["city"] = w["city"]
	var opts := { "seed": int(o.get("seed", 11)), "hero": h, "beast": String(o.get("beast", "green-warden")), "respawn": false, "arena": Vector2(22, 16) }
	if float(o.get("health", 1.0)) != 1.0:
		opts["beast_health"] = roundf(float(Data.beast(String(opts["beast"]))["health"]) * float(o["health"]))
	if String(o.get("form", "")) != "":
		var g := Genius.at_form(String(o["form"]), int(o.get("instar", 0)))
		g.order = String(o.get("order", "guard"))
		opts["genius"] = g
		if g.order == "hold":
			opts["post"] = Vector2.ZERO
	var f := Fight.new(opts)
	var hand := String(o.get("hand", "steady"))
	var use_key: bool = o.get("key", true)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(o.get("seed", 11)) * 3 + 7
	var guard_this := true
	var rng_half := true
	var was_windup := false
	var felled := -1.0
	var keys := 0
	for i in int(float(o.get("seconds", 240.0)) / DT):
		var to_w := f.w_pos - f.p_pos
		var move := Vector2.ZERO
		var windup := f.w_state == "windup" and f.w_target == -1
		if windup and not was_windup:
			guard_this = rng.randf() < 0.67
			rng_half = rng.randf() < 0.5
		was_windup = windup
		match hand:
			"sure":
				if _bite_coming(f) and f.w_target == -1:
					f.input("block-down")
				if f.p_block_held and not windup:
					f.input("block-up")
			"steady":
				if windup and guard_this and not f.p_block_held and f.w_timer > 0.25:
					f.input("block-down")
				if f.p_block_held and not windup and f.w_state != "strike":
					f.input("block-up")
			"learning":
				if windup and rng_half and not f.p_block_held:
					f.input("block-down")
				if f.p_block_held and not windup and f.w_state != "strike":
					f.input("block-up")
		var guarding: bool = windup and (hand == "sure" or (hand == "steady" and guard_this))
		if use_key and f.genius != null and f.g_type != "companion" and GeniusTypes.bot_wants_key(f, guarding):
			f.input("order")
			keys += 1
		if f.pattern_ready():
			f.input("pattern")
		var foe_up := f.w_state not in ["down", "absent"]
		if f.p_state == "pattern" and not f.chain.is_empty():
			var c: float = f.chain["cues"][f.chain["next"]]
			if absf(f.now - c) < DT / 2.0:
				f.input("attack")
		elif f.ranged:
			# the weapon in the hand is a ranged one (the hero's own, or a bow or gun genius taken up)
			if f.style.has("draw"):
				if f.p_state == "free" and foe_up and not f.p_block_held and to_w.length() < float(f.combo[0]["range"]):
					f.input("attack")
				elif f.p_state == "draw" and f.p_draw >= f.draw_seconds():
					f.input("attack-up")
			elif f.p_ammo_max > 0 and f.p_ammo == 0 and f.p_state == "free":
				f.input("reload")
			elif foe_up and not f.p_block_held and (not windup or hand == "new") and f.p_state == "free" and to_w.length() < float(f.combo[0]["range"]):
				f.input("attack")
		elif to_w.length() < 2.6 and not f.p_block_held and foe_up:
			var opening: bool = f.w_state in ["recover", "stagger", "flinch", "idle", "prowl"] and (f.w_state != "recover" or f.w_duration - f.w_timer > 0.45)
			if opening or (f.beast.has("guard") and f.guard_open()) or hand == "new" or (hand == "learning" and guard_this and not windup):
				if hand in ["sure", "steady"] and f.p_will > 40 and f.now >= float(f.p_cooldowns.get(f.tech["id"], 0.0)):
					f.input("technique")
				else:
					f.input("attack")
		# where the hero goes: a far-fighter keeps their distance, the rest close
		var far_fighter: bool = f.ranged
		if f.g_in_hand:
			far_fighter = f.main.get("ranged", false) and f.ranged
		if foe_up:
			if far_fighter:
				if to_w.length() > 8.5 and not windup:
					move = to_w.normalized()
				elif to_w.length() < 5.0 and f.p_state != "draw":
					move = -to_w.normalized()
			elif to_w.length() > 2.0 and (not windup or hand == "new"):
				move = to_w.normalized()
		f.update(DT, move)
		for e in f.drain():
			if e["type"] == "wolf-down" and felled < 0.0:
				felled = f.now
		if f.p_state == "down" or felled >= 0.0:
			break
	return { "felled": felled, "t": f.now, "hero": f.p_hp, "beast": 100.0 * f.w_hp / float(f.beast["health"]), "dealt": f.stats["damage_dealt"], "hurts": f.stats["hurts"], "parries": f.stats["parries"],
		"g_damage": f.stats["g_damage"], "g_guards": f.stats["g_guards"], "g_will": f.stats["g_will_spent"], "g_moves": f.stats["g_moves"], "keys": keys, "g_own": int(f.stats.get("g_own", 0)), "mended": float(f.stats.get("g_mended", 0.0)), "hand": float(f.stats.get("hand_damage", 0.0)), "hits": f.stats["hits"], "hand_hits": int(f.stats.get("hand_hits", 0)), "patterns": f.stats["patterns"] }

## The same fight over several seeds, as one row's numbers.
func _type_row(o: Dictionary) -> Dictionary:
	var wins: Array = []
	var hero := 0.0
	var lost_at := 0.0
	var share := 0.0
	var kept := 0.0
	var hurts := 0.0
	var keys := 0.0
	var own := 0.0
	for sd in TYPE_SEEDS:
		var oo := o.duplicate()
		oo["seed"] = 11 + sd * 17
		var r := _type_run(oo)
		if r["felled"] >= 0.0:
			wins.append(r["felled"])
			hero += float(r["hero"])
		else:
			lost_at += float(r["beast"])
		share += float(r["g_damage"]) / maxf(1.0, float(r["dealt"]))
		kept += float(r["g_guards"])
		hurts += float(r["hurts"])
		keys += float(r["keys"])
		own += float(r["g_own"])
	wins.sort()
	var n := float(TYPE_SEEDS)
	var losses := TYPE_SEEDS - wins.size()
	var mid := float(wins[wins.size() / 2]) if not wins.is_empty() else 240.0
	return { "won": wins.size(), "in": mid if not wins.is_empty() else -1.0, "hero": hero / maxf(1.0, wins.size()), "lost_at": lost_at / maxf(1.0, losses),
		"share": 100.0 * share / n, "kept": kept / n, "hurts": hurts / n, "keys": keys / n, "own": own / n,
		# one number to rank by: fights won first, then what was left of the hero, then how soon
		"score": wins.size() * 1000.0 + hero / maxf(1.0, wins.size()) * 2.0 - mid - lost_at / maxf(1.0, losses) }

func _cell(r: Dictionary) -> String:
	if int(r["won"]) == 0:
		return "0/%d at %.0f%%" % [TYPE_SEEDS, r["lost_at"]]
	return "%d/%d %3.0fs hp%3.0f" % [r["won"], TYPE_SEEDS, r["in"], r["hero"]]

## What a base is, in a few words, for a table.
func _what(base: Dictionary) -> String:
	var T := Data.genius_types()
	var id := String(base["id"])
	var type := GeniusTypes.type_of_class(String(base["class"]))
	match type:
		"weapon": return "weapon (%s)" % String(T["weapon"]["bases"].get(id, {}).get("style", "?"))
		"defense", "ritual": return "%s (%s)" % ["defensive" if type == "defense" else "ritual", String(T["items"].get(id, {}).get("use", {}).get("effect", "?"))]
	return String(T["companions"].get(id, {}).get("role", "companion"))

func _types() -> void:
	var only := ""
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--types="):
			only = String(a).trim_prefix("--types=")
	var T := Data.genius_types()
	# --- 1. every base, at three ages
	print("\n== THE THREE TYPES: every base down its first road, beside a steady saber hero alone against the Warden of the Cutting at %.1f times its health (%d fights of up to 240 s) ==" % [LONG, TYPE_SEEDS])
	print("   a companion is on the order its role is best given; a weapon's and an item's key is used as a bot uses it, and in the last column never used.")
	print("%-12s %-20s %-6s %-18s %6s %6s %6s %5s   %-18s" % ["base", "what it is", "instar", "felled, in, hero", "share", "kept", "hurts", "keys", "key never used"])
	var none := _type_row({ "weapon": "saber", "hand": "steady", "health": LONG })
	print("%-12s %-20s %-6s %-18s %6s %6s %6.1f" % ["(no genius)", "", "", _cell(none), "", "", none["hurts"]])
	for b in Data.bases():
		if only != "" and only != String(b["id"]):
			continue
		var road := Genius.road_of(String(b["id"]))
		if road.size() < 4:
			continue
		var type := GeniusTypes.type_of_class(String(b["class"]))
		var role := String(T["companions"].get(String(b["id"]), {}).get("role", ""))
		for n in [1, 3, 6]:
			var form: Dictionary = road[0] if n == 1 else (road[2] if n == 3 else road[3])
			var o := { "weapon": "saber", "hand": "steady", "form": form["id"], "instar": n, "order": ROLE_ORDER.get(role, "guard"), "health": LONG }
			var r := _type_row(o)
			var never := ""
			if type != "companion":
				var o2 := o.duplicate()
				o2["key"] = false
				never = _cell(_type_row(o2))
			print("%-12s %-20s %-6d %-18s %5.0f%% %6.1f %6.1f %5.1f   %-18s" % [b["id"], _what(b), n, _cell(r), r["share"], r["kept"], r["hurts"], r["keys"], never])
	if only != "":
		return
	# --- 2. the roles, beside the partners they are meant to balance
	print("\n== ROLES AND PARTNERS: a grown companion of each role (a path that keeps to its role), beside four partners, alone against the Warden at %.1f times its health but where a row says otherwise (%d fights each) ==" % [LONG, TYPE_SEEDS])
	for p in PARTNERS:
		print("   %-8s %s" % [p["id"], p["says"]])
	var header := "%-22s" % "companion"
	for p in PARTNERS:
		header += " %-18s" % p["id"]
	print(header)
	var table := {}
	var rows: Array = [{ "label": "(no genius)", "role": "" }]
	for role in GeniusTypes.ROLES:
		for b in Data.bases():
			var c: Dictionary = T["companions"].get(String(b["id"]), {})
			if String(c.get("role", "")) != role:
				continue
			var pure := ""
			for pid in c["paths"]:
				if String(c["paths"][pid]["shade"]) == role:
					pure = pid
			if pure == "":
				continue
			var kids := Data.children_of(pure)
			rows.append({ "label": "%s (%s)" % [role, String(kids[0]["name"]) if not kids.is_empty() else pure], "role": role, "form": String(kids[0]["id"]) if not kids.is_empty() else pure })
			break
	for row in rows:
		var line := "%-22s" % String(row["label"]).left(22)
		table[row["role"]] = {}
		for p in PARTNERS:
			var o := { "weapon": p["weapon"], "hand": p["hand"], "health": p["health"] }
			if row.has("form"):
				o["form"] = row["form"]
				o["instar"] = 3
				o["order"] = ROLE_ORDER.get(String(row["role"]), "guard")
			var r := _type_row(o)
			table[row["role"]][p["id"]] = r
			line += " %-18s" % _cell(r)
		print(line)
	for p in PARTNERS:
		# who wins most often beside this partner; among those, who fells it soonest, and who leaves them safest
		var most := 0
		for role in GeniusTypes.ROLES:
			if table.has(role):
				most = maxi(most, int(table[role][p["id"]]["won"]))
		var soonest := ""
		var safest := ""
		for role in GeniusTypes.ROLES:
			if not table.has(role) or int(table[role][p["id"]]["won"]) < most:
				continue
			var r: Dictionary = table[role][p["id"]]
			if soonest == "" or (most > 0 and float(r["in"]) < float(table[soonest][p["id"]]["in"])) or (most == 0 and float(r["lost_at"]) < float(table[soonest][p["id"]]["lost_at"])):
				soonest = role
			if safest == "" or float(r["hero"]) > float(table[safest][p["id"]]["hero"]):
				safest = role
		print("   beside the %s (won %d of %d at best): soonest with the %s, safest with the %s" % [p["id"], most, TYPE_SEEDS, soonest, safest])
	# --- 3. a second reach: a weapon genius beside a partner whose own weapon has the other reach
	print("\n== A SECOND REACH: a grown weapon genius beside a steady partner whose own weapon has the other reach, alone against the Warden at %.1f times its health (%d fights each) ==" % [LONG, TYPE_SEEDS])
	print("%-12s %-22s %-20s %-20s %-20s" % ["genius", "partner's own weapon", "no genius", "its key never used", "its key used"])
	for b in Data.bases():
		if GeniusTypes.type_of_class(String(b["class"])) != "weapon":
			continue
		var w: Dictionary = T["weapon"]["bases"].get(String(b["id"]), {})
		var mine_ranged: bool = String(Data.room["styles"].get(String(w.get("style", "")), {}).get("kind", "melee")) == "ranged"
		var partner := "saber" if mine_ranged else "musket"
		var road := Genius.road_of(String(b["id"]))
		var o := { "weapon": partner, "hand": "steady", "health": LONG }
		var alone := _cell(_type_row(o))
		o["form"] = road[2]["id"]
		o["instar"] = 3
		var used := _cell(_type_row(o))
		o["key"] = false
		print("%-12s %-22s %-20s %-20s %-20s" % [b["id"], partner, alone, _cell(_type_row(o)), used])
	# --- 4. a learner's First Form: is the Academy's own elite still fair with each type?
	print("\n== A LEARNER'S FIRST FORM: each type young, beside three hands with a saber, alone against the Warden (%d fights each); the key used, and [never used] ==" % TYPE_SEEDS)
	print("%-12s %-20s %-32s %-32s %-20s" % ["base", "what it is", "steady", "learning", "new (never uses it)"])
	var l0 := "%-12s %-20s" % ["(no genius)", ""]
	for hand in ["steady", "learning", "new"]:
		l0 += " %-32s" % _cell(_type_row({ "weapon": "saber", "hand": hand }))
	print(l0)
	for b in Data.bases():
		var type := GeniusTypes.type_of_class(String(b["class"]))
		var role := String(T["companions"].get(String(b["id"]), {}).get("role", ""))
		var line := "%-12s %-20s" % [b["id"], _what(b)]
		for hand in ["steady", "learning", "new"]:
			var o := { "weapon": "saber", "hand": hand, "form": b["settled"]["id"], "instar": 1, "order": ROLE_ORDER.get(role, "guard"), "key": hand != "new" }
			var cell := _cell(_type_row(o))
			if type != "companion" and hand != "new":
				var o2 := o.duplicate()
				o2["key"] = false
				cell += " [%s]" % _cell(_type_row(o2))
			line += " %-32s" % cell
		print(line)
