## The on-screen layer: the hero's frame, the target frame, the ability bar, the Pattern's
## chain, the tutorial box, menus and results. Built on Style (lamplight gothic).
class_name Hud
extends CanvasLayer

static var FG: Color = Style.FG
static var DIM: Color = Style.DIM
static var ACCENT: Color = Style.GOLD
static var RED: Color = Style.BLOOD
static var BLUE: Color = Style.WILL
static var GOLD: Color = Style.GOLD

## (the interface is drawn for a screen 900 high and scaled to the window: at 720 a size of 14
## is 11 pixels, which is the least that reads)
const SLOT_W := 96.0
const SLOT_H := 72.0

var play_ui := Control.new()
var _frame := PanelContainer.new()
var _name_label := Label.new()
var _shape_label := Label.new()
var _sigil := ColorRect.new()
var hp_bar := ProgressBar.new()
var hp_ghost := ProgressBar.new()
var will_bar := ProgressBar.new()
var hp_text := Label.new()
var will_text := Label.new()
var _g_row := VBoxContainer.new()
var _g_label := Label.new()
var _g_order := Label.new()
var g_bar := ProgressBar.new()
var _party := VBoxContainer.new()
var _party_rows: Array = []   # [{label, bar}]
var status := Label.new()
var target := PanelContainer.new()
var target_name := Label.new()
var target_sub := Label.new()
var target_bar := ProgressBar.new()
var target_ghost := ProgressBar.new()
var target_pips := Label.new()
var timer_label := Label.new()
var score_label := Label.new()
var bar := HBoxContainer.new()
var slots := {}
var pattern_banner := Label.new()
var prompt := PanelContainer.new()
var prompt_title := Label.new()
var prompt_text := RichTextLabel.new()
var prompt_note := Label.new()
var prompt_progress := Label.new()
var hint := RichTextLabel.new()
var objective_title := Label.new()
var objective_progress := Label.new()
var chip := PanelContainer.new()   # the step, folded: its name, the count, the note, and how to read it again
var chip_note := Label.new()
var chip_hint := Label.new()
var prompt_foot := Label.new()
var pad := false                  # the last thing pressed was a gamepad's: the keys shown are its buttons
var _prompt_raw := ""             # the step's words as written (for the keyboard)
var _prompt_min_until := 0.0      # the step's words stay at least this long (time to read them)
var _prompt_max_until := 0.0      # and fold by themselves at this
var _prompt_acted := false        # the player has done the first thing the step asks
var _progress_first := "\n"
var _hint_until := 0.0
var screen := Control.new()
var card := Control.new()         # a story card: lines on black, one after another
var _card_black := ColorRect.new()
var _card_box := VBoxContainer.new()
var _card_hint := Label.new()
var _card_items: Array = []       # the lines, in the order they arrive
var _card_next := Callable()
var _card_t := 0.0                # seconds the card has been up
var _card_full_at := 0.0          # when its last line has arrived
var _card_auto := 0.0             # it goes on by itself this long after that (0: it waits)
var _card_state := ""             # "", arriving, waiting, leaving
var _card_serial := 0
var speech := Control.new()       # someone speaks: a plate across the foot of the screen
var _speech_name := Label.new()
var _speech_sub := Label.new()
var _speech_text := RichTextLabel.new()
var _speech_hint := Label.new()
var _speech_count := Label.new()
var _speech_buttons := HBoxContainer.new()
var _speech_bars: Array = []
var _speech_lines: Array = []
var _speech_i := 0
var _speech_t := 0.0
var _speech_end: Array = []       # the buttons after the last line
var _speech_tween: Tween = null
var _veil := ColorRect.new()
var _center := CenterContainer.new()
var _left := MarginContainer.new()
var screen_box := VBoxContainer.new()

var _hero_name := "Anchor"
var _hero_sub := "Anchor"
var _accent := Style.GOLD
var _hp_ghost_hold := 0.0
var _t_ghost_hold := 0.0
var _last_hp := -1.0
var _last_t := -1.0
var _play_time := 0.0
var _hurt_flash := 0.0

const SLOTS := [
	["attack", "LMB", "Strike", ""],
	["block", "RMB", "Block · Parry", ""],
	["dodge", "Space", "Dodge", "8"],
	["technique", "Q", "Technique", "18"],
	["tech1", "1", "", ""],
	["tech2", "2", "", ""],
	["tech3", "3", "", ""],
	["stance", "F", "Stance", "2/s"],
	["pattern", "R", "Pattern", ""],
	["genius", "G", "Genius", ""],
]

const VEIL := """
shader_type canvas_item;
uniform float mode = 0.0;   // 0: a centred card, 1: the title (dark on the left, the world on the right)
void fragment() {
	vec2 uv = UV;
	float a;
	if (mode > 0.5) {
		a = mix(0.92, 0.0, smoothstep(0.16, 0.7, uv.x));
		a = max(a, smoothstep(0.6, 1.0, uv.y) * 0.5);
	} else {
		float d = length((uv - 0.5) * vec2(1.3, 1.0));
		a = mix(0.84, 0.97, smoothstep(0.1, 0.75, d));
	}
	COLOR = vec4(0.02, 0.016, 0.016, a);
}
"""

