"""WILDLINE genius lines, the beasts with bodies of their own: the Tortoise and the Hawk
(docs/genius-evolutions.md, "The Tortoise and the Hawk"). Neither is on the wolf's rig: a
tortoise is its shell, built here plate by plate; a hawk is built along its spine in the
pose it holds (on the wing, hovering, stooping, on a perch it carries), with two wings the
game beats. The three forms of the Hawk that came down to run (the Harrier and its Finals)
are on the wolf's rig, as their base body is.

    python tools/blender/genius_lines.py tortoise
    python tools/blender/genius_lines.py hawk hawk-storm-kite hawk-post-eagle

A body's `body` is read as the Wolf's is (a form wears what its parent wears; null takes a
thing off; `build` merges key by key). The slots and their styles are in the docs.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, mark, PALETTE, STAND  # noqa: E402

GL = None       # genius_lines, whichever way it was started (set in register)

PALETTE.update({
    "moss": ((0.13, 0.2, 0.085), 1.0, 0.0), "moss_light": ((0.27, 0.36, 0.14), 1.0, 0.0), "leaf": ((0.17, 0.3, 0.12), 0.9, 0.0),
    "mud": ((0.17, 0.13, 0.09), 1.0, 0.0), "reed": ((0.4, 0.38, 0.2), 0.9, 0.0), "cloth_canvas": ((0.48, 0.43, 0.34), 0.95, 0.0),
    "tooth": ((0.76, 0.7, 0.56), 0.45, 0.0), "bone_paint": ((0.78, 0.74, 0.64), 0.7, 0.0), "coal_soot": ((0.035, 0.032, 0.03), 1.0, 0.0),
    "feather_down": ((0.74, 0.7, 0.62), 1.0, 0.0), "eye_night": ((0.012, 0.012, 0.016), 0.15, 0.0), "leather_jess": ((0.26, 0.15, 0.08), 0.7, 0.0),
    "brick": ((0.3, 0.2, 0.16), 0.95, 0.0), "plaster_mortar": ((0.5, 0.48, 0.43), 1.0, 0.0), "bark_thorn": ((0.14, 0.1, 0.07), 0.9, 0.0),
    # the lines builder's own, under the names the style knows them by
    "hide_maw": ((0.13, 0.025, 0.025), 0.6, 0.0), "hide_tongue": ((0.42, 0.12, 0.11), 0.5, 0.0), "hide_scar": ((0.6, 0.48, 0.44), 0.6, 0.0),
    "shade_smoke": ((0.1, 0.095, 0.11), 1.0, 0.0), "cloth_stripe": ((0.34, 0.12, 0.08), 0.95, 0.0),
})

# what is soft is shaded round; what is hard keeps its planes (an item may say for itself)
SOFT = ("feather", "fur", "cloth", "shade", "hide_tongue", "hide_maw", "field", "cord", "leather", "moss", "leaf", "mud", "reed", "bark", "wax")


def log(*a):
    print("[lines_beasts]", *a)


def pieces(name, items):
    """[(geometry, material[, smooth]), ...] as one object, each piece shaded as it should be."""
    obs = []
    for i, it in enumerate(items):
        geo, m = it[0], it[1]
        if not geo or not geo[0]:
            continue
        smooth = it[2] if len(it) > 2 else m.name.startswith(SOFT)
        obs.append(g.to_object("%s_%d" % (name, i), geo, m, smooth))
    return g.join(name, obs)


def rotx(a):
    return Matrix.Rotation(a, 4, "X")


def turned(geo, R, about=(0, 0, 0)):
    """A geometry turned by a 3x3 or 4x4 about a point."""
    c = V(about)
    R3 = R.to_3x3()
    return [c + R3 @ (V(p) - c) for p in geo[0]], list(geo[1])


def shifted(geo, d):
    d = V(d)
    return [V(p) + d for p in geo[0]], list(geo[1])


def hoop(centre, rx, rz, n=16, u=X, v=Z):
    c = V(centre)
    return [c + V(u) * (math.cos(2 * math.pi * i / n) * rx) + V(v) * (math.sin(2 * math.pi * i / n) * rz) for i in range(n + 1)]


def band(centre, rx, rz, r, n=16, u=X, v=Z, sides=4, flat=1.0):
    """A ring of tube: a hoop, a rim of light, a strap."""
    pts = hoop(centre, rx, rz, n, u, v)
    return g.tube(pts, [r] * len(pts), n=sides, caps=False, flat=flat)


def lantern(at, s, glow="lamp", strength=3.2):
    """A small caged lamp hanging from `at`: [(geometry, material), ...]."""
    at = V(at)
    c = at + Vector((0, 0, -s * 1.5))
    items = [
        (g.tube([at, at + Vector((0, 0, -s * 0.55))], s * 0.07, n=5), mat("metal_iron")),
        (g.lathe([(s * 0.12, s * 0.95), (s * 0.5, s * 0.6), (s * 0.56, s * 0.52)], n=6, centre=c), mat("metal_brass")),
        (g.lathe([(s * 0.52, -s * 0.62), (s * 0.3, -s * 0.8)], n=6, centre=c), mat("metal_brass")),
        (g.ico(c, s * 0.36, sub=1, scale=(1, 1, 1.25)), field(glow, strength)),
    ]
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p = c + Vector((math.cos(a) * s * 0.5, math.sin(a) * s * 0.5, 0))
        items.append((g.tube([p + Vector((0, 0, -s * 0.62)), p + Vector((0, 0, s * 0.55))], s * 0.05, n=4), mat("metal_iron")))
    return items


def chain(points, link=0.03, material="metal_iron"):
    """Links along a path: flattened beads, turned alternately."""
    geo = None
    pts = [V(p) for p in points]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / (link * 1.5)))
        for i in range(n):
            c = a.lerp(b, (i + 0.5) / n)
            geo = g.merge(geo, g.ico(c, link, sub=0, scale=(1.0, 0.55, 1.0) if i % 2 else (0.55, 1.0, 1.0)))
    return geo, mat(material)


def num(v, default=1.0):
    """A slot that is only a size: 1.2, ["style", 1.2], or nothing."""
    if v is None or v is False:
        return 0.0
    if v is True:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, (list, tuple)):
        return float(v[1]) if len(v) > 1 and isinstance(v[1], (int, float)) else default
    return default


# ======================================================================================
# The Tortoise
# ======================================================================================

TORTOISE_STAGE = {
    # the young of its kind is all dome and eyes; the Final is broad and heavy
    1: {"width": 0.2, "length": 0.215, "dome": 0.25, "round": 0.5, "rim": 0.13, "legs": 0.62, "girth": 0.9, "neck": 0.55, "head": 1.6, "tail": 0.5, "eyes": 2.3, "beak": 0.7},
    2: {"width": 0.215, "length": 0.265, "dome": 0.232, "round": 0.55, "rim": 0.145, "legs": 0.88, "girth": 0.95, "neck": 0.9, "head": 1.16, "tail": 0.8, "eyes": 1.25, "beak": 0.9},
    3: {"width": 0.235, "length": 0.3, "dome": 0.232, "round": 0.55, "rim": 0.15, "legs": 1.0, "girth": 1.0, "neck": 1.0, "head": 1.0, "tail": 1.0, "eyes": 1.0, "beak": 1.0},
    4: {"width": 0.262, "length": 0.335, "dome": 0.246, "round": 0.58, "rim": 0.158, "legs": 1.06, "girth": 1.16, "neck": 1.1, "head": 1.06, "tail": 1.15, "eyes": 1.0, "beak": 1.12},
}
# keys of `build` that multiply the stage's own (the rest replace it)
TORTOISE_TIMES = ("width", "length", "dome", "legs", "girth", "neck", "head", "tail", "eyes", "beak")


class Shell:
    """The tortoise's numbers, and where things are on it."""

    def __init__(self, level, spec):
        b = dict(TORTOISE_STAGE[min(4, max(1, level))])
        own = spec.get("build", {})
        for k, v in own.items():
            b[k] = b[k] * v if k in TORTOISE_TIMES else v
        self.level = level
        self.W, self.L = b["width"], b["length"]
        self.H, self.e = b["dome"], b["round"]
        self.flat = b.get("flat", 1.0)            # under 1: the top is cut flat at that share of the dome
        self.wedge = b.get("wedge", 0.0)          # the front stands higher than the back by this share
        self.legs, self.girth = b["legs"], b["girth"]
        self.stance = b.get("stance", 1.0)        # how wide it sets its feet
        self.lift = 0.15 * (self.legs - 1.0) + b.get("lift", 0.0)      # how high the whole shell rides
        self.rim = b["rim"] + self.lift
        self.neck, self.head, self.tail, self.eyes, self.beak = b["neck"], b["head"], b["tail"], b["eyes"], b["beak"]
        self.cy = 0.03
        self.top = self.at(0, self.cy)

    def q(self, x, y):
        return max(0.0, 1.0 - (x / self.W) ** 2 - ((y - self.cy) / self.L) ** 2)

    def at(self, x, y):
        """The height of the dome over (x, y)."""
        z = self.H * min(self.q(x, y) ** self.e, self.flat)
        z *= 1.0 + self.wedge * (-(y - self.cy) / self.L)
        return self.rim + 0.015 + z

    def normal(self, x, y):
        d = 0.004
        nx = self.at(x - d, y) - self.at(x + d, y)
        ny = self.at(x, y - d) - self.at(x, y + d)
        return Vector((nx, ny, 2 * d)).normalized()

    def on(self, x, y, up=0.0):
        """A point on the dome, lifted along its normal."""
        return Vector((x, y, self.at(x, y))) + self.normal(x, y) * up

    def frame(self, x, y):
        """A 4x4 that sets a thing made about the origin (Z up) on the dome at (x, y)."""
        n = self.normal(x, y)
        u = Vector((1, 0, 0)) - n * n.x
        u = u.normalized() if u.length > 1e-5 else Vector((1, 0, 0))
        v = n.cross(u)
        M = Matrix((u, v, n)).transposed().to_4x4()
        M.translation = Vector((x, y, self.at(x, y)))
        return M

    def edge(self, a, out=1.0, z=0.0):
        """A point on the rim at angle a (0 is the left side, -90 degrees the front)."""
        return Vector((math.cos(a) * self.W * out, self.cy + math.sin(a) * self.L * out, self.rim + z))


def _shell_rings(S, n=14):
    fs = (1.0, 1.035, 0.95, 0.8, 0.62, 0.42, 0.2, 0.07)
    rings = []
    for k, f in enumerate(fs):
        ring = []
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n
            x, y = S.W * f * math.cos(a), S.cy + S.L * f * math.sin(a)
            if k == 0:
                z = S.rim - 0.012
            elif k == 1:
                z = S.rim + 0.012
            else:
                z = S.at(x, y) - 0.012
            ring.append(Vector((x, y, z)))
        rings.append(ring)
    return rings


SCUTES = [(0.0, dy, 0.058) for dy in (-0.19, -0.095, 0.0, 0.095, 0.19)] + [(s * 0.125, dy, 0.052) for s in (1, -1) for dy in (-0.14, -0.047, 0.047, 0.14)]


def _scute_spots(S):
    """Where the thirteen scutes sit on this shell, and how large."""
    return [(x * S.W / 0.235, S.cy + y * S.L / 0.3, r * (S.W / 0.235 + S.L / 0.3) / 2) for x, y, r in SCUTES]


def _plate(S, x, y, r, h, sides=6, top=0.55, sink=0.012, squash=0.9):
    """One scute: a low six-sided plate lying on the dome."""
    geo = g.lathe([(r, -sink), (r * 0.94, h * 0.6), (r * top, h)], n=sides, phase=math.pi / sides)
    geo = ([Vector((p.x, p.y * squash, p.z)) for p in geo[0]], geo[1])
    return g.moved(geo, S.frame(x, y))


def tortoise_shell(S, items, style, size):
    hide, light, plate = mat("stone_hide"), mat("stone_light"), mat("stone_plate")
    rings = _shell_rings(S)
    under = [[Vector((p.x * 0.86, S.cy + (p.y - S.cy) * 0.9, S.rim - 0.03)) for p in rings[0]], [Vector((p.x * 0.6, S.cy + (p.y - S.cy) * 0.7, S.rim - 0.045)) for p in rings[0]]]
    items.append((g.loft(list(reversed(under)) + rings[:2], caps=True), light, True))        # the plastron and the lip
    shell_mat = {"iron": mat("metal_iron"), "map": mat("paper"), "moss": mat("moss"), "soft": hide, "smooth": hide}.get(style, plate)
    items.append((g.loft(rings[1:], caps=True), shell_mat, style in ("smooth", "soft", "moss", "young")))
    spots = _scute_spots(S)
    if style in ("dome", "lit", "dial", "worn"):
        # the scutes: five down the spine, four a side, a ring in the middle of each
        sc, rg = None, None
        for x, y, r in spots:
            sc = g.merge(sc, _plate(S, x, y, r, 0.02 * size, top=0.6))
            rg = g.merge(rg, shifted(_plate(S, x, y, r * 0.5, 0.012, top=0.5, sink=0.0), S.normal(x, y) * 0.02 * size))
        items += [(sc, hide, False), (rg, mark("rings", hide), False)]
        if style == "lit":
            # a cold light between its plates: the seams of the shell are the field's
            lit = None
            for x, y, r in spots:
                lit = g.merge(lit, _plate(S, x, y, r * 1.16, 0.006, top=0.98, sink=0.004))
            items.append((lit, field("seam", 1.5)))
    elif style == "young":
        # few plates, soft-edged, hardly raised: a shell that has not been anywhere yet
        sc = None
        for x, y, r in spots[:5]:
            sc = g.merge(sc, _plate(S, x * 1.0, y, r * 1.5, 0.01, top=0.75))
        items.append((sc, hide, True))
    elif style == "stones":
        # fieldstone: lumps of grey rock set in the dome, no two alike
        a, b2 = None, None
        for i, (x, y, r) in enumerate(spots):
            k = 1.0 + 0.3 * math.sin(i * 2.3)
            st = g.ico(S.on(x, y, 0.006 * size), r * 1.02 * k, sub=1, scale=(1.0, 0.9, 0.5 * size), rot=(-(y - S.cy) * 2.2 + 0.3 * math.sin(i), x * 2.6, i * 0.9))
            if i % 3 == 1:
                b2 = g.merge(b2, st)
            else:
                a = g.merge(a, st)
        items += [(a, hide, False), (b2, mat("slate_light"), False)]
    elif style == "ridges":
        # a row of raised ridges down its shell, one for each blow it stood under
        sc, rd = None, None
        for x, y, r in spots:
            sc = g.merge(sc, _plate(S, x, y, r, 0.016, top=0.7))
        items.append((sc, hide, False))
        for row, (sx, n, hgt) in enumerate(((0.0, 6, 0.085), (0.52, 4, 0.05), (-0.52, 4, 0.05))):
            for i in range(n):
                t = (i + 0.5) / n
                y = S.cy + S.L * (-0.78 + 1.56 * t) * (0.9 if sx else 1.0)
                x = sx * S.W * math.sqrt(max(0.0, 1.0 - ((y - S.cy) / S.L) ** 2))
                base = S.on(x, y, -0.01)
                h = hgt * size * (0.75 + 0.5 * math.sin(math.pi * t))
                n_ = S.normal(x, y)
                tip = base + n_ * h + Vector((0, 0.05 * size, 0))
                rd = g.merge(rd, g.blade(base + Vector((0, -0.06, 0)), tip, 0.035, normal=X if not sx else Vector((sx, 0, 0.6)), belly=0.55, thick=0.03))
                rd = g.merge(rd, g.blade(base + Vector((0, 0.075, 0)), tip, 0.035, normal=X if not sx else Vector((sx, 0, 0.6)), belly=0.5, thick=0.03))
        items.append((rd, mat("slate_light"), False))
    elif style == "iron":
        # dark iron crossed with pale lines, like a slate nobody has wiped
        sc = None
        for x, y, r in spots:
            sc = g.merge(sc, _plate(S, x, y, r * 1.04, 0.018, top=0.8, sides=5))
        items.append((sc, mat("metal_iron_light"), False))
        rd = None
        for i in range(5):
            t = (i + 0.5) / 5
            y = S.cy + S.L * (-0.7 + 1.4 * t)
            base = S.on(0, y, -0.01)
            tip = base + S.normal(0, y) * 0.05 * (0.7 + 0.5 * math.sin(math.pi * t)) + Vector((0, 0.04, 0))
            rd = g.merge(rd, g.blade(base + Vector((0, -0.06, 0)), tip, 0.03, normal=X, belly=0.55, thick=0.028))
            rd = g.merge(rd, g.blade(base + Vector((0, 0.07, 0)), tip, 0.03, normal=X, belly=0.5, thick=0.028))
        items.append((rd, mat("metal_iron"), False))
        sl = None
        for i in range(int(13 * size)):
            a = i * 2.39996
            rr = 0.25 + 0.62 * ((i * 7) % 11) / 11.0
            x0, y0 = S.W * rr * math.cos(a), S.cy + S.L * rr * math.sin(a)
            d = a + 1.2 + 0.9 * math.sin(i * 1.7)
            ln = 0.09 + 0.05 * math.sin(i * 3.1)
            x1, y1 = x0 + ln * math.cos(d), y0 + ln * math.sin(d)
            if S.q(x1, y1) < 0.08:
                continue
            p0, p1 = S.on(x0, y0, 0.024), S.on(x1, y1, 0.024)
            sl = g.merge(sl, g.tube([p0, (p0 + p1) / 2 + Vector((0, 0, 0.004)), p1], [0.006, 0.008, 0.004], n=4))
        items.append((sl, mat("hide_scar"), False))
    elif style == "map":
        # the lines on its shell are a map: coasts, a river, the places it has been
        ink = None
        for k, (rr, wob) in enumerate(((0.78, 0.09), (0.5, 0.12), (0.26, 0.08))):
            pts = []
            for i in range(19):
                a = 2 * math.pi * i / 18
                f = rr + wob * math.sin(a * 3 + k * 1.7) + 0.04 * math.sin(a * 7 + k)
                pts.append(S.on(S.W * f * math.cos(a), S.cy + S.L * f * math.sin(a), 0.006))
            ink = g.merge(ink, g.tube(pts, 0.0055, n=4, caps=False))
        river = [S.on(S.W * (-0.5 + 0.28 * t + 0.1 * math.sin(t * 5)), S.cy + S.L * (-0.75 + 1.4 * t / 4.0 * 1.0), 0.008) for t in (0, 1, 2, 3, 4)]
        items.append((ink, mat("ink"), False))
        items.append((g.tube(river, [0.012, 0.011, 0.01, 0.008, 0.006], n=4), mat("cloth_watch"), False))
        pins, heads = None, None
        for i, (fx, fy) in enumerate(((0.3, -0.45), (-0.34, 0.1), (0.1, 0.42), (-0.1, -0.2), (0.42, 0.2))[: 2 + int(3 * size)]):
            p = S.on(S.W * fx, S.cy + S.L * fy, 0.0)
            n_ = S.normal(S.W * fx, S.cy + S.L * fy)
            pins = g.merge(pins, g.tube([p, p + n_ * 0.05], 0.004, n=4))
            heads = g.merge(heads, g.ico(p + n_ * 0.058, 0.014, sub=0))
        items += [(pins, mat("metal_iron"), False), (heads, field("pins", 2.4))]
    elif style == "moss":
        # moss in cushions, the stone showing between
        a, b2 = None, None
        for i, (x, y, r) in enumerate(spots):
            k = 1.0 + 0.25 * math.sin(i * 1.9)
            lump = g.ico(S.on(x, y, 0.004), r * 1.12 * k, sub=1, scale=(1.0, 0.95, 0.55 * size))
            if i % 4 == 2:
                b2 = g.merge(b2, lump)
            else:
                a = g.merge(a, lump)
        items += [(a, mat("moss"), True), (b2, mat("moss_light"), True)]
    elif style == "soft":
        # no plates: leather over the bone, a flange all round
        fl = g.loft([[Vector((p.x * 1.16, S.cy + (p.y - S.cy) * 1.12, S.rim + 0.004)) for p in rings[1]], [Vector((p.x * 1.0, p.y, S.rim + 0.03)) for p in rings[1]]], caps=True)
        items.append((fl, hide, True))
        rg = None
        for x, y, r in spots[:5]:
            rg = g.merge(rg, shifted(_plate(S, x, y, r * 0.5, 0.006, top=0.6, sink=0.0), Vector((0, 0, 0.004))))
        items.append((rg, mark("rings", hide), True))
    if style in ("smooth", "worn"):
        # one mark of its own kind still shows: the rings, where its partner wears them
        rg = None
        for x, y, r in spots[:5]:
            rg = g.merge(rg, shifted(_plate(S, x, y, r * 0.42, 0.004, top=0.7, sink=0.0), S.normal(x, y) * 0.004))
        items.append((rg, mark("rings", hide), True))


