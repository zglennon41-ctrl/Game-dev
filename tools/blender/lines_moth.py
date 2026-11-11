"""WILDLINE genius lines, the Moth: a soul standing outside the body, in the plainest picture
of that there is (in Greek one word, psyche, is the soul and the moth). docs/genius-lines.md,
"The Moth", says what its `body` may say.

    python tools/blender/genius_lines.py moth
    python tools/blender/genius_lines.py moth moth-candle moth-emperor moth-moon
    python tools/blender/lines_moth.py gifts        # what a hybrid wears of it (dust-wings, antennae)
    python tools/blender/lines_moth.py body         # bodies/beast-moth.glb: the plain moth

It has no rig. Its anatomy is a moth's and is sound: a head with two great eyes, a coiled
tongue and two feathered feelers; a furred thorax that bears six legs and two pairs of wings;
an abdomen in rings. One thing is a magical choice, made on purpose: it is the size of an owl
and it floats in the field, so it may hold its wings still and its body upright, with its
wings spread to be read. A wing is its canvas: a sheet in a grid of cells (along it, across
it), each cell a material, so a bar follows the wing's own curve and a hole is a cell left
out; an eye-spot is a stack of discs laid on it. The pieces the game moves are named for it
(genius_lines.moving): wings beat or glide about their roots, the head turns, the eyes blink,
the feelers and the tails sway, the abdomen breathes, its dust rises and falls.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE, STAND  # noqa: E402
import genius_forms2 as f2  # noqa: E402
import genius_homes as gh  # noqa: E402
import style  # noqa: E402

GL = None       # genius_lines, whichever name it was loaded under (register)


def _r(ramp, step, rough=0.85):
    return (tuple(style.ramp(ramp, step)[:3]), rough, 0.0)


# what the Moth is made of that the kit's palette did not have (each on a ramp of its class)
PALETTE.update({
    "scale_white": _r("bone", 4), "scale_cream": _r("bone", 3), "scale_black": _r("ink", 1), "scale_ash": _r("stone", 3), "scale_ash_pale": _r("stone", 4),
    "scale_grey": _r("slate", 3), "wood_bark": _r("stone", 1), "wood_beam": _r("umber", 2), "wood_twig": _r("umber", 1), "tongue_dark": _r("umber", 1, 0.5),
    "bristle_leg": _r("ink", 3, 0.6), "cloth_silk": _r("bone", 3, 0.6), "thread_silk": _r("bone", 4, 0.5), "dust_pale": _r("bone", 4), "smoke_grey": _r("slate", 3),
    "wax_comb": _r("ochre", 3, 0.5), "wax_comb_dark": _r("ochre", 1, 0.5), "bone_skull": _r("bone", 4, 0.6), "paper_chart": _r("bone", 3), "stone_mortar": _r("stone", 4),
})

HARD = ("metal", "glass", "wood", "bone", "claw", "wax", "paper", "stone")       # what keeps its planes; the rest is shaded round
EPS = 0.0022        # how far one layer of a wing's pattern stands off the one under it
TH = 0.007          # how thick a wing is


def log(*a):
    print("[lines_moth]", *a)


def opt(v, default_size=1.0):
    if v is None or v is False:
        return None, 0.0
    if isinstance(v, (list, tuple)):
        return v[0], float(v[1]) if len(v) > 1 else default_size
    return v, default_size


def names(v):
    """A slot that holds several styles: "bars" or ["bars", "singe"]."""
    if not v:
        return []
    return [v] if isinstance(v, str) else list(v)


def cr(pts, s):
    """The point s (0..1) of the way along a smooth curve through pts."""
    n = len(pts) - 1
    x = min(max(s, 0.0), 1.0) * n
    i = min(int(x), n - 1)
    t = x - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n)]
    return 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * (t * t) + (3 * p1 - p0 - 3 * p2 + p3) * (t ** 3))


def rnd(i, k=1.0):
    """A number in 0..k that is the same every build (nothing here is drawn by chance)."""
    return k * ((math.sin(i * 12.9898 + 4.1414) * 43758.5453) % 1.0)


# ======================================================================================
# A wing: a sheet in a grid of cells
# ======================================================================================

# Outlines, in lengths of the forewing, from the forewing's root: u out along the wing, v toward
# the head. lead and trail run from the root to the outer margin; bulge rounds that margin out
# (or hooks it, below nothing); scallop (how deep, how many) notches it.
def _w(lead, trail, bulge=0.0, scallop=(0.0, 4), ns=11, nt=6):
    return {"lead": [Vector(p) for p in lead], "trail": [Vector(p) for p in trail], "bulge": bulge, "scallop": scallop, "ns": ns, "nt": nt}


_HIND = _w([(0, -0.1), (0.3, -0.2), (0.55, -0.34), (0.66, -0.45)], [(0, -0.2), (0.08, -0.42), (0.2, -0.62), (0.3, -0.72)], 0.14, ns=8)
_HIND_BROAD = _w([(0, -0.1), (0.35, -0.22), (0.66, -0.36), (0.8, -0.5)], [(0, -0.22), (0.1, -0.5), (0.26, -0.76), (0.4, -0.88)], 0.2, ns=9)

WINGS = {
    # the Candle-moth's: a plain rounded triangle, a tiger moth's
    "delta": (_w([(0, 0.07), (0.45, 0.2), (0.82, 0.25), (1.0, 0.2)], [(0, -0.06), (0.35, -0.2), (0.62, -0.33), (0.74, -0.4)], 0.07), _HIND),
    "ragged": (_w([(0, 0.07), (0.45, 0.2), (0.82, 0.25), (1.0, 0.2)], [(0, -0.06), (0.35, -0.2), (0.62, -0.33), (0.74, -0.4)], 0.08, (0.085, 3)),
               dict(_HIND, scallop=(0.09, 3))),
    "tiger": (_w([(0, 0.06), (0.45, 0.2), (0.85, 0.24), (1.08, 0.16)], [(0, -0.06), (0.4, -0.18), (0.75, -0.26), (0.92, -0.26)], 0.1),
              _w([(0, -0.1), (0.3, -0.2), (0.55, -0.32), (0.7, -0.42)], [(0, -0.2), (0.1, -0.44), (0.24, -0.64), (0.36, -0.74)], 0.16, ns=8)),
    "swept": (_w([(0, 0.05), (0.45, 0.14), (0.85, 0.1), (1.1, -0.02)], [(0, -0.07), (0.3, -0.16), (0.5, -0.24), (0.62, -0.3)], -0.05),
              _w([(0, -0.08), (0.25, -0.18), (0.42, -0.27), (0.5, -0.34)], [(0, -0.16), (0.06, -0.3), (0.14, -0.4), (0.2, -0.46)], 0.06, ns=6)),
    # the Emperor's: broad and round, a place for an eye
    "broad": (_w([(0, 0.08), (0.5, 0.3), (0.88, 0.36), (1.02, 0.28)], [(0, -0.08), (0.4, -0.24), (0.72, -0.36), (0.86, -0.4)], 0.1), _HIND_BROAD),
    "owl": (_w([(0, 0.1), (0.4, 0.38), (0.7, 0.52), (0.8, 0.7)], [(0, -0.06), (0.45, -0.16), (0.8, -0.2), (0.98, -0.16)], 0.16),
            _w([(0, -0.1), (0.4, -0.18), (0.75, -0.26), (0.92, -0.4)], [(0, -0.22), (0.12, -0.5), (0.32, -0.74), (0.5, -0.84)], 0.22, ns=9)),
    "four": (_w([(0, 0.06), (0.3, 0.2), (0.62, 0.28), (0.86, 0.22)], [(0, -0.04), (0.3, -0.14), (0.6, -0.18), (0.84, -0.12)], 0.2, ns=9),
             _w([(0, -0.08), (0.3, 0.06), (0.62, 0.14), (0.86, 0.08)], [(0, -0.18), (0.3, -0.28), (0.6, -0.32), (0.84, -0.26)], 0.2, ns=9)),
    "lintel": (_w([(0, 0.2), (0.5, 0.27), (1.0, 0.28), (1.3, 0.28)], [(0, 0.0), (0.4, 0.02), (0.9, 0.06), (1.3, 0.1)], 0.0, ns=10, nt=4),
               _w([(0, -0.04), (0.4, 0.0), (0.8, 0.02), (1.02, 0.02)], [(0, -0.24), (0.2, -0.7), (0.6, -0.92), (0.92, -0.8)], 0.07, ns=9)),
    "under": (_w([(0, 0.06), (0.45, 0.16), (0.85, 0.18), (1.05, 0.12)], [(0, -0.07), (0.35, -0.2), (0.62, -0.3), (0.76, -0.36)], 0.05),
              dict(_HIND, bulge=0.17)),
    "wall": (_w([(0, 0.1), (0.3, 0.36), (0.7, 0.4), (0.96, 0.4)], [(0, -0.07), (0.35, -0.12), (0.7, -0.12), (0.96, -0.12)], 0.0, ns=9),
             _w([(0, -0.1), (0.35, -0.14), (0.7, -0.14), (0.96, -0.14)], [(0, -0.24), (0.3, -0.62), (0.7, -0.66), (0.96, -0.66)], 0.0, ns=9)),
    "atlas": (_w([(0, 0.08), (0.45, 0.32), (0.82, 0.46), (1.14, 0.52)], [(0, -0.08), (0.4, -0.24), (0.7, -0.3), (0.9, -0.2)], -0.1, ns=12), _HIND_BROAD),
    "long": (_w([(0, 0.06), (0.4, 0.18), (0.8, 0.16), (1.15, 0.0)], [(0, -0.08), (0.35, -0.22), (0.7, -0.34), (0.95, -0.4)], 0.05, (0.04, 4), ns=12),
             _w([(0, -0.1), (0.3, -0.24), (0.55, -0.42), (0.68, -0.62)], [(0, -0.2), (0.08, -0.5), (0.2, -0.82), (0.32, -1.02)], 0.1, (0.05, 3), ns=9)),
    # the Moon-moth's: long in the hindwing, and tailed
    "tailed": (_w([(0, 0.08), (0.5, 0.28), (0.85, 0.36), (1.0, 0.38)], [(0, -0.08), (0.4, -0.22), (0.7, -0.3), (0.84, -0.3)], -0.05),
               _w([(0, -0.1), (0.3, -0.2), (0.55, -0.3), (0.68, -0.42)], [(0, -0.2), (0.1, -0.45), (0.22, -0.66), (0.3, -0.8)], 0.1, ns=8)),
    "narrow": (_w([(0, 0.05), (0.4, 0.14), (0.8, 0.16), (1.05, 0.1)], [(0, -0.06), (0.4, -0.14), (0.78, -0.14), (0.98, -0.08)], 0.07),
               _w([(0, -0.08), (0.3, -0.16), (0.6, -0.26), (0.78, -0.38)], [(0, -0.16), (0.2, -0.3), (0.45, -0.42), (0.62, -0.5)], 0.07, ns=8)),
    "psyche": (_w([(0, 0.08), (0.45, 0.3), (0.8, 0.4), (1.0, 0.4)], [(0, -0.06), (0.4, -0.16), (0.74, -0.2), (0.92, -0.16)], 0.14, ns=12),
               _w([(0, -0.1), (0.35, -0.2), (0.62, -0.3), (0.78, -0.42)], [(0, -0.22), (0.12, -0.48), (0.3, -0.68), (0.46, -0.76)], 0.2, ns=9)),
    "chart": (_w([(0, 0.12), (0.25, 0.32), (0.7, 0.34), (1.05, 0.34)], [(0, -0.16), (0.25, -0.48), (0.7, -0.52), (1.05, -0.52)], 0.0, ns=12, nt=8), None),
    "quills": (None, None), "fans": (None, None),       # made of plumes, not of a sheet (Moth.plumes)
}

# How the wings are held: how far each is swept back about its own root and how far it is
# raised, in degrees (fore, hind); how far its tip droops; hind: how much of the hindwing shows.
HOLDS = {
    "v": dict(sf=-8, sh=4, df=26, dh=20, droop=0.04), "flat": dict(sf=-14, sh=0, df=6, dh=4, droop=0.07),
    "spread": dict(sf=-2, sh=0, df=2, dh=2, droop=0.02), "cross": dict(sf=-34, sh=42, df=6, dh=4, droop=0.04),
    "tent": dict(sf=62, sh=58, df=-34, dh=-30, droop=0.1), "shut": dict(sf=58, sh=30, df=-44, dh=-24, droop=0.06),
    "cape": dict(sf=72, sh=62, df=-26, dh=-20, droop=0.12), "back": dict(sf=58, sh=50, df=-12, dh=-10, droop=0.05),
    "high": dict(sf=-6, sh=6, df=58, dh=50, droop=0.0), "flash": dict(sf=-44, sh=8, df=32, dh=6, droop=0.04),
    "press": dict(sf=0, sh=0, df=0, dh=0, droop=0.0), "offer": dict(sf=-22, sh=0, df=12, dh=8, droop=0.05, lift_l=36),
    "droop": dict(sf=14, sh=24, df=-20, dh=-26, droop=0.2), "hang": dict(sf=34, sh=52, df=14, dh=10, droop=0.08),
    "swept": dict(sf=30, sh=30, df=12, dh=8, droop=0.03), "dart": dict(sf=48, sh=44, df=30, dh=24, droop=0.0),
    "tee": dict(sf=0, sh=0, df=4, dh=0, droop=0.05), "fan": dict(sf=0, sh=0, df=8, dh=6, droop=0.05),
}
FLAP_MEAN = {"beat": 17.0, "glide": 4.6}       # the game holds a moving wing this far above where it was made, on average


class Wing:
    """One wing of one side: where its cells are, what each is made of, and what is laid on it."""

    def __init__(self, shape, sweep, root_v=0.0):
        self.lead, self.trail = shape["lead"], shape["trail"]
        self.bulge, self.scallop = shape["bulge"], shape["scallop"]
        self.ns, self.nt = shape["ns"], shape["nt"]
        self.sweep = math.radians(sweep)
        self.pivot = (self.lead[0] + self.trail[0]) * 0.5
        mid = lambda s: (cr(self.lead, s) + cr(self.trail, s)) * 0.5
        self.out = (mid(1.0) - mid(0.5)).normalized()
        self.cells = {(i, j): None for i in range(self.ns) for j in range(self.nt)}
        self.rims = {}          # (i, j) -> what the cut edge of that cell is made of, where it is not the cell's own
        self.decals = []        # (points in the wing's plane, material, layer)
        self.moved = {}         # (i, j) -> where that corner of the grid is, when it is not where the grid puts it

    def point(self, i, j):
        return self.moved[(i, j)] if (i, j) in self.moved else self.at(i / self.ns, j / self.nt)

    def bite(self, s, t, r):
        """Cut a round bite out of it about (s, t): the cells in it go, and the corners of the
        cells left on its edge are drawn onto the round. Returns the edge, as points in order."""
        c = self.at(s, t)
        mid = lambda cell: (self.at(cell[0] / self.ns, cell[1] / self.nt) + self.at((cell[0] + 1) / self.ns, (cell[1] + 1) / self.nt)) / 2
        gone = [cell for cell in self.cells if (mid(cell) - c).length < r]
        for cell in gone:
            del self.cells[cell]
        corners = lambda cell: [(cell[0], cell[1]), (cell[0] + 1, cell[1]), (cell[0] + 1, cell[1] + 1), (cell[0], cell[1] + 1)]
        lost = {k for cell in gone for k in corners(cell)}
        kept = {k for cell in self.cells for k in corners(cell)}
        edge = []
        for k in lost & kept:
            d = self.point(*k) - c
            self.moved[k] = c + d.normalized() * r if d.length > 1e-6 else self.point(*k)
            edge.append(self.moved[k])
        edge.sort(key=lambda q: math.atan2((q - c).y, (q - c).x))
        # the edge is an arc, not a ring: begin it after its widest gap
        if len(edge) > 2:
            ang = [math.atan2((q - c).y, (q - c).x) for q in edge]
            gaps = [((ang[(i + 1) % len(ang)] - ang[i]) % (2 * math.pi), i) for i in range(len(ang))]
            start = (max(gaps)[1] + 1) % len(edge)
            edge = edge[start:] + edge[:start]
        near = [cell for cell in self.cells if any(k in lost for k in corners(cell))]
        return c, edge, near

    def raw(self, s, t):
        a, b = cr(self.lead, s), cr(self.trail, s)
        p = a + (b - a) * t
        w = max(0.0, (s - 0.5) / 0.5) ** 2
        if self.bulge:
            p = p + self.out * (self.bulge * math.sin(math.pi * t) * w)
        if self.scallop[0]:
            p = p - self.out * (self.scallop[0] * abs(math.sin(math.pi * self.scallop[1] * t)) * w)
        return p

    def at(self, s, t):
        """Where (s along it, t across it) is in the wing's plane, swept as it is held."""
        p = self.raw(s, t) - self.pivot
        c, sn = math.cos(self.sweep), math.sin(self.sweep)
        return Vector((p.x * c + p.y * sn, -p.x * sn + p.y * c)) + self.pivot

    def paint(self, fn):
        """fn(s, t, i, j) for the middle of every cell: a material, None to leave it, False to cut it out."""
        for (i, j) in list(self.cells):
            m = fn((i + 0.5) / self.ns, (j + 0.5) / self.nt, i, j)
            if m is False:
                del self.cells[(i, j)]
            elif m is not None:
                self.cells[(i, j)] = m

    def disc(self, s, t, r, material, layer=1, squash=1.0, turn=0.0, n=10, off=(0.0, 0.0)):
        c = self.at(s, t) + Vector(off)
        pts = []
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = r * math.cos(a), r * squash * math.sin(a)
            pts.append(c + Vector((x * math.cos(turn) - y * math.sin(turn), x * math.sin(turn) + y * math.cos(turn))))
        self.decals.append((pts, material, layer))

    def eye(self, s, t, r, rings, glint="scale_white"):
        """An eye-spot: rings from the outside in, [(share of r, material), ...], and a point of light in it."""
        for k, (share, material) in enumerate(rings):
            self.disc(s, t, r * share, material, layer=1 + k)
        if glint:
            self.disc(s, t, r * 0.14, glint, layer=2 + len(rings), n=6, off=(-r * 0.16, r * 0.2))

    def stroke(self, st, width, material, layer=1, flat=False):
        """A line drawn on it through points given as (s, t) (flat: as points of its plane)."""
        pts = [Vector(q) for q in st] if flat else [self.at(s, t) for s, t in st]
        left, right = [], []
        for k, p in enumerate(pts):
            d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            nrm = Vector((-d.y, d.x)) * (width / 2)
            left.append(p + nrm)
            right.append(p - nrm)
        self.decals.append((left + right[::-1], material, layer))


