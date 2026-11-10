## A genius: the character's field made into a companion, read and not chosen. This is the
## whole of it in one place, so everything built later (combat, the Academy, the hall, the
## server) has the same thing to talk to:
##   its body now (its form on the genius tree and that form's base, own features, heritage,
##   the Seed-mark, grafts, adaptations), its
##   instar and history, the Tally of play since the last Reading, lifetime counters, its
##   orders, Will and falls, secondary forms, witnessed Patterns and shadows, and its look
##   (the coat, markings and build it was born with, and the keepsake its partner gave it).
## Pure and saveable: to_dict() / from_dict() round-trip through the hero's save.
## The rules are in data/rules.json ("genius", "instars", "tiers"), data/reading.json and
## data/genius.json; the Reading itself in genius_reading.gd.
class_name Genius
extends RefCounted

var name := ""
var instar := 0                  # 0 before the rite
var body: Dictionary = {}        # form, base, expression, silhouette, coatOf, own, heritage, seedMark, grafts, adaptations
var origin: Dictionary = {}      # seed, blood, shape: read alongside play
var tally: Dictionary = GeniusReading.empty_tally()
var lifetime: Dictionary = {}    # counters over the whole life (adaptations use the Tally's; secondary forms these)
var history: Array = []          # [{ instar, form, name, day, by, settled }]
var milestones: Array = []       # rite, gate, pattern-built, adept, master, accord
var day := 0                     # days since the rite
var secondary: Array = []        # [{ id, vestigial }]
var witnessed: Dictionary = {}   # pattern key -> uses seen
var shadows: Array = []          # [{ key, name, form, terms }]
var pending_grafts: Array = []   # [{ id, feature, source }]
var faded_at: Dictionary = {}    # adaptation id -> counter when it faded
var order := "guard"
var falls_this_season := 0
var fallen := false
var pending_reading: Dictionary = {}
var look: Dictionary = {}        # what it was born looking like and what its partner chose (genius_look.gd)

# --- Making and saving ------------------------------------------------------------

static func from_dict(d: Dictionary) -> Genius:
	var g := Genius.new()
	if d.is_empty():
		return g
	for k in ["name", "instar", "body", "origin", "tally", "lifetime", "history", "milestones", "day", "secondary",
			"witnessed", "shadows", "pending_grafts", "faded_at", "order", "falls_this_season", "fallen", "look"]:
		if d.has(k):
			g.set(k, d[k])
	# Saves from before the genius system: a First Form with its fields at the top level.
	if g.body.is_empty() and d.has("form"):
		g.body = { "form": d["form"], "expression": d.get("expression", ""), "silhouette": d.get("silhouette", ""),
			"own": d.get("own", d.get("features", [])), "heritage": [], "seedMark": d.get("seedMark", ""), "grafts": [], "adaptations": [] }
		g.instar = maxi(1, int(d.get("instar", 1)))
	g.instar = int(g.instar)
	g._onto_the_tree()
	return g

## A genius saved before the genius tree (docs/genius-tree.md) is a form no tree has. It
## settles again, as the base nearest the body it wore, at the first level of that base's
## tree: it keeps its name, its look, its Seed-mark, what it had kept and its instars (they
## are its age), and refines from there at its next Readings.
func _onto_the_tree() -> void:
	if body.is_empty() or String(body.get("form", "")) == "":
		return
	var f := Data.form(String(body["form"]))
	if not f.is_empty():
		if not body.has("base"):
			body["base"] = f["base"]
			body["coatOf"] = f["coatOf"]
		return
	var b := Genius.nearest_base(String(body.get("silhouette", "")), String(body.get("expression", "")))
	if b.is_empty():
		return
	var was := String(body["form"])
	var settled := Data.form(String(b["settled"]["id"]))
	var kept: Array = []
	for x in body.get("heritage", []):
		if GeniusReading.is_adaptation(String(x)) and not kept.has(x):
			kept.append(x)
	body = { "form": settled["id"], "base": settled["base"], "expression": settled["expression"], "silhouette": settled["silhouette"],
		"coatOf": settled["coatOf"], "own": (settled["features"] as Array).duplicate(), "heritage": kept,
		"seedMark": body.get("seedMark", ""), "grafts": body.get("grafts", []), "adaptations": body.get("adaptations", []) }
	history.append({ "instar": instar, "form": settled["id"], "name": settled["name"], "day": day, "by": "the tree", "settled": true, "resettled": was })
	pending_reading = {}

