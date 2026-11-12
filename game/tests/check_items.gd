## A check on the bodies of the items of power (the Lantern, the Astrolabe, the Bell): every
## form of the three must have a model of its own in game/assets/genius/forms, and the model
## must carry what the game and the contract rely on (docs/genius-lines.md): `ref_top`
## at the kit's height, `carry` (where a hand or a hook takes it), the usual sockets, a light
## of the field somewhere on it; it must stand on the ground and weigh under 120 KB.
##
## And the rule of the hand, for every genius that is held (data/genius.json, equipment.hand:
## the blade, the bow, the gun, the shield, the gauntlet and the three above): at the size the
## game holds it (GeniusEquip), every form is as long as its base says, give or take the
## tolerance; with all it has grown it reaches no further than `most`; and no form of any
## stage is larger than the line's Starter by more than the tolerance either way. A held
## genius grows by what it shows, never by how big it is.
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
			if glb and glb.get_length() >= 120000:
				said.append("over 120 KB (%d bytes)" % glb.get_length())
			count += 1
			if said.is_empty():
				print("%-28s stands %.2f over all, carried by %.2f, held %.2f m" % [id, high, (carry as Node3D).position.y, float(body.get("held", 0.0))])
			else:
				ok = false
				printerr(id, ": ", ", ".join(said))
			inst.free()
	print("items: %d forms, %s" % [count, "all good" if ok else "PROBLEMS"])
	var sized := _check_hand()
	quit(0 if ok and sized else 1)


## The rule of the hand: every held form, at the size the game gives it.
func _check_hand() -> bool:
	var rules: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/genius.json"))["equipment"]
	var tol := float(rules["tolerance"])
	var ok := true
	var count := 0
	for base: String in rules["hand"]:
		var h: Dictionary = rules["hand"][base]
		var b: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/genius-bases/%s.json" % base))
		if GeniusEquip.category_of(rules, base) == "":
			printerr(base, ": held, and in no category")
			ok = false
		var ids: Array = []
		_walk(b["settled"], ids)
		for p in b["paths"]:
			_walk(p, ids)
		var starter := 0.0
		var lo := INF
		var hi := 0.0
		for entry in ids:
			var id := String(entry[0])
			if not ResourceLoader.exists(DIR % id):
				printerr(id, ": no model")
				ok = false
				continue
			var inst: Node3D = (load(DIR % id) as PackedScene).instantiate()
			var m := GeniusEquip.sizing(rules, { "base": base, "body": entry[1] }, String(b["class"]), inst)
			inst.free()
			count += 1
			# what the rule measures of it, at the game's scale: its whole length, or its glove
			var size := float(m["natural"]) * float(m["k"])
			var said: Array[String] = []
			if float(m["long"]) > float(h["most"]) + 0.005:
				said.append("reaches %.2f, further than %.2f" % [m["long"], h["most"]])
			if size > float(h["long"]) * (1.0 + tol) + 0.005:
				said.append("is %.2f, larger than %.2f and the tolerance" % [size, h["long"]])
			# (smaller only where what it has grown had to be brought inside `most`)
			if size < float(h["long"]) * (1.0 - tol) - 0.005 and float(m["long"]) < float(h["most"]) - 0.005:
				said.append("is %.2f, smaller than %.2f and the tolerance" % [size, h["long"]])
			if starter == 0.0:
				starter = size
			elif size > starter * (1.0 + tol) / (1.0 - tol) + 0.005:
				said.append("is %.2f, and its Starter %.2f" % [size, starter])
			lo = minf(lo, size)
			hi = maxf(hi, size)
			if not said.is_empty():
				ok = false
				printerr(id, ": ", ", ".join(said))
		print("%-10s in the hand: its Starter %.2f, every form %.2f to %.2f (the rule: %.2f, give or take %d%%; nothing past %.2f)" % [base, starter, lo, hi, h["long"], roundi(tol * 100.0), h["most"]])
	print("held: %d forms, %s" % [count, "all good" if ok else "PROBLEMS"])
	return ok


## Every form under a node, with the body it wears (its own keys over its parent's).
func _walk(n: Dictionary, out: Array, parent: Dictionary = {}) -> void:
	var body := parent.duplicate()
	for k in (n.get("body", {}) as Dictionary):
		body[k] = n["body"][k]
	out.append([n["id"], body])
	for key in ["prongs", "finishes"]:
		for c in n.get(key, []):
			_walk(c, out, body)
