## The three types of genius (docs/genius-types.md; data/genius-types.json): what a genius
## does beside its partner follows from the class of its base. A weapon is taken in hand; a
## defensive item and a ritual item are worn or carried and used; a companion fights at its
## partner's side in a role. This file is the reading of that data, with no fight in it: what
## a genius is, what its base and its path give it, and how to say so. The fight's side is in
## fight.gd ("the genius's type"). Pure: the same genius always reads the same.
class_name GeniusTypes
extends RefCounted

const AGES := ["young", "half-grown", "grown", "prime", "great", "apex"]
const ROLES := ["bulwark", "hunter", "harrier", "keeper", "lookout"]

static func data() -> Dictionary:
	return Data.genius_types()

## The first base of a base's id: a hybrid is its first base's type (wolf+blade is a wolf).
static func first_base(base_id: String) -> String:
	return base_id.split("+")[0] if base_id != "" else ""

## The type a class of base is: weapon, defense, ritual or companion ("" for no class).
static func type_of_class(cls: String) -> String:
	var T: Dictionary = data().get("types", {})
	for id in T:
		if T[id] is Dictionary and (T[id].get("classes", []) as Array).has(cls):
			return id
	return ""

## Does the data say what this base does? (A base nobody has written a type for yet fights
## as every genius did before there were types: it guards and hunts, with no role.)
static func written(type: String, base: String) -> bool:
	var T := data()
	match type:
		"weapon": return T.get("weapon", {}).get("bases", {}).has(base)
		"defense", "ritual": return T.get("items", {}).get(base, {}) is Dictionary and T.get("items", {}).has(base)
		"companion": return T.get("companions", {}).has(base)
	return false

## The path a form is on: the id of the path's form in its base's file ("" while it is only
## settled). A hybrid's path is its first base's.
static func path_of(form: Dictionary) -> String:
	var f := form
	var guard := 0
	while not f.is_empty() and int(f.get("level", 0)) > 2 and guard < 8:
		f = Data.form(String(f.get("parent", "")))
		guard += 1
	if f.is_empty() or int(f.get("level", 0)) != 2:
		return ""
	var id := String(f["id"])
	return id.split(":")[1] if id.contains(":") else id

## What a form is: { type, base, path, level, written }.
static func of_form(form: Dictionary) -> Dictionary:
	if form.is_empty():
		return { "type": "companion", "base": "", "path": "", "level": 0, "written": false }
	var base := first_base(String(form.get("base", "")))
	var type := type_of_class(String(form.get("class", "")))
	var known := type != "" and written(type, base)
	return { "type": type if known else "companion", "base": base, "path": path_of(form), "level": int(form.get("level", 0)), "written": known }

## What a genius is: as of_form, for the form it is now.
static func of(g: Genius) -> Dictionary:
	if g == null:
		return of_form({})
	return of_form(g.form())

## The row of an age (types.ages): { worth, wait }.
static func age_row(instar: int) -> Dictionary:
	var id := String(Genius.age_at(instar).get("id", "grown"))
	return data().get("ages", {}).get(id, { "worth": 1.0, "wait": 1.0 })

## An always-true multiplier at an age: 1 + (m - 1) x worth.
static func at_worth(m: float, worth: float) -> float:
	return 1.0 + (m - 1.0) * worth

static func _laid(base: Dictionary, over: Dictionary) -> Dictionary:
	var out := base.duplicate(true)
	for k in over:
		out[k] = over[k]
	return out

## A weapon genius's weapon: its base's { style, willPerBlow, held, inHand } with `sig`, the
## one signature property its path gives it ({} while it is only settled).
static func weapon_spec(base: String, path: String) -> Dictionary:
	var W: Dictionary = data().get("weapon", {})
	var b: Dictionary = W.get("bases", {}).get(base, {})
	if b.is_empty():
		return {}
	var out := b.duplicate(true)
	out["sig"] = (b.get("paths", {}).get(path, {}) as Dictionary).duplicate(true)
	out.erase("paths")
	return out

