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

