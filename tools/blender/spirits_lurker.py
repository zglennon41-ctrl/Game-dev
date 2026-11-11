"""WILDLINE genius lines: the Lurker (docs/genius-lines.md, "The spirits").

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

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import field
import spirits_kit as sk
from spirits_kit import each, opt

PROF = [(0.87, 0.01, 0.01, 0.075), (0.82, 0.05, 0.06, 0.05), (0.75, 0.092, 0.105, 0.02), (0.67, 0.104, 0.118, 0.0), (0.6, 0.085, 0.09, 0.0),
        (0.555, 0.13, 0.098, 0.005), (0.5, 0.152, 0.1, 0.008), (0.41, 0.145, 0.092, 0.012), (0.3, 0.112, 0.075, 0.012), (0.2, 0.072, 0.052, 0.012)]
N = 16      # how many round a cloak

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
    "bar": ((0.13, -0.1, -0.06), (0.2, -0.2, -0.1), 1.15),
}
# the arms that hold nothing, and so hang loose and sway
SWAYS = ("hang", "broad", "long", "floor", "spread", "mantis", "reach")


def _stage(level):
    """The age of the figure by its place on the line."""
    return {1: {}, 2: {"tall": 0.86, "hood": 1.12, "broad": 0.95}, 3: {"tall": 1.0, "hood": 1.0, "broad": 1.0}}.get(level, {"tall": 1.08, "hood": 0.96, "broad": 1.06})


class Fig:
    """A hooded figure: where its parts are, and how it leans."""

    def __init__(self, B, bd, at=(0, 0)):
        self.B = B
        self.tall, self.broad, self.hood = bd.get("tall", 1.0), bd.get("broad", 1.0), bd.get("hood", 1.0)
        self.skirt, self.lean, self.hem = bd.get("skirt", 1.0), bd.get("lean", 0.0), bd.get("hem", 0.2)
        self.turn, self.reach, self.thick = bd.get("turn", 0.0), bd.get("reach", 1.0), bd.get("thick", 1.0)
        self.tatters, self.deep, self.side = bd.get("tatters", 1.0), bd.get("deep", 1.0), bd.get("side", 0.0)
        self.neck = self.hem + 0.4 * self.tall
        self.top = self.neck + 0.27 * self.hood
        self.zsh = self.hem + 0.31 * self.tall
        self.o = Vector((at[0], at[1], 0.0))     # where its hood stands, when it is only a hood
        self.hands = {}
        self.elbows = {}
        self.final = False        # its hands are given where they are (not on the upright figure)
        self.head = None          # its hood, where that is a piece of its own that looks about
        self.arm_mv = {}          # its arms, where they sway: what hangs from a hand rides one
        # the thread along its edges: a step of its Path's colour (the Unremarked's is the pale one)
        self.thread = "accent_" + str(B.spec.get("thread", "light"))

    def hand(self, tag, default=None):
        """Where a hand is, in the finished body."""
        if tag not in self.hands:
            return V(default) if default is not None else None
        return self.hands[tag] if self.final else self.P(self.hands[tag])

    def P(self, p):
        """A point of the upright figure, where the lean puts it."""
        p = V(p)
        return Vector((p.x + self.side * (p.z - self.hem), p.y - self.lean * (p.z - self.hem), p.z))

    def leant(self, geo):
        return sk.sheared(geo, self.lean, self.hem, self.side) if geo else geo

    def put(self, geo, material, smooth=None):
        self.B.add(self.leant(geo), material, smooth)

    def puts(self, items):
        for it in items:
            self.put(*it)

    def mv(self, kind, what, items, pivot, **kw):
        """A piece of the upright figure that the game moves (spirits_kit.Body.move), leant as the figure is."""
        return self.B.move(kind, what, [(self.leant(it[0]),) + tuple(it[1:]) for it in items if it and it[0]], self.P(pivot), **kw)

    def on_head(self, geo, material, smooth=None):
        """Something that rides its hood: it turns when the hood does."""
        if self.head is None:
            self.put(geo, material, smooth)
        elif geo and geo[0]:
            self.head["items"].append((self.leant(geo), material, smooth))

    def sh(self, s):
        return Vector((s * 0.165 * self.broad, 0.0, self.zsh))

    def hood_at(self, x, y, z):
        """A point given on the plain hood (its void is at z 0.672, its face at y -0.12), on this one."""
        p = Vector((self.o.x + x * self.hood, self.o.y + y * self.hood, self.neck + (z - 0.6) * self.hood))
        return sk.rotz(p, self.turn, (self.o.x, self.o.y)) if self.turn else p

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


def _row(F, z, rx, ry, yo):
    """A row of the plain profile, on this figure: the y of its middle, its height, its half-width, its half-depth."""
    if z > 0.6:
        return yo * F.hood, F.neck + (z - 0.6) * F.hood, rx * F.hood, ry * F.hood
    w = F.broad if z >= 0.38 else (F.skirt + (F.broad - F.skirt) * max(0.0, (z - 0.2) / 0.18))
    return yo, F.hem + (z - 0.2) * F.tall, rx * w, ry * (1.0 + (w - 1.0) * 0.5) * F.deep


def _front(F, z, x=0.0, out=0.0):
    """The front of the cloak at a height of the plain profile (0.2 the hem, 0.6 the neck) and an x:
    where a thing worn on it lies. Returns the point, and the cloak's half-width there."""
    rows = [r for r in PROF if r[0] <= 0.6]
    z = min(0.6, max(0.2, z))
    for hi, lo in zip(rows, rows[1:]):
        if lo[0] <= z <= hi[0]:
            t = (z - lo[0]) / (hi[0] - lo[0])
            a, b = _row(F, *lo), _row(F, *hi)
            y0, zz, rx, ry = [a[i] + (b[i] - a[i]) * t for i in range(4)]
            xx = max(-rx * 0.98, min(rx * 0.98, x))
            return Vector((xx, y0 - (ry + out) * math.sqrt(max(0.0, 1.0 - (xx / rx) ** 2)), zz)), rx
    return Vector((x, 0, F.hem)), 0.07


def lining(F, top=0.548, wide=0.62, m=5):
    """The cloak opens down its front and its lining is its Path's colour: narrow at the breast,
    wide at the hem, with a thread down each edge of it and one round the hem."""
    rows, left, right = [], [], []
    for i in range(7):
        z = top - (top - 0.2) * i / 6
        hw = _front(F, z)[1] * (0.07 + (wide - 0.07) * (i / 6.0) ** 0.85)
        outer = [_front(F, z, hw * (2.0 * j / (m - 1) - 1.0), out=0.006)[0] for j in range(m)]
        rows.append(outer + [p + Vector((0, 0.014, 0)) for p in reversed(outer)])
        left.append(outer[0] + Vector((0, -0.003, 0)))
        right.append(outer[-1] + Vector((0, -0.003, 0)))
    F.put(g.loft(rows), "accent", True)
    for edge in (left, right):
        F.put(g.tube(edge, 0.0055, n=5), F.thread, True)
    y, zz, rx, ry = _row(F, *PROF[-1])
    F.put(sk.hoop((0, y, zz + 0.004), rx + 0.004, ry + 0.004, 0.0065, n=N, sides=5), F.thread, True)


def cloak(F, n=N, lined=True):
    """Its cloak, from the neck to the hem, in folds; and its lining where it opens."""
    rings = []
    for row in [r for r in PROF if r[0] <= 0.6]:
        y, zz, rx, ry = _row(F, *row)
        rings.append(g.ring((0, y, zz), rx, ry, n=n, u=X, v=Y, phase=math.pi / n))
    a, b = _pleats(rings[::-1], n)
    F.put(a, F.B.main)
    F.put(b, F.B.under)
    if lined:
        lining(F)


def eyes_of(F, style, k=None):
    """The eyes in a hood, by their kind: (what stays open, what blinks), each [(geometry, material, smooth)]
    on the plain hood. Larger than they were, and lidded: a Lurker is known by its eyes."""
    if not style or style == "none":
        return [], []
    k = F.hood if k is None else k
    H = F.hood_at
    B = F.B
    nrm = sk.rotz(Vector((0, -1, 0.35)), F.turn)
    stat, blink = [], []
    if style == "slit":           # long, lit, a lid lowered over each: it is thinking
        eyes, lids = None, None
        for s in (1, -1):
            eyes = g.merge(eyes, g.ico(H(s * 0.037, -0.119, 0.68), 0.027 * k, sub=2, scale=(1.2, 0.36, 0.52), rot=(0, s * -0.28, F.turn)))
            lids = g.merge(lids, g.tongue([H(s * 0.004, -0.123, 0.691), H(s * 0.035, -0.13, 0.7), H(s * 0.07, -0.121, 0.709)], [0.005 * k, 0.014 * k, 0.004 * k], thick=0.5, normal=nrm))
        blink.append((eyes, field("eyes", 3.5), True))
        stat.append((lids, B.under, True))
    elif style == "dim":
        blink.append((sk.eye_pair(H(0, -0.12, 0.682), 0.032 * k, 0.017 * k, scale=(1.1, 0.4, 0.7), slant=0.0), field("eyes", 1.8), True))
    elif style == "old":          # old, patient, heavy in the lid, and they do not close for long
        eyes, lids = None, None
        for s in (1, -1):
            x = s * 0.037
            eyes = g.merge(eyes, g.ico(H(x, -0.12, 0.678), 0.027 * k, sub=2, scale=(1.05, 0.4, 0.88), rot=(0, 0, F.turn)))
            lids = g.merge(lids, g.tongue([H(x - 0.034, -0.125, 0.69), H(x, -0.136, 0.705), H(x + 0.034, -0.125, 0.687)], [0.008 * k, 0.024 * k, 0.008 * k], thick=0.5, normal=nrm))
            lids = g.merge(lids, g.tongue([H(x - 0.03, -0.124, 0.657), H(x, -0.13, 0.648), H(x + 0.03, -0.124, 0.657)], [0.005 * k, 0.012 * k, 0.005 * k], thick=0.5, normal=sk.rotz(Vector((0, -1, -0.35)), F.turn)))
        blink.append((eyes, field("eyes", 3.2), True))
        stat.append((lids, "mask_pale", True))
    elif style == "one":          # a single pale eye, open
        blink.append((g.ico(H(0, -0.116, 0.682), 0.056 * k, sub=2, scale=(1.25, 0.36, 0.86), rot=(0, 0, F.turn)), "mask_pale", True))
        blink.append((g.ico(H(0, -0.132, 0.682), 0.025 * k, sub=2, scale=(1.0, 0.5, 1.0), rot=(0, 0, F.turn)), field("eyes", 4.0), True))
        stat.append((g.tongue([H(-0.07, -0.124, 0.706), H(0, -0.14, 0.728), H(0.07, -0.124, 0.706)], [0.006 * k, 0.02 * k, 0.006 * k], thick=0.5, normal=nrm), B.under, True))
    elif style == "wide":         # set forward and wide, in two round rims: it reads
        eyes, rims = None, None
        u = sk.rotz(X, F.turn)
        for s in (1, -1):
            eyes = g.merge(eyes, g.ico(H(s * 0.041, -0.126, 0.688), 0.033 * k, sub=2, scale=(1.0, 0.35, 1.0), rot=(0, 0, F.turn)))
            rims = g.merge(rims, sk.hoop(H(s * 0.041, -0.133, 0.688), 0.038 * k, 0.038 * k, 0.006 * k, n=12, u=u, v=Z, sides=4))
        rims = g.merge(rims, g.tube([H(-0.008, -0.136, 0.694), H(0, -0.139, 0.7), H(0.008, -0.136, 0.694)], 0.0045 * k, n=4))
        blink.append((eyes, field("eyes", 4.0), True))
        stat.append((rims, "accent_pale", True))
    elif style == "holes":        # the black of a stair going down, and a long way down it a light
        holes, rims, lights = None, None, None
        u = sk.rotz(X, F.turn)
        for s in (1, -1):
            holes = g.merge(holes, g.ico(H(s * 0.037, -0.122, 0.682), 0.029 * k, sub=2, scale=(1.0, 0.4, 1.12), rot=(0, 0, F.turn)))
            rims = g.merge(rims, sk.hoop(H(s * 0.037, -0.128, 0.682), 0.034 * k, 0.038 * k, 0.0065 * k, n=12, u=u, v=Z, sides=4))
            lights = g.merge(lights, g.ico(H(s * 0.037, -0.134, 0.672), 0.007 * k, sub=1))
        blink.append((holes, "void", True))
        blink.append((lights, field("eyes", 3.0), True))
        stat.append((rims, F.thread, True))
    elif style == "single":       # one eye, low in the hood, and a lid on it
        blink.append((g.ico(H(0, -0.122, 0.678), 0.03 * k, sub=2, scale=(1.15, 0.4, 0.8), rot=(0, 0, F.turn)), field("eyes", 4.0), True))
        stat.append((g.tongue([H(-0.04, -0.124, 0.692), H(0, -0.136, 0.704), H(0.04, -0.124, 0.692)], [0.005 * k, 0.016 * k, 0.005 * k], thick=0.5, normal=nrm), B.under, True))
    elif style == "closed":
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.tongue([H(s * 0.012, -0.124, 0.682), H(s * 0.036, -0.128, 0.677), H(s * 0.062, -0.123, 0.684)], [0.004 * k, 0.012 * k, 0.004 * k], thick=0.5, normal=nrm))
        blink.append((geo, field("eyes", 2.2), True))
    return stat, blink


