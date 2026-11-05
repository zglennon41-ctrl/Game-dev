## The Reading: score the lattice against the Tally and offer three candidates with heritage.
## A faithful copy of the tools' src/rules/reading.ts (the tests hold the two to the same
## answers, game/tests/fixtures/readings.json). Every number is in data/reading.json.
class_name GeniusReading
extends RefCounted

const EXPRESSIONS := ["beast", "kith", "engine", "relic", "daemon", "aspect"]
const COUNT_LINES := ["families", "range", "orders", "company", "ground", "discipline"]

## The record of play since the last Reading. Counts, not shares.
static func empty_tally() -> Dictionary:
	return { "families": {}, "range": {}, "orders": {}, "company": {}, "ground": {}, "discipline": {}, "bonds": {},
		"intention": null, "runsWith": {}, "counters": {} }

## The intention line: the Pattern's Form, and its Terms' tags shared out.
static func intention_keys(form: String, terms: Array) -> Dictionary:
	var keys := { "family:" + form: 1.0 }
	var tags: Array = []
	for id in terms:
		for t in Data.terms:
			if t["id"] == id:
				tags.append_array(t["tags"])
	for tag in tags:
		keys["tag:" + tag] = float(keys.get("tag:" + tag, 0.0)) + 1.0 / tags.size()
	return keys

## A Tally as per-line shares, and how much each line counts (its emphasis).
static func lines_of(t: Dictionary, origin: Dictionary, cfg: Dictionary) -> Dictionary:
	var shares := {}
	var emphasis := {}
	for line in COUNT_LINES:
		var counts: Dictionary = t.get(line, {})
		var total := 0.0
		for k in counts:
			total += float(counts[k])
		var s := {}
		if total > 0.0:
			for k in counts:
				s[k] = float(counts[k]) / total
		shares[line] = s
		emphasis[line] = minf(1.0, total / float(cfg["emphasis"]["reference"].get(line, 1)))
	var bonds := {}
	var any_bond := false
	for k in t.get("bonds", {}):
		bonds[k] = 1.0 if float(t["bonds"][k]) > 0.0 else 0.0
		any_bond = any_bond or float(t["bonds"][k]) > 0.0
	shares["bonds"] = bonds
	emphasis["bonds"] = 1.0 if any_bond else 0.0
	var it: Variant = t.get("intention")
	if it is Dictionary and not (it as Dictionary).is_empty():
		shares["intention"] = intention_keys(it["form"], it["terms"])
		var base := float(cfg["emphasis"]["intentionBase"])
		emphasis["intention"] = base + (1.0 - base) * minf(1.0, float(it["fires"]) / float(cfg["emphasis"]["intentionFires"]))
	else:
		shares["intention"] = {}
		emphasis["intention"] = 0.0
	shares["seed"] = { origin["seed"]: 1.0 }
	shares["blood"] = { origin["blood"]: 1.0 }
	shares["shape"] = { origin["shape"]: 1.0 }
	emphasis["seed"] = 1.0
	emphasis["blood"] = 1.0
	emphasis["shape"] = 1.0
	return { "shares": shares, "emphasis": emphasis }

static func _lean(cfg: Dictionary, line: String, key: String) -> Dictionary:
	return cfg["leans"].get(line, {}).get(key, {})

static func _key_fit(lean: Dictionary, expression: String, features: Array) -> float:
	if lean.is_empty():
		return 0.0
	var v := float(lean.get("expression", {}).get(expression, 0.0))
	for f in features:
		v += float(lean.get("features", {}).get(f, 0.0))
	return v

