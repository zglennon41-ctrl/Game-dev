# The genius tree

> "I want each region to not have set forms but probabilistic increases to certain forms.
> That way we can build each out with core development paths that can be pathed out to give
> players their perfect complement. I want a good mix of animals, monsters, magical
> creatures, items of power, weapons, armors, all with a degree of sentience and the ability
> to evolve, grow, adapt and interact with the character's development in the game. I want
> at least 20 base forms, with development paths that work as follows: level 0 (spark),
> level 1 (settled), three paths for development, three prongs further from the first, two
> finishing specialization evolutions. I also want hybrids that blend the 20 base models
> that have their own similar development paths and represent individuals who change their
> playtime after the genius settles but before the first refinement." (owner, 2026-11-10)

This replaces the lattice of forms (`data/forms.json`) and the kinds of the thirteen homes.
It is the specification; the rules in `docs/systems-10-genius-shades.md` that it changes
are listed at the end.

> "Every path should feel unique. Genius are the representation of the soul outside of the
> body. No level of detail will be enough to capture that depth but I love and prefer the
> attention to detail." (owner, 2026-11-10)

## The soul outside the body

A genius is its partner's soul, standing where it can be seen. So a tree is not a set of
combat roles with a creature's name on them. Each base is a kind of soul; each path is a
trait in a person, shown as what this creature becomes when its partner lives that way; and
no two paths in the whole game are the same trait or are earned by the same play.

What that asks of the data, and the checker holds it to:

- **A base says whose soul it is** (`soul`: one sentence).
- **Every form from the first refinement on says what in its partner it is the picture of**
  (`of`: a phrase, a trait and not a role: "one who cannot leave a thing unfinished", not
  "a defender").
- **Every form has detail a player can see and come to know**: `sign` (what a stranger
  would notice about it: something on its body or in how it carries itself) and `habit`
  (what it does when nothing is happening). These are shown on its page and are what an
  artist and an animator build from.
- **Every path is unique in play.** A path's signature is the two things it leans on most.
  No two paths in the game share a signature; no more than three in the game lean first on
  the same thing; and the three paths of one base lean first on three different lines of
  the Tally. The common triad (one that strikes, one that guards, one that thinks) is
  exactly what this rules out.

## The shape

Every genius is on one tree. A tree has five levels and thirty-one forms after the spark.

| Level | Called | When | Choices | Forms in a tree |
|---|---|---|---|---|
| 0 | the spark | from the night the field wakes | none: it is the mote | (1) |
| 1 | settled | the rite | the bowl offers three **bases** | 1 |
| 2 | a path | the first refinement, at the Gate | three **paths** of its base (or it turns: see Hybrids) | 3 |
| 3 | a prong | the second refinement | three **prongs** of its path | 9 |
| 4 | a finish | the last refinement | two **finishes** of its prong | 18 |

After the finish it does not change form again. It grows great, and then to its apex, as
the form it finished as (instars five and six: size, presence, its great move; `docs/
genius-progression.md`, "Ages").

Twenty-two bases, so 682 forms before hybrids. Each form has a name, a sentence, what it
adds to the body, and what play leads to it.

## The bases

A mix by class, each a thing with a will of its own.

| Class | Bases |
|---|---|
| Animals | Wolf, Hawk, Stag, Tortoise, Fox |
| Monsters | Imp, Lurker, Fiend, Drake |
| Magical creatures | Sprite, Homunculus, Ember, Fog |
| Items of power | Lantern, Astrolabe, Bell |
| Weapons | Blade, Gun, Bow |
| Armors | Shield, Gauntlet, Coat |

A settled form is the young or the small of its base (a wolf pup, a kept knife, a buckler),
so that what it grows into is growth.

## A base, as data

One file a base: `data/genius-bases/<id>.json`. `data/genius-bases/wolf.json` is the
pattern; `python3 tools/genius-base-check.py` checks every file against this page.

