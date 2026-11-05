## The on-screen layer: the Anchor's frame, the target frame, the ability bar, the Pattern's
## chain, the tutorial box, menus and results.
class_name Hud
extends CanvasLayer

const BG := Color(0.05, 0.045, 0.04, 0.82)
const FG := Color(0.94, 0.9, 0.83)
const DIM := Color(0.62, 0.58, 0.52)
const ACCENT := Color(0.95, 0.72, 0.3)
const RED := Color(0.86, 0.24, 0.2)
const BLUE := Color(0.45, 0.7, 0.98)
const GOLD := Color(1.0, 0.8, 0.35)
const EDGE := Color(0.32, 0.27, 0.21)

var play_ui := Control.new()
var hp_bar := ProgressBar.new()
var will_bar := ProgressBar.new()
var hp_text := Label.new()
var will_text := Label.new()
var status := Label.new()
var target := VBoxContainer.new()
var target_name := Label.new()
var target_bar := ProgressBar.new()
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
var hint := Label.new()
var screen := ColorRect.new()
var screen_box := VBoxContainer.new()

const SLOTS := [
	["attack", "LMB", "Strike", ""],
	["block", "RMB", "Block · Parry", ""],
	["dodge", "Space", "Dodge", "8"],
	["technique", "Q", "Ground Strike", "18"],
	["stance", "F", "Anchor Stance", "2/s"],
	["pattern", "R", "Pattern", ""],
]

func _ready() -> void:
	layer = 10
	play_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	play_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(play_ui)

	# The Anchor's frame.
	var me := VBoxContainer.new()
	me.position = Vector2(28, 22)
	me.custom_minimum_size = Vector2(380, 0)
	me.add_theme_constant_override("separation", 4)
	play_ui.add_child(me)
	var name_l := Label.new()
	_label(name_l, 18, FG)
	name_l.text = "ANCHOR  ·  Marshal"
	me.add_child(name_l)
	for pair in [[hp_bar, hp_text, RED, 18], [will_bar, will_text, BLUE, 12]]:
		var holder := Control.new()
		holder.custom_minimum_size = Vector2(380, pair[3])
		var b: ProgressBar = pair[0]
		_bar(b, pair[2])
		b.set_anchors_preset(Control.PRESET_FULL_RECT)
		holder.add_child(b)
		var t: Label = pair[1]
		_label(t, 12, FG)
		t.set_anchors_preset(Control.PRESET_FULL_RECT)
		t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		t.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		holder.add_child(t)
		me.add_child(holder)
	_label(status, 14, ACCENT)
	me.add_child(status)

	# The target frame.
	target.set_anchors_preset(Control.PRESET_CENTER_TOP)
	target.position = Vector2(-220, 20)
	target.custom_minimum_size = Vector2(440, 0)
	target.add_theme_constant_override("separation", 3)
	_label(target_name, 18, FG)
	target_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	target.add_child(target_name)
	_bar(target_bar, RED)
	target_bar.custom_minimum_size = Vector2(440, 14)
	target.add_child(target_bar)
	_label(target_pips, 18, GOLD)
	target_pips.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	target.add_child(target_pips)
	play_ui.add_child(target)

	var right := VBoxContainer.new()
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	right.position = Vector2(-300, 20)
	right.custom_minimum_size = Vector2(272, 0)
	_label(timer_label, 34, FG)
	timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(timer_label)
	_label(score_label, 15, DIM)
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(score_label)
	play_ui.add_child(right)

	# The ability bar.
	bar.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	bar.add_theme_constant_override("separation", 8)
	bar.position = Vector2(-((96 + 8) * SLOTS.size()) / 2.0, -118)
	for s in SLOTS:
		bar.add_child(_slot(s))
	play_ui.add_child(bar)

	_label(pattern_banner, 26, GOLD)
	pattern_banner.set_anchors_preset(Control.PRESET_CENTER)
	pattern_banner.position = Vector2(-400, 150)
	pattern_banner.custom_minimum_size = Vector2(800, 0)
	pattern_banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	play_ui.add_child(pattern_banner)

	_label(hint, 13, DIM)
	hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	hint.position = Vector2(-450, -28)
	hint.custom_minimum_size = Vector2(900, 0)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.text = "WASD move  ·  mouse look  ·  Tab lock-on  ·  N name the foe  ·  Esc menu     |     pad: X strike · RB block · A dodge · Y Ground Strike · LB stance · B Pattern · Up name"
	play_ui.add_child(hint)

	# The tutorial box.
	prompt.set_anchors_preset(Control.PRESET_CENTER_TOP)
	prompt.custom_minimum_size = Vector2(720, 0)
	prompt.position = Vector2(-360, 104)
	prompt.add_theme_stylebox_override("panel", _panel(BG))
	var pv := VBoxContainer.new()
	prompt.add_child(pv)
	_label(prompt_title, 19, ACCENT)
	pv.add_child(prompt_title)
	prompt_text.bbcode_enabled = true
	prompt_text.fit_content = true
	prompt_text.scroll_active = false
	prompt_text.custom_minimum_size = Vector2(688, 0)
	prompt_text.add_theme_font_size_override("normal_font_size", 16)
	prompt_text.add_theme_font_size_override("bold_font_size", 16)
	prompt_text.add_theme_color_override("default_color", FG)
	pv.add_child(prompt_text)
	var row := HBoxContainer.new()
	_label(prompt_note, 14, DIM)
	prompt_note.autowrap_mode = TextServer.AUTOWRAP_WORD
	prompt_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(prompt_note)
	_label(prompt_progress, 14, ACCENT)
	row.add_child(prompt_progress)
	pv.add_child(row)
	play_ui.add_child(prompt)

	# Menus and results.
	screen.color = Color(0.03, 0.025, 0.025, 0.9)
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(screen)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen.add_child(center)
	screen_box.custom_minimum_size = Vector2(620, 0)
	screen_box.add_theme_constant_override("separation", 10)
	center.add_child(screen_box)

