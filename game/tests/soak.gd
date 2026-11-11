## The soak test: many different characters play the whole game, from the questionnaire's
## result to Commencement, without a window and faster than the clock.
##
##   npm run soak                      every character of the spread (about forty)
##   npm run soak -- --count=6         the first six
##   npm run soak -- --only=17         one of them, by number (to look at a failure again)
##   npm run soak -- --debug           and say what the autopilot is doing
##
## The spread: every home (13), every weapon a school teaches as the weapon carried from the
## station and another of the same school chosen at the Discipline lesson (so every weapon type
## is played through both halves of the term), the six Shapes in turn, both sexes, the bloods
## the creator offers, the whole term and advanced standing. Each character is made as the
## creator makes one (Creation.generate from answers and a spark).
##
## The game is the real one (game/scenes/main.tscn) with the autopilot at the keys. The test
## presses the screens' own buttons, as a player does; it leaves by the pause menu and comes
## back by "Continue"; it closes the game without warning and opens it again.
##
## It fails on: a step, a scene or a choice that does not move for STALL seconds of game time;
## a character not through in LIMIT minutes; a choice with nothing in it; words on the screen
## with a {token} or a $name left in them; a character who leaves without what the Academy
## promises. Script errors are printed by the engine: tools/soak.sh reads the log for them.
extends Node

const MAIN := preload("res://game/scenes/main.tscn")
const SAVE := "user://soak.cfg"
const STALL := 150.0          # game seconds with nothing moving
const LIMIT := 75.0 * 60.0    # game seconds for one character, creation to Commencement

var main: Node = null
var args := {}
var cast: Array = []
var at := -1
var who: Dictionary = {}
var rng := RandomNumberGenerator.new()

var _t := 0.0                 # this character's game seconds
var _wall0 := 0
var _sig := ""
var _sig_t := 0.0
var _screen_t := 0.0
var _box_t := 0.0
var _seen := {}
var _next_break := 0.0
var _breaks := 0
var _state := "idle"
var _fails: Array = []        # this character's
var _results: Array = []
var _waiting := 0.0
var _last_lesson := ""
var _steps_seen := {}

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	process_priority = 1000   # after the game's own frame
	for a in OS.get_cmdline_user_args():
		var kv := String(a).trim_prefix("--").split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else true
	Settings.use_file(SAVE)
	_wipe_save()
	cast = make_cast(int(args.get("seed", "20261111")))
	if args.has("list"):
		for i in cast.size():
			print("%02d %s" % [i, _who_line(cast[i])])
		get_tree().quit(0)
		return
	_new_main()
	call_deferred("_next_character")

func _wipe_save() -> void:
	Settings.cfg = ConfigFile.new()
	Settings.cfg.save(SAVE)

func _new_main() -> void:
	if main:
		main.free()
	get_tree().paused = false
	Engine.time_scale = 1.0
	main = MAIN.instantiate()
	add_child(main)
	main.fixed_clock = true
	main._args["bot"] = true
	if args.has("debug"):
		main._args["debug"] = true
		main.academy.debug = true

# --- The spread -------------------------------------------------------------------

