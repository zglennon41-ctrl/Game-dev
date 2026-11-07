# The Academy: the MMO, offline

The owner's direction (2026-11-07): the first Academy, played through in thirty minutes, was
the scaffold. The real one is the MMO at every level, played alone and offline, eight to
twelve hours long, to an AAA standard of art and interface. This is the plan for the rebuild.
Each milestone leaves the game playable; the order is what the owner plays first.

## What the term is

A season at Alexandria: **the Thaw, thirteen weeks**, played as about twenty-five days the
player chooses to spend (lessons take a day each; a day with no lesson is a day on the board,
in the yard, at the hearth, or with the cohort). The clock never gates the player; the
calendar gives the term its shape:

| Week | What the term holds | The crisis |
| --- | --- | --- |
| 1 | Arrival, Hold, the rite, Shape | Omen: rumours, a new zone variant, side quests that point at the trouble |
| 2–3 | Discipline, the line, the board opens (Green) | Omen |
| 4–9 | The board in full (Green and the first Amber), Project, deeper courses, the Examination | Pressure: Ledgers published Wednesdays; crisis quests weigh them |
| 10–12 | The crisis quests; the Deep Run; the Rally | Crisis |
| 13 | The Reckoning; the Gate; Commencement | Reckoning: the ending writes the world the character leaves with |

Twelve classmates live through the same term as agents of their own.

## The milestones

> Status (2026-11-07): M1 to M5 are built (`docs/zones.md`, `docs/academy-board.md`); M6 is
> under way (the wild kit, the beasts and the people reshaped in Blender; lighting per zone);
> M7 is under way (the fight HUD, the chooser sheet and the pause sheet are redone; the pages
> and the title remain).

**M1. The world.** Packs: fights with several foes at once, each with its own behaviour.
Four zones around Alexandria, each a tile library (12–20 tiles) assembled into 3–5 areas with
fixed set pieces, three variants, a post, and the beasts of the zone:

| Zone | Line | Colour | Beasts | Set piece |
| --- | --- | --- | --- | --- |
| The Green hills (the cutting) | Columbia | Green | cut-wolves, the Warden | the den |
| The Shenandoah ruin | Cahokia | Green, Amber | river-things, a ruin-stag | the bridge-thing |
| Harper's Cut junction | Columbia | Green, Amber | molted hounds, a post-breaker | the dark junction |
| The Cahokia river line | Cahokia | Amber | eels of the current, the Barge-Heart | the crossing |

