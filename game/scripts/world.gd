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
var portrait_side := 1.25   # where the character stands in the portrait: + left of the screen, - right
var portrait_dist := 3.6
var cine := false            # a scene holds the camera (the rite)
var cine_pos := Vector3.ZERO
var cine_look := Vector3.ZERO
var cine_speed := 2.0

var _player: Node3D
var _p_anim: AnimationPlayer
var _p_meshes: Array = []
var _p_oneshot_until := 0.0
var _p_current := ""
var _wolf: Node3D
var _w_anim: AnimationPlayer
var _w_meshes: Array = []
var _w_anims: Dictionary = {}   # the foe's animation names by what the fight asks for ({}: the wolf's)
var _foe_spec: Dictionary = {}  # {} for the wolf; a person: {body, weapon, name}
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
var _moon: DirectionalLight3D
var _env: Environment
var place := "cut"
var arena := Vector2(22, 14)
var _place_root := Node3D.new()
var _figures: Array = []   # people standing in the place: {node, anim, pos, facing}
var obstacles: Array = []  # Vector3(x, z, radius) for the place's pillars, people and furniture
var _ally_nodes: Array = []   # the party, drawn from the fight's allies: {node, anim, cur, until}
var open_doors: Dictionary = {}   # doors the term has opened (by where they lead)
var _motes := CPUParticles3D.new()
var _p_skel: Skeleton3D
var _head_bone := -1

func _ready() -> void:
	_build_environment()
	add_child(_place_root)
	_build_chamber()
	_build_genius()
	_build_player()
	_build_wolf()
	_build_markers()
	_build_effects()
	_build_flair()
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
	_place_root.add_child(n)
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
	_env = env
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
	_moon = moon

func _build_chamber() -> void:
	var a: Dictionary = Data.room["arena"]
	arena = Vector2(a["width"], a["depth"])
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
		_place_root.add_child(b)
		tx += 0.8
	for rz in [-0.72, 0.72]:
		var r := MeshInstance3D.new()
		var rm := BoxMesh.new()
		rm.size = Vector3(hw * 2.0, 0.12, 0.1)
		r.mesh = rm
		r.position = Vector3(0, 0.2, rz)
		r.material_override = rail
		_place_root.add_child(r)
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
	_overlay_player.next_pass = _ink(2.2)
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
	_p_skel = skel
	_head_bone = skel.find_bone("head")
	_tint_genius(_shape_color(hero.get("shape", "anchor")))
	# After the rite the genius has a First Form; before it, it is the orb.
	var g: Dictionary = hero.get("genius", {})
	if g.is_empty():
		clear_form()
	elif _g_form_info.get("form", "") != g.get("form", "") or not _g_form:
		clear_form()
		var form := make_form(g, _shape_color(hero.get("shape", "anchor")).lightened(0.15))
		add_child(form)
		form.position = _player.position + Vector3(1, 1.5, 0)
		set_form(g, form)

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

const WOLF_ANIMS := { "idle": "AnimalArmature|Idle", "walk": "AnimalArmature|Walk", "gallop": "AnimalArmature|Gallop",
	"windup": "AnimalArmature|Idle_2_HeadLow", "stagger": "AnimalArmature|Idle_2_HeadLow", "flinch": "AnimalArmature|Idle",
	"Attack": "AnimalArmature|Attack", "HitReact": "AnimalArmature|Idle_HitReact_Left", "HitReact2": "AnimalArmature|Idle_HitReact_Right", "Death": "AnimalArmature|Death" }
const PERSON_ANIMS := { "idle": "Idle", "walk": "Walking_A", "gallop": "Running_A", "windup": "Idle", "stagger": "Idle", "flinch": "Idle",
	"Attack": "1H_Melee_Attack_Slice_Horizontal", "HitReact": "Hit_A", "HitReact2": "Hit_B", "Death": "Death_A" }

## The foe: the wolf ({}), or a person ({ body, weapon, name }) such as a classmate in the yard.
func set_foe(spec: Dictionary) -> void:
	if spec == _foe_spec and _wolf:
		return
	_foe_spec = spec
	if _wolf:
		_wolf.queue_free()
	if not spec.has("body"):
		_wolf = load("res://game/assets/quaternius/Wolf.glb").instantiate()
		_wolf.scale = Vector3.ONE * WOLF_SCALE * float(spec.get("wolf_scale", 1.0))
		_w_anims = WOLF_ANIMS
	else:
		_wolf = load("res://game/assets/kaykit/%s.glb" % spec.get("body", "Knight")).instantiate()
		_w_anims = PERSON_ANIMS
		for a in _wolf.find_children("*", "BoneAttachment3D", true, false):
			var an := String(a.name)
			a.visible = an.contains("Helmet") or an.contains("Hat") or an.contains("Cape") or an.contains("Hood")
		var skel: Skeleton3D = _wolf.find_child("Skeleton3D", true, false)
		if spec.get("weapon", "") != "":
			var w: Dictionary = Data.by_id(Data.weapons, spec["weapon"])
			_attach(skel, "handslot.r", "res://game/assets/kaykit/weapons/%s.gltf" % w["model"])
			if w.has("offhand"):
				_attach(skel, "handslot.l", "res://game/assets/kaykit/weapons/%s.gltf" % w["offhand"])
	add_child(_wolf)
	_w_anim = _wolf.find_child("AnimationPlayer", true, false)
	for key in ["idle", "walk", "gallop", "windup", "stagger", "flinch"]:
		if _w_anim.has_animation(_w_anims[key]):
			_w_anim.get_animation(_w_anims[key]).loop_mode = Animation.LOOP_LINEAR
	_w_meshes = _wolf.find_children("*", "MeshInstance3D", true, false)
	_overlay_wolf = _mat(C_WINDUP, 2.0, true, 0.0)
	_overlay_wolf.next_pass = _ink(2.4)
	for m in _w_meshes:
		m.material_overlay = _overlay_wolf
	_w_current = ""
	_w_oneshot_until = 0.0

func _wa(key: String) -> String:
	return _w_anims.get(key, key)

