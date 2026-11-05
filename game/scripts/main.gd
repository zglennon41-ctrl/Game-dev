## WILDLINE: the title, the character creator, the night the field wakes, the recruiter, the year,
## the Academy's gate; and the practice yard and the combat tutorial.
## Command-line extras for automated checks (after --): --bot plays well; --tutorial / --fight
## start straight in; --shots=DIR saves screenshots every --every seconds; --session=S shortens
## the fight; --quit quits at the results.
extends Node3D

var world := World.new()
var hud := Hud.new()
var sfx := Sfx.new()
var builder := Builder.new()
var creator := Creator.new()
var prologue: Prologue
var hero: Dictionary = {}
var preview: Fight
var _breached := false
var fight: Fight
var tutorial: Tutorial
var mode := "menu"   # menu, creator, prologue, story, tutorial, fight, results
var fight_end := 0.0
var _cam_mouse := Vector2.ZERO
var _last_ticks := 0

var _args := {}
var _shot_n := 0
var _next_shot := 0.0
var _bot_move := Vector2.ZERO

const ACTIONS := {
	"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT], "move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
	"attack": [KEY_J], "block": [KEY_K], "dodge": [KEY_SPACE, KEY_SHIFT], "technique": [KEY_Q, KEY_1],
	"stance": [KEY_F, KEY_L], "pattern": [KEY_R], "name_foe": [KEY_N], "lock_on": [KEY_TAB], "menu": [KEY_ESCAPE],
}
const MOUSE := { "attack": MOUSE_BUTTON_LEFT, "block": MOUSE_BUTTON_RIGHT, "lock_on": MOUSE_BUTTON_MIDDLE }
const PAD := { "attack": JOY_BUTTON_X, "block": JOY_BUTTON_RIGHT_SHOULDER, "dodge": JOY_BUTTON_A, "technique": JOY_BUTTON_Y,
	"stance": JOY_BUTTON_LEFT_SHOULDER, "pattern": JOY_BUTTON_B, "lock_on": JOY_BUTTON_RIGHT_STICK, "menu": JOY_BUTTON_START, "name_foe": JOY_BUTTON_DPAD_UP }

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		var kv := String(a).trim_prefix("--").split("=", true, 1)
		_args[kv[0]] = kv[1] if kv.size() > 1 else true
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_input()
	add_child(world)
	add_child(hud)
	add_child(sfx)
	add_child(builder)
	builder.visible = false
	add_child(creator)
	creator.visible = false
	creator.changed.connect(_preview_hero)
	creator.finished.connect(_hero_made)
	creator.cancelled.connect(func(): creator.visible = false; menu())
	builder.done.connect(_pattern_built)
	builder.cancelled.connect(func(): builder.visible = false; menu())
	_last_ticks = Time.get_ticks_usec()
	if _args.has("shots"):
		DirAccess.make_dir_recursive_absolute(_args["shots"])
	if _args.has("builder"):
		menu()
		_open_builder()
		if _args.has("shots"):
			await get_tree().create_timer(0.5).timeout
			builder.spec["terms"] = ["after-perfect-hold", "half-health", "never-twice-one-foe"]
			builder.spec["sworn"] = true
			builder._refresh()
			await get_tree().create_timer(0.3).timeout
			_shot("builder")
			await get_tree().create_timer(0.5).timeout
			get_tree().quit()
		return
	if _args.has("reveal"):
		var ra: Array = Array(String(_args["reveal"]).split(",")).map(func(x): return int(x))
		new_character()
		creator.answers = ra
		creator._reveal()
		await get_tree().create_timer(1.2).timeout
		_shot("reveal")
		await get_tree().create_timer(0.3).timeout
		creator._choose_blood()
		await get_tree().create_timer(0.4).timeout
		_shot("bloods")
		await get_tree().create_timer(0.3).timeout
		creator._ask(2)
		await get_tree().create_timer(0.4).timeout
		_shot("question")
		await get_tree().create_timer(0.3).timeout
		get_tree().quit()
		return
	if _args.has("answers"):
		# Automated checks: answer the questions from the command line, then play the opening.
		var ans: Array = Array(String(_args["answers"]).split(",")).map(func(x): return int(x))
		var h := Creation.generate(ans)
		h["name"] = "Test"
		_hero_made(h)
		return
	if _args.has("new"):
		new_character()
	elif _args.has("tutorial"):
		start("tutorial")
	elif _args.has("fight"):
		start("fight")
	else:
		menu()

