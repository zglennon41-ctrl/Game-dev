# Weapons: twelve types, three a city

Every weapon in `data/weapons.json` names one of the twelve **weapon types** in
`data/combat-room.json` (`styles`), and every one of the twelve cities carries three. A
type is a moveset; a weapon is a type with a city's name, a model and a story. The
Disciplines (`data/disciplines.json`) teach their city's three.

| Type | Hands | What it does |
| --- | --- | --- |
| Blade | 1 | three cuts, the third wide; a shield in the other hand for some |
| Greatblade | 2 | long and heavy; the wheel at the end throws the foe back |
| Axe | 1 | chops that bite deep; the cleave throws the foe back |
| Twin | 2 | two short blades: four fast cuts, the last leaves a bleed; a block drops any swing (the quick guard) |
| Spear | 2 | reach: thrusts that land first, a lunge that pushes |
| Polehook | 2 | reach, the rake, and the wheel that clears a circle |
| Staff | 2 | fast and sweeping; the parry window is half again as wide |
| Maul | 2 | the slowest and the heaviest; its slam breaks |
| Pistol | 1 | six rounds, quick; a reload of a second and a half |
| Musket | 2 | two rounds that hit hard and far; a long reload |
| Bow | 2 | hold to draw: a full draw hits three times a snap shot; the quiver never empties |
| Scatter | 2 | two shells of a wide cone that hits everything close and throws it back |

**Magazines and reloads.** A gun shoots until its magazine is empty; the press that finds
it empty reloads, or X reloads early. A reload takes the type's seconds (the slot's shutter
shows it); a dodge or a block cancels it. The ability bar's Strike slot shows rounds left.

**The draw.** A bow draws while the attack is held; the slot shows the draw. Release looses;
held past full draw it looses on its own half a second later. Drawn, you walk at half pace
and turn toward the foe you are locked on to.

**The cone.** A scatter-gun's shot hits every foe in its arc, the pack included, and throws
them back.

**Classmates** carry any of the twelve (`cohort.fighting.weapons` in `data/academy.json`
gives each type their reach and damage), and shoot with the ranged ones.

**Models.** A weapon's `model` is read from `game/assets/weapons/<model>.glb` (built by
`tools/blender/weapon_kit.py`), else from KayKit's of that name. A material named `field…`
on a model glows in the Shape's colour, brighter for every technique the hero has
perfected.

## The twelve cities and their Disciplines

| City | Discipline | Weapons |
| --- | --- | --- |
| Columbia | Marshal | saber, pistol, musket |
| Cahokia | Pilot | harpoon, boat-hook, oar-staff |
| Lunden | Aeronaut | air-pistol, rapier, grapple |
| Colonia | Engineer | engine-arm, hammer, bolt-thrower |
| Tiber | Legionary | scutum and gladius, short blades, pilum |
| Khemet | Grower | ward-staff, sickle, seed-sling |
| Baghdad | Geometer | astrolabe, glass blade, dividers |
| Varanasi | Ascetic | wrapped fists, staff, chakram |
| Jiangnan | Examiner | war fan, needles, brush-staff |
| Kazan | Rider | lance, horse-bow, stock whip |
| Timbuktu | Archivist | lantern-staff, pen-knives, the ledger |
| Edo | Blade | katana, naginata, longbow |

Each Discipline is a kit of nine techniques (`data/discipline-kits.json`): three taught in
Lesson 4, the rest learned from the school's instructor in the yard for Marks. The twelve
Disciplines are the game's twelve base classes; a Shape and a Discipline together make one
of the seventy-two archetypes in `data/archetypes.json`.

## Validation

`npm run balance:game` plays every weapon type for two minutes with a skilled bot that
knows its weapon (melee closes and strikes in the openings; ranged keeps its distance,
shoots and reloads; the bow draws), fires every Discipline's techniques against a standing
wolf, and runs two classmates of each temperament, and prints the tables. Every type fells
seven to eleven wolves in the two minutes and the test suite holds the floor (three in a
minute, alive at fifty seconds). The techniques' damage per Will sits between 0.7 and 1.6
for those that deal damage; marks, sounds, tethers and wards are utility and show 0.
Temperaments read distinct: the reckless strike most, the scared and the kind fall back
most, nobody is useless.
