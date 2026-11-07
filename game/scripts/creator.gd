## The character creator: questions about the life before the field woke, then the reveal of
## who those answers made. The blood is suggested and confirmed (or another is chosen); the
## rest is read from the answers, each with its reason. Name and body are the player's.
class_name Creator
extends CanvasLayer

signal finished(hero: Dictionary)
signal cancelled
signal clicked                     # a button was pressed: a soft sound
signal changed(hero: Dictionary)   # the reveal changed: the world redraws the character

const BG := Color(0.03, 0.025, 0.025, 0.86)
const PANEL := Color(0.06, 0.05, 0.045, 0.94)
const FG := Color(0.94, 0.9, 0.83)
const DIM := Color(0.62, 0.58, 0.52)
const GOLD := Color(1.0, 0.8, 0.35)
const EDGE := Color(0.32, 0.27, 0.21)

var answers: Array = []
var hero: Dictionary = {}
var spark := 1                # this character's spark: nudges the leans, picks the name
var _field_col := Color(0.6, 0.9, 0.7)
var _field_k := 0.0
var blood_choice := ""
var _q := 0
var _root := Control.new()
var _bg := ColorRect.new()

func _ready() -> void:
	layer = 15
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)

func begin() -> void:
	visible = true
	answers = []
	blood_choice = ""
	hero = {}
	spark = _new_spark()
	_q = 0
	_field_k = 0.0
	_intro()

static func _new_spark() -> int:
	return 1 + randi() % 2000000000

## The field gathering as you answer: the colour of the Shapes your answers lean toward so far,
## brighter with every answer.
func _field_now() -> void:
	var t := Creation.tally_with(answers, spark)
	var total := 0.0
	var c := Color(0, 0, 0)
	for s in t["shape"]:
		var w := pow(maxf(0.0, float(t["shape"][s])), 2.0)
		c += World.SHAPE_COLORS.get(s, Color.WHITE) * w
		total += w
	if total > 0.0:
		_field_col = Color(c.r / total, c.g / total, c.b / total)
	_field_k = clampf(float(answers.size()) / float(Data.creation["questions"].size()), 0.0, 1.0)

func _clear() -> void:
	for c in _root.get_children():
		_root.remove_child(c)
		c.queue_free()

# --- The opening card ------------------------------------------------------------

func _intro() -> void:
	_screen = "other"
	_clear()
	_backdrop()
	var box := _centered(760)
	_text(box, "WILDLINE  ·  THE MAKING OF A LIFE", 14, Style.BRASS, "title_light")
	_text(box, "Before the Field", 52, FG, "title")
	box.add_child(Style.rule(420))
	_text(box, "Ten thousand years ago, the will of every living thing became a force in the world. It still wakes in every child, at the edge of growing up, and settles into a Shape.\n\nYours has not woken yet. Before it does, tell us who you were.", 19, FG)
	_text(box, "There are no right answers. Your answers lean your blood, your Shape, your weapon, what will stand beside you, and the Terms you would accept for power. You will see all of it, and why, before anything is final.", 15, DIM)
	_button(box, "Begin", func(): _ask(0), true)
	_button(box, "Surprise me: answer at random", _surprise)
	_button(box, "Back", func(): cancelled.emit())
	_arrive(box)

# --- The questions ----------------------------------------------------------------

func _ask(i: int, all_shown := false) -> void:
	_screen = "other"
	_q = i
	_clear()
	_backdrop()
	var qs: Array = Data.creation["questions"]
	var q: Dictionary = qs[i]
	var box := _centered(860)
	box.add_child(_progress(i, qs.size()))
	_text(box, q["ask"], 34, FG, "body")
	box.add_child(Style.rule(300, Style.BRASS_DIM))
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 6)
	box.add_child(gap)
	# Five of the answers, drawn by this character's spark, each a card with its emblem; the
	# rest wait behind "the others". An answer already given is always among the five.
	var order: Array = range(q["answers"].size())
	var rng := RandomNumberGenerator.new()
	rng.seed = spark + i * 101
	Academy._shuffle(order, rng)
	var given: int = int(answers[i]) if answers.size() > i else -1
	if given >= 0 and order.find(given) >= CARDS_SHOWN:
		order.erase(given)
		order.insert(0, given)
	var shown: Array = order if (all_shown or order.size() <= CARDS_SHOWN) else order.slice(0, CARDS_SHOWN)
	var grid := GridContainer.new()
	grid.columns = 1
	grid.add_theme_constant_override("v_separation", 8)
	box.add_child(grid)
	var numerals := ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]
	for n in shown.size():
		var ai: int = shown[n]
		grid.add_child(_card(q["answers"][ai], numerals[n], ai == given, func(): _answer(i, ai)))
	var foot := HBoxContainer.new()
	foot.add_theme_constant_override("separation", 12)
	box.add_child(foot)
	if shown.size() < order.size():
		var more := _button(foot, "The others  (%d)" % (order.size() - shown.size()), func(): _ask(i, true))
		more.autowrap_mode = TextServer.AUTOWRAP_OFF
		more.add_theme_color_override("font_color", DIM)
	if i > 0:
		var back := _button(foot, "Back", func(): _ask(i - 1))
		back.autowrap_mode = TextServer.AUTOWRAP_OFF
		back.add_theme_color_override("font_color", DIM)
	_arrive(box)

