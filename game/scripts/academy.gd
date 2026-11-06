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
	var opts := { "hero": hero, "beast": "millstone", "passive": true, "respawn": true, "mercy": true, "allow_breach": false,
		"arena": Vector2(spec["size"][0], spec["size"][1]) }
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
	world.set_foe({})
	world.build_hero(hero)
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
	hud.play_ui.visible = false
	_show_place(spec["name"])
	save()

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
	if in_lesson() or _target.is_empty():
		return
	sfx.play("ui-take", 1.0, -6.0)
	match _target["kind"]:
		"door": _use_door(_target["door"])
		"rest": _rest_now()
		"instructor": _talk_instructor(_target["id"])
		"classmate": _talk_classmate(_target["c"])

func door_open(d: Dictionary) -> bool:
	if not d.has("locked"):
		return true
	match String(d.get("opensWhen", "")):
		"rested": return rested_on("hold") or progress["done"].has("rite")
	return false

func _use_door(d: Dictionary) -> void:
	if not door_open(d):
		say("", [d["locked"]])
		return
	var from: String = progress["place"]
	go(d["to"], false, from)

func _talk_instructor(id: String) -> void:
	var data: Dictionary = Data.by_id(Data.academy["instructors"], id)
	progress["record"]["talks"] += 1
	var lines: Dictionary = data["lines"]
	# The Instructor who teaches the next lesson starts it.
	for lesson in Data.academy["lessons"]:
		if lesson_instructor(lesson) == id and not progress["done"].has(lesson["id"]) and lesson["place"] == progress["place"] and lesson_available(lesson):
			var intro: Array = [lines.get("before:" + String(lesson["id"]), "")] + lesson["intro"]
			say(id, intro.filter(func(x): return x != ""), func(): _start_lesson(lesson))
			return
	var rite: Dictionary = Data.academy["rite"]
	if id == rite["instructor"] and progress["place"] == rite["place"] and not progress["done"].has("rite"):
		_start_rite()
		return
	var key := _stage_key()
	say(id, [lines.get(key, lines["default"])])

func _talk_classmate(c: Dictionary) -> void:
	var t: Dictionary = Data.by_id(Data.academy["cohort"]["temperaments"], c["temperament"])
	progress["record"]["talks"] += 1
	var first: bool = not progress["met"].has(c["id"])
	if first:
		progress["met"].append(c["id"])
	var line: String = t["lines"]["greet"]
	if not first:
		for key in [_stage_key(), "after:rite" if progress["done"].has("rite") else "", "after:hold" if progress["done"].has("hold") else ""]:
			if key != "" and t["lines"].has(key):
				line = t["lines"][key]
				break
	say(c, [line], save)

## Where the term has got to, for which lines people say.
func _stage_key() -> String:
	var order := ["hold", "rite", "shape"]
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
		if progress["done"].has(lesson["id"]):
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

func lesson_available(lesson: Dictionary) -> bool:
	var req: Dictionary = lesson.get("requires", {})
	for d in req.get("done", []):
		if not progress["done"].has(d):
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
			if not progress["done"].has(lesson["id"]):
				return "rest" if lesson.get("requires", {}).has("rested_after") and not rested_on(lesson["requires"]["rested_after"]) else ""
		# Nothing more is built yet: the day still ends in the dormitory.
		return "rest" if not rested_on(last_done()) else ""
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
		save())

# --- Each frame -----------------------------------------------------------------

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
	var g: Dictionary = hero.get("genius", {})
	return "Day %d · %s walks with you. Next: Lesson 4, Discipline (the next part to be built)." % [day, g.get("name", "Your genius")]

## The lesson asks for stillness now (Contain): the autopilot keeps its hands down.
func wants_still() -> bool:
	return bot_mode() == "still"

## What the autopilot should be doing in the lesson: still, guard, stance, technique or fight.
func bot_mode() -> String:
	if not in_lesson() or _step < 0 or _step >= _lesson["steps"].size():
		return "walk"
	var g: Dictionary = _lesson["steps"][_step]["goal"]
	match String(g["type"]):
		"will-full", "choose-weapon": return "still"
		"stance-seconds": return "stance"
		"spar": return "fight"
		"event":
			var want: Array = g["event"] if g["event"] is Array else [g["event"]]
			return "technique" if "technique" in want else "guard"
	return "guard"

## The technique the autopilot should use now, and the action that presses it.
func bot_tech() -> Dictionary:
	var g: Dictionary = _lesson["steps"][_step]["goal"]
	if g.has("tech") and int(g["tech"]) - 1 < fight.extra_techs.size():
		return fight.extra_techs[int(g["tech"]) - 1]
	return fight.tech

func bot_action() -> String:
	var g: Dictionary = _lesson["steps"][_step]["goal"]
	return "tech%d" % int(g["tech"]) if g.has("tech") else "technique"

func busy() -> bool:
	return talking() or _rite != null or _naming or _choice_box != null

func in_rite() -> bool:
	return _rite != null

func in_lesson() -> bool:
	return not _lesson.is_empty()

func update(events: Array, dt: float) -> void:
	_objective.text = objective()
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
	if not in_lesson():
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
	_prompt.visible = not _target.is_empty()
	if _prompt.visible:
		match _target["kind"]:
			"door": _prompt_label.text = ("E   " + ("Enter " if door_open(_target["door"]) else "Try ") + String(_target["door"]["label"]))
			"rest": _prompt_label.text = "E   Rest in %s" % _rest["label"]
			_: _prompt_label.text = "E   Talk to %s" % _target["name"]

## Automated checks: where the autopilot walks next, and whether to act there.
func auto_move() -> Vector2:
	if talking() or in_lesson() or in_rite():
		return Vector2.ZERO
	var goal := Vector2.INF
	var place: String = progress["place"]
	var want_place := ""
	match next_need():
		"rest": want_place = "dorm"
		"rite": want_place = "hearth"
		_:
			var nl := next_lesson()
			want_place = nl["place"] if not nl.is_empty() else ""
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

func _start_lesson(lesson: Dictionary) -> void:
	_lesson = lesson
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
	if _spar_mode == "instructor":
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
	if setup.get("spar", false):
		_spar_mode = "instructor" if str(setup["spar"]) == "instructor" else "cohort"
		_spar_rung = 0
		_spar_wins = 0
		_spar_begin()
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
		"event", "streak": return "%d / %d" % [_count, int(g["count"])]
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
	match String(g["type"]):
		"event", "streak": done = _count >= int(g["count"])
		"will-full": done = fight.p_will >= float(Data.rules["field"]["willMax"]) - 0.5
		"stance-seconds": done = done or _held >= float(g["count"])
		"choose-weapon": done = _choice_done
	hud.set_prompt_status(_note, _progress_text(s))
	if done:
		sfx.play("cue-hit", 1.0)
		hud.set_prompt_status("Done.", "")
		_step_hold = 1.0

func _finish_lesson() -> void:
	var lesson := _lesson
	progress["done"].append(lesson["id"])
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