def tortoise_rim(S, items, style, size):
    hide = mat("stone_hide")
    n = 14
    if style in ("marginals", "ward", "plaques", "serrated", "spikes"):
        rim, lit, carved = None, None, None
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n
            c = S.edge(a, 1.02, 0.02)
            front, back = math.sin(a) < -0.5, math.sin(a) > 0.5
            if style == "plaques":
                # name-plates round the rim, a few of them faintly lit
                rim = g.merge(rim, g.box(c + Vector((0, 0, 0.004)), (0.034, 0.108 * size, 0.07 * size), rot=(0, 0, a)))
                tag = g.box(S.edge(a, 1.065, 0.022), (0.008, 0.07 * size, 0.034 * size), rot=(0, 0, a))
                if i % 3 == 1:
                    lit = g.merge(lit, tag)
                elif i % 2 == 0:
                    carved = g.merge(carved, tag)
            else:
                rim = g.merge(rim, g.box(c, (0.03, 0.105, 0.036), rot=(0, 0, a)))
            if style == "serrated" and back:
                rim = g.merge(rim, g.cone(S.edge(a, 1.03, 0.02), S.edge(a, 1.03 + 0.2 * size, 0.0), 0.03, n=4))
            if style == "spikes" and front:
                rim = g.merge(rim, g.cone(S.edge(a, 1.03, 0.022), S.edge(a, 1.03 + 0.26 * size, 0.05), 0.028, n=4))
        items.append((rim, hide, False))
        if lit:
            items += [(lit, field("names", 1.6)), (carved, mat("bone_paint"), False)]
        if style == "ward":
            # ward-lines cut round the rim, and they glow
            items.append((band((0, S.cy, S.rim + 0.045), S.W * 1.045, S.L * 1.045, 0.011 * size, n=28, v=Y, sides=4), field("ward", 2.0)))
            runes = None
            for i in range(n):
                a = 2 * math.pi * (i + 0.5) / n
                runes = g.merge(runes, g.box(S.edge(a, 1.075, 0.02), (0.008, 0.02, 0.05 * size), rot=(0.3 * math.sin(i * 2.0), 0, a)))
            items.append((runes, field("ward", 2.0)))
        elif S.level >= 3:
            items.append((band((0, S.cy, S.rim + 0.05), S.W * 1.0, S.L * 1.0, 0.006, n=20, v=Y, sides=3), field("seam", 1.3)))
    elif style == "lip":
        # the young have no plates at the rim yet: a soft lip
        items.append((band((0, S.cy, S.rim + 0.004), S.W * 1.03, S.L * 1.03, 0.018, n=20, v=Y, sides=5), hide, True))


def tortoise_legs(S, items, style, size, feet):
    hide = mat("stone_hide")
    socks = mark("socks", hide)
    W, L = S.W, S.L
    g_ = S.girth
    for tag, sx, fy in (("fl", 1, -0.5), ("fr", -1, -0.5), ("bl", 1, 0.62), ("br", -1, 0.62)):
        y = S.cy + fy * L
        out = S.stance
        hip = Vector((sx * W * 0.62, y, S.rim + 0.01))
        if style == "web":
            # flat paddles, splayed
            a = Vector((sx * W * 1.04 * out, y + (-0.08 if fy < 0 else 0.08), 0.03))
            items.append((g.tube([hip, (hip + a) / 2 + Vector((0, 0, 0.01)), a], [0.05 * g_, 0.045 * g_, 0.03 * g_], n=6), hide, True))
            pad = g.tongue([a, a + Vector((sx * 0.05, -0.04 if fy < 0 else 0.05, -0.012)), a + Vector((sx * 0.1 * size, -0.08 if fy < 0 else 0.1, -0.02))], [0.07, 0.13 * size, 0.09 * size], thick=0.16, normal=Z)
            items.append((pad, socks, True))
            feet[tag] = a + Vector((sx * 0.06, 0, -0.02))
            continue
        tuck = 0.55 if style == "tucked" else 1.0
        fwd = (-0.045 if fy < 0 else 0.03) * tuck
        knee = Vector((sx * W * 0.9 * out * (0.9 if style == "tucked" else 1.0), y + fwd, (0.085 * S.legs + S.lift * 0.5) * tuck + 0.02 * (1 - tuck)))
        foot = Vector((sx * W * 0.93 * out * (0.88 if style == "tucked" else 1.0), y + fwd, 0.0))
        k = 1.25 if style == "set" else 1.0
        items.append((g.tube([hip, knee], [0.066 * g_, 0.058 * g_ * k], n=7), hide, True))
        items.append((g.tube([knee, foot + Z * 0.014, foot], [0.058 * g_ * k, 0.062 * g_ * k, 0.052 * g_ * k], n=7), socks, True))
        claws = None
        cl = (0.75 if style == "worn" else 1.0) * (1.25 if style == "set" else 1.0)
        for dx in (-0.03, 0.0, 0.03):
            c0 = foot + Vector((dx * k, -0.045 * g_ * k, 0.022))
            claws = g.merge(claws, g.cone(c0, c0 + Vector((dx * 0.3, -0.04 * cl, -0.018)), 0.014 * k, n=4))
        items.append((claws, mat("claw"), False))
        feet[tag] = foot


def tortoise_head(S, items, style, size, where):
    """The neck and the head. style: out (as its kind), peek (half out), in (drawn in), high
    (up and forward, a walker's), long (stretched to strike), low (down to the ground,
    listening). `where` is filled with the places sockets and carried things need."""
    hide, light, plate = mat("stone_hide"), mat("stone_light"), mat("stone_plate")
    base = Vector((0, S.cy - S.L * 0.74, S.rim + 0.045))
    r = 0.064 * S.head
    hidden = style == "hidden"
    if hidden:
        style = "in"
    Ln = {"out": 0.22, "peek": 0.085, "in": 0.03, "high": 0.3, "long": 0.36, "low": 0.25}[style] * (S.neck if style not in ("peek", "in") else 1.0) * (size if style in ("high", "long", "low") else 1.0)
    rise = {"out": 0.42, "peek": 0.2, "in": 0.0, "high": 0.9, "long": 0.12, "low": -0.55}[style]         # the neck's angle from level
    pitch = {"out": 0.12, "peek": 0.0, "in": -0.1, "high": 0.05, "long": 0.0, "low": -0.75}[style]      # the head's own
    d = Vector((0, -math.cos(rise), math.sin(rise)))
    end = base + d * Ln
    if style == "high":
        mid = base + Vector((0, -Ln * 0.35, Ln * 0.2))
    else:
        mid = base + d * Ln * 0.55 + Vector((0, 0, -0.012))
    if style != "in":
        items.append((g.tube([base + Vector((0, 0.05, -0.01)), mid, end], [0.072 * S.girth, 0.056 * S.girth, 0.05 * S.head], n=8), hide, True))
        if style not in ("peek",):
            for s in (1, -1):
                st = g.tongue([base + Vector((s * 0.06 * S.girth, 0.0, 0.01)), mid + Vector((s * 0.05 * S.girth, 0, 0.012)), end + Vector((s * 0.043 * S.head, 0, 0.01))], [0.022, 0.022, 0.012], thick=0.3, normal=(s, 0, 0.2))
                items.append((st, mark("stripes", hide), True))
    hf = Vector((0, -math.cos(pitch), math.sin(pitch)))        # the way the head looks
    hu = Vector((0, math.sin(pitch), math.cos(pitch)))
    c = end + hf * r * 0.8 + Vector((0, 0, 0.012))
    if style == "in":
        c = base + Vector((0, -0.035 if not hidden else 0.06, -0.005))
    roll = 0.5 if style == "low" else 0.0

    def P(x, y, z):       # a point about the head: x to its left, y back along it, z up
        v = Vector((x, 0, 0)) + (-hf) * y + hu * z
        if roll:
            v = Matrix.Rotation(roll, 3, hf) @ v
        return c + v

    def Rh(geo):
        M = Matrix((Vector((1, 0, 0)), -hf, hu)).transposed()
        if roll:
            M = Matrix.Rotation(roll, 3, hf) @ M
        return [c + M @ V(p) for p in geo[0]], list(geo[1])
    bk = S.beak
    brow, eyes = None, None
    er = 0.015 * S.eyes * (S.head ** 0.5)
    for s in (1, -1):
        brow = g.merge(brow, g.blade((s * r * 0.19, -r * 0.82, r * 0.52), (s * r * 1.03, r * 0.26, r * 0.6), r * 0.56, normal=(s * 0.4, -0.2, 1), belly=0.5))
        eyes = g.merge(eyes, g.ico((s * r * 0.75, -r * 0.33, r * 0.25), er, sub=1, scale=(0.6, 1.0, 0.85)))
    if hidden:
        # all the way in: two lights in the dark of the shell's mouth, and nothing else
        front = Vector((0, S.cy - S.L * 0.985, S.rim + 0.05))
        items.append((g.ico(front, 0.075 * S.girth, sub=1, scale=(1.1, 0.5, 0.62)), mat("coal_soot"), True))
        lights = None
        for s in (1, -1):
            lights = g.merge(lights, g.ico(front + Vector((s * 0.03, -0.03, 0.008)), er * 0.9, sub=0))
        items.append((lights, field("eyes", 3.0)))
    else:
        items.append((Rh(g.ico((0, 0, 0), r, sub=1, scale=(0.95, 1.28, 0.84))), hide, True))
        items.append((Rh(g.ico((0, -r * 0.24, -r * 0.4), r * 0.74, sub=1, scale=(0.92, 1.25, 0.5))), light, True))
        items.append((Rh(g.blade((0, -r * 0.82, -r * 0.18), (0, -r * (1.55 + 0.35 * (bk - 1)), -r * (0.46 + 0.4 * (bk - 1))), r * 0.8 * bk, normal=(0, 0, 1), belly=0.3)), mat("horn_ridge"), False))
        if style != "peek":
            items.append((Rh(brow), plate, False))
        items.append((Rh(eyes), field("eyes", 3.0)))
    where.update({"head": c, "hf": hf, "hu": hu, "r": r, "P": P, "Rh": Rh, "neck": (base + end) / 2 if style != "in" else base, "neck_r": 0.06 * S.girth,
                  "mouth": P(0, -r * 1.3, -r * 0.3), "crown": P(0, 0, r * 0.84), "base": base})
    if style == "in" and not hidden:
        # drawn in under the brow of its own shell
        f0 = Vector((0, S.cy - S.L * 0.82, S.at(0, S.cy - S.L * 0.82) + 0.004))
        items.append((g.tongue([f0, f0 + Vector((0, -S.L * 0.2, -0.012)), f0 + Vector((0, -S.L * 0.36, -0.05))], [S.W * 1.1, S.W * 0.95, S.W * 0.5], thick=0.16, normal=(0, 0, 1)), mat("stone_plate"), False))
        # and the dark of the shell's mouth round it
        items.append((g.ico(Vector((0, S.cy - S.L * 0.93, S.rim + 0.05)), 0.085 * S.girth, sub=1, scale=(1.15, 0.6, 0.72)), mat("coal_soot"), True))


def tortoise_tail(S, items, style, size):
    hide = mat("stone_hide")
    root = Vector((0, S.cy + S.L * 0.96, S.rim + 0.035))
    if style == "keel":
        # long, with a finned keel down it
        pts = [root, root + Vector((0, 0.16, -0.05)) * size, root + Vector((0, 0.36, -0.09)) * size, root + Vector((0, 0.56, -0.07)) * size]
        items.append((g.tube(pts, [0.05, 0.04, 0.026, 0.006], n=6), hide, True))
        fin = None
        for i in range(7):
            t = i / 6.0
            b = root.lerp(pts[-1], 0.08 + 0.8 * t) + Vector((0, 0, 0.02))
            fin = g.merge(fin, g.blade(b, b + Vector((0, 0.07, (0.14 - 0.06 * t) * size)), 0.09, normal=X, belly=0.45, thick=0.012))
        items.append((fin, mat("slate_light"), False))
    else:
        ln = (0.1 if style == "short" else 0.26) * S.tail * size
        items.append((g.cone(root, root + Vector((0, ln, -0.07 * min(1.5, ln / 0.1))), 0.032 * S.girth, n=5), hide, True))


# --- what it carries, and what has been done to it ---------------------------------------

def _stone(c, r, i=0, sc=(1.0, 0.9, 0.5), sub=1):
    return g.ico(c, r, sub=sub, scale=sc, rot=(0.2 * i, 0.3, 0.9 * i))


def carry_cairn(S, items, size, where):
    """A small cairn of pebbles rides on its shell. None has fallen off."""
    hide, light = mat("stone_hide"), mat("stone_light")
    z = S.top
    for i, (r, dz) in enumerate(((0.078, 0.024), (0.058, 0.072), (0.043, 0.112), (0.03, 0.144), (0.02, 0.17))[: 3 + int(round(2 * (size - 1.0) + 0.01)) if size >= 1 else 2]):
        items.append((_stone((0.006 * math.sin(i * 2.0), S.cy + 0.005 * math.cos(i * 1.3), z + dz * size), r * size, i, (1.0, 0.88, 0.5), sub=1 if i < 2 and size >= 1 else 0), light if i % 2 == 0 else hide, False))
    items.append((g.ico((0.004, S.cy + 0.003, z + 0.05 * size), 0.02 * size, sub=0), field("core", 3.4)))
    where["top"] = z + 0.19 * size


def carry_gnomon(S, items, size, where):
    """The plates of its shell are worn like the face of a dial, and its shadow tells the hour."""
    z = S.top
    c = Vector((0, S.cy, z))
    items.append((g.lathe([(0.2 * size, -0.006), (0.2 * size, 0.012), (0.185 * size, 0.018)], n=16, centre=c), mat("stone_light"), False))
    tip = c + Vector((0, 0.15 * size, 0.2 * size))
    blade_ = g.loft([[c + Vector((-0.012, -0.15 * size, 0.016)), c + Vector((0.012, -0.15 * size, 0.016)), c + Vector((0.012, 0.15 * size, 0.016)), c + Vector((-0.012, 0.15 * size, 0.016))],
                     [tip + Vector((-0.008, -0.01, 0)), tip + Vector((0.008, -0.01, 0)), tip + Vector((0.008, 0.0, 0)), tip + Vector((-0.008, 0.0, 0))]], caps=True)
    items.append((blade_, mat("metal_brass"), False))
    marks = None
    for i in range(12):
        a = 2 * math.pi * i / 12
        marks = g.merge(marks, g.box(c + Vector((math.cos(a) * 0.165 * size, math.sin(a) * 0.165 * size, 0.02)), (0.012, 0.04 if i % 3 else 0.06, 0.006), rot=(0, 0, a + math.pi / 2)))
    items.append((marks, field("hours", 1.4)))
    where["top"] = tip.z


def carry_post(S, items, size, where):
    """A post lamp is bolted to its shell."""
    foot = S.on(0, S.cy + 0.02, 0.0)
    top = foot + Vector((0, 0.0, 0.62 * size))
    arm = top + Vector((0, -0.2 * size, 0.07 * size))
    items.append((g.lathe([(0.085, -0.01), (0.085, 0.02), (0.045, 0.035), (0.03, 0.06)], n=8, centre=foot), mat("metal_brass"), False))
    bolts = None
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        bolts = g.merge(bolts, g.ico(foot + Vector((math.cos(a) * 0.068, math.sin(a) * 0.068, 0.024)), 0.012, sub=0))
    items.append((bolts, mat("metal_iron"), False))
    items.append((g.tube([foot, top, top + Vector((0, -0.07 * size, 0.07 * size)), arm], [0.024, 0.02, 0.016, 0.012], n=6), mat("metal_iron"), False))
    items.append((g.tube([top + Vector((0, 0, -0.16 * size)), top + Vector((0, -0.12 * size, -0.02 * size))], 0.008, n=4), mat("metal_iron"), False))
    items.extend(lantern(arm, 0.105 * size, "lamp", 3.8))
    where["top"] = arm.z + 0.02


def carry_milestone(S, items, size, where):
    """A number is cut in its shell, and repainted each year by somebody."""
    c = S.on(0, S.cy + S.L * 0.3, -0.02)
    w, h, t = 0.2 * size, 0.34 * size, 0.07
    prof = [(-w / 2, 0), (-w / 2, h * 0.7), (-w * 0.36, h * 0.92), (0, h), (w * 0.36, h * 0.92), (w / 2, h * 0.7), (w / 2, 0)]
    front = [c + Vector((x, -t / 2, z)) for x, z in prof]
    back = [c + Vector((x, t / 2, z)) for x, z in prof]
    items.append((g.loft([front, back], caps=True), mat("stone_light"), False))
    items.append((g.box(c + Vector((0, -t / 2 - 0.004, h * 0.55)), (w * 0.72, 0.008, h * 0.4)), mat("bone_paint"), False))
    num = None
    for i, x in enumerate((-0.045, 0.0, 0.045)):
        num = g.merge(num, g.box(c + Vector((x * size, -t / 2 - 0.01, h * 0.55)), (0.014, 0.008, (0.1 if i != 1 else 0.07) * size), rot=(0, 0.25 * (i - 1), 0)))
    items.append((num, mat("ink"), False))
    where["top"] = c.z + h


def carry_packs(S, items, size, where):
    """Strap marks are worn across its shell: the party's packs ride on it."""
    z = S.top
    c = Vector((0, S.cy, z))
    canvas, leather = mat("cloth_canvas"), mat("leather")
    items.append((g.box(c + Vector((0, 0.01, 0.055 * size)), (0.3 * size, 0.36 * size, 0.11 * size)), canvas, True))
    roll = g.tube([c + Vector((-0.15 * size, -0.1 * size, 0.155 * size)), c + Vector((0.15 * size, -0.1 * size, 0.155 * size))], 0.052 * size, n=8)
    items.append((roll, mat("cloth_wool"), True))
    items.append((g.box(c + Vector((0.04 * size, 0.09 * size, 0.17 * size)), (0.16 * size, 0.15 * size, 0.12 * size), rot=(0, 0, 0.2)), mat("leather_dark"), True))
    if size > 1.15:
        items.append((g.box(c + Vector((-0.07 * size, 0.07 * size, 0.27 * size)), (0.12 * size, 0.12 * size, 0.09 * size), rot=(0, 0, -0.3)), canvas, True))
    straps = None
    for y in (-0.1, 0.1):
        pts = [Vector((sx * S.W * 0.98, S.cy + y * size, S.rim + 0.03)) for sx in (1,)] + [S.on(S.W * 0.7, S.cy + y * size, 0.012), c + Vector((0.155 * size, y * size, 0.1 * size)),
                                                                                           c + Vector((-0.155 * size, y * size, 0.1 * size)), S.on(-S.W * 0.7, S.cy + y * size, 0.012), Vector((-S.W * 0.98, S.cy + y * size, S.rim + 0.03))]
        straps = g.merge(straps, g.tube(pts, 0.012, n=4, flat=0.4))
    items.append((straps, leather, True))
    where["top"] = z + (0.24 if size <= 1.15 else 0.32) * size


