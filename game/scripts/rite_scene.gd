## The rite, played: pour your field into the bowl; the six Shapes' lights race round it and
## slow, and the fire lands on yours; the little orb goes into the fire, a column of light
## stands up, the features are called out one by one, and the First Form comes out of it.
## Built for anticipation, like a monster-breeding game's disc reading. Reading: rite.gd.
class_name RiteScene
extends RefCounted

signal done

var ac: Academy
var world: World
var sfx: Sfx
var hero: Dictionary
var cfg: Dictionary
var phase := "intro"
var t := 0.0
var fill := 0.0
var reading: Dictionary
var form: Dictionary
var seq: Array = []
var seq_i := 0
var next_tick := 0.0
var turn := 0.0
var _feat_i := 0
var _form_node: Node3D
var _tick_t := 0.0

func _init(a: Academy, h: Dictionary) -> void:
	ac = a
	world = a.world
	sfx = a.sfx
	hero = h
	cfg = Data.academy["rite"]
	var seed_value := int(a.progress["seed"]) * 13 + 5
	reading = Rite.read_shape(hero, a.progress["record"], seed_value)
	form = Rite.first_form(hero, reading["shape"], seed_value)
	seq = _sequence(reading["shape"], reading["was"], reading["surprise"], int(cfg["spinSteps"]))

## The lights the fire passes through: round the ring, slowing; on a surprise it hesitates on
## the Shape the questions gave, then tips over to the one it reads.
static func _sequence(result: String, was: String, surprise: bool, n: int) -> Array:
	var ring: Array = Creation.SHAPES
	var out: Array = []
	var stop := was if surprise else result
	var start := posmod(ring.find(stop) - (n - 1), ring.size())
	for i in n:
		out.append(ring[(start + i) % ring.size()])
	if surprise:
		out.append(was)       # it hangs there...
		out.append(result)    # ...and goes over
	return out

func start() -> void:
	phase = "intro"
	world.cine = true
	world.cine_speed = 1.6
	_cam_side()
	var lines: Array = cfg["lines"]["intro"]
	ac.say(cfg["instructor"], lines, func(): _go("pour"))

func _go(p: String) -> void:
	phase = p
	t = 0.0
	match p:
		"pour":
			ac.show_pour(true, Rite_fill(cfg["lines"]["pour"]))
		"spin":
			ac.show_pour(false, "")
			seq_i = 0
			next_tick = 0.0
			world.cine_speed = 0.8
		"genius":
			world.sigils(false)
			world.genius_goal = World.BOWL + Vector3(0, 1.5, 0)
			world.genius_goal_radius = 1.2
			sfx.play("pattern", 0.7)
		"name":
			ac.ask_name(form["name"], func(n: String): _named(n))

func Rite_fill(s: String) -> String:
	return ac.fill(s)

func _cam_side() -> void:
	var p := Vector3(ac.fight.p_pos.x, 0, ac.fight.p_pos.y)
	world.cine_pos = p + Vector3(3.6, 2.6, 2.6)
	world.cine_look = World.BOWL.lerp(p, 0.45) + Vector3(0, 1.4, 0)

func busy() -> bool:
	return true

func update(dt: float, held: bool) -> void:
	t += dt
	match phase:
		"pour": _pour(dt, held)
		"spin": _spin(dt)
		"landed": _landed(dt)
		"genius": _genius(dt)
		"making": _making(dt)
		"form": _form(dt)

func _pour(dt: float, held: bool) -> void:
	fill = clampf(fill + (dt / float(cfg["pourSeconds"]) if held else -dt * 0.25), 0.0, 1.0)
	ac.set_pour(fill)
	world.dim(fill * 0.85)
	var c := Color(1.0, 0.65, 0.3).lerp(Color(1.0, 0.95, 0.85), fill)
	world.flame(c, 0.8 + 1.4 * fill, 4.0 + 4.0 * fill)
	_tick_t -= dt
	if held and _tick_t <= 0.0:
		_tick_t = 0.22 - 0.12 * fill
		sfx.play("cue", 0.7 + 0.8 * fill, -8.0)
		var p := Vector3(ac.fight.p_pos.x, 1.3, ac.fight.p_pos.y)
		world.burst(p.lerp(World.BOWL + Vector3(0, 1.4, 0), randf()), Color(1.0, 0.85, 0.55), 3, 1.5)
	# The camera leans in as the field pours.
	var p2 := Vector3(ac.fight.p_pos.x, 0, ac.fight.p_pos.y)
	world.cine_pos = p2 + Vector3(3.6 - fill, 2.6 - 0.6 * fill, 2.6 - 0.6 * fill)
	if fill >= 1.0:
		world.flash_screen(Color(1, 0.9, 0.7), 0.5)
		world._shake = 0.08
		_go("spin")