| Key | What it is |
|---|---|
| `id`, `name`, `class`, `expression` | `class` is animal, monster, creature, item, weapon or armor. `expression` is how it fights and is drawn (beast, kith, engine, relic, daemon, aspect). |
| `silhouette` | Its body (`game/assets/genius/bodies/<silhouette>.glb`). Any form in the tree may name its own `silhouette` where a better body exists; otherwise it wears the base's, shaped by its age and its features. Where a prong or a path names its own `silhouette`, the forms below it on that road wear it too, unless they name their own. |
| `soul` | One sentence: whose soul settles as this. |
| `spark` | One sentence: how the mote behaves before the rite when this is what it will settle as. |
| `nature` | What the base stands for, as leans on the Tally (below). Used to tell when play has turned toward another base. |
| `calls` | What the first Reading reads to offer this base: weights by `seed`, `shape` and `blood`. |
| `hybrid` | `adj` (how it names a hybrid it is the second half of: "Fanged"), `gift` (the one or two features it lends that hybrid's body), `text`. |
| `settled` | The level 1 form: `id`, `name`, `text`, `sign`, `habit`, `features`. |
| `paths` | Three. Each has `id`, `name`, `of`, `text`, `sign`, `habit`, `leans`, `features`, and three `prongs`; each prong the same and two `finishes`. |
| `newFeatures` | Features this base needs that `data/features.json` does not have: `id`, `slot`, `label`. |

Rules for a form:

- **`id`** begins with its base's id. **`name`** is unique across every base.
- **`text`** is one or two plain sentences in the game's voice: what it is and how it came
  of how its partner plays. No statistics.
- **`features`** are what this form adds to the body (one to three). A form wears its own
  and those of every form above it on its path, so a finish carries the whole road.
- **`leans`** say what play leads here, in the words of the Tally. Every form from level 2
  down must have them, and the choices offered together (three paths, three prongs, two
  finishes) must lean on different play, so that a player who plays one way gets one
  answer.

The Tally's lines and keys a form may lean on, each with a weight above 0 and up to 1:

| Line | Keys | It counts |
|---|---|---|
| `range` | close, mid, far | where the partner's blows land |
| `orders` | guard, hunt, hold, free | the orders it is given |
| `shape` | anchor, turn, cast, read, bind, make | the technique families the partner uses, by Shape |
| `fights` | parries, blocks, hurts, dodges | how the partner meets a blow |
| `company` | alone, party | who they go out with |
| `ground` | line, wild, water, ruin, night, quiet | where they go |
| `pattern` | fires, sworn | how the Pattern is used |
| `bonds` | classmate, shade, named | who they are bound to: classmates fought beside, shades spoken with, named beasts felled |
| `quests` | linework, salvage, hunt, escort, writ, deep-run | the work they take |

## Regions

A home does not have forms of its own. It raises the chance of some bases at the rite
(`data/genius-homes.json`): a multiplier on that base's score for a child of that home. No
home makes a base certain and none forbids one. The Seed, the blood and the Shape still do
most of the reading, and the bowl's best fit is never moved by the home alone.

## The Readings

- **The rite** scores every base by its `calls` (Seed, blood, Shape), multiplies by the
  home's lean, and offers three. The one taken settles.
- **A refinement** reads the Tally since the last Reading, scores the children of the form
  it is (three, or two at the last) by their `leans`, and offers them all, best fit first,
  each with the lines of the Tally that speak for it. The partner chooses or lets it settle
  on the best fit. Nothing outside its own tree is offered, so a genius always keeps its
  kind; what the play decides is which of its kind it becomes.
- **Heritage, adaptations and grafts** work as before: adaptations a partner kept fed
  become part of it at a refinement; grafts are taken then.

How each is scored (every number is in `data/reading.json`; the same code in the tools,
`src/rules/reading.ts`, and in the game, `game/scripts/genius/genius_reading.gd`, held to
the same answers by `game/tests/fixtures/readings.json`):

- **The rite.** For each base: the weight of the Seed line times what the base's `calls`
  say of the character's Seed, and the same for the blood and the Shape (weights 1.0, 1.0
  and 0.6). The bowl's own chance adds a little to each (the game's `rite.formNoise`,
  seeded by the run). The best of those is offered first, and the home has no say in it.
  For the second and third offers each base's score is multiplied by the home's lean on
  it, and counts for 0.8 of itself for every base of the same class already offered, so
  the bowl shows three kinds of thing. A base offered because of the lean says so, and its
  score stays the Reading's own.
- **A refinement.** The Tally is read as nine lines (the table above). On a line that
  counts things (range, orders, shape, fights, company, ground, quests) each key has its
  share of the line, and the line counts in full once it has enough on it (its
  `reference`: twenty blows, twenty orders, ten runs, six postings) and for less before.
  The pattern line counts fires against `patternFires` and whether it is sworn; bonds are
  yes or no. A form's fit is, over everything it leans on: the line's weight, times how
  much the line counts, times the lean, times the share; summed and divided by the sum of
  its leans. So a form whose leans are exactly the play scores near 1, and a form that
  leans on nothing the partner has done scores 0. Of equal fits the one written first is
  offered first. The three heaviest contributions are the lines that "speak for it".
- **Instars five and six.** A finished form has no children: the Reading offers it itself,
  it keeps what it kept fed and takes its grafts, and its age rises. A genius that is
  behind (an old save: below) is still offered the children of the form it is, however
  old it is.
