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

## What it will not do

It will not reach DW9's character fidelity: that is sculpted art and motion capture. What
it will do is make the stylized image look finished, so the next step is art direction on
top of a working pipeline, not a pipeline.
