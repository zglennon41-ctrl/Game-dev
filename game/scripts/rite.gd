## The rite's reading, pure: what Shape the bowl finds, and what First Form the genius takes.
## The same hero, record and seed always read the same; the numbers are in data/academy.json
## ("rite") and data/reading.json ("firstFormWeights", "leans").
class_name Rite
extends RefCounted

## The Shape: the questionnaire's leans (nudged by the spark), how the Academy has been played
## so far, and the bowl's own noise. { shape, was, surprise, scores }.
static func read_shape(hero: Dictionary, record: Dictionary, seed_value: int) -> Dictionary:
	var cfg: Dictionary = Data.academy["rite"]
	var answers: Array = hero.get("answers", [])
	var scores := {}
	if not answers.is_empty():
		var t := Creation.tally_with(answers, int(hero.get("spark", 0)))
		var top := 0.0
		for s in Creation.SHAPES:
			top = maxf(top, float(t["shape"].get(s, 0.0)))
		for s in Creation.SHAPES:
			scores[s] = float(t["shape"].get(s, 0.0)) / maxf(top, 0.001)
	else:
		for s in Creation.SHAPES:
			scores[s] = 0.0
	# The questionnaire's own pick is where the reading starts.
	var was: String = hero["shape"]
	scores[was] = maxf(float(scores[was]), 1.0)
	var lean := {}
	for thing in cfg["recordLeans"]:
		var n := float(record.get(thing, 0))
		for s in cfg["recordLeans"][thing]:
			lean[s] = float(lean.get(s, 0.0)) + n * float(cfg["recordLeans"][thing][s])
	for s in lean:
		scores[s] = float(scores.get(s, 0.0)) + minf(float(lean[s]), float(cfg["recordCap"]))
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	for s in Creation.SHAPES:
		scores[s] = float(scores[s]) + rng.randf() * float(cfg["noise"])
	var best := was
	for s in Creation.SHAPES:
		if float(scores[s]) > float(scores[best]):
			best = s
	return { "shape": best, "was": was, "surprise": best != was, "scores": scores }

## The First Form: the Reading of the Seed, the blood and the Shape (genius_reading.gd), with
## a little of the bowl's chance (rite.formNoise), settled on the best fit.
static func first_form(hero: Dictionary, shape: String, seed_value: int) -> Dictionary:
	var origin := { "seed": String(hero.get("seed", "")), "blood": String(hero.get("blood", "")), "shape": shape }
	var r := GeniusReading.read(1, GeniusReading.empty_tally(), origin, {}, float(Data.academy["rite"]["formNoise"]), seed_value * 31 + 7)
	var c: Dictionary = r["candidates"][0]
	return { "form": c["form"], "name": c["name"], "expression": c["expression"], "silhouette": c["silhouette"],
		"features": c["features"], "score": c["score"], "seedMark": c["seedMark"], "reading": r }

## The hero's genius after the rite: born in the First Form the bowl read, and named.
static func birth(hero: Dictionary, reading: Dictionary, genius_name: String) -> Genius:
	var g := Genius.for_hero(hero)
	g.pending_reading = reading.duplicate(true)
	g.pending_reading["unlockedBy"] = "rite"
	g.take()
	g.milestone("rite")
	g.name = genius_name
	g.save_to(hero)
	return g

## Apply a new Shape to the hero: the kit changes, and the Pattern's Form becomes the new
## Shape's Form with the same effect (strikes, guard, mend), keeping its Terms.
static func reshape(hero: Dictionary, shape: String) -> void:
	if hero["shape"] == shape:
		return
	var old_kit: Dictionary = Data.kits[hero["shape"]]
	var effect := "strikes"
	var p: Dictionary = hero["pattern"]
	if old_kit["forms"].has(p["form"]):
		effect = old_kit["forms"][p["form"]]["effect"]
	var kit: Dictionary = Data.kits[shape]
	var form_id: String = kit["forms"].keys()[0]
	for fid in kit["forms"]:
		if kit["forms"][fid]["effect"] == effect:
			form_id = fid
			break
	p["form"] = form_id
	p["name"] = kit["forms"][form_id]["name"]
	hero["shape_asked"] = hero["shape"]
	hero["shape"] = shape

## A feature's words, for the reveal.
static func feature_label(id: String) -> String:
	for f in Data.features():
		if f["id"] == id:
			return f.get("label", id)
	return id.replace("-", " ")
