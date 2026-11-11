# One style

> "Generally improve and conform the design of the game. I want a universal style for every
> aspect of the game: lineages, attire, weapons, genii, settings, animations. I want this
> game to have a uniform style that fits the theme and tone of the game." (owner, 2026-11-10)

WILDLINE is drawn as a lamplit woodcut: quiet, earth-coloured surfaces cut in clean shapes,
lit in bands by a warm lamp and a cool moon, inked where it lives, and loud only where the
field is.

That sentence is the art bible's "lamplight gothic" (`docs/art-bible.md`), which until now
was words. This page is the same style as rules a check can test; the numbers are in
**`data/style.json`**; the game reads them through `game/scripts/style.gd`; and **`npm run
check:style`** fails on whatever is off them. An asset that is off the style is a bug, the
same as a failing test.

| To change | Change |
|---|---|
| A colour of the palette, the cap on saturation | `ramps`, `cap` |
| What a material is, how it is shaded, how worn it looks | `materials` |
| The ink line's weight or colour | `ink` |
| The lamp's, the fire's or the moon's colour; how a kind of place is lit | `lights` |
| The picture's grade, grain, exposure | `film` |
| An effect's colour or shape | `effects` |
| How long things take to move | `motion` |
| The interface's colours, corners, typefaces | `interface`, `type` |

No code changes for any of these.

## Bright, or loud?

The art bible said two things that pull apart. The look the owner chose is "cel-shaded,
clean shapes, light in bands, **bright colour**" (§11). Rule 5 says "**one loud colour per
frame**: the scene is muted; the field's colour is the only saturated thing."

Resolved this way: **bright is a matter of light, loud is a matter of saturation.** A
surface is quiet in colour (never more saturated than the cap, half way from grey) and
clean in light (its lit band is its true colour, not grey mud, and its shadow is tinted, not
black). Full saturation is kept for what is light itself: the six Shapes' colours (the
field: a genius's eyes and seams, a technique, the echo on a partner), the telegraph's red,
and flame.

Why this way and not bright colour everywhere:

1. **The genius is the signature.** It and the field must be the first thing the eye finds
   in any frame. They cannot be if a coat or a lawn is as loud as they are.
2. **Danger must read.** A telegraph is always the same red and nothing else is that red.
3. **Lamplight needs dusk.** A lamp is only warm against something quiet and cool.
4. **It is what makes thirteen homes, three art kits and two CC0 libraries one world.** A
   borrowed prop cannot be redrawn, but it can be held to the same palette.

How muted is a number (`cap`, 0.5) and the owner's to move.

## The rules

Each rule says what holds it. "The check" is `npm run check:style`.

### 1. Shape

- **Silhouette first.** A person, a beast and a genius read as a black shape at fifteen
  metres. (By eye: `godot --path . -- --sheet=<base>` for genii.)
- **Few, large, clean shapes.** Detail is cut in as planes (a bevel, a fuller, a fold),
  never as noise.
- **The living are smooth; the made are cut.** Flesh, fur, hair and cloth are smooth-shaded
  so the bands of light run as clean curves. Stone, timber, iron, brass and glass keep hard
  edges and flat planes (`shading.smooth`; the kits read it through
  `tools/blender/style.py`).
- **The cut corner and the pointed arch.** One family of corners everywhere: the
  interface's plates are clipped at 45°; stone and timber are cut square or chamfered; a
  blade's tip and a lancet come to a point. Nothing is rounded like a toy (the borrowed
  dungeon tiles of the Cut still are: see "Not done"). This one is held by eye.
- **Worn and mended.** Nothing is new: every made thing carries its grain (`materials`,
  `wear`).

### 2. Colour: ramps, and a cap

- The palette is **twenty ramps**, each a line of five colours from shadow to light:
  ink, slate, stone, bone, umber, leather, oxblood, ochre, saffron, moss, verdigris,
  indigo, plum, earth, reed, water, iron, steel, and two accents, brass and rust.
- **Every unlit surface lies on a ramp** its material allows, within a small tolerance. One
  that does not is moved to the nearest point of the nearest such ramp **when its material
  is made** (`World.toonify`, and wherever the game dyes something afterwards: a cloak, a
  head of hair). A kit's painted texture is brought over whole, colour by colour.
- **No unlit surface is more saturated than the cap** (0.5). Brass and rust may reach 0.66:
  brass because it is small (rims, fittings, buttons), rust because red hair and a fox's
  coat are what they are. Skin keeps the tones of `data/creation.json`, up to 0.62.
- **Loud is a short list** (`loud`): the six Shapes' colours, the telegraph's red, the
  unshaped field's moss. Only light wears them: a material named `field_*`, an effect, the
  interface's accents.
- Each of the thirteen homes keeps its own hue, on the ramps: Columbia's coat is indigo,
  Tiber's tunic oxblood, Varanasi's cloth saffron, Jiangnan's plum, Khemet's linen bone
  with verdigris.

Held by: the check walks every material in the game's art and what the game makes of it.

### 3. Materials

