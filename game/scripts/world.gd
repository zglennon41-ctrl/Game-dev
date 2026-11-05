## The 3D room: a stretch of the Cumberland Cut, the Anchor, the cut-wolf, the pulse ring at
## the Anchor's feet, a third-person camera with lock-on, and hit feedback.
## Placeholder art is primitives with labels; the feel is not placeholder.
class_name World
extends Node3D

const C_PLAYER := Color(0.54, 0.43, 0.30)
const C_PLAYER_EDGE := Color(0.85, 0.76, 0.62)
const C_STANCE := Color(0.85, 0.64, 0.25)
const C_RING := Color(0.91, 0.86, 0.78)
const C_WOLF := Color(0.42, 0.48, 0.54)
const C_WINDUP := Color(0.85, 0.28, 0.23)
const C_STAGGER := Color(0.95, 0.82, 0.42)
const C_PERFECT := Color(0.62, 0.88, 0.54)
const C_OFF := Color(0.88, 0.59, 0.35)
const C_GUARD := Color(0.62, 0.78, 0.91)
const C_DIM := Color(0.6, 0.55, 0.47)

var camera := Camera3D.new()
var lock_on := true
var cam_yaw := 0.0
var cam_pitch := -0.42
var show_wolf := true

var _player := Node3D.new()
var _player_body_mat := StandardMaterial3D.new()
var _guard := MeshInstance3D.new()
var _aura := MeshInstance3D.new()
var _saber := Node3D.new()
var _ring_base := MeshInstance3D.new()
var _ring_close := MeshInstance3D.new()
var _ring_band := MeshInstance3D.new()
var _ring_mat := StandardMaterial3D.new()
var _ring_close_mat := StandardMaterial3D.new()
var _player_label := Label3D.new()

var _wolf := Node3D.new()
var _wolf_mat := StandardMaterial3D.new()
var _wolf_label := Label3D.new()
var _wolf_pips := Label3D.new()
var _reach := MeshInstance3D.new()
var _reach_mat := StandardMaterial3D.new()
var _wolf_head := Node3D.new()

var _floaters: Array = []
var _shake := 0.0
var _flash := 0.0
var _hitstop_until := 0
var _frozen := {}
var _lunge := 0.0
var _recoil := 0.0
var _swing := 0.0
var _last_p := Vector3.ZERO
var _last_w := Vector3.ZERO
var _cam_pos := Vector3(0, 4, 8)
var _cam_look := Vector3.ZERO

func _ready() -> void:
	_build_environment()
	_build_tunnel()
	_build_player()
	_build_wolf()
	add_child(camera)
	camera.fov = 62.0
	camera.current = true

# --- Building ---------------------------------------------------------------

func _mat(color: Color, emission := 0.0, unshaded := false, alpha := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(color, alpha)
	if emission > 0.0:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = emission
	if unshaded:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if alpha < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return m

func _box(parent: Node3D, size: Vector3, pos: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.position = pos
	mi.material_override = mat
	parent.add_child(mi)
	return mi

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.05, 0.04, 0.035)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.32, 0.27, 0.22)
	env.ambient_light_energy = 0.55
	env.fog_enabled = true
	env.fog_light_color = Color(0.09, 0.075, 0.06)
	env.fog_density = 0.035
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.glow_intensity = 0.6
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-55, 30, 0)
	key.light_color = Color(0.75, 0.7, 0.85)
	key.light_energy = 0.35
	key.shadow_enabled = true
	add_child(key)

