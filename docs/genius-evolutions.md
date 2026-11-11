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
| `carry` | what it has been given | `lamp` `book` `tags` `knots` `post` `cloak` `shroud` `rug` `bell` |
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
| Baby | built: a small round thing of pale matter with a face, the field in its eyes, its belly and the tip of its tail (`python tools/blender/genius_lines.py baby`); it rides where the orb did until the rite |

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

## The armors: the Shield, the Gauntlet, the Coat

`tools/blender/lines_armors.py` builds the Shield and loads the Gauntlet
(`armors_hand.py`) and the Coat (`armors_coat.py`). These are the defensive items: a
genius that is worn. Each is an object, not a rigged body. It floats at its partner's
shoulder like any relic, and it can be put on.

**Size.** Every model is made at the size one of the game's people would wear it (a
person is about 2.4 units tall, a hand 0.26 long, shoulders 0.62 across), its foot at
z = 0. `ref_top` is set so that, floating, it is as large as its stage says; `stands` in
a form's `body` is how large it floats against that (a tower shield 1.6 of its stage's
height, a buckler 0.8), since a thing that is all height reads smaller than a beast.

**`wear`.** Every model carries an empty named `wear` where it meets its partner. To wear
a piece, give the model a scale of one and bring `wear` onto the place (the model's
transform is the place's, times the inverse of `wear`'s own in the model). Nothing needs
to know which form it is: a piece that floats leaning or turned comes square when worn,
because `wear` leans and turns with it.

| Line | Where `wear` is | How it is turned |
|---|---|---|
| Shield | the middle of the grip, behind the boss | the model's own axes: on a hand slot it sits as the weapon kit's shields do (the grip along the fist, the face out of the back of the hand, the top up) |
| Gauntlet | the middle of the wrist's opening; it is a left hand | as a hand slot is: in the game's axes +Y runs out of the thumb side, +Z out of the back of the hand, −X to the fingertips |
| Coat | the nape: between the shoulders, at the base of the collar | the wearer's own: up, the wearer's left, the wearer's front. The Starter's clasp hangs a hand's breadth in front of its `wear`, at the throat |

**Where each is alive.** A shield: the eye in its boss (or what took the boss's place: a
mouth, a grille, a pair of eyes). A gauntlet: the pulse of light round its wrist. A coat:
the eye in the clasp at its throat, which is the clasp it grew from.

The Shield:

| Key | What it is | Styles |
|---|---|---|
| `shape` | `[outline, width, height]` | `round` `oval` `drum` `tower` `door` `rect` `wide` `board` `carriage` `coffin` `heater` `kite` |
| `curve` `dome` `vee` `thick` | bent round its partner; domed; folded down its middle; how thick | numbers |
| `face` | what its face is made of | `iron` `leather` `wood` `polish` `glass` `stone` `timber` `black` `hide` `steel` `copper` |
| `rim` | a style, or `[style, radius]` | `iron` `brass` `stone` `timber` `black` `leather` `polish` `none` |
| `boss` | `[style, size]` | `eye` `dome` `spike` `ram` `flat` `hound` `ring` `none` |
| `blazon` | the mark its partner may show, and the studs | `chevron` `bar` `arc` `ring` `none` |
| `grown` | what it has grown or been given | `dents` `hammered` `patches` `notch` `teeth` `jaws` `strap` `worn` `spine` `bars` `brow` `footbar` `frame` `glints` `ripples` `tines` `vision` `hood` `hinges` `bar` `peep` `foot` `slit` `number` `merlons` `turrets` `wicket` `portcullis` `lintel` `sign` `pane` `feet` `crest` `plumes` `ribbons` `panel` `moss` `chains` `soot` `embers` `lattice` `eyes2` `ribs` `poles` `poles4` `shingles` `flange` `eye_top` `window` `cutwater` `waterline` `mooring` `ears` `torn_ear` `ruff` `scars3` `tokens` `old` `lacing` `beaters` `boards` `mouth` `seam`; and three that are the plate itself: `posts` `tiles` `halves` |
| `grip` | how far up the grip is, as a part of its height | number |
| `lean` `yaw` | how it is held, in degrees | numbers |

The Gauntlet:

| Key | What it is | Styles |
|---|---|---|
| `bulk` | how broad the hand is (1 is a hand) | number |
| `stuff` | what it is made of | `leather` `iron` `stone` `bare` `dark` `cloth` |
| `fingers` | how the fingers lie | `rest` `open` `flat` `spread` `fist` `pinch` `point` `beckon` `sign` `grip` `claw` `cup` `knock` `shake` |
| `hold` | how the whole hand is held; or `[hold, x, y, z]`, leaned in degrees | `up` `palm_front` `palm_up` `palm_down` `side` `down` `reach` |
| `cuff` | `[style, length]` | `glove` `flare` `sleeve` `plate` `arm` `wrap` `stone` |
| `plates` | | `back` `knuckles` `bar` `palm` `pad` |
| `finger_plates` | lames over the finger joints | `iron` `brass` `dark` |
| `long_first` `fingers_long` | the first finger's length; all of them | numbers |
| `grown` | what it has grown, or holds | `loupe` `tools` `gears` `wrench` `pulse_palm` `wire` `wheels` `lever` `worn_tips` `rope` `phial` `lamp` `keys` `ring_wrist` `seams` `sixth` `ember_heel` `face_plate` `split` `scars` `shard` `chain` `roots` `nails` `tuft` `glow` `eye_back` `worn_palm` `loop` `warm` `bands` `tassels` `post` `lens` `pale_palm` `band_light` `ribbon` `cuff_other` `ghost` `wisps` `patch` `stripes` `spur` `rivets` |

The Coat:

| Key | What it is | Styles |
|---|---|---|
| `kind` | the Starter is only its clasp | `clasp` `coat` |
| `length` `flare` `chest` `waist` `shoulders` | its cut: shoulders to hem, and how it spreads | numbers |
| `open` `cut` | how far it stands open down the front; how far it is cut away toward the hem | numbers |
| `wave` `rag` `sweep` | a hem that moves; a hem that has been through things; `[side, back]`, the way the skirt is blown | numbers |
| `sleeves` | a style, or `[left, right]`; `arm` is how thick | `hang` `flat` `reach` `spread` `back` `none` |
| `collar` | `[style, size]` | `turned` `stand` `high` `spread` `ear` `hood` `fur` `cape` `whiskers` `frost` `none` |
| `lining` | what shows where it is turned back (collar, lapels, cuffs); `field` is the field's light at those edges, `storm` is light all through | `plain` `field` `storm` `red` `fur` |
| `mantle` | what its shoulder cape is made of | `oil` |
| `clasp` | the size of the clasp at its throat | number |
| `grown` | what it has grown, carries, or has had done to it | `belt` `buttons` `buttons2` `offices` `pack` `dust` `stamps` `pockets` `items` `pelt` `rime` `pads` `lamp` `smoke` `ghost_sleeve` `knife` `lapels` `eyes` `stars` `wind` `scorch` `epaulettes` `chain` `sash` `stock` `oath` `tug` `hook` `patches` `figure` `tokens` `whiskers` `drops` `current` `mantle` |

All three take `stands` and `coat` (the shift), as above. A style may not be `null` (that
takes the key off and the line's default comes back): say `none`.

**Their gifts** (what a hybrid of another base wears to say it is half armor), as parts in
`tools/blender/genius_relics.py`: the Shield's `broad-guard` (a small iron shield at the
shoulder) and `shell` (a round shield across the back); the Gauntlet's `small-hands` (a
pair of gloved hands) and `talon-grip`; the Coat's `wing-cloak` and `shadow-cloak`.
## The Hawk and the Tortoise (`tools/blender/lines_beasts.py`)

Neither is on the wolf's rig. A tortoise is its shell: one object the game walks, with a
dome, a rim, four legs and a neck that comes out or stays in. A hawk is a body on the wing
with two wings the game beats (`wing_l`, `wing_r`; it is built at the bottom of the stroke),
or the same bird perched with its wings shut. The Harrier and its two Finals are ground
hunters in the tree, so they are a hawk that runs, built on the wolf's rig (`"rig": "ground"`).

The Tortoise:

| Key | What it is | Styles |
|---|---|---|
| `build` | proportions against the stage's own | `width` `length` `dome` `legs` `girth` `neck` `head` `tail` `eyes` `beak` (multiples of 1); `round` `rim` `stance` `lift` (set outright); `flat` (under 1: the top is cut flat); `wedge` (the front stands higher) |
| `shell` | the dome and its plates | `young` `dome` `stones` `ridges` `iron` `lit` `smooth` `worn` `map` `dial` `moss` `soft` |
| `rim` | round the edge of the shell | `lip` `marginals` `ward` `plaques` `serrated` `spikes` `none` |
| `legs` | | `stump` `set` `tucked` `web` `worn` |
| `neck` | how the head is carried | `peek` `out` `in` `hidden` `high` `long` `low` |
| `jaw` | | `hook` `gape` `chain` `horn` `lure` `old` `trumpet` `snorkel` `notched` |
| `tail` | | `short` `long` `keel` |
| `carry` | what rides on the shell | `pebbles` `cairn` `gnomon` `post` `milestone` `packs` `wagon` `hearth` `lamps` `balance` `dial` `salvage` `teeth` `garden` `reeds` `anvil` `stele` `ward` |
| `marks` | on the hide | `dust` `mud` `soot` `straps` `hoop` `weeds` |
| `coat` | | the shifts above, and one more, `moss` |

