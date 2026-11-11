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

## Fill a pattern's {words}; tidy the spaces an empty word leaves.
static func fill(pattern: String, words: Dictionary) -> String:
	var s := pattern
	for k in words:
		s = s.replace("{%s}" % k, String(words[k]))
	while s.contains("  "):
		s = s.replace("  ", " ")
	return s.strip_edges()

static func _round(x: float, places: int) -> float:
	var k := pow(10.0, places)
	return roundf(x * k) / k

## What a form wears of its body (docs/genius-lines.md): everything its parent wears,
## unless it says otherwise; null takes a thing off.
static func wear(parent: Dictionary, own: Dictionary) -> Dictionary:
	var out := parent.duplicate(true)
	for k in own:
		if own[k] == null:
			out.erase(k)
		elif own[k] is Dictionary and out.get(k) is Dictionary:
			var d: Dictionary = (out[k] as Dictionary).duplicate()
			d.merge(own[k], true)
			out[k] = d
		else:
			out[k] = own[k]
	return out

static func _grow(parent_id: String, parent_features: Array, nodes: Array, level: int, silhouette: String, c: Dictionary, out: Array, parent_body: Dictionary = {}) -> Array:
	var ids: Array = []
	for n in nodes:
		# a form wears its own body where it names one; the forms below it on that road wear it too
		var sil := String(n.get("silhouette", silhouette))
		var f := {
			"id": (c["prefix"] + String(n["id"])), "name": n["name"], "text": n["text"], "of": String(n.get("of", "")), "sign": String(n.get("sign", "")), "habit": String(n.get("habit", "")),
			"base": c["base"], "kind": c["kind"], "level": level, "parent": parent_id,
			"expression": c["expression"], "class": c["class"], "silhouette": sil, "coatOf": c["coatOf"] if c["coatOf"] != "" else sil,
			"own": (n["features"] as Array).duplicate(), "features": _uniq(parent_features + n["features"]), "leans": n.get("leans", {}), "children": [],
			"instars": { "min": level, "max": 6 if level >= 4 else level },
			"body": wear(parent_body, n.get("body", {})),
			# the form whose own model it wears: its own; or, carried into a hybrid from its second
			# base, the form of the first it took the place of (a hybrid keeps its first's body)
			"wears": String(n.get("wears", n["id"])),
		}
		out.append(f)
		ids.append(f["id"])
		f["children"] = _grow(f["id"], f["features"], _kids(n), level + 1, sil, c, out, f["body"])
	return ids

## A base's thirty-one forms, the settled one first.
static func flatten(b: Dictionary) -> Array:
	var out: Array = []
	var c := { "prefix": "", "base": b["id"], "kind": b["name"], "expression": b["expression"], "class": b["class"], "coatOf": "" }
	var settled: Dictionary = (b["settled"] as Dictionary).duplicate()
	settled["prongs"] = b["paths"]
	_grow("", [], [settled], 1, String(b["silhouette"]), c, out)
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

## What play earns a path: "first" is the thing it leans on most ("orders.hunt"), "sig" its two
## heaviest leans in the order of their names. Of equal leans the one written first counts first.
static func signature(leans: Dictionary) -> Dictionary:
	var a := ""
	var b := ""
	var wa := -1.0
	var wb := -1.0
	for line in leans:
		for k in leans[line]:
			var id := "%s.%s" % [line, k]
			var w := float(leans[line][k])
			if w > wa:
				b = a
				wb = wa
				a = id
				wa = w
			elif w > wb:
				b = id
				wb = w
	var sig: Array = [a, b].filter(func(x): return x != "")
	sig.sort()
	return { "first": a, "sig": sig }

static func hybrid_id(first: String, second: String) -> String:
	return "%s+%s" % [first, second]

## A name made of another's word and a form's name: a Winged Mantler; The Winged Last Word.
static func rename(pattern: String, adj: String, name: String) -> String:
	if name.begins_with("The "):
		return "The " + fill(pattern, { "adj": adj, "name": name.substr(4) })
	return fill(pattern, { "adj": adj, "name": name })

## The hybrid's name: a pair written by hand, or the rule's.
static func hybrid_name(a: Dictionary, b: Dictionary, hy: Dictionary) -> String:
	var pair: Dictionary = hy["pairs"].get(hybrid_id(a["id"], b["id"]), {})
	return String(pair.get("name", fill(hy["rule"]["kind"], { "adj": b["hybrid"]["adj"], "name": a["name"] })))