func _build_tunnel() -> void:
	var a: Dictionary = Data.room["arena"]
	var w := float(a["width"]) + 10.0
	var d := float(a["depth"])
	var floor_mat := _mat(Color(0.13, 0.11, 0.095))
	_box(self, Vector3(w, 0.2, d + 2.0), Vector3(0, -0.1, 0), floor_mat)
	# The line: ties and two rails running through the Cut.
	var tie_mat := _mat(Color(0.2, 0.15, 0.11))
	var rail_mat := _mat(Color(0.35, 0.33, 0.31))
	rail_mat.metallic = 0.8
	rail_mat.roughness = 0.35
	var x := -w / 2.0 + 0.4
	while x < w / 2.0:
		_box(self, Vector3(0.28, 0.1, 2.5), Vector3(x, 0.05, 0), tie_mat)
		x += 0.75
	for z in [-0.72, 0.72]:
		_box(self, Vector3(w, 0.12, 0.09), Vector3(0, 0.14, z), rail_mat)
	# Tunnel walls of dressed stone, and lamps.
	var wall_mat := _mat(Color(0.17, 0.15, 0.135))
	for side in [-1, 1]:
		_box(self, Vector3(w, 5.0, 0.6), Vector3(0, 2.5, side * (d / 2.0 + 0.6)), wall_mat)
		var lx := -w / 2.0 + 3.0
		while lx < w / 2.0:
			var lamp := OmniLight3D.new()
			lamp.light_color = Color(1.0, 0.72, 0.42)
			lamp.light_energy = 1.6
			lamp.omni_range = 7.0
			lamp.position = Vector3(lx, 3.0, side * (d / 2.0 - 0.1))
			add_child(lamp)
			_box(self, Vector3(0.25, 0.35, 0.25), lamp.position, _mat(Color(1.0, 0.75, 0.45), 3.0, true))
			lx += 6.0
	# Arches overhead, every few meters, so the space reads as a tunnel.
	var arch_mat := _mat(Color(0.12, 0.1, 0.09))
	var ax := -w / 2.0 + 1.5
	while ax < w / 2.0:
		_box(self, Vector3(0.6, 0.6, d + 2.4), Vector3(ax, 5.2, 0), arch_mat)
		ax += 4.5

func _build_player() -> void:
	add_child(_player)
	_player_body_mat = _mat(C_PLAYER)
	var body := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.42
	cap.height = 1.45
	body.mesh = cap
	body.position = Vector3(0, 0.78, 0)
	body.material_override = _player_body_mat
	_player.add_child(body)
	_box(_player, Vector3(1.15, 0.28, 0.55), Vector3(0, 1.32, 0), _mat(C_PLAYER_EDGE))
	var head := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.22
	sph.height = 0.44
	head.mesh = sph
	head.position = Vector3(0, 1.68, 0)
	head.material_override = _mat(Color(0.72, 0.6, 0.48))
	_player.add_child(head)
	# The saber, held forward-right; it swings on a strike.
	_saber.position = Vector3(0.55, 1.0, 0)
	_player.add_child(_saber)
	_box(_saber, Vector3(0.06, 0.06, 1.05), Vector3(0, 0, -0.55), _mat(Color(0.82, 0.84, 0.88), 0.4))
	_box(_saber, Vector3(0.22, 0.05, 0.05), Vector3(0, 0, -0.02), _mat(Color(0.75, 0.6, 0.3)))
	# The guard: a pane of field in front of the Anchor while Holding.
	var gm := BoxMesh.new()
	gm.size = Vector3(1.5, 1.4, 0.06)
	_guard.mesh = gm
	_guard.position = Vector3(0, 1.0, -0.75)
	_guard.material_override = _mat(C_GUARD, 1.2, true, 0.35)
	_guard.visible = false
	_player.add_child(_guard)
	# The stance: a low amber column of field.
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.75
	cyl.bottom_radius = 0.9
	cyl.height = 2.0
	_aura.mesh = cyl
	_aura.position = Vector3(0, 1.0, 0)
	_aura.material_override = _mat(C_STANCE, 1.0, true, 0.13)
	_aura.visible = false
	_player.add_child(_aura)
	# The pulse ring at the feet: a base ring, a band for the window, a ring that closes on the beat.
	_ring_mat = _mat(C_RING, 1.5, true, 0.9)
	_ring_close_mat = _mat(C_RING, 1.2, true, 0.6)
	for pair in [[_ring_base, 0.9, 1.0, _ring_mat], [_ring_close, 0.95, 1.03, _ring_close_mat], [_ring_band, 0.8, 1.1, _mat(C_RING, 0.5, true, 0.1)]]:
		var mi: MeshInstance3D = pair[0]
		var t := TorusMesh.new()
		t.inner_radius = pair[1]
		t.outer_radius = pair[2]
		t.rings = 48
		mi.mesh = t
		mi.scale = Vector3(1, 0.05, 1)
		mi.position = Vector3(0, 0.05, 0)
		mi.material_override = pair[3]
		add_child(mi)
	_player_label.text = "ANCHOR"
	_player_label.font_size = 40
	_player_label.pixel_size = 0.005
	_player_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_player_label.modulate = Color(C_RING, 0.8)
	_player_label.outline_size = 8
	_player_label.position = Vector3(0, 2.15, 0)
	_player.add_child(_player_label)