def prism(top, bot):
    """A closed slab from two matching rings of points."""
    n = len(top)
    verts = list(top) + list(bot)
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for k in range(n):
        faces.append((k, (k + 1) % n, n + (k + 1) % n, n + k))
    return verts, faces


class Raw:
    """A mesh made face by face, each face wound to look the way it is told to, of as many
    materials as it likes: a wing's sheets and what is laid on them, the rings of an abdomen.
    (The kit's own objects are one material each and guess which way is out; a thin sheet
    gives them nothing to guess by.)"""

    def __init__(self):
        self.verts, self.faces, self.fmat, self.mats = [], [], [], []

    def v(self, p):
        self.verts.append(Vector(p))
        return len(self.verts) - 1

    def face(self, ids, want, m):
        a, b, c = self.verts[ids[0]], self.verts[ids[1]], self.verts[ids[2]]
        nrm = (b - a).cross(c - a)
        if nrm.length < 1e-12 and len(ids) > 3:
            nrm = (self.verts[ids[2]] - self.verts[ids[1]]).cross(self.verts[ids[3]] - self.verts[ids[1]])
        if m not in self.mats:
            self.mats.append(m)
        self.faces.append(tuple(ids) if nrm.dot(want) >= 0 else tuple(reversed(ids)))
        self.fmat.append(self.mats.index(m))

    def sheet(self, top, bot, cells, rims, up):
        """A wing's sheet: its upper face, its under face and its cut edges (up: the way its upper face looks)."""
        vid = {}

        def v(layer, i, j):
            key = (layer, i, j)
            if key not in vid:
                vid[key] = self.v((top if layer == 0 else bot)[i][j])
            return vid[key]

        for (i, j), m in cells.items():
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            self.face([v(0, *c) for c in corners], up, m)
            self.face([v(1, *c) for c in corners], -up, m)
            centre = sum((top[a][b] for a, b in corners), Vector()) / 4
            for k, (di, dj) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
                if (i + di, j + dj) in cells:
                    continue
                p, q = corners[k], corners[(k + 1) % 4]
                if (top[p[0]][p[1]] - top[q[0]][q[1]]).length < 1e-6:
                    continue
                mid = (top[p[0]][p[1]] + top[q[0]][q[1]]) / 2
                self.face([v(0, *p), v(0, *q), v(1, *q), v(1, *p)], mid - centre, rims.get((i, j), m))

    def plate(self, top, bot, up, m):
        """A flat shape laid on a sheet, seen from both sides (its edge is too thin to need making)."""
        self.face([self.v(p) for p in top], up, m)
        self.face([self.v(p) for p in bot], -up, m)

    def rings(self, rings, mats, cap=True):
        """Rings of points bridged in order, the band between each two its own material."""
        n = len(rings[0])
        ids = [[self.v(p) for p in ring] for ring in rings]
        cs = [sum(ring, Vector()) / n for ring in rings]
        for i in range(len(rings) - 1):
            for k in range(n):
                quad = [ids[i][k], ids[i][(k + 1) % n], ids[i + 1][(k + 1) % n], ids[i + 1][k]]
                mid = sum((self.verts[q] for q in quad), Vector()) / 4
                self.face(quad, mid - (cs[i] + cs[i + 1]) / 2, mats[i])
        if cap:
            self.face(ids[0], cs[0] - cs[1], mats[0])
            self.face(ids[-1], cs[-1] - cs[-2], mats[-1])

    def object(self, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.verts], [], self.faces)
        me.update()
        for m in self.mats:
            me.materials.append(M_(m) if isinstance(m, str) else m)
        for p, k in zip(me.polygons, self.fmat):
            p.material_index = k
            p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        return ob


def finish(ob, sharp=False):
    """What is soft is shaded round and what is hard keeps its planes; and a sheet is not
    shaded round its own edge."""
    me = ob.data
    for p in me.polygons:
        nm = me.materials[p.material_index].name if me.materials else ""
        p.use_smooth = not nm.startswith(HARD)
    if sharp:
        me.set_sharp_from_angle(angle=0.95)
    return ob


def M_(name):
    """A material by name: the field's by field_<what>."""
    return field(name[6:], 2.6) if name.startswith("field_") else mat(name)


def piece(kind, what, items, pivot, side="", n=None, parent=None, raws=()):
    """A piece the game moves by its name (genius_lines.moving), made here so that a wing's
    sheet (already an object) can be part of it. kind None: a piece that does not move."""
    if kind is None:
        name = what
    else:
        assert kind in GL.MOVES, kind
        name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else "")
    objs = [g.to_object("%s_%d" % (name, i), geo, M_(m) if isinstance(m, str) else m, True) for i, (geo, m) in enumerate(items) if geo and geo[0]]
    ob = g.join(name, list(objs) + list(raws))
    finish(ob, sharp=bool(raws))
    GL.set_origin(ob, pivot)
    if parent is not None:
        GL.child_of(ob, parent)
    return ob


def twin(src, kind, what, side="", n=None, parent=None):
    """The other of a pair: the same mesh again, its piece mirrored across the body (a model
    carries one wing, one feeler, one eye, and each twice). A twin is turned by the game as
    its original is and the mirror makes the turn its own side's; so a pair that must turn
    opposite ways about the way the body faces (wings: beat, glide) is named by number, not
    by side: beat_wing_0 and its twin beat_wing_1."""
    if kind is None:
        name = what
    else:
        assert kind in GL.MOVES, kind
        name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else "")
    ob = bpy.data.objects.new(name, src.data)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.update()
    ob.matrix_world = Matrix.Scale(-1, 4, X) @ src.matrix_world
    if parent is not None:
        GL.child_of(ob, parent)
    return ob


def ribbon(points, widths, twists, thick=0.006):
    """A flat band through points, turning about its own length: a tail, a train."""
    pts = [V(p) for p in points]
    rings = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = d.cross(Z)
        side = side.normalized() if side.length > 1e-4 else X.copy()
        up = side.cross(d).normalized()
        c, s = math.cos(twists[i]), math.sin(twists[i])
        a, b = side * c + up * s, up * c - side * s
        w = widths[i] / 2
        rings.append([p + a * w, p + b * (thick / 2), p - a * w, p - b * (thick / 2)])
    return g.loft(rings, caps=True)