Its three paths: the Stone-back's is stone and iron on a high dome, a warded rim, a jaw
that waits (slate); the Cairn-back's is a flat back that carries things, a cairn first and
then a post, a wagon, a hearth, a hall's candles (warm, then ash and moon); the Unhurried's
is long legs and a high neck with a chart on its shell, or a prow of horn, or a flat soft
shell low in the water (night, blood, moss).

The Hawk:

| Key | What it is | Styles |
|---|---|---|
| `build` | proportions against the stage's own | `size` `body` `chest` `head` `neck` `span` `chord` `tail` `legs` `feet` `beak` `eyes` `shoulders` (multiples of 1); `pitch` `look` (degrees, in place of the pose's) |
| `pose` | how it holds itself | `fledge` `soar` `hover` `dive` `stoop` `perch` `mantle` `lean` |
| `wings` | open, and the game beats them | `stub` `broad` `long` `pointed` `round` `kite` `soft` `swept` |
| | shut, or worn | `folded` `tucked` `cloak` `shield` `ironshield` `shelter` `broken` |
| `tips` `dihedral` `sweep` `wingpitch` | numbers for open wings | how many primaries are lit; how high the wings are held; how far back the whole wing is swept; how much of the body's pitch the wings share |
| `tail` | | `short` `fan` `long` `fork` `square` `wedge` `spread` `streamers` |
| `head` | | `call` `crest` `crown` `owl` `white` `plume` |
| `eyes` | | `dark` `owl` `far` `old` |
| `feet` | tucked in flight unless said | `down` `set` `grip` `strike` `dangle` |
| `perch` | what it stands on | `stone` `iron` `tower` `glove` `shoulder` |
| `carry` | what it has been given | `lamp` `case` `plate` `writ` `bright` `jesses` `rings` |
| `aura` | | `smoke` `hush` `ring` `cold` `underwing` `flock` `dust` |
| `sleek` `down` `iron` `stance` | | feathers laid flat; a nestling's down (a size); which wing is iron; how wide it stands |
| on the ground rig | the wolf's `build`, and | `crest` `wings` `fan` `bill` (sizes); `tufts`; `grown`: `sickle` `brambles` |

Its three paths: the High Circler's is the bird on the wing, told apart by the wing itself
(long, pointed, round and owl-eyed, broad and white-headed); the Eyrie-holder's is the bird
that stands, on a stone and then on iron, a tower or a shoulder, its wings a cloak or a
shield; the Stooper's is the bird that falls and is flown, swept wings and struck feet, then
the glove, the jesses, the message tied to its leg, and the Harrier that hunts on foot.

Their gifts are parts of this file too (`python tools/blender/lines_beasts.py parts`, or
with the rest by `genius_lines.py gifts`): the Hawk's `wings` and `talons`, the Tortoise's
`shell` and `broad-chest`.

A sheet's cells are measured before they are scaled, and a wide wing reaches into its
neighbour's: look at the Hawk with `--cell=7`.

Both lines are built, all thirty-one of each. An unrigged body here is under 120 KB; the
three on the wolf's rig are under 200.
## The small people: the Imp, the Sprite, the Homunculus

Built by `tools/blender/lines_people.py` (with `people_dress.py`, `people_things.py`,
`people_carry.py`, `people_shapes.py`) from the human pipeline on the people's rig. A form is
a small person of its own: a child's head on the Starter, a figure with presence at the
Final. Its attire is cut from its own skin (pushed out and painted), so a dressed body is
still one welded skin; what it has grown, wears on its head, holds and carries are pieces
that ride its bones. It has its own hands; nothing is hung on it for a feature its line
gave it.

The three paths of each, by what never changes down them:

