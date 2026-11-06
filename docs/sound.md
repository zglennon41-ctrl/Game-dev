# Sound: the score, the barks, the effects

**The score** (`data/music.json`, `game/assets/music/*.ogg`, composed and rendered by
`tools/score/compose.py`): a theme for the title, for each place of the Academy (the quad,
the yard, the hearth, the dormitory), for each zone, and for the Gate; a fight layer that
the `Music` node raises while foes are up in a zone; and stingers for the Pattern, the rite,
the Reckoning, and a posting done or lost. One motif runs through every piece; two tempos
(60 and 120) and one key family round D minor, so the fight layer sits on any zone. The
tracks are placeholders in the right shape: the data, the cues and the player are what
lasts. `python3 tools/score/compose.py --ogg` renders them all (ffmpeg writes the OGG).

**The barks** (`game/assets/voice/<temperament>_<kind>_<n>.ogg`, kinds: technique, hurt,
retreat, down, pattern, parry): a classmate speaks for the moment in their temperament's
voice; `Sfx.play_bark` picks one of up to four takes and will not speak twice within two
seconds. The lines are in `data/academy.json` (`cohort.fighting.calls`); the clips are made
by `tools/score/barks.py` when a speech synthesizer is available here, and nothing plays
until they exist.

**The effects** (`game/scripts/sfx.gd`): synthesized at start; the ambience is the halls' hum
or the line's wind.
