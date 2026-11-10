# How a genius's progress shows

The rules of progression are settled (`docs/systems-10-genius-shades.md`): six instars read
at milestones, a Tally kept in the open, heritage carried forward, adaptations that come
and go, grafts, shadows, secondary forms, falls, and the shade at the end. This is the
other half: **what the player sees**, moment to moment and over years, and how it gets
built. It is a plan with a first proof in the game; the calls that are the owner's are at
the end.

The aim in one line: *at any moment a player can look at their genius, without opening a
page, and see what it is, how far along it is, and that it is theirs.*

## The owner's direction (2026-11-10)

> "I want the genius system to be incredibly deep but also logical: if the size is too
> small to be a wolf, maybe it is a pup and evolves into a wolf. I want the final stage to
> be an impressive ally. The process of growth reflected by their design, and the echo
> effect on the player."

Four things follow, and all four are in the game now (see "Ages" and "The echo" below):

1. **A genius has an age, and its body says so.** Each instar is an age: young, half-grown,
   grown, in its prime, great, at its apex. A First Form is the young of its kind.
2. **The name follows the age.** A Field-wolf at the First Form is a *wolf pup*, at the
   Second a *yearling wolf*, and a Field-wolf from the Third.
3. **The last stage is an impressive ally.** An Apex genius stands taller than its partner,
   carries a mantle of light, and lights the ground it stands on.
4. **Its growth echoes on its partner.** Each instar writes something on the partner's own
   body, in the genius's own coat.

## Ages

| Instar | Age | A wolf is | Stands | Its body |
|---|---|---|---|---|
| First | young | a wolf pup | 0.6 m | large head and ears, short legs, short tail |
| Second | half-grown | a yearling wolf | 0.8 m | the head still large for it, the legs coming |
| Third | grown | a Field-wolf | 1.0 m | the creature its name says |
| Fourth | in its prime | | 1.3 m | deeper in the chest; steady lines of light along it |
| Fifth | great | | 1.7 m | long in the leg, the head small for its size; a mantle of five blades of light; the ground lit |
| Apex | at its apex | | 2.3 m | taller than its partner; a mantle of nine; the ground lit for paces round |

How it is built:

- **Names** are in `data/forms.json` (`ages`): a name for each instar at which the form is
  not yet grown. Eighteen forms have them (wolf pup, ram lamb, otter kit, crow fledgling,
  tortoise hatchling, iron whelp, impling, spark, young stag uncrowned, and so on). The
  Reading's rules still speak of the form; only what the player is shown changes, so the
  three scripted lives read as before.
- **Proportions** are scales on the bones of a rigged body, by age and by kind of body
  (`data/genius-bodies.json`, `ages`). The wolf's rig and the small people's take them now.
  A body with no rig (the hawk, the relics, the engines that are not hounds, the Aspects)
  shows its age by size and by what it carries; a young body of its own for each is art
  still to make.
- **Size** is `data/genius.json`, `size`.
- **Presence** (the lines, the mantle, the lit ground) is `data/genius.json`,
  `progression.presence`.

`godot --path . -- --lineage=life` stands a wolf's whole life in a row with its partner
beside it at every age.

## The echo

What a genius's growth writes on its partner (`data/genius.json`, `echo`):

| From | On the partner | Drawn in |
|---|---|---|
| First Form | its colour threads the cloak | the genius's own coat |
| Second Form | its light in the eyes | the field's colour |
| Third Form | the field under the skin, stronger at every instar after | the field's colour |
| Third Form | **a piece that says what the genius is**, larger at every instar after | the genius's own coat |

The piece, by Expression:

| The genius is a | Its partner wears |
|---|---|
| Beast | a ruff of its fur at the collar |
| Kith | a charm at the throat that it made |
| Engine or Relic | a gorget of its metal, with a boss that burns |
| Daemon | a brand over the heart |
| Aspect | motes of its field that keep to the shoulders |