func _build_wolf() -> void:
	add_child(_wolf)
	_wolf_mat = _mat(C_WOLF)
	_wolf_mat.emission_enabled = true
	_wolf_mat.emission = C_WINDUP
	_wolf_mat.emission_energy_multiplier = 0.0
	# Body along -z (forward), low and long; legs; a head with a snout and ears.
	var body := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.32
	cap.height = 1.5
	body.mesh = cap
	body.rotation_degrees = Vector3(90, 0, 0)
	body.position = Vector3(0, 0.78, 0)
	body.material_override = _wolf_mat
	_wolf.add_child(body)
	for lx in [-0.2, 0.2]:
		for lz in [-0.45, 0.45]:
			_box(_wolf, Vector3(0.12, 0.6, 0.12), Vector3(lx, 0.3, lz), _wolf_mat)
	_wolf_head.position = Vector3(0, 1.05, -0.85)
	_wolf.add_child(_wolf_head)
	_box(_wolf_head, Vector3(0.38, 0.34, 0.42), Vector3.ZERO, _wolf_mat)
	_box(_wolf_head, Vector3(0.22, 0.18, 0.36), Vector3(0, -0.06, -0.34), _wolf_mat)
	for ex in [-0.12, 0.12]:
		var ear := MeshInstance3D.new()
		var pm := PrismMesh.new()
		pm.size = Vector3(0.14, 0.2, 0.08)
		ear.mesh = pm
		ear.position = Vector3(ex, 0.26, 0.06)
		ear.material_override = _wolf_mat
		_wolf_head.add_child(ear)
	for ey in [-0.09, 0.09]:
		_box(_wolf_head, Vector3(0.06, 0.05, 0.02), Vector3(ey, 0.06, -0.22), _mat(Color(0.95, 0.85, 0.5), 3.0, true))
	_box(_wolf, Vector3(0.1, 0.1, 0.6), Vector3(0, 0.95, 0.95), _wolf_mat).rotation_degrees = Vector3(-30, 0, 0)
	# The bite's reach, shown on the ground while it winds up.
	var disc := CylinderMesh.new()
	disc.top_radius = 1.0
	disc.bottom_radius = 1.0
	disc.height = 0.02
	_reach.mesh = disc
	_reach_mat = _mat(C_WINDUP, 1.0, true, 0.15)
	_reach.material_override = _reach_mat
	_reach.position = Vector3(0, 0.03, 0)
	add_child(_reach)
	for l in [_wolf_label, _wolf_pips]:
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.pixel_size = 0.005
		l.outline_size = 8
		l.no_depth_test = true
		_wolf.add_child(l)
	_wolf_label.font_size = 34
	_wolf_label.modulate = C_DIM
	_wolf_label.position = Vector3(0, 1.9, 0)
	_wolf_pips.font_size = 44
	_wolf_pips.modulate = C_STAGGER
	_wolf_pips.position = Vector3(0, 1.6, 0)

# --- Feedback ---------------------------------------------------------------

func floater(at: Vector3, text: String, color: Color, size := 48, life := 0.9) -> void:
	var l := Label3D.new()
	l.text = text
	l.font_size = size
	l.pixel_size = 0.005
	l.modulate = color
	l.outline_size = 10
	l.outline_modulate = Color(0, 0, 0, 0.9)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.position = at
	add_child(l)
	_floaters.append({ "l": l, "age": 0.0, "life": life })

