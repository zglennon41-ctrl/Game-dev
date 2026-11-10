## The Gate, played: the genius's Second Form is read from the term (three candidates, with the
## lines of the Tally that chose them), the player chooses or lets it settle, the old body goes
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

## The Reading: the genius reads the Tally for its Second Form and offers three.
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
	# The old body into light, the new out of it.
	var p := Vector3(ac.fight.p_pos.x, 0, ac.fight.p_pos.y)
	world.cine_pos = p + Vector3(2.4, 2.0, 3.6)
	world.cine_look = p + Vector3(0.6, 1.2, 0)
	world.flash_screen(col, 0.8)
	world._ring_wave(p, col, 6.0)
	world.burst(p + Vector3(0.6, 1.2, 0), col, 120, 7.0)
	world.impact(p + Vector3(0.6, 1.2, 0), col, 2.4)
	world.slowmo(0.5, 0.3)
	sfx.play("pattern", 0.9)
	sfx.play("heavy", 0.6)
	world.build_hero(hero)
	var feats: Array = c["features"].map(func(f): return Rite.feature_label(String(f)))
	ac.title_card(g.form_name().to_upper(), "SECOND FORM  ·  %s  ·  %s" % [String(c["expression"]).to_upper(), ", ".join(feats)], col)
	ac.show_card(g.to_dict(), col, "SECOND FORM")
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
