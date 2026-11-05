## The 3D room: a chamber in the Cumberland Cut built from KayKit Dungeon pieces, the Anchor
## (KayKit Knight) and the cut-wolf (Quaternius Wolf), animated; telegraphs, hit feedback,
## hit-stop, the parry's slow motion, a third-person camera with lock-on.
## Art: KayKit (Kay Lousberg) and Quaternius, both CC0. Placeholder for the game's own art.
class_name World
extends Node3D

const C_STANCE := Color(0.95, 0.68, 0.25)
const C_WINDUP := Color(1.0, 0.22, 0.12)
const C_STAGGER := Color(1.0, 0.85, 0.35)
const C_HIT := Color(1.0, 1.0, 1.0)
const C_GUARD := Color(0.55, 0.8, 1.0)
const C_TEXT := Color(0.95, 0.92, 0.85)
const C_DIM := Color(0.7, 0.66, 0.6)
const C_GOLD := Color(1.0, 0.8, 0.35)
const WOLF_SCALE := 0.62
const WA := "AnimalArmature|"

var camera := Camera3D.new()
var lock_on := true
var cam_yaw := 0.0
var cam_pitch := -0.32
var show_wolf := true

var _player: Node3D
var _p_anim: AnimationPlayer
var _p_meshes: Array = []
var _p_oneshot_until := 0.0
var _p_current := ""
var _wolf: Node3D
var _w_anim: AnimationPlayer
var _w_meshes: Array = []
var _w_oneshot_until := 0.0
var _w_current := ""
var _overlay_wolf := StandardMaterial3D.new()
var _overlay_player := StandardMaterial3D.new()
var _wolf_flash := 0.0
var _player_flash := 0.0
var _aura := MeshInstance3D.new()
var _telegraph := MeshInstance3D.new()
var _telegraph_mat := StandardMaterial3D.new()
var _lock_ring := MeshInstance3D.new()
var _cue_ring := MeshInstance3D.new()
var _cue_target := MeshInstance3D.new()
var _cue_mat := StandardMaterial3D.new()
var _wolf_label := Label3D.new()
var _alert := Label3D.new()
var _torches: Array = []
var _floaters: Array = []
var _shake := 0.0
var _cam_pos := Vector3(0, 4, 8)
var _cam_look := Vector3.ZERO
var _hitstop_until := 0
var _slowmo_until := 0
var _clock := 0.0

func _ready() -> void:
	_build_environment()
	_build_chamber()
	_build_player()
	_build_wolf()
	_build_markers()
	add_child(camera)
	camera.fov = 60.0
	camera.near = 0.05
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
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m

func _piece(name: String, pos: Vector3, rot_deg := 0.0, scale := 1.0) -> Node3D:
	var n: Node3D = load("res://game/assets/kaykit_dungeon/%s.glb" % name).instantiate()
	n.position = pos
	n.rotation_degrees.y = rot_deg
	n.scale = Vector3.ONE * scale
	add_child(n)
	return n

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.018, 0.02)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.42, 0.45, 0.6)
	env.ambient_light_energy = 0.32
	env.fog_enabled = true
	env.fog_light_color = Color(0.06, 0.05, 0.06)
	env.fog_density = 0.022
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 0.9
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_bloom = 0.08
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.08
	env.adjustment_saturation = 1.1
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	# Moonlight through the broken roof of the Cut: cool, from above, casting the shadows.
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-62, -35, 0)
	moon.light_color = Color(0.6, 0.68, 0.95)
	moon.light_energy = 0.4
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 40.0
	add_child(moon)

