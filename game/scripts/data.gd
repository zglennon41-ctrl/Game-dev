## The rules, as data. Reads data/*.json (the same files the simulator reads).
extends Node

var rules: Dictionary
var room: Dictionary
var beasts: Array
var shapes: Array
var wheel: Array
var terms: Array
var bloods: Array
var weapons: Array
var kits: Dictionary
var creation: Dictionary

func _init() -> void:
	rules = _load("res://data/rules.json")
	room = _load("res://data/combat-room.json")
	beasts = _load("res://data/beasts.json")
	shapes = _load("res://data/shapes.json")
	wheel = _load("res://data/wheel.json")["order"]
	terms = _load("res://data/terms.json")
	bloods = _load("res://data/bloods.json")
	weapons = _load("res://data/weapons.json")
	kits = _load("res://data/shape-kits.json")
	creation = _load("res://data/creation.json")

func _load(path: String) -> Variant:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Cannot open %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed == null:
		push_error("Bad JSON in %s" % path)
		return {}
	return parsed

func by_id(list: Array, id: String) -> Dictionary:
	for x in list:
		if x["id"] == id:
			return x
	push_error("Unknown id: %s" % id)
	return {}

func shape(id: String) -> Dictionary:
	return by_id(shapes, id)

func beast(id: String) -> Dictionary:
	return by_id(beasts, id)

## The Shape opposite on the wheel: the counter.
func opposite(s: String) -> String:
	var i := wheel.find(s)
	return wheel[(i + wheel.size() / 2) % wheel.size()]

func beat_window_ms(line: String) -> float:
	var c: Dictionary = rules["combat"]
	return c["beatWindowMsGreen"] if line == "green" else c["beatWindowMs"]
