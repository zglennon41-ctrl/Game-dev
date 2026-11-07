## The Academy at Alexandria: the solo, offline act every character plays before the server.
## Walk the grounds (the quad, the yard, the dormitory), meet the cohort of twelve generated for
## this run, talk with the Instructors, take the lessons. No one dies here: the wards hold.
## Words and places live in data/academy.json. Progress lives on the hero, under "academy".
class_name Academy
extends CanvasLayer

signal leave   # back to the title
signal open_builder(pattern: Dictionary)   # the Hearthkeeper sits you down with your Pattern

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
		progress = { "seed": fixed_seed if fixed_seed >= 0 else randi() % 1000000, "arrived": false, "done": [], "met": [], "day": 1, "rested_after": "",
			"place": "quad", "record": { "parries": 0, "blocks": 0, "hurts": 0, "dodges": 0, "talks": 0 } }
		hero["academy"] = progress
	# Saves from before rest was per stage.
	if progress.has("rested") and not progress.has("rested_after"):
		progress["rested_after"] = "hold" if progress["rested"] else ""
		progress.erase("rested")
	cohort = Academy.make_cohort(int(progress["seed"]), hero)
	genius = Genius.for_hero(hero)
	visible = true
	_carrying = false
	if progress.get("quest", {}) is Dictionary and not progress.get("quest", {}).is_empty():
		# A posting in hand from last time: the run starts over from the quad.
		progress["place"] = "quad"
		progress["cleared"] = {}
	go(String(progress.get("place", "quad")), not bool(progress["arrived"]))
	if progress.get("quest", {}) is Dictionary and not progress.get("quest", {}).is_empty():
		_begin_quest(progress["quest"])
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
			"body": bodies[rng.randi() % bodies.size()], "weapon": weapons[rng.randi() % weapons.size()]["id"],
			"look": random_look(rng) })
	return out

## A classmate's look, drawn with the cohort: most go bare-headed so their faces and hair show.
static func random_look(rng: RandomNumberGenerator) -> Dictionary:
	var L: Dictionary = Data.creation.get("look", {})
	var hairs: Array = L.get("hair", ["crop"])
	var beards: Array = L.get("beards", ["none"])
	var cols: Array = L.get("hairColors", { "brown": [] }).keys()
	var sts: Array = L.get("statures", { "middling": 1.0 }).values()
	return { "headgear": rng.randf() < 0.3, "cape": rng.randf() < 0.6, "cape_color": ["city", "plain", "shape"][rng.randi() % 3],
		"hair": hairs[rng.randi() % hairs.size()], "beard": beards[rng.randi() % beards.size()] if rng.randf() < 0.35 else beards[0],
		"hair_color": cols[rng.randi() % cols.size()], "stature": sts[rng.randi() % sts.size()] }

static func _shuffle(a: Array, rng: RandomNumberGenerator) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = a[i]
		a[i] = a[j]
		a[j] = t

## Walk into a place: build it, fill it with the people who are there, put the hero at the door.
## A place by id: the Academy's own (data/academy.json) or an area of a zone ("green/cutting"),
## drawn for this run and this day.
func place_spec(id: String) -> Dictionary:
	if Data.academy["places"].has(id):
		return Data.academy["places"][id]
	if Zones.is_zone(id):
		return Zones.area_place(id, int(progress.get("seed", 0)) + int(progress.get("day", 1)) * 7)
	return {}

## Automated checks print what the Academy does (--debug), and may fix a fresh run's seed.
var debug := OS.get_cmdline_user_args().has("--debug")
var fixed_seed := -1

func go(place_id: String, quiet := false, from := "") -> void:
	var spec: Dictionary = place_spec(place_id)
	if debug:
		print("GO %s from %s (lesson %s step %d)" % [place_id, from, _lesson.get("id", ""), _step])
	progress["place"] = place_id
	# The shade stays at its hearth.
	if _shade_node:
		_shade_node.queue_free()
		_shade_node = null
	world.open_doors = {}
	for d in spec["doors"]:
		if door_open(d):
			world.open_doors[d["to"]] = true
	world.place = ""
	world.set_place(place_id, spec)
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
	var named: Dictionary = {}
	if not zone.is_empty():
		opts = { "hero": hero, "beast": zone["beast"], "passive": false, "respawn": zone.get("respawn", true), "mercy": false, "allow_breach": false,
			"arena": Vector2(spec["size"][0], spec["size"][1]), "seed": randi(), "allies": party(), "pack": zone.get("pack", []) }
		# A hunt's named beast holds its area in place of the zone's elite.
		if in_lesson() and _lesson.get("quest", false) and String(_lesson.get("named_at", "")) == place_id:
			named = _lesson["named"]
			opts["beast"] = named["beast"]
			opts["beast_health"] = roundf(float(Data.beast(named["beast"])["health"]) * float(named.get("health", 1.5)))
			opts["respawn"] = false
	if genius and genius.is_born():
		opts["genius"] = genius
	fight = Fight.new(opts)
	if not named.is_empty():
		var escaped := named_escapes(String(named["id"]))
		fight.beast = fight.beast.duplicate(true)
		fight.beast["name"] = named["name"]
		fight.beast["title"] = "named  ·  it remembers" if escaped == 0 else ("named  ·  escaped you once" if escaped == 1 else "named  ·  escaped you %d times" % escaped)
		fight.beast["modelScale"] = float(fight.beast.get("modelScale", 1.0)) * float(named.get("scale", 1.2))
		fight.beast["health"] = roundf(float(fight.beast["health"]) * (1.0 + 0.15 * escaped))
		fight.w_hp = float(fight.beast["health"])
		fight.beast["walkSpeed"] = float(fight.beast["walkSpeed"]) * (1.0 + 0.1 * escaped)
		fight.beast["gallopSpeed"] = float(fight.beast["gallopSpeed"]) * (1.0 + 0.08 * escaped)
		fight.w_named = true
	if not zone.is_empty() and in_lesson() and _lesson.has("passenger"):
		var ps: Dictionary = _lesson["passenger"].duplicate()
		ps["temperament"] = "scared"
		var pa := Fight.make_ally(ps, spawn + Vector2(-1.6, 0.0))
		pa["hp"] = 70.0
		pa["hp_max"] = 70.0
		pa["passenger"] = true
		fight.allies.append(pa)
	if _carrying:
		_apply_carry()
	fight.p_pos = spawn
	fight.p_facing = (-spawn).angle() if spawn.length() > 0.1 else -PI / 2.0
	fight.w_state = "absent"
	world.show_wolf = false
	world.lock_on = false
	world.portrait = false
	world.genius_visible = true
	world.set_foe({ "wolf_scale": float(fight.beast.get("modelScale", 1.0)), "model": String(fight.beast.get("model", "")) })
	world.set_allies(fight.allies)
	world.build_hero(hero)
	if not zone.is_empty():
		for al in fight.allies:
			al["pos"] = spawn + Vector2(-1.2 - 0.6 * fight.allies.find(al), 1.4 * (1 if fight.allies.find(al) % 2 == 0 else -1))
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
		if ins.has("after") and not progress["done"].has(String(ins["after"])):
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
	var smith: Dictionary = Data.gear.get("smith", {})
	if place_id == "yard" and not smith.is_empty() and progress["done"].has("discipline"):
		var sm_at := Vector2(smith["at"][0], smith["at"][1])
		world.add_figure(smith["body"], sm_at, (spawn - sm_at).angle(), smith["name"], smith["title"], smith["weapon"])
		_people.append({ "kind": "smith", "id": "smith", "name": smith["name"], "pos": sm_at })
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
		var here: Array = cohort
		if progress["done"].has("rite"):
			here = cohort.filter(func(c): return _classmate_here(c, place_id))
		for i in mini(here.size(), spots.size()):
			var c: Dictionary = here[i]
			var at := Vector2(spots[i][0], spots[i][1])
			var fig := world.add_figure(c["body"], at, (Vector2.ZERO - at).angle() + randf_range(-0.6, 0.6), c["name"],
				"%s · %s" % [c["blood_name"], String(c["shape"]).capitalize()], c["weapon"], Color(0, 0, 0, 0), c.get("look", {}))
			_people.append({ "kind": "classmate", "id": c["id"], "name": c["name"], "pos": at, "c": c })
	fight.obstacles = world.obstacles
	hud.hide_screen()
	hud.configure(fight, hero["name"])
	hud.play_ui.visible = not zone.is_empty()
	if not zone.is_empty():
		hud.target.visible = true
	_show_place(spec["name"])
	sfx.set_ambience("wild" if not zone.is_empty() else "hall")
	var mus: Node = get_parent().get("music") if get_parent() and "music" in get_parent() else null
	if mus:
		mus.call("play_for", place_id)
	# Arrive out of the dark.
	if _fade.is_inside_tree():
		_fade.modulate.a = 1.0
		var tw := _fade.create_tween()
		tw.tween_interval(0.15)
		tw.tween_property(_fade, "modulate:a", 0.0, 0.7).set_trans(Tween.TRANS_SINE)
	save()

## Marks earned: counted on the record, logged by day, and shown as they land.
func earn_marks(what: String, label: String) -> void:
	earn_marks_n(Marks.academy(what), label)

