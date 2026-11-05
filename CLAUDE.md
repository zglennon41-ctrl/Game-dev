# WILDLINE — project instructions

You are building WILDLINE, a real-time party RPG with guild management, set on an Earth
ten thousand years after magic rose as the will of living things. The owner is a game
designer, not a programmer. Treat `HANDOFF.md` as the source of truth for what the game
is and `docs/` as the source of truth for how each system works. When they disagree,
`HANDOFF.md` wins, and you say so.

## What we are building first

A vertical slice, in this order, each step playable before the next starts:

1. Rules engine as data (Shapes, Stages, Terms, techniques) with a headless simulator.
2. The pulse combat room: one Shape, one beast, one Pattern, timed on a visible beat.
3. The Pattern builder: Form + up to three Terms, with the multiplier and breach rules.
4. One Green zone: three areas, a post, a boss, 20–40 minutes, extraction.
5. The genius as an AI follower: orders, Witness, a Reading at the Gate.
6. The hall: common room, board, six roster members, one named death.
7. Co-op for three.

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
- **The pulse is the game.** Combat work goes to input timing, beat windows, and
  feedback before anything else. Placeholder art is fine; placeholder feel is not.
- **Placeholders are shapes with tags.** No art pipeline yet. A genius form is a
  silhouette primitive plus feature tags rendered as labels. The lattice is data.
- **Small, playable, often.** Every PR leaves `npm run dev` playable. No branches that
  go dark for a week.
- **Explain in plain language.** The owner does not code. When you report, say what
  changed in the game, not in the code, and give the command to run it.
- **Ask before deciding game design.** Anything not settled in `HANDOFF.md` §9 is a
  question for the owner, not a default you pick silently. Build the obvious thing
  behind a flag and ask.

## Stack

TypeScript, Vite, PixiJS for the 2D prototype; Vitest for tests; JSON Schema for data.
Browser-first so the owner runs it with one command. Engine migration is a later
decision and is not yours to make.

## Commands

- `npm run dev` — the playable prototype
- `npm test` — rules and simulator tests
- `npm run sim -- --life data/lives/mira.json` — run a scripted life through a year
- `npm run validate` — schema-check every file in `data/`

## Layout

```
CLAUDE.md          this file
HANDOFF.md         what the game is; the spine; the slice; decisions
docs/              one file per system, buildable detail
data/              the rules, as JSON
src/rules/         pure functions: field, terms, reading, resonance, marks
src/sim/           headless simulator and scripted lives
src/game/          the PixiJS prototype
tests/
```

## Vocabulary

Use the game's words in code and comments: Shape (not class), Stage (not level),
technique (not skill), archetype (not job), Term (not condition), genius (not pet),
instar and Reading (not evolution), Mark (not XP), Will (not mana), line color (not
difficulty). The vocabulary is the design; keeping it keeps the design.