| | Path | What it is at a glance |
|---|---|---|
| Imp | Debt-collector | stocky, forward, bull-horned, in an oxblood coat (`blood`), a chain of tags at its belt |
| | Stickler | thin and tall, lilac (`moon`), a white collar, thin straight horns, a glass in one eye, a pen's nib on its tail |
| | Surety | charcoal (`ash`), upright, ram-horned, dressed in parchment ruled with black: a kilt, then a robe; it grows into the size of what it promised |
| Sprite | Hob | stocky, in a linen shirt and a brown apron (`hearth`), a kerchief or a cap, green wing-cases held half open, the light at its belt or in its hands |
| | Lore-sprite | bent to look, long-haired and spectacled, moth-winged and pale (`moon`), in a gown; the light held up to things |
| | Pixy | lean, grinning, spike-haired, in its own leaf-green, on long glass wings; the light kept away from itself |
| Homunculus | Clay Apprentice | a maker in a leather apron, its hands the best of it |
| | Likeness | slimmer and smoother at every step, pale as a doll (`moon`), in homespun like a person's, masked or half-faced |
| | Clay Bearer | slate-grey (`slate`), broad and bowed, strapped for a load, and at last loaded |

The forms that name another silhouette are built to it: a clerk's or a fitter's or a
lamplighter's attire in that body's own roles, so the partner's coat still goes on; the
Imp's Marginal and its two Finals are a book open in the air with a thing of ink come out
of it (`rises`: `climbs`, `reads`, `points`), and the Sprite's Star-burst is a drift of
small lights, neither with a rig (`shape`: `marginal`, `starburst`).

Three things these lines had to learn, which hold for any line of people:

- **A shifted coat is one colour.** A shift brings every colour of the partner's coat most
  of the way to one tint, so a body whose skin and clothes are both the coat (the
  Homunculus's clay, the Imp's ink) goes flat in a shifted path. So each path wears the
  coat on its skin, and where it can on its main garment, and something of the lines' own beside it that no
  shift touches (`OWN` in `lines_people.py`: `homespun`, `paper_old`, `apron_hide`,
  `robe_black`, `seal_wax`, `tin`, `beetle`, `wing_glass`...). Those are written into the
  model in linear light, and show brighter in the game than their numbers look.
- **Every light on a body burns alike** (the game lights every `field` surface the same),
  so a large surface of light is a blur. A wing is glass with the light in its veins;
  only a wing called `light` is light, and that is kept for the forms that are a blaze.
- **Each kind has its own eyes**, so a face reads on its own skin: the Imp's are alight
  from lid to lid in a dark face, with a slit down them; the Sprite's are large and dark
  in a pale one, with a light in each; the Homunculus's are dark, with the light sunk in
  them. The Sprite has hair (a cap of it cut from the scalp, and leaves over).

A slot holds a style, `[style, size]`, `[style, size, word]`, or a list whose entries are a
style or `[style, size and word in either order]`. The word is a material (a role of the
partner's coat, `main`, `under` or `trim`, or a name from the kit's palette or the lines'
own) or a variant.