def carry_wagon(S, items, size, where):
    """Two small wheels are fitted under the hind edge of its shell, and a seat for the passenger."""
    wood, iron = mat("wood"), mat("metal_iron")
    r = 0.14 * size
    for sx in (1, -1):
        hub = Vector((sx * (S.W * 0.98 + 0.035), S.cy + S.L * 0.62, r))
        items.append((band(hub, r, r, 0.02, n=12, u=Y, v=Z, sides=4), mat("metal_iron_light"), True))
        items.append((g.ico(hub, 0.026, sub=0, scale=(1.2, 1, 1)), mat("metal_brass"), False))
        sp = None
        for k in range(6):
            a = k * math.pi / 3
            sp = g.merge(sp, g.tube([hub, hub + Vector((0, math.cos(a) * r, math.sin(a) * r))], 0.009, n=4))
        items.append((sp, wood, True))
    items.append((g.tube([Vector((-(S.W + 0.035), S.cy + S.L * 0.62, r)), Vector((S.W + 0.035, S.cy + S.L * 0.62, r))], 0.014, n=5), iron, False))
    # the seat: a bench with a rail, and a pole with a lamp for the road
    z = S.top
    c = Vector((0, S.cy + 0.03, z))
    items.append((g.box(c + Vector((0, 0, 0.03)), (0.3 * size, 0.2 * size, 0.035)), wood, False))
    items.append((g.box(c + Vector((0, 0.1 * size, 0.12 * size)), (0.3 * size, 0.03, 0.16 * size)), wood, False))
    rail = None
    for sx in (1, -1):
        rail = g.merge(rail, g.tube([c + Vector((sx * 0.14 * size, 0.1 * size, 0.2 * size)), c + Vector((sx * 0.15 * size, -0.02 * size, 0.13 * size)), c + Vector((sx * 0.15 * size, -0.09 * size, 0.03))], 0.011, n=4))
    items.append((rail, iron, False))
    items.append((g.box(c + Vector((0, 0.0, 0.062)), (0.24 * size, 0.15 * size, 0.035)), mat("cloth_stripe"), True))
    pole = c + Vector((-0.13 * size, 0.1 * size, 0.2 * size))
    tipp = pole + Vector((0.0, -0.02, 0.24 * size))
    items.append((g.tube([pole, tipp, tipp + Vector((-0.07 * size, 0, 0.02))], 0.009, n=4), iron, False))
    items.extend(lantern(tipp + Vector((-0.07 * size, 0, 0.02)), 0.07 * size, "lamp", 3.4))
    where["top"] = tipp.z


def carry_hearth(S, items, size, where):
    """An iron fire-pan is set in the hollow of its shell with coals in it."""
    z = S.top
    c = Vector((0, S.cy, z + 0.01))
    iron = mat("metal_iron")
    items.append((g.lathe([(0.05 * size, 0.0), (0.15 * size, 0.035 * size), (0.185 * size, 0.09 * size), (0.17 * size, 0.1 * size)], n=10, centre=c), iron, False))
    coals, glow = None, None
    for i in range(7):
        a = i * 2.39996
        rr = 0.085 * size * math.sqrt((i + 0.5) / 7.0) * 1.3
        p = c + Vector((math.cos(a) * rr, math.sin(a) * rr, 0.085 * size))
        if i % 2:
            coals = g.merge(coals, g.ico(p, 0.035 * size, sub=0, scale=(1, 1, 0.7)))
        else:
            glow = g.merge(glow, g.ico(p, 0.037 * size, sub=0, scale=(1, 1, 0.7)))
    items += [(coals, mat("coal"), False), (glow, field("coals", 3.2))]
    fl = None
    for i, (dx, dy, h) in enumerate(((0.0, 0.0, 0.2), (0.05, 0.03, 0.13), (-0.05, -0.02, 0.15), (0.01, -0.05, 0.1))):
        b = c + Vector((dx * size, dy * size, 0.09 * size))
        fl = g.merge(fl, g.tongue([b, b + Vector((0.02, 0, h * 0.5)) * size, b + Vector((-0.012, 0.01, h)) * size], [0.06 * size, 0.045 * size, 0.004], thick=0.5, normal=Y if i % 2 else X))
    items.append((fl, field("flame", 2.6)))
    # a tripod over it, and the kettle
    apex = c + Vector((0, 0, 0.36 * size))
    legs = None
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        legs = g.merge(legs, g.tube([c + Vector((math.cos(a) * 0.19 * size, math.sin(a) * 0.19 * size, 0.05 * size)), apex], 0.008, n=4))
    items.append((legs, iron, False))
    items.append((g.tube([apex, apex + Vector((0, 0, -0.07 * size))], 0.005, n=4), iron, False))
    kc = apex + Vector((0, 0, -0.12 * size))
    items.append((g.lathe([(0.018, 0.05), (0.05, 0.035), (0.062, -0.01), (0.04, -0.045)], n=8, centre=kc), mat("metal_dark"), False))
    items.append((g.tube([kc + Vector((0.05, 0, 0.0)), kc + Vector((0.095, 0, 0.03))], [0.012, 0.007], n=4), mat("metal_dark"), False))
    where["top"] = apex.z


def carry_lamps(S, items, size, where):
    """A lamp for each of the names along its rim, and a few of them are lit."""
    n = 8
    cups, flames, wax = None, None, None
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        p = S.edge(a, 1.04, 0.075)
        cups = g.merge(cups, g.lathe([(0.012, 0.0), (0.026, 0.012), (0.03, 0.03)], n=6, centre=p))
        wax = g.merge(wax, g.tube([p + Vector((0, 0, 0.015)), p + Vector((0, 0, 0.06 * size))], 0.013, n=4))
        if i % 3 != 2:
            f0 = p + Vector((0, 0, 0.06 * size))
            flames = g.merge(flames, g.blade(f0, f0 + Vector((0, 0, 0.055 * size)), 0.028, normal=Vector((math.cos(a), math.sin(a), 0)), belly=0.35, thick=0.014))
    items += [(cups, mat("metal_brass"), True), (wax, mat("wax"), True), (flames, field("candle", 3.2))]


def carry_balance(S, items, size, where):
    """With its head in it looks like a river stone; one stone rests on it, and the air above is still."""
    z = S.top
    items.append((_stone((0.0, S.cy, z + 0.03 * size), 0.07 * size, 1, (1.0, 0.85, 0.42)), mat("stone_light"), True))
    items.append((_stone((0.006, S.cy - 0.004, z + 0.075 * size), 0.04 * size, 2, (1.0, 0.9, 0.5)), mat("slate_light"), True))
    items.append((band((0, S.cy, z + 0.2 * size), S.W * 0.82, S.L * 0.82, 0.006, n=24, v=Y, sides=3), field("still", 1.2)))
    where["top"] = z + 0.2 * size


def carry_dial(S, items, size, where):
    """A small brass dial is set in its shell, and the needle points at the way out."""
    c = S.on(0, S.cy - S.L * 0.05, 0.0)
    r = 0.13 * size
    brass = mat("metal_brass")
    items.append((g.lathe([(r, -0.01), (r, 0.03), (r * 0.9, 0.04), (r * 0.86, 0.022)], n=14, centre=c), brass, False))
    items.append((g.lathe([(r * 0.86, 0.02), (0.0, 0.024)], n=14, centre=c), mat("paper"), False))
    needle = g.merge(g.blade(c + Vector((0, 0, 0.034)), c + Vector((r * 0.5, -r * 0.62, 0.034)), 0.03, normal=Z, belly=0.3, thick=0.008),
                     g.blade(c + Vector((0, 0, 0.034)), c + Vector((-r * 0.3, r * 0.38, 0.034)), 0.022, normal=Z, belly=0.3, thick=0.006))
    items.append((needle, field("needle", 3.4)))
    items.append((g.ico(c + Vector((0, 0, 0.04)), 0.014, sub=0), brass, False))
    # the rings of the deep, cut round it
    for k, f in enumerate((0.62, 0.82)):
        items.append((band((0, S.cy, S.at(S.W * f, S.cy) + 0.012), S.W * f, S.L * f, 0.005, n=24, v=Y, sides=3), field("rings", 1.2)))
    where["top"] = c.z + 0.05


def carry_salvage(S, items, size, where):
    """What it sits on, it has found: a spade, a sack, a marker flag."""
    z = S.top
    c = Vector((0, S.cy + 0.02, z))
    items.append((g.ico(c + Vector((0.03, 0.05, 0.05 * size)), 0.1 * size, sub=1, scale=(1.0, 1.1, 0.75)), mat("cloth_canvas"), True))
    items.append((g.tube([c + Vector((0.03, 0.05, 0.11 * size)), c + Vector((0.03, 0.05, 0.15 * size))], [0.03, 0.045], n=6), mat("cloth_canvas"), True))
    # the spade, across its back
    a, b = c + Vector((-0.16 * size, 0.2 * size, 0.03)), c + Vector((-0.08 * size, -0.2 * size, 0.1 * size))
    items.append((g.tube([a, b], 0.011, n=5), mat("wood"), False))
    items.append((g.blade(b, b + (b - a).normalized() * 0.13 * size, 0.1 * size, normal=Z, belly=0.3, thick=0.012), mat("metal_iron_light"), False))
    # the marker
    p = c + Vector((0.12 * size, -0.1 * size, 0.0))
    t = p + Vector((0, 0, 0.3 * size))
    items.append((g.tube([p, t], 0.007, n=4), mat("wood"), False))
    items.append((g.blade(t + Vector((0, 0, -0.01)), t + Vector((0, 0.13 * size, -0.05 * size)), 0.09 * size, normal=X, belly=0.25, thick=0.008), mat("cloth_stripe"), True))
    items.append((g.ico(c + Vector((-0.02, -0.08 * size, 0.03 * size)), 0.03 * size, sub=0), field("find", 3.0)))
    where["top"] = t.z


def carry_teeth(S, items, size, where):
    """A ring of great teeth is set round the crown of its shell, each in a place it chose."""
    geo = None
    n = 9
    for i in range(n):
        a = 2 * math.pi * i / n + 0.2
        f = 0.5
        x, y = S.W * f * math.cos(a), S.cy + S.L * f * math.sin(a)
        b = S.on(x, y, -0.01)
        out = Vector((math.cos(a), math.sin(a), 0))
        h = (0.15 + 0.07 * math.sin(i * 2.2)) * size
        geo = g.merge(geo, g.tongue([b, b + out * 0.035 + Vector((0, 0, h * 0.6)), b - out * 0.015 + Vector((0, 0, h))], [0.06 * size, 0.045 * size, 0.004], thick=0.7, normal=out))
    items.append((geo, mat("tooth"), False))
    items.append((g.ico(S.on(0, S.cy, 0.02), 0.035 * size, sub=1, scale=(1, 1, 0.6)), field("core", 2.6)))
    where["top"] = S.top + 0.2 * size


def carry_garden(S, items, size, where):
    """Moss and small ferns grow on its shell, and a seedling has taken root at the back."""
    leaf, wood = mat("leaf"), mat("root")
    ferns = None
    for i, (fx, fy) in enumerate(((0.4, -0.35), (-0.45, -0.1), (0.3, 0.2), (-0.2, 0.45), (0.0, -0.55), (-0.5, 0.3))):
        b = S.on(S.W * fx, S.cy + S.L * fy, 0.0)
        for k in range(4):
            a = k * math.pi / 2 + i
            d = Vector((math.cos(a), math.sin(a), 0))
            ferns = g.merge(ferns, g.tongue([b, b + d * 0.06 * size + Vector((0, 0, 0.09 * size)), b + d * 0.15 * size + Vector((0, 0, 0.06 * size))], [0.03, 0.055 * size, 0.004], thick=0.2, normal=Z))
    items.append((ferns, leaf, True))
    # the seedling: a small crooked tree at the back
    b = S.on(0.02, S.cy + S.L * 0.5, -0.01)
    t1 = b + Vector((0.02, 0.03, 0.11 * size))
    t2 = t1 + Vector((-0.03, 0.0, 0.08 * size))
    items.append((g.tube([b, t1, t2], [0.028 * size, 0.018 * size, 0.008], n=6), wood, False))
    crown = None
    for i, (dx, dy, dz, r) in enumerate(((0.0, 0.0, 0.03, 0.1), (0.08, 0.02, -0.03, 0.075), (-0.07, -0.03, -0.02, 0.07), (0.01, 0.07, -0.05, 0.065))):
        crown = g.merge(crown, g.ico(t2 + Vector((dx, dy, dz)) * size, r * 1.05 * size, sub=1, scale=(1, 1, 0.8)))
    items.append((crown, mat("moss_light"), True))
    roots = None
    for i, sx in enumerate((1, -1, 1)):
        p0 = S.on(sx * S.W * 0.3, S.cy + S.L * (0.4 - 0.3 * i), 0.004)
        p1 = S.on(sx * S.W * 0.75, S.cy + S.L * (0.3 - 0.25 * i), 0.006)
        p2 = Vector((sx * S.W * 1.04, S.cy + S.L * (0.25 - 0.25 * i), S.rim - 0.06))
        roots = g.merge(roots, g.tube([p0, p1, p2], [0.014, 0.011, 0.004], n=4))
    items.append((roots, wood, False))
    where["top"] = t2.z + 0.1 * size


def carry_reeds(S, items, size, where):
    """Mud to the eyes: reeds and a cat's-tail stand on its back as on the bank."""
    reeds, heads = None, None
    for i, (fx, fy, h) in enumerate(((0.3, 0.3, 0.3), (-0.2, 0.45, 0.38), (0.0, 0.2, 0.26), (-0.45, 0.1, 0.22), (0.45, -0.05, 0.2))):
        b = S.on(S.W * fx, S.cy + S.L * fy, -0.005)
        t = b + Vector((0.03 * math.sin(i * 2.0), 0.02, h * 0.72 * size))
        reeds = g.merge(reeds, g.tube([b, t], [0.007, 0.004], n=4))
        if i < 2:
            heads = g.merge(heads, g.tube([t + Vector((0, 0, -0.09 * size)), t + Vector((0, 0, -0.01))], 0.015, n=6))
        else:
            reeds = g.merge(reeds, g.blade(b + Vector((0, 0, h * 0.4 * size)), t + Vector((0.06, 0.02, -0.02)), 0.025, normal=Y, belly=0.4, thick=0.004))
    items += [(reeds, mat("reed"), True), (heads, mat("mud"), True)]
    where["top"] = S.top + 0.3 * size


def carry_anvil(S, items, size, where):
    """A flat bright plate on the crown of its shell, dented and ringing: an anvil's."""
    z = S.top
    c = Vector((0, S.cy, z))
    iron, bright = mat("metal_iron"), mat("metal_iron_light")
    items.append((g.box(c + Vector((0, 0, 0.02)), (0.16 * size, 0.2 * size, 0.05)), iron, False))            # the foot
    items.append((g.box(c + Vector((0, 0, 0.07 * size)), (0.09 * size, 0.12 * size, 0.07 * size)), iron, False))   # the waist
    top = c + Vector((0, 0, 0.13 * size))
    items.append((g.box(top, (0.15 * size, 0.3 * size, 0.06 * size)), bright, False))                     # the face
    items.append((g.cone(top + Vector((0, -0.15 * size, 0.0)), top + Vector((0, -0.32 * size, 0.02 * size)), 0.035 * size, n=6), bright, False))    # the horn
    items.append((g.box(top + Vector((0, 0.17 * size, 0.012 * size)), (0.11 * size, 0.06 * size, 0.035 * size)), iron, False))                    # the heel
    items.append((band(top + Vector((0, 0, 0.034 * size)), 0.055 * size, 0.08 * size, 0.005, n=14, v=Y, sides=3), field("ring", 2.2)))
    where["top"] = top.z + 0.04 * size


def carry_stele(S, items, size, where):
    """It was the witness: a sworn stone stands on it, and the Terms are cut in it small and deep."""
    c = S.on(0, S.cy + S.L * 0.18, -0.02)
    w, h, t = 0.19 * size, 0.42 * size, 0.06
    prof = [(-w / 2, 0), (-w * 0.44, h * 0.86), (-w * 0.2, h), (w * 0.26, h * 0.97), (w * 0.46, h * 0.8), (w / 2, 0)]
    items.append((g.loft([[c + Vector((x, -t / 2, z)) for x, z in prof], [c + Vector((x, t / 2, z)) for x, z in prof]], caps=True), mat("slate"), False))
    lines = None
    for i in range(6):
        zz = h * (0.2 + 0.105 * i)
        lines = g.merge(lines, g.box(c + Vector((0.008 * math.sin(i * 2.0), -t / 2 - 0.004, zz)), (w * (0.7 - 0.04 * (i % 3)), 0.008, 0.012)))
    items.append((lines, field("terms", 1.8)))
    items.append((g.ico(c + Vector((0, -t / 2 - 0.008, h * 0.86)), 0.022 * size, sub=0, scale=(1, 0.4, 1)), mat("metal_brass"), False))
    where["top"] = c.z + h


def carry_ward(S, items, size, where):
    """Where it stops there is a post: four small pillars at the corners of its shell, and the
    air between them standing like glass."""
    slate = mat("slate_light")
    tops = []
    for sx in (1, -1):
        for sy in (-1, 1):
            b = S.on(sx * S.W * 0.6, S.cy + sy * S.L * 0.58, -0.01)
            t = Vector((b.x, b.y, S.top + 0.2 * size))
            items.append((g.tube([b, t], [0.026, 0.02], n=5), slate, False))
            items.append((g.ico(t + Vector((0, 0, 0.012)), 0.026, sub=0), field("ward", 2.6)))
            tops.append(t)
    z = S.top + 0.2 * size
    # the standing air: ribs of the field between the pillars, meeting over the middle
    apex = Vector((0, S.cy, z + 0.16 * size))
    ribs = None
    for t in tops:
        ribs = g.merge(ribs, g.tube([t, t.lerp(apex, 0.55) + Vector((0, 0, 0.07 * size)), apex], [0.006, 0.005, 0.004], n=3))
    for a, b in ((tops[0], tops[1]), (tops[1], tops[3]), (tops[3], tops[2]), (tops[2], tops[0])):
        ribs = g.merge(ribs, g.tube([a, (a + b) / 2 + Vector((0, 0, 0.03 * size)), b], 0.004, n=3))
    items.append((ribs, field("air", 1.3)))
    where["top"] = apex.z


def carry_pebbles(S, items, size, where):
    """The cairn, kept small on its shoulder where the crown of the shell is taken."""
    x, y = -S.W * 0.5, S.cy - S.L * 0.42
    b = S.on(x, y, 0.0)
    for i, (r, dz) in enumerate(((0.04, 0.012), (0.03, 0.04), (0.02, 0.062))):
        items.append((_stone(b + Vector((0.004 * i, 0.0, dz * size)), r * size, i, (1.0, 0.88, 0.5), sub=0), mat("stone_light") if i % 2 == 0 else mat("stone_hide"), False))


TORTOISE_CARRY = {"pebbles": carry_pebbles, "cairn": carry_cairn, "gnomon": carry_gnomon, "post": carry_post, "milestone": carry_milestone, "packs": carry_packs, "wagon": carry_wagon,
                  "hearth": carry_hearth, "lamps": carry_lamps, "balance": carry_balance, "dial": carry_dial, "salvage": carry_salvage, "teeth": carry_teeth,
                  "garden": carry_garden, "reeds": carry_reeds, "anvil": carry_anvil, "stele": carry_stele, "ward": carry_ward}