def hood(F, eyes="slit", cowl=True, void=True, watch=True, n=N):
    """Its hood and the face in it: the dark of it lined with its Path's colour, a thread round
    the opening, and its eyes. The hood is a piece of its own that looks slowly about (`watch`),
    and what is in it or on it rides it (Fig.on_head)."""
    B, H, k = F.B, F.hood_at, F.hood
    rings = []
    for z, rx, ry, yo in [r for r in PROF if r[0] >= 0.6]:
        y, zz, rx, ry = _row(F, z + 1e-6, rx, ry, yo)
        ring = g.ring((F.o.x, F.o.y + y, zz), rx, ry, n=n, u=X, v=Y, phase=math.pi / n)
        rings.append([sk.rotz(p, F.turn, (F.o.x, F.o.y)) for p in ring] if F.turn else ring)
    a, b = _pleats(rings[::-1], n)
    items = [(a, B.main, True), (b, B.under, True)]
    if void:
        items.append((g.ico(H(0, -0.079, 0.672), 0.087 * k, sub=2, scale=(0.96, 0.42, 1.16), rot=(0, 0, F.turn)), "accent", True))
        items.append((g.ico(H(0, -0.085, 0.672), 0.077 * k, sub=2, scale=(0.92, 0.43, 1.17), rot=(0, 0, F.turn)), "void", True))
        items.append((sk.hoop(H(0, -0.097, 0.672), 0.084 * k, 0.102 * k, 0.0065 * k, n=18, u=sk.rotz(X, F.turn), v=Z, sides=5), F.thread, True))
    stat, blink = eyes_of(F, eyes)
    items += stat
    if watch:
        F.head = F.mv("turn", "head", items, (F.o.x, F.o.y, F.neck))
    else:
        F.puts(items)
    if blink:
        F.mv("blink", "eyes", blink, H(0, -0.12, 0.682), parent=F.head)


def tatters(F, n=14, r=0.072, top=None, L=1.0, flare=1.0):
    """The hem: tatters hanging, each its own length, in four pieces that sway."""
    B = F.B
    if F.tatters <= 0.0:
        return
    z0 = (F.hem if top is None else top) + 0.012
    r = r * F.skirt
    groups = {}
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        d = Vector((math.cos(a), math.sin(a) * 0.72 * F.deep, 0))
        Li = (0.15 + 0.05 * ((i * 7) % 4)) * L * F.tatters
        drift = Vector((0.02 * math.sin(i * 1.7), 0.03, 0))
        pts = [d * r + Z * z0, d * (r * 1.2 * flare) + Z * (z0 - Li * 0.4), d * (r * (1.0 + 0.2 * (i % 2)) * flare) + Z * (z0 - Li * 0.75) + drift * 0.5,
               d * (r * (0.85 + 0.3 * (i % 2)) * flare) + Z * (z0 - Li) + drift]
        key = "front" if math.sin(a) < -0.5 else ("back" if math.sin(a) > 0.5 else ("l" if math.cos(a) > 0 else "r"))
        grp = groups.setdefault(key, [None, None])
        grp[i % 2] = g.merge(grp[i % 2], g.tongue(pts, [0.05 * F.skirt, 0.046 * F.skirt, 0.03 * F.skirt, 0.003], thick=0.3, normal=d))
    for key, (a, b) in groups.items():
        F.mv("sway", "hem_" + key, [(a, B.under, True), (b, B.main, True)], (0, 0, z0))


def hand_of(F, wr, d, k=1.0, hook=0.0, n=4, spread=0.016, r=0.0115):
    """A hand of the same dark, from a wrist and along d: a palm, long fingers of three joints
    that hook downward, and the nail of each in its Path's colour. [(geometry, material, smooth)]"""
    wr, d = V(wr), V(d).normalized()
    side = d.cross(Z)
    side = side.normalized() if side.length > 1e-5 else X.copy()
    down = Vector((0, 0, -1.0))
    palm = g.tube([wr - d * 0.01 * k, wr + d * 0.02 * k, wr + d * 0.045 * k], [0.02 * k, 0.027 * k, 0.022 * k], n=6, flat=0.6, up=side.cross(d))
    fingers, nails = None, None
    for j in range(n):
        o = j - (n - 1) / 2.0
        f = (d + side * (o * 0.16)).normalized()
        L = (1.0 - 0.12 * abs(o)) * k
        base = wr + d * 0.04 * k + side * (o * spread * k)
        p1 = base + f * 0.045 * L + down * hook * 0.008 * L
        p2 = base + f * 0.085 * L + down * hook * 0.04 * L
        p3 = base + f * 0.115 * L + down * hook * 0.09 * L
        fingers = g.merge(fingers, g.tube([base, p1, p2], [r * k, r * 0.86 * k, r * 0.62 * k], n=5))
        nails = g.merge(nails, g.tube([p2, p3], [r * 0.62 * k, r * 0.04 * k], n=5))
    return [(palm, F.B.under, True), (fingers, F.B.under, True), (nails, F.thread, True)]


def sleeve(F, sh, el, wr, w=1.0, cuff=True):
    """A sleeve from a shoulder by an elbow to a wrist, wider at the cuff, with a thread of its
    Path's colour round it. [(geometry, material, smooth)]"""
    sh, el, wr = V(sh), V(el), V(wr)
    items = [(g.tube([sh, (sh + el) * 0.5, el, (el + wr) * 0.5, wr], [0.052 * w, 0.048 * w, 0.043 * w, 0.045 * w, 0.052 * w], n=8), F.B.main, True)]
    if cuff:
        d = (wr - el).normalized()
        u, v = g._frame(d)
        items.append((sk.hoop(wr, 0.053 * w, 0.053 * w, 0.0065, n=10, u=u, v=v, sides=5), F.thread, True))
    return items


def limb(F, sh, el, wr, d=None, w=1.0, finger=1.0, hook=0.0, hand=True, fingers=4):
    """An arm where it is: its sleeve and its hand."""
    items = sleeve(F, sh, el, wr, w)
    if hand:
        items += hand_of(F, wr, d if d is not None else V(wr) - V(el), k=finger, hook=hook, n=fingers)
    return items


def arm(F, s, pose, hand=True, reach=None, width=None, finger=1.0, hook=0.0, sway=None):
    """One arm in a pose; returns its wrist (upright). One that holds nothing hangs loose and sways."""
    el_o, wr_o, w = POSES[pose]
    L = F.reach if reach is None else reach
    w = w * F.thick if width is None else width
    sh = F.sh(s)
    el = sh + Vector((s * el_o[0], el_o[1], el_o[2])) * L
    wr = sh + Vector((s * wr_o[0], wr_o[1], wr_o[2])) * L
    items = limb(F, sh, el, wr, w=w, finger=finger, hook=hook, hand=hand)
    tag = "l" if s > 0 else "r"
    if pose in SWAYS if sway is None else sway:
        F.arm_mv[tag] = F.mv("sway", "arm", items, sh, side=tag)
    else:
        F.puts(items)
    F.hands[tag], F.elbows[tag] = wr, el
    return wr


def arms(F, style, size=1.0):
    if not style or style == "none":
        return
    if style == "whisper":        # the left raised beside the hood, the right hanging
        sh = F.sh(1)
        el, wr = sh + Vector((0.04, -0.09, 0.02)), sh + Vector((-0.05, -0.15, 0.13))
        F.puts(limb(F, sh, el, wr, d=Vector((-0.3, -0.2, 1)), w=0.9, finger=0.7))
        F.hands["l"] = wr
        arm(F, -1, "hang")
    elif style == "blade":        # one forward, low; the other drawn back
        arm(F, 1, "reach", sway=False)
        arm(F, -1, "back", hand=False)
    elif style == "floor":        # longer than it is tall: they hang below its hem
        for s in (1, -1):
            arm(F, s, "floor", reach=size * F.reach, finger=1.5, hook=0.5)
    elif style == "wings":        # swept back and out, and held there like wings
        for s in (1, -1):
            el_o, wr_o, w = POSES["wings"]
            sh = F.sh(s)
            el, wr = sh + Vector((s * el_o[0], el_o[1], el_o[2])) * F.reach, sh + Vector((s * wr_o[0], wr_o[1], wr_o[2])) * F.reach
            F.arm_mv["l" if s > 0 else "r"] = F.mv("glide", "arm", limb(F, sh, el, wr, w=w * F.thick), sh, side="l" if s > 0 else "r")
            F.hands["l" if s > 0 else "r"], F.elbows["l" if s > 0 else "r"] = wr, el
    else:
        for s in (1, -1):
            arm(F, s, style, hook=0.7 if style in ("mantis", "reach") else 0.25, finger=1.3 if style in ("long", "reach") else 1.0)


def wisps(F, k=1.0):
    """The dark coming off its shoulders: it sways."""
    geo = None
    for sgn, y in ((1, 0.03), (-1, 0.05), (1, 0.08)):
        b = Vector((sgn * 0.13 * F.broad, y, F.zsh + 0.03))
        geo = g.merge(geo, sk.strand(sk.curve([b, b + Vector((sgn * 0.035, 0.03, 0.07)) * k, b + Vector((sgn * 0.005, 0.07, 0.13)) * k, b + Vector((sgn * 0.03, 0.09, 0.2)) * k], n=3), 0.034, n=5, swell=0.3))
    F.mv("sway", "wisps", [(geo, F.B.under, True)], (0, 0.05, F.zsh))


# --- plans: what kind of thing it is ---------------------------------------------------------

def _spread(vals, m):
    """A short list of values drawn out over m of them."""
    out = []
    for i in range(m):
        t = i * (len(vals) - 1) / max(1, m - 1)
        j = min(len(vals) - 2, int(t))
        out.append(vals[j] + (vals[j + 1] - vals[j]) * (t - j))
    return out


def hangs(B, at, L=0.1, w=0.055, what="under"):
    """Shreds of the same dark hanging under a piece of ground it carries, so that the ground
    reads as carried and not as left in the air. They sway."""
    geo = [None, None]
    mid = Vector((0, 0, 0))
    for i, p in enumerate(at):
        p = V(p)
        mid += p / len(at)
        Li = L * (0.7 + 0.3 * ((i * 5) % 3))
        geo[i % 2] = g.merge(geo[i % 2], sk.strand([p, p + Vector((0.012, 0.01, -Li * 0.5)), p + Vector((-0.012 + 0.024 * (i % 2), 0.02, -Li))], w, n=5, swell=0.25))
    B.move("sway", what, [(geo[0], B.main, True), (geo[1], B.under, True)], mid)


def plan_blot(B, spec):
    """The Starter: a shadow at your heel that is not yours, a little darker where the eyes would be."""
    F = Fig(B, {"hem": 0.2})
    B.add(g.ico((0, 0, 0.4), 0.15, sub=2, scale=(1.0, 0.92, 1.0)), B.under)
    B.add(g.ico((0, 0.02, 0.5), 0.1, sub=2, scale=(1.0, 0.95, 0.85)), B.under)
    # the peak a hood will grow from, and the tail of it
    B.add(g.tube(sk.curve([(0, 0.03, 0.56), (0.0, 0.06, 0.63), (0.025, 0.1, 0.67), (0.05, 0.11, 0.66)], n=3), [0.06, 0.055, 0.047, 0.04, 0.033, 0.026, 0.018, 0.012, 0.007, 0.003], n=7), B.under, True)
    B.move("sway", "tail", [(g.tongue([(0, 0.04, 0.34), (0.05, 0.16, 0.25), (-0.03, 0.24, 0.16), (0.03, 0.27, 0.06)], [0.22, 0.14, 0.07, 0.005], thick=0.7), B.main, True)], (0, 0.04, 0.34))
    # a little darker where the eyes would be, and the eyes: soft, lidded, awake
    B.add(sk.eye_pair((0, -0.118, 0.42), 0.057, 0.05, scale=(1.0, 0.4, 1.15), slant=0.0), B.main)
    eyes, lids = None, None
    for s in (1, -1):
        eyes = g.merge(eyes, g.ico((s * 0.057, -0.139, 0.422), 0.021, sub=2, scale=(1.0, 0.5, 1.05)))
        lids = g.merge(lids, g.tongue([(s * 0.026, -0.14, 0.44), (s * 0.057, -0.152, 0.447), (s * 0.088, -0.138, 0.436)], [0.006, 0.02, 0.006], thick=0.5, normal=(0, -1, 0.4)))
    B.move("blink", "eyes", [(eyes, field("eyes", 2.4), True)], (0, -0.139, 0.422))
    B.add(lids, B.under, True)
    drips = None
    for i, (x, L) in enumerate(((-0.09, 0.1), (0.0, 0.15), (0.09, 0.08))):
        drips = g.merge(drips, sk.strand([(x, -0.03, 0.31), (x * 1.1, -0.03, 0.3 - L * 0.5), (x * 1.2, -0.02, 0.3 - L)], 0.075, n=6, swell=0.2))
    B.move("sway", "drips", [(drips, B.main, True)], (0, -0.03, 0.31))
    # the one flag of the floor it keeps to, and on it the shadow it throws: the wrong way for the lamp
    B.add(sk.disc((0.0, -0.02, 0.0), 0.25, thick=0.028, n=6, squash=0.8), "stone_flag", False)
    B.add(g.tongue([(0.05, 0.0, 0.03), (-0.06, -0.05, 0.03), (-0.2, -0.08, 0.03)], [0.2, 0.2, 0.03], thick=0.1, normal=Z), B.main)
    F.top, F.zsh, F.neck = 0.55, 0.36, 0.42
    B.frame(0.55, front=-0.13, mid=0.36, half=0.15)
    return F


