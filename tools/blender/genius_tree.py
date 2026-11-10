"""WILDLINE genius kit, the bodies the genius tree needed and did not have (docs/genius-tree.md):
a drake and a bow. Every other base of the tree wears a body the kit already builds.

    python tools/blender/genius_tree.py                 # both bodies, their cards, a render of each
    python tools/blender/genius_tree.py beast-drake     # one

The drake is on the wolf's rig, so it walks and the ages shape it (data/genius-bodies.json,
ages). The bow is a modelled thing with the sockets the other relics have. Materials follow
docs/genius-forms.md, "Conventions": the coat's materials by the names the looks give roles
to, mark(<region>) for what a marking shows or hides, field(...) for what glows.

genius_kit.py loads this file (register()).
"""
import math
import os
import sys

import bpy  # noqa: F401  (mathutils is importable once bpy is)
from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z

gk = None       # genius_kit, given by register()
f2 = None       # genius_forms2: band
gr = None       # genius_relics: _eye
gh = None       # genius_homes: _beast, _table and the wolf's helpers

# The card of each body is the card of the settled form that wears it (data/genius-bases).
CARDS = {"beast-drake": "drake-hatchling", "relic-bow": "bow-childs-bow"}
RIMS = {"beast-drake": (0.95, 0.68, 0.25), "relic-bow": (0.85, 0.85, 1.0)}


def register(kit):
    global gk, f2, gr, gh
    import genius_forms2
    import genius_homes
    import genius_relics
    gk, f2, gr, gh = kit, genius_forms2, genius_relics, genius_homes
    kit.PALETTE.update({
        "wing": ((0.16, 0.2, 0.19), 0.6, 0.0), "drake_horn": ((0.72, 0.66, 0.5), 0.45, 0.0),
        "bowstring": ((0.8, 0.76, 0.66), 0.7, 0.0),
    })
    kit.BODIES.update({"beast-drake": drake_body, "relic-bow": bow_body})


# ======================================================================================
# The drake: a small dragon of the line's wild places, on the wolf's rig
# ======================================================================================