func _build_wolf() -> void:
	set_foe({})
	for l in [_wolf_label, _alert]:
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.pixel_size = 0.004
		l.outline_size = 10
		l.outline_modulate = Color(0, 0, 0, 0.85)
		add_child(l)
	_wolf_label.font_size = 28
	_wolf_label.font = Style.font("title")
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
// The film the game is shot on: cool shadows, lamplit highlights, a little grain, the edge of
// the frame falling into dark; and the hit's colour flashing in from the edges.
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform vec4 tint : source_color = vec4(0.0);
uniform float base = 0.5;
uniform float grain = 0.03;
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	vec3 cool = vec3(0.84, 0.94, 1.12);
	vec3 warm = vec3(1.1, 1.0, 0.84);
	vec3 g = c * mix(cool, warm, smoothstep(0.04, 0.55, l));
	g += vec3(0.006, 0.008, 0.016) * (1.0 - smoothstep(0.0, 0.25, l));
	g = mix(vec3(l), g, 1.08);
	vec2 uv = UV - 0.5;
	float d = length(uv * vec2(1.5, 1.0));
	g *= 1.0 - smoothstep(0.36, 0.95, d) * base;
	g += (hash(floor(FRAGCOORD.xy * 0.5) + fract(TIME * 7.13) * 97.0) - 0.5) * grain;
	g = mix(g, tint.rgb, clamp(tint.a * smoothstep(0.2, 0.9, d) * 0.8, 0.0, 1.0));
	COLOR = vec4(g, 1.0);
}
"""

const INK := """
shader_type spatial;
// Ink lines around the characters and the beasts, like a woodcut: the mesh drawn again, its
// back faces pushed out a few pixels along the normal.
render_mode unshaded, cull_front, shadows_disabled, depth_draw_opaque;
uniform vec4 ink : source_color = vec4(0.045, 0.03, 0.028, 1.0);
uniform float width = 2.0;
void vertex() {
	vec4 clip = PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0));
	vec3 n = (MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	vec2 off = (PROJECTION_MATRIX * vec4(n, 0.0)).xy;
	off = off / max(length(off), 1e-4);
	clip.xy += off * width * 2.0 / VIEWPORT_SIZE * clip.w;
	POSITION = clip;
}
void fragment() {
	ALBEDO = ink.rgb;
}
"""

const SHAFT := """
shader_type spatial;
// A shaft of moonlight through the broken roof: brightest where you look across it.
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 tint : source_color = vec4(0.5, 0.62, 1.0, 1.0);
uniform float strength = 0.17;
uniform float half_height = 7.0;
varying float h;
void vertex() { h = VERTEX.y; }
void fragment() {
	float edge = pow(abs(dot(NORMAL, VIEW)), 2.0);
	float fade = smoothstep(-half_height, -half_height + 1.2, h) * (1.0 - smoothstep(half_height * 0.1, half_height, h));
	float shimmer = 0.85 + 0.15 * sin(TIME * 0.5 + h * 0.9);
	ALBEDO = tint.rgb;
	ALPHA = clamp(strength * edge * fade * shimmer, 0.0, 1.0);
}
"""

const GLOW := """
shader_type spatial;
// A soft round glow that always faces the camera: the genius's halo, the moon's pool.
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 tint : source_color = vec4(1.0);
uniform float strength = 1.0;
uniform float falloff = 2.2;
uniform bool billboard = true;
void vertex() {
	if (billboard) {
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	}
}
void fragment() {
	float d = length(UV - 0.5) * 2.0;
	ALBEDO = tint.rgb;
	ALPHA = clamp(pow(max(0.0, 1.0 - d), falloff) * strength, 0.0, 1.0);
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
		var name: String = _wa(e["name"])
		if e["name"] == "HitReact" and randf() < 0.5:
			name = _wa("HitReact2")
		if e["name"] == "Attack" and e.has("anim") and _w_anim.has_animation(e["anim"]):
			name = e["anim"]
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
	l.font = Style.font("title")
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
	genius_born()
	_motes.amount = 260
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
				genius_react("parry")
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
				genius_react("hurt")
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
				genius_react("stance")
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
			"genius-hunt":
				_g_dart_at = _v3(f.w_pos, 1.0)
				_g_dart_until = _clock + 0.28
				impact(_v3(f.w_pos, 1.0), _g_tint, 0.6)
				burst(_v3(f.w_pos, 1.0), _g_tint, 10, 4.0)
				floater(W + Vector3(0.4, 0.4, 0), "%d" % int(e["damage"]), _g_tint.lightened(0.3), 46, 0.8)
				_wolf_flash = maxf(_wolf_flash, 0.5)
			"genius-guard":
				var mid := _v3(f.p_pos.lerp(f.w_pos, 0.35), 1.2)
				_g_dart_at = mid
				_g_dart_until = _clock + 0.35
				impact(mid, _g_tint, 1.0)
				_ring_wave(_v3(f.p_pos), _g_tint, 1.6)
				floater(P, "GUARDED", _g_tint.lightened(0.3), 52, 1.0)
				genius_react("parry")
			"genius-fall":
				genius_down = true
				floater(P + Vector3(0, 0.4, 0), "YOUR GENIUS FALLS", Color(0.8, 0.75, 0.7), 56, 1.6)
				_g_flicker = 1.5
			"genius-up":
				genius_down = false
				floater(P, "IT STANDS AGAIN", _g_tint.lightened(0.3), 48, 1.2)
				genius_react("stance")
			"order":
				floater(P + Vector3(0, 0.3, 0), "ORDER: %s" % String(e["order"]).to_upper(), _g_tint.lightened(0.3), 44, 1.0)
				genius_react("cue")
			"ally-hit", "ally-hurt", "ally-down", "ally-up":
				_ally_event(f, e)
			"field-open":
				_ring_wave(_v3(f.p_pos), _shape_color(f.player_shape), 5.0)
				burst(P, _shape_color(f.player_shape), 60, 6.0)
				floater(P + Vector3(0, 0.6, 0), "THE FIELD OPENS", _shape_color(f.player_shape), 80, 2.0, 0.4)
				flash_screen(_shape_color(f.player_shape), 0.5)
				genius_react("stance")
			"marked":
				floater(W + Vector3(0, 0.9, 0), "UNDER WARRANT", C_GOLD, 56, 1.4)
				_ring_wave(_v3(f.w_pos), C_GOLD, 2.0)
			"sounded":
				floater(W + Vector3(0, 0.9, 0), "SOUNDED", Color(0.6, 0.85, 1.0), 56, 1.2)
				_ring_wave(_v3(f.w_pos), Color(0.6, 0.85, 1.0), 3.0)
			"pulled":
				floater(W + Vector3(0, 0.9, 0), "LINE ACROSS", Color(0.8, 0.55, 1.0), 56, 1.0)
				_tracer(_v3(f.p_pos, 1.3), _v3(f.w_pos, 1.0), true)
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
				genius_react("cue")
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
	_aura.visible = f.p_stance or f.p_field_open
	(_aura.material_override as StandardMaterial3D).albedo_color.a = 0.09 if f.p_stance else 0.035
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
			"prowl": _loop(_w_anim, _wa("walk"), 1.2, true)
			"approach": _loop(_w_anim, _wa("gallop"), 1.3, true)
			"windup": _loop(_w_anim, _wa("windup"), 0.6, true)
			"recover", "idle", "pinned": _loop(_w_anim, _wa("idle"), 1.0, true)
			"stagger": _loop(_w_anim, _wa("stagger"), 0.3, true)
			"flinch": _loop(_w_anim, _wa("flinch"), 1.0, true)
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
	_update_genius(f, dt)
	_update_figures(f, dt)
	_update_allies(f, dt)

## Models face +Z; the fight's facing is the angle on the ground plane.
func _yaw(facing: float) -> float:
	var d := Vector2.from_angle(facing)
	return atan2(d.x, d.y)

func _update_camera(dt: float, cam_input: Vector2, f: Fight) -> void:
	var p := _v3(f.p_pos)
	if cine:
		var kc := 1.0 - exp(-dt * cine_speed)
		_cam_pos = _cam_pos.lerp(cine_pos, kc)
		_cam_look = _cam_look.lerp(cine_look, kc)
		_shake = maxf(0.0, _shake - dt * 0.9)
		var jit := Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * _shake
		camera.position = _cam_pos + jit
		camera.look_at(_cam_look + jit * 0.4, Vector3.UP)
		return
	if portrait:
		# Face the character; leave room on the right for the reveal.
		var k2 := 1.0 - exp(-dt * 4.0)
		var sway := Vector3(sin(_clock * 0.23) * 0.25, sin(_clock * 0.31) * 0.08, 0)
		_cam_pos = _cam_pos.lerp(p + Vector3(portrait_side, 1.25 + portrait_dist * 0.12, portrait_dist) + sway, k2)
		_cam_look = _cam_look.lerp(p + Vector3(portrait_side, 1.15, 0), k2)
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
	var hx := arena.x / 2.0 + 0.2
	var hz := arena.y / 2.0 + 0.2
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
	genius_down = false
	_hitstop_until = 0
	_slowmo_until = 0
	_p_oneshot_until = 0.0
	_w_oneshot_until = 0.0
	_p_current = ""
	_w_current = ""
	_play(_p_anim, "Idle", 1.0, 0.0)
	_play(_w_anim, _wa("idle"), 1.0, 0.0)

# --- The look: ink, motes, moonlight -------------------------------------------

static var _shaders := {}

func _shader_mat(code: String) -> ShaderMaterial:
	if not _shaders.has(code):
		var sh := Shader.new()
		sh.code = code
		_shaders[code] = sh
	var m := ShaderMaterial.new()
	m.shader = _shaders[code]
	return m

func _ink(width: float) -> ShaderMaterial:
	var m := _shader_mat(INK)
	m.set_shader_parameter("width", width)
	return m

## The chamber's air: motes of field drifting in the dark, and moonlight falling through the
## broken roof in shafts, with a pale pool where each one lands.
func _build_flair() -> void:
	var a: Dictionary = Data.room["arena"]
	var hw := float(a["width"]) / 2.0
	var hd := float(a["depth"]) / 2.0
	_motes.amount = 170
	_motes.lifetime = 9.0
	_motes.preprocess = 9.0
	_motes.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_motes.emission_box_extents = Vector3(hw, 1.8, hd)
	_motes.position = Vector3(0, 2.0, 0)
	_motes.direction = Vector3(0, 1, 0)
	_motes.spread = 180.0
	_motes.initial_velocity_min = 0.03
	_motes.initial_velocity_max = 0.18
	_motes.gravity = Vector3(0, 0.035, 0)
	_motes.scale_amount_min = 0.5
	_motes.scale_amount_max = 1.3
	var q := QuadMesh.new()
	q.size = Vector2(0.05, 0.05)
	_motes.mesh = q
	var mm := _shader_mat(GLOW)
	mm.set_shader_parameter("tint", Color(1, 1, 1))
	mm.set_shader_parameter("strength", 1.6)
	mm.set_shader_parameter("falloff", 1.6)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = _soft_dot()
	mat.no_depth_test = false
	_motes.material_override = mat
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0))
	ramp.set_color(1, Color(1, 1, 1, 0))
	ramp.add_point(0.2, Color(1, 1, 1, 0.9))
	ramp.add_point(0.8, Color(1, 1, 1, 0.7))
	_motes.color_ramp = ramp
	var hues := Gradient.new()
	hues.set_color(0, Color(0.62, 0.95, 0.7))
	hues.set_color(1, Color(1.0, 0.78, 0.45))
	_motes.color_initial_ramp = hues
	add_child(_motes)
	_moonlight([[Vector3(-5.5, 0, -2.6), 1.3], [Vector3(3.2, 0, 3.4), 0.9], [Vector3(8.6, 0, -4.4), 1.1]])

