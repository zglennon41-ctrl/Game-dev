"""WILDLINE genius kit: the gifts of the four lines with no flesh (docs/genius-evolutions.md).

A hybrid wears its other base's gift on a body that is not that base's: a wolf under a Lurker's
cloak, a hawk with a Fiend's horns. So each gift is made to say whose it is from across a room:

    the Lurker    shadow-cloak (a ragged mantle and a thrown-back hood), watching-eye (one great eye on the brow)
    the Fiend     ember (a split coal with a tall flame), horns (long, swept, ringed with the field)
    the Ember     ember, glow (a halo of the field, rayed)
    the Fog       mist (a wreath of it at the breast, trailing), glow

    python tools/blender/parts_spirits.py      writes game/assets/genius/parts/<feature>.glb for the six

They are made the kit's way (genius_kit.PARTS, build_part): in a socket's own space, Z up,
facing -Y, a part of a pair made for the left. The shadow-cloak and the mist are surfaces; they
hang as parts because data/genius-bodies.json (featureSockets) gives each a place of its own:
the back, and the breast.
"""
import math
import sys

import bpy  # noqa: F401  (mathutils comes with it)
from mathutils import Vector

import genius_geo as g
from genius_geo import X, Z
import genius_kit as kit
from genius_kit import mat, field
import genius_relics as relics
import spirits_kit as sk


def shadow_cloak_part():
    """The Lurker's cloak, on its back: a ragged mantle of ink over the shoulders, a hood thrown
    back with nothing in it, the hem streaming behind, and one line of the field along its edge."""
    ink, edge = mat("ink"), mat("ink_edge")
    items = [(g.tongue([(0, -0.14, 0.0), (0, -0.02, 0.035), (0, 0.14, 0.03), (0, 0.3, 0.0)], [0.2, 0.26, 0.24, 0.1], thick=0.3, normal=Z), ink)]
    flaps, hem = None, None
    for s in (1, -1):
        pts = [Vector((s * 0.07, 0.03, 0.02)), Vector((s * 0.13, 0.04, -0.07)), Vector((s * 0.155, 0.07, -0.2)), Vector((s * 0.15, 0.12, -0.31))]
        flaps = g.merge(flaps, g.tongue(pts, [0.3, 0.32, 0.24, 0.03], thick=0.16, normal=(s, 0, 0.35)))
        hem = g.merge(hem, g.tube([pts[1] + Vector((s * 0.012, -0.16, 0)), pts[2] + Vector((s * 0.012, -0.12, 0)), pts[3] + Vector((s * 0.006, -0.01, 0))], [0.005, 0.005, 0.002], n=3))
    items += [(flaps, ink), (hem, field("hem", 1.8))]
    tat = None
    for i, (x, L) in enumerate(((-0.1, 0.2), (-0.04, 0.3), (0.03, 0.25), (0.1, 0.19))):
        b0 = Vector((x, 0.25, 0.0))
        tat = g.merge(tat, g.tongue([b0, b0 + Vector((x * 0.3, L * 0.5, 0.03)), b0 + Vector((x * 0.5, L, 0.07 + 0.02 * (i % 2)))], [0.075, 0.06, 0.004], thick=0.25, normal=Z))
    items.append((tat, edge))
    # the hood, thrown back, and the dark in it
    hood = g.loft([g.ring((0, y, z), rx, rz, n=8, u=X, v=Z) for y, z, rx, rz in ((-0.17, 0.04, 0.085, 0.07), (-0.1, 0.07, 0.1, 0.085), (0.0, 0.085, 0.075, 0.06), (0.09, 0.1, 0.03, 0.025), (0.14, 0.12, 0.004, 0.004))])
    items += [(hood, ink), (g.ico((0, -0.165, 0.045), 0.062, sub=1, scale=(1.0, 0.4, 0.85)), mat("void")),
              (sk.hoop((0, -0.172, 0.042), 0.086, 0.071, 0.009, n=10, u=X, v=Z, sides=3), edge)]
    return [kit._part("shadow-cloak", items)]


