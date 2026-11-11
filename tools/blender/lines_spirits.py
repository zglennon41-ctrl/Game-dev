"""WILDLINE genius lines, the things with no flesh: the Lurker (a shadow), the Fiend (a wick),
the Ember (a flame) and the Fog (weather). docs/genius-evolutions.md, "The things with no
flesh", says what each line's `body` may say.

    python tools/blender/genius_lines.py lurker
    python tools/blender/genius_lines.py fiend fiend-wick-fiend fiend-stove-devil

None of them has a rig: each body is one object, built from pieces (spirits_kit.py) by its
line's own file (spirits_lurker.py, spirits_fiend.py, spirits_ember.py, spirits_fog.py), and
the game floats it or walks it by its silhouette's kind. A form's coat is named by the look
its silhouette wears, so the partner's coat goes on whichever body the form has.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _line(name):
    def build(form_id, level, spec, base):
        mod = __import__("spirits_" + name)
        mod.build(form_id, level, spec, base)
    return build


def register(builders):
    for name in ("lurker", "fiend", "ember", "fog"):
        if os.path.exists(os.path.join(HERE, "spirits_%s.py" % name)):
            builders[name] = _line(name)
