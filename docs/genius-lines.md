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
| All twenty-two | all thirty-one each: 682 models, one a form |
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
| Astrolabe | Sighting-glass `peacock` · Orrery `lapis` · Almanac `madder` |
| Bell | Rally-bell `marigold` · Hour-bell `lapis` · Alarm-bell `madder` |
| Blade | Duelling Blade `lapis` · Cleaver `madder` · Scored Blade `gold` |
| Bow | Hunting Bow `jade` · War Bow `madder` · Singing Bow `amethyst` |
| Coat | Travelling Coat `marigold` · Shadow-coat `amethyst` · Listening Coat `peacock` |
| Drake | Hoard-drake `gold` · Fire-drake `madder` · Sky-drake `lapis` |
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
line, in a sentence. The known cases: the Drake (a hound with wings: it is to be a true
drake, long in the neck and the tail, low and splayed, its wings rooted at the shoulder and
beating); the Hawk's Harriers (griffins by accident: to be griffins on purpose, or birds
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
| Drake | `horns` `frill` `ridge` `wings` `belly` `throat` `tailend` `shell` `jaw` `breath` `nostrils` `claws` `eye` | wings are fixed at the shoulder and do not beat |

What each Path keeps: of the Fox, the Gone-away is lean and looks elsewhere, the Cache-fox
is hearth-brown with something in its mouth, the Fire-tail carries its tail high with a
light at the tip; of the Stag, the Tilter has a plated brow and its head down, the
Wood-walker a red hide and branch antlers with moss, the Watch-hart one ear turned and its
head over its shoulder; of the Drake, the Hoard is low and long and plated in brass, the
Fire blood-red with a row of flame down its back, the Sky taller on the leg with its wings
up.

The look's roles are kept, so the partner's coat goes on: `fur_dark` and `fur_light` on the
Fox and the Drake (whose ridge, wings and tail-tip are its markings), `hide_red` and
`fur_cream` on the Stag. Two coat shifts are theirs: `russet` and `brass`.

**Their gifts** (`python tools/blender/lines_wolfkin.py gifts`): the Fox's brush and its
foxfire (`fox-tail`, `fox-glow`), the Stag's crown and its long legs (`stag-horn-brow`,
`stag-long-legs`), the Drake's horns and its tail (`drake-horns`, `drake-tail`).

## What is still weak

Said by whoever built each family, after looking at its sheets. None of these fails a check;
each is a form or a habit of the build that does not yet meet the rule at the top of this
page.

- **Every line on the wolf's rig** (Wolf, Fox, Stag, Drake, the Hawk's three Harriers):
  one wolf reshaped. Outlines change by proportion, carriage and what is grown; none has a
  skeleton or clips of its own. The Drake is the weakest for it: its legs and chest are a
  wolf's, so the Sky path can read as a winged hound, and its wings do not beat. The
  Harriers read as small griffins, not hawks on foot.
- **Dark on dark.** A night coat on a dark ground: the Lurker by nature; the Imp's
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
- **Reads as something else.** Fog: Mist of the Named Dead (a boulder), Sea-fret (fish),
  Hoar (a white plant), and its rolls are faceted, so fog looks a little like rock.
  Hawk: the Passenger's shoulder reads as a draped stand. Sprite: the Collar-rider's face is
  lost between hair and collar. Drake: Kiln-throat's glazed jaw reads as big teeth.
- **A face you cannot see.** The Hollow Behind's and the Writ-riddler's second faces are at
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
- **Floats where it should lie.** Ground-veil, Black Damp, Black Ice and Grass-fire float at
  the shoulder with their ground, because their bases float.
- **Light.** The game shows every lit surface at one brightness, so a large lit area glares;
  light is kept to edges and small things except where a form is all light on purpose.

