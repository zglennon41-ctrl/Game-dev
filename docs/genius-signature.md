# The genius: the signature

> "Everything should be logical. I want the genius to be the signature mechanic of the
> series. It needs to be the best part. Every aspect fully developed, a unique expression of
> character and play." (owner, 2026-11-10)

This is the bar, and the audit against it: every aspect of the genius, the rule that makes
it logical, where it stands in the game today, and what is left. The rules are in
`docs/systems-10-genius-shades.md`; how progress shows is in `docs/genius-progression.md`;
the forms are in `docs/genius-forms.md`. This file is the list to work down.

> "Build the most complex and full variety version that is logically sound and clever
> while capturing the diversity of humanity." (owner, 2026-11-10)

So variety has to come from somewhere a player can name. A genius is the product of these,
each one a reason and each one seen:

| It comes from | What it sets | How many |
|---|---|---|
| The partner's home | Which kinds are native to them; what the home puts on it | 13 homes |
| The partner's Seed, blood and Shape | Its First Form | the lattice of forms |
| Its age | Its body, its name, its presence | 6 |
| The partner's Seed, Pattern, spark and name | Its coat, markings, build, light | thousands |
| The partner's choices | Coat of three, markings, keepsake, the home's piece on or off | |
| How the partner plays | Every Reading after the first; what it adapts; how it fights when Free | open-ended |
| What it has met | Grafts, shadows | open-ended |

## The home's hand

Where a character grew up shows on their genius twice.

- **The kinds of that home.** Each of the thirteen homes has kinds of its own, the young of
  something from its land, craft or working life, more likely to be offered at the rite to
  a child of that home. (Being built; `docs/genius-forms.md`, "The kinds of the thirteen
  homes".)
- **What the home puts on it** (built). Each home dresses the genii raised there with one
  small piece from its own dress, in its own colours (`data/bodies.json`, `dress.trapping`;
  `tools/blender/genius_trappings.py`): the Academy's brass tag, a marshal's star, a river sash,
  a docker's scarf, a works lens, a bronze disc, a growers' collar, a jewel on blue cloth,
  a string of saffron beads, a jade ring, a tuft of fur on an ochre band, a satchel for one
  page, a knotted cord. It hangs at the collar or the throat beside any keepsake, and the
  partner may take it off on the genius's page. `godot --path . -- --lineage=homes:0` (and
  `:1`, or `homes:edo`) stands a partner from each home beside a genius wearing it.

The pieces are drawn from each home's dress as already written, from tools, cloth and
ornament. None is a sacred object and none stands for a people's faith.

## The cohort's genii

Every classmate has a genius after the rite (built), read by the hero's own rules from that
classmate's blood, Shape and name and from a Seed their temperament gives them (the scared
want something to hold; the proud something that watches from above; `data/academy.json`,
`cohort.temperaments`). It stands at their heel or their shoulder wherever they are, wears
their home's piece, is the same age as the hero's and grows with it, and they wear its echo.
Twelve classmates from twelve cities with twelve different things beside them is the
plainest proof that no two are alike.

## The three tests

Every part of the genius must pass all three. A part that fails one is not finished.

1. **Logical.** A player can say why, in a sentence, from what they did and what it is. A
   pup becomes a wolf. A graft from the dead looks like the dead. A genius that was given
   Hold orders all term stands like something that holds.
2. **Yours.** No two are alike, and the differences come from the character and the play,
   not from a dice roll the player never sees.
3. **Seen.** It shows on the creature, on its partner or in the fight, without opening a
   page. The page explains; it is never the only place.

## The audit

State: **built** (in the game and tested), **part** (works, with a named gap), **plan**
(designed, not built), **open** (needs the owner or a design).

### What it is

| Aspect | The logic | State | What is left |
|---|---|---|---|
| The mote before the rite | The field has not taken a body yet | built | |
| The Seed | A sentence about what you want beside you; it leaves one mark for life | built | The Seed-mark sits where each body has a place for it; three marks show as parts, the rest as eyes or light |
| The First Form | Read from Seed, blood and Shape; three offered | built | Twenty-two First Forms; Wolf, Otter and Shadow are reached only through a blood (decision 72) |
| Its kind, and keeping it | **A genius may always keep its kind**: at every Reading, beside the three forms the Tally reads, it may grow into the next age of what it is, or the elder of its kind (a hawk into a griffin, a kept knife into a living blade) | built | Fourteen kinds name an elder; the rest grow great as themselves. Which is right for each kind is the owner's (below) |
| Its age | Each instar is an age; the young of its kind first | built | Proportions on rigged bodies only; the others need a young body each |
| Its name | The form's, or its young's, or the great of its kind | built | Names of the young and the great are drafts |
| Its size | A pup to taller than its partner | built | One ladder for every Expression (open) |

### What makes it yours