## Shafts of moonlight along the moon's direction, each with a pool on the floor.
func _moonlight(spots: Array) -> void:
	var up := _moon.global_transform.basis.z.normalized() if _moon.is_inside_tree() else _moon.transform.basis.z.normalized()
	for spot in spots:
		var at: Vector3 = spot[0]
		var r: float = spot[1]
		var shaft := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = r * 1.25
		cm.bottom_radius = r
		cm.height = 14.0
		cm.cap_top = false
		cm.cap_bottom = false
		cm.radial_segments = 24
		shaft.mesh = cm
		var sm := _shader_mat(SHAFT)
		sm.set_shader_parameter("half_height", 7.0)
		shaft.material_override = sm
		shaft.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var y := up
		var x := y.cross(Vector3.FORWARD).normalized()
		var z := x.cross(y).normalized()
		shaft.transform = Transform3D(Basis(x, y, z), at + up * 7.0)
		_place_root.add_child(shaft)
		var pool := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(r * 3.4, r * 3.4)
		pool.mesh = pm
		var gm := _shader_mat(GLOW)
		gm.set_shader_parameter("billboard", false)
		gm.set_shader_parameter("tint", Color(0.45, 0.58, 1.0))
		gm.set_shader_parameter("strength", 0.35)
		gm.set_shader_parameter("falloff", 1.4)
		pool.material_override = gm
		pool.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		pool.position = at + Vector3(0, 0.13, 0)
		_place_root.add_child(pool)

## A soft round dot, drawn once, for motes and sparks.
static var _dot: ImageTexture
static func _soft_dot() -> ImageTexture:
	if _dot:
		return _dot
	var n := 32
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for yy in n:
		for xx in n:
			var d := Vector2(xx - n / 2.0 + 0.5, yy - n / 2.0 + 0.5).length() / (n / 2.0)
			var a := clampf(pow(maxf(0.0, 1.0 - d), 1.8), 0.0, 1.0)
			img.set_pixel(xx, yy, Color(1, 1, 1, a))
	_dot = ImageTexture.create_from_image(img)
	return _dot

# --- The genius: before the rite, a little orb circling the head ------------------

## Before the Academy's rite gives it a First Form, the genius is a mote of the hero's own field:
## a small light that rings their head, keeps pace when they move, and answers what they do.
var genius_visible := true
var _genius := Node3D.new()
var _g_core := MeshInstance3D.new()
var _g_core_mat := StandardMaterial3D.new()
var _g_halo := MeshInstance3D.new()
var _g_halo_mat: ShaderMaterial
var _g_light := OmniLight3D.new()
var _g_trail := CPUParticles3D.new()
var _g_tint := Color(1.0, 0.8, 0.4)
var _g_angle := 0.0
var _g_pulse := 0.0
var _g_flicker := 0.0
var _g_spin := 0.0
var _g_born := 1.0
var _g_pos := Vector3.ZERO
var genius_goal := Vector3.INF     # where a scene has called the genius to
var genius_down := false           # fallen in a fight: it lies where it fell
var _g_dart_at := Vector3.ZERO
var _g_dart_until := 0.0
var genius_goal_radius := 0.0
var _g_form: Node3D = null         # the First Form, once the rite has given it one
var _g_form_info: Dictionary = {}
var _g_form_anim: AnimationPlayer
var _g_body: GeniusBody = null
var _g_form_pos := Vector3.ZERO
var _g_form_facing := 0.0

const GENIUS_RADIUS := 0.62
const GENIUS_RISE := 0.42   # above the head bone, which sits at the jaw

func _build_genius() -> void:
	add_child(_genius)
	var sm := SphereMesh.new()
	sm.radius = 0.075
	sm.height = 0.15
	sm.radial_segments = 16
	sm.rings = 8
	_g_core.mesh = sm
	_g_core_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_g_core.material_override = _g_core_mat
	_g_core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_genius.add_child(_g_core)
	var q := QuadMesh.new()
	q.size = Vector2(0.9, 0.9)
	_g_halo.mesh = q
	_g_halo_mat = _shader_mat(GLOW)
	_g_halo_mat.set_shader_parameter("falloff", 2.4)
	_g_halo.material_override = _g_halo_mat
	_g_halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_genius.add_child(_g_halo)
	_g_light.omni_range = 2.4
	_g_light.omni_attenuation = 1.4
	_g_light.light_energy = 0.7
	_g_light.shadow_enabled = false
	_genius.add_child(_g_light)
	# The trail: sparks left in the world as it circles, so the ring draws itself.
	_g_trail.local_coords = false
	_g_trail.amount = 64
	_g_trail.lifetime = 0.75
	_g_trail.direction = Vector3(0, 1, 0)
	_g_trail.spread = 180.0
	_g_trail.initial_velocity_min = 0.0
	_g_trail.initial_velocity_max = 0.05
	_g_trail.gravity = Vector3(0, 0.12, 0)
	var tq := QuadMesh.new()
	tq.size = Vector2(0.13, 0.13)
	_g_trail.mesh = tq
	var tm := StandardMaterial3D.new()
	tm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	tm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	tm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	tm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	tm.vertex_color_use_as_albedo = true
	tm.albedo_texture = _soft_dot()
	_g_trail.material_override = tm
	var sc := Curve.new()
	sc.add_point(Vector2(0, 1))
	sc.add_point(Vector2(1, 0.1))
	_g_trail.scale_amount_curve = sc
	add_child(_g_trail)
	_tint_genius(_g_tint)