def plan_figure(B, spec):
    bd = dict(_stage(B.level))
    bd.update(spec.get("build", {}))
    F = Fig(B, bd)
    cloak(F)
    style, _ = opt(spec.get("eyes", "slit"))
    hood(F, style if not spec.get("face") else "none", watch=bd.get("watch", 1.0) > 0)
    legs, _ = opt(spec.get("legs"))
    if legs != "roots":
        tatters(F, L=0.6 if legs else (0.78 if spec.get("ground") else 1.0))
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


def _chair(B, back=0.92, w=0.13, seat=0.34):
    """A chair of grey wood: four legs, a seat, a ladder back, and its brass in its Path's colour."""
    legs = None
    for x in (w, -w):
        for y in (0.1, -0.12):
            legs = g.merge(legs, g.box((x, y, seat - 0.14), (0.03, 0.03, 0.26)))
    B.add(legs, "wood_grey", False)
    B.add(g.box((0, -0.01, seat), (2 * w + 0.05, 0.28, 0.03)), "wood_grey_pale", False)
    ladder = None
    for x in (w, -w):
        ladder = g.merge(ladder, g.box((x, 0.115, (seat + back) / 2), (0.03, 0.03, back - seat), rot=(-0.06, 0, 0)))
    for i in range(3):
        z = seat + 0.16 + i * (back - seat - 0.22) / 2
        ladder = g.merge(ladder, g.box((0, 0.118 + 0.01 * i, z), (2 * w, 0.02, 0.05)))
    B.add(ladder, "wood_grey", False)
    knobs = None
    for x in (w, -w):
        knobs = g.merge(knobs, g.ico((x, 0.14, back + 0.018), 0.026, sub=1))
    B.add(knobs, "accent_light", True)


def rug(B, c, w, d):
    """The rug a chair stands on, in its Path's colour, bordered and fringed: the ground it carries."""
    c = V(c)
    B.add(g.box(c + Vector((0, 0, -0.012)), (w, d, 0.022)), "accent_dark", False)
    B.add(g.box(c + Vector((0, 0, -0.009)), (w * 0.78, d * 0.8, 0.022)), "accent", False)
    line, fringe = None, None
    for s in (1, -1):
        line = g.merge(line, g.box(c + Vector((s * w * 0.31, 0, -0.005)), (0.012, d * 0.64, 0.02)), g.box(c + Vector((0, s * d * 0.32, -0.005)), (w * 0.62, 0.012, 0.02)))
        for i in range(7):
            x = -w * 0.45 + w * 0.9 * i / 6
            fringe = g.merge(fringe, g.tongue([c + Vector((x, s * d * 0.5, -0.008)), c + Vector((x + 0.006, s * (d * 0.5 + 0.045), -0.014))], [0.03, 0.006], thick=0.3, normal=Z))
    B.add(line, "accent_light", False)
    B.add(fringe, "accent_pale", True)


def stick(B, at, h=0.2, lit=1.0, what="flame"):
    """A candle in a stick, in its Path's colour: the light it sits by. Its flame gutters."""
    at = V(at)
    B.add(g.lathe([(0.05, 0.0), (0.045, 0.012), (0.012, 0.03), (0.012, h * 0.5), (0.03, h * 0.56), (0.012, h * 0.62)], n=8, centre=at), "accent_light", False)
    top = at + Z * (h * 0.6)
    B.add(g.lathe([(0.016, 0.0), (0.017, h * 0.42), (0.011, h * 0.5)], n=7, centre=top), "accent_pale", True)
    B.add(g.tube([top + Z * (h * 0.5), top + Z * (h * 0.5 + 0.012)], 0.003, n=3), "metal_dark", False)
    if lit > 0:
        t = top + Z * (h * 0.5 + 0.006)
        B.move("flick", what, [(g.tongue([t, t + Vector((0.006, 0, 0.022 * lit)), t + Vector((0, 0, 0.065 * lit))], [0.018, 0.026, 0.002], thick=0.7, normal=Y), field("flame", 3.0), True)], t)


def plan_seated(B, spec):
    """Someone sitting forward in a chair, on the rug the chair stands on, a candle beside it."""
    bd = {"tall": 0.62, "hem": 0.36, "lean": 0.5, "hood": 1.08, "broad": 0.95, "tatters": 0.0}
    bd.update(spec.get("build", {}))
    F = Fig(B, bd)
    cloak(F)
    style, _ = opt(spec.get("eyes", "slit"))
    hood(F, style)
    # the lap, the shins, and the lining that hangs between its knees
    for s in (1, -1):
        hip, knee, foot = Vector((s * 0.07, 0.0, 0.39)), Vector((s * 0.095, -0.21, 0.4)), Vector((s * 0.09, -0.22, 0.13))
        B.add(g.tube([hip, knee], [0.062, 0.052], n=8), B.main, True)
        B.add(g.tube([knee + Vector((0, 0.01, 0.02)), (knee + foot) * 0.5 + Vector((0, -0.012, 0)), foot], [0.05, 0.042, 0.032], n=8), B.main, True)
        B.add(g.tongue([foot + Vector((0, 0.03, 0)), foot + Vector((0, -0.07, -0.03))], [0.06, 0.02], thick=0.5, normal=Z), B.under)
    B.add(g.tongue([(0, -0.2, 0.38), (0, -0.22, 0.24), (0.01, -0.21, 0.12)], [0.15, 0.11, 0.01], thick=0.2, normal=-Y), "accent", True)
    # forearms on the knees
    for s in (1, -1):
        sh = F.P(F.sh(s))
        el, wr = Vector((s * 0.15, sh.y - 0.07, 0.5)), Vector((s * 0.085, -0.22, 0.425))
        B.extend(limb(F, sh, el, wr, d=Vector((-s * 0.4, -0.5, -0.6)), w=0.9, finger=0.75, hook=0.3))
        F.hands["l" if s > 0 else "r"] = wr
    _chair(B, back=0.36 + 0.6 * bd.get("chair", 1.0))
    rug(B, (0, -0.07, 0.07), 0.6, 0.64)
    stick(B, (0.24, -0.27, 0.07), 0.22)
    hangs(B, [(-0.2, 0.15, 0.045), (0.2, 0.12, 0.045), (0.0, -0.25, 0.045), (-0.18, -0.2, 0.045)], L=0.09)
    top = F.P(Vector((0, 0, F.top))).z
    B.frame(top, front=-0.26, mid=0.5, half=0.17)
    B.socket("socket_eyes", F.P(F.hood_at(0, -0.128, 0.682)))
    B.socket("socket_head", F.P(Vector((0, 0.04, F.top))))
    F.seated = True
    return F


def _hood_only(B, c, k=1.0, eyes="slit", lean=0.0, turn=0.0, watch=True):
    """Just the hood and what is in it, its neck at c, bent forward by `lean`."""
    c = V(c)
    F = Fig(B, {"hem": c.z - 0.4, "tall": 1.0, "hood": k, "lean": lean, "turn": turn}, at=(c.x, c.y + 0.4 * lean))
    hood(F, eyes, watch=watch)
    return F


def plan_robed(B, spec):
    """Gone down on its heels, the robe pooled round it, its head bent."""
    bd = {"tall": 0.55, "hood": 1.0, "wide": 1.0, "bent": 0.1}
    bd.update(spec.get("build", {}))
    k, wide = bd["tall"] / 0.55, bd["wide"]
    main, under = B.main, B.under
    F = Fig(B, {"hem": 0.2, "tall": 1.0, "hood": bd["hood"]})
    B.add(g.lathe([(0.3 * wide, 0.0), (0.27 * wide, 0.03), (0.2, 0.12 * k), (0.16, 0.26 * k), (0.15, 0.36 * k), (0.1, 0.44 * k), (0.0, 0.46 * k)], n=18), main)
    hem = None
    for i in range(14):
        a = 2 * math.pi * i / 14
        hem = g.merge(hem, g.blade((0.22 * wide * math.cos(a), 0.22 * wide * math.sin(a), 0.05), (0.38 * wide * math.cos(a + 0.2), 0.38 * wide * math.sin(a + 0.2), 0.0), 0.13 * wide, normal=(0, 0, 1), belly=0.4))
    B.add(hem, B.mark("hem", under))
    B.add(sk.hoop((0, 0, 0.036), 0.272 * wide, 0.272 * wide, 0.007, n=18, sides=5), F.thread, True)
    # the robe opens down its front on its lining
    B.add(g.tongue([(0, -0.1, 0.43 * k), (0, -0.162, 0.3 * k), (0, -0.2, 0.13 * k), (0, -0.27 * wide, 0.04)], [0.03, 0.06, 0.1, 0.15], thick=0.22, normal=-Y), "accent", True)
    hz = 0.52 * k
    hy = -0.01 - bd["bent"]
    style, _ = opt(spec.get("eyes", "single"))
    Fh = _hood_only(B, (0, hy + 0.045, hz - 0.085), bd["hood"] * 0.98, style, lean=0.28 + 2.0 * bd["bent"], turn=bd.get("turn", 0.0), watch=bd.get("watch", 1.0) > 0)
    F.head = Fh.head
    F.neck, F.top, F.zsh = hz - 0.085, hz - 0.085 + 0.27 * bd["hood"], 0.36 * k
    F.eye_c = Fh.P(Fh.hood_at(0, -0.125, 0.682))
    # the arms: to the lap, or held out
    pose, _ = opt(spec.get("arms", "lap"))
    for s in (1, -1):
        sh = Vector((s * 0.15, -0.02, 0.36 * k))
        if pose == "cup":
            el, wr = Vector((s * 0.17, -0.2, 0.3 * k)), Vector((s * 0.05, -0.34, 0.3 * k))
        else:
            el, wr = Vector((s * 0.17, -0.16, 0.24 * k)), Vector((s * 0.06, -0.22, 0.2 * k))
        B.extend(limb(F, sh, el, wr, d=Vector((-s * 0.5, -0.6, 0.15 if pose == "cup" else -0.3)), w=0.85, finger=0.7, hook=-0.35 if pose == "cup" else 0.2))
        F.hands["l" if s > 0 else "r"] = wr
    B.ground = False
    B.frame(F.top, front=-0.2, mid=0.36 * k, half=0.2)
    B.socket("socket_eyes", F.eye_c + Vector((0, -0.01, 0)))
    B.socket("socket_light", (0, -0.23, 0.245 * k))
    F.robed = True
    return F


def plan_door(B, spec):
    """It stands in a doorway in the shape of a door. The frame and the step are a doorway's, grey;
    the leaf is itself, all rails and no panels; and the light of the room it keeps shows under
    it and at the keyhole."""
    bd = {"tall": 1.0, "wide": 1.0}
    bd.update(spec.get("build", {}))
    h, w = 0.66 * bd["tall"], 0.21 * bd["wide"]
    main, under = B.main, B.under
    z0 = 0.09
    # the doorway: two posts, a lintel, a step
    B.add(g.merge(g.box((w + 0.055, 0.01, z0 + h / 2), (0.06, 0.1, h)), g.box((-(w + 0.055), 0.01, z0 + h / 2), (0.06, 0.1, h))), "wood_grey", False)
    B.add(g.box((0, 0.01, z0 + h + 0.03), (2 * w + 0.24, 0.12, 0.06)), "wood_grey_pale", False)
    B.extend(sk.flags((0, -0.03, z0), 2 * w + 0.32, 0.28, nx=2, ny=1, thick=0.045, names=("stone_step", "stone_flag_pale")))
    # the leaf
    zs = z0 + h * 0.58          # its shoulders: the rail its hood stands on
    leaf = g.merge(g.box((w - 0.03, 0, (z0 + zs) / 2), (0.05, 0.034, zs - z0)), g.box((-(w - 0.03), 0, (z0 + zs) / 2), (0.05, 0.034, zs - z0)), g.box((0, 0, zs), (2 * w - 0.01, 0.036, 0.055)))
    B.add(leaf, main, False)
    rails = g.merge(g.box((0, 0, z0 + 0.05), (2 * w - 0.1, 0.024, 0.05)), g.box((0, 0, z0 + h * 0.3), (2 * w - 0.1, 0.024, 0.04)), g.box((0, 0, (z0 + 0.05 + zs) / 2), (0.034, 0.024, zs - z0 - 0.06)))
    B.add(rails, under, False)
    th = None
    for s in (1, -1):
        th = g.merge(th, g.tube([(s * (w - 0.006), -0.02, z0 + 0.03), (s * (w - 0.006), -0.02, zs + 0.03)], 0.0055, n=4))
    th = g.merge(th, g.tube([(-(w - 0.006), -0.02, zs + 0.03), (w - 0.006, -0.02, zs + 0.03)], 0.0055, n=4))
    style, _ = opt(spec.get("eyes", "slit"))
    F = _hood_only(B, (0, 0, zs), 0.8 * min(1.0, bd["wide"]), style)
    B.add(th, F.thread, True)
    # the light of the room behind it: under the door, and at the keyhole
    B.add(g.box((0, -0.004, z0 + 0.013), (2 * w - 0.1, 0.016, 0.012)), field("door", 2.6), False)
    lock = Vector((-(w - 0.03), -0.019, z0 + h * 0.3))
    B.add(g.box(lock, (0.034, 0.008, 0.07)), "accent_light", False)
    B.add(g.merge(g.ico(lock + Vector((0, -0.005, 0.01)), 0.008, sub=1, scale=(1, 0.5, 1)), g.box(lock + Vector((0, -0.005, -0.008)), (0.006, 0.006, 0.022))), field("door", 2.6), False)
    # its hands on the posts, from behind
    for s in (1, -1):
        wr = Vector((s * (w + 0.1), 0.05, z0 + h * 0.52))
        B.extend(hand_of(F, wr, Vector((-s, -0.75, 0)), k=0.72, hook=0.25))
        F.hands["l" if s > 0 else "r"] = wr
    hangs(B, [(x * w, 0.0, z0 - 0.05) for x in (-0.9, -0.3, 0.35, 0.9)], L=0.11)
    F.door = (w, h)
    F.top = z0 + h + 0.06
    B.frame(F.top, front=-0.08, mid=z0 + h * 0.6, half=w + 0.05)
    B.socket("socket_eyes", F.P(F.hood_at(0, -0.128, 0.682)))
    return F


