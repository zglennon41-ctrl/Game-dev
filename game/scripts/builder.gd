## The Pattern builder: a Form and up to three Terms, one of each kind. The Pattern reads as a
## sentence, shows its multiplier, chain and payout as it is built, and is set or sworn.
## Terms the combat room cannot judge yet are shown, greyed, with the reason.
class_name Builder
extends CanvasLayer

signal done(spec: Dictionary)
signal cancelled

const BG := Color(0.035, 0.03, 0.028, 0.97)
const FG := Color(0.94, 0.9, 0.83)
const DIM := Color(0.6, 0.56, 0.5)
const OFF := Color(0.4, 0.37, 0.33)
const GOLD := Color(1.0, 0.8, 0.35)
const RED := Color(0.9, 0.35, 0.3)
const EDGE := Color(0.32, 0.27, 0.21)

var spec := {}
var _form_buttons := {}
var _term_buttons := {}
var _sentence := RichTextLabel.new()
var _numbers := Label.new()
var _name := LineEdit.new()
var _sworn := CheckButton.new()
var _swear_note := Label.new()
var _lost_box := VBoxContainer.new()

func _ready() -> void:
	layer = 20
	var bg := ColorRect.new()
	bg.color = BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 28)
	bg.add_child(margin)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 10)
	margin.add_child(root)

	var title := Label.new()
	_label(title, 36, GOLD)
	title.text = "BUILD YOUR PATTERN"
	root.add_child(title)
	var sub := Label.new()
	_label(sub, 15, DIM)
	sub.text = "A Pattern is a technique that is yours, and a Term is the condition that makes it strong. One Form from the Anchor's own Shape; up to three Terms, one of each kind. Each Term multiplies it; swearing doubles it; x9 is the ceiling."
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD
	root.add_child(sub)

	var cols := HBoxContainer.new()
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	cols.add_theme_constant_override("separation", 14)
	root.add_child(cols)
	cols.add_child(_forms_column())
	for kind in [["trigger", "TRIGGER", "when it may be used  ·  x1.5"], ["toll", "TOLL", "what it costs  ·  x2"], ["bar", "BAR", "what it may never do  ·  x1.5"]]:
		cols.add_child(_terms_column(kind[0], kind[1], kind[2]))

	# The sentence and the numbers.
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _box(Color(0.07, 0.06, 0.05, 1.0)))
	root.add_child(panel)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 6)
	panel.add_child(pv)
	_sentence.bbcode_enabled = true
	_sentence.fit_content = true
	_sentence.scroll_active = false
	_sentence.add_theme_font_size_override("normal_font_size", 20)
	_sentence.add_theme_font_size_override("bold_font_size", 20)
	_sentence.add_theme_font_size_override("italics_font_size", 20)
	_sentence.add_theme_color_override("default_color", FG)
	pv.add_child(_sentence)
	_label(_numbers, 16, GOLD)
	pv.add_child(_numbers)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	pv.add_child(row)
	var nl := Label.new()
	_label(nl, 16, DIM)
	nl.text = "Name (public; the Terms are not):"
	row.add_child(nl)
	_name.custom_minimum_size = Vector2(320, 0)
	_name.max_length = 28
	_name.text_changed.connect(func(t): spec["name"] = t; _refresh())
	row.add_child(_name)
	_sworn.text = "Swear it"
	_sworn.add_theme_font_size_override("font_size", 17)
	_sworn.toggled.connect(func(on): spec["sworn"] = on; _refresh())
	row.add_child(_sworn)
	_label(_swear_note, 13, DIM)
	_swear_note.autowrap_mode = TextServer.AUTOWRAP_WORD
	_swear_note.text = "Sworn: x2 on the whole. Break a sworn Term and the Pattern is gone for good; break an unsworn one and it is gone for a season. (In the full game you swear at the hall's hearth on a Sunday, before three witnesses; here the builder stands in for the hearth.)"
	pv.add_child(_swear_note)
	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", 12)
	pv.add_child(buttons)
	buttons.add_child(_button("Keep this Pattern", func(): done.emit(spec.duplicate(true))))
	buttons.add_child(_button("Back", func(): cancelled.emit()))
	pv.add_child(_lost_box)