func _ready() -> void:
	layer = 10
	play_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	play_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(play_ui)

	# The hero's frame: a plate, a Shape-coloured sigil, the name, health and Will.
	_frame.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_frame.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_frame.position = Vector2(24, -24)
	_frame.custom_minimum_size = Vector2(330, 0)
	_frame.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.034, 0.03, 0.72), Style.BRASS_DIM, 1, 10))
	play_ui.add_child(_frame)
	var me := VBoxContainer.new()
	me.add_theme_constant_override("separation", 4)
	_frame.add_child(me)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 12)
	me.add_child(head)
	_sigil.custom_minimum_size = Vector2(11, 11)
	_sigil.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_sigil.rotation = PI / 4.0
	_sigil.pivot_offset = Vector2(5.5, 5.5)
	head.add_child(_sigil)
	Style.label(_name_label, 17, FG, "title", 4)
	head.add_child(_name_label)
	Style.label(_shape_label, 14, DIM.lerp(FG, 0.2), "ui")
	_shape_label.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(_shape_label)
	me.add_child(_meter(hp_bar, hp_ghost, hp_text, RED, 14, 310))
	me.add_child(_meter(will_bar, null, null, BLUE, 6, 310))
	var srow := HBoxContainer.new()
	me.add_child(srow)
	Style.label(status, 14, ACCENT, "ui_bold", 3)
	status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	srow.add_child(status)
	Style.label(will_text, 14, BLUE.lightened(0.3), "ui", 3)
	srow.add_child(will_text)
	# The genius: its name and form, its Will, its order (G changes it).
	_g_row.add_theme_constant_override("separation", 3)
	var grow := HBoxContainer.new()
	grow.add_theme_constant_override("separation", 10)
	_g_row.add_child(grow)
	Style.label(_g_label, 13, FG, "title", 3)
	_g_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grow.add_child(_g_label)
	Style.label(_g_order, 13, GOLD, "ui_bold", 3)
	grow.add_child(_g_order)
	_g_row.add_child(_meter(g_bar, null, null, Style.GOLD, 5, 310))
	_g_row.visible = false
	me.add_child(_g_row)
	# The party: a small bar for each classmate beside you.
	_party.add_theme_constant_override("separation", 3)
	for i in 2:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		var l := Label.new()
		Style.label(l, 13, Style.DIM, "ui", 3)
		l.custom_minimum_size = Vector2(130, 0)
		l.clip_text = true
		row.add_child(l)
		var b := ProgressBar.new()
		Style.bar_styles(b, Color(0.55, 0.72, 0.95))
		b.custom_minimum_size = Vector2(170, 5)
		b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(b)
		_party.add_child(row)
		_party_rows.append({ "label": l, "bar": b, "row": row })
	_party.visible = false
	me.add_child(_party)

	# The target frame.
	target.set_anchors_preset(Control.PRESET_CENTER_TOP)
	target.custom_minimum_size = Vector2(420, 0)
	target.position = Vector2(-210, 14)
	target.add_theme_stylebox_override("panel", Style.plate(Color(0.04, 0.03, 0.03, 0.66), Style.BRASS_DIM, 1, 8))
	var tv := VBoxContainer.new()
	tv.add_theme_constant_override("separation", 3)
	target.add_child(tv)
	var trow := HBoxContainer.new()
	trow.alignment = BoxContainer.ALIGNMENT_CENTER
	trow.add_theme_constant_override("separation", 12)
	tv.add_child(trow)
	Style.label(target_name, 16, FG, "title", 4)
	trow.add_child(target_name)
	Style.label(target_sub, 14, DIM.lerp(FG, 0.2), "ui", 3)
	target_sub.size_flags_vertical = Control.SIZE_SHRINK_END
	trow.add_child(target_sub)
	tv.add_child(_meter(target_bar, target_ghost, null, RED, 10, 400))
	Style.label(target_pips, 13, GOLD, "ui_bold", 4)
	target_pips.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tv.add_child(target_pips)
	play_ui.add_child(target)

	var right := VBoxContainer.new()
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	right.position = Vector2(-364, 18)
	right.custom_minimum_size = Vector2(340, 0)
	right.add_theme_constant_override("separation", 0)
	Style.label(timer_label, 36, FG, "title", 5)
	timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(timer_label)
	Style.label(score_label, 17, DIM.lerp(FG, 0.25), "italic", 4)
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(score_label)
	var ogap := Control.new()
	ogap.custom_minimum_size = Vector2(0, 6)
	right.add_child(ogap)
	# The step, folded away: a plate that reads over any ground, with the count in the open and
	# the key that brings the words back.
	var cs := Style.plate(Color(0.045, 0.038, 0.034, 0.84), Style.BRASS_DIM, 1, 10)
	cs.border_width_right = 4
	cs.border_color = Style.BRASS
	cs.content_margin_right = 16
	cs.content_margin_left = 14
	chip.add_theme_stylebox_override("panel", cs)
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.visible = false
	var cv := VBoxContainer.new()
	cv.add_theme_constant_override("separation", 1)
	chip.add_child(cv)
	Style.label(objective_title, 18, ACCENT, "title", 4)
	objective_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	objective_title.autowrap_mode = TextServer.AUTOWRAP_WORD
	cv.add_child(objective_title)
	Style.label(objective_progress, 19, FG, "ui_bold", 4)
	objective_progress.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	objective_progress.autowrap_mode = TextServer.AUTOWRAP_WORD
	cv.add_child(objective_progress)
	Style.label(chip_note, 16, FG, "italic", 3)
	chip_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	chip_note.autowrap_mode = TextServer.AUTOWRAP_WORD
	chip_note.visible = false
	cv.add_child(chip_note)
	Style.label(chip_hint, 14, DIM.lerp(FG, 0.45), "ui", 3)
	chip_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	cv.add_child(chip_hint)
	right.add_child(chip)
	play_ui.add_child(right)

	# The ability bar.
	bar.add_theme_constant_override("separation", 8)
	for s in SLOTS:
		bar.add_child(_slot(s))
	play_ui.add_child(bar)
	_place_bar(SLOTS.size())

	Style.label(pattern_banner, 20, GOLD, "title", 5)
	# Above the ability bar, clear of the gold ring at the hero's feet.
	pattern_banner.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	pattern_banner.grow_vertical = Control.GROW_DIRECTION_BEGIN
	pattern_banner.position = Vector2(-450, -SLOT_H - 100)
	pattern_banner.custom_minimum_size = Vector2(900, 0)
	pattern_banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	play_ui.add_child(pattern_banner)

	# The keys that are on no slot of the bar, under it: large enough and light enough to read.
	Style.rich(hint, 15, FG.lerp(DIM, 0.25), "ui")
	hint.bbcode_enabled = true
	hint.fit_content = true
	hint.scroll_active = false
	hint.autowrap_mode = TextServer.AUTOWRAP_OFF
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hint.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	hint.add_theme_constant_override("outline_size", 4)
	hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	hint.position = Vector2(-700, -26)
	hint.custom_minimum_size = Vector2(1400, 0)
	play_ui.add_child(hint)
	_write_hint(false, false)

	# The tutorial box: a plate with a brass edge down its left side.
	prompt.set_anchors_preset(Control.PRESET_CENTER_TOP)
	prompt.custom_minimum_size = Vector2(680, 0)
	prompt.position = Vector2(-340, 92)
	prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var ps := Style.plate(Color(0.045, 0.038, 0.034, 0.9), Style.BRASS, 1, 14)
	ps.border_width_left = 4
	ps.content_margin_left = 22
	prompt.add_theme_stylebox_override("panel", ps)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 6)
	prompt.add_child(pv)
	Style.label(prompt_title, 20, ACCENT, "title")
	pv.add_child(prompt_title)
	prompt_text.bbcode_enabled = true
	prompt_text.fit_content = true
	prompt_text.scroll_active = false
	prompt_text.custom_minimum_size = Vector2(640, 0)
	Style.rich(prompt_text, 19, FG, "body")
	pv.add_child(prompt_text)
	var row := HBoxContainer.new()
	Style.label(prompt_note, 17, FG.lerp(DIM, 0.3), "italic")
	prompt_note.autowrap_mode = TextServer.AUTOWRAP_WORD
	prompt_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(prompt_note)
	Style.label(prompt_progress, 19, ACCENT, "ui_bold")
	row.add_child(prompt_progress)
	pv.add_child(row)
	Style.label(prompt_foot, 14, DIM.lerp(FG, 0.3), "ui")
	prompt_foot.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	pv.add_child(prompt_foot)
	play_ui.add_child(prompt)

	# Menus, story cards and results.
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(screen)
	_veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sh := Shader.new()
	sh.code = VEIL
	var sm := ShaderMaterial.new()
	sm.shader = sh
	_veil.material = sm
	screen.add_child(_veil)
	_center.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen.add_child(_center)
	_left.set_anchors_preset(Control.PRESET_FULL_RECT)
	_left.add_theme_constant_override("margin_left", 120)
	_left.add_theme_constant_override("margin_top", 60)
	_left.add_theme_constant_override("margin_bottom", 60)
	screen.add_child(_left)
	# Both holders fill the screen and one lies over the other: neither may take the mouse, or
	# the buttons of whichever is underneath cannot be clicked.
	_center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen_box.custom_minimum_size = Vector2(640, 0)
	screen_box.add_theme_constant_override("separation", 10)
	_center.add_child(screen_box)
	_build_banner()
	_build_speech()
	_build_card()

## A meter: the groove, a lighter ghost that trails a loss (so the size of a hit reads), the fill.
func _meter(b: ProgressBar, ghost: ProgressBar, text: Label, color: Color, h: int, w: int) -> Control:
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(w, h)
	Style.bar_styles(b, color)
	if ghost:
		Style.bar_styles(ghost, Color(1.0, 0.86, 0.6, 0.85), true)
		var gbg := ghost.get_theme_stylebox("background").duplicate() as StyleBoxFlat
		gbg.bg_color = Color(0.02, 0.015, 0.015, 0.78)
		gbg.border_color = Style.BRASS_DIM
		ghost.add_theme_stylebox_override("background", gbg)
		ghost.set_anchors_preset(Control.PRESET_FULL_RECT)
		holder.add_child(ghost)
		# The real bar draws over the ghost, so its own groove is see-through.
		var bg := b.get_theme_stylebox("background").duplicate() as StyleBoxFlat
		bg.bg_color = Color(0, 0, 0, 0)
		b.add_theme_stylebox_override("background", bg)
	b.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.add_child(b)
	if text:
		Style.label(text, 13, FG, "ui_bold", 4)
		text.set_anchors_preset(Control.PRESET_FULL_RECT)
		text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		holder.add_child(text)
	return holder

## The ability bar sits centred at the bottom; all four offsets are set so no layout pass can
## leave it at the origin.
func _place_bar(n: int) -> void:
	# as wide as reads best, and narrower when there are many: the bar keeps clear of the
	# hero's frame at the left
	_slot_w = slot_width(n)
	for sl in slots.values():
		(sl["panel"] as Control).custom_minimum_size.x = _slot_w
		(sl["name"] as Control).custom_minimum_size.x = _slot_w - 10
	var w := (_slot_w + 8) * n - 8
	bar.anchor_left = 0.5
	bar.anchor_right = 0.5
	bar.anchor_top = 1.0
	bar.anchor_bottom = 1.0
	bar.offset_left = -w / 2.0
	bar.offset_right = w / 2.0
	bar.offset_top = -SLOT_H - 30
	bar.offset_bottom = -30

