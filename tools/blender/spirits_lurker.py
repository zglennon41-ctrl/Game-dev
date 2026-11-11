"""WILDLINE genius lines: the Lurker (docs/genius-evolutions.md, "The spirits").

A shadow that stands behind. The Starter is a blot with eyes; from there it is a hooded
figure of ink, and each path gives the figure a different way to stand: broad and behind
(the Back-stander's line), bent and sitting up (the One Who Sits Up), narrow with its collar
raised (the Unremarked). What a form is the picture of is built round the figure: the long
shadow it throws, the chair it sits in, the door it has become.

A Lurker's `body` (data/genius-bases/lurker.json):
    plan     what kind of thing it is: blot, figure (the default), seated, robed, door, gate,
             hatch, human, streak, corner, monolith, tree
    build    the figure's proportions: tall, broad, hood, skirt, lean, hem, turn, reach, thick,
             tatters, deep (each a multiple of 1; lean and turn are amounts)
    eyes     slit, dim, old, one, wide, holes, closed, none
    arms     hang, broad, spread, guard, long, apart, reach, lap, cup, hold, mantis, up, back,
             wings, whisper, blade, floor, none
    legs     stilts, back, roots
    ground   what lies or stands under and behind it: long, cohort, ring, wall
    wears    mantle, collar, script, cape, shawl, rime
    chest    maw, cold-hand, core
    face     mask
    shoulder face, face-crowned
    head     ear, prow
    holds    lamp, lamp-low, dark-lamp, glow, book, chain, blade
    back     chair
    aura     veils, breath, stubs
"""
import math

from mathutils import Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import field
import spirits_kit as sk
from spirits_kit import each, opt

PROF = [(0.87, 0.01, 0.01, 0.075), (0.82, 0.05, 0.06, 0.05), (0.75, 0.092, 0.105, 0.02), (0.67, 0.104, 0.118, 0.0), (0.6, 0.085, 0.09, 0.0),
        (0.555, 0.13, 0.098, 0.005), (0.5, 0.152, 0.1, 0.008), (0.41, 0.145, 0.092, 0.012), (0.3, 0.112, 0.075, 0.012), (0.2, 0.072, 0.052, 0.012)]

# where the elbow and the wrist are from the shoulder, for the left arm (x outward), and how thick
POSES = {
    "hang": ((0.07, -0.045, -0.12), (0.097, -0.1, -0.225), 1.0),
    "broad": ((0.13, -0.02, -0.1), (0.16, -0.07, -0.26), 1.35),
    "spread": ((0.15, -0.05, -0.04), (0.3, -0.12, 0.03), 1.1),
    "guard": ((0.08, -0.15, -0.1), (-0.02, -0.21, 0.07), 1.2),
    "long": ((0.1, -0.08, -0.2), (0.17, -0.2, -0.44), 0.85),
    "floor": ((0.13, -0.08, -0.2), (0.24, -0.22, -0.5), 0.95),
    "apart": ((0.09, -0.11, -0.08), (0.12, -0.24, -0.02), 0.9),
    "reach": ((0.05, -0.17, -0.03), (0.04, -0.36, 0.0), 0.9),
    "lap": ((0.08, -0.1, -0.15), (-0.09, -0.19, -0.2), 1.0),
    "cup": ((0.07, -0.14, -0.1), (-0.1, -0.27, -0.09), 1.0),
    "hold": ((0.07, -0.08, -0.13), (-0.09, -0.15, -0.09), 1.0),
    "mantis": ((0.05, -0.12, -0.15), (0.03, -0.22, 0.01), 0.75),
    "up": ((0.12, 0.0, 0.1), (0.22, -0.02, 0.34), 0.8),
    "back": ((0.06, 0.07, -0.12), (0.0, 0.11, -0.2), 0.9),
    "wings": ((0.15, 0.08, -0.05), (0.33, 0.2, -0.12), 1.2),
}


def _stage(level):
    """The age of the figure by its place on the line."""
    return {1: {}, 2: {"tall": 0.86, "hood": 1.12, "broad": 0.95}, 3: {"tall": 1.0, "hood": 1.0, "broad": 1.0}}.get(level, {"tall": 1.08, "hood": 0.96, "broad": 1.06})


class Fig:
    """A hooded figure: where its parts are, and how it leans."""

    def __init__(self, B, bd):
        self.B = B
        self.tall, self.broad, self.hood = bd.get("tall", 1.0), bd.get("broad", 1.0), bd.get("hood", 1.0)
        self.skirt, self.lean, self.hem = bd.get("skirt", 1.0), bd.get("lean", 0.0), bd.get("hem", 0.2)
        self.turn, self.reach, self.thick = bd.get("turn", 0.0), bd.get("reach", 1.0), bd.get("thick", 1.0)
        self.tatters, self.deep, self.side = bd.get("tatters", 1.0), bd.get("deep", 1.0), bd.get("side", 0.0)
        self.neck = self.hem + 0.4 * self.tall
        self.top = self.neck + 0.27 * self.hood
        self.zsh = self.hem + 0.31 * self.tall
        self.hands = {}
        self.elbows = {}
        self.final = False        # its hands are given where they are (not on the upright figure)

    def hand(self, tag, default=None):
        """Where a hand is, in the finished body."""
        if tag not in self.hands:
            return V(default) if default is not None else None
        return self.hands[tag] if self.final else self.P(self.hands[tag])

    def P(self, p):
        """A point of the upright figure, where the lean puts it."""
        p = V(p)
        return Vector((p.x + self.side * (p.z - self.hem), p.y - self.lean * (p.z - self.hem), p.z))

    def put(self, geo, material, smooth=None):
        self.B.add(sk.sheared(geo, self.lean, self.hem, self.side) if geo else geo, material, smooth)

    def puts(self, items):
        for it in items:
            self.put(*it)

    def sh(self, s):
        return Vector((s * 0.165 * self.broad, 0.0, self.zsh))

    def hood_at(self, x, y, z):
        """A point given on the plain hood (its void is at z 0.672, its face at y -0.12), on this one."""
        p = Vector((x * self.hood, y * self.hood, self.neck + (z - 0.6) * self.hood))
        return sk.rotz(p, self.turn) if self.turn else p

    @property
    def chest(self):
        """The front of the chest, upright."""
        return Vector((0, -0.1 * self.deep * (1.0 + (self.broad - 1.0) * 0.5), self.hem + 0.26 * self.tall))


def _pleats(rings, n):
    """A lofted cloak as two geometries, its folds by turns."""
    verts, faces = g.loft(rings)
    side = (len(rings) - 1) * n
    out = [([], [], {}), ([], [], {})]
    for fi, f in enumerate(faces):
        vs, fs, remap = out[1 if (fi < side and (fi % n) % 2 == 0) else 0]
        idx = []
        for i in f:
            if i not in remap:
                remap[i] = len(vs)
                vs.append(verts[i])
            idx.append(remap[i])
        fs.append(tuple(idx))
    return (out[0][0], out[0][1]), (out[1][0], out[1][1])


def cloak(F, n=10, close=True):
    rings = []
    for z, rx, ry, yo in PROF:
        if z > 0.6:
            zz = F.neck + (z - 0.6) * F.hood
            rx, ry, yo = rx * F.hood, ry * F.hood, yo * F.hood
        else:
            zz = F.hem + (z - 0.2) * F.tall
            w = F.broad if z >= 0.38 else (F.skirt + (F.broad - F.skirt) * max(0.0, (z - 0.2) / 0.18))
            rx, ry = rx * w, ry * (1.0 + (w - 1.0) * 0.5) * F.deep
        ring = g.ring((0, yo, zz), rx, ry, n=n, u=X, v=Y, phase=math.pi / n)
        if z > 0.6 and F.turn:
            ring = [sk.rotz(p, F.turn) for p in ring]
        rings.append(ring)
    a, b = _pleats(rings[::-1], n)
    F.put(a, F.B.main)
    F.put(b, F.B.under)


def hood(F, eyes="slit", cowl=True, void=True):
    B = F.B
    H = F.hood_at
    if void:
        F.put(g.ico(H(0, -0.086, 0.672), 0.075 * F.hood, sub=1, scale=(0.92, 0.42, 1.18), rot=(0, 0, F.turn)), "void")
    if cowl:
        for s in (1, -1):
            F.put(g.tongue([H(0, -0.1, 0.785), H(s * 0.066, -0.118, 0.72), H(s * 0.078, -0.116, 0.64), H(s * 0.04, -0.1, 0.575)], [0.02 * F.hood, 0.034 * F.hood, 0.032 * F.hood, 0.012], thick=0.5, normal=(s * 0.3, -1, 0)), B.under)
    face_eyes(F, eyes)


