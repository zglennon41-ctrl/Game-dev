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
const WOLF_SCALE := 0.8
const WA := "AnimalArmature|"

var camera := Camera3D.new()
var lock_on := true
var cam_yaw := 0.0
var cam_pitch := -0.32
var show_wolf := true
var portrait := false   # the character creator: the camera faces the character

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
	_build_effects()
	add_child(camera)
	camera.fov = 66.0
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
	env.ambient_light_color = Color(0.5, 0.44, 0.48)
	env.ambient_light_energy = 0.2
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
	moon.light_energy = 0.28
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
	_piece("barrel_large", Vector3(-6.5, 0, hd - 0.95), 20.0, 0.6)
	_piece("barrel_small_stack", Vector3(7.5, 0, -hd + 0.85), 0.0, 0.7)
	_piece("crates_stacked", Vector3(hw - 1.6, 0, -hd + 1.0), 15.0, 0.6)
	_piece("rubble_half", Vector3(2.0, 0, hd - 0.6), 180.0, 0.45)
	_piece("banner_patternA_red", Vector3(-2.0, 0.6, -hd + 0.55), 0.0)
	_piece("banner_patternA_red", Vector3(6.0, 0.6, hd - 0.55), 180.0)

func _build_player() -> void:
	build_hero(Fight.default_hero())

var _tint := Color(0, 0, 0, 0)
var _glow_light: OmniLight3D = null

## Dress the body the character creator chose: the body model, the weapon in the right hand
## (a shield in the left if it comes with one), and the blood where it shows.
func build_hero(hero: Dictionary) -> void:
	if _player:
		_player.queue_free()
	_player = load("res://game/assets/kaykit/%s.glb" % hero.get("body", "Knight")).instantiate()
	add_child(_player)
	for a in _player.find_children("*", "BoneAttachment3D", true, false):
		var n := String(a.name)
		a.visible = n.contains("Helmet") or n.contains("Hat") or n.contains("Cape") or n.contains("Hood")
	var skel: Skeleton3D = _player.find_child("Skeleton3D", true, false)
	var w: Dictionary = Data.by_id(Data.weapons, hero.get("weapon", "saber"))
	_sword = _attach(skel, "handslot.r", "res://game/assets/kaykit/weapons/%s.gltf" % w["model"])
	if w.has("offhand"):
		_attach(skel, "handslot.l", "res://game/assets/kaykit/weapons/%s.gltf" % w["offhand"])
	_p_anim = _player.find_child("AnimationPlayer", true, false)
	for loop in ["Idle", "Running_A", "Running_Strafe_Left", "Running_Strafe_Right", "Walking_Backwards", "Walking_A", "Blocking", "Death_A_Pose", "1H_Ranged_Aiming", "2H_Ranged_Aiming", "Spellcasting"]:
		if _p_anim.has_animation(loop):
			_p_anim.get_animation(loop).loop_mode = Animation.LOOP_LINEAR
	_p_current = ""
	_p_meshes = _player.find_children("*", "MeshInstance3D", true, false)
	_overlay_player = _mat(C_HIT, 2.0, true, 0.0)
	for m in _p_meshes:
		m.material_overlay = _overlay_player
	_aura = MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.7
	cyl.bottom_radius = 0.95
	cyl.height = 2.2
	_aura.mesh = cyl
	_aura.position = Vector3(0, 1.1, 0)
	_aura.material_override = _mat(_shape_color(hero.get("shape", "anchor")), 1.4, true, 0.09)
	_aura.visible = false
	_player.add_child(_aura)
	_dress_blood(skel, hero.get("blood", ""))
	_measure_weapon()

func _attach(skel: Skeleton3D, bone: String, path: String) -> Node3D:
	var att := BoneAttachment3D.new()
	att.bone_name = bone
	skel.add_child(att)
	var model: Node3D = load(path).instantiate()
	att.add_child(model)
	return att

const SHAPE_COLORS := { "anchor": Color(0.95, 0.68, 0.25), "turn": Color(1.0, 0.42, 0.15), "cast": Color(0.55, 0.85, 1.0),
	"read": Color(0.85, 0.85, 1.0), "bind": Color(0.75, 0.45, 1.0), "make": Color(0.5, 1.0, 0.6) }

