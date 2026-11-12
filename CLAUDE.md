# WILDLINE — project instructions

You are building WILDLINE, a real-time party RPG with guild management, set on an Earth
ten thousand years after magic rose as the will of living things. The owner is a game
designer, not a programmer. Treat `HANDOFF.md` as the source of truth for what the game
is and `docs/` as the source of truth for how each system works. When they disagree,
`HANDOFF.md` wins, and you say so.

## What we are building first

A vertical slice, in this order, each step playable before the next starts:

1. Rules engine as data (Shapes, Stages, Terms, techniques) with a headless simulator. (done)
2. The combat room: real-time action on one beast; the timing layer in the parry and the
   Pattern. (done; owner: "a lot of fun")
3. **Character creation and the opening** (owner's direction, 2026-11-05): a questionnaire
   whose answers make the character (blood or people, Shape, city, weapon, Seed, and a
   Pattern of its own); the world encounter where the field wakes and the Pattern fires;
   the Academy recruiter; one year later; the Academy's gate. All six Shapes playable.
4. **Act 1, the Academy: the current and only focus** (owner, 2026-11-05). A solo, offline
   game every character plays before the server: the walkable Academy, the cohort of twelve,
   the six lessons (Hold, the rite, Shape, Discipline, the line, Project), the Field
   Examination, Commencement. No one dies here (wards; a rescue team on expeditions). Every
   run should make a character unlike the last, and the run ends with a settled field:
   a character ready for the server (owner, 2026-11-06). **It is the MMO, offline, at every
   level** (owner, 2026-11-07): a season's crisis arc, the full quest board in zones around
   Alexandria, deeper lessons, classmates with AI of their own, AAA-standard art and
   interface. The first version (thirty minutes long) was the scaffold; the plan for the
   rebuild is `docs/academy-plan.md`.
5. The hall: common room, board, roster members, one named death.
6. Co-op for three.

Do not start a later step until the owner has played the earlier one and said it is fun.
If step 2 is not fun with one Shape and one zone, nothing added later fixes it.

## How to work

- **Rules are data, not code.** Shapes, families, techniques, Terms, archetypes, forms,
  features, adaptations, quests, and crises live in `data/*.json` and are validated by
  schema. Code reads data. A designer must be able to change a Toll's multiplier without
  touching code.
- **Everything deterministic is testable.** The Reading, the Ledger tally, Resonance,
  breach detection, Mark counting, and canonization are pure functions with tests. The
  headless simulator runs a character through a year of play in seconds and prints what
  the genius became; `docs/three-lives.md` is the acceptance test for it.
- **The creator is a key feature.** The first hook of the game is the questionnaire and the
  night the field wakes. Its words live in `data/creation.json` and `data/story.json`.
- **Real-time feel is the game.** WILDLINE is a real-time MMORPG first; it should feel
  like a AAA action MMO. Combat work goes to responsiveness, animation, hit feedback,
  readable enemy telegraphs, and the camera before anything else. The beat is secondary:
  it lives only in the parry (timed against an enemy's wind-up) and in the Pattern's
  chain (owner's decision, 2026-11-05). Placeholder art is fine; placeholder feel is not.
- **One style.** Everything the game draws and moves is held to `docs/style.md`; its numbers
  are `data/style.json`. An asset off it is a bug: `npm run check:style` finds it. A new
  material is named for what it is made of; a new colour comes from a ramp.
- **Placeholder art is CC0.** Until the game has its own art direction, characters,
  creatures and environments come from CC0 libraries (KayKit, Quaternius), credited in
  `game/assets/CREDITS.md`. A genius form may still be a silhouette plus feature tags.
- **Small, playable, often.** Every PR leaves the Godot project playable. No branches that
  go dark for a week.
- **Explain in plain language.** The owner does not code. When you report, say what
  changed in the game, not in the code, and give the command to run it.
- **Ask before deciding game design.** Anything not settled in `HANDOFF.md` §9 is a
  question for the owner, not a default you pick silently. Build the obvious thing
  behind a flag and ask.

## Stack

**The game: Godot 4.3, GDScript, 3D, third-person** (the owner chose Godot over Unity and
Unreal on 2026-11-05, replacing the 2D browser prototype). The project file is
`project.godot` at the repo root; the game lives in `game/`. It uses the Compatibility
renderer so it also exports to the web. Godot reads the same `data/*.json` as the tools.

**The tools: TypeScript and Vitest** for the headless rules and the simulator (`src/`),
and JSON Schema for data. The rules a designer tunes live in `data/` and are shared by both.

## Commands

- Open `project.godot` in Godot 4.3 and press Play (F5) — the playable game
- `godot --path .` — the same, from a terminal
- `npm run test:game` — the game's headless tests (Godot)
- `npm test` — rules and simulator tests (TypeScript)
- `npm run sim -- --life data/lives/mira.json` — run a scripted life through a year
- `npm run validate` — schema-check every file in `data/`
- `npm run balance:game` — play every weapon type, technique and temperament headlessly and print the tables
- `npm run check:style` — fail on anything off the game's one style (`docs/style.md`, `data/style.json`)
- `npm run check:fit` — measure how every piece of dress sits on every body, standing and moving; fail on what does not fit (`docs/dress-fit.md`; needs Blender's Python module)

## Layout

```
CLAUDE.md          this file
HANDOFF.md         what the game is; the spine; the slice; decisions
docs/              one file per system, buildable detail
data/              the rules, as JSON
project.godot      the Godot project
game/              the game: scenes, scripts, its own tests
src/rules/         pure functions: field, terms, reading, resonance, marks (tools)
src/sim/           headless simulator and scripted lives (tools)
tests/             tests for the tools
```

## Vocabulary

Use the game's words in code and comments: Shape (not class), Stage (not level),
technique (not skill), archetype (not job), Term (not condition), genius (not pet),
instar and Reading (not evolution), Mark (not XP), Will (not mana), line color (not
difficulty). A genius is on a line, and the stages of a line are Baby, Starter, Path,
Advancement and Final (the owner compared a line to an evolution, 2026-11-10; the game's
word for the step is an advancement, and for the moment a Reading). The vocabulary is the
design; keeping it keeps the design.
