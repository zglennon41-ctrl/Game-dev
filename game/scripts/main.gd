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
var music := Music.new()
var creator := Creator.new()
var academy := Academy.new()
var page := GeniusPage.new()
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
	"attack": [KEY_J], "block": [KEY_K], "dodge": [KEY_SPACE, KEY_SHIFT], "technique": [KEY_Q], "tech1": [KEY_1], "tech2": [KEY_2], "tech3": [KEY_3],
	"stance": [KEY_F, KEY_L], "pattern": [KEY_R], "name_foe": [KEY_N], "lock_on": [KEY_TAB], "menu": [KEY_ESCAPE], "interact": [KEY_E], "order": [KEY_G], "genius_page": [KEY_J], "show_step": [KEY_H], "reload": [KEY_X],
}
const MOUSE := { "attack": MOUSE_BUTTON_LEFT, "block": MOUSE_BUTTON_RIGHT, "lock_on": MOUSE_BUTTON_MIDDLE }
const PAD := { "attack": JOY_BUTTON_X, "block": JOY_BUTTON_RIGHT_SHOULDER, "dodge": JOY_BUTTON_A, "technique": JOY_BUTTON_Y,
	"stance": JOY_BUTTON_LEFT_SHOULDER, "pattern": JOY_BUTTON_B, "lock_on": JOY_BUTTON_RIGHT_STICK, "menu": JOY_BUTTON_START, "name_foe": JOY_BUTTON_DPAD_UP, "interact": JOY_BUTTON_X, "order": JOY_BUTTON_DPAD_LEFT, "genius_page": JOY_BUTTON_BACK }

