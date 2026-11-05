# WILDLINE Art Bible

Draft 0.1, 2026-11-05. The owner's decisions behind it: AI-assisted art, cleaned up by hand;
grounded proportions; a painted card for every genius form; Blender as the workbench.
Every asset, whoever or whatever makes it, is judged against this file.

## 1. The feeling: lamplight gothic

Ten thousand years after the Awakening, Earth is rail and river and fog, and people live by
lamps. The world is hard, worn and mended; it is not grim. Picture woodcut prints, rail-yard
ironwork, oil lamps on wet stone, and the tonalist painters' dusk. Three lights tell every
scene's story:

| Light | Colour | Means |
| --- | --- | --- |
| Lamp | warm amber `#FF9A4D` | people, safety, the hall |
| Moon | cool blue `#8C9EF2` | the line at night, the unknown |
| Field | the Shape's colour (below) | will, power, the genius |

**Five rules**

1. **Light tells the story.** Every frame has a warm source and a cool one; the field is the third.
2. **Silhouette first.** Every character, beast and genius must read as a black shape at 15 metres.
3. **Worn and mended.** Nothing is new. Brass is rubbed, cloth is patched, iron is rusted at the edges.
4. **Ink on the living.** Characters, beasts and geniuses carry a 2-pixel warm-black ink line
   (the game draws it); places do not.
5. **One loud colour per frame.** The scene is muted; the field's colour is the only saturated thing.

## 2. Palette

| Name | Hex | Use |
| --- | --- | --- |
| Ink | `#090807` | outlines, deepest shadow |
| Plate | `#100D0B` | UI panels, night stone |
| Brass | `#A8803F` | rims, fittings, frames |
| Brass, lit | `#FFD175` | highlights, focus |
| Parchment | `#F2E8D6` | text, bone, linen |
| Dust | `#A89B8A` | secondary text, plaster |
| Ember | `#EB5C33` | danger, hurt |
| Blood | `#C72B24` | health |
| Will | `#6BADFA` | Will |
| Moss | `#9EF2B3` | the field before it has a Shape |

**The six Shapes' colours** (the field, the genius's glow, the HUD sigil):

| Anchor | Turn | Cast | Read | Bind | Make |
| --- | --- | --- | --- | --- | --- |
| `#F2AD40` amber | `#FF6B26` flame | `#8CD9FF` sky | `#D9D9FF` pale | `#BF73FF` violet | `#80FF99` green |

Materials sit in desaturated earths (umber, slate, oxblood, verdigris, bone) so the Shape
colours carry the eye.

## 3. People: grounded proportions

Grounded, not chibi (owner, 2026-11-05).

| | Height | Heads tall | Notes |
| --- | --- | --- | --- |
| Adult | 1.75 m (1.60–1.90) | 7.5 | Instructors, townsfolk |
| Student (15–17) | 1.65 m | 7 | The player at the Academy |
| Child | 1.20 m | 5.5 | Stations, towns |

- **Readable at the game camera**: hands and feet 10% larger than life; heads true to life;
  shoulders and hips 5% wider; strong, simple shapes in clothing (coats, sashes, straps).
- **Faces**: carved, not cute. Large readable features, little fine detail.
- **Builds**: three per body (slight, middle, heavy), mixable with any blood.
- **Bloods show on the body.** Each blood's "shows" line in `data/bloods.json` is its art
  brief. Ridgefolk are broad with grey, stone-flecked skin; Aerie-born are long-limbed and
  light; Fogborn are pale with clouded eyes; Demon-blooded have horns and a second face in
  shadow; Winged have true wings that fold into a cloak. A blood is parts on the base body
  (horns, wings, tails, skin layers), never a different skeleton.
- **The cities dress differently.** Columbia: marshals' greatcoats, bells, brass buttons, the
  saber and round shield. Cahokia: oilskins, river hooks, beadwork, pole and oar. Lunden: fog
  leathers, goggles, airship rigging, rapiers and air pistols.

**Rig**: one humanoid skeleton for every person, with Godot's standard humanoid bone names,
so one library of animations fits everyone. Weapons hang from `hand.r` and `hand.l`
attachments.

## 4. Geniuses

The genius is the one thing every player sees as *theirs*. It is built the way the rules
build it: **a body for its silhouette, and parts for its features**.

### The six Expressions

| Expression | Design language | Its light |
| --- | --- | --- |
| Beast | An animal grown strange: too-long limbs, extra eyes, plates where fur should be | Eyes and seams |
| Kith | A small person of the field: a face, hands, a voice | Eyes and a heart-light in the chest |
| Engine | Brass, iron and glass with a lit core; rivets, gauges, vents | The core, through glass |
| Relic | Worn equipment that is alive: an eye in a buckle, a pulse in the leather | One eye or sigil |
| Daemon | Ink-black, contract script crawling on the skin, horns, a want in its eyes | The script and the eyes |
| Aspect | No body: flame, shadow, chord, weather; particles and shader only | All of it |

**Every genius**: glows its partner's Shape colour; carries its Seed-mark visibly for life;
reads first by its silhouette. A First Form is small (0.4–0.8 m); each instar is roughly
20% larger, and an Apex may be taller than its partner.

### Bodies and parts

