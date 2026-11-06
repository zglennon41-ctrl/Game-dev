## The Academy at Alexandria: the solo, offline act every character plays before the server.
## Walk the grounds (the quad, the yard, the dormitory), meet the cohort of twelve generated for
## this run, talk with the Instructors, take the lessons. No one dies here: the wards hold.
## Words and places live in data/academy.json. Progress lives on the hero, under "academy".
class_name Academy
extends CanvasLayer

signal leave   # back to the title

var hero: Dictionary
var progress: Dictionary
var cohort: Array = []
var fight: Fight
var world: World
var hud: Hud
var sfx: Sfx
var auto := false            # automated checks: walk to each objective, read each line

var _people: Array = []      # who is in this place: {kind, id, name, pos, fig}
var _doors: Array = []
var _rest: Dictionary = {}
var _target: Dictionary = {}  # what E would act on
var _lines: Array = []        # the dialogue being read: [{speaker, sub, text}]
var _line_i := 0
var _after_lines: Callable
var _lesson: Dictionary = {}
var _step := -1
var _count := 0
var _note := ""
var _step_hold := 0.0
var _auto_wait := 0.0
var _type_tw: Tween

var _fade := ColorRect.new()
var _prompt := PanelContainer.new()
var _prompt_label := Label.new()
var _objective := Label.new()
var _place_card := Label.new()
var _box := PanelContainer.new()
var _speaker := Label.new()
var _speaker_sub := Label.new()
var _text := RichTextLabel.new()
var _cont := Label.new()

func _ready() -> void:
	layer = 12
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	# What you are doing now, top left under nothing else.
	Style.label(_objective, 17, Style.FG, "italic", 4)
	_objective.position = Vector2(30, 24)
	_objective.custom_minimum_size = Vector2(620, 0)
	_objective.autowrap_mode = TextServer.AUTOWRAP_WORD
	root.add_child(_objective)
	# The name of the place, as you enter it.
	Style.label(_place_card, 46, Style.FG, "title", 6)
	_place_card.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_place_card.position = Vector2(-400, 90)
	_place_card.custom_minimum_size = Vector2(800, 0)
	_place_card.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_place_card.modulate.a = 0.0
	root.add_child(_place_card)
	# "E  Talk to ...".
	_prompt.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt.position = Vector2(-200, -150)
	_prompt.custom_minimum_size = Vector2(400, 0)
	_prompt.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.034, 0.03, 0.85), Style.BRASS, 1, 10))
	Style.label(_prompt_label, 18, Style.FG, "ui")
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt.add_child(_prompt_label)
	_prompt.visible = false
	root.add_child(_prompt)
	# The dialogue box.
	_box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_box.custom_minimum_size = Vector2(980, 0)
	_box.position = Vector2(-490, -250)
	var bs := Style.plate(Color(0.035, 0.03, 0.027, 0.94), Style.BRASS, 1, 22)
	bs.border_width_top = 3
	bs.content_margin_left = 30
	bs.content_margin_right = 30
	_box.add_theme_stylebox_override("panel", bs)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	_box.add_child(v)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 14)
	v.add_child(head)
	Style.label(_speaker, 22, Style.GOLD, "title")
	head.add_child(_speaker)
	Style.label(_speaker_sub, 15, Style.DIM, "italic")
	_speaker_sub.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(_speaker_sub)
	_text.bbcode_enabled = true
	_text.fit_content = true
	_text.scroll_active = false
	_text.custom_minimum_size = Vector2(920, 60)
	Style.rich(_text, 21, Style.FG, "body")
	v.add_child(_text)
	Style.label(_cont, 13, Style.FAINT, "ui")
	_cont.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_cont.text = "E · click · continue"
	v.add_child(_cont)
	_box.visible = false
	root.add_child(_box)
	# The fade between places: black, in and out.
	_fade.color = Color(0.01, 0.008, 0.008, 1.0)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.modulate.a = 0.0
	root.add_child(_fade)

# --- Entering ----------------------------------------------------------------

## Begin or resume the Academy with this hero.
func enter(h: Dictionary) -> void:
	hero = h
	_rite = null
	_naming = false
	_lesson = {}
	_lines.clear()
	_box.visible = false
	world.cine = false
	world.genius_goal = Vector3.INF
	if _ui_built:
		_pour_box.visible = false
		_name_box.visible = false
	progress = hero.get("academy", {})
	if progress.is_empty():
		progress = { "seed": randi() % 1000000, "arrived": false, "done": [], "met": [], "day": 1, "rested_after": "",
			"place": "quad", "record": { "parries": 0, "blocks": 0, "hurts": 0, "dodges": 0, "talks": 0 } }
		hero["academy"] = progress
	# Saves from before rest was per stage.
	if progress.has("rested") and not progress.has("rested_after"):
		progress["rested_after"] = "hold" if progress["rested"] else ""
		progress.erase("rested")
	cohort = Academy.make_cohort(int(progress["seed"]), hero)
	genius = Genius.for_hero(hero)
	visible = true
	go(String(progress.get("place", "quad")), not bool(progress["arrived"]))
	if not progress["arrived"]:
		var a: Dictionary = Data.academy["arrival"]
		say(a["speaker"], a["lines"], func(): progress["arrived"] = true; save())

var genius: Genius = null

func save() -> void:
	if genius and genius.is_born():
		genius.update_adaptations()
		genius.save_to(hero)
	hero["academy"] = progress
	Settings.save_hero(hero)

## The twelve classmates of this run, made from its seed: names from their cities, bloods,
## Shapes two of each, temperaments, bodies, weapons. Deterministic, and new every run.
static func make_cohort(seed_value: int, h: Dictionary) -> Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var c: Dictionary = Data.academy["cohort"]
	var size := int(Data.academy["term"].get("cohortSize", 12))
	var shapes: Array = []
	for s in ["anchor", "turn", "cast", "read", "bind", "make"]:
		shapes.append_array([s, s])
	_shuffle(shapes, rng)
	var temps: Array = c["temperaments"].duplicate()
	_shuffle(temps, rng)
	var cities: Array = c["first"].keys()
	var used := { String(h.get("name", "")): true }
	var out: Array = []
	for i in size:
		var city: String = cities[rng.randi() % cities.size()]
		var name := ""
		for tries in 20:
			var firsts: Array = c["first"][city]
			var lasts: Array = c["last"][city]
			name = "%s %s" % [firsts[rng.randi() % firsts.size()], lasts[rng.randi() % lasts.size()]]
			if not used.has(name):
				break
		used[name] = true
		var blood: Dictionary = Data.bloods[rng.randi() % Data.bloods.size()]
		var weapons: Array = Data.weapons.filter(func(w): return w["city"] == city)
		var bodies: Array = Data.creation["bodies"]
		out.append({ "id": "c%d" % i, "name": name, "city": city, "blood": blood["id"], "blood_name": blood["name"],
			"shape": shapes[i % shapes.size()], "temperament": temps[i % temps.size()]["id"],
			"body": bodies[rng.randi() % bodies.size()], "weapon": weapons[rng.randi() % weapons.size()]["id"] })
	return out

static func _shuffle(a: Array, rng: RandomNumberGenerator) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = a[i]
		a[i] = a[j]
		a[j] = t

## Walk into a place: build it, fill it with the people who are there, put the hero at the door.
func go(place_id: String, quiet := false, from := "") -> void:
	var spec: Dictionary = Data.academy["places"][place_id]
	progress["place"] = place_id
	world.open_doors = {}
	for d in spec["doors"]:
		if door_open(d):
			world.open_doors[d["to"]] = true
	world.place = ""
	world.set_place(place_id)
	_people.clear()
	_doors = spec["doors"]
	_rest = spec.get("rest", {})
	var spawn := Vector2(spec["spawn"][0], spec["spawn"][1])
	for d in _doors:
		if d["to"] == from:
			spawn = Vector2(d["at"][0], d["at"][1]) * 0.78
	# The hero walks the grounds in a fight with no foe in it; in the yard, Millstone sits by Bask.
	# In a zone of the line the fight is real: wolves, the party beside you, no wards.
	var zone: Dictionary = spec.get("zone", {})
	_post = spec.get("post", {})
	_holding = false
	var opts := { "hero": hero, "beast": "millstone", "passive": true, "respawn": true, "mercy": true, "allow_breach": false,
		"arena": Vector2(spec["size"][0], spec["size"][1]) }
	if not zone.is_empty():
		opts = { "hero": hero, "beast": zone["beast"], "passive": false, "respawn": zone.get("respawn", true), "mercy": false, "allow_breach": false,
			"arena": Vector2(spec["size"][0], spec["size"][1]), "seed": randi(), "allies": party() }
	if genius and genius.is_born():
		opts["genius"] = genius
	fight = Fight.new(opts)
	fight.p_pos = spawn
	fight.p_facing = (-spawn).angle() if spawn.length() > 0.1 else -PI / 2.0
	fight.w_state = "absent"
	world.show_wolf = false
	world.lock_on = false
	world.portrait = false
	world.genius_visible = true
	world.set_foe({ "wolf_scale": float(fight.beast.get("modelScale", 1.0)) })
	world.set_allies(fight.allies)
	world.build_hero(hero)
	if not zone.is_empty():
		for al in fight.allies:
			al["pos"] = spawn + Vector2(-1.2, 1.4 * (1 if fight.allies.find(al) == 0 else -1))
		if zone.get("waitForPost", false):
			fight.respawn = false
		else:
			fight._spawn_wolf()
			fight.w_pos = fight._clamp_in(spawn + Vector2(9.0, randf_range(-3.0, 3.0)))
			fight.p_lock = true
			world.lock_on = true
			world.show_wolf = true
		if genius and genius.is_born():
			genius.ran(String(zone.get("ground", "wild")), zone.get("night", false))
	world.reset_feedback()
	world.cam_yaw = atan2(spawn.x, spawn.y) if spawn.length() > 0.1 else 0.0
	world.snap_camera_behind(fight)
	for ins in spec["instructors"]:
		if ins.has("discipline") and ins["discipline"] != hero.get("discipline", ""):
			continue
		var data: Dictionary = Data.by_id(Data.academy["instructors"], ins["id"])
		var at := Vector2(ins["at"][0], ins["at"][1])
		var fig := world.add_figure(data["body"], at, (spawn - at).angle(), data["name"], data.get("title", ""))
		_people.append({ "kind": "instructor", "id": data["id"], "name": data["name"], "pos": at })
		if data.has("genius"):
			fight.w_state = "idle"
			fight.w_pos = at + Vector2(1.6, 0.8)
			fight.w_facing = (spawn - fight.w_pos).angle()
			world.show_wolf = true
	var sh: Dictionary = Data.academy.get("shade", {})
	if place_id == sh.get("place", "") and progress["done"].has("rite"):
		var sd := shade()
		var sat := Vector2(sh["at"][0], sh["at"][1])
		var body := world.make_form({ "form": "shade:" + sd["id"], "silhouette": sh["silhouette"].get(sd["expression"], "kith-elder"), "expression": sd["expression"], "features": sd["features"], "instar": 4 }, Color(0.55, 0.62, 0.75))
		world.add_child(body)
		body.position = world._v3(sat)
		body.rotation.y = world._yaw((spawn - sat).angle())
		(body as GeniusBody).set_strength(0.6)
		_shade_node = body
		var l := Label3D.new()
		l.text = sd["name"].to_upper() + "\na shade of the hearth"
		l.font = Style.font("title")
		l.font_size = 24
		l.fixed_size = true
		l.pixel_size = 0.001
		l.modulate = Color(0.75, 0.82, 0.95, 0.85)
		l.outline_size = 8
		l.outline_modulate = Color(0, 0, 0, 0.8)
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.position = Vector3(0, 2.2, 0)
		body.add_child(l)
		_people.append({ "kind": "shade", "id": sd["id"], "name": sd["name"], "pos": sat })
	if place_id == "quad" or spec.get("cohortHere", false):
		var spots: Array = spec["spots"]
		for i in mini(cohort.size(), spots.size()):
			var c: Dictionary = cohort[i]
			var at := Vector2(spots[i][0], spots[i][1])
			var fig := world.add_figure(c["body"], at, (Vector2.ZERO - at).angle() + randf_range(-0.6, 0.6), c["name"],
				"%s · %s" % [c["blood_name"], String(c["shape"]).capitalize()], c["weapon"])
			_people.append({ "kind": "classmate", "id": c["id"], "name": c["name"], "pos": at, "c": c })
	fight.obstacles = world.obstacles
	hud.hide_screen()
	hud.configure(fight, hero["name"])
	hud.play_ui.visible = not zone.is_empty()
	if not zone.is_empty():
		hud.target.visible = true
	_show_place(spec["name"])
	sfx.set_ambience("wild" if not zone.is_empty() else "hall")
	# Arrive out of the dark.
	if _fade.is_inside_tree():
		_fade.modulate.a = 1.0
		var tw := _fade.create_tween()
		tw.tween_interval(0.15)
		tw.tween_property(_fade, "modulate:a", 0.0, 0.7).set_trans(Tween.TRANS_SINE)
	save()

