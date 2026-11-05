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
	test_shape_kits()
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
func run_bot(seconds: float, smart: bool, hero := {}) -> Fight:
	var opts := { "seed": 5 }
	if not hero.is_empty():
		opts["hero"] = hero
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
