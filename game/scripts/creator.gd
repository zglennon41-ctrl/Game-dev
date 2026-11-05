## The character creator: questions about the life before the field woke, then the reveal of
## who those answers made. The blood is suggested and confirmed (or another is chosen); the
## rest is read from the answers, each with its reason. Name and body are the player's.
class_name Creator
extends CanvasLayer

signal finished(hero: Dictionary)
signal cancelled
signal changed(hero: Dictionary)   # the reveal changed: the world redraws the character

const BG := Color(0.03, 0.025, 0.025, 0.86)
const PANEL := Color(0.06, 0.05, 0.045, 0.94)
const FG := Color(0.94, 0.9, 0.83)
const DIM := Color(0.62, 0.58, 0.52)
const GOLD := Color(1.0, 0.8, 0.35)
const EDGE := Color(0.32, 0.27, 0.21)

var answers: Array = []
var hero: Dictionary = {}
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
	_q = 0
	_intro()

func _clear() -> void:
	for c in _root.get_children():
		_root.remove_child(c)
		c.queue_free()

# --- The opening card ------------------------------------------------------------

func _intro() -> void:
	_clear()
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.018, 0.018, 0.97)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(bg)
	var box := _centered(760)
	_text(box, "BEFORE THE FIELD", 40, GOLD)
	_text(box, "Ten thousand years ago, the will of every living thing became a force in the world. It still wakes in every child, at the edge of growing up, and settles into a Shape.\n\nYours has not woken yet. Before it does, tell us who you were.", 19, FG)
	_text(box, "There are no right answers. Your answers lean your blood, your Shape, your weapon, what will stand beside you, and the Terms you would accept for power. You will see all of it, and why, before anything is final.", 15, DIM)
	_button(box, "Begin", func(): _ask(0), true)
	_button(box, "Back", func(): cancelled.emit())

# --- The questions ----------------------------------------------------------------

func _ask(i: int) -> void:
	_q = i
	_clear()
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.018, 0.018, 0.97)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(bg)
	var qs: Array = Data.creation["questions"]
	var q: Dictionary = qs[i]
	var box := _centered(780)
	_text(box, "%d / %d" % [i + 1, qs.size()], 15, DIM)
	_text(box, q["ask"], 34, FG)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 8)
	box.add_child(gap)
	for ai in q["answers"].size():
		var a: Dictionary = q["answers"][ai]
		var chosen: bool = answers.size() > i and int(answers[i]) == ai
		_button(box, a["text"], func(): _answer(i, ai), chosen)
	if i > 0:
		_button(box, "Back", func(): _ask(i - 1))

func _answer(i: int, ai: int) -> void:
	while answers.size() <= i:
		answers.append(0)
	answers[i] = ai
	if i + 1 < Data.creation["questions"].size():
		_ask(i + 1)
	else:
		blood_choice = ""
		_reveal()

# --- The reveal --------------------------------------------------------------------