const CARDS_SHOWN := 5

## One answer as a card: its emblem in the colour of its lean, a numeral, its title, its words.
func _card(a: Dictionary, numeral: String, chosen: bool, cb: Callable) -> Control:
	var b := Button.new()
	b.custom_minimum_size = Vector2(0, 92)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_style(b, chosen, 17, "body")
	b.pressed.connect(func(): clicked.emit(); cb.call())
	var col := _lean_color(a)
	var row := HBoxContainer.new()
	row.set_anchors_preset(Control.PRESET_FULL_RECT)
	row.offset_left = 12
	row.offset_right = -12
	row.offset_top = 8
	row.offset_bottom = -8
	row.add_theme_constant_override("separation", 16)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(row)
	var em := emblem(String(a.get("emblem", "")), col, 68.0)
	em.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(em)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.add_theme_constant_override("separation", 2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(v)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(head)
	var num := _text(head, numeral, 13, col.lerp(Style.BRASS, 0.5), "title_light")
	num.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var title := _text(head, String(a.get("title", "")).to_upper(), 14, col, "title")
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var words := _text(v, String(a["text"]), 17, FG if not chosen else GOLD, "body")
	words.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b

## The colour an answer leans: its Shape's, else its city's, else the blood's, else brass.
func _lean_color(a: Dictionary) -> Color:
	var shapes: Dictionary = a.get("shape", {})
	if not shapes.is_empty():
		var best := ""
		for sh in shapes:
			if best == "" or float(shapes[sh]) > float(shapes[best]):
				best = sh
		return World.SHAPE_COLORS.get(best, Style.BRASS)
	if a.has("city"):
		return World.CITY_COLORS.get(a["city"], Style.BRASS).lightened(0.25)
	if a.has("blood") or a.has("tier"):
		return Style.BLOOD.lightened(0.2)
	if a.has("style") or a.has("effect"):
		return Style.GOLD
	return Style.BRASS

## An emblem drawn from its strokes (data/emblems.json), `size` across, in `col`.
static func emblem(id: String, col: Color, size: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(size, size)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var strokes: Array = Data.emblems.get(id, {}).get("strokes", [])
	c.draw.connect(func():
		var w := maxf(2.0, size / 28.0)
		c.draw_circle(Vector2(size / 2.0, size / 2.0), size / 2.0, Color(col, 0.08))
		c.draw_arc(Vector2(size / 2.0, size / 2.0), size / 2.0 - 1.0, 0.0, TAU, 48, Color(col, 0.35), 1.0, true)
		for st in strokes:
			var fill: bool = st.get("fill", false)
			if st.has("line"):
				var pts := PackedVector2Array()
				for p in st["line"]:
					pts.append(Vector2(p[0], p[1]) * size)
				c.draw_polyline(pts, col, w, true)
			elif st.has("poly"):
				var pts2 := PackedVector2Array()
				for p in st["poly"]:
					pts2.append(Vector2(p[0], p[1]) * size)
				if fill:
					c.draw_colored_polygon(pts2, col)
				else:
					pts2.append(pts2[0])
					c.draw_polyline(pts2, col, w, true)
			elif st.has("circle"):
				var cc: Array = st["circle"]
				if fill:
					c.draw_circle(Vector2(cc[0], cc[1]) * size, cc[2] * size, col)
				else:
					c.draw_arc(Vector2(cc[0], cc[1]) * size, cc[2] * size, 0.0, TAU, 40, col, w, true)
			elif st.has("arc"):
				var ar: Array = st["arc"]
				c.draw_arc(Vector2(ar[0], ar[1]) * size, ar[2] * size, deg_to_rad(float(ar[3])), deg_to_rad(float(ar[4])), 32, col, w, true))
	return c

## Where you are in the questions: a row of lozenges, the answered ones lit.
func _progress(i: int, n: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, 22)
	c.draw.connect(func():
		for k in n:
			var x := 7.0 + k * 22.0
			var y := 11.0
			var r := 6.0 if k == i else 4.5
			var pts := PackedVector2Array([Vector2(x, y - r), Vector2(x + r, y), Vector2(x, y + r), Vector2(x - r, y)])
			if k < i:
				c.draw_colored_polygon(pts, Style.BRASS)
			elif k == i:
				c.draw_colored_polygon(pts, Style.BRASS_HI)
			else:
				pts.append(pts[0])
				c.draw_polyline(pts, Style.BRASS_DIM, 1.0)
		var f := Style.font("ui")
		c.draw_string(f, Vector2(n * 22.0 + 12.0, 16.0), "%d of %d" % [i + 1, n], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, DIM)
	)
	return c

## Answer every question at random and go straight to who that made.
func _surprise() -> void:
	answers = []
	for q in Data.creation["questions"]:
		answers.append(randi() % q["answers"].size())
	blood_choice = ""
	_reveal()

func _answer(i: int, ai: int) -> void:
	while answers.size() <= i:
		answers.append(0)
	answers[i] = ai
	if i + 1 < Data.creation["questions"].size():
		_ask(i + 1)
	else:
		blood_choice = ""
		_reveal()

var _screen := ""

# --- The reveal --------------------------------------------------------------------

func _reveal() -> void:
	var keep_name: String = hero.get("name", "")
	var keep_body: String = hero.get("body_override", "")
	var keep_weapon: String = hero.get("weapon_override", "")
	var keep_look: Dictionary = hero.get("look", {})
	hero = Creation.generate(answers, blood_choice, spark)
	if keep_body != "":
		hero["body"] = keep_body
		hero["body_override"] = keep_body
	if keep_weapon != "":
		hero["weapon"] = keep_weapon
		hero["weapon_override"] = keep_weapon
	if not keep_look.is_empty():
		hero["look"] = keep_look
		hero["body"] = "%s-%s" % [hero["city"], String(keep_look.get("sex", "m"))]
	if keep_name == "":
		keep_name = Creation.name_for(hero["city"], spark)
	hero["name"] = keep_name
	changed.emit(hero)
	_clear()
	# The left of the screen is the character, standing in the world; the reveal is on the right.
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	panel.offset_left = -820
	var ps := Style.plate(Color(0.04, 0.034, 0.03, 0.93), Style.BRASS_DIM, 1, 26, 0)
	ps.border_width_top = 0
	ps.border_width_bottom = 0
	ps.border_width_right = 0
	ps.border_width_left = 2
	ps.border_color = Style.BRASS
	ps.shadow_size = 40
	ps.shadow_color = Color(0, 0, 0, 0.6)
	panel.add_theme_stylebox_override("panel", ps)
	_root.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(780, 0)
	v.add_theme_constant_override("separation", 6)
	scroll.add_child(v)

	_text(v, "WHO YOUR ANSWERS MADE", 14, Style.BRASS, "title_light")
	var title := _text(v, hero["name"] if hero["name"] != "" else "Unnamed", 44, FG, "title")
	v.add_child(Style.rule(380))
	# Name.
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	v.add_child(row)
	_text(row, "Name", 17, DIM)
	var name_edit := LineEdit.new()
	name_edit.text = hero["name"]
	name_edit.custom_minimum_size = Vector2(320, 0)
	name_edit.max_length = 24
	name_edit.add_theme_font_size_override("font_size", 18)
	name_edit.text_changed.connect(func(t): hero["name"] = t)
	row.add_child(name_edit)

	# Blood.
	var b := Creation.blood(hero["blood"])
	_section(v, "BLOOD", "%s  ·  %s" % [b["name"], String(b["tier"]).capitalize()])
	_line(v, "Shows as %s. %s" % [b.get("shows", "nothing"), b["gift"] + "."])
	_line(v, "The Gap: %s." % b["gap"], DIM)
	var reasons := ""
	for s in Creation.suggest_bloods(Creation.tally_with(answers, spark), 26):
		if s["id"] == hero["blood"]:
			reasons = ", ".join(s["reasons"])
	if reasons != "":
		_line(v, "Because %s." % reasons, DIM)
	var alt := HBoxContainer.new()
	alt.add_theme_constant_override("separation", 8)
	v.add_child(alt)
	_text(alt, "Or:", 15, DIM)
	for s in Creation.suggest_bloods(Creation.tally_with(answers, spark)):
		if s["id"] != hero["blood"]:
			var id: String = s["id"]
			_chip(alt, Creation.blood(id)["name"], func(): blood_choice = id; _reveal())
	_chip(alt, "Choose another...", _choose_blood)

	# Shape, city, weapon.
	_section(v, "SHAPE", String(hero["shape"]).capitalize())
	_line(v, Data.shape(hero["shape"])["field"] + ". " + _shape_line(hero["shape"]))
	_line(v, "Because %s. (The rite at the Academy will read it, and may not agree.)" % ", ".join(hero["why"]["shape"]), DIM)
	var w := Creation.weapon(hero["weapon"])
	_section(v, "HOME AND WEAPON", "%s  ·  %s" % [String(hero["city"]).capitalize(), w["name"]])
	var wtype: Dictionary = Data.room["styles"].get(w["style"], {})
	_line(v, "%s %s The %s Discipline teaches it." % [w["text"], wtype.get("text", ""), String(hero["discipline"]).capitalize()])
	_line(v, "Because %s." % ", ".join(hero["why"]["city"] + hero["why"]["weapon"]), DIM)
	# The city's other weapons, in the hand at once.
	var wrow := HBoxContainer.new()
	wrow.add_theme_constant_override("separation", 8)
	v.add_child(wrow)
	_text(wrow, "Or carry:", 15, DIM)
	# A home without a school of its own (Alexandria) carries the weapons of the school it took.
	var school_city: String = hero["city"]
	if Data.weapons.filter(func(cw): return cw["city"] == hero["city"]).is_empty():
		for d in Data.disciplines:
			if d["id"] == hero["discipline"]:
				school_city = d["city"]
	for cw in Data.weapons:
		if cw["city"] != school_city:
			continue
		var wid: String = cw["id"]
		_chip(wrow, cw["name"], func(): hero["weapon_override"] = wid; hero["weapon"] = wid; changed.emit(hero); _reveal(), hero["weapon"] == wid)
	# Technique and stance.
	var kit: Dictionary = Data.kits[hero["shape"]]
	_line(v, "Technique: [b]%s[/b]. %s" % [kit["technique"]["name"], kit["technique"]["text"]])
	_line(v, "Stance: [b]%s[/b]: %s." % [kit["stance"]["name"], kit["stance"]["text"]])
	# The Seed.
	_section(v, "WHAT WILL STAND BESIDE YOU", _seed_text(hero["seed"]))
	_line(v, "Your genius takes its First Form at the rite, read from this, your blood, and your Shape.", DIM)
	# The Pattern.
	var p: Dictionary = hero["pattern"]
	_section(v, "YOUR PATTERN", "x%s  ·  chain of %d" % [str(snappedf(Fight.multiplier_of(p), 0.01)), Fight.chain_length(p)])
	_line(v, Builder.sentence(p))
	_line(v, Builder.payout(p) + ".", GOLD)
	var pw: Array = []
	if hero["why"]["form"].size() > 0: pw.append("its Form because %s" % ", ".join(hero["why"]["form"]))
	for k in ["trigger", "toll", "bar"]:
		if hero["why"][k] != "": pw.append(hero["why"][k])
	if pw.size() > 0:
		_line(v, "Because %s." % "; ".join(pw), DIM)
	_line(v, "It is yours from the start. You will outgrow it.", DIM)
	# The body: its sex, its build, its skin; then the look. It shows at once, on the left.
	var look: Dictionary = hero.get("look", { "headgear": true, "cape": true, "cape_color": "shape" })
	hero["look"] = look
	var L: Dictionary = Data.creation.get("look", {})
	_section(v, "BODY", "")
	var bodies := HBoxContainer.new()
	bodies.add_theme_constant_override("separation", 8)
	v.add_child(bodies)
	for sx in L.get("sexes", {}):
		var sid: String = sx
		_chip(bodies, L["sexes"][sx], func(): look["sex"] = sid; hero["body"] = "%s-%s" % [hero["city"], sid]; changed.emit(hero); _reveal(), String(look.get("sex", "m")) == sid)
	var brow0 := HBoxContainer.new()
	brow0.add_theme_constant_override("separation", 8)
	v.add_child(brow0)
	_text(brow0, "Build:", 15, DIM)
	for bd in L.get("builds", {}):
		var bv: float = float(L["builds"][bd])
		_chip(brow0, bd, func(): look["build"] = bv; changed.emit(hero); _reveal(), absf(float(look.get("build", 0.0)) - bv) < 0.001)
	var srow0 := HBoxContainer.new()
	srow0.add_theme_constant_override("separation", 8)
	v.add_child(srow0)
	_text(srow0, "Skin:", 15, DIM)
	# The home's palette (data/bodies.json); every tone if the home has none.
	var palette: Array = Data.bodies.get(hero["city"], {}).get("palette", L.get("skinTones", {}).keys())
	for tn in palette:
		var tid: String = tn
		_chip(srow0, tid, func(): look["skin"] = tid; changed.emit(hero); _reveal(), String(look.get("skin", "olive")) == tid)
	_section(v, "LOOK", "")
	var lrow := HBoxContainer.new()
	lrow.add_theme_constant_override("separation", 8)
	v.add_child(lrow)
	_chip(lrow, "Headgear on", func(): look["headgear"] = not look["headgear"]; changed.emit(hero); _reveal(), look["headgear"])
	_chip(lrow, "Cape on", func(): look["cape"] = not look["cape"]; changed.emit(hero); _reveal(), look["cape"])
	var hrow := HBoxContainer.new()
	hrow.add_theme_constant_override("separation", 8)
	v.add_child(hrow)
	_text(hrow, "Hair:", 15, DIM)
	for hs in L.get("hair", []):
		var hid: String = hs
		_chip(hrow, hid, func(): look["hair"] = hid; changed.emit(hero); _reveal(), String(look.get("hair", "crop")) == hid)
	var brow := HBoxContainer.new()
	brow.add_theme_constant_override("separation", 8)
	v.add_child(brow)
	_text(brow, "Beard:", 15, DIM)
	for bs in L.get("beards", []):
		var bid2: String = bs
		_chip(brow, bid2, func(): look["beard"] = bid2; changed.emit(hero); _reveal(), String(look.get("beard", "none")) == bid2)
	var hcrow := HBoxContainer.new()
	hcrow.add_theme_constant_override("separation", 8)
	v.add_child(hcrow)
	_text(hcrow, "Colour:", 15, DIM)
	for hc in L.get("hairColors", {}):
		var cid0: String = hc
		_chip(hcrow, cid0, func(): look["hair_color"] = cid0; changed.emit(hero); _reveal(), String(look.get("hair_color", "brown")) == cid0)
	var srow := HBoxContainer.new()
	srow.add_theme_constant_override("separation", 8)
	v.add_child(srow)
	_text(srow, "Stature:", 15, DIM)
	for st in L.get("statures", {}):
		var sv: float = float(L["statures"][st])
		_chip(srow, st, func(): look["stature"] = sv; changed.emit(hero); _reveal(), absf(float(look.get("stature", 1.0)) - sv) < 0.001)
	var crow := HBoxContainer.new()
	crow.add_theme_constant_override("separation", 8)
	v.add_child(crow)
	_text(crow, "Cape:", 15, DIM)
	for cc in L.get("capeColors", {}):
		var cid: String = cc
		_chip(crow, L["capeColors"][cc], func(): look["cape_color"] = cid; changed.emit(hero); _reveal(), look["cape_color"] == cid)
	var end := HBoxContainer.new()
	end.add_theme_constant_override("separation", 12)
	v.add_child(end)
	_button(end, "This is me", func(): finished.emit(hero), true)
	_button(end, "Answer again", func(): hero = {}; _ask(0))
	_button(end, "Another life, same answers", func(): hero = {}; blood_choice = ""; spark = _new_spark(); _reveal())
	name_edit.text_changed.connect(func(t): title.text = t if t != "" else "Unnamed")
	if _screen != "reveal":
		_arrive(v)
		panel.modulate.a = 0.0
		panel.create_tween().tween_property(panel, "modulate:a", 1.0, 0.4)
	_screen = "reveal"

func _shape_line(shape: String) -> String:
	match shape:
		"anchor": return "Strength, endurance, the wall."
		"turn": return "Elements and properties: fire, cold, conversion."
		"cast": return "Range, projection, speed: the shot."
		"read": return "Senses, foresight, the break, mending."
		"bind": return "Control, contracts, the leash."
		"make": return "Constructs, conjured weapons, wards."
	return ""

func _seed_text(id: String) -> String:
	for q in Data.creation["questions"]:
		for a in q["answers"]:
			if a.get("seed", "") == id:
				return a["text"]
	return id

func _choose_blood() -> void:
	_screen = "other"
	_clear()
	_backdrop()
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.offset_left = 60
	scroll.offset_right = -60
	scroll.offset_top = 30
	scroll.offset_bottom = -30
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_root.add_child(scroll)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 6)
	scroll.add_child(v)
	_text(v, "Choose Your Blood", 42, FG, "title")
	v.add_child(Style.rule(380))
	_text(v, "The peoples and bloodlines that came out of the Awakening, and the single Marks that come to anyone.", 15, DIM)
	for tier in [["bloodline", "BLOODLINES  ·  strong blood, registered by the cities"], ["kindred", "KINDREDS  ·  peoples who carry it together"], ["mark", "MARKS  ·  one mutation, yours alone"]]:
		var gap := Control.new()
		gap.custom_minimum_size = Vector2(0, 8)
		v.add_child(gap)
		_text(v, tier[1], 16, Style.BRASS, "title")
		var grid := GridContainer.new()
		grid.columns = 3
		grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grid.add_theme_constant_override("h_separation", 8)
		grid.add_theme_constant_override("v_separation", 8)
		v.add_child(grid)
		for b in Data.bloods:
			if b["tier"] != tier[0]:
				continue
			var id: String = b["id"]
			var btn := Button.new()
			btn.text = "%s\n%s\nGap: %s" % [b["name"], b["gift"], b["gap"]]
			btn.autowrap_mode = TextServer.AUTOWRAP_WORD
			btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
			btn.custom_minimum_size = Vector2(0, 96)
			btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			_style(btn, id == hero["blood"], 14, "ui")
			btn.pressed.connect(func(): blood_choice = id; _reveal())
			grid.add_child(btn)
	_button(v, "Back", _reveal)
	_arrive(v)

# --- Helpers ---------------------------------------------------------------------

func _centered(width: float) -> VBoxContainer:
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(c)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(width, 0)
	v.add_theme_constant_override("separation", 10)
	c.add_child(v)
	return v

func _text(parent: Control, t: String, size: int, color: Color, kind := "") -> Label:
	var l := Label.new()
	l.text = t
	# Labels in a row size to their text; elsewhere they wrap.
	if not (parent is HBoxContainer):
		l.autowrap_mode = TextServer.AUTOWRAP_WORD
	if kind == "":
		kind = "title" if size >= 28 else ("italic" if color == DIM and size <= 16 else ("body" if size >= 17 else "ui"))
	Style.label(l, size, color, kind)
	parent.add_child(l)
	return l

## A section of the reveal: a small brass heading over its value.
func _section(parent: Control, title: String, value: String) -> void:
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 10)
	parent.add_child(gap)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 10)
	parent.add_child(h)
	var t := Label.new()
	Style.label(t, 14, Style.BRASS, "title")
	t.text = title
	h.add_child(t)
	var r := Style.rule(200, Style.BRASS_DIM)
	r.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(r)
	if value != "":
		var l := Label.new()
		Style.label(l, 25, FG, "body_bold")
		l.autowrap_mode = TextServer.AUTOWRAP_WORD
		l.text = value
		parent.add_child(l)

