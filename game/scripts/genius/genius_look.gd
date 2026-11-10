## What makes one genius unlike another of its form (data/genius-looks.json), pure and testable.
## A genius carries a small `look`: the number it was born with and what its partner chose.
##   { seed, coat, marks, keepsake, keepsakeColor }
## Everything it is born with is drawn from the seed, so it is the same every time it is built
## and stays its own through every instar: which coats of its body's palette are its own (the
## first is the one it was born in), which marking regions show, how lean or heavy it stands,
## how its light burns. The partner chooses among its coats, turns markings on and off, and
## gives it a keepsake. resolve() turns a look into what genius_body.gd paints.
class_name GeniusLook
extends RefCounted

## The number a genius is born with: its partner's Seed and Pattern, their spark and name.
static func identity(hero: Dictionary) -> int:
	var p: Dictionary = hero.get("pattern", {})
	var terms: Array = p.get("terms", [])
	var key := "%s|%s|%s|%s|%s" % [hero.get("seed", ""), p.get("form", ""), ",".join(terms.map(func(t): return String(t))), str(int(hero.get("spark", 0))), hero.get("name", "")]
	return int(key.hash())

static func born(seed_value: int) -> Dictionary:
	return { "seed": seed_value, "coat": 0, "marks": {}, "keepsake": "", "keepsakeColor": "" }

## A number in [0, 1) from the seed and a word: the same every time, on every machine.
static func roll(seed_value: int, salt: String) -> float:
	return float(("%d|%s" % [seed_value, salt]).hash() % 100003) / 100003.0

static func body(silhouette: String) -> Dictionary:
	return Data.genius_looks()["bodies"].get(silhouette, {})

## The coats a form may wear: its own palette if it has one, or its body's. A hybrid wears its
## first base's body in a coat of its second's (the form's coatOf; docs/genius-tree.md).
static func palette(form: String, silhouette: String) -> Array:
	var looks: Dictionary = Data.genius_looks()
	var coat_of := String(Data.form(form).get("coatOf", silhouette)) if form != "" else silhouette
	var theirs: String = body(coat_of).get("coats", "")
	var pid: String = looks["forms"].get(form, {}).get("coats", theirs if theirs != "" else body(silhouette).get("coats", ""))
	return looks["palettes"].get(pid, [])

## The few coats that are this genius's own, the one it was born in first.
static func offered_coats(look: Dictionary, form: String, silhouette: String) -> Array:
	var pal: Array = palette(form, silhouette).duplicate()
	var s := int(look.get("seed", 0))
	pal.sort_custom(func(a, b): return roll(s, "coat:" + String(a["id"])) < roll(s, "coat:" + String(b["id"])))
	return pal.slice(0, int(Data.genius_looks()["born"]["coatsOffered"]))

## The markings it was born with: each of its body's regions by chance, no more than a few.
static func born_marks(look: Dictionary, silhouette: String) -> Dictionary:
	var cfg: Dictionary = Data.genius_looks()["born"]
	var s := int(look.get("seed", 0))
	var regions: Array = body(silhouette).get("marks", {}).keys()
	regions.sort_custom(func(a, b): return roll(s, "mark:" + String(a)) < roll(s, "mark:" + String(b)))
	var out := {}
	var n := 0
	for r in regions:
		var on := roll(s, "mark:" + String(r)) < float(cfg["markChance"]) and n < int(cfg["marksMax"])
		out[r] = on
		if on:
			n += 1
	return out

## The markings it shows: what it was born with, changed where its partner has chosen.
static func marks(look: Dictionary, silhouette: String) -> Dictionary:
	var out := born_marks(look, silhouette)
	var chosen: Dictionary = look.get("marks", {})
	for r in out:
		if chosen.has(r):
			out[r] = bool(chosen[r])
	return out

