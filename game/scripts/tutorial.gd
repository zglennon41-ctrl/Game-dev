## The guided tutorial on a chained yard-wolf: move, strike, dodge, block and parry, the
## technique that breaks, the stance, and the Pattern.
class_name Tutorial
extends RefCounted

signal finished

var steps: Array = []
var i := 0
var n := 0
var note := ""
var last_note := ""
var _hold_until := 0
var _moved := 0.0
var fight: Fight
var world: World

func _init(f: Fight, w: World) -> void:
	fight = f
	world = w
	steps = [
		{ "title": "Move", "text": "[b]WASD[/b] moves; the [b]mouse[/b] turns the camera. [b]Tab[/b] locks on to a foe and back off. Walk to the yard-wolf on its chain.",
		  "enter": _enter_move, "on": _on_move, "frame": _frame_move },
		{ "title": "Strike", "text": "[b]Left click[/b] swings the sword. Keep pressing and the swings chain into a three-hit combo; the third hits hardest. Land a full combo.",
		  "on": _on_combo, "progress": _prog_combo },
		{ "title": "Dodge", "text": "[b]Space[/b] dodges in the direction you are moving (backward if you are still). For a moment in the middle of it, nothing can touch you. It costs 8 Will. Dodge twice.",
		  "on": _on_dodge, "progress": _prog_n2 },
		{ "title": "Block and parry", "text": "Now it bites. When it winds up it glows red, a [b]![/b] rises over it, and its reach shows on the ground. [b]Hold right click[/b] to block (most of the bite, and some Will). [b]Tap right click just before the bite lands[/b] to parry: no damage, Will back, and the wolf reels. Parry it twice.",
		  "enter": _enter_bite, "provoke": true, "on": _on_parry, "progress": _prog_n2 },
		{ "title": "A technique that breaks", "text": "[b]Q[/b] is Ground Strike, an Anchor technique: 18 Will, a short cooldown, a heavy blow. A beast breaks under techniques of the Shape opposite its own, and this wolf is a [b]Read[/b], the Anchor's opposite. Three Ground Strikes fill the gold diamonds and break it: it staggers, and takes more from everything.",
		  "enter": _enter_idle, "on": _on_break },
		{ "title": "The stance", "text": "[b]F[/b] takes the Anchor's Shape: you hit half again as hard and a bite cannot knock you back, but you move slower and it drains Will while you hold it. Take the stance, then leave it.",
		  "on": _on_stance, "progress": _prog_stance },
		{ "title": "The Pattern", "text": "Your Pattern is [b]Breaking Ground[/b]: its Trigger is [i]only after a perfect Hold[/i]; its Toll is [i]all my Will[/i]. Parry a bite, then press [b]R[/b]. A gold ring closes on you five times: [b]strike as it closes[/b], every time. Land all five and the Terms pay out. Miss one and it fizzles, and the Toll is still taken.",
		  "enter": _enter_bite, "provoke": true, "on": _on_pattern },
	]

func start(hud: Hud) -> void:
	i = 0
	_enter(hud)

func _enter_move() -> void:
	fight.passive = true
	fight.w_state = "idle"
	fight.w_pos = fight.p_pos + Vector2(6.0, -2.0)
	fight.p_lock = false
	world.lock_on = false

func _enter_bite() -> void:
	fight.passive = true
	fight.w_state = "idle"

func _enter_idle() -> void:
	fight.passive = true
	fight.w_state = "idle"

func _frame_move() -> void:
	pass

func _prog_combo() -> String: return "%d / 3" % n
func _prog_n2() -> String: return "%d / 2" % n
func _prog_stance() -> String: return ["take it", "now leave it"][mini(n, 1)]

func _on_move(e: Dictionary) -> bool:
	return false

func _on_combo(e: Dictionary) -> bool:
	if e["type"] == "hit" and not e["pattern"]:
		n = int(e["combo"]) + 1
	if e["type"] == "whiff":
		note = "Out of reach: step in closer."
	return n >= 3

func _on_dodge(e: Dictionary) -> bool:
	if e["type"] == "dodge":
		n += 1
	if e["type"] == "no-will":
		note = "Out of Will: wait a moment; it refills by itself."
	return n >= 2

func _on_parry(e: Dictionary) -> bool:
	if e["type"] == "parry":
		n += 1
		note = ""
	if e["type"] == "block":
		note = "Blocked: you held the guard too early. Tap it just as the bite lands."
	if e["type"] == "hurt":
		note = "Bitten (it does no harm here). Watch for the red glow and the !, then tap right click as it lunges."
	return n >= 2

func _on_break(e: Dictionary) -> bool:
	if e["type"] == "no-will":
		note = "Out of Will: step back and let it refill (4 a second)."
	if e["type"] == "whiff":
		note = "Out of reach: Ground Strike reaches a little farther than the sword, but not far."
	return e["type"] == "stagger"

func _on_stance(e: Dictionary) -> bool:
	if e["type"] == "stance":
		if e["on"]:
			n = 1
		elif n == 1:
			return true
	return false

func _on_pattern(e: Dictionary) -> bool:
	if e["type"] == "parry":
		note = "Parried: press R now, while the Trigger holds."
	if e["type"] == "pattern-fizzle":
		note = "It fizzled. Parry again and strike exactly as the gold ring meets the inner ring."
	return e["type"] == "pattern-done"

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
	if s.get("provoke", false) and fight.w_state == "idle" and fight.dist() < 3.5:
		fight.provoke()
	if Time.get_ticks_msec() < _hold_until:
		return
	var done := false
	if i == 0 and fight.dist() < 2.6:
		done = true
	for e in events:
		if done:
			break
		if s["on"].call(e):
			done = true
	if done:
		last_note = note
		i += 1
		if i >= steps.size():
			finished.emit()
			return
		_hold_until = Time.get_ticks_msec() + 700
		_enter(hud)
	var prog: String = steps[i]["progress"].call() if steps[i].has("progress") else ""
	hud.set_prompt_status(note, prog)
