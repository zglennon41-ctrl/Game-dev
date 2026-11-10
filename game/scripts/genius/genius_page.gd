## The genius's page: everything it is and everything it is learning, in the open. The Tally
## is shown in full (the design's honesty: a player can see what the genius reads of them).
class_name GeniusPage
extends CanvasLayer

signal closed
## The partner chose a coat, a marking or a keepsake. Whoever keeps the genius saves it and
## sets look_saved; if nobody does, the page saves it to the stored character itself.
signal look_changed(g: Genius)

var look_saved := false
var _root := Control.new()
var _g: Genius
var _color := Color.WHITE
var _tier := 0
var _marks_n := 0
var _scroll: ScrollContainer
var _card: GeniusCard

const MILESTONE_WORDS := {
	"rite": "the rite", "gate": "passing the Field Examination, at the Gate", "pattern-built": "building your own Pattern",
	"tier:3": "your Pattern's third Intention tier", "adept": "Adept in any archetype", "tier:4": "the fourth Intention tier",
	"master": "Master in any archetype", "tier:5": "the fifth Intention tier", "accord": "Accord: the Fifth Form and the fifth tier together",
}
const LINE_WORDS := {
	"families": "Technique families", "range": "Where your hits land", "orders": "Orders it carried out", "company": "Who you fought beside",
	"ground": "Where you ran", "discipline": "Your Discipline", "bonds": "Bonds",
}

func _ready() -> void:
	layer = 30
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	visible = false