func _slot(s: Array) -> PanelContainer:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(96, 84)
	p.add_theme_stylebox_override("panel", _panel(Color(0.06, 0.05, 0.045, 0.85)))
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 0)
	p.add_child(v)
	var key := Label.new()
	_label(key, 20, FG)
	key.text = s[1]
	key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(key)
	var name := Label.new()
	_label(name, 12, DIM)
	name.text = s[2]
	name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(name)
	var cost := Label.new()
	_label(cost, 11, BLUE)
	cost.text = ("%s Will" % s[3]) if s[3] != "" else " "
	cost.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(cost)
	var cd := ColorRect.new()
	cd.color = Color(0, 0, 0, 0.6)
	cd.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cd.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	p.add_child(cd)
	slots[s[0]] = { "panel": p, "key": key, "name": name, "cd": cd }
	return p

func _label(l: Label, size: int, color: Color) -> void:
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 5)

func _bar(b: ProgressBar, color: Color) -> void:
	b.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0, 0, 0, 0.65)
	bg.border_color = EDGE
	bg.set_border_width_all(1)
	bg.set_corner_radius_all(2)
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	fill.set_corner_radius_all(2)
	b.add_theme_stylebox_override("background", bg)
	b.add_theme_stylebox_override("fill", fill)

func _panel(color: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.border_color = EDGE
	s.set_border_width_all(1)
	s.set_corner_radius_all(3)
	s.set_content_margin_all(12)
	return s

# --- Screens ----------------------------------------------------------------

func show_screen(title: String, subtitle: String, body: String, buttons: Array) -> void:
	for c in screen_box.get_children():
		c.queue_free()
	var t := Label.new()
	_label(t, 52, ACCENT)
	t.text = title
	screen_box.add_child(t)
	if subtitle != "":
		var s := Label.new()
		_label(s, 19, DIM)
		s.text = subtitle
		s.autowrap_mode = TextServer.AUTOWRAP_WORD
		screen_box.add_child(s)
	if body != "":
		var b := RichTextLabel.new()
		b.bbcode_enabled = true
		b.fit_content = true
		b.scroll_active = false
		b.custom_minimum_size = Vector2(620, 0)
		b.add_theme_font_size_override("normal_font_size", 17)
		b.add_theme_color_override("default_color", FG)
		b.text = body
		screen_box.add_child(b)
	var first: Button = null
	for spec in buttons:
		var btn := Button.new()
		btn.text = "   " + spec[0]
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.add_theme_font_size_override("font_size", 19)
		btn.custom_minimum_size = Vector2(0, 48)
		btn.add_theme_stylebox_override("normal", _panel(Color(0.08, 0.07, 0.06, 0.9)))
		btn.add_theme_stylebox_override("hover", _panel(Color(0.16, 0.12, 0.08, 0.95)))
		btn.add_theme_stylebox_override("focus", _panel(Color(0.2, 0.14, 0.08, 0.95)))
		btn.add_theme_stylebox_override("pressed", _panel(Color(0.24, 0.17, 0.09, 0.95)))
		btn.pressed.connect(spec[1])
		screen_box.add_child(btn)
		if first == null:
			first = btn
	screen.visible = true
	play_ui.visible = false
	if first:
		first.call_deferred("grab_focus")

func hide_screen() -> void:
	screen.visible = false
	play_ui.visible = true

func set_prompt(title: String, text: String) -> void:
	prompt.visible = title != ""
	prompt_title.text = title
	prompt_text.text = text

func set_prompt_status(note: String, progress: String) -> void:
	prompt_note.text = note
	prompt_progress.text = progress

func update_play(f: Fight, timer_text: String, score_text: String, show_target: bool) -> void:
	hp_bar.max_value = float(Data.room["player"]["health"])
	hp_bar.value = f.p_hp
	hp_text.text = "%d / %d" % [roundi(f.p_hp), int(hp_bar.max_value)]
	will_bar.value = f.p_will
	will_text.text = "Will %d" % roundi(f.p_will)
	var st: Array = []
	if f.p_stance: st.append("ANCHOR STANCE")
	if f.p_fainted: st.append("FAINTED")
	if f.p_combo_count > 2: st.append("%d hits" % f.p_combo_count)
	status.text = "  ·  ".join(st)
	target.visible = show_target and f.w_state not in ["down", "absent"]
	target_name.text = "%s  ·  %s  ·  first molt" % [f.beast["name"], String(f.beast["shape"]).capitalize()]
	target_bar.max_value = float(f.beast["health"])
	target_bar.value = f.w_hp
	target_bar.visible = float(f.beast["health"]) < 50000
	target_pips.text = ("BREAK  %d / %d" % [f.w_break, int(Data.room["break"]["needed"])]) if f.breaks_beast() else ""
	timer_label.text = timer_text
	score_label.text = score_text
	# Ability bar state.
	var tech: Dictionary = f.tech
	var cd_left := maxf(0.0, float(f.p_cooldowns.get(tech["id"], 0.0)) - f.now)
	_set_slot("technique", cd_left / float(tech["cooldown"]), f.p_will >= float(tech["will"]) and not f.p_fainted, false)
	_set_slot("dodge", 0.0, f.p_will >= float(Data.room["dodge"]["will"]), f.p_state == "dodge")
	_set_slot("block", 0.0, not f.p_fainted, f.p_block_held)
	_set_slot("stance", 0.0, not f.p_fainted, f.p_stance)
	_set_slot("attack", 0.0, true, f.p_state == "attack")
	var ready := f.pattern_ready()
	_set_slot("pattern", 0.0 if ready else 1.0, ready, f.p_state == "pattern", Color(GOLD, 0.35 + 0.35 * sin(Time.get_ticks_msec() / 90.0)) if ready else Color(0, 0, 0, 0))
	var pname: String = f.pattern["name"]
	slots["pattern"]["name"].text = "LOST" if f.pattern_lost else (pname if pname.length() <= 15 else pname.substr(0, 14) + ".")
	_set_slot("stance", 0.0, not f.p_fainted and not f.p_stance_locked, f.p_stance)
	if f.p_state == "pattern" and not f.chain.is_empty():
		var n: int = f.chain["cues"].size()
		pattern_banner.text = "%s  x%s\nstrike as the gold ring closes     %d / %d" % [pname.to_upper(), str(f.chain["multiplier"]), int(f.chain["next"]), n]
	elif f.now <= f.breach_armed_until:
		pattern_banner.text = "A BAR FORBIDS THIS: press R again to break your Term" + ("  (sworn: lost for good)" if f.pattern["sworn"] else "  (lost for a season)")
	elif ready:
		pattern_banner.text = "%s is ready: press R" % pname
	else:
		pattern_banner.text = ""

func _set_slot(id: String, cooldown: float, usable: bool, active: bool, glow := Color(0, 0, 0, 0)) -> void:
	var s: Dictionary = slots[id]
	var cd: ColorRect = s["cd"]
	cd.size = Vector2(96, 84 * clampf(cooldown, 0.0, 1.0))
	cd.position = Vector2(0, 84 - cd.size.y)
	var p: PanelContainer = s["panel"]
	var col := Color(0.06, 0.05, 0.045, 0.85)
	if active: col = Color(0.32, 0.22, 0.08, 0.92)
	elif glow.a > 0.0: col = Color(glow, glow.a)
	p.add_theme_stylebox_override("panel", _panel(col))
	(s["key"] as Label).add_theme_color_override("font_color", FG if usable else Color(0.5, 0.45, 0.4))
