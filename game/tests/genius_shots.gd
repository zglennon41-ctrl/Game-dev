extends Node
## A genius in a fight, to look at (docs/genius-combat.md): a steady hand plays the hero against
## the Warden with one genius on one order, and the frame after a given event is saved.
##   xvfb-run -a godot --path . res://game/tests/genius_shots.tscn -- FORM INSTAR ORDER EVENT OUT.png
## FORM is a form of the tree by its id (a base's, or a hybrid's: wolf+hawk:wolf-courser); with
## none, the first prong of the first base.   (EVENT: genius-move, genius-great, genius-hold, free, genius-guard)

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	var root := get_tree().root
	await get_tree().process_frame
	var args := OS.get_cmdline_user_args()
	var form_id: String = args[0] if args.size() > 0 else String(Genius.road_of(String(Data.bases()[0]["id"]))[2]["id"])
	var instar: int = int(args[1]) if args.size() > 1 else 3
	var order: String = args[2] if args.size() > 2 else "hunt"
	var want: String = args[3] if args.size() > 3 else "genius-move"
	var out: String = args[4] if args.size() > 4 else "user://genius-%s-%d-%s.png" % [form_id, instar, order]
	var g := Genius.at_form(form_id, instar)
	g.look = GeniusLook.born(4711)
	g.order = order
	g.name = ""
	var hero := Fight.default_hero()
	hero["stage"] = 3
	hero["projected"] = true
	g.save_to(hero)
	var world := World.new()
	root.add_child(world)
	var hud := Hud.new()
	root.add_child(hud)
	world.set_place("cut")
	world.build_hero(hero)
	var opts := { "hero": hero, "beast": "green-warden", "seed": 7, "respawn": false, "genius": g }
	if order == "hold":
		opts["post"] = Vector2(-1.0, 0.5)
	var f := Fight.new(opts)
	world.set_foe({ "wolf_scale": float(f.beast.get("modelScale", 1.0)), "model": String(f.beast.get("model", "")) })
	world.show_wolf = true
	world.reset_feedback()
	world.snap_camera(f)
	hud.configure(f, "Test")
	hud.hide_screen()
	hud.play_ui.visible = true
	var dt := 1.0 / 60.0
	var shot_at := -1.0
	var done := false
	for i in 60 * 40:
		var to_w := f.w_pos - f.p_pos
		var move := Vector2.ZERO
		if f.w_state == "windup" and f.w_duration - f.w_timer <= 0.1 and f.w_duration - f.w_timer > 0.1 - dt:
			f.input("block-down")
		if f.p_block_held and f.w_state != "windup":
			f.input("block-up")
		if to_w.length() < 2.4 and f.w_state in ["recover", "stagger", "flinch"] and not f.p_block_held:
			f.input("attack")
		if order != "hold" and to_w.length() > 2.0 and f.w_state != "windup" and f.w_state not in ["down", "absent"]:
			move = to_w.normalized()
		f.update(dt, move)
		var evs := f.drain()
		world.feedback(f, evs)
		world.draw(f, dt, Vector2.ZERO, move)
		hud.update_play(f, "", "", true)
		for e in evs:
			if shot_at < 0.0 and (f.now > 3.0 or want == "free") and String(e["type"]) == want:
				shot_at = f.now + 0.35
		if i % 12 == 0 or (shot_at > 0.0):
			await get_tree().process_frame
		if shot_at > 0.0 and f.now >= shot_at:
			await RenderingServer.frame_post_draw
			root.get_viewport().get_texture().get_image().save_png(out)
			print("SHOT ", out, " at ", f.now, " order ", f.g_order, " why ", f.g_free_why, " move ", f.g_move_now)
			done = true
			break
		if f.w_state == "down" or f.p_state == "down":
			break
	if not done:
		await RenderingServer.frame_post_draw
		root.get_viewport().get_texture().get_image().save_png(out)
		print("SHOT (end) ", out, " at ", f.now)
	get_tree().quit()