func _line(parent: Control, t: String, color := FG) -> void:
	var l := RichTextLabel.new()
	l.bbcode_enabled = true
	l.fit_content = true
	l.scroll_active = false
	Style.rich(l, 17, color, "italic" if color == DIM else "body")
	l.text = t
	parent.add_child(l)

func _box(color: Color) -> StyleBoxFlat:
	return Style.plate(color, Style.BRASS_DIM, 1, 14)

func _style(b: Button, on := false, size := 19, kind := "body") -> void:
	Style.button(b, on, size, kind)

func _button(parent: Control, t: String, cb: Callable, primary := false) -> Button:
	var b := Button.new()
	b.text = t
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.autowrap_mode = TextServer.AUTOWRAP_WORD
	b.custom_minimum_size = Vector2(0, 50)
	_style(b, primary, 19)
	b.pressed.connect(func(): _click(); cb.call())
	parent.add_child(b)
	if primary:
		b.call_deferred("grab_focus")
	return b

func _chip(parent: Control, t: String, cb: Callable, on := false) -> void:
	var b := Button.new()
	b.text = t
	_style(b, on, 15, "ui")
	for st in ["normal", "hover", "focus", "pressed", "hover_pressed"]:
		var sb := b.get_theme_stylebox(st) as StyleBoxFlat
		sb.content_margin_left = 12
		sb.content_margin_right = 12
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6
	b.pressed.connect(func(): _click(); cb.call())
	parent.add_child(b)