func _build_chamber() -> void:
	var a: Dictionary = Data.room["arena"]
	var hw := float(a["width"]) / 2.0 + 1.0
	var hd := float(a["depth"]) / 2.0 + 1.0
	# Floor: large stone tiles, a few broken by rocks.
	var x := -hw + 2.0
	var i := 0
	while x < hw:
		var z := -hd + 2.0
		while z < hd:
			_piece("floor_tile_large_rocks" if (i * 7) % 11 == 3 else "floor_tile_large", Vector3(x, 0, z), 90.0 * (i % 4))
			z += 4.0
			i += 1
		x += 4.0
	# The line runs through the chamber: ties and two rails.
	var tie := _mat(Color(0.22, 0.15, 0.1))
	var rail := _mat(Color(0.42, 0.4, 0.38))
	rail.metallic = 0.85
	rail.roughness = 0.3
	var tx := -hw
	while tx < hw:
		var b := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.3, 0.12, 2.4)
		b.mesh = bm
		b.position = Vector3(tx, 0.1, 0)
		b.material_override = tie
		add_child(b)
		tx += 0.8
	for rz in [-0.72, 0.72]:
		var r := MeshInstance3D.new()
		var rm := BoxMesh.new()
		rm.size = Vector3(hw * 2.0, 0.12, 0.1)
		r.mesh = rm
		r.position = Vector3(0, 0.2, rz)
		r.material_override = rail
		add_child(r)
	# Walls on the long sides, with pillars, arches, and torches.
	var kinds := ["wall", "wall_pillar", "wall_cracked", "wall_arched", "wall", "wall_broken", "wall_pillar"]
	var wx := -hw + 2.0
	var k := 0
	while wx < hw:
		for side in [-1, 1]:
			var kind: String = kinds[(k + (2 if side > 0 else 0)) % kinds.size()]
			if kind == "wall_arched" and absf(wx) < 4.0:
				kind = "wall"
			_piece(kind, Vector3(wx, 0, side * hd), 0.0 if side < 0 else 180.0)
			if k % 2 == 1:
				var t := _piece("torch_mounted", Vector3(wx, 2.4, side * (hd - 0.45)), 0.0 if side < 0 else 180.0)
				var light := OmniLight3D.new()
				light.light_color = Color(1.0, 0.6, 0.3)
				light.light_energy = 1.5
				light.omni_range = 7.5
				light.omni_attenuation = 1.6
				light.shadow_enabled = false
				light.position = Vector3(0, 0.6, 0.25)
				t.add_child(light)
				_torches.append(light)
		wx += 4.0
		k += 1
	# The ends of the chamber: where the line enters and leaves, dark arches.
	for side in [-1, 1]:
		var ez := -hd + 2.0
		while ez < hd:
			var kind := "wall_arched" if absf(ez) < 2.5 else "wall"
			_piece(kind, Vector3(side * hw, 0, ez), 90.0 if side < 0 else -90.0)
			ez += 4.0
	# Props along the walls, kept out of the fighting floor.
	_piece("pillar_decorated", Vector3(-hw + 1.6, 0, -hd + 1.6))
	_piece("pillar", Vector3(hw - 1.6, 0, hd - 1.6))
	_piece("barrel_large", Vector3(-6.5, 0, hd - 1.3), 20.0, 0.7)
	_piece("barrel_small_stack", Vector3(7.5, 0, -hd + 1.2), 0.0, 0.8)
	_piece("crates_stacked", Vector3(hw - 2.0, 0, -hd + 1.8), 15.0, 0.8)
	_piece("rubble_half", Vector3(2.0, 0, hd - 0.8), 180.0, 0.6)
	_piece("banner_patternA_red", Vector3(-2.0, 0.6, -hd + 0.55), 0.0)
	_piece("banner_patternA_red", Vector3(6.0, 0.6, hd - 0.55), 180.0)

func _build_player() -> void:
	_player = load("res://game/assets/kaykit/Knight.glb").instantiate()
	add_child(_player)
	for n in ["2H_Sword", "Rectangle_Shield", "Spike_Shield", "1H_Sword_Offhand", "Badge_Shield"]:
		var x := _player.find_child(n, true, false)
		if x:
			x.visible = false
	_p_anim = _player.find_child("AnimationPlayer", true, false)
	for loop in ["Idle", "Running_A", "Running_Strafe_Left", "Running_Strafe_Right", "Walking_Backwards", "Walking_A", "Blocking", "Death_A_Pose"]:
		if _p_anim.has_animation(loop):
			_p_anim.get_animation(loop).loop_mode = Animation.LOOP_LINEAR
	_p_meshes = _player.find_children("*", "MeshInstance3D", true, false)
	_overlay_player = _mat(C_HIT, 2.0, true, 0.0)
	for m in _p_meshes:
		m.material_overlay = _overlay_player
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.7
	cyl.bottom_radius = 0.95
	cyl.height = 2.2
	_aura.mesh = cyl
	_aura.position = Vector3(0, 1.1, 0)
	_aura.material_override = _mat(C_STANCE, 1.4, true, 0.09)
	_aura.visible = false
	_player.add_child(_aura)