func _ready() -> void:
	Style.apply_global()
	for a in OS.get_cmdline_user_args():
		var kv := String(a).trim_prefix("--").split("=", true, 1)
		_args[kv[0]] = kv[1] if kv.size() > 1 else true
	process_mode = Node.PROCESS_MODE_ALWAYS
	if _args.has("bases"):
		# --bases=res://game/tests/fixtures/bases: more bases beside the game's own, to look at
		# the tree's screens with (a turning needs a second base).
		Data.use_bases(Data.load_bases() + Data.load_bases(str(_args["bases"])))
	_setup_input()
	add_child(world)
	add_child(hud)
	add_child(sfx)
	add_child(builder)
	builder.visible = false
	add_child(creator)
	creator.visible = false
	academy.world = world
	academy.hud = hud
	academy.sfx = sfx
	add_child(academy)
	academy.visible = false
	academy.leave.connect(func(): academy.save(); menu())
	academy.open_builder.connect(func(pat: Dictionary):
		hud.screen.visible = false
		builder.open(pat, "", func(): pass))
	add_child(page)
	page.closed.connect(func(): if mode == "academy" and not _args.has("bot"): Input.mouse_mode = Input.MOUSE_MODE_CAPTURED)
	creator.changed.connect(_preview_hero)
	creator.look_changed.connect(func(h: Dictionary): world.redress(h))
	creator.cleared.connect(func(): world.show_figure(false))
	creator.framed.connect(func(kind: String): world.portrait_frame = kind)
	creator.shifted.connect(func(part: float): world.portrait_shift = part)
	creator.turned.connect(func(by: float): if preview: preview.p_facing += by)
	creator.field.connect(func(col: Color, k: float, flare: float): world.stage_field(col, k, flare))
	creator.finished.connect(_hero_made)
	creator.cancelled.connect(func(): creator.visible = false; menu())
	creator.clicked.connect(func(): sfx.play("ui-take", 1.0, -6.0))
	# A soft tick whenever the chosen button moves, by mouse or pad.
	get_viewport().gui_focus_changed.connect(func(c: Control): if c is Button: sfx.play("ui-move", 1.0, -10.0))
	add_child(music)
	builder.done.connect(_pattern_built)
	builder.cancelled.connect(func():
		builder.visible = false
		if mode == "academy":
			if not _args.has("bot"):
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		else:
			menu())
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
		# --look=hair:long,beard:full,hair_color:red,headgear:0 dresses the revealed character.
		if _args.has("look"):
			for kv in String(_args["look"]).split(","):
				var parts := kv.split(":")
				if parts.size() == 2 and parts[0] == "blood":
					creator.blood_choice = parts[1]
				elif parts.size() == 2:
					creator.hero["look"][parts[0]] = (parts[1] == "1") if parts[0] in ["headgear", "cape"] else (float(parts[1]) if parts[0] in ["stature", "build"] else parts[1])
			creator._reveal()
			world.redress(creator.hero)
		# --turn=DEGREES turns the figure; every leaf of the reveal is shot in its own framing.
		if _args.has("turn"):
			preview.p_facing += deg_to_rad(float(_args["turn"]))
		await get_tree().create_timer(1.6).timeout
		await _shot("reveal")
		for leaf in ["body", "face", "dress"]:
			creator._set_tab(leaf)
			await get_tree().create_timer(1.3).timeout
			await _shot("reveal-" + leaf)
		creator._set_tab("reading")
		creator._set_frame("half")
		await get_tree().create_timer(1.3).timeout
		await _shot("reveal-close")
		if _args.has("leaves"):
			get_tree().quit()
			return
		await get_tree().create_timer(0.3).timeout
		creator._choose_blood()
		await get_tree().create_timer(0.4).timeout
		await _shot("bloods")
		await get_tree().create_timer(0.3).timeout
		creator._intro()
		await get_tree().create_timer(1.6).timeout
		await _shot("intro")
		creator.answers = ra.slice(0, 2)
		creator._ask(2)
		await get_tree().create_timer(1.4).timeout
		await _shot("question")
		creator.answers = ra.slice(0, 9)
		creator._ask(9)
		await get_tree().create_timer(1.4).timeout
		await _shot("question-last")
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
	if _args.has("page"):
		var ph := Settings.hero()
		if ph.is_empty() or not ph.has("genius") or _args.has("fresh"):
			# no saved character: one made here, its genius settled, to look at the page with.
			# --page=<form id> (a base's, or a hybrid's: wolf+hawk:wolf-courser) stands it at that form.
			ph = Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
			ph["name"] = "Test"
			var pff := Rite.first_form(ph, ph["shape"], 11)
			var pg := Rite.birth(ph, pff["reading"], pff["name"])
			var want := Data.form(str(_args["page"]))
			if not want.is_empty():
				var steps: Array = []
				var wf := want
				while not wf.is_empty() and int(wf["level"]) >= 1:
					steps.push_front(wf)
					wf = Data.form(String(wf["parent"])) if String(wf["parent"]) != "" else {}
				for st in steps:
					pg.pending_reading = { "instar": int(st["level"]), "candidates": [GeniusReading._candidate(st, 0.0, [], String(pg.body.get("seedMark", "")), [], [])], "unlockedBy": "gate" }
					pg.take(0)
				pg.history = pg.history.slice(1) if not steps.is_empty() else pg.history
				pg.name = String(steps[0]["name"]) if not steps.is_empty() else pg.name
			for i in 22: pg.hit_at(1.5)
			for i in 9: pg.hit_at(6.0)
			for i in 14: pg.gave_order("hunt")
			for i in 6: pg.gave_order("guard")
			for i in 8: pg.met_blow("parries")
			for i in 5: pg.met_blow("dodges")
			for i in 4: pg.ran("wild", false, 2)
			pg.ran("ruin", true, 0)
			pg.save_to(ph)
		menu()
		page.open(Genius.for_hero(ph), World.SHAPE_COLORS.get(ph.get("shape", "anchor"), Color.WHITE), 0, int(ph.get("academy", {}).get("record", {}).get("marks", 0)))
		if _args.has("shots"):
			await get_tree().create_timer(1.5).timeout
			_shot("page")
			get_tree().quit()
		return
	if _args.has("lineage"):
		_lineage(str(_args["lineage"]))
		return
	if _args.has("sheet"):
		_sheet(str(_args["sheet"]))
		return
	if _args.has("gallery"):
		# The genius tree, assembled: a check of the bodies.
		#   --gallery=wolf        one base's whole tree: the settled form, its three paths, the
		#                         nine prongs, and the eighteen finishes in two rows
		#   --gallery=wolf+hawk   a hybrid's
		#   --gallery             every base, a row each: its settled form, and down each path
		#                         the path, its first prong and that prong's first finish
		#   --gallery=animal      the same for the bases of one class (animal, monster,
		#                         creature, item, weapon, armor)
		#   --gallery=everything  every base's whole tree, a row each
		mode = "gallery"
		hud.hide_screen()
		hud.play_ui.visible = false
		world.show_wolf = false
		world.genius_visible = false
		world._player.visible = false
		var only: String = str(_args.get("gallery", ""))
		var grid: Array = []      # rows of forms
		if only != "" and only != "true" and not Data.tree_of(only).is_empty():
			var tree := Data.tree_of(only)
			for lv in [1, 2, 3]:
				grid.append(tree.filter(func(f): return int(f["level"]) == lv))
			var fins: Array = tree.filter(func(f): return int(f["level"]) == 4)
			grid.append(fins.slice(0, 9))
			grid.append(fins.slice(9))
		else:
			for b in Data.bases():
				if only == "everything":
					grid.append(Data.tree_of(String(b["id"])))
				elif only in ["", "true"] or only == String(b["class"]):
					var row: Array = [Data.form(String(b["settled"]["id"]))]
					for k in 3:
						row.append_array(Genius.road_of(String(b["id"]), [k, 0, 0]).slice(1))
					grid.append(row)
		var rows := grid.size()
		var widest := 1
		for r in grid:
			widest = maxi(widest, (r as Array).size())
		var step := 2.4 if widest <= 18 else 1.7
		for ri in rows:
			var line: Array = grid[ri]
			for i in line.size():
				var f: Dictionary = line[i]
				var col: Color = World.SHAPE_COLORS.values()[ri % 6]
				var info := { "form": f["id"], "silhouette": f["silhouette"], "expression": f["expression"], "features": f["features"], "instar": int(f["level"]), "look": GeniusLook.born(4711 + ri) }
				var b := world.make_form(info, col)
				world.add_child(b)
				b.position = Vector3((i - line.size() / 2.0 + 0.5) * step, 0, (ri - (rows - 1) / 2.0) * 2.8)
				b.rotation.y = 0.5
				var l := Label3D.new()
				l.text = String(f["name"]).to_upper()
				l.font = Style.font("title")
				l.font_size = 30 if step > 2.0 else 22
				l.pixel_size = 0.005 if rows > 8 else 0.008
				l.outline_size = 8
				l.modulate = Style.BRASS_HI
				l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
				l.no_depth_test = true
				l.position = b.position + Vector3(0, 0.08, 0.95)
				world.add_child(l)
		rows = maxi(rows + 1, ceili(widest * step / 3.6))
		world.cine = true
		# the camera stands back far enough for every row
		world.cine_pos = Vector3(0, 2.4 + rows * 1.35, rows * 1.3 + 2.6)
		world.cine_look = Vector3(0, 0.2, 0.6)
		world._cam_pos = world.cine_pos
		world._cam_look = world.cine_look
		if _args.has("shots"):
			await get_tree().create_timer(1.5).timeout
			_shot("gallery")
			get_tree().quit()
		return
	if _args.has("academy"):
		# Automated checks: walk into the Academy with the saved hero (or a made one), fresh.
		var h := Settings.hero()
		if h.is_empty() or _args.has("fresh"):
			# Fresh: a character straight from the questionnaire, nothing of an earlier run on it.
			h = Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
			h["name"] = "Test"
			if _args.has("blood"):
				h["blood"] = String(_args["blood"])
		if _args.has("gate"):
			# The morning of the Gate: Stage 3, the term behind you, for automated checks.
			var dkg: Dictionary = Data.discipline_kits.get(h.get("discipline", "marshal"), {})
			h["techniques"] = dkg.get("techniques", []).slice(0, 3).map(func(t): return t["id"])
			h["stage"] = 3
			h["projected"] = true
			h["academy"] = { "seed": int(_args.get("seed", "4242")), "arrived": true, "done": ["hold", "rite", "shape", "discipline", "line", "project"], "met": ["c0", "c1", "c2"], "day": 7, "rested_after": "project",
				"place": "quad", "party": ["c0", "c1"], "record": { "parries": 14, "blocks": 4, "hurts": 3, "dodges": 1, "talks": 9, "spars_won": 3, "spars_lost": 0, "posts_held": 2, "runs_out": 2, "examined": true } }
			if not h.has("genius"):
				var ffg := Rite.first_form(h, h["shape"], 11)
				var gg := Rite.birth(h, ffg["reading"], ffg["name"])
				for i in 30: gg.hit_at(1.5)
				for i in 12: gg.gave_order("hold")
				for i in 9: gg.gave_order("guard")
				for i in 14: gg.used_family("%s.%s" % [h["shape"], Data.kits[h["shape"]]["technique"]["family"]])
				gg.save_to(h)
		if _args.has("project"):
			# The morning of Lesson 6: the line behind you, for automated checks.
			var dk0: Dictionary = Data.discipline_kits.get(h.get("discipline", "marshal"), {})
			h["techniques"] = dk0.get("techniques", []).slice(0, 3).map(func(t): return t["id"])
			h["stage"] = 2
			h.erase("projected")
			h["academy"] = { "seed": int(_args.get("seed", "4242")), "arrived": true, "done": ["hold", "rite", "shape", "discipline", "line"], "met": ["c0", "c1"], "day": 6, "rested_after": "line",
				"place": "yard", "party": ["c0", "c1"], "record": { "parries": 9, "blocks": 4, "hurts": 3, "dodges": 1, "talks": 6, "spars_won": 3, "spars_lost": 0, "posts_held": 1, "runs_out": 1 } }
			if not h.has("genius"):
				var ff4 := Rite.first_form(h, h["shape"], 11)
				Rite.birth(h, ff4["reading"], ff4["name"])
		if _args.has("line"):
			# The morning of Lesson 5: a genius born, a Discipline learned, for automated checks.
			var dk: Dictionary = Data.discipline_kits.get(h.get("discipline", "marshal"), {})
			h["techniques"] = dk.get("techniques", []).slice(0, 3).map(func(t): return t["id"])
			h["academy"] = { "seed": int(_args.get("seed", "4242")), "arrived": true, "done": ["hold", "rite", "shape", "discipline"], "met": ["c0", "c1"], "day": 5, "rested_after": "discipline",
				"place": "quad", "record": { "parries": 8, "blocks": 4, "hurts": 2, "dodges": 1, "talks": 5, "spars_won": 3, "spars_lost": 0 } }
			if not h.has("genius"):
				var ff3 := Rite.first_form(h, h["shape"], 11)
				Rite.birth(h, ff3["reading"], ff3["name"])
		if _args.has("board"):
			# After Lesson 3, with the board open, for automated checks of classmates' troubles.
			h["academy"] = { "seed": int(_args.get("seed", "4242")), "arrived": true, "done": ["hold", "rite", "shape"], "met": ["c0", "c1"], "day": 3, "rested_after": "rite",
				"place": "quad", "record": { "parries": 8, "blocks": 4, "hurts": 2, "dodges": 1, "talks": 3, "spars_won": 2, "spars_lost": 0 } }
			if not h.has("genius"):
				var ffb := Rite.first_form(h, h["shape"], 11)
				Rite.birth(h, ffb["reading"], ffb["name"])
		if _args.has("discipline"):
			# The morning of Lesson 4, with a genius born, for automated checks.
			h["academy"] = { "seed": int(_args.get("seed", "4242")), "arrived": true, "done": ["hold", "rite", "shape"], "met": [], "day": 4, "rested_after": "shape",
				"place": "yard", "record": { "parries": 8, "blocks": 4, "hurts": 2, "dodges": 1, "talks": 3, "spars_won": 2, "spars_lost": 0 } }
			if not h.has("genius"):
				var ff2 := Rite.first_form(h, h["shape"], 11)
				Rite.birth(h, ff2["reading"], ff2["name"])
		if _args.has("shape"):
			# Straight to the morning of Lesson 3, with a genius born, for automated checks.
			h["academy"] = { "seed": int(_args.get("seed", "4242")), "arrived": true, "done": ["hold", "rite"], "met": [], "day": 3, "rested_after": "rite",
				"place": "yard", "record": { "parries": 6, "blocks": 4, "hurts": 2, "dodges": 1, "talks": 3 } }
			if not h.has("genius"):
				var ff := Rite.first_form(h, h["shape"], 11)
				Rite.birth(h, ff["reading"], ff["name"])
		if _args.has("rite"):
			# Straight to the morning of the rite, for automated checks of it.
			h.erase("genius")
			h["academy"] = { "seed": int(_args.get("seed", "4242")), "arrived": true, "done": ["hold"], "met": [], "day": 2, "rested": true,
				"place": "hearth", "record": { "parries": 6, "blocks": 4, "hurts": 2, "dodges": 1, "talks": 3 } }
		hero = h
		enter_academy()
		if _args.has("tour"):
			# A review of the grounds: every place from above and from where a student stands.
			_tour()
			return
		if _args.has("quit"):
			get_tree().create_timer(float(_args.get("seconds", "90")), true, false, true).timeout.connect(func():
				print("ACADEMY: place %s, done %s, met %d, rested after %s, record %s" % [academy.progress["place"], str(academy.progress["done"]), academy.progress["met"].size(), str(academy.progress.get("rested_after", "")), str(academy.progress["record"])])
				get_tree().quit())
	elif _args.has("new"):
		new_character()
	elif _args.has("tutorial"):
		start("tutorial")
	elif _args.has("fight"):
		if _args.has("saved"):
			hero = Settings.hero()
		start("fight")
	else:
		menu()
		if _args.has("shots") and _args.has("title"):
			await get_tree().create_timer(2.0).timeout
			_shot("title")
			await get_tree().create_timer(0.3).timeout
			get_tree().quit()

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
	music.play_track(String(Data.music.get("places", {}).get("title", "title")) if not Data.music.is_empty() else "title")
	music.set_fight(false)
	creator.visible = false
	academy.visible = false
	world.set_place("cut")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var saved := Settings.hero()
	# The title stands over the chamber: the last hero made, in the moonlight, the genius circling.
	var h: Dictionary = saved if not saved.is_empty() else Fight.default_hero()
	world.portrait_frame = ""
	_preview_hero(h)
	world.portrait_side = -2.0
	world.portrait_dist = 5.6
	var buttons: Array = [["New character", new_character]]
	var body := "A real-time party RPG of a guild that keeps a rail junction alive.\n[color=#a59a8a][i]Mouse and keyboard, or a gamepad. Sound on.[/i][/color]"
	if not saved.is_empty():
		var where := ("settled, ready for the line" if saved.get("settled", false) else "at the Academy") if saved.has("academy") else "at the Academy's gate"
		buttons.append(["Continue as %s  (%s, %s, %s)" % [saved["name"], Data.by_id(Data.bloods, saved["blood"])["name"], String(saved["shape"]).capitalize(), where], func(): hero = saved; enter_academy() if saved.has("academy") else _academy_gate()])
		buttons.append(["Practice yard: fight cut-wolves as %s  (two minutes)" % saved["name"], func(): hero = saved; start("fight")])
	if saved.has("genius") and Genius.from_dict(saved["genius"]).is_born():
		var sg := Genius.for_hero(saved)
		buttons.append(["Your genius: %s" % (sg.name if sg.name != "" else sg.form_name()), func(): page.open(sg, World.SHAPE_COLORS.get(saved["shape"], Color.WHITE), 0, int(saved.get("academy", {}).get("record", {}).get("marks", 0)))])
	buttons.append(["Combat tutorial  (as an Anchor)", func(): hero = {}; start("tutorial")])
	buttons.append(["Quit", func(): get_tree().quit()])
	hud.show_screen("WILDLINE", "The Cumberland Cut", body, buttons, "title")

