## The pulse room (Step 1): a title screen, the tutorial, two minutes with a cut-wolf.
## Command-line extras for automated checks (after --): --bot plays on the beat;
## --tutorial / --fight start straight in; --shots=DIR saves screenshots; --quit quits at results.
extends Node3D

var world := World.new()
var hud := Hud.new()
var pulse := Pulse.new()
var fight: Fight
var tutorial: Tutorial
var mode := "menu"   # menu, tutorial, fight, results
var fight_end := 0.0
var window_ms := 200.0
var _queue: Array = []
var _cam_mouse := Vector2.ZERO

# Automated checks.
var _args := {}
var _bot_last_beat := -1
var _bot_moves := {}
var _shot_n := 0
var _next_shot := 0.0

const ACTIONS := {
	"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT], "move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
	"strike": [KEY_J, KEY_SPACE], "ground_strike": [KEY_I, KEY_E], "hold": [KEY_K, KEY_SHIFT], "stance": [KEY_L, KEY_F],
	"lock_on": [KEY_TAB], "menu": [KEY_ESCAPE],
}
const MOUSE := { "strike": MOUSE_BUTTON_LEFT, "hold": MOUSE_BUTTON_RIGHT, "lock_on": MOUSE_BUTTON_MIDDLE }
const PAD := { "strike": JOY_BUTTON_A, "ground_strike": JOY_BUTTON_X, "hold": JOY_BUTTON_RIGHT_SHOULDER, "stance": JOY_BUTTON_Y, "lock_on": JOY_BUTTON_RIGHT_STICK, "menu": JOY_BUTTON_START }

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		var kv := String(a).trim_prefix("--").split("=", true, 1)
		_args[kv[0]] = kv[1] if kv.size() > 1 else true
	_setup_input()
	add_child(world)
	add_child(hud)
	pulse.force_ticks = _args.has("tickclock")
	add_child(pulse)
	window_ms = Settings.window_ms()
	if _args.has("shots"):
		DirAccess.make_dir_recursive_absolute(_args["shots"])
	if _args.has("tutorial"):
		start("tutorial")
	elif _args.has("fight"):
		start("fight")
	else:
		menu()

func _setup_input() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.2)
		for k in ACTIONS[action]:
			var e := InputEventKey.new()
			e.physical_keycode = k
			InputMap.action_add_event(action, e)
		if MOUSE.has(action):
			var m := InputEventMouseButton.new()
			m.button_index = MOUSE[action]
			InputMap.action_add_event(action, m)
		if PAD.has(action):
			var j := InputEventJoypadButton.new()
			j.button_index = PAD[action]
			InputMap.action_add_event(action, j)
	var b := InputEventJoypadButton.new()
	b.button_index = JOY_BUTTON_B
	InputMap.action_add_event("hold", b)
	for pair in [["move_left", JOY_AXIS_LEFT_X, -1.0], ["move_right", JOY_AXIS_LEFT_X, 1.0], ["move_up", JOY_AXIS_LEFT_Y, -1.0], ["move_down", JOY_AXIS_LEFT_Y, 1.0]]:
		var m := InputEventJoypadMotion.new()
		m.axis = pair[1]
		m.axis_value = pair[2]
		InputMap.action_add_event(pair[0], m)

# --- Screens ----------------------------------------------------------------

func menu() -> void:
	mode = "menu"
	pulse.stop()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var cal := roundi(Settings.calibration())
	hud.show_screen("WILDLINE", "The pulse room · an Anchor, a cut-wolf, the beat", "Sound on: the beat is in the music. Keyboard and mouse, or a gamepad.", [
		["Learn the pulse  (tutorial, about three minutes)", func(): start("tutorial")],
		["Fight the cut-wolf  (two minutes)", func(): start("fight")],
		["Beat window: %d ms %s" % [window_ms, "(Green line)" if window_ms == 200 else "(Amber and up)"], _toggle_window],
		["Timing calibration: %d ms%s" % [cal, "  ·  reset" if cal != 0 else ""], _reset_calibration],
		["Quit", func(): get_tree().quit()],
	])

func _toggle_window() -> void:
	window_ms = 150.0 if window_ms == 200.0 else 200.0
	Settings.save_window(window_ms)
	menu()

func _reset_calibration() -> void:
	Settings.save_calibration(0.0)
	menu()

