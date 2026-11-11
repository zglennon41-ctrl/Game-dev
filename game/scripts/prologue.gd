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
var sfx: Sfx = null
var music: Music = null
var _walked := 0.0
var _last_pos := Vector2.ZERO
var _wake_left := 0.0      # the camera stays on the hero this long while the field wakes
var _won := false

func _init(f: Fight, w: World, h: Dictionary) -> void:
	fight = f
	world = w
	hero = h

static func fill(text: String, h: Dictionary) -> String:
	var b: Dictionary = Data.by_id(Data.bloods, h["blood"]) if h.get("blood", "") != "" else {}
	var kit: Dictionary = Data.kits[h["shape"]]
	var w: Dictionary = Data.by_id(Data.weapons, h["weapon"])
	var cities := { "columbia": "Outside Columbia", "cahokia": "Below Cahokia", "lunden": "Under Lunden" }
	# how this weapon strikes: a blade swings, a gun shoots and reloads, a bow is drawn and loosed
	var st: Dictionary = Data.room["styles"].get(String(w.get("style", "")), {})
	var strike := "[b]left click[/b]"
	var strike_short := "Strike ([b]LMB[/b])"
	if String(st.get("kind", "")) == "ranged" and st.has("draw"):
		strike = "[b]hold left click[/b] to draw, and let go to loose"
		strike_short = "Draw and loose (hold [b]LMB[/b], then let go)"
	elif String(st.get("kind", "")) == "ranged":
		strike = "[b]left click[/b] to shoot; when it runs dry, [b]X[/b] reloads"
		strike_short = "Shoot ([b]LMB[/b]; [b]X[/b] reloads)"
	return text.format({
		"strike": strike, "strike_short": strike_short,
		"name": h.get("name", ""), "blood": b.get("name", ""), "shape": String(h["shape"]).capitalize(),
		"weapon": w["name"].to_lower(), "technique": kit["technique"]["name"], "city": String(h["city"]).capitalize(),
		"stationcity": cities.get(h["city"], "Outside %s" % String(h["city"]).capitalize()), "pattern": Builder.sentence(h["pattern"]),
		"pattern_name": h["pattern"]["name"], "stance": kit["stance"]["name"], "stance_text": kit["stance"]["text"],
		"technique_text": kit["technique"]["text"],
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
	world.genius_visible = false   # the genius is born when the field wakes
	fight.p_lock = false
	world.lock_on = false
	_last_pos = fight.p_pos
	_enter(hud)

## A word of the night's own (data/story.json, notes).
func _note(id: String) -> String:
	return fill(String(Data.story.get("notes", {}).get(id, "")), hero)

## The field wakes: the game's first great moment. Time slows, the camera comes in on the
## hero, the lamps of the platform catch one after another, the genius is born, and the wolf
## is thrown back and left open.
func _wake(hud: Hud, how: String) -> void:
	note = _note("wake_" + how)
	world.field_wakes(fight, hero)
	world.set_lamps(1.0, 2.6)
	var m: Dictionary = Data.story.get("moments", {}).get("wake", {})
	hud.banner(fill(String(m.get("title", "YOUR FIELD WAKES")), hero), fill(String(m.get("sub", "")), hero), World.SHAPE_COLORS.get(hero.get("shape", "anchor"), Color.WHITE), 2.4)
	if sfx:
		sfx.play("wake")
	if music:
		music.sting("rite")
	var away := fight.w_pos - fight.p_pos
	away = away.normalized() if away.length() > 0.01 else Vector2.RIGHT
	fight.w_pos = fight._clamp_in(fight.p_pos + away * maxf(3.4, fight.dist()))
	fight._wolf_set("recover", 1.8)
	# the camera comes in from where it is, low, and is given back
	var p3 := world._v3(fight.p_pos)
	var from := world._cam_pos - p3
	from.y = 0.0
	from = from.normalized() if from.length() > 0.1 else Vector3(0, 0, 1)
	world.cine = true
	world.cine_speed = 3.2
	world.cine_pos = p3 + from * 3.4 + Vector3(0, 1.0, 0)
	world.cine_look = p3 + Vector3(0, 1.45, 0)
	_wake_left = 1.9

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
	if _wake_left > 0.0:
		_wake_left -= dt
		if _wake_left <= 0.0:
			world.cine = false
	if beat >= Data.story["beats"].size():
		return
	_t += dt
	var id: String = _beat_data()["id"]
	var progress := ""
	# The Pattern can come early, on instinct: then the story goes straight to the end.
	if id != "pattern" and id != "finish":
		for e in events:
			if e["type"] == "pattern-done":
				if not world.genius_visible:
					world.field_wakes(fight, hero)
					world.set_lamps(1.0, 2.6)
				_pattern_landed(hud)
				beat = _beat_index("finish")
				_enter(hud)
				return
	if Time.get_ticks_msec() < _hold_until:
		hud.set_prompt_status(note, "")
		return
	match id:
		"quiet":
			# The wolf comes out of the tunnel once the player has found their feet (or has
			# stood long enough reading).
			_walked += (fight.p_pos - _last_pos).length()
			_last_pos = fight.p_pos
			var b := _beat_data()
			if (_walked >= float(b.get("walk", 2.5)) and _t > float(b.get("least", 3.0))) or _t > float(b.get("most", 12.0)):
				fight.respawn_from_arch = true
				fight._spawn_wolf()
				fight._choose_attack()
				world.show_wolf = true
				fight.p_lock = true
				world.lock_on = true
				if sfx:
					sfx.play("growl", 0.8, 2.0)
				if music:
					music.set_fight(true)
				_next(hud)
		"hold":
			for e in events:
				if e["type"] in ["parry", "block", "hurt", "evade", "turned"]:
					_wake(hud, String(e["type"]))
					_next(hud)
					return
		"woke":
			var need := int(_beat_data().get("hits", 3))
			for e in events:
				if e["type"] == "hit" and not e["pattern"]:
					hits += 1
				if e["type"] == "whiff":
					note = _note("whiff")
			progress = "%d / %d" % [mini(hits, need), need]
			if hits >= need:
				_next(hud)
				return
		"technique":
			for e in events:
				if e["type"] == "technique":
					_next(hud)
					return
				if e["type"] == "no-will":
					note = _note("no_will")
				if e["type"] == "not-ready":
					note = _note("not_ready")
		"pattern":
			# Nobody is kept at the station for want of a Trigger they cannot yet meet (a first
			# parry is hard): after a minute the night goes on without the Pattern.
			if _t > float(_beat_data().get("most", 60.0)) and fight.p_state != "pattern":
				note = _note("pattern_later")
				fight.w_floor = 0.0
				fight.w_hp = minf(fight.w_hp, 30.0)
				_next(hud)
				return
			for e in events:
				if e["type"] == "pattern-done":
					# The Pattern lands: the wolf is beaten, near enough.
					_pattern_landed(hud)
					_next(hud)
					return
				if e["type"] == "pattern-fizzle":
					fizzles += 1
					note = _note("pattern_slipped") if fizzles < 2 else _note("pattern_later")
					if fizzles >= 2:
						fight.w_floor = 0.0
						fight.w_hp = minf(fight.w_hp, 30.0)
						_next(hud)
						return
				if e["type"] == "bar-warning":
					note = _note("pattern_bar")
				if e["type"] == "pattern-locked":
					note = _note("pattern_locked").replace("{trigger}", String(e.get("trigger", "")).to_lower())
		"finish":
			if fight.w_state == "down":
				_won = true
			for e in events:
				if e["type"] == "wolf-down":
					_won = true
			if _won:
				beat = 99
				hud.set_prompt("", "")
				finished.emit()
				return
	hud.set_prompt_status(note, progress)

## The Pattern lands for the first time: its name across the screen, a held beat, the wolf all
## but beaten.
func _pattern_landed(hud: Hud) -> void:
	fight.w_floor = 0.0
	fight.w_hp = minf(fight.w_hp, 30.0)
	var m: Dictionary = Data.story.get("moments", {}).get("pattern", {})
	hud.banner(fill(String(m.get("title", "{pattern_name}")), hero).to_upper(), fill(String(m.get("sub", "")), hero), Style.GOLD, 2.0)
	world.slowmo(1.1, 0.3)
