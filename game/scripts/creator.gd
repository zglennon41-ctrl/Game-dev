## The character creator: questions about the life before the field woke, then the reveal of
## who those answers made. It is set on a platform on the line at night (data/creation.json,
## stage): the words stand on the right, the platform shows on the left, and the field gathers
## there as the answers come. At the reveal the figure steps out of it, and the right is a
## panel of four leaves: the Reading (blood, Shape, home, weapon, the Seed, the Pattern, each
## with its reason), the body, the face and hair, and the dress. The blood is suggested and
## confirmed (or another is chosen); the name and the look are the player's.
class_name Creator
extends CanvasLayer

signal finished(hero: Dictionary)
signal cancelled
signal clicked                          # a button was pressed: a soft sound
signal changed(hero: Dictionary)        # who the answers made changed: the world builds the character again
signal look_changed(hero: Dictionary)   # only the look changed: the world dresses the standing figure again
signal cleared                          # back to the questions: the platform stands empty
signal framed(kind: String)             # the camera's framing: wide, full, half or face
signal shifted(part: float)             # the part of the screen's width the words cover, on the right
signal turned(by: float)                # the figure is turned, in radians
signal field(col: Color, k: float, flare: float)   # the field at the spot: colour, how far gathered, a flare

# The interface's one palette (Style, from data/style.json).
static var BG: Color = Color(Style.INK, 0.86)
static var PANEL: Color = Style.PLATE
static var FG: Color = Style.FG
static var DIM: Color = Style.DIM
static var GOLD: Color = Style.GOLD
static var EDGE: Color = Style.BRASS_DIM
const PANEL_W := 640.0      # the reveal's panel
const COL_W := 700.0        # the column of the questions
const COL_MARGIN := 64.0
const TABS := [["reading", "The Reading"], ["body", "Body"], ["face", "Face and hair"], ["dress", "Dress"]]
const TAB_FRAMES := { "reading": "full", "body": "full", "face": "face", "dress": "full" }
const FRAMES := [["full", "Whole"], ["half", "Close"], ["face", "Face"]]

var answers: Array = []
var hero: Dictionary = {}
var spark := 1                # this character's spark: nudges the leans, picks the name
var tab := "reading"          # the leaf of the reveal that is open
var frame := "full"           # the camera's framing at the reveal
var _field_col := Color(0.6, 0.9, 0.7)
var _field_k := 0.0
var blood_choice := ""
var _q := 0
var _root := Control.new()
var _bg := ColorRect.new()
var _scroll_keep := 0

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
	_field_k = clampf(0.12 + 0.88 * float(answers.size()) / float(Data.creation["questions"].size()), 0.0, 1.0)

func _clear() -> void:
	for c in _root.get_children():
		_root.remove_child(c)
		c.queue_free()

# --- The opening card ------------------------------------------------------------

func _intro() -> void:
	_screen = "other"
	_clear()
	_backdrop(COL_W + COL_MARGIN * 2.0)
	_stage("wide", COL_W + COL_MARGIN * 2.0)
	cleared.emit()
	var box := _column(COL_W)
	_text(box, "WILDLINE  ·  THE MAKING OF A LIFE", 14, Style.BRASS, "title_light")
	_text(box, "Before the Field", 52, FG, "title")
	box.add_child(Style.rule(420))
	_text(box, "A platform on the line, at night. Nobody is standing on it yet.", 18, DIM.lerp(FG, 0.2))
	_text(box, "Ten thousand years ago, the will of every living thing became a force in the world. It still wakes in every child, at the edge of growing up, and settles into a Shape.\n\nYours has not woken yet. Before it does, tell us who you were.", 19, FG)
	_text(box, "There are no right answers. Your answers lean your blood, your Shape, your weapon, what will stand beside you, and the Terms you would accept for power. You will see all of it, and why, before anything is final.", 17, DIM.lerp(FG, 0.2))
	_button(box, "Begin", func(): _ask(0), true)
	_button(box, "Surprise me: answer at random", _surprise)
	_button(box, "Back", func(): cancelled.emit())
	_arrive(box)

# --- The questions ----------------------------------------------------------------

func _ask(i: int, all_shown := false) -> void:
	_screen = "other"
	_q = i
	_clear()
	_backdrop(COL_W + COL_MARGIN * 2.0)
	_stage("wide", COL_W + COL_MARGIN * 2.0)
	cleared.emit()
	var qs: Array = Data.creation["questions"]
	var q: Dictionary = qs[i]
	var box := _column(COL_W)
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
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if shown.size() > 6:
		# every answer at once is more than the screen holds: they scroll
		var sc := ScrollContainer.new()
		sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		sc.custom_minimum_size = Vector2(0, 560)
		box.add_child(sc)
		sc.add_child(grid)
	else:
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

## Read the answers into a character (keeping the name, the look and the weapon the player has
## already set), stand it on the platform, and open the panel.
func _reveal() -> void:
	var first := _screen != "reveal"
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
	if not hero.has("look"):
		hero["look"] = { "headgear": true, "cape": false, "cape_color": "shape" }
	# a skin of another home's palette does not follow the character to a new home
	var palette: Array = _palette() + _other_tones()
	if not palette.is_empty() and not palette.has(String(hero["look"].get("skin", ""))):
		hero["look"]["skin"] = Creation.skin_of(hero["city"], spark)
	changed.emit(hero)
	if first and keep_look.is_empty():
		tab = "reading"
		frame = "full"
	# the field settles into the Shape's colour; the figure steps out of it
	_field_col = World.SHAPE_COLORS.get(hero["shape"], _field_col)
	_field_k = 0.0
	field.emit(_field_col, 0.0, 1.0 if first else 0.0)
	_draw_reveal(first)

