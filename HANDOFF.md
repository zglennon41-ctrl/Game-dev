# WILDLINE — Handoff

This is the build-facing version of the design. It replaces nothing in the design docs;
it chooses from them. Where the docs explore, this decides. Where they list options,
this picks one and says why. Read it top to bottom once, then use §5 (the slice) and
§9 (decisions) daily.

Source docs, for depth:
- Design Bible — https://claude.ai/artifact/8XisZssaRVrz4gRMYfqe2n
- Systems (15 tabs) — https://claude.ai/artifact/2g1k1EJT7Mbnr3ujqPZVH9
- The Guide: Field, Genius, Jobs — https://claude.ai/artifact/LD6bW3LhYrpS2jcbd4eM4k

---

## 1. The game in one page

**Fantasy.** You are a member of the best, strangest guild on the line. What you are is
visible on your body, your beast, and your name, and nothing about you is a number you
picked: everything is something you did.

**Loop.** Hub → board → party of three → ride the line → a 20–40 minute excursion →
home to a hall that has changed. The hall is home. The excursion is the game. The world
keeps its appointments on real time.

**Pillars.**
1. The hall is home: a roster of individuals with lives, a hearth with the dead.
2. Every rule has a reason: one logic from the field down, legible enough to argue about.
3. Excursions are the game: PSO's loop, Monster Hunter's prep, named members at risk.
4. Consequences are real: houses, a Charter, deaths, a political map that moves.
5. What you are is visible: Shape, blood, genius, gear, and jobs the world remembers.

**Comparables.** Phantasy Star Online (loop), Fairy Tail (tone), Hunter × Hunter (system),
Game of Thrones (world), Guild Wars (builds), Legend of Dragoon (timing).

**Shape of a character.** Blood (born with) → Shape (read at the rite) → Stages (trained,
four) → techniques (learned, graded by use) → archetypes (earned by witnessed work) →
a Pattern (a vow) → a genius (the field embodied, read from play). Three characters per
account per server. Every character passes through the Academy and graduates into a guild.

---

## 2. The world in one page

Earth, ten thousand years after the Awakening, when will became a physical force. Twelve
fortress cities on the old rivers, each a genre; three reachable at launch (Columbia on
the Potomac: gunpowder and law; Cahokia on the Mississippi: river-steam; Lunden on the
Thames: gaslamp airships). Between the cities, the wild: unstable fields, old-world ruins,
beasts that molt, the Quiet (places with no field). Rail lines, mostly underground, hold
the cities together; junction halls keep the tunnels open with their resonance fields.

The player's guild holds Cumberland Junction in the Appalachian spine, where the Columbia
line, the Cahokia line, and the airship dock meet. Five houses of Columbia (Calvert,
winged; Carroll, dragon-blooded; Howard, shapechangers; Key, demon-blooded; Banneker,
demigod) are bloodlines with seats, heirs, and wants. The Linewright Compact charters
junctions and publishes the Ledgers. The Charter is the rules of the game, amended by the
server every third winter.

Everything with a name in this world is derived from something real and grown forward.
That is the rule for new content too.

---

## 3. The spine

Ten systems, in dependency order. Each entry: purpose, the core rule, the numbers that
matter, and what it depends on. Detail lives in `docs/`.

### 3.1 Field
- **Purpose.** The physics of magic. Everything a character does in a fight is this.
- **Rule.** A field has Will (100), reach, density, a Shape (one of six, read at the
  rite), a pulse (tempo), and a leak. Training is four Stages: Hold (guard, contain),
  Shape (stance, ×2), Project (techniques, ×3), Pattern (signature, ×4). Still closes the
  field; Fold concentrates it.
- **Numbers.** Regen 4/s open, 0 Still; perfect Hold refunds 10; stance 2/s; technique
  8–25; faint at 0 until 20. Reach: skin, 2 paces, 10 paces. Six Shapes on a wheel
  (Anchor, Turn, Cast, Read, Bind, Make); affinity 100/80/60/40 by distance; opposite is
  the counter.
- **Depends on.** Nothing. Build first.

