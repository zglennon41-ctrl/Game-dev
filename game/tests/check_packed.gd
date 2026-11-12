## Are the people's shape keys packed small (game/scripts/shapes.gd)? Prints, for each body, how
## many of its meshes carry keys and how many of those are packed, and the size of what was
## imported: the web build has a ceiling, and unpacked people do not fit under it.
## Run: godot --headless --path . -s res://game/tests/check_packed.gd
extends SceneTree

func _init() -> void:
	var total := 0
	var packed_all := true
	for f in DirAccess.get_files_at("res://game/assets/people"):
		if not f.ends_with(".glb"):
			continue
		var scene: PackedScene = load("res://game/assets/people/" + f)
		var inst := scene.instantiate()
		var keyed := 0
		var packed := 0
		for m in inst.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = (m as MeshInstance3D).mesh
			if mesh is ArrayMesh and mesh.has_meta(Shapes.META):
				keyed += 1
				packed += 1
			elif mesh is ArrayMesh and (mesh as ArrayMesh).get_blend_shape_count() > 0:
				keyed += 1
		inst.free()
		var cfg := ConfigFile.new()
		cfg.load("res://game/assets/people/" + f + ".import")
		var size := FileAccess.open(String(cfg.get_value("remap", "path", "")), FileAccess.READ).get_length()
		total += size
		packed_all = packed_all and packed == keyed
		print("%s: %d of %d keyed meshes packed, %.1f MB imported" % [f, packed, keyed, size / 1e6])
	print("people imported: %.0f MB, %s" % [total / 1e6, "packed" if packed_all else "NOT all packed"])
	quit(0)
