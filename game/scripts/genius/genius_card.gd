## A genius's card: a painted portrait in a brass frame, its name, its form, and its parts.
## The portrait is game/assets/genius/cards/<form>.png when that art exists; until then the card
## shows the genius itself, turning slowly in its own light.
class_name GeniusCard
extends PanelContainer

const CARD_DIR := "res://game/assets/genius/cards/%s.png"
const W := 380.0
const ART_H := 400.0

var _vp: SubViewport
var _pivot: Node3D
var _t := 0.0

## info: a genius's to_dict() (or the Reading's candidate with a name), color: the Shape's.
static func make(info: Dictionary, color: Color, title := "") -> GeniusCard:
	var c := GeniusCard.new()
	c._build(info, color, title)
	return c

func _build(info: Dictionary, color: Color, title: String) -> void:
	custom_minimum_size = Vector2(W, 0)
	var frame := Style.plate(Color(0.035, 0.03, 0.028, 0.97), Style.BRASS, 2, 14, 10)
	frame.shadow_size = 24
	frame.shadow_color = Color(color, 0.25)
	add_theme_stylebox_override("panel", frame)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	add_child(v)
	if title != "":
		var t := Label.new()
		Style.label(t, 13, Style.BRASS, "title_light")
		t.text = title
		t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(t)
	# The portrait.
	var art := PanelContainer.new()
	art.custom_minimum_size = Vector2(W - 28, ART_H)
	var inner := Style.plate(Color(0.02, 0.018, 0.02), Style.BRASS_DIM, 1, 0, 6)
	inner.shadow_size = 0
	art.add_theme_stylebox_override("panel", inner)
	v.add_child(art)
	var form: String = info.get("form", "")
	if ResourceLoader.exists(CARD_DIR % form):
		var tr := TextureRect.new()
		tr.texture = load(CARD_DIR % form)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		art.add_child(tr)
	else:
		art.add_child(_portrait(info, color))
	# Name, form, and what it is.
	var n := Label.new()
	Style.label(n, 30, color.lightened(0.45), "title")
	n.text = String(info.get("name", "")) if String(info.get("name", "")) != "" else _form_name(form)
	n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(n)
	var sub := Label.new()
	Style.label(sub, 15, Style.DIM, "italic")
	var instar := int(info.get("instar", 1))
	sub.text = "%s  ·  %s  ·  %s" % [_form_name(form), String(info.get("expression", "")).capitalize(), GeniusResonance.instar_rule(maxi(1, instar)).get("name", "")]
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(sub)
	var r := Style.rule(W - 40, Style.BRASS_DIM)
	v.add_child(r)
	# Its parts, the Seed-mark first and marked.
	var feats: Array = info.get("features", [])
	var mark := String(info.get("body", {}).get("seedMark", info.get("seedMark", "")))
	var txt := RichTextLabel.new()
	txt.bbcode_enabled = true
	txt.fit_content = true
	txt.scroll_active = false
	txt.custom_minimum_size = Vector2(W - 28, 0)
	Style.rich(txt, 15, Style.FG, "body")
	var lines: Array = []
	for f in feats:
		var slot := GeniusBody._slot_of(f)
		var lbl := Rite.feature_label(f)
		lines.append("[color=#a8803f]%s[/color]   %s%s" % [slot.to_upper(), lbl, "   [i][color=#9e958a](the Seed-mark)[/color][/i]" if f == mark or (mark == "" and f == feats[0]) else ""])
	txt.text = "\n".join(lines)
	v.add_child(txt)

static func _form_name(id: String) -> String:
	for f in Data.forms():
		if f["id"] == id:
			return f["name"]
	return id.capitalize()

## A small world of its own: the genius on a dark ground, lit from behind in its colour.
func _portrait(info: Dictionary, color: Color) -> Control:
	var holder := SubViewportContainer.new()
	holder.stretch = true
	holder.custom_minimum_size = Vector2(W - 28, ART_H)
	_vp = SubViewport.new()
	_vp.own_world_3d = true
	_vp.transparent_bg = false
	_vp.size = Vector2i(int(W - 28), int(ART_H))
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	holder.add_child(_vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.03, 0.025, 0.03)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.5, 0.45, 0.45)
	env.ambient_light_energy = 0.3
	env.glow_enabled = true
	env.glow_intensity = 0.8
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	_pivot = Node3D.new()
	_vp.add_child(_pivot)
	var gi := info.duplicate()
	gi["instar"] = 1
	var body := GeniusBody.build(gi, color, 1)
	_pivot.add_child(body)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-30, 30, 0)
	key.light_color = Color(1.0, 0.75, 0.5)
	key.light_energy = 0.9
	_vp.add_child(key)
	var rim := OmniLight3D.new()
	rim.position = Vector3(0, 0.6, -1.0)
	rim.light_color = color
	rim.light_energy = 3.0
	rim.omni_range = 3.0
	_vp.add_child(rim)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 0.45, 1.65)
	cam.fov = 38.0
	_vp.add_child(cam)
	cam.look_at_from_position(cam.position, Vector3(0, 0.3, 0), Vector3.UP)
	return holder

func _process(dt: float) -> void:
	_t += dt
	if _pivot:
		_pivot.rotation.y = 0.5 + 0.4 * sin(_t * 0.5)