def face_eyes(F, style, c=None, k=None):
    """The eyes in the hood, by their kind."""
    if not style or style == "none":
        return
    k = F.hood if k is None else k
    H = F.hood_at
    c = H(0, -0.121, 0.682) if c is None else V(c)
    if style == "slit":
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.ico(H(s * 0.03, -0.121, 0.682), 0.017 * k, sub=1, scale=(1.25, 0.4, 0.4), rot=(0, s * -0.3, F.turn)))
        F.put(geo, field("eyes", 3.5))
    elif style == "dim":
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.ico(H(s * 0.03, -0.121, 0.682), 0.012 * k, sub=1, scale=(1.1, 0.4, 0.6)))
        F.put(geo, field("eyes", 1.6))
    elif style == "old":          # old, patient, and they do not close
        eyes, lids = None, None
        for s in (1, -1):
            p = H(s * 0.034, -0.122, 0.68)
            eyes = g.merge(eyes, g.ico(p, 0.022 * k, sub=1, scale=(1.05, 0.4, 0.85)))
            lids = g.merge(lids, g.tongue([p + Vector((-0.028 * k, -0.006, 0.02 * k)), p + Vector((0, -0.012, 0.03 * k)), p + Vector((0.028 * k, -0.006, 0.014 * k))], [0.008, 0.02 * k, 0.008], thick=0.5, normal=(0, -1, 0.4)))
            lids = g.merge(lids, g.tongue([p + Vector((-0.026 * k, -0.006, -0.02 * k)), p + Vector((0, -0.01, -0.032 * k)), p + Vector((0.026 * k, -0.006, -0.02 * k))], [0.006, 0.014 * k, 0.006], thick=0.5, normal=(0, -1, -0.4)))
        F.put(eyes, field("eyes", 3.2))
        F.put(lids, "mask_pale")
    elif style == "one":          # a single pale eye, open
        p = H(0, -0.12, 0.682)
        F.put(g.ico(p, 0.05 * k, sub=1, scale=(1.25, 0.4, 0.85)), "mask_pale")
        F.put(g.ico(p + Vector((0, -0.014, 0)), 0.022 * k, sub=1, scale=(1.0, 0.5, 1.0)), field("eyes", 4.0))
    elif style == "wide":         # set forward and wide
        eyes, rims = None, None
        for s in (1, -1):
            p = H(s * 0.042, -0.128, 0.69)
            eyes = g.merge(eyes, g.ico(p, 0.032 * k, sub=1, scale=(1.0, 0.35, 1.0)))
            rims = g.merge(rims, sk.hoop(p + Vector((0, -0.004, 0)), 0.037 * k, 0.037 * k, 0.007, n=8, u=X, v=Z, sides=3))
        F.put(eyes, field("eyes", 4.0))
        F.put(rims, "mask_pale", False)
    elif style == "holes":        # the black of a stair going down
        holes, rims = None, None
        for s in (1, -1):
            p = H(s * 0.036, -0.124, 0.682)
            holes = g.merge(holes, g.ico(p, 0.026 * k, sub=1, scale=(1.0, 0.4, 1.1)))
            rims = g.merge(rims, sk.hoop(p + Vector((0, -0.002, 0)), 0.031 * k, 0.034 * k, 0.006, n=8, u=X, v=Z, sides=3))
        F.put(holes, "void")
        F.put(rims, "mask_pale", False)
    elif style == "closed":
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.box(H(s * 0.032, -0.123, 0.68), (0.036 * k, 0.006, 0.005)))
        F.put(geo, field("eyes", 1.8))


def tatters(F, n=10, r=0.072, top=None, L=1.0, flare=1.0):
    """The hem: tatters hanging, each its own length."""
    B = F.B
    z0 = (F.hem if top is None else top) + 0.01
    r = r * F.skirt
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        d = Vector((math.cos(a), math.sin(a) * 0.72 * F.deep, 0))
        Li = (0.14 + 0.05 * ((i * 7) % 4)) * L * F.tatters
        pts = [d * r + Z * z0, d * (r * 1.18 * flare) + Z * (z0 - Li * 0.5), d * (r * (0.83 + 0.28 * (i % 2)) * flare) + Z * (z0 - Li) + Vector((0.015 * math.sin(i), 0.02, 0))]
        F.put(g.tongue(pts, [0.05 * F.skirt, 0.04 * F.skirt, 0.003], thick=0.3, normal=d), B.main if i % 2 else B.under)


def arm(F, s, pose, hand=True, reach=None, width=None, finger=1.0, hook=0.0):
    """One arm in a pose; returns its wrist (upright)."""
    el_o, wr_o, w = POSES[pose]
    L = F.reach if reach is None else reach
    w = w * F.thick if width is None else width
    sh = F.sh(s)
    el = sh + Vector((s * el_o[0], el_o[1], el_o[2])) * L
    wr = sh + Vector((s * wr_o[0], wr_o[1], wr_o[2])) * L
    F.put(g.tongue([sh, el, wr], [0.1 * w, 0.1 * w, 0.075 * w], thick=0.5, normal=(s, 0, 0.3)), F.B.main)
    if hand:
        d = (wr - el).normalized()
        F.put(sk.fingers(wr, d, n=3, L=0.11 * finger, spread=0.02, r=0.016, hook=hook), F.B.under)
    tag = "l" if s > 0 else "r"
    F.hands[tag], F.elbows[tag] = wr, el
    return wr


def arms(F, style, size=1.0):
    if not style or style == "none":
        return
    if style == "whisper":        # the left raised beside the hood, the right hanging
        sh = F.sh(1)
        el, wr = sh + Vector((0.04, -0.09, 0.02)), sh + Vector((-0.05, -0.15, 0.13))
        F.put(g.tongue([sh, el, wr], [0.09, 0.085, 0.06], thick=0.5, normal=(1, 0, 0.3)), F.B.main)
        F.put(sk.fingers(wr, Vector((-0.3, -0.2, 1)), n=3, L=0.07, spread=0.016), F.B.under)
        F.hands["l"] = wr
        arm(F, -1, "hang")
    elif style == "blade":        # one forward, low; the other drawn back
        arm(F, 1, "reach")
        arm(F, -1, "back", hand=False)
    elif style == "floor":        # longer than it is tall: its hands are on the floor ahead of it
        for s in (1, -1):
            arm(F, s, "floor", reach=size * F.reach, finger=1.6, hook=0.2)
    else:
        for s in (1, -1):
            arm(F, s, style, hook=0.5 if style in ("mantis", "reach") else 0.0, finger=1.3 if style in ("long", "reach") else 1.0)


def wisps(F, k=1.0):
    geo = None
    for sgn, y in ((1, 0.03), (-1, 0.05), (1, 0.08)):
        b = Vector((sgn * 0.13 * F.broad, y, F.zsh + 0.03))
        geo = g.merge(geo, g.tongue([b, b + Vector((sgn * 0.03, 0.03, 0.07)) * k, b + Vector((sgn * 0.01, 0.06, 0.15)) * k], [0.03, 0.022, 0.002], thick=0.3))
    F.put(geo, F.B.under)


# --- plans: what kind of thing it is ---------------------------------------------------------

def plan_blot(B, spec):
    """The Starter: a shadow at your heel that is not yours, a little darker where the eyes would be."""
    F = Fig(B, {"hem": 0.2})
    B.add(g.ico((0, 0, 0.4), 0.15, sub=1, scale=(1.0, 0.92, 1.0)), B.under)
    B.add(g.ico((0, 0.02, 0.5), 0.1, sub=1, scale=(1.0, 0.95, 0.8)), B.under)
    B.add(g.tongue([(0, 0.04, 0.34), (0.05, 0.16, 0.25), (-0.03, 0.24, 0.16), (0.03, 0.27, 0.06)], [0.22, 0.14, 0.07, 0.005], thick=0.7), B.main)
    # a little darker where the eyes would be
    B.add(sk.eye_pair((0, -0.118, 0.42), 0.055, 0.042, scale=(1.0, 0.4, 1.2), slant=0.0), B.main)
    B.add(sk.eye_pair((0, -0.136, 0.425), 0.055, 0.013, scale=(1.0, 0.5, 1.0), slant=0.0), field("eyes", 2.2))
    drips = None
    for i, (x, L) in enumerate(((-0.09, 0.1), (0.0, 0.15), (0.09, 0.08))):
        drips = g.merge(drips, g.tongue([(x, -0.03, 0.3), (x * 1.1, -0.03, 0.3 - L * 0.5), (x * 1.2, -0.02, 0.3 - L)], [0.07, 0.05, 0.004], thick=0.5))
    B.add(drips, B.main)
    # the shadow it throws, the wrong way for the lamp
    B.add(g.tongue([(0, 0, 0.05), (-0.1, -0.05, 0.03), (-0.22, -0.08, 0.03)], [0.22, 0.2, 0.03], thick=0.16, normal=Z), B.main)
    F.top, F.zsh, F.neck = 0.55, 0.36, 0.42
    B.frame(0.55, front=-0.13, mid=0.36, half=0.15)
    return F


def plan_figure(B, spec):
    bd = dict(_stage(B.level))
    bd.update(spec.get("build", {}))
    F = Fig(B, bd)
    cloak(F)
    style, _ = opt(spec.get("eyes", "slit"))
    hood(F, style if not spec.get("face") else "none")
    legs, _ = opt(spec.get("legs"))
    if legs != "roots":
        tatters(F, L=0.6 if legs else 1.0)
    for st, size in each(spec.get("arms", "hang")):
        arms(F, st, size)
    if bd.get("wisps", 1.0):
        wisps(F)
    B.frame(F.top, front=-0.13, mid=F.zsh - 0.08, half=0.17 * F.broad)
    B.socket("socket_eyes", F.P(F.hood_at(0, -0.128, 0.682)))
    B.socket("socket_head", F.P(Vector((0, 0.04 * F.hood, F.top - 0.01))))
    B.socket("socket_back", F.P(Vector((0, 0.11, F.zsh))))
    for tag in ("l", "r"):
        if tag in F.hands:
            B.socket("socket_hand_" + tag, F.P(F.hands[tag]))
            B.socket("socket_arm_" + tag, F.P(F.hands[tag]))
    if "r" in F.hands:
        B.socket("socket_grip", F.P(F.hands["r"] + Vector((0, 0, -0.02))))
    return F


