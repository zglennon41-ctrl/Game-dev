# The three types of genius

> "I also want to create distinct types of genius: weapon genius should be their own weapon
> usable on a switch with their main weapon, defensive and ritual items should have
> functions in combat, companion genius should fulfill different roles that balance out the
> player. The distinctness of their genius will be the pride of each player."
> (owner, 2026-11-10)

Until now every genius fought the same way: it took orders, guarded or hunted, and one
kind differed from another by its moves. Now what a genius *does* beside its partner
follows from what it is. This is built and playable; the calls it leaves for the owner are
at the end.

Every number here is in `data/genius-types.json` (checked by
`data/schemas/genius-types.schema.json`). The rules are in `game/scripts/fight.gd` ("the
genius's type") and `game/scripts/genius/genius_types.gd`. The older rules it sits on
(moves, ages, orders) are in `docs/genius-combat.md`; the tree is `docs/genius-tree.md`.

## The rule

**A genius's type is its base's.** Nothing is chosen: the 28 bases already say what they
are (`class` in `data/genius-bases/*.json`).

| Type | Bases | What its partner does with it |
|---|---|---|
| **Weapon** | blade, bow, gun | Takes it in hand in place of the weapon they carry, and lets it go again |
| **Defensive item** | shield, gauntlet | Has it on the arm or the hand. Something is always true while they do, and there is one thing they do with it |
| **Ritual item** | lantern, astrolabe, bell | Carries it. The same rule: something always true, one thing done with it |
| **Companion** | wolf, hawk, stag, tortoise, fox, imp, lurker, fiend, drake, sprite, homunculus, ember, fog, moth, octopus, carp, angel, demon, elemental, and the Living Armor (panoply) | Gives it orders. It fights at their side in a **role** that supplies what they lack |

**One key.** The genius's key (**G**; left on a pad's d-pad) does what the type means: it
takes a weapon in hand or lets it go, it uses an item, it steps a companion through its
orders. The HUD says which: the slot marked G on the ability bar names the thing ("Take in
hand", "Set it", "Toll", or the order), shows what it costs and when it is ready again, and
the genius's line reads "IN YOUR HAND", "AT YOUR SHOULDER", "ON YOUR ARM", "AT YOUR BELT",
or "BULWARK · GUARD".

**The type comes from the base, the size of it from the age, the character of it from the
path.** A young genius does a little of what its type does; a great one does a great deal
(`ages`: a First Form is worth 0.6 of a grown one and waits a quarter longer; an apex is
worth 1.3 and waits a quarter less). Each of a base's three paths changes it in one way
that can be said in a sentence. So two players with a blade have two different blades.

**This does not undo "the soul outside the body".** A path is still a trait in a person
and is still earned by how its partner lives (`docs/genius-tree.md`). What a path does in a
fight is written to follow from that trait: the Counting Wolf, the picture of one who
counts heads, mends whoever is hurt; the Scored Blade keeps every blow its partner takes
and pays them back.

**A hybrid** is its first base's type, with that base's paths. **A base with nothing
written** in `data/genius-types.json` fights as every genius did before (a companion with
no role), so a base added later works before anyone has written its type.

## Arms, Regalia, Augments: the equipment geniuses

> "The item type geniuses need to be fixed to actually make narrative sense and mechanical
> scale. A giant bow or misaimed/held firearm is incredibly awkward." ... "They should
> manifest secondary characteristics but stay the same size. It can be a pure aesthetic
> companion form and/or more complex animations for their attacks and design."
> (owner, 2026-11-12)

A genius that is held, carried or worn is **a living thing in that shape**, not a made
object with a soul in it. There are three kinds of them, in the player's words
(`data/genius.json`, `equipment.categories`):

| Category | What it is | Bases now |
|---|---|---|
| **Arms** | A living thing in the shape of a weapon or a shield: melee, ranged, shields | blade, bow, gun, shield, gauntlet |
| **Regalia** | A living thing in the shape of an instrument of office: relics, staffs, crowns | lantern, astrolabe, bell |
| **Augments** | A living thing that is part of its partner: wings, a tail, a light under the skin | none on the tree yet: one proof, below |

**A category is a name over the types, and changes nothing in a fight.** A weapon and a
defensive item are Arms; a ritual item is Regalia; a companion is in none. What each base
does is still its type's, below. The genius's page heads "What it does beside you" with the
category and opens with the category's own sentence; a card says the category before the
kind ("Arms · Bow · Relic · First Form"). A saved genius needs no mapping: its category is
read from its base, which the `renamed` table already carries from old saves.

**The rule of the hand** (`equipment.hand`, `equipment.tolerance`; `GeniusEquip` in
`game/scripts/genius/genius_equip.gd`). A held genius is sized to the hand **at every
stage**. Each base has one length in the hand; every form of it, from Starter to Final, is
brought into that length give or take the tolerance (8%), and with everything it has grown
it reaches no further than `most`. It floats at its partner's shoulder at the same size
(`afloat`). So it does not grow as a creature does: the ages still make it worth more
(`ages`), and what a stage gives it to *show* is secondary characteristics.

| Base | In the hand (a person stands about 2.4) | Measured |
|---|---|---|
| Blade | 1.15 | the whole of it |
| Bow | 1.45 | the whole of it |
| Gun | 0.60 | the whole of it: every form is a thing held in one hand |
| Shield | 0.95 | the whole of it |
| Gauntlet | a hand (its `bulk` brought to 1) | the glove; its cuff and what it holds reach no further than 0.7 |
| Lantern | 0.46 | the whole of it |
| Astrolabe, Bell | 0.36 | the whole of it |

`godot --headless --path . -s res://game/tests/check_items.gd` fails if any form of any
stage is outside its base's length, reaches past `most`, or is larger than its line's
Starter by more than the tolerance; `-s res://game/tests/measure_held.gd` prints the table.
The Blade, the Bow and the Gun are *made* at that size (`tools/blender/lines_weapons.py`
squeezes a form's own length into the rule: a long gun is cut down to its stock and its
lens, a child's bow is strung to the length of any other); the Shield, the Gauntlet and the
three Regalia are made as they were and brought to the rule when the game builds them.

**How each is held** (`data/genius-types.json`, `weapon.bases.*.held` and `mounts`):

- **A bow** is held by its grip in the left hand and drawn with the right. Aimed (drawing,
  loosing, or locked on to a foe), the bow hand is put out from its own shoulder along the
  line to the foe, the bow stands upright on that line a little canted, the string comes
  back to the corner of the jaw with the drawing hand on it (elbow up behind), and the
  arrow of light lies from that hand through the grip. At rest it hangs upright at the side.
- **A gun** is held in the right hand; aimed or fired, its barrel lies along the line to
  the foe with its top to the sky, whatever the wrist is doing.
- **A blade** sits in the right hand as the carried one did.
- **A shield** sits up the forearm (not in the fist) with its top to the sky, so a tall one
  does not hang on its side from an arm at rest.
- A thing held in the left hand or in both puts the carried shield away while it is held.

**Living things.** Every form of the Blade, the Bow and the Gun has an eye that blinks (a
gun's lens is its eye). From the Path it has sinews of the field along it that breathe;
from the Advancement, strings of sinew that sway (a blade, a bow) or gills at the breech (a
gun); at the Final, gills (a blade, a bow) or a string of sinew from the butt (a gun). A
bow's arrow of light breathes on the string. These are pieces of the model moved by name
(`docs/genius-lines.md`, "What moves"). Colour by Path was already the coat's.

**Augments: a first proof.** One line, living wings, is built to be looked at and nothing
more (`tools/blender/augment_wings.py`, `game/scripts/genius/augment.gd`,
`equipment.augments.wings`): five models, one a stage, the same size at all five, hung on
the bone between the shoulder blades and made to the breadth of the wearer's shoulders.
They fold at rest, lift as their partner runs, open on a strike, and breathe.

| Stage | What it shows |
|---|---|
| Baby | down on the arm of the wing, bare quills where the flight feathers will be |
| Starter | plain flight feathers; an eye at each wrist that blinks |
| Path | a second row, banded dark; sinews of the field down the arm |
| Advancement | coverts over the shoulder; an eye of the field on every third feather |
| Final | every feather edged with the field; strings of sinew; a third eye; gills that breathe |

`godot --path . -- --study=wings --augment=wings --stage=4 --body=kazan-f --poses=idle,run,attack --views=back,side --shots=DIR`
There is no Augment on the tree, the rite does not offer one, and **how an Augment fights
is not decided**: see the calls.

`--study=<form>[,<form>]` takes pictures of any held genius on its partner (idle, aiming,
attacking, running; from the quarter, the side, the back): `game/scripts/main.gd`, `_study`.

## Weapons: the blade, the bow, the gun

A weapon genius is a weapon of its own. It has two places.

**At the shoulder** (where it floats when its partner has their own weapon out) it rests:
its Will comes back twice as fast as a companion's, and every third blow its partner lands
it adds one of its own.

**In the hand** (press G) it *is* the weapon. Its partner's own weapon is put away, the
genius's body goes into the hand, and they fight with it:

- **What weapon it is comes from the base**: a blade is three cuts, the third wide; a bow
  is held to draw, and a full draw hits three times as hard; a gun fires from where you
  stand and has no magazine, because its rounds are its Will.
- **How hard it hits comes from its age**: from the First Form it is as good as a named
  weapon of its kind (1.2 times a plain one); grown, 1.7 times; at its apex, 2.4 times.
- **It spends its own Will.** Each blow costs it some (a blade 2.5, a gun 3.5, a bow 4),
  and it gets none back while it is held. When it has too little for another blow it leaves
  the hand of itself, the press goes to the carried weapon, and it cannot be taken up again
  until it has rested back to three tenths of its Will. So it is a burst, and choosing the
  moment is the skill.
- **The switch is fast.** It changes hands at once, from a free hand or the end of a swing,
  a reload or a draw. Taken up after two and a half seconds of rest and struck with at
  once, the first blow is **the cut of the draw**: it starts in six tenths of its time and
  lands a quarter harder.
- **Each path gives it one property**, below.
- A partner who has been disarmed (the Toll) cannot take it up either.
- Its great move is still **The second hand** (`docs/genius-combat.md`).

## Defensive items and ritual items

An item is not sent anywhere and does not fall. It is with its partner, and two things are
true of it:

1. **Always**: something is true of its partner for as long as it is theirs, with no key.
   It is small at the First Form and grows with age.
2. **The key**: one thing its partner does with it, on a wait, paid for from the item's
   own Will. With too little Will the key does nothing.

Each of its three paths bends one or the other. The five items, in a line each (there were six: the Coat, the one genius that was worn on the
body, became the Living Armor, a companion, on 2026-11-12, and nothing is worn any more):

| Item | Always | The key |
|---|---|---|
| **Shield** (on the arm) | Blocked blows land for less and cost less Will | **Set the shield**: the next blow at you, from anywhere, it takes whole |
| **Gauntlet** (on the hand) | The moment to parry is longer | **Catch it**: reach for a foe that is winding up and the strike is caught before it is thrown |
| **Lantern** (at the side) | Blows you neither turned nor blocked land for a little less | **Set it down**: a lit circle where the moment to parry is half again as long |
| **Astrolabe** (at the shoulder) | Each strike you parry, block or dodge is a measure of the foe; each measure adds to your blows on it | **Take a sight**: for seven seconds your blows in the foe's weak moment land much harder |
| **Bell** (at the belt) | Your Pattern's chain moments are wider; a parry gives back a little more Will | **Toll**: every foe near you that is winding up is broken out of its strike |

Shield and lantern have a great move, **The wall**. The gauntlet, the astrolabe
and the bell keep whichever great move their body already had (a call, below).

## Companions: five roles

A companion keeps everything it had (its moves by what it is, its ages, the four orders:
`docs/genius-combat.md`). On top of that its base gives it a **role**: what it is for.

| Role | What it supplies | Where it stands | Its numbers | The one thing only it does |
|---|---|---|---|---|
| **Bulwark** | A front, for a partner who fights from far off or cannot take a blow | Between its partner and the foe | More Will, lighter blows, guards for less and sooner | **Holds it**: calls the foe onto itself. For a few seconds the foe goes for the genius, and its strikes land on the genius, out of its Will |
| **Hunter** | The blow, for a partner who turns every strike and has too little to put in the opening | On the foe | Harder, quicker blows, a little less Will | **Goes for the opening**: its blows on a staggered or open foe land half again as hard, and it comes at once when the foe staggers |
| **Harrier** | The opening, for a partner whose blows are heavy and slow | Behind the foe | Light, fast blows; quick on its feet | **Worries it**: for three seconds the foe's guard is down and every blow on it lands nearly a third harder |
| **Keeper** | Staying, for a partner who takes a blow to give one | At its partner's side | More Will, the lightest blows | **Mends**: while its partner is hurt and nothing has struck them for a moment, it gives them health out of its own Will. In a party it sees to whoever is worst hurt |
| **Lookout** | The moment, for a partner who is struck by what they did not see | Behind its partner | Slightly lighter blows, quick | **Calls the strike**: while it watches, the moment to parry is a third longer, and when the foe has struck and missed it calls the opening: blows land a fifth harder until the foe recovers |

- **A role's own thing works from the First Form**, at the worth of its age. The nine moves
  still wait for age, as before.
- **A role favours moves.** Of the moves its body gives it, a companion keeps first the
  ones its role favours, and makes them a fifth sooner.
- **Each path shades the role.** One of a base's three paths keeps to the role (its own
  thing is 1.3 times as strong); the other two lean toward another role, and have that
  role's own thing as well at half strength. A wolf is a Hunter; a Counting Wolf is a
  Hunter that also mends.
- **A strike it holds is the genius's.** Once the foe has wound a strike up at a genius
  that holds it, that strike is thrown at the genius even if the hold's time runs out
  first, and it does not bite the partner in passing. Whatever its role, a genius that
  holds the foe comes round to stand between the foe and its partner while it does.
- **The page says whether its partner needs it.** A genius's page has a section "What it
  does beside you" that names the type or role, what is always true, what the key does and
  what its path changed, and for a companion one line from how its partner actually fights:
  "As you fight now, it is what you lack", "you have some need of it", or "you could do
  without it; it does it all the same" (`need` in the data). Nothing is chosen from that
  line yet (a call, below).

## Every base

Printed from the data by `python3 tools/genius-types-table.py` (run it again after changing
`data/genius-types.json`; `--check` says only whether every base and path is written).

### Weapons

| Base | In the hand | Its paths, and the one property each gives it |
|---|---|---|
| **Blade** | A blade: three cuts, the third wide. Each blow costs it 2.5 of its Will. | **Duelling Blade** (The answer): After a parry made with it in hand, its next blow within a second and a half lands nearly twice as hard and costs it nothing. The moment to parry is a little longer while you hold it.<br>**Cleaver** (No guard): Every cut is a fifth heavier and the third throws the foe back. The moment to parry is shorter while you hold it: a guard is time not spent cutting.<br>**Scored Blade** (The score): Every blow you take is cut into its flat, up to five. The next blow that lands with it pays them all back: a seventh harder for each. |
| **Bow** | A bow: hold to draw, and a full draw hits three times as hard. Each blow costs it 4 of its Will. | **Hunting Bow** (The first arrow): Each time you take it up after it has rested six seconds, its first arrow from a full draw lands twice as hard. The shot is the last and smallest part of a hunt.<br>**War Bow** (Covering arrows): An arrow that lands while the foe is winding up takes the weight out of that strike: it lands for half, on you or on whoever it was meant for.<br>**Singing Bow** (The note): An arrow from a full draw leaves its note in the foe: for two and a half seconds the foe's time runs slow. |
| **Gun** | A gun with no magazine: its rounds are its Will, so it is never reloaded. Each blow costs it 3.5 of its Will. | **Long Gun** (The long shot): It reaches as far as a musket and is slower between shots, and a shot lands harder the farther off the foe is: half again as hard and more from sixteen metres.<br>**Repeater** (The second shot): It comes back to the aim sooner, and every second shot in a row lands half again as hard.<br>**Standing Gun** (Feet set): Fired from a stand, when you have not moved for most of a second, its shots land two fifths harder. |

### Defensive items

| Base | Always | The key | Its paths, and how each bends it |
|---|---|---|---|
| **Gauntlet** (on your hand) | **A sure hand.** The moment to parry is longer. | **Catch it.** Reach for a foe that is winding up, from close: the strike is caught before it is thrown, and the foe flinches. Reach for nothing and the hand closes on air. Every 10 seconds, for 9 of its Will. | **Maker's Hand**: What it catches it takes apart: for two and a half seconds the foe's guard is down and every blow on it lands a sixth harder.<br>**Fighting Fist**: The catch is a blow: it strikes as it closes and throws the foe back. Between catches it strikes with you: every third blow of yours it adds one.<br>**Open Hand**: It reaches across the ground for a strike wound up at a classmate. And once a fight, when a blow would fell you, it catches you: you are left standing. |
| **Shield** (on your arm) | **Shield arm.** A blow you block lands for less, and a blocked blow costs you less Will. | **Set the shield.** For a moment the shield is set: the next blow at you, from anywhere, it takes whole. Every 9 seconds, for 8 of its Will. | **Wall-shield**: It takes two blows, not one, and stays set nearly twice as long.<br>**Gate-shield**: It is set on the ground where you stand, as a door: for six seconds it takes the blows at you, and at any classmate, while you stand by it. Three blows.<br>**Shelter-shield**: Set, it covers whoever is struck first: you, or a classmate within eight metres. It is ready again a third sooner. |

### Ritual items

| Base | Always | The key | Its paths, and how each bends it |
|---|---|---|---|
| **Astrolabe** (at your shoulder) | **It takes the measure.** Each strike of a foe that you parry, block or dodge is a measure of it, up to five; every measure adds a little to your blows on that foe. | **Take a sight.** The foe you are locked on to is sighted. For seven seconds your blows in its weak moment, when it is staggered or recovering from its own strike, land more than half again as hard. Every 14 seconds, for 8 of its Will. | **Sighting-glass**: From seven metres or more, your blows on a sighted foe land a third harder at any moment, weak or not.<br>**Orrery**: It has worked the strike out. Against a sighted foe the moment to parry is much longer, and a parry staggers it most of a second longer.<br>**Almanac**: It writes it down. The sight lasts longer and comes round sooner, and what it has measured of one kind of beast it keeps for the next of that kind. |
| **Bell** (at your belt) | **It keeps the time.** The moments of your Pattern's chain are a little wider, and a parry rings it: you get a little more Will back. | **Toll.** It tolls. Every foe near you that is winding up is broken out of its strike, and you are steadied: a little Will back. Every 13 seconds, for 9 of its Will. | **Rally-bell**: Its toll steadies the whole table: you and every classmate in hearing get health back, and you twice the Will.<br>**Hour-bell**: It keeps better time: your Pattern's moments are wider still. And every twenty-two seconds, when a strike is wound up at you, it tolls of itself.<br>**Alarm-bell**: It does not startle, it stuns: what its toll breaks is staggered and struck. It is longer coming round again. |
| **Lantern** (at your side) | **Nothing comes unseen.** A blow you neither turned nor blocked lands for a little less: you saw it coming, at least. | **Set it down.** It is set on the ground where you stand and lights a circle. Inside it the moment to parry is half again as long, and a parry staggers the foe longer. Every 16 seconds, for 8 of its Will. | **Wayfinder**: It is set at the foe's feet. A guarded foe standing in its light is found out: blows out of turn land for half again what its guard would let through.<br>**Watch-lamp**: It burns half as long again, and blows at you or a classmate standing in its light land for a fifth less.<br>**Kept Flame**: What stands against you in its light burns, and your Will comes back half again as fast while you stand in it. |

### Companions

| Base | Role | Its paths, and the role each leans toward |
|---|---|---|
| **Angel** | Keeper | **Shoulder-angel** (keeps to the Keeper): It has chosen whose side it is on: it mends more.<br>**Clarion** (toward the Lookout): It says so before it happens: it calls the strike.<br>**Weigher** (toward the Hunter): It believes in what is deserved: heavier into every opening. |
| **Carp** | Bulwark | **Weir-leaper** (keeps to the Bulwark): It does not go round: it holds the foe longer.<br>**Still-water Carp** (toward the Keeper): It makes the place it stays in deep: it mends who rests by it.<br>**Silt-reader** (toward the Lookout): It feels it in the floor: it calls the strike. |
| **Demon** | Hunter | **Exile** (toward the Lookout): It stands a little apart, where it can see: it calls the strike.<br>**Advocate** (toward the Harrier): It puts the other side of it to the foe: the guard is down longer.<br>**Head-down** (keeps to the Hunter): It puts its head down and goes through: heavier into every opening. |
| **Drake** | Bulwark | **Hoard-drake** (keeps to the Bulwark): It counts you among what it keeps: it holds the foe longer.<br>**Fire-drake** (toward the Hunter): It keeps the fire in until it is wanted: then into the opening, unstinted.<br>**Sky-drake** (toward the Lookout): From higher up it sees the strike coming, and calls it. |
| **Elemental** | Harrier | **Cornerstone** (toward the Bulwark): It stands where it stood: it takes the foe on itself.<br>**Tideling** (keeps to the Harrier): It always comes back at the foe: the guard is down longer.<br>**Squall** (toward the Hunter): It is suddenly there: it strikes hard into what it opened. |
| **Ember** | Hunter | **Kept Fire** (toward the Keeper): Near enough to warm: it mends.<br>**Rushlight** (toward the Lookout): A small light in a bad place: it calls the strike.<br>**Wildfire** (keeps to the Hunter): It spends the whole of itself: heavier into every opening. |
| **Fiend** | Hunter | **Flare-up** (keeps to the Hunter): It does not come down until something has paid: heavier into every opening.<br>**Banked Coal** (toward the Harrier): It has a list: it worries the one it is waiting for.<br>**Grate-fiend** (toward the Keeper): It learned to be warm: it mends. |
| **Fog** | Harrier | **Fog-shroud** (toward the Bulwark): It gets in the way gently: it takes the foe on itself.<br>**Lingering Mist** (toward the Lookout): It stays and listens: it calls the strike.<br>**Shifting Fog** (keeps to the Harrier): It cannot be pinned: the guard is down longer. |
| **Fox** | Harrier | **Gone-away** (keeps to the Harrier): It is never where the foe looks: the guard is down longer.<br>**Cache-fox** (toward the Keeper): It brings you what it buried: it mends between worries.<br>**Fire-tail** (toward the Bulwark): The foe follows its light: it draws it off you. |
| **Hawk** | Lookout | **High Circler** (keeps to the Lookout): It sees the whole of it: the moment to parry is longer still.<br>**Eyrie-holder** (toward the Bulwark): It keeps the high place: it draws the foe's eye and holds it.<br>**Stooper** (toward the Hunter): It chooses once: it comes down hard into an opening. |
| **Homunculus** | Keeper | **Clay Apprentice** (keeps to the Keeper): It does the next thing before you have got to it: it mends more.<br>**Likeness** (toward the Hunter): It fights like you: it strikes into your openings.<br>**Clay Bearer** (toward the Bulwark): It chose your purpose: it takes the foe on itself. |
| **Imp** | Harrier | **Debt-collector** (toward the Hunter): It goes and gets it: it strikes hard into what it opened.<br>**Stickler** (keeps to the Harrier): It holds the foe to the letter: the guard is down longer.<br>**Surety** (toward the Bulwark): It put its name under yours: it takes the foe on itself. |
| **Lurker** | Lookout | **Back-stander** (toward the Bulwark): It fills the place behind you: it takes the foe onto itself.<br>**The One Who Sits Up** (toward the Keeper): It sits up with the hurt: it mends.<br>**The Unremarked** (keeps to the Lookout): It sees from where it is not seen: the moment to parry is longer still. |
| **Moth** | Lookout | **Candle-moth** (toward the Hunter): It goes where the fire is: heavier into every opening.<br>**Emperor** (toward the Bulwark): It opens its eyes at the foe: the foe looks at it, and not at you.<br>**Moon-moth** (keeps to the Lookout): It keeps its one far light in view: the moment to parry is longer still. |
| **Octopus** | Keeper | **Many-hands** (keeps to the Keeper): It has an arm for everyone: it mends more.<br>**Latch-lifter** (toward the Harrier): It finds where the foe is fastened: it worries the guard open.<br>**Sleeps-on-it** (toward the Lookout): It has dreamed the foe already: it calls the strike. |
| **Living Armor** | Bulwark | **Sworn Plate** (keeps to the Bulwark): It has chosen its few and stands before them: it holds the foe longer.<br>**Siege-plate** (toward the Harrier): It goes through what is shut: it breaks the foe's guard.<br>**Wayfarer's Harness** (toward the Lookout): It keeps the watch at the edge: it calls the strike. |
| **Sprite** | Keeper | **Hob** (keeps to the Keeper): Somebody has to mind the house: it mends more.<br>**Lore-sprite** (toward the Lookout): Knowing is a light too: it calls the strike.<br>**Pixy** (toward the Harrier): Other eyes go after it: it worries the foe. |
| **Stag** | Bulwark | **Tilter** (toward the Hunter): Its head goes down: held, the foe is struck hard when it opens.<br>**Wood-walker** (toward the Harrier): It leads the foe a dance: it worries it between holds.<br>**Watch-hart** (keeps to the Bulwark): It walks at the back and stands between: it holds the foe longer. |
| **Tortoise** | Bulwark | **Stone-back** (keeps to the Bulwark): It will not be moved: it holds the foe longer.<br>**Cairn-back** (toward the Keeper): It is a post that travels: it mends who rests by it.<br>**The Unhurried** (toward the Hunter): It arrives anyway: its few blows land in the openings. |
| **Wolf** | Hunter | **Counting Wolf** (toward the Keeper): It counts heads between bites: it mends whoever is hurt.<br>**Third-day Wolf** (keeps to the Hunter): It does not let go: its blows in an opening are heavier still.<br>**Night-watch** (toward the Lookout): It does not sleep: it calls the strike you would not have seen. |

Roles across the twenty: five Bulwarks (stag, tortoise, drake, carp, the Living Armor), four
Hunters (wolf, fiend, demon, ember), four Harriers (fox, imp, elemental, fog), four Keepers
(sprite, homunculus, octopus, angel), three Lookouts (hawk, lurker, moth). Every base has one
path that keeps to its role.

## What the genius learns from it

A weapon or an item takes no orders, but the Reading still reads the orders line of the
Tally, and paths lean on it. So what its partner does with a weapon or an item is counted
there (`tally` in the data):

- **A weapon.** A blow landed with it in hand counts a third toward Hunt, or toward Hold
  if it was struck from a stand (feet set for most of a second, or on the fight's post). A
  blow parried or blocked with it in hand counts toward Guard. A blow it adds from the
  shoulder counts toward Free.
- **An item.** Each use counts toward the line that use is for (the shield's toward Guard,
  the lantern's and a gate-shield's toward Hold, the bell's, the gauntlet's and the
  astrolabe's toward Hunt), and a blow landed just after a use
  counts a half toward Hunt.

## How it reads

- **The HUD**: the G slot and the genius's line, as above. With a weapon genius in hand,
  the attack slot is named for it.
- **In the world**: a weapon genius in the hand is drawn in the hand, seated where its own
  model says the hand closes on it (an empty named `grip`), and the carried weapon is not
  drawn. An item is drawn where it is worn (`mounts` in the data, by its base's `worn`):
  a shield in the left hand, where a carried shield would be (and a carried one is not
  drawn under it), and a gauntlet on that hand, each by its own `wear`; a lantern at the hip, a bell at the belt and an astrolabe afloat at the
  shoulder, each hung by its own ring (`carry`), upright whatever its partner's body does,
  at the height its form says it has in the hand (`held`) times the mount's `scale`.
  `godot --path . -- --fight --genius=<form id>:3 --near` (or `--near=back`) brings the
  camera close to see it. A set shield, a caught strike, a slip,
  a toll, a sight and a mend each show their name over the place and a ring or a flash; a
  lantern set down lights a warm disc on the ground; a gate-shield draws its door as a ring.
- **The genius's page** (J): the section "What it does beside you". Orders are listed only
  for a companion.
- **The lessons**: where a lesson names the key, it now says what the key does for the
  genius that student has ("G takes it in hand, and lets it go again").

## What the tables say

`npm run balance:game -- --types` plays every base against the Warden of the Cutting and
prints four tables (about ten minutes; `-- --types=wolf` for one base). The fights are
played by the game's own bots, which use the key. Six fights each.

**1. Every base, beside a steady saber hero, the Warden at twice its health.** Alone: wins
6 of 6 in 44 seconds with 37 health left.

| | First Form | Third Form | Apex |
|---|---|---|---|
| **Hunters** (wolf, ember, fiend) | 44 s, wins 3 to 6 of 6 | 35 s, 51 to 68 health | 22 to 27 s, 69 to 73 health; the genius does a third to a half of the damage |
| **Harriers** (fox, imp, fog) | 40 to 43 s, wins 4 or 5 of 6 | 34 to 45 s | 25 to 39 s, 39 to 73 health |
| **Bulwarks** (stag, tortoise, drake) | 48 s, wins 4 of 6 | 58 to 60 s, 67 to 88 health | 71 to 76 s, 90 to 92 health; it takes about twenty strikes |
| **Keepers** (sprite, homunculus) | 46 s, 71 health | 44 to 47 s, 74 to 81 | 44 to 47 s, 80 to 88 |
| **Lookouts** (hawk, lurker) | 46 s, 51 health | 44 to 52 s, 62 to 71 | 44 to 54 s, 66 to 71 |
| **Blade** | 43 s, 37 health | 40 s, 47 | 35 s, 53 |
| **Bow**, **gun** (with a saber) | 44 s, wins 5 of 6 | 37 to 42 s, 5 of 6 | 37 s |
| **Shield** | 62 health | 72 | 84 (38, 38 and 62 if its key is never pressed) |
| **Gauntlet** | 61 | 63 | 65 (37 if never pressed) |
| **Bell** | 57 | 70 | 89 |
| **Lantern** | 41 | 57 | 79 |
| **Astrolabe** | 43 s, 39 health | 40 s, 45 | 40 s, 49 |

Read plainly: Hunters and Harriers end the fight sooner; Bulwarks, Keepers and the
defensive items end it with more health and Bulwarks take much longer about it; no row is
best at both. Items do nothing to the length of this fight, because this hero's damage is
mostly its Pattern, and no type touches the Pattern.

**2. A grown companion of each role beside four different partners.**

| Companion | Far (a musket) | Heavy (a maul) | Turner (a saber, every strike parried) | Brawler (twin blades, still learning) |
|---|---|---|---|---|
| none | loses 6 of 6 | 91 s, 79 health | 36 s, 91 health | loses 6 of 6, the Warden at 79% |
| **Bulwark** | **wins 6 of 6** | 97 s, 94 | 57 s, 96 | loses, the Warden at 33% |
| **Hunter** | loses | **57 s**, 89 | **32 s**, 91 | loses, at 65% |
| **Harrier** | loses | **57 s**, 83 | 36 s, 73 | loses, at 60% |
| **Keeper** | loses (gets it to 37%) | 91 s, **97** | 38 s, 91 | loses, at 47% |
| **Lookout** | wins 5 of 6 | 99 s, 94 | 36 s, 94 | wins 1 of 6 |

Each role is the best answer for a different partner and none is the best for all four:
the far partner cannot win without a Bulwark or a Lookout; the heavy one is fastest with a
Harrier or a Hunter and safest with a Keeper; the turner is fastest with a Hunter.

**3. A second reach.** A hero with a musket and a blade genius loses 6 of 6 alone and with
the key never pressed, and wins 2 of 6 pressing it. A saber hero with a bow or a gun genius
does no better for taking it in hand (5 of 6 against 6 of 6): the bots fight close and
seldom use a ranged genius well.

**4. A learner's First Form, against the Warden as it is.** A "learning" hand with a saber
wins 3 of 6 alone. It wins 6 of 6 with any Bulwark, Keeper or Lookout, a shield, a gauntlet
or a gun; 4 of 6 with a bell or a lantern (and, when there was one, a coat); and still 3 of 6 with a Hunter, a
Harrier, a blade, a bow or an astrolabe. A "new" hand, which does not parry or use the key,
loses with everything, as before.

Known soft spots in these tables: a young Bulwark beside a hero who already parries
everything is a poor match (30 s and 47 health, against 22 s and 69 alone), because it
takes the strikes that hero would have parried and spends the Will it would have guarded
with; young Hunters and Harriers cost that same hero a little for the same reason (their
nips make the foe flinch out of strikes he would have turned), which was so before the
types; and Fog down its first road is the weakest companion in table 1.

## To see it

- `npm run test:game` — the game's tests (2261 pass; the types have about 160 of them)
- `npm run validate` — checks `data/genius-types.json` against its schema and the bases
- `npm run balance:game -- --types` — the four tables above; `-- --genii` and `-- --elites`
  as before, with bots that use the key
- `godot --path . -- --fight --genius=blade-duelling:3` — the practice yard beside
  any genius at any form and age (`--genius=<form id>:<instar>`, and `--weapon=<weapon id>`
  for the weapon carried). Press G.
- `godot --path . -- --page=<form id> --fresh` — that genius's page

## Where it lives

| What | Where |
|---|---|
| Every number and sentence | `data/genius-types.json`, schema `data/schemas/genius-types.schema.json` |
| Reading the data: type, path, role, the page's words, the bots' use of the key | `game/scripts/genius/genius_types.gd` |
| The rules in a fight | `game/scripts/fight.gd`, "the genius's type" |
| The HUD slot and line | `game/scripts/hud.gd` |
| The body in the hand, the marks in the world | `game/scripts/world.gd` (`_update_form`, `_genius_ground`) |
| The page | `game/scripts/genius/genius_page.gd` (`_does_section`) |
| Tests | `game/tests/run_tests.gd` (`test_types_*`), `tests/types.test.ts`, fixtures in `game/tests/fixtures/types.json` |
| The tables | `game/tests/balance.gd` (`--types`), `tools/genius-types-table.py` |

## The calls that are the owner's

**On the equipment geniuses (2026-11-12):**

- **How an Augment fights.** Nothing is built. The options: (a) it is a fourth type with a
  key of its own (wings: a leap or a glide out of a strike; a tail: a third hand that
  catches or trips; tattoos: a charge that is spent); (b) it has no key and only an
  "always" (wings: a longer dodge; a tail: balance, so less knockback), so the G key is
  free for something else; (c) it borrows the companion's roles (wings a Lookout, a tail a
  Harrier) without leaving the body; (d) it changes its partner's own moves (the dodge
  becomes a short flight) rather than adding one.
- **Where an Augment comes from.** A new base on the tree offered at the rite like any
  other (then each needs 31 forms and their words), or something a person already has from
  their blood that a genius wakes.
- **The Gauntlet's category.** It is sorted into Arms (it catches a strike; it is worn like
  a shield). It could as well be an Augment (a living hand).
- **The Starters' names.** At one size the Kept Knife is as long as a sword and the Pocket
  Piece as long as a horse-pistol: their names say something smaller. Rename them, or make
  the Blade's and the Gun's hand-size the knife's and the pocket pistol's.
- **Staffs and crowns** (Regalia) are not built: proposals are in the worker's report.
- **A cloak and a pair of wings want the same place** on a back.

These are built the obvious way so the game is playable; each is a design decision and is
yours to change.

1. **The five roles, their names, and who has which.** Bulwark, Hunter, Harrier, Keeper,
   Lookout; which base has which, and which role each path leans toward, are in the table
   above. All of it is one line per path in the data.
2. **A weapon or an item no longer takes the blow you did not see.** Before, every genius
   on Guard did, so every First Form protected a learner. Now only companions take orders.
   The cost shows in table 4: a learner with a blade, a bow or an astrolabe is no safer
   than one with no genius. The other choice: a weapon at the shoulder and an item still
   take the unseen blow, at a price, and the types are a little less distinct.
3. **A weapon in the hand spends the genius's own Will and leaves the hand when it is
   spent.** That makes it a burst weapon and makes the switch a decision. The other choice
   is a second weapon that costs nothing to hold, in which case the better of the two is
   simply always in hand.
4. **A gun genius has no magazine**: it is never reloaded, and its rounds are its Will.
5. **A disarmed partner cannot take their genius in hand.** The other choice (the genius is
   the one weapon nothing can take from you) would be a strong thing to be able to say.
6. **What a weapon or an item teaches the genius** (the Tally table above). It decides
   which paths open to a player whose genius takes no orders.
7. **A caught, tolled or shielded strike is not a parry.** So it does not answer a
   Pattern's "after a perfect Hold", and these items are worth most to a player who does
   not parry yet and take something from one who does. Should a catch count as a parry?
8. **A role's own thing works from the First Form** (at six tenths), though its moves wait
   for age. This is what lets a young Keeper or Bulwark carry a learner.
9. **Should the rite lean toward what its partner lacks?** You asked for roles "that
   balance out the player". Today a genius's base still comes from the bowl as before (the
   region's leans and the Tally), and the page only *says* how much its partner needs its
   role. The measure exists (`need`); using it to weight the three bases the bowl offers,
   or the path at a Reading, is a rule about who gets which soul, so I did not make it.
10. **A hybrid has one type**, its first base's. A wolf turned toward the blade is a
    companion with the wolf's role; it cannot be taken in hand.
11. **No type touches the Pattern** (except the bell's wider chain moments). So for a
    practiced player a genius changes a hard fight by roughly a tenth to a half, most for
    Hunters. Is that the right size for "the pride of each player"?
12. **Great moves.** Weapons keep The second hand; the shield and the lantern have The
    wall; the gauntlet, the astrolabe and the bell have none written for them.
13. **Every number.** Waits, costs and strengths are first guesses tuned only until the
    tables above read sensibly.

## What is not done

- **Worn items are small.** A lantern at the hip is a hand tall and an astrolabe at the
  shoulder smaller, as they would be; from the fight's camera they read as a shape and a
  light, not as the form they are. They are drawn a third larger than life for that
  (`mounts.*.scale`); how large they should be is the owner's call. Set down, each stands
  at its own full height.
- **No animation of its own.** Every new thing is marked by a name, a ring, a flash or a
  light, not by a movement of the genius or its partner.
- **Classmates' genii have no types in a fight.** Only the player's genius does.
- **No lesson teaches the key.** Two lesson texts say what G does; nothing drills it.
- **Elites were not re-tuned** for a party whose genii do more.
- **Bots seldom use a bow or a gun genius well** beside a melee weapon, so its tables
  understate it.
- **Shift and Duet** are still locked, and the TypeScript simulator has no fights, so
  nothing of this is in it.
