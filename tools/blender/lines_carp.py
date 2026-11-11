"""WILDLINE genius lines, the Carp: a fish that swims in the air at its partner's shoulder,
in the field, as if the field were water (docs/genius-lines.md, "The Carp").

    python tools/blender/genius_lines.py carp
    python tools/blender/genius_lines.py carp carp-past-the-gate carp-brocade
    python tools/blender/lines_carp.py gifts        # what a hybrid wears of it: a fin, a tail

A carp is built along its spine. The spine is a pose (level, bent like a bow, climbing,
coiled); the body is a skin of rings about it, shaped by what kind of fish it is; and it is
cut into pieces that the game moves by their names, so that it swims where it hangs: the
head is still, and behind it `wag_body_0`, `wag_body_1` and the tail `wag_body_2` each turn
on the one before. Its shoulder fins are `glide_fin_l` and `_r`, its whiskers `sway_*`, its
eyes `blink_eye_*`, its gill-covers `pulse_gill_*`.

A form's `body` is read as every line's is (a form wears what its parent wears; a key
replaces its parent's; `build` merges). The keys and their styles are in the docs.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE  # noqa: E402

GL = None           # genius_lines, whichever way it was started (set in register)
REF = 0.43          # how high the game's measure of it stands over a fish of size 1 (a Path's carp is 0.7 m long)
FLOAT = 0.17        # how far the lowest of it hangs above its own origin
YAW = -0.3          # it never hangs dead ahead: a fish holding station is always a little across
# The points round the body, from the keel of the belly up its left side, over the back and
# down its right: sixteen, with one narrow face on each side where the line runs by which a
# fish feels the current (the field shows there, when it is old enough).
_SIDE = [-math.pi / 2, -1.08, -0.6, -0.16, 0.04, 0.2, 0.62, 1.08]
ANG = _SIDE + [math.pi / 2] + [math.pi - a for a in reversed(_SIDE[1:])]
N = len(ANG)
LINE_K = (4, 11)    # the faces of the line: left, right

PALETTE.update({
    # the look's roles for the carp (data/genius-looks.json, beast-carp): its partner's coat
    "scale": ((0.5, 0.3, 0.12), 0.35, 0.0), "scale_pale": ((0.78, 0.72, 0.6), 0.35, 0.0), "fin": ((0.36, 0.2, 0.1), 0.5, 0.0),
    # what is its own whatever its coat
    "scale_ink": ((0.03, 0.03, 0.035), 0.4, 0.0), "hide_lip": ((0.72, 0.58, 0.5), 0.5, 0.0), "hide_maw": ((0.13, 0.025, 0.025), 0.6, 0.0),
    "eye_pupil": ((0.008, 0.008, 0.012), 0.15, 0.0), "eye_white": ((0.82, 0.8, 0.72), 0.3, 0.0),
    "bone_barbel": ((0.74, 0.66, 0.54), 0.6, 0.0), "bone_white": ((0.86, 0.85, 0.8), 0.6, 0.0), "bone_horn": ((0.6, 0.52, 0.38), 0.5, 0.0),
    "bone_bud": ((0.5, 0.38, 0.3), 0.9, 0.0), "stone_key": ((0.2, 0.2, 0.215), 0.95, 0.0), "stone_plate": ((0.17, 0.18, 0.2), 0.8, 0.0),
    "stone_silt": ((0.2, 0.19, 0.2), 1.0, 0.0), "stone_silt_dark": ((0.06, 0.055, 0.065), 1.0, 0.0),
    "stone_barnacle": ((0.56, 0.53, 0.46), 0.95, 0.0), "cord_rope": ((0.44, 0.34, 0.2), 0.95, 0.0), "cloth_ribbon": ((0.4, 0.1, 0.08), 0.9, 0.0),
    "glass_ice": ((0.34, 0.48, 0.56), 0.12, 0.0), "glass_spray": ((0.8, 0.87, 0.9), 0.3, 0.0), "iron_lamp": ((0.1, 0.1, 0.115), 0.5, 0.8),
    "brass_lamp": ((0.52, 0.4, 0.15), 0.4, 0.8), "iron_chain": ((0.16, 0.16, 0.18), 0.5, 0.8), "moss_weed": ((0.12, 0.2, 0.1), 0.9, 0.0),
    "earth_mud": ((0.22, 0.165, 0.11), 1.0, 0.0), "earth_crack": ((0.07, 0.05, 0.035), 1.0, 0.0),
})


def log(*a):
    print("[lines_carp]", *a)


# ======================================================================================
# The spine: a pose
# ======================================================================================
# A pose is how the spine turns from the nose to the tail: (pitch, yaw, roll) of the way the
# body runs at t (0 the nose, 1 the root of the tail). Pitch up means the tail end is higher
# there, so a head held up is a negative pitch at the front.

def _c(v):
    return lambda t: v


POSES = {
    "level": (_c(0.0), _c(0.0), 0.0),
    "bow": (lambda t: 0.8 - 1.6 * t, _c(-0.25), 0.0),                                   # the top of a leap
    "climb": (lambda t: -1.12 + 0.3 * math.sin(2 * math.pi * t), lambda t: 0.3 * math.sin(2 * math.pi * t + 0.6), 0.0),
    "rear": (lambda t: -1.05 * (1 - t) ** 1.6, _c(-0.2), 0.0),                          # the head lifted, the rest level
    "rise": (lambda t: -0.8 + 0.35 * t, _c(-0.15), 0.0),                                # mouth first, to a hand
    "dart": (_c(0.03), lambda t: 0.14 * math.sin(2 * math.pi * t), 0.0),
    "glide": (lambda t: -0.2 + 0.1 * t, _c(-0.1), 0.0),
    "broadside": (_c(0.0), _c(-0.67), 0.0),                                             # across the way it is going
    "turn": (_c(0.04), lambda t: -0.2 - 1.15 * t ** 1.3, 0.12),                         # the turn at the end of a length
    "sway": (lambda t: 0.1 * math.sin(2 * math.pi * t), lambda t: -0.35 + 0.55 * math.sin(2 * math.pi * t + 0.4), 0.0),
    "hang": (_c(0.14), _c(-0.3), 0.0),
    "burst": (lambda t: -1.0 + 0.55 * t, lambda t: -0.2 + 0.3 * t, -0.1),
    "nose-down": (lambda t: 0.5 - 0.42 * t, _c(-0.25), 0.0),
    "arch": (lambda t: 0.5 - 1.0 * t, _c(-0.2), 0.0),
    "thrash": (lambda t: 0.12 * math.sin(4 * math.pi * t), lambda t: -0.2 + 0.95 * math.sin(2.3 * math.pi * t), 0.0),
    "lean": (_c(0.0), _c(-0.45), 0.36),
    "curl": (lambda t: 0.3 * t, lambda t: -0.5 - 2.6 * t, 0.0),
    "coil": (lambda t: -0.95 * math.cos(2.5 * math.pi * t), lambda t: -0.25 + 0.8 * math.sin(1.9 * math.pi * t), 0.0),
    # a dragon holding station: its head level and high, and the length of it in two slow waves behind
    "dragon": (lambda t: -1.2 * math.sin(2 * math.pi * 1.5 * max(0.0, t - 0.05) / 0.95), lambda t: 0.28 * math.sin(2 * math.pi * 0.9 * t), 0.0),
    "present": (lambda t: 0.85 * (1 - t) ** 2 - 0.12, _c(-0.2), 0.0),                   # a bow: the crown of the head shown
    "stand": (lambda t: -1.25 + 0.5 * t * t, lambda t: 0.25 * math.sin(2 * math.pi * t), 0.0),
    "crescent": (lambda t: 0.06 * math.sin(2 * math.pi * t), lambda t: -0.75 + 1.5 * t, 0.0),        # bent round whoever it lies against
}

# what kind of fish: (t, half-width, height of the back, depth of the belly), in lengths
SHAPES = {
    "carp": [(0.0, .014, .016, .016), (0.04, .05, .05, .046), (0.12, .074, .082, .07), (0.24, .09, .118, .094), (0.4, .092, .132, .106),
             (0.55, .08, .116, .094), (0.7, .058, .082, .068), (0.84, .034, .052, .044), (0.94, .02, .036, .032), (1.0, .014, .032, .03)],
    "slim": [(0.0, .01, .012, .012), (0.05, .036, .034, .032), (0.14, .054, .054, .05), (0.3, .066, .078, .068), (0.46, .064, .08, .07),
             (0.62, .052, .066, .058), (0.78, .034, .046, .04), (0.9, .02, .03, .026), (1.0, .012, .024, .022)],
    "bull": [(0.0, .04, .036, .034), (0.04, .074, .064, .056), (0.12, .1, .098, .08), (0.24, .112, .128, .1), (0.4, .104, .134, .108),
             (0.55, .086, .116, .094), (0.7, .06, .082, .068), (0.84, .036, .052, .044), (0.94, .022, .036, .032), (1.0, .016, .032, .03)],
    "flat": [(0.0, .05, .014, .012), (0.05, .098, .034, .026), (0.14, .12, .052, .04), (0.26, .108, .07, .052), (0.42, .086, .076, .058),
             (0.6, .06, .064, .052), (0.78, .036, .054, .048), (0.92, .016, .048, .046), (1.0, .008, .044, .044)],
    "round": [(0.0, .03, .03, .03), (0.08, .11, .1, .1), (0.25, .18, .17, .17), (0.45, .2, .19, .19), (0.65, .17, .16, .16),
              (0.82, .09, .09, .09), (0.94, .04, .05, .05), (1.0, .025, .04, .04)],
    "tench": [(0.0, .02, .02, .02), (0.05, .056, .054, .05), (0.14, .08, .09, .08), (0.28, .094, .124, .108), (0.45, .096, .134, .118),
              (0.62, .084, .12, .104), (0.78, .064, .092, .08), (0.9, .046, .07, .062), (1.0, .036, .06, .054)],
    "long": [(0.0, .01, .011, .011), (0.02, .026, .024, .02), (0.05, .037, .038, .028), (0.09, .041, .046, .034), (0.13, .036, .041, .035),
             (0.22, .034, .038, .035), (0.5, .033, .037, .034), (0.78, .026, .029, .027), (0.92, .015, .018, .017), (1.0, .007, .01, .01)],
}
HEAD_T = {"carp": 0.24, "slim": 0.24, "bull": 0.26, "flat": 0.3, "round": 0.3, "tench": 0.22, "long": 0.1}


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(k):
    k = min(1.0, max(0.0, k))
    return k * k * (3 - 2 * k)


class Fish:
    """The spine and the skin of one carp: where it is at t, and how wide and deep."""

    def __init__(self, spec):
        b = spec.get("build", {})
        self.L = float(b.get("len", 0.56))
        self.depth = float(b.get("depth", 1.0))
        self.width = float(b.get("width", 1.0))
        self.head = float(b.get("head", 1.0))
        self.eye = float(b.get("eye", 1.0))
        self.size = float(b.get("size", 1.0))
        self.shape = spec.get("shape", "carp")
        self.pose = spec.get("pose", "level")
        self.ht = HEAD_T[self.shape]
        pitch, yaw, self.roll = POSES[self.pose]
        # the spine, walked in small steps from the nose
        steps = 200
        self._ts = [i / steps for i in range(steps + 1)]
        p = Vector((0, 0, 0))
        self._ps = [p.copy()]
        self._tan = []
        for i in range(steps):
            t = (i + 0.5) / steps
            ph, ps = pitch(t), yaw(t) + YAW
            d = Vector((math.sin(ps), math.cos(ps) * math.cos(ph), math.cos(ps) * math.sin(ph)))
            self._tan.append(d)
            p = p + d * (self.L / steps)
            self._ps.append(p.copy())
        self._tan.append(self._tan[-1])
        # hang it over its own origin
        lo = min(q.z for q in self._ps) - self.L * 0.12 * self.depth
        cx = sum(q.x for q in self._ps) / len(self._ps)
        cy = sum(q.y for q in self._ps) / len(self._ps)
        off = Vector((-cx, -cy, FLOAT - lo))
        self._ps = [q + off for q in self._ps]

    def at(self, t):
        """(point, the way the body runs toward the tail, its side, its up) at t."""
        t = min(1.0, max(0.0, t))
        x = t * (len(self._ts) - 1)
        i = min(int(x), len(self._ts) - 2)
        k = x - i
        p = self._ps[i].lerp(self._ps[i + 1], k)
        d = self._tan[i].lerp(self._tan[min(i + 1, len(self._tan) - 1)], k).normalized()
        side = d.cross(Z)
        side = side.normalized() if side.length > 0.05 else X.copy()
        if side.x < 0 and abs(d.z) > 0.96:
            side = -side
        up = side.cross(d).normalized()
        if self.roll:
            side, up = (side * math.cos(self.roll) + up * math.sin(self.roll)), (up * math.cos(self.roll) - side * math.sin(self.roll))
        return p, d, side, up

    def girth(self, t):
        """(half-width, back, belly) at t, in metres of the model."""
        rows = SHAPES[self.shape]
        for a, b in zip(rows, rows[1:]):
            if t <= b[0]:
                k = smooth((t - a[0]) / max(1e-6, b[0] - a[0]))
                w, u, d = lerp(a[1], b[1], k), lerp(a[2], b[2], k), lerp(a[3], b[3], k)
                break
        else:
            w, u, d = rows[-1][1:]
        hk = 1.0 + (self.head - 1.0) * (1.0 - smooth((t - self.ht * 0.6) / (self.ht * 0.9)))
        return w * self.width * hk * self.L, u * self.depth * hk * self.L, d * self.depth * hk * self.L

    def skin(self, t, a, out=1.0):
        """The point of the skin at t, at angle a round the body (0 its left side, pi/2 its back)."""
        p, d, side, up = self.at(t)
        w, u, dn = self.girth(t)
        s = math.sin(a)
        return p + side * (math.cos(a) * w * out) + up * (s * (u if s >= 0 else dn) * out)

    def frame(self, t):
        """A 4x4 at t: its own right, the way it runs, its up. A piece made in it turns about its up."""
        p, d, side, up = self.at(t)
        M = Matrix.Identity(4)
        for r in range(3):
            M[r][0], M[r][1], M[r][2], M[r][3] = side[r], d[r], up[r], p[r]
        return M


# ======================================================================================
# Pieces
# ======================================================================================

def obj(name, items, frame=None, parent=None):
    """[(geometry, material, smooth), ...] as one object. frame: its own axes and origin (a
    piece the game turns is made in the frame it turns in). parent: the piece it rides."""
    obs = []
    for i, it in enumerate(items):
        geo, m = it[0], it[1]
        if not geo or not geo[0]:
            continue
        obs.append(g.to_object("%s_%d" % (name, i), geo, m, it[2] if len(it) > 2 else False))
    if not obs:
        return None
    ob = g.join(name, obs)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0003)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)       # the skin is made a face at a time: only whole can it tell its outside
    bm.to_mesh(ob.data)
    bm.free()
    if frame is not None:
        ob.data.transform(frame.inverted())
        ob.matrix_world = frame
    if parent is not None:
        bpy.context.view_layer.update()
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def at_point(p):
    return Matrix.Translation(V(p))


def plate(outline, normal, thick, parity=None, band=0.0):
    """A thin flat piece through an outline of points (a fin, a pane): both faces and its edge.
    The outline's first and last points are its root; it is fanned from between them. With
    parity, returns two geometries, every other ray, so a fin can be rayed in two colours.
    With band (a share of the way out), four: the inner part of each ray, then the outer."""
    pts = [V(p) for p in outline]
    n = V(normal).normalized() * (thick / 2.0)
    c = (pts[0] + pts[-1]) / 2.0
    geos = [([], []) for _ in range(4)]
    for i in range(len(pts) - 1):
        par = (i % 2) if parity else 0
        a, b = pts[i], pts[i + 1]
        if band > 0.0:
            a1, b1 = c.lerp(a, band), c.lerp(b, band)
            vs, fs = geos[par]
            o = len(vs)
            vs += [c + n, a1 + n, b1 + n, c - n, a1 - n, b1 - n]
            fs += [(o, o + 1, o + 2), (o + 5, o + 4, o + 3)]
            vs, fs = geos[2 + par]
            o = len(vs)
            vs += [a1 + n, a + n, b + n, b1 + n, a1 - n, a - n, b - n, b1 - n]
            fs += [(o, o + 1, o + 2, o + 3), (o + 7, o + 6, o + 5, o + 4), (o + 1, o + 5, o + 6, o + 2)]
        else:
            vs, fs = geos[par]
            o = len(vs)
            vs += [c + n, a + n, b + n, c - n, a - n, b - n]
            fs += [(o, o + 1, o + 2), (o + 5, o + 4, o + 3), (o + 1, o + 4, o + 5, o + 2)]
    if band > 0.0:
        return geos
    return geos[:2] if parity else geos[0]


def fin_items(outline, normal, thick, style, spec):
    """A fin through an outline, marked as its Path marks its fins (the body's `finmark`):
    rays (every other ray the Path's colour), roots (pale, the colour at the root: a koi's),
    edge (dark, lit along its margin), plain."""
    a, b = _fin_mats(style, spec)
    mark = spec.get("finmark", "rays") if style not in ("foam", "mane", "banner", "claw", "wing") else "rays"
    if style == "veil" and mark == "rays":
        mark = "veil"
    if mark == "roots":
        q = plate(outline, normal, thick, parity=True, band=0.4)
        return [(q[0], mat("accent"), True), (q[1], mat("accent_dark"), True), (q[2], mat("scale_pale"), True), (q[3], mat("fin"), True)]
    if mark == "edge":
        q = plate(outline, normal, thick, parity=True, band=0.7)
        return [(q[0], mat("fin"), True), (q[1], mat("scale"), True), (q[2], mat("accent_light"), True), (q[3], mat("accent"), True)]
    if mark == "veil":      # long and pale, three colours at the hem
        q = plate(outline, normal, thick, parity=True, band=0.66)
        return [(q[0], mat("scale_pale"), True), (q[1], mat("accent_pale"), True), (q[2], mat("accent"), True), (q[3], mat("accent2"), True)]
    if mark == "plain":
        q = plate(outline, normal, thick, parity=True)
        return [(q[0], mat("scale_pale"), True), (q[1], mat("fin"), True)]
    ga, gb = plate(outline, normal, thick, parity=True)
    return [(ga, a, True), (gb, b, True)]


def tori(centre, normal, r, thick, n=16, sides=5, arc=1.0, start=0.0, flat=1.0):
    """A ring (or part of one) about a point, facing along normal; flat squashes it up and down."""
    nrm = V(normal).normalized()
    u = nrm.cross(Z if abs(nrm.z) < 0.9 else X).normalized()
    v = nrm.cross(u).normalized()
    m = max(3, int(n * arc))
    pts = [V(centre) + (u * math.cos(start + 2 * math.pi * arc * i / m) + v * (math.sin(start + 2 * math.pi * arc * i / m) * flat)) * r for i in range(m + 1)]
    return g.tube(pts, [thick] * (m + 1), n=sides, caps=arc < 0.999)


# ======================================================================================
# The skin, painted
# ======================================================================================

STATIONS = [0.0, 0.02, 0.05, 0.09, 0.14, 0.19, 0.24, 0.3, 0.36, 0.42, 0.48, 0.54, 0.6, 0.66, 0.72, 0.78, 0.84, 0.9, 0.95, 1.0]
PATCHES = [(0.11, 1.55, 0.075, 0.95), (0.36, 2.05, 0.1, 0.85), (0.58, 1.1, 0.09, 0.75), (0.8, 1.6, 0.07, 1.0)]
PATCHES2 = [(0.24, 0.85, 0.07, 0.6), (0.47, 1.65, 0.07, 0.7), (0.7, 2.3, 0.07, 0.6), (0.92, 1.5, 0.05, 0.9)]
PATCHES3 = [(0.17, 2.3, 0.05, 0.5), (0.4, 0.9, 0.05, 0.45), (0.65, 1.7, 0.045, 0.5)]


def _in(t, a, patches, k=1.0):
    for pt, pa, rt, ra in patches:
        da = math.atan2(math.sin(a - pa), math.cos(a - pa))
        if ((t - pt) / (rt * k)) ** 2 + (da / (ra * k)) ** 2 < 1.0:
            return True
    return False


def painter(spec, fish, level):
    """What the skin is made of, from the form's scales and marks. The skin is laid in scales:
    a diamond about every other point of it, its front half the coat and its rear half the
    coat's darker trim, so that the rows show; a mark colours whole scales, in two steps of
    the Path's colour. The belly and the line of the side are laid plain. Returns (materials,
    paint(t, a, half, i, k) -> index): t and a the middle of the scale, half "front", "rear",
    "whole" (the belly) or "line"."""
    names = ["scale", "scale_pale", "fin", "accent", "accent_dark", "accent_light", "accent_pale", "accent_deep", "accent2", "accent2_light",
             "accent2_dark", "scale_ink", "hide_lip", "bone_barbel"]
    mats = [mat(n) for n in names] + [field("line", 1.6)]
    ix = {n: i for i, n in enumerate(names)}
    ix["field"] = len(names)
    scales = spec.get("scales", "net")
    marks = {m[0]: float(m[1]) for m in GL.each(spec.get("marks"))}
    carry = {m[0]: float(m[1]) for m in GL.each(spec.get("carry"))}
    lit = (level >= 3 or "line" in marks) and "unlit" not in marks
    zone = {"coin": (fish.ht * 0.98, 0.64), "none": (2.0, 2.0), "plates": (fish.ht * 1.04, 0.95)}.get(scales, (fish.ht * 1.04, 0.95))

    def paint(t, a, half, i, k):
        s = math.sin(a)
        top = abs(math.atan2(math.sin(a - math.pi / 2), math.cos(a - math.pi / 2)))      # how far round from the back
        if half == "line":
            if fish.ht * 1.12 < t < 0.94:
                return ix["field"] if lit else ix["fin"]
            half = "whole"
        scaled = zone[0] < t < zone[1] and half != "whole"
        rear = scaled and half == "rear"

        def two(front, back):
            return back if rear else front

        base = two("scale", "fin")
        if half == "whole" and s < -0.55:
            base = "scale_pale"
            if scales == "plates" and i % 2:
                base = "accent2_light" if spec.get("accent2") else "bone_barbel"          # a belly in bands, as a dragon's is
        if "scuff" in carry and t < 0.07:
            base = "scale_pale"
        # the Path's colour
        if "back" in marks and s > 0.34 and t > 0.05:
            base = two("accent_dark", "accent_deep")
        if "stripe" in marks and top < 0.36 * marks["stripe"] and 0.1 < t < 0.985:
            base = two("accent", "accent_dark")
        if "bands" in marks and s > -0.4 and any(lo < t < lo + 0.06 * marks["bands"] for lo in (0.33, 0.47, 0.61, 0.75, 0.87)):
            base = two("accent_dark", "accent_deep")
        if "dash" in marks and 0.3 < t < 0.9 and 0.45 < s < 0.95 and i % 2 == 0:
            base = "accent_light"
        if "shoulder" in marks and fish.ht * 0.85 < t < fish.ht * 1.6 and s > -0.2:
            base = two("accent", "accent_dark")
        if "patches" in marks and _in(t, a, PATCHES, marks["patches"]):
            base = two("accent", "accent_dark")
        if "faded" in marks and _in(t, a, PATCHES, 1.0):
            base = two("accent_pale", "accent_light")
        if "saddle" in marks and 0.3 < t < 0.7 and s > 0.05:
            base = two("accent", "accent_dark")
        if "mask" in marks and t < fish.ht * 0.84 and s > -0.1:
            base = "accent"
        if "crown" in marks and ((t - fish.ht * 0.52) / 0.07) ** 2 + (top / 0.9) ** 2 < 1.0:
            base = "accent"
        if "brocade" in marks:
            if _in(t, a, PATCHES, 1.05):
                base = two("accent", "accent_dark")
            if _in(t, a, PATCHES2, 1.0):
                base = two("accent2", "accent2_dark")
            if _in(t, a, PATCHES3, 1.0):
                base = "scale_ink"
        if "collar" in marks and fish.ht * 1.0 < t < fish.ht * 1.3:
            base = two("accent", "accent_dark")
        if "spots" in marks and 0.3 < t < 0.92 and -0.3 < s < 0.34 and i % 3 == 0 and half != "whole":
            base = "accent_light"
        if "sheen" in marks and -0.5 < s < 0.34 and (i + 2 * k) % 3 == 0 and t > fish.ht:
            base = "accent2_light"
        if "worn" in marks and half != "whole":
            e = ((t - 0.46) / 0.17) ** 2 + ((s - 0.1) / 0.62) ** 2
            if e < 0.3:
                base = "field"
            elif e < 1.25:
                base = "accent_pale"
        return ix[base]

    return mats, paint


def skin_piece(fish, ts, mats, paint, i0, cap0=True, cap1=True, tuck=0.0):
    """One piece of the body's skin, between two stations: an object's worth of geometry by
    material. i0: the count of the first ring, so the scales run on from piece to piece.
    tuck: how far its front end reaches inside the piece before it, narrower, like the joint
    of a lobster's tail, so that no gap opens where it turns."""
    rings = [[fish.skin(t, a) for a in ANG] for t in ts]
    by = {}

    def tri(mi, a, b, c):
        vs, fs = by.setdefault(mi, ([], []))
        o = len(vs)
        vs += [a, b, c]
        fs.append((o, o + 1, o + 2))

    for j in range(len(rings) - 1):
        i = i0 + j
        t0, t1 = ts[j], ts[j + 1]
        for k in range(N):
            k1 = (k + 1) % N
            A, B, C, D = rings[j][k], rings[j][k1], rings[j + 1][k1], rings[j + 1][k]
            am = (ANG[k] + (ANG[k + 1] if k + 1 < N else ANG[0] + 2 * math.pi)) / 2.0
            if k in LINE_K or math.sin(am) < -0.55:
                mi = paint((t0 + t1) / 2.0, am, "line" if k in LINE_K else "whole", i, k)
                tri(mi, A, B, C)
                tri(mi, A, C, D)
            elif (i + k) % 2 == 0:        # the rear half of the scale about A, the front half of the one about C
                tri(paint(t0, ANG[k], "rear", i, k), A, B, D)
                tri(paint(t1, ANG[k1], "front", i + 1, k1), B, C, D)
            else:                         # the same of B and of D
                tri(paint(t0, ANG[k1], "rear", i, k1), A, B, C)
                tri(paint(t1, ANG[k], "front", i + 1, k), A, C, D)
    first = rings[0]
    if tuck:
        first = [fish.skin(ts[0] - tuck, a, out=0.84) for a in ANG]
        dark = 2      # the trim: a joint is in shadow
        for k in range(N):
            k1 = (k + 1) % N
            tri(dark, first[k], first[k1], rings[0][k1])
            tri(dark, first[k], rings[0][k1], rings[0][k])
    items = [(geo, mats[mi], True) for mi, geo in by.items()]
    for cap, ring, flip in ((cap0, first, True), (cap1, rings[-1], False)):
        if cap:
            c = sum(ring, Vector((0, 0, 0))) / len(ring)
            vs = [c] + list(ring)
            fs = [((0, 1 + (k + 1) % N, 1 + k) if flip else (0, 1 + k, 1 + (k + 1) % N)) for k in range(N)]
            items.append(((vs, fs), mats[2 if tuck and flip else 0], True))
    return items


