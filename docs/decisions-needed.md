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
