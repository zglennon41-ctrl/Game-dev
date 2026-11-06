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
- **The Gate**: your genius's Second Form read from how you played, the Reckoning of the
  season's crisis, the cohort's write-up of you, Commencement.

And between the lessons, the term itself (`docs/academy-board.md`, `docs/zones.md`):

- **The board** in the quad: your classmates' troubles, and from Lesson 5 three to five
  postings a day (Linework, Salvage, Hunt, Escort, Writ, the Deep Run, the Friday Rally)
  into four zones around Alexandria: the Green hills, the Shenandoah ruin, Harper's Cut
  junction and the Cahokia river line, each with its own beasts, its pack and its named
  beast that remembers. Marks for every one done.
- **The crisis of the Dark Mile**: rumours, then Ledgers that every posting weighs, then
  the Reckoning at the Gate that writes the world your server will know.
- **Your cohort**: twelve classmates with their own days (the yard, the quad, the hearth;
  out on runs of their own; the infirmary when carried out) who fight on their own beside
  you: their own targets, techniques, Patterns, parries, and a retreat when hurt.
- **Mastery**: nine techniques a school (one more from your school's instructor in the yard
  for every three Marks; three set for your hand), grades by use, and the Hearthkeeper at
  the hearth who sits you down with your Pattern.

Between it all, talk to anyone (E), rest in the dormitory (the day turns and the board
changes), press J for your genius's page, H for the step's words again, and Esc for the
term so far. **Practice yard** lets your character fight cut-wolves at any time; the art for every
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
| Esc | Start | the term so far (the Academy), or the menu |
| H | | the step's words again |
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