def watching_eye_part():
    """The Lurker's eye, on its brow: one great eye, upright, lidded in ink, with the dark standing up off it."""
    c = Vector((0, -0.012, 0.075))
    items = relics._eye(c, 0.046, lids=mat("ink"))
    lash = None
    for i, (x, L) in enumerate(((-0.05, 0.07), (-0.018, 0.11), (0.018, 0.1), (0.05, 0.065))):
        b0 = c + Vector((x, 0.01, 0.04))
        lash = g.merge(lash, g.tongue([b0, b0 + Vector((x * 0.5, 0.02, L * 0.6)), b0 + Vector((x * 0.9, 0.05, L))], [0.03, 0.022, 0.003], thick=0.3, normal=(0, -1, 0.3)))
    items.append((lash, mat("ink_edge")))
    items.append((sk.hoop(c + Vector((0, 0.006, 0)), 0.064, 0.066, 0.007, n=10, u=X, v=Z, sides=3), mat("ink")))
    return [kit._part("watching-eye", items)]


def ember_part():
    """An ember carried: a coal split open on the field, and its flame going up either side of
    whatever carries it and out in front, so that no body it is hung in can hide it."""
    c = Vector((0, -0.03, -0.02))
    items = [(g.ico(c, 0.05, sub=0, scale=(1.15, 1.0, 0.78), rot=(0.3, 0.2, 0.4)), mat("coal")),
             (g.ico(c + Vector((0, -0.006, 0.006)), 0.037, sub=0, rot=(0.1, 0.5, 0.2)), field("crack", 4.0))]
    lit, dark, cin = None, None, None
    for s in (1, -1):
        lit = g.merge(lit, g.tongue([c + Vector((s * 0.03, 0.01, 0.0)), c + Vector((s * 0.1, 0.0, 0.05)), c + Vector((s * 0.15, 0.03, 0.15)), c + Vector((s * 0.13, 0.07, 0.25))], [0.05, 0.075, 0.055, 0.004], thick=0.45, normal=(0, -1, 0.2)))
        dark = g.merge(dark, g.tongue([c + Vector((s * 0.04, 0.03, 0.0)), c + Vector((s * 0.12, 0.04, 0.04)), c + Vector((s * 0.175, 0.07, 0.11))], [0.05, 0.06, 0.004], thick=0.4, normal=(0, -1, 0.2)))
        cin = g.merge(cin, g.ico(c + Vector((s * 0.17, 0.05, 0.3)), 0.009, sub=0), g.ico(c + Vector((s * 0.11, 0.09, 0.36)), 0.007, sub=0))
    lit = g.merge(lit, g.tongue([c + Vector((0, -0.03, 0.0)), c + Vector((0.01, -0.09, 0.03)), c + Vector((0, -0.12, 0.11))], [0.045, 0.055, 0.004], thick=0.5, normal=(1, 0, 0)))
    items += [(lit, field("flame", 4.0)), (dark, mat("coal")), (cin, field("cinder", 3.0))]
    return [kit._part("ember", items)]


def horns_part():
    """A daemon's horns: long, swept up and back in a curve, ridged, ringed with the field at the root."""
    pts = [(0.036, 0.0, -0.014), (0.07, 0.004, 0.05), (0.092, 0.03, 0.12), (0.088, 0.075, 0.185), (0.064, 0.125, 0.225)]
    left = g.tube(pts, [0.027, 0.023, 0.017, 0.01, 0.002], n=5)
    ridges = None
    for t, r in ((0.3, 0.026), (0.55, 0.021), (0.8, 0.015)):
        a, b = Vector(pts[1]) * (1 - t) + Vector(pts[2]) * t, Vector(pts[2]) * (1 - t) + Vector(pts[3]) * t
        p = a * (1 - t) + b * t
        ridges = g.merge(ridges, g.tube([p - Vector((0, 0.004, 0.008)), p + Vector((0, 0.004, 0.008))], [r, r * 0.96], n=5))
    ring = g.tube([(0.042, 0.002, 0.0), (0.05, 0.004, 0.016)], [0.032, 0.03], n=5)
    return [kit._part("horns", [(g.merge(left, g.mirrored(left)), mat("horn")), (g.merge(ridges, g.mirrored(ridges)), mat("horn_ridge")),
                               (g.merge(ring, g.mirrored(ring)), field("ring", 2.2))])]