func _shape_color(shape: String) -> Color:
	return SHAPE_COLORS.get(shape, C_STANCE)

## Blood is always visible: horns, wings, a glow, scales, fur, or a people's colouring.
func _dress_blood(skel: Skeleton3D, blood_id: String) -> void:
	_tint = Color(0, 0, 0, 0)
	if _glow_light:
		_glow_light = null
	if blood_id == "":
		return
	var b: Dictionary = Data.by_id(Data.bloods, blood_id)
	var tints := { "ridgefolk": Color(0.55, 0.55, 0.6), "fogborn": Color(0.75, 0.8, 0.9), "mound-kin": Color(0.6, 0.35, 0.2),
		"greenwood": Color(0.3, 0.7, 0.3), "forgeborn": Color(0.25, 0.15, 0.1), "ironblooded": Color(0.3, 0.32, 0.4),
		"tidewater": Color(0.3, 0.6, 0.7), "nightfolk": Color(0.2, 0.1, 0.3), "dragon-blooded": Color(0.2, 0.55, 0.35), "fused": Color(0.45, 0.32, 0.2) }
	if tints.has(blood_id):
		_tint = Color(tints[blood_id], 0.22)
	match b.get("look", ""):
		"horns":
			var head := BoneAttachment3D.new()
			head.bone_name = "head"
			skel.add_child(head)
			for side in [-1, 1]:
				var horn := MeshInstance3D.new()
				var cone := CylinderMesh.new()
				cone.top_radius = 0.0
				cone.bottom_radius = 0.09
				cone.height = 0.45
				horn.mesh = cone
				horn.position = Vector3(side * 0.28, 0.95, 0.05)
				horn.rotation_degrees = Vector3(-20, 0, -side * 25)
				horn.material_override = _mat(Color(0.18, 0.1, 0.1))
				head.add_child(horn)
		"wings":
			var chest := BoneAttachment3D.new()
			chest.bone_name = "chest"
			skel.add_child(chest)
			for side in [-1, 1]:
				var wing := MeshInstance3D.new()
				var pm := PrismMesh.new()
				pm.size = Vector3(1.1, 1.3, 0.05)
				wing.mesh = pm
				wing.position = Vector3(side * 0.55, 0.45, -0.35)
				wing.rotation_degrees = Vector3(0, side * 25, side * 65)
				wing.material_override = _mat(Color(0.92, 0.9, 0.85))
				chest.add_child(wing)
		"glow":
			_tint = Color(1.0, 0.85, 0.5, 0.18)
			_glow_light = OmniLight3D.new()
			_glow_light.light_color = Color(1.0, 0.85, 0.55)
			_glow_light.light_energy = 0.8
			_glow_light.omni_range = 3.0
			_glow_light.position = Vector3(0, 1.4, 0)
			_player.add_child(_glow_light)
		"fur":
			var head2 := BoneAttachment3D.new()
			head2.bone_name = "head"
			skel.add_child(head2)
			for side in [-1, 1]:
				var ear := MeshInstance3D.new()
				var pm2 := PrismMesh.new()
				pm2.size = Vector3(0.22, 0.3, 0.08)
				ear.mesh = pm2
				ear.position = Vector3(side * 0.3, 1.05, 0.0)
				ear.material_override = _mat(Color(0.4, 0.28, 0.18))
				head2.add_child(ear)

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

var _trail := MeshInstance3D.new()
var _trail_mesh := ImmediateMesh.new()
var _trail_pts: Array = []
var _sword: Node3D
var _sword_a := Vector3.ZERO
var _sword_b := Vector3.ZERO
var _vignette := ColorRect.new()
var _vig_tint := Color(0, 0, 0, 0)

const VIGNETTE := """
shader_type canvas_item;
uniform vec4 tint : source_color = vec4(0.0);
uniform float base = 0.42;
void fragment() {
	vec2 uv = UV - 0.5;
	float d = length(uv * vec2(1.5, 1.0));
	float v = smoothstep(0.38, 0.95, d);
	COLOR = vec4(tint.rgb * tint.a, v * base + tint.a * smoothstep(0.2, 0.9, d) * 0.8);
}
"""

