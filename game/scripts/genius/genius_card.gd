## A genius's card: a painted portrait in a brass frame, its name, its form, and its parts.
## The portrait is game/assets/genius/cards/<form>.png when that art exists; until then the card
## shows the genius itself, turning slowly in its own light. A genius with a look of its own
## (its coat, its markings, its keepsake) is always shown as itself: the painted card is the
## form's, and no two of a form are alike.
class_name GeniusCard
extends PanelContainer

const CARD_DIR := "res://game/assets/genius/cards/%s.png"
const W_FULL := 380.0
const ART_FULL := 400.0
var W := 380.0      # a compact card (three on a screen) is narrower and shorter
var ART_H := 400.0

var body: GeniusBody = null   # the genius in the portrait, when the portrait is the genius itself
var _vp: SubViewport
var _pivot: Node3D
var _color := Color.WHITE
var _t := 0.0

## info: a genius's to_dict() (or the Reading's candidate with a name), color: the Shape's.
## art_h: a shorter portrait, where four cards share a screen.
static func make(info: Dictionary, color: Color, title := "", compact := false, art_h := 0.0) -> GeniusCard:
	var c := GeniusCard.new()
	if compact:
		c.W = 300.0
		c.ART_H = 250.0
	if art_h > 0.0:
		c.ART_H = art_h
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
	_color = color
	if ResourceLoader.exists(CARD_DIR % form) and (info.get("look", {}) as Dictionary).is_empty():
		var tr := TextureRect.new()
		tr.texture = load(CARD_DIR % form)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		art.add_child(tr)
	else:
		art.add_child(_portrait(info, color))
	# Name, form, and what it is.
	var n := Label.new()
	Style.label(n, 30 if W >= W_FULL else 25, color.lightened(0.45), "title")
	n.text = String(info.get("name", "")) if String(info.get("name", "")) != "" else _form_name(form)
	n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	# a long name takes a second line; it does not widen the card
	n.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	n.custom_minimum_size = Vector2(W - 28, 0)
	v.add_child(n)
	# what in its partner it is the picture of, under its name
	var pic := String(info.get("of", Data.form(form).get("of", "")))
	if pic != "":
		var ofl := Label.new()
		Style.label(ofl, 15, Style.FG, "italic")
		ofl.text = pic
		ofl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ofl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		ofl.custom_minimum_size = Vector2(W - 28, 0)
		v.add_child(ofl)
	var sub := Label.new()
	Style.label(sub, 15, Style.DIM, "italic")
	var instar := int(info.get("instar", 1))
	var fm := Data.form(form)
	sub.text = "%s  ·  %s  ·  %s" % [String(fm.get("kind", _form_name(form))), String(info.get("expression", "")).capitalize(), GeniusResonance.instar_rule(maxi(1, instar)).get("name", "")]
	# a held genius says which of the three kinds it is (data/genius.json, equipment)
	var cat := GeniusEquip.category(Data.genius().get("equipment", {}), String(fm.get("base", "")).get_slice("+", 0))
	if not cat.is_empty():
		sub.text = "%s  ·  %s" % [String(cat["name"]), sub.text]
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
	# a small card names its first parts; the page names them all
	var named: Array = feats if feats.size() <= 5 else feats.slice(0, 4)
	for f in named:
		var slot := GeniusBody._slot_of(f)
		var lbl := Rite.feature_label(f)
		lines.append("[color=#a8803f]%s[/color]   %s%s" % [slot.to_upper(), lbl, "   [i][color=#9e958a](the Seed-mark)[/color][/i]" if f == mark or (mark == "" and f == feats[0]) else ""])
	if named.size() < feats.size():
		lines.append("[color=#9e958a][i]and %d more[/i][/color]" % (feats.size() - named.size()))
	txt.text = "\n".join(lines)
	v.add_child(txt)

static func _form_name(id: String) -> String:
	var f := Data.form(id)
	return String(f["name"]) if not f.is_empty() else id.capitalize()

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
	env.ambient_light_color = Color(0.62, 0.58, 0.56)
	env.ambient_light_energy = 0.55
	env.glow_enabled = true
	env.glow_intensity = 0.8
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	_pivot = Node3D.new()
	_vp.add_child(_pivot)
	_stand(info)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-30, 30, 0)
	key.light_color = Color(1.0, 0.9, 0.78)
	key.light_energy = 1.35
	_vp.add_child(key)
	var rim := OmniLight3D.new()
	rim.position = Vector3(0, 0.6, -1.0)
	rim.light_color = color
	rim.light_energy = 1.6
	rim.omni_range = 3.0
	_vp.add_child(rim)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 0.45, 1.65)
	cam.fov = 38.0
	_vp.add_child(cam)
	cam.look_at_from_position(cam.position, Vector3(0, 0.3, 0), Vector3.UP)
	return holder

## Put the genius in the portrait (again, when its look has changed).
func _stand(info: Dictionary) -> void:
	if _pivot == null:
		return
	if body:
		_pivot.remove_child(body)
		body.queue_free()
	var gi := info.duplicate()
	gi["instar"] = 1
	body = GeniusBody.build(gi, _color, 1)
	# a portrait is to see it by: its own colours first, the Shape's along the edge
	body.set_rim(0.3)
	_pivot.add_child(body)
	_pivot.scale = Vector3.ONE * portrait_scale(body.stands * body.art_size)
	# (a held genius is the size of a thing a hand holds, at every stage: a bow is brought down
	# into the frame, a bell up into it)
	if body.hand_k > 0.0:
		_pivot.scale = Vector3.ONE * held_scale(body.stands)

## A portrait is to see it by: a genius that stands very small (a godling, a kit) is brought up
## to fill a fair part of the frame; one that already does is left at its own size.
static func portrait_scale(height: float) -> float:
	return clampf(0.56 / maxf(height, 0.05), 1.0, 2.8)

## The same for a held genius, which may also be longer than the frame is tall.
static func held_scale(long: float) -> float:
	return clampf(0.6 / maxf(long, 0.05), 0.35, 2.8)

func restyle(info: Dictionary) -> void:
	_stand(info)

func _process(dt: float) -> void:
	_t += dt
	if _pivot:
		_pivot.rotation.y = 0.5 + 0.4 * sin(_t * 0.5)
