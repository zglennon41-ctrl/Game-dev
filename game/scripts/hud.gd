## The on-screen layer: the hero's frame, the target frame, the ability bar, the Pattern's
## chain, the tutorial box, menus and results. Built on Style (lamplight gothic).
class_name Hud
extends CanvasLayer

const FG := Style.FG
const DIM := Style.DIM
const ACCENT := Style.GOLD
const RED := Style.BLOOD
const BLUE := Style.WILL
const GOLD := Style.GOLD

const SLOT_W := 72.0
const SLOT_H := 62.0

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
var hint := Label.new()
var objective_title := Label.new()
var objective_progress := Label.new()
var _toast_until := 0.0
var screen := Control.new()
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
	Style.label(_shape_label, 12, DIM, "ui")
	_shape_label.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(_shape_label)
	me.add_child(_meter(hp_bar, hp_ghost, hp_text, RED, 14, 310))
	me.add_child(_meter(will_bar, null, null, BLUE, 6, 310))
	var srow := HBoxContainer.new()
	me.add_child(srow)
	Style.label(status, 12, ACCENT, "ui_bold", 3)
	status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	srow.add_child(status)
	Style.label(will_text, 11, BLUE.lightened(0.3), "ui", 3)
	srow.add_child(will_text)
	# The genius: its name and form, its Will, its order (G changes it).
	_g_row.add_theme_constant_override("separation", 3)
	var grow := HBoxContainer.new()
	grow.add_theme_constant_override("separation", 10)
	_g_row.add_child(grow)
	Style.label(_g_label, 13, FG, "title", 3)
	_g_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grow.add_child(_g_label)
	Style.label(_g_order, 11, GOLD, "ui_bold", 3)
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
		Style.label(l, 11, Style.DIM, "ui", 3)
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
	Style.label(target_sub, 12, DIM, "ui", 3)
	target_sub.size_flags_vertical = Control.SIZE_SHRINK_END
	trow.add_child(target_sub)
	tv.add_child(_meter(target_bar, target_ghost, null, RED, 10, 400))
	Style.label(target_pips, 13, GOLD, "ui_bold", 4)
	target_pips.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tv.add_child(target_pips)
	play_ui.add_child(target)

	var right := VBoxContainer.new()
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	right.position = Vector2(-300, 18)
	right.custom_minimum_size = Vector2(272, 0)
	right.add_theme_constant_override("separation", 0)
	Style.label(timer_label, 36, FG, "title", 5)
	timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(timer_label)
	Style.label(score_label, 15, DIM, "italic", 4)
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(score_label)
	var ogap := Control.new()
	ogap.custom_minimum_size = Vector2(0, 6)
	right.add_child(ogap)
	Style.label(objective_title, 15, ACCENT, "title", 4)
	objective_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	objective_title.autowrap_mode = TextServer.AUTOWRAP_WORD
	right.add_child(objective_title)
	Style.label(objective_progress, 13, DIM, "ui", 3)
	objective_progress.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	objective_progress.autowrap_mode = TextServer.AUTOWRAP_WORD
	right.add_child(objective_progress)
	play_ui.add_child(right)

	# The ability bar.
	bar.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	bar.add_theme_constant_override("separation", 8)
	bar.position = Vector2(-((SLOT_W + 8) * SLOTS.size() - 8) / 2.0, -SLOT_H - 26)
	for s in SLOTS:
		bar.add_child(_slot(s))
	play_ui.add_child(bar)

	Style.label(pattern_banner, 20, GOLD, "title", 5)
	# Above the ability bar, clear of the gold ring at the hero's feet.
	pattern_banner.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	pattern_banner.grow_vertical = Control.GROW_DIRECTION_BEGIN
	pattern_banner.position = Vector2(-450, -SLOT_H - 96)
	pattern_banner.custom_minimum_size = Vector2(900, 0)
	pattern_banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	play_ui.add_child(pattern_banner)

	Style.label(hint, 12, DIM, "ui", 3)
	hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	hint.position = Vector2(-500, -20)
	hint.custom_minimum_size = Vector2(1000, 0)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.text = "WASD move  ·  mouse look  ·  Tab lock-on  ·  H the step again  ·  N name the foe  ·  Esc menu      pad: X strike · RB block · A dodge · Y technique · LB stance · B Pattern"
	play_ui.add_child(hint)

	# The tutorial box: a plate with a brass edge down its left side.
	prompt.set_anchors_preset(Control.PRESET_CENTER_TOP)
	prompt.custom_minimum_size = Vector2(600, 0)
	prompt.position = Vector2(-300, 92)
	prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var ps := Style.plate(Color(0.045, 0.038, 0.034, 0.9), Style.BRASS, 1, 14)
	ps.border_width_left = 4
	ps.content_margin_left = 22
	prompt.add_theme_stylebox_override("panel", ps)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 6)
	prompt.add_child(pv)
	Style.label(prompt_title, 18, ACCENT, "title")
	pv.add_child(prompt_title)
	prompt_text.bbcode_enabled = true
	prompt_text.fit_content = true
	prompt_text.scroll_active = false
	prompt_text.custom_minimum_size = Vector2(560, 0)
	Style.rich(prompt_text, 17, FG, "body")
	pv.add_child(prompt_text)
	var row := HBoxContainer.new()
	Style.label(prompt_note, 15, DIM, "italic")
	prompt_note.autowrap_mode = TextServer.AUTOWRAP_WORD
	prompt_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(prompt_note)
	Style.label(prompt_progress, 15, ACCENT, "ui_bold")
	row.add_child(prompt_progress)
	pv.add_child(row)
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
	screen_box.custom_minimum_size = Vector2(640, 0)
	screen_box.add_theme_constant_override("separation", 10)
	_center.add_child(screen_box)

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