def glow_part():
    """A glow: a halo of the field's light round it, broken and tilted, rayed, with motes on it."""
    arcs, motes, rays = None, None, None
    for i in range(4):
        a0 = 2 * math.pi * i / 4 + 0.2
        arc = [(0.2 * math.cos(a0 + t), 0.2 * math.sin(a0 + t), 0.04 * math.sin(a0 + t)) for t in [0.2 * j for j in range(6)]]
        arcs = g.merge(arcs, g.tube(arc, [0.003, 0.011, 0.013, 0.013, 0.011, 0.003], n=4))
        am = a0 + 1.27
        motes = g.merge(motes, g.ico((0.2 * math.cos(am), 0.2 * math.sin(am), 0.04 * math.sin(am)), 0.017, sub=0))
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.1
        d = Vector((math.cos(a), math.sin(a), 0.2 * math.sin(a)))
        rays = g.merge(rays, g.blade(d * 0.235, d * (0.3 + 0.03 * (i % 2)), 0.022, normal=Z, belly=0.3, thick=0.004))
    inner = sk.hoop((0, 0, 0.0), 0.12, 0.12, 0.004, n=14, sides=3)
    return [kit._part("glow", [(arcs, field("glow", 2.4)), (motes, field("mote", 3.2)), (rays, field("ray", 1.8)), (inner, field("glow", 2.4))])]


def mist_part():
    """The Fog's mist, at its breast: a wreath of it, darker under and paler on top, and two
    long shreds of it trailing back along the flanks."""
    mist, dark, pale = mat("mist"), mat("mist_dark"), mat("mist_pale")
    lo, mid, hi = None, None, None
    for i in range(7):          # round the breast, from flank to flank
        a = math.pi * (1.08 + 0.84 * i / 6)          # from the left flank, round the front, to the right
        p = Vector((0.15 * math.cos(a), 0.11 * math.sin(a) + 0.04, 0.0))
        r = 0.06 + 0.012 * math.sin(i * 2.1)
        lo = g.merge(lo, g.ico(p + Vector((0, 0, -0.03)), r, sub=1, scale=(1.15, 1.0, 0.7), rot=(0, 0, a)))
        if i % 2 == 0:
            hi = g.merge(hi, g.ico(p + Vector((0, 0.0, 0.03)), r * 0.72, sub=1, scale=(1.15, 1.0, 0.6), rot=(0, 0, a)))
        else:
            mid = g.merge(mid, g.ico(p + Vector((0, -0.01, 0.01)), r * 0.85, sub=1, scale=(1.15, 1.0, 0.7), rot=(0, 0, a)))
    for s in (1, -1):
        mid = g.merge(mid, g.tongue([(s * 0.15, 0.05, 0.0), (s * 0.19, 0.2, 0.02), (s * 0.18, 0.36, -0.01), (s * 0.15, 0.5, 0.03)], [0.1, 0.085, 0.06, 0.006], thick=0.5, normal=(s, 0, 0.3)))
        hi = g.merge(hi, g.ico((s * 0.2, 0.44, 0.07), 0.028, sub=0, scale=(1.3, 1.0, 0.7)), g.ico((s * 0.17, 0.56, 0.1), 0.02, sub=0, scale=(1.3, 1.0, 0.7)))
    return [kit._part("mist", [(lo, dark), (mid, mist), (hi, pale)])]


PARTS = {"shadow-cloak": shadow_cloak_part, "watching-eye": watching_eye_part, "ember": ember_part, "horns": horns_part, "glow": glow_part, "mist": mist_part}


def register(k):
    k.PARTS.update(PARTS)


if __name__ == "__main__":
    register(kit)
    for name in [a for a in sys.argv[1:] if a in PARTS] or list(PARTS):
        kit.build_part(name)