# --- The opening ---------------------------------------------------------------

func new_character() -> void:
	mode = "creator"
	hud.hide_screen()
	hud.play_ui.visible = false
	sfx.start_ambience()
	# The creator's stage: a platform on the line at night, empty until the answers are read.
	world.set_place("stage")
	world.portrait_frame = "wide"
	_preview_hero(Fight.default_hero())
	world.show_figure(false)
	world.snap_camera(preview)
	creator.begin()

## The reveal changed: build the character where it stands (the creator's stage, or the
## chamber behind the title), keeping the way it was turned.
func _preview_hero(h: Dictionary) -> void:
	var facing := preview.p_facing if (preview and mode == "creator") else PI / 2.0
	world.build_hero(h)
	preview = Fight.new({ "hero": h, "passive": true, "respawn": false })
	preview.w_state = "absent"
	preview.p_pos = world.stage_spot() if world.place == "stage" else Vector2.ZERO
	preview.p_facing = facing
	preview.p_lock = false   # standing, not aiming: a gun or a crossbow rests in the hand
	world.show_wolf = false
	world.portrait = true
	world.portrait_side = 1.25
	world.portrait_dist = 4.4
	world.show_figure(true)

func _hero_made(h: Dictionary) -> void:
	hero = h
	Settings.save_hero(h)
	creator.visible = false
	world.portrait = false
	# A second life may take advanced standing at the Academy (owner, 2026-11-06).
	if Settings.settled_count() > 0 and not _args.has("answers"):
		var adv: Dictionary = Data.academy.get("advanced", {}).get("offer", {})
		hud.show_screen(adv.get("title", "A second life"), "", adv.get("text", ""), [
			[adv.get("full", "The whole term"), func(): hero["advanced"] = false; Settings.save_hero(hero); _card(Data.story["cards"]["open"], _start_prologue)],
			[adv.get("short", "Advanced standing"), func(): hero["advanced"] = true; Settings.save_hero(hero); _card(Data.story["cards"]["open"], _start_prologue)],
		])
		return
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
	world.set_place("cut")
	world.portrait_frame = ""
	fight = Fight.new({ "hero": hero, "beast": "cut-wolf", "seed": randi(), "respawn": false, "mercy": true,
		"allow_breach": false, "beast_health": 220 })
	world.portrait = false
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
		["Walk through the Gate", enter_academy],
		["Practice yard: fight cut-wolves  (two minutes)", func(): start("fight")],
		["Main menu", menu],
	])
	if _args.has("answers"):
		print("REACHED THE ACADEMY: %s, %s %s with a %s; Pattern %s" % [hero["name"], hero["blood"], hero["shape"], hero["weapon"], Builder.sentence(hero["pattern"])])
		_shot.call_deferred("academy")
		if _args.has("quit"):
			get_tree().create_timer(1.0, true, false, true).timeout.connect(get_tree().quit)