## Marks earned: counted on the record, logged by day, and shown as they land.
func earn_marks(what: String, label: String) -> void:
	var n := Marks.academy(what)
	if n <= 0:
		return
	var rec: Dictionary = progress["record"]
	rec["marks"] = int(rec.get("marks", 0)) + n
	if not progress.has("marks_log"):
		progress["marks_log"] = []
	progress["marks_log"].append({ "day": int(progress["day"]), "what": label, "n": n })
	if fight:
		world.floater(world._v3(fight.p_pos, 2.6), ("%d MARK" if n == 1 else "%d MARKS") % n, Style.GOLD, 48, 1.6, 0.5)
	sfx.play("cue-hit", 1.2, -4.0)

## The two classmates chosen for the party, as classmate dictionaries.
func party() -> Array:
	var out: Array = []
	for id in progress.get("party", []):
		for c in cohort:
			if c["id"] == id:
				out.append(c)
	return out

var _post: Dictionary = {}
var _holding := false
var _hold_t := 0.0

func _show_place(title: String) -> void:
	_place_card.text = title
	var tw := _place_card.create_tween()
	_place_card.modulate.a = 0.0
	tw.tween_property(_place_card, "modulate:a", 1.0, 0.6)
	tw.tween_interval(1.6)
	tw.tween_property(_place_card, "modulate:a", 0.0, 0.9)

# --- Talking -----------------------------------------------------------------

## Open the dialogue box with lines from someone. `who` is an Instructor id, a classmate
## dictionary, or "" for narration.
func say(who: Variant, lines: Array, then: Callable = Callable()) -> void:
	_lines.clear()
	var speaker := ""
	var sub := ""
	var c: Dictionary = {}
	if who is String and who != "":
		var data: Dictionary = Data.by_id(Data.academy["instructors"], who)
		speaker = data["name"]
		sub = data.get("title", "")
	elif who is Dictionary:
		c = who
		speaker = c["name"]
		sub = "%s · %s · %s" % [c["blood_name"], String(c["shape"]).capitalize(), String(c["city"]).capitalize()]
	for l in lines:
		_lines.append({ "speaker": speaker, "sub": sub, "text": fill(String(l), c) })
	_line_i = 0
	_after_lines = then
	_show_line()

func fill(t: String, c: Dictionary = {}) -> String:
	t = Prologue.fill(t, hero)
	t = t.replace("{your_shape}", String(hero["shape"]).capitalize()).replace("{your_blood}", Data.by_id(Data.bloods, hero["blood"])["name"] if hero.get("blood", "") != "" else "unmarked")
	var arch := Marks.archetype_for(hero["shape"], hero.get("discipline", ""))
	t = t.replace("{archetype}", arch.get("name", "Journeyman")).replace("{marks}", str(int(progress["record"].get("marks", 0))))
	t = t.replace("{weekday}", weekday()).replace("{season}", String(Data.academy.get("calendar", {}).get("season", "the Thaw")))
	t = t.replace("{discipline_rite}", String(Data.discipline_kits.get(hero.get("discipline", ""), {}).get("rite", "the Instructor's test")))
	var dk: Dictionary = Data.discipline_kits.get(hero.get("discipline", ""), {})
	if not dk.is_empty():
		t = t.replace("{discipline}", dk["name"]).replace("{discipline_school}", dk["school"])
		for i in dk["techniques"].size():
			t = t.replace("{tech%d}" % (i + 1), dk["techniques"][i]["name"]).replace("{tech%d_text}" % (i + 1), dk["techniques"][i]["text"])
	if not c.is_empty():
		t = t.replace("{my_name}", c["name"]).replace("{my_shape}", String(c["shape"]).capitalize()).replace("{my_blood}", c["blood_name"]).replace("{my_city}", String(c["city"]).capitalize())
	return t

func _show_line() -> void:
	if _line_i >= _lines.size():
		_box.visible = false
		var then := _after_lines
		_after_lines = Callable()
		if then.is_valid():
			then.call()
		return
	var l: Dictionary = _lines[_line_i]
	_speaker.text = l["speaker"] if l["speaker"] != "" else ""
	_speaker_sub.text = l["sub"]
	_text.text = l["text"]
	_text.visible_ratio = 0.0
	_box.visible = true
	_prompt.visible = false
	_box.modulate.a = 1.0
	if _type_tw:
		_type_tw.kill()
	_type_tw = _text.create_tween()
	_type_tw.tween_property(_text, "visible_ratio", 1.0, clampf(String(l["text"]).length() / 90.0, 0.3, 1.8))
	_auto_wait = 0.5

func talking() -> bool:
	return _box.visible

## E, a click, or the pad's interact: finish the line, next line, or act on what is near.
func interact() -> void:
	if talking():
		if _text.visible_ratio < 1.0:
			if _type_tw:
				_type_tw.kill()
			_text.visible_ratio = 1.0
		else:
			_line_i += 1
			sfx.play("ui-move", 0.9, -8.0)
			_show_line()
		return
	if _target.is_empty() or (in_lesson() and _target["kind"] not in ["door", "post", "find", "classmate", "instructor"]) or _rite or _gate or _reading_box or _naming:
		return
	sfx.play("ui-take", 1.0, -6.0)
	match _target["kind"]:
		"door": _use_door(_target["door"])
		"rest": _rest_now()
		"post": _take_post()
		"board": _read_board()
		"shade": _visit_shade()
		"find": _pick_up()
		"instructor": _talk_instructor(_target["id"])
		"classmate": _talk_classmate(_target["c"])

func door_open(d: Dictionary) -> bool:
	if not d.has("locked"):
		return true
	match String(d.get("opensWhen", "")):
		"rested": return rested_on("hold") or progress["done"].has("rite")
		"cleared": return progress.get("cleared", {}).has(progress["place"])
		"gate": return rested_on("project") or progress["done"].has("gate")
	return false

func _use_door(d: Dictionary) -> void:
	if not door_open(d):
		say("", [d["locked"]])
		return
	var from: String = progress["place"]
	if d["to"] == "extraction":
		_extract()
		return
	go(d["to"], false, from)

func _talk_instructor(id: String) -> void:
	var data: Dictionary = Data.by_id(Data.academy["instructors"], id)
	progress["record"]["talks"] += 1
	if in_lesson():
		say(id, [data["lines"]["default"]])
		return
	var lines: Dictionary = data["lines"]
	# The Instructor who teaches the next lesson starts it.
	for lesson in Data.academy["lessons"]:
		if lesson_instructor(lesson) == id and not lesson_done(lesson["id"]) and lesson["place"] == progress["place"] and lesson_available(lesson):
			var intro: Array = [lines.get("before:" + String(lesson["id"]), "")] + lesson["intro"]
			say(id, intro.filter(func(x): return x != ""), func(): _start_lesson(lesson))
			return
	var rite: Dictionary = Data.academy["rite"]
	if id == rite["instructor"] and progress["place"] == rite["place"] and not progress["done"].has("rite"):
		_start_rite()
		return
	var gate: Dictionary = Data.academy["gate"]
	if id == gate["instructor"] and progress["place"] == gate["place"] and not progress["done"].has("gate") and next_need() == "gate":
		_start_gate()
		return
	var key := _stage_key()
	say(id, [lines.get(key, lines["default"])])

