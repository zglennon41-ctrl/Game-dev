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
		progress = { "seed": randi() % 1000000, "arrived": false, "done": [], "met": [], "day": 1, "rested": false,
			"place": "quad", "record": { "parries": 0, "blocks": 0, "hurts": 0, "dodges": 0, "talks": 0 } }
		hero["academy"] = progress
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
	world.build_hero(hero)
	world.reset_feedback()
	world.cam_yaw = atan2(spawn.x, spawn.y) if spawn.length() > 0.1 else 0.0
	world.snap_camera_behind(fight)
	for ins in spec["instructors"]:
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
		"rested": return progress.get("rested", false)
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
		if lesson["instructor"] == id and not progress["done"].has(lesson["id"]) and lesson["place"] == progress["place"]:
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
	if progress["done"].has("rite"):
		return "after:rite"
	if progress.get("rested", false):
		return "before:rite"
	if progress["done"].has("hold"):
		return "after:hold"
	return "before:hold"

func _rest_now() -> void:
	if not progress["done"].has("hold"):
		say("", ["It is too early to sleep. The Yardmaster is waiting in the yard."])
		return
	var r: Dictionary = Data.academy["rest"]
	if progress.get("rested", false):
		say("", ["You are rested. The hearth is waiting."])
		return
	say("", r["lines"] + [r["next"]], func():
		progress["rested"] = true
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
	if not progress.get("rested", false):
		return "Rest in the Dormitory (the east door of the quad)."
	if not progress["done"].has("rite"):
		if progress["place"] == "hearth":
			return "Day %d · The rite: speak to Instructor Varga at the bowl." % int(progress["day"])
		return "Day %d · The rite: go to the Hearth Hall (the north door of the quad)." % int(progress["day"])
	var g: Dictionary = hero.get("genius", {})
	return "Day %d · %s walks with you. Next: Lesson 3, Shape (the next part to be built)." % [int(progress["day"]), g.get("name", "Your genius")]

## The lesson asks for stillness now (Contain): the autopilot keeps its hands down.
func wants_still() -> bool:
	return in_lesson() and _step >= 0 and _step < _lesson["steps"].size() and _lesson["steps"][_step]["goal"]["type"] == "will-full"

func busy() -> bool:
	return talking() or _rite != null or _naming

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
	if progress.get("rested", false) and not progress["done"].has("rite"):
		if place == "quad":
			goal = Vector2(0, -11) * 0.86
		elif place == "hearth":
			goal = _people.filter(func(p): return p["kind"] == "instructor")[0]["pos"]
		elif place == "dorm":
			goal = Vector2(-7, 0) * 0.86
	if not progress["done"].has("hold"):
		if place == "quad":
			# Greet two classmates on the way, then the west door.
			var unmet := _people.filter(func(p): return p["kind"] == "classmate" and not progress["met"].has(p["id"]))
			goal = unmet[0]["pos"] if progress["met"].size() < 2 and not unmet.is_empty() else Vector2(-15, 0) * 0.86
		elif place == "yard":
			goal = _people[0]["pos"]
	elif not progress.get("rested", false):
		goal = Vector2(15, 4) * 0.86 if place == "quad" else (Vector2(_rest["at"][0], _rest["at"][1]) if place == "dorm" else Vector2(-11, 0) * 0.86)
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
	var spec: Dictionary = Data.academy["places"][lesson["place"]]
	var ins: Dictionary = Data.by_id(Data.academy["instructors"], lesson["instructor"])
	var p := fight.p_pos
	fight = Fight.new({ "hero": hero, "beast": ins.get("genius", {}).get("beast", "millstone"), "passive": true, "respawn": true, "genius": genius if genius and genius.is_born() else null,
		"mercy": true, "allow_breach": false, "arena": Vector2(spec["size"][0], spec["size"][1]), "seed": randi() })
	fight.allowed = lesson.get("allow", [])
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
	hud.play_ui.visible = true
	hud.target.visible = false
	_prompt.visible = false
	_step = -1
	_next_step()

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
	hud.set_prompt("%d/%d · %s" % [_step + 1, steps.size(), s["title"]], fill(s["text"]))
	hud.set_prompt_status("", _progress_text(s))

func _progress_text(s: Dictionary) -> String:
	var g: Dictionary = s["goal"]
	match String(g["type"]):
		"event", "streak": return "%d / %d" % [_count, int(g["count"])]
		"will-full": return "Will %d / %d" % [roundi(fight.p_will), int(Data.rules["field"]["willMax"])]
	return ""

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
	for e in events:
		var t: String = e["type"]
		if notes.has(t):
			_note = notes[t]
		match String(g["type"]):
			"event":
				var want: Array = g["event"] if g["event"] is Array else [g["event"]]
				if t in want:
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
	say(lesson["instructor"], lesson["outro"], func():
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
