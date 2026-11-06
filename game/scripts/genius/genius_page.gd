## The genius's page: everything it is and everything it is learning, in the open. The Tally
## is shown in full (the design's honesty: a player can see what the genius reads of them).
class_name GeniusPage
extends CanvasLayer

signal closed

var _root := Control.new()

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
	visible = true
	var veil := ColorRect.new()
	veil.color = Color(0.02, 0.016, 0.016, 0.94)
	veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(veil)
	var info := g.to_dict()
	var card := GeniusCard.make(info, color, "YOUR GENIUS")
	card.position = Vector2(70, 60)
	_root.add_child(card)
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.offset_left = 500
	scroll.offset_right = -60
	scroll.offset_top = 50
	scroll.offset_bottom = -90
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_root.add_child(scroll)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 6)
	scroll.add_child(v)
	_h(v, "%s, %s" % [g.name if g.name != "" else g.form_name(), g.instar_name()], 36)
	v.add_child(Style.rule(420))
	if marks > 0:
		_p(v, "Your record: %d Marks." % marks, Style.DIM)
	_p(v, "A %s, %s. Resonance %d: it fights with %d Will and can carry %d shadow%s. Day %d since the rite." % [
		String(g.body.get("expression", "")).capitalize(), g.form_name(), g.resonance(tier), int(g.will_max(tier)), g.shadow_cap(tier), "" if g.shadow_cap(tier) == 1 else "s", g.day])
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
	Style.button(close, false, 18)
	close.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	close.position = Vector2(-260, -70)
	close.custom_minimum_size = Vector2(200, 46)
	close.pressed.connect(hide_page)
	_root.add_child(close)
	close.call_deferred("grab_focus")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

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