### 3.2 Terms and Patterns
- **Purpose.** The character's signature and the game's expression system.
- **Rule.** Pattern = one Form (a technique of the character's own Shape) + up to three
  Terms, one per kind: Trigger (when it may fire, ×1.5, cannot be breached), Toll (what
  it costs, ×2, auto-taken), Bar (what it may never do, ×1.5, the risk). Sworn before
  three witnesses doubles it. Sworn breach: Pattern lost for good. Unsworn breach: lost a
  season. Grammar: 20 Triggers, 20 Tolls, 15 Bars; the engine judges breaches.
- **Numbers.** Chain 3 beats + 1 per Term; ×9 ceiling. Intention tiers by witnessed use:
  I built, II 50, III 150, IV 400, V sworn + Master; each tier adds a verse (a beat).
- **Depends on.** Field.

### 3.3 Combat
- **Purpose.** Third-person, real time, on the pulse.
- **Rule.** Real-time action (owner's decision, 2026-11-05: the beat is secondary to good
  real-time gameplay). The four Stages are the verbs: Hold (block; a block tapped just
  before a blow lands is a parry), Shape (the stance), Project (strikes, combos and
  techniques, which always work fully when pressed), Pattern (the signature). Dodge is a
  fifth input. The timing layer lives only in the parry and in the Pattern's chain, which
  plays on the character's pulse. Beasts have a Shape and a molt and telegraph their
  attacks; three breaks from techniques of the opposite Shape stagger them. Party of three
  plus three geniuses; Chord (shared perfect timing) is to be redesigned for this model.
- **Numbers.** Parry window 0.2 s; Pattern cue window 200 ms on Green (150 above). Health
  100. Down timer 60 s. No player death except Sworn characters. Feel numbers in
  `data/combat-room.json`.
- **Depends on.** Field, Terms.

### 3.4 Genius
- **Purpose.** The field embodied as a companion; the lineage system.
- **Rule.** Created from a Seed (a one-line leaning), not a body. First Form read at the
  rite from Seed + blood + Shape. Six instars over a life, unlocked by milestones (Gate,
  first Pattern, Adept, Master, Accord), each a Reading: the Tally of play scored against
  the form lattice, three candidates offered, player picks or settles; the base form
  changes every time and carries 1–3 heritage features plus the Seed-mark. Six
  Expressions: Beast, Kith, Engine, Relic, Daemon, Aspect. Five change mechanisms:
  growth (instars), adaptation (reversible features from recent play), specialization
  (Focus, secondary forms), hybridization (grafts from party-mates, beasts, shades, blood),
  form change (Shift, the Quiet, falls, Union, Reversion).
- **Resonance.** The higher of the genius's instar and the Pattern's tier; both fight at
  it. An evolution grants the Pattern its next verse; a tier gained unlocks the next
  Reading. Neither side loses the one the player neglected; the neglected side's shape
  is read from the other.
- **Numbers.** Minimum days 0/7/30/90/365/540. Genius Will 40 +10 per instar. Witness
  10 paces, 10 uses to a shadow, cap 1/2/3. Adaptation slots 2; grafts 3; secondary
  forms 3; Shift 20 Will. Lattice: 36 silhouettes + 12 hybrid, ~60 features, 120 named
  forms at launch, as compositions (silhouette + features + palette).
- **Depends on.** Field, Terms, Combat.

### 3.5 Skills and Archetypes
- **Purpose.** Private skill becoming public identity; the greatest job system.
- **Rule.** A technique belongs to a Shape family (3 per Shape, 9 techniques each) or a
  Discipline (a city school: weapon class, stance modifier, 3 techniques, a rite of the
  school). Techniques grade by use: Learned, Practiced (100, ×1.2), Perfected (500,
  ×1.5, −25% Will). An archetype is Shape × Discipline: slots 1–3 from family 1, 4–5 from
  family 2, 6 from family 3, 7–9 the Discipline's, plus a capstone. Ranks: Journeyman
  (take it), Adept (10 Marks), Master (50 Marks + a Pattern built in it). A Mark is a
  witnessed quest in the archetype. Build: 8 slots (Pattern, 4 techniques, 2 stances,
  Duet). Founding: three members, three accounts, identical Form + Terms, 10 witnessed
  uses each → provisional; canon at the season turn with 100 server uses, max 12 a
  season; founders' names forever.
- **Numbers.** 72 base archetypes (6 Shapes × 12 Disciplines); 3 Disciplines at launch.
- **Depends on.** Field, Terms.

### 3.6 Quests and Excursions
- **Purpose.** The world asking the guild for something; the run.
- **Rule.** Board refreshes at the lamp hour (04:00 server) with 9–15 postings, 48-hour
  life, each showing line color, poster, pay, Ledger served, and named members at risk.
  Seven types: Linework, Salvage, Hunt, Escort, Writ, Deep Run, Rally. Excursion:
  platform → the car (60–90 s) → areas 1–2 → the post (checkpoint, half restore, push or
  extract) → areas 3–5 → extraction → the hearth. Zones from handcrafted tile libraries
  (12–20 per territory) with fixed set pieces and 3 server-state variants.
- **Numbers.** Line colors Green/Amber/Red/Black; Marks 1/2/3/5; named risk none/low/
  high/certain; Black at night only, the Quiet on the new moon.
- **Depends on.** Combat, Genius (orders), Archetypes (Marks).

### 3.7 Guilds
- **Purpose.** The unit history is written in; the hall as home.
- **Rule.** Founded by three graduates of one cohort from three accounts (NPC classmates
  fill). Charter: Captaincy, Council, or Commons (one vote per account; can refuse Writs
  free; pays double tolls). Roster: 60 player characters + 30 NPC members who arrive by
  Atmosphere (0–100: kitchen, yard, shades, Shape mix, feuds, how the last leaver was
  treated). Officers: Quartermaster, Hearthkeeper, Yardmaster, Archivist; one seat per
  account. Halls are junctions: 48 per server, 12 lit at launch by elder guilds, the rest
  awarded each Thaw by Standing and relit by a Deep Run. Standing decays 10% a season.
  Tiers: Company → Chartered → Great → Seat.
- **Depends on.** Quests, Academy.

### 3.8 Academy and Characters
- **Purpose.** Every character's first act; the recruiting floor; the server's teacher.
- **Rule.** Three slots per account per server. Creation: blood → city → Seed →
  appearance → name → Sworn or not (permanent; can die; double Marks; a fourth Term).
  Cohort = one week's enrollments + 12 NPC classmates. Six lessons (Hold, the rite,
  Shape, Discipline, the line, Project) ending in the Field Examination, a real Green
  run; 8–12 hours first character, 3–4 with advanced standing (rite and exam never
  skipped). Commencement nightly 20:00, Grand on Sunday 18:00: join a guild, found with
  classmates, or leave as a Free Lance. Alts may join the first character's guild: one
  officer seat per account, one vote, never in one party, flagged kin in opposing
  Rallies. Retirement to the hearth leaves a shade and frees the slot.