def tortoise_jaw(S, items, style, size, where):
    """What is at its mouth or its brow."""
    P, Rh, r, c = where["P"], where["Rh"], where["r"], where["head"]
    if style == "hook":
        # a great hooked beak, like a latch at the shell's edge
        items.append((Rh(g.tongue([(0, -r * 0.5, r * 0.1), (0, -r * 1.5, -r * 0.05), (0, -r * (1.9 + 0.3 * size), -r * 0.75 * size)], [r * 1.5, r * 1.0, r * 0.08], thick=0.8, normal=(0, 0, 1))), mat("horn"), False))
        items.append((Rh(g.tongue([(0, -r * 0.4, -r * 0.5), (0, -r * 1.3, -r * 0.62), (0, -r * 1.6, -r * 0.5)], [r * 1.2, r * 0.8, r * 0.1], thick=0.5, normal=(0, 0, -1))), mat("horn_ridge"), False))
    elif style == "gape":
        # jaws open, and a ring of pale light closing round them
        items.append((Rh(g.tongue([(0, -r * 0.5, r * 0.2), (0, -r * 1.6, r * 0.5), (0, -r * 2.2 * size, r * 0.2)], [r * 1.5, r * 1.1, r * 0.1], thick=0.7, normal=(0, 0, 1))), mat("horn"), False))
        items.append((Rh(g.tongue([(0, -r * 0.4, -r * 0.5), (0, -r * 1.4, -r * 1.1), (0, -r * 2.0 * size, -r * 1.1)], [r * 1.3, r * 1.0, r * 0.1], thick=0.5, normal=(0, 0, -1))), mat("horn_ridge"), False))
        items.append((Rh(g.ico((0, -r * 0.9, -r * 0.25), r * 0.55, sub=1, scale=(1.0, 1.3, 0.7))), mat("hide_maw"), True))
        items.append((Rh(band((0, -r * 1.5, -r * 0.3), r * 1.5 * size, r * 1.5 * size, r * 0.11, n=18, u=X, v=Z, sides=4)), field("ring", 2.8)))
    elif style == "chain":
        # a length of chain trails from its beak; it has not opened its mouth to drop it
        items.append((Rh(g.tongue([(0, -r * 0.5, r * 0.1), (0, -r * 1.5, -r * 0.1), (0, -r * 1.95, -r * 0.7)], [r * 1.6, r * 1.15, r * 0.1], thick=0.9, normal=(0, 0, 1))), mat("horn"), False))
        m = where["mouth"]
        pts = [m + Vector((-0.01, 0.01, -0.02)), m + Vector((-0.1, 0.05, -0.13)), Vector((-S.W * 0.98, m.y + 0.2, 0.035)), Vector((-S.W * 1.34, S.cy + 0.02, 0.03)), Vector((-S.W * 1.18, S.cy + S.L * 0.8 * size, 0.03))]
        items.append((chain(pts, 0.034 * (0.8 + 0.2 * size))[0], mat("metal_iron_light"), True))
        items.append((band(pts[-1] + Vector((-0.02, 0.07, 0.02)), 0.06, 0.06, 0.014, n=10, u=X, v=Y, sides=4), mat("metal_iron_light"), True))
    elif style == "horn":
        # a blunt horn of shell stands over its brow
        b = Vector((0, S.cy - S.L * 0.9, S.at(0, S.cy - S.L * 0.8) + 0.0))
        tip = b + Vector((0, -0.2 * size, 0.1 * size))
        items.append((g.tube([b + Vector((0, 0.12, -0.03)), b, tip], [0.13 * size, 0.1 * size, 0.035 * size], n=7), mat("stone_plate"), False))
        items.append((g.ico(tip, 0.045 * size, sub=1, scale=(1, 1.1, 0.8)), mat("hide_scar"), False))
        scr = None
        for i, dx in enumerate((-0.07, -0.02, 0.04, 0.09)):
            p0 = Vector((dx * size * 1.2, S.cy - S.L * 0.97, S.rim + 0.07 + 0.02 * (i % 2)))
            scr = g.merge(scr, g.box(p0, (0.012, 0.03, 0.09 * size), rot=(0.2, 0.2 * (i - 1.5), 0)))
        items.append((scr, mat("hide_scar"), False))
    elif style == "lure":
        # a small light hangs from its jaw on a stalk, over the water
        m = P(0, -r * 0.2, r * 0.8)
        pts = [m, m + Vector((0, -0.08, 0.16)) * size, m + Vector((0, -0.24, 0.2)) * size, m + Vector((0, -0.34, 0.1)) * size]
        items.append((g.tube(pts, [0.016, 0.012, 0.008, 0.005], n=5), mat("stone_hide"), True))
        items.append((g.ico(pts[-1] + Vector((0, -0.01, -0.035 * size)), 0.04 * size, sub=1, scale=(1, 1, 1.2)), field("lure", 4.2)))
        items.append((Rh(g.tongue([(0, -r * 0.4, -r * 0.5), (0, -r * 1.3, -r * 1.0), (0, -r * 1.8, -r * 0.9)], [r * 1.5, r * 1.2, r * 0.2], thick=0.5, normal=(0, 0, -1))), mat("stone_light"), True))
        items.append((Rh(g.ico((0, -r * 0.8, -r * 0.3), r * 0.5, sub=1, scale=(1.0, 1.3, 0.6))), mat("hide_maw"), True))
    elif style == "old":
        # old eyes: heavy pale brows, and the skin of its neck in folds
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.blade((s * r * 0.3, -r * 0.6, r * 0.62), (s * r * 1.5 * size, r * 0.5, r * 0.45), r * 0.5, normal=(s * 0.4, -0.2, 1), belly=0.5))
        items.append((Rh(geo), mat("bone_paint"), True))
        nk = where["neck"]
        for k in range(2):
            items.append((band(nk + Vector((0, 0.03 * k - 0.01, 0.0)), where["neck_r"] * 1.12, where["neck_r"] * 1.12, 0.008, n=10, u=X, v=Z, sides=4), mat("stone_light"), True))
    elif style == "trumpet":
        # it listens at the ground like someone at a door: an ear-horn, strapped on
        b = P(-r * 0.9, r * 0.25, r * 0.15)
        d = (P(-r * 2.1, r * 0.0, -r * 0.75) - b) * size
        items.append((g.tube([b, b + d * 0.5, b + d * 0.86, b + d], [0.012, 0.022, 0.05 * size, 0.07 * size], n=8, caps=False), mat("metal_brass"), False))
        items.append((Rh(band((0, r * 0.25, 0), r * 1.0, r * 0.9, 0.008, n=10, u=X, v=Z, sides=4)), mat("leather"), True))
    elif style == "snorkel":
        # only the nostrils show: a long thin snout held just out of the water
        items.append((Rh(g.tube([(0, -r * 0.7, r * 0.0), (0, -r * 1.7, r * 0.15), (0, -r * (2.3 + 0.6 * size), r * 0.5)], [r * 0.5, r * 0.3, r * 0.16], n=6)), mat("stone_hide"), True))
    elif style == "notched":
        # its beak is notched from large bones
        items.append((Rh(g.tongue([(0, -r * 0.5, r * 0.15), (0, -r * 1.6, 0.0), (0, -r * 2.2 * size, -r * 0.5)], [r * 1.55, r * 1.2, r * 0.3], thick=0.8, normal=(0, 0, 1))), mat("horn"), False))
        nt = None
        for i, y in enumerate((-1.1, -1.5, -1.85)):
            nt = g.merge(nt, g.cone((r * 0.5, y * r, -r * 0.1), (r * 0.6, y * r - r * 0.05, -r * 0.5), r * 0.14, n=4))
            nt = g.merge(nt, g.cone((-r * 0.5, y * r, -r * 0.1), (-r * 0.6, y * r - r * 0.05, -r * 0.5), r * 0.14, n=4))
        items.append((Rh(nt), mat("tooth"), False))


def tortoise_marks(S, items, style, size, where):
    """What its travels and its work have done to the shell."""
    if style == "dust":
        # travel-stained to the rim
        items.append((band((0, S.cy, S.rim + 0.07), S.W * 0.985, S.L * 0.985, 0.03 * size, n=24, v=Y, sides=4, flat=0.35), mat("mud"), True))
    elif style == "mud":
        # mud to the eyes
        items.append((band((0, S.cy, S.rim + 0.03), S.W * 1.08, S.L * 1.06, 0.05 * size, n=24, v=Y, sides=5, flat=0.6), mat("mud"), True))
        blobs = None
        for i in range(7):
            a = i * 0.9 + 0.3
            blobs = g.merge(blobs, g.ico(S.on(S.W * 0.55 * math.cos(a), S.cy + S.L * 0.55 * math.sin(a), 0.0), 0.05 + 0.02 * math.sin(i * 2.0), sub=1, scale=(1, 1, 0.3)))
        items.append((blobs, mat("mud"), True))
    elif style == "soot":
        # its neck is sooty
        nk = where["neck"]
        items.append((g.ico(nk + Vector((0, 0.0, 0.015)), where["neck_r"] * 1.25, sub=1, scale=(1.05, 1.6, 0.9)), mat("coal_soot"), True))
    elif style == "straps":
        st = None
        for y in (-0.12, 0.1):
            pts = [Vector((sx * S.W * 0.99, S.cy + y, S.rim + 0.03)) for sx in (1,)] + [S.on(S.W * f, S.cy + y, 0.01) for f in (0.75, 0.4, 0.0, -0.4, -0.75)] + [Vector((-S.W * 0.99, S.cy + y, S.rim + 0.03))]
            st = g.merge(st, g.tube(pts, 0.014, n=4, flat=0.35))
        items.append((st, mat("leather"), True))
    elif style == "hoop":
        # an iron band round the shell, to hold what it has taken
        items.append((band((0, S.cy, S.rim + 0.06), S.W * 1.03, S.L * 1.03, 0.016 * size, n=24, v=Y, sides=4, flat=0.5), mat("metal_iron"), False))
        for k, y in enumerate((-0.1, 0.12)):
            pts = [Vector((S.W * 1.0, S.cy + y, S.rim + 0.04))] + [S.on(S.W * f, S.cy + y, 0.012) for f in (0.7, 0.35, 0.0, -0.35, -0.7)] + [Vector((-S.W * 1.0, S.cy + y, S.rim + 0.04))]
            items.append((g.tube(pts, 0.013 * size, n=4, flat=0.4), mat("metal_iron"), False))
    elif style == "weeds":
        # the bog's own weed, trailing
        geo = None
        for i in range(6):
            a = 0.5 + i * 1.0
            b = S.edge(a, 1.0, 0.03)
            geo = g.merge(geo, g.tongue([b, b + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, -0.07)), b + Vector((math.cos(a) * 0.07, math.sin(a) * 0.09, -0.15 * size))], [0.035, 0.03, 0.004], thick=0.2, normal=Vector((math.cos(a), math.sin(a), 0.3))))
        items.append((geo, mat("moss"), True))


def tortoise(form_id, level, spec, base):
    kit.reset()
    S = Shell(level, spec)
    items, feet, where = [], {}, {}
    opt, each = GL.opt, GL.each
    style, size = opt(spec.get("shell", "dome"))
    tortoise_shell(S, items, style or "dome", size)
    style, size = opt(spec.get("rim", "marginals"))
    if style and style != "none":
        tortoise_rim(S, items, style, size)
    style, size = opt(spec.get("legs", "stump"))
    tortoise_legs(S, items, style or "stump", size, feet)
    style, size = opt(spec.get("neck", "out"))
    tortoise_head(S, items, style or "out", size, where)
    style, size = opt(spec.get("tail", "short"))
    tortoise_tail(S, items, style or "short", size)
    for style, size in each(spec.get("jaw")):
        tortoise_jaw(S, items, style, size, where)
    for style, size in each(spec.get("marks")):
        tortoise_marks(S, items, style, size, where)
    for style, size in each(spec.get("carry")):
        TORTOISE_CARRY[style](S, items, size, where)
    ob = pieces("tortoise_" + form_id, items)
    c, r = where["head"], where["r"]
    P = where["P"]
    nk = where["neck"]
    table = {
        "socket_head": [tuple(where["crown"]), Matrix.Scale(0.5 * S.head, 3)], "socket_eyes": [tuple(P(0, -r * 0.9, r * 0.3)), Matrix.Scale(0.6 * S.head, 3)],
        "socket_mouth": [tuple(where["mouth"]), Matrix.Scale(0.6 * S.head, 3)], "socket_grip": [tuple(P(0, -r * 1.0, -r * 0.45)), kit.ACROSS_MOUTH],
        "socket_throat": [tuple(nk + Vector((0, 0.02, -where["neck_r"] - 0.01)))], "socket_light": [tuple(nk + Vector((0, 0.05, -where["neck_r"] - 0.03)))],
        "socket_back": [tuple(S.on(0, S.cy - S.L * 0.5, -0.01))], "socket_body": [(0, S.cy - S.L * 0.98, S.rim + 0.02)],
        "socket_tail": [(0, S.cy + S.L * 0.96, S.rim + 0.035)], "socket_arm_l": [(S.W * 0.96, S.cy - 0.11, S.rim + 0.11)], "socket_arm_r": [(-S.W * 0.96, S.cy - 0.11, S.rim + 0.11)],
        "socket_collar": [tuple(nk), Matrix.Rotation(-0.3, 3, "X") @ Matrix.Diagonal((where["neck_r"] * 1.1 / 0.1, 1.0, where["neck_r"] * 1.1 / 0.1))],
    }
    for tag in ("fl", "fr", "bl", "br"):
        table["socket_limb_" + tag] = [tuple(feet[tag] + Vector((0, -0.03, 0.03)))]
    table["socket_hand_l"] = [tuple(feet["fl"] + Vector((0, -0.05, 0.03))), kit.HAND_ON_PAW_L]
    table["socket_hand_r"] = [tuple(feet["fr"] + Vector((0, -0.05, 0.03))), kit.HAND_ON_PAW_R]
    GL.export_objects([ob], kit._sockets(table), os.path.join(GL.OUT, form_id + ".glb"), ref=S.top)


# ======================================================================================
# The Hawk
# ======================================================================================

HAWK_STAGE = {
    # a fledgling is head, feet and down; a Final is a great raptor with a wingspan
    1: {"size": 0.9, "body": 0.78, "chest": 1.16, "head": 1.5, "neck": 0.8, "span": 0.4, "chord": 0.62, "tail": 0.42, "legs": 0.95, "feet": 1.4, "beak": 0.82, "eyes": 1.7, "shoulders": 1.0},
    2: {"size": 1.0, "body": 0.95, "chest": 0.94, "head": 1.18, "neck": 1.0, "span": 0.74, "chord": 1.0, "tail": 0.9, "legs": 1.0, "feet": 1.1, "beak": 0.95, "eyes": 1.2, "shoulders": 1.0},
    3: {"size": 1.1, "body": 1.0, "chest": 1.0, "head": 1.08, "neck": 1.0, "span": 0.78, "chord": 1.12, "tail": 1.0, "legs": 1.0, "feet": 1.0, "beak": 1.0, "eyes": 1.05, "shoulders": 1.0},
    4: {"size": 1.22, "body": 1.05, "chest": 1.1, "head": 1.06, "neck": 1.0, "span": 0.8, "chord": 1.15, "tail": 1.1, "legs": 1.0, "feet": 1.15, "beak": 1.14, "eyes": 1.05, "shoulders": 1.08},
}
HAWK_TIMES = ("size", "body", "chest", "head", "neck", "span", "chord", "tail", "legs", "feet", "beak", "eyes", "shoulders")
# how it holds itself: the body's angle above level, and the way the head looks (degrees)
POSES = {"soar": (14, -4), "hover": (44, -14), "dive": (-30, -34), "stoop": (-64, -66), "perch": (64, 0), "mantle": (56, -8), "lean": (40, -10), "fledge": (52, 4)}
# the spine from the root of the tail to the root of the bill: how far along, half-width,
# half-height, and how much of the neck's bend has happened by there
STATIONS = [(0.0, 0.034, 0.028, 0.0), (0.08, 0.07, 0.06, 0.0), (0.2, 0.105, 0.095, 0.0), (0.32, 0.112, 0.105, 0.0), (0.41, 0.09, 0.085, 0.12),
            (0.47, 0.062, 0.06, 0.5), (0.51, 0.064, 0.06, 0.9), (0.555, 0.067, 0.062, 1.0), (0.595, 0.052, 0.048, 1.0), (0.622, 0.028, 0.028, 1.0)]
RUMP, BELLY, CHEST, SHOULDER, NECK, NAPE, HEAD, FACE, BILL = 1, 2, 3, 4, 5, 6, 7, 8, 9


class Bird:
    """A hawk's numbers and its spine, level (the body along -Y), and the way from there
    to where it stands in the pose it holds."""

    def __init__(self, level, spec):
        b = dict(HAWK_STAGE[min(4, max(1, level))])
        for k, v in spec.get("build", {}).items():
            b[k] = b.get(k, 1.0) * v if k in HAWK_TIMES else v
        self.b, self.level = b, level
        self.pose = GL.opt(spec.get("pose", "soar"))[0] or "soar"
        pitch, look = POSES[self.pose]
        self.pitch, self.look = math.radians(b.get("pitch", pitch)), math.radians(b.get("look", look))
        bend = self.look - self.pitch
        self.C, self.r = [Vector((0, 0, 0))], []
        prev_s, prev_a = 0.0, 0.0
        for i, (s, rx, rz, share) in enumerate(STATIONS):
            klen = b["body"] if i <= SHOULDER else (b["neck"] if i <= NAPE else b["head"])
            if i == 0:
                kr = b["chest"] ** 0.5
            elif i <= SHOULDER:
                kr = b["chest"]
            elif i == NECK:
                kr = (b["chest"] * b["head"]) ** 0.5
            else:
                kr = b["head"]
            kx = b["shoulders"] if i in (CHEST, SHOULDER) else 1.0
            self.r.append((rx * kr * kx, rz * kr))
            a = bend * share
            if i > 0:
                am = (a + prev_a) / 2
                self.C.append(self.C[-1] + Vector((0, -math.cos(am), math.sin(am))) * (s - prev_s) * klen)
            prev_s, prev_a = s, a
        n = len(self.C)
        self.T = [(self.C[min(i + 1, n - 1)] - self.C[max(i - 1, 0)]).normalized() for i in range(n)]
        self.U = [t.cross(X).normalized() for t in self.T]
        self.size = b["size"]
        # from level to the pose: turned about X, brought to size, and set so the crown of
        # the head (or the root of the tail, for one that is falling head first) is at STAND
        R = Matrix.Rotation(-self.pitch, 4, "X")
        crown = self.C[HEAD] + self.U[HEAD] * self.r[HEAD][1]
        anchor = crown if self.pose != "stoop" else self.C[0] + Vector((0, 0.06, 0))
        a = (R @ anchor) * self.size
        chest = (R @ self.C[CHEST]) * self.size
        self.M = Matrix.Translation(Vector((0, -0.05 - chest.y, STAND - a.z))) @ Matrix.Scale(self.size, 4) @ R

    def L(self, i, x=0.0, y=0.0, z=0.0):
        """A point by station i: x to its left, y back along the spine, z up (level space)."""
        return self.C[i] + X * x - self.T[i] * y + self.U[i] * z

    def at(self, i, geo):
        """A geometry made about the origin (facing -Y, Z up) set at station i (level space)."""
        Mi = Matrix((X, -self.T[i], self.U[i])).transposed()
        return [self.C[i] + Mi @ V(p) for p in geo[0]], list(geo[1])

    def skin(self, i, a, k=1.0):
        """A point on the body's surface at station i, at angle a round it (0 its left, 90 degrees its back)."""
        rx, rz = self.r[i]
        return self.C[i] + (X * math.cos(a) * rx + self.U[i] * math.sin(a) * rz) * k

    def out(self, i, a):
        return (X * math.cos(a) + self.U[i] * math.sin(a)).normalized()

    def W(self, p):
        """Level space to where it stands."""
        return self.M @ V(p)

    def Wd(self, d):
        """A direction, level space to where it stands."""
        return (self.M.to_3x3() @ V(d)).normalized()

    def world(self, geo):
        return [self.M @ V(p) for p in geo[0]], list(geo[1])