var _slot_w := SLOT_W
const BAR_MOST := 860.0     # the widest the bar may stand, between the frames at either side

## How wide a slot of the bar is when `n` of them show.
static func slot_width(n: int) -> float:
	return clampf(floorf((BAR_MOST + 8.0) / maxi(1, n) - 8.0), 64.0, SLOT_W)

func _slot(s: Array) -> PanelContainer:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(SLOT_W, SLOT_H)
	p.add_theme_stylebox_override("panel", _slot_box(Color(0.05, 0.042, 0.038, 0.86), Style.BRASS_DIM))
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", -1)
	p.add_child(v)
	var key := Label.new()
	Style.label(key, 18, FG, "title", 4)
	key.text = s[1]
	key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(key)
	var name := Label.new()
	Style.label(name, 14, DIM.lerp(FG, 0.25), "ui", 3)
	name.text = s[2]
	name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name.clip_text = true
	name.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name.custom_minimum_size = Vector2(SLOT_W - 10, 0)
	v.add_child(name)
	var cost := Label.new()
	Style.label(cost, 13, BLUE.lightened(0.25), "ui", 3)
	cost.text = ("%s Will" % s[3]) if s[3] != "" else " "
	cost.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(cost)
	# The cooldown: a dark shutter that lifts, with the seconds left on it.
	var cd_holder := Control.new()
	cd_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(cd_holder)
	var cd := ColorRect.new()
	cd.color = Color(0, 0, 0, 0.62)
	cd.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cd_holder.add_child(cd)
	var cd_text := Label.new()
	Style.label(cd_text, 20, FG, "title", 5)
	cd_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	cd_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	cd_text.set_anchors_preset(Control.PRESET_FULL_RECT)
	cd_holder.add_child(cd_text)
	slots[s[0]] = { "panel": p, "key": key, "name": name, "cd": cd, "cd_text": cd_text, "cost": cost, "state": "" }
	return p

func _slot_box(bg: Color, rim: Color, width := 1) -> StyleBoxFlat:
	var b := Style.plate(bg, rim, width, 4, 9)
	b.shadow_size = 6
	return b

## Name the ability bar for the hero in this fight.
func configure(f: Fight, hero_name: String) -> void:
	(slots["attack"]["name"] as Label).text = ("Draw" if f.style.has("draw") else "Shot") if f.ranged else "Strike"
	(slots["attack"]["cost"] as Label).text = " "
	(slots["technique"]["name"] as Label).text = f.tech["name"]
	(slots["technique"]["cost"] as Label).text = "%d Will" % int(f.tech["will"])
	(slots["stance"]["name"] as Label).text = f.kit["stance"]["name"]
	# The Discipline's three, once learned.
	var visible_n := 0
	for i in 3:
		var sid := "tech%d" % (i + 1)
		var have := i < f.extra_techs.size()
		(slots[sid]["panel"] as PanelContainer).visible = have
		if have:
			(slots[sid]["name"] as Label).text = f.extra_techs[i]["name"]
			(slots[sid]["cost"] as Label).text = "%d Will" % int(f.extra_techs[i]["will"])
	# The genius's key: what it does is its type's (an order, the hand, its use).
	(slots["genius"]["panel"] as PanelContainer).visible = f.genius != null
	for s in slots.values():
		if (s["panel"] as PanelContainer).visible:
			visible_n += 1
	_place_bar(visible_n)
	_write_hint(f.ranged and f.p_ammo_max > 0, f.genius != null)
	_hero_name = hero_name if hero_name != "" else "Anchor"
	var wname := String(Data.by_id(Data.weapons, f.hero.get("weapon", "saber")).get("name", ""))
	var gtier := String(f.gear.get("tier", "plain"))
	_hero_sub = "%s  ·  %s" % [String(f.player_shape).capitalize(), (String(f.gear.get("name", wname)) if gtier == "named" else ("fine " + wname.to_lower() if gtier == "fine" else wname))]
	_accent = World.SHAPE_COLORS.get(f.player_shape, Style.GOLD)
	_sigil.color = _accent
	_last_hp = -1.0
	_last_t = -1.0
	_play_time = 0.0
	_g_row.visible = f.genius != null
	_party.visible = not f.allies.is_empty()
	for i in _party_rows.size():
		(_party_rows[i]["row"] as Control).visible = i < f.allies.size()
	if f.genius:
		(g_bar.get_theme_stylebox("fill") as StyleBoxFlat).bg_color = _accent.lightened(0.15)

# --- Screens ----------------------------------------------------------------

