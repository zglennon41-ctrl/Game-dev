# WILDLINE

A real-time party RPG with guild management. Read `HANDOFF.md` for what the game is and
`CLAUDE.md` for how it is built.

## Play it

1. Download **Godot 4.3** (the standard version, not .NET) from
   https://godotengine.org/download/archive/4.3-stable/ and unzip it. There is nothing
   to install; the unzipped file is the program.
2. Download this repository (on GitHub: **Code → Download ZIP**, branch
   `claude/new-session-izp0bs`) and unzip it.
3. Open Godot, click **Import**, and pick `project.godot` in the unzipped folder.
4. Press **F5** (or the ▶ button, top right). The first open takes a minute while Godot
   imports the project.

Turn the sound on. Start with **Learn the pulse**: six short steps, about three minutes.
The first step tunes the beat to your screen and speakers. Then **Fight the cut-wolf**
for two minutes.

| Keyboard and mouse | Gamepad | Verb |
| --- | --- | --- |
| WASD / arrows | left stick | move |
| mouse | right stick | look around (when lock-on is off) |
| J, Space, left click | A | strike (Project) |
| I, E | X | Ground Strike: an Anchor technique, 18 Will; it breaks the wolf |
| K, Shift, right click | B, RB | Hold: tap on the wolf's strike beat to parry, hold to block |
| L, F | Y | Anchor stance (Shape) |
| Tab, middle click | R3 | lock-on on or off |
| Esc | Start | menu |

The feel numbers are in `data/combat-room.json` and `data/beasts.json`. Change one, press
F5 again, and the room plays differently.

## The rules simulator (Step 0)

Needs Node.js 18 or newer.

```
npm install
npm run sim                                         # three scripted lives, three years each
npm run sim -- --life data/lives/mira.json --log    # one life, day by day
npm test                                            # rules and simulator tests
npm run validate                                    # schema-check data/
npm run test:game                                   # the game's own tests (needs godot on your PATH)
```

## Where things are

- `project.godot`, `game/`: the game (Godot 4.3)
- `data/`: the rules as JSON, read by both the game and the simulator
- `src/`: the rules simulator (TypeScript)
- `docs/`: the design docs, and `decisions-needed.md` (open questions for the owner)
