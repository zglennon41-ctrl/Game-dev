## The balance harness: plays every weapon type, every technique and every temperament
## headlessly and prints tables, so a change to a number can be judged before it is played.
##   npm run balance:game   (godot --headless --path . res://game/tests/balance.tscn)
## Rules are data; this is how the data is read back.
extends Node

const DT := 1.0 / 60.0

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
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
	print("\n== TEMPERAMENTS: two classmates of one temperament, 90 s with the hero standing still, a pack of one beside the locked wolf ==")
	print("%-10s %6s %7s %8s %6s %6s %6s %6s" % ["temper", "felled", "hits", "dealt", "techs", "parry", "retreat", "down"])
	for tp in Data.academy["cohort"]["temperaments"]:
		var r := _cohort(String(tp["id"]))
		print("%-10s %6d %7d %8d %6d %6d %6d %6d" % r)
	get_tree().quit()

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
		if f.w_state == "windup" and f.w_duration - f.w_timer <= 0.1 and f.w_duration - f.w_timer > 0.1 - DT:
			f.input("block-down")
		if f.p_block_held and f.w_state != "windup":
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
		if f.w_state == "windup" and f.w_duration - f.w_timer <= 0.1 and f.w_duration - f.w_timer > 0.1 - DT:
			f.input("block-down")
		if f.p_block_held and f.w_state != "windup":
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
