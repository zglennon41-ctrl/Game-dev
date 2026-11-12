# Representation: everyone can make themselves

The owner's direction (2026-11-12, `HANDOFF.md` §9): "I also want everyone to feel represented in
the game and the variety of outfits, cultures, and body types is crucial." Chosen, all of: body
builds; hair and head coverings; outfit choice across cultures; disability and age; and
"diversity of style and individuality. Maybe the ability to mix and match from three to five
core outfits and hairstyles for each culture."

This file is the audit of where the creator stood, the target, what it costs, the order of
work, and what is built. `docs/bodies-plan.md` is how the bodies and the dress are made;
this file is who can be made with them.

## 1. Where we stood (the audit, 2026-11-12)

The creator makes a character from the answers (blood, Shape, home, weapon) and then offers
the look on three leaves: Body, Face and hair, Dress. Before this pass:

| | What existed | What a player could choose |
| --- | --- | --- |
| Bodies | 26: a masculine and a feminine body for each of the 13 homes | either, in any home |
| Build | two shape keys, lean and heavy, both a mix of muscle and a little weight | one slider, Lean to Heavy; "heavy" was a strong body, never a fat one |
| Height | a scale on the whole body | Slight to Towering (0.94 to 1.12) |
| Age | one: a young adult. Grey and white hair, a "weathered" and a "grave" face | no age |
| Skin | seven tones | **only the home's palette**: three to seven of them |
| Face | the home's own (an ancestry mix and details) and eight shapes over it, four features, six brows, eight eye colours, lips, marks | all of it, in any home; the home's cast itself comes with the home |
| Hair | fourteen styles and shaved; coils, rows, locs and curls among them | all of them, in any home, in seven colours |
| Beards | five | all, on either body |
| Head coverings | one headgear for each home and sex (16 kinds: a turban, a wound cloth, a head-tie, a veil, a kerchief, a head-cloth, hats, caps, helms) | the one of your home and your sex, on or off |
| Dress | one outfit for each home and sex, as one mesh; a second dye; a formal layer | the dye and the formal layer; **the outfit of the other sex not at all** |
| Visible difference | two scars, freckles, a mole, a home's face paint | those. No prosthetic, cane, eye patch, hearing aid, chair, vitiligo, burn |