func earn_marks_n(n: int, label: String) -> void:
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
		sub = c["sub"] if c.has("sub") else "%s · %s · %s" % [c.get("blood_name", ""), String(c.get("shape", "")).capitalize(), String(c.get("city", "")).capitalize()]
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
		t = t.replace("{my_name}", String(c.get("name", ""))).replace("{my_shape}", String(c.get("shape", "")).capitalize()).replace("{my_blood}", String(c.get("blood_name", ""))).replace("{my_city}", String(c.get("city", "")).capitalize())
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
		"smith": _smith()
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
		# The car only leaves when the run says so: the extraction step, or no run at all.
		if in_lesson() and _step_goal_type() != "extract":
			say("", ["Not yet. %s" % objective()])
			return
		if not in_lesson():
			say("", ["The car is not here for you tonight."])
			return
		_extract()
		return
	go(d["to"], false, from)

func _talk_instructor(id: String) -> void:
	var data: Dictionary = Data.by_id(Data.academy["instructors"], id)
	progress["record"]["talks"] += 1
	if in_lesson():
		var st: Dictionary = _lesson["steps"][_step] if _step >= 0 and _step < _lesson["steps"].size() else {}
		if _lesson.get("quest", false) and st.get("goal", {}).get("type", "") == "talk" and String(st["goal"].get("who", "")) == id:
			_choice_done = true
			say(id, [fill(String(_lesson["posting"].get("thanks", data["lines"]["default"])))])
			return
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
	if id == _school_instructor() and progress["done"].has("discipline") and next_need() != "gate":
		_teach(id)
		return
	if id == "keeper" and progress["done"].has("discipline"):
		var L: Dictionary = Data.academy.get("mastery", {}).get("lines", {})
		say(id, [String(L.get("keeperIntro", "")).replace("{pattern}", Builder.sentence(hero["pattern"]))], func():
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			open_builder.emit(hero["pattern"]))
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
	var sch: Dictionary = Data.academy["cohort"].get("schedule", {})
	if not first and away_today(int(progress["day"]) - 1).has(c["id"]):
		line = sch.get("lines", {}).get("backFromAway", line)
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
			if not gate_ready():
				return "board"
			return "gate" if rested_on("project") else "rest"
		return ""
	return ""

## The Gate opens after the term's postings are done: ten, with one of each type the term has
## posted (data/academy.json, gate.requires).
func gate_ready() -> bool:
	return gate_short() == 0 and gate_types_missing().is_empty()

func gate_short() -> int:
	var req: Dictionary = Data.academy["gate"].get("requires", {})
	return maxi(0, int(req.get("postings", 0)) - progress.get("quests_done", []).size())

func gate_types_missing() -> Array:
	var req: Dictionary = Data.academy["gate"].get("requires", {})
	if not req.get("eachType", false):
		return []
	var done_types := {}
	for t in progress.get("quest_types_done", []):
		done_types[t] = true
	return progress.get("quest_types_seen", []).filter(func(t): return not done_types.has(t))

## Whether you may sleep now: after a lesson, once; in the board phase, once the day's work is
## done (a posting or a trouble finished today, or nothing left on the board). "" when you may,
## else the key of the line that says why not (data/academy.json, rest).
static func rest_reason_for(prog: Dictionary, need: String, open_postings: int) -> String:
	var last: String = prog["done"].back() if not prog["done"].is_empty() else ""
	if last == "":
		return "too_early"
	if need == "board":
		return "" if int(prog.get("worked_day", 0)) == int(prog["day"]) or open_postings == 0 else "board_waits"
	return "already" if String(prog.get("rested_after", "")) == last else ""

func rest_reason() -> String:
	return rest_reason_for(progress, next_need(), postings_open().size())

func _rest_now() -> void:
	var r: Dictionary = Data.academy["rest"]
	var last := last_done()
	var why := rest_reason()
	if why != "":
		say("", [r.get(why, r["already"])])
		return
	# After the last lesson the mornings are the board's, until the Gate's postings are done.
	var next_key := "board" if last == "project" and not gate_ready() else last
	var next_line: String = r["next"].get(next_key, "") if r["next"] is Dictionary else String(r["next"])
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
	if in_lesson() and _lesson.get("quest", false):
		var st: Dictionary = _lesson["steps"][_step] if _step >= 0 and _step < _lesson["steps"].size() else {}
		return "%s · %s" % [_lesson["title"], st.get("title", "")]
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
		"board":
			var n := gate_short()
			var missing := gate_types_missing()
			var kinds := ("" if missing.is_empty() else "  (still to do: %s)" % ", ".join(missing.map(func(t): return String(Data.quests["types"][t]["name"]).to_lower())))
			var sleep := "  ·  rest when the day's work is done" if rest_reason() == "" else ""
			return "Day %d · %s%s%s" % [day, String(Data.academy["gate"]["lines"].get("not_yet", "The Gate waits: {n} more posting{s}.")).replace("{n}", str(n)).replace("{s}", "" if n == 1 else "s"), kinds, sleep]
		"rite":
			if progress["place"] == "hearth":
				return "Day %d · The rite: speak to Instructor Varga at the bowl." % day
			return "Day %d · The rite: go to the Hearth Hall (the north door of the quad)." % day
	var nl := next_lesson()
	if not nl.is_empty():
		var ins: Dictionary = Data.by_id(Data.academy["instructors"], lesson_instructor(nl))
		var place: Dictionary = place_spec(nl["place"])
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
		"will-full", "choose-weapon", "choose-party", "travel", "decide": return "still"
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

## Technique grades: every use counts; crossing a grade is said aloud.
func _count_technique(id: String) -> void:
	if not hero.has("technique_use"):
		hero["technique_use"] = {}
	var before: String = fight.grade_of(id)["id"]
	hero["technique_use"][id] = int(hero["technique_use"].get(id, 0)) + 1
	var after: Dictionary = fight.grade_of(id)
	if after["id"] != before:
		var tname := id
		for t in [fight.tech] + fight.extra_techs:
			if t["id"] == id:
				tname = t["name"]
		title_card(String(after["name"]).to_upper(), tname, Style.GOLD)
		sfx.play("cue-hit", 1.3)

## The techniques the school may still teach, and how many the hero may know now.
func techniques_allowed() -> int:
	var m: Dictionary = Data.academy.get("mastery", {})
	var dk: Dictionary = Data.discipline_kits.get(hero.get("discipline", ""), {})
	var all: int = dk.get("techniques", []).size()
	return mini(all, 3 + int(progress["record"].get("marks", 0)) / maxi(1, int(m.get("learnEveryMarks", 3))))

func techniques_known() -> Array:
	if not hero.has("techniques_known"):
		hero["techniques_known"] = hero.get("techniques", []).duplicate()
	return hero["techniques_known"]

func _school_instructor() -> String:
	for ins in Data.academy["places"]["yard"]["instructors"]:
		if ins.get("discipline", "") == hero.get("discipline", ""):
			return ins["id"]
	return ""

## The school's instructor: another technique when Marks allow, and the three for the hand.
func _teach(id: String) -> void:
	var m: Dictionary = Data.academy.get("mastery", {})
	var L: Dictionary = m.get("lines", {})
	var dk: Dictionary = Data.discipline_kits.get(hero.get("discipline", ""), {})
	var known := techniques_known()
	if known.size() < techniques_allowed():
		var opts: Array = []
		for t in dk["techniques"]:
			if not known.has(t["id"]):
				opts.append({ "id": t["id"], "label": t["name"], "text": "%s\n[i]%d Will  ·  %.1f s[/i]" % [t["text"], int(t["will"]), float(t["cooldown"])] })
		say(id, [L.get("learn", "Which?")], func():
			choose("The school's techniques  ·  %d of %d known" % [known.size(), dk["techniques"].size()], opts, func(tid: String):
				techniques_known().append(tid)
				var tname := ""
				for t in dk["techniques"]:
					if t["id"] == tid:
						tname = t["name"]
				progress["record"]["techniques_learned"] = int(progress["record"].get("techniques_learned", 0)) + 1
				if genius:
					genius.studied(String(hero.get("discipline", "")), 1.0)
				save()
				say(id, [String(L.get("learned", "{tech} is yours.")).replace("{tech}", tname)], func(): _set_slots(id))))
		return
	if known.size() > int(m.get("slots", 3)):
		_set_slots(id)
		return
	say(id, [L.get("nothingNew", "Nothing new yet.")])

## Choose the three techniques for the hand, one at a time.
func _set_slots(id: String, picked: Array = []) -> void:
	var m: Dictionary = Data.academy.get("mastery", {})
	var dk: Dictionary = Data.discipline_kits.get(hero.get("discipline", ""), {})
	var n := int(m.get("slots", 3))
	var known := techniques_known()
	if known.size() <= n:
		return
	if picked.size() >= n:
		hero["techniques"] = picked
		save()
		go(progress["place"], true, "")
		sfx.play("done")
		return
	var opts: Array = []
	for t in dk["techniques"]:
		if known.has(t["id"]) and not picked.has(t["id"]):
			var g: Dictionary = fight.grade_of(t["id"])
			opts.append({ "id": t["id"], "label": "%s  ·  %s" % [t["name"], g["name"]], "text": "%s\n[i]%d Will  ·  %.1f s[/i]" % [t["text"], int(t["will"]), float(t["cooldown"])], "on": hero.get("techniques", []).has(t["id"]) and opts.is_empty() })
	choose("%s  (%d of %d)" % [m.get("lines", {}).get("setSlots", "Set your three."), picked.size() + 1, n], opts, func(tid: String):
		var p2 := picked.duplicate()
		p2.append(tid)
		_set_slots(id, p2))