def bird_body(B):
    """The body, the neck and the head as one skin: dark above, pale below, the hood a marking."""
    n = 8
    rings = [[B.C[i] + X * math.cos(2 * math.pi * k / n + math.pi / n) * B.r[i][0] + B.U[i] * math.sin(2 * math.pi * k / n + math.pi / n) * B.r[i][1] for k in range(n)] for i in range(len(B.C))]
    dark, pale = mat("feather_dark"), mat("feather_pale")
    body = g.to_object("hawk_body", g.loft(rings), dark, smooth=True)
    sides = (len(B.C) - 1) * n
    kit.paint(body, lambda c, nm, i: i < sides and i // n <= NECK and i % n in (4, 5, 6), pale)
    kit.paint(body, lambda c, nm, i: i < sides and i // n >= NECK and i % n not in (4, 5, 6), mark("hood", dark))
    return body


def bird_feathers(B, items, sleek, down):
    dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")
    k = B.b["chest"]
    if not sleek:
        # the breast: rows of barred feathers lying back along it
        for si, n, Ln in ((CHEST, 5, 0.085), (BELLY, 6, 0.09), (RUMP, 4, 0.08)):
            geo = None
            for i in range(n):
                a = math.radians(-150 + 120 * i / (n - 1))
                base = B.skin(si, a, 0.96) + B.T[si] * 0.045
                d = B.out(si, a)
                geo = g.merge(geo, g.blade(base, base - B.T[si] * Ln * k + d * 0.012, 0.06 * k, normal=d, belly=0.5))
            items.append((geo, mid))
    # the mantle: rows of dark feathers down the back
    for si, n, Ln in ((SHOULDER, 4, 0.1), (CHEST, 5, 0.11), (BELLY, 4, 0.1)):
        geo = None
        for i in range(n):
            a = math.radians(40 + 100 * i / (n - 1))
            base = B.skin(si, a, 0.95) + B.T[si] * 0.03
            d = B.out(si, a)
            geo = g.merge(geo, g.blade(base, base - B.T[si] * Ln * k + d * 0.014, 0.07 * k, normal=d, belly=0.5))
        items.append((geo, dark if si != CHEST or sleek else mid))
    if down:
        # down still showing through: pale tufts standing off it everywhere
        geo = None
        for j, si in enumerate((RUMP, BELLY, CHEST, SHOULDER, NECK)):
            for i in range(7):
                a = 2 * math.pi * (i + 0.5 * (j % 2)) / 7
                base = B.skin(si, a, 0.9)
                d = B.out(si, a)
                geo = g.merge(geo, g.blade(base, base + d * 0.05 * down - B.T[si] * 0.03, 0.05, normal=-B.T[si], belly=0.45, thick=0.02))
        items.append((geo, mat("feather_down")))


def bird_head(B, items, style, size, eyes, eye_size):
    """The face: the brow, the eyes, the bill. In the head's own frame: x left, y back, z up."""
    dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")
    h = B.b["head"]
    bk = B.b["beak"] * h
    put = lambda geo: B.at(HEAD, geo)  # noqa: E731
    brow, eye = None, None
    er = 0.017 * h * B.b["eyes"] * (eye_size if eyes in ("far", "dark", "owl") else 1.0)
    for s in (1, -1):
        brow = g.merge(brow, g.blade((s * 0.012 * h, -0.07 * h, 0.018 * h), (s * 0.078 * h, 0.035 * h, 0.022 * h), 0.05 * h, normal=(s * 0.5, -0.2, 1), belly=0.45))
        eye = g.merge(eye, g.ico((s * 0.05 * h, -0.027 * h, 0.003 * h), er, sub=1, scale=(0.6, 1.0, 0.9)))
    if eyes == "dark":
        # too dark and too large for a hawk's: night itself, with one point of light in each
        items.append((put(eye), mat("eye_night"), True))
        glint = None
        for s in (1, -1):
            glint = g.merge(glint, g.ico((s * (0.05 * h + er * 0.5), -0.027 * h - er * 0.45, 0.003 * h + er * 0.3), er * 0.28, sub=0))
        items.append((put(glint), field("eyes", 3.4)))
    elif eyes == "owl":
        # a face made to gather the dark: a pale disc round each eye, the eyes forward and fixed
        disc, pupil, ring_ = None, None, None
        for s in (1, -1):
            c = Vector((s * 0.036 * h, -0.058 * h, 0.004 * h))
            disc = g.merge(disc, g.ico(c, 0.05 * h * eye_size, sub=1, scale=(1.0, 0.35, 1.0), rot=(0, 0, -s * 0.45)))
            ring_ = g.merge(ring_, g.ico(c + Vector((s * 0.004, -0.014 * h, 0)), 0.027 * h * eye_size, sub=1, scale=(1.0, 0.4, 1.0), rot=(0, 0, -s * 0.45)))
            pupil = g.merge(pupil, g.ico(c + Vector((s * 0.006, -0.022 * h, 0)), 0.014 * h * eye_size, sub=1, scale=(1.0, 0.4, 1.0), rot=(0, 0, -s * 0.45)))
        items += [(put(disc), pale, True), (put(ring_), field("eyes", 3.2)), (put(pupil), mat("eye_night"), True)]
    else:
        items.append((put(eye), field("eyes", 3.0 if eyes != "far" else 4.2)))
    if eyes == "far":
        # the eyes of one who sees a long way: larger, brighter, under a heavier brow
        vis = None
        for s in (1, -1):
            vis = g.merge(vis, g.blade((s * 0.008 * h, -0.085 * h, 0.022 * h), (s * 0.092 * h, 0.04 * h, 0.03 * h), 0.062 * h, normal=(s * 0.5, -0.2, 1), belly=0.45, thick=0.02))
        items.append((put(vis), mat("horn"), False))
    elif eyes == "old":
        # old eyes: long pale brows, and pale about the bill
        ob = None
        for s in (1, -1):
            ob = g.merge(ob, g.blade((s * 0.01 * h, -0.075 * h, 0.02 * h), (s * 0.1 * h * eye_size, 0.07 * h, 0.03 * h), 0.05 * h, normal=(s * 0.5, -0.2, 1), belly=0.4))
        items.append((put(ob), mat("feather_down")))
    elif eyes != "owl":
        items.append((put(brow), dark))
    # the bill: its root and the cere, the upper mandible hooked over the lower
    o = Vector((0, -0.083 * h, -0.016 * h))
    gape = 0.5 if style == "call" else 0.0
    root = g.merge(g.box((0, -0.077 * h, -0.01 * h), (0.03 * h, 0.03 * h, 0.02 * h)), g.blade((0, -0.065 * h, -0.026 * h), (0, -0.105 * h, -0.034 * h), 0.026 * h, normal=(0, 0, -1)))
    upper = g.tongue([o + Vector((0, 0.012, 0.008)) * bk, o + Vector((0, -0.03, 0.006)) * bk, o + Vector((0, -0.058, -0.012)) * bk], [0.04 * bk, 0.034 * bk, 0.02 * bk], thick=0.8, normal=(0, 0, 1))
    hook = g.tongue([o + Vector((0, -0.054, -0.01)) * bk, o + Vector((0, -0.07, -0.028)) * bk, o + Vector((0, -0.064, -0.05)) * bk], [0.02 * bk, 0.014 * bk, 0.002], thick=0.8, normal=(0, -1, 0.3))
    lower = g.tongue([o + Vector((0, 0.01, -0.012)) * bk, o + Vector((0, -0.03, -0.018 - 0.03 * gape)) * bk, o + Vector((0, -0.05, -0.022 - 0.06 * gape)) * bk], [0.03 * bk, 0.024 * bk, 0.004], thick=0.5, normal=(0, 0, -1))
    items += [(put(g.merge(root, upper, lower)), mat("beak"), False), (put(hook), mat("talon"), False)]
    if style == "call":
        # it calls, and they look up: the throat's hackles stand out
        hk = None
        for i in range(7):
            a = math.radians(-160 + 140 * i / 6)
            base = B.skin(NECK, a, 0.95)
            d = B.out(NECK, a)
            hk = g.merge(hk, g.blade(base, base + d * 0.075 * size - B.T[NECK] * 0.05, 0.05, normal=-B.T[NECK], belly=0.4))
        items.append((hk, pale))
        items.append((put(g.ico(o + Vector((0, -0.02, -0.014)) * bk, 0.012 * bk, sub=0)), mat("hide_tongue"), True))
    elif style == "crest":
        # a crest at the nape
        cr, tp = None, None
        for i, (dx, Ln) in enumerate(((0.0, 0.13), (-0.022, 0.1), (0.022, 0.1))):
            b0 = Vector((dx * h, 0.02 * h, 0.05 * h))
            t0 = b0 + Vector((dx * 1.5, 0.75, 0.55)) * Ln * size * h
            cr = g.merge(cr, g.blade(b0, t0, 0.04 * h, normal=(dx * 6, -0.5, 1), belly=0.4))
            tp = g.merge(tp, g.blade(b0.lerp(t0, 0.75), b0.lerp(t0, 1.04), 0.03 * h, normal=(dx * 6, -0.5, 1), belly=0.4, thick=0.012))
        items += [(put(cr), mid), (put(tp), pale)]
    elif style == "crown":
        # a crest like a crown: a ring of feathers standing round the top of its head
        cr, tp = None, None
        n = 9
        for i in range(n):
            a = math.pi * (0.08 + 0.84 * i / (n - 1))
            d = Vector((math.cos(a), 0.25, math.sin(a) * 0.5 + 0.8)).normalized()
            b0 = Vector((math.cos(a) * 0.045 * h, 0.012 * h, 0.035 * h + math.sin(a) * 0.014 * h))
            Ln = (0.085 + 0.045 * math.sin(a)) * size * h
            cr = g.merge(cr, g.blade(b0, b0 + d * Ln, 0.034 * h, normal=(0, -1, 0.2), belly=0.45))
            tp = g.merge(tp, g.blade(b0 + d * Ln * 0.72, b0 + d * Ln * 1.05, 0.026 * h, normal=(0, -1, 0.2), belly=0.4, thick=0.012))
        items += [(put(cr), mat("metal_brass"), False), (put(tp), field("crown", 2.6))]
    elif style == "owl":
        # ear-tufts, and a ruff round the face
        tf = None
        for s in (1, -1):
            b0 = Vector((s * 0.04 * h, -0.01 * h, 0.05 * h))
            tf = g.merge(tf, g.blade(b0, b0 + Vector((s * 0.035, 0.03, 0.085)) * size * h, 0.035 * h, normal=(0, -1, 0.2), belly=0.4))
        items.append((put(tf), dark))
    elif style == "white":
        # a white head on a dark bird: old before its time
        cap = g.ico((0, 0.022 * h, 0.012 * h), 0.068 * h, sub=1, scale=(0.94, 1.0, 0.95))
        items.append((put(cap), mat("feather_down")))
        nape = None
        for i in range(7):
            a = math.radians(-20 + 220 * i / 6)
            base = B.skin(NAPE, a, 1.0)
            d = B.out(NAPE, a)
            nape = g.merge(nape, g.blade(base, base - B.T[NAPE] * 0.06 * size + d * 0.012, 0.05 * h, normal=d, belly=0.5))
        items.append((nape, mat("feather_down")))
    elif style == "plume":
        # a falconer's hood, open at the face, with its plume
        cap = g.ico((0, 0.026 * h, 0.012 * h), 0.069 * h, sub=1, scale=(1.0, 1.0, 0.92))
        items.append((put(cap), mat("leather_jess"), True))
        pl, pt = None, None
        for i, dx in enumerate((-0.012, 0.0, 0.012)):
            b0 = Vector((dx * h, 0.02 * h, 0.07 * h))
            t0 = b0 + Vector((dx * 2, 0.045 + 0.02 * (i % 2), 0.1)) * size * h
            pl = g.merge(pl, g.blade(b0, t0, 0.028 * h, normal=(0, -1, 0.3), belly=0.5))
        items.append((put(pl), mat("cloth_stripe")))
        items.append((put(g.ico((0, 0.02 * h, 0.072 * h), 0.012 * h, sub=0)), mat("metal_brass"), False))


def bird_tail(B, items, style, size):
    mid, dark, pale = mat("feather_mid"), mat("feather_dark"), mat("feather_pale")
    kt = B.b["tail"] * size
    root = B.C[0] + B.U[0] * 0.002
    back = -B.T[0]
    down = math.radians({"spread": -34.0, "square": -4.0}.get(style, 0.0))
    back = (back * math.cos(down) + B.U[0] * math.sin(down)).normalized()
    up = back.cross(X).normalized() * -1.0
    spread = {"fan": 33, "long": 16, "fork": 30, "square": 26, "wedge": 30, "streamers": 26, "short": 36, "spread": 62}.get(style, 33)
    n = 9 if style == "spread" else 7
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(-spread + 2 * spread * t)
        e = abs(t - 0.5) * 2            # 0 in the middle, 1 at the edge
        Ln = 0.27 * kt
        if style == "long":
            Ln *= 1.5
        elif style == "fork":
            Ln *= 0.62 + 1.25 * e ** 1.3
        elif style == "wedge":
            Ln *= 1.25 - 0.4 * e
        elif style == "short":
            Ln *= 0.9
        elif style == "square":
            Ln *= 1.0 + 0.12 * e
        d = (back * math.cos(a) + X * math.sin(a)).normalized()
        base = root + X * math.sin(a) * 0.02 - up * 0.002 * abs(i - n // 2)
        tip = base + d * Ln - up * (0.03 + 0.008 * abs(i - n // 2))
        w = 0.062 * (1.0 if style != "fork" else 0.9) * (B.b["chest"] ** 0.5)
        items.append((g.blade(base, tip, w, normal=up, belly=0.72), mid if i % 2 == 0 else dark))
        items.append((g.blade(base.lerp(tip, 0.8), base.lerp(tip, 1.02), w * 0.8, normal=up, belly=0.4, thick=0.008), mark("band", pale)))
    if style == "streamers":
        # two long feathers trailing from the middle of it
        for s in (1, -1):
            b0 = root + X * s * 0.012
            pts = [b0, b0 + back * 0.3 * kt + X * s * 0.02, b0 + back * 0.62 * kt + X * s * 0.05 - up * 0.02, b0 + back * 0.9 * kt + X * s * 0.07 - up * 0.05]
            items.append((g.tongue(pts, [0.02, 0.018, 0.03, 0.004], thick=0.25, normal=up), pale))


def bird_folded(B, items, tight, size, tips):
    """The wings folded along its sides: coverts, secondaries, and the long primaries crossed
    over the tail. tight is how close they are held (a stooping bird's are a blade)."""
    dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")
    ch = B.b["chord"] * size
    for s in (1, -1):
        a = math.radians(90 - s * (62 - 10 * tight))        # high on the flank
        sh = B.skin(SHOULDER, a, 1.02)
        out = B.out(CHEST, a)
        back = -B.T[CHEST]
        lay = lambda b0, Ln, w, drop, m, th=None, sweep=0.0: items.append((g.blade(b0, b0 + back * Ln + out * (0.012 - sweep) - B.U[CHEST] * drop, w, normal=out, belly=0.45, thick=th), m))  # noqa: E731
        for i in range(4):          # the coverts
            lay(sh + back * (0.01 + 0.035 * i) - B.U[CHEST] * 0.012 * i, 0.12 * ch, 0.09, 0.015, dark)
        for i in range(3):          # the secondaries
            lay(sh + back * (0.05 + 0.05 * i) - B.U[CHEST] * (0.03 + 0.014 * i), 0.2 * ch, 0.1, 0.03, mid)
        bar = sh + back * 0.13 - B.U[CHEST] * 0.03
        lay(bar, 0.07, 0.11, 0.012, pale)
        for i in range(3):          # the primaries, long, their tips crossing behind
            b0 = sh + back * (0.16 + 0.03 * i) - B.U[CHEST] * (0.05 + 0.012 * i)
            Ln = (0.3 + 0.05 * i) * ch
            lay(b0, Ln, 0.06, 0.035 + 0.01 * i, dark, None, 0.03 * (1 + i) * (0.4 + 0.6 * tight))
            if tips > i:
                tipb = b0 + back * Ln * 0.82 + out * (0.012 - 0.03 * (1 + i) * (0.4 + 0.6 * tight)) * 0.82 - B.U[CHEST] * (0.035 + 0.01 * i) * 0.82
                items.append((g.blade(tipb, tipb + back * Ln * 0.2 - out * 0.005, 0.045, normal=out, belly=0.4, thick=0.01), field("tips", 2.4)))


def bird_tucked_legs(B, items, style, size):
    """On the wing: feathered thighs, the shanks tucked back, the feet closed (level space).
    Returns the feet, for what hangs from them."""
    pale, leg = mat("feather_pale"), mat("beak")
    kf = B.b["feet"] * size
    feet = {}
    for s in (1, -1):
        hip = B.skin(BELLY, math.radians(-90 + s * 28), 0.8) + B.T[BELLY] * 0.02
        knee = hip - B.T[BELLY] * 0.07 - B.U[BELLY] * 0.05
        ankle = knee - B.T[BELLY] * 0.035 - B.U[BELLY] * 0.02
        foot = ankle - B.T[BELLY] * 0.06 * B.b["legs"] - B.U[BELLY] * 0.013
        items.append((g.tube([hip, knee, ankle], [0.045 * B.b["chest"], 0.034, 0.014], n=6), pale))
        items.append((g.tube([ankle, foot], [0.011 * kf, 0.009 * kf], n=5), leg, False))
        toes = None
        for dx, dy in ((-0.016, 0.03), (0.0, 0.036), (0.016, 0.03), (0.0, -0.02)):
            toes = g.merge(toes, g.tube([foot, foot + X * dx * kf - B.T[BELLY] * dy * kf - B.U[BELLY] * 0.014 * kf], [0.008 * kf, 0.005 * kf], n=4))
        items.append((toes, leg if style != "glow" else field("talons", 2.8), False))
        feet["l" if s > 0 else "r"] = foot
    return feet


def bird_legs(B, items, style, size, stance=1.0):
    """Legs that are down: standing on a perch, set wide, thrust out to strike, or hanging.
    Built where it stands (world space). Returns the feet."""
    pale, leg, talon = mat("feather_pale"), mat("beak"), mat("talon")
    sz = B.size
    kf = B.b["feet"] * size * sz
    feet = {}
    fwd, up = Vector((0, -1, 0)), Vector((0, 0, 1))
    for s in (1, -1):
        hip = B.W(B.skin(BELLY, math.radians(-90 + s * 30), 0.75) + B.T[BELLY] * 0.03)
        Ln = 0.15 * B.b["legs"] * sz
        if style in ("down", "set", "grip"):
            wide = (1.9 if style == "set" else 1.25) * stance
            knee = hip + Vector((s * 0.012 * wide, -0.02, -0.07 * sz))
            foot = Vector((hip.x * wide, hip.y - 0.015, knee.z - Ln * 0.62))
            toe_dir, spread_, curl = fwd, (1.45 if style == "set" else 1.0), -0.2
        elif style == "strike":
            knee = hip + Vector((s * 0.02, -0.07, -0.06)) * sz
            foot = knee + Vector((s * 0.035, -0.6, -0.5)).normalized() * Ln * 1.05
            toe_dir, spread_, curl = Vector((0, -0.75, -0.66)).normalized(), 1.9, 0.5
        else:           # dangle
            knee = hip + Vector((s * 0.008, 0.01, -0.075)) * sz
            foot = knee + Vector((s * 0.01, 0.02, -1.0)).normalized() * Ln * 0.9
            toe_dir, spread_, curl = Vector((0, -0.4, -0.9)).normalized(), 1.3, 0.3
        items.append((g.tube([hip, knee, knee.lerp(foot, 0.3)], [0.046 * B.b["chest"] * sz, 0.036 * sz, 0.016 * sz], n=6), pale))
        items.append((g.tube([knee.lerp(foot, 0.25), foot], [0.012 * kf, 0.011 * kf], n=5), leg, False))
        side = toe_dir.cross(up)
        side = side.normalized() if side.length > 1e-4 else X
        nrm = side.cross(toe_dir).normalized()
        toes, claws = None, None
        for dx, dy in ((-0.5, 0.86), (0.0, 1.0), (0.5, 0.86), (0.0, -0.75)):
            d = (toe_dir * dy + side * dx * spread_ * 0.75).normalized()
            Lt = (0.05 if dy > 0 else 0.036) * kf
            mid = foot + d * Lt - nrm * 0.006 * kf
            toes = g.merge(toes, g.tube([foot, mid], [0.01 * kf, 0.008 * kf], n=4))
            tip = mid + d * 0.022 * kf * (1 + curl) - nrm * 0.03 * kf * (1 + curl)
            claws = g.merge(claws, g.tongue([mid, mid + d * 0.018 * kf - nrm * 0.008 * kf, tip], [0.012 * kf, 0.009 * kf, 0.001], thick=0.7, normal=nrm))
        items.append((toes, leg if style != "glow" else field("talons", 2.8), False))
        items.append((claws, talon, False))
        feet["l" if s > 0 else "r"] = foot
    return feet


WINGS = {
    # span, how far forward the wrist is carried, how far back the tip is swept, the chord,
    # the primaries: how many, the angles they fan through (from the span, degrees), their length and width
    "broad": {"span": 1.0, "fwd": 1.0, "sweep": 0.0, "chord": 1.15, "n": 7, "a": (84, 6), "len": 0.3, "w": 0.047},
    "long": {"span": 1.32, "fwd": 0.8, "sweep": 0.0, "chord": 0.9, "n": 7, "a": (80, 10), "len": 0.3, "w": 0.05},
    "pointed": {"span": 1.05, "fwd": 1.5, "sweep": 0.09, "chord": 0.8, "n": 6, "a": (64, 26), "len": 0.4, "w": 0.052},
    "round": {"span": 0.86, "fwd": 0.7, "sweep": 0.0, "chord": 1.28, "n": 8, "a": (90, -6), "len": 0.24, "w": 0.07},
    "kite": {"span": 1.2, "fwd": 2.1, "sweep": 0.12, "chord": 0.84, "n": 6, "a": (72, 14), "len": 0.36, "w": 0.05},
    "soft": {"span": 1.25, "fwd": 0.7, "sweep": 0.0, "chord": 1.15, "n": 8, "a": (88, 0), "len": 0.3, "w": 0.064},
    "swept": {"span": 0.8, "fwd": 2.0, "sweep": 0.3, "chord": 0.72, "n": 6, "a": (88, 60), "len": 0.44, "w": 0.05},
    "stub": {"span": 0.95, "fwd": 0.8, "sweep": 0.0, "chord": 1.0, "n": 4, "a": (78, 18), "len": 0.2, "w": 0.06},
}


def bird_wing(B, style, size, sg, tips, metal=False, wing_pitch=1.0, dihedral=0.38, sweep=0.0):
    """One wing, spread, as a thing of its own that the game beats (wing_l, wing_r): a bone
    with three ranks of feathers. Built where it stands, its pivot at the shoulder."""
    W_ = WINGS[style]
    sz = B.size
    sp = W_["span"] * B.b["span"] * size * sz
    ch = W_["chord"] * B.b["chord"] * (size ** 0.5) * sz
    root = B.W(B.skin(SHOULDER, math.radians(90 - sg * 55), 0.92) + B.T[SHOULDER] * 0.01)
    Mw = (Matrix.Rotation(-B.pitch * wing_pitch, 3, "X") @ Matrix.Rotation(-sg * dihedral, 3, "Y") @ Matrix.Rotation(sg * sweep, 3, "Z"))
    return wing(root, Mw, style, sp, ch, sz, sg, tips, metal)


def wing(root, Mw, style, sp, ch, sz, sg, tips, metal=False):
    """A wing at a shoulder: root is the shoulder, Mw how it is held, sp its span and ch its
    chord (already at size), sz the size of the bird it is on."""
    W_ = WINGS[style]
    soft = style == "soft"
    if metal:
        dark, mid, pale = mat("metal_iron"), mat("metal_iron_light"), mat("metal_iron_light")
    else:
        dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")

    def P(x, y, z):
        return root + Mw @ Vector((x, y, z))
    sh = Vector((0, 0, 0))
    el = Vector((sg * 0.2 * sp, -0.05 * W_["fwd"] * sz, 0.03 * sz))
    wr = Vector((sg * 0.42 * sp, -0.085 * W_["fwd"] * sz, 0.03 * sz))
    tip = Vector((sg * 0.6 * sp, (-0.02 + W_["sweep"]) * sz, 0.01 * sz))
    up = Mw @ Vector((0, 0, 1))
    arm = lambda t: (sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1))  # noqa: E731
    items = [(g.tube([P(*sh), P(*el), P(*wr), P(*tip)], [0.024 * sz, 0.02 * sz, 0.015 * sz, 0.006 * sz], n=5), dark, not metal)]
    # the wing itself, under its feathers: one surface from the shoulder out along the hand
    mids, wds = [], []
    for t in (0.0, 0.3, 0.62, 1.0):
        Ln = (0.2 + 0.07 * math.sin(t * math.pi)) * ch
        mids.append(P(*(arm(t) + Vector((sg * 0.015 * t * sz, Ln * 0.5, -0.012 * sz)))))
        wds.append(Ln * 1.02)
    am = math.radians((W_["a"][0] + W_["a"][1]) / 2)
    dm = Vector((sg * math.cos(am), math.sin(am), -0.04))
    hand = wr.lerp(tip, 0.5)
    for f_, w_ in ((0.42, 0.8), (0.82, 0.34)):
        mids.append(P(*(hand + dm * W_["len"] * ch * f_)))
        wds.append(W_["len"] * ch * w_)
    items.append((g.tongue(mids, wds, thick=0.06, normal=up), dark, not metal))
    sec, cov, prim, lit, bar, fringe = None, None, None, None, None, None
    for i in range(8):
        t = i / 7.0
        b0 = arm(t) + Vector((0, 0.01, -0.004)) * sz
        Ln = (0.2 + 0.07 * math.sin(t * math.pi)) * ch
        sec = g.merge(sec, g.blade(P(*b0), P(*(b0 + Vector((sg * 0.03 * t * sz, Ln, -0.02 * sz)))), 0.095 * sp ** 0.5 * (1.1 if soft else 1.0), normal=up, belly=0.6, thick=0.008))
        b1 = arm(t) + Vector((sg * 0.012 * t, 0.115 * ch / sz, -0.006)) * sz
        bar = g.merge(bar, g.blade(P(*b1), P(*(b1 + Vector((0, 0.045 * ch, -0.004 * sz)))), 0.06 * sp ** 0.5, normal=up, belly=0.5, thick=0.01))
        if soft:
            e = b0 + Vector((sg * 0.03 * t * sz, Ln, -0.02 * sz))
            fringe = g.merge(fringe, g.blade(P(*e), P(*(e + Vector((sg * 0.01, 0.05 * ch, -0.012 * sz)))), 0.045, normal=up, belly=0.3, thick=0.004))
    for i in range(9):
        t = i / 8.0
        b0 = arm(t) + Vector((0, -0.005, 0.008)) * sz
        cov = g.merge(cov, g.blade(P(*b0), P(*(b0 + Vector((sg * 0.02 * t * sz, (0.1 + 0.02 * (i % 2)) * ch, 0.0)))), 0.08 * sp ** 0.5, normal=up, belly=0.5, thick=0.012))
    n = W_["n"]
    for i in range(n):
        a = math.radians(W_["a"][0] + (W_["a"][1] - W_["a"][0]) * i / (n - 1))
        d = Vector((sg * math.cos(a), math.sin(a), -0.04))
        Ln = W_["len"] * (1.0 + 0.17 * math.sin((i + 1) / (n + 1.0) * math.pi)) * ch
        b0 = wr.lerp(tip, i / (n + 2.0)) + Vector((0, 0.005, -0.004)) * sz
        prim = g.merge(prim, g.blade(P(*b0), P(*(b0 + d * Ln)), W_["w"] * 1.25 * sp ** 0.5, normal=up, belly=0.55, thick=0.007))
        tp = g.blade(P(*(b0 + d * Ln * 0.8)), P(*(b0 + d * Ln * 1.03)), W_["w"] * 0.96 * sp ** 0.5, normal=up, belly=0.4, thick=0.009)
        if i >= n - tips:
            lit = g.merge(lit, tp)
        if soft:
            e = b0 + d * Ln
            fringe = g.merge(fringe, g.blade(P(*e), P(*(e + d * 0.06 * ch + Vector((0, 0.02, -0.01)) * sz)), 0.04, normal=up, belly=0.3, thick=0.004))
    items += [(sec, mid, not metal), (prim, dark, not metal), (cov, dark, not metal), (bar, pale, not metal)]
    if lit:
        items.append((lit, field("tips", 2.5)))
    if fringe:
        items.append((fringe, mat("shade_edge")))
    ob = pieces("wing_" + ("l" if sg > 0 else "r"), items)
    kit.set_origin(ob, root)
    return ob


def bird_cloak(B, items, size, sides=(1, -1)):
    """Wings hanging half open like a cloak, even at rest: the arm out and down, the long
    feathers falling from it past its feet (where it stands)."""
    dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")
    sz = B.size
    k = size * B.b["span"] ** 0.5 * sz
    for s in sides:
        sh = B.W(B.skin(SHOULDER, math.radians(90 - s * 50), 0.95))
        el = sh + Vector((s * 0.17, -0.03, -0.035)) * k
        wr = sh + Vector((s * 0.27, -0.07, -0.2)) * k
        items.append((g.tube([sh, el, wr], [0.03 * sz, 0.024 * sz, 0.014 * sz], n=5), dark))
        fall, edge, cov = None, None, None
        for i in range(9):
            t = i / 8.0
            b0 = (sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)) + Vector((0, 0.0, -0.01))
            Ln = (0.2 + 0.26 * t) * k * B.b["chord"]
            nrm = Vector((s * 0.75, -0.6, 0.25))
            tip = b0 + Vector((s * 0.05 * t, 0.045 + 0.05 * (1 - t), -1.0)).normalized() * Ln
            if i % 2:
                edge = g.merge(edge, g.blade(b0, tip, 0.085 * k, normal=nrm, belly=0.5, thick=0.01))
            else:
                fall = g.merge(fall, g.blade(b0, tip, 0.085 * k, normal=nrm, belly=0.5, thick=0.01))
            cov = g.merge(cov, g.blade(b0 + Vector((0, -0.004, 0.012)), b0 + Vector((s * 0.02 * t, 0.02, -1.0)).normalized() * Ln * 0.4 + Vector((s * 0.008, -0.012, 0)), 0.07 * k, normal=nrm, belly=0.5, thick=0.014))
        items += [(fall, dark), (edge, mid), (cov, dark)]
        bar = None
        for i in range(8):
            t = (i + 0.5) / 8.0
            b0 = (sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)) + Vector((s * 0.01, -0.016, -0.085 * k))
            bar = g.merge(bar, g.blade(b0, b0 + Vector((0, 0, -0.045 * k)), 0.06 * k, normal=Vector((s * 0.75, -0.6, 0.25)), belly=0.5, thick=0.012))
        items.append((bar, pale))


def bird_shield(B, items, size, iron, sg=-1):
    """A wing put between: the arm carried forward, the leading feathers thick and overlapped
    like plates, several of them missing (or, grown back, of metal)."""
    sz = B.size
    k = size * sz
    dark, edge = (mat("metal_iron"), mat("metal_iron_light")) if iron else (mat("feather_dark"), mat("feather_mid"))
    sh = B.W(B.skin(SHOULDER, math.radians(90 - sg * 50), 0.95))
    el = sh + Vector((sg * 0.14, -0.1, 0.02)) * k
    wr = sh + Vector((sg * 0.2, -0.26, -0.06)) * k
    items.append((g.tube([sh, el, wr], [0.03 * sz, 0.026 * sz, 0.016 * sz], n=5), dark, not iron))
    geo, geo2 = None, None
    gone = () if iron else (2, 5)
    for i in range(8):
        if i in gone:
            continue
        t = i / 7.0
        b0 = (sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)) + Vector((0, 0, -0.004))
        Ln = (0.26 + 0.14 * math.sin(t * math.pi) + 0.06 * t) * k * B.b["chord"]
        nrm = Vector((sg * 0.55, -0.82, 0.12))
        tip = b0 + Vector((sg * 0.03, -0.03 * t, -1.0)).normalized() * Ln
        bl = g.blade(b0, tip, 0.1 * k, normal=nrm, belly=0.62, thick=0.03 * k)
        if i % 2:
            geo2 = g.merge(geo2, bl)
        else:
            geo = g.merge(geo, bl)
    items += [(geo, dark, False), (geo2, edge, False)]
    if iron:
        # and it rings: a rim of the field along the leading edge
        items.append((g.tube([sh + Vector((0, -0.012, 0.012)), el + Vector((0, -0.016, 0.014)), wr + Vector((0, -0.016, 0.01))], 0.007 * sz, n=4), field("ring", 2.2)))


def bird_broken(B, items, size, sg=-1):
    """One wing that never set straight, scorched at the tip."""
    sz = B.size
    k = size * B.b["span"] * sz
    dark, mid = mat("feather_dark"), mat("feather_mid")
    sh = B.W(B.skin(SHOULDER, math.radians(90 - sg * 55), 0.92))
    el = sh + Vector((sg * 0.19, -0.02, 0.05)) * k
    wr = sh + Vector((sg * 0.3, 0.06, -0.07)) * k
    tip = sh + Vector((sg * 0.33, 0.2, -0.2)) * k
    items.append((g.tube([sh, el, wr, tip], [0.024 * sz, 0.02 * sz, 0.015 * sz, 0.006 * sz], n=5), dark))
    sec, prim, burnt = None, None, None
    up = Vector((sg * 0.25, 0, 1)).normalized()
    for i in range(7):
        t = i / 6.0
        b0 = sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)
        Ln = (0.2 + 0.05 * math.sin(t * math.pi)) * k * B.b["chord"]
        sec = g.merge(sec, g.blade(b0, b0 + Vector((sg * 0.03 * t, 1.0, -0.25 - 0.5 * t)).normalized() * Ln, 0.075 * k ** 0.5, normal=up, belly=0.6, thick=0.008))
    for i in range(5):
        b0 = wr.lerp(tip, i / 5.0)
        d = Vector((sg * (0.25 - 0.12 * i), 0.55 + 0.1 * i, -0.75 + 0.1 * (i % 2))).normalized()
        Ln = (0.26 - 0.02 * i) * k * B.b["chord"]
        prim = g.merge(prim, g.blade(b0, b0 + d * Ln * 0.72, 0.05, normal=up, belly=0.55, thick=0.007))
        burnt = g.merge(burnt, g.blade(b0 + d * Ln * 0.6, b0 + d * Ln, 0.046, normal=up, belly=0.4, thick=0.009))
    items += [(sec, mid), (prim, dark), (burnt, mat("coal"))]
    items.append((g.ico(wr.lerp(tip, 0.7) + Vector((0, 0.1, -0.12)) * k, 0.02 * sz, sub=0), field("ember", 2.4)))


