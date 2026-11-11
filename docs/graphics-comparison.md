# Graphics: where WILDLINE stands against Dynasty Warriors, and the plan to compete

The owner asked (2026-11-07) for a comparison with games like Dynasty Warriors and a plan to
be competitive. Plainly: Dynasty Warriors 9 and Origins are AAA productions of a large
studio, and no procedural kit closes that gap in one pass. But a great deal of what reads
as "AAA" on screen is lighting, surface, silhouette and motion, and much of that is
reachable here. This page says what they do, what we do, and what we change, in the order
of visual payoff per hour.

## What Dynasty Warriors does (Origins, 2025; DW9, 2018)

| Layer | Dynasty Warriors | WILDLINE today |
| --- | --- | --- |
| Characters | Hand-sculpted heroes, 40–80k triangles, 4K PBR textures (albedo, normal, roughness, metal), subsurface skin, hair as strands or cards, layered armour with physics | Procedural bodies of ~8k triangles, flat colours per material, no textures, hair as caps and tubes, dress as shells |
| Faces | Scanned or sculpted, blend-shape expressions, eye shaders with caustics and wet reflections | A carved skull with set eyeballs, lids, nose, lips, ears; no expressions |
| Animation | Motion capture, blended by state, inverse kinematics, cloth and hair simulation | Seventy-six KayKit clips on a shared rig, linear blending, no cloth |
| Crowds | Hundreds of soldiers with levels of detail, instancing, impostors | A pack of up to three beasts, a cohort of twelve |
| Lighting | Deferred PBR, cascaded shadows, screen-space ambient occlusion and reflections, volumetric fog, global illumination | A moon and lamps, shadows on one directional light, no ambient occlusion, flat ambient |
| Post | Bloom, depth of field, motion blur, colour grading, tone mapping, temporal anti-aliasing | Bloom, filmic tone mapping, a vignette with grain, contrast and saturation |
| Effects | Particle systems with lit sprites, trails, decals, camera shake, hit-stop | Particle bursts, a sword trail, floaters, hit flashes, camera kick |
| Environment | Terrain with layered materials, foliage, weather, time of day | Tile libraries, flat materials, a night mood throughout |
| Look | Realistic with a stylized edge | Cel-shaded with ink outlines (the owner's choice: Zelda, Genshin) |

Our look is not theirs, by decision: a cel-shaded stylized game competes with Genshin and
Breath of the Wild, not with DW9's realism. The relevant comparison is **how finished the
stylized image looks**: surface detail under the bands, soft and hard shadows, rim light,
ambient occlusion in the folds, cloth that hangs, hair with volume, faces that hold a
close-up, and motion that does not slide.

## The gaps, ranked by payoff per hour here

1. **Lighting and ambient** (hours, no art): a sky-lit ambient so the top of a form is
   lighter than the underside, a key light with soft shadows, a rim light that lifts the
   character off the ground, a two-band specular so metal is metal, exposure and grading.
   This alone moves the image most.
2. **Surface detail under the bands** (hours): tileable detail textures (linen weave, wool,
   leather grain, brushed bronze, skin) blended by world-space triplanar projection, so no
   UVs are needed; vertex-colour ambient occlusion baked into every body, so armpits, the
   neck, under the belt and inside the collar darken.
3. **Silhouette** (a day): cloth folds displaced into the garment shells, hems with
   thickness, layered edges; hair with more volume and a second layer.
4. **Faces** (days): lids that wrap the ball, brows as hair, a nose bridge in profile, mouth
   corners; later, expressions as blend shapes.
5. **Animation** (weeks, and the largest gap): the KayKit clips are limited; our own clips
   for strikes and locomotion with weight, and simple cloth and hair sway, would do more
   than any texture. Motion capture is out of reach here; hand-keyed clips in Blender are
   not.
6. **Effects** (days): hit impacts with lit sprites and decals, dust at the feet, weather.
7. **Environments** (weeks): the tile libraries carry the same treatment as the people.

## What changes now (this pass)

- The cel shader becomes `TOON2`: sky-tinted ambient wrap, two-band specular with a
  per-material gloss (metal, leather, skin, cloth), a rim light, a world-space triplanar
  detail texture chosen by material name, and vertex-colour ambient occlusion.
- Seven tileable detail textures generated here (`tools/textures.py`): linen, wool,
  leather, bronze, skin, stone, wood; the surface is read from the material's name, so the
  places' floors and walls take stone and their crates and beams wood without any edit.
- The environment: a sky for ambient, soft shadows, exposure and grading tuned for the
  bands.
- The body kit bakes a cavity ambient occlusion into every body's vertex colours and
  displaces folds into the garments.

Everything stays data: `data/rules.json`, `art` holds the shader's numbers.

## The second pass (the owner: "faces and body mechanics")

- Faces: eyelids that wrap the ball with lashes and a pupil, brows as hair, a nose and a
  mouth as surface patches on the skull (a bridge that reads in profile, a cupid's bow,
  corners), lips tinted from the skin, the hairline cut along its curve
  (`docs/bodies-plan.md`, "Faces v3 and the joints").
- Joints: one weighting for the body and its garments, the shoulder and the hip shared
  across the joint, toes that roll, asymmetric blends so a deep bend folds without passing
  through itself.
- Feet: every locomotion clip plays at the body's ground speed over the clip's stride, a
  walk below the run line (`data/rules.json`, `motion`), so the feet plant.

## The third pass (the owner: "more realistic and distinct; they are horrifying")

The characters row of the table changes: the bodies are now MakeHuman's sculpted human
(CC0) on the game's bones, about 26,000 triangles with a real face, hands and feet, each
home's people shaped from its own ancestry mix and face details, the rig moved onto real
joints and the standing and moving clips' arms brought down to the sides
(`docs/bodies-plan.md`, "The human base"). Still flat colour under the cel bands, by the
look's decision. A bug found on the way: the game had been hiding the eyes, noses and
lips of every kit body since they arrived (the look's show-and-hide loop treated them as
headgear); that is fixed and tested.

## The third pass of the picture: light, ground and air (the owner, 2026-11-11: "graphics improved dramatically and upgraded resolution")

(The pass above was the bodies'. This one is everything round them. All of it runs in the
Compatibility renderer and on the web; the numbers are in `data/style.json`.)

| What | Was | Is | Costs |
|---|---|---|---|
| Walls, floors, roofs, ground | one flat colour a material, under a faint blocky grain | nine grains made for places at 512 (`tools/textures.py --places`: flagstone, ashlar, brick, plaster, planks, slate, cobble, earth, grass), chosen by the material's name (`materials.places`), with their smaller copies and anisotropic filtering; broad patches of lighter and darker over the whole place; the dark at the foot of whatever stands | two more texture reads a fragment of a place (`shading.place`) |
| The sky | a flat dark with a disc | a gradient, stars of two sizes, drifting cloud silvered by the moon, the moon's seas and ring; the zones of the line have it too, in their own night | a few noise reads on the sky's pixels only |
| Lamps and fires | a light and a flat pane | a glow about each (one quad that faces the camera, flickering with its light), the lit dust in the cone under a lamp on a post, a pool on the ground, the light a lit window lays before it (`lights.halo`) | one to three small additive quads a lamp; no light added |
| Depth | far walls faded to black | they fade toward a paler, bluer dark out of doors and a warm haze in a hall (`lights.kinds`: `fog`) | none |
| Shadows | four cascades, soft and thin | two cascades (half the shadow passes: the quad draws about a fifth fewer objects than before with everything here added), a crisper edge, a stronger moon in a court | less than before |
| Standing on the ground | figures and props floated where the moon did not reach | a soft contact shadow under every person, beast and prop (`shading.contact`) | one quad each |
| People and beasts | a pale rim all round | also the key light along the edge on the side the light is: amber by a lamp, pale under the moon (`shading.keyRim`); the ink line thins with distance (`ink.thinFrom`) | a few operations a light |
| Wind | none | grass, leaves and hung banners move (`shading.place.sway`) | a few operations a vertex |
| A blow | a star | the star lights what is about it for as long as it lasts | one light for a fifth of a second |
| Text in the world | drawn from a small picture | from one three times the size, with its smaller copies | a little memory |
| The line's rails and ties | plain boxes outside the style | of the style: named, on their ramps, banded, grained | none |
| Settings | | 8x anisotropic filtering, hi-dpi on, 4096 shadow map, 4x MSAA as before | |

Still short of a shipped game: the trees' crowns and other round things are still cut in few
facets (the kits want rebuilding with more segments, and soft crowns); the Cut is still the
borrowed dungeon tiles; there is no day (every place is dusk or night); lamps cast no shadows of
their own; there is no true bloom, depth of field or ambient occlusion in corners; water does
not move; the ground beyond a place's walls is bare.

## What it will not do

It will not reach DW9's character fidelity: that is sculpted art and motion capture. What
it will do is make the stylized image look finished, so the next step is art direction on
top of a working pipeline, not a pipeline.
