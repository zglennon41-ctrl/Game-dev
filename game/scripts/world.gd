## The 3D room: a chamber in the Cumberland Cut built from KayKit Dungeon pieces, the Anchor
## (KayKit Knight) and the cut-wolf (Quaternius Wolf), animated; telegraphs, hit feedback,
## hit-stop, the parry's slow motion, a third-person camera with lock-on.
## Art: KayKit (Kay Lousberg) and Quaternius, both CC0. Placeholder for the game's own art.
class_name World
extends Node3D

# The colours of what happens in a fight (data/style.json, effects.colors and loud).
static var C_STANCE: Color
static var C_WINDUP: Color
static var C_STAGGER: Color
static var C_HIT: Color
static var C_GUARD: Color
static var C_TEXT: Color
static var C_DIM: Color
static var C_GOLD: Color
## The six Shapes' colours: the field's, and the only loud thing a partner owns.
static var SHAPE_COLORS: Dictionary = {}

static func _static_init() -> void:
	C_STANCE = Style.shape_color("anchor")
	C_WINDUP = Style.telegraph()
	C_STAGGER = Style.fx("stagger")
	C_HIT = Style.fx("spark")
	C_GUARD = Style.fx("guard")
	C_TEXT = Style.fx("text")
	C_DIM = Style.fx("dim")
	C_GOLD = Style.GOLD
	for sh in Style.data()["loud"]["shapes"]:
		SHAPE_COLORS[sh] = Style.shape_color(sh)
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
var portrait_frame := ""    # the creator's framing: wide, full, half or face (data/creation.json, stage.frames); "" is the title's
var portrait_shift := 0.0   # the part of the screen's width a panel covers on the right: the figure centres in what is left
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
	toonify(n)
	return n

func _build_environment() -> void:
	var env := Environment.new()
	var cut := Style.place_light("cut")
	var film: Dictionary = Style.data()["film"]
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(String(cut["sky"]))
	# The ambient from a sky: the tops of forms lit cooler and lighter than their undersides.
	if Style.data()["shading"].get("sky", true):
		var moon_cast := Style.light("moon")
		var sky_mat := ProceduralSkyMaterial.new()
		sky_mat.sky_top_color = moon_cast.darkened(0.7)
		sky_mat.sky_horizon_color = Color(String(cut["ambient"])).darkened(0.58)
		sky_mat.ground_bottom_color = Style.ramp_at("ink", 2)
		sky_mat.ground_horizon_color = Style.ramp_at("ink", 3)
		sky_mat.sun_angle_max = 10.0
		sky_mat.sun_curve = 0.2
		var sky := Sky.new()
		sky.sky_material = sky_mat
		env.sky = sky
		env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
		env.ambient_light_sky_contribution = 1.0
		env.ambient_light_energy = 0.55
	else:
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = Color(String(cut["ambient"]))
		env.ambient_light_energy = float(cut["ambientEnergy"])
	env.fog_enabled = true
	env.fog_light_color = Color(String(cut["fog"]))
	env.fog_density = float(cut["fogDensity"])
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = float(film.get("exposure", 0.9))
	env.glow_enabled = true
	env.glow_intensity = float(film.get("glow", 0.7))
	env.glow_bloom = float(film.get("bloom", 0.08))
	env.adjustment_enabled = true
	env.adjustment_contrast = float(film.get("contrast", 1.0))
	env.adjustment_saturation = float(film.get("saturation", 1.0))
	_env = env
	_ambient_default = env.ambient_light_source
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	# Moonlight through the broken roof of the Cut: cool, from above, casting the shadows.
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-62, -35, 0)
	moon.light_color = Style.light("moon")
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 40.0
	moon.shadow_blur = 2.0
	moon.shadow_normal_bias = 1.5
	moon.light_energy = 0.42
	add_child(moon)
	_moon = moon

## The light of a kind of place (data/style.json, lights.kinds: hall, court, wild, cut, stage):
## the dark behind it, its ambient, its fog and how strong the moon stands. A place's own
## numbers (a zone's, a hall's) are given over the kind's.
func _light_place(kind: String, over: Dictionary = {}) -> void:
	var L := Style.place_light(kind)
	_env.background_color = Color(String(over.get("sky", L["sky"])))
	_env.ambient_light_color = Color(String(over.get("ambient", L["ambient"])))
	_env.ambient_light_energy = float(over.get("ambientEnergy", L["ambientEnergy"]))
	_env.fog_light_color = Color(String(over.get("fog", L["fog"])))
	_env.fog_density = float(over.get("fogDensity", L["fogDensity"]))
	_moon.light_color = Color(String(over["moonColor"])) if over.has("moonColor") else Style.light("moon")
	_moon.light_energy = float(over.get("moon", L["moon"])) * Style.light_energy("moon")

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
				light.light_color = Style.light("fire")
				light.light_energy = 1.5 * Style.light_energy("fire")
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
	_player = load(_person_model(hero.get("body", "Knight"))).instantiate()
	add_child(_player)
	toonify(_player)
	dress(_player, hero.get("look", {}), hero)
	var skel: Skeleton3D = _player.find_child("Skeleton3D", true, false)
	var w: Dictionary = Data.by_id(Data.weapons, hero.get("weapon", "saber"))
	_sword = _attach(skel, "handslot.r", _weapon_model(w["model"]))
	_offhand = _attach(skel, "handslot.l", _weapon_model(w["offhand"])) if w.has("offhand") else null
	_p_anim = _player.find_child("AnimationPlayer", true, false)
	for loop in ["Idle", "Running_A", "Running_Strafe_Left", "Running_Strafe_Right", "Walking_Backwards", "Walking_A", "Blocking", "Death_A_Pose", "1H_Ranged_Aiming", "2H_Ranged_Aiming", "Spellcasting"]:
		if _p_anim.has_animation(loop):
			_p_anim.get_animation(loop).loop_mode = Animation.LOOP_LINEAR
	_p_current = ""
	_p_meshes = _player.find_children("*", "MeshInstance3D", true, false)
	_overlay_player = _mat(C_HIT, 2.0, true, 0.0)
	_overlay_player.next_pass = _ink("people")
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
	_glow_weapon(hero)
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
	var scene := load(path)
	if scene == null:
		push_warning("WEAPON MODEL MISSING: %s" % path)
		return att
	var model: Node3D = scene.instantiate()
	# Guns and bows are built along the back of the hand (KayKit's crossbow convention) and
	# would point across the body when aimed: turned a quarter so the barrel points forward.
	var base := path.get_file().get_basename()
	if base in RANGED_MODELS:
		model.rotate_y(PI / 2.0)
	att.add_child(model)
	toonify(model)
	return att

const RANGED_MODELS := ["pistol", "air_pistol", "musket", "bolt_thrower", "seed_sling", "bow_short", "bow_long", "astrolabe", "chakram", "crossbow_1handed", "crossbow_2handed"]


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
	# A kit body takes the blood as features (dress); a KayKit body is washed over whole.
	if _has_skin(_player):
		return
	if BLOOD_TINTS.has(blood_id):
		_tint = Color(BLOOD_TINTS[blood_id], 0.22)
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
			_glow_light.light_color = Style.light("lamp")
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
		_wolf = load(_beast_model(String(spec.get("model", "")))).instantiate()
		_wolf.scale = Vector3.ONE * WOLF_SCALE * float(spec.get("wolf_scale", 1.0))
		_w_anims = WOLF_ANIMS
	else:
		_wolf = load(_person_model(spec.get("body", "Knight"))).instantiate()
		_w_anims = PERSON_ANIMS
		dress(_wolf, spec["look"] if not spec.get("look", {}).is_empty() else look_for(String(spec.get("name", ""))))
		var skel: Skeleton3D = _wolf.find_child("Skeleton3D", true, false)
		if spec.get("weapon", "") != "":
			var w: Dictionary = Data.by_id(Data.weapons, spec["weapon"])
			_attach(skel, "handslot.r", _weapon_model(w["model"]))
			if w.has("offhand"):
				_attach(skel, "handslot.l", _weapon_model(w["offhand"]))
	add_child(_wolf)
	toonify(_wolf)
	_w_anim = _wolf.find_child("AnimationPlayer", true, false)
	for key in ["idle", "walk", "gallop", "windup", "stagger", "flinch"]:
		if _w_anim.has_animation(_w_anims[key]):
			_w_anim.get_animation(_w_anims[key]).loop_mode = Animation.LOOP_LINEAR
	_w_meshes = _wolf.find_children("*", "MeshInstance3D", true, false)
	_overlay_wolf = _mat(C_WINDUP, 2.0, true, 0.0)
	_overlay_wolf.next_pass = _ink("beasts")
	for m in _w_meshes:
		m.material_overlay = _overlay_wolf
	_w_current = ""
	_w_oneshot_until = 0.0

const CITY_COLORS := { "columbia": Color(0.2, 0.35, 0.75), "cahokia": Color(0.25, 0.55, 0.5), "lunden": Color(0.55, 0.55, 0.6), "colonia": Color(0.7, 0.45, 0.2),
	"tiber": Color(0.7, 0.15, 0.15), "khemet": Color(0.15, 0.4, 0.2), "baghdad": Color(0.2, 0.5, 0.7), "varanasi": Color(0.85, 0.5, 0.15), "jiangnan": Color(0.5, 0.15, 0.3),
	"kazan": Color(0.45, 0.3, 0.15), "timbuktu": Color(0.75, 0.6, 0.25), "edo": Color(0.15, 0.15, 0.2) }

## What the bloods that show in the skin do to it (until their marks are parts and surfaces).
const BLOOD_TINTS := { "ridgefolk": Color(0.55, 0.55, 0.6), "fogborn": Color(0.75, 0.8, 0.9), "mound-kin": Color(0.6, 0.35, 0.2),
	"greenwood": Color(0.3, 0.7, 0.3), "forgeborn": Color(0.25, 0.15, 0.1), "ironblooded": Color(0.3, 0.32, 0.4),
	"tidewater": Color(0.3, 0.6, 0.7), "nightfolk": Color(0.2, 0.1, 0.3), "dragon-blooded": Color(0.2, 0.55, 0.35), "fused": Color(0.45, 0.32, 0.2) }

## Does a body carry the kit's skin material (a body of the body kit, not KayKit's)?
func _has_skin(node: Node) -> bool:
	if node == null:
		return false
	for m in node.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		if mi.mesh:
			for i in mi.mesh.get_surface_count():
				var mat := mi.get_active_material(i)
				if mat and String(mat.resource_name) == "skin":
					return true
	return false

## Every person wears their look: headgear and cape on or off, the hair and beard the look
## names and the hair's colour, the cape's colour, and the stature. The hair's cap hides under
## headgear and under a hood; its fall hangs from under them either way.
func dress(node: Node3D, look: Dictionary, hero: Dictionary = {}) -> void:
	var has_headgear := node.find_child("*Helmet*", true, false) != null or node.find_child("*Hat*", true, false) != null or node.find_child("Headgear_*", true, false) != null
	var headgear: bool = look.get("headgear", true) and has_headgear
	var hooded := node.find_child("*Hooded*", true, false) != null
	# The build blends the body's lean and heavy shape keys; the skin takes the chosen tone.
	var build := clampf(float(look.get("build", 0.0)), -1.0, 1.0)
	var tone := skin_color(String(look.get("skin", "")))
	# The features: the blood's marks and whatever else the character carries
	# (data/people-features.json). Tints blend into the skin; eyes colour the iris; parts hang
	# on the sockets; a glow lights the skin.
	var feats := features_of(hero, look)
	var shape_col := _shape_color(String(hero.get("shape", "anchor")))
	# what the echo is drawn in: the genius's own coat, how far it has come
	var gd: Dictionary = hero.get("genius", {}) if hero.get("genius", {}) is Dictionary else {}
	var g_instar := int(gd.get("instar", 0))
	var g_coat := genius_coat(gd, shape_col)
	var echo_cfg: Dictionary = Data.genius().get("echo", {})
	var echo_grow := float(echo_cfg.get("grow", {}).get(str(g_instar), 1.0))
	var echo_field := float(echo_cfg.get("field", {}).get(str(g_instar), 1.0))
	var iris := Color(0.12, 0.09, 0.07)
	var iris_glow := 0.0
	var glow := Color(0, 0, 0)
	var glow_k := 0.0
	var cape_thread := 0.0
	for fid in feats:
		var f: Dictionary = Data.people_features.get(fid, {})
		match String(f.get("kind", "")):
			"tint":
				var t: Array = f.get("tint", [0.5, 0.5, 0.5])
				tone = tone.lerp(Color(t[0], t[1], t[2]), float(f.get("strength", 0.5)))
			"eyes":
				var c: Array = f.get("iris", [0.1, 0.1, 0.1])
				iris = shape_col if f.get("shapeColor", "") == "iris" else Color(c[0], c[1], c[2])
				iris_glow = float(f.get("emission", 0.0))
			"glow":
				var g: Array = f.get("glow", [1.0, 0.85, 0.55])
				glow = shape_col if f.get("shapeColor", "") == "glow" else Color(g[0], g[1], g[2])
				glow_k = float(f.get("strength", 0.35)) * (echo_field if f.get("shapeColor", "") == "glow" else 1.0)
			"cape":
				cape_thread = float(f.get("strength", 0.5))
	var skel: Skeleton3D = node.find_child("Skeleton3D", true, false)
	for m in node.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		var li := mi.find_blend_shape_by_name("lean")
		var hi := mi.find_blend_shape_by_name("heavy")
		if li >= 0:
			mi.set_blend_shape_value(li, maxf(0.0, -build))
		if hi >= 0:
			mi.set_blend_shape_value(hi, maxf(0.0, build))
		_recolor_named(mi, "skin", tone, glow, glow_k)
		_recolor_named(mi, "lips", lip_color(tone), glow, glow_k * 0.5)
		_recolor_named(mi, "iris", iris, iris, iris_glow)
	if skel:
		for a in skel.get_children():
			if a is BoneAttachment3D and String(a.name).begins_with("feature_"):
				skel.remove_child(a)
				a.queue_free()
		for fid in feats:
			var f: Dictionary = Data.people_features.get(fid, {})
			if String(f.get("kind", "")) != "part":
				continue
			for sock in f.get("sockets", []):
				if skel.find_bone(sock) < 0:
					continue
				var att := _attach(skel, sock, "res://game/assets/people/parts/%s.glb" % String(f["part"]))
				att.name = "feature_%s_%s" % [fid, sock]
				# A hand part is built for the left hand; the right wears its mirror.
				if String(sock).ends_with("_r") and att.get_child_count() > 0:
					(att.get_child(0) as Node3D).scale.x = -1.0
				if f.get("shapeColor", "") == "trim":
					for m2 in att.find_children("*", "MeshInstance3D", true, false):
						_recolor_named(m2, "trim", shape_col, shape_col, 0.6)
				if f.get("color", "") == "genius":
					# an echo of the genius: in its coat, its light in the field's colour, grown with it
					for m2 in att.find_children("*", "MeshInstance3D", true, false):
						_recolor_named(m2, "echo", g_coat)
						_recolor_named(m2, "echo_glow", shape_col, shape_col, 1.6)
					if att.get_child_count() > 0:
						(att.get_child(0) as Node3D).scale *= echo_grow
		# A kit body's cloak is a part on the back socket, in the colour the look names, and
		# threaded with the bonded genius's colour once there is one.
		if look.get("cape", true) and skel.find_bone("socket_back") >= 0:
			var cape := _attach(skel, "socket_back", "res://game/assets/people/parts/cape.glb")
			cape.name = "feature_cape_socket_back"
			var col := cape_color_for(hero, String(look.get("cape_color", "shape")))
			if cape_thread > 0.0:
				col = col.lerp(g_coat, cape_thread)
			_recolor(cape, col)
	if glow_k > 0.0 and node == _player:
		if _glow_light == null:
			_glow_light = OmniLight3D.new()
			_player.add_child(_glow_light)
		_glow_light.light_color = glow
		_glow_light.light_energy = 0.8
		_glow_light.omni_range = 3.0
		_glow_light.position = Vector3(0, 1.4, 0)
	var hair := String(look.get("hair", "crop"))
	var beard := String(look.get("beard", "none"))
	var col := hair_color(String(look.get("hair_color", "brown")))
	# A headband leaves the crown bare (data/creation.json, look.openHeadgear): the hair shows under it.
	var covers := headgear
	if headgear:
		var open_kinds: Array = Data.creation.get("look", {}).get("openHeadgear", [])
		var worn := node.find_children("Headgear_*", "", true, false)
		if not worn.is_empty():
			covers = false
			for hg in worn:
				var kind := String(hg.name).trim_prefix("Headgear_").get_slice("_", 0)
				if not open_kinds.has(kind):
					covers = true
	node.scale = Vector3.ONE * clampf(float(look.get("stature", 1.0)), 0.85, 1.2)
	for a in node.find_children("*", "BoneAttachment3D", true, false):
		var n := String(a.name)
		if n.begins_with("feature_") or n.begins_with("socket_"):
			continue
		if n.begins_with("Hair_"):
			a.visible = n.begins_with("Hair_%s_" % hair) and not hooded and (n.ends_with("_fall") or not covers)
			if a.visible:
				_recolor(a, col, "coat")
		elif n.begins_with("Beard_"):
			a.visible = n == "Beard_%s" % beard or n.begins_with("Beard_%s_" % beard)
			if a.visible:
				_recolor(a, col, "coat")
		elif n.begins_with("Brow_"):
			# the brows take the hair's colour, a little darker
			_recolor(a, col.darkened(0.3), "coat")
		else:
			# Only headgear and a cape are the look's to show or hide: the eyes, the lashes and
			# the dress's rigid pieces (a button, a pauldron) stay as the body has them.
			var head := n.contains("Helmet") or n.contains("Hat") or n.contains("Hood") or n.begins_with("Headgear_")
			var cape := n.contains("Cape")
			if head:
				a.visible = headgear
			elif cape:
				a.visible = look.get("cape", true)
				if a.visible and not hero.is_empty():
					_tint_cape(a, hero, String(look.get("cape_color", "shape")))