func _talk_classmate(c: Dictionary) -> void:
	var t: Dictionary = Data.by_id(Data.academy["cohort"]["temperaments"], c["temperament"])
	progress["record"]["talks"] += 1
	if in_lesson() and _lesson.get("trouble", false):
		if c["id"] == _lesson["poster"]["id"] and _step_goal_type() == "talk":
			_choice_done = true
			say(c, [fill(_lesson["kind_spec"]["thanks"], c)])
		else:
			say(c, [t["lines"]["greet"]])
		return
	var first: bool = not progress["met"].has(c["id"])
	if first:
		progress["met"].append(c["id"])
	var line: String = t["lines"]["greet"]
	if not first:
		for key in [_stage_key(), "after:rite" if progress["done"].has("rite") else "", "after:hold" if progress["done"].has("hold") else ""]:
			if key != "" and t["lines"].has(key):
				line = t["lines"][key]
				break
	var lines: Array = [line]
	# The season's Omen, a rumour a day, from whoever you talk to first.
	var rum: Array = Data.academy.get("rumours", {}).get("lines", [])
	var heard := int(progress.get("rumours_heard", 0))
	if heard < rum.size() and int(progress.get("rumour_day", 0)) != int(progress["day"]):
		lines.append("[i]%s[/i]" % rum[heard])
		progress["rumours_heard"] = heard + 1
		progress["rumour_day"] = int(progress["day"])
		progress["record"]["rumours"] = heard + 1
	say(c, lines, save)

## Where the term has got to, for which lines people say.
func _stage_key() -> String:
	var order := ["hold", "rite", "shape", "discipline", "line", "project", "gate"]
	var last := last_done()
	if last == "":
		return "before:hold"
	if rested_on(last):
		var i := order.find(last)
		return "before:" + order[i + 1] if i + 1 < order.size() else "after:" + last
	return "after:" + last

func last_done() -> String:
	return progress["done"].back() if not progress["done"].is_empty() else ""

func rested_on(id: String) -> bool:
	return String(progress.get("rested_after", "")) == id

## The next lesson (or the rite) whose requirements are met and is not done: {} if none.
func next_lesson() -> Dictionary:
	for lesson in Data.academy["lessons"]:
		if lesson_done(lesson["id"]):
			continue
		if lesson_available(lesson):
			return lesson
		return {}
	return {}

## Who teaches a lesson: an Instructor id, or "$discipline" for the hero's city's school.
func lesson_instructor(lesson: Dictionary) -> String:
	if lesson["instructor"] == "$discipline":
		for ins in Data.academy["instructors"]:
			if ins.get("discipline", "") == hero.get("discipline", ""):
				return ins["id"]
	return lesson["instructor"]

## Advanced standing: a second character's short term (data/academy.json, "advanced").
func advanced() -> bool:
	return hero.get("advanced", false)

func lesson_done(id: String) -> bool:
	if progress["done"].has(id):
		return true
	return advanced() and Data.academy.get("advanced", {}).get("skipLessons", []).has(id)

func lesson_available(lesson: Dictionary) -> bool:
	var req: Dictionary = lesson.get("requires", {})
	for d in req.get("done", []):
		if not lesson_done(d):
			return false
	if req.has("rested_after") and not rested_on(req["rested_after"]):
		return false
	return true

## What stands between the hero and the next lesson: "rest", "rite", or "".
func next_need() -> String:
	if not progress["done"].has("hold"):
		return ""
	if not progress["done"].has("rite"):
		return "rite" if rested_on("hold") else "rest"
	var nl := next_lesson()
	if nl.is_empty():
		for lesson in Data.academy["lessons"]:
			if not lesson_done(lesson["id"]):
				return "rest" if lesson.get("requires", {}).has("rested_after") and not rested_on(lesson["requires"]["rested_after"]) else ""
		if not progress["done"].has("gate"):
			return "gate" if rested_on("project") else "rest"
		return ""
	return ""

func _rest_now() -> void:
	var r: Dictionary = Data.academy["rest"]
	var last := last_done()
	if last == "":
		say("", [r["too_early"]])
		return
	if rested_on(last):
		say("", [r["already"]])
		return
	var next_line: String = r["next"].get(last, "") if r["next"] is Dictionary else String(r["next"])
	say("", r["lines"] + ([next_line] if next_line != "" else []), func():
		progress["rested_after"] = last
		progress["day"] = int(progress["day"]) + 1
		save()
		_build_rite_ui()
		# Morning: the fade down and up, and the day's number.
		_fade.modulate.a = 1.0
		var tw := _fade.create_tween()
		tw.tween_interval(0.6)
		tw.tween_property(_fade, "modulate:a", 0.0, 1.0).set_trans(Tween.TRANS_SINE)
		title_card("DAY %d" % int(progress["day"]), "%s  ·  %s" % [date_line(), Data.academy.get("calendar", {}).get("notes", {}).get(weekday(), "")], Style.GOLD)
		sfx.play("stance", 0.8, -6.0))

# --- Each frame -----------------------------------------------------------------

## The term's date: "Day 3, Wednesday of the Thaw".
func weekday() -> String:
	var cal: Dictionary = Data.academy.get("calendar", {})
	var days: Array = cal.get("weekdays", ["Monday"])
	return days[(int(progress["day"]) - 1) % days.size()]

func date_line() -> String:
	return "Day %d, %s of %s" % [int(progress["day"]), weekday(), String(Data.academy.get("calendar", {}).get("season", "the Thaw"))]

func objective() -> String:
	if in_lesson():
		return "Lesson %d · %s" % [int(_lesson["number"]), _lesson["title"]]
	if not progress["done"].has("hold"):
		if progress["place"] == "yard":
			return "Lesson 1 · Hold: speak to Yardmaster Bask."
		return "Lesson 1 · Hold: find Yardmaster Bask in the Yard (the west door of the quad). Meet your cohort on the way."
	var day := int(progress["day"])
	match next_need():
		"rest": return "Day %d · Rest in the Dormitory (the east door of the quad)." % day
		"gate":
			if progress["place"] == "gate":
				return "Day %d · The Gate: speak to Instructor Varga on the platform." % day
			return "Day %d · The Gate: the south door of the quad. Your cohort is gathering." % day
		"rite":
			if progress["place"] == "hearth":
				return "Day %d · The rite: speak to Instructor Varga at the bowl." % day
			return "Day %d · The rite: go to the Hearth Hall (the north door of the quad)." % day
	var nl := next_lesson()
	if not nl.is_empty():
		var ins: Dictionary = Data.by_id(Data.academy["instructors"], lesson_instructor(nl))
		var place: Dictionary = Data.academy["places"][nl["place"]]
		if progress["place"] == nl["place"]:
			return "Day %d · Lesson %d, %s: speak to %s." % [day, int(nl["number"]), nl["title"], ins["name"]]
		return "Day %d · Lesson %d, %s: find %s in %s." % [day, int(nl["number"]), nl["title"], ins["name"], place["name"]]
	if in_lesson() and _lesson.get("trouble", false):
		return "%s's trouble · %s" % [_lesson["poster"]["name"], fill(_lesson["steps"][_step]["title"], _lesson["poster"]) if _step >= 0 and _step < _lesson["steps"].size() else ""]
	var g: Dictionary = hero.get("genius", {})
	if progress["done"].has("gate"):
		return "Settled. The line is waiting; the Academy is yours to walk."
	return "Day %d · %s walks with you." % [day, g.get("name", "Your genius")]

## The lesson asks for stillness now (Contain): the autopilot keeps its hands down.
func wants_still() -> bool:
	return bot_mode() == "still"

## What the autopilot should be doing in the lesson: still, guard, stance, technique or fight.
func bot_mode() -> String:
	if not in_lesson() or _step < 0 or _step >= _lesson["steps"].size():
		return "walk"
	var g: Dictionary = _lesson["steps"][_step]["goal"]
	match String(g["type"]):
		"will-full", "choose-weapon", "choose-party", "travel": return "still"
		"find", "talk", "reach": return "walk"
		"hunt": return "fight"
		"fell": return "fight"
		"reach-hits": return "technique"
		"hold": return "fight" if _holding else "walk"
		"extract": return "walk"
		"stance-seconds": return "stance"
		"spar": return "fight"
		"event":
			var want: Array = g["event"] if g["event"] is Array else [g["event"]]
			if "field-open" in want:
				return "stance"
			return "technique" if "technique" in want else "guard"
	return "guard"

## The technique the autopilot should use now, and the action that presses it.
func bot_tech() -> Dictionary:
	var g: Dictionary = _lesson["steps"][_step]["goal"]
	if g.has("tech") and int(g["tech"]) - 1 < fight.extra_techs.size():
		return fight.extra_techs[int(g["tech"]) - 1]
	return fight.tech

## How far from the foe the autopilot should stand to use a technique.
func bot_range() -> float:
	var g: Dictionary = _lesson["steps"][_step]["goal"]
	return float(g.get("distance", 2.5)) + 0.35 if String(g["type"]) == "reach-hits" else 2.2

func bot_action() -> String:
	var g: Dictionary = _lesson["steps"][_step]["goal"]
	return "tech%d" % int(g["tech"]) if g.has("tech") else "technique"

func busy() -> bool:
	return talking() or _rite != null or _gate != null or _naming or _choice_box != null or _reading_box != null

func in_rite() -> bool:
	return _rite != null

func in_lesson() -> bool:
	return not _lesson.is_empty()