def _chair(B, F, back=0.92, w=0.13):
    """A chair of the same shadow: four legs, a seat, a ladder back."""
    m = B.under
    legs = None
    for x in (w, -w):
        for y in (0.1, -0.12):
            legs = g.merge(legs, g.box((x, y, 0.2), (0.03, 0.03, 0.26)))
    B.add(legs, m, False)
    B.add(g.box((0, -0.01, 0.34), (2 * w + 0.05, 0.28, 0.03)), m, False)
    ladder = None
    for x in (w, -w):
        ladder = g.merge(ladder, g.box((x, 0.115, (0.34 + back) / 2), (0.03, 0.03, back - 0.34), rot=(-0.06, 0, 0)))
    for i in range(3):
        z = 0.5 + i * (back - 0.56) / 2
        ladder = g.merge(ladder, g.box((0, 0.118 + 0.01 * i, z), (2 * w, 0.02, 0.05)))
    B.add(ladder, m, False)
    for x in (w, -w):
        B.add(g.ico((x, 0.14, back + 0.015), 0.024, sub=0), B.main)


def plan_seated(B, spec):
    """Someone sitting forward in a chair."""
    bd = {"tall": 0.62, "hem": 0.36, "lean": 0.5, "hood": 1.08, "broad": 0.95, "tatters": 0.0}
    bd.update(spec.get("build", {}))
    F = Fig(B, bd)
    cloak(F)
    style, _ = opt(spec.get("eyes", "slit"))
    hood(F, style)
    # the lap, the shins, the hem that hangs between them
    for s in (1, -1):
        hip, knee, foot = Vector((s * 0.07, 0.0, 0.39)), Vector((s * 0.095, -0.21, 0.4)), Vector((s * 0.09, -0.22, 0.13))
        B.add(g.tongue([hip, knee], [0.12, 0.1], thick=0.75, normal=Z), B.main)
        B.add(g.tongue([knee + Vector((0, 0.01, 0.02)), foot], [0.095, 0.06], thick=0.7, normal=-Y), B.main)
        B.add(g.tongue([foot + Vector((0, 0.03, 0)), foot + Vector((0, -0.07, -0.03))], [0.06, 0.02], thick=0.5, normal=Z), B.under)
    B.add(g.tongue([(0, -0.2, 0.38), (0, -0.22, 0.24), (0.01, -0.21, 0.12)], [0.16, 0.12, 0.01], thick=0.2, normal=-Y), B.under)
    # forearms on the knees
    for s in (1, -1):
        sh = F.P(F.sh(s))
        el, wr = Vector((s * 0.15, sh.y - 0.07, 0.5)), Vector((s * 0.085, -0.22, 0.425))
        B.add(g.tongue([sh, el, wr], [0.095, 0.09, 0.065], thick=0.5, normal=(s, 0, 0.3)), B.main)
        B.add(sk.fingers(wr, Vector((-s * 0.4, -0.5, -0.6)), n=3, L=0.08, spread=0.018), B.under)
        F.hands["l" if s > 0 else "r"] = wr
    _chair(B, F, back=0.36 + 0.6 * bd.get("chair", 1.0))
    top = F.P(Vector((0, 0, F.top))).z
    B.frame(top, front=-0.26, mid=0.5, half=0.17)
    B.socket("socket_eyes", F.P(F.hood_at(0, -0.128, 0.682)))
    B.socket("socket_head", F.P(Vector((0, 0.04, F.top))))
    F.seated = True
    return F


def plan_robed(B, spec):
    """Gone down on its heels, the robe pooled round it, its head bent."""
    bd = {"tall": 0.55, "hood": 1.0, "wide": 1.0, "bent": 0.1}
    bd.update(spec.get("build", {}))
    k, wide = bd["tall"] / 0.55, bd["wide"]
    main, under = B.main, B.under
    B.add(g.lathe([(0.3 * wide, 0.0), (0.27 * wide, 0.03), (0.2, 0.12 * k), (0.16, 0.26 * k), (0.15, 0.36 * k), (0.1, 0.44 * k), (0.0, 0.46 * k)], n=10), main)
    hem = None
    for i in range(10):
        a = 2 * math.pi * i / 10
        hem = g.merge(hem, g.blade((0.22 * wide * math.cos(a), 0.22 * wide * math.sin(a), 0.05), (0.38 * wide * math.cos(a + 0.2), 0.38 * wide * math.sin(a + 0.2), 0.0), 0.16 * wide, normal=(0, 0, 1), belly=0.4))
    B.add(hem, B.mark("hem", under))
    F = Fig(B, {"hem": 0.2, "tall": 1.0, "hood": bd["hood"]})
    hz = 0.52 * k
    F.neck, F.top, F.zsh = hz - 0.08, hz + 0.12 * bd["hood"], 0.36 * k
    hy = -0.01 - bd["bent"]
    B.add(g.ico((0, hy, hz), 0.11 * bd["hood"], sub=1, scale=(1.0, 1.1, 1.05)), main)
    B.add(g.ico((0, hy - 0.05, hz - 0.02), 0.085 * bd["hood"], sub=1, scale=(0.9, 0.7, 1.0)), "void")
    B.add(g.tongue([(0, hy + 0.03, hz + 0.1), (0, hy + 0.11, hz + 0.04), (0, 0.16, 0.42 * k)], [0.02, 0.1, 0.01], thick=0.4, normal=(0, 1, 0.5)), under)
    F.eye_c = Vector((0, hy - 0.105, hz - 0.015))
    style, _ = opt(spec.get("eyes", "single"))
    if style == "single":
        B.add(g.ico(F.eye_c, 0.02, sub=1), field("eyes", 4.0))
    elif style == "old":
        eyes, lids = None, None
        for s in (1, -1):
            p = F.eye_c + Vector((s * 0.036, 0, 0.005))
            eyes = g.merge(eyes, g.ico(p, 0.024, sub=1, scale=(1.05, 0.5, 0.9)))
            lids = g.merge(lids, g.tongue([p + Vector((-0.03, -0.004, 0.022)), p + Vector((0, -0.012, 0.034)), p + Vector((0.03, -0.004, 0.016))], [0.008, 0.022, 0.008], thick=0.5, normal=(0, -1, 0.4)))
            lids = g.merge(lids, g.tongue([p + Vector((-0.028, -0.004, -0.022)), p + Vector((0, -0.01, -0.034)), p + Vector((0.028, -0.004, -0.022))], [0.006, 0.016, 0.006], thick=0.5, normal=(0, -1, -0.4)))
        B.add(eyes, field("eyes", 3.4))
        B.add(lids, "mask_pale")
    else:
        B.add(sk.eye_pair(F.eye_c, 0.03, 0.016), field("eyes", 3.5))
    # the arms: to the lap, or held out
    pose, _ = opt(spec.get("arms", "lap"))
    for s in (1, -1):
        sh = Vector((s * 0.15, -0.02, 0.36 * k))
        if pose == "cup":
            el, wr = Vector((s * 0.17, -0.2, 0.3 * k)), Vector((s * 0.05, -0.34, 0.3 * k))
        else:
            el, wr = Vector((s * 0.17, -0.16, 0.24 * k)), Vector((s * 0.06, -0.22, 0.2 * k))
        B.add(g.tube([sh, el, wr], [0.05, 0.04, 0.03], n=6), main, True)
        B.add(g.ico(wr + Vector((-s * 0.015, -0.005, 0)), 0.03, sub=0, scale=(1, 1, 0.7)), under)
        F.hands["l" if s > 0 else "r"] = wr
    B.ground = False
    B.frame(F.top, front=-0.2, mid=0.36 * k, half=0.2)
    B.socket("socket_eyes", F.eye_c + Vector((0, -0.01, 0)))
    B.socket("socket_light", (0, -0.23, 0.245 * k))
    F.robed = True
    return F


def _hood_only(B, c, k=1.0, eyes="slit", under=None):
    """Just the hood and what is in it, its neck at c."""
    F = Fig(B, {"hem": c[2] - 0.4, "tall": 1.0, "hood": k})
    rings = []
    for z, rx, ry, yo in PROF[:6]:
        zz = F.neck + (z - 0.6) * k
        rings.append(g.ring((c[0], c[1] + yo * k, zz), rx * k, ry * k, n=10, u=X, v=Y, phase=math.pi / 10))
    B.add(g.loft(rings[::-1]), B.main)
    shift = Vector((c[0], c[1], 0))
    B.add(sk.shifted(g.ico(F.hood_at(0, -0.086, 0.672), 0.075 * k, sub=1, scale=(0.92, 0.42, 1.18)), shift), "void")
    for s in (1, -1):
        B.add(sk.shifted(g.tongue([F.hood_at(0, -0.1, 0.785), F.hood_at(s * 0.066, -0.118, 0.72), F.hood_at(s * 0.078, -0.116, 0.64), F.hood_at(s * 0.04, -0.1, 0.575)], [0.02 * k, 0.034 * k, 0.032 * k, 0.012], thick=0.5, normal=(s * 0.3, -1, 0)), shift), under or B.under)
    keep, F.B = F.B, _Shift(B, shift)
    face_eyes(F, eyes)
    F.B = keep
    F.c = shift
    return F


class _Shift:
    """A Body that puts what it is given somewhere else."""

    def __init__(self, B, d):
        self.B, self.d = B, V(d)
        self.main, self.under = B.main, B.under

    def add(self, geo, material, smooth=None):
        self.B.add(sk.shifted(geo, self.d) if geo else geo, material, smooth)


