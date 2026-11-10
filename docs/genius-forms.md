# Genius forms: the art and how it is built

What the First Forms (and the Second Forms a student can reach at the Gate) look like, the
conventions their art follows, and how to rebuild it. The design language is
`docs/art-bible.md` §4; the rules of forms, features and instars are `docs/genius.md`. This
file covers only the bodies, parts and cards under `game/assets/genius/` and the kit that
makes them, `tools/blender/genius_kit.py`.

## The idea

Every form should read at once as **what it is** (a hawk, a ram, a little clay man) and as
**a genius** (something the field made: light in the eyes and the seams, a heart-light, a
lit core). Silhouette first; colour second; the glow last and always in the partner's Shape
colour.

A genius is still assembled in the game from a **body** (one per silhouette) and **parts**
(one per feature) hung on the body's sockets, so heritage shows: an otter that inherits
horns wears the same horns the ram does.

## Three families of body

| Family | Built from | Forms | Moves |
|---|---|---|---|
| Wolf rig | Quaternius' wolf (CC0), reshaped bone by bone with `beast_kit.Rig`, then dressed | field-wolf, ram, river-otter, iron hound (and clockwork hound), crowned stag, harrier | idle, walk, gallop |
| Small people | MakeHuman's base (CC0) through the game's human pipeline, on the KayKit rig, with a child's proportions and a head grown large | lantern-sprite, homunculus, ledger-imp, contract daemon, stooping kith | idle, walk, run |
| Modelled | built from plain geometry (`genius_geo.py`) | hawk, walking lantern, ember, shadow, the One Behind, chord | the hawk's wings beat; the rest hover or stand |

All of it is faceted (flat-shaded, low polygon) with **named flat materials**, no textures,
so the game's cel bands and ink outline do the drawing.

## The forms

> **Superseded (2026-11-10).** The lattice of forms (`data/forms.json`) and the kinds of the
> thirteen homes were replaced by the genius tree: `docs/genius-tree.md`. The bodies, parts and cards described
> here are all kept in `game/assets/genius` and are what the trees' forms wear; the list of forms
> below is the old lattice's, kept as the record of what each body was built for.


First Forms:

- **Hawk** (`beast-flier`): a raptor on the wing. Deep barred breast, hooded brow, fanned
  tail with a pale band, legs tucked. Its wings, bill and feet are parts (wings, beak, talons).
- **Ram** (`beast-grazer`): stone-skinned and stocky. Short thick legs with hooves, a deep
  chest, the head carried low under a slab of brow, plates of stone down the back, cracks
  of light along the flanks. The curled horns are the horn-brow part.
- **Field-wolf** (`beast-runner`): a lean wolf on legs a third too long, a ruff of quills
  over the neck, a second pair of eyes above the first, a seam of light down the spine.
- **River-otter** (`beast-swimmer`): long, low and sleek. Round small-eared head, pale
  throat, whiskers, a heavy tapering tail, a line of light along each flank; small hands
  on its forepaws and fins at its heels.
- **Lantern-sprite** (`kith-fey`): a slight child of the field with pointed ears and lit
  eyes, a leaf-green shift with a hem of petals, a crest of pale leaves, a heart-light,
  and two pairs of glass wings that beat. It carries its lantern in its left hand.
- **Homunculus** (`kith-homunculus`): made, not born. A big-headed little man of fired
  clay with an old face, a leather apron, a brass-ringed stone in the chest, the mould's
  seam lit over the crown; spectacles (old-eyes) and a brush in the right hand.
- **Iron hound** (`engine-quadruped`): the wolf's frame in riveted plate. Iron hide, brass
  lower legs, a copper cable for a tail, vents along the back, a furnace behind a brass
  grille in each flank, a lantern at the collar.
- **Walking lantern** (`engine-lantern`): a caged lamp on three jointed legs with clawed
  feet, a peaked cap and a carrying ring, a gauge on its belly.
- **Ledger-imp** (`daemon-small`): gaunt and ink-black, long-eared, pot-bellied, the lines
  of its ledger ruled in light across its chest and arms, a rag at the hips, the book
  strapped to its belt; ringed horns and a tail are parts.
- **Ember** (`aspect-flame`): no body. A bright heart in a cradle of cracked coal, tongues
  of flame turning round it, cinders adrift, a thread of smoke.
- **Shadow** (`aspect-shadow`): a hooded figure with nothing in the hood but two eyes; the
  cloak falls in flat folds to tatters that never reach the ground; long fingers.