func update(events: Array, dt: float) -> void:
	_objective.text = objective()
	if _gate and talking() and auto:
		_auto_wait -= dt
		if _auto_wait <= 0.0:
			if _type_tw:
				_type_tw.kill()
			_text.visible_ratio = 1.0
			interact()
		return
	if _rite:
		var held := auto or Input.is_action_pressed("interact") or Input.is_action_pressed("attack")
		if not talking():
			_rite.update(dt, held)
		_prompt.visible = false
		if talking() and auto:
			_auto_wait -= dt
			if _auto_wait <= 0.0:
				if _type_tw:
					_type_tw.kill()
				_text.visible_ratio = 1.0
				interact()
		return
	_objective.visible = not in_lesson()
	if in_lesson():
		_lesson_update(events, dt)
	if talking():
		if auto:
			_auto_wait -= dt
			if _auto_wait <= 0.0:
				if _type_tw:
					_type_tw.kill()
				_text.visible_ratio = 1.0
				interact()
		return
	# What is within reach to act on.
	_target = {}
	if not in_lesson() or _in_zone():
		var best := 2.4
		for p in _people:
			var d: float = (fight.p_pos - p["pos"]).length()
			if d < best:
				best = d
				_target = p
		for d in _doors:
			var at := Vector2(d["at"][0], d["at"][1]) * 0.86
			var dd := (fight.p_pos - at).length()
			if dd < 2.2 and dd < best:
				best = dd
				_target = { "kind": "door", "door": d, "pos": at }
		if not _rest.is_empty():
			var ra := Vector2(_rest["at"][0], _rest["at"][1])
			if (fight.p_pos - ra).length() < minf(best, 2.4):
				_target = { "kind": "rest", "pos": ra }
		if not _post.is_empty() and not _holding:
			var pa := Vector2(_post["at"][0], _post["at"][1])
			if (fight.p_pos - pa).length() < minf(best, 2.6):
				_target = { "kind": "post", "pos": pa }
		if board_open() and not in_lesson():
			var bspec: Dictionary = Data.academy["places"][progress["place"]].get("board", {})
			if not bspec.is_empty():
				var ba := Vector2(bspec["at"][0], bspec["at"][1])
				if (fight.p_pos - ba).length() < minf(best, 2.8):
					_target = { "kind": "board", "pos": ba }
		if _lost_at != Vector2.INF and (fight.p_pos - _lost_at).length() < minf(best, 2.0):
			_target = { "kind": "find", "pos": _lost_at }
	_prompt.visible = not _target.is_empty()
	if _prompt.visible:
		match _target["kind"]:
			"door": _prompt_label.text = ("E   " + ("Enter " if door_open(_target["door"]) else "Try ") + String(_target["door"]["label"]))
			"rest": _prompt_label.text = "E   Rest in %s" % _rest["label"]
			"post": _prompt_label.text = "E   Take %s" % _post["label"]
			"board": _prompt_label.text = "E   Read the board"
			"shade": _prompt_label.text = "E   Speak with the shade"
			"find": _prompt_label.text = "E   Pick up %s" % _lost_label
			_: _prompt_label.text = "E   Talk to %s" % _target["name"]

## Automated checks: where the autopilot walks next, and whether to act there.
func auto_move() -> Vector2:
	if busy():
		return Vector2.ZERO
	var goal := Vector2.INF
	var place: String = progress["place"]
	if in_lesson():
		# In a lesson, the only walking is to the post, the way out, or a trouble's goal.
		if _step >= 0 and _step < _lesson["steps"].size():
			var st: Dictionary = _lesson["steps"][_step]
			var gt := String(st["goal"]["type"])
			if gt == "hold" and not _holding and not _post.is_empty():
				goal = Vector2(_post["at"][0], _post["at"][1])
			elif gt == "extract":
				for d in _doors:
					if d["to"] == "extraction":
						goal = Vector2(d["at"][0], d["at"][1]) * 0.86
			elif gt == "find" and _lost_at != Vector2.INF:
				goal = _lost_at
			elif gt == "talk":
				var who: Dictionary = _lesson.get("poster", {})
				var want_place := String(st.get("place", progress["place"]))
				if progress["place"] != want_place:
					for d in _doors:
						if d["to"] == want_place:
							goal = Vector2(d["at"][0], d["at"][1]) * 0.86
				else:
					for p in _people:
						if p.get("id", "") == who.get("id", "-"):
							goal = p["pos"]
			elif gt == "reach":
				for d in _doors:
					if d["to"] == st["goal"]["place"]:
						goal = Vector2(d["at"][0], d["at"][1]) * 0.86
		if goal == Vector2.INF:
			return Vector2.ZERO
		if (goal - fight.p_pos).length() < 1.8:
			if not _target.is_empty():
				interact()
			return Vector2.ZERO
		return (goal - fight.p_pos).normalized()
	var want_place := ""
	match next_need():
		"rest": want_place = "dorm"
		"rite": want_place = "hearth"
		"gate": want_place = "gate"
		_:
			var nl := next_lesson()
			want_place = nl["place"] if not nl.is_empty() else ""
	if auto_troubles and board_open() and progress.get("trouble", "") == "" and troubles_open().size() > 0:
		var bspec: Dictionary = Data.academy["places"].get("quad", {}).get("board", {})
		if place == "quad":
			goal = Vector2(bspec["at"][0], bspec["at"][1])
		else:
			for d in _doors:
				if d["to"] == "quad":
					goal = Vector2(d["at"][0], d["at"][1]) * 0.86
		if (goal - fight.p_pos).length() < 2.2 and not _target.is_empty():
			interact()
			return Vector2.ZERO
		return (goal - fight.p_pos).normalized() if goal != Vector2.INF else Vector2.ZERO
	if want_place == "":
		return Vector2.ZERO
	if place == want_place:
		if want_place == "dorm":
			goal = Vector2(_rest["at"][0], _rest["at"][1])
		else:
			var nl2 := next_lesson()
			var who := lesson_instructor(nl2) if not nl2.is_empty() else ""
			var teachers := _people.filter(func(p): return p["kind"] == "instructor" and (who == "" or p["id"] == who))
			if teachers.is_empty():
				teachers = _people.filter(func(p): return p["kind"] == "instructor")
			goal = teachers[0]["pos"]
	elif place == "quad":
		# Greet two classmates on the way out, the first time.
		var unmet := _people.filter(func(p): return p["kind"] == "classmate" and not progress["met"].has(p["id"]))
		if progress["met"].size() < 2 and not unmet.is_empty():
			goal = unmet[0]["pos"]
		else:
			for d in _doors:
				if d["to"] == want_place:
					goal = Vector2(d["at"][0], d["at"][1]) * 0.86
	else:
		for d in _doors:
			if d["to"] == "quad":
				goal = Vector2(d["at"][0], d["at"][1]) * 0.86
	if goal == Vector2.INF:
		return Vector2.ZERO
	if (goal - fight.p_pos).length() < 1.6:
		if not _target.is_empty():
			interact()
		return Vector2.ZERO
	return (goal - fight.p_pos).normalized()

# --- Lessons -------------------------------------------------------------------

func _start_lesson(lesson0: Dictionary) -> void:
	var lesson := lesson0
	if advanced():
		# The short term: the drills named in the data are left out, and the rest cut down.
		var adv: Dictionary = Data.academy.get("advanced", {})
		lesson = lesson0.duplicate(true)
		var skip: Array = adv.get("skipSteps", {}).get(lesson["id"], [])
		lesson["steps"] = lesson["steps"].filter(func(st): return not skip.has(st["title"]))
		var counts: Dictionary = adv.get("counts", {}).get(lesson["id"], {})
		for st in lesson["steps"]:
			if counts.has(st["title"]):
				st["goal"]["count"] = counts[st["title"]]
	_lesson = lesson
	# A run of the line starts with every door of the Green shut again.
	progress["cleared"] = {}
	# The Discipline lesson hands over the school's three techniques to learn.
	if lesson["id"] == "discipline":
		var dk: Dictionary = Data.discipline_kits.get(hero.get("discipline", ""), {})
		hero["techniques"] = dk.get("techniques", []).map(func(t): return t["id"])
	var spec: Dictionary = Data.academy["places"][lesson["place"]]
	var ins: Dictionary = Data.by_id(Data.academy["instructors"], lesson["instructor"])
	_drill_fight()
	hud.play_ui.visible = true
	hud.target.visible = false
	_prompt.visible = false
	_step = -1
	_next_step()

## The Instructor's genius sits in the ring: the fight the drills are done in.
func _drill_fight() -> void:
	var spec: Dictionary = Data.academy["places"][_lesson["place"]]
	var ins: Dictionary = Data.by_id(Data.academy["instructors"], lesson_instructor(_lesson))
	var p := fight.p_pos if fight else Vector2(-1.5, 0.5)
	world.set_foe({})
	fight = Fight.new({ "hero": hero, "beast": ins.get("genius", {}).get("beast", "millstone"), "passive": true, "respawn": true, "genius": genius if genius and genius.is_born() else null,
		"mercy": true, "allow_breach": false, "arena": Vector2(spec["size"][0], spec["size"][1]), "seed": randi() })
	fight.allowed = _lesson.get("allow", [])
	fight.obstacles = world.obstacles
	fight.p_pos = Vector2(-1.5, 0.5)
	fight.w_pos = Vector2(2.5, 0.0)
	fight.w_state = "idle"
	fight.p_facing = 0.0
	fight.w_facing = PI
	world.show_wolf = true
	world.reset_feedback()
	world.snap_camera(fight)
	hud.configure(fight, hero["name"])

# --- The ladder: sparring the cohort -------------------------------------------------

var _spar_rung := 0
var _spar_wins := 0
var _spar_hold := 0.0
var _spar_who: Dictionary = {}
var _spar_mode := "cohort"
var _choice_done := false

## The cohort in the order they step up: the shy ones first, the proud last.
func spar_order() -> Array:
	var order: Array = _lesson.get("spar", {}).get("order", [])
	var out := cohort.duplicate()
	out.sort_custom(func(a, b): return order.find(a["temperament"]) < order.find(b["temperament"]))
	return out