func _tint_genius(c: Color) -> void:
	_g_tint = c.lightened(0.25)
	_g_core_mat.albedo_color = c.lightened(0.7)
	_g_halo_mat.set_shader_parameter("tint", _g_tint)
	_g_light.light_color = _g_tint
	var ramp := Gradient.new()
	ramp.set_color(0, Color(_g_tint.lightened(0.3), 0.8))
	ramp.set_color(1, Color(_g_tint, 0.0))
	_g_trail.color_ramp = ramp

## The genius is born: it comes out of the burst when the field wakes.
func genius_born() -> void:
	genius_visible = true
	_g_born = 0.0
	_g_pulse = 1.0

func genius_react(kind: String) -> void:
	match kind:
		"parry": _g_pulse = 1.0; _g_spin = 1.0
		"hit": _g_pulse = maxf(_g_pulse, 0.35)
		"cue": _g_pulse = maxf(_g_pulse, 0.8)
		"hurt": _g_flicker = 0.5
		"stance": _g_pulse = maxf(_g_pulse, 0.6)

func _update_genius(f: Fight, dt: float) -> void:
	var show := genius_visible and _player != null and _p_skel != null and _head_bone >= 0
	_genius.visible = show
	_g_trail.emitting = show
	if not show:
		return
	var down := f.p_state == "down"
	var pattern := f.p_state == "pattern"
	_g_born = minf(1.0, _g_born + dt * 0.9)
	_g_pulse = maxf(0.0, _g_pulse - dt * 2.2)
	_g_spin = maxf(0.0, _g_spin - dt * 1.2)
	_g_flicker = maxf(0.0, _g_flicker - dt)
	var speed := 2.1 + 5.0 * _g_spin + (5.5 if pattern else 0.0) + (1.0 if f.p_stance else 0.0)
	if down:
		speed = 0.6
	_g_angle = fmod(_g_angle + dt * speed, TAU)
	if _g_form:
		_update_form(f, dt)
		return
	var head := _p_skel.global_transform * _p_skel.get_bone_global_pose(_head_bone).origin
	var centre := head + Vector3(0, GENIUS_RISE, 0)
	if genius_goal != Vector3.INF:
		# A scene has called it away (the rite): it spirals in to the goal.
		var to := genius_goal + Vector3(cos(_clock * 9.0), 0.3 * sin(_clock * 5.0), sin(_clock * 9.0)) * genius_goal_radius
		_g_pos = _g_pos.lerp(to, 1.0 - exp(-dt * 3.5))
		_genius.global_position = _g_pos
		_g_trail.global_position = _g_pos
		_g_core.scale = Vector3.ONE * (1.0 + 0.6 * _g_pulse)
		_g_halo.scale = Vector3.ONE * (1.0 + 1.6 * _g_pulse)
		_g_halo_mat.set_shader_parameter("strength", 1.4 + _g_pulse)
		_g_light.light_energy = 1.4 + 2.0 * _g_pulse
		return
	var radius := GENIUS_RADIUS * (0.8 if pattern else 1.0)
	if down:
		centre = _player.global_position + Vector3(0, 0.5, 0)
		radius = 0.4
	# The ring tilts a little, so it reads as a ring and not a line, and breathes.
	var off := Vector3(cos(_g_angle) * radius, sin(_g_angle * 1.0 + 0.7) * 0.09 + 0.04 * sin(_clock * 2.3), sin(_g_angle) * radius)
	var born_k := _g_born * _g_born * (3.0 - 2.0 * _g_born)
	var want := centre + off * born_k
	if _clock < _g_dart_until:
		want = _g_dart_at
	if genius_down:
		want = _player.global_position + Vector3(0.6, 0.15, 0.4)
	var k := 1.0 - exp(-dt * 16.0)
	_g_pos = want if _g_pos == Vector3.ZERO else _g_pos.lerp(want, k)
	_genius.global_position = _g_pos
	_g_trail.global_position = _g_pos
	var will := clampf(f.p_will / 100.0, 0.0, 1.0)
	var bright := (0.55 + 0.45 * will) * (0.4 if down else 1.0)
	if _g_flicker > 0.0:
		bright *= 0.35 + 0.65 * absf(sin(_clock * 40.0))
	var s := (0.9 + 0.7 * _g_pulse + 0.06 * sin(_clock * 6.0)) * (0.3 + 0.7 * born_k)
	_g_core.scale = Vector3.ONE * s
	_g_halo.scale = Vector3.ONE * (0.8 + 1.4 * _g_pulse) * (0.3 + 0.7 * born_k)
	_g_halo_mat.set_shader_parameter("strength", (0.7 + 0.9 * _g_pulse) * bright)
	_g_light.light_energy = (0.55 + 1.6 * _g_pulse) * bright
	_g_core_mat.albedo_color = _g_tint.lightened(0.55 + 0.4 * _g_pulse) * Color(1, 1, 1, 1)

# --- Places: the Cut, and the Academy's grounds ----------------------------------

## Leave the current place and build another: "cut" (the chamber of the opening and the
## practice yard) or a place of the Academy from data/academy.json.
func set_place(id: String) -> void:
	if id == place and _place_root.get_child_count() > 0:
		return
	place = id
	remove_child(_place_root)
	_place_root.queue_free()
	_place_root = Node3D.new()
	add_child(_place_root)
	_torches.clear()
	_figures.clear()
	obstacles.clear()
	_sigils.clear()
	_pillar = null
	bowl_flame = null
	if id == "cut":
		_build_chamber()
		_moonlight([[Vector3(-5.5, 0, -2.6), 1.3], [Vector3(3.2, 0, 3.4), 0.9], [Vector3(8.6, 0, -4.4), 1.1]])
		_env.background_color = Color(0.02, 0.018, 0.02)
		_env.ambient_light_energy = 0.2
		_env.ambient_light_color = Color(0.5, 0.44, 0.48)
		_env.fog_density = 0.022
		_moon.light_energy = 0.28
	else:
		_build_academy_place(Data.academy["places"][id])
	_motes.emission_box_extents = Vector3(arena.x / 2.0, 1.8, arena.y / 2.0)
	_motes.restart()