## The sword trail, the screen's edge, and the effects that go with hits.
func _build_effects() -> void:
	_trail.mesh = _trail_mesh
	var tm := StandardMaterial3D.new()
	tm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	tm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	tm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	tm.cull_mode = BaseMaterial3D.CULL_DISABLED
	tm.vertex_color_use_as_albedo = true
	_trail.material_override = tm
	_trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_trail)
	var layer := CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	_vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = VIGNETTE
	var sm := ShaderMaterial.new()
	sm.shader = sh
	_vignette.material = sm
	layer.add_child(_vignette)

## Where the blade is: two points along its length, from the weapon mesh's own bounds.
func _measure_weapon() -> void:
	if not _sword:
		return
	var ms := _sword.find_children("*", "MeshInstance3D", true, false)
	if ms.size() == 0:
		return
	var mi: MeshInstance3D = ms[0]
	var box := mi.get_aabb()
	var axis := 0
	for i in 3:
		if box.size[i] > box.size[axis]:
			axis = i
	var lo := box.get_center()
	var hi := box.get_center()
	lo[axis] = box.position[axis] + box.size[axis] * 0.35
	hi[axis] = box.position[axis] + box.size[axis] * 1.0
	var rel := _sword.global_transform.affine_inverse() * mi.global_transform
	_sword_a = rel * lo
	_sword_b = rel * hi

func _update_trail(swinging: bool, dt: float) -> void:
	if _sword and swinging:
		var t := _sword.global_transform
		_trail_pts.push_front({ "a": t * _sword_a, "b": t * _sword_b, "age": 0.0 })
	for p in _trail_pts:
		p["age"] += dt
	while _trail_pts.size() > 0 and (_trail_pts.back()["age"] > 0.14 or _trail_pts.size() > 14):
		_trail_pts.pop_back()
	_trail_mesh.clear_surfaces()
	if _trail_pts.size() < 2:
		return
	_trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	for p in _trail_pts:
		var a := 1.0 - float(p["age"]) / 0.14
		_trail_mesh.surface_set_color(Color(1.0, 0.92, 0.75, 0.55 * a))
		_trail_mesh.surface_add_vertex(p["a"])
		_trail_mesh.surface_set_color(Color(1.0, 0.95, 0.85, 0.85 * a))
		_trail_mesh.surface_add_vertex(p["b"])
	_trail_mesh.surface_end()

func impact(at: Vector3, color: Color, size := 0.7) -> void:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.5
	sm.height = 1.0
	mi.mesh = sm
	var m := _mat(color, 4.0, true, 0.9)
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m
	mi.position = at
	mi.scale = Vector3.ONE * size * 0.3
	add_child(mi)
	var tw: Tween = create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3.ONE * size, 0.12).set_ease(Tween.EASE_OUT)
	tw.tween_property(m, "albedo_color:a", 0.0, 0.14)
	tw.chain().tween_callback(mi.queue_free)

func dust(at: Vector3, amount := 18) -> void:
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = amount
	p.lifetime = 0.6
	p.explosiveness = 0.9
	p.direction = Vector3(0, 1, 0)
	p.spread = 80.0
	p.initial_velocity_min = 0.8
	p.initial_velocity_max = 2.2
	p.gravity = Vector3(0, -1.5, 0)
	p.damping_min = 2.0
	p.damping_max = 4.0
	p.scale_amount_min = 1.0
	p.scale_amount_max = 2.5
	var sm := SphereMesh.new()
	sm.radius = 0.06
	sm.height = 0.12
	p.mesh = sm
	p.material_override = _mat(Color(0.55, 0.47, 0.4), 0.0, true, 0.5)
	p.position = at
	add_child(p)
	p.emitting = true
	get_tree().create_timer(1.2, true, false, true).timeout.connect(p.queue_free)

func flash_screen(color: Color, strength: float) -> void:
	_vig_tint = Color(color, maxf(_vig_tint.a, strength))

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
		# Play the animation at the speed that fits the action's real timing, so the blade
		# lands on the frame the hit lands.
		if e.has("duration") and _p_anim.has_animation(name):
			speed = clampf(_p_anim.get_animation(name).length / float(e["duration"]) * 0.9, 0.7, 2.6)
		_p_anim.speed_scale = 1.0
		_play(_p_anim, name, speed, 0.05)
		_p_current = name
		var len := _p_anim.get_animation(name).length if _p_anim.has_animation(name) else 0.4
		_p_oneshot_until = _clock + len / speed * (0.95 if not name.begins_with("Death") else 99.0)
	else:
		var name: String = WA + String(e["name"])
		if e["name"] == "HitReact":
			name = WA + ("Idle_HitReact_Left" if randf() < 0.5 else "Idle_HitReact_Right")
		_w_anim.speed_scale = 1.0
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
	l.fixed_size = true
	l.pixel_size = 0.0009
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