Second Forms reachable at the Gate that now have art bodies:

- **Crowned Stag** (`beast-crowned`): tall on fine legs, the neck carried high, antlers
  with the field at every point and a ring of light held between them.
- **Harrier** (`beast-ground-hunter`): the hawk come down to hunt on foot: a lean coursing
  beast with a crest of feathers from brow to shoulder, hooked fore-claws, a fanned tail.
- **Clockwork Hound** (`engine-quadruped`): wears the iron hound's body.
- **Stooping Kith** (`kith-small-warrior`): a small warrior hooded and mantled in hawk's
  feathers over a leather jerkin.
- **Contract Daemon** (`daemon-tall`): the imp grown tall and thin.
- **The One Behind** (`daemon-shadow`): the shadow's figure in ink, broad in the shoulder,
  its cloak ruled with script.
- **Chord** (`aspect-chord`): three tilted rings of light about one bright note, smaller
  notes riding the rings, a dark tuning fork beneath.

The other Second Forms (the relics, the shield-faced engine, the thinking gun) still use
the game's placeholder bodies.

Parts with art (23): wings, beak, talons, far-eyes, horn-brow, horns, broad-chest,
long-legs, fangs, fins, small-hands, lantern, voice, brush, old-eyes, roots, cold-core,
tail, ember, glow, and for the Second Forms short-blade, chain and gears. A feature with
no part file still gets the game's placeholder shape.

## What is rough

- The ram, the stag and the harrier are the wolf's skeleton underneath: they read by their
  horns, antlers, crest and proportions, but they move like a wolf (a stag does not gallop
  like that) and the ram's face is still a dog's under the stone.
- The small people have realistic human faces at a small size. They read as kith by their
  proportions, lit eyes and dress, not by a designed face; a stylized head would serve
  them better.
- The hawk does not fold its wings or perch; it is always on the wing.
- Nothing has an attack, a hit or a death clip of its own: bodies play idle, walk and run.
- Placeholder shapes sit beside the art for features without parts (crest and mask on the
  relics, wall-plate, and so on) and for the Second Forms without bodies.

## Conventions

- **Files.** `bodies/<silhouette>.glb`, `parts/<feature>.glb`, `cards/<form>.png`. The game
  uses an art body or part when the file exists and falls back to its placeholder otherwise.
- **Facing and sides.** In Blender a body faces −Y and stands on Z = 0; the character's
  left is +X. (In the game that is facing +Z, left +X.)
- **Size.** Every body is built about 0.72 units tall; the game scales it to its instar's
  size (`data/genius.json`). An art body carries its own proportions, so the old
  per-silhouette `scale` applies only to placeholders; `artSize` in
  `data/genius-bodies.json` says how tall an art body stands against its instar's size
  (the otter 0.5, the stag 1.35 for its antlers).
- **Sockets.** Empties named `socket_<name>`. On a rigged body each is parented to a bone;
  the importer brings those through as bones and the game hangs a node on each
  (`GeniusBody._art_sockets`). Every body has: `head`, `eyes`, `mouth`, `throat`, `light`,
  `back`, `body`, `tail`, `grip`, `arm_l/r`, `limb_fl/fr` (and `limb_bl/br` on four legs),
  `hand_l/r` where it has hands or forepaws.
- **Which socket a part uses.** By its feature's slot (`slotSockets`), unless
  `featureSockets` names sockets for that feature and the body has them: a beak and fangs
  at the mouth, small hands at the wrists, a brush in the grip, a tail at the tail's root.
- **What a body carries itself.** Where a feature is the body's own design (the stag's
  antlers, the harrier's crest and claws, the stooping kith's feather mantle, the chord's
  rings), the silhouette lists it under `carries` in `data/genius-bodies.json` and the
  game hangs no part for it. Features of the `surface` slot (stone skin, a ruff, a ledger,
  a cloak of shadow) are always the body's own.
- **Pairs are made for the left.** A part hung on a right-hand socket (a name ending `_r`,
  `fr` or `br`) is mirrored by the game.
- **A socket may be turned and sized.** The hand sockets turn a hanging hand onto a paw or
  the end of an arm; the ram's head socket is 1.75 times as big as an ordinary head's, so
  the horns made for an ordinary head clear its broad skull.
- **Part frames.** A part is modelled at its socket's origin, the body facing −Y. A hand
  hangs: fingers down (−Z), palm inward (−X), thumb forward. A held tool's working end
  points along the grip socket's −Z.
