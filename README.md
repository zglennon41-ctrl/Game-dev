# WILDLINE

A real-time party RPG with guild management. Read `HANDOFF.md` for what the game is and
`CLAUDE.md` for how it is built.

## Run it

```
npm install
npm run dev        # opens the Step 0 page: the three lives, in the browser
npm run sim        # all three lives in the terminal
npm run sim -- --life data/lives/mira.json --log   # one life, with the day-by-day log
npm test           # rules tests + the three-lives acceptance test
npm run validate   # schema-check data/
```

## Where things are

- `data/` — the rules as JSON. Change a number here, rerun `npm run sim`, see what changed.
  - `rules.json` — Will, Terms, tiers, instars, Resonance, Marks
  - `reading.json` — how the Reading weighs play (the knob to tune what geniuses become)
  - `forms.json`, `features.json` — the lattice
  - `lives/` — Mira, Tobiah, Sable, scripted
- `src/rules/` — pure rules: field, terms, resonance, marks, reading
- `src/sim/` — the simulator and its report
- `docs/decisions-needed.md` — open questions for the owner