func open(g: Genius, color: Color, tier := 0, marks := 0) -> void:
	for c in _root.get_children():
		c.queue_free()
	_g = g
	_color = color
	_tier = tier
	_marks_n = marks
	visible = true
	var veil := ColorRect.new()
	veil.color = Color(0.02, 0.016, 0.016, 0.8)
	veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(veil)
	# One sheet, like the board's: the card on the left, the page on the right.
	var sheet := PanelContainer.new()
	sheet.set_anchors_preset(Control.PRESET_FULL_RECT)
	sheet.offset_left = 40
	sheet.offset_right = -40
	sheet.offset_top = 30
	sheet.offset_bottom = -30
	sheet.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.034, 0.03, 0.97), Style.BRASS, 1, 22))
	_root.add_child(sheet)
	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 8)
	sheet.add_child(outer)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 16)
	outer.add_child(head)
	var title := Label.new()
	Style.label(title, 26, Style.GOLD, "title")
	title.text = "%s, %s" % [g.name if g.name != "" else g.form_name(), g.instar_name()]
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	var kicker := Label.new()
	Style.label(kicker, 14, Style.DIM, "italic")
	kicker.text = "your genius  ·  everything it is and everything it is learning"
	kicker.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(kicker)
	outer.add_child(Style.rule(420))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 28)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(row)
	var info := g.to_dict()
	var card := GeniusCard.make(info, color, "")
	card.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(card)
	_card = card
	var scroll := ScrollContainer.new()
	_scroll = scroll
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	row.add_child(scroll)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 6)
	scroll.add_child(v)
	var foot := HBoxContainer.new()
	outer.add_child(foot)
	var hint := Label.new()
	Style.label(hint, 13, Style.DIM, "ui")
	hint.text = "J or Esc  close      scroll the page with the wheel or the stick"
	hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(hint)
	if marks > 0:
		_p(v, "Your record: %d Marks." % marks, Style.DIM)
	_p(v, "A %s, %s, %s. Resonance %d: it fights with %d Will and can carry %d shadow%s. Day %d since the rite." % [
		String(g.body.get("expression", "")).capitalize(), g.form_name(), String(g.age().get("word", "grown")), g.resonance(tier), int(g.will_max(tier)), g.shadow_cap(tier), "" if g.shadow_cap(tier) == 1 else "s", g.day])
	if g.is_born() and not g.look.is_empty():
		_look_section(v, g)
	# The next Reading.
	_section(v, "THE NEXT READING")
	var n := g.instar + 1
	if n <= 6:
		var r := GeniusResonance.instar_rule(n)
		var ways: Array = r["unlockedBy"].map(func(u): return MILESTONE_WORDS.get(u, u))
		var reason := GeniusResonance.unlock_reason(n, g.milestones, tier)
		var status := "Unlocked by %s" % MILESTONE_WORDS.get(reason, reason) if reason != "" else "Unlocked by %s" % " or ".join(ways)
		_p(v, "%s: %s, and at least %d days old. %s" % [r["name"], status, int(r["minDay"]), "It may be read now." if g.reading_due(tier) == n else ""])
	else:
		_p(v, "It is at its Apex.")
	# Orders.
	_section(v, "ORDERS")
	for o in Data.genius()["orders"]:
		var have := int(o["fromInstar"]) <= maxi(1, g.instar)
		var mark := "  [color=#ffd175](now)[/color]" if o["id"] == g.order else ""
		_p(v, "[b]%s[/b]%s  %s" % [o["name"], mark, o["text"]] if have else "[color=#736a60]%s: from the %s.[/color]" % [o["name"], GeniusResonance.instar_rule(int(o["fromInstar"]))["name"]])
	# Parts.
	_section(v, "WHAT IT IS MADE OF")
	var by := g.features_by_slot()
	for slot in by:
		_p(v, "[color=#a8803f]%s[/color]   %s" % [String(slot).to_upper(), ", ".join(by[slot].map(func(f): return Rite.feature_label(f)))])
	var gr: Dictionary = Data.rules["genius"]
	_p(v, "Heritage from earlier forms: %s.  Adaptations: %d of %d.  Grafts: %d of %d%s." % [
		", ".join(g.body.get("heritage", []).map(func(f): return Rite.feature_label(f))) if not g.body.get("heritage", []).is_empty() else "none yet",
		g.body.get("adaptations", []).size(), int(gr["adaptationSlots"]), g.body.get("grafts", []).size(), int(gr["graftSlots"]),
		(", %d waiting for the next Reading" % g.pending_grafts.size()) if not g.pending_grafts.is_empty() else ""], Style.DIM)
	# The Tally.
	_section(v, "WHAT IT IS LEARNING (THE TALLY, SINCE ITS LAST READING)")
	var any := false
	for line in LINE_WORDS:
		var d: Dictionary = g.tally.get(line, {})
		if d.is_empty():
			continue
		any = true
		var total := 0.0
		for k in d:
			total += float(d[k])
		var parts: Array = []
		var keys: Array = d.keys()
		keys.sort_custom(func(a, b): return float(d[a]) > float(d[b]))
		for k in keys:
			parts.append("%s %d%%" % [String(k).replace(".", " · "), roundi(100.0 * float(d[k]) / maxf(total, 1.0))])
		_p(v, "[color=#a8803f]%s[/color]   %s" % [LINE_WORDS[line], ",  ".join(parts)])
	var it: Variant = g.tally.get("intention")
	if it is Dictionary:
		_p(v, "[color=#a8803f]Your Pattern[/color]   %s, fired %d times" % [String(it["form"]).replace(".", " · "), int(it["fires"])])
		any = true
	if not any:
		_p(v, "Nothing yet. It learns from every fight, every order, every place you run.", Style.DIM)
	# Secondary forms and shadows.
	_section(v, "SECONDARY FORMS (%d of %d, from the %s)" % [g.secondary.size(), int(gr["secondarySlots"]), GeniusResonance.instar_rule(int(gr["secondaryFromInstar"]))["name"]])
	var ready := g.secondary_ready().map(func(s): return s["id"])
	for s in Data.secondary_forms():
		var has := g.secondary.any(func(x): return x["id"] == s["id"])
		var state := "developed" if has else ("ready" if ready.has(s["id"]) else "")
		_p(v, ("[b]%s[/b]" % s["name"] if state != "" else "[color=#9e958a]%s[/color]" % s["name"]) + ("  (%s)" % state if state != "" else "") + "   " + s["does"], Style.FG if state != "" else Style.DIM)
	_section(v, "SHADOWS (%d of %d)" % [g.shadows.size(), g.shadow_cap(tier)])
	if g.shadows.is_empty():
		_p(v, "Ten Patterns witnessed within its field make a shadow of it.", Style.DIM)
	for s in g.shadows:
		_p(v, "%s (%s)" % [s["name"], String(s["form"]).replace(".", " · ")])
	_section(v, "ITS LIFE")
	for h in g.history:
		_p(v, "Day %d: the %s, a %s%s." % [int(h["day"]), GeniusResonance.instar_rule(int(h["instar"]))["name"], h["name"], " (settled)" if h.get("settled", false) else " (chosen)"])
	var close := Button.new()
	close.text = "Close   (J)"
	Style.button(close, false, 17)
	close.custom_minimum_size = Vector2(180, 40)
	close.pressed.connect(hide_page)
	foot.add_child(close)
	close.call_deferred("grab_focus")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