## A place of the Academy: a floor, walls of the fortress with an arch at every door, torches,
## and the props that say what the place is for. Evening at the Thaw: a deep blue sky.
func _build_academy_place(spec: Dictionary) -> void:
	arena = Vector2(spec["size"][0], spec["size"][1])
	var hw := arena.x / 2.0 + 1.0
	var hd := arena.y / 2.0 + 1.0
	var floor_piece: String = spec["floor"]
	var x := -hw + 2.0
	var i := 0
	while x < hw:
		var z := -hd + 2.0
		while z < hd:
			var fp := floor_piece
			if floor_piece == "floor_tile_large" and (i * 7) % 13 == 5:
				fp = "floor_tile_large_rocks"
			_piece(fp, Vector3(x, 0, z), 90.0 * (i % 4))
			z += 4.0
			i += 1
		x += 4.0
	var doors: Array = spec["doors"]
	var is_door := func(px: float, pz: float) -> bool:
		for d in doors:
			if absf(float(d["at"][0]) - px) < 2.1 and absf(float(d["at"][1]) - pz) < 2.1:
				return true
		return false
	var kinds := ["wall", "wall_pillar", "wall", "wall_cracked", "wall_pillar", "wall"]
	var wild: bool = spec.get("walls", "") == "wild"
	if spec.get("walls", "") == "yard":
		kinds = ["wall", "wall_broken", "wall_pillar", "wall_cracked", "wall", "wall_pillar"]
	if wild:
		kinds = ["wall_broken", "rubble_large", "wall_cracked", "rubble_large", "wall_broken", "wall_broken"]
	var k := 0
	var wx := -hw + 2.0
	while wx < hw:
		for side in [-1, 1]:
			var kind: String = "wall_arched" if is_door.call(wx, side * (hd - 1.0)) else kinds[(k + (3 if side > 0 else 0)) % kinds.size()]
			_piece(kind, Vector3(wx, 0, side * hd), 0.0 if side < 0 else 180.0)
			if k % 2 == 0 and kind != "wall_arched" and not wild:
				_torch(Vector3(wx, 2.4, side * (hd - 0.45)), 0.0 if side < 0 else 180.0)
		wx += 4.0
		k += 1
	var ez := -hd + 2.0
	while ez < hd:
		for side in [-1, 1]:
			var kind: String = "wall_arched" if is_door.call(side * (hw - 1.0), ez) else kinds[(k + 1) % kinds.size()]
			_piece(kind, Vector3(side * hw, 0, ez), 90.0 if side < 0 else -90.0)
			if k % 3 == 0 and kind != "wall_arched" and not wild:
				_torch(Vector3(side * (hw - 0.45), 2.4, ez), 90.0 if side < 0 else -90.0)
		ez += 4.0
		k += 1
	for d in doors:
		_door_marker(Vector3(float(d["at"][0]), 0, float(d["at"][1])), String(d["label"]), d.has("locked") and not open_doors.has(d["to"]))
	if spec.get("rails", false):
		_rails(arena.x / 2.0 + 1.0)
	match String(spec["name"]):
		"The Quad": _furnish_quad()
		"The Yard": _furnish_yard()
		"The Dormitory": _furnish_dorm(spec)
		"The Hearth Hall": _furnish_hearth()
	if wild:
		_furnish_wild(spec)
		_env.background_color = Color(0.03, 0.045, 0.06)
		_env.ambient_light_energy = 0.42
		_env.ambient_light_color = Color(0.5, 0.6, 0.75)
		_env.fog_density = 0.018
		_moon.light_energy = 0.9
		_moonlight([[Vector3(-arena.x * 0.2, 0, -arena.y * 0.15), 1.4], [Vector3(arena.x * 0.28, 0, arena.y * 0.2), 1.0], [Vector3(0, 0, 0), 0.8]])
		return
	_env.background_color = Color(0.045, 0.05, 0.095)
	_env.ambient_light_energy = 0.34
	_env.ambient_light_color = Color(0.5, 0.44, 0.48)
	_env.fog_density = 0.012
	_moon.light_energy = 0.28
	if spec.get("walls", "") != "fortress" or arena.x > 20.0:
		_moonlight([[Vector3(arena.x * 0.18, 0, -arena.y * 0.12), 1.2], [Vector3(-arena.x * 0.25, 0, arena.y * 0.2), 0.9]])

## The line itself: ties and two rails across the place.
func _rails(hw: float) -> void:
	var tie := _mat(Color(0.22, 0.15, 0.1))
	var rail := _mat(Color(0.42, 0.4, 0.38))
	rail.metallic = 0.85
	rail.roughness = 0.3
	var tx := -hw
	while tx < hw:
		var bm := BoxMesh.new()
		bm.size = Vector3(0.3, 0.12, 2.4)
		var b := MeshInstance3D.new()
		b.mesh = bm
		b.position = Vector3(tx, 0.1, 0)
		b.material_override = tie
		_place_root.add_child(b)
		tx += 0.8
	for rz in [-0.72, 0.72]:
		var rm := BoxMesh.new()
		rm.size = Vector3(hw * 2.0, 0.12, 0.1)
		var r := MeshInstance3D.new()
		r.mesh = rm
		r.position = Vector3(0, 0.2, rz)
		r.material_override = rail
		_place_root.add_child(r)

func _torch(at: Vector3, rot: float) -> void:
	var t := _piece("torch_mounted", at, rot)
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.6, 0.3)
	light.light_energy = 1.5
	light.omni_range = 8.0
	light.omni_attenuation = 1.5
	light.shadow_enabled = false
	light.position = Vector3(0, 0.6, 0.25)
	t.add_child(light)
	_torches.append(light)

## Where a door is: a soft ring of light on the floor and its name above, dim if it is shut.
func _door_marker(at: Vector3, label: String, locked: bool) -> void:
	var ring := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(2.6, 2.6)
	ring.mesh = pm
	var gm := _shader_mat(GLOW)
	gm.set_shader_parameter("billboard", false)
	gm.set_shader_parameter("tint", Color(0.55, 0.6, 0.7) if locked else Color(1.0, 0.75, 0.4))
	gm.set_shader_parameter("strength", 0.25 if locked else 0.6)
	gm.set_shader_parameter("falloff", 1.8)
	ring.material_override = gm
	ring.position = at * Vector3(0.86, 0, 0.86) + Vector3(0, 0.12, 0)
	_place_root.add_child(ring)
	var l := Label3D.new()
	l.text = label.to_upper()
	l.font = Style.font("title")
	l.font_size = 30
	l.pixel_size = 0.006
	l.modulate = Color(0.75, 0.72, 0.68, 0.55) if locked else Color(1.0, 0.85, 0.6)
	l.outline_size = 8
	l.outline_modulate = Color(0, 0, 0, 0.8)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.position = at * Vector3(0.86, 0, 0.86) + Vector3(0, 3.6, 0)
	_place_root.add_child(l)

## The Green: rocks, the odd dead stump (a scaled column), and at the post a ring of ward-light.
func _furnish_wild(spec: Dictionary) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(arena.x * 7 + arena.y)
	for i in 7:
		var at := Vector3(rng.randf_range(-arena.x / 2.0 + 1.5, arena.x / 2.0 - 1.5), 0, rng.randf_range(-arena.y / 2.0 + 1.5, arena.y / 2.0 - 1.5))
		if at.length() < 3.0:
			continue
		if i % 3 == 0:
			_piece("column", at, rng.randf_range(0, 360), 0.55)
			obstacles.append(Vector3(at.x, at.z, 0.5))
		else:
			_piece("rubble_half" if i % 2 == 0 else "rubble_large", at, rng.randf_range(0, 360), 0.5)
			obstacles.append(Vector3(at.x, at.z, 0.7))
	if spec.has("post"):
		var pa := Vector3(float(spec["post"]["at"][0]), 0, float(spec["post"]["at"][1]))
		_piece("column", pa, 0.0, 0.45)
		obstacles.append(Vector3(pa.x, pa.z, 0.6))
		var ring := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 3.4
		tm.outer_radius = 3.55
		ring.mesh = tm
		ring.scale = Vector3(1, 0.05, 1)
		ring.position = pa + Vector3(0, 0.12, 0)
		ring.material_override = _mat(Color(0.55, 0.75, 1.0), 2.0, true, 0.5)
		_place_root.add_child(ring)
		var lamp := OmniLight3D.new()
		lamp.light_color = Color(0.6, 0.78, 1.0)
		lamp.light_energy = 1.8
		lamp.omni_range = 8.0
		lamp.position = pa + Vector3(0, 2.2, 0)
		_place_root.add_child(lamp)
		var flame := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.2
		sm.height = 0.4
		flame.mesh = sm
		flame.material_override = _mat(Color(0.6, 0.8, 1.0), 4.0, true)
		flame.position = pa + Vector3(0, 1.55, 0)
		_place_root.add_child(flame)

