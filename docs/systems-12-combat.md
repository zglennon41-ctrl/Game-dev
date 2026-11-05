# Combat

Combat is third-person, real time, and timed on the pulse: every character's field beats, techniques land on beats, and a Pattern is a chain of them. The four Stages are the four buttons, the Shape wheel is the counter system, and a party of three with three geniuses is six bodies that have to agree on a rhythm.

## The pulse

The pulse is a ring at the character's feet that beats at a tempo set by their Shape and gear: Anchor slow, Cast fast, a heavy weapon slower, a blade quicker. A beat is a window of about 150 milliseconds. Inputs on the beat are perfect; inputs off it still happen, at reduced output. A party's three pulses are visible to each other, and the score of every zone is written to the party's tempo, which is why fights feel like music when they go well and like noise when they do not.

## The four verbs

| Verb | Input | On the beat | Off the beat |
| --- | --- | --- | --- |
| Hold | Guard | Parry: no damage, 10 Will refunded, the foe staggered a beat | Block: half damage, Will drains |
| Shape | Stance toggle | Enter the stance at once | A beat of delay |
| Project | Attack and technique buttons | Full output; techniques chain | 70% output; chains break |
| Pattern | The Pattern button, then the chain | Each beat hit continues the chain; all hit pays the full multiplier | Fizzle: Will spent, Toll taken, no effect |

Still and Fold are held inputs: hold Guard with no foe locked to go Still, hold Attack to Fold.

## Health, Will, and falling

Health is 100 for everyone, raised only by gear and Anchor Endurance. Will is 100, spent and regenerated as the Shapes tab says. At 0 health a character is downed: sixty seconds for the party to revive them by standing on them for three beats, else carried home. A downed character's genius goes Guard on the body. There is no death on the line except for Sworn characters.

## Weapons by city

Every weapon is a city's genre and a tempo.

| City | Weapons | Tempo | Wants |
| --- | --- | --- | --- |
| Columbia | Musket, pistol, saber, hatchet | Slow shot, fast melee | Cast for the shot, Anchor for the saber |
| Cahokia | Harpoon, boat-hook, oar-staff | Medium | Bind for the hook, Anchor for the staff |
| Lunden | Air-pistol, rapier, grapple | Fast | Cast and Bind |
| Colonia | Engine-arm, hammer, bolt-thrower | Slow, heavy | Make and Anchor; the engine-arm is its own stance |
| Edo | Katana, naginata, bow | Exact | Turn and Cast; the blade punishes a missed beat hardest |
| Kazan | Lance, horse-bow, whip | Fast on the charge | Cast and Bind |

The other six cities' weapons arrive with their routes. A weapon off your city is usable at a beat's delay until you have 10 Marks with it.

## Beasts and breaks

Every beast has a Shape and a molt. The Shape is readable with a beat of Read or by watching it fight; the molt is its tier (first to fourth, and past the fourth on Black). A beast is broken by techniques of the Shape opposite its own: three breaks open a stagger window of three beats in which every hit is perfect and Patterns pay double. Bosses have two Shapes and switch between them.

| Molt | Where | Behavior |
| --- | --- | --- |
| First | Green | Fights simply; one Shape |
| Second | Green, Amber | Reads your stance and counters it |
| Third | Amber, Red | Targets the genius; breaks posts |
| Fourth | Red | Two Shapes; names you (a fourth-molt beast remembers a party that fled it) |
| Past the fourth | Black | Nobody's wolf; the rules are per creature |

## The party

Three characters, three geniuses, three accounts. Roles are not classes; they are what the Shapes do when they meet: an Anchor holds the line, a Read calls the break, a Cast takes it. The party sees each other's pulses and Will, and a technique landed on a party member's beat (a Make ward placed as an Anchor braces) chains across characters, which is the ensemble system without a word of UI.

## Genius in the fight

The six orders are a radial (Shift, into a secondary form, joins them from the Third Form), and the genius acts on its own pulse, which is the partner's. Hunt uses the genius's own technique family. Duet is called on the Pattern button with a genius at its Fourth Form or beyond: the chain doubles in length, the genius strikes on alternate beats, and the payout doubles. A missed beat in a Duet fizzles both.

## PvP

PvP exists in two places only. Rallies: three against three in Compact tunnels, Fridays, objective-based (hold the post, carry the lamp, break the other hall's ward), Standing on the line, no death. Writ wars: Red zones flagged by a house against another house's hired guild, consensual on both sides at acceptance, named NPC members at risk, Favor and Standing on the line, Sworn characters can die. There is no open-world PvP, no dueling outside the yard, and no way to attack a party that did not accept a Writ.

## Numbers

|  |  |
| --- | --- |
| Beat window | \~150 ms |
| Off-beat output | 70% |
| Health | 100 base |
| Down timer | 60 s; revive by 3 beats standing on the body |
| Break | 3 breaks open 3 beats of stagger; Patterns ×2 inside |
| Party | 3 characters, 3 geniuses |
| Rally | 3v3, objective, Fridays |

## Open questions

- [ ] Is a 150 ms beat window too tight for console players on a TV, and does the window widen on Green lines?
- [ ] Should a party's three tempos be forced to one shared pulse in the car, or is three tempos the point?
- [ ] How does lag treat the pulse in co-op: client beat with server reconciliation, or server beat with client prediction?