## The base nearest a body: the one that wears it, or one of its Expression, or the first.
static func nearest_base(silhouette: String, expression: String) -> Dictionary:
	var same: Dictionary = {}
	for b in Data.bases():
		if String(b["silhouette"]) == silhouette:
			return b
		if same.is_empty() and String(b["expression"]) == expression:
			same = b
	if not same.is_empty():
		return same
	return Data.bases()[0] if not Data.bases().is_empty() else {}

func to_dict() -> Dictionary:
	var d := {}
	for k in ["name", "instar", "body", "origin", "tally", "lifetime", "history", "milestones", "day", "secondary",
			"witnessed", "shadows", "pending_grafts", "faded_at", "order", "falls_this_season", "fallen", "look"]:
		d[k] = get(k)
	# Kept at the top level too, for the parts of the game that only need to draw it.
	d["form"] = body.get("form", "")
	d["expression"] = body.get("expression", "")
	d["silhouette"] = body.get("silhouette", "")
	d["features"] = features()
	return d

static func for_hero(hero: Dictionary) -> Genius:
	var g := Genius.from_dict(hero.get("genius", {}))
	g.origin = { "seed": hero.get("seed", ""), "blood": hero.get("blood", ""), "shape": hero.get("shape", ""), "city": hero.get("city", ""), "home": hero.get("city", "") }
	if g.tally.get("intention") == null and hero.has("pattern"):
		g.tally["intention"] = { "form": hero["pattern"]["form"], "terms": hero["pattern"]["terms"], "fires": 0, "sworn": hero["pattern"].get("sworn", false) }
	# A genius born before looks existed gets the one it would have been born with.
	if g.is_born() and g.look.is_empty():
		g.look = GeniusLook.born(GeniusLook.identity(hero))
	return g

func save_to(hero: Dictionary) -> void:
	hero["genius"] = to_dict()

func is_born() -> bool:
	return instar >= 1 and not body.is_empty()

# --- What it is now ----------------------------------------------------------------

func features() -> Array:
	var out: Array = []
	var parts: Array = [body.get("seedMark", "")] + body.get("own", []) + body.get("heritage", []) \
		+ body.get("grafts", []).map(func(g): return g["feature"]) + body.get("adaptations", []).map(func(a): return a["id"])
	for x in parts:
		if x != "" and not out.has(x):
			out.append(x)
	return out

## Features grouped by slot (head, eyes, wings, body, surface, limbs, arms, light, voice).
func features_by_slot() -> Dictionary:
	var out := {}
	for f in features():
		var slot := "body"
		for fd in Data.features():
			if fd["id"] == f:
				slot = fd["slot"]
		if not out.has(slot):
			out[slot] = []
		out[slot].append(f)
	return out

## What it is called now: its form's name on the tree, and once it has finished, the name of
## its age (data/genius.json, progression.ages: a Great Pack-mother, a Pack-mother of the Line).
func form_name() -> String:
	return Genius.form_name_at(String(body.get("form", "")), instar)

static func form_name_at(form_id: String, at_instar: int) -> String:
	var f := Data.form(form_id)
	if f.is_empty():
		return form_id.capitalize()
	var nm := String(f["name"])
	if f["children"].is_empty():
		var pat := String(age_at(at_instar).get("name", ""))
		if pat != "" and not (nm.begins_with("The ") or nm.begins_with("Old ")):
			return pat.replace("{name}", nm)
	return nm

## A form of the tree by its id (a base's, or a hybrid's: first+second:form). {} if none.
static func form_of(form_id: String) -> Dictionary:
	return Data.form(form_id)

## Its form now, as the tree has it.
func form() -> Dictionary:
	return Data.form(String(body.get("form", "")))

## What it is: its base's name, or its hybrid's ("Wolf", "Edged Wolf").
func kind() -> String:
	return String(form().get("kind", ""))

## How far along its tree it is: 1 settled, 2 a path, 3 a prong, 4 a finish.
func level() -> int:
	return int(form().get("level", 0))

## The forms it may become at its next refinement (none once it has finished).
func next_forms() -> Array:
	return Data.children_of(String(body.get("form", "")))

## The road it took: its forms from the settled one to the one it is.
func road() -> Array:
	var out: Array = []
	var f := form()
	while not f.is_empty():
		out.push_front(f)
		f = Data.form(String(f.get("parent", ""))) if String(f.get("parent", "")) != "" else {}
	return out

## Its age: each instar is one (data/genius.json, progression.ages): { id, word }.
func age() -> Dictionary:
	return Genius.age_at(instar)

