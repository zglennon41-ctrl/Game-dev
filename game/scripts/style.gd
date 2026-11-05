## WILDLINE's look on screen: "lamplight gothic". An old printer's capitals for titles (Cinzel),
## a warm book face for the story (Alegreya), a clean humanist face for the HUD (Alegreya Sans);
## dark ink plates with brass rims and clipped corners, like the plates on a rail engine.
## Every screen builds its panels and buttons from here, so the look changes in one place.
class_name Style
extends RefCounted

# The palette.
const INK := Color(0.035, 0.03, 0.028)
const PLATE := Color(0.062, 0.052, 0.046, 0.94)
const PLATE_HI := Color(0.13, 0.095, 0.06, 0.96)
const PLATE_ON := Color(0.27, 0.18, 0.07, 0.97)
const BRASS := Color(0.66, 0.5, 0.27)
const BRASS_DIM := Color(0.36, 0.29, 0.19)
const BRASS_HI := Color(1.0, 0.82, 0.46)
const FG := Color(0.95, 0.91, 0.84)
const DIM := Color(0.66, 0.61, 0.54)
const FAINT := Color(0.45, 0.41, 0.36)
const GOLD := Color(1.0, 0.8, 0.38)
const EMBER := Color(0.92, 0.36, 0.2)
const BLOOD := Color(0.78, 0.17, 0.14)
const WILL := Color(0.42, 0.68, 0.98)
const FIELD := Color(0.62, 0.95, 0.7)

static var _fonts := {}

static func font(kind: String) -> Font:
	if _fonts.has(kind):
		return _fonts[kind]
	var path := ""
	var weight := 0
	match kind:
		"title": path = "Cinzel.ttf"; weight = 600
		"title_light": path = "Cinzel.ttf"; weight = 450
		"body": path = "Alegreya.ttf"; weight = 400
		"body_bold": path = "Alegreya.ttf"; weight = 700
		"italic": path = "Alegreya-Italic.ttf"
		"ui": path = "AlegreyaSans-Medium.ttf"
		"ui_bold": path = "AlegreyaSans-Bold.ttf"
		_: path = "AlegreyaSans-Regular.ttf"
	# Loaded as an imported resource, so it is packed into every export (the web too).
	var ff: FontFile = load("res://game/assets/fonts/" + path)
	ff.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	ff.hinting = TextServer.HINTING_LIGHT
	var f: Font = ff
	if weight > 0:
		var fv := FontVariation.new()
		fv.base_font = ff
		fv.variation_opentype = { TextServerManager.get_primary_interface().name_to_tag("wght"): weight }
		f = fv
	_fonts[kind] = f
	return f

## A plate: dark ink, a brass rim, clipped corners.
static func plate(bg := PLATE, rim := BRASS_DIM, width := 1, margin := 14.0, cut := 7) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = rim
	s.set_border_width_all(width)
	s.set_corner_radius_all(cut)
	s.corner_detail = 1   # straight cuts, not rounds
	s.set_content_margin_all(margin)
	s.shadow_color = Color(0, 0, 0, 0.45)
	s.shadow_size = 10
	s.anti_aliasing = true
	return s

## Buttons: a plate that warms on hover and lights its rim when focused.
static func button(b: Button, on := false, size := 19, kind := "ui") -> void:
	var base := PLATE_ON if on else Color(0.075, 0.063, 0.054, 0.93)
	var m := 12.0
	var n := plate(base, BRASS if on else BRASS_DIM, 1, m)
	n.content_margin_left = 20
	var h := plate(PLATE_HI, BRASS, 1, m)
	h.content_margin_left = 20
	h.border_width_left = 4
	var f := plate(PLATE_HI, BRASS_HI, 1, m)
	f.content_margin_left = 20
	f.border_width_left = 4
	var p := plate(PLATE_ON, BRASS_HI, 1, m)
	p.content_margin_left = 20
	p.border_width_left = 4
	var d := plate(Color(0.05, 0.045, 0.04, 0.8), Color(0.2, 0.17, 0.13), 1, m)
	d.content_margin_left = 20
	b.add_theme_stylebox_override("normal", n)
	b.add_theme_stylebox_override("hover", h)
	b.add_theme_stylebox_override("focus", f)
	b.add_theme_stylebox_override("pressed", p)
	b.add_theme_stylebox_override("hover_pressed", p)
	b.add_theme_stylebox_override("disabled", d)
	b.add_theme_font_override("font", font(kind))
	b.add_theme_font_size_override("font_size", size)
	b.add_theme_color_override("font_color", GOLD if on else FG)
	b.add_theme_color_override("font_hover_color", BRASS_HI)
	b.add_theme_color_override("font_focus_color", BRASS_HI)
	b.add_theme_color_override("font_pressed_color", BRASS_HI)
	b.add_theme_color_override("font_hover_pressed_color", BRASS_HI)
	b.add_theme_color_override("font_disabled_color", FAINT)
	b.focus_mode = Control.FOCUS_ALL
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	# Hovering a button takes the keyboard's focus too, so mouse and pad agree on what is chosen.
	b.mouse_entered.connect(func(): if b.is_inside_tree() and not b.disabled: b.grab_focus())