## For looking at a Reading: count play into a genius's Tally in the proportions of some leans.
func _play_like(g: Genius, leans: Dictionary, n: int) -> void:
	for line in leans:
		for key in leans[line]:
			var k := roundi(n * float(leans[line][key]))
			match String(line):
				"range": g.count("range", String(key), k)
				"orders": g.count("orders", String(key), k)
				"shape": g.count("families", "%s.%s" % [key, Data.kits[String(key)]["technique"]["family"]], k)
				"fights": g.counter("fights." + String(key), k)
				"company": g.counter("runs." + String(key), k)
				"ground": g.count("ground", String(key), k)
				"quests": g.counter("runs.quest." + String(key), k)
				"bonds": g.bonded(String(key))
				"pattern":
					if g.tally.get("intention") is Dictionary:
						g.tally["intention"]["fires" if key == "fires" else "sworn"] = 100 if key == "fires" else true

## --sheet=<base> (or a hybrid, wolf+hawk) with --shots=DIR: every form of one tree as the game
## draws it, each alone in its own cell of a grid of eight by four, at the size of its age, on
## a plain ground and seen flat (no perspective), so that a tool can cut the picture into
## portraits. It writes sheet.json beside the picture: the ids of the forms, in order of cell.
## tools/genius-tree-page.py makes the page of the whole tree from these.
func _sheet(what: String) -> void:
	mode = "gallery"
	hud.hide_screen()
	hud.play_ui.visible = false
	world.show_wolf = false
	world.genius_visible = false
	world._player.visible = false
	var tree := Data.tree_of(what)
	if what == "baby":      # everyone's, before the rite: one body, and no tree
		tree = [{ "id": "baby", "level": 1, "silhouette": "aspect-wisps", "expression": "aspect", "features": [] }]
	if tree.is_empty():
		push_error("no such base: " + what)
		get_tree().quit(1)
		return
	const COLS := 8
	const ROWS := 4
	const HIGH := 300.0       # far above the room, where nothing else is
	const FLOOR := 0.16       # how far up its cell a form's ground is
	world._env.fog_enabled = false
	world._env.background_color = Color(0.009, 0.007, 0.0055)
	world._env.glow_bloom = 0.0
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-32, 28, 0)
	key.light_color = Color(1.0, 0.93, 0.82)
	key.light_energy = 0.36
	world.add_child(key)
	var cool := DirectionalLight3D.new()      # a faint cool light from the other side, to open the shadows
	cool.rotation_degrees = Vector3(-12, -70, 0)
	cool.light_color = Color(0.62, 0.7, 0.95)
	cool.light_energy = 0.14
	world.add_child(cool)
	var ground := StandardMaterial3D.new()
	ground.albedo_color = Color(0.2, 0.17, 0.14)
	ground.roughness = 1.0
	# one partner's genius all the way down: the colour of the Shape this base comes to most, and
	# one coat, so that what differs between two cells is the form and nothing else
	var col: Color = World.SHAPE_COLORS["anchor"]
	var called: Dictionary = Data.base(what.get_slice("+", 0)).get("calls", {}).get("shape", {})
	var most := 0.0
	for sh in called:
		if float(called[sh]) > most and World.SHAPE_COLORS.has(sh):
			most = float(called[sh])
			col = World.SHAPE_COLORS[sh]
	var look := GeniusLook.born(4711 + what.hash() % 97)
	# for a portrait, a coat of middling value: one near black hides what the body has grown
	var sil0 := String(tree[0].get("silhouette", ""))
	for k in 60:
		var tryit := GeniusLook.born(4711 + what.hash() % 97 + k * 131)
		var cols: Dictionary = GeniusLook.resolve(tryit, String(tree[0]["id"]), sil0, 3)["colors"]
		var v := 0.0
		var n := 0
		for name in cols:
			if name != "keepsake_tint" and not String(name).begins_with("mark_"):
				v += (cols[name] as Color).v
				n += 1
		if n == 0:
			break
		if v / n > 0.3 and v / n < 0.55:
			look = tryit
			break
	var ids: Array = []
	var bodies: Array = []
	for i in tree.size():
		var f: Dictionary = tree[i]
		ids.append(f["id"])
		var info := { "form": f["id"], "silhouette": f["silhouette"], "expression": f["expression"], "features": f["features"], "instar": int(f["level"]), "look": look }
		var b := world.make_form(info, col)
		world.add_child(b)
		b.rotation.y = 0.6
		bodies.append(b)
	var vp := get_viewport().get_visible_rect().size
	var shape := (vp.y / ROWS) / (vp.x / COLS)
	var pitch := deg_to_rad(10.0)
	var discs: Array = []
	var lift: Array = bodies.map(func(b): return 0.35 if (b as GeniusBody).hover else 0.0)      # how high each floats
	# stand them in cells of this width, with or without the ground under each
	var place := func(cell_w: float, grounded: bool) -> void:
		var cell_h := cell_w * shape
		for d in discs:
			d.queue_free()
		discs.clear()
		for i in bodies.size():
			var b: Node3D = bodies[i]
			var at := Vector3((i % COLS - (COLS - 1) / 2.0) * cell_w, HIGH - (i / COLS) * cell_h, 0)
			b.position = at + Vector3(0, float(lift[i]), 0)
			if grounded:
				var disc := MeshInstance3D.new()
				var dm := CylinderMesh.new()
				dm.top_radius = cell_w * 0.4
				dm.bottom_radius = cell_w * 0.4
				dm.height = cell_w * 0.015
				dm.radial_segments = 48
				disc.mesh = dm
				disc.material_override = ground
				disc.position = at - Vector3(0, dm.height / 2.0, 0)
				world.add_child(disc)
				discs.append(disc)
		var mid := Vector3(0, HIGH - (ROWS - 1) / 2.0 * cell_h + cell_h * (0.5 - FLOOR), 0)
		world.camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		world.camera.size = ROWS * cell_h * cos(pitch)
		world.camera.far = 400.0
		world.cine = true
		world.cine_pos = mid + Vector3(0, 60.0 * sin(pitch), 60.0 * cos(pitch))
		world.cine_look = mid
		world._cam_pos = world.cine_pos
		world._cam_look = world.cine_look
	# First with no ground, to measure each where it is drawn (a body's own bounds are not to
	# be trusted: skins, wings and lights all report their own). Then each is brought up to fill
	# its cell, the settled form least and the finishes most, so that a pocket astrolabe is
	# seen as near as a drake and the young still look young. True sizes are --lineage's.
	var cell := float(_args.get("cell", "5.0"))
	place.call(cell, false)
	await get_tree().create_timer(1.0).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.resize(COLS * 100, ROWS * 100, Image.INTERPOLATE_BILINEAR)
	var back := img.get_pixel(1, 1)
	var wide: Array = []      # of each, from the middle of its cell, and how tall, in hundredths of a cell
	var tall: Array = []
	var low: Array = []       # and how far above its ground its underside is
	for i in bodies.size():
		wide.append(1.0)
		tall.append(1.0)
		low.append(100.0)
	for y in img.get_height():
		for x in img.get_width():
			var n := (y / 100) * COLS + x / 100
			if n >= bodies.size():
				continue
			var c := img.get_pixel(x, y)
			if absf(c.r - back.r) + absf(c.g - back.g) + absf(c.b - back.b) < 0.12:
				continue
			var up := (1.0 - FLOOR) * 100.0 - float(y % 100)
			if up < 0.0:
				continue      # what hangs below its ground is not counted
			wide[n] = maxf(wide[n], absf(float(x % 100) + 0.5 - 50.0) + 1.0)
			tall[n] = maxf(tall[n], up + 1.0)
			low[n] = minf(low[n], up)
	const FILL := [0.56, 0.68, 0.78, 0.9]
	for i in bodies.size():
		var fill: float = FILL[clampi(int(tree[i]["level"]) - 1, 0, 3)]
		var room := (1.0 - FLOOR - 0.05) * 100.0
		if float(lift[i]) > 0.0:
			# one that floats is measured by its own height, and floats a tenth of a cell up
			var own := maxf(1.0, float(tall[i]) - float(low[i]))
			var k := fill * minf(46.0 / float(wide[i]), (room - 10.0) / own)
			var px := cell * shape / 100.0      # a hundredth of a cell's height, in metres
			lift[i] = 10.0 * px - (float(low[i]) * px - float(lift[i])) * k
			(bodies[i] as Node3D).scale *= k
		else:
			(bodies[i] as Node3D).scale *= fill * minf(46.0 / float(wide[i]), room / float(tall[i]))
	place.call(cell, true)
	if _args.has("shots"):
		await get_tree().create_timer(1.2).timeout
		await _shot("sheet")
		var out := FileAccess.open("%s/sheet.json" % _args["shots"], FileAccess.WRITE)
		out.store_string(JSON.stringify({ "base": what, "cols": COLS, "rows": ROWS, "cell": cell, "forms": ids }))
		out.close()
		get_tree().quit()