- **Heritage** is the fixable adaptations it holds at a Reading, added to those it already
  kept, up to `rules.genius.heritageMax`. It is never lost afterwards. The parts of the
  forms above it on its road are not heritage: the tree carries them (a form wears its
  road).

What the Tally counts for each line, in the game: `range` where the partner's blows land;
`orders` the orders the genius carried out; `shape` the technique families used, by their
Shape; `fights` the partner's parries, blocks, blows taken and dodges; `company` runs
with a party and runs alone; `ground` the zone's ground (the tunnel, the line, a post and
the junction are the line; a river is water) and runs by night, and a day at study is a
day somewhere quiet; `pattern` the Pattern's fires and whether it is sworn; `bonds` a
classmate's trouble seen to or a run with one, a shade's acceptance, a named beast felled;
`quests` the type of each posting taken.

## Old saves

A genius saved before the tree is a form no tree has. When it is loaded it settles again,
as the base that wears the body it had (or, failing that, a base of its Expression, or the
first base), at the first level of that tree. It keeps its name, its look, its Seed-mark,
its grafts, the adaptations it had kept, and its instars: they are its age. Its history
says it settled again. At its next Readings it is refined from there, late as it is.

## Hybrids

A hybrid is the genius of someone whose play changed after it settled and before its first
refinement.

- At the first refinement the Tally is scored against the `nature` of every base, as a
  form's leans are. If the best of the others fits at least `min` (0.45) and at least
  `1 + margin` (1.5) times as well as its own, the genius may **turn**: it becomes the
  hybrid of the base it settled as (the first) and the base its partner has been playing
  like (the second). Both numbers are in `data/genius-hybrids.json`.
