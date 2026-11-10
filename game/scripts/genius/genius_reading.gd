## The Readings on the genius tree (docs/genius-tree.md): the rite offers three bases; a
## refinement offers the children of the form the genius is, and once, a turning.
## A faithful copy of the tools' src/rules/reading.ts (the tests hold the two to the same
## answers, game/tests/fixtures/readings.json). Every number is in data/reading.json and
## data/genius-hybrids.json.
class_name GeniusReading
extends RefCounted

const SHAPES := ["anchor", "turn", "cast", "read", "bind", "make"]
const ORDERS := ["guard", "hunt", "hold", "free"]
const FIGHTS := ["parries", "blocks", "hurts", "dodges"]
const QUESTS := ["linework", "salvage", "hunt", "escort", "writ", "deep-run"]
## Where a run was, in the tree's words.
const GROUND := { "tunnel": "line", "line": "line", "post": "line", "junction": "line", "river": "water", "sky": "wild", "wild": "wild", "water": "water", "ruin": "ruin", "night": "night", "quiet": "quiet" }
## The lines a refinement reads, in order.
const PLAY_LINES := ["range", "orders", "shape", "fights", "company", "ground", "pattern", "bonds", "quests"]

## The record of play since the last Reading. Counts, not shares.
static func empty_tally() -> Dictionary:
	return { "families": {}, "range": {}, "orders": {}, "company": {}, "ground": {}, "discipline": {}, "bonds": {},
		"intention": null, "runsWith": {}, "counters": {} }

## The Tally as the tree reads it: for each line, the share of each key and how much the line counts.
static func play_lines(t: Dictionary, cfg: Dictionary = {}) -> Dictionary:
	if cfg.is_empty():
		cfg = Data.rules_reading()
	var ref: Dictionary = cfg["refine"]["reference"]
	var counts := { "range": {}, "orders": {}, "shape": {}, "fights": {}, "company": {}, "ground": {}, "quests": {} }
	var counters: Dictionary = t.get("counters", {})
	for k in ["close", "mid", "far"]:
		if float(t.get("range", {}).get(k, 0.0)) != 0.0:
			counts["range"][k] = float(t["range"][k])
	for k in ORDERS:
		if float(t.get("orders", {}).get(k, 0.0)) != 0.0:
			counts["orders"][k] = float(t["orders"][k])
	for k in t.get("families", {}):
		var s := String(k).split(".")[0]
		var v := float(t["families"][k])
		if SHAPES.has(s) and v != 0.0:
			counts["shape"][s] = float(counts["shape"].get(s, 0.0)) + v
	for k in FIGHTS:
		if float(counters.get("fights." + k, 0.0)) != 0.0:
			counts["fights"][k] = float(counters["fights." + k])
	for k in ["alone", "party"]:
		if float(counters.get("runs." + k, 0.0)) != 0.0:
			counts["company"][k] = float(counters["runs." + k])
	for k in t.get("ground", {}):
		var v := float(t["ground"][k])
		if v != 0.0:
			var g := String(GROUND.get(k, "wild"))
			counts["ground"][g] = float(counts["ground"].get(g, 0.0)) + v
	for k in QUESTS:
		if float(counters.get("runs.quest." + k, 0.0)) != 0.0:
			counts["quests"][k] = float(counters["runs.quest." + k])
	var shares := {}
	var emphasis := {}
	for line in counts:
		var total := 0.0
		for k in counts[line]:
			total += float(counts[line][k])
		var s := {}
		if total > 0.0:
			for k in counts[line]:
				s[k] = float(counts[line][k]) / total
		shares[line] = s
		emphasis[line] = minf(1.0, total / float(ref.get(line, 1)))
	var it: Variant = t.get("intention")
	if it is Dictionary and not (it as Dictionary).is_empty():
		shares["pattern"] = { "fires": minf(1.0, float(it.get("fires", 0)) / float(cfg["refine"]["patternFires"])), "sworn": 1.0 if it.get("sworn", false) else 0.0 }
		emphasis["pattern"] = 1.0
	else:
		shares["pattern"] = {}
		emphasis["pattern"] = 0.0
	var tb: Dictionary = t.get("bonds", {})
	var ran_with := false
	for k in t.get("runsWith", {}):
		ran_with = ran_with or float(t["runsWith"][k]) > 0.0
	var bonds := {
		"classmate": 1.0 if float(tb.get("classmate", 0.0)) > 0.0 or ran_with else 0.0,
		"shade": 1.0 if float(tb.get("shade", 0.0)) > 0.0 or float(tb.get("hearth", 0.0)) > 0.0 else 0.0,
		"named": 1.0 if float(tb.get("named", 0.0)) > 0.0 else 0.0,
	}
	shares["bonds"] = bonds
	emphasis["bonds"] = 1.0 if bonds["classmate"] + bonds["shade"] + bonds["named"] > 0.0 else 0.0
	return { "shares": shares, "emphasis": emphasis }

