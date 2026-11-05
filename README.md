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

Turn the sound on and choose **New character**: ten questions about who you were before
your field woke, then the reveal of who your answers made (your blood, Shape, weapon, what
will stand beside you, and your Pattern), then the night your field wakes. Afterwards,
**Practice yard** lets your character fight cut-wolves.

| Keyboard and mouse | Gamepad | Verb |
| --- | --- | --- |
| WASD / arrows | left stick | move |
| mouse | right stick | look around (when lock-on is off) |
| left click, J | X | strike, or shoot if you carry a gun |
| right click, K | RB | hold to block; tap just before a blow lands to parry |
| Space, Shift | A | dodge |
| Q, 1 | Y | your Shape's technique; it breaks the beast |
| F, L | LB | your Shape's stance |
| R | B | your Pattern (when its Trigger is met) |
| N | D-pad up | name the foe aloud (some Patterns need it) |
| Tab, middle click | R3 | lock-on on or off |
| Esc | Start | menu |
| E | X | talk, open a door, rest (at the Academy) |
| G | D-pad left | your genius's order: Guard or Hunt |
| J | Back | your genius's page |

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