## The tones beyond the home's own, where the data lets a life wear any of them
## (data/creation.json, look.anySkin): people come to every city from every other.
func _other_tones() -> Array:
	var L: Dictionary = Data.creation.get("look", {})
	if not L.get("anySkin", false):
		return []
	var mine := _palette()
	return (L.get("skinTones", {}).keys() as Array).filter(func(t): return not mine.has(t))

## The home's skin tones (data/bodies.json); every tone if the home names none.
func _palette() -> Array:
	return Data.bodies.get(hero.get("city", ""), {}).get("palette", Data.creation.get("look", {}).get("skinTones", {}).keys())

func _home() -> Dictionary:
	return Data.bodies.get(hero.get("city", ""), {})

## What the creator calls a value of the look (data/creation.json, look.labels).
func _label(kind: String, id: String) -> String:
	return String(Data.creation.get("look", {}).get("labels", {}).get(kind, {}).get(id, id.capitalize()))

## The look changed: the standing figure is dressed again, and the panel drawn again.
func _look_set(key: String, value: Variant) -> void:
	hero["look"][key] = value
	look_changed.emit(hero)
	_draw_reveal()

func _set_tab(id: String) -> void:
	tab = id
	frame = TAB_FRAMES.get(id, "full")
	_scroll_keep = 0
	_draw_reveal()

func _set_frame(id: String) -> void:
	frame = id
	_draw_reveal()

## The reveal, drawn: the figure on the left with the controls of the view, the panel on the right.
func _draw_reveal(first := false) -> void:
	for c in _root.get_children():
		if c is PanelContainer:
			var sc: ScrollContainer = c.find_child("Leaf", true, false)
			if sc and not first:
				_scroll_keep = sc.scroll_vertical
	_clear()
	_stage(frame, PANEL_W)
	_view_controls()
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	panel.offset_left = -PANEL_W
	var ps := Style.plate(Color(0.04, 0.034, 0.03, 0.95), Style.BRASS_DIM, 1, 26, 0)
	ps.border_width_top = 0
	ps.border_width_bottom = 0
	ps.border_width_right = 0
	ps.border_width_left = 2
	ps.border_color = Style.BRASS
	ps.shadow_size = 40
	ps.shadow_color = Color(0, 0, 0, 0.6)
	ps.content_margin_top = 22
	ps.content_margin_bottom = 20
	panel.add_theme_stylebox_override("panel", ps)
	_root.add_child(panel)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 8)
	panel.add_child(col)

	# The head of the panel: whose it is.
	_text(col, "WHO YOUR ANSWERS MADE", 13, Style.BRASS, "title_light")
	var name_row := HBoxContainer.new()
	name_row.add_theme_constant_override("separation", 10)
	col.add_child(name_row)
	var name_edit := LineEdit.new()
	name_edit.text = hero["name"]
	name_edit.placeholder_text = "Name"
	name_edit.max_length = 24
	name_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_edit.add_theme_font_override("font", Style.font("title"))
	name_edit.add_theme_font_size_override("font_size", 38)
	name_edit.add_theme_color_override("font_color", FG)
	name_edit.add_theme_color_override("font_placeholder_color", Style.FAINT)
	for st in [["normal", Style.BRASS_DIM], ["focus", Style.BRASS_HI]]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0)
		sb.border_width_bottom = 1
		sb.border_color = st[1]
		sb.content_margin_bottom = 4
		sb.content_margin_left = 0
		name_edit.add_theme_stylebox_override(st[0], sb)
	name_edit.text_changed.connect(func(t): hero["name"] = t)
	name_row.add_child(name_edit)
	var another := _chip(name_row, "Another name", func():
		hero["name"] = Creation.name_for(hero["city"], _new_spark())
		_draw_reveal())
	another.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var b := Creation.blood(hero["blood"])
	var who := RichTextLabel.new()
	who.bbcode_enabled = true
	who.fit_content = true
	who.scroll_active = false
	Style.rich(who, 17, DIM, "body")
	who.text = "[color=#%s]%s[/color]  ·  [color=#%s]%s[/color]  ·  [color=#%s]%s[/color]" % [
		Style.BLOOD.lightened(0.35).to_html(false), b["name"],
		(World.SHAPE_COLORS.get(hero["shape"], FG) as Color).to_html(false), String(hero["shape"]).capitalize(),
		(World.CITY_COLORS.get(hero["city"], Style.BRASS) as Color).lightened(0.4).to_html(false), String(hero["city"]).capitalize()]
	col.add_child(who)

	# The leaves.
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 0)
	col.add_child(tabs)
	for t in TABS:
		var id: String = t[0]
		_tab_button(tabs, t[1], tab == id, func(): _set_tab(id))
	var scroll := ScrollContainer.new()
	scroll.name = "Leaf"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.add_child(scroll)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 6)
	scroll.add_child(v)
	match tab:
		"body": _leaf_body(v)
		"face": _leaf_face(v)
		"dress": _leaf_dress(v)
		_: _leaf_reading(v)
	var foot_gap := Control.new()
	foot_gap.custom_minimum_size = Vector2(0, 8)
	v.add_child(foot_gap)

	# The foot: always in reach.
	col.add_child(Style.rule(300, Style.BRASS_DIM))
	var done := _button(col, "This is me", func(): finished.emit(hero), true)
	done.alignment = HORIZONTAL_ALIGNMENT_CENTER
	var end := HBoxContainer.new()
	end.add_theme_constant_override("separation", 8)
	col.add_child(end)
	for e in [["Answer again", func(): hero = {}; _ask(0)], ["Another life, same answers", func(): hero = {}; blood_choice = ""; spark = _new_spark(); _screen = "other"; _reveal()]]:
		var eb := _button(end, e[0], e[1])
		eb.autowrap_mode = TextServer.AUTOWRAP_OFF
		eb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		eb.alignment = HORIZONTAL_ALIGNMENT_CENTER
		eb.custom_minimum_size = Vector2(0, 42)
		eb.add_theme_font_size_override("font_size", 16)
		eb.add_theme_color_override("font_color", DIM)
	if first:
		_arrive(v)
		panel.modulate.a = 0.0
		Style.ease_ui(panel.create_tween().tween_property(panel, "modulate:a", 1.0, Style.t("arrive")).set_delay(Style.t("arrive")))
	else:
		var keep := _scroll_keep
		scroll.ready.connect(func(): scroll.set_deferred("scroll_vertical", keep))
	_screen = "reveal"