func open(current: Dictionary, lost_text: String, on_restore: Callable) -> void:
	spec = current.duplicate(true)
	_name.text = spec["name"]
	_sworn.button_pressed = spec.get("sworn", false)
	for c in _lost_box.get_children():
		c.queue_free()
	if lost_text != "":
		var l := Label.new()
		_label(l, 15, RED)
		l.text = lost_text
		_lost_box.add_child(l)
		_lost_box.add_child(_button("Testing only: restore it", func(): on_restore.call(); open(spec, "", on_restore)))
	visible = true
	_refresh()

# --- Columns ----------------------------------------------------------------

func _forms_column() -> Control:
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(320, 0)
	v.add_theme_constant_override("separation", 8)
	var h := Label.new()
	_label(h, 18, FG)
	h.text = "FORM  ·  what it does"
	v.add_child(h)
	for id in Data.room["pattern"]["forms"]:
		var f: Dictionary = Data.room["pattern"]["forms"][id]
		var b := Button.new()
		b.toggle_mode = true
		b.text = "%s\n%s family\n%s" % [f["name"], f["family"], f["text"]]
		b.autowrap_mode = TextServer.AUTOWRAP_WORD
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(320, 120)
		b.add_theme_font_size_override("font_size", 14)
		_style_toggle(b)
		b.pressed.connect(func(): spec["form"] = id; _refresh())
		v.add_child(b)
		_form_buttons[id] = b
	return v

func _terms_column(kind: String, title: String, sub: String) -> Control:
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var h := Label.new()
	_label(h, 18, FG)
	h.text = title
	v.add_child(h)
	var s := Label.new()
	_label(s, 13, DIM)
	s.text = sub
	v.add_child(s)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(scroll)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 4)
	scroll.add_child(list)
	var none := Button.new()
	none.toggle_mode = true
	none.text = "(none)"
	none.alignment = HORIZONTAL_ALIGNMENT_LEFT
	_style_toggle(none)
	none.pressed.connect(func(): _set_term(kind, ""))
	list.add_child(none)
	_term_buttons[kind + ":"] = none
	var ids: Array = Data.terms.filter(func(t): return t["kind"] == kind).map(func(t): return t["id"])
	# Available Terms first.
	ids.sort_custom(func(a, b): return int(PatternTerms.available(a)) > int(PatternTerms.available(b)))
	for id in ids:
		var t: Dictionary = PatternTerms.term(id)
		var b := Button.new()
		b.toggle_mode = true
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.autowrap_mode = TextServer.AUTOWRAP_WORD
		b.add_theme_font_size_override("font_size", 14)
		if id in ["never-beast", "never-green"]:
			b.text = "%s\n   (in this room it always forbids: every use breaks it)" % t["text"]
		elif PatternTerms.available(id):
			b.text = t["text"]
		else:
			b.text = "%s\n   (not yet: %s)" % [t["text"], PatternTerms.reason(id)]
			b.disabled = true
		_style_toggle(b)
		b.pressed.connect(func(): _set_term(kind, id))
		list.add_child(b)
		_term_buttons[kind + ":" + id] = b
	return v

func _set_term(kind: String, id: String) -> void:
	var terms: Array = spec["terms"].filter(func(x): return PatternTerms.term(x)["kind"] != kind)
	if id != "":
		terms.append(id)
	# Keep the sentence in order: Trigger, Toll, Bar.
	var order := { "trigger": 0, "toll": 1, "bar": 2 }
	terms.sort_custom(func(a, b): return order[PatternTerms.term(a)["kind"]] < order[PatternTerms.term(b)["kind"]])
	spec["terms"] = terms
	_refresh()

# --- The sentence and numbers -------------------------------------------------

