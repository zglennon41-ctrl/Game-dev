## The Gate, played: the genius's first refinement is read from the term (the three paths of
## its base, each with the lines of the Tally that speak for it, and a turning where the play
## has turned), the player chooses or lets it settle, the old body goes
## into light and the new one comes out of it; then the cohort's write-up, and Commencement.
class_name GateScene
extends RefCounted

signal done

var ac: Academy
var world: World
var sfx: Sfx
var hero: Dictionary
var cfg: Dictionary
var reading: Dictionary = {}
var _t := 0.0
var phase := "intro"

func _init(a: Academy, h: Dictionary) -> void:
	ac = a
	world = a.world
	sfx = a.sfx
	hero = h
	cfg = Data.academy["gate"]

func start() -> void:
	world.cine = true
	world.cine_speed = 1.6
	var p := Vector3(ac.fight.p_pos.x, 0, ac.fight.p_pos.y)
	world.cine_pos = p + Vector3(3.2, 2.4, 3.0)
	world.cine_look = p + Vector3(0, 1.3, 0)
	ac.say(cfg["instructor"], cfg["lines"]["intro"], _offer)

## The Reading: the Tally since the rite, read against the three paths of what it settled as.
func _offer() -> void:
	var g: Genius = ac.genius
	g.milestone("gate")
	g.day = maxi(g.day, int(GeniusResonance.instar_rule(2)["minDay"]))
	reading = g.read(2)
	ac.show_reading(reading, func(i: int): _take(i))

func _take(i: int) -> void:
	var g: Genius = ac.genius
	var old_name := g.form_name()
	var c := g.take(i)
	g.save_to(hero)
	ac.save()
	var col: Color = World.SHAPE_COLORS.get(hero["shape"], Color.WHITE)
	# The old body goes into light: its seams open, it becomes a shape of light and nothing
	# else, and the light draws in. Then the new body comes out of it. (An evolution is a
	# thing to watch, not a flash: docs/genius-evolutions.md.)
	var p := Vector3(ac.fight.p_pos.x, 0, ac.fight.p_pos.y)
	var body: GeniusBody = world._g_body
	var at: Vector3 = body.global_position if body and is_instance_valid(body) else p + Vector3(0.6, 0, 0)
	var tall: float = body.stands if body and is_instance_valid(body) else 0.6
	world.cine_speed = 2.4
	world.cine_pos = at + Vector3(1.5 + tall, 0.9 + tall, 2.2 + tall * 1.6)
	world.cine_look = at + Vector3(0, tall * 0.6, 0)
	sfx.play("pattern", 0.5)
	var beat := [0]
	var tw := ac.create_tween()
	tw.tween_method(func(k: float):
		if body and is_instance_valid(body):
			body.set_molt(minf(1.0, k * 1.6))
			body.set_flood(k * k)
		# the light draws in, quicker as it goes
		if int(k * (5.0 + 6.0 * k)) > beat[0]:
			beat[0] = int(k * (5.0 + 6.0 * k))
			world.burst(at + Vector3(0, tall * 0.5, 0), col, 10, 1.2 + 2.0 * k)
			world._ring_wave(at, col, 2.4 - 1.6 * k), 0.0, 1.0, 2.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tw.tween_callback(func(): _becomes(g, c, i, old_name, col, at))

## The new body, out of the light.
func _becomes(g: Genius, c: Dictionary, i: int, old_name: String, col: Color, at: Vector3) -> void:
	world.flash_screen(col, 0.8)
	world._ring_wave(at, col, 6.0)
	world.burst(at + Vector3(0, 0.8, 0), col, 120, 7.0)
	world.impact(at + Vector3(0, 0.8, 0), col, 2.4)
	world.slowmo(0.5, 0.3)
	sfx.play("pattern", 0.9)
	sfx.play("heavy", 0.6)
	world.build_hero(hero)
	var now: GeniusBody = world._g_body
	if now and is_instance_valid(now):
		var rest := now.lines
		now.set_flood(1.0)
		var tw := ac.create_tween()
		tw.tween_method(func(k: float):
			if is_instance_valid(now):
				now.set_flood(1.0 - k)
				now.set_molt(maxf(rest, 1.0 - k)), 0.0, 1.0, 1.3).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		world.cine_pos = at + Vector3(1.6 + now.stands, 1.0 + now.stands, 2.4 + now.stands * 1.7)
		world.cine_look = at + Vector3(0, now.stands * 0.6, 0)
	var feats: Array = c["features"].map(func(f): return Rite.feature_label(String(f)))
	# where it now is on its line, in the player's words
	var stage := String(Data.genius().get("stages", {}).get(str(g.level()), {}).get("name", "Second Form")).to_upper()
	ac.title_card(g.form_name().to_upper(), "%s  ·  %s  ·  %s" % [stage, g.kind().to_upper(), ", ".join(feats)], col)
	ac.show_card(g.to_dict(), col, stage)
	var key := "settled" if i == -1 else "chosen"
	var line := String(cfg["lines"][key]).replace("{genius_name}", g.name).replace("{form}", g.form_name().to_lower()).replace("{was}", old_name.to_lower())
	ac.say(cfg["instructor"], [line], func():
		ac.hide_card()
		_reckoning())

## The Ledgers are read at the lamp hour: the crisis ends one way, and the world is written.
func _reckoning() -> void:
	var e: Dictionary = ac.reckoning()
	if e.is_empty():
		_writeup()
		return
	ac.title_card(String(e["title"]).to_upper(), "the Reckoning", Color(0.85, 0.75, 0.5))
	ac._sting("reckoning")
	ac.say(cfg["instructor"], ["The Ledgers were read at the lamp hour, while you were on the platform.", "[i]%s[/i]" % e["text"]], _writeup)

## The cohort's write-up: what the term saw, from the record.
func _writeup() -> void:
	var rec: Dictionary = ac.progress["record"]
	var lines: Array = []
	for w in cfg["writeup"]:
		var t: Array = w["test"]
		var v: Variant = rec.get(t[0], 0)
		var want: Variant = t[2]
		var ok := false
		match String(t[1]):
			">=": ok = float(v) >= float(want)
			">": ok = float(v) > float(want)
			"<=": ok = float(v) <= float(want)
			"<": ok = float(v) < float(want)
			"==": ok = (v == want) or (float(v) == 1.0 if want is bool and want else false)
		if ok:
			lines.append(w["text"])
	# What the cohort saw you do for them goes in first.
	for extra in ac.progress.get("writeup_extra", []):
		lines.push_front(extra)
	if lines.size() > 6:
		lines = lines.slice(0, 6)
	ac.progress["writeup"] = lines
	ac.say(cfg["instructor"], [cfg["lines"]["writeup_intro"]], func():
		ac.say("", ["[i]%s[/i]" % "  ".join(lines), "[i]%s[/i]" % cfg["closing"]], _commencement))

func _commencement() -> void:
	var lines: Array = cfg["lines"]["commencement"].map(func(l): return ac.fill(String(l)))
	world.cine = false
	ac.say(cfg["instructor"], lines, func(): ac.declare(func(): done.emit()))