Four beast kinds beyond the wolf (built in Blender on the wolf's rig so they walk and bite),
second-molt behaviour (reads your stance and counters), named beasts that remember.

**M2. The board.** The seven quest types as excursion templates with objectives, failure
conditions and pay, posted daily from the term's state: Linework (hold a post three beats),
Salvage (carry a thing out, no Patterns while carrying), Hunt (a named beast on a timer),
Escort (a car with health, waves from both sides), Writ (a house's errand with a decision
timer), Deep Run (two zones, one extraction), Rally (three against three in the yard, Fridays).
The excursion loop: platform (gear, orders, the party), the car, areas, the post (push or
extract), extraction, the hearth (Marks, witness, loot).

**M3. The crisis.** One season's crisis as data (`data/crises.json`): the Omen's rumours and
side quests, Pressure's Ledgers (three), crisis-tagged quests that weigh them, the Reckoning
that picks the heaviest ending and writes the world state (the line map, the houses, the
named NPCs who lived or died) onto the character for the server.

**M4. The cohort's AI.** Classmates as agents: goals and a schedule through the term; a
fighting style from Shape, school and temperament (their own targets, techniques, stance,
Pattern, retreat when hurt); their own excursions the player may join; they can be lost on
a run (hurt and carried out, never killed at the Academy).

**M5. Deeper lessons and mastery.** Technique grades by use (learned, practiced,
perfected); the school's nine techniques across Journeyman rank; Pattern building at the
Academy hearth under a Hearthkeeper; the Examination as a true Green run with the field
open and an Instructor at the post.

**M6. Art.** Grounded people (built in Blender on the existing rig so the animation library
carries over), beasts on the wolf's rig, environments from a proper kit with lighting and
post-processing, effects for the field; AI-made assets produced and improved through
Blender here; briefs and a drop-in pipeline for assets the owner generates with their own
tools (`docs/art-bible.md`).

**M7. Interface.** The fight HUD and the menus, sheets and pages redesigned: fewer, calmer
elements in fights; one consistent sheet language; gamepad and keyboard first-class.

## What is kept

The creator, the opening, the genius system and its Readings, the rite and the Gate, the
six lessons as the spine of the term, the seeds already planted (Marks, the board, the
shade, the calendar, the declaration), advanced standing.

## Pacing to eight hours (the term as it stands, 2026-11-07)

| Part | Count | Each | Hours |
| --- | --- | --- | --- |
| The opening, the arrival, the rite | 1 | 30 min | 0.5 |
| The six lessons as courses | 6 | 20–30 min | 2.5 |
| The cohort's troubles | 3 | 5–10 min | 0.4 |
| The board: the ten postings the Gate waits for, one of each type | 10 | 20–40 min | 3.5–6.5 |
| The crisis's own postings among them, the Deep Run | | | (in the ten) |
| The smith, the Hearthkeeper, the school's extra techniques, the shade | | | 0.5 |
| The Gate, the Reckoning, Commencement | 1 | 20 min | 0.3 |
| **A term** | | | **7.7–10.7** |

## Validation: the term played by the autopilot (2026-11-07)

The acceptance test for the term is the autopilot playing it end to end on a fresh
character (`--academy --fresh --seed=N --bot --troubles --debug`, with `--shots`), and the
shorter replays from a saved point (`--board`, `--discipline`, `--line`, `--project`,
`--gate`, `--quests`). Under `--debug` the Academy prints what it does (`GO`, `STEP`,
`HUNT`, `TROUBLE`, `EVENT`), so a stall shows as a step that never ends. What the runs found
and what changed, so the next person knows which stalls are real and which are the bot's:

| Found by | What was wrong | Fixed |
| --- | --- | --- |
| full term | A trouble's rematch was set up before the walk to the yard, and the yard wiped it | spar set up after the walk |
| full term | After the rematch, "talk to them" in the yard, where no classmate stands: a step no one could finish | the poster steps into the place for any talk step of a trouble |
| fresh, 15 min | The keepsake could lie at an instructor's feet, and E talked to him instead (298 times) | the keepsake lies in the open and wins the prompt within reach |
| full term | The bot, sent from the yard to the hearth, had no door and stood still (the yard opens only on the quad) | the bot goes by way of the quad; a reached place is stayed in |
| board replays | Postings doubled; the Deep Run was never posted; Lesson 6's "Reach" could not be met by Turn or Cast | deduped; forced every third day; reach measured from the technique's press |
| full term | The Friday rally ends with Bask's standings in the yard, but nothing on the grounds could be acted on during a posting: a step no one could finish | people, doors, the post and the find are within reach during a posting too |
| postings replay | After the last lesson you could sleep only once, so the day never turned and the board never refreshed: the Gate's ten postings were out of reach (the bot talked to an instructor 3,466 times) | in the board phase you may sleep once the day's work is done (a posting or trouble finished today, or the board bare); the morning line says the board, not the Gate |

Clean runs so far: three troubles, Lessons 4–5 and a Linework posting from the board (seeds
4242, 4244, 4251); the hunt, escort and salvage troubles plus Lesson 4 on a fresh character
in fifteen minutes (seed 4242). The full term to the Gate with ten postings is the run still
owed; it is the one that catches a stall two hours in.

## Pacing to eight hours (the first plan)

| Part | Hours |
| --- | --- |
| The opening and arrival | 0.5 |
| The six lessons as courses | 2.5 |
| The board: ten to fifteen excursions of 20–40 minutes | 4–6 |
| The crisis quests, the Deep Run, the Rally | 1.5 |
| The hearth, the cohort, the shade, the Gate | 0.5 |

## After the Academy (the owner's direction, 2026-11-06)

The server is a mastery progression: the player learns to use their field and to cover its
weaknesses by levelling, until the character dies of old age, of injury, or by spending the
whole field at once in a grand working that leaves a lasting mark on the world. A life is
about 300 hours. The Academy is built to lead into that life; its rules are later steps.
