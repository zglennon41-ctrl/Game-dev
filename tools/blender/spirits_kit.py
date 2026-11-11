"""WILDLINE genius lines, the things with no flesh: what the four lines share
(lines_spirits.py: the Lurker, the Fiend, the Ember, the Fog; docs/genius-lines.md).

A body here has no rig. It is built as a list of pieces, each a geometry and a material, in
the genius kit's space (Z up, facing -Y, left is +X, about 0.7 units tall), and written as one
object with the usual sockets and `ref_top` at the crown of its head. The game stands it to
its stage's height by `ref_top`, floats it or walks it by its silhouette's kind, glows its
`field_*` materials in the partner's Shape colour and paints the partner's coat on the
materials its silhouette's look names (data/genius-looks.json, bodies: roles).

So that the coat goes on whatever a form's silhouette is, a builder never names a coat
material itself: it asks the Body for a role (main, under, trim).
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
import genius_kit as kit
from genius_kit import mat, field, PALETTE, STAND
import genius_forms2 as f2
import genius_homes as gh

ROOT = kit.ROOT
OUT = os.path.join(ROOT, "game", "assets", "genius", "forms")

# what these lines are made of that the kits' palettes did not have: muted, a value apart
PALETTE.update({
    "ash": ((0.5, 0.48, 0.45), 0.95, 0.0), "ash_dark": ((0.25, 0.24, 0.235), 0.95, 0.0), "ash_pale": ((0.72, 0.7, 0.66), 0.95, 0.0),
    "brick": ((0.4, 0.2, 0.14), 0.9, 0.0), "wax_red": ((0.36, 0.075, 0.06), 0.4, 0.0), "rust": ((0.3, 0.16, 0.09), 0.8, 0.3),
    "soot": ((0.05, 0.045, 0.045), 0.9, 0.0), "clinker": ((0.16, 0.14, 0.14), 0.7, 0.2), "clinker_light": ((0.3, 0.27, 0.26), 0.7, 0.2),
    "pane": ((0.1, 0.14, 0.17), 0.12, 0.0), "stone_grave": ((0.38, 0.39, 0.37), 0.95, 0.0), "timber": ((0.22, 0.15, 0.09), 0.85, 0.0),
    "mask_pale": ((0.74, 0.71, 0.64), 0.6, 0.0), "veil": ((0.56, 0.57, 0.6), 0.9, 0.0), "steam": ((0.8, 0.81, 0.8), 0.9, 0.0),
    "stubble": ((0.06, 0.05, 0.045), 0.95, 0.0), "grass_dry": ((0.42, 0.38, 0.2), 0.9, 0.0),
})

SPREAD = 1.7        # how far across a body may be, against the height it is stood to

# what is soft is shaded round; what is hard keeps its planes
SOFT = ("ink", "shade", "void", "field", "mist", "smoke", "cloth", "wool", "wax", "water", "dust", "ash", "tongue", "maw", "leather", "cord",
        "veil", "steam", "mask", "soot", "mark_")


def lines():
    """genius_lines, under whichever name it was loaded (it is __main__ when it is run)."""
    m = sys.modules.get("__main__")
    if m is not None and hasattr(m, "export_objects") and hasattr(m, "forms_of"):
        return m
    import genius_lines
    return genius_lines


def log(*a):
    print("[lines_spirits]", *a)


def opt(v, default_size=1.0):
    if v is None or v is False:
        return None, 0.0
    if isinstance(v, (list, tuple)):
        return v[0], float(v[1]) if len(v) > 1 else default_size
    return v, default_size


def each(v):
    """A slot that may hold several: "lamp", ["lamp", 1.2], or [["lamp", 1.2], "tags"]."""
    if v is None or v is False:
        return []
    if isinstance(v, str):
        return [(v, 1.0)]
    if len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], (int, float)):
        return [(v[0], float(v[1]))]
    return [opt(x) for x in v]


# --- silhouettes and their coats ---------------------------------------------------------

_LOOKS = None


def roles_of(silhouette):
    """role -> material name, for the look this silhouette wears (main, under, trim)."""
    global _LOOKS
    if _LOOKS is None:
        with open(os.path.join(ROOT, "data", "genius-looks.json")) as f:
            _LOOKS = json.load(f)
    r = {role: name for name, role in _LOOKS["bodies"].get(silhouette, {}).get("roles", {}).items()}
    r.setdefault("main", "shade")
    r.setdefault("under", r["main"])
    r.setdefault("trim", r["under"])
    return r


def silhouette_of(base, form_id):
    """The silhouette a form wears: its own where it names one, or the nearest above it."""
    def walk(n, sil):
        sil = n.get("silhouette", sil)
        if n["id"] == form_id:
            return sil
        for k in ("paths", "prongs", "finishes"):
            for c in n.get(k, []):
                got = walk(c, sil)
                if got:
                    return got
        return None
    s = base["settled"]
    if s["id"] == form_id:
        return s.get("silhouette", base["silhouette"])
    for p in base["paths"]:
        got = walk(p, s.get("silhouette", base["silhouette"]))
        if got:
            return got
    return base["silhouette"]


# --- geometry, beyond genius_geo ---------------------------------------------------------

def rotz(p, a, about=(0, 0)):
    p = V(p)
    x, y = p.x - about[0], p.y - about[1]
    return Vector((about[0] + x * math.cos(a) - y * math.sin(a), about[1] + x * math.sin(a) + y * math.cos(a), p.z))


def turned(geo, a, about=(0, 0)):
    """A geometry turned about the vertical through `about`."""
    return [rotz(p, a, about) for p in geo[0]], list(geo[1])


def shifted(geo, d):
    d = V(d)
    return [V(p) + d for p in geo[0]], list(geo[1])


def scaled(geo, s, about=(0, 0, 0)):
    c = V(about)
    s = Vector((s, s, s)) if isinstance(s, (int, float)) else V(s)
    return [Vector((c.x + (p.x - c.x) * s.x, c.y + (p.y - c.y) * s.y, c.z + (p.z - c.z) * s.z)) for p in map(V, geo[0])], list(geo[1])


def sheared(geo, lean, z0, side=0.0):
    """Leaned forward (to -Y) by `lean` a unit of height above z0, and to its left by `side`."""
    return [Vector((p.x + side * (p.z - z0), p.y - lean * (p.z - z0), p.z)) for p in map(V, geo[0])], list(geo[1])


def tilted(geo, rx=0.0, ry=0.0, rz=0.0, about=(0, 0, 0)):
    c = V(about)
    R = Matrix.Rotation(rz, 3, "Z") @ Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X")
    return [c + R @ (V(p) - c) for p in geo[0]], list(geo[1])


def disc(c, r, thick=0.02, n=10, squash=1.0):
    """A flat round slab lying on the ground at c."""
    c = V(c)
    geo = g.lathe([(r, 0.0), (r * 0.94, thick), (0.0, thick)], n=n)
    return [Vector((c.x + p.x, c.y + p.y * squash, c.z + p.z)) for p in geo[0]], geo[1]


def hoop(c, rx, ry, r, n=14, u=X, v=Y, sides=4, flat=1.0):
    """A ring of tube round c in the plane of u and v."""
    return f2.band(c, rx, ry, r, n=n, u=u, v=v, sides=sides, flat=flat)


def arc(c, rx, rz, a0, a1, r, n=10, u=X, v=Z, sides=4, flat=1.0):
    """Part of a hoop, from angle a0 to a1 (radians, from u toward v)."""
    c = V(c)
    pts = [c + V(u) * (math.cos(a0 + (a1 - a0) * i / n) * rx) + V(v) * (math.sin(a0 + (a1 - a0) * i / n) * rz) for i in range(n + 1)]
    return g.tube(pts, [r] * len(pts), n=sides, flat=flat)


def chain(points, link=0.03, n=None):
    """Links along a line of points: small flat ovals, turned by turns."""
    pts = [V(p) for p in points]
    total = sum((b - a).length for a, b in zip(pts, pts[1:]))
    n = n or max(2, int(total / (link * 1.5)))
    geo = None
    for i in range(n + 1):
        t = total * i / n
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length
            if t <= L or (b is pts[-1]):
                p = a + (b - a) * min(1.0, t / max(L, 1e-6))
                break
            t -= L
        geo = g.merge(geo, g.ico(p, link, sub=0, scale=(1.0, 0.45, 1.0) if i % 2 else (0.45, 1.0, 1.0)))
    return geo


def sag(a, b, drop, n=6):
    """Points from a to b hanging in a curve."""
    a, b = V(a), V(b)
    return [a + (b - a) * (i / n) + Vector((0, 0, -drop * math.sin(math.pi * i / n))) for i in range(n + 1)]


def eye_pair(c, dx, r, scale=(1.25, 0.4, 0.4), slant=0.3):
    """Two eyes either side of c, on a face that looks to -Y."""
    c = V(c)
    geo = None
    for s in (1, -1):
        geo = g.merge(geo, g.ico(c + Vector((s * dx, 0, 0)), r, sub=1, scale=scale, rot=(0, s * -slant, 0)))
    return geo


def fingers(wr, d, n=3, L=0.12, spread=0.02, r=0.016, hook=0.0):
    """Fingers from a wrist, along d; hook bends their ends down."""
    wr, d = V(wr), V(d).normalized()
    side = d.cross(Z)
    side = side.normalized() if side.length > 1e-5 else X
    geo = None
    for j in range(n):
        o = (j - (n - 1) / 2.0)
        mid = wr + d * (L * 0.5) + side * (o * spread)
        tip = wr + d * (L * (1.0 + 0.1 * (o == 0))) + side * (o * spread * 1.6) + Vector((0, 0, -hook * L))
        geo = g.merge(geo, g.tongue([wr, mid, tip], [r, r * 0.75, r * 0.12], thick=0.5))
    return geo


def lantern(at, s, glow="lamp", strength=3.2, frame="metal_iron", cap="metal_brass", lit=True):
    """A small caged lamp hanging from `at`: [(geometry, material), ...]."""
    at = V(at)
    c = at + Vector((0, 0, -s * 1.5))
    items = [
        (g.tube([at, at + Vector((0, 0, -s * 0.55))], s * 0.07, n=4), mat(frame)),
        (g.lathe([(s * 0.12, s * 0.95), (s * 0.5, s * 0.6), (s * 0.56, s * 0.52)], n=6, centre=c), mat(cap)),
        (g.lathe([(s * 0.52, -s * 0.62), (s * 0.3, -s * 0.8)], n=6, centre=c), mat(cap)),
        (g.ico(c, s * 0.36, sub=1, scale=(1, 1, 1.25)), field(glow, strength) if lit else mat("glass")),
    ]
    posts = None
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p = c + Vector((math.cos(a) * s * 0.5, math.sin(a) * s * 0.5, 0))
        posts = g.merge(posts, g.tube([p + Vector((0, 0, -s * 0.62)), p + Vector((0, 0, s * 0.55))], s * 0.05, n=3))
    items.append((posts, mat(frame)))
    return items


def candle(at, h, r, lit=1.0, wax="wax", glow="flame"):
    """A candle standing at `at`: its wax, its wick, its flame (lit 0 for none)."""
    at = V(at)
    items = [(g.lathe([(r, 0.0), (r * 1.05, h * 0.85), (r * 0.7, h)], n=6, centre=at), mat(wax)),
             (g.tube([at + Z * h, at + Z * (h + r * 0.7)], r * 0.12, n=3), mat("metal_dark"))]
    if lit > 0:
        t = at + Z * (h + r * 0.5)
        items.append((g.tongue([t, t + Vector((r * 0.25, 0, r * 1.2 * lit)), t + Vector((0, 0, r * 3.2 * lit))], [r * 0.9, r * 1.2, r * 0.1], thick=0.6, normal=Y), field(glow, 3.0)))
    return items


def book(c, s, rot=(0, 0, 0), cover="leather_dark", clasp=True):
    """A closed book about c, its spine up; s is its height."""
    c = V(c)
    R = Matrix.Rotation(rot[2], 3, "Z") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[0], 3, "X")
    items = [(g.box(c, (s * 0.78, s * 0.2, s), rot=R), mat(cover)),
             (g.box(c + R @ Vector((0, 0, -s * 0.03)), (s * 0.7, s * 0.14, s * 1.0), rot=R), mat("paper"))]
    if clasp:
        items.append((g.box(c + R @ Vector((0, -s * 0.11, 0)), (s * 0.84, s * 0.03, s * 0.14), rot=R), mat("metal_brass")))
    return items


def crown_points(c, r, n, h, w, tilt=0.0):
    """A ring of upright points round c: a crown."""
    c = V(c)
    geo = None
    for i in range(n):
        a = 2 * math.pi * i / n + tilt
        d = Vector((math.cos(a), math.sin(a), 0))
        geo = g.merge(geo, g.blade(c + d * r, c + d * (r * 1.12) + Z * h, w, normal=d, belly=0.3))
    return geo


def flame(c, r, h, n=3, turn=0.0, lean=(0, 0), tall=None, thick=0.42):
    """Tongues of flame turning round c: n of them, r wide at the root, h tall; lean bends the tips."""
    c = V(c)
    geo = None
    for i in range(n):
        a = 2 * math.pi * i / n + turn
        hh = h * (1.0 + (0.14 * ((i * 3) % 4) if tall is None else tall * i))
        tip = Vector((lean[0] * hh, lean[1] * hh, hh))
        pts = [c + Vector((r * 0.4 * math.cos(a), r * 0.4 * math.sin(a), 0)), c + Vector((r * 0.95 * math.cos(a + 0.25), r * 0.95 * math.sin(a + 0.25), 0)) + tip * 0.3,
               c + Vector((r * 0.55 * math.cos(a + 0.75), r * 0.55 * math.sin(a + 0.75), 0)) + tip * 0.66, c + Vector((r * 0.06 * math.cos(a + 1.2), r * 0.06 * math.sin(a + 1.2), 0)) + tip]
        geo = g.merge(geo, g.tongue(pts, [r * 0.75, r * 1.0, r * 0.62, r * 0.04], thick=thick, normal=(math.cos(a), math.sin(a), 0)))
    return geo


def smoke_thread(base, h, sway=0.05, w=0.035, n=5, bend=None):
    """A thread of smoke rising from base; bend = (height fraction, dx, dy) turns it aside."""
    base = V(base)
    pts, ws = [], []
    for i in range(n + 1):
        t = i / n
        p = base + Vector((sway * math.sin(t * 5.0), sway * 0.6 * math.cos(t * 4.0), h * t))
        if bend and t > bend[0]:
            k = (t - bend[0]) / (1.0 - bend[0])
            p += Vector((bend[1] * k, bend[2] * k, -h * 0.12 * k))
        pts.append(p)
        ws.append(w * (0.6 + 0.9 * math.sin(math.pi * min(1.0, t * 1.1))) if i < n else w * 0.08)
    return g.tongue(pts, ws, thick=0.4)


def puff(c, r, k=3, seed=0.0, squash=0.7):
    """A small cloud: a few rolls about c."""
    c = V(c)
    geo = g.ico(c, r, sub=1, scale=(1.15, 1.0, squash))
    for i in range(k):
        a = seed + i * 2.3
        geo = g.merge(geo, g.ico(c + Vector((r * 0.75 * math.cos(a), r * 0.6 * math.sin(a), r * 0.25 * math.sin(a * 1.7))), r * (0.62 - 0.07 * i), sub=1, scale=(1.1, 1.0, squash), rot=(0, 0, a)))
    return geo


def crystal(base, tip, r, n=5, waist=0.28):
    base, tip = V(base), V(tip)
    d = tip - base
    return g.tube([base, base + d * waist, base + d * 0.78, tip], [r * 0.45, r, r * 0.8, r * 0.03], n=n)


def post(base, h, r=0.03, n=5, cap=True):
    base = V(base)
    geo = g.tube([base, base + Z * h], [r, r * 0.9], n=n)
    if cap:
        geo = g.merge(geo, g.cone(base + Z * h, base + Z * (h + r * 1.2), r * 1.1, n=n))
    return geo


def gear(c, r, teeth=8, thick=0.02, axis=Y):
    """A toothed wheel about c, its axle along `axis`."""
    c = V(c)
    u, v = g._frame(axis)
    a = V(axis).normalized()
    n = teeth * 2

    def rim(off):
        return [c + (u * math.cos(math.pi * k / teeth) + v * math.sin(math.pi * k / teeth)) * (r if k % 2 == 0 else r * 0.72) + a * off for k in range(n)]
    return g.loft([rim(-thick / 2), rim(thick / 2)], caps=True)


# --- a body --------------------------------------------------------------------------------

class Body:
    """What is being built: its pieces, where its sockets are, how its coat is named."""

    def __init__(self, form_id, level, spec, base):
        kit.reset()
        self.id, self.level, self.spec, self.base = form_id, level, spec, base
        self.sil = silhouette_of(base, form_id)
        self.roles = roles_of(self.sil)
        self.items = []
        self.socks = {}
        self.top, self.front, self.mid, self.half = STAND, -0.13, 0.4, 0.16
        self.ground = False       # it stands on the ground: nothing of it may be under z = 0

    # the partner's coat
    def role(self, name):
        return mat(self.roles.get(name, self.roles["main"]))

    @property
    def main(self):
        return self.role("main")

    @property
    def under(self):
        return self.role("under")

    @property
    def trim(self):
        return self.role("trim")

    def mark(self, region, like=None):
        return kit.mark(region, like or self.under)

    def add(self, geo, material, smooth=None):
        if geo and geo[0]:
            self.items.append((geo, mat(material) if isinstance(material, str) else material, smooth))

    def extend(self, items):
        for it in items:
            self.add(*it)

    def frame(self, top, front=None, mid=None, half=None):
        """Where its sockets go: the crown of its head, its front (a y), its middle height, its half-width."""
        self.top = top
        self.front = self.front if front is None else front
        self.mid = top * 0.55 if mid is None else mid
        self.half = self.half if half is None else half

    def socket(self, name, at, rot=None):
        self.socks[name] = [tuple(V(at))] + ([rot] if rot is not None else [])

    def export(self):
        objs = []
        for i, (geo, material, smooth) in enumerate(self.items):
            sm = material.name.startswith(SOFT) if smooth is None else smooth
            objs.append(g.to_object("p%d" % i, geo, material, sm))
        ob = g.join(self.id.replace("-", "_"), objs)
        # stand it on z = 0: the lowest of it there, whatever it was built at
        low = min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
        for v in ob.data.vertices:
            v.co.z -= low
        ob.data.update()
        socks = dict(gh._table(self.top - low, self.front, self.mid - low, self.half, None))
        for name, at in self.socks.items():
            if name in socks:
                bpy.data.objects.remove(socks[name])
            p = Vector(at[0]) - Vector((0, 0, low))
            socks[name] = kit.free_socket(name, p, at[1] if len(at) > 1 else None)
        # The game stands it to its stage's height by this mark. A thing that is low and long (a
        # streak, a line of fire, a pool) is not stood by its crown, or it would fill the room:
        # nothing is more than SPREAD times as far across as the height it is stood to.
        xs, ys = [v.co.x for v in ob.data.vertices], [v.co.y for v in ob.data.vertices]
        ref = max(self.top - low, max(max(xs) - min(xs), max(ys) - min(ys)) / SPREAD)
        path = os.path.join(OUT, self.id + ".glb")
        lines().export_objects([ob], socks, path, ref=ref)
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        log(self.id, "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))
