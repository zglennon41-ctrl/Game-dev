# The body system: people of the thirteen cities

The owner's direction (2026-11-07, after the term first held end to end): the KayKit
bodies were placeholders; the people of WILDLINE need a body system of their own, as robust
as the genius forms, that reflects the narrative, the world and the mechanics. Thirteen
homes (the twelve cities and Alexandria), each with a masculine and a feminine body, a
musculature slider, every blood's marks reading cleanly on every body, and the body able to
take the marks and changes that come at instars and ranks. This is a full-length focus.

Decided with the owner (2026-11-07): 7.5 heads tall (feminine 7.25); our own meshes on the
KayKit bones, so its seventy-six animations keep playing and our own clips replace them one
by one later; what differs by city is the face and the skin palette, and the dress; build
and hair stay the player's. Skin tone comes first, painted faces later.

## What the player sees

At creation, after the questions: **home** (from the answers), **sex** (masculine or
feminine, a choice, not read from the answers), **build** (a slider from lean through fit
to heavy, three stops, any point between), **skin** (the home's palette, four to six tones),
**face** (the home's faces, in a later pass), then hair, beard, headgear, cape, stature as
now. The blood's marks appear on the body as soon as the blood is confirmed, on the figure
standing in the chamber. At the Gate the Journeyman's trim appears; the bonded genius's
colour threads the cloak; at each instar of the genius, what the Reading writes onto the
partner (an adaptation, a graft) shows on the body.

## The pieces

| Piece | What | Where |
| --- | --- | --- |
| Base bodies | 26: `<home>-<sex>`, our mesh, skinned to the KayKit armature at 7.5 heads | `game/assets/people/<home>-<sex>.glb` |
| Musculature | shape keys `lean` and `heavy` on every base body; the slider blends | in each body |
| Faces | geometry (brow, nose, lips, ears, jaw) parameterized per home and sex; the eyes a part on `socket_eyes` | in each body; eyes `parts/eyes-<kind>.glb` |
| Skin | an albedo per tone, no texture: the material takes the tone | `data/bodies.json` palettes |
| Dress | per home: the outfit skinned with the body's weights; headgear and cape as accessories on bones | `game/assets/people/dress/<home>-<sex>.glb` |
| Hair, beards | as now, hung from the head bone, on every body | in each body |
| Marks | a part on a socket, or a surface layer, or an eye part, or a tint | `game/assets/people/parts/<feature>.glb`; surfaces in `data/people-features.json` |

### Sockets on every body

`socket_head` (horns, a crest), `socket_eyes` (the eye part), `socket_throat` (gill-lines, a
bell), `socket_back` (wings), `socket_tail`, `socket_hand_l` / `socket_hand_r` (claws, scales
on the hands), `socket_light` (a glow under the skin, carried as an emissive part), and the
hand slots and head bone the game already uses. The names and the convention are the genius
kit's (`docs/art-bible.md` §8), so one `World.dress` serves both people and geniuses.

### Features from any source

`data/people-features.json` lists every feature the body can take, each `{ id, slot, kind,
asset | surface | tint }`. Sources write feature ids onto the hero:

- the **blood** (`data/bloods.json`, `marks: [feature ids]`): ridgefolk `skin-stone`,
  tidewater `gill-lines`, lamplighters `eyes-cat`, winged `wings`, dragon-blooded
  `scales-throat`, `scales-hands`, `eyes-slit`, demon-blooded `horns`, `tail`, demigod
  `glow-under-skin`, fused `fur`, `claws`; the marks (eyes-heat and the rest) show nothing,
  which is their point;
- the **rank** at Commencement: `trim-journeyman` (the archetype's colour on collar and hem);
- the **bonded genius**: `cloak-genius` (its Shape colour threading the cape);
- **instars**: the Reading's adaptations and grafts that write onto the partner
  (`src/rules/` names them; the game lists them on `hero["features"]`).

`World.dress(node, look, hero)` reads `hero["features"]`, finds each in the data, and hangs,
layers or tints. A test proves every feature resolves to an asset or a surface and that every
blood's marks are features.

## The Blender kit

`tools/blender/body_kit.py`, headless with the bpy venv like the others:

1. **The rig**: import a KayKit body, reshape its bones with the people kit's method to the
   new proportions (7.5 heads: head 0.32 of 2.4 units), delete KayKit's meshes, keep the
   armature and every action.
2. **The body**: our mesh, grown from a chain of cross-sections (the genius kit's
   `skin_body` method, refined): torso, pelvis, limbs, hands with mitten fingers, feet, neck,
   head. Masculine and feminine differ in the chain (shoulders, hips, chest, waist, jaw).
   Three builds are three chains; `lean` and `heavy` become shape keys against `fit`.
3. **Skinning**: automatic weights from the bones, then the weights cleaned at the joints
   (the elbow, knee and shoulder bands limited to their two bones).
4. **Faces**: the head chain plus feature meshes (brow ridge, nose, lips, ears), the
   parameters per home in `data/bodies.json`; eyes as a part.
5. **Sockets**: empties placed from the bone positions.
6. **Dress**: the outfit meshes built on the body's surface (an offset shell cut to the
   garment), weights transferred from the body.
7. **Export**: one `.glb` per body with the armature, the actions, the shape keys, the
   sockets, the hair and beards; `check_glb` proves the animations, bones, sockets and
   keys survived. A card sheet renders every body in Idle and mid-strike, bare and dressed.

Budgets: body 4–8k triangles, dress 1–3k, a part 200–1,500; no textures on skin (tones are
colours), one 512 texture at most on a dress.

## Status

- **v1 (2026-11-07)**: `tools/blender/body_kit.py` builds `alexandria-m` and `alexandria-f`:
  lofts on the reshaped KayKit bones, hand weights blended across the joints, lean and
  heavy shape keys, eyes and hair on the head bone, eight sockets (Godot folds them into
  the skeleton as bones), plain materials. The game loads them for the hero, the cohort,
  the instructors and the smith (`World._person_model`; every other home wears
  Alexandria's for now; KayKit names from old saves map to them). Creation offers sex,
  build (five stops) and skin tone (seven); `World.dress` blends the shape keys, tints the
  skin (a blood that shows in the skin is blended into the tone) and keeps the cel bands.
  `godot --headless -s res://game/tests/check_people.gd` proves the animations, bones,
  sockets and keys; the sheet is `python tools/blender/body_kit.py sheet`.

- **Marks (2026-11-07)**: every blood that shows is a list of features (`data/bloods.json`,
  `marks`; the features in `data/people-features.json`): eight parts built by the body kit
  (`python tools/blender/body_kit.py parts`) hang on the socket bones (horns, a tail, wings,
  scales at the throat and on the hands, gill-lines, a beast's ears, claws; a hand part is
  built for the left hand and mirrored for the right); tints blend into the skin (stone,
  ochre, iron veins, leaf flecks, soot, fur); eyes colour the iris (cat's eyes shine); the
  demigod's glow lights the skin. `World.dress` applies them from `features_of(hero)`, which
  also reads `hero["features"]` for what instars and ranks will write. The blood sheet is
  `python tools/blender/body_kit.py bloods`; the suite proves every mark on both bodies.

- **The life on the body (2026-11-07)**: `World.features_of` adds, beyond the blood, the
  Journeyman's trim at the collar once an archetype is taken at the Gate (a part on the throat
  socket in the Shape's colour), the bonded genius's colour threading the cloak once it is
  born, its light in the eyes from its second instar, and the field under the skin from its
  third (`data/people-features.json`, `shapeColor`). The cloak is a part on the back socket,
  in the colour the look names. Anything else a Reading writes goes on `hero["features"]`
  by id and is worn the same way. Tested in `test_life_features`.

## Anatomy v2 (the owner, 2026-11-07: accurate heads and joints, or immersion breaks)

The lofted v1 bodies met at seams at every joint and the head was a loft. v2 grows **one
continuous body** from a skeleton graph with Blender's Skin modifier (`tools/blender/anatomy.py`):
nodes with radii at the pelvis, the spine, the shoulder girdle, each joint, the hands with
five fingers, the feet with heel and toes, the neck, the jaw, the skull and the crown; the
girths come from a 1.8 m frame scaled to the game's 2.4. The surface is subdivided, then
**carved** by displacement points along the normals: pectorals, deltoids, biceps, trapezius,
the spine's groove, glutes, quadriceps, calves (scaled by the build), and the face: eye
sockets, brow ridge, cheekbones, temples, the jaw's corners, the chin, the mouth's line, the
lips, the nose's ridge, the back of the skull (scaled by the home's face parameters). The
shoulders, elbows, hips and knees are continuous surfaces that bend with the weights. The
nose, ears, eyes, hair, sockets and dress hang on it as before.

## The head (the owner, 2026-11-07: bodies 7/10, heads 4/10)

`tools/blender/head.py` builds the head apart from the body's graph and sets it on the
neck: a **skull from three silhouettes** (the profile, the front, the back, blended round the
head by azimuth) on a real skull's proportions (the eyes at the middle of its height, the
face 0.39 of the height ahead of the centre, the occiput 0.39 behind, the sides 0.36 out),
**carved** (eye sockets, brow ridge, cheekbones, temples, the jaw's angles, the chin, the
philtrum, under the lip), then the features: **eyeballs set in the sockets** with an iris
and upper and lower lids, a **nose** lofted from the bridge to the tip with nostril wings,
**lips** with a cupid's bow, **ears** with helix, concha and lobe. The home's face parameters
and the sex reshape all of it. **Hair and beards are grown from the skull's own surface**:
a cap is the skull above a hairline (high at the brow, over the ear, down the nape) pushed
out along its normals with a rim, so it fits the carved head; the long fall, braid, bun and
tail hang from it; a beard is the jaw's surface the same way. The whole head is one object
skinned to the head bone; its pieces hang from the bone.

## Status, 2026-11-07, end of day

All twenty-six bodies are built on the anatomy with the carved heads, hair from the skull,
each home's face parameters, skin palette and dress; the game loads them for everyone;
`check_people.gd` is all good and the suite is at 1386. The owner's ratings before the
head pass: bodies 7/10, heads 4/10. The faces v3 pass (below) answered the face list;
the body mechanics pass the joints and the feet. Next: the dress shells cut to the body
(the shoulder notch), expressions as blend shapes, the ears, and the owner's sentences for
the thirteen faces.

## Faces v3 and the joints (the owner, 2026-11-07: "faces and body mechanics")

**The face.** The eyes are set into the socket (the ball a little deeper, the socket carved
to hold it) with **eyelids that wrap the ball**: a shell about the eye with an almond
opening whose rim turns in to the ball, so the lid has an edge and the upper lid rests on
the top of the iris; **lashes** along the upper lid, a **pupil** on the iris. **Brows are
hair**: a stroke laid on the brow's bone, thick at the root, arched at two thirds, in the
hair's colour. The **nose** and the **mouth** are surface patches that follow the skull
(each vertex the skull's own point lifted by a height): the nose a ridge from the root to a
bulb at the tip with the wings flaring behind it and the nostrils' shadow under them, so it
reads in profile; the mouth two lip mounds either side of the mouth's line, the upper with
a cupid's bow, both tapering into **corners set a little into the cheeks**; the lips take
their own material, tinted in the game from the skin's tone (darker, warmer), so they read
on every tone. The skull is finer (96 by 66) and the jaw a touch broader. The **hairline
is cut along its curve** rather than stepped: the cap is the skull's surface clipped at the
line, thin at the edge and thick at the crown; the beards the same.

**The joints.** One function gives every vertex of the body *and the garments* its bone
weights by where it is, so a sleeve's top rises with the arm as the deltoid does (the
tunic's shoulder no longer tears from the sleeve). The **shoulder** is shared between the
upper arm and the chest out past the joint, and not down the ribs under the armpit; the
**hip** between the thigh and the pelvis, with the crotch's middle kept by the pelvis; the
**toes** take the front of the foot so it rolls. The blend at a joint is **asymmetric**:
narrow on the folding side (the elbow's front, the knee's back, the hip's front) so a deep
bend does not pass through itself, wide on the stretching side (the point of the elbow, the
kneecap, the glute) so the stretch spreads. Checked in a sitting pose, a kick, a block, a
chop overhead and the run.

**The feet.** The game plays each locomotion clip at the body's ground speed divided by
the clip's own stride speed (measured in Blender: the walk crosses 1.78 units a second, the
run 8.44), within limits, and walks below a run line (`data/rules.json`, `motion`), so the
feet plant instead of sliding; the hero in the fight and the Academy, and the allies, all.

## Dress as culture (the owner, 2026-11-07: the outfits mark the culture they grew up in)

`tools/blender/wardrobe.py` dresses each home from `data/bodies.json` (`dress`): a culture
line, colours, pieces and headgear. Pieces are shells on the body's own rings (tunic, vest,
coat, robe, kaftan, kilt, wrap-skirt, cuirass, apron, hakama, greaves, boots, sandals, belt,
sash, obi, collar, scarf, wrap, gloves) with trim bands at hem, cuff or collar, cuffs and
stripes; rigid pieces hang from bones (buttons, a badge, a sash's knot and tails, tools at
the belt, pauldrons, pteruges); the headgear hangs from the head (cap with a peak, hat with a
band, folded turban with a jewel, tall fur hat, scholar's cap, hood, headband, crested
helm, goggles on any). The thirteen outfits as written: Alexandria's grey with a brass
collar; Columbia's marshal coat, brass buttons, star, gun belt, boots and brimmed hat;
Cahokia's oilskin, striped sash, boots and knit cap; Lunden's docker's jacket, red scarf,
gloves, peaked cap with goggles; Colonia's leather apron over rust, tools, gauntlets, cap
with goggles; Tiber's red tunic, bronze cuirass, pauldrons, pteruges, greaves, sandals,
crested helm; Khemet's white linen, striped sash, broad gold collar, headband; Baghdad's
deep-blue robe with gold at hem and cuff, sash, folded turban with a jewel; Varanasi's
saffron wraps, headband; Jiangnan's plum robe with white cuffs, jade belt, scholar's cap;
Kazan's belted kaftan with ochre trim, wrap, cuffed boots, fur hat; Timbuktu's indigo boubou
with gold collar, satchel strap, white cap; Edo's dark kimono with white collar, hakama, obi.
Every line of it is the owner's to rewrite.

## Order of work

1. **v1, one home**: the masculine and feminine Alexandria bodies at 7.5 heads on the rig,
   lean/fit/heavy keys, skin tones, sockets, hair; the game loads them; creation chooses sex,
   build and tone. The other twelve homes are the same bodies until their faces and dress
   come. (This replaces Knight/Rogue/Mage/Barbarian everywhere: the hero, the cohort, the
   instructors.)
2. **Marks**: every blood's features as parts and surfaces, the blood sheet on both sexes.
3. **Faces and palettes** per home.
4. **Dress** per home.
5. **Instars and ranks**: the features list fed by the Reading, the Gate and the bond.

Each step leaves the game playable and ends with a card sheet for the owner.

## Open to the owner

- The faces' character per city (a sentence each would steer the carving).
- Which of the thirteen dresses to carve first after Alexandria's.
- Whether build should change anything mechanical (it does not, by default: the line colour
  is the only difficulty, and build is a look).