static func _said(n: Dictionary, pair: Dictionary, rule: Dictionary, words: Dictionary) -> Dictionary:
	var o: Dictionary = pair.get("nodes", {}).get(n["id"], {})
	var out := n.duplicate()
	out["name"] = o.get("name", n["name"])
	out["text"] = o.get("text", n["text"])
	out["of"] = o.get("of", n.get("of", ""))
	var w := words.duplicate()
	w["sign"] = String(n.get("sign", ""))
	out["sign"] = o.get("sign", fill(rule["sign"], w))
	out["habit"] = o.get("habit", n.get("habit", ""))
	return out

static func _or(a: Variant, b: Variant) -> String:
	return String(a) if a != null and String(a) != "" else ("" if b == null else String(b))

## The tree of the hybrid of two bases: thirty forms under the first base's settled form. Its
## paths are the first's, bent toward the second's nature (less far where two of them would
## otherwise be earned by the same play); in each, the prong furthest from that nature gives
## way to the second's prong nearest the path, carried across with its finishes. Every form
## says what it is the picture of, carries the second's gift as its sign, and keeps a habit of
## the first's. labels: a feature's words, by its id.
static func compose(a: Dictionary, b: Dictionary, hy: Dictionary, labels: Dictionary = {}) -> Array:
	var h := hybrid_id(a["id"], b["id"])
	var pair: Dictionary = hy["pairs"].get(h, {})
	var rule: Dictionary = hy["rule"]
	var gift: Array = []
	for g in b["hybrid"]["gift"]:
		gift.append(String(labels.get(g, String(g).replace("-", " "))))
	var words := { "first": String(a["name"]).to_lower(), "second": String(b["name"]).to_lower(), "gift": " and ".join(gift) }
	var used: Array = []
	var theirs: Array = []
	for p in b["paths"]:
		theirs.append_array(p.get("prongs", []))
	var taken: Array = []
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
		var gone: Dictionary = mine[drop] if drop < mine.size() else {}
		var gone_fins: Array = gone.get("finishes", [])
		var fins: Array = []
		var theirs_fins: Array = best.get("finishes", [])
		for j in theirs_fins.size():
			var f: Dictionary = theirs_fins[j]
			fins.append(_said({ "id": f["id"], "name": rename(rule["carried"], String(a["hybrid"]["adj"]), String(f["name"])), "text": f["text"], "of": f.get("of", ""), "sign": "",
				"habit": _or(gone_fins[j].get("habit") if j < gone_fins.size() else null, f.get("habit")), "features": f["features"], "leans": f.get("leans", {}),
				"wears": String(gone_fins[j]["id"]) if j < gone_fins.size() else String(gone.get("id", f["id"])) }, pair, rule, words))
		var carried := _said({ "id": best["id"], "name": rename(rule["carried"], String(a["hybrid"]["adj"]), String(best["name"])), "text": best["text"], "of": best.get("of", ""), "sign": "",
			"habit": _or(gone.get("habit"), best.get("habit")), "features": best["features"], "leans": best.get("leans", {}), "finishes": fins,
			"wears": String(gone.get("id", best["id"])) }, pair, rule, words)
		var prongs: Array = []
		for i in mine.size():
			if i == drop:
				prongs.append(carried)
			else:
				var kept := _said(mine[i], pair, rule, words)
				kept["finishes"] = (mine[i].get("finishes", []) as Array).map(func(f): return _said(f, pair, rule, words))
				prongs.append(kept)
		# every path of a hybrid is earned by its own play: bend less far while two would share a signature
		var leans := bend(P.get("leans", {}), b["nature"], float(rule["bend"]))
		for t in [float(rule["bend"]) / 2.0, float(rule["bend"]) / 4.0, 0.0]:
			if not taken.has("|".join(signature(leans)["sig"])):
				break
			leans = bend(P.get("leans", {}), b["nature"], t)
		taken.append("|".join(signature(leans)["sig"]))
		var path: Dictionary = (P as Dictionary).duplicate()
		path["name"] = rename(rule["path"], String(b["hybrid"]["adj"]), String(P["name"]))
		path["text"] = "%s %s" % [P["text"], b["hybrid"]["text"]]
		var ow := words.duplicate()
		ow["of"] = String(P.get("of", ""))
		path["of"] = fill(rule["of"], ow) if String(P.get("of", "")) != "" else ""
		path["leans"] = leans
		path["prongs"] = prongs
		paths.append(_said(path, pair, rule, words))
	var out: Array = []
	var c := { "prefix": h + ":", "base": h, "kind": hybrid_name(a, b, hy), "expression": a["expression"], "class": a["class"], "coatOf": String(b["silhouette"]) }
	_grow(a["settled"]["id"], _uniq(a["settled"]["features"] + b["hybrid"]["gift"]), paths, 2, String(a["silhouette"]), c, out, a["settled"].get("body", {}))
	return out