## The colour a genius's echo is drawn in on its partner: the main colour of the coat it
## wears (genius_look.gd), or the partner's Shape colour for a genius with no look of its own.
func genius_coat(g: Dictionary, fallback: Color) -> Color:
	var lk: Dictionary = g.get("look", {}) if g.get("look", {}) is Dictionary else {}
	if lk.is_empty() or String(g.get("silhouette", "")) == "":
		return fallback
	var coat: Dictionary = GeniusLook.resolve(lk, String(g.get("form", "")), String(g["silhouette"]), int(g.get("instar", 1))).get("coat", {})
	return Color(String(coat["main"])) if coat.has("main") else fallback

## A skin tone by its name in data/creation.json.
func skin_color(id: String) -> Color:
	var tones: Dictionary = Data.creation.get("look", {}).get("skinTones", {})
	var c: Array = tones.get(id, tones.get("olive", [0.62, 0.46, 0.33]))
	return Color(c[0], c[1], c[2])

## The features a character carries: the blood's marks, and whatever else was written onto
## them (hero["features"]: the rank's trim, the genius's colour, the changes of instars).
func features_of(hero: Dictionary, look: Dictionary = {}) -> Array:
	var out: Array = []
	var blood_id := String(hero.get("blood", look.get("blood", "")))
	if blood_id != "":
		var b: Dictionary = Data.by_id(Data.bloods, blood_id)
		for m in b.get("marks", []):
			out.append(m)
	# What the life writes onto the body: the rank's trim once an archetype is taken at the
	# Gate; the bonded genius's colour in the cloak once it is born; its light in the eyes from
	# its second instar; the field under the skin from its third.
	if not hero.get("archetypes", []).is_empty():
		out.append("trim-journeyman")
	# The echo (data/genius.json, echo): each instar of the genius writes something on its
	# partner, and from the Third Form a piece that says what kind of thing the genius is.
	var g: Dictionary = hero.get("genius", {}) if hero.get("genius", {}) is Dictionary else {}
	var instar := int(g.get("instar", 0))
	var echo: Dictionary = Data.genius().get("echo", {})
	var expr := String(g.get("expression", g.get("body", {}).get("expression", "") if g.get("body", {}) is Dictionary else ""))
	for src in [echo.get("all", {}), echo.get("byExpression", {}).get(expr, {})]:
		for at in src:
			if instar >= int(at):
				for fid in src[at]:
					if not out.has(fid):
						out.append(fid)
	for f in hero.get("features", []):
		if not out.has(f):
			out.append(f)
	return out

## Recolour the surfaces of one mesh whose material carries a name, keeping the cel shading;
## with a glow, the surface shines in that colour.
func _recolor_named(mi: MeshInstance3D, name: String, col: Color, glow := Color(0, 0, 0), glow_k := 0.0) -> void:
	if mi.mesh == null:
		return
	for i in mi.mesh.get_surface_count():
		var mat := mi.get_active_material(i)
		if mat == null or String(mat.resource_name) != name:
			continue
		# on the ramps of what it is, unless it shines: what glows is the field's, and keeps its colour
		if glow_k <= 0.0:
			col = Style.conform_named(col, name)
		if mat is ShaderMaterial and _toon_shader != null and (mat as ShaderMaterial).shader == _toon_shader:
			var t: ShaderMaterial = (mat as ShaderMaterial).duplicate()
			t.set_shader_parameter("albedo", col)
			t.set_shader_parameter("emission", glow)
			t.set_shader_parameter("emission_energy", glow_k)
			t.resource_name = name
			mi.set_surface_override_material(i, t)
		else:
			var sm := StandardMaterial3D.new()
			sm.albedo_color = col
			sm.roughness = 0.9
			if glow_k > 0.0:
				sm.emission_enabled = true
				sm.emission = glow
				sm.emission_energy_multiplier = glow_k
			sm.resource_name = name
			mi.set_surface_override_material(i, sm)

## The lips' colour from the skin's tone: a little darker and warmer, so they read on every tone.
static func lip_color(tone: Color) -> Color:
	var warm := Color(0.62, 0.3, 0.32)
	return tone.darkened(0.18).lerp(warm, 0.3)

## A hair colour by its name in data/creation.json, on the coat's ramps (docs/style.md).
func hair_color(id: String) -> Color:
	var cols: Dictionary = Data.creation.get("look", {}).get("hairColors", {})
	var c: Array = cols.get(id, cols.get("brown", [0.2, 0.12, 0.07]))
	return Style.conform(Color(c[0], c[1], c[2]), "coat")

## A look for someone the player did not make (a classmate, an instructor, the smith), the same
## every time for the same name: hair, beard, colour, stature, and whether they go bare-headed.
func look_for(name: String) -> Dictionary:
	var L: Dictionary = Data.creation.get("look", {})
	var h := absi(name.hash())
	var hairs: Array = L.get("hair", ["crop"])
	var beards: Array = L.get("beards", ["none"])
	var cols: Array = L.get("hairColors", { "brown": [] }).keys()
	var sts: Array = L.get("statures", { "middling": 1.0 }).values()
	var tones: Array = L.get("skinTones", { "olive": [] }).keys()
	var builds: Array = L.get("builds", { "fit": 0.0 }).values()
	return { "headgear": (h / 7) % 5 < 2, "cape": (h / 11) % 3 != 0, "cape_color": "plain",
		"hair": hairs[h % hairs.size()], "beard": beards[(h / 3) % beards.size()] if (h / 13) % 3 == 0 else beards[0],
		"hair_color": cols[(h / 5) % cols.size()], "stature": sts[(h / 17) % sts.size()],
		"skin": tones[(h / 19) % tones.size()], "build": builds[(h / 23) % builds.size()] }

## Recolour an attachment's meshes, keeping the cel shading when it has it. The colour is
## brought onto the ramps of what it is (cloth, unless said).
func _recolor(att: Node, col: Color, cls := "cloth") -> void:
	col = Style.conform(col, cls)
	for m in att.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var mat := mi.get_active_material(i)
			if mat is ShaderMaterial and (mat as ShaderMaterial).shader == _toon_shader and _toon_shader != null:
				var t: ShaderMaterial = (mat as ShaderMaterial).duplicate()
				t.set_shader_parameter("albedo", col)
				t.set_shader_parameter("use_tex", false)
				mi.set_surface_override_material(i, t)
			else:
				var sm := StandardMaterial3D.new()
				sm.albedo_color = col
				sm.roughness = 0.9
				mi.set_surface_override_material(i, sm)

## The cape takes a colour: the Shape's, the city's, the blood's, or plain cloth.
func _tint_cape(att: Node, hero: Dictionary, which: String) -> void:
	_recolor(att, cape_color_for(hero, which))

func cape_color_for(hero: Dictionary, which: String) -> Color:
	var col := Color(0.5, 0.42, 0.36)
	match which:
		"shape": col = _shape_color(hero.get("shape", "anchor")).darkened(0.25)
		"city": col = CITY_COLORS.get(hero.get("city", "columbia"), col)
		"blood":
			var b: Dictionary = Data.by_id(Data.bloods, hero["blood"]) if hero.get("blood", "") != "" else {}
			col = Color(0.35, 0.1, 0.12) if b.is_empty() else Color(0.25, 0.12, 0.14).lerp(_shape_color(String(b.get("shapeLean", {}).keys()[0]) if not b.get("shapeLean", {}).is_empty() else "anchor"), 0.5)
		"plain": col = Color(0.5, 0.42, 0.36)
	return col

## Mastery shows on the weapon: every perfected technique makes the field in it glow brighter.
func _glow_weapon(hero: Dictionary) -> void:
	if not _sword:
		return
	var grades: Array = Data.academy.get("mastery", {}).get("grades", [])
	var top := int(grades[grades.size() - 1]["uses"]) if not grades.is_empty() else 999999
	var perfected := 0
	for id in hero.get("technique_use", {}):
		if int(hero["technique_use"][id]) >= top:
			perfected += 1
	var tier: Dictionary = Data.gear["tiers"].get(String(hero.get("gear", {}).get("tier", "plain")), {})
	var strength := minf(1.0, 0.35 * perfected + float(tier.get("finish", 0.0)))
	var col := _shape_color(hero.get("shape", "anchor"))
	# A fine weapon takes a brass finish; a named one glows whether or not its model has a field material.
	if float(tier.get("finish", 0.0)) > 0.0:
		for m in _sword.find_children("*", "MeshInstance3D", true, false):
			var mi2: MeshInstance3D = m
			if mi2.material_overlay == null:
				var ov := _mat(Color(1.0, 0.85, 0.5) if String(hero["gear"]["tier"]) == "fine" else col, 1.6 if String(hero["gear"]["tier"]) == "fine" else 2.2, true, 0.18 if String(hero["gear"]["tier"]) == "fine" else 0.3)
				mi2.material_overlay = ov
	for m in _sword.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		for i in mi.get_surface_override_material_count():
			var mat := mi.get_active_material(i)
			if mat and String(mat.resource_name).begins_with("field"):
				var g := StandardMaterial3D.new()
				g.albedo_color = col.darkened(0.3)
				g.emission_enabled = true
				g.emission = col
				g.emission_energy_multiplier = 0.4 + 2.6 * strength
				mi.set_surface_override_material(i, g)
	if perfected > 0:
		var lamp := OmniLight3D.new()
		lamp.light_color = col
		lamp.light_energy = 0.6 * strength
		lamp.omni_range = 2.5
		_sword.add_child(lamp)

## A weapon's model: the weapon kit's when it exists, else KayKit's of that name.
func _weapon_model(model: String) -> String:
	var path := "res://game/assets/weapons/%s.glb" % model
	if ResourceLoader.exists(path):
		return path
	var kk := "res://game/assets/kaykit/weapons/%s.gltf" % model
	if ResourceLoader.exists(kk):
		return kk
	return "res://game/assets/kaykit/weapons/sword_1handed.gltf"

## A person's body: the grounded one from the people kit when it exists, else KayKit's.
func _person_model(body: String) -> String:
	var path := "res://game/assets/people/%s.glb" % body
	if ResourceLoader.exists(path):
		return path
	# A home without a body of its own yet wears Alexandria's of the same sex; the old KayKit
	# names (saves from before the body kit) take Alexandria's too.
	var sex: String = body.get_slice("-", 1) if body.contains("-") else String(LEGACY_BODIES.get(body, "m"))
	var alt := "res://game/assets/people/alexandria-%s.glb" % sex
	if ResourceLoader.exists(alt):
		return alt
	return "res://game/assets/kaykit/%s.glb" % body

const LEGACY_BODIES := { "Knight": "m", "Barbarian": "m", "Rogue_Hooded": "m", "Mage": "f", "Rogue": "f" }

