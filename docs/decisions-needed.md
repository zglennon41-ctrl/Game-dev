# Decisions needed — Step 0

Built while making the simulator pass `docs/three-lives.md`. Each item is a place where the
docs disagree, or where nothing was settled and I had to put something in to make the rules
run. Every one is a value in `data/`, so changing your mind doesn't touch code.

## Where the acceptance test and the Systems doc disagree

**1. Tobiah: "tier III before the Third Form" can't happen today.** The Systems table says
building the first Pattern unlocks the Third Form. Tobiah builds his early, so his Third Form
arrives on day 30. Tier III needs 150 fires, which at his scripted rate is day ~73. The test
is written and **skipped**, marked OWNER QUESTION 1 in `tests/three-lives.test.ts`.
Options:
- (a) Keep the Systems rule and reword the expectation to "tier III before the *Fourth* Form" (this passes today).
- (b) Building a Pattern stops unlocking the Third Form. Then the Third Form comes from tier III, and Mira and Sable reach it later.
- (c) Something else you intended.

**2. Resonance is counted on the instar scale.** Two expectations ("Tobiah: Resonance ≥ 4 at
month 6 while instar ≤ 3" and "Sable: two verses by the Fourth Form while tier is I or II") only
hold if tier III fights like a Fourth Form. That is also how the Guide describes Tobiah. So
Resonance = max(instar, tier + 1). The literal "higher of instar and tier" is
`rules.json → resonance.tierOffset: 0`. Default set to **1**.

**3. Which tier unlocks which Reading.** Systems says tier II unlocks the Third Form, III the
Fourth, IV the Fifth. With that, Tobiah's tier III (day ~73) unlocks the Fourth Form on day 90,
and he would be at instar 4 by month 6, which breaks the expectation in item 2. I shifted it by
one: tier III unlocks the Third, IV the Fourth, V the Fifth (`rules.json → instars[].unlockedBy`).
Confirm or revert.

**4. Tier IV needs "Stage 4 for a year" (Systems).** That is what puts Tobiah's tier IV at month 13,
inside the 10–14 window. He crosses 400 uses around month 5, so "~400 uses" in the expectation
reads loosely. Kept as written in Systems.

## Things I had to fill in (placeholders, all in `data/`)

5. **The form lattice:** 35 forms across six Expressions, plus their features. Names follow the
   Guide where it names them (Hawk, Harrier, Stooping Kith, Talon Relic, Hawk-Mask, Iron Hound,
   tower-shield). The rest are mine.
6. **Reading weights and leans** (`data/reading.json`): how much each line of the Tally pulls
   toward each Expression and feature. The order follows the Guide: intention, then how, then
   where and with whom, then orders, bonds, blood. The numbers are mine.
7. **Term tags** (`data/terms.json → tags`): how the Reading reads a Term (a debt Toll leans
   Daemon, "the genius sits out" leans Relic). Mine.
8. **Seeds:** only the 8 the Systems doc lists. Seed-marks other than far-eyes and ledger are mine.
   The other 16 Seeds are yours to write.
9. **Techniques:** 8 placeholders, enough for the three Patterns and an Anchor starter set. The
   162 are yours.

## Smaller calls

10. **Two Readings on one day.** When Master arrives late, Accord can land the same day and the
   Fifth Form and Apex Readings happen back to back (Tobiah, day 816). Should there be a gap?
11. **Quests with no archetype equipped** count toward Stage 4 but give no Marks. The scripts use
   this so Tobiah reaches Stage 4 early and Adept late. Is that a real thing in the game?
12. **A genius witnesses its own partner's Pattern**, even under Mira's "the genius sits out"
   Toll, so it grows a shadow of it. HANDOFF's genius sketch shows exactly this (a Stoop shadow).
13. **Chain length isn't capped.** Systems says "to six"; the Bible says "three to seven"; with
   verses it reaches 9 here.

# Step 1 — the combat room (real-time, 2026-11-05)

Calls I made building real-time combat. Every number is in `data/combat-room.json` or
`data/beasts.json`.

14. **The cut-wolf is Read-shaped, not Bind.** Breaks come from techniques of the Shape
    opposite the beast's, and the slice has only the Anchor, whose opposite is Read.
15. **Dodge exists and costs 8 Will.** The design docs have no dodge. A real-time action
    game needs one; it has a moment of invulnerability in the middle.
16. **Block takes 30% of a blow and some Will; a parry is a block tapped in the last 0.2 s
    before the blow lands.** No damage, 10 Will back, the wolf reels for 1.4 s.
17. **The sword combo is three swings** (Chop, Diagonal, Sweep), with presses buffered, and
    can be cancelled into a dodge or a block from its recovery. Swords do damage but do
    not break; only techniques break.
18. **Ground Strike** (the one technique): 18 Will, 3.5 s cooldown, heavy, knocks back, breaks.
19. **The wolf** circles, then bites (fast) or pounces (from range). Light hits do not make it
    flinch; every second light hit while it is circling or recovering, it snaps back with a
    quick bite. Heavy hits make it flinch. Its wind-up shows as a red glow, a "!", and its
    reach on the ground.
20. **The starting Pattern is "Breaking Ground"**: Form anchor.weight; Trigger "Only after a
    perfect Hold" (×1.5), Toll "All my Will" (×2), ×3 in all. After a parry it can be fired
    for 3 s. Its chain is five strikes on the Anchor's pulse; each landed strike hits, and
    all five pay base 14 × Stage 4 × 3 = 168 on top. One missed fizzles it; the Toll is taken.
21. **Anchor stance**: hits ×1.5, cannot be knocked back or flinched, moves at 75%, 2 Will/s.
22. **Hit-stop and the parry's slow motion** are part of the feel; both are numbers in `feel`.

# Step 3 — the Pattern builder (2026-11-05)

23. **Three Forms for the Anchor**, one per family: Weight (Ground Strike: a chain of blows,
    then a heavy finisher), Wall (Cannot Be Moved: untouchable while it runs, then a shockwave
    that staggers), Endurance (Second Wind: heals). Their effects and numbers are mine
    (`data/combat-room.json → pattern.forms`).
24. **20 of the 55 Terms work in the combat room.** The rest are shown greyed, with what they
    need (the genius, a party, the hall, the calendar). "Only on the seventh beat" has no
    meaning in real-time combat and needs redesigning.
25. **"After I have named the foe aloud"** is a key (N): the Anchor shouts the beast's name.
    "Never in silence" uses the same naming as its declaration.
26. **The Pattern can be rebuilt any time** in the prototype. The design says once a year, at
    the Thaw; that comes with the calendar.
27. **Swearing happens in the builder** for now. The design puts it at the hall's hearth, on a
    Sunday, before three witnesses (Step 6).
28. **A breach is real time**: unsworn, the Pattern is lost for 91 days; sworn, for good. The
    builder has a "testing only: restore" button so you can keep playing.
29. **Two Bars always forbid in this room** (never against a beast, never on a Green line):
    every use is a breach. They are allowed, and labelled, because a vow can be impossible.

# Step 3 (revised) — character creation and the opening (2026-11-05)

30. **The ten questions and every answer's leanings are mine** (`data/creation.json`). They are
    yours to rewrite: each answer lists what it leans toward and a "because" line for the reveal.
31. **The Shape comes from the answers, leaned by the blood**, and the reveal says the rite at the
    Academy will confirm it. In your design the rite decides the Shape and nobody chooses it;
    should the rite in Act 1 ever disagree with the creator?
32. **Weapons are the three launch cities' weapons from your Combat tab**, chosen by city and by
    how you said you fight. The 3D models are KayKit placeholders (a harpoon is a staff, a
    musket is a crossbow) until there is art.
33. **Each Shape's one technique, stance, and three Pattern Forms are mine**
    (`data/shape-kits.json`): Anchor Ground Strike; Turn Kindle (fire); Cast Closing Strike
    (a dash); Read Read the Break (criticals); Bind Leash (slows); Make Ward (takes a bite).
34. **Only 8 of the 40 Marks exist** (the ones the Blood tab names); the other 32 are yours.
35. **The beast in a fight is always the Shape the hero counters**, so every Shape can break it.
36. **The world encounter cannot kill you**, and a Bar there warns but cannot be broken.
37. **The recruiter is Instructor Ilse Varga** of the Academy at Alexandria, a Read; her lines
    are in `data/story.json`.
38. **Order after this**: I have written the Academy (Act 1) as the next step, and folded the
    Green zone into its Field Examination, which is how your Academy tab describes it.
39. **The look is "lamplight gothic"** (`game/scripts/style.gd`): Cinzel capitals for titles,
    Alegreya for the story, Alegreya Sans for the HUD (all OFL); dark plates with brass rims
    and clipped corners; ink outlines on characters and beasts; moonlight shafts, drifting
    motes of field, and a cool-shadow, warm-highlight film grade. A placeholder direction
    until the game has its own art director; say if it is wrong.
40. **The genius before the rite is a small orb circling the head**, tinted by the Shape.
    In the opening it is born from the burst when the field wakes; it flares on a parry,
    a Pattern cue and a stance, flickers when you are hit, dims with low Will, and settles
    beside you when you fall. Whether the Seed should colour it instead is yours.
41. **The Academy's first Instructors and voices are mine** (`data/academy.json`): the
    Yardmaster is Oren Bask (Anchor) with his genius Millstone; the cohort's eight
    temperaments (earnest, wry, proud, scared, kind, sharp, quiet, reckless) and every line.
42. **Lesson 1, Hold teaches only the guard, the parry and the dodge**: four drills
    (contain your Will, block, parry, five bites in a row) with the other moves locked.
    The lore line I gave it: a waking field leaks Will like lamplight, and that is what
    drew the cut-wolf to you. Yours to keep or change.
43. **Every run's cohort is twelve classmates made from a seed**: two of every Shape,
    names from their cities, random bloods; the run keeps a record (parries, blocks,
    hurts, dodges, talks, who you met) for the Readings to come.
44. **The rite's numbers are mine** (`data/academy.json`, "rite"): about one rite in five
    surprises with the default record; parrying, blocking, dodging, being hit and talking
    each lean the bowl a little toward a Shape. When it surprises, your Pattern keeps its
    Terms and becomes the new Shape's Form with the same effect.
45. **The spark** (`data/creation.json`, "spark"): every character gets a hidden random
    number that nudges the answers' leans (up to 30%) and picks the name, so the same answers
    can make another person. A strong answer (a fear that names a blood) still wins. On the
    reveal, "Another life, same answers" draws a new spark.
46. **Graphics**: options and a recommendation are in `docs/art-direction.md`, with four
    questions for you.
47. **The genius in a fight** (`data/genius.json`, mine): Guard spends 12 Will and half the
    bite, every 6 seconds; Hunt strikes every 2.2 seconds for 5, scaled by its Expression and
    Resonance, only at a foe you are locked on to and within 7 metres. In the practice yard a
    fallen genius stands again after 20 seconds; on the line it will wait for the post.
48. **Order key**: G (pad: D-pad left) cycles Guard and Hunt; J opens the genius page.
49. **The First Form is settled at the rite** (the bowl picks the best fit, with a little
    chance); from the Second Form on, the Reading offers three and you choose. Say if the rite
    should offer a choice too.
50. **The genius page shows the whole Tally** (the systems doc's open question): I chose to
    show it.
51. **The sparring ladder** (`data/academy.json`, lesson "shape", mine): classmates step up
    in order of temperament (the frightened first, the proud last); each rung has 18% more
    health; two wins pass the lesson, a loss repeats the rung; the wards catch whoever drops.
    Classmates fight at close reach with a strike and a heavy blow, whatever their weapon;
    their own techniques and ranged styles are still to build.
52. **Rest closes every day**: the Hearth Hall opens after sleeping on Lesson 1, Lesson 3 after
    sleeping on the rite, and so on. The dormitory line for each night is in `rest.next`.
53. **The Disciplines' first three techniques are mine** (`data/discipline-kits.json`), on keys
    1, 2, 3: Marshal (Covering Fire, Warrant, Last Round), Pilot (Sounding, Line Across,
    Capstan), Aeronaut (Grapple Line, Vent, Ballast), and their Instructors (Captain Ada
    Rourke, Pilot Oyelaran Tane, Dockmaster Wren Halloway). The names in `disciplines.json`
    stand; the effects and numbers are placeholders for you to tune.
54. **Lesson 4 lets you change your weapon** to any your city's school teaches, then ends in
    a bout against your Instructor (health ×1.9). Classmates now bring their school's attack
    to the ladder (a Columbia shot, a Cahokia hook, a Lunden lunge).
55. **Lesson 5 and 6 numbers, mine**: classmates in the party have 90 health and strike for 7
    every two seconds; the foe turns on a classmate about a third of the time; the post is held
    for 45 seconds; the Warden of the Cutting has 520 health and is half again as large; Stage 3
    makes techniques hit half again as hard and reach one pace farther (shots two).
56. **The Gate's write-up** (`data/academy.json`, "gate.writeup") is a list of tests on the
    term's record with a sentence each; the cohort signs it. Yours to rewrite.
57. **Advanced standing** (`data/academy.json`, "advanced", mine): the second character's
    short term skips Lesson 5 (the first run of the line) and the drill steps named there,
    cuts Hold to three bites and the ladder to one win, and keeps the rite, the Field
    Examination and the Gate. The offer appears after the questionnaire once any character
    has left the Academy settled.
58. **First Form blockouts**: all eleven First Forms now have Blender-built bodies, parts and
    cards (placeholder quality, proportions and sockets right). An art body with no rig walks
    with a bob and a lean the game gives it; rigged art will replace that.
59. **The seeds of the MMO planted in the Academy** (owner's direction, 2026-11-06), all mine
    to be rewritten: the board's four troubles and their words (`academy.json`, "board"); the
    hearth's shade, drawn from `shades.json`, accepting a student after three visits and
    firing its Pattern four times a visit; classmates' Patterns (their Shape's first Form,
    Trigger "below-half"), fired once a bout; the three recruiting guilds (the Lamplighters'
    Company, Banneker Commons, the Ninth Car) and the founding promise; the five rumours of
    the season's Omen (the Shenandoah ruin, Harper's Cut, House Carroll's Writ for Enoch
    Vane, the Green's lamps, the Marshal's old enemy); the schools' rites framed on the
    Instructor's test.
60. **What the server will read off a settled character**: Shape and Stage 3; blood; school,
    weapon and three techniques; the Pattern; the genius (Second Form, with any shadow and
    graft); Marks and the Journeyman archetype; the record (parries, bouts, posts, runs,
    troubles, rumours heard, the shade's acceptance); the cohort's write-up; the declaration
    (a guild joined, a founding promised with two named classmates, or free).
61. **The board's pay and pace** (`data/quests.json`, mine): three to five postings a day;
    Linework, Salvage and Escort pay 1 Mark on the Green and 2 on Amber, Hunt and Writ one
    more, the Deep Run 3 and 4, the Rally 1; a Hunt's named beast has 240 seconds; a Writ's
    clock is 200 seconds a step. A classmate takes a posting with you about a third of the
    time. Whether a lost posting should cost anything beyond its Marks is yours.
62. **The crisis's weights and endings** (`data/crises.json`, mine): Green 1, Amber 3, the
    crisis's own postings threefold, a Writ's decision 2; the heaviest Ledger with a quarter
    of the weight wins, else the mile is abandoned. The three endings' words and what they
    write onto the character (the line, the house, the lamps, Enoch Vane) are placeholders
    in the right shape.
63. **The cohort's days** (`data/academy.json`, cohort.schedule, mine): haunts by temperament
    and weekday; two classmates out on runs of their own each day; two days in the infirmary
    for one carried out. Their fighting styles (cohort.fighting): aggression, caution, parry
    and block by temperament; a Pattern once a fight below half. All numbers to be played.
64. **Mastery's pace** (`data/academy.json`, mastery, mine): one more technique for every
    three Marks, up to the school's nine; practiced at twelve uses, perfected at thirty-six
    (+6% / +14% damage, cooldowns 0.9 / 0.8). The eighteen new techniques' names and numbers
    are mine.
65. **The art kits** (`tools/blender/wild_kit.py`, `beast_kit.py`, `people_kit.py`): the
    outdoor pieces, the six beasts on the wolf's rig and the people reshaped on the KayKit
    rig are placeholders in the right shape, made here in Blender. Whether the final look
    comes from refining these in Blender or from your own tools' renders dropped in by name
    is your call; both paths keep the names.
66. **Twelve weapon types** (`data/combat-room.json`, "styles", mine; `docs/weapons.md`):
    the movesets, the magazines (pistol 6, musket 2, scatter 2), the reload times (1.6 /
    2.4 / 2.2 s), the bow's draw (1.1 s, 7 to 21 damage), the staff's wider parry window, the
    maul's break. All numbers to be played; the twelve names are a proposal.
67. **Thirty-six weapons, three a city** (`data/weapons.json`): the ids follow
    `data/disciplines.json`; the names and words are mine (a geometer's astrolabe drawn
    like a bow, an archivist's iron-bound ledger). Whether some cities should carry four is
    yours.
68. **The nine new Disciplines' kits** (`data/discipline-kits.json`): eighty-one techniques
    named and numbered by me on the eleven effects the fight knows, nine instructors in the
    yard with their lines, and the twelve cities offered at the first question of the
    creator with names for each. The twelve Disciplines are the twelve base classes.
69. **The look** (creation, "LOOK"): headgear on or off, the cape on or off and its colour
    (the Shape's, the city's, the blood's, plain); the city's three weapons to carry; the
    weapon's field glows brighter for every technique perfected; the stature; the hair
    (five styles), the beard (two) and the hair's colour (seven); since the body kit
    (`docs/bodies-plan.md`): the sex, the build, the skin tone, every blood's marks as parts
    and tints, the rank's trim, the genius's colour in the cloak and its light in the eyes at
    the instars. Still to come: painted faces per home, and the dress per home.

**Resolved on 2026-11-07** (see HANDOFF §9): 61 (ten postings before the Gate, one of each
type), 66–67 (one weapon at a time; gear tiers at the Academy: named from Hunts and the
Archive, fine for Marks, no armour), 68 (one Discipline for life), 69 (the art steers by
cel-shaded stylized high detail; the next people effort is open), and sound: the score
first, then barks.

**Resolved on 2026-11-07, later** (see HANDOFF §9): the owner plays the term before
anything is added; the board phase's days (sleep once the day's work is done) stand; 67
(three weapons a city); 69 (next: skin tone, then painted faces; a rank's trim at
Commencement; the genius's colour on the cloak); 62 (the endings drafted after the owner has
played the arc); barks stay as floating text. Still to be played rather than decided: 66
(the weapon numbers), 70 (packs and elites).
70. **Packs, elites and the harness** (mine, 2026-11-07): the pack takes turns at the hero
    (one bite in flight), bites for 0.6, and goes for whoever is nearest; elites are guarded
    (a third of damage lands) until broken; `npm run balance:game` prints the tables that
    set these. The Green's packs are two; Harper's Cut's and the river's up to three.
71. **The creator's stage and what the look offers** (mine, 2026-11-10; `docs/art-bible.md`
    §12): (a) the creator is set on a wayside platform on the line at night, not in a named
    place of the story; should it be the character's own home (a stage per city) once the
    cities have kits? (b) build and stature are sliders between the named ends, where they
    were five and four steps; (c) a new life starts with hair, hair colour, build and
    stature drawn by its spark (`data/creation.json`, `look.start`), fair and red hair only
    on the fair skins to start with, anything by choice; (d) the face is still the home's
    (one per home and sex): the creator says so on the Body leaf rather than offering faces
    it does not have. Choosing among several faces per home is the next step if wanted.
72. **More genii, and each its own** (mine, 2026-11-10; `docs/genius-forms.md`): (a) the
    seventeen new forms' names and features (eleven First Forms: Hooded Crow, Cairn-tortoise,
    Fledgling Kith, Clockwork Wren, Hearth-stove, Watch-buckle, Kept Knife, Worn Glove,
    Wick-fiend, Whisperer, Rime; six Second Forms: Storm-crow, Weir-otter, Old Cairn-back,
    Lamplighter, Brass Kite, Wisp-train); (b) the new First Forms are offered only at the
    rite, as the Hawk is; (c) twenty-three bloods that had no lean in the Reading now have
    one, so the three offers differ by blood; (d) with more First Forms, the Field-wolf, the
    River-otter and the Shadow are offered at the rite only through a blood's lean, not by
    Seed and Shape alone (`npx tsx tools/genius-offers.ts` prints the offers); (e) what a
    genius is born with (build, the way its light burns, which three coats it may wear) and
    what the partner chooses (which coat, each marking on or off, a keepsake of four in five
    colours); (f) four new features: a shell, a skin of rime, an eye that opens in it, a
    pulse in the leather.
73. **The guarded elites, made fair** (mine, 2026-11-10, after the owner was caught at one):
    the four elites were tuned against a bot that parries every bite. Measured with hands
    that do not (`npm run balance:game -- --elites`: sure, steady, learning, new), a hero
    who misses parries was down in ten to twenty seconds with the beast barely marked. Now:
    (a) an elite's guard is down while it recovers from its own strike, not only while it
    is staggered (`data/combat-room.json`, `guard.open`), so guarding a blow and answering
    it works for every Shape, and the screen says GUARDED or OPEN; (b) the elites wait a
    little longer between strikes, the Warden and the Ruin-stag bite a little less hard, and
    the Post-breaker and the Barge-Heart have less health and no longer fell a fresh hero in
    three blows (`data/beasts.json`). A hand that never guards still loses to every elite;
    a learning hand fells the Warden and the Ruin-stag and still loses to the other two.
    Yours to set: how hard each should be, and whether breaking a beast (three breaking
    blows, a long stagger) should stay the opposite Shape's alone.
74. **How a genius's progress shows** (mine, 2026-11-10): the plan and its eight calls are
    in `docs/genius-progression.md` ("Calls that are the owner's"): growth between Readings,
    the molt as the ready signal, the coat carried across forms, grafts in the donor's
    colour, Resonance as light and instar as body, the Reading as six beats, what each
    instar adds, and whether a First Form at 0.6 m is too small.
75. **The genius as the signature** (owner's bar, 2026-11-10; mine to work down): the audit
    and the four calls are in `docs/genius-signature.md`: whether keeping its kind is always
    offered at a Reading; which kinds have an elder; the names of the great; and the order
    of what to build next (it fights as what it is; the Reading as a ceremony; classmates'
    genii in the yard; the lineage on its page; what shows between Readings; bodies).