## Every school weapon as the weapon carried, for a character of that home; three from
## Alexandria, which has no school; Shapes in turn. Answers are searched for (seeded) until the
## creator's own generator gives that home and that Shape.
static func make_cast(seed_value: int) -> Array:
	var r := RandomNumberGenerator.new()
	r.seed = seed_value
	var out: Array = []
	var homes: Array = Data.creation["questions"][0]["answers"]
	var n := 0
	for hi in homes.size():
		var probe: Array = [hi]
		for q in range(1, Data.creation["questions"].size()):
			probe.append(0)
		var city := String(Creation.generate(probe)["city"])
		var school: Array = Data.weapons.filter(func(w): return w["city"] == city)
		var slots := school.size() if not school.is_empty() else 3
		for k in slots:
			var want_shape: String = Creation.SHAPES[n % Creation.SHAPES.size()]
			var h := {}
			var best := {}
			for tries in 400:
				var ans: Array = [hi]
				for q in range(1, Data.creation["questions"].size()):
					ans.append(r.randi() % Data.creation["questions"][q]["answers"].size())
				var spark := r.randi() % 100000
				# the blood: one of the three the creator offers
				var offered := Creation.suggest_bloods(Creation.tally_with(ans, spark))
				var blood := String(offered[r.randi() % offered.size()]["id"])
				h = Creation.generate(ans, blood, spark)
				if best.is_empty():
					best = h
				if h["shape"] == want_shape:
					best = h
					break
			h = best
			# the weapon carried: the creator's "Or carry" chips are the school's weapons
			var teach := Creation.school_weapons(h)
			var carried: Dictionary = teach[k % teach.size()]
			h["weapon"] = carried["id"]
			h["weapon_override"] = carried["id"]
			var sex := "m" if n % 2 == 0 else "f"
			h["look"]["sex"] = sex
			h["body"] = "%s-%s" % [h["city"], sex]
			h["name"] = Creation.name_for(h["city"], int(h["spark"]))
			out.append({ "hero": h, "n": n, "then": String(teach[(k + 1) % teach.size()]["id"]),
				"advanced": n % 7 == 5, "troubles": n % 3 == 1 })
			n += 1
	return out

func _who_line(c: Dictionary) -> String:
	var h: Dictionary = c["hero"]
	return "%s: %s %s of %s (%s), %s, %s then %s%s%s" % [h["name"], h["blood"], h["shape"], h["city"], h["body"], h["discipline"], h["weapon"], c["then"],
		", advanced standing" if c["advanced"] else "", ", takes the board's troubles" if c["troubles"] else ""]

# --- One character ----------------------------------------------------------------

func _next_character() -> void:
	at += 1
	if args.has("only"):
		if at == 0:
			at = int(args["only"])
		else:
			at = cast.size()
	if at >= cast.size() or (args.has("count") and at >= int(args["count"])):
		_finish()
		return
	who = cast[at]
	rng.seed = 7919 * (at + 1)
	seed(104729 * (at + 1))
	_t = 0.0
	_wall0 = Time.get_ticks_msec()
	_sig = ""
	_sig_t = 0.0
	_fails = []
	_breaks = 0
	_next_break = rng.randf_range(60.0, 200.0)
	_steps_seen = {}
	# A fresh save, but not a first life: the second-life offer is part of the road.
	_wipe_save()
	if at > 0:
		Settings.cfg.set_value("hero", "settled_count", 1)
	print("SOAK %02d/%02d  %s" % [at, cast.size() - 1, _who_line(who)])
	var h: Dictionary = who["hero"].duplicate(true)
	main.academy.auto_want = String(who["then"])
	if who["troubles"]:
		main._args["troubles"] = true
	else:
		main._args.erase("troubles")
	_state = "play"
	main._hero_made(h)

func _fail(what: String) -> void:
	var line := "%s  [%s]" % [what, _where()]
	if _fails.size() < 12:
		_fails.append(line)
	printerr("SOAK FAIL %02d %s: %s" % [at, who["hero"]["name"], line])

func _where() -> String:
	var s := "t=%.0fs mode=%s" % [_t, main.mode]
	if main.mode == "academy":
		var a: Academy = main.academy
		var f: Fight = a.fight
		s += " day=%s place=%s done=%s lesson=%s step=%d" % [str(a.progress.get("day", "")), str(a.progress.get("place", "")), ",".join(a.progress.get("done", [])), str(a._lesson.get("id", "")), a._step]
		if a.in_lesson() and a._step >= 0 and a._step < a._lesson["steps"].size():
			var st: Dictionary = a._lesson["steps"][a._step]
			s += " \"%s\" goal=%s count=%d bot=%s" % [st.get("title", ""), JSON.stringify(st["goal"]).substr(0, 90), a._count, a.bot_mode()]
		s += " need=%s target=%s talking=%s rite=%s gate=%s naming=%s choice=%s reading=%s screen=%s paused=%s" % [a.next_need(), str(a._target.get("kind", "")), str(a.talking()), str(a._rite != null), str(a._gate != null), str(a._naming), str(a._choice_box != null), str(a._reading_box != null), str(main.hud.screen.visible), str(get_tree().paused)]
		if f:
			s += " hero=%s hp=%.0f will=%.0f at=%s weapon=%s foe=%s/%s hp=%.0f dist=%.1f" % [f.p_state, f.p_hp, f.p_will, str(f.p_pos.round()), str(a.hero.get("weapon", "")), str(f.beast.get("id", "")), f.w_state, f.w_hp, f.dist()]
	elif main.mode == "prologue" and main.prologue:
		s += " beat=%d foe=%s hp=%.0f hero=%s weapon=%s" % [main.prologue.beat, main.fight.w_state, main.fight.w_hp, main.fight.p_state, str(main.hero.get("weapon", ""))]
	return s

