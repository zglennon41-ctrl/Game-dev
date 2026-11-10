# Three lives — simulator acceptance

Three scripted lives run through the rules for a Charter term. The simulator must
reproduce the expected outcomes below, within the tolerances given. These are the tests
for `reading.ts`, `resonance.ts`, `marks.ts`, and `terms.ts` together.

    npm run sim -- --life data/lives/mira.json      (and tobiah, sable)

**The genius in these lives is on the genius tree** (`docs/genius-tree.md`, owner,
2026-11-10). What used to be expected of it here (a Beast with wings, a Kith and a Relic at
the Gate, a worn Relic at the Third Form, a Daemon, Engine and Relic forms with walls) were
expectations of the lattice of forms, which the tree replaced. They are gone, and are not
quietly kept: a life no longer crosses from one kind of thing to another at every Reading.
It settles as one base and becomes more itself.

What every life must show now, whatever the bases say (`tests/three-lives.test.ts` holds
all three lives to this, and names no base, form or lean, because those are the designer's
and change):

- **The rite** offers three different bases, read from the Seed, the blood and the Shape;
  the best fit is called by something of the character's own; what settles is that base's
  first form and carries the Seed-mark.
- **Three refinements** (instars two, three and four): a path, a prong, a finish, each
  offered only from the children of the form before, best fit first, every one carrying the
  Seed-mark. A turning may be offered at the first and only there, and only toward another
  base.
- **Instars five and six**: nothing new is offered. It grows as what it finished as, and
  wears the whole road it took.
- **Heritage**: an adaptation it holds at a Reading and can keep becomes part of it, and is
  never lost afterwards.

What each life is on the bases as they are written today is told below, so that a change
in the data can be read against it. These roads are the data's, not the test's.

## Mira — says ranged, fights close

| | |
| --- | --- |
| Blood | Mark: long stride |
| Seed | Something that watches from above |
| Shape | Cast |
| City / Discipline | Columbia / Marshal |
| Script | Saber at close range in 80% of fights, most blows parried; Guard orders 70%; a shade's Draw-Cut lessons from month 4; 100+ runs beside an Anchor (Oona) by month 10 |
| Pattern | Stoop: Cast Reach; Trigger after a perfect Hold; Toll genius sits out; Bar never against the unarmed |
| At the Gate | If her play has turned from what the bowl read, she lets it turn (`picks`: `turn`) |

Expected:
- By the Gate she has fought close for a week: the `set-feet` adaptation is present and
  fixable, and it becomes heritage and stays.
- At the Gate, if a turning is offered she takes it, and her genius is the hybrid of what
  it settled as and what she has played like; if none is offered it settles on the best of
  its own paths.
- The Third Form is read when the Pattern is built.
- Kin-form offered at the first Reading after 100 runs beside Oona.
- Cross title Deadeye Draw-Cutter by month 18 (Adept in both).
- Accord in year 3 after swearing Stoop with Master Draw-Cutter; founding eligible once
  two other accounts match Form + Terms with 10 uses each.

Today: the bowl offers a Child's bow (her blood and her Seed), a Fledgling hawk and a
Pocket-piece (Columbia leans on the gun). The bow settles. A week of saber work later the
Tally fits a Blade far better than a Bow (0.60 against 0.11), and it turns: an **Edged
Bow**, on the War Bow's path. It becomes a Volley-bow and finishes as an **Arrow-storm**
("one who has been saving it up"), grows great in year 3 and comes to its apex at the
Accord. She said ranged and fought close, and her genius is a bow with an edge on it.

## Tobiah — fires the Pattern, ignores the genius

| | |
| --- | --- |
| Blood | Kindred: Ridgefolk |
| Seed | Something that stands between me and harm |
| Shape | Anchor |
| City / Discipline | Columbia / Marshal |
| Script | Pattern fired in every fight (≈2 per run, 1.5 runs/day); blows blocked, some taken; genius ordered ≤ 50 times a year; plated and set-feet thresholds crossed |
| Pattern | Bulwark Stand: Anchor Wall; Trigger with a member behind; Toll half health |

Expected:
- Intention tier III before the genius reaches the Third Form by milestone; the tier
  unlocks a Reading at day ≥ 30. (Still an open question for the owner: building the
  Pattern unlocks the Third Form first. The test is skipped, as it was.)
- Resonance at month 6 ≥ 4 while instar ≤ 3.
- He never chooses: every form his genius takes is the one the Tally read.
- Tier IV at ~400 uses (month 10–14 at the scripted rate).
- Accord reachable from the Pattern side in year 3 once sworn and Master Bulwark.
- Grafts: only the Kin-form (if the script keeps him beside Mira); no beast or shade grafts.

Today: a Buckler settles (Seed, blood and Shape all call the Shield). He blocks, so it
takes the Wall-shield's path; he takes the blows that get past, so it becomes a Battered
Shield and finishes as a **Shield-biter** ("one who has started biting back"). He ignored
it for three years and it grew teeth.

## Sable — bonds with everything, rarely fires

| | |
| --- | --- |
| Blood | Bloodline: demon-blooded (Key) |
| Seed | Something that owes me |
| Shape | Bind |
| City / Discipline | Lunden / Aeronaut, later Examiner |
| Script | Hearth every Sunday; two shades accepted by month 9; blows dodged or taken; Pattern ≤ 80 fires a year until year 3; Examiner rite in year 2 |
| Pattern | Collection: Bind Contract; Trigger after naming the foe aloud; Toll a point of Favor with Key; Bar never against her cohort |

Expected:
- Shade graft (a feature) offered at the first Reading after acceptance; Shade-walker
  secondary form unlocked from the Third Form.
- Resonance from the genius side: Pattern pays with two verses by the Fourth Form while
  tier is still I or II.
- Fifth Form in year 3 by Master milestone; Accord blocked until tier V (400 uses); a
  scripted burst of 200 fires in the Hearth War reaches it.
- Own-blood graft (`second-face`) available from the Third Form.

Today: an Impling settles (her Seed and her blood). It takes the Surety's path, becomes a
Whipping-imp and finishes as a **Proxy of Record** ("one who writes down every hurt they
bore for someone"), with a shade's lantern, a lantern jaw and her blood's second face
grafted on along the way.

## Tolerances

- Instar dates within ±14 days of expected given the script's rates.
- The forms a life takes are the data's: a change to a base file may change them, and the
  roads told above are then told again, not defended.
- Tier thresholds exact; Resonance exact.
- Any change to the Readings' weights (`data/reading.json`, `data/genius-hybrids.json`)
  that breaks the expectations above is a design change and goes to the owner, not a test
  edit.
