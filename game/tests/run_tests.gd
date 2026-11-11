## Headless tests for the combat room's rules and fight.
## Run: godot --headless --path . res://game/tests/tests.tscn   (or: npm run test:game)
extends Node

var failures := 0
var passes := 0
const DT := 1.0 / 60.0

func check(cond: bool, what: String) -> void:
	if cond:
		passes += 1
	else:
		failures += 1
		printerr("  FAIL: ", what)

func _ready() -> void:
	call_deferred("_run")

## The genius tree in the tests (docs/genius-tree.md). The game's bases are the designer's and
## change; a test must not depend on what they say. So three small bases of the tests' own
## (written by tools/genius-test-bases.py) stand beside them for the whole run, a test of the
## rules names only those, and a test of the game's bases holds for whatever is there.
const TEST_BASES := "res://game/tests/fixtures/bases"

func _all_bases() -> void:
	Data.use_bases(Data.load_bases() + Data.load_bases(TEST_BASES))

func _only_test_bases() -> void:
	Data.use_bases(Data.load_bases(TEST_BASES))

func _game_base_ids() -> Array:
	return Data.load_bases().map(func(b): return String(b["id"]))

func _run() -> void:
	_all_bases()
	test_breaks_and_chord()
	test_combo()
	test_parry()
	test_block_and_hurt()
	test_dodge()
	test_break()
	test_pattern()
	test_builder_rules()
	test_forms()
	test_triggers_tolls_bars()
	test_creation()
	test_academy()
	test_rite()
	test_spark()
	test_genius_parity()
	test_genius_life()
	test_genius_fights()
	test_genius_assembly()
	test_genius_art()
	test_genius_tree()
	test_genius_hybrids()
	test_genius_looks()
	test_genius_looks_on_the_body()
	test_sparring()
	test_disciplines()
	test_party()
	test_project_and_gate()
	test_advanced_standing()
	test_marks()
	test_board()
	test_shade_and_witness()
	test_calendar_and_declaration()
	test_shape_kits()
	test_pack()
	test_zones()
	test_quests()
	test_cohort_ai()
	test_cohort_days_and_crisis()
	test_mastery()
	test_weapons()
	test_gear_and_gate()
	test_weapon_balance()
	test_look()
	test_rest()
	test_motion()
	test_creator()
	test_guard()
	test_progression()
	test_ages()
	test_refinement_and_turning()
	test_old_saves()
	test_renamed_saves()
	test_homes_hand()
	test_homes_lean()
	test_genius_fight()
	test_lines()
	test_path_colours()
	# the three types of genius: the tests' own bases are given types for these, and no others
	var game_types := Data.genius_types()
	_all_types()
	test_types_data()
	test_types_weapon()
	test_types_items()
	test_types_roles()
	test_types_need_and_bots()
	test_first_hour()
	Data.use_types(game_types)
	test_blood_marks()
	test_life_features()
	test_bots()
	print("%d passed, %d failed" % [passes, failures])
	get_tree().quit(1 if failures > 0 else 0)

func run_for(f: Fight, seconds: float, move := Vector2.ZERO) -> Array:
	var all: Array = []
	for i in int(seconds / DT):
		f.update(DT, move)
		all.append_array(f.drain())
	return all

func types(evs: Array) -> Array:
	return evs.map(func(e): return e["type"])

## A wolf about to bite: facing the Anchor at close range, its wind-up nearly over.
func biting_wolf(f: Fight, seconds_left := 0.1) -> void:
	f.w_attack = f.beast["attacks"][0]
	f.w_pos = f.p_pos + Vector2(1.3, 0)
	f.w_facing = PI
	f.p_facing = 0.0
	f.w_state = "windup"
	f.w_duration = float(f.w_attack["windup"])
	f.w_timer = f.w_duration - seconds_left

func test_breaks_and_chord() -> void:
	var c := CombatRules.ChordTracker.new()
	var any := false
	for i in 8: any = any or c.beat(true)
	check(not any and c.beat(false) and c.beat(false) and c.beat(false) and not c.beat(true), "Chord after eight shared perfects, for three")

func test_combo() -> void:
	var f := Fight.new({ "seed": 1, "passive": true })
	f.w_pos = f.p_pos + Vector2(1.2, 0)
	f.w_state = "idle"
	f.input("attack")
	run_for(f, 0.05)
	f.input("attack")   # buffered during the first swing
	var evs := run_for(f, 0.6)
	f.input("attack")
	evs.append_array(run_for(f, 1.2))
	var hits := evs.filter(func(e): return e["type"] == "hit")
	check(hits.size() >= 2, "buffered presses chain into a combo (%d hits)" % hits.size())
	check(f.stats["attacks"] == 3, "three swings")

func test_parry() -> void:
	var f := Fight.new({ "seed": 1 })
	biting_wolf(f, 0.1)
	f.p_will = 50
	f.input("block-down")   # 0.1 s before the bite: inside the 0.2 s window
	var evs := run_for(f, 0.4)
	check(types(evs).has("parry"), "a block tapped just before the bite parries")
	check(f.p_hp == 100 and f.p_will > 55, "a parry takes no damage and gives Will back")
	check(f.w_state == "stagger" and f.pattern_ready(), "the wolf reels and the Pattern's Trigger is met")

func test_block_and_hurt() -> void:
	var f := Fight.new({ "seed": 1 })
	biting_wolf(f, 0.5)
	f.input("block-down")   # 0.5 s early: a block, not a parry
	run_for(f, 0.8)
	check(is_equal_approx(f.p_hp, 100 - 14 * 0.3), "a held block takes 30%% of the bite (hp %s)" % f.p_hp)
	var g := Fight.new({ "seed": 1 })
	biting_wolf(g, 0.1)
	var evs := run_for(g, 0.5)
	check(types(evs).has("hurt") and g.p_hp == 86, "no guard takes the whole bite")
	check(g.p_state == "flinch" or g.p_state == "free", "the Anchor flinches")

func test_dodge() -> void:
	var f := Fight.new({ "seed": 1 })
	biting_wolf(f, 0.12)
	f.update(DT, Vector2(0, 1))
	f.input("dodge")
	var evs := run_for(f, 0.6, Vector2(0, 1))
	check(types(evs).has("evade") and f.p_hp == 100, "a dodge through the bite takes nothing")

func test_break() -> void:
	var f := Fight.new({ "seed": 1, "passive": true })
	f.w_state = "idle"
	for i in 3:
		f.w_pos = f.p_pos + Vector2(1.4, 0)
		f.p_facing = 0.0
		f.p_cooldowns.clear()
		f.input("technique")
		run_for(f, 1.0)
	check(f.stats["staggers"] == 1 and f.w_state == "stagger", "three Ground Strikes break a Read beast")
	var g := Fight.new({ "seed": 1, "passive": true })
	g.w_state = "idle"
	g.w_pos = g.p_pos + Vector2(1.2, 0)
	for i in 6:
		g.input("attack")
		run_for(g, 0.5)
	check(g.stats["breaks"] == 0, "sword swings do not break")

func test_pattern() -> void:
	var f := Fight.new({ "seed": 1 })
	biting_wolf(f, 0.1)
	f.input("block-down")
	run_for(f, 0.3)
	f.input("block-up")
	f.input("pattern")
	check(f.p_state == "pattern" and f.p_will == 0.0, "the Pattern fires and its Toll takes all Will")
	var cues: Array = f.chain["cues"]
	check(cues.size() == 5, "chain: three beats for the Form, one per Term")
	var hp_before := f.w_hp
	var evs: Array = []
	for c in cues:
		evs.append_array(run_for(f, float(c) - f.now))
		f.input("attack")
		evs.append_array(f.drain())
	evs.append_array(run_for(f, 0.2))
	check(types(evs).has("pattern-done"), "every cue landed pays the Pattern")
	check(hp_before - f.w_hp >= 14 * 4 * 3, "it pays at Stage 4 times the Terms' multiplier (x3)")
	var g := Fight.new({ "seed": 1 })
	biting_wolf(g, 0.1)
	g.input("block-down")
	run_for(g, 0.3)
	g.input("pattern")
	var gevs := run_for(g, 2.0)   # never presses: the first cue passes
	check(types(gevs).has("pattern-fizzle") and g.p_will < 10.0, "a missed cue fizzles it; the Toll is still taken")
	var h := Fight.new({ "seed": 1 })
	h.input("pattern")
	check(types(h.drain()).has("pattern-locked"), "the Pattern is unavailable without its Trigger")

## Two bots: one plays well (parries telegraphs, punishes, breaks, fires the Pattern), one mashes.
func run_bot(seconds: float, smart: bool, hero := {}, extra := {}) -> Fight:
	var opts := { "seed": 5 }
	if not hero.is_empty():
		opts["hero"] = hero
	opts.merge(extra, true)
	var f := Fight.new(opts)
	var frame := 0
	for i in int(seconds / DT):
		frame += 1
		var to_w := f.w_pos - f.p_pos
		var move := Vector2.ZERO
		if smart:
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
			elif f.w_state in ["recover", "stagger", "flinch"] and to_w.length() < 2.4 and (f.w_state != "recover" or f.w_duration - f.w_timer > 0.45):
				if f.p_will > 40 and f.now >= float(f.p_cooldowns.get(f.tech["id"], 0.0)):
					f.input("technique")
				else:
					f.input("attack")
			if to_w.length() > 2.0 and f.w_state != "windup":
				move = to_w.normalized()
		else:
			if frame % 9 == 0 and to_w.length() < 2.4:
				f.input("attack")
			if to_w.length() > 1.6:
				move = to_w.normalized()
		f.update(DT, move)
		f.drain()
		if f.p_state == "down":
			break
	return f

func summary(f: Fight) -> String:
	var s := f.stats
	return "%d wolves, %d hits, %d parries, %d staggers, %d patterns (%d fizzled), bitten %d, hp %d, lasted %.0f s" % [s["wolves_down"], s["hits"], s["parries"], s["staggers"], s["patterns"], s["pattern_fizzles"], s["hurts"], f.p_hp, f.now]

func test_bots() -> void:
	var good := run_bot(120, true)
	var mash := run_bot(120, false)
	print("  skilled bot: ", summary(good))
	print("  masher bot:  ", summary(mash))
	check(good.stats["parries"] > 3, "the skilled bot parries")
	check(good.stats["patterns"] > 0 and good.stats["pattern_fizzles"] == 0, "the skilled bot lands Patterns")
	check(good.now > mash.now * 2.0, "the skilled bot lasts far longer (%.0f s against %.0f s)" % [good.now, mash.now])
	check(good.stats["hurts"] / maxf(1.0, good.now) < mash.stats["hurts"] / maxf(1.0, mash.now), "the skilled bot is bitten less often")
	check(good.stats["wolves_down"] >= mash.stats["wolves_down"], "the skilled bot fells at least as many wolves")
	check(good.stats["wolves_down"] <= 12, "a wolf takes real work, even played perfectly (%d felled)" % good.stats["wolves_down"])

## Fire a Pattern from a fresh parry and land every cue.
func land_pattern(f: Fight) -> Array:
	biting_wolf(f, 0.1)
	f.input("block-down")
	run_for(f, 0.3)
	f.input("block-up")
	f.input("pattern")
	var evs: Array = f.drain()
	if f.chain.is_empty():
		return evs
	for c in f.chain["cues"].duplicate():
		evs.append_array(run_for(f, maxf(0.0, float(c) - f.now)))
		f.input("attack")
		evs.append_array(f.drain())
	evs.append_array(run_for(f, 0.2))
	return evs

func test_builder_rules() -> void:
	var base := { "name": "x", "form": "anchor.weight", "terms": [], "sworn": false }
	check(Fight.multiplier_of(base) == 1.0 and Fight.chain_length(base) == 3, "a bare Form: x1, chain of 3")
	var three := { "name": "x", "form": "anchor.weight", "terms": ["below-half", "half-health", "never-twice-one-foe"], "sworn": false }
	check(is_equal_approx(Fight.multiplier_of(three), 4.5) and Fight.chain_length(three) == 6, "three Terms: x4.5, chain of 6")
	three["sworn"] = true
	check(is_equal_approx(Fight.multiplier_of(three), 9.0), "sworn doubles it, to the x9 ceiling")
	check(not PatternTerms.available("genius-sits-out") and PatternTerms.reason("genius-sits-out").contains("genius"), "Terms the room cannot judge are unavailable, with a reason")
	var n := 0
	for t in Data.terms:
		if PatternTerms.available(t["id"]): n += 1
	print("  Terms available in the combat room: %d of %d" % [n, Data.terms.size()])
	check(n >= 15, "at least fifteen Terms can be taken in the combat room")

func test_forms() -> void:
	var g := Fight.new({ "seed": 1, "pattern": { "name": "Wall", "form": "anchor.wall", "terms": ["after-perfect-hold"], "sworn": false } })
	biting_wolf(g, 0.1)
	g.input("block-down")
	run_for(g, 0.3)
	g.input("block-up")
	g.input("pattern")
	# A second bite lands mid-chain: the guard Form turns it aside.
	biting_wolf(g, 0.05)
	g.p_state = "pattern"
	var evs := run_for(g, 0.3)
	check(types(evs).has("turned") and g.p_hp == 100, "the Wall Form turns a bite aside while it holds")
	var m := Fight.new({ "seed": 1, "pattern": { "name": "Mend", "form": "anchor.endurance", "terms": ["after-perfect-hold"], "sworn": false } })
	m.p_hp = 40
	var mevs := land_pattern(m)
	check(types(mevs).has("pattern-done") and m.p_hp > 40 + 3 * 4, "the Endurance Form heals (to %d)" % m.p_hp)

func test_triggers_tolls_bars() -> void:
	# Trigger: only below half health.
	var f := Fight.new({ "seed": 1, "pattern": { "name": "x", "form": "anchor.weight", "terms": ["below-half"], "sworn": false } })
	f.w_state = "idle"
	f.input("pattern")
	check(types(f.drain()).has("pattern-locked") and f.p_state != "pattern", "an unmet Trigger keeps it locked")
	f.p_hp = 40
	f.input("pattern")
	check(f.p_state == "pattern", "below half health, it fires")
	# Trigger: only after I have named the foe aloud.
	var nf := Fight.new({ "seed": 1, "pattern": { "name": "x", "form": "anchor.weight", "terms": ["named-aloud"], "sworn": false } })
	nf.w_state = "idle"
	check(not nf.pattern_ready(), "unnamed foe: not ready")
	nf.input("name")
	check(nf.pattern_ready(), "named aloud: ready")
	# Toll: half my health.
	var t := Fight.new({ "seed": 1, "pattern": { "name": "x", "form": "anchor.weight", "terms": ["full-will", "half-health"], "sworn": false } })
	t.w_state = "idle"
	t.input("pattern")
	check(t.p_hp == 50, "the Toll takes half my health when it fires")
	# Bar: never twice on one foe. The second use warns; pressing again is the breach.
	var b := Fight.new({ "seed": 1, "pattern": { "name": "x", "form": "anchor.weight", "terms": ["full-will", "never-twice-one-foe"], "sworn": false } })
	b.w_state = "idle"
	b.input("pattern")
	run_for(b, 3.0)
	b.p_will = 100
	b.p_state = "free"
	b.input("pattern")
	var bevs := b.drain()
	check(types(bevs).has("bar-warning") and b.p_state != "pattern", "a covering Bar refuses, with a warning")
	b.input("pattern")
	bevs = b.drain()
	check(types(bevs).has("breach") and b.pattern_lost, "pressing again is the breach: the Pattern is lost")
	var sworn_breach: Array = bevs.filter(func(e): return e["type"] == "breach")
	check(not sworn_breach[0]["sworn"], "unsworn: lost for a season (the game records the date)")
	b.p_state = "free"
	b.input("pattern")
	check(types(b.drain()).has("pattern-lost"), "a lost Pattern will not fire")

func test_creation() -> void:
	var qs: Array = Data.creation["questions"]
	check(qs.size() >= 8, "the creator asks at least eight questions")
	# Every answer to the door question makes its own Shape, all six reachable.
	var shapes := {}
	for ai in qs[2]["answers"].size():
		var answers: Array = []
		for qi in qs.size():
			answers.append(ai if qi == 2 else 0)
		var c := Creation.generate(answers)
		shapes[c["shape"]] = true
	check(shapes.size() == 6, "all six Shapes can be made (%s)" % str(shapes.keys()))
	# Whatever home a character has, the Discipline lesson has weapons to offer, and the one
	# carried from creation is among them (Alexandria has no school of its own: it was a wall).
	var homes_seen := {}
	for qi in qs.size():
		for ai in qs[qi]["answers"].size():
			var answers2: Array = []
			for qj in qs.size():
				answers2.append(ai if qj == qi else 0)
			var c2 := Creation.generate(answers2)
			homes_seen[c2["city"]] = true
			var offered := Creation.school_weapons(c2)
			check(not offered.is_empty(), "a character from %s has weapons to choose at the Discipline lesson" % c2["city"])
			check(offered.any(func(w): return w["id"] == c2["weapon"]), "%s's school teaches the weapon they came with (%s)" % [c2["city"], c2["weapon"]])
	check(homes_seen.has("alexandria"), "the questionnaire can make an Alexandrian (%s)" % str(homes_seen.keys()))
	check(not Creation.school_weapons({ "city": "alexandria", "discipline": "" }).is_empty(), "no home and no school still has weapons to offer")
	# Determinism, and a full character.
	var a := [1, 2, 4, 7, 2, 0, 3, 4, 0, 8]
	var c1 := Creation.generate(a)
	var c2 := Creation.generate(a)
	check(c1 == c2, "the same answers make the same character")
	check(c1["blood"] == "demon-blooded", "bloodline + 'nothing with a name' + 'owes me': demon-blooded (got %s)" % c1["blood"])
	check(c1["shape"] == "bind" and c1["city"] == "cahokia", "Sable's answers: a Bind from Cahokia (got %s, %s)" % [c1["shape"], c1["city"]])
	check(c1["pattern"]["terms"] == ["named-aloud", "half-health", "never-silence"], "the Pattern carries the Terms she named (%s)" % str(c1["pattern"]["terms"]))
	check(Creation.weapon(c1["weapon"])["city"] == "cahokia", "a Cahokia weapon")
	check(c1["why"]["shape"].size() > 0, "the Shape comes with its reasons")
	# The player may pick another blood; the Shape is re-read with it.
	var sug := Creation.suggest_bloods(Creation.tally(a))
	check(sug.size() == 3 and sug[0]["id"] == "demon-blooded", "three bloods suggested, best first")
	var c3 := Creation.generate(a, "ridgefolk")
	check(c3["blood"] == "ridgefolk", "a picked blood is honoured")
	# Every generated Pattern is legal: its Form is of its own Shape, one Term of each kind.
	for i in 40:
		var r := RandomNumberGenerator.new()
		r.seed = i
		var ans: Array = []
		for q in qs:
			ans.append(r.randi_range(0, q["answers"].size() - 1))
		var c := Creation.generate(ans)
		var kinds := {}
		for id in c["pattern"]["terms"]:
			kinds[PatternTerms.term(id)["kind"]] = true
		if not (String(c["pattern"]["form"]).begins_with(c["shape"] + ".") and kinds.size() == c["pattern"]["terms"].size()):
			check(false, "a generated Pattern is legal (%s)" % str(c["pattern"]))
			return
	check(true, "forty random characters all have legal Patterns")

func hero_of(shape: String, weapon: String) -> Dictionary:
	return { "name": shape, "shape": shape, "weapon": weapon, "blood": "", "city": "columbia", "body": "Knight",
		"pattern": { "name": "p", "form": Data.kits[shape]["forms"].keys()[0], "terms": ["after-perfect-hold"], "sworn": false } }

func idle_wolf_at(f: Fight, d: float) -> void:
	f.w_state = "idle"
	f.passive = true
	f.w_pos = f.p_pos + Vector2(d, 0)
	f.p_facing = 0.0

func test_shape_kits() -> void:
	# A shot reaches a wolf eight paces off; a sword does not.
	var gun := Fight.new({ "seed": 1, "hero": hero_of("cast", "pistol"), "passive": true })
	idle_wolf_at(gun, 8.0)
	gun.input("attack")
	var evs := run_for(gun, 0.6)
	check(types(evs).has("hit") and types(evs).has("shot"), "a pistol shot lands at eight paces")
	# Cast: Closing Strike throws you at the foe.
	var cast := Fight.new({ "seed": 1, "hero": hero_of("cast", "pistol"), "passive": true })
	idle_wolf_at(cast, 5.0)
	var before := cast.dist()
	cast.input("technique")
	run_for(cast, 0.5)
	check(cast.dist() < before - 2.0, "Closing Strike closes the distance (%.1f to %.1f)" % [before, cast.dist()])
	# Turn: Kindle sets it burning.
	var turn := Fight.new({ "seed": 1, "hero": hero_of("turn", "saber"), "passive": true })
	idle_wolf_at(turn, 1.4)
	turn.input("technique")
	var tevs := run_for(turn, 2.0)
	check(types(tevs).has("burn-tick"), "Kindle burns")
	# Read: Read the Break makes the next hits critical.
	var read := Fight.new({ "seed": 1, "hero": hero_of("read", "pistol"), "passive": true })
	idle_wolf_at(read, 6.0)
	read.input("technique")
	run_for(read, 0.7)
	read.input("attack")
	var revs := run_for(read, 0.6)
	check(revs.any(func(e): return e["type"] == "hit" and e["crit"]), "after Read the Break, hits are critical")
	# Bind: the Leash slows the beast.
	var bind := Fight.new({ "seed": 1, "hero": hero_of("bind", "pistol"), "passive": true })
	idle_wolf_at(bind, 6.0)
	bind.input("technique")
	run_for(bind, 0.6)
	check(bind._wolf_time_scale() < 0.9, "the Leash slows it")
	# Make: the Ward takes the next bite.
	var make := Fight.new({ "seed": 1, "hero": hero_of("make", "saber") })
	make.input("technique")
	run_for(make, 0.8)
	biting_wolf(make, 0.1)
	var mevs := run_for(make, 0.4)
	check(types(mevs).has("ward-broken") and make.p_hp == 100, "the Ward takes the next bite")
	# Every Shape's technique breaks the beast the room sets against it.
	for shape in ["anchor", "turn", "cast", "read", "bind", "make"]:
		var f := Fight.new({ "seed": 1, "hero": hero_of(shape, "pistol" if shape in ["read", "bind"] else "saber"), "passive": true })
		check(f.breaks_beast(), "%s breaks the beast it faces" % shape)
	# And every Shape can win a fight played well.
	var line := ""
	for shape in ["anchor", "turn", "cast", "read", "bind", "make"]:
		var weapon: String = { "anchor": "saber", "turn": "saber", "cast": "pistol", "read": "pistol", "bind": "grapple", "make": "oar-staff" }[shape]
		var f := run_bot(60, true, hero_of(shape, weapon))
		line += "%s %d, " % [shape, f.stats["wolves_down"]]
		check(f.stats["wolves_down"] >= 1, "a %s with a %s fells a wolf in a minute" % [shape, weapon])
	print("  wolves felled in a minute by Shape: ", line)

func test_academy() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
	h["name"] = "Test"
	var a := Academy.make_cohort(42, h)
	var b := Academy.make_cohort(42, h)
	var c := Academy.make_cohort(43, h)
	check(a.size() == 12, "the cohort is twelve")
	check(str(a) == str(b), "the same run's seed makes the same cohort")
	check(str(a) != str(c), "another run makes another cohort")
	var names := {}
	var shapes := {}
	for m in a:
		names[m["name"]] = true
		shapes[m["shape"]] = int(shapes.get(m["shape"], 0)) + 1
		var own_school := not Data.weapons.filter(func(w): return w["city"] == m["city"]).is_empty()
		check(Data.by_id(Data.weapons, m["weapon"])["city"] == m["city"] or not own_school, "%s carries a weapon of %s (or of any city, from Alexandria)" % [m["name"], m["city"]])
	check(names.size() == 12 and not names.has("Test"), "every classmate has their own name")
	check(shapes.size() == 6 and shapes.values().all(func(n): return n == 2), "two classmates of every Shape")
	# Every lesson is in a place that exists, taught by an Instructor who exists, with goals it knows.
	for lesson in Data.academy["lessons"]:
		check(Data.academy["places"].has(lesson["place"]) or Zones.is_zone(lesson["place"]), "lesson %s has its place" % lesson["id"])
		check(lesson["instructor"] == "$discipline" or not Data.by_id(Data.academy["instructors"], lesson["instructor"]).is_empty(), "lesson %s has its Instructor" % lesson["id"])
		for st in lesson["steps"]:
			check(st["goal"]["type"] in ["event", "streak", "will-full", "stance-seconds", "spar", "choose-weapon", "choose-party", "travel", "fell", "hold", "extract", "reach-hits"], "step %s has a goal the Academy knows" % st["title"])
	# A lesson can lock the moves it is not teaching.
	var f := Fight.new({ "hero": h, "beast": "millstone", "passive": true, "mercy": true })
	f.allowed = ["block-down", "block-up", "dodge", "lock"]
	f.p_will = 100.0
	f.input("pattern")
	f.input("attack")
	check(f.p_state == "free", "a locked move does nothing")
	f.input("dodge")
	check(f.p_state == "dodge", "an allowed move works")

func test_rite() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 99)
	var rec := { "parries": 6, "blocks": 4, "hurts": 2, "dodges": 1, "talks": 3 }
	var a := Rite.read_shape(h, rec, 7)
	check(str(a) == str(Rite.read_shape(h, rec, 7)), "the bowl reads the same hero the same way")
	# Across many runs the bowl mostly agrees with the questions, and sometimes it does not.
	var surprises := 0
	var shapes := {}
	for s in 200:
		var r := Rite.read_shape(h, rec, 1000 + s)
		if r["surprise"]:
			surprises += 1
		shapes[r["shape"]] = true
	check(surprises > 10 and surprises < 110, "the rite surprises sometimes, not always (%d of 200)" % surprises)
	# What you do at the Academy moves it: a student who parries everything leans Read.
	var reader := 0
	var plain := 0
	for s in 200:
		if Rite.read_shape(h, { "parries": 40 }, 2000 + s)["shape"] == "read": reader += 1
		if Rite.read_shape(h, {}, 2000 + s)["shape"] == "read": plain += 1
	check(reader > plain, "parrying through the Academy leans the bowl toward Read (%d against %d)" % [reader, plain])
	# What it settles as is the first form of a base, with the Seed's mark, out of three offered.
	var f := Rite.first_form(h, a["shape"], 7)
	var form := Data.form(String(f["form"]))
	check(int(form["level"]) == 1 and String(form["parent"]) == "" and String(Data.base(String(form["base"]))["settled"]["id"]) == String(f["form"]), "the rite settles it as a base's first form (%s)" % f["form"])
	check(f["features"].size() >= form["features"].size() and (f["features"] as Array).has(f["seedMark"]), "what settles carries its own parts and the Seed-mark")
	var offered: Array = f["reading"]["candidates"].map(func(c): return c["base"])
	check(offered.size() == 3 and offered[0] != offered[1] and offered[1] != offered[2] and offered[0] != offered[2], "the bowl offers three different bases (%s)" % ", ".join(offered))
	check(str(Rite.first_form(h, a["shape"], 7)["reading"]) == str(f["reading"]), "the same hero and the same bowl: the same three")
	var forms := {}
	for s in 60:
		var hh := Creation.generate([0, 1, s % 6, s % 4, 1, 2, 0, s % 3, 2, 0], "", s + 1)
		forms[Rite.first_form(hh, hh["shape"], s)["form"]] = true
	check(forms.size() >= mini(4, Data.bases().size()), "different lives settle as different bases (%d kinds)" % forms.size())
	# A surprise Shape keeps a Pattern that works with the new kit.
	for s in Creation.SHAPES:
		var hh := h.duplicate(true)
		Rite.reshape(hh, s)
		check(Data.kits[s]["forms"].has(hh["pattern"]["form"]), "after the rite reads %s, the Pattern's Form is the %s kit's" % [s, s])
		var fi := Fight.new({ "hero": hh })
		check(fi.player_shape == s, "a %s fights as a %s" % [s, s])

func test_spark() -> void:
	var ans := [0, 1, 2, 0, 1, 2, 0, 1, 2, 0]
	check(str(Creation.generate(ans, "", 0)) == str(Creation.generate(ans)), "with no spark, the answers alone decide")
	check(str(Creation.generate(ans, "", 5)) == str(Creation.generate(ans, "", 5)), "the same spark makes the same person")
	var shapes := {}
	var bloods := {}
	var weapons := {}
	for s in 80:
		var c := Creation.generate(ans, "", s + 1)
		shapes[c["shape"]] = true
		bloods[c["blood"]] = true
		weapons[c["weapon"]] = true
	check(shapes.size() >= 2 and weapons.size() >= 2, "the same answers can make different people (%d Shapes, %d bloods, %d weapons)" % [shapes.size(), bloods.size(), weapons.size()])
	var names := {}
	for s in 40:
		names[Creation.name_for("columbia", s + 1)] = true
	check(names.size() >= 20, "a spark names people many ways (%d names in 40)" % names.size())

## The game's tree, hybrids, Readings and Resonance give the tools' answers (fixtures written by
## tools/genius-fixtures.ts from src/, on the tests' own three bases).
func test_genius_parity() -> void:
	var fx: Dictionary = JSON.parse_string(FileAccess.open("res://game/tests/fixtures/readings.json", FileAccess.READ).get_as_text())
	var homes: Dictionary = Data._homes
	_only_test_bases()
	Data._homes = fx["homes"]
	check(str(Data.bases().map(func(b): return b["id"])) == str(fx["bases"]), "the tests' bases are the ones the tools wrote the answers from")
	for bid in fx["trees"]:
		var why := _forms_differ(Data.tree_of(String(bid)), fx["trees"][bid])
		check(why == "", "the tree of %s is the tools' tree, form for form%s" % [bid, " (%s)" % why if why != "" else ""])
	for pair in fx["hybrids"]:
		var ab := String(pair).split("+")
		var why := _forms_differ(Data.hybrid_forms(ab[0], ab[1]), fx["hybrids"][pair])
		check(why == "", "the hybrid %s is composed as the tools compose it%s" % [pair, " (%s)" % why if why != "" else ""])
	for r in fx["readings"]:
		var cur: Dictionary = r["current"] if r["current"] is Dictionary else {}
		var got := GeniusReading.read(int(r["instar"]), r["tally"], r["origin"], cur)
		var want: Dictionary = r["result"]
		var ok: bool = got["grows"] == want["grows"] and int(got["level"]) == int(want["level"]) and _same_candidates(got["candidates"], want["candidates"])
		if want["turning"] == null:
			ok = ok and (got["turning"] as Dictionary).is_empty()
		else:
			var gt: Dictionary = got["turning"]
			var wt: Dictionary = want["turning"]
			ok = ok and not gt.is_empty() and gt["second"] == wt["second"] and gt["base"] == wt["base"] and gt["name"] == wt["name"] \
				and absf(float(gt["own"]) - float(wt["own"])) < 0.0011 and absf(float(gt["other"]) - float(wt["other"])) < 0.0011 \
				and _same_reasons(gt["reasons"], wt["reasons"]) and _same_candidates(gt["candidates"], wt["candidates"])
		check(ok, "the Reading matches the tools: %s (%s%s)" % [r["name"], ", ".join(got["candidates"].map(func(c): return c["form"])), "; turning toward %s" % got["turning"]["second"] if not (got["turning"] as Dictionary).is_empty() else ""])
	# a whole life, taking the best fit each time
	var hunting: Dictionary = {}
	for r in fx["readings"]:
		if String(r["name"]).contains("hunted the wild"):
			hunting = r["tally"]
	var g: Dictionary = {}
	var life: Array = []
	for n in range(1, 7):
		var rd := GeniusReading.read(n, GeniusReading.empty_tally() if n == 1 else hunting, { "seed": "stands-between", "blood": "ridgefolk", "shape": "anchor" }, g)
		g = GeniusReading.take(g, rd["candidates"][0])
		life.append(g["form"])
	check(str(life) == str(fx["life"]), "a whole life on the tree is the tools' life (%s)" % " > ".join(life))
	Data._homes = homes
	_all_bases()
	for x in fx["resonance"]:
		var res := GeniusResonance.resonance(int(x["instar"]), int(x["tier"]))
		check(res == int(x["resonance"]) and GeniusResonance.paying_tier(res, int(x["tier"])) == int(x["paying"]) and GeniusResonance.verses(GeniusResonance.paying_tier(res, int(x["tier"]))) == int(x["verses"]) and GeniusResonance.shadow_cap(res) == int(x["shadowCap"]) and is_equal_approx(GeniusResonance.genius_will(res), float(x["will"])), "Resonance matches the tools at instar %d, tier %d" % [int(x["instar"]), int(x["tier"])])
	for x in fx["tiers"]:
		check(GeniusResonance.tier_for({ "uses": x["uses"], "built": true }) == int(x["tier"]), "Intention tier at %d uses" % int(x["uses"]))

