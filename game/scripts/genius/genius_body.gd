## A genius, assembled: a body for its silhouette and a part for each feature, hung on named
## sockets (data/genius-bodies.json). Real art drops in by name and replaces the placeholders:
##   game/assets/genius/bodies/<silhouette>.glb   (with empties named socket_<name>)
##   game/assets/genius/parts/<feature>.glb
## Until then, placeholder bodies borrow a rigged model (four-legged and humanoid kinds) or are
## built from shapes, in shadow lit at the edges by the partner's Shape colour.
## A genius with a look (genius_look.gd, data/genius-looks.json) is painted as itself: its coat
## on the body's coat materials, its markings on the materials named mark_<region>, its build
## on the body's blend shapes (or the whole body, where it has none), its light in its own
## style, and its keepsake hung where the body has a place for one.
class_name GeniusBody
extends Node3D

const BODY_DIR := "res://game/assets/genius/bodies/%s.glb"
const PART_DIR := "res://game/assets/genius/parts/%s.glb"
const KEEP_DIR := "res://game/assets/genius/keepsakes/%s.glb"
const TRAP_DIR := "res://game/assets/genius/trappings/%s.glb"

const SILHOUETTE := """
shader_type spatial;
// A genius before there is art for it: a body of shadow lit at the edges in its colour, like a
// figure seen against the fire. Surface features tint it and lay bands across it.
render_mode cull_back;
uniform vec4 glow : source_color = vec4(1.0, 0.7, 0.3, 1.0);
uniform vec4 tint : source_color = vec4(0.03, 0.025, 0.03, 1.0);
uniform float rim_k = 1.0;
uniform float bands = 0.0;
uniform float strength = 1.0;
varying vec3 local_pos;
void vertex() { local_pos = VERTEX; }
void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.4);
	float band = bands > 0.0 ? step(0.5, fract(local_pos.y * bands * 4.0)) * 0.35 : 0.0;
	ALBEDO = tint.rgb * (1.0 + band);
	EMISSION = glow.rgb * (rim * 3.2 * rim_k + 0.25) * strength;
	ROUGHNESS = 0.85;
}
"""

const RIM := """
shader_type spatial;
// Over an art body: the partner's Shape colour at the edges, as the placeholder shadow has.
render_mode blend_add, unshaded, cull_back, depth_draw_never;
uniform vec4 glow : source_color = vec4(1.0, 0.7, 0.3, 1.0);
uniform float strength = 1.0;
uniform float molt = 0.0;      // 0 to 1: the molt lines, as a Reading nears
uniform float molt_scale = 1.0;
varying vec3 lp;
void vertex() { lp = VERTEX * length(MODEL_MATRIX[0].xyz); }   // the body's own space, in metres
// Thin seams of light across the body, where it will split: a folded field of sines, its
// zero crossings drawn as lines that widen and brighten with the molt.
float seams(vec3 p) {
	float v = sin(p.x * 9.0 + sin(p.y * 7.0) * 1.7) + sin(p.y * 11.0 + sin(p.z * 6.0) * 1.3) + sin(p.z * 8.0 + sin(p.x * 5.0) * 1.9);
	return smoothstep(0.08 + 0.2 * molt, 0.0, abs(v));
}
void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.6);
	vec3 col = glow.rgb * rim * 1.6 * strength;
	if (molt > 0.0) {
		float breathe = 0.75 + 0.25 * sin(TIME * 2.2 + lp.y * 5.0);
		col += mix(glow.rgb, vec3(1.0), 0.3) * seams(lp * molt_scale) * molt * breathe * 3.2;
	}
	ALBEDO = col;
}
"""
static var _rim_shader: Shader

var info: Dictionary = {}
var color := Color.WHITE
var kind := ""
var hover := false
var anim: AnimationPlayer = null
var anim_names: Dictionary = {}
var sockets: Dictionary = {}       # name -> Node3D
var uses_art := false              # the body came from an art file, not a placeholder
var nearness := 0.0                # how near its next Reading is (Genius.readiness), 0 to 1
var molt := 0.0                    # the molt lines showing for it, 0 to 1
var stands := 0.6                  # how tall it stands now, in metres
var age := "grown"                 # young, half-grown, grown, prime, great, apex (by instar)
var lines := 0.0                   # the steady light along its body at the later instars, 0 to 1
var mantle: Node3D = null          # the blades of light behind a great one's head
var parts_from_art: Array = []     # features whose parts came from art files
var look: Dictionary = {}          # how this one looks, resolved (GeniusLook.resolve); {} for none
var keepsake := ""                 # the keepsake it wears, if its body has a place for it
var painted := 0                   # how many surfaces took the coat's colours
var shapes_set: Dictionary = {}    # blend shape -> value, as set on its meshes
var _field_surfaces: Array = []    # [mesh, surface, energy]: the field's surfaces, for a light that pulses
var _rims: Array = []              # the edge-light laid over its art, so a portrait can turn it down
var _glow := 1.0
var _mat: ShaderMaterial
var _model: Node3D
var _wings: Array = []
var _spinners: Array = []
var _t := 0.0

static var _shader: Shader

## Build a genius from what the Reading made: { silhouette, features, expression, form }.
static func build(genius_info: Dictionary, shape_color: Color, instar := 1) -> GeniusBody:
	var b := GeniusBody.new()
	b.name = "Genius"
	b.info = genius_info
	b.color = shape_color
	b._assemble(instar)
	return b

