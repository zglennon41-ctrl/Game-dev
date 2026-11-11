# The genius in a fight

A genius fights as what it is. This is item 1 of "What 'the best part' needs first" in
`docs/genius-signature.md`: until now every genius guarded and hunted the same way, and one
kind differed from another by two numbers.

Since 2026-11-10 it also fights as its **type** (a weapon is taken in hand, an item is worn
and used, a companion has a role): `docs/genius-types.md`. What is written here is what a
companion does, and what the types are laid over.

What it does in a fight now follows from four things, each of which a player can see:

1. **What it is**: the kind of body it has and the features it carries give it its moves.
2. **How old it is**: its age says how much of that it can do yet.
3. **Its order**: where it stands and what it attends to.
4. **How its partner fights**: on Free, it chooses for itself from the record of their play.

Every number is in `data/genius.json` (`fight`, and the `hold` and `free` blocks of
`orders`). The rules are in `game/scripts/fight.gd` ("the genius"), pure and seeded.

## Moves, by what it is

A move is never given to a form by name. It comes from the **kind of body**
(`data/genius-bodies.json`, `kind`), the **Expression**, and each **feature** the genius
carries, in that order, no move twice, up to three (`fight.byKind`, `byExpression`,
`byFeature`). A form added later gets its moves from what it is made of, with no code; so
does a genius that picks up a feature as heritage, an adaptation or a graft.

| Move | What it does | Who has it |
|---|---|---|
| **Hamstring** | Comes in low: a blow, and the foe is slowed for three seconds | Four-legged bodies; anything with long legs, ground-claws, fangs, fins |
| **Stoop** | Climbs and comes down: one heavy blow, then it must climb again before it can strike | Fliers; anything with wings, talons, a wing-cloak |
| **A shot** | Fires from where it stands | Anything with a barrel or a sight-glass |
| **Mark a debt** | Writes the foe a debt: if the foe strikes its partner while the debt stands, the foe pays (a blow that goes through any guard, heavier for what the partner took) | Daemons; anything with a chain, a ledger, a maw |
| **Lay itself down** | Lies on the ground under the foe for five seconds. What it does there is what it is made of: an ember **burns** what stands on it, rime or a cold core **chills** it (its time runs slow), smoke or a shadow-cloak **darkens** it (blows struck from inside land weakly) | Aspects; anything with those features |
| **Light the ground** | For five seconds its partner reads every wind-up sooner: the moment to parry is half again as long | Anything with a lantern, a glow, a ring of light, far or watching eyes |
| **Call it** | When a strike is wound up at its partner, calls it onto itself: the blow lands on the genius, out of its Will, and the partner is untouched | The small people; anything with a voice, a second face, a mask, a crown, antlers |
| **Brace** | Always: guarding costs it about half the Will, it is ready again sooner, and a blow it guards cannot fell it | Constructs; anything with a shell, a broad chest, stone or iron skin, plate, a shield, set feet |
| **Strike with you** | Always: it is in your hand or on your back, so it is never apart from you, and every third blow of yours it adds one of its own | Relics and other worn or wielded bodies |

Its plain blow between moves is named for its body (a bite, a rake, a cut, a blow, a strike,
a lick of it).

**It has to get there.** A genius has a place on the ground and a speed by its kind: a
flier crosses a yard at once, a four-legged body nearly as fast, the small people at a
walk, a construct slowly; a relic is wherever its partner is. On Hunt it must reach the foe
to strike it; on Guard it must be beside its partner to take a blow for them. So a
lantern on legs is a poor hunter and a good keeper of a place, and a wolf is the opposite,
without a rule saying so.

**Its blows meet an elite's guard like anyone's.** Out of turn they land for the guard's
fraction; in the foe's stagger or recovery they land whole. A debt paid goes through.

What each kind has, by age (the example forms the table below uses):