## An item's function: its base's always and use, with its path's laid over them, and the
## keys its use names in `grows` multiplied by the worth of its age. { type, worn, wornAs,
## always, use, bend } (bend: the path's own name and sentence, {} while it is only settled).
static func item_spec(base: String, path: String, worth := 1.0) -> Dictionary:
	var b: Dictionary = data().get("items", {}).get(base, {})
	if b.is_empty():
		return {}
	var p: Dictionary = b.get("paths", {}).get(path, {})
	var use := _laid(b["use"], p.get("use", {}))
	for k in use.get("grows", []):
		if use.has(k) and (use[k] is float or use[k] is int):
			use[k] = float(use[k]) * worth
	var out := { "type": b["type"], "worn": b.get("worn", "side"), "wornAs": b.get("wornAs", ""), "always": _laid(b["always"], p.get("always", {})), "use": use,
		"bend": { "name": p["name"], "text": p["text"] } if not p.is_empty() else {} }
	if b.has("great"):
		out["great"] = b["great"]
	return out

## A companion's role: { id, role, shade_id, shade, k, shade_k, text } ({} for a base with
## none). k is the strength of its role's own thing before its age: 1, or shade.pure where
## its path keeps to its role; shade_k the strength of the role it shades toward (0 for none).
static func role_spec(base: String, path: String) -> Dictionary:
	var T := data()
	var c: Dictionary = T.get("companions", {}).get(base, {})
	if c.is_empty():
		return {}
	var R: Dictionary = T.get("roles", {})
	var id := String(c["role"])
	var p: Dictionary = c.get("paths", {}).get(path, {})
	var shade_id := String(p.get("shade", ""))
	var sh: Dictionary = R.get("shade", { "pure": 1.3, "other": 0.5 })
	return { "id": id, "role": R.get(id, {}), "shade_id": shade_id if shade_id != id else "", "shade": R.get(shade_id, {}) if shade_id != "" and shade_id != id else {},
		"k": float(sh["pure"]) if shade_id == id else 1.0, "shade_k": float(sh["other"]) if shade_id != "" and shade_id != id else 0.0, "text": String(p.get("text", "")) }

## The moves a companion has at an age, its role's favourites first (they are kept first as
## it ages, and made first): Fight.genius_moves' answer, reordered. `favours`: move ids.
static func favoured(moves_all: Array, favours: Array, count: int) -> Array:
	var first: Array = []
	var rest: Array = []
	for fid in favours:
		for m in moves_all:
			if String(m["id"]) == String(fid) and not first.has(m):
				first.append(m)
	for m in moves_all:
		if not first.has(m):
			rest.append(m)
	return (first + rest).slice(0, maxi(0, count))

## How slow a weapon type is, 0 (quick) to 1 (the slowest): from the time one of its blows takes.
static func slowness(style: Dictionary) -> float:
	var N: Dictionary = data().get("need", {}).get("slow", { "from": 0.6, "to": 1.2 })
	var blows: Array = style.get("combo", [style.get("shot", {})])
	var total := 0.0
	var n := 0
	for s in blows:
		if not (s is Dictionary) or (s as Dictionary).is_empty():
			continue
		total += float(s.get("startup", 0.0)) + float(s.get("active", 0.0)) + float(s.get("recovery", 0.0))
		n += 1
	if style.has("draw"):
		total += float(style["draw"].get("seconds", 0.0)) * n
	if n == 0:
		return 0.0
	return clampf((total / n - float(N["from"])) / maxf(0.01, float(N["to"]) - float(N["from"])), 0.0, 1.0)