## A screen: a title, a subtitle, a body and buttons. layout "title" sits on the left with the
## world showing on the right; "center" is a card on a dark veil.
func show_screen(title: String, subtitle: String, body: String, buttons: Array, layout := "center") -> void:
	for c in screen_box.get_children():
		screen_box.remove_child(c)
		c.queue_free()
	# "title": the game's name, large, on the left with the world on the right. "left": any
	# other screen that stands on the left the same way (the Academy's gate, the settings).
	var is_title := layout == "title"
	var on_left := layout in ["title", "left"]
	screen_box.get_parent().remove_child(screen_box)
	(_left if on_left else _center).add_child(screen_box)
	screen_box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	screen_box.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	screen_box.custom_minimum_size = Vector2(560 if on_left else 660, 0)
	(_veil.material as ShaderMaterial).set_shader_parameter("mode", 1.0 if on_left else 0.0)
	var items: Array = []
	if is_title:
		var kicker := Label.new()
		Style.label(kicker, 15, Style.BRASS, "title_light")
		kicker.text = "TEN THOUSAND YEARS AFTER THE AWAKENING"
		screen_box.add_child(kicker)
		items.append(kicker)
	var t := Label.new()
	var big := 88 if is_title else (50 if title.length() < 22 else 38)
	Style.label(t, big, Style.FG if is_title else Style.GOLD, "title", 0)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD
	t.text = title
	t.add_theme_color_override("font_shadow_color", Color(1.0, 0.68, 0.3, 0.22))
	t.add_theme_constant_override("shadow_offset_x", 0)
	t.add_theme_constant_override("shadow_offset_y", 0)
	t.add_theme_constant_override("shadow_outline_size", 16 if is_title else 10)
	screen_box.add_child(t)
	items.append(t)
	var r := Style.rule(320 if is_title else 420)
	screen_box.add_child(r)
	items.append(r)
	if subtitle != "":
		var s := Label.new()
		Style.label(s, 21, DIM, "italic")
		s.text = subtitle
		s.autowrap_mode = TextServer.AUTOWRAP_WORD
		screen_box.add_child(s)
		items.append(s)
	if body != "" and not is_title:
		var b := RichTextLabel.new()
		b.bbcode_enabled = true
		b.fit_content = true
		b.scroll_active = false
		b.custom_minimum_size = Vector2(screen_box.custom_minimum_size.x, 0)
		Style.rich(b, 19, FG, "body")
		b.text = body
		screen_box.add_child(b)
		items.append(b)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 8)
	screen_box.add_child(gap)
	var first: Button = null
	var row: HBoxContainer = null
	for spec in buttons:
		# a button: [words, what it does, { primary, quiet, row, sub }]. primary is the one a
		# player most likely wants (lit, larger, chosen first); quiet ones are smaller; row
		# puts the small ones side by side under the rest; sub is a second, dimmer line.
		var o: Dictionary = spec[2] if spec.size() > 2 else {}
		if o.has("stepper"):
			# a setting: its name, and its value between two arrows
			var st: Dictionary = o["stepper"]
			var line := HBoxContainer.new()
			line.add_theme_constant_override("separation", 10)
			var nm := Label.new()
			Style.label(nm, 20, Style.FG, "ui")
			nm.text = spec[0]
			nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			line.add_child(nm)
			var val := Label.new()
			Style.label(val, 20, Style.GOLD, "ui_bold")
			val.custom_minimum_size = Vector2(96, 0)
			val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			val.text = st["value"].call()
			var less := Button.new()
			var more := Button.new()
			for pair in [[less, "‹", -1], [more, "›", 1]]:
				var sb: Button = pair[0]
				var by: int = pair[2]
				sb.text = pair[1]
				sb.custom_minimum_size = Vector2(52, 44)
				Style.button(sb, false, 22)
				sb.alignment = HORIZONTAL_ALIGNMENT_CENTER
				sb.pressed.connect(func():
					st["step"].call(by)
					val.text = st["value"].call())
			line.add_child(less)
			line.add_child(val)
			line.add_child(more)
			screen_box.add_child(line)
			items.append(line)
			if first == null:
				first = more
			continue
		var btn := Button.new()
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.autowrap_mode = TextServer.AUTOWRAP_WORD
		var primary: bool = o.get("primary", false)
		var quiet: bool = o.get("quiet", false) or o.get("row", false)
		btn.custom_minimum_size = Vector2(0, 42 if quiet else 50)
		Style.button(btn, primary, 17 if quiet else (21 if primary else 19))
		if o.has("sub"):
			# two lines: the words, and under them who or what
			btn.custom_minimum_size = Vector2(0, 72)
			btn.autowrap_mode = TextServer.AUTOWRAP_OFF
			btn.clip_text = true
			var v := VBoxContainer.new()
			v.set_anchors_preset(Control.PRESET_FULL_RECT)
			v.offset_left = 22
			v.offset_right = -14
			v.alignment = BoxContainer.ALIGNMENT_CENTER
			v.add_theme_constant_override("separation", 0)
			v.mouse_filter = Control.MOUSE_FILTER_IGNORE
			var l1 := Label.new()
			Style.label(l1, 22, Style.GOLD if primary else Style.FG, "ui")
			l1.text = spec[0]
			l1.mouse_filter = Control.MOUSE_FILTER_IGNORE
			v.add_child(l1)
			var l2 := Label.new()
			Style.label(l2, 16, Style.DIM.lerp(Style.FG, 0.35), "italic")
			l2.text = String(o["sub"])
			l2.clip_text = true
			l2.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			l2.mouse_filter = Control.MOUSE_FILTER_IGNORE
			v.add_child(l2)
			btn.add_child(v)
		else:
			btn.text = spec[0]
		btn.pressed.connect(spec[1])
		if o.get("row", false):
			if row == null:
				row = HBoxContainer.new()
				row.add_theme_constant_override("separation", 10)
				screen_box.add_child(row)
				items.append(row)
			btn.alignment = HORIZONTAL_ALIGNMENT_CENTER
			btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(btn)
		else:
			screen_box.add_child(btn)
			items.append(btn)
		if first == null or (primary and not first.has_meta("primary")):
			first = btn
			if primary:
				btn.set_meta("primary", true)
	if is_title and body != "":
		# the title's foot: a quiet line under the menu
		var foot := RichTextLabel.new()
		foot.bbcode_enabled = true
		foot.fit_content = true
		foot.scroll_active = false
		foot.mouse_filter = Control.MOUSE_FILTER_IGNORE
		foot.custom_minimum_size = Vector2(screen_box.custom_minimum_size.x, 0)
		Style.rich(foot, 15, Style.DIM.lerp(Style.FG, 0.2), "ui")
		foot.text = body
		var fgap := Control.new()
		fgap.custom_minimum_size = Vector2(0, 6)
		screen_box.add_child(fgap)
		screen_box.add_child(foot)
		items.append(foot)
	screen.visible = true
	speech.visible = false
	play_ui.visible = false
	_veil.modulate.a = 0.0
	screen.create_tween().tween_property(_veil, "modulate:a", 1.0, Style.t("arrive"))
	for i in items.size():
		var it: CanvasItem = items[i]
		it.modulate.a = 0.0
		Style.ease_ui(it.create_tween().tween_property(it, "modulate:a", 1.0, Style.t("arrive")).set_delay(Style.t("stagger") * i))
	if first:
		first.call_deferred("grab_focus")

func hide_screen() -> void:
	screen.visible = false
	speech.visible = false
	play_ui.visible = true
	_play_time = 0.0

# --- A moment's title, over the play ------------------------------------------------

var _banner := VBoxContainer.new()
var _banner_title := Label.new()
var _banner_sub := Label.new()
var _banner_from := 0.0
var _banner_hold := 2.0

func _build_banner() -> void:
	# in the lower third: the words that rise off a blow stand over the heads, above it
	_banner.set_anchors_preset(Control.PRESET_CENTER)
	_banner.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_banner.position = Vector2(0, 86)
	_banner.custom_minimum_size = Vector2(1000, 0)
	_banner.add_theme_constant_override("separation", 2)
	_banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.visible = false
	add_child(_banner)
	Style.label(_banner_title, 58, Style.FG, "title", 8)
	_banner_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.add_child(_banner_title)
	_banner.add_child(_mid_rule(320))
	Style.label(_banner_sub, 24, Style.FG, "italic", 5)
	_banner_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.add_child(_banner_sub)

## The title of a moment in play (the field wakes, the Pattern lands): it arrives, holds, and
## goes, in real time, over whatever is happening. The step's words stand aside for it.
func banner(title: String, sub: String, color: Color, hold := 2.2) -> void:
	_banner_title.text = title
	_banner_title.add_theme_color_override("font_color", color.lerp(Style.FG, 0.45))
	_banner_sub.text = sub
	_banner_sub.visible = sub != ""
	_banner.visible = true
	_banner.modulate.a = 0.0
	_banner_from = Time.get_ticks_msec() / 1000.0
	_banner_hold = hold

## (by the wall's clock, not the game's: time slows under it)
func _banner_frame() -> void:
	if not _banner.visible:
		return
	var t := Time.get_ticks_msec() / 1000.0 - _banner_from
	var a_in := Style.t("arrive")
	var a_out := Style.t("ceremony")
	if t < a_in:
		_banner.modulate.a = t / a_in
	elif t < a_in + _banner_hold:
		_banner.modulate.a = 1.0
	elif t < a_in + _banner_hold + a_out:
		_banner.modulate.a = 1.0 - (t - a_in - _banner_hold) / a_out
	else:
		_banner.visible = false

func banner_up() -> bool:
	return _banner.visible

# --- Story cards -------------------------------------------------------------------

func _build_card() -> void:
	card.set_anchors_preset(Control.PRESET_FULL_RECT)
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.visible = false
	add_child(card)
	_card_black.color = Style.ramp_at("ink", 0) if Style.ramp("ink").size() > 0 else Color(0.012, 0.01, 0.01)
	_card_black.color.a = 1.0
	_card_black.set_anchors_preset(Control.PRESET_FULL_RECT)
	_card_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(_card_black)
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(c)
	_card_box.custom_minimum_size = Vector2(1180, 0)
	_card_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_card_box.add_theme_constant_override("separation", 22)
	_card_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(_card_box)
	Style.label(_card_hint, 18, Style.DIM.lerp(Style.FG, 0.45), "ui")
	_card_hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_card_hint.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_card_hint.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_card_hint.position = Vector2(0, -54)
	_card_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_card_hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(_card_hint)