def plan_hatch(B, spec):
    """It comes up out of a hatch in a flagged floor, its hands on the rim, the lid thrown back,
    and the light of the cellar coming up round it."""
    main = B.main
    w, zf = 0.26, 0.13
    slabs = [None, None]
    for s in (1, -1):
        slabs[0 if s > 0 else 1] = g.merge(slabs[0 if s > 0 else 1], g.box((s * (w + 0.135), -0.02, zf - 0.022), (0.2, 2 * w + 0.47, 0.044)))
        slabs[1 if s > 0 else 0] = g.merge(slabs[1 if s > 0 else 0], g.box((0, -0.02 + s * (w + 0.135), zf - 0.02 - 0.003 * s), (2 * w + 0.06, 0.2, 0.044)))
    B.add(slabs[0], "stone_flag", False)
    B.add(slabs[1], "stone_flag_pale", False)
    rim, glow = None, None
    for s in (1, -1):
        rim = g.merge(rim, g.box((s * w, -0.02, zf + 0.012), (0.06, 2 * w + 0.06, 0.05)), g.box((0, -0.02 + s * w, zf + 0.012), (2 * w + 0.06, 0.06, 0.05)))
        glow = g.merge(glow, g.box((s * (w - 0.036), -0.02, zf - 0.012), (0.012, 2 * w - 0.07, 0.012)), g.box((0, -0.02 + s * (w - 0.036), zf - 0.012), (2 * w - 0.07, 0.012, 0.012)))
    B.add(rim, "wood_grey", False)
    B.add(glow, field("cellar", 2.2), False)
    B.add(g.box((0, -0.02, zf - 0.03), (2 * w, 2 * w, 0.02)), "void", False)
    steps = None
    for i in range(3):
        steps = g.merge(steps, g.box((0.1, -0.2 + 0.11 * i, zf - 0.012 * (i + 1)), (0.22, 0.09, 0.012)))
    B.add(steps, "stone_step", False)
    # the lid, thrown back
    lid = Vector((0, w + 0.11, zf + 0.21))
    for geo, name in sk.planks((0, 0, 0), 2 * w - 0.02, 2 * w - 0.06, n=4, thick=0.03)[:2]:
        B.add(sk.shifted(sk.tilted(geo, rx=math.pi / 2 - 0.35), lid), name, False)
    straps = g.merge(g.box((-0.14, 0, 0.004), (0.03, 2 * w - 0.08, 0.012)), g.box((0.14, 0, 0.004), (0.03, 2 * w - 0.08, 0.012)))
    B.add(sk.shifted(sk.tilted(straps, rx=math.pi / 2 - 0.35), lid), "metal_iron", False)
    B.add(sk.arc(lid + Vector((0, -0.03, 0.02)), 0.05, 0.05, 0.0, math.pi, 0.011, n=6, u=X, v=Z, sides=4), "accent_light", False)
    bd = {"tall": 0.62, "hem": 0.12, "broad": 1.3, "hood": 1.05, "lean": 0.1, "skirt": 1.6}
    bd.update(spec.get("build", {}))
    F = Fig(B, bd)
    cloak(F)
    style, _ = opt(spec.get("eyes", "holes"))
    hood(F, style)
    for s in (1, -1):
        sh = F.P(F.sh(s))
        el, wr = Vector((s * 0.3, -0.08, 0.3)), Vector((s * 0.2, -0.26, zf + 0.06))
        items = limb(F, sh, el, wr, d=Vector((-s * 0.1, -1, -0.25)), w=1.15, finger=0.95, hook=0.5)
        items[-2] = (items[-2][0], "brick_dust", True)       # brick dust on what would be its fingers
        B.extend(items)
        F.hands["l" if s > 0 else "r"] = wr
    wisps(F)
    hangs(B, [(-0.3, -0.25, zf - 0.045), (0.32, -0.2, zf - 0.045), (0.3, 0.26, zf - 0.045), (-0.32, 0.2, zf - 0.045), (0.0, 0.0, zf - 0.04)], L=0.12)
    top = F.P(Vector((0, 0, F.top))).z
    B.frame(top, front=-0.14, mid=0.4, half=0.28)
    B.socket("socket_eyes", F.P(F.hood_at(0, -0.128, 0.682)))
    return F


def plan_human(B, spec):
    """It has your outline: a person of shadow with a hollow where the breast is, and a small
    light in the hollow. Its own face is two eyes; a second, faint face looks back over its shoulder."""
    main, under = B.main, B.under
    k = spec.get("build", {}).get("tall", 1.0)
    z = lambda v: v * k  # noqa: E731
    F = Fig(B, {"hem": 0.0, "tall": 1.0})
    th = F.thread
    # the trunk is a frame round the hollow: two flanks, the shoulders, the hips
    for s in (1, -1):
        B.add(g.tube([(s * 0.07, 0, z(0.42)), (s * 0.108, 0, z(0.5)), (s * 0.112, 0, z(0.62)), (s * 0.128, 0, z(0.72)), (s * 0.11, 0, z(0.78))], [0.05, 0.043, 0.04, 0.045, 0.05], n=8, flat=1.3), main, True)
    B.add(g.tube([(-0.155, 0, z(0.755)), (-0.08, 0, z(0.785)), (0.08, 0, z(0.785)), (0.155, 0, z(0.755))], [0.048, 0.056, 0.056, 0.048], n=8, flat=1.15), main, True)
    B.add(g.tube([(-0.095, 0, z(0.43)), (0, 0, z(0.415)), (0.095, 0, z(0.43))], [0.062, 0.068, 0.062], n=8, flat=1.1), main, True)
    c = Vector((0, 0, z(0.61)))
    rx, rz = 0.078, 0.125 * k
    wall = [g.ring(c + Y * y, rx + o, rz + o, n=16, u=X, v=Z) for y, o in ((-0.045, 0.014), (0.045, 0.014), (0.045, 0.0), (-0.045, 0.0), (-0.045, 0.014))]
    B.add(g.loft(wall, caps=False), "accent", True)
    B.add(sk.hoop(c + Y * -0.05, rx + 0.008, rz + 0.008, 0.007, n=18, u=X, v=Z, sides=5), th, True)
    B.move("pulse", "heart", [(g.ico(c + Z * 0.01, 0.036, sub=2, scale=(1, 0.8, 1.25)), field("heart", 3.2), True)], c + Z * 0.01)
    # the neck, the head, and its own eyes
    B.add(g.tube([(0, 0, z(0.79)), (0, 0, z(0.85))], [0.045, 0.04], n=8), main, True)
    hc = Vector((0, 0, z(0.925)))
    B.add(g.ico(hc, 0.094, sub=2, scale=(0.95, 1.0, 1.12)), main)
    B.move("blink", "eyes", [(sk.eye_pair(hc + Vector((0, -0.088, 0.01)), 0.034, 0.024, scale=(1.2, 0.4, 0.5), slant=0.25), field("eyes", 3.4), True)], hc + Vector((0, -0.088, 0.01)))
    # the second face: faint, pale, its eyes shut, looking back over the shoulder
    c2 = hc + Vector((-0.07, 0.03, -0.004))
    face = g.merge(g.ico(c2, 0.07, sub=2, scale=(0.36, 0.84, 1.12)),
                   g.tongue([c2 + Vector((-0.024, 0, 0.022)), c2 + Vector((-0.04, 0, -0.004)), c2 + Vector((-0.022, 0, -0.024))], [0.012, 0.024, 0.008], thick=0.7, normal=Y))
    B.add(face, "mask_pale", True)
    shut = None
    for s in (1, -1):
        shut = g.merge(shut, g.tongue([c2 + Vector((-0.023, s * 0.012, 0.022)), c2 + Vector((-0.024, s * 0.028, 0.018)), c2 + Vector((-0.016, s * 0.044, 0.024))], [0.003, 0.009, 0.003], thick=0.5, normal=-X))
    B.add(shut, field("eyes", 1.6), True)
    B.add(g.box(c2 + Vector((-0.021, 0, -0.045)), (0.006, 0.03, 0.005)), "void", False)
    # arms and legs, a thread of its Path's colour down the outside of each
    for s in (1, -1):
        tag = "l" if s > 0 else "r"
        pts = [Vector((s * 0.165, 0, z(0.75))), Vector((s * 0.21, -0.01, z(0.58))), Vector((s * 0.235, -0.05, z(0.42)))]
        rr = [0.048, 0.04, 0.03]
        items = [(g.tube(pts, rr, n=8), under, True), (g.tube([p + Vector((s * (r + 0.002), 0, 0)) for p, r in zip(pts, rr)], 0.005, n=4), th, True)]
        items += hand_of(F, pts[2], Vector((s * 0.1, -0.2, -1)), k=0.8, hook=0.0)
        B.move("sway", "arm", items, pts[0], side=tag)
        F.hands[tag] = pts[2]
        leg = [Vector((s * 0.07, 0, z(0.43))), Vector((s * 0.085, -0.01, z(0.22))), Vector((s * 0.08, 0.0, z(0.04)))]
        lr = [0.062, 0.05, 0.035]
        B.add(g.tube(leg, lr, n=8), under, True)
        B.add(g.tube([p + Vector((s * (r + 0.002), 0, 0)) for p, r in zip(leg, lr)], 0.005, n=4), th, True)
        B.add(g.tongue([(s * 0.08, 0.03, z(0.03)), (s * 0.085, -0.09, 0.0)], [0.07, 0.025], thick=0.5, normal=Z), main)
    F.top, F.zsh, F.neck = z(1.02), z(0.75), z(0.8)
    B.frame(F.top, front=-0.12, mid=z(0.6), half=0.2)
    B.socket("socket_eyes", (0, -0.11, z(0.94)))
    return F