func _setup_input() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.25)
		for k in ACTIONS[action]:
			var e := InputEventKey.new()
			e.physical_keycode = k
			InputMap.action_add_event(action, e)
		if MOUSE.has(action):
			var m := InputEventMouseButton.new()
			m.button_index = MOUSE[action]
			InputMap.action_add_event(action, m)
		if PAD.has(action):
			var j := InputEventJoypadButton.new()
			j.button_index = PAD[action]
			InputMap.action_add_event(action, j)
	for pair in [["move_left", JOY_AXIS_LEFT_X, -1.0], ["move_right", JOY_AXIS_LEFT_X, 1.0], ["move_up", JOY_AXIS_LEFT_Y, -1.0], ["move_down", JOY_AXIS_LEFT_Y, 1.0]]:
		var m := InputEventJoypadMotion.new()
		m.axis = pair[1]
		m.axis_value = pair[2]
		InputMap.action_add_event(pair[0], m)

# --- Screens ----------------------------------------------------------------

func menu() -> void:
	mode = "menu"
	Engine.time_scale = 1.0
	sfx.stop_ambience()
	creator.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var saved := Settings.hero()
	var buttons: Array = [["New character", new_character]]
	var body := "A real-time party RPG of a guild that keeps a rail junction alive, ten thousand years after the Awakening.\n\nMouse and keyboard, or a gamepad. Sound on."
	if not saved.is_empty():
		buttons.append(["Continue as %s  (%s, %s)" % [saved["name"], Data.by_id(Data.bloods, saved["blood"])["name"], String(saved["shape"]).capitalize()], _academy_gate])
		buttons.append(["Practice yard: fight cut-wolves as %s  (two minutes)" % saved["name"], func(): hero = saved; start("fight")])
	buttons.append(["Combat tutorial  (as an Anchor)", func(): hero = {}; start("tutorial")])
	buttons.append(["Quit", func(): get_tree().quit()])
	hud.show_screen("WILDLINE", "The Cumberland Cut", body, buttons)

# --- The opening ---------------------------------------------------------------

func new_character() -> void:
	mode = "creator"
	hud.hide_screen()
	hud.play_ui.visible = false
	sfx.start_ambience()
	preview = null
	creator.begin()

## The reveal changed: dress the character standing in the chamber.
func _preview_hero(h: Dictionary) -> void:
	world.build_hero(h)
	preview = Fight.new({ "hero": h, "passive": true, "respawn": false })
	preview.w_state = "absent"
	preview.p_pos = Vector2.ZERO
	preview.p_facing = PI / 2.0
	world.show_wolf = false
	world.portrait = true

func _hero_made(h: Dictionary) -> void:
	hero = h
	Settings.save_hero(h)
	creator.visible = false
	world.portrait = false
	_card(Data.story["cards"]["open"], _start_prologue)

## A title card: a few lines on black, and Continue.
func _card(lines: Array, next: Callable) -> void:
	mode = "story"
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var filled: Array = lines.map(func(l): return Prologue.fill(l, hero))
	hud.show_screen(filled[0], "\n".join(filled.slice(1)), "", [["Continue", next]])
	if _args.has("answers"):
		_shot.call_deferred("card")
		next.call_deferred()

