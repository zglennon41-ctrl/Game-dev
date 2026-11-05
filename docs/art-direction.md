# Improving the graphics: options and a recommendation

Written for the owner, 2026-11-05. Nothing here is decided; the questions at the end are yours.

## First, a word about "sprites"

WILDLINE is a 3D, third-person action game, so most of its art is not sprites (flat 2D
pictures) but **models** (3D shapes), **textures** (the paint on them), **animations** and
**effects**. Making the characters into 2D sprites would mean a different game: a fixed
camera, a different kind of combat, and losing the over-the-shoulder action feel you asked
for. I do not recommend it.

2D art still has real places in this game, and they are worth planning for:

| Where 2D art belongs | What it is |
| --- | --- |
| Effects | Flipbook sprites for fire, field, sparks, the genius's light (now: simple dots) |
| Portraits | Painted busts for Instructors, classmates and the reveal screen |
| Genius cards | A painted card of each First Form, shown at the rite, like a monster-breeding game's reveal |
| The interface | Frames, icons for techniques and Terms, the Shape sigils |

## What holds the look back today

- **The characters are chibi** (KayKit: big heads, small bodies). They read well, but they
  fight the "lamplight gothic" tone of the rest: brass, ink, moonlight, a hard world.
- **The genius has no art.** At the rite it is built from spheres and boxes. It is the one thing
  every player sees as *theirs*, so it is the most important thing to fix.
- **Bloods barely show.** Horns, wings and skin are bolted on; there is no body built for them.
- **One environment kit.** The Academy is built from dungeon pieces; there is no timber, glass,
  rail iron, sky or Library.
- **Few animations** beyond what KayKit ships, and none for geniuses.

## The ways to get better art

| Route | What it means | Good | Hard |
| --- | --- | --- | --- |
| **A. More free art, stronger style** | More CC0 packs (KayKit, Quaternius, Kenney), unified by the game's shaders (the ink lines, the grade, painted light) | Free, fast, I can do it now | The ceiling is low; it will always look like someone else's game |
| **B. Commission artists** | A concept artist sets the look; 3D artists build characters, geniuses and places; an animator animates them | The best and most original result; you own it | Costs real money; slower; needs art direction from you |
| **C. AI-assisted art, cleaned up by hand** | Image tools for concept art and textures; image-to-3D tools for rough models; a 3D artist (or me, within limits) cleans, rigs and fits them | Fast exploration of many looks; cheaper than B | Models come out messy and need fixing; style drifts between pieces; check each tool's licence for commercial use and ownership |
| **D. A hybrid** | B or C for the few things that matter most, A for the rest | Spends money where players look | Needs a clear list of "what matters most" (below) |

## Recommendation: D, in this order

1. **An art bible first** (cheap, and I can draft it): the palette, the proportions, how
   bloods show, what each Shape's light looks like, what a genius is made of. Every later
   piece, whoever makes it, is judged against it.
2. **The genius kit: the highest value.** Your data already builds geniuses from parts: 30
   body silhouettes (11 for First Forms) and 66 features in 9 slots (eyes, head, body,
   surface, limbs, arms, wings, light, voice). Art should be made the same way: **one body per
   silhouette, and each feature as a part that snaps onto a socket**. Then the game assembles a
   genius no one else has, from the same Reading that already decides it. Start with the 11
   First Form bodies and the features they use. Paired with a painted card per First Form
   for the rite's reveal.
3. **One hero body built for this world**: grounded proportions, with modular parts for the
   bloods (horns, wings, stone skin, fur, scales) and the cities' clothing. A humanoid rig
   so standard animations fit it.
4. **An Academy kit**: stone, timber, glass, brass and rail iron pieces, so the quad, the
   yard, the Hearth Hall and the Library can be built and rebuilt quickly.
5. **Effects**: flipbook sprites for field, fire and the Shapes' lights.

Whatever the route, the files follow one set of rules, so they drop straight in: Blender to
glTF, one unit is one metre, models face forward on +Z, sockets are empties named
`socket_<slot>` (so `socket_wings`, `socket_head`), and every file's licence is written in
`game/assets/CREDITS.md`. I can build the importer that reads those sockets and a test that
checks every delivered file against the rules, before any art exists, so artists can deliver
into it from day one.

## What I can do without an artist

- The art bible draft.
- The socket pipeline and its tests, with the current placeholder parts.
- Better shaders: a painted, hand-lit look on the CC0 models, and softer, warmer geniuses.
- Better placeholder geniuses: more parts, better silhouettes, a feature-by-feature build.

## Questions for you

1. Which route: free art only for now, commissioning, AI-assisted with cleanup, or a mix?
   Is there a budget?
2. Keep the chibi proportions, or move to grounded ones?
3. Should the rite end on a painted genius card (a 2D illustration) as well as the 3D genius?
4. Shall I start with the art bible draft and the genius socket pipeline?