# --- what it stands on, and what it carries ---------------------------------------------

def perch_stone(B, items, size, feet, where):
    """The highest thing in sight, and it has brought it with it."""
    f = (feet["l"] + feet["r"]) / 2
    r = 0.15 * size * B.size
    items.append((g.ico(f + Vector((0, 0.01, -r * 0.62)), r, sub=1, scale=(1.15, 1.0, 0.62), rot=(0.15, 0.1, 0.6)), mat("slate"), False))
    items.append((g.ico(f + Vector((0.05 * size, 0.04, -r * 1.25)), r * 0.62, sub=1, scale=(1.0, 0.9, 0.7), rot=(0.4, 0.2, 0.1)), mat("slate_light"), False))
    where["low"] = f.z - r * 1.7


def perch_iron(B, items, size, feet, where):
    """It sits the lamp-iron with the flame between its feet and is not singed."""
    f = (feet["l"] + feet["r"]) / 2
    iron = mat("metal_iron")
    w = abs(feet["l"].x - feet["r"].x) / 2 + 0.07 * size
    bar = f + Vector((0, 0.0, -0.012))
    items.append((g.tube([bar + Vector((-w, 0, 0)), bar + Vector((w, 0, 0))], 0.013, n=6), iron, False))
    for s in (1, -1):
        items.append((g.tube([bar + Vector((s * w, 0, 0)), bar + Vector((s * (w + 0.03), 0, 0.03)), bar + Vector((s * (w + 0.01), 0, 0.055))], [0.011, 0.009, 0.004], n=5), iron, False))
    # the bracket: down from the bar, scrolled, as it would stand out from a post
    post = bar + Vector((0, 0.05 * size, 0))
    foot = post + Vector((0, 0.03, -0.34 * size))
    items.append((g.tube([bar, post, post + Vector((0, 0.01, -0.12 * size)), foot], [0.012, 0.012, 0.011, 0.009], n=5), iron, False))
    scroll = g.spiral(foot + Vector((0, -0.045 * size, 0)), 0.045 * size, 0.012 * size, 1.4, 0.0, n=12, axis=X, start=0.0)
    items.append((g.tube(scroll, 0.007, n=4), iron, False))
    # the cup and the flame
    cup = bar + Vector((0, -0.005, 0.0))
    items.append((g.lathe([(0.014, -0.03), (0.04 * size, -0.012), (0.046 * size, 0.012)], n=7, centre=cup), mat("metal_brass"), False))
    fl = None
    for i, (dx, hgt) in enumerate(((0.0, 0.13), (0.02, 0.085), (-0.02, 0.095))):
        b0 = cup + Vector((dx * size, 0.0, 0.006))
        fl = g.merge(fl, g.tongue([b0, b0 + Vector((0.012, -0.004, hgt * 0.5)) * size, b0 + Vector((-0.006, 0.0, hgt)) * size], [0.04 * size, 0.03 * size, 0.003], thick=0.5, normal=Y if i % 2 == 0 else X))
    items.append((fl, field("flame", 3.2)))
    where["low"] = foot.z - 0.05 * size


def perch_tower(B, items, size, feet, where):
    """The tallest broken thing in the ruin: the top of a tower, and it owns the floor from there."""
    f = (feet["l"] + feet["r"]) / 2
    r = 0.2 * size * B.size
    top = f.z - 0.012
    low = max(0.03, top - 0.46 * size * B.size)
    c = Vector((f.x, f.y + 0.02, 0))
    items.append((g.lathe([(r * 0.86, low), (r * 0.9, top - 0.05), (r * 0.6, top - 0.04)], n=8, centre=c), mat("slate"), False))
    bricks, pale = None, None
    courses = max(2, int((top - low) / 0.085))
    for j in range(courses):
        z = low + (top - low) * (j + 0.5) / courses
        n = 8
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * (j % 2)) / n
            broken = j >= courses - 2 and (math.cos(a - 2.3) > 0.2 + 0.4 * (courses - 1 - j))
            if broken:
                continue
            bx = g.box(c + Vector((math.cos(a) * r, math.sin(a) * r, z)), (0.07 * size, 0.15 * size * B.size, (top - low) / courses * 0.92), rot=(0, 0, a))
            if (i + j) % 3 == 0:
                pale = g.merge(pale, bx)
            else:
                bricks = g.merge(bricks, bx)
    items += [(bricks, mat("slate_light"), False), (pale, mat("plaster_mortar"), False)]
    # a merlon left standing under its feet, and the rubble
    items.append((g.box(Vector((f.x, f.y, top - 0.03)), (abs(feet["l"].x - feet["r"].x) + 0.1, 0.12, 0.06)), mat("slate_light"), False))
    for i, (dx, dy, rr) in enumerate(((0.75, 0.5, 0.05), (-0.85, 0.3, 0.04), (0.5, -0.9, 0.035))):
        items.append((g.ico(c + Vector((dx * r, dy * r, top - 0.07 - 0.03 * i)), rr * size, sub=0, scale=(1, 0.9, 0.7), rot=(0.3 * i, 0.5, i)), mat("plaster_mortar"), False))
    where["low"] = low