# ======================================================================================
# Fins
# ======================================================================================

def _fin_mats(style, spec):
    """(the membrane, its rays) for a fin of this style."""
    marks = {m[0] for m in GL.each(spec.get("marks"))}
    if style in ("foam",):
        return mat("glass_spray"), mat("scale_pale")
    if style in ("veil",):
        return mat("accent_light"), mat("accent")
    if style in ("mane", "banner"):
        return mat("accent"), mat("accent_dark")
    if "tips" in marks or "wingbars" in marks:
        return mat("accent"), mat("fin")
    return mat("fin"), mat("accent")


def tail_fin(fish, style, size, spec):
    """The tail, in the frame of the tail's root (x its side, y on along the body, z its up)."""
    w, u, dn = fish.girth(1.0)
    R = fish.L * 0.3 * size
    rnd = random.Random(7)

    def r_of(th):
        k = abs(th) / 1.0
        if style in ("fan", "foam", "ragged"):
            v = 0.78 + 0.22 * math.sin(min(1.0, k) * math.pi * 0.85) - 0.16 * math.exp(-(th / 0.16) ** 2)
        elif style == "fork":
            v = 0.42 + 0.58 * math.sin(min(1.0, k * 1.25) * math.pi / 2) ** 2
        elif style == "scythe":
            v = 0.26 + 0.74 * math.sin(min(1.0, k * 1.2) * math.pi / 2) ** 3
        elif style == "veil":
            v = 0.6 + 0.4 * math.cos(th * 5.0) * 0.5 + (0.55 if th < 0 else 0.0) * min(1.0, -th / 0.7)
        elif style == "paddle":
            v = 0.8 * math.cos(th * 0.75)
        elif style == "eel":
            v = 0.95 * math.cos(th * 1.15) ** 2 + 0.05
        elif style == "banner":
            v = 0.55 + 0.45 * abs(math.sin(th * 4.2))
        elif style == "closed":
            v = 0.95 * math.cos(th * 1.3) ** 1.5 + 0.05
        else:
            v = 0.8
        if style in ("ragged", "foam"):
            v *= 0.72 + 0.4 * rnd.random()
        return max(0.05, v)

    spread = {"fan": 1.0, "foam": 1.05, "ragged": 0.95, "fork": 0.95, "scythe": 0.85, "veil": 1.1, "paddle": 0.85, "eel": 0.55, "banner": 0.8, "closed": 0.34}.get(style, 0.9)
    m = 12
    out = [Vector((0, 0, -dn * 0.9))]
    for j in range(m + 1):
        th = -spread + 2 * spread * j / m
        droop = -0.35 * R * (max(0.0, -th) ** 1.5) if style == "veil" else 0.0
        out.append(Vector((0, math.cos(th) * R * r_of(th), math.sin(th) * R * r_of(th) + droop)))
    out.append(Vector((0, 0, u * 0.9)))
    return fin_items(out, X, fish.L * 0.012, style, spec)