func _build_wolf() -> void:
	_wolf = load("res://game/assets/quaternius/Wolf.glb").instantiate()
	_wolf.scale = Vector3.ONE * WOLF_SCALE
	add_child(_wolf)
	_w_anim = _wolf.find_child("AnimationPlayer", true, false)
	for loop in ["Idle", "Walk", "Gallop", "Idle_2_HeadLow", "Idle_2"]:
		if _w_anim.has_animation(WA + loop):
			_w_anim.get_animation(WA + loop).loop_mode = Animation.LOOP_LINEAR
	_w_meshes = _wolf.find_children("*", "MeshInstance3D", true, false)
	_overlay_wolf = _mat(C_WINDUP, 2.0, true, 0.0)
	for m in _w_meshes:
		m.material_overlay = _overlay_wolf
	for l in [_wolf_label, _alert]:
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.pixel_size = 0.004
		l.outline_size = 10
		l.outline_modulate = Color(0, 0, 0, 0.85)
		add_child(l)
	_wolf_label.font_size = 28
	_wolf_label.fixed_size = true
	_wolf_label.pixel_size = 0.0012
	_wolf_label.modulate = C_DIM
	_alert.font_size = 120
	_alert.text = "!"
	_alert.modulate = C_WINDUP
	_alert.visible = false

func _build_markers() -> void:
	# The bite's reach, on the ground in front of the wolf while it winds up.
	var disc := CylinderMesh.new()
	disc.top_radius = 1.0
	disc.bottom_radius = 1.0
	disc.height = 0.02
	disc.radial_segments = 48
	_telegraph.mesh = disc
	_telegraph_mat = _mat(C_WINDUP, 1.5, true, 0.2)
	_telegraph.material_override = _telegraph_mat
	_telegraph.visible = false
	add_child(_telegraph)
	# Lock-on: a thin ring under the target.
	for pair in [[_lock_ring, 0.95, 1.0, _mat(Color(1, 0.4, 0.3), 1.5, true, 0.6)], [_cue_ring, 0.95, 1.02, null], [_cue_target, 0.9, 1.0, _mat(C_GOLD, 2.0, true, 0.8)]]:
		var mi: MeshInstance3D = pair[0]
		var t := TorusMesh.new()
		t.inner_radius = pair[1]
		t.outer_radius = pair[2]
		t.rings = 64
		mi.mesh = t
		mi.scale = Vector3(1, 0.04, 1)
		if pair[3] != null:
			mi.material_override = pair[3]
		mi.visible = false
		add_child(mi)
	_cue_mat = _mat(C_GOLD, 2.5, true, 0.9)
	_cue_ring.material_override = _cue_mat

# --- Animation ----------------------------------------------------------------

func _play(ap: AnimationPlayer, name: String, speed := 1.0, blend := 0.12) -> void:
	if not ap.has_animation(name):
		return
	ap.play(name, blend, speed)

## A one-shot from the fight (a swing, a dodge, a bite): it holds the body until it ends.
func anim_event(e: Dictionary) -> void:
	var speed := float(e.get("speed", 1.0))
	if e["who"] == "player":
		var name: String = e["name"]
		_play(_p_anim, name, speed, 0.06)
		_p_current = name
		var len := _p_anim.get_animation(name).length if _p_anim.has_animation(name) else 0.4
		_p_oneshot_until = _clock + len / speed * (0.95 if not name.begins_with("Death") else 99.0)
	else:
		var name: String = WA + String(e["name"])
		if e["name"] == "HitReact":
			name = WA + ("Idle_HitReact_Left" if randf() < 0.5 else "Idle_HitReact_Right")
		_play(_w_anim, name, speed, 0.06)
		_w_current = name
		var len := _w_anim.get_animation(name).length if _w_anim.has_animation(name) else 0.4
		_w_oneshot_until = _clock + len / speed * (0.9 if e["name"] != "Death" else 99.0)

func _loop(ap: AnimationPlayer, name: String, speed := 1.0, is_wolf := false) -> void:
	var current := _w_current if is_wolf else _p_current
	if current == name and ap.is_playing():
		ap.speed_scale = speed
		return
	_play(ap, name, 1.0, 0.18)
	ap.speed_scale = speed
	if is_wolf:
		_w_current = name
	else:
		_p_current = name

# --- Feedback ---------------------------------------------------------------