- **One body per silhouette** (30 in the lattice, 11 of them First Forms).
- **One part per feature** (66 features in 9 slots). A heritage feature is *literally the same
  part* carried onto the new body, so a player sees the hawk's eyes on their gauntlet.
- **Sockets**: every body carries empties named for the slots it can take:

| Socket | Slot | Example parts |
| --- | --- | --- |
| `socket_head` | head | crest, horns, crown, beak |
| `socket_eyes` | eyes | far eyes, extra eyes, a lens |
| `socket_back` | wings | wings, a wing-cloak |
| `socket_body` | body | a broad chest, a shell |
| `socket_arm_l`, `socket_arm_r` | arms | blades, gauntlets, extra hands |
| `socket_limb_*` | limbs | talons, hooves, webbing |
| `socket_light` | light | a lantern, an ember, a core |
| `socket_throat` | voice | a bell, a resonating throat |
| (none) | surface | a material layer: iron hide, stone skin, scales, script |

- **Surface** features are not parts but material layers on the body (texture masks).
- **Budgets**: body 3–8k triangles; part 200–1,500; one 1024 texture for the body, 512 for parts.

### Cards

Every form gets a painted card, shown at the rite and on the genius's page.

- 768 × 1024 portrait; the game draws the brass frame, name and text.
- The genius three-quarter view, centred, filling two-thirds of the height.
- A dark ground with a Shape-coloured rim light from behind; one warm fill from the front.
- Painted, not photographic: visible brush edges, the palette above.
- One card per named form (120 at launch), made from the same model the game uses, rendered
  in Blender and painted over by the AI image step.

## 5. Places

- **A modular kit on a 4-metre grid** (walls, floors, arches, stairs, roofs), with trim
  sheets for stone, timber, brass, glass and rail iron.
- **The Academy** is stone and timber with brass fittings and tall glass; the Library's
  stained light falls in the quad. **The line** is iron, cinders and wet stone. **The
  river** is mud, reeds and pilings. **Lunden** is fog, rigging and gaslight.
- Line colour sets the light: green zones in daylight or lamplight; amber at dusk; red in
  fire and storm; black in the Quiet.
- Texel density 512 px per metre; places carry no ink line.

## 6. Effects

- Flipbook sprites, 8 × 8 frames at 512 px, additive for light, alpha for smoke and ink.
- Coloured by the Shape of whoever made them. Telegraphs are always red-orange (`#FF3820`),
  never a Shape colour, so danger always reads.

## 7. The interface

Already in the game (`game/scripts/style.gd`): Cinzel capitals, Alegreya for story text,
Alegreya Sans for the HUD; ink plates with brass rims and clipped corners. Icons are 64 px,
single-weight line art in parchment on transparent, with one Shape-colour accent.

## 8. The pipeline: AI-assisted, cleaned in Blender

Blender runs headless in the development environment (as the `bpy` module), so models can be
built, cleaned, exported and rendered by script; the owner may also connect an AI to a
desktop Blender later.

1. **Concept**: an image model, prompted with the template below and this bible's palette
   and rules. Pick one; draw over it if needed.
2. **Reference sheet**: front, side and back views of the chosen concept.
3. **Model**: image-to-3D, or built in Blender by script. Either way:
4. **Clean up in Blender**: retopology to the budget, UVs, baked and painted texture, the
   palette checked; scale in metres; facing +Z (the game's forward).
5. **Rig**: the humanoid template for people; the quadruped, bird and small-humanoid
   templates for geniuses. Parts are rigid and hang from sockets.
6. **Sockets**: empties named as in section 4.
7. **Export**: glTF binary (`.glb`) to `game/assets/genius/bodies/<silhouette>.glb`,
   `game/assets/genius/parts/<feature>.glb`, `game/assets/people/...`.
8. **Check**: the game's asset test (budgets, sockets, names, scale) must pass.
9. **Card**: render the model in Blender at the card framing, then paint over it with the
   image model; save to `game/assets/genius/cards/<form>.png`.
10. **Credit**: every file's source and licence goes in `game/assets/CREDITS.md`. Check each AI
    tool's terms for commercial use and ownership before its output ships.

### Prompt template (concept art)

> Concept art for a video game, painted, visible brush strokes, lamplight gothic: [subject].
> Grounded proportions. Muted earth palette (umber, slate, oxblood, verdigris, bone) with one
> glowing accent of [Shape colour]. Warm lamp light from one side, cool moonlight rim from the
> other. Worn, mended materials: rubbed brass, patched cloth, rusted iron. Clear silhouette,
> plain dark background, three-quarter view, full figure. No text.

For a genius, [subject] is: "a [Expression] creature, [form name], with [its features in
plain words], about [size]". For a card, add: "portrait framing, the creature fills two
thirds of the frame, rim light in [Shape colour]".

## 9. Checklist for every asset

- [ ] Reads as a silhouette at 15 m
- [ ] Palette: muted, one Shape accent
- [ ] Worn, not new
- [ ] Scale in metres; faces +Z
- [ ] Within budget (triangles, texture size)
- [ ] Sockets named and placed (geniuses)
- [ ] Exported as `.glb` to the right folder
- [ ] Asset test passes
- [ ] Credited, with licence
