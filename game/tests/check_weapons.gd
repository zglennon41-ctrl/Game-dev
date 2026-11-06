extends SceneTree
func _init() -> void:
	var dir := DirAccess.open("res://game/assets/weapons")
	var bad := []
	for f in dir.get_files():
		if f.ends_with(".glb"):
			var r = load("res://game/assets/weapons/" + f)
			if r == null: bad.append(f)
	var w = JSON.parse_string(FileAccess.get_file_as_string("res://data/weapons.json"))
	for x in w:
		for key in ["model", "offhand"]:
			if x.has(key):
				var p := "res://game/assets/weapons/%s.glb" % x[key]
				var kk := "res://game/assets/kaykit/weapons/%s.gltf" % x[key]
				if not ResourceLoader.exists(p) and not ResourceLoader.exists(kk): bad.append("missing " + x[key])
	print("BAD: ", bad)
	quit()