func _furnish_quad() -> void:
	# The middle of the quad: a brazier that never goes out; the decorated pillars stand in its corners.
	for c in [Vector2(-12, -8), Vector2(12, -8), Vector2(-12, 8.5), Vector2(12, 8.5)]:
		_piece("pillar_decorated", Vector3(c.x, 0, c.y), 0.0)
		obstacles.append(Vector3(c.x, c.y, 0.9))
	var lamp := OmniLight3D.new()
	lamp.light_color = Color(1.0, 0.72, 0.42)
	lamp.light_energy = 2.2
	lamp.omni_range = 10.0
	lamp.position = Vector3(0, 2.2, 0)
	_place_root.add_child(lamp)
	_torches.append(lamp)
	_piece("column", Vector3(0, 0, 0), 0.0, 0.4)
	var flame := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.28
	sm.height = 0.5
	flame.mesh = sm
	flame.material_override = _mat(Color(1.0, 0.7, 0.35), 4.0, true)
	flame.position = Vector3(0, 1.45, 0)
	_place_root.add_child(flame)
	obstacles.append(Vector3(0, 0, 0.7))
	for b in [[-9.0, -10.4, 0.0], [9.0, -10.4, 0.0], [-5.0, 10.4, 180.0], [5.0, 10.4, 180.0]]:
		_piece("banner_patternA_red", Vector3(b[0], 0.6, b[1]), b[2])
	_piece("barrel_large", Vector3(12.5, 0, 8.5), 30.0, 0.6)
	_piece("crates_stacked", Vector3(-13.0, 0, 9.0), 10.0, 0.6)
	_piece("barrel_small_stack", Vector3(-13.0, 0, -9.0), 0.0, 0.7)

func _furnish_yard() -> void:
	# Pillars in the corners, clear of the ring and of the camera behind whoever is sparring.
	for p in [Vector3(-9.5, 0, -5.8), Vector3(9.5, 0, -5.8), Vector3(9.5, 0, 5.8)]:
		_piece("pillar", p, 0.0, 0.7)
		obstacles.append(Vector3(p.x, p.z, 0.6))
	_piece("crates_stacked", Vector3(9.0, 0, 5.0), 0.0, 0.6)
	_piece("barrel_large", Vector3(7.0, 0, 5.4), 15.0, 0.6)
	_piece("rubble_half", Vector3(-3.0, 0, 6.2), 180.0, 0.5)
	_piece("banner_patternA_red", Vector3(0.0, 0.6, -7.55), 0.0)
	# The ward ring: the circle the drills are fought in.
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 4.6
	tm.outer_radius = 4.75
	ring.mesh = tm
	ring.scale = Vector3(1, 0.05, 1)
	ring.position = Vector3(0, 0.12, 0)
	ring.material_override = _mat(Color(0.55, 0.75, 1.0), 2.0, true, 0.55)
	_place_root.add_child(ring)

func _furnish_dorm(spec: Dictionary) -> void:
	# Bunks: wooden frames with blankets, two rows.
	var wood := _mat(Color(0.32, 0.2, 0.12))
	var cloth := [Color(0.45, 0.2, 0.18), Color(0.2, 0.28, 0.4), Color(0.3, 0.35, 0.22), Color(0.5, 0.42, 0.3)]
	var n := 0
	for row in [-3.4, 3.4]:
		for bx in [-2.0, 1.0, 4.0]:
			var frame := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(1.2, 0.45, 2.2)
			frame.mesh = bm
			frame.material_override = wood
			frame.position = Vector3(bx, 0.35, row)
			obstacles.append(Vector3(bx, row - 0.55, 0.65))
			obstacles.append(Vector3(bx, row + 0.55, 0.65))
			_place_root.add_child(frame)
			var blanket := MeshInstance3D.new()
			var cm := BoxMesh.new()
			cm.size = Vector3(1.1, 0.12, 1.5)
			blanket.mesh = cm
			blanket.material_override = _mat(cloth[n % cloth.size()])
			blanket.position = Vector3(bx, 0.62, row + (0.3 if row > 0 else -0.3))
			_place_root.add_child(blanket)
			n += 1
	_piece("barrel_small_stack", Vector3(5.6, 0, 0.0), 0.0, 0.6)

## The party beside the hero: bodies that follow the fight's allies.
func set_allies(specs: Array) -> void:
	for a in _ally_nodes:
		(a["node"] as Node).queue_free()
	_ally_nodes.clear()
	for sp in specs:
		var n: Node3D = load("res://game/assets/kaykit/%s.glb" % sp.get("body", "Knight")).instantiate()
		add_child(n)
		for a in n.find_children("*", "BoneAttachment3D", true, false):
			var an := String(a.name)
			a.visible = an.contains("Helmet") or an.contains("Hat") or an.contains("Cape") or an.contains("Hood")
		var skel: Skeleton3D = n.find_child("Skeleton3D", true, false)
		var w: Dictionary = Data.by_id(Data.weapons, sp.get("weapon", "saber"))
		_attach(skel, "handslot.r", "res://game/assets/kaykit/weapons/%s.gltf" % w["model"])
		if w.has("offhand"):
			_attach(skel, "handslot.l", "res://game/assets/kaykit/weapons/%s.gltf" % w["offhand"])
		for m in n.find_children("*", "MeshInstance3D", true, false):
			m.material_overlay = _ink(2.0)
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		for loop in ["Idle", "Running_A"]:
			if ap.has_animation(loop):
				ap.get_animation(loop).loop_mode = Animation.LOOP_LINEAR
		ap.play("Idle")
		var l := Label3D.new()
		l.text = sp.get("name", "")
		l.font = Style.font("title")
		l.font_size = 22
		l.fixed_size = true
		l.pixel_size = 0.001
		l.modulate = Color(0.8, 0.9, 1.0, 0.85)
		l.outline_size = 8
		l.outline_modulate = Color(0, 0, 0, 0.8)
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.position = Vector3(0, 2.3, 0)
		n.add_child(l)
		_ally_nodes.append({ "node": n, "anim": ap, "cur": "Idle", "until": 0.0 })

func _update_allies(f: Fight, dt: float) -> void:
	for i in mini(_ally_nodes.size(), f.allies.size()):
		var a: Dictionary = _ally_nodes[i]
		var al: Dictionary = f.allies[i]
		var n: Node3D = a["node"]
		n.position = _v3(al["pos"])
		n.rotation.y = _yaw(float(al["facing"]))
		# Never between the camera and the hero.
		n.visible = camera.global_position.distance_to(n.global_position + Vector3(0, 1.0, 0)) > 2.4
		var ap: AnimationPlayer = a["anim"]
		if _clock < float(a["until"]):
			continue
		var want := "Death_A" if al["down"] else ("Running_A" if al["moving"] else "Idle")
		if want != a["cur"]:
			a["cur"] = want
			ap.play(want, 0.15)
			if want == "Death_A":
				a["until"] = _clock + 99.0

