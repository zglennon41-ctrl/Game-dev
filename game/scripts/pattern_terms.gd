## How the combat room judges a Pattern's Terms: which Triggers are met, what each Toll takes,
## which Bars forbid this moment. Terms the room cannot judge yet are unavailable, with the
## reason shown in the builder. The Terms themselves (text, multiplier) are data/terms.json.
class_name PatternTerms
extends RefCounted

## Why a Term cannot be taken in this room yet ("" if it can).
const UNAVAILABLE := {
	"seventh-beat": "the beat is not counted in real-time combat; to be redesigned",
	"at-night": "comes with the calendar (the zone runs at night or day)",
	"under-sun": "comes with the calendar",
	"with-member-behind": "needs a party (Step 7)",
	"genius-down": "needs your genius (Step 5)",
	"genius-beside": "needs your genius (Step 5)",
	"foe-downed-member": "needs a party (Step 7)",
	"outnumbered": "needs more than one foe (Step 4, the Cut)",
	"ally-sees": "needs a party (Step 7)",
	"blood-bared": "needs blood (bloodlines and kindreds)",
	"out-of-still": "needs Still, an advanced technique",
	"past-the-post": "needs a zone with a post (Step 4, the Cut)",
	"genius-sits-out": "needs your genius (Step 5)",
	"mark-burned": "needs Marks (Step 6, the hall)",
	"day-silence": "needs the hall and chat (Step 6)",
	"infirmary-night": "needs the hall (Step 6)",
	"favor-house": "needs the houses",
	"terms-spoken": "needs witnesses (Step 7)",
	"genius-clock": "needs your genius (Step 5)",
	"tenth-wallet": "needs the economy",
	"guild-standing": "needs a guild (Step 6)",
	"loot-share": "needs loot (Step 4, the Cut)",
	"forget-shadow": "needs your genius (Step 5)",
	"no-duet-season": "needs your genius (Step 5)",
	"year-of-life": "Sworn characters only",
	"never-shared-meal": "needs the hall (Step 6)",
	"never-in-hall": "needs the hall (Step 6)",
	"never-mark-covered": "needs the guild mark (Step 6)",
	"never-sunday": "comes with the calendar",
	"never-cohort": "needs your cohort (the Academy)",
	"never-borrowed-weapon": "needs gear",
	"never-after-fallen": "needs a party (Step 7)",
	"never-quiet": "needs the Quiet",
	"never-person": "the room has no people in it",
	"never-unarmed": "the room has no unarmed foes",
}

static func available(id: String) -> bool:
	return not UNAVAILABLE.has(id)

static func reason(id: String) -> String:
	return UNAVAILABLE.get(id, "")

static func term(id: String) -> Dictionary:
	return Data.by_id(Data.terms, id)

static func of_kind(terms: Array, kind: String) -> Array:
	return terms.filter(func(id): return term(id)["kind"] == kind)

## Is every Trigger met right now? Returns "" if so, else the first unmet Trigger's text.
static func unmet_trigger(f: Fight, terms: Array) -> String:
	for id in of_kind(terms, "trigger"):
		if not trigger_met(f, id):
			return term(id)["text"]
	return ""

static func trigger_met(f: Fight, id: String) -> bool:
	match id:
		"after-perfect-hold": return f.now <= f.parried_until
		"struck-first": return f.p_struck_this_foe
		"below-half": return f.p_hp < float(Data.room["player"]["health"]) / 2.0
		"full-will": return f.p_will >= float(Data.rules["field"]["willMax"]) - 0.01
		"last-standing": return true      # alone in the room, the Anchor is the last standing
		"underground": return true        # the Cut is a tunnel
		"named-aloud": return f.w_named
		"once-per-excursion": return f.stats["patterns"] == 0
	return false

## The Bars that forbid firing now: a list of their texts (empty if none).
static func covering_bars(f: Fight, terms: Array) -> Array:
	var out: Array = []
	for id in of_kind(terms, "bar"):
		var covers := false
		match id:
			"never-twice-one-foe": covers = f.w_pattern_hits > 0
			"never-beast": covers = true
			"never-green": covers = Data.room["line"] == "green"
			"never-save-myself": covers = f.p_hp < float(Data.room["player"]["health"]) * 0.3
			"never-silence": covers = not f.w_named
		if covers:
			out.append(term(id)["text"])
	return out

## Take the Tolls. Called when the Pattern fires, whether or not it lands.
static func take_tolls(f: Fight, terms: Array) -> Array:
	var taken: Array = []
	for id in of_kind(terms, "toll"):
		match id:
			"all-will": f.p_will = 0.0
			"half-health": f.p_hp = maxf(1.0, roundf(f.p_hp / 2.0))
			"no-weapon": f.p_disarmed = true
			"season-no-stance":
				f.p_stance = false
				f.p_stance_locked = true
			"double-cost-next": f.p_double_cost = 3
			"leak-run": f.p_leaking = true
			"scar": f.p_scars += 1
		taken.append(term(id)["text"])
	return taken