def plan_streak(B, spec):
    """It goes along with what was sent: a figure thrown forward beside an arrow in its flight,
    its hands out ahead of it and the rest of it streaming."""
    main, under = B.main, B.under
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    spine = [Vector((0.0, -0.3, 0.5)), Vector((0.0, -0.12, 0.56)), Vector((0.0, 0.12, 0.55)), Vector((0.02, 0.4, 0.5)), Vector((-0.02, 0.72, 0.43)), Vector((0.02, 1.0, 0.38))]
    pts = sk.curve(spine, n=3)
    rr = _spread([0.085, 0.12, 0.125, 0.09, 0.05, 0.004], len(pts))
    B.add(g.tube(pts, rr, n=10), main, True)
    B.add(g.tube([p + Z * (r + 0.001) for p, r in zip(pts[2:13], rr[2:13])], 0.006, n=4), F.thread, True)       # a thread along its back
    # the hood, low and forward
    hc = Vector((0, -0.3, 0.5))
    B.add(g.ico(hc, 0.1, sub=2, scale=(0.95, 1.25, 0.86)), main)
    fc = Vector((0, -0.375, 0.478))
    B.add(g.ico(fc + Vector((0, 0.03, 0.004)), 0.082, sub=2, scale=(0.95, 0.5, 0.8)), "accent", True)
    B.add(g.ico(fc + Vector((0, 0.022, 0.002)), 0.072, sub=2, scale=(0.92, 0.5, 0.78)), "void", True)
    B.add(sk.hoop(fc + Vector((0, 0.004, 0)), 0.073, 0.06, 0.006, n=16, u=X, v=Vector((0, -0.3, 0.95)).normalized(), sides=5), F.thread, True)
    e = fc + Vector((0, -0.016, 0.004))
    B.move("blink", "eyes", [(sk.eye_pair(e, 0.03, 0.024, scale=(1.2, 0.45, 0.55), slant=0.28), field("eyes", 3.8), True)], e)
    for s in (1, -1):
        sh, el, wr = Vector((s * 0.1, -0.1, 0.52)), Vector((s * 0.17, -0.34, 0.47)), Vector((s * 0.11, -0.6, 0.44))
        B.extend(limb(F, sh, el, wr, d=Vector((-s * 0.1, -1, -0.12)), w=0.95, finger=1.25, hook=0.7))
        F.hands["l" if s > 0 else "r"] = wr
    stream = [None, None]
    for i in range(9):
        t = i / 8
        p = spine[2] + (spine[5] - spine[2]) * t
        a = i * 2.2
        d = Vector((math.cos(a) * 0.1, 0.0, math.sin(a) * 0.08))
        stream[i % 2] = g.merge(stream[i % 2], g.tongue([p + d, p + d * 1.5 + Vector((0, 0.16, -0.02)), p + d * 1.2 + Vector((0, 0.36, -0.03))], [0.07, 0.05, 0.003], thick=0.3, normal=d))
    B.move("sway", "stream_a", [(stream[0], under, True)], spine[2])
    B.move("sway", "stream_b", [(stream[1], main, True)], spine[3])
    # what was sent
    a0, a1 = Vector((-0.02, -0.2, 0.36)), Vector((-0.02, -0.84, 0.385))
    d = (a1 - a0).normalized()
    B.add(g.tube([a0, a1], 0.0065, n=5), "wood_grey_pale", False)
    B.add(g.cone(a1, a1 + d * 0.06, 0.018, n=4), "metal_iron_light", False)
    fl = None
    for i in range(3):
        n = Vector((math.cos(i * 2.1), 0, math.sin(i * 2.1)))
        fl = g.merge(fl, g.blade(a0 + d * 0.01, a0 + d * 0.11 + n * 0.012, 0.05, normal=n.cross(d), belly=0.35))
    B.add(fl, "accent_light", False)
    F.top, F.zsh, F.neck = 0.62, 0.52, 0.5
    B.frame(0.62, front=-0.4, mid=0.5, half=0.16)
    B.socket("socket_eyes", e + Vector((0, -0.01, 0)))
    B.socket("socket_back", (0, 0.2, 0.62))
    return F