## How this one looks, and what its partner may choose: one of its own few coats, which of its
## body's markings show, and a keepsake to wear.
func _look_section(v: Control, g: Genius) -> void:
	var form := String(g.body.get("form", ""))
	var sil := String(g.body.get("silhouette", ""))
	var res := GeniusLook.resolve(g.look, form, sil, g.instar)
	_section(v, "HOW IT LOOKS")
	_p(v, GeniusLook.describe(g.look, form, sil) + "  [color=#9e958a]No other %s is quite like it. Its build and its light it was born with; the coat, the markings and the keepsake are yours to choose.[/color]" % g.form_name().to_lower())
	var offered: Array = res["offered"]
	if not offered.is_empty():
		var row := _choice_row(v, "Coat")
		for i in offered.size():
			_choice(row, String(offered[i]["name"]).capitalize() + ("  (born)" if i == 0 else ""), clampi(int(g.look.get("coat", 0)), 0, offered.size() - 1) == i, func(): _set_look("coat", i), Color(String(offered[i]["main"])))
	var shown: Dictionary = res["marks"]
	if not shown.is_empty():
		var row := _choice_row(v, "Markings")
		var names: Dictionary = GeniusLook.body(sil)["marks"]
		for r in shown:
			_choice(row, String(names[r]["name"]).capitalize(), bool(shown[r]), func():
				var m: Dictionary = g.look.get("marks", {}).duplicate()
				m[r] = not bool(shown[r])
				_set_look("marks", m))
	# the home's hand: what its partner's home put on it, worn or put away
	var home_id := String(g.origin.get("city", ""))
	var trap: Dictionary = Data.bodies.get(home_id, {}).get("dress", {}).get("trapping", {})
	if not trap.is_empty():
		var trow := _choice_row(v, "From %s" % home_id.capitalize())
		var trap_on := bool(g.look.get("trapping", true))
		_choice(trow, String(trap["name"]).capitalize(), trap_on, func(): _set_look("trapping", not trap_on))
	var can: Array = GeniusLook.keepsakes_for(_card.body.sockets.keys()) if _card and _card.body else Data.genius_looks()["keepsakes"]
	var krow := _choice_row(v, "Keepsake")
	var worn := String(g.look.get("keepsake", ""))
	_choice(krow, "None", worn == "", func(): _set_look("keepsake", ""))
	for k in can:
		_choice(krow, String(k["name"]).capitalize(), worn == String(k["id"]), func(): _set_look("keepsake", String(k["id"])))
	if worn != "":
		var crow := _choice_row(v, "Its colour")
		var now := String(GeniusLook.keepsake_color(String(g.look.get("keepsakeColor", "")))["id"])
		for c in Data.genius_looks()["keepsakeColors"]:
			_choice(crow, String(c["name"]).capitalize(), now == String(c["id"]), func(): _set_look("keepsakeColor", String(c["id"])), Color(String(c["color"])))

func _choice_row(v: Control, label: String) -> HFlowContainer:
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	row.add_theme_constant_override("v_separation", 6)
	var l := Label.new()
	Style.label(l, 14, Style.BRASS, "title_light")
	l.text = label.to_upper()
	l.custom_minimum_size = Vector2(120, 34)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(l)
	v.add_child(row)
	return row

func _choice(row: Control, text: String, chosen: bool, then: Callable, swatch: Variant = null) -> void:
	var b := Button.new()
	b.text = text
	Style.button(b, chosen, 15)
	b.custom_minimum_size = Vector2(0, 34)
	if swatch is Color:
		# a chip of the colour itself beside its name
		var img := Image.create(14, 14, false, Image.FORMAT_RGBA8)
		img.fill(swatch)
		b.icon = ImageTexture.create_from_image(img)
	b.pressed.connect(then)
	row.add_child(b)

## A choice made: the genius keeps it, whoever holds the genius saves it, and the page is drawn
## again with the genius as it now looks.
func _set_look(key: String, value: Variant) -> void:
	if _g == null:
		return
	_g.look[key] = value
	look_saved = false
	look_changed.emit(_g)
	if not look_saved:
		var h: Dictionary = Settings.hero()
		var saved: Dictionary = h.get("genius", {})
		if not saved.is_empty() and String(saved.get("name", "")) == _g.name and String(saved.get("form", "")) == String(_g.body.get("form", "")):
			_g.save_to(h)
			Settings.save_hero(h)
	var at := _scroll.scroll_vertical if _scroll else 0
	open(_g, _color, _tier, _marks_n)
	_scroll.set_deferred("scroll_vertical", at)

func hide_page() -> void:
	visible = false
	closed.emit()

func _h(v: Control, t: String, size: int) -> void:
	var l := Label.new()
	Style.label(l, size, Style.FG, "title")
	l.text = t
	l.autowrap_mode = TextServer.AUTOWRAP_WORD
	v.add_child(l)

func _section(v: Control, t: String) -> void:
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 8)
	v.add_child(gap)
	var l := Label.new()
	Style.label(l, 14, Style.BRASS, "title")
	l.text = t
	v.add_child(l)

func _p(v: Control, t: String, color := Style.FG) -> void:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = true
	r.scroll_active = false
	Style.rich(r, 17, color, "body")
	r.text = t
	v.add_child(r)