- The partner is told, and may refuse: the turning is offered beside its own three paths,
  never forced. Letting it settle never turns it. What is offered is the hybrid's path the
  Tally speaks best for, with the lines that speak for the second base ("since it settled
  you have fought like a Blade: fighting close, parrying"); taking it makes the genius that
  form, and from there it is refined down the hybrid's own tree and never turns again.
- **Body**: the first base's, wearing the second's `gift` and a coat from the second's
  palette.
- **Name**: the second's `adj` and the first's name: an Edged Wolf, a Winged Shield, a
  Lantern Fox.
- **Its own tree**, the same shape (three paths, three prongs each, two finishes each),
  composed by rule from the two bases' trees so that all 462 ordered pairs exist without
  being written by hand: its paths are the first base's paths bent toward the second (each
  keeps the first's body and takes its leans half from each), and in every path one prong
  is the second base's nearest prong carried across, with its finishes. Names are composed
  from the two (the rule and its fragments are data), and a pair may be written by hand in
  `data/genius-hybrids.json` where the rule's result is not good enough.
- A hybrid is one genius, not two: it has one Seed-mark, one coat, one page.

The rule exactly (`compose` in `src/data/tree.ts` and `game/scripts/genius/genius_tree.gd`;
`npx tsx tools/genius-tree.ts wolf blade` prints any pair's tree):

1. For each of the first base's three paths, in order: of the second's nine prongs not
   yet carried, take the one whose leans are most like the path's. Of the path's own three
   prongs, the one whose leans are least like the second's `nature` gives way to it. The
   carried prong comes with its two finishes.
2. The path's leans are bent toward the second's nature: each lean is half the path's own
   and half the nature's (`bend`). **A hybrid's three paths are each earned by their own
   play**, as a base's are: where a path bent that far would have the same signature (its
   two heaviest leans) as one before it, it is bent half as far, then a quarter, then not
   at all.
3. Names: the hybrid is the second's `adj` and the first's name (an Edged Wolf). Its paths
   are the second's `adj` and the path's name (an Edged Night-watch). The first's own
   prongs and finishes keep their names. A carried prong and its finishes take the first's
   `adj` (a Fanged Wooden Sword), which is where a pair most wants writing by hand.
4. The soul's fields: a hybrid's path is the picture `of` what the first's path was,
   "turned toward the (second)'s way"; the forms under it keep their own `of`. Every
   form's `sign` is its own with the second's gift added in words ("It wears a short blade
   and an edge, the blade's."). Every form keeps a `habit` of the first base's: a carried
   prong takes the habit of the prong it replaced, and its finishes those of that prong's
   finishes, since it is the first's body that has the habit.
5. Its body is the first's (a form that names its own body keeps it); every form wears the
   second's `gift`; its coat is from the palette of the second's body.

A pair written by hand (`pairs` in `data/genius-hybrids.json`, keyed `first+second`) may
give the hybrid a `name`, and any form of it (by the id of the form it came from) a
`name`, `text`, `of`, `sign` or `habit`. Three are written: the Edged Wolf (wolf, blade),
the Winged Shield (shield, hawk) and the Lantern Fox (fox, lantern), each with what its
paths are the picture of and a creature's name and sign for every carried form.

## What this changes in the rules

| Was | Is |
|---|---|
| Six instars, each a new base form read from the whole lattice | Four forms on one tree (settled, path, prong, finish), then two ages as the finished form |
| A Reading offers the top three of every form, and may cross Expressions | A refinement offers the children of the form it is; it turns only once, into a hybrid, at the first refinement |
| "Keeping its kind" as a fourth choice | Always: there is nothing else to keep |
| Kinds native to a home | A home's lean on the common bases |
| 82 forms | 22 bases of 31 forms, and hybrids by rule |

The Seed and its mark, the Tally kept in the open, heritage, adaptations, grafts, shadows,
secondary forms, orders, moves by body and feature, ages, looks, the home's piece, the echo
and the cohort's genii all stand.

## Where it lives

| | |
|---|---|
| A base | `data/genius-bases/<id>.json`, checked by `npm run validate` (schema `data/schemas/genius-base.schema.json`, and every rule of this page) and by `python3 tools/genius-base-check.py` |
| The homes' leans | `data/genius-homes.json` |
| The Readings' numbers and the plain words for each line | `data/reading.json` |
| The turning, the rule that composes a hybrid, pairs written by hand | `data/genius-hybrids.json` |
| The tree and the hybrids, in code | `src/data/tree.ts`, `game/scripts/genius/genius_tree.gd` |
| The Readings, in code | `src/rules/reading.ts`, `game/scripts/genius/genius_reading.gd` |
| A form, asked for | `Data.form(id)` in the game, `formOf(id)` in the tools. A base's form is asked for by its id (`wolf-pup`); a hybrid's by `first+second:` and the id of the form it came from (`wolf+blade:wolf-night-watch`). Every form says its `base`, `kind`, `level`, `parent`, `children`, its `own` parts and all the `features` it wears, its `leans`, its body and whose coat it wears, and its `of`, `sign` and `habit` |
| The tests' own three bases | `game/tests/fixtures/bases` (written by `tools/genius-test-bases.py`): the rules are tested on these, so that a change to a real base is never a failing test of the engine |

To look at it: `npx tsx tools/genius-tree.ts <base> [<second>]` prints a tree;
`npx tsx tools/genius-tree.ts --turnings` and `npx tsx tools/genius-offers.ts` count what
the turning and the bowl do across every base. In the game, `godot --path . --
--gallery=<base>` (or `<first>+<second>`, or a class, or nothing) stands a tree up;
`-- --page=<form id> --fresh` opens the genius's page at a form; `-- --academy --fresh
--gate --reading=<base>` opens the first refinement as if the term had been played like
that base.

`habit` is shown on the page and is not yet acted out in the world: `Genius.habit()`
returns the form's, for the body's idle and the hall to use.

## Calls that are the owner's

1. **The twenty-two bases** and their classes.
2. **Instars five and six** are ages of the finished form, not new forms.
3. **A turning is offered, not forced.**
4. **Hybrids are composed by rule** from the two bases, with hand-written pairs where it
   matters. The alternative, every pair written by hand, is 462 trees.
5. **Each home's leans** (`data/genius-homes.json`).
6. **Every form's name, sentence and leans**: about seven hundred, all drafts.
7. **How easily a genius turns** (`data/genius-hybrids.json`: least fit 0.45, margin 0.5).
   A character does not choose their base by how they play (the bowl reads the Seed, the
   blood and the Shape), so many will find that their play fits another base better than
   their own. With these numbers, play that is purely another base's nature brings a
   turning in 449 of the 462 ordered pairs, and play that is its own nature never does.
   Lower them and most characters are offered a turning; raise them and a hybrid is rare.
8. **What the turning offers**: one card, the hybrid's best-fitting path, beside its own
   three. The alternative is to offer all three of the hybrid's paths (six cards).
9. **The words the rule gives a hybrid** (`rule` in `data/genius-hybrids.json`) and the
   three pairs written by hand, which are drafts.
10. **Heritage** is now only what it adapted and kept. Before the tree a new form also
    carried parts of the form it had been; on the tree it wears its whole road instead.
11. **A day at study counts as somewhere quiet**, and a run in the tunnels, on the line, at
    a post or at the junction counts as the line (the `ground` line of the Tally).
12. **How often each base is offered.** With no chance and no home, the Stag is the bowl's
    best fit for about 1 character in 100 and the Wolf for 1 in 80, against 1 in 10 for the
    Hawk and the Imp (`npx tsx tools/genius-offers.ts`). That is the bases' `calls`, which
    are drafts.