func _assemble(instar: int) -> void:
	var cfg: Dictionary = Data.genius_bodies()
	var sil: String = info.get("silhouette", "beast-runner")
	var spec: Dictionary = cfg["silhouettes"].get(sil, { "kind": "aspect", "build": "flame" })
	kind = spec["kind"]
	hover = spec.get("hover", false)
	if not _shader:
		_shader = Shader.new()
		_shader.code = SILHOUETTE
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	_mat.set_shader_parameter("glow", color)
	_apply_surfaces(cfg)
	_glow = GeniusLook.glow(int(info.get("instar", instar)))
	var born: Dictionary = info.get("look", {})
	if not born.is_empty():
		look = GeniusLook.resolve(born, String(info.get("form", "")), sil, int(info.get("instar", instar)))
		_glow *= float(look["eyes"]["energy"])
	if ResourceLoader.exists(BODY_DIR % sil):
		_model = load(BODY_DIR % sil).instantiate()
		add_child(_model)
		uses_art = true
		_art_sockets(_model)
		anim = _model.find_child("AnimationPlayer", true, false)
		if anim:
			anim_names = _clips(cfg["kinds"].get(kind, {}).get("anim", {}))
		_adopt_art(_model)
	else:
		_placeholder_body(cfg["kinds"][kind], spec)
	var sc: Array = spec.get("scale", [1, 1, 1])
	var proportions := Vector3(sc[0], sc[1], sc[2])
	if uses_art:
		# An art body carries its own proportions: the data says only how tall it stands
		# against its instar's size (an otter stands half as tall as a wolf).
		proportions = Vector3.ONE * float(spec.get("artSize", 1.0))
	proportions *= _apply_proportions()
	# It grows between Readings: part of the way to the next instar's size as the Reading nears.
	var prog: Dictionary = Data.genius().get("progression", {})
	nearness = float(info["ready"]) if info.has("ready") else (Genius.from_dict(info).readiness() if info.has("history") and info.has("tally") else 0.0)
	var sizes: Dictionary = Data.genius()["size"]
	var h0 := float(sizes.get(str(maxi(1, instar)), 0.6))
	var h1 := float(sizes.get(str(mini(6, maxi(1, instar) + 1)), h0))
	stands = h0 + (h1 - h0) * float(prog.get("growth", 0.0)) * nearness
	_fit_height(stands, proportions)
	# Parts, on the sockets for their slots.
	var feats: Array = info.get("features", [])
	var slot_count := {}
	for f in feats:
		var slot := _slot_of(f)
		# A surface changes the skin and hangs nothing, unless it has a part and a place of its
		# own (the Seed-marks: a grip to hold it by, a ledger at its chest).
		if slot == "surface" and not (ResourceLoader.exists(PART_DIR % f) and cfg.get("featureSockets", {}).has(f)):
			continue
		# An art body may carry a feature in its own design (the stag its antlers): no part hangs.
		if uses_art and (spec.get("carries", []) as Array).has(f):
			continue
		var socks: Array = cfg["slotSockets"].get(slot, ["socket_body"])
		var i: int = slot_count.get(slot, 0)
		slot_count[slot] = i + 1
		if ResourceLoader.exists(PART_DIR % f):
			# A part made for a paired slot (limbs, arms) goes on every socket the body has for it;
			# some features name their own sockets (a beak at the mouth, hands at the wrists).
			var named: Array = cfg.get("featureSockets", {}).get(f, []).filter(func(sn): return sockets.has(sn))
			var targets: Array = named if not named.is_empty() else (socks.filter(func(sn): return sockets.has(sn)) if socks.size() > 1 else [socks[0]])
			if targets.is_empty():
				targets = [socks[i % socks.size()]]
			for sn in targets:
				var art: Node3D = load(PART_DIR % f).instantiate()
				_socket(sn).add_child(art)
				# Parts of a pair are made for the left; the right wears the mirror.
				if is_right(String(sn)):
					art.scale.x = -1.0
				_adopt_art(art)
			parts_from_art.append(f)
		else:
			_placeholder_part(f, slot, socks)
	_wear_keepsake()
	_wear_trapping()
	# Its age shapes it: the young of its kind at the First Form, great at the Fifth.
	age = String(prog.get("ages", {}).get(str(clampi(instar, 1, 6)), {}).get("id", "grown"))
	_apply_age(cfg.get("ages", {}).get(kind, {}).get(age, {}))
	# What the later instars add: steady lines of light, a mantle, the ground lit under it.
	var pres: Dictionary = prog.get("presence", {}).get(str(clampi(instar, 1, 6)), {})
	lines = float(pres.get("lines", 0.0))
	if int(pres.get("mantle", 0)) > 0:
		_mantle(int(pres["mantle"]))
	if float(pres.get("ground", 0.0)) > 0.0:
		var gl := OmniLight3D.new()
		gl.name = "GroundLight"
		gl.light_color = color
		gl.light_energy = float(pres["ground"])
		gl.omni_range = stands * 2.2
		gl.omni_attenuation = 1.6
		gl.position = Vector3(0, stands * 0.25, 0)
		add_child(gl)
	# Near the Reading it molts: seams of light where the body will split.
	var mfrom := float(prog.get("molt", {}).get("from", 0.55))
	var molting := (nearness - mfrom) / maxf(0.01, 1.0 - mfrom) * float(prog.get("molt", {}).get("strength", 1.0)) if nearness > mfrom else 0.0
	if maxf(molting, lines) > 0.0:
		set_molt(maxf(molting, lines))
	if anim and anim_names.has("idle") and anim.has_animation(anim_names["idle"]):
		for k in anim_names:
			if anim.has_animation(anim_names[k]):
				anim.get_animation(anim_names[k]).loop_mode = Animation.LOOP_LINEAR
		anim.play(anim_names["idle"])