## The left of the screen is the figure: drag to turn it, the wheel to step closer or back,
## and the same on buttons along the foot.
func _view_controls() -> void:
	var area := Control.new()
	area.set_anchors_preset(Control.PRESET_FULL_RECT)
	area.offset_right = -PANEL_W
	area.mouse_default_cursor_shape = Control.CURSOR_HSIZE
	area.gui_input.connect(func(ev: InputEvent):
		if ev is InputEventMouseMotion and (ev.button_mask & MOUSE_BUTTON_MASK_LEFT) != 0:
			turned.emit(-ev.relative.x * 0.011)
		elif ev is InputEventMouseButton and ev.pressed:
			var at := 0
			for k in FRAMES.size():
				if FRAMES[k][0] == frame:
					at = k
			if ev.button_index == MOUSE_BUTTON_WHEEL_UP and at < FRAMES.size() - 1:
				_set_frame(FRAMES[at + 1][0])
			elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN and at > 0:
				_set_frame(FRAMES[at - 1][0]))
	_root.add_child(area)
	var m := MarginContainer.new()
	m.set_anchors_preset(Control.PRESET_FULL_RECT)
	m.add_theme_constant_override("margin_left", 28)
	m.add_theme_constant_override("margin_bottom", 22)
	m.add_theme_constant_override("margin_right", 28)
	m.mouse_filter = Control.MOUSE_FILTER_PASS
	area.add_child(m)
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_END
	v.add_theme_constant_override("separation", 6)
	v.mouse_filter = Control.MOUSE_FILTER_PASS
	m.add_child(v)
	var hint := _text(v, "Drag to turn.  Scroll to step closer.", 14, DIM)
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hint.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7))
	hint.add_theme_constant_override("outline_size", 4)
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 6)
	bar.mouse_filter = Control.MOUSE_FILTER_PASS
	v.add_child(bar)
	for f in FRAMES:
		var id: String = f[0]
		_chip(bar, f[1], func(): _set_frame(id), frame == id)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(14, 0)
	gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bar.add_child(gap)
	_chip(bar, "‹  Turn", func(): turned.emit(PI / 6.0))
	_chip(bar, "Turn  ›", func(): turned.emit(-PI / 6.0))

# --- The leaves of the reveal --------------------------------------------------------

## The Reading: what the answers made, each with its reason.
func _leaf_reading(v: VBoxContainer) -> void:
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
	var alt := _flow(v, "Or")
	for s in Creation.suggest_bloods(Creation.tally_with(answers, spark)):
		if s["id"] != hero["blood"]:
			var id: String = s["id"]
			_chip(alt, Creation.blood(id)["name"], func(): blood_choice = id; _reveal())
	_chip(alt, "Choose another...", _choose_blood)

	_section(v, "SHAPE", String(hero["shape"]).capitalize(), World.SHAPE_COLORS.get(hero["shape"], FG))
	_line(v, Data.shape(hero["shape"])["field"] + ". " + _shape_line(hero["shape"]))
	_line(v, "Because %s. (The rite at the Academy will read it, and may not agree.)" % ", ".join(hero["why"]["shape"]), DIM)

	var w := Creation.weapon(hero["weapon"])
	_section(v, "HOME AND WEAPON", "%s  ·  %s" % [String(hero["city"]).capitalize(), w["name"]])
	var wtype: Dictionary = Data.room["styles"].get(w["style"], {})
	_line(v, "%s %s The %s Discipline teaches it." % [w["text"], wtype.get("text", ""), String(hero["discipline"]).capitalize()])
	_line(v, "Because %s." % ", ".join(hero["why"]["city"] + hero["why"]["weapon"]), DIM)
	_weapon_chips(v)
	var kit: Dictionary = Data.kits[hero["shape"]]
	_line(v, "Technique: [b]%s[/b]. %s" % [kit["technique"]["name"], kit["technique"]["text"]])
	_line(v, "Stance: [b]%s[/b]: %s." % [kit["stance"]["name"], kit["stance"]["text"]])

	_section(v, "WHAT WILL STAND BESIDE YOU", _seed_text(hero["seed"]))
	_line(v, "Your genius takes its First Form at the rite, read from this, your blood, and your Shape. Until then it is the mote of light that keeps to your shoulder.", DIM)

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

## The city's weapons, in the hand at once. A home without a school of its own (Alexandria)
## carries the weapons of the school it took.
func _weapon_chips(v: VBoxContainer) -> void:
	var wrow := _flow(v, "Or carry")
	var school_city: String = hero["city"]
	if Data.weapons.filter(func(cw): return cw["city"] == hero["city"]).is_empty():
		for d in Data.disciplines:
			if d["id"] == hero["discipline"]:
				school_city = d["city"]
	for cw in Data.weapons:
		if cw["city"] != school_city:
			continue
		var wid: String = cw["id"]
		_chip(wrow, cw["name"], func(): hero["weapon_override"] = wid; hero["weapon"] = wid; changed.emit(hero); _draw_reveal(), hero["weapon"] == wid)