func _ally_event(f: Fight, e: Dictionary) -> void:
	var i := int(e.get("who", -1))
	if i < 0 or i >= _ally_nodes.size() or i >= f.allies.size():
		return
	var a: Dictionary = _ally_nodes[i]
	var ap: AnimationPlayer = a["anim"]
	var at := _v3(f.allies[i]["pos"], 1.2)
	match String(e["type"]):
		"ally-hit":
			ap.play("1H_Melee_Attack_Slice_Horizontal", 0.05)
			a["cur"] = "attack"
			a["until"] = _clock + 0.5
			impact(_v3(f.w_pos, 0.9), Color(0.8, 0.9, 1.0), 0.5)
			floater(_v3(f.w_pos, 1.8) + Vector3(-0.4, 0.3, 0), "%d" % int(e["damage"]), Color(0.75, 0.85, 1.0), 40, 0.7)
		"ally-hurt":
			ap.play("Hit_A", 0.05)
			a["cur"] = "hurt"
			a["until"] = _clock + 0.5
			floater(at + Vector3(0, 0.6, 0), "-%d" % int(e["damage"]), C_WINDUP, 44, 0.8)
		"ally-down":
			a["until"] = 0.0
			a["cur"] = ""
			floater(at + Vector3(0, 0.8, 0), "%s IS DOWN" % String(f.allies[i]["name"]).to_upper(), C_WINDUP, 56, 1.8)
		"ally-up":
			a["until"] = 0.0
			a["cur"] = ""
			_ring_wave(_v3(f.allies[i]["pos"]), Color(0.6, 0.8, 1.0), 2.0)
			floater(at + Vector3(0, 0.8, 0), "%s STANDS" % String(f.allies[i]["name"]).to_upper(), Color(0.6, 0.8, 1.0), 48, 1.4)

## Someone standing in the place: a body, a weapon, their name and what they are over the head.
func add_figure(body: String, at: Vector2, facing: float, title: String, sub: String, weapon := "", tint := Color(0, 0, 0, 0)) -> Dictionary:
	var n: Node3D = load("res://game/assets/kaykit/%s.glb" % body).instantiate()
	_place_root.add_child(n)
	for a in n.find_children("*", "BoneAttachment3D", true, false):
		var an := String(a.name)
		a.visible = an.contains("Helmet") or an.contains("Hat") or an.contains("Cape") or an.contains("Hood")
	var skel: Skeleton3D = n.find_child("Skeleton3D", true, false)
	if weapon != "":
		var w: Dictionary = Data.by_id(Data.weapons, weapon)
		_attach(skel, "handslot.r", "res://game/assets/kaykit/weapons/%s.gltf" % w["model"])
		if w.has("offhand"):
			_attach(skel, "handslot.l", "res://game/assets/kaykit/weapons/%s.gltf" % w["offhand"])
	var over := _mat(C_HIT, 0.0, true, 0.0)
	over.albedo_color = tint
	over.next_pass = _ink(2.0)
	for m in n.find_children("*", "MeshInstance3D", true, false):
		m.material_overlay = over
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap.has_animation("Idle"):
		ap.get_animation("Idle").loop_mode = Animation.LOOP_LINEAR
		ap.play("Idle", 0.0, randf_range(0.85, 1.1))
		ap.seek(randf() * 2.0, true)
	n.position = _v3(at)
	n.rotation.y = _yaw(facing)
	var l := Label3D.new()
	l.text = title + ("\n" + sub if sub != "" else "")
	l.font = Style.font("title")
	l.font_size = 26
	l.fixed_size = true
	l.pixel_size = 0.0011
	l.modulate = Color(0.95, 0.91, 0.84, 0.0)
	l.outline_size = 8
	l.outline_modulate = Color(0, 0, 0, 0.0)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.position = _v3(at, 2.55)
	_place_root.add_child(l)
	obstacles.append(Vector3(at.x, at.y, 0.45))
	var fig := { "node": n, "anim": ap, "pos": at, "facing": facing, "label": l, "home": facing }
	_figures.append(fig)
	return fig

## People turn to look at the hero when they come near, and their names show.
func _update_figures(f: Fight, dt: float) -> void:
	for fig in _figures:
		var d: float = (f.p_pos - fig["pos"]).length()
		var want: float = (f.p_pos - fig["pos"]).angle() if d < 4.5 else fig["home"]
		fig["facing"] = lerp_angle(fig["facing"], want, 1.0 - exp(-dt * 4.0))
		(fig["node"] as Node3D).rotation.y = _yaw(fig["facing"])
		var l: Label3D = fig["label"]
		var a := clampf((7.0 - d) / 3.0, 0.0, 1.0)
		# In a scene, names stand down, and no one stands between the camera and what matters.
		var node: Node3D = fig["node"]
		if cine:
			a = 0.0
			node.visible = camera.global_position.distance_to(node.global_position + Vector3(0, 1.0, 0)) > 2.6
		else:
			node.visible = true
		l.modulate.a = move_toward(l.modulate.a, a, dt * 3.0)
		l.outline_modulate.a = l.modulate.a * 0.8

## Put the camera straight behind the hero along the current yaw, with no glide in.
func snap_camera_behind(f: Fight) -> void:
	var back := Vector3(sin(cam_yaw), 0, cos(cam_yaw))
	cam_pitch = -0.32
	_cam_pos = _v3(f.p_pos) + back * 6.0 + Vector3(0, 3.2, 0)
	_cam_look = _v3(f.p_pos, 1.4)

# --- The Hearth Hall and the rite ------------------------------------------------

var bowl_flame: MeshInstance3D
var bowl_flame_mat: StandardMaterial3D
var bowl_light: OmniLight3D
var _sigils: Array = []        # the six Shapes' lights around the bowl during the reading
var _pillar: MeshInstance3D    # the column of light when the genius is made

const BOWL := Vector3(0, 0, -1.2)

func _furnish_hearth() -> void:
	# The bowl: a broad stone basin on a short column, with the fire in it.
	_piece("column", BOWL, 0.0, 0.5)
	var rim := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.7
	tm.outer_radius = 1.0
	rim.mesh = tm
	rim.position = BOWL + Vector3(0, 1.05, 0)
	rim.material_override = _mat(Color(0.35, 0.3, 0.27))
	_place_root.add_child(rim)
	var basin := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.85
	cm.bottom_radius = 0.4
	cm.height = 0.4
	basin.mesh = cm
	basin.position = BOWL + Vector3(0, 0.85, 0)
	basin.material_override = _mat(Color(0.3, 0.26, 0.24))
	_place_root.add_child(basin)
	obstacles.append(Vector3(BOWL.x, BOWL.z, 1.1))
	bowl_flame = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.45
	sm.height = 0.9
	bowl_flame.mesh = sm
	bowl_flame_mat = _mat(Color(1.0, 0.65, 0.3), 4.0, true)
	bowl_flame_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	bowl_flame.material_override = bowl_flame_mat
	bowl_flame.position = BOWL + Vector3(0, 1.35, 0)
	bowl_flame.scale = Vector3(0.6, 0.8, 0.6)
	_place_root.add_child(bowl_flame)
	bowl_light = OmniLight3D.new()
	bowl_light.light_color = Color(1.0, 0.65, 0.35)
	bowl_light.light_energy = 2.0
	bowl_light.omni_range = 9.0
	bowl_light.position = BOWL + Vector3(0, 2.0, 0)
	_place_root.add_child(bowl_light)
	# A ring on the floor round the bowl, where the student stands.
	var ring := MeshInstance3D.new()
	var rt := TorusMesh.new()
	rt.inner_radius = 2.6
	rt.outer_radius = 2.72
	ring.mesh = rt
	ring.scale = Vector3(1, 0.05, 1)
	ring.position = BOWL + Vector3(0, 0.12, 0)
	ring.material_override = _mat(Color(1.0, 0.75, 0.4), 1.5, true, 0.5)
	_place_root.add_child(ring)
	for b in [[-4.0, -9.4, 0.0], [4.0, -9.4, 0.0]]:
		_piece("banner_patternA_red", Vector3(b[0], 0.6, b[1]), b[2])
	for c in [Vector2(-6.5, -6.5), Vector2(6.5, -6.5)]:
		_piece("pillar_decorated", Vector3(c.x, 0, c.y), 0.0)
		obstacles.append(Vector3(c.x, c.y, 0.9))

