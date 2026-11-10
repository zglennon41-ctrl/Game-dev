## The genius tree (docs/genius-tree.md): a base is a tree of thirty-one forms; a hybrid is a
## tree composed from two bases by rule. A faithful copy of the tools' src/data/tree.ts (the
## tests hold the two to the same answers). Pure: the bases and the rule are passed in.
class_name GeniusTree
extends RefCounted

static func _kids(n: Dictionary) -> Array:
	return n.get("prongs", n.get("finishes", []))

static func _uniq(xs: Array) -> Array:
	var out: Array = []
	for x in xs:
		if not out.has(x):
			out.append(x)
	return out

static func _fill(pattern: String, adj: String, name: String) -> String:
	return pattern.replace("{adj}", adj).replace("{name}", name)

static func _round(x: float, places: int) -> float:
	var k := pow(10.0, places)
	return roundf(x * k) / k

static func _grow(parent_id: String, parent_features: Array, nodes: Array, level: int, c: Dictionary, out: Array) -> Array:
	var ids: Array = []
	for n in nodes:
		var f := {
			"id": (c["prefix"] + String(n["id"])), "name": n["name"], "text": n["text"], "base": c["base"], "kind": c["kind"], "level": level, "parent": parent_id,
			"expression": c["expression"], "class": c["class"], "silhouette": n.get("silhouette", c["silhouette"]), "coatOf": c["coatOf"] if c["coatOf"] != "" else n.get("silhouette", c["silhouette"]),
			"own": (n["features"] as Array).duplicate(), "features": _uniq(parent_features + n["features"]), "leans": n.get("leans", {}), "children": [],
			"instars": { "min": level, "max": 6 if level >= 4 else level },
		}
		out.append(f)
		ids.append(f["id"])
		f["children"] = _grow(f["id"], f["features"], _kids(n), level + 1, c, out)
	return ids

## A base's thirty-one forms, the settled one first.
static func flatten(b: Dictionary) -> Array:
	var out: Array = []
	var c := { "prefix": "", "base": b["id"], "kind": b["name"], "expression": b["expression"], "class": b["class"], "silhouette": b["silhouette"], "coatOf": "" }
	var settled: Dictionary = (b["settled"] as Dictionary).duplicate()
	settled["prongs"] = b["paths"]
	_grow("", [], [settled], 1, c, out)
	return out

## How alike two sets of leans are, 0 to 1 (the cosine of the two as vectors).
static func alike(a: Dictionary, b: Dictionary) -> float:
	var dot := 0.0
	var na := 0.0
	var nb := 0.0
	for line in a:
		for k in a[line]:
			var w := float(a[line][k])
			na += w * w
			dot += w * float(b.get(line, {}).get(k, 0.0))
	for line in b:
		for k in b[line]:
			nb += float(b[line][k]) * float(b[line][k])
	return _round(dot / sqrt(na * nb), 6) if na > 0.0 and nb > 0.0 else 0.0

## Leans part of the way from one to another.
static func bend(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var out := {}
	for line in _uniq(a.keys() + b.keys()):
		for k in _uniq(a.get(line, {}).keys() + b.get(line, {}).keys()):
			var w := _round((1.0 - t) * float(a.get(line, {}).get(k, 0.0)) + t * float(b.get(line, {}).get(k, 0.0)), 3)
			if w > 0.0:
				if not out.has(line):
					out[line] = {}
				out[line][k] = w
	return out

static func hybrid_id(first: String, second: String) -> String:
	return "%s+%s" % [first, second]

## The hybrid's name: a pair written by hand, or the rule's.
static func hybrid_name(a: Dictionary, b: Dictionary, hy: Dictionary) -> String:
	var pair: Dictionary = hy["pairs"].get(hybrid_id(a["id"], b["id"]), {})
	return String(pair.get("name", _fill(hy["rule"]["kind"], b["hybrid"]["adj"], a["name"])))

static func _said(n: Dictionary, pair: Dictionary) -> Dictionary:
	var o: Dictionary = pair.get("nodes", {}).get(n["id"], {})
	var out := n.duplicate()
	out["name"] = o.get("name", n["name"])
	out["text"] = o.get("text", n["text"])
	return out

## The tree of the hybrid of two bases: thirty forms under the first base's settled form. Its
## paths are the first's, bent toward the second's nature; in each, the prong furthest from
## that nature gives way to the second's prong nearest the path, carried across with its finishes.
static func compose(a: Dictionary, b: Dictionary, hy: Dictionary) -> Array:
	var h := hybrid_id(a["id"], b["id"])
	var pair: Dictionary = hy["pairs"].get(h, {})
	var rule: Dictionary = hy["rule"]
	var used: Array = []
	var theirs: Array = []
	for p in b["paths"]:
		theirs.append_array(p.get("prongs", []))
	var paths: Array = []
	for P in a["paths"]:
		var best: Dictionary = {}
		var best_s := -1.0
		for q in theirs:
			if used.has(q["id"]):
				continue
			var s := alike(q.get("leans", {}), P.get("leans", {}))
			if s > best_s:
				best_s = s
				best = q
		used.append(best["id"])
		var drop := 0
		var drop_s := INF
		var mine: Array = P.get("prongs", [])
		for i in mine.size():
			var s2 := alike(mine[i].get("leans", {}), b["nature"])
			if s2 <= drop_s:
				drop_s = s2
				drop = i
		var fins: Array = []
		for f in best.get("finishes", []):
			fins.append(_said({ "id": f["id"], "name": _fill(rule["carried"], a["hybrid"]["adj"], f["name"]), "text": f["text"], "features": f["features"], "leans": f.get("leans", {}) }, pair))
		var carried := _said({ "id": best["id"], "name": _fill(rule["carried"], a["hybrid"]["adj"], best["name"]), "text": best["text"], "features": best["features"], "leans": best.get("leans", {}), "finishes": fins }, pair)
		var prongs: Array = []
		for i in mine.size():
			if i == drop:
				prongs.append(carried)
			else:
				var kept := _said(mine[i], pair)
				kept["finishes"] = (mine[i].get("finishes", []) as Array).map(func(f): return _said(f, pair))
				prongs.append(kept)
		var path: Dictionary = (P as Dictionary).duplicate()
		path["name"] = _fill(rule["path"], b["hybrid"]["adj"], P["name"])
		path["text"] = "%s %s" % [P["text"], b["hybrid"]["text"]]
		path["leans"] = bend(P.get("leans", {}), b["nature"], float(rule["bend"]))
		path["prongs"] = prongs
		paths.append(_said(path, pair))
	var out: Array = []
	var c := { "prefix": h + ":", "base": h, "kind": hybrid_name(a, b, hy), "expression": a["expression"], "class": a["class"], "silhouette": a["silhouette"], "coatOf": b["silhouette"] }
	_grow(a["settled"]["id"], _uniq(a["settled"]["features"] + b["hybrid"]["gift"]), paths, 2, c, out)
	return out