By home (ancestry is MakeHuman's three forms mixed; pieces are the working dress):

| Home | Ancestry mix | Skin tones offered | Its people's hair | Headgear | Top / legs (m; f) |
| --- | --- | --- | --- | --- | --- |
| Alexandria | a third of each | all seven | crop, short, curls, bob, long, tail, braid, knot | none | tunic; tunic |
| Columbia | afr 25, asi 15, cau 60 | pale to brown | short, crop, tail, long, braid, curls | hat | coat; tunic / wrapped skirt |
| Cahokia | afr 10, asi 55, cau 35 | olive to deep | twins, long, braid, tail, crest, crop | knit cap | coat; tunic / wrapped skirt |
| Lunden | cau 100 | pale, fair, olive | short, crop, bob, tail, curls, knot | flat cap; flying cap | jacket / trousers; coat / trousers |
| Colonia | asi 10, cau 90 | fair to brown | crop, short, crest, tail, braid, knot | works cap; kerchief | tunic; tunic |
| Tiber | afr 10, asi 5, cau 85 | fair, olive, tan | crop, short, curls, knot, braid, bob | helm | tunic and cuirass / strap skirt; tunic and cuirass |
| Khemet | afr 55, cau 45 | tan to dark | rows, locs, coils, crop, bob, braid, curls | head-cloth | bare / kilt; robe |
| Baghdad | afr 10, asi 10, cau 80 | fair to brown | curls, short, long, braid, knot, tail | turban; veil | coat / trousers; tunic / trousers |
| Varanasi | afr 25, asi 20, cau 55 | olive to deep | long, braid, knot, topknot, short, curls | headband; brow jewel | bare / wrapped cloth; tunic / wrapped skirt |
| Jiangnan | asi 100 | pale to tan | topknot, knot, long, tail, bob, braid | scholar's cap; hair band | robe; tunic / wrapped skirt |
| Kazan | asi 50, cau 50 | fair to brown | twins, braid, crest, tail, crop, long | fur hat | kaftan; kaftan and vest |
| Timbuktu | afr 100 | brown, deep, dark | coils, locs, rows, crop, curls, braid | wound cloth; head-tie | robe; tunic / wrapped skirt |
| Edo | asi 90, cau 10 | pale, fair, olive | topknot, tail, long, knot, bob, crop | none (a straw hat for masters) | jacket / pleated trousers; the same |

### Who could not make themselves

- **Anyone whose skin was not in the palette of the home their answers gave them.** The home
  comes from the questions, not from a choice. A dark-skinned player sent to Lunden, Edo or
  Tiber could not have dark skin; a pale player sent to Timbuktu could not be pale. Ten of the
  thirteen homes offered no deep or dark tone at all. The cast of the face (the ancestry mix)
  is fixed by the home in the same way, and still is: see "Open to the owner".
- **Fat people, and thin people.** The one build slider ran from a lean athlete to a heavy
  athlete. There was no soft, full or fat body, no slight one, and no broad frame apart from muscle.
- **Short people.** The least stature was 0.94 of the middle; nobody in a home was small.
- **Anyone not young.** No middle age, no old age, on the body or the face.
- **Anyone who dresses across the line the data drew between the sexes.** A woman in Timbuktu
  could not wear the wide robe, a man could not wear the head-tie, a woman in Columbia could
  not wear the long coat and trousers. The pieces existed; the game hid them.
- **Anyone who covers their hair by choice or by faith, outside the two homes that happen to.**
  A veil existed only on Baghdad's women and a kerchief only on Colonia's; a turban only on
  Baghdad's men. No home offered a plain headscarf or a head wrap as a choice.
- **Disabled people.** Nothing: no prosthetic limb, cane, crutch, chair, eye patch, hearing aid.
- **Hair**: the textures were there (coils, rows, locs, curls) but thin: one length of locs,
  no long braids, no full round afro, no twists or knots, no fade, no thinning or balding hair.

Pictures of this state: the report of the pass names them (the homes' sheet, the hair sheet).

## 2. The target

**A player of any body, any skin, any age and any way of dressing can make themselves in any
home, and two players of one home do not look alike.**

- **Bodies.** Any build from slight to heavy and from narrow to broad, any height from short to
  towering, any age from young adult to old; each a measure the player moves, not a body type
  to pick from a list of three. Every garment of every home fits every one of them.
- **Skin.** Any tone in any home: people come to every city from every other. The home's own
  tones are shown first. (Built behind a switch; the owner's call.)
- **Hair.** Three to five styles that each home is known by, and every style of every home open
  to everyone. Textures as first-class as straight hair: coils, a full afro, locs short and
  long, braids in rows and long braids, twists, knots; shaved and faded; thinning and bald.
- **Head coverings as first-class choices**, not as one home's costume: a head wrap, a
  headscarf that covers the hair and neck, a turban, a kerchief, a hood; in the home's own
  cloth and colours, beside the home's own headgear, on any body.
- **Dress.** Three to five core outfits for each home, mixed **slot by slot**: head, top, legs,
  feet, over it, worn and carried. Any piece on any body: nothing is one sex's. The dyes of the
  home stay the home's (its colour chord is how a home is told from far off).
- **Visible difference.** A prosthetic arm or leg, a cane, an eye patch, a hearing aid, a
  brace, a chair; scars and burns on the body; vitiligo and albinism in the skin; a missing
  hand or eye. Chosen, never assigned; never a blood's mark and never a penalty.
- **The cohort and the Academy reflect it.** Classmates and Instructors are drawn from the
  same ranges, so the player is not the only heavy, old, covered or disabled person in the hall.

## 3. How it is built

### Bodies: shape keys and bones

A build is a **shape key** on the body and on every garment, made from MakeHuman's own
measured forms (`data/bodies.json`, `builds.keys`; `tools/blender/human_kit.py`,
`_extra_build`). The kit builds each garment again on each build's body, so the dress fits
it by construction and blends with it.

| Key | What it is | The look's measure |
| --- | --- | --- |
| `lean`, `heavy` | less and more muscle (as before) | `build`, -1 to 1 |
| `thin`, `stout` | little weight, and MakeHuman's fullest weight on little muscle | `weight`, -1 to 1 |
| `broad` | wide shoulders, ribs, hips and neck; drawn backwards it is a narrow frame | `frame`, -1 to 1 |
| `old` | MakeHuman's old age: the face, the neck, the chest, the limbs | `age`, 0 to 1 |

Two rules keep these honest. **A shape key cannot move a joint**, and a broad frame sets the
shoulders 6 cm wider, age carries the head and shoulders forward: so each part of the body is
kept on its own bone in the key, and what the form did to the joints is given back by moving
the bones (`game/scripts/frame.gd`; `data/creation.json`, `look.frame.bones`). Elbows and
knees still bend where they are. **The skull under the hair does not move** in any build, so
every cap of hair and every hat fits every body; the face, jaw and neck do change, and the
brows, lashes, beards, marks and eyes go with them.

Stature is a scale on the whole person (0.88 to 1.12). Proportion by height (longer legs on
the tall) is not built: it needs the rig's bones scaled, and is in the order of work.

### Dress: slots and cuts

Every piece of a home's dress has a **slot** by its kind (`data/creation.json`,
`look.slots.kinds`): head, top, legs, feet, outer, extra. A home's dress has **cuts**: today
two, the pieces its data marks `m` and the pieces it marks `f`. The body kit builds **every
cut on every body** and joins the pieces of one slot and one cut into one mesh
(`Dress_top_m`, `Dress_legs_f`, `Dress_extra`, `Headgear_gele_f`). The look keeps a choice
for each slot (`look.wear`: slot to cut, or `none` where a slot may be left off); a slot the
look does not name is worn in the cut made for the body, so every old save and every person
made before looks as they did. The creator offers each slot's choices by the names of their
pieces (`Creation.wear_options`); a piece may carry a `name` of its own in the data.

This is the frame the three to five outfits hang on: **a new outfit is a new cut in the
data**, and the creator, the saves and the cohort take it without a change. What it needs
first is the name of a cut freed from the two sexes (`cut: "a"`, `"b"`, `"c"`) and a line for
each outfit in the home's own words.

### Hair and head coverings

Hair is cut from each head's own scalp (`tools/blender/hair.py`), so a new style is a new
function there and a new id in `data/creation.json` (`look.hair`); a home names the styles its
people most often wear (`data/bodies.json`, `hair`) and the creator shows those first.
A covering is built the same way, from the skull, so it fits the head it is on; it is a
choice of the head slot beside the home's own headgear, dyed in the home's cloth.

### Visible difference

Three kinds, each with a place that already exists:

- **On the skin** (scars, burns, vitiligo): marks, as the face's marks are now (small meshes
  laid on the skin, `Mark_<id>`), extended from the face to the body. Albinism is a skin tone
  and a hair and eye colour.
- **Worn and carried** (a cane, an eye patch, a hearing aid, a brace): parts on the sockets
  every body has (`socket_hand_l`, `socket_eyes`, `socket_head`), as the bloods' marks are.
- **The body itself** (a prosthetic arm or leg, a missing hand): a shape key cannot remove a
  limb. A prosthetic is a part that replaces the limb's surface below a joint: the body's
  faces below the joint hidden (a second surface on the mesh, so it can be switched off) and
  a rigid part on the bone in their place. A chair is a different way of moving and is
  design, not art: see "Open to the owner".

## 4. What it costs in file size

The web build has a ceiling of 256 MB and stood at 210 MB. What a person's file is made of
(one body as the game keeps it, `godot --headless -s res://game/tests/check_packed.gd`;
by part, `tools/glb-parts.py`):

| Part | In one person's file | Note |
| --- | --- | --- |
| The body and its face | about 0.9 MB of mesh, and the shape keys | 13,700 points |
| The 76 animation clips | about 1.0 MB | **the same clips in all 26 files** |
| Hair, all 14 styles | about 0.75 MB | 21,000 points; each style 30 to 90 KB |
| Beards and their keys | about 0.3 MB | they carry every face key |
| One cut of the dress | about 0.2 MB, and its keys | 3,000 points |
| One headgear | 5 to 40 KB | |

Measured, all 26 people together as the web build carries them (the people, and the whole
game's data file, `build/web/index.pck`):

| State | People | The game's data |
| --- | --- | --- |
| Before this pass | 108 MB | 210 of 256 |
| With the four build keys | 124 MB (+16) | about 226 |
| With both cuts on every body | about 131 MB (+7) | about 233 |
| With five hair styles and two coverings (after they were lightened; they were +16 at first) | 139 MB (+8) | 243.6, measured |
| Merged with the dress that fits (every body's own cloak, the fitted pieces) | 146 MB | 251.4, measured |
| With the shadow copies taken out of the people's files (below) | **128 MB** | **233.6, measured** |

So the prices are: **a shape key on everything costs about 4 MB** over the 26 people (keys are
kept as only the points that move, but a build moves nearly all of them); **a cut of dress on
every body about 7 MB**; **a hair style 1 to 2 MB**; **a covering about 1 MB**.

One saving was taken in this pass: Godot keeps a second copy of every mesh for casting shadows.
For people that was a fifth of each file (twenty hair styles, of which one is worn), and the
mesh itself casts the same shadow: `game/assets/people/people_import.gd` drops the copies,
18 MB back.

The target still does not fit as the files are laid out: four outfits for each home would be
about 28 MB of dress, and the build keys they carry more. Three things buy the room, in order
of worth:

1. **One set of animations for everyone** instead of a copy in each of the 26 files: about
   25 MB back. The clips are the same; only the rest pose's joint places differ by body, and
   the clips' rotations do not depend on them. The risk is the baked translations (the hips'
   bounce), which were scaled per body.
2. **Hair as its own files**, loaded for the style a person wears: the 26 files carry every
   style for every person now, and a scene of thirty people needs perhaps ten styles.
   It also takes hair out of the price of every new style.
3. **Garments shared between homes where the cut is the same** (a plain tunic, trousers,
   boots, sandals), dyed and trimmed by the home.

Until the first of these is done, the budget for new meshes is about 20 MB: every build key
and every cut is weighed against it.

## 5. Order of work

1. **Body builds** (built, this pass): weight, frame and years beside muscle; short to
   towering; the dress on every build; classmates and Instructors drawn from them.
2. **Mix and match with what exists** (built, this pass): slots and cuts; either cut on any
   body; any skin tone in any home behind a switch; a home's hair shown first.
3. **Hair and coverings, first slice** (this pass, as far as it went: see Status).
4. **The room to grow**: the animations shared (§4), then hair as its own files.
5. **Cuts freed from the sexes, and a third outfit for each home**: the data's `sex` on a
   piece becomes `cut`; each home gets a third cut in its own words (a working dress, a
   travelling dress, a festival dress), built from the kinds of piece the wardrobe already cuts.
   One home first, on a sheet, for the owner; then the rest.
6. **Visible difference, first slice**: body scars and vitiligo as marks; a cane, an eye
   patch and a hearing aid as parts; then the prosthetic arm and leg.
7. **Hair, the rest**: long braids, twists, knots, a fade, thinning hair; a second length of
   every hanging style; hair colours by strand (greying at the temples for the years).
8. **Age in the face's surface**: lines at the eyes and the mouth as marks that come with the
   years; an older voice in the barks, if the game gets voices.
9. **Proportion by height** and a **fourth and fifth outfit** where a home's culture has them.

Each step leaves the game playable and ends with a sheet for the owner.

## 6. Borrowed dress: for the owner to look at

The thirteen homes are the game's own, ten thousand years on, but their dress is drawn from
living traditions, and some of what is drawn carries meaning to the people it belongs to.
Flagged here so each is a decision and not an accident:

| Where | What is borrowed | What to weigh |
| --- | --- | --- |
| Baghdad, men: the turban; and any turban offered to everyone | turbans of the Middle East and South Asia; for Sikhs the dastar is an article of faith | offered as "a turban" in a home's cloth it is dress, and it must never be a joke, a villain's mark or knocked off in a fight. If a Sikh player should be able to wear a dastar as such, it wants its own shape and a line from someone who wears one |
| Baghdad, women: the veil; the headscarf offered to everyone | the hijab and other head coverings worn for faith | the game names it by what it is (a scarf, a veil) and gives no rule about who wears it; it is never removed by the game |
| Timbuktu: the wound cloth and the head-tie | the tagelmust of the Tuareg (a man's veil, with its own meaning of age and respect) and the gele of the Yoruba | the data's names for them are the real words; the creator calls them "Wound cloth" and "Head-tie". Both are now open to either body, which the traditions themselves do not do |
| Khemet: the head-cloth, the broad collar, kohl | ancient Egypt's nemes (a king's) and wesekh | a long-dead court's dress, low risk; the nemes was royal and here it is everyone's |
| Varanasi: saffron, the mark between the brows, the prayer beads | Hindu ascetics' cloth, the tilaka or bindi, the mala | the most loaded set in the game: saffron and the mark are religious. The mark is offered to any face in Varanasi and Baghdad as "a mark between the brows" |
| Cahokia: the lines on the chin, the ochre under the eyes, the crest of hair, the two braids | Native American face marks and hair; chin lines are specific to some peoples (Inuit, Mojave, Māori moko kauae elsewhere) | marks with living owners. Worth a reader from the people before the game ships; the crest is offered to everyone as "Crest" |
| Jiangnan: the scholar's robe, the winged cap, the square of rank | Ming court dress (the wushamao and the rank badge) | a historical court's dress worn here as the Examiners'; low risk, and the women's jacket and skirt are hanfu |
| Edo: the stiff shoulders and pleated trousers, the topknot, the straw hat | kamishimo and hakama, the chonmage, the kasa | historical; the topknot is offered to everyone |
| Kazan: the kaftan, the pointed fur hat, the braids | Mongol and Tatar dress | historical and living; low risk as drawn |
| Tiber, Columbia, Lunden, Colonia | Rome's legions, the American marshal, the British docker and flyer, the German works | the game's own homes wearing their own past; no flag |
| Hair: rows, locs, coils, long braids | Black hair, with a history of being policed | drawn with the same care as any other hair and offered to everyone; the names are the plain ones. A reader would catch what we cannot |

The rule this pass followed: a real tradition's piece is named for what it is made of or
where it sits, is never the mark of a blood or a villain, is never taken off a person by the
game, and is open to any body. Where a piece is an article of faith the plan is to ask before
adding more of it.

## 7. Open to the owner

See the report of the pass for the list in full. The ones that shape the plan:

- **Any skin in any home** is built behind `look.anySkin` and is on. It reverses an earlier
  decision (the home's palette only).
- **The cast of the face still comes with the home.** A player sent to Lunden has a Lunden
  face. Letting the face's ancestry be chosen (a slider over the home's mix, or "born
  elsewhere") is a design decision about what a home is.
- **Whether home should be a choice at all**, at the end of the questions, as the blood is.
- **What an old first-year means.** The Academy takes children at the edge of growing up; the
  creator now lets a first-year be old. Is that a late waking, and does the story say so?
- **A chair, and other ways of moving**, change combat's feel and are not art alone.
- **Which third outfit each home gets**, in the home's words.

## 8. Status (2026-11-12)

Built in the first pass, each playable:

- **Body builds.** The Body leaf of the creator: eight builds by name (Slight, Lean, Average,
  Strong, Broad, Full, Heavy, Big), each a setting of three measures the player may move
  (Muscle, Weight, Frame); Stature from Short to Towering; Years from Young to Old. Four new
  shape keys on all 26 bodies and on every piece of their dress; `frame.gd` moves the
  shoulders and the head with the bones. Classmates and new lives start with a weight and a
  frame of their own; Instructors have years. Looked at: three homes in every build, a big and
  broad body in a run, a swing and a dodge, long hair and a full beard on heavy bodies.
- **Mix and match.** The Dress leaf: each slot of the home's dress in either cut, on either
  body (head, top, legs, feet, over it, worn and carried), a bare head and nothing over it or
  carried where a slot may be left off. Both cuts of every home are on both of its bodies.
  A mix that would leave a bare-legged home undressed is settled (`Creation.wear_settle`).
  About a third of the time a classmate wears the other cut of a slot. Any skin tone in any
  home (`look.anySkin`); the home's hair styles are shown first.
- **Hair and coverings.** Five more styles (Afro, Long braids, Coiled knots, Faded sides,
  Thinning) and two coverings on every head of every home (Head wrap, Headscarf), in the
  home's cloth. A few classmates cover their hair. The headscarf is skinned like the body
  under it (the neck's part bends with the neck) and carries every build.
- **On the dress that fits** (`docs/dress-fit.md`, merged the same day): both cuts are built
  by the fitted wardrobe, each piece seated on its own cut; `npm run check:fit` measures both
  cuts on both bodies and the coverings on the neck (417 pieces on 26 bodies, all good).
  Three pieces fit only the body they were cut for and are kept off the other
  (`cutOnBody` in `data/bodies.json`: Lunden's fleece collar, Colonia's waistcoat buttons,
  Edo's great bow).

Still weak, and next:

- The two cuts of a home are still its "men's" and "women's" dress under other names; a third
  outfit for each home is the real variety and is not begun.
- Age is in the form only: no lines in the face, and the "old" body is a mild one.
- The builds do not reach a very fat or a very small body: MakeHuman's fullest weight is the
  end of the Weight measure.
- Coverings are two, plain, and one colour each; the scarf is close-fitting (no drape on the
  shoulders, which would need the chest's bones).
- No visible difference beyond the face's two scars.
- The home's own headgear is the old blocky kind and looks poorer beside the new coverings.