def drake_body():
    """The drake: long in the neck and longer in the tail, low on thick legs, a wedge of a
    head with two small horns, a ridge down the spine, wings it has not grown into folded
    along its flanks, and plates under it from throat to tail."""
    def shape(bk, r):
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (0.9, 1.0, 0.9))
        r.stretch_y(-0.6, 0.4, 1.12)
        r.leg_length(0.36)
        r.leg_girth(1.18)
        r.lengthen_chain(bk.NECK, gh._head(r), 1.9)
        r.scale(bk.NECK, r.bone("Neck1"), (0.8, 1.0, 0.8))
        r.rotate(bk.NECK + gh._head(r), r.bone("Neck1"), X, math.radians(-52))
        r.rotate(gh._head(r), r.bone("Neck3"), X, math.radians(50))
        r.scale_along(gh._head(r), r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.3)
        r.scale(gh._head(r), r.bone("Neck3"), (1.04, 1.0, 0.72))
        gh._ears(r, 0.3)
        r.lengthen_chain(gh._tail(r), [], 1.6)
        gh._tail_girth(r, (1.35, 1.0, 1.35))
        r.scale(r.family("Tail5"), r.bone("Tail5"), (0.5, 1.0, 0.5))
        r.rotate(gh._tail(r), r.bone("Tail1"), X, math.radians(34))
        r.damp_rotations(gh._tail(r), 0.4)

    def extra(bk, r):
        horn, wing = gk.mat("drake_horn"), gk.mat("wing")
        hb = r.bone("Head")
        crown = r.top(hb.y + 0.06, half_width=0.25)
        # two small horns, swept back
        horns = None
        for s in (1, -1):
            pts = [Vector((s * 0.1, hb.y + 0.1, crown - 0.05)), Vector((s * 0.14, hb.y + 0.26, crown + 0.1)), Vector((s * 0.15, hb.y + 0.44, crown + 0.16))]
            horns = g.merge(horns, g.tube(pts, [0.05, 0.034, 0.006], n=5))
        # a frill of two shorter spines behind each cheek
        for s in (1, -1):
            for k, (dz, ln) in enumerate(((-0.1, 0.24), (-0.2, 0.18))):
                base = Vector((s * 0.15, hb.y + 0.06, crown + dz))
                horns = g.merge(horns, g.cone(base, base + Vector((s * 0.1, ln, 0.02 - 0.03 * k)), 0.035, n=4))
        gk._add(r, "horns", horns, "Head", horn)
        # a ridge of plates from the back of the skull to the root of the tail
        r.fin("ridge", r.bone("Neck3").y, r.bone("Tail1").y, lambda t: 0.1 + 0.08 * math.sin(t * math.pi), gk.mark("ridge", horn), thickness=0.07, steps=24, sink=0.05, serrate=True)
        # and a smaller one along the tail
        r.fin("tail_ridge", r.bone("Tail1").y + 0.05, r.bone("Tail5").y, lambda t: 0.1 * (1.0 - t), gk.mark("ridge", horn), thickness=0.05, steps=12, sink=0.04, serrate=True)
        # plates under it
        # (between the legs only: under a leg the rig's "bottom" is the foot)
        fy, by = r.bone("FrontUpperLeg.L").y, r.bone("BackUpperLeg.L").y
        r.fin("belly", fy + (by - fy) * 0.24, fy + (by - fy) * 0.74, 0.03, gk.mat("fur_light"), thickness=0.34, steps=10, sink=0.06, under=True)
        # the wings, folded: three long fingers of membrane laid back along each flank from the shoulder
        sh = r.bone("FrontUpperLeg.L")
        y0 = sh.y + 0.02
        z0 = r.top(y0) - 0.1
        geo = None
        for s in (1, -1):
            x0 = s * (r.side(y0, z0) + 0.01)
            root = Vector((x0, y0, z0))
            elbow = root + Vector((s * 0.12, -0.2, 0.42))
            geo = g.merge(geo, g.tube([root, elbow], [0.055, 0.04], n=5))
            for k, (dy, dz, w) in enumerate(((1.5, 0.02, 0.3), (1.38, -0.22, 0.36), (1.12, -0.46, 0.32), (0.8, -0.62, 0.26))):
                tip = elbow + Vector((s * 0.03 * (3 - k), dy, dz - 0.1))
                geo = g.merge(geo, g.blade(elbow, tip, w, normal=(s, 0, 0.2), belly=0.55, thick=0.025))
            geo = g.merge(geo, g.cone(elbow, elbow + Vector((s * 0.03, -0.1, 0.1)), 0.022, n=4))
        gk._add(r, "wings_folded", geo, "Torso3", gk.mark("wings", wing))
        # the fire it has not learned yet, banked under the jaw
        n3 = r.bone("Neck3")
        n2 = r.bone("Neck2")
        d = (n3 - n2).normalized()
        under = Vector((0, -abs(d.z), -abs(d.y)))  # the front of a raised neck: forward is -Y
        gk._add(r, "throat", g.ico((n2 + n3) * 0.5 + under * 0.085, 0.07, sub=1, scale=(0.9, 1.0, 1.0)), "Neck3", gk.field("ember", 2.4))
        # a spade at the tail's end
        tip = r.bone("Tail8") if "Tail8" in r.all_bones() else r.bone("Tail5")
        back = (tip - r.bone("Tail5")).normalized() if (tip - r.bone("Tail5")).length > 1e-4 else Y
        gk._add(r, "spade", g.blade(tip, tip + back * 0.26, 0.2, normal=(0, 0.3, 1), belly=0.45, thick=0.03), "Tail8" if "Tail8" in r.all_bones() else "Tail5", gk.mark("tailtip", horn))
    return gh._beast(shape, extra, rough=(0.42, 0.5), marks=("socks", "mask", "saddle"), tail=True)


# ======================================================================================
# The bow: a recurved bow, strung, an arrow of the field on the string
# ======================================================================================

def _bow_curve(zc, half, n=17):
    """The limbs from the lower tip to the upper: back toward the hand's side (+Y) as they go
    out, and forward again at the tips. The grip is at y = 0."""
    pts = []
    for i in range(n):
        t = -1.0 + 2.0 * i / (n - 1)
        a = abs(t)
        y = 0.2 * a ** 1.5 - 0.13 * max(0.0, a - 0.7) ** 1.2 / 0.3 ** 1.2 * 0.6
        pts.append(Vector((0.0, y, zc + half * t)))
    return pts


