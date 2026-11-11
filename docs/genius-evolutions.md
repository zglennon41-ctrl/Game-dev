# A line is an evolution

> "I want these to be distinct like Pokémon evolutions or digivolutions. Right now it just
> looks very clunky. Baby, three starters, three paths from each starter and hybrid lines,
> three advancements from there, final advancement." (owner, 2026-11-10, on seeing the whole
> tree drawn as the game drew it: thirty-one forms of a base, one body, a part apiece)

The tree (`docs/genius-tree.md`) says what a form *is*: whose soul, what it is the picture
of, its sign, its habit, the play that earns it. This page says what it *looks like*, and
holds every form to one rule: **each form on a line is a different creature to look at, and
a stranger shown the line out of order could put it back in order.**

## The stages

The player's words for where a genius is on its line (`data/genius.json`, `stages`), and
what they are in the tree:

| Stage | When | In the tree | Its age |
|---|---|---|---|
| **Baby** | From the night the field wakes until the rite | (none: everyone's is the same small thing of light) | not yet born into a form |
| **Starter** | The rite: three are offered, by the bowl and the partner's home | a base's settled form (22) | young |
| **Path** | The first refinement, at the Gate: three, and a turning into a **hybrid line** where the play has turned | a path (3 a starter) | half-grown |
| **Advancement** | The second refinement: three | a prong (3 a path) | grown |
| **Final** | The third refinement | a finish (2 an advancement) | in its prime |
| | Then it grows **great**, and to its **apex**: the Final's own body, larger, with the presence of its age | | great, apex |

This is the reading taken of the owner's sentence: the Baby is the stage before the rite
and the three starters are the rite's three offers, so the tree keeps its shape. The other
reading (each base's own baby, then three starters of that base, one more tier) and the
count of Finals (the sentence says "final advancement"; the tree has two to choose from)
are calls for the owner, below.

## What must change, and what must carry

Four things change at **every** step down a line. A form that changes fewer than three of
them from its parent is not finished.

1. **Its build.** Proportions, not size alone: the legs, the chest, the neck, how it
   carries its head. The stage gives the age (the Starter has the head and paws of the
   young; the Final is deep in the chest); the form gives the rest.
2. **Its great parts.** What it has grown or been given, large enough to change its outline
   at fifteen metres: a mane, a crown of fur, plates, a lamp on a post, flags from the
   shoulders. Never a tag. A form's `sign` is its brief: the sign is made physical.
3. **Its coat.** It wears its partner's own coat (that never stops being theirs), shifted:
   gone to night, to frost, to slate, to ember; and marked as the form is marked (dark round
   the eyes, grey at the muzzle, grease to the hock).
4. **Its light.** Where the field shows on it: the eyes, then a seam, then windows in its
   flank or a coal in its throat. More with each stage, and never the whole body.

And one thing carries: **a form wears everything its parent wears unless it says
otherwise.** The Night-watch's dark eyes are still there on the Storm-coat and the
Frost-ruff; the Grey Shield's slate is on the Wall-wolf, grown. That is what makes it a
line and not thirty-one animals.

How much, by stage:

| Stage | Stands | Great parts | Light |
|---|---|---|---|
| Starter | 0.6 m | one small thing of its kind (a pup's ruff) | its eyes |
| Path | 0.8 m | one or two that say which way it has gone | its eyes |
| Advancement | 1.0 m | two or three; one new and large | eyes and one more place |
| Final | 1.3 m (1.7 great, 2.3 at its apex) | everything, at full size; an outline no other form in the game has | several, and the mantle and lines of its age on top |

## A body, as data

Each node of a base file (`data/genius-bases/<base>.json`) may carry a `body`. It is read
against its parent's: a key it names replaces the parent's, `null` takes a thing off,
`build` is merged key by key. The schema allows any slot; what a slot means belongs to the
family that builds it.

On the wolf's rig (`tools/blender/genius_lines.py`):

| Key | What it is | Styles |
|---|---|---|
| `build` | proportions against the stage's own, each a multiple of 1 | `legs` `girth` `chest` `waist` `neck` `nape` `head` `muzzle` `jaw` `ears` `tail` `brush` `body` `paws`; `pitch` (radians: more lowers the head); `stance` (how wide it stands) |
| `ears` | | `tunnel` `tall` `back` `split` `torn` `hound` |
| `eyes` | | `dark` `lamp` `old` `third` `far` `second` |
| `maw` | | `fangs` `open` `glow` |
| `ruff` | round the neck | `pup` `quills` `mane` `crown` `slate` `frost` `ember` |
| `spine` | along the back | `seam` `ridge` `quills` `iron` `plates` `smoke` `frost` `ember` `stars` |
| `tail` | | `whip` `short` (its shape); `flag` `smoke` `lamp` `rings` `ember` |
| `flags` | from the shoulders | `fur` `pale` `light` |
| `armor` | | `brow` `chest` `chain` `harness` `scars` |
| `carry` | what it has been given | `lamp` `book` `tags` `knots` `post` `cloak` `rug` `bell` |
| `paws` | | `set` `grease` `shade` `frost` |
| `aura` | | `windows` `motes` `cold` `crescent` |
| `coat` | how its partner's coat is worn | a shift in `data/genius-looks.json`, `shifts`: `night` `ash` `frost` `ember` `slate` `iron` `hearth` `blood` `moon` |

A slot holds a style, `[style, size]`, or a list of them.

## How it is built

`python tools/blender/genius_lines.py <base> [<form>...]` (Blender's Python module) reads
the base file and writes one model a form, `game/assets/genius/forms/<form id>.glb`. A
family of lines is one file, `tools/blender/lines_<family>.py`, with `register(builders)`.

What every model keeps to, whatever builds it:

- The genius kit's conventions (`tools/blender/genius_kit.py`): Z up, facing −Y; sockets
  named `socket_<name>`; materials named `field_*` glow in the partner's Shape colour and
  nothing else glows; the look's roles (`fur_dark`, `fur_light`, `fur_ruff` on the wolf's
  rig; a body's own in `data/genius-looks.json`, `bodies`) are the partner's coat and are
  never painted over wholesale.
- `ref_top`: an empty at the crown of its head (or the top of the thing itself, for an
  object). The game stands the body *that* tall; what it has grown above it stands above
  its stage's height.
- What is soft is shaded round (fur, cloth, smoke, light); what is hard keeps its planes
  (plate, ice, horn, brass). The body is one welded skin.
- No clips. A rigged form moves by its base body's, which the game fits to its
  proportions. No textures. A rigged form under 200 KB, an object under 80 KB.
- Colours from the kit's palette: muted earths, stone and metal, a value apart.

## How the game wears it

`game/scripts/genius/genius_body.gd`: a form whose model exists wears it in place of its
base's body (a hybrid's form wears the body of the form it came from). The features its
line gave it are in the model, so no parts hang for them; a feature from anywhere else
(heritage, an adaptation, a graft, a hybrid's gift) still hangs on its sockets. It is not
reshaped by age until it is great. Its partner's coat goes on through the form's `coat`
shift. A form with no model wears its base's body and parts as before, so the game is
whole while the lines are built.

**Hybrids** are not modelled one by one (there are 462 of them). A hybrid's form wears the
body of the form it came from, in a coat of its second base's, with the second's gift
hung on it as parts. So each base's gift (`hybrid.gift`) must be a part bold enough to say
whose it is.

## Looking at a line

```
python tools/blender/genius_lines.py wolf          # build the Wolf's thirty-one
godot --headless --path . --import                  # let the game take them in
godot --path . --resolution 3200x1800 -- --sheet=wolf --shots=DIR     # every form, a cell each
python3 tools/genius-sheet.py DIR out.png --line 2  # one path's line, large and named
bash tools/genius-tree-page.sh wolf                 # the page of the whole tree, with these in it
```

## Where it stands

| Line | Bodies |
|---|---|
| Wolf | all thirty-one (the proof) |
| the other twenty-one | their base's body and parts, until built |
| Baby | the orb it was; to be given a body |

## Calls that are the owner's

1. **The shape of a line.** Taken: Baby (everyone's) → Starter (three offered at the rite)
   → three Paths and the hybrid lines → three Advancements → Finals. The other reading: a
   Baby of each base, then three Starters *of that base*, which is one more tier on every
   tree (and every form of it to design).
2. **One Final or two.** The tree has two Finals under each Advancement, earned by
   different play. "Final advancement" may mean one. Nothing was cut.
3. **The names of the stages**: Baby, Starter, Path, Advancement, Final are the owner's
   words; the tree's files still say settled, path, prong, finish.
4. **How strange a Final may be.** The Wolf's Finals stay wolves (a Wall-wolf is a wolf
   built like a wall). They could go further from the animal: say how far.
5. **The Baby**: one for everyone, or one that already leans toward what it will be.

## The items of power: the Lantern, the Astrolabe, the Bell

`tools/blender/lines_items.py`. An item is an instrument, and every form of it is a
different instrument: a hand-lamp, a miner's lamp, a lamp on a post, a stove; a pocket disc,
a frame with a scale along its rim, a cage of hoops, a fan of plates; a hand-bell, a bell
in a frame, a clock with a bell on it, a horn. Each of a base's three Paths has a look of
its own that the forms below it keep: the Lantern's are the round dark-lantern with one
great lens (Wayfinder), the low lamp under a brim that sits up late (Watch-lamp) and the
cup with a canopy over its flame (Kept Flame); the Astrolabe's are the disc with an arm
and a glass (Sighting-glass), rings inside rings (Orrery) and plates fanned like pages
(Almanac); the Bell's are the bell on a stock and a rope (Rally-bell), the bell on a clock
(Hour-bell) and the bell turned mouth-forward, with teeth (Alarm-bell).

**It is alive.** Every form has an eye of the field set in its metal, lidded in its own
stuff (a heavy lid for one that is old or sits up late; two, either side of the mouth, on a
bell turned mouth-forward). The Lantern walks on legs it has grown.

**Its coat.** The metals are its partner's coat (the roles of the silhouette the form is
drawn as, in `data/genius-looks.json`). A lantern's and an astrolabe's main metal is the
coat's first; a bell is cast in the coat's *third* (the brass of an iron-and-brass coat,
the copper of a blued one) and hung in ironwork of its first. Glass, enamel, wax, rope,
wood and cloth keep colours of their own. A turned thing is shaded round with crisp rims;
a cut or forged thing keeps its planes.

**It can be carried.** Every model has an empty named `carry` where a hand or a hook takes
it: the lantern's ring, the ring on the astrolabe's throne, the bell's handle or the ring
on its stock. `carry` is never turned and the instrument always hangs *below* it, upright,
facing the way the body faces; so the game hangs any form of any of the three from a hand,
a belt or a bracket by putting `carry` there, without knowing which form it is. How tall
it is in the hand is the form's `held` (metres, in its `body`: a pocket astrolabe 0.14, a
Tenor 0.55); as a body in the world it stands at its stage's height by `ref_top` like any
other.

**The Lantern's body** (a lamp, and how it holds itself up):

| Key | What it is | Styles |
|---|---|---|
| `vessel` | the lamp's own frame | `box` `hex` `oct` `drum` (closed behind) `safety` (glass in a guard, gauze above) `globe` `font` (an oil lamp) `dome` `cup` `glasshouse` `belly` (a stove) `column` `pyramid` |
| `roof` | | `cap` `vent` `hood` `gauze` `brim` `pagoda` `dome` `crown` `battlement` `ball` `chimney` `canopy` `spike` `rays` `none` |
| `glass` | what stands between you and the flame | `bars` `cage` `lens` `shutter` `portholes` `pierced` `gem` `hood` `signals` (a green glass and a red) |
| `flame` | | `candle` `heart` `low` `tall` `clear` `star` `cold` `root` `points` `coal` `flat` |
| `stand` | how it holds itself up | `legs` `stride` `four` `stilts` `crab` `fold` `bow`; `arm` `neck` `post` `mast` `stem` `float`; `keeper` (it grew one to carry it); `none` (it left its glass behind) |
| `feet` | | `claw` `flat` `web` `ball` |
| `keeper` | how the keeper holds it | `plain` `veiled` (high, and a little behind) `both` |
| `face` | where it is alive | `eye` `lids` `lens` (its lens is its eye) `gauge` `none` |
| `carry` | what it has been given | `ring` `hoops` `halo` `lens-arm` `scale` `reflector` `rods` `cloak` `rag` `mirror` `scroll` `seals` `pilot` `book` `shade` `wide-shade` `kettle` `door` `gallery` `semaphore` `chain` `paddles` `reeds` `pendulum` `clock` `taper` `yoke` |
| `build` | | `w` `h` (the lamp's width and height) `head` (the whole lamp) `legs` `girth` `float` `tower` `curious` (how far its flame leans to what it is looking at) |

**The Astrolabe's body** (a plate about a pin, and what it measures with):

| Key | What it is | Styles |
|---|---|---|
| `plate` | the instrument's own body | `disc` `sector` `rings` `sphere` `globe` `shield` `wave` `eclipse` `book` `strip` `board` `table` `case` `ball` `rose` `worn` `dome` `chart` |
| `rete` | what lies over a disc | `ticks` `fret` `hours` |
| `arms` | | `rule` `lens` `tube` `long-tube` `pointer` `bead` `needle` `hands` `tide-hands` `dividers` `pantograph` `broken-hand` |
| `rings` | what turns round it | `orbit` `cage` `ellipse` `horizon` |
| `wings` | | `leaves` and `glider` (they beat) `vanes` `fins` |
| `face` | | `eye` `lids` `dark` `none` |
| `carry` | | `fob` `gears` `dial2` `plumb` `lines` `vane` `cups` `telltales` `eyes3` `trumpet` `headlamp` `escapement` `foot` `striker` `moon` `stamp` `star` `crown` `cord` |

**The Bell's body** (a bell, how it is hung, what it is rung with):

| Key | What it is | Styles |
|---|---|---|
| `bell` | its casting | `hand` `ship` `pot` `tower` `great` `gong` `flare` `barrel` `long` `tall`; `horn` (it is a horn now) |
| `pose` | how it is turned | `hang` `swing` (an angle); `forward` (its mouth to the front: 1 is level) |
| `hang` | what holds it | `handle` `yoke` `frame` `cradle` `hook` `crane` `wheel` `beam` (eight small bells along it) `headstock` `clock` `belfry` `post` `float` `tower` `none` |
| `tongue` | | `trembling` `ball` `fist` `long` `row` `none` |
| `face` | | `eye` `lids` `none` |
| `carry` | | on the bell: `teeth` `band` `bumps` `dent` `marks` `brow` `horns` `studs` `inscription` `plaques` `verdigris` `drops` `icicles` `ribbons` `doors` `sight` `fin` `chains` `selector`; with it: `rope` `foot` `lamp` `pennons` `scroll` `abacus` `ladle` `sound` `cushion` `mallet` `tags` `taper` `soot` `hourglass` `cowl` `post-lamp` `fork` `damper` `dish` `line` `hammers` `topmark` `chain` `ghosts` `hammer` `anvil` `smiths` `cloud` `bolts` |
| `build` | | `tilt` (it rides a swell that is not there) |

**Their gifts** (what a hybrid of one of them wears, `python tools/blender/lines_items.py
gifts`): the Lantern's is a caged lamp a hand tall, hung at the light's socket; the Bell's a
bell at the throat (the `bell` feature hangs at `socket_throat`, `data/genius-bodies.json`)
with rings of sound going out before it (`voice`); the Astrolabe's a band of brass across
the brow with a great lens (`far-eyes`) and its works worn at the breast (`gears`).

`godot --headless --path . -s res://game/tests/check_items.gd` holds all ninety-three to
this: a model of its own, `ref_top`, `carry`, the usual sockets, a light of the field, its
feet on the ground, a `held` size; it ends "items: 93 forms, all good".
