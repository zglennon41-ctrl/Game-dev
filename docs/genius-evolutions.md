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

## The weapons: the Blade, the Gun and the Bow

`tools/blender/lines_weapons.py` builds these three lines (ninety-three bodies). A weapon
genius is its own weapon, so every form is two things in one model.

**In the hand.** The model is made in the weapon kit's frame and at its scale
(`tools/blender/weapon_kit.py`, `docs/weapons.md`): a blade runs along +Z from the hand, its
true edge to +X; a gun's barrel runs along −Y, its top to +Z; a bow's limbs run along ±Z,
its back to −Y and its string at +Y; the origin is the hand slot. That frame is kept in the
model as an empty named `grip`; `grip_off` is where the second hand goes (the lower grip of
a hilt long enough for two, a long gun's fore-end, the nock of a bowstring). To put a form
in a hand, give the model the inverse of `grip`'s transform under the hand slot, at scale 1,
and from there treat it as the kit's own model of that type (guns and bows take the same
quarter turn the kit's do, `World.RANGED_MODELS`).

**Floating.** It stands the way its base did: a blade hangs point-down (the wooden swords
point-up, the Lunge at a slant, the Bar crosswise, the Wall of One planted in the ground), a
gun rides level at the hip with its muzzle to the front, a bow stands upright with its arrow
of light to the front; the standing guns stand on their own legs. `ref_top` is set so an
Advancement or a Final floats at exactly the size it is in the hand at the Form it is earned
at, a Path a tenth larger, the Starter a third larger; `show` makes one form larger still (a
small knife, a belly-gun).

The partner's coat is on the weapon by role (`data/genius-looks.json`, `bodies`): the wrap
and the brass of a blade, the ironwork and the brass of a gun (its stock stays walnut), the
limbs of a bow.

| Line | Key | What it is | Styles |
|---|---|---|---|
| Blade | `blade` | the steel: `kind` `shape` `len` `width` `thick` `curve` `tip` `taper` `flare` `fuller` `steel` | kinds `sword` `saber` `board`; shapes `knife` `cleaver` `belly` `hook` `bar` `clip`; steels `steel` `bright` `grey` `night` `oak` `pale` `green` `dark` `hot` |
| | `hilt` | `len` `wrap` `metal` `grooved` `thick` | wraps `leather` `dark` `wire` `cord` `cloth` `bone` `wood` `worn` `red` `green` `pale` `crepe` |
| | `guard` | | `none` `bar` `droop` `wide` `sail` `cup` `shell` `disc` `knuckle` `ring` `hook` `wood` `block` `crescent` |
| | `pommel` | | `scent` `cap` `ball` `ring` `disc` `spike` `knot` `eye` `none` |
| | `edge` | what its edge has become | `notched` `old-notch` `light` `temper` `blunt` |
| | `cut` | what is cut or laid into the flat | `tally` `names` `line` `core` `plates` `bands` `pulse` |
| | `spine` | along its back | `rings` `oak` `glow` `hook` `saw` |
| | `eye`, `eyelook`, `lens` | where its eye is, and how it looks | `blade` `guard` `pommel` `knot`; `open` `old` `closed` `dark` |
| | `hang`, `cloth` | what hangs from it | `tassel` `whetstone` `sheath` `wrap` `smoke` `endring` `chain` |
| | `pose`, `sheathed` | how it floats | `down` `up` `slant` `cross` `planted` |
| Gun | `gun` | the piece: `frame` `barrel` `bore` `barrels` `muzzle` `butt` `lock` `wheel` `chambers` `closed` `hammer` `wood` | frames `pocket` `revolver` `rifle` `carbine` `pole` `wall`; locks `flint` `hammer` `cogs` `thumb` `none` |
| | `sight`, `eyelook` | its lens, which is its eye | `lens` `long` `wide` `dark` `two` |
| | `grows` | what it has grown or been given | `bipod` `stride` `level` `wheels` `tripod` `gimbal` `drum` `mud` `round` `rags` `works` `vanes` `screen` `frost` `rings` `wire` `patches` `smoke` `hot` `odd` `hands` `lamp` `veil` `writ` `shield` `mantlet` `walls` `horn` `flag` `badge` `wisps` |
| | `height` | how tall it stands on its legs (0: it floats) | |
| Bow | `bow` | the stave: `len` `bend` `recurve` `limb` `width` `thick` `wood` `belly` `grip` `lower` `shoulders` `rough` `wrap` `tips` | limbs `stave` `leaf` `paddle` `scroll`; tips `mark_tips` `horn` `bone` `brass` `horn-long` `scroll` |
| | `string`, `draw` | | `plain` `wrapped` `dark` `ring` `tremble` `twitch` `hair` `glow` `wires` `none` |
| | `arrow` | the arrow of light on the string | `light` `fire` `up` `many` `threads` `none` |
| | `eye`, `eyelook` | the eye in its grip | `grip`; `open` `old` `closed` `dark` |
| | `rides` | what rides on it | `bark` `arrows` `ear` `sinew` `vanes` `wings` `sight` `fletch` `brazier` `feet` `lamp` `quiver` `insulators` `spool` `gourd` `roots` `candle` `tip-eyes` `token` `knot` `crepe` `needle` `bands` `cloth` |
| all | `show`, `coat` | larger or smaller than its stage; how the partner's coat is worn | a shift, as above |

What each path keeps, so its line can be put back in order:

| Line | Path | It is | It grows |
|---|---|---|---|
| Blade | Duelling Blade | slim straight steel, a cup at the hand | a wider guard, a lens, a line of light; or a needle; or, from the Wooden Sword, wood to bare steel, point up |
| | Cleaver | a broad single edge, heavy at the point, iron | rings on its back, notches in its edge, a hook, a plated slab, a bar |
| | Scored Blade | a curved edge, a brass bow over the knuckles, tally marks | names, a shell guard, a glowing back; or it goes grey, old, black |
| Gun | Long Gun | a walnut rifle and a far eye | a bipod and mud, one great round, rags; a wide lens and works; a dark lens |
| | Repeater | a wheel of chambers in a brass frame | a fanning hammer, rings of light; legs, a gimbal, wheels; a hand-cannon on a pole |
| | Standing Gun | a wall-gun on three legs | a lamp, a writ, a shield, a mantlet taller than you, walls, a horn, a badge, a drum |
| Bow | Hunting Bow | a flat bow, leaf-limbed, bark still on it | a wrapped string, a full draw; arrows on its back, an ear; vanes, wings |
| | War Bow | broad in the shoulder, banded in iron, a red grip | a fan of fletchings, many arrows, fire; feet, a lamp, wires; a great eye |
| | Singing Bow | slender, twice-curved, scrolled at the tips, a gourd to speak through | a ring of light, roots; an old eye, more eyes; a hair for a string, then none |

**Their gifts**, as parts (`python tools/blender/lines_weapons.py parts`): `short-blade` (a
real one, carried across the mouth or in the hand), `edge` (a blade swept back from each
shoulder), `gears` (three cogs at the breast and a key to wind them), `sight-glass` (a brass
glass borne over the brow), `far-eyes` (two great lenses on a band), `fletching` (flights of
the field along the back; it hangs at `socket_back`, `featureSockets`). A body does not wear
its own base's gift: a Gun carried into a hybrid's line is already the picture of a gun.

Small round things (studs, knees, bags, the gourd) are shaded round: twelve points where a
faceted ball spends sixty. It is what keeps every body under 80 KB.
