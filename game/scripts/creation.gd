## The character creator's generator: answers become a character. Pure: the same answers and
## the same spark always make the same character; a new spark (every new character gets one)
## nudges the leans, so the same answers can make someone else. Every result carries its reasons.
class_name Creation
extends RefCounted

const SHAPES := ["anchor", "turn", "cast", "read", "bind", "make"]
## The Discipline a city teaches (data/disciplines.json).
static func discipline_of(city: String) -> String:
	for d in Data.disciplines:
		if d["city"] == city:
			return d["id"]
	return "marshal"

static func question(i: int) -> Dictionary:
	return Data.creation["questions"][i]

static func answer(qi: int, ai: int) -> Dictionary:
	return question(qi)["answers"][ai]

static func _add(into: Dictionary, from: Dictionary, why: String, reasons: Dictionary) -> void:
	for k in from:
		into[k] = float(into.get(k, 0.0)) + float(from[k])
		if float(from[k]) > 0.0:
			if not reasons.has(k):
				reasons[k] = []
			reasons[k].append(why)

static func _top(scores: Dictionary, among: Array = []) -> String:
	var best := ""
	var best_v := -INF
	for k in (among if among.size() > 0 else scores.keys()):
		var v := float(scores.get(k, 0.0))
		if v > best_v:
			best_v = v
			best = k
	return best

## Everything the answers point at, before any choice is made.
static func tally(answers: Array) -> Dictionary:
	var t := { "shape": {}, "tier": {}, "blood": {}, "style": {}, "effect": {}, "city": "", "seed": "",
		"trigger": "", "toll": "", "bar": "", "why": { "shape": {}, "tier": {}, "blood": {}, "style": {}, "effect": {} }, "lines": {} }
	for qi in answers.size():
		var a := answer(qi, int(answers[qi]))
		var why: String = a["why"]
		for key in ["shape", "tier", "blood", "style", "effect"]:
			if a.has(key):
				_add(t[key], a[key], why, t["why"][key])
		for key in ["city", "seed", "trigger", "toll", "bar"]:
			if a.has(key):
				t[key] = a[key]
				t["lines"][key] = why
	return t

## The tally, nudged by the spark: each lean moves by up to `jitter` either way. Spark 0: no nudge.
static func tally_with(answers: Array, spark: int) -> Dictionary:
	var t := tally(answers)
	if spark == 0:
		return t
	var rng := RandomNumberGenerator.new()
	rng.seed = spark
	var j := float(Data.creation.get("spark", {}).get("jitter", 0.3))
	for key in ["shape", "tier", "blood", "style", "effect"]:
		var d: Dictionary = t[key]
		var keys: Array = d.keys()
		keys.sort()
		for k in keys:
			d[k] = float(d[k]) * (1.0 + rng.randf_range(-j, j))
		# A little of every Shape, so a quiet lean can still win on a strong spark.
		if key == "shape":
			for s in SHAPES:
				d[s] = float(d.get(s, 0.0)) + rng.randf_range(0.0, j * 0.4)
		# And of every blood, so the same answers do not always suggest the same people.
		if key == "blood":
			var top := 0.0
			for k in d:
				top = maxf(top, float(d[k]))
			for b in Data.bloods:
				d[b["id"]] = float(d.get(b["id"], 0.0)) + rng.randf_range(0.0, j * 1.2) * maxf(top, 0.3)
	return t

## A name from the city's names, by the spark.
static func name_for(city: String, spark: int) -> String:
	var c: Dictionary = Data.academy["cohort"]
	var rng := RandomNumberGenerator.new()
	rng.seed = spark + 7
	var firsts: Array = c["first"].get(city, c["first"]["columbia"])
	var lasts: Array = c["last"].get(city, c["last"]["columbia"])
	return "%s %s" % [firsts[rng.randi() % firsts.size()], lasts[rng.randi() % lasts.size()]]

## The bloods the answers suggest, best first: [{ id, score, reasons }].
static func suggest_bloods(t: Dictionary, count := 3) -> Array:
	var tier := _top(t["tier"], ["mark", "kindred", "bloodline"])
	if tier == "":
		tier = "mark"
	var out: Array = []
	for b in Data.bloods:
		if b["tier"] != tier:
			continue
		var score := float(t["blood"].get(b["id"], 0.0))
		# A small pull toward bloods whose rite lean matches the Shape the answers point at.
		for sh in b.get("shapeLean", {}):
			score += 0.3 * float(t["shape"].get(sh, 0.0)) / maxf(1.0, _max(t["shape"]))
		out.append({ "id": b["id"], "score": score, "reasons": t["why"]["blood"].get(b["id"], []) })
	out.sort_custom(func(a, b): return a["score"] > b["score"] or (a["score"] == b["score"] and a["id"] < b["id"]))
	return out.slice(0, count)

