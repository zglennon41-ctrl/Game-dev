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