- **Depends on.** Field, Combat, Genius, Quests.

### 3.9 Calendar, Crises, Server History
- **Purpose.** Real time shapes the world, never the player; servers diverge.
- **Rule.** One real day = one game day. Week: Monday rumors, Wednesday Compact, Friday
  Rally 20:00, Saturday market, Sunday hearth + Grand Commencement. Month: the 1st
  postings, new moon opens the Quiet 3 nights, full moon Hunts ×2. Seasons on the
  equinoxes and solstices (Thaw, Writ, Rally, Dark), 13 weeks, one crisis each: Omen
  (w1–3) → Pressure (w4–9, Ledgers published Wednesdays from w4) → Crisis (w10–12) →
  Reckoning (w13). Three Ledgers per crisis, weight from crisis quests (1/3/9 by color),
  guild declarations (Standing), Favor burned, and the Convention vote in the third
  Dark; heaviest wins with ≥25% or the default holds. Every ending writes the line map,
  the houses, the Archive, the roster of the named, and the Chronicle. Three years = a
  Charter term; the Convention amends from a bounded list of 12. Echoes replay past
  crises for late players. Caravans carry one archetype between servers a season.
- **Never gated by the clock.** Lessons, Stages, Marks, ranks, gear, zones below Black.
- **Depends on.** Everything above; built last in the slice, simulated first.