## A beast's body: its own model from the beast kit when it exists, else the wolf.
func _beast_model(model: String) -> String:
	var path := "res://game/assets/beasts/%s.glb" % model
	if model != "" and ResourceLoader.exists(path):
		return path
	return "res://game/assets/quaternius/Wolf.glb"

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
var _offhand: Node3D = null      # what the partner carries in the other hand (a shield); not drawn while a genius is worn in its place
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
uniform vec3 cool = vec3(0.92, 0.97, 1.06);
uniform vec3 warm = vec3(1.06, 1.0, 0.9);
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	vec3 g = c * mix(cool, warm, smoothstep(0.04, 0.55, l));
	g += vec3(0.005, 0.006, 0.009) * (1.0 - smoothstep(0.0, 0.25, l));
	vec2 uv = UV - 0.5;
	float d = length(uv * vec2(1.5, 1.0));
	g *= 1.0 - smoothstep(0.36, 0.95, d) * base;
	g += (hash(floor(FRAGCOORD.xy * 0.5) + fract(TIME * 7.13) * 97.0) - 0.5) * grain;
	g = mix(g, tint.rgb, clamp(tint.a * smoothstep(0.2, 0.9, d) * 0.8, 0.0, 1.0));
	COLOR = vec4(g, 1.0);
}
"""

const TOON := """
shader_type spatial;
// Cel shading, second pass (docs/graphics-comparison.md): light in bands with a tinted
// shadow side; a sky-lit ambient wrap; a two-band specular by surface; a rim light; a
// tileable detail texture laid on by world-space triplanar projection, so no UVs are needed;
// and the baked cavity occlusion in the vertex colour. The ink lines are the overlay's next
// pass as before.
render_mode cull_back;
uniform vec4 albedo : source_color = vec4(1.0);
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform bool use_tex = false;
// the palette's ramps as a lookup (Style.ramp_lut): a painted texture that could not be
// brought onto the ramps beforehand is brought onto them here
uniform sampler2D ramp_lut : source_color, filter_linear, repeat_disable;
uniform bool use_lut = false;
uniform float bands = 3.0;
uniform vec4 shadow_tint : source_color = vec4(0.5, 0.55, 0.78, 1.0);
uniform vec4 emission : source_color = vec4(0.0);
uniform float emission_energy = 0.0;
uniform sampler2D detail_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float detail_scale = 6.0;
uniform float detail_strength = 0.0;
uniform float spec_strength = 0.05;
uniform float spec_gloss = 8.0;
uniform float rim_strength = 0.35;
uniform float rim_power = 3.0;
uniform vec4 rim_color : source_color = vec4(0.85, 0.9, 1.0, 1.0);
uniform float ao_strength = 0.8;
uniform bool use_ao = false;
varying vec3 world_pos;
varying vec3 world_nrm;
varying float ao;
void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	ao = use_ao ? COLOR.r : 1.0;
}
float triplanar(vec3 p, vec3 n) {
	vec3 w = abs(n);
	w = w / max(w.x + w.y + w.z, 0.001);
	float x = texture(detail_tex, p.yz * detail_scale).r;
	float y = texture(detail_tex, p.xz * detail_scale).r;
	float z = texture(detail_tex, p.xy * detail_scale).r;
	return x * w.x + y * w.y + z * w.z;
}
vec3 on_ramps(vec3 lin) {
	vec3 c = clamp(pow(max(lin, vec3(0.0)), vec3(1.0 / 2.2)), 0.0, 1.0);
	float b = c.b * 15.0;
	float b0 = floor(b);
	float b1 = min(b0 + 1.0, 15.0);
	vec2 at = vec2(0.5 + c.r * 15.0, (0.5 + c.g * 15.0) / 16.0);
	vec3 lo = texture(ramp_lut, vec2((b0 * 16.0 + at.x) / 256.0, at.y)).rgb;
	vec3 hi = texture(ramp_lut, vec2((b1 * 16.0 + at.x) / 256.0, at.y)).rgb;
	return mix(lo, hi, b - b0);
}
void fragment() {
	vec3 col = albedo.rgb;
	if (use_tex) {
		vec3 painted = texture(albedo_tex, UV).rgb;
		col *= use_lut ? on_ramps(painted) : painted;
	}
	if (detail_strength > 0.0) {
		float d = triplanar(world_pos, world_nrm);
		col *= mix(1.0, d * 2.0, detail_strength);
	}
	float occ = mix(1.0, ao, ao_strength);
	ALBEDO = col * occ;
	EMISSION = emission.rgb * emission_energy;
	float fres = pow(1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0), rim_power);
	EMISSION += rim_color.rgb * fres * rim_strength * col;
	ROUGHNESS = 0.9;
	SPECULAR = 0.1;
}
void light() {
	float ndl = dot(NORMAL, LIGHT);
	float t = clamp(ndl * 0.5 + 0.5, 0.0, 1.0);
	float stepped = clamp(floor(t * bands) / max(bands - 1.0, 1.0), 0.0, 1.0);
	vec3 lit = mix(ALBEDO * shadow_tint.rgb, ALBEDO, stepped);
	DIFFUSE_LIGHT += lit * LIGHT_COLOR * ATTENUATION;
	vec3 h = normalize(LIGHT + VIEW);
	float s = pow(max(dot(NORMAL, h), 0.0), spec_gloss);
	float sb = s > 0.5 ? 1.0 : (s > 0.2 ? 0.4 : 0.0);
	SPECULAR_LIGHT += sb * spec_strength * LIGHT_COLOR * ATTENUATION * (stepped > 0.0 ? 1.0 : 0.3);
}
"""

var _toon_shader: Shader = null
var _detail_cache: Dictionary = {}

## Which class a material is, by its name (data/style.json, materials): skin, coat, cloth,
## leather, wood, stone, iron, brass, bone, glass, growth, earth, water, eye, ink, the field's
## light or a lit thing. "cloth" for a name that says nothing (the style check finds those).
static func surface_of(name: String, color := Color(-1, -1, -1)) -> String:
	var cls := Style.material_class(name, color)
	return cls if cls != "" else "cloth"

## The class's look on a toon material: its bands, its shadow's tint, its highlight, its grain
## and wear, the rim light, and the occlusion baked in the vertex colour.
func _surface_look(t: ShaderMaterial, cls: String, mi: MeshInstance3D) -> void:
	var spec: Dictionary = Style.class_spec(cls)
	var sh: Dictionary = Style.data()["shading"]
	t.set_shader_parameter("bands", float(spec.get("bands", 3)))
	t.set_shader_parameter("shadow_tint", Color(String(spec.get("shadowTint", "#9690A8"))))
	var hl: Array = spec.get("spec", [0.05, 8.0])
	t.set_shader_parameter("spec_strength", float(hl[0]))
	t.set_shader_parameter("spec_gloss", float(hl[1]))
	var rim: Dictionary = sh.get("rim", {})
	t.set_shader_parameter("rim_strength", float(rim.get("strength", 0.22)))
	t.set_shader_parameter("rim_power", float(rim.get("power", 3.0)))
	t.set_shader_parameter("rim_color", Color(String(rim.get("color", "#D2D8EC"))))
	var grain := String(spec.get("grain", ""))
	if grain != "" and float(spec.get("wear", 0.0)) > 0.0:
		var path := "res://game/assets/textures/detail/%s.png" % grain
		if not _detail_cache.has(path):
			_detail_cache[path] = load(path) if ResourceLoader.exists(path) else null
		if _detail_cache[path] != null:
			t.set_shader_parameter("detail_tex", _detail_cache[path])
			t.set_shader_parameter("detail_scale", float(spec.get("grainScale", 4.0)))
			t.set_shader_parameter("detail_strength", float(spec["wear"]))
	t.set_shader_parameter("ao_strength", float(sh.get("occlusion", 0.8)))
	var has_color := mi.mesh != null and mi.mesh is ArrayMesh and (mi.mesh as ArrayMesh).surface_get_format(0) & Mesh.ARRAY_FORMAT_COLOR
	t.set_shader_parameter("use_ao", bool(has_color))

## The cel look, and the style's hold on every surface (docs/style.md): each StandardMaterial3D
## under the node becomes a banded toon material of its class. Its colour is brought onto the
## ramps its class allows (a painted texture too), a lit thing takes the lamp's or the moon's
## colour, and its emission is kept. Off when data/style.json shading.cel is false.
func toonify(node: Node) -> void:
	if not Style.data()["shading"].get("cel", true) or node == null:
		return
	if _toon_shader == null:
		_toon_shader = Shader.new()
		_toon_shader.code = TOON
	var meshes := node.find_children("*", "MeshInstance3D", true, false)
	if node is MeshInstance3D:
		meshes.append(node)
	for m in meshes:
		var mi: MeshInstance3D = m
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var mat := mi.get_active_material(i)
			if mat == null or not (mat is StandardMaterial3D):
				continue
			var sm: StandardMaterial3D = mat
			if sm.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or sm.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED or sm.blend_mode != BaseMaterial3D.BLEND_MODE_MIX:
				continue
			var cls := surface_of(String(sm.resource_name), sm.albedo_color)
			var t := ShaderMaterial.new()
			t.shader = _toon_shader
			t.resource_name = sm.resource_name
			t.set_shader_parameter("use_tex", sm.albedo_texture != null)
			if sm.albedo_texture:
				# a painted texture is brought onto the ramps whole; what multiplies it is left
				# (-- --style-lut leaves it to the shader everywhere, to look at that way of doing it)
				var painted := sm.albedo_texture if OS.get_cmdline_user_args().has("--style-lut") else Style.conform_texture(sm.albedo_texture)
				t.set_shader_parameter("albedo_tex", painted)
				t.set_shader_parameter("albedo", sm.albedo_color)
				if painted == sm.albedo_texture:
					# it could not be read back here: the shader brings it over as it draws
					t.set_shader_parameter("use_lut", true)
					t.set_shader_parameter("ramp_lut", Style.ramp_lut())
			else:
				t.set_shader_parameter("albedo", Style.conform(sm.albedo_color, cls))
			_surface_look(t, cls, mi)
			if sm.emission_enabled:
				var glow := sm.emission
				var energy := sm.emission_energy_multiplier
				if cls == "lit":
					# a lamp, a flame, a lit pane: the lamp's light or the moon's; coloured glass banked
					var stained := String(sm.resource_name).to_lower().contains("stain")
					if stained:
						var st: Dictionary = Style.data()["lights"]["stain"]
						glow = glow.darkened(float(st.get("darken", 0.25)))
						energy *= float(st.get("energy", 0.5))
						t.set_shader_parameter("albedo", sm.albedo_color.darkened(float(st.get("darken", 0.25)) + 0.2))
					else:
						# its light's own colour, over a pane dark enough that the light is what shows
						glow = Style.conform_light(glow, "color")
						if String(sm.resource_name).to_lower().contains("glass"):
							energy *= float(Style.data()["lights"]["window"].get("energy", 1.0))
						t.set_shader_parameter("albedo", glow.darkened(0.72))
				t.set_shader_parameter("emission", glow)
				t.set_shader_parameter("emission_energy", energy)
			t.next_pass = sm.next_pass
			mi.set_surface_override_material(i, t)

const INK := """
shader_type spatial;
// Ink lines around the characters and the beasts, like a woodcut: the mesh drawn again, its
// back faces pushed out a few pixels along the normal.
render_mode unshaded, cull_front, shadows_disabled, depth_draw_opaque;
uniform vec4 ink : source_color = vec4(0.045, 0.03, 0.028, 1.0);
uniform float width = 2.0;
uniform float screen = 900.0;
void vertex() {
	vec4 clip = PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0));
	vec3 n = (MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	vec2 off = (PROJECTION_MATRIX * vec4(n, 0.0)).xy;
	off = off / max(length(off), 1e-4);
	clip.xy += off * width * (VIEWPORT_SIZE.y / screen) * 2.0 / VIEWPORT_SIZE * clip.w;
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
uniform vec4 tint : source_color = vec4(0.55, 0.62, 0.95, 1.0);
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
	# the film the game is shot on (data/style.json, film)
	var film: Dictionary = Style.data()["film"]
	var fs: Array = film.get("shadows", [0.92, 0.97, 1.06])
	var fh: Array = film.get("highlights", [1.06, 1.0, 0.9])
	sm.set_shader_parameter("cool", Vector3(fs[0], fs[1], fs[2]))
	sm.set_shader_parameter("warm", Vector3(fh[0], fh[1], fh[2]))
	sm.set_shader_parameter("base", float(film.get("vignette", 0.5)))
	sm.set_shader_parameter("grain", float(film.get("grain", 0.03)))
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

# --- Effects: one family of shapes, in ink and light (data/style.json, effects) ----------------
# The ring (thin, flat), the shard (a long splinter of light laid along its travel), the puff
# (a soft blot of dust or ink), the flash (a four-pointed star) and the word. Nothing else.

static var _fx_shard: ArrayMesh
static var _fx_star: ImageTexture

## A shard: a long thin diamond, its length along Y so a particle lies along its travel.
static func fx_shard_mesh() -> ArrayMesh:
	if _fx_shard:
		return _fx_shard
	var half := Style.fx_n("shard", "length", 0.22) / 2.0
	var w := Style.fx_n("shard", "width", 0.035) / 2.0
	var top := Vector3(0, half, 0)
	var bot := Vector3(0, -half, 0)
	var ring := [Vector3(w, 0, 0), Vector3(0, 0, w), Vector3(-w, 0, 0), Vector3(0, 0, -w)]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in 4:
		var p: Vector3 = ring[i]
		var q: Vector3 = ring[(i + 1) % 4]
		for tri in [[top, q, p], [bot, p, q]]:
			for v in tri:
				st.add_vertex(v)
	st.generate_normals()
	_fx_shard = st.commit()
	return _fx_shard

## The flash: a four-pointed star, drawn once.
static func fx_star() -> ImageTexture:
	if _fx_star:
		return _fx_star
	var n := 96
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var u := absf((x + 0.5) / n * 2.0 - 1.0)
			var v := absf((y + 0.5) / n * 2.0 - 1.0)
			var star := clampf(1.0 - (sqrt(u) + sqrt(v)), 0.0, 1.0)
			var core := clampf(1.0 - Vector2(u, v).length() * 2.2, 0.0, 1.0)
			img.set_pixel(x, y, Color(1, 1, 1, clampf(pow(star, 1.3) * 2.2 + core * core, 0.0, 1.0)))
	_fx_star = ImageTexture.create_from_image(img)
	return _fx_star

## A flash where a blow lands: the star, opening and gone.
func impact(at: Vector3, color: Color, size := 0.7) -> void:
	var mi := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(1.6, 1.6)
	mi.mesh = qm
	var m := _mat(color, 0.0, true, 0.95)
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_texture = fx_star()
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.billboard_keep_scale = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = true
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = at
	mi.scale = Vector3.ONE * size * 0.35
	mi.rotation.z = randf_range(0.0, PI / 2.0)
	add_child(mi)
	var secs := Style.fx_n("flash", "seconds", 0.13)
	var tw: Tween = create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3.ONE * size, secs).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(m, "albedo_color:a", 0.0, secs * 1.1)
	tw.chain().tween_callback(mi.queue_free)

## Dust kicked up: a few soft blots, in the dust's colour, that swell and thin.
func dust(at: Vector3, amount := 18) -> void:
	var p := CPUParticles3D.new()
	var secs := Style.fx_n("puff", "seconds", 0.7)
	p.one_shot = true
	p.amount = maxi(4, amount / 2)
	p.lifetime = secs
	p.explosiveness = 0.9
	p.direction = Vector3(0, 1, 0)
	p.spread = 80.0
	p.initial_velocity_min = 0.5
	p.initial_velocity_max = 1.6
	p.gravity = Vector3(0, -0.6, 0)
	p.damping_min = 2.0
	p.damping_max = 4.0
	p.scale_amount_min = 0.7
	p.scale_amount_max = 1.5
	var grow := Curve.new()
	grow.add_point(Vector2(0.0, 0.45))
	grow.add_point(Vector2(1.0, 1.6))
	p.scale_amount_curve = grow
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 1))
	fade.set_color(1, Color(1, 1, 1, 0))
	p.color_ramp = fade
	var qm := QuadMesh.new()
	var sz := Style.fx_n("puff", "size", 0.16) * 2.0
	qm.size = Vector2(sz, sz)
	p.mesh = qm
	var m := _mat(Style.fx("dust"), 0.0, true, Style.fx_n("puff", "alpha", 0.55))
	m.albedo_texture = _soft_dot()
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.billboard_keep_scale = true
	m.vertex_color_use_as_albedo = true
	p.material_override = m
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	p.position = at
	add_child(p)
	p.emitting = true
	get_tree().create_timer(secs + 0.6, true, false, true).timeout.connect(p.queue_free)

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

## The living idle on one breath (data/style.json, motion.idle): the speed that makes an idle
## clip's loop last the breath's period, whatever the clip's own length. 1 for any other clip.
static func breath(ap: AnimationPlayer, name: String) -> float:
	if ap == null or not name.to_lower().ends_with("idle") or not ap.has_animation(name):
		return 1.0
	return clampf(ap.get_animation(name).length / Style.motion("idle", "period", 3.6), 0.25, 1.5)

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

## The gait for a ground speed: a walk below the walk-run line, a run above (data/rules.json, motion).
static func gait_for(v: float) -> String:
	var m: Dictionary = Data.rules.get("motion", {})
	return "Walking_A" if v < float(m.get("runAbove", 2.6)) else "Running_A"

## The clip's playback rate that plants the feet at this ground speed: the clip's own stride
## speed (how fast the feet move over the ground in the clip, data/rules.json, motion) scaled
## to the speed the body moves, within limits so a slow walk never crawls nor a sprint blurs.
static func stride_scale(clip: String, v: float) -> float:
	var m: Dictionary = Data.rules.get("motion", {})
	var strides: Dictionary = m.get("strides", {})
	var stride := float(strides.get(clip, 0.0))
	if stride <= 0.0 or v <= 0.0:
		return 1.0
	var lim: Array = m.get("rateLimits", [0.6, 1.6])
	return clampf(v / stride, float(lim[0]), float(lim[1]))

func _loop(ap: AnimationPlayer, name: String, speed := 1.0, is_wolf := false) -> void:
	var current := _w_current if is_wolf else _p_current
	speed *= breath(ap, name)
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
	l.outline_size = int(Style.fx_n("word", "outline", 12))
	l.outline_modulate = Color(Style.ink_color(), 0.85)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	# Several at once near the same spot stack upward instead of piling on one another.
	var lift := 0.0
	for f in _floaters:
		if float(f["age"]) < 0.5 and (f["l"] as Node3D).position.distance_to(at) < 2.5:
			lift += 0.45
	l.position = at + Vector3(randf_range(-0.25, 0.25), lift, 0)
	add_child(l)
	_floaters.append({ "l": l, "age": 0.0, "life": life, "rise": rise })

## Sparks thrown from a blow: shards of light, each lying along its own travel.
func burst(at: Vector3, color: Color, amount: int, speed := 5.0) -> void:
	var p := CPUParticles3D.new()
	var secs := Style.fx_n("shard", "seconds", 0.4)
	p.one_shot = true
	p.amount = maxi(4, int(amount * 0.7))
	p.lifetime = secs
	p.explosiveness = 1.0
	p.direction = Vector3(0, 1, 0)
	p.spread = 180.0
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.gravity = Vector3(0, -9, 0)
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.5
	var thin := Curve.new()
	thin.add_point(Vector2(0.0, 1.0))
	thin.add_point(Vector2(1.0, 0.0))
	p.scale_amount_curve = thin
	p.particle_flag_align_y = true
	p.mesh = fx_shard_mesh()
	var m := _mat(color, 4.0, true)
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	p.material_override = m
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	p.position = at
	add_child(p)
	p.emitting = true
	get_tree().create_timer(secs + 0.8, true, false, true).timeout.connect(p.queue_free)

