## The on-screen layer: Health and Will, the timer, the tutorial box, the beat track along the
## bottom (beats ride in to a line; the wolf's bite is marked red), menus and results.
class_name Hud
extends CanvasLayer

const BG := Color(0.06, 0.05, 0.04, 0.88)
const FG := Color(0.91, 0.86, 0.78)
const DIM := Color(0.6, 0.55, 0.47)
const ACCENT := Color(0.85, 0.64, 0.25)
const RED := Color(0.85, 0.28, 0.23)
const BLUE := Color(0.62, 0.78, 0.91)
const GREEN := Color(0.62, 0.88, 0.54)
const OFF := Color(0.88, 0.59, 0.35)

var play_ui := Control.new()
var hp_bar := ProgressBar.new()
var will_bar := ProgressBar.new()
var hp_label := Label.new()
var will_label := Label.new()
var chain_label := Label.new()
var timer_label := Label.new()
var score_label := Label.new()
var wolf_bar := ProgressBar.new()
var prompt := PanelContainer.new()
var prompt_title := Label.new()
var prompt_text := RichTextLabel.new()
var prompt_note := Label.new()
var prompt_progress := Label.new()
var keys := Label.new()
var track := BeatTrack.new()
var screen := ColorRect.new()
var screen_box := VBoxContainer.new()

func _ready() -> void:
	layer = 10
	play_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	play_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(play_ui)

	var left := VBoxContainer.new()
	left.position = Vector2(24, 18)
	left.custom_minimum_size = Vector2(380, 0)
	play_ui.add_child(left)
	for pair in [[hp_label, hp_bar, RED], [will_label, will_bar, BLUE]]:
		var l: Label = pair[0]
		_style_label(l, 15, DIM)
		left.add_child(l)
		var b: ProgressBar = pair[1]
		_style_bar(b, pair[2])
		left.add_child(b)
	_style_label(chain_label, 18, GREEN)
	left.add_child(chain_label)

	var right := VBoxContainer.new()
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	right.position = Vector2(-320, 18)
	right.custom_minimum_size = Vector2(296, 0)
	right.alignment = BoxContainer.ALIGNMENT_END
	play_ui.add_child(right)
	_style_label(timer_label, 36, FG)
	timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(timer_label)
	_style_label(score_label, 15, DIM)
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(score_label)
	_style_bar(wolf_bar, RED)
	right.add_child(wolf_bar)

	# The tutorial box, top centre.
	prompt.set_anchors_preset(Control.PRESET_CENTER_TOP)
	prompt.custom_minimum_size = Vector2(760, 0)
	prompt.position = Vector2(-380, 110)
	prompt.add_theme_stylebox_override("panel", _panel())
	var pv := VBoxContainer.new()
	prompt.add_child(pv)
	_style_label(prompt_title, 20, ACCENT)
	pv.add_child(prompt_title)
	prompt_text.bbcode_enabled = true
	prompt_text.fit_content = true
	prompt_text.scroll_active = false
	prompt_text.custom_minimum_size = Vector2(728, 0)
	prompt_text.add_theme_font_size_override("normal_font_size", 17)
	prompt_text.add_theme_font_size_override("bold_font_size", 17)
	prompt_text.add_theme_color_override("default_color", FG)
	pv.add_child(prompt_text)
	var row := HBoxContainer.new()
	_style_label(prompt_note, 14, DIM)
	prompt_note.autowrap_mode = TextServer.AUTOWRAP_WORD
	prompt_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(prompt_note)
	_style_label(prompt_progress, 14, DIM)
	row.add_child(prompt_progress)
	pv.add_child(row)
	play_ui.add_child(prompt)

	track.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	track.offset_top = -120
	play_ui.add_child(track)

	_style_label(keys, 14, DIM)
	keys.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	keys.position = Vector2(24, -152)
	keys.text = "WASD move · mouse look · J / left click strike · I / E Ground Strike (18 Will) · K / right click Hold · L / F stance · Tab lock-on · Esc menu"
	play_ui.add_child(keys)

	# Menus and results.
	screen.color = Color(0.06, 0.05, 0.04, 0.94)
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(screen)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen.add_child(center)
	screen_box.custom_minimum_size = Vector2(640, 0)
	screen_box.add_theme_constant_override("separation", 10)
	center.add_child(screen_box)

func _style_label(l: Label, size: int, color: Color) -> void:
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("outline_size", 4)

func _style_bar(b: ProgressBar, color: Color) -> void:
	b.custom_minimum_size = Vector2(0, 14)
	b.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0, 0, 0, 0.7)
	bg.border_color = Color(0.23, 0.2, 0.16)
	bg.set_border_width_all(1)
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	b.add_theme_stylebox_override("background", bg)
	b.add_theme_stylebox_override("fill", fill)