### 3.10 Houses and Economy
- **Purpose.** Politics and money, both as consequence.
- **Rule.** Favor per house per character (−100 to 100) from Writs; tiers at ±20, ±60.
  Writs carry decision timers by Charter (2 h / 12 h / 24 h). Writ wars: Red zones,
  consensual, named members at risk, Writ season only. Houses have heirs who can die; a
  house with no heir at a season turn ends. Four currencies that never convert: Notes
  (account wallet), Favor, Standing, Marks. Gear tiers by line color; the Smith reforges,
  tempers, names (1 h / 6 h / 24 h). Real money buys cosmetics only.
- **Depends on.** Quests, Guilds, Calendar.

---

## 4. Data model for the slice

All rules are JSON in `data/`, validated by schema. Sketches, not final.

```jsonc
// data/shapes.json
{ "id": "anchor", "opposite": "read", "neighbors": ["make", "turn"],
  "families": ["wall", "weight", "endurance"], "pulseMs": 600, "bowlSign": "the water rises" }

// data/techniques.json
{ "id": "brace", "shape": "anchor", "family": "wall", "beats": 2, "will": 10,
  "stage": 2, "effect": { "kind": "guard", "value": 1.0 }, "tags": ["close"] }

// data/terms.json
{ "id": "struck-first", "kind": "trigger", "text": "Only after I have been struck",
  "multiplier": 1.5, "predicate": "wasStruckThisFight" }
{ "id": "no-weapon", "kind": "toll", "text": "No weapon for the rest of the run",
  "multiplier": 2.0, "apply": "disarmForRun" }
{ "id": "never-unarmed", "kind": "bar", "text": "Never against the unarmed",
  "multiplier": 1.5, "forbids": "targetUnarmed" }

// a Pattern on a character
{ "form": "brace", "terms": ["with-member-behind", "half-health"], "sworn": true,
  "name": "Ridgeback", "uses": 212, "tier": 3 }

// data/forms.json (the lattice)
{ "id": "harrier", "expression": "beast", "silhouette": "beast-ground-hunter",
  "features": ["far-eyes", "crest", "ground-claws"], "fit": {
    "range": { "close": 0.6, "mid": 0.4 }, "families": { "cast.reach": 0.5, "anchor.wall": 0.3 },
    "orders": { "guard": 0.5 }, "seeds": { "watches-from-above": 0.4 } } }

// data/features.json
{ "id": "far-eyes", "slot": "eyes", "bonus": { "readRange": 1.2 }, "fixable": true }

// a genius on a character
{ "seed": "watches-from-above", "seedMark": "far-eyes", "instar": 3,
  "form": "hawk-mask", "expression": "relic", "heritage": ["far-eyes", "set-feet"],
  "adaptations": [{ "id": "dark-eyed", "lastFed": "2027-03-01" }],
  "grafts": [{ "id": "horn-brow", "source": "kin:oona" }], "focus": null,
  "secondary": [], "shadows": [{ "pattern": "stoop", "uses": 14 }], "will": 60 }

// the Tally (since last Reading)
{ "families": { "cast.reach": 180, "anchor.wall": 90 }, "range": { "close": 240, "far": 30 },
  "orders": { "guard": 120, "hunt": 15 }, "company": { "anchor": 100, "read": 40 },
  "ground": { "tunnel": 60, "ruin": 30 }, "intention": { "form": "stoop", "terms": [...] , "fires": 110 },
  "bonds": { "shades": ["old-marshal"], "runsWith": { "oona": 101 } } }

// data/beasts.json
{ "id": "cut-wolf", "shape": "bind", "molt": 2, "health": 180, "pulseMs": 500,
  "behaviors": ["readsStance", "targetsLeak"], "breakWindowBeats": 3 }

// data/zones/cumberland-cut.json
{ "id": "cumberland-cut", "color": "green", "territory": "the-cut",
  "areas": 3, "post": 2, "boss": "bridge-thing", "variants": ["lit", "dark-line", "winter"] }

// data/quests.json
{ "id": "linework-cut-1", "type": "linework", "poster": "compact", "zone": "cumberland-cut",
  "color": "green", "pay": 40, "ledger": null, "namedRisk": [] }

// data/roster.json
{ "id": "oona", "blood": { "tier": "kindred", "id": "ridgefolk" }, "shape": "anchor",
  "discipline": "rider", "pattern": { "form": "wall-stand", "terms": ["with-member-behind", "no-stance-season"], "sworn": true },
  "wants": ["a ram that outlives her"], "feuds": ["hollis"], "atRiskOn": ["red"] }
```