## The body: the home's cast of face, then sex, build, stature and skin.
func _leaf_body(v: VBoxContainer) -> void:
	var look: Dictionary = hero["look"]
	var L: Dictionary = Data.creation.get("look", {})
	var home := _home()
	_section(v, "THE FACE OF %s" % String(hero["city"]).to_upper(), "")
	if home.has("brief"):
		_line(v, String(home["brief"]))
	_line(v, "Your home gives the cast of the face. The body is yours.", DIM)

	_section(v, "BODY", "")
	var sexes := _flow(v, "")
	for sx in L.get("sexes", {}):
		var sid: String = sx
		_chip(sexes, _label("sexes", sid), func():
			look["sex"] = sid
			hero["body"] = "%s-%s" % [hero["city"], sid]
			hero.erase("body_override")
			changed.emit(hero)
			_draw_reveal(), String(look.get("sex", "m")) == sid)

	# The build: a row of builds by name, each a setting of the three measures under it, which
	# stay the player's to move (data/creation.json, look.frame.presets).
	var presets: Array = L.get("frame", {}).get("presets", [])
	_section(v, "BUILD", "")
	var prow := _flow(v, "")
	var chips := {}
	var relight := func():
		var now := build_preset(look)
		for pid in chips:
			_chip_style(chips[pid], pid == now)
	for pr in presets:
		var pid := String(pr["id"])
		var set_to: Dictionary = pr
		chips[pid] = _chip(prow, _label("buildPresets", pid), func():
			for k in ["build", "weight", "frame"]:
				look[k] = float(set_to.get(k, 0.0))
			look_changed.emit(hero)
			_draw_reveal(), build_preset(look) == pid)
	for m in [["Muscle", "builds", "build"], ["Weight", "weights", "weight"], ["Frame", "frames", "frame"]]:
		var key: String = m[2]
		_slider(v, m[0], m[1], L.get(m[1], { "even": 0.0 }), 0.05, float(look.get(key, 0.0)), func(x: float):
			look[key] = x
			relight.call()
			look_changed.emit(hero))
	_line(v, "Your home's dress is cut to whatever body you make.", DIM)

	_section(v, "STATURE AND YEARS", "")
	var sts: Dictionary = L.get("statures", { "middling": 1.0 })
	_slider(v, "Stature", "statures", sts, 0.01, float(look.get("stature", 1.0)), func(x: float):
		look["stature"] = x
		look_changed.emit(hero))
	_slider(v, "Years", "ages", L.get("ages", { "young": 0.0 }), 0.05, float(look.get("age", 0.0)), func(x: float):
		look["age"] = x
		look_changed.emit(hero))

	var skin := String(look.get("skin", "olive"))
	_section(v, "SKIN", _label("skinTones", skin))
	var srow := _flow(v, "")
	for tn in _palette():
		var tid: String = tn
		var c: Array = L.get("skinTones", {}).get(tid, [0.6, 0.45, 0.33])
		_swatch(srow, Color(c[0], c[1], c[2]), skin == tid, _label("skinTones", tid), func(): _look_set("skin", tid))
	var others := _other_tones()
	if not others.is_empty():
		var orow := _flow(v, "From elsewhere")
		for tn in others:
			var tid: String = tn
			var c: Array = L.get("skinTones", {}).get(tid, [0.6, 0.45, 0.33])
			_swatch(orow, Color(c[0], c[1], c[2]), skin == tid, _label("skinTones", tid), func(): _look_set("skin", tid))
		_line(v, "The first are the tones %s's people most often have. People come to every city from every other." % String(home.get("name", hero["city"])), DIM)
	var b := Creation.blood(hero["blood"])
	if String(b.get("shows", "")) != "":
		_line(v, "Your blood shows as %s." % b["shows"], DIM)