## Art follows the bible's conventions: materials named field* glow in the partner's Shape
## colour; wing_l and wing_r beat.
func _adopt_art(n: Node) -> void:
	if not _rim_shader:
		_rim_shader = Shader.new()
		_rim_shader.code = RIM
	var rim := ShaderMaterial.new()
	rim.shader = _rim_shader
	rim.set_shader_parameter("glow", color)
	_rims.append(rim)
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		mi.material_overlay = rim
		for i in mi.get_surface_override_material_count():
			var mat: Material = mi.mesh.surface_get_material(i)
			if mat and mat.resource_name.begins_with("field") and mat is StandardMaterial3D:
				var t := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				t.emission_enabled = true
				t.emission = color
				t.emission_energy_multiplier = 1.8 * _glow
				t.albedo_color = color.darkened(0.7)
				mi.set_surface_override_material(i, t)
				_field_surfaces.append([mi, i, 1.8 * _glow])
			elif mat and mat is StandardMaterial3D and look.get("colors", {}).has(String(mat.resource_name)):
				# its own coat, and its markings: shown in the marking's colour, or hidden in the coat's
				var c := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				c.albedo_color = look["colors"][String(mat.resource_name)]
				mi.set_surface_override_material(i, c)
				painted += 1
	# The character's left is +X: the left wing rises with a positive turn about the way it faces.
	for side in [["wing_l", 1.0], ["wing_r", -1.0]]:
		var w: Node = n.find_child(side[0], true, false)
		# A wing that rides a bone is a mesh under its attachment: the mesh is what beats.
		if w is BoneAttachment3D and w.get_child_count() > 0:
			w = w.get_child(0)
		if w is Node3D:
			var w3 := w as Node3D
			w3.set_meta("wing", side[1])
			w3.set_meta("wing_rest", w3.transform)
			# the axis it beats about: the model's forward, seen from the wing's own frame
			w3.set_meta("wing_axis", (_rest_xf(w3, n).basis.orthonormalized().inverse() * Vector3(0, 0, 1)).normalized())
			_wings.append(w3)

## Its build: each proportion on the body's blend shapes where the art carries them (lean and
## heavy, a longer tail); where it does not, the whole body a little broader or narrower.
## Returns that scale.
func _apply_proportions() -> Vector3:
	var scale_by := Vector3.ONE
	if look.is_empty() or _model == null:
		return scale_by
	var meshes := _model.find_children("*", "MeshInstance3D", true, false)
	for p in Data.genius_looks()["proportions"]:
		var v := clampf(float(look["proportions"].get(p["id"], 0.0)), -1.0, 1.0)
		var shape_name := String(p["shapes"][0] if v < 0.0 else p["shapes"][1])
		var found := false
		for m in meshes:
			var mi := m as MeshInstance3D
			for sh in p["shapes"]:
				if sh != "" and mi.find_blend_shape_by_name(sh) >= 0:
					found = true
					mi.set_blend_shape_value(mi.find_blend_shape_by_name(sh), absf(v) if sh == shape_name else 0.0)
		if found:
			if shape_name != "":
				shapes_set[shape_name] = absf(v)
		else:
			scale_by *= Vector3(1.0 + float(p["scale"][0]) * v, 1.0 + float(p["scale"][1]) * v, 1.0 + float(p["scale"][2]) * v)
	return scale_by

## Its keepsake, on the first socket the body has for it (a collar needs a neck).
func _wear_keepsake() -> void:
	var k: Dictionary = look.get("keepsake", {})
	if k.is_empty() or not ResourceLoader.exists(KEEP_DIR % String(k["id"])):
		return
	for sn in k["sockets"]:
		if sockets.has(sn):
			var art: Node3D = load(KEEP_DIR % String(k["id"])).instantiate()
			art.name = "Keepsake"
			_socket(sn).add_child(art)
			_adopt_art(art)
			keepsake = String(k["id"])
			return