## How dark the hall falls while the bowl reads (0: as lit; 1: only the bowl).
func dim(k: float) -> void:
	for t in _torches:
		(t as OmniLight3D).light_energy = lerpf(1.5, 0.15, k)
	_env.ambient_light_energy = lerpf(0.34, 0.08, k)
	_torch_dim = k

var _torch_dim := 0.0

## The bowl's fire: its colour and how high it burns.
func flame(color: Color, size: float, energy := 4.0) -> void:
	if not bowl_flame:
		return
	bowl_flame_mat.albedo_color = color
	bowl_flame_mat.emission = color
	bowl_flame_mat.emission_energy_multiplier = energy
	bowl_flame.scale = Vector3(0.6, 0.85, 0.6) * size
	bowl_flame.position = BOWL + Vector3(0, 1.2 + 0.25 * size, 0)
	bowl_light.light_color = color
	bowl_light.light_energy = 1.0 + 1.6 * size

## The six Shapes' lights, in a ring above the bowl. lit: the one the reading is passing.
func sigils(show: bool, lit := "", turn := 0.0) -> void:
	if show and _sigils.is_empty():
		for s in Creation.SHAPES:
			var m := MeshInstance3D.new()
			var sm := SphereMesh.new()
			sm.radius = 0.16
			sm.height = 0.32
			m.mesh = sm
			var mat := _mat(SHAPE_COLORS[s], 1.0, true)
			m.material_override = mat
			var l := Label3D.new()
			l.text = s.to_upper()
			l.font = Style.font("title")
			l.font_size = 22
			l.pixel_size = 0.006
			l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			l.modulate = Color(SHAPE_COLORS[s], 0.5)
			l.outline_size = 6
			l.outline_modulate = Color(0, 0, 0, 0.8)
			l.position = Vector3(0, 0.38, 0)
			m.add_child(l)
			_place_root.add_child(m)
			_sigils.append({ "shape": s, "m": m, "mat": mat, "l": l })
	for i in _sigils.size():
		var sg: Dictionary = _sigils[i]
		var m: MeshInstance3D = sg["m"]
		m.visible = show
		if not show:
			continue
		var a := turn + i * TAU / 6.0
		m.position = BOWL + Vector3(cos(a) * 1.9, 2.3 + 0.1 * sin(_clock * 3.0 + i), sin(a) * 1.9)
		var on: bool = sg["shape"] == lit
		(sg["mat"] as StandardMaterial3D).emission_energy_multiplier = 6.0 if on else 0.6
		m.scale = Vector3.ONE * (1.6 if on else 0.8)
		(sg["l"] as Label3D).modulate.a = 1.0 if on else 0.35

## The column of light that stands in the bowl while the genius is made.
func light_pillar(height: float, color: Color) -> void:
	if not _pillar:
		_pillar = MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.5
		cm.bottom_radius = 0.7
		cm.height = 1.0
		cm.cap_top = false
		cm.cap_bottom = false
		_pillar.mesh = cm
		_pillar.material_override = _shader_mat(SHAFT)
		_place_root.add_child(_pillar)
	_pillar.visible = height > 0.01
	(_pillar.material_override as ShaderMaterial).set_shader_parameter("tint", color)
	(_pillar.material_override as ShaderMaterial).set_shader_parameter("strength", 0.9)
	(_pillar.material_override as ShaderMaterial).set_shader_parameter("half_height", height / 2.0)
	_pillar.mesh.height = maxf(height, 0.01)
	_pillar.position = BOWL + Vector3(0, 1.2 + height / 2.0, 0)

const SILHOUETTE := """
shader_type spatial;
// A genius before there is art for it: a body of shadow lit at the edges in its colour,
// like a figure seen against the fire.
render_mode cull_back;
uniform vec4 glow : source_color = vec4(1.0, 0.7, 0.3, 1.0);
uniform float strength = 1.0;
void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.4);
	ALBEDO = vec3(0.03, 0.025, 0.03);
	EMISSION = glow.rgb * (rim * 3.2 + 0.25) * strength;
	ROUGHNESS = 0.9;
}
"""

## The genius's body, from its silhouette and features (genius_body.gd: art if there is any,
## placeholders if not).
func make_form(info: Dictionary, color: Color) -> Node3D:
	var gb := GeniusBody.build(info, color, int(info.get("instar", 1)))
	for m in gb.find_children("*", "MeshInstance3D", true, false):
		(m as MeshInstance3D).material_overlay = _ink(1.6)
	return gb

func _sphere(r: float) -> SphereMesh:
	var m := SphereMesh.new()
	m.radius = r
	m.height = r * 2.0
	m.radial_segments = 16
	m.rings = 8
	return m

func _cone(r: float, h: float) -> CylinderMesh:
	var m := CylinderMesh.new()
	m.top_radius = 0.0
	m.bottom_radius = r
	m.height = h
	return m

func _box(size: Vector3) -> BoxMesh:
	var m := BoxMesh.new()
	m.size = size
	return m

## Give the genius its First Form: the orb goes, the form stays, and follows from now on.
func set_form(info: Dictionary, form: Node3D) -> void:
	if _g_form and _g_form != form:
		_g_form.queue_free()
	_g_form = form
	_g_form_info = info
	_g_body = form as GeniusBody
	if form.get_parent() == null:
		add_child(form)
	elif form.get_parent() != self:
		form.reparent(self)
	_g_form_pos = form.global_position
	_genius.visible = false
	_g_trail.emitting = false

func clear_form() -> void:
	if _g_form:
		_g_form.queue_free()
	_g_form = null
	_g_form_info = {}
	_g_form_anim = null
	_g_body = null

## The First Form follows: fliers and fey and flames at the shoulder, walkers at the heel.
func _update_form(f: Fight, dt: float) -> void:
	_genius.visible = false
	_g_trail.emitting = false
	var walker := _g_body != null and _g_body.walks()
	var side := Vector2.from_angle(f.p_facing + (2.2 if walker else 1.9))
	var want := _v3(f.p_pos + side * (1.1 if walker else 0.8), 0.0 if walker else 1.5 + 0.08 * sin(_clock * 2.4))
	if genius_goal != Vector3.INF:
		want = genius_goal
	if _clock < _g_dart_until:
		want = _g_dart_at
	var before := _g_form_pos
	_g_form_pos = _g_form_pos.lerp(want, 1.0 - exp(-dt * (4.0 if walker else 6.0)))
	_g_form.global_position = _g_form_pos
	var vel := (_g_form_pos - before) / maxf(dt, 1e-4)
	var flat := Vector2(vel.x, vel.z)
	if flat.length() > 0.3:
		_g_form_facing = lerp_angle(_g_form_facing, flat.angle(), 1.0 - exp(-dt * 8.0))
	else:
		_g_form_facing = lerp_angle(_g_form_facing, f.p_facing, 1.0 - exp(-dt * 3.0))
	_g_form.rotation.y = _yaw(_g_form_facing)
	# Fallen, it lies on its side where it fell.
	_g_form.rotation.z = lerpf(_g_form.rotation.z, PI / 2.0 if genius_down else 0.0, 1.0 - exp(-dt * 6.0))
	if genius_down:
		_g_form_pos = _g_form_pos.lerp(Vector3(_g_form_pos.x, 0.15, _g_form_pos.z), 1.0 - exp(-dt * 4.0))
		_g_form.global_position = _g_form_pos
	if _g_body:
		_g_body.move_at(flat.length())