## The backdrop of the creator's screens: lamplight in the dark, with motes of field drifting.
func _backdrop() -> void:
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sh := Shader.new()
	sh.code = BACKDROP
	var sm := ShaderMaterial.new()
	sm.shader = sh
	bg.material = sm
	_root.add_child(bg)
	# The field: from where it was, to where the answers have taken it.
	sm.set_shader_parameter("field_col", Vector3(_field_col.r, _field_col.g, _field_col.b))
	sm.set_shader_parameter("field_k", _field_k)
	var before := _field_col
	var k0 := _field_k
	_field_now()
	var tw := bg.create_tween()
	tw.tween_method(func(u: float):
		var c := before.lerp(_field_col, u)
		sm.set_shader_parameter("field_col", Vector3(c.r, c.g, c.b))
		sm.set_shader_parameter("field_k", lerpf(k0, _field_k, u)), 0.0, 1.0, 1.2).set_trans(Tween.TRANS_SINE)

func _click() -> void:
	clicked.emit()

## Every screen of the creator arrives: its pieces fade in, one after another.
func _arrive(box: Control) -> void:
	var i := 0
	for c in box.get_children():
		if c is CanvasItem:
			var it := c as CanvasItem
			it.modulate.a = 0.0
			it.create_tween().tween_property(it, "modulate:a", 1.0, 0.35).set_delay(0.045 * i).set_trans(Tween.TRANS_SINE)
			i += 1