## The face and hair: the style, its colour, the beard.
func _leaf_face(v: VBoxContainer) -> void:
	var look: Dictionary = hero["look"]
	var L: Dictionary = Data.creation.get("look", {})
	var roll := _flow(v, "")
	_chip(roll, "Surprise me", func():
		var rng := RandomNumberGenerator.new()
		rng.randomize()
		var keep := { "sex": look.get("sex", "m"), "skin": look.get("skin", ""), "build": look.get("build", 0.0), "stature": look.get("stature", 1.0),
			"weight": look.get("weight", 0.0), "frame": look.get("frame", 0.0), "age": look.get("age", 0.0), "wear": look.get("wear", {}), "dress": look.get("dress", ""),
			"headgear": false, "cape": look.get("cape", true), "cape_color": look.get("cape_color", "shape") }
		var fresh := Creation.look_of(String(hero["city"]), rng.randi() % 100000)
		fresh.merge(keep, true)
		if String(fresh["sex"]) == "m" and rng.randf() < float(L.get("start", {}).get("beardChance", 0.35)):
			var bs: Array = L.get("beards", ["none"])
			fresh["beard"] = bs[rng.randi() % bs.size()]
		hero["look"] = fresh
		look_changed.emit(hero)
		_draw_reveal())
	_line(v, "A whole face at once, from what the people of %s most often have. Everything under it is yours to change." % String(_home().get("name", hero["city"])), DIM)

	var shape := String(look.get("face", "own"))
	_section(v, "FACE", _label("faces", shape))
	var frow := _flow(v, "")
	for fs in L.get("faces", ["own"]):
		var fid: String = fs
		_chip(frow, _label("faces", fid), func(): _look_set("face", fid), shape == fid)
	if shape != "own":
		_slider(v, "How strongly", "faceStrength", L.get("faceStrength", { "plain": 0.8 }), 0.05, float(look.get("face_strength", 0.8)), func(x: float):
			look["face_strength"] = x
			look_changed.emit(hero))
	if not (look.get("face_set", {}) is Dictionary):
		look["face_set"] = {}
	var sliders: Dictionary = L.get("faceSliders", {})
	for sk in sliders:
		var sid: String = sk
		_slider(v, _label("faceSliders", sid), "lipsShape" if sid == "lips" else sid, sliders[sid], 0.05, float(look.get("face_set", {}).get(sid, 0.0)), func(x: float):
			var fs2: Dictionary = (look.get("face_set", {}) as Dictionary).duplicate()   # a look once shared is not changed under another
			fs2[sid] = x
			look["face_set"] = fs2
			look_changed.emit(hero))

	var eye_now := String(look.get("eye_color", "dark"))
	_section(v, "EYES", _label("eyeColors", eye_now))
	var erow := _flow(v, "")
	for ec in L.get("eyeColors", {}):
		var eid: String = ec
		var e: Array = L["eyeColors"][eid]
		_swatch(erow, Color(e[0], e[1], e[2]).lightened(0.12), eye_now == eid, _label("eyeColors", eid), func(): _look_set("eye_color", eid))
	var brows_now := String(look.get("brows", "soft"))
	var browrow := _flow(v, "Brows")
	for bw in L.get("brows", ["soft"]):
		var bwid: String = bw
		_chip(browrow, _label("brows", bwid), func(): _look_set("brows", bwid), brows_now == bwid)

	var lips_now := String(look.get("lips", "bare"))
	_section(v, "LIPS", _label("lips", lips_now))
	var lrow := _flow(v, "")
	var tn: Array = L.get("skinTones", {}).get(String(look.get("skin", "")), [0.62, 0.46, 0.33])
	var tone_now := Color(tn[0], tn[1], tn[2])
	for lp in L.get("lips", ["bare"]):
		var lid: String = lp
		_swatch(lrow, World.lips_color(tone_now, lid), lips_now == lid, _label("lips", lid), func(): _look_set("lips", lid))

	var marks_now: Array = (look.get("marks", []) as Array).duplicate() if look.get("marks", []) is Array else []
	var offered: Array = (L.get("marks", []) as Array) + (_home().get("marks", []) as Array)
	if not offered.is_empty():
		var names: Array = marks_now.map(func(m): return _label("marks", String(m)))
		_section(v, "MARKS", ", ".join(names) if not names.is_empty() else "None")
		var mrow := _flow(v, "")
		for mk in offered:
			var mid: String = mk
			_chip(mrow, _label("marks", mid), func():
				var next: Array = marks_now.duplicate()
				if next.has(mid):
					next.erase(mid)
				else:
					next.append(mid)
				_look_set("marks", next), marks_now.has(mid))
		if not (_home().get("marks", []) as Array).is_empty():
			_line(v, "The last of these are worn in %s." % String(_home().get("name", hero["city"])), DIM)

	var hair := String(look.get("hair", "crop"))
	_section(v, "HAIR", _label("hair", hair))
	# the home's own styles first, then every other: all of them are anyone's
	var own_hair: Array = (_home().get("hair", []) as Array).filter(func(h): return (L.get("hair", []) as Array).has(h))
	var hrow := _flow(v, "Worn in %s" % String(_home().get("name", hero["city"])) if not own_hair.is_empty() else "")
	for hs in own_hair:
		var hid: String = hs
		_chip(hrow, _label("hair", hid), func(): _look_set("hair", hid), hair == hid)
	var rest: Array = (L.get("hair", []) as Array).filter(func(h): return not own_hair.has(h))
	if not rest.is_empty():
		var hrow2 := _flow(v, "And" if not own_hair.is_empty() else "")
		for hs in rest:
			var hid: String = hs
			_chip(hrow2, _label("hair", hid), func(): _look_set("hair", hid), hair == hid)
	var hc_now := String(look.get("hair_color", "brown"))
	var hcrow := _flow(v, "")
	for hc in L.get("hairColors", {}):
		var cid: String = hc
		var c: Array = L["hairColors"][cid]
		_swatch(hcrow, Color(c[0], c[1], c[2]), hc_now == cid, _label("hairColors", cid), func(): _look_set("hair_color", cid))
	_line(v, "%s. The brows take the same colour." % _label("hairColors", hc_now), DIM)
	if _headgear_name() != "" and look.get("headgear", true) and _headgear_covers():
		var cover := _flow(v, "")
		_chip(cover, "Take off the %s" % _headgear_name().to_lower(), func(): _look_set("headgear", false))
		_line(v, "It covers the hair." if String(_headgear().get("type", "")) == "cover" else "It covers the crown; only the fall of the hair shows under it.", DIM)

	var beard := String(look.get("beard", "none"))
	_section(v, "BEARD", _label("beards", beard))
	var brow := _flow(v, "")
	for bs in L.get("beards", []):
		var bid: String = bs
		_chip(brow, _label("beards", bid), func(): _look_set("beard", bid), beard == bid)

	var feats: Array = []
	var b := Creation.blood(hero["blood"])
	if String(b.get("shows", "")) != "":
		feats.append("Your blood shows as %s." % b["shows"])
	feats.append("What your blood puts in the eyes is not yours to choose: where it shows there, it shows over their colour.")
	_section(v, "WHAT YOU DID NOT CHOOSE", "")
	_line(v, " ".join(feats), DIM)

