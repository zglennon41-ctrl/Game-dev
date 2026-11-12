class_name GeniusEquip
extends RefCounted
## The equipment geniuses (data/genius.json, equipment; docs/genius-types.md, "Arms, Regalia,
## Augments"): which of the three kinds a base is, and how large a held one is. A held genius
## is sized to the hand at every stage: it grows by what it shows, not by how big it is.
##
## Every function here is pure and is given the rules (Data.genius()["equipment"]), so that
## the checks can run it without the game (game/tests/check_items.gd).

## Where each kind of model says it is taken hold of, by its base's class.
const BY := { "weapon": "grip", "armor": "wear", "item": "carry" }


## The category a base is in ("arms", "regalia", "augments"), or "" for a companion.
static func category_of(rules: Dictionary, base_id: String) -> String:
	var cats: Dictionary = rules.get("categories", {})
	for id: String in cats:
		if base_id in (cats[id].get("bases", []) as Array):
			return id
	return ""

## The category's words: { name, one, text }, or {} for a companion.
static func category(rules: Dictionary, base_id: String) -> Dictionary:
	return rules.get("categories", {}).get(category_of(rules, base_id), {})

## How a base is sized in the hand: { long, measure, most }, or {} if it is not held.
static func hand(rules: Dictionary, base_id: String) -> Dictionary:
	return rules.get("hand", {}).get(base_id, {})

## The size a thing is brought to, from the size it was made: into the base's length, give or
## take the tolerance. So a Final is never more than a little larger than its Starter.
static func fit(natural: float, long: float, tolerance: float) -> float:
	return clampf(natural, long * (1.0 - tolerance), long * (1.0 + tolerance))

## How much a form's model is scaled to be held. natural: what the rule measures of it (the
## longest side of its box, or its bulk), box_long: the longest side of the whole of it.
static func scale_for(rules: Dictionary, base_id: String, natural: float, box_long: float) -> float:
	var h := hand(rules, base_id)
	if h.is_empty() or natural <= 0.0:
		return 1.0
	var k := fit(natural, float(h["long"]), float(rules.get("tolerance", 0.08))) / natural
	# and with all it has grown, it reaches no further than `most`
	if box_long * k > float(h.get("most", INF)):
		k = float(h["most"]) / box_long
	return k

## The box of a model as it is held: in the frame of the empty it is taken by, at the size it
## was made. Only what shows in the hand is counted (a worn piece alone, where it has one;
## nothing that shows only while it goes free).
static func held_box(model: Node3D, by: String) -> AABB:
	var at: Node3D = model.find_child(by, true, false) as Node3D
	var worn: Node3D = model.find_child("worn", true, false) as Node3D
	var frame := _xf(at, model).affine_inverse() if at else Transform3D.IDENTITY
	var box := AABB()
	var first := true
	for n in model.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi.mesh == null or (worn and not worn.is_ancestor_of(mi)) or _aloft(mi, model):
			continue
		var b: AABB = frame * _xf(mi, model) * mi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box

## How a form's own model is held, from the model itself and its form's body:
## { k: the scale it is given, long: the longest side of it at that scale, natural: what was
## measured, box: its box as made }. {} if its base is not held. form: the form (Data.form),
## base_class: its base's class.
static func sizing(rules: Dictionary, form: Dictionary, base_class: String, model: Node3D) -> Dictionary:
	var base_id := String(form.get("base", ""))
	var h := hand(rules, base_id)
	if h.is_empty() or model == null:
		return {}
	var box := held_box(model, String(BY.get(base_class, "grip")))
	var box_long := maxf(box.size.x, maxf(box.size.y, box.size.z))
	var natural := box_long
	if String(h.get("measure", "box")) == "bulk":
		natural = float((form.get("body", {}) as Dictionary).get("bulk", 1.0))
	var k := scale_for(rules, base_id, natural, box_long)
	return { "k": k, "long": box_long * k, "natural": natural, "box": box }

static func _aloft(n: Node, root: Node) -> bool:
	var cur := n
	while cur and cur != root:
		if String(cur.name).begins_with("aloft"):
			return true
		cur = cur.get_parent()
	return false

static func _xf(n: Node3D, root: Node) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var cur: Node = n
	while cur and cur != root:
		if cur is Node3D:
			xf = (cur as Node3D).transform * xf
		cur = cur.get_parent()
	return xf
