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
func run_bot(seconds: float, smart: bool) -> Fight:
	var f := Fight.new({ "seed": 5 })
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
				if f.p_will > 40 and f.now >= float(f.p_cooldowns.get("ground-strike", 0.0)):
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
	return "%d wolves, %d hits, %d parries, %d staggers, %d patterns (%d fizzled), bitten %d, hp %d" % [s["wolves_down"], s["hits"], s["parries"], s["staggers"], s["patterns"], s["pattern_fizzles"], s["hurts"], f.p_hp]

func test_bots() -> void:
	var good := run_bot(120, true)
	var mash := run_bot(120, false)
	print("  skilled bot: ", summary(good))
	print("  masher bot:  ", summary(mash))
	check(good.stats["parries"] > 3, "the skilled bot parries")
	check(good.stats["patterns"] > 0 and good.stats["pattern_fizzles"] == 0, "the skilled bot lands Patterns")
	check(good.stats["hurts"] < mash.stats["hurts"], "the skilled bot is bitten less")
	check(good.stats["wolves_down"] >= mash.stats["wolves_down"], "the skilled bot fells at least as many wolves")
	check(good.stats["wolves_down"] <= 12, "a wolf takes real work, even played perfectly (%d felled)" % good.stats["wolves_down"])