| Kind (the example) | First Form | Third Form | Apex |
|---|---|---|---|
| beast, runner | a nip | hamstring | hamstring and **Pull it down** |
| beast, flier | a nip | stoop | stoop and **The long stoop** |
| beast, shelled | a nip | hamstring, brace | hamstring, brace and **Pull it down** |
| kith | a nip | call, light | call, light and **The word** |
| engine, hound | a nip | hamstring, brace | hamstring, brace, light and **Pull it down** |
| engine, lantern | a nip | brace, light | brace, light, lay:chill and **The wall** |
| relic | a nip | with | with and **The second hand** |
| daemon | a nip | call, debt | call, debt and **The reckoning** |
| aspect, flame | a nip | lay:burn, light | lay:burn, light and **The weather** |
| aspect, shadow | a nip | lay:dark, light | lay:dark, light and **The weather** |

## Its age

| Age | Its plain blow | Its moves | What only it does |
|---|---|---|---|
| Young (First Form) | A **nip**: almost no damage | None yet | Every third nip, the foe flinches |
| Half-grown | Does damage, a little under its grown worth | The first of them | |
| Grown | Its full worth | Two | |
| In its prime | A little more, and its moves come round sooner | All three | |
| Great | | All three, stronger | **The move only the great have**, at a little over half strength |
| Apex | | All three, strongest | The same move, whole |

The move only the great have is on a long wait (about half a minute at Apex, longer for the
great) and changes the fight when it lands:

| Body | The move | What it does |
|---|---|---|
| Four-legged | **Pull it down** | The foe is thrown down and struck: staggered, its guard open |
| Flier | **The long stoop** | The same, from the sky, harder and shorter |
| The small people | **The word** | The next two blows at its partner are turned |
| Construct | **The wall** | The next three are |
| Relic | **The second hand** | For six seconds every blow of its partner's lands again, for a share |
| Aspect | **The weather** | It lays itself over the whole ground |
| Any Daemon | **The reckoning** | The foe is struck through its guard and written a debt at once |

On Guard a genius keeps to what shields its partner: it will raise the wall or lend the
second hand, but it will not leave their side to pull a foe down.

## Orders

G steps through the orders it has: Guard and Hunt from the First Form, Hold and Free from
the Second. Each has a place to stand, so it can be read across a yard.

| Order | Where it is | What it does |
|---|---|---|
| **Guard** | At its partner's side | Takes the blow they did not see, out of its Will. A caller calls strikes onto itself. It does not strike |
| **Hunt** | On the foe its partner is locked on to (a four-legged one comes round behind it) | Its moves when they are ready, its plain blow between. It does not guard |
| **Hold** | On a piece of ground: the post where the fight has one, or where its partner stood when the order was given. A ring marks it | Strikes and slows whatever comes onto its ground, the pack as well as the locked foe, and guards its partner while they stand on it. It does not follow: off its ground, its partner is alone |
| **Free** | Wherever the order it chooses puts it | Chooses Guard, Hunt or Hold for itself, and says why |

**How Free decides.** Every two and a half seconds it scores each order from what it has
seen of its partner (`orders.free.weights`), and changes only for a clearly better score:

- **Guard** scores by the share of blows its partner has *taken* (over their life together
  and in this fight), and by how far below half health they are now.
- **Hunt** scores by the share of blows they have *parried*, by how much of their fighting
  is close, and by the foe standing open.
- **Hold** scores by how much of their fighting is from far, by the fight having a post,
  and by there being a pack.

So a genius raised by a partner who parries hunts beside them, one raised by a partner who
takes blows guards, and either will keep a post. What it says is the reason that decided
it: "you turn blows yourself", "you take blows", "you are hurt", "there is a post to keep".
The line shows on the HUD beside its order ("FREE: HUNT (you turn blows yourself)"). The
same partner in the same fight always gets the same judgment: there is no chance in it.

For this the genius now counts, over its life, the blows its partner parries, blocks and
takes (`fights.parries`, `fights.blocks`, `fights.hurts`, in the game's Genius only; the
Reading does not read them yet).

Shift and Duet are still locked.

## How it reads

