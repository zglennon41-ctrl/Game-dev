# The home base: the Academy as a place

The owner's direction (2026-11-10): "improve the home base design and scale." The home
base is the Academy at Alexandria: the five places a student walks (the Quad, the Yard,
the Dormitory, the Hearth Hall, the Gate). Until now every one of them was the same thing:
a rectangle of KayKit dungeon floor inside a dungeon wall that came to a person's shoulder,
under a flat blue void. No buildings, no roofs, no indoors. People are 2.4 units tall
(about 1.75 m) since the human bodies; the walls were 3.

This page says what the places are now, how they are built, and what is the owner's to
change. The look is the art bible's lamplight gothic (`docs/art-bible.md`, sections 1, 2
and 5): stone and timber with brass fittings and tall glass, warm lamps against a cool
dusk, the Library's coloured light on the paving.

## The five places

| Place | What it is now |
| --- | --- |
| **The Quad** | A cloistered court under the dusk sky. North, the Library: stone its whole height, tall lancets of coloured glass between buttresses, a rose window over the great door to the Hearth Hall, its light in four pools on the paving. West, a cloister walk under a timber storey, and the porch to the Yard. South, a two-storey range (ashlar below, timber and plaster above, slate over all) and the gatehouse to the line: two turrets, the portcullis up. East, the range again, the door to the Dormitory, and the Instructors' Tower standing out of the roofs with its lamp room lit. In the court: four lawns round crossing paths, the brazier that never goes out, two old trees, six lamp posts, benches, the board with its postings, two ward stones by the gate. |
| **The Yard** | A drill ground of packed earth inside a curtain wall with a wall-walk and round corner towers. North, the stand: a timber gallery where the cohort watches a bout. East, the armoury's lean-to with blades and poles racked. Banners and lanterns on the wall. The ward ring in the middle; pells, straw dummies, a weapon rack and barrels along the south wall. |
| **The Dormitory** | Indoors. A boarded floor, a timber wainscot, plaster between posts, night in the windows, king-post trusses in the dark overhead. Six double bunks with blankets and ladders, a footlocker a student, an iron stove with its pipe up into the roof, two writing desks with their lamps, a rug, an iron ring of lamps hung from the roof. |
| **The Hearth Hall** | Indoors. A stone-flagged hall under five great trusses. North, the great hearth: a stone breast eight units wide, the fire, a brass mantel, arms above it. Banners between the windows. The rite's bowl on its carved drum in the middle with the ring round it. Two long tables against the walls, four rings of lamps. |
| **The Gate** | The Academy's own platform on the line. Station walls with glazed canopies on iron brackets, benches under notice boards, two clocks. West, the door back to the Quad. The track comes in from the east through a great arch open on the dark, the signal burning blue beside it, and ends at a buffer stop; cinders between the platform edges. Lamp posts, luggage. |

Scale against a person (2.4): a storey is 5, a door 3.9 (a great door 5.4 to 6), a window
sill 1.7 to 1.9, the ranges 12 to their ridges, the Library 14, the Tower 24, a lamp post
4.8.

## How it is built