## The home's hand: what its partner's home puts on a genius raised there (data/bodies.json,
## dress.trapping), in the home's own colours, hung at the collar or the throat beside any
## keepsake. A partner may take it off (look.trapping false).
var trapping := ""
func _wear_trapping() -> void:
	var home := String(info.get("home", (info.get("origin", {}) as Dictionary).get("city", "") if info.get("origin", {}) is Dictionary else ""))
	var born: Dictionary = info.get("look", {}) if info.get("look", {}) is Dictionary else {}
	if home == "" or not born.get("trapping", true) or not ResourceLoader.exists(TRAP_DIR % home):
		return
	var dress: Dictionary = Data.bodies.get(home, {}).get("dress", {})
	var cols: Dictionary = dress.get("colors", {})
	var lin := func(key: String, fallback: Color) -> Color:
		if not cols.has(key):
			return fallback
		var c: Array = cols[key]
		return Color(c[0], c[1], c[2]).linear_to_srgb()
	var main: Color = lin.call("main", Color(0.4, 0.4, 0.45))
	var second: Color = lin.call("second", main.lightened(0.4))
	var third := second
	for k in cols:
		if k not in ["main", "second"]:
			third = lin.call(String(k), second)
			if k == "metal":
				break
	var paint := func(n: Node3D) -> void:
		for m in n.find_children("*", "MeshInstance3D", true, false):
			var mi := m as MeshInstance3D
			for i in mi.mesh.get_surface_count():
				var nm := String(mi.mesh.surface_get_material(i).resource_name) if mi.mesh.surface_get_material(i) else ""
				var c: Color = main if nm == "home_main" else (second if nm == "home_second" else third)
				var sm := StandardMaterial3D.new()
				sm.albedo_color = c
				sm.roughness = 0.5 if nm == "home_metal" else 0.85
				sm.metallic = 0.5 if nm == "home_metal" and cols.has("metal") else 0.0
				mi.set_surface_override_material(i, sm)
	# a band first, where the body has a neck to put one on; then the piece on a free place
	var taken := ""
	for sn in ["socket_collar", "socket_keepsake", "socket_throat", "socket_body"]:
		if not sockets.has(sn):
			continue
		var holds_keepsake := false
		for ch in _socket(sn).get_children():
			holds_keepsake = holds_keepsake or String(ch.name) == "Keepsake"
		if holds_keepsake:
			continue
		if sn == "socket_collar" and ResourceLoader.exists(TRAP_DIR % "band"):
			var b: Node3D = load(TRAP_DIR % "band").instantiate()
			b.name = "TrappingBand"
			_socket(sn).add_child(b)
			paint.call(b)
		var art: Node3D = load(TRAP_DIR % home).instantiate()
		art.name = "Trapping"
		_socket(sn).add_child(art)
		if sn == "socket_collar":
			art.position = Vector3(0, -0.105, 0)     # it hangs from the band's lowest point
		paint.call(art)
		taken = sn
		break
	if taken != "":
		trapping = home

## An art body's sockets: nodes named socket_<name>, or, on a rigged body, bones of that name
## (an empty parented to a bone comes through the importer as a bone), each given a node to
## hang parts from that rides the bone.
func _art_sockets(model: Node3D) -> void:
	for n in model.find_children("socket_*", "", true, false):
		sockets[String(n.name)] = n
	for sk in model.find_children("*", "Skeleton3D", true, false):
		var skel := sk as Skeleton3D
		for i in skel.get_bone_count():
			var bn := skel.get_bone_name(i)
			if bn.begins_with("socket_") and not sockets.has(bn):
				var att := BoneAttachment3D.new()
				att.name = bn
				att.bone_name = bn
				skel.add_child(att)
				sockets[bn] = att

## The clips this body has, by what they are for (idle, walk, run), from its kind's names.
func _clips(names: Dictionary) -> Dictionary:
	var out := {}
	for k in names:
		if anim.has_animation(names[k]):
			out[k] = names[k]
	return out

## Parts of a pair are made for the left; a right-hand socket wears the mirror.
static func is_right(socket_name: String) -> bool:
	return socket_name.ends_with("_r") or socket_name.ends_with("fr") or socket_name.ends_with("br")

## A node's transform up to `root`, in the rest pose (a bone attachment stands at its bone's rest).
func _rest_xf(n: Node3D, root: Node) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var cur: Node = n
	while cur and cur != root:
		if cur is BoneAttachment3D and cur.get_parent() is Skeleton3D:
			var skel := cur.get_parent() as Skeleton3D
			var bi := skel.find_bone((cur as BoneAttachment3D).bone_name)
			xf = (skel.get_bone_global_rest(bi) if bi >= 0 else (cur as Node3D).transform) * xf
		elif cur is Node3D:
			xf = (cur as Node3D).transform * xf
		cur = cur.get_parent()
	return xf

## Whether it walks (and so follows at the heel) or floats and flies (at the shoulder).
func walks() -> bool:
	return not hover and kind in ["quadruped", "humanoid", "construct"]

var _gait := 0.0
var _gait_speed := 0.0

## Play idle, walk or run by how fast it is moving. An art body with no rig gets a gait of
## its own: a bob and a lean that read as walking.
func move_at(speed: float) -> void:
	_gait_speed = speed
	if not anim:
		return
	var want: String = anim_names.get("run" if speed > 4.0 else ("walk" if speed > 0.4 else "idle"), "")
	if want != "" and anim.has_animation(want) and anim.current_animation != want:
		anim.play(want, 0.2)

## The proportions of its age, on a rigged body: each bone named is scaled, and the body set
## down again so its feet stay on the ground when its legs are shorter or longer.
func _apply_age(bones: Dictionary) -> void:
	if bones.is_empty() or _model == null:
		return
	var sks := _model.find_children("*", "Skeleton3D", true, false)
	if sks.is_empty():
		return
	var sk: Skeleton3D = sks[0]
	var low := func() -> float:
		var y := INF
		for i in sk.get_bone_count():
			y = minf(y, sk.get_bone_global_pose(i).origin.y)
		return y
	var before: float = low.call()
	for bn in bones:
		var idx := sk.find_bone(String(bn))
		if idx >= 0:
			sk.set_bone_pose_scale(idx, Vector3.ONE * float(bones[bn]))
	var after: float = low.call()
	# the skeleton's own height above the model's floor, in the model's units
	sk.position.y -= (after - before) * sk.scale.y
	aged = true

