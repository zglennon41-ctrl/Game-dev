## WILDLINE's one style, read from data/style.json (docs/style.md): "lamplight gothic". The
## interface's own look is here too: an old printer's capitals for titles (Cinzel), a warm book
## face for the story (Alegreya), a clean humanist face for the HUD (Alegreya Sans); dark ink
## plates with brass rims and clipped corners, like the plates on a rail engine. Every screen
## builds its panels and buttons from here, and everything the world draws asks here what its
## colours, lights, lines and motions are, so the look changes in one place: the data.
class_name Style
extends RefCounted

# The interface's palette (data/style.json, interface.colors).
static var INK: Color
static var PLATE: Color
static var PLATE_HI: Color
static var PLATE_ON: Color
static var BRASS: Color
static var BRASS_DIM: Color
static var BRASS_HI: Color
static var FG: Color
static var DIM: Color
static var FAINT: Color
static var GOLD: Color
static var EMBER: Color
static var BLOOD: Color
static var WILL: Color
static var FIELD: Color

static var _d: Dictionary = {}
static var _ramps: Dictionary = {}        # ramp -> [Color x5]
static var _conformed: Dictionary = {}    # class|rgb -> Color
static var _classes: Dictionary = {}      # material name -> class
static var _textures: Dictionary = {}     # a texture's content -> its conformed copy

static func _static_init() -> void:
	data()

## The style, as data. Read once.
static func data() -> Dictionary:
	if _d.is_empty():
		_d = JSON.parse_string(FileAccess.get_file_as_string("res://data/style.json"))
		for k in _d["ramps"]:
			_ramps[k] = (_d["ramps"][k] as Array).map(func(h): return Color(String(h)))
		var ui: Dictionary = _d["interface"]["colors"]
		var a := float(_d["interface"].get("plateAlpha", 0.94))
		INK = Color(String(ui["ink"]))
		PLATE = Color(Color(String(ui["plate"])), a)
		PLATE_HI = Color(Color(String(ui["plateHi"])), a + 0.02)
		PLATE_ON = Color(Color(String(ui["plateOn"])), a + 0.03)
		BRASS = Color(String(ui["brass"]))
		BRASS_DIM = Color(String(ui["brassDim"]))
		BRASS_HI = Color(String(ui["brassHi"]))
		FG = Color(String(ui["fg"]))
		DIM = Color(String(ui["dim"]))
		FAINT = Color(String(ui["faint"]))
		GOLD = Color(String(ui["gold"]))
		EMBER = Color(String(ui["ember"]))
		BLOOD = Color(String(ui["blood"]))
		WILL = Color(String(ui["will"]))
		FIELD = Color(String(ui["field"]))
	return _d

# --- Colour: the ramps, and what may be loud -------------------------------------------

## A ramp's five colours, shadow to light.
static func ramp(name: String) -> Array:
	data()
	return _ramps.get(name, [])

static func ramp_at(name: String, step: int) -> Color:
	var r := ramp(name)
	return r[clampi(step, 0, r.size() - 1)] if not r.is_empty() else Color.MAGENTA

## How saturated a colour is (HSV), the measure the cap is in.
static func saturation(c: Color) -> float:
	var mx := maxf(c.r, maxf(c.g, c.b))
	return 0.0 if mx <= 0.0001 else (mx - minf(c.r, minf(c.g, c.b))) / mx

## The Shape's colour: the field's, and the only loud thing a partner owns.
static func shape_color(shape: String) -> Color:
	var sh: Dictionary = data()["loud"]["shapes"]
	return Color(String(sh.get(shape, sh["anchor"])))

static func telegraph() -> Color:
	return Color(String(data()["loud"]["telegraph"]))

## The class of a material, by its name (data/style.json, materials.words): the first word in
## the list that the name carries. "" for a name that says nothing; a class written a|b is
## decided by the colour.
static func material_class(name: String, color := Color(-1, -1, -1)) -> String:
	var key := name.to_lower()
	var found := ""
	if _classes.has(key):
		found = _classes[key]
	else:
		for pair in data()["materials"]["words"]:
			if key.contains(String(pair[0])):
				found = String(pair[1])
				break
		_classes[key] = found
	if found.contains("|"):
		var best := ""
		var best_d := 1e9
		for alt in found.split("|"):
			var d := off_ramp(color, alt) if color.r >= 0.0 else 0.0
			if d < best_d:
				best_d = d
				best = alt
		return best
	return found

