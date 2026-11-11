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

// data/genius-bases/<id>.json (a base of the genius tree: docs/genius-tree.md; the lattice,
// data/forms.json, is gone). One settled form, three paths, three prongs a path, two finishes a prong.
{ "id": "hawk", "name": "Hawk", "class": "animal", "expression": "beast", "silhouette": "beast-flier",
  "soul": "...", "nature": { "range": { "far": 1.0 } }, "calls": { "seed": { "watches-from-above": 1.0 } },
  "hybrid": { "adj": "Winged", "gift": ["wings", "talons"], "text": "..." },
  "settled": { "id": "hawk-fledgling-hawk", "name": "Fledgling hawk", "sign": "...", "habit": "...", "features": ["wings", "beak"] },
  "paths": [{ "id": "hawk-stooper", "name": "Stooper", "of": "one who ...", "leans": { "shape": { "cast": 1.0 }, "pattern": { "fires": 0.7 } },
    "features": ["talons"], "prongs": [{ "...": "three, each with two finishes" }] }] }

// data/features.json
{ "id": "far-eyes", "slot": "eyes", "bonus": { "readRange": 1.2 }, "fixable": true }

// a genius on a character
{ "seed": "watches-from-above", "seedMark": "far-eyes", "instar": 3,
  "form": "hawk-stooper", "base": "hawk", "expression": "beast", "heritage": ["set-feet"],
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
system (Reading, Resonance, orders, adaptations, grafts, secondary forms, shadows), the art
pipeline (First Form blockouts, the wild kit, six beasts on the wolf's rig), and the
Academy as the MMO offline (2026-11-07): packs, four zones from tile libraries
(`docs/zones.md`), the board's seven quest types posted daily, the term's crisis with its
Ledgers and Reckoning, classmates who fight on their own and keep their own days
(`docs/academy-board.md`). Not yet: Red/Black lines; Disciplines beyond the three launch
cities; guild founding, Charters, Atmosphere, Standing; houses' Favor as a currency; economy,
gear tiers, the Smith; Rallies as PvP; airship routes; cosmetics; the server's mastery
progression and the deaths that end a life; deeper lessons and technique grades (M5); the
interface redesign (M7); finished art (the kits are placeholders in the right shape).

---

## 9. Decisions

**Decided** (do not ask again):
- **Twelve is the base number** (owner, 2026-11-07): twelve cities and their twelve
  Disciplines are the twelve base classes (a Shape and a Discipline make one of the
  seventy-two archetypes); twelve weapon types, three weapons a city; the twelve
  Disciplines fully realized at the Academy (kits of nine, instructors, rites). Ranged
  weapons carry magazines and reload; the bow draws. Creation and development must show in
  the art: the body, the headgear, the cape and its colour, the stature, the hair, beard
  and their colour, the weapon in the hand, the field glowing in the weapon with mastery.
  The bar is a AAA studio game.
- **Answers of 2026-11-07** (owner): one weapon at a time (chosen at creation, changed at the
  school); gear tiers at the Academy, visible: named weapons from Hunts and the Archive
  (three Salvage fragments), fine ones bought with Marks at the yard, no armour yet; one
  Discipline for life, the archetypes grow from it; the Gate opens after ten postings done
  with at least one of each type open; difficulty is the line colour only, the same for
  everyone; the art steers by cel-shaded stylized high detail (Zelda, Genshin: clean shapes,
  banded light, outlines kept, bright colour); the score first (a theme per place and zone,
  stingers for the Pattern, the rite and the Reckoning), generated here as placeholders in
  the right shape, then the cohort's barks.
- **Answers of 2026-11-07, later** (owner, after the term first held end to end): the owner
  plays the term before anything is added, and reports in their own words; after Lesson 6
  the day turns only in the dormitory, and the bunk takes you once the day's work is done
  (a posting or a trouble finished that day, or the board bare); three weapons a city stays;
  the look grows by skin tone first (painted faces later), a rank's trim at Commencement,
  and the bonded genius's colour on the cloak; the crisis's three endings are drafted after
  the owner has played the arc; the cohort's barks stay as floating text until the project
  has voices.
- **First impressions of the play (owner, 2026-11-07)**: the creator's questions are not
  engaging as a list; each step offers five answers at random as cards with an emblem. The
  bodies: a proper body system of the game's own in place of the KayKit placeholders, a
  full-length focus: thirteen homes (the twelve cities and Alexandria), masculine and
  feminine, a musculature slider, every blood's marks reading cleanly, as robust as the
  genius forms, and both systems taking the marks and changes of instars. Decided: 7.5 heads
  (feminine 7.25); our meshes on the KayKit bones so the animations keep playing; face,
  skin palette and dress differ by city; emblem cards only. The plan is
  `docs/bodies-plan.md`. Then (same day): the bodies must be anatomically accurate, the heads
  and the joints above all, or they break immersion; the first lofted bodies are replaced by
  one continuous body grown from a skeleton graph and carved (`tools/blender/anatomy.py`).
  Ratings after that: bodies 7/10, heads 4/10; the head was rebuilt from silhouettes
  (`head.py`). Then: the characters fully realized, the outfits marking the culture they
  grew up in; each home's dress is data (`data/bodies.json`) built by `wardrobe.py`. Then:
  compare the graphics with Dynasty Warriors and improve to compete; the comparison and the
  plan are `docs/graphics-comparison.md`, the first pass done (the second cel shader, detail
  textures, sky ambient, baked occlusion, folds). Then (2026-11-10): "make the body and
  head forms more realistic and distinct; they are horrifying right now." The generated
  bodies are replaced by MakeHuman's CC0 human on the game's bones, each home's people
  shaped by data (`data/bodies.json`, `form`); `docs/bodies-plan.md`, "The human base".
  The ancestry mix and details of each home are a first draft for the owner to rewrite.
  Then (2026-11-10): "review the forms of genii and weapons and improve them across the
  board; also improve the home base design and scale." Done as three passes: the weapons
  redrawn for the human hand and the hands closed round a grip (`docs/weapons.md`); the
  First Forms and seven Second Forms redesigned (`docs/genius-forms.md`); the Academy
  rebuilt as its own architecture at human scale, laid out from data (`docs/home-base.md`).
  Design calls made on the way and left for the owner: the harrier, the stooping kith and
  the chord as drawn; the Academy's layout; whether the small kith should keep realistic
  faces.
  Then (2026-11-10): "expand the genii possible forms and improve the potential for unique
  customization; also review the character creator to reflect the new level and tone of
  the design." The creator is restaged (`docs/art-bible.md` §12): a platform on the line
  at night built from the Academy's kit, the field gathering where the figure will stand,
  portrait lights and four framings down to the face, the figure turned by hand, and the
  reveal as four leaves (the Reading, body, face and hair, dress) with swatches, sliders
  and names for every value. A life now starts with a look drawn by its spark. The genii
  (`docs/genius-forms.md`, the last two sections): fifty-two forms where there were
  thirty-five, twenty-two of them First Forms (the Relic can now be a first genius), every
  form the Academy can reach with a body of its own; and every genius its own: born with
  three coats, markings, a build and a way its light burns, drawn from its partner's Seed,
  Pattern, spark and name (`data/genius-looks.json`), with the coat, the markings and a
  keepsake the partner's to choose on its page. The three scripted lives pick as before.
  Calls left for the owner: `docs/decisions-needed.md` 71 and 72.
  Then (2026-11-10): "figure out how the visual process of genius progression is going
  to work," and the owner was caught at a boss mission with the armoured wolf. The plan
  for how progress shows is `docs/genius-progression.md` (four clocks: a fight, a day, a
  season, a Reading; what stays and what changes; the Reading as six beats; a build
  order), with a first proof in the game: readiness, growth between Readings, the molt
  seams, and a lineage view. The elites were tuned against a bot that parries everything;
  they are now measured against four hands and made fair (`docs/zones.md`, "Elites and
  their guard"). Calls left for the owner: `docs/decisions-needed.md` 73 and 74.
- **A genius has an age** (owner, 2026-11-10): "I want the genius system to be incredibly
  deep but also logical: if the size is too small to be a wolf, maybe it is a pup and
  evolves into a wolf. I want the final stage to be an impressive ally. The process of
  growth reflected by their design, and the echo effect on the player." So: each instar is
  an age (young, half-grown, grown, prime, great, apex); a First Form is the young of its
  kind in name and in proportion; an Apex genius stands taller than its partner with a
  mantle of light; and each instar echoes on the partner's own body, in the genius's coat
  (`docs/genius-progression.md`, "Ages" and "The echo").
- **The genius is the signature** (owner, 2026-11-10): "Everything should be logical. I
  want the genius to be the signature mechanic of the series. It needs to be the best part.
  Every aspect fully developed, a unique expression of character and play." The bar, the
  audit of every aspect against it, and the order to work in are `docs/genius-signature.md`.
  First consequence, built: a genius may always keep its kind at a Reading and grow (a pup
  into a wolf; a hawk into a griffin, the elder of its kind), and its coat goes with it
  into a new body. (The genius tree, below, made this the whole rule: a refinement offers
  only the forms of its own tree, so there is nothing else to keep and no fourth choice.)
- **Full variety, logically sound, the diversity of humanity** (owner, 2026-11-10): "Build
  the most complex and full variety version that is logically sound and clever while
  capturing the diversity of humanity." Variety must come from somewhere a player can name:
  the partner's home (kinds native to each of the thirteen homes, and a piece each home
  puts on its genii), Seed, blood and Shape, its age, its born look, the partner's choices,
  how the partner plays (it fights as what it is; Free follows the partner's play), and
  what it has met. Every classmate has a genius of their own. `docs/genius-signature.md`.
  Built in four parts: twenty-six kinds native to the thirteen homes with a home lean at
  the rite (`docs/genius-forms.md`); a genius that fights as what it is, with nine moves by
  kind and feature, four working orders and an age that matters (`docs/genius-combat.md`);
  the piece each home puts on its genii; and the cohort's twelve genii. Calls left for the
  owner: `docs/decisions-needed.md` 75 to 78.
- **The genius tree** (owner, 2026-11-10, replacing the lattice and the home kinds): "I am
  still unimpressed. I want each region to not have set forms but probabilistic increases
  to certain forms... at least 20 base forms, with development paths that work as follows:
  level 0 (spark), level 1 (settled), three paths for development, three prongs further
  from the first, two finishing specialization evolutions. I also want hybrids that blend
  the 20 base models that have their own similar development paths and represent
  individuals who change their playtime after the genius settles but before the first
  refinement." A good mix of animals, monsters, magical creatures, items of power, weapons
  and armors. The specification is `docs/genius-tree.md`; a base is one file in
  `data/genius-bases/`; a home's lean is `data/genius-homes.json`.
- **The soul outside the body** (owner, 2026-11-10): "Every path should feel unique. Genius
  are the representation of the soul outside of the body. No level of detail will be enough
  to capture that depth but I love and prefer the attention to detail." So a tree is not
  combat roles with a creature's name on them: a base is a kind of soul, a path is a trait
  in a person, no two paths in the game are earned by the same play, and every form carries
  detail a player can come to know (what it is the picture of, a sign, a habit).
  `docs/genius-tree.md`, "The soul outside the body"; `tools/genius-base-check.py` holds
  the data to it.
- **A line is an evolution** (owner, 2026-11-10, on seeing the whole tree): "I want these
  to be distinct like Pokémon evolutions or digivolutions. Right now it just looks very
  clunky. Baby, three starters, three paths from each starter and hybrid lines, three
  advancements from there, final advancement." So every form on a line is a different
  creature to look at, not its base wearing one more part: its build, its great parts, its
  coat and its light change at every stage, and something of the stage before is always
  carried into the next. The stages, in the player's words: **Baby** (everyone's, before
  the rite), **Starter** (three offered at the rite; the tree's settled form), **Path**
  (three from each starter, and the hybrid lines), **Advancement** (three from each path),
  **Final** (from each advancement), and then it grows great and to its apex. The reading
  taken, and the calls it leaves, are in `docs/genius-lines.md`.
- **Three types of genius** (owner, 2026-11-10): "I also want to create distinct types of
  genius: weapon genius should be their own weapon usable on a switch with their main
  weapon, defensive and ritual items should have functions in combat, companion genius
  should fulfill different roles that balance out the player. The distinctness of their
  genius will be the pride of each player." A base's class says what a genius *does*
  beside its partner, not only what it looks like: a **weapon** (blade, gun, bow) is taken
  in hand; a **defensive item** (shield, gauntlet, coat) and a **ritual item** (lantern,
  astrolabe, bell) are worn or carried and used; a **companion** (the animals, monsters and
  magical creatures) fights at its partner's side in a role that supplies what its partner
  lacks. This does not undo "the soul outside the body": a path is still a trait in a
  person, and its job in a fight follows from that trait. `docs/genius-types.md`.
- **One style** (owner, 2026-11-10): "Generally improve and conform the design of the
  game. I want a universal style for every aspect of the game: lineages, attire, weapons,
  genii, settings, animations. I want this game to have a uniform style that fits the theme
  and tone of the game." The style is the art bible's lamplight gothic, held as data and
  applied to everything the game draws and moves; an asset that is off it is a bug.
  `docs/style.md`.
- **The second pass on the lines** (owner, 2026-11-11, on seeing all 682 bodies): "I want
  a few more companion forms and I want you to do a tightening pass for detail,
  readability, and path uniqueness. I want each one to be intelligent, thoughtful, and
  cool. Also fix the way that the clothing is sitting. I think a full garment won't be easy
  with the mechanics but smaller accessory type genius may solve the problem. Also I want
  probably 50% graphics precision. Don't be afraid to use color to highlight path changes
  and textures. Make sure the anatomy makes sense or if its a magical universe choice lean
  in." And: take the initiative, refine and expand it in a meaningful way. So: every Path
  of every line has **a colour of its own**, and the world stays muted so that a soul may
  carry colour; a body **moves** (wings, tails, flames, eyes that blink); a form must read
  on a dark ground and be a different black shape from its neighbours, and that is
  measured; a body is either sound in its anatomy or leans into its magic on purpose; a
  genius that is a garment is **worn as a small piece** (a mantle on the shoulders), not as
  the whole garment; and there are three more companions, the **Moth**, the **Octopus** and
  the **Carp**. The readings taken (which companions, what "50% graphics precision" means)
  and the calls they leave are in `docs/genius-lines.md`, "The second pass", and
  `docs/decisions-needed.md`.
- **The Angel, the Demon and the Elemental** (owner, 2026-11-11): "Add three more one
  angel line, one demon line, and one line specifically for elementals with a humanoid
  form like tiny demigods." Three more companions, each a whole line of small people (a
  forearm tall; adult and heroic in proportion, not chibi). The **Angel** is conscience:
  the soul of one who answers to something larger than themselves. The **Demon** is
  refusal: the soul of one who will not be told; it is not evil, and it is neither the
  Fiend (a flame) nor the Imp (a clerk). The **Elemental** is the soul of one who is more
  a place or a weather than a person: tiny demigods of Earth, Sea and Sky. None of the
  three takes a real religion's names or symbols: they belong to this world, where magic
  is the will of living things, and an angel's halo is the field's light. That makes
  nineteen companions and twenty-eight lines. Their classes, roles and Paths are calls
  recorded in `docs/decisions-needed.md`.
- **Playable by morning** (owner, 2026-11-11, at night): "The weapons tutorial is broken...
  get everything into a playable AAA studio standard for me to play tomorrow morning. I give
  you creative license to improve the game and the methods you are employing to achieve the
  best result. I want you to really be able to immerse myself in the full game. Also the
  faces of the character creator need a little more work and variety. I want people to have
  beautiful characters and the design of the clothing should be more distinct. I want the
  games graphics to be improved dramatically and upgraded resolution." So, ahead of more
  genius lines: nothing in the game may be a dead end for any character; faces are to be
  beautiful and chosen, not one a home; each home's dress is to be told by its outline and
  its colours; and the picture itself (light, ground, depth, sharpness) is to be raised.
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
- **The owner on the 28 lines** (owner, 2026-11-12, on the tree page): "Some of the trees
  are stronger than others. The wolf tree is incredible, the drake tree is weak, the
  humanoid shaped designs are better for the new ones. The winged shield is goofy. The
  other hybrids look incredible. I love the moth and the octopus as well. Maybe instead of
  coats living armors that are a tank type companion and keep equipment type genius in the
  hand." Read as: the Wolf is the standard a line is held to; the Drake is rebuilt to it;
  the Winged Shield is redesigned; **the Coat line is replaced by the Living Armor**, a
  companion that stands on its own feet and is a Bulwark; and no genius is worn: a weapon
  or an item genius is in the hand (or carried), a companion walks beside. The "maybe" is
  the owner's: the Living Armor is built to be looked at, and the Coat's data is kept in
  git history if it is not liked.
- **Wolves in other skins** (owner, 2026-11-12): "Also some of the figures are just poorly
  adapted wolf figures. The stag is the most glaring example especially at the higher
  levels." Read as: a line built by reshaping the Wolf's body (the Stag, the Fox, the
  Hawk's Harriers) gets a body of its own, with its own animal's anatomy; the Stag first.
- **The Harriers are birds on foot** (owner, 2026-11-12): "Birds on foot. I think things
  like griffins would be good hybrid lines." The Hawk's three Harriers become long-legged
  birds that hunt on the ground, not a wolf's body with a beak. A griffin (and things like
  it: a beast made of two) belongs to the hybrids: a hybrid may be its own creature, not
  only one base wearing another's gift. Which pairs, and how far that goes, is not yet
  settled.
- **The first thirty minutes** (owner, 2026-11-12): "Take a general improvement pass. Start
  with how the game load, check for any bugs, or UI failures", then "Improve the first 30
  minutes and introduction screens." Read as: the title, the questionnaire, the creator,
  the night the field wakes, the recruiter, the year, the gate and the first lesson are
  what a new player judges the game by, and get their own pass for presentation, pacing,
  clarity and feel. Words changed in that pass are drafts for the owner to rewrite.

## 10. What good looks like

The owner opens the prototype, fights a wolf on the beat, builds a Pattern, swears it,
runs the Cut, loses a roster member because he pushed past the post, comes home, and
his genius offers him three bodies and the reason for each. He closes it and wants to
run the Cut again, differently. That is the slice. Everything in `docs/` is what comes
after.