## --lineage: how a genius's progress shows (docs/genius-progression.md), on the creator's
## platform. --lineage=life (or a list of form ids) stands one life in a row, a form for each
## instar at that instar's size, the same coat, the Seed-mark and one part carried forward;
## --lineage=molt stands one form through the days between two Readings: new, half grown,
## the seams showing, the Reading due.
func _lineage(what: String) -> void:
	mode = "gallery"
	hud.hide_screen()
	hud.play_ui.visible = false
	world.set_place("stage")
	world.show_wolf = false
	world.genius_visible = false
	world._player.visible = false
	var col: Color = World.SHAPE_COLORS["anchor"]
	var look := GeniusLook.born(4711)
	var by_id := func(id: String) -> Dictionary:
		return Data.form(id)
	# a road down the first base's tree: settled, its first path, that path's first prong and finish
	var road: Array = [Data.bases()[0]["settled"]["id"]]
	while not Data.children_of(String(road.back())).is_empty():
		road.append(Data.children_of(String(road.back()))[0]["id"])
	var stand: Array = []      # [info, label]
	var names := ["Starter", "Path", "Advancement", "Final", "Great", "Apex"]
	var homes_row: Array = []
	if what.begins_with("homes"):
		# --lineage=homes:0 (or :1): a grown genius of one kind beside a partner from each home,
		# wearing what that home puts on its genii
		var all_homes: Array = Data.bodies.keys()
		var half := int(what.get_slice(":", 1)) if what.contains(":") else 0
		homes_row = all_homes.slice(0, 7) if half == 0 else all_homes.slice(7)
		if what.contains(":") and all_homes.has(what.get_slice(":", 1)):
			homes_row = Array(what.get_slice(":", 1).split(","))      # --lineage=homes:edo, one home close
		var hf: Dictionary = by_id.call(String(road[mini(2, road.size() - 1)]))
		for hid in homes_row:
			stand.append([{ "form": hf["id"], "silhouette": hf["silhouette"], "expression": hf["expression"], "features": hf["features"], "instar": 3, "look": GeniusLook.born(4711 + String(hid).hash() % 977), "ready": 0.0, "home": hid },
				"%s\n%s" % [String(hid).to_upper(), String(Data.bodies[hid]["dress"].get("trapping", {}).get("name", ""))]])
	elif what == "molt":
		var f: Dictionary = by_id.call(String(road[0]))
		for st in [[0.0, "THE DAY OF THE RITE"], [0.5, "HALF THE DAYS LIVED\nit has grown"], [0.85, "NEAR\nthe seams show"], [1.0, "THE READING IS DUE\nit molts"]]:
			stand.append([{ "form": f["id"], "silhouette": f["silhouette"], "expression": f["expression"], "features": f["features"], "instar": 1, "look": look, "ready": st[0] }, String(st[1])])
	elif homes_row.is_empty():
		# by default one road down a tree and its two ages after: settled, path, prong, finish,
		# great, apex. --lineage=<base> for that base's first road; or a list of form ids.
		var ids: Array = Array(what.split(","))
		if what in ["true", "", "life"] or not Data.base(what).is_empty():
			if not Data.base(what).is_empty():
				road = [Data.base(what)["settled"]["id"]]
				while not Data.children_of(String(road.back())).is_empty():
					road.append(Data.children_of(String(road.back()))[0]["id"])
			ids = road.duplicate()
			while ids.size() < 6:
				ids.append(ids.back())
		var carried: Array = []
		for i in ids.size():
			var f: Dictionary = by_id.call(String(ids[i]))
			if f.is_empty():
				continue
			var feats: Array = (f["features"] as Array).duplicate()
			# heritage: one part of the form before, carried as the same part
			for c in carried:
				if not feats.has(c):
					feats.append(c)
			if i == 0:
				feats.append("far-eyes")
			carried = ["far-eyes", String(f["features"][0])]
			stand.append([{ "form": f["id"], "silhouette": f["silhouette"], "expression": f["expression"], "features": feats, "instar": i + 1, "look": look, "ready": 0.0 },
				"%s\n%s  ·  %.2f m" % [String(names[mini(i, 5)]).to_upper(), Genius.form_name_at(String(f["id"]), i + 1), float(Data.genius()["size"][str(i + 1)])]])
	var spot := world.stage_spot()
	var widths: Array = stand.map(func(sd): return 2.3 if what == "molt" else 2.0 + float(Data.genius()["size"][str(int(sd[0]["instar"]))]) * 0.8)
	var wide := 0.0
	for wv in widths:
		wide += float(wv)
	var x := -wide / 2.0
	for k in stand.size():
		var sdef: Array = stand[k]
		x += float(widths[k]) / 2.0
		var b := world.make_form(sdef[0], col)
		world.add_child(b)
		b.position = Vector3(spot.x + x, 0.35 if (b as GeniusBody).hover else 0.0, spot.y)
		b.rotation.y = 0.55
		if what != "molt":
			# its partner beside it, wearing the echo of that instar
			var phome := String(sdef[0].get("home", "cahokia"))
			var pbody := "%s-%s" % [phome, "f" if k % 2 == 0 else "m"]
			var partner_hero := { "shape": "anchor", "blood": "", "city": phome, "body": pbody, "genius": sdef[0] }
			var pn: Node3D = load(world._person_model(pbody)).instantiate()
			world.add_child(pn)
			world.toonify(pn)
			var plook := { "headgear": not homes_row.is_empty(), "cape": true, "cape_color": "plain", "hair": "braid", "hair_color": "black", "skin": Creation.skin_of(phome, 5 + k) }
			world.dress(pn, plook, partner_hero)
			pn.position = Vector3(spot.x + x - 0.75 - float(Data.genius()["size"][str(int(sdef[0]["instar"]))]) * 0.3, 0, spot.y - 0.5)
			pn.rotation.y = 0.35
			var pa: AnimationPlayer = pn.find_child("AnimationPlayer", true, false)
			if pa and pa.has_animation("Idle"):
				pa.play("Idle")
		var l := Label3D.new()
		l.text = String(sdef[1])
		l.font = Style.font("title")
		l.font_size = 40
		l.pixel_size = 0.0036
		l.outline_size = 12
		l.modulate = Style.BRASS_HI
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.position = Vector3(spot.x + x, 0.16, spot.y + 1.1)
		world.add_child(l)
		x += float(widths[k]) / 2.0
	world.cine = true
	world.cine_pos = Vector3(spot.x + 0.4, 1.0 + wide * 0.05, spot.y + 1.2 + wide * (0.42 if what == "molt" else 0.46))
	world.cine_look = Vector3(spot.x, 0.4 if what == "molt" else 0.95, spot.y)
	world._cam_pos = world.cine_pos
	world._cam_look = world.cine_look
	if _args.has("shots"):
		await get_tree().create_timer(1.6).timeout
		await _shot("lineage-" + ("molt" if what == "molt" else "life"))
		get_tree().quit()