## Its proportions, each from -1 to 1, most often near the middle.
static func proportions(look: Dictionary) -> Dictionary:
	var s := int(look.get("seed", 0))
	var out := {}
	for p in Data.genius_looks()["proportions"]:
		out[p["id"]] = roll(s, "prop-a:" + String(p["id"])) + roll(s, "prop-b:" + String(p["id"])) - 1.0
	return out

static func eyes(look: Dictionary) -> Dictionary:
	var list: Array = Data.genius_looks()["eyes"]
	return list[int(roll(int(look.get("seed", 0)), "eyes") * list.size()) % list.size()]

static func glow(instar: int) -> float:
	return float(Data.genius_looks()["instarGlow"].get(str(clampi(instar, 1, 6)), 1.0))

static func keepsake(id: String) -> Dictionary:
	for k in Data.genius_looks()["keepsakes"]:
		if k["id"] == id:
			return k
	return {}

## The keepsakes a body can wear: those with a socket on it to hang from.
static func keepsakes_for(sockets: Array) -> Array:
	return Data.genius_looks()["keepsakes"].filter(func(k): return k["sockets"].any(func(sn): return sockets.has(sn)))

static func keepsake_color(id: String) -> Dictionary:
	var list: Array = Data.genius_looks()["keepsakeColors"]
	for c in list:
		if c["id"] == id:
			return c
	return list[0]

## Everything the body needs to paint it: { coat, colors (material name -> Color), marks,
## proportions, eyes, glow, keepsake, keepsake_color }. A body with no entry in the data keeps
## the colours it was made in, and still has its build, its light and its keepsake.
static func resolve(look: Dictionary, form: String, silhouette: String, instar := 1) -> Dictionary:
	var b := body(silhouette)
	var offered := offered_coats(look, form, silhouette)
	var coat: Dictionary = offered[clampi(int(look.get("coat", 0)), 0, offered.size() - 1)] if not offered.is_empty() else {}
	var colors := {}
	var shown := marks(look, silhouette)
	if not coat.is_empty():
		for mat_name in b.get("roles", {}):
			colors[mat_name] = Color(String(coat[b["roles"][mat_name]]))
		for r in b.get("marks", {}):
			colors["mark_" + String(r)] = Color(String(coat["mark"] if shown.get(r, false) else coat[b["marks"][r]["on"]]))
	var kc := keepsake_color(String(look.get("keepsakeColor", "")))
	colors["keepsake_tint"] = Color(String(kc["color"]))
	return { "coat": coat, "offered": offered, "colors": colors, "marks": shown, "proportions": proportions(look), "eyes": eyes(look),
		"glow": glow(instar), "keepsake": keepsake(String(look.get("keepsake", ""))), "keepsake_color": kc }

## In words, for its page: "A dun coat, with socks and a mask. Lean. A slow pulse of light."
static func describe(look: Dictionary, form: String, silhouette: String) -> String:
	var r := resolve(look, form, silhouette)
	var b := body(silhouette)
	var parts: Array = []
	if not r["coat"].is_empty():
		var named: Array = []
		for m in r["marks"]:
			if r["marks"][m]:
				named.append(String(b["marks"][m]["name"]))
		parts.append("Its coat is %s%s." % [r["coat"]["name"], (", with " + " and ".join(named)) if not named.is_empty() else ""])
	for p in Data.genius_looks()["proportions"]:
		var v := float(r["proportions"].get(p["id"], 0.0))
		# said only of a body that can show it: by a shape of its own, or by its whole build
		var shows: bool = p["shapes"].any(func(sh): return sh != "" and b.get("shapes", []).has(sh)) or p["scale"].any(func(x): return float(x) != 0.0)
		if shows and absf(v) >= float(p["words"]):
			parts.append("It is %s." % String(p["low"] if v < 0.0 else p["high"]))
	parts.append("It burns with %s." % r["eyes"]["name"])
	if not r["keepsake"].is_empty():
		parts.append("It wears %s (%s)." % [r["keepsake"]["name"], r["keepsake_color"]["name"]])
	return " ".join(parts)