def plan_door(B, spec):
    """It stands in a doorway in the shape of a door."""
    bd = {"tall": 1.0, "wide": 1.0}
    bd.update(spec.get("build", {}))
    h, w = 0.66 * bd["tall"], 0.21 * bd["wide"]
    main, under = B.main, B.under
    posts = g.merge(g.box((w, 0, 0.09 + h / 2), (0.07, 0.07, h)), g.box((-w, 0, 0.09 + h / 2), (0.07, 0.07, h)))
    B.add(posts, main, False)
    B.add(g.box((0, 0, 0.09 + h + 0.03), (2 * w + 0.13, 0.085, 0.07)), main, False)
    B.add(g.box((0, 0, 0.075), (2 * w + 0.13, 0.1, 0.03)), under, False)
    # the leaf of the door: only its rails, so you can see through it
    rails = None
    for t in (0.2, 0.5, 0.8):
        rails = g.merge(rails, g.box((0, 0, 0.09 + h * t), (2 * w - 0.07, 0.014, 0.018)))
    rails = g.merge(rails, g.box((0, 0, 0.09 + h / 2), (0.018, 0.014, h)))
    B.add(rails, under, False)
    B.add(g.ico((w - 0.07, -0.03, 0.09 + h * 0.48), 0.018, sub=0), "mask_pale", False)
    style, _ = opt(spec.get("eyes", "slit"))
    F = _hood_only(B, (0, 0, 0.09 + h + 0.03), 0.95, style)
    # its hands on the posts, from behind
    for s in (1, -1):
        wr = Vector((s * (w + 0.045), 0.02, 0.09 + h * 0.62))
        B.add(sk.fingers(wr, Vector((-s, -0.6, 0)), n=3, L=0.07, spread=0.03, r=0.017, hook=0.2), under)
        F.hands["l" if s > 0 else "r"] = wr
    hang = None
    for i, x in enumerate((-0.6, 0.0, 0.6)):
        hang = g.merge(hang, g.tongue([(x * w, 0.0, 0.075), (x * w + 0.01, 0.01, 0.0), (x * w, 0.02, -0.07 - 0.03 * (i % 2))], [0.06, 0.04, 0.003], thick=0.3, normal=-Y))
    B.add(hang, main)
    F.door = (w, h)
    B.frame(F.top, front=-0.08, mid=0.09 + h * 0.6, half=w + 0.05)
    B.socket("socket_eyes", Vector((0, -0.125, F.neck + 0.082 * 0.95)))
    return F


def plan_gate(B, spec):
    """A gate: pillars, an arch, the hood for its keystone; the air in it stands still."""
    bd = {"tall": 1.0, "wide": 1.0}
    bd.update(spec.get("build", {}))
    h, w = 0.6 * bd["tall"], 0.27 * bd["wide"]
    main, under = B.main, B.under
    for s in (1, -1):
        B.add(g.lathe([(0.075, 0.0), (0.07, 0.03), (0.05, 0.05), (0.047, h - 0.04), (0.07, h - 0.02), (0.075, h)], n=8, centre=(s * w, 0, 0.07)), main)
        B.add(g.lathe([(0.09, 0.0), (0.09, 0.03), (0.07, 0.04)], n=8, centre=(s * w, 0, 0.04)), under, False)
    B.add(sk.arc((0, 0, 0.07 + h), w, w * 0.78, 0.0, math.pi, 0.05, n=10, u=X, v=Z, sides=6), main)
    B.add(g.box((0, 0, 0.045), (2 * w + 0.2, 0.16, 0.035)), under, False)
    style, _ = opt(spec.get("eyes", "slit"))
    F = _hood_only(B, (0, 0, 0.07 + h + w * 0.78 - 0.02), 1.05, style)
    for s in (1, -1):
        wr = Vector((s * (w + 0.05), 0.01, 0.07 + h * 0.7))
        B.add(sk.fingers(wr, Vector((-s, -0.6, 0)), n=3, L=0.075, spread=0.032, r=0.018, hook=0.2), under)
        F.hands["l" if s > 0 else "r"] = wr
    hang = None
    for i, x in enumerate((-0.8, -0.3, 0.3, 0.8)):
        hang = g.merge(hang, g.tongue([(x * w, 0.0, 0.05), (x * w + 0.01, 0.01, -0.03), (x * w, 0.02, -0.1 - 0.03 * (i % 2))], [0.07, 0.05, 0.003], thick=0.3, normal=-Y))
    B.add(hang, main)
    F.door = (w, h + w * 0.6)
    B.frame(F.top, front=-0.1, mid=0.07 + h * 0.6, half=w + 0.07)
    B.socket("socket_eyes", Vector((0, -0.135, F.neck + 0.082 * 1.05)))
    return F


def plan_hatch(B, spec):
    """It comes up out of a hatch in the floor, its hands on the rim."""
    main = B.main
    w = 0.26
    rim = None
    for s in (1, -1):
        rim = g.merge(rim, g.box((s * w, -0.02, 0.1), (0.06, 2 * w + 0.06, 0.06)), g.box((0, -0.02 + s * w, 0.1), (2 * w + 0.06, 0.06, 0.06)))
    B.add(rim, "timber", False)
    B.add(g.box((0, -0.02, 0.085), (2 * w, 2 * w, 0.02)), "void", False)
    steps = None
    for i in range(3):
        steps = g.merge(steps, g.box((0.1, -0.2 + 0.11 * i, 0.1 - 0.012 * i), (0.22, 0.09, 0.012)))
    B.add(steps, "brick", False)
    # the lid, thrown back
    B.add(g.box((0, w + 0.1, 0.3), (2 * w - 0.02, 0.04, 2 * w - 0.06), rot=(0.35, 0, 0)), "timber", False)
    B.add(sk.arc((0, w + 0.03, 0.33), 0.05, 0.05, 0.0, math.pi, 0.012, n=6, u=X, v=Z, sides=3), "metal_iron", False)
    bd = {"tall": 0.62, "hem": 0.12, "broad": 1.3, "hood": 1.05, "lean": 0.1, "skirt": 1.6}
    bd.update(spec.get("build", {}))
    F = Fig(B, bd)
    cloak(F)
    style, _ = opt(spec.get("eyes", "holes"))
    hood(F, style)
    for s in (1, -1):
        sh = F.P(F.sh(s))
        el, wr = Vector((s * 0.3, -0.08, 0.26)), Vector((s * 0.2, -0.27, 0.135))
        B.add(g.tongue([sh, el, wr], [0.12, 0.11, 0.08], thick=0.5, normal=(s, 0, 0.3)), main)
        B.add(sk.fingers(wr, Vector((-s * 0.1, -1, -0.1)), n=3, L=0.1, spread=0.03, r=0.02, hook=0.3), "brick")
        F.hands["l" if s > 0 else "r"] = wr
    wisps(F)
    top = F.P(Vector((0, 0, F.top))).z
    B.frame(top, front=-0.14, mid=0.4, half=0.28)
    B.socket("socket_eyes", F.P(F.hood_at(0, -0.128, 0.682)))
    return F


def plan_human(B, spec):
    """It has your outline: a person of shadow, hollow, with a faint second face."""
    main, under = B.main, B.under
    k = spec.get("build", {}).get("tall", 1.0)
    z = lambda v: v * k  # noqa: E731
    B.add(g.lathe([(0.075, z(0.4)), (0.12, z(0.47)), (0.105, z(0.58)), (0.15, z(0.7)), (0.165, z(0.76)), (0.06, z(0.8))], n=10), main)
    B.add(g.tube([(0, 0, z(0.78)), (0, 0, z(0.84))], [0.045, 0.04], n=8), main, True)
    B.add(g.ico((0, 0, z(0.92)), 0.092, sub=1, scale=(0.95, 1.0, 1.12)), main)
    for s in (1, -1):
        B.add(g.tube([(s * 0.16, 0, z(0.75)), (s * 0.21, -0.01, z(0.58)), (s * 0.235, -0.05, z(0.42))], [0.05, 0.04, 0.03], n=6), main, True)
        B.add(sk.fingers((s * 0.235, -0.05, z(0.42)), Vector((s * 0.1, -0.2, -1)), n=3, L=0.1, spread=0.018), under)
        B.add(g.tube([(s * 0.07, 0, z(0.43)), (s * 0.085, -0.01, z(0.22)), (s * 0.08, 0.0, z(0.04))], [0.065, 0.05, 0.035], n=6), main, True)
        B.add(g.tongue([(s * 0.08, 0.03, z(0.03)), (s * 0.085, -0.08, 0.0)], [0.06, 0.02], thick=0.5, normal=Z), under)
    # hollow: what it took has left its shape
    B.add(g.ico((0, -0.085, z(0.63)), 0.1, sub=1, scale=(1.15, 0.4, 1.55)), "void")
    rim = None
    for i in range(12):
        a = 2 * math.pi * i / 12
        p = Vector((0.118 * math.cos(a), -0.105, z(0.63) + 0.16 * math.sin(a)))
        rim = g.merge(rim, g.blade(p, p + Vector((-0.04 * math.cos(a), -0.01, -0.05 * math.sin(a))), 0.05, normal=-Y))
    B.add(rim, under)
    # the second face: faint, pale, its eyes shut
    B.add(g.ico((0, -0.078, z(0.925)), 0.07, sub=1, scale=(0.82, 0.32, 1.1)), "mask_pale")
    B.add(g.tongue([(0, -0.1, z(0.94)), (0, -0.112, z(0.91)), (0, -0.1, z(0.892))], [0.01, 0.02, 0.006], thick=0.7, normal=X), "mask_pale")
    B.add(sk.eye_pair((0, -0.1, z(0.94)), 0.028, 0.014, scale=(1.3, 0.4, 0.3), slant=-0.15), field("eyes", 1.6))
    B.add(g.box((0, -0.097, z(0.875)), (0.03, 0.008, 0.005)), "void", False)
    wis = None
    for sgn, x in ((1, 0.12), (-1, 0.14), (1, -0.02)):
        b = Vector((x * sgn, 0.05, z(0.78)))
        wis = g.merge(wis, g.tongue([b, b + Vector((sgn * 0.03, 0.04, 0.08)), b + Vector((0, 0.08, 0.17))], [0.035, 0.025, 0.002], thick=0.3))
    B.add(wis, under)
    F = Fig(B, {"hem": 0.0, "tall": 1.0})
    F.top, F.zsh, F.neck = z(1.02), z(0.75), z(0.8)
    F.hands = {"l": Vector((0.235, -0.05, z(0.42))), "r": Vector((-0.235, -0.05, z(0.42)))}
    B.frame(F.top, front=-0.12, mid=z(0.6), half=0.2)
    B.socket("socket_eyes", (0, -0.11, z(0.94)))
    return F