static func age_at(at_instar: int) -> Dictionary:
	return Data.genius().get("progression", {}).get("ages", {}).get(str(clampi(at_instar, 1, 6)), { "id": "grown", "word": "grown" })

func instar_name() -> String:
	var r := GeniusResonance.instar_rule(instar)
	return r.get("name", "Unread")

## Resonance, given the Pattern's Intention tier.
func resonance(tier := 0) -> int:
	return GeniusResonance.resonance(maxi(1, instar), tier)

func will_max(tier := 0) -> float:
	return GeniusResonance.genius_will(resonance(tier))

func shadow_cap(tier := 0) -> int:
	return GeniusResonance.shadow_cap(resonance(tier))

## How tall it stands, in metres, by instar.
func height() -> float:
	return float(Data.genius()["size"].get(str(maxi(1, instar)), 0.6))

## The orders it can take now.
func orders_available() -> Array:
	return Data.genius()["orders"].filter(func(o): return int(o["fromInstar"]) <= maxi(1, instar))

func next_order() -> String:
	var combat := orders_available().filter(func(o): return o.has("guard") or o.has("hunt") or o.has("hold") or o.has("free"))
	var ids: Array = combat.map(func(o): return o["id"])
	if ids.is_empty():
		return order
	var i := ids.find(order)
	return ids[(i + 1) % ids.size()]

# --- The Tally: what it learns from play -------------------------------------------

static func _add(d: Dictionary, k: String, n := 1.0) -> void:
	d[k] = float(d.get(k, 0.0)) + n

## Count a thing into a Tally line (families, range, orders, company, ground, discipline).
func count(line: String, key: String, n := 1.0) -> void:
	if not tally.has(line) or not (tally[line] is Dictionary):
		tally[line] = {}
	_add(tally[line], key, n)

## Count a raw counter, both since the last Reading (adaptations) and over the life.
func counter(metric: String, n := 1.0) -> void:
	_add(tally["counters"], metric, n)
	_add(lifetime, metric, n)

## A hit landed at a distance: the range line ("close", "mid", "far").
func hit_at(distance: float) -> void:
	var t: Dictionary = Data.genius()["tally"]
	var band := "close" if distance < float(t["close"]) else ("mid" if distance < float(t["mid"]) else "far")
	count("range", band)
	counter("fights.range." + band)

## A technique or Pattern Form of a family was used (e.g. "anchor.weight").
func used_family(family: String) -> void:
	count("families", family)
	counter("fieldUses." + family)

func gave_order(id: String) -> void:
	count("orders", id)
	counter("orders." + id)

func pattern_fired() -> void:
	if tally.get("intention") is Dictionary:
		tally["intention"]["fires"] = int(tally["intention"]["fires"]) + 1
	counter("pattern.fires")

## A run: where it was, whether by night, and whether anyone went with them.
func ran(ground: String, night := false, party := -1) -> void:
	count("ground", ground)
	counter("runs")
	counter("runs.ground." + ground)
	if night:
		count("ground", "night")
		counter("runs.night")
	if party >= 0:
		counter("runs.party" if party > 0 else "runs.alone")

## The work they took: a posting of a type (linework, salvage, hunt, escort, writ, deep-run).
func took_work(quest_type: String) -> void:
	counter("runs.quest." + quest_type)

## How its partner met a blow: "parries", "blocks", "hurts", "dodges".
func met_blow(how: String) -> void:
	counter("fights." + how)

func fought_beside(shape: String) -> void:
	count("company", shape)
	counter("runs.company." + shape)

## A day at study is a day somewhere quiet.
func studied(discipline: String, n := 1.0) -> void:
	count("discipline", discipline, n)
	count("ground", "quiet")

func bonded(kind: String) -> void:
	_add(tally["bonds"], kind)

# --- Adaptations, grafts, secondary forms, shadows ------------------------------------

