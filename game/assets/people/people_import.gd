## Runs when Godot imports a person: saves each mesh without its shape keys and keeps the keys
## small beside it (see game/scripts/shapes.gd). Named as `import_script/path` in each
## person's .import file; check_people.gd fails if one has lost it.
@tool
extends EditorScenePostImport

func _post_import(scene: Node) -> Object:
	for m in scene.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		if mi.mesh is ArrayMesh:
			mi.mesh = Shapes.pack(mi.mesh)
			# a second copy of every mesh for casting shadows is a fifth of a person's file: the
			# hair of twenty styles, of which one is worn. Shadows are cast by the mesh itself.
			(mi.mesh as ArrayMesh).shadow_mesh = null
		if String(mi.name) == "Cape":      # the cloak every body has: off until a look puts it on (world.gd, dress)
			mi.visible = false
	return scene
