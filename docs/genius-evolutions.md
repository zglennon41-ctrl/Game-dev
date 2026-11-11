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

## The spirits: the Lurker, the Fiend, the Ember, the Fog

The things with no flesh: shadow, wick, flame, weather. `tools/blender/lines_spirits.py`
(one file a line: `spirits_lurker.py`, `spirits_fiend.py`, `spirits_ember.py`,
`spirits_fog.py`; what they share is `spirits_kit.py`). None has a rig: a body is built as
pieces and written as one object with sockets. Each has a `plan` (what kind of thing the
form is), and round the plan the slots below. A child with a new `plan` restates its `build`.

**How each floats or stands.** The Fiend walks at its partner's heel (an imp on two legs, a
stove on three); its bodies are built standing on the ground. The Lurker, the Ember and the
Fog float at the shoulder, as their silhouettes do, and so does whatever a form of theirs
stands on: the Vigil's chair, the Camp-fire's ring of stones, the Sea-fret's quay are part
of the body and go where it goes. Each is a piece of its own ground, with rolls or tatters
under it, so that it reads as one thing carried and not as furniture in the air. Every body
is set down on its lowest point.

What each line keeps from its Starter, and what each path adds and carries:

| Line | It keeps | The three paths |
|---|---|---|
| Lurker | a hood of ink and two eyes in it | broad and behind, a mantle (the Back-stander's); bent and sitting, a chair and a lamp, coat `ash` (the One Who Sits Up); narrow, its collar up, coat `iron` (the Unremarked) |
| Fiend | two horns, a scowl, the candle on its skull | the fire let out: a maw, a mane of flame (Flare-up's); banked: ash-grey, letters, bottles and smoke, coat `ash` (Banked Coal's); a hearth: a grate, stoves and candles, coat `hearth` (the Grate-fiend's) |
| Ember | the coal it began as, at the foot of its flame, with its eyes lit in the coal | kept: a bed, a ring, a shell (Kept Fire's); small and stubborn: thin, pale, with the things of study and signal, coat `moon` (the Rushlight's); spent at once: ragged, thrown, running (Wildfire's) |
| Fog | rolls of grey and two eyes | the cowl: the hood of a coat with nobody in it (the Fog-shroud's); square edges, pale bands and a stone, coat `moon` (Lingering Mist's); the curl: a tail that is already leaving, coat `iron` (Shifting Fog's) |

| Line | Key | Styles |
|---|---|---|
| Lurker | `plan` | `blot` (the Starter) `figure` `seated` `robed` `door` `gate` `hatch` `human` `streak` `corner` `monolith` `tree` |
| | `build` | `tall` `broad` `hood` `skirt` `lean` `hem` `turn` `reach` `thick` `tatters` `deep` |
| | `eyes` | `slit` `dim` `old` `one` `wide` `holes` `closed` `none` |
| | `arms` | `hang` `broad` `spread` `guard` `long` `apart` `reach` `lap` `cup` `hold` `mantis` `up` `back` `wings` `whisper` `blade` `floor` `none` |
| | `legs` `ground` | `stilts` `back` `roots`; `long` `cohort` `ring` `wall` |
| | `wears` `chest` `face` | `mantle` `collar` `script` `cape` `shawl` `rime`; `maw` `cold-hand` `core`; `mask` |
| | `shoulder` `head` `back` | `face` `face-crowned`; `ear` `prow`; `chair` |
| | `holds` `aura` | `lamp` `lamp-low` `dark-lamp` `glow` `book` `chain` `blade`; `veils` `breath` `stubs` |
| Fiend | `plan` | `wick` (the Starter) `imp` `ball` `bottle` `stove` `candle` |
| | `build` | `belly` `tall` `head` `legs` `lean` `dive` `lift` `horn` `ear` |
| | `eyes` `mouth` `horns` | `scowl` `wide` `old` `sleepy` `shut` `white`; `grin` `maw` `scowl` `lamp` `none`; `curved` `stub` `long` `swept` `ram` |
| | `arms` | `hang` `hips` `crossed` `out` `low` `up` `raise` `forward` `down` `wrap` `knees` `cup` `grip` `ride`; `raise/hips` gives each its own |
| | `hands` `legs` `tail` | `claws` `small` `plated` `ash` `fists`; `bowed` `long` `tiptoe` `sit` `crouch` `kneel` `ride`; `flame` `dark` `none` |
| | `crown` `skin` `chest` | `candle` `flare` `fuse` `letters` `thread` `bare` `none`; `ash` `iron` `soot` `still`; `grate` `core` `cracks` |
| | `wears` `holds` `rides` | `apron` `necklace` `bracelet` `bottle`; `flame` `hammer` `writ` `snuffers` `coal` `list`; `blade` |
| | `ground` `aura` | `hill` `sling` `fires` `ring` `ward` `puddle` `heap` `sift` `stick` `quiet` `anvil`; `mane` `smokes` `steam` `wings` |
| | `bottle` `stove` | `bound`; `walker` `pot` `watchfire` |
| Ember | `plan` | `spark` (the Starter) `flame` `window` `hollow` `mast` `wax` `wheel` `lash` `star` `dart` `line` `mouth` `whirl` |
| | `build` | `r` `h` `n` (how wide, how tall, how many tongues) `lean` `side` `lift` `ragged`; `long` (a dart's) |
| | `eyes` `bed` | `dark` `pale` `old` `one` `none`; `coals` `stones` `logs` `sticks` `rush` `bowl` `basket` `pot` `book` `lamp` `frost` |
| | `shell` `crown` `wings` `ring` | `scale` `petals` `clinker` `cage`; `twelve`; `thin`; `ground` `dial` `impact` |
| | `has` `smoke` | `andirons` `fireback` `gimbal` `pages` `flashes` `chain` `hand` `shimmer` `cinders`; `thread` `stream` |
| Fog | `plan` | every form is its own: `wisp` (the Starter); `coat` `layer` `mask` `horseshoe` `folds` `douse` `pall` `maw` `pool` `thick`; `pillar` `wall` `drift` `streamers` `graves` `bust` `trail` `hoops` `edge` `curtain`; `swirl` `echo` `faces` `signpost` `frost` `hoar` `blackice` `hound` `flood` `storm` |
| all four | `coat` | a shift, as on the wolf's rig |

Two things these bodies need that a beast's does not. A flame, a shadow and a fog have no
face of their own, so each line is given one that carries: eyes in a hood, in a coal, in a
cowl. And a thing that is low and long (a streak, a line of fire, a pool) is not stood by
its crown, or it would fill the room: `spirits_kit.py` never lets a body be more than 1.7
times as far across as the height its `ref_top` stands it to.

**Their gifts** are parts, written by `tools/blender/parts_spirits.py` to
`game/assets/genius/parts/<feature>.glb`:

| Base | Gift | What it is | Where it hangs |
|---|---|---|---|
| Lurker | `shadow-cloak` | a ragged mantle of ink, a hood thrown back, the hem streaming | the back (`socket_back`) |
| | `watching-eye` | one great eye, lidded in ink, the dark standing up off it | the brow (`socket_eyes`) |
| Fiend | `ember` | a split coal, its flame up either side of whatever carries it | the light (`socket_light`) |
| | `horns` | long, swept, ridged, ringed with the field at the root | the head (`socket_head`) |
| Ember | `ember`, `glow` | the coal, and a rayed halo of the field round it | the light, both |
| Fog | `mist`, `glow` | a wreath of fog at the breast, trailing down the flanks; the halo | the breast (`socket_body`); the light |

**What was changed outside these files, and why.**

- `data/genius-bodies.json`, `featureSockets`: `shadow-cloak` and `mist` are given a place
  (the back, the breast). They are surfaces, and a surface hangs nothing unless it has one.
- `game/assets/genius/parts/`: `ember`, `glow`, `horns` and `watching-eye` are rebuilt
  bolder, and `mist` and `shadow-cloak` are new. These are the shared parts: a wolf that
  comes by horns any other way wears these too, and `glow`, `horns` and `shadow-cloak` are
  also other bases' gifts.
- Nothing in the game's scripts, in `genius_lines.py`, `genius_kit.py` or
  `data/genius-looks.json`.
- `spirits_kit.py` adds materials the kits did not have, named for what they are made of
  and not yet drawn from a ramp: `ash` `ash_dark` `ash_pale` `brick` `wax_red` `rust` `soot`
  `clinker` `clinker_light` `pane` `stone_grave` `timber` `mask_pale` `veil` `steam`
  `stubble` `grass_dry`.