func update(events: Array, dt: float) -> void:
	for e in events:
		if debug and e["type"] in ["wolf-down", "player-down", "second-heart", "foe-down", "ally-down"]:
			print("EVENT %s at %s (lesson %s step %d)" % [e["type"], str(fight.p_pos), _lesson.get("id", ""), _step])
		if e["type"] == "technique" and fight:
			_count_technique(String(e.get("id", "")))
		elif e["type"] in ["wolf-down", "foe-down"] and _in_zone():
			progress["record"]["wolves_felled"] = int(progress["record"].get("wolves_felled", 0)) + 1
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
	# What is within reach to act on: everything on the grounds, or in a zone, a trouble or a
	# posting (the Friday rally ends with Bask's standings in the yard); a lesson's drills only
	# what the lesson allows (interact() keeps to doors, the post, the find and the people).
	if not in_lesson() or _in_zone() or _lesson.get("trouble", false) or _lesson.get("quest", false):
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
			var bspec: Dictionary = place_spec(progress["place"]).get("board", {})
			if not bspec.is_empty():
				var ba := Vector2(bspec["at"][0], bspec["at"][1])
				if (fight.p_pos - ba).length() < minf(best, 2.8):
					_target = { "kind": "board", "pos": ba }
		# The lost thing is the errand: within reach it wins over whoever stands beside it.
		if _lost_at != Vector2.INF and (fight.p_pos - _lost_at).length() < 2.0:
			_target = { "kind": "find", "pos": _lost_at }
	_prompt.visible = not _target.is_empty()
	if _prompt.visible:
		match _target["kind"]:
			"door": _prompt_label.text = ("E   " + ("Enter " if door_open(_target["door"]) else "Try ") + String(_target["door"]["label"]))
			"rest": _prompt_label.text = "E   Rest in %s" % _rest["label"]
			"post": _prompt_label.text = "E   Take %s" % _post["label"]
			"board": _prompt_label.text = "E   Read the board"
			"shade": _prompt_label.text = "E   Speak with the shade"
			"smith": _prompt_label.text = "E   The smith's bench"
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
				if goal == Vector2.INF:
					# No way out here: back through an open door toward an area that has one.
					for d in _doors:
						if door_open(d) and Zones.is_zone(String(d["to"])) and _leads_out(String(d["to"]), 4):
							goal = Vector2(d["at"][0], d["at"][1]) * 0.86
							break
			elif gt == "find" and _lost_at != Vector2.INF:
				goal = _lost_at
			elif gt == "talk":
				var who: Dictionary = _lesson.get("poster", {})
				if st["goal"].has("who"):
					who = { "id": st["goal"]["who"] }
				var want_place := String(st.get("place", progress["place"]))
				if progress["place"] != want_place:
					goal = _door_toward(want_place)
				else:
					for p in _people:
						if p.get("id", "") == who.get("id", "-"):
							goal = p["pos"]
			elif gt == "reach" and progress["place"] != String(st["goal"]["place"]):
				goal = _door_toward(String(st["goal"]["place"]))
		if goal == Vector2.INF:
			return Vector2.ZERO
		return _walk_or_act(goal, 1.8)
	var want_place := ""
	match next_need():
		"rest": want_place = "dorm"
		"rite": want_place = "hearth"
		"gate": want_place = "gate"
		"board": want_place = "dorm" if rest_reason() == "" and postings_open().is_empty() and troubles_open().is_empty() else "quad"
		_:
			var nl := next_lesson()
			want_place = nl["place"] if not nl.is_empty() else ""
	# The autopilot, asked to, visits the shade until it is accepted, then the board.
	var sh: Dictionary = Data.academy.get("shade", {})
	if auto_troubles and progress["done"].has("rite") and int(progress.get("shade_visits", 0)) < int(sh.get("acceptVisits", 3)) and not in_lesson():
		if place == sh["place"]:
			goal = Vector2(sh["at"][0], sh["at"][1])
		elif place == "quad":
			for d in _doors:
				if d["to"] == sh["place"] and door_open(d):
					goal = Vector2(d["at"][0], d["at"][1]) * 0.86
		else:
			for d in _doors:
				if d["to"] == "quad":
					goal = Vector2(d["at"][0], d["at"][1]) * 0.86
		if goal != Vector2.INF:
			return _walk_or_act(goal, 2.2)
	var quests_so_far := int(progress["record"].get("quests", 0)) + int(progress["record"].get("quests_lost", 0))
	var term_needs_board := next_need() == "board"
	if (auto_troubles or term_needs_board) and board_open() and progress.get("trouble", "") == "" and (progress.get("quest", {}) is Dictionary and progress.get("quest", {}).is_empty()) and (troubles_open().size() > 0 or (postings_open().size() > 0 and (quests_so_far < auto_quest_cap or term_needs_board))):
		var bspec: Dictionary = place_spec("quad").get("board", {})
		if place == "quad":
			goal = Vector2(bspec["at"][0], bspec["at"][1])
		else:
			for d in _doors:
				if d["to"] == "quad":
					goal = Vector2(d["at"][0], d["at"][1]) * 0.86
		return _walk_or_act(goal, 2.2) if goal != Vector2.INF else Vector2.ZERO
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
	return _walk_or_act(goal, 1.6)

## The door that leads toward an Academy place: its own door, or else the quad's, since every
## place of the Academy opens on the quad (a trouble taken in the yard may send you to the hearth).
func _door_toward(place_id: String) -> Vector2:
	for d in _doors:
		if d["to"] == place_id:
			return Vector2(d["at"][0], d["at"][1]) * 0.86
	if not Zones.is_zone(place_id):
		for d in _doors:
			if d["to"] == "quad":
				return Vector2(d["at"][0], d["at"][1]) * 0.86
	return Vector2.INF

## Within reach of the goal and it is what is in reach: act on it. Otherwise keep walking
## (a classmate standing nearer than the door must not be talked to in the door's place).
func _walk_or_act(goal: Vector2, reach: float) -> Vector2:
	var dist := (goal - fight.p_pos).length()
	if dist < reach and not _target.is_empty() and (Vector2(_target["pos"]) - goal).length() < 1.3:
		interact()
		return Vector2.ZERO
	if dist < 0.35:
		return Vector2.ZERO
	return _steer((goal - fight.p_pos).normalized())

## Does a zone area reach extraction within a few doors?
func _leads_out(pid: String, depth: int) -> bool:
	if depth <= 0 or not Zones.is_zone(pid):
		return false
	var area: Dictionary = Zones.area_of(Zones.zone_of(pid), pid.split("/")[1])
	for d in area["doors"]:
		if d["to"] == "extraction":
			return true
	for d in area["doors"]:
		if d["to"] != "extraction" and _leads_out("%s/%s" % [Zones.zone_of(pid), d["to"]], depth - 1):
			return true
	return false

var _steer_last_pos := Vector2.INF
var _steer_stuck_t := 0.0
var _unstick_until := 0.0
var _unstick_dir := Vector2.ZERO

## Walk round what is in the way: a pillar, a brazier, a person. Boxed in (no ground gained
## for a while), take a sidestep for a moment and try again.
func _steer(dir: Vector2) -> Vector2:
	var now := Time.get_ticks_msec() / 1000.0
	if now < _unstick_until:
		return _unstick_dir
	if _steer_last_pos != Vector2.INF and fight.p_pos.distance_to(_steer_last_pos) < 0.06:
		_steer_stuck_t += get_process_delta_time()
		if _steer_stuck_t > 1.2:
			_steer_stuck_t = 0.0
			_unstick_until = now + 0.9
			_unstick_dir = dir.rotated((PI / 2.0) * (1.0 if randf() < 0.5 else -1.0)).normalized()
			return _unstick_dir
	else:
		_steer_stuck_t = 0.0
	_steer_last_pos = fight.p_pos
	for o in fight.obstacles:
		var c := Vector2(o.x, o.y)
		var to := c - fight.p_pos
		var d := to.length()
		if d < float(o.z) + 1.2 and d > 0.01 and dir.dot(to / d) > 0.6:
			var side := 1.0 if dir.cross(to) < 0.0 else -1.0
			return dir.rotated(side * 1.1).normalized()
	return dir

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
		hero["techniques"] = dk.get("techniques", []).slice(0, 3).map(func(t): return t["id"])
	var spec: Dictionary = place_spec(lesson["place"])
	var ins: Dictionary = Data.by_id(Data.academy["instructors"], lesson["instructor"])
	_drill_fight()
	hud.play_ui.visible = true
	hud.target.visible = false
	_prompt.visible = false
	_step = -1
	_next_step()