var aged := false

## The mantle of a great genius: blades of light standing in a fan behind its head and
## shoulders, in its partner's Shape colour, breathing slowly. It is what says, from across a
## yard, that this one has come a long way.
func _mantle(count: int) -> void:
	mantle = Node3D.new()
	mantle.name = "Mantle"
	add_child(mantle)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.albedo_color = Color(color.lightened(0.25), 0.85)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var blade := PrismMesh.new()
	blade.size = Vector3(0.09, 1.0, 0.012)
	for i in count:
		var t := (float(i) / float(maxi(1, count - 1))) - 0.5          # -0.5 to 0.5 across the fan
		var mi := MeshInstance3D.new()
		mi.mesh = blade
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var length := stands * (0.62 - 0.5 * absf(t))                  # the middle blades the longest
		var pivot := Node3D.new()
		pivot.rotation.z = -t * 2.3                                    # fanned to either side
		mi.scale = Vector3(stands * 0.9, length, 1.0)
		mi.position = Vector3(0, length * 0.5 + stands * 0.16, 0)
		pivot.add_child(mi)
		mantle.add_child(pivot)
	# behind and above the shoulders: on the head's socket where the body has one
	mantle.position = Vector3(0, stands * 0.7, stands * (0.22 if kind == "quadruped" else -0.1))
	mantle.set_meta("rest", mantle.position)

## The molt lines: seams of light along the body as its next Reading nears (0 none, 1 due).
func set_molt(k: float) -> void:
	molt = clampf(k, 0.0, 1.0)
	for r in _rims:
		(r as ShaderMaterial).set_shader_parameter("molt", molt)
		# a few seams across the body, whatever its size
		(r as ShaderMaterial).set_shader_parameter("molt_scale", 0.42 / maxf(0.2, stands))

func set_strength(k: float) -> void:
	_mat.set_shader_parameter("strength", k)

## How strongly the Shape colour lies along its edges (1 in the world; a portrait that must
## show its coat turns it down).
func set_rim(k: float) -> void:
	for r in _rims:
		(r as ShaderMaterial).set_shader_parameter("strength", k)

func _process(dt: float) -> void:
	_t += dt
	for w in _wings:
		var side: float = w.get_meta("wing")
		var beat := side * (0.35 + 0.45 * sin(_t * 14.0))
		if w.has_meta("wing_rest"):
			var rest: Transform3D = w.get_meta("wing_rest")
			(w as Node3D).transform = rest * Transform3D(Basis(w.get_meta("wing_axis") as Vector3, beat), Vector3.ZERO)
		else:
			(w as Node3D).rotation.z = beat
	if _spinners.is_empty():
		for n in find_children("*", "MeshInstance3D", true, false):
			if n.has_meta("spin"):
				_spinners.append(n)
	for sp in _spinners:
		(sp as Node3D).rotate_object_local(Vector3.UP, dt * float(sp.get_meta("spin")))
	# A light that pulses or flickers: the field's surfaces breathe (the cel shader's copies too).
	var pulse := float(look.get("eyes", {}).get("pulse", 0.0)) if not look.is_empty() else 0.0
	if pulse > 0.0:
		var rate := float(look["eyes"].get("rate", 1.0))
		var k := 1.0 + pulse * (sin(_t * rate * TAU) if rate < 4.0 else sin(_t * rate * TAU) * sin(_t * rate * 2.7))
		for fs in _field_surfaces:
			if not is_instance_valid(fs[0]):
				continue
			var fm: Material = (fs[0] as MeshInstance3D).get_surface_override_material(int(fs[1]))
			if fm is StandardMaterial3D:
				(fm as StandardMaterial3D).emission_energy_multiplier = float(fs[2]) * k
			elif fm is ShaderMaterial:
				(fm as ShaderMaterial).set_shader_parameter("emission_energy", float(fs[2]) * k)
	if mantle:
		mantle.scale = Vector3.ONE * (1.0 + 0.04 * sin(_t * 1.3))
		mantle.rotation.x = -0.12 + 0.03 * sin(_t * 0.9)
	if hover and _model:
		_model.position.y = 0.06 * sin(_t * 2.2)
	elif _model and anim == null and uses_art:
		# No rig: a gait from the body itself.
		_gait += dt * clampf(_gait_speed, 0.0, 6.0) * 3.0
		var k := clampf(_gait_speed / 2.0, 0.0, 1.0)
		_model.position.y = absf(sin(_gait)) * 0.04 * k
		_model.rotation.z = sin(_gait) * 0.06 * k
		_model.rotation.x = -0.08 * k

# --- Placeholders ------------------------------------------------------------------

func _apply_surfaces(cfg: Dictionary) -> void:
	for f in info.get("features", []):
		var s: Dictionary = cfg["surfaces"].get(f, {})
		if s.is_empty():
			continue
		_mat.set_shader_parameter("tint", Color(s.get("tint", "#08060a")))
		_mat.set_shader_parameter("rim_k", float(s.get("rim", 1.0)))
		_mat.set_shader_parameter("bands", float(s.get("bands", 0)))

static func _slot_of(feature: String) -> String:
	for fd in Data.features():
		if fd["id"] == feature:
			return fd["slot"]
	return "body"