const BACKDROP := """
shader_type canvas_item;
uniform vec3 field_col = vec3(0.6, 0.9, 0.7);
uniform float field_k = 0.0;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void fragment() {
	vec2 uv = UV;
	vec3 col = vec3(0.022, 0.018, 0.018);
	// Lamplight from above the centre.
	float d = length((uv - vec2(0.5, 0.18)) * vec2(1.0, 1.4));
	col += vec3(0.16, 0.09, 0.04) * pow(max(0.0, 1.0 - d), 2.5);
	// Motes: a sparse grid of soft points drifting up, each with its own pace.
	float m = 0.0;
	for (int k = 0; k < 2; k++) {
		vec2 g = uv * vec2(28.0, 16.0) * (1.0 + float(k) * 0.6);
		g.y += TIME * (0.35 + float(k) * 0.2);
		vec2 id = floor(g);
		vec2 f = fract(g) - 0.5;
		float h = hash(id + float(k) * 17.0);
		if (h > 0.86) {
			vec2 o = vec2(hash(id + 3.1) - 0.5, hash(id + 7.7) - 0.5) * 0.6;
			o.x += 0.15 * sin(TIME * 0.7 + h * 30.0);
			float r = length(f - o);
			float tw = 0.5 + 0.5 * sin(TIME * 1.7 + h * 50.0);
			m += smoothstep(0.09, 0.0, r) * tw * (0.5 + 0.5 * float(k == 0));
		}
	}
	col += mix(vec3(0.55, 0.8, 0.55), field_col, field_k) * m * (0.32 + 0.5 * field_k);
	// Your field, gathering below: it takes the colour of the Shapes your answers lean toward.
	vec2 fp = (uv - vec2(0.5, 1.08)) * vec2(1.0, 1.5);
	float a = atan(fp.y, fp.x);
	float swirl = 0.85 + 0.15 * sin(a * 7.0 + TIME * 0.9) * sin(length(fp) * 14.0 - TIME * 1.6);
	float glow = pow(max(0.0, 1.0 - length(fp) * 1.25), 2.6) * swirl;
	col += field_col * glow * (0.08 + 0.55 * field_k) * (0.9 + 0.1 * sin(TIME * 1.3));
	float v = smoothstep(0.35, 1.0, length((uv - 0.5) * vec2(1.4, 1.0)));
	col *= 1.0 - v * 0.75;
	COLOR = vec4(col, 0.98);
}
"""