def dorsal_fin(fish, style, size, spec, t0, t1):
    """The fin of the back between two stations, in the model's own space."""
    if style in ("none",) or t1 <= t0:
        return []
    if style == "dragon":
        return dorsal_fin(fish, "mane", size, spec, t0, min(t1, 0.36)) + dorsal_fin(fish, "ridge", size * 1.5, spec, max(t0, 0.36), t1)
    a, b = _fin_mats(style, spec)
    H = fish.L * 0.17 * size
    rnd = random.Random(11)
    full0, full1 = (0.3, 0.7) if style not in ("mane", "ridge", "spines", "veil") else (fish.ht * 0.9, 0.96)
    lo, hi = max(t0, full0), min(t1, full1)
    if hi - lo < 0.02:
        return []
    m = max(3, int((hi - lo) / 0.035))
    base, tips = [], []
    for j in range(m + 1):
        t = lerp(lo, hi, j / m)
        s = (t - full0) / (full1 - full0)
        p, d, side, up = fish.at(t)
        w, u, dn = fish.girth(t)
        root = p + up * (u * 0.96)
        if style == "sail":
            h = H * (0.35 + 0.75 * math.sin(min(1.0, s * 2.4) * math.pi / 2)) * (1.0 - 0.72 * s ** 1.4)
            lean = 0.5
        elif style == "low":
            h = H * 0.42 * math.sin(max(0.02, min(1.0, s)) * math.pi) ** 0.5
            lean = 0.5
        elif style == "round":
            h = H * 0.8 * math.sin(max(0.02, min(1.0, s)) * math.pi) ** 0.7
            lean = 0.3
        elif style == "veil":
            h = H * (0.5 + 0.9 * math.sin(min(1.0, s * 1.2) * math.pi * 0.6)) * (1.0 + 0.12 * math.sin(j * 2.2))
            lean = 1.2
        elif style == "folded":
            h = H * 0.16
            lean = 1.5
        elif style in ("foam", "ragged"):
            h = H * (0.3 + 0.6 * math.sin(min(1.0, s * 2.2) * math.pi / 2)) * (1.0 - 0.6 * s) * (0.6 + 0.6 * rnd.random())
            lean = 0.6
        else:
            h = H * 0.5
            lean = 0.5
        base.append(root)
        tips.append(root + up * h + d * (h * lean))
    if style in ("mane", "ridge", "spines"):
        # a row of tongues: a mane, a saw of spines
        items = []
        count = max(3, int((hi - lo) / (0.05 if style == "mane" else 0.075)))
        for j in range(count):
            t = lerp(lo, hi, (j + 0.5) / count)
            p, d, side, up = fish.at(t)
            w, u, dn = fish.girth(t)
            root = p + up * (u * 0.9)
            if style == "mane":
                h = H * (1.15 - 0.6 * (j / count)) * (0.85 + 0.3 * rnd.random())
                tip = root + up * (h * 0.75) + d * (h * 0.95) + side * ((rnd.random() - 0.5) * h * 0.35)
                items.append((g.tongue([root - d * 0.01, root.lerp(tip, 0.5) + up * h * 0.16, tip], [h * 0.34, h * 0.26, 0.004], thick=0.35, normal=side), a if j % 2 else b, True))
            else:
                h = H * (0.5 if style == "ridge" else 0.85) * (1.0 - 0.5 * abs(j / count - 0.35))
                items.append((g.blade(root - d * (h * 0.3), root + up * h + d * (h * 0.35), h * 0.55, thick=h * 0.12, normal=side, belly=0.2), (b if j % 2 else mat("accent_dark")) if style == "ridge" else mat("bone_horn")))
        return items
    out = [base[0]] + tips + [base[-1]]
    # close it along the back: the outline runs up the front, along the tips, and down the back
    geos = []
    side = fish.at((lo + hi) / 2)[2]
    mark = spec.get("finmark", "rays") if style not in ("foam",) else "rays"
    if style == "veil" and mark == "rays":
        mark = "veil"
    cut = {"roots": 0.4, "edge": 0.68, "veil": 0.66}.get(mark, 0.0)
    pair = {"roots": (("accent", "accent_dark"), ("scale_pale", "fin")), "edge": (("fin", "scale"), ("accent_light", "accent")),
            "veil": (("scale_pale", "accent_pale"), ("accent", "accent2")), "plain": (("scale_pale", "fin"), None)}.get(mark)
    nn = side * (fish.L * 0.0055)
    for j in range(m):
        if cut:
            m0, m1 = base[j].lerp(tips[j], cut), base[j + 1].lerp(tips[j + 1], cut)
            slabs = (([base[j], m0, m1, base[j + 1]], mat(pair[0][j % 2])), ([m0, tips[j], tips[j + 1], m1], mat(pair[1][j % 2])))
        else:
            slabs = (([base[j], tips[j], tips[j + 1], base[j + 1]], mat(pair[0][j % 2]) if pair else (a if j % 2 else b)),)
        for q, mm in slabs:
            vs = [q[0] + nn, q[1] + nn, q[2] + nn, q[3] + nn, q[0] - nn, q[1] - nn, q[2] - nn, q[3] - nn]
            geos.append(((vs, [(0, 1, 2, 3), (7, 6, 5, 4), (1, 5, 6, 2), (0, 4, 5, 1), (2, 6, 7, 3)]), mm, True))
    return geos