## The brass rule for words that stand centred: the lozenge in the middle, a line fading to
## either side.
static func _mid_rule(width: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(width, 14)
	c.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(func():
		var w := c.size.x
		var y := c.size.y / 2.0
		var m := w / 2.0
		c.draw_colored_polygon(PackedVector2Array([Vector2(m, y - 5), Vector2(m + 5, y), Vector2(m, y + 5), Vector2(m - 5, y)]), Style.BRASS)
		c.draw_polyline_colors(PackedVector2Array([Vector2(m + 11, y), Vector2(w, y)]), PackedColorArray([Color(Style.BRASS, 0.85), Color(Style.BRASS, 0.0)]), 1.0)
		c.draw_polyline_colors(PackedVector2Array([Vector2(m - 11, y), Vector2(0, y)]), PackedColorArray([Color(Style.BRASS, 0.85), Color(Style.BRASS, 0.0)]), 1.0))
	return c

## How long a card's line waits for the line before it: time to read that line, and a breath.
static func card_wait(line: String) -> float:
	return clampf(0.7 + 0.2 * line.split(" ", false).size(), 1.0, 3.2)

## A story card: the whole screen goes dark and the lines arrive one after another. Any key,
## a click or a pad's button brings the rest at once, and then goes on; `next` is called with
## the screen still dark, and the dark lifts off whatever `next` has put there.
## style "story": a place and a time, then what is happening (the last line the largest).
## style "title": a small line over a large one (ACT ONE / THE ACADEMY), or one large line.
## auto: it goes on by itself this many seconds after its last line (0: it waits to be told).
func show_card(lines: Array, next: Callable, style := "story", auto := 0.0) -> void:
	_card_serial += 1
	for c in _card_box.get_children():
		_card_box.remove_child(c)
		c.queue_free()
	_card_items.clear()
	_card_next = next
	_card_auto = auto
	_card_t = 0.0
	var at := 0.5
	for i in lines.size():
		var l := Label.new()
		var last := i == lines.size() - 1
		if style == "title":
			if last:
				Style.label(l, 64 if lines.size() > 1 else 46, Style.FG, "title")
				l.add_theme_color_override("font_shadow_color", Color(1.0, 0.68, 0.3, 0.22))
				l.add_theme_constant_override("shadow_offset_x", 0)
				l.add_theme_constant_override("shadow_offset_y", 0)
				l.add_theme_constant_override("shadow_outline_size", 14)
			else:
				Style.label(l, 20, Style.BRASS, "title_light")
		elif last and lines.size() > 1:
			Style.label(l, 34, Style.FG, "body")
		elif i == 0:
			Style.label(l, 21, Style.BRASS, "title_light")
		else:
			Style.label(l, 24, Style.DIM.lerp(Style.FG, 0.3), "italic")
		l.text = String(lines[i]).to_upper() if (style == "story" and i == 0 and lines.size() > 1) else String(lines[i])
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.autowrap_mode = TextServer.AUTOWRAP_WORD
		l.custom_minimum_size = Vector2(1180, 0)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		l.modulate.a = 0.0
		_card_box.add_child(l)
		_card_items.append({ "node": l, "at": at })
		if style == "title" and not last:
			var r := _mid_rule(300)
			r.modulate.a = 0.0
			_card_box.add_child(r)
			_card_items.append({ "node": r, "at": at + 0.2 })
		at += card_wait(String(lines[i])) if style == "story" else 0.9
	# (with no lines it is only the dark between two places: it holds until the dark is whole)
	_card_full_at = (float(_card_items[-1]["at"]) + Style.t("ceremony")) if not _card_items.is_empty() else Style.t("arrive")
	_card_hint.text = _go_on_words()
	_card_hint.modulate.a = 0.0
	_card_state = "arriving"
	if not card.visible:
		card.visible = true
		_card_black.modulate.a = 0.0
		card.create_tween().tween_property(_card_black, "modulate:a", 1.0, Style.t("arrive"))
	else:
		_card_black.modulate.a = 1.0
	screen.visible = false
	speech.visible = false
	play_ui.visible = false

func _go_on_words() -> String:
	return "A   to go on" if pad else "Enter or click   to go on"

func card_up() -> bool:
	return card.visible and _card_state != ""

## The screen goes dark, `then` is called in the dark, and the dark lifts.
func blackout(then: Callable) -> void:
	show_card([], then, "title", 0.01)

func _card_frame(dt: float) -> void:
	if not card.visible or _card_state == "" or _card_state == "leaving":
		return
	_card_t += dt
	var fade := Style.t("ceremony")
	for it in _card_items:
		var n: CanvasItem = it["node"]
		n.modulate.a = 1.0 if _card_state == "waiting" else clampf((_card_t - float(it["at"])) / fade, 0.0, 1.0)
	if _card_state == "arriving" and _card_t >= _card_full_at:
		_card_state = "waiting"
		_card_t = _card_full_at
	if _card_state == "waiting":
		var since := _card_t - _card_full_at
		if _card_auto > 0.0:
			if since >= _card_auto:
				_card_go()
		else:
			_card_hint.modulate.a = clampf((since - 0.4) / 0.5, 0.0, 1.0) * (0.72 + 0.28 * sin(_card_t * 2.6))

## A key, a click, a button: the rest of the lines at once, and at the next one, on.
func card_press() -> void:
	if _card_state == "arriving" and _card_t > 0.3:
		if _card_auto > 0.0:
			_card_go()
		else:
			_card_state = "waiting"
			_card_t = _card_full_at
	elif _card_state == "waiting" and _card_t > _card_full_at + 0.15:
		_card_go()

func _card_go() -> void:
	if _card_state == "leaving":
		return
	_card_state = "leaving"
	var serial := _card_serial
	var tw := card.create_tween()
	tw.set_parallel(true)
	for it in _card_items:
		tw.tween_property(it["node"], "modulate:a", 0.0, Style.t("leave"))
	tw.tween_property(_card_hint, "modulate:a", 0.0, Style.t("leave"))
	tw.set_parallel(false)
	tw.tween_interval(0.05)
	tw.tween_callback(func():
		var next := _card_next
		_card_next = Callable()
		if next.is_valid():
			next.call()
		if serial != _card_serial:
			return   # another card came up in its place: the dark stays
		_card_state = ""
		var out := card.create_tween()
		out.tween_property(_card_black, "modulate:a", 0.0, Style.t("ceremony"))
		out.tween_callback(func():
			if serial == _card_serial:
				card.visible = false))

# --- Someone speaks ---------------------------------------------------------------------

func _build_speech() -> void:
	speech.set_anchors_preset(Control.PRESET_FULL_RECT)
	speech.mouse_filter = Control.MOUSE_FILTER_STOP
	speech.visible = false
	add_child(speech)
	# the bars of a scene, top and bottom
	for top in [true, false]:
		var b := ColorRect.new()
		b.color = Color(0.012, 0.01, 0.01, 1.0)
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.set_anchors_preset(Control.PRESET_TOP_WIDE if top else Control.PRESET_BOTTOM_WIDE)
		b.grow_vertical = Control.GROW_DIRECTION_END if top else Control.GROW_DIRECTION_BEGIN
		b.custom_minimum_size = Vector2(0, 64)
		speech.add_child(b)
		_speech_bars.append(b)
	var plate := PanelContainer.new()
	plate.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	plate.grow_horizontal = Control.GROW_DIRECTION_BOTH
	plate.grow_vertical = Control.GROW_DIRECTION_BEGIN
	plate.custom_minimum_size = Vector2(900, 190)
	plate.position = Vector2(0, -30)
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var ps := Style.plate(Color(0.045, 0.038, 0.034, 0.94), Style.BRASS, 1, 18)
	ps.border_width_left = 4
	ps.content_margin_left = 26
	ps.content_margin_right = 24
	plate.add_theme_stylebox_override("panel", ps)
	speech.add_child(plate)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.add_child(v)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 14)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(head)
	Style.label(_speech_name, 21, Style.GOLD, "title")
	head.add_child(_speech_name)
	Style.label(_speech_sub, 17, Style.DIM.lerp(Style.FG, 0.25), "italic")
	_speech_sub.size_flags_vertical = Control.SIZE_SHRINK_END
	_speech_sub.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(_speech_sub)
	Style.label(_speech_count, 15, Style.DIM, "ui")
	_speech_count.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(_speech_count)
	_speech_text.bbcode_enabled = true
	_speech_text.fit_content = true
	_speech_text.scroll_active = false
	_speech_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_speech_text.custom_minimum_size = Vector2(850, 92)
	_speech_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	Style.rich(_speech_text, 23, Style.FG, "body")
	v.add_child(_speech_text)
	var foot := HBoxContainer.new()
	foot.alignment = BoxContainer.ALIGNMENT_END
	foot.add_theme_constant_override("separation", 12)
	foot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(foot)
	Style.label(_speech_hint, 17, Style.DIM.lerp(Style.FG, 0.45), "ui")
	_speech_hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_speech_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	foot.add_child(_speech_hint)
	_speech_buttons.add_theme_constant_override("separation", 10)
	foot.add_child(_speech_buttons)

