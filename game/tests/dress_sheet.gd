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
	var mid := Vector3(0, HIGH - (rows - 1) / 2.0 * cell.y + 0.98, 0)
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