func _spin(dt: float) -> void:
	turn += dt * (2.5 - 2.0 * float(seq_i) / seq.size())
	# The camera circles the bowl, slowly, high.
	var a := 0.6 + t * 0.12
	world.cine_pos = World.BOWL + Vector3(sin(a) * 6.0, 4.2, cos(a) * 6.0)
	world.cine_look = World.BOWL + Vector3(0, 1.8, 0)
	var shape: String = seq[mini(seq_i, seq.size() - 1)]
	world.sigils(true, shape, turn)
	if t < next_tick:
		return
	if seq_i >= seq.size():
		_go("landed")
		_land()
		return
	var col: Color = World.SHAPE_COLORS[shape]
	world.flame(col, 1.6 + 0.3 * float(seq_i) / seq.size(), 6.0)
	var k := float(seq_i) / float(seq.size())
	sfx.play("cue", 0.8 + 0.7 * k, -4.0)
	# Faster at first, slower and slower; on a surprise, a long breath on the Shape it nearly was.
	var gap := lerpf(0.07, 0.55, pow(k, 2.2))
	if reading["surprise"] and seq_i == seq.size() - 2:
		gap = 1.5
	elif seq_i == seq.size() - 1:
		gap = 0.9
	next_tick = t + gap
	seq_i += 1

func _land() -> void:
	var shape: String = reading["shape"]
	var col: Color = World.SHAPE_COLORS[shape]
	var top := World.BOWL + Vector3(0, 1.8, 0)
	world.flame(col, 2.6, 9.0)
	world.flash_screen(col, 0.9)
	world._ring_wave(World.BOWL, col, 7.0)
	world.burst(top, col, 140, 8.0)
	world.impact(top, col, 2.8)
	world._shake = 0.25
	world.slowmo(0.5, 0.3)
	sfx.play("heavy", 0.7)
	sfx.play("pattern", 1.0)
	world.cine_pos = World.BOWL + Vector3(0, 3.0, 5.4)
	world.cine_look = top
	world.cine_speed = 3.0
	ac.title_card(shape.to_upper(), "THE BOWL READS YOU" if not reading["surprise"] else "NOT %s" % String(reading["was"]).to_upper(), col)
	if reading["surprise"]:
		Rite.reshape(hero, shape)
	world._tint_genius(col)
	hero["rite_shape"] = { "was": reading["was"], "read": shape }

func _landed(dt: float) -> void:
	world.sigils(true, reading["shape"], turn)
	turn += dt * 0.3
	if t > 2.6 and not ac.talking():
		world.sigils(true, reading["shape"], turn)
		var key := "surprise" if reading["surprise"] else "confirm"
		var line := String(cfg["lines"][key]).replace("{shape}", String(reading["shape"]).capitalize()).replace("{was}", String(reading["was"]).capitalize())
		phase = "landed-talk"
		ac.say(cfg["instructor"], [line, cfg["lines"]["genius"]], func(): _go("genius"))

func _genius(dt: float) -> void:
	# The orb spirals in, tighter and tighter, and the fire takes it.
	world.genius_goal_radius = maxf(0.0, 1.2 - t * 0.45)
	world.cine_pos = World.BOWL + Vector3(2.2, 2.4, 4.4)
	world.cine_look = World.BOWL + Vector3(0, 1.6, 0)
	world._g_pulse = 0.3 + 0.2 * sin(t * 12.0)
	if t > 2.8:
		world.genius_visible = false
		world.flame(Color(1, 1, 1), 2.4, 10.0)
		world.flash_screen(Color(1, 1, 1), 0.6)
		sfx.play("parry", 0.8)
		_feat_i = 0
		_go("making")

