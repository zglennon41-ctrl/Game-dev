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
will stand beside you, and your Pattern), then the night your field wakes, and the
Instructor who takes you in.

Then **the Academy at Alexandria**, a term of play that ends with a settled character:

- **Lesson 1, Hold** in the warded yard: the guard and the parry.
- **The rite** in the Hearth Hall: the bowl reads your Shape (it can surprise you) and your
  genius takes its First Form, one of three the bowl offers.
- **Lesson 3, Shape**: your stance, your technique, and a sparring ladder against your
  cohort of twelve classmates, made new for every character.
- **Lesson 4, Discipline**: your city's school, a weapon of your choosing, three techniques
  on keys 1, 2, 3, and a bout against your Instructor.
- **Lesson 5, the line**: a party of two classmates, the car to the Green, the post, the
  Warden's den, extraction. No one dies: the rescue team carries the fallen out.
- **Lesson 6, Project**: the field opened past the skin, and the Field Examination with it
  open: Stage 3.
- **The Gate**: your genius's Second Form read from how you played, the cohort's write-up of
  you, Commencement.

Between lessons, talk to anyone (E), rest in the dormitory, and press J for your genius's
page. **Practice yard** lets your character fight cut-wolves at any time; the art for every
genius is built by `tools/blender/genius_kit.py` (see `docs/art-bible.md`).

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
| Tab, middle click | R3 | lock-on on or off; locked on with a pack about, passes the lock to the next of them |
| Esc | Start | menu |
| E | X | talk, open a door, rest (at the Academy) |
| G | D-pad left | your genius's order: Guard or Hunt |
| J | Back | your genius's page |
| 1, 2, 3 | | your Discipline's techniques (from Lesson 4) |
| F (held, Will high) | LB | Project: opens the field past the skin (from Lesson 6) |

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
