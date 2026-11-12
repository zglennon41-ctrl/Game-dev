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

## The weapons a character's school teaches: those of the city whose Discipline they took. A
## home with no school of its own (Alexandria) took another city's Discipline at creation,
## so its school's weapons are that city's. Never empty: a choice with nothing in it is a wall.
static func school_weapons(hero: Dictionary) -> Array:
	var school := String(Data.discipline_kits.get(String(hero.get("discipline", "")), {}).get("city", ""))
	for city in [school, String(hero.get("city", ""))]:
		var out := Data.weapons.filter(func(w): return w["city"] == city)
		if not out.is_empty():
			return out
	return Data.weapons.duplicate()

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
	# A home with no school of its own (Alexandria: everyone passes through) reaches for any
	# city's weapon, and takes that city's Discipline.
	var any_city := Data.weapons.filter(func(w): return w["city"] == city).is_empty()
	for w in Data.weapons:
		if w["city"] != city and not any_city:
			continue
		var ws := float(t["style"].get(w["style"], 0.0)) + float(kit["styles"].get(w["style"], 0.0))
		if ws > best_ws:
			best_ws = ws
			best_w = w
	var weapon_why: Array = t["why"]["style"].get(best_w["style"], []).duplicate()
	var wname := String(best_w["name"]).to_lower().trim_prefix("the ").trim_prefix("a ")
	weapon_why.append("a %s reaches for %s %s" % [shape.capitalize(), "an" if wname.substr(0, 1) in ["a", "e", "i", "o", "u"] else "a", wname])
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
		"name": "", "blood": blood_id, "shape": shape, "city": city, "discipline": discipline_of(best_w["city"] if any_city else city),
		"weapon": best_w["id"], "seed": seed, "pattern": pattern, "body": "%s-%s" % [city, "m" if spark % 2 == 0 else "f"],
		"look": look_of(city, spark),
		"answers": answers.duplicate(), "spark": spark,
		"why": { "shape": _unique(shape_why), "city": [city_why], "weapon": _unique(weapon_why.filter(func(x): return x != city_why)),
			"form": t["why"]["effect"].get(effect, []), "trigger": t["lines"].get("trigger", ""),
			"toll": t["lines"].get("toll", ""), "bar": t["lines"].get("bar", ""), "seed": t["lines"].get("seed", "") },
	}

## A skin tone from the home's palette (data/bodies.json), by the spark.
static func skin_of(city: String, spark: int) -> String:
	var palette: Array = Data.bodies.get(city, {}).get("palette", ["olive"])
	return palette[(spark / 3) % palette.size()]

## The look a life starts with, drawn by its spark (data/creation.json, look.start): every
## character begins unlike the last, and all of it is the player's to change at the reveal.
static func look_of(city: String, spark: int) -> Dictionary:
	var st: Dictionary = Data.creation.get("look", {}).get("start", {})
	var skin := skin_of(city, spark)
	var home: Dictionary = Data.bodies.get(city, {})
	var hairs: Array = home.get("hair", st.get("hair", ["crop"]))
	var cols: Array = (home.get("hairColors", st.get("hairColors", ["brown"])) as Array).duplicate()
	if not home.has("hairColors") and (st.get("fairSkins", []) as Array).has(skin):
		cols.append_array(st.get("fairHairColors", []))
	var b: Array = st.get("build", [0.0, 0.0])
	var h: Array = st.get("stature", [1.0, 1.0])
	var rng := RandomNumberGenerator.new()
	rng.seed = spark * 2654435761 + 97
	var look := { "headgear": true, "cape": false, "cape_color": "shape", "beard": "none",
		"sex": "m" if spark % 2 == 0 else "f", "skin": skin,
		"hair": hairs[rng.randi() % hairs.size()], "hair_color": cols[rng.randi() % cols.size()],
		"build": snappedf(rng.randf_range(float(b[0]), float(b[1])), 0.05),
		"stature": snappedf(rng.randf_range(float(h[0]), float(h[1])), 0.01) }
	look.merge(face_of(rng, city))
	look.merge(frame_of(rng))
	return look