- **The field.** Any material whose name starts with `field` glows the partner's Shape
  colour in the game (and takes the card's rim colour in a card). Eyes, seams, heart-lights,
  cores, script, wing membranes and feather tips are all `field_*`.
- **Wings.** Objects named `wing_l` and `wing_r`, origin at the shoulder. The game beats
  them about the body's forward axis, the left rising with a positive turn.
- **Clips.** A rigged body keeps only three: `AnimalArmature|Idle`, `|Walk`, `|Gallop` on
  the wolf rig; `Idle`, `Walking_A`, `Running_A` on the KayKit rig. `data/genius-bodies.json`
  `kinds.<kind>.anim` names them and `GeniusBody` plays idle, walk and run from that table.
- **Budgets.** Bodies at most 8,000 triangles (the game's tests hold them to it): the
  wolf-rig bodies run about 2,300 to 2,700, the small people 6,400 to 7,400, the modelled
  ones 700 to 1,400. Parts 40 to 1,500 (the hand is the heaviest at about 1,000).

## Cards

A card is the assembled form (body, its parts on their sockets, a rigged body in its idle
pose, wings lifted) rendered at 768 × 1024 on a dark ground: a warm key from the front
left, a rim in the Expression's colour from behind, a faint cool fill.

## Rebuilding

From the repository root, with Blender's Python module installed (`pip install bpy`):

```
python tools/blender/genius_kit.py                 # every body, part and card, then the sheet
python tools/blender/genius_kit.py bodies parts    # models only
python tools/blender/genius_kit.py cards           # cards and the sheet
python tools/blender/genius_kit.py ram otter       # those forms' bodies and cards
godot --headless --path . --import                 # let the game pick the new files up
```

The sheet of all cards is written to the kit's scratch folder (set `WILDLINE_GENII_SCRATCH`).
To see them in the game: `godot --path . -- --gallery=2` (every form up to the Second), or
`godot --path . -- --academy --fresh --gate`.

To add a form's art: write a function in the kit that returns a `Built` (objects, sockets,
and the armature if it is rigged), add it to `BODIES` under its silhouette, and run the kit
with the form's id. To add a part: a function returning its objects, added to `PARTS` under
the feature's id.

## The second set: more forms (2026-11-10)

> **Superseded (2026-11-10).** The lattice of forms (`data/forms.json`) and the kinds of the
> thirteen homes were replaced by the genius tree: `docs/genius-tree.md`. What follows is the record of the
> bodies built then; the forms that wore them are now forms of the trees.


The owner asked for more possible forms. The lattice (`data/forms.json`) went from 35 forms
to 52, and from 11 First Forms to 22: every Expression now has at least three ways in at the
rite, the Relic among them (it had none). All of it is a first draft for the owner: names,
features and who is offered what are design calls, listed at the end of this section.

New First Forms (offered only at the rite, like the Hawk):

| Form | Expression | Body | Who is offered it |
| --- | --- | --- | --- |
| Hooded Crow | Beast | `beast-corvid` | "watches from above"; "with a voice" for a Cast; aerie-born, beast-voice, winged |
| Cairn-tortoise | Beast | `beast-shell` | "remembers"; Anchors; ridgefolk, mound-kin |
| Fledgling Kith | Kith | `kith-fledgling` | "with a voice"; "remembers"; "watches from above" for a Read or a Bind; winged |
| Clockwork Wren | Engine | `engine-flier` | "watches from above" (first for a Make); "never alive"; forgeborn, ironblooded |
| Hearth-stove | Engine | `engine-stove` | "stands between"; "that burns" for an Anchor or a Make; forgeborn, iron-blood |
| Watch-buckle | Relic | `relic-buckle` | "something I can hold"; second-heart, fused |
| Kept Knife | Relic | `relic-knife` | "something I can hold"; eyes-heat |
| Worn Glove | Relic | `relic-glove` | "something I can hold"; second-heart, fused, riverborn |
| Wick-fiend | Daemon | `daemon-wick` | "that burns"; "owes me"; demon-blooded, dragon-blooded |
| Whisperer | Daemon | `daemon-whisper` | "with a voice"; "owes me"; demon-blooded, nightfolk, hollowfolk |
| Rime | Aspect | `aspect-frost` | "never alive"; "that burns" for a Turn; a Turn of any Seed |

New Second Forms (from the Gate on): Storm-crow (the crow's body, a voice and old eyes),
Weir-otter (the otter's body, fangs), Old Cairn-back (the tortoise's body, a horned brow),
Lamplighter (`kith-lamplighter`: an old kith with the light on a pole over his head), Brass
Kite (the wren's body, a sight-glass), Wisp-train (`aspect-wisps`: five flames in procession,
the first in a cage).

The placeholders a student could reach at the Gate now have bodies: the Shield-faced Engine
(`engine-sentinel`), the Thinking Gun (`engine-weapon`), the Talon Relic (`relic-gauntlet`),
the Living Blade (`relic-blade`), the Tower-shield Hound (`relic-shield`) and the Coat That
Listens (`relic-coat`). The relics are worn equipment that is alive: an eye in a buckle and
in a pommel, a line of the field beating in the leather, a coat with nobody in it.

Twenty-three bloods had no lean in the Reading; each now leans toward an Expression and a
feature or two (`data/reading.json`, `leans.blood`), so the bowl's three depend on the
answers that gave the blood as well as on the Seed and the Shape. The three scripted lives
(`docs/three-lives.md`) become what they became before; only the two offers Mira, Tobiah and
Sable did not take at the rite have changed. `npx tsx tools/genius-offers.ts` prints the
bowl's three for every Seed and Shape.

Seed-marks that had nothing to show on an art body now have parts: a grip (a leather-bound
handle on its back), a ledger (a strapped book at its chest), a broad guard (a plate on each
shoulder). A watching eye and a shell have parts too, for when they are heritage.

Where the new bodies are built: the crow is the hawk with `corvid=True` in
`genius_kit.py`; the rest of the beasts, engines, daemons, aspects and kith are in
`tools/blender/genius_forms2.py`; the relics, the new parts and the keepsakes in
`tools/blender/genius_relics.py`. The kit loads both.

## Looks: no two of a form alike (2026-11-10)

`data/genius-looks.json` says how one genius differs from another of its form;
`game/scripts/genius/genius_look.gd` reads it; `genius_body.gd` paints it. A genius carries a
small `look`, saved with it: the number it was born with and what its partner chose.

**Born with** (drawn from the partner's Seed, Pattern, spark and name; the same every time,
and its own through every instar):

- its coats: three out of its body's palette (`palettes`, `bodies.<silhouette>.coats`, or a
  form's own under `forms`), the first of which it is born in. Every coat is a muted earth,
  stone or metal: the Shape colour stays the one loud colour.
- its markings: which of its body's marking regions show (about half, no more than two).
- its build: lean to heavy, and a longer or shorter tail.
- its light: steady, bright, banked, a slow pulse, a flicker.

**The partner chooses**, on the genius's page (J), under "How it looks": which of its three
coats it wears, each marking on or off, and a keepsake (a collar, a ribbon, a charm, a bell)
in one of five colours. The bowl's three offers at the rite are shown as this hero's genius
would wear them, so the same form looks different for another student.

**Play writes**: the Seed-mark is always a part on the body; heritage carries over as
before; every instar the body is bigger and its light is stronger (`instarGlow`).

How the art carries it (the conventions a new body follows):

- **Coat**: the body uses the palette's material names; `bodies.<silhouette>.roles` maps
  each to a role (`main`, `under`, `trim`) and the game paints the role's colour. Parts that
  share those names (the hawk's wings) are painted with the body.
- **Markings**: faces in a marking region use a material named `mark_<region>`
  (`mark("socks", like)` in the kit), born the colour of the coat under it. The game shows
  it in the coat's marking colour or hides it in the role named by `on`. Wolf-rig bodies get
  socks, a mask, a saddle and a tail tip cut from their own skin (`_finish_wolf(coat=...)`);
  the others name what suits them (a hood, ringed scutes, stitching, a blazon, enamel).
- **Build**: blend shapes named `lean`, `heavy`, `long_tail` (`shape_key(ob, name, move)`).
  A body without them is made a little broader or narrower as a whole.
- **Keepsake**: hung on `socket_keepsake`, or the throat, or the chest. A collar goes on
  `socket_collar`, whose scale is the size of the neck (the collar is a hoop 0.1 in radius
  in its own XZ plane); a body with no such socket is not offered a collar. Keepsakes are in
  `game/assets/genius/keepsakes/`; the material `keepsake_tint` takes the chosen colour.

A body with a look is shown on its card as itself (the live model); the painted card is the
form's and is used where there is no look (a shade, the gallery).

```
python tools/blender/genius_kit.py keepsakes            # the keepsakes
python tools/blender/genius_kit.py looks field-wolf 8   # one form in eight looks, as the game paints it
```

The second writes `genius_looks_<form>.png` to the kit's scratch folder. The kit's copy of
the look rules is in `genius_relics.py` (`resolve_look`); keep it in step with
`genius_look.gd`.

What is rough: the small people (sprite, homunculus, imp, the kiths) take coats but have no
marking regions or blend shapes yet; surface features (stone skin, a sleek coat) still do
not change an art body's skin; later forms (the Third on) that have no body of their own
are still placeholders.

**Design calls in this set, for the owner to confirm or change:** the seventeen new forms'
names and features; that the new First Forms are offered only at the rite; the leans given
to twenty-three bloods; the four new features (a shell, a skin of rime, an eye that opens
in it, a pulse in the leather); what a genius is born with against what its partner may
choose; three coats on offer; the four keepsakes and five colours; the names of the coats.

## The kinds of the thirteen homes (2026-11-10)

> **Superseded (2026-11-10).** The lattice of forms (`data/forms.json`) and the kinds of the
> thirteen homes were replaced by the genius tree: `docs/genius-tree.md`. A home no longer has kinds of
> its own: it raises the chance of some bases at the rite (`data/genius-homes.json`). The
> bodies and cards built for the home kinds are kept, and several are the bodies of bases
> and of forms on their trees (`silhouette` in `data/genius-bases/*.json`). The `home` block of
> `data/reading.json`, `growsInto` and "keeping its kind" as a fourth choice are gone from
> the rules: a genius always keeps its kind now, because a refinement offers nothing else.


The owner asked for the fullest variety that is logically sound, and for it to carry the
diversity of the people in the game. So where a character grew up now shapes what the field
takes as a body: every home has two kinds of genius of its own, First Forms that are the
young of something from that home's land, its craft or its working life. Twenty-six First
Forms and four elders (`data/forms.json`, `home`); the lattice went from 52 forms to 82, and
from 22 First Forms to 48. All of it is a first draft for the owner.

The rule for choosing them: one from the home's real animals, one from what its people make
or do, something a child of that home could plausibly want beside them. No gods, no sacred
things, no figures of worship, no people: animals, tools, instruments, weather, work.

| Home | Kind | Expression | What it is | Young | Grown, and its elder |
| --- | --- | --- | --- | --- | --- |
| Alexandria | Station Cat | Beast | the cat every platform has | Station kitten | Station Cat |
| | Handcar | Engine | a pump-trolley of the line, the size of a dog | Little handcar | Handcar, then **Shunter** |
| Columbia | Ring-tail | Beast | a raccoon: masked, clever-handed | Ring-tail kit | Ring-tail |
| | Marshal's Star | Relic | a badge nobody is wearing, with an eye in the boss | Tin star | Marshal's Star |
| Cahokia | Beaver | Beast | the river's builder | Beaver kit | Beaver |
| | Bell-buoy | Engine | a channel marker: a bell in a cage, a light on top | Little bell-buoy | Bell-buoy, then **Channel-light** |
| Lunden | Dock Fox | Beast | the fox of the wharves | Fox kit | Dock Fox |
| | Fog | Aspect | a bank of it that came ashore and stayed | Wisp of fog | Fog; great, a Fog-bank |
| Colonia | Boar | Beast | the boar of the forest above the works | Boar piglet | Boar |
| | Fitter | Kith | a small hand of the engine-works: apron, cap, a spanner as long as its arm | Bench-hand | Fitter; great, a Master fitter |
| Tiber | Wall-mastiff | Beast | the big dog that guards the old walls | Mastiff whelp | Wall-mastiff |
| | Signal-horn | Relic | a great round horn of brass; the note sits in the bell as a light | Little horn | Signal-horn |
| Khemet | River-horse | Beast | a barrel on four posts, out of the river | River-horse calf | River-horse |
| | Flood | Aspect | the rise of brown water the black fields live by | Trickle | Flood; great, a High Flood |
| Baghdad | Gazelle | Beast | all leg and neck, ringed horns | Gazelle fawn | Gazelle |
| | Astrolabe | Engine | a brass disc that turns to look at you | Little astrolabe | Astrolabe, then **Armillary** |
| Varanasi | Mongoose | Beast | long, low and quick, afraid of nothing | Mongoose pup | Mongoose |
| | Vigil | Daemon | what sits up with you: a hooded shape with a lamp in its lap. Its contract: it stays awake while you do | Small vigil | Vigil; great, a Long Vigil |
| Jiangnan | Carp | Beast | a golden fish that swims in the air at your shoulder | Carp fry | Carp, then **Gate-carp** (the carp that leaps the gate, as a candidate passes the halls) |
| | Clerk | Kith | a small scholar: long robe, square cap, a roll of paper | Little clerk | Clerk; great, an Examiner's clerk |
| Kazan | Steppe Horse | Beast | short, deep-chested, tough | Steppe foal | Steppe Horse |
| | Dust-devil | Aspect | a column of wind that has picked up the steppe | Breeze | Dust-devil; great, a Steppe-wind |
| Timbuktu | Camel | Beast | a long way up; the caravans' own | Camel calf | Camel |
| | Marginal | Daemon | what lives in the margins of a book and wants to be read | Small marginal | Marginal |
| Edo | Crane | Beast | tall on stilts, a spear of a bill | Crane chick | Crane; great, an Old Crane |
| | Wooden Sword | Relic | a practice blade of oak | Wooden Sword | then the **Living Blade** (the practice sword becomes the real one) |

By Expression: thirteen Beasts, three Engines, three Relics, three Aspects, two Kith, two
Daemons.

**How a home leans the bowl** (`data/reading.json`, `home`; the same in
`src/rules/reading.ts` and `genius_reading.gd`):

- The bowl's first offer, the best fit, is read from Seed, blood and Shape alone, as before.
  A home does not move it.
- For the second and third offers, a kind of the character's own home counts for nearly
  twice its score and a little more (`bonus`, `floor`). At most one of the three is of home
  (`most`). The offer says so: "home: columbia" is among its reasons.
- A kind of another home counts for half (`away`), everywhere, so it is rare: a child of
  Edo is seldom offered a camel. Alexandria's two are open to everyone (`open`): everyone
  passes through.
- With no blood and no chance, a kind of home is among the bowl's three in 79 bowls of
  100, across every home, Seed and Shape (`npx tsx tools/genius-home-offers.ts` prints the
  count by home). It is the best fit on its own merit in about one bowl in a hundred.
- A home's kinds come only at the rite. Later Readings offer the common lattice, and the
  kind is kept by keeping its kind: a carp fry that stays a carp becomes a gate-carp at the
  Third Form whatever the Tally says.

The three scripted lives pick and become what they did. Mira and Tobiah, both of Columbia,
are now offered the Ring-tail second at the rite and take the hawk and the iron hound as
before; Sable's bowl is unchanged.

**Where they are built.** `tools/blender/genius_homes.py` (loaded by the kit). Eleven
beasts are the wolf's rig reshaped (`_beast`), so the ages in `data/genius-bodies.json`
shape them: a steppe foal has the large head and short legs of the young. The carp and the
crane are modelled; the fitter and the clerk are small people on the KayKit rig; the rest
are modelled things. Each has a palette of coats of its own or shares a fitting one
(`data/genius-looks.json`: cat, ringtail, fox, bristle, hound, hide, sand, grizzle, horse,
carp, crane, mist, water, dust, oak, robe), marking regions, and a card.

Ten new features, all of the body's own surface (nothing hangs for them): whiskers, a
paddle of a tail, a mane, a hump, wheels, a bell, a dial of figures, a body of mist, a
current, pages.

```
python tools/blender/genius_kit.py station-cat handcar      # those forms' bodies and cards
npx tsx tools/genius-home-offers.ts                         # how often each home's kinds are offered
```

What is rough: the wolf-rig beasts are honest reshapings, not new sculpts (the camel and
the horse most of all: a wolf's skull on a long neck); the carp's side fins beat as wings
do; the crane walks with its wings folded and has no flight; the vigil and the marginal
do not move their hands; the small people take coats but no markings; a new surface
feature that becomes heritage on another body shows nothing there (as with every surface
feature).

**Design calls in this set, for the owner:** which two kinds each home has, and their
names; the names of their young and their great; which have an elder; that a home's kinds
come only at the rite; that the home never moves the bowl's best fit; how strongly it
leans the other two (79 in 100); that another home's kind is rare, not impossible; that
Alexandria's are open to all; the sixteen palettes.

## Sources

The wolf (Quaternius, CC0), the KayKit rig and its clips (Kay Lousberg, CC0) and the
MakeHuman base mesh and targets (CC0) are credited in `game/assets/CREDITS.md`. The child
and baby proportion targets used for the small people come from the same MakeHuman set.
The second set of forms, the relics, the parts and the keepsakes use nothing from outside:
they are modelled in the kit.