func _signature() -> String:
	var hud: Hud = main.hud
	var parts: Array = [main.mode, hud.screen.visible, get_tree().paused]
	if hud.screen.visible:
		var b := _buttons(hud.screen)
		parts.append(b[0].text if not b.is_empty() else "")
	if main.mode == "prologue" and main.prologue:
		parts.append_array([main.prologue.beat, main.prologue.hits, int(main.fight.w_hp / 20.0)])
	if main.mode == "academy":
		var a: Academy = main.academy
		var rec: Dictionary = a.progress.get("record", {})
		parts.append_array([a.progress.get("place", ""), a.progress.get("day", 0), a.progress.get("done", []).size(), a.progress.get("met", []).size(), a.progress.get("rested_after", ""),
			a._lesson.get("id", ""), a._step, a._count, a._spar_wins, a._spar_rung, a._holding, int(a._hold_t / 10.0), int(a._held), a._line_i, a._lines.size(), a.talking(),
			a._naming, a._choice_box != null, a._reading_box != null, a._gate != null, a._rite.phase if a._rite else "", rec.get("marks", 0), rec.get("quests", 0), rec.get("quests_lost", 0),
			rec.get("troubles", 0), rec.get("wolves_felled", 0), rec.get("spars_won", 0), rec.get("spars_lost", 0), rec.get("rescued", 0), a.progress.get("shade_visits", 0),
			int(a.fight.w_hp / 25.0) if a.fight else 0, int(a.fight.p_will / 25.0) if a.fight else 0])
	return str(parts)

static func _buttons(under: Node) -> Array:
	var out: Array = []
	if under == null or not is_instance_valid(under):
		return out
	for c in under.get_children():
		if c is Button and (c as Button).is_visible_in_tree() and not (c as Button).disabled:
			out.append(c)
		out.append_array(_buttons(c))
	return out

func _process(delta: float) -> void:
	if _state != "play" or main == null:
		return
	# No hit-stop and no slow motion here: they are kept by the wall clock, and this run is not.
	Engine.time_scale = 1.0
	var dt := minf(delta, 0.1)
	_t += dt
	var hud: Hud = main.hud
	var a: Academy = main.academy
	# What the game stepped round and said so.
	while not a.problems.is_empty():
		_fail(String(a.problems.pop_front()))
	_read_words()
	_watch_steps()
	# The screens: a player presses a button.
	if hud.screen.visible:
		_screen_t += dt
		if _screen_t > 0.5:
			_screen_t = 0.0
			_press_screen()
	else:
		_screen_t = 0.0
	# A choice or a Reading: a player picks one (the weapon is the one this character is here to try).
	var box: Control = a._choice_box if a._choice_box else a._reading_box
	if main.mode == "academy" and box and is_instance_valid(box):
		_box_t += dt
		if _box_t > 0.6:
			_box_t = -5.0
			var bs := _buttons(box)
			var wanted := bs.filter(func(b): return a.auto_want != "" and Creation.weapon(a.auto_want).get("name", "-") == b.text)
			if bs.is_empty():
				_fail("a choice with no button to press")
			elif wanted.is_empty():
				(bs[rng.randi() % bs.size()] as Button).pressed.emit()
	else:
		_box_t = 0.0
	# Leaving and coming back.
	if main.mode == "academy" and not hud.screen.visible and _t >= _next_break and _breaks < 6:
		_break()
	# Is anything moving?
	var sig := _signature()
	if sig != _sig:
		_sig = sig
		_sig_t = _t
	elif _t - _sig_t > STALL:
		_fail("nothing has moved for %d seconds" % int(STALL))
		_end_character(false)
		return
	if _t > LIMIT:
		_fail("not through in %d minutes" % int(LIMIT / 60.0))
		_end_character(false)
		return