func burst(at: Vector3, color: Color, amount: int) -> void:
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = amount
	p.lifetime = 0.45
	p.explosiveness = 1.0
	p.direction = Vector3(0, 1, 0)
	p.spread = 180.0
	p.initial_velocity_min = 2.5
	p.initial_velocity_max = 6.0
	p.gravity = Vector3(0, -9, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.0
	var sm := SphereMesh.new()
	sm.radius = 0.04
	sm.height = 0.08
	p.mesh = sm
	p.material_override = _mat(color, 3.0, true)
	p.position = at
	add_child(p)
	p.emitting = true
	get_tree().create_timer(1.0).timeout.connect(p.queue_free)

func _hitstop(ms: int) -> void:
	_hitstop_until = maxi(_hitstop_until, Time.get_ticks_msec() + ms)

## React to the fight's events with feedback.
func feedback(events: Array) -> void:
	var P := _last_p + Vector3(0, 2.4, 0)
	var W := _last_w + Vector3(0, 1.6, 0)
	for e in events:
		match e["type"]:
			"beat":
				_flash = 1.0
			"judged":
				var j: Dictionary = e["j"]
				if not j["perfect"] and e["action"] != "stance":
					floater(P + Vector3(0, 0.3, 0), "%s %d ms" % ["early" if j["offset_ms"] < 0 else "late", absi(roundi(j["offset_ms"]))], C_OFF, 36)
			"hit":
				var heavy: bool = e["action"] == "ground-strike"
				floater(W + Vector3(randf_range(-0.2, 0.2), 0.3, 0), str(int(e["damage"])), C_PERFECT if e["perfect"] else C_OFF, 72 if e["perfect"] else 48)
				if e["perfect"]:
					floater(W + Vector3(0, 0.8, 0), "STAGGERED" if e["staggered"] else ("PERFECT ×%d" % e["chain"] if e["chain"] > 1 else "PERFECT"), C_PERFECT, 40)
				burst(_last_w + Vector3(0, 0.9, 0), C_PERFECT if e["perfect"] else C_OFF, 26 if e["perfect"] else 10)
				_shake = maxf(_shake, 0.12 if heavy else (0.07 if e["perfect"] else 0.03))
				if e["perfect"]:
					_hitstop(110 if heavy else 70)
				_swing = 1.0
				_recoil = 1.0
			"whiff":
				floater(P, "out of reach", C_DIM, 32)
				_swing = 1.0
			"fumble":
				floater(P, "fumble — %s" % e["reason"], C_OFF, 34)
			"break":
				floater(W - Vector3(0, 0.9, 0), "break %d/3" % e["count"], C_STAGGER, 40)
			"stagger":
				floater(W + Vector3(0, 1.2, 0), "BROKEN — STAGGER", C_STAGGER, 64, 1.3)
				_shake = 0.2
				_hitstop(160)
			"parry":
				floater(P + Vector3(0, 0.4, 0), "PARRY  +10 Will", C_GUARD, 64)
				burst((_last_p + _last_w) / 2.0 + Vector3(0, 1.0, 0), C_GUARD, 40)
				_hitstop(120)
				_shake = 0.1
			"block":
				floater(P, "blocked −%d" % int(e["damage"]), C_GUARD, 40)
				_shake = 0.08
			"hurt":
				floater(P, "−%d" % int(e["damage"]), C_WINDUP, 64)
				_shake = 0.22
			"dodge":
				floater(P, "dodged", C_DIM, 36)
			"windup":
				_lunge = 0.0
			"stance":
				floater(_last_p + Vector3(0, 0.4, 0), "ANCHOR STANCE" if e["on"] else "stance off", C_STANCE, 38)
			"faint":
				floater(P, "FIELD FAINTS — no Will", C_WINDUP, 44)
			"no-will":
				floater(P, "not enough Will", C_OFF, 34)
			"wolf-down":
				floater(W + Vector3(0, 0.6, 0), "THE WOLF FALLS", C_RING, 64, 1.4)
				_shake = 0.15
			"wolf-up":
				floater(W + Vector3(0, 0.6, 0), "another comes out of the dark", C_DIM, 36, 1.4)

# --- Each frame ---------------------------------------------------------------

func _v3(v: Vector2, y := 0.0) -> Vector3:
	return Vector3(v.x, y, v.y)

## Draw a frame. t is the beat clock as heard.
func draw(f: Fight, t: float, dt: float, cam_input: Vector2) -> void:
	var stopped := Time.get_ticks_msec() < _hitstop_until
	if stopped and _frozen.is_empty():
		_frozen = { "p": f.p_pos, "w": f.w_pos }
	if not stopped:
		_frozen = {}
	var pp: Vector2 = _frozen.get("p", f.p_pos)
	var wp: Vector2 = _frozen.get("w", f.w_pos)
	_last_p = _v3(pp)
	_last_w = _v3(wp)

	# The Anchor.
	_player.position = _last_p
	_player.rotation.y = -f.p_facing - PI / 2.0
	_guard.visible = f.p_guard
	_aura.visible = f.p_stance
	_player_body_mat.albedo_color = Color(0.25, 0.2, 0.16) if f.p_down else (C_PLAYER.lerp(C_STANCE, 0.25) if f.p_stance else C_PLAYER)
	_player_label.text = "DOWN" if f.p_down else ("ANCHOR · fainted" if f.p_fainted else "ANCHOR")
	_swing = maxf(0.0, _swing - dt * 6.0)
	_saber.rotation.y = lerpf(0.0, 1.6, sin(_swing * PI)) if _swing > 0.0 else 0.0

	# The pulse ring: the outer ring closes on the base ring at the beat.
	var ph := fposmod((t - f.t0) / f.period, 1.0)
	for r in [_ring_base, _ring_close, _ring_band]:
		r.position = Vector3(_last_p.x, 0.05, _last_p.z)
	var ring_color := C_STANCE if f.p_stance else C_RING
	_flash = maxf(0.0, _flash - dt * 5.0)
	_ring_mat.albedo_color = Color(ring_color.lerp(Color.WHITE, _flash * 0.6), 0.55 + 0.45 * _flash)
	_ring_mat.emission = ring_color
	_ring_mat.emission_energy_multiplier = 1.0 + 3.0 * _flash
	_ring_base.scale = Vector3(1.0 + 0.12 * _flash, 0.05, 1.0 + 0.12 * _flash)
	var closing := 1.0 + 1.6 * (1.0 - ph)
	_ring_close.scale = Vector3(closing, 0.05, closing)
	_ring_close_mat.albedo_color = Color(ring_color, 0.15 + 0.7 * ph)
	_ring_close.visible = t >= f.t0 - f.period
	var band := f.window_ms / 1000.0 / f.period
	_ring_band.scale = Vector3(1.0 + band * 0.6, 0.05, 1.0 + band * 0.6)

	# The wolf.
	_wolf.visible = show_wolf
	_reach.visible = false
	if show_wolf:
		var mode := f.w_mode
		var to_p := pp - wp
		_wolf.position = _last_w
		_wolf.rotation.y = -to_p.angle() - PI / 2.0
		var glow := 0.0
		var body := C_WOLF
		if mode == "windup":
			var beats_left := f.w_strike_beat - (t - f.t0) / f.period
			glow = clampf(1.0 - beats_left / float(f.beast["telegraphBeats"]), 0.0, 1.0)
			body = C_WOLF.lerp(C_WINDUP, 0.3 + 0.7 * glow)
			_reach.visible = true
			_reach.position = Vector3(_last_w.x, 0.03, _last_w.z)
			var rr := float(f.beast["strikeReach"])
			_reach.scale = Vector3(rr, 1, rr)
			_reach_mat.albedo_color = Color(C_WINDUP, 0.08 + 0.22 * glow)
			# Crouch back before the bite; lunge on it.
			_wolf_head.position.y = 1.05 - 0.25 * glow
		else:
			_wolf_head.position.y = 1.05
		if mode == "stagger":
			body = C_STAGGER
			_wolf.rotation.z = sin(t * 30.0) * 0.12
		else:
			_wolf.rotation.z = 0.0
		if mode == "recover" and f.w_until - (t - f.t0) / f.period > float(f.beast["recoverBeats"]) - 0.5:
			_wolf.position += _v3(to_p.normalized() * 0.35)
		_recoil = maxf(0.0, _recoil - dt * 5.0)
		_wolf.position -= _v3(to_p.normalized() * 0.25 * _recoil)
		_wolf_mat.albedo_color = Color(body, 0.3 if mode == "down" else 1.0)
		_wolf_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if mode == "down" else BaseMaterial3D.TRANSPARENCY_DISABLED
		_wolf_mat.emission_energy_multiplier = 2.5 * glow
		_wolf.scale = Vector3(1, 0.4, 1) if mode == "down" else Vector3.ONE
		var molt := "first molt"
		var state := ""
		match mode:
			"stagger": state = " · STAGGERED"
			"windup": state = " · winding up"
			"down": state = " · down"
		_wolf_label.text = "%s · %s · %s%s" % [String(f.beast["name"]).to_upper(), String(f.beast["shape"]).capitalize(), molt, state]
		var pips := ""
		for i in f.breaks.needed:
			pips += "● " if i < f.breaks.count else "○ "
		_wolf_pips.text = pips.strip_edges() if mode != "down" else ""

	# Floaters rise and fade.
	for fl in _floaters.duplicate():
		fl["age"] += dt
		var l: Label3D = fl["l"]
		l.position.y += dt * 0.8
		l.modulate.a = 1.0 - fl["age"] / fl["life"]
		if fl["age"] > fl["life"]:
			l.queue_free()
			_floaters.erase(fl)

	_update_camera(dt, cam_input, show_wolf and f.w_mode != "down")

func _update_camera(dt: float, cam_input: Vector2, can_lock: bool) -> void:
	var focus := _last_p + Vector3(0, 1.3, 0)
	var back: Vector3
	if lock_on and can_lock:
		var to_w := (_last_w - _last_p)
		to_w.y = 0
		if to_w.length() < 0.1:
			to_w = Vector3(0, 0, -1)
		to_w = to_w.normalized()
		cam_yaw = atan2(-to_w.x, -to_w.z)
		back = -to_w
		focus = _last_p.lerp(_last_w, 0.35) + Vector3(0, 1.1, 0)
	else:
		cam_yaw -= cam_input.x * dt * 2.6
		cam_pitch = clampf(cam_pitch - cam_input.y * dt * 1.6, -1.1, -0.15)
		back = Vector3(sin(cam_yaw), 0, cos(cam_yaw))
	var dist := 6.2
	var want := _last_p + back * dist * cos(cam_pitch) + Vector3(0, 1.4 + dist * sin(-cam_pitch), 0)
	var k := 1.0 - exp(-dt * 7.0)
	_cam_pos = _cam_pos.lerp(want, k)
	_cam_look = _cam_look.lerp(focus, k)
	_shake = maxf(0.0, _shake - dt * 0.8)
	var jitter := Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * _shake
	camera.position = _cam_pos + jitter
	if camera.position.distance_to(_cam_look) > 0.01:
		camera.look_at(_cam_look + jitter * 0.5, Vector3.UP)

## The ground-plane direction the stick means, given the camera.
func move_from_stick(stick: Vector2) -> Vector2:
	if stick.length() < 0.05:
		return Vector2.ZERO
	var fwd := Vector2(-sin(cam_yaw), -cos(cam_yaw))
	var right := Vector2(cos(cam_yaw), -sin(cam_yaw))
	return (right * stick.x + fwd * -stick.y).limit_length(1.0)

func snap_camera() -> void:
	_cam_pos = _last_p + Vector3(0, 4, 6)
	_cam_look = _last_p