## A ring run out across the ground: thin and flat.
func _ring_wave(at: Vector3, color: Color, radius: float) -> void:
	var mi := MeshInstance3D.new()
	var t := TorusMesh.new()
	t.inner_radius = 1.0 - Style.fx_n("ring", "thickness", 0.06)
	t.outer_radius = 1.0
	t.rings = 48
	mi.mesh = t
	mi.scale = Vector3(0.2, 0.03, 0.2)
	mi.position = at + Vector3(0, 0.08, 0)
	var m := _mat(color, 3.0, true, 0.9)
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	var secs := Style.fx_n("ring", "seconds", 0.35)
	var tw: Tween = create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3(radius, 0.03, radius), secs).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(m, "albedo_color:a", 0.0, secs)
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
	var m := _mat(Style.fx("shot"), 4.0, true, 0.9)
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	im.surface_add_vertex(from)
	im.surface_add_vertex(to)
	im.surface_end()
	add_child(mi)
	impact(from, Style.fx("shot"), 0.5)
	if hit:
		impact(to, Style.fx("spark"), 0.6)
	var tw: Tween = create_tween()
	tw.tween_property(m, "albedo_color:a", 0.0, Style.fx_n("flash", "seconds", 0.13))
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
				if f.beast.has("guard") and f.w_state != "stagger":
					floater(W + Vector3(0, 0.95, 0), "THROUGH THE GUARD" if e["pattern"] else "guarded", C_GOLD if e["pattern"] else C_DIM, 40 if e["pattern"] else 30, 0.7)
				floater(W + Vector3(0, 0.2, 0), ("%d!" if e.get("crit", false) else "%d") % int(e["damage"]), C_GOLD if e["pattern"] else (C_STAGGER if e["staggered"] else (Color(0.85, 0.85, 1.0) if e.get("crit", false) else C_TEXT)), 84 if heavy or e.get("crit", false) else 60)
				burst(_v3(f.w_pos, 0.9), C_GOLD if heavy else C_HIT, 30 if heavy else 14, 7.0 if heavy else 5.0)
				impact(_v3(f.w_pos, 0.9) + _v3((f.p_pos - f.w_pos).normalized() * 0.4), C_GOLD if heavy else C_HIT, 1.1 if heavy else 0.7)
				_wolf_flash = 1.0
				_shake = maxf(_shake, float(feel["shakeOnHit"]) * (2.0 if heavy else 1.0))
				hitstop(float(feel["heavyHitstop"]) if heavy else float(feel["hitstop"]))
			"whiff":
				pass
			"shot":
				if e.get("cone", false):
					var m := _v3(f.p_pos, 1.2) + _v3(Vector2.from_angle(f.p_facing) * 1.0)
					burst(m, Style.fx("shot"), 40, 9.0)
					impact(m, Style.fx("shot"), 1.2)
					_shake = maxf(_shake, 0.2)
				else:
					_tracer(_v3(e["from"], 1.35) + _v3(Vector2.from_angle(f.p_facing) * 0.6), _v3(e["to"], 1.0), e["hit"])
			"reload":
				floater(P - Vector3(0, 0.5, 0), "RELOADING", C_DIM, 36, 0.8)
			"reloaded":
				floater(P - Vector3(0, 0.5, 0), "LOADED", Color(0.75, 0.85, 1.0), 36, 0.6)
			"draw-release":
				if float(e.get("charge", 0.0)) >= 0.99:
					floater(P + Vector3(0, 0.2, 0), "FULL DRAW", C_GOLD, 44, 0.8)
			"burst":
				_ring_wave(_v3(e["at"]), Style.shape_color("turn"), 2.8)
				burst(_v3(e["at"], 0.8), Style.shape_color("turn"), 40, 6.0)
				impact(_v3(e["at"], 1.0), Style.shape_color("turn"), 1.6)
			"crit-open":
				floater(W + Vector3(0, 0.9, 0), "THE BREAK IS OPEN", Color(0.9, 0.9, 1.0), 56, 1.4)
			"tether":
				floater(W + Vector3(0, 0.9, 0), "LEASHED", Style.shape_color("bind"), 56, 1.2)
			"ward-up":
				_ward_at = _v3(e["at"])
				_ring_wave(_ward_at, Style.shape_color("make"), 2.0)
			"ward-broken":
				if _ward:
					burst(_ward.position + Vector3(0, 1.0, 0), Style.shape_color("make"), 40, 6.0)
				floater(P, "THE WARD TAKES IT", Style.shape_color("make"), 52)
			"burn-tick":
				floater(W + Vector3(randf_range(-0.3, 0.3), 0, 0), "%d" % int(e["damage"]), Color(1.0, 0.55, 0.2), 34, 0.6)
			"second-heart":
				floater(P + Vector3(0, 0.4, 0), "A SECOND HEART", Color(1.0, 0.4, 0.4), 72, 1.6)
				flash_screen(Style.fx("hurt"), 0.6)
			"hesitates":
				floater(W + Vector3(0, 0.8, 0), "IT HESITATES", C_TEXT, 56)
			"quake":
				_ring_wave(_v3(e["at"]), C_STANCE, 2.6)
				dust(_v3(e["at"], 0.1), 24)
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
				var from := _foe_pos(f, int(e.get("foe", -1)))
				burst((_v3(f.p_pos, 1.2) + _v3(from, 1.2)) / 2.0, C_GUARD, 50, 8.0)
				_ring_wave(_v3(f.p_pos), C_GUARD, 3.5)
				_shake = 0.12
				slowmo(float(feel["parrySlowmo"]), 0.3)
				impact((_v3(f.p_pos, 1.2) + _v3(from, 1.2)) / 2.0, C_GUARD, 1.4)
				flash_screen(C_GUARD, 0.35)
			"block":
				floater(P, "BLOCKED  -%d" % int(e["damage"]), C_GUARD, 48)
				burst(_v3(f.p_pos, 1.2) + _v3(Vector2.from_angle(f.p_facing) * 0.5), C_GUARD, 12, 4.0)
				_shake = 0.07
			"hurt":
				genius_react("hurt")
				floater(P, "-%d" % int(e["damage"]), C_WINDUP, 80)
				_player_flash = 1.0
				_shake = float(feel["shakeOnHurt"])
				flash_screen(Style.fx("hurt"), 0.55)
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
				# its own blow darts in; what it laid on the ground, or added to its partner's swing, only counts
				var gm := String(e.get("move", "strike"))
				if gm not in ["lay", "with", "double", "debt"]:
					_g_dart_at = _v3(f.w_pos, 1.0)
					_g_dart_until = _clock + 0.28
					impact(_v3(f.w_pos, 1.0), _g_tint, 0.6 if gm == "strike" else 1.0)
					burst(_v3(f.w_pos, 1.0), _g_tint, 10, 4.0)
				floater(W + Vector3(0.4, 0.4, 0), "%d" % int(e["damage"]), _g_tint.lightened(0.3), 46 if gm != "lay" else 34, 0.8)
				_wolf_flash = maxf(_wolf_flash, 0.5 if gm != "lay" else 0.2)
			"genius-move":
				_genius_move_shown(f, e, P, W)
			"genius-great":
				floater(W + Vector3(0, 1.0, 0), String(e["name"]).to_upper(), _g_tint.lightened(0.45), 64, 1.8)
				flash_screen(_g_tint, 0.35)
				_ring_wave(_v3(f.w_pos), _g_tint, 5.0)
				burst(_v3(f.w_pos, 1.0), _g_tint.lightened(0.3), 60, 6.0)
				impact(_v3(f.w_pos, 1.0), _g_tint, 2.0)
				genius_react("parry")
			"genius-called":
				_g_dart_at = _v3(f.g_pos.lerp(f.w_pos, 0.4), 1.0)
				_g_dart_until = _clock + 0.3
				impact(_v3(f.g_pos, 1.0), _g_tint, 1.0)
				floater(_v3(f.g_pos, 1.6), "IT TAKES THE BLOW", _g_tint.lightened(0.3), 48, 1.0)
			"genius-ward":
				_ring_wave(_v3(f.p_pos), _g_tint, 2.2)
				floater(P, "TURNED", _g_tint.lightened(0.3), 52, 1.0)
			"genius-hold":
				_ring_wave(_v3(f.g_hold_at), _g_tint, float(f._order("hold")["hold"]["radius"]))
			"free":
				floater(_v3(f.g_pos, 1.9), "%s: %s" % [String(e["order"]).to_upper(), String(e["why"])], _g_tint.lightened(0.3), 40, 1.6)
				genius_react("cue")
			"genius-guard":
				var mid := _v3(f.p_pos.lerp(f.w_pos, 0.35), 1.2)
				_g_dart_at = mid
				_g_dart_until = _clock + 0.35
				impact(mid, _g_tint, 1.0)
				_ring_wave(_v3(f.p_pos), _g_tint, 1.6)
				floater(P, "GUARDED", _g_tint.lightened(0.3), 52, 1.0)
				genius_react("parry")
			"genius-take":
				# a weapon genius changes hands
				if e["in"]:
					floater(P + Vector3(0, 0.3, 0), "IN HAND" + ("  ·  THE CUT" if e.get("cut", false) else ""), _g_tint.lightened(0.35), 46, 0.9)
					burst(P, _g_tint.lightened(0.3), 14, 3.0)
				else:
					floater(P + Vector3(0, 0.3, 0), "IT IS SPENT" if e.get("spent", false) else "LET GO", _g_tint.lightened(0.2) if not e.get("spent", false) else Color(0.8, 0.75, 0.7), 42, 0.9)
				genius_react("cue")
			"genius-use":
				var ua := _v3(e.get("at", f.p_pos), 1.7)
				floater(ua, String(e["name"]).to_upper() + ("  ·  ON AIR" if e.get("miss", false) else ""), _g_tint.lightened(0.35) if not e.get("miss", false) else C_DIM, 44, 1.1)
				if String(e.get("effect", "")) == "set" and not e.get("miss", false):
					_ring_wave(_v3(f.p_pos), _g_tint, 1.4)
				genius_react("stance")
			"genius-took":
				var who := int(e.get("ally", -1))
				var ta: Vector3 = P if who < 0 or who >= f.allies.size() else _v3(f.allies[who]["pos"], 1.2)
				impact(ta, _g_tint, 1.2)
				_ring_wave(Vector3(ta.x, 0.0, ta.z), _g_tint, 1.8)
				floater(ta + Vector3(0, 0.5, 0), "IT TAKES THE BLOW", _g_tint.lightened(0.3), 48, 1.0)
				genius_react("parry")
			"genius-door":
				_ring_wave(_v3(e["at"]), _g_tint, float(e["radius"]))
			"genius-caught":
				var ca := _v3(e["at"], 1.0)
				impact(ca, _g_tint, 1.4)
				burst(ca, _g_tint.lightened(0.3), 16, 3.5)
				floater(ca + Vector3(0, 0.8, 0), "CAUGHT", _g_tint.lightened(0.35), 52, 1.0)
			"genius-lamp":
				_ring_wave(_v3(e["at"]), Color(1.0, 0.9, 0.6), float(e["radius"]))
			"genius-sight":
				_ring_wave(_v3(f.w_pos), _g_tint.lightened(0.3), 1.6)
				floater(W + Vector3(0, 1.0, 0), "SIGHTED", _g_tint.lightened(0.35), 46, 1.2)
			"genius-toll":
				_ring_wave(_v3(e["at"]), _g_tint.lightened(0.2), float(e["radius"]))
				floater(P + Vector3(0, 0.5, 0), "IT TOLLS" if not e.get("auto", false) else "IT TOLLS OF ITSELF", _g_tint.lightened(0.35), 50, 1.1)
				if int(e.get("broke", 0)) > 0:
					flash_screen(_g_tint, 0.12)
			"genius-took-back":
				floater(P + Vector3(0, 0.2, 0), "+%d" % roundi(float(e["amount"])), _g_tint.lightened(0.4), 46, 1.0)
			"genius-caught-fall":
				flash_screen(_g_tint, 0.4)
				_ring_wave(_v3(f.p_pos), _g_tint, 2.4)
				floater(P + Vector3(0, 0.6, 0), "IT CATCHES YOU", _g_tint.lightened(0.4), 60, 1.6)
				genius_react("parry")
			"genius-mend":
				var mw := int(e.get("who", -1))
				var ma: Vector3 = P if mw < 0 or mw >= f.allies.size() else _v3(f.allies[mw]["pos"], 1.6)
				floater(ma + Vector3(0.3, 0.1, 0), "+%d" % roundi(float(e["amount"])), _g_tint.lightened(0.45), 40, 0.9)
			"genius-held-blow":
				impact(_v3(e["at"], 0.9), _g_tint, 1.2)
				floater(_v3(e["at"], 1.7), "IT HOLDS", _g_tint.lightened(0.3), 46, 1.0)
			"genius-sig":
				floater(W + Vector3(-0.3, 0.9, 0), String(e["name"]).to_upper(), _g_tint.lightened(0.4), 42, 1.0)
			"genius-not-ready":
				floater(P, "your genius is not ready", C_DIM, 36)
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
			"ally-hit", "ally-hurt", "ally-down", "ally-up", "ally-windup", "ally-pattern", "ally-parry", "ally-block", "ally-retreat", "ally-shot", "ally-miss":
				_ally_event(f, e)
			"foe-spawn", "foe-windup", "foe-strike", "foe-hit", "foe-down", "foe-stagger", "retarget":
				_pack_event(f, e)
			"field-open":
				_ring_wave(_v3(f.p_pos), _shape_color(f.player_shape), 5.0)
				burst(P, _shape_color(f.player_shape), 60, 6.0)
				floater(P + Vector3(0, 0.6, 0), "THE FIELD OPENS", _shape_color(f.player_shape), 80, 2.0, 0.4)
				flash_screen(_shape_color(f.player_shape), 0.5)
				genius_react("stance")
			"foe-pattern":
				floater(W + Vector3(0, 1.1, 0), String(e["name"]).to_upper(), C_GOLD, 64, 1.6)
				_ring_wave(_v3(f.w_pos), C_GOLD, 3.0)
				genius_react("cue")
			"shadow-made":
				floater(P + Vector3(0, 0.8, 0), "A SHADOW: %s" % String(e["name"]).to_upper(), _g_tint.lightened(0.3), 56, 2.0)
				genius_react("parry")
			"marked":
				floater(W + Vector3(0, 0.9, 0), "UNDER WARRANT", C_GOLD, 56, 1.4)
				_ring_wave(_v3(f.w_pos), C_GOLD, 2.0)
			"sounded":
				floater(W + Vector3(0, 0.9, 0), "SOUNDED", Style.shape_color("cast"), 56, 1.2)
				_ring_wave(_v3(f.w_pos), Style.shape_color("cast"), 3.0)
			"pulled":
				floater(W + Vector3(0, 0.9, 0), "LINE ACROSS", Style.shape_color("bind"), 56, 1.0)
				_tracer(_v3(f.p_pos, 1.3), _v3(f.w_pos, 1.0), true)
			"named":
				floater(_v3(f.p_pos, 2.6), "%s!" % String(e["who"]).to_upper(), C_TEXT, 64, 1.0)
			"bar-warning":
				floater(P + Vector3(0, 0.5, 0), String(e["bars"][0]).to_upper(), C_WINDUP, 60, 1.6)
				floater(P, "press R again to break your Term", C_WINDUP, 40, 1.6)
				flash_screen(Style.fx("hurt"), 0.25)
			"breach":
				floater(P + Vector3(0, 0.8, 0), "TERM BROKEN", C_WINDUP, 110, 2.2)
				floater(P + Vector3(0, 0.2, 0), "the Pattern is lost for good" if e["sworn"] else "the Pattern is lost for a season", C_WINDUP, 48, 2.2)
				flash_screen(Style.fx("hurt").darkened(0.25), 0.8)
				_shake = 0.35
			"turned":
				floater(P, "TURNED ASIDE", C_GUARD, 56)
				impact(_v3(f.p_pos, 1.2) + _v3(Vector2.from_angle(f.p_facing) * 0.6), C_GUARD, 1.0)
			"ward-pulse":
				_ring_wave(_v3(f.p_pos), C_GUARD, 2.2)
			"mend":
				floater(P, "+%d" % int(e["amount"]), Style.shape_color("make"), 56)
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
					floater(P + Vector3(0, 0.6, 0), "+%d" % int(e["heal"]), Style.shape_color("make"), 140, 1.6, 0.6)
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
					var v := f.p_vel.length() / _player.scale.y
					if f.p_lock and f.w_state not in ["down", "absent"] and absf(rel) > PI * 0.3:
						if absf(rel) > PI * 0.75:
							_loop(_p_anim, "Walking_Backwards", stride_scale("Walking_Backwards", v))
						else:
							_loop(_p_anim, "Running_Strafe_Right" if rel > 0 else "Running_Strafe_Left", stride_scale("Running_Strafe_Left", v))
					else:
						var clip := gait_for(v)
						_loop(_p_anim, clip, stride_scale(clip, v) * (0.9 if f.p_stance else 1.0))
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
	_update_pack(f, dt)
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
	# (one flame's flicker for all of them: data/style.json, motion.flicker; an open flame twice a lamp's)
	var fw := TAU / Style.motion("flicker", "period", 0.7)
	var fd := Style.motion("flicker", "depth", 0.12)
	for idx in _torches.size():
		var l: OmniLight3D = _torches[idx]
		l.light_energy = 1.4 * Style.light_energy("fire") * (1.0 + 2.0 * fd * (0.6 * sin(_clock * fw + idx * 1.7) + 0.4 * sin(_clock * fw * 2.6 + idx)))
	# The Academy's lamps and fires, each about its own level; the rite dims them.
	for idx in _lamps.size():
		var lm: Dictionary = _lamps[idx]
		var fl := 1.0 if lm["steady"] else 1.0 + fd * (0.65 * sin(_clock * fw + idx * 1.9) + 0.35 * sin(_clock * fw * 2.6 + idx))
		(lm["light"] as OmniLight3D).light_energy = float(lm["base"]) * fl * lerpf(1.0, 0.1, _torch_dim)
	_update_cutaway()

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
	_update_stage(dt)
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
	if portrait and portrait_frame != "":
		# The creator's stage: a framing by name, the figure centred in what the panel leaves.
		var fr: Dictionary = Data.creation.get("stage", {}).get("frames", {}).get(portrait_frame, { "dist": 4.3, "look": 1.02, "rise": 0.1 })
		var sc := _player.scale.y if _player else 1.0
		var dist := float(fr["dist"])
		var look_y := float(fr["look"]) * sc
		if fr.get("head", false) and _p_skel != null and _head_bone >= 0 and _p_skel.is_inside_tree():
			look_y = (_p_skel.global_transform * _p_skel.get_bone_global_pose(_head_bone).origin).y - p.y + float(fr["look"]) * sc
		var vp := get_viewport().get_visible_rect().size
		var side := portrait_shift * dist * tan(deg_to_rad(camera.fov) / 2.0) * (vp.x / maxf(1.0, vp.y))
		var k3 := 1.0 - exp(-dt * 3.2)
		var sway3 := Vector3(sin(_clock * 0.23) * 0.05, sin(_clock * 0.31) * 0.018, 0) * dist
		_cam_pos = _cam_pos.lerp(p + Vector3(side, look_y + float(fr.get("rise", 0.0)) * dist, dist) + sway3, k3)
		_cam_look = _cam_look.lerp(p + Vector3(side, look_y, 0), k3)
		camera.position = _cam_pos
		camera.look_at(_cam_look, Vector3.UP)
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
		_ward.material_override = _mat(Style.shape_color("make"), 1.5, true, 0.45)
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
	_play(_p_anim, "Idle", breath(_p_anim, "Idle"), 0.0)
	_play(_w_anim, _wa("idle"), breath(_w_anim, _wa("idle")), 0.0)

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

## The ink line on the living (data/style.json, ink): by what carries it, "people", "beasts"
## or "genii". Places carry none. (A width given as a number, as this once took, is not
## heeded: the weight of the line is the style's.)
func _ink(category = "people") -> ShaderMaterial:
	var m := _shader_mat(INK)
	m.set_shader_parameter("width", Style.ink_width(String(category) if category is String else "people"))
	m.set_shader_parameter("screen", float(Style.data()["ink"].get("screen", 900)))
	m.set_shader_parameter("ink", Style.ink_color())
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
		sm.set_shader_parameter("tint", Style.light("moon", "color"))
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
		gm.set_shader_parameter("tint", Style.light("moon", "color"))
		gm.set_shader_parameter("strength", 0.3)
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
var _g_baby: Node3D = null         # the Baby: the body it has before the rite (docs/genius-lines.md)
var _g_baby_lit: Array = []        # its materials of the field, which take the partner's colour
var _g_baby_was := Vector3.ZERO
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
	# The Baby: before the rite the genius is the same small thing for everyone, a round body
	# with a face and the field in its eyes, its belly and the tip of its tail. It rides where
	# the orb did, and the orb's light is still round it.
	const BABY := "res://game/assets/genius/forms/baby.glb"
	if ResourceLoader.exists(BABY):
		_g_baby = load(BABY).instantiate()
		_g_core.mesh = null
		_g_core.add_child(_g_baby)
		_g_baby.scale = Vector3.ONE * (0.26 / 0.72)
		_g_baby.position = Vector3(0, -0.13, 0)
		var skins := _g_baby.find_children("*", "MeshInstance3D", true, false)
		for m in skins:
			var mi := m as MeshInstance3D
			for i in mi.mesh.get_surface_count():
				var born := mi.mesh.surface_get_material(i)
				if born is StandardMaterial3D and String(born.resource_name).begins_with("field"):
					var lit := (born as StandardMaterial3D).duplicate() as StandardMaterial3D
					lit.emission_enabled = true
					lit.emission_energy_multiplier = 2.2
					mi.set_surface_override_material(i, lit)
		toonify(_g_baby)
		for m in skins:
			var mi := m as MeshInstance3D
			mi.material_overlay = _ink(1.2)
			for i in mi.mesh.get_surface_count():
				var am := mi.get_active_material(i)
				if am and String(am.resource_name).begins_with("field"):
					_g_baby_lit.append(am)
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
	for m in _g_baby_lit:
		if m is ShaderMaterial:
			(m as ShaderMaterial).set_shader_parameter("emission", _g_tint)
		elif m is StandardMaterial3D:
			(m as StandardMaterial3D).emission = _g_tint
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
	# (in the creator's closest framing the mote would cross the face: it waits out of frame)
	var show := genius_visible and _player != null and _p_skel != null and _head_bone >= 0 and not (portrait and portrait_frame == "face")
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
	if _g_baby:
		# it looks where it is going
		var went := _g_pos - _g_baby_was
		_g_baby_was = _g_pos
		if Vector2(went.x, went.z).length() > 0.0004:
			_g_baby.rotation.y = lerp_angle(_g_baby.rotation.y, atan2(went.x, went.z), 1.0 - exp(-dt * 9.0))
	_g_halo.scale = Vector3.ONE * (0.8 + 1.4 * _g_pulse) * (0.3 + 0.7 * born_k)
	_g_halo_mat.set_shader_parameter("strength", (0.7 + 0.9 * _g_pulse) * bright * (0.42 if _g_baby else 1.0))
	_g_light.light_energy = (0.55 + 1.6 * _g_pulse) * bright
	_g_core_mat.albedo_color = _g_tint.lightened(0.55 + 0.4 * _g_pulse) * Color(1, 1, 1, 1)

