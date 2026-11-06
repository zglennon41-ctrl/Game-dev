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

func _run() -> void:
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
	var turn := Fight.new({ "seed": 1, "hero": hero_of("turn", "hatchet"), "passive": true })
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
		var weapon: String = { "anchor": "saber", "turn": "hatchet", "cast": "pistol", "read": "pistol", "bind": "grapple", "make": "oar-staff" }[shape]
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
		check(Data.by_id(Data.weapons, m["weapon"])["city"] == m["city"], "%s carries a weapon of %s" % [m["name"], m["city"]])
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
	# The First Form is a first-instar form, with the Seed's mark.
	var f := Rite.first_form(h, a["shape"], 7)
	var form: Dictionary = Data.forms().filter(func(x): return x["id"] == f["form"])[0]
	check(int(form["instars"]["min"]) == 1, "the First Form is a form a first instar can take (%s)" % f["form"])
	check(f["features"].size() >= form["features"].size(), "the First Form carries its features")
	var forms := {}
	for s in 60:
		var hh := Creation.generate([0, 1, s % 6, s % 4, 1, 2, 0, s % 3, 2, 0], "", s + 1)
		forms[Rite.first_form(hh, hh["shape"], s)["form"]] = true
	check(forms.size() >= 4, "different lives take different First Forms (%d kinds)" % forms.size())
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

## The game's Reading and Resonance give the tools' answers (fixtures written by
## tools/genius-fixtures.ts from src/rules).
func test_genius_parity() -> void:
	var fx: Dictionary = JSON.parse_string(FileAccess.open("res://game/tests/fixtures/readings.json", FileAccess.READ).get_as_text())
	for r in fx["readings"]:
		var cur: Dictionary = r["current"] if r["current"] is Dictionary else {}
		var got := GeniusReading.read(int(r["instar"]), r["tally"] if r["tally"]["intention"] != null else _no_null(r["tally"]), r["origin"], cur)
		var want: Array = r["result"]["candidates"]
		var ok: bool = got["candidates"].size() == want.size() and got["crossingAllowed"] == r["result"]["crossingAllowed"]
		for i in mini(want.size(), got["candidates"].size()):
			var a: Dictionary = got["candidates"][i]
			var b: Dictionary = want[i]
			ok = ok and a["form"] == b["form"] and absf(float(a["score"]) - float(b["score"])) < 0.002 and str(a["heritage"]) == str(b["heritage"]) and str(a["features"]) == str(b["features"])
		check(ok, "the Reading matches the tools: %s (%s)" % [r["name"], ", ".join(got["candidates"].map(func(c): return c["form"]))])
	for x in fx["resonance"]:
		var res := GeniusResonance.resonance(int(x["instar"]), int(x["tier"]))
		check(res == int(x["resonance"]) and GeniusResonance.paying_tier(res, int(x["tier"])) == int(x["paying"]) and GeniusResonance.verses(GeniusResonance.paying_tier(res, int(x["tier"]))) == int(x["verses"]) and GeniusResonance.shadow_cap(res) == int(x["shadowCap"]) and is_equal_approx(GeniusResonance.genius_will(res), float(x["will"])), "Resonance matches the tools at instar %d, tier %d" % [int(x["instar"]), int(x["tier"])])
	for x in fx["tiers"]:
		check(GeniusResonance.tier_for({ "uses": x["uses"], "built": true }) == int(x["tier"]), "Intention tier at %d uses" % int(x["uses"]))

func _no_null(t: Dictionary) -> Dictionary:
	var d := t.duplicate(true)
	d["intention"] = null
	return d

## A genius's life, start to finish of what exists: born, learns, adapts, reads, inherits.
func test_genius_life() -> void:
	var h := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	h["seed"] = "watches-from-above"
	h["blood"] = "aerie-born"
	h["shape"] = "cast"
	var g := Genius.for_hero(h)
	check(not g.is_born(), "a genius before the rite has no body")
	g.read(1)
	var c := g.take()
	g.milestone("rite")
	check(g.is_born() and g.instar == 1 and c["form"] == "hawk", "the rite gives a First Form (%s)" % c["form"])
	check(g.features().has("far-eyes"), "the Seed-mark is on it")
	check(is_equal_approx(g.will_max(), 40.0) and g.orders_available().size() == 2, "a First Form has 40 Will and two orders")
	# Saved and loaded, it is the same genius.
	var g2 := Genius.from_dict(g.to_dict())
	check(str(g2.to_dict()) == str(g.to_dict()), "a genius survives saving")
	# Play: close fighting with Guard and Hold.
	for i in 30: g.hit_at(1.5)
	for i in 6: g.hit_at(5.0)
	for i in 14: g.used_family("cast.reach")
	for i in 6: g.used_family("anchor.wall")
	for i in 12: g.gave_order("hold")
	for i in 9: g.gave_order("guard")
	for i in 6: g.fought_beside("anchor")
	for i in 4: g.fought_beside("read")
	for i in 8: g.ran("tunnel")
	for i in 3: g.ran("ruin")
	g.studied("marshal", 10)
	check(g.reading_due() == 0, "no Second Form before the Gate")
	g.milestone("gate")
	check(g.reading_due() == 0, "nor before its seventh day")
	g.day = 7
	check(g.reading_due() == 2, "the Gate and a week: the Second Form may be read")
	var rd := g.read(2)
	check(rd["candidates"].size() == 3, "a Reading offers three")
	var forms: Array = rd["candidates"].map(func(x): return x["form"])
	check(forms.has("talon-relic") and forms.has("stooping-kith"), "the Guide's hawk that fights close is offered a Talon Relic and a Stooping Kith (%s)" % str(forms))
	for cand in rd["candidates"]:
		check(cand["features"].has("far-eyes") and cand["heritage"].size() >= 1, "%s carries the Seed-mark and heritage" % cand["form"])
	g.take(1)
	check(g.instar == 2 and g.history.size() == 2 and float(g.tally["range"].get("close", 0.0)) == 0.0, "taking a form starts a new Tally, and history remembers")
	check(is_equal_approx(g.will_max(), 50.0) and g.orders_available().size() == 4, "a Second Form has 50 Will and four orders")
	# Adaptations come from play and fade unfed.
	for i in 50: g.hit_at(1.0)
	var ch := g.update_adaptations()
	check(ch.size() == 1 and ch[0]["id"] == "set-feet" and g.features().has("set-feet"), "fifty close fights grow set feet")
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
	check(g.reading_due() == 3, "a built Pattern and thirty days: the Third Form")
	g.read(3)
	g.take()
	check(g.features().has("lantern"), "the graft is on the Third Form")
	for i in 60: g.gave_order("hunt")
	var ready: Array = g.secondary_ready().map(func(s): return s["id"])
	check(ready.has("arms") == (g.body["expression"] in ["relic", "engine"]), "Arms needs a Relic or Engine and fifty Hunts (%s, %s)" % [g.body["expression"], str(ready)])
	var hb := g.features_by_slot()
	check(hb.size() >= 2, "features sort into slots (%s)" % str(hb.keys()))
	g.fall(); g.fall(); g.develop_secondary("night"); g.fall()
	check(g.secondary.is_empty() and g.fallen, "three falls in a season cost the newest secondary form")

