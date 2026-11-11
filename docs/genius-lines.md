# The lines: a body of its own for every form

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
| `build` | proportions against the stage's own, each a multiple of 1 | `legs` `girth` `chest` `waist` `neck` `nape` `head` `muzzle` `jaw` `ears` `tail` `brush` `body` `paws`; `pitch` (radians: more lowers the head); `stance` (how wide it stands); `croup` (its rump carried low; less than nothing, high) |
| `ears` | | `tunnel` `tall` `back` `split` `torn` `hound` |
| `eyes` | | `dark` `lamp` `old` `third` `far` `second` |
| `maw` | | `fangs` `open` `glow` |
| `ruff` | round the neck | `pup` `quills` `mane` `crown` `slate` `frost` `ember`; the Wolf's own, as locks of fur with its cheeks: `tuft` `scruff` `fur` `shag` |
| `spine` | along the back | `seam` `ridge` `quills` `iron` `plates` `smoke` `frost` `ember` `stars`; the Wolf's own: `crest` |
| `tail` | | `whip` `short` (its shape); `flag` `smoke` `lamp` `rings` `ember` |
| `flags` | from the shoulders | `fur` `pale` `light` |
| `armor` | | `brow` `chest` `chain` `harness` `scars` |
| `carry` | what it has been given | `lamp` `book` `tags` `knots` `post` `cloak` `shroud` `rug` `bell` `bird` |
| `paws` | | `set` `grease` `shade` `frost` |
| `aura` | | `windows` `motes` `cold` `crescent` `followers` |
| `marks` | where it wears its Path's colour (the second pass, rule 1); a step of the colour after a colon, `bars:light` | the body's own faces painted: `saddle` `blanket` `mask` `muzzle` `blaze` `socks` `stockings` `bands` `tailtip` `ears` `bib` `under`; fur laid on it: `stripe` `bars` `chevrons` `dapple` `rings` `hackles` |
| `trim` | `accent`: what it has been given takes its Path's colour too (a collar, a cloak and its band, a rug's bands, a lamp's cap, a post's bands, tags, scars, the boss of a plate) | |
| `face` | its eyes, lids, the mark round them, the corner of its mouth | `young` `open` `fixed` `aside` |
| `feet` | | `toes` |
| `fur` | tufts at the ears and a brush to the tail | `coat` |
| `pose` | how it carries itself, put on last: a list of `[what, radians]` | `crane` (its neck lowered; less raises it) `nod` `turn` (its head to its left) `tilt` `tail` (raised) `curl` `side` |
| `rest` | what it does when it has stood a while ("How it rests", below) | `sit` `lie` `crouch` `stride` `stalk` `point` |
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
  proportions. No textures. A rigged form under 300 KB, an object under 120 KB (the
  second pass raised both by half: rule 4).
- Colours from the kit's palette: muted earths, stone and metal, a value apart. The kit puts
  every colour on the style's ramps as it makes the material (`docs/style.md`).
- **A family's colours are its own.** Two families may each call a colour `moss` or `glaze`
  and mean different things by it (eleven names are shared so today). What a family's file
  adds to the palette is kept apart, and a base is built on the kit's palette, the Wolf's,
  and its own family's (`_families`, `_palette_of` in `genius_lines.py`). Building one line
  never repaints another.

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