def anal_fin(fish, style, size, spec, t):
    """The single fin under the tail's root: a small fan in the body's own plane."""
    p, d, side, up = fish.at(t)
    w, u, dn = fish.girth(t)
    root = p - up * dn * 0.88
    Lf = fish.L * (0.2 if style == "veil" else 0.125) * size
    a, b = _fin_mats(style, spec)
    out = [root - d * Lf * 0.45]
    for j in range(6):
        th = -0.25 + 1.3 * j / 5
        out.append(root + (d * math.sin(th) - up * math.cos(th)) * Lf * (0.7 + 0.3 * math.sin(j / 5 * math.pi)))
    out.append(root + d * Lf * 0.5)
    return fin_items(out, side, fish.L * 0.01, style, spec)


def side_fin(fish, style, size, spec, sg, t=None, low=-0.55):
    """A fin of the shoulder (or the belly), made at its root: returns (items, root point)."""
    t = fish.ht * 1.08 if t is None else t
    p, d, side, up = fish.at(t)
    root = fish.skin(t, low if sg > 0 else math.pi - low, out=0.94)
    outw = side * sg
    Lf = fish.L * 0.24 * size
    a, b = _fin_mats(style, spec)
    marks = {m[0] for m in GL.each(spec.get("marks"))}
    if style == "folded":
        tip = root + d * Lf * 0.9 - up * Lf * 0.12 + outw * Lf * 0.05
        return [(g.blade(root, tip, Lf * 0.3, thick=fish.L * 0.01, normal=outw, belly=0.45), a)], root
    # the fin's own axes: along it, and across it
    if style == "wing":
        along, across, Lf, wide, m = (outw * 0.82 + d * 0.42 + up * 0.38).normalized(), (d * 0.86 + up * 0.5 - outw * 0.1).normalized(), Lf * 2.6, 0.5, 9
    elif style == "swept":
        along, across, wide, m = (outw * 0.45 + d * 0.85 - up * 0.25).normalized(), (d * 0.5 - up * 0.85).normalized(), 0.4, 5
    elif style == "veil":
        along, across, Lf, wide, m = (outw * 0.5 + d * 0.55 - up * 0.68).normalized(), (d * 0.8 + up * 0.3).normalized(), Lf * 1.5, 0.7, 8
    elif style == "claw":
        along, across, Lf, wide, m = (outw * 0.6 - d * 0.35 - up * 0.72).normalized(), (d * 0.9 + outw * 0.2).normalized(), Lf * 1.5, 0.55, 4
    elif style == "shelter":
        along, across, Lf, wide, m = (outw * 0.75 + d * 0.2 - up * 0.63).normalized(), d, Lf * 1.25, 0.95, 8
    elif style == "foam":
        along, across, wide, m = (outw * 0.7 + d * 0.5 - up * 0.5).normalized(), (d * 0.8 - up * 0.4).normalized(), 0.75, 7
    elif style == "belly":      # a fin of the belly: it hangs down and back, its face outward
        along, across, wide, m = (d * 0.62 - up * 0.74 + outw * 0.26).normalized(), (d * 0.8 + up * 0.56 + outw * 0.1).normalized(), 0.62, 5
    else:       # paddle, fan: swept back and down, its face to the side and to what is ahead
        along, across, wide, m = (outw * 0.56 + d * 0.62 - up * 0.55).normalized(), (-outw * 0.1 + d * 0.5 + up * 0.75).normalized(), (0.62 if style == "paddle" else 0.85), 7
    nrm = along.cross(across).normalized()
    rnd = random.Random(5)
    out = [root - across * Lf * 0.1]
    for j in range(m + 1):
        th = -wide + 2 * wide * j / m
        if style == "wing":
            r = 1.0 - 0.5 * (j / m) ** 1.3
        elif style == "claw":
            r = 0.75 + 0.25 * (j % 2)
        elif style == "veil":
            r = 0.7 + 0.3 * math.sin(j * 1.9) ** 2 + 0.25 * (j / m)
        elif style == "foam":
            r = 0.6 + 0.5 * rnd.random()
        else:
            r = 0.72 + 0.28 * math.cos(th * 1.2)
        out.append(root + (along * math.cos(th) + across * math.sin(th)) * Lf * r)
    out.append(root + across * Lf * 0.1)
    items = fin_items(out, nrm, fish.L * 0.01, style, spec)
    if "wingbars" in marks and style == "wing":
        q = plate(out, nrm, fish.L * 0.01, parity=True, band=0.55)
        items = [(q[0], mat("fin"), True), (q[1], mat("accent_dark"), True), (q[2], mat("accent"), True), (q[3], mat("accent_pale"), True)]
    if style == "claw":
        for j in range(1, m + 1, 2):
            tip = out[j + 1]
            items.append((g.cone(tip - along * Lf * 0.04, tip + along * Lf * 0.16 - nrm * Lf * 0.02, Lf * 0.035, n=5), mat("bone_horn")))
    return items, root


# ======================================================================================
# The head: eyes, mouth, whiskers, gills, and what grows on it
# ======================================================================================

BROWS = {     # how a lid sits over an eye: (its tilt, the front end down if less than none; how far above the middle its edge is; how long)
    "keen": (-0.34, 0.3, 1.5), "calm": (0.0, 0.5, 1.45), "heavy": (0.14, 0.12, 1.6), "stern": (-0.5, 0.2, 1.6),
    "mild": (0.16, 0.62, 1.4), "sleepy": (0.05, -0.12, 1.6),
}


