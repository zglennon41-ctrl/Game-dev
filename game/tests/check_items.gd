## A check on the bodies of the items of power (the Lantern, the Astrolabe, the Bell): every
## form of the three must have a model of its own in game/assets/genius/forms, and the model
## must carry what the game and the contract rely on (docs/genius-lines.md): `ref_top`
## at the kit's height, `carry` (where a hand or a hook takes it), the usual sockets, a light
## of the field somewhere on it; it must stand on the ground and weigh under 80 KB.
## Run: godot --headless --path . -s res://game/tests/check_items.gd
extends SceneTree

const DIR := "res://game/assets/genius/forms/%s.glb"
const BASES := ["lantern", "astrolabe", "bell"]
const SOCKETS := ["socket_head", "socket_eyes", "socket_light", "socket_throat", "socket_back", "socket_body", "socket_keepsake"]


func _init() -> void:
	var ok := true
	var count := 0
	for base: String in BASES:
		var file := FileAccess.open("res://data/genius-bases/%s.json" % base, FileAccess.READ)
		var b: Dictionary = JSON.parse_string(file.get_as_text())
		var ids: Array = []
		_walk(b["settled"], ids)
		for p in b["paths"]:
			_walk(p, ids)
		for entry in ids:
			var id := String(entry[0])
			var body: Dictionary = entry[1]
			var path := DIR % id
			if not ResourceLoader.exists(path):
				printerr(id, ": no model")
				ok = false
				continue
			var inst: Node3D = (load(path) as PackedScene).instantiate()
			var said: Array[String] = []
			var ref: Node = inst.find_child("ref_top", true, false)
			if ref == null or absf((ref as Node3D).position.y - 0.72) > 0.01:
				said.append("ref_top is not at the kit's height")
			var carry: Node = inst.find_child("carry", true, false)
			if carry == null:
				said.append("no carry")
			elif (carry as Node3D).position.y < 0.1:
				said.append("carry is on the ground")
			for s in SOCKETS:
				if inst.find_child(s, true, false) == null:
					said.append("no " + s)
			var lit := false
			var low := INF
			var high := -INF
			for m in inst.find_children("*", "MeshInstance3D", true, false):
				var mi := m as MeshInstance3D
				var box: AABB = mi.transform * mi.get_aabb()
				low = minf(low, box.position.y)
				high = maxf(high, box.end.y)
				for i in mi.mesh.get_surface_count():
					var mat := mi.mesh.surface_get_material(i)
					if mat and String(mat.resource_name).begins_with("field"):
						lit = true
			if not lit:
				said.append("nothing of the field on it")
			if absf(low) > 0.02:
				said.append("does not stand on the ground (%.3f)" % low)
			if not body.has("held"):
				said.append("no held size in its body")
			var glb := FileAccess.open(path, FileAccess.READ)
			if glb and glb.get_length() >= 80000:
				said.append("over 80 KB (%d bytes)" % glb.get_length())
			count += 1
			if said.is_empty():
				print("%-28s stands %.2f over all, carried by %.2f, held %.2f m" % [id, high, (carry as Node3D).position.y, float(body.get("held", 0.0))])
			else:
				ok = false
				printerr(id, ": ", ", ".join(said))
			inst.free()
	print("items: %d forms, %s" % [count, "all good" if ok else "PROBLEMS"])
	quit(0 if ok else 1)


## Every form under a node, with the body it wears (its own keys over its parent's).
func _walk(n: Dictionary, out: Array, parent: Dictionary = {}) -> void:
	var body := parent.duplicate()
	for k in (n.get("body", {}) as Dictionary):
		body[k] = n["body"][k]
	out.append([n["id"], body])
	for key in ["prongs", "finishes"]:
		for c in n.get(key, []):
			_walk(c, out, body)