static func _score_form(form: Dictionary, shares: Dictionary, emphasis: Dictionary, weights: Dictionary, cfg: Dictionary) -> Dictionary:
	var score := 0.0
	var reasons: Array = []
	for line in weights:
		if line.begins_with("$"):
			continue
		var w := float(weights[line])
		var e := float(emphasis.get(line, 0.0))
		if w == 0.0 or e == 0.0:
			continue
		var sh: Dictionary = shares.get(line, {})
		for key in sh:
			var c := w * e * float(sh[key]) * _key_fit(_lean(cfg, line, key), form["expression"], form["features"])
			if c > 0.0:
				score += c
				reasons.append({ "line": line, "key": key, "share": float(sh[key]), "contribution": c })
	reasons.sort_custom(func(a, b): return a["contribution"] > b["contribution"])
	return { "score": score, "reasons": reasons.slice(0, 3) }

static func _score_feature(feature: String, shares: Dictionary, emphasis: Dictionary, weights: Dictionary, cfg: Dictionary) -> float:
	var s := 0.0
	for line in weights:
		if line.begins_with("$"):
			continue
		var w := float(weights[line])
		var e := float(emphasis.get(line, 0.0))
		var sh: Dictionary = shares.get(line, {})
		for key in sh:
			s += w * e * float(sh[key]) * float(_lean(cfg, line, key).get("features", {}).get(feature, 0.0))
	return s

## For each line, which Expression it points at most, and how hard.
static func line_leads(shares: Dictionary, emphasis: Dictionary, weights: Dictionary, cfg: Dictionary) -> Array:
	var out: Array = []
	for line in weights:
		if line.begins_with("$"):
			continue
		var w := float(weights[line])
		var e := float(emphasis.get(line, 0.0))
		if w == 0.0 or e == 0.0:
			continue
		var best := ""
		var best_v := 0.0
		for x in EXPRESSIONS:
			var v := 0.0
			var sh: Dictionary = shares.get(line, {})
			for key in sh:
				v += float(sh[key]) * float(_lean(cfg, line, key).get("expression", {}).get(x, 0.0))
			if v > best_v:
				best_v = v
				best = x
		if best != "":
			out.append({ "line": line, "expression": best, "weight": w * e * best_v })
	out.sort_custom(func(a, b): return a["weight"] > b["weight"])
	return out

static func is_adaptation(id: String) -> bool:
	for f in Data.features():
		if f["id"] == id:
			return f.get("adaptation", false)
	return false

static func _is_fixable(id: String) -> bool:
	for f in Data.features():
		if f["id"] == id:
			return f.get("fixable", false)
	return false

static func seed_mark(seed_id: String) -> String:
	for s in Data.seeds():
		if s["id"] == seed_id:
			return s["seedMark"]
	return ""