func floater(at: Vector3, text: String, color: Color, size := 56, life := 0.9, rise := 0.9) -> void:
	var l := Label3D.new()
	l.text = text
	l.font_size = size
	l.pixel_size = 0.004
	l.modulate = color
	l.outline_size = 12
	l.outline_modulate = Color(0, 0, 0, 0.85)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.position = at + Vector3(randf_range(-0.25, 0.25), 0, 0)
	add_child(l)
	_floaters.append({ "l": l, "age": 0.0, "life": life, "rise": rise })

func burst(at: Vector3, color: Color, amount: int, speed := 5.0) -> void:
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = amount
	p.lifetime = 0.45
	p.explosiveness = 1.0
	p.direction = Vector3(0, 1, 0)
	p.spread = 180.0
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.gravity = Vector3(0, -12, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.2
	var sm := SphereMesh.new()
	sm.radius = 0.035
	sm.height = 0.07
	p.mesh = sm
	p.material_override = _mat(color, 4.0, true)
	p.position = at
	add_child(p)
	p.emitting = true
	get_tree().create_timer(1.2, true, false, true).timeout.connect(p.queue_free)

func _ring_wave(at: Vector3, color: Color, radius: float) -> void:
	var mi := MeshInstance3D.new()
	var t := TorusMesh.new()
	t.inner_radius = 0.9
	t.outer_radius = 1.0
	mi.mesh = t
	mi.scale = Vector3(0.2, 0.05, 0.2)
	mi.position = at + Vector3(0, 0.08, 0)
	var m := _mat(color, 3.0, true, 0.9)
	mi.material_override = m
	add_child(mi)
	var tw: Tween = create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3(radius, 0.05, radius), 0.35).set_ease(Tween.EASE_OUT)
	tw.tween_property(m, "albedo_color:a", 0.0, 0.35)
	tw.chain().tween_callback(mi.queue_free)

## Freeze time for a moment: the weight of a hit.
func hitstop(seconds: float, scale := 0.05) -> void:
	Engine.time_scale = scale
	_hitstop_until = Time.get_ticks_msec() + int(seconds * 1000.0)

func slowmo(seconds: float, scale: float) -> void:
	Engine.time_scale = scale
	_slowmo_until = Time.get_ticks_msec() + int(seconds * 1000.0)

func _v3(v: Vector2, y := 0.0) -> Vector3:
	return Vector3(v.x, y, v.y)