## Gain adaptations whose counters have crossed their thresholds (while there is a slot);
## lose those left unfed for a season. Returns what changed: [{ id, change }].
func update_adaptations() -> Array:
	var out: Array = []
	if not is_born():
		return out
	var g: Dictionary = Data.rules["genius"]
	var have: Array = body.get("adaptations", [])
	for ad in Data.adaptations():
		var cnt := float(tally["counters"].get(ad["metric"], 0.0))
		var found: Dictionary = {}
		for a in have:
			if a["id"] == ad["id"]:
				found = a
		if not found.is_empty():
			if float(tally["counters"].get("__last." + ad["metric"], -1.0)) != cnt:
				found["lastFed"] = day
		elif cnt - float(faded_at.get(ad["id"], 0.0)) >= float(ad["threshold"]) and have.size() < int(g["adaptationSlots"]) and not features().has(ad["id"]):
			have.append({ "id": ad["id"], "lastFed": day })
			out.append({ "id": ad["id"], "change": "gained" })
		tally["counters"]["__last." + ad["metric"]] = cnt
	for a in have.duplicate():
		if day - int(a["lastFed"]) > int(g["adaptationFadeDays"]):
			have.erase(a)
			for ad in Data.adaptations():
				if ad["id"] == a["id"]:
					faded_at[a["id"]] = float(tally["counters"].get(ad["metric"], 0.0))
			out.append({ "id": a["id"], "change": "faded" })
	body["adaptations"] = have
	return out

## A graft offered (a shade's, a named beast's, a kin's), taken at the next Reading.
func offer_graft(g: Dictionary) -> void:
	for p in pending_grafts:
		if p["id"] == g["id"]:
			return
	for p in body.get("grafts", []):
		if p["id"] == g["id"]:
			return
	pending_grafts.append(g)

## Does it meet a secondary form's requirements? ctx: { pattern_form, ranks: [{discipline, rank}] }.
func meets(reqs: Array, ctx: Dictionary = {}) -> bool:
	for r in reqs:
		match String(r["kind"]):
			"expression":
				if not r["in"].has(body.get("expression", "")): return false
			"counter":
				if float(lifetime.get(r["metric"], 0.0)) < float(r["atLeast"]): return false
			"patternFamily":
				if ctx.get("pattern_form", "") != r["family"]: return false
			"instar":
				if instar < int(r["atLeast"]): return false
			"accord":
				if not milestones.has("accord"): return false
			"rank":
				var ok := false
				for rk in ctx.get("ranks", []):
					if rk["discipline"] == r["archetypeDiscipline"] and (rk["rank"] == "master" or (r["rank"] == "adept" and rk["rank"] != "journeyman")):
						ok = true
				if not ok: return false
	return true

## Secondary forms it could develop now (from the Third Form, while there is a slot).
func secondary_ready(ctx: Dictionary = {}) -> Array:
	var g: Dictionary = Data.rules["genius"]
	if instar < int(g["secondaryFromInstar"]) or secondary.size() >= int(g["secondarySlots"]):
		return []
	var have: Array = secondary.map(func(s): return s["id"])
	return Data.secondary_forms().filter(func(s): return not have.has(s["id"]) and meets(s["requires"], ctx))

func develop_secondary(id: String) -> void:
	secondary.append({ "id": id, "vestigial": false })

## A Pattern used inside its field (by anyone). Ten witnessed uses make a shadow, up to the cap.
## Returns the new shadow, or {}.
func witness(pattern: Dictionary, tier := 0) -> Dictionary:
	var key := "%s|%s" % [pattern.get("form", ""), ",".join(pattern.get("terms", []))]
	witnessed[key] = int(witnessed.get(key, 0)) + 1
	if int(witnessed[key]) < int(Data.rules["genius"]["shadowUses"]):
		return {}
	for s in shadows:
		if s["key"] == key:
			return {}
	if shadows.size() >= shadow_cap(tier):
		return {}
	var s := { "key": key, "name": pattern.get("name", ""), "form": pattern.get("form", ""),
		"terms": pattern.get("terms", []).filter(func(t): return _kind(t) == "trigger") }
	shadows.append(s)
	return s

static func _kind(term_id: String) -> String:
	for t in Data.terms:
		if t["id"] == term_id:
			return t["kind"]
	return ""

## Falling: Will emptied by damage. Too many falls in a season costs the newest secondary form.
func fall() -> void:
	fallen = true
	falls_this_season += 1
	if falls_this_season >= int(Data.genius()["fall"]["fallsPerSeasonCostSecondary"]) and not secondary.is_empty():
		secondary.pop_back()

func recover() -> void:
	fallen = false

# --- Instars and the Reading -------------------------------------------------------------

## The next instar whose Reading may happen now (0 if none).
func reading_due(tier := 0) -> int:
	var n := instar + 1
	if n > 6:
		return 0
	return n if GeniusResonance.reading_due(n, day, milestones, tier) != "" else 0

