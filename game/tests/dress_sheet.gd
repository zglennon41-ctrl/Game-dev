extends Node
## The dress of the thirteen homes, to look at (docs/bodies-plan.md, "Dress as culture"): every
## home's people as the game draws them, on a plain ground and seen flat.
##   xvfb-run -a -s "-screen 0 2600x1400x24" godot --path . --resolution 2600x1400 \
##       res://game/tests/dress_sheet.tscn -- OUT_DIR [what] [key=value ...]
## what: homes (default: a row each for the men from the front, the men from behind, the women
## from the front and from behind), masters (the Academy's instructors, front and behind),
## options (each home's dress options side by side), motion (one home in a walk, a swing and a
## dodge, from behind: home=<id>).
## It saves sheet.png and mask.png (the same as white shapes on black: the test of a silhouette).
## Keys: dress=<option id> (every figure wears it), rank=<rank>, anim=<clip>, at=<0..1>,
## home=<id>, sex=<m|f>.

const HIGH := 300.0
const HOMES := ["alexandria", "columbia", "cahokia", "lunden", "colonia", "tiber", "khemet", "baghdad", "varanasi", "jiangnan", "kazan", "timbuktu", "edo"]

var world: World
var bodies: Array = []

func _ready() -> void:
	_run.call_deferred()

func _figure(body: String, look: Dictionary, col: int, row: int, cols: int, rows: int, turn: float, anim: String, at: float, cell: Vector2) -> void:
	var n: Node3D = Shapes.wake(load(world._person_model(body)).instantiate())
	world.add_child(n)
	world.toonify(n)
	world.dress(n, look, {})
	n.position = Vector3((col - (cols - 1) / 2.0) * cell.x, HIGH - row * cell.y, 0)
	n.rotation.y = turn
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation(anim):
		ap.play(anim)
		ap.seek(ap.get_animation(anim).length * at, true)
		ap.pause()
	bodies.append(n)

