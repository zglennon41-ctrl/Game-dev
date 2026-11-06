## The zones around Alexandria (data/zones.json): each a tile library, a set of areas chained
## by their doors, and the beasts of the zone. An area becomes a place the Academy can walk
## (the same shape as data/academy.json's places) by Zones.area_place, with the pack, the
## props and the variant drawn from a seed, so no two runs through it are the same.
class_name Zones
extends RefCounted

## A place id of the form "<zone>/<area>".
static func is_zone(id: String) -> bool:
	return id.contains("/")

static func zone_of(id: String) -> String:
	return id.split("/")[0]

static func area_of(zone_id: String, area_id: String) -> Dictionary:
	return Data.by_id(Data.zone(zone_id)["areas"], area_id)

## The ids of a zone's areas, as place ids.
static func places_of(zone_id: String) -> Array:
	return Data.zone(zone_id)["areas"].map(func(a): return "%s/%s" % [zone_id, a["id"]])

## A walkable place from an area: its beasts (the pack's size drawn by the seed), its doors
## pointing at sibling areas, its post and set piece, and the zone itself for the world to draw.
static func area_place(id: String, seed_value: int) -> Dictionary:
	var parts := id.split("/")
	var z: Dictionary = Data.zone(parts[0])
	var area: Dictionary = area_of(parts[0], parts[1])
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value * 31 + hash(id)
	var which := String(area.get("beast", "common"))
	var beast_id: String = z["beasts"]["common"] if which == "common" else (z["beasts"]["elite"] if which == "elite" else which)
	var pack: Array = []
	if area.has("pack"):
		for i in rng.randi_range(int(area["pack"]["min"]), int(area["pack"]["max"])):
			pack.append(z["beasts"]["common"])
	var doors: Array = []
	for d in area["doors"]:
		var dd: Dictionary = d.duplicate()
		dd["to"] = "extraction" if d["to"] == "extraction" else "%s/%s" % [parts[0], d["to"]]
		doors.append(dd)
	var spec := {
		"id": id, "name": area["name"], "size": area["size"], "floor": "wild", "walls": "wild", "spawn": area["spawn"], "doors": doors,
		"spots": [], "instructors": area.get("instructors", []), "rails": area.get("rails", false),
		"zone": { "id": parts[0], "area": parts[1], "beast": beast_id, "ground": z["ground"], "night": z["night"], "colour": z["colour"],
			"pack": pack, "respawn": area.get("respawn", true), "waitForPost": area.get("waitForPost", false) },
		"wild": z, "area": area, "variant": rng.randi(),
	}
	if area.has("post"):
		spec["post"] = area["post"]
	return spec

## Every area of every zone, for tests and the board.
static func all_places() -> Array:
	var out: Array = []
	for z in Data.zones():
		out.append_array(places_of(z["id"]))
	return out
