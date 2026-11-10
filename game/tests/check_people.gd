## A check on the people art: every body in game/assets/people must load, carry an
## AnimationPlayer with the animations the game plays by name, a Skeleton3D with the hand slots
## the game hangs weapons from, and skinned meshes; the bone attachments (helmet, hat, cape,
## the pack's weapons) are listed so a lost one shows.
## Run: godot --headless --path . -s res://game/tests/check_people.gd
extends SceneTree

const DIR := "res://game/assets/people"
const HOMES := ["alexandria", "columbia", "cahokia", "lunden", "colonia", "tiber", "khemet", "baghdad", "varanasi", "jiangnan", "kazan", "timbuktu", "edo"]
const BODIES := ["alexandria-m", "alexandria-f", "columbia-m", "columbia-f", "cahokia-m", "cahokia-f", "lunden-m", "lunden-f", "colonia-m", "colonia-f", "tiber-m", "tiber-f", "khemet-m", "khemet-f", "baghdad-m", "baghdad-f", "varanasi-m", "varanasi-f", "jiangnan-m", "jiangnan-f", "kazan-m", "kazan-f", "timbuktu-m", "timbuktu-f", "edo-m", "edo-f"]
const SOCKETS := ["socket_head", "socket_eyes", "socket_throat", "socket_back", "socket_tail", "socket_hand_l", "socket_hand_r", "socket_light"]
const MUST := ["Idle", "Running_A", "1H_Melee_Attack_Slice_Horizontal", "Walking_A", "Walking_Backwards", "Blocking",
	"Block_Hit", "Hit_A", "Hit_B", "Death_A", "Dodge_Forward", "Dodge_Backward"]
const BONES := ["handslot.r", "handslot.l", "head"]


func _init() -> void:
	var ok := true
	for body: String in BODIES:
		var path := DIR + "/" + body + ".glb"
		if not ResourceLoader.exists(path):
			printerr(body, ": missing ", path)
			ok = false
			continue
		var scene: PackedScene = load(path)
		if scene == null:
			printerr(body, ": does not load")
			ok = false
			continue
		var inst: Node = scene.instantiate()
		var ap: AnimationPlayer = inst.find_child("AnimationPlayer", true, false)
		var skel: Skeleton3D = inst.find_child("Skeleton3D", true, false)
		var missing: Array[String] = []
		if ap == null:
			missing.append("(no AnimationPlayer)")
		else:
			for a in MUST:
				if not ap.has_animation(a):
					missing.append(a)
		var lost_bones: Array[String] = []
		if skel == null:
			lost_bones.append("(no Skeleton3D)")
		else:
			for b in BONES:
				if skel.find_bone(b) < 0:
					lost_bones.append(b)
		var meshes := inst.find_children("*", "MeshInstance3D", true, false)
		var skinned := 0
		var textured := 0
		for m in meshes:
			var mi := m as MeshInstance3D
			if mi.skin != null:
				skinned += 1
			if mi.mesh != null and mi.mesh.get_surface_count() > 0:
				var mat := mi.mesh.surface_get_material(0) as StandardMaterial3D
				if mat != null and mat.albedo_texture != null:
					textured += 1
		var attachments: Array[String] = []
		for a in inst.find_children("*", "BoneAttachment3D", true, false):
			attachments.append(String(a.name))
		attachments.sort()
		# Godot folds an empty under a joint into the skeleton: the sockets are bones.
		for sk in SOCKETS:
			if skel == null or skel.find_bone(sk) < 0:
				missing.append(sk)
		var body_mesh: MeshInstance3D = inst.find_child("Body", true, false)
		if body_mesh == null or body_mesh.find_blend_shape_by_name("lean") < 0 or body_mesh.find_blend_shape_by_name("heavy") < 0:
			missing.append("(lean/heavy shape keys)")
		# The home's dress (data/bodies.json): its pieces skinned, its headgear on the head.
		var home := body.get_slice("-", 0)
		var homes: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/bodies.json")).get("homes", {})
		var dress: Dictionary = homes.get(home, {}).get("dress", {})
		if not dress.is_empty():
			var pieces := inst.find_children("Dress_*", "MeshInstance3D", true, false)
			if pieces.size() < dress.get("pieces", []).size():
				missing.append("(dress: %d of %d pieces)" % [pieces.size(), dress.get("pieces", []).size()])
			for pc in pieces:
				# rigid pieces (buttons, a badge, knots, tools, pauldrons, pteruges) hang from bones
				var rigid := false
				for word in ["_button_", "_badge", "_knot", "_tail_", "_tool_", "_pauldron_", "_strip_"]:
					if String(pc.name).contains(word):
						rigid = true
				if not rigid and (pc as MeshInstance3D).skin == null:
					missing.append("(dress piece %s not skinned)" % pc.name)
					break
			if dress.has("headgear") and inst.find_child("Headgear_*", true, false) == null:
				missing.append("(headgear %s)" % dress["headgear"]["type"])
		# the face: the eyes, the brows and the lashes hang from the head; the rest is the body's own
		for fc in ["Eye_l", "Eye_r", "Brow_l", "Brow_r", "Lash_l", "Lash_r"]:
			if inst.find_child(fc, true, false) == null:
				missing.append(fc)
		print(body, ": animations=", ap.get_animation_list().size() if ap else 0, " bones=", skel.get_bone_count() if skel else 0,
			" meshes=", meshes.size(), " skinned=", skinned, " textured=", textured)
		print("    attachments=", attachments)
		if not missing.is_empty() or not lost_bones.is_empty() or skinned == 0:
			printerr(body, ": FAIL missing animations=", missing, " lost bones=", lost_bones, " skinned=", skinned, " textured=", textured)
			ok = false
		inst.free()
	print("people: ", "all good" if ok else "FAILED")
	quit(0 if ok else 1)
