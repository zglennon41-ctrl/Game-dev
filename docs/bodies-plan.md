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

## Proportions (the owner, 2026-11-07: "see how lanky our current iteration is")

Measured, not eyeballed: the built body and head against adult anthropometry (a 175 cm
man and a 162 cm woman, each in their own body units of 2.4 tall; the head in
head-heights, H). The first column is what we had, the second what an adult measures, the
third what we have now.

| Measure | Before | Adult | Now |
| --- | --- | --- | --- |
| Neck width | 0.13 | 0.165 | 0.17 |
| Chest width | 0.32 | 0.41 | 0.41 |
| Waist width | 0.245 | 0.36 | 0.35 |
| Hips width | 0.29 | 0.46 | 0.48 (f 0.52) |
| Hips depth | 0.18 | 0.32 | 0.30 |
| Shoulders, deltoid to deltoid | 0.52 | 0.64 | 0.64 |
| Thigh | 0.19 | 0.23 | 0.205 |
| Calf | 0.146 | 0.165 | 0.155 |
| Upper arm | 0.123 | 0.13 | 0.137 |
| Forearm | 0.095 | 0.115 | 0.11 |
| Wrist | 0.057 | 0.075 | 0.066 |
| Upper arm length, shoulder to elbow | 0.367 | 0.45 | 0.424 |
| Forearm length, elbow to wrist | 0.395 | 0.36 | 0.338 |
| Head width at the eyes, in H | 0.72 | 0.65 | 0.66 |
| Jaw width, in H | 0.59 | 0.47 | 0.48 |
| Pupils apart, in H | 0.34 | 0.29 | 0.29 |
| Eye opening, in H | 0.16 | 0.13 | 0.135 |
| Nose, root to base, in H | 0.37 | 0.23 | 0.25 |
| Nose width, in H | 0.23 | 0.15 | 0.15 |
| Mouth line below the eyes, in H | 0.26 | 0.30 | 0.305 |
| Ear height, in H | 0.2 | 0.27 | 0.26 |

So the lankiness was real and it was the trunk: the waist and hips a third too narrow, the
neck and the shoulders a fifth, with a short upper arm on a long forearm; and the head wide
at the brow with the eyes too far apart, a nose half again too long and a mouth crowded up
under it. What changed: the skeleton graph's girths and the **trunk laid on measured
rings** after it grows (`anatomy.py`, `TRUNK_RINGS`: the skin modifier's hulls at the
branches came out as boxes however the radii were set, so the trunk's vertices are set
again on a superellipse of the adult width and depth at each height, blending into the
thighs, the arms and the neck; the feminine figure has her hips wider than her shoulders);
the **elbow moved** out to 0.556 of the arm (`people_kit.py`, `elbow`), so the upper arm
is the longer bone as on an adult; the garments cut on the same rings plus a margin, so
they fit the wider body; the head's side silhouette narrowed, the eyes, nose, mouth and
ears set to the adult places. (Superseded on 2026-11-10 by the human base, below: the body is now a sculpted human
with its own girths, and what was still wrong here was the rig, not the widths: the hips
at 0.46 of the height where a hip joint is at 0.53, the knee at 0.24 for 0.29, and too
much neck. `tools/blender/measure.py` now checks the rig's joints against an adult's.)

## The human base (the owner, 2026-11-10: "more realistic and distinct; they are horrifying")

Three generations of bodies made here (lofted rings, a grown skeleton graph, a carved
sphere for a head) each improved on the last and none held a close-up: a face is the
hardest form there is, and a procedure does not sculpt one. So the bodies are no longer
generated. They are **MakeHuman's base mesh** (a sculpted adult, 13,380 vertices, with a
real face, hands and feet) **and its library of shape targets**, both CC0
(`tools/blender/makehuman/`, credited in `game/assets/CREDITS.md`; none of the plugin's GPL
code is used). `tools/blender/human.py` and `human_kit.py` do the work:

- **The form.** MakeHuman's macros give the sex, the age (young adult), muscle and weight
  (the three builds, lean, fit and heavy, are three points on those two scales, blended by
  the player's slider as before) and an **ancestry mix**; its detail targets shape the face
  feature by feature. Each home's people are written in `data/bodies.json` as `form`: the
  mix, and details by short name with a value from -1 to 1 (`nose-hump: 0.8`,
  `ear-wing: 0.8`, `head-square: 0.7`), with `m` and `f` to differ by sex. The details
  were written from each home's `brief`, the sentence that was already there ("a Roman
  nose, a firm mouth, a round head held still"). All of it is the owner's to rewrite; the
  validator checks every name against the targets the kit has.
- **The pose.** MakeHuman's stance (arms down at an angle, feet apart) is turned into the
  game rig's T-pose with MakeHuman's own game rig and weights, by forward kinematics and
  skinning in numpy: arms level, palms down, fingers together and a little curled, legs
  under the hips, soles flat.
- **The rig moves to the body, not the body to the rig.** The earlier bodies were built
  round the reshaped KayKit joints, and those joints were wrong for an adult: the hips at
  0.46 of the height (a real hip joint is at 0.53), the knee at 0.24 (0.29), and a quarter
  of a head too much neck. Now the game rig's bones are moved onto the human's own joints,
  each keeping its direction so the seventy-six clips still mean what they meant, and the
  baked translations scale with the legs and arms.
- **The weights** are MakeHuman's: the limbs bone for bone, the trunk's share laid along
  the game rig's three trunk bones, the neck shared between chest and head. The shoulders,
  hips, elbows and knees bend as their authors made them bend.
- **The head.** The face is the mesh's own: lids, nose, lips, ears. The kit adds the
  eyeballs (white, iris, pupil), brows as ribbons laid on the brow's bone, MakeHuman's lash
  strips, and cuts the hair and beards from the scalp as before. The lips are their own
  material (from MakeHuman's lip mask), tinted from the skin tone in the game.
- **The dress.** The garments are cut on rings measured from this body, then each vertex
  is laid on the body's true surface at the distance its loft gave it, so a tunic follows
  the chest and shoulders and a boot the calf; cloth that stands well off (a skirt's
  flare) is left to hang. Garments take the weights of the body under them. Under the
  dress the body is painted: an undershirt, trousers, and shoes over the feet unless the
  home goes in sandals.

What it does not do yet: expressions (MakeHuman has the targets for them), finger bones
(the hand is one piece on the rig), per-character face variation inside a home, and
garments sewn as cloth rather than shells.

## Dress as culture (the owner, 2026-11-07: the outfits mark the culture they grew up in; 2026-11-10: "the design of the clothing should be more distinct")

The test of a home's dress: **black out the figures and you can still name the home; blur the
sheet and you can still name it by colour.** So each home has a silhouette of its own, a colour
chord of its own (two colours and a metal, from the style's ramps, worn in the same places) and
a signature piece that says what the home does. `data/bodies.json` (`dress`) is the design and
`tools/blender/wardrobe.py` cuts it; every line is the owner's to rewrite.

| Home | Silhouette | Chord | Signature |
| --- | --- | --- | --- |
| Alexandria | a tabard hanging square before and behind over a high collar | slate grey, ink, brass | the cohort's brass tag; an Instructor's chain |
| Columbia (Marshal) | a broad flat hat over a long coat flaring to the calf (women: short jacket, long split skirt) | navy, cream, brass | the star, and the gun slung low on the thigh |
| Cahokia (Pilot) | a short rain cape, long sash-ends, boots flaring at the thigh (women: the woven shawl) | river green, woven ochre and red, copper | the sounding line coiled at the hip |
| Lunden (Aeronaut) | heavy fleece collar, flared breeches bound at the calf, a scarf's two ends down the back (women: the long flying coat) | charcoal, a red scarf, steel | goggles pushed up; the rigger's harness |
| Colonia (Engineer) | a slab of apron, gauntlets, one heavy shoulder, a roll across the back (women: smock, short apron, kerchief) | brick rust, black leather, steel | the tool roll and the hammer |
| Tiber (Legionary) | plated shoulders, a skirt of straps, a cloak behind, a crest above | legion red, bronze, white | layered shoulder plate; the crest (across, for a Centurion) |
| Khemet (Grower) | bare arms, a head-cloth's two lappets, a kilt with a stiff panel (women: the long sheath) | white linen, field green, gold | the growers' broad collar |
| Baghdad (Geometer) | a great turban over a robe worn open; wide trousers gathered at the ankle (women: knee coat, veil) | deep teal, cream, gold | the brass astrolabe at the sash |
| Varanasi (Ascetic) | bare shoulders and feet, a cloth across one shoulder and down the back | saffron, ash white, dark beads | the prayer beads |
| Jiangnan (Examiner) | great hanging sleeves, a straight fall to the floor (women: white jacket, skirt tied high) | plum, white, jade | the jade ring and tassel; the square of rank and the winged cap for those who have passed |
| Kazan (Rider) | a coat flaring like a bell from the sash, fur at every edge, a pointed hat | gold ochre, dark fur, red | the quiver across the back |
| Timbuktu (Archivist) | the widest: sleeves like wings, a high-wound head (women: the tall head-tie) | indigo, white, gold | the satchel for one page; a Librarian's scroll case |
| Edo (Blade) | stiff shoulders that stand past the arms over wide pleated legs (women: a crossed cord and a great bow behind) | white over black, a red sash | the blade-sash |

How the data says it:

- `colors` names each colour by a ramp and a step (`"indigo:1.25"`); `stuff` says what each is
  made of (wool, linen, robe, leather...), which goes into the material's name so the game's
  surface grain follows it. `under` is what is painted on the body beneath: a shirt and legs
  in one of the colours, or `bare` (Khemet's and Varanasi's men go bare-chested; legs are bare
  under a kilt).
- `pieces` lists what is worn. A piece may be for one sex (`sex`), so the men's and the
  women's dress of a home are the same culture and not the same garment; and for some of the
  three ways of wearing the dress (`in`: `plain`, `formal`, `master`). **Rank shows**: a
  first-year's dress is plain; formal dress adds a layer; an Instructor (`master`) wears the
  same culture grown rich: the long version, the cloak or mantle, the chain of office.
  The Academy's twelve Discipline instructors now each wear their own home's dress as masters
  (`data/academy.json`, `body`; `academy.gd` gives them the look `dress: master`).
- `headgear` is one entry or a list, by sex and by way of wearing (Tiber's crest turns across
  for a Centurion; Jiangnan's winged cap is for those who have passed).
- `options` are what the creator's Dress page offers: the working dress, a second dye of it,
  and the formal dress, each with a name and a line (`look.dress`). People the player did not
  dress take one of the plain ones by their name, so a crowd of one home is not all one colour.

How it is cut: soft pieces are shells on the body's own rings, laid on its surface, folded
toward the hem, and weighted like the body under them; an open coat or a hanging sheet has a
thickness; what stands off the body (a cloak, a mantle) hangs from the trunk and takes a
share of what moves under it; a hard piece (a holster, a roll, a chain) rides one bone. All
the pieces of one way of wearing end as one mesh (`Dress_all`, `Dress_some__in_<ways>`), and
each headgear is one mesh (`Headgear_<type>`), so a body is a handful of draw calls. The game
shows the meshes of the way a look wears the dress and dyes the option's colours in
(`World._dress_home`).

To look at it: `python tools/blender/dress_sheet.py OUT_DIR <home ...> [wear=master]` draws
bodies front and back with no game (and the white-shape and blurred sheets beside them);
`game/tests/dress_sheet.tscn` is the same as the game draws it. To rebuild every person from a
clean tree: `python tools/blender/body_kit.py all` (then `godot --headless --path . --import`).

Still weak: cloth is skinned, not simulated (a long skirt follows the legs; a cloak takes a
share of them); the game's own cloak (the creator's Cloak) is drawn over the dress and is off
by default now; trims are bands of colour, with no woven pattern yet.

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

- **The ancestry mix and the details of each home's people** (`data/bodies.json`, `form`).
  They were written from the briefs that were already there and from the cities' names;
  ten thousand years on, who lives in Kazan or Cahokia is the owner's to say, and every
  number is his to change.
- Faces inside a home: today one face per home and sex. A second and third (as shape keys,
  chosen at creation and drawn for the cohort) would make twelve classmates twelve people.
- Which of the thirteen dresses to carve first after Alexandria's.
- Whether build should change anything mechanical (it does not, by default: the line colour
  is the only difficulty, and build is a look).