## What a class is: its ramps, bands, shadow tint, highlight, grain and wear.
static func class_spec(cls: String) -> Dictionary:
	return data()["materials"]["classes"].get(cls, data()["materials"]["classes"]["cloth"])

## The nearest point to a colour on the ramps a class allows, and how far it is: [Color, distance].
static func _nearest(c: Color, cls: String) -> Array:
	var names: Array = class_spec(cls).get("ramps", [])
	var best := c
	var best_d := 1e9
	for rn in names:
		var pts: Array = ramp(String(rn))
		for i in pts.size() - 1:
			var a: Color = pts[i]
			var b: Color = pts[i + 1]
			var ab := Vector3(b.r - a.r, b.g - a.g, b.b - a.b)
			var t := clampf(Vector3(c.r - a.r, c.g - a.g, c.b - a.b).dot(ab) / maxf(ab.length_squared(), 1e-9), 0.0, 1.0)
			var p := Vector3(a.r, a.g, a.b) + ab * t
			var d := p.distance_to(Vector3(c.r, c.g, c.b))
			if d < best_d:
				best_d = d
				best = Color(p.x, p.y, p.z, c.a)
	return [best, best_d if best_d < 1e8 else 0.0]

## How far a colour is from the ramps its class allows (0 for a class that is not held to any).
static func off_ramp(c: Color, cls: String) -> float:
	return float(_nearest(c, cls)[1])

## The colour a surface of this class takes: itself if it is on a ramp (within the tolerance),
## else the nearest point of the nearest ramp its class allows. The field, the lit and skin
## are not moved.
static func conform(c: Color, cls: String) -> Color:
	if cls == "" or (class_spec(cls).get("ramps", []) as Array).is_empty():
		return c
	var key := "%s|%d|%d|%d" % [cls, int(c.r * 255.0 + 0.5), int(c.g * 255.0 + 0.5), int(c.b * 255.0 + 0.5)]
	if not _conformed.has(key):
		var n := _nearest(c, cls)
		var near := float(n[1]) <= float(data().get("tolerance", 0.03)) and saturation(c) <= cap_of(cls)
		_conformed[key] = c if near else Color((n[0] as Color).r, (n[0] as Color).g, (n[0] as Color).b)
	var out: Color = _conformed[key]
	return Color(out.r, out.g, out.b, c.a)

## The most saturated a surface of this class may be: the cap, or the accents' for a class
## that may wear brass, or skin's.
static func cap_of(cls: String) -> float:
	if cls == "skin":
		return float(data()["skinCap"])
	for rn in class_spec(cls).get("ramps", []):
		if (data()["accents"] as Array).has(rn):
			return float(data()["accentCap"])
	return float(data()["cap"])

## Whether a class may shine with a light of its own: the field, the lit, the moon on water.
static func glows(cls: String) -> bool:
	return bool(class_spec(cls).get("glows", false)) if cls != "" else false

## The same, for a material known only by its name.
static func conform_named(c: Color, name: String) -> Color:
	return conform(c, material_class(name, c))

## Whether a colour is on-style for its class: on a ramp, or of a class that carries light.
static func on_style(c: Color, cls: String) -> bool:
	if cls == "":
		return false
	if (class_spec(cls).get("ramps", []) as Array).is_empty():
		return cls != "skin" or saturation(c) <= float(data()["skinCap"])
	return off_ramp(c, cls) <= float(data().get("tolerance", 0.03)) + 0.002