func _press_screen() -> void:
	var hud: Hud = main.hud
	var bs := _buttons(hud.screen)
	if bs.is_empty():
		_fail("a screen with no button on it")
		return
	var texts: Array = bs.map(func(b): return b.text)
	if main.mode == "menu":
		var saved := Settings.hero()
		if saved.get("settled", false):
			_end_character(true)
			return
		for b in bs:
			if (b as Button).text.begins_with("Continue as"):
				(b as Button).pressed.emit()
				return
		_fail("the title has no Continue for a character in mid-term: %s" % str(texts))
		_end_character(false)
		return
	var pick: Button = bs[0]
	var adv: Dictionary = Data.academy.get("advanced", {}).get("offer", {})
	if texts.has(adv.get("short", "Advanced standing")) and who["advanced"]:
		pick = bs[texts.find(adv.get("short", "Advanced standing"))]
	if get_tree().paused:
		for b in bs:
			if (b as Button).text.begins_with("Leave by the line"):
				pick = b
	pick.pressed.emit()

## Leave and come back: by the pause menu and "Continue" (the term saved), or the game closed
## without warning and opened again (whatever was last saved).
func _break() -> void:
	var a: Academy = main.academy
	_breaks += 1
	_next_break = _t + rng.randf_range(90.0, 420.0)
	if rng.randf() < 0.5:
		if a.busy():
			_next_break = _t + 3.0
			_breaks -= 1
			return
		if args.has("debug"):
			print("SOAK   leaves by the pause menu at %s" % _where())
		a.pause()
	else:
		if args.has("debug"):
			print("SOAK   the game is closed without warning at %s" % _where())
		Settings.use_file(SAVE)   # what is on the disk, not what is in the hand
		_new_main()
		main.academy.auto_want = String(who["then"])
		if who["troubles"]:
			main._args["troubles"] = true
	_sig_t = _t

## The words on the screen: nothing a player reads may have a token left in it.
func _read_words() -> void:
	var hud: Hud = main.hud
	var a: Academy = main.academy
	var texts: Array = [hud.prompt_title.text, hud.prompt_text.text, hud.prompt_note.text, hud.objective_title.text, hud.pattern_banner.text]
	if main.mode == "academy":
		texts.append_array([a._text.text, a._speaker.text, a._speaker_sub.text, a._objective.text, a._prompt_label.text, a._place_card.text, a._big.text, a._big_sub.text])
		for box in [a._choice_box, a._reading_box]:
			if box and is_instance_valid(box):
				_gather(box, texts)
	if hud.screen.visible:
		_gather(hud.screen, texts)
	for t in texts:
		var s := String(t)
		if s == "" or _seen.has(s):
			continue
		_seen[s] = true
		var bad := _token_in(s)
		if bad != "":
			_fail("words with %s left in them: \"%s\"" % [bad, s.substr(0, 160)])

static func _gather(n: Node, into: Array) -> void:
	for c in n.get_children():
		if c is Label or c is RichTextLabel or c is Button:
			into.append(c.text)
		_gather(c, into)

static var _re_token: RegEx = null
static func _token_in(s: String) -> String:
	if _re_token == null:
		_re_token = RegEx.new()
		_re_token.compile("\\{[A-Za-z_][A-Za-z0-9_]*\\}|\\$[A-Za-z_]+|<null>|%[sd]|\\bNull\\b|\\bnan\\b")
	var m := _re_token.search(s)
	return m.get_string() if m else ""