## A body's weight and frame drawn at random between the least and the greatest a life starts
## with (data/creation.json, look.start): for a new life and for everyone the player did not make.
static func frame_of(rng: RandomNumberGenerator) -> Dictionary:
	var st: Dictionary = Data.creation.get("look", {}).get("start", {})
	var w: Array = st.get("weight", [0.0, 0.0])
	var f: Array = st.get("frame", [0.0, 0.0])
	# two draws each: most people are near the middle, a few at either end
	var weight := (rng.randf_range(float(w[0]), float(w[1])) + rng.randf_range(float(w[0]), float(w[1]))) / 2.0
	var frame := (rng.randf_range(float(f[0]), float(f[1])) + rng.randf_range(float(f[0]), float(f[1]))) / 2.0
	return { "weight": snappedf(weight, 0.05), "frame": snappedf(frame, 0.05), "age": 0.0 }

## A face drawn at random, from what the home's people most often have (data/bodies.json: eyes,
## marks) and from every shape, brow and feature the bodies carry (data/creation.json, look):
## for a new life, for "surprise me", and for everyone the player did not make.
static func face_of(rng: RandomNumberGenerator, city: String) -> Dictionary:
	var L: Dictionary = Data.creation.get("look", {})
	var st: Dictionary = L.get("start", {})
	var home: Dictionary = Data.bodies.get(city, {})
	var shapes: Array = L.get("faces", ["own"])
	var brows: Array = L.get("brows", ["soft"])
	var eyes: Array = home.get("eyes", L.get("eyeColors", { "dark": [] }).keys())
	var strengths: Array = L.get("faceStrength", { "plain": 0.8 }).values()
	var out := { "face": shapes[rng.randi() % shapes.size()], "face_strength": snappedf(rng.randf_range(float(strengths.min()), float(strengths.max())), 0.05),
		"brows": brows[rng.randi() % brows.size()], "eye_color": eyes[rng.randi() % eyes.size()], "lips": "bare", "marks": [], "face_set": {} }
	var far := float(st.get("faceSlider", 0.4))
	for k in L.get("faceSliders", {}):
		out["face_set"][k] = snappedf(rng.randf_range(-far, far), 0.05)
	if rng.randf() < float(st.get("markChance", 0.3)):
		var marks: Array = (L.get("marks", []) as Array) + (home.get("marks", []) as Array)
		if not marks.is_empty():
			out["marks"] = [marks[rng.randi() % marks.size()]]
	return out

## The slot a piece of a home's dress is worn in (data/creation.json, look.slots.kinds): the
## top, the legs, the feet, over it, or an extra.
static func slot_of(piece: Dictionary) -> String:
	if piece.has("slot"):
		return String(piece["slot"])
	var kinds: Dictionary = Data.creation.get("look", {}).get("slots", {}).get("kinds", {})
	for s in kinds:
		if (kinds[s] as Array).has(String(piece.get("type", ""))):
			return s
	return "extra"

## What is painted on a body beneath its home's dress (data/bodies.json, dress.under): a colour's
## name for the shirt, the legs and the shoes, or "bare"; a sex may have its own.
static func under_of(home: String, sex: String) -> Dictionary:
	var u: Dictionary = (Data.bodies.get(home, {}).get("dress", {}).get("under", {}) as Dictionary).duplicate()
	if u.get(sex) is Dictionary:
		u.merge(u[sex], true)
	u.erase("m")
	u.erase("f")
	return u

