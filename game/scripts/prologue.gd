## The night the field wakes: the world encounter, played. A director over the fight, like the
## tutorial, but told as a story: the line goes quiet, a cut-wolf comes, the field wakes, the
## Shape's technique comes on its own, the Pattern fires on instinct, and the wolf goes down.
class_name Prologue
extends RefCounted

signal finished

var fight: Fight
var world: World
var hero: Dictionary
var beat := 0
var hits := 0
var fizzles := 0
var _t := 0.0
var _hold_until := 0
var note := ""

func _init(f: Fight, w: World, h: Dictionary) -> void:
	fight = f
	world = w
	hero = h

static func fill(text: String, h: Dictionary) -> String:
	var b: Dictionary = Data.by_id(Data.bloods, h["blood"]) if h.get("blood", "") != "" else {}
	var kit: Dictionary = Data.kits[h["shape"]]
	var w: Dictionary = Data.by_id(Data.weapons, h["weapon"])
	var cities := { "columbia": "Outside Columbia", "cahokia": "Below Cahokia", "lunden": "Under Lunden" }
	return text.format({
		"name": h.get("name", ""), "blood": b.get("name", ""), "shape": String(h["shape"]).capitalize(),
		"weapon": w["name"].to_lower(), "technique": kit["technique"]["name"], "city": String(h["city"]).capitalize(),
		"stationcity": cities.get(h["city"], "On the line"), "pattern": Builder.sentence(h["pattern"]),
		"pattern_name": h["pattern"]["name"],
	})

func _beat_index(id: String) -> int:
	for i in Data.story["beats"].size():
		if Data.story["beats"][i]["id"] == id:
			return i
	return 0

func _beat_data() -> Dictionary:
	return Data.story["beats"][beat]

func start(hud: Hud) -> void:
	beat = 0
	fight.w_floor = 40.0
	fight.w_state = "absent"
	world.show_wolf = false
	fight.p_lock = false
	world.lock_on = false
	_enter(hud)

func _enter(hud: Hud) -> void:
	var b := _beat_data()
	var text := fill(b["text"], hero)
	if b["id"] == "pattern":
		var trig := ""
		var bar := ""
		for id in hero["pattern"]["terms"]:
			var k: String = PatternTerms.term(id)["kind"]
			if k == "trigger": trig = id
			if k == "bar": bar = id
		var hint: String = Data.story["trigger_hints"].get(trig, Data.story["trigger_hints"][""])
		if bar != "" and Data.story["bar_hints"].has(bar):
			hint += " " + Data.story["bar_hints"][bar]
		text = text.replace("{trigger_hint}", hint)
	hud.set_prompt(fill(b["title"], hero), text)
	note = ""
	_t = 0.0
	_hold_until = Time.get_ticks_msec() + 500

func _next(hud: Hud) -> void:
	beat += 1
	if beat >= Data.story["beats"].size():
		finished.emit()
		return
	_enter(hud)

func update(events: Array, dt: float, hud: Hud) -> void:
	if beat >= Data.story["beats"].size():
		return
	_t += dt
	var id: String = _beat_data()["id"]
	# The Pattern can come early, on instinct: then the story goes straight to the end.
	if id != "pattern" and id != "finish":
		for e in events:
			if e["type"] == "pattern-done":
				fight.w_floor = 0.0
				fight.w_hp = minf(fight.w_hp, 30.0)
				beat = _beat_index("finish")
				_enter(hud)
				return
	if Time.get_ticks_msec() < _hold_until:
		hud.set_prompt_status(note, "")
		return
	match id:
		"quiet":
			# The wolf comes out of the tunnel after a few seconds.
			if _t > 4.0:
				fight.respawn_from_arch = true
				fight._spawn_wolf()
				fight._choose_attack()
				world.show_wolf = true
				fight.p_lock = true
				world.lock_on = true
				_next(hud)
		"hold":
			for e in events:
				if e["type"] in ["parry", "block", "hurt", "evade", "turned"]:
					note = "You caught it clean." if e["type"] == "parry" else ""
					world.field_wakes(fight, hero)
					_next(hud)
					return
		"woke":
			for e in events:
				if e["type"] == "hit" and not e["pattern"]:
					hits += 1
			if hits >= 3:
				_next(hud)
		"technique":
			for e in events:
				if e["type"] == "technique":
					_next(hud)
					return
		"pattern":
			for e in events:
				if e["type"] == "pattern-done":
					# The Pattern lands: the wolf is beaten, near enough.
					fight.w_floor = 0.0
					fight.w_hp = minf(fight.w_hp, 30.0)
					_next(hud)
					return
				if e["type"] == "pattern-fizzle":
					fizzles += 1
					note = "It slipped away from you. Meet the Trigger again and strike as the ring closes." if fizzles < 2 else "It will come, one day. For now, fight."
					if fizzles >= 2:
						fight.w_floor = 0.0
						fight.w_hp = minf(fight.w_hp, 30.0)
						_next(hud)
						return
				if e["type"] == "bar-warning":
					note = "Your Bar forbids it, here and now. Make it so it does not."
				if e["type"] == "pattern-locked":
					note = "Not yet: %s." % String(e.get("trigger", "")).to_lower()
		"finish":
			if fight.w_state == "down":
				finished.emit()
				beat = 99
				return
			for e in events:
				if e["type"] == "wolf-down":
					finished.emit()
					beat = 99
					return
	hud.set_prompt_status(note, "")