**The kit.** `tools/blender/academy_kit.py` (headless Blender, on the wild kit's `Piece`)
builds sixty-four pieces into `game/assets/academy/<name>.glb`: wall bays for the court's
ranges, the Library, the curtain, the station and the halls; eight-wide portals, the
gatehouse, the line's arch, the great hearth; the Tower; corner pieces; seven floors; two
trusses; and the furniture. Flat-shaded, no textures; materials are named so the toon
shader finds the surface (stone, wood, metal, cloth), and names ending `_lit` glow.
`python tools/blender/academy_kit.py --sheet <file.png>` renders a contact sheet.

**The conventions** (the game relies on them):

- A wall piece is 4 wide (a portal 8), its inside face on the wall line, the building
  behind it. It is two objects: `Plinth` (the kerb, to 0.9) and `Upper` (everything else).
- A corner piece fills the quadrant outside a corner.
- A floor piece is a 4 by 4 tile, its top at 0.
- An empty named `light_lamp`, `light_fire`, `light_stain` or `light_cool` is where the
  game hangs a light; `socket_flame` is where a fire burns.

**The layout is data.** `data/academy.json`: each place has a `style` and a `furniture`
list (the schema is `data/schemas/academy.schema.json`).

- `style.kind`: `court` (under the sky) or `hall` (indoors).
- `style.floor`: the floor tile. `lawns`: rectangles of grass laid over it.
- `style.sides`: for each of `n`, `s`, `e`, `w`, the wall `bays` in order (they repeat)
  and the `door` piece. A door of the place stands its door piece exactly where the door
  is; the bays fill the wall between, stretched a little where the gap is not a whole
  number of bays. A door may name its own `piece` (the Tower). `features` stand a piece
  at a point along a side (the great hearth).
- `style.corner`, `style.trusses` (the roof timbers of a hall), `style.track` (the line
  from x: cinders, platform edges, rails, the buffer), `style.pools` (coloured light on
  the paving: x, z, size, colour), `style.ambient` and `style.lamps` (how bright).
- `furniture`: `piece`, `at` (x, z), `rot`, `scale`, and `solid` (a radius people walk
  round) or `solids` (several).

Doors, the spawn, the cohort's spots, the instructors, the board and the rest spot are
where they were: the cohort and the autopilot walk the same ground. A place without a
`style` (the zones of the line) is built as before, and if a kit file is missing KayKit's
piece stands in. `-- --kaykit` on the command line builds the old places, to compare.

**The camera never loses the hero.** Tall walls would stand between a third-person camera
and the student. So every wall's `Upper` hides while the camera is outside that wall (or
pressed against it), and its plinth stays as the room's edge. Looking into a place from
outside, it opens like a doll's house; inside, the walls ahead of you stand their full
height.

**Light.** Courts get a sky drawn as a dome (night above, the last of the day in the
west, stars, a moon) in place of the flat blue, and the moon casts the buildings'
shadows across the court. Halls have no sky: a dark warm ground, more fog, no moon. The
lamps are the kit's: every lantern, sconce, lamp post, ring of lamps and fire is a light,
each flickering about its own level; coloured glass lights every other bay; a place is
held to twenty-six lights. The rite still dims the Hearth Hall to the bowl.

## Checking it

- `xvfb-run -a -s "-screen 0 1600x900x24" godot --path . -- --academy --fresh --gate --tour --shots=DIR`
  walks the camera through every place and saves three pictures of each (`--tour=quad,dorm`
  for some; `--debug` prints what each view draws).
- `npm run validate` checks the styles and the furniture against the schema.

## What is rough, and what is the owner's

- **The layout is a first draft.** Which building is on which side of the Quad, what
  stands in the Yard, how many bunks: all of it is the data above.
- **The Library and the Tower are fronts.** There is no room behind the Library's glass
  and the Tower's door is the locked one. They are the next places if the owner wants them.
- **Outside the walls there is nothing.** From inside it never shows; the tour's high
  view sees the edge of the world. A skyline (roofs, the city, the line running out)
  would close it.
- **The cutaway pops.** A wall's upper part appears and vanishes in a frame; a short fade
  would be kinder.
- **People are the cost, not the buildings.** The architecture draws fewer triangles than
  the dungeon tiles did. A full Hearth Hall draws over two million a frame, nearly all of
  it the twelve classmates' bodies drawn three times (the body, its ink line, its shadow).
  A lighter body for people across the room is the thing to build before the web page
  slows.
- **Tests to add** (not added here, so as not to collide with other work in the test
  file): every place's style names pieces that exist in `game/assets/academy`; every
  door of a place lies on a side; every furniture `solid` leaves the spawn and the doors
  clear; `World.set_place` on each place fills the cutaway list and stays under the
  light cap.
