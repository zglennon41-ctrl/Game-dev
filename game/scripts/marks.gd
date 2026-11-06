## Marks: what a character earns for runs and the Academy's work, and the archetype ranks they
## buy. The numbers are data/rules.json ("marks") and data/academy.json ("marks"); the server's
## rules in src/rules/marks.ts give the same answers (the tests hold them to it).
class_name Marks
extends RefCounted

## Marks for a run of a line colour (green 1, amber 2, red 3, black 5), doubled for a Sworn character.
static func for_run(color: String, sworn := false) -> int:
	var m: Dictionary = Data.rules["marks"]
	var n := float(m["byColor"].get(color, 1))
	if sworn:
		n *= float(m["swornMultiplier"])
	return int(n)

## Rank in one archetype. Adept needs Stage 4; Master needs a Pattern built in it.
static func rank_for(marks: int, stage: int, pattern_built_in: bool) -> String:
	var m: Dictionary = Data.rules["marks"]
	if marks >= int(m["master"]) and pattern_built_in and stage >= 4:
		return "master"
	if marks >= int(m["adept"]) and stage >= 4:
		return "adept"
	return "journeyman"

## The base archetype for a Shape and a Discipline (the cell on the grid): {} if none.
static func archetype_for(shape: String, discipline: String) -> Dictionary:
	for a in Data.archetypes():
		if a["shape"] == shape and a["discipline"] == discipline:
			return a
	return {}

## What the Academy pays in Marks for a thing done (data/academy.json, "marks").
static func academy(what: String) -> int:
	return int(Data.academy.get("marks", {}).get(what, 0))