## Someone speaks, a line at a time, across the foot of the screen with the world behind. A
## key, a click or a pad's button brings the whole of a line and then the next; after the
## last line the buttons stand ([words, what it does], the first one chosen).
func show_speech(speaker: String, sub: String, lines: Array, buttons: Array) -> void:
	_speech_name.text = speaker
	_speech_sub.text = sub
	_speech_lines = lines
	_speech_end = buttons
	_speech_i = -1
	for c in _speech_buttons.get_children():
		_speech_buttons.remove_child(c)
		c.queue_free()
	speech.visible = true
	speech.modulate.a = 0.0
	speech.create_tween().tween_property(speech, "modulate:a", 1.0, Style.t("arrive"))
	screen.visible = false
	play_ui.visible = false
	_speech_next()

func speech_up() -> bool:
	return speech.visible

func hide_speech() -> void:
	speech.visible = false

func _speech_next() -> void:
	_speech_i += 1
	_speech_t = 0.0
	var line := String(_speech_lines[_speech_i])
	_speech_text.text = for_device(line)
	_speech_text.visible_ratio = 0.0
	_speech_count.text = "%d / %d" % [_speech_i + 1, _speech_lines.size()]
	if _speech_tween and _speech_tween.is_valid():
		_speech_tween.kill()
	# the words come at the pace of speech, quicker than they are read
	_speech_tween = speech.create_tween()
	_speech_tween.tween_property(_speech_text, "visible_ratio", 1.0, clampf(line.length() / 70.0, 0.4, 2.6))
	_speech_tween.tween_callback(_speech_line_out)
	_speech_hint.text = ""

func _speech_line_out() -> void:
	_speech_text.visible_ratio = 1.0
	if _speech_i >= _speech_lines.size() - 1:
		_speech_hint.text = ""
		if _speech_buttons.get_child_count() == 0:
			for spec in _speech_end:
				var btn := Button.new()
				btn.text = spec[0]
				btn.custom_minimum_size = Vector2(220, 46)
				Style.button(btn, _speech_buttons.get_child_count() == 0, 19)
				btn.pressed.connect(spec[1])
				_speech_buttons.add_child(btn)
				Style.arrive(btn)
			if _speech_buttons.get_child_count() > 0:
				(_speech_buttons.get_child(0) as Button).call_deferred("grab_focus")
	else:
		_speech_hint.text = _go_on_words()

func speech_press() -> void:
	if not speech.visible or _speech_t < 0.2:
		return
	if _speech_text.visible_ratio < 1.0:
		if _speech_tween and _speech_tween.is_valid():
			_speech_tween.kill()
		_speech_line_out()
		_speech_t = 0.0
	elif _speech_i < _speech_lines.size() - 1:
		_speech_next()

func _process(dt: float) -> void:
	_banner_frame()
	_card_frame(dt)
	if speech.visible:
		_speech_t += dt
		if _speech_hint.text != "":
			_speech_hint.modulate.a = 0.72 + 0.28 * sin(Time.get_ticks_msec() / 380.0)

## A card or a speech is up: a key, a click or a pad's button goes on, and nothing under it
## hears the press.
func _input(event: InputEvent) -> void:
	var up_card := card_up()
	var up_speech := speech.visible and not up_card
	if not up_card and not up_speech:
		return
	var go := false
	if event is InputEventKey and event.pressed and not event.echo:
		go = event.physical_keycode in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_E, KEY_ESCAPE]
		if up_speech and event.physical_keycode == KEY_ESCAPE:
			go = false
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		go = true
	elif event is InputEventJoypadButton and event.pressed:
		go = event.button_index in [JOY_BUTTON_A, JOY_BUTTON_X, JOY_BUTTON_START]
	if not go:
		return
	if up_card:
		card_press()
		get_viewport().set_input_as_handled()
	elif _speech_buttons.get_child_count() == 0:
		# (once the buttons stand, a press is theirs)
		speech_press()
		get_viewport().set_input_as_handled()

## The step. Its words stand in the middle top of the screen until they have been read and the
## first thing they ask has been done (or, for someone standing reading, a good while longer);
## then they fold into the plate at the top right, which keeps the step's name, the count, what
## went wrong last, and the key that brings the words back.
func set_prompt(title: String, text: String) -> void:
	var changed := prompt_title.text != title or _prompt_raw != text
	objective_title.text = title
	prompt_title.text = title
	_prompt_raw = text
	prompt_text.text = for_device(text)
	prompt_note.text = ""
	chip_note.text = ""
	chip_note.visible = false
	if title == "":
		prompt.visible = false
		chip.visible = false
		objective_progress.text = ""
		return
	if changed:
		_prompt_acted = false
		_progress_first = "\n"
		_open_prompt(read_seconds(text), read_seconds(text) * 2.0 + 12.0)

func set_prompt_status(note: String, progress: String) -> void:
	# the count has moved: the player is doing what the step asks
	if _progress_first == "\n":
		_progress_first = progress
	elif progress != _progress_first:
		_prompt_acted = true
	objective_progress.text = progress
	objective_progress.visible = progress != ""
	prompt_progress.text = progress
	if note != prompt_note.text:
		prompt_note.text = note
		chip_note.text = note
		chip_note.visible = note != ""

## H: the step's words again, or away if they are up.
func show_prompt_again() -> void:
	if prompt_title.text == "":
		return
	_hint_until = Time.get_ticks_msec() / 1000.0 + 12.0
	if prompt.visible and prompt.modulate.a > 0.9:
		_prompt_acted = true
		_prompt_min_until = 0.0
	else:
		_prompt_acted = true
		_open_prompt(read_seconds(_prompt_raw) + 4.0, read_seconds(_prompt_raw) + 4.0)

## The seconds a person needs to read some words (a little under three words a second, and a
## moment to find the panel).
static func read_seconds(text: String) -> float:
	var words := text.replace("[b]", "").replace("[/b]", "").replace("[i]", "").replace("[/i]", "").split(" ", false).size()
	return clampf(2.5 + words * 0.4, 6.0, 40.0)

func _open_prompt(least: float, most: float) -> void:
	var now := Time.get_ticks_msec() / 1000.0
	_prompt_min_until = now + least
	_prompt_max_until = now + most
	if not prompt.visible and prompt.is_inside_tree():
		prompt.modulate.a = 0.0
		prompt.create_tween().tween_property(prompt, "modulate:a", 1.0, Style.t("quick"))
	else:
		prompt.modulate.a = 1.0
	prompt.visible = true
	chip.visible = false

## The last thing pressed was a key or the mouse (false), or a gamepad's button (true): the
## bar, the hint line and the step's words name what is in the hand.
func set_device(is_pad: bool) -> void:
	if is_pad == pad:
		return
	pad = is_pad
	for sl in SLOTS:
		(slots[sl[0]]["key"] as Label).text = String(PAD_KEYS.get(sl[0], sl[1])) if pad else String(sl[1])
	prompt_text.text = for_device(_prompt_raw)
	_write_hint(_hint_reload, _hint_genius)
	if _card_hint.text != "":
		_card_hint.text = _go_on_words()
	if _speech_hint.text != "":
		_speech_hint.text = _go_on_words()

const PAD_KEYS := { "attack": "X", "block": "RB", "dodge": "A", "technique": "Y", "tech1": "D↓", "tech2": "D→", "tech3": "LT", "stance": "LB", "pattern": "B", "genius": "D←" }
## The words a lesson uses for the keyboard and the mouse, and the gamepad's for the same thing.
const PAD_WORDS := [["Hold right click", "Hold RB"], ["hold right click", "hold RB"], ["tap right click", "tap RB"], ["Tap right click", "Tap RB"], ["right click", "RB"],
	["hold left click", "hold X"], ["Hold left click", "Hold X"], ["Left click", "X"], ["left click", "X"], ["the mouse", "the right stick"], ["mouse", "right stick"],
	["[b]WASD[/b]", "[b]The left stick[/b]"], ["[b]LMB[/b]", "[b]X[/b]"], ["[b]RMB[/b]", "[b]RB[/b]"], ["[b]Space[/b]", "[b]A[/b]"], ["[b]Q[/b]", "[b]Y[/b]"], ["[b]F[/b]", "[b]LB[/b]"],
	["[b]R[/b]", "[b]B[/b]"], ["[b]Tab[/b]", "[b]R3[/b]"], ["[b]E[/b]", "[b]X[/b]"], ["[b]G[/b]", "[b]D-pad left[/b]"], ["[b]1[/b]", "[b]D-pad down[/b]"], ["[b]2[/b]", "[b]D-pad right[/b]"],
	["[b]3[/b]", "[b]LT[/b]"], ["[b]H[/b]", "[b]L3[/b]"], ["[b]N[/b]", "[b]D-pad up[/b]"], ["press R ", "press B "], ["press R:", "press B:"], ["press R.", "press B."], ["press R,", "press B,"]]

