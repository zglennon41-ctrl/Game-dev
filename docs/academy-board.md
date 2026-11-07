# The board, the crisis and the cohort's days

What fills the term between the six lessons: the board's postings (excursions into the
zones), the season's crisis they weigh, and the classmates who live their own days. All of
it is data (`data/quests.json`, `data/crises.json`, `data/academy.json` under `cohort`).

## The board

The board in the quad carries the cohort's troubles (three a run, one per temperament) and,
once Lesson 5 has opened the line, **three to five postings a day** drawn from the run's seed
and the day, so the board changes after every rest. A posting is one of the seven quest
types the hall's board carries on the server, filled for a zone that is open:

| Type | Poster | The run | Pay (Green / Amber) |
| --- | --- | --- | --- |
| Linework | the Compact | fell the way in, hold the post a minute, extract | 1 / 2 |
| Salvage | the Archive | find a thing in the post's area and carry it out with no Patterns | 1 / 2 |
| Hunt | a town | the pack, then the zone's named beast in its area, on a timer | 2 / 3 |
| Escort | a house | a passenger walks beside you and must not fall; the post; extract | 1 / 2 |
| Writ | a house | on a timer, find the writ's thing, then a decision the character keeps | 2 / 3 |
| Deep Run | Varga (field open) | the way in, the post, the zone's heart, one extraction | 3 / 4 |
| Rally | the Compact, Fridays | three bouts in the yard, win two; Bask reads the standings | 1 |

A posting now and then comes with the classmate who took it (they are the party's first).
Zones open by lesson (`opensAfter` in `data/zones.json`): the Green and the Shenandoah after
Lesson 5, Harper's Cut and the Cahokia river after Project.

The excursion: the party (two classmates, chosen one at a time), the car (the travel step's
lines), the areas, the post (whoever is down stands up there), extraction (the car only
leaves on the run's last step), and the pay at the hearth. A step with `limit` has a clock;
when it runs out the quest is lost. A passenger down, the carried thing dropped (the hero
down while carrying) or the rescue team lose it too. Lost quests go on the record and the
board carries them again.

## The crisis

One crisis a term (`data/crises.json`; the first is the Dark Mile, crisis 1 of
`docs/systems-05-crisis-storylines.md`). Its phase follows the term:

| Phase | When | What happens |
| --- | --- | --- |
| Omen | until Lesson 5 | the rumours (a line a day from whoever you talk to), the Compact's notice |
| Pressure | after Lesson 5 | the Ledgers open; every quest done weighs the Ledger its type serves; the crisis posts its own quest every other day |
| Crisis | with the field open | a crisis posting every day, weighing threefold |
| Reckoning | at the Gate | the heaviest Ledger with a quarter of the weight ends it, else the default |

Weight: Green 1, Amber 3 per quest, times three for the crisis's own postings; a Writ's
decision weighs the Ledgers that name it. The board shows the Ledgers' standing. The ending
is told at the Gate and written onto the character (`hero.world`: the line, the house, the
lamps, the named man, the Chronicle's line) for the server to read.

## The cohort's days

After the rite each classmate stands where their temperament puts them on that weekday (the
yard, the quad, the hearth: `cohort.schedule.haunts`). Two a day are out on runs of their
own and say so the next day. A classmate carried out of a run (down at extraction) spends
two days in the infirmary and cannot come on a run. A classmate a trouble or a quest needs is
always where the step says.

In a fight each classmate is an agent (`cohort.fighting`): see `docs/zones.md`, "The
cohort fights on its own".

## Days and sleep in the board phase (2026-11-07)

After Lesson 6 the mornings belong to the board until the Gate's ten postings are done. The
day turns only in the dormitory. You may sleep once a posting or a trouble has been finished
that day, or when the board is bare; otherwise the bunk says the board still has the day's
work on it (`data/academy.json`, `rest.board_waits`). The rule is `Academy.rest_reason_for`,
pure and tested; the autopilot sleeps by it.