func _run() -> void:
	var root := get_tree().root
	await get_tree().process_frame
	var args := OS.get_cmdline_user_args()
	var out: String = args[0] if args.size() > 0 else "user://dress"
	var what: String = args[1] if args.size() > 1 and not args[1].contains("=") else "homes"
	var kv := {}
	for a in args:
		if a.contains("="):
			kv[a.get_slice("=", 0)] = a.get_slice("=", 1)
	if what == "wear":      # what every home offers slot by slot, in words (no picture)
		for h in HOMES:
			for slot in Data.creation["look"]["slots"]["order"]:
				for sx in ["m", "f"]:
					var names: Array = Creation.wear_options(h, slot, sx).map(func(o): return "%s=%s" % [o["id"], o["name"]])
					if not names.is_empty():
						print("%-11s %-6s on %s: %s" % [h, slot, sx, " | ".join(names)])
		get_tree().quit()
		return
	DirAccess.make_dir_recursive_absolute(out)
	world = World.new()
	root.add_child(world)
	world.set_place("cut")
	world.build_hero(Fight.default_hero())
	world._player.visible = false
	world.show_wolf = false
	world.genius_visible = false
	if world._wolf:
		world._wolf.visible = false
	world._env.fog_enabled = false
	world._env.background_mode = Environment.BG_COLOR
	world._env.background_color = Color(0.085, 0.08, 0.075)
	world._env.glow_bloom = 0.0
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-32, 28, 0)
	key.light_color = Color(1.0, 0.93, 0.82)
	key.light_energy = 0.36
	world.add_child(key)
	var cool := DirectionalLight3D.new()
	cool.rotation_degrees = Vector3(-12, -70, 0)
	cool.light_color = Color(0.62, 0.7, 0.95)
	cool.light_energy = 0.14
	world.add_child(cool)
	var anim := String(kv.get("anim", "Idle"))
	var at := float(kv.get("at", "0.0"))
	var base := { "headgear": true, "cape": false, "hair": "crop", "beard": "none", "hair_color": "brown", "build": 0.0, "stature": 1.0 }
	if kv.has("dress"):
		base["dress"] = kv["dress"]
	if kv.has("rank"):
		base["rank"] = kv["rank"]
	# the body's measures and anything else of the look, on every figure: weight=1 frame=0.5 age=1 hair=locs
	for k in ["build", "weight", "frame", "age", "stature"]:
		if kv.has(k):
			base[k] = float(kv[k])
	for k in ["hair", "hair_color", "beard", "skin"]:
		if kv.has(k):
			base[k] = kv[k]
	if kv.has("headgear"):
		base["headgear"] = kv["headgear"] == "1"
	if kv.has("wear"):      # wear=head:scarf,top:f
		var w := {}
		for pair in String(kv["wear"]).split(","):
			w[pair.get_slice(":", 0)] = pair.get_slice(":", 1)
		base["wear"] = w
	var cell := Vector2(1.25, 2.3)
	var cols := 13
	var rows := 4
	const FRONT := 0.45
	const BACK := PI - 0.6
	match what:
		"homes":
			for i in HOMES.size():
				var home: Dictionary = Data.bodies[HOMES[i]]
				var tones: Array = home.get("palette", ["olive"])
				for r in 4:
					var sex := "m" if r < 2 else "f"
					var look := base.duplicate()
					look["skin"] = tones[tones.size() / 2]
					look["hair"] = "crop" if sex == "m" else "tail"
					_figure("%s-%s" % [HOMES[i], sex], look, i, r, cols, rows, FRONT if r % 2 == 0 else BACK, anim, at, cell)
		"covers":
			# every home's people in each covering any head may wear (data/creation.json,
			# look.coverings): the men then the women, from the front
			# (back=1: from behind; side=1: from the side)
			var cvs: Array = (Data.creation["look"].get("coverings", []) as Array).map(func(c): return String(c["id"]))
			rows = cvs.size() * 2
			cell = Vector2(1.25, 2.3)
			for i in HOMES.size():
				var tones: Array = Data.bodies[HOMES[i]].get("palette", ["olive"])
				for r in rows:
					var sex := "m" if r < cvs.size() else "f"
					var look := base.duplicate()
					look.merge({ "skin": tones[tones.size() / 2], "hair": "long", "headgear": true, "wear": { "head": cvs[r % cvs.size()] } }, true)
					_figure("%s-%s" % [HOMES[i], sex], look, i, r, cols, rows, (PI - 0.6 if kv.has("back") else (1.5 if kv.has("side") else FRONT)), anim, at, cell)
		"hair", "heads":
			# heads, close: one row of one home's people (home=<id> sex=<m|f>), from the front, or
			# back=1 from behind, or side=1. hair: every hair style the creator offers, bare-headed
			# (first=10 count=10 for some of them). heads: everything the home may wear on the head
			# (its own headgear in both cuts, the coverings, bare), over hair=<style>.
			# The body hangs out of the picture: a window about 2600x420 fits ten.
			var hhome := String(kv.get("home", "timbuktu"))
			var hsex := String(kv.get("sex", "f"))
			var htones: Array = Data.bodies[hhome].get("palette", ["olive"])
			var looks: Array = []
			if what == "hair":
				var styles: Array = Data.creation["look"]["hair"]
				if kv.has("first"):
					styles = styles.slice(int(kv["first"]), int(kv["first"]) + int(kv.get("count", "10")))
				for st in styles:
					looks.append({ "hair": st, "headgear": false })
			else:
				for o in Creation.wear_options(hhome, "head", hsex):
					looks.append({ "headgear": String(o["id"]) != "none", "wear": { "head": String(o["id"]) } })
			cols = looks.size()
			rows = 1
			cell = Vector2(0.66, 0.84)
			for i in looks.size():
				var look := base.duplicate()
				look.merge({ "skin": kv.get("skin", htones[htones.size() / 2]), "hair_color": kv.get("hair_color", (Data.bodies[hhome].get("hairColors", ["black"]) as Array)[0]) }, true)
				look.merge(looks[i], true)
				_figure("%s-%s" % [hhome, hsex], look, i, 0, cols, rows, (PI - 0.6 if kv.has("back") else (1.5 if kv.has("side") else FRONT)), anim, at, cell)
				(bodies[-1] as Node3D).position.y -= 1.95      # the head, not the feet, in the picture
		"cuts":
			# every home's two cuts mixed (docs/representation-plan.md): each body in its own cut,
			# then with the other cut's top, the other's legs and feet, and the whole other cut;
			# the men then the women (back=1 for behind)
			rows = 8
			cell = Vector2(1.25, 2.3)
			var mixes := [[], ["top"], ["legs", "feet"], ["head", "top", "legs", "feet", "outer", "extra"]]
			for i in HOMES.size():
				var tones: Array = Data.bodies[HOMES[i]].get("palette", ["olive"])
				for r in 8:
					var sex := "m" if r < 4 else "f"
					var look := base.duplicate()
					look["skin"] = tones[tones.size() / 2]
					look["hair"] = "crop" if sex == "m" else "tail"
					var w := {}
					for slot in mixes[r % 4]:
						w[slot] = "f" if sex == "m" else "m"
					look["wear"] = w
					_figure("%s-%s" % [HOMES[i], sex], look, i, r, cols, rows, FRONT if not kv.has("back") else BACK, anim, at, cell)
		"builds":
			# one home's people in every build the creator names, then old, then old and heavy:
			# the men from the front and behind, the women from the front and behind (home=<id>)
			var bhome := String(kv.get("home", "alexandria"))
			var named: Array = (Data.creation["look"].get("frame", {}).get("presets", []) as Array).duplicate()
			named.append({ "id": "old", "age": 1.0 })
			named.append({ "id": "old-heavy", "age": 1.0, "weight": 1.0 })
			named.append({ "id": "short", "stature": 0.88, "weight": 0.5 })
			named.append({ "id": "tall", "stature": 1.12, "weight": -0.5 })
			if kv.has("pick"):      # only these builds, larger: pick=heavy,big,old
				var want := String(kv["pick"]).split(",")
				named = named.filter(func(b): return want.has(String(b["id"])))
			cols = named.size()
			cell = Vector2(1.45, 2.75)
			var btones: Array = Data.bodies[bhome].get("palette", ["olive"])
			for i in named.size():
				for r in 4:
					var sex := "m" if r < 2 else "f"
					var look := base.duplicate()
					look["skin"] = btones[btones.size() / 2]
					for k in ["build", "weight", "frame", "age", "stature"]:
						look[k] = float(named[i].get(k, base.get(k, 0.0 if k != "stature" else 1.0)))
					if not kv.has("hair"):
						look["hair"] = "crop" if sex == "m" else "tail"
					if float(look["age"]) > 0.5 and not kv.has("hair_color"):
						look["hair_color"] = "grey"
					_figure("%s-%s" % [bhome, sex], look, i, r, cols, rows, FRONT if r % 2 == 0 else BACK, anim, at, cell)
		"masters":
			var ins: Array = Data.academy["instructors"]
			cols = ins.size()
			rows = 2
			cell = Vector2(1.25, 2.3)
			for i in ins.size():
				var d: Dictionary = ins[i]
				var look: Dictionary = world.look_for(String(d["name"]))
				look.merge({ "dress": "master", "headgear": true, "cape": false }, true)      # as academy.gd dresses them
				if d.has("look"):
					look.merge(d["look"], true)
				for r in 2:
					_figure(String(d["body"]), look, i, r, cols, rows, FRONT if r == 0 else BACK, anim, at, cell)
		"options":
			var sex := String(kv.get("sex", "m"))
			var most := 1
			for h in HOMES:
				most = maxi(most, (Data.bodies[h].get("dress", {}).get("options", []) as Array).size())
			rows = most + 1
			for i in HOMES.size():
				var home: Dictionary = Data.bodies[HOMES[i]]
				var opts: Array = home.get("dress", {}).get("options", [])
				var tones: Array = home.get("palette", ["olive"])
				for r in rows:
					if r > opts.size():
						continue
					var look := base.duplicate()
					look["skin"] = tones[tones.size() / 2]
					if r == opts.size():
						look["rank"] = "master"
					else:
						look["dress"] = String(opts[r]["id"])
					_figure("%s-%s" % [HOMES[i], sex], look, i, r, cols, rows, FRONT if not kv.has("back") else BACK, anim, at, cell)
		"motion":
			var home := String(kv.get("home", "columbia"))
			var clips := [["Idle", 0.0], ["Walking_A", 0.25], ["Running_A", 0.3], ["Running_A", 0.8], ["1H_Melee_Attack_Slice_Horizontal", 0.45], ["1H_Melee_Attack_Chop", 0.4], ["Dodge_Forward", 0.5], ["Dodge_Left", 0.5], ["Blocking", 0.5], ["2H_Melee_Attack_Spin", 0.5], ["Spellcasting", 0.5], ["Sit_Chair_Idle", 0.5], ["Hit_A", 0.4]]
			cols = clips.size()
			rows = 4
			cell = Vector2(1.9, 2.3)
			for i in clips.size():
				for r in 4:
					var sex := "m" if r < 2 else "f"
					var look := base.duplicate()
					if kv.has("cape"):
						look["cape"] = true
					_figure("%s-%s" % [home, sex], look, i, r, cols, rows, BACK if r % 2 == 0 else FRONT, String(clips[i][0]), float(clips[i][1]), cell)
	var cam := Camera3D.new()
	world.add_child(cam)
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	var vp := get_viewport().get_visible_rect().size
	var mid := Vector3(0, HIGH - (rows - 1) / 2.0 * cell.y + (0.98 if not (what in ["hair", "heads"]) else 0.25), 0)
	cam.size = maxf(rows * cell.y, cols * cell.x * vp.y / vp.x)
	cam.far = 400.0
	cam.position = mid + Vector3(0, 0.0, 60.0)
	cam.look_at(mid)
	cam.make_current()
	for i in 20:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	root.get_viewport().get_texture().get_image().save_png("%s/sheet.png" % out)
	var white := StandardMaterial3D.new()
	white.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	white.albedo_color = Color.WHITE
	for b in bodies:
		for m in (b as Node).find_children("*", "MeshInstance3D", true, false):
			(m as MeshInstance3D).material_override = white
			(m as MeshInstance3D).material_overlay = null
	world._env.background_color = Color.BLACK
	world._env.glow_enabled = false
	world._env.adjustment_enabled = false
	for i in 3:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	root.get_viewport().get_texture().get_image().save_png("%s/mask.png" % out)
	print("DRESS SHEET ", out, " ", what, " ", bodies.size(), " figures")
	get_tree().quit()