def plan_streak(B, spec):
    """It goes along with what was sent: a figure thrown forward, its hands out ahead of it."""
    main, under = B.main, B.under
    # the body lies along the way it flies: head low and forward, the cloak a long streak behind
    spine = [Vector((0.0, -0.3, 0.5)), Vector((0.0, -0.12, 0.56)), Vector((0.0, 0.12, 0.55)), Vector((0.02, 0.4, 0.5)), Vector((-0.02, 0.72, 0.43)), Vector((0.02, 1.0, 0.38))]
    B.add(g.tube(spine, [0.085, 0.12, 0.125, 0.09, 0.05, 0.004], n=8), main, True)
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    B.add(g.ico((0, -0.33, 0.47), 0.07, sub=1, scale=(0.92, 1.0, 0.8)), "void")
    for s in (1, -1):
        B.add(g.tongue([(0, -0.22, 0.585), (s * 0.075, -0.3, 0.55), (s * 0.085, -0.36, 0.48), (s * 0.04, -0.38, 0.42)], [0.02, 0.036, 0.034, 0.012], thick=0.5, normal=(s * 0.3, -0.5, 1)), under)
    B.add(sk.eye_pair((0, -0.385, 0.475), 0.028, 0.017), field("eyes", 3.8))
    for s in (1, -1):
        sh, el, wr = Vector((s * 0.1, -0.1, 0.52)), Vector((s * 0.17, -0.34, 0.47)), Vector((s * 0.11, -0.6, 0.44))
        B.add(g.tongue([sh, el, wr], [0.09, 0.07, 0.05], thick=0.5, normal=(s, 0, 0.5)), main)
        B.add(sk.fingers(wr, Vector((-s * 0.1, -1, -0.15)), n=4, L=0.15, spread=0.026, r=0.016, hook=0.55), under)
        F.hands["l" if s > 0 else "r"] = wr
    stream = None
    for i in range(9):
        t = i / 8
        p = spine[2] + (spine[5] - spine[2]) * t
        a = i * 2.2
        d = Vector((math.cos(a) * 0.1, 0.0, math.sin(a) * 0.08))
        stream = g.merge(stream, g.tongue([p + d, p + d * 1.5 + Vector((0, 0.16, -0.02)), p + d * 1.2 + Vector((0, 0.36, -0.03))], [0.07, 0.05, 0.003], thick=0.3, normal=d))
    B.add(stream, under)
    F.top, F.zsh, F.neck = 0.62, 0.52, 0.5
    B.frame(0.62, front=-0.4, mid=0.5, half=0.16)
    B.socket("socket_eyes", (0, -0.395, 0.475))
    B.socket("socket_back", (0, 0.2, 0.62))
    return F


def plan_corner(B, spec):
    """Something in the corner of the ceiling: a clot of dark, one pale eye, long fingers hanging."""
    main, under = B.main, B.under
    c = Vector((0, 0, 0.78))
    B.add(g.ico(c, 0.2, sub=1, scale=(1.15, 0.95, 0.72)), main)
    lobes = None
    for i, (dx, dy, dz, r) in enumerate(((0.2, 0.1, 0.06, 0.12), (-0.21, 0.08, 0.04, 0.13), (0.0, 0.16, 0.1, 0.13), (0.1, -0.08, -0.09, 0.1), (-0.1, -0.06, -0.1, 0.11))):
        lobes = g.merge(lobes, g.ico(c + Vector((dx, dy, dz)), r, sub=1, scale=(1.1, 1.0, 0.8), rot=(0, 0, i)))
    B.add(lobes, under)
    # the three strands that hold it in its corner
    strands = None
    for a in (0.35, 2.6, 4.9):
        d = Vector((math.cos(a), math.sin(a) * 0.5 + 0.5, 0))
        strands = g.merge(strands, g.tube([c + d * 0.15 + Z * 0.08, c + d * 0.42 + Z * 0.2, c + d * 0.72 + Z * 0.34], [0.03, 0.016, 0.003], n=4))
    B.add(strands, main, True)
    eye = c + Vector((0, -0.17, -0.01))
    B.add(g.ico(eye, 0.11, sub=1, scale=(1.3, 0.4, 0.84)), "mask_pale")
    B.add(g.ico(eye + Vector((0, -0.03, 0.0)), 0.048, sub=1, scale=(1.0, 0.5, 1.0)), field("eyes", 4.2))
    B.add(sk.arc(eye + Vector((0, -0.012, 0.0)), 0.15, 0.1, 0.15, math.pi - 0.15, 0.018, n=8, u=X, v=Z, sides=3), main)
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    hang = None
    for i, (x, L) in enumerate(((-0.2, 0.42), (-0.12, 0.6), (-0.04, 0.5), (0.05, 0.66), (0.13, 0.46), (0.21, 0.56))):
        b = c + Vector((x, -0.06 + 0.03 * (i % 2), -0.1))
        hang = g.merge(hang, g.tongue([b, b + Vector((0.01, -0.02, -L * 0.5)), b + Vector((-0.01 + 0.02 * (i % 3), -0.05, -L))], [0.03, 0.022, 0.002], thick=0.5))
    B.add(hang, main)
    F.top, F.zsh, F.neck = 0.93, 0.7, 0.78
    F.hands = {"l": Vector((0.21, -0.1, 0.3)), "r": Vector((-0.2, -0.1, 0.36))}
    B.frame(0.93, front=-0.2, mid=0.72, half=0.24)
    B.socket("socket_eyes", eye + Vector((0, -0.03, 0)))
    return F


def plan_monolith(B, spec):
    """No step, no cloth, no breath: a still shape with nothing loose on it."""
    main = B.main
    k = spec.get("build", {}).get("tall", 1.0)
    B.add(g.lathe([(0.0, 0.1), (0.08, 0.14), (0.13, 0.3), (0.15, 0.5 * k), (0.13, 0.7 * k), (0.11, 0.8 * k), (0.115, 0.9 * k), (0.085, 1.0 * k), (0.0, 1.05 * k)], n=12), main)
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    c = Vector((0, -0.105, 0.9 * k))
    B.add(g.ico(c + Vector((0, 0.02, 0)), 0.07, sub=1, scale=(0.9, 0.4, 1.1)), "void")
    geo = None
    for s in (1, -1):
        geo = g.merge(geo, g.box(c + Vector((s * 0.03, -0.012, 0.0)), (0.034, 0.006, 0.005)))
    B.add(geo, field("eyes", 2.0))
    F.top, F.zsh, F.neck = 1.05 * k, 0.66 * k, 0.8 * k
    B.frame(F.top, front=-0.14, mid=0.55 * k, half=0.16)
    B.socket("socket_eyes", c + Vector((0, -0.02, 0)))
    return F


def plan_tree(B, spec):
    """You count the trees and there is one too many."""
    main, under = B.main, B.under
    B.add(g.lathe([(0.11, 0.06), (0.085, 0.2), (0.075, 0.5), (0.07, 0.8), (0.08, 0.92), (0.06, 1.02), (0.0, 1.08)], n=8), main)
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    roots = None
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        roots = g.merge(roots, g.tube([d * 0.07 + Z * 0.14, d * 0.2 + Z * 0.05, d * (0.34 + 0.06 * (i % 2)) + Z * 0.0], [0.04, 0.028, 0.004], n=5))
    B.add(roots, main, True)
    # the arms go up as branches
    for s, lift in ((1, 0.0), (-1, 0.08)):
        b0, b1, b2 = Vector((s * 0.06, 0, 0.82)), Vector((s * 0.2, -0.02, 0.98 + lift)), Vector((s * 0.3, 0.0, 1.2 + lift))
        B.add(g.tube([b0, b1, b2], [0.04, 0.028, 0.012], n=5), main, True)
        twigs = None
        for j, (dx, dy, dz) in enumerate(((0.12, -0.03, 0.14), (0.02, 0.05, 0.2), (-0.06, -0.04, 0.17))):
            twigs = g.merge(twigs, g.tube([b2, b2 + Vector((s * dx, dy, dz)) * 0.6, b2 + Vector((s * dx, dy, dz)) * 1.2], [0.012, 0.008, 0.002], n=4))
        tw2 = b1 + Vector((s * 0.02, 0, 0.02))
        twigs = g.merge(twigs, g.tube([tw2, tw2 + Vector((s * 0.13, -0.04, 0.02)), tw2 + Vector((s * 0.2, -0.06, 0.1))], [0.014, 0.009, 0.002], n=4))
        B.add(twigs, under, True)
        F.hands["l" if s > 0 else "r"] = b2
    leaves = None
    for i, (x, y, z) in enumerate(((0.33, 0.02, 1.3), (-0.3, 0.0, 1.42), (0.42, -0.05, 1.18), (-0.38, 0.04, 1.22), (0.25, 0.06, 1.42))):
        leaves = g.merge(leaves, g.blade((x, y, z), (x + 0.03 * (-1) ** i, y, z - 0.09), 0.05, normal=Y))
    B.add(leaves, under)
    # eyes like two holes in the hedge
    holes, rims = None, None
    for s in (1, -1):
        p = Vector((s * 0.03, -0.073, 0.93))
        holes = g.merge(holes, g.ico(p, 0.022, sub=1, scale=(1.0, 0.5, 1.2)))
        rims = g.merge(rims, sk.hoop(p + Vector((0, -0.006, 0)), 0.027, 0.031, 0.006, n=8, u=X, v=Z, sides=3))
    B.add(holes, "void")
    B.add(rims, "mask_pale", False)
    F.top, F.zsh, F.neck = 1.08, 0.82, 0.9
    B.frame(1.08, front=-0.1, mid=0.6, half=0.14)
    B.socket("socket_eyes", (0, -0.085, 0.93))
    return F