var _ward: MeshInstance3D = null
var _ward_at := Vector3.ZERO
var _tether := MeshInstance3D.new()
var _tether_mesh := ImmediateMesh.new()
var _fire: CPUParticles3D = null

func _tracer(from: Vector3, to: Vector3, hit: bool) -> void:
	var im := ImmediateMesh.new()
	var mi := MeshInstance3D.new()
	mi.mesh = im
	var m := _mat(Color(1.0, 0.9, 0.6), 4.0, true, 0.9)
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	im.surface_add_vertex(from)
	im.surface_add_vertex(to)
	im.surface_end()
	add_child(mi)
	impact(from, Color(1.0, 0.85, 0.5), 0.5)
	if hit:
		impact(to, Color(1.0, 0.9, 0.7), 0.6)
	var tw: Tween = create_tween()
	tw.tween_property(m, "albedo_color:a", 0.0, 0.12)
	tw.tween_callback(mi.queue_free)

## The first time: the field wakes. A wave of the Shape's colour, and the screen breathes.
func field_wakes(f: Fight, hero: Dictionary) -> void:
	var c := _shape_color(hero.get("shape", "anchor"))
	_ring_wave(_v3(f.p_pos), c, 6.0)
	burst(_v3(f.p_pos, 1.0), c, 80, 7.0)
	impact(_v3(f.p_pos, 1.2), c, 2.4)
	flash_screen(c, 0.7)
	floater(_v3(f.p_pos, 3.0), "YOUR FIELD WAKES", c, 96, 2.2, 0.4)
	slowmo(0.6, 0.25)

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
				floater(W + Vector3(0, 0.2, 0), ("%d!" if e.get("crit", false) else "%d") % int(e["damage"]), C_GOLD if e["pattern"] else (C_STAGGER if e["staggered"] else (Color(0.85, 0.85, 1.0) if e.get("crit", false) else C_TEXT)), 84 if heavy or e.get("crit", false) else 60)
				burst(_v3(f.w_pos, 0.9), C_GOLD if heavy else C_HIT, 30 if heavy else 14, 7.0 if heavy else 5.0)
				impact(_v3(f.w_pos, 0.9) + _v3((f.p_pos - f.w_pos).normalized() * 0.4), C_GOLD if heavy else C_HIT, 1.1 if heavy else 0.7)
				_wolf_flash = 1.0
				_shake = maxf(_shake, float(feel["shakeOnHit"]) * (2.0 if heavy else 1.0))
				hitstop(float(feel["heavyHitstop"]) if heavy else float(feel["hitstop"]))
			"whiff":
				pass
			"shot":
				_tracer(_v3(e["from"], 1.35) + _v3(Vector2.from_angle(f.p_facing) * 0.6), _v3(e["to"], 1.0), e["hit"])
			"burst":
				_ring_wave(_v3(e["at"]), Color(1.0, 0.45, 0.15), 2.8)
				burst(_v3(e["at"], 0.8), Color(1.0, 0.5, 0.15), 40, 6.0)
				impact(_v3(e["at"], 1.0), Color(1.0, 0.5, 0.2), 1.6)
			"crit-open":
				floater(W + Vector3(0, 0.9, 0), "THE BREAK IS OPEN", Color(0.9, 0.9, 1.0), 56, 1.4)
			"tether":
				floater(W + Vector3(0, 0.9, 0), "LEASHED", Color(0.8, 0.55, 1.0), 56, 1.2)
			"ward-up":
				_ward_at = _v3(e["at"])
				_ring_wave(_ward_at, Color(0.5, 1.0, 0.6), 2.0)
			"ward-broken":
				if _ward:
					burst(_ward.position + Vector3(0, 1.0, 0), Color(0.5, 1.0, 0.6), 40, 6.0)
				floater(P, "THE WARD TAKES IT", Color(0.5, 1.0, 0.6), 52)
			"burn-tick":
				floater(W + Vector3(randf_range(-0.3, 0.3), 0, 0), "%d" % int(e["damage"]), Color(1.0, 0.55, 0.2), 34, 0.6)
			"second-heart":
				floater(P + Vector3(0, 0.4, 0), "A SECOND HEART", Color(1.0, 0.4, 0.4), 72, 1.6)
				flash_screen(Color(1.0, 0.2, 0.2), 0.6)
			"hesitates":
				floater(W + Vector3(0, 0.8, 0), "IT HESITATES", C_TEXT, 56)
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
				impact((_v3(f.p_pos, 1.2) + _v3(f.w_pos, 1.2)) / 2.0, C_GUARD, 1.4)
				flash_screen(Color(0.4, 0.7, 1.0), 0.35)
			"block":
				floater(P, "BLOCKED  -%d" % int(e["damage"]), C_GUARD, 48)
				burst(_v3(f.p_pos, 1.2) + _v3(Vector2.from_angle(f.p_facing) * 0.5), C_GUARD, 12, 4.0)
				_shake = 0.07
			"hurt":
				floater(P, "-%d" % int(e["damage"]), C_WINDUP, 80)
				_player_flash = 1.0
				_shake = float(feel["shakeOnHurt"])
				flash_screen(Color(0.9, 0.08, 0.05), 0.55)
				hitstop(0.08)
			"evade":
				floater(P, "EVADED" if e["how"] == "dodged" else "MISSED", C_DIM, 44)
			"dodge":
				dust(_v3(f.p_pos, 0.1), 20)
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
				floater(P, "not yet: %s" % String(e.get("trigger", "")).to_lower(), C_DIM, 40)
			"pattern-lost":
				floater(P, "your Pattern is lost", C_WINDUP, 44)
			"stance-locked":
				floater(P, "no stance this season (your Toll)", C_DIM, 40)
			"named":
				floater(_v3(f.p_pos, 2.6), "%s!" % String(e["who"]).to_upper(), C_TEXT, 64, 1.0)
			"bar-warning":
				floater(P + Vector3(0, 0.5, 0), String(e["bars"][0]).to_upper(), C_WINDUP, 60, 1.6)
				floater(P, "press R again to break your Term", C_WINDUP, 40, 1.6)
				flash_screen(Color(0.8, 0.1, 0.05), 0.25)
			"breach":
				floater(P + Vector3(0, 0.8, 0), "TERM BROKEN", C_WINDUP, 110, 2.2)
				floater(P + Vector3(0, 0.2, 0), "the Pattern is lost for good" if e["sworn"] else "the Pattern is lost for a season", C_WINDUP, 48, 2.2)
				flash_screen(Color(0.6, 0.0, 0.0), 0.8)
				_shake = 0.35
			"turned":
				floater(P, "TURNED ASIDE", C_GUARD, 56)
				impact(_v3(f.p_pos, 1.2) + _v3(Vector2.from_angle(f.p_facing) * 0.6), C_GUARD, 1.0)
			"ward-pulse":
				_ring_wave(_v3(f.p_pos), C_GUARD, 2.2)
			"mend":
				floater(P, "+%d" % int(e["amount"]), Color(0.5, 1.0, 0.55), 56)
			"pattern-start":
				floater(P + Vector3(0, 0.5, 0), String(e["name"]).to_upper(), C_GOLD, 96, 1.4)
				for i in e["tolls"].size():
					floater(P - Vector3(0, 0.4 + 0.3 * i, 0), "Toll: %s" % String(e["tolls"][i]).to_lower(), C_DIM, 36, 1.6)
				_ring_wave(_v3(f.p_pos), C_GOLD, 4.0)
			"pattern-cue":
				if e["hit"]:
					burst(_v3(f.p_pos, 0.2), C_GOLD, 16, 4.0)
				else:
					floater(P, "%s" % ("too early" if e["offset_ms"] < 0 else "late"), C_DIM, 44)
			"pattern-done":
				if e.has("heal"):
					floater(P + Vector3(0, 0.6, 0), "+%d" % int(e["heal"]), Color(0.5, 1.0, 0.55), 140, 1.6, 0.6)
				else:
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
## Mouse look: applied directly (not scaled by frame time), so it feels the same at any frame rate.
func look(mouse_delta: Vector2, sensitivity := 0.0032) -> void:
	cam_yaw -= mouse_delta.x * sensitivity
	cam_pitch = clampf(cam_pitch - mouse_delta.y * sensitivity, -1.0, 0.05)

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
	_overlay_player.albedo_color = _tint.lerp(Color(C_WINDUP, 0.45), _player_flash) if _player_flash > 0.01 else _tint
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
				elif f.ranged and f.p_lock:
					_loop(_p_anim, "2H_Ranged_Aiming" if f.weapon["style"] == "gun-heavy" else "1H_Ranged_Aiming")
				else:
					_loop(_p_anim, "Idle")
			"down":
				pass

	# The wolf.
	_wolf.visible = show_wolf and f.w_state != "absent"
	_wolf.position = _v3(f.w_pos)
	if f.w_state == "down" and f.w_timer > 1.4:
		_wolf.position.y -= (f.w_timer - 1.4) * 0.6
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
		_alert.position = _v3(f.w_pos, 2.5 + 0.15 * sin(_clock * 20.0))
		_alert.modulate = Color(C_WINDUP, 0.5 + 0.5 * glow)
	_wolf_label.visible = _wolf.visible and f.w_state != "down"
	_wolf_label.position = _v3(f.w_pos, 2.1)
	var state_text := ""
	match f.w_state:
		"stagger": state_text = "  ·  STAGGERED"
		"windup": state_text = "  ·  %s" % String(f.w_attack["name"]).to_upper()
	_wolf_label.text = "%s  ·  %s%s" % [String(f.beast["name"]).to_upper(), String(f.w_shape).capitalize(), state_text]
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

	_update_trail(f.p_state in ["attack", "technique", "pattern"] and not f.ranged, dt)
	_update_statuses(f)
	_vig_tint.a = maxf(0.0, _vig_tint.a - dt * 1.6)
	var low := 1.0 - clampf(f.p_hp / float(Data.room["player"]["health"]), 0.0, 1.0)
	var pulse := 0.0 if f.p_hp > 30.0 or f.p_state == "down" else 0.12 * (0.5 + 0.5 * sin(_clock * 6.0)) * low
	var tint := _vig_tint if _vig_tint.a > pulse else Color(0.8, 0.05, 0.05, pulse)
	(_vignette.material as ShaderMaterial).set_shader_parameter("tint", tint)
	_update_camera(dt, cam_input, f)

