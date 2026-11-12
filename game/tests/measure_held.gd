## Measures every form of the held geniuses (data/genius.json, equipment.hand) as the game
## holds it: the longest side of the model in the frame of the empty it is taken by (grip,
## wear, carry), as it was made and at the scale the game gives it (GeniusEquip). Prints one
## line a form and a table by base and stage. With --json=<path> writes the numbers.
## Run: godot --headless --path . -s res://game/tests/measure_held.gd
extends SceneTree

const DIR := "res://game/assets/genius/forms/%s.glb"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var data: Node = root.get_node("Data")
	var out := {}
	for base: String in data.genius()["equipment"]["hand"]:
		var by_level := { 1: [], 2: [], 3: [], 4: [] }
		var made_level := { 1: [], 2: [], 3: [], 4: [] }
		for f: Dictionary in data.tree_of(base):
			var id := String(f["id"])
			if not ResourceLoader.exists(DIR % id):
				continue
			var inst: Node3D = (load(DIR % id) as PackedScene).instantiate()
			var m := GeniusEquip.sizing(data.genius()["equipment"], f, String(data.base(base)["class"]), inst)
			inst.free()
			var level := int(f["level"])
			var box: AABB = m["box"]
			var made := maxf(box.size.x, maxf(box.size.y, box.size.z))
			out[id] = { "level": level, "made": made, "held": m["long"], "k": m["k"] }
			(by_level[level] as Array).append(m["long"])
			(made_level[level] as Array).append(made)
			print("%-30s L%d  made %.2f  held %.2f  (k %.2f)" % [id, level, made, m["long"], m["k"]])
		var line := "== %-10s held" % base
		var line2 := "== %-10s made" % base
		for lv in [1, 2, 3, 4]:
			if (by_level[lv] as Array).is_empty():
				continue
			line += "  L%d %.2f..%.2f" % [lv, (by_level[lv] as Array).min(), (by_level[lv] as Array).max()]
			line2 += "  L%d %.2f..%.2f" % [lv, (made_level[lv] as Array).min(), (made_level[lv] as Array).max()]
		print(line2)
		print(line)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--json="):
			var f := FileAccess.open(a.trim_prefix("--json="), FileAccess.WRITE)
			f.store_string(JSON.stringify(out, " "))
	quit(0)