def eye(fish, sg, style):
    """One eye, about its own middle: the light of it, its pupil and the glint on it. Returns
    (the items, its middle, the way it looks, its radius, the way out of the head there)."""
    t = fish.ht * (0.5 if style == "top" else 0.46)
    ang = {"top": 1.0, "up": 0.74, "small": 0.3}.get(style, 0.42 - 0.13 * max(0.0, fish.eye - 1.0))
    a = ang if sg > 0 else math.pi - ang
    p, d, side, up = fish.at(t)
    q = fish.skin(t, a)
    out = (q - p).normalized()
    r = fish.L * 0.046 * fish.eye * {"small": 0.62, "old": 0.9}.get(style, 1.0)
    c = q - out * r * (0.4 + 0.12 * max(0.0, fish.eye - 1.0))
    if style in ("top", "up"):
        look = (out * 0.75 + up * 0.6 - d * 0.2).normalized()
    else:
        look = (out * 0.78 - d * 0.52 + up * 0.14).normalized()        # out, and on ahead: at what is coming
    rp = r * (0.48 if style == "old" else 0.58)
    e1 = look.cross(up).normalized()
    e2 = look.cross(e1).normalized()
    M = Matrix.Identity(4)
    base = c + look * (r * 0.74)
    for row in range(3):
        M[row][0], M[row][1], M[row][2], M[row][3] = e1[row], e2[row], look[row], base[row]
    dome = g.moved(g.lathe([(rp, 0.0), (rp * 0.9, r * 0.2), (rp * 0.55, r * 0.29), (rp * 0.02, r * 0.32)], n=14, caps=False), M)
    items = [(g.ico(c, r, sub=1), field("eyes", 3.0), True), (dome, mat("eye_pupil"), True),
             (g.ico(c + look * r * 1.02 + up * r * 0.36 + d * r * 0.26, r * 0.16, sub=0), mat("eye_white"), False)]
    return items, c, look, r, out


def eye_setting(fish, sg, spec, c, look, r, out):
    """What an eye sits in, on the head and still: the dark rim of the socket and the lid over
    it. The lid is what makes a fish look as if it is thinking: a fish has none, and this is a soul."""
    p, d, side, up = fish.at(fish.ht * 0.46)
    items = [(tori(c + out * r * 0.1, out, r * 1.05, r * 0.13, n=14, sides=5), mat("fin"), True)]
    style = spec.get("brow", {"old": "heavy", "small": None, "top": None}.get(spec.get("eyes", "round"), "calm"))
    if style and style in BROWS:
        tilt, edge, length = BROWS[style]
        fwd = (-d - out * (-d).dot(out)).normalized()
        e_up = out.cross(fwd)
        if e_up.dot(up) < 0:
            e_up = -e_up
        c1 = (fwd * math.cos(tilt) + e_up * math.sin(tilt)).normalized()
        c2 = out.cross(c1)
        if c2.dot(up) < 0:
            c2 = -c2
        h = r * 0.46
        mid = c + c2 * (edge * r + h) + out * r * 0.42
        M = Matrix.Identity(4)
        for row in range(3):
            M[row][0], M[row][1], M[row][2], M[row][3] = c1[row], out[row], c2[row], mid[row]
        items.append((g.moved(g.ico((0, 0, 0), 1.0, sub=1, scale=(r * length * 0.6, r * 0.5, h)), M), mat("accent_dark" if "brow" in {m[0] for m in GL.each(spec.get("marks"))} else "scale"), True))
    return items


def mouth(fish, spec):
    """The mouth, on the head: a carp's is thick-lipped and opens forward and down. Returns (items, the middle of it, the way it opens)."""
    L = fish.L
    p, d, side, up = fish.at(0.0)
    w, u, dn = fish.girth(0.03)
    style = spec.get("mouth", "lips")
    lipm = mat("accent") if any(m[0] == "lips" for m in GL.each(spec.get("marks"))) else mat("hide_lip")
    items = []
    if style == "wide":
        # a slit across a flat head, a lip above and a lip below, turned up a little at the corners
        w2 = fish.girth(0.035)[0]
        for dz, th in ((0.3, 0.017), (-0.55, 0.013)):
            q = fish.at(0.014)[0] + up * u * dz
            pts = [q - side * w2 * 1.2 + d * L * 0.03 + up * L * 0.012, q - side * w2 * 0.7 + d * L * 0.006, q - d * L * 0.016, q + side * w2 * 0.7 + d * L * 0.006, q + side * w2 * 1.2 + d * L * 0.03 + up * L * 0.012]
            items.append((g.tube(spline(pts, 2), L * th, n=6), lipm, True))
        return items, p - d * L * 0.01, -d
    gape = style == "gape"
    r = L * (0.03 if not gape else 0.055) * fish.head
    nrm = (-d - up * (0.6 if not gape else -0.55)).normalized()
    c = p - d * L * 0.004 - up * dn * (0.5 if not gape else -0.1)
    flat = 1.0 if gape else 0.42
    items.append((tori(c, nrm, r * 1.15, r * 0.52, n=12, sides=6, arc=0.5, start=math.pi, flat=flat), lipm, True))                    # the upper lip
    items.append((tori(c + d * r * 0.3, nrm, r * 1.0, r * 0.42, n=12, sides=6, arc=0.5, start=0.0, flat=flat), lipm, True))           # the lower
    items.append((g.ico(c - nrm * r * 0.35, r * 0.85, sub=1, scale=(1.0, 1.0, 1.0 if gape else 0.5)), mat("hide_maw"), True))
    return items, c, nrm


def gill_cover(fish, sg, spec):
    """The cover of one gill: a curved plate lying on the head behind the eye, its rear edge
    lifted. It breathes. Returns (items, the point it breathes about)."""
    ht = fish.ht
    marks = {m[0] for m in GL.each(spec.get("marks"))}
    rings = []
    a0, a1 = -0.95, 0.9
    m = 6
    for j in range(m + 1):
        k = j / m
        a = lerp(a0, a1, k)
        aa = a if sg > 0 else math.pi - a
        bulge = math.sin(k * math.pi) ** 0.6
        tf, tr = ht * (0.8 + 0.02 * bulge), ht * (0.86 + 0.2 * bulge)
        rings.append([fish.skin(tf, aa, out=1.0), fish.skin(tr, aa, out=1.075), fish.skin(tr, aa, out=0.97), fish.skin(tf, aa, out=0.93)])
    pivot = fish.skin(ht * 0.8, 0.0 if sg > 0 else math.pi, out=0.98)
    return [(g.loft(rings, caps=True), mat("accent" if "cheek" in marks else "scale_pale" if "pale-cheek" in marks else "scale"), True)], pivot


def taper(n, keys):
    """n values run evenly through the keys."""
    out = []
    for i in range(n):
        x = i / max(1, n - 1) * (len(keys) - 1)
        j = min(int(x), len(keys) - 2)
        out.append(lerp(keys[j], keys[j + 1], x - j))
    return out


def mud_ball(fish):
    """The ball of dried silt a Mud-sleeper has shut itself in: (its middle, its radius, the way its crack faces)."""
    c = sum((fish.at(t)[0] for t in (0.1, 0.3, 0.5, 0.7)), Vector((0, 0, 0))) / 4.0
    return c, fish.L * 0.44, Vector((-0.5, -0.8, 0.26)).normalized()


def spline(pts, sub=3):
    """A smooth run through points (Catmull-Rom)."""
    pts = [V(q) for q in pts]
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        for s in range(sub):
            x = s / sub
            out.append(0.5 * ((2 * P[i]) + (P[i + 1] - P[i - 1]) * x + (2 * P[i - 1] - 5 * P[i] + 4 * P[i + 1] - P[i + 2]) * x * x
                              + (3 * P[i] - P[i - 1] - 3 * P[i + 1] + P[i + 2]) * x * x * x))
    out.append(pts[-1])
    return out


def barbel_points(fish, sg, style, size, which=0):
    """The run of one whisker from the corner of the mouth."""
    t = fish.ht * (0.12 + 0.1 * which)
    root = fish.skin(t, (-0.5 - 0.25 * which) if sg > 0 else math.pi + 0.5 + 0.25 * which, out=0.95)
    p, d, side, up = fish.at(t)
    o = side * sg
    Lb = fish.L * 0.2 * size * (0.6 if which else 1.0)
    if style == "short":
        ks = [(0, 0, 0), (0.35, -0.25, -0.45), (0.5, -0.1, -0.95)]
        Lb *= 0.55
    elif style == "long":
        ks = [(0, 0, 0), (0.45, -0.1, -0.3), (0.7, 0.45, -0.45), (0.75, 1.0, -0.3)]
    elif style == "feelers":
        ks = [(0, 0, 0), (0.5, -0.5, -0.1), (0.9, -0.9, -0.35), (1.15, -1.1, -0.8)] if not which else [(0, 0, 0), (0.3, -0.1, -0.5), (0.4, 0.1, -1.0)]
    elif style == "plumb":
        ks = [(0, 0, 0), (0.22, -0.08, -0.3), (0.26, -0.05, -0.9), (0.26, -0.03, -1.6)]
    elif style == "lash":
        ks = [(0, 0, 0), (0.6, -0.4, 0.1), (1.1, 0.1, 0.35), (1.3, 0.8, 0.1), (1.0, 1.4, -0.2)]
    elif style == "white":
        ks = [(0, 0, 0), (0.4, -0.15, -0.35), (0.55, 0.15, -0.95), (0.5, 0.45, -1.5)]
    elif style == "dragon":       # they stream back along it, in one long wave
        ks = [(0, 0, 0), (0.35, -0.3, -0.05), (0.6, 0.1, 0.1), (0.62, 0.8, 0.3), (0.5, 1.6, 0.15), (0.58, 2.3, 0.4)]
    else:
        return None, None
    pts = [root + (o * x + d * y + up * z) * Lb for x, y, z in ks]
    return pts, Lb