## What a home's dress offers in one slot, on a body of one sex, worn one way (plain, formal,
## master): each choice { id, name }. A home's dress has two cuts (the pieces its data marks m
## and f); the id is the cut, or "none" where the slot may be left off. A cut is named for its
## own pieces, or for what both cuts wear there, or for what the body shows without (trousers,
## bare legs, a shirt, a bare chest). Two cuts that are the same are one choice; a slot with
## nothing to choose offers nothing.
static func wear_options(home: String, slot: String, sex := "m", wear := "plain") -> Array:
	var L: Dictionary = Data.creation.get("look", {})
	var labels: Dictionary = L.get("labels", {})
	var dress: Dictionary = Data.bodies.get(home, {}).get("dress", {})
	var names := { "m": [], "f": [], "": [] }
	var entries: Array = []
	if slot == "head":
		var hgs: Variant = dress.get("headgear", [])
		entries = [hgs] if hgs is Dictionary else (hgs as Array)
	else:
		entries = (dress.get("pieces", []) as Array).filter(func(p): return slot_of(p) == slot)
	var any := false
	for e in entries:
		if e.has("in") and not (e["in"] as Array).has(wear):
			continue
		any = true
		var label := String(e.get("name", labels.get("headgear" if slot == "head" else "pieces", {}).get(String(e["type"]), String(e["type"]).capitalize())))
		var cut := String(e.get("sex", ""))
		if label != "" and not (names[cut] as Array).has(label):
			(names[cut] as Array).append(label)
	if not any and not (slot == "head" and not (L.get("coverings", []) as Array).is_empty()):
		return []
	var under := String(under_of(home, sex).get({ "top": "shirt", "legs": "legs", "feet": "feet" }.get(slot, ""), ""))
	var none_name := String(labels.get("wearBare" if under == "bare" else "wearNone", {}).get(slot, labels.get("wearNone", {}).get(slot, "None")))
	var named := func(list: Array) -> String:
		return " and ".join(list) if list.size() <= 2 else "%s, %s and more" % [list[0], list[1]]
	var out: Array = []
	for cut in ["m", "f"]:
		var mine: Array = names[cut] if not (names[cut] as Array).is_empty() else names[""]
		if slot == "head" and mine.is_empty():
			continue        # a cut with no headgear is the bare head, offered once below
		var name: String = named.call(mine) if not mine.is_empty() else none_name
		if not out.any(func(o): return o["name"] == name):
			out.append({ "id": cut, "name": name })
	if slot == "head":      # and the cloths any head may wear over its hair (look.coverings)
		for cv in L.get("coverings", []):
			out.append({ "id": String(cv["id"]), "name": String(cv.get("name", String(cv["id"]).capitalize())) })
	if (L.get("slots", {}).get("optional", []) as Array).has(slot) and not out.any(func(o): return o["name"] == none_name):
		out.append({ "id": "none", "name": none_name })
	return out if out.size() > 1 else []

## The choice of a slot a look wears on a body of one sex, as one of the home's choices for it:
## the look's own (look.wear), else the body's cut; a cut the home does not tell apart is the
## first choice.
static func wear_choice(home: String, slot: String, look: Dictionary, sex: String, wear := "plain") -> String:
	var opts := wear_options(home, slot, sex, wear)
	var want := wear_of(look, slot, sex)
	if opts.is_empty() or opts.any(func(o): return o["id"] == want):
		return want
	for o in opts:
		if String(o["id"]) in ["m", "f"]:
			return String(o["id"])
	return "none" if opts.any(func(o): return o["id"] == "none") else String(opts[0]["id"])

## Whether a cut of a home's dress has anything of its own or of both cuts' to wear in a slot.
static func cut_has(home: String, slot: String, cut: String, wear := "plain") -> bool:
	for p in Data.bodies.get(home, {}).get("dress", {}).get("pieces", []):
		if slot_of(p) == slot and String(p.get("sex", cut)) == cut and (not p.has("in") or (p["in"] as Array).has(wear)):
			return true
	return false

## A look's choices of cut, settled so the body is dressed: where a home goes bare-legged under
## its dress (data/bodies.json, dress.under), a cut with nothing on the legs is worn only with
## a top (its own long robe); with a cut that has no top either, the legs take the other cut.
static func wear_settle(home: String, wear: Dictionary, sex: String) -> Dictionary:
	var out := wear.duplicate()
	if String(under_of(home, sex).get("legs", "")) != "bare":
		return out
	var top := String(out.get("top", sex))
	var legs := String(out.get("legs", sex))
	if not cut_has(home, "top", top) and not cut_has(home, "legs", legs):
		var other := "f" if legs == "m" else "m"
		if cut_has(home, "legs", other):
			out["legs"] = other
		elif cut_has(home, "top", "f" if top == "m" else "m"):
			out["top"] = "f" if top == "m" else "m"
	return out

## The covering a look wears over its hair (data/creation.json, look.coverings): its id, or ""
## when the head wears its home's own headgear or nothing.
static func cover_of(look: Dictionary) -> String:
	var w: Variant = look.get("wear", {})
	var id := String((w as Dictionary).get("head", "")) if w is Dictionary else ""
	for cv in Data.creation.get("look", {}).get("coverings", []):
		if String(cv["id"]) == id:
			return id
	return ""

## The cut of a slot a look wears on a body of one sex: its own unless the look says another
## (look.wear: slot -> m, f or none).
static func wear_of(look: Dictionary, slot: String, sex: String) -> String:
	var w: Variant = look.get("wear", {})
	return String((w as Dictionary).get(slot, sex)) if w is Dictionary else sex

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