def perch_glove(B, items, size, feet, where):
    """It grips your fist hard enough to mark the glove."""
    f = (feet["l"] + feet["r"]) / 2
    k = size * B.size
    lea, dk = mat("leather"), mat("leather_dark")
    fist = f + Vector((0, 0.0, -0.05 * k))
    items.append((g.ico(fist, 0.075 * k, sub=1, scale=(1.25, 1.0, 0.8)), lea, True))
    items.append((g.ico(fist + Vector((0.09 * k, -0.035 * k, -0.012 * k)), 0.035 * k, sub=1, scale=(1.0, 1.2, 0.9)), lea, True))       # the thumb
    wrist = fist + Vector((-0.02 * k, 0.08 * k, -0.07 * k))
    cuff = wrist + Vector((-0.03 * k, 0.14 * k, -0.2 * k))
    d = (cuff - wrist).normalized()
    u_, v_ = g._frame(d)
    items.append((g.loft([g.ring(fist + d * 0.03 * k, 0.07 * k, 0.06 * k, n=8, u=u_, v=v_), g.ring(wrist, 0.062 * k, 0.055 * k, n=8, u=u_, v=v_), g.ring(cuff, 0.11 * k, 0.1 * k, n=8, u=u_, v=v_)], caps=True), dk, True))
    items.append((g.loft([g.ring(cuff - d * 0.012, 0.115 * k, 0.105 * k, n=8, u=u_, v=v_), g.ring(cuff + d * 0.012, 0.118 * k, 0.108 * k, n=8, u=u_, v=v_)], caps=True), mat("cloth_stripe"), True))
    # the tassel
    t0 = wrist + Vector((0.07 * k, 0.0, -0.01))
    items.append((g.tube([t0, t0 + Vector((0.02, 0, -0.06 * k))], 0.006, n=4), mat("cord")))
    items.append((g.cone(t0 + Vector((0.02, 0, -0.06 * k)), t0 + Vector((0.02, 0, -0.13 * k)), 0.022 * k, n=6), mat("cloth_stripe")))
    where["low"] = cuff.z - 0.1 * k


def perch_shoulder(B, items, size, feet, where):
    """It rides a stranger's shoulder: the shoulder it grips, the collar beside it, the fall of their cloak."""
    f = (feet["l"] + feet["r"]) / 2
    k = size * B.size
    c = f + Vector((0.02 * k, 0.01, -0.06 * k))
    cloth = mat("cloth_watch")
    items.append((g.ico(c, 0.13 * k, sub=1, scale=(1.5, 1.0, 0.55), rot=(0, 0.28, 0)), cloth, True))               # the shoulder, sloping
    # the collar and the turn of a hood, at the neck's side of it
    nk = c + Vector((0.2 * k, 0.0, 0.1 * k))
    items.append((g.tube([c + Vector((0.14 * k, 0, 0.02 * k)), nk, nk + Vector((0.03 * k, 0.0, 0.1 * k))], [0.085 * k, 0.07 * k, 0.062 * k], n=8), mat("cloth_dark"), True))
    items.append((band(nk + Vector((0.015 * k, 0, 0.05 * k)), 0.085 * k, 0.085 * k, 0.018 * k, n=12, u=X, v=Y, sides=4), mat("cloth_stripe"), True))
    # the pad it stands on, strapped
    items.append((g.ico(f + Vector((0, 0.0, -0.02 * k)), 0.075 * k, sub=1, scale=(1.3, 1.0, 0.35)), mat("leather"), True))
    cl = None
    for i in range(6):
        x = (-0.2 + 0.07 * i) * k
        b0 = c + Vector((x, 0.02, -0.04 * k - 0.03 * k * abs(i - 4) / 4))
        Ln = (0.24 + 0.06 * math.sin(i * 1.9)) * k
        cl = g.merge(cl, g.tongue([b0, b0 + Vector((x * 0.2, 0.03, -Ln * 0.5)), b0 + Vector((x * 0.32, 0.02, -Ln))], [0.09 * k, 0.1 * k, 0.05 * k], thick=0.22, normal=Y))
    items.append((cl, cloth))
    items.append((g.ico(c + Vector((0.12 * k, -0.1 * k, 0.03 * k)), 0.025 * k, sub=0), mat("metal_brass"), False))
    where["low"] = c.z - 0.34 * k


PERCHES = {"stone": perch_stone, "iron": perch_iron, "tower": perch_tower, "glove": perch_glove, "shoulder": perch_shoulder}


def bird_carry(B, items, style, size, feet, where):
    """What it has been given to carry (where it stands)."""
    sz = B.size
    k = size * sz
    f = (feet["l"] + feet["r"]) / 2
    if style == "lamp":
        # a point of lamplight rides under its breast
        at = B.W(B.skin(CHEST, math.radians(-90), 1.0))
        items.append((B.world(band(B.C[CHEST], B.r[CHEST][0] * 1.03, B.r[CHEST][1] * 1.03, 0.008, n=14, u=X, v=B.U[CHEST], sides=4)), mat("leather"), True))
        items.extend(lantern(at + Vector((0, 0, 0.01)), 0.07 * k, "lamp", 3.6))
    elif style == "case":
        # a small case at its leg, and the ribbon it is tied with
        c = feet["r"] + Vector((-0.012, 0.0, 0.012)) * sz
        d = B.Wd(-B.T[BELLY])
        items.append((g.tube([c - d * 0.03 * k, c + d * 0.07 * k], 0.02 * k, n=7), mat("leather_dark"), True))
        items.append((g.tube([c + d * 0.065 * k, c + d * 0.085 * k], 0.023 * k, n=7), mat("metal_brass"), False))
        items.append((g.tube([c - d * 0.04 * k, c - d * 0.028 * k], 0.023 * k, n=7), mat("metal_brass"), False))
        rb = c + d * 0.03 * k
        items.append((g.tongue([rb, rb + d * 0.1 * k + Vector((-0.02, 0, -0.03)), rb + d * 0.24 * k + Vector((-0.03, 0, -0.01)), rb + d * 0.36 * k + Vector((-0.035, 0, -0.05))], [0.03 * k, 0.034 * k, 0.03 * k, 0.012], thick=0.2, normal=Vector((1, 0, 0.3))), mat("cloth_stripe")))
    elif style == "plate":
        # a brass plate on its breast, with every house's seal stamped small upon it
        c = B.skin(CHEST, math.radians(-90), 1.0) + B.T[CHEST] * 0.05
        nrm = (-B.U[CHEST] * 0.7 + B.T[CHEST] * 0.7).normalized()
        u_ = X
        v_ = nrm.cross(u_).normalized()
        pl = [c + u_ * x * size + v_ * y * size + nrm * 0.012 for x, y in ((-0.075, 0.07), (0.075, 0.07), (0.085, 0.0), (0.05, -0.075), (0.0, -0.105), (-0.05, -0.075), (-0.085, 0.0))]
        back = [p - nrm * 0.014 for p in pl]
        items.append((B.world(g.loft([back, pl], caps=True)), mat("metal_brass"), False))
        seals = None
        for i, (x, y) in enumerate(((-0.04, 0.035), (0.0, 0.04), (0.04, 0.035), (-0.025, -0.01), (0.025, -0.01), (0.0, -0.055))):
            seals = g.merge(seals, g.ico(c + u_ * x * size + v_ * y * size + nrm * 0.016, 0.012 * size, sub=0, scale=(1, 1, 0.5)))
        items.append((B.world(seals), mat("cloth_stripe"), False))
        items.append((B.world(g.ico(c + nrm * 0.02 + v_ * 0.005, 0.014 * size, sub=0)), field("seal", 2.4)))
    elif style == "writ":
        # the writ itself, rolled and sealed, in its feet
        c = f + Vector((0, -0.005, -0.03 * k))
        items.append((g.tube([c + Vector((-0.13 * k, 0, 0)), c + Vector((0.13 * k, 0, 0))], 0.028 * k, n=8), mat("paper"), True))
        for s in (1, -1):
            items.append((g.tube([c + Vector((s * 0.13 * k, 0, 0)), c + Vector((s * 0.15 * k, 0, 0))], 0.034 * k, n=8), mat("wood"), False))
        items.append((g.tongue([c + Vector((0.02, 0, -0.02 * k)), c + Vector((0.03, 0.01, -0.08 * k)), c + Vector((0.02, 0.0, -0.15 * k))], [0.035 * k, 0.035 * k, 0.02 * k], thick=0.2, normal=Y), mat("cloth_stripe")))
        items.append((g.ico(c + Vector((0.022, -0.006, -0.16 * k)), 0.028 * k, sub=1, scale=(1, 0.45, 1)), field("seal", 2.6)))
    elif style == "bright":
        # something small and bright, held
        c = f + Vector((0, -0.01, -0.035 * k))
        items.append((g.lathe([(0.045 * k, -0.008), (0.05 * k, 0.0), (0.045 * k, 0.008), (0.02 * k, 0.012)], n=8, centre=c), mat("metal_brass"), False))
        teeth = None
        for i in range(8):
            a = 2 * math.pi * i / 8
            teeth = g.merge(teeth, g.box(c + Vector((math.cos(a) * 0.055 * k, math.sin(a) * 0.055 * k, 0)), (0.018 * k, 0.014 * k, 0.014), rot=(0, 0, a)))
        items.append((teeth, mat("metal_brass"), False))
        items.append((g.ico(c + Vector((0, 0, 0.004)), 0.024 * k, sub=1), field("find", 3.6)))
    elif style == "jesses":
        # fine chain jesses on both legs, unfastened, carried tucked up
        a, b = feet["l"], feet["r"]
        low = (a + b) / 2 + Vector((0, 0.03, -0.11 * k))
        geo, _ = chain([a, a.lerp(low, 0.6) + Vector((0.03, 0, -0.03)), low, b.lerp(low, 0.6) + Vector((-0.03, 0, -0.03)), b], 0.011 * k)
        items.append((geo, mat("metal_iron_light"), True))
        for s, p in ((1, a), (-1, b)):
            items.append((band(p + Vector((0, 0, 0.012)), 0.016 * k, 0.016 * k, 0.005 * k, n=8, u=X, v=Y, sides=4), mat("leather_jess"), True))
            t0 = p + Vector((s * 0.02, 0.02, -0.02))
            items.append((g.tube([p, t0, t0 + Vector((s * 0.01, 0.03, -0.07 * k))], 0.004 * k, n=4), mat("leather_jess")))
            items.append((g.ico(t0 + Vector((s * 0.01, 0.03, -0.085 * k)), 0.017 * k, sub=1), mat("metal_brass"), False))
    elif style == "rings":
        # a ring for each of the party
        for s, p in ((1, feet["l"]), (-1, feet["r"])):
            for j in range(2):
                items.append((band(p + Vector((0, 0.012 * j, 0.012 + 0.012 * j)), 0.016 * k, 0.016 * k, 0.005 * k, n=8, u=X, v=Y, sides=4), mat("metal_brass"), False))


def bird_aura(B, items, style, size, feet, where):
    sz = B.size
    k = size * sz
    if style == "smoke":
        # smoke-grey, with the smell of rain on it: the weather it rides, trailing
        for i, (si, sx) in enumerate(((CHEST, 0.9), (CHEST, -0.9), (BELLY, 0.6), (BELLY, -0.6), (RUMP, 0.0))):
            b0 = B.W(B.skin(si, math.radians(90 - sx * 50), 1.0))
            back = B.Wd(-B.T[si])
            kk = k * (0.8 + 0.3 * math.sin(i * 1.7))
            pts = [b0, b0 + back * 0.14 * kk + Vector((sx * 0.03, 0, 0.05)), b0 + back * 0.34 * kk + Vector((-sx * 0.02, 0, 0.11)), b0 + back * 0.52 * kk + Vector((sx * 0.02, 0, 0.19))]
            items.append((g.tongue(pts, [0.07 * kk, 0.06 * kk, 0.04 * kk, 0.006], thick=0.35, normal=Z), mat("shade_smoke")))
    elif style == "hush":
        # its shadow arrives without a sound: the edges of it go to nothing
        for i, sx in enumerate((1, -1, 0.5, -0.5)):
            b0 = B.W(B.C[0] + X * sx * 0.03)
            back = B.Wd(-B.T[0])
            pts = [b0 + back * 0.2 * k, b0 + back * 0.36 * k + Vector((sx * 0.05, 0, -0.03)), b0 + back * 0.55 * k + Vector((sx * 0.09, 0, -0.02))]
            items.append((g.tongue(pts, [0.06 * k, 0.045 * k, 0.004], thick=0.25, normal=Z), mat("shade_edge")))
    elif style == "ring":
        # a pale ring opens in the air behind it when it falls
        back = B.Wd(-B.T[0])
        u_, v_ = g._frame(back)
        c = B.W(B.C[0]) + back * 0.2 * k
        items.append((band(c, 0.2 * k, 0.2 * k, 0.012 * k, n=22, u=u_, v=v_, sides=4), field("ring", 2.6)))
        items.append((band(c + back * 0.16 * k, 0.12 * k, 0.12 * k, 0.008 * k, n=16, u=u_, v=v_, sides=4), field("ring", 2.0)))
    elif style == "cold":
        # a cold light under the breast feathers
        c = B.skin(CHEST, math.radians(-90), 0.97) - B.T[CHEST] * 0.01
        items.append((B.world(g.ico(c, 0.04 * size, sub=1, scale=(1.3, 1.6, 0.5))), field("core", 3.2)))
    elif style == "underwing":
        # a cold light under one wing, and frost where it has been
        c = B.W(B.skin(SHOULDER, math.radians(-25), 1.0))
        items.append((g.ico(c + Vector((-0.03, 0.02, -0.01)) * k, 0.05 * k, sub=1, scale=(1.6, 1.3, 0.5)), field("core", 3.4)))
        fr = None
        t0 = B.W(B.C[0])
        back = B.Wd(-B.T[0])
        for i in range(6):
            b0 = t0 + back * (0.16 + 0.03 * i) * k + Vector((0.05 * math.sin(i * 2.0), 0, 0))
            fr = g.merge(fr, g.cone(b0, b0 + Vector((0.02 * math.sin(i), 0.02, -0.07 * k)), 0.012 * k, n=4))
        items.append((fr, mat("ice_pale"), False))
    elif style == "flock":
        # others rise with it: small birds of the field at its tail
        back = B.Wd(-B.T[0])
        t0 = B.W(B.C[0])
        n = max(2, int(round(3 * size)))
        geo = None
        for i in range(n):
            row = 1 + i // 2
            s = 1 if i % 2 == 0 else -1
            c = t0 + back * (0.2 + 0.2 * row) * sz + Vector((s * (0.15 + 0.15 * row) * sz, 0, 0.05 + 0.05 * row))
            geo = g.merge(geo, g.ico(c, 0.04 * sz, sub=0, scale=(0.8, 1.7, 0.7)))
            for w in (1, -1):
                geo = g.merge(geo, g.blade(c, c + Vector((w * 0.17 * sz, 0.04 * sz, 0.07 * sz)), 0.085 * sz, normal=Z, belly=0.5, thick=0.01))
        items.append((geo, field("flock", 2.2)))
    elif style == "dust":
        # mortar dust in its feathers
        geo = None
        for i in range(9):
            a = math.radians(30 + 120 * (i % 5) / 4)
            si = (SHOULDER, CHEST, BELLY)[i % 3]
            geo = g.merge(geo, g.ico(B.skin(si, a, 1.06) - B.T[si] * 0.02 * (i % 4), 0.012 + 0.004 * (i % 3), sub=0))
        items.append((B.world(geo), mat("plaster_mortar"), False))


def hawk(form_id, level, spec, base):
    if spec.get("rig") == "ground":
        return harrier(form_id, level, spec, base)
    kit.reset()
    opt, each = GL.opt, GL.each
    B = Bird(level, spec)
    pose = B.pose
    items = []          # level space
    witems = []         # where it stands
    where = {}
    body = bird_body(B)
    bird_feathers(B, items, bool(spec.get("sleek")), num(spec.get("down"), 1.0))
    hstyle, hsize = opt(spec.get("head"))
    estyle, esize = opt(spec.get("eyes"))
    bird_head(B, items, hstyle, hsize or 1.0, estyle, esize or 1.0)
    tstyle, tsize = opt(spec.get("tail", "fan"))
    bird_tail(B, items, tstyle or "fan", tsize or 1.0)
    wstyle, wsize = opt(spec.get("wings", "broad"))
    tips = spec.get("tips")
    if tips is None:
        tips = {1: 0, 2: 0, 3: 3, 4: 9}[min(4, max(1, level))]
    wings = []
    fstyle, fsize = opt(spec.get("feet", "tucked" if pose in ("soar", "dive") else "down"))
    if fstyle in ("tucked",):
        feet_l = bird_tucked_legs(B, items, fstyle, fsize)
        feet = {s: B.W(p) for s, p in feet_l.items()}
    else:
        glow = fstyle == "glow"
        feet = bird_legs(B, witems, "dangle" if glow else fstyle, fsize, float(spec.get("stance", 1.0)))
        if glow:
            for s, p in feet.items():
                witems.append((g.ico(p + Vector((0, -0.01, -0.02)) * B.size, 0.03 * B.size * fsize, sub=1), field("talons", 3.0)))
    if wstyle in ("folded", "tucked"):
        bird_folded(B, items, 1.0 if wstyle == "tucked" else 0.0, wsize, min(3, tips))
    elif wstyle == "cloak":
        bird_cloak(B, witems, wsize)
    elif wstyle in ("shield", "ironshield"):
        bird_shield(B, witems, wsize, wstyle == "ironshield")
        _fold_side(B, items, 1, wsize, min(3, tips))
    elif wstyle == "shelter":
        bird_cloak(B, witems, wsize, sides=(-1,))
        _fold_side(B, items, 1, 1.0, min(3, tips))
    elif wstyle == "broken":
        bird_broken(B, witems, wsize)
        wings.append(bird_wing(B, "broad", wsize, 1, tips, wing_pitch=float(spec.get("wingpitch", 1.0)), dihedral=0.3))
    else:
        wp = float(spec.get("wingpitch", 0.35 if pose in ("hover", "fledge") else 1.0))
        # held in a V: the game beats them up from where they rest, and a bird at its partner's
        # shoulder is hovering more than it is gliding
        dih = float(spec.get("dihedral", 0.5 if pose in ("hover", "fledge") else 0.38))
        iron = spec.get("iron")
        for sg in (1, -1):
            wings.append(bird_wing(B, wstyle, wsize, sg, tips, metal=(iron == "r" and sg < 0) or iron == "both", wing_pitch=wp, dihedral=dih, sweep=float(spec.get("sweep", 0.0))))
    for style, size in each(spec.get("perch")):
        PERCHES[style](B, witems, size, feet, where)
    for style, size in each(spec.get("carry")):
        bird_carry(B, witems, style, size, feet, where)
    for style, size in each(spec.get("aura")):
        bird_aura(B, witems, style, size, feet, where)
    rest = pieces("hawk_dress", items)
    ob = g.join("hawk_" + form_id, [body, rest])
    ob.data.transform(B.M)
    ob.data.update()
    if witems:
        ob = g.join("hawk_" + form_id, [ob, pieces("hawk_world", witems)])
    # nothing it stands on or carries goes under the ground it is measured from: it is all
    # lifted, the crown with it, and the game stands it by where the crown has gone
    low = min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
    dz = max(0.0, 0.02 - low)
    lift = Vector((0, 0, dz))
    if dz > 0.0:
        ob.data.transform(Matrix.Translation(lift))
        ob.data.update()
        for w in wings:
            w.matrix_world = Matrix.Translation(lift) @ w.matrix_world
        feet = {k_: v_ + lift for k_, v_ in feet.items()}
    # the sockets, where it stands
    h = B.b["head"]
    f = (feet["l"] + feet["r"]) / 2
    Rn = (B.M.to_3x3().normalized() @ Matrix((X, -B.T[NECK], B.U[NECK])).transposed())
    nr = B.r[NECK]
    Wl = lambda p_: tuple(B.W(p_) + lift)  # noqa: E731
    table = {
        "socket_head": [Wl(B.L(HEAD, 0, 0, B.r[HEAD][1]))], "socket_eyes": [Wl(B.L(HEAD, 0, -0.057 * h, 0.006 * h))],
        "socket_mouth": [Wl(B.L(HEAD, 0, -0.083 * h, -0.016 * h))], "socket_grip": [tuple(f)], "socket_light": [tuple(f)],
        "socket_throat": [Wl(B.L(NECK, 0, 0, -nr[1]))], "socket_back": [Wl(B.L(SHOULDER, 0, 0, B.r[SHOULDER][1]))],
        "socket_body": [Wl(B.L(CHEST, 0, 0, -B.r[CHEST][1]))], "socket_tail": [Wl(B.C[0])],
        "socket_limb_fl": [tuple(feet["l"])], "socket_limb_fr": [tuple(feet["r"])], "socket_hand_l": [tuple(feet["l"])], "socket_hand_r": [tuple(feet["r"])],
        "socket_arm_l": [Wl(B.L(SHOULDER, B.r[SHOULDER][0], 0, 0.3 * B.r[SHOULDER][1]))], "socket_arm_r": [Wl(B.L(SHOULDER, -B.r[SHOULDER][0], 0, 0.3 * B.r[SHOULDER][1]))],
        "socket_collar": [Wl(B.C[NECK]), Rn @ Matrix.Diagonal((nr[0] * B.size * 1.12 / 0.1, 1.0, nr[1] * B.size * 1.12 / 0.1))],
    }
    GL.export_objects([ob] + wings, kit._sockets(table), os.path.join(GL.OUT, form_id + ".glb"), ref=STAND + dz)