| Key | What it is | Styles |
|---|---|---|
| `build` | proportions, each against its stage's own, so a line carries them down as it grows: `head` `legs` `arms` `hands` `feet` `limbs`; and as given: `age` `belly` `wide` `deep` `shoulders` `neck` `hips` `ears` `fat` `old` `bow` (how far it stoops) `forearms` `leg_girth` `arm_girth`, and any of MakeHuman's own details by its name (`nose-scale-vert`) | |
| `skin` | marks on the body itself | `script` `cracks` `crackle` `rough` `clay-legs` `ink-arms` `ink-hands` `iron-arms` `stone-arms` `fired-hands` `stone-knuckles` `glow-hands` `glow-fingers` `terms-palms` `wax-nails` `white-gloves` `thread-fingers` `wrist-gears` `flat-arms` `cogs` `white-knees` `ink-feet` `wet-legs` `scratched-legs` `webbed-feet` `clawed-feet` `patch` (above 1: the patches before it too) `mends` `scorch-marks` `tear-tracks` |
| `wear` | what it is dressed in | `rag` `kilt` `shift` `tunic` `shirt` `shirt-rolled` `waistcoat` `coat` (size: how far its tails fall) `robe` `apron` `breeches` `hose` `boots` `gloves` `cuffs` `sleeve-guards` `bracers` `belt` `sash` `collar` `scarf` `muffler` `collar-fur` `stole` `tabard` `mantle` `cloak` `shadow-cloak` `hood` `bandolier` `harness` `pauldrons` `strap-plates` `beetle-plates` `padding` `bandages` |
| `eyes` | how they are lit | `lit` `big` `dim` `far` `black` `old` `shut` |
| `mouth` | | `open` `wide` `pursed` `tongue` |
| `face` | | `glass` `spectacles` (`low`) `loupe` `goggles` `mask-smooth` `tin-mask` `face-mask` `blank-half` `second-face` `big-eye` `big-ear` `beard` `thumbprint` `mouth-light` `dents` |
| `head` | horns, crowns, hats, hair | `nubs` `horns-bull` `horns-quill` `horns-swept` `horns-ram` `horn-brow`; `crown-plain` `crown-coins` `crown-wire` `crown-grass` `crown-iron` `circlet`; `thimble` `beetle-helm` `cap-square` `cap-flat` `cap-peaked` `cap-wool` `kerchief` `hat-brim` `acorn-cap` `lamp-roof` `eyeshade` `brow-band` `lamp-band`; `crest` (`long` `spiky` `swept` `flame`) `hair-wig` `seam` `brush-ear` `pens-ears` `screwdriver-ear` `quill-ear` `twigs` `veil` `brow-ridge` |
| `back` | | `tail` (`spade` `hook` `nib` `seal` `ball`); `wings` (`bud` `glass` `beetle` `moth` `dragonfly` `pages` `light` `elytra` `frost` `soot` `eyed`); `welts`; `pack` `pack-frame` `bundle` `book-stack` `card-drawers` `thread-spool` `hod` `satchel-back`; `lamp-pole` `lamp-pole-behind` `crook-lantern` `tap-pole` `broom` `hammer-long` `spanner-back` `litter-poles` `toll-pole` `stakes` `winding-key` `smoke` `lantern-behind` |
| `chest` | what it holds to it or wears on it | `book-hug` `book-flat` `book-clasped` `book-open` `lantern-hug` `lantern-heart` `lantern-peek` `thimble-string` `badge` `wall-plate` `heart` `heart-glow` `ember-heart` `seal` `dial` `clock` `pattern-ring` `terms` |
| `belt` | | `book` `chain-tags` `lantern` `lantern-front` `purse` `pouch` `shot-pouch` `tools` `keys` `seals` `kettle` `satchel` `ledger-chained` `chalk-ring` `bandage-rolls` `pincushion` |
| `right`, `left` | what is in each hand | `bill` `letter-open` `writ` `writ-long` `paper-bag` `quill` `mallet` `snuffer` `candle` `scales` `relic` `flask` `coal-fist` `broken-chain` `toll-bowl` `needle` `needle-lance` `button-shield` `coal-shell` `rag` `chain-lamp` `key-ring` `lantern` `lantern-stick` `lantern-low` `dial` `thorn` (`upright`) `short-blade` (`steel`) `shot` `stone` `spanner` `trowel` `chalk` `seal-stamp` `brush-tool` `cup-shade`; and what an arm has become: `book-arm` `book-grown` `edge-hand` `barrel-arm` |
| `around` | what keeps it company | `motes` `ring-lights` `gear-halo` `coals` `shades` (`line`) `wedge` `little-ones` `afterglow` `light-ring` `ward-ring` `standing-air` `lamp-glass` `small-weather` (`pale` `storm`) `strings` |
| `coat` | how its partner's coat is worn | the shifts in `data/genius-looks.json` |

A lantern is `round`, `square` (a window with someone home), `jar`, `shutter`, `eye`, `cold`,
`thimble` or `shell`, wherever one is carried.

**What they give a hybrid** (`python tools/blender/people_gifts.py`). Other bases give
horns, a tail, a glow and small hands too, so a gift is the giver's own part where it has
made one, `game/assets/genius/gifts/<base>-<feature>.glb`, and the game hangs that in
place of the common part: the Imp's thick pale horns ruled with its ledger's light and its
red tail, banded with brass and hung with tags; the Sprite's winged lantern in a ring of
afterglow and its small hands in cuffs of petals; the Homunculus's maker's hands, larger
than the arm they are on, and its brush. A hybrid's form that wears a body of the base it
turned toward is not hung with that base's gift: the body has it already.


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
wood, cloth and a bell's teeth keep colours of their own, so that they read on any coat. A
turned thing is shaded round with crisp rims; a cut or forged thing keeps its planes; cloth
(a cape, a hood) is a sheet with a thickness, so that it has two faces.

**Each Path wears the coat its own way** (`coat`, a shift), so that a line can be told by
its colour before its shape: of the Lantern, the Wayfinder keeps the coat as it was born
(its water forms and the Deep-light in blue steel, `iron`), the Watch-lamp wears it as
copper (`hearth`), the Kept Flame as silver (`moon`); of the Astrolabe, the Sighting-glass
as born, the Orrery pale (`moon`), the Almanac the brown of a bound book (`hearth`); of the
Bell, the Rally-bell bronze as born, the Hour-bell silver (`frost`), the Alarm-bell red
(`blood`). A final form may still wear its own where its sign says so (the Watch-bell is a
dark bronze that shows no shine at night; the Passing-bell is one cold note).

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
feet on the ground, a `held` size, under 80 KB; it ends "items: 93 forms, all good".