Pure functions in `src/rules/`:
- `field.ts` — Will spend/regen, states, reach by Stage, affinity by wheel distance.
- `terms.ts` — build a Pattern, compute multiplier and chain length, judge a breach.
- `combat.ts` — beat judgment, break counting, Chord detection.
- `reading.ts` — score forms against a Tally, return 3 candidates with heritage.
- `resonance.ts` — tier from uses, Resonance from (instar, tier), what each milestone unlocks.
- `marks.ts` — Marks by color, rank thresholds, founding eligibility.
- `ledger.ts` — crisis weights and Reckoning (slice: tests only).

---

## 5. The vertical slice

Scope: one character, one Shape (Anchor), one Discipline (Marshal), one zone (the
Cumberland Cut), one hall room (the common room), six roster members, a genius with two
Readings, co-op for three. Everything else is data that exists but is not reachable.

| Step | Build | Done when the owner can… |
| --- | --- | --- |
| 0 | Rules as data; headless simulator | Run `npm run sim` on a scripted life and read what the genius became and what the Pattern pays |
| 1 | Pulse combat room | Fight one wolf for two minutes with Hold/Shape/Project on a visible beat and say it feels good |
| 2 | Pattern builder | Build a Pattern from a Form and three Terms, see the multiplier, fire it as a chain, breach a Bar and lose it |
| 3 | The Cumberland Cut | Run three areas, hold the post, choose push or extract, beat the bridge-thing, in 20–40 minutes |
| 4 | Genius | Give orders, watch it Witness, take the Gate Reading with three candidates, see heritage carried |
| 5 | The hall | Read a board of nine postings, take one with a named member at risk, fail it, and find them gone from the common room |
| 6 | Co-op | Run the Cut with two friends, hit Chord once, revive one of them |

Acceptance for the whole slice: a new player, with no explanation, understands within
one run that the beat matters, that the Pattern is a vow, and that the genius is watching
them. If any of the three is not understood, the slice is not done.

---

## 6. Build order and milestones

Each milestone is playable and ends with the owner playing it.

1. **Week 1–2: Rules + sim.** Schemas, loaders, `field`, `terms`, `resonance`,
   `reading` with tests from `docs/three-lives.md`. `npm run sim` prints a year.
2. **Week 3–4: Pulse room.** PixiJS scene, beat ring, one beast, Hold/Shape/Project,
   hit feedback. Tune the window. Nothing else until it feels right.
3. **Week 5: Pattern builder.** UI over `terms.ts`; the chain; breach.
4. **Week 6–8: The Cut.** Tiles, areas, the post, the boss, extraction, the tally.
5. **Week 9–10: Genius.** Follower AI, orders radial, Witness, the Reading screen.
6. **Week 11–12: The hall.** Common room scene, board, roster cards, named risk, death.
7. **Week 13–14: Co-op.** Three clients, server-authoritative beat, Chord, revive.

Timeboxes are honest guesses; the order is not negotiable.

---

## 7. The simulator

`src/sim/` runs a scripted life (a JSON of play per day: runs, families used, range,
orders, Pattern fires, company) through the rules for a year and reports: Stages reached,
techniques and grades, Marks and ranks, Pattern tier, each Reading's candidates and the
pick, adaptations gained and lost, grafts offered, Resonance over time. Three scripted
lives ship in `data/lives/` (Mira, Tobiah, Sable from the Guide); their expected outcomes
are the tests. The simulator is how the owner tunes the Reading without playing a year.