## What a partner's fighting measures, each 0 to 1: what the need for each role is read from.
static func measures(hero: Dictionary, g: Genius) -> Dictionary:
	var w := Data.by_id(Data.weapons, String(hero.get("weapon", "saber")))
	var style: Dictionary = Data.room["styles"].get(String(w.get("style", "blade")), {})
	var lt: Dictionary = g.lifetime if g != null else {}
	var hurts := float(lt.get("fights.hurts", 0.0))
	var parries := float(lt.get("fights.parries", 0.0))
	var blocks := float(lt.get("fights.blocks", 0.0))
	var dodges := float(lt.get("fights.dodges", 0.0))
	var came := hurts + parries + blocks + dodges
	var rng_line: Dictionary = g.tally.get("range", {}) if g != null and g.tally.get("range", {}) is Dictionary else {}
	var landed := float(rng_line.get("close", 0.0)) + float(rng_line.get("mid", 0.0)) + float(rng_line.get("far", 0.0))
	var ranged := 1.0 if String(style.get("kind", "melee")) == "ranged" else 0.0
	return {
		"base": 1.0, "ranged": ranged, "slow": slowness(style),
		# with nothing landed yet, a ranged weapon is taken to fight from far and a melee one close
		"far": float(rng_line.get("far", 0.0)) / landed if landed > 0.0 else ranged,
		"close": float(rng_line.get("close", 0.0)) / landed if landed > 0.0 else 1.0 - ranged,
		"hurtShare": hurts / came if came > 0.0 else 0.0,
		"turnShare": (parries + blocks) / came if came > 0.0 else 0.0,
		"noParry": 1.0 - parries / came if came > 0.0 else 0.0,
	}

## How much a partner lacks what each role supplies, 0 to 1 (need: weights on the measures).
static func needs(hero: Dictionary, g: Genius) -> Dictionary:
	var N: Dictionary = data().get("need", {})
	var seen := measures(hero, g)
	var out := {}
	for r in ROLES:
		var s := 0.0
		for k in N.get(r, {}):
			s += float(N[r][k]) * float(seen.get(k, 0.0))
		out[r] = clampf(s, 0.0, 1.0)
	return out

## What the page says of a need (need.words).
static func need_words(need: float) -> String:
	for row in data().get("need", {}).get("words", []):
		if need >= float(row[0]):
			return String(row[1])
	return ""

## What it does for its partner, for the genius's page and the HUD: { type, title, lines }.
## title: "WEAPON", "DEFENSIVE ITEM", "BULWARK"...; lines: plain sentences, the first what it
## is, then what is always true, what the key does, what its path changes, and for a
## companion how much its partner needs what it supplies.
static func says(g: Genius, hero: Dictionary = {}) -> Dictionary:
	var what := of(g)
	var T := data()
	var type := String(what["type"])
	var t: Dictionary = T.get("types", {}).get(type, {})
	var lines: Array = []
	if not what["written"]:
		return { "type": "companion", "title": "", "lines": lines }
	var title := String(t.get("name", "")).to_upper()
	lines.append(String(t.get("says", "")))
	match type:
		"weapon":
			var w := weapon_spec(String(what["base"]), String(what["path"]))
			lines.append("In your hand: %s" % String(w.get("inHand", "")))
			var sig: Dictionary = w.get("sig", {})
			if not sig.is_empty():
				lines.append("%s: %s" % [String(sig["name"]), String(sig["text"])])
			else:
				lines.append("Its path will give it one property of its own.")
		"defense", "ritual":
			var it := item_spec(String(what["base"]), String(what["path"]), float(age_row(g.instar).get("worth", 1.0)))
			lines.append("%s. Always: %s" % [String(it.get("wornAs", "")), String(it["always"]["text"])])
			lines.append("%s (G): %s" % [String(it["use"]["name"]), String(it["use"]["text"])])
			if not (it["bend"] as Dictionary).is_empty():
				lines.append("%s: %s" % [String(it["bend"]["name"]), String(it["bend"]["text"])])
			else:
				lines.append("Its path will bend what it does.")
		"companion":
			var r := role_spec(String(what["base"]), String(what["path"]))
			if r.is_empty():
				return { "type": "companion", "title": "", "lines": [] }
			var role: Dictionary = r["role"]
			title = String(role.get("name", "")).to_upper()
			lines.append("%s %s" % [String(role.get("does", "")), String(role.get("lacks", ""))])
			lines.append("%s: %s" % [String(role["own"]["name"]), String(role["own"]["text"])])
			if not (r["shade"] as Dictionary).is_empty():
				lines.append("Its path leans it toward the %s. %s" % [String(r["shade"]["name"]), String(r["text"])])
			elif String(r["text"]) != "":
				lines.append("Its path keeps it to its role. %s" % String(r["text"]))
			if not hero.is_empty():
				lines.append(need_words(float(needs(hero, g).get(String(r["id"]), 0.0))))
	return { "type": type, "title": title, "lines": lines }