func _reveal() -> void:
	var keep_name: String = hero.get("name", "")
	var keep_body: String = hero.get("body_override", "")
	hero = Creation.generate(answers, blood_choice)
	if keep_body != "":
		hero["body"] = keep_body
		hero["body_override"] = keep_body
	if keep_name == "":
		var names: Array = Data.creation["names"][hero["city"]]
		keep_name = names[(answers.reduce(func(a, b): return a + b, 0)) % names.size()]
	hero["name"] = keep_name
	changed.emit(hero)
	_clear()
	# The left of the screen is the character, standing in the world; the reveal is on the right.
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	panel.offset_left = -820
	panel.add_theme_stylebox_override("panel", _box(PANEL))
	_root.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(780, 0)
	v.add_theme_constant_override("separation", 6)
	scroll.add_child(v)

	_text(v, "WHO YOUR ANSWERS MADE", 30, GOLD)
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
	for s in Creation.suggest_bloods(Creation.tally(answers), 26):
		if s["id"] == hero["blood"]:
			reasons = ", ".join(s["reasons"])
	if reasons != "":
		_line(v, "Because %s." % reasons, DIM)
	var alt := HBoxContainer.new()
	alt.add_theme_constant_override("separation", 8)
	v.add_child(alt)
	_text(alt, "Or:", 15, DIM)
	for s in Creation.suggest_bloods(Creation.tally(answers)):
		if s["id"] != hero["blood"]:
			var id: String = s["id"]
			_chip(alt, Creation.blood(id)["name"], func(): blood_choice = id; _reveal())
	_chip(alt, "Choose another...", _choose_blood)

	# Shape, city, weapon.
	_section(v, "SHAPE", String(hero["shape"]).capitalize())
	_line(v, Data.shape(hero["shape"])["field"] + ". " + _shape_line(hero["shape"]))
	_line(v, "Because %s. (The rite at the Academy will confirm it.)" % ", ".join(hero["why"]["shape"]), DIM)
	var w := Creation.weapon(hero["weapon"])
	_section(v, "HOME AND WEAPON", "%s  ·  %s" % [String(hero["city"]).capitalize(), w["name"]])
	_line(v, "%s The %s Discipline teaches it." % [w["text"], String(hero["discipline"]).capitalize()])
	_line(v, "Because %s." % ", ".join(hero["why"]["city"] + hero["why"]["weapon"]), DIM)
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
	# Body.
	_section(v, "BODY", "")
	var bodies := HBoxContainer.new()
	bodies.add_theme_constant_override("separation", 8)
	v.add_child(bodies)
	for body in Data.creation["bodies"]:
		var bid: String = body
		_chip(bodies, bid.replace("_", " "), func(): hero["body_override"] = bid; hero["body"] = bid; changed.emit(hero); _reveal(), hero["body"] == bid)
	var end := HBoxContainer.new()
	end.add_theme_constant_override("separation", 12)
	v.add_child(end)
	_button(end, "This is me", func(): finished.emit(hero), true)
	_button(end, "Answer again", func(): hero = {}; _ask(0))

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
	_clear()
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.018, 0.018, 0.97)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(bg)
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
	_text(v, "CHOOSE YOUR BLOOD", 30, GOLD)
	_text(v, "The peoples and bloodlines that came out of the Awakening, and the single Marks that come to anyone.", 15, DIM)
	for tier in [["bloodline", "BLOODLINES  ·  strong blood, registered by the cities"], ["kindred", "KINDREDS  ·  peoples who carry it together"], ["mark", "MARKS  ·  one mutation, yours alone"]]:
		_text(v, tier[1], 19, FG)
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
			btn.add_theme_font_size_override("font_size", 13)
			_style(btn, id == hero["blood"])
			btn.pressed.connect(func(): blood_choice = id; _reveal())
			grid.add_child(btn)
	_button(v, "Back", _reveal)

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

func _text(parent: Control, t: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = t
	# Labels in a row size to their text; elsewhere they wrap.
	if not (parent is HBoxContainer):
		l.autowrap_mode = TextServer.AUTOWRAP_WORD
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	parent.add_child(l)
	return l

func _section(parent: Control, title: String, value: String) -> void:
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 6)
	parent.add_child(gap)
	var l := RichTextLabel.new()
	l.bbcode_enabled = true
	l.fit_content = true
	l.scroll_active = false
	l.add_theme_font_size_override("normal_font_size", 22)
	l.add_theme_color_override("default_color", FG)
	l.text = "[color=#9e958a]%s[/color]   %s" % [title, value]
	parent.add_child(l)

func _line(parent: Control, t: String, color := FG) -> void:
	var l := RichTextLabel.new()
	l.bbcode_enabled = true
	l.fit_content = true
	l.scroll_active = false
	l.add_theme_font_size_override("normal_font_size", 16)
	l.add_theme_font_size_override("bold_font_size", 16)
	l.add_theme_font_size_override("italics_font_size", 16)
	l.add_theme_color_override("default_color", color)
	l.text = t
	parent.add_child(l)

func _box(color: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.border_color = EDGE
	s.set_border_width_all(1)
	s.set_corner_radius_all(3)
	s.set_content_margin_all(14)
	return s

func _style(b: Button, on := false) -> void:
	b.add_theme_stylebox_override("normal", _box(Color(0.32, 0.22, 0.08) if on else Color(0.08, 0.07, 0.06)))
	b.add_theme_stylebox_override("hover", _box(Color(0.18, 0.13, 0.08)))
	b.add_theme_stylebox_override("focus", _box(Color(0.2, 0.14, 0.08)))
	b.add_theme_stylebox_override("pressed", _box(Color(0.32, 0.22, 0.08)))
	b.add_theme_color_override("font_color", GOLD if on else FG)

func _button(parent: Control, t: String, cb: Callable, primary := false) -> Button:
	var b := Button.new()
	b.text = "   " + t
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.autowrap_mode = TextServer.AUTOWRAP_WORD
	b.add_theme_font_size_override("font_size", 19)
	b.custom_minimum_size = Vector2(0, 48)
	_style(b, primary)
	b.pressed.connect(cb)
	parent.add_child(b)
	if primary:
		b.call_deferred("grab_focus")
	return b

func _chip(parent: Control, t: String, cb: Callable, on := false) -> void:
	var b := Button.new()
	b.text = " %s " % t
	b.add_theme_font_size_override("font_size", 15)
	_style(b, on)
	b.pressed.connect(cb)
	parent.add_child(b)
