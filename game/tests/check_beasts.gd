## A check on the beast art: every file in game/assets/beasts must load, carry an
## AnimationPlayer with the wolf's animations (the game plays them by name) and a skinned mesh.
## Run: godot --headless --path . -s res://game/tests/check_beasts.gd
extends SceneTree

const DIR := "res://game/assets/beasts"
const MUST := ["AnimalArmature|Walk", "AnimalArmature|Idle", "AnimalArmature|Attack", "AnimalArmature|Death",
	"AnimalArmature|Gallop", "AnimalArmature|Idle_2_HeadLow", "AnimalArmature|Idle_HitReact_Left", "AnimalArmature|Idle_HitReact_Right"]


func _init() -> void:
	var ok := true
	var files: Array[String] = []
	var dir := DirAccess.open(DIR)
	if dir == null:
		printerr("no such folder: ", DIR)
		quit(1)
		return
	dir.list_dir_begin()
	var f := dir.get_next()
	while f != "":
		if f.ends_with(".glb"):
			files.append(f)
		f = dir.get_next()
	files.sort()
	if files.is_empty():
		printerr("no beasts in ", DIR)
		ok = false
	for name in files:
		var scene: PackedScene = load(DIR + "/" + name)
		if scene == null:
			printerr(name, ": does not load")
			ok = false
			continue
		var inst: Node = scene.instantiate()
		var ap: AnimationPlayer = inst.find_child("AnimationPlayer", true, false)
		if ap == null:
			printerr(name, ": no AnimationPlayer")
			ok = false
			inst.free()
			continue
		var anims := ap.get_animation_list()
		var has_walk := ap.has_animation("AnimalArmature|Walk")
		var missing: Array[String] = []
		for a in MUST:
			if not ap.has_animation(a):
				missing.append(a)
		var skel: Skeleton3D = inst.find_child("Skeleton3D", true, false)
		var meshes := inst.find_children("*", "MeshInstance3D", true, false)
		var skinned := 0
		for m in meshes:
			if (m as MeshInstance3D).skin != null:
				skinned += 1
		print(name, ": ", anims.size(), " animations ", anims, " walk=", has_walk)
		print("    bones=", skel.get_bone_count() if skel else 0, " meshes=", meshes.size(), " skinned=", skinned)
		if not has_walk or not missing.is_empty() or skel == null or skinned == 0:
			printerr(name, ": FAIL missing=", missing, " skeleton=", skel != null, " skinned=", skinned)
			ok = false
		inst.free()
	print("beasts: ", "all good" if ok else "FAILED")
	quit(0 if ok else 1)