## The Instructor's genius sits in the ring: the fight the drills are done in.
func _drill_fight() -> void:
	var spec: Dictionary = place_spec(_lesson["place"])
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
	var spec: Dictionary = place_spec(_lesson["place"])
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
	if debug:
		print("STEP %s %d/%d %s goal=%s place=%s" % [_lesson.get("id", ""), _step + 1, steps.size(), s.get("title", ""), s["goal"]["type"], s.get("place", "-")])
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
	_step_limit = float(s.get("limit", 0.0))
	if s.get("companion", false) and _lesson.get("trouble", false):
		# The poster walks beside you.
		fight.allies = []
		var c: Dictionary = _lesson["poster"]
		fight.allies.append(Fight.make_ally(c, fight.p_pos + Vector2(-1.2, 1.2)))
		world.set_allies(fight.allies)
	if s.has("place") and progress["place"] != s["place"]:
		go(s["place"], false, progress["place"])
	# A trouble's "talk" step: the poster must be standing here to be talked to (after the
	# rematch in the yard, where the cohort does not otherwise stand).
	if _lesson.get("trouble", false) and String(s["goal"]["type"]) == "talk" and String(s.get("place", progress["place"])) == progress["place"]:
		_ensure_poster_here()
	# The spar is set up after the walk to its place, or the new place would wipe it.
	if setup.get("spar", false):
		_spar_mode = "poster" if str(setup["spar"]) == "poster" else ("instructor" if str(setup["spar"]) == "instructor" else "cohort")
		_spar_rung = 0
		_spar_wins = 0
		_spar_begin()
	match String(s["goal"]["type"]):
		"find":
			_choice_done = false
			var rng := RandomNumberGenerator.new()
			rng.seed = int(progress["seed"]) + 77
			var a: Dictionary = place_spec(progress["place"])
			# Somewhere in the open: clear of the people standing about and of what is in the way.
			for tries in 24:
				_lost_at = Vector2(rng.randf_range(-a["size"][0] / 2.0 + 2.0, a["size"][0] / 2.0 - 2.0), rng.randf_range(-a["size"][1] / 2.0 + 2.0, a["size"][1] / 2.0 - 2.0))
				var clear := true
				for pp in _people:
					if (Vector2(pp["pos"]) - _lost_at).length() < 3.0:
						clear = false
				for o in fight.obstacles:
					if (Vector2(o.x, o.y) - _lost_at).length() < float(o.z) + 1.0:
						clear = false
				if clear:
					break
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
			say("", s["goal"].get("lines", []).map(func(l): return fill(String(l))), func():
				_choice_done = true
				go(to, false, progress["place"]))
		"extract":
			_choice_done = false
		"decide":
			_choice_done = false
			var opts: Array = s["goal"]["options"].map(func(o): return { "id": o["id"], "label": fill(o["label"]), "text": fill(o["text"]) })
			choose(fill(s["title"]), opts, func(id: String):
				if not progress.has("decisions"):
					progress["decisions"] = []
				progress["decisions"].append({ "quest": _lesson["id"], "type": _lesson.get("kind", ""), "choice": id, "day": int(progress["day"]) })
				weigh_decision("%s:%s" % [_lesson.get("kind", ""), id])
				_choice_done = true
				save())
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
	hud.set_prompt("%d/%d · %s" % [_step + 1, steps.size(), fill(s["title"])], fill(String(s.get("text", ""))))
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
		"find", "talk", "decide": done = _choice_done
		"reach": done = progress["place"] == g["place"]
		"hunt":
			for e in events:
				if e["type"] == "wolf-down":
					_choice_done = true
			done = _choice_done
	# A quest's clock, and what loses a quest outright.
	if _lesson.get("quest", false):
		if _step_limit > 0.0:
			_step_limit -= dt
			if _step_limit <= 0.0:
				_fail_quest("timer")
				return
		for e in events:
			if e["type"] == "ally-down" and int(e.get("who", -1)) < fight.allies.size() and fight.allies[int(e.get("who", -1))].get("passenger", false):
				_fail_quest("passenger")
				return
			if e["type"] == "player-down" and _carrying:
				_fail_quest("dropped")
				return
	if String(g["type"]) in ["fell", "hold", "extract", "travel", "choose-party"]:
		for e in events:
			var t: String = e["type"]
			if notes.has(t):
				_note = notes[t]
			if t == "player-down" and _in_zone():
				if _lesson.get("quest", false):
					_fail_quest("rescued")
				else:
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
				# Reach is measured where the technique was thrown from, so a dash or a lunge
				# that closes the gap still counts for the distance it crossed.
				if t == "technique":
					_tech_from = float(e.get("dist", 0.0))
				if t == "hit" and e.get("technique", false) and maxf(float(e.get("dist", 0.0)), _tech_from) >= float(g.get("distance", 2.5)):
					_count += 1
					_note = ""
				elif t == "hit" and e.get("technique", false):
					_note = "Too close: that one landed inside arm's reach."
	match String(g["type"]):
		"event", "streak", "reach-hits": done = _count >= int(g["count"])
		"will-full": done = fight.p_will >= float(Data.rules["field"]["willMax"]) - 0.5
		"stance-seconds": done = done or _held >= float(g["count"])
		"choose-weapon", "fell", "hold", "extract", "travel", "choose-party", "find", "talk", "reach", "hunt", "decide": done = done or (_choice_done and String(g["type"]) in ["choose-weapon", "extract", "travel", "choose-party", "find", "talk", "hunt", "decide"])
	var status := _note
	if _step_limit > 0.0 and _lesson.get("quest", false):
		status = "%s%d s left." % [(_note + "  ") if _note != "" else "", ceili(_step_limit)]
	hud.set_prompt_status(status, _progress_text(s))
	if done:
		sfx.play("cue-hit", 1.0)
		hud.set_prompt_status("Done.", "")
		_step_hold = 1.0

func _finish_lesson() -> void:
	var lesson := _lesson
	if lesson.get("trouble", false):
		_finish_trouble()
		return
	if lesson.get("quest", false):
		_finish_quest()
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
	_sting("rite")
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

var _choice_box: Control = null

## A choice among a few things, each with a line about it; the autopilot takes the first.
func choose(title: String, options: Array, then: Callable) -> void:
	if _choice_box:
		_choice_box.queue_free()
	var veil := ColorRect.new()
	veil.color = Color(0.02, 0.016, 0.016, 0.55)
	veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	_choice_box = veil
	get_child(0).add_child(veil)
	var sheet := PanelContainer.new()
	sheet.set_anchors_preset(Control.PRESET_CENTER)
	sheet.custom_minimum_size = Vector2(940, 520)
	sheet.position = Vector2(-470, -260)
	sheet.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.034, 0.03, 0.97), Style.BRASS, 1, 22))
	veil.add_child(sheet)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	sheet.add_child(v)
	var l := Label.new()
	Style.label(l, 26, Style.GOLD, "title")
	l.text = title
	v.add_child(l)
	v.add_child(Style.rule(420))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(row)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(400, 0)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	row.add_child(scroll)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 6)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list)
	var desc_panel := PanelContainer.new()
	desc_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	desc_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	desc_panel.add_theme_stylebox_override("panel", Style.plate(Color(0.03, 0.026, 0.024, 0.9), Style.BRASS_DIM, 1, 18))
	row.add_child(desc_panel)
	var dv := VBoxContainer.new()
	dv.add_theme_constant_override("separation", 8)
	desc_panel.add_child(dv)
	var dh := Label.new()
	Style.label(dh, 20, Style.FG, "title")
	dh.autowrap_mode = TextServer.AUTOWRAP_WORD
	dv.add_child(dh)
	var dt := RichTextLabel.new()
	dt.bbcode_enabled = true
	dt.fit_content = true
	dt.scroll_active = false
	dt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Style.rich(dt, 17, Style.FG, "body")
	dv.add_child(dt)
	var foot := Label.new()
	Style.label(foot, 13, Style.DIM, "ui")
	foot.text = "Up / Down  look      Enter / click  choose"
	v.add_child(foot)
	var first: Button = null
	for o in options:
		var b := Button.new()
		b.text = o["label"]
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.clip_text = true
		b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		b.custom_minimum_size = Vector2(0, 44)
		Style.button(b, o.get("on", false), 17)
		var id: String = o["id"]
		var show := func():
			dh.text = o["label"]
			dt.text = String(o.get("text", ""))
		b.focus_entered.connect(show)
		b.mouse_entered.connect(show)
		b.pressed.connect(func():
			sfx.play("ui-take", 1.0, -6.0)
			_choice_box.queue_free()
			_choice_box = null
			if not auto:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			then.call(id))
		list.add_child(b)
		if first == null or o.get("on", false):
			first = b
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if first:
		first.call_deferred("grab_focus")
	if auto:
		get_tree().create_timer(1.0).timeout.connect(func(): if _choice_box: (first as Button).pressed.emit())

# --- The line: zones, the post, extraction, the rescue team --------------------------------

func _in_zone() -> bool:
	return place_spec(progress["place"]).has("zone")