func for_device(text: String) -> String:
	if not pad:
		return text
	# (X is the reload on the keys and the strike on the pad: keep the reload's aside while the rest change)
	text = text.replace("[b]X[/b]", "[b]\u0001[/b]")
	for w in PAD_WORDS:
		text = text.replace(w[0], w[1])
	return text.replace("[b]\u0001[/b]", "[b]RT[/b]")

var _hint_reload := false
var _hint_genius := false
func _write_hint(reload: bool, has_genius: bool) -> void:
	_hint_reload = reload
	_hint_genius = has_genius
	var k := func(key: String, what: String) -> String: return "[color=#%s][b]%s[/b][/color] %s" % [GOLD.lightened(0.15).to_html(false), key, what]
	var parts: Array = []
	if pad:
		parts = [k.call("Left stick", "move"), k.call("Right stick", "look"), k.call("R3", "lock on"), k.call("L3", "the step again")]
		if reload:
			parts.append(k.call("RT", "reload"))
		parts.append_array([k.call("D-pad up", "name the foe"), k.call("Start", "menu")])
	else:
		parts = [k.call("WASD", "move"), k.call("Mouse", "look"), k.call("Tab", "lock on"), k.call("H", "the step again")]
		if reload:
			parts.append(k.call("X", "reload"))
		parts.append_array([k.call("N", "name the foe"), k.call("Esc", "menu")])
	hint.text = "[center]%s[/center]" % "      ".join(parts)
	chip_hint.text = ("L3   the step again" if pad else "H   the step again")
	prompt_foot.text = ("L3  puts this away, and brings it back" if pad else "H  puts this away, and brings it back")

func update_play(f: Fight, timer_text: String, score_text: String, show_target: bool) -> void:
	var dt := get_process_delta_time()
	_play_time += dt
	_name_label.text = _hero_name
	_shape_label.text = _hero_sub
	var hp_max := float(Data.room["player"]["health"])
	hp_bar.max_value = hp_max
	hp_ghost.max_value = hp_max
	if _last_hp < 0.0:
		hp_ghost.value = f.p_hp
	elif f.p_hp < _last_hp - 0.01:
		_hp_ghost_hold = 0.5
		_hurt_flash = 1.0
	_last_hp = f.p_hp
	hp_bar.value = f.p_hp
	_hp_ghost_hold -= dt
	if _hp_ghost_hold <= 0.0:
		hp_ghost.value = move_toward(hp_ghost.value, f.p_hp, dt * hp_max * 0.6)
	hp_ghost.value = maxf(hp_ghost.value, f.p_hp)
	hp_text.text = "%d / %d" % [roundi(f.p_hp), int(hp_max)]
	_hurt_flash = maxf(0.0, _hurt_flash - dt * 3.0)
	(_frame.get_theme_stylebox("panel") as StyleBoxFlat).border_color = Style.BRASS_DIM.lerp(Style.EMBER, _hurt_flash)
	will_bar.value = f.p_will
	for i in mini(f.allies.size(), _party_rows.size()):
		var al: Dictionary = f.allies[i]
		var pr: Dictionary = _party_rows[i]
		(pr["label"] as Label).text = String(al["name"]) + ("  ·  DOWN" if al["down"] else "")
		(pr["label"] as Label).add_theme_color_override("font_color", Style.EMBER if al["down"] else Style.DIM)
		(pr["bar"] as ProgressBar).max_value = float(al["hp_max"])
		(pr["bar"] as ProgressBar).value = float(al["hp"])
	if f.genius:
		var gn: Genius = f.genius
		_g_label.text = gn.form_name() if gn.name == "" or gn.name == gn.form_name() else "%s  ·  %s" % [gn.name, gn.form_name()]
		g_bar.max_value = f.g_will_max
		g_bar.value = f.g_will
		# what it is doing, by its type: a companion's role and order (on Free, what it chose
		# and why), a weapon in the hand or at the shoulder, an item ready or coming round; and
		# the move it is making
		var key: Dictionary = f.genius_key()
		var ord := gn.order.to_upper()
		if gn.order == "free":
			ord = "FREE: %s%s" % [f.g_order.to_upper(), ("  (%s)" % f.g_free_why) if f.g_free_why != "" else ""]
		match f.g_type:
			"weapon":
				ord = "IN YOUR HAND" if f.g_in_hand else ("AT YOUR SHOULDER" if key["ready"] else "RESTING  %ds" % ceili(float(key["left"])))
			"defense", "ritual":
				ord = String(f.g_item.get("wornAs", "")).to_upper()
				if key["active"]:
					ord += "   ·   %s" % String(f.g_item["use"]["name"]).to_upper()
				elif not key["ready"]:
					ord += "   ·   %ds" % ceili(float(key["left"])) if float(key["left"]) > 0.0 else "   ·   SPENT"
			_:
				if not f.g_role.is_empty():
					ord = "%s   ·   %s" % [String(f.g_role["name"]).to_upper(), ord]
		if f.now < f.g_move_until and f.g_move_now != "" and not key["active"]:
			ord += "   ·   %s" % f.g_move_now
		_g_order.text = "FALLEN" if gn.fallen else "%s   [G]" % ord
		_g_order.add_theme_color_override("font_color", Style.EMBER if gn.fallen else GOLD)
		# its key on the ability bar
		(slots["genius"]["name"] as Label).text = String(key["label"])
		var cost := ""
		match f.g_type:
			"weapon": cost = "%d a blow, its Will" % roundi(float(f.g_weapon.get("willPerBlow", 0.0))) if f.g_in_hand else "its Will %d" % roundi(f.g_will)
			"defense", "ritual": cost = "%d of its Will" % roundi(float(f.g_item["use"].get("will", 0.0)))
			_: cost = String(f.g_role.get("name", " "))
		(slots["genius"]["cost"] as Label).text = cost
		var total := maxf(0.01, float(f.g_item.get("use", {}).get("wait", 1.0)) * f.g_twait) if f.g_type in ["defense", "ritual"] else maxf(0.01, float(key["left"]))
		_set_slot("genius", float(key["left"]) / total if float(key["left"]) > 0.0 else 0.0, key["ready"] and not gn.fallen, key["active"], Color(0, 0, 0, 0), float(key["left"]))
	will_text.text = "Will %d" % roundi(f.p_will)
	var low := f.p_hp <= hp_max * 0.3 and f.p_state != "down"
	(hp_bar.get_theme_stylebox("fill") as StyleBoxFlat).bg_color = RED.lerp(Color(1, 0.42, 0.3), (0.5 + 0.5 * sin(_play_time * 8.0)) * 0.5) if low else RED
	var st: Array = []
	if f.p_stance: st.append(String(f.kit["stance"]["name"]).to_upper())
	if f.p_fainted: st.append("FAINTED")
	if f.p_field_open: st.append("FIELD OPEN" if f.stage < 3 else "STAGE 3")
	if f.p_combo_count > 2: st.append("%d HITS" % f.p_combo_count)
	status.text = "  ·  ".join(st)
	_sigil.color = _accent.lightened(0.35 * (0.5 + 0.5 * sin(_play_time * 5.0))) if f.p_stance else _accent

	target.visible = show_target and f.w_state not in ["down", "absent"]
	target_name.text = String(f.beast["name"]).to_upper()
	var more := f.foes_alive()
	target_sub.text = "%s  ·  %s%s" % [String(f.w_shape).capitalize(), f.beast.get("title", "first molt"), ("  ·  +%d in the pack" % more) if more > 0 else ""]
	var t_max := float(f.beast["health"])
	target_bar.max_value = t_max
	target_ghost.max_value = t_max
	if _last_t < 0.0 or f.w_hp > _last_t + 0.01:
		target_ghost.value = f.w_hp
	elif f.w_hp < _last_t - 0.01:
		_t_ghost_hold = 0.45
	_last_t = f.w_hp
	target_bar.value = f.w_hp
	_t_ghost_hold -= dt
	if _t_ghost_hold <= 0.0:
		target_ghost.value = move_toward(target_ghost.value, f.w_hp, dt * t_max * 0.5)
	target_ghost.value = maxf(target_ghost.value, f.w_hp)
	target_bar.get_parent().visible = t_max < 50000
	var stag := f.w_state == "stagger"
	(target_bar.get_theme_stylebox("fill") as StyleBoxFlat).bg_color = Style.GOLD if stag else RED
	target_pips.text = "STAGGERED" if stag else ((("BREAK  %d / %d" % [f.w_break, int(Data.room["break"]["needed"])]) if f.breaks_beast() else "") + (("   ·   OPEN: strike now" if f.guard_open() and f.w_state not in ["down", "absent"] else "   ·   GUARDED: see its strike out, then answer") if f.beast.has("guard") else ""))
	timer_label.text = timer_text
	score_label.text = score_text
	var now_s := Time.get_ticks_msec() / 1000.0
	hint.modulate.a = maxf(clampf(1.0 - (_play_time - 20.0) / 3.0, 0.0, 1.0), clampf(_hint_until - now_s, 0.0, 1.0))
	hint.visible = hint.modulate.a > 0.01
	if prompt.visible:
		# read, and begun: fold. Never begun: fold all the same, after a good while.
		var until := _prompt_min_until if _prompt_acted else _prompt_max_until
		var left := until - now_s
		if left <= 0.0:
			prompt.visible = false
		elif left < 0.4:
			prompt.modulate.a = minf(prompt.modulate.a, left / 0.4)
	var folded := prompt_title.text != "" and not prompt.visible
	if folded and not chip.visible:
		chip.modulate.a = 0.0
		chip.create_tween().tween_property(chip, "modulate:a", 1.0, Style.t("arrive"))
	chip.visible = folded

	# Ability bar state (a lesson can lock some of it).
	_fight_allowed = f.allowed
	var tech: Dictionary = f.tech
	var cd_left := maxf(0.0, float(f.p_cooldowns.get(tech["id"], 0.0)) - f.now)
	_set_slot("technique", cd_left / float(tech["cooldown"]), f.p_will >= float(tech["will"]) and not f.p_fainted, false, Color(0, 0, 0, 0), cd_left)
	for i in f.extra_techs.size():
		var et: Dictionary = f.extra_techs[i]
		var left := maxf(0.0, float(f.p_cooldowns.get(et["id"], 0.0)) - f.now)
		_set_slot("tech%d" % (i + 1), left / float(et["cooldown"]), f.p_will >= float(et["will"]) and not f.p_fainted, f.p_state == "technique" and f.p_technique == et["id"], Color(0, 0, 0, 0), left)
	_set_slot("dodge", 0.0, f.p_will >= float(Data.room["dodge"]["will"]), f.p_state == "dodge")
	_set_slot("block", 0.0, not f.p_fainted, f.p_block_held)
	# the weapon in the hand may have changed (a weapon genius taken up or let go)
	(slots["attack"]["name"] as Label).text = ("Draw" if f.style.has("draw") else "Shot") if f.ranged else "Strike"
	if f.ranged and f.p_ammo_max > 0:
		_set_slot("attack", (1.0 - f.p_timer / maxf(0.01, f.p_reload_t)) if f.p_state == "reload" else 0.0, f.p_ammo > 0 or f.p_state == "reload", f.p_state == "attack", Color(0, 0, 0, 0), 0.0)
		(slots["attack"]["cost"] as Label).text = ("reloading  (X)" if f.p_state == "reload" else ("%d / %d%s" % [f.p_ammo, f.p_ammo_max, "" if f.p_ammo > 0 else "  ·  X"]))
		(slots["attack"]["cost"] as Label).add_theme_color_override("font_color", Style.EMBER if f.p_ammo == 0 and f.p_state != "reload" else BLUE.lightened(0.2))
	elif f.ranged and f.style.has("draw"):
		var charge := clampf(f.p_draw / f.draw_seconds(), 0.0, 1.0) if f.p_state == "draw" else 0.0
		_set_slot("attack", 0.0, true, f.p_state in ["attack", "draw"], Color(GOLD, charge) if charge > 0.0 else Color(0, 0, 0, 0), 0.0)
		(slots["attack"]["cost"] as Label).text = ("drawn %d%%" % int(charge * 100)) if f.p_state == "draw" else "hold to draw"
	else:
		_set_slot("attack", 0.0, true, f.p_state == "attack")
		(slots["attack"]["cost"] as Label).text = "its Will for rounds" if f.g_in_hand and f.ranged else " "
	var ready := f.pattern_ready()
	_set_slot("pattern", 0.0 if ready or f.p_state == "pattern" else 1.0, ready, f.p_state == "pattern", Color(GOLD, 0.5 + 0.5 * sin(Time.get_ticks_msec() / 110.0)) if ready else Color(0, 0, 0, 0))
	var pname: String = f.pattern["name"]
	slots["pattern"]["name"].text = "LOST" if f.pattern_lost else pname
	_set_slot("stance", 0.0, not f.p_fainted and not f.p_stance_locked, f.p_stance)
	if f.p_state == "pattern" and not f.chain.is_empty():
		var n: int = f.chain["cues"].size()
		pattern_banner.text = "%s   x%s\nstrike as the gold ring closes   %d / %d" % [pname.to_upper(), str(f.chain["multiplier"]), int(f.chain["next"]), n]
	elif f.now <= f.breach_armed_until:
		pattern_banner.text = "A BAR FORBIDS THIS: press R again to break your Term" + ("  (sworn: lost for good)" if f.pattern["sworn"] else "  (lost for a season)")
	elif ready and (f.allowed.is_empty() or "pattern" in f.allowed):
		pattern_banner.text = "%s is ready: press R" % pname
	else:
		pattern_banner.text = ""

