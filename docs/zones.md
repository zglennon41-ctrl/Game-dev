# Zones: the ground the line runs through

The world outside the Academy's walls is four **zones** around Alexandria, one per stretch
of line (`data/zones.json`). The Academy's excursions, Lesson 5, the Field Examination and
the board's quests all take place in them. Everything here is data: a designer adds an area,
a beast or a tile without touching code.

## What a zone is

| Field | Meaning |
| --- | --- |
| `line`, `colour` | the line it lies on (Columbia or Cahokia) and the line colour of the zone; `colourDeep` is the colour past its post |
| `light` | the zone's night: sky, ambient, fog, moon and the moon's colour |
| `tiles` | the tile library: `floor` tiles by weight, `edge` pieces by weight, `props` as `[piece, radius, weight]` (radius 0: walk-through) |
| `beasts` | `common` (the pack), `elite` (the zone's one named boss, who stays down), `named` (beasts that remember) |
| `areas` | the places of the zone, chained by their doors |
| `extraction` | where the car waits |

The four: the Green hills (the Academy's cutting; cut-wolves and the Warden), the Shenandoah
ruin (river-things and the ruin-stag), Harper's Cut junction (molted hounds and the
post-breaker), the Cahokia river line (eels of the current and the Barge-Heart).

## What an area is

An area is a place the hero can walk, the same shape as the Academy's own places. Its fields:
`size`, `spawn`, `doors` (to sibling areas or `extraction`; `locked` + `opensWhen: cleared`
waits for the area's beasts to fall), `density` (props per sixteen square metres), `rails`
(the line crosses it: a ballast band and rails along z = 0), `water` (a band of water along
a side), `post` (the post's place; `waitForPost` holds the beasts until it is taken), `set`,
`setAt`, `setRot` (the area's set piece), `beast` (`common`, `elite`, or an id), `pack`
(`min`..`max` of the common beast beside the locked one), `respawn`.

`Zones.area_place("<zone>/<area>", seed)` turns an area into a place: the pack's size, the
props' positions and the tile mix are drawn from the seed, so a run on another day lays the
area out another way. The Academy uses the run's seed plus the day. Place ids of areas are
`zone/area` (`green/cutting`); `Academy.place_spec` resolves both kinds.

## Drawing

`World._build_zone_ground` lays 4 m floor tiles from the library (ballast on the rails
band, water on the water side), then edge pieces round the rim with a gap at every door.
`World._furnish_zone` scatters props by density, keeping clear of the spawn, the doors, the
post, the set piece and the rails; props with a radius become obstacles the hero and the
pack walk round. Pieces are read from `game/assets/wild/<name>.glb` (built by
`tools/blender/wild_kit.py`); any piece not yet built is stood in for by the dungeon kit.

## Packs

A fight in a zone has the locked foe (the Fight's `w_*`) and a **pack** (`Fight.foes`,
each a `Foe`). Each of the pack prowls, picks the hero or a classmate, winds up (a `!` and
a glow), bites, recovers; swings and techniques hit every foe in the arc; the party strikes
whichever is nearest. When the locked foe falls, the nearest of the pack takes the lock
(`swap_target`); the lock button passes the lock round. The HUD counts the pack in the
target frame.

## Beasts

Every beast has `model` (`game/assets/beasts/<model>.glb`, built on the wolf's rig by
`tools/blender/beast_kit.py`; the wolf stands in when the file is missing), `modelScale`,
a Shape on the wheel (so one Shape's techniques break it), three attacks (the third with
weight 0 is its counter) and `respawnSeconds` (99 for elites: they stay down).

## The cohort fights on its own

A classmate in the party is an agent (`data/academy.json`, `cohort.fighting`; `Fight.make_ally`
and `Fight._update_allies`). Each picks a foe (the one hunting them, the one you are locked
on to by how much their temperament helps, else the nearest), closes to their weapon's reach,
circles for as long as their aggression lets them, strikes (or shoots, with a gun), spends
Will on their Shape's technique every few strikes, fires their Pattern once a fight when
their foe is below half (your genius witnesses it), parries or blocks a bite aimed at them
by temperament (a parry staggers the beast), and falls back toward you when hurt past their
nerve. Events: `ally-windup`, `ally-hit`, `ally-pattern`, `ally-parry`, `ally-block`,
`ally-retreat`, `ally-shot`.

## Elites and their guard (2026-11-10)

An elite is guarded (`guard` in `data/beasts.json`): a blow out of turn lands for that
fraction. The guard is down, and a blow lands whole, while the beast is staggered and while
it recovers from a strike of its own (`data/combat-room.json`, `guard.open`); a Pattern
always goes through. The target line reads GUARDED or OPEN. So the fight is: see the strike
out (guard it, parry it, step out of it) and answer in the opening.

The elites are tuned against four hands, not only the bot that parries everything:
`npm run balance:game -- --elites` prints, for each elite and named beast, how many of six
fights each hand wins, how long it takes, and what is left of the hero or the beast. The
Green's Warden is the one a learner must pass (the Field Examination ends at its den), so a
hand that guards half the blows and never parries should fell it every time.
