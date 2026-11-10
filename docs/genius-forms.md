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

## Sources

The wolf (Quaternius, CC0), the KayKit rig and its clips (Kay Lousberg, CC0) and the
MakeHuman base mesh and targets (CC0) are credited in `game/assets/CREDITS.md`. The child
and baby proportion targets used for the small people come from the same MakeHuman set.