A material is one of a fixed set, told by a word in its name (`materials.words`:
`metal_brass` is brass, `dress_tiber_main` is cloth, `field_seam` is the field's light).
The class gives its ramps, its bands of light, the tint of its shadow side, its highlight,
its grain and how worn it looks.

| | Classes |
|---|---|
| The made and the worn | skin, cloth, leather, wood, stone, iron, brass, bone, glass |
| The land and the living | coat (hair, fur, feather, hide, a genius's markings), growth, earth, water |
| Light | field (the Shape's colour), lit (a lamp, a flame, a lit pane) |
| What the game needs | eye, ink (shadow, void), mixed (a kit's painted texture) |

- **Only light glows.** A material that shines and is not `field_*` or `*_lit` (or water
  under the moon) fails the check.
- A name that says nothing of what the thing is made of fails the check.
- Skin's shadow is warm; everything else's is near grey, a little cool (a blue coat in
  moonlight in a blue shadow is how a quiet colour turns loud, so the shadow adds almost
  no colour of its own). Metal has a hard highlight; cloth almost none.

### 4. Ink

- **The living carry a 2-pixel warm-black line** (people, beasts, genii), measured on a
  screen 900 pixels tall and scaled with the screen, so it is the same share of the picture
  at any size. **Places carry none.** (`ink`; the check builds a hero, a beast, a genius
  and every place and looks.)

### 5. Light

Three lights tell every scene's story, and every place has a warm one and a cool one.

| Light | Its source looks | It throws | Means |
|---|---|---|---|
| Lamp | amber `#FF9A4D` | `#FFB57A` | people, safety, the hall |
| Fire | `#FF8A3D` | `#FFA763` | the hearth, a torch, the bowl |
| Moon | blue `#8C9EF2` | pale `#B3BDE6` | the line at night, the unknown |
| Field | the Shape's colour | the same, small | will, power, the genius |

- **What a light throws is paler than its source.** A wall in moonlight is stone with a
  cool cast, not blue paint. The moon's cast, and any zone's own moon, may be no more than
  0.24 saturated.
- A lit pane is the lamp's amber; the Library's stained glass is the Shapes' own colours,
  banked down (`lights.stain`).
- **Kinds of place** (`lights.kinds`): a **hall** is keyed by lamps and filled by the night
  in its windows; a **court** is keyed by the moon and filled by lamps and lit windows; the
  **wild** is the moon and the post's lamp (the post is a lamp because the post is
  safety); the **Cut** is moonlight through a broken roof and torches. A place may give
  its own numbers over its kind's (`data/academy.json`, `data/creation.json`, a zone's
  `light`).

Held by: the check builds every place and finds its warm light and its cool one, and holds
each zone's moon and ambient to the caps.

### 6. The film

One grade over the whole world and never over the interface (`film`): shadows a little
cool, highlights a little warm, saturation just under true, a vignette, a little grain.
It used to add saturation and contrast; it no longer does.

### 7. Motion

So that things move alike (`motion`):

- **A motion made for show has three parts**: it gathers (the anticipation, about a third),
  it goes (the strike, the shortest), it comes to rest (the settle, the longest).
- **The living idle on one breath**: 3.6 seconds, whatever the clip's own length (the
  people's idle was a one-second bob; a wolf's was already slow).
- **The unliving hover on another**: 2.8 seconds, rising and falling a twentieth of their
  own height.
- **Feet plant.** A walk or a run is played at the speed that matches the ground
  (`data/rules.json`, `motion`; this was already so).
- **A thing with weight settles with one small overshoot** and never bounces twice.
- **A hit stops time for 0.04 to 0.14 seconds and shakes the frame 0.04 to 0.2**; the
  fight's own numbers (`data/combat-room.json`, `feel`) must lie inside those.
- **Every flame flickers alike**, an open one twice as deep as a lamp behind glass.
- **The interface has three times and one easing**: quick (0.2 s, a prompt), arrive
  (0.35 s, a panel; lines of a list 0.05 s apart), ceremony (0.7 s, a title card, a fade
  between places); everything eases out and nothing bounces.

### 8. Effects

One family of shapes, in ink and light (`effects`): the **ring** (thin, flat on the
ground), the **shard** (a long splinter of light lying along its travel), the **puff** (a
soft blot of dust), the **flash** (a four-pointed star where a blow lands), the **slash**
(the blade's trail) and the **word**. No spheres, no confetti.

- A telegraph is the telegraph's red and nothing else is.
- What a partner makes is in their Shape's colour; a technique of another Shape in that
  Shape's.
- A block and a parry are the moon's colour, lit; a break brass-lit; a blow landing a warm
  spark; a hurt blood at the screen's edge; dust dust.

### 9. Type and the interface

- Three typefaces and no others: Cinzel for titles, Alegreya for the story, Alegreya Sans
  for the interface. No script but `style.gd` loads a font.
- Ink plates, brass rims, clipped corners. One palette (`interface.colors`); no screen
  keeps a copy of its own.

## What it means for each part of the game

| | The style asks |
|---|---|
| **Lineages** (people, bloods) | Grounded proportions (art bible §3). Smooth. Skin from the home's tones, shadowed warm. A blood shows as parts and marks on the same body; what glows of it is the field's. |
| **Attire** | Each home its own hue, on a ramp, never past the cap; cloth, leather and metal by name; brass only as trim. Worn, not new. |
| **Weapons** | The same iron, steel, brass, wood and leather as everything else. Cut edges. The only light on a weapon is `field_glow`, and it grows with mastery. |
| **Genii** | See "What a genius's body must hold to", below. |
| **Beasts** | Smooth. Coats on the ramps; ink; the field shows in eyes and seams only. |
| **Settings** | Cut edges, no ink. Materials on the ramps (the CC0 kits' painted textures brought over). A warm light and a cool one in every place. |
| **Effects** | The family above, in the colours above. |
| **Animation** | The motion language above. |
| **Interface** | Three typefaces, one palette, clipped corners, three times, one easing. |
| **Sound** | Not held yet. The same idea would hold it: a warm voice (the lamp: strings, a bell) and a cool one (the moon: breath, glass) in every place, and one loud voice (the field). `docs/sound.md` is where it would go. |

## What a genius's body must hold to

For whoever builds the bodies (`tools/blender/genius_*.py`, `GeniusBody`). The check
already walks `game/assets/genius`.

1. **Name every material for what it is made of** (a word from `materials.words`). What is
   light is named `field_*`.
2. **Colours on the ramps**: `style.conform(name, color)` in the kit's `mat()` does it
   (`tools/blender/style.py`). Coats in `data/genius-looks.json` belong on the coat's
   ramps (132 of 637 are off today, 2 far off: two of the carp's).
3. **Smooth where it is flesh, fur, feather or cloth; cut where it is blade, plate, brass
   or stone** (`style.smooth(living)`).
4. **Only `field_*` glows, on no more than an eighth of the body** (`genius.glowShare`):
   eyes, seams, one sigil. Never a whole limb, wing or blade. Its strength by instar is
   `genius.glowEnergy` (1.2 at the First Form to 2.8 at Apex); the light it throws on the
   ground no more than `genius.groundLight`.
5. **The field's light is the partner's Shape colour and no other.**
6. **Ink**: the game draws it (`World.make_form`), 2 pixels.
7. **It hovers by the motion language**: height × `motion.hover.rise` ×
   sin(2π·t / `motion.hover.period`). A rigged one idles on the breath:
   `World.breath(anim, clip)` is the speed to play its idle at.
8. **Every stage a different black shape at fifteen metres.**

## The check

```
npm run check:style
godot --headless --path . res://game/tests/style_check.tscn -- --verbose
```

It checks, in order: the style's own numbers (every ramp under its cap and running shadow
to light; the telegraph no Shape's colour; the moon's cast pale; every kind of place warm
and cool; the fight's feel inside the motion's bounds; hair, skin and each zone's night);
the typefaces and that no screen keeps its own palette; every material in the art (a known
class; nothing glowing that is not light; no colour that is not a shade of anything its
class may be) and what the game makes of it (on a ramp, under the cap, a painted texture
brought over); the ink line on the living and not on places; and the warm and cool light of
every place.

A **FAIL** is off-style and the game cannot put it right by itself. A colour the game
moves onto its ramp when the material is made is counted and passes; `--verbose` lists
them. The fewer of those the better: `tools/blender/style.py` puts a kit's colours on the
ramps when the kit is built, and `python3 tools/style-conform.py --write` does the same for
the colours the data names (hair, a zone's night, the creator's lights).

## Calls that are the owner's

1. **How muted.** The cap is 0.5. At 0.6 the coats and the grass are livelier and the
   field stands out less; at 0.4 it is closer to a print.
2. **Facets or smooth for the living.** The rule here is smooth (people already are;
   beasts and genii are faceted today and would be rebuilt smooth). The other way is to
   call the facets the field's hand: everything the field made is cut like a gem, and only
   people are smooth.
3. **How much a genius may glow.** An eighth of the body, eyes and seams. More reads as
   power and less as a creature.
4. **How dark the night.** The places are as bright as they were; only the colour came out
   of them. Darker nights would make the lamps mean more and the fights harder to read.
5. **The Library's glass.** Banked down to deep colours. It could be the one place the
   Academy is allowed to be loud.
6. **Red hair.** Held to rust (0.66). It was a much brighter red.

## Not done

- Every genius form now has a body of its own, built on the ramps, soft where it is living
  and cut where it is made (`docs/genius-lines.md`); the beasts are welded smooth. Fog is
  the exception: its rolls are still faceted, as its first body was.
- The people's art was not rebuilt on the ramps: the game moves 25 of their 64 colours as
  it makes them. The weapons, the wild and the Academy's kits were rebuilt.
- The CC0 dungeon tiles of the Cut are still toy shapes in the right colours. The Cut
  wants a kit of its own, like the Academy's.
- The game shows every lit surface of a genius at one brightness whatever its model asks,
  so a large lit area glares; the bodies keep light to edges and small things for it.
- Sound.