## Models face +Z; the fight's facing is the angle on the ground plane.
func _yaw(facing: float) -> float:
	var d := Vector2.from_angle(facing)
	return atan2(d.x, d.y)

func _update_camera(dt: float, cam_input: Vector2, f: Fight) -> void:
	var p := _v3(f.p_pos)
	if portrait:
		# Face the character; leave room on the right for the reveal.
		var k2 := 1.0 - exp(-dt * 4.0)
		_cam_pos = _cam_pos.lerp(p + Vector3(1.25, 1.55, 3.6), k2)
		_cam_look = _cam_look.lerp(p + Vector3(1.25, 1.05, 0), k2)
		camera.position = _cam_pos
		camera.look_at(_cam_look, Vector3.UP)
		return
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
		cam_yaw = lerp_angle(cam_yaw, target_yaw, 1.0 - exp(-dt * 7.0))
		var back := Vector3(sin(cam_yaw), 0, cos(cam_yaw))
		var side := Vector3(cos(cam_yaw), 0, -sin(cam_yaw))
		var d := clampf(p.distance_to(w), 2.0, 8.0)
		# Over the right shoulder and wide, so the wolf is never hidden behind the Anchor.
		want = p + back * (4.3 + d * 0.3) + side * 3.3 + Vector3(0, 5.0 + d * 0.15, 0)
		focus = p.lerp(w, 0.7) + Vector3(0, 0.5, 0)
	else:
		cam_yaw -= cam_input.x * dt * 2.8
		cam_pitch = clampf(cam_pitch - cam_input.y * dt * 1.8, -1.0, 0.05)
		var back := Vector3(sin(cam_yaw), 0, cos(cam_yaw))
		var dist := 6.0
		want = p + back * dist * cos(cam_pitch) + Vector3(0, 1.6 + dist * sin(-cam_pitch), 0)
	want = _keep_in_chamber(focus, want)
	var k := 1.0 - exp(-dt * 11.0)
	_cam_pos = _cam_pos.lerp(want, k)
	_cam_pos = _keep_in_chamber(focus, _cam_pos)
	_cam_look = _cam_look.lerp(focus, 1.0 - exp(-dt * 10.0))
	_shake = maxf(0.0, _shake - dt * 0.9)
	var jitter := Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * _shake
	camera.position = _cam_pos + jitter
	if camera.position.distance_to(_cam_look) > 0.01:
		camera.look_at(_cam_look + jitter * 0.4, Vector3.UP)