PLANS = {"blot": plan_blot, "figure": plan_figure, "seated": plan_seated, "robed": plan_robed, "door": plan_door, "gate": plan_gate, "hatch": plan_hatch,
         "human": plan_human, "streak": plan_streak, "corner": plan_corner, "monolith": plan_monolith, "tree": plan_tree}


# --- what it has, round the figure -----------------------------------------------------------

def legs_stilts(B, F, size):
    """Tall and thin: two legs of the same dark under the hem."""
    for s in (1, -1):
        hip = Vector((s * 0.035, 0.0, F.hem + 0.02))
        knee = hip + Vector((s * 0.015, -0.02, -0.26 * size))
        foot = hip + Vector((s * 0.02, 0.0, -0.52 * size))
        B.add(g.tube([hip, knee, foot], [0.03, 0.02, 0.012], n=5), B.main, True)
        B.add(g.tongue([foot + Vector((0, 0.02, 0)), foot + Vector((0, -0.07, -0.015))], [0.035, 0.008], thick=0.5, normal=Z), B.under)


def legs_back(B, F, size):
    """Long thin legs that fold the wrong way."""
    for s in (1, -1):
        hip = Vector((s * 0.06, 0.02, F.hem + 0.04))
        knee = hip + Vector((s * 0.05, 0.2 * size, -0.12 * size))
        ank = hip + Vector((s * 0.06, -0.06 * size, -0.36 * size))
        foot = hip + Vector((s * 0.06, 0.02 * size, -0.52 * size))
        B.add(g.tube([hip, knee, ank, foot], [0.035, 0.024, 0.017, 0.012], n=5), B.main, True)
        B.add(sk.fingers(foot, Vector((0, -1, -0.15)), n=3, L=0.09, spread=0.022, r=0.014, hook=0.2), B.under)


def legs_roots(B, F, size):
    roots = None
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        roots = g.merge(roots, g.tube([d * 0.05 + Z * (F.hem + 0.03), d * 0.16 + Z * (F.hem - 0.06), d * (0.28 + 0.05 * (i % 2)) + Z * (F.hem - 0.1)], [0.035, 0.025, 0.004], n=5))
    B.add(roots, B.main, True)


def ground_long(B, F, size):
    """It stretches long across the floor, and there are eyes in it."""
    z0 = F.hem - 0.24
    pts = [Vector((0, 0.02, z0)), Vector((-0.2, 0.06, z0 - 0.005)), Vector((-0.48, 0.14, z0 - 0.01)), Vector((-0.78, 0.2, z0 - 0.01))]
    pts = [Vector((p.x * size, p.y * size, p.z)) for p in pts]
    B.add(g.tongue(pts, [0.24, 0.36, 0.28, 0.03], thick=0.16, normal=Z), B.under)
    B.add(g.tongue([Vector((0, 0, F.hem)), Vector((-0.03, 0.01, F.hem - 0.12)), pts[0]], [0.1, 0.12, 0.2], thick=0.5, normal=-Y), B.main)
    # the eyes in it: each on a swell of the shadow, looking up the room
    eyes, lids, swell = None, None, None
    for i, t in enumerate((0.3, 0.56, 0.8)):
        p = pts[0] + (pts[3] - pts[0]) * t + Vector((0, -0.03 + 0.03 * (i % 2), 0.035))
        k = 1.0 - 0.18 * i
        swell = g.merge(swell, g.ico(p, 0.07 * k, sub=1, scale=(1.3, 1.0, 0.75)))
        eyes = g.merge(eyes, g.ico(p + Vector((0, -0.06 * k, 0.012)), 0.022 * k, sub=1, scale=(1.1, 0.5, 0.9)))
        lids = g.merge(lids, sk.arc(p + Vector((0, -0.062 * k, 0.012)), 0.04 * k, 0.034 * k, 0.1, math.pi - 0.1, 0.007, n=6, u=X, v=Z, sides=3))
    B.add(swell, B.under)
    B.add(eyes, field("eyes", 3.2))
    B.add(lids, "mask_pale", False)


def ground_cohort(B, F, size):
    """Twelve small shapes stand round its hem."""
    heads, eyes = None, None
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        d = Vector((math.cos(a), math.sin(a) * 0.8, 0))
        c = d * (0.25 + 0.03 * (i % 2)) * size + Z * (F.hem - 0.12 - 0.03 * (i % 3))
        heads = g.merge(heads, g.lathe([(0.0, -0.06), (0.03, -0.04), (0.036, 0.03), (0.026, 0.065), (0.0, 0.085)], n=6, centre=c))
        if d.y < 0.2:
            eyes = g.merge(eyes, g.ico(c + Vector((d.x * 0.02, -0.03, 0.035)), 0.008, sub=0))
    B.add(heads, B.under)
    B.add(eyes, field("eyes", 2.4))


def ground_ring(B, F, size):
    """The quiet has an edge: rings of pale, round its foot."""
    B.add(sk.hoop((0, 0, 0.14), 0.3 * size, 0.3 * size, 0.008, n=20, sides=3), "mask_pale", False)
    B.add(sk.hoop((0, 0, 0.2), 0.4 * size, 0.4 * size, 0.005, n=22, sides=3), "veil", False)
    B.add(sk.hoop((0, 0, 0.09), 0.2 * size, 0.2 * size, 0.006, n=16, sides=3), "veil", False)


def ground_wall(B, F, size):
    """The wall it listens at."""
    x = 0.36
    bricks = None
    for r in range(5):
        for c in range(3):
            y = -0.2 + c * 0.17 + (0.085 if r % 2 else 0.0)
            bricks = g.merge(bricks, g.box((x, y, F.hem + 0.02 + r * 0.11), (0.05, 0.155, 0.095)))
    B.add(bricks, "brick", False)


def wears_mantle(B, F, size):
    """Broad across the back: a yoke of the same dark over the shoulders."""
    z = F.zsh
    w = 0.185 * F.broad * (0.9 + 0.1 * size)
    rings = [g.ring((0, 0.012, z - 0.13 * size), w + 0.04, 0.125 * F.deep + 0.02, n=10, u=X, v=Y, phase=math.pi / 10),
             g.ring((0, 0.01, z - 0.02), w + 0.02, 0.118 * F.deep + 0.012, n=10, u=X, v=Y, phase=math.pi / 10),
             g.ring((0, 0.005, z + 0.045), w * 0.72, 0.1 * F.deep, n=10, u=X, v=Y, phase=math.pi / 10)]
    F.put(g.loft(rings, caps=False), B.under)
    pts = None
    for i in range(10):
        a = 2 * math.pi * (i + 0.5) / 10
        d = Vector((math.cos(a) * (w + 0.04), math.sin(a) * (0.125 * F.deep + 0.02), 0))
        pts = g.merge(pts, g.blade(Vector((0, 0.012, z - 0.12 * size)) + d, Vector((0, 0.012, z - 0.12 * size - 0.09 * size)) + d * 1.08, 0.09, normal=d, belly=0.35))
    F.put(pts, B.under)


def wears_collar(B, F, size):
    """Its collar is up: two wings of it stand to the eyes."""
    z = F.neck - 0.045
    for s in (1, -1):
        pts = [Vector((s * 0.03, -0.1 * F.hood, z)), Vector((s * 0.1 * F.hood, -0.08 * F.hood, z + 0.06 * size)), Vector((s * 0.135 * F.hood, -0.02, z + 0.14 * size)), Vector((s * 0.125 * F.hood, 0.06, z + 0.17 * size))]
        F.put(g.tongue(pts, [0.05, 0.13 * size, 0.15 * size, 0.06], thick=0.25, normal=(s, -0.4, 0.2)), B.under)
    F.put(g.tongue([Vector((-0.1 * F.hood, 0.08, z + 0.02)), Vector((0, 0.115 * F.hood, z + 0.1 * size)), Vector((0.1 * F.hood, 0.08, z + 0.02))], [0.1, 0.17 * size, 0.1], thick=0.25, normal=(0, 1, 0.2)), B.under)


