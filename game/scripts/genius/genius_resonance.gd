## Resonance: the Pattern's Intention tier from witnessed uses, Resonance from the instar and
## the tier, and what each milestone unlocks. A copy of the tools' src/rules/resonance.ts.
class_name GeniusResonance
extends RefCounted

## Intention tier (0 if no Pattern). inputs: uses, built, sworn, masterInArchetype, stage4Days.
static func tier_for(x: Dictionary) -> int:
	if not x.get("built", false):
		return 0
	var tier := 0
	for t in Data.rules["tiers"]:
		if int(x.get("uses", 0)) < int(t["uses"]): break
		if t.has("stage4Days") and int(x.get("stage4Days", 0)) < int(t["stage4Days"]): break
		if t.get("sworn", false) and not x.get("sworn", false): break
		if t.get("masterInArchetype", false) and not x.get("masterInArchetype", false): break
		tier = int(t["tier"])
	return tier

## Resonance on the instar scale: the higher of the instar and the tier (offset).
static func resonance(instar: int, tier: int) -> int:
	var tier_side := tier + int(Data.rules["resonance"]["tierOffset"]) if tier > 0 else 0
	return mini(6, maxi(instar, tier_side))

static func paying_tier(res: int, tier: int) -> int:
	return maxi(tier, res - int(Data.rules["resonance"]["tierOffset"]))

static func verses(pay_tier: int) -> int:
	var v := 0
	var by: Dictionary = Data.rules["verses"]["byTierEquivalent"]
	for t in by:
		if pay_tier >= int(t):
			v = maxi(v, int(by[t]))
	return v

static func shadow_cap(res: int) -> int:
	return int(Data.rules["genius"]["shadowCapByResonance"].get(str(res), 0))

static func genius_will(res: int) -> float:
	var g: Dictionary = Data.rules["genius"]
	return float(g["willBase"]) + float(g["willPerInstar"]) * (maxi(1, res) - 1)

static func is_accord(instar: int, tier: int) -> bool:
	return instar >= int(Data.rules["accord"]["instar"]) and tier >= int(Data.rules["accord"]["tier"])

static func instar_rule(n: int) -> Dictionary:
	for r in Data.rules["instars"]:
		if int(r["instar"]) == n:
			return r
	return {}

## Which condition has unlocked instar n ("" if none), given milestones reached and the tier.
static func unlock_reason(n: int, milestones: Array, tier: int) -> String:
	if n > 6:
		return ""
	for u in instar_rule(n)["unlockedBy"]:
		if String(u).begins_with("tier:"):
			if tier >= int(String(u).substr(5)):
				return u
		elif milestones.has(u):
			return u
	return ""

## May the Reading for instar n happen on this day? Unlocked, and the genius old enough.
static func reading_due(n: int, day: int, milestones: Array, tier: int) -> String:
	if n > 6:
		return ""
	var reason := unlock_reason(n, milestones, tier)
	if reason == "":
		return ""
	return reason if day >= int(instar_rule(n)["minDay"]) else ""
