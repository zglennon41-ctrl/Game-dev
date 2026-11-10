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
| `silhouette` | Its body (`game/assets/genius/bodies/<silhouette>.glb`). Any form in the tree may name its own `silhouette` where a better body exists; otherwise it wears the base's, shaped by its age and its features. |
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

## Hybrids

A hybrid is the genius of someone whose play changed after it settled and before its first
refinement.

- At the first refinement the Tally is scored against the `nature` of every base. If
  another base's nature fits the play better than its own by a clear margin (data), the
  genius **turns**: it becomes the hybrid of the base it settled as (the first) and the
  base its partner has been playing like (the second).
- The partner is told, and may refuse: the turning is offered beside its own three paths,
  never forced.
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

## Calls that are the owner's

1. **The twenty-two bases** and their classes.
2. **Instars five and six** are ages of the finished form, not new forms.
3. **A turning is offered, not forced.**
4. **Hybrids are composed by rule** from the two bases, with hand-written pairs where it
   matters. The alternative, every pair written by hand, is 462 trees.
5. **Each home's leans** (`data/genius-homes.json`).
6. **Every form's name, sentence and leans**: about seven hundred, all drafts.