---

## 8. Not in the slice

Built so far: the rules and simulator, the combat room, the creator and the opening, the whole
Academy (six lessons, the rite, the Field Examination, the Gate, Commencement), the genius
system (Reading, Resonance, orders, adaptations, grafts, secondary forms, shadows) and the
art pipeline with First Form blockouts. Not yet: Amber/Red/Black lines; Disciplines beyond
the three launch cities; guild founding, Charters, Atmosphere, Standing; the calendar,
crises, Ledgers, Chronicle; houses, Favor, Writs; economy, gear tiers, the Smith; secondary
forms, grafts and shadows in play (the rules exist, nothing yet earns them); shades; Rallies
and PvP; airship routes; cosmetics; the server's mastery progression and the deaths that
end a life; finished art (the blockouts are placeholders in the right shape).

---

## 9. Decisions

**Decided** (do not ask again):
- **The Academy is a solo, offline game of its own** (owner, 2026-11-05). Every character
  plays it alone before entering a server; it introduces the world, the gameplay and the
  character systems, and gives the field and the genius time to grow into something unique.
  It is the full 8–12 hours, walkable in 3D (the quad, the yard, the hearth hall, the
  dormitories, the Instructors' tower, the Gate). The cohort is the twelve NPC classmates,
  generated new for every run. Nothing in it happens on a server.
- **The rite can surprise** (owner, 2026-11-05): the bowl reads the Shape from the
  questionnaire, how the Academy has been played, and its own chance, and may disagree with
  the questions. It plays as a slow, anticipatory reveal (a monster-breeding game's disc
  reading): pour, the Shapes' lights spinning and slowing, the landing, then the genius made
  in the fire.
- **Art** (owner, 2026-11-05): AI-assisted, cleaned up by hand, with Blender as the workbench;
  grounded proportions (not chibi); a painted card for every genius form, shown at the rite.
  The art bible is `docs/art-bible.md`.
- **The genius system is built first, whole** (owner, 2026-11-05), so everything after it has
  the same scaffolding: the Reading, Resonance, instars, the Tally, orders, adaptations, grafts,
  secondary forms, shadows and falls, in the game and matching the tools; and geniuses
  assembled from bodies and socketed parts that art files replace by name.
- **The Academy is finished as a whole, polished sequence that ends with a settled field**
  (owner, 2026-11-06): Lesson 5 (the line: a party of three, the Green zone, the post,
  extraction, orders), Lesson 6 (Project: the field opens to Stage 3), the Field Examination
  with the field open, the Gate Reading (the genius's Second Form) and Commencement. The
  character that leaves is settled: Shape, Stage 3, Discipline and weapon, Pattern, a genius
  in its Second Form, and a record of how they were made.
- **The server is a mastery progression to a death** (owner, 2026-11-06). After the Academy,
  the player learns to use their field and to cover its weaknesses by levelling, until the
  character dies: of old age, of injury, or by spending the whole field at once in a grand
  working that leaves a lasting effect on the world at the cost of their life. The Academy
  teaches toward that life; the server's own rules are later steps of the slice.
- **Every Reading offers three, the rite included** (owner, 2026-11-06): the bowl shows three
  First Forms with their reasons and the player chooses, or lets it settle.
- **After a death, the player chooses how much Academy to replay** (owner, 2026-11-06): the
  whole term, or advanced standing (the rite, the Field Examination and the Gate never skipped,
  the drills compressed).
- **A life is about 300 hours of play** from the Gate to death of old age (owner, 2026-11-06):
  months per character; a death is an event the server notices. The mastery progression is
  paced to that.
- **After the Academy is polished, the art comes next** (owner, 2026-11-06): the remaining
  First Forms in Blender (bodies, parts and cards), so every rite has real art.
- **The Academy is the MMO, offline, at every level** (owner, 2026-11-07, after playing the
  first version through in thirty minutes): eight to twelve hours of a term that carries a
  season-long crisis arc (Omen, Pressure, Crisis, Reckoning, with Ledgers the cohort's quests
  weigh and an ending that writes the world the character leaves with); the full quest board
  (Linework, Salvage, Hunt, Escort, Writ, Deep Run, Rally) run in zones around Alexandria;
  deeper lessons and mastery (technique grades, more of each school, Pattern building at the
  hearth, a harder Examination). The cohort's classmates are agents of their own: goals, a
  schedule, a fighting style from their Shape, school and temperament; in a party they choose
  their own targets and techniques, retreat, and can be lost.
- **AAA standard is the bar for art and interface** (owner, 2026-11-07). Art on two tracks at
  once: grounded models, real lighting, animation and effects built now (AI-made assets made
  and improved through Blender in the development environment, and grounded CC0 where it
  serves), with briefs and a drop-in pipeline for assets the owner generates with their own
  tools. The fight HUD and the menus, sheets and pages are to be redesigned. The genius
  mechanics are the direction to keep.
- **No one dies at the Academy** (owner, 2026-11-05). Its wards make training safe, and on
  expeditions a rescue team stands by: a downed student is pulled out, and failing costs the
  run something but never the character.
- **Death belongs to the server, and it is rare and spectacular** (owner, 2026-11-05). It can
  happen on a character's first night on the server and leaves a lasting mark on the player.
  A new character starts again at the questionnaire and the Academy. What carries over is a
  mix of memory (the world remembers), lineage (something of the dead reaches the next) and
  unlocks (new options for the next run), depending on how and why the character died.
- The game opens with a character creator of questions (2026-11-05): answers suggest a blood
  (confirmed or changed by the player) and make the Shape, city, weapon, Seed and a first
  Pattern, which the character has from the start and outgrows. Then the world encounter, the
  Academy recruiter (Instructor Ilse Varga), one year later, Act 1 at the Academy. All six
  Shapes are playable from the start.
- Rules are data; the Reading and Ledgers are deterministic and tested.
- Combat is real-time action; the beat lives only in the parry and the Pattern
  (2026-11-05). Online play stays at Step 7 of the slice. Placeholder art is CC0.
- Terms are a flat grammar (no severity tiers). ×9 is the ceiling.
- One Pattern per character, rebuilt at the Thaw.
- Resonance is the higher of instar and tier; each milestone unlocks the other side's
  next step; the neglected side's form is read from the other.
- The genius's base form changes at every instar; forms are compositions from a lattice.
- Adaptation slots: 2. Grafts: 3. Secondary forms: 3. Reversion once per life.
- Notes are an account wallet per server; the other three currencies are personal.
- Canonization cap 12 a season; founding needs 3 accounts.
- Ledgers hidden weeks 1–3, published from week 4.
- No open-world PvP. Rallies and Writ wars only.
- Engine: Godot 4 (owner's decision, 2026-11-05), 3D third-person from Step 1. The
  earlier plan of a browser prototype first was dropped.

**Deferred** (ask the owner when the slice reaches them):
- What becomes of the genius when its partner dies (a shade, as the systems say; freed;
  inherited; something else).
- The grand working that ends a life (its name, what it can do, who can witness it, what it
  leaves behind) and how old age and injury accrue: the server's rules, to be designed with
  the owner before the hall is built.
- Which deaths carry over what (memory, lineage, unlocks), and whether Sworn survives as a
  separate flag now that any character can die on the server.
- Perfected at 500 uses or 300.
- Whether a Reading can be refused outright for one instar.
- Whether a Kin-form survives a partner's retirement.
- Whether a Sworn death in a crisis zone adds Ledger weight.
- Hall lobby size before the common room stops feeling like one.
- Whether the Unfounded has a face.

---

## 10. What good looks like

The owner opens the prototype, fights a wolf on the beat, builds a Pattern, swears it,
runs the Cut, loses a roster member because he pushed past the post, comes home, and
his genius offers him three bodies and the reason for each. He closes it and wants to
run the Cut again, differently. That is the slice. Everything in `docs/` is what comes
after.
