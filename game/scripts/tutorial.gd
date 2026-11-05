## The guided tutorial: the pulse, then each verb, on a chained yard-wolf. Its first step also
## calibrates timing to the player's screen and speakers.
class_name Tutorial
extends RefCounted

signal finished

var steps: Array = []
var i := 0
var n := 0
var offsets: Array = []
var note := ""
var last_note := ""
var _hold_until := 0
var fight: Fight
var world: World
var pulse: Pulse

func _init(f: Fight, w: World, p: Pulse) -> void:
	fight = f
	world = w
	pulse = p
	steps = [
		{ "title": "Your field beats",
		  "text": "Listen. The ring at your feet closes on every beat, and the track below carries the beats to the line. Tap [b]J[/b] (or left click) with the click, eight times. This also tunes the game to your screen and speakers.",
		  "enter": _enter_listen, "on": _calibrate, "progress": _prog_calibrate },
		{ "title": "On the beat",
		  "text": "Inputs on the beat are [b]perfect[/b]. Off it, everything you do is worth 70%. Land four taps on the beat in a row. The marks under the track show where you landed: green on the beat, orange off it.",
		  "on": _on_beat, "progress": _prog_on_beat },
		{ "title": "Shape: the stance",
		  "text": "Press [b]L[/b] (or F) on the beat. Your field takes the Anchor's Shape: you hit half again as hard, you cannot be knocked back, you move slower, and it drains Will while you hold it. Off the beat, the stance comes a beat late. Press it again to leave.",
		  "on": _on_stance },
		{ "title": "Project: strike",
		  "text": "A yard-wolf on a chain. Walk to it ([b]WASD[/b]) and strike on the beat. On-beat strikes in a row build a chain that hits harder. One press per beat: a second press in the same beat fumbles. Build a chain of four.",
		  "enter": _enter_wolf, "on": _on_chain, "progress": _prog_chain },
		{ "title": "A technique: Ground Strike",
		  "text": "[b]I[/b] (or E) is Ground Strike, an Anchor technique. It costs 18 Will and hits hard. A beast breaks under techniques of the Shape opposite its own, and this wolf is a [b]Read[/b], the Anchor's opposite. Three Ground Strikes on the beat in a row break it: the gold pips over it fill, and it staggers. Wait a beat between strikes.",
		  "on": _on_break },
		{ "title": "Hold: the parry",
		  "text": "Now it will bite. When it winds up, it glows red, its reach shows on the ground, and a red mark rides the track toward the line. Press [b]K[/b] (or right click) on that beat: a [b]parry[/b]. No damage, 10 Will back, and the wolf reels. Holding the guard early only blocks, for half. Parry it twice.",
		  "enter": _enter_idle, "provoke": true, "on": _on_parry, "progress": _prog_parry },
	]

func _enter_listen() -> void:
	world.show_wolf = false
	world.lock_on = false
	fight.w_mode = "absent"

func _enter_wolf() -> void:
	world.show_wolf = true
	world.lock_on = true
	fight.passive = true
	fight.w_mode = "idle"

func _enter_idle() -> void:
	fight.passive = true
	fight.w_mode = "idle"

func _prog_calibrate() -> String: return "%d / 8" % n
func _prog_on_beat() -> String: return "%d / 4 in a row" % n
func _prog_chain() -> String: return "chain %d / 4" % n
func _prog_parry() -> String: return "%d / 2" % n

func _on_beat(e: Dictionary) -> bool:
	if e["type"] == "judged" and e["action"] == "strike":
		n = n + 1 if e["j"]["perfect"] else 0
	return n >= 4

func _on_stance(e: Dictionary) -> bool:
	return e["type"] == "stance" and e["on"]

func _on_chain(e: Dictionary) -> bool:
	if e["type"] == "hit":
		n = maxi(n, e["chain"])
	if e["type"] == "fumble" or (e["type"] == "hit" and not e["perfect"]):
		n = 0
	return n >= 4

func _on_break(e: Dictionary) -> bool:
	if e["type"] == "no-will":
		note = "Out of Will. Leave the stance and let it fill: open, the field regenerates 4 a second."
	if e["type"] == "hit" and e["action"] == "ground-strike" and not e["perfect"]:
		note = "Off the beat: that strike does not break. Land all three on the beat."
	return e["type"] == "stagger"

func _on_parry(e: Dictionary) -> bool:
	if e["type"] == "parry":
		n += 1
	if e["type"] == "block":
		note = "Blocked: that was a guard held early. Tap K exactly on the strike beat."
	if e["type"] == "hurt" or e["type"] == "dodge":
		note = "Watch the red mark on the track; tap K as it crosses the line."
	return n >= 2

func start(hud: Hud) -> void:
	i = 0
	_enter(hud)

func _calibrate(e: Dictionary) -> bool:
	if e["type"] != "judged" or e["action"] != "strike":
		return false
	offsets.append(e["j"]["offset_ms"])
	n = offsets.size()
	if n < 8:
		return false
	var last: Array = offsets.slice(-8)
	last.sort()
	var m: float = last[4]
	if absf(m) > 15.0:
		pulse.calibration_ms = clampf(pulse.calibration_ms + m, -200.0, 200.0)
		Settings.save_calibration(pulse.calibration_ms)
		note = "You tap %d ms %s on this device; the beat has been adjusted to you." % [absi(roundi(m)), "late" if m > 0 else "early"]
	else:
		note = "Your timing sits right on the beat on this device."
	return true

func _enter(hud: Hud) -> void:
	var s: Dictionary = steps[i]
	n = 0
	note = ""
	if s.has("enter"):
		s["enter"].call()
	hud.set_prompt("%d/%d · %s" % [i + 1, steps.size(), s["title"]], s["text"])

## Called every frame with the fight's events.
func update(events: Array, hud: Hud) -> void:
	if i >= steps.size():
		return
	var s: Dictionary = steps[i]
	if s.get("provoke", false) and fight.w_mode == "idle":
		fight.provoke()
	if Time.get_ticks_msec() < _hold_until:
		return
	for e in events:
		if s["on"].call(e):
			last_note = note
			i += 1
			if i >= steps.size():
				finished.emit()
				return
			_hold_until = Time.get_ticks_msec() + 600
			_enter(hud)
			break
	var prog: String = steps[i]["progress"].call() if steps[i].has("progress") else ""
	hud.set_prompt_status(note if note != "" else last_note, prog)