def head_grown(fish, spec):
    """Horn-buds, antlers, a prow: what the head has grown. Still pieces of the head."""
    items = []
    for style, size in GL.each(spec.get("head")):
        for sg in (1, -1):
            t = fish.ht * 0.72
            base = fish.skin(t, 1.05 if sg > 0 else math.pi - 1.05, out=0.9)
            p, d, side, up = fish.at(t)
            o = side * sg
            if style == "cap" and sg > 0:
                pc, dc, sc, uc = fish.at(fish.ht * 0.6)
                wc, ucc, dnc = fish.girth(fish.ht * 0.6)
                M = Matrix.Identity(4)
                top = pc + uc * (ucc * 0.93)
                for row in range(3):
                    M[row][0], M[row][1], M[row][2], M[row][3] = sc[row], dc[row], uc[row], top[row]
                rr = wc * 0.92 * size
                items.append((g.moved(g.lathe([(rr, -ucc * 0.16), (rr * 0.93, ucc * 0.0), (rr * 0.62, ucc * 0.1), (rr * 0.02, ucc * 0.14)], n=16, caps=False), M), mat("accent"), True))
            if style == "buds":
                r = fish.L * 0.026 * size
                items.append((g.ico(base + up * r * 0.7, r, sub=1, scale=(0.9, 0.9, 1.5)), mat("bone_bud"), True))
            elif style == "antlers":
                Lh = fish.L * 0.2 * size
                beam = [base, base + (up * 0.55 + d * 0.5 + o * 0.25) * Lh, base + (up * 0.95 + d * 1.25 + o * 0.5) * Lh, base + (up * 1.5 + d * 1.75 + o * 0.42) * Lh]
                items.append((g.tube(beam, [Lh * 0.1, Lh * 0.08, Lh * 0.058, Lh * 0.012], n=6), mat("bone_horn")))
                for k, (at, rise) in enumerate(((1, 0.62), (2, 0.5))):
                    tb = beam[at]
                    items.append((g.tube([tb, tb + (up * rise + o * 0.34 - d * 0.14) * Lh, tb + (up * (rise + 0.42) + o * 0.3 + d * 0.16) * Lh],
                                         [Lh * 0.062, Lh * 0.042, Lh * 0.01], n=5), mat("bone_horn")))
        if style == "prow":
            # a ship's stem of harbour stone: a wedge up the middle of the face, from under the chin to a crest behind the eyes
            ht, L = fish.ht, fish.L

            def sec(t, top, rise, fwd=0.0, spread=0.6):
                p, d, side, up = fish.at(t)
                w, u, dn = fish.girth(t)
                if top is None:       # the nose itself
                    return [fish.skin(0.006, 0.0), p - d * L * fwd * size, fish.skin(0.006, math.pi)]
                a0 = math.pi / 2 if top else -math.pi / 2
                k = 1.0 if top else -1.0
                apex = p + up * k * ((u if top else dn) + L * rise * size) - d * L * fwd * size
                return [fish.skin(t, a0 - k * spread, out=0.97), apex, fish.skin(t, a0 + k * spread, out=0.97)]

            rings = [sec(ht * 0.6, False, 0.0), sec(ht * 0.32, False, 0.04), sec(0.03, False, 0.035, 0.035), sec(0.0, None, 0.0, 0.1),
                     sec(0.03, True, 0.05, 0.05), sec(ht * 0.35, True, 0.075), sec(ht * 0.72, True, 0.15), sec(ht * 1.05, True, 0.08), sec(ht * 1.4, True, 0.0)]
            items.append((g.loft(rings, caps=True), mat("stone_plate")))
            for sg in (1, -1):       # and a plate on each cheek
                for t, a in ((ht * 0.62, 0.15), (ht * 0.95, -0.25), (ht * 1.2, 0.3)):
                    q = fish.skin(t, a if sg > 0 else math.pi - a, out=1.03)
                    nrm = (q - fish.at(t)[0]).normalized()
                    dd = fish.at(t)[1]
                    items.append((g.blade(q - dd * L * 0.07, q + dd * L * 0.075, L * 0.12, thick=L * 0.016, normal=nrm, belly=0.45), mat("stone_plate")))
    return items


# ======================================================================================
# What it carries and what hangs about it
# ======================================================================================