func _spar_begin() -> void:
	var spec: Dictionary = Data.academy["places"][_lesson["place"]]
	var scale := 1.0 + _spar_rung * float(_lesson.get("spar", {}).get("scalePerRung", 0.18))
	if _spar_mode == "poster":
		_spar_who = _lesson["poster"].duplicate()
		scale = 1.1
	elif _spar_mode == "instructor":
		var ins: Dictionary = Data.by_id(Data.academy["instructors"], lesson_instructor(_lesson))
		_spar_who = { "name": ins["name"], "shape": ins["shape"], "body": ins["body"], "weapon": ins.get("weapon", "saber"),
			"blood_name": ins.get("title", "Instructor"), "city": Data.discipline_kits.get(ins.get("discipline", ""), {}).get("city", hero["city"]),
			"discipline": ins.get("discipline", ""), "temperament": "" }
		scale = float(_lesson.get("spar", {}).get("scale", 1.9))
	else:
		var line := spar_order()
		_spar_who = line[_spar_rung % line.size()]
	var foe := _spar_who.duplicate()
	foe["title"] = "%s · %s" % [_spar_who["blood_name"], Data.academy["term"]["cohort"]]
	var keep := fight.p_pos if fight else Vector2(-1.5, 0.5)
	fight = Fight.new({ "hero": hero, "foe": foe, "foe_scale": scale, "passive": false, "respawn": false, "mercy": false,
		"genius": genius if genius and genius.is_born() else null, "allow_breach": false,
		"arena": Vector2(spec["size"][0], spec["size"][1]), "seed": randi() })
	fight.obstacles = world.obstacles
	fight.p_pos = keep
	fight.w_pos = Vector2(3.0, 0.0) if keep.x < 0.0 else Vector2(-3.0, 0.0)
	fight.w_facing = fight._angle_to(fight.w_pos, fight.p_pos)
	fight.p_lock = true
	fight._wolf_set("prowl", 1.0)
	world.set_foe(fight.beast["person"])
	world.lock_on = true
	world.show_wolf = true
	world.reset_feedback()
	hud.configure(fight, hero["name"])
	hud.target.visible = true
	var sl: Dictionary = _lesson.get("spar", {}).get("lines", {})
	_note = fill(sl.get("step_up", "{my_name} steps up."), _spar_who)
	title_card(String(_spar_who["name"]).to_upper(), "%s  ·  %s  ·  bout %d" % [_spar_who["blood_name"], String(_spar_who["shape"]).capitalize(), _spar_rung + 1], World.SHAPE_COLORS.get(_spar_who["shape"], Color.WHITE))
	sfx.play("stance", 1.2)

func _spar_result(won: bool) -> void:
	var sl: Dictionary = _lesson.get("spar", {}).get("lines", {})
	var rec: Dictionary = progress["record"]
	rec["spars_won"] = int(rec.get("spars_won", 0)) + (1 if won else 0)
	rec["spars_lost"] = int(rec.get("spars_lost", 0)) + (0 if won else 1)
	if won:
		_spar_wins += 1
		_count = _spar_wins
		_spar_rung += 1
		earn_marks("bout", "a bout won against %s" % _spar_who["name"])
		title_card("THE BOUT IS YOURS", fill(sl.get("won", ""), _spar_who), Style.GOLD)
		sfx.play("done")
	else:
		title_card("DOWN", fill(sl.get("lost", ""), _spar_who), Style.EMBER)
		sfx.play("fizzle", 0.7)
	_spar_hold = 2.4

## The ladder is done: Millstone sits back in the ring.
func _spar_end() -> void:
	_drill_fight()
	hud.target.visible = false

func _next_step() -> void:
	_step += 1
	var steps: Array = _lesson["steps"]
	if _step >= steps.size():
		_finish_lesson()
		return
	var s: Dictionary = steps[_step]
	_count = 0
	_note = ""
	var setup: Dictionary = s.get("setup", {})
	if setup.has("will"):
		fight.p_will = float(setup["will"])
	fight.project_training = setup.get("project", false)
	match String(setup.get("genius", "")):
		"sit":
			fight.passive = true
			fight.w_state = "idle"
		"loose":
			fight.passive = false
			fight.p_lock = true
			world.lock_on = true
			if fight.w_state in ["idle", "absent"]:
				fight._wolf_set("prowl", 0.8)
	_held = 0.0
	if s.get("companion", false) and _lesson.get("trouble", false):
		# The poster walks beside you.
		fight.allies = []
		var c: Dictionary = _lesson["poster"]
		fight.allies.append({ "id": c["id"], "name": c["name"], "shape": c["shape"], "body": c["body"], "weapon": c["weapon"], "hp": 90.0, "hp_max": 90.0,
			"pos": fight.p_pos + Vector2(-1.2, 1.2), "facing": 0.0, "down": false, "hit_at": 0.0, "damage": 0.0, "interval": 9.0, "moving": false })
		world.set_allies(fight.allies)
	if setup.get("spar", false):
		_spar_mode = "poster" if str(setup["spar"]) == "poster" else ("instructor" if str(setup["spar"]) == "instructor" else "cohort")
		_spar_rung = 0
		_spar_wins = 0
		_spar_begin()
	if s.has("place") and progress["place"] != s["place"]:
		go(s["place"], false, progress["place"])
	match String(s["goal"]["type"]):
		"find":
			_choice_done = false
			var rng := RandomNumberGenerator.new()
			rng.seed = int(progress["seed"]) + 77
			var a: Dictionary = Data.academy["places"][progress["place"]]
			_lost_at = Vector2(rng.randf_range(-a["size"][0] / 2.0 + 2.0, a["size"][0] / 2.0 - 2.0), rng.randf_range(-a["size"][1] / 2.0 + 2.0, a["size"][1] / 2.0 - 2.0))
			_lost_label = fill(String(s["goal"]["item"]), _lesson.get("poster", {}))
			world.set_marker(_lost_at)
		"talk", "reach":
			_choice_done = false
		"hunt":
			_choice_done = false
			_hunt_begin(String(s["goal"]["beast"]), float(s["goal"].get("scale", 1.0)))
		"choose-party":
			_choice_done = false
			progress["party"] = []
			_pick_party(2)
		"travel":
			_choice_done = false
			var to: String = s["goal"]["to"]
			say("", s["goal"].get("lines", []), func():
				_choice_done = true
				go(to, false, progress["place"]))
		"extract":
			_choice_done = false
	if String(s["goal"]["type"]) == "choose-weapon":
		_choice_done = false
		var opts: Array = []
		for w in Data.weapons:
			if w["city"] == hero["city"]:
				opts.append({ "id": w["id"], "label": w["name"], "text": w["text"], "on": w["id"] == hero["weapon"] })
		choose("Your weapon", opts, func(id: String):
			hero["weapon"] = id
			world.build_hero(hero)
			_drill_fight()
			_choice_done = true)
	hud.set_prompt("%d/%d · %s" % [_step + 1, steps.size(), fill(s["title"])], fill(s["text"]))
	hud.set_prompt_status("", _progress_text(s))

func _progress_text(s: Dictionary) -> String:
	var g: Dictionary = s["goal"]
	match String(g["type"]):
		"event", "streak", "fell", "reach-hits": return "%d / %d" % [_count, int(g["count"])]
		"hold": return ("%d / %d s" % [int(_hold_t), int(g["seconds"])]) if _holding else "take the post"
		"will-full": return "Will %d / %d" % [roundi(fight.p_will), int(Data.rules["field"]["willMax"])]
		"stance-seconds": return "%.1f / %d s" % [_held, int(g["count"])]
		"spar": return "bouts won %d / %d" % [_spar_wins, int(g["count"])]
	return ""

var _held := 0.0

func _lesson_update(events: Array, dt: float) -> void:
	var rec: Dictionary = progress["record"]
	for e in events:
		match e["type"]:
			"parry": rec["parries"] += 1
			"block": rec["blocks"] += 1
			"hurt": rec["hurts"] += 1
			"dodge": rec["dodges"] += 1
	if _step < 0 or _step >= _lesson["steps"].size():
		return
	if _step_hold > 0.0:
		_step_hold -= dt
		if _step_hold <= 0.0:
			_next_step()
		return
	var s: Dictionary = _lesson["steps"][_step]
	var g: Dictionary = s["goal"]
	var notes: Dictionary = s.get("notes", {})
	var done := false
	if String(g["type"]) == "spar":
		if _spar_hold > 0.0:
			_spar_hold -= dt
			if _spar_hold <= 0.0:
				if _spar_wins >= int(g["count"]):
					_spar_end()
					done = true
				else:
					_spar_begin()
		else:
			for e in events:
				if e["type"] == "wolf-down":
					_spar_result(true)
				elif e["type"] == "player-down":
					_spar_result(false)
		if not done:
			hud.set_prompt_status(_note, _progress_text(s))
			return
	if String(g["type"]) == "stance-seconds":
		_held = _held + dt if fight.p_stance else 0.0
		done = _held >= float(g["count"])
	match String(g["type"]):
		"find", "talk": done = _choice_done
		"reach": done = progress["place"] == g["place"]
		"hunt":
			for e in events:
				if e["type"] == "wolf-down":
					_choice_done = true
			done = _choice_done
	if String(g["type"]) in ["fell", "hold", "extract", "travel", "choose-party"]:
		for e in events:
			var t: String = e["type"]
			if notes.has(t):
				_note = notes[t]
			if t == "player-down" and _in_zone():
				_rescue()
				return
			if t == "field-open":
				hero["projected"] = true
			if t == "wolf-down" and String(g["type"]) == "fell":
				_count += 1
		match String(g["type"]):
			"fell":
				done = _count >= int(g["count"])
				if done:
					fight.respawn = false
					_clear_place()
			"hold":
				if _holding:
					_hold_t += dt
					done = _hold_t >= float(g["seconds"])
					if done:
						fight.respawn = false
						_clear_place()
			"extract", "travel", "choose-party":
				done = _choice_done
		if done and String(g["type"]) in ["fell", "hold"]:
			var ahead: Array = _doors.filter(func(d): return door_open(d))
			if not ahead.is_empty():
				_note = "The way on is open: %s." % String(ahead[0]["label"])
	for e in events:
		var t: String = e["type"]
		if notes.has(t):
			_note = notes[t]
		match String(g["type"]):
			"event":
				var want: Array = g["event"] if g["event"] is Array else [g["event"]]
				var ok := t in want
				if ok and g.has("tech"):
					var i := int(g["tech"]) - 1
					ok = i < fight.extra_techs.size() and e.get("id", "") == fight.extra_techs[i]["id"]
				if ok:
					_count += 1
					_note = ""
			"streak":
				if t in ["parry", "block"]:
					_count += 1
				elif t == "hurt":
					_count = 0
			"reach-hits":
				if t == "hit" and e.get("technique", false) and float(e.get("dist", 0.0)) >= float(g.get("distance", 2.5)):
					_count += 1
					_note = ""
				elif t == "hit" and e.get("technique", false):
					_note = "Too close: that one landed inside arm's reach."
	match String(g["type"]):
		"event", "streak", "reach-hits": done = _count >= int(g["count"])
		"will-full": done = fight.p_will >= float(Data.rules["field"]["willMax"]) - 0.5
		"stance-seconds": done = done or _held >= float(g["count"])
		"choose-weapon", "fell", "hold", "extract", "travel", "choose-party", "find", "talk", "reach", "hunt": done = done or (_choice_done and String(g["type"]) in ["choose-weapon", "extract", "travel", "choose-party", "find", "talk", "hunt"])
	hud.set_prompt_status(_note, _progress_text(s))
	if done:
		sfx.play("cue-hit", 1.0)
		hud.set_prompt_status("Done.", "")
		_step_hold = 1.0