- **Where it is.** On Hunt the body is at the foe; on Hold it stands on its ground inside a
  ring of its partner's Shape colour; a flier that has stooped is up above until it can
  strike again; fallen, it lies where it fell.
- **Each move** shows its name over the place it lands, and a mark of what it does: a pool
  on the ground where it has laid itself (orange, pale blue or violet), a light over its
  partner while the ground is lit, red where a debt is written and where it is paid.
- **The great move** is named large, with a flash and a ring across the ground.
- **The HUD's genius line** shows the order, what Free chose and why, and the move it is
  making.

To look at any of it: `xvfb-run -a godot --path . res://game/tests/genius_shots.tscn --
field-wolf 3 hunt genius-move /tmp/hunt.png` (form, instar, order, the event to wait for,
where to save).

## Measured

`npm run balance:game -- --genii` prints this: a steady hero (raises the guard late two
times in three, strikes in the openings) alone with one genius against the Green's Warden,
four fights a row. The first row is the hero with no genius.

| Genius | Instar | Order | Fells it | In | Its share of the damage | Blows kept off | Will spent | Moves | Falls | Hero left |
|---|---|---|---|---|---|---|---|---|---|---|
| (no genius) | - | - | 4/4 | 24 s | 0% | 0.0 | 0 | 0.0 | 0.0 | 59 |
| beast, runner | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| beast, runner | 1 | hunt | 4/4 | 24 s | 1% | 0.0 | 26 | 0.0 | 0.0 | 59 |
| beast, runner | 3 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| beast, runner | 3 | hunt | 4/4 | 24 s | 7% | 0.0 | 38 | 3.0 | 0.0 | 73 |
| beast, runner | 3 | hold | 4/4 | 24 s | 1% | 0.0 | 4 | 0.8 | 0.0 | 58 |
| beast, runner | 3 | free | 4/4 | 24 s | 9% | 0.2 | 42 | 3.0 | 0.0 | 63 |
| beast, runner | 6 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| beast, runner | 6 | hunt | 4/4 | 17 s | 27% | 0.0 | 56 | 4.0 | 0.0 | 82 |
| beast, runner | 6 | hold | 4/4 | 22 s | 10% | 0.0 | 22 | 1.8 | 0.0 | 67 |
| beast, runner | 6 | free | 4/4 | 18 s | 30% | 0.2 | 58 | 4.0 | 0.0 | 72 |
| beast, flier | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| beast, flier | 1 | hunt | 4/4 | 27 s | 1% | 0.0 | 26 | 0.0 | 0.0 | 56 |
| beast, flier | 3 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| beast, flier | 3 | hunt | 4/4 | 24 s | 7% | 0.0 | 36 | 3.0 | 0.0 | 59 |
| beast, flier | 3 | hold | 4/4 | 24 s | 1% | 0.0 | 3 | 0.5 | 0.0 | 59 |
| beast, flier | 3 | free | 4/4 | 24 s | 9% | 0.2 | 36 | 2.5 | 0.0 | 59 |
| beast, flier | 6 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| beast, flier | 6 | hunt | 4/4 | 17 s | 29% | 0.0 | 53 | 4.0 | 0.0 | 68 |
| beast, flier | 6 | hold | 4/4 | 22 s | 15% | 0.0 | 21 | 1.5 | 0.0 | 68 |
| beast, flier | 6 | free | 4/4 | 17 s | 32% | 0.2 | 49 | 3.0 | 0.0 | 68 |
| beast, shelled | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| beast, shelled | 1 | hunt | 4/4 | 24 s | 1% | 0.0 | 26 | 0.0 | 0.0 | 59 |
| beast, shelled | 3 | guard | 4/4 | 29 s | 0% | 2.5 | 26 | 0.0 | 0.0 | 63 |
| beast, shelled | 3 | hunt | 4/4 | 24 s | 7% | 0.0 | 38 | 3.0 | 0.0 | 73 |
| beast, shelled | 3 | hold | 4/4 | 24 s | 1% | 0.0 | 4 | 0.8 | 0.0 | 58 |
| beast, shelled | 3 | free | 4/4 | 24 s | 9% | 0.2 | 40 | 3.0 | 0.0 | 63 |
| beast, shelled | 6 | guard | 4/4 | 29 s | 0% | 2.5 | 26 | 0.0 | 0.0 | 63 |
| beast, shelled | 6 | hunt | 4/4 | 17 s | 27% | 0.0 | 56 | 4.0 | 0.0 | 82 |
| beast, shelled | 6 | hold | 4/4 | 22 s | 10% | 0.0 | 22 | 1.8 | 0.0 | 67 |
| beast, shelled | 6 | free | 4/4 | 18 s | 30% | 0.2 | 56 | 4.0 | 0.0 | 72 |
| kith | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| kith | 1 | hunt | 4/4 | 26 s | 1% | 0.0 | 22 | 0.0 | 0.0 | 59 |
| kith | 3 | guard | 4/4 | 21 s | 0% | 1.5 | 41 | 4.0 | 0.0 | 91 |
| kith | 3 | hunt | 4/4 | 21 s | 4% | 0.0 | 30 | 2.0 | 0.0 | 88 |
| kith | 3 | hold | 4/4 | 21 s | 0% | 0.2 | 18 | 2.0 | 0.0 | 85 |
| kith | 3 | free | 4/4 | 21 s | 3% | 0.0 | 31 | 2.8 | 0.0 | 88 |
| kith | 6 | guard | 4/4 | 21 s | 0% | 1.5 | 53 | 6.0 | 0.0 | 91 |
| kith | 6 | hunt | 4/4 | 21 s | 9% | 0.2 | 54 | 3.2 | 0.0 | 91 |
| kith | 6 | hold | 4/4 | 21 s | 0% | 0.8 | 38 | 3.2 | 0.0 | 91 |
| kith | 6 | free | 4/4 | 21 s | 8% | 0.2 | 55 | 4.0 | 0.0 | 91 |
| engine, hound | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| engine, hound | 1 | hunt | 4/4 | 26 s | 1% | 0.0 | 25 | 0.0 | 0.0 | 59 |
| engine, hound | 3 | guard | 4/4 | 29 s | 0% | 2.5 | 26 | 0.0 | 0.0 | 63 |
| engine, hound | 3 | hunt | 4/4 | 24 s | 5% | 0.0 | 37 | 3.0 | 0.0 | 73 |
| engine, hound | 3 | hold | 4/4 | 24 s | 0% | 0.0 | 4 | 0.8 | 0.0 | 58 |
| engine, hound | 3 | free | 4/4 | 25 s | 6% | 0.2 | 39 | 3.0 | 0.0 | 60 |
| engine, hound | 6 | guard | 4/4 | 21 s | 0% | 1.2 | 26 | 2.2 | 0.0 | 91 |
| engine, hound | 6 | hunt | 4/4 | 17 s | 20% | 0.0 | 69 | 6.5 | 0.0 | 82 |
| engine, hound | 6 | hold | 4/4 | 21 s | 7% | 0.0 | 39 | 4.5 | 0.0 | 82 |
| engine, hound | 6 | free | 4/4 | 17 s | 20% | 0.0 | 61 | 5.8 | 0.0 | 91 |
| engine, lantern | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| engine, lantern | 1 | hunt | 4/4 | 24 s | 1% | 0.0 | 24 | 0.0 | 0.0 | 59 |
| engine, lantern | 3 | guard | 4/4 | 21 s | 0% | 1.2 | 25 | 2.0 | 0.0 | 91 |
| engine, lantern | 3 | hunt | 4/4 | 21 s | 4% | 0.0 | 30 | 2.0 | 0.0 | 88 |
| engine, lantern | 3 | hold | 4/4 | 21 s | 0% | 0.0 | 12 | 2.0 | 0.0 | 85 |
| engine, lantern | 3 | free | 4/4 | 21 s | 2% | 0.0 | 30 | 2.0 | 0.0 | 88 |
| engine, lantern | 6 | guard | 4/4 | 21 s | 0% | 1.5 | 39 | 3.2 | 0.0 | 94 |
| engine, lantern | 6 | hunt | 4/4 | 24 s | 10% | 0.5 | 83 | 6.8 | 0.0 | 79 |
| engine, lantern | 6 | hold | 4/4 | 21 s | 0% | 0.5 | 32 | 3.2 | 0.0 | 91 |
| engine, lantern | 6 | free | 4/4 | 21 s | 8% | 0.2 | 72 | 6.0 | 0.0 | 91 |
| relic | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| relic | 1 | hunt | 4/4 | 24 s | 1% | 0.0 | 18 | 0.0 | 0.0 | 59 |
| relic | 3 | guard | 4/4 | 26 s | 7% | 1.8 | 32 | 8.8 | 0.0 | 60 |
| relic | 3 | hunt | 4/4 | 23 s | 10% | 0.0 | 17 | 6.5 | 0.0 | 65 |
| relic | 3 | hold | 4/4 | 24 s | 6% | 0.0 | 0 | 7.0 | 0.0 | 59 |
| relic | 3 | free | 4/4 | 23 s | 11% | 0.2 | 20 | 6.8 | 0.0 | 62 |
| relic | 6 | guard | 4/4 | 23 s | 16% | 1.5 | 46 | 9.0 | 0.0 | 66 |
| relic | 6 | hunt | 4/4 | 20 s | 21% | 0.0 | 37 | 6.8 | 0.0 | 68 |
| relic | 6 | hold | 4/4 | 22 s | 12% | 0.0 | 18 | 7.2 | 0.0 | 68 |
| relic | 6 | free | 4/4 | 20 s | 21% | 0.2 | 40 | 7.0 | 0.0 | 65 |
| daemon | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| daemon | 1 | hunt | 4/4 | 26 s | 1% | 0.0 | 20 | 0.0 | 0.0 | 59 |
| daemon | 3 | guard | 4/4 | 29 s | 0% | 3.5 | 57 | 2.5 | 0.0 | 67 |
| daemon | 3 | hunt | 4/4 | 22 s | 10% | 0.0 | 32 | 2.2 | 0.0 | 65 |
| daemon | 3 | hold | 4/4 | 24 s | 2% | 0.0 | 3 | 0.5 | 0.0 | 59 |
| daemon | 3 | free | 4/4 | 24 s | 8% | 1.0 | 42 | 3.0 | 0.0 | 63 |
| daemon | 6 | guard | 4/4 | 29 s | 0% | 3.5 | 59 | 3.0 | 0.0 | 67 |
| daemon | 6 | hunt | 4/4 | 18 s | 31% | 0.0 | 51 | 3.2 | 0.0 | 68 |
| daemon | 6 | hold | 4/4 | 21 s | 13% | 0.0 | 21 | 1.5 | 0.0 | 68 |
| daemon | 6 | free | 4/4 | 20 s | 28% | 1.0 | 60 | 4.0 | 0.0 | 69 |
| aspect, flame | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| aspect, flame | 1 | hunt | 4/4 | 28 s | 2% | 0.0 | 31 | 0.0 | 0.0 | 58 |
| aspect, flame | 3 | guard | 4/4 | 21 s | 0% | 1.0 | 30 | 2.0 | 0.0 | 88 |
| aspect, flame | 3 | hunt | 4/4 | 21 s | 6% | 0.0 | 48 | 4.0 | 0.0 | 88 |
| aspect, flame | 3 | hold | 4/4 | 21 s | 0% | 0.0 | 16 | 2.5 | 0.0 | 85 |
| aspect, flame | 3 | free | 4/4 | 21 s | 5% | 0.0 | 46 | 4.0 | 0.0 | 88 |
| aspect, flame | 6 | guard | 4/4 | 21 s | 0% | 1.0 | 32 | 2.2 | 0.0 | 88 |
| aspect, flame | 6 | hunt | 4/4 | 19 s | 15% | 0.0 | 76 | 5.5 | 0.0 | 88 |
| aspect, flame | 6 | hold | 4/4 | 21 s | 4% | 0.0 | 35 | 3.8 | 0.0 | 88 |
| aspect, flame | 6 | free | 4/4 | 19 s | 14% | 0.0 | 68 | 5.0 | 0.0 | 88 |
| aspect, shadow | 1 | guard | 4/4 | 28 s | 0% | 2.0 | 36 | 0.0 | 0.0 | 60 |
| aspect, shadow | 1 | hunt | 4/4 | 28 s | 2% | 0.0 | 31 | 0.0 | 0.0 | 58 |
| aspect, shadow | 3 | guard | 4/4 | 21 s | 0% | 1.0 | 30 | 2.0 | 0.0 | 88 |
| aspect, shadow | 3 | hunt | 4/4 | 21 s | 4% | 0.0 | 48 | 4.0 | 0.0 | 91 |
| aspect, shadow | 3 | hold | 4/4 | 21 s | 0% | 0.0 | 16 | 2.5 | 0.0 | 86 |
| aspect, shadow | 3 | free | 4/4 | 21 s | 3% | 0.0 | 46 | 4.0 | 0.0 | 91 |
| aspect, shadow | 6 | guard | 4/4 | 21 s | 0% | 1.0 | 32 | 2.2 | 0.0 | 88 |
| aspect, shadow | 6 | hunt | 4/4 | 21 s | 9% | 0.0 | 79 | 5.8 | 0.0 | 90 |
| aspect, shadow | 6 | hold | 4/4 | 21 s | 0% | 0.0 | 35 | 3.8 | 0.0 | 88 |
| aspect, shadow | 6 | free | 4/4 | 21 s | 8% | 0.0 | 72 | 5.5 | 0.0 | 92 |