# --- Places: the Cut, and the Academy's grounds ----------------------------------

## Leave the current place and build another: "cut" (the chamber of the opening and the
## practice yard) or a place of the Academy from data/academy.json.
func set_place(id: String, spec: Dictionary = {}) -> void:
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
	_cut_walls.clear()
	_lamps.clear()
	_sky_dome = null
	_ambient_lit = 0.0
	_env.ambient_light_source = _ambient_default
	if id == "cut":
		_build_chamber()
		_moonlight([[Vector3(-5.5, 0, -2.6), 1.3], [Vector3(3.2, 0, 3.4), 0.9], [Vector3(8.6, 0, -4.4), 1.1]])
		_light_place("cut")
	elif id == "stage":
		_build_stage()
	else:
		_build_academy_place(spec if not spec.is_empty() else Data.academy["places"][id])
	_motes.emission_box_extents = Vector3(arena.x / 2.0, 1.8, arena.y / 2.0)
	_motes.restart()

# --- The creator's stage: a platform on the line, at night (data/creation.json, stage) ------

var _stage_light: OmniLight3D = null
var _stage_glow: MeshInstance3D = null
var _stage_k := 0.0
var _stage_flare := 0.0

## Where the figure stands on the stage.
func stage_spot() -> Vector2:
	var sp: Array = Data.creation.get("stage", {}).get("spawn", [0, 0])
	return Vector2(float(sp[0]), float(sp[1]))

## The stage of the character creator, built from the Academy's kit: a wayside platform under a
## lamp, the line behind. Three lights of its own make a face read: a warm key from the lamp's
## side, a cool fill, a cool rim from behind. The field gathers where the figure will stand.
func _build_stage() -> void:
	var spec: Dictionary = Data.creation["stage"]
	_build_academy_place(spec)
	var at := _v3(stage_spot())
	var L: Dictionary = spec.get("lights", {})
	for id in L:
		var d: Dictionary = L[id]
		var from := at + Vector3(d["from"][0], d["from"][1], d["from"][2])
		var c: Array = d["color"]
		var light: Light3D
		if d.get("spot", true):
			var sl := SpotLight3D.new()
			sl.spot_range = float(d.get("range", 9.0))
			sl.spot_angle = float(d.get("angle", 34.0))
			sl.spot_attenuation = 0.8
			sl.spot_angle_attenuation = 0.7
			light = sl
		else:
			var ol := OmniLight3D.new()
			ol.omni_range = float(d.get("range", 7.0))
			light = ol
		light.light_color = Color(c[0], c[1], c[2])
		light.light_energy = float(d["energy"])
		light.shadow_enabled = bool(d.get("shadow", false))
		light.light_specular = 0.4
		_place_root.add_child(light)
		light.position = from
		if light is SpotLight3D:
			light.look_at(at + Vector3(0, float(d.get("aim", 1.3)), 0), Vector3.UP)
	# the field: a light and a soft glow at the spot, in the colour the answers lean
	_stage_light = OmniLight3D.new()
	_stage_light.omni_range = 5.5
	_stage_light.omni_attenuation = 1.3
	_stage_light.light_energy = 0.0
	_stage_light.position = at + Vector3(0, 0.9, 0)
	_place_root.add_child(_stage_light)
	_stage_glow = MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(3.4, 3.4)
	_stage_glow.mesh = q
	var gm := _shader_mat(GLOW)
	gm.set_shader_parameter("falloff", 2.6)
	gm.set_shader_parameter("strength", 0.0)
	_stage_glow.material_override = gm
	_stage_glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_stage_glow.position = at + Vector3(0, 1.0, 0)
	_place_root.add_child(_stage_glow)
	_stage_k = 0.0
	_stage_flare = 0.0

## The field at the spot: its colour, how far it has gathered (0 to 1), and a flare when the
## figure steps out of it.
func stage_field(col: Color, k: float, flare := 0.0) -> void:
	if _stage_light == null or not is_instance_valid(_stage_light):
		return
	_stage_light.light_color = col
	(_stage_glow.material_override as ShaderMaterial).set_shader_parameter("tint", col)
	_stage_k = k
	if flare > 0.0:
		_stage_flare = flare
		burst(_stage_light.global_position, col.lightened(0.3), 46, 3.4)

func _update_stage(dt: float) -> void:
	if place != "stage" or _stage_light == null or not is_instance_valid(_stage_light):
		return
	_stage_flare = maxf(0.0, _stage_flare - dt * 1.4)
	var breathe := 0.9 + 0.1 * sin(_clock * 1.7)
	var want := 2.2 * _stage_k * breathe + 5.0 * _stage_flare
	_stage_light.light_energy = lerpf(_stage_light.light_energy, want, 1.0 - exp(-dt * 3.0))
	var gm := _stage_glow.material_override as ShaderMaterial
	var g: float = gm.get_shader_parameter("strength")
	gm.set_shader_parameter("strength", lerpf(g, 0.55 * _stage_k * breathe + 0.6 * _stage_flare, 1.0 - exp(-dt * 3.0)))

## The look changed and the body did not: dress the standing figure again.
func redress(hero: Dictionary) -> void:
	if _player:
		dress(_player, hero.get("look", {}), hero)

## Show or hide the standing figure and the mote of its genius (the stage waits empty while
## the questions are asked).
func show_figure(on: bool) -> void:
	if _player:
		_player.visible = on
	genius_visible = on

## Someone else's genius, standing by them: built as the hero's is, at their heel if it walks
## and at their shoulder if it does not.
func _figure_genius(person: Node3D, info: Dictionary, col: Color) -> GeniusBody:
	var gb := make_form(info, col.lightened(0.15)) as GeniusBody
	gb.name = "TheirGenius"
	person.add_child(gb)
	gb.position = Vector3(0.85, 0.0, -0.2) if gb.walks() else Vector3(0.7, 1.3, 0.1)
	gb.rotation.y = 0.35
	return gb

## A place of the Academy: a floor, walls of the fortress with an arch at every door, torches,
## and the props that say what the place is for. Evening at the Thaw: a deep blue sky.
func _build_academy_place(spec: Dictionary) -> void:
	arena = Vector2(spec["size"][0], spec["size"][1])
	# --kaykit (after --) builds the old dungeon-tile places, to compare.
	if spec.has("style") and ResourceLoader.exists(ACADEMY_DIR % String(spec["style"].get("floor", "floor_flags"))) and not OS.get_cmdline_user_args().has("--kaykit"):
		_build_kit_place(spec)
		return
	var hw := arena.x / 2.0 + 1.0
	var hd := arena.y / 2.0 + 1.0
	var floor_piece: String = spec["floor"]
	var in_zone := spec.has("wild")
	var x := -hw + 2.0
	var i := 0
	if in_zone:
		_build_zone_ground(spec, hw, hd)
		x = hw
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
	if in_zone:
		wx = hw
	while wx < hw:
		for side in [-1, 1]:
			var kind: String = "wall_arched" if is_door.call(wx, side * (hd - 1.0)) else kinds[(k + (3 if side > 0 else 0)) % kinds.size()]
			_piece(kind, Vector3(wx, 0, side * hd), 0.0 if side < 0 else 180.0)
			if k % 2 == 0 and kind != "wall_arched" and not wild:
				_torch(Vector3(wx, 2.4, side * (hd - 0.45)), 0.0 if side < 0 else 180.0)
		wx += 4.0
		k += 1
	var ez := -hd + 2.0
	if in_zone:
		ez = hd
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
	if spec.has("board"):
		var ba := Vector3(float(spec["board"]["at"][0]), 0, float(spec["board"]["at"][1]))
		_piece("crates_stacked", ba, 20.0, 0.5)
		_piece("banner_patternA_red", ba + Vector3(0, 0.6, -0.6), 0.0)
		obstacles.append(Vector3(ba.x, ba.z, 0.8))
		var l := Label3D.new()
		l.text = "THE BOARD"
		l.font = Style.font("title")
		l.font_size = 26
		l.pixel_size = 0.006
		l.modulate = Color(1.0, 0.85, 0.6)
		l.outline_size = 8
		l.outline_modulate = Color(0, 0, 0, 0.8)
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.position = ba + Vector3(0, 2.6, 0)
		_place_root.add_child(l)
	if spec.get("rails", false):
		_rails(arena.x / 2.0 + 1.0)
	match String(spec["name"]):
		"The Quad": _furnish_quad()
		"The Yard": _furnish_yard()
		"The Dormitory": _furnish_dorm(spec)
		"The Hearth Hall": _furnish_hearth()
	if in_zone:
		_furnish_zone(spec)
		return
	if wild:
		_furnish_wild(spec)
		_light_place("wild")
		_moonlight([[Vector3(-arena.x * 0.2, 0, -arena.y * 0.15), 1.4], [Vector3(arena.x * 0.28, 0, arena.y * 0.2), 1.0], [Vector3(0, 0, 0), 0.8]])
		return
	_light_place("court", { "ambientEnergy": 0.34, "fogDensity": 0.012, "moon": 0.28 })
	if spec.get("walls", "") != "fortress" or arena.x > 20.0:
		_moonlight([[Vector3(arena.x * 0.18, 0, -arena.y * 0.12), 1.2], [Vector3(-arena.x * 0.25, 0, arena.y * 0.2), 0.9]])

# --- The Academy's own architecture (tools/blender/academy_kit.py, docs/home-base.md) -----

const ACADEMY_DIR := "res://game/assets/academy/%s.glb"
## Pieces 8 wide; every other wall piece is 4.
const WIDE_PIECES := ["range_portal", "library_portal", "gatehouse", "curtain_portal", "station_portal", "line_arch", "hall_portal", "hall_hearth"]
## What a light the kit marks (an empty named light_<kind>) gives: colour, energy, range. The
## colours are the style's lights (data/style.json): the lamp's, the fire's, the moon's, and
## the Library's glass banked down.
static func kit_light(kind: String) -> Array:
	match kind:
		"lamp": return [Style.light("lamp"), 0.95 * Style.light_energy("lamp"), 7.0]
		"fire": return [Style.light("fire"), 2.0 * Style.light_energy("fire"), 12.0]
		"stain": return [Color(String(Style.data()["lights"]["stain"].get("cast", "#B9A6D9"))), 0.5 * float(Style.data()["lights"]["stain"].get("energy", 0.5)) * 2.0, 6.5]
		"cool": return [Style.light("moon"), 1.1 * Style.light_energy("moon"), 8.0]
	return []

var _cut_walls: Array = []    # {upper, at, out, out2}: a wall's upper part hides on the camera's side
var _lamps: Array = []        # {light, base, steady}: the kit's lights, flickering about their own level
var _sky_dome: MeshInstance3D = null
var _ambient_default := Environment.AMBIENT_SOURCE_COLOR
var _stain_count := 0
var _lamp_scale := 1.0     # a place's own level for its lamps (style.lamps)

const SKY := """
shader_type spatial;
// The sky over the Academy at dusk: night above, the last of the day along the horizon,
// stars, a moon. A dome drawn behind everything.
render_mode unshaded, cull_disabled, depth_draw_never, fog_disabled, shadows_disabled;
uniform vec3 moon_dir = vec3(0.35, 0.55, -0.75);
uniform vec3 top : source_color = vec3(0.075, 0.094, 0.14);
uniform vec3 mid : source_color = vec3(0.13, 0.16, 0.22);
uniform vec3 low : source_color = vec3(0.22, 0.2, 0.25);
uniform vec3 ember : source_color = vec3(0.48, 0.29, 0.2);
uniform vec3 stars : source_color = vec3(0.8, 0.83, 0.92);
uniform vec3 moon : source_color = vec3(0.87, 0.89, 0.95);
uniform vec3 halo : source_color = vec3(0.23, 0.26, 0.38);
varying vec3 dir;
float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}
void vertex() { dir = normalize(VERTEX); }
void fragment() {
	vec3 d = normalize(dir);
	float h = d.y;
	vec3 col = mix(mid, top, smoothstep(0.12, 0.8, h));
	col = mix(low, col, smoothstep(0.0, 0.3, h));
	// the last light, in the west only
	float west = smoothstep(0.2, 1.0, dot(normalize(vec3(d.x, 0.0, d.z) + vec3(0.0001)), normalize(vec3(-0.8, 0.0, 0.6))));
	col = mix(col, ember, west * (1.0 - smoothstep(0.0, 0.16, h)) * 0.8);
	// stars, thinning toward the horizon
	vec3 gp = d * 170.0;
	vec3 g = floor(gp);
	float r = hash(g);
	float star = step(0.992, r) * smoothstep(0.08, 0.4, h) * smoothstep(0.3, 0.05, length(fract(gp) - 0.5));
	col += stars * star * (0.5 + 0.5 * sin(TIME * (1.0 + r * 3.0) + r * 40.0)) * 0.9;
	// the moon and its halo
	float m = dot(d, normalize(moon_dir));
	col += moon * smoothstep(0.99965, 0.9998, m);
	col += halo * pow(max(m, 0.0), 220.0);
	if (h < 0.0) { col = mix(low * 0.35, vec3(0.008, 0.008, 0.012), smoothstep(0.0, -0.08, h)); }
	ALBEDO = col;
}
"""