func _clear_place() -> void:
	if not progress.has("cleared"):
		progress["cleared"] = {}
	progress["cleared"][progress["place"]] = true
	world.open_doors = {}
	for d in _doors:
		if door_open(d):
			world.open_doors[d["to"]] = true
	world.place = ""
	world.set_place(progress["place"], place_spec(progress["place"]))
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
	if not _lesson.get("quest", false):
		_carry_out_fallen()
	say("", lines, func():
		_choice_done = true
		progress["record"]["runs_out"] = int(progress["record"].get("runs_out", 0)) + 1
		if not _lesson.get("quest", false):
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
		if chosen.has(c["id"]) or party_unavailable(c["id"]):
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

# --- The pause sheet ---------------------------------------------------------------

## Esc: the term so far, the genius, and the way out. The fight stands still while it is up.
func pause() -> void:
	save()
	get_tree().paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var rec: Dictionary = progress["record"]
	var lines: Array = []
	lines.append("[color=#a8803f]%s[/color]   %s, %s" % ["Today", date_line(), objective()])
	lines.append("[color=#a8803f]Marks[/color]   %d  ·  %s, %s" % [int(rec.get("marks", 0)), Marks.archetype_for(hero["shape"], hero.get("discipline", "")).get("name", "no archetype yet"), String(Marks.rank_for(int(rec.get("marks", 0)), int(hero.get("stage", 2)), rec.get("pattern_built", false))).capitalize()])
	lines.append("[color=#a8803f]The term[/color]   %d parries, %d blocks, bitten %d  ·  %d bouts won, %d lost  ·  %d posts held, %d runs out" % [int(rec.get("parries", 0)), int(rec.get("blocks", 0)), int(rec.get("hurts", 0)), int(rec.get("spars_won", 0)), int(rec.get("spars_lost", 0)), int(rec.get("posts_held", 0)), int(rec.get("runs_out", 0))])
	if int(rec.get("quests", 0)) + int(rec.get("quests_lost", 0)) > 0:
		lines.append("[color=#a8803f]The board[/color]   %d postings done, %d lost  ·  %d troubles seen to" % [int(rec.get("quests", 0)), int(rec.get("quests_lost", 0)), int(rec.get("troubles", 0))])
	var q: Dictionary = progress.get("quest", {}) if progress.get("quest", {}) is Dictionary else {}
	if not q.is_empty():
		lines.append("[color=#a8803f]In hand[/color]   %s" % q.get("title", ""))
	if not crisis().is_empty():
		lines.append("[color=#a8803f]%s[/color]   %s" % [crisis()["name"], ledgers_text()])
	var g: Dictionary = hero.get("genius", {})
	if genius and genius.is_born():
		lines.append("[color=#a8803f]Genius[/color]   %s, %s  ·  %s" % [genius.name if genius.name != "" else genius.form_name(), genius.form_name(), genius.instar_name()])
	var buttons: Array = [["Continue", unpause]]
	if genius and genius.is_born():
		buttons.append(["The genius's page  (J)", func(): unpause(); get_parent().call("open_genius_page")])
	buttons.append(["Leave by the line  (to the title, the term saved)", func(): get_tree().paused = false; leave.emit()])
	hud.show_screen("THE TERM SO FAR", "%s  ·  %s" % [hero["name"], Data.academy["term"]["cohort"]], "\n".join(lines), buttons)

func unpause() -> void:
	get_tree().paused = false
	hud.hide_screen()
	hud.play_ui.visible = _in_zone() or in_lesson()
	if not auto:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

## What the HUD says of where you are.
func place_label() -> String:
	if _in_zone():
		var sp := place_spec(progress["place"])
		var z: Dictionary = sp.get("wild", {})
		return "%s  ·  %s  ·  %s" % [String(z.get("name", "the line")).to_lower(), String(sp.get("name", "")).to_lower(), String(sp.get("zone", {}).get("colour", "green"))]
	return "%s  ·  warded" % String(place_spec(progress["place"]).get("name", "the yard")).to_lower()

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
	# Centred on the screen, whatever its size: a CenterContainer, not a centre anchor.
	var centre := CenterContainer.new()
	centre.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(centre)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	centre.add_child(v)
	var title := Label.new()
	Style.label(title, 30, Style.FG, "title")
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
		var card := GeniusCard.make(info, col, "CANDIDATE %d" % (i + 1), true)
		col_v.add_child(card)
		var why := RichTextLabel.new()
		why.bbcode_enabled = true
		why.fit_content = true
		why.scroll_active = false
		why.custom_minimum_size = Vector2(300, 0)
		Style.rich(why, 13, Style.DIM, "italic")
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
		if i == 0:
			b.call_deferred("grab_focus")
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
		var hold := 14.0 if OS.get_cmdline_user_args().has("--slowchoice") else 1.5
		get_tree().create_timer(hold).timeout.connect(func(): if _reading_box: hide_reading(); then.call(-1))

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
	var techs: Array = []
	for t in dk.get("techniques", []):
		if techniques_known().has(t["id"]):
			var gr: Dictionary = fight.grade_of(t["id"]) if fight else { "id": "learned", "name": "learned" }
			techs.append(t["name"] + ("" if gr["id"] == "learned" else " (%s)" % gr["name"]))
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
var auto_quest_cap := 4   # the autopilot takes this many postings, then gets on with the term
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

## The poster of the trouble in hand stands in this place, a few steps off, if not here already.
func _ensure_poster_here() -> void:
	var c: Dictionary = _lesson.get("poster", {})
	if c.is_empty():
		return
	for p in _people:
		if p.get("id", "") == c["id"]:
			return
	var at := fight.p_pos + Vector2.from_angle(fight.p_facing) * 2.6
	var spec: Dictionary = place_spec(progress["place"])
	at = Vector2(clampf(at.x, -float(spec["size"][0]) / 2.0 + 1.5, float(spec["size"][0]) / 2.0 - 1.5), clampf(at.y, -float(spec["size"][1]) / 2.0 + 1.5, float(spec["size"][1]) / 2.0 - 1.5))
	world.add_figure(c["body"], at, (fight.p_pos - at).angle(), c["name"], "%s · %s" % [c.get("blood_name", ""), String(c.get("shape", "")).capitalize()], c.get("weapon", ""), Color(0, 0, 0, 0), c.get("look", {}))
	_people.append({ "kind": "classmate", "id": c["id"], "name": c["name"], "pos": at, "c": c })

func _classmate(id: String) -> Dictionary:
	for c in cohort:
		if c["id"] == id:
			return c
	return {}

func _read_board() -> void:
	var b: Dictionary = Data.academy["board"]
	var open := troubles_open()
	var posts := postings_open()
	if progress.get("trouble", "") != "":
		say("", ["You have %s's trouble in hand already." % _classmate(progress["trouble"].trim_prefix("trouble:")).get("name", "a classmate")])
		return
	if open.is_empty() and posts.is_empty():
		say("", [Data.quests["lines"]["nothing"], ledgers_text()] if not crisis().is_empty() else [Data.quests["lines"]["nothing"]])
		return
	if open.is_empty() and crisis().is_empty():
		_read_postings(posts)
		return
	if open.is_empty():
		var qopts: Array = [{ "id": "postings", "label": "The day's postings  ·  %d" % posts.size(), "text": "Work from the Compact, the Archive, the towns and the houses: excursions out on the line." },
			{ "id": "ledgers", "label": "The Ledgers  ·  %s" % crisis()["name"], "text": ledgers_text() }]
		choose("The board", qopts, func(id: String):
			if id == "postings":
				_read_postings(posts)
			else:
				say("", [ledgers_text()]))
		return
	var opts: Array = []
	for t in open:
		var c := _classmate(t["poster"])
		var ks: Dictionary = b["kinds"][t["kind"]]
		opts.append({ "id": t["id"], "label": "%s  ·  %s" % [ks["title"], c["name"]], "text": fill(ks["posting"], c) })
	if not posts.is_empty():
		opts.append({ "id": "postings", "label": "The day's postings  ·  %d" % posts.size(), "text": "Work from the Compact, the Archive, the towns and the houses: excursions out on the line." })
	if not crisis().is_empty():
		opts.append({ "id": "ledgers", "label": "The Ledgers  ·  %s" % crisis()["name"], "text": ledgers_text() })
	choose("The board", opts, func(id: String):
		if id == "postings":
			_read_postings(posts)
		elif id == "ledgers":
			say("", [ledgers_text()])
		else:
			_take_trouble(id))

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
	if in_lesson() and _step < _lesson["steps"].size() and _lesson["steps"][_step]["goal"].get("carry", false):
		_carrying = true
		_apply_carry()
		title_card("CARRIED", "no Patterns while you carry it", Style.GOLD)
	sfx.play("cue-hit", 1.3)
	world.floater(world._v3(fight.p_pos, 2.2), "FOUND", Style.GOLD, 52, 1.2)

## A beast loose in the yard, wards up: a small hunt.
func _hunt_begin(beast: String, scale: float) -> void:
	var spec: Dictionary = place_spec(progress["place"])
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
	if debug:
		print("HUNT %s x%.2f at %s" % [beast, scale, str(fight.p_pos)])
	title_card("LOOSE IN THE YARD", "the wards are up", Style.EMBER)

func _finish_trouble() -> void:
	var lesson := _lesson
	if debug:
		print("TROUBLE done %s" % lesson.get("id", ""))
	var c: Dictionary = lesson["poster"]
	if not progress.has("troubles_done"):
		progress["troubles_done"] = []
	progress["troubles_done"].append(lesson["id"])
	progress["trouble"] = ""
	progress["worked_day"] = int(progress["day"])
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

# --- The board's postings: excursions into the zones ---------------------------------------
# The seven quest types (data/quests.json) posted daily for the zones that are open
# (data/zones.json, opensAfter), each an excursion: the party, the car, the areas, the post,
# extraction, and pay in Marks. A posting is drawn by the run's seed and the day, so the
# board changes after every rest. Rally posts on its weekday only; the Deep Run needs the
# field open. A quest is run on the lesson step engine with a few more goal types.

var _step_limit := 0.0
var _tech_from := 0.0
var _carrying := false

## The zones the hero may be sent to.
func zones_open() -> Array:
	return Data.zones().filter(func(z): return progress["done"].has(String(z.get("opensAfter", "line"))))

## The day's postings, drawn by the seed and the day.
func postings_for_day(day: int) -> Array:
	var q: Dictionary = Data.quests
	var rng := RandomNumberGenerator.new()
	rng.seed = int(progress["seed"]) * 101 + day * 7 + 11
	var zones := zones_open()
	if zones.is_empty():
		return []
	var n := rng.randi_range(int(q["perDay"]["min"]), int(q["perDay"]["max"]))
	var out: Array = []
	var types: Array = q["types"].keys()
	var tries := 0
	var used_types := {}
	while out.size() < n and tries < 40:
		tries += 1
		var tid: String = types[rng.randi() % types.size()]
		var t: Dictionary = q["types"][tid]
		if t.has("weekday") and t["weekday"] != weekday_of(day):
			continue
		if t.has("requires") and not progress["done"].has(String(t["requires"])):
			continue
		if rng.randf() * 4.0 > float(t["weight"]) and not (tid == "deep-run" and out.size() == n - 1 and not used_types.has("deep-run") and day % 3 == 0):
			continue
		if used_types.get(tid, 0) >= 2:
			continue
		var colours := ["green", "amber", "red", "black"]
		var fit: Array = zones.filter(func(zz): return colours.find(String(zz["colour"])) >= colours.find(String(t["minColour"])))
		if fit.is_empty():
			continue
		var z: Dictionary = fit[rng.randi() % fit.size()]
		if out.any(func(q): return q["type"] == tid and q["zone"] == z["id"]):
			continue
		var pname: Array = q["posterNames"].get(t["poster"], ["The board"])
		var named: Array = z["beasts"].get("named", []).filter(func(n): return not progress.get("named", {}).get(n["id"], {}).get("felled", false))
		if tid == "hunt" and named.is_empty():
			continue
		var p := {
			"id": "quest:%d:%d" % [day, out.size()], "day": day, "type": tid, "zone": z["id"], "colour": z["colour"],
			"poster": pname[rng.randi() % pname.size()], "pay": int(t["pay"].get(z["colour"], 1)),
			"entry": "%s/%s" % [z["id"], z["areas"][0]["id"]], "post": "", "elite": "", "named": named[rng.randi() % named.size()] if not named.is_empty() else {},
		}
		for a in z["areas"]:
			if a.has("post") and p["post"] == "":
				p["post"] = "%s/%s" % [z["id"], a["id"]]
			if a.get("beast", "") == "elite" and p["elite"] == "":
				p["elite"] = "%s/%s" % [z["id"], a["id"]]
		if p["post"] == "" or p["elite"] == "":
			continue
		if t.has("place"):
			p["entry"] = t["place"]
		p["title"] = fill_quest(t["title"], p)
		p["posting"] = fill_quest(t["posting"], p)
		# A classmate took this one and wants a second.
		if rng.randf() < 0.35 and progress["done"].has("rite"):
			var free: Array = cohort.filter(func(c): return not party_unavailable(c["id"], day))
			if not free.is_empty():
				var c: Dictionary = free[rng.randi() % free.size()]
				p["with"] = c["id"]
				p["posting"] += "  " + fill(String(Data.academy["cohort"].get("schedule", {}).get("lines", {}).get("withPosting", "")), c)
		used_types[tid] = used_types.get(tid, 0) + 1
		out.append(p)
	# The crisis posts one of its own while its Ledgers are open.
	var cp := crisis_posting(day, rng)
	if not cp.is_empty():
		out.append(cp)
	if day == int(progress["day"]):
		if not progress.has("quest_types_seen"):
			progress["quest_types_seen"] = []
		for q2 in out:
			if not progress["quest_types_seen"].has(q2["type"]):
				progress["quest_types_seen"].append(q2["type"])
	return out

func weekday_of(day: int) -> String:
	var days: Array = Data.academy.get("calendar", {}).get("weekdays", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
	return days[(day - 1) % days.size()]

## Today's postings not yet taken.
func postings_open() -> Array:
	var done: Array = progress.get("quests_done", [])
	var failed: Array = progress.get("quests_failed", [])
	var in_hand: Dictionary = progress.get("quest", {}) if progress.get("quest", {}) is Dictionary else {}
	return postings_for_day(int(progress["day"])).filter(func(p): return not done.has(p["id"]) and not failed.has(p["id"]) and in_hand.get("id", "") != p["id"])

## The posting's words: the zone's names in the text, its place ids in the steps.
func fill_quest(t: String, p: Dictionary, ids := false) -> String:
	var z: Dictionary = Data.zone(p["zone"])
	var area_name := func(pid: String) -> String:
		if not Zones.is_zone(pid):
			return place_spec(pid).get("name", pid)
		return Zones.area_of(Zones.zone_of(pid), pid.split("/")[1])["name"]
	for key in ["entry", "post", "elite"]:
		t = t.replace("{%s}" % key, p[key] if ids else String(area_name.call(p[key])))
	t = t.replace("{zone}", z["name"]).replace("{beast}", Data.beast(z["beasts"]["common"])["name"]).replace("{poster}", String(p.get("poster", "")))
	t = t.replace("{named}", String(p["named"].get("name", "the beast")) if p["named"] is Dictionary else "the beast")
	t = t.replace("{passenger}", String(p.get("passenger_name", "the passenger")))
	return fill(t)

func _read_postings(posts: Array) -> void:
	if progress.get("quest", {}) is Dictionary and not progress.get("quest", {}).is_empty():
		say("", [String(Data.quests["lines"]["inHand"]).replace("{title}", progress["quest"]["title"])])
		return
	var opts: Array = []
	for p in posts:
		var t: Dictionary = Data.quests["types"][p["type"]]
		var zname := String(Data.zone(p["zone"])["name"]) if p["type"] != "rally" else "the yard"
		opts.append({ "id": p["id"], "label": "%s  ·  %s" % [String(t["name"]).to_upper(), p["title"]],
			"text": "%s\n[i]%s  ·  %s  ·  %s line  ·  %d Mark%s%s[/i]" % [p["posting"], p["poster"], zname, String(p["colour"]).capitalize(), int(p["pay"]), "" if int(p["pay"]) == 1 else "s", "  ·  CRISIS" if p.has("crisis_ledger") else ""] })
	choose("The day's postings", opts, func(id: String):
		for p in posts:
			if p["id"] == id:
				_take_quest(p))

func _take_quest(p: Dictionary) -> void:
	progress["quest"] = p
	save()
	say("", [Data.quests["lines"]["taken"]], func(): _begin_quest(p))

## The run: a party unless the quest stays in the yard, then the posting's steps.
func _begin_quest(p: Dictionary) -> void:
	var t: Dictionary = Data.quests["types"][p["type"]]
	var steps: Array = []
	if not t.has("place"):
		steps.append({ "title": "Your party", "text": "Choose two classmates for the car.", "goal": { "type": "choose-party" } })
	for s0 in t["steps"]:
		var st: Dictionary = s0.duplicate(true)
		st["title"] = fill_quest(String(st["title"]), p)
		if st.has("text"):
			st["text"] = fill_quest(String(st["text"]), p)
		if st.has("place"):
			st["place"] = fill_quest(String(st["place"]), p, true)
		var g: Dictionary = st["goal"]
		if g.has("to"):
			g["to"] = fill_quest(String(g["to"]), p, true)
		if g.has("place"):
			g["place"] = fill_quest(String(g["place"]), p, true)
		if g.has("lines"):
			g["lines"] = g["lines"].map(func(l): return fill_quest(String(l), p))
		if g.has("item"):
			g["item"] = fill_quest(String(g["item"]), p)
		steps.append(st)
	_lesson = { "id": p["id"], "quest": true, "kind": p["type"], "posting": p, "number": 0, "title": p["title"], "place": progress["place"],
		"instructor": "varga", "steps": steps, "intro": [], "outro": [], "rescue": { "lines": ["The rescue team carries you out. The posting is lost."] } }
	if t["steps"].any(func(s0): return s0.get("goal", {}).get("named", false)):
		_lesson["named_at"] = p["elite"]
		_lesson["named"] = p["named"]
	if t["steps"].any(func(s0): return s0.get("escort", false)):
		var rng := RandomNumberGenerator.new()
		rng.seed = int(progress["seed"]) + int(p["day"]) * 3
		var c: Dictionary = cohort[rng.randi() % cohort.size()]
		_lesson["passenger"] = { "id": "passenger", "name": "the passenger", "shape": c["shape"], "body": c["body"], "weapon": c["weapon"] }
	progress["party"] = [p["with"]] if p.has("with") and not party_unavailable(String(p["with"])) else []
	_run_rec = progress["record"].duplicate()
	_run_t0 = Time.get_ticks_msec() / 1000.0
	_carrying = false
	hud.play_ui.visible = true
	hud.target.visible = false
	_step = -1
	_next_step()

## The Hearthkeeper's work is done: the Pattern is the hero's, the genius knows, the hall remembers.
func pattern_built(spec: Dictionary) -> void:
	hero["pattern"] = spec
	progress["record"]["pattern_built"] = true
	if genius:
		genius.milestone("pattern-built")
		genius.save_to(hero)
	save()
	var L: Dictionary = Data.academy.get("mastery", {}).get("lines", {})
	go(progress["place"], true, "")
	say("keeper", [L.get("keeperDone", "Written.")])

## Carrying the Archive's thing: no Patterns.
func _apply_carry() -> void:
	fight.allowed = ["attack", "technique", "dodge", "block-down", "block-up", "stance", "lock", "tech1", "tech2", "tech3", "order"]

func _finish_quest() -> void:
	var lesson := _lesson
	var p: Dictionary = lesson["posting"]
	var t: Dictionary = Data.quests["types"][p["type"]]
	if not progress.has("quests_done"):
		progress["quests_done"] = []
	progress["quests_done"].append(p["id"])
	progress["quest"] = {}
	progress["worked_day"] = int(progress["day"])
	if not progress.has("quest_types_done"):
		progress["quest_types_done"] = []
	if not progress["quest_types_done"].has(p["type"]):
		progress["quest_types_done"].append(p["type"])
	var rec: Dictionary = progress["record"]
	rec["quests"] = int(rec.get("quests", 0)) + 1
	_gear_from_run(p)
	rec["quests_" + String(p["type"])] = int(rec.get("quests_" + String(p["type"]), 0)) + 1
	if not progress.has("writeup_extra"):
		progress["writeup_extra"] = []
	progress["writeup_extra"].append(fill_quest(String(t["writeup"]), p))
	if lesson.has("named"):
		if not progress.has("named"):
			progress["named"] = {}
		progress["named"][String(lesson["named"]["id"])] = { "escaped": named_escapes(String(lesson["named"]["id"])), "felled": true }
	if genius:
		genius.bonded("party")
	var carried := _carry_out_fallen()
	var before := ledgers()
	weigh_ledgers(p)
	_end_quest_run()
	earn_marks_n(int(p["pay"]), p["title"])
	sfx.play("done")
	_sting("done")
	save()
	_run_sheet(p, true, carried, before)

func _fail_quest(why: String) -> void:
	var lesson := _lesson
	var p: Dictionary = lesson["posting"]
	var t: Dictionary = Data.quests["types"][p["type"]]
	if not progress.has("quests_failed"):
		progress["quests_failed"] = []
	progress["quests_failed"].append(p["id"])
	progress["worked_day"] = int(progress["day"])
	progress["quest"] = {}
	progress["record"]["quests_lost"] = int(progress["record"].get("quests_lost", 0)) + 1
	if lesson.has("named") and why in ["timer", "rescued"]:
		# The named beast got away: it will remember the car.
		if not progress.has("named"):
			progress["named"] = {}
		var nid := String(lesson["named"]["id"])
		progress["named"][nid] = { "escaped": named_escapes(nid) + 1, "felled": false }
	if why == "rescued":
		progress["record"]["rescued"] = int(progress["record"].get("rescued", 0)) + 1
	var carried := _carry_out_fallen()
	var L: Dictionary = Data.quests["lines"]
	var line := String(L["failed"]).replace("{title}", p["title"])
	match why:
		"passenger": line = String(L["passengerDown"]) + "  " + line
		"timer": line = String(L["timer"]) + "  " + line
	_end_quest_run()
	fight.allowed = []
	_sting("lost")
	say("", [line, fill_quest(String(t["failed"]), p)], func():
		if _in_zone():
			progress["cleared"] = {}
			go("quad", true, "")
		save()
		_run_sheet(p, false, carried, ledgers()))

var _run_rec: Dictionary = {}
var _run_t0 := 0.0

## The hearth's tally after a run: what it paid, what it cost, what it weighed, what was seen.
func _run_sheet(p: Dictionary, won: bool, carried: Array, before: Dictionary) -> void:
	var t: Dictionary = Data.quests["types"][p["type"]]
	var rec: Dictionary = progress["record"]
	var d := func(k: String) -> int: return int(rec.get(k, 0)) - int(_run_rec.get(k, 0))
	var minutes := int((Time.get_ticks_msec() / 1000.0 - _run_t0) / 60.0)
	var lines: Array = []
	lines.append("[color=#a8803f]%s[/color]   %s  ·  %s" % [t["name"], p["title"], p["poster"]])
	lines.append("[color=#a8803f]Pay[/color]   %s" % (("%d Mark%s" % [int(p["pay"]), "" if int(p["pay"]) == 1 else "s"]) if won else "none: the posting was lost"))
	lines.append("[color=#a8803f]The run[/color]   %d minute%s  ·  %d parries, %d blocks, bitten %d  ·  %d beast%s felled" % [minutes, "" if minutes == 1 else "s", d.call("parries"), d.call("blocks"), d.call("hurts"), d.call("wolves_felled"), "" if d.call("wolves_felled") == 1 else "s"])
	if not carried.is_empty():
		lines.append("[color=#a8803f]Carried out[/color]   %s: the infirmary for two days" % ", ".join(carried))
	var after := ledgers()
	var weighed: Array = []
	for k in after:
		if int(after[k]) != int(before.get(k, 0)):
			weighed.append("%s +%d" % [crisis()["ledgers"][k]["name"], int(after[k]) - int(before.get(k, 0))])
	if not weighed.is_empty():
		lines.append("[color=#a8803f]The Ledgers[/color]   %s" % ", ".join(weighed))
	if genius and genius.is_born():
		lines.append("[color=#a8803f]Witness[/color]   %s ran %s with you" % [genius.name if genius.name != "" else genius.form_name(), String(Data.zone(p["zone"])["name"]) if p["type"] != "rally" else "the yard"])
	lines.append("\n[i]%s[/i]" % fill_quest(String(t["writeup"] if won else t["failed"]), p))
	hud.show_screen("THE RUN" if won else "THE RUN, LOST", "the hearth's tally", "\n".join(lines), [["Continue", func():
		hud.hide_screen()
		hud.play_ui.visible = _in_zone()
		if not auto:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED]])
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if auto:
		get_tree().create_timer(2.0).timeout.connect(func():
			if hud.screen.visible:
				hud.hide_screen()
				hud.play_ui.visible = _in_zone())

func _end_quest_run() -> void:
	_lesson = {}
	_carrying = false
	_step_limit = 0.0
	world.set_marker(null)
	_lost_at = Vector2.INF
	fight.allowed = []
	fight.passive = true
	fight.p_lock = false
	world.lock_on = false
	hud.set_prompt("", "")
	hud.set_prompt_status("", "")
	hud.play_ui.visible = false
	if _in_zone():
		progress["cleared"] = {}
		go("quad", true, "")

# --- The cohort's days: where each of them is, who is out, who is in the infirmary -----------

## Is this classmate at this place today? (After the rite; before it the cohort keeps together.)
func _classmate_here(c: Dictionary, place_id: String) -> bool:
	if in_lesson() and _lesson.get("poster", {}).get("id", "") == c["id"]:
		return true
	return classmate_status(c, int(progress["day"]))["place"] == place_id

## Where a classmate is on a day, and whether they are away: on a run of their own, or in
## the infirmary after being carried out.
func classmate_status(c: Dictionary, day: int) -> Dictionary:
	var inf: Dictionary = progress.get("infirmary", {})
	if int(inf.get(c["id"], 0)) >= day:
		return { "place": "", "away": "infirmary" }
	if away_today(day).has(c["id"]):
		return { "place": "", "away": "run" }
	var sch: Dictionary = Data.academy["cohort"].get("schedule", {})
	var haunts: Array = sch.get("haunts", {}).get(c["temperament"], ["quad"])
	return { "place": haunts[(day - 1) % haunts.size()], "away": "" }

## The classmates out on a run of their own today (none before Lesson 5 opens the line).
func away_today(day: int) -> Array:
	if day < 1 or not progress["done"].has("line"):
		return []
	var sch: Dictionary = Data.academy["cohort"].get("schedule", {})
	var rng := RandomNumberGenerator.new()
	rng.seed = int(progress["seed"]) * 13 + day * 5
	var ids: Array = cohort.map(func(c): return c["id"])
	Academy._shuffle(ids, rng)
	return ids.slice(0, mini(int(sch.get("awayPerDay", 2)), ids.size()))

func party_unavailable(id: String, day := -1) -> bool:
	var d := int(progress["day"]) if day < 0 else day
	for c in cohort:
		if c["id"] == id:
			return classmate_status(c, d)["away"] != ""
	return true

## After a run: whoever was down is carried out by the rescue team and spends days in the
## infirmary. Returns their names.
func _carry_out_fallen() -> Array:
	var out: Array = []
	if not fight or fight.allies.is_empty():
		return out
	var sch: Dictionary = Data.academy["cohort"].get("schedule", {})
	for al in fight.allies:
		if not al["down"] or al.get("passenger", false) or String(al.get("id", "")) == "":
			continue
		out.append(String(al["name"]))
		if not progress.has("infirmary"):
			progress["infirmary"] = {}
		progress["infirmary"][al["id"]] = int(progress["day"]) + int(sch.get("infirmaryDays", 2))
		progress["record"]["carried_out"] = int(progress["record"].get("carried_out", 0)) + 1
		if not progress.has("writeup_extra"):
			progress["writeup_extra"] = []
		progress["writeup_extra"].append(fill(String(sch.get("lines", {}).get("carriedOut", "")), _classmate(al["id"])))
	return out

# --- The season's crisis: the Omen, Pressure, the Crisis, the Reckoning ---------------------
# One crisis a term (data/crises.json). Its phase follows the term; its Ledgers take weight
# from the quests done (the type that serves a Ledger, by the line colour), from a Writ's
# decision, and from the crisis postings; the Reckoning at the Gate reads the heaviest and
# writes the ending onto the character for the server.

## How many hunts a named beast has escaped this term.
func named_escapes(id: String) -> int:
	return int(progress.get("named", {}).get(id, {}).get("escaped", 0))

func crisis() -> Dictionary:
	var all: Array = Data.crises()
	return all[0] if not all.is_empty() else {}

func crisis_phase() -> String:
	if progress.has("reckoning") or progress["done"].has("gate"):
		return "reckoning"
	if progress["done"].has("project"):
		return "crisis"
	if progress["done"].has("line"):
		return "pressure"
	return "omen"

func ledgers() -> Dictionary:
	var c := crisis()
	var out := {}
	for k in c.get("ledgers", {}):
		out[k] = int(progress.get("ledgers", {}).get(k, 0))
	return out

func _add_weight(ledger: String, w: int) -> void:
	if not progress.has("ledgers"):
		progress["ledgers"] = {}
	progress["ledgers"][ledger] = int(progress["ledgers"].get(ledger, 0)) + w

## A quest done weighs the Ledger its type serves (the crisis's own postings weigh threefold).
func weigh_ledgers(p: Dictionary) -> void:
	var c := crisis()
	if c.is_empty() or crisis_phase() in ["omen", "reckoning"]:
		return
	var w := int(c["weights"].get(p.get("colour", "green"), 1))
	if p.has("crisis_ledger"):
		_add_weight(p["crisis_ledger"], w * int(c["weights"].get("crisis", 3)))
		return
	for k in c["ledgers"]:
		if c["ledgers"][k]["serves"].has(p["type"]):
			_add_weight(k, w)

## A decision in a quest (a Writ's) weighs the Ledgers that name it.
func weigh_decision(key: String) -> void:
	var c := crisis()
	if c.is_empty() or crisis_phase() in ["omen", "reckoning"]:
		return
	for k in c["ledgers"]:
		var d: Dictionary = c["ledgers"][k].get("decisions", {})
		if d.has(key):
			_add_weight(k, int(d[key]))

## The crisis's own posting for the day, while its Ledgers are open.
func crisis_posting(day: int, rng: RandomNumberGenerator) -> Dictionary:
	var c := crisis()
	var phase := crisis_phase()
	if c.is_empty() or phase not in ["pressure", "crisis"]:
		return {}
	if phase == "pressure" and day % 2 == 0:
		return {}
	var open_ids: Array = zones_open().map(func(z): return z["id"])
	var fit: Array = c["crisisQuests"].filter(func(q):
		var t: Dictionary = Data.quests["types"][q["type"]]
		return open_ids.has(q["zone"]) and (not t.has("requires") or progress["done"].has(String(t["requires"]))))
	if fit.is_empty():
		return {}
	var cq: Dictionary = fit[rng.randi() % fit.size()]
	var t: Dictionary = Data.quests["types"][cq["type"]]
	var z: Dictionary = Data.zone(cq["zone"])
	var named: Array = z["beasts"].get("named", [])
	var p := { "id": "crisis:%d" % day, "day": day, "type": cq["type"], "zone": z["id"], "colour": z["colour"], "poster": "The Compact's crisis board",
		"pay": int(t["pay"].get(z["colour"], 1)) + 1, "entry": "%s/%s" % [z["id"], z["areas"][0]["id"]], "post": "", "elite": "",
		"named": named[rng.randi() % named.size()] if not named.is_empty() else {}, "crisis_ledger": cq["ledger"] }
	for a in z["areas"]:
		if a.has("post") and p["post"] == "":
			p["post"] = "%s/%s" % [z["id"], a["id"]]
		if a.get("beast", "") == "elite" and p["elite"] == "":
			p["elite"] = "%s/%s" % [z["id"], a["id"]]
	p["title"] = fill_quest(cq["title"], p)
	p["posting"] = fill_quest(cq["posting"], p)
	return p

## What the board says of the Ledgers.
func ledgers_text() -> String:
	var c := crisis()
	if c.is_empty():
		return ""
	var phase := crisis_phase()
	var parts: Array = []
	var L := ledgers()
	for k in L:
		parts.append("%s %d" % [c["ledgers"][k]["name"], int(L[k])])
	var notice := String(c["notices"].get(phase, ""))
	if phase == "omen":
		return notice
	return "%s  [i]%s[/i]" % [notice, "  ·  ".join(parts)]

## The Reckoning: the heaviest Ledger with a quarter of the weight, else the default; written
## onto the character as the world the server will know.
func reckoning() -> Dictionary:
	var c := crisis()
	if c.is_empty():
		return {}
	if progress.has("reckoning"):
		return c["endings"][progress["reckoning"]]
	var L := ledgers()
	var total := 0
	var best := ""
	var best_w := -1
	for k in L:
		total += int(L[k])
		if int(L[k]) > best_w:
			best_w = int(L[k])
			best = k
	var key: String = c["default"]
	if total > 0 and best_w * 4 >= total and best_w > 0:
		key = best
	progress["reckoning"] = key
	var e: Dictionary = c["endings"][key]
	var world_state: Dictionary = e["world"].duplicate()
	world_state["crisis"] = c["id"]
	world_state["ending"] = key
	world_state["chronicle"] = e["chronicle"]
	world_state["ledgers"] = L
	hero["world"] = world_state
	save()
	return e

# --- Gear: the yard's smith, named weapons, the Archive's fragments ---------------------------

## A stinger from the score, when the game has one.
func _sting(name: String) -> void:
	var par := get_parent()
	if par and "music" in par and par.music:
		par.music.sting(name)

## Marks spent at the smith are kept apart from the record's Marks (ranks read the record).
func marks_spendable() -> int:
	return int(progress["record"].get("marks", 0)) - int(progress.get("marks_spent", 0))

func weapon_name() -> String:
	var g: Dictionary = hero.get("gear", {})
	var w: Dictionary = Data.by_id(Data.weapons, hero.get("weapon", "saber"))
	match String(g.get("tier", "plain")):
		"fine": return "a fine %s" % String(w["name"]).to_lower()
		"named": return String(g.get("name", w["name"]))
	return String(w["name"])

func _smith() -> void:
	var sm: Dictionary = Data.gear["smith"]
	var L: Dictionary = sm["lines"]
	var g: Dictionary = hero.get("gear", { "tier": "plain" })
	var cost := int(Data.gear["tiers"]["fine"].get("costMarks", 3))
	var w: Dictionary = Data.by_id(Data.weapons, hero["weapon"])
	progress["record"]["talks"] += 1
	if String(g.get("tier", "plain")) != "plain":
		say({ "name": sm["name"], "sub": sm["title"] }, [L["have"]])
		return
	say({ "name": sm["name"], "sub": sm["title"] }, [L["default"], String(L["offer"]).replace("{weapon}", String(w["name"]).to_lower()).replace("{cost}", str(cost))], func():
		var opts: Array = [{ "id": "buy", "label": "A fine %s  ·  %d Marks" % [String(w["name"]).to_lower(), cost], "text": "%s\n[i]You have %d Marks to spend.[/i]" % [Data.gear["tiers"]["fine"].get("text", "It hits a tenth harder and it shows."), marks_spendable()] },
			{ "id": "no", "label": "Not today", "text": "The bench will be here." }]
		choose("The smith's bench", opts, func(id: String):
			if id != "buy":
				return
			if marks_spendable() < cost:
				say({ "name": sm["name"], "sub": sm["title"] }, [String(L["short"]).replace("{cost}", str(cost))])
				return
			progress["marks_spent"] = int(progress.get("marks_spent", 0)) + cost
			hero["gear"] = { "tier": "fine", "name": "", "trait": "" }
			progress["record"]["gear_bought"] = int(progress["record"].get("gear_bought", 0)) + 1
			save()
			go(progress["place"], true, "")
			title_card("A FINE %s" % String(w["name"]).to_upper(), "it shows", Style.GOLD)
			sfx.play("done")
			say({ "name": sm["name"], "sub": sm["title"] }, [L["bought"]])))

## What a run leaves in the hand: a Hunt's named beast gives the zone's named weapon; three
## Salvage fragments make the Archive's own.
func _gear_from_run(p: Dictionary) -> void:
	var order := { "plain": 0, "fine": 1, "named": 2 }
	var have := int(order.get(String(hero.get("gear", {}).get("tier", "plain")), 0))
	var grant: Dictionary = {}
	if p["type"] == "hunt" and Data.gear["named"].has(p["zone"]):
		grant = Data.gear["named"][p["zone"]]
	elif p["type"] == "salvage":
		progress["fragments"] = int(progress.get("fragments", 0)) + 1
		if int(progress["fragments"]) >= int(Data.gear["archive"].get("fragments", 3)):
			progress["fragments"] = 0
			grant = Data.gear["archive"]
	if grant.is_empty():
		return
	progress["record"]["named_weapons"] = int(progress["record"].get("named_weapons", 0)) + 1
	if have >= 2 and String(hero.get("gear", {}).get("name", "")) == grant["name"]:
		return
	hero["gear"] = { "tier": "named", "name": grant["name"], "trait": grant["trait"] }
	if not progress.has("writeup_extra"):
		progress["writeup_extra"] = []
	progress["writeup_extra"].append("Carries %s, %s." % [grant["name"], grant.get("text", "")])
	title_card(String(grant["name"]).to_upper(), "a named weapon: %s" % Data.gear["traits"][grant["trait"]]["text"], Style.GOLD)
	sfx.play("done")

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
	say({ "name": sd["name"], "sub": "a shade of the hearth · once a %s" % String(sd["discipline"]).capitalize() }, lines, func():
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