def bow_body():
    """The bow: a short recurve of wood and horn, the grip bound, the string a little drawn,
    and on the string an arrow that is not wood: a line of the field, pointing where it
    means to go. An eye in the riser watches the same way."""
    wood, dark, cord, horn, string = gk.mat("wood"), gk.mat("leather_dark"), gk.mat("cord"), gk.mat("horn"), gk.mat("bowstring")
    zc, half = 0.46, 0.38
    pts = _bow_curve(zc, half)
    n = len(pts)
    rad = [0.011 + 0.014 * (1.0 - abs(-1.0 + 2.0 * i / (n - 1))) ** 0.7 for i in range(n)]
    items = [(g.tube(pts, rad, n=6, flat=0.6, up=Y), wood)]
    # the riser and its binding
    mid = n // 2
    items.append((g.tube(pts[mid - 2:mid + 3], [0.024, 0.028, 0.03, 0.028, 0.024], n=7, flat=0.85, up=Y), dark))
    wraps = None
    for k in range(6):
        p = pts[mid - 2].lerp(pts[mid + 2], (k + 0.5) / 6.0)
        wraps = g.merge(wraps, f2.band(p, 0.032, 0.03, 0.004, n=8, v=Y, sides=3))
    items.append((wraps, gk.mark("wrap", cord)))
    # horn at the tips, where the string sits
    tips = None
    for p, q in ((pts[0], pts[1]), (pts[-1], pts[-2])):
        d = (p - q).normalized()
        tips = g.merge(tips, g.cone(p - d * 0.01, p + d * 0.05, 0.016, n=5))
        tips = g.merge(tips, g.ico(p, 0.017, sub=0))
    items.append((tips, gk.mark("tips", horn)))
    # the string, a little drawn
    nock = Vector((0.0, pts[0].y + 0.07, zc + 0.012))
    items.append((g.tube([pts[0], nock, pts[-1]], [0.0035, 0.0035, 0.0035], n=4), string))
    # the arrow: of the field, from the string out past the riser
    head = Vector((0.0, -0.3, zc + 0.012))
    items.append((g.tube([nock, head], [0.006, 0.006], n=5), gk.field("pulse", 2.6)))
    items.append((g.cone(head, head + Vector((0, -0.09, 0)), 0.022, n=4), gk.field("pulse", 2.6)))
    fletch = None
    for a in (0.0, 2.1, 4.2):
        nrm = Vector((math.cos(a), 0, math.sin(a)))
        fletch = g.merge(fletch, g.blade(nock + Y * -0.01, nock + Y * -0.11 + nrm * 0.035, 0.03, normal=nrm.cross(Y), belly=0.5, thick=0.004))
    items.append((fletch, gk.field("pulse", 2.6)))
    # the eye in the riser, looking down the arrow
    items += gr._eye((0.0, -0.031, zc - 0.03), 0.014)
    ob = g.pieces("bow_body", items)
    return gk.Built([ob], gh._table(zc + half + 0.03, -0.05, zc, 0.06, {
        "socket_grip": [(0.0, 0.0, zc)], "socket_light": [tuple(nock.lerp(head, 0.5))], "socket_keepsake": [tuple(pts[2] + Vector((0, -0.01, -0.01)))],
        "socket_head": [tuple(pts[-1] + Z * 0.02)], "socket_mouth": [tuple(head)]}))


# ======================================================================================

def render_body(silhouette, path, view=None, card=True):
    """A body alone, as its card shows it."""
    gk.reset()
    built = gk.BODIES[silhouette]()
    if built.pose:
        built.pose()
    shown = [o for o in built.objects if o.type == "MESH"]
    gk.render(path, shown, rim=RIMS.get(silhouette, (0.42, 0.9, 0.55)), card=card, view=view or ((0.95, -1.1, 0.35) if silhouette == "relic-bow" else (0.8, -1.25, 0.35)))
    return path


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import genius_kit as kit            # registers this file's bodies with the rest
    me = sys.modules.get("genius_tree") or sys.modules[__name__]
    want = [a for a in sys.argv[1:] if a in CARDS] or list(CARDS)
    for sil in want:
        kit.build_body(sil)
        card = os.path.join(kit.OUT, "cards", CARDS[sil] + ".png")
        me.render_body(sil, card)
        kit.log("wrote", os.path.relpath(card, kit.ROOT))
        side = os.path.join(kit.SCRATCH, sil + "-side.png")
        me.render_body(sil, side, view=(1.3, -0.25, 0.25), card=False)
        kit.log("wrote", side)