## The dress: the home's own, what is worn on the head and the back, and what is in the hand.
func _leaf_dress(v: VBoxContainer) -> void:
	var look: Dictionary = hero["look"]
	var L: Dictionary = Data.creation.get("look", {})
	var home := _home()
	_section(v, "THE DRESS OF %s" % String(hero["city"]).to_upper(), "")
	_line(v, String(home.get("dress", {}).get("culture", "What your home wears.")))
	# the ways the home's dress is worn: its working colours, a second dye, the formal dress
	var opts: Array = home.get("dress", {}).get("options", [])
	if opts.size() > 1:
		var now: Dictionary = World.dress_option(String(hero.get("city", "")), look)
		_section(v, "WORN AS", String(now.get("name", "")))
		var orow := _flow(v, "")
		for o in opts:
			var oid := String(o["id"])
			_chip(orow, String(o.get("name", oid)), func(): _look_set("dress", oid), String(now.get("id", "")) == oid)
		_line(v, String(now.get("text", "")))
	# Piece by piece: each slot of the dress in either of the home's cuts, on any body
	# (Creation.wear_options; data/creation.json, look.slots).
	var sex := String(hero.get("body", "")).get_slice("-", 1)
	var way := String(World.dress_option(String(hero.get("city", "")), look).get("wear", "plain"))
	var rows := 0
	for slot in L.get("slots", {}).get("order", []):
		var sid: String = slot
		var choices: Array = Creation.wear_options(String(hero.get("city", "")), sid, sex, way)
		if choices.is_empty():
			continue
		if rows == 0:
			_section(v, "PIECE BY PIECE", "")
			_line(v, "Every piece of your home's dress goes on any body. Take each as you like.", DIM)
		rows += 1
		var now := wear_now(sid)
		var srow := _flow(v, _label("slots", sid))
		for o in choices:
			var oid := String(o["id"])
			_chip(srow, String(o["name"]), func(): _wear_set(sid, oid), now == oid)
	var wear := _flow(v, "Wearing")
	if rows == 0 and _headgear_name() != "":
		_chip(wear, _headgear_name(), func(): _look_set("headgear", not look.get("headgear", true)), look.get("headgear", true))
	_chip(wear, "Cloak", func(): _look_set("cape", not look.get("cape", true)), look.get("cape", true))

	if look.get("cape", true):
		var cc_now := String(look.get("cape_color", "shape"))
		_section(v, "THE CLOAK'S COLOUR", _label("capeColors", cc_now))
		var crow := _flow(v, "")
		for cc in L.get("capeColors", {}):
			var cid: String = cc
			_swatch(crow, _cape_color(cid), cc_now == cid, _label("capeColors", cid), func(): _look_set("cape_color", cid))

	var w := Creation.weapon(hero["weapon"])
	_section(v, "IN YOUR HAND", w["name"])
	_line(v, String(w["text"]))
	_weapon_chips(v)

## The choice a slot of the dress is worn in now: a cut (m, f) or none. The head is bare when
## the look's headgear is off.
func wear_now(slot: String) -> String:
	var look: Dictionary = hero.get("look", {})
	if slot == "head" and not look.get("headgear", true):
		return "none"
	if slot == "head" and Creation.cover_of(look) != "":
		return Creation.cover_of(look)
	var way := String(World.dress_option(String(hero.get("city", "")), look).get("wear", "plain"))
	return Creation.wear_choice(String(hero.get("city", "")), slot, look, String(hero.get("body", "")).get_slice("-", 1), way)

## Take a slot of the dress in another cut, or leave it off.
func _wear_set(slot: String, id: String) -> void:
	var look: Dictionary = hero["look"]
	var w: Dictionary = (look["wear"] as Dictionary).duplicate() if look.get("wear") is Dictionary else {}      # a look once shared is not changed under another
	if slot == "head":
		look["headgear"] = id != "none"
		if id != "none":
			w[slot] = id
	else:
		w[slot] = id
	_look_set("wear", Creation.wear_settle(String(hero.get("city", "")), w, String(hero.get("body", "")).get_slice("-", 1)))

## What the home wears on the head, by name; "" where it wears nothing.
func _headgear_name() -> String:
	var hg := _headgear()
	if hg.is_empty():
		return ""
	return String(hg.get("name", _label("headgear", String(hg.get("type", "hat")))))

## The headgear this character's home gives this body, as it is dressed now ({} for none).
func _headgear() -> Dictionary:
	var hgs: Variant = _home().get("dress", {}).get("headgear", null)
	if hgs is Dictionary:
		hgs = [hgs]
	if not (hgs is Array):
		return {}
	var worn_cover := Creation.cover_of(hero.get("look", {}))
	for cv in Data.creation.get("look", {}).get("coverings", []):
		if String(cv["id"]) == worn_cover:
			return { "type": "cover", "name": String(cv.get("name", worn_cover)) }
	var body := String(hero.get("body", ""))
	var wear := String(World.dress_option(String(hero.get("city", "")), hero.get("look", {})).get("wear", "plain"))
	var cut := Creation.wear_of(hero.get("look", {}), "head", body.get_slice("-", 1))      # the cut of the head the look wears
	for h in hgs:
		if String(h.get("sex", cut)) == cut and (not h.has("in") or (h["in"] as Array).has(wear)):
			return h
	return {}

## Does the home's headgear cover the crown (a headband does not)?
func _headgear_covers() -> bool:
	var hg := _headgear()
	return not hg.is_empty() and not (Data.creation.get("look", {}).get("openHeadgear", []) as Array).has(String(hg.get("type", "")))

