class_name Augment
extends Node3D
## An Augment: a genius that is part of its partner's body (docs/genius-types.md, "Augments";
## data/genius.json, equipment.augments). A first proof, for looking at: living wings worn at
## the back through the five stages. It rides a bone of its partner's own rig, is made to the
## breadth of their shoulders, and is the same size at every stage. Nothing here is a rule of
## a fight: how an Augment fights is not decided.

const DIR := "res://game/assets/genius/augments/%s-%d.glb"

var kind := ""
var stage := 0
var spread := 0.0          # 0 folded at the back to 1 opened (its partner moving fast, or striking)
var _wings: Array = []     # [node, rest transform, side]
var _movers: Array = []    # [node, kind, rest transform, phase]
var _t := 0.0
var _open := 0.0


## How broad a body is against the one the wings were made on, from its own bones (pure).
static func fit(shoulders: float, made_for: float, least := 0.8, most := 1.25) -> float:
	return clampf(shoulders / maxf(0.01, made_for), least, most)

## The stage of a line (0 Baby to 4 Final) an Augment's model is for, kept inside what there is.
static func stage_of(level: int, stages: int) -> int:
	return clampi(level, 0, maxi(0, stages - 1))

## Hang one on a partner's rig. rule: its entry in data/genius.json (equipment.augments.<kind>:
## bone, at, madeFor, stages). tint: the colour its lights take (the partner's Shape).
## Returns null if the rig has no such bone or the stage no model.
static func wear(skel: Skeleton3D, kind_id: String, rule: Dictionary, level: int, tint: Color) -> Augment:
	var st := stage_of(level, (rule.get("stages", []) as Array).size())
	var bone := skel.find_bone(String(rule.get("bone", "chest"))) if skel else -1
	if bone < 0 or not ResourceLoader.exists(DIR % [kind_id, st]):
		return null
	var att := BoneAttachment3D.new()
	att.name = "augment_" + kind_id
	att.bone_name = skel.get_bone_name(bone)
	skel.add_child(att)
	var a := Augment.new()
	a.kind = kind_id
	a.stage = st
	att.add_child(a)
	# it stands as its partner stands, whatever way the bone itself is turned, and from there
	# it goes with the bone
	var rest := skel.get_bone_global_rest(bone)
	var at: Array = rule.get("at", [0, 0, 0])
	var square := rest.basis.orthonormalized().inverse()
	a.transform = Transform3D(square, square * Vector3(at[0], at[1], at[2]))
	# and it is made to the breadth of their shoulders
	var l := skel.find_bone("upperarm.l")
	var r := skel.find_bone("upperarm.r")
	if l >= 0 and r >= 0:
		var k := fit(skel.get_bone_global_rest(l).origin.distance_to(skel.get_bone_global_rest(r).origin), float(rule.get("madeFor", 0.375)))
		a.scale = Vector3.ONE * k
	var model: Node3D = (load(DIR % [kind_id, st]) as PackedScene).instantiate()
	a.add_child(model)
	for n in model.find_children("*", "Node3D", true, false):
		var nm := String(n.name)
		var node := n as Node3D
		if nm.begins_with("wing_"):
			a._wings.append([node, node.transform, 1.0 if nm.ends_with("_l") else -1.0])
		else:
			for mv in ["blink", "pulse", "sway"]:
				if nm.begins_with(mv + "_"):
					a._movers.append([node, mv, node.transform, float(nm.hash() % 628) / 100.0])
	# its lights take its partner's colour
	for m in model.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			var born := mi.mesh.surface_get_material(i)
			if born and String(born.resource_name).begins_with("field"):
				var lit := StandardMaterial3D.new()
				lit.resource_name = born.resource_name
				lit.albedo_color = tint.lightened(0.35)
				lit.emission_enabled = true
				lit.emission = tint.lightened(0.2)
				lit.emission_energy_multiplier = 2.4
				mi.set_surface_override_material(i, lit)
	return a


func _process(dt: float) -> void:
	_t += dt
	_open = lerpf(_open, spread, 1.0 - exp(-dt * 7.0))
	for w in _wings:
		var node := w[0] as Node3D
		var rest: Transform3D = w[1]
		var side: float = w[2]
		# folded, they lie in behind the shoulders; opened, they stand out and up; and they breathe
		var breathe := 0.03 * sin(TAU * _t / 3.4 + (0.6 if side < 0.0 else 0.0))
		var out := lerpf(-0.42, 0.5, _open) + breathe
		var back := lerpf(0.1, 0.3, _open)
		node.transform = rest * Transform3D(Basis(Vector3.UP, side * back) * Basis(Vector3.BACK, side * out), Vector3.ZERO)
	var blinking := fmod(_t, 4.3) < 0.11 or fmod(_t + 1.7, 7.1) < 0.11
	for mv in _movers:
		var node := mv[0] as Node3D
		var rest: Transform3D = mv[2]
		var ph: float = mv[3]
		var turn := Basis.IDENTITY
		match String(mv[1]):
			"blink": turn = Basis.from_scale(Vector3(1.0, 0.08 if blinking else 1.0, 1.0))
			"pulse": turn = Basis.from_scale(Vector3.ONE * (1.0 + 0.045 * sin(TAU * _t / 3.2 + ph)))
			"sway": turn = Basis.from_euler(Vector3(0.1 * sin(TAU * _t / 2.6 + ph), 0.0, 0.06 * sin(TAU * _t / 3.4 + ph * 1.7)))
		node.transform = rest * Transform3D(turn, Vector3.ZERO)
