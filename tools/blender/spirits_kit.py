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

import bmesh
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



def _ramp(name, step, rough=0.9, metal=0.0):
    """A colour of the style's ramps (data/style.json), as a palette entry."""
    import style
    return (tuple(style.ramp(name, step)[:3]), rough, metal)


# The second pass: the ground a floor-lying form carries (a flag floor, a doorstep, a road),
# and what stands on it. All of it weathered and grey, off the ramps, so that the only colour
# on a form is its Path's.
PALETTE.update({
    "wood_grey": _ramp("stone", 1, 0.85), "wood_grey_pale": _ramp("stone", 2, 0.85), "wood_black": _ramp("ink", 3, 0.8),
    "stone_flag": _ramp("slate", 2, 0.95), "stone_flag_pale": _ramp("slate", 3, 0.95), "stone_dark": _ramp("slate", 0, 0.95),
    "stone_step": _ramp("stone", 2, 0.95), "stone_sett": _ramp("slate", 1, 0.95), "earth_grey": _ramp("stone", 1, 0.95),
    "grass_dew": _ramp("verdigris", 2, 0.9), "cloth_grey": _ramp("slate", 2, 0.9), "paper_pale": _ramp("bone", 3, 0.8),
})

# and the corner of a room, the dust on a hand, what fog is dark with and frost is white with
PALETTE.update({
    "plaster": _ramp("stone", 2, 0.95), "plaster_dark": _ramp("stone", 1, 0.95), "plaster_pale": _ramp("stone", 3, 0.95), "brick_dust": _ramp("earth", 3, 0.95),
    "stone_worn": _ramp("stone", 1, 0.95), "mist_black": _ramp("slate", 1, 0.95), "frost_white": _ramp("steel", 4, 0.3),
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


# --- fog, smoke, a bank of cloud: one round surface ---------------------------------------------

_CLOUDS = [0]
_CLOUD_AT = 0.6     # where the surface of a cloud is drawn in the field its balls make


def cloud(balls, res=0.045, keep=None, firm=3.0):
    """One round, lumpy surface about a list of balls: what fog is made of, so that a bank of
    it has one outline and not a line round every roll. A ball is (centre, radius); a third
    value scales it by axis, a fourth turns it about the vertical, and a fifth below 0 takes
    it away from the rest (a hollow). A ball alone comes out at its radius; beside another it
    swells to meet it. `res` is the size of a facet, `keep` thins the surface to about that
    many corners, and `firm` (1 to 10) is how far two rolls stay two."""
    balls = [b for b in balls if b]
    if not balls:
        return None
    _CLOUDS[0] += 1
    name = "cloudof%s" % "".join(chr(97 + int(c)) for c in str(_CLOUDS[0]))       # no number in it: a number makes a family of them
    mb = bpy.data.metaballs.new(name)
    mb.resolution = res
    mb.render_resolution = res
    mb.threshold = _CLOUD_AT
    ob = bpy.data.objects.new(name, mb)
    bpy.context.collection.objects.link(ob)
    k = 2.0 * math.sqrt(1.0 - (_CLOUD_AT / firm) ** (1.0 / 3.0))
    for b in balls:
        c, r = V(b[0]), float(b[1])
        sc = b[2] if len(b) > 2 and b[2] is not None else (1, 1, 1)
        e = mb.elements.new(type="ELLIPSOID")
        e.co = c
        e.radius = 2.0
        e.stiffness = firm
        e.size_x, e.size_y, e.size_z = [max(1e-4, r * s / k) for s in sc]
        if len(b) > 3 and b[3]:
            e.rotation = Matrix.Rotation(b[3], 3, "Z").to_quaternion()
        if len(b) > 4 and b[4] < 0:
            e.use_negative = True
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=res * 0.2)
    if keep and len(bm.verts) > keep:
        ratio = keep / float(len(bm.verts))
        bm.to_mesh(me)
        bm.free()
        tmp = bpy.data.objects.new(name + "thin", me)
        bpy.context.collection.objects.link(tmp)
        tmp.modifiers.new("thin", "DECIMATE").ratio = ratio
        thin = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bpy.data.objects.remove(tmp)
        bpy.data.meshes.remove(me)
        me = thin
        bm = bmesh.new()
        bm.from_mesh(me)
    verts = [v.co.copy() for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    bpy.data.meshes.remove(me)
    return (verts, faces) if faces else None


def strand(points, w, n=6, swell=0.0, flat=1.0, tip=0.04):
    """A strand of fog or smoke or shadow through points: round, w wide at its root, a little
    fuller part of the way along (`swell`), thinning to nothing at its end."""
    pts = [V(p) for p in points]
    m = len(pts) - 1
    radii = [max(w * tip, w * 0.5 * (1.0 - i / m) ** 0.8 * (1.0 + swell * math.sin(math.pi * i / m))) for i in range(m + 1)]
    return g.tube(pts, radii, n=n, flat=flat)


def curve(points, n=4):
    """More points along a line of points, rounded (Catmull-Rom): a wisp that bends, not a wire."""
    pts = [V(p) for p in points]
    if len(pts) < 3:
        return pts
    out = []
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return out


# --- the ground a thing carries: what lies or stands on a floor floats with its floor ------------

def planks(c, length, width, n=4, thick=0.024, turn=0.0, seed=0):
    """A piece of a boarded floor, the middle of its top at c: n boards along x (turned `turn`
    about the vertical), each ending where it likes, on a dark bed. [(geometry, material)]"""
    c = V(c)
    w = width / n
    geo = [None, None]
    for i in range(n):
        x0 = -length / 2 + 0.035 * ((i * 7 + seed) % 3)
        x1 = length / 2 - 0.04 * ((i * 5 + seed) % 3)
        geo[i % 2] = g.merge(geo[i % 2], g.box(((x0 + x1) / 2, -width / 2 + w * (i + 0.5), -thick / 2), (x1 - x0, w - 0.007, thick)))
    bed = g.box((0, 0, -thick * 1.3), (length * 0.86, width * 0.9, thick * 0.7))
    return [(shifted(turned(geo[k], turn), c), mat(name)) for k, name in ((0, "wood_grey"), (1, "wood_grey_pale"))] + [(shifted(turned(bed, turn), c), mat("wood_black"))]


def flags(c, w, d, nx=3, ny=2, thick=0.03, turn=0.0, seed=0, names=("stone_flag", "stone_flag_pale"), bed="stone_dark"):
    """A piece of a flagged floor, the middle of its top at c, w by d: flags of two greys, a
    finger apart and none quite level, on a dark bed. [(geometry, material)]"""
    c = V(c)
    geo = [None, None]
    for i in range(nx):
        for j in range(ny):
            lift = 0.004 * (((i * 3 + j * 5 + seed) % 3) - 1)
            geo[(i + j) % 2] = g.merge(geo[(i + j) % 2], g.box((-w / 2 + w / nx * (i + 0.5), -d / 2 + d / ny * (j + 0.5), -thick / 2 + lift), (w / nx - 0.009, d / ny - 0.009, thick)))
    under = g.box((0, 0, -thick * 1.2), (w * 0.93, d * 0.93, thick * 0.6))
    return [(shifted(turned(geo[k], turn), c), mat(names[k])) for k in (0, 1)] + [(shifted(turned(under, turn), c), mat(bed))]


# --- a body --------------------------------------------------------------------------------

class Body:
    """What is being built: its pieces, where its sockets are, how its coat is named."""

    def __init__(self, form_id, level, spec, base):
        kit.reset()
        self.id, self.level, self.spec, self.base = form_id, level, spec, base
        self.sil = silhouette_of(base, form_id)
        self.roles = roles_of(self.sil)
        self.items = []
        self.movers = []          # the pieces of it that the game moves by their names (move)
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

    def move(self, kind, what, items, pivot, side="", n=None, parent=None, up=None):
        """A piece of it that the game moves by its name (docs/genius-lines.md, "What moves"):
        <kind>_<what>[_l|_r][_<n>], about `pivot`. items: [(geometry, material[, smooth]), ...]
        made where the piece stands in the body. Its own up is Z as it is made, or `up` where
        that is given (an eye that looks up out of a pool shuts along the pool; a ring turns
        about the way it faces). `parent` is another piece (what this returned for it) that
        this one rides: an eye in a head that turns. Returns the piece, to be a parent in its
        turn."""
        assert kind in lines().MOVES, kind
        mv = {"name": "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else ""), "up": None if up is None else V(up).normalized(),
              "items": [it for it in items if it and it[0] and it[0][0]], "pivot": V(pivot).copy(), "parent": parent, "ob": None}
        if mv["items"]:
            self.movers.append(mv)
        return mv

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
        # what moves: each piece an object of its own, named for how it moves
        for mv in self.movers:
            parts = []
            for i, it in enumerate(mv["items"]):
                material = mat(it[1]) if isinstance(it[1], str) else it[1]
                sm = material.name.startswith(SOFT) if len(it) < 3 or it[2] is None else it[2]
                parts.append(g.to_object("%s_p%d" % (mv["name"], i), it[0], material, sm))
            mv["ob"] = g.join(mv["name"], parts)
        moving = [mv["ob"] for mv in self.movers]
        # stand it on z = 0: the lowest of it there, whatever it was built at
        low = min(v.co.z for o in [ob] + moving for v in o.data.vertices)
        for o in [ob] + moving:
            for v in o.data.vertices:
                v.co.z -= low
            o.data.update()
        socks = dict(gh._table(self.top - low, self.front, self.mid - low, self.half, None))
        for name, at in self.socks.items():
            if name in socks:
                bpy.data.objects.remove(socks[name])
            p = Vector(at[0]) - Vector((0, 0, low))
            socks[name] = kit.free_socket(name, p, at[1] if len(at) > 1 else None)
        # The game stands it to its stage's height by this mark. A thing that is low and long (a
        # streak, a line of fire, a pool) is not stood by its crown, or it would fill the room:
        # nothing is more than SPREAD times as far across as the height it is stood to.
        xs, ys = [v.co.x for o in [ob] + moving for v in o.data.vertices], [v.co.y for o in [ob] + moving for v in o.data.vertices]
        ref = max(self.top - low, max(max(xs) - min(xs), max(ys) - min(ys)) / SPREAD)
        # each moving piece turns about its own place, and rides what it was given to ride
        for mv in self.movers:
            at = mv["pivot"] - Vector((0, 0, low))
            if mv["up"] is None:
                lines().set_origin(mv["ob"], at)
            else:       # its own up is not the world's: the piece is turned, and what it is made of turned back
                z = mv["up"]
                x = Y.cross(z)
                x = x.normalized() if x.length > 1e-4 else X.copy()
                M = Matrix.Translation(at) @ Matrix((x, z.cross(x), z)).transposed().to_4x4()
                mv["ob"].data.transform(M.inverted())
                mv["ob"].matrix_world = M
        for mv in self.movers:
            if mv["parent"] is not None and mv["parent"].get("ob") is not None:
                lines().child_of(mv["ob"], mv["parent"]["ob"])
        path = os.path.join(OUT, self.id + ".glb")
        lines().export_objects([ob] + moving, socks, path, ref=ref)
        tris = sum(len(p.vertices) - 2 for o in [ob] + moving for p in o.data.polygons)
        log(self.id, "%d triangles, %d KB%s" % (tris, os.path.getsize(path) // 1024, ", %d moving" % len(moving) if moving else ""))