## How near the next Reading is, 0 to 1: the share of the minimum days lived since this
## instar's, held just short of 1 until the milestone that unlocks the next is reached too.
## The body shows it (data/genius.json, progression): it grows, and near the end it molts.
func readiness(tier := 0) -> float:
	if not is_born() or instar >= 6:
		return 0.0
	if reading_due(tier) > 0:
		return 1.0
	var d0 := float(GeniusResonance.instar_rule(instar).get("minDay", 0))
	var d1 := float(GeniusResonance.instar_rule(instar + 1).get("minDay", d0 + 1.0))
	return clampf((float(day) - d0) / maxf(1.0, d1 - d0), 0.0, 1.0) * 0.9

## Read for instar n (genius_reading.gd): the rite's three bases; or the forms it may become,
## best fit first, and at the first refinement perhaps a turning; or, once it has finished,
## nothing new ("grows").
func read(n: int, noise := 0.0, noise_seed := 0) -> Dictionary:
	var current := body if is_born() else {}
	pending_reading = GeniusReading.read(n, tally, origin, current, noise, noise_seed)
	pending_reading["unlockedBy"] = GeniusResonance.unlock_reason(n, milestones, 0)
	return pending_reading

const TURN := -3    # take(TURN): take the turning, where one is offered

## Take candidate i of the pending Reading (or settle on the best, i = -1; or take the turning,
## i = TURN, which makes it the hybrid's best-fitting path). A finished form has one candidate,
## itself: it grows. Adaptations it kept fed become heritage; pending grafts are taken while
## there are slots; the Tally starts again, keeping the Pattern as the intention.
func take(i := -1) -> Dictionary:
	var cands: Array = pending_reading.get("candidates", [])
	var turning: Dictionary = pending_reading.get("turning", {})
	var turned := i == TURN and not turning.is_empty()
	if turned:
		cands = turning["candidates"]
	if cands.is_empty():
		return {}
	var settled := i == -1
	var grew: bool = pending_reading.get("grows", false)
	var n := int(pending_reading["instar"])
	var c: Dictionary = cands[0 if i < 0 else clampi(i, 0, cands.size() - 1)]
	var was_form := String(body.get("form", ""))
	var was_sil := String(body.get("coatOf", body.get("silhouette", "")))
	var room := maxi(0, int(Data.rules["genius"]["graftSlots"]) - body.get("grafts", []).size())
	var accepted: Array = pending_grafts.slice(0, room) if n >= 2 else []
	pending_grafts = pending_grafts.slice(room) if n >= 2 else pending_grafts
	body = GeniusReading.take(body, c, accepted)
	instar = n
	var entry := { "instar": n, "form": c["form"], "name": Genius.form_name_at(String(c["form"]), n), "day": day, "by": pending_reading.get("unlockedBy", ""), "settled": settled or grew }
	if grew:
		entry["grew"] = true
	if turned:
		entry["turned"] = String(turning["second"])
	history.append(entry)
	_carry_coat(was_form, was_sil)
	var intention: Variant = tally.get("intention")
	tally = GeniusReading.empty_tally()
	if intention is Dictionary:
		tally["intention"] = { "form": intention["form"], "terms": intention["terms"], "fires": 0, "sworn": intention.get("sworn", false) }
	faded_at = {}
	for s in secondary:
		var sf: Dictionary = {}
		for x in Data.secondary_forms():
			if x["id"] == s["id"]:
				sf = x
		s["vestigial"] = not meets(sf.get("requires", []).filter(func(r): return r["kind"] == "expression"))
	pending_reading = {}
	return c

## The coat goes with it into a new body: of the coats the new body offers it, the one nearest
## in colour to the coat it wore.
func _carry_coat(was_form: String, was_sil: String) -> void:
	if look.is_empty() or was_sil == "" or was_sil == String(body.get("coatOf", body.get("silhouette", ""))):
		return
	var was := GeniusLook.offered_coats(look, was_form, was_sil)
	var now := GeniusLook.offered_coats(look, String(body.get("form", "")), String(body.get("silhouette", "")))
	if was.is_empty() or now.is_empty():
		return
	var worn := Color(String(was[clampi(int(look.get("coat", 0)), 0, was.size() - 1)].get("main", "#808080")))
	var best := 0
	var best_d := INF
	for k in now.size():
		var c := Color(String(now[k].get("main", "#808080")))
		var d := Vector3(c.r - worn.r, c.g - worn.g, c.b - worn.b).length()
		if d < best_d:
			best_d = d
			best = k
	look["coat"] = best

func milestone(id: String) -> void:
	if not milestones.has(id):
		milestones.append(id)