func _finish_lesson() -> void:
	var lesson := _lesson
	if lesson.get("trouble", false):
		_finish_trouble()
		return
	progress["done"].append(lesson["id"])
	earn_marks("lesson", "Lesson %d, %s" % [int(lesson["number"]), lesson["title"]])
	save()
	hud.set_prompt("", "")
	fight.passive = true
	fight.allowed = []
	fight.p_lock = false
	world.lock_on = false
	fight.w_state = "idle"
	sfx.play("done")
	if lesson["id"] == "discipline" and genius:
		genius.studied(String(hero.get("discipline", "")), 3.0)
	if _in_zone():
		go("quad", true, "")
	say(lesson_instructor(lesson), lesson["outro"], func():
		_lesson = {}
		hud.play_ui.visible = false
		save())

# --- The rite ------------------------------------------------------------------

var _rite: RiteScene = null
var _naming := false
var _big := Label.new()
var _big_sub := Label.new()
var _pour_box := PanelContainer.new()
var _pour_label := RichTextLabel.new()
var _pour_bar := ProgressBar.new()
var _name_box := PanelContainer.new()
var _ui_built := false

func _build_rite_ui() -> void:
	if _ui_built:
		return
	_ui_built = true
	var root: Control = get_child(0)
	Style.label(_big, 120, Style.FG, "title", 10)
	_big.set_anchors_preset(Control.PRESET_CENTER)
	_big.position = Vector2(-700, -400)
	_big.custom_minimum_size = Vector2(1400, 0)
	_big.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_big.modulate.a = 0.0
	root.add_child(_big)
	Style.label(_big_sub, 24, Style.FG, "title_light", 6)
	_big_sub.set_anchors_preset(Control.PRESET_CENTER)
	_big_sub.position = Vector2(-700, -250)
	_big_sub.custom_minimum_size = Vector2(1400, 0)
	_big_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_big_sub.autowrap_mode = TextServer.AUTOWRAP_WORD
	_big_sub.modulate.a = 0.0
	root.add_child(_big_sub)
	_pour_box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_pour_box.custom_minimum_size = Vector2(640, 0)
	_pour_box.position = Vector2(-320, -190)
	_pour_box.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.034, 0.03, 0.88), Style.BRASS, 1, 16))
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 10)
	_pour_box.add_child(pv)
	_pour_label.bbcode_enabled = true
	_pour_label.fit_content = true
	_pour_label.scroll_active = false
	_pour_label.custom_minimum_size = Vector2(600, 0)
	Style.rich(_pour_label, 19, Style.FG, "body")
	pv.add_child(_pour_label)
	Style.bar_styles(_pour_bar, Style.GOLD)
	_pour_bar.custom_minimum_size = Vector2(600, 16)
	_pour_bar.max_value = 1.0
	_pour_bar.step = 0.0
	pv.add_child(_pour_bar)
	_pour_box.visible = false
	root.add_child(_pour_box)

func _start_rite() -> void:
	_build_rite_ui()
	_target = {}
	_prompt.visible = false
	_rite = RiteScene.new(self, hero)
	_rite.done.connect(_rite_done)
	_rite.start()

func _rite_done() -> void:
	progress["done"].append("rite")
	_rite = null
	world.cine = false
	save()
	# The hall comes back, with the genius in it.
	go("hearth", true, "")

func show_pour(on: bool, text: String) -> void:
	_pour_box.visible = on
	_pour_label.text = text
	_pour_bar.value = 0.0

func set_pour(k: float) -> void:
	_pour_bar.value = k

## A great word over the scene: the Shape, the form.
func title_card(text: String, sub: String, color: Color) -> void:
	_big.text = text
	_big.add_theme_font_size_override("font_size", 120 if text.length() <= 10 else (88 if text.length() <= 16 else 64))
	_big.add_theme_color_override("font_color", color.lightened(0.35))
	_big.add_theme_color_override("font_shadow_color", Color(color, 0.5))
	_big.add_theme_constant_override("shadow_outline_size", 30)
	_big.add_theme_constant_override("shadow_offset_x", 0)
	_big.add_theme_constant_override("shadow_offset_y", 0)
	_big_sub.text = sub
	_big.pivot_offset = Vector2(700, 70)
	_big.scale = Vector2(1.25, 1.25)
	var tw := _big.create_tween().set_parallel(true)
	tw.tween_property(_big, "modulate:a", 1.0, 0.25)
	tw.tween_property(_big, "scale", Vector2.ONE, 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(_big_sub, "modulate:a", 1.0, 0.6).set_delay(0.5)
	var out := _big.create_tween()
	out.tween_interval(3.4)
	out.tween_property(_big, "modulate:a", 0.0, 0.8)
	out.parallel().tween_property(_big_sub, "modulate:a", 0.0, 0.8)

## Name the genius: a box with its form's name already in it.
func ask_name(default_name: String, then: Callable) -> void:
	_naming = true
	for c in _name_box.get_children():
		c.queue_free()
	if _name_box.get_parent() == null:
		_name_box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
		_name_box.custom_minimum_size = Vector2(620, 0)
		_name_box.position = Vector2(-310, -230)
		_name_box.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.034, 0.03, 0.94), Style.BRASS, 1, 22))
		get_child(0).add_child(_name_box)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	_name_box.add_child(v)
	var l := Label.new()
	Style.label(l, 22, Style.GOLD, "title")
	l.text = "Name your genius"
	v.add_child(l)
	var hint := Label.new()
	Style.label(hint, 16, Style.DIM, "italic")
	hint.text = fill(String(Data.academy["rite"]["lines"]["name"]))
	v.add_child(hint)
	var e := LineEdit.new()
	e.text = default_name
	e.max_length = 20
	e.add_theme_font_size_override("font_size", 22)
	v.add_child(e)
	var b := Button.new()
	b.text = "This is its name"
	Style.button(b, true, 19)
	v.add_child(b)
	var finish := func():
		if not _naming:
			return
		_naming = false
		_name_box.visible = false
		if not auto:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		then.call(e.text)
	b.pressed.connect(finish)
	e.text_submitted.connect(func(_t): finish.call())
	_name_box.visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	e.call_deferred("grab_focus")
	e.call_deferred("select_all")
	if auto:
		get_tree().create_timer(1.0).timeout.connect(finish)

var _card: GeniusCard = null

## The genius's card, at the left of the screen.
func show_card(info: Dictionary, color: Color, title: String) -> void:
	hide_card()
	_card = GeniusCard.make(info, color, title)
	_card.position = Vector2(60, 70)
	get_child(0).add_child(_card)
	_card.modulate.a = 0.0
	_card.position.x -= 40
	var tw := _card.create_tween().set_parallel(true)
	tw.tween_property(_card, "modulate:a", 1.0, 0.5)
	tw.tween_property(_card, "position:x", 60.0, 0.6).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

func hide_card() -> void:
	if _card:
		_card.queue_free()
		_card = null

# --- A choice ----------------------------------------------------------------------

var _choice_box: PanelContainer = null

## A choice among a few things, each with a line about it; the autopilot takes the first.
func choose(title: String, options: Array, then: Callable) -> void:
	if _choice_box:
		_choice_box.queue_free()
	_choice_box = PanelContainer.new()
	_choice_box.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	_choice_box.custom_minimum_size = Vector2(520, 0)
	_choice_box.position = Vector2(-580, -200)
	_choice_box.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.034, 0.03, 0.95), Style.BRASS, 1, 20))
	get_child(0).add_child(_choice_box)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	_choice_box.add_child(v)
	var l := Label.new()
	Style.label(l, 22, Style.GOLD, "title")
	l.text = title
	v.add_child(l)
	var first: Button = null
	for o in options:
		var b := Button.new()
		b.text = "%s\n%s" % [o["label"], o.get("text", "")]
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.autowrap_mode = TextServer.AUTOWRAP_WORD
		Style.button(b, o.get("on", false), 17, "body")
		var id: String = o["id"]
		b.pressed.connect(func():
			sfx.play("ui-take", 1.0, -6.0)
			_choice_box.queue_free()
			_choice_box = null
			if not auto:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			then.call(id))
		v.add_child(b)
		if first == null or o.get("on", false):
			first = b
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if first:
		first.call_deferred("grab_focus")
	if auto:
		get_tree().create_timer(1.0).timeout.connect(func(): if _choice_box: (first as Button).pressed.emit())

# --- The line: zones, the post, extraction, the rescue team --------------------------------

func _in_zone() -> bool:
	return Data.academy["places"].get(progress["place"], {}).has("zone")

func _clear_place() -> void:
	if not progress.has("cleared"):
		progress["cleared"] = {}
	progress["cleared"][progress["place"]] = true
	world.open_doors = {}
	for d in _doors:
		if door_open(d):
			world.open_doors[d["to"]] = true
	world.place = ""
	world.set_place(progress["place"])
	fight.obstacles = world.obstacles
	world.set_allies(fight.allies)
	sfx.play("done")

## Take the post: the party regroups, and then the holding begins: the wolves come.
func _take_post() -> void:
	fight.allies_recover()
	_holding = true
	_hold_t = 0.0
	fight.respawn = true
	fight._spawn_wolf()
	fight.w_pos = fight._clamp_in(Vector2(7.0, 6.0))
	fight.p_lock = true
	world.lock_on = true
	world.show_wolf = true
	world._ring_wave(world._v3(fight.p_pos), Color(0.6, 0.8, 1.0), 4.0)
	title_card("THE POST IS YOURS", "hold it", Color(0.6, 0.8, 1.0))
	sfx.play("stance", 1.2)
	progress["record"]["posts_held"] = int(progress["record"].get("posts_held", 0)) + 1
	if genius:
		genius.gave_order("hold")