def wears_script(B, F, size):
    """Lines of what was sworn, round the cloak."""
    geo = None
    for t in (0.36, 0.5):
        z = F.hem + (t - 0.2) * F.tall
        geo = g.merge(geo, sk.hoop((0, 0.01, z), 0.15 * F.broad * (0.86 if t < 0.4 else 1.0), 0.1 * F.deep, 0.006, n=12, sides=3))
    F.put(geo, field("script", 2.0))


def wears_cape(B, F, size):
    """The cloak thrown back behind it, as if it had moved."""
    z = F.zsh
    for s in (1, -1):
        pts = [Vector((s * 0.1, 0.06, z + 0.02)), Vector((s * 0.2, 0.22 * size, z - 0.04)), Vector((s * 0.25, 0.46 * size, z - 0.16)), Vector((s * 0.18, 0.66 * size, z - 0.24))]
        F.put(g.tongue(pts, [0.16, 0.24, 0.2, 0.02], thick=0.2, normal=(s * 0.4, 0, 1)), B.under)
    F.put(g.tongue([Vector((0, 0.08, z + 0.02)), Vector((0, 0.3 * size, z - 0.08)), Vector((0, 0.56 * size, z - 0.22)), Vector((0, 0.78 * size, z - 0.3))], [0.2, 0.26, 0.2, 0.02], thick=0.2, normal=Z), B.main)


def wears_shawl(B, F, size):
    """A shawl over the shoulders, for the cold hour."""
    z = F.zsh
    rings = [g.ring((0, 0.0, z - 0.12 * size), 0.2, 0.15, n=10, u=X, v=Y, phase=math.pi / 10), g.ring((0, 0.0, z + 0.02), 0.175, 0.13, n=10, u=X, v=Y, phase=math.pi / 10),
             g.ring((0, 0.0, z + 0.07), 0.1, 0.09, n=10, u=X, v=Y, phase=math.pi / 10)]
    F.put(g.loft(rings, caps=False), "cloth_wool")
    fr = None
    for i in range(10):
        a = 2 * math.pi * (i + 0.5) / 10
        d = Vector((math.cos(a) * 0.2, math.sin(a) * 0.15, 0))
        fr = g.merge(fr, g.blade(Vector((0, 0, z - 0.11 * size)) + d, Vector((0, 0, z - 0.2 * size)) + d * 1.05, 0.06, normal=d))
    F.put(fr, "cloth_wool")


def wears_rime(B, F, size):
    """Rime on its hem and its collar."""
    geo = None
    for i in range(9):
        a = 2 * math.pi * (i + 0.5) / 9
        d = Vector((math.cos(a), math.sin(a) * 0.72, 0))
        b = d * 0.085 * F.skirt + Z * (F.hem + 0.03)
        geo = g.merge(geo, sk.crystal(b, b + d * 0.05 + Z * (-0.1 - 0.04 * (i % 3)) * size, 0.016, n=4))
    for i in range(7):
        a = math.pi * (0.1 + 0.8 * i / 6)
        d = Vector((math.cos(a), -math.sin(a) * 0.5, 0))
        b = d * 0.15 * F.broad + Z * (F.zsh + 0.03)
        geo = g.merge(geo, sk.crystal(b, b + d * 0.04 + Z * 0.08 * size, 0.014, n=4))
    F.put(geo, "ice_pale")


def chest_maw(B, F, size):
    """A wide dark place in the middle of it, like a mouth."""
    c = F.chest + Vector((0, -0.016, -0.01))
    F.put(g.ico(c + Vector((0, 0.03, 0)), 0.13 * size, sub=1, scale=(1.3 * F.broad, 0.35, 0.92)), "void")
    rim = None
    n = 14
    for i in range(n):
        a = 2 * math.pi * i / n
        p = c + Vector((0.17 * F.broad * size * math.cos(a), 0.0, 0.125 * size * math.sin(a)))
        rim = g.merge(rim, g.blade(p + Vector((0.02 * math.cos(a), 0, 0.02 * math.sin(a))), p + Vector((-0.085 * math.cos(a), -0.014, -0.07 * math.sin(a))) * 1.0, 0.045 * size, normal=-Y, belly=0.25))
    F.put(rim, B.under)


def chest_cold_hand(B, F, size):
    """A patch of cold the size of a hand."""
    c = F.chest + Vector((0, -0.018, 0.02))
    F.put(g.ico(c, 0.04 * size, sub=1, scale=(1.0, 0.3, 1.1)), "ice_pale")
    fing = None
    for i, a in enumerate((-0.6, -0.25, 0.05, 0.35, 0.95)):
        d = Vector((math.sin(a), 0, math.cos(a)))
        L = (0.075 if i != 4 else 0.05) * size
        fing = g.merge(fing, g.tongue([c + d * 0.03 * size, c + d * (0.03 * size + L)], [0.018 * size, 0.012 * size], thick=0.4, normal=-Y))
    F.put(fing, "ice_pale")
    F.put(g.ico(c + Vector((0, -0.012, 0)), 0.014 * size, sub=0), field("core", 3.2))


def chest_core(B, F, size):
    """A cold light in the middle of it."""
    c = F.chest + Vector((0, -0.01, 0.02))
    F.put(g.ico(c, 0.045 * size, sub=1, scale=(0.8, 0.5, 1.3)), field("core", 3.4))
    geo = None
    for i in range(6):
        a = 2 * math.pi * i / 6
        d = Vector((math.cos(a), 0, math.sin(a)))
        geo = g.merge(geo, sk.crystal(c + d * 0.05 * size, c + d * 0.13 * size + Vector((0, -0.02, 0)), 0.016, n=4))
    F.put(geo, "ice")


def face_mask(B, F, size):
    """A blank pale mask hangs in the dark of the hood."""
    H = F.hood_at
    F.put(g.ico(H(0, -0.1, 0.672), 0.07 * F.hood * size, sub=1, scale=(0.84, 0.3, 1.16)), "mask_pale")
    geo = None
    for s in (1, -1):
        geo = g.merge(geo, g.box(H(s * 0.028, -0.123, 0.69), (0.03 * size, 0.008, 0.006)))
    F.put(geo, "void", False)


def _second_face(F, c, r, crowned=False, mouth=True):
    B = F.B
    # its neck, from the shoulder
    root = F.sh(1) + Vector((-0.04, 0.0, 0.03))
    F.put(g.tube([root, (root + c) / 2 + Vector((0.02, 0.02, 0)), c + Vector((0, 0.01, -r * 0.7))], [0.03, 0.022, 0.02], n=5), B.main, True)
    F.put(g.ico(c, r, sub=1, scale=(0.95, 0.95, 1.1)), B.main)
    F.put(g.ico(c + Vector((0, -r * 0.62, 0.0)), r * 0.8, sub=1, scale=(0.84, 0.36, 1.12)), "mask_pale")
    F.put(g.tongue([c + Vector((0, -r * 0.92, r * 0.25)), c + Vector((0, -r * 1.08, 0)), c + Vector((0, -r * 0.9, -r * 0.18))], [r * 0.14, r * 0.26, r * 0.08], thick=0.7, normal=X), "mask_pale")
    F.put(sk.eye_pair(c + Vector((0, -r * 0.94, r * 0.28)), r * 0.36, r * 0.17, scale=(1.3, 0.4, 0.45), slant=0.25), field("eyes", 3.0))
    if mouth:
        F.put(g.tongue([c + Vector((-r * 0.36, -r * 0.84, -r * 0.42)), c + Vector((0, -r * 0.95, -r * 0.5)), c + Vector((r * 0.36, -r * 0.84, -r * 0.42))], [0.004, r * 0.22, 0.004], thick=0.3, normal=(0, -1, 0)), field("mouth", 3.2))
    if crowned:
        F.put(sk.hoop(c + Vector((0, 0, r * 0.8)), r * 0.82, r * 0.82, r * 0.1, n=10, sides=3), "metal_brass", False)
        F.put(sk.crown_points(c + Vector((0, 0, r * 0.8)), r * 0.82, 6, r * 0.9, r * 0.5), "metal_brass", False)
        F.put(sk.crown_points(c + Vector((0, 0, r * 0.84)), r * 0.5, 3, r * 0.5, r * 0.3, tilt=0.5), field("crown", 1.2))


def shoulder_face(B, F, size):
    """A second, smaller face rides at its shoulder and does the talking."""
    _second_face(F, F.sh(1) + Vector((0.06, -0.05, 0.19)), 0.064 * size)


def shoulder_face_crowned(B, F, size):
    """A dim crown sits over the second face, which has grown."""
    _second_face(F, F.sh(1) + Vector((0.05, -0.03, 0.3 * size)), 0.068 * size, crowned=True)


def head_ear(B, F, size):
    """One side of it is all ear."""
    c = F.hood_at(0.09, 0.0, 0.675)
    rings = [g.ring(c + X * off, r, r * 1.1, n=10, u=Y, v=Z) for off, r in ((0.0, 0.03), (0.06 * size, 0.07 * size), (0.14 * size, 0.15 * size), (0.2 * size, 0.24 * size))]
    F.put(g.loft(rings, caps=False), B.under)
    F.put(g.loft([g.ring(c + X * off, r, r * 1.1, n=10, u=Y, v=Z) for off, r in ((0.2 * size, 0.24 * size), (0.19 * size, 0.2 * size), (0.08 * size, 0.06 * size))], caps=False), "void")