## How well the play fits a set of leans, 0 to 1 or so, and the lines that speak for it.
static func fit(leans: Dictionary, lines: Dictionary, cfg: Dictionary = {}) -> Dictionary:
	if cfg.is_empty():
		cfg = Data.rules_reading()
	var num := 0.0
	var den := 0.0
	var reasons: Array = []
	for line in leans:
		var w := float(cfg["refine"]["weights"].get(line, 0.0)) * float(lines["emphasis"].get(line, 0.0))
		for key in leans[line]:
			var lean := float(leans[line][key])
			den += lean
			var share := float(lines["shares"].get(line, {}).get(key, 0.0))
			var c := w * lean * share
			if c > 0.0:
				num += c
				reasons.append({ "line": line, "key": key, "share": share, "contribution": c })
	if den > 0.0:
		for r in reasons:
			r["contribution"] = float(r["contribution"]) / den
	reasons.sort_custom(_by_weight)
	return { "score": (num / den) if den > 0.0 else 0.0, "reasons": reasons.slice(0, 3) }

static func _by_weight(a: Dictionary, b: Dictionary) -> bool:
	if a["contribution"] != b["contribution"]:
		return a["contribution"] > b["contribution"]
	if a["line"] != b["line"]:
		return String(a["line"]) < String(b["line"])
	return String(a["key"]) < String(b["key"])

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

static func _candidate(f: Dictionary, score: float, reasons: Array, mark: String, heritage: Array, grafts: Array) -> Dictionary:
	var feats: Array = []
	for x in [mark] + f["features"] + heritage + grafts:
		if x != "" and not feats.has(x):
			feats.append(x)
	return { "form": f["id"], "base": f["base"], "kind": f["kind"], "name": f["name"], "text": f["text"], "expression": f["expression"],
		"silhouette": f["silhouette"], "coatOf": f["coatOf"], "level": int(f["level"]), "score": _round(score),
		"own": (f["features"] as Array).duplicate(), "heritage": heritage.duplicate(), "seedMark": mark, "features": feats,
		"reasons": reasons.map(func(r): return { "line": r["line"], "key": r["key"], "share": _round(r["share"]), "contribution": _round(r["contribution"]) }) }

## The rite: three bases, read from the Seed, the blood and the Shape, leaned by the home.
## noise / noise_seed: the bowl may add a little chance to each base (0 for the pure Reading).
static func _rite(origin: Dictionary, cfg: Dictionary, mark: String, noise: float, noise_seed: int) -> Dictionary:
	var own := { "seed": String(origin.get("seed", "")), "blood": String(origin.get("blood", "")), "shape": String(origin.get("shape", "")) }
	var home := String(origin.get("home", ""))
	var lean: Dictionary = Data.genius_homes().get(home, {}) if home != "" and not home.begins_with("$") else {}
	var rng := RandomNumberGenerator.new()
	rng.seed = noise_seed
	var pool: Array = []
	for b in Data.bases():
		var raw := 0.0
		var reasons: Array = []
		for line in ["seed", "blood", "shape"]:
			var c := float(cfg["rite"]["weights"].get(line, 0.0)) * float(b["calls"].get(line, {}).get(own[line], 0.0))
			if c > 0.0:
				raw += c
				reasons.append({ "line": line, "key": own[line], "share": 1.0, "contribution": c })
		reasons.sort_custom(_by_weight)
		if noise > 0.0:
			raw += rng.randf() * noise
		pool.append({ "b": b, "raw": raw, "leaned": raw * float(lean.get(b["id"], 1.0)), "reasons": reasons })
	var picked: Array = []
	while picked.size() < 3 and not pool.is_empty():
		var best_i := 0
		var best_v := -INF
		for i in pool.size():
			var c: Dictionary = pool[i]
			var same := picked.filter(func(p): return p["b"]["class"] == c["b"]["class"]).size()
			# the best fit is the field's own; the home leans only what is offered beside it
			var v := float(c["raw"] if picked.is_empty() else c["leaned"]) * pow(float(cfg["rite"]["sameClass"]), same)
			if v > best_v:
				best_v = v
				best_i = i
		var got: Dictionary = pool.pop_at(best_i)
		if not picked.is_empty() and float(got["leaned"]) > float(got["raw"]):
			got["reasons"] = got["reasons"] + [{ "line": "home", "key": home, "share": 1.0, "contribution": float(got["leaned"]) - float(got["raw"]) }]
		picked.append(got)
	var candidates: Array = []
	for p in picked:
		candidates.append(_candidate(Data.form(String(p["b"]["settled"]["id"])), float(p["raw"]), p["reasons"], mark, [], []))
	return { "instar": 1, "level": 1, "candidates": candidates, "turning": {}, "grows": false }

static func _offer(forms: Array, lines: Dictionary, cfg: Dictionary, mark: String, heritage: Array, grafts: Array) -> Array:
	var scored: Array = []
	for i in forms.size():
		var s := fit(forms[i].get("leans", {}), lines, cfg)
		scored.append({ "f": forms[i], "i": i, "score": s["score"], "reasons": s["reasons"] })
	scored.sort_custom(func(a, b): return a["score"] > b["score"] or (a["score"] == b["score"] and a["i"] < b["i"]))
	return scored.map(func(x): return _candidate(x["f"], x["score"], x["reasons"], mark, heritage, grafts))

