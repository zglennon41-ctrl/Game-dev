# WILDLINE

A real-time party RPG with guild management. Read `HANDOFF.md` for what the game is and
`CLAUDE.md` for how it is built.

## Run it

```
npm install
npm run dev        # the pulse room: open the address it prints (http://localhost:5173)
npm run sim        # all three lives in the terminal
npm run sim -- --life data/lives/mira.json --log   # one life, with the day-by-day log
npm test           # rules tests + the three-lives acceptance test
npm run validate   # schema-check data/
```

## Playing the pulse room (Step 1)

Turn the sound on. Start with **Learn the pulse**: six short steps, about three minutes, and
the first one tunes the beat to your screen and speakers. Then **Fight the cut-wolf** for two
minutes.

| Key | Verb |
| --- | --- |
| WASD / arrows | move |
| J or Space | strike (Project) |
| I | Ground Strike, an Anchor technique: 18 Will, breaks the wolf |
| K or Shift | Hold: tap on the wolf's strike beat to parry, hold to block |
| L | Anchor stance (Shape) |
| Esc | menu |

A gamepad works too: A strike, X Ground Strike, B or RB Hold, Y stance. The feel numbers
are in `data/combat-room.json` and `data/beasts.json`.

The rules simulator from Step 0 is at `/sim.html`.

## Where things are

- `data/` — the rules as JSON. Change a number here, rerun `npm run sim`, see what changed.
  - `rules.json` — Will, Terms, tiers, instars, Resonance, Marks
  - `reading.json` — how the Reading weighs play (the knob to tune what geniuses become)
  - `forms.json`, `features.json` — the lattice
  - `lives/` — Mira, Tobiah, Sable, scripted
- `src/rules/` — pure rules: field, terms, resonance, marks, reading
- `src/sim/` — the simulator and its report
- `docs/decisions-needed.md` — open questions for the owner