static func _max(d: Dictionary) -> float:
	var m := 0.0
	for k in d:
		m = maxf(m, float(d[k]))
	return m

## Build the character from the answers and a blood (the suggested one, or the player's pick).
static func generate(answers: Array, blood_id := "", spark := 0) -> Dictionary:
	var t := tally_with(answers, spark)
	if blood_id == "":
		blood_id = suggest_bloods(t)[0]["id"]
	var blood: Dictionary = Data.by_id(Data.bloods, blood_id)
	# The Shape: the answers, leaned by the blood (a kindred 40%, a bloodline 70%, a Mark a little).
	var shape_scores: Dictionary = t["shape"].duplicate()
	var lean_scale := _max(t["shape"])
	for sh in blood.get("shapeLean", {}):
		shape_scores[sh] = float(shape_scores.get(sh, 0.0)) + float(blood["shapeLean"][sh]) * lean_scale
	var shape := _top(shape_scores, SHAPES)
	var shape_why: Array = t["why"]["shape"].get(shape, []).duplicate()
	if blood.get("shapeLean", {}).has(shape):
		shape_why.append("%s blood leans toward it" % blood["name"])
	# The city: where you said home was, or where your blood comes from.
	var city: String = t["city"] if t["city"] != "" else blood.get("home", "columbia")
	var city_why: String = t["lines"].get("city", "your blood comes from there")
	# The weapon: the city's weapons, by the style you fight in and the style your Shape wants.
	var kit: Dictionary = Data.kits[shape]
	var best_w: Dictionary = {}
	var best_ws := -INF
	for w in Data.weapons:
		if w["city"] != city:
			continue
		var ws := float(t["style"].get(w["style"], 0.0)) + float(kit["styles"].get(w["style"], 0.0))
		if ws > best_ws:
			best_ws = ws
			best_w = w
	var weapon_why: Array = t["why"]["style"].get(best_w["style"], []).duplicate()
	weapon_why.append("a %s reaches for a %s" % [shape.capitalize(), best_w["name"].to_lower()])
	# The Pattern: a Form of the Shape by how you would rather fight, and the Terms you named.
	var effect := _top(t["effect"], ["strikes", "guard", "mend"])
	if effect == "":
		effect = "strikes"
	var form_id := ""
	for fid in kit["forms"]:
		if kit["forms"][fid]["effect"] == effect and form_id == "":
			form_id = fid
	if form_id == "":
		form_id = kit["forms"].keys()[0]
	var terms: Array = []
	for k in ["trigger", "toll", "bar"]:
		if t[k] != "":
			terms.append(t[k])
	var form: Dictionary = kit["forms"][form_id]
	var pattern := { "name": form["name"], "form": form_id, "terms": terms, "sworn": false }
	var seed: String = t["seed"] if t["seed"] != "" else "stands-between"
	return {
		"name": "", "blood": blood_id, "shape": shape, "city": city, "discipline": discipline_of(city),
		"weapon": best_w["id"], "seed": seed, "pattern": pattern, "body": Data.creation["models"][shape],
		"look": { "headgear": true, "cape": true, "cape_color": "shape", "stature": 1.0 },
		"answers": answers.duplicate(), "spark": spark,
		"why": { "shape": _unique(shape_why), "city": [city_why], "weapon": _unique(weapon_why.filter(func(x): return x != city_why)),
			"form": t["why"]["effect"].get(effect, []), "trigger": t["lines"].get("trigger", ""),
			"toll": t["lines"].get("toll", ""), "bar": t["lines"].get("bar", ""), "seed": t["lines"].get("seed", "") },
	}

static func weapon(id: String) -> Dictionary:
	return Data.by_id(Data.weapons, id)

static func blood(id: String) -> Dictionary:
	return Data.by_id(Data.bloods, id)

static func _unique(xs: Array) -> Array:
	var out: Array = []
	for x in xs:
		if not out.has(x):
			out.append(x)
	return out