So two partners of the same Shape and city are told apart, at a glance, by what stands
beside them, even when it is not beside them. When a Reading carries the genius into
another Expression the piece changes with it: the partner of a Beast that becomes a Relic
trades the ruff for the gorget.

Not built yet, and proposed as the next echoes: the genius's markings on the partner (a
wolf's mask as a band across the eyes, a hawk's bars on the forearms) at the Fourth Form;
the partner's footfall lit at the Fifth; and at Apex the mantle shared in Union.

## Where it stands today

| Shows now | Does not show yet |
|---|---|
| A new body at each Reading, by form | The change itself: today it is a flash and a swap |
| Height by instar (0.6 m at the First Form to 1.9 m at Apex) | Anything between two Readings: it is the same on day 1 and day 29 |
| The form's parts; a carried part is the same part | Which parts are heritage, which are new, which are on loan (adaptations) |
| The Seed-mark as a part or an eye | Shadows carried, grafts waiting, falls taken |
| Its own coat, markings, build, keepsake; a light that brightens each instar | The coat carried from one form to the next (each form has its own palette) |
| | Resonance (a small body that fights like a Fifth Form looks like a First) |
| | Secondary forms, the shade |

## Four clocks

Progress shows on four time scales, each with its own kind of sign. Nothing here needs a
number on screen.

| Clock | What changes | The sign |
|---|---|---|
| **A fight** (seconds) | Its Will, its order, a fall | The light dims as Will drains and gutters before it falls; its posture is its order (at the heel on Guard, ahead and low on Hunt, planted on Hold); fallen, it lies dark where it fell |
| **A day** (the hearth) | The Tally filling; an adaptation gained or fading; a shadow made; a graft offered | Small, local, and on the body: a part growing in, a part greying, a new mark of light, a token tied on |
| **A season** (between Readings) | Growth, and the Reading coming | It grows part of the way to its next size; near the end it **molts**: seams of light open along the body |
| **A Reading** (a handful in a life) | The form | A ceremony: what it keeps stays lit and is carried across; the rest goes into light |

## Between Readings

**It grows.** A genius does not jump from 0.6 m to 0.8 m at the Gate. Between Readings it
grows part of the way to the next instar's size (three fifths, in the data), in step with
how near the Reading is, so the jump at the Reading is the last two fifths. *Built: see
"The proof".*

**It molts.** In the last stretch before a Reading, seams of light open along its body in
its partner's Shape colour, thin at first, wide and breathing when the Reading is due.
This is the "your genius is ready" signal, and it is on the creature, not in a menu. A
genius whose days are lived but whose milestone is not reached holds just short of the full
molt: the player sees it waiting on them. *Built.*

**Adaptations come in and go out.** An adaptation is a feature on loan from the Tally. When
one is gained its part grows in over a day, raw-coloured (paler than the coat) so it reads
as new. While it is fed it takes the coat's colour. Unfed, it greys from the tip for the
last third of its fade, which is the warning; then it drops. At a Reading an adaptation
that is kept becomes heritage and loses the raw edge for good.

