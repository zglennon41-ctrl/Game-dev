# Three lives — simulator acceptance

Three scripted lives run through the rules for a Charter term. The simulator must
reproduce the expected outcomes below, within the tolerances given. These are the tests
for `reading.ts`, `resonance.ts`, `marks.ts`, and `terms.ts` together.

## Mira — says ranged, fights close

| | |
| --- | --- |
| Blood | Mark: long stride |
| Seed | Something that watches from above |
| Shape | Cast |
| City / Discipline | Columbia / Marshal |
| Script | Saber at close range in 80% of fights; Guard orders 70%; a shade's Draw-Cut lessons from month 4; 100+ runs beside an Anchor (Oona) by month 10 |
| Pattern | Stoop: Cast Reach; Trigger after a perfect Hold; Toll genius sits out; Bar never against the unarmed |

Expected:
- First Form: a Beast with wings and far-eyes (Seed-mark `far-eyes`).
- Gate Reading candidates include at least one Kith and one Relic; all carry `far-eyes`;
  the `set-feet` adaptation is present and fixable.
- Third Form Reading (at the Pattern) offers a worn Relic in the top three.
- Kin-form offered at the first Reading after 100 runs beside Oona.
- Cross title Deadeye Draw-Cutter by month 18 (Adept in both).
- Accord in year 3 after swearing Stoop with Master Draw-Cutter; founding eligible once
  two other accounts match Form + Terms with 10 uses each.

## Tobiah — fires the Pattern, ignores the genius

| | |
| --- | --- |
| Blood | Kindred: Ridgefolk |
| Seed | Something that stands between me and harm |
| Shape | Anchor |
| City / Discipline | Columbia / Marshal |
| Script | Pattern fired in every fight (≈2 per run, 1.5 runs/day); genius ordered ≤ 50 times a year; plated and set-feet thresholds crossed |
| Pattern | Bulwark Stand: Anchor Wall; Trigger with a member behind; Toll half health |

Expected:
- Intention tier III before the genius reaches the Third Form by milestone; the tier
  unlocks a Reading at day ≥ 30.
- Resonance at month 6 ≥ 4 while instar ≤ 3.
- Readings weighted by the Intention line: every candidate set after tier III contains
  at least two Engine/Relic forms with wall or shield features.
- Tier IV at ~400 uses (month 10–14 at the scripted rate).
- Accord reachable from the Pattern side in year 3 once sworn and Master Bulwark.
- Grafts: only the Kin-form (if the script keeps him beside Mira); no beast or shade grafts.

## Sable — bonds with everything, rarely fires

| | |
| --- | --- |
| Blood | Bloodline: demon-blooded (Key) |
| Seed | Something that owes me |
| Shape | Bind |
| City / Discipline | Lunden / Aeronaut, later Examiner |
| Script | Hearth every Sunday; two shades accepted by month 9; Pattern ≤ 80 fires a year until year 3; Examiner rite in year 2 |
| Pattern | Collection: Bind Contract; Trigger after naming the foe aloud; Toll a point of Favor with Key; Bar never against her cohort |

Expected:
- First Form: a Daemon (bloodline lean 70%, Seed lean).
- Shade graft (a feature) offered at the first Reading after acceptance; Shade-walker
  secondary form unlocked from the Third Form.
- Resonance from the genius side: Pattern pays with two verses by the Fourth Form while
  tier is still I or II.
- Fifth Form in year 3 by Master milestone; Accord blocked until tier V (400 uses); a
  scripted burst of 200 fires in the Hearth War reaches it.
- Own-blood graft (`second-face`) available from the Third Form.

## Tolerances

- Instar dates within ±14 days of expected given the script's rates.
- Candidate sets: the named Expressions must appear; exact form ids may vary.
- Tier thresholds exact; Resonance exact.
- Any change to the Reading's weights that breaks these expectations is a design change
  and goes to the owner, not a test edit.