## --tour (with --academy --gate --shots=DIR): walk the camera through every place of the
## Academy and save two pictures of each, for reviewing the architecture and its scale.
func _tour() -> void:
	await get_tree().create_timer(1.0).timeout
	var only := str(_args.get("tour", ""))
	for id in Data.academy["places"]:
		if only != "" and only != "true" and not only.split(",").has(id):
			continue
		academy.go(id, true)
		var a: Vector2 = world.arena
		var views := {
			"wide": [Vector3(a.x * 0.42, maxf(a.x, a.y) * 0.5, a.y * 0.95), Vector3(0, 1.5, -a.y * 0.08)],
			"eye": [Vector3(-a.x * 0.3, 1.9, a.y * 0.42), Vector3(a.x * 0.12, 2.0, -a.y * 0.3)],
			"cross": [Vector3(a.x * 0.44, 2.6, -a.y * 0.1), Vector3(-a.x * 0.3, 1.6, a.y * 0.05)],
		}
		for v in views:
			world.cine = true
			world.cine_speed = 60.0
			world.cine_pos = views[v][0]
			world.cine_look = views[v][1]
			await get_tree().create_timer(0.9).timeout
			hud.screen.visible = false
			if _args.has("debug"):
				print("TOUR %s %s: %.1f frames a second, %d objects, %d primitives" % [id, v, Engine.get_frames_per_second(),
					RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME), RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)])
			_shot("tour-%s-%s" % [id, v])
			await get_tree().create_timer(0.3).timeout
	get_tree().quit()