def carried(fish, spec, pieces):
    """What a form has about it besides itself. pieces: {"head", "b0", "b1"} objects, to ride.
    Returns objects (some moved by the game) to export."""
    out = []
    rnd = random.Random(3)
    for style, size in GL.each(spec.get("carry")):
        L = fish.L
        if style == "spray":
            p, d, side, up = fish.at(1.0)
            items = []
            for j in range(int(5 * size)):
                q = p + d * L * (0.36 + 0.085 * j) + up * L * (0.05 + 0.045 * math.sin(j * 1.7)) + side * L * 0.05 * math.cos(j * 2.3)
                items.append((g.ico(q, L * (0.042 - 0.0045 * j), sub=1, scale=(1, 1, 1.25)), mat("glass_spray"), True))
            out.append(obj("spray", items))
        elif style == "eddy":
            for j, t in enumerate((0.3, 0.62)):
                p, d, side, up = fish.at(t)
                w, u, dn = fish.girth(t)
                out.append(obj("eddy_%d" % j, [(tori(p, d, max(w, u) * 1.75, L * 0.008, n=20, sides=4, arc=0.62, start=0.5 + j * 2.4), mat("glass_spray"), True)],
                               frame=fish.frame(t), parent=None))
        elif style == "wake":
            # the wave it pushes before it: a horseshoe of white water round its head, trailing back along both sides
            p0, d0, s0, u0 = fish.at(0.0)
            w0 = fish.girth(0.06)[0]
            arm = []
            for t, off in ((0.66, 0.3), (0.36, 0.2), (0.13, 0.13)):
                pp, d, side, up = fish.at(t)
                arm.append((pp, side, fish.girth(t)[0] + L * off * size))
            pts = [pp + side * r for pp, side, r in arm]
            pts += [p0 + s0 * (w0 + L * 0.1 * size) - d0 * L * 0.08 * size, p0 - d0 * L * 0.17 * size, p0 - s0 * (w0 + L * 0.1 * size) - d0 * L * 0.08 * size]
            pts += [pp - side * r for pp, side, r in reversed(arm)]
            pts = spline([q - u0 * L * 0.03 for q in pts], 2)
            n = len(pts)
            radii = [L * (0.004 + 0.013 * math.sin(math.pi * j / (n - 1)) ** 2) * math.sqrt(size) for j in range(n)]
            out.append(obj("wake", [(g.tube(pts, radii, n=6, flat=1.7, up=Z), mat("glass_spray"), True)]))
        elif style == "lee":
            pass        # the still water behind it is what its two waves leave between them
        elif style == "fry":
            # the small ones: a line of them along its near side from under its fin to past its tail, and one or two over its back
            groups = {0: [], 1: [], 2: []}
            firsts = {}
            for j in range(int(8 * size)):
                t = 0.36 + 0.15 * j
                pp, d, side, up = fish.at(min(t, 1.0))
                w, u, dn = fish.girth(min(t, 1.0))
                far = (j % 4 == 3)
                c = pp + d * L * max(0.0, t - 1.0) + (side if far else -side) * (w + L * (0.13 + 0.04 * math.sin(j * 1.9))) + up * L * ((0.2 if far else -0.1) + 0.05 * math.cos(j * 2.3))
                fd = -d
                M = Matrix.Identity(4)
                for row in range(3):
                    M[row][0], M[row][1], M[row][2], M[row][3] = side[row], d[row], up[row], c[row]
                s_ = L * (0.062 - 0.003 * j)
                its = groups[j % 3]
                firsts.setdefault(j % 3, c)
                its.append((g.moved(g.ico((0, 0, 0), 1.0, sub=1, scale=(s_ * 0.5, s_ * 1.45, s_ * 0.78)), M), mat("scale_pale"), True))
                its.append((g.blade(c + d * s_ * 1.2, c + d * s_ * 2.7, s_ * 1.5, thick=s_ * 0.14, normal=side), mat("accent")))
                its.append((g.ico(c + fd * s_ * 0.9 + up * s_ * 0.2 - side * s_ * 0.3, s_ * 0.3, sub=0), field("fry", 2.4), False))
            for j, its in groups.items():
                if its:
                    out.append(obj("bob_fry_%d" % j, its, frame=at_point(firsts[j])))
        elif style == "weed":
            for j in range(int(4 * size) + 1):
                t = 0.34 + 0.14 * j
                p, d, side, up = fish.at(t)
                w, u, dn = fish.girth(t)
                root = p + up * u * 0.9 + side * w * 0.3 * math.sin(j * 2.1)
                h = L * (0.2 + 0.07 * math.sin(j * 1.3))
                geo = g.tongue([root, root + up * h * 0.5 + d * h * 0.25, root + up * h * 0.75 + d * h * 0.75, root + up * h * 0.6 + d * h * 1.2], [L * 0.035, L * 0.04, L * 0.03, 0.004], thick=0.25, normal=side)
                out.append(obj("sway_weed_%d" % j, [(geo, mat("moss_weed"), True)], frame=at_point(root), parent=pieces["b0" if t < 0.62 else "b1"]))
        elif style == "seal":
            p, d, side, up = fish.at(0.0)
            c = p - d * L * 0.085 - up * L * 0.03
            items = []
            for sg in (1, -1):
                a0 = c + side * sg * L * 0.07 - up * L * 0.05
                items.append((g.tube([a0, a0 - up * L * 0.07], [L * 0.005, L * 0.005], n=4), mat("cord_rope")))
                items.append((g.box(a0 - up * L * 0.115, (L * 0.06, L * 0.012, L * 0.085)), mat("accent")))
                items.append((g.ico(a0 - up * L * 0.115 - d * L * 0.008, L * 0.02, sub=0, scale=(1, 0.4, 1)), mat("brass_lamp")))
            out.append(obj("sway_seal", items, frame=at_point(c)))
        elif style == "rime":
            items = []
            for j in range(int(12 * size)):
                t = 0.14 + 0.065 * j
                p, d, side, up = fish.at(t)
                w, u, dn = fish.girth(t)
                root = p + up * u * 0.92 + side * w * 0.5 * math.sin(j * 2.6)
                h = L * (0.05 + 0.035 * rnd.random())
                items.append((g.blade(root, root + up * h + side * h * 0.5 * math.sin(j * 2.6), h * 0.42, thick=h * 0.16, normal=d), mat("glass_ice")))
            for j in range(int(5 * size)):      # and the ice that hangs from it
                t = 0.1 + 0.19 * j
                p, d, side, up = fish.at(t)
                w, u, dn = fish.girth(t)
                root = p - up * dn * 0.9
                h = L * (0.12 + 0.07 * rnd.random())
                items.append((g.cone(root + Z * h * 0.1, root - Z * h, h * 0.2, n=5), mat("glass_ice")))
            out.append(obj("rime", items))
        elif style == "pane":
            p, d, side, up = fish.at(0.45)
            w, u, dn = fish.girth(0.45)
            c = p + up * (u + L * 0.1)
            R = Matrix.Rotation(-0.12, 3, "X")
            items = [(g.box(c, (L * 0.66, L * 0.98, L * 0.026), rot=R), mat("glass_ice"))]
            for j, (dx, dy) in enumerate(((0.3, 0.4), (-0.28, 0.3), (0.2, -0.42), (-0.3, -0.36))):
                q = c + side * L * dx + d * L * dy
                items.append((g.blade(q - up * L * 0.02, q - up * L * (0.16 + 0.04 * j), L * 0.07, thick=L * 0.03, normal=d), mat("glass_ice")))
            out.append(obj("pane", items))
        elif style == "shards":
            items = []
            for j in range(9):
                t = 0.2 + 0.085 * j
                p, d, side, up = fish.at(t)
                w, u, dn = fish.girth(t)
                o = (up * (0.8 + 0.5 * rnd.random()) + side * rnd.uniform(-0.8, 0.8) + d * rnd.uniform(-0.3, 0.3)).normalized()
                q = p + o * (u * 1.25 + L * 0.06 * (j % 3))
                items.append((g.blade(q, q + o * L * (0.1 + 0.05 * rnd.random()), L * 0.07, thick=L * 0.022, normal=d + side * rnd.uniform(-0.5, 0.5)), mat("glass_ice")))
            out.append(obj("shards", items))
        elif style == "drops":
            items = []
            for j in range(7):
                p, d, side, up = fish.at(0.25 + 0.1 * j)
                w, u, dn = fish.girth(0.25 + 0.1 * j)
                q = p - up * (dn + L * (0.08 + 0.07 * rnd.random())) + side * w * rnd.uniform(-1, 1)
                items.append((g.ico(q, L * 0.018, sub=1, scale=(0.8, 0.8, 1.5)), mat("glass_spray"), True))
            out.append(obj("drops", items))
        elif style == "tremor":
            p, d, side, up = fish.at(1.0)
            c = p + d * L * 0.16
            items = [(tori(c, d, L * r * size, L * 0.007, n=22, sides=4), field("ring", 1.8), True) for r in (0.16, 0.27)]
            out.append(obj("pulse_tremor", items, frame=at_point(c)))
        elif style == "stone":
            p, d, side, up = fish.at(0.4)
            w, u, dn = fish.girth(0.4)
            c = p + up * (u + L * 0.15)
            items = [(g.ico(c, L * 0.24, sub=1, scale=(1.05, 1.35, 0.72), rot=(0.1, 0.2, 0.3)), mat("stone_key"))]
            for dy in (-0.14, 0.12):
                q = p + d * L * dy
                items.append((tori(q + up * L * 0.07, d, max(w, u) * 1.5, L * 0.016, n=16, sides=5), mat("cord_rope"), True))
            for sg in (1, -1):       # the rope's ends, with a twist of paper on each
                a0 = c + side * sg * L * 0.27 - up * L * 0.04
                items.append((g.tube([a0, a0 - up * L * 0.12 + side * sg * L * 0.03], [L * 0.012, L * 0.01], n=5), mat("cord_rope")))
                items.append((g.blade(a0 - up * L * 0.11, a0 - up * L * 0.25 + side * sg * L * 0.05, L * 0.07, thick=L * 0.006, normal=d), mat("bone_white")))
            out.append(obj("stone", items, parent=pieces["b0"]))
        elif style == "rod":
            p, d, side, up = fish.at(fish.ht * 0.3)
            w, u, dn = fish.girth(fish.ht * 0.3)
            root = p + up * u * 0.9
            pts = [root, root + (up * 0.5 - d * 0.2) * L * 0.4, root + (up * 0.75 - d * 0.75) * L * 0.4, root + (up * 0.5 - d * 1.3) * L * 0.4, root + (up * 0.12 - d * 1.55) * L * 0.4]
            lamp = pts[-1] - up * L * 0.05
            items = [(g.tube(pts, [L * 0.014, L * 0.011, L * 0.008, L * 0.006, L * 0.005], n=5), mat("bone_barbel"), True),
                     (g.ico(lamp, L * 0.05, sub=2), field("lamp", 3.2), True),
                     (g.ico(lamp + up * L * 0.04, L * 0.028, sub=1, scale=(1, 1, 0.6)), mat("accent_dark"), True)]
            out.append(obj("sway_rod", items, frame=at_point(root)))
        elif style == "shiplamp":
            p, d, side, up = fish.at(0.42)
            w, u, dn = fish.girth(0.42)
            c = p + up * (u + L * 0.07)
            s = L * 0.085
            items = [(g.box(c, (s * 1.5, s * 1.5, s * 0.3)), mat("iron_lamp")), (g.ico(c + up * s * 0.95, s * 0.62, sub=1, scale=(1, 1, 1.25)), field("lamp", 3.0), True),
                     (g.box(c + up * s * 1.9, (s * 1.6, s * 1.6, s * 0.28)), mat("iron_lamp")),
                     (g.cone(c + up * s * 2.0, c + up * s * 2.9, s * 0.75, n=4), mat("brass_lamp")), (tori(c + up * s * 3.05, side, s * 0.3, s * 0.07, n=10, sides=4), mat("brass_lamp"))]
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                q = c + side * dx * s * 0.66 + d * dy * s * 0.66
                items.append((g.tube([q, q + up * s * 1.9], [s * 0.07, s * 0.07], n=4), mat("iron_lamp")))
            out.append(obj("shiplamp", items, parent=pieces["b0"]))
        elif style == "barnacles":
            items = []
            for j in range(16):
                t = 0.1 + 0.052 * j
                a = 0.5 + 2.0 * rnd.random()
                q = fish.skin(t, a, out=0.97)
                nrm = (q - fish.at(t)[0]).normalized()
                r = L * (0.018 + 0.022 * rnd.random())
                items.append((g.cone(q - nrm * r * 0.3, q + nrm * r * 1.5, r, n=5), mat("stone_barnacle"), True))
            pc = [(i, it) for i, it in enumerate(items)]
            out.append(obj("barnacles_head", [it for i, it in pc if i < 4]))
            out.append(obj("barnacles_b0", [it for i, it in pc if 4 <= i < 10], parent=pieces["b0"]))
            out.append(obj("barnacles_b1", [it for i, it in pc if i >= 10], parent=pieces["b1"]))
        elif style == "chain":
            p, d, side, up = fish.at(0.5)
            w, u, dn = fish.girth(0.5)
            root = p - up * dn * 0.9 + side * w * 0.3
            items = []
            for j in range(5):
                q = root - up * L * 0.055 * j
                items.append((tori(q, side if j % 2 else d, L * 0.026, L * 0.007, n=8, sides=4), mat("iron_chain"), True))
            out.append(obj("sway_chain", items, frame=at_point(root), parent=pieces["b0"]))
        elif style == "coin":
            p, d, side, up = fish.at(0.3)
            w, u, dn = fish.girth(0.3)
            c = p + up * (u + L * 0.34) - d * L * 0.06
            out.append(obj("bob_coin", [(g.ico(c, L * 0.17, sub=2, scale=(1, 1, 0.1)), field("coin", 2.0), True),
                                        (tori(c, Z, L * 0.2, L * 0.012, n=20, sides=4), mat("accent"), True)], frame=at_point(c)))
        elif style == "ribbons":
            for j in range(5):
                sg = 1 if j % 2 else -1
                t = 0.34 + 0.11 * j
                root = fish.skin(t, 0.1 if sg > 0 else math.pi - 0.1, out=1.0)
                p, d, side, up = fish.at(t)
                o = side * sg
                h = L * 0.5
                geo = g.tongue([root, root + (o * 0.25 + d * 0.5 - up * 0.1) * h, root + (o * 0.2 + d * 1.0 + up * 0.08) * h, root + (o * 0.3 + d * 1.5 - up * 0.1) * h], [L * 0.05, L * 0.055, L * 0.04, 0.004], thick=0.16, normal=up)
                out.append(obj("sway_ribbon_%d" % j, [(geo, mat("accent2_light") if j % 2 else mat("accent_pale"), True)], frame=at_point(root), parent=pieces["b0" if t < 0.62 else "b1"]))
        elif style == "pearl":
            p, d, side, up = fish.at(0.0)
            c = p - d * L * 0.1 - up * L * 0.07
            out.append(obj("bob_pearl", [(g.ico(c, L * 0.045, sub=2), field("pearl", 2.8), True)], frame=at_point(c)))
        elif style == "mudball":
            c, R, look = mud_ball(fish)
            items = [(g.ico(c, R, sub=2, scale=(1.0, 1.0, 0.9)), mat("stone_silt"))]
            # the crack it looks out of, and the flakes coming off it
            e1 = look.cross(Z).normalized()
            e2 = e1.cross(look).normalized()
            crack = [c + (look + e2 * 0.62 + e1 * 0.2).normalized() * R * 0.99, c + (look + e2 * 0.2 - e1 * 0.05).normalized() * R * 0.97, c + (look - e2 * 0.25 + e1 * 0.08).normalized() * R * 0.97, c + (look - e2 * 0.7 - e1 * 0.18).normalized() * R * 0.97]
            items.append((g.tongue(crack, [R * 0.16, R * 0.56, R * 0.5, R * 0.12], thick=0.05, normal=look), mat("accent_deep"), True))
            for j in range(6):
                o = Vector((math.cos(j * 2.4), math.sin(j * 2.4) * 0.8, 0.5 + 0.4 * math.sin(j))).normalized()
                items.append((g.blade(c + o * R * 0.95, c + o * R * 1.2, R * 0.32, thick=R * 0.05, normal=o.cross(Z)), mat("stone_silt")))
            for j in range(3):          # and a few cracks more, lit from inside by the Path's colour
                o = (look + e1 * (0.9 - 0.9 * j) + e2 * (0.5 if j == 1 else -0.35)).normalized()
                items.append((g.blade(c + o * R * 0.985, c + (o + e2 * 0.35 + e1 * 0.1).normalized() * R * 0.985, R * 0.09, thick=R * 0.03, normal=o), mat("accent")))
            out.append(obj("mudball", items))
    return [o for o in out if o is not None]


# ======================================================================================
# A form
# ======================================================================================