## Every lesson step this character met, with how long it took (the slow ones are worth a look).
var _step_key := ""
var _step_t0 := 0.0
func _watch_steps() -> void:
	if main.mode != "academy":
		return
	var a: Academy = main.academy
	var key := ""
	if a.in_lesson() and a._step >= 0 and a._step < a._lesson["steps"].size() and not (a._lesson.get("quest", false) or a._lesson.get("trouble", false)):
		key = "%s/%s" % [a._lesson["id"], a._lesson["steps"][a._step]["title"]]
	if key != _step_key:
		if _step_key != "":
			_steps_seen[_step_key] = maxf(float(_steps_seen.get(_step_key, 0.0)), _t - _step_t0)
		_step_key = key
		_step_t0 = _t

func _end_character(through: bool) -> void:
	_state = "idle"
	var h := Settings.hero()
	var line := ""
	if through:
		# What the Academy promises a character who leaves by the Gate.
		var g := Genius.for_hero(h) if h.has("genius") else null
		var rec: Dictionary = h.get("academy", {}).get("record", {})
		if g == null or not g.is_born():
			_fail("left with no genius born")
		elif g.instar < 2:
			_fail("left without a Second Form (the genius is at %s)" % g.instar_name())
		elif g.name == "":
			_fail("left with a genius that has no name")
		if int(h.get("stage", 2)) < 3:
			_fail("left at Stage %d, not 3" % int(h.get("stage", 2)))
		if h.get("techniques", []).size() < 3:
			_fail("left with %d school techniques in the hand, not 3" % h.get("techniques", []).size())
		if int(h.get("marks", 0)) <= 0 or int(rec.get("marks", 0)) <= 0:
			_fail("left with no Marks")
		if h.get("archetypes", []).is_empty():
			_fail("left with no archetype")
		for l in ["hold", "rite", "shape", "discipline", "line", "project", "gate"]:
			if not h.get("academy", {}).get("done", []).has(l) and not (h.get("advanced", false) and l in ["hold", "shape", "discipline", "line"]):
				_fail("left without %s done" % l)
		if not h.get("advanced", false) and who["then"] != h.get("weapon", ""):
			_fail("chose %s at the Discipline lesson and carries %s" % [who["then"], h.get("weapon", "")])
		if g and g.is_born():
			line = "Stage %d, %d Marks, %s the %s (%s), techniques %s, %d postings, %d troubles, carried out %d" % [int(h.get("stage", 2)), int(h.get("marks", 0)), g.name, g.form_name(), g.instar_name(),
				",".join(h.get("techniques", [])), int(rec.get("quests", 0)), int(rec.get("troubles", 0)), int(rec.get("rescued", 0))]
	var ok := through and _fails.is_empty()
	var wall := (Time.get_ticks_msec() - _wall0) / 1000.0
	print("SOAK %02d  %s  in %.1f game minutes (%.0f s), left and came back %d times.  %s" % [at, "THROUGH" if ok else ("THROUGH, WITH FAILURES" if through else "STOPPED"), _t / 60.0, wall, _breaks, line])
	if args.has("steps"):
		var slow: Array = _steps_seen.keys().map(func(k): return "%s %.0fs" % [k, _steps_seen[k]])
		print("SOAK     steps: %s" % ", ".join(slow))
	_results.append({ "n": at, "who": _who_line(who), "through": through, "fails": _fails.duplicate(), "minutes": _t / 60.0 })
	# The next one starts in the same session (a second character), unless this one broke it.
	if not through or get_tree().paused:
		_new_main()
	call_deferred("_next_character")

func _finish() -> void:
	var through := _results.filter(func(r): return r["through"]).size()
	var clean := _results.filter(func(r): return r["through"] and r["fails"].is_empty()).size()
	print("")
	for r in _results:
		if not r["fails"].is_empty():
			print("SOAK FAILED %02d %s" % [r["n"], r["who"]])
			for f in r["fails"]:
				print("    - %s" % f)
	print("SOAK: %d characters, %d reached Commencement, %d of them with nothing wrong; %d failed" % [_results.size(), through, clean, _results.size() - clean])
	get_tree().quit(0 if clean == _results.size() else 1)