## The Academy: walk the grounds, meet the cohort, take the lessons.
func enter_academy() -> void:
	if hero.is_empty():
		hero = Settings.hero()
	mode = "academy"
	Engine.time_scale = 1.0
	sfx.start_ambience()
	academy.auto = _args.has("bot")
	academy.auto_troubles = _args.has("troubles") or _args.has("quests")
	if _args.has("seed"):
		academy.fixed_seed = int(_args["seed"])
	if _args.has("quests") and hero.has("academy"):
		# Straight to the postings: the cohort's troubles seen to, the shade accepted, the quad.
		var pr: Dictionary = hero["academy"]
		pr["troubles_done"] = Academy.make_troubles(int(pr["seed"]), Academy.make_cohort(int(pr["seed"]), hero)).map(func(t): return t["id"])
		pr["shade_visits"] = 3
		pr["place"] = "quad"
	academy.enter(hero)
	if _args.has("posting"):
		# --posting=deep-run:green takes that posting at once, whatever the day's board drew.
		var want := String(_args["posting"]).split(":")
		var forced := academy.make_posting(want[0], want[1] if want.size() > 1 else "green")
		if not forced.is_empty():
			academy._begin_quest(forced)
	fight = academy.fight
	if str(_args.get("reading", "")) == "rite":
		# --reading=rite (with --academy --rite): the bowl's three offers at once, to look at them.
		academy.auto = false
		if _args.has("shots"):
			await get_tree().create_timer(4.0).timeout   # the place's own title card has gone by then
		academy.show_reading(Rite.first_form(hero, hero["shape"], int(_args.get("seed", "11")))["reading"], func(_i: int): pass, "The bowl offers three",
			"Read from your Seed, your blood and your Shape. Whichever settles carries the Seed-mark, and grows by how you play.")
		if _args.has("shots"):
			await get_tree().create_timer(2.0).timeout
			await _shot("rite-offer")
			get_tree().quit()
		return
	if _args.has("becoming") and academy.genius and academy.genius.is_born():
		# --becoming (with --academy --fresh --gate --shots=DIR): the change of form at the Gate,
		# taken at once (the first offer), and shot as it goes: the old body into light, the new
		# out of it. --becoming=<base> for a genius of that base.
		var bg: Genius = academy.genius
		var want := str(_args["becoming"])
		if not Data.base(want).is_empty():
			bg = Genius.at_form(String(Data.base(want)["settled"]["id"]))
			bg.look = academy.genius.look
			academy.genius = bg
			bg.save_to(academy.hero)
			world.build_hero(academy.hero)
		bg.milestone("gate")
		bg.day = maxi(bg.day, 7)
		academy.auto = false
		await get_tree().create_timer(4.0).timeout      # the place's own title card has gone by then
		var gate := GateScene.new(academy, academy.hero)
		world.cine = true
		gate.reading = bg.read(2)
		gate._take(0)
		var n := 0
		for wait in [0.7, 0.7, 0.5, 0.25, 0.5, 1.2, 1.5]:
			await get_tree().create_timer(wait).timeout
			n += 1
			await _shot("becoming-%d" % n)
		get_tree().quit()
		return
	if _args.has("reading") and academy.genius and academy.genius.is_born():
		# --reading (with --academy --gate): open the Gate's Reading at once, to look at it.
		var rg: Genius = academy.genius
		rg.milestone("gate")
		rg.day = maxi(rg.day, 7)
		# --reading=<base>: as if the term had been played like that base, so that it turns.
		var like := Data.base(str(_args["reading"]))
		if not like.is_empty():
			rg.tally = GeniusReading.empty_tally()
			_play_like(rg, like["nature"], 40)
		academy.auto = false
		if _args.has("shots"):
			await get_tree().create_timer(4.0).timeout   # the place's own title card has gone by then
		academy.show_reading(rg.read(2), func(_i: int): pass)
		if _args.has("shots"):
			await get_tree().create_timer(2.0).timeout
			await _shot("reading")
			get_tree().quit()
		return
	if not _args.has("bot"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _academy_frame(delta: float, real_dt: float) -> void:
	var stick := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var move := world.move_from_stick(stick)
	if academy.busy() or page.visible:
		move = Vector2.ZERO
	fight = academy.fight
	if _args.has("bot"):
		match academy.bot_mode() if not academy.talking() else "talk":
			"still", "talk": move = Vector2.ZERO
			"guard": move = _lesson_bot()
			"stance":
				if not fight.p_stance and fight.p_state == "free":
					fight.input("stance")
				move = Vector2.ZERO
			"technique":
				var bt := academy.bot_tech()
				var want_d := academy.bot_range()
				if fight.p_state == "free" and fight.p_will >= float(bt["will"]) and fight.now >= float(fight.p_cooldowns.get(bt["id"], 0.0)):
					if not fight.p_lock:
						fight.input("lock")
					if fight.dist() > want_d + 0.5:
						move = (fight.w_pos - fight.p_pos).normalized()
					elif fight.dist() < want_d - 0.1:
						move = -(fight.w_pos - fight.p_pos).normalized()
					else:
						fight.input(academy.bot_action())
				elif fight.p_state == "free" and fight.dist() < want_d - 0.1:
					move = -(fight.w_pos - fight.p_pos).normalized()
			"fight": move = _bot()
			_: move = academy.auto_move()
	fight.update(minf(delta, 0.1), move)
	var events := fight.drain()
	_sounds(events)
	_stings(events)
	music.set_fight(fight.threats() > 0 and not fight.passive and academy._in_zone())
	world.feedback(fight, events)
	academy.update(events, real_dt)
	if _args.has("debug") and Engine.get_process_frames() % 90 == 0:
		print("BOT place=%s mode=%s move=%s pos=%s target=%s busy=%s lesson=%s" % [academy.progress["place"], academy.bot_mode(), str(move), str(fight.p_pos), str(academy._target.get("kind", "")), str(academy.busy()), str(academy._lesson.get("id", ""))])
	fight = academy.fight
	var cam := Vector2(Input.get_joy_axis(0, JOY_AXIS_RIGHT_X), Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y))
	if cam.length() < 0.15:
		cam = Vector2.ZERO
	if not fight.p_lock:
		world.look(_cam_mouse)
	_cam_mouse = Vector2.ZERO
	world.draw(fight, real_dt, cam, move)
	if academy.in_lesson():
		hud.update_play(fight, "", academy.place_label(), true)
	if _args.has("shots") and not _args.has("tour") and _clock_shots(real_dt):
		_shot("academy-" + String(academy.progress["place"]))

## Automated checks in a lesson: keep near the genius, face it, and parry each bite.
func _lesson_bot() -> Vector2:
	if not fight.p_lock:
		fight.input("lock")
	var to := fight.w_pos - fight.p_pos
	if fight.w_state == "windup" and fight.w_timer >= fight.w_duration - 0.12 and not fight.p_block_held:
		fight.input("block-down")
	elif fight.w_state not in ["windup", "strike"] and fight.p_block_held:
		fight.input("block-up")
	if to.length() > 3.0:
		return to.normalized()
	return Vector2.ZERO

var _shot_clock := 0.0
func _clock_shots(dt: float) -> bool:
	_shot_clock += dt
	if _shot_clock >= float(_args.get("every", "5")):
		_shot_clock = 0.0
		return true
	return false

func _open_builder() -> void:
	hud.screen.visible = false
	builder.open(Settings.pattern(), Settings.pattern_lost_text(), func(): Settings.restore_pattern())

func open_genius_page() -> void:
	if academy.genius and academy.genius.is_born():
		page.open(academy.genius, World.SHAPE_COLORS.get(academy.hero["shape"], Color.WHITE), 0, int(academy.progress["record"].get("marks", 0)))

