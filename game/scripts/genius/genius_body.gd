## A genius, assembled: a body for its silhouette and a part for each feature, hung on named
## sockets (data/genius-bodies.json). Real art drops in by name and replaces the placeholders:
##   game/assets/genius/bodies/<silhouette>.glb   (with empties named socket_<name>)
##   game/assets/genius/parts/<feature>.glb
## Until then, placeholder bodies borrow a rigged model (four-legged and humanoid kinds) or are
## built from shapes, in shadow lit at the edges by the partner's Shape colour.
class_name GeniusBody
extends Node3D

const BODY_DIR := "res://game/assets/genius/bodies/%s.glb"
const PART_DIR := "res://game/assets/genius/parts/%s.glb"

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
void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.6);
	ALBEDO = glow.rgb * rim * 1.6 * strength;
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
var parts_from_art: Array = []     # features whose parts came from art files
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
	if ResourceLoader.exists(BODY_DIR % sil):
		_model = load(BODY_DIR % sil).instantiate()
		add_child(_model)
		uses_art = true
		for n in _model.find_children("socket_*", "", true, false):
			sockets[String(n.name)] = n
		anim = _model.find_child("AnimationPlayer", true, false)
		_adopt_art(_model)
	else:
		_placeholder_body(cfg["kinds"][kind], spec)
	var sc: Array = spec.get("scale", [1, 1, 1])
	_fit_height(float(Data.genius()["size"].get(str(maxi(1, instar)), 0.6)), Vector3(sc[0], sc[1], sc[2]))
	# Parts, on the sockets for their slots.
	var feats: Array = info.get("features", [])
	var slot_count := {}
	for f in feats:
		var slot := _slot_of(f)
		if slot == "surface":
			continue
		var socks: Array = cfg["slotSockets"].get(slot, ["socket_body"])
		var i: int = slot_count.get(slot, 0)
		slot_count[slot] = i + 1
		if ResourceLoader.exists(PART_DIR % f):
			# A part made for a paired slot (limbs, arms) goes on every socket the body has for it.
			var targets: Array = socks.filter(func(sn): return sockets.has(sn)) if socks.size() > 1 else [socks[0]]
			if targets.is_empty():
				targets = [socks[i % socks.size()]]
			for sn in targets:
				var art: Node3D = load(PART_DIR % f).instantiate()
				_socket(sn).add_child(art)
				_adopt_art(art)
			parts_from_art.append(f)
		else:
			_placeholder_part(f, slot, socks)
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
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		mi.material_overlay = rim
		for i in mi.get_surface_override_material_count():
			var mat: Material = mi.mesh.surface_get_material(i)
			if mat and mat.resource_name.begins_with("field") and mat is StandardMaterial3D:
				var t := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				t.emission_enabled = true
				t.emission = color
				t.emission_energy_multiplier = 1.8
				t.albedo_color = color.darkened(0.7)
				mi.set_surface_override_material(i, t)
	for side in [["wing_l", -1.0], ["wing_r", 1.0]]:
		var w: Node = n.find_child(side[0], true, false)
		if w:
			w.set_meta("wing", side[1])
			_wings.append(w)

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

func set_strength(k: float) -> void:
	_mat.set_shader_parameter("strength", k)

func _process(dt: float) -> void:
	_t += dt
	for w in _wings:
		var side: float = w.get_meta("wing")
		(w as Node3D).rotation.z = side * (0.35 + 0.45 * sin(_t * 14.0))
	if _spinners.is_empty():
		for n in find_children("*", "MeshInstance3D", true, false):
			if n.has_meta("spin"):
				_spinners.append(n)
	for sp in _spinners:
		(sp as Node3D).rotate_object_local(Vector3.UP, dt * float(sp.get_meta("spin")))
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
		var xf := _local_xf(mi)
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