func _making(dt: float) -> void:
	var col: Color = World.SHAPE_COLORS[hero["shape"]].lightened(0.15)
	world.light_pillar(minf(9.0, t * 6.0), col)
	world._shake = minf(0.12, 0.02 + t * 0.025)
	world.cine_pos = World.BOWL + Vector3(0, 2.0 + t * 0.4, 5.6 - t * 0.2)
	world.cine_look = World.BOWL + Vector3(0, 2.2 + t * 0.2, 0)
	var feats: Array = form["features"]
	# Each feature is called out of the light, one after another, each a note higher.
	if _feat_i < feats.size() and t > 1.0 + _feat_i * 0.85:
		var lbl := Rite.feature_label(String(feats[_feat_i]))
		world.floater(World.BOWL + Vector3(randf_range(-0.9, 0.9), 2.6 + _feat_i * 0.35, 0.6), lbl.to_upper(), col.lightened(0.3), 64, 2.6, 0.35)
		sfx.play("cue-hit", 0.8 + 0.18 * _feat_i)
		_feat_i += 1
	if t > 1.4 + feats.size() * 0.85 + 0.8:
		_burst_form()
		_go("form")

func _burst_form() -> void:
	var col: Color = World.SHAPE_COLORS[hero["shape"]].lightened(0.15)
	_form_node = world.make_form(form, col)
	world.add_child(_form_node)
	_form_node.global_position = World.BOWL + Vector3(0, 1.5, 0)
	_form_node.scale = Vector3.ONE * 0.05
	var tw := _form_node.create_tween()
	tw.tween_property(_form_node, "scale", Vector3.ONE * 2.6, 0.9).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	world.light_pillar(0.0, col)
	world.flash_screen(col, 1.0)
	world._ring_wave(World.BOWL, col, 8.0)
	world.burst(World.BOWL + Vector3(0, 2.0, 0), col, 160, 9.0)
	world.impact(World.BOWL + Vector3(0, 2.0, 0), col, 3.2)
	world._shake = 0.3
	world.slowmo(0.6, 0.3)
	world.flame(Color(1.0, 0.65, 0.3), 0.7, 3.0)
	sfx.play("heavy", 0.6)
	sfx.play("done", 1.0)
	world.cine_pos = World.BOWL + Vector3(1.0, 2.0, 4.6)
	world.cine_look = World.BOWL + Vector3(0, 2.3, 0)
	world.cine_speed = 2.0
	var feats: Array = form["features"].map(func(f): return Rite.feature_label(String(f)))
	ac.title_card(String(form["name"]).to_upper(), "FIRST FORM  ·  %s  ·  %s" % [String(form["expression"]).to_upper(), ", ".join(feats)], col)

func _form(dt: float) -> void:
	if _form_node:
		_form_node.rotation.y += dt * 0.6
		_form_node.position.y = World.BOWL.y + 1.5 + 0.12 * sin(t * 2.0)
	if t > 3.6 and phase == "form":
		_go("name")

func _named(n: String) -> void:
	var g := form.duplicate(true)
	g["name"] = n if n.strip_edges() != "" else form["name"]
	g["form_name"] = form["name"]
	hero["genius"] = g
	# It comes down to its partner, small, and stays.
	var tw := _form_node.create_tween()
	tw.tween_property(_form_node, "scale", Vector3.ONE, 0.8).set_trans(Tween.TRANS_SINE)
	world.set_form(g, _form_node)
	world.genius_goal = Vector3.INF
	world.genius_visible = true
	var lines: Array = []
	for l in cfg["lines"]["after"]:
		lines.append(String(l).replace("{genius_name}", g["name"]).replace("{form}", String(form["name"]).to_lower()).replace("{shape}", String(hero["shape"]).capitalize()))
	var d := world.create_tween()
	d.tween_method(func(k: float): world.dim(k), 0.85, 0.0, 2.0)
	world.cine = false
	world.sigils(false)
	ac.say(cfg["instructor"], lines, func(): done.emit())