const SLOT_ACTION := { "attack": "attack", "block": "block-down", "dodge": "dodge", "technique": "technique", "stance": "stance", "pattern": "pattern", "tech1": "tech1", "tech2": "tech2", "tech3": "tech3", "genius": "order" }
var _fight_allowed: Array = []

func _set_slot(id: String, cooldown: float, usable: bool, active: bool, glow := Color(0, 0, 0, 0), seconds := 0.0) -> void:
	if not _fight_allowed.is_empty() and SLOT_ACTION[id] not in _fight_allowed:
		usable = false
		glow = Color(0, 0, 0, 0)
	var s: Dictionary = slots[id]
	var cd: ColorRect = s["cd"]
	var k := clampf(cooldown, 0.0, 1.0)
	cd.size = Vector2(_slot_w - 4, (SLOT_H - 4) * k)
	cd.position = Vector2(2, 2 + (SLOT_H - 4) - cd.size.y)
	(s["cd_text"] as Label).text = ("%d" % ceili(seconds)) if seconds > 0.05 else ""
	# Only rebuild the plate when the slot's look changes.
	var state := "active" if active else (("glow%.1f" % glow.a) if glow.a > 0.0 else ("on" if usable else "off"))
	if state != s["state"]:
		s["state"] = state
		var box: StyleBoxFlat
		if active:
			box = _slot_box(Color(0.3, 0.2, 0.08, 0.94), Style.BRASS_HI, 2)
		elif glow.a > 0.0:
			box = _slot_box(Color(0.12 + 0.18 * glow.a, 0.09 + 0.12 * glow.a, 0.04, 0.92), Style.BRASS_DIM.lerp(Style.GOLD, glow.a), 2)
			box.shadow_color = Color(Style.GOLD, 0.35 * glow.a)
			box.shadow_size = 14
		else:
			box = _slot_box(Color(0.05, 0.042, 0.038, 0.86 if usable else 0.7), Style.BRASS_DIM if usable else Color(0.22, 0.19, 0.16))
		(s["panel"] as PanelContainer).add_theme_stylebox_override("panel", box)
	(s["key"] as Label).add_theme_color_override("font_color", FG if usable else Color(0.5, 0.45, 0.4))
	(s["name"] as Label).add_theme_color_override("font_color", DIM if usable else Color(0.42, 0.38, 0.34))