func start(which: String) -> void:
	var period := float(Data.shape(Data.room["player"]["shape"])["pulseMs"]) / 1000.0
	pulse.calibration_ms = Settings.calibration()
	pulse.start(period)
	fight = Fight.new({ "beast": "yard-wolf" if which == "tutorial" else "cut-wolf", "t0": pulse.t0, "period": period,
		"window_ms": window_ms, "seed": randi(), "passive": which == "tutorial", "respawn": true })
	world.show_wolf = true
	world.lock_on = true
	hud.hide_screen()
	hud.track.marks.clear()
	_queue.clear()
	_bot_last_beat = -1
	_next_shot = 0.0
	if not _args.has("bot"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	if which == "tutorial":
		mode = "tutorial"
		tutorial = Tutorial.new(fight, world, pulse)
		tutorial.finished.connect(_tutorial_done)
		tutorial.start(hud)
	else:
		mode = "fight"
		tutorial = null
		hud.set_prompt("", "")
		hud.set_prompt_status("", "")
		fight_end = pulse.t0 + float(Data.room["sessionSeconds"])
	world.draw(fight, 0.0, 0.016, Vector2.ZERO)
	world.snap_camera()

func _tutorial_done() -> void:
	pulse.play("done")
	mode = "results"
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var note := tutorial.last_note
	hud.show_screen("THE PULSE", "That is the whole of it: the beat, the stance, the strike, the technique that breaks, the parry.",
		("%s\n\n" % note if note != "" else "") + "A cut-wolf is coming out of the Cut. It circles, it commits, it bites on the beat. It does not stand still for you.", [
		["Fight it  (two minutes)", func(): start("fight")],
		["The tutorial again", func(): start("tutorial")],
		["Menu", menu],
	])
	if _args.has("bot"):
		_shot("tutorial-done")
		start.call_deferred("fight")

func _results(reason: String) -> void:
	pulse.stop()
	pulse.play("done")
	mode = "results"
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var s := fight.stats
	var pct := roundi(100.0 * s["perfect"] / maxf(1, s["inputs"]))
	var avg := 0.0
	for o in s["offsets"]:
		avg += o
	avg /= maxf(1, s["offsets"].size())
	var sub := "The wolf put you on the ties. On the line, the party would have sixty seconds to stand on you." if reason == "down" else "%d cut-%s felled." % [s["wolves_down"], "wolf" if s["wolves_down"] == 1 else "wolves"]
	var body := "[table=2]"
	for row in [["On the beat", "%d%% of %d inputs" % [pct, s["inputs"]]], ["Your timing", "%d ms %s on average" % [absi(roundi(avg)), "late" if avg >= 0 else "early"]],
			["Parries / blocks / bitten / dodged", "%d / %d / %d / %d" % [s["parries"], s["blocks"], s["hurts"], s["dodges"]]], ["Breaks into stagger", str(s["staggers"])],
			["Longest chain", str(s["longest_chain"])], ["Damage dealt", str(int(s["damage_dealt"]))], ["Fumbles", str(s["fumbles"])], ["Health left", str(roundi(fight.p_hp))]]:
		body += "[cell][color=#9a8c78]%s[/color]      [/cell][cell]%s[/cell]" % row
	body += "[/table]"
	hud.show_screen("DOWN" if reason == "down" else "TWO MINUTES", sub, body, [
		["Again", func(): start("fight")],
		["Tutorial", func(): start("tutorial")],
		["Menu", menu],
	])
	print("RESULTS ", JSON.stringify({ "reason": reason, "wolves": s["wolves_down"], "inputs": s["inputs"], "perfect": s["perfect"], "parries": s["parries"], "hurts": s["hurts"], "staggers": s["staggers"], "hp": fight.p_hp }))
	if _args.has("shots"):
		_shot.call_deferred("results")
	if _args.has("quit"):
		get_tree().create_timer(1.0).timeout.connect(get_tree().quit)

# --- Input ------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_cam_mouse += event.relative
	if mode != "tutorial" and mode != "fight":
		return
	if event.is_action_pressed("menu"):
		menu()
		return
	if event.is_action_pressed("lock_on"):
		world.lock_on = not world.lock_on
	if event is InputEventMouseButton and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not _args.has("bot"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	for pair in [["strike", "strike"], ["ground_strike", "ground-strike"], ["stance", "stance"], ["hold", "hold-down"]]:
		if event.is_action_pressed(pair[0], false, true):
			_queue.append([pair[1], pulse.input_time()])
	if event.is_action_released("hold", true):
		_queue.append(["hold-up", pulse.input_time()])

# --- Each frame -------------------------------------------------------------

func _process(dt: float) -> void:
	if mode != "tutorial" and mode != "fight":
		return
	if _args.has("bot"):
		_bot()
	for q in _queue:
		fight.input(q[0], q[1])
	_queue.clear()
	var t := pulse.now()
	var stick := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if _args.has("bot"):
		stick = _bot_stick()
	fight.update(t, world.move_from_stick(stick))
	var events := fight.drain()
	_sounds(events)
	world.feedback(events)
	for e in events:
		if e["type"] == "judged" and e["action"] != "hold-up":
			hud.track.mark(e["t"], e["j"]["perfect"])
	if tutorial:
		tutorial.update(events, hud)
	var cam := Vector2(Input.get_joy_axis(0, JOY_AXIS_RIGHT_X), Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y))
	cam += _cam_mouse * 0.12
	_cam_mouse = Vector2.ZERO
	world.draw(fight, t, dt, cam)
	hud.track.show_wolf = world.show_wolf
	var timer := ""
	var score := "the yard"
	if mode == "fight":
		var left := maxf(0.0, fight_end - t)
		timer = "%d:%02d" % [int(left) / 60, int(left) % 60]
		score = "wolves felled: %d" % fight.stats["wolves_down"]
	hud.update_play(fight, t, timer, score)
	pulse.mark_frame()
	if _args.has("shots") and t > _next_shot:
		_next_shot = t + float(_args.get("every", "6"))
		_shot("%s" % mode)
	if mode == "fight":
		if fight.p_down:
			_results("down")
		elif t >= fight_end:
			_results("time")

func _sounds(events: Array) -> void:
	for e in events:
		match e["type"]:
			"hit":
				if e["action"] == "ground-strike": pulse.play("heavy")
				if e["perfect"]: pulse.play("hit", pow(2.0, mini(e["chain"], 6) / 12.0))
				else: pulse.play("hit-off")
			"whiff": pulse.play("whiff")
			"fumble": pulse.play("fumble")
			"parry": pulse.play("parry")
			"block": pulse.play("block")
			"hurt": pulse.play("hurt")
			"windup": pulse.play("growl")
			"stagger": pulse.play("stagger")
			"stance": pulse.play("stance", 1.0 if e["on"] else 0.75)
			"wolf-down": pulse.play("fell")

func _shot(label: String) -> void:
	if not _args.has("shots"):
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	_shot_n += 1
	img.save_png("%s/%02d-%s.png" % [_args["shots"], _shot_n, label])

# --- The bot: plays on the beat, for automated checks ------------------------

func _bot() -> void:
	var t := pulse.now()
	var k := roundi((t - fight.t0) / fight.period)
	var to_beat := fight.beat_time(k) - t
	if k <= _bot_last_beat or to_beat > 0.006 or to_beat < -0.03:
		return
	_bot_last_beat = k
	var step := tutorial.i if tutorial else 99
	var it := t
	if fight.w_mode == "windup" and fight.w_strike_beat == k:
		_queue.append(["hold-down", it])
		_queue.append(["hold-up", it + 0.05])
	elif step == 2 and not fight.p_stance:
		_queue.append(["stance", it])
	elif step == 3 and fight.p_stance:
		_queue.append(["stance", it])
	elif step == 5:
		pass
	elif k > fight.p_last_action_beat:
		var gs := step == 4 or (step == 99 and fight.p_will > 70)
		_queue.append(["ground-strike" if gs else "strike", it])

func _bot_stick() -> Vector2:
	if not world.show_wolf:
		return Vector2.ZERO
	var d := fight.w_pos - fight.p_pos
	if d.length() < 1.3:
		return Vector2.ZERO
	# Convert the ground direction back into a stick direction for the camera.
	var fwd := Vector2(-sin(world.cam_yaw), -cos(world.cam_yaw))
	var right := Vector2(cos(world.cam_yaw), -sin(world.cam_yaw))
	var n := d.normalized()
	return Vector2(n.dot(right), -n.dot(fwd))