func _panel() -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = BG
	s.border_color = Color(0.23, 0.2, 0.16)
	s.set_border_width_all(1)
	s.set_content_margin_all(16)
	return s

# --- Screens ----------------------------------------------------------------

func show_screen(title: String, subtitle: String, body: String, buttons: Array) -> void:
	for c in screen_box.get_children():
		c.queue_free()
	var t := Label.new()
	_style_label(t, 44, ACCENT)
	t.text = title
	screen_box.add_child(t)
	if subtitle != "":
		var s := Label.new()
		_style_label(s, 19, DIM)
		s.text = subtitle
		s.autowrap_mode = TextServer.AUTOWRAP_WORD
		screen_box.add_child(s)
	if body != "":
		var b := RichTextLabel.new()
		b.bbcode_enabled = true
		b.fit_content = true
		b.scroll_active = false
		b.custom_minimum_size = Vector2(640, 0)
		b.add_theme_font_size_override("normal_font_size", 17)
		b.add_theme_color_override("default_color", FG)
		b.text = body
		screen_box.add_child(b)
	var first: Button = null
	for spec in buttons:
		var btn := Button.new()
		btn.text = spec[0]
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.add_theme_font_size_override("font_size", 19)
		btn.custom_minimum_size = Vector2(0, 46)
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

func update_play(f: Fight, t: float, timer_text: String, score_text: String) -> void:
	hp_bar.max_value = float(Data.room["player"]["health"])
	hp_bar.value = f.p_hp
	hp_label.text = "HEALTH  %d" % roundi(f.p_hp)
	will_bar.value = f.p_will
	var state := ""
	if f.p_fainted: state = "  ·  FAINTED"
	elif f.p_stance: state = "  ·  ANCHOR STANCE (−2/s)"
	elif f.p_guard: state = "  ·  HOLDING (−3/s)"
	will_label.text = "WILL  %d%s" % [roundi(f.p_will), state]
	chain_label.text = "Chain ×%d" % f.p_chain if f.p_chain > 1 else ""
	timer_label.text = timer_text
	score_label.text = score_text
	wolf_bar.max_value = float(f.beast["health"])
	wolf_bar.value = f.w_hp
	wolf_bar.visible = float(f.beast["health"]) < 5000
	track.f = f
	track.t = t
	track.queue_redraw()

## The beat track: beats ride in from the right to the line; a strike is a red diamond.
class BeatTrack extends Control:
	var f: Fight
	var t := 0.0
	var show_wolf := true
	var marks: Array = []

	func mark(at: float, perfect: bool) -> void:
		marks.append({ "t": at, "perfect": perfect })

	func _draw() -> void:
		if f == null:
			return
		var w := size.x
		var h := size.y
		draw_rect(Rect2(0, 0, w, h), Color(0.04, 0.035, 0.03, 0.92))
		var line_x := 220.0
		var px := 150.0
		var y := h / 2.0
		var half := f.window_ms / 2000.0 / f.period * px
		draw_rect(Rect2(line_x - half, 14, half * 2, h - 28), Color(0.91, 0.86, 0.78, 0.08))
		draw_rect(Rect2(line_x - 1.5, 10, 3, h - 20), Color(0.91, 0.86, 0.78, 0.85))
		var k_now := floori((t - f.t0) / f.period)
		for k in range(maxi(0, k_now - 2), k_now + 12):
			var x := line_x + (f.beat_time(k) - t) / f.period * px
			if x < 0 or x > w:
				continue
			var r := 10.0 if k % 4 == 0 else 7.0
			draw_circle(Vector2(x, y), r, Color(0.91, 0.86, 0.78, 0.2 if x < line_x else 0.8))
		if show_wolf and f.w_mode == "windup":
			var x := line_x + (f.beat_time(f.w_strike_beat) - t) / f.period * px
			var pts := PackedVector2Array([Vector2(x, y - 24), Vector2(x + 17, y), Vector2(x, y + 24), Vector2(x - 17, y)])
			draw_colored_polygon(pts, Color(0.85, 0.28, 0.23, 0.9))
			draw_string(get_theme_default_font(), Vector2(x - 70, y - 30), "STRIKE — Hold (K)", HORIZONTAL_ALIGNMENT_CENTER, 140, 14, Color(0.95, 0.4, 0.33))
		var keep: Array = []
		for m in marks:
			if t - m["t"] < f.period * 3:
				keep.append(m)
				var x: float = line_x + (float(m["t"]) - t) / f.period * px
				draw_rect(Rect2(x - 2, y + 20, 4, 24), Color(0.62, 0.88, 0.54) if m["perfect"] else Color(0.88, 0.59, 0.35))
		marks = keep