## React to the fight's events with feedback.
func feedback(f: Fight, events: Array) -> void:
	var feel: Dictionary = Data.room["feel"]
	var P := _v3(f.p_pos, 2.3)
	var W := _v3(f.w_pos, 1.6)
	for e in events:
		match e["type"]:
			"anim":
				anim_event(e)
			"hit":
				var heavy: bool = e["heavy"] or e["pattern"]
				floater(W + Vector3(0, 0.2, 0), str(int(e["damage"])), C_GOLD if e["pattern"] else (C_STAGGER if e["staggered"] else C_TEXT), 84 if heavy else 60)
				burst(_v3(f.w_pos, 0.9), C_GOLD if heavy else C_HIT, 30 if heavy else 14, 7.0 if heavy else 5.0)
				_wolf_flash = 1.0
				_shake = maxf(_shake, float(feel["shakeOnHit"]) * (2.0 if heavy else 1.0))
				hitstop(float(feel["heavyHitstop"]) if heavy else float(feel["hitstop"]))
			"whiff":
				pass
			"quake":
				_ring_wave(_v3(e["at"]), C_STANCE, 2.6)
				burst(_v3(e["at"], 0.1), Color(0.7, 0.6, 0.5), 24, 4.0)
				_shake = maxf(_shake, 0.12)
			"break":
				floater(W + Vector3(0, 0.9, 0), "BREAK %d/%d" % [e["count"], e["needed"]], C_STAGGER, 48)
			"stagger":
				floater(W + Vector3(0, 1.2, 0), "BROKEN", C_STAGGER, 90, 1.3)
				_ring_wave(_v3(f.w_pos), C_STAGGER, 3.0)
				_shake = 0.2
			"parry":
				floater(P + Vector3(0, 0.3, 0), "PARRY", C_GUARD, 96, 1.0)
				burst((_v3(f.p_pos, 1.2) + _v3(f.w_pos, 1.2)) / 2.0, C_GUARD, 50, 8.0)
				_ring_wave(_v3(f.p_pos), C_GUARD, 3.5)
				_shake = 0.12
				slowmo(float(feel["parrySlowmo"]), 0.3)
			"block":
				floater(P, "BLOCKED  −%d" % int(e["damage"]), C_GUARD, 48)
				burst(_v3(f.p_pos, 1.2) + _v3(Vector2.from_angle(f.p_facing) * 0.5), C_GUARD, 12, 4.0)
				_shake = 0.07
			"hurt":
				floater(P, "−%d" % int(e["damage"]), C_WINDUP, 80)
				_player_flash = 1.0
				_shake = float(feel["shakeOnHurt"])
				hitstop(0.08)
			"evade":
				floater(P, "EVADED" if e["how"] == "dodged" else "MISSED", C_DIM, 44)
			"windup":
				_alert.visible = true
			"stance":
				floater(P - Vector3(0, 0.6, 0), "ANCHOR STANCE" if e["on"] else "stance off", C_STANCE, 46)
			"faint":
				floater(P, "THE FIELD FAINTS", C_WINDUP, 56)
			"no-will":
				floater(P, "not enough Will", C_DIM, 40)
			"not-ready":
				floater(P, "%s is not ready" % e["what"], C_DIM, 40)
			"pattern-locked":
				floater(P, "the Pattern needs a perfect Hold first", C_DIM, 40)
			"pattern-start":
				floater(P + Vector3(0, 0.5, 0), String(e["name"]).to_upper(), C_GOLD, 96, 1.4)
				_ring_wave(_v3(f.p_pos), C_GOLD, 4.0)
			"pattern-cue":
				if e["hit"]:
					burst(_v3(f.p_pos, 0.2), C_GOLD, 16, 4.0)
				else:
					floater(P, "%s" % ("too early" if e["offset_ms"] < 0 else "late"), C_DIM, 44)
			"pattern-done":
				floater(W + Vector3(0, 1.0, 0), "%d" % int(e["damage"]), C_GOLD, 140, 1.6, 0.6)
				_ring_wave(_v3(f.w_pos), C_GOLD, 5.0)
				burst(_v3(f.w_pos, 1.0), C_GOLD, 80, 10.0)
				_shake = 0.3
				hitstop(0.22)
			"pattern-fizzle":
				floater(P + Vector3(0, 0.4, 0), "THE PATTERN FIZZLES", C_DIM, 64, 1.2)
			"wolf-down":
				floater(W + Vector3(0, 0.6, 0), "THE WOLF FALLS", C_TEXT, 80, 1.6)
				_shake = 0.15
			"wolf-up":
				floater(W + Vector3(0, 0.6, 0), "another comes out of the dark", C_DIM, 44, 1.6)

# --- Each frame ---------------------------------------------------------------