Reading it:

- **A First Form matters a little.** On Guard it keeps two blows off its partner; on Hunt
  its nips are about a hundredth of the damage and now and then a flinch.
- **Grown, each kind is worth having for a different reason.** The hunters (wolf, hawk,
  daemon, relic) do between a fifteenth and a tenth of the damage. The light-bearers (the kith, the lantern,
  the Aspects) do little damage and leave the hero far healthier and the fight shorter.
  The shelled guard more often for less.
- **An Apex is an impressive ally and not the whole fight.** The hunters do between a fifth
  and a third of the damage and cut the fight by a quarter or more; the hero still does
  most of it.
- **Hold is for a place.** In this table the fight wanders off the genius's ground, so Hold
  scores low; that is the order working as written.
- **The lit ground is strong for this particular hand**, whose guard comes up just outside
  the plain parry window and just inside the lit one. A hand that already parries gains
  little; a hand that never guards gains nothing. The number to tune is
  `moves.light.parryWindow`.

The elites table (`-- --elites`) is unchanged by this work: its heroes carry a First Form
on Guard, which guards as it did.

## Design calls for the owner

1. **The nine moves**, their names, and which features bring which (`fight.byFeature`).
2. **A young genius cannot do its kind's move yet**, and nips. The alternative is a weak
   version of the move from the First Form.
3. **A genius has to be there**: speed by kind, so slow bodies hunt badly and guard a
   moving partner badly. It makes kinds differ a great deal; it also means a lantern
   feels sluggish on Hunt.
4. **On Hunt it does not guard, and on Guard it does not strike.** Free is the order that
   does both, by judgment.
5. **Hold's ground** is the post, or where the partner stood: there is no way yet to point
   at a spot.
6. **Free judges by blows taken and parried, range, health, a post and a pack.** What else
   should it know of its partner (their Shape, their Pattern's Terms, their Discipline)?
7. **The move only the great have**, one a body, and that the great have it at part
   strength before Apex.
8. **How much an Apex should do**: a fifth to a third of the damage against an elite now.
9. **A genius's blows are stopped by an elite's guard** like its partner's. Before this
   they went through.