## One piece of the kit, placed; null if the file is not there. The lights it marks are hung.
func _kit_piece(name: String, pos: Vector3, rot_deg := 0.0, scale := Vector3.ONE) -> Node3D:
	var path := ACADEMY_DIR % name
	if not ResourceLoader.exists(path):
		return null
	var n: Node3D = load(path).instantiate()
	n.position = pos
	n.rotation_degrees.y = rot_deg
	n.scale = scale
	_place_root.add_child(n)
	toonify(n)
	if name.begins_with("floor_"):
		# a floor takes shadows and casts none
		for m in n.find_children("*", "MeshInstance3D", true, false):
			(m as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.find_children("light_*", "", true, false):
		var kind := String(c.name).get_slice("_", 1)
		if kit_light(kind).is_empty():
			continue
		# coloured glass lights every other bay only, and no place more lights than it can draw
		if kind == "stain":
			_stain_count += 1
			if _stain_count % 2 == 0 and not WIDE_PIECES.has(name):
				continue
		if _lamps.size() >= 26:
			continue
		var k: Array = kit_light(kind)
		var light := OmniLight3D.new()
		light.light_color = k[0]
		light.light_energy = k[1]
		light.omni_range = float(k[2]) * (1.6 if String(c.name).contains("tower") else (0.6 if String(c.name).contains("small") else 1.0))
		light.omni_attenuation = 1.4
		light.shadow_enabled = false
		(c as Node3D).add_child(light)
		_lamps.append({ "light": light, "base": float(k[1]) * _lamp_scale, "steady": kind in ["stain", "cool"] })
	return n

## A place built from the Academy's kit by its style (data/academy.json): a floor, four sides
## of wall bays with a door piece at every door, corners, trusses indoors, and the furniture.
func _build_kit_place(spec: Dictionary) -> void:
	var style: Dictionary = spec["style"]
	var hall: bool = String(style.get("kind", "court")) == "hall"
	# the walls stand a tile's grid round the arena, at least a unit clear of where people walk
	var W := ceilf((arena.x + 2.0) / 4.0) * 4.0
	var D := ceilf((arena.y + 2.0) / 4.0) * 4.0
	_stain_count = 0
	_lamp_scale = float(style.get("lamps", 1.0))
	# the floor
	var boards: bool = String(style["floor"]) == "floor_boards"
	var i := 0
	var x := -W / 2.0 + 2.0
	while x < W / 2.0:
		var z := -D / 2.0 + 2.0
		while z < D / 2.0:
			_kit_piece(String(style["floor"]), Vector3(x, 0, z), (180.0 * (i % 2)) if boards else 90.0 * ((i * 7 + int(x)) % 4))
			z += 4.0
			i += 1
		x += 4.0
	for lawn in style.get("lawns", []):
		_kit_rect(String(style.get("lawn", "floor_lawn")), float(lawn[0]), float(lawn[1]), float(lawn[2]), float(lawn[3]), 0.07)
	# the four sides
	var doors: Array = spec["doors"]
	var sides: Dictionary = style.get("sides", {})
	for side in ["n", "s", "w", "e"]:
		var ss: Dictionary = sides.get(side, {})
		if ss.get("open", false):
			continue   # no wall on this side: the creator's stage is seen from here
		var along_x: bool = side in ["n", "s"]
		var length := W if along_x else D
		var fixed := (-D / 2.0 if side == "n" else D / 2.0) if along_x else (-W / 2.0 if side == "w" else W / 2.0)
		var rot: float = { "n": 0.0, "s": 180.0, "w": 90.0, "e": -90.0 }[side]
		var out: Vector3 = { "n": Vector3(0, 0, -1), "s": Vector3(0, 0, 1), "w": Vector3(-1, 0, 0), "e": Vector3(1, 0, 0) }[side]
		# what must stand at a given place along the side: a door piece at each door, and features
		var feats: Array = []
		for d in doors:
			var dx := float(d["at"][0])
			var dz := float(d["at"][1])
			var on_side := absf(dz - signf(fixed) * arena.y / 2.0) < 0.6 if along_x else absf(dx - signf(fixed) * arena.x / 2.0) < 0.6
			if on_side:
				feats.append({ "piece": String(d.get("piece", ss.get("door", style.get("door", "range_door")))), "at": dx if along_x else dz })
		for f in ss.get("features", []):
			feats.append({ "piece": String(f["piece"]), "at": float(f["at"]) })
		feats.sort_custom(func(a, b): return float(a["at"]) < float(b["at"]))
		var bays: Array = ss.get("bays", style.get("bays", ["range_plain"]))
		var cursor := -length / 2.0
		var b := 0
		for fi in feats.size() + 1:
			var stop := length / 2.0
			var fw := 0.0
			var fat := 0.0
			if fi < feats.size():
				fw = 8.0 if WIDE_PIECES.has(feats[fi]["piece"]) else 4.0
				fat = clampf(float(feats[fi]["at"]), cursor + fw / 2.0, length / 2.0 - fw / 2.0)
				stop = fat - fw / 2.0
			var gap := stop - cursor
			if gap > 0.4:
				var count := maxi(1, int(round(gap / 4.0)))
				var bw := gap / count
				for k in count:
					var t := cursor + bw * (k + 0.5)
					_kit_wall(String(bays[b % bays.size()]), t, fixed, along_x, rot, out, bw / 4.0)
					b += 1
			if fi < feats.size():
				_kit_wall(String(feats[fi]["piece"]), fat, fixed, along_x, rot, out, 1.0)
				cursor = fat + fw / 2.0
	# the corners
	var corner := String(style.get("corner", ""))
	if corner != "":
		for c in [[1, -1, 0.0], [-1, -1, 90.0], [-1, 1, 180.0], [1, 1, 270.0]]:
			var cat := Vector3(c[0] * W / 2.0, 0, c[1] * D / 2.0)
			var cn := _kit_piece(corner, cat, c[2])
			if cn and cn.has_node("Upper"):
				_cut_walls.append({ "upper": cn.get_node("Upper"), "at": cat, "out": Vector3(c[0], 0, 0), "out2": Vector3(0, 0, c[1]) })
	# the roof's timbers, indoors
	if style.has("trusses"):
		var tr: Dictionary = style["trusses"]
		var across_z: bool = String(tr.get("across", "z")) == "z"
		var run := W if across_z else D
		var t2 := -run / 2.0 + 2.0
		while t2 < run / 2.0:
			_kit_piece(String(tr["piece"]), Vector3(t2, 0, 0) if across_z else Vector3(0, 0, t2), 90.0 if across_z else 0.0)
			t2 += float(tr.get("every", 4.0))
	# the line, where the place has one: cinders between the platforms, the rails, the buffer
	if style.has("track"):
		var from := float(style["track"].get("from", -W / 2.0))
		var tx := from + 2.0
		while tx < W / 2.0 + 2.0:
			_kit_piece("floor_ballast", Vector3(tx, 0.035, 0), 0.0, Vector3(1, 1, 0.82))
			for sz in [-1, 1]:
				_kit_piece("platform_edge", Vector3(tx, 0.06, sz * 1.9), 0.0 if sz > 0 else 180.0)
			tx += 4.0
		if style["track"].get("through", false):
			# the line runs on through both ends
			_rails(W / 2.0 + 1.0)
		else:
			_rails(W / 2.0 + 1.0, from + 0.6)
			_kit_piece("buffer_stop", Vector3(from + 0.4, 0, 0), 0.0)
			obstacles.append(Vector3(from + 0.2, 0, 1.2))
	# the furniture
	for f in spec.get("furniture", []):
		var at := Vector3(float(f["at"][0]), float(f.get("y", 0.0)), float(f["at"][1]))
		var sc := float(f.get("scale", 1.0))
		if _kit_piece(String(f["piece"]), at, float(f.get("rot", 0.0)), Vector3.ONE * sc) == null:
			continue
		if f.has("solid"):
			obstacles.append(Vector3(at.x, at.z, float(f["solid"])))
		for so in f.get("solids", []):
			obstacles.append(Vector3(at.x + float(so[0]), at.z + float(so[1]), float(so[2])))
	for d in doors:
		_door_marker(Vector3(float(d["at"][0]), 0, float(d["at"][1])), String(d["label"]), d.has("locked") and not open_doors.has(d["to"]))
	if spec.has("board"):
		var ba := Vector3(float(spec["board"]["at"][0]), 0, float(spec["board"]["at"][1]))
		_kit_piece("notice_board", ba, float(spec["board"].get("rot", 0.0)))
		obstacles.append(Vector3(ba.x - 0.8, ba.z, 0.7))
		obstacles.append(Vector3(ba.x + 0.8, ba.z, 0.7))
		var l := Label3D.new()
		l.text = "THE BOARD"
		l.font = Style.font("title")
		l.font_size = 26
		l.pixel_size = 0.006
		l.modulate = Color(1.0, 0.85, 0.6)
		l.outline_size = 8
		l.outline_modulate = Color(0, 0, 0, 0.8)
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.position = ba + Vector3(0, 4.1, 0)
		_place_root.add_child(l)
	match String(spec["name"]):
		"The Yard": _furnish_yard(true)
		"The Hearth Hall": _furnish_hearth(true)
	# the light of the place
	_ambient_lit = float(style.get("ambient", 0.3 if hall else 0.5))
	_torch_dim = 0.0
	if hall:
		# indoors: no sky, the dark of a roof overhead, lamps and a fire
		_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		_light_place("hall", { "ambientEnergy": _ambient_lit })
	else:
		_light_place("court", { "ambientEnergy": _ambient_lit, "moon": float(style.get("moon", Style.place_light("court")["moon"])) })
		_sky_dome = MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 260.0
		sm.height = 520.0
		sm.radial_segments = 24
		sm.rings = 12
		_sky_dome.mesh = sm
		var sky_mat := _shader_mat(SKY)
		var sky_cols: Dictionary = Style.data()["lights"]["sky"]
		for k in ["top", "mid", "low", "ember", "stars", "moon", "halo"]:
			sky_mat.set_shader_parameter(k, Color(String(sky_cols[k])))
		_sky_dome.material_override = sky_mat
		_sky_dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_sky_dome.extra_cull_margin = 1000.0
		_place_root.add_child(_sky_dome)
		for pool in style.get("pools", []):
			# the Library's glass on the paving: a pool of coloured light
			var pm := MeshInstance3D.new()
			var plane := PlaneMesh.new()
			plane.size = Vector2(float(pool[2]), float(pool[2]) * 1.6)
			pm.mesh = plane
			var gm := _shader_mat(GLOW)
			gm.set_shader_parameter("billboard", false)
			gm.set_shader_parameter("tint", Color(String(pool[3])))
			gm.set_shader_parameter("strength", 0.34)
			gm.set_shader_parameter("falloff", 1.5)
			pm.material_override = gm
			pm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			pm.position = Vector3(float(pool[0]), 0.14, float(pool[1]))
			_place_root.add_child(pm)

## A wall piece on a side, and its upper part entered for the cutaway.
func _kit_wall(name: String, t: float, fixed: float, along_x: bool, rot: float, out: Vector3, stretch: float) -> void:
	var at := Vector3(t, 0, fixed) if along_x else Vector3(fixed, 0, t)
	var n := _kit_piece(name, at, rot, Vector3(stretch, 1, 1))
	if n == null:
		# the kit lacks the piece: KayKit's wall stands in
		_piece("wall_arched" if name.contains("door") or name.contains("portal") else "wall", at, rot)
		return
	if n.has_node("Upper"):
		_cut_walls.append({ "upper": n.get_node("Upper"), "at": at, "out": out, "out2": Vector3.ZERO })

## A rectangle of the floor laid again in another tile (the lawns), a little proud of it.
func _kit_rect(name: String, x0: float, z0: float, x1: float, z1: float, y: float) -> void:
	var nx := maxi(1, int(round((x1 - x0) / 4.0)))
	var nz := maxi(1, int(round((z1 - z0) / 4.0)))
	var sx := (x1 - x0) / nx
	var sz := (z1 - z0) / nz
	for ix in nx:
		for iz in nz:
			_kit_piece(name, Vector3(x0 + sx * (ix + 0.5), y, z0 + sz * (iz + 0.5)), 0.0, Vector3(sx / 4.0, 1, sz / 4.0))

## Tall walls never stand between the camera and the hero: a wall's upper part hides while the
## camera is outside it (or pressed against it), leaving its plinth as the room's edge.
func _update_cutaway() -> void:
	if _cut_walls.is_empty():
		return
	var cp := camera.global_position
	for w in _cut_walls:
		var rel: Vector3 = cp - (w["at"] as Vector3)
		var hide := rel.dot(w["out"]) > -1.4
		if (w["out2"] as Vector3) != Vector3.ZERO:
			hide = hide or rel.dot(w["out2"]) > -1.4
		(w["upper"] as Node3D).visible = not hide

## The line itself: ties and two rails across the place.
func _rails(hw: float, from := -INF) -> void:
	var tie := _mat(Color(0.22, 0.15, 0.1))
	var rail := _mat(Color(0.42, 0.4, 0.38))
	rail.metallic = 0.85
	rail.roughness = 0.3
	var x0 := maxf(-hw, from)
	var tx := x0
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
		rm.size = Vector3(hw - x0, 0.12, 0.1)
		var r := MeshInstance3D.new()
		r.mesh = rm
		r.position = Vector3((hw + x0) / 2.0, 0.2, rz)
		r.material_override = rail
		_place_root.add_child(r)

func _torch(at: Vector3, rot: float) -> void:
	var t := _piece("torch_mounted", at, rot)
	var light := OmniLight3D.new()
	light.light_color = Style.light("fire")
	light.light_energy = 1.5 * Style.light_energy("fire")
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
		_build_post(Vector3(float(spec["post"]["at"][0]), 0, float(spec["post"]["at"][1])))

## The post: an iron lamp column with the line's blue flame, and the ring the party holds.
func _build_post(pa: Vector3) -> void:
	var flame_y := 1.55
	var lamp_y := 2.2
	if ResourceLoader.exists(WILD_DIR % "set_post"):
		var post := _wild_piece("set_post", pa, 0.0)
		var sock: Node3D = post.find_child("socket_flame", true, false)
		if sock:
			flame_y = sock.position.y
			lamp_y = flame_y + 0.3
	else:
		_piece("column", pa, 0.0, 0.45)
	obstacles.append(Vector3(pa.x, pa.z, 0.6))
	if true:
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
		lamp.light_color = Style.light("lamp")
		lamp.light_energy = 1.8 * Style.light_energy("lamp")
		lamp.omni_range = 8.0
		lamp.position = pa + Vector3(0, lamp_y, 0)
		_place_root.add_child(lamp)
		var flame := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.2
		sm.height = 0.4
		flame.mesh = sm
		flame.material_override = _mat(Color(0.6, 0.8, 1.0), 4.0, true)
		flame.position = pa + Vector3(0, flame_y, 0)
		_place_root.add_child(flame)

# --- Zones: areas drawn from a tile library ---------------------------------------------
# A zone's area (data/zones.json via Zones.area_place) comes with the zone's tiles: ground
# tiles by weight, edge pieces round the rim with a gap at every door, props scattered by the
# area's density and the run's variant, a set piece, the post, the line's ballast and rails,
# water along a side. Until the wild kit is built, the dungeon kit stands in for every piece.

const WILD_DIR := "res://game/assets/wild/%s.glb"

func _wild_piece(name: String, pos: Vector3, rot_deg := 0.0, scale := 1.0) -> Node3D:
	var path := WILD_DIR % name
	if ResourceLoader.exists(path):
		var n: Node3D = load(path).instantiate()
		n.position = pos
		n.rotation_degrees.y = rot_deg
		n.scale = Vector3.ONE * scale
		_place_root.add_child(n)
		toonify(n)
		return n
	var sub := "rubble_half"
	var sub_scale := scale
	if name.begins_with("ground_"):
		sub = "floor_dirt_large_rocky"
	elif name.begins_with("edge_"):
		sub = "wall_broken" if name != "edge_rocks" and name != "edge_cliff" else "rubble_large"
	elif name.begins_with("tree_") or name in ["ruin_column", "signal_post", "lamp_post", "fence_post"]:
		sub = "column"
		sub_scale = scale * 0.55
	elif name.begins_with("set_"):
		sub = "rubble_large"
		sub_scale = scale * 1.6
	elif name in ["boulder_a", "boulder_b", "cairn", "rail_car", "ruin_arch"]:
		sub = "rubble_large"
		sub_scale = scale * 0.6
	else:
		sub_scale = scale * 0.5
	return _piece(sub, pos, rot_deg, sub_scale)

## One of a weighted list [[name, weight], ...] or [[name, radius, weight], ...].
func _pick(options: Array, rng: RandomNumberGenerator) -> Array:
	var total := 0.0
	for o in options:
		total += float(o[o.size() - 1])
	var r := rng.randf() * total
	for o in options:
		r -= float(o[o.size() - 1])
		if r <= 0.0:
			return o
	return options[0]

func _zone_rng(spec: Dictionary) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(spec.get("variant", 0))
	return rng

func _build_zone_ground(spec: Dictionary, hw: float, hd: float) -> void:
	var z: Dictionary = spec["wild"]
	var area: Dictionary = spec["area"]
	var rng := _zone_rng(spec)
	var water := String(area.get("water", ""))
	var x := -hw + 2.0
	while x < hw:
		var zz := -hd + 2.0
		while zz < hd:
			var name: String = _pick(z["tiles"]["floor"], rng)[0]
			if area.get("rails", false) and absf(zz) < 2.0:
				name = "ground_ballast"
			if (water == "north" and zz < -hd + 4.5) or (water == "south" and zz > hd - 4.5):
				name = "ground_water"
			_wild_piece(name, Vector3(x, 0, zz), 90.0 * (rng.randi() % 4))
			zz += 4.0
		x += 4.0
	# The rim: an edge piece every four metres, none where a door is.
	var doors: Array = spec["doors"]
	var is_door := func(px: float, pz: float) -> bool:
		for d in doors:
			if absf(float(d["at"][0]) - px) < 2.6 and absf(float(d["at"][1]) - pz) < 2.6:
				return true
		return false
	var wx := -hw + 2.0
	while wx < hw:
		for side in [-1, 1]:
			if is_door.call(wx, side * (hd - 1.0)):
				continue
			var name: String = _pick(z["tiles"]["edge"], rng)[0]
			if water == "north" and side < 0:
				name = "edge_reeds"
			_wild_piece(name, Vector3(wx, 0, side * hd), 0.0 if side < 0 else 180.0)
		wx += 4.0
	var ez := -hd + 2.0
	while ez < hd:
		for side in [-1, 1]:
			if is_door.call(side * (hw - 1.0), ez):
				continue
			_wild_piece(_pick(z["tiles"]["edge"], rng)[0], Vector3(side * hw, 0, ez), 90.0 if side < 0 else -90.0)
		ez += 4.0

func _furnish_zone(spec: Dictionary) -> void:
	var z: Dictionary = spec["wild"]
	var area: Dictionary = spec["area"]
	var rng := _zone_rng(spec)
	rng.state = rng.state + 7
	var keep: Array = []   # [Vector2, radius] nothing may stand in
	keep.append([Vector2(float(spec["spawn"][0]), float(spec["spawn"][1])), 3.0])
	for d in spec["doors"]:
		keep.append([Vector2(float(d["at"][0]), float(d["at"][1])), 3.0])
	if spec.has("post"):
		var pa := Vector2(float(spec["post"]["at"][0]), float(spec["post"]["at"][1]))
		keep.append([pa, 4.2])
		_build_post(Vector3(pa.x, 0, pa.y))
	for ins in spec.get("instructors", []):
		keep.append([Vector2(float(ins["at"][0]), float(ins["at"][1])), 1.5])
	# The car waits beyond the door that leads back to the line, lamps lit.
	for d in spec["doors"]:
		if d["to"] == "extraction":
			var da := Vector2(float(d["at"][0]), float(d["at"][1]))
			var out_dir := da.normalized() if da.length() > 0.1 else Vector2(-1, 0)
			var ca := da + out_dir * 4.5
			var along_x := absf(out_dir.x) > absf(out_dir.y)
			_wild_piece("set_car", Vector3(ca.x, 0, ca.y), 0.0 if along_x else 90.0)
			var lamp := OmniLight3D.new()
			lamp.light_color = Style.light("lamp")
			lamp.light_energy = 1.4 * Style.light_energy("lamp")
			lamp.omni_range = 9.0
			lamp.position = Vector3(ca.x, 2.4, ca.y) - Vector3(out_dir.x, 0, out_dir.y) * 2.0
			_place_root.add_child(lamp)
	if area.has("set"):
		var sa := Vector2(float(area["setAt"][0]), float(area["setAt"][1]))
		_wild_piece(area["set"], Vector3(sa.x, 0, sa.y), float(area.get("setRot", 0.0)))
		obstacles.append(Vector3(sa.x, sa.y, 2.4))
		keep.append([sa, 4.0])
	var water := String(area.get("water", ""))
	var props: Array = z["tiles"]["props"]
	var count := int(float(area.get("density", 0.4)) * arena.x * arena.y / 16.0)
	var placed := 0
	var tries := 0
	while placed < count and tries < count * 12 and not props.is_empty():
		tries += 1
		var o: Array = _pick(props, rng)
		var at := Vector2(rng.randf_range(-arena.x / 2.0 + 1.2, arena.x / 2.0 - 1.2), rng.randf_range(-arena.y / 2.0 + 1.2, arena.y / 2.0 - 1.2))
		if area.get("rails", false) and absf(at.y) < 2.6:
			continue
		if (water == "north" and at.y < -arena.y / 2.0 + 3.0) or (water == "south" and at.y > arena.y / 2.0 - 3.0):
			continue
		var blocked := false
		for k in keep:
			if at.distance_to(k[0]) < float(k[1]):
				blocked = true
				break
		if blocked:
			continue
		var r := float(o[1])
		_wild_piece(o[0], Vector3(at.x, 0, at.y), rng.randf_range(0, 360), rng.randf_range(0.85, 1.15))
		if r > 0.0:
			obstacles.append(Vector3(at.x, at.y, r))
		keep.append([at, maxf(r, 0.6) + 0.8])
		placed += 1
	# The zone's night.
	var L: Dictionary = z["light"]
	var over := { "sky": Color(L["sky"][0], L["sky"][1], L["sky"][2]).to_html(false), "ambient": Color(L["ambient"][0], L["ambient"][1], L["ambient"][2]).to_html(false),
		"ambientEnergy": float(L["ambientEnergy"]), "fogDensity": float(L["fog"]), "moon": float(L["moon"]) }
	if L.has("moonColor"):
		over["moonColor"] = Color(L["moonColor"][0], L["moonColor"][1], L["moonColor"][2]).to_html(false)
	_light_place("wild", over)
	_moonlight([[Vector3(-arena.x * 0.2, 0, -arena.y * 0.15), 1.4], [Vector3(arena.x * 0.28, 0, arena.y * 0.2), 1.0], [Vector3(0, 0, 0), 0.8]])

func _furnish_quad() -> void:
	# The middle of the quad: a brazier that never goes out; the decorated pillars stand in its corners.
	for c in [Vector2(-12, -8), Vector2(12, -8), Vector2(-12, 8.5), Vector2(12, 8.5)]:
		_piece("pillar_decorated", Vector3(c.x, 0, c.y), 0.0)
		obstacles.append(Vector3(c.x, c.y, 0.9))
	var lamp := OmniLight3D.new()
	lamp.light_color = Style.light("fire")
	lamp.light_energy = 2.2 * Style.light_energy("fire")
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

func _furnish_yard(kit := false) -> void:
	if not kit:
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
# --- The pack ------------------------------------------------------------------------
# The rest of the pack: a body each, on the wolf rig, drawn from the fight's foes. The one the
# hero is locked on to is the wolf above (w_*); when it falls and the lock moves, the bodies
# swap with the data so nothing jumps.

var _pack: Array = []   # one per fight.foes: {node, anim, meshes, overlay, label, alert, flash, cur, until, spec}

func _pack_make(fo: Foe) -> Dictionary:
	var n: Node3D = load(_beast_model(String(fo.beast.get("model", "")))).instantiate()
	n.scale = Vector3.ONE * WOLF_SCALE * float(fo.beast.get("modelScale", 1.0))
	add_child(n)
	toonify(n)
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	for key in ["idle", "walk", "gallop", "windup", "stagger", "flinch"]:
		if ap.has_animation(WOLF_ANIMS[key]):
			ap.get_animation(WOLF_ANIMS[key]).loop_mode = Animation.LOOP_LINEAR
	var meshes := n.find_children("*", "MeshInstance3D", true, false)
	var ov := _mat(C_WINDUP, 2.0, true, 0.0)
	ov.next_pass = _ink("beasts")
	for m in meshes:
		m.material_overlay = ov
	var l := Label3D.new()
	l.font = Style.font("title")
	l.font_size = 22
	l.fixed_size = true
	l.pixel_size = 0.0011
	l.modulate = C_DIM
	l.outline_size = 8
	l.outline_modulate = Color(0, 0, 0, 0.85)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	add_child(l)
	var al := Label3D.new()
	al.font_size = 96
	al.text = "!"
	al.modulate = C_WINDUP
	al.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	al.no_depth_test = true
	al.pixel_size = 0.004
	al.outline_size = 10
	al.outline_modulate = Color(0, 0, 0, 0.85)
	al.visible = false
	add_child(al)
	return { "node": n, "anim": ap, "meshes": meshes, "overlay": ov, "label": l, "alert": al, "flash": 0.0, "cur": "", "until": 0.0,
		"spec": { "wolf_scale": float(fo.beast.get("modelScale", 1.0)), "model": String(fo.beast.get("model", "")) } }

func _pack_free(d: Dictionary) -> void:
	for k in ["node", "label", "alert"]:
		(d[k] as Node).queue_free()

func _pack_loop(d: Dictionary, name: String, speed: float) -> void:
	var ap: AnimationPlayer = d["anim"]
	speed *= breath(ap, name)
	if d["cur"] == name and ap.is_playing():
		ap.speed_scale = speed
		return
	_play(ap, name, 1.0, 0.18)
	ap.speed_scale = speed
	d["cur"] = name

func _pack_oneshot(d: Dictionary, name: String, speed := 1.0, hold := 0.9) -> void:
	var ap: AnimationPlayer = d["anim"]
	ap.speed_scale = 1.0
	_play(ap, name, speed, 0.06)
	d["cur"] = name
	var len: float = ap.get_animation(name).length if ap.has_animation(name) else 0.4
	d["until"] = _clock + len / speed * hold

## Where a foe stands: the locked one (-1) or one of the pack.
func _foe_pos(f: Fight, i: int) -> Vector2:
	if i >= 0 and i < f.foes.size():
		return (f.foes[i] as Foe).pos
	return f.w_pos

func _update_pack(f: Fight, dt: float) -> void:
	while _pack.size() > f.foes.size():
		_pack_free(_pack.pop_back())
	while _pack.size() < f.foes.size():
		_pack.append(_pack_make(f.foes[_pack.size()]))
	for i in _pack.size():
		var fo: Foe = f.foes[i]
		var d: Dictionary = _pack[i]
		var n: Node3D = d["node"]
		n.visible = show_wolf and fo.state != "absent"
		var l: Label3D = d["label"]
		var al: Label3D = d["alert"]
		if not n.visible:
			l.visible = false
			al.visible = false
			continue
		n.position = _v3(fo.pos)
		if fo.state == "down" and fo.timer > 1.4:
			n.position.y -= (fo.timer - 1.4) * 0.6
		n.rotation.y = _yaw(fo.facing)
		n.rotation.z = sin(_clock * 22.0) * 0.06 if fo.state == "stagger" else 0.0
		d["flash"] = maxf(0.0, float(d["flash"]) - dt * 7.0)
		var glow := 0.0
		if fo.state == "windup":
			glow = clampf(fo.timer / maxf(0.01, fo.duration), 0.0, 1.0)
		var overlay := Color(C_WINDUP, 0.6 * glow * glow)
		if fo.state == "stagger":
			overlay = Color(C_STAGGER, 0.25 + 0.15 * sin(_clock * 18.0))
		if float(d["flash"]) > 0.0:
			overlay = Color(C_HIT, 0.7 * float(d["flash"]))
		(d["overlay"] as StandardMaterial3D).albedo_color = overlay
		if _clock >= float(d["until"]):
			match fo.state:
				"prowl": _pack_loop(d, WOLF_ANIMS["walk"], 1.2)
				"approach": _pack_loop(d, WOLF_ANIMS["gallop"], 1.3)
				"windup": _pack_loop(d, WOLF_ANIMS["windup"], 0.6)
				"recover", "idle": _pack_loop(d, WOLF_ANIMS["idle"], 1.0)
				"stagger": _pack_loop(d, WOLF_ANIMS["stagger"], 0.3)
				"flinch": _pack_loop(d, WOLF_ANIMS["flinch"], 1.0)
		al.visible = fo.state == "windup"
		if al.visible:
			al.position = _v3(fo.pos, 2.3 + 0.15 * sin(_clock * 20.0))
			al.modulate = Color(C_WINDUP, 0.5 + 0.5 * glow)
		l.visible = fo.state != "down"
		l.position = _v3(fo.pos, 1.9)
		var state_text := ""
		match fo.state:
			"stagger": state_text = "  ·  STAGGERED"
			"windup": state_text = "  ·  %s" % String(fo.attack.get("name", "")).to_upper()
		l.text = "%s%s" % [String(fo.beast["name"]).to_upper(), state_text]

func _pack_event(f: Fight, e: Dictionary) -> void:
	var i := int(e.get("foe", -1))
	if String(e["type"]) == "retarget":
		_pack_swap(i)
		return
	while _pack.size() < f.foes.size():
		_pack.append(_pack_make(f.foes[_pack.size()]))
	if i < 0 or i >= _pack.size():
		return
	var d: Dictionary = _pack[i]
	var fo: Foe = f.foes[i]
	var at := _v3(fo.pos, 1.0)
	match String(e["type"]):
		"foe-spawn":
			dust(_v3(fo.pos, 0.1), 14)
		"foe-strike":
			_pack_oneshot(d, WOLF_ANIMS["Attack"], 1.0)
		"foe-hit":
			var heavy: bool = e.get("heavy", false)
			floater(at + Vector3(0, 0.8, 0), "%d" % int(e["damage"]), C_TEXT, 72 if heavy else 52)
			burst(at, C_GOLD if heavy else C_HIT, 24 if heavy else 10, 6.0 if heavy else 4.5)
			impact(at + _v3((f.p_pos - fo.pos).normalized() * 0.4), C_GOLD if heavy else C_HIT, 0.9 if heavy else 0.6)
			d["flash"] = 1.0
			if fo.state != "down":
				_pack_oneshot(d, WOLF_ANIMS["HitReact" if randf() < 0.5 else "HitReact2"], 1.0, 0.6)
		"foe-stagger":
			floater(at + Vector3(0, 1.0, 0), "BROKEN", C_STAGGER, 60, 1.1)
			_ring_wave(_v3(fo.pos), C_STAGGER, 2.4)
		"foe-down":
			_pack_oneshot(d, WOLF_ANIMS["Death"], 1.0, 99.0)
			floater(at + Vector3(0, 1.0, 0), "%s FALLS" % String(fo.beast["name"]).to_upper(), C_GOLD, 52, 1.5)
			_ring_wave(_v3(fo.pos), C_GOLD, 2.5)
			dust(_v3(fo.pos, 0.1), 24)

## The lock moved to one of the pack: the fight swapped their data, so the bodies swap too.
func _pack_swap(i: int) -> void:
	if i < 0 or i >= _pack.size() or _foe_spec.has("body"):
		return
	var d: Dictionary = _pack[i]
	var mine := { "node": _wolf, "anim": _w_anim, "meshes": _w_meshes, "overlay": _overlay_wolf, "label": d["label"], "alert": d["alert"],
		"flash": _wolf_flash, "cur": _w_current, "until": _w_oneshot_until, "spec": _foe_spec }
	_wolf = d["node"]
	_w_anim = d["anim"]
	_w_meshes = d["meshes"]
	_overlay_wolf = d["overlay"]
	_wolf_flash = float(d["flash"])
	_w_current = String(d["cur"])
	_w_oneshot_until = float(d["until"])
	_foe_spec = d["spec"]
	_w_anims = WOLF_ANIMS
	_pack[i] = mine

func set_allies(specs: Array) -> void:
	for a in _ally_nodes:
		(a["node"] as Node).queue_free()
	_ally_nodes.clear()
	for sp in specs:
		var n: Node3D = load(_person_model(sp.get("body", "Knight"))).instantiate()
		add_child(n)
		toonify(n)
		dress(n, sp["look"] if not sp.get("look", {}).is_empty() else look_for(String(sp.get("name", ""))))
		var skel: Skeleton3D = n.find_child("Skeleton3D", true, false)
		var w: Dictionary = Data.by_id(Data.weapons, sp.get("weapon", "saber"))
		_attach(skel, "handslot.r", _weapon_model(w["model"]))
		if w.has("offhand"):
			_attach(skel, "handslot.l", _weapon_model(w["offhand"]))
		for m in n.find_children("*", "MeshInstance3D", true, false):
			m.material_overlay = _ink("people")
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		for loop in ["Idle", "Running_A"]:
			if ap.has_animation(loop):
				ap.get_animation(loop).loop_mode = Animation.LOOP_LINEAR
		ap.play("Idle")
		ap.speed_scale = breath(ap, "Idle")
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
		# Never between the camera and the hero: anyone nearer the camera than the hero is fades out.
		var cam_to_hero := camera.global_position.distance_to(_player.global_position + Vector3(0, 1.0, 0))
		n.visible = camera.global_position.distance_to(n.global_position + Vector3(0, 1.0, 0)) > cam_to_hero * 0.7
		var ap: AnimationPlayer = a["anim"]
		if _clock < float(a["until"]):
			continue
		var v := 0.0
		if a.has("last_pos"):
			v = (n.position - (a["last_pos"] as Vector3)).length() / maxf(dt, 1e-4)
		a["last_pos"] = n.position
		var want := "Death_A" if al["down"] else (gait_for(v) if al["moving"] else "Idle")
		if want != a["cur"]:
			a["cur"] = want
			ap.play(want, 0.15)
			if want == "Death_A":
				a["until"] = _clock + 99.0
		if al["moving"] and not al["down"]:
			ap.speed_scale = stride_scale(want, v)
		elif not al["down"]:
			ap.speed_scale = breath(ap, want)

func _ally_event(f: Fight, e: Dictionary) -> void:
	var i := int(e.get("who", -1))
	if i < 0 or i >= _ally_nodes.size() or i >= f.allies.size():
		return
	var a: Dictionary = _ally_nodes[i]
	var ap: AnimationPlayer = a["anim"]
	var at := _v3(f.allies[i]["pos"], 1.2)
	var col: Color = SHAPE_COLORS.get(f.allies[i].get("shape", "anchor"), Color(0.8, 0.9, 1.0))
	# Until the voices exist, a classmate's call shows as words over their head.
	var calls: Dictionary = Data.academy["cohort"].get("fighting", {}).get("calls", {})
	var call_kind: String = { "ally-windup": "technique" if e.get("technique", false) else "", "ally-pattern": "pattern", "ally-parry": "parry", "ally-retreat": "retreat", "ally-down": "down" }.get(String(e["type"]), "")
	if call_kind != "" and calls.has(call_kind) and randf() < 0.6:
		var lines: Array = calls[call_kind]
		floater(at + Vector3(0, 1.3, 0), "\"%s\"" % String(lines[randi() % lines.size()]), Color(0.9, 0.9, 0.85), 34, 1.3, 0.5)
	match String(e["type"]):
		"ally-windup":
			ap.play("2H_Melee_Attack_Chop" if e.get("technique", false) else "1H_Melee_Attack_Slice_Horizontal", 0.05)
			ap.speed_scale = 0.6
			a["cur"] = "windup"
			a["until"] = _clock + 0.6
			if e.get("technique", false):
				_ring_wave(_v3(f.allies[i]["pos"]), Color(col, 0.6), 1.6)
		"ally-hit":
			if a["cur"] != "windup":
				ap.play("1H_Melee_Attack_Slice_Horizontal", 0.05)
			ap.speed_scale = 1.6
			a["cur"] = "attack"
			a["until"] = _clock + 0.4
			var fp := _foe_pos(f, int(e.get("foe", -1)))
			var heavy: bool = e.get("heavy", false)
			var patt: bool = e.get("pattern", false)
			impact(_v3(fp, 0.9), C_GOLD if patt else (col if heavy else Color(0.8, 0.9, 1.0)), 1.2 if patt else (0.8 if heavy else 0.5))
			if heavy or patt:
				burst(_v3(fp, 0.9), C_GOLD if patt else col, 30 if patt else 14, 7.0 if patt else 5.0)
			floater(_v3(fp, 1.8) + Vector3(-0.4, 0.3, 0), "%d" % int(e["damage"]), C_GOLD if patt else (col.lightened(0.3) if heavy else Color(0.75, 0.85, 1.0)), 64 if patt else (48 if heavy else 40), 0.8)
		"ally-pattern":
			floater(at + Vector3(0, 1.0, 0), "%s  ·  %s" % [String(f.allies[i]["name"]).to_upper(), String(e["name"]).to_upper()], C_GOLD, 52, 1.4)
			_ring_wave(_v3(f.allies[i]["pos"]), C_GOLD, 3.5)
			burst(at, C_GOLD, 40, 6.0)
			ap.play("2H_Melee_Attack_Spin", 0.05)
			a["cur"] = "pattern"
			a["until"] = _clock + 1.1
		"ally-parry":
			ap.play("Block_Hit", 0.05)
			a["cur"] = "parry"
			a["until"] = _clock + 0.5
			floater(at + Vector3(0, 0.5, 0), "PARRY", C_GUARD, 56, 0.9)
			burst(at, C_GUARD, 24, 6.0)
			impact(at, C_GUARD, 0.9)
		"ally-block":
			ap.play("Block_Hit", 0.05)
			a["cur"] = "block"
			a["until"] = _clock + 0.4
			floater(at + Vector3(0, 0.4, 0), "BLOCKED", C_GUARD, 40, 0.7)
		"ally-retreat":
			floater(at + Vector3(0, 0.8, 0), "%s FALLS BACK" % String(f.allies[i]["name"]).to_upper(), C_WINDUP, 44, 1.2)
		"ally-shot":
			ap.play("1H_Ranged_Shoot", 0.05)
			a["cur"] = "shot"
			a["until"] = _clock + 0.4
			_tracer(_v3(e["from"], 1.3), _v3(e["to"], 1.0), e["hit"])
		"ally-miss":
			pass
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

## A thing to find, lying in the place: a small keepsake with a glow round it. null hides it.
var _marker: Node3D = null
func set_marker(at: Variant) -> void:
	if _marker:
		_marker.queue_free()
		_marker = null
	if at == null:
		return
	_marker = Node3D.new()
	var m := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.18, 0.12, 0.14)
	m.mesh = bm
	m.material_override = _mat(Color(0.75, 0.6, 0.35), 0.6)
	m.position = Vector3(0, 0.1, 0)
	_marker.add_child(m)
	var halo := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(1.2, 1.2)
	halo.mesh = q
	var gm := _shader_mat(GLOW)
	gm.set_shader_parameter("tint", Color(1.0, 0.85, 0.5))
	gm.set_shader_parameter("strength", 0.9)
	halo.material_override = gm
	halo.position = Vector3(0, 0.35, 0)
	_marker.add_child(halo)
	_marker.position = _v3(at, 0.0)
	add_child(_marker)