## One line for a table: what a base's key does and what is always true ("" for a companion).
static func key_line(base: String) -> String:
	var T := data()
	if T.get("weapon", {}).get("bases", {}).has(base):
		return "take it in hand, or let it go"
	var it: Dictionary = T.get("items", {}).get(base, {})
	if not it.is_empty():
		return String(it["use"]["name"])
	return "its orders"

## Should a bot press the genius's key now? One policy for every bot (the room's, the tests',
## the balance tables'), so a table measures the rules and not a bot of its own. guarding: the
## bot's own hand will turn the strike that is coming (a parry is worth more than a strike
## that never comes, so an item that would prevent it is left alone).
static func bot_wants_key(f: Fight, guarding := false) -> bool:
	if f.genius == null or f.genius.fallen or f.p_state in ["down", "pattern"]:
		return false
	var foe_up := f.w_state not in ["down", "absent"]
	match f.g_type:
		"weapon":
			var cost := float(f.g_weapon.get("willPerBlow", 2.5))
			var mine: bool = String(Data.room["styles"].get(String(f.g_weapon.get("style", "")), {}).get("kind", "melee")) == "ranged"
			var theirs: bool = f.main.get("ranged", f.ranged) if f.g_in_hand else f.ranged
			var gap := f.dist() - float(f.beast["radius"])
			if mine != theirs:
				# two reaches: the weapon whose reach fits the distance is the one in the hand
				var fits: bool = (gap >= 4.0) if mine else (gap <= 3.0)
				var misfit: bool = (gap < 2.4) if mine else (gap > 5.0)
				if f.g_in_hand:
					return f.p_state in ["free", "draw"] and (misfit or f.g_will < cost)
				return foe_up and fits and f.genius_key()["ready"] and f.g_will >= maxf(f.g_will_max * 0.5, cost * 3.0) and f.p_state == "free" and not f.p_block_held and f.w_state != "windup"
			if f.g_in_hand:
				# it is let go once it is nearly spent, to rest at the shoulder
				return f.g_will < cost * 2.0 and f.p_state == "free"
			# one reach: it is taken up rested, and used until it is spent
			return foe_up and f.genius_key()["ready"] and f.g_will >= f.g_will_max * 0.9 and f.p_state == "free" and not f.p_block_held
		"defense", "ritual":
			if not f.genius_key()["ready"]:
				return false
			var soon := false       # a strike at the hero about to land
			var winding := f.w_state == "windup" and f.w_target == -1
			if winding and f.w_duration - f.w_timer <= 0.3:
				soon = true
			for fo in f.foes:
				if (fo as Foe).state == "windup" and (fo as Foe).target == -1:
					winding = true
					if (fo as Foe).duration - (fo as Foe).timer <= 0.3:
						soon = true
			match String(f.g_item.get("use", {}).get("effect", "")):
				"set": return soon and not guarding
				"catch": return not guarding and f.w_state == "windup" and f.w_timer >= 0.12 and f.dist() - float(f.beast["radius"]) <= float(f.g_item["use"].get("reach", 3.0))
				"slip": return f.p_state == "flinch" or (soon and not guarding and f.now > f.p_parry_until and not f._blocking())
				"light": return foe_up and f.dist() <= 7.0
				"sight": return foe_up and f.w_state in ["windup", "strike"]
				"toll": return winding and not guarding
	return false