def build_form(form_id, level, spec, base=None):
    kit.reset()
    fish = Fish(spec)
    L = fish.L
    mats, paint = painter(spec, fish, level)
    mud = any(s == "mudball" for s, _ in GL.each(spec.get("carry")))
    long_body = fish.shape == "long"
    ts = list(STATIONS) if not long_body else [0.0, 0.01, 0.025, 0.05, 0.075, 0.1, 0.13] + [0.13 + 0.87 * j / 24 for j in range(1, 25)]
    cuts = [fish.ht * 1.25, 0.62] if not long_body else [0.13, 0.35, 0.57, 0.79]
    cuts = [min(ts, key=lambda t: abs(t - c)) for c in cuts]
    bounds = [0.0] + cuts + [1.0]
    objects, pieces = [], {}
    eyes = spec.get("eyes", "round")
    # the head is still; each piece behind it turns on the one before
    prev = None
    count = 0
    for n_piece, (lo, hi) in enumerate(zip(bounds, bounds[1:])):
        seg = [t for t in ts if lo - 1e-9 <= t <= hi + 1e-9]
        first = n_piece == 0
        items = skin_piece(fish, seg, mats, paint, count, tuck=0.0 if first else (0.014 if long_body else 0.035))
        count += len(seg) - 1
        if first:
            items += head_grown(fish, spec)
            its, mc, mn = mouth(fish, spec)
            items += its
            if spec.get("mouth") == "ring":      # what it has been given to keep, held in its lips
                rc = mc + mn * L * 0.03
                objects.append(obj("pulse_ring", [(tori(rc, fish.at(0.0)[1], L * 0.085, L * 0.014, n=18, sides=6), field("ring", 2.6), True)], frame=at_point(rc)))
            for sg in (1, -1):
                _, c, look, r, out = eye(fish, sg, eyes)
                items += eye_setting(fish, sg, spec, c, look, r, out)
        # the fin of its back, and the fins of its belly, ride the piece they are on
        dstyle, dsize = (GL.each(spec.get("dorsal")) or [("sail", 1.0)])[0]
        if not mud:
            items += dorsal_fin(fish, dstyle, dsize, spec, max(lo, 0.0), hi)
        fstyle, fsize = (GL.each(spec.get("fins")) or [("paddle", 1.0)])[0]
        if not mud and not long_body:
            if lo < 0.5 <= hi:            # the two fins of the belly
                for sg in (1, -1):
                    its, _ = side_fin(fish, "folded" if fstyle == "folded" else ("veil" if fstyle == "veil" else "belly"), fsize * 0.62, spec, sg, t=0.5, low=-1.0)
                    items += its
            if lo < 0.76 <= hi and fstyle != "folded":      # and the one behind them
                items += anal_fin(fish, fstyle, fsize, spec, 0.76)
        if long_body and n_piece == 2:               # a dragon has four limbs of fin: these the hind pair
            for sg in (1, -1):
                its, _ = side_fin(fish, "claw", fsize * 0.9, spec, sg, t=(lo + hi) / 2, low=-0.75)
                items += its
        name = "carp_head" if first else "wag_body_%d" % (n_piece - 1)
        ob = obj(name, items, frame=None if first else fish.frame(lo), parent=prev)
        objects.append(ob)
        pieces[["head", "b0", "b1"][min(n_piece, 2)] if not long_body else ("head" if first else "b0" if n_piece < 3 else "b1")] = ob
        prev = ob
    # the tail turns on the last of them
    tstyle, tsize = (GL.each(spec.get("tail")) or [("fan", 1.0)])[0]
    tail_items = tail_fin(fish, tstyle, tsize, spec)
    F1 = fish.frame(1.0)
    tail = obj("wag_body_%d" % (len(bounds) - 2), [(g.moved(it[0], F1),) + tuple(it[1:]) for it in tail_items], frame=F1, parent=prev)
    objects.append(tail)
    # the eyes blink; the fins of the shoulder glide; the whiskers sway; the gills breathe
    for sg, tag in ((1, "l"), (-1, "r")):
        its, c, look, r, out = eye(fish, sg, eyes)
        if not mud:
            objects.append(obj("blink_eye_" + tag, its, frame=at_point(c)))
        elif sg < 0:          # shut in its ball, it looks out of the crack with one eye
            bc, bR, bl = mud_ball(fish)
            ec = bc + bl * bR * 0.84
            r = bR * 0.22
            M = Matrix.Identity(4)
            e1 = bl.cross(Z).normalized()
            e2 = bl.cross(e1).normalized()
            for row in range(3):
                M[row][0], M[row][1], M[row][2], M[row][3] = e1[row], e2[row], bl[row], (ec + bl * r * 0.74)[row]
            rp = r * 0.55
            dome = g.moved(g.lathe([(rp, 0.0), (rp * 0.9, r * 0.2), (rp * 0.55, r * 0.29), (rp * 0.02, r * 0.32)], n=14, caps=False), M)
            objects.append(obj("blink_eye_" + tag, [(g.ico(ec, r, sub=1), field("eyes", 3.0), True), (dome, mat("eye_pupil"), True),
                                                   (g.ico(ec + bl * r * 1.02 + Z * r * 0.36, r * 0.16, sub=0), mat("eye_white"), False)], frame=at_point(ec)))
        if not mud:
            fstyle, fsize = (GL.each(spec.get("fins")) or [("paddle", 1.0)])[0]
            if fstyle != "claw":
                its, root = side_fin(fish, fstyle, fsize, spec, sg)
            else:
                its, root = side_fin(fish, "claw", fsize, spec, sg, t=fish.ht * 1.7, low=-0.75)
            objects.append(obj("glide_fin_" + tag, its, frame=at_point(root)))
            its, pivot = gill_cover(fish, sg, spec)
            objects.append(obj("pulse_gill_" + tag, its, frame=at_point(pivot)))
        bstyle, bsize = (GL.each(spec.get("barbels")) or [("none", 1.0)])[0]
        for which in range(2 if bstyle in ("feelers", "plumb", "dragon") else 1):
            pts, Lb = barbel_points(fish, sg, bstyle if not (bstyle == "dragon" and which) else "long", bsize, which)
            if pts and not mud:
                pts = spline(pts, 3)
                n = len(pts)
                radii = [Lb * (0.05 - 0.04 * j / (n - 1)) * (0.6 if long_body else 1.0) + 0.0012 for j in range(n)]
                bm = mat("bone_white") if bstyle == "white" else (mat("accent_pale") if bstyle in ("dragon", "lash") else mat("bone_barbel"))
                objects.append(obj("sway_barbel%s_%s" % ("2" if which else "", tag), [(g.tube(pts, radii, n=5), bm, True)], frame=at_point(pts[0])))
    objects += carried(fish, spec, pieces)
    objects = [o for o in objects if o is not None]
    # hang it over its own origin: the middle of everything it is, its lowest point a hand above
    bpy.context.view_layer.update()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for ob in objects:
        for v in ob.data.vertices:
            q = ob.matrix_world @ v.co
            for ax in range(3):
                lo[ax], hi[ax] = min(lo[ax], q[ax]), max(hi[ax], q[ax])
    shift = Vector((-(lo[0] + hi[0]) / 2.0, -(lo[1] + hi[1]) / 2.0, FLOAT - lo[2]))
    for ob in objects:
        if ob.parent is None:
            ob.matrix_world = Matrix.Translation(shift) @ ob.matrix_world
    bpy.context.view_layer.update()
    # the usual sockets, from where its parts are
    p0, d0, s0, u0 = fish.at(0.0)
    ph, dh, sh, uh = fish.at(fish.ht * 0.5)
    pm, dm, sm, um = fish.at(0.45)
    pt, dt, st, ut = fish.at(1.0)
    wm, umid, dmid = fish.girth(0.45)
    wh, uhd, dhd = fish.girth(fish.ht * 0.5)
    tup = lambda v: (v.x + shift.x, v.y + shift.y, v.z + shift.z)
    table = {
        "socket_head": [tup(ph + uh * uhd)], "socket_eyes": [tup(ph + uh * uhd * 0.5 - dh * L * 0.03)], "socket_mouth": [tup(p0 - d0 * L * 0.02)],
        "socket_throat": [tup(ph - uh * dhd)], "socket_light": [tup(pm)], "socket_back": [tup(pm + um * umid)], "socket_body": [tup(pm - um * dmid)],
        "socket_tail": [tup(pt)], "socket_grip": [tup(ph + sh * (wh + 0.03))], "socket_arm_l": [tup(pm + sm * wm)], "socket_arm_r": [tup(pm - sm * wm)],
        "socket_limb_fl": [tup(ph + sh * wh * 0.7 - uh * dhd * 0.8)], "socket_limb_fr": [tup(ph - sh * wh * 0.7 - uh * dhd * 0.8)],
        "socket_keepsake": [tup(ph - uh * dhd * 1.15)],
    }
    path = os.path.join(GL.OUT, form_id + ".glb")
    GL.export_objects(objects, kit._sockets(table), path, ref=REF / fish.size)
    kb = os.path.getsize(path) // 1024
    log(form_id, "%d KB" % kb, "TOO LARGE" if kb > 120 else "")


# ======================================================================================
# What a hybrid wears of it: a fin down the back, a fish's tail
# ======================================================================================

def gift_fins():
    """The Carp's fin on another's back: a sail of seven rays, made at the back's socket."""
    out = [Vector((0, -0.2, 0.0))]
    for j in range(8):
        s = j / 7.0
        h = 0.27 * (0.4 + 0.75 * math.sin(min(1.0, s * 2.2) * math.pi / 2)) * (1.0 - 0.7 * s ** 1.5)
        out.append(Vector((0, -0.2 + 0.46 * s + h * 0.35, h)))
    out.append(Vector((0, 0.27, 0.0)))
    ga, gb = plate(out, X, 0.012, parity=True)
    return [kit._part("fins", [(ga, mat("accent")), (gb, mat("fin"))])]


def gift_tail():
    """The Carp's tail in place of another's: a deep fan in two lobes, made at the tail's socket."""
    out = [Vector((0, 0, -0.035))]
    for j in range(13):
        th = -1.0 + 2.0 * j / 12
        r = 0.36 * (0.78 + 0.22 * math.sin(min(1.0, abs(th)) * math.pi * 0.85) - 0.2 * math.exp(-(th / 0.16) ** 2))
        out.append(Vector((0, math.cos(th) * r + 0.1, math.sin(th) * r)))
    out.append(Vector((0, 0, 0.035)))
    ga, gb = plate(out, X, 0.014, parity=True)
    stem = g.tube([(0, -0.02, 0), (0, 0.12, 0)], [0.05, 0.03], n=8)
    return [kit._part("tail", [(ga, mat("fin")), (gb, mat("accent")), (stem, mat("scale"))])]


GIFTS = {"carp-fins": gift_fins, "carp-tail": gift_tail}


def gifts():
    GL.accent({"accent": "jade"})
    for name, fn in GIFTS.items():
        kit.reset()
        GL.accent({"accent": "jade"})
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
        m = sys.modules.get(name)
        if m is not None and getattr(m, "BUILDERS", None) is builders:
            GL = m
    if GL is None:
        import genius_lines
        GL = genius_lines
    builders["carp"] = build_form


if __name__ == "__main__":
    import genius_lines
    GL = genius_lines
    if sys.argv[1:2] == ["gifts"]:
        gifts()
