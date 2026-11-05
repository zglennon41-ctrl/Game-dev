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

## The First Form: every form a first instar can take, scored by the Seed, the blood and the
## Shape's leans toward its Expression and its features, plus a little of the bowl's noise.
static func first_form(hero: Dictionary, shape: String, seed_value: int) -> Dictionary:
	var reading: Dictionary = Data.rules_reading()
	var w: Dictionary = reading["firstFormWeights"]
	var leans: Dictionary = reading["leans"]
	var keys := { "seed": String(hero.get("seed", "")), "blood": String(hero.get("blood", "")), "shape": shape }
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value * 31 + 7
	var noise := float(Data.academy["rite"]["formNoise"])
	var best: Dictionary = {}
	var best_score := -INF
	var forms: Array = Data.forms().filter(func(f): return int(f["instars"]["min"]) == 1)
	forms.sort_custom(func(a, b): return a["id"] < b["id"])
	for f in forms:
		var score := 0.0
		for line in keys:
			var lean: Dictionary = leans.get(line, {}).get(keys[line], {})
			if lean.is_empty():
				continue
			var s := float(lean.get("expression", {}).get(f["expression"], 0.0))
			for feat in f["features"]:
				s += float(lean.get("features", {}).get(feat, 0.0))
			score += float(w.get(line, 0.0)) * s
		score += rng.randf() * noise
		if score > best_score:
			best_score = score
			best = f
	var feats: Array = best["features"].duplicate()
	var seed_mark := ""
	for sd in Data.seeds():
		if sd["id"] == keys["seed"]:
			seed_mark = sd["seedMark"]
	if seed_mark != "" and not feats.has(seed_mark):
		feats.append(seed_mark)
	return { "form": best["id"], "name": best["name"], "expression": best["expression"], "silhouette": best["silhouette"],
		"features": feats, "score": best_score }

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