## Someone standing in the place: a body, a weapon, their name and what they are over the head.
## `partner` is what a person is beyond their look, where they have a genius of their own: their
## Shape, blood, city and genius, so they wear its echo and it stands by them.
func add_figure(body: String, at: Vector2, facing: float, title: String, sub: String, weapon := "", tint := Color(0, 0, 0, 0), look := {}, partner := {}) -> Dictionary:
	var n: Node3D = load(_person_model(body)).instantiate()
	_place_root.add_child(n)
	toonify(n)
	dress(n, look if not look.is_empty() else look_for(title), partner)
	if partner.get("genius", {}) is Dictionary and not partner.get("genius", {}).is_empty():
		_figure_genius(n, partner["genius"], _shape_color(String(partner.get("shape", "anchor"))))
	var skel: Skeleton3D = n.find_child("Skeleton3D", true, false)
	if weapon != "":
		var w: Dictionary = Data.by_id(Data.weapons, weapon)
		_attach(skel, "handslot.r", _weapon_model(w["model"]))
		if w.has("offhand"):
			_attach(skel, "handslot.l", _weapon_model(w["offhand"]))
	var over := _mat(C_HIT, 0.0, true, 0.0)
	over.albedo_color = tint
	over.next_pass = _ink("people")
	for m in n.find_children("*", "MeshInstance3D", true, false):
		m.material_overlay = over
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap.has_animation("Idle"):
		ap.get_animation("Idle").loop_mode = Animation.LOOP_LINEAR
		ap.play("Idle", 0.0, breath(ap, "Idle") * randf_range(0.9, 1.1))
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