static func label(l: Label, size: int, color := FG, kind := "ui", outline := 0) -> Label:
	l.add_theme_font_override("font", font(kind))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if outline > 0:
		l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
		l.add_theme_constant_override("outline_size", outline)
	if kind.begins_with("title"):
		l.add_theme_constant_override("line_spacing", -2)
	return l

static func rich(r: RichTextLabel, size: int, color := FG, kind := "body") -> RichTextLabel:
	r.add_theme_font_override("normal_font", font(kind))
	r.add_theme_font_override("bold_font", font("body_bold" if kind == "body" else "ui_bold"))
	r.add_theme_font_override("italics_font", font("italic"))
	for k in ["normal_font_size", "bold_font_size", "italics_font_size"]:
		r.add_theme_font_size_override(k, size)
	r.add_theme_color_override("default_color", color)
	r.add_theme_constant_override("line_separation", 3)
	return r

## A brass rule with a lozenge in the middle: the divider under titles.
static func rule(width := 360.0, color := BRASS) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(width, 14)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(func():
		var w := c.size.x
		var y := c.size.y / 2.0
		var d := PackedVector2Array([Vector2(5, y - 5), Vector2(10, y), Vector2(5, y + 5), Vector2(0, y)])
		c.draw_colored_polygon(d, color)
		c.draw_polyline_colors(PackedVector2Array([Vector2(16, y), Vector2(w, y)]), PackedColorArray([Color(color, 0.85), Color(color, 0.0)]), 1.0)
	)
	return c

## A bar: an inset groove with a brass rim, the fill, and a lighter "ghost" that trails behind
## a loss so the size of a hit reads at a glance.
static func bar_styles(b: ProgressBar, color: Color, ghost := false) -> void:
	b.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.02, 0.015, 0.015, 0.0 if ghost else 0.78)
	bg.border_color = Color(BRASS_DIM, 0.0 if ghost else 1.0)
	bg.set_border_width_all(1)
	bg.set_corner_radius_all(3)
	bg.corner_detail = 1
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	fill.set_corner_radius_all(2)
	fill.corner_detail = 1
	fill.set_expand_margin_all(-2)
	if not ghost:
		fill.border_color = color.lightened(0.35)
		fill.border_width_top = 2   # a lit top edge, like glass over the reading
	b.add_theme_stylebox_override("background", bg)
	b.add_theme_stylebox_override("fill", fill)

## The look every control falls back to, for anything not styled by hand.
static func apply_global() -> void:
	ThemeDB.fallback_font = font("ui")
	var t := ThemeDB.get_default_theme()
	if t == null:
		return
	t.default_font = font("ui")
	var le := plate(Color(0.03, 0.026, 0.024, 0.95), BRASS_DIM, 1, 8)
	le.content_margin_left = 12
	var lef := plate(Color(0.04, 0.034, 0.03, 0.97), BRASS_HI, 1, 8)
	lef.content_margin_left = 12
	t.set_stylebox("normal", "LineEdit", le)
	t.set_stylebox("focus", "LineEdit", lef)
	t.set_color("font_color", "LineEdit", FG)
	t.set_color("caret_color", "LineEdit", BRASS_HI)
	t.set_color("selection_color", "LineEdit", Color(BRASS, 0.4))
	t.set_font("font", "LineEdit", font("body"))
	var grab := StyleBoxFlat.new()
	grab.bg_color = BRASS_DIM
	grab.set_corner_radius_all(3)
	var grab_hi := grab.duplicate()
	grab_hi.bg_color = BRASS
	var groove := StyleBoxFlat.new()
	groove.bg_color = Color(0, 0, 0, 0.35)
	groove.set_corner_radius_all(3)
	groove.set_content_margin_all(3)
	for sb in ["VScrollBar", "HScrollBar"]:
		t.set_stylebox("grabber", sb, grab)
		t.set_stylebox("grabber_highlight", sb, grab_hi)
		t.set_stylebox("grabber_pressed", sb, grab_hi)
		t.set_stylebox("scroll", sb, groove)
	t.set_color("font_color", "Label", FG)
	t.set_color("default_color", "RichTextLabel", FG)

## Fade a control in from slightly below: every screen arrives this way.
static func arrive(c: CanvasItem, delay := 0.0, rise := 12.0) -> void:
	if not c.is_inside_tree():
		return
	c.modulate.a = 0.0
	var ctl := c as Control
	var tw := c.create_tween()
	tw.set_parallel(true)
	tw.tween_property(c, "modulate:a", 1.0, 0.35).set_delay(delay).set_trans(Tween.TRANS_SINE)
	if ctl and not (ctl.get_parent() is Container):
		var to := ctl.position
		ctl.position.y += rise
		tw.tween_property(ctl, "position", to, 0.45).set_delay(delay).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
