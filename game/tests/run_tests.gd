## Headless tests for the pulse room's rules and fight.
## Run: godot --headless --path . res://game/tests/tests.tscn   (or: npm run test:game)
extends Node

var failures := 0
var passes := 0

func check(cond: bool, what: String) -> void:
	if cond:
		passes += 1
	else:
		failures += 1
		printerr("  FAIL: ", what)

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	test_judge()
	test_breaks_and_chord()
	test_fight_bots()
	test_parry()
	test_block_and_hurt()
	test_fumble()
	test_breaks_from_techniques()
	test_stance()
	print("%d passed, %d failed" % [passes, failures])
	get_tree().quit(1 if failures > 0 else 0)

func test_judge() -> void:
	check(Data.beat_window_ms("green") == 200, "Green window 200 ms")
	check(Data.beat_window_ms("amber") == 150, "Amber window 150 ms")
	var j := CombatRules.judge(1.27, 0, 0.6, 150)
	check(j["beat"] == 2 and roundi(j["offset_ms"]) == 70 and j["perfect"], "70 ms late is perfect at 150")
	check(not CombatRules.judge(1.28, 0, 0.6, 150)["perfect"], "80 ms late is off the beat")
	check(CombatRules.judge(1.28, 0, 0.6, 150)["output"] == 0.7, "off the beat is 70%")
	check(CombatRules.judge(1.125, 0, 0.6, 150)["perfect"], "75 ms early is perfect")

func test_breaks_and_chord() -> void:
	var b := CombatRules.BreakMeter.new()
	check(b.hit(true) == 0 and b.hit(true) == 0, "two breaks open nothing")
	b.slip()
	b.hit(true); b.hit(true)
	check(b.hit(true) == 3, "three breaks open three beats")
	var c := CombatRules.ChordTracker.new()
	var any := false
	for i in 8: any = any or c.beat(true)
	check(not any, "no Chord during the eight")
	check(c.beat(false) and c.beat(false) and c.beat(false) and not c.beat(true), "three beats of Chord")

## Run a fight at 60 fps with an input policy; the bot walks toward the wolf.
func run_fight(seconds: float, policy: Callable, opts := {}) -> Fight:
	var o := { "seed": 3 }
	o.merge(opts, true)
	var f := Fight.new(o)
	for frame in int(seconds * 60):
		var t := frame / 60.0
		policy.call(f, t, frame)
		var d := f.w_pos - f.p_pos
		f.update(t, d.normalized() if d.length() > 1.3 else Vector2.ZERO)
		f.drain()
	return f

func test_fight_bots() -> void:
	var on_beat := run_fight(120, func(f: Fight, t: float, _frame: int):
		var k := roundi(t / f.period)
		if absf(t - k * f.period) >= 1.0 / 120.0:
			return
		if f.w_mode == "windup" and f.w_strike_beat == k:
			f.input("hold-down", t); f.input("hold-up", t + 0.01)
		elif f.dist() < 2.0 and k > f.p_last_action_beat:
			f.input("ground-strike" if f.p_will > 60 else "strike", t))
	var masher := run_fight(120, func(f: Fight, t: float, frame: int):
		if frame % 11 == 0 and f.dist() < 2.0:
			f.input("strike", t))
	print("  on-beat bot: ", _summary(on_beat))
	print("  masher bot:  ", _summary(masher))
	check(on_beat.stats["wolves_down"] > masher.stats["wolves_down"], "on the beat fells more wolves than mashing")
	check(on_beat.stats["parries"] > 0, "the on-beat bot parries")
	check(on_beat.stats["staggers"] > 0, "the on-beat bot breaks the wolf")
	check(on_beat.stats["hurts"] < masher.stats["hurts"], "the on-beat bot is bitten less")
	check(masher.stats["fumbles"] > 0, "mashing fumbles")

func _summary(f: Fight) -> String:
	var s := f.stats
	return "%d wolves, %d hits, %d parries, %d staggers, bitten %d, fumbles %d, hp %d" % [s["wolves_down"], s["hits"], s["parries"], s["staggers"], s["hurts"], s["fumbles"], f.p_hp]

func _wolf_winding(f: Fight, beat: int) -> void:
	f.w_mode = "windup"
	f.w_strike_beat = beat
	f.w_pos = f.p_pos + Vector2(1.0, 0)

func test_parry() -> void:
	var f := Fight.new({ "seed": 1 })
	_wolf_winding(f, 5)
	f.p_will = 50
	f.update(4.9 * f.period)
	f.input("hold-down", 5 * f.period - 0.05)
	f.update(5 * f.period + 0.2)
	var types := f.drain().map(func(e): return e["type"])
	check(types.has("parry") and f.p_hp == 100 and f.p_will > 55 and f.w_mode == "stagger", "a perfect Hold parries: no damage, Will back, the wolf reels")
	var g := Fight.new({ "seed": 1 })
	_wolf_winding(g, 5)
	g.update(5 * g.period + 0.01)
	g.input("hold-down", 5 * g.period + 0.08)
	g.update(5 * g.period + 0.3)
	check(g.drain().map(func(e): return e["type"]).has("parry"), "a late Hold inside the window parries")

func test_block_and_hurt() -> void:
	var f := Fight.new({ "seed": 1 })
	_wolf_winding(f, 5)
	f.input("hold-down", 4.5 * f.period)
	f.update(5 * f.period + 0.2)
	check(f.p_hp == 94, "a held guard blocks for half")
	var g := Fight.new({ "seed": 1 })
	_wolf_winding(g, 5)
	g.update(5 * g.period + 0.2)
	check(g.p_hp == 88, "no guard takes the full bite")

func test_fumble() -> void:
	var f := Fight.new({ "seed": 1, "passive": true })
	f.w_pos = f.p_pos + Vector2(1.0, 0)
	f.input("strike", 1 * f.period)
	f.input("strike", 1 * f.period + 0.05)
	var types := f.drain().map(func(e): return e["type"])
	check(types.has("hit") and types.has("fumble") and f.p_chain == 0, "two Projects in one beat fumble and break the chain")

func test_breaks_from_techniques() -> void:
	var f := Fight.new({ "seed": 1, "passive": true })
	for k in [1, 2, 3]:
		f.w_pos = f.p_pos + Vector2(1.0, 0)
		f.input("strike", k * f.period)
	check(f.w_mode != "stagger", "saber strikes do not break")
	for k in [4, 6, 8]:
		f.w_pos = f.p_pos + Vector2(1.0, 0)
		f.input("ground-strike", k * f.period)
	check(f.w_mode == "stagger", "three on-beat Ground Strikes break a Read beast")

func test_stance() -> void:
	var f := Fight.new({ "seed": 1, "passive": true })
	f.w_pos = f.p_pos + Vector2(1.0, 0)
	f.input("stance", 1 * f.period)
	check(f.p_stance, "stance on the beat enters at once")
	f.update(2 * f.period)
	check(f.p_will < 100, "stance drains Will")
	f.drain()
	f.w_pos = f.p_pos + Vector2(1.0, 0)
	f.input("strike", 3 * f.period)
	var hit: Dictionary = {}
	for e in f.drain():
		if e["type"] == "hit": hit = e
	check(hit.get("damage", 0) == 15, "stance hits half again as hard")