## Draw a frame. `dt` is real time (unscaled), for the camera and the feedback.
func draw(f: Fight, dt: float, cam_input: Vector2, move_input: Vector2) -> void:
	_clock += dt * Engine.time_scale
	var now_ms := Time.get_ticks_msec()
	if now_ms > _hitstop_until and now_ms > _slowmo_until and Engine.time_scale != 1.0:
		Engine.time_scale = 1.0
	elif now_ms > _hitstop_until and now_ms <= _slowmo_until:
		Engine.time_scale = 0.3

	# The Anchor.
	_player.position = _v3(f.p_pos)
	_player.rotation.y = _yaw(f.p_facing)
	_aura.visible = f.p_stance
	_player_flash = maxf(0.0, _player_flash - dt * 6.0)
	_overlay_player.albedo_color = Color(C_WINDUP, 0.45 * _player_flash)
	if _clock >= _p_oneshot_until:
		match f.p_state:
			"free":
				if f.p_block_held and not f.p_fainted:
					_loop(_p_anim, "Blocking")
				elif move_input.length() > 0.1:
					var rel := angle_difference(f.p_facing, move_input.angle())
					if f.p_lock and f.w_state not in ["down", "absent"] and absf(rel) > PI * 0.3:
						if absf(rel) > PI * 0.75:
							_loop(_p_anim, "Walking_Backwards", 1.3)
						else:
							_loop(_p_anim, "Running_Strafe_Right" if rel > 0 else "Running_Strafe_Left", 1.0)
					else:
						_loop(_p_anim, "Running_A", 1.0 if not f.p_stance else 0.8)
				else:
					_loop(_p_anim, "Idle")
			"down":
				pass

	# The wolf.
	_wolf.visible = show_wolf and f.w_state != "absent"
	_wolf.position = _v3(f.w_pos)
	_wolf.rotation.y = _yaw(f.w_facing)
	_wolf_flash = maxf(0.0, _wolf_flash - dt * 7.0)
	var glow := 0.0
	if f.w_state == "windup":
		glow = clampf(f.w_timer / maxf(0.01, f.w_duration), 0.0, 1.0)
	var overlay := Color(C_WINDUP, 0.6 * glow * glow)
	if f.w_state == "stagger":
		overlay = Color(C_STAGGER, 0.25 + 0.15 * sin(_clock * 18.0))
	if _wolf_flash > 0.0:
		overlay = Color(C_HIT, 0.7 * _wolf_flash)
	_overlay_wolf.albedo_color = overlay
	if _clock >= _w_oneshot_until:
		match f.w_state:
			"prowl": _loop(_w_anim, WA + "Walk", 1.2, true)
			"approach": _loop(_w_anim, WA + "Gallop", 1.3, true)
			"windup": _loop(_w_anim, WA + "Idle_2_HeadLow", 0.6, true)
			"recover", "idle", "pinned": _loop(_w_anim, WA + "Idle", 1.0, true)
			"stagger": _loop(_w_anim, WA + "Idle_2_HeadLow", 0.3, true)
			"flinch": _loop(_w_anim, WA + "Idle", 1.0, true)
	if f.w_state == "stagger":
		_wolf.rotation.z = sin(_clock * 22.0) * 0.06
	else:
		_wolf.rotation.z = 0.0

	# The wind-up: the reach on the ground and a "!" over the head.
	_telegraph.visible = _wolf.visible and f.w_state == "windup"
	_alert.visible = _telegraph.visible
	if _telegraph.visible:
		var reach := float(f.w_attack["range"]) + float(f.w_attack.get("lunge", 0.0)) * 0.5
		var fwd := Vector2.from_angle(f.w_facing)
		var c := f.w_pos + fwd * reach * 0.5
		_telegraph.position = _v3(c, 0.06)
		var r := reach * 0.55 * (0.6 + 0.4 * glow)
		_telegraph.scale = Vector3(r, 1, r)
		_telegraph_mat.albedo_color = Color(C_WINDUP, 0.12 + 0.3 * glow)
		_alert.position = _v3(f.w_pos, 2.0 + 0.15 * sin(_clock * 20.0))
		_alert.modulate = Color(C_WINDUP, 0.5 + 0.5 * glow)
	_wolf_label.visible = _wolf.visible and f.w_state != "down"
	_wolf_label.position = _v3(f.w_pos, 1.75)
	var state_text := ""
	match f.w_state:
		"stagger": state_text = "  ·  STAGGERED"
		"windup": state_text = "  ·  %s" % String(f.w_attack["name"]).to_upper()
	_wolf_label.text = "%s%s" % [String(f.beast["name"]).to_upper(), state_text]
	_lock_ring.visible = _wolf.visible and f.p_lock and f.w_state != "down"
	_lock_ring.position = _v3(f.w_pos, 0.07)
	_lock_ring.scale = Vector3(1.0 + 0.05 * sin(_clock * 5.0), 0.04, 1.0 + 0.05 * sin(_clock * 5.0))

	# The Pattern's cue: a gold ring closing on the Anchor at each beat of the chain.
	_cue_ring.visible = false
	_cue_target.visible = false
	if f.p_state == "pattern" and not f.chain.is_empty():
		var cues: Array = f.chain["cues"]
		var i: int = f.chain["next"]
		if i < cues.size():
			var left := float(cues[i]) - f.now
			var span := float(f.chain["period"])
			var k := clampf(left / span, 0.0, 1.5)
			_cue_ring.visible = true
			_cue_target.visible = true
			var s := 1.1 + 2.2 * k
			_cue_ring.scale = Vector3(s, 0.04, s)
			_cue_ring.position = _v3(f.p_pos, 0.08)
			_cue_target.position = _v3(f.p_pos, 0.08)
			_cue_target.scale = Vector3(1.1, 0.04, 1.1)
			_cue_mat.albedo_color = Color(C_GOLD, clampf(1.0 - k * 0.5, 0.3, 1.0))

	# Torches flicker.
	for idx in _torches.size():
		var l: OmniLight3D = _torches[idx]
		l.light_energy = 1.4 + 0.25 * sin(_clock * 9.0 + idx * 1.7) + 0.15 * sin(_clock * 23.0 + idx)

	# Floaters rise and fade (in real time, so they read during hit-stop).
	for fl in _floaters.duplicate():
		fl["age"] += dt
		var lb: Label3D = fl["l"]
		lb.position.y += dt * float(fl["rise"])
		var u: float = fl["age"] / fl["life"]
		lb.modulate.a = 1.0 - u * u
		if fl["age"] > fl["life"]:
			lb.queue_free()
			_floaters.erase(fl)

	_update_camera(dt, cam_input, f)

