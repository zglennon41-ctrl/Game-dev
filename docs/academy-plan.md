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

## Pacing to eight hours

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