func _start_prologue() -> void:
	fight = Fight.new({ "hero": hero, "beast": "cut-wolf", "seed": randi(), "respawn": false, "mercy": true,
		"allow_breach": false, "beast_health": 220 })
	world.build_hero(hero)
	world.reset_feedback()
	world.snap_camera(fight)
	hud.hide_screen()
	hud.configure(fight, hero["name"])
	sfx.start_ambience()
	mode = "prologue"
	tutorial = null
	_next_shot = 0.0
	if not _args.has("bot"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	prologue = Prologue.new(fight, world, hero)
	prologue.finished.connect(_recruiter)
	prologue.start(hud)

func _recruiter() -> void:
	mode = "story"
	Engine.time_scale = 1.0
	sfx.play("done")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var r: Dictionary = Data.story["recruiter"]
	var b: Dictionary = Data.by_id(Data.bloods, hero["blood"])
	var lines: Array = []
	for l in Data.story["recruiter_lines"]:
		var line: String = String(l).replace("{blood_line}", Data.story["blood_lines"][b["tier"]])
		lines.append(Prologue.fill(line, hero))
	hud.show_screen(String(r["name"]).to_upper(), r["title"], "\n\n".join(lines), [["Go with her", func(): _card(Data.story["cards"]["skip"], func(): _card(Data.story["cards"]["act1"], _academy_gate))]])
	if _args.has("answers"):
		_shot.call_deferred("recruiter")
		await get_tree().create_timer(0.6, true, false, true).timeout
		_card(Data.story["cards"]["skip"], func(): _card(Data.story["cards"]["act1"], _academy_gate))

func _academy_gate() -> void:
	mode = "story"
	if hero.is_empty():
		hero = Settings.hero()
	var a: Dictionary = Data.story["academy"]
	hud.show_screen(a["title"], "%s  ·  %s  ·  %s" % [hero["name"], Data.by_id(Data.bloods, hero["blood"])["name"], String(hero["shape"]).capitalize()], a["text"], [
		["Practice yard: fight cut-wolves  (two minutes)", func(): start("fight")],
		["Main menu", menu],
	])
	if _args.has("answers"):
		print("REACHED THE ACADEMY: %s, %s %s with a %s; Pattern %s" % [hero["name"], hero["blood"], hero["shape"], hero["weapon"], Builder.sentence(hero["pattern"])])
		_shot.call_deferred("academy")
		if _args.has("quit"):
			get_tree().create_timer(1.0, true, false, true).timeout.connect(get_tree().quit)

func _open_builder() -> void:
	hud.screen.visible = false
	builder.open(Settings.pattern(), Settings.pattern_lost_text(), func(): Settings.restore_pattern())

func _pattern_built(spec: Dictionary) -> void:
	Settings.save_pattern(spec)
	builder.visible = false
	menu()

func start(which: String) -> void:
	# The tutorial teaches with the starting Pattern; the fight uses the one you built.
	var h: Dictionary = Fight.default_hero() if which == "tutorial" or hero.is_empty() else hero
	fight = Fight.new({ "hero": h, "beast": "yard-wolf" if which == "tutorial" else "cut-wolf", "seed": randi(),
		"passive": which == "tutorial", "respawn": true,
		"pattern_lost": false if which == "tutorial" else Settings.pattern_lost() })
	world.build_hero(h)
	hud.configure(fight, h.get("name", ""))
	_breached = false
	world.show_wolf = true
	world.reset_feedback()
	world.snap_camera(fight)
	hud.hide_screen()
	sfx.start_ambience()
	_next_shot = 0.0
	if not _args.has("bot"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	if which == "tutorial":
		mode = "tutorial"
		tutorial = Tutorial.new(fight, world)
		tutorial.finished.connect(_tutorial_done)
		tutorial.start(hud)
	else:
		mode = "fight"
		tutorial = null
		hud.set_prompt("", "")
		hud.set_prompt_status("", "")
		fight_end = float(_args.get("session", Data.room["sessionSeconds"]))

func _tutorial_done() -> void:
	sfx.play("done")
	mode = "results"
	Engine.time_scale = 1.0
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	hud.show_screen("READY", "Strike, dodge, block and parry, break, the stance, the Pattern.",
		"A cut-wolf is coming out of the Cut. It circles, it commits, and it does not wait for you. Read its wind-up. Punish the opening. Parry, and answer with the Pattern.", [
		["Fight it  (two minutes)", func(): start("fight")],
		["The tutorial again", func(): start("tutorial")],
		["Menu", menu],
	])
	if _args.has("bot"):
		_shot("tutorial-done")
		start.call_deferred("fight")

func _results(reason: String) -> void:
	sfx.play("done")
	mode = "results"
	Engine.time_scale = 1.0
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var s := fight.stats
	var sub := "The wolf put you on the stones. On the line, your party would have sixty seconds to stand you up." if reason == "down" else "%d cut-%s felled." % [s["wolves_down"], "wolf" if s["wolves_down"] == 1 else "wolves"]
	var body := ""
	if _breached:
		body += "[color=#e65a4d]You broke a Term. %s[/color]\n\n" % Settings.pattern_lost_text()
	body += "[table=2]"
	for row in [["Damage dealt", str(int(s["damage_dealt"]))], ["Parries / blocks / bitten / evaded", "%d / %d / %d / %d" % [s["parries"], s["blocks"], s["hurts"], s["evades"]]],
			["Breaks into stagger", str(s["staggers"])], ["Patterns landed / fizzled", "%d / %d" % [s["patterns"] - s["pattern_fizzles"], s["pattern_fizzles"]]],
			["Longest run of hits", str(s["longest_combo"])], ["Health left", str(roundi(fight.p_hp))]]:
		body += "[cell][color=#9e958a]%s[/color]        [/cell][cell]%s[/cell]" % row
	body += "[/table]"
	hud.show_screen("DOWN" if reason == "down" else "TIME", sub, body, [
		["Again", func(): start("fight")],
		["Tutorial", func(): start("tutorial")],
		["Menu", menu],
	])
	print("RESULTS ", JSON.stringify({ "reason": reason, "wolves": s["wolves_down"], "hits": s["hits"], "parries": s["parries"], "hurts": s["hurts"], "staggers": s["staggers"], "patterns": s["patterns"], "fizzles": s["pattern_fizzles"], "hp": fight.p_hp }))
	if _args.has("shots"):
		_shot.call_deferred("results")
	if _args.has("quit"):
		get_tree().create_timer(1.0, true, false, true).timeout.connect(get_tree().quit)

# --- Input ------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_cam_mouse += event.relative
	if mode != "tutorial" and mode != "fight" and mode != "prologue":
		return
	if event.is_action_pressed("menu"):
		menu()
		return
	if event is InputEventMouseButton and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not _args.has("bot"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		return
	if event.is_action_pressed("lock_on"):
		fight.input("lock")
		world.lock_on = fight.p_lock
	for pair in [["attack", "attack"], ["technique", "technique"], ["dodge", "dodge"], ["stance", "stance"], ["pattern", "pattern"], ["block", "block-down"], ["name_foe", "name"]]:
		if event.is_action_pressed(pair[0], false, true):
			fight.input(pair[1])
	if event.is_action_released("block", true):
		fight.input("block-up")

# --- Each frame -------------------------------------------------------------

func _process(delta: float) -> void:
	var t := Time.get_ticks_usec()
	var real_dt := minf(0.1, (t - _last_ticks) / 1e6)
	_last_ticks = t
	if mode == "creator" and preview:
		world.draw(preview, real_dt, Vector2.ZERO, Vector2.ZERO)
		return
	if mode != "tutorial" and mode != "fight" and mode != "prologue":
		return
	var stick := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var move := world.move_from_stick(stick)
	if _args.has("bot"):
		move = _bot()
	fight.update(minf(delta, 0.1), move)
	var events := fight.drain()
	for e in events:
		if e["type"] == "breach" and mode == "fight":
			_breached = true
			Settings.lose_pattern(e["sworn"])
	_sounds(events)
	world.feedback(fight, events)
	if tutorial:
		tutorial.update(events, hud)
	if mode == "prologue" and prologue:
		prologue.update(events, real_dt, hud)
		if _args.has("debug"):
			for e in events:
				if e["type"] not in ["anim"]:
					print("%.2f beat %d  %s  wolf %s %s hp %d" % [fight.now, prologue.beat, e["type"], fight.w_state, str(fight.w_pos), fight.w_hp])
	var cam := Vector2(Input.get_joy_axis(0, JOY_AXIS_RIGHT_X), Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y))
	if cam.length() < 0.15:
		cam = Vector2.ZERO
	if not fight.p_lock:
		world.look(_cam_mouse)
	_cam_mouse = Vector2.ZERO
	world.draw(fight, real_dt, cam, move)
	var timer := ""
	var score := "the old station" if mode == "prologue" else "the yard"
	if mode == "fight":
		var left := maxf(0.0, fight_end - fight.now)
		timer = "%d:%02d" % [int(left) / 60, int(left) % 60]
		score = "wolves felled: %d" % fight.stats["wolves_down"]
	hud.update_play(fight, timer, score, world.show_wolf)
	if _args.has("shots") and fight.now > _next_shot:
		_next_shot = fight.now + float(_args.get("every", "5"))
		_shot(mode)
	if mode == "fight":
		if fight.p_state == "down":
			_results.call_deferred("down")
			mode = "results"
		elif fight.now >= fight_end:
			_results("time")

func _sounds(events: Array) -> void:
	for e in events:
		match e["type"]:
			"anim":
				if e["who"] == "player" and String(e["name"]).contains("Attack"):
					sfx.play("swish", 1.1)
				if e["who"] == "wolf" and e["name"] == "Attack":
					sfx.play("bark", 0.9)
			"hit":
				if e["heavy"] or e["pattern"]: sfx.play("heavy")
				sfx.play("hit", 1.0 + 0.08 * int(e.get("combo", 0)))
			"parry": sfx.play("parry")
			"block": sfx.play("block")
			"hurt": sfx.play("hurt")
			"dodge": sfx.play("dodge")
			"windup": sfx.play("growl", 1.3 if e["attack"] == "snap" else 1.0)
			"stagger": sfx.play("stagger")
			"stance": sfx.play("stance", 1.0 if e["on"] else 0.75)
			"wolf-down": sfx.play("fell")
			"no-will", "not-ready", "pattern-locked": sfx.play("deny")
			"pattern-start": sfx.play("pattern")
			"pattern-cue": sfx.play("cue-hit" if e["hit"] else "fizzle")
			"pattern-done": sfx.play("heavy", 0.7)
			"pattern-fizzle": sfx.play("fizzle", 0.8)
			"named": sfx.play("stance", 1.4)
			"bar-warning": sfx.play("deny", 0.7)
			"breach": sfx.play("stagger", 0.6)
			"turned": sfx.play("block", 1.3)
			"mend": sfx.play("cue-hit", 0.8)
			"pattern-lost", "stance-locked": sfx.play("deny")

func _shot(label: String) -> void:
	if not _args.has("shots"):
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	_shot_n += 1
	img.save_png("%s/%02d-%s.png" % [_args["shots"], _shot_n, label])

# --- The bot: plays well, for automated checks --------------------------------

func _bot() -> Vector2:
	var f := fight
	if mode == "prologue" and prologue and prologue.beat < Data.story["beats"].size():
		var bid: String = Data.story["beats"][prologue.beat]["id"]
		if bid == "pattern":
			var terms: Array = f.pattern["terms"]
			if ("named-aloud" in terms or "never-silence" in terms) and not f.w_named:
				f.input("name")
			if ("struck-first" in terms and not f.p_struck_this_foe) or ("below-half" in terms and f.p_hp >= 50):
				# Let it bite: no guard, no dodging.
				if f.p_block_held:
					f.input("block-up")
				if f.pattern_ready():
					f.input("pattern")
				return (f.w_pos - f.p_pos).normalized() if (f.w_pos - f.p_pos).length() > 2.0 else Vector2.ZERO
		if bid == "technique" and f.p_state == "free":
			f.input("technique")
	var to_w := f.w_pos - f.p_pos
	var step := tutorial.i if tutorial else 99
	var move := Vector2.ZERO
	if f.w_state == "windup" and f.w_duration - f.w_timer <= 0.12 and not f.p_block_held:
		f.input("block-down")
	elif f.p_block_held and f.w_state != "windup":
		f.input("block-up")
	if f.pattern_ready():
		f.input("pattern")
	if f.p_state == "pattern" and not f.chain.is_empty():
		var c: float = f.chain["cues"][f.chain["next"]]
		if absf(f.now - c) < 0.03:
			f.input("attack")
		return Vector2.ZERO
	match step:
		2:
			if f.p_state == "free" and randf() < 0.03:
				f.input("dodge")
			return Vector2(0, 1) if f.p_state == "free" else Vector2.ZERO
		5:
			if randf() < 0.02:
				f.input("stance")
	var punish := f.w_state in ["recover", "stagger", "flinch", "idle"] and (f.w_state != "recover" or f.w_duration - f.w_timer > 0.45)
	if to_w.length() < 2.3 and punish and f.p_state in ["free", "attack"]:
		if (step == 4 or step == 99) and f.p_will > 40 and f.now >= float(f.p_cooldowns.get(f.tech["id"], 0.0)):
			f.input("technique")
		elif step != 4:
			f.input("attack")
	if to_w.length() > 2.0 and f.w_state != "windup":
		move = to_w.normalized()
	return move