## The way out of the Green: the car, and the lesson's end.
func _extract() -> void:
	var s: Dictionary = _lesson["steps"][_step] if in_lesson() and _step < _lesson["steps"].size() else {}
	var lines: Array = s.get("goal", {}).get("lines", ["The car takes you back."])
	hud.set_prompt("", "")
	var award := String(s.get("goal", {}).get("award", ""))
	say("", lines, func():
		_choice_done = true
		progress["record"]["runs_out"] = int(progress["record"].get("runs_out", 0)) + 1
		earn_marks("exam" if award == "stage3" else "run", "the Field Examination" if award == "stage3" else "a run out on the Green")
		if award == "stage3":
			hero["stage"] = 3
			hero["projected"] = true
			progress["record"]["examined"] = true
			if genius:
				genius.milestone("gate")
				genius.day = maxi(genius.day, int(GeniusResonance.instar_rule(2)["minDay"]))
			title_card("STAGE THREE", "the Field Examination, passed", World.SHAPE_COLORS.get(hero["shape"], Color.WHITE))
			sfx.play("done")
		save())

## Down on the line: the rescue team carries you out, and the lesson waits for another night.
func _rescue() -> void:
	var r: Dictionary = _lesson.get("rescue", {})
	progress["record"]["rescued"] = int(progress["record"].get("rescued", 0)) + 1
	var lesson := _lesson
	_lesson = {}
	hud.set_prompt("", "")
	hud.set_prompt_status("", "")
	fight.allowed = []
	say("", r.get("lines", ["The rescue team carries you out."]), func():
		progress["cleared"] = {}
		save()
		go("quad", true, "")
		var ins := lesson_instructor(lesson)
		say(ins, ["Not tonight. Rest, and we go out again when you're ready."]))

## Choose the party, one classmate at a time.
func _pick_party(n: int) -> void:
	var chosen: Array = progress.get("party", [])
	if chosen.size() >= n:
		_choice_done = true
		return
	var opts: Array = []
	for c in cohort:
		if chosen.has(c["id"]):
			continue
		var t: Dictionary = Data.by_id(Data.academy["cohort"]["temperaments"], c["temperament"])
		opts.append({ "id": c["id"], "label": "%s  ·  %s  ·  %s" % [c["name"], String(c["shape"]).capitalize(), c["blood_name"]],
			"text": "%s. %s" % [String(c["city"]).capitalize(), Creation.weapon(c["weapon"])["name"]], "on": progress["met"].has(c["id"]) and opts.is_empty() })
	choose("Who comes with you? (%d of %d)" % [chosen.size() + 1, n], opts, func(id: String):
		progress["party"].append(id)
		if genius:
			for c in cohort:
				if c["id"] == id:
					genius.bonded("party")
		save()
		_pick_party(n))

## What the HUD says of where you are.
func place_label() -> String:
	if _in_zone():
		return "the Green  ·  the line"
	return "%s  ·  warded" % String(Data.academy["places"].get(progress["place"], {}).get("name", "the yard")).to_lower()

# --- The Gate ---------------------------------------------------------------------

var _gate: GateScene = null
var _reading_box: Control = null

func _start_gate() -> void:
	_build_rite_ui()
	_target = {}
	_prompt.visible = false
	_gate = GateScene.new(self, hero)
	_gate.done.connect(_gate_done)
	_gate.start()

func _gate_done() -> void:
	progress["done"].append("gate")
	progress["day"] = int(progress["day"]) + 1
	hero["settled"] = true
	# The Archive's name for what you are: the Journeyman archetype of your Shape and school.
	var arch := Marks.archetype_for(hero["shape"], hero.get("discipline", ""))
	if not arch.is_empty():
		hero["archetypes"] = [{ "archetype": arch["id"], "marks": int(progress["record"].get("marks", 0)), "rank": "journeyman", "takenDay": int(progress["day"]) }]
	hero["marks"] = int(progress["record"].get("marks", 0))
	Settings.mark_settled()
	_gate = null
	world.cine = false
	save()
	settled_sheet()

## The Reading laid out: three cards with the lines of the Tally that chose each, a choice,
## or "let it settle".
func show_reading(reading: Dictionary, then: Callable, heading := "The Reading: a Second Form", subheading := "") -> void:
	hide_reading()
	var col: Color = World.SHAPE_COLORS.get(hero["shape"], Color.WHITE)
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	var veil := ColorRect.new()
	veil.color = Color(0.02, 0.016, 0.016, 0.82)
	veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(veil)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.add_theme_constant_override("separation", 12)
	root.add_child(v)
	var title := Label.new()
	Style.label(title, 34, Style.FG, "title")
	title.text = heading
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(title)
	var sub := Label.new()
	Style.label(sub, 16, Style.DIM, "italic")
	var leads: Array = reading.get("lineLeads", []).slice(0, 3).map(func(l): return GeniusPage.LINE_WORDS.get(l["line"], String(l["line"])).to_lower())
	sub.text = subheading if subheading != "" else "Read from %s. Every one carries the Seed-mark and heritage from the First Form." % (", ".join(leads) if not leads.is_empty() else "the term")
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(sub)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 18)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(row)
	var cands: Array = reading["candidates"]
	for i in cands.size():
		var c: Dictionary = cands[i]
		var col_v := VBoxContainer.new()
		col_v.add_theme_constant_override("separation", 8)
		var info := c.duplicate()
		info["instar"] = 2 if int(reading.get("instar", 2)) >= 2 else 1
		info["name"] = c["name"]
		var card := GeniusCard.make(info, col, "CANDIDATE %d" % (i + 1))
		card.custom_minimum_size = Vector2(330, 0)
		col_v.add_child(card)
		var why := RichTextLabel.new()
		why.bbcode_enabled = true
		why.fit_content = true
		why.scroll_active = false
		why.custom_minimum_size = Vector2(330, 0)
		Style.rich(why, 14, Style.DIM, "italic")
		var reasons: Array = []
		for r in c.get("reasons", []):
			reasons.append("%s: %s" % [GeniusPage.LINE_WORDS.get(r["line"], String(r["line"])).to_lower(), String(r["key"]).replace(".", " · ").replace("family:", "").replace("tag:", "")])
		var her: Array = c.get("heritage", []).map(func(f): return Rite.feature_label(String(f)))
		why.text = ("Because of " + "; ".join(reasons) + "." if not reasons.is_empty() else "") + (("  Carries %s from the First Form." % ", ".join(her)) if not her.is_empty() else "")
		col_v.add_child(why)
		var b := Button.new()
		b.text = "This one"
		Style.button(b, i == 0, 18)
		b.pressed.connect(func():
			sfx.play("ui-take", 1.0, -6.0)
			hide_reading()
			then.call(i))
		col_v.add_child(b)
		row.add_child(col_v)
	var settle := Button.new()
	settle.text = "Let it settle on the best fit"
	Style.button(settle, false, 17)
	settle.pressed.connect(func():
		sfx.play("ui-take", 1.0, -6.0)
		hide_reading()
		then.call(-1))
	v.add_child(settle)
	_reading_box = root
	get_child(0).add_child(root)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if auto:
		get_tree().create_timer(1.5).timeout.connect(func(): if _reading_box: hide_reading(); then.call(-1))

func hide_reading() -> void:
	if _reading_box:
		_reading_box.queue_free()
		_reading_box = null
	if not auto:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

## The settled character: everything the Academy made, on one sheet.
func settled_sheet() -> void:
	var g := Genius.for_hero(hero)
	var b: Dictionary = Data.by_id(Data.bloods, hero["blood"]) if hero.get("blood", "") != "" else { "name": "unmarked" }
	var dk: Dictionary = Data.discipline_kits.get(hero.get("discipline", ""), { "name": String(hero.get("discipline", "")).capitalize() })
	var techs: Array = dk.get("techniques", []).map(func(t): return t["name"])
	var rec: Dictionary = progress["record"]
	var body := "[table=2]"
	for r in [["Blood", b["name"]], ["Shape", "%s  ·  Stage %d" % [String(hero["shape"]).capitalize(), int(hero.get("stage", 2))]],
			["School", "%s  ·  %s" % [dk["name"], Creation.weapon(hero["weapon"])["name"]]], ["Techniques", ", ".join([Data.kits[hero["shape"]]["technique"]["name"]] + techs)],
			["Pattern", Builder.sentence(hero["pattern"])],
			["Archetype", "%s, Journeyman  ·  %d Marks" % [Marks.archetype_for(hero["shape"], hero.get("discipline", "")).get("name", "none"), int(rec.get("marks", 0))]],
			["Declared", declaration_text()],
			["Genius", "%s, a %s (%s), %s" % [g.name, g.form_name(), String(g.body.get("expression", "")).capitalize(), g.instar_name()]],
			["The term", "%d parries, %d blocks, bitten %d; %d bouts won, %d lost; %d posts held, %d runs out%s" % [int(rec.get("parries", 0)), int(rec.get("blocks", 0)), int(rec.get("hurts", 0)), int(rec.get("spars_won", 0)), int(rec.get("spars_lost", 0)), int(rec.get("posts_held", 0)), int(rec.get("runs_out", 0)), ", carried out %d" % int(rec["rescued"]) if int(rec.get("rescued", 0)) > 0 else ""]]]:
		body += "[cell][color=#a8803f]%s[/color]   [/cell][cell]%s[/cell]" % [r[0], r[1]]
	body += "[/table]"
	var wu: Array = progress.get("writeup", [])
	if not wu.is_empty():
		body += "\n\n[i]%s[/i]" % "  ".join(wu)
	hud.show_screen("%s" % hero["name"], "Settled. Ready for the line.", body, [
		["Leave by the line  (to the title)", func(): leave.emit()],
		["Stay a while: walk the Academy", func(): hud.hide_screen(); go("quad", true, "")],
	])
	hud.play_ui.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if auto:
		get_tree().create_timer(2.0).timeout.connect(func(): if hud.screen.visible: leave.emit())

# --- The board: classmates' troubles ---------------------------------------------------

var auto_troubles := false
var _lost_at := Vector2.INF
var _lost_label := ""

func _step_goal_type() -> String:
	if not in_lesson() or _step < 0 or _step >= _lesson["steps"].size():
		return ""
	return String(_lesson["steps"][_step]["goal"]["type"])

func board_open() -> bool:
	return progress["done"].has(String(Data.academy["board"].get("opensAfter", "shape")))