## A classmate speaks for the moment, in their temperament's voice.
func _bark(e: Dictionary, kind: String) -> void:
	var i := int(e.get("who", -1))
	if fight == null or i < 0 or i >= fight.allies.size():
		return
	var al: Dictionary = fight.allies[i]
	var temper := String(al.get("temperament", ""))
	if temper == "" and mode == "academy":
		var c := academy._classmate(String(al.get("id", "")))
		temper = String(c.get("temperament", "earnest"))
	sfx.play_bark(temper if temper != "" else "earnest", kind)

func _stings(events: Array) -> void:
	for e in events:
		match e["type"]:
			"pattern-start": music.sting("pattern")
			"quest-done": music.sting("done")
			"quest-lost": music.sting("lost")

func _pattern_built(spec: Dictionary) -> void:
	builder.visible = false
	if mode == "academy":
		academy.pattern_built(spec)
		if not _args.has("bot"):
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		return
	Settings.save_pattern(spec)
	menu()

func start(which: String) -> void:
	# The tutorial teaches with the starting Pattern; the fight uses the one you built.
	var h: Dictionary = Fight.default_hero() if which == "tutorial" or hero.is_empty() else hero
	fight = Fight.new({ "hero": h, "beast": "yard-wolf" if which == "tutorial" else "cut-wolf", "seed": randi(),
		"passive": which == "tutorial", "respawn": true,
		"pattern_lost": false if which == "tutorial" else Settings.pattern_lost(),
		"genius": Genius.for_hero(h) if h.has("genius") else null })
	world.build_hero(h)
	hud.configure(fight, h.get("name", ""))
	_breached = false
	world.show_wolf = true
	world.portrait = false
	world.genius_visible = true
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
	# What the genius learned in the yard goes home with the hero.
	if fight.genius and not hero.is_empty() and hero.has("genius"):
		fight.genius.recover()
		fight.genius.update_adaptations()
		fight.genius.save_to(hero)
		Settings.save_hero(hero)
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
	if page.visible:
		if event.is_action_pressed("genius_page") or event.is_action_pressed("menu"):
			page.hide_page()
		return
	if event.is_action_pressed("show_step"):
		hud.show_prompt_again()
	if mode == "academy":
		if event.is_action_pressed("genius_page") and not academy.busy() and not academy.in_lesson() and academy.genius and academy.genius.is_born():
			page.open(academy.genius, World.SHAPE_COLORS.get(academy.hero["shape"], Color.WHITE), 0, int(academy.progress["record"].get("marks", 0)))
			return
		if event.is_action_pressed("menu"):
			if hud.screen.visible:
				academy.unpause()
			elif not academy.busy():
				academy.pause()
			return
		if event is InputEventMouseButton and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not _args.has("bot"):
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			return
		if event.is_action_pressed("interact") or (academy.talking() and event.is_action_pressed("attack")):
			academy.interact()
			return
		if not academy.in_lesson() or academy.talking():
			return
	elif mode != "tutorial" and mode != "fight" and mode != "prologue":
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
	for pair in [["attack", "attack"], ["technique", "technique"], ["dodge", "dodge"], ["stance", "stance"], ["pattern", "pattern"], ["block", "block-down"], ["name_foe", "name"], ["order", "order"], ["tech1", "tech1"], ["tech2", "tech2"], ["tech3", "tech3"], ["reload", "reload"]]:
		if event.is_action_pressed(pair[0], false, true):
			fight.input(pair[1])
	if event.is_action_released("block", true):
		fight.input("block-up")
	if event.is_action_released("attack", true):
		fight.input("attack-up")

# --- Each frame -------------------------------------------------------------

func _process(delta: float) -> void:
	var t := Time.get_ticks_usec()
	var real_dt := minf(0.1, (t - _last_ticks) / 1e6)
	_last_ticks = t
	if mode == "academy":
		if get_tree().paused:
			world.draw(fight, 0.0, Vector2.ZERO, Vector2.ZERO)
			return
		_academy_frame(delta, real_dt)
		return
	if mode == "gallery":
		world.draw(Fight.new({ "passive": true }), real_dt, Vector2.ZERO, Vector2.ZERO)
		return
	if (mode == "creator" or mode == "menu") and preview:
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
			"reload": sfx.play("ui-take", 0.7, -6.0)
			"reloaded": sfx.play("cue-hit", 1.4, -8.0)
			"draw-start": sfx.play("swish", 0.5, -10.0)
			"ally-hit":
				if e.get("pattern", false): sfx.play("heavy", 0.8, -4.0)
				elif e.get("heavy", false): sfx.play("hit", 0.9, -4.0)
				else: sfx.play("hit", 1.1, -8.0)
			"ally-windup":
				sfx.play("swish", 1.0, -8.0)
				if e.get("technique", false): _bark(e, "technique")
			"ally-hurt": _bark(e, "hurt")
			"ally-retreat": _bark(e, "retreat")
			"ally-down": _bark(e, "down")
			"ally-pattern":
				sfx.play("pattern", 1.1, -4.0)
				_bark(e, "pattern")
			"ally-parry":
				sfx.play("parry", 1.1, -4.0)
				_bark(e, "parry")
			"ally-block": sfx.play("block", 1.1, -6.0)
			"ally-shot": sfx.play("swish", 1.6, -6.0)
			"foe-windup": sfx.play("growl", 1.1, -4.0)
			"foe-strike": sfx.play("bark", 0.9, -3.0)
			"foe-hit": sfx.play("hit", 1.0, -2.0)
			"foe-stagger": sfx.play("stagger", 1.0, -3.0)
			"foe-down": sfx.play("fell", 1.0, -3.0)
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
			"genius-guard": sfx.play("block", 1.5)
			"genius-hunt": sfx.play("hit", 1.6, -3.0)
			"genius-fall": sfx.play("fizzle", 0.6)
			"genius-up": sfx.play("cue-hit", 0.7)
			"field-open": sfx.play("pattern", 1.1)
			"order": sfx.play("stance", 1.7, -4.0)

func _shot(label: String) -> void:
	if not _args.has("shots"):
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	_shot_n += 1
	img.save_png("%s/%02d-%s.png" % [_args["shots"], _shot_n, label.replace("/", "-")])
	if _args.has("debug"):
		print("SHOT %d %s mode=%s at %.1f" % [_shot_n, label, mode, Time.get_ticks_msec() / 1000.0])

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
		var used := false
		for i in f.extra_techs.size():
			var et: Dictionary = f.extra_techs[i]
			if not used and f.p_will > float(et["will"]) + 20.0 and f.now >= float(f.p_cooldowns.get(et["id"], 0.0)) and randf() < 0.5:
				f.input("tech%d" % (i + 1))
				used = true
		if used:
			pass
		elif (step == 4 or step == 99) and f.p_will > 40 and f.now >= float(f.p_cooldowns.get(f.tech["id"], 0.0)):
			f.input("technique")
		elif step != 4:
			f.input("attack")
	if to_w.length() > 2.0 and f.w_state != "windup":
		move = to_w.normalized()
	return move