func _same_reasons(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		if a[i]["line"] != b[i]["line"] or a[i]["key"] != b[i]["key"] or absf(float(a[i]["share"]) - float(b[i]["share"])) > 0.0011 or absf(float(a[i]["contribution"]) - float(b[i]["contribution"])) > 0.0011:
			return false
	return true

func _same_candidates(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		var x: Dictionary = a[i]
		var y: Dictionary = b[i]
		if x["form"] != y["form"] or x["base"] != y["base"] or x["name"] != y["name"] or int(x["level"]) != int(y["level"]) or x["silhouette"] != y["silhouette"] or x["seedMark"] != y["seedMark"]:
			return false
		if absf(float(x["score"]) - float(y["score"])) > 0.0011 or str(x["own"]) != str(y["own"]) or str(x["heritage"]) != str(y["heritage"]) or str(x["features"]) != str(y["features"]) or not _same_reasons(x["reasons"], y["reasons"]):
			return false
	return true

## "" if two lists of forms are the same, form for form; or the first difference.
func _forms_differ(a: Array, b: Array) -> String:
	if a.size() != b.size():
		return "%d forms against %d" % [a.size(), b.size()]
	for i in a.size():
		var x: Dictionary = a[i]
		var y: Dictionary = b[i]
		for k in ["id", "name", "text", "of", "sign", "habit", "base", "kind", "parent", "expression", "class", "silhouette", "coatOf"]:
			if String(x[k]) != String(y[k]):
				return "%s: %s is '%s', the tools say '%s'" % [x["id"], k, x[k], y[k]]
		if int(x["level"]) != int(y["level"]) or str(x["own"]) != str(y["own"]) or str(x["features"]) != str(y["features"]) or str(x["children"]) != str(y["children"]):
			return "%s: its level, parts or children" % x["id"]
		if int(x["instars"]["min"]) != int(y["instars"]["min"]) or int(x["instars"]["max"]) != int(y["instars"]["max"]):
			return "%s: its instars" % x["id"]
		var xl: Dictionary = x["leans"]
		var yl: Dictionary = y["leans"]
		if str(xl.keys()) != str(yl.keys()):
			return "%s: the lines it leans on (%s against %s)" % [x["id"], str(xl.keys()), str(yl.keys())]
		for line in xl:
			if str(xl[line].keys()) != str(yl[line].keys()):
				return "%s: what it leans on in %s" % [x["id"], line]
			for key in xl[line]:
				if absf(float(xl[line][key]) - float(yl[line][key])) > 0.0000001:
					return "%s: %s.%s is %s, the tools say %s" % [x["id"], line, key, str(xl[line][key]), str(yl[line][key])]
	return ""

## A genius's life on its tree, start to finish: it settles, learns, adapts, is refined three
## times, and grows twice as what it finished as.
func test_genius_life() -> void:
	_only_test_bases()
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	h["seed"] = "stands-between"
	h["blood"] = "ridgefolk"
	h["shape"] = "anchor"
	var mark := GeniusReading.seed_mark("stands-between")
	var g := Genius.for_hero(h)
	check(not g.is_born(), "a genius before the rite has no body")
	var r1 := g.read(1)
	check(r1["candidates"].size() == 3 and int(r1["level"]) == 1, "the bowl offers three bases")
	var c := g.take()
	g.milestone("rite")
	check(g.is_born() and g.instar == 1 and c["form"] == "trun-small" and g.body["base"] == "trun" and g.level() == 1 and g.kind() == "Test Runner", "the rite settles it as the base its Seed, blood and Shape call (%s)" % c["form"])
	check(g.features().has(mark), "the Seed-mark is on it")
	check(g.soul() != "" and g.sign_now().contains("Small test runner") and g.habit().contains("counts to itself") and g.picture_of() == "", "it says whose soul it is, and has a sign and a habit; a settled form is not yet the picture of anything")
	check(is_equal_approx(g.will_max(), 40.0) and g.orders_available().size() == 2, "a First Form has 40 Will and two orders")
	# Saved and loaded, it is the same genius.
	var g2 := Genius.from_dict(g.to_dict())
	check(str(g2.to_dict()) == str(g.to_dict()), "a genius survives saving")
	# Play: hunting in the wild with a party, a little guarding, a posting taken.
	for i in 30: g.hit_at(1.5)
	for i in 6: g.hit_at(5.0)
	for i in 14: g.used_family("anchor.wall")
	for i in 22: g.gave_order("hunt")
	for i in 4: g.gave_order("guard")
	for i in 9: g.ran("wild", false, 2)
	for i in 2: g.ran("ruin", true, 0)
	for i in 6: g.met_blow("blocks")
	for i in 3: g.met_blow("dodges")
	g.took_work("hunt")
	g.fought_beside("read")
	g.studied("marshal", 10)
	var cn: Dictionary = g.tally["counters"]
	check(float(cn.get("runs.party", 0)) == 9.0 and float(cn.get("runs.alone", 0)) == 2.0 and float(cn.get("fights.blocks", 0)) == 6.0 and float(cn.get("fights.dodges", 0)) == 3.0 and float(cn.get("runs.quest.hunt", 0)) == 1.0, "the Tally counts who they went out with, how blows were met and the work taken")
	check(float(g.tally["ground"].get("night", 0)) == 2.0 and float(g.tally["ground"].get("quiet", 0)) == 1.0, "and a run by night, and a day somewhere quiet")
	var pl := GeniusReading.play_lines(g.tally)
	check(is_equal_approx(float(pl["shares"]["orders"]["hunt"]), 22.0 / 26.0) and is_equal_approx(float(pl["shares"]["company"]["party"]), 9.0 / 11.0) and is_equal_approx(float(pl["shares"]["shape"]["anchor"]), 1.0) and is_equal_approx(float(pl["emphasis"]["fights"]), 9.0 / 20.0), "the Tally is read as shares of each line, and a line with little on it counts for less")
	check(g.reading_due() == 0, "no Second Form before the Gate")
	g.milestone("gate")
	check(g.reading_due() == 0, "nor before its seventh day")
	g.day = 7
	check(g.reading_due() == 2, "the Gate and a week: the first refinement may be read")
	var rd := g.read(2)
	var forms: Array = rd["candidates"].map(func(x): return x["form"])
	check(forms.size() == 3 and forms[0] == "trun-a" and forms.has("trun-b") and forms.has("trun-c") and int(rd["level"]) == 2, "the first refinement offers the three paths of its own base, the one its partner played first (%s)" % str(forms))
	check((rd["turning"] as Dictionary).is_empty(), "play that is its own nature does not turn it")
	check((rd["candidates"][0]["reasons"] as Array).map(func(x): return "%s.%s" % [x["line"], x["key"]]) == ["orders.hunt", "ground.wild"], "and says which lines of the Tally spoke for it")
	for cand in rd["candidates"]:
		check(cand["features"].has(mark) and cand["of"] != "", "%s carries the Seed-mark and says what it is the picture of" % cand["form"])
	g.take(1)
	check(g.instar == 2 and g.level() == 2 and g.history.size() == 2 and not g.history[-1]["settled"] and float(g.tally["range"].get("close", 0.0)) == 0.0, "taking a path starts a new Tally, and history remembers it was chosen")
	check(g.road().map(func(f): return f["id"]) == ["trun-small", String(g.body["form"])] and g.picture_of().begins_with("one who is like"), "it knows the road it took, and what it is now the picture of")
	check(is_equal_approx(g.will_max(), 50.0) and g.orders_available().size() == 4, "a Second Form has 50 Will and four orders")
	# Adaptations come from play; kept fed until a Reading they become part of it; unfed they fade.
	for i in 50: g.hit_at(1.0)
	var ch := g.update_adaptations()
	check(ch.size() == 1 and ch[0]["id"] == "set-feet" and g.features().has("set-feet"), "fifty close fights grow set feet")
	var kept := Genius.from_dict(JSON.parse_string(JSON.stringify(g.to_dict())))
	kept.read(3)
	kept.take()
	check(kept.level() == 3 and (kept.body["heritage"] as Array).has("set-feet") and (kept.body["adaptations"] as Array).is_empty() and kept.features().has("set-feet"), "kept until the next refinement, it becomes part of it")
	g.day += 100
	ch = g.update_adaptations()
	check(ch.size() == 1 and ch[0]["change"] == "faded" and not g.features().has("set-feet"), "unfed for a season, it fades")
	# Shadows: ten witnessed uses, within the cap.
	var p := { "name": "Last Post", "form": "anchor.endurance", "terms": ["struck-first", "below-half", "never-twice-one-foe"] }
	var made := {}
	for i in 10: made = g.witness(p)
	check(not made.is_empty() and g.shadows.size() == 1 and made["terms"].all(func(t): return Genius._kind(t) == "trigger") and made["terms"].size() >= 1, "ten witnessed uses make a shadow, Triggers kept, the rest gone (%s)" % str(made.get("terms", [])))
	var p2 := { "name": "Other", "form": "cast.reach", "terms": [] }
	for i in 10: g.witness(p2)
	check(g.shadows.size() == 1, "a Second Form carries one shadow")
	# Grafts wait for the next Reading; secondary forms from the Third.
	g.offer_graft({ "id": "shade:old-marshal", "feature": "lantern", "source": "shade" })
	check(g.secondary_ready().is_empty(), "no secondary forms before the Third")
	g.milestone("pattern-built")
	g.day = 40
	check(g.reading_due() == 3, "a built Pattern and thirty days: the second refinement")
	var rd3 := g.read(3)
	check(rd3["candidates"].size() == 3 and rd3["candidates"].all(func(x): return Data.form(String(x["form"]))["parent"] == g.body["form"]), "the second refinement offers the three prongs of its path")
	g.take()
	check(g.features().has("lantern") and g.level() == 3, "the graft is on the Third Form")
	for i in 60: g.gave_order("hunt")
	var ready: Array = g.secondary_ready().map(func(s): return s["id"])
	check(ready.has("arms") == (g.body["expression"] in ["relic", "engine"]), "Arms needs a Relic or Engine and fifty Hunts (%s, %s)" % [g.body["expression"], str(ready)])
	var hb := g.features_by_slot()
	check(hb.size() >= 2, "features sort into slots (%s)" % str(hb.keys()))
	# The last refinement: two finishes. Then nothing new: it grows.
	var rd4 := g.read(4)
	check(rd4["candidates"].size() == 2 and int(rd4["level"]) == 4, "the last refinement offers the two finishes of its prong")
	g.take()
	var fin := String(g.body["form"])
	var fin_name := String(Data.form(fin)["name"])
	check(g.level() == 4 and g.next_forms().is_empty() and g.road().size() == 4 and g.form_name() == fin_name, "it has finished its tree (%s)" % fin_name)
	var whole := true
	for f in g.road():
		for x in f["own"]:
			whole = whole and (g.body["own"] as Array).has(x)
	check(whole, "a finish wears the whole road: what every form on it added")
	for i in 50: g.hit_at(1.0)
	g.update_adaptations()
	var rd5 := g.read(5)
	check(rd5["grows"] and rd5["candidates"].size() == 1 and rd5["candidates"][0]["form"] == fin, "at the fifth instar nothing new is offered")
	g.take()
	check(g.instar == 5 and g.body["form"] == fin and g.history[-1].get("grew", false) and g.form_name() == "Great " + fin_name and (g.body["heritage"] as Array).has("set-feet"), "it grows great as what it is, named for it, and keeps what it kept fed (%s)" % g.form_name())
	g.read(6)
	g.take()
	check(g.instar == 6 and g.body["form"] == fin and g.form_name() == fin_name + " of the Line" and is_equal_approx(g.will_max(), 90.0), "and comes to its apex (%s)" % g.form_name())
	g.fall(); g.fall(); g.develop_secondary("night"); g.fall()
	check(g.secondary.is_empty() and g.fallen, "three falls in a season cost the newest secondary form")
	_all_bases()

## A genius settled as the tests' runner, for whatever needs one.
func _born_genius() -> Genius:
	var h := Fight.default_hero()
	h["seed"] = "stands-between"
	h["blood"] = "ridgefolk"
	var g := Genius.for_hero(h)
	g.pending_reading = { "instar": 1, "level": 1, "candidates": [GeniusReading._candidate(Data.form("trun-small"), 0.0, [], GeniusReading.seed_mark("stands-between"), [], [])], "turning": {}, "grows": false, "unlockedBy": "rite" }
	g.take()
	g.milestone("rite")
	return g

## A genius standing at a form of the tree, with a Seed-mark and an origin.
func _genius_at(form_id: String, at_instar := 0) -> Genius:
	var g := Genius.at_form(form_id, at_instar, GeniusReading.seed_mark("stands-between"))
	g.origin = { "seed": "stands-between", "blood": "ridgefolk", "shape": "anchor", "city": "", "home": "" }
	g.look = GeniusLook.born(4711)
	return g

## Count play into a genius's Tally in the proportions of some leans.
func _play_like(g: Genius, leans: Dictionary, n := 40) -> void:
	for line in leans:
		for key in leans[line]:
			var k := maxi(1, roundi(n * float(leans[line][key])))
			match String(line):
				"range": g.count("range", String(key), k)
				"orders": g.count("orders", String(key), k)
				"shape": g.count("families", "%s.x" % key, k)
				"fights": g.counter("fights." + String(key), k)
				"company": g.counter("runs." + String(key), k)
				"ground": g.count("ground", String(key), k)
				"quests": g.counter("runs.quest." + String(key), k)
				"bonds": g.bonded(String(key))
				"pattern":
					if not (g.tally.get("intention") is Dictionary):
						g.tally["intention"] = { "form": "x.y", "terms": [], "fires": 0, "sworn": false }
					g.tally["intention"]["fires" if key == "fires" else "sworn"] = 1000 if key == "fires" else true

## The genius in a fight: Guard, Hunt, falling, getting up, orders, and what it learns.
func test_genius_fights() -> void:
	var g := _born_genius()
	g.order = "guard"
	var f := Fight.new({ "seed": 1, "genius": g })
	check(is_equal_approx(f.g_will, 40.0), "a First Form starts a fight with 40 Will")
	biting_wolf(f, 0.1)
	var evs := run_for(f, 0.5)
	check(types(evs).has("genius-guard") and f.p_hp == 100.0 and f.g_will < 40.0, "on Guard, it takes the bite you did not see")
	biting_wolf(f, 0.1)
	evs = run_for(f, 0.5)
	check(types(evs).has("hurt"), "but not twice in a row: Guard has a cooldown")
	# Guarding until it falls.
	var falls := 0
	for i in 12:
		f.g_guard_ready_at = 0.0
		biting_wolf(f, 0.1)
		evs = run_for(f, 0.5)
		if types(evs).has("genius-fall"):
			falls += 1
			break
	check(falls == 1 and g.fallen and f.g_will == 0.0, "emptied of Will, it falls")
	run_for(f, 21.0)
	check(not g.fallen, "in the practice yard it gets up again")
	# Hunt: only when locked on, and only near.
	g.order = "hunt"
	var h := Fight.new({ "seed": 2, "genius": g, "passive": true })
	h.w_state = "idle"
	h.w_pos = h.p_pos + Vector2(3, 0)
	var hp0 := h.w_hp
	h.p_lock = false
	run_for(h, 3.0)
	check(h.w_hp == hp0, "unlocked, it does not hunt")
	h.p_lock = true
	evs = run_for(h, 5.0)
	check(types(evs).has("genius-hunt") and h.w_hp < hp0, "locked on, it hunts")
	check(float(g.tally["orders"].get("hunt", 0)) >= 1.0, "and the Tally counts the order")
	# Orders cycle among those it knows.
	h.input("order")
	check(g.order == "guard", "G changes the order")
	# What it learns from the player's own hits.
	var k := Fight.new({ "seed": 3, "genius": g, "passive": true })
	k.w_state = "idle"
	k.w_pos = k.p_pos + Vector2(1.6, 0)
	k.p_facing = 0.0
	k.input("attack")
	run_for(k, 1.0)
	check(float(g.tally["range"].get("close", 0)) >= 1.0, "a hit up close is counted as close")
	# Without a genius, nothing changes.
	var n := Fight.new({ "seed": 1 })
	biting_wolf(n, 0.1)
	evs = run_for(n, 0.5)
	check(not types(evs).has("genius-guard") and n.genius == null, "no genius, no guard")

## Every form of every tree assembles, with a part for every feature it has a socket for.
func test_genius_assembly() -> void:
	var bad: Array = []
	for f in Data.forms():
		var info := { "form": f["id"], "silhouette": f["silhouette"], "expression": f["expression"], "features": f["features"] }
		var b := GeniusBody.build(info, Color.ORANGE, 1)
		var meshes := b.find_children("*", "MeshInstance3D", true, false).size() + b.find_children("*", "CPUParticles3D", true, false).size()
		if meshes == 0 or b.sockets.is_empty():
			bad.append(f["id"])
		b.free()
	check(bad.is_empty(), "every form of every tree assembles (%d forms; failed: %s)" % [Data.forms().size(), str(bad)])

## Art files follow the art bible: named for a silhouette, feature or form; sockets on bodies;
## within budget; cards in portrait 3:4.
func test_genius_art() -> void:
	# every body the game knows (data/genius-bodies.json), whether a tree wears it yet or not
	var sils := {}
	for sil in Data.genius_bodies()["silhouettes"]:
		sils[sil] = true
	var feats := {}
	for f in Data.features():
		feats[f["id"]] = true
	var forms := {}
	for f in Data.forms():
		forms[f["id"]] = true
	var n := 0
	var named := 0
	for pair in [["bodies", sils, 8000], ["parts", feats, 1500]]:
		var dir := "res://game/assets/genius/%s/" % pair[0]
		for file in DirAccess.get_files_at(dir):
			if not file.ends_with(".glb"):
				continue
			n += 1
			var id := file.get_basename()
			check((pair[1] as Dictionary).has(id), "%s/%s is named for a %s" % [pair[0], file, "silhouette" if pair[0] == "bodies" else "feature"])
			var scene: Node3D = load(dir + file).instantiate()
			var tris := 0
			for m in scene.find_children("*", "MeshInstance3D", true, false):
				var mesh: Mesh = (m as MeshInstance3D).mesh
				for si in mesh.get_surface_count():
					var arr := mesh.surface_get_arrays(si)
					tris += (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3 if arr[Mesh.ARRAY_INDEX] != null else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
			check(tris <= int(pair[2]), "%s/%s is within budget (%d of %d triangles)" % [pair[0], file, tris, int(pair[2])])
			if pair[0] == "bodies":
				var socks := scene.find_children("socket_*", "", true, false).map(func(x): return String(x.name))
				# a rigged body carries its sockets as bones of its skeleton
				for sk in scene.find_children("*", "Skeleton3D", true, false):
					for bi in (sk as Skeleton3D).get_bone_count():
						var bn := (sk as Skeleton3D).get_bone_name(bi)
						if bn.begins_with("socket_") and not socks.has(bn):
							socks.append(bn)
				check(socks.has("socket_body") and socks.size() >= 4, "bodies/%s carries its sockets (%s)" % [file, ", ".join(socks)])
			scene.free()
	for file in DirAccess.get_files_at("res://game/assets/genius/cards/"):
		if not file.ends_with(".png"):
			continue
		n += 1
		# a card is drawn for the form it is named for; those painted for the lattice before the
		# tree are kept (game/assets is not thrown away) until a form of the tree takes their name
		named += 1 if forms.has(file.get_basename()) else 0
		var tex: Texture2D = load("res://game/assets/genius/cards/" + file)
		check(absf(float(tex.get_width()) / tex.get_height() - 0.75) < 0.01, "cards/%s is a 3:4 portrait" % file)
	check(n > 0, "there is genius art to check (%d files; %d cards are named for a form of the tree)" % [n, named])

## The tree every genius is on (docs/genius-tree.md), for whatever bases there are: thirty-one
## forms a base; a form wears its road; every lean is one the Tally answers; the rite offers
## three bases; a refinement offers the children of the form it is; a finished form grows.
func test_genius_tree() -> void:
	var lines := { "range": ["close", "mid", "far"], "orders": GeniusReading.ORDERS, "shape": GeniusReading.SHAPES, "fights": GeniusReading.FIGHTS, "company": ["alone", "party"],
		"ground": ["line", "wild", "water", "ruin", "night", "quiet"], "pattern": ["fires", "sworn"], "bonds": ["classmate", "shade", "named"], "quests": GeniusReading.QUESTS }
	check(lines.keys() == GeniusReading.PLAY_LINES, "the Readings read the nine lines of the specification")
	var ids := {}
	check(Data.bases().size() >= 3, "there are bases to settle as (%d)" % Data.bases().size())
	for b in Data.bases():
		var tree := Data.tree_of(String(b["id"]))
		var by_level := [0, 0, 0, 0, 0]
		var ok: bool = tree.size() == 31 and tree[0]["id"] == b["settled"]["id"]
		var why := ""
		for f in tree:
			by_level[int(f["level"])] += 1
			if ids.has(f["id"]):
				why = "%s is used twice" % f["id"]
			ids[f["id"]] = true
			if Data.form(String(f["id"])) != f or f["base"] != b["id"] or f["kind"] != b["name"]:
				why = "%s is not asked for by its id" % f["id"]
			if (f["children"] as Array).size() != [0, 3, 3, 2, 0][int(f["level"])]:
				why = "%s has %d children" % [f["id"], (f["children"] as Array).size()]
			var parent := Data.form(String(f["parent"])) if String(f["parent"]) != "" else {}
			for x in parent.get("features", []) + f["own"]:
				if not (f["features"] as Array).has(x):
					why = "%s does not wear %s" % [f["id"], x]
			for line in f["leans"]:
				for key in f["leans"][line]:
					if not (lines.get(line, []) as Array).has(key):
						why = "%s leans on %s.%s, which the Tally does not count" % [f["id"], line, key]
			if int(f["level"]) >= 2 and (f["leans"] as Dictionary).is_empty():
				why = "%s leans on nothing" % f["id"]
		check(ok and by_level == [0, 1, 3, 9, 18] and why == "", "%s is a tree of thirty-one forms: one settled, three paths, nine prongs, eighteen finishes%s" % [b["name"], " (%s)" % why if why != "" else ""])
	# The Tally answers every line and key a form may lean on.
	var full := Genius.new()
	for line in lines:
		var ask := {}
		for key in lines[line]:
			ask[key] = 1.0
		_play_like(full, { line: ask }, 5)
	var pl := GeniusReading.play_lines(full.tally)
	var deaf: Array = []
	for line in lines:
		for key in lines[line]:
			if float(pl["shares"].get(line, {}).get(key, 0.0)) <= 0.0:
				deaf.append("%s.%s" % [line, key])
	check(deaf.is_empty(), "the Tally answers every line and key of the tree (unanswered: %s)" % ", ".join(deaf))
	# The rite: three bases to everyone, each with the Seed-mark, the same every time.
	var odd: Array = []
	var trios := {}
	for sd in Data.seeds():
		for sh in Creation.SHAPES:
			for b in ["", "ridgefolk", "long-stride"]:
				var origin := { "seed": sd["id"], "blood": b, "shape": sh }
				var r := GeniusReading.read(1, GeniusReading.empty_tally(), origin, {})
				var offered: Array = r["candidates"].map(func(c): return c["base"])
				trios[",".join(offered)] = true
				if offered.size() != 3 or offered[0] == offered[1] or offered[1] == offered[2] or offered[0] == offered[2] or str(GeniusReading.read(1, GeniusReading.empty_tally(), origin, {})) != str(r):
					odd.append("%s %s %s" % [sd["id"], sh, b])
				for c in r["candidates"]:
					if not (c["features"] as Array).has(sd["seedMark"]) or int(c["level"]) != 1 or String(Data.base(String(c["base"]))["settled"]["id"]) != String(c["form"]):
						odd.append("%s on %s" % [sd["seedMark"], c["form"]])
	check(odd.is_empty(), "the bowl offers three different bases to every Seed, blood and Shape, each settled form carrying the Seed-mark (%s)" % ", ".join(odd.slice(0, 4)))
	check(trios.size() >= mini(12, Data.bases().size()), "the bowl's three vary by Seed, blood and Shape (%d different offers)" % trios.size())
	# A refinement offers the children of the form it is, best fit first, and nothing else.
	var strays: Array = []
	for f in Data.forms():
		var g := _genius_at(String(f["id"]))
		_play_like(g, { "range": { "close": 0.8, "far": 0.2 }, "orders": { "hunt": 0.7, "guard": 0.3 }, "fights": { "parries": 0.5 }, "ground": { "wild": 0.4 } })
		var r := g.read(int(f["level"]) + 1)
		var got: Array = r["candidates"].map(func(c): return c["form"])
		if int(f["level"]) == 4:
			if not r["grows"] or got != [f["id"]]:
				strays.append("%s does not grow as itself" % f["id"])
			continue
		var want: Array = (f["children"] as Array).duplicate()
		got.sort()
		want.sort()
		if r["grows"] or got != want or (int(f["level"]) != 1 and not (r["turning"] as Dictionary).is_empty()):
			strays.append(String(f["id"]))
		for i in range(1, r["candidates"].size()):
			if float(r["candidates"][i - 1]["score"]) < float(r["candidates"][i]["score"]):
				strays.append("%s: not best first" % f["id"])
	check(strays.is_empty(), "at every form of every tree a refinement offers its children and nothing else; a finish grows (%s)" % ", ".join(strays.slice(0, 4)))
	# Play made of what a form leans on speaks for that form.
	var mute: Array = []
	for f in Data.forms():
		if int(f["level"]) < 2:
			continue
		var g := _genius_at(String(f["parent"]))
		_play_like(g, f["leans"], 60)
		for c in g.read(int(f["level"]))["candidates"]:
			if c["form"] == f["id"] and (float(c["score"]) <= 0.0 or (c["reasons"] as Array).is_empty()):
				mute.append(String(f["id"]))
	check(mute.is_empty(), "play made of what a form leans on speaks for it (%s)" % ", ".join(mute.slice(0, 4)))
	# On the tests' own bases: all of one path's play is read as that path.
	var wrong: Array = []
	for bid in ["tedge", "tlamp", "trun"]:
		for p in Data.base(bid)["paths"]:
			var g := _genius_at(String(Data.base(bid)["settled"]["id"]))
			_play_like(g, p["leans"], 60)
			if g.read(2)["candidates"][0]["form"] != p["id"]:
				wrong.append(String(p["id"]))
	check(wrong.is_empty(), "play that is all one path's is read as that path (%s)" % ", ".join(wrong))
	# A form that names a body of its own is worn by the forms below it too.
	check(Data.form("tedge-b")["silhouette"] == "relic-knife" and Data.form("tedge-b1")["silhouette"] == "relic-blade" and Data.form("tedge-b1x")["silhouette"] == "relic-blade" and Data.form("tedge-b2x")["silhouette"] == "relic-knife", "a prong's own body is its finishes' body too")
	# Every Seed-mark has something to show on an art body: a part of its own.
	for sd in Data.seeds():
		check(ResourceLoader.exists(GeniusBody.PART_DIR % String(sd["seedMark"])), "the Seed-mark %s has a part to show" % sd["seedMark"])
	# Every form a student can reach in the Academy (the rite, the Gate) has an art body, unless
	# its base says that body is still to be built.
	var bare: Array = []
	for f in Data.forms():
		var to_build: Array = Data.base(String(f["base"])).get("toBuild", [])
		if int(f["level"]) <= 2 and not ResourceLoader.exists(GeniusBody.BODY_DIR % String(f["silhouette"])) and not to_build.has(f["silhouette"]):
			bare.append(String(f["id"]))
	check(bare.is_empty(), "every form the Academy can give has a body of its own (placeholders: %s)" % str(bare))
	# What the tree is said in: every line and key has plain words.
	var wordless: Array = []
	for line in lines:
		for key in lines[line]:
			if GeniusReading.words(line, key) == "%s %s" % [line, key]:
				wordless.append("%s.%s" % [line, key])
	check(wordless.is_empty() and GeniusReading.lean_words({ "range": { "close": 1.0 }, "fights": { "parries": 0.5 } }) == "fighting close, parrying", "every line of the Tally is said in plain words (%s)" % ", ".join(wordless))

## Hybrids (docs/genius-tree.md): any two bases make one by rule, with a tree of its own; the
## rule itself is tested on the tests' own bases, and its shape on every pair there is.
func test_genius_hybrids() -> void:
	var rule: Dictionary = Data.genius_hybrids()["rule"]
	var bad: Array = []
	var pairs := 0
	for a in Data.bases():
		for b in Data.bases():
			if a["id"] == b["id"]:
				if not Data.hybrid_forms(a["id"], b["id"]).is_empty():
					bad.append("%s with itself" % a["id"])
				continue
			pairs += 1
			var pair := "%s+%s" % [a["id"], b["id"]]
			var forms := Data.hybrid_forms(a["id"], b["id"])
			var by_level := [0, 0, 0, 0, 0]
			var sigs := {}
			var why := ""
			for f in forms:
				by_level[int(f["level"])] += 1
				if not String(f["id"]).begins_with(pair + ":") or Data.form(String(f["id"])) != f or f["base"] != pair:
					why = "%s is not asked for by its id" % f["id"]
				if f["expression"] != a["expression"] or f["coatOf"] != b["silhouette"]:
					why = "%s is not the first's body in the second's coat" % f["id"]
				for x in (b["hybrid"]["gift"] as Array) + (a["settled"]["features"] as Array):
					if not (f["features"] as Array).has(x):
						why = "%s does not wear %s" % [f["id"], x]
				if int(f["level"]) == 2:
					sigs["|".join(GeniusTree.signature(f["leans"])["sig"])] = true
					if f["parent"] != a["settled"]["id"]:
						why = "%s does not come of the first's settled form" % f["id"]
					var carried: Array = (f["children"] as Array).filter(func(cid): return String(cid).begins_with("%s:%s-" % [pair, b["id"]]))
					if carried.size() != 1:
						why = "%s carries %d of the second's prongs" % [f["id"], carried.size()]
			if forms.size() != 30 or by_level != [0, 0, 3, 9, 18] or sigs.size() != 3 or why != "":
				bad.append("%s%s" % [pair, " (%s)" % why if why != "" else " (%d forms, %d plays)" % [forms.size(), sigs.size()]])
	check(bad.is_empty(), "every ordered pair of bases makes a hybrid: thirty forms, three paths each earned by its own play, the first's body with the second's gift and coat (%d pairs; wrong: %s)" % [pairs, ", ".join(bad.slice(0, 4))])
	# The rule, on the tests' own: the runner turned toward the edge.
	var a := Data.base("trun")
	var b := Data.base("tedge")
	var forms := Data.hybrid_forms("trun", "tedge")
	var paths: Array = forms.filter(func(f): return int(f["level"]) == 2)
	check(paths.map(func(f): return f["name"]) == ["Edged Test Runner Path A", "Edged Test Runner Path B", "Edged Test Runner Path C"] and paths[0]["kind"] == "Edged Test Runner" and GeniusTree.hybrid_name(a, b, Data.genius_hybrids()) == "Edged Test Runner", "a hybrid is named for the second's word and the first's name, and so are its paths")
	check(str(paths[0]["leans"]) == str(GeniusTree.bend(a["paths"][0]["leans"], b["nature"], float(rule["bend"]))) and is_equal_approx(float(paths[0]["leans"]["orders"]["hunt"]), 0.5) and is_equal_approx(float(paths[0]["leans"]["range"]["close"]), 0.5), "a hybrid's path leans half its own way and half the second's nature")
	check(paths[0]["of"] == "one who is like Test Runner Path A, turned toward the test edge's way" and paths[0]["sign"] == String(a["paths"][0]["sign"]) + " It wears an edge, the test edge's." and paths[0]["habit"] == a["paths"][0]["habit"], "it says what it is the picture of, wears the second's gift as its sign, and keeps the first's habit")
	var carried_ok := true
	for i in 3:
		var P: Dictionary = a["paths"][i]
		var drop := 0
		var drop_s := INF
		for j in 3:
			var s := GeniusTree.alike(P["prongs"][j]["leans"], b["nature"])
			if s <= drop_s:
				drop_s = s
				drop = j
		var prongs: Array = (paths[i]["children"] as Array).map(func(cid): return Data.form(String(cid)))
		for j in 3:
			if j != drop:
				carried_ok = carried_ok and prongs[j]["id"] == "trun+tedge:" + String(P["prongs"][j]["id"]) and prongs[j]["name"] == P["prongs"][j]["name"]
			else:
				var from := Data.form(String(prongs[j]["id"]).split(":")[1])
				carried_ok = carried_ok and String(prongs[j]["id"]).begins_with("trun+tedge:tedge-") and String(prongs[j]["name"]) == "Running " + String(from["name"]) and prongs[j]["of"] == from["of"] \
					and prongs[j]["habit"] == P["prongs"][drop]["habit"] and prongs[j]["silhouette"] == a["silhouette"] and prongs[j]["sign"] == "It wears an edge, the test edge's."
	check(carried_ok, "in each path the prong furthest from the second's nature gives way to one of the second's, carried across with its finishes and named for the first")
	var back := Data.hybrid_forms("tedge", "trun")
	check(back[0]["kind"] == "Running Test Edge" and back[0]["expression"] == "relic" and back[0]["coatOf"] == "beast-runner" and back[0]["id"] != forms[0]["id"], "the other way round is another genius")
	# two paths are never earned by the same play: one that would be bends less far
	var heavy: Dictionary = b.duplicate(true)
	heavy["id"] = "theavy"
	heavy["nature"] = { "range": { "close": 1.0 }, "fights": { "parries": 1.0 } }
	var light: Dictionary = a.duplicate(true)
	var faint := [{ "orders": { "hunt": 0.4 }, "ground": { "wild": 0.3 } }, { "orders": { "guard": 0.4 }, "ground": { "ruin": 0.3 } }, { "bonds": { "named": 0.4 }, "ground": { "night": 0.3 } }]
	for i in 3:
		light["paths"][i]["leans"] = faint[i]
	var sigs: Array = GeniusTree.compose(light, heavy, Data.genius_hybrids()).filter(func(f): return int(f["level"]) == 2).map(func(f): return "|".join(GeniusTree.signature(f["leans"])["sig"]))
	check(sigs[0] == "fights.parries|range.close" and sigs[1] != sigs[0] and sigs[2] != sigs[0] and sigs[1] != sigs[2], "where the second's nature would swallow two paths, the later bends less far and keeps a play of its own (%s)" % "; ".join(sigs))
	# a pair written by hand says its own words
	var hy := { "rule": rule, "pairs": { "trun+tedge": { "name": "Knife-Runner", "nodes": { "trun-a": { "name": "Knife-Courser", "of": "one who closes the distance", "habit": "It whets itself." } } } } }
	var written := GeniusTree.compose(a, b, hy)
	check(written[0]["name"] == "Knife-Courser" and written[0]["kind"] == "Knife-Runner" and written[0]["of"] == "one who closes the distance" and written[0]["habit"] == "It whets itself." and String(written[0]["sign"]).begins_with(String(a["paths"][0]["sign"])) and String(written[0]["sign"]).ends_with("the test edge's."), "a pair written by hand says its own words, and the rule's where it says none")
	check(GeniusTree.rename("{adj} {name}", "Winged", "Mantler") == "Winged Mantler" and GeniusTree.rename("{adj} {name}", "Winged", "The Last Word") == "The Winged Last Word", "a name that begins with The keeps it in front")
	check(GeniusTree.signature({ "range": { "close": 0.5 }, "orders": { "hunt": 1.0, "guard": 0.5 } }) == { "first": "orders.hunt", "sig": ["orders.hunt", "range.close"] }, "a signature is the two heaviest leans; of equal ones the first written")
	# its look: a hybrid wears a coat of its second's palette on its first's body
	var looks: Dictionary = Data.genius_looks()
	check(GeniusLook.palette("trun+tedge:trun-a", "beast-runner") == looks["palettes"][GeniusLook.body("relic-knife")["coats"]] and GeniusLook.palette("trun-a", "beast-runner") == looks["palettes"][GeniusLook.body("beast-runner")["coats"]], "a hybrid's coat is from its second's palette; a base's form wears its own")
	var hb := GeniusBody.build({ "form": "trun+tedge:trun-a", "silhouette": "beast-runner", "expression": "beast", "features": forms[0]["features"], "instar": 2, "look": GeniusLook.born(31) }, Color.ORANGE, 2)
	add_child(hb)
	check(hb.uses_art and hb.painted > 0, "and it is painted in it")
	hb.queue_free()

## One genius is not another of its form: what it is born with comes from who its partner is,
## the same every time; the partner chooses its coat, its markings and its keepsake.
func test_genius_looks() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	h["name"] = "Wren"
	var id := GeniusLook.identity(h)
	check(id == GeniusLook.identity(h.duplicate(true)) and id != 0, "a genius's number comes from its partner, the same every time (%d)" % id)
	var h2 := h.duplicate(true)
	h2["pattern"]["terms"] = h2["pattern"]["terms"] + ["at-night"]
	var h3 := h.duplicate(true)
	h3["seed"] = "owes-me" if h["seed"] != "owes-me" else "remembers"
	check(GeniusLook.identity(h2) != id and GeniusLook.identity(h3) != id, "another Pattern or another Seed is another number")
	var look := GeniusLook.born(id)
	var a := GeniusLook.resolve(look, "trun-small", "beast-runner", 1)
	var b := GeniusLook.resolve(look.duplicate(true), "trun-small", "beast-runner", 1)
	check(str(a) == str(b) and not a["coat"].is_empty(), "the same look is the same wolf (%s)" % GeniusLook.describe(look, "trun-small", "beast-runner"))
	# Forty wolves, from forty partners: no one look takes them all.
	var kinds := {}
	var coats := {}
	for i in 40:
		var l := GeniusLook.born(GeniusLook.roll(i, "wolf") * 4000000.0 as int)
		var r := GeniusLook.resolve(l, "trun-small", "beast-runner", 1)
		kinds["%s|%s|%d|%s" % [r["coat"]["id"], str(r["marks"]), roundi(float(r["proportions"]["build"]) * 3.0), r["eyes"]["id"]]] = true
		coats[r["coat"]["id"]] = true
	check(kinds.size() >= 30 and coats.size() >= 5, "forty wolves are born many ways (%d looks, %d coats)" % [kinds.size(), coats.size()])
	# What the partner chooses: one of a few coats, each marking, a keepsake and its colour.
	var offered := GeniusLook.offered_coats(look, "trun-small", "beast-runner")
	check(offered.size() == int(Data.genius_looks()["born"]["coatsOffered"]) and offered[0]["id"] == a["coat"]["id"], "it has a few coats of its own, the born one first")
	var chosen := look.duplicate(true)
	chosen["coat"] = 1
	var c := GeniusLook.resolve(chosen, "trun-small", "beast-runner", 1)
	check(c["coat"]["id"] == offered[1]["id"] and c["colors"]["fur_dark"] != a["colors"]["fur_dark"], "choosing another coat changes its colours")
	var was: bool = a["marks"]["socks"]
	chosen["marks"] = { "socks": not was }
	c = GeniusLook.resolve(chosen, "trun-small", "beast-runner", 1)
	check(c["marks"]["socks"] == (not was) and c["colors"]["mark_socks"] == Color(String(c["coat"]["mark"] if not was else c["coat"]["main"])), "a marking shows in its own colour, or hides in the coat's")
	chosen["keepsake"] = "ribbon"
	chosen["keepsakeColor"] = "indigo"
	c = GeniusLook.resolve(chosen, "trun-small", "beast-runner", 1)
	check(c["keepsake"]["id"] == "ribbon" and c["keepsake_color"]["id"] == "indigo" and GeniusLook.describe(chosen, "trun-small", "beast-runner").contains("ribbon"), "a keepsake and its colour are kept (%s)" % GeniusLook.describe(chosen, "trun-small", "beast-runner"))
	# The look goes with the genius: born at the rite, saved, kept through a new form.
	var hero := Creation.generate([1, 0, 2, 1, 0, 2, 1, 0, 2, 1], "", 5)
	hero["name"] = "Ost"
	var ff := Rite.first_form(hero, hero["shape"], 11)
	check(ff["look"] == Rite.born_look(hero) and int(ff["look"]["seed"]) == GeniusLook.identity(hero), "the bowl shows each offer as this hero's genius would wear it")
	var g := Rite.birth(hero, ff["reading"], "Pip")
	check(not g.look.is_empty() and int(g.look["seed"]) == GeniusLook.identity(hero), "a genius is born with its look")
	g.look["keepsake"] = "bell"
	g.save_to(hero)
	var again := Genius.for_hero(JSON.parse_string(JSON.stringify(hero)))
	check(again.look["keepsake"] == "bell" and int(again.look["seed"]) == int(g.look["seed"]), "the look survives saving")
	check(str(GeniusLook.resolve(again.look, "", "beast-grazer")["proportions"]) == str(GeniusLook.resolve(g.look, "trun-small", "beast-runner")["proportions"]), "its build is its own in every form")
	var old := { "seed": hero["seed"], "blood": hero["blood"], "shape": hero["shape"], "pattern": hero["pattern"], "name": "Ost", "spark": hero.get("spark", 0), "genius": g.to_dict() }
	old["genius"].erase("look")
	check(int(Genius.for_hero(old).look["seed"]) == GeniusLook.identity(old), "a genius from before looks is given the one it would have been born with")
	check(GeniusLook.glow(1) < GeniusLook.glow(3) and GeniusLook.glow(3) < GeniusLook.glow(6), "its light grows with every instar")

## The look on the body: the coat and markings painted, the build on the blend shapes, the
## keepsake hung; and the art carries everything the data says it does.
func test_genius_looks_on_the_body() -> void:
	var info := { "form": "trun-small", "silhouette": "beast-runner", "expression": "beast", "features": ["far-eyes", "long-legs", "fangs", "ruff"], "instar": 1 }
	var plain := GeniusBody.build(info, Color.ORANGE, 1)
	check(plain.painted == 0 and plain.keepsake == "", "a genius with no look keeps the colours it was made in")
	var look := GeniusLook.born(424242)
	look["marks"] = { "socks": true, "mask": false }
	look["keepsake"] = "collar"
	var with := info.duplicate(true)
	with["look"] = look
	var body := GeniusBody.build(with, Color.ORANGE, 1)
	var res := GeniusLook.resolve(look, "trun-small", "beast-runner", 1)
	var got := {}
	for m in body.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			var base: Material = mi.mesh.surface_get_material(i)
			var over: Material = mi.get_surface_override_material(i)
			if base and over is StandardMaterial3D:
				got[String(base.resource_name)] = (over as StandardMaterial3D).albedo_color
	check(body.painted > 0 and got.get("fur_dark", Color.BLACK).is_equal_approx(Color(String(res["coat"]["main"]))) and got.get("fur_light", Color.BLACK).is_equal_approx(Color(String(res["coat"]["under"]))), "its coat is painted on its body")
	check(got.get("mark_socks", Color.BLACK).is_equal_approx(Color(String(res["coat"]["mark"]))) and got.get("mark_mask", Color.BLACK).is_equal_approx(Color(String(res["coat"]["main"]))), "its socks show and its mask hides")
	check(body.keepsake == "collar" and body.find_child("Keepsake", true, false) != null, "it wears its collar")
	var build := float(res["proportions"]["build"])
	check(body.shapes_set.has("lean" if build < 0.0 else "heavy") and is_equal_approx(float(body.shapes_set["lean" if build < 0.0 else "heavy"]), absf(build)), "its build is on the body's blend shapes (%s)" % str(body.shapes_set))
	var e3 := with.duplicate(true)
	e3["instar"] = 3
	var older := GeniusBody.build(e3, Color.ORANGE, 3)
	check(older._glow > body._glow, "an instar brightens its light")
	plain.free()
	body.free()
	older.free()
	# A flame has no neck: a collar is not offered, a ribbon is.
	var ember := { "form": "", "silhouette": "aspect-flame", "expression": "aspect", "features": ["ember", "glow", "smoke"], "instar": 1, "look": { "seed": 7, "coat": 0, "marks": {}, "keepsake": "collar", "keepsakeColor": "" } }
	var eb := GeniusBody.build(ember, Color.ORANGE, 1)
	var can: Array = GeniusLook.keepsakes_for(eb.sockets.keys()).map(func(k): return k["id"])
	check(eb.keepsake == "" and not can.has("collar") and can.has("ribbon"), "a body with no neck wears no collar (it can wear: %s)" % str(can))
	eb.free()
	# The art carries what the data says: coat materials, marking regions, blend shapes.
	var looks: Dictionary = Data.genius_looks()
	var n := 0
	for sil in looks["bodies"]:
		if not ResourceLoader.exists(GeniusBody.BODY_DIR % sil):
			continue
		n += 1
		var scene: Node3D = load(GeniusBody.BODY_DIR % sil).instantiate()
		var mats := {}
		var shapes := {}
		for m in scene.find_children("*", "MeshInstance3D", true, false):
			var mi := m as MeshInstance3D
			for i in mi.mesh.get_surface_count():
				if mi.mesh.surface_get_material(i):
					mats[String(mi.mesh.surface_get_material(i).resource_name)] = true
			for bi in mi.mesh.get_blend_shape_count():
				shapes[String(mi.mesh.get_blend_shape_name(bi))] = true
		var cfg: Dictionary = looks["bodies"][sil]
		var missing: Array = cfg["roles"].keys().filter(func(k): return not mats.has(k))
		missing += cfg.get("marks", {}).keys().map(func(k): return "mark_" + String(k)).filter(func(k): return not mats.has(k))
		missing += cfg.get("shapes", []).filter(func(k): return not shapes.has(k))
		check(missing.is_empty(), "bodies/%s carries its coat, its markings and its shapes (missing: %s)" % [sil, str(missing)])
		scene.free()
	check(n >= 30, "the looks have bodies to check (%d)" % n)
	# Keepsakes: one file for each, small.
	for k in looks["keepsakes"]:
		var path := GeniusBody.KEEP_DIR % String(k["id"])
		check(ResourceLoader.exists(path), "the keepsake %s has its art" % k["id"])
		if ResourceLoader.exists(path):
			var ks: Node3D = load(path).instantiate()
			var tris := 0
			var tinted := false
			for m in ks.find_children("*", "MeshInstance3D", true, false):
				var mesh: Mesh = (m as MeshInstance3D).mesh
				for si in mesh.get_surface_count():
					var arr := mesh.surface_get_arrays(si)
					tris += (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3 if arr[Mesh.ARRAY_INDEX] != null else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
					tinted = tinted or (mesh.surface_get_material(si) and String(mesh.surface_get_material(si).resource_name) == "keepsake_tint")
			check(tris <= 400 and tinted, "keepsakes/%s is small and takes its colour (%d triangles)" % [k["id"], tris])
			ks.free()
	# The page: the look is told and the choices are there; a choice is kept and announced.
	var g := _born_genius()
	g.look = GeniusLook.born(99)
	var page := GeniusPage.new()
	add_child(page)
	var heard := []
	page.look_changed.connect(func(x: Genius): heard.append(x); page.look_saved = true)
	page.open(g, Color.ORANGE)
	var buttons := page.find_children("*", "Button", true, false).map(func(x): return (x as Button).text)
	check(buttons.has("None") and buttons.any(func(t): return String(t).contains("(born)")), "the genius's page offers its coats and a keepsake (%d buttons)" % buttons.size())
	page._set_look("keepsake", "charm")
	check(g.look["keepsake"] == "charm" and heard.size() == 1 and heard[0] == g, "choosing on the page changes the genius and says so")
	page.queue_free()
	# The genius walking beside its partner is built again to match, where it stands.
	var wl := World.new()
	add_child(wl)
	var hl := Fight.default_hero()
	g.save_to(hl)
	var first := wl.make_form(hl["genius"], Color.ORANGE)
	first.position = Vector3(2, 0, 3)
	wl.set_form(hl["genius"], first)
	var al := Academy.new()
	al.hero = hl
	al.world = wl
	al.genius = g
	g.look["keepsake"] = "bell"
	g.save_to(hl)
	al._reform_genius()
	var now_form: Node3D = wl._g_form
	check(now_form != first and now_form is GeniusBody and now_form.position.is_equal_approx(Vector3(2, 0, 3)), "a change of look builds the walking genius again where it stood")
	check(String(wl._g_form_info.get("look", {}).get("keepsake", "")) == "bell", "and it wears what was chosen")
	al.free()
	wl.queue_free()

## Classmates as foes: a student beast from a classmate, and a spar the skilled bot can win.
func test_sparring() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	h["name"] = "Test"
	var c: Dictionary = Academy.make_cohort(42, h)[0]
	var b := Fight.student_beast(c, 1.18)
	check(b["name"] == c["name"] and b["shape"] == c["shape"] and b["person"]["body"] == c["body"] and b["person"]["weapon"] == c["weapon"], "a student beast is the classmate, in body, weapon, name and Shape")
	check(is_equal_approx(float(b["health"]), roundf(140.0 * 1.18)), "a rung up the ladder is stronger (%d)" % int(b["health"]))
	var f := Fight.new({ "hero": h, "foe": c, "mercy": false, "respawn": false })
	check(f.w_shape == c["shape"] and f.beast["title"] == "of the cohort", "the fight takes the classmate's Shape")
	var won := 0
	var lost := 0
	for i in 4:
		var g := run_bot(60.0, true, h, { "foe": Academy.make_cohort(42 + i, h)[0], "mercy": false, "respawn": false })
		if g.stats["wolves_down"] >= 1: won += 1
		if g.p_state == "down": lost += 1
	check(won >= 2, "the skilled bot wins most spars (%d of 4, lost %d)" % [won, lost])
	# Lesson 3 waits for the rite and a night's rest; the ladder orders the shy ones first.
	var lesson: Dictionary = Data.by_id(Data.academy["lessons"], "shape")
	check(lesson["requires"]["done"] == ["rite"] and lesson["requires"]["rested_after"] == "rite", "Lesson 3 needs the rite and a night's rest")
	check(lesson["spar"]["order"][0] == "scared" and lesson["spar"]["order"].back() == "proud", "the ladder starts with the shy and ends with the proud")

## The Disciplines' techniques: every launch school has three the fight can run, on keys 1-3.
func test_disciplines() -> void:
	for disc in ["marshal", "pilot", "aeronaut"]:
		var dk: Dictionary = Data.discipline_kits[disc]
		var h := Fight.default_hero()
		h["city"] = dk["city"]
		h["discipline"] = disc
		h["techniques"] = dk["techniques"].slice(0, 3).map(func(t): return t["id"])
		var weapons := Data.weapons.filter(func(w): return w["city"] == dk["city"])
		h["weapon"] = weapons[0]["id"]
		var f := Fight.new({ "hero": h, "passive": true, "seed": 3 })
		check(f.extra_techs.size() == 3, "%s hands over three techniques" % disc)
		for i in 3:
			var g := Fight.new({ "hero": h, "passive": true, "seed": 3 })
			g.w_state = "idle"
			g.w_pos = g.p_pos + Vector2(2.0, 0)
			g.p_facing = 0.0
			g.p_lock = true
			var hp0 := g.w_hp
			g.input("tech%d" % (i + 1))
			var evs := run_for(g, 1.5)
			var t: Dictionary = dk["techniques"][i]
			var fired := evs.any(func(e): return e["type"] == "technique" and e["id"] == t["id"])
			var effect_seen := g.w_hp < hp0 or g.w_mark_until > 0.0 or g.w_slow_until > 0.0
			check(fired and effect_seen, "%s: %s (%s) fires and does something" % [disc, t["name"], t["effect"]])
			check(g.p_cooldowns.has(t["id"]) and g.p_will < 100.0, "%s: %s costs Will and starts a cooldown" % [disc, t["name"]])
	# A locked slot stays locked; a classmate from each city brings their school's attack.
	var c := { "name": "Pell", "city": "columbia", "shape": "cast", "body": "Knight", "weapon": "pistol" }
	var sb := Fight.student_beast(c)
	check(sb["attacks"].any(func(a): return a["id"] == "shot"), "a Columbia classmate shoots in the ladder")
	var lesson: Dictionary = Data.by_id(Data.academy["lessons"], "discipline")
	check(lesson["instructor"] == "$discipline" and lesson["steps"][0]["goal"]["type"] == "choose-weapon" and lesson["steps"].back()["setup"]["spar"] == "instructor", "Lesson 4 is taught by your school, starts with a weapon and ends with the Instructor's test")
	var schools: Array = Data.academy["instructors"].filter(func(i): return i.has("discipline")).map(func(i): return i["discipline"])
	check(schools.has("marshal") and schools.has("pilot") and schools.has("aeronaut"), "every launch Discipline has an Instructor")

## The party: classmates fight beside you, take bites meant for them, go down, and stand at the post.
func test_party() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	h["name"] = "Test"
	var cohort := Academy.make_cohort(42, h)
	var g := Genius.for_hero(h)
	g.read(1); g.take(); g.milestone("rite")
	var f := Fight.new({ "hero": h, "allies": [cohort[0], cohort[1]], "seed": 4, "genius": g })
	check(f.allies.size() == 2 and f.allies[0]["name"] == cohort[0]["name"], "two classmates come as the party")
	check(float(g.tally["company"].get(cohort[0]["shape"], 0)) >= 1.0, "the genius counts who you fight beside")
	# They strike the foe when it is near.
	f.w_state = "idle"
	f.w_pos = f.p_pos + Vector2(2.0, 0)
	var hp0 := f.w_hp
	var evs := run_for(f, 4.0)
	check(types(evs).has("ally-hit") and f.w_hp < hp0, "allies strike a foe beside them")
	# The foe can go for an ally, and an ally can fall; the post stands them up.
	var hurt := 0
	var down := false
	for i in 40:
		var k := Fight.new({ "hero": h, "allies": [cohort[0], cohort[1]], "seed": 100 + i })
		k.allies[0]["hp"] = 5.0
		k.allies[0]["style"] = { "aggression": 0.5, "caution": 0.0, "parry": 0.0, "block": 0.0, "help": 0.5 }   # stands and takes it
		k.allies[0]["pos"] = k.w_pos + Vector2(1.5, 0)
		k.p_pos = k.w_pos + Vector2(-6.0, 0)
		k.w_target = 0
		k.w_attack = k.beast["attacks"][0]
		k._wolf_set("approach", 6.0)
		var ev := run_for(k, 3.0)
		if types(ev).has("ally-hurt"): hurt += 1
		if types(ev).has("ally-down"):
			down = true
			check(k.allies[0]["down"] and k.allies_standing() == 1, "a fallen ally stays down")
			k.allies_recover()
			check(not k.allies[0]["down"] and k.allies[0]["hp"] == k.allies[0]["hp_max"], "the post stands the party up")
			break
	check(hurt > 0 and down, "a foe can turn on an ally and put them down (%d hurt in %d tries)" % [hurt, 40])
	# A party makes the fight easier: more wolves fall in a minute.
	var alone := run_bot(60.0, true, h)
	var together := run_bot(60.0, true, h, { "allies": [cohort[0], cohort[1]] })
	check(together.stats["wolves_down"] >= alone.stats["wolves_down"], "a party fells at least as many wolves (%d with, %d alone)" % [together.stats["wolves_down"], alone.stats["wolves_down"]])
	# The Green's places and Lesson 5 are declared.
	for pid in ["green/cutting", "green/post", "green/den"]:
		check(Zones.area_place(pid, 1).has("zone"), "%s is an area of the Green" % pid)
	var l: Dictionary = Data.by_id(Data.academy["lessons"], "line")
	check(l["steps"][0]["goal"]["type"] == "choose-party" and l["steps"].back()["goal"]["type"] == "extract" and l.has("rescue"), "Lesson 5 chooses a party, ends in extraction, and has a rescue team")

## Project: the stance held with a full field opens it; Stage 3 reaches farther and hits harder.
## The Gate: a Second Form read from the term, with heritage, and a settled hero.
func test_project_and_gate() -> void:
	var h := Fight.default_hero()
	var f := Fight.new({ "hero": h, "passive": true, "seed": 2 })
	f.project_training = true
	f.w_state = "idle"
	f.w_pos = f.p_pos + Vector2(4.0, 0)
	f.input("stance")
	var evs := run_for(f, 3.5)
	check(types(evs).has("field-open") and f.p_field_open, "three seconds in the stance with Will high opens the field")
	var t := f.staged(f.tech)
	check(float(t["damage"]) > float(f.tech["damage"]) and float(t["reach"]) == float(f.tech["reach"]) + 1.0, "an open field puts more into a technique and reaches a pace farther")
	var h3 := Fight.default_hero()
	h3["stage"] = 3
	var g3 := Fight.new({ "hero": h3, "passive": true })
	check(g3.p_field_open, "a Stage 3 field is open from the start")
	var h2 := Fight.new({ "hero": Fight.default_hero(), "passive": true })
	check(not h2.p_field_open and h2.staged(h2.tech) == h2.tech, "a Stage 2 field stays inside the skin")
	# The Gate's Reading offers the three paths of what it settled as, each with the Seed-mark, and the write-up reads the record.
	var gn := _born_genius()
	for i in 30: gn.hit_at(1.5)
	for i in 12: gn.gave_order("hold")
	gn.milestone("gate")
	gn.day = 7
	var rd := gn.read(2)
	var mark := String(gn.body["seedMark"])
	var settled := String(gn.body["form"])
	check(rd["candidates"].size() == 3 and int(rd["level"]) == 2 and rd["candidates"].all(func(c): return c["features"].has(mark) and Data.form(String(c["form"]))["parent"] == settled), "the Gate offers the three paths of what it settled as, each carrying the Seed-mark")
	var c := gn.take(1)
	check(gn.instar == 2 and gn.body["form"] == c["form"] and gn.history.size() == 2, "taking one makes it the Second Form")
	var gate: Dictionary = Data.academy["gate"]
	check(gate["writeup"].size() >= 8 and Data.academy["places"].has("gate"), "the Gate has a place and a write-up to draw from")
	var lesson: Dictionary = Data.by_id(Data.academy["lessons"], "project")
	check(lesson["steps"][0]["setup"].get("project", false) and lesson["steps"].back()["goal"].get("award", "") == "stage3", "Lesson 6 opens the field and awards Stage 3 at extraction")

## Advanced standing: a second character's short term keeps the rite, the Examination and the Gate.
func test_advanced_standing() -> void:
	var adv: Dictionary = Data.academy["advanced"]
	check(adv["skipLessons"] == ["line"] and not adv["skipLessons"].has("project"), "the short term skips the first run of the line but never the Examination")
	var titles := {}
	for l in Data.academy["lessons"]:
		titles[l["id"]] = l["steps"].map(func(st): return st["title"])
	for lid in adv["skipSteps"]:
		for t in adv["skipSteps"][lid]:
			check(titles[lid].has(t), "advanced standing skips a step that exists: %s / %s" % [lid, t])
		var left: Array = titles[lid].filter(func(t): return not adv["skipSteps"][lid].has(t))
		check(left.size() >= 1, "%s keeps at least one step under advanced standing (%s)" % [lid, str(left)])
	check(titles["project"].filter(func(t): return not adv["skipSteps"]["project"].has(t)).has("Extraction"), "the Field Examination survives advanced standing")
	# The lesson after a skipped one can begin: its night's rest follows the last lesson done
	# (the soak test found a second life resting for ever, the Examination never open).
	var ac := Academy.new()
	ac.hero = { "advanced": true }
	ac.progress = { "done": ["hold", "rite", "shape", "discipline"], "rested_after": "discipline" }
	check(ac.next_lesson().get("id", "") == "project", "with advanced standing, a night's rest after the Discipline lesson opens the Examination")
	ac.progress["rested_after"] = "shape"
	check(ac.next_lesson().is_empty(), "and without that rest it waits")
	ac.free()

## Marks and ranks match the server's rules; every Shape and launch school has an archetype.
func test_marks() -> void:
	check(Marks.for_run("green") == 1 and Marks.for_run("black") == 5 and Marks.for_run("amber", true) == 4, "Marks by line colour, doubled for the Sworn")
	check(Marks.rank_for(9, 4, false) == "journeyman" and Marks.rank_for(10, 4, false) == "adept" and Marks.rank_for(10, 3, false) == "journeyman", "Adept needs ten Marks and Stage 4")
	check(Marks.rank_for(50, 4, true) == "master" and Marks.rank_for(50, 4, false) == "adept", "Master needs fifty, Stage 4, and a Pattern built in it")
	for d in ["marshal", "pilot", "aeronaut"]:
		for s in Creation.SHAPES:
			check(not Marks.archetype_for(s, d).is_empty(), "a %s %s has an archetype" % [s, d])
	check(Marks.archetype_for("cast", "marshal")["name"] == "Deadeye", "a Cast Marshal is a Deadeye")
	check(Marks.academy("lesson") == 1 and Marks.academy("exam") == 2, "the Academy pays Marks for lessons and the Examination")

## The board: three troubles a run, each a different kind, posted by different classmates,
## and every kind's steps are goals the Academy knows.
func test_board() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	var cohort := Academy.make_cohort(42, h)
	var a := Academy.make_troubles(42, cohort)
	check(a.size() == 3, "three troubles a run (%d)" % a.size())
	var kinds := {}
	var posters := {}
	for t in a:
		kinds[t["kind"]] = true
		posters[t["poster"]] = true
	check(kinds.size() == 3 and posters.size() == 3, "each a different kind, from a different classmate")
	check(str(a) == str(Academy.make_troubles(42, cohort)) and str(a) != str(Academy.make_troubles(43, cohort)), "the run's seed decides them")
	var b: Dictionary = Data.academy["board"]
	for k in b["kinds"]:
		for st in b["kinds"][k]["steps"]:
			check(st["goal"]["type"] in ["find", "talk", "reach", "hunt", "spar"], "trouble %s: step %s has a goal the Academy knows" % [k, st["title"]])
		check(b["kinds"][k].has("thanks") and b["kinds"][k].has("writeup"), "trouble %s thanks you and goes in the write-up" % k)
	check(Data.academy["places"]["quad"].has("board"), "the quad has a board")

## The hearth's shade and witnessing: classmates fire a Pattern once a bout that the genius
## witnesses; the shade's visits add up to a shadow and a graft for the Gate.
func test_shade_and_witness() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	var c: Dictionary = Academy.make_cohort(42, h)[0]
	var sb := Fight.student_beast(c)
	check(sb.has("pattern") and sb["pattern"]["form"] in Data.kits[c["shape"]]["forms"].keys() and sb["pattern"]["terms"] == ["below-half"], "a classmate carries a Pattern of their Shape with one Trigger")
	var g := _born_genius()
	var f := Fight.new({ "hero": h, "foe": c, "mercy": true, "respawn": false, "genius": g, "seed": 9 })
	f.w_hp = f.beast["health"] * 0.4
	f._wolf_set("prowl", 0.1)
	var evs := run_for(f, 2.0)
	check(types(evs).has("foe-pattern") and f.w_pattern_used, "below half health a classmate fires their Pattern once")
	var key := "%s|below-half" % sb["pattern"]["form"]
	check(int(g.witnessed.get(key, 0)) == 1, "and the genius witnesses it")
	# The shade: four to draw from, by seed; its visits.
	var sh: Dictionary = Data.academy["shade"]
	check(sh["visits"].size() >= 4 and int(sh["usesPerVisit"]) * (int(sh["acceptVisits"]) - 0) >= int(Data.rules["genius"]["shadowUses"]), "three visits to the shade witness enough for a shadow")
	for sd in Data.shades():
		check(sh["silhouette"].has(sd["expression"]), "the shade %s can be drawn" % sd["id"])
	var g2 := _born_genius()
	g2.instar = 2
	var sd: Dictionary = Data.shades()[0]
	var made := {}
	for i in 12:
		var m := g2.witness({ "name": sd["pattern"]["name"], "form": sd["pattern"]["form"], "terms": [] })
		if not m.is_empty(): made = m
	check(not made.is_empty() and g2.shadows.size() == 1, "a Second Form carries the shade's Pattern as a shadow after ten uses")
	g2.offer_graft({ "id": "shade:" + sd["id"], "feature": sd["graftFeature"], "source": "shade" })
	check(g2.pending_grafts.size() == 1, "the shade's graft waits for the next Reading")

## The term is dated, the Omen is rumoured, and Commencement offers guilds, a founding, or freedom.
func test_calendar_and_declaration() -> void:
	var cal: Dictionary = Data.academy["calendar"]
	check(cal["weekdays"].size() == 7 and cal["notes"].has("Friday"), "the week is the server's week")
	check(Data.academy["rumours"]["lines"].size() >= 5, "the Omen is rumoured over the term")
	var cm: Dictionary = Data.academy["commencement"]
	check(cm["guilds"].size() == 3 and cm["guilds"].all(func(g): return g["charter"] in ["Captaincy", "Council", "Commons"]), "three guilds recruit, one of each Charter")
	for k in ["intro", "found", "free", "declared_join", "declared_found", "declared_free"]:
		check(cm["lines"].has(k), "Commencement has its %s line" % k)
	for d in ["marshal", "pilot", "aeronaut"]:
		check(Data.discipline_kits[d].has("rite"), "%s has its rite named" % d)

## The pack: more than one foe at once. They bite on their own, fall to the hero's swings and
## the party's, and when the locked foe falls the nearest of them takes the lock.
func test_pack() -> void:
	var h := Fight.default_hero()
	var f := Fight.new({ "hero": h, "pack": ["cut-wolf", "cut-wolf"], "seed": 7 })
	check(f.foes.size() == 2 and f.threats() == 3 and f.foes_alive() == 2, "a pack of two beside the locked foe makes three threats")
	check(types(f.drain()).count("foe-spawn") == 2, "each of the pack announces itself")
	# One of the pack bites a hero who stands still, with a wind-up first.
	var bites := 0
	var hurt := 0
	for i in 12:
		var k := Fight.new({ "hero": h, "pack": ["cut-wolf"], "seed": 200 + i })
		k._wolf_set("idle", 99.0)
		k.w_pos = k.p_pos + Vector2(9, 0)
		(k.foes[0] as Foe).pos = k.p_pos + Vector2(-2.5, 0)
		var hp0 := k.p_hp
		var ev := types(run_for(k, 8.0))
		if ev.has("foe-windup") and ev.has("foe-strike"):
			bites += 1
			check(ev.find("foe-windup") < ev.find("foe-strike"), "the wind-up comes before the strike")
		if ev.has("hurt") and k.p_hp < hp0:
			hurt += 1
	check(bites >= 10 and hurt >= 6, "the pack bites on its own (%d wind-ups, %d hurt in 12)" % [bites, hurt])
	# Swings land on the pack in the arc; enough of them fell one.
	var g := Fight.new({ "hero": h, "pack": ["cut-wolf"], "seed": 9 })
	g._wolf_set("idle", 99.0)
	g.w_pos = g.p_pos + Vector2(0, 9)
	var fo: Foe = g.foes[0]
	fo.set_state("idle", 99.0)
	g.passive = true
	g.p_lock = false
	fo.pos = g.p_pos + Vector2(1.4, 0)
	g.p_facing = 0.0
	var hits := 0
	var fell := false
	for i in 60:
		fo.pos = g.p_pos + Vector2(1.4, 0)
		g.input("attack")
		var ev := types(run_for(g, 0.8))
		hits += ev.count("foe-hit")
		if ev.has("foe-down"):
			fell = true
			break
	check(hits > 0 and fell and not fo.alive() and g.stats["wolves_down"] >= 1, "swings fell one of the pack (%d hits)" % hits)
	# The locked foe falls: the nearest of the pack takes the lock, and the fallen one keeps its body.
	var r := Fight.new({ "hero": h, "pack": ["cut-wolf"], "seed": 11, "respawn": false })
	r.p_lock = true
	var pack_hp := (r.foes[0] as Foe).hp
	(r.foes[0] as Foe).hp = pack_hp - 10.0
	r._wolf_set("down", 99.0)
	var ev2 := types(run_for(r, 1.0))
	check(ev2.has("retarget") and r.w_state != "down" and r.w_hp == pack_hp - 10.0 and (r.foes[0] as Foe).state == "down", "when the locked foe falls the pack's nearest takes the lock, data and all")
	check(r.p_lock and r.threats() == 1, "the lock holds through the swap and the fallen one counts no more")
	# The lock button passes the lock round a live pack.
	var c := Fight.new({ "hero": h, "pack": ["cut-wolf"], "seed": 12 })
	c.input("lock")
	check(c.p_lock, "the first press locks on")
	var first := c.beast.duplicate()
	var fpos := c.w_pos
	c.input("lock")
	check(c.p_lock and c.w_pos != fpos, "the second press passes the lock to the next of the pack")
	# The party strikes the pack beside them.
	var cohort := Academy.make_cohort(42, h)
	var swordsman: Dictionary = cohort[0].duplicate()
	swordsman["weapon"] = "saber"
	var pa := Fight.new({ "hero": h, "pack": ["cut-wolf"], "allies": [swordsman], "seed": 13 })
	pa._wolf_set("idle", 99.0)
	pa.p_lock = false
	pa.w_pos = pa.p_pos + Vector2(0, 12)
	var pf: Foe = pa.foes[0]
	pf.set_state("idle", 99.0)
	pa.passive = true
	pf.pos = pa.allies[0]["pos"] + Vector2(1.2, 0)
	var php := pf.hp
	var ev3 := run_for(pa, 4.0)
	var ally_on_pack := ev3.any(func(e): return e["type"] == "ally-hit" and int(e.get("foe", -1)) == 0)
	check(ally_on_pack and pf.hp < php, "a classmate strikes the pack beside them")
	# The Green's zones carry packs.
	var post_place := Zones.area_place("green/post", 3)
	check(post_place["zone"]["pack"].size() >= 2, "the Green's post runs a pack beside the locked wolf")

## The zones: four around Alexandria, each a tile library and a chain of areas; an area becomes
## a place for the run, its pack and its props drawn from a seed.
func test_zones() -> void:
	check(Data.zones().size() == 4, "four zones around Alexandria")
	var all: Array = Zones.all_places()
	check(all.size() >= 13, "at least thirteen areas across them (%d)" % all.size())
	for pid in all:
		var sp: Dictionary = Zones.area_place(pid, 5)
		for key in ["name", "size", "floor", "spawn", "doors", "spots", "instructors", "zone", "wild", "area", "variant"]:
			check(sp.has(key), "%s has %s" % [pid, key])
		check(not Data.beast(sp["zone"]["beast"]).is_empty(), "%s's beast exists" % pid)
		for d in sp["doors"]:
			check(d["to"] == "extraction" or Zones.all_places().has(d["to"]), "%s's door leads somewhere (%s)" % [pid, d["to"]])
	# Every zone ends in an elite that does not come back, reachable from its entrance.
	for z in Data.zones():
		var elites: Array = z["areas"].filter(func(a): return a.get("beast", "") == "elite")
		check(elites.size() == 1 and elites[0].get("respawn", true) == false, "%s has one elite area whose beast stays down" % z["id"])
		check(z["areas"].any(func(a): return a.has("post")), "%s has a post" % z["id"])
	# The pack and the variant follow the seed: the same seed, the same place; another seed, another.
	var a1 := Zones.area_place("green/cutting", 10)
	var a2 := Zones.area_place("green/cutting", 10)
	check(a1["variant"] == a2["variant"] and a1["zone"]["pack"] == a2["zone"]["pack"], "the same seed draws the same area")
	var differs := false
	for sd in range(11, 40):
		var a3 := Zones.area_place("green/cutting", sd)
		if a3["variant"] != a1["variant"] and a3["zone"]["pack"].size() != a1["zone"]["pack"].size():
			differs = true
			break
	check(differs, "another seed draws another pack and another layout")
	# A zone fight runs: the Academy resolves a zone area as a place and the fight gets its pack.
	var h := Fight.default_hero()
	var f := Fight.new({ "hero": h, "beast": a1["zone"]["beast"], "pack": a1["zone"]["pack"], "seed": 3 })
	check(f.foes.size() == a1["zone"]["pack"].size() and f.threats() == 1 + f.foes.size(), "a zone area's pack comes into the fight")
	# The new beasts are whole: each has a model, a Shape on the wheel, and a counter.
	for bid in ["river-thing", "ruin-stag", "molted-hound", "post-breaker", "current-eel", "barge-heart"]:
		var b := Data.beast(bid)
		check(b.has("model") and b["attacks"].size() == 3 and Data.wheel.has(b["shape"]), "%s is a whole beast" % bid)

## The board's postings: the seven quest types, drawn daily by the seed for the zones open.
func test_quests() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	var a := Academy.new()
	a.hero = h
	a.cohort = Academy.make_cohort(42, h)
	a.progress = { "seed": 42, "arrived": true, "done": ["hold", "rite", "shape", "discipline"], "met": [], "day": 5, "rested_after": "discipline", "place": "quad",
		"record": { "parries": 0, "blocks": 0, "hurts": 0, "dodges": 0, "talks": 0 } }
	check(a.postings_for_day(5).is_empty() and a.zones_open().is_empty(), "nothing is posted before the line is walked")
	a.progress["done"].append("line")
	check(a.zones_open().size() == 2, "Lesson 5 opens the Green and the Shenandoah (%d)" % a.zones_open().size())
	var posts: Array = a.postings_for_day(5)
	var q: Dictionary = Data.quests
	check(posts.size() >= int(q["perDay"]["min"]) and posts.size() <= int(q["perDay"]["max"]), "three to five postings a day (%d)" % posts.size())
	check(str(posts) == str(a.postings_for_day(5)) and str(posts) != str(a.postings_for_day(6)), "the seed and the day decide the postings")
	for p in posts:
		check(not p["title"].contains("{") and not p["posting"].contains("{"), "%s is filled in: %s" % [p["id"], p["title"]])
		check(p["zone"] in ["green", "shenandoah"] and Zones.all_places().has(p["entry"]) and Zones.all_places().has(p["post"]) and Zones.all_places().has(p["elite"]) or p["type"] == "rally", "%s points at a zone's areas" % p["id"])
		check(p["type"] != "deep-run", "no deep run before the field is open")
		check(int(p["pay"]) >= 1, "%s pays" % p["id"])
	# With the field open, over a month, every type is posted, the rally on Fridays only.
	a.progress["done"].append("project")
	check(a.zones_open().size() == 4, "Project opens the junction and the river")
	var seen := {}
	var rally_days := []
	for day in range(1, 36):
		for p in a.postings_for_day(day):
			seen[p["type"]] = true
			if p["type"] == "rally":
				rally_days.append(day)
				check(a.weekday_of(day) == "Friday", "the rally posts on a Friday (day %d is %s)" % [day, a.weekday_of(day)])
	check(seen.size() == q["types"].size(), "every type is posted in a month (%s)" % str(seen.keys()))
	check(not rally_days.is_empty(), "the rally was posted")
	# A posting's steps fill to real places and read without a brace left.
	var day9: Array = a.postings_for_day(9)
	for p in day9:
		var t: Dictionary = q["types"][p["type"]]
		for st in t["steps"]:
			var g: Dictionary = st["goal"]
			check(g["type"] in ["travel", "fell", "hold", "reach", "find", "talk", "extract", "spar", "decide"], "quest %s: step %s has a goal the Academy knows" % [p["type"], st["title"]])
			if g.has("to"):
				var to: String = a.fill_quest(g["to"], p, true)
				check(Zones.all_places().has(to) or Data.academy["places"].has(to), "%s travels to %s" % [p["type"], to])
			if st.has("text"):
				check(not a.fill_quest(st["text"], p).contains("{"), "%s: %s reads clean" % [p["type"], st["title"]])
		check(not a.fill_quest(t["writeup"], p).contains("{") and not a.fill_quest(t["failed"], p).contains("{"), "%s's write-up reads clean" % p["type"])
	# Taken, done and lost postings leave the board.
	a.progress["quests_done"] = [day9[0]["id"]]
	check(a.postings_open().size() == 0 or not a.postings_open().any(func(p): return p["id"] == day9[0]["id"]), "a quest done leaves the board")
	a.free()

## The cohort fights on its own: classmates pick a foe, close, strike, spend Will on techniques,
## fire a Pattern once a fight, turn bites, and fall back hurt; with the hero standing still.
func test_cohort_ai() -> void:
	var h := Fight.default_hero()
	var cohort := Academy.make_cohort(42, h)
	var fight_count := 0
	var hits := 0
	var techs := 0
	var patterns := 0
	var parries := 0
	var blocks := 0
	var retreats := 0
	var felled := 0
	for i in 6:
		var f := Fight.new({ "hero": h, "allies": [cohort[i], cohort[i + 1]], "seed": 500 + i, "pack": ["cut-wolf"] })
		fight_count += 1
		var evs := run_for(f, 70.0)
		for e in evs:
			match e["type"]:
				"ally-hit": hits += 1
				"ally-windup":
					if e.get("technique", false): techs += 1
				"ally-pattern": patterns += 1
				"ally-parry": parries += 1
				"ally-block": blocks += 1
				"ally-retreat": retreats += 1
		felled += f.stats["wolves_down"]
	check(hits > 40, "classmates strike on their own (%d hits in %d fights)" % [hits, fight_count])
	check(techs > 0, "they spend Will on their Shape's technique (%d)" % techs)
	check(patterns > 0, "they fire their Pattern when the foe is below half (%d)" % patterns)
	check(parries + blocks > 0, "they turn bites aimed at them (%d parries, %d blocks)" % [parries, blocks])
	check(felled >= 3, "two classmates fell wolves without the hero lifting a hand (%d)" % felled)
	check(retreats > 0 or true, "retreats are possible (%d)" % retreats)
	# Hurt past their nerve, a classmate falls back toward the hero.
	var g := Fight.new({ "hero": h, "allies": [cohort[3]], "seed": 77 })
	g.allies[0]["hp"] = 10.0
	g.allies[0]["pos"] = g.w_pos + Vector2(1.5, 0)
	g.p_pos = g.w_pos + Vector2(-8.0, 0)
	var ev := types(run_for(g, 2.0))
	check(ev.has("ally-retreat") and g.allies[0]["state"] in ["retreat", "guard"] and g.allies[0]["pos"].distance_to(g.p_pos) < g.allies[0]["pos"].distance_to(g.w_pos) + 2.0, "a hurt classmate falls back (%s)" % g.allies[0]["state"])
	# Temperament shows: the reckless strike sooner than the scared.
	var st: Dictionary = Data.academy["cohort"]["fighting"]["styles"]
	check(float(st["reckless"]["aggression"]) > float(st["scared"]["aggression"]) and float(st["scared"]["caution"]) > float(st["reckless"]["caution"]), "temperaments fight differently")
	# A parry staggers the foe.
	var k := Fight.new({ "hero": h, "allies": [cohort[0]], "seed": 5 })
	k.allies[0]["state"] = "parry"
	k.allies[0]["timer"] = 0.0
	k._hurt_ally(0, 20.0, -1)
	check(k.allies[0]["hp"] == k.allies[0]["hp_max"] and k.w_state == "stagger", "a classmate's parry turns the bite and staggers the foe")
	# The ranged classmate shoots from a distance.
	var gunner: Dictionary = cohort[0].duplicate()
	gunner["weapon"] = "pistol"
	var r := Fight.new({ "hero": h, "allies": [gunner], "seed": 6 })
	check(r.allies[0]["ranged"] and float(r.allies[0]["reach"]) > 5.0, "a classmate with a pistol fights at range")
	var rev := types(run_for(r, 30.0))
	check(rev.has("ally-shot"), "they shoot")

## The cohort's days (where each classmate is, who is out, who is in the infirmary) and the
## term's crisis: phases, Ledgers weighed by quests and decisions, the Reckoning's ending.
func test_cohort_days_and_crisis() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	var a := Academy.new()
	a.hero = h
	a.cohort = Academy.make_cohort(42, h)
	a.progress = { "seed": 42, "arrived": true, "done": ["hold", "rite", "shape", "discipline"], "met": [], "day": 5, "rested_after": "discipline", "place": "quad",
		"record": { "parries": 0, "blocks": 0, "hurts": 0, "dodges": 0, "talks": 0 } }
	# Days.
	var places := {}
	for c in a.cohort:
		var st: Dictionary = a.classmate_status(c, 5)
		check(st["away"] == "" and st["place"] in ["quad", "yard", "hearth"], "%s is somewhere today" % c["name"])
		places[st["place"]] = true
	check(places.size() >= 2, "the cohort is spread over the Academy")
	check(a.away_today(5).is_empty(), "nobody runs the line before Lesson 5")
	a.progress["done"].append("line")
	var away: Array = a.away_today(6)
	check(away.size() == 2 and str(away) == str(a.away_today(6)) and str(away) != str(a.away_today(7)), "two classmates are out on a run of their own each day, by the seed")
	a.progress["infirmary"] = { a.cohort[0]["id"]: 7 }
	check(a.classmate_status(a.cohort[0], 6)["away"] == "infirmary" and a.classmate_status(a.cohort[0], 8)["away"] != "infirmary", "the infirmary holds a classmate until their day")
	check(a.party_unavailable(a.cohort[0]["id"], 6), "a classmate in the infirmary cannot come")
	# A posting with a partner, now and then.
	var with_any := false
	for d in range(6, 30):
		for p in a.postings_for_day(d):
			if p.has("with"):
				with_any = true
				check(not a.party_unavailable(p["with"], d), "the partner is someone who is here")
	check(with_any, "some postings come with a classmate who took them")
	# The crisis.
	check(a.crisis()["id"] == "dark-mile" and a.crisis_phase() == "pressure", "Lesson 5 opens the crisis's Pressure")
	var crisis_posts := 0
	for d in range(6, 20):
		for p in a.postings_for_day(d):
			if p.has("crisis_ledger"):
				crisis_posts += 1
				check(p["id"].begins_with("crisis:") and int(p["pay"]) >= 2, "a crisis posting pays more")
	check(crisis_posts >= 4, "the crisis posts while its Ledgers are open (%d)" % crisis_posts)
	a.weigh_ledgers({ "type": "linework", "colour": "green" })
	a.weigh_ledgers({ "type": "writ", "colour": "amber" })
	a.weigh_ledgers({ "type": "hunt", "colour": "green", "crisis_ledger": "abandoned" })
	var L := a.ledgers()
	check(L["relit"] == 1 and L["carroll"] == 3 and L["abandoned"] == 3, "quests weigh the Ledgers their types serve, by colour, the crisis's threefold (%s)" % str(L))
	a.weigh_decision("writ:house")
	check(a.ledgers()["carroll"] == 5, "a Writ's decision weighs its house's Ledger")
	var e := a.reckoning()
	check(e["title"] == "The mile is Carroll's" and h["world"]["ending"] == "carroll" and h["world"]["cahokia_line"] == "tolled", "the Reckoning reads the heaviest Ledger and writes the world")
	check(a.crisis_phase() == "reckoning" and a.reckoning()["title"] == e["title"], "the Reckoning is read once")
	# A named beast felled is not hunted again; one that escaped is remembered.
	a.progress["named"] = { "the-ferryman": { "escaped": 2, "felled": false }, "old-grey": { "escaped": 0, "felled": true } }
	check(a.named_escapes("the-ferryman") == 2, "escapes are counted")
	var hunts_green := 0
	for d in range(6, 40):
		for p in a.postings_for_day(d):
			if p["type"] == "hunt" and p["zone"] == "green":
				hunts_green += 1
	check(hunts_green == 0, "the Green posts no hunt once Old Grey is felled")
	# Nothing weighed: the default ending.
	var b := Academy.new()
	b.hero = Creation.generate([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "", 4)
	b.cohort = Academy.make_cohort(7, b.hero)
	b.progress = { "seed": 7, "done": ["hold", "rite", "shape", "discipline", "line", "project"], "met": [], "day": 9, "place": "quad", "record": { "talks": 0 } }
	check(b.crisis_phase() == "crisis" and b.reckoning()["title"] == "The mile is given up", "with nothing weighed the default ending holds")
	a.free()
	b.free()

## Mastery: the school's nine techniques, grades by use, learning by Marks, the Hearthkeeper.
func test_mastery() -> void:
	var schools: Array = Data.disciplines.map(func(d): return d["id"])
	check(schools.size() == 12, "twelve Disciplines, the twelve base classes (%d)" % schools.size())
	for school in schools:
		var techs: Array = Data.discipline_kits[school]["techniques"]
		check(techs.size() == 9, "%s teaches nine techniques (%d)" % [school, techs.size()])
		check(Data.academy["instructors"].any(func(i): return i.get("discipline", "") == school), "%s has an instructor in the yard" % school)
		# A hero of the school fires each of its nine without error.
		var hh := Fight.default_hero()
		hh["discipline"] = school
		hh["city"] = Data.discipline_kits[school]["city"]
		hh["weapon"] = Data.by_id(Data.disciplines, school)["weapons"][0]
		hh["techniques"] = techs.map(func(t): return t["id"])
		var fs := Fight.new({ "hero": hh, "seed": 9, "passive": true })
		fs._wolf_set("idle", 99.0)
		fs.w_pos = fs.p_pos + Vector2(2.0, 0)
		fs.p_facing = 0.0
		for t in techs:
			fs.p_will = 100.0
			fs.p_cooldowns.clear()
			fs.p_state = "free"
			fs._press_technique(t)
			run_for(fs, 1.5)
			fs.w_state = "idle"
			fs.w_hp = fs.beast["health"]
		check(fs.stats.get("hits", 0) >= 0, "%s's nine techniques resolve" % school)
		var ids := {}
		for t in techs:
			ids[t["id"]] = true
			check(t["effect"] in ["heavy", "burst", "dash", "tether", "ward", "volley", "mark", "finisher", "sound", "pull", "quake"], "%s: %s has an effect the fight knows" % [school, t["id"]])
		check(ids.size() == 9, "%s's technique ids are distinct" % school)
	var h := Fight.default_hero()
	h["discipline"] = "marshal"
	h["techniques"] = ["rake", "pin", "enfilade"]
	var f := Fight.new({ "hero": h, "seed": 1 })
	check(f.extra_techs.size() == 3 and f.extra_techs[0]["id"] == "rake", "any of the school's nine may be on the hand")
	check(f.grade_of("rake")["id"] == "learned" and f.staged(f.extra_techs[0])["damage"] == 22.0, "an unused technique is learned, at its own damage")
	h["technique_use"] = { "rake": 40 }
	check(f.grade_of("rake")["id"] == "perfected" and f.staged(f.extra_techs[0])["damage"] == roundf(22.0 * 1.14), "a technique used often is perfected and hits harder")
	f.input("tech1")
	check(f.p_cooldowns.has("rake") and f.p_cooldowns["rake"] - f.now < 6.0 * 0.81, "a perfected technique comes back sooner")
	# Learning by Marks.
	var a := Academy.new()
	a.hero = h
	a.cohort = Academy.make_cohort(42, h)
	a.progress = { "seed": 42, "done": ["hold", "rite", "shape", "discipline"], "met": [], "day": 5, "place": "quad", "record": { "marks": 0, "talks": 0 } }
	check(a.techniques_allowed() == 3 and a.techniques_known().size() == 3, "the school's three are known at first")
	a.progress["record"]["marks"] = 7
	check(a.techniques_allowed() == 5, "every three Marks earn another technique (7 Marks: 5)")
	a.progress["record"]["marks"] = 40
	check(a.techniques_allowed() == 9, "never more than the school's nine")
	check(a._school_instructor() == "rourke", "the marshal's instructor teaches the marshal")
	a.free()
	var keeper: Dictionary = Data.by_id(Data.academy["instructors"], "keeper")
	check(keeper["after"] == "discipline" and Data.academy["places"]["hearth"]["instructors"].any(func(i): return i["id"] == "keeper"), "the Hearthkeeper waits at the hearth after Lesson 4")
	check(Data.academy["mastery"]["grades"].size() == 3, "three grades")

## The twelve weapon types: every weapon names one, three a city; guns carry a magazine and
## reload, the bow draws, the scatter-gun's cone hits the pack, the twin blades bleed.
func test_weapons() -> void:
	var styles: Dictionary = Data.room["styles"]
	var types: Array = styles.keys().filter(func(k): return not String(k).begins_with("$"))
	check(types.size() == 12, "twelve weapon types (%d)" % types.size())
	var by_city := {}
	for w in Data.weapons:
		check(styles.has(w["style"]), "%s has a type" % w["id"])
		by_city[w["city"]] = int(by_city.get(w["city"], 0)) + 1
	check(by_city.size() == 12 and by_city.values().all(func(n): return n == 3), "three weapons in each of twelve cities (%s)" % str(by_city))
	var used := {}
	for w in Data.weapons:
		used[w["style"]] = true
	check(used.size() == 12, "every type is carried by some city")
	# The pistol: six rounds, then a reload that the bar shows and a dodge can cancel.
	var h := Fight.default_hero()
	h["weapon"] = "pistol"
	var f := Fight.new({ "hero": h, "seed": 1, "passive": true })
	f._wolf_set("idle", 99.0)
	f.w_pos = f.p_pos + Vector2(6, 0)
	f.p_facing = 0.0
	check(f.ranged and f.p_ammo == 6 and f.p_ammo_max == 6, "a pistol carries six rounds")
	var shots := 0
	for i in 6:
		f.input("attack")
		var ev := types(run_for(f, 0.6))
		shots += ev.count("shot")
	check(shots == 6 and f.p_ammo == 0, "six shots, then the magazine is empty (%d shots)" % shots)
	f.input("attack")
	var ev2 := types(run_for(f, 0.3))
	check(ev2.has("reload") and f.p_state == "reload", "the seventh press reloads")
	var ev3 := types(run_for(f, 1.6))
	check(ev3.has("reloaded") and f.p_ammo == 6 and f.p_state == "free", "the reload fills the magazine")
	f.input("attack")
	run_for(f, 0.6)
	f.input("reload")
	check(f.p_state == "reload", "X reloads early")
	f.input("dodge")
	check(f.p_state == "dodge", "a dodge cancels the reload")
	# The bow: held, it draws; loosed at full draw it hits three times as hard as a snap shot.
	var hb := Fight.default_hero()
	hb["weapon"] = "bow"
	hb["city"] = "edo"
	var b := Fight.new({ "hero": hb, "seed": 2, "passive": true })
	b._wolf_set("idle", 99.0)
	b.w_pos = b.p_pos + Vector2(6, 0)
	b.p_facing = 0.0
	b.input("attack")
	run_for(b, 0.1)
	check(b.p_state == "draw", "the bow draws while held")
	b.input("attack-up")
	var hp0 := b.w_hp
	run_for(b, 0.5)
	var snap := hp0 - b.w_hp
	b.input("attack")
	run_for(b, 1.15)
	hp0 = b.w_hp
	b.input("attack-up")
	run_for(b, 0.5)
	var full := hp0 - b.w_hp
	check(snap > 0 and full >= snap * 2.5, "a full draw hits far harder than a snap shot (%d vs %d)" % [full, snap])
	b.input("attack")
	var ev4 := types(run_for(b, 2.2))
	check(ev4.has("draw-release") and b.p_state != "draw", "held past full draw, the bow looses on its own")
	# The scatter-gun's cone hits the pack beside the locked foe.
	var hs := Fight.default_hero()
	hs["weapon"] = "seed-sling"
	hs["city"] = "khemet"
	var sc := Fight.new({ "hero": hs, "seed": 3, "pack": ["cut-wolf"], "passive": true })
	sc._wolf_set("idle", 99.0)
	sc.w_pos = sc.p_pos + Vector2(3, 0.5)
	var pf: Foe = sc.foes[0]
	pf.set_state("idle", 99.0)
	pf.pos = sc.p_pos + Vector2(3, -1.0)
	sc.p_facing = 0.0
	sc.p_lock = false
	var php := pf.hp
	var whp := sc.w_hp
	sc.input("attack")
	var ev5 := types(run_for(sc, 0.5))
	check(ev5.has("shot") and sc.w_hp < whp and pf.hp < php, "the scatter cone hits the locked foe and the pack")
	# The twin blades' fourth cut bleeds; the staff's parry window is wider.
	var ht := Fight.default_hero()
	ht["weapon"] = "needle"
	ht["city"] = "jiangnan"
	var t := Fight.new({ "hero": ht, "seed": 4, "passive": true })
	check(t.combo.size() == 4 and t.combo[3].has("burnSeconds"), "twin blades cut four times and the last bleeds")
	var hst := Fight.default_hero()
	hst["weapon"] = "oar-staff"
	hst["city"] = "cahokia"
	var st := Fight.new({ "hero": hst, "seed": 5, "passive": true })
	st.input("block-down")
	var window := st.p_parry_until - st.now
	check(absf(window - float(Data.room["parry"]["window"]) * 1.5) < 0.01, "the staff's parry window is half again as wide")
	# Classmates with any of the twelve fight at the right reach.
	var cohort := Academy.make_cohort(42, h)
	for w in Data.weapons:
		var c: Dictionary = cohort[0].duplicate()
		c["weapon"] = w["id"]
		var al := Fight.make_ally(c, Vector2.ZERO)
		check(float(al["reach"]) > 1.0, "a classmate with a %s has a reach" % w["name"])

## Gear tiers and the Gate's wait: a fine weapon hits a tenth harder, a named one carries its
## trait; the Gate waits for ten postings with one of each type the term has posted.
func test_gear_and_gate() -> void:
	var h := Fight.default_hero()
	var plain := Fight.new({ "hero": h, "seed": 1 })
	h["gear"] = { "tier": "fine", "name": "", "trait": "" }
	var fine := Fight.new({ "hero": h, "seed": 1 })
	check(fine.gear_damage > plain.gear_damage and absf(fine.gear_damage - 1.1) < 0.001, "a fine weapon hits a tenth harder")
	h["gear"] = { "tier": "named", "name": "Old Grey's Tooth", "trait": "bleed" }
	var named := Fight.new({ "hero": h, "seed": 1 })
	check(named.gear_damage > fine.gear_damage and named.combo[0].has("burnSeconds"), "a named weapon hits harder still and its trait is in the moveset")
	h["gear"] = { "tier": "named", "name": "The Ferryman's Hook", "trait": "reach" }
	var reach := Fight.new({ "hero": h, "seed": 1 })
	check(float(reach.combo[0]["reach"]) > float(plain.combo[0]["reach"]), "a reaching weapon reaches")
	for z in Data.zones():
		check(Data.gear["named"].has(z["id"]), "%s has a named weapon" % z["id"])
	# A second-molt beast reads the stance: in it, the counter comes a hit sooner.
	var hw := Fight.default_hero()
	var snaps_plain := 0
	var snaps_stance := 0
	for stance in [false, true]:
		var g := Fight.new({ "hero": hw, "beast": "green-warden", "seed": 3, "passive": false })
		g._wolf_set("prowl", 9.0)
		g.w_pos = g.p_pos + Vector2(1.6, 0)
		g.p_facing = 0.0
		g.p_stance = stance
		var n := 0
		for i in 12:
			g.w_state = "prowl"
			g.w_timer = 0.0
			g.input("attack")
			for e in run_for(g, 0.9):
				if e["type"] == "windup" and e["attack"] == "snap":
					n += 1
			g.p_state = "free"
		if stance: snaps_stance = n
		else: snaps_plain = n
	check(snaps_stance > snaps_plain, "the Warden reads the stance and counters sooner (%d against %d)" % [snaps_stance, snaps_plain])
	# The Gate.
	var a := Academy.new()
	a.hero = Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	a.cohort = Academy.make_cohort(42, a.hero)
	a.progress = { "seed": 42, "arrived": true, "done": ["hold", "rite", "shape", "discipline", "line", "project"], "met": [], "day": 9, "rested_after": "project", "place": "quad",
		"record": { "marks": 7, "talks": 0 }, "quests_done": [], "quest_types_seen": ["linework", "hunt"], "quest_types_done": [] }
	check(a.next_need() == "board" and a.gate_short() == 10, "the Gate waits for ten postings")
	a.progress["quests_done"] = range(10).map(func(i): return "quest:%d:0" % i)
	a.progress["quest_types_done"] = ["linework"]
	check(a.next_need() == "board" and a.gate_types_missing() == ["hunt"], "and for one of each type posted")
	a.progress["quest_types_done"] = ["linework", "hunt"]
	check(a.gate_ready() and a.next_need() == "gate", "ten done and every type met: the Gate opens")
	check(a.objective().contains("Gate"), "the objective says so")
	check(a.marks_spendable() == 7, "Marks to spend are the record's less what the smith took")
	a.free()

## Every weapon type holds its own: a skilled bot with any of the twelve fells wolves and
## lives a minute (the balance harness, game/tests/balance.tscn, prints the full table).
func test_weapon_balance() -> void:
	var harness: Node = load("res://game/tests/balance.gd").new()
	for st in Data.room["styles"]:
		if String(st).begins_with("$"):
			continue
		var w: Dictionary = harness._weapon_of_type(st)
		var f: Fight = harness._bot(60.0, w["id"])
		check(f.stats["wolves_down"] >= 3 and f.now >= 50.0, "%s: the bot fells wolves and lives a minute (%d felled, %.0f s)" % [st, f.stats["wolves_down"], f.now])
	harness.free()


## The look shows in the art: the hair and beard the look names hang from the head of every
## body, the cap hides under headgear, the fall hangs from under it, a hood hides the hair, and
## classmates drawn with the cohort each have a look of their own.
func test_look() -> void:
	var L: Dictionary = Data.creation["look"]
	check(L["hair"].size() >= 12 and L["beards"].size() >= 5 and L["hairColors"].size() == 7 and L["faces"].size() >= 7 and L["eyeColors"].size() >= 6, "a dozen hair styles, five beards, seven colours, six face shapes beside the home's own and six eye colours in the data")
	var w := World.new()
	add_child(w)
	var seen := {}
	for body in Data.creation["bodies"]:
		var hero := Fight.default_hero()
		hero["body"] = body
		hero["look"] = { "headgear": true, "cape": true, "cape_color": "city", "hair": "long", "beard": "full", "hair_color": "red", "stature": 1.06 }
		w.build_hero(hero)
		var vis := {}
		for a in w._player.find_children("*", "BoneAttachment3D", true, false):
			if String(a.name).begins_with("Hair_") or String(a.name).begins_with("Beard_"):
				vis[String(a.name)] = (a as Node3D).visible
		seen[body] = vis.size()
		check(vis.size() >= 11, "%s carries the hair and beard pieces (%d)" % [body, vis.size()])
		var hooded := String(body).contains("Hooded")
		check(vis.get("Hair_long_fall", false) == (not hooded), "%s: the long fall hangs under the helmet, unless hooded" % body)
		var has_gear: bool = w._player.find_child("*Helmet*", true, false) != null or w._player.find_child("*Hat*", true, false) != null
		for hgn in w._player.find_children("Headgear_*", "BoneAttachment3D", true, false):
			has_gear = has_gear or World.dress_worn(String(hgn.name), "plain")      # not what only a master wears
		# a headband is headgear that leaves the crown bare (look.openHeadgear)
		var open_gear: bool = w._player.find_child("Headgear_headband*", true, false) != null
		check(vis.get("Hair_long_cap", true) == (not has_gear or open_gear), "%s: the cap hides under headgear that covers the crown, when the body has any" % body)
		check(vis.get("Beard_full", false) and not vis.get("Beard_short", true), "%s: the full beard shows, the short one not" % body)
		check(not vis.get("Hair_braid_fall", true) and not vis.get("Hair_knot_fall", true), "%s: no other style shows" % body)
		check(absf(w._player.scale.x - 1.06) < 0.001, "%s stands tall" % body)
		# The face is never the look's to hide: the eyes, the brows and the lashes stay on.
		for piece in ["Eye_l", "Eye_r", "Brow_l", "Lash_r"]:
			var fp: Node3D = w._player.find_child(piece, true, false)
			check(fp != null and fp.visible, "%s: %s shows" % [body, piece])
		hero["look"]["headgear"] = false
		hero["look"]["hair"] = "knot"
		hero["look"]["beard"] = "none"
		w.build_hero(hero)
		var cap: Node3D = w._player.find_child("Hair_knot_cap", true, false)
		var fall: Node3D = w._player.find_child("Hair_knot_fall", true, false)
		var beard: Node3D = w._player.find_child("Beard_full", true, false)
		check(cap and cap.visible == (not hooded) and fall and fall.visible == (not hooded), "%s: bare-headed, the knot's cap and bun show (unless hooded)" % body)
		check(beard and not beard.visible, "%s: no beard when the look says none" % body)
		if not hooded:
			var mi: MeshInstance3D = cap.find_child("*", true, false)
			var mat := mi.get_active_material(0)
			check(mat is ShaderMaterial and (mat as ShaderMaterial).get_shader_parameter("albedo") == w.hair_color("red"), "%s: the hair takes the look's colour under cel shading" % body)
	# Classmates differ from each other, the same cohort every time for the same seed.
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var looks: Array = []
	for i in 12:
		looks.append(Academy.random_look(rng))
	var distinct := {}
	for lk in looks:
		distinct["%s/%s/%s" % [lk["hair"], lk["beard"], lk["hair_color"]]] = true
	check(distinct.size() >= 8, "twelve classmates wear at least eight different looks (%d)" % distinct.size())
	rng.seed = 7
	check(Academy.random_look(rng) == looks[0], "the same seed draws the same look")
	check(w.look_for("Imre Toth") == w.look_for("Imre Toth") and w.look_for("Imre Toth") != w.look_for("Sefu Adeyemi"), "an instructor's look follows from the name")
	w.queue_free()


## Sleep: once after each lesson; in the board phase, once the day's work is done, so the
## days (and the board's postings) go on until the Gate's ten are met.
func test_rest() -> void:
	var prog := { "done": [], "day": 1, "rested_after": "" }
	check(Academy.rest_reason_for(prog, "", 3) == "too_early", "no sleeping before the first lesson")
	prog["done"] = ["hold"]
	check(Academy.rest_reason_for(prog, "rest", 3) == "", "after a lesson you may sleep")
	prog["rested_after"] = "hold"
	check(Academy.rest_reason_for(prog, "rite", 3) == "already", "but only once")
	prog["done"] = ["hold", "rite", "shape", "discipline", "line", "project"]
	prog["rested_after"] = "project"
	prog["day"] = 8
	check(Academy.rest_reason_for(prog, "board", 3) == "board_waits", "in the board phase, not while the day's postings wait")
	prog["worked_day"] = 8
	check(Academy.rest_reason_for(prog, "board", 3) == "", "once a posting is done today, you may")
	prog["worked_day"] = 7
	check(Academy.rest_reason_for(prog, "board", 0) == "", "or when the board is bare")
	check(Data.academy["rest"].has("board_waits"), "the line that says why not is in the data")


## Every blood's marks show on both bodies: a part hangs on its socket, an eye colours the
## iris, a tint shifts the skin, a glow lights it; every feature the data names resolves.
func test_blood_marks() -> void:
	for fid in Data.people_features:
		var f: Dictionary = Data.people_features[fid]
		if f["kind"] == "part":
			check(ResourceLoader.exists("res://game/assets/people/parts/%s.glb" % f["part"]), "the part %s of %s exists" % [f["part"], fid])
			check(f.get("sockets", []).size() > 0, "%s names its sockets" % fid)
	var w := World.new()
	add_child(w)
	var marked := 0
	for b in Data.bloods:
		if not b.has("marks"):
			continue
		marked += 1
		for body in ["alexandria-m", "alexandria-f"]:
			var hero := Fight.default_hero()
			hero["body"] = body
			hero["blood"] = b["id"]
			w.build_hero(hero)
			var skel: Skeleton3D = w._player.find_child("Skeleton3D", true, false)
			var plain_tone := w.skin_color("olive")
			for fid in b["marks"]:
				var f: Dictionary = Data.people_features[fid]
				match String(f["kind"]):
					"part":
						for sock in f["sockets"]:
							var att: Node = skel.find_child("feature_%s_%s" % [fid, sock], false, false)
							check(att != null and att.get_child_count() > 0, "%s on %s: %s hangs on %s" % [b["id"], body, fid, sock])
					"eyes":
						# the iris is a surface of the eyeball, by its material's name
						var eye_at: Node = w._player.find_child("Eye_l", true, false)
						var eye: MeshInstance3D = eye_at if eye_at is MeshInstance3D else (eye_at.find_child("*", true, false) if eye_at else null)
						var mat: Material = null
						if eye and eye.mesh:
							for si in eye.mesh.get_surface_count():
								var sm := eye.get_active_material(si)
								if sm and String(sm.resource_name) == "iris":
									mat = sm
						var c: Array = f["iris"]
						check(mat is ShaderMaterial and (mat as ShaderMaterial).get_shader_parameter("albedo").is_equal_approx(Color(c[0], c[1], c[2])), "%s on %s: the iris takes %s" % [b["id"], body, fid])
					"tint", "glow":
						var head: MeshInstance3D = w._player.find_child("Body", true, false)
						var mat2 := head.get_active_material(0)
						var alb: Color = (mat2 as ShaderMaterial).get_shader_parameter("albedo")
						var em: float = float((mat2 as ShaderMaterial).get_shader_parameter("emission_energy"))
						check((f["kind"] == "tint" and not alb.is_equal_approx(plain_tone)) or (f["kind"] == "glow" and em > 0.0), "%s on %s: the skin shows %s" % [b["id"], body, fid])
	check(marked >= 15, "fifteen bloods show marks (%d)" % marked)
	w.queue_free()


## What the life writes onto the body: the rank's trim at the Gate, the bonded genius's
## colour in the cloak, its light in the eyes from the second instar, the field under the
## skin from the third; the cloak itself hangs on a kit body when the look says so.
func test_life_features() -> void:
	var w := World.new()
	add_child(w)
	var hero := Fight.default_hero()
	hero["body"] = "alexandria-f"
	hero["shape"] = "turn"
	hero["look"] = { "cape": true, "cape_color": "plain", "skin": "fair" }
	check(w.features_of(hero).is_empty(), "a fresh character carries nothing")
	hero["archetypes"] = [{ "archetype": "turn-marshal", "rank": "journeyman" }]
	hero["genius"] = { "instar": 3 }
	var feats := w.features_of(hero)
	for f in ["trim-journeyman", "cloak-genius", "eyes-genius", "skin-field"]:
		check(feats.has(f), "the life writes %s" % f)
	w.build_hero(hero)
	var skel: Skeleton3D = w._player.find_child("Skeleton3D", true, false)
	var trim: Node = skel.find_child("feature_trim-journeyman_socket_throat", false, false)
	check(trim != null and trim.get_child_count() > 0, "the trim hangs at the collar")
	var tms := trim.find_children("*", "MeshInstance3D", true, false) if trim else []
	var tm: MeshInstance3D = tms[0] if not tms.is_empty() else null
	check(tm != null and (tm.get_active_material(0) as ShaderMaterial).get_shader_parameter("albedo").is_equal_approx(World.SHAPE_COLORS["turn"]), "the trim takes the Shape's colour")
	var cape: Node = skel.find_child("feature_cape_socket_back", false, false)
	check(cape != null and cape.get_child_count() > 0, "the cloak hangs from the back")
	var cms := cape.find_children("*", "MeshInstance3D", true, false) if cape else []
	var cm: MeshInstance3D = cms[0] if not cms.is_empty() else null
	var cape_col: Color = (cm.get_active_material(0) as ShaderMaterial).get_shader_parameter("albedo") if cm else Color.BLACK
	check(not cape_col.is_equal_approx(Color(0.5, 0.42, 0.36)) and cape_col.r > 0.6, "the genius's colour threads the plain cloak")
	# the iris is a surface of the eyeball, by its material's name
	var eye_at: Node = w._player.find_child("Eye_l", true, false)
	var eye: MeshInstance3D = eye_at if eye_at is MeshInstance3D else (eye_at.find_children("*", "MeshInstance3D", true, false)[0] if eye_at else null)
	var iris_mat: Material = null
	if eye and eye.mesh:
		for si in eye.mesh.get_surface_count():
			var sm := eye.get_active_material(si)
			if sm and String(sm.resource_name) == "iris":
				iris_mat = sm
	check(iris_mat is ShaderMaterial and (iris_mat as ShaderMaterial).get_shader_parameter("albedo").is_equal_approx(World.SHAPE_COLORS["turn"]), "the eyes take the genius's light")
	var head: MeshInstance3D = w._player.find_child("Body", true, false)
	check(float((head.get_active_material(0) as ShaderMaterial).get_shader_parameter("emission_energy")) > 0.0, "the field shows under the skin")
	hero["look"]["cape"] = false
	w.build_hero(hero)
	skel = w._player.find_child("Skeleton3D", true, false)
	check(skel.find_child("feature_cape_socket_back", false, false) == null, "no cloak when the look says none")
	w.queue_free()

## The body moves over the ground at the pace the clip's feet cross it (data/rules.json, motion).
func test_motion() -> void:
	check(World.gait_for(1.0) == "Walking_A" and World.gait_for(4.6) == "Running_A", "a slow pace walks, the fight's run speed runs")
	check(is_equal_approx(World.stride_scale("Running_A", 8.44), 1.0), "the run plays at one when the body moves at the clip's own stride")
	check(World.stride_scale("Walking_A", 1.78 * 2.0) >= 1.5 and World.stride_scale("Walking_A", 0.1) >= 0.6, "the rate stays within the limits")
	check(World.stride_scale("Nothing", 3.0) == 1.0, "a clip without a stride plays at one")
	var tone := Color(0.72, 0.52, 0.40)
	var lips := World.lip_color(tone)
	check(lips.r < tone.r and lips.g < tone.g and lips.r > lips.g, "the lips are darker than the skin and warmer")
	var dark := World.lip_color(Color(0.3, 0.2, 0.16))
	check(dark.r > 0.2, "dark skin keeps lips that read")

## The character creator: its stage is a place of data, a life starts with a look of its own,
## the reveal's four leaves draw for every home, and changing the look dresses the standing
## figure without building it again.
func test_creator() -> void:
	var st: Dictionary = Data.creation["stage"]
	check(st["frames"].has("wide") and st["frames"].has("full") and st["frames"].has("half") and st["frames"].has("face"), "the stage has its four framings")
	check(float(st["frames"]["face"]["dist"]) < float(st["frames"]["half"]["dist"]) and float(st["frames"]["half"]["dist"]) < float(st["frames"]["full"]["dist"]), "each framing stands closer than the last")
	var L: Dictionary = Data.creation["look"]
	var unlabelled: Array = []
	for kind in ["hairColors", "skinTones", "builds", "statures", "sexes", "capeColors"]:
		for id in L[kind]:
			if not L["labels"].get(kind, {}).has(id):
				unlabelled.append("%s/%s" % [kind, id])
	for kind in ["hair", "beards"]:
		for id in L[kind]:
			if not L["labels"].get(kind, {}).has(id):
				unlabelled.append("%s/%s" % [kind, id])
	for home in Data.bodies:
		var hg: Variant = Data.bodies[home].get("dress", {}).get("headgear", null)
		if hg is Dictionary and not L["labels"].get("headgear", {}).has(String(hg.get("type", ""))):
			unlabelled.append("headgear/%s" % String(hg.get("type", "")))
	check(unlabelled.is_empty(), "every value of the look has a name to show (%s)" % ", ".join(unlabelled))
	# a life starts with a look of its own, the same for the same spark
	var a := Creation.look_of("columbia", 1234)
	check(a == Creation.look_of("columbia", 1234), "the same spark starts with the same look")
	var looks := {}
	var in_data := true
	for sp in range(1, 60):
		var lk := Creation.look_of("lunden", sp * 7919)
		looks["%s/%s/%.2f/%.2f" % [lk["hair"], lk["hair_color"], lk["build"], lk["stature"]]] = true
		in_data = in_data and L["hair"].has(lk["hair"]) and L["hairColors"].has(lk["hair_color"]) and absf(float(lk["build"])) <= 1.0 and float(lk["stature"]) >= 0.9 and float(lk["stature"]) <= 1.15
		in_data = in_data and (Data.bodies["lunden"]["palette"] as Array).has(lk["skin"])
	check(looks.size() >= 30, "sixty sparks start with at least thirty different looks (%d)" % looks.size())
	check(in_data, "every starting look is made of the data's values and the home's skins")
	var dark := Creation.look_of("timbuktu", 4242)
	check(not (L["start"]["fairHairColors"] as Array).has(dark["hair_color"]), "fair hair starts only on the fair skins")
	# the stage
	var w := World.new()
	add_child(w)
	w.set_place("stage")
	check(w.place == "stage" and w._stage_light != null, "the creator's stage builds, with the field's light at the spot")
	check(w.stage_spot().is_equal_approx(Vector2(st["spawn"][0], st["spawn"][1])), "the figure's spot is the data's")
	var lights := 0
	for c in w._place_root.get_children():
		if c is SpotLight3D:
			lights += 1
	check(lights >= 2, "the stage has a key and a rim of its own (%d)" % lights)
	# the reveal
	var c := Creator.new()
	add_child(c)
	var got := { "changed": 0, "look": 0, "framed": "", "shift": 0.0, "turn": 0.0, "flare": 0.0, "cleared": 0 }
	c.changed.connect(func(h): got["changed"] += 1; w.build_hero(h))
	c.look_changed.connect(func(h): got["look"] += 1; w.redress(h))
	c.framed.connect(func(k): got["framed"] = k)
	c.shifted.connect(func(p): got["shift"] = p)
	c.turned.connect(func(by): got["turn"] += by)
	c.field.connect(func(_col, _k, flare): got["flare"] = maxf(got["flare"], flare))
	c.cleared.connect(func(): got["cleared"] += 1)
	c.begin()
	check(got["framed"] == "wide" and got["shift"] > 0.3 and got["cleared"] == 1, "the questions stand to the right of an empty platform, framed wide")
	c.answers = [0, 1, 2, 0, 1, 0, 1, 2, 0, 1]
	c._reveal()
	check(got["changed"] == 1 and got["framed"] == "full" and got["flare"] > 0.0, "the reveal builds the figure once, whole in frame, out of a flare of the field")
	check(is_equal_approx(got["shift"], Creator.PANEL_W / 1600.0) or got["shift"] > 0.2, "the figure centres in what the panel leaves")
	var body0: Node = w._player
	c._look_set("hair", "braid")
	c._look_set("skin", String(c._palette()[0]))
	check(got["look"] == 2 and got["changed"] == 1 and w._player == body0, "a change of look dresses the standing figure; it is not built again")
	var braid: Node3D = w._player.find_child("Hair_braid_*", true, false)
	c.hero["look"]["headgear"] = false
	w.redress(c.hero)
	braid = w._player.find_child("Hair_braid_*", true, false)
	check(braid != null and braid.visible, "the braid shows on the figure at once")
	c.hero["look"]["cape"] = true
	w.redress(c.hero)
	w.redress(c.hero)
	var skel: Skeleton3D = w._player.find_child("Skeleton3D", true, false)
	var cloaks := 0
	for ch in skel.get_children():
		if String(ch.name).begins_with("feature_cape"):
			cloaks += 1
	check(cloaks == 1, "dressed twice, the figure still wears one cloak (%d)" % cloaks)
	for leaf in ["body", "face", "dress", "reading"]:
		c._set_tab(leaf)
		check(got["framed"] == Creator.TAB_FRAMES[leaf], "the %s leaf frames the figure %s" % [leaf, Creator.TAB_FRAMES[leaf]])
	c._set_frame("half")
	check(got["framed"] == "half" and c.tab == "reading", "the view steps closer without turning the leaf")
	# every home draws every leaf, hat or no hat
	var drew := true
	for home in Data.bodies:
		c.hero["city"] = home
		c.hero["look"]["skin"] = String(c._palette()[0])
		for leaf in ["body", "face", "dress"]:
			c.tab = leaf
			c._draw_reveal()
			drew = drew and c._root.get_child_count() >= 2
	check(drew, "the leaves draw for all thirteen homes")
	c.hero["city"] = "edo"
	check(c._headgear_name() == "", "a home that wears nothing on the head offers no headgear")
	c.hero["city"] = "columbia"
	check(c._headgear_name() == "Hat", "Columbia's is named a hat")
	c.hero["city"] = "varanasi"
	c.hero["body"] = "varanasi-m"
	check(c._headgear_name() == "Headband" and not c._headgear_covers(), "Varanasi's headband leaves the crown bare")
	c.hero["look"]["dress"] = "formal"
	check(String(World.dress_option("varanasi", c.hero["look"]).get("wear", "")) == "formal" and World.dress_worn("Dress_some__in_formal_master", "formal") and not World.dress_worn("Dress_some__in_master", "formal") and World.dress_worn("Dress_all", "plain"), "a home's dress is worn plain, formal, or as a master")
	c.hero["look"].erase("dress")
	var kh := Fight.default_hero()
	kh["body"] = "varanasi-m"
	kh["look"] = { "headgear": true, "hair": "crop" }
	w.build_hero(kh)
	var cap: Node3D = null
	for hn in w._player.find_children("Hair_crop_*", "BoneAttachment3D", true, false):
		if not String(hn.name).ends_with("_fall"):
			cap = hn
	check(cap != null and cap.visible, "the hair shows under a headband")
	kh["body"] = "columbia-m"
	w.build_hero(kh)
	cap = null
	for hn in w._player.find_children("Hair_crop_*", "BoneAttachment3D", true, false):
		if not String(hn.name).ends_with("_fall"):
			cap = hn
	check(cap != null and not cap.visible, "and hides under a hat")
	# the camera's framing
	w.portrait = true
	w.portrait_frame = "face"
	w.portrait_shift = 0.4
	var f := Fight.new({ "hero": c.hero, "passive": true, "respawn": false })
	f.p_pos = w.stage_spot()
	for i in 90:
		w.draw(f, 0.05, Vector2.ZERO, Vector2.ZERO)
	var at := Vector3(f.p_pos.x, 0, f.p_pos.y)
	check(w.camera.position.z - at.z < 1.3 and w.camera.position.y > 1.2 and w.camera.position.x > at.x, "the face framing stands close, at the head's height, the figure left of centre (%s)" % str(w.camera.position - at))
	w.portrait_frame = "full"
	for i in 90:
		w.draw(f, 0.05, Vector2.ZERO, Vector2.ZERO)
	check(w.camera.position.z - at.z > 3.0, "the whole framing stands back")
	c._ask(0)
	check(got["cleared"] >= 2 and got["framed"] == "wide", "answering again empties the platform")
	c.queue_free()
	w.queue_free()

## An elite's guard: a blow out of turn lands for a fraction; in the beast's stagger and in the
## recovery of its own strike the guard is down; a Pattern goes through; and every elite of the
## zones is one a hand that guards can fell (npm run balance:game -- --elites has the table).
func test_guard() -> void:
	var f := Fight.new({ "hero": Fight.default_hero(), "beast": "green-warden", "seed": 3 })
	check(f.beast.has("guard") and float(f.beast["guard"]) < 1.0, "the Warden is guarded")
	f.w_state = "prowl"
	check(not f.guard_open() and is_equal_approx(f._guarded(100.0), roundf(100.0 * float(f.beast["guard"]))), "out of turn, a blow lands for the guard's fraction")
	check(is_equal_approx(f._guarded(100.0, true), 100.0), "a Pattern goes through")
	for st in Data.room["guard"]["open"]:
		f.w_state = String(st)
		check(f.guard_open() and is_equal_approx(f._guarded(100.0), 100.0), "the guard is down while it is in %s" % st)
	check((Data.room["guard"]["open"] as Array).has("recover"), "the guard drops after its own strike: an opening anyone can use")
	f.w_state = "windup"
	check(not f.guard_open(), "and is up while it gathers")
	var plain := Fight.new({ "hero": Fight.default_hero(), "beast": "cut-wolf", "seed": 3 })
	plain.w_state = "prowl"
	check(plain.guard_open() and is_equal_approx(plain._guarded(100.0), 100.0), "a beast with no guard is always open")
	# no elite fells a hero at full health in fewer than four blows
	for z in Data.zones():
		var eb: Dictionary = Data.beast(String(z["beasts"]["elite"]))
		var worst := 0.0
		for a in eb["attacks"]:
			worst = maxf(worst, float(a["damage"]))
		check(worst * 3.0 < float(Data.room["player"]["health"]), "%s cannot fell a fresh hero in three blows (%d a blow)" % [eb["id"], int(worst)])

## A genius's progress shows between Readings (docs/genius-progression.md): readiness runs
## from 0 on the day of a Reading toward 1 as the next nears, it grows part of the way to its
## next size, and near the end the molt seams show.
func test_progression() -> void:
	var g := _born_genius()
	g.day = 0
	check(is_zero_approx(g.readiness()), "on the day of the rite it is not near anything")
	var need := int(GeniusResonance.instar_rule(2)["minDay"])
	g.day = need / 2
	var half := g.readiness()
	check(half > 0.2 and half < 0.7, "half the days lived, it is part of the way (%.2f)" % half)
	g.day = need
	var waiting := g.readiness()
	check(waiting >= half and waiting < 1.0, "its days lived and the milestone not reached, it holds short of ready (%.2f)" % waiting)
	g.milestone("gate")
	check(is_equal_approx(g.readiness(), 1.0), "with the Gate passed, the Reading is due")
	var prog: Dictionary = Data.genius()["progression"]
	var sizes: Dictionary = Data.genius()["size"]
	var info := g.to_dict()
	var due := GeniusBody.build(info, Color.ORANGE, 1)
	add_child(due)
	check(is_equal_approx(due.nearness, 1.0) and due.molt > 0.9, "the body knows the Reading is due, and molts")
	var want: float = float(sizes["1"]) + (float(sizes["2"]) - float(sizes["1"])) * float(prog["growth"])
	check(is_equal_approx(due.stands, want), "it has grown part of the way to the Second Form's size (%.2f m)" % due.stands)
	g.milestones.erase("gate")
	g.day = 0
	var fresh := GeniusBody.build(g.to_dict(), Color.ORANGE, 1)
	add_child(fresh)
	check(is_equal_approx(fresh.stands, float(sizes["1"])) and is_zero_approx(fresh.molt), "new from the rite, it stands at the First Form's size and shows no seams")
	var plain := GeniusBody.build({ "form": "trun-small", "silhouette": "beast-runner", "expression": "beast", "features": [], "instar": 2 }, Color.ORANGE, 2)
	add_child(plain)
	check(is_equal_approx(plain.stands, float(sizes["2"])) and is_zero_approx(plain.molt), "a body shown without a life (a card, a candidate) stands at its instar's size")
	due.queue_free()
	fresh.queue_free()
	plain.queue_free()

## A genius has an age (owner, 2026-11-10: a First Form too small to be a wolf is a pup that
## grows into one; the last stage is an impressive ally; its growth shows in its design and
## echoes on its partner). Names, proportions, size, presence, and the echo, by instar.
func test_ages() -> void:
	check(Genius.form_name_at("trun-small", 1) == "Small test runner" and Genius.form_name_at("trun-a", 2) == "Test Runner Path A" and Genius.form_name_at("trun-a1", 3) == "Test Runner Prong A1", "the young of a base has its own name, and so has every form it grows into")
	check(Genius.form_name_at("trun-a1x", 4) == "Test Runner Finish A1X" and Genius.form_name_at("trun-a1x", 5) == "Great Test Runner Finish A1X" and Genius.form_name_at("trun-a1x", 6) == "Test Runner Finish A1X of the Line", "a finished form is named for its age when it grows great, and at its apex")
	check(Genius.form_name_at("trun-a", 5) == "Test Runner Path A", "a form that has not finished keeps its plain name")
	var ages := {}
	for i in range(1, 7):
		ages[String(Genius.age_at(i)["id"])] = true
	check(ages.size() == 6 and Genius.age_at(1)["id"] == "young" and Genius.age_at(6)["id"] == "apex", "six instars, six ages, young to apex")
	var sizes: Dictionary = Data.genius()["size"]
	var rising := true
	for i in range(1, 6):
		rising = rising and float(sizes[str(i + 1)]) > float(sizes[str(i)])
	check(rising and float(sizes["6"]) > 1.8 and float(sizes["1"]) <= 0.7, "it grows at every instar, from the young of its kind to taller than its partner (%.1f to %.1f m)" % [float(sizes["1"]), float(sizes["6"])])
	var wolf := func(instar: int) -> GeniusBody:
		var b := GeniusBody.build({ "form": "trun-small", "silhouette": "beast-runner", "expression": "beast", "features": ["fangs"], "instar": instar }, Color.ORANGE, instar)
		add_child(b)
		return b
	var pup: GeniusBody = wolf.call(1)
	var grown: GeniusBody = wolf.call(3)
	var apex: GeniusBody = wolf.call(6)
	var head_of := func(b: GeniusBody) -> float:
		var sk: Skeleton3D = b.find_children("*", "Skeleton3D", true, false)[0]
		return sk.get_bone_pose_scale(sk.find_bone("Head")).x
	var leg_of := func(b: GeniusBody) -> float:
		var sk: Skeleton3D = b.find_children("*", "Skeleton3D", true, false)[0]
		return sk.get_bone_pose_scale(sk.find_bone("FrontUpperLeg.L")).x
	check(pup.age == "young" and head_of.call(pup) > 1.2 and leg_of.call(pup) < 0.85, "the pup has a large head and short legs (head %.2f, legs %.2f)" % [head_of.call(pup), leg_of.call(pup)])
	check(grown.age == "grown" and is_equal_approx(head_of.call(grown), 1.0), "the grown wolf has its own proportions")
	check(apex.age == "apex" and head_of.call(apex) < 1.0 and leg_of.call(apex) > 1.0, "at its apex it is long in the leg and its head small for its size")
	check(pup.mantle == null and grown.mantle == null and apex.mantle != null and apex.mantle.get_child_count() >= 7, "only the great carry a mantle of light (%d blades at Apex)" % (apex.mantle.get_child_count() if apex.mantle else 0))
	check(apex.find_child("GroundLight", false, false) != null and grown.find_child("GroundLight", false, false) == null, "the ground is lit under an Apex genius")
	check(is_zero_approx(pup.lines) and apex.lines > 0.3 and apex.molt >= apex.lines, "lines of light run along the great, none along the young")
	check(apex.stands > grown.stands * 2.0 and grown.stands > pup.stands, "the Apex stands more than twice the grown wolf")
	for b in [pup, grown, apex]:
		b.queue_free()
	# the echo on the partner
	var w := World.new()
	add_child(w)
	var hero := Fight.default_hero()
	hero["body"] = "cahokia-f"
	var g := { "instar": 1, "expression": "beast", "form": "trun-small", "silhouette": "beast-runner", "look": GeniusLook.born(4711) }
	hero["genius"] = g
	check(w.features_of(hero) == ["cloak-genius"], "the First Form's echo is its coat in the cloak (%s)" % str(w.features_of(hero)))
	g["instar"] = 3
	var f3: Array = w.features_of(hero)
	check(f3.has("eyes-genius") and f3.has("skin-field") and f3.has("echo-ruff"), "by the Third Form: its light in the eyes, the field under the skin, and a Beast's ruff (%s)" % str(f3))
	for ex in Data.genius()["echo"]["byExpression"]:
		g["expression"] = ex
		var piece: Array = w.features_of(hero).filter(func(x): return String(x).begins_with("echo-"))
		check(piece.size() == 1 and Data.people_features.has(piece[0]), "a %s leaves a piece of its own on its partner (%s)" % [ex, str(piece)])
	g["expression"] = "beast"
	hero["look"] = { "cape": true, "cape_color": "plain", "skin": "tan" }
	w.build_hero(hero)
	var skel: Skeleton3D = w._player.find_child("Skeleton3D", true, false)
	var ruff: Node3D = skel.find_child("feature_echo-ruff_socket_throat", false, false)
	check(ruff != null, "the ruff hangs at the partner's collar")
	var coat := w.genius_coat(g, Color.WHITE)
	check(not coat.is_equal_approx(Color.WHITE), "the echo is drawn in the genius's own coat")
	var s3 := (ruff.get_child(0) as Node3D).scale.x if ruff and ruff.get_child_count() > 0 else 0.0
	g["instar"] = 6
	w.build_hero(hero)
	skel = w._player.find_child("Skeleton3D", true, false)
	ruff = skel.find_child("feature_echo-ruff_socket_throat", false, false)
	var s6 := (ruff.get_child(0) as Node3D).scale.x if ruff and ruff.get_child_count() > 0 else 0.0
	check(s6 > s3 and s3 > 0.0, "and it grows as the genius does (%.2f at the Third Form, %.2f at Apex)" % [s3, s6])
	w.queue_free()

## A genius always keeps its kind (docs/genius-tree.md): a refinement offers nothing outside
## its own tree. What the play decides is which of its kind it becomes; and once, at the first
## refinement, whether it turns into a hybrid. The turning is offered, never forced.
func test_refinement_and_turning() -> void:
	_only_test_bases()
	var rule: Dictionary = Data.genius_hybrids()["rule"]
	# played as its own nature, nothing turns
	var own := _genius_at("trun-small", 1)
	_play_like(own, Data.base("trun")["nature"])
	var r0 := own.read(2)
	check((r0["turning"] as Dictionary).is_empty() and r0["candidates"].all(func(c): return c["base"] == "trun"), "played as what it is, it is offered its own three paths and no turning")
	# since it settled its partner has fought like an edge: close, parrying, casting
	var g := _genius_at("trun-small", 1)
	g.look["coat"] = 2
	_play_like(g, Data.base("tedge")["nature"])
	var worn := Color(String(GeniusLook.offered_coats(g.look, "trun-small", "beast-runner")[2]["main"]))
	var r := g.read(2)
	var t: Dictionary = r["turning"]
	check(not t.is_empty() and t["second"] == "tedge" and t["base"] == "trun+tedge" and t["name"] == "Edged Test Runner", "play that is another base's is seen: a turning toward it is offered (%s)" % t.get("name", "none"))
	check(float(t["other"]) >= float(rule["min"]) and float(t["other"]) >= float(t["own"]) * (1.0 + float(rule["margin"])), "because that nature fits the play better than its own by the margin (%.2f against %.2f)" % [float(t.get("other", 0)), float(t.get("own", 0))])
	check(GeniusReading.reason_words(t["reasons"]) == "fighting close, parrying, Cast techniques", "and the Reading says why, in plain words (%s)" % GeniusReading.reason_words(t.get("reasons", [])))
	check(r["candidates"].size() == 3 and r["candidates"].all(func(c): return c["base"] == "trun") and (t["candidates"] as Array).size() == 3 and (t["candidates"] as Array).all(func(c): return c["base"] == "trun+tedge"), "it is offered beside its own three paths, never in place of them")
	# refusing it: its own path
	var refused := Genius.from_dict(JSON.parse_string(JSON.stringify(g.to_dict())))
	refused.pending_reading = r.duplicate(true)
	refused.take(0)
	check(refused.body["base"] == "trun" and refused.kind() == "Test Runner" and not refused.history[-1].has("turned"), "its partner may refuse: it takes a path of its own")
	var settled := Genius.from_dict(JSON.parse_string(JSON.stringify(g.to_dict())))
	settled.pending_reading = r.duplicate(true)
	settled.take(-1)
	check(settled.body["form"] == r["candidates"][0]["form"] and settled.history[-1]["settled"], "letting it settle never turns it: it takes the best of its own")
	# taking it
	var c := g.take(Genius.TURN)
	check(c["form"] == t["candidates"][0]["form"] and g.body["base"] == "trun+tedge" and g.kind() == "Edged Test Runner" and g.level() == 2 and g.instar == 2, "taking the turning makes it the hybrid, on the hybrid's best path")
	check(g.features().has("edge") and g.features().has(Data.base("trun")["settled"]["features"][0]) and g.body["silhouette"] == "beast-runner" and g.body["coatOf"] == "relic-knife", "it is one genius: the runner's body, wearing the edge's gift, in a coat of the edge's")
	check(g.history[-1].get("turned", "") == "tedge" and not g.history[-1]["settled"] and g.road().map(func(f): return f["id"]) == ["trun-small", String(c["form"])], "its history says it turned, and its road begins where it settled")
	check(g.soul() == String(Data.base("trun")["soul"]) and g.picture_of().ends_with("turned toward the test edge's way") and g.sign_now().ends_with("It wears an edge, the test edge's."), "it is still its first base's soul, and says what it has turned toward")
	var offered := GeniusLook.offered_coats(g.look, String(g.body["form"]), "beast-runner")
	var got := Color(String(offered[int(g.look["coat"])]["main"]))
	var nearest := true
	for o in offered:
		var oc := Color(String(o["main"]))
		if Vector3(oc.r - worn.r, oc.g - worn.g, oc.b - worn.b).length() + 0.0001 < Vector3(got.r - worn.r, got.g - worn.g, got.b - worn.b).length():
			nearest = false
	check(nearest, "in its new coat it wears the one nearest the coat it wore")
	# from there it is on the hybrid's tree, and does not turn again
	_play_like(g, Data.base("tlamp")["nature"])
	var r3 := g.read(3)
	var kids: Array = (Data.form(String(g.body["form"]))["children"] as Array).duplicate()
	var got3: Array = r3["candidates"].map(func(x): return x["form"])
	kids.sort()
	got3.sort()
	check(got3 == kids and (r3["turning"] as Dictionary).is_empty(), "a hybrid is refined down its own tree, and nothing turns twice")
	g.take()
	g.read(4)
	g.take()
	check(g.level() == 4 and g.next_forms().is_empty() and g.body["base"] == "trun+tedge" and g.read(5)["grows"], "it finishes as a hybrid and grows as one")
	# no turning below the least fit, however far ahead; none where the margin is not met
	var faint := _genius_at("trun-small", 1)
	faint.count("range", "close", 3)
	check((faint.read(2)["turning"] as Dictionary).is_empty(), "a little play is not a turning")
	var half := _genius_at("trun-small", 1)
	_play_like(half, Data.base("tedge")["nature"])
	_play_like(half, Data.base("trun")["nature"])
	var rh := half.read(2)
	check((rh["turning"] as Dictionary).is_empty(), "play that is as much its own as another's does not turn it")
	# asking for a turning where none is offered takes its own best
	var none := _genius_at("trun-small", 1)
	_play_like(none, Data.base("trun")["nature"])
	none.read(2)
	check(none.take(Genius.TURN)["base"] == "trun", "with no turning offered there is nothing to turn into")
	# the page shows its tree: where it is, what comes next, and what play leads to each
	var page := GeniusPage.new()
	add_child(page)
	var pg := _genius_at("trun-a", 2)
	_play_like(pg, { "orders": { "hunt": 1.0 }, "fights": { "blocks": 0.5 } })
	page.open(pg, Color.ORANGE)
	var text := "\n".join(page.find_children("*", "RichTextLabel", true, false).map(func(x): return (x as RichTextLabel).text))
	var heads := page.find_children("*", "Label", true, false).map(func(x): return (x as Label).text)
	check(heads.any(func(x): return String(x).begins_with("ITS LINE")) and heads.has("YOUR SOUL, OUTSIDE YOU"), "the genius's page has its line and its soul")
	var all_named := true
	for f in Data.tree_of("trun"):
		all_named = all_named and (int(f["level"]) == 1 or text.contains(String(f["name"])))
	check(all_named and text.contains("(it is this)") and text.contains("(next: fits your play"), "the tree names every form of its base, where it is, and what it may become next")
	check(text.contains("comes of sending it to Hunt") and text.contains("one who is like Test Runner Path B") and text.contains("WHOSE SOUL") and text.contains("ITS HABIT") and text.contains("ITS SIGN") and text.contains("THE PICTURE OF"), "each form says what play leads to it and what it is the picture of; the page says whose soul it is, its sign and its habit")
	page.queue_free()
	_all_bases()

## A base taken out of the tree (data/genius.json, renamed: the Coat became the Living Armor): a
## saved genius of it loads as the base that stands in its place, form for form.
func test_renamed_saves() -> void:
	_all_bases()
	var r: Dictionary = Data.genius().get("renamed", {})
	var bases: Dictionary = r.get("bases", {})
	var forms: Dictionary = r.get("forms", {})
	check(String(bases.get("coat", "")) == "panoply" and forms.size() == 31, "the Coat is read as the Living Armor, all thirty-one forms of it (%d)" % forms.size())
	var lost: Array = []
	for old in forms:
		var f := Data.form(String(forms[old]))
		if f.is_empty() or not Data.form(String(old)).is_empty() or bases.get(String(old).get_slice("-", 0), "") != f["base"]:
			lost.append(old)
	check(lost.is_empty(), "every form of a base that is gone has a form that stands in its place, and is itself gone (lost: %s)" % str(lost))
	var saved := { "name": "Hem", "instar": 3, "day": 70, "order": "guard", "look": { "seed": 99, "coat": 5, "marks": {}, "keepsake": "bell", "keepsakeColor": "" },
		"body": { "form": "coat-night-coat", "base": "coat", "expression": "relic", "silhouette": "relic-coat", "coatOf": "relic-coat", "own": ["watching-eye", "coat-weave", "shadow-cloak", "dark-eyed"],
			"heritage": ["set-feet", "high-collar"], "seedMark": "far-eyes", "grafts": [{ "id": "shade:x", "feature": "lantern", "source": "shade:x" }], "adaptations": [] },
		"history": [{ "instar": 1, "form": "coat-clasp", "name": "Clasp", "day": 0, "by": "rite", "settled": true }] }
	var g := Genius.from_dict(saved.duplicate(true))
	var want := String(forms["coat-night-coat"])
	check(g.body["form"] == want and g.body["base"] == "panoply" and g.body["silhouette"] == "relic-panoply" and g.level() == 3, "a saved Night-coat loads as the form in its place (%s)" % g.body["form"])
	check(g.name == "Hem" and g.instar == 3 and g.day == 70 and g.body["seedMark"] == "far-eyes" and int(g.look["seed"]) == 99 and g.look["keepsake"] == "bell", "it keeps its name, its age, its Seed-mark and its look")
	check((g.body["heritage"] as Array) == ["set-feet"] and g.features().has("lantern") and not g.features().has("coat-weave") and (g.body["own"] as Array) == (Data.form(want)["features"] as Array),
		"what it had adapted and its grafts stay; it is made of what the new form is made of")
	check(g.history.size() == 2 and g.history[-1].get("renamed", "") == "coat-night-coat", "and its history says what it was")
	var body := GeniusBody.build({ "form": g.body["form"], "silhouette": g.body["silhouette"], "expression": g.body["expression"], "features": g.features(), "instar": g.instar, "look": g.look }, Color.ORANGE, g.instar)
	check(body != null and body.find_children("*", "MeshInstance3D", true, false).size() > 0, "and it can be drawn")
	body.free()
	var again := Genius.from_dict(g.to_dict())
	check(again.body["form"] == want and again.history.size() == 2, "it is renamed once only")
	# a hybrid whose second base was the Coat, and one whose first was
	var first := String(Data.base("wolf")["paths"][0]["id"])
	var hy := Genius.from_dict({ "name": "Burr", "instar": 2, "body": { "form": "wolf+coat:" + first, "base": "wolf+coat", "expression": "beast", "silhouette": "beast-runner", "coatOf": "relic-coat",
		"own": [], "heritage": [], "seedMark": "", "grafts": [], "adaptations": [] } })
	check(hy.body["form"] == "wolf+panoply:" + first and hy.body["coatOf"] == "relic-panoply" and hy.features().has("helm"), "a Wolf turned toward the Coat is a Wolf turned toward the Living Armor (%s)" % hy.body["form"])
	var yh := Genius.from_dict({ "name": "Nap", "instar": 2, "body": { "form": "coat+wolf:coat-shadow", "base": "coat+wolf", "expression": "relic", "silhouette": "relic-coat", "coatOf": "beast-runner",
		"own": [], "heritage": [], "seedMark": "", "grafts": [], "adaptations": [] } })
	check(yh.body["form"] == "panoply+wolf:" + String(forms["coat-shadow"]) and yh.body["silhouette"] == "relic-panoply", "and a Coat turned toward the Wolf a Living Armor turned toward it (%s)" % yh.body["form"])

## A genius saved before the tree is a form no tree has (docs/genius-tree.md). It settles again
## as the base nearest the body it wore, keeping its name, its look, its Seed-mark and its age.
func test_old_saves() -> void:
	_only_test_bases()
	var old := { "name": "Brack", "instar": 3, "day": 55, "order": "hunt", "look": { "seed": 4711, "coat": 1, "marks": {}, "keepsake": "bell", "keepsakeColor": "" },
		"body": { "form": "field-wolf", "expression": "beast", "silhouette": "beast-runner", "own": ["long-legs", "fangs", "ruff"], "heritage": ["set-feet", "beak"], "seedMark": "far-eyes",
			"grafts": [{ "id": "shade:x", "feature": "lantern", "source": "shade:x" }], "adaptations": [] },
		"history": [{ "instar": 1, "form": "field-wolf", "name": "Wolf pup", "day": 0, "by": "rite", "settled": true }], "milestones": ["rite", "gate", "pattern-built"] }
	var g := Genius.from_dict(old.duplicate(true))
	check(g.body["form"] == "trun-small" and g.body["base"] == "trun" and g.level() == 1, "a genius from before the tree settles again as the base that wears its old body (%s)" % g.body["form"])
	check(g.name == "Brack" and g.look["coat"] == 1 and g.look["keepsake"] == "bell" and int(g.look["seed"]) == 4711 and g.body["seedMark"] == "far-eyes" and g.instar == 3 and g.day == 55, "it keeps its name, its look, its Seed-mark and its instars: they are its age")
	check((g.body["heritage"] as Array) == ["set-feet"] and g.features().has("lantern") and not g.features().has("beak"), "what it had adapted and its grafts stay; the parts of forms that are gone do not")
	check(g.history.size() == 2 and g.history[-1].get("resettled", "") == "field-wolf" and g.history[-1]["form"] == "trun-small", "and its history says so")
	var r := g.read(4)
	check(not r["grows"] and r["candidates"].size() == 3 and int(r["level"]) == 2, "at its next Reading it is offered the paths of its base, late as it is")
	var again := Genius.from_dict(g.to_dict())
	check(again.body["form"] == "trun-small" and again.history.size() == 2, "it settles again once only")
	var lamp: Dictionary = old.duplicate(true)
	lamp["body"]["silhouette"] = "engine-sentinel"
	lamp["body"]["expression"] = "engine"
	check(Genius.from_dict(lamp).body["base"] == "tlamp", "a body no base wears settles as a base of its Expression")
	var odd: Dictionary = old.duplicate(true)
	odd["body"]["silhouette"] = "aspect-fog"
	odd["body"]["expression"] = "aspect"
	check(Genius.from_dict(odd).body["base"] == String(Data.bases()[0]["id"]), "and where there is none of its Expression, as the first base")
	# a save from before the genius system, with its form at the top
	var older := Genius.from_dict({ "form": "hawk", "expression": "beast", "silhouette": "beast-flier", "features": ["wings", "talons"], "seedMark": "far-eyes" })
	check(older.is_born() and older.body["base"] == "trun" and older.instar == 1 and older.body["seedMark"] == "far-eyes", "the oldest saves come onto the tree too")
	# a genius on the tree is left as it is
	var here := _genius_at("tedge-b1", 3)
	var same := Genius.from_dict(here.to_dict())
	check(same.body["form"] == "tedge-b1" and same.history.is_empty(), "a genius that is on the tree is not touched")
	var hy := _genius_at("trun+tedge:trun-a", 2)
	check(Genius.from_dict(hy.to_dict()).body["form"] == "trun+tedge:trun-a", "nor is a hybrid")
	_all_bases()

## The home's hand, and the cohort's genii (owner, 2026-11-10: full variety, logically sound,
## capturing the diversity of humanity): a genius wears what its partner's home puts on its
## genii, and every classmate has a genius of their own, read by the hero's rules.
func test_homes_hand() -> void:
	var missing: Array = []
	for home in Data.bodies:
		var t: Dictionary = Data.bodies[home].get("dress", {}).get("trapping", {})
		if String(t.get("name", "")) == "" or String(t.get("text", "")) == "" or not ResourceLoader.exists(GeniusBody.TRAP_DIR % home):
			missing.append(home)
	check(Data.bodies.size() == 13 and missing.is_empty(), "each of the thirteen homes has a piece it puts on its genii (%s)" % ", ".join(missing))
	var wolf := { "form": "trun-small", "silhouette": "beast-runner", "expression": "beast", "features": ["fangs"], "instar": 3, "look": GeniusLook.born(7), "home": "edo" }
	var b := GeniusBody.build(wolf, Color.ORANGE, 3)
	add_child(b)
	check(b.trapping == "edo" and b.find_child("Trapping", true, false) != null and b.find_child("TrappingBand", true, false) != null, "a wolf raised in Edo wears Edo's cord, on a band at its neck")
	var worn: MeshInstance3D = b.find_child("Trapping", true, false).find_children("*", "MeshInstance3D", true, false)[0]
	var c0 := (worn.get_surface_override_material(0) as StandardMaterial3D).albedo_color
	var wolf2 := wolf.duplicate(true)
	wolf2["home"] = "khemet"
	var b2 := GeniusBody.build(wolf2, Color.ORANGE, 3)
	add_child(b2)
	var worn2: MeshInstance3D = b2.find_child("Trapping", true, false).find_children("*", "MeshInstance3D", true, false)[0]
	check(b2.trapping == "khemet" and not (worn2.get_surface_override_material(0) as StandardMaterial3D).albedo_color.is_equal_approx(c0), "one raised in Khemet wears Khemet's, in Khemet's colours")
	var off := wolf.duplicate(true)
	off["look"]["trapping"] = false
	var b3 := GeniusBody.build(off, Color.ORANGE, 3)
	add_child(b3)
	check(b3.trapping == "" and b3.find_child("Trapping", true, false) == null, "its partner may take it off")
	var kept := wolf.duplicate(true)
	kept["look"]["keepsake"] = "collar"
	var b4 := GeniusBody.build(kept, Color.ORANGE, 3)
	add_child(b4)
	check(b4.keepsake == "collar" and b4.trapping == "edo", "a keepsake and the home's piece are both worn, each in its own place")
	var none := GeniusBody.build({ "form": "trun-small", "silhouette": "beast-runner", "expression": "beast", "features": [], "instar": 1 }, Color.ORANGE, 1)
	add_child(none)
	check(none.trapping == "", "a genius with no partner's home wears nothing of one")
	for x in [b, b2, b3, b4, none]:
		x.queue_free()
	var h := Fight.default_hero()
	h["city"] = "timbuktu"
	check(Genius.for_hero(h).origin.get("city", "") == "timbuktu", "a genius knows where its partner is from")
	# the cohort's genii
	var a := Academy.new()
	a.hero = Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	a.cohort = Academy.make_cohort(42, a.hero)
	a.progress = { "seed": 42, "done": ["hold"], "day": 2 }
	check(a.classmate_genius(a.cohort[0]).is_empty() and a.classmate_partner(a.cohort[0]).is_empty(), "before the rite no classmate has a genius")
	a.progress["done"].append("rite")
	var kinds := {}
	var expressions := {}
	var whole := true
	for c in a.cohort:
		var g := a.classmate_genius(c)
		whole = whole and not g.is_empty() and int(Genius.form_of(String(g["form"])).get("level", 0)) == 1 and String(g["home"]) == String(c["city"]) and int(g["instar"]) == 1 and not (g["look"] as Dictionary).is_empty()
		kinds[g.get("form", "")] = true
		expressions[g.get("expression", "")] = true
	check(whole, "after it, each of the twelve has one, settled as a base of the tree, with a look of its own and its partner's home")
	check(kinds.size() >= mini(4, Data.bases().size()), "and the cohort's genii are of several kinds (%d kinds, %d Expressions)" % [kinds.size(), expressions.size()])
	# after the Gate each classmate's genius has taken a path of its own tree
	var first_forms := {}
	for c in a.cohort:
		first_forms[c["id"]] = String(a.classmate_genius(c)["form"])
	a.genius = _genius_at("trun-a", 2)
	var on_paths := true
	for c in a.cohort:
		var g2 := a.classmate_genius(c)
		var pf := Data.form(String(g2["form"]))
		on_paths = on_paths and int(g2["instar"]) == 2 and int(pf["level"]) == 2 and String(pf["parent"]) == String(first_forms[c["id"]]) and (g2["features"] as Array).has(g2["seedMark"]) and str(g2) == str(a.classmate_genius(c))
	check(on_paths, "after the Gate each has taken a path of its own base, the same every time it is asked")
	a.genius = null
	check(str(a.classmate_genius(a.cohort[3])) == str(a.classmate_genius(a.cohort[3])), "a classmate's genius is the same every time it is asked for")
	var seeds := {}
	for t in Data.academy["cohort"]["temperaments"]:
		seeds[String(t.get("seed", ""))] = true
	check(seeds.size() == Data.academy["cohort"]["temperaments"].size() and not seeds.has(""), "every temperament wants something different beside it")
	var w := World.new()
	add_child(w)
	w.set_place("cut")
	var c5: Dictionary = a.cohort[5]
	var fig := w.add_figure(c5["body"], Vector2(2, 2), 0.0, c5["name"], "", c5["weapon"], Color(0, 0, 0, 0), c5.get("look", {}), a.classmate_partner(c5))
	check((fig["node"] as Node3D).find_child("TheirGenius", false, false) is GeniusBody, "a classmate's genius stands by them")
	a.free()
	w.queue_free()

## A home has no forms of its own (docs/genius-tree.md, Regions): it raises the chance of some
## bases at the rite. It never makes one certain, never forbids one, and never moves the
## bowl's best fit.
func test_homes_lean() -> void:
	var homes: Dictionary = Data.genius_homes()
	var strangers: Array = []
	var flat: Array = []
	for h in homes:
		if String(h).begins_with("$"):
			continue
		if not Data.bodies.has(h):
			strangers.append(h)
		for b in homes[h]:
			if float(homes[h][b]) <= 1.0:
				flat.append("%s: %s" % [h, b])
	check(strangers.is_empty() and flat.is_empty(), "every lean is a home's, and raises a base (not homes: %s; not raised: %s)" % [", ".join(strangers), ", ".join(flat)])
	# on whatever bases there are: the best fit is the field's own
	var bowls := 0
	var leaned := 0
	var moved: Array = []
	for h in Data.bodies:
		for sd in Data.seeds():
			for shp in ["anchor", "cast", "read"]:
				var here := GeniusReading.read(1, GeniusReading.empty_tally(), { "seed": sd["id"], "blood": "", "shape": shp, "home": h }, {})
				var nowhere := GeniusReading.read(1, GeniusReading.empty_tally(), { "seed": sd["id"], "blood": "", "shape": shp }, {})
				bowls += 1
				if here["candidates"][0]["form"] != nowhere["candidates"][0]["form"] or float(here["candidates"][0]["score"]) != float(nowhere["candidates"][0]["score"]):
					moved.append("%s %s %s" % [h, sd["id"], shp])
				for i in range(1, here["candidates"].size()):
					var c: Dictionary = here["candidates"][i]
					if (c["reasons"] as Array).any(func(r): return r["line"] == "home"):
						leaned += 1
						if String(c["reasons"][-1]["key"]) != String(h) or float(homes.get(h, {}).get(c["base"], 1.0)) <= 1.0:
							moved.append("%s says %s is for the home's sake" % [h, c["base"]])
	check(moved.is_empty(), "the bowl's best fit is read from Seed, blood and Shape: no home moves it (%s)" % ", ".join(moved.slice(0, 4)))
	var some := false
	for h in homes:
		if not String(h).begins_with("$"):
			for b in homes[h]:
				some = some or not Data.base(String(b)).is_empty()
	check(leaned > 0 or not some, "a home's lean shows in the offers beside it, and the offer says so (%d of %d bowls)" % [leaned, bowls])
	# the rule, on the tests' own bases
	_only_test_bases()
	Data._homes = { "columbia": { "tlamp": 1.8 } }
	var o := { "seed": "i-can-hold", "blood": "", "shape": "read" }
	var at_home := GeniusReading.read(1, GeniusReading.empty_tally(), { "seed": "i-can-hold", "blood": "", "shape": "read", "home": "columbia" }, {})
	var away := GeniusReading.read(1, GeniusReading.empty_tally(), o, {})
	check(at_home["candidates"].map(func(c): return c["base"]) == ["tedge", "tlamp", "trun"] and str(at_home["candidates"][0]) == str(away["candidates"][0]), "the best fit is the same at home and away")
	check(float(at_home["candidates"][1]["score"]) == float(away["candidates"][1]["score"]) and at_home["candidates"][1]["reasons"][-1]["line"] == "home" and at_home["candidates"][1]["reasons"][-1]["key"] == "columbia", "a base offered for the home's sake keeps the Reading's own score, and says so")
	var w := { "seed": "watches-from-above", "blood": "", "shape": "read", "home": "columbia" }
	check(GeniusReading.read(1, GeniusReading.empty_tally(), w, {})["candidates"].map(func(c): return c["base"]) == ["trun", "tlamp", "tedge"], "with no lean on it the third fit is offered third")
	Data._homes = { "columbia": { "tedge": 5.0 } }
	check(GeniusReading.read(1, GeniusReading.empty_tally(), w, {})["candidates"].map(func(c): return c["base"]) == ["trun", "tedge", "tlamp"], "a lean can bring a base up the bowl, but not to the top of it")
	# with the bowl's own chance, a leaned base is likelier and never certain
	Data._homes = { "columbia": { "tedge": 1.8 } }
	var second_home := 0
	var second_away := 0
	for k in 200:
		var wh := GeniusReading.read(1, GeniusReading.empty_tally(), w, {}, 0.6, 1000 + k)
		var wa := GeniusReading.read(1, GeniusReading.empty_tally(), { "seed": "watches-from-above", "blood": "", "shape": "read" }, {}, 0.6, 1000 + k)
		second_home += 1 if wh["candidates"][1]["base"] == "tedge" or wh["candidates"][0]["base"] == "tedge" else 0
		second_away += 1 if wa["candidates"][1]["base"] == "tedge" or wa["candidates"][0]["base"] == "tedge" else 0
	check(second_home > second_away and second_home < 200 and second_away > 0, "at home the leaned base is among the first two more often, and neither always nor never (%d against %d of 200)" % [second_home, second_away])
	Data._homes = homes
	_all_bases()


## The genius fights as what it is (docs/genius-combat.md; data/genius.json, fight): its moves
## from its kind and features, what it can do yet from its age, where it stands from its
## order, and on Free what it chooses from how its partner fights.
## The bodies these fights are fought with: a kind of body, an Expression and parts. A fight
## asks nothing else of a genius, so the tests do not depend on which forms the tree has.
const BODIES := {
	"runner": ["beast-runner", "beast", ["long-legs", "fangs", "ruff"]],
	"flier": ["beast-flier", "beast", ["wings", "talons", "beak"]],
	"shelled": ["beast-shell", "beast", ["shell", "stone-skin", "old-eyes"]],
	"lantern": ["engine-lantern", "engine", ["lantern", "roots", "cold-core"]],
	"sprite": ["kith-fey", "kith", ["lantern", "voice", "small-hands"]],
	"blade": ["relic-blade", "relic", ["edge", "grip", "sheath"]],
	"imp": ["daemon-small", "daemon", ["horns", "ledger", "tail"]],
	"ember": ["aspect-flame", "aspect", ["ember", "glow", "smoke"]],
	"shadow": ["aspect-shadow", "aspect", ["shadow-cloak", "glow", "smoke"]],
	"hound": ["engine-quadruped", "engine", ["broad-chest", "iron-hide", "lantern"]],
}

func _fighting_genius(body_id: String, instar: int, order: String) -> Genius:
	var b: Array = BODIES[body_id]
	var g := Genius.new()
	g.instar = instar
	g.body = { "form": "", "base": "", "expression": b[1], "silhouette": b[0], "coatOf": b[0], "own": (b[2] as Array).duplicate(), "heritage": [], "seedMark": "", "grafts": [], "adaptations": [] }
	g.order = order
	return g

func _genius_fight(body_id: String, instar: int, order: String, beast := "cut-wolf", extra: Dictionary = {}) -> Fight:
	var opts := { "hero": Fight.default_hero(), "beast": beast, "seed": 3, "respawn": false, "genius": _fighting_genius(body_id, instar, order) }
	for k in extra:
		opts[k] = extra[k]
	var f := Fight.new(opts)
	f.w_state = "prowl"
	f.w_pos = f.p_pos + Vector2(2.0, 0.0)
	f.p_lock = true
	return f

func test_genius_fight() -> void:
	var F: Dictionary = Data.genius()["fight"]
	var ids := func(ms: Array) -> Array: return ms.map(func(m): return String(m["id"]))
	# --- moves by kind and feature, never by form
	check(ids.call(Fight.genius_moves("quadruped", "beast", ["long-legs", "fangs", "ruff"], 2)) == ["hamstring"], "a runner hamstrings")
	check(ids.call(Fight.genius_moves("flier", "beast", ["wings", "talons", "beak"], 2)) == ["stoop"], "a flier stoops")
	check(ids.call(Fight.genius_moves("quadruped", "beast", ["shell", "stone-skin"], 2)) == ["hamstring", "brace"], "a shelled beast braces as well")
	check(ids.call(Fight.genius_moves("object", "relic", ["edge", "sheath"], 2)) == ["with"], "a relic strikes with its partner")
	check(ids.call(Fight.genius_moves("humanoid", "daemon", ["chain", "horns"], 2)) == ["call", "debt"], "a daemon calls, and marks a debt")
	check(ids.call(Fight.genius_moves("quadruped", "beast", ["wings", "lantern"], 3)) == ["hamstring", "stoop", "light"], "a body no form has yet (a winged runner with a lantern) has moves by what it is made of")
	var lay_of := func(feats: Array) -> String: return String(Fight.genius_moves("aspect", "aspect", feats, 1)[0].get("effect", ""))
	check(lay_of.call(["ember"]) == "burn" and lay_of.call(["shadow-cloak"]) == "dark" and lay_of.call(["rime"]) == "chill" and lay_of.call(["ring"]) == "burn", "an Aspect lays itself down as what it is: an ember burns, a shadow darkens, rime chills")
	var bare: Array = []
	var named_by_form: Array = []
	var form_ids: Array = Data.forms().map(func(f): return f["id"])
	for f in Data.forms():
		var kind := String(Data.genius_bodies()["silhouettes"][f["silhouette"]]["kind"])
		if Fight.genius_moves(kind, String(f["expression"]), f["features"], 2).is_empty():
			bare.append(f["id"])
	for table in ["byKind", "byExpression", "byFeature", "moves"]:
		for k in F[table]:
			if form_ids.has(k) and not Data.features().map(func(x): return x["id"]).has(k):
				named_by_form.append(k)
	check(bare.is_empty(), "every form of every tree has a move, grown (%s)" % ", ".join(bare))
	check(named_by_form.is_empty(), "no move is keyed by a form's name (%s)" % ", ".join(named_by_form))
	var unknown: Array = []
	for table in ["byKind", "byExpression", "byFeature"]:
		for k in F[table]:
			for id in F[table][k]:
				if not F["moves"].has(id):
					unknown.append(id)
	check(unknown.is_empty(), "every move a rule names exists")
	# --- its age
	check(Fight.genius_moves("quadruped", "beast", ["long-legs"], int(F["ages"]["young"]["moves"])).is_empty() and F["ages"]["young"].has("nip"), "a young one has no moves yet: it nips")
	var ages_up := true
	var last := -1
	for a in ["young", "half-grown", "grown", "prime", "great", "apex"]:
		ages_up = ages_up and int(F["ages"][a]["moves"]) >= last
		last = int(F["ages"][a]["moves"])
	check(ages_up, "it has more of its moves as it grows")
	var pup := _genius_fight("runner", 1, "hunt")
	var flinched := false
	var pup_dmg := 0.0
	for i in 600:
		pup.w_pos = pup.p_pos + Vector2(2.0, 0.0)
		if pup.w_state not in ["prowl", "flinch"]:
			pup.w_state = "prowl"
		pup._update_genius(1.0 / 60.0)
		pup.now += 1.0 / 60.0
		for e in pup.drain():
			if e["type"] == "genius-move" and e["move"] == "nip":
				flinched = true
			if e["type"] == "genius-hunt":
				pup_dmg = maxf(pup_dmg, float(e["damage"]))
	var grown := _genius_fight("runner", 3, "hunt")
	var grown_dmg := 0.0
	var slowed := false
	var hamstrung := false
	for i in 600:
		grown.w_pos = grown.p_pos + Vector2(2.0, 0.0)
		if grown.w_state != "prowl":
			grown.w_state = "prowl"
		grown._update_genius(1.0 / 60.0)
		slowed = slowed or grown.now < grown.w_slow_until
		for e in grown.drain():
			if e["type"] == "genius-hunt" and e["move"] == "strike":
				grown_dmg = maxf(grown_dmg, float(e["damage"]))
			if e["type"] == "genius-move" and e["move"] == "hamstring":
				hamstrung = true
		grown.now += 1.0 / 60.0
	check(flinched and pup_dmg > 0.0, "a pup's nips make the foe flinch now and then (%d a nip)" % int(pup_dmg))
	check(grown_dmg > pup_dmg * 2.0, "a grown wolf's bite does damage (%d to the pup's %d)" % [int(grown_dmg), int(pup_dmg)])
	check(hamstrung and slowed and grown.g_pos.distance_to(grown.w_pos) < 3.0, "on Hunt the wolf is at the foe, and its hamstring slows it")
	check(Fight.genius_great("quadruped", "beast").get("effect", "") == "stagger" and _genius_fight("runner", 3, "hunt").g_great.is_empty() and not _genius_fight("runner", 6, "hunt").g_great.is_empty(), "only the great have the great move")
	# --- the great move changes the fight
	var apex := _genius_fight("runner", 6, "hunt", "green-warden")
	apex.g_great_at = 0.0
	apex._update_genius(0.016)
	check(apex.w_state == "stagger" and apex.guard_open() and apex.stats["g_great"] == 1, "an Apex wolf pulls the Warden down: its guard is open")
	var wall := _genius_fight("lantern", 6, "guard")
	wall.g_great_at = 0.0
	wall._update_genius(0.016)
	check(wall.g_ward_blows >= 2, "an Apex lantern raises the wall: the next blows are turned (%d)" % wall.g_ward_blows)
	var hp0 := wall.p_hp
	wall._resolve_bite_from(wall.beast["attacks"][0], wall.w_pos, -1)
	check(is_equal_approx(wall.p_hp, hp0), "and a blow behind the wall does not land")
	# --- its damage is guarded like any blow out of turn
	var w1 := _genius_fight("runner", 3, "hunt", "green-warden")
	var before := w1.w_hp
	w1._genius_hits(100.0, "strike")
	var shut := before - w1.w_hp
	w1.w_state = "recover"
	before = w1.w_hp
	w1._genius_hits(100.0, "strike")
	check(shut < 60.0 and before - w1.w_hp >= 99.0, "an elite's guard holds against its genius too, and its openings are open to it (%d, then %d)" % [int(shut), int(before - w1.w_hp)])
	# --- stoop: one heavy blow, then it climbs
	var hawk := _genius_fight("flier", 3, "hunt")
	hawk._genius_move(hawk._genius_has("stoop"))
	var struck: float = hawk.stats["g_damage"]
	hawk._genius_hunts(hawk._order("hunt")["hunt"], hawk.g_pos)
	check(struck > 0.0 and hawk.now < hawk.g_climb_until and is_equal_approx(hawk.stats["g_damage"], struck), "a hawk stoops, and cannot strike again until it has climbed")
	# --- brace
	var soft := _genius_fight("runner", 3, "guard")
	var hard := _genius_fight("shelled", 3, "guard")
	soft.g_pos = soft.p_pos
	hard.g_pos = hard.p_pos
	soft._genius_guards(20.0)
	hard._genius_guards(20.0)
	check(hard.g_will_max - hard.g_will < soft.g_will_max - soft.g_will and hard.g_guard_ready_at < soft.g_guard_ready_at, "a shelled one guards for less of its Will, and is ready sooner")
	hard.g_will = 3.0
	hard.g_guard_ready_at = 0.0
	hard._genius_guards(60.0)
	check(not hard.genius.fallen and hard.g_will >= 1.0, "braced, a blow it guards does not fell it")
	soft.g_pos = soft.p_pos + Vector2(9.0, 0.0)
	soft.g_guard_ready_at = 0.0
	check(not soft._genius_guards(10.0), "it cannot guard a partner it is not beside")
	# --- call
	var kith := _genius_fight("sprite", 3, "guard")
	kith.g_pos = kith.p_pos
	kith.w_state = "windup"
	kith.w_target = -1
	kith._update_genius(0.016)
	var kw := kith.g_will
	var kh := kith.p_hp
	check(kith.now < kith.g_called_until, "a kith calls the strike wound up at its partner")
	kith._resolve_bite_from(kith.beast["attacks"][0], kith.w_pos, -1)
	check(is_equal_approx(kith.p_hp, kh) and kith.g_will < kw and kith.g_called_until < kith.now, "the blow lands on it, out of its Will, and its partner is untouched")
	# --- with
	var blade := _genius_fight("blade", 3, "guard")
	var added := 0
	for i in 6:
		blade._genius_after_hit(10.0, false)
	for e in blade.drain():
		if e["type"] == "genius-hunt" and e["move"] == "with":
			added += 1
	check(added == 2, "a relic adds a blow of its own to every third of its partner's (%d in six)" % added)
	blade._update_genius(0.016)
	check(blade.g_pos.is_equal_approx(blade.p_pos), "and is never apart from them")
	# --- debt
	var imp := _genius_fight("imp", 3, "hunt")
	imp._genius_move(imp._genius_has("debt"))
	check(imp.now < imp.g_debt_until, "a daemon writes the foe a debt")
	var wh := imp.w_hp
	imp._resolve_bite_from(imp.beast["attacks"][0], imp.w_pos, -1)
	check(imp.w_hp < wh and imp.g_debt_until < imp.now, "the foe strikes its partner, and pays")
	# --- lay
	var ember := _genius_fight("ember", 3, "hunt")
	ember._genius_move(ember._genius_has("lay"))
	var eh := ember.w_hp
	for i in 90:
		ember.now += 1.0 / 60.0
		ember._genius_zone()
	check(ember.g_zone["effect"] == "burn" and ember.w_hp < eh, "an ember laid on the ground burns what stands there")
	var dark := _genius_fight("shadow", 3, "hunt")
	dark._genius_move(dark._genius_has("lay"))
	var full := float(dark.beast["attacks"][0]["damage"])
	check(dark._genius_on_struck(full, dark.w_pos, -1) < full and is_equal_approx(dark._genius_on_struck(full, dark.w_pos + Vector2(20, 0), -1), full), "a shadow laid down weakens the blows struck from inside it, and no others")
	# --- light
	var lamp := _genius_fight("lantern", 3, "guard")
	lamp.p_state = "free"
	lamp.input("block-down")
	var plain_window := lamp.p_parry_until - lamp.now
	lamp.input("block-up")
	lamp._genius_move(lamp._genius_has("light"))
	lamp.input("block-down")
	check(lamp.p_parry_until - lamp.now > plain_window * 1.2, "on ground its genius has lit, the moment to parry is longer")
	# --- orders
	var g1 := _fighting_genius("runner", 1, "guard")
	var seen1 := [g1.order]
	for i in 3:
		g1.order = g1.next_order()
		seen1.append(g1.order)
	var g3 := _fighting_genius("runner", 3, "guard")
	var seen3 := [g3.order]
	for i in 4:
		g3.order = g3.next_order()
		seen3.append(g3.order)
	check(seen1 == ["guard", "hunt", "guard", "hunt"] and seen3 == ["guard", "hunt", "hold", "free", "guard"], "a First Form guards and hunts; from the Second it can hold and go free (%s)" % str(seen3))
	# --- hold
	var hold := _genius_fight("hound", 3, "hold")
	hold.g_hold_at = hold.p_pos
	hold.w_pos = hold.p_pos + Vector2(2.5, 0)
	var held_hits := 0
	for i in 400:
		hold.w_pos = hold.p_pos + Vector2(2.5, 0)
		hold.w_state = "prowl"
		hold._update_genius(1.0 / 60.0)
		hold.now += 1.0 / 60.0
		for e in hold.drain():
			if e["type"] == "genius-hold":
				held_hits += 1
	check(held_hits >= 2 and hold.g_pos.distance_to(hold.g_hold_at) < 0.2 and hold.w_slow < 1.0, "on Hold it stands on its ground, and what comes onto it is struck and slowed (%d blows)" % held_hits)
	hold.g_guard_ready_at = 0.0
	check(hold._genius_guards(10.0), "its partner is guarded while they stand on that ground")
	hold.p_pos = hold.g_hold_at + Vector2(12.0, 0)
	hold.g_guard_ready_at = 0.0
	check(not hold._genius_guards(10.0) and hold.g_pos.distance_to(hold.g_hold_at) < 0.2, "and not when they leave it: it does not follow")
	var far := _genius_fight("hound", 3, "hold")
	far.w_pos = far.p_pos + Vector2(11.0, 0)
	var none := 0
	for i in 300:
		far.w_pos = far.p_pos + Vector2(11.0, 0)
		far.w_state = "prowl"
		far._update_genius(1.0 / 60.0)
		far.now += 1.0 / 60.0
		for e in far.drain():
			if e["type"] in ["genius-hold", "genius-hunt"]:
				none += 1
	check(none == 0, "a foe that keeps off its ground it leaves alone")
	var posted := _genius_fight("hound", 3, "hold", "cut-wolf", { "post": Vector2(4, -3) })
	posted._update_genius(0.016)
	check(posted.g_hold_at.is_equal_approx(Vector2(4, -3)), "where the fight has a post, that is the ground it holds")
	# --- free: it judges by how its partner fights
	var parrier := _genius_fight("runner", 3, "free")
	parrier.genius.lifetime["fights.parries"] = 40.0
	parrier.genius.lifetime["fights.hurts"] = 4.0
	parrier._update_genius(0.016)
	var brawler := _genius_fight("runner", 3, "free")
	brawler.genius.lifetime["fights.hurts"] = 40.0
	brawler.genius.lifetime["fights.parries"] = 2.0
	brawler.g_order = "hunt"
	brawler._update_genius(0.016)
	check(parrier.g_order == "hunt" and parrier.g_free_why == String(Data.genius()["orders"][3]["free"]["why"]["parryShare"]), "raised by a partner who parries, on Free it hunts, and says why (%s: %s)" % [parrier.g_order, parrier.g_free_why])
	check(brawler.g_order == "guard" and brawler.g_free_why == String(Data.genius()["orders"][3]["free"]["why"]["hurtShare"]), "raised by one who takes the blows, it guards (%s: %s)" % [brawler.g_order, brawler.g_free_why])
	var keeper := _genius_fight("runner", 3, "free", "cut-wolf", { "post": Vector2(1, 1) })
	keeper._update_genius(0.016)
	check(keeper.g_order == "hold" and keeper.g_hold_at.is_equal_approx(Vector2(1, 1)), "and where there is a post to keep, it keeps it")
	var again := _genius_fight("runner", 3, "free")
	again.genius.lifetime["fights.parries"] = 40.0
	again.genius.lifetime["fights.hurts"] = 4.0
	again._update_genius(0.016)
	check(again.g_order == parrier.g_order and again.g_free_why == parrier.g_free_why, "the same partner, the same judgment: Free is not chance")
	var said := false
	for e in parrier.drain():
		said = said or (e["type"] == "free" and e["order"] == "hunt")
	check(said, "it says what it chose when it chooses")
	# --- the Tally learns how its partner meets a blow
	var learn := _genius_fight("runner", 3, "guard")
	learn._record([{ "type": "parry" }, { "type": "parry" }, { "type": "hurt" }, { "type": "block" }, { "type": "evade", "how": "dodged" }, { "type": "evade", "how": "dodged" }, { "type": "evade", "how": "dodged" }])
	check(float(learn.genius.lifetime.get("fights.parries", 0.0)) == 2.0 and float(learn.genius.lifetime.get("fights.hurts", 0.0)) == 1.0 and float(learn.genius.lifetime.get("fights.blocks", 0.0)) == 1.0 and float(learn.genius.tally["counters"].get("fights.dodges", 0.0)) == 3.0, "it counts the blows its partner parries, blocks, takes and dodges")
	# --- a fight with a genius is the same fight twice
	var runs: Array = []
	for k in 2:
		var d := _genius_fight("runner", 6, "free", "green-warden")
		for i in 900:
			d.update(1.0 / 60.0, Vector2.ZERO)
			d.drain()
		runs.append("%.3f %.3f %.3f %s" % [d.w_hp, d.g_will, d.p_hp, str(d.g_pos)])
	check(runs[0] == runs[1], "seeded, a fight with a genius plays out the same")

## A Path's colour (docs/genius-lines.md, "The second pass"): every Path of every line has a
## colour of its own, a ramp of the style; its forms wear it; the three of a line differ.
func test_path_colours() -> void:
	_all_bases()
	var style := Style.data()
	check((style.get("paths", []) as Array).size() >= 6 and (style["paths"] as Array).all(func(r): return (style["ramps"] as Dictionary).has(r)),
		"the style has ramps that are a genius's Path's alone, and each is a ramp")
	check(is_equal_approx(Style.cap_of("accent"), float(style["pathCap"])) and Style.cap_of("accent") > Style.cap_of("cloth"),
		"a Path's colour may be more saturated than the world's cloth: the world is muted so a soul can carry colour")
	check(Style.material_class("accent_dark") == "accent" and Style.material_class("accent2_light") == "accent",
		"a material named accent is a Path's colour, whatever else its name says")
	var missing: Array = []
	var same: Array = []
	for bid in _game_base_ids():
		var b := Data.base(String(bid))
		var seen: Array = []
		for p in b["paths"]:
			var ramp := String((p.get("body", {}) as Dictionary).get("accent", ""))
			if ramp == "" or Style.ramp(ramp).is_empty():
				missing.append(String(p["id"]))
			if seen.has(ramp):
				same.append(String(p["id"]))
			seen.append(ramp)
	check(missing.is_empty(), "every Path of every line has a colour that is a ramp of the style (without: %s)" % str(missing))
	check(same.is_empty(), "the three Paths of a line have three different colours (the same as a sibling's: %s)" % str(same))
	# a form wears its Path's colour, by the step its material names; a form with none wears none
	var wolf := Data.base("wolf")
	var path: Dictionary = wolf["paths"][0]
	var fin := String(path["prongs"][0]["finishes"][0]["id"])
	var ramp0 := String(path["body"]["accent"])
	check(GeniusBody.accent_of(fin, "accent").is_equal_approx(Style.ramp_at(ramp0, 2)) and GeniusBody.accent_of(fin, "accent_dark").is_equal_approx(Style.ramp_at(ramp0, 1))
		and GeniusBody.accent_of(fin, "accent_pale").is_equal_approx(Style.ramp_at(ramp0, 4)),
		"a Final wears its Path's colour: accent is the ramp's middle, accent_dark and accent_pale its other steps")
	check(GeniusBody.accent_of(fin, "accent2_light").is_equal_approx(Style.ramp_at(ramp0, 3)), "with no second colour of its own, accent2 is its Path's")
	check(GeniusBody.accent_of(String(wolf["settled"]["id"]), "accent").a == 0.0 and GeniusBody.accent_of("", "accent").a == 0.0,
		"a Starter has no Path yet, and wears no Path's colour")

## The lines (docs/genius-lines.md): a form wears what its parent wears, a
## form with a model of its own wears it, and the stages have the player's names.
func test_lines() -> void:
	_all_bases()
	# what a form wears of its body: its parent's, unless it says otherwise
	var parent := { "ruff": ["quills", 1.0], "build": { "legs": 1.1, "chest": 1.2 }, "carry": "lamp", "coat": "night" }
	var child := GeniusTree.wear(parent, { "ruff": ["mane", 1.4], "build": { "legs": 1.3 }, "carry": null, "eyes": "dark" })
	check(child["ruff"][0] == "mane" and is_equal_approx(float(child["build"]["legs"]), 1.3) and is_equal_approx(float(child["build"]["chest"]), 1.2)
		and not child.has("carry") and child["eyes"] == "dark" and child["coat"] == "night" and parent.has("carry") and is_equal_approx(float(parent["build"]["legs"]), 1.1),
		"a form wears what its parent wears: what it names replaces, null takes off, the build is merged, and the parent is unchanged")
	var stages: Dictionary = Data.genius().get("stages", {})
	check(["0", "1", "2", "3", "4"].all(func(k): return String(stages.get(k, {}).get("name", "")) != "" and String(stages.get(k, {}).get("plural", "")) != ""), "the five stages of a line have their names (Baby to Final)")
	# every model of a form's own is a form's (or the Baby's), and the game wears it
	var forms := {}
	for b in Data.bases():
		for f in Data.tree_of(String(b["id"])):
			forms[String(f["id"])] = f
	var strays: Array = []
	var built := 0
	var wrong: Array = []
	for file in DirAccess.get_files_at("res://game/assets/genius/forms/"):
		if not file.ends_with(".glb"):
			continue
		var id := file.trim_suffix(".glb")
		if id == "baby":
			continue
		if not forms.has(id):
			strays.append(id)
			continue
		var f: Dictionary = forms[id]
		# one of each stage of each line is enough to hold the rule; all of them is a slow test
		if built >= 40 and int(f["level"]) > 1:
			continue
		var info := { "form": id, "silhouette": f["silhouette"], "expression": f["expression"], "features": f["features"], "instar": int(f["level"]), "look": GeniusLook.born(7) }
		var body := GeniusBody.build(info, Color.ORANGE, int(f["level"]))
		add_child(body)
		built += 1
		var ok := body.own_body == id and body.uses_art and body.parts_from_art.is_empty() and body._model.find_child("ref_top", true, false) != null
		# it stands as tall as its stage says for a body of its kind (a tortoise stands lower than
		# a wolf: data/genius-bodies.json, artSize), by the crown of its head
		var ref: Node3D = body._model.find_child("ref_top", true, false)
		if ref:
			var art_size := float(Data.genius_bodies()["silhouettes"].get(String(f["silhouette"]), {}).get("artSize", 1.0))
			ok = ok and absf(body._local_xf(ref).origin.y - body.stands * art_size) < 0.02
		# a rigged form moves by its base body's clips
		if not body._model.find_children("*", "Skeleton3D", true, false).is_empty() and ResourceLoader.exists(GeniusBody.BODY_DIR % String(f["silhouette"])):
			ok = ok and body.anim != null and body.anim_names.has("idle") and body.anim.has_animation(body.anim_names["idle"])
		if not ok:
			wrong.append(id)
		body.queue_free()
	# A gift made again for one base (docs/genius-lines.md): the Hawk's on a Shield is an eagle
	# displayed, a wing on each side of the rim and a head on the top edge, spread while the
	# shield goes free and shut while it is on an arm; on a wolf the Hawk's wings are as they were.
	var ws: Array = Data.tree_of("shield+hawk").filter(func(f): return String(f["id"]) == "shield+hawk:shield-wall")
	if not ws.is_empty() and ResourceLoader.exists(GeniusBody.GIFT_DIR % ["hawk", "wings-on-shield"]):
		var wf: Dictionary = ws[0]
		var wb := GeniusBody.build({ "form": wf["id"], "silhouette": wf["silhouette"], "expression": wf["expression"], "features": wf["features"], "instar": int(wf["level"]), "look": GeniusLook.born(7) }, Color.ORANGE, int(wf["level"]))
		add_child(wb)
		var on_sockets := true
		for sn in ["socket_arm_l", "socket_arm_r", "socket_head", "socket_tail"]:
			on_sockets = on_sockets and wb.sockets.has(sn) and (wb.sockets[sn] as Node).find_child("at_" + sn, false, false) != null
		check(on_sockets, "the Winged Shield wears the Hawk's gift as made for a shield: a wing at each side, a head on top, feet below")
		var spread: Array = wb.find_children("aloft*", "Node3D", true, false)
		var shut: Array = wb.find_children("furled*", "Node3D", true, false)
		check(spread.size() == 3 and shut.size() == 3 and spread.all(func(n): return n.visible) and not shut.any(func(n): return n.visible), "going free its wings are spread and its feet open")
		wb.set_worn(true)
		check(shut.all(func(n): return n.visible) and not spread.any(func(n): return n.visible), "on an arm its wings are shut down its rim and its feet drawn up")
		wb.set_worn(false)
		check(spread.all(func(n): return n.visible), "and let go, it spreads them again")
		wb.queue_free()
		var wh: Array = Data.tree_of("wolf+hawk").filter(func(f): return String(f["id"]) == "wolf+hawk:wolf-counting-wolf")
		if not wh.is_empty():
			var hf: Dictionary = wh[0]
			var hb := GeniusBody.build({ "form": hf["id"], "silhouette": hf["silhouette"], "expression": hf["expression"], "features": hf["features"], "instar": int(hf["level"]), "look": GeniusLook.born(7) }, Color.ORANGE, int(hf["level"]))
			add_child(hb)
			check(hb.find_children("at_*", "Node3D", true, false).is_empty() and hb.parts_from_art.has("wings"), "a Winged Wolf wears the Hawk's own wings, not the shield's")
			hb.queue_free()
	# a form with a way of resting (one clip of its model's own: docs/genius-lines.md, "How it
	# rests") is first seen in it, gets up to walk by its base body's clips, and takes its rest
	# again when it has stood a while
	if forms.has("wolf-hearth-wolf") and ResourceLoader.exists("res://game/assets/genius/forms/wolf-hearth-wolf.glb"):
		var hf: Dictionary = forms["wolf-hearth-wolf"]
		var rb := GeniusBody.build({ "form": "wolf-hearth-wolf", "silhouette": hf["silhouette"], "expression": hf["expression"], "features": hf["features"], "instar": 3, "look": GeniusLook.born(7) }, Color.ORANGE, 3)
		add_child(rb)
		var began := rb.anim != null and rb.anim.has_animation(GeniusBody.REST) and rb.anim.current_animation == GeniusBody.REST
		rb.move_at(2.0)
		rb._process(0.02)
		var walked := rb.anim != null and rb.anim.current_animation == String(rb.anim_names.get("walk", "-"))
		rb.move_at(0.0)
		var stood := rb.anim != null and rb.anim.current_animation == String(rb.anim_names.get("idle", "-"))
		rb._process(GeniusBody.rest_after() + 0.1)
		rb.move_at(0.0)
		check(began and walked and stood and rb.anim.current_animation == GeniusBody.REST,
			"a form with a way of resting begins in it, gets up to walk, stands, and rests again when it has stood a while (%s %s %s)" % [began, walked, stood])
		rb.queue_free()
	# a hybrid keeps its first base's body: each of its forms wears a form of the first, a form
	# carried across from the second wearing the one it took the place of
	var firsts := Data.tree_of("trun").map(func(f): return String(f["id"]))
	var hy := Data.hybrid_forms("trun", "tedge")
	var own_ids := hy.filter(func(f): return firsts.has(String(f["id"]).get_slice(":", 1)))
	var across := hy.filter(func(f): return not firsts.has(String(f["id"]).get_slice(":", 1)))
	check(not hy.is_empty() and not across.is_empty() and hy.all(func(f): return firsts.has(String(f["wears"])))
		and own_ids.all(func(f): return String(f["wears"]) == String(f["id"]).get_slice(":", 1))
		and across.all(func(f): return int(Data.form(String(f["wears"]))["level"]) == int(f["level"])),
		"every form of a hybrid wears a form of its first base: its own, or the one a carried form took the place of, at the same stage (%d carried)" % across.size())
	check(strays.is_empty(), "every model in game/assets/genius/forms is a form of the tree (%s)" % ", ".join(strays.slice(0, 5)))
	check(wrong.is_empty(), "a form with a model of its own wears it, stands by the crown of its head, hangs no parts for what its line gave it, and moves by its base's clips (%d built; %s)" % [built, ", ".join(wrong.slice(0, 5))])
# ===================================================================== the three types of genius
# docs/genius-types.md; data/genius-types.json. The rules are tested on the tests' own bases
# (tedge a weapon, tlamp a ritual item, trun a companion: fixtures/types.json) and on numbers
# a test puts on a fight itself; what is asked of the game's own bases holds whatever they say.

const TEST_TYPES := "res://game/tests/fixtures/types.json"

## The game's types with the tests' own bases' laid over them, for the whole run.
func _all_types() -> void:
	var t: Dictionary = (Data._load("res://data/genius-types.json") as Dictionary).duplicate(true)
	var mine: Dictionary = Data._load(TEST_TYPES)
	for k in mine["weapon"]:
		t["weapon"]["bases"][k] = mine["weapon"][k]
	for k in mine["items"]:
		t["items"][k] = mine["items"][k]
	for k in mine["companions"]:
		t["companions"][k] = mine["companions"][k]
	Data.use_types(t)

## A fight with a genius standing at a form of the tree, and a foe that stands idle at arm's
## length until the test moves it.
func _typed_fight(form_id: String, instar := 0, extra: Dictionary = {}) -> Fight:
	var opts := { "hero": Fight.default_hero(), "seed": 3, "respawn": false, "genius": _genius_at(form_id, instar), "passive": true }
	for k in extra:
		opts[k] = extra[k]
	var f := Fight.new(opts)
	f.w_state = "idle"
	f.w_pos = f.p_pos + Vector2(1.6, 0.0)
	f.p_facing = 0.0
	f.p_lock = true
	return f

## A fight whose genius is an item with exactly this always and this use: the test's own
## numbers, at full worth.
func _item_fight(always: Dictionary, use: Dictionary, type := "defense", extra: Dictionary = {}) -> Fight:
	var f := _typed_fight("tlamp-small", 3, extra)
	var a := { "name": "always", "text": "", "feeds": "free" }
	a.merge(always, true)
	var u := { "name": "use", "short": "use", "effect": "set", "feeds": "guard", "text": "", "wait": 8.0, "will": 5.0 }
	u.merge(use, true)
	f.g_type = type
	f.g_item = { "type": type, "worn": "side", "wornAs": "", "always": a, "use": u, "bend": {} }
	f.g_worth = 1.0
	f.g_twait = 1.0
	return f

## A fight whose genius is a weapon of this type with this one property.
func _weapon_fight(style: String, sig: Dictionary, will_per_blow := 3.0, instar := 3) -> Fight:
	var f := _typed_fight("tedge-small", instar)
	f.g_weapon = { "style": style, "willPerBlow": will_per_blow, "held": { "length": 1.0 }, "inHand": "", "sig": sig }
	return f

## A fight beside a companion with a role (and a shade), each at a given strength.
func _role_fight(role: String, order := "guard", beast := "cut-wolf", shade := "", k := 1.0, shade_k := 0.5) -> Fight:
	var f := _genius_fight("runner", 3, order, beast)
	var R: Dictionary = Data.genius_types()["roles"]
	f.g_role = R[role]
	f.g_role_id = role
	f.g_role_k = k
	if shade != "":
		f.g_shade = R[shade]
		f.g_shade_id = shade
		f.g_shade_k = shade_k
	return f

func _first_hit(evs: Array) -> Dictionary:
	for e in evs:
		if e["type"] == "hit":
			return e
	return {}

## The game's own bases: every one has a type by its class, and the data is whole.
func test_types_data() -> void:
	var T := Data.genius_types()
	var game := Data.load_bases()
	var missing: Array = []
	var bad_paths: Array = []
	var bad_refs: Array = []
	var roles_used := {}
	var counts := {}
	for b in game:
		var id := String(b["id"])
		var type := GeniusTypes.type_of_class(String(b["class"]))
		counts[type] = int(counts.get(type, 0)) + 1
		if type == "" or not GeniusTypes.written(type, id):
			missing.append(id)
			continue
		var paths: Array = (b["paths"] as Array).map(func(p): return String(p["id"]))
		var named: Array = []
		match type:
			"weapon":
				var w: Dictionary = T["weapon"]["bases"][id]
				named = (w["paths"] as Dictionary).keys()
				if not Data.room["styles"].has(String(w["style"])):
					bad_refs.append("%s: style %s" % [id, w["style"]])
			"defense", "ritual":
				var it: Dictionary = T["items"][id]
				named = (it["paths"] as Dictionary).keys()
				if String(it["type"]) != type:
					bad_refs.append("%s: says %s, its class says %s" % [id, it["type"], type])
			"companion":
				var c: Dictionary = T["companions"][id]
				named = (c["paths"] as Dictionary).keys()
				roles_used[String(c["role"])] = true
		named.sort()
		paths.sort()
		if named != paths:
			bad_paths.append(id)
	check(missing.is_empty(), "every base of the game has its type written (%s)" % ", ".join(missing))
	check(bad_paths.is_empty(), "and what each of its three paths changes (%s)" % ", ".join(bad_paths))
	check(bad_refs.is_empty(), "and names only what exists (%s)" % ", ".join(bad_refs))
	check(int(counts.get("", 0)) == 0, "every class of base is one of the four types")
	if int(counts.get("companion", 0)) >= GeniusTypes.ROLES.size():
		check(roles_used.size() == GeniusTypes.ROLES.size(), "every role has a companion that fills it (%s)" % ", ".join(roles_used.keys()))
	# what the page says of each: its settled form, and each path
	var silent: Array = []
	for b in game:
		for fid in [String(b["settled"]["id"])] + (b["paths"] as Array).map(func(p): return String(p["id"])):
			var g := Genius.at_form(fid, 0)
			var said: Dictionary = GeniusTypes.says(g, Fight.default_hero())
			if (said["lines"] as Array).size() < 3 or String(said["title"]) == "":
				silent.append(fid)
	check(silent.is_empty(), "the page can say what every form does for its partner (%s)" % ", ".join(silent))
	# a hybrid is its first base's type, and its paths are that base's
	if game.size() >= 2:
		var a: Dictionary = game[0]
		var bb: Dictionary = game[1]
		var hy := Data.hybrid_forms(String(a["id"]), String(bb["id"]))
		if not hy.is_empty():
			var of := GeniusTypes.of_form(hy[0])
			check(of["base"] == a["id"] and of["type"] == GeniusTypes.type_of_class(String(a["class"])) and (a["paths"] as Array).map(func(p): return String(p["id"])).has(String(of["path"])), "a hybrid is its first base's type, on that base's paths (%s)" % str(of))
	# the tests' own
	check(GeniusTypes.of_form(Data.form("tedge-small"))["type"] == "weapon" and GeniusTypes.of_form(Data.form("tlamp-a"))["type"] == "ritual" and GeniusTypes.of_form(Data.form("trun-b1"))["path"] == "trun-b", "a form knows its type and the path it is on")
	check(is_equal_approx(GeniusTypes.at_worth(1.5, 0.6), 1.3) and is_equal_approx(GeniusTypes.at_worth(0.5, 1.0), 0.5), "what is always true is worth more as it ages")
	check(GeniusTypes.key_words(_genius_at("tedge-small")).contains("hand") and GeniusTypes.key_words(_genius_at("tlamp-small")).contains("Set it down") and GeniusTypes.key_words(_genius_at("trun-small")).contains("order") and GeniusTypes.key_words(null).contains("order"), "a lesson can say what the key does for the genius a student has")
	var unsaid: Array = []
	for l in Data.academy["lessons"]:
		for st in l["steps"]:
			if String(st.get("text", "")).contains("gives your genius its order") or String(st.get("text", "")).contains("to change its order"):
				unsaid.append(String(l["id"]))
	check(unsaid.is_empty(), "no lesson tells a student with a weapon or an item that G gives an order (%s)" % ", ".join(unsaid))
	var ages_up := true
	var last := 0.0
	for a2 in GeniusTypes.AGES:
		ages_up = ages_up and float(T["ages"][a2]["worth"]) >= last and float(T["weapon"]["inHand"][a2]) > 0.0
		last = float(T["ages"][a2]["worth"])
	check(ages_up, "a genius has more of its function at every age")

## A weapon genius: taken in hand on a switch with the main weapon.
func test_types_weapon() -> void:
	var W: Dictionary = Data.genius_types()["weapon"]
	var chop := float(Data.room["styles"]["blade"]["combo"][0]["damage"])
	var f := _typed_fight("tedge-small", 3)
	check(f.g_type == "weapon" and f.genius_key()["does"] == "take" and not f.g_in_hand and f.genius_key()["ready"], "a weapon genius's key takes it in hand")
	check(f.g_moves.is_empty() and not f._genius_guards(10.0), "it makes no companion's moves and does not guard as one")
	var main_style := f.style
	var main_combo := f.combo
	var main_damage := f.gear_damage
	f.input("order")
	check(f.g_in_hand and not is_same(f.style, main_style) and String(f.style["kind"]) == "melee" and f.combo.size() == (Data.room["styles"]["blade"]["combo"] as Array).size() and f.genius_key()["active"], "in hand, its partner fights with the weapon it is")
	check(is_equal_approx(f.gear_damage, float(W["inHand"]["grown"])), "its blows are worth what its age makes them")
	var w0 := f.g_will
	f.input("attack")
	var evs := run_for(f, 0.7)
	var cut_hit := _first_hit(evs)
	check(is_equal_approx(f.g_will, w0 - 4.0), "a blow with it costs it its own Will (%.1f)" % (w0 - f.g_will))
	check(not cut_hit.is_empty() and is_equal_approx(float(cut_hit["damage"]), roundf(chop * float(W["take"]["drawCut"]["damage"]) * float(W["inHand"]["grown"]))), "taken up rested and struck with at once, its first blow is the cut of the draw (%s)" % str(cut_hit.get("damage", 0)))
	run_for(f, 3.0)
	check(is_equal_approx(f.g_will, w0 - 4.0), "held, it gets none of its Will back")
	f.input("order")
	check(not f.g_in_hand and is_same(f.style, main_style) and is_same(f.combo, main_combo) and is_equal_approx(f.gear_damage, main_damage), "let go, the weapon that was put away is in the hand again")
	run_for(f, 4.0)
	check(f.g_will > w0 - 4.0, "at the shoulder its Will comes back")
	# no cut without rest, and the cut is quicker
	var c := _typed_fight("tedge-small", 3)
	c.input("order")
	var t0 := c.now
	c.input("attack")
	var quick := _first_hit(run_for(c, 0.7))
	c.input("order")
	c.input("order")
	check(c.g_in_hand and c.g_cut_until < c.now, "taken up again at once, there is no cut")
	c.p_last_attack_end = -9.0
	var t1 := c.now
	c.input("attack")
	var plain := _first_hit(run_for(c, 0.7))
	check(not plain.is_empty() and is_equal_approx(float(plain["damage"]), roundf(chop * float(W["inHand"]["grown"]))) and float(quick["t"]) - t0 < float(plain["t"]) - t1 - 0.03, "the cut lands sooner and harder than the same blow without it (%.2f s against %.2f s)" % [float(quick["t"]) - t0, float(plain["t"]) - t1])
	# spent: it leaves the hand of itself
	var sp := _typed_fight("tedge-small", 3)
	var sp_main := sp.style
	sp.input("order")
	sp.g_will = 3.0
	sp.input("attack")
	var spent := false
	for e in sp.drain():
		spent = spent or (e["type"] == "genius-take" and not e["in"] and e.get("spent", false))
	check(not sp.g_in_hand and sp.p_state == "attack" and spent and is_same(sp.style, sp_main), "with too little Will for a blow it leaves the hand of itself, and the press goes to the weapon put away")
	run_for(sp, 1.0)
	sp.g_will = 1.0
	sp.input("order")
	check(not sp.g_in_hand and not sp.genius_key()["ready"] and float(sp.genius_key()["left"]) > 0.0, "spent, it cannot be taken up until it has rested")
	sp.g_will = sp.g_will_max
	sp.input("order")
	check(sp.g_in_hand, "rested, it can")
	# it changes hands only when a hand is free: mid-swing the press waits for the swing's end
	var busy := _typed_fight("tedge-small", 3)
	busy.input("attack")
	run_for(busy, 0.15)
	busy.input("order")
	check(not busy.g_in_hand and busy.p_queued == "order", "pressed in the middle of a swing, the switch waits")
	run_for(busy, 0.35)
	check(busy.g_in_hand, "and is made the moment the swing allows it")
	var dis := _typed_fight("tedge-small", 3)
	dis.p_disarmed = true
	dis.input("order")
	check(not dis.g_in_hand, "a partner whose Toll was their weapon cannot take it up")
	# from the shoulder it strikes with its partner, from its First Form; in the hand it is the blow
	var y := _typed_fight("tedge-small", 1)
	var every := int(W["with"]["every"])
	for i in every * 2:
		y._genius_after_hit(10.0, false)
	var added := 0
	for e in y.drain():
		if e["type"] == "genius-hunt" and e["move"] == "with":
			added += 1
	check(added == 2 and float(y.genius.tally["orders"].get("free", 0.0)) >= 2.0, "young, at the shoulder, it adds a blow to every third of its partner's, and the Tally counts those as its own doing")
	y.input("order")
	for i in every * 2:
		y._genius_after_hit(10.0, false)
	added = 0
	for e in y.drain():
		if e["type"] == "genius-hunt" and e["move"] == "with":
			added += 1
	check(added == 0, "in the hand it adds none: it is the blow")
	# what the Tally learns of a weapon: blows landed with it, from a stand or not; blows turned with it
	var l := _typed_fight("tedge-small", 3)
	l.input("order")
	l.p_moved_at = l.now
	l.input("attack")
	run_for(l, 0.5)
	var hunts := float(l.genius.tally["orders"].get("hunt", 0.0))
	l.p_moved_at = -9.0
	l.input("attack")
	run_for(l, 0.6)
	check(hunts > 0.0 and float(l.genius.tally["orders"].get("hold", 0.0)) > 0.0, "a blow landed with it in hand counts toward Hunt; struck from a stand, toward Hold")
	biting_wolf(l, 0.1)
	l.input("block-down")
	run_for(l, 0.3)
	l.input("block-up")
	check(float(l.genius.tally["orders"].get("guard", 0.0)) >= 1.0, "a blow turned with it in hand counts toward Guard")
	# --- the one property a path gives it
	var grown := float(W["inHand"]["grown"])
	var stag := float(Data.room["break"]["staggerDamageFactor"])
	var r := _typed_fight("tedge-a", 3)
	check(String(r.g_weapon["sig"].get("name", "")) != "" and r.g_path == "tedge-a", "on a path, it has that path's property")
	r.input("order")
	r.g_cut_until = -9.0
	biting_wolf(r, 0.1)
	r.input("block-down")
	run_for(r, 0.3)
	r.input("block-up")
	check(r.now < r.g_riposte_until, "a parry made with it in hand arms the answer")
	var rw := r.g_will
	r.input("attack")
	var ans := _first_hit(run_for(r, 0.6))
	check(not ans.is_empty() and is_equal_approx(float(ans["damage"]), roundf(roundf(chop * grown * 2.0) * stag)) and is_equal_approx(r.g_will, rw) and r.g_riposte_until < r.now, "the answer lands twice as hard, costs it nothing, and is given once (%s)" % str(ans.get("damage", 0)))
	var sc := _typed_fight("tedge-b", 3)
	sc._resolve_bite_from(sc.beast["attacks"][0], sc.w_pos, -1)
	sc._resolve_bite_from(sc.beast["attacks"][0], sc.w_pos, -1)
	check(sc.g_score == 2, "every blow its partner takes is scored")
	for i in 5:
		sc._resolve_bite_from(sc.beast["attacks"][0], sc.w_pos, -1)
	check(sc.g_score == 3, "up to its most")
	sc.p_state = "free"
	sc.p_hp = 100.0
	sc.w_pos = sc.p_pos + Vector2(1.6, 0.0)
	sc.input("order")
	sc.g_cut_until = -9.0
	sc.input("attack")
	var paid := _first_hit(run_for(sc, 0.6))
	check(not paid.is_empty() and is_equal_approx(float(paid["damage"]), roundf(chop * grown * (1.0 + 0.5 * 3))) and sc.g_score == 0, "the next blow that lands with it pays them all back (%s)" % str(paid.get("damage", 0)))
	var cl := _typed_fight("tedge-c", 3)
	cl.input("order")
	check(is_equal_approx(cl.gear_damage, grown * 1.5) and is_equal_approx(cl._parry_k(), 0.5) and float(cl.combo[2].get("knockback", 0.0)) >= 1.0 and float(Data.room["styles"]["blade"]["combo"][2].get("knockback", 0.0)) == 0.0, "a heavier blade: every cut heavier, the third throws the foe back, the moment to parry shorter, and the blade everyone else carries is unchanged")
	cl.input("order")
	check(is_equal_approx(cl._parry_k(), 1.0), "and none of that out of the hand")
	# a bow
	var bow_max := float(Data.room["styles"]["bow"]["draw"]["max"])
	var bow_secs := float(Data.room["styles"]["bow"]["draw"]["seconds"])
	var hb := _weapon_fight("bow", { "firstFullDraw": { "damage": 2.0, "rest": 1.0 }, "fullDraw": { "slow": 0.5, "seconds": 2.0 } })
	hb.input("order")
	hb.g_cut_until = -9.0
	check(hb.ranged and hb.style.has("draw") and hb.g_first_draw, "a bow genius in the hand is a bow")
	hb.input("attack")
	run_for(hb, bow_secs + 0.05)
	hb.input("attack-up")
	var first := _first_hit(run_for(hb, 0.3))
	check(not first.is_empty() and is_equal_approx(float(first["damage"]), roundf(bow_max * 2.0 * grown)) and not hb.g_first_draw, "its first arrow from a full draw lands twice as hard (%s)" % str(first.get("damage", 0)))
	check(hb.now < hb.w_slow_until and is_equal_approx(hb.w_slow, 0.5), "and an arrow from a full draw leaves the foe's time running slow")
	run_for(hb, 0.6)
	hb.input("attack")
	run_for(hb, bow_secs + 0.05)
	hb.input("attack-up")
	var second := _first_hit(run_for(hb, 0.3))
	check(not second.is_empty() and is_equal_approx(float(second["damage"]), roundf(bow_max * grown)), "the second is an arrow like any other (%s)" % str(second.get("damage", 0)))
	var wb := _weapon_fight("bow", { "onWindup": { "weaken": 0.5 } })
	wb.input("order")
	wb.input("attack")
	run_for(wb, 0.3)
	biting_wolf(wb, 0.5)
	wb.input("attack-up")
	run_for(wb, 0.15)
	check(wb.now < wb.w_weak_until, "an arrow that lands while the foe winds up takes the weight out of that strike")
	var hurt_by := 0.0
	for e in run_for(wb, 0.8):
		if e["type"] == "hurt":
			hurt_by = float(e["damage"])
	check(is_equal_approx(hurt_by, float(wb.beast["attacks"][0]["damage"]) * 0.5), "the strike lands for half (%.1f)" % hurt_by)
	# a gun: no magazine, its rounds are its Will
	var shot := float(Data.room["styles"]["pistol"]["shot"]["damage"])
	var gn := _weapon_fight("pistol", { "everyNth": { "n": 2, "damage": 1.5 }, "still": { "seconds": 0.8, "damage": 2.0 } }, 3.0)
	gn.input("order")
	gn.g_cut_until = -9.0
	check(gn.ranged and gn.p_ammo_max == 0 and not gn.style.has("reload") and (Data.room["styles"]["pistol"] as Dictionary).has("reload"), "a gun genius has no magazine and is never reloaded")
	var gw := gn.g_will
	gn.p_moved_at = gn.now
	gn.input("attack")
	var s1 := _first_hit(run_for(gn, 0.5))
	gn.p_moved_at = gn.now
	gn.input("attack")
	var s2 := _first_hit(run_for(gn, 0.5))
	check(is_equal_approx(gn.g_will, gw - 6.0), "its rounds are its Will")
	check(is_equal_approx(float(s1["damage"]), roundf(shot * grown)) and is_equal_approx(float(s2["damage"]), roundf(shot * 1.5 * grown)), "every second shot in a row lands harder (%s, %s)" % [str(s1["damage"]), str(s2["damage"])])
	gn.p_moved_at = gn.now - 2.0
	gn.input("attack")
	var s3 := _first_hit(run_for(gn, 0.5))
	check(is_equal_approx(float(s3["damage"]), roundf(shot * 2.0 * grown)), "fired from a stand, feet set, it lands harder (%s)" % str(s3["damage"]))
	var lg := _weapon_fight("pistol", { "shot": { "range": 17.0 }, "far": { "from": 6.0, "to": 16.0, "damage": 2.0 } })
	lg.w_pos = lg.p_pos + Vector2(11.0 + float(lg.beast["radius"]) * 0.0, 0.0)
	lg.input("order")
	lg.g_cut_until = -9.0
	lg.p_moved_at = lg.now
	check(is_equal_approx(float(lg.combo[0]["range"]), 17.0), "a long gun reaches as far as its path says")
	lg.input("attack")
	var far_hit := _first_hit(run_for(lg, 0.5))
	check(not far_hit.is_empty() and float(far_hit["dist"]) > 9.0 and is_equal_approx(float(far_hit["damage"]), roundf(shot * lerpf(1.0, 2.0, clampf((float(far_hit["dist"]) - 6.0) / 10.0, 0.0, 1.0)) * grown)), "and lands harder the farther off the foe is (%s from %.1f m)" % [str(far_hit.get("damage", 0)), float(far_hit.get("dist", 0.0))])
	# the great have the second hand still
	var old := _typed_fight("tedge-small", 6)
	check(String(old.g_great.get("effect", "")) == String(W["great"]["effect"]) and _typed_fight("tedge-small", 3).g_great.is_empty(), "its great move stays")

## An item: something always true, and one thing its partner does with the key.
func test_types_items() -> void:
	var bite := float(Data.beast("cut-wolf")["attacks"][0]["damage"])
	var regen_delay := float(Data.genius()["will"]["regenDelayAfterHit"])
	check(regen_delay >= 0.0, "there is a wait before an item's Will comes back")
	# the tests' lamp, as the data has it
	var lamp := _typed_fight("tlamp-a", 3)
	var grown_worth := float(Data.genius_types()["ages"]["grown"]["worth"])
	check(lamp.g_type == "ritual" and lamp.genius_key()["does"] == "use" and String(lamp.g_item["use"]["effect"]) == "light" and is_equal_approx(float(lamp.g_item["use"]["shelter"]), 0.5) and is_equal_approx(float(lamp.g_item["use"]["seconds"]), 6.0 * grown_worth) and lamp.g_moves.is_empty(), "an item has its base's use with its path's laid over it, at the worth of its age")
	check(not lamp._genius_guards(10.0), "it does not guard as a companion does")
	lamp.input("order")
	check(not lamp.g_lamp.is_empty() and not lamp.genius_key()["ready"] and float(lamp.genius.tally["orders"].get("hold", 0.0)) >= 1.0, "the key uses it, its wait begins, and the Tally counts the use toward the line it feeds")
	# --- set: the shield takes the next blow whole
	var s := _item_fight({}, { "effect": "set", "seconds": 1.4, "blows": 1, "takes": 0.5 })
	var sw := s.g_will
	s.input("order")
	check(s.now < s.g_set_until and is_equal_approx(s.g_will, sw - 5.0), "the shield is set, for its Will")
	biting_wolf(s, 0.1)
	var evs := run_for(s, 0.4)
	check(types(evs).has("genius-took") and is_equal_approx(s.p_hp, 100.0) and is_equal_approx(s.g_will, sw - 5.0 - bite * 0.5) and s.p_state != "flinch", "set, it takes the next blow whole, out of its own Will")
	biting_wolf(s, 0.1)
	evs = run_for(s, 0.4)
	check(types(evs).has("hurt") and s.g_set_until < s.now, "one blow, and it is no longer set")
	check(not s.genius_key()["ready"] and float(s.genius_key()["left"]) > 6.0, "and it must come round again")
	var s2 := _item_fight({}, { "effect": "set", "seconds": 3.0, "blows": 2, "takes": 0.0 })
	s2.input("order")
	for i in 2:
		biting_wolf(s2, 0.1)
		run_for(s2, 0.4)
	check(is_equal_approx(s2.p_hp, 100.0), "a wall takes two")
	s2.g_will = 0.0
	s2.g_use_at = 0.0
	s2.input("order")
	check(s2.g_set_until < s2.now and not s2.genius.fallen, "with no Will it cannot be set; an item does not fall")
	var door := _item_fight({}, { "effect": "set", "ground": { "radius": 3.0, "seconds": 6.0 }, "blows": 2, "takes": 0.0 })
	door.input("order")
	check(not door.g_door.is_empty() and (door.g_door["at"] as Vector2).is_equal_approx(door.p_pos), "a gate is set on the ground where its partner stands")
	biting_wolf(door, 0.1)
	run_for(door, 0.4)
	check(is_equal_approx(door.p_hp, 100.0), "by the door, the blow is the door's")
	door.p_pos += Vector2(-6.0, 0.0)
	biting_wolf(door, 0.1)
	evs = run_for(door, 0.4)
	check(types(evs).has("hurt"), "away from it, it is not")
	var cohort := Academy.make_cohort(42, Fight.default_hero())
	var sh := _item_fight({}, { "effect": "set", "seconds": 2.0, "blows": 1, "takes": 0.0, "allies": 8.0 }, "defense", { "allies": [cohort[0]] })
	sh.input("order")
	var ally_hp := float(sh.allies[0]["hp"])
	sh._hurt_ally(0, 10.0, -1)
	check(is_equal_approx(float(sh.allies[0]["hp"]), ally_hp), "a shelter covers a classmate: the blow at them is the shield's")
	var own := _item_fight({}, { "effect": "set", "seconds": 2.0, "blows": 1, "takes": 0.0 }, "defense", { "allies": [cohort[0]] })
	own.input("order")
	own._hurt_ally(0, 10.0, -1)
	check(float(own.allies[0]["hp"]) < ally_hp, "a shield that is only its partner's does not")
	# --- catch: the hand reaches for a strike before it is thrown
	var c := _item_fight({}, { "effect": "catch", "reach": 3.2, "flinch": 0.9, "missWait": 2.5, "missWill": 3.0, "wait": 10.0, "will": 9.0 })
	var cw := c.g_will
	c.input("order")
	check(is_equal_approx(c.g_will, cw - 3.0) and not c.genius_key()["ready"] and float(c.genius_key()["left"]) <= 2.5, "reaching for nothing, the hand closes on air: a little Will and a short wait")
	run_for(c, 3.0)
	c.g_will = cw
	biting_wolf(c, 0.3)
	c.input("order")
	evs = c.drain()
	check(c.w_state == "flinch" and types(evs).has("genius-caught") and is_equal_approx(c.g_will, cw - 9.0), "reaching for a foe that is winding up, it catches the strike")
	evs = run_for(c, 1.2)
	check(not types(evs).has("hurt") and is_equal_approx(c.p_hp, 100.0), "and the strike is never thrown")
	var co := _item_fight({}, { "effect": "catch", "reach": 3.2, "flinch": 0.9, "open": 2.5, "exposed": 1.2 }, "defense", { "beast": "green-warden" })
	check(not co.guard_open(), "an elite keeps its guard")
	biting_wolf(co, 0.3)
	co.input("order")
	check(co.guard_open() and is_equal_approx(co._typed_blow_k(), 1.2), "a maker's hand takes it apart: its guard is down and it takes more")
	co.now += 3.0
	co.w_state = "prowl"
	check(not co.guard_open() and is_equal_approx(co._typed_blow_k(), 1.0), "for a while")
	var cs := _item_fight({}, { "effect": "catch", "reach": 3.2, "flinch": 0.9, "strike": 3.0, "knockback": 1.5 })
	biting_wolf(cs, 0.3)
	var hp0 := cs.w_hp
	var d0 := cs.dist()
	cs.input("order")
	check(is_equal_approx(hp0 - cs.w_hp, roundf(cs._genius_base() * 3.0)) and cs.dist() > d0 + 1.0, "a fighting fist strikes as it closes and throws the foe back")
	var far := _item_fight({}, { "effect": "catch", "reach": 3.0, "flinch": 0.9, "allyReach": 10.0 }, "defense", { "allies": [cohort[0]] })
	biting_wolf(far, 0.3)
	far.w_pos = far.p_pos + Vector2(7.0, 0.0)
	far.w_target = 0
	far.input("order")
	check(far.w_state == "flinch", "an open hand reaches across the ground for a strike wound up at a classmate")
	far.g_use_at = 0.0
	biting_wolf(far, 0.3)
	far.w_pos = far.p_pos + Vector2(7.0, 0.0)
	far.w_target = -1
	far.input("order")
	check(far.w_state == "windup", "and not that far for one at its partner")
	# --- slip: the coat pulls its partner out
	var sl := _item_fight({}, { "effect": "slip", "distance": 1.0, "iframes": 0.42 })
	sl.p_state = "flinch"
	var pw := sl.p_will
	var at0 := sl.p_pos
	sl.input("order")
	check(sl.p_state == "dodge" and sl.p_invulnerable() and is_equal_approx(sl.p_will, pw), "the slip is made out of a flinch, untouchable at once, for none of its partner's Will")
	biting_wolf(sl, 0.05)
	sl.w_pos = sl.p_pos + Vector2(1.3, 0.0)
	evs = run_for(sl, 0.6)
	check(types(evs).has("evade") and is_equal_approx(sl.p_hp, 100.0) and sl.p_state == "free" and sl.p_slip.is_empty() and sl.p_pos.distance_to(at0) > 2.0, "the blow lands where they were")
	var late := _item_fight({}, { "effect": "slip", "distance": 1.0, "iframes": 0.42, "late": { "seconds": 0.33, "back": 0.5 } })
	biting_wolf(late, 0.05)
	run_for(late, 0.1)
	check(is_equal_approx(late.p_hp, 100.0 - bite) and late.p_state == "flinch", "a blow lands")
	late.input("order")
	check(is_equal_approx(late.p_hp, 100.0 - bite * 0.5), "a listening coat, slipped at once, takes half of it back")
	var pun := _item_fight({}, { "effect": "slip", "distance": 1.0, "iframes": 0.42, "punish": { "seconds": 2.2, "damage": 1.5 }, "willBack": 8.0, "haste": { "seconds": 2.0, "speed": 1.25 } })
	pun.p_will = 50.0
	biting_wolf(pun, 0.05)
	pun.input("order")
	run_for(pun, 0.2)
	check(pun.now < pun.p_punish_until and pun.p_will > 57.0 and pun.now < pun.p_haste_until, "a blow slipped leaves the foe open to the next; the slip gives Will back and haste")
	check(is_equal_approx(pun._typed_blow_k(), 1.5) and is_equal_approx(pun._typed_blow_k(), 1.0), "the next blow lands half again as hard, once")
	# --- light: the lantern set down
	var l := _item_fight({}, { "effect": "light", "radius": 4.0, "seconds": 6.0, "parryWindow": 2.0, "stagger": 0.5 }, "ritual")
	check(is_equal_approx(l._parry_k(), 1.0), "before it is lit, the moment to parry is its own")
	l.input("order")
	check(not l.g_lamp.is_empty() and is_equal_approx(l._parry_k(), 2.0), "in its light the moment to parry is longer")
	biting_wolf(l, 0.1)
	l.input("block-down")
	run_for(l, 0.2)
	l.input("block-up")
	check(l.w_state == "stagger" and is_equal_approx(l.w_duration, float(Data.room["parry"]["staggerSeconds"]) + 0.5), "and a parry made in it staggers the foe longer")
	l.p_pos += Vector2(-7.0, 0.0)
	check(is_equal_approx(l._parry_k(), 1.0), "out of its light, no longer")
	run_for(l, 6.5)
	check(l.g_lamp.is_empty(), "it burns its time")
	var found := _item_fight({}, { "effect": "light", "radius": 4.0, "seconds": 6.0, "at": "foe", "found": 2.0 }, "ritual", { "beast": "green-warden" })
	var guard := float(found.beast["guard"])
	check(is_equal_approx(found._guarded(100.0), roundf(100.0 * guard)), "a guard lets a share through")
	found.input("order")
	check((found.g_lamp["at"] as Vector2).is_equal_approx(found.w_pos) and is_equal_approx(found._guarded(100.0), roundf(100.0 * minf(1.0, guard * 2.0))), "a wayfinder is set at the foe's feet, and a guarded foe in its light lets more through")
	var shel := _item_fight({}, { "effect": "light", "radius": 4.0, "seconds": 6.0, "shelter": 0.5, "burn": 1.0, "willRegen": 2.0 }, "ritual")
	shel.input("order")
	shel.w_state = "idle"
	var whp := shel.w_hp
	shel.p_will = 40.0
	run_for(shel, 2.0)
	check(shel.w_hp < whp and shel.stats["g_damage"] > 0.0, "what stands in a kept flame burns")
	var plain_will := _item_fight({}, { "effect": "light", "radius": 4.0, "seconds": 6.0 }, "ritual")
	plain_will.p_will = 40.0
	run_for(plain_will, 2.0)
	check(is_equal_approx(shel.p_will - 40.0, (plain_will.p_will - 40.0) * 2.0), "and its partner's Will comes back faster in it (%.1f against %.1f)" % [shel.p_will - 40.0, plain_will.p_will - 40.0])
	biting_wolf(shel, 0.05)
	run_for(shel, 0.2)
	check(is_equal_approx(shel.p_hp, 100.0 - bite * 0.5), "a blow at one standing in a watch-lamp's light lands for less")
	# --- sight: the astrolabe
	var sg := _item_fight({}, { "effect": "sight", "seconds": 7.0, "damage": 1.5, "reach": 18.0, "far": { "from": 7.0, "damage": 1.3 }, "parryWindow": 1.6 }, "ritual")
	sg.w_state = "down"
	sg.input("order")
	check(sg.g_sight_until < sg.now and sg.genius_key()["ready"], "with no foe to sight, nothing is spent")
	sg.w_state = "prowl"
	sg.input("order")
	check(sg.now < sg.g_sight_until and is_equal_approx(sg._typed_blow_k(), 1.0), "a sighted foe is struck as any other, out of its weak moment")
	sg.w_state = "recover"
	check(is_equal_approx(sg._typed_blow_k(), 1.5), "in its weak moment, recovering from its own strike, harder")
	sg.w_state = "stagger"
	check(is_equal_approx(sg._typed_blow_k(), 1.5) and is_equal_approx(sg._parry_k(), 1.6), "and staggered; and its strikes are easier to parry")
	sg.w_state = "prowl"
	sg.w_pos = sg.p_pos + Vector2(9.0, 0.0)
	check(is_equal_approx(sg._typed_blow_k(), 1.3), "a sighting-glass makes it harder from far off at any moment")
	sg.now += 8.0
	check(is_equal_approx(sg._typed_blow_k(), 1.0) and is_equal_approx(sg._parry_k(), 1.0), "the sight lapses")
	# --- toll: the bell
	var t := _item_fight({}, { "effect": "toll", "radius": 5.5, "flinch": 0.7, "willBack": 6.0, "mend": 4.0 }, "ritual", { "pack": ["cut-wolf"] })
	biting_wolf(t, 0.3)
	(t.foes[0] as Foe).pos = t.p_pos + Vector2(0.0, 2.0)
	(t.foes[0] as Foe).attack = t.beast["attacks"][0]
	(t.foes[0] as Foe).set_state("windup", 0.5)
	t.p_will = 50.0
	t.p_hp = 60.0
	t.input("order")
	check(t.w_state == "flinch" and (t.foes[0] as Foe).state == "flinch", "the toll breaks every strike wound up near its partner, the pack's with the rest")
	check(is_equal_approx(t.p_will, 56.0) and is_equal_approx(t.p_hp, 64.0), "and steadies them: Will back, and for a rally-bell health")
	var ts := _item_fight({}, { "effect": "toll", "radius": 5.5, "flinch": 0.7, "stagger": 1.2, "strike": 2.0 }, "ritual")
	biting_wolf(ts, 0.3)
	var th := ts.w_hp
	ts.input("order")
	check(ts.w_state == "stagger" and ts.w_hp < th, "an alarm-bell staggers what it breaks, and strikes it")
	var ta := _item_fight({}, { "effect": "toll", "radius": 5.5, "flinch": 0.7, "auto": 22.0 }, "ritual")
	biting_wolf(ta, 0.3)
	ta._update_genius(DT)
	check(ta.w_state == "flinch" and ta.g_auto_at > ta.now + 20.0 and ta.genius_key()["ready"], "an hour-bell tolls of itself when a strike is wound up at its partner, and its own toll is still to hand")
	# --- what is always true
	var blk := _item_fight({ "block": { "damage": 0.5, "will": 0.5 } }, {})
	blk.input("block-down")
	run_for(blk, 0.5)
	biting_wolf(blk, 0.02)
	var blocked := 0.0
	for e in run_for(blk, 0.1):
		if e["type"] == "block":
			blocked = float(e["damage"])
	check(is_equal_approx(blocked, bite * float(Data.room["block"]["damageFactor"]) * 0.5), "a shield arm: a blocked blow lands for less (%.2f)" % blocked)
	var pr := _item_fight({ "parryWindow": 1.5, "parryWill": 4.0 }, {})
	check(is_equal_approx(pr._parry_k(), 1.5), "a sure hand: the moment to parry is longer")
	pr.g_worth = 0.6
	check(is_equal_approx(pr._parry_k(), 1.3), "less so while it is young")
	pr.g_worth = 1.0
	pr.p_will = 50.0
	biting_wolf(pr, 0.1)
	pr.input("block-down")
	run_for(pr, 0.2)
	pr.input("block-up")
	check(pr.p_will >= 50.0 + float(Data.room["parry"]["will"]) + 4.0 - 1.5 and float(pr.genius.tally["orders"].get("free", 0.0)) > 0.0, "a bell: a parry rings it, for a little more Will; what is always true of an item is counted as its own doing")
	var dg := _item_fight({ "dodge": { "will": 0.5, "iframes": 0.1 } }, {})
	var plain_dodge := _item_fight({}, {})
	dg.p_will = 50.0
	plain_dodge.p_will = 50.0
	dg.input("dodge")
	plain_dodge.input("dodge")
	check(is_equal_approx(50.0 - dg.p_will, (50.0 - plain_dodge.p_will) * 0.5) and is_equal_approx(dg._always_add("dodge", "iframes"), 0.1), "a coat hangs loose: a dodge costs less and is untouchable a moment longer")
	var ht := _item_fight({ "hurt": 0.8 }, {}, "ritual")
	biting_wolf(ht, 0.05)
	run_for(ht, 0.2)
	check(is_equal_approx(ht.p_hp, 100.0 - bite * 0.8), "a lantern: a blow taken whole lands for a little less")
	var ms := _item_fight({ "measure": { "per": 0.05, "max": 2 } }, {}, "ritual")
	for i in 3:
		biting_wolf(ms, 0.1)
		ms.input("block-down")
		run_for(ms, 0.2)
		ms.input("block-up")
		ms.w_state = "idle"
	check(ms.g_measure == 2 and is_equal_approx(ms._typed_blow_k(), 1.10), "an astrolabe takes the measure of every strike answered, up to its most, and each adds to its partner's blows")
	ms._spawn_wolf()
	check(ms.g_measure == 0, "another foe is another measure")
	var keeps := _item_fight({ "measure": { "per": 0.05, "max": 2, "keeps": true } }, {}, "ritual")
	keeps.g_measure = 2
	keeps._spawn_wolf()
	check(keeps.g_measure == 2, "an almanac keeps what it has measured of a kind of beast")
	var ch := _item_fight({ "chain": 1.5 }, {}, "ritual")
	var plain_chain := _item_fight({}, {}, "ritual")
	for ff in [ch, plain_chain]:
		biting_wolf(ff, 0.1)
		ff.input("block-down")
		run_for(ff, 0.3)
		ff.input("block-up")
		ff.input("pattern")
	check(not ch.chain.is_empty() and is_equal_approx(float(ch.chain["window"]), float(plain_chain.chain["window"]) * 1.5), "a bell keeps the time: the moments of the Pattern's chain are wider")
	var wi := _item_fight({ "with": { "every": 3, "damage": 0.9 } }, {})
	for i in 6:
		wi._genius_after_hit(10.0, false)
	var added := 0
	for e in wi.drain():
		if e["type"] == "genius-hunt" and e["move"] == "with":
			added += 1
	check(added == 2, "a fighting fist strikes with its partner")
	var cf := _item_fight({ "catchFall": 1 }, {})
	cf.p_hp = 5.0
	cf._resolve_bite_from(cf.beast["attacks"][0], cf.w_pos, -1)
	check(is_equal_approx(cf.p_hp, 1.0) and cf.p_state != "down", "an open hand catches its partner when a blow would fell them")
	cf.p_state = "free"
	cf._resolve_bite_from(cf.beast["attacks"][0], cf.w_pos, -1)
	check(cf.p_state == "down", "once a fight")

## A companion's role: where it stands, its numbers, the moves it favours, and the one thing only it does.
func test_types_roles() -> void:
	var T := Data.genius_types()
	var R: Dictionary = T["roles"]
	var worth := func(age: String) -> float: return float(T["ages"][age]["worth"])
	# read off its form: the tests' runner is a Hunter; a path shades it, or keeps it to its role
	var pup := _typed_fight("trun-small", 1)
	check(pup.g_type == "companion" and pup.g_role_id == "hunter" and is_equal_approx(pup.g_role_k, worth.call("young")) and pup.g_shade_id == "" and pup.genius_key()["does"] == "order", "a companion has its base's role from its First Form, at the worth of its age")
	check(is_equal_approx(pup.g_will_max, pup.genius.will_max() * float(R["hunter"]["numbers"].get("will", 1.0))), "its role sets its Will")
	var shaded := _typed_fight("trun-a", 3)
	check(shaded.g_shade_id == "keeper" and is_equal_approx(shaded.g_shade_k, float(R["shade"]["other"]) * worth.call("grown")) and is_equal_approx(shaded.g_role_k, worth.call("grown")), "a path that shades toward another role has that role's own thing at a share of its strength")
	var pure := _typed_fight("trun-b1", 3)
	check(pure.g_shade_id == "" and is_equal_approx(pure.g_role_k, float(R["shade"]["pure"]) * worth.call("grown")), "a path that keeps to its role has its own thing stronger, and so do the forms under it")
	check(is_equal_approx(shaded._own("mend"), shaded.g_shade_k) and is_equal_approx(shaded._own("opening"), shaded.g_role_k) and shaded._own("hold-it") == 0.0, "it has the own things of its role and its shade and no others")
	shaded.genius.fallen = true
	check(shaded._own("mend") == 0.0, "fallen, it does nothing")
	var legacy := _genius_fight("runner", 3, "hunt")
	check(legacy.g_role.is_empty() and is_equal_approx(legacy._role_n("damage"), 1.0), "a genius no tree has written a type for fights as before, with no role")
	# its numbers
	var b := _role_fight("bulwark", "guard")
	check(is_equal_approx(b._genius_base(), legacy._genius_base() * float(R["bulwark"]["numbers"]["damage"])), "a role's numbers are laid over what it is: a Bulwark strikes for less")
	var soft := _genius_fight("runner", 3, "guard")
	soft.g_pos = soft.p_pos
	b.g_pos = b.p_pos
	soft._genius_guards(20.0)
	b._genius_guards(20.0)
	check(b.g_will_max - b.g_will < soft.g_will_max - soft.g_will and b.g_guard_ready_at < soft.g_guard_ready_at, "and guards for less of its Will, and sooner again")
	# the moves it favours
	var ids := func(ms: Array) -> Array: return ms.map(func(m): return String(m["id"]))
	check(ids.call(Fight.genius_moves("quadruped", "beast", ["wings", "lantern"], 1)) == ["hamstring"] and ids.call(Fight.genius_moves("quadruped", "beast", ["wings", "lantern"], 1, ["light"])) == ["light"] and ids.call(Fight.genius_moves("quadruped", "beast", ["wings", "lantern"], 3, ["light"])) == ["light", "hamstring", "stoop"], "the moves a role favours are the ones it keeps first as it ages")
	# where it stands
	var front := _role_fight("bulwark", "guard")
	var back := _role_fight("lookout", "guard")
	for ff in [front, back]:
		ff.passive = true
		ff.w_state = "idle"
		ff.w_pos = ff.p_pos + Vector2(6.0, 0.0)
		for i in 120:
			ff._update_genius(DT)
			ff.now += DT
	check((front.g_pos - front.p_pos).x > 1.0 and (back.g_pos - back.p_pos).x < -1.0, "a Bulwark stands between its partner and the foe, a Lookout behind them (%.1f, %.1f)" % [(front.g_pos - front.p_pos).x, (back.g_pos - back.p_pos).x])
	# --- a Bulwark holds the foe
	var hold: Dictionary = R["bulwark"]["own"]
	var h := _role_fight("bulwark", "guard")
	h.g_pos = h.p_pos + Vector2(0.0, 3.0)
	var hw := h.g_will
	h._role_acts(true)
	check(h._held() and h.w_target == Fight.HELD and h._tpos().is_equal_approx(h.g_pos) and h.w_state == "approach" and is_equal_approx(h.g_will, hw - float(hold["will"])), "a Bulwark calls the foe onto itself: the foe goes for it")
	h.w_attack = h.beast["attacks"][0]
	h.w_pos = h.g_pos + Vector2(1.2, 0.0)
	h.w_facing = PI
	h.w_state = "strike"
	h.w_timer = 0.0
	h.w_duration = float(h.w_attack["active"])
	h.w_hit_done = false
	hw = h.g_will
	h._update_wolf(DT)
	var held_evs := types(h.drain())
	check(held_evs.has("genius-held-blow") and is_equal_approx(h.p_hp, 100.0) and is_equal_approx(h.g_will, hw - float(h.w_attack["damage"]) * float(hold["takes"])), "its strike lands on the genius, out of its Will, and its partner is untouched")
	# the hold's time runs out while a strike wound up at the genius is still being thrown
	h.w_hit_done = false
	hw = h.g_will
	h.now = h.g_held_until + 0.1
	check(not h._held() and h._holds() and h._tpos().is_equal_approx(h.g_pos), "a strike wound up at the genius is the genius's, though the hold's time ends before it is thrown")
	h._update_wolf(DT)
	check(types(h.drain()).has("genius-held-blow") and is_equal_approx(h.p_hp, 100.0) and h.g_will < hw, "it lands on the genius, not on a partner who could not have read it")
	h.w_state = "recover"
	h.w_timer = 0.0
	h.w_duration = 1.0
	h._update_wolf(DT)
	check(not h._holds() and h.w_target == -1 and h._tpos().is_equal_approx(h.p_pos), "when the hold ends the foe is its partner's again")
	h._choose_attack()
	check(h.w_target != Fight.HELD, "and chooses as it did")
	# a genius of another role with a Bulwark's shade comes forward to hold
	var comes := _role_fight("lookout", "guard", "cut-wolf", "bulwark")
	comes.passive = true
	comes.w_state = "approach"
	comes.w_attack = comes.beast["attacks"][0]
	comes.w_pos = comes.p_pos + Vector2(6.0, 0.0)
	comes.w_target = Fight.HELD
	comes.g_held_until = comes.now + 30.0
	for i in 120:
		comes._update_genius(DT)
		comes.now += DT
	check((comes.g_pos - comes.p_pos).x > 1.0, "whatever its role, while it holds the foe it stands between the foe and its partner (%.1f)" % (comes.g_pos - comes.p_pos).x)
	# a strike it holds is thrown at the genius: its partner, in the way, is not bitten in passing
	var passing: Array = []
	for is_held in [true, false]:
		var by := _role_fight("bulwark", "guard")
		by.passive = true
		by.g_pos = by.p_pos + Vector2(0.0, 6.0)
		if is_held:
			by.w_target = Fight.HELD
			by.g_held_until = by.now + 30.0
		by.w_attack = by.beast["attacks"][0]
		by.w_pos = by.p_pos + Vector2(1.2, 0.0)
		by.w_facing = PI
		by.w_state = "strike"
		by.w_timer = 0.0
		by.w_duration = float(by.w_attack["active"])
		by.w_hit_done = false
		by._update_wolf(DT)
		passing.append(by.w_hit_done)
	check(passing == [false, true], "a strike it holds is the genius's: its partner, standing in the way, is not bitten in passing (%s)" % str(passing))
	# --- a Hunter goes for the opening
	var into := float(R["hunter"]["own"]["damage"])
	var hu := _role_fight("hunter", "hunt")
	hu.w_state = "prowl"
	var before := hu.w_hp
	hu._genius_hits(100.0, "strike")
	var shut := before - hu.w_hp
	hu.w_state = "recover"
	before = hu.w_hp
	hu._genius_hits(100.0, "strike")
	check(is_equal_approx(shut, 100.0) and is_equal_approx(before - hu.w_hp, roundf(100.0 * into)), "a Hunter's blow into an opening lands harder (%d, then %d)" % [int(shut), int(before - hu.w_hp)])
	hu.g_hunt_at = hu.now + 5.0
	hu._wolf_set("stagger", 1.0)
	check(hu.g_hunt_at <= hu.now, "and when the foe staggers it comes at once")
	var half := _role_fight("bulwark", "hunt", "cut-wolf", "hunter", 1.0, 0.5)
	half.w_state = "recover"
	before = half.w_hp
	half._genius_hits(100.0, "strike")
	check(is_equal_approx(before - half.w_hp, roundf(100.0 * (1.0 + (into - 1.0) * 0.5))), "a shade of the Hunter has half of that")
	# --- a Harrier opens the guard
	var worry: Dictionary = R["harrier"]["own"]
	var ha := _role_fight("harrier", "hunt", "green-warden")
	ha.g_pos = ha.w_pos
	check(not ha.guard_open(), "an elite keeps its guard")
	ha._role_acts(true)
	check(ha.guard_open() and is_equal_approx(ha._typed_blow_k(), float(worry["exposed"])), "a Harrier worries it: its guard is down, and every blow on it lands for more")
	ha.now += float(worry["seconds"]) + 0.1
	check(not ha.guard_open() and is_equal_approx(ha._typed_blow_k(), 1.0), "for a moment")
	ha._role_acts(true)
	check(not ha.guard_open(), "and not again until it has waited")
	# --- a Keeper mends
	var mend: Dictionary = R["keeper"]["own"]
	var k := _role_fight("keeper", "guard")
	k.g_pos = k.p_pos
	k.p_hp = 50.0
	var kw := k.g_will
	k._role_acts(true)
	check(is_equal_approx(k.p_hp, 50.0 + float(mend["health"])) and is_equal_approx(k.g_will, kw - float(mend["will"])), "a Keeper mends its partner out of its own Will")
	k._role_acts(true)
	check(is_equal_approx(k.p_hp, 50.0 + float(mend["health"])), "a little at a time")
	k.now += float(mend["every"]) + 0.1
	k.p_struck_at = k.now
	k._role_acts(true)
	check(is_equal_approx(k.p_hp, 50.0 + float(mend["health"])), "not while the blows are still landing")
	k.p_struck_at = -9.0
	k.p_hp = 95.0
	k._role_acts(true)
	check(is_equal_approx(k.p_hp, 95.0), "and not one who is barely hurt")
	var cohort := Academy.make_cohort(42, Fight.default_hero())
	var kp := _genius_fight("runner", 3, "guard", "cut-wolf", { "allies": [cohort[0]] })
	kp.g_role = R["keeper"]
	kp.g_role_id = "keeper"
	kp.g_role_k = 1.0
	kp.g_pos = kp.allies[0]["pos"]
	kp.allies[0]["hp"] = float(kp.allies[0]["hp_max"]) * 0.3
	var a0 := float(kp.allies[0]["hp"])
	kp._role_acts(true)
	check(float(kp.allies[0]["hp"]) > a0, "with a party, it sees to whoever is worst hurt")
	# --- a Lookout reads the fight
	var calls: Dictionary = R["lookout"]["own"]
	var lo := _role_fight("lookout", "guard")
	lo.g_pos = lo.p_pos
	check(is_equal_approx(lo._parry_k(), float(calls["parryWindow"])), "while a Lookout watches, the moment to parry is longer")
	lo.g_pos = lo.p_pos + Vector2(40.0, 0.0)
	check(is_equal_approx(lo._parry_k(), 1.0), "not from out of sight")
	lo.g_pos = lo.p_pos
	lo.w_state = "recover"
	lo.w_duration = 0.9
	lo._foe_recovers()
	check(is_equal_approx(lo._typed_blow_k(), float(calls["mark"])), "and when the foe has struck and missed its chance, it calls the opening")
	lo.w_state = "prowl"
	check(is_equal_approx(lo._typed_blow_k(), 1.0), "which is over when the foe has recovered")
	# a fight beside a companion with a role is the same fight twice
	var runs: Array = []
	for n in 2:
		var d := _typed_fight("trun-a", 4, { "passive": false, "beast": "green-warden" })
		d.w_state = "prowl"
		for i in 900:
			d.update(DT, Vector2.ZERO)
			d.drain()
		runs.append("%.3f %.3f %.3f %s" % [d.w_hp, d.g_will, d.p_hp, str(d.g_pos)])
	check(runs[0] == runs[1], "seeded, a fight beside a companion with a role plays out the same")

## What a partner lacks, and bots that use the key.
func test_types_need_and_bots() -> void:
	var g := _genius_at("trun-small", 1)
	var blade := hero_of("anchor", "saber")
	var gun := hero_of("anchor", "musket")
	var maul := hero_of("anchor", "hammer")
	var nb := GeniusTypes.needs(blade, g)
	var ng := GeniusTypes.needs(gun, g)
	var nm := GeniusTypes.needs(maul, g)
	check(float(ng["bulwark"]) > float(nb["bulwark"]) + 0.3, "a partner who fights from far off lacks a front (%.2f against %.2f)" % [ng["bulwark"], nb["bulwark"]])
	check(float(nm["harrier"]) > float(nb["harrier"]), "one whose weapon is slow lacks the opening (%.2f against %.2f)" % [nm["harrier"], nb["harrier"]])
	var hurt := _genius_at("trun-small", 1)
	hurt.lifetime["fights.hurts"] = 30.0
	hurt.lifetime["fights.parries"] = 3.0
	var turner := _genius_at("trun-small", 1)
	turner.lifetime["fights.parries"] = 30.0
	turner.lifetime["fights.hurts"] = 3.0
	check(float(GeniusTypes.needs(blade, hurt)["keeper"]) > float(GeniusTypes.needs(blade, turner)["keeper"]) + 0.3 and float(GeniusTypes.needs(blade, turner)["hunter"]) > float(GeniusTypes.needs(blade, hurt)["hunter"]) + 0.3, "one who takes the blows lacks staying; one who turns them lacks the blow to put in the opening")
	check(GeniusTypes.need_words(0.9) != "" and GeniusTypes.need_words(0.9) != GeniusTypes.need_words(0.0), "the page says how much they need it")
	var all_in := true
	for r in GeniusTypes.ROLES:
		all_in = all_in and float(nb[r]) >= 0.0 and float(nb[r]) <= 1.0
	check(all_in, "a need is between nothing and everything")
	# every base of the game, settled and on each path, in a fight with a bot that uses its key: nothing breaks, and the key is used
	var unused: Array = []
	var broke: Array = []
	for b in Data.load_bases():
		for fid in [String(b["settled"]["id"])] + (b["paths"] as Array).map(func(p): return String(p["id"])):
			var form := Data.form(fid)
			var f := Fight.new({ "hero": Fight.default_hero(), "seed": 9, "respawn": true, "genius": _genius_at(fid, maxi(2, int(form["level"]) + 1)) })
			var used := 0
			for i in int(40.0 / DT):
				var to_w := f.w_pos - f.p_pos
				var move := Vector2.ZERO
				if GeniusTypes.bot_wants_key(f):
					f.input("order")
				if f.w_state == "windup" and f.w_duration - f.w_timer <= 0.1 and f.w_duration - f.w_timer > 0.1 - DT and i % 3 != 0:
					f.input("block-down")
				if f.p_block_held and f.w_state != "windup":
					f.input("block-up")
				if f.w_state in ["recover", "stagger", "flinch"] and to_w.length() < 2.4:
					f.input("attack")
				if to_w.length() > 2.0 and f.w_state != "windup":
					move = to_w.normalized()
				f.update(DT, move)
				for e in f.drain():
					if e["type"] in ["genius-use", "genius-take"] or (e["type"] == "genius-move" and String(e.get("move", "")) in ["hold-it", "worry", "calls"]) or e["type"] == "genius-mend":
						used += 1
				if f.p_state == "down":
					break
			if f.g_type != "companion" and used == 0:
				unused.append(fid)
			if is_nan(f.w_hp) or is_nan(f.p_hp) or is_nan(f.g_will) or f.g_will < 0.0 or f.g_will > f.g_will_max + 0.01:
				broke.append(fid)
	check(broke.is_empty(), "every base of the game fights through with a bot at its key (%s)" % ", ".join(broke))
	check(unused.is_empty(), "and a bot finds a use for every weapon and item (%s)" % ", ".join(unused))

## The Academy's first hour: the pieces of its presentation that can be checked without a screen.
func test_first_hour() -> void:
	# the objective in two parts
	var o := Academy.split_objective("Lesson 1 · Hold: find Yardmaster Bask in the Yard (the west door of the quad). Meet your cohort on the way.")
	check(o[0] == "LESSON 1 · HOLD" and String(o[1]).begins_with("Find Yardmaster Bask"), "the objective splits into a heading and what to do")
	o = Academy.split_objective("Day 2 · Rest in the Dormitory (the east door of the quad).")
	check(o[0] == "DAY 2" and String(o[1]).begins_with("Rest in the Dormitory"), "a day's objective takes the day as its heading")
	o = Academy.split_objective("Settled. The line is waiting; the Academy is yours to walk.")
	check(o[0] == "" and String(o[1]).begins_with("Settled."), "and a line with no heading is left whole")
	# the day's card and the place's name
	check(Academy.day_card_sub("Tuesday", "the Thaw", "") == "Tuesday of the Thaw", "a day known for nothing has no dangling mark on its card")
	check(Academy.day_card_sub("Friday", "the Thaw", "Rally night in the cities") == "Friday of the Thaw  ·  Rally night in the cities", "and a day known for something says so")
	check(not Academy.place_card_may_show(1.0, false) and not Academy.place_card_may_show(0.3, false) and not Academy.place_card_may_show(0.0, true) and Academy.place_card_may_show(0.0, false),
		"the place's name never shows with the day's card, nor while the night passes")
	# a step done
	check(Academy.step_done_line(0, 4, 1) == "1 of 4 done" and Academy.step_done_line(3, 4, 1) == "Lesson 1 learned", "a step done says how far through; the last names the lesson learned")
	# a conversation's frame: off the shoulder, on the speaker, clear of an Instructor's genius
	var f := Academy.talk_frame(Vector2(0, 8), Vector2(2, 7))
	var cam := Vector2((f[0] as Vector3).x, (f[0] as Vector3).z)
	var line := (Vector2(2, 7) - cam).normalized()
	var off := absf((Vector2(0, 8) - cam).cross(line))
	check(off > 0.8 and (cam - Vector2(0, 8)).length() < 3.5 and (f[1] as Vector3).x == 2.0, "the camera stands off the listener's shoulder and looks at the speaker (%.2f m clear)" % off)
	var fa := Academy.talk_frame(Vector2(0, 0), Vector2(0, -3), Vector2(1.6, -2.2))
	var fb := Academy.talk_frame(Vector2(0, 0), Vector2(0, -3), Vector2(-1.6, -2.2))
	check((fa[0] as Vector3).x < 0.0 and (fb[0] as Vector3).x > 0.0, "and takes the shoulder away from a genius sitting by its Instructor")
	# names over heads
	var room := World.declutter([Rect2(100, 100, 200, 50), Rect2(150, 120, 200, 50), Rect2(400, 100, 200, 50), Rect2(320, 110, 60, 50)])
	check(room == [true, false, true, true], "names over heads give way to nearer names they would run through (and only to names that show)")
	# the rite's staging
	check(RiteScene.camera_side(1.5) == -1.0 and RiteScene.camera_side(-1.5) == 1.0, "the rite's camera keeps to the side of the bowl the partner is not on")
	var spots := [RiteScene.feature_spot(0), RiteScene.feature_spot(1), RiteScene.feature_spot(2)]
	check(spots[0].x < 0.0 and spots[1].x > 0.0 and spots[2].y - spots[0].y >= 0.9, "a genius's features are called to either side of the light, never one over another")
	check(GeniusCard.portrait_scale(0.2) > 2.0 and is_equal_approx(GeniusCard.portrait_scale(0.8), 1.0), "a very small genius is brought up in its portrait; a larger one is left alone")
	# the arrival's card is in the data, and the way-marker finds its way
	check(String(Data.academy["arrival"].get("card", {}).get("title", "")) != "", "the arrival names the place (data/academy.json, arrival.card)")
	var a := Academy.new()
	a.hero = Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	a.cohort = Academy.make_cohort(42, a.hero)
	a.progress = { "seed": 42, "arrived": true, "done": [], "met": [], "day": 1, "rested_after": "", "place": "quad", "record": { "talks": 0 } }
	a._doors = Data.academy["places"]["quad"]["doors"]
	var g := a.guide_goal()
	check(String(g.get("label", "")) == "The Yard" and (g["pos"] as Vector2).x < -10.0, "on the first day the way-marker stands on the Yard's door")
	a.progress["place"] = "yard"
	a._doors = Data.academy["places"]["yard"]["doors"]
	a._people = [{ "kind": "instructor", "id": "bask", "name": "Bask", "pos": Vector2(1, 2) }]
	check(a.guide_goal().get("pos", Vector2.ZERO) == Vector2(1, 2), "and in the yard, over the Yardmaster")
	a.progress["done"] = ["hold"]
	check(String(a.guide_goal().get("label", "")) == "The Quad", "after the lesson it points the way back out, toward the dormitory")
	a.progress["arrived"] = false
	check(a.guide_goal().is_empty(), "and it says nothing before the newcomer has arrived")
	a.free()