def head_prow(B, F, size):
    """Its hood runs forward to a point, like the prow of something."""
    H = F.hood_at
    F.put(g.tongue([H(0, 0.02, 0.84), H(0, -0.12, 0.86), H(0, -0.26 * size, 0.8), H(0, -0.38 * size, 0.7)], [0.1, 0.12, 0.07, 0.006], thick=0.9, normal=Z), B.main)
    for s in (1, -1):
        F.put(g.tongue([H(s * 0.07, -0.05, 0.8), H(s * 0.12, 0.08, 0.86), H(s * 0.14, 0.24 * size, 0.9)], [0.07, 0.09, 0.01], thick=0.3, normal=(s, 0, 1)), B.under)


def holds_lamp(B, F, size, low=False):
    """A covered lamp in its lap."""
    robed = getattr(F, "robed", False)
    k = B.spec.get("build", {}).get("tall", 0.55) / 0.55 if robed else 1.0
    c = Vector((0, -0.23, 0.2 * k)) if robed else ((F.hand("l") + F.hand("r")) / 2 + Vector((0, -0.02, -0.03)) if "l" in F.hands and "r" in F.hands else Vector((0, -0.24, 0.42)))
    if low:
        # burned down beside it, and it has not noticed
        c = Vector((0.17, -0.33, 0.02)) if robed else c
        B.add(sk.disc(c, 0.07, thick=0.014, n=8), "metal_dark", False)
        B.add(sk.disc(c + Vector((0, 0, 0.012)), 0.05, thick=0.014, n=8), "wax")
        B.extend(sk.candle(c + Vector((0, 0, 0.02)), 0.04, 0.03, lit=0.5))
        return
    B.add(g.lathe([(0.02, 0.0), (0.045, 0.01), (0.045, 0.03)], n=6, centre=c), "metal_dark", False)
    B.add(g.lathe([(0.045, 0.06), (0.047, 0.075), (0.02, 0.1), (0.0, 0.11)], n=6, centre=c), "metal_dark", False)
    B.add(g.lathe([(0.036, 0.03), (0.036, 0.06)], n=6, centre=c, caps=False), field("core", 4.0))
    B.add(sk.arc(c + Vector((0, 0, 0.1)), 0.03, 0.035, 0.0, math.pi, 0.006, n=6, u=X, v=Z, sides=3), "metal_dark", False)


def holds_lamp_low(B, F, size):
    holds_lamp(B, F, size, low=True)


def holds_dark_lamp(B, F, size):
    """A lamp it carries and does not light."""
    wr = F.hand("r", (-0.26, -0.1, 0.28))
    B.extend(sk.lantern(wr + Vector((0, -0.02, -0.04)), 0.075 * size, lit=False))


def holds_glow(B, F, size):
    """A faint warm light under its hands, held where it can be seen."""
    if "l" in F.hands and "r" in F.hands:
        c = (F.hand("l") + F.hand("r")) / 2 + Vector((0, -0.03, 0.035))
    else:
        c = Vector((0, -0.3, 0.4))
    B.add(g.ico(c, 0.05 * size, sub=1), field("glow", 3.6))
    B.add(sk.hoop(c, 0.085 * size, 0.085 * size, 0.005, n=12, u=X, v=Z, sides=3), field("halo", 1.4))


def holds_book(B, F, size):
    """A thin dark book it never opens, held to its chest."""
    c = F.chest + Vector((0, -0.05, -0.01))
    F.puts(sk.book(c, 0.17 * size, rot=(-0.12, 0, 0)))
    F.put(g.tongue([c + Vector((0.03, -0.01, -0.08 * size)), c + Vector((0.035, -0.02, -0.14 * size)), c + Vector((0.03, -0.015, -0.2 * size))], [0.016, 0.016, 0.004], thick=0.3, normal=-Y), "cloth_rag")


def holds_chain(B, F, size):
    """A thin chain hangs between its two hands."""
    a, b = F.hand("l"), F.hand("r")
    B.add(sk.chain(sk.sag(a + Vector((0, -0.01, -0.02)), b + Vector((0, -0.01, -0.02)), 0.09 * size, n=8), link=0.017, n=13), "metal_iron_light", False)
    for p in (a, b):
        B.add(sk.chain([p + Vector((0, -0.01, -0.02)), p + Vector((0, -0.01, -0.1 * size))], link=0.017, n=2), "metal_iron_light", False)


def holds_blade(B, F, size):
    """A short dark blade, held in the other hand."""
    wr = F.hand("l")
    d = Vector((0.05, -1.0, -0.12)).normalized()
    B.add(g.tube([wr - d * 0.05, wr + d * 0.02], [0.012, 0.012], n=5), "leather_dark", False)
    B.add(g.box(wr + d * 0.025, (0.06, 0.012, 0.014)), "metal_iron", False)
    B.add(g.blade(wr + d * 0.03, wr + d * (0.03 + 0.22 * size), 0.045, thick=0.008, normal=Z, belly=0.25), "metal_dark", False)
    B.add(g.tube([wr + d * 0.04 + Vector((0.021, 0, 0)), wr + d * (0.03 + 0.2 * size)], [0.003, 0.002], n=3), field("edge", 2.6))


def back_chair(B, F, size):
    """The chair it has sat in all night: its back stands high behind."""
    _chair(B, F, back=0.36 + 0.62 * size, w=0.15)


def aura_veils(B, F, size):
    """The air in front of it stands thick and still."""
    w, h = getattr(F, "door", (0.22, 0.6))
    geo = None
    for i in range(5):
        x = (-0.8 + 0.4 * i) * w
        top = 0.1 + h * (0.92 if abs(i - 2) < 2 else 0.74)
        geo = g.merge(geo, g.tongue([(x, -0.03, top), (x + 0.01, -0.05, top * 0.55), (x, -0.04, 0.14)], [0.035, 0.05, 0.03], thick=0.12, normal=-Y))
    B.add(geo, "smoke")
    bend = None
    for s in (1, -1):
        b = Vector((s * (w + 0.12), -0.02, 0.16))
        bend = g.merge(bend, g.tongue([b, b + Vector((s * 0.02, 0, 0.2)), b + Vector((s * 0.12, 0, 0.36)), b + Vector((s * 0.26, 0, 0.42))], [0.03, 0.04, 0.03, 0.003], thick=0.3, normal=-Y))
    B.add(bend, "smoke")


def aura_breath(B, F, size):
    """Your breath shows when it is near."""
    c = F.P(F.hood_at(0, -0.17, 0.63))
    geo = None
    for i, (dy, dz, r) in enumerate(((0.0, 0.0, 0.016), (-0.06, 0.02, 0.022), (-0.13, 0.055, 0.03))):
        geo = g.merge(geo, sk.puff(c + Vector((0.012 * i, dy * size, dz * size)), r * size, k=2, seed=i))
    B.add(geo, "veil")


def aura_stubs(B, F, size):
    """The candles it has burned through."""
    for i, (x, y, h) in enumerate(((0.26, -0.2, 0.02), (0.3, -0.1, 0.035), (-0.27, -0.16, 0.025))):
        B.extend(sk.candle((x, y, 0.02), h, 0.022, lit=0.0))


STYLES = {
    ("legs", "stilts"): legs_stilts, ("legs", "back"): legs_back, ("legs", "roots"): legs_roots,
    ("ground", "long"): ground_long, ("ground", "cohort"): ground_cohort, ("ground", "ring"): ground_ring, ("ground", "wall"): ground_wall,
    ("wears", "mantle"): wears_mantle, ("wears", "collar"): wears_collar, ("wears", "script"): wears_script, ("wears", "cape"): wears_cape,
    ("wears", "shawl"): wears_shawl, ("wears", "rime"): wears_rime,
    ("chest", "maw"): chest_maw, ("chest", "cold-hand"): chest_cold_hand, ("chest", "core"): chest_core,
    ("face", "mask"): face_mask,
    ("shoulder", "face"): shoulder_face, ("shoulder", "face-crowned"): shoulder_face_crowned,
    ("head", "ear"): head_ear, ("head", "prow"): head_prow,
    ("holds", "lamp"): holds_lamp, ("holds", "lamp-low"): holds_lamp_low, ("holds", "dark-lamp"): holds_dark_lamp, ("holds", "glow"): holds_glow,
    ("holds", "book"): holds_book, ("holds", "chain"): holds_chain, ("holds", "blade"): holds_blade,
    ("back", "chair"): back_chair,
    ("aura", "veils"): aura_veils, ("aura", "breath"): aura_breath, ("aura", "stubs"): aura_stubs,
}
SLOTS = ("legs", "ground", "back", "wears", "chest", "face", "shoulder", "head", "holds", "aura")
# what each kind of thing can have: a door or a tree that inherits a mantle from its parent leaves it off
EVERY = set(SLOTS)
CAN = {"figure": EVERY, "hatch": EVERY - {"legs", "holds"}, "seated": {"ground", "back", "wears", "shoulder", "holds", "aura"}, "robed": {"ground", "back", "wears", "holds", "aura"},
       "door": {"ground", "aura"}, "gate": {"ground", "aura"}, "blot": set()}
# the plans whose hands are given where they are
FINAL_HANDS = ("seated", "robed", "door", "gate", "hatch", "human", "streak", "corner", "tree")


def build(form_id, level, spec, base):
    B = sk.Body(form_id, level, spec, base)
    plan = spec.get("plan", "blot" if level <= 1 else "figure")
    F = PLANS[plan](B, spec)
    F.final = plan in FINAL_HANDS
    for slot in SLOTS:
        for style, size in each(spec.get(slot)):
            fn = STYLES.get((slot, style))
            if fn is None:
                sk.log("no such style", slot, style, "on", form_id)
                continue
            if slot not in CAN.get(plan, {"ground", "aura"}):
                continue
            fn(B, F, size)
    B.export()