def plan_corner(B, spec):
    """Something in the corner of the ceiling, and the corner with it: two walls and a ceiling,
    a clot of dark where they meet, one pale eye that looks about, long fingers hanging."""
    main, under = B.main, B.under
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    c = Vector((0, 0, 0.78))
    # the corner it keeps to: broken off where the plaster ends
    A = Vector((0.2, 0.26, 1.02))
    back = [A, Vector((-0.5, 0.26, 1.02)), Vector((-0.54, 0.26, 0.86)), Vector((-0.4, 0.26, 0.74)), Vector((-0.24, 0.26, 0.8)), Vector((-0.1, 0.26, 0.62)), Vector((0.06, 0.26, 0.7)), Vector((0.2, 0.26, 0.52))]
    side = [A, Vector((0.2, 0.26, 0.52)), Vector((0.2, 0.1, 0.66)), Vector((0.2, -0.06, 0.6)), Vector((0.2, -0.2, 0.76)), Vector((0.2, -0.36, 0.84)), Vector((0.2, -0.4, 1.02))]
    top = [A, Vector((0.2, -0.4, 1.02)), Vector((0.04, -0.3, 1.02)), Vector((-0.16, -0.16, 1.02)), Vector((-0.3, -0.02, 1.02)), Vector((-0.5, 0.26, 1.02))]

    def slab(poly, n, t=0.03):
        n = V(n)
        m = len(poly)
        verts = [p for p in poly] + [p + n * t for p in poly]
        return verts, [tuple(range(m - 1, -1, -1)), tuple(range(m, 2 * m))] + [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
    B.add(slab(back, Y), "plaster", False)
    B.add(slab(side, X), "plaster_dark", False)
    B.add(slab(top, Z), "plaster_pale", False)
    B.add(g.merge(g.tube([A + Vector((-0.01, -0.012, -0.012)), Vector((-0.5, 0.248, 1.008))], 0.012, n=4), g.tube([A + Vector((-0.012, -0.01, -0.012)), Vector((0.188, -0.4, 1.008))], 0.012, n=4)), "plaster_pale", False)
    # the clot
    B.add(g.ico(c, 0.2, sub=2, scale=(1.15, 0.95, 0.72)), main)
    lobes = None
    for i, (dx, dy, dz, r) in enumerate(((0.16, 0.12, 0.08, 0.12), (-0.21, 0.1, 0.06, 0.13), (0.0, 0.17, 0.12, 0.13), (0.1, -0.08, -0.09, 0.1), (-0.1, -0.06, -0.1, 0.11))):
        lobes = g.merge(lobes, g.ico(c + Vector((dx, dy, dz)), r, sub=2, scale=(1.1, 1.0, 0.8), rot=(0, 0, i)))
    B.add(lobes, under)
    strands = None
    for tip in (Vector((-0.44, 0.25, 0.98)), Vector((0.19, -0.3, 0.98)), Vector((0.18, 0.24, 1.0))):
        d = tip - c
        strands = g.merge(strands, g.tube([c + d * 0.3, c + d * 0.65 + Z * 0.02, tip], [0.03, 0.016, 0.006], n=5))
    B.add(strands, main, True)
    # the eye: pale, ringed in its Path's colour, lit at the middle; it looks about, and it blinks
    eye = c + Vector((0, -0.17, -0.01))
    ball = B.move("turn", "eye", [(g.ico(eye, 0.115, sub=2, scale=(1.3, 0.42, 0.86)), "mask_pale", True),
                                  (g.ico(eye + Vector((0, -0.022, 0.0)), 0.072, sub=2, scale=(1.0, 0.4, 1.0)), "accent", True)], c)
    B.move("blink", "pupil", [(g.ico(eye + Vector((0, -0.04, 0.0)), 0.04, sub=2, scale=(1.0, 0.5, 1.0)), field("eyes", 4.2), True)], eye + Vector((0, -0.04, 0)), parent=ball)
    B.add(sk.arc(eye + Vector((0, -0.012, 0.0)), 0.155, 0.105, 0.12, math.pi - 0.12, 0.02, n=10, u=X, v=Z, sides=5), main, True)
    hang = [[None, None], [None, None]]
    tips = []
    for i, (x, L) in enumerate(((-0.2, 0.42), (-0.12, 0.6), (-0.04, 0.5), (0.05, 0.66), (0.13, 0.46), (0.21, 0.56))):
        b = c + Vector((x, -0.06 + 0.03 * (i % 2), -0.1))
        p1, p2, p3 = b + Vector((0.01, -0.02, -L * 0.5)), b + Vector((-0.005 + 0.012 * (i % 3), -0.045, -L * 0.88)), b + Vector((-0.01 + 0.02 * (i % 3), -0.05, -L))
        hang[i % 2][0] = g.merge(hang[i % 2][0], g.tube([b, p1, p2], [0.017, 0.012, 0.007], n=5))
        hang[i % 2][1] = g.merge(hang[i % 2][1], g.tube([p2, p3], [0.007, 0.0006], n=5))
        tips.append(p3)
    for j, what in enumerate(("fingers_a", "fingers_b")):
        B.move("sway", what, [(hang[j][0], main, True), (hang[j][1], F.thread, True)], c + Vector((0, -0.05, -0.1)))
    F.top, F.zsh, F.neck = 0.93, 0.7, 0.78
    F.hands = {"l": Vector((0.21, -0.1, 0.3)), "r": Vector((-0.2, -0.1, 0.36))}
    B.frame(0.93, front=-0.2, mid=0.72, half=0.24)
    B.socket("socket_eyes", eye + Vector((0, -0.03, 0)))
    return F


def plan_monolith(B, spec):
    """No step, no cloth, no breath: a still shape with nothing loose on it, one seam down the
    front of it, and its eyes shut."""
    main = B.main
    k = spec.get("build", {}).get("tall", 1.0)
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    prof = [(0.0, 0.1), (0.08, 0.14), (0.13, 0.3), (0.15, 0.5 * k), (0.13, 0.7 * k), (0.11, 0.8 * k), (0.115, 0.9 * k), (0.085, 1.0 * k), (0.0, 1.05 * k)]
    B.add(g.lathe(prof, n=18), main)
    seam = [Vector((0, -r - 0.003, zz)) for r, zz in prof[1:6]]
    B.add(g.tube(sk.curve(seam, n=3), 0.006, n=4), F.thread, True)
    c = Vector((0, -0.105, 0.9 * k))
    B.add(g.ico(c + Vector((0, 0.03, 0)), 0.08, sub=2, scale=(0.95, 0.4, 1.12)), "accent", True)
    B.add(g.ico(c + Vector((0, 0.022, 0)), 0.071, sub=2, scale=(0.9, 0.4, 1.1)), "void", True)
    B.add(sk.hoop(c + Vector((0, 0.008, 0)), 0.07, 0.083, 0.006, n=16, u=X, v=Z, sides=5), F.thread, True)
    geo = None
    for s in (1, -1):
        geo = g.merge(geo, g.tongue([c + Vector((s * 0.01, -0.008, 0.0)), c + Vector((s * 0.031, -0.012, -0.006)), c + Vector((s * 0.054, -0.006, 0.002))], [0.004, 0.012, 0.004], thick=0.5, normal=(0, -1, 0.3)))
    B.move("blink", "eyes", [(geo, field("eyes", 2.4), True)], c + Vector((0, -0.01, 0)))
    F.top, F.zsh, F.neck = 1.05 * k, 0.66 * k, 0.8 * k
    B.frame(F.top, front=-0.14, mid=0.55 * k, half=0.16)
    B.socket("socket_eyes", c + Vector((0, -0.02, 0)))
    return F


def plan_tree(B, spec):
    """You count the trees and there is one too many: a bare tree in its own sod, a few leaves of
    its Path's colour still on it, and two eyes like holes in the hedge."""
    main, under = B.main, B.under
    F = Fig(B, {"hem": 0.2, "tall": 1.0})
    B.add(g.lathe([(0.11, 0.06), (0.085, 0.2), (0.075, 0.5), (0.07, 0.8), (0.08, 0.92), (0.06, 1.02), (0.0, 1.08)], n=12), main)
    roots = None
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        roots = g.merge(roots, g.tube([d * 0.07 + Z * 0.14, d * 0.2 + Z * 0.06, d * (0.32 + 0.06 * (i % 2)) + Z * 0.03], [0.04, 0.028, 0.008], n=6))
    B.add(roots, main, True)
    # the sod it stands in
    B.add(g.ico((0, 0, 0.0), 0.4, sub=2, scale=(1.0, 0.86, 0.14)), "earth_grey", True)
    B.add(g.ico((0.03, 0.02, -0.04), 0.3, sub=1, scale=(1.0, 0.9, 0.22)), "stone_dark", False)
    fallen = None
    for i, (x, y) in enumerate(((0.26, -0.14), (-0.22, -0.2), (0.05, -0.3), (-0.3, 0.05), (0.2, 0.2))):
        fallen = g.merge(fallen, g.blade((x, y, 0.05), (x + 0.07 * math.cos(i * 1.9), y + 0.07 * math.sin(i * 1.9), 0.052), 0.045, normal=Z))
    B.add(fallen, "accent_dark", False)
    # the arms go up as branches; what is on them sways
    for s, lift in ((1, 0.0), (-1, 0.08)):
        b0, b1, b2 = Vector((s * 0.06, 0, 0.82)), Vector((s * 0.2, -0.02, 0.98 + lift)), Vector((s * 0.3, 0.0, 1.2 + lift))
        B.add(g.tube([b0, b1, b2], [0.04, 0.028, 0.012], n=6), main, True)
        twigs, leaves = None, None
        for j, (dx, dy, dz) in enumerate(((0.12, -0.03, 0.14), (0.02, 0.05, 0.2), (-0.06, -0.04, 0.17))):
            tip = b2 + Vector((s * dx, dy, dz)) * 1.2
            twigs = g.merge(twigs, g.tube([b2, b2 + Vector((s * dx, dy, dz)) * 0.6, tip], [0.012, 0.008, 0.002], n=4))
            leaves = g.merge(leaves, g.blade(tip, tip + Vector((s * 0.03, -0.01, -0.1)), 0.06, normal=Y), g.blade(tip - Vector((s * dx, dy, dz)) * 0.5, tip - Vector((s * dx, dy, dz)) * 0.5 + Vector((-s * 0.05, -0.01, -0.09)), 0.05, normal=Y))
        tw2 = b1 + Vector((s * 0.02, 0, 0.02))
        twigs = g.merge(twigs, g.tube([tw2, tw2 + Vector((s * 0.13, -0.04, 0.02)), tw2 + Vector((s * 0.2, -0.06, 0.1))], [0.014, 0.009, 0.002], n=4))
        leaves = g.merge(leaves, g.blade(tw2 + Vector((s * 0.2, -0.06, 0.1)), tw2 + Vector((s * 0.22, -0.07, 0.0)), 0.06, normal=Y))
        B.move("sway", "bough", [(twigs, under, True), (leaves, "accent", False)], b2, side="l" if s > 0 else "r")
        F.hands["l" if s > 0 else "r"] = b2
    # eyes like two holes in the hedge
    holes, rims, lights = None, None, None
    for s in (1, -1):
        p = Vector((s * 0.032, -0.073, 0.93))
        holes = g.merge(holes, g.ico(p, 0.026, sub=2, scale=(1.0, 0.5, 1.2)))
        rims = g.merge(rims, sk.hoop(p + Vector((0, -0.008, 0)), 0.031, 0.036, 0.006, n=10, u=X, v=Z, sides=4))
        lights = g.merge(lights, g.ico(p + Vector((0, -0.012, -0.008)), 0.007, sub=1))
    B.move("blink", "eyes", [(holes, "void", True), (lights, field("eyes", 3.0), True)], (0, -0.08, 0.93))
    B.add(rims, F.thread, True)
    F.top, F.zsh, F.neck = 1.08, 0.82, 0.9
    B.frame(1.08, front=-0.1, mid=0.6, half=0.14)
    B.socket("socket_eyes", (0, -0.085, 0.93))
    return F


PLANS = {"blot": plan_blot, "figure": plan_figure, "seated": plan_seated, "robed": plan_robed, "door": plan_door, "hatch": plan_hatch,
         "human": plan_human, "streak": plan_streak, "corner": plan_corner, "monolith": plan_monolith, "tree": plan_tree}


# --- what it has, round the figure -----------------------------------------------------------

def legs_stilts(B, F, size):
    """Tall and thin: two legs of the same dark under the hem, a thread at each knee."""
    for s in (1, -1):
        hip = Vector((s * 0.035, 0.0, F.hem + 0.02))
        knee = hip + Vector((s * 0.015, -0.02, -0.26 * size))
        foot = hip + Vector((s * 0.02, 0.0, -0.52 * size))
        B.add(g.tube([hip, knee, foot], [0.03, 0.021, 0.013], n=6), B.main, True)
        B.add(g.tongue([foot + Vector((0, 0.02, 0)), foot + Vector((0, -0.08, -0.015))], [0.04, 0.008], thick=0.5, normal=Z), B.under)
        B.add(sk.hoop(knee, 0.025, 0.025, 0.005, n=8, sides=4), F.thread, True)


def legs_back(B, F, size):
    """Long thin legs that fold the wrong way, and feet that are hands."""
    for s in (1, -1):
        hip = Vector((s * 0.06, 0.02, F.hem + 0.04))
        knee = hip + Vector((s * 0.05, 0.2 * size, -0.12 * size))
        ank = hip + Vector((s * 0.06, -0.06 * size, -0.36 * size))
        foot = hip + Vector((s * 0.06, 0.02 * size, -0.52 * size))
        B.add(g.tube([hip, knee, ank, foot], [0.036, 0.025, 0.018, 0.013], n=6), B.main, True)
        B.add(g.ico(knee, 0.03, sub=1), B.under, True)
        B.add(sk.hoop(ank, 0.022, 0.022, 0.005, n=8, sides=4), F.thread, True)
        B.extend(hand_of(F, foot + Vector((0, 0.01, 0)), Vector((0, -1, -0.2)), k=0.8, hook=0.35, n=3, spread=0.02))


def legs_roots(B, F, size):
    roots = None
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        roots = g.merge(roots, g.tube([d * 0.05 + Z * (F.hem + 0.03), d * 0.16 + Z * (F.hem - 0.06), d * (0.28 + 0.05 * (i % 2)) + Z * (F.hem - 0.1)], [0.035, 0.025, 0.004], n=6))
    B.add(roots, B.main, True)


def ground_long(B, F, size):
    """It stretches long across the boards of a floor, and there are eyes in it. The boards are the
    floor it lies on, and go where it goes."""
    z0 = F.hem - 0.24
    B.extend(sk.planks((-0.36 * size, 0.07 * size, z0 - 0.014), 1.08 * size, 0.56 * size, n=4, turn=-0.2))
    pts = [Vector((0, 0.02, z0)), Vector((-0.2, 0.06, z0 - 0.005)), Vector((-0.48, 0.14, z0 - 0.01)), Vector((-0.78, 0.2, z0 - 0.01))]
    pts = [Vector((p.x * size, p.y * size, p.z)) for p in pts]
    B.add(g.tongue(pts, [0.24 * size, 0.34 * size, 0.27 * size, 0.03], thick=0.1, normal=Z), B.main)
    B.add(g.tongue([Vector((0, 0, F.hem)), Vector((-0.03, 0.01, F.hem - 0.12)), pts[0]], [0.1, 0.12, 0.2], thick=0.5, normal=-Y), B.main)
    # the eyes in it: each on a swell of the shadow, looking up the room
    eyes, lids, swell = None, None, None
    for i, t in enumerate((0.3, 0.56, 0.8)):
        p = pts[0] + (pts[3] - pts[0]) * t + Vector((0, -0.03 + 0.03 * (i % 2), 0.03))
        k = (1.0 - 0.16 * i) * (0.7 + 0.3 * size)
        swell = g.merge(swell, g.ico(p, 0.075 * k, sub=2, scale=(1.3, 1.0, 0.7)))
        eyes = g.merge(eyes, g.ico(p + Vector((0, -0.058 * k, 0.014)), 0.028 * k, sub=2, scale=(1.15, 0.5, 0.85)))
        lids = g.merge(lids, sk.arc(p + Vector((0, -0.064 * k, 0.012)), 0.045 * k, 0.038 * k, 0.1, math.pi - 0.1, 0.007, n=8, u=X, v=Z, sides=4))
    B.add(swell, B.under)
    B.move("blink", "eyes_long", [(eyes, field("eyes", 3.2), True)], pts[0] + (pts[3] - pts[0]) * 0.56 + Vector((0, -0.06, 0.044)))
    B.add(lids, F.thread, True)
    hangs(B, [Vector((x * size, y * size, z0 - 0.045)) for x, y in ((-0.05, 0.1), (-0.35, -0.08), (-0.6, 0.22), (-0.78, 0.05))], L=0.1)


def ground_cohort(B, F, size):
    """Twelve small shapes stand round its hem, on the round of floor they share."""
    zf = F.hem - 0.27
    B.add(sk.disc((0, 0, zf - 0.035), 0.4 * size, thick=0.035, n=18, squash=0.86), "stone_flag", False)
    B.add(sk.hoop((0, 0, zf + 0.001), 0.22 * size, 0.19 * size, 0.008, n=18, sides=4), "stone_flag_pale", False)
    groups = [[None, None, None] for _ in range(3)]
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        d = Vector((math.cos(a), math.sin(a) * 0.86, 0))
        h = 1.0 + 0.2 * ((i * 5) % 3)
        c = d * 0.31 * size + Z * zf
        grp = groups[i % 3]
        grp[0] = g.merge(grp[0], g.lathe([(0.0, 0.0), (0.036, 0.01), (0.03, 0.07 * h), (0.04, 0.1 * h), (0.031, 0.135 * h), (0.0, 0.16 * h)], n=8, centre=c))
        grp[1] = g.merge(grp[1], sk.hoop(c + Z * 0.074 * h, 0.032, 0.032, 0.006, n=8, sides=4))
        if d.y < 0.3:
            grp[2] = g.merge(grp[2], sk.eye_pair(c + Vector((d.x * 0.02, -0.036, 0.108 * h)), 0.013, 0.008, scale=(1, 0.6, 1), slant=0.0))
    for j, grp in enumerate(groups):
        B.move("bob", "cohort_" + "abc"[j], [(grp[0], B.under, True), (grp[1], F.thread, True), (grp[2], field("eyes", 2.6), True)], (0, 0, zf))
    hangs(B, [(0.2, 0.1, zf - 0.06), (-0.22, 0.05, zf - 0.06), (0.0, -0.2, zf - 0.06)], L=0.1)


def ground_ring(B, F, size):
    """The round of road it stands on, and the edge the quiet has: rings on the setts, round its foot."""
    B.add(sk.disc((0, 0, 0.055), 0.46 * size, thick=0.045, n=18), "stone_sett", False)
    setts = None
    for i in range(14):
        a = 2 * math.pi * i / 14
        setts = g.merge(setts, g.box((0.4 * size * math.cos(a), 0.4 * size * math.sin(a), 0.1), (0.1, 0.07, 0.016), rot=(0, 0, a + math.pi / 2)))
    B.add(setts, "stone_flag", False)
    rings = g.merge(sk.hoop((0, 0, 0.106), 0.3 * size, 0.3 * size, 0.008, n=22, sides=4), sk.hoop((0, 0, 0.106), 0.21 * size, 0.21 * size, 0.006, n=18, sides=4))
    B.move("pulse", "rings", [(rings, "accent_pale", True)], (0, 0, 0.106))
    hangs(B, [(0.25, 0.1, 0.05), (-0.25, 0.12, 0.05), (0.0, -0.28, 0.05)], L=0.1)


def ground_wall(B, F, size):
    """The wall it listens at, and the floor at the foot of it."""
    x = 0.36
    zf = F.hem - 0.3
    rows = [None, None]
    for r in range(6):
        for c in range(3):
            y = -0.2 + c * 0.17 + (0.085 if r % 2 else 0.0)
            rows[(r + c) % 2] = g.merge(rows[(r + c) % 2], g.box((x, y, zf + 0.05 + r * 0.11), (0.05, 0.158, 0.098)))
    B.add(rows[0], "stone_flag", False)
    B.add(rows[1], "stone_flag_pale", False)
    B.extend(sk.flags((0.02, -0.08, zf), 0.78, 0.62, nx=3, ny=2))
    hangs(B, [(0.2, 0.1, zf - 0.045), (-0.25, -0.1, zf - 0.045), (0.0, -0.3, zf - 0.045)], L=0.1)


def ground_sill(B, F, size):
    """The sill it keeps: a worn stone step, as wide as a door, and it stands on it."""
    zf = F.hem - 0.25
    B.extend(sk.flags((0, -0.02, zf), 0.86 * size, 0.3, nx=3, ny=1, thick=0.055, names=("stone_step", "stone_flag_pale")))
    hangs(B, [(x * size, 0.0, zf - 0.07) for x in (-0.34, -0.12, 0.14, 0.34)], L=0.11)


def ground_bed(B, F, size):
    """The head of the bed it sits by: a post, a pillow, the blanket turned down."""
    x0 = -0.3
    B.add(g.box((x0 - 0.2, 0.0, 0.15), (0.44, 0.5, 0.1)), "cloth_grey", False)              # the mattress
    B.add(g.box((x0 - 0.21, -0.1, 0.215), (0.44, 0.32, 0.04)), "accent_dark", False)         # the blanket
    B.add(g.box((x0 - 0.21, 0.045, 0.225), (0.45, 0.05, 0.045)), "accent_light", False)      # turned down
    B.add(g.ico((x0 - 0.2, 0.16, 0.235), 0.1, sub=2, scale=(1.5, 0.8, 0.42)), "paper_pale", True)   # the pillow
    posts = g.merge(g.box((x0 + 0.03, 0.26, 0.26), (0.04, 0.04, 0.52)), g.box((x0 - 0.42, 0.26, 0.26), (0.04, 0.04, 0.52)), g.box((x0 - 0.195, 0.26, 0.4), (0.44, 0.03, 0.16)),
                    g.box((x0 + 0.03, -0.24, 0.1), (0.04, 0.04, 0.2)), g.box((x0 - 0.42, -0.24, 0.1), (0.04, 0.04, 0.2)))
    B.add(posts, "wood_grey", False)
    B.add(g.merge(g.ico((x0 + 0.03, 0.26, 0.545), 0.03, sub=1), g.ico((x0 - 0.42, 0.26, 0.545), 0.03, sub=1)), "accent_light", True)


def wears_mantle(B, F, size):
    """Broad across the back: a yoke of the same dark over the shoulders, its edge dagged, a
    thread along it and a clasp at the throat."""
    z = F.zsh
    w = 0.185 * F.broad * (0.9 + 0.1 * size)
    dp = 0.125 * F.deep
    rings = [g.ring((0, 0.012, z - 0.13 * size), w + 0.04, dp + 0.02, n=N, u=X, v=Y, phase=math.pi / N),
             g.ring((0, 0.01, z - 0.02), w + 0.02, dp + 0.012, n=N, u=X, v=Y, phase=math.pi / N),
             g.ring((0, 0.005, z + 0.045), w * 0.72, 0.1 * F.deep, n=N, u=X, v=Y, phase=math.pi / N)]
    F.put(g.loft(rings, caps=False), B.under, True)
    F.put(sk.hoop((0, 0.012, z - 0.13 * size), w + 0.043, dp + 0.023, 0.006, n=N, sides=5), F.thread, True)
    dags = [None, None]
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        d = Vector((math.cos(a) * (w + 0.04), math.sin(a) * (dp + 0.02), 0))
        dags[i % 2] = g.merge(dags[i % 2], g.blade(Vector((0, 0.012, z - 0.125 * size)) + d, Vector((0, 0.012, z - 0.125 * size - 0.1 * size)) + d * 1.08, 0.085, normal=d, belly=0.35))
    F.put(dags[0], B.under, True)
    F.put(dags[1], "accent_dark", True)
    F.put(g.ico(Vector((0, -(0.1 * F.deep) - 0.012, z + 0.03)), 0.02, sub=1, scale=(1, 0.5, 1)), F.thread, True)


def wears_collar(B, F, size):
    """Its collar is up: two wings of it stand to the eyes, lined with its Path's colour."""
    z = F.neck - 0.045
    for s in (1, -1):
        pts = [Vector((s * 0.03, -0.1 * F.hood, z)), Vector((s * 0.1 * F.hood, -0.08 * F.hood, z + 0.06 * size)), Vector((s * 0.135 * F.hood, -0.02, z + 0.14 * size)), Vector((s * 0.125 * F.hood, 0.06, z + 0.17 * size))]
        F.put(g.tongue(pts, [0.05, 0.13 * size, 0.15 * size, 0.06], thick=0.25, normal=(s, -0.4, 0.2)), B.under, True)
        F.put(g.tongue([p + Vector((-s * 0.014, -0.004, 0.004)) for p in pts], [0.036, 0.105 * size, 0.125 * size, 0.045], thick=0.2, normal=(s, -0.4, 0.2)), "accent", True)
    F.put(g.tongue([Vector((-0.1 * F.hood, 0.08, z + 0.02)), Vector((0, 0.115 * F.hood, z + 0.1 * size)), Vector((0.1 * F.hood, 0.08, z + 0.02))], [0.1, 0.17 * size, 0.1], thick=0.25, normal=(0, 1, 0.2)), B.under, True)


def wears_script(B, F, size):
    """Lines of what was sworn, round the cloak."""
    geo = None
    for t in (0.36, 0.5):
        z = F.hem + (t - 0.2) * F.tall
        geo = g.merge(geo, sk.hoop((0, 0.01, z), 0.152 * F.broad * (0.86 if t < 0.4 else 1.0), 0.103 * F.deep, 0.006, n=N, sides=4))
    F.put(geo, field("script", 2.0))


def wears_cape(B, F, size):
    """The cloak thrown back behind it, as if it had moved: it shows its lining at the edges, and sways."""
    z = F.zsh
    over, lining_ = None, None
    for s in (1, -1):
        pts = [Vector((s * 0.1, 0.06, z + 0.02)), Vector((s * 0.2, 0.22 * size, z - 0.04)), Vector((s * 0.25, 0.46 * size, z - 0.16)), Vector((s * 0.18, 0.66 * size, z - 0.24))]
        over = g.merge(over, g.tongue(pts, [0.16, 0.24, 0.2, 0.02], thick=0.2, normal=(s * 0.4, 0, 1)))
        lining_ = g.merge(lining_, g.tongue([p + Vector((s * 0.02, 0.012, -0.016)) for p in pts], [0.18, 0.27, 0.23, 0.03], thick=0.12, normal=(s * 0.4, 0, 1)))
    mid = [Vector((0, 0.08, z + 0.02)), Vector((0, 0.3 * size, z - 0.08)), Vector((0, 0.56 * size, z - 0.22)), Vector((0, 0.78 * size, z - 0.3))]
    F.mv("sway", "cape", [(over, B.under, True), (g.tongue(mid, [0.2, 0.26, 0.2, 0.02], thick=0.2, normal=Z), B.main, True), (lining_, "accent", True)], (0, 0.07, z + 0.02))


def wears_shawl(B, F, size):
    """A shawl over the shoulders, for the cold hour: its Path's colour, fringed."""
    z = F.zsh
    rings = [g.ring((0, 0.0, z - 0.12 * size), 0.2, 0.15, n=N, u=X, v=Y, phase=math.pi / N), g.ring((0, 0.0, z + 0.02), 0.175, 0.13, n=N, u=X, v=Y, phase=math.pi / N),
             g.ring((0, 0.0, z + 0.07), 0.1, 0.09, n=N, u=X, v=Y, phase=math.pi / N)]
    F.put(g.loft(rings, caps=False), "accent_dark", True)
    F.put(sk.hoop((0, 0, z - 0.05 * size), 0.19, 0.142, 0.006, n=N, sides=4), "accent_light", True)
    fr = None
    for i in range(14):
        a = 2 * math.pi * (i + 0.5) / 14
        d = Vector((math.cos(a) * 0.2, math.sin(a) * 0.15, 0))
        fr = g.merge(fr, g.blade(Vector((0, 0, z - 0.11 * size)) + d, Vector((0, 0, z - 0.2 * size)) + d * 1.05, 0.05, normal=d))
    F.put(fr, "accent", True)


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
    """A wide dark place in the middle of it, like a mouth, and a light a long way down it."""
    c = F.chest + Vector((0, -0.016, -0.01))
    F.put(g.ico(c + Vector((0, 0.03, 0)), 0.13 * size, sub=2, scale=(1.3 * F.broad, 0.35, 0.92)), "void")
    F.put(sk.hoop(c + Vector((0, -0.006, 0)), 0.166 * F.broad * size, 0.118 * size, 0.007, n=18, u=X, v=Z, sides=5), F.thread, True)
    rim = None
    n = 14
    for i in range(n):
        a = 2 * math.pi * i / n
        p = c + Vector((0.17 * F.broad * size * math.cos(a), 0.0, 0.125 * size * math.sin(a)))
        rim = g.merge(rim, g.blade(p + Vector((0.02 * math.cos(a), 0, 0.02 * math.sin(a))), p + Vector((-0.085 * math.cos(a), -0.014, -0.07 * math.sin(a))) * 1.0, 0.045 * size, normal=-Y, belly=0.25))
    F.put(rim, B.under)
    low = c + Vector((0, -0.02, -0.02 * size))
    F.mv("pulse", "maw", [(g.ico(low, 0.042 * size, sub=2, scale=(1.5 * F.broad, 0.3, 0.7)), field("maw", 2.0), True)], low)


def chest_keyhole(B, F, size):
    """The door in its chest: a keyhole in a plate of its Path's colour, lit from inside."""
    c = F.chest + Vector((0, -0.012, 0.01))
    F.put(g.ico(c, 0.07 * size, sub=2, scale=(0.8, 0.22, 1.25)), F.thread, True)
    F.put(g.merge(g.ico(c + Vector((0, -0.012, 0.03 * size)), 0.03 * size, sub=2, scale=(1, 0.4, 1)),
                  g.tongue([c + Vector((0, -0.016, 0.03 * size)), c + Vector((0, -0.016, -0.06 * size))], [0.022 * size, 0.046 * size], thick=0.3, normal=-Y)), "void", True)
    lit = g.merge(g.ico(c + Vector((0, -0.02, 0.03 * size)), 0.019 * size, sub=2, scale=(1, 0.4, 1)),
                  g.tongue([c + Vector((0, -0.022, 0.03 * size)), c + Vector((0, -0.022, -0.05 * size))], [0.012 * size, 0.03 * size], thick=0.3, normal=-Y))
    F.mv("pulse", "keyhole", [(lit, field("door", 3.0), True)], c)


def chest_cold_hand(B, F, size):
    """A patch of cold the size of a hand."""
    c = F.chest + Vector((0, -0.018, 0.02))
    F.put(g.ico(c, 0.04 * size, sub=2, scale=(1.0, 0.3, 1.1)), "ice_pale")
    fing = None
    for i, a in enumerate((-0.6, -0.25, 0.05, 0.35, 0.95)):
        d = Vector((math.sin(a), 0, math.cos(a)))
        L = (0.075 if i != 4 else 0.05) * size
        fing = g.merge(fing, g.tongue([c + d * 0.03 * size, c + d * (0.03 * size + L)], [0.018 * size, 0.012 * size], thick=0.4, normal=-Y))
    F.put(fing, "ice_pale")
    F.mv("pulse", "cold", [(g.ico(c + Vector((0, -0.012, 0)), 0.016 * size, sub=1), field("core", 3.2), True)], c)


def chest_core(B, F, size):
    """A cold light in the middle of it."""
    c = F.chest + Vector((0, -0.01, 0.02))
    F.mv("pulse", "core", [(g.ico(c, 0.045 * size, sub=2, scale=(0.8, 0.5, 1.3)), field("core", 3.4), True)], c)
    geo = None
    for i in range(6):
        a = 2 * math.pi * i / 6
        d = Vector((math.cos(a), 0, math.sin(a)))
        geo = g.merge(geo, sk.crystal(c + d * 0.05 * size, c + d * 0.13 * size + Vector((0, -0.02, 0)), 0.016, n=4))
    F.put(geo, "ice")


def face_mask(B, F, size):
    """A blank pale mask hangs in the dark of the hood, and lifts when your guard lifts."""
    H = F.hood_at
    geo = None
    for s in (1, -1):
        geo = g.merge(geo, g.box(H(s * 0.028, -0.126, 0.69), (0.034 * size, 0.008, 0.007)))
    F.mv("bob", "mask", [(g.ico(H(0, -0.1, 0.672), 0.072 * F.hood * size, sub=2, scale=(0.84, 0.3, 1.16)), "mask_pale", True), (geo, "void", False),
                         (sk.hoop(H(0, -0.106, 0.672), 0.058 * F.hood * size, 0.082 * F.hood * size, 0.004, n=14, u=X, v=Z, sides=4), F.thread, True)], H(0, -0.1, 0.672), parent=F.head)


def _second_face(F, c, r, crowned=False, mouth=True):
    """A second, smaller head on a neck of its own from the shoulder: it looks about, and blinks."""
    B = F.B
    root = F.sh(1) + Vector((-0.04, 0.0, 0.03))
    F.put(g.tube([root, (root + c) / 2 + Vector((0.02, 0.02, 0)), c + Vector((0, 0.01, -r * 0.7))], [0.03, 0.022, 0.02], n=6), B.main, True)
    items = [(g.ico(c, r, sub=2, scale=(0.95, 0.95, 1.1)), B.main, True),
             (g.ico(c + Vector((0, -r * 0.62, 0.0)), r * 0.8, sub=2, scale=(0.84, 0.36, 1.12)), "mask_pale", True),
             (g.tongue([c + Vector((0, -r * 0.92, r * 0.25)), c + Vector((0, -r * 1.08, 0)), c + Vector((0, -r * 0.9, -r * 0.18))], [r * 0.14, r * 0.26, r * 0.08], thick=0.7, normal=X), "mask_pale", True),
             (sk.hoop(c + Vector((0, -r * 0.6, 0)), r * 0.72, r * 0.95, r * 0.07, n=14, u=X, v=Z, sides=4), F.thread, True)]
    if mouth:
        items.append((g.tongue([c + Vector((-r * 0.36, -r * 0.84, -r * 0.42)), c + Vector((0, -r * 0.95, -r * 0.5)), c + Vector((r * 0.36, -r * 0.84, -r * 0.42))], [0.004, r * 0.22, 0.004], thick=0.3, normal=(0, -1, 0)), field("mouth", 3.2), True))
    if crowned:
        items.append((sk.hoop(c + Vector((0, 0, r * 0.8)), r * 0.82, r * 0.82, r * 0.1, n=12, sides=4), "accent_light", False))
        items.append((sk.crown_points(c + Vector((0, 0, r * 0.8)), r * 0.82, 6, r * 0.9, r * 0.5), "accent_light", False))
        items.append((sk.crown_points(c + Vector((0, 0, r * 0.84)), r * 0.5, 3, r * 0.5, r * 0.3, tilt=0.5), field("crown", 1.2), False))
    head = F.mv("turn", "face", items, c)
    e = c + Vector((0, -r * 0.94, r * 0.28))
    F.mv("blink", "eyes_b", [(sk.eye_pair(e, r * 0.36, r * 0.2, scale=(1.3, 0.4, 0.5), slant=0.25), field("eyes", 3.0), True)], e, parent=head)


def shoulder_face(B, F, size):
    """A second, smaller face rides at its shoulder and does the talking."""
    _second_face(F, F.sh(1) + Vector((0.06, -0.05, 0.19)), 0.068 * size)


def shoulder_face_crowned(B, F, size):
    """A dim crown sits over the second face, which has grown."""
    _second_face(F, F.sh(1) + Vector((0.05, -0.03, 0.3 * size)), 0.07 * size, crowned=True)


def head_ear(B, F, size):
    """One side of it is all ear."""
    c = F.hood_at(0.09, 0.0, 0.675)
    rings = [g.ring(c + X * off, r, r * 1.1, n=14, u=Y, v=Z) for off, r in ((0.0, 0.03), (0.06 * size, 0.07 * size), (0.14 * size, 0.15 * size), (0.2 * size, 0.24 * size))]
    F.on_head(g.loft(rings, caps=False), B.under, True)
    F.on_head(g.loft([g.ring(c + X * off, r, r * 1.1, n=14, u=Y, v=Z) for off, r in ((0.2 * size, 0.24 * size), (0.19 * size, 0.2 * size), (0.08 * size, 0.06 * size))], caps=False), "accent_dark", True)
    F.on_head(sk.hoop(c + X * 0.2 * size, 0.24 * size, 0.264 * size, 0.007, n=18, u=Y, v=Z, sides=5), F.thread, True)
    F.on_head(g.ico(c + X * 0.08 * size, 0.05 * size, sub=1, scale=(0.4, 1, 1.1)), "void", True)


def head_prow(B, F, size):
    """Its hood runs forward to a point, like the prow of something."""
    H = F.hood_at
    F.on_head(g.tongue([H(0, 0.02, 0.84), H(0, -0.12, 0.86), H(0, -0.26 * size, 0.8), H(0, -0.38 * size, 0.7)], [0.1, 0.12, 0.07, 0.006], thick=0.9, normal=Z), B.main, True)
    F.on_head(g.tube([H(0, -0.1, 0.875), H(0, -0.26 * size, 0.812), H(0, -0.385 * size, 0.7)], 0.0055, n=4), F.thread, True)
    for s in (1, -1):
        F.on_head(g.tongue([H(s * 0.07, -0.05, 0.8), H(s * 0.12, 0.08, 0.86), H(s * 0.14, 0.24 * size, 0.9)], [0.07, 0.09, 0.01], thick=0.3, normal=(s, 0, 1)), B.under, True)


def holds_lamp(B, F, size, low=False):
    """A covered lamp in its lap: brass of its Path's colour, and the light in it breathing."""
    robed = getattr(F, "robed", False)
    k = B.spec.get("build", {}).get("tall", 0.55) / 0.55 if robed else 1.0
    c = Vector((0, -0.23, 0.2 * k)) if robed else ((F.hand("l") + F.hand("r")) / 2 + Vector((0, -0.02, -0.03)) if "l" in F.hands and "r" in F.hands else Vector((0, -0.24, 0.42)))
    if low:
        # burned down beside it, and it has not noticed
        c = Vector((0.2, -0.36, 0.02)) if robed else c
        B.add(sk.disc(c, 0.075, thick=0.014, n=10), "accent_dark", False)
        B.add(sk.disc(c + Vector((0, 0, 0.012)), 0.05, thick=0.016, n=10), "accent_pale", True)
        t = c + Vector((0, 0, 0.03))
        B.add(g.tube([t, t + Z * 0.012], 0.003, n=3), "metal_dark", False)
        B.move("flick", "flame", [(g.tongue([t + Z * 0.008, t + Vector((0.004, 0, 0.022)), t + Vector((0, 0, 0.045))], [0.014, 0.02, 0.002], thick=0.7, normal=Y), field("flame", 3.0), True)], t + Z * 0.008)
        return
    s = 1.25 * size
    B.add(g.lathe([(0.02 * s, 0.0), (0.045 * s, 0.01 * s), (0.045 * s, 0.03 * s)], n=8, centre=c), "accent_dark", False)
    B.add(g.lathe([(0.045 * s, 0.06 * s), (0.047 * s, 0.075 * s), (0.02 * s, 0.1 * s), (0.0, 0.11 * s)], n=8, centre=c), "accent_light", False)
    B.move("pulse", "lamp", [(g.lathe([(0.036 * s, 0.03 * s), (0.04 * s, 0.045 * s), (0.036 * s, 0.06 * s)], n=8, centre=c, caps=False), field("core", 4.0), True)], c + Z * 0.045 * s)
    posts = None
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        posts = g.merge(posts, g.tube([c + Vector((math.cos(a) * 0.042 * s, math.sin(a) * 0.042 * s, 0.03 * s)), c + Vector((math.cos(a) * 0.042 * s, math.sin(a) * 0.042 * s, 0.06 * s))], 0.004 * s, n=3))
    B.add(posts, "accent_dark", False)
    B.add(sk.arc(c + Vector((0, 0, 0.1 * s)), 0.03 * s, 0.035 * s, 0.0, math.pi, 0.006, n=6, u=X, v=Z, sides=3), "accent_light", False)


def holds_lamp_low(B, F, size):
    holds_lamp(B, F, size, low=True)


def holds_dark_lamp(B, F, size):
    """A lamp it carries and does not light: it hangs from its hand, and swings when the arm does."""
    wr = F.hand("r", (-0.26, -0.1, 0.28))
    at = wr + Vector((0, -0.02, -0.06))
    B.move("sway", "lamp", sk.lantern(at, 0.085 * size, lit=False, cap="accent_light"), at, parent=F.arm_mv.get("r"))


def holds_glow(B, F, size):
    """A faint warm light under its hands, held where it can be seen."""
    if "l" in F.hands and "r" in F.hands:
        c = (F.hand("l") + F.hand("r")) / 2 + Vector((0, -0.03, 0.045))
    else:
        c = Vector((0, -0.3, 0.4))
    B.move("pulse", "glow", [(g.ico(c, 0.05 * size, sub=2), field("glow", 3.6), True), (sk.hoop(c, 0.085 * size, 0.085 * size, 0.005, n=14, u=X, v=Z, sides=3), field("halo", 1.4), True)], c)


def holds_book(B, F, size):
    """A thin dark book it never opens, held to its chest: its boards and its ribbon are its Path's colour."""
    c = F.chest + Vector((0, -0.05, -0.01))
    s = 0.17 * size
    R = Matrix.Rotation(-0.12, 3, "X")
    F.put(g.box(c, (s * 0.78, s * 0.2, s), rot=R), "accent_dark", False)
    F.put(g.box(c + R @ Vector((0, 0, -s * 0.03)), (s * 0.7, s * 0.14, s * 1.0), rot=R), "paper", False)
    F.put(g.merge(g.box(c + R @ Vector((0, -s * 0.11, 0)), (s * 0.84, s * 0.03, s * 0.14), rot=R), g.box(c + R @ Vector((0, -s * 0.104, s * 0.42)), (s * 0.8, s * 0.02, s * 0.05), rot=R),
                  g.box(c + R @ Vector((0, -s * 0.104, -s * 0.42)), (s * 0.8, s * 0.02, s * 0.05), rot=R)), "accent_light", False)
    F.mv("sway", "ribbon", [(g.tongue([c + Vector((0.03, -0.01, -0.08 * size)), c + Vector((0.035, -0.02, -0.14 * size)), c + Vector((0.03, -0.015, -0.21 * size))], [0.018, 0.018, 0.004], thick=0.3, normal=-Y), "accent", True)], c + Vector((0.03, -0.01, -0.08 * size)))


def holds_chain(B, F, size):
    """A thin chain hangs between its two hands, and swings."""
    a, b = F.hand("l") + Vector((0, -0.03, -0.03)), F.hand("r") + Vector((0, -0.03, -0.03))
    links = sk.chain(sk.sag(a, b, 0.09 * size, n=8), link=0.017, n=13)
    for p in (a, b):
        links = g.merge(links, sk.chain([p, p + Vector((0, 0, -0.085 * size))], link=0.017, n=2))
    B.move("sway", "chain", [(links, "metal_iron_light", True)], (a + b) / 2)


def holds_blade(B, F, size):
    """A short dark blade, held in the other hand."""
    wr = F.hand("l") + Vector((0, -0.05, 0))
    d = Vector((0.05, -1.0, -0.12)).normalized()
    B.add(g.tube([wr - d * 0.05, wr + d * 0.02], [0.012, 0.012], n=5), "leather_dark", False)
    B.add(g.ico(wr - d * 0.06, 0.016, sub=1), F.thread, True)
    B.add(g.box(wr + d * 0.025, (0.07, 0.012, 0.014)), "metal_iron", False)
    B.add(g.blade(wr + d * 0.03, wr + d * (0.03 + 0.24 * size), 0.05, thick=0.008, normal=Z, belly=0.25), "metal_dark", False)
    B.add(g.tube([wr + d * 0.04 + Vector((0.023, 0, 0)), wr + d * (0.03 + 0.22 * size)], [0.0035, 0.002], n=3), field("edge", 2.6))


def holds_bar(B, F, size):
    """The bar of a door, held across it in both hands: none shall pass."""
    a, b = F.hand("l"), F.hand("r")
    mid = (a + b) / 2 + Vector((0, -0.045, 0.0))
    L = (abs(a.x - b.x) / 2 + 0.2) * size
    B.add(g.box(mid, (2 * L, 0.05, 0.06)), "wood_grey", False)
    bands = None
    for x in (-L + 0.03, -L * 0.45, L * 0.45, L - 0.03):
        bands = g.merge(bands, g.box(mid + Vector((x, 0, 0)), (0.03, 0.058, 0.068)))
    B.add(bands, "metal_iron", False)
    B.add(g.merge(g.box(mid + Vector((-L - 0.006, 0, 0)), (0.014, 0.056, 0.066)), g.box(mid + Vector((L + 0.006, 0, 0)), (0.014, 0.056, 0.066))), F.thread, False)
    F.bar = (mid, L)


def back_chair(B, F, size):
    """The chair it has sat in all night: its back stands high behind."""
    _chair(B, back=0.36 + 0.62 * size, w=0.15)


def aura_veils(B, F, size):
    """The air in front of it stands thick and still, and lamp smoke bends away from either end of it."""
    mid, L = getattr(F, "bar", (Vector((0, -0.25, F.zsh - 0.1)), 0.4))
    still = None
    for i in range(5):
        x = (-0.7 + 0.35 * i) * L
        still = g.merge(still, sk.strand([mid + Vector((x, -0.02, -0.03)), mid + Vector((x + 0.008, -0.035, -0.16)), mid + Vector((x, -0.025, -0.3 - 0.03 * (i % 2)))], 0.03, n=5, swell=0.5))
    B.add(still, "smoke", True)
    for s in (1, -1):
        b = mid + Vector((s * (L + 0.05), 0.0, -0.12))
        smoke = sk.strand(sk.curve([b, b + Vector((s * 0.01, 0, 0.14)), b + Vector((s * 0.09, 0, 0.27)), b + Vector((s * 0.2, 0, 0.3))], n=3), 0.04, n=5, swell=0.4)
        B.move("sway", "smoke", [(smoke, "smoke", True)], b, side="l" if s > 0 else "r")


def aura_breath(B, F, size):
    """Your breath shows when it is near."""
    c = F.P(F.hood_at(0, -0.17, 0.63))
    geo = None
    for i, (dy, dz, r) in enumerate(((0.0, 0.0, 0.018), (-0.06, 0.02, 0.026), (-0.13, 0.055, 0.034))):
        geo = g.merge(geo, sk.cloud([(c + Vector((0.012 * i, dy * size, dz * size)), r * size * 1.2, (1.2, 1.0, 0.8)), (c + Vector((0.012 * i + r, dy * size - r * 0.5, dz * size + r * 0.3)), r * size * 0.8)], res=0.012))
    B.move("bob", "breath", [(geo, "veil", True)], c)


def aura_stubs(B, F, size):
    """The candles it has burned through."""
    for i, (x, y, h) in enumerate(((0.26, -0.2, 0.02), (0.3, -0.1, 0.035), (-0.27, -0.16, 0.025))):
        B.add(g.lathe([(0.024, 0.0), (0.025, h * 0.85), (0.016, h)], n=7, centre=(x, y, 0.02)), "accent_pale", True)
        B.add(sk.disc((x, y, 0.012), 0.04, thick=0.01, n=8), "accent_dark", False)


STYLES = {
    ("legs", "stilts"): legs_stilts, ("legs", "back"): legs_back, ("legs", "roots"): legs_roots,
    ("ground", "long"): ground_long, ("ground", "cohort"): ground_cohort, ("ground", "ring"): ground_ring, ("ground", "wall"): ground_wall,
    ("ground", "sill"): ground_sill, ("ground", "bed"): ground_bed,
    ("wears", "mantle"): wears_mantle, ("wears", "collar"): wears_collar, ("wears", "script"): wears_script, ("wears", "cape"): wears_cape,
    ("wears", "shawl"): wears_shawl, ("wears", "rime"): wears_rime,
    ("chest", "maw"): chest_maw, ("chest", "keyhole"): chest_keyhole, ("chest", "cold-hand"): chest_cold_hand, ("chest", "core"): chest_core,
    ("face", "mask"): face_mask,
    ("shoulder", "face"): shoulder_face, ("shoulder", "face-crowned"): shoulder_face_crowned,
    ("head", "ear"): head_ear, ("head", "prow"): head_prow,
    ("holds", "lamp"): holds_lamp, ("holds", "lamp-low"): holds_lamp_low, ("holds", "dark-lamp"): holds_dark_lamp, ("holds", "glow"): holds_glow,
    ("holds", "book"): holds_book, ("holds", "chain"): holds_chain, ("holds", "blade"): holds_blade, ("holds", "bar"): holds_bar,
    ("back", "chair"): back_chair,
    ("aura", "veils"): aura_veils, ("aura", "breath"): aura_breath, ("aura", "stubs"): aura_stubs,
}
SLOTS = ("legs", "ground", "back", "wears", "chest", "face", "shoulder", "head", "holds", "aura")
# what each kind of thing can have: a door or a tree that inherits a mantle from its parent leaves it off
EVERY = set(SLOTS)
CAN = {"figure": EVERY, "hatch": EVERY - {"legs", "holds", "ground"}, "seated": {"ground", "back", "wears", "shoulder", "holds", "aura"}, "robed": {"ground", "back", "wears", "holds", "aura"},
       "door": {"aura"}, "blot": set()}
# the plans whose hands are given where they are
FINAL_HANDS = ("seated", "robed", "door", "hatch", "human", "streak", "corner", "tree")


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