func _socket(name: String) -> Node3D:
	if sockets.has(name):
		return sockets[name]
	if sockets.has("socket_body"):
		return sockets["socket_body"]
	return self

func _placeholder_body(kspec: Dictionary, spec: Dictionary) -> void:
	_model = Node3D.new()
	add_child(_model)
	var skel: Skeleton3D = null
	if kspec.has("model"):
		var m: Node3D = load(kspec["model"]).instantiate()
		_model.add_child(m)
		for a in m.find_children("*", "BoneAttachment3D", true, false):
			a.visible = false
		for mi in m.find_children("*", "MeshInstance3D", true, false):
			mi.material_override = _mat
		skel = m.find_child("Skeleton3D", true, false)
		anim = m.find_child("AnimationPlayer", true, false)
		anim_names = kspec.get("anim", {})
	else:
		_shape_body(String(spec.get("build", "")))
	for sname in kspec["sockets"]:
		var s: Dictionary = kspec["sockets"][sname]
		var at := Vector3(s.get("at", [0, 0, 0])[0], s.get("at", [0, 0, 0])[1], s.get("at", [0, 0, 0])[2])
		var marker := Marker3D.new()
		marker.name = sname
		marker.position = at
		if s.has("bone") and skel and skel.find_bone(s["bone"]) >= 0:
			var att := BoneAttachment3D.new()
			att.bone_name = s["bone"]
			skel.add_child(att)
			# Bone sockets ride the rig; a rig may be scaled inside its file, so the socket
			# undoes that scale and its parts come out in metres.
			var bone_xf := _local_xf(skel) * skel.get_bone_global_rest(skel.find_bone(s["bone"]))
			var k := bone_xf.basis.get_scale()
			var inv := Vector3(1.0 / maxf(k.x, 1e-4), 1.0 / maxf(k.y, 1e-4), 1.0 / maxf(k.z, 1e-4))
			marker.scale = inv
			marker.position = at * inv
			att.add_child(marker)
		else:
			_model.add_child(marker)
		sockets[sname] = marker

func _part(mesh: Mesh, parent: Node3D, pos := Vector3.ZERO, rot := Vector3.ZERO, scl := Vector3.ONE, mat: Material = null) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	m.mesh = mesh
	m.position = pos
	m.rotation = rot
	m.scale = scl
	m.material_override = mat if mat else _mat
	parent.add_child(m)
	if m.has_meta("spin"):
		_spinners.append(m)
	return m