func _slot(s: Array) -> PanelContainer:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(SLOT_W, SLOT_H)
	p.add_theme_stylebox_override("panel", _slot_box(Color(0.05, 0.042, 0.038, 0.86), Style.BRASS_DIM))
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", -1)
	p.add_child(v)
	var key := Label.new()
	Style.label(key, 16, FG, "title", 4)
	key.text = s[1]
	key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(key)
	var name := Label.new()
	Style.label(name, 11, DIM, "ui", 3)
	name.text = s[2]
	name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name.clip_text = true
	name.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name.custom_minimum_size = Vector2(SLOT_W - 10, 0)
	v.add_child(name)
	var cost := Label.new()
	Style.label(cost, 10, BLUE.lightened(0.2), "ui", 3)
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
	(slots["attack"]["name"] as Label).text = "Shot" if f.ranged else "Strike"
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
	for s in slots.values():
		if (s["panel"] as PanelContainer).visible:
			visible_n += 1
	bar.position = Vector2(-((SLOT_W + 8) * visible_n - 8) / 2.0, -SLOT_H - 26)
	_hero_name = hero_name if hero_name != "" else "Anchor"
	_hero_sub = String(f.player_shape).capitalize()
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
	var is_title := layout == "title"
	screen_box.get_parent().remove_child(screen_box)
	(_left if is_title else _center).add_child(screen_box)
	screen_box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	screen_box.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	screen_box.custom_minimum_size = Vector2(560 if is_title else 660, 0)
	(_veil.material as ShaderMaterial).set_shader_parameter("mode", 1.0 if is_title else 0.0)
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
	if body != "":
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
	for spec in buttons:
		var btn := Button.new()
		btn.text = spec[0]
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.autowrap_mode = TextServer.AUTOWRAP_WORD
		btn.custom_minimum_size = Vector2(0, 50)
		Style.button(btn, false, 19)
		btn.pressed.connect(spec[1])
		screen_box.add_child(btn)
		items.append(btn)
		if first == null:
			first = btn
	screen.visible = true
	play_ui.visible = false
	_veil.modulate.a = 0.0
	screen.create_tween().tween_property(_veil, "modulate:a", 1.0, 0.4)
	for i in items.size():
		var it: CanvasItem = items[i]
		it.modulate.a = 0.0
		it.create_tween().tween_property(it, "modulate:a", 1.0, 0.4).set_delay(0.06 * i).set_trans(Tween.TRANS_SINE)
	if first:
		first.call_deferred("grab_focus")

func hide_screen() -> void:
	screen.visible = false
	play_ui.visible = true
	_play_time = 0.0

## The step: its title stays as the objective line (top right); its words show as a toast for
## a while and fade, so the fight's middle stays clear.
func set_prompt(title: String, text: String) -> void:
	var changed := prompt_title.text != title or prompt_text.text != text
	objective_title.text = title
	prompt_title.text = title
	prompt_text.text = text
	prompt_note.text = ""
	if title == "":
		prompt.visible = false
		objective_progress.text = ""
		return
	if changed:
		_toast(8.0)

func set_prompt_status(note: String, progress: String) -> void:
	objective_progress.text = progress
	prompt_progress.text = progress
	if note != prompt_note.text:
		prompt_note.text = note
		if note != "" and not note.ends_with("s left."):
			_toast(4.0)

func show_prompt_again() -> void:
	if prompt_title.text != "":
		_toast(8.0)

func _toast(seconds: float) -> void:
	_toast_until = Time.get_ticks_msec() / 1000.0 + seconds
	if not prompt.visible and prompt.is_inside_tree():
		prompt.modulate.a = 0.0
		prompt.create_tween().tween_property(prompt, "modulate:a", 1.0, 0.25)
	prompt.visible = true

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
		_g_order.text = "FALLEN" if gn.fallen else "%s   [G]" % gn.order.to_upper()
		_g_order.add_theme_color_override("font_color", Style.EMBER if gn.fallen else GOLD)
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
	target_pips.text = "STAGGERED" if stag else (("BREAK  %d / %d" % [f.w_break, int(Data.room["break"]["needed"])]) if f.breaks_beast() else "")
	timer_label.text = timer_text
	score_label.text = score_text
	hint.modulate.a = clampf(1.0 - (_play_time - 14.0) / 3.0, 0.0, 1.0)
	hint.visible = hint.modulate.a > 0.01
	if prompt.visible:
		var left := _toast_until - Time.get_ticks_msec() / 1000.0
		if left <= 0.0:
			prompt.visible = false
		elif left < 0.5:
			prompt.modulate.a = left / 0.5

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
	_set_slot("attack", 0.0, true, f.p_state == "attack")
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

const SLOT_ACTION := { "attack": "attack", "block": "block-down", "dodge": "dodge", "technique": "technique", "stance": "stance", "pattern": "pattern", "tech1": "tech1", "tech2": "tech2", "tech3": "tech3" }
var _fight_allowed: Array = []

func _set_slot(id: String, cooldown: float, usable: bool, active: bool, glow := Color(0, 0, 0, 0), seconds := 0.0) -> void:
	if not _fight_allowed.is_empty() and SLOT_ACTION[id] not in _fight_allowed:
		usable = false
		glow = Color(0, 0, 0, 0)
	var s: Dictionary = slots[id]
	var cd: ColorRect = s["cd"]
	var k := clampf(cooldown, 0.0, 1.0)
	cd.size = Vector2(SLOT_W - 4, (SLOT_H - 4) * k)
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