func _update_statuses(f: Fight) -> void:
	# The Ward post.
	var warded := f.now < f.ward_until
	if warded and not _ward:
		_ward = MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.25
		cm.bottom_radius = 0.35
		cm.height = 2.2
		_ward.mesh = cm
		_ward.material_override = _mat(Color(0.5, 1.0, 0.6), 1.5, true, 0.45)
		add_child(_ward)
	if _ward:
		if warded:
			_ward.position = _v3(f.p_pos + Vector2.from_angle(f.p_facing + 1.2) * 1.0, 1.1)
		else:
			_ward.queue_free()
			_ward = null
	# The Leash: a line of field from the hand to the foe while it holds.
	if _tether.get_parent() == null:
		_tether.mesh = _tether_mesh
		var tm := _mat(Color(0.75, 0.45, 1.0), 3.0, true, 0.85)
		tm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_tether.material_override = tm
		add_child(_tether)
	_tether_mesh.clear_surfaces()
	if f.now < f.w_slow_until and f.w_state not in ["down", "absent"]:
		_tether_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
		var a := _v3(f.p_pos, 1.3)
		var b := _v3(f.w_pos, 0.9)
		for k in 6:
			var u := float(k) / 6.0
			var v := float(k + 1) / 6.0
			var sag := Vector3(0, -0.3 * sin(u * PI), 0)
			var sag2 := Vector3(0, -0.3 * sin(v * PI), 0)
			_tether_mesh.surface_add_vertex(a.lerp(b, u) + sag)
			_tether_mesh.surface_add_vertex(a.lerp(b, v) + sag2)
		_tether_mesh.surface_end()
	# Burning.
	if not _fire:
		_fire = CPUParticles3D.new()
		_fire.amount = 24
		_fire.lifetime = 0.6
		_fire.direction = Vector3(0, 1, 0)
		_fire.spread = 25.0
		_fire.initial_velocity_min = 0.8
		_fire.initial_velocity_max = 1.8
		_fire.gravity = Vector3(0, 1.5, 0)
		_fire.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
		_fire.emission_sphere_radius = 0.5
		var sm := SphereMesh.new()
		sm.radius = 0.06
		sm.height = 0.12
		_fire.mesh = sm
		var fm := _mat(Color(1.0, 0.5, 0.15), 4.0, true, 0.8)
		fm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_fire.material_override = fm
		add_child(_fire)
	_fire.emitting = f.now < f.w_burn_until and f.w_state not in ["down", "absent"]
	_fire.position = _v3(f.w_pos, 0.8)

## Like a spring arm: if the camera would sit inside a wall, pull it in along the line to
## the focus and lift it, so it looks down over the Anchor instead of through stone.
func _keep_in_chamber(focus: Vector3, want: Vector3) -> Vector3:
	var a: Dictionary = Data.room["arena"]
	var hx := float(a["width"]) / 2.0 + 0.2
	var hz := float(a["depth"]) / 2.0 + 0.2
	if absf(want.x) <= hx and absf(want.z) <= hz:
		return want
	var d := want - focus
	var t := 1.0
	if absf(want.x) > hx and absf(d.x) > 1e-4:
		t = minf(t, (signf(d.x) * hx - focus.x) / d.x)
	if absf(want.z) > hz and absf(d.z) > 1e-4:
		t = minf(t, (signf(d.z) * hz - focus.z) / d.z)
	t = clampf(t, 0.0, 1.0)
	var p := focus + d * t
	p.y = maxf(p.y, focus.y + 1.5 + (1.0 - t) * 3.5)
	return p

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