func _glow_mat(k := 5.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = color.lightened(0.4)
	m.emission_enabled = true
	m.emission = color
	m.emission_energy_multiplier = k
	return m

## Bodies built from shapes, for the kinds with no rigged model to borrow.
func _shape_body(build: String) -> void:
	var b := _model
	match build:
		"bird":
			_part(_sphere(0.16), b, Vector3(0, 0.5, 0), Vector3.ZERO, Vector3(1, 1, 1.5))
			_part(_sphere(0.11), b, Vector3(0, 0.64, 0.2))
			_part(_box(Vector3(0.12, 0.02, 0.22)), b, Vector3(0, 0.46, -0.28), Vector3(0.3, 0, 0))
		"lantern":
			_part(_box(Vector3(0.34, 0.42, 0.34)), b, Vector3(0, 0.62, 0))
			_part(_cone(0.26, 0.2), b, Vector3(0, 0.92, 0))
			_part(_sphere(0.1), b, Vector3(0, 0.62, 0), Vector3.ZERO, Vector3.ONE, _glow_mat())
		"fortress":
			_part(_box(Vector3(0.9, 0.7, 0.7)), b, Vector3(0, 0.4, 0))
			for x in [-0.35, 0.35]:
				_part(_box(Vector3(0.22, 0.95, 0.22)), b, Vector3(x, 0.5, 0.3))
		"wall":
			_part(_box(Vector3(1.0, 0.9, 0.3)), b, Vector3(0, 0.45, 0))
		"gate":
			for x in [-0.4, 0.4]:
				_part(_box(Vector3(0.2, 1.0, 0.2)), b, Vector3(x, 0.5, 0))
			_part(_box(Vector3(1.0, 0.18, 0.24)), b, Vector3(0, 1.05, 0))
		"gun":
			_part(_box(Vector3(0.14, 0.18, 0.7)), b, Vector3(0, 0.5, 0))
			_part(_cyl(0.05, 0.6), b, Vector3(0, 0.55, 0.5), Vector3(PI / 2, 0, 0))
		"blade":
			_part(_box(Vector3(0.05, 0.95, 0.12)), b, Vector3(0, 0.6, 0))
			_part(_box(Vector3(0.3, 0.05, 0.08)), b, Vector3(0, 0.18, 0))
		"shield":
			_part(_cyl(0.42, 0.08), b, Vector3(0, 0.5, 0), Vector3(PI / 2, 0, 0))
		"gauntlet":
			_part(_box(Vector3(0.26, 0.34, 0.3)), b, Vector3(0, 0.45, 0))
			for i in 4:
				_part(_box(Vector3(0.05, 0.16, 0.05)), b, Vector3(-0.09 + i * 0.06, 0.68, 0.08))
		"coat":
			_part(_cone(0.32, 0.8), b, Vector3(0, 0.45, 0))
			_part(_cyl(0.16, 0.14), b, Vector3(0, 0.88, 0))
		"mask":
			_part(_sphere(0.28), b, Vector3(0, 0.55, 0), Vector3.ZERO, Vector3(1, 1.2, 0.35))
		"flame", "shadow", "chord", "weather":
			_aspect(build)
		_:
			_part(_sphere(0.25), b, Vector3(0, 0.5, 0))

func _aspect(build: String) -> void:
	var core_mat: Material = _glow_mat(3.0) if build != "shadow" else _mat
	_part(_sphere(0.2), _model, Vector3(0, 0.55, 0), Vector3.ZERO, Vector3.ONE, core_mat)
	if build == "chord":
		for i in 3:
			var r := _part(_torus(0.3 + i * 0.12, 0.012), _model, Vector3(0, 0.55, 0), Vector3(randf() * PI, randf() * PI, 0), Vector3.ONE, _glow_mat(3.0))
			r.set_meta("spin", 1.0 + i)
	var p := CPUParticles3D.new()
	p.amount = 40
	p.lifetime = 0.9
	p.local_coords = false
	p.direction = Vector3(0, 1, 0)
	p.spread = 25.0 if build != "weather" else 180.0
	p.initial_velocity_min = 0.3
	p.initial_velocity_max = 0.8
	p.gravity = Vector3(0, 0.6, 0) if build != "weather" else Vector3.ZERO
	p.orbit_velocity_min = 0.0 if build != "weather" else 0.6
	p.orbit_velocity_max = 0.0 if build != "weather" else 1.0
	var q := QuadMesh.new()
	q.size = Vector2(0.16, 0.16)
	p.mesh = q
	var pm := StandardMaterial3D.new()
	pm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	pm.blend_mode = BaseMaterial3D.BLEND_MODE_MIX if build == "shadow" else BaseMaterial3D.BLEND_MODE_ADD
	pm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	pm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	pm.vertex_color_use_as_albedo = true
	pm.albedo_texture = World._soft_dot()
	p.material_override = pm
	var g := Gradient.new()
	g.set_color(0, Color(0.08, 0.04, 0.12, 0.8) if build == "shadow" else Color(color.lightened(0.3), 0.9))
	g.set_color(1, Color(color, 0.0))
	p.color_ramp = g
	p.position = Vector3(0, 0.5, 0)
	_model.add_child(p)

## A part for a feature with no art yet: a shape for its slot, chosen by what its name says.
func _placeholder_part(f: String, slot: String, socks: Array) -> void:
	match slot:
		"head":
			var s := _socket(socks[0])
			if f.contains("horn"):
				for side in [-1, 1]:
					_part(_cone(0.04, 0.2), s, Vector3(side * 0.08, 0.04, 0), Vector3(0, 0, -side * 0.45))
			elif f == "beak":
				_part(_cone(0.05, 0.16), s, Vector3(0, -0.06, 0.12), Vector3(PI / 2, 0, 0))
			elif f == "antlers":
				for side in [-1, 1]:
					_part(_cyl(0.015, 0.3), s, Vector3(side * 0.08, 0.12, 0), Vector3(0, 0, -side * 0.5))
					_part(_cyl(0.012, 0.15), s, Vector3(side * 0.16, 0.2, 0.02), Vector3(0.6, 0, -side * 0.9))
			elif f == "crown":
				for i in 5:
					var a := i * TAU / 5.0
					_part(_cone(0.025, 0.1), s, Vector3(cos(a) * 0.08, 0.05, sin(a) * 0.08), Vector3.ZERO, Vector3.ONE, _glow_mat(2.0))
			elif f in ["fangs", "maw", "lantern-jaw"]:
				_part(_box(Vector3(0.16, 0.06, 0.08)), s, Vector3(0, -0.1, 0.12), Vector3.ZERO, Vector3.ONE, _glow_mat(1.5))
			elif f in ["mask", "shield-face", "second-face"]:
				_part(_sphere(0.12), s, Vector3(0, -0.04, 0.1), Vector3.ZERO, Vector3(1, 1.2, 0.3))
			else:
				for i in 3:
					_part(_box(Vector3(0.02, 0.14 - i * 0.03, 0.06)), s, Vector3(0, 0.05, -0.04 * i), Vector3(-0.4, 0, 0))
		"eyes":
			var s := _socket(socks[0])
			var r := 0.035 if f == "far-eyes" else 0.028
			var n := 2
			for i in n:
				_part(_sphere(r), s, Vector3((i - 0.5) * 0.12, 0, 0), Vector3.ZERO, Vector3.ONE, _glow_mat(6.0))
		"wings":
			var s := _socket(socks[0])
			for side in [-1, 1]:
				var w := _part(_box(Vector3(0.6, 0.025, 0.28) if f == "wings" else Vector3(0.3, 0.5, 0.03)), s, Vector3(side * (0.36 if f == "wings" else 0.12), 0, 0), Vector3(0, 0, side * 0.3))
				if f == "wings":
					w.set_meta("wing", side)
					_wings.append(w)
		"body":
			var s := _socket(socks[0])
			if f in ["gears"]:
				var g := _part(_torus(0.1, 0.03), s, Vector3(0, 0, 0.04), Vector3(PI / 2, 0, 0), Vector3.ONE, _glow_mat(1.5))
				g.set_meta("spin", 2.0)
			elif f in ["tower-shield", "bastion", "door"]:
				_part(_box(Vector3(0.3, 0.42, 0.05)), s, Vector3(0, 0, 0.1))
			else:
				_part(_sphere(0.16), s, Vector3(0, 0, 0.02), Vector3.ZERO, Vector3(1.2, 0.9, 0.7))
		"arms":
			var s := _socket(socks[0])
			if f == "barrel":
				_part(_cyl(0.04, 0.4), s, Vector3(0, 0, 0.2), Vector3(PI / 2, 0, 0))
			elif f == "chain":
				for i in 4:
					_part(_torus(0.04, 0.012), s, Vector3(0, -0.07 * i, 0), Vector3(0, PI / 2 * (i % 2), 0), Vector3.ONE, _glow_mat(1.2))
			else:
				_part(_box(Vector3(0.03, 0.34, 0.07)), s, Vector3(0, 0.12, 0.04), Vector3.ZERO, Vector3.ONE, _glow_mat(0.8) if f == "edge" else null)
		"limbs":
			for sn in socks:
				if not sockets.has(sn):
					continue
				var s := _socket(sn)
				if f in ["talons", "talon-grip", "ground-claws", "set-feet"]:
					_part(_cone(0.03, 0.08), s, Vector3(0, -0.02, 0.04), Vector3(PI / 2, 0, 0))
				elif f in ["fins", "webbed"]:
					_part(_box(Vector3(0.1, 0.01, 0.12)), s, Vector3(0, 0, 0))
				elif f == "roots":
					_part(_cone(0.05, 0.22), s, Vector3(0, -0.08, 0), Vector3(PI, 0, 0))
			if f == "tail":
				_part(_cone(0.04, 0.4), _socket("socket_body"), Vector3(0, -0.05, -0.3), Vector3(-PI / 2 - 0.4, 0, 0))
		"light":
			var s := _socket(socks[0])
			_part(_sphere(0.07 if f != "lantern" else 0.09), s, Vector3.ZERO, Vector3.ZERO, Vector3.ONE, _glow_mat(6.0))
			if f == "lantern":
				_part(_box(Vector3(0.16, 0.2, 0.16)), s, Vector3.ZERO, Vector3.ZERO, Vector3.ONE, null).transparency = 0.6
			var l := OmniLight3D.new()
			l.light_color = color
			l.light_energy = 0.8
			l.omni_range = 2.0
			s.add_child(l)
		"voice":
			var s := _socket(socks[0])
			var r := _part(_torus(0.07, 0.012), s, Vector3.ZERO, Vector3(PI / 2, 0, 0), Vector3.ONE, _glow_mat(3.0))
			r.set_meta("spin", 1.5)

## Scale the whole genius to its height for its instar, with its silhouette's proportions.
func _fit_height(height: float, proportions: Vector3) -> void:
	var top := 0.0
	var bottom := INF
	for m in find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		if not _shown(mi):
			continue
		var xf := _mesh_xf(mi)
		var ab: AABB = xf * mi.get_aabb()
		top = maxf(top, ab.end.y)
		bottom = minf(bottom, ab.position.y)
	var h := maxf(0.05, top - minf(bottom, 0.0))
	var k := height / h
	_model.scale = proportions * k

func _shown(n: Node) -> bool:
	var cur: Node = n
	while cur and cur != self:
		if cur is Node3D and not (cur as Node3D).visible:
			return false
		cur = cur.get_parent()
	return true

## Where a mesh's own points stand in this body. A skinned mesh of an art body stands where
## its skeleton binds it (its bones may carry a scale the mesh's node does not), not where its
## node is.
func _mesh_xf(mi: MeshInstance3D) -> Transform3D:
	if uses_art and mi.skin and mi.skin.get_bind_count() > 0:
		var skel := mi.get_node_or_null(mi.skeleton) as Skeleton3D
		if skel:
			var b := mi.skin.get_bind_bone(0)
			if b < 0:
				b = skel.find_bone(mi.skin.get_bind_name(0))
			if b >= 0:
				return _local_xf(skel) * skel.get_bone_global_rest(b) * mi.skin.get_bind_pose(0)
	# a piece that rides a bone stands at the bone's rest (its attachment has not moved yet)
	return _rest_xf(mi, self) if uses_art else _local_xf(mi)

func _local_xf(n: Node3D) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var cur: Node = n
	while cur and cur != self:
		if cur is Node3D:
			xf = (cur as Node3D).transform * xf
		cur = cur.get_parent()
	return xf

static func _sphere(r: float) -> SphereMesh:
	var m := SphereMesh.new()
	m.radius = r
	m.height = r * 2.0
	m.radial_segments = 16
	m.rings = 8
	return m

static func _cone(r: float, h: float) -> CylinderMesh:
	var m := CylinderMesh.new()
	m.top_radius = 0.0
	m.bottom_radius = r
	m.height = h
	return m

static func _cyl(r: float, h: float) -> CylinderMesh:
	var m := CylinderMesh.new()
	m.top_radius = r
	m.bottom_radius = r
	m.height = h
	return m

static func _box(size: Vector3) -> BoxMesh:
	var m := BoxMesh.new()
	m.size = size
	return m

static func _torus(r: float, t: float) -> TorusMesh:
	var m := TorusMesh.new()
	m.inner_radius = r - t
	m.outer_radius = r + t
	return m