func _furnish_hearth(kit := false) -> void:
	# The bowl: a broad stone basin on a short column, with the fire in it.
	if not kit or _kit_piece("rite_bowl", BOWL) == null:
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
	bowl_light.light_color = Style.light("fire")
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
	if kit:
		return
	for b in [[-4.0, -9.4, 0.0], [4.0, -9.4, 0.0]]:
		_piece("banner_patternA_red", Vector3(b[0], 0.6, b[1]), b[2])
	for c in [Vector2(-6.5, -6.5), Vector2(6.5, -6.5)]:
		_piece("pillar_decorated", Vector3(c.x, 0, c.y), 0.0)
		obstacles.append(Vector3(c.x, c.y, 0.9))

## How dark the hall falls while the bowl reads (0: as lit; 1: only the bowl).
func dim(k: float) -> void:
	for t in _torches:
		(t as OmniLight3D).light_energy = lerpf(1.5, 0.15, k)
	_env.ambient_light_energy = lerpf(_ambient_lit if _ambient_lit > 0.0 else 0.34, 0.08, k)
	_torch_dim = k

var _torch_dim := 0.0
var _ambient_lit := 0.0     # the place's own ambient, for the rite to dim from and return to

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
	# An art body takes the cel bands like everything else that lives (the placeholders keep
	# their shadow shader: toonify only turns standard materials).
	if gb.uses_art:
		toonify(gb)
	for m in gb.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		if mi.material_overlay:
			mi.material_overlay.next_pass = _ink("genii")
		else:
			mi.material_overlay = _ink("genii")
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

## A move of the genius's, shown: its name over where it lands, and a mark of what it does.
func _genius_move_shown(f: Fight, e: Dictionary, P: Vector3, W: Vector3) -> void:
	var at := _v3(e.get("at", f.w_pos), 0.0)
	var hi := _g_tint.lightened(0.35)
	floater(at + Vector3(0, 1.7, 0), String(e["name"]).to_upper(), hi, 44, 1.2)
	match String(e["move"]):
		"hamstring":
			burst(at + Vector3(0, 0.3, 0), hi, 18, 3.0)
			_g_dart_at = at + Vector3(0, 0.3, 0)
			_g_dart_until = _clock + 0.35
		"stoop":
			# from above, hard
			_g_form_pos = at + Vector3(0, 4.5, 0)
			_g_dart_at = at + Vector3(0, 0.8, 0)
			_g_dart_until = _clock + 0.4
			impact(at + Vector3(0, 1.0, 0), _g_tint, 1.6)
			_ring_wave(at, _g_tint, 2.2)
		"shot":
			burst(_v3(e.get("from", f.g_pos), 1.0), hi, 8, 6.0)
			impact(at + Vector3(0, 1.0, 0), _g_tint, 1.0)
		"debt":
			_ring_wave(at, Color(0.8, 0.25, 0.3), 1.4)
			burst(at + Vector3(0, 1.8, 0), Color(0.9, 0.3, 0.35), 14, 2.0)
		"debt-paid":
			impact(at + Vector3(0, 1.0, 0), Color(0.9, 0.3, 0.35), 1.6)
			_ring_wave(at, Color(0.9, 0.3, 0.35), 2.6)
		"lay":
			_ring_wave(at, _g_tint, float(e.get("radius", 2.6)))
		"light":
			_ring_wave(_v3(f.p_pos), Color(1.0, 0.9, 0.6), 4.0)
			genius_react("stance")
		"call":
			_ring_wave(_v3(f.g_pos), hi, 1.6)
			genius_react("cue")
		"nip":
			burst(at + Vector3(0, 0.4, 0), hi, 6, 2.0)

var _g_hold_ring: MeshInstance3D = null
var _g_door_ring: MeshInstance3D = null
var _g_door_r := 0.0
var _g_zone_disc: MeshInstance3D = null
var _g_lit_light: OmniLight3D = null

## What the genius has put on the ground, drawn: a ring round the ground it holds, a pool
## where it has laid itself down, and a light over its partner while the ground is lit.
func _genius_ground(f: Fight) -> void:
	var up := f.genius != null and not f.genius.fallen
	var holding := up and f.g_order == "hold" and f.g_hold_at != Vector2.INF
	if holding and _g_hold_ring == null:
		_g_hold_ring = MeshInstance3D.new()
		var tm := TorusMesh.new()
		var hr := float(f._order("hold")["hold"]["radius"])
		tm.inner_radius = hr - 0.07
		tm.outer_radius = hr
		tm.rings = 64
		tm.ring_segments = 6
		_g_hold_ring.mesh = tm
		_g_hold_ring.material_override = _mat(_g_tint, 1.6, true, 0.55)
		_g_hold_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_g_hold_ring)
	if _g_hold_ring:
		_g_hold_ring.visible = holding
		if holding:
			_g_hold_ring.position = _v3(f.g_hold_at, 0.07)
			_g_hold_ring.scale = Vector3.ONE * (1.0 + 0.015 * sin(_clock * 2.0))
	# a lamp set down lights its circle the way a genius laid on the ground does its own
	var lamped := up and not f.g_lamp.is_empty()
	var zoned := (up and not f.g_zone.is_empty()) or lamped
	if zoned and _g_zone_disc == null:
		_g_zone_disc = MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(2.0, 2.0)
		_g_zone_disc.mesh = pm
		var gm := _shader_mat(GLOW)
		gm.set_shader_parameter("billboard", false)
		gm.set_shader_parameter("falloff", 1.1)
		_g_zone_disc.material_override = gm
		_g_zone_disc.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_g_zone_disc)
	if _g_zone_disc:
		_g_zone_disc.visible = zoned
		if zoned:
			var zone: Dictionary = f.g_lamp if lamped else f.g_zone
			var zr := minf(float(zone["radius"]), 14.0)
			var zc: Color = Style.light("lamp", "color") if lamped else { "burn": Color(1.0, 0.45, 0.15), "chill": Style.shape_color("cast"), "dark": Color(0.35, 0.2, 0.55) }.get(String(f.g_zone["effect"]), _g_tint)
			_g_zone_disc.position = _v3(zone["at"], 0.09)
			_g_zone_disc.scale = Vector3(zr, 1, zr)
			var zm := _g_zone_disc.material_override as ShaderMaterial
			zm.set_shader_parameter("tint", zc)
			zm.set_shader_parameter("strength", 0.55 + 0.12 * sin(_clock * 5.0))
	# a shield standing as a door: a ring round the ground it covers
	var doored := up and not f.g_door.is_empty()
	if doored and (_g_door_ring == null or not is_equal_approx(_g_door_r, float(f.g_door["radius"]))):
		if _g_door_ring:
			_g_door_ring.queue_free()
		_g_door_r = float(f.g_door["radius"])
		_g_door_ring = MeshInstance3D.new()
		var dm := TorusMesh.new()
		dm.inner_radius = _g_door_r - 0.09
		dm.outer_radius = _g_door_r
		dm.rings = 64
		dm.ring_segments = 6
		_g_door_ring.mesh = dm
		_g_door_ring.material_override = _mat(_g_tint.lightened(0.2), 1.8, true, 0.6)
		_g_door_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_g_door_ring)
	if _g_door_ring:
		_g_door_ring.visible = doored
		if doored:
			_g_door_ring.position = _v3(f.g_door["at"], 0.08)
	var lit := (up and f.now < f.g_lit_until) or (lamped and f.p_pos.distance_to(f.g_lamp["at"]) <= float(f.g_lamp["radius"]))
	if lit and _g_lit_light == null:
		_g_lit_light = OmniLight3D.new()
		_g_lit_light.light_color = Style.light("lamp").lerp(Color.WHITE, 0.35)
		_g_lit_light.omni_range = 9.0
		_g_lit_light.omni_attenuation = 1.2
		add_child(_g_lit_light)
	if _g_lit_light:
		_g_lit_light.light_energy = 1.8 if lit else 0.0
		_g_lit_light.position = _v3(f.p_pos, 2.6)

## The First Form follows: fliers and fey and flames at the shoulder, walkers at the heel. On
## Hunt it is at the foe; on Hold it stands on its ground; a flier that has stooped climbs.
## Where a genius's own model says it is taken hold of (grip), worn (wear) or carried (carry):
## an empty of that name in its model, found once for each body.
var _held_body: GeniusBody = null
var _held_nodes := {}
func _held_at(what: String) -> Node3D:
	if _g_body == null or not is_instance_valid(_g_body) or _g_body._model == null:
		return null
	if _held_body != _g_body:
		_held_body = _g_body
		_held_nodes = {}
	if not _held_nodes.has(what):
		# a piece made for wearing is its own place: it is made where it is worn, and as it lies there
		_held_nodes[what] = _g_body.worn_piece if what == "wear" and _g_body.worn_piece else _g_body._model.find_child(what, true, false)
	return _held_nodes[what] as Node3D

func _update_form(f: Fight, dt: float) -> void:
	_genius.visible = false
	_g_trail.emitting = false
	_genius_ground(f)
	# A weapon genius in the hand is the weapon: it sits where the weapon put away sat, at the
	# length a hand holds (data/genius-types.json, weapon.bases.*.held), and that one is not drawn.
	if _sword:
		_sword.visible = not f.g_in_hand
	if f.g_in_hand and _sword and _g_form:
		# length: how long it is in the hand, in metres. grip: how far along that length, from its
		# foot, the hand takes it. flip: its foot is its point (a blade that floats point down).
		var held: Dictionary = f.g_weapon.get("held", {})
		var long := float(held.get("length", 1.0))
		var k := long / maxf(0.2, _g_body.stands if _g_body else 1.0)
		var slot := _sword.global_transform.basis.orthonormalized()
		var hb := slot
		var at := _sword.global_position - slot.y * long * float(held.get("grip", 0.0))
		if held.get("upright", false):
			# a thing held level (a gun): upright, turned the way its partner faces
			hb = Basis(Vector3.UP, _yaw(f.p_facing))
			at = _sword.global_position - Vector3.UP * long * float(held.get("grip", 0.0))
		elif held.get("flip", false):
			hb = slot * Basis(Vector3.RIGHT, PI)
			at = _sword.global_position + slot.y * long * float(held.get("grip", 0.0))
		_g_form.global_transform = Transform3D(hb * Basis.from_scale(Vector3.ONE * k), at)
		# A weapon with a model of its own says where the hand closes on it (an empty named
		# grip, turned as a weapon is turned in the hand): it is seated there, whatever its form.
		# Such a model is made in the weapon kit's frame and at its size (docs/genius-lines.md,
		# "The weapons"): the size it floats at is undone, and a gun or a bow takes the quarter
		# turn the kit's own take in the hand.
		var grip := _held_at("grip")
		if grip:
			var g := _g_body._local_xf(grip)
			var made := 1.0 / maxf(0.001, _g_body._model.scale.y)
			var quarter := Basis(Vector3.UP, PI / 2.0) if String(f.g_weapon.get("style", "")) in ["gun", "bow"] else Basis.IDENTITY
			var fb := slot * quarter * g.basis.orthonormalized().inverse() * Basis.from_scale(Vector3.ONE * made)
			_g_form.global_transform = Transform3D(fb, _sword.global_position - fb * g.origin)
		_g_form_pos = _sword.global_position
		if _g_body:
			_g_body.move_at(0.0)
		return
	# A worn or carried genius sits on its partner where its kind is worn (data/genius-types.json,
	# mounts), by the empty its own model has for that, at the size it was made.
	if _offhand and is_instance_valid(_offhand):
		_offhand.visible = true
	if f.g_type in ["defense", "ritual"] and not genius_down and _p_skel and _g_body and is_instance_valid(_g_body) and _g_body._model:
		var mount: Dictionary = Data.genius_types().get("mounts", {}).get(String(f.g_item.get("worn", "")), {})
		var held: Node3D = _held_at(String(mount["by"])) if not mount.is_empty() else null
		var bone := _p_skel.find_bone(String(mount.get("bone", ""))) if held else -1
		if held and bone >= 0:
			_g_body.set_worn(true)
			# a shield that is its genius is the shield on that arm: the carried one is not drawn
			if _offhand and is_instance_valid(_offhand) and String(mount.get("hides", "")) == "offhand":
				_offhand.visible = false
			var bt := _p_skel.global_transform * _p_skel.get_bone_global_pose(bone)
			var at: Array = mount["at"]
			var turn: Array = mount["turn"]
			# plumb: it hangs upright from its place whatever the bone does, facing as its partner faces
			var frame := Basis(Vector3.UP, _yaw(f.p_facing)) if mount.get("plumb", false) else bt.basis.orthonormalized()
			var place := Transform3D(frame, bt.origin) * Transform3D(Basis.from_euler(Vector3(deg_to_rad(turn[0]), deg_to_rad(turn[1]), deg_to_rad(turn[2]))), Vector3(at[0], at[1], at[2]))
			var g := _g_body._local_xf(held)
			var k := float(mount["scale"]) / maxf(0.001, _g_body._model.scale.y)
			# a form that says how tall it is in the hand (held, in its body) is brought to that
			var tall := float(Data.form(_g_body.own_body).get("body", {}).get("held", 0.0)) if _g_body.own_body != "" else 0.0
			var crown := _held_at("ref_top")
			if tall > 0.0 and crown:
				k = float(mount["scale"]) * tall / maxf(0.001, _g_body._local_xf(crown).origin.y)
			var fb := place.basis * g.basis.orthonormalized().inverse() * Basis.from_scale(Vector3.ONE * k)
			_g_form.global_transform = Transform3D(fb, place.origin - fb * g.origin)
			_g_form_pos = place.origin
			_g_body.move_at(0.0)
			return
	if not _g_form.scale.is_equal_approx(Vector3.ONE):
		_g_form.scale = Vector3.ONE
	if _g_body and is_instance_valid(_g_body):
		_g_body.set_worn(false)
	var walker := _g_body != null and _g_body.walks()
	var side := Vector2.from_angle(f.p_facing + (2.2 if walker else 1.9))
	var want := _v3(f.p_pos + side * (1.1 if walker else 0.8), 0.0 if walker else 1.5 + 0.08 * sin(_clock * 2.4))
	var posted := f.genius != null and not genius_down and f.g_order in ["hunt", "hold"] and f.g_kind != "object" and f.w_state != "absent"
	if posted:
		var lift := 0.0 if walker else (3.4 if f.now < f.g_climb_until else 1.3 + 0.08 * sin(_clock * 2.4))
		want = _v3(f.g_pos, lift)
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
	elif posted and f.w_state not in ["down", "absent"]:
		# at its post or on the foe, it faces what it watches
		_g_form_facing = lerp_angle(_g_form_facing, (f.w_pos - f.g_pos).angle(), 1.0 - exp(-dt * 5.0))
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