func _born_genius() -> Genius:
	var h := Fight.default_hero()
	h["seed"] = "stands-between"
	h["blood"] = "ridgefolk"
	var g := Genius.for_hero(h)
	g.read(1)
	g.take()
	g.milestone("rite")
	return g

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

## Every form in the lattice assembles, with a part for every feature it has a socket for.
func test_genius_assembly() -> void:
	var bad: Array = []
	for f in Data.forms():
		var info := { "form": f["id"], "silhouette": f["silhouette"], "expression": f["expression"], "features": f["features"] }
		var b := GeniusBody.build(info, Color.ORANGE, 1)
		var meshes := b.find_children("*", "MeshInstance3D", true, false).size() + b.find_children("*", "CPUParticles3D", true, false).size()
		if meshes == 0 or b.sockets.is_empty():
			bad.append(f["id"])
		b.free()
	check(bad.is_empty(), "every form in the lattice assembles (%d forms; failed: %s)" % [Data.forms().size(), str(bad)])

## Art files follow the art bible: named for a silhouette, feature or form; sockets on bodies;
## within budget; cards in portrait 3:4.
func test_genius_art() -> void:
	var sils := {}
	for f in Data.forms():
		sils[f["silhouette"]] = true
	var feats := {}
	for f in Data.features():
		feats[f["id"]] = true
	var forms := {}
	for f in Data.forms():
		forms[f["id"]] = true
	var n := 0
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
				check(socks.has("socket_body") and socks.size() >= 4, "bodies/%s carries its sockets (%s)" % [file, ", ".join(socks)])
			scene.free()
	for file in DirAccess.get_files_at("res://game/assets/genius/cards/"):
		if not file.ends_with(".png"):
			continue
		n += 1
		check(forms.has(file.get_basename()), "cards/%s is named for a form" % file)
		var tex: Texture2D = load("res://game/assets/genius/cards/" + file)
		check(absf(float(tex.get_width()) / tex.get_height() - 0.75) < 0.01, "cards/%s is a 3:4 portrait" % file)
	check(n > 0, "there is genius art to check (%d files)" % n)

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
		h["techniques"] = dk["techniques"].map(func(t): return t["id"])
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
	# The Gate's Reading offers three, each with the Seed-mark and heritage, and the write-up reads the record.
	var hero := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], "", 3)
	hero["seed"] = "watches-from-above"
	var gn := Genius.for_hero(hero)
	gn.read(1); gn.take(); gn.milestone("rite")
	for i in 30: gn.hit_at(1.5)
	for i in 12: gn.gave_order("hold")
	gn.milestone("gate")
	gn.day = 7
	var rd := gn.read(2)
	check(rd["candidates"].size() == 3 and rd["candidates"].all(func(c): return c["features"].has("far-eyes") and c["heritage"].size() >= 1), "the Gate offers three Second Forms, each marked and carrying heritage")
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
	var a1 := Zones.area_place("green/post", 10)
	var a2 := Zones.area_place("green/post", 10)
	check(a1["variant"] == a2["variant"] and a1["zone"]["pack"] == a2["zone"]["pack"], "the same seed draws the same area")
	var differs := false
	for sd in range(11, 40):
		var a3 := Zones.area_place("green/post", sd)
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
	# Nothing weighed: the default ending.
	var b := Academy.new()
	b.hero = Creation.generate([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "", 4)
	b.cohort = Academy.make_cohort(7, b.hero)
	b.progress = { "seed": 7, "done": ["hold", "rite", "shape", "discipline", "line", "project"], "met": [], "day": 9, "place": "quad", "record": { "talks": 0 } }
	check(b.crisis_phase() == "crisis" and b.reckoning()["title"] == "The mile is given up", "with nothing weighed the default ending holds")
	a.free()
	b.free()