## Models face +Z; the fight's facing is the angle on the ground plane.
func _yaw(facing: float) -> float:
	var d := Vector2.from_angle(facing)
	return atan2(d.x, d.y)

func _update_camera(dt: float, cam_input: Vector2, f: Fight) -> void:
	var p := _v3(f.p_pos)
	var w := _v3(f.w_pos)
	var focus := p + Vector3(0, 1.4, 0)
	var want: Vector3
	var can_lock := show_wolf and f.w_state not in ["down", "absent"]
	if f.p_lock and can_lock:
		# Behind and over the shoulder, framing the Anchor and the wolf.
		var to_w := w - p
		to_w.y = 0
		if to_w.length() < 0.1:
			to_w = Vector3(0, 0, -1)
		to_w = to_w.normalized()
		var target_yaw := atan2(-to_w.x, -to_w.z)
		cam_yaw = lerp_angle(cam_yaw, target_yaw, 1.0 - exp(-dt * 5.0))
		var back := Vector3(sin(cam_yaw), 0, cos(cam_yaw))
		var side := Vector3(cos(cam_yaw), 0, -sin(cam_yaw))
		var d := clampf(p.distance_to(w), 2.0, 8.0)
		want = p + back * (5.0 + d * 0.25) + side * 1.2 + Vector3(0, 2.8 + d * 0.12, 0)
		focus = p.lerp(w, 0.45) + Vector3(0, 1.0, 0)
	else:
		cam_yaw -= cam_input.x * dt * 2.6
		cam_pitch = clampf(cam_pitch - cam_input.y * dt * 1.6, -1.0, 0.05)
		var back := Vector3(sin(cam_yaw), 0, cos(cam_yaw))
		var dist := 6.0
		want = p + back * dist * cos(cam_pitch) + Vector3(0, 1.6 + dist * sin(-cam_pitch), 0)
	var k := 1.0 - exp(-dt * 8.0)
	_cam_pos = _cam_pos.lerp(want, k)
	_cam_look = _cam_look.lerp(focus, 1.0 - exp(-dt * 10.0))
	_shake = maxf(0.0, _shake - dt * 0.9)
	var jitter := Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * _shake
	camera.position = _cam_pos + jitter
	if camera.position.distance_to(_cam_look) > 0.01:
		camera.look_at(_cam_look + jitter * 0.4, Vector3.UP)

## The ground-plane direction the stick means, given the camera.
func move_from_stick(stick: Vector2) -> Vector2:
	if stick.length() < 0.1:
		return Vector2.ZERO
	var fwd := Vector2(-sin(cam_yaw), -cos(cam_yaw))
	var right := Vector2(cos(cam_yaw), -sin(cam_yaw))
	return (right * stick.x + fwd * -stick.y).limit_length(1.0)

func snap_camera(f: Fight) -> void:
	cam_yaw = atan2(-(f.w_pos - f.p_pos).normalized().x, -(f.w_pos - f.p_pos).normalized().y)
	_cam_pos = _v3(f.p_pos) + Vector3(sin(cam_yaw), 0, cos(cam_yaw)) * 6.0 + Vector3(0, 3.2, 0)
	_cam_look = _v3(f.p_pos, 1.2)

func reset_feedback() -> void:
	Engine.time_scale = 1.0
	_hitstop_until = 0
	_slowmo_until = 0
	_p_oneshot_until = 0.0
	_w_oneshot_until = 0.0
	_p_current = ""
	_w_current = ""
	_play(_p_anim, "Idle", 1.0, 0.0)
	_play(_w_anim, WA + "Idle", 1.0, 0.0)