## A painted texture brought onto the ramps (a CC0 kit's palette sheet): every colour in it
## moved as conform() would move it. Made once for each picture, small, and kept.
static func conform_texture(tex: Texture2D) -> Texture2D:
	if tex == null:
		return tex
	var path := tex.resource_path
	if path != "" and _textures.has(path):
		return _textures[path]
	var img: Image = tex.get_image()
	if (img == null or img.is_empty()) and path != "" and FileAccess.file_exists(path):
		img = Image.load_from_file(path)      # headless: the picture is not on a graphics card
	if img == null or img.is_empty():
		return tex
	if img.is_compressed():
		if img.decompress() != OK:
			return tex
	img.convert(Image.FORMAT_RGBA8)
	if maxi(img.get_width(), img.get_height()) > 256:
		img.resize(mini(img.get_width(), 256), mini(img.get_height(), 256), Image.INTERPOLATE_BILINEAR)
	var bytes := img.get_data()
	var key := "%d:%d" % [bytes.size(), hash(bytes)]
	if not _textures.has(key):
		var memo := {}
		for i in range(0, bytes.size(), 4):
			var k := (bytes[i] >> 2) << 12 | (bytes[i + 1] >> 2) << 6 | (bytes[i + 2] >> 2)
			if not memo.has(k):
				var c := conform(Color8(bytes[i], bytes[i + 1], bytes[i + 2]), "mixed")
				memo[k] = [c.r8, c.g8, c.b8]
			var m: Array = memo[k]
			bytes[i] = m[0]
			bytes[i + 1] = m[1]
			bytes[i + 2] = m[2]
		var out := Image.create_from_data(img.get_width(), img.get_height(), false, Image.FORMAT_RGBA8, bytes)
		out.generate_mipmaps()
		_textures[key] = ImageTexture.create_from_image(out)
	if path != "":
		_textures[path] = _textures[key]
	return _textures[key]

## The ramps as a lookup, for a shader: sixteen slices of sixteen by sixteen side by side,
## each colour of the cube moved as conform() would move a painted texture's. Made once, and
## only where a texture could not be brought over on the processor.
static var _lut: ImageTexture
static func ramp_lut() -> ImageTexture:
	if _lut:
		return _lut
	var n := 16
	var img := Image.create(n * n, n, false, Image.FORMAT_RGB8)
	for b in n:
		for g in n:
			for r in n:
				img.set_pixel(b * n + r, g, conform(Color(r / 15.0, g / 15.0, b / 15.0), "mixed"))
	_lut = ImageTexture.create_from_image(img)
	return _lut

# --- Light ------------------------------------------------------------------------------

## One of the three lights (lamp, fire, moon, window): "cast" is what it throws on a surface,
## "color" the light as you see its source.
static func light(name: String, what := "cast") -> Color:
	var l: Dictionary = data()["lights"].get(name, {})
	return Color(String(l.get(what, l.get("color", "#FFFFFF"))))

static func light_energy(name: String) -> float:
	return float(data()["lights"].get(name, {}).get("energy", 1.0))

## What a kind of place is lit by (hall, court, wild, cut). A place may give its own numbers
## over its kind's (data/academy.json and data/creation.json, style; a zone's light).
static func place_light(kind: String) -> Dictionary:
	var kinds: Dictionary = data()["lights"]["kinds"]
	return kinds.get(kind, kinds["court"])

## A light's colour brought to the style: a warm one becomes the lamp's (or the fire's, if it
## is redder), a cool one the moon's. `what` is "cast" for what it throws on a surface, "color"
## for the light as you see its source (a flame, a lit pane).
static func conform_light(c: Color, what := "cast") -> Color:
	if saturation(c) < 0.04:
		return c
	var h := c.h
	if h < 0.2 or h > 0.9:
		if what == "color" and h >= 0.075 and h < 0.2:
			return Color(String(data()["lights"]["window"]["color"]))
		return light("fire" if (h < 0.075 or h > 0.9) else "lamp", what)
	if h > 0.5 and h < 0.75:
		return light("moon", what)
	return c

# --- Line, effects, motion --------------------------------------------------------------

## The ink line's width in pixels for what carries it (people, beasts, genii; 0 for places),
## on a screen of the given height.
static func ink_width(category: String, screen_height := 0.0) -> float:
	var ink: Dictionary = data()["ink"]
	var w := float(ink["width"].get(category, 0.0))
	return w * (screen_height / float(ink.get("screen", 900)) if screen_height > 0.0 else 1.0)

