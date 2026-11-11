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
var _bases: Array          # the bases of the genius tree (data/genius-bases/*.json)
var _forms: Array          # every form of every base, flattened
var _form_index: Dictionary
var _hybrid_cache: Dictionary
var _homes: Dictionary     # each home's lean on the bases (data/genius-homes.json)
var _hybrids: Dictionary   # the rule that composes a hybrid, and pairs written by hand
var _seeds: Array
var _features_file: Array  # data/features.json
var _features: Array       # those and every base's newFeatures
var _genius: Dictionary
var _adaptations: Array
var _secondary: Array
var _shades: Array
var _bodies: Dictionary
var _looks: Dictionary   # what makes one genius unlike another of its form (data/genius-looks.json)
var _types: Dictionary   # the three types of genius: what each base does beside its partner (data/genius-types.json)
var discipline_kits: Dictionary
var _archetypes: Array
var _zones: Array
var disciplines: Array
var gear: Dictionary
var music: Dictionary
var emblems: Dictionary   # the emblems the creator's cards draw (data/emblems.json)
var bodies: Dictionary   # the thirteen homes' faces and palettes (data/bodies.json)
var people_features: Dictionary   # what a body can take: a blood's marks, trim, the changes of instars (data/people-features.json)
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
	_seeds = _load("res://data/seeds.json")
	_features_file = _load("res://data/features.json")
	_homes = _load("res://data/genius-homes.json")
	_hybrids = _load("res://data/genius-hybrids.json")
	use_bases(load_bases())
	_genius = _load("res://data/genius.json")
	_adaptations = _load("res://data/adaptations.json")
	_secondary = _load("res://data/secondary-forms.json")
	_shades = _load("res://data/shades.json")
	_bodies = _load("res://data/genius-bodies.json")
	_looks = _load("res://data/genius-looks.json")
	_types = _load("res://data/genius-types.json") if FileAccess.file_exists("res://data/genius-types.json") else {}
	discipline_kits = _load("res://data/discipline-kits.json")
	_archetypes = _load("res://data/archetypes.json")
	_zones = _load("res://data/zones.json")
	disciplines = _load("res://data/disciplines.json")
	gear = _load("res://data/gear.json")
	music = _load("res://data/music.json") if FileAccess.file_exists("res://data/music.json") else {}
	emblems = _load("res://data/emblems.json").get("emblems", {}) if FileAccess.file_exists("res://data/emblems.json") else {}
	bodies = _load("res://data/bodies.json").get("homes", {}) if FileAccess.file_exists("res://data/bodies.json") else {}
	people_features = _load("res://data/people-features.json").get("features", {}) if FileAccess.file_exists("res://data/people-features.json") else {}
	quests = _load("res://data/quests.json")
	_crises = _load("res://data/crises.json")

func rules_reading() -> Dictionary: return _reading

# --- The genius tree (docs/genius-tree.md) ---------------------------------------------

## Read every base in a folder (data/genius-bases by default), in the order of their ids.
func load_bases(dir := "res://data/genius-bases") -> Array:
	var out: Array = []
	var names: Array = []
	for f in DirAccess.get_files_at(dir):
		# an exported game lists a folder's files with .remap or .import after them
		var n := String(f).trim_suffix(".remap")
		if n.ends_with(".json") and not names.has(n):
			names.append(n)
	names.sort()
	for n in names:
		var b: Variant = _load("%s/%s" % [dir, n])
		if b is Dictionary and not (b as Dictionary).is_empty():
			out.append(b)
	return out

## Set the bases the rules run on (the game's own by default; a test may add its own).
func use_bases(list: Array) -> void:
	_bases = list.duplicate()
	_bases.sort_custom(func(a, b): return String(a["id"]) < String(b["id"]))
	_forms = []
	_form_index = {}
	_hybrid_cache = {}
	_features = _features_file.duplicate()
	var known := {}
	for f in _features:
		known[f["id"]] = true
	for b in _bases:
		for f in GeniusTree.flatten(b):
			_forms.append(f)
			_form_index[f["id"]] = f
		for nf in b.get("newFeatures", []):
			if not known.has(nf["id"]):
				known[nf["id"]] = true
				var feat: Dictionary = (nf as Dictionary).duplicate()
				if not feat.has("bonus"):
					feat["bonus"] = {}
				_features.append(feat)

## The bases, in the order of their ids.
func bases() -> Array: return _bases

func base(id: String) -> Dictionary:
	for b in _bases:
		if b["id"] == id:
			return b
	return {}

## Every form of every base, each base's settled form first. A hybrid's are asked for with form().
func forms() -> Array: return _forms

## The thirty forms of the hybrid of two bases.
func hybrid_forms(first: String, second: String) -> Array:
	var key := GeniusTree.hybrid_id(first, second)
	if not _hybrid_cache.has(key):
		var a := base(first)
		var b := base(second)
		var labels := {}
		for f in _features:
			labels[f["id"]] = f.get("label", f["id"])
		_hybrid_cache[key] = GeniusTree.compose(a, b, _hybrids, labels) if not a.is_empty() and not b.is_empty() and first != second else []
	return _hybrid_cache[key]

## A form by its id: a form of a base, or of a hybrid (first+second:form). {} if there is none.
func form(id: String) -> Dictionary:
	if _form_index.has(id):
		return _form_index[id]
	if not id.contains(":"):
		return {}
	var pair := id.split(":")[0].split("+")
	if pair.size() != 2:
		return {}
	for f in hybrid_forms(pair[0], pair[1]):
		if f["id"] == id:
			return f
	return {}

## The forms a form may become.
func children_of(id: String) -> Array:
	var out: Array = []
	for c in form(id).get("children", []):
		var f := form(String(c))
		if not f.is_empty():
			out.append(f)
	return out

## Every form of the tree a form is on, the settled one first (a hybrid's tree begins with its
## first base's settled form).
func tree_of(base_id: String) -> Array:
	if base_id.contains("+"):
		var pair := base_id.split("+")
		var a := base(pair[0])
		if a.is_empty():
			return []
		return [form(String(a["settled"]["id"]))] + hybrid_forms(pair[0], pair[1])
	return _forms.filter(func(f): return f["base"] == base_id)

## Each home's lean on the bases at the rite.
func genius_homes() -> Dictionary: return _homes
func genius_hybrids() -> Dictionary: return _hybrids
func seeds() -> Array: return _seeds
func features() -> Array: return _features
func genius() -> Dictionary: return _genius
func adaptations() -> Array: return _adaptations
func secondary_forms() -> Array: return _secondary
func shades() -> Array: return _shades
func genius_bodies() -> Dictionary: return _bodies
func genius_looks() -> Dictionary: return _looks
func genius_types() -> Dictionary: return _types

## Set the types the rules run on (the game's own by default; a test lays its own bases' over them).
func use_types(d: Dictionary) -> void:
	_types = d
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
