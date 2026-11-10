## A genius: the character's field made into a companion, read and not chosen. This is the
## whole of it in one place, so everything built later (combat, the Academy, the hall, the
## server) has the same thing to talk to:
##   its body now (form, own features, heritage, the Seed-mark, grafts, adaptations), its
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
var body: Dictionary = {}        # form, expression, silhouette, own, heritage, seedMark, grafts, adaptations
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
	return g

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
	g.origin = { "seed": hero.get("seed", ""), "blood": hero.get("blood", ""), "shape": hero.get("shape", ""), "city": hero.get("city", "") }
	if g.tally.get("intention") == null and hero.has("pattern"):
		g.tally["intention"] = { "form": hero["pattern"]["form"], "terms": hero["pattern"]["terms"], "fires": 0 }
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

## What it is called now: the form's name, or the name of its young while it is not yet grown
## (data/forms.json, ages: a Field-wolf at the First Form is a wolf pup).
func form_name() -> String:
	return Genius.form_name_at(String(body.get("form", "")), instar)

static func form_name_at(form_id: String, at_instar: int) -> String:
	for f in Data.forms():
		if f["id"] == form_id:
			var nm := String(f["name"])
			if f.get("ages", {}).has(str(at_instar)):
				return String(f["ages"][str(at_instar)])
			# the great and the apex of a kind are named for it, where the name allows
			var pat := String(age_at(at_instar).get("name", ""))
			if pat != "" and not (nm.begins_with("The ") or nm.begins_with("Old ")):
				return pat.replace("{name}", nm)
			return nm
	return form_id.capitalize()

static func form_of(form_id: String) -> Dictionary:
	for f in Data.forms():
		if f["id"] == form_id:
			return f
	return {}

## Its own kind at instar n: what it becomes if it keeps its kind at the Reading and grows
## (data/genius.json, progression.kind). The same form a year older, or the elder of its
## kind once it has outgrown the form (data/forms.json, growsInto). It keeps its heritage,
## and whatever it had adapted becomes heritage, as at any Reading.
func kept_kind(n: int) -> Dictionary:
	if not is_born() or not Data.genius().get("progression", {}).get("kind", {}).get("offered", false):
		return {}
	var cur := Genius.form_of(String(body.get("form", "")))
	if cur.is_empty():
		return {}
	var f := cur
	if n > int(cur["instars"]["max"]) and cur.has("growsInto"):
		var elder := Genius.form_of(String(cur["growsInto"]))
		if not elder.is_empty() and n >= int(elder["instars"]["min"]):
			f = elder
	var mark := String(body.get("seedMark", ""))
	var own: Array = (f["features"] as Array).duplicate()
	var heritage: Array = []
	var carried: Array = body.get("heritage", []).duplicate()
	if f["id"] != cur["id"]:
		carried += body.get("own", [])
	carried += body.get("adaptations", []).map(func(a): return a["id"])
	for x in carried:
		if x != mark and not own.has(x) and not heritage.has(x) and heritage.size() < int(Data.rules["genius"]["heritageMax"]):
			heritage.append(x)
	var feats: Array = []
	for x in [mark] + own + heritage + body.get("grafts", []).map(func(gr): return gr["feature"]):
		if x != "" and not feats.has(x):
			feats.append(x)
	return { "form": f["id"], "name": f["name"], "expression": f["expression"], "silhouette": f["silhouette"], "score": 0.0,
		"own": own, "heritage": heritage, "seedMark": mark, "features": feats, "reasons": [], "kept": true }

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
	var combat := orders_available().filter(func(o): return o.has("guard") or o.has("hunt"))
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

func ran(ground: String, night := false) -> void:
	count("ground", ground)
	counter("runs")
	counter("runs.ground." + ground)
	if night:
		counter("runs.night")

func fought_beside(shape: String) -> void:
	count("company", shape)
	counter("runs.company." + shape)

func studied(discipline: String, n := 1.0) -> void:
	count("discipline", discipline, n)

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

## Read the Tally for instar n: three candidates (or the First Form's, from Seed, blood, Shape).
func read(n: int, noise := 0.0, noise_seed := 0) -> Dictionary:
	var current := body if is_born() else {}
	pending_reading = GeniusReading.read(n, tally, origin, current, noise, noise_seed)
	pending_reading["unlockedBy"] = GeniusResonance.unlock_reason(n, milestones, 0)
	return pending_reading

const KEEP := -2    # take(KEEP): keep its kind and grow

## Take candidate i of the pending Reading (or settle on the best, i = -1; or keep its kind,
## i = KEEP). Fixed adaptations
## become heritage; pending grafts are taken while there are slots; the Tally starts again,
## keeping the Pattern as the intention.
func take(i := -1) -> Dictionary:
	var cands: Array = pending_reading.get("candidates", [])
	if cands.is_empty():
		return {}
	var settled := i == -1
	var n := int(pending_reading["instar"])
	var c: Dictionary = cands[0 if i < 0 else clampi(i, 0, cands.size() - 1)]
	var kept := false
	if i == KEEP:
		var own_kind := kept_kind(n)
		if not own_kind.is_empty():
			c = own_kind
			kept = true
	var was_form := String(body.get("form", ""))
	var was_sil := String(body.get("silhouette", ""))
	var room := maxi(0, int(Data.rules["genius"]["graftSlots"]) - body.get("grafts", []).size())
	var accepted: Array = pending_grafts.slice(0, room) if n >= 2 else []
	pending_grafts = pending_grafts.slice(room) if n >= 2 else pending_grafts
	body = GeniusReading.take(body, c, accepted)
	instar = n
	history.append({ "instar": n, "form": c["form"], "name": c["name"], "day": day, "by": pending_reading.get("unlockedBy", ""), "settled": settled, "kept": kept })
	_carry_coat(was_form, was_sil)
	var intention: Variant = tally.get("intention")
	tally = GeniusReading.empty_tally()
	if intention is Dictionary:
		tally["intention"] = { "form": intention["form"], "terms": intention["terms"], "fires": 0 }
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
	if look.is_empty() or was_sil == "" or was_sil == String(body.get("silhouette", "")):
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