## Read for instar n. The rite (no genius yet: current is {}) offers three bases. A refinement
## offers the children of the form the genius is, best fit first; the first refinement may
## also offer a turning ("turning": {} when there is none). From the fifth instar nothing is
## offered: the finished form grows ("grows": true).
static func read(instar: int, tally: Dictionary, origin: Dictionary, current: Dictionary, noise := 0.0, noise_seed := 0) -> Dictionary:
	var cfg: Dictionary = Data.rules_reading()
	var mark := seed_mark(String(origin.get("seed", "")))
	if current.is_empty() or instar == 1:
		return _rite(origin, cfg, mark, noise, noise_seed)
	var kids := Data.children_of(String(current.get("form", "")))
	# What it kept fed becomes part of it.
	var heritage: Array = []
	for x in current.get("heritage", []) + current.get("adaptations", []).map(func(a): return a["id"]).filter(func(id): return _is_fixable(id)):
		if not heritage.has(x):
			heritage.append(x)
	heritage = heritage.slice(0, int(Data.rules["genius"]["heritageMax"]))
	var grafts: Array = current.get("grafts", []).map(func(g): return g["feature"])
	# A finished form is offered nothing new: it grows, as itself, an age on.
	if kids.is_empty():
		var me := Data.form(String(current.get("form", "")))
		return { "instar": instar, "level": int(me.get("level", 4)), "candidates": [] if me.is_empty() else [_candidate(me, 0.0, [], mark, heritage, grafts)], "turning": {}, "grows": true }
	var lines := play_lines(tally, cfg)
	var candidates := _offer(kids, lines, cfg, mark, heritage, grafts)
	var turning := {}
	var mine := Data.base(String(current.get("base", "")))
	if int(kids[0]["level"]) == 2 and not mine.is_empty():
		var rule: Dictionary = Data.genius_hybrids()["rule"]
		var own := float(fit(mine["nature"], lines, cfg)["score"])
		var best_id := ""
		var best_s := 0.0
		var best_r: Array = []
		for b in Data.bases():
			if b["id"] == mine["id"]:
				continue
			var ft := fit(b["nature"], lines, cfg)
			var s := float(ft["score"])
			if best_id == "" or s > best_s:
				best_s = s
				best_id = b["id"]
				best_r = ft["reasons"]
		if best_id != "" and best_s >= float(rule["min"]) and best_s >= own * (1.0 + float(rule["margin"])):
			var other := Data.base(best_id)
			var paths := Data.hybrid_forms(mine["id"], best_id).filter(func(f): return int(f["level"]) == 2)
			turning = { "second": best_id, "base": GeniusTree.hybrid_id(mine["id"], best_id), "name": GeniusTree.hybrid_name(mine, other, Data.genius_hybrids()),
				"own": _round(own), "other": _round(best_s),
				"reasons": best_r.map(func(r): return { "line": r["line"], "key": r["key"], "share": _round(r["share"]), "contribution": _round(r["contribution"]) }),
				"candidates": _offer(paths, lines, cfg, mark, heritage, grafts) }
	return { "instar": instar, "level": int(kids[0]["level"]), "candidates": candidates, "turning": turning, "grows": false }

## The genius's body after a candidate is taken: its form, what it kept, and its grafts.
## Adaptations start again.
static func take(current: Dictionary, c: Dictionary, accepted_grafts: Array = []) -> Dictionary:
	return { "form": c["form"], "base": c["base"], "expression": c["expression"], "silhouette": c["silhouette"], "coatOf": c.get("coatOf", c["silhouette"]),
		"own": c["own"].duplicate(), "heritage": c["heritage"].duplicate(), "seedMark": c["seedMark"],
		"grafts": current.get("grafts", []).duplicate(true) + accepted_grafts, "adaptations": [] }

## A line and key of the Tally in plain words ("fighting close"; data/reading.json, words).
static func words(line: String, key: String) -> String:
	var w: Dictionary = Data.rules_reading().get("words", {})
	if line == "home":
		return "%s (%s)" % [String(w.get("rite", {}).get("home", "home")), key.capitalize()]
	if w.get("rite", {}).has(line):
		return String(w["rite"][line])
	return String(w.get(line, {}).get(key, "%s %s" % [line, key]))

## What play leads to a form, in plain words: its strongest leans first.
static func lean_words(leans: Dictionary, most := 3) -> String:
	var all: Array = []
	for line in leans:
		for key in leans[line]:
			all.append({ "line": line, "key": key, "contribution": float(leans[line][key]) })
	all.sort_custom(_by_weight)
	return ", ".join(all.slice(0, most).map(func(x): return words(x["line"], x["key"])))

## The lines that spoke for a candidate, in plain words.
static func reason_words(reasons: Array) -> String:
	return ", ".join(reasons.map(func(r): return words(String(r["line"]), String(r["key"]))))

static func _round(x: float) -> float:
	return roundf(x * 1000.0) / 1000.0