## This run's troubles: `count` classmates with different troubles, drawn by the run's seed,
## kinds by temperament (data/academy.json, "board").
static func make_troubles(seed_value: int, cohort_in: Array) -> Array:
	var b: Dictionary = Data.academy["board"]
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value + 303
	var order := cohort_in.duplicate()
	_shuffle(order, rng)
	var out: Array = []
	var kinds_used := {}
	for c in order:
		var kind: String = b["byTemperament"].get(c["temperament"], "")
		if kind == "" or kinds_used.has(kind):
			continue
		kinds_used[kind] = true
		out.append({ "id": "trouble:%s" % c["id"], "kind": kind, "poster": c["id"] })
		if out.size() >= int(b.get("count", 3)):
			break
	return out

## The troubles still open (not done, not the one in hand).
func troubles_open() -> Array:
	var done: Array = progress.get("troubles_done", [])
	return make_troubles(int(progress["seed"]), cohort).filter(func(t): return not done.has(t["id"]))

func _classmate(id: String) -> Dictionary:
	for c in cohort:
		if c["id"] == id:
			return c
	return {}

func _read_board() -> void:
	var b: Dictionary = Data.academy["board"]
	var open := troubles_open()
	if progress.get("trouble", "") != "":
		say("", ["You have %s's trouble in hand already." % _classmate(progress["trouble"].trim_prefix("trouble:")).get("name", "a classmate")])
		return
	if open.is_empty():
		say("", ["Nothing on the board for you. The cohort's troubles are its own this week."])
		return
	var opts: Array = []
	for t in open:
		var c := _classmate(t["poster"])
		var ks: Dictionary = b["kinds"][t["kind"]]
		opts.append({ "id": t["id"], "label": "%s  ·  %s" % [ks["title"], c["name"]], "text": fill(ks["posting"], c) })
	choose("The board", opts, func(id: String): _take_trouble(id))

func _take_trouble(id: String) -> void:
	var b: Dictionary = Data.academy["board"]
	var t: Dictionary = {}
	for x in troubles_open():
		if x["id"] == id:
			t = x
	if t.is_empty():
		return
	var c := _classmate(t["poster"])
	var ks: Dictionary = b["kinds"][t["kind"]]
	progress["trouble"] = id
	save()
	say("", [fill(b["taken"], c)], func():
		_lesson = { "id": id, "trouble": true, "kind": t["kind"], "kind_spec": ks, "poster": c, "number": 0, "title": ks["title"],
			"place": progress["place"], "instructor": "varga", "steps": ks["steps"].duplicate(true), "intro": [], "outro": [] }
		hud.play_ui.visible = true
		hud.target.visible = false
		_step = -1
		_next_step())

func _pick_up() -> void:
	_choice_done = true
	world.set_marker(null)
	_lost_at = Vector2.INF
	sfx.play("cue-hit", 1.3)
	world.floater(world._v3(fight.p_pos, 2.2), "FOUND", Style.GOLD, 52, 1.2)

## A beast loose in the yard, wards up: a small hunt.
func _hunt_begin(beast: String, scale: float) -> void:
	var spec: Dictionary = Data.academy["places"][progress["place"]]
	var keep := fight.p_pos
	fight = Fight.new({ "hero": hero, "beast": beast, "passive": false, "respawn": false, "mercy": true, "allow_breach": false,
		"genius": genius if genius and genius.is_born() else null, "arena": Vector2(spec["size"][0], spec["size"][1]), "seed": randi(), "beast_health": roundf(float(Data.beast(beast)["health"]) * scale) })
	fight.obstacles = world.obstacles
	fight.p_pos = keep
	fight.w_pos = fight._clamp_in(keep + Vector2(7.0, 3.0))
	fight.p_lock = true
	world.set_foe({})
	world.lock_on = true
	world.show_wolf = true
	world.reset_feedback()
	hud.configure(fight, hero["name"])
	hud.target.visible = true
	title_card("LOOSE IN THE YARD", "the wards are up", Style.EMBER)

func _finish_trouble() -> void:
	var lesson := _lesson
	var c: Dictionary = lesson["poster"]
	if not progress.has("troubles_done"):
		progress["troubles_done"] = []
	progress["troubles_done"].append(lesson["id"])
	progress["trouble"] = ""
	progress["record"]["troubles"] = int(progress["record"].get("troubles", 0)) + 1
	if not progress.has("writeup_extra"):
		progress["writeup_extra"] = []
	progress["writeup_extra"].append(lesson["kind_spec"]["writeup"])
	earn_marks("quest", "%s's trouble" % c["name"])
	if genius:
		genius.bonded("classmate")
	_lesson = {}
	world.set_marker(null)
	_lost_at = Vector2.INF
	fight.allowed = []
	hud.set_prompt("", "")
	hud.set_prompt_status("", "")
	hud.play_ui.visible = _in_zone()
	sfx.play("done")
	save()

# --- The hearth's shade ---------------------------------------------------------------

var _shade_node: Node3D = null

## This run's shade: one of the dead, by the run's seed.
func shade() -> Dictionary:
	var all: Array = Data.shades()
	return all[int(progress["seed"]) % all.size()]

## A visit: the shade speaks, fires its Pattern for the hall (your genius witnesses it), and
## after enough visits accepts you and offers its graft for the Gate.
func _visit_shade() -> void:
	var sh: Dictionary = Data.academy["shade"]
	var sd := shade()
	var visits := int(progress.get("shade_visits", 0))
	var lines_all: Array = sh["visits"]
	var lines: Array = lines_all[mini(visits, lines_all.size() - 1)].map(func(l): return String(l).replace("{pattern_name}", sd["pattern"]["name"]))
	progress["shade_visits"] = visits + 1
	progress["record"]["talks"] += 1
	var fires := visits < lines_all.size() - 1
	say(sd["name"], lines, func():
		if fires:
			_shade_fires(sd)
		if visits + 1 == int(sh["acceptVisits"]) and genius:
			genius.offer_graft({ "id": "shade:" + sd["id"], "feature": sd["graftFeature"], "source": "shade:" + sd["id"] })
			genius.bonded("shade")
			progress["record"]["shade_accepted"] = true
			title_card("ACCEPTED", "the shade's graft waits for the Gate", Color(0.7, 0.8, 1.0))
			sfx.play("done")
		save())

## The Pattern fired for the hall: gold rings from the shade, and the genius takes it in.
func _shade_fires(sd: Dictionary) -> void:
	var sh: Dictionary = Data.academy["shade"]
	var at := Vector2(sh["at"][0], sh["at"][1])
	var n := int(sh["usesPerVisit"])
	var pattern := { "name": sd["pattern"]["name"], "form": sd["pattern"]["form"], "terms": [] }
	var made := {}
	for i in n:
		var tw := create_tween()
		tw.tween_interval(0.5 * i)
		tw.tween_callback(func():
			world._ring_wave(world._v3(at), World.C_GOLD, 3.5)
			world.burst(world._v3(at, 1.2), World.C_GOLD, 20, 4.0)
			sfx.play("cue-hit", 0.9 + 0.1 * i)
			world.genius_react("cue"))
		if genius:
			var m := genius.witness(pattern)
			if not m.is_empty():
				made = m
	if genius:
		var key := "%s|" % pattern["form"]
		var count := int(genius.witnessed.get(key, 0))
		var need := int(Data.rules["genius"]["shadowUses"])
		var tw2 := create_tween()
		tw2.tween_interval(0.5 * n + 0.3)
		tw2.tween_callback(func():
			world.floater(world._v3(fight.p_pos, 2.6), String(sh["witness"]).replace("{genius_name}", genius.name).replace("{pattern_name}", sd["pattern"]["name"]).replace("{n}", str(mini(count, need))).replace("{need}", str(need)).to_upper(), World.C_GOLD, 40, 2.4, 0.4)
			if not made.is_empty():
				world.floater(world._v3(fight.p_pos, 3.0), String(sh["shadow"]).replace("{genius_name}", genius.name).replace("{pattern_name}", sd["pattern"]["name"]).to_upper(), Color(0.8, 0.9, 1.0), 48, 3.0, 0.3)
				sfx.play("pattern", 1.2))
		save()

# --- Commencement: the declaration ---------------------------------------------------

func declaration_text() -> String:
	var dcl: Dictionary = hero.get("declaration", {})
	match String(dcl.get("kind", "")):
		"join": return "joined %s (%s)" % [dcl.get("guild_name", "a guild"), dcl.get("charter", "")]
		"found": return "a founding promised with %s" % " and ".join(dcl.get("founders", []))
		"free": return "a Free Lance"
	return "nothing yet"

## The recruiters and the cohort on the platform: join, found, or go free.
func declare(then: Callable) -> void:
	var cm: Dictionary = Data.academy.get("commencement", {})
	if cm.is_empty():
		then.call()
		return
	var p := party()
	var a: String = p[0]["name"] if p.size() > 0 else cohort[0]["name"]
	var b: String = p[1]["name"] if p.size() > 1 else cohort[1]["name"]
	var opts: Array = []
	for g in cm["guilds"]:
		opts.append({ "id": "join:" + g["id"], "label": "%s  ·  %s" % [g["name"], g["charter"]], "text": g["line"] })
	opts.append({ "id": "found", "label": "Found with %s and %s" % [a, b], "text": String(cm["lines"]["found"]).replace("{a}", a).replace("{b}", b) })
	opts.append({ "id": "free", "label": "Leave as a Free Lance", "text": cm["lines"]["free"] })
	say("", [cm["lines"]["intro"]], func():
		choose("Commencement", opts, func(id: String):
			var line := ""
			if id.begins_with("join:"):
				var g: Dictionary = Data.by_id(cm["guilds"], id.trim_prefix("join:"))
				hero["declaration"] = { "kind": "join", "guild": g["id"], "guild_name": g["name"], "charter": g["charter"] }
				line = String(cm["lines"]["declared_join"]).replace("{guild}", g["name"]).replace("{charter}", g["charter"])
			elif id == "found":
				hero["declaration"] = { "kind": "found", "founders": [a, b], "founder_ids": p.map(func(c): return c["id"]) }
				line = String(cm["lines"]["declared_found"]).replace("{a}", a).replace("{b}", b)
			else:
				hero["declaration"] = { "kind": "free" }
				line = cm["lines"]["declared_free"]
			progress["record"]["declared"] = hero["declaration"]["kind"]
			save()
			say("", [line], then)))