A gift is the giver's own make of the part: `game/assets/genius/gifts/<base>-<feature>.glb`
(the Fox's `fox-tail` is a brush and the Drake's `drake-tail` a ridged whip, and both are "a
tail"). The game hangs that file for that base's gift and for nothing else; where a base has
made none, or the feature comes some other way (heritage, an adaptation, a graft), it hangs
the part every base shares, `parts/<feature>.glb`. A gift hangs where its feature hangs
(`data/genius-bodies.json`, `featureSockets`), unless that table gives the giver's own make
a place of its own under `<base>-<feature>` (the Lurker's cloak down the back, where the
Coat's is on the head). A form carried into a hybrid's line from its second base wears the
first base's body in its place (`wears`), and a body never wears its own base's gift.

## Looking at a line

```
python tools/blender/genius_lines.py wolf          # build the Wolf's thirty-one
python tools/blender/genius_lines.py --all         # every line and the Baby (about eight minutes)
godot --headless --path . --import                  # let the game take them in
godot --path . --resolution 3200x1800 -- --sheet=wolf --shots=DIR     # every form, a cell each
python3 tools/genius-sheet.py DIR out.png --line 2  # one path's line, large and named
bash tools/genius-tree-page.sh wolf                 # the page of the whole tree, with these in it
```

## Where it stands

| Line | Bodies |
|---|---|
| All twenty-eight | all thirty-one each: 868 models, one a form (the Moth, the Carp, the Octopus, the Angel, the Demon and the Elemental joined on 2026-11-11) |
| Hybrids | each wears its first base's bodies and its second's gift (43 gift parts, two a base bar the Lantern, whose glow is the shared one) |
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

## The second pass

> "I want a few more companion forms and I want you to do a tightening pass for detail,
> readability, and path uniqueness. I want each one to be intelligent, thoughtful, and cool.
> Also fix the way that the clothing is sitting. I think a full garment won't be easy with
> the mechanics but smaller accessory type genius may solve the problem. Also I want
> probably 50% graphics precision. Don't be afraid to use color to highlight path changes
> and textures. Make sure the anatomy makes sense or if its a magical universe choice lean
> in." (owner, 2026-11-11, on seeing all 682 bodies)

The first pass gave every form a body. This one holds every body to seven rules, each of
which can be looked at or measured. A family's worker builds to all seven.

### 1. A Path's colour

The world is muted so that a soul may carry colour. Each Path of a line has **one colour
of its own**, and every form under it wears that colour, so that a line's three Paths can be
told apart at the size of a thumbnail before their shapes can.

- It is data: the Path's `body.accent` names a ramp of `data/style.json`, and its forms
  inherit it (a form may name its own, a neighbour of its Path's, where its sign calls for
  it). `accent2` is a second colour for a form that needs one (a Final's trim).
- In the model it is the materials named `accent`, `accent_deep`, `accent_dark`,
  `accent_light` and `accent_pale` (the ramp's five steps; `accent2*` the same of the
  second). The builder's `mat("accent_dark")` is already the right colour
  (`genius_lines.accent`), and the game puts the colour on again at load from the data, so
  a Path's colour is changed in the JSON with no rebuild.
- Eight ramps are a genius's alone and may be more saturated than anything else in the
  world (`paths`, `pathCap` 0.72): `madder` (blood, pursuit, what will not be let go),
  `marigold` (the hearth, warmth, company), `gold` (an oath, a hoard, a watch-light),
  `jade` (the wild, patience, mending), `peacock` (water, the road, finding the way),
  `lapis` (night, cold, the long view), `amethyst` (secrets, omens, what is not said) and
  `rose` (likeness, affection, play). Any other ramp may be a Path's colour too.
- **How much, and where.** Between a tenth and a third of what can be seen of the form,
  and in the same kind of place down the whole Path: a wolf's saddle, mask and socks; a
  bird's wing-bars and tail; a coat's lining and collar; a lamp's enamel; a blade's grip and
  tassel. It is never the light (the field's light is the partner's Shape colour and
  nothing else) and never the whole body (the body is still its partner's coat).
- **It marks the change.** An Advancement keeps its Path's colour and takes its own step or
  pattern of it (banded where its Path was plain; `accent_pale` where its Path was
  `accent_dark`); a Final may add `accent2`. A pattern is geometry in an accent material:
  bars, bands, spots, eye-spots, chevrons, a stripe down the spine.
- A Path keeps to one coat shift or none, so that the coat does not argue with its colour.

| Line | Its three Paths and their colours |
|---|---|
| Angel | Shoulder-angel `gold` · Clarion `rose` · Weigher `lapis` |
| Astrolabe | Sighting-glass `peacock` · Orrery `lapis` · Almanac `madder` |
| Bell | Rally-bell `marigold` · Hour-bell `lapis` · Alarm-bell `madder` |
| Blade | Duelling Blade `lapis` · Cleaver `madder` · Scored Blade `gold` |
| Bow | Hunting Bow `jade` · War Bow `madder` · Singing Bow `amethyst` |
| Carp | Weir-leaper `jade` · Still-water Carp `madder` · Silt-reader `amethyst` |
| Coat | Travelling Coat `marigold` · Shadow-coat `amethyst` · Listening Coat `peacock` |
| Demon | Exile `amethyst` · Advocate `gold` · Head-down `madder` |
| Drake | Hoard-drake `gold` · Fire-drake `madder` · Sky-drake `lapis` |
| Elemental | Cornerstone `gold` · Tideling `peacock` · Squall `amethyst` |
| Ember | Kept Fire `marigold` · Rushlight `peacock` · Wildfire `madder` |
| Fiend | Flare-up `madder` · Banked Coal `amethyst` · Grate-fiend `marigold` |
| Fog | Fog-shroud `peacock` · Lingering Mist `gold` · Shifting Fog `amethyst` |
| Fox | Gone-away `jade` · Cache-fox `gold` · Fire-tail `amethyst` |
| Gauntlet | Maker's Hand `gold` · Fighting Fist `madder` · Open Hand `jade` |
| Gun | Long Gun `jade` · Repeater `marigold` · Standing Gun `lapis` |
| Hawk | High Circler `lapis` · Eyrie-holder `gold` · Stooper `madder` |
| Homunculus | Clay Apprentice `marigold` · Likeness `rose` · Clay Bearer `peacock` |
| Imp | Debt-collector `madder` · Stickler `lapis` · Surety `gold` |
| Lantern | Wayfinder `peacock` · Watch-lamp `marigold` · Kept Flame `amethyst` |
| Lurker | Back-stander `amethyst` · The One Who Sits Up `gold` · The Unremarked `lapis` |
| Moth | Candle-moth `marigold` · Emperor `amethyst` · Moon-moth `jade` |
| Octopus | Many-hands `marigold` · Latch-lifter `peacock` · Sleeps-on-it `amethyst` |
| Shield | Wall-shield `lapis` · Gate-shield `madder` · Shelter-shield `jade` |
| Sprite | Hob `marigold` · Lore-sprite `lapis` · Pixy `jade` |
| Stag | Tilter `madder` · Wood-walker `jade` · Watch-hart `gold` |
| Tortoise | Stone-back `lapis` · Cairn-back `gold` · The Unhurried `jade` |
| Wolf | Counting Wolf `marigold` · Third-day Wolf `madder` · Night-watch `lapis` |

### 2. It reads on a dark ground

The game is lamplit and most of its grounds are dark. A form whose lit surface is dim on
average is lost on them (the line check's `dark`). Nothing is fixed by making the whole
body pale; a dark thing is given an edge: a pale or coloured trim along its outline, a
lighter underside, eyes a size larger, a seam of the field where two dark surfaces meet, a
thing of another value held or worn. The Lurker is the model case: it must stay a thing of
ink and still be seen.

### 3. A different black shape

Every form on a line is a different outline from every other, and from its parent. The
line check lays each pair of outlines one on the other (`alike`: they overlap by four
fifths or more) and each form on its parent (`unchanged`). Told apart only by what it
carries is not enough: change the build, the carriage, the great part, the pose.

### 4. Half again the precision

"50% graphics precision" is read as half again as precise as the first pass: not final
art, but no longer a sketch. What it is spent on, in this order: the **face** (eyes with
lids that blink, a mouth, a brow: the form should look as if it is thinking); **hands,
feet, claws, hooves**; **the outline** (a curve that shows as facets is given more
segments; flesh is shaded round); then **surface** (pattern in the Path's colour, and the
grain the style lays on by what a thing is made of). The sizes: a rigged body under 300 KB
(was 200), an object under 120 KB (was 80).

### 5. Anatomy that is sound, or magic leaned into

A body is either what it says it is, with the joints and the weight of that animal or
thing, or it is a magical choice made on purpose and carried all the way. Nothing may be
one animal wearing another's parts by accident. Each family's section says which for each
line, in a sentence. The known cases: the Drake (was a hound with wings; rebuilt on
2026-11-11 as a true drake, and again on 2026-11-12 to the Wolf's standard: standing on
thick legs, a larger head, wings that are an event, rooted at the shoulder); the Hawk's Harriers (griffins by accident: to be griffins on purpose, or birds
on foot); what floats and should lie (a pool, black ice, a grass-fire); a fish and an
octopus in the air (a choice: they swim in the field, and everything about them says so).

### 6. What moves

A body with no clips for a thing can still move it. A piece of the model named
`<kind>_<what>[_l|_r][_<n>]` is moved by the game about its own origin
(`genius_lines.moving` makes one):

| Kind | What it does | For |
|---|---|---|
| `beat` | flaps about the way the body faces (`_l`, `_r`) | a wing |
| `glide` | the same, slow and shallow | a wing held out, a fin, a sail |
| `sway` | a slow pendulum | a lamp on a hook, a tassel, a cloak's hem, a tail at rest |
| `wave` | nods, each piece of a chain after the one before (`_<n>`) | an arm of an octopus, a feeler, a long tail |
| `wag` | the same from side to side | a fish's body and tail |
| `spin` | turns about its own up (`_r` the other way) | a wheel, a ring, a vane |
| `flick` | stretches and gutters along its own up | a flame |
| `pulse` | breathes | a throat, a bell of a jellyfish, a heart of light |
| `bob` | rises and falls along its own up | what floats beside it |
| `turn` | looks slowly left and right | a head, an eye on a stalk |
| `blink` | shuts now and then, all of a body's together | an eye |

The larger a body stands the slower it moves. A piece that rides a rigged body's bone is a
separate mesh parented to that bone. **Every companion blinks**, and every form has at
least one thing that moves; a form that is alive should not be perfectly still.

### 7. A worn piece

A genius that is worn (`data/genius-types.json`, `mounts`) and whose body will not sit on a
person as it is made has a piece for wearing: an empty named `worn` holding it
(`genius_lines.worn`). Worn, the game shows that piece and nothing else of it; let go, the
rest and not the piece. The Coat is the case: a whole garment cannot follow a body that
has no bones for it, so a Coat is worn as a **mantle**: its own collar and a short cape
across the shoulders, in its Path's colour, carrying its form's sign. The piece is made
where it would sit on a person standing at the origin, facing the way the kit faces, and
`worn` stands at the nape of the neck.

### The line check

```
godot --path . --resolution 1600x900 -- --sheet=wolf --plain --shots=DIR/sheet-wolf
python3 tools/genius-line-check.py DIR --detail             # every sheet in DIR
python3 tools/genius-line-check.py DIR wolf --against before.json
godot --path . --resolution 1600x900 -- --sheet=wolf --only=wolf-wall-wolf,wolf-grey-shield --shots=DIR
```

It reads the game's own pictures of a line and says how many pairs are `alike`, how many
forms are `unchanged` from their parents, how many are `dark` (lit to under a sixth of
full brightness on average, or three fifths of it nearly black), and how often a form's
colour puts it in its own Path (`colour`: 100% is every form; a third is chance). A
finished line has no alike pair, no unchanged form, no dark form, and its Paths told by
colour nine times in ten.

Before this pass, over the 22 lines and 682 forms: **213 pairs alike** (the Coat 64, the
Tortoise 48, the Shield 45, the Wolf 9, the Blade 8), **18 unchanged**, **37 dark** (the
Coat 9, the Lurker 7, the Hawk 5, the Imp 5), and the Paths **told by colour 57%** of the
time (the Stag 23%, the Ember 27%, the Fox 40%).

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
| Coat | the nape: between the shoulders, at the base of the collar. A Coat is not worn by its `wear` any more: it has a piece for wearing, a mantle, and the empty `worn` is what the game brings to the place (below, "The Coat: the second pass") | the wearer's own: up, the wearer's left, the wearer's front |

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
| `kind` | the Starter is only its clasp and the two scraps it still holds | `clasp` `coat` |
| `length` `flare` `chest` `waist` `shoulders` | its cut: shoulders to hem, and how it spreads | numbers |
| `open` `cut` | how far it stands open down the front; how far it is cut away toward the hem | numbers |
| `taper` `bend` | its skirts drawn in to a wisp; `[side, front]`, a bow of its whole length | numbers |
| `wave` `rag` `sweep` | a hem that moves; a hem that has been through things; `[side, back]`, the way the skirt is blown | numbers |
| `lean` `turn` | how it holds itself: `[to its front, to its left]` in degrees, from its hem; and turned about its own height | numbers |
| `sleeves` | a gesture, or `[left, right]`; `arm` is how thick | `hang` `flat` `trail` `reach` `grab` `spread` `back` `akimbo` `tuck` `raise` `cup` `throat` `point` `hold` `fold` `wrap` `heart` `behind` `low` `fore` `aft` `none` |
| `hand` | which hand holds what it holds (a lamp, a staff, a candle) | `l` `r` |
| `collar` | `[style, size]`; `ears` is `[left, right]`, how large each ear of an `ear` collar is | `turned` `stand` `high` `spread` `ear` `hood` `souwester` `fur` `cape` `whiskers` `frost` `none` |
| `lining` | what shows where it is turned back and where it stands open: its Path's colour (`plain`, `red`); `field` and `storm` put the field's light on its lapels and seams (never on a whole collar or panel: an eighth of a body is the most); `fur` is pelt | `plain` `field` `storm` `red` `fur` |
| `trim` | where its Path's colour is on its outside | `hem` `hem2` `dags` `facing` `piping` `yoke` `stripe` `spine` `cuffs` `bands` `collar` |
| `tone` | the step of its Path's colour its broad trims take (the line beside them takes another) | `mid` `dark` `light` `pale` |
| `mantle` `cape` | what its shoulder cape is made of, where that is not the coat's own stuff; how far the cape stands out at its edge | `oil` `dust` `wool`; number |
| `clasp` `brow` | the size of the clasp at its throat; how the lid of its eye is set, in degrees | numbers |
| `grown` | what it has grown, carries, or has had done to it | `belt` `buttons` `buttons2` `offices` `pack` `frame` `dust` `stamps` `pockets` `items` `candle` `pelt` `rime` `pads` `lamp` `handlamp` `smoke` `ghost_sleeve` `knife` `lapels` `spikes` `eyes` `stars` `wind` `scorch` `epaulettes` `chain` `sash` `stock` `oath` `tug` `hook` `patches` `figure` `tokens` `whiskers` `drops` `current` `mantle` `tails` `pool` `train` `fling` `cane` |
| `worn` | its mantle (below): `cut`; how far it falls (`back` `side` `front`), parts (`gap` `part`) and folds (`fold` `folds` `flare`); a hem in points (`points` `dag`); its own `trim` and `tone`; `ends`, how far a tippet's ends hang; `signs`, what it carries of its form (left out: whatever of `grown` a mantle can carry); `grown`, what only the mantle has | cuts: `capelet` `cowl` `tippet` `yoke` `scarf`; trims: `hem` `hem2` `piping` `facing` `yoke` `points` `ends` |

### The Coat: the second pass (`tools/blender/armors_coat.py`)

**What it is (rule 5).** A magical choice, carried all the way: a garment with nobody in
it, which holds itself as its wearer would. It stands on its hem, gestures with empty
sleeves, leans, turns, folds its arms; where a head would be there is the dark of its
collar or its hood. It looks out of the clasp at its throat: one eye of the field under a
brass lid, in a dark socket, so that it shows whatever colour the field is. Nothing of it
pretends to be a body.

**Three Paths: three colours, and three values (rules 1 and 2).** A Path keeps one coat
shift, so the three are told apart by how dark they are before their colour is seen: a
brown coat, a black one, a pale one. (A shifted coat is still brought onto the ramps
leather may wear, `data/style.json`: that is why `frost` comes out a pale tan and not a
blue.)

| Path | Colour | Coat | Where the colour is | What the Path keeps | Its Advancements' own step of it |
|---|---|---|---|---|---|
| Travelling Coat | `marigold` | `hearth` | the lining, a broad band at the hem, deep cuffs | a turned-up collar, a belt, something carried; it is always going somewhere | Oilskin `light`, two bands; Road-coat `pale`, a hem of points and a stripe down each side; Hide-coat bands on its arms |
| Shadow-coat | `amethyst` | `night` | a bright line along every edge (`piping`: a black coat's outline), the lining | a hood or a collar full of dark; it never stands square | Slip-coat `light`, a stripe down its spine; Night-coat a hem of points and its collar; Turncoat its fronts faced, and its lining flung out |
| Listening Coat | `peacock` | `frost` | the lining of its ears, the facing down its front, its cuffs | a collar shaped like two ears; it leans toward what it hears | Clerk's Coat `dark`, a yoke; Whisper-collar `light`, bands on its arms; Hand-me-down two bands at its hem |

**Thirty-one outlines (rule 3).** No two coats stand alike, and what tells them apart is
how each holds itself, which is its form's habit:

| Form | How it stands |
|---|---|
| Clasp | a hook and an eye a hand across, the eye open; two scraps of the coat hang from it and two points of a collar stand up from it |
| Travelling Coat | one sleeve reaching for the latch, a bedroll on its back |
| Oilskin | a sou'wester and a bell of a cape, its sleeves held out to shake itself |
| Pilot's Coat | leaning, its hem dragged aside by the current, one sleeve pointing the channel |
| The Lent Coat | narrow in the shoulder, its sleeves empty and flat, open and bowed round someone who is not there |
| Road-coat | leaning far into its stride, one sleeve swung forward and one back, its skirts swept out behind |
| Thousand-mile Coat | tall under a pack-frame, a staff in its hand |
| Many Pockets | short and broad, a fist on its hip, a candle end held out |
| Hide-coat | broad, a pelt over its shoulders, its arms held away from it |
| Winter Coat | a tent: hooded, wide in the skirt, its arms wrapped round itself |
| Deep-coat | short and square, stone on its shoulders, a lamp held out level |
| Shadow-coat | hooded and ragged, bowed aside, one cuff in a pocket |
| Slip-coat | narrow, bent like an S, its sleeves swept back |
| Empty Sleeve | one sleeve flat; the other stands apart from it, raised to ward |
| Knife-coat | open to its lining, its lapels like blades and its shoulders cut to points |
| Night-coat | long, its hands behind its back, two eyes in its collar, the night in a pool round its hem |
| Collar-up | a short coat under a collar as large as itself, one cuff holding the collar shut |
| Nobody's Coat | a hooded wisp with no sleeves and no hem, under a grey cape |
| Turncoat | one front flung open to its lining |
| Storm-lined | both fronts flung, and the weather coming out |
| Scorched Hem | a short stiff jacket, arms folded, leaning away from the fire |
| Listening Coat | one cuff cupped to an ear of its collar |
| Clerk's Coat | a tailcoat, one hand behind it and one brushing its breast |
| Coat of Offices | wide in the shoulder, a fist on its hip, a train behind it |
| Sworn Cloth | one sleeve raised to swear and one on its breast |
| Whisper-collar | short, under two ears larger than itself, one of them lifted |
| The Warning Tug | one sleeve stretched out further than an arm goes |
| Eavesdropper | hung from a hook, perfectly straight, its collar a dish |
| Hand-me-down | too large for anyone: its sleeves past its hem, its hem in a heap |
| Inherited Coat | tall and square, its hands behind its back, a head of light above its collar |
| Coat of the Cohort | its arms held wide |

**What moves (rule 6).** `blink_eye` (the iris and its slit, in the clasp) and `sway_tag`
(the tag on the clasp's ring) on every form. A sleeve that only hangs (`hang`, `flat`,
`trail`) is `sway_sleeve_l|r`. And by form: `sway_belt` (a belt's end), `sway_cup`,
`sway_pan`, `sway_lamp` (what hangs from it), `sway_scrap_l|r` (the Starter's scraps),
`sway_ghost` (the sleeve the Empty Sleeve left), `flick_flame` (Many Pockets' candle),
`blink_eyes` (what looks out of a high collar). On the worn piece: `blink_weye`,
`sway_wtag`, `sway_hood` (a cowl's hood), `sway_tassel_l|r` (a tippet's ends),
`sway_wscrap_l|r` (the Starter's).

**The worn piece: a mantle (rule 7).** A coat that is worn is not its whole body hung down
a back. It is the coat's own collar and a short cape over the shoulders, in its Path's cut
and colour, with its form's sign on it small, and its clasp at the wearer's throat.

- *It is made on the bodies it is worn on.* `MANTLE_ROWS` is its section at each height
  below the top of the shoulders: up the slope of the neck, flat across the shoulders,
  round the point of the shoulder, down the blades and the breast. One piece is worn by
  all twenty-six of the game's people, each brought to it by the chest bone, so the rows
  are the least that clears every one of them in the tunic they wear (the women's backs
  and napes stand furthest behind the bone and set its back; the men's chests set its
  front). Its folds open toward its hem.
- *It keeps clear of the arms.* It is longest down the back (never below the bottom of the
  shoulder blades: 0.34 under the top of the shoulders), shortest over the arms (0.10 to
  0.16), with its two ends down the breast.
- *Where it sits.* `worn` stands at the nape of a person at the origin; the game brings it
  to the chest bone, 0.4 up and 0.05 back (`data/genius-types.json`, `mounts.back`), and it
  rides that bone. A great coat's blades of light (the fifth and sixth instars) stand
  behind its wearer's head, from the mantle (`GeniusBody.set_worn`).

| Cut | Whose | What it is |
|---|---|---|
| `capelet` | the Travelling Coat's | a traveller's shoulder cape, longest down the back, a broad band of marigold at its hem and its collar turned up; the bedroll lies across the top of the back |
| `cowl` | the Shadow-coat's | a hood thrown back between the shoulders (it stirs), a hem cut in points, a bright line of amethyst on every edge |
| `tippet` | the Listening Coat's | round and even with a yoke of peacock, two long banded ends down the breast with a tassel on each (they stir), and the ears of its collar standing behind its wearer's own |
| `yoke` | the Slip-coat's | the least of them: no wider than a collar laid flat |
| `scarf` | the Starter's | no cape yet: a band of its cloth round the neck, and two scraps down the front from the clasp |

What a mantle carries of its form comes from the form's own `grown`, each sign made small
for it (`ON_A_MANTLE`; or `worn.signs` says): the Oilskin's is oilcloth with water standing
on it, the Pilot's has the current round its hem, the Hide-coat's a ruff of pelt, the
Deep-coat's stone on the shoulders and its lamp at the collar, the Night-coat's a collar to
the ears with its stars, Nobody's is plain grey, the Coat of Offices' has its epaulettes
and its chain, the Sworn Cloth's its oath on one end, the Inherited Coat's a hand of light
on one shoulder, the Cohort's its twelve tokens.

**How it is built.** The game draws a face from its own side only, and inks the other
(the toon shader culls back faces whatever the model says). So cloth here is made of
faces that each look one way: `skin` (a shell's outside, and its lining only where the
lining can be seen), `leaf` (a flat piece seen from both sides: two sheets back to back,
each the other's ink line), `band_on` (a trim lying on the cloth), `sheet` (anything else
already turned the right way out). The clasp is one mesh, set in two places: on the coat
and on its mantle. Every model with its mantle in it is under 120 KB.

**What is still weak.** The mantle is rigid: it rides the chest bone, so an arm lifted
high passes through the lobe over its shoulder, and a wearer bent far forward carries it
like a yoke. One cut for every body is a loose cut on some: on a man it stands three
fingers off the back and the nape, where on a woman it lies close. The eye in the clasp is
small at a distance (a thumbnail's width on a sheet): a coat's face is still its whole
bearing. On the sheet the Starter is drawn smaller than its cell allows (the sheet's first
measure misjudges a body under half a metre: `--cell=1.6 --only=coat-clasp` draws it
right). The Coat's two gifts to a hybrid (`wing-cloak`, `shadow-cloak`) are as the first
pass left them.

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
| Lurker | a hood of ink, lined, and two lidded eyes in it | broad and behind, a mantle, the maw or the door in its chest lit from inside, `amethyst` (the Back-stander's); bent and sitting, a chair, a rug and a light to sit by, coat `ash`, `gold` (the One Who Sits Up); narrow, its collar up, a bold pale edge, coat `iron`, `lapis` (the Unremarked) |
| Fiend | two horns, a scowl, the candle on its skull | the fire let out: a maw, a mane of flame (Flare-up's); banked: ash-grey, letters, bottles and smoke, coat `ash` (Banked Coal's); a hearth: a grate, stoves and candles, coat `hearth` (the Grate-fiend's) |
| Ember | the coal it began as, at the foot of its flame, with its eyes lit in the coal | kept: a bed, a ring, a shell (Kept Fire's); small and stubborn: thin, pale, with the things of study and signal, coat `moon` (the Rushlight's); spent at once: ragged, thrown, running (Wildfire's) |
| Fog | rolls of grey, round and breathing, and two eyes | the cowl: the hood of a coat with nobody in it, cloth of `peacock` (the Fog-shroud's); square edges, a stone, a lamp and a name, in `gold`, coat `moon` (Lingering Mist's); the curl: a tail that is already leaving, edged in `amethyst`, coat `iron` (Shifting Fog's) |

| Line | Key | Styles |
|---|---|---|
| Lurker | `plan` | `blot` (the Starter) `figure` `seated` `robed` `door` `hatch` `human` `streak` `corner` `monolith` `tree` |
| | `build` | `tall` `broad` `hood` `skirt` `lean` `hem` `turn` `reach` `thick` `tatters` `deep`; `watch` (0: its hood does not look about); `wisps` |
| | `thread` `edge` | which step of its Path's colour its edges are (`light`, `pale`), and how bold (1 is a thread) |
| | `eyes` | `slit` `dim` `old` `one` `single` `wide` `holes` `closed` `none` |
| | `arms` | `hang` `broad` `spread` `guard` `long` `apart` `reach` `lap` `cup` `hold` `mantis` `up` `back` `wings` `whisper` `blade` `floor` `bar` `none` |
| | `legs` `ground` | `stilts` `back` `roots`; `long` `cohort` `ring` `wall` `sill` `bed` |
| | `wears` `chest` `face` | `mantle` `collar` `script` `cape` `shawl` `rime`; `maw` `keyhole` `cold-hand` `core`; `mask` |
| | `shoulder` `head` `back` | `face` `face-crowned`; `ear` `prow`; `chair` |
| | `holds` `aura` | `lamp` `lamp-low` `dark-lamp` `glow` `book` `chain` `blade` `bar`; `veils` `breath` `stubs` |
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
`game/assets/genius/parts/<feature>.glb` (and, as a base's own make of one,
`python tools/blender/parts_spirits.py gifts lurker fog` writes
`game/assets/genius/gifts/<base>-<feature>.glb` and leaves the shared part alone):

| Base | Gift | What it is | Where it hangs |
|---|---|---|---|
| Lurker | `shadow-cloak` | a ragged mantle of ink, shaded round, a hood thrown back, the hem streaming | the back (`socket_back`) |
| | `watching-eye` | one great eye, lidded in ink, the dark standing up off it | the brow (`socket_eyes`) |
| Fiend | `ember` | a split coal, its flame up either side of whatever carries it | the light (`socket_light`) |
| | `horns` | long, swept, ridged, ringed with the field at the root | the head (`socket_head`) |
| Ember | `ember`, `glow` | the coal, and a rayed halo of the field round it | the light, both |
| Fog | `mist`, `glow` | a wreath of fog at the breast, round as the Fog's own rolls, trailing down the flanks; the halo | the breast (`socket_body`); the light |

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

### The Lurker and the Fog: the second pass

Line check, before and after: the Lurker 1 alike, 1 unchanged, 7 dark, colour 73% → **0, 0, 0,
100%**; the Fog 0, 0, 0, colour 60% → **0, 0, 0, 100%**.

**The Lurker stays a thing of ink, and is given edges.** Every hooded form is built from the
same pieces (`spirits_lurker.py`: `cloak`, `lining`, `hood`, `eyes_of`, `sleeve`, `hand_of`,
`tatters`), so the rule is kept in one place:

- The cloak opens down its front on a **lining** of its Path's colour, narrow at the breast
  and wide at the hem. A **thread** of that colour runs down each edge of the opening, round
  the hem, round the opening of the hood and round each cuff; the hood is lined with it; each
  finger ends in a nail of it. That is the tenth to a third of it that is coloured.
- Its **eyes** are half again as large, lit by the field, and lidded (a lid lowered over a
  long eye is the Lurker thinking). They blink. The hood is a piece of its own and looks
  slowly about, and what is in it or on it (a mask, a prow, an ear) rides it.
- Sleeves and legs are the lighter of its two darks and the folds of the cloak go by turns,
  so a pose reads without anything being made pale.

| Path | Colour | Every form of it has | Its second value |
|---|---|---|---|
| Back-stander | `amethyst` | the lining, the threads, a mantle dagged with it | something in its chest lit from inside by the field: the maw (Blow-eater), the hollow with a small light in it (the Hollow Behind), light under the door and at the keyhole (Door-shadow), a keyhole in its breast (Dark Threshold), the cellar's light round the hatch (Cellar-keeper) |
| The One Who Sits Up | `gold` | the lining, the threads | the things of a vigil: the rug, the chair's knobs, the candle and its stick, the lamp, the shawl, the bed's blanket, the book's boards, the second face's crown |
| The Unremarked | `lapis` | a deep blue lining | its edge is the pale step of the colour and bold (`thread: pale`, `edge: 1.6`): a blue-black figure drawn in a pale blue line |

*Its anatomy*, in a sentence: a Lurker is a choice of magic carried through, a hood, a cloak
and two hands of shadow with nothing in them, afloat; where a form has legs they are a
shadow's (stilts, or folded the wrong way, with hands for feet), and where it is some other
thing (a door, a tree, your outline, a clot in a corner) it is that thing made of the same
dark, with the same eyes.

*What lies or stands on a floor carries its floor* (rule 5), a grey thing with shreds of the
same dark hanging under it: the Small Shadow (one flagstone, and its shadow on it), the Long
Shadow and the Last in Line (the boards the shadow lies along), the Shadow of the Cohort (the
round of floor the twelve stand on), the Door-shadow (the doorway and its step), the Dark
Threshold (the sill; it bars the door, a bar across its hands), the Cellar-keeper (the flags
round the hatch, and the lid), the One Who Sits Up (the rug under its chair), the Name-stalker
(the wall and the floor at its foot), the Thing in the Corner (two walls and a lip of
ceiling), the Quiet at Your Back (a round of road, with the rings on it), the Count One Short
(the sod it is rooted in). The Vigil's three stand on the ground themselves. The Shot-shadow
is given no ground: it flies, beside the arrow it goes with. The Long-reaching Shadow's hands
are no longer on a floor: its arms hang below it and sway.

*What moves*: the hood (`turn_head`; not the Name-stalker's, which is at a wall), the eyes
(`blink_`), the hem in four pieces and every arm that holds nothing (`sway_`), the Dark
Ahead's arms (`glide_`), the cape, the chain, the ribbon, the boughs, a lamp under a swaying
arm (`sway_`), a candle's flame and the keeper's lamp (`flick_`), the glow, the heart, the
maw, the keyhole, the core, the road's rings (`pulse_`), the mask, the twelve in three
companies, the breath (`bob_`), the second face and the eye in the corner (`turn_`, and their
eyes blink).

**The Fog is made of cloud.** A roll is no longer a thing of its own. `roll()` only notes a
ball; when the form is done each part of it is made as one round surface a role
(`spirits_kit.cloud`: a metaball skin, thinned to a budget of corners), so that a bank has
one soft outline and not a line round every roll. A part breathes (`pulse_fog...`), and the
eyes and the dark round them ride it. `ragged()` and `wisps()` are the strands at its edge,
thin enough at their ends to see past, and they sway. What is not fog in a form (a cowl, a
stone, a post, a window) is hard-edged and still.

| Path | Colour | Held in | In the fog itself |
|---|---|---|---|
| Fog-shroud | `peacock` | the cowl: dark without, bright within, a thread round its opening, two tails that sway; and the rope on a pile, the border of the pall, the webs of a hand, a candle's dish | a dark roll of it low in the bank |
| Lingering Mist | `gold` | a name cut in every stone and gilded; lamps and their posts; an ear-trumpet, gateposts' caps, a bollard, boundary flags, a plumb-bob, curtain ties, a painted waymark | a pale roll of it, as if a lamp were in the fog |
| Shifting Fog | `amethyst` | the edge of every curl; the mouths, the voice's rings, a hound's collar, a window's frame, a ledger's boards, a flood-gauge, the rim of the ice | a dark roll of it under the blue |

A Path keeps to one coat shift: the Fog-shroud none (Choke-damp's `slate` and Black Damp's
`night` are gone; Black Damp is dark by a material of its own, `mist_black`), Lingering Mist
`moon`, Shifting Fog `iron` (Night-frost's `frost` and Black Ice's `night` are gone; needles
and ferns are `frost_white`, which no coat shifts). One form is off its Path's shift on
purpose: Rising Water has `coat: null`, its partner's own water, because under `iron` brown
water would be slate.

*Its anatomy*: fog is weather that has taken a habit; it has no body but its rolls, which are
one surface and breathe, and each form's sign is something the fog does to a place (lies on
it, stands in a gap, comes over a quay) or carries from one. The Driven Mist is fog in the
shape of a hound, on purpose: a deep chest, a long head, legs that are streamers, a collar.

*Its floor forms and their floors*: Ground-veil (a sod of open ground, a fence standing clear
of it), Black Damp (a cellar's flags and the first of its stairs, which it has come up),
Black Ice (the top step, and its joints seen through the ice), Trail-keeper (the path),
Lost-road (a round of road), Night-frost (the flag it settled on), Sea-fret (the quay),
Sudden Clearing (the sill), Hoar (the window it grows on).

*What moves*: every bank and limb of fog (`pulse_fog`, `_a`, `_b`, `_figs`, `_shape`,
`_anvil`), ragged edges, wisps, curls, the cowl's tails, a hung lantern, a ledger, flags,
tassels, ears, a hound's legs (`sway_`), shreds, steam, bubbles, salt, rain (`bob_`), flames
and the storm's bolts (`flick_`), the storm's ring (`spin_`), a cold place, a low sun, old
prints, ripples, a voice's rings (`pulse_`), and the eyes of every one (`blink_`).

**Still weak.** The Lurker: a floating form is small in its cell and in the world, and its
face smaller; the Hollow Behind faces you, with its second face at the side of its head (that
it stands the other way is not shown); the Long Shadow and the Last in Line use one device;
the Dark Threshold no longer shows the still air; the Second Assailant is the nearest to dark
(0.17 against 0.165). The Fog: `mist` is drawn as water is, so every roll has a highlight
(it wants a class of its own in `data/style.json`); the dark round an eye reads as
spectacles; the Trail-keeper is a caterpillar on a board and the Smother a stack of blankets;
the Calling Mist's faces are uncanny rather than nearly-known; Harbour Fog and Ground-veil
are within a tenth of the size an object may be.

**What was changed outside the two lines' files, and why.**

- `spirits_kit.py`, by adding only: `cloud`, `strand`, `curve` (fog and smoke), `Body.move`
  and the writing of moving pieces in `Body.export` (a body with none is written as it
  was), `planks` and `flags` (a floor), and colours for a floor, a corner, brick dust, black
  mist and white frost, each on a ramp.
- `parts_spirits.py`: the Lurker's `shadow-cloak` and `watching-eye` and the Fog's `mist`
  are shaded round, and `gifts <base>...` writes a base's own make to
  `game/assets/genius/gifts/` without touching the shared parts. Only
  `lurker-shadow-cloak`, `lurker-watching-eye` and `fog-mist` were rebuilt.
- Nothing in the game's scripts, `genius_lines.py`, `genius_kit.py`, `data/style.json` or
  `data/genius-looks.json`.
## The Wolf (`tools/blender/genius_lines.py`)

The line every other was made after, and the first held to the second pass.

**Its anatomy** is a wolf's, sound: four legs that walk, toes and a claw to each, a real ear
with a tuft at its root, a ruff and a mane of locks of fur (no two the same length, so its
edge is broken), a brush to its tail. What it has that no wolf has is said to be given or
grown, and is carried all the way: a lamp, a book, a rug, a post; slate where fur was; a
window in a flank; smoke; a crescent.

**What each Path keeps.** One coat shift down each Path, so the three families are three
values as well as three colours:

| Path | Coat | Colour, and where | Its face | Its Advancements, by what the colour does |
|---|---|---|---|---|
| Counting Wolf | `hearth` | `marigold`: the saddle, the inside of the ears, the tail's brush; the cord it counts on | `open`: round eyes that look at who is here, a brow over each, its head turned to you | Pack-runner bars across the back and socks; Hearth-wolf a blanket, dappled pale; Caller a pale bib under the lifted muzzle |
| Third-day Wolf | `ash` | `madder`: the muzzle as if dipped, a stripe down the spine, socks; its scars | `fixed`: narrowed, the lid lowered toward the nose, a slash over the eye and a tear-line down the muzzle as a courser has | Long-strider stockings; Throat-taker the throat and chest; Grey Shield two bands round each leg |
| Night-watch | `night` | `lapis`: the belly, throat and inside of the legs pale, bands on the legs, the inside of the ears; its cloak | `aside`: half-lidded, looking over its shoulder and past you, a pale crescent under each eye (it has not slept); dark round the eyes on a pale face | Perimeter Wolf a banded cloak and a blue brush; Moon-reader pale dapples like stars and a crescent; Storm-coat hackles |

A Final adds a step or a second place of the same colour (the Den-keeper's rug is woven in
bands of it; the Scar-bearer's scars are it; the Still Wolf has a bird of it on its head).

**What each form does** (its `pose`, and its `rest`):

| | Standing | Resting |
|---|---|---|
| Wolf pup | head on one side, tail up | sits |
| Counting Wolf / Pack-runner / Pack-mother / Line-runner | head turned to you / level / high, tail up, three small lights walking in its tracks / stretched forward, a lamp at its tail | (stands) / caught between two steps / (stands) / a forepaw lifted |
| Hearth-wolf / Den-keeper / Shade-friend | heavy, a lit window in its flank / rug and lamp / lean, smoking, head on one side | lies with its head up / sits up with its lamp / sits |
| Caller / Voice of the Pack / Oath-wolf | muzzle to the sky, a crown of fur / the same, larger, a chain / head level, a book | (stands) / sits and howls / sits facing you |
| Third-day Wolf / Long-strider / Name-hunter / Far Courser | nose a hand off the ground / looking back over its shoulder / nose down, tail up, tags / flags of fur streaming | (stands) / (stands) / a forepaw lifted / a long stride |
| Throat-taker / Red Maw / Quiet Tooth | head low, jaw open / jaws wide, a light in its throat, quills / low, shrouded, smoking | chest down and rump up / (stands) / sunk low, a forepaw off the ground |
| Grey Shield / Wall-wolf / Scar-bearer | square, slate on its shoulders / a wall, plated / head high and turned, scarred | (stand) |
| Night-watch / Perimeter Wolf / Post-wolf / Lamp-eyed Wolf | head high, turned away / cloaked / cloaked, a lamp on a post / eyes like lamps | (stands) / a short stride / lies under its lamp / sits |
| Moon-reader / Omen-wolf / Still Wolf | face to the sky under a crescent / tail straight up and ringed, a third eye / upright, a bird on its head | sits / (stands) / sits |
| Storm-coat / Frost-ruff / Ember-ruff | head down and aside, smoking / rime on its ruff / coals in its ruff | (stand) / (stands) / lies |

### How it rests

A form's `rest` is one clip of its model's own, named `rest`, made by the builder on that
form's own bones (so its feet come to the ground whatever the length of its legs). The game
(`genius_body.gd`) plays it in place of idle once the body has stood still a few seconds
(`data/style.json`, `motion.rest.after`, 2.5 where it is not given), blends back to the
borrowed walk the moment it moves, and shows a body first in its rest: so a portrait shows the
Den-keeper sitting, and in play it sits down beside you when you stop. Its habit is the brief.

What that took: a joint for each paw (`Paw.fl` and the rest: the rig's feet are one piece with
the leg above them, and a leg laid along the ground would stand its paw on end; no borrowed
clip moves them, so it walks as it did), and a bone at the hook of each thing that hangs
(`Hang.<n>`), which the resting pose keeps plumb, so a lamp at the collar of a sitting wolf
hangs down and not out.

### What moves

Ears, tail and legs by the borrowed clips. By name: the eyes blink (`blink_eye_l`, `_r`:
each a ball of the field's light with its pupil where it looks); what hangs sways
(`sway_lamp`, `sway_postlamp`, `sway_taillamp`, `sway_book`, `sway_tags`, `sway_knots`,
`sway_chain`); a lamp's light, the light in the Red Maw's throat and a cold core breathe
(`pulse_*`); smoke gutters (`flick_smoke*`); motes, the Pack-mother's followers and the
crescent rise and fall (`bob_*`); the Still Wolf's bird looks about (`turn_bird`).

### What the second pass found

- **The pale lines like cracks** were the field's own seams: the steady lines of light a
  Final carries (`data/genius.json`, `presence`, 0.14 at the fourth instar), which the edge
  shader drew a hair wide and nearly white. They are drawn now with a width of their own and
  in the field's colour (`genius_body.gd`, `seams`), on every line.
- **The eyes of the first try were on the ground.** A piece put on a bone was put where the
  bone stood in the pose the rig is imported in, not at its rest. The Wolf is built at rest
  (`pose_position`); the kit's own sockets on the wolf's rig still carry that small error for
  the other animals on it.
- **Ink.** The game draws a two-pixel line round every separate piece whatever its size, so a
  face made of small pieces is a blot. An eye is one closed ball whose pupil and glint are
  its own faces; fur is flat locks lying close; marks are the body's own faces painted where
  that will do.

## The wolf's kin: the Fox, the Stag, the Drake

`tools/blender/lines_wolfkin.py`. Each is the wolf's rig reshaped as a species, aged its own
way (a fawn is all leg where a pup is all paw), and then grown from its `body`. Underneath,
every form is one wolf reshaped: outlines change through proportion, carriage and what is
grown, and none has a skeleton of its own. The wolf's slots still work on them (`build`,
`ears`, `eyes`, `maw`, `spine`, `paws`, `armor`, `carry`, `aura`); what is theirs alone:

| Line | Keys | What they are |
|---|---|---|
| all three | `pose` | how it carries its head, put on last so that everything it has grown goes with it: `low` `high` `nod` `back` (over its shoulder) `aside` `tilt` |
| | `tail` | `up` `over` (arched over its back) `wrap` `low` `loop` |
| | `neck` | what is worn round a neck as it lies: `mane` `bell` `lamp` `ivy` `garland` `teeth` `chains` `ash` `bands` |
| Fox | `whiskers` `mouth` `tails` `tip` `mask` `face` `back` `feet` `fins` `claws` | what it carries in its mouth; two tails or many; what its tail-tips carry (`light` `white` `ring` `coal` `flame` `wisp`); a mask and the face under it. In `carry`: `panniers` `pole` `cape`; in `ruff`: `courtier` |
| Stag | `crown` `horn` `hung` `throat` `breath` `hide` `legs` `flank` `chest` | the shape of its antlers, what they are made of, and what is in them |
| Drake | `crane` `tail` `horns` `frill` `ridge` `wings` `membrane` `flight` `belly` `scales` `throat` `tailend` `shell` `lies` `hide` `jaw` `gape` `fangs` `breath` `nostrils` `claws` `feet` `eye` `lid` `head` `plating`, and `build.rear` | a body of its own on the wolf's bones: see "The Drake" below |

What each Path keeps: of the Fox, the Gone-away is lean and looks elsewhere, the Cache-fox
is hearth-brown with something in its mouth, the Fire-tail carries its tail high with a
light at the tip; of the Stag, the Tilter has a plated brow and its head down, the
Wood-walker a red hide and branch antlers with moss, the Watch-hart one ear turned and its
head over its shoulder; of the Drake, the Hoard is low and long and plated in gold, the
Fire stands up before, blood-red, its throat lit and its wings folded above its back, the Sky
is a wyvern, all wing.

The look's roles are kept, so the partner's coat goes on: `fur_dark` and `fur_light` on the
Fox and the Drake (whose ridge, wings and tail-tip are its markings), `hide_red` and
`fur_cream` on the Stag. Two coat shifts are theirs: `russet` and `brass`.

**Their gifts** (`python tools/blender/lines_wolfkin.py gifts`): the Fox's brush and its
foxfire (`fox-tail`, `fox-glow`), the Stag's crown and its long legs (`stag-horn-brow`,
`stag-long-legs`), the Drake's horns and its tail (`drake-horns`, `drake-tail`).

## The Octopus (`tools/blender/lines_octopus.py`)

A companion of the monsters' class, a keeper: the most intelligent animal that is nothing
like us. It thinks with every arm, gets out of anything, takes things apart to see how they
work, and holds eight things at once.

**Its anatomy** is an octopus's, kept whole on every form: a mantle (the sack behind the head,
which breathes), a head with two large eyes on turrets and a bar for a pupil, a small horn of
skin over each eye, a siphon under the right eye, and a crown of eight arms round a mouth
underneath, each arm pale and suckered on the side that faces the mouth. **The magical choice,
made on purpose:** it swims in the field, in the air. Nothing of it stands on anything; its arms
trail, curl and wave as in water that is not there; and what a form lives on or in (a book, a
mooring post, a bottle, a lever frame, a bed of earth with a wall round it) floats with it as
part of its body. No rig: a body is pieces, under 120 KB a form.

**Its colours.** Its skin is its Path's colour: it changes colour, and here that is the story
(the Starter "has not chosen a colour"; a Path is the colour it chose). The mantle and the backs
of the arms are the accent, patterned in the accent's own steps. Its partner's coat is its
face, the roots and pale undersides of its arms and the rims of its eyes (`hide_octopus` main,
`hide_octopus_pale` under, `hide_octopus_dark` trim: `data/genius-looks.json`, `beast-octopus`),
and the Starter is that coat and nothing else. The field is a ring round each eye, and what a
form holds: a lamp, a cup, rings, a mended seam, a light at an arm's tip.

| Path | Colour | The animal it is | What it keeps | Its nine |
|---|---|---|---|---|
| Many-hands | `marigold` | the round common octopus, mottled, kind-eyed | round and warm; arms full, and one free | a cup held high and still; stilts and a sling; a pot, a ladle and bowls; a pale cross of two reaching arms; a knotted line with a loop at each end; a mooring post and one long ringed arm; four lifted arms with rings of light; a wheel of eight tools; a mended plate over seven fists |
| Latch-lifter | `peacock` | the long-armed mimic, banded, keen-eyed | a tall narrow mantle; arms long and fine as wire at the tips | in a bottle, an eye at its neck; a corked bottle held high, a quill and a page; a great bottle on its back with a ship in it; five keys fanned; a lever frame under a lamp; itself the shape of a key; two shell halves and two tiptoe arms; a walled bed with a sprig; an old helm and a beard of arms |
| Sleeps-on-it | `amethyst` | the dumbo: a bell with ear-fins and a web, half-lidded | the bell, the fins, the web between the arms | asleep on a book; a comb of arms with an hour lit on each; a still parasol; a tall glass with weather in it; an inked arm and a thought in ink; a blot with eyes and an omen; a great book and two quills; a glass chandelier with one light; eight lights in a ring; a dark cloak, great fins, a cold light |

| Key | What it is | Styles |
|---|---|---|
| `mantle` | its shape, `[style, size]` | `round` `tall` `egg` `flat` `bell` `glass` |
| `skin` | the pattern, in the accent's steps | `plain` `mottle` `bands` `stripes` `rings` `pale` `bone` `hours` `weather` `inked` `glass` `deep` |
| `eyes` | | `bar` `wide` (a round dark pupil, no lid) `half` (the lid half down) |
| `arms` | its pose: where all eight go and what is in them. One a form | `inkling`; `many-hands` `cup-bearer` `splints` `last-served` `outstretched` `lifeline` `holdfast` `upraised` `wheel` `mended-plate`; `latch-lifter` `bottled` `bottle-post` `ship-bearer` `key-fan` `signalman` `skeleton-key` `shell-carrier` `gardener` `beard`; `dozing` `comb` `parasol` `tucked` `writer` `in-the-blot` `copyist` `chandelier` `ring-of-lights` `cloaked` |
| `holds` `house` | what is in its arms; what it lives in or on. Said for the reader: the pose builds them | |
| `fins` `web` | ear-fins on the mantle; a web between the arms | `ear` `great`; `skirt` `parasol` `cloak` |
| `build` | `arm` `girth` `head`, multiples of 1 | |

**What moves.** `pulse_mantle` breathes; `blink_eye_l`, `blink_eye_r` shut along their own up;
each arm is still for its first third (that share is part of the body, and carries the web)
and then one to three pieces `wave_arm<n>_<k>`, each the child of the one before, each turned
so that it nods across itself: an arm lifts and falls in the plane it curls in, and the wave
runs down it. What an arm holds rides its last piece. `glide_fin_l`, `glide_fin_r` are the
ear-fins; `sway_lamp`, `sway_keys`, `sway_steam` hang; `spin_ring_<n>` are the Plate-spinner's
rings and `spin_weather` the Storm-glass's cloud; `pulse_mind<n>`, `pulse_thought`,
`pulse_cold`, `pulse_light` are its small lights; `bob_ink` is the Ink-hand's thought. An arm
that carries something by more than one hold, or holds a thing level, is still on purpose:
the Cup-bearer's cup never moves, and Slack-water moves nothing but its eyes.

**Its gifts** (`python tools/blender/lines_octopus.py gifts`): `octopus-many-arms`, four arms
out of the wearer's back, suckered sides out, in the wearer's own Path's colour (the back,
`socket_back`); `octopus-bar-eyes`, two gold eyes with a bar on turrets wide of the wearer's
own, a ring of the field round each (`socket_eyes`). Both keep their moving names, so the
arms wave and the eyes blink on a wolf.

**Still weak.** Bottle-dweller's neck is lost behind its own eye and arm, so the bottle reads
as a jar. Key-turner and Eight-at-once are wide, so the game stands their bodies smaller than
their neighbours'. Ink-blot is a crowd of lobes and its drawn omen (a door) is small. The
Storm-glass, Glass Thinker and Eight Minds are "glass" by being pale and opened at the front
(nothing in the style is see-through). The comb's lit hours are small. An arm that grips a
thing does not wave, so Holdfast, Points-turner, Shell-carrier and Fair Copy move little.
Deep Sleeper alone on its Path wears a coat shift (`night`).
### The Drake

Rebuilt on 2026-11-12 to the Wolf's standard (the owner: "the wolf tree is incredible, the
drake tree is weak"). What was weak, form by form, came to five things: a head too small to
read; legs that were a wolf's skin, thin, folded under a belly that lay on the ground; wings
that were stubs or lay flat on the flank, so only one Path in three had an outline with wings
in it; tails that were a straight stick behind; and a Hoard Path that was a row of low lumps.

**Its anatomy, in a sentence:** a six-limbed dragon that stands with its belly clear of the
ground on thick legs (a round of muscle at each shoulder and each haunch, a forearm and a
shank under them, a heel on the ground behind), deep and keeled in the chest, plated under
from chin to tail, long in the neck and the tail, with a head half again a wolf's (a brow,
a jaw of its own, spines swept back from the hinge of the jaw, nostrils, teeth, an eye a
fifth larger than it was) and, as a third pair of limbs rooted above the shoulder, wings with
an arm, a wrist, fingers and the skin between. Six limbs is the choice made, and it is carried
all the way: the keel is there for the wings, and nothing of the forelegs is a wing.

**What is still the wolf's:** its skeleton and its three clips (idle, walk, run), so a drake
walks with a wolf's gait; and the skin of its four legs under the drake's own muscle, in one
hide all the way down (a wolf's pale inner leg and socks are painted out; the drake's toes
carry its socks). Everything else of the wolf is taken away as the form is built
(`_strip_wolf`), and the drake's own is laid on the bones: one skin from the back of the skull
to the end of the tail (`_drake_body`), cut to where the wolf's frame put its back, its
brisket and its ribs, so `build` still means what it says; and a head made from nothing
(`_drake_head`, sized by `HEAD_K`), so `build.head`, `muzzle` and `jaw` are its own.

**Carriage is data.** `crane` is how it carries its neck (`swan` as it is made, `low`,
`level`, `reared`, `hook`, `down`, `up`, `sky`, `ground`, `strike`, `proud`; a size under 1
goes part of the way): the neck is bent along its own line once it is made, so it stays
round however it is carried. `tail` has the drake's own carriages beside the kin's: `drag`,
`sweep`, `coil` (on the ground), `level`, `high`, `hook`, `lash`; `drag`, `level` and `high`
now turn one way and then the other along their length, so a tail is a line and not a stick;
a tail never goes under the ground. `build.rear` (the Drake's own) stands it up before: the
forelegs longer by that much and everything before the hips raised with them, so its back
climbs to its withers. A form is sized by where its head would be carried as it is made, so a
drake that carries its head on the ground is as large as one that rears.

**The three Paths are three dragons in outline**, each in one coat shift and one colour:

| Path | The dragon | Its coat | Its colour, and where | Each Advancement's step |
|---|---|---|---|---|
| Hoard-drake | low and long on four square legs, no wings to speak of, broad horns like a bull's, a back like a row of shields, plates lapped down each shoulder and haunch, eyes half shut (it is counting) | `brass` | `gold`: the shields of its back (`ridge: hoard`), the plates of its limbs (`plating: limbs`), the plates under it | Post-coiler banded, its neck up and its tail in a coil with a lamp in it; Ruin-sleeper dulled, head down under rubble and dust; Debt-drake plain and taller, one horn grown long, gold beads on a wire down its back |
| Fire-drake | upright: forelegs longer than hind (`rear`), deep in the chest, its neck carried proud, its throat lit between the plates, wings folded so that they stand above its back | `blood` | `madder`: the row of flame down its back, the plates under it, the skin of its wings | Kiln-throat pale under, wings half open, a glazed cap on its snout; Far-spitter banded up a long level neck; Smoke-drake dark, no flame, smoke where the ridge was |
| Sky-drake | a wyvern in build: narrow, long in the leg, risen a little before, all wing | `moon` | `lapis`: the skin of its wings, and the plates under it | Thermal-rider's wings out wide and pale along the leading edge; the Stooping Drake's dark and swept back; the Herald-drake's raised and barred, with a frill |

**Wings are an event.** They are a third larger than they were (`WING_K`) and heavier in the
arm. On the small forms they are `nubs` (the hatchling) or `folded`: the wrist carried above
the shoulder and the fingers trailing back, so a shut wing is still a shape against the sky
(`flat` is the old fold along the flank; `furled` a smaller fold). On Advancements and Finals
they open: `half`, `glide`, `stoop`, `brake`, `banner`, `shadow`, `cloak`, and the two that
are a Final's moment, `mantle` (raised high over the back, seen whole from the side) and
`rampant` (thrown wide). Every Final but the three that have given up the air for something
else (the Vault-drake under its vault, Old Coin gone to coin, the Ledger-wyrm) has its wings
out: the Sworn Drake's mantle in gold over a reared chest; the Gate-wyrm's laid out along the
road like the leaves of a gate; Slag-jaw's and the Signal-fire's raised; the Ridge-king's the
largest mantle of the line, the Trophy-drake's rampant.

**Its face.** Every drake has a brow over each eye, a lid, a slit, nostrils under hoods,
teeth along the lip and (past the hatchling) two spines swept back from the hinge of each
jaw. `eye` sets the eyes: `keen`, `counting` (half shut, one brow up), `glare`, `far`, `old`,
`shut`, `sly`; `lid: shutter` is the Gate-wyrm's. `gape` opens the jaw (`open`, `glow`,
`yawn`, `speak`, `taste`).

**What moves.** Every drake's eyes blink (`blink_eye_l`, `_r`, riding the head's bone). Open
wings ride the chest's bone: `glide_wing_*` where they are held half open or out for warm air,
`beat_wing_*` where it is mantling, rampant, landing or hanging in the air (`flight`
overrides), and a cloak of them sways. Also: `flick_` flames of the Fire's ridge, heat over
its nostrils and the Slag-jaw's drips; `pulse_` a lit throat or gullet, the Forge-drake's jet,
the Signal-fire's beacon; `sway_` lamps on their hooks, smoke, a beard, a black tongue, a
ledger on its strap, a pennant; `spin_helm` the Vault-drake's wheel; `bob_cinders`. Folded
wings and stubs do not move. (A piece named `*_wheel` would be taken by the importer for a
vehicle's wheel: hence `helm`.)

**Still weak.** The gait is a wolf's trot, and a dragged tail swings with the wolf's tail
clip. The hind leg still sits on its heel, so a drake at rest looks ready to spring rather
than standing square. The Hoard's low Finals (Gate-wyrm, Ruin-sleeper, Vault-drake) are long
and low by design and so are the smallest pictures of the line. Wings seen from dead ahead or
dead behind are thin: their webs are flat panels. Smoke is puffs of grey. The hatchling is
the partner's coat with no Path colour, and on a dark coat it is a dark small thing. One
model (the Ruin-sleeper, 302 KB) is a little over the 300 KB asked of a rigged body; the
heaviest was 289 KB. The base body the clips are borrowed from (`beast-drake`, `tools/blender/genius_tree.py`)
is still the first pass's hound-drake; it is seen only if a form's own model is missing.

## What is still weak

Said by whoever built each family, after looking at its sheets. None of these fails a check;
each is a form or a habit of the build that does not yet meet the rule at the top of this
page.

- **The Wolf**: its poses of rest are worked out, not drawn: a sitting haunch is a folded
  standing leg, and creases at the stifle. What hangs is plumb at rest but rides its bone
  while it walks. A cloak is short on a form that lies down (the Post-wolf), because a long
  one goes through the floor. The Shade-friend is pale for its Path and is the one form the
  colour check still puts elsewhere at some sizes. Faces read as eyes and marks; at a
  thumbnail the lids' angle (which is what makes the three Paths' looks) is two pixels.
- **Every other line on the wolf's rig** (Fox, Stag, the Hawk's three Harriers; the Drake
  has had a body of its own since 2026-11-11, so what is said of it here is the old one):
  one wolf reshaped. Outlines change by proportion, carriage and what is grown; none has a
  skeleton or clips of its own. The Drake is the weakest for it: its legs and chest are a
  wolf's, so the Sky path can read as a winged hound, and its wings do not beat. The
  Harriers read as small griffins, not hawks on foot.
- **Dark on dark.** A night coat on a dark ground: the Imp's
  Night-clerk, Lights-out Imp, Bondsman and Whipping-imp; the Drake's Lamp-hoarder,
  Slag-jaw, Smoke-drake, Chimney-wyrm and Wing-shadow; the Coat's Shadow and Listening
  paths on a black sample coat; bows and the Smoke-pole branch at night.
- **Told apart by what they carry, not by outline.** Coat: the nine of the Listening path
  (Whisper-collar and Warning Tug nearest). Shield: Wall-shield to Battered Shield; the
  Road-shield is plain. Gauntlet: Catching Hand and Iron Palm. Hawk: the eleven of the
  High Circler's path, all on the wing. Sprite and Homunculus: Shoulder-mender, Clay
  Stand-in, Ward-builder, Weather-sprite. Fox: Gone-away, Listening Fox, Snow-pouncer;
  Marsh-light beside Fire-tail. Stag: Tilter, Long Charge, the Watch-hart. Fiend:
  Flare-up, Pyre-dancer and Brush-burner are one imp in three moods; Oath-scorch, Mark of
  the Sworn and Vendetta differ by what they wear. Ember: Kept Fire, Circle-flame,
  Tempering Flame. Bow: Omen-bow, The Twitch, Oath-bow.
- **Reads as something else.** Fog: the Trail-keeper (a caterpillar on a board), the Smother
  (a stack of blankets), the Sea-fret's three streamers (three fingers); and every roll of
  fog has a highlight on it, because `mist` is drawn as water is.
  Hawk: the Passenger's shoulder reads as a draped stand. Sprite: the Collar-rider's face is
  lost between hair and collar. Drake: Kiln-throat's glazed jaw reads as big teeth.
- **A face you cannot see.** The Writ-riddler's second face is at
  the back of the head; Hill-fire has none in view; the Whipping-imp's welts are on its
  back.
- **Small in its cell or in the world.** The Clasp (the Coat's Starter) is the weakest of
  the armors. The Mud-lier and the Bog-lure are low. Flight forms are scaled by their wings.
  The Salvor's ear-trumpet is near the ground.
- **Leaves its Path's look.** Gun: Smoke-pole, Hot Barrel and Tinker's Piece have no wheel.
  Blade: Grave-blade, Heirloom and Night-edge are straight; the Wooden Sword branch is wood,
  point up.
- **No pose of its own.** The small people move by their base body's clips, so what is in a
  hand hangs at the side. A bow is edge-on from in front and behind. A Standing Gun in the
  hand brings its legs, its shield and its walls with it.
- **Floats where it should lie.** Grass-fire floats at the shoulder with its ground, because
  its base floats. The Lurker's and the Fog's floor forms float too, each now with the piece
  of floor it lies on (their section lists them); a Small Shadow carries one flagstone.
- **Light.** The game shows every lit surface at one brightness, so a large lit area glares;
  light is kept to edges and small things except where a form is all light on purpose.


## The Moth (`tools/blender/lines_moth.py`)

In Greek one word, *psyche*, is the soul and the moth. A genius is its partner's soul standing
outside the body, and the game is lamplit: the Moth is the plainest picture of that there is.
Class `creature`, role Lookout, silhouette `beast-moth` (it floats).

**Its anatomy is a moth's, and sound**: a head with two great eyes, a coiled tongue between
two palps and two feelers; a furred thorax that bears six legs and two pairs of wings; an
abdomen in rings. **One thing is a magical choice, made on purpose**: it is the size of an
owl and it floats in the field as a lamp does, so it need not beat its wings to stay up. That
is leaned into: most forms hold the body upright and the wings spread to be read (a wing is
its canvas), a form at rest rests on the air, and the Ghost-moth and the Starter hang by a
thread from a point of the field. The Starter is not a moth yet: a grub in a case of scraps.
The change at the Gate is its coming out.

| Path | Colour | What it keeps down the Path |
|---|---|---|
| **Candle-moth** | `marigold`, no coat shift | small plain wings **barred** the colour of a lamp flame and singed dark at the edge; comb feelers; always a fire near it (a burn alight, a candle, a taper, cracks that light). Its Advancements leave the shape three ways: the Singed Moth (a bite burned out of one wing), the Ermine (white, spotted, a cape and a ruff), the Hover-moth (narrow wings, a tongue out, a fan to steer by) |
| **Emperor** | `amethyst`, coat `slate` | broad round wings with **eye-spots** ringed violet, and great feathered feelers. The Owl-wing (the wings are a face), the Underwing (grey as bark and shut, the violet hidden), the Serpent-wing (hooked tips that are two snakes' heads) |
| **Moon-moth** | `jade`, coat `moon` | pale wings washed green from the body out, a dark green leading edge, long **tails** on the hindwings. The Ghost-moth (white, tailless, hanging), the Long-tail (tails streaming behind), the Plume-moth (wings come apart into quills) |

On every Path the colour is in the same three places: the pattern of the wings, the vanes of
the feelers and the rings of the abdomen.

A `body` on the Moth's line:

| Key | What it is | Styles |
|---|---|---|
| `kind` | | `grub` (the Starter: `case`, `eyes`) · `moth` |
| `build` | against its stage's own | `span` (the wings) `body` `head` |
| `pitch` | degrees the body is raised from level: 0 flies flat, 90 stands upright with its wings spread to be read | |
| `wings` | their shape, `[shape, size]` | `delta` `ragged` `tiger` `swept` · `broad` `owl` `four` `lintel` `under` `wall` `atlas` `long` · `tailed` `narrow` `psyche` `chart` · `quills` `fans` (made of plumes) |
| `hold` | how they are held | `v` `flat` `spread` `cross` `tent` `shut` `cape` `back` `high` `flash` `press` `offer` (one held up) `droop` `hang` `swept` `dart` `tee` `fan` |
| `flap` | | `beat` `glide` `still` |
| `pattern` | what is painted on them, a list, laid in order | `bars` `singe` `neat` `hem` `ash` `cracks` `holes` `ermine` `tiger` `skull` (on its back) · `rings` `eyes` `owl` `eyes4` `ward` `bark` `peek` `flash` `wall` `snake` `windows` `worn` · `moon` `costa` `white` `edge` `frame` `likeness` `streak` `compass` `ink` `ruled` `chart` |
| `burn` | a bite burned out of a forewing, `[side, size]` | `l` `r` |
| `tails` | of the hindwings, `[style, length]` | `twist` `stream` `burn` |
| `feelers` | | `comb` `feather` `thread` `club` |
| `eyes` | | `big` `small` `far` (ringed in brass) |
| `brow` | how it looks at you | `keen` `stern` `calm` `wide` |
| `look` | where its head is turned | `back` (over its shoulder) |
| `fur` | the thorax | `plain` `mane` `ermine` `ghost` `ash` |
| `abdomen` | | `stout` `slim` `banded` `bee` `fan` |
| `tongue` | | (coiled) `out` `deep` (a watch-spring) |
| `legs` | | `long` |
| `carry` | | `taper` `snuffers` `comb` `dividers` `star` `train` |
| `perch` | what it sits over, and brings with it | `lamp` (a candle in a dish) `log` (a twig) |
| `aura` | | `dust` `embers` `rings` `halo` `sway` (the whole of it hangs by a thread) |
| `accent`, `coat` | its Path's colour; how it wears its partner's coat | |

**How it is built.** No rig. A wing is a sheet in a grid of cells (along it and across it),
each cell a material, so a bar follows the wing's own curve, a margin is the last row and a
hole or a window is cells left out; an eye-spot is a stack of discs laid on the sheet, seen
from both faces. The partner's coat is the look's three roles: `fur_dark` (forewings),
`fur_light` (hindwings, face, abdomen), `fur_ruff` (thorax, crown, wing roots); the look's two
marks are `collar` and `bands`. A model carries **one** wing, one feeler, one eye and one tail:
the other of each pair is the same mesh on a mirrored piece (`twin`), which halves a model
(60 to 100 KB a form).

**What moves.** Every form: the head turns (`turn_head`, and what is on it turns with it), the
eyes blink (`blink_eye_l`, `_r`), the feelers sway (`sway_feeler_l`, `_r`), the abdomen
breathes (`pulse_abdomen`). Wings `beat` or `glide` about their roots unless the form holds
them still. Tails and the Lych-moth's train are chains that `wave`; a tongue held out sways;
a flame `flick`s; dust and a halo `bob`; the Lodestar's star and the Flash-wing's rings
`pulse`; the Starter and the Ghost-moth sway whole from the top of their thread
(`sway_grub`, `sway_hang`). A pair of wings is named by number, `beat_wing_0` and
`beat_wing_1`, not by side: the second is a mirrored twin, the game gives both the same turn,
and the mirror makes it the other side's. Where the two sides differ (a burn, a wing held up)
both are made, and named `_l` and `_r`.

**Its gifts** (`python tools/blender/lines_moth.py gifts`): `moth-dust-wings`, two broad
wings held up from the back with an eye on each, which beat; and `moth-antennae`, two great
feathered feelers on the head, which sway. Both take the colour of the Path of whatever wears
them. `python tools/blender/lines_moth.py body` makes `bodies/beast-moth.glb`, the moth with
no Path's colour on it.

**What is still weak.** The Starter is small and its case reads as a banded cocoon before it
reads as scraps. The Honey-thief's skull is on its back and is not in its portrait. A form
that flies level (the Hover-moth, the Long-tail, the Comet-moth) shows its wings edge-on from
in front and is small in its cell for its tails. The Underwing's bark is seen from behind and
above, not from in front. Cells are a tenth of a wing across, so a pattern finer than that
(the Chart-moth's coast, the Bark-sitter's bricks) is drawn in lines laid on the sheet, and a
hole is square-cornered. Wings that are held upright and `beat` turn in their own plane
(the game beats a wing about the way the body faces): it reads as a slow fanning, and a true
flap about the body's own length would want a kind of its own.

## The Carp (`tools/blender/lines_carp.py`)

A fish that swims in the air at its partner's shoulder: the one who goes up against the
current as a matter of course. **Its anatomy is a magical choice, made on purpose and
carried all the way: the field is its water.** It hangs a little across the way it faces, as
a fish holds station in a current. It has a carp's parts in a carp's places (one fin down
the back, a pair at the shoulder, a pair and a single one under the belly, the tail;
gill-covers that breathe; barbels at the corners of a thick-lipped mouth that opens forward
and down) and nothing for the ground: no legs, no perch. What it has about it is what a fish
in water has about it: spray, a wave at its head, fry, weed, ice. One thing on it is not a
fish's: it has lids, and it blinks. It is a soul.

The Weir-leaper's climb ends at the edge of a dragon, as the old story of the carp and the
gate has it, and that is on purpose too. The Horn-bud is a carp with two buds of new antler.
Past-the-Gate is a carp's head, and a carp's round mild eye, on a body grown long: antlers,
a mane down its neck, a saw of fin down its back, four fins held like limbs, whiskers that
stream back along it, and a pearl of the field under its chin.

**How it is built.** A carp is a spine with a skin about it. The spine is a `pose` (how it
turns from nose to tail); the skin is sixteen points round it at each of twenty stations,
its girth by its `shape`. The skin is laid in scales, a diamond about every other point,
the front half of each the coat and the rear half the coat's trim, so the rows show; a mark
colours whole scales in two steps of the Path's colour. The body is cut behind the gills and
behind the belly, and each piece reaches a little way inside the one before it, narrower,
like the joints of a lobster's tail, so no gap opens where it bends. It is not rigged, and a
form is under 120 KB.

| Key | What it is | Styles |
|---|---|---|
| `build` | proportions | `len` (metres of the model, nose to the root of the tail) `depth` `width` `head` `eye` (each a multiple of 1); `size` (how large the game stands it: a Path's carp of size 1 is 0.7 m long) |
| `shape` | what kind of fish | `carp` `slim` `bull` (a blunt head, heavy shoulders) `flat` (a flat head: a fish of the bottom) `tench` `round` (a float) `long` (a dragon's) |
| `pose` | how it holds itself, and half of what makes each form a different outline | `level` `bow` `climb` `rear` `rise` `dart` `bank` `broadside` `turn` `sway` `hang` `burst` `present` (a bow, the crown shown) `nose-down` `arch` `thrash` `lean` `crescent` `curl` `dragon` |
| `tail` | | `fan` `fork` `scythe` `veil` `paddle` `eel` `banner` `closed` `ragged` `foam` |
| `dorsal` | the fin of the back | `sail` `low` `round` `veil` `folded` `ragged` `foam` `mane` `ridge` `spines` `dragon` (a mane on the neck, a ridge behind) `none` |
| `fins` | the fins of the shoulder (the belly's follow them) | `paddle` `fan` `swept` `veil` `shelter` `foam` `folded` `wing` `claw` |
| `finmark` | how the Path marks every fin | `rays` (every other ray the colour) `roots` (pale, the colour at the root: a koi's) `edge` (dark, lit along the margin) `plain` |
| `barbels` | | `none` `short` `long` `feelers` (two pair, out in front) `plumb` (straight down) `lash` `white` `dragon` |
| `mouth` | | `lips` `gape` (round and open, turned up to a hand) `wide` (a slit across a flat head) `ring` (a ring of the field held in it) |
| `eyes`, `brow` | the eye, and the lid over it: what it is thinking | eyes `round` `old` `up` `top` `small`; brow `keen` `calm` `mild` `heavy` `stern` `sleepy` |
| `scales` | | `net` `coin` (large, on the shoulder) `small` `armour` `plates` (a belly in bands) `none` |
| `marks` | the Path's colour on the skin | `stripe` `bands` `dash` `shoulder` · `patches` `saddle` `mask` `collar` `lips` `faded` `brocade` · `back` `spots` `sheen` `worn` (the field shows through) · on the fins `tips` `wingbars` |
| `head` | what the head has grown | `buds` `antlers` `prow` (a ship's stem of stone) `cap` (the crane's red crown) |
| `carry` | what it has about it | `scuff` `spray` `eddy` `wake` `fry` · `weed` `seal` `rime` `pane` `shards` `drops` · `tremor` `stone` `rod` `shiplamp` `barnacles` `chain` `coin` `mudball` · `pearl` |

**What each Path keeps.** The **Weir-leaper** (`jade`) wears its colour as a stripe down the
spine and in the rays of every fin; its body is bent or climbing, its whiskers lengthen with
every stage, and the fin of its back turns from a sail to a ridge, a mane, a row of spines.
The **Still-water Carp** (`madder`, a coat gone to `frost`) is a koi: a deep pale body, the
colour in patches on the skin and at the root of every fin, which are otherwise pale. The **Silt-reader** (`amethyst`, a coat gone to `slate`) is a
fish of the bottom: a flat head, small eyes under heavy lids, long feelers, the colour dark
over the whole back and bright along the margin of every fin.

**Its light.** The eyes; from the Advancement, the line down each side by which a fish feels
the current, which is a face of the skin itself; and a Final has one thing more that is its
own (the pearl, the ring it carries, the ship's lamp, the coin of sky, the eyes of its fry,
the worn places on the Salve-carp's sides, the rings from the Ground-shaker's tail).

**What moves.** `wag_body_0` and `_1` and the tail `wag_body_2` (a dragon has one piece more),
each the child of the one before, so that it swims where it hangs; `glide_fin_l` and `_r`,
the fins of the shoulder; `pulse_gill_l` and `_r`; `blink_eye_l` and `_r`; `sway_barbel_l`
and `_r` (and `sway_barbel2_*`); and of what it carries, `bob_fry_0` to `_2`, `bob_pearl`,
`bob_coin`, `pulse_ring`, `pulse_tremor`, `sway_rod`, `sway_seal`, `sway_weed_<n>`,
`sway_chain`.

**Where it hangs.** The game holds a genius that floats by its origin, at its partner's
shoulder. A carp is made with its belly at its origin and the middle of everything it is over
it, so it swims at the shoulder at every stage; what hangs from it (plumb whiskers, a chain)
hangs below, by no more than 0.3 m. `ref_top` is not the crown of its head: it is set from
`size` so that the game stands the fish at the length it should be.

**Its gifts** (`python tools/blender/lines_carp.py gifts`): `carp-fins`, a swept sail of a fin
down the back, and `carp-tail`, a forked tail on a scaled stem; both rayed in the wearer's own
Path's colour.

**What is still weak.** The sheet measures a body at one moment and pictures it at another,
and a carp swims between the two: a long form's tail may touch the edge of its cell, and the
Fingerling (the smallest, in the first column, which the sheet's measure favours least) is
small in its. The Fingerling is 0.4 m long, not the length of a finger: smaller, the ink line
is most of it. Whiskers are thin, and at a distance the ink makes dark lines of them. The
Skimmer's wings are flat, so it is posed banking; level, from in front, they are edge-on. The
wave at the Shoal-head's head can read as a hoop. A great carp's mantle of light stands off
its back: the game sets it by height, and a fish is long and low. Its face is its lids: the
eyes do not turn to look at anything. The game's grain lays round scales on the fins as on the body (a fin is the coat's trim, and is named for it). By colour the Under-the-Ice reads as a Silt-reader: its floe is the largest thing in its picture, and it is slate.
## The Demon (`tools/blender/lines_demon.py`, `demon_dress.py`, `demon_gifts.py`)

## The Angel (`tools/blender/lines_angel.py`)

> "Add three more: one angel line, one demon line, and one line specifically for elementals
> with a humanoid form like tiny demigods." (owner, 2026-11-11)

A prince in exile: the soul of one who will not be told, and would rather be wrong on their
own account than right on another's. It is not evil; it is pride, appetite and refusal, and
it is loyal to its partner and to no one else. It is neither of the game's two small devils:
the Fiend is a flame (it feels everything) and the Imp a clerk (it keeps count). The Demon is
a small horned person with a straight back. Class `monster`; beside its partner it is a
**hunter**; silhouette `daemon-prince` (it walks; the coat is the `drake` palette's, so its
hide is its partner's verdigris, rust, slate, soot, sand or plum).

**Its anatomy, in a sentence.** A person in the trunk, the arms and the face; **a goat's legs
made of the person's own and nothing else**: the thigh brought forward, the shin back, the
foot stood on its toes and drawn out long, so that the hock is its heel and the cloven hoof
its toe, and the rig's hip, knee, ankle and toe bones are exactly where that leg bends
(`goat_legs`; `build.hock`, 0 a person's to 1 a goat's); horns from the brow; a tail that
carries on the spine; and wings of skin rooted at the shoulder blades, which is the one
magical choice (six limbs), made on purpose and worn by every form.

**What carries down the whole line:** horns (its crown and its outline: a different pair at
every one of the thirty-one forms), hooves, a tail, eyes of the field with a goat's level
pupil, and **wings whose skin is its Path's colour**, worn as that Path wears them.

| Path | Colour, coat | What it keeps | Its wings | Its face |
|---|---|---|---|---|
| **Exile** (the one who left) | `amethyst`, coat `moon` | a straight back, a black doublet, the crown that broke | a short cloak over its shoulders; a collar; spread, on the branch that left by the window | hooded eyes, level brows |
| **Advocate** (the one who can make the case) | `gold`, the partner's own coat | a cut-away coat, a gold waistcoat and cuffs, a white cravat, gilt hooves, a small beard | the tails of its coat | one brow up, a smile on one side |
| **Head-down** (the one who settles it by being larger) | `madder`, coat `russet` | bulk, a goat's shag to the hock, a kilt of straps, paint on its hide, tusks | stubs that never grew | narrowed eyes, brows down |

The Advancements, by their great part: Pretender (lyre horns, the crown mended, a staff),
Door-keeper (the door it left by, on its back; one horn broken on the lintel; the key),
Fly-by-night (wings half open); Fair Offer (a light in its hand), Both Sides (a face behind,
one horn forward and one back, a coat of two halves, one wing a tail and one a cape), Good
Company (curled banded horns, a cane, its tails held out); Gate-ram (a ram's curl), Strong Arm
(hands the size of its head, no wings), Sharp-set (lean, a stag's horns, a whip of a tail).
The Finals grow strange on purpose: Court of One (a ring of seven horns for a crown, the back
of a throne strapped on), Stiff-neck (no head: a crown of flame with eyes in it), Door Left
Ajar (the field's light through the gap), Bolted Door (the door on its arm), Long Way Round,
Moonless (its wings a cloak, going to smoke), Gilded Hand, Second Helping (a second mouth
across its belly), Full Bench (mouths in the air, horns rolled like a wig), Last Word (a mouth
behind), Master of Revels, Honest Enemy (a half-mask, a tail like a sword), Wall-goer (the
horns met in one boss), Gate-crasher (half a gate hanging from a horn), Arms Folded (four
arms, two of them folded), Yoke-breaker, Horn-wreath, Never Full.

**How it is built.** On the small people's kit (`lines_people.Person`, loaded when the first
form is built and not changed), so a garment is cut from its own skin and sits as the skin
sits. Its knees come forward, so nothing it wears is a closed skirt: a doublet's short stiff
skirt, a kilt of straps that lie out over the thighs, a gown open down the front; and its
long garments are its own wings. A slot holds a style, `[style, size]`, `[style, size,
word]`, or a list; a style the Demon has not is looked for among the small people's.

| Key | What it is | Styles (and words) |
|---|---|---|
| `build` | the small people's, and `hock` (how far its legs are a goat's), `muscle` (0 to 1), `faces` (the share of its stage's faces the body keeps) | |
| `horns` | | `buds` `prongs` `lyre` `spires` `swept` `back` `antelope` `crescent` `hooks` `stubs` `wide` `rapier` `forward` `great-bull` `low` `ox` `spiral` `curled` `ram` `wig` `stag`; `single` (one whole, one stump) `broken` `both-ways` `mono` `ring` (a crown of seven) `four` `double` `boss` `wreath`; words `gilt` `banded` `iron` `ember` `gate` |
| `crown` | | `broken` `mended` `iron` `wreath` (leaves from horn to horn) `flame` (no head: a crown of fire) |
| `eyes`, `brow`, `mouth` | each Path a temperament | eyes `lit` `big` `wide` `hooded` `narrow` `far`; brow `level` `proud` `wry` `fierce` `glad` `calm` `sad`; mouth `set` `smile` `grin` `tusks` `fangs` `open` `grin-tusks` |
| `face`, `hair` | | `goatee` `half-mask` `nose-ring` `back-face` `back-mouth`; hair `slick` `long` `mane` |
| `wings` | in its Path's colour | `buds` `cape` (`split` `trimmed`) `high` `half` `spread` (`barred`) `cloak` `tails` (`lined` `parti` `odd`) `fan` `stubs` |
| `tail` | | `tuft` `spade` `curl` `whip` `barb` `bull` `smoke` `flame`; words `wag` `spade` `tuft` |
| `legs` | hooves always | `bare` `shag` `gaiters` `wraps` `smoke`; word `gilt` |
| `wear` | | `loincloth` `breeches` `shirt` `doublet` `waistcoat` (`striped` `open`) `tailcoat` (`parti`) `gown` (`bell`) `cravat` (`napkin`) `bands` `cuffs` `glove` `bracers` (`iron`) `belt` `belt-wide` `sash` `collar-fur` `ruff` `scarf-long` `harness` `door-straps` `pauldron` `pauldrons-stone` `war-kilt` `paint` |
| `skin`, `arms` | | `stone-dust` `ribs`; arms `gilded` `four` `smoke` |
| `back`, `chest`, `belt` | | `door` (`shut` `ajar`) `throne` `spines`; `order` `chain-of-office` `flower` `belly-mouth` `yoke`; `key` `crown` |
| `right`, `left`, `around` | | `coin-light` `cup` `cane` `door-shield`; `mouths` `smoke-edges` |
| `coat`, `accent` | as every line's | |

**What moves.** Every form blinks (`blink_eye_l/_r`: the eye is a piece of its own riding the
head bone; the lids are the face's). Its wings mantle (`glide_wing_l/_r`; the Princeling's
buds `beat_`), its tail sways (`sway_tail`; the Princeling's wags), and by form: the flames of
a crown and a tail `flick_`, a key, a chain, a wreath, a scarf and half a gate `sway_`, mouths
and embers `bob_`. `Demon.rider` makes a moving piece that rides any bone.

**Its gifts** (`python tools/blender/lines_demon.py gifts`): `demon-horns` (two long ringed
horns standing through a crown that has lost a third of itself) and `demon-wings` (skin on
long fingers, a claw at each wrist, that mantle). The adjective is Unbowed.
`python tools/blender/lines_demon.py body` builds `bodies/daemon-prince.glb`, the
Princeling's own body with the rig's three clips left in it, which the forms borrow.

**What is still weak.**
- **The face at a distance.** The eyes read; the brows and mouth are a few pixels at fifteen
  metres, and on a dark coat (soot, plum) the unshifted Advocate's face is dark.
- **Rigid on a moving body.** Kilts, gowns, doors and the throne ride one bone; in a run the
  thighs come through a kilt's front straps. Wings worn as a cape cover the upper arm only
  while the arms hang (they do in all three clips).
- **It walks, always.** The Fly-by-night branch has wings that could carry it, and no
  floating silhouette was registered for it (a humanoid that hovers still plays its walk).
- **No chains on a rigged body.** The game takes each piece that rides a bone in as a bone
  of its own and moves that piece alone, so a `wave_`/`wag_` chain (`_<n>`) does not carry
  its next piece: a tail here is one piece, and a tail's flame keeps the tail still.
- **Seen from in front, a pair is one.** The Pretender's collar of wings and the Advocate's
  tails are mostly one shape from the sheet's angle; the Advocate's nine differ by what they
  carry and their horns more than by their build.
- The walk is the rig's own, fitted to a goat's leg: honest in its joints, not yet a trot.
## The Elemental (`tools/blender/lines_elemental.py`)

> "one line specifically for elementals with a humanoid form like tiny demigods" (owner, 2026-11-11)

The elements as people: the soul of one who is more a place or a weather than a person.
Each form is a small god of something, a forearm tall (its silhouette, `aspect-demigod`,
has `artSize` 0.5: it stays small even grown). The Ember is a fire that is not a person and
the Fog a weather that is not a person; this is the hill, the tide and the storm with a
face and hands.

**Its anatomy**, in a sentence: a grown human figure at a small size, sound as a person
(the small people's body on the people's bones, grounded proportions: a youth at the
Starter, heroic at the Final), and one magical choice carried all the way: it does not
stand on the world's ground but brings its own (a slab, a wave, a cloud) and floats on it;
its hair, its mantle and its crown are the element itself, and its flesh is its partner's
coat as stone. Two Finals leave the person on purpose: the Spring Tide is a figure to the
waist in a wave taller than itself, and the Tempest is a turning storm with a face
(`shape`: `storm`, no rig).

What each Path keeps, down all ten of its forms:

| Path | Its colour | Its coat | What it is at a glance |
|---|---|---|---|
| Cornerstone (Earth) | `gold`: ore in its seams, its sash and kilt, lichen, leaves, lava | `sand` | broad, heavy in the limb, planted on a slab of its own ground; a stone of the field breathing in its chest; level brows |
| Tideling (Sea) | `peacock`: its hair that is water, the band on its chest, fins, its wave | `frost` | a long pale woman's figure, weight on one hip, rising out of water; a soft mouth |
| Squall (Sky) | `amethyst`: hair and scarf streaming sideways, its cloak | `storm` | slight, windswept, on a cloud; brows up at the outer end, a crooked mouth |

Its nine Advancements are nine small gods, each a different carriage and great part: of
Earth the Tor (fists on hips, a crown of basalt columns, slates on its shoulders), the Loam
(hands held out, leaves for hair, roots under its slab) and the Smoulder (seated, cracked,
a flame for hair); of Sea the Meander (in mid-step, a stole that loops out like a river),
the Floe (stiff on a raft of ice, a crown of shards) and the Fathom (hanging as in deep
water, weed standing up for hair); of Sky the Gale (laid along the wind, a cloak that never
hangs), the Thunderhead (hands behind its back under an anvil of cloud) and the Daybreak
(arms flung up before a rising disc). A sun in the Sky path is `accent2` (`rose` at
daybreak, `bone` at noon, `madder` at sundown), so the Path's own colour is still its
hair and its cloak.

The look's roles are `stone_flesh` (main), `cloth_wrap` (under) and `stone_band` (trim), on
the `stone` palette: its flesh, its wrap and its belt are its partner's coat. Everything
else is its own and does not shift (`OWN` in the file: basalt, slag, loam, moss, straw,
water, ice, cloud). Two coat shifts are its own: `sand` and `storm`. The Starter wears `ash`
so that it is a pale statue whatever its partner's coat.

| Key | What it is | Styles |
|---|---|---|
| `figure` | | `woman` (the Sea's) |
| `build` | the small people's proportions, and two of its own | `muscle` `weight` (0 to 1) |
| `stance` | how it holds itself (below) | `attend` `folded` `planted` `column` `seated` `offer` `carry` `guard` `shoulder` `wrath` `flow` `stroll` `pole` `open` `stiff` `stride` `drift` `hang` `yoke` `lean` `fly` `blow` `brood` `throw` `greet` `hieratic` `knee-up` |
| `flesh` | marks on the body itself | `seams` `cracks` `slag-limbs` `earth-legs` `lava` `glow-hands` `fins` `rime` `deep-limbs` `ribs` `barnacles` `storm-shoulders` |
| `hair` | the element, as hair | `wisps` `crystals` `leaves` `flame` `water` `weed` `wind` (`forward`) `rays` `spikes` |
| `crown` | | `columns` `peak` `wheat` `crater` `shards` `lure` `anvil` |
| `wear` | | `wrap` `band` `sash` `kilt` `mantle` (`stones` `moss`) `apron` `bracers` `pauldrons` `stole` `scarf` `cloak` (`wind` `ice` `dusk`) `menhir` |
| `under` | what it stands on or rises from | `slab` (`tor` `ridge` `roots` `magma`) `cone` `wave` (`deep`) `surge` `boat` `floe` `berg` `cloud` (`storm` `bank`) |
| `right` `left` `both` | what it holds | `hammer` `sickle` `bolt`; `sheaf`; `pole` `anchor` `sail` |
| `chest` `belt` `back` | | `heart` `flower`; `line`; `briars` `disc` (`low` `high` `sunk`) |
| `around` | what keeps it company | `cloudlet` `stones` `embers` `sparks` `fish` `bubbles` `streams` `breath` |
| `face` | its temperament: brows and a mouth | `steady` `old` `stern` `soft` `keen`; `beard` |
| `eyes` | pale, the field in the iris; each shuts | `lit` `dark` |

Three things this line had to learn, which hold for any line of people:

- **A stance.** A form with no clip of its own could only stand as its base body's Idle
  stood, with whatever it held hanging at its side. Here each form is posed (`STANCES`: a
  limb is aimed along a direction, or its wrist or ankle brought to a point with the elbow
  or knee toward a hint) and the pose is baked into the model's rest, less what the
  borrowed clip will add: the game gives a form its base body's clip as a turn from rest,
  so in the game it holds its pose and still breathes. What it holds in two hands rides its
  chest, and the hands are brought to it. The base's own body carries only the Idle clip,
  so an Elemental glides as it stands and does not pedal the air.
- **What it stands on is made where it sits.** A stance says how high its lowest part is
  (`seat`), and its slab or cloud is made there and rides the root, so a seated god sits on
  its slab.
- **A dark mass shines.** The style's highlight is the same on a black surface as on a pale
  one, so a large dark thing (the Caldera's cone, a storm cloud) shows a pale sheen in the
  lamp. It is kept smooth so that the sheen is one soft shape and not a facet.

**What moves**: its eyes shut (`blink_eye_l`, `blink_eye_r`, each riding the head); hair
that is water or weed or leaves sways and hair that is wind glides (`sway_hair`,
`glide_hair_l`); a flame and a held stroke of lightning gutter (`flick_`); the stone in an
Earth form's chest, a cloud under a Sky form's feet and an anvil of cloud breathe
(`pulse_`); the curl of a wave, a ring of stones, embers, sparks or fish and the rays of a
sun turn (`spin_`); a sash, a cloak, a stole, a chain, roots and a ferry's lantern hang and
sway (`sway_`); a scarf glides; the Starter's wisp of cloud bobs. The Tempest's bands of
cloud turn each against the next.

**Its gifts** (`python tools/blender/lines_elemental.py gifts`): a crown nobody gave it
(`elemental-crown`: a ring of basalt columns that stands off the head, a flame of the field
in it, three small stones going round) and a small weather of its own
(`elemental-small-weather`, a new feature: a fist of cloud over the head that rains the
field's light and lets go a stroke; `featureSockets` puts it on the head's socket, above
the crown).

Still weak: the face is the size of a fingernail on a figure a forearm tall, and at the
size of a sheet's cell it is two lights and a brow; the Starter is the smallest thing on any
sheet and is drawn smaller than its cell allows; the waves are a bowl with a curl, not yet
water; the Berg's block and the Longstone's stone are plain; a figure sitting cross-legged
is crude at the hip where the wrap does not cover it; the Sundown is
the one the line check reads as another Path by colour (a red sun); a great or apex
Elemental is lit from inside by the light the game puts under the great, which sits at its
waist, not its feet.
The soul of one who answers to something larger than themselves, and is hard to live with
for it: the picture of conscience. A companion, a Keeper, and it floats. It belongs to this
world and to no church: its halo is the field's light, so it is the colour of its partner's
Shape, and that is the one thing of it that is its partner's and not its own.

**Its anatomy** is a magical choice, made on purpose and carried all the way: a small
person (an adult, a forearm tall; a child only as the Starter) whose wings are rooted
between the shoulder blades as a third pair of limbs, each with its own shoulder, elbow and
wrist and three ranks of feathers on them (the long feathers, the coverts over their roots,
the lesser coverts over those). It does not walk: its robe falls past its feet, and what it
carries may hang lower than it stands. Four Finals stop being people, as the old pictures
of such things did: two hands, a horn, a pair of scales, a wheel of eyes.

It is built on the small people's kit (`lines_people.Person`, on the people's bones, moved
by the three clips of `bodies/kith-angel.glb`), with what that kit has not got written
here: wings, a halo, a face made to be read small, pieces the game moves, and a way to stand
a form otherwise than at ease.

| Path | What it is at a glance, and what never changes down it | Colour | Coat |
|---|---|---|---|
| **Shoulder-angel** (the one who has chosen whose side they are on) | sturdy, level-browed, its mouth shut; its wings held *round* things (mantled, closed like doors, braced, borne as pillars); a sash of its colour at the waist and its colour on the **coverts** of the wing | `gold` | its partner's own, unshifted: it wears your colours as they are |
| **Clarion** (the one who brings the word whether or not it is wanted) | slight, brows up, mouth open; its wings *raised* (swept up, fanned like a sunrise, long and narrow); a herald's tabard of its colour with a pale disc on the breast, and its colour on the **tips** of the long feathers | `rose` | `moon`: bleached toward morning |
| **Weigher** (the one who believes in what is deserved) | tall and narrow in a gown with a train and a standing collar, brows drawn down, mouth a line; its wings *composed* (folded like a gown, half open and still, held level as a rule); a stole of its colour with pale ends, and its colour in **bars** across the long feathers; a halo that stands upright behind the head | `lapis` | `iron`: a judge's dark |

An Advancement takes its own step of its Path's colour on the wing (`marks`: the zone, then
`accent`, `accent_light` or `accent_dark`), and a new thing in its hands or on its back.

The body's keys (a slot holds a style, `[style, size]`, or a list of them):

| Key | What it is | Styles |
|---|---|---|
| `build` | the small people's proportions, against its stage's own | as theirs; and `small` (how tall it stands against its stage: the Quiet Word is 0.74) |
| `hair` | | `down` (the fledgling's) `cropped` `swept` `curls` `bound` `long` `bare` |
| `eyes` | each eye its own piece, which blinks | `open` `wide` `lowered` `shut` `light` |
| `brows` | the temperament | `level` `raised` `stern` `soft` |
| `mouth` | | `closed` `small` `open` `line` |
| `face` | what is over the face, or in place of it | `blindfold` `band-up` `light` (a light in a cowl) `lamp` (a lamp where the head was) |
| `halo` | the field's light | `slipped` (too big, and over one eye) `ring` `tilted` `plate` (upright behind the head) `rayed` `coin` `hung` |
| `wings` | pairs, the upper first: `[pose, size, make]` | makes: `down` `feather` `steel` `blades` `paper` `light` `eyed`. Poses (`POSES`): `stubs` `nubs` `raised` `half` `spread` `wide` `level` `folded` `low` `braced` `planted` `pillars` `closed` `over-face` `over-feet` `display` `sunrise` `sunrise-low` `rise` `fall` `signal-up` `signal-down` `swift` `cupped` `pages`; and four that are not the same on both sides: `mantled` `uneven` `whisper` `plucked` |
| `marks` | where its Path's colour lies on the wing, and which step | `[coverts \| tips \| bars \| edge, accent \| accent_light \| accent_dark]` |
| `robe` | its partner's coat | `smock` `tunic` `robe` `gown` `wound` (its own scroll, wound round it) |
| `over` | what is worn over it; where its Path's colour is on the body | `sash` `hem` `tabard` `stole` `cord` `collar` `baldric` `case` `cowl` `pauldrons` `bracers` `gorget` |
| `right`, `left` | what is in each hand | `buckler` `lamp-staff` `trumpet` `great-horn` `scroll` `quill` `scales` `pan` `sword-down` `sword-up` |
| `belt`, `bears` | | `sword-bound`; `arch` (on its two raised wings) `yoke` (the beam of its scales, across its shoulders) |
| `pose` | how it stands otherwise than at ease (`STANCES`) | `hand-up` |
| `shape` | a Final that is no longer a person | `hands` `horn` `beam` `wheel` |
| `coat` | how its partner's coat is worn | the shifts in `data/genius-looks.json` |

A wing's pose is data too (`POSES`): the bones of its arm, which part of the arm carries
the long feathers, the way they point at the shoulder and at the tip, how long they are, how
far the wing is swung back or forward. A new pose is one line.

Three things this line had to learn:

- **The game inks every piece that stands clear of another**, and on a face a few pixels
  across that is the whole face: an eyeball that stands proud of its lids is drawn as a
  pair of spectacles. So the pieces of a face lie *in* the skin (an eye within its lids, a
  brow and a mouth with their middles on the surface), and then they take no ink.
- **A form can stand otherwise than its kind stands** though it has no clips of its own.
  The game moves it as far from its rest as the idle is from the base body's rest; so the
  rest is made the one which, moved so, comes to the pose wanted (`Angel.repose`). The
  Forewarner and Be-not-afraid hold one hand up, palm out, and still breathe and walk.
- **The field's light is its partner's Shape colour, and a Shape may be gold or blue or
  rose.** So a Path's colour has to cover enough of a form to outvote the halo: a tenth of
  it is too little on a body this white.

**What moves**: every wing (`glide_wing_l/r`; the Starter's `beat`; a second and third pair
`wing2`, `wing3`), each eye (`blink_eye_l/r`), the halo (`bob_`, `sway_` where it has
slipped or hangs, `spin_` where it has rays, `pulse_` where it stands upright), and what
hangs: `sway_sash`, `sway_cord`, `sway_pennon`, `sway_lamp`, `sway_scales`, `sway_pan`,
`sway_scroll`, `sway_band` (a blindfold's ends), `sway_knot`. The Beacon's lamp `pulse_`s
and its flame `flick_`s; the light that is Be-not-afraid's face `pulse_`s. Of the four that
are not people: the Upholding Hands `bob_`, their halo `spin_`s; the Unblown Horn's throat
`pulse_`s and its pennon `sway_`s; the Level Beam's beam `sway_`s with its pans hung from it;
the Eye-wheel's two rings `spin_` against each other. The Arch-bearer's wings do not move:
they bear a load. Six forms do not blink, on purpose: the Covert (its face is under its
wings), the Unsleeping (its own eyes are the only ones that are ever shut), the Beacon and
Be-not-afraid (a lamp, a light), and the horn, the scales and the hands, which have no
eyes; the Eye-wheel's never rest.

**What it gives a hybrid** (`python tools/blender/lines_angel.py gifts`): its halo
(`gifts/angel-halo.glb`: a rayed ring of the field over the head, which bobs) and its wings
(`gifts/angel-wings.glb`: white, raised, their coverts in the wearer's own Path's colour,
which glide). `halo` is a feature of this base's own.

**What is still weak**: the faces are right in kind and small in fact: at the size of a
sheet's cell a temperament is two dots and a line, and it is the wings and the stance that
say who this is. The raised hand of the Forewarner is seen against its own white wing. The
robe is one stiff skirt on the hips, as every small person's is: it does not swing. The
Makeweight's bare wing and the Reprieve's bound sword are small things on large forms.
Hands at ease are the kit's half-closed hands; only the two that hold a hand up were stood
otherwise, and nothing may sway from a hand that has been.