def _fold_side(B, items, side, size, tips):
    """One wing folded (the other is doing something else)."""
    keep = []
    bird_folded(B, keep, 0.0, size, tips)
    # bird_folded lays the left wing's pieces first, then the right's
    half = len(keep) // 2
    items.extend(keep[:half] if side > 0 else keep[half:])


# --- the Hawk that came down to run: on the wolf's rig, as its base body is ----------------

def harrier(form_id, level, spec, base):
    """The Harrier and its Finals: a coursing bird-beast, lean and deep in the chest on long
    bare legs, a hooked bill, a crest from brow to shoulder, its wings half out for balance,
    a fan of feathers for a tail. It runs with the wolf's clips, as beast-ground-hunter does."""
    bk = GL.bk
    opt, each = GL.opt, GL.each
    _, r = kit._wolf()
    GL._weld(r)
    c = PALETTE
    r.recolor("Main", "feather_dark", c["feather_dark"][0], rough=0.9)
    r.recolor("Main_Light", "feather_pale", c["feather_pale"][0], rough=0.85)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.3, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "beak", c["beak"][0], rough=0.4)
    head = r.family("Head", "Ear1.L", "Ear1.R")
    r.leg_length(-0.45)
    r.leg_girth(0.74)
    top = r.top(r.bone("Torso2").y)
    r.scale(bk.TORSO, (0, 0, top), (0.82, 1.0, 0.86))
    r.scale_along(head, r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.25)
    r.scale(head, r.bone("Neck3"), (0.84, 1.0, 0.9))
    tufts = opt(spec.get("tufts"))
    for i, ear in enumerate(("Ear1.L", "Ear1.R")):
        r.scale(r.family(ear), r.bone(ear), 0.35 if not tufts[0] else (0.5, 1.0, 1.5 * tufts[1]))
    if tufts[0]:
        # one ear-tuft always turned to the undergrowth
        r.rotate(r.family("Ear1.R"), r.bone("Ear1.R"), Y, -1.1)
    GL.stage(r, level)
    GL.build(r, spec.get("build", {}))
    # the wolf's tail goes; a fan of feathers stands in its place
    r.lengthen_chain(r.family("Tail1"), [], 0.28)
    r.scale(r.family("Tail1"), r.bone("Tail1"), (0.55, 1.0, 0.55))
    r.settle()
    kit._wolf_marks(r, ("feather_dark", "feather_pale"), ("socks", "mask", "saddle", "tailtip"))
    A = GL.Anat(r)
    spots = GL._spots(r, A)
    add = lambda r_, name, geo, weights, material: GL._add(r_, name, geo, weights, material, smooth=material.name.startswith(SOFT))  # noqa: E731
    dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")
    # the bill: hooked over the muzzle, and the muzzle its colour
    n = A.nose
    GL._paint(r, lambda p, nm: p.y < n.y + 0.12, mat("beak"))
    kb = num(spec.get("bill", 1.0))
    upper = g.tongue([(0, n.y + 0.36, n.z + 0.13), (0, n.y + 0.04, n.z + 0.09), (0, n.y - 0.1 * kb, n.z - 0.03)], [0.26, 0.22, 0.09], thick=0.75, normal=(0, 0, 1))
    hook = g.tongue([(0, n.y - 0.07 * kb, n.z - 0.02), (0, n.y - 0.15 * kb, n.z - 0.13), (0, n.y - 0.1 * kb, n.z - 0.27 * kb)], [0.1, 0.07, 0.01], thick=0.8, normal=(0, -1, 0.3))
    add(r, "bill", upper, "Head", mat("beak"))
    add(r, "bill_hook", hook, "Head", mat("talon"))
    # the crest: feathers down the midline from the brow to the shoulders, the tallest on the crown
    ksz = num(spec.get("crest", 1.0))
    crest, ctip = None, None
    hb = A.head
    for y, Ln in ((hb.y - 0.12, 0.3), (hb.y + 0.1, 0.56), (A.n3.y, 0.52), (A.n2.y, 0.44), (A.n1.y, 0.36), (A.t3.y, 0.28)):
        z = r.top(y, half_width=0.12) - 0.05
        for dx in (-0.07, 0.0, 0.07):
            b0 = Vector((dx, y, z))
            t0 = b0 + Vector((dx * 1.5, Ln * 0.75, Ln * 0.72)) * ksz
            crest = g.merge(crest, g.blade(b0, t0, 0.16, normal=(dx * 4, -0.5, 1), belly=0.4))
            ctip = g.merge(ctip, g.blade(b0.lerp(t0, 0.76), b0.lerp(t0, 1.04), 0.1, normal=(dx * 4, -0.5, 1), belly=0.4, thick=0.02))
    add(r, "crest", crest, "Neck3", mid)
    add(r, "crest_tips", ctip, "Neck3", pale if level < 4 else field("tips", 2.2))
    # the wings, half out for balance
    kw = num(spec.get("wings", 1.0)) or 1.0
    for s, tag in ((1, "l"), (-1, "r")):
        root = Vector((s * (r.side(A.t3.y, A.withers - 0.3) + 0.02), A.t3.y + 0.05, A.withers - 0.28))
        el = root + Vector((s * 0.34, 0.2, 0.2)) * kw
        wr = root + Vector((s * 0.52, 0.78, 0.1)) * kw
        tip = root + Vector((s * 0.5, 1.25, -0.1)) * kw
        add(r, "wingbone_" + tag, g.tube([root, el, wr, tip], [0.09, 0.075, 0.055, 0.02], n=5), "Torso3", dark)
        sec, prim, bar = None, None, None
        nrm = Vector((s * 0.8, 0, 0.6))
        for i in range(7):
            t = i / 6.0
            b0 = root.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)
            Ln = (0.62 + 0.25 * math.sin(t * math.pi)) * kw
            sec = g.merge(sec, g.blade(b0, b0 + Vector((s * 0.05, 0.55, -0.82)).normalized() * Ln, 0.3 * kw, normal=nrm, belly=0.55, thick=0.03))
            bar = g.merge(bar, g.blade(b0 + Vector((0, 0.06, -0.3 * kw)), b0 + Vector((0, 0.1, -0.46 * kw)), 0.26 * kw, normal=nrm, belly=0.5, thick=0.04))
        for i in range(5):
            b0 = wr.lerp(tip, i / 5.0)
            d = Vector((s * (0.1 - 0.04 * i), 0.92, -0.38 + 0.06 * i)).normalized()
            prim = g.merge(prim, g.blade(b0, b0 + d * (0.95 + 0.1 * i) * kw, 0.2 * kw, normal=nrm, belly=0.55, thick=0.03))
        add(r, "wing_sec_" + tag, sec, "Torso3", mid)
        add(r, "wing_bar_" + tag, bar, "Torso3", pale)
        add(r, "wing_prim_" + tag, prim, "Torso3", dark)
    # the tail's fan
    tb = r.bone("Tail1")
    fan, band_ = None, None
    kt = num(spec.get("fan", 1.0)) or 1.0
    for i in range(7):
        a = math.radians(-36 + 12 * i)
        d = Vector((math.sin(a), math.cos(a), 0.12 - 0.02 * abs(i - 3)))
        bl = g.blade(tb, tb + d * 1.25 * kt, 0.3, normal=(0, 0, 1), belly=0.7)
        fan = g.merge(fan, bl)
        band_ = g.merge(band_, g.blade(tb + d * 1.0 * kt, tb + d * 1.28 * kt, 0.24, normal=(0, 0, 1), belly=0.4, thick=0.03))
    add(r, "tail_fan", fan, "Tail1", mid)
    add(r, "tail_band", band_, "Tail1", pale)
    # long bare legs, feathered to the hock, and hooked claws
    GL._legs_painted(r, A, 0.95, mat("beak"))
    for tag, foot, bone in GL.FEET:
        f = r.bone(foot)
        cl = None
        for dx in (-0.09, 0.0, 0.09):
            cl = g.merge(cl, g.tongue([(f.x + dx, f.y - 0.1, 0.12), (f.x + dx * 1.3, f.y - 0.3, 0.17), (f.x + dx * 1.4, f.y - 0.42, 0.02)], [0.05, 0.04, 0.004], thick=0.7, normal=(0, 0, 1)))
        add(r, "claws_" + tag, cl, bone, mat("talon"))
        up = r.bone({"fl": "FrontUpperLeg.L", "fr": "FrontUpperLeg.R", "bl": "BackUpperLeg.L", "br": "BackUpperLeg.R"}[tag])
        tr = None
        for k in range(5):
            a = 2 * math.pi * k / 5
            b0 = Vector((up.x + math.cos(a) * 0.1, up.y + 0.05 + math.sin(a) * 0.12, up.z - 0.1))
            tr = g.merge(tr, g.blade(b0, b0 + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, -0.42)), 0.2, normal=(math.cos(a), math.sin(a), 0.2), belly=0.45))
        add(r, "trousers_" + tag, tr, {"fl": "FrontUpperLeg.L", "fr": "FrontUpperLeg.R", "bl": "BackUpperLeg.L", "br": "BackUpperLeg.R"}[tag], pale)
    for style, size in each(spec.get("grown")):
        if style == "sickle":
            # it goes for the back of the leg: a great hooked claw carried clear of the ground on each hind foot
            for tag, foot, bone in GL.FEET[2:]:
                f = r.bone(foot)
                s = 1 if f.x > 0 else -1
                b0 = Vector((f.x - s * 0.1, f.y - 0.02, 0.2))
                geo = g.tongue([b0, b0 + Vector((-s * 0.06, -0.22, 0.34)) * size, b0 + Vector((-s * 0.08, -0.5, 0.22)) * size, b0 + Vector((-s * 0.08, -0.6, -0.08)) * size], [0.1, 0.085, 0.06, 0.006], thick=0.7, normal=(0, 0.4, 1))
                add(r, "sickle_" + tag, geo, bone, mat("talon"))
        elif style == "brambles":
            # burrs in its breast feathers, and the bramble it came through still on its back
            burr = None
            for i in range(9):
                a = i * 2.39996
                p = Vector((0.2 * math.cos(a) * (0.5 + 0.5 * (i % 3) / 2), A.chest_y + 0.02 + 0.05 * (i % 2), A.sh.z + 0.05 + 0.28 * math.sin(a)))
                burr = g.merge(burr, g.ico(p, 0.065 * size, sub=0))
            add(r, "burrs", burr, "Torso3", mat("bark_thorn"))
            for j, sx in enumerate((1, -1)):
                pts = [Vector((sx * 0.3, A.t3.y + 0.1, A.withers - 0.2)), Vector((sx * 0.12, A.t3.y + 0.5, A.withers + 0.22 * size)), Vector((-sx * 0.2, A.t2.y + 0.3, A.withers + 0.1)), Vector((-sx * 0.42, A.t1.y + 0.3, A.withers - 0.3))]
                geo = g.tube(pts, [0.035, 0.03, 0.025, 0.012], n=5)
                th, lf = None, None
                for k in range(8):
                    t = (k + 0.5) / 8.0
                    q = pts[0].lerp(pts[1], t * 3) if t < 1 / 3 else (pts[1].lerp(pts[2], t * 3 - 1) if t < 2 / 3 else pts[2].lerp(pts[3], t * 3 - 2))
                    d = Vector((math.cos(k * 2.4), math.sin(k * 1.7), 0.8)).normalized()
                    th = g.merge(th, g.cone(q, q + d * 0.14, 0.022, n=4))
                    if k % 3 == 0:
                        lf = g.merge(lf, g.blade(q, q + Vector((d.x, d.y, 0.3)).normalized() * 0.3, 0.16, normal=(0, 0, 1), belly=0.5))
                add(r, "bramble_%d" % j, g.merge(geo, th), GL._spine_w(r, g.merge(geo, th)), mat("bark_thorn"))
                add(r, "bramble_leaf_%d" % j, lf, GL._spine_w(r, lf), mat("leaf"))
        elif style == "low":
            pass
    k = STAND / A.skull
    r.uniform(k)
    sockets = {name: kit.bone_socket(r.arm, name, bone, Vector(at) * k, rot(k) if callable(rot) else rot) for name, (bone, at, rot) in spots.items()}
    sockets["ref_top"] = kit.free_socket("ref_top", (0, 0, STAND))
    GL.export(r, sockets, os.path.join(GL.OUT, form_id + ".glb"))


# ======================================================================================
# The gifts: what a hybrid wears of the Hawk, and of the Tortoise
# ======================================================================================

def part_wings():
    """The Hawk's gift: two broad wings, a span and a half of what the kit's were, fingered at
    the tips with the field. Hung on the back; the game beats them."""
    out = []
    for sg in (1, -1):
        root = Vector((sg * 0.055, 0.0, -0.02))
        Mw = Matrix.Rotation(-sg * 0.3, 3, "Y")
        out.append(wing(root, Mw, "broad", 1.28, 1.25, 1.0, sg, 5))
    return out


def part_talons():
    """The Hawk's gift, on every foot: three toes forward and one back, each a hooked claw as
    long as the toe."""
    toes, claws = None, None
    for dx, dy in ((0.034, -0.05), (0.0, -0.066), (-0.034, -0.05), (0.0, 0.05)):
        mid = Vector((dx, dy, -0.014))
        toes = g.merge(toes, g.tube([(0, 0, 0.01), mid], [0.018, 0.014], n=5))
        claws = g.merge(claws, g.tongue([mid, mid + Vector((dx * 0.7, dy * 0.7, -0.012)), mid + Vector((dx * 0.9, dy * 0.9, -0.075))], [0.022, 0.017, 0.002], thick=0.75))
    items = [(toes, mat("beak"), False), (claws, mat("talon"), False), (g.ico((0, 0, 0.018), 0.026, sub=1, scale=(1.1, 1.1, 0.8)), mat("feather_pale"), True)]
    return [pieces("talons", items)]


def part_shell():
    """The Tortoise's gift: its shell, worn on the back of whatever it has joined: the dome,
    its plates and their rings, the rim, a seam of the field where the dome sits on it."""
    S = Shell(3, {"build": {"width": 0.84, "length": 0.98, "dome": 0.8, "rim": 0.0}})
    items = []
    tortoise_shell(S, items, "dome", 1.25)
    tortoise_rim(S, items, "marginals", 1.0)
    ob = pieces("shell", items)
    # it sits behind the shoulders, its rim round the back
    ob.data.transform(Matrix.Translation(Vector((0, 0.16, -0.035))))
    return [ob]


def part_broad_chest():
    """The Tortoise's gift: the plate of its underside, worn as a breastplate: four plates on
    a keeled ground, a seam of the field down the middle."""
    hide, plate = mat("stone_hide"), mat("stone_plate")
    base = g.tongue([(0, 0.012, 0.15), (0, -0.03, 0.05), (0, -0.028, -0.07), (0, 0.012, -0.17)], [0.2, 0.3, 0.26, 0.08], thick=0.3, normal=(0, -1, 0))
    items = [(base, plate, False)]
    sc = None
    for sx, sz_, r in ((0.062, 0.062, 0.058), (-0.062, 0.062, 0.058), (0.055, -0.05, 0.052), (-0.055, -0.05, 0.052)):
        pl = g.lathe([(r, 0.0), (r * 0.9, 0.016), (r * 0.55, 0.024)], n=6, phase=math.pi / 6)
        pl = ([Vector((p_.x + sx, -0.036 - p_.z, p_.y + sz_)) for p_ in pl[0]], pl[1])
        sc = g.merge(sc, pl)
    items.append((sc, hide, False))
    items.append((g.tongue([(0, -0.05, 0.12), (0, -0.07, 0.0), (0, -0.055, -0.13)], [0.016, 0.022, 0.005], thick=0.6, normal=(0, -1, 0)), field("seam", 1.8)))
    return [pieces("broad_chest", items)]


PARTS = {"wings": part_wings, "talons": part_talons, "shell": part_shell, "broad-chest": part_broad_chest}


def build_parts(only=None):
    for feature, fn in PARTS.items():
        if only and feature not in only:
            continue
        kit.reset()
        objs = fn()
        path = os.path.join(kit.OUT, "parts", feature + ".glb")
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        log("wrote", os.path.relpath(path, kit.ROOT), "%d KB" % (os.path.getsize(path) // 1024))


# ======================================================================================
# Registration
# ======================================================================================

def register(builders):
    global GL
    for name in ("genius_lines", "__main__"):
        m = sys.modules.get(name)
        if m is not None and getattr(m, "BUILDERS", None) is builders:
            GL = m
    builders["tortoise"] = tortoise
    builders["hawk"] = hawk
    kit.PARTS.update(PARTS)        # the kit builds the gifts as these, too
    gifts = getattr(GL, "GIFTS", None)
    if gifts is not None:          # and so does `genius_lines.py gifts`
        gifts.update(PARTS)


if __name__ == "__main__":
    # python tools/blender/lines_beasts.py parts [wings talons shell broad-chest]: the gifts
    import genius_lines
    GL = genius_lines
    if sys.argv[1:2] == ["parts"]:
        build_parts(set(sys.argv[2:]) or None)