static func ink_color() -> Color:
	return Color(String(data()["ink"]["color"]))

## An effect's colour by what it is for (telegraph, hurt, guard, parry, stagger, spark, dust,
## smoke, shot, text, dim).
static func fx(name: String) -> Color:
	return Color(String(data()["effects"]["colors"].get(name, "#F2E8D6")))

## A number of the effects' shapes: fx_n("ring", "seconds").
static func fx_n(shape: String, key: String, fallback := 0.0) -> float:
	return float(data()["effects"].get(shape, {}).get(key, fallback))

## One of the interface's times (data/style.json, motion.ui): "quick" for a prompt, "arrive"
## for a panel, "leave", "ceremony" for a title or a fade between places, "stagger", "hold".
static func t(name: String) -> float:
	return float(data()["motion"]["ui"].get(name, 0.3))

## How a thing with weight comes to rest in the world: one small overshoot, never a bounce.
static func ease_settle(tw: PropertyTweener) -> PropertyTweener:
	if String(data()["motion"].get("settle", "back")) == "back":
		return tw.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	return tw.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

## A number of the motion language: motion("hover", "period"), motion("idle", "period").
static func motion(group: String, key: String, fallback := 0.0) -> float:
	return float(data()["motion"].get(group, {}).get(key, fallback))

## The interface's easing on a tween's step: everything arrives the same way.
static func ease_ui(t: PropertyTweener) -> PropertyTweener:
	match String(data()["motion"]["ui"].get("ease", "out-cubic")):
		"out-sine": return t.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		"out-quad": return t.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		"linear": return t.set_trans(Tween.TRANS_LINEAR)
		_: return t.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

# --- The interface ----------------------------------------------------------------------

static var _fonts := {}

static func font(kind: String) -> Font:
	if _fonts.has(kind):
		return _fonts[kind]
	var ty: Dictionary = data()["type"]
	var path := ""
	var weight := 0
	match kind:
		"title": path = "%s.ttf" % ty["title"]; weight = 600
		"title_light": path = "%s.ttf" % ty["title"]; weight = 450
		"body": path = "%s.ttf" % ty["body"]; weight = 400
		"body_bold": path = "%s.ttf" % ty["body"]; weight = 700
		"italic": path = "%s-Italic.ttf" % ty["body"]
		"ui": path = "%s-Medium.ttf" % ty["ui"]
		"ui_bold": path = "%s-Bold.ttf" % ty["ui"]
		_: path = "%s-Regular.ttf" % ty["ui"]
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
static func plate(bg := PLATE, rim := BRASS_DIM, width := -1, margin := 14.0, cut := -1) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = rim
	s.set_border_width_all(width if width >= 0 else int(data()["interface"].get("rim", 1)))
	s.set_corner_radius_all(cut if cut >= 0 else int(data()["interface"].get("cut", 7)))
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

## Fade a control in from slightly below: every screen arrives this way, in the motion
## language's time (data/style.json, motion.ui).
static func arrive(c: CanvasItem, delay := 0.0, rise := 12.0) -> void:
	if not c.is_inside_tree():
		return
	c.modulate.a = 0.0
	var ctl := c as Control
	var tw := c.create_tween()
	tw.set_parallel(true)
	ease_ui(tw.tween_property(c, "modulate:a", 1.0, t("arrive")).set_delay(delay))
	if ctl and not (ctl.get_parent() is Container):
		var to := ctl.position
		ctl.position.y += rise
		ease_ui(tw.tween_property(ctl, "position", to, t("arrive")).set_delay(delay))

## The same going: a control fades in the interface's leaving time, then `then` is called.
static func leave(c: CanvasItem, then: Callable = Callable()) -> void:
	if not c.is_inside_tree():
		if then.is_valid():
			then.call()
		return
	var tw := c.create_tween()
	ease_ui(tw.tween_property(c, "modulate:a", 0.0, t("leave")))
	if then.is_valid():
		tw.tween_callback(then)
