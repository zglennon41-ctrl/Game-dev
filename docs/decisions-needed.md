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