| Aspect | The logic | State | What is left |
|---|---|---|---|
| Coat, markings, build, light | Born with them, from the partner's Seed, Pattern, spark and name | built | The small people take coats but no markings or builds |
| The partner's choices | Coat of three, markings on or off, a keepsake | built | |
| The coat across forms | It wears the nearest coat in the new body | built | Nearest of the three the new body offers it, not of the whole palette |
| Markings across forms | A mask stays a mask | plan | Regions are per body; a map of meanings between bodies |
| Heritage | The same parts carried forward | built | Shown at the Reading only as words; the six-beat Reading shows it |
| Adaptations | On loan from the Tally; fed or they fade | part | The rules run; nothing shows them growing in or greying out |
| Grafts | From a shade, a named beast, kin; in the donor's colour | part | The rules run; the token and the donor's colour are not drawn |
| Its temper | How it behaves at rest and on Free should be the partner's last thirty days of play | plan | Free exists as an order; its model of the partner is not built |

### What it does

| Aspect | The logic | State | What is left |
|---|---|---|---|
| Orders | Guard and Hunt from the First Form; Hold and Free from the Second; Shift, Duet later | part | Guard and Hunt fight; Hold, Free, Shift and Duet are named and locked. Each order needs a posture the player can read across a yard |
| How it fights | By its Expression: a Beast flanks, an Engine holds a line, a Relic fights as part of you | part | The numbers differ by Expression; the *moves* do not. This is the largest gap between the design and the game |
| Its form in the fight | A harrier should not fight like a hawk | plan | A move or two per silhouette, read from its features (talons stoop, a shell braces) |
| Its age in the fight | A pup should not hit like an Apex; an Apex should change the fight | part | Will rises with Resonance; nothing a pup cannot do that a grown one can, except orders |
| Witness and shadows | Ten witnessed uses of a Pattern make a shadow | part | The rules run; marks on the body and the after-image are not drawn |
| Secondary forms | A fold of the same body for another job | plan | Rules in the simulator; nothing in the game |
| Falling | It lies where it fell; three falls cost a form | part | It falls and recovers; no cracks, no season's count shown |
| Resonance | The higher of instar and Pattern tier; each lifts the other | part | Counted; not shown as light |

### How it changes

| Aspect | The logic | State | What is left |
|---|---|---|---|
| The Tally | Kept in the open: what it is learning about you | built | On the page. On the body: nothing yet (the leaning silhouettes) |
| Readiness | It grows and then molts as the Reading nears | built | |
| The Reading | Three read from play, or its own kind | built | The ceremony is a flash; the six beats are designed |
| Crossing Expressions | A Beast can become a Relic if the play says so | built | The change of materials is not staged |
| The lineage | Every form it has been | plan | Saved; not drawn on the page |

### What it does to you

| Aspect | The logic | State | What is left |
|---|---|---|---|
| The echo on the body | Cloak, eyes, field, a piece of what it is | built | Markings, footfall and the shared mantle are proposed |
| The echo in the fight | Resonance: its instars give the Pattern verses | part | Counted in the rules; the player is not told when the genius's growth lengthens their chain |
| The echo in the hall | Others should know a partner by their genius | built | Classmates have genii and wear their echo; their genii do not yet fight beside them on the line |

### After

| Aspect | The logic | State | What is left |
|---|---|---|---|
| The shade | Its final form at the hearth, teaching | part | The Academy's shade speaks; a player's own genius has no end yet |
| The fused | You are your own genius | open | One blood; none of the above applies to it as written |

## What "the best part" needs first

In order of how much each closes the gap between the design and what a player feels:

1. **It fights as what it is.** A move or two per kind of body, a posture per order, and
   an age that matters in the fight. Today every genius guards and hunts the same way. This
   is where "a unique expression of play" is won or lost.
2. **The Reading as a ceremony** (six beats; `docs/genius-progression.md`). The Reading is
   the moment the whole system exists for, and it is a flash.
3. *(Built: classmates have genii you can see. See "The cohort's genii".)* Next: their
   genii fight beside them on the line.
4. **The page tells its life**: the lineage, and where it is leaning.
5. **What shows between Readings**: adaptations, shadows, grafts, falls, Resonance.
6. **Bodies**: a young body for each kind with no rig, and bodies for the forms past the
   Second.

## Calls that are the owner's

1. **Keeping its kind.** It is always offered, beside the three. Should it be? The case
   for: a pup that cannot stay a wolf is not logical. The case against: the Reading was
   written to replace the form with the play ("the hawk is gone, and the player's play is
   standing in its place"). A middle way: keeping its kind is offered only when the Tally
   scores its kind above some line.
2. **Which kinds have an elder** (`data/forms.json`, `growsInto`): hawk to griffin, crow to
   storm-crow, otter to weir-otter, tortoise to cairn-back, clockwork wren to brass kite,
   iron hound to clockwork hound, kept knife to living blade, worn glove to talon relic,
   ledger-imp to contract daemon to the Ledger Closed, lantern-sprite to lamplighter,
   fledgling kith to stooping kith, whisperer to the One Behind, tower-shield hound to
   relic bastion. The rest (the wolf, the ram, the stag, the stove, the buckle and others)
   grow great as themselves.
3. **The names of the great**: "Great Field-wolf" at the Fifth Form, "Field-wolf of the
   Line" at Apex, unless a form has a name of its own for that age.
4. **The order of the list above.**