## Score every eligible form and offer three. current: the genius's form now (a dictionary as
## take() makes), or {} for the First Form. noise / noise_seed: the rite's bowl may add a
## little chance to each score (0 for the pure Reading).
static func read(instar: int, tally: Dictionary, origin: Dictionary, current: Dictionary, noise := 0.0, noise_seed := 0) -> Dictionary:
	var cfg: Dictionary = Data.rules_reading()
	var genius_rules: Dictionary = Data.rules["genius"]
	var first := instar == 1 or current.is_empty()
	var weights: Dictionary = cfg["firstFormWeights"] if first else cfg["weights"]
	var lo := lines_of(tally, origin, cfg)
	var shares: Dictionary = lo["shares"]
	var emphasis: Dictionary = lo["emphasis"]
	var leads := line_leads(shares, emphasis, weights, cfg)
	var mark := seed_mark(origin["seed"])
	var top := leads.slice(0, 3)
	var crossing := current.is_empty() or top.filter(func(l): return l["expression"] != current["expression"]).size() >= int(cfg["crossing"]["linesAway"])
	var rng := RandomNumberGenerator.new()
	rng.seed = noise_seed
	var scored: Array = []
	var lattice: Array = Data.forms().duplicate()
	lattice.sort_custom(func(a, b): return a["id"] < b["id"])
	for f in lattice:
		if int(f["instars"]["min"]) > instar or instar > int(f["instars"]["max"]) or f["id"] == current.get("form", ""):
			continue
		var s := _score_form(f, shares, emphasis, weights, cfg)
		var stay := 1.0
		if not current.is_empty() and not crossing and f["expression"] == current["expression"]:
			stay = 1.0 + float(cfg["crossing"]["stayBonus"])
		var sc := float(s["score"]) * stay
		if noise > 0.0:
			sc += rng.randf() * noise
		scored.append({ "f": f, "score": sc, "reasons": s["reasons"] })
	scored.sort_custom(func(a, b): return a["score"] > b["score"] or (a["score"] == b["score"] and a["f"]["id"] < b["f"]["id"]))
	# Greedy pick of three, discounting repeats of an Expression so three bodies are offered.
	var picked: Array = []
	var pool := scored.duplicate()
	while picked.size() < 3 and not pool.is_empty():
		var best_i := 0
		var best_v := -INF
		for i in pool.size():
			var c: Dictionary = pool[i]
			var same := picked.filter(func(p): return p["f"]["expression"] == c["f"]["expression"]).size()
			var v := float(c["score"]) * pow(float(cfg["diversity"]["sameExpression"]), same)
			if v > best_v:
				best_v = v
				best_i = i
		picked.append(pool.pop_at(best_i))
	var heritage_pool: Array = []
	if not current.is_empty():
		var raw: Array = current["own"] + current["heritage"] + current.get("adaptations", []).map(func(a): return a["id"])
		var graft_feats: Array = current.get("grafts", []).map(func(g): return g["feature"])
		for x in raw:
			if x != current["seedMark"] and not graft_feats.has(x) and not heritage_pool.has(x):
				heritage_pool.append(x)
	var candidates: Array = []
	for p in picked:
		var f: Dictionary = p["f"]
		var heritage: Array = []
		if not current.is_empty():
			var options: Array = []
			for x in heritage_pool:
				if f["features"].has(x):
					continue
				if is_adaptation(x) and not _is_fixable(x):
					continue
				options.append({ "x": x, "s": _score_feature(x, shares, emphasis, weights, cfg) })
			options.sort_custom(func(a, b): return a["s"] > b["s"] or (a["s"] == b["s"] and a["x"] < b["x"]))
			for o in options:
				if float(o["s"]) >= float(cfg["heritage"]["minScore"]) and heritage.size() < int(genius_rules["heritageMax"]):
					heritage.append(o["x"])
			if heritage.size() < int(genius_rules["heritageMin"]) and not options.is_empty():
				heritage = options.slice(0, int(genius_rules["heritageMin"])).map(func(o): return o["x"])
		var grafts: Array = current.get("grafts", []).map(func(g): return g["feature"])
		var feats: Array = []
		for x in [mark] + f["features"] + heritage + grafts:
			if x != "" and not feats.has(x):
				feats.append(x)
		candidates.append({ "form": f["id"], "name": f["name"], "expression": f["expression"], "silhouette": f["silhouette"],
			"score": _round(float(p["score"])), "own": f["features"].duplicate(), "heritage": heritage, "seedMark": mark,
			"features": feats, "reasons": p["reasons"].map(func(r): return { "line": r["line"], "key": r["key"], "share": _round(r["share"]), "contribution": _round(r["contribution"]) }) })
	return { "instar": instar, "crossingAllowed": crossing, "lineLeads": leads, "candidates": candidates }

## The genius's body after a candidate is taken. Fixed adaptations became heritage; the rest go.
static func take(current: Dictionary, c: Dictionary, accepted_grafts: Array = []) -> Dictionary:
	return { "form": c["form"], "expression": c["expression"], "silhouette": c["silhouette"], "own": c["own"].duplicate(),
		"heritage": c["heritage"].duplicate(), "seedMark": c["seedMark"],
		"grafts": current.get("grafts", []).duplicate(true) + accepted_grafts, "adaptations": [] }

static func _round(x: float) -> float:
	return roundf(x * 1000.0) / 1000.0