## The cloak's colours as the world dyes them (World.cape_color_for): cloth, on the ramps.
func _cape_color(which: String) -> Color:
	var plain := Color(0.5, 0.42, 0.36)
	var col := plain
	match which:
		"shape": col = (World.SHAPE_COLORS.get(hero["shape"], plain) as Color).darkened(0.25)
		"city": col = World.CITY_COLORS.get(hero["city"], plain)
		"blood":
			var b: Dictionary = Creation.blood(hero["blood"])
			var lean: Dictionary = b.get("shapeLean", {})
			col = Color(0.25, 0.12, 0.14).lerp(World.SHAPE_COLORS.get(String(lean.keys()[0]) if not lean.is_empty() else "anchor", Color.WHITE), 0.5)
	return Style.conform(col, "cloth")

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
	_stage(frame, 0.0)
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
	for tier in [["bloodline", "BLOODLINES  ·  strong blood, registered by the cities", Style.BLOOD.lightened(0.35)], ["kindred", "KINDREDS  ·  peoples who carry it together", Style.GOLD], ["mark", "MARKS  ·  one mutation, yours alone", FG]]:
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
			btn.custom_minimum_size = Vector2(0, 142)
			btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			btn.clip_contents = true
			_style(btn, id == hero["blood"], 14, "ui")
			btn.pressed.connect(func(): _click(); blood_choice = id; _reveal())
			grid.add_child(btn)
			# the card: the blood's name, how it shows, what it gives, and its Gap
			var box := VBoxContainer.new()
			box.set_anchors_preset(Control.PRESET_FULL_RECT)
			box.offset_left = 16
			box.offset_right = -14
			box.offset_top = 10
			box.offset_bottom = -8
			box.add_theme_constant_override("separation", 1)
			box.mouse_filter = Control.MOUSE_FILTER_IGNORE
			btn.add_child(box)
			var lines: Array = [_text(box, String(b["name"]), 19, tier[2], "title")]
			if String(b.get("shows", "")) != "":
				lines.append(_text(box, "Shows as %s." % b["shows"], 14, DIM, "italic"))
			lines.append(_text(box, String(b["gift"]) + ".", 15, FG, "ui"))
			lines.append(_text(box, "The Gap: %s." % b["gap"], 14, Style.EMBER.lightened(0.25), "italic"))
			for l in lines:
				(l as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	_button(v, "Back", _reveal)
	_arrive(v)

# --- Helpers ---------------------------------------------------------------------

## The column of words on the right of the stage, centred on its height.
func _column(width: float) -> VBoxContainer:
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	c.offset_left = -(width + COL_MARGIN)
	c.offset_right = -COL_MARGIN
	_root.add_child(c)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(width, 0)
	v.add_theme_constant_override("separation", 10)
	c.add_child(v)
	return v

## Tell the stage how to frame itself: the camera's framing, and how much of the screen's
## width the words cover on the right (the figure centres in what is left).
func _stage(kind: String, covered: float) -> void:
	var w := 1600.0
	if is_inside_tree():
		w = maxf(1.0, get_viewport().get_visible_rect().size.x)
	framed.emit(kind)
	shifted.emit(clampf(covered / w, 0.0, 0.8))

func _text(parent: Control, t: String, size: int, color: Color, kind := "") -> Label:
	var l := Label.new()
	l.text = t
	# Labels in a row size to their text; elsewhere they wrap.
	if not (parent is HBoxContainer or parent is FlowContainer):
		l.autowrap_mode = TextServer.AUTOWRAP_WORD
	if kind == "":
		kind = "title" if size >= 28 else ("italic" if color == DIM and size <= 16 else ("body" if size >= 17 else "ui"))
	Style.label(l, size, color, kind)
	parent.add_child(l)
	return l

## A section of the reveal: a small brass heading over its value.
func _section(parent: Control, title: String, value: String, color := FG) -> void:
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
		Style.label(l, 23, color, "body_bold")
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
		(func(): if is_instance_valid(b) and b.is_inside_tree(): b.grab_focus()).call_deferred()
	return b

func _chip(parent: Control, t: String, cb: Callable, on := false) -> Button:
	var b := Button.new()
	b.text = t
	_chip_style(b, on)
	b.pressed.connect(func(): _click(); cb.call())
	parent.add_child(b)
	return b

## A chip as it is drawn: lit when it is the one chosen.
func _chip_style(b: Button, on: bool) -> void:
	_style(b, on, 15, "ui")
	for st in ["normal", "hover", "focus", "pressed", "hover_pressed"]:
		var sb := b.get_theme_stylebox(st) as StyleBoxFlat
		sb.content_margin_left = 12
		sb.content_margin_right = 12
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6

## The named build a look's three measures are set to (data/creation.json, look.frame.presets);
## "" when they are the player's own.
static func build_preset(look: Dictionary) -> String:
	for pr in Data.creation.get("look", {}).get("frame", {}).get("presets", []):
		var same := true
		for k in ["build", "weight", "frame"]:
			if absf(float(look.get(k, 0.0)) - float(pr.get(k, 0.0))) > 0.026:
				same = false
		if same:
			return String(pr["id"])
	return ""

## A row that wraps: chips or swatches, with a small label before them.
func _flow(parent: Control, label: String) -> HFlowContainer:
	var f := HFlowContainer.new()
	f.add_theme_constant_override("h_separation", 8)
	f.add_theme_constant_override("v_separation", 8)
	parent.add_child(f)
	if label != "":
		var l := _text(f, label + ":", 15, DIM)
		l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return f

## A leaf's tab: its name over a brass line when it is the open one.
func _tab_button(parent: Control, t: String, on: bool, cb: Callable) -> void:
	var b := Button.new()
	b.text = t
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.custom_minimum_size = Vector2(0, 40)
	b.focus_mode = Control.FOCUS_ALL
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.add_theme_font_override("font", Style.font("title"))
	b.add_theme_font_size_override("font_size", 14)
	b.add_theme_color_override("font_color", Style.BRASS_HI if on else DIM)
	b.add_theme_color_override("font_hover_color", Style.BRASS_HI)
	b.add_theme_color_override("font_focus_color", Style.BRASS_HI)
	b.add_theme_color_override("font_pressed_color", Style.BRASS_HI)
	for st in ["normal", "hover", "focus", "pressed", "hover_pressed"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.27, 0.18, 0.07, 0.35) if (on or st != "normal") else Color(0, 0, 0, 0)
		sb.border_width_bottom = 2 if on else 1
		sb.border_color = Style.BRASS_HI if on else Style.BRASS_DIM
		sb.content_margin_top = 8
		sb.content_margin_bottom = 8
		b.add_theme_stylebox_override(st, sb)
	b.pressed.connect(func(): _click(); cb.call())
	parent.add_child(b)

## A colour to choose: a disc of it, ringed in brass when it is the one worn.
func _swatch(parent: Control, col: Color, on: bool, tip: String, cb: Callable) -> void:
	var b := Button.new()
	b.custom_minimum_size = Vector2(46, 46)
	b.tooltip_text = tip
	b.focus_mode = Control.FOCUS_ALL
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	for st in ["normal", "hover", "focus", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(st, StyleBoxEmpty.new())
	var shown := col
	b.draw.connect(func():
		var c := b.size / 2.0
		b.draw_circle(c, 15.0, shown)
		b.draw_arc(c, 15.0, 0.0, TAU, 40, Color(0, 0, 0, 0.55), 1.5, true)
		if on:
			b.draw_arc(c, 20.0, 0.0, TAU, 48, Style.BRASS_HI, 2.0, true)
		elif b.is_hovered() or b.has_focus():
			b.draw_arc(c, 20.0, 0.0, TAU, 48, Style.BRASS, 1.0, true))
	for sig in [b.mouse_entered, b.mouse_exited, b.focus_entered, b.focus_exited]:
		sig.connect(b.queue_redraw)
	b.pressed.connect(func(): _click(); cb.call())
	parent.add_child(b)

## A measure set on a slider between the least and the greatest of its named values
## (data/creation.json); the name it falls nearest shows beside it.
func _slider(parent: Control, title: String, kind: String, named: Dictionary, step: float, value: float, on_change: Callable) -> void:
	var lo := INF
	var hi := -INF
	for k in named:
		lo = minf(lo, float(named[k]))
		hi = maxf(hi, float(named[k]))
	var nearest := func(x: float) -> String:
		var best := ""
		for k in named:
			if best == "" or absf(float(named[k]) - x) < absf(float(named[best]) - x):
				best = k
		return _label(kind, best)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	parent.add_child(row)
	var t := _text(row, title, 15, DIM)
	t.custom_minimum_size.x = 70
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = clampf(value, lo, hi)
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	s.custom_minimum_size = Vector2(240, 30)
	s.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	s.add_theme_icon_override("grabber", _grabber(false))
	s.add_theme_icon_override("grabber_highlight", _grabber(true))
	var line := StyleBoxFlat.new()
	line.bg_color = Style.BRASS_DIM.darkened(0.35)
	line.content_margin_top = 2
	line.content_margin_bottom = 2
	s.add_theme_stylebox_override("slider", line)
	for st in ["grabber_area", "grabber_area_highlight"]:
		var fill := StyleBoxFlat.new()
		fill.bg_color = Style.BRASS
		fill.content_margin_top = 2
		fill.content_margin_bottom = 2
		s.add_theme_stylebox_override(st, fill)
	row.add_child(s)
	var val := _text(row, nearest.call(s.value), 16, FG, "body")
	val.custom_minimum_size.x = 92
	s.value_changed.connect(func(x: float):
		val.text = nearest.call(x)
		on_change.call(x))

## The slider's handle: a brass lozenge.
static var _grab: Array = [null, null]
static func _grabber(lit: bool) -> ImageTexture:
	var at := 1 if lit else 0
	if _grab[at] != null:
		return _grab[at]
	var n := 24
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var d := absf(x - n / 2.0 + 0.5) + absf(y - n / 2.0 + 0.5)
			var a := clampf(n / 2.0 - 1.0 - d, 0.0, 1.0)
			var c := (Style.BRASS_HI if lit else Style.GOLD) if d < n / 2.0 - 4.5 else Style.INK
			img.set_pixel(x, y, Color(c, a))
	_grab[at] = ImageTexture.create_from_image(img)
	return _grab[at]

## The backdrop of the creator's screens: lamplight in the dark, with motes of field drifting.
func _backdrop(covered := -1.0) -> void:
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = BACKDROP
	var sm := ShaderMaterial.new()
	sm.shader = sh
	bg.material = sm
	_root.add_child(bg)
	if covered >= 0.0:
		var w := 1600.0
		if is_inside_tree():
			w = maxf(1.0, get_viewport().get_visible_rect().size.x)
		sm.set_shader_parameter("open", clampf(1.0 - covered / w, 0.05, 1.0))
	# The field: from where it was, to where the answers have taken it.
	sm.set_shader_parameter("field_col", Vector3(_field_col.r, _field_col.g, _field_col.b))
	sm.set_shader_parameter("field_k", _field_k)
	var before := _field_col
	var k0 := _field_k
	_field_now()
	if covered >= 0.0:
		field.emit(_field_col, _field_k, 0.0)
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
			Style.ease_ui(it.create_tween().tween_property(it, "modulate:a", 1.0, Style.t("arrive")).set_delay(Style.t("stagger") * i))
			i += 1

const BACKDROP := """
shader_type canvas_item;
uniform vec3 field_col = vec3(0.6, 0.9, 0.7);
uniform float field_k = 0.0;
uniform float open = 0.0;   // the part of the width, from the left, where the stage shows through; 0: none
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
	float cover = 0.98;
	if (open > 0.0) {
		// the stage shows on the left; the dark gathers under the words, and at the screen's edges
		cover = 0.95 * smoothstep(open - 0.2, open + 0.02, uv.x);
		vec2 e = (uv - vec2(open * 0.5, 0.5)) * vec2(1.0 / open, 1.0);
		cover = max(cover, 0.6 * smoothstep(0.42, 0.78, length(e * vec2(0.9, 1.25))) * (1.0 - smoothstep(open - 0.1, open, uv.x)));
		cover = max(cover, m * 0.5);
	}
	COLOR = vec4(col, cover);
}
"""
