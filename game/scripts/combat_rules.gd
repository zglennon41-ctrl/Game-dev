## Combat rules that are pure: beat judgment, break counting, Chord detection.
class_name CombatRules
extends RefCounted

## Judge an input at time t (seconds) against a pulse beating at t0 + k * period.
## Perfect within half the window either side of the beat; off-beat is 70% output.
static func judge(t: float, t0: float, period: float, window_ms: float) -> Dictionary:
	var k := roundi((t - t0) / period)
	var offset_ms := (t - (t0 + k * period)) * 1000.0
	var perfect := absf(offset_ms) <= window_ms / 2.0
	return { "beat": k, "offset_ms": offset_ms, "perfect": perfect, "output": 1.0 if perfect else float(Data.rules["combat"]["offBeatOutput"]) }

## Three breaks from the Shape opposite the beast's open a stagger of three beats.
class BreakMeter:
	var count := 0
	var needed: int
	var stagger_beats: int
	func _init() -> void:
		needed = int(Data.rules["combat"]["breaksToStagger"])
		stagger_beats = int(Data.rules["combat"]["staggerBeats"])
	## Returns the stagger beats opened (0 if none).
	func hit(breaks: bool) -> int:
		if not breaks:
			return 0
		count += 1
		if count >= needed:
			count = 0
			return stagger_beats
		return 0
	func slip() -> void:
		count = 0

## Chord: every member perfect on the same beat eight beats running opens three beats of Chord.
class ChordTracker:
	var streak := 0
	var chord_left := 0
	func beat(all_perfect: bool) -> bool:
		if chord_left > 0:
			chord_left -= 1
			return true
		streak = streak + 1 if all_perfect else 0
		if streak >= int(Data.rules["combat"]["chordPerfectBeats"]):
			streak = 0
			chord_left = int(Data.rules["combat"]["chordBeats"])
		return false