def mirror_items(items):
    return [(g.mirrored(geo), m) for geo, m in items]


# ======================================================================================
# The moth
# ======================================================================================

AGE = {1: dict(head=1.2, wing=0.9, body=0.95), 2: dict(head=1.12, wing=0.94, body=0.96), 3: dict(head=1.0, wing=1.0, body=1.0), 4: dict(head=0.95, wing=1.05, body=1.05)}
BROWS = {"keen": (0.012, 0.016, 0.004), "stern": (-0.006, 0.01, 0.012), "calm": (0.0, 0.004, 0.0), "wide": (0.014, 0.02, 0.012)}


class Moth:
    def __init__(self, form_id, level, spec, plain=False):
        kit.reset()
        self.id, self.level, self.spec, self.plain = form_id, level, spec, plain
        b = spec.get("build", {})
        age = AGE[level]
        self.k = float(b.get("body", 1.0)) * age["body"]
        self.kh = self.k ** 0.5 * age["head"] * float(b.get("head", 1.0))
        self.L = 0.38 * float(b.get("span", 1.0)) * age["wing"]
        self.pitch = math.radians(float(spec.get("pitch", 40)))
        self.C = Vector((0, 0, 0.34))
        self.M = Matrix.Translation(self.C) @ Matrix.Rotation(-self.pitch, 4, "X")
        # the head keeps its eyes forward whatever the body does: it follows the body a third of the way
        self.nod = max(math.radians(-22), min(math.radians(26), self.pitch * 0.3))
        self.yaw = math.radians({"back": -98, "left": 30, "down": 0}.get(spec.get("look", ""), 0))
        self.H = self.M @ Vector((0, -0.118 * self.k, 0.014 * self.k)) + Vector((0, -0.012, 0.012)) * math.sin(max(0.0, self.pitch))
        self.MH = Matrix.Translation(self.H) @ Matrix.Rotation(self.yaw, 4, "Z") @ Matrix.Rotation(-self.nod, 4, "X")
        self.objects = []
        self.body_items = []
        self.root = None            # the piece everything hangs from, where the whole of it sways
        self.wing_ob = {}           # side -> the piece its wing is
        self.wing = {}              # (which, side) -> Wing, as it was painted
        self.frames = {}
        self.accent_ok = not plain and bool(spec.get("accent"))

    # --- where things are --------------------------------------------------------------
    def B(self, geo):
        """A geometry made in the body's own frame (head to -Y, back to +Z), where the body is."""
        return g.moved(geo, self.M)

    def Hd(self, geo):
        return g.moved(geo, self.MH)

    def ac(self, name, plain_name="fur_ruff"):
        """A Path's colour, or what stands in for it on a body with none (the plain moth)."""
        return name if self.accent_ok else plain_name

    # --- the wings ---------------------------------------------------------------------
    def wing_frame(self, which, side):
        hold = HOLDS[self.spec.get("hold", "v")]
        flap = self.spec.get("flap", "beat")
        dih = hold["df" if which == "fore" else "dh"] - FLAP_MEAN.get(flap, 0.0)
        if side == "l" and "lift_l" in hold:
            dih += hold["lift_l"]
        dih = math.radians(dih)
        k = self.k
        root = Vector((0.046 * k, -0.035 * k, 0.046 * k))
        eu = Vector((math.cos(dih), 0, math.sin(dih)))
        ev = Vector((0, -1, 0))
        en = Vector((-math.sin(dih), 0, math.cos(dih)))
        return root, eu, ev, en, hold["droop"]

    def W(self, frame, p, off=0.0):
        """A point of a wing's plane (in lengths of the forewing), in the body's frame."""
        root, eu, ev, en, droop = frame
        x, y = p.x * self.L, p.y * self.L
        return root + eu * x + ev * y + en * (off - droop * x * x / self.L)

    def wing_objects(self, side):
        """The sheets of one side's wings and what is laid on them, in the world: ([object], [])."""
        raw = Raw()
        sgn = 1 if side == "l" else -1
        flip = (lambda p: p) if sgn > 0 else (lambda p: Vector((-p.x, p.y, p.z)))
        for which in ("fore", "hind"):
            w = self.wing.get((which, side))
            if w is None or not w.cells:
                continue
            fr = self.wing_frame(which, side)
            lower = 0.0 if which == "fore" else -TH * 0.9       # the hindwing lies under the forewing
            top = [[flip(self.M @ self.W(fr, w.point(i, j), TH / 2 + lower)) for j in range(w.nt + 1)] for i in range(w.ns + 1)]
            bot = [[flip(self.M @ self.W(fr, w.point(i, j), -TH / 2 + lower)) for j in range(w.nt + 1)] for i in range(w.ns + 1)]
            up = flip((self.M.to_3x3() @ fr[3]).normalized())
            cells = {c: (m or ("fur_dark" if which == "fore" else "fur_light")) for c, m in w.cells.items()}
            raw.sheet(top, bot, cells, w.rims, up)
            for pts, material, layer in w.decals:
                raw.plate([flip(self.M @ self.W(fr, p, TH / 2 + lower + layer * EPS)) for p in pts],
                          [flip(self.M @ self.W(fr, p, -TH / 2 + lower - layer * EPS)) for p in pts], up, material)
        return ([raw.object("wings_" + side)] if raw.faces else []), []

    def wing_root(self, side):
        p = self.M @ self.wing_frame("fore", side)[0]
        return p if side == "l" else Vector((-p.x, p.y, p.z))

    def uneven(self):
        """Whether its two sides differ (a burn on one wing, one wing held up): then each is made."""
        return bool(opt(self.spec.get("burn"))[0]) or "lift_l" in HOLDS[self.spec.get("hold", "v")]

    def pair(self, flap, make):
        """The two wings from make(side) -> (items, raws): one made and its twin, or both made where they differ."""
        root = self.wing_root("l")
        kind = flap if flap in ("beat", "glide") else None
        if self.uneven():
            for side in ("l", "r"):
                items, raws = make(side)
                ob = piece(kind, "wing" if kind else "wings_" + side, items, self.wing_root(side), side=side if kind else "", raws=raws, parent=self.root)
                self.wing_ob[side] = ob
                self.objects.append(ob)
            return
        items, raws = make("l")
        left = piece(kind, "wing" if kind else "wings_l", items, root, n=0 if kind else None, raws=raws, parent=self.root)
        right = twin(left, kind, "wing" if kind else "wings_r", n=1 if kind else None, parent=self.root)
        self.wing_ob = {"l": left, "r": right}
        self.objects += [left, right]

    def make_wings(self):
        shape, size = opt(self.spec.get("wings"), 1.0)
        if not shape:
            return
        self.L *= size
        hold = HOLDS[self.spec.get("hold", "v")]
        flap = self.spec.get("flap", "beat")
        if shape in ("quills", "fans"):
            return self.pair(flap, lambda side: (self.plumes(shape, side), []))
        fore, hind = WINGS[shape]
        for side in (("l", "r") if self.uneven() else ("l",)):
            self.wing[("fore", side)] = Wing(fore, hold["sf"])
            if hind is not None and self.spec.get("hold") != "tent":
                self.wing[("hind", side)] = Wing(hind, hold["sh"])
            paint_wings(self, side)

        def make(side):
            raws, items = self.wing_objects(side)
            return items + self.wing_extras(side), raws
        self.pair(flap, make)

    def wing_extras(self, side):
        """What rides a wing that is not its sheet: the rolled end of a chart."""
        return roll(self, side) if "chart" in names(self.spec.get("pattern")) else []

    def plumes(self, shape, side):
        """Wings that have come apart into quills: each a shaft, a narrow vane and a tip dipped in ink."""
        many = shape == "fans"
        angles = [58 - 128 * i / 11 for i in range(12)] if many else [10, -3, -17, -29, -41]
        lengths = [0.78 + 0.3 * math.sin(math.pi * (i + 0.5) / 12) for i in range(12)] if many else [1.0, 0.96, 0.82, 0.72, 0.6]
        ruled = "ruled" in names(self.spec.get("pattern"))
        fr = self.wing_frame("fore", side)
        shafts, vanes, tips, rules, bars = None, None, None, None, None
        for i, (ang, ln) in enumerate(zip(angles, lengths)):
            a = math.radians(ang)
            d = Vector((math.cos(a), math.sin(a)))
            nrm = Vector((-d.y, d.x))
            r0 = Vector((0.03, 0.02 - 0.012 * i * (0.45 if many else 1.0)))
            pt = lambda t, o=0.0, q=0.0: self.M @ self.W(fr, r0 + d * (ln * t) + nrm * q, o + (0.004 if i % 2 else 0.0))
            shafts = g.merge(shafts, g.tube([pt(0.0), pt(0.5), pt(1.0)], [0.0055, 0.004, 0.0015], n=4))
            wv = 0.05 if many else 0.062

            def slab(ring, o):
                topv = [pt(t, o, q) for t, q in ring] + [pt(t, o, -q) for t, q in ring[-2:0:-1]]
                botv = [pt(t, -o, q) for t, q in ring] + [pt(t, -o, -q) for t, q in ring[-2:0:-1]]
                return prism(topv, botv)
            vanes = g.merge(vanes, slab([(0.14, 0.0), (0.3, wv), (0.62, wv * 1.15), (0.84, wv * 0.8), (0.9, 0.0)], 0.003))
            tips = g.merge(tips, slab([(0.8, 0.0), (0.84, wv * 0.86), (0.93, wv * 0.5), (1.0, 0.0)], 0.0045))
            bars = g.merge(bars, slab([(0.33, 0.0), (0.34, wv * 1.04), (0.46, wv * 1.12), (0.47, 0.0)], 0.0055))
            if ruled:
                for t in (0.56, 0.66, 0.76):
                    rules = g.merge(rules, slab([(t - 0.002, 0.0), (t, wv * 1.08), (t + 0.025, wv * 1.05), (t + 0.027, 0.0)], 0.0055))
        items = [(shafts, "bone"), (vanes, "fur_light"), (tips, "scale_black"), (bars, self.ac("accent")), (rules, self.ac("accent_dark", "fur_dark"))]
        return items if side == "l" else mirror_items(items)

    # --- the tails of a hindwing ---------------------------------------------------------
    def make_tails(self):
        style_, size = opt(self.spec.get("tails"), 1.0)
        if not style_ or ("hind", "l") not in self.wing:
            return
        length = 0.3 * size
        w = self.wing[("hind", "l")]
        fr = self.wing_frame("hind", "l")
        a2 = w.at(1.0, 0.72)
        d2 = (w.at(1.0, 0.72) - w.at(0.7, 0.72)).normalized()
        d2 = (d2 + Vector((0.0, -1.2))).normalized() if style_ != "twist" else (d2 + Vector((0.1, -0.5))).normalized()
        nseg = 3 if size > 1.5 else 2
        left, right = self.wing_ob.get("l") or self.root, self.wing_ob.get("r") or self.root
        for n in range(nseg):
            pts, widths, twists = [], [], []
            for q in range(5):
                t = (n + q / 4) / nseg
                bend = 0.05 * math.sin(t * math.pi * 1.5) if style_ == "twist" else 0.0
                p2 = a2 + d2 * (t * length / self.L) + Vector((-d2.y, d2.x)) * bend * (length / self.L)
                pts.append(self.M @ self.W(fr, p2, -TH))
                widths.append(0.016 + 0.03 * (1 - t) ** 2 + (0.034 * math.exp(-((t - 0.88) / 0.09) ** 2) if style_ != "burn" else 0.0))
                twists.append(math.pi * (0.5 if style_ == "twist" else 0.25) * max(0.0, t - 0.25))
            if n == nseg - 1:
                widths[-1] = 0.004
            lit = style_ == "burn" and n >= 1
            material = "field_tail" if lit else (self.ac("accent_light", "fur_light") if n == nseg - 1 else "fur_light")
            items = [(ribbon(pts, widths, twists), material)]
            if n == 0 and self.accent_ok:
                items.append((ribbon(pts[:3], [x * 1.12 for x in widths[:3]], twists[:3], thick=0.008), "accent_dark"))
            left = piece("wave", "tail", items, pts[0], side="l", n=n, parent=left)
            right = twin(left, "wave", "tail", side="r", n=n, parent=right)
            self.objects += [left, right]

    # --- the body ----------------------------------------------------------------------
    def make_thorax(self):
        k = self.k
        fur, fsize = opt(self.spec.get("fur"), 1.0)
        coat = {"ash": "scale_ash", "ermine": "scale_white", "ghost": "scale_white"}.get(fur, "fur_ruff")
        it = self.body_items
        it.append((self.B(g.ico((0, 0, 0), 1.0, sub=2, scale=(0.066 * k, 0.094 * k, 0.07 * k))), coat))
        # the collar: a ring of tufts behind the head, and tufts down the back
        n = 11
        ruff, ruff2 = None, None
        thick = {"mane": 1.5, "ermine": 1.45, "ghost": 1.25}.get(fur, 1.0) * fsize
        for i in range(n):
            a = 2 * math.pi * i / n + 0.28
            r = Vector((math.cos(a), 0, math.sin(a)))
            base = Vector((0.052 * k * r.x, -0.066 * k, 0.052 * k * r.z))
            tip = base + r * (0.034 * k * thick) + Vector((0, 0.085 * k * thick, 0))
            bl = g.blade(base, tip, 0.05 * k * thick, normal=r, belly=0.36)
            if i % 2:
                ruff2 = g.merge(ruff2, bl)
            else:
                ruff = g.merge(ruff, bl)
        collar = kit.mark("collar", mat(coat)) if coat == "fur_ruff" else mat(coat)
        it.append((self.B(ruff), collar))
        it.append((self.B(ruff2), coat if fur in ("ermine", "ghost", "ash") else "fur_light"))
        if fur in ("mane", "ermine"):
            more = None
            for i in range(9):
                a = 2 * math.pi * i / 9
                r = Vector((math.cos(a), 0, math.sin(a)))
                base = Vector((0.06 * k * r.x, -0.02 * k, 0.06 * k * r.z))
                more = g.merge(more, g.blade(base, base + r * (0.03 * k * thick) + Vector((0, 0.1 * k * thick, 0)), 0.055 * k * thick, normal=r, belly=0.36))
            it.append((self.B(more), self.ac("accent_dark", "fur_dark") if fur == "mane" else coat))
        tufts = None
        for i in range(3):
            y = (-0.02 + 0.04 * i) * k
            tufts = g.merge(tufts, g.blade((0, y, 0.062 * k), (0, y + 0.06 * k, 0.1 * k - 0.012 * i * k), 0.05 * k, normal=Z, belly=0.4))
        it.append((self.B(tufts), coat))
        if fur in ("ermine", "ghost") and self.accent_ok:        # a band of its Path's colour at the throat, where white would hide it
            it.append((self.B(f2.band((0, -0.084 * k, 0.004 * k), 0.05 * k, 0.05 * k, 0.012 * k, n=12, u=X, v=Z, sides=4)), "accent"))
        if fur == "ermine":     # a judge's fur: the black tips of the tails sewn into it
            spots = None
            for i in range(7):
                a = 2 * math.pi * i / 7 + 0.4
                r = Vector((math.cos(a), 0, math.sin(a)))
                c = Vector((0.074 * k * r.x * thick ** 0.5, 0.012 * k, 0.074 * k * r.z * thick ** 0.5))
                spots = g.merge(spots, g.blade(c, c + r * 0.012 * k + Vector((0, 0.03 * k, 0)), 0.018 * k, normal=r, belly=0.4))
            it.append((self.B(spots), "scale_black"))
        if "skull" in names(self.spec.get("pattern")):
            self.skull()

    def skull(self):
        """The mark on the Honey-thief's back: pale, and a joke."""
        k = self.k
        it = self.body_items
        c = Vector((0, 0.0, 0.07 * k))
        it.append((self.B(g.ico(c, 1.0, sub=1, scale=(0.036 * k, 0.04 * k, 0.012 * k))), "bone_skull"))
        it.append((self.B(g.ico(c + Vector((0, 0.036 * k, -0.004 * k)), 1.0, sub=1, scale=(0.022 * k, 0.02 * k, 0.01 * k))), "bone_skull"))
        holes = None
        for sx in (1, -1):
            holes = g.merge(holes, g.ico(c + Vector((sx * 0.014 * k, -0.006 * k, 0.008 * k)), 1.0, sub=1, scale=(0.0095 * k, 0.011 * k, 0.006 * k)))
        holes = g.merge(holes, g.ico(c + Vector((0, 0.018 * k, 0.007 * k)), 1.0, sub=0, scale=(0.005 * k, 0.008 * k, 0.005 * k)))
        it.append((self.B(holes), "scale_black"))

    def make_legs(self):
        k = self.k
        long_ = opt(self.spec.get("legs"))[0] == "long"
        s = 1.9 if long_ else 1.0
        legs, feet = None, None
        self.hands = {}
        carry = opt(self.spec.get("carry"))[0]
        perch = opt(self.spec.get("perch"))[0]
        for sx in (1, -1):
            for n, (y0, d1, d2, d3) in enumerate((
                    (-0.05, (0.034, -0.032, -0.026), (0.008, -0.05, -0.036), (0.0, -0.03, 0.006)),
                    (-0.008, (0.05, 0.0, -0.03), (0.014, 0.006, -0.056), (0.008, -0.022, -0.008)),
                    (0.034, (0.04, 0.03, -0.026), (0.01, 0.046, -0.05), (0.0, 0.03, -0.008)))):
                p0 = Vector((sx * 0.03 * k, y0 * k, -0.054 * k))
                d1, d2, d3 = [Vector((sx * d[0], d[1], d[2])) * k * s for d in (d1, d2, d3)]
                if n == 0 and carry in ("taper", "snuffers", "dividers", "comb"):       # the front pair holds what it carries
                    d1, d2, d3 = Vector((sx * 0.018, -0.04, -0.02)) * k, Vector((-sx * 0.012, -0.05, -0.006)) * k, Vector((-sx * 0.016, -0.02, 0.0)) * k
                if perch and n > 0:         # the others stand on what it sits on
                    d2 = Vector((d2.x * 1.4, d2.y, d2.z * 0.8))
                    d3 = Vector((sx * 0.02 * k, d3.y * 0.6, -0.004 * k))
                p1, p2, p3 = p0 + d1, p0 + d1 + d2, p0 + d1 + d2 + d3
                legs = g.merge(legs, g.tube([p0, p1, p2, p3], [0.0085 * k, 0.0065 * k, 0.0045 * k, 0.003 * k], n=4))
                feet = g.merge(feet, g.cone(p3, p3 + (d3.normalized() * 0.014 + Vector((0, 0, -0.008))) * k, 0.004 * k, n=3))
                if long_:       # a plume-moth's spurs
                    feet = g.merge(feet, g.cone(p2, p2 + Vector((sx * 0.02, 0.012, 0.004)) * k, 0.003 * k, n=3))
                if n == 0:
                    self.hands[sx] = self.M @ p3
        self.body_items.append((self.B(legs), "bristle_leg"))
        self.body_items.append((self.B(feet), "claw"))

    def make_abdomen(self):
        style_, size = opt(self.spec.get("abdomen", "stout"), 1.0)
        k = self.k
        prof = {"stout": [(0.0, 0.052), (0.2, 0.068), (0.5, 0.066), (0.8, 0.046), (1.0, 0.012)],
                "slim": [(0.0, 0.036), (0.25, 0.044), (0.6, 0.038), (0.85, 0.026), (1.0, 0.007)],
                "bee": [(0.0, 0.05), (0.2, 0.074), (0.5, 0.08), (0.8, 0.056), (1.0, 0.012)]}.get(style_ if style_ in ("slim", "bee") else "stout")
        length = {"slim": 0.26, "bee": 0.25}.get(style_, 0.21) * k * (size if style_ != "bee" else size ** 0.6)
        fat = size ** 0.5 if style_ != "slim" else 1.0
        droop = 0.22
        w0 = Vector((0, 0.066 * k, -0.004 * k))

        def ring_at(t):
            r = 0.0
            for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
                if t0 <= t <= t1:
                    r = r0 + (r1 - r0) * (t - t0) / (t1 - t0)
            c = w0 + Vector((0, length * t, -droop * length * t * t))
            return g.ring(c, r * k * fat, r * k * fat * 0.94, n=8, u=X, v=Z)

        nseg = 6
        if style_ in ("bee", "banded"):
            ma, mb = self.ac("accent", "fur_light"), "scale_black"
        else:
            ma, mb = "fur_light", (self.ac("accent_dark") if self.accent_ok else kit.mark("bands", mat("fur_light")))
        raw = Raw()
        rings, mats = [], []
        for i in range(nseg):
            t0, t1 = i / nseg, (i + 1) / nseg
            tm = t0 + (t1 - t0) * (0.72 if style_ not in ("bee", "banded") else 0.5)
            rings += [[self.M @ p for p in ring_at(t0)], [self.M @ p for p in ring_at(tm)]]
            mats += [ma, mb]
        rings.append([self.M @ p for p in ring_at(1.0)])
        raw.rings(rings, mats)
        items = []
        end = w0 + Vector((0, length, -droop * length))
        if style_ == "fan":         # a fan of scales it steers by
            fan, fan2 = None, None
            for i in range(5):
                a_ = math.radians(-50 + 25 * i)
                tipp = end + Vector((math.sin(a_) * 0.085 * k, math.cos(a_) * 0.09 * k, 0.0))
                bl = g.blade(end - Vector((0, 0.02 * k, 0)), tipp, 0.04 * k, normal=Z, belly=0.6)
                if i % 2:
                    fan2 = g.merge(fan2, bl)
                else:
                    fan = g.merge(fan, bl)
            items += [(self.B(fan), "scale_black"), (self.B(fan2), "scale_white")]
        ob = piece("pulse", "abdomen", items, self.M @ w0, parent=self.root, raws=[raw.object("abdomen")])
        finish(ob, sharp=False)
        self.objects.append(ob)
        self.tail_end = self.M @ end

    def make_head(self):
        kh = self.kh
        eyes, esize = opt(self.spec.get("eyes", "big"), 1.0)
        fur = opt(self.spec.get("fur"))[0]
        special = {"ash": "scale_ash", "ermine": "scale_white", "ghost": "scale_white"}.get(fur)
        face, dark = special or "fur_light", "fur_dark"       # a pale face, so that dark eyes can be seen in it
        re = {"big": 0.036, "small": 0.021, "far": 0.04}.get(eyes, 0.036) * kh * esize
        items = [(self.Hd(g.ico((0, 0, 0), 1.0, sub=3, scale=(0.056 * kh, 0.052 * kh, 0.05 * kh))), face)]
        ex, ey, ez = 0.037 * kh, -0.031 * kh, 0.006 * kh
        # the lids, that stay when it blinks, and a brow over each eye: how it looks at you
        b_in, b_mid, b_out = BROWS.get(self.spec.get("brow", "calm"), BROWS["calm"])
        lids, crest, cheeks = None, None, None
        for sx in (1, -1):
            lids = g.merge(lids, g.ico((sx * ex, ey + 0.004 * kh, ez), re * 0.93, sub=1))
            top = re * 0.98
            lids = g.merge(lids, g.tongue([(sx * (ex - re * 0.95), ey - re * 0.5, ez + top * 0.55 + b_in * kh), (sx * ex, ey - re * 0.9, ez + top * 0.86 + b_mid * kh),
                                           (sx * (ex + re * 0.98), ey - re * 0.3, ez + top * 0.5 + b_out * kh)], [0.016 * kh, 0.022 * kh, 0.012 * kh], thick=0.55, normal=(0, -0.4, 1)))
            cheeks = g.merge(cheeks, g.blade((sx * 0.04 * kh, -0.012 * kh, -0.022 * kh), (sx * 0.075 * kh, 0.004 * kh, -0.05 * kh), 0.034 * kh, normal=(sx * 0.3, -1, 0), belly=0.4))
        items.append((self.Hd(lids), dark))
        items.append((self.Hd(cheeks), face))
        # a cap of darker fur, and a crest behind it
        items.append((self.Hd(g.ico((0, 0.012 * kh, 0.016 * kh), 1.0, sub=2, scale=(0.05 * kh, 0.046 * kh, 0.042 * kh))), special or "fur_ruff"))
        for i in range(3):
            crest = g.merge(crest, g.blade((0, (-0.012 + 0.016 * i) * kh, 0.04 * kh), (0, (0.01 + 0.03 * i) * kh, (0.082 - 0.008 * i) * kh), 0.034 * kh, normal=(0, -1, 0.4), belly=0.4))
        items.append((self.Hd(crest), special or "fur_ruff"))
        if "no-mouth" not in self.spec.get("_features", ()) and self.spec.get("mouth", True):
            palps = None
            for sx in (1, -1):
                palps = g.merge(palps, g.ico((sx * 0.013 * kh, -0.05 * kh, -0.02 * kh), 1.0, sub=1, scale=(0.011 * kh, 0.016 * kh, 0.02 * kh)))
            items.append((self.Hd(palps), "fur_light"))
        if opt(self.spec.get("tongue", "coil"))[0] == "coil" and "no-mouth" not in self.spec.get("_features", ()):
            pts = g.spiral(Vector((0, -0.058 * kh, -0.036 * kh)), 0.015 * kh, 0.004 * kh, 1.6, 0.0, n=12, axis=X, start=math.pi * 0.5)
            items.append((self.Hd(g.tube(pts, [0.0042 * kh] * len(pts), n=4)), "tongue_dark"))
        self.head = piece("turn", "head", items, self.H, parent=self.root)
        self.objects.append(self.head)
        # the eyes: dark and deep, a point of the field in each; they shut
        c = Vector((ex, ey, ez))
        look = Vector((0.16, -0.97, 0.1)).normalized()
        ei = [(self.Hd(g.ico(c, re, sub=2)), "eye_dark"), (self.Hd(g.ico(c + look * re * 0.9, 1.0, sub=1, scale=(re * 0.36, re * 0.17, re * 0.36))), "field_eyes")]
        if eyes == "far":       # a ring round it, as round a glass
            ei.append((self.Hd(f2.band(c + look * re * 0.55, re * 0.78, re * 0.78, re * 0.09, n=10, u=Vector((0.92, 0.3, 0)), v=Z, sides=3)), "metal_brass"))
        left = piece("blink", "eye", ei, self.MH @ c, side="l", parent=self.head)
        self.objects += [left, self.twin_on_head(left, "blink", "eye")]
        self.make_feelers()
        self.make_tongue()

    def twin_on_head(self, left, kind, what):
        """The other of a pair on the head: mirrored across the head's own middle, whichever way the head is turned."""
        ob = twin(left, kind, what, side="r")
        Mh = self.MH
        ob.matrix_world = Mh @ Matrix.Scale(-1, 4, X) @ Mh.inverted() @ left.matrix_world
        GL.child_of(ob, self.head)
        return ob

    def make_feelers(self):
        style_, size = opt(self.spec.get("feelers", "comb"), 1.0)
        kh = self.kh
        s = kh * size * (1.25 if style_ == "thread" else 1.0)
        b0 = Vector((0.022 * kh, -0.022 * kh, 0.042 * kh))
        path = [b0, b0 + Vector((0.026, -0.03, 0.07)) * s, b0 + Vector((0.07, -0.06, 0.125)) * s, b0 + Vector((0.12, -0.072, 0.152)) * s, b0 + Vector((0.162, -0.058, 0.148)) * s]
        if style_ == "thread":
            path.append(b0 + Vector((0.186, -0.03, 0.12)) * s)
        pts = [cr(path, i / 8) for i in range(9)]
        items = [(self.Hd(g.tube(pts, [0.0058 * kh * (1 - 0.08 * i) for i in range(9)], n=4)), "bristle_leg")]
        teeth, teeth2 = None, None
        if style_ in ("feather", "comb"):
            nt = 9 if style_ == "feather" else 7
            for i in range(nt):
                t = 0.12 + 0.84 * i / (nt - 1)
                p = cr(path, t)
                d = (cr(path, min(1.0, t + 0.05)) - cr(path, max(0.0, t - 0.05))).normalized()
                out = d.cross(Vector((0, -1, 0.25))).normalized()
                ln = (0.05 if style_ == "feather" else 0.036) * s * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.08) ** 0.8))
                for sg in ((1, -1) if style_ == "feather" else (-1,)):
                    bl = g.blade(p, p + out * (sg * ln) + d * (ln * 0.45), 0.017 * s, normal=(0, -1, 0.25), belly=0.45)
                    if i % 2:
                        teeth2 = g.merge(teeth2, bl)
                    else:
                        teeth = g.merge(teeth, bl)
            items += [(self.Hd(teeth), self.ac("accent_light", "fur_light")), (self.Hd(teeth2), self.ac("accent", "fur_ruff"))]
        elif style_ == "club":
            items.append((self.Hd(g.ico(pts[-1], 1.0, sub=1, scale=(0.011 * s, 0.011 * s, 0.02 * s), rot=(0.5, 0.6, 0))), self.ac("accent", "fur_ruff")))
        else:
            items.append((self.Hd(g.ico(pts[-1], 0.0075 * s, sub=0)), self.ac("accent_light", "fur_light")))
        left = piece("sway", "feeler", items, self.MH @ b0, side="l", parent=self.head)
        self.objects += [left, self.twin_on_head(left, "sway", "feeler")]

    def make_tongue(self):
        style_, size = opt(self.spec.get("tongue", "coil"), 1.0)
        kh = self.kh
        if "no-mouth" in self.spec.get("_features", ()):
            return
        c = Vector((0, -0.058 * kh, -0.036 * kh))
        if style_ == "out":         # half unrolled: it reaches for the next thing
            pts = [Vector((0, -0.05 * kh, -0.026 * kh)), Vector((0, -0.1 * kh, -0.04 * kh)) * 1.0, Vector((0, -0.2 * kh * size, -0.06 * kh)), Vector((0, -0.27 * kh * size, -0.045 * kh))]
            pts = [cr(pts, i / 8) for i in range(9)] + g.spiral(Vector((0, -0.27 * kh * size, -0.062 * kh)), 0.017 * kh, 0.005 * kh, 1.3, 0.0, n=10, axis=X, start=math.pi / 2)
            geo = g.tube(pts, [0.0066 * kh] * len(pts), n=5)
            self.objects.append(piece("sway", "tongue", [(self.Hd(geo), "tongue_dark")], self.MH @ Vector((0, -0.05 * kh, -0.026 * kh)), parent=self.head))
        elif style_ == "deep":      # three times its own length, carried like a watch-spring
            R = 0.085 * kh * size
            cc = Vector((0, -0.05 * kh - R * 0.55, -0.03 * kh - R * 0.9))
            pts = g.spiral(cc, R, 0.012 * kh, 3.1, 0.0, n=46, axis=X, start=math.pi * 0.35)
            geo = g.tube(pts, [0.0062 * kh * (1 - 0.5 * i / 46) for i in range(47)], n=5)
            hub = g.ico(cc, 0.014 * kh, sub=1)
            self.objects.append(piece("sway", "tongue", [(self.Hd(geo), "tongue_dark"), (self.Hd(hub), "field_spring")], self.MH @ Vector((0, -0.05 * kh, -0.026 * kh)), parent=self.head))

    # --- what is about it ----------------------------------------------------------------
    def make_aura(self):
        style_, size = opt(self.spec.get("aura"), 1.0)
        if not style_:
            return
        L = self.L
        if style_ in ("dust", "embers"):
            for side, sx in (("l", 1), ("r", -1)):
                motes, lit = None, None
                for i in range(6):
                    q = i + (0 if sx > 0 else 11)
                    p = self.C + Vector((sx * (0.07 + rnd(q, 0.55) * L), 0.02 + rnd(q + 3, 0.12), -0.12 - rnd(q + 7, 0.16)))
                    geo = g.ico(p, 0.007 + rnd(q + 5, 0.006), sub=0)
                    if i % 3 == 0:
                        lit = g.merge(lit, geo)
                    else:
                        motes = g.merge(motes, geo)
                items = [(motes, "dust_pale" if style_ == "dust" else "scale_ash"), (lit, "field_dust")]
                self.objects.append(piece("bob", "dust", items, self.C + Vector((sx * 0.2, 0.1, -0.2)), side=side, parent=self.root))
        elif style_ == "rings":       # the shape it leaves on the eye
            items = []
            for i, r in enumerate((0.62, 0.9)):
                items.append((f2.band(self.C + Vector((0, 0.03, -0.02)), L * 1.05 * r, L * 0.9 * r, 0.0065, n=22, u=X, v=Z, sides=3), "field_ring"))
            self.objects.append(piece("pulse", "rings", items, self.C + Vector((0, 0.03, 0)), parent=self.root))
        elif style_ == "halo":
            top = self.H + Vector((0, 0.01, 0.15 * self.kh))
            self.objects.append(piece("bob", "halo", [(f2.band(top, 0.07 * self.kh, 0.07 * self.kh, 0.0065, n=16, u=X, v=Y, sides=4), "field_halo")], top, parent=self.root))

    def smoke(self, side, at):
        """Threads of smoke off what is still burning: they ride the wing they rise from."""
        items = []
        for i in range(2):
            b0 = at + Vector((0.02 * i, 0.02 * i, 0.0))
            pts = [b0 + Vector((0.012 * math.sin(q * 1.9 + i), 0.02 * q, 0.035 * q)) for q in range(5)]
            items.append((g.tongue(pts, [0.012, 0.02, 0.024, 0.018, 0.003], thick=0.4), "smoke_grey"))
        self.objects.append(piece("sway", "smoke", items, at, parent=self.wing_ob.get(side) or self.root))

    # --- what it carries, and what it sits on ----------------------------------------------
    def make_carry(self):
        style_, size = opt(self.spec.get("carry"), 1.0)
        if not style_:
            return
        k = self.k
        hand = (self.hands[1] + self.hands[-1]) / 2 if getattr(self, "hands", None) else self.C + Vector((0, -0.1, -0.05))
        if style_ == "taper":       # a lit taper as long as itself, carried upright
            base = hand + Vector((0, -0.012, -0.12 * k))
            h = 0.36 * k * size
            items = [(g.lathe([(0.012 * k, 0.0), (0.011 * k, h * 0.96), (0.006 * k, h)], n=6, centre=base), "wax"),
                     (g.lathe([(0.022 * k, 0.0), (0.024 * k, 0.012), (0.012 * k, 0.02)], n=6, centre=base + Vector((0, 0, h * 0.3))), "metal_brass"),
                     (g.tube([base + Z * h, base + Z * (h + 0.012)], 0.0016, n=3), "scale_black")]
            self.body_items += items
            t = base + Z * (h + 0.006)
            fl = g.tongue([t, t + Vector((0.006, 0, 0.024)), t + Vector((0, 0, 0.066))], [0.018, 0.026, 0.002], thick=0.8, normal=Y)
            self.objects.append(piece("flick", "flame", [(fl, "field_flame")], t, parent=self.root))
        elif style_ == "snuffers":  # a wick-trimmer's scissors, the size of a seed
            c = hand + Vector((0, -0.02, 0.0))
            items = []
            for sg in (1, -1):
                items.append((g.tongue([c + Vector((sg * 0.012, 0.01, 0)), c + Vector((sg * 0.004, -0.02, 0)), c + Vector((-sg * 0.003, -0.062, 0.0))], [0.008, 0.01, 0.003], thick=0.5, normal=Z), "metal_brass"))
                items.append((f2.band(c + Vector((sg * 0.02, 0.022, 0)), 0.011, 0.011, 0.0028, n=8, u=X, v=Y, sides=3), "metal_brass"))
            items.append((g.box(c + Vector((0, -0.05, 0.006)), (0.02, 0.016, 0.012)), "metal_brass"))
            self.body_items += items
        elif style_ == "dividers":  # a chart-maker's dividers
            c = hand + Vector((0, -0.016, 0.02))
            items = [(g.ico(c, 0.011, sub=1), "metal_brass")]
            for sg in (1, -1):
                items.append((g.tube([c, c + Vector((sg * 0.045, -0.01, -0.13))], [0.0055, 0.0012], n=4), "metal_brass"))
            self.body_items += items
        elif style_ == "comb":      # a piece of someone else's comb
            c = hand + Vector((0, -0.02, -0.03 * k))
            cells, dark, lit = None, None, None
            for i, (x, z) in enumerate(((-0.036, 0.0), (0.0, 0.0), (0.036, 0.0), (-0.018, -0.031), (0.018, -0.031), (-0.018, 0.031), (0.018, 0.031))):
                p = c + Vector((x, 0, z)) * k
                hexa = g.lathe([(0.02 * k, -0.012 * k), (0.02 * k, 0.012 * k)], n=6, phase=math.pi / 6)
                hexa = ([Vector((v_.x, v_.z, v_.y)) + p for v_ in hexa[0]], hexa[1])
                cells = g.merge(cells, hexa)
                inner = g.lathe([(0.013 * k, 0.0), (0.011 * k, 0.004 * k)], n=6, phase=math.pi / 6)
                inner = ([Vector((v_.x, -v_.z - 0.0125 * k, v_.y)) + p for v_ in inner[0]], inner[1])
                if i in (1, 5):
                    lit = g.merge(lit, inner)
                else:
                    dark = g.merge(dark, inner)
            self.body_items += [(cells, "wax_comb"), (dark, "wax_comb_dark"), (lit, "field_honey")]
        elif style_ == "star":      # a point of steady light above its head, like a star on a stick
            top = self.H + Vector((0, -0.01, 0.2 * self.kh))
            self.body_items.append((g.tube([self.H + Vector((0, 0, 0.04 * self.kh)), top], [0.0035, 0.002], n=3), "bone"))
            rays = None
            for i in range(4):
                a = math.pi * i / 4
                d = Vector((math.cos(a), 0, math.sin(a)))
                ln = 0.05 if i % 2 == 0 else 0.03
                rays = g.merge(rays, g.tongue([top - d * ln, top, top + d * ln], [0.001, 0.014, 0.001], thick=0.8, normal=Y))
            self.objects.append(piece("pulse", "star", [(rays, "field_star"), (g.ico(top, 0.014, sub=1), "field_star")], top, parent=self.root))
        elif style_ == "train":     # a pale train behind it that a hand could keep hold of
            parent = self.root
            a0 = self.tail_end
            back = (self.M.to_3x3() @ Vector((0, 1, -0.25))).normalized()
            for n in range(3):
                pts, widths, twists = [], [], []
                for q in range(4):
                    t = (n + q / 3) / 3
                    pts.append(a0 + back * (0.42 * size * t) + Vector((0.03 * math.sin(t * 5), 0, -0.05 * t * t)))
                    widths.append(0.03 + 0.06 * math.sin(math.pi * min(1.0, t * 1.2)) * (1 - 0.5 * t))
                    twists.append(0.5 * t)
                items = [(ribbon(pts, widths, twists, thick=0.005), "scale_white")]
                ob = piece("wave", "train", items, pts[0], n=n, parent=parent)
                self.objects.append(ob)
                parent = ob

    def make_perch(self):
        style_, size = opt(self.spec.get("perch"), 1.0)
        if not style_:
            return
        k = self.k
        foot = self.M @ Vector((0, 0.0, -0.118 * k))
        if style_ == "lamp":        # the light it keeps: a candle in a dish; it sits over the flame, and the wick is its own business
            base = self.C + Vector((0, -0.115 * k, -0.3 * k))
            r = 0.078 * k
            items = [(g.lathe([(r * 0.3, 0.0), (r * 1.0, 0.005), (r * 1.3, 0.03), (r * 1.22, 0.038), (r * 0.9, 0.016), (r * 0.02, 0.014)], n=10, centre=base), "metal_brass"),
                     (f2.band(base + Vector((0, r * 1.5, 0.03)), r * 0.34, r * 0.34, 0.0085 * k, n=10, u=Y, v=Z, sides=4), "metal_brass"),
                     (g.lathe([(r * 0.46, 0.012), (r * 0.44, 0.15 * k), (r * 0.3, 0.166 * k), (r * 0.02, 0.166 * k)], n=8, centre=base), "wax")]
            drips = None
            for a_, h_ in ((0.4, 0.11), (2.3, 0.13), (4.1, 0.09)):
                d_ = Vector((math.cos(a_), math.sin(a_), 0)) * (r * 0.45)
                drips = g.merge(drips, g.tube([base + d_ + Z * (0.158 * k), base + d_ * 1.06 + Z * (h_ * k)], [0.008 * k, 0.011 * k], n=4))
            items.append((drips, "wax"))
            t = base + Z * (0.166 * k)
            items.append((g.tube([t, t + Z * 0.016 * k], 0.002 * k, n=3), "scale_black"))
            self.body_items += items
            t = t + Z * 0.01 * k
            fl = g.tongue([t, t + Vector((0.008, 0, 0.03)) * k, t + Vector((0, 0, 0.088 * k))], [0.022 * k, 0.036 * k, 0.003], thick=0.8, normal=Y)
            self.objects.append(piece("flick", "flame", [(fl, "field_flame")], t, parent=self.root))
        elif style_ == "log":       # a twig it has made its own
            a, b = foot + Vector((-0.2 * k, 0.03, -0.012)), foot + Vector((0.21 * k, -0.02, 0.0))
            items = [(g.tube([a, (a + b) / 2 + Vector((0, 0, -0.01)), b], [0.017 * k, 0.02 * k, 0.014 * k], n=6), "wood_twig"),
                     (g.tube([a + (b - a) * 0.7, a + (b - a) * 0.8 + Vector((0.02, -0.03, 0.05))], [0.008 * k, 0.003 * k], n=4), "wood_twig"),
                     (g.blade(a + (b - a) * 0.8 + Vector((0.02, -0.03, 0.05)), a + (b - a) * 0.8 + Vector((0.07, -0.05, 0.075)), 0.035, normal=Z), "fur_light")]
            self.body_items += items

    # --- all of it (see _build) -----------------------------------------------------------
    def export(self, path=None):
        bpy.context.view_layer.update()
        low = min((ob.matrix_world @ v.co).z for ob in self.objects for v in ob.data.vertices)
        lift = max(0.0, 0.05 - low)
        for ob in self.objects:
            if ob.parent is None:
                ob.location.z += lift
        bpy.context.view_layer.update()
        C, H, k, kh = self.C + Z * lift, self.H + Z * lift, self.k, self.kh
        Mr = self.M.to_3x3()
        fwd = (self.MH.to_3x3() @ Vector((0, -1, 0)))
        socks = gh._table(H.z + 0.05 * kh, -0.1, C.z, 0.1, {
            "socket_head": [tuple(H + Vector((0, 0, 0.045 * kh)))], "socket_eyes": [tuple(H + fwd * 0.05 * kh)], "socket_mouth": [tuple(H + fwd * 0.05 * kh + Vector((0, 0, -0.03 * kh)))],
            "socket_throat": [tuple(H + Vector((0, -0.02, -0.06 * kh)))], "socket_keepsake": [tuple(C + Mr @ Vector((0, -0.07 * k, -0.07 * k)))],
            "socket_light": [tuple(C)], "socket_back": [tuple(C + Mr @ Vector((0, 0.0, 0.075 * k)))], "socket_body": [tuple(C + Mr @ Vector((0, 0.0, -0.07 * k)))],
            "socket_tail": [tuple(C + Mr @ Vector((0, 0.3 * k, -0.02 * k)))], "socket_arm_l": [tuple(C + Vector((0.075 * k, 0, 0)))], "socket_arm_r": [tuple(C + Vector((-0.075 * k, 0, 0)))],
            "socket_limb_fl": [tuple(C + Mr @ Vector((0.05 * k, -0.08 * k, -0.11 * k)))], "socket_limb_fr": [tuple(C + Mr @ Vector((-0.05 * k, -0.08 * k, -0.11 * k)))],
            "socket_grip": [tuple(C + Mr @ Vector((0, -0.1 * k, -0.12 * k)))],
            "socket_collar": f2.collar_at(tuple(C + Mr @ Vector((0, -0.075 * k, 0.0))), 0.06 * k, 0.06 * k, tilt=-self.pitch)})
        path = path or os.path.join(GL.OUT, self.id + ".glb")
        tris = GL.export_objects(self.objects, socks, path, ref=STAND)
        log(self.id, "%d triangles, %d KB, %d pieces" % (tris, os.path.getsize(path) // 1024, len(self.objects)))
        return tris


# ======================================================================================
# The patterns: what is painted on a wing, cell by cell and disc by disc
# ======================================================================================

def paint_wings(m, side):
    fore, hind = m.wing.get(("fore", side)), m.wing.get(("hind", side))
    A = m.ac
    pats = names(m.spec.get("pattern"))
    black, white, cream = "scale_black", "scale_white", "scale_cream"
    glint = "field_glint" if m.level >= 3 else white        # an eye-spot's point of light is the field's, once it is grown
    # every wing is furred where it leaves the body
    for w in (fore, hind):
        if w is not None:
            w.paint(lambda s, t, i, j: "fur_ruff" if i == 0 else None)
    for p in pats:
        if p == "bars":
            fore.paint(lambda s, t, i, j: A("accent") if (0.3 < s < 0.4 or 0.58 < s < 0.68) else None)
            if hind:
                hind.paint(lambda s, t, i, j: A("accent_light", "fur_ruff") if 0.5 < s < 0.75 else None)
        elif p == "singe":
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j, w=w: black if i >= w.ns - 1 else (A("accent_dark", "fur_dark") if i == w.ns - 2 else None))
        elif p == "neat":
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j, w=w: A("accent_pale", "fur_light") if i >= w.ns - 1 else None)
        elif p == "hem":
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j, w=w: A("accent") if i >= w.ns - 1 else None)
        elif p == "scar":
            pass        # the burn itself is cut below, when everything else is painted
        elif p == "ash":
            fore.paint(lambda s, t, i, j: ("scale_ash_pale" if s > 0.72 else "scale_ash") if s > 0.3 else None)
            fore.paint(lambda s, t, i, j: A("accent_dark", "fur_dark") if 0.18 < s < 0.3 else None)
            if hind:
                hind.paint(lambda s, t, i, j: ("scale_ash_pale" if s > 0.7 else "scale_ash") if s > 0.25 else A("accent_dark", "fur_dark"))
        elif p == "cracks":
            for w, lines in ((fore, (((0.3, 0.2), (0.5, 0.34), (0.66, 0.24), (0.9, 0.36)), ((0.36, 0.76), (0.56, 0.6), (0.72, 0.7), (0.94, 0.62)), ((0.5, 0.34), (0.56, 0.6)))),
                             (hind, (((0.3, 0.3), (0.52, 0.5), (0.7, 0.4), (0.92, 0.55)),))):
                if w:
                    for ln in lines:
                        w.stroke(ln, 0.03, "field_cracks", layer=1)
        elif p == "holes":
            fore.paint(lambda s, t, i, j: False if (i, j) in ((6, 2), (8, 4), (9, 1)) else None)
            if hind:
                hind.paint(lambda s, t, i, j: False if (i, j) in ((5, 3), (6, 1)) else None)
        elif p == "ermine":
            fore.paint(lambda s, t, i, j: white if i > 0 else None)
            for q, (s, t) in enumerate(((0.26, 0.3), (0.3, 0.72), (0.46, 0.5), (0.56, 0.2), (0.62, 0.78), (0.74, 0.46), (0.84, 0.74), (0.86, 0.2))):
                fore.disc(s, t, 0.034 + 0.008 * (q % 2), black, n=7, squash=1.3)
            if hind:
                hind.paint(lambda s, t, i, j: A("accent_light", "fur_light") if i > 0 else None)
                hind.disc(0.6, 0.5, 0.045, black, n=7)
        elif p == "tiger":
            fore.paint(lambda s, t, i, j: black if i > 0 else None)
            fore.paint(lambda s, t, i, j: cream if (i + (1 if j >= 3 else 0)) % 4 == 2 else None)
            if hind:
                hind.paint(lambda s, t, i, j, w=hind: (black if i >= w.ns - 1 else A("accent")) if i > 0 else None)
                for s, t in ((0.5, 0.3), (0.56, 0.7), (0.78, 0.5)):
                    hind.disc(s, t, 0.05, black, n=8)
        elif p == "rings":
            fore.paint(lambda s, t, i, j, w=fore: A("accent_pale", "fur_light") if i >= w.ns - 1 else (A("accent_dark", "fur_ruff") if i == w.ns - 3 else None))
            if hind:
                hind.paint(lambda s, t, i, j, w=hind: A("accent_pale", "fur_light") if i >= w.ns - 1 else (A("accent_dark", "fur_ruff") if i == w.ns - 3 else None))
        elif p == "eyes":
            fore.eye(0.5, 0.5, 0.15, ((1.0, A("accent_pale", "fur_light")), (0.8, black), (0.6, A("accent")), (0.36, black)), glint)
        elif p == "owl":
            fore.paint(lambda s, t, i, j: black if (j <= 1 and 0.25 < s < 0.9) else (cream if (j == 2 and 0.3 < s < 0.85) else None))
            fore.paint(lambda s, t, i, j, w=fore: A("accent_dark", "fur_ruff") if i >= w.ns - 1 else None)
            if hind:
                hind.paint(lambda s, t, i, j, w=hind: A("accent_dark", "fur_ruff") if i >= w.ns - 1 else None)
                hind.eye(0.52, 0.5, 0.22, ((1.0, cream), (0.82, A("accent")), (0.6, black), (0.3, A("accent_light", "fur_light"))), glint)
        elif p == "eyes4":
            rings = ((1.0, A("accent_pale", "fur_light")), (0.8, black), (0.6, A("accent")), (0.34, black))
            fore.eye(0.6, 0.5, 0.17, rings, glint)
            if hind:
                hind.eye(0.6, 0.5, 0.17, rings, glint)
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j, w=w: A("accent_dark", "fur_ruff") if i >= w.ns - 1 else None)
        elif p == "ward":
            fore.paint(lambda s, t, i, j: "wood_beam" if i > 0 else None)
            fore.paint(lambda s, t, i, j: "wood_bark" if (i % 4 == 3 and j in (1, 2)) else None)
            if hind:
                hind.paint(lambda s, t, i, j, w=hind: A("accent_dark", "fur_ruff") if i >= w.ns - 1 else None)
                hind.eye(0.5, 0.45, 0.17, ((1.0, A("accent_pale", "fur_light")), (0.8, black), (0.6, A("accent")), (0.34, black)), glint)
        elif p == "bark":
            fore.paint(lambda s, t, i, j: "wood_bark" if ((i * 3 + j * 5) % 7 in (0, 3) and i > 0) else None)
            fore.paint(lambda s, t, i, j: "scale_grey" if ((i * 5 + j * 3) % 11 == 2 and i > 1) else None)
        elif p == "peek":
            if hind:
                hind.paint(lambda s, t, i, j, w=hind: (black if (i >= w.ns - 1 or i in (3, 4)) else A("accent")) if i > 0 else None)
        elif p == "flash":
            if hind:
                hind.paint(lambda s, t, i, j, w=hind: (black if i >= w.ns - 1 else ("field_flash" if i in (2, 3, 4) else A("accent_light", "fur_light"))) if i > 0 else None)
        elif p == "wall":
            for w in (fore, hind):
                if w:
                    for jj in (2, 4):
                        w.stroke([(0.1, jj / w.nt), (0.5, jj / w.nt), (0.98, jj / w.nt)], 0.022, "stone_mortar")
                    for q, ss in enumerate((0.3, 0.62, 0.9)):
                        for band in range(3):
                            s_ = ss - (0.16 if band % 2 else 0.0)
                            w.stroke([(s_, band * 2 / w.nt + 0.02), (s_, min(1.0, (band + 1) * 2 / w.nt) - 0.02)], 0.022, "stone_mortar")
            fore.stroke([(0.34, 0.1), (0.46, 0.4), (0.4, 0.62), (0.52, 0.95)], 0.02, "field_crack", layer=2)
            fore.paint(lambda s, t, i, j, w=fore: A("accent_dark", "fur_ruff") if (i >= w.ns - 1) else None)
            if hind:
                hind.paint(lambda s, t, i, j, w=hind: A("accent_dark", "fur_ruff") if (i >= w.ns - 1 or j >= w.nt - 1) else None)
        elif p == "snake":
            fore.paint(lambda s, t, i, j, w=fore: A("accent_dark", "fur_ruff") if (i >= w.ns - 3 and j <= 1) else None)
            fore.paint(lambda s, t, i, j, w=fore: A("accent_pale", "fur_light") if (i >= w.ns - 3 and j == 2) else None)
            fore.disc(0.9, 0.12, 0.034, cream, layer=1, n=8)
            fore.disc(0.9, 0.12, 0.016, black, layer=2, n=6)
            fore.stroke([(0.8, 0.3), (0.9, 0.27), (0.985, 0.2)], 0.014, black, layer=1)
        elif p == "windows":
            fore.paint(lambda s, t, i, j: False if (i in (5, 6) and j in (2, 3)) else (A("accent_light", "fur_light") if (4 <= i <= 7 and 1 <= j <= 4) else None))
            if hind:
                hind.paint(lambda s, t, i, j: False if (i in (4, 5) and j in (2, 3)) else (A("accent_light", "fur_light") if (3 <= i <= 6 and 1 <= j <= 4) else None))
        elif p == "worn":         # worn thin enough to read through: pale, veined, gone in places
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j, w=w: "fur_light" if i > 0 else None)
                    w.paint(lambda s, t, i, j, w=w: False if ((i * 7 + j * 3) % 13 == 5 and i > 3) else None)
                    for tt in (0.2, 0.5, 0.8):
                        w.stroke([(0.1, tt), (0.4, tt), (0.7, tt), (0.92, tt)], 0.018, A("accent_light", "fur_ruff"))
        elif p == "moon":
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j, w=w: (A("accent_light", "fur_light") if s < 0.62 else None) if i > 0 else None)
                    w.eye(0.56 if w is fore else 0.5, 0.52, 0.06, ((1.0, A("accent_dark", "fur_dark")), (0.66, cream), (0.34, black)), glint=None)
        elif p == "costa":
            fore.paint(lambda s, t, i, j: A("accent_dark", "fur_dark") if j == 0 else None)
        elif p == "white":
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j: white if i > 0 else None)
        elif p == "edge":
            for w in (fore, hind):
                if w:
                    for c in list(w.cells):
                        if c[0] == w.ns - 1:
                            w.rims[c] = "field_edge"
                    w.paint(lambda s, t, i, j, w=w: A("accent_light", "fur_light") if i == w.ns - 1 else None)
        elif p == "frame":        # nearly clear: a frame and its veins, and nothing between them
            for w in (fore, hind):
                if w:
                    veins = (4, 8) if w is fore else (w.ns // 2,)
                    keep = lambda i, j, w=w, veins=veins: i <= 1 or i >= w.ns - 1 or j == 0 or j == w.nt - 1 or j == w.nt // 2 or i in veins
                    w.paint(lambda s, t, i, j, w=w, keep=keep: (A("accent_light", "fur_light") if (j == 0 or i >= w.ns - 1) else white) if keep(i, j) else False)
        elif p == "likeness":       # two eyes and a mouth in the widest pane: nobody's face in particular, and yours
            for s_ in (0.49, 0.59):
                fore.disc(s_, 0.26, 0.034, A("accent_pale", "fur_light"), n=8)
            fore.stroke([(0.485, 0.4), (0.54, 0.44), (0.595, 0.4)], 0.024, A("accent_pale", "fur_light"))
        elif p == "streak":
            fore.paint(lambda s, t, i, j, w=fore: A("accent_pale", "fur_light") if j == w.nt // 2 and i > 1 else None)
        elif p == "compass":
            for w in (fore, hind):
                if w:
                    w.paint(lambda s, t, i, j, w=w: None if i == 0 else (A("accent") if (j % 2 == 0 and i < w.ns - 1) else (white if i < w.ns - 1 else A("accent_dark", "fur_dark"))))
        elif p == "chart":
            w = fore
            w.paint(lambda s, t, i, j: "paper_chart" if i > 0 else None)
            w.paint(lambda s, t, i, j: A("accent_pale", "fur_light") if (s < 0.62 and (j >= 5 or (j == 4 and i % 3 != 1))) else None)     # the sea
            w.stroke([(0.1, 0.56), (0.22, 0.5), (0.36, 0.6), (0.5, 0.52), (0.62, 0.58)], 0.02, A("accent_dark", "fur_dark"))                       # the coast
            for q in range(6):                                                                                                                      # the road walked
                w.disc(0.14 + 0.085 * q, 0.3 - 0.05 * math.sin(q * 1.3), 0.016, black, n=5)
            w.disc(0.62, 0.3, 0.03, A("accent"), n=4, turn=0.78)                                                                                    # a post
            w.stroke([(0.7, 0.05), (0.7, 0.95)], 0.012, A("accent_light", "fur_light"))                                                             # where the known stops
    # a bite burned out of one forewing, its edge still alight
    burn, bsize = opt(m.spec.get("burn"), 1.0)
    if burn == side and fore is not None:
        c, edge, near = fore.bite(0.97, 0.62, 0.3 * bsize)
        for cell in near:
            fore.cells[cell] = black
            fore.rims[cell] = "field_edge"
        if len(edge) > 2:
            fore.stroke([c + (q - c) * 1.045 for q in edge], 0.03, "field_edge", layer=1, flat=True)


def roll(m, side):
    """The rolled end of the Chart-moth's wing: a rod, the chart wound on it, a knob at each end."""
    w = m.wing[("fore", side)]
    fr = m.wing_frame("fore", side)
    a, b = m.M @ m.W(fr, w.at(1.0, -0.06), 0.012), m.M @ m.W(fr, w.at(1.0, 1.06), 0.012)
    items = [(g.tube([a + (b - a) * 0.06, b - (b - a) * 0.06], 0.019, n=8), "paper_chart"), (g.tube([a, b], 0.007, n=5), "wood_twig"),
             (g.ico(a, 0.013, sub=1), "metal_brass"), (g.ico(b, 0.013, sub=1), "metal_brass")]
    return items if side == "l" else mirror_items(items)


# ======================================================================================
# The Starter: not a moth yet
# ======================================================================================

def build_grub(form_id, level, spec, path=None):
    """The Case-grub: a grub in a case it has spun of whatever was nearest (twigs, a page corner,
    thread, lamp-soot), hanging by one thread from a point of the field. Its head and six feet
    come out of the mouth of the case and it looks at you; the whole of it sways."""
    kit.reset()
    case, cs = opt(spec.get("case", "scraps"), 1.0)
    T = Vector((0, 0.07, 0.7))                          # the point of the field its thread hangs from
    O = Vector((0, -0.01, 0.42))                        # the middle of the case's mouth
    ax = Vector((0, 0.3, -1.0)).normalized()            # the way the case hangs from its mouth
    fw = ax.cross(X).normalized()                       # the front of it
    ln = 0.34 * cs
    rad = lambda a: X * math.cos(a) + fw * math.sin(a)
    prof = [(-0.035, 0.074), (0.0, 0.083), (0.16, 0.092), (0.42, 0.084), (0.7, 0.06), (0.9, 0.031), (1.0, 0.008)]

    def r_at(t):
        for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
            if t0 <= t <= t1:
                return (r0 + (r1 - r0) * (t - t0) / (t1 - t0)) * cs
        return prof[-1][1] * cs
    items = [(g.loft([g.ring(O + ax * (t * ln), r * cs, r * cs, n=10, u=X, v=fw) for t, r in prof], caps=True), "fur_light")]
    # what it is made of: twigs laid along it, thread wound round it, a band of lamp-soot, a page corner
    twigs = None
    for i, (a, t0, t1, tw) in enumerate(((1.25, 0.06, 0.8, 0.25), (2.3, 0.02, 0.62, -0.2), (0.3, 0.1, 0.94, 0.2), (3.5, 0.05, 0.7, 0.3), (-0.7, 0.0, 0.76, -0.25), (4.6, 0.12, 0.9, 0.1))):
        p0 = O + ax * (t0 * ln) + rad(a) * (r_at(t0) + 0.007)
        p1 = O + ax * (t1 * ln) + rad(a + tw) * (r_at(t1) + 0.012)
        twigs = g.merge(twigs, g.tube([p0 - ax * 0.012, (p0 + p1) / 2 + rad(a + tw / 2) * 0.004, p1 + ax * 0.02], [0.0085, 0.0095, 0.006], n=5))
    items.append((twigs, "wood_twig"))
    wraps = None
    for t in (0.24, 0.56):
        wraps = g.merge(wraps, f2.band(O + ax * (t * ln), r_at(t) + 0.004, r_at(t) + 0.004, 0.007, n=12, u=X, v=fw, sides=4))
    items.append((wraps, "fur_dark"))
    items.append((f2.band(O + ax * (0.4 * ln), r_at(0.4) + 0.003, r_at(0.4) + 0.003, 0.012, n=12, u=X, v=fw, sides=4, flat=0.45), "scale_black"))
    pc = O + ax * (0.3 * ln) + rad(1.9) * (r_at(0.3) + 0.004)
    items.append((g.tongue([pc - ax * 0.05 + rad(1.9) * 0.004, pc + rad(2.4) * 0.012, pc + ax * 0.085 + rad(1.5) * 0.03], [0.05, 0.085, 0.004], thick=0.07, normal=rad(1.9)), "paper"))
    items.append((g.tube([T, O - fw * 0.07 + Vector((0, 0, 0.008))], 0.0026, n=3), "thread_silk"))
    items.append((g.ico(T, 0.013, sub=1), "field_thread"))
    # the grub: a ring of it in the mouth of the case, and six feet over the lip
    items.append((g.ico(O + Vector((0, -0.004, 0.012)), 1.0, sub=2, scale=(0.068, 0.066, 0.05)), "fur_dark"))
    feet = None
    for sx in (1, -1):
        for n in range(3):
            p0 = O + Vector((sx * (0.026 + 0.016 * n), -0.05 + 0.014 * n, 0.03))
            p1 = p0 + Vector((sx * 0.012, -0.03, 0.002))
            p2 = p1 + Vector((sx * 0.004, -0.012, -0.034))
            feet = g.merge(feet, g.tube([p0, p1, p2], [0.011, 0.0095, 0.0045], n=5))
    items.append((feet, "bristle_leg"))
    root = piece("sway", "grub", items, T)
    objects = [root]
    # its head: all face
    Hc = O + Vector((0, -0.04, 0.078))
    es = opt(spec.get("eyes", "big"))[1]
    re = 0.027 * es
    hi = [(g.ico(Hc, 1.0, sub=3, scale=(0.068, 0.063, 0.061)), "fur_light"),
          (g.ico(Hc + Vector((0, 0.016, 0.018)), 1.0, sub=2, scale=(0.061, 0.056, 0.052)), "fur_ruff")]
    lids, jaws, cheeks = None, None, None
    ex, ey, ez = 0.037, -0.04, 0.006
    for sx in (1, -1):
        lids = g.merge(lids, g.ico(Hc + Vector((sx * ex, ey + 0.004, ez)), re * 0.93, sub=1))
        lids = g.merge(lids, g.tongue([Hc + Vector((sx * (ex - re * 0.95), ey - re * 0.5, ez + re * 0.72)), Hc + Vector((sx * ex, ey - re * 0.9, ez + re * 1.12)),
                                       Hc + Vector((sx * (ex + re * 0.98), ey - re * 0.3, ez + re * 0.74))], [0.013, 0.018, 0.01], thick=0.55, normal=(0, -0.4, 1)))
        jaws = g.merge(jaws, g.cone(Hc + Vector((sx * 0.014, -0.054, -0.026)), Hc + Vector((sx * 0.003, -0.066, -0.04)), 0.0075, n=4))
        cheeks = g.merge(cheeks, g.ico(Hc + Vector((sx * 0.03, -0.04, -0.024)), 1.0, sub=1, scale=(0.02, 0.016, 0.015)))
    hi += [(lids, "fur_dark"), (jaws, "claw"), (cheeks, "fur_light")]
    head = piece("turn", "head", hi, Hc, parent=root)
    objects.append(head)
    c = Hc + Vector((ex, ey, ez))
    look = Vector((0.14, -0.98, 0.12)).normalized()
    eye = piece("blink", "eye", [(g.ico(c, re, sub=2), "eye_dark"), (g.ico(c + look * re * 0.9, 1.0, sub=1, scale=(re * 0.38, re * 0.17, re * 0.38)), "field_eyes")], c, side="l", parent=head)
    objects += [eye, twin(eye, "blink", "eye", side="r", parent=head)]
    b0 = Hc + Vector((0.022, -0.02, 0.05))
    fe = [(g.tube([b0, b0 + Vector((0.012, -0.014, 0.03)), b0 + Vector((0.034, -0.024, 0.046))], [0.0055, 0.0045, 0.0025], n=4), "bristle_leg"),
          (g.ico(b0 + Vector((0.034, -0.024, 0.046)), 0.0075, sub=1), "fur_light")]
    feeler = piece("sway", "feeler", fe, b0, side="l", parent=head)
    objects += [feeler, twin(feeler, "sway", "feeler", side="r", parent=head)]
    bpy.context.view_layer.update()
    tip = O + ax * ln
    socks = gh._table(Hc.z + 0.06, -0.1, 0.4, 0.09, {
        "socket_head": [tuple(Hc + Vector((0, 0, 0.06)))], "socket_eyes": [tuple(Hc + Vector((0, -0.062, 0.008)))], "socket_mouth": [tuple(Hc + Vector((0, -0.066, -0.03)))],
        "socket_back": [tuple(O + ax * (0.3 * ln) - fw * 0.1)], "socket_tail": [tuple(tip)], "socket_light": [tuple(O + ax * (0.4 * ln))], "socket_body": [tuple(O + ax * (0.4 * ln) + fw * 0.1)],
        "socket_keepsake": [tuple(O + ax * (0.12 * ln) + fw * 0.1)], "socket_collar": f2.collar_at(tuple(O + ax * (0.05 * ln)), 0.088, 0.088, tilt=0.29)})
    path = path or os.path.join(GL.OUT, form_id + ".glb")
    tris = GL.export_objects(objects, socks, path, ref=STAND)
    log(form_id, "%d triangles, %d KB, %d pieces" % (tris, os.path.getsize(path) // 1024, len(objects)))


# ======================================================================================
# The line
# ======================================================================================

def _features(base, form_id):
    def walk(n):
        if n.get("id") == form_id:
            return n.get("features", [])
        for key in ("paths", "prongs", "finishes"):
            for c in n.get(key, []):
                got = walk(c)
                if got is not None:
                    return got
        return None
    return walk(base["settled"]) or walk({"paths": base["paths"]}) or []


def moth(form_id, level, spec, base):
    spec = dict(spec)
    spec["_features"] = tuple(_features(base, form_id)) if base else ()
    if spec.get("kind", "moth") == "grub":
        return build_grub(form_id, level, spec)
    m = Moth(form_id, level, spec)
    _build(m)


def _build(m, path=None):
    """Moth.build, with the chart's rolled ends joined to its wings before they are made pieces."""
    hang = opt(m.spec.get("aura"))[0] == "sway"
    if hang:
        top = Vector((0, m.H.y, m.H.z + 0.3))
        thread = [(g.tube([m.H + Vector((0, 0.01, 0.04)), top], 0.0022, n=3), "thread_silk"), (g.ico(top, 0.011, sub=1), "field_thread")]
        m.root = piece("sway", "hang", thread, top)
        m.objects.append(m.root)
    m.make_thorax()
    m.make_legs()
    m.make_perch()
    m.make_wings()
    m.make_tails()
    m.make_abdomen()
    m.make_head()
    m.make_carry()
    m.make_aura()
    burn = opt(m.spec.get("burn"))
    if burn[0] and m.wing_ob.get(burn[0]) is not None and ("fore", burn[0]) in m.wing:
        w = m.wing[("fore", burn[0])]
        p = m.M @ m.W(m.wing_frame("fore", burn[0]), w.at(0.66, 0.62), 0.01)
        m.smoke(burn[0], p if burn[0] == "l" else Vector((-p.x, p.y, p.z)))
    body = piece(None, "body", m.body_items, m.C, parent=m.root)
    if m.root is not None:
        for ob in m.objects:
            if ob.parent is None and ob is not m.root:
                GL.child_of(ob, m.root)
    m.objects.append(body)
    return m.export(path)


# ======================================================================================
# The plain moth (the base's own body), and the gifts
# ======================================================================================

PLAIN = {"kind": "moth", "wings": ["delta", 1.0], "hold": "v", "flap": "beat", "pitch": 34, "pattern": ["bars", "singe"], "feelers": ["comb", 1.0], "fur": ["plain", 1.0],
         "abdomen": ["stout", 1.0], "eyes": ["big", 1.0], "brow": "keen", "build": {"span": 1.0, "body": 1.0}}


def build_body():
    """bodies/beast-moth.glb: the moth with no Path's colour on it, for whatever has no form of its own."""
    m = Moth("beast-moth", 2, dict(PLAIN), plain=True)
    _build(m, os.path.join(kit.OUT, "bodies", "beast-moth.glb"))


def gift_dust_wings():
    """The Moth's gift, on the back of whatever it has joined: two broad wings, an eye on each,
    in the colour of the Path it is on. They beat."""
    L = 0.5
    out = []
    for side, sgn in (("l", 1),):
        fore, hind = Wing(WINGS["broad"][0], -12), Wing(WINGS["broad"][1], 0)
        for w in (fore, hind):
            w.paint(lambda s, t, i, j, w=w: "accent_pale" if i >= w.ns - 1 else ("accent_dark" if i == w.ns - 3 else ("fur_ruff" if i == 0 else None)))
        fore.eye(0.5, 0.5, 0.16, ((1.0, "accent_pale"), (0.8, "scale_black"), (0.6, "accent"), (0.36, "scale_black")))
        root = Vector((0.03, 0.0, 0.0))
        dih = math.radians(34)
        eu, ev, en = Vector((math.cos(dih), 0, math.sin(dih))), Vector((0, -1, 0)), Vector((-math.sin(dih), 0, math.cos(dih)))
        raw = Raw()
        flip = lambda p: Vector((sgn * p.x, p.y, p.z))
        for which, w in (("fore", fore), ("hind", hind)):
            lower = 0.0 if which == "fore" else -TH
            W = lambda p, off: flip(root + eu * (p.x * L) + ev * (p.y * L) + en * (off - 0.06 * (p.x * L) ** 2 / L))
            top = [[W(w.at(i / w.ns, j / w.nt), TH / 2 + lower) for j in range(w.nt + 1)] for i in range(w.ns + 1)]
            bot = [[W(w.at(i / w.ns, j / w.nt), -TH / 2 + lower) for j in range(w.nt + 1)] for i in range(w.ns + 1)]
            cells = {c: (mm or ("fur_dark" if which == "fore" else "fur_light")) for c, mm in w.cells.items()}
            raw.sheet(top, bot, cells, w.rims, flip(en))
            for pts, material, layer in w.decals:
                raw.plate([W(p, TH / 2 + lower + layer * EPS) for p in pts], [W(p, -TH / 2 + lower - layer * EPS) for p in pts], flip(en), material)
        raws, items = [raw.object("wings_" + side)], []
        out.append(piece("beat", "wing", items, root, n=0, raws=raws))
        out.append(twin(out[0], "beat", "wing", n=1))
    return out


def gift_antennae():
    """The Moth's gift, on the head of whatever it has joined: two great feathered feelers that
    read the air. They sway."""
    out = []
    s = 2.1
    for sx, side in ((1, "l"),):
        b0 = Vector((sx * 0.035, -0.02, 0.0))
        path = [b0, b0 + Vector((sx * 0.026, -0.03, 0.07)) * s, b0 + Vector((sx * 0.07, -0.06, 0.125)) * s, b0 + Vector((sx * 0.12, -0.072, 0.152)) * s, b0 + Vector((sx * 0.162, -0.058, 0.148)) * s]
        pts = [cr(path, i / 8) for i in range(9)]
        items = [(g.tube(pts, [0.011 * (1 - 0.08 * i) for i in range(9)], n=5), "bristle_leg")]
        teeth, teeth2 = None, None
        for i in range(10):
            t = 0.1 + 0.86 * i / 9
            p = cr(path, t)
            d = (cr(path, min(1.0, t + 0.05)) - cr(path, max(0.0, t - 0.05))).normalized()
            o = d.cross(Vector((0, -1, 0.25))).normalized() * sx
            ln = 0.056 * s * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.08) ** 0.8))
            for sg in (1, -1):
                bl = g.blade(p, p + o * (sg * ln) + d * (ln * 0.45), 0.02 * s, normal=(0, -1, 0.25), belly=0.45)
                if i % 2:
                    teeth2 = g.merge(teeth2, bl)
                else:
                    teeth = g.merge(teeth, bl)
        items += [(teeth, "accent_light"), (teeth2, "accent")]
        out.append(piece("sway", "feeler", items, b0, side=side))
        out.append(twin(out[0], "sway", "feeler", side="r"))
    return out


GIFTS = {"moth-dust-wings": gift_dust_wings, "moth-antennae": gift_antennae}


def gifts():
    for name, fn in GIFTS.items():
        kit.reset()
        GL.accent({"accent": "amethyst"})
        objs = fn()
        path = os.path.join(kit.OUT, "gifts", name + ".glb")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        log("wrote", os.path.relpath(path, kit.ROOT), "%d KB" % (os.path.getsize(path) // 1024))


def register(builders):
    global GL
    for name in ("genius_lines", "__main__"):
        mod = sys.modules.get(name)
        if mod is not None and getattr(mod, "BUILDERS", None) is builders:
            GL = mod
    if GL is None:
        import genius_lines
        GL = genius_lines
    builders["moth"] = moth


if __name__ == "__main__":
    import genius_lines  # noqa: F401  (it registers the families, this one among them)
    import lines_moth
    lines_moth.GL = genius_lines
    genius_lines._palette_of("moth")
    if sys.argv[1:] == ["gifts"]:
        lines_moth.gifts()
    elif sys.argv[1:] == ["body"]:
        genius_lines.accent({})
        lines_moth.build_body()
    else:
        print(__doc__)