## A Form by its id, from the Shape's kit ("cast.reach" is in the Cast kit).
static func form_of(form_id: String) -> Dictionary:
	var shape := form_id.split(".")[0]
	if Data.kits.has(shape) and Data.kits[shape]["forms"].has(form_id):
		return Data.kits[shape]["forms"][form_id]
	return Data.room["pattern"]["forms"][form_id]

static func sentence(sp: Dictionary) -> String:
	var form: Dictionary = form_of(sp["form"])
	var parts: Array = ["[b]%s[/b]: %s." % [sp["name"] if sp["name"] != "" else "(unnamed)", form["name"]]]
	for id in sp["terms"]:
		var t: Dictionary = PatternTerms.term(id)
		match t["kind"]:
			"trigger": parts.append("[i]%s.[/i]" % t["text"])
			"toll": parts.append("At the cost of [i]%s[/i]." % String(t["text"]).to_lower())
			"bar": parts.append("[i]%s.[/i]" % t["text"])
	if sp.get("sworn", false):
		parts.append("Sworn.")
	return " ".join(parts)

static func payout(sp: Dictionary) -> String:
	var form: Dictionary = form_of(sp["form"])
	var n := Fight.chain_length(sp)
	var m := Fight.multiplier_of(sp)
	var stage := float(Data.rules["field"]["stageOutput"][3])
	var pay := float(form["base"]) * stage * m
	match form["effect"]:
		"strikes": return "%d cues of %d damage, then %d" % [n, int(form["base"]), roundi(pay)]
		"guard": return "untouchable for %d cues, then a %d-damage shockwave that staggers" % [n, roundi(pay)]
		"mend": return "%d cues healing %d, then %d health" % [n, int(form["base"]), roundi(pay * float(form.get("healFactor", 1.0)))]
	return ""

func _refresh() -> void:
	for id in _form_buttons:
		_form_buttons[id].button_pressed = spec["form"] == id
	var chosen := {}
	for id in spec["terms"]:
		chosen[PatternTerms.term(id)["kind"]] = id
	for key in _term_buttons:
		var parts: PackedStringArray = String(key).split(":")
		_term_buttons[key].button_pressed = chosen.get(parts[0], "") == parts[1]
	_sentence.text = sentence(spec)
	var m := Fight.multiplier_of(spec)
	_numbers.text = "x%s   ·   chain of %d   ·   %s" % [str(snappedf(m, 0.01)), Fight.chain_length(spec), payout(spec)]

# --- Style -------------------------------------------------------------------

func _label(l: Label, size: int, color: Color) -> void:
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)

func _box(color: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.border_color = EDGE
	s.set_border_width_all(1)
	s.set_corner_radius_all(3)
	s.set_content_margin_all(10)
	return s

func _style_toggle(b: Button) -> void:
	b.add_theme_stylebox_override("normal", _box(Color(0.08, 0.07, 0.06)))
	b.add_theme_stylebox_override("hover", _box(Color(0.14, 0.11, 0.08)))
	b.add_theme_stylebox_override("pressed", _box(Color(0.32, 0.22, 0.08)))
	b.add_theme_stylebox_override("hover_pressed", _box(Color(0.36, 0.25, 0.09)))
	b.add_theme_stylebox_override("focus", _box(Color(0.12, 0.1, 0.07)))
	b.add_theme_stylebox_override("disabled", _box(Color(0.05, 0.045, 0.04)))
	b.add_theme_color_override("font_color", FG)
	b.add_theme_color_override("font_disabled_color", OFF)
	b.add_theme_color_override("font_pressed_color", GOLD)

func _button(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = "  %s  " % text
	b.add_theme_font_size_override("font_size", 18)
	b.custom_minimum_size = Vector2(0, 44)
	b.add_theme_stylebox_override("normal", _box(Color(0.1, 0.08, 0.06)))
	b.add_theme_stylebox_override("hover", _box(Color(0.2, 0.14, 0.08)))
	b.add_theme_stylebox_override("focus", _box(Color(0.2, 0.14, 0.08)))
	b.pressed.connect(cb)
	return b
