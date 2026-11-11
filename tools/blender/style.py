"""The game's one style, for the kits and the tools (data/style.json; docs/style.md).

The game holds every surface to the style when its material is made (game/scripts/style.gd).
This is the same rule on the art's side, so that what a kit makes is born on-style and the
game has nothing to move:

    import style
    color = style.conform("leather_dark", color)     # a Blender colour (linear, rgba)
    style.ramp("umber", 2)                           # a ramp's colour by step, 0 shadow to 4 light
    style.light("lamp")                              # what the lamp throws on a surface

A kit's material() calls conform() on the colour it is given, by the material's name: the
name says what class it is (materials.words), the class says which ramps it may lie on, and a
colour off them is moved to the nearest point of the nearest. Light (field_*, *_lit) and skin
are not moved. Nothing here needs Blender: colours are plain tuples.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_D = None
_RAMPS = {}


def data():
    global _D
    if _D is None:
        with open(os.path.join(ROOT, 'data', 'style.json')) as f:
            _D = json.load(f)
        for k, hexes in _D['ramps'].items():
            _RAMPS[k] = [rgb(h) for h in hexes]
    return _D


def rgb(hx):
    """'#RRGGBB' as an sRGB triple."""
    return tuple(int(hx[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def to_hex(c):
    return '#%02X%02X%02X' % tuple(max(0, min(255, int(round(x * 255)))) for x in c[:3])


def to_linear(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


def to_srgb(c):
    return tuple(max(0.0, x) * 12.92 if x <= 0.0031308 else 1.055 * max(0.0, x) ** (1 / 2.4) - 0.055 for x in c[:3])


def saturation(c):
    mx = max(c[:3])
    return 0.0 if mx <= 0.0001 else (mx - min(c[:3])) / mx


def _nearest(c, cls):
    """The nearest point to an sRGB colour on the ramps a class allows: (point, distance)."""
    data()
    best, best_d = tuple(c[:3]), None
    for rn in _D['materials']['classes'].get(cls, {}).get('ramps', []):
        pts = _RAMPS[rn]
        for a, b in zip(pts, pts[1:]):
            ab = [b[i] - a[i] for i in range(3)]
            t = sum((c[i] - a[i]) * ab[i] for i in range(3)) / max(1e-9, sum(x * x for x in ab))
            t = min(1.0, max(0.0, t))
            p = tuple(a[i] + ab[i] * t for i in range(3))
            d = sum((c[i] - p[i]) ** 2 for i in range(3)) ** 0.5
            if best_d is None or d < best_d:
                best, best_d = p, d
    return best, (best_d or 0.0)


def off_ramp(c, cls):
    return _nearest(c, cls)[1]


def material_class(name, srgb=None):
    """The class of a material by its name: the first word of materials.words its name carries."""
    key = name.lower()
    found = ''
    for word, cls in data()['materials']['words']:
        if word in key:
            found = cls
            break
    if '|' in found:
        alts = found.split('|')
        return min(alts, key=lambda a: off_ramp(srgb, a)) if srgb is not None else alts[0]
    return found


def conform_srgb(c, cls):
    """An sRGB colour as a surface of this class may be: itself if it is on a ramp, else moved."""
    d = data()
    if not cls or not d['materials']['classes'].get(cls, {}).get('ramps'):
        return tuple(c[:3])
    p, dist = _nearest(c, cls)
    ramps = d['materials']['classes'][cls]['ramps']
    cap = d['cap']
    if any(r in d['accents'] for r in ramps):
        cap = max(cap, d['accentCap'])
    if any(r in d.get('paths', []) for r in ramps):
        cap = max(cap, d.get('pathCap', cap))       # a genius's Path colours
    if dist <= d.get('tolerance', 0.03) and saturation(c) <= cap:
        return tuple(c[:3])
    return p


def conform(name, color):
    """A Blender colour (linear rgb or rgba) for the material of this name, on the style."""
    s = to_srgb(color)
    out = to_linear(conform_srgb(s, material_class(name, s)))
    return tuple(out) + tuple(color[3:]) if len(color) > 3 else tuple(out)


def on_style(name, color):
    """Whether a Blender colour is on the ramps its name's class allows."""
    s = to_srgb(color)
    cls = material_class(name, s)
    if not cls:
        return False
    if not data()['materials']['classes'][cls]['ramps']:
        return True
    return off_ramp(s, cls) <= data().get('tolerance', 0.03) + 0.002


def ramp(name, step, alpha=1.0):
    """A ramp's colour by step (0 shadow to 4 light), as a Blender colour."""
    data()
    return to_linear(_RAMPS[name][max(0, min(4, step))]) + (alpha,)


def light(name, what='cast', alpha=1.0):
    """One of the lights (lamp, fire, moon): what it throws ('cast') or how its source looks ('color')."""
    return to_linear(rgb(data()['lights'][name].get(what, data()['lights'][name]['color']))) + (alpha,)


def shape(name, alpha=1.0):
    return to_linear(rgb(data()['loud']['shapes'][name])) + (alpha,)


def smooth(living=True):
    """Whether a thing is smooth-shaded: the living are, the made keep their cut edges."""
    return bool(data()['shading']['smooth']['living' if living else 'made'])
