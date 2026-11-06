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
var story: Dictionary
var academy: Dictionary
var _reading: Dictionary
var _forms: Array
var _seeds: Array
var _features: Array
var _genius: Dictionary
var _adaptations: Array
var _secondary: Array
var _shades: Array
var _bodies: Dictionary
var discipline_kits: Dictionary
var _archetypes: Array
var _zones: Array
var disciplines: Array
var gear: Dictionary
var quests: Dictionary
var _crises: Array

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
	story = _load("res://data/story.json")
	academy = _load("res://data/academy.json")
	_reading = _load("res://data/reading.json")
	_forms = _load("res://data/forms.json")
	_seeds = _load("res://data/seeds.json")
	_features = _load("res://data/features.json")
	_genius = _load("res://data/genius.json")
	_adaptations = _load("res://data/adaptations.json")
	_secondary = _load("res://data/secondary-forms.json")
	_shades = _load("res://data/shades.json")
	_bodies = _load("res://data/genius-bodies.json")
	discipline_kits = _load("res://data/discipline-kits.json")
	_archetypes = _load("res://data/archetypes.json")
	_zones = _load("res://data/zones.json")
	disciplines = _load("res://data/disciplines.json")
	gear = _load("res://data/gear.json")
	quests = _load("res://data/quests.json")
	_crises = _load("res://data/crises.json")

func rules_reading() -> Dictionary: return _reading
func forms() -> Array: return _forms
func seeds() -> Array: return _seeds
func features() -> Array: return _features
func genius() -> Dictionary: return _genius
func adaptations() -> Array: return _adaptations
func secondary_forms() -> Array: return _secondary
func shades() -> Array: return _shades
func genius_bodies() -> Dictionary: return _bodies
func archetypes() -> Array: return _archetypes
func zones() -> Array: return _zones
func zone(id: String) -> Dictionary: return by_id(_zones, id)
func crises() -> Array: return _crises

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
