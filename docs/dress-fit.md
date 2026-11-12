# Dress that fits

The owner, 2026-11-12: "Right now cloaks cut awkwardly through the back and neck ware juts out
inorganically." And the rule for clothing that fights the body: **cut what fails; a piece comes
back when it fits.**

This file says how fit is measured, what was changed so the dress fits, and what is cut from
the game until it does. The table of every piece on every body is `docs/dress-fit-table.md`.

## The check

    npm run check:fit                       # every body; exit 1 if a piece does not fit
    npm run check:fit -- columbia-m tiber-f # some bodies
    npm run check:fit -- --all              # also what is cut, to see whether it fits yet
    npm run check:fit -- --md docs/dress-fit-table.md

(`python` must be the one with Blender's module, as for the body kit: `pip install bpy`.)

`tools/blender/fit_check.py` builds each body exactly as `body_kit.py` does when it writes the
game's files, stands it in the rest pose and in fourteen moments of the clips the game plays
(idle, walk, two of the run, a strafe, a slice, a chop, a spin, the two dodges, which go down
into a crouch, blocking, casting, aiming, a hit), at the fit build and, for idle and the run,
lean and heavy. It spreads up to 700 points over each piece and measures each one:

| measure | what it is | what it catches |
| --- | --- | --- |
| **sunk** | the share of the piece that lies inside the body, or under a garment worn beneath it, deeper than cloth is thick (0.014) | a cloak through the back, a belt lost in a coat |
| **deep** | how deep the worst twentieth of the piece is sunk (only held when more than about a twentieth is sunk at all) | a leg through a hanging cloth |
| **float** | how far the nearest tenth of the piece is from what it lies on | a piece that touches nothing |
| **jut** | how far the farthest twentieth stands off what it lies on | neckwear that juts out |
| **drift** | how much a point's distance from the body changes between the rest pose and a clip | a piece that does not move with the body |

Lengths are the kit's: a body is 2.4 tall, so 0.01 is about 7 mm on a person. "Beneath" is
decided by layers (`wardrobe.LAYER`): legs' cloth, then the tunic or coat, then what is worn
over it (a cuirass, a tabard), buttons, belts and neckwear, the small solid things, a coat
worn over everything, the shoulder cape, the cloak. Each point is measured from the part of
the body it lies on in the rest pose, so an arm may brush the trunk's dress; nothing is
measured against the head.

The limits, by the kind of piece (`LIMITS` in the script; the owner's to tighten):

| kind | pieces | sunk | deep | float | jut | drift |
| --- | --- | --- | --- | --- | --- | --- |
| cloth | tunic, coat, robe, skirt, trousers, apron, tabard | 12% | 0.045 | | | |
| snug | belt, sash, strap, wrap, cuirass, vest, boots, gloves | 15% | 0.035 | 0.02 | 0.07 | 0.05 |
| neck | collar, scarf, fur collar, beads, chain, brooch | 15% | 0.035 | 0.02 | 0.08 | 0.04 |
| bulky | knot, satchel, roll, pauldrons, holster, coil, tools, bow | 60% | 0.06 | 0.035 | | 0.08 |
| hang | cloak, shoulder cape, the creator's cloak (float, jut and drift are of the top quarter) | 10% | 0.035 | 0.03 | 0.09 | 0.06 |

A solid thing rests half in the cloth by nature, so it is held only to not being swallowed
(60%). A roll slung on a strap and starched shoulder wings are stiff by nature and are not
held to drift.

## What was wrong, measured (before: 26 bodies, 413 pieces, 248 failing; after: 285 pieces, none failing)

- **The creator's cloak** (the Cloak chip; six in ten classmates wore one) was one stiff
  board hung from a socket on the chest bone: 67% of it sunk on the median body, 0.09 deep,
  standing 0.25 off the body in a run. On every body.
- **The homes' cloaks** (a master's, Tiber's, Varanasi's): the legs through them in a run
  (18% sunk, 0.06 deep).
- **The collar pieces** hung at the throat (the echo ruff, charm and gorget, the rank's trim)
  rode the head, made for a bare neck: a third to a half under the dress's collar, 0.08 deep,
  the ruff standing 0.10 to 0.12 off.
- **Fur collars** were a stiff ring in the air round the neck (a third sunk in the shoulders,
  0.06 to 0.09 off); **scarves** stood 0.07 to 0.10 off; **chains and beads** hung 0.08 to
  0.17 in front of the breast.
- **Shoulder capes** were a stiff cone on the chest (up to 30% sunk when the arms moved).
- **Belts, sashes, buttons, badges** were cut on the bare body and so lay under the coat or
  tabard worn over it (a belt 50 to 100% sunk).
- **What hangs at the hip** (a sash's ends, a satchel, a tassel, a disc, a coil) was fixed to
  the hip bone and stayed still while the thigh and the skirt beside it moved (drift 0.1 to 0.2).
- **What hangs from headgear** (a veil's fall, a head-cloth's lappets, a turban's tail) rode
  the head and passed through the back and shoulders (90 to 100% sunk).

## What was done (`tools/blender/wardrobe.py`)

- **A cloak hangs from the shoulders.** Its yoke is cut from the body's own upper back and
  shoulders, so it lies on them and moves as they move; under the yoke's edge a fall hangs
  plumb down the back from whatever stands out most (measured on the dressed body, so it
  clears the coat under it), opening a little toward a hem at mid-thigh; below the hips each
  side swings with its leg. It is shorter than it was (it ended below the knee): a cloak to
  the calf cannot stay out of a running leg without cloth simulation.
- **The creator's cloak is that same cloak**, a mesh of every body (`Cape`), in the colour
  the look names. The stiff part on the back socket is gone from the game.
- **One cloak at a time** (the game, `world.gd`): the look's cloak is worn in place of the
  home's own cloak and of its shoulder cape, and what is slung on the back (a quiver, a tool
  roll) is under a cloak, unseen. They do not fit together.
- **A shoulder cape is cut from the body** (shoulders, the top of the arms, breast and back)
  and let out over the dress beneath; it moves with the shoulders and arms.
- **Neckwear wraps the neck's real surface.** The fur collar is cut from the neck's base and
  shoulders and stood off like a roll of fleece; a scarf's ends are bands laid on the breast
  or the back; chains and beads lie on the breast, each bead seated on its own.
- **Everything is seated on what is worn under it**, lowest layer first: a band is let out
  until it clears the cloth beneath, a solid thing is moved out until only its back is in the
  cloth (or drawn in until it touches), a coat is let out over full trousers.
- **What hangs at the hip and what is pinned to the cloth takes the body's weights**, as the
  skirt it hangs against does, so a stride moves both alike.
- Shells cut from the body have their stepped edges evened.

## Cut until it fits

A piece of a home's dress is cut by `cutUntilFits` (the reason) on the piece in
`data/bodies.json`; a part by the same key in `data/people-features.json`. The cutter is kept;
take the key away and `npm run check:fit` says whether it fits yet.

| cut | where | why (worst measured) | to bring it back |
| --- | --- | --- | --- |
| The collar pieces: the echo's ruff, charm and gorget, and the rank's trim | every body (parts on the throat socket) | made for a bare neck and hung on the head: a third to a half under the collar, the scarf or the shoulder cape, 0.08 deep, and they turn with the head, not the shoulders. All 104 failed. | cut each from the body's neck and shoulders as the fur collar is, seated on the dress, as a mesh of the body shown when earned. The echo is still written on the partner (`features_of`); only the piece is not hung. |
| What hangs from headgear below the chin: the veil's fall, the head-cloth's lappets and fall, the turban's and the tagelmust's tail, the kerchief's ends | Baghdad, Khemet, Varanasi (master), Timbuktu, Colonia | rides the head alone, through the neck, shoulders and back (64 to 100% sunk). They now stop at the chin. | hang the fall from the shoulders (weights of the upper back) and leave only the crown on the head. |
| Belt | Alexandria | over the tabard: in a run the tabard's skirt rides over it (a tenth sunk, 0.07 deep) | a tabard cut in two at the belt, or a belt the tabard is gathered under |
| Belt | Lunden, women | over the long coat, where the riding breeches stand out under it in a run (7% sunk, 0.065 deep) | |
| Holster | Columbia, women | on the long split skirt the holster and its strap sink in at a walk (38%, 0.069) | hang it from the belt at the hip, not strapped to the thigh, under a skirt |
| Apron, the Foreman's coat, the waistcoat's buttons | Colonia, women | over the women's flared tunic each sinks into it (apron 10 to 21%, 0.045; coat 8 to 13%, just over the limit; buttons 8 to 13%, 0.064 to 0.084) | a tunic for the women without the flare under an apron |
| Pteruges (the leather strips) | Tiber, men | a dodge or a run puts the thighs and the tunic's skirt through them (44%, 0.085) | strips cut as one pleated skirt on the tunic's own surface |
| The front cloth (panel) | Khemet men, Varanasi men | hangs between the legs: a stride puts the thighs through it (16 to 20%, 0.05 to 0.065) | |
| The sash's long ends | Khemet; Jiangnan women | hang down the front between the legs, or against a full skirt (22 to 42%, 0.07) | shorter ends, to the side |
| Tassel | Jiangnan | hangs in front of the thigh (43 to 62%, 0.07 to 0.08) | |
| The brass disc (the astrolabe) | Baghdad | hangs from the belt in front of the thigh (39 to 41%, 0.085) | worn at the side of the hip, or on the breast |
| Fur collar | Kazan; Lunden men | Kazan: over the crossed kaftan a tenth of it is sunk standing or moving (10 to 12%, 0.07). Lunden men: a fifth of it is sunk in the jacket's collar and under the shoulder strap (20%, 0.065) | Lunden's women's fits on the long coat: the collar wants the strap and the crossed front to pass under it |

Worn less, so the rest fits (not cut): Edo's stiff shoulder wings are worn in plain dress only
(under the over-coat of visiting dress they came through it); Timbuktu's scroll case is worn in
reading dress but not by a master (it came through the master's shoulder cape).

Changed in shape so it fits: Edo's over-coat is hip length (it was to the thigh, and the wide
hakama came through it); Alexandria's women's tabard is shorter; Columbia's sash ends are
shorter, the women's sash sits higher and their neckerchief has no ends; Khemet's and
Timbuktu's women's collars are narrower; Columbia's gun belt is marked as worn under the open
coat (`under`).

## Still weak

- A long skirt or coat stretches between the legs in the widest stride (its hem follows both
  thighs). It passes the measure (little of it is sunk) but it is not cloth. Real cloaks and
  skirts want simulation, or bones of their own.
- The cloak is a short back-cloak, not a full cloak that wraps the shoulders and closes at
  the breast.
- The check does not measure hair against dress, or weapons against dress.
- The clips that are not in the game yet (sitting, lying, picking up) are not measured.