**Grafts wait in plain sight.** A graft offered by a shade, a named beast or kin is taken
at the next Reading. Until then it is carried as a token tied where the keepsake hangs (a
feather, a tooth, a link of chain, in the donor's colour). At the Reading the token becomes
the part, and the part **keeps the donor's colour**, not the genius's coat: a graft from the
dead is visibly from the dead for the rest of its life.

**Shadows are counted on the body.** Each shadow it carries is a mark of light, the
Pattern's own glyph, worn in a row along the flank, the cloak's hem, the blade's flat or
the lantern's glass (a place per Expression). Witnessing a Pattern makes the marks flicker;
the tenth witness draws the new one. When it uses a shadow on Hunt, that mark peels off as
an after-image that performs the Pattern beside it.

**Falls leave a crack.** A fall this season shows as a dark crack through its light, one a
fall. Three cost it its newest secondary form, so the third crack matters and can be seen
coming. The cracks close at the season's turn.

**Resonance is the light, instar is the body.** The body's size and complexity are the
instar's. The light's strength, and the number of rings it throws on the ground under it,
are Resonance (the higher of instar and the Pattern's tier). A character who fires their
Pattern four hundred times and never passes a milestone has a small genius that burns like
a furnace, which is what the rules say it is.

## At a Reading

Today: a flash, a burst, the new body. Proposed, in six beats, about twelve seconds, every
one skippable:

1. **The molt opens.** The seams it has been showing run together; the camera comes in.
2. **The three.** The candidates stand in the light as silhouettes in its own coat, each
   with the lines of the Tally that chose it (as now) and its heritage parts drawn bright.
   The player chooses, or lets it settle.
3. **What it keeps.** The body goes to light along the seams. The heritage parts and the
   Seed-mark do not: they stay lit and hang in the air where they were. The keepsake hangs
   with them.
4. **The new body grows around them.** The silhouette of the chosen form closes from the
   ground up, at the new size, and each kept part travels to its place on it. Heritage is
   literally the same parts carried forward (the lattice already works this way); this
   beat is what makes the player see it.
5. **The coat comes back.** Colour runs over the new body from the kept parts outward, in
   the coat it wore before (see "What stays"), markings last.
6. **The name.** The form's name, the instar, and one line of what was read. The old form
   goes to the lineage on its page.

A Reading that crosses Expressions (a Beast to a Relic) plays the same six beats; beat 4 is
longer, because the materials change (fur to brass), and that crossing is the moment the
system is proudest of.

## What stays, what changes

So that a sixth body still reads as the same creature as the first:

| Stays for life | Changes at a Reading |
|---|---|
| The Seed-mark, in the same place on every body | The silhouette |
| Heritage parts (the same parts) | The Expression's materials |
| **The coat**: its colour family carried to the new body | Size, in steps |
| Markings, by what they mean (a mask stays a mask, socks stay socks) | How many parts it carries |
| The keepsake | How much of it is light |
| The way its light burns (steady, pulse, flicker) | |
| Its build (lean, heavy) | |
| Grafts, in their donors' colours | |

The coat is the one that needs a rule. Each form has its own palette today, so a pale-barred
hawk can become a rust harrier. Proposed: at a Reading the new body takes, from its own
palette, the coat nearest in colour to the one it wore; the player's other two coats are
its neighbours. The page still lets the partner change it.

## Each instar, at a glance

A Fifth Form should read as more than a Second from across the quad, whatever the form.
The body's age is in "Ages" above; this is what else each instar adds.

| Instar | Parts it carries | Light | New at this instar |
|---|---|---|---|
| First | 3 and the Seed-mark | Eyes only | The mote becomes a body |
| Second | +1 heritage | Eyes and one seam | An adaptation can show; one shadow mark |
| Third | +1 | The Seed-mark glows | Secondary forms: it can Shift; two shadow marks |
| Fourth | +1, grafts likely | Lines along the body (built) | It joins the Pattern (Duet): its light takes the Pattern's beat |
| Fifth | A mantle of light (built); a piece of its Expression's own to come (antlers, a banner, a cowl, a halo of gears) | The ground under it is lit (built) | Its tread leaves light |
| Apex | Everything it kept | The field stands around it, with the Pattern's glyph in it | Union |

## Secondary forms, and the end

**Shift** (from the Third Form) is a fold, not a Reading: the same parts and coat, the body
rearranged in its Expression's way (a Beast lowers and broadens into a Mount; an Engine
plants and unfolds into a Ward). One second, 20 Will, and it folds back.

**The shade.** When the partner dies or retires, the genius goes to the hearth in its final
form with the colour drained to hearth-light: the coat's pattern stays as lines of light,
the grafts keep their donors' colours, and its shadows hang round it as small lanterns. A
player who knew it alive should know it at the hearth.

## The page

Two things on the genius's page (J) carry the long view:

- **Its lineage**: every form it has been, small, in a row, in its coat, with the day and
  what unlocked the Reading. The history is already saved; this draws it.
- **The next Reading**: the lines of the Tally that are leading, drawn as faint silhouettes
  of where it is leaning ("toward Kith, toward Relic"), so a player can steer.

## The proof (in the game now)

- `Genius.readiness()`: how near the next Reading is, 0 to 1, from the days lived and the
  milestone. Pure and tested.
- **Growth between Readings** and **the molt seams**, on every art body, driven by it
  (`data/genius.json`, `progression`: how far it grows, when the seams begin).
- **A lineage view**: `godot --path . -- --lineage=life` stands one life in a row at each
  instar's size; `--lineage=molt` stands one genius on the day of the rite, half grown,
  with the seams showing, and with the Reading due.

What the proof shows honestly: a First Form at 0.6 m is small on a platform, and the coat
does not carry from form to form yet.

## Build order

Each step is playable on its own. Sizes: S is a day, M a few days, L a week or more.

| # | Step | Size | Needs |
|---|---|---|---|
| 1 | Readiness, growth and the molt seams | done | |
| 1a | Ages: names, proportions on the rigged bodies, the size ladder | done | |
| 1b | The Apex's presence: lines, the mantle, the lit ground | done | |
| 1c | The echo on the partner: cloak, eyes, field, and a piece by Expression | done | |
| 1d | A young body of its own for each form with no rig (a fledgling hawk, a hand-lantern) | L | art |
| 2 | The Reading as six beats (kept parts hang, the new body closes round them) | M | |
| 3 | The coat carried across forms | S | the coat rule, below |
| 4 | The lineage and the leaning silhouettes on the page | S | |
| 5 | Adaptations growing in and greying out | S | |
| 6 | Shadow marks, and the after-image on Hunt | M | a glyph per Pattern |
| 7 | Resonance as light and ground rings | S | |
| 8 | Grafts as tokens, then parts in the donor's colour | S | |
| 9 | Fall cracks | S | |
| 10 | The mantle at the Fifth Form, one per Expression | M | six pieces of art |
| 11 | Shift, per Expression | L | a second pose or body per form that can shift |
| 12 | The shade's look | M | step 6 |
| 13 | Bodies for the forms past the Second | L | most of them are placeholders today: of eleven forms that begin at the Third or later, three have art |

Steps 2 to 5 are what the Academy can show (it ends at the Second Form). Steps 6 on belong
to the server's years, and step 13 is the large one whenever the game goes past the Gate.

## Calls that are the owner's

1. **Growth between Readings**: three fifths of the way to the next size before the
   Reading. More makes the Reading's jump smaller; none keeps it as it was.
2. **The molt as the ready signal**: on the body, in the Shape's colour. Should a genius
   that is ready but waiting on a milestone look different from one whose Reading is due?
   (It does now: it holds just short.)
3. **The coat carried across forms** by nearest colour, or a fresh coat each form.
4. **Grafts keep the donor's colour** for life.
5. **Resonance as light, instar as body**, so the two can disagree in plain sight.
6. **The six beats of the Reading**, and how long it may run (twelve seconds proposed).
7. **The table of instars**: what each one adds, and the mantle at the Fifth.
8. *(Answered, 2026-11-10: a First Form is the young of its kind. See "Ages".)*
9. **The names of the young** (`data/forms.json`, `ages`): eighteen drafts.
10. **The size ladder**: 0.6 m to 2.3 m. Is an Apex taller than its partner right for every
    Expression (a 2.3 m lantern, a 2.3 m blade), or should the Relics and the small Kith
    have a ladder of their own?
11. **The echo's pieces** by Expression, and that they change when the genius crosses to
    another Expression.
12. **The mantle** is one design for all (blades of light) until each Expression has its
    own.
