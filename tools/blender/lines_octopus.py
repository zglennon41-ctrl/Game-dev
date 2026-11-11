"""WILDLINE genius lines, the Octopus (docs/genius-lines.md, "The Octopus").

    python tools/blender/genius_lines.py octopus
    python tools/blender/genius_lines.py octopus octopus-inkling octopus-many-hands
    python tools/blender/lines_octopus.py gifts

The most intelligent animal that is nothing like us. It swims in the field, in the air, and
everything about how it holds itself says it is in water that is not there: nothing of it
stands on anything, its arms trail and curl, its mantle breathes.

Its anatomy is an octopus's and is kept: a mantle (the sack behind the head, which breathes),
a head with two eyes on turrets and a bar for a pupil, a siphon under one eye, and a crown of
eight arms round a mouth underneath, each arm pale and suckered on the side that faces the
mouth. No rig: a body is pieces, and the game moves them by their names (`pulse_mantle`,
`blink_eye_l`, `wave_arm3_1`, `glide_fin_l`, `sway_...`, `spin_...`).

Its colours: the mantle and the backs of its arms are its Path's colour (it changes colour;
here that is in the story), patterned in the steps of that colour. Its face, the roots and
the undersides of its arms and the rims of its eyes are its partner's coat (`hide_octopus`,
`hide_octopus_pale`, `hide_octopus_dark`: data/genius-looks.json, beast-octopus). The field
shows in a ring round each eye and in what a form holds.

A form's `body`:
    mantle  [style, size]   round tall egg flat bell glass
    skin    [pattern, strength]   plain mottle bands stripes rings pale bone hours weather inked glass deep
    eyes    [style, size]   bar wide half
    arms    a pose, one a form (POSES): where each arm goes and what is in it
    holds   what is in its arms (said for the reader; the pose places them)
    house   [style, size]   what it lives in or on: bottle ship-bottle levers wall helm blot
    fins    [style, size]   ear great
    web     [style, size]   skirt parasol cloak
    build   arm girth head  (multiples of 1)
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
from genius_kit import mat, field, PALETTE  # noqa: E402
import style  # noqa: E402

OUT = os.path.join(kit.ROOT, "game", "assets", "genius", "forms")
REF = 0.66          # the height the game stands it to: its arms let down, to the crown of its mantle
SPREAD = 1.7        # nothing is more than this many times as far across as the height it is stood to


def _r(ramp, step):
    return tuple(style.ramp(ramp, step)[:3])


# What an octopus is made of. The three hides are its partner's coat (the look recolours them);
# everything else is named for what it is made of and lies on a ramp.
PALETTE.update({
    "hide_octopus": (_r("rust", 3), 0.5, 0.0), "hide_octopus_pale": (_r("bone", 3), 0.45, 0.0), "hide_octopus_dark": (_r("rust", 1), 0.55, 0.0),
    "eye_gold": ((0.83, 0.51, 0.2), 0.25, 0.0), "pupil_bar": ((0.012, 0.01, 0.014), 0.2, 0.0),
    "glass_bottle": (_r("verdigris", 1), 0.12, 0.0), "glass_bottle_pale": (_r("verdigris", 3), 0.1, 0.0), "glass_bottle_dark": (_r("verdigris", 0), 0.15, 0.0),
    "glass_clear": (_r("steel", 3), 0.08, 0.0), "glass_clear_dark": (_r("steel", 0), 0.1, 0.0), "glass_flesh": (_r("steel", 4), 0.1, 0.0),
    "brass_key": (_r("brass", 3), 0.3, 0.85), "brass_key_dark": (_r("brass", 1), 0.35, 0.85), "iron_pot": (_r("iron", 1), 0.5, 0.7), "iron_pot_light": (_r("iron", 3), 0.45, 0.7),
    "iron_helm": (_r("iron", 3), 0.45, 0.8), "iron_helm_dark": (_r("iron", 1), 0.5, 0.8), "steel_pin": (_r("steel", 2), 0.3, 0.85),
    "wood_post": (_r("umber", 2), 0.85, 0.0), "wood_pale": (_r("umber", 3), 0.8, 0.0), "wood_dark": (_r("umber", 1), 0.85, 0.0),
    "cloth_linen": (_r("bone", 3), 0.95, 0.0), "cloth_linen_dark": (_r("bone", 1), 0.95, 0.0), "cloth_coat": (_r("indigo", 2), 0.95, 0.0), "cloth_coat_light": (_r("indigo", 4), 0.95, 0.0),
    "cloth_sail": (_r("bone", 4), 0.9, 0.0), "paper_page": (_r("bone", 4), 0.8, 0.0), "paper_edge": (_r("bone", 2), 0.8, 0.0), "leather_book": (_r("oxblood", 2), 0.7, 0.0),
    "leather_book_dark": (_r("leather", 1), 0.7, 0.0), "bone_shell": (_r("bone", 3), 0.4, 0.0), "bone_shell_dark": (_r("bone", 1), 0.45, 0.0), "bone_dish": (_r("bone", 4), 0.3, 0.0),
    "bone_pale": (_r("bone", 4), 0.4, 0.0), "bone_mid": (_r("bone", 2), 0.45, 0.0), "stone_wall": (_r("stone", 2), 0.95, 0.0), "stone_wall_dark": (_r("stone", 1), 0.95, 0.0),
    "stone_wall_pale": (_r("stone", 4), 0.95, 0.0), "earth_bed": (_r("earth", 2), 1.0, 0.0), "leaf_sprig": (_r("moss", 3), 0.8, 0.0), "leaf_sprig_dark": (_r("moss", 1), 0.8, 0.0),
    "ink_cloud": (_r("plum", 1), 0.9, 0.0), "ink_cloud_edge": (_r("plum", 2), 0.9, 0.0), "ink_wet": (_r("ink", 0), 0.3, 0.0), "steam_pale": (_r("stone", 4), 0.95, 0.0),
    "mist_cloud": (_r("steel", 2), 0.95, 0.0), "mist_cloud_dark": (_r("slate", 3), 0.95, 0.0), "cord_rope": (_r("leather", 3), 0.9, 0.0), "wax_cork": (_r("umber", 3), 0.8, 0.0),
    "feather_quill": (_r("bone", 4), 0.6, 0.0),
})


def lines():
    """genius_lines, under whichever name it was loaded (it is __main__ when it is run)."""
    m = sys.modules.get("__main__")
    if m is not None and hasattr(m, "export_objects") and hasattr(m, "forms_of"):
        return m
    import genius_lines
    return genius_lines


def log(*a):
    print("[lines_octopus]", *a)


def opt(v, default_size=1.0):
    if v is None or v is False:
        return None, 0.0
    if isinstance(v, (list, tuple)):
        return v[0], float(v[1]) if len(v) > 1 else default_size
    return v, default_size


def M_(name):
    return mat(name) if isinstance(name, str) else name


# ======================================================================================
# Geometry of its own: everything here is wound to face outward, so nothing is re-wound.
# A part is (verts, faces, material or one a face, smooth).
# ======================================================================================

def frame(axis, u=None):
    """Two unit vectors across an axis, u x v = axis."""
    axis = V(axis).normalized()
    if u is None:
        u = Z if abs(axis.dot(Z)) < 0.9 else Y
    u = V(u) - axis * axis.dot(V(u))
    if u.length < 1e-6:
        u = X - axis * axis.dot(X)
    u = u.normalized()
    return u, axis.cross(u).normalized()


def spun(profile, origin=(0, 0, 0), axis=Z, n=12, u=None, squash=(1.0, 1.0), phase=0.0):
    """A profile of (radius, height) spun about an axis; a radius of 0 is a point. Returns
    (verts, faces, tags): a face's tag is (ring, side), for painting it."""
    o = V(origin)
    axis = V(axis).normalized()
    u, v = frame(axis, u)
    verts, rings = [], []
    for r, h in profile:
        if r <= 1e-6:
            rings.append([len(verts)])
            verts.append(o + axis * h)
        else:
            rings.append(list(range(len(verts), len(verts) + n)))
            for k in range(n):
                a = 2 * math.pi * k / n + phase
                verts.append(o + axis * h + (u * (math.cos(a) * squash[0]) + v * (math.sin(a) * squash[1])) * r)
    faces, tags = [], []
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        if len(A) == 1 and len(B) == 1:
            continue
        for k in range(n):
            k2 = (k + 1) % n
            if len(A) == 1:
                faces.append((A[0], B[k2], B[k]))
            elif len(B) == 1:
                faces.append((A[k], A[k2], B[0]))
            else:
                faces.append((A[k], A[k2], B[k2], B[k]))
            tags.append((i, k))
    if len(rings[0]) > 1:
        faces.append(tuple(reversed(rings[0])))
        tags.append((-1, 0))
    if len(rings[-1]) > 1:
        faces.append(tuple(rings[-1]))
        tags.append((len(rings), 0))
    return verts, faces, tags


def turn(profile, origin, axis, material, n=10, u=None, smooth=True, squash=(1.0, 1.0)):
    """A thing turned on a lathe, as a part."""
    vs, fs, tg = spun(profile, origin, axis, n=n, u=u, squash=squash)
    return (vs, fs, M_(material), smooth)


def inside(profile, origin, axis, material, n=10, u=None, smooth=True):
    """The same seen from within (the far wall of a bottle, the hollow of a shell): its faces turned about, its ends left open."""
    vs, fs, tg = spun(profile, origin, axis, n=n, u=u)
    keep = [tuple(reversed(f)) for f, (i, k) in zip(fs, tg) if 0 <= i < len(profile)]
    return (vs, keep, M_(material), smooth)


def ball(c, r, n=8, m=5, scale=(1, 1, 1), axis=Z, u=None):
    """A round thing with its poles on an axis (smoother in outline than an icosphere of its cost)."""
    prof = [(r * math.sin(math.pi * i / m), -r * math.cos(math.pi * i / m)) for i in range(m + 1)]
    prof[0], prof[-1] = (0.0, -r), (0.0, r)
    vs, fs, tg = spun(prof, (0, 0, 0), Z, n)
    uu, vv = frame(axis, u)
    T = Matrix((uu, vv, V(axis).normalized())).transposed()
    c = V(c)
    return [c + T @ Vector((p.x * scale[0], p.y * scale[1], p.z * scale[2])) for p in vs], fs, tg


def blob(c, r, material, n=8, m=5, scale=(1, 1, 1), axis=Z, u=None):
    vs, fs, tg = ball(c, r, n, m, scale, axis, u)
    return (vs, fs, M_(material), True)


def hoop(c, r, t, axis=Z, n=12, sides=4, u=None, squash=1.0):
    """A ring of round section about an axis."""
    c = V(c)
    u, v = frame(axis, u)
    axis = V(axis).normalized()
    verts, faces = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        rad = u * math.cos(a) + v * (math.sin(a) * squash)
        for j in range(sides):
            b = 2 * math.pi * j / sides + math.pi / sides
            verts.append(c + rad * (r + t * math.cos(b)) + axis * (t * math.sin(b)))
    for k in range(n):
        k2 = (k + 1) % n
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append((k * sides + j, k2 * sides + j, k2 * sides + j2, k * sides + j2))
    return verts, faces


def band(c, r, t, material, axis=Z, n=12, sides=3, u=None, squash=1.0):
    return hoop(c, r, t, axis, n, sides, u, squash) + (M_(material), True)


def sheet(rows, two=True):
    """A skin through rows of points (each row the same count): its upper face and, when two,
    its under face as a second geometry (a web, a fin, a cloth: what is seen from both sides)."""
    n = len(rows[0])
    verts = [V(p) for row in rows for p in row]
    top, under = [], []
    for i in range(len(rows) - 1):
        for k in range(n - 1):
            a, b, c, d = i * n + k, i * n + k + 1, (i + 1) * n + k + 1, (i + 1) * n + k
            top.append((a, b, c, d))
            under.append((d, c, b, a))
    return (verts, top), ((list(verts), under) if two else None)


def cloth(rows, top_mat, under_mat=None, smooth=True):
    top, under = sheet(rows)
    return [(top[0], top[1], M_(top_mat), smooth), (under[0], under[1], M_(under_mat or top_mat), smooth)]


def plate(outline, at, x, y, thick, material):
    """A flat thing cut from sheet (a key, a blade, a page): an outline of (x, y), counter-clockwise, given its thickness."""
    at, x, y = V(at), V(x).normalized(), V(y).normalized()
    nz = x.cross(y).normalized()
    n = len(outline)
    top = [at + x * p[0] + y * p[1] + nz * (thick / 2) for p in outline]
    bot = [at + x * p[0] + y * p[1] - nz * (thick / 2) for p in outline]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((k2, k, n + k, n + k2))
    return (top + bot, faces, M_(material), False)


def rod(a, b, r, material, n=5, smooth=True, r1=None):
    """A straight round bar from a to b."""
    a, b = V(a), V(b)
    d = b - a
    return spun([(r, 0.0), (r if r1 is None else r1, d.length)], a, d, n=n)[:2] + (M_(material), smooth)


def wire(points, r, material, n=4, r1=None):
    """A thin round thing through points (a thread, a gooseneck, a stem)."""
    pts = [V(p) for p in points]
    m = len(pts)
    radii = [r + ((r1 if r1 is not None else r) - r) * i / max(1, m - 1) for i in range(m)]
    return soft(g.tube(pts, radii, n=n), material)


def helix(c, axis, r, a0, sweep, drop, n=10, u=None, r1=None):
    """Points going round an axis from angle a0 (degrees) through `sweep`, moving `drop` along it."""
    c = V(c)
    axis = V(axis).normalized()
    uu, vv = frame(axis, u)
    out = []
    for k in range(n + 1):
        t = k / n
        a = math.radians(a0 + sweep * t)
        rr = r + ((r1 if r1 is not None else r) - r) * t
        out.append(c + axis * (drop * t) + (uu * math.cos(a) + vv * math.sin(a)) * rr)
    return out


def make(name, parts):
    """Parts as one object. A part of three (verts, faces, material) is genius_geo's making: it
    is wound here and keeps its planes; a part of four is wound already."""
    obs = []
    for i, p in enumerate(parts):
        if not p or not p[0] or not p[1]:
            continue
        verts, faces, material = p[0], p[1], p[2]
        smooth = p[3] if len(p) > 3 else False
        me = bpy.data.meshes.new("%s_%d" % (name, i))
        me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
        me.update()
        if len(p) <= 3:
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
        if isinstance(material, (list, tuple)):
            slots = []
            for m_ in material:
                if m_ not in slots:
                    slots.append(m_)
                    me.materials.append(m_)
            for poly, m_ in zip(me.polygons, material):
                poly.material_index = slots.index(m_)
        else:
            me.materials.append(material)
        for poly in me.polygons:
            poly.use_smooth = bool(smooth)
        ob = bpy.data.objects.new("%s_%d" % (name, i), me)
        bpy.context.collection.objects.link(ob)
        obs.append(ob)
    if not obs:
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
        bpy.context.collection.objects.link(ob)
        return ob
    return g.join(name, obs)


def turned(ob, pivot, rot=None):
    """Give a piece its own origin and, where it matters, its own axes (the columns of rot)."""
    T = Matrix.Translation(V(pivot)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    ob.data.transform(T.inverted())
    ob.matrix_world = T
    return ob


def hard(geo, material):
    """A thing of genius_geo's making, with its planes kept (a box, a blade)."""
    return (geo[0], geo[1], M_(material))


def soft(geo, material):
    """The same, shaded round (wound here, then smooth)."""
    import bmesh
    me = bpy.data.meshes.new("tmp")
    me.from_pydata([tuple(v) for v in geo[0]], [], [tuple(f) for f in geo[1]])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    bpy.data.meshes.remove(me)
    return (geo[0], faces, M_(material), True)


# ======================================================================================
# The octopus
# ======================================================================================

AZ = (-22.5, 22.5, -67.5, 67.5, -112.5, 112.5, -157.5, 157.5)     # its eight arms, from in front (-Y): even on its right, odd on its left
SECTION = ((40, 0.9), (95, 1.0), (150, 1.0), (210, 1.0), (265, 1.0), (320, 0.9))      # an arm across: flat on the side that faces its mouth
ORAL = 5            # the face of an arm's section that faces its mouth

MANTLES = {         # radius, length, where it is widest, how narrow at the neck, how pointed, how far it leans back (degrees)
    "round": (0.168, 0.33, 0.44, 0.5, 0.0, 46), "tall": (0.122, 0.43, 0.36, 0.55, 0.55, 24), "egg": (0.15, 0.38, 0.38, 0.5, 0.25, 34),
    "flat": (0.2, 0.225, 0.46, 0.55, 0.0, 50), "bell": (0.172, 0.27, 0.34, 0.86, 0.0, 12), "glass": (0.13, 0.47, 0.5, 0.6, 0.0, 6),
}
BLOTCH = ((2, 3, 1.3, 1.7), (5, 6, 1.7, 2.2), (7, 11, 1.5, 2.1), (3, 12, 1.6, 1.8), (6, 1, 1.2, 1.7), (4, 9, 1.0, 1.3), (8, 15, 1.1, 2.0), (1, 7, 0.9, 1.4))
RINGS = ((3, 2), (6, 5), (4, 9), (7, 13), (2, 12), (5, 15))


class Arm:
    def __init__(self):
        self.pts, self.fr, self.rad, self.w = [], [], [], []
        self.i, self.still, self.pieces, self.suckers, self.paint, self.wave = 0, 0.3, 2, None, None, True
        self.lit = None         # (from, to): a share of it that is the field's light
        self.ink = None         # from this share on it is black with ink
        self.knots = ()         # shares at which it is knotted (banded pale)
        self.bare = False       # all one colour (no pale side): a thing made of an arm
        self.extra = {}         # piece -> parts that ride it (what it holds)
        self.objs = []          # its pieces that wave, root first

    def at(self, s):
        """The point (and its frame) a share of the way along."""
        j = min(range(len(self.w)), key=lambda x: abs(self.w[x] - s))
        return self.pts[j], self.fr[j]

    def r_at(self, s):
        return self.rad[min(range(len(self.w)), key=lambda x: abs(self.w[x] - s))]

    @property
    def tip(self):
        return self.pts[-1]

    @property
    def dir(self):
        return self.fr[-1][0]

    def centre(self, share):
        """The middle of the curl its last share makes (what it is wrapped round)."""
        k = max(2, int(round(share * (len(self.fine) - 1))))
        ps = self.fine[-k:]
        return sum(ps, Vector((0, 0, 0))) / len(ps)


class Octo:
    """One form being built: its anatomy, then whatever its pose puts in its arms."""

    def __init__(self, form_id, level, spec):
        kit.reset()
        self.id, self.level, self.spec = form_id, level, spec
        b = spec.get("build", {})
        self.k_arm, self.k_girth, self.k_head = float(b.get("arm", 1.0)), float(b.get("girth", 1.0)), float(b.get("head", 1.0))
        self.path = bool(spec.get("accent"))
        self.skin, self.skin_k = opt(spec.get("skin"), 1.0)
        self.skin = self.skin or "plain"
        self.static, self.mantle_parts, self.arms, self.movers = [], [], [], []
        self.C = Vector((0, 0, 0.0))                 # the middle of its crown of arms: its mouth is under this
        self.tilt = 0.0                              # the whole animal leant forward (radians), put on at the end
        self.lean = None                             # how far its mantle leans back, where a pose says
        self.root_coat = 0.13                        # the share of each arm, from its root, that is still its partner's coat
        self.lid_slant = 0.0                         # how its lids are drawn: above 0 kind (outer ends down), below 0 keen
        self.lid = None
        self.sock = {}
        self.rc = 0.07
        self.mantle_style, self.mantle_at = None, None
        # the names its skin is painted by
        if self.path:
            self.M = {"S": "accent", "D": "accent_dark", "L": "accent_light", "P": "accent_pale", "E": "accent_deep", "K": "accent_dark",
                      "U": "hide_octopus_pale", "H": "hide_octopus", "T": "hide_octopus_dark", "F": "field_tip"}
        else:       # the Starter has not chosen a colour: it is all its partner's coat, and nearly clear
            self.M = {"S": "hide_octopus_pale", "D": "hide_octopus", "L": "hide_octopus", "P": "hide_octopus", "E": "hide_octopus_dark", "K": "hide_octopus",
                      "U": "hide_octopus_pale", "H": "hide_octopus_pale", "T": "hide_octopus_dark", "F": "field_tip"}
            self.root_coat = 0.0
        if self.skin == "pale":
            self.M.update({"S": "accent_pale", "D": "accent_light", "L": "accent", "P": "accent", "K": "accent"})
        elif self.skin == "bone":
            self.M.update({"S": "bone_pale", "D": "accent", "L": "bone_mid", "P": "accent_light", "K": "accent"})
        elif self.skin in ("glass", "weather"):
            self.M.update({"S": "accent_pale", "D": "accent_light", "L": "glass_flesh", "P": "accent", "K": "accent"})
        elif self.skin == "deep":
            self.M.update({"S": "accent_dark", "D": "accent_deep", "L": "accent", "P": "accent_light", "K": "accent_light"})

    def m(self, key):
        name = self.M.get(key, key)
        return field(name[6:], 2.6) if name.startswith("field_") else mat(name)

    # --- the head and the mantle -------------------------------------------------------

    def body(self, mantle=True, eyes=True, siphon=True):
        """Its head, on the crown of its arms; its eyes; its siphon; its mantle behind."""
        hk = self.k_head
        C = self.C
        gk = 0.5 + 0.5 * self.k_girth
        self.rc = 0.07 * self.k_girth * (0.6 + 0.4 * hk)               # the ring its arms leave from
        hc = C + Vector((0, -0.012, 0.086 * hk))
        self.head = hc
        prof = [(0.0, -0.108), (0.074, -0.1), (0.102, -0.06), (0.113, -0.012), (0.115, 0.025), (0.103, 0.066), (0.07, 0.098), (0.0, 0.11)]
        vs, fs, tg = spun([(r * hk * gk, h * hk) for r, h in prof], hc, Z, n=12, squash=(1.0, 0.95))
        self.static.append((vs, fs, [self.m("H") if i > 1 else self.m("U") for i, k in tg], True))
        if eyes:
            st, sz = opt(self.spec.get("eyes"), 1.0)
            self.eyes(st or "bar", sz)
        if siphon:      # a short funnel under its right eye (the side the world mostly sees)
            s0 = hc + Vector((-0.078 * hk * gk, -0.03 * hk, -0.036 * hk))
            sd = Vector((-0.8, -0.3, -0.42)).normalized()
            vs, fs, tg = spun([(0.031 * hk, -0.02), (0.028 * hk, 0.035 * hk), (0.021 * hk, 0.058 * hk), (0.013 * hk, 0.05 * hk), (0.0, 0.03 * hk)], s0, sd, n=7)
            self.static.append((vs, fs, [self.m("U") if i < 2 else self.m("T") for i, k in tg], True))
        if mantle:
            self.mantle()

    def eye(self, E, e, re, st, side, sg, up=None, brow=True, lid=None):
        """One eye at E, looking along e: a turret, a ring of the field at its rim, gold with a
        bar across it, and a lid drawn part of the way down. It shuts along its own up."""
        e = V(e).normalized()
        up = Z if up is None else V(up)
        up = (up - e * e.dot(up)).normalized()
        sv = up.cross(e).normalized()
        hk = self.k_head
        self.static.append(turn([(re * 1.5, -0.05 * hk), (re * 1.3, -re * 0.22), (re * 1.17, 0.0)], E, e, self.m("T"), n=9, u=up))
        self.static.append(band(E + e * re * 0.04, re * 1.12, re * 0.13, field("eye", 2.6), axis=e, n=10, sides=3, u=up))
        d = re * 0.5
        dome = turn([(re, -re * 0.1), (re * 0.95, d * 0.3), (re * 0.72, d * 0.72), (re * 0.36, d * 0.95), (0.0, d)], E, e, "eye_gold", n=8, u=up)
        wide, tall = (0.94, 0.52) if st != "wide" else (0.85, 0.64)
        pupil = blob(E, 1.0, "pupil_bar", n=8, m=4, scale=(re * wide, re * tall, d * 1.12), axis=e, u=sv)
        self.mover("blink", "eye", [dome, pupil], E, side=side, rot=Matrix((sv, -e, up)).transposed())
        lid = {"bar": 0.2, "wide": 0.0, "half": 0.42}.get(st, 0.2) if lid is None else lid
        if lid > 0.0:       # a lid: its own skin, drawn part of the way down
            cut = re * (1.0 - 2.0 * lid)
            a = 0.28 * sg * self.lid_slant
            slant = up * math.cos(a) + sv * math.sin(a)
            vs, fs, tg = spun([(re * 1.13, -re * 0.1), (re * 1.1, d * 0.3), (re * 0.86, d * 0.8), (re * 0.45, d * 1.08), (0.0, d * 1.16)], E, e, n=10, u=up)
            keep = [f for f in fs if (sum((vs[i] for i in f), Vector((0, 0, 0))) / len(f) - E).dot(slant) > cut]
            self.static.append((vs, keep, self.m("H"), True))
        if brow:            # a small horn of skin over each eye, as an octopus has
            b0 = E + up * re * 1.02 - e * re * 0.5
            self.static.append(turn([(re * 0.4, 0.0), (re * 0.27, re * 0.5), (0.0, re * 1.0)], b0, (up * 0.9 - e * 0.3 + sv * 0.3 * sg).normalized(), self.m("T"), n=5))

    def eyes(self, st, size):
        """Large, set wide, looking a little outward."""
        hk = self.k_head
        gk = 0.5 + 0.5 * self.k_girth
        re = 0.046 * size * (0.55 + 0.45 * hk)
        self.eye_r = re
        self.eye_at = []
        for sg, side in ((-1, "r"), (1, "l")):
            e = Vector((sg * 0.6, -0.76, 0.22)).normalized()
            E = self.head + Vector((sg * 0.08 * hk * gk, -0.07 * hk, 0.04 * hk)) + e * (0.014 + re * 0.3)
            self.eye_at.append((E, e))
            self.eye(E, e, re, st, side, sg, lid=self.lid)

    def profile(self, st, R, H, rings=10):
        _, _, mid, neck, point, _ = MANTLES[st]
        prof = []
        for i in range(rings + 1):
            u_ = i / rings
            if u_ < mid:
                r = R * (neck + (1.0 - neck) * math.sin(math.pi / 2 * u_ / mid) ** 0.8)
            else:
                r = R * max(0.0, 1.0 - ((u_ - mid) / (1.0 - mid)) ** 2) ** (0.5 + 0.5 * point)
            prof.append((r if i < rings else 0.0, H * (u_ - 0.1)))
        return prof

    def mantle(self, window=None):
        """The sack behind its head. window: sides of it left open (glass with something inside)."""
        st, size = opt(self.spec.get("mantle"), 1.0)
        st = st or "round"
        R, H, mid, neck, point, lean = MANTLES.get(st, MANTLES["round"])
        lean = lean if self.lean is None else self.lean
        gk = 0.45 + 0.55 * self.k_girth
        R, H = R * (0.5 + 0.5 * size) * gk, H * size
        self.mantle_style = st
        N = self.head + Vector((0, 0.04 * self.k_head, 0.03 * self.k_head))
        axis = Vector((0, math.sin(math.radians(lean)), math.cos(math.radians(lean))))
        rings = 10
        prof = self.profile(st, R, H, rings)
        vs, fs, tg = spun(prof, N, axis, n=16, u=Vector((0, -1, 0)))
        self.mantle_at, self.mantle_axis, self.mantle_R, self.mantle_H = N, axis, R, H
        self.mantle_top = N + axis * H * 0.9
        keep, mats = [], []
        for f, (i, k) in zip(fs, tg):
            if window and k in window and 2 <= i <= 7:
                continue
            keep.append(f)
            mats.append(self.m(self.mantle_paint(i, k, rings, 16)))
        self.mantle_parts.append((vs, keep, mats, True))
        if window:      # the far wall of it, seen through the opening
            vs, fs, tg = spun([(r * 0.93, h) for r, h in prof], N, axis, n=16, u=Vector((0, -1, 0)))
            self.mantle_parts.append((vs, [tuple(reversed(f)) for f, (i, k) in zip(fs, tg) if 1 <= i <= 8 and k not in window], self.m("glass_clear_dark"), True))

    def mantle_point(self, u_, a, lift=1.0):
        """A point on the mantle: u_ of the way along it, a degrees round it from its front (to its left)."""
        prof = self.profile(self.mantle_style, self.mantle_R, self.mantle_H, 40)
        r, h = prof[max(0, min(40, int(round(u_ * 40))))]
        uu, vv = frame(self.mantle_axis, Vector((0, -1, 0)))
        rad = uu * math.cos(math.radians(a)) + vv * math.sin(math.radians(a))
        return self.mantle_at + self.mantle_axis * h + rad * r * lift, rad

    def mantle_paint(self, i, k, rings, n):
        """The pattern of its skin on the mantle: ring i of `rings` from the neck, side k of n from its front."""
        s, kk = self.skin, self.skin_k
        front = min(k, n - k) / (n / 2.0)       # 0 in front (its belly side), 1 behind
        if i < 0 or i >= rings:
            return "S"
        if not self.path:       # the Starter: clear, a blush of its partner's coat at the crown
            return "D" if i >= 7 else "S"
        if s == "mottle" and kk > 0:
            for i0, k0, ri, rk in BLOTCH[: int(4 + 4 * min(1.0, kk))]:
                dk = min(abs(k - k0), n - abs(k - k0))
                if ((i - i0) / ri) ** 2 + (dk / rk) ** 2 < 1.0:
                    return "D"
            return "L" if (front < 0.3 and i < 4) else "S"
        if s == "bands":
            return "D" if (i + 1) % 4 >= 2 else "S"
        if s == "stripes":
            return "P" if i % 3 == 1 else ("D" if i % 3 == 2 and kk >= 1 else "S")
        if s == "rings":
            for i0, k0 in RINGS:
                dk = min(abs(k - k0), n - abs(k - k0))
                di = abs(i - i0)
                if di == 0 and dk == 0:
                    return "D"
                if max(di, dk) == 1:
                    return "P"
            return "S"
        if s == "hours":
            return "D" if i in (1, 2) else ("L" if i in (5,) else "S")
        if s == "pale":
            return "L" if i in (1, 2) else ("P" if i == 6 else "S")
        if s == "bone":
            return "D" if i in (2, 5) else ("P" if i == 8 else "S")
        if s in ("glass", "weather"):
            return "P" if (i <= 2 or i == 6) else ("L" if i >= 9 else "S")
        if s == "deep":
            return "L" if i == 3 else ("D" if i in (6, 7) else "S")
        if s == "inked":
            return "D" if (i + 1) % 4 >= 2 else "S"
        return "L" if (front < 0.3 and i < 5) else "S"

    def arm_paint(self, a, j, k, s):
        """The pattern on an arm: ring j, side k, s of the way along."""
        if a.lit and a.lit[0] <= s <= a.lit[1]:
            return "F"
        if a.ink is not None and s >= a.ink:
            return "ink_wet"
        if k == ORAL and not a.bare:
            return "U"
        if s < self.root_coat:
            return "H"
        for kn in a.knots:
            if abs(s - kn) < 0.035:
                return "P"
        sk, kk = self.skin, self.skin_k
        if not self.path:
            return "D" if s > 0.72 else "S"
        if sk == "mottle" and kk > 0:
            return "D" if math.sin(j * 1.3 + a.i * 2.0) > 0.55 / kk and k in (1, 2, 3) else "S"
        if sk in ("bands", "inked"):
            return "D" if j % 4 >= 2 else "S"
        if sk == "stripes":
            return "P" if j % 3 == 1 else "S"
        if sk == "rings":
            return "P" if j % 3 == 1 else "S"
        if sk == "hours":
            return "P" if j % 2 == 1 and k in (1, 2, 3) else "S"
        if sk == "pale":
            return "P" if s > 0.8 else "S"
        if sk == "bone":
            return "D" if j % 4 == 2 else "S"
        if sk in ("glass", "weather"):
            return "P" if j % 4 == 3 else ("D" if s > 0.86 else "S")
        if sk == "deep":
            return "L" if s > 0.86 else "S"
        return "S"

    # --- its arms ------------------------------------------------------------------------

    def root(self, i, az=None):
        a = math.radians(AZ[i] if az is None else az)
        d = Vector((math.sin(a), -math.cos(a), 0.0))
        return self.C + d * self.rc + Vector((0, 0, 0.012)), d

    def _new(self, i, n, pieces, still, suckers, wave, paint, lit=None, ink=None, knots=(), bare=False):
        a = Arm()
        a.i, a.still, a.pieces, a.suckers, a.wave, a.paint = i, still, pieces, suckers, wave, paint
        a.lit, a.ink, a.knots, a.bare = lit, ink, knots, bare
        return a

    def _rings(self, a, pts, fr, w, n, r, tipr, swell):
        a.fine = pts
        fine = len(pts) - 1
        r0 = 0.047 * self.k_girth * r
        for jn in range(n + 1):
            target = w[-1] * jn / n
            q = min(range(len(w)), key=lambda x: abs(w[x] - target))
            s = q / fine
            a.pts.append(pts[q])
            a.fr.append(fr[q])
            rr = tipr + (r0 - tipr) * (1.0 - s) ** 0.85
            if swell:
                rr *= 1.0 + sum(k_ * math.exp(-((s - c_) / w_) ** 2) for c_, w_, k_ in swell)
            a.rad.append(rr)
            a.w.append(s)
        self.arms.append(a)
        return a

    def arm(self, i, out, turns, L=1.0, r=1.0, az=None, n=11, pieces=2, still=0.3, suckers=None, wave=True, yaw=0.0, tipr=0.006,
            root=None, d0=None, o0=None, paint=None, swell=None, **kw):
        """Lay one arm out as a turtle walks: from its place on the crown, leaving `out` degrees
        from straight down (90 level, 180 straight up), then by `turns`: [(share of its length,
        curl in degrees, to the side in degrees, roll in degrees)]. A curl above 0 is away from
        its mouth (a tip that curls up and shows its pale side); below 0 is round its mouth's
        side (a grip). To the side above 0 is toward its back. The first `still` of it is part
        of the body; the rest is `pieces` pieces that wave, each the child of the one before."""
        a = self._new(i, n, pieces, still, suckers, wave, paint, **kw)
        p0, dr = self.root(i, az)
        if root is not None:
            p0 = V(root)
        sgn = 1.0 if (AZ[i] if az is None else az) < 0 else -1.0
        if d0 is None:
            o = math.radians(out)
            d = dr * math.sin(o) - Z * math.cos(o)
            oo = -dr * math.cos(o) - Z * math.sin(o)
            if yaw:
                Ry = Matrix.Rotation(math.radians(yaw) * -sgn, 3, "Z")
                d, oo = Ry @ d, Ry @ oo
        else:
            d = V(d0).normalized()
            oo = V(o0) if o0 is not None else -Z
        oo = (oo - d * oo.dot(d)).normalized()
        b = d.cross(oo)
        L = L * 0.5 * self.k_arm
        fine = 84
        tot = sum(t[0] for t in turns)
        pts, fr, w = [p0.copy()], [(d.copy(), oo.copy(), b.copy())], [0.0]
        for q in range(fine):
            s = (q + 0.5) / fine
            acc = 0.0
            for t in turns:
                share = t[0] / tot
                if s <= acc + share + 1e-9:
                    break
                acc += share
            curl = math.radians(t[1]) / (share * fine)
            side = math.radians(t[2]) / (share * fine) if len(t) > 2 else 0.0
            roll = math.radians(t[3]) / (share * fine) if len(t) > 3 else 0.0
            if curl:
                Rm = Matrix.Rotation(-curl, 3, b)
                d, oo = Rm @ d, Rm @ oo
            if side:
                Rm = Matrix.Rotation(side * sgn, 3, oo)
                d, b = Rm @ d, Rm @ b
            if roll:
                Rm = Matrix.Rotation(roll * sgn, 3, d)
                oo, b = Rm @ oo, Rm @ b
            pts.append(pts[-1] + d * (L / fine))
            fr.append((d.copy(), oo.copy(), b.copy()))
            w.append(w[-1] + 1.0 + (abs(curl) + abs(side)) * 9.0)
        return self._rings(a, pts, fr, w, n, r, tipr, swell)

    def arm_pts(self, i, pts, toward=None, o0=None, root=True, r=1.0, n=11, pieces=2, still=0.3, suckers=None, wave=True, tipr=0.006, paint=None, swell=None, **kw):
        """An arm through given points (after its own place on the crown, unless root is False).
        toward: what the side that faces its mouth is turned to (a point, or a function of a
        point): what it grips."""
        a = self._new(i, n, pieces, still, suckers, wave, paint, **kw)
        P = [V(p) for p in pts]
        p0, dr = self.root(i)
        if root:
            P = [p0] + P
        seg = [max(1e-6, (P[k + 1] - P[k]).length) for k in range(len(P) - 1)]
        tot = sum(seg)
        fine = 84
        fp = []
        for q in range(fine + 1):
            s = tot * q / fine
            k = 0
            while k < len(seg) - 1 and s > seg[k]:
                s -= seg[k]
                k += 1
            t = min(1.0, s / seg[k])
            A, B, C_, D = P[max(k - 1, 0)], P[k], P[k + 1], P[min(k + 2, len(P) - 1)]
            fp.append(0.5 * ((2 * B) + (C_ - A) * t + (2 * A - 5 * B + 4 * C_ - D) * t * t + (3 * B - A - 3 * C_ + D) * t * t * t))
        fr, w = [], [0.0]
        for q in range(fine + 1):
            d = (fp[min(q + 1, fine)] - fp[max(q - 1, 0)])
            d = d.normalized() if d.length > 1e-9 else (fr[-1][0] if fr else Z)
            if toward is not None:
                v = toward(fp[q]) if callable(toward) else (V(toward) - fp[q])
                oo = v - d * v.dot(d)
            elif q == 0:
                oo = V(o0) if o0 is not None else (-Z if abs(d.z) < 0.85 else -dr * (1.0 if d.z < 0 else -1.0))
                oo = oo - d * oo.dot(d)
            else:
                oo = fr[-1][1] - d * fr[-1][1].dot(d)
            oo = oo.normalized() if oo.length > 1e-6 else frame(d)[0]
            fr.append((d, oo, d.cross(oo)))
            if q:
                w.append(w[-1] + 1.0 + d.angle(fr[-2][0], 0.0) * 9.0)
        a.length = tot
        return self._rings(a, fp, fr, w, n, r, tipr, swell)

    def pair(self, p, out, turns, **kw):
        """The two arms of a pair, as mirrors of each other."""
        return self.arm(2 * p, out, turns, **kw), self.arm(2 * p + 1, out, turns, **kw)

    def hold(self, a, parts, piece=-1):
        """Put a thing in an arm: it rides that arm's piece (the last, unless said)."""
        a.extra.setdefault(piece, []).extend(parts)

    def mover(self, kind, what, parts, pivot, side="", n=None, parent=None, rot=None):
        """A piece the game moves by its name (docs/genius-lines.md, "What moves"). parent: an
        arm (its last piece), "mantle", or nothing. rot: its own axes, where the way it turns
        matters (a wave nods about its own X; an eye shuts along its own Z)."""
        self.movers.append((kind, what, parts, V(pivot), side, n, parent, rot))

    def _arm_parts(self, a):
        """The pieces of an arm: [(first ring, last ring, parts)], the still share first."""
        n = len(a.pts) - 1
        j_still = int(round(a.still * n)) if a.wave else n
        if not a.wave:
            cuts = [0, n]
        else:
            cuts = [0] if j_still == 0 else [0, j_still]
            for p in range(1, a.pieces + 1):
                cuts.append(j_still + int(round((n - j_still) * p / a.pieces)))
        out = []
        paint = a.paint or self.arm_paint
        for pi in range(len(cuts) - 1):
            j0, j1 = cuts[pi], cuts[pi + 1]
            verts, faces, mats, ring_of, js = [], [], [], [], []

            def add_ring(c, f, rr, shrink=1.0):
                d, oo, b = f
                ring_of.append(len(verts))
                for ang, fl in SECTION:
                    t = math.radians(ang)
                    verts.append(c + (oo * (math.cos(t) * fl) + b * math.sin(t)) * rr * shrink)

            if j0 > 0:      # a plug into the piece before, so that no gap opens as it nods
                add_ring(a.pts[j0] - a.fr[j0][0] * a.rad[j0] * 0.55, a.fr[j0], a.rad[j0], 0.72)
                js.append(j0)
            for j in range(j0, j1 + 1):
                add_ring(a.pts[j], a.fr[j], a.rad[j])
                js.append(j)
            if j1 < n:      # and a blunt end inside the piece after
                add_ring(a.pts[j1] + a.fr[j1][0] * a.rad[j1] * 0.4, a.fr[j1], a.rad[j1], 0.7)
                js.append(max(j1 - 1, j0))
            for q in range(len(ring_of) - 1):
                A, B = ring_of[q], ring_of[q + 1]
                for k in range(6):
                    k2 = (k + 1) % 6
                    faces.append((A + k, A + k2, B + k2, B + k))
                    mats.append(self.m(paint(a, js[q], k, (a.w[js[q]] + a.w[min(js[q] + 1, n)]) / 2)))
            end = self.m(paint(a, js[0], 2, a.w[js[0]]))
            faces.append(tuple(reversed(range(ring_of[0], ring_of[0] + 6))))
            mats.append(end)
            faces.append(tuple(range(ring_of[-1], ring_of[-1] + 6)))
            mats.append(self.m(paint(a, js[-1], 2, a.w[js[-1]])))
            parts = [(verts, faces, mats, True)]
            # suckers: a row of small cups down the side that faces its mouth, where that side is seen
            if a.suckers:
                s0, s1 = a.suckers
                cv, cf = [], []
                for j in range(j0, j1):
                    sm = (a.w[j] + a.w[j + 1]) / 2
                    rr = (a.rad[j] + a.rad[j + 1]) / 2
                    if sm < s0 or sm > s1 or rr < 0.009:
                        continue
                    d, oo, b = a.fr[j]
                    c = (a.pts[j] + a.pts[j + 1]) / 2 + oo * rr * 0.76
                    vs, fs, tg = spun([(rr * 0.52, 0.0), (rr * 0.36, rr * 0.3), (0.0, rr * 0.14)], c, oo, n=5, u=b)
                    cf += [tuple(x + len(cv) for x in f) for f, (i_, k_) in zip(fs, tg) if i_ >= 0]
                    cv += vs
                if cv:
                    parts.append((cv, cf, self.m("K"), True))
            out.append((j0, j1, parts))
        return out, (j_still > 0 and a.wave)

    # --- the web, the fins ----------------------------------------------------------------

    def web(self, arms=None, to=None, sag=0.3, top="S", under="U", closed=None):
        """A web between its arms, from the crown out along a share of them (the share that is still)."""
        arms = arms or sorted(self.arms, key=lambda a: math.atan2(a.pts[0].x - self.C.x, -(a.pts[0].y - self.C.y)))
        closed = (len(arms) >= 8) if closed is None else closed
        tv, tf, uf = [], [], []
        for q in range(len(arms) if closed else len(arms) - 1):
            a, b = arms[q], arms[(q + 1) % len(arms)]
            na, nb = len(a.pts) - 1, len(b.pts) - 1
            ja = max(1, int(round((to if to is not None else a.still) * na)))
            jb = max(1, int(round((to if to is not None else b.still) * nb)))
            steps = max(ja, jb)
            rows = []
            for s_ in range(steps + 1):
                pa, pb = a.pts[min(na, int(round(ja * s_ / steps)))], b.pts[min(nb, int(round(jb * s_ / steps)))]
                t = s_ / steps
                row = []
                for c in range(5):
                    x = c / 4.0
                    p = pa.lerp(pb, x)
                    slack = math.sin(math.pi * x) * sag * t * t      # it hangs slack between two arms, most at its hem
                    row.append(p + (self.C - p) * slack * 0.5 - Z * slack * (pa - pb).length * 0.25)
                rows.append(row)
            (v_, f_), (v2, f2) = sheet(rows)
            off = len(tv)
            tv += v_
            tf += [tuple(x + off for x in f) for f in f_]
            uf += [tuple(x + off for x in f) for f in f2]
        self.static.append((tv, tf, self.m(top), True))
        self.static.append((list(tv), uf, self.m(under), True))

    def fins(self, style_, size, still=False):
        """Fins like ears, one either side of the mantle: they beat, slowly."""
        for sg, side in ((-1, "r"), (1, "l")):
            root, rad = self.mantle_point(0.6, 104 * sg)
            out = (rad * 0.95 + self.mantle_axis * 0.45).normalized()
            L = 0.16 * size
            wd = (self.mantle_axis * 0.85 + Vector((0, -0.5, 0))).normalized()
            wd = (wd - out * out.dot(wd)).normalized()
            nrm = out.cross(wd).normalized()
            rim = []
            for k in range(10):
                t = 2 * math.pi * k / 10
                rim.append(root + out * (L * 0.5 + L * 0.62 * math.cos(t)) + wd * (L * 0.46 * math.sin(t) * (1.0 + 0.3 * math.cos(t))))
            mid = root + out * L * 0.5
            verts = rim + [mid + nrm * L * 0.1, mid - nrm * L * 0.1]
            faces = [(k, (k + 1) % 10, 10) for k in range(10)] + [((k + 1) % 10, k, 11) for k in range(10)]
            front = nrm.dot(Vector((0, -1, 0))) > 0
            a_, b_ = ("L", "S") if style_ != "great" else ("L", "D")
            mats = [self.m(a_ if front else b_)] * 10 + [self.m(b_ if front else a_)] * 10
            part = (verts, faces, mats, True)
            if still:
                self.mantle_parts.append(part)
            else:
                self.mover("glide", "fin", [part], root - out * 0.012, side=side, parent="mantle")

    # --- finishing ------------------------------------------------------------------------

    def finish(self):
        """Make the objects, stand the lowest of it on z = 0, and write the model."""
        gl = lines()
        chains = []
        for a in self.arms:
            pcs, has_still = self._arm_parts(a)
            if not a.wave:      # an arm that is still is part of the body, and so is what it holds
                self.static.extend(pcs[0][2])
                for parts in a.extra.values():
                    self.static.extend(parts)
                a.extra = {}
                chains.append((a, []))
                continue
            if has_still:
                self.static.extend(pcs[0][2])
                pcs = pcs[1:]
            chains.append((a, pcs))
        every = list(self.static) + list(self.mantle_parts)
        for a, pcs in chains:
            for j0, j1, parts in pcs:
                every.extend(parts)
            for parts in a.extra.values():
                every.extend(parts)
        for mv in self.movers:
            every.extend(mv[2])
        # leant, then stood on its lowest point
        T = Matrix.Rotation(self.tilt, 4, "X") if self.tilt else Matrix.Identity(4)
        pivot = self.C + Vector((0, 0, 0.1))
        T = Matrix.Translation(pivot) @ T @ Matrix.Translation(-pivot)
        zs, xs, ys = [], [], []
        for p in every:
            if not p or not p[1]:
                continue
            for v in p[0]:
                q = T @ V(v)
                zs.append(q.z)
                xs.append(q.x)
                ys.append(q.y)
        T = Matrix.Translation((0, 0, -min(zs))) @ T
        R3 = T.to_3x3()

        def tf(parts):
            return [([T @ V(v) for v in p[0]],) + tuple(p[1:]) for p in parts if p and p[0] and p[1]]

        objs = [make("body", tf(self.static))]
        mantle = None
        if self.mantle_parts:
            mantle = make("pulse_mantle", tf(self.mantle_parts))
            gl.set_origin(mantle, T @ self.mantle_at)
            objs.append(mantle)
        for a, pcs in chains:
            parent = None
            for q, (j0, j1, parts) in enumerate(pcs):
                extra = a.extra.get(q, []) + (a.extra.get(-1, []) if q == len(pcs) - 1 else [])
                ob = make("wave_arm%d_%d" % (a.i, q), tf(parts + extra))
                d, oo, b = a.fr[j0]
                # it nods about its own X: across the arm, so that it lifts and falls in the plane it curls in
                turned(ob, T @ a.pts[j0], Matrix((R3 @ b, R3 @ d, R3 @ (b.cross(d)))).transposed())
                if parent is not None:
                    gl.child_of(ob, parent)
                parent = ob
                objs.append(ob)
                a.objs.append(ob)
        for kind, what, parts, pivot_, side, n_, par, rot in self.movers:
            assert kind in gl.MOVES, kind
            name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n_ if n_ is not None else "")
            ob = make(name, tf(parts))
            turned(ob, T @ pivot_, (R3 @ rot) if rot is not None else None)
            if par == "mantle" and mantle is not None:
                gl.child_of(ob, mantle)
            elif isinstance(par, Arm) and par.objs:
                gl.child_of(ob, par.objs[-1])
            objs.append(ob)
        # the usual sockets, where a part from elsewhere would hang on an octopus
        hk = self.k_head
        top = self.mantle_top if self.mantle_at is not None else self.head + Vector((0, 0, 0.11 * hk))
        table = {
            "socket_head": top, "socket_eyes": self.head + Vector((0, -0.125 * hk, 0.05 * hk)), "socket_mouth": self.head + Vector((0, -0.125 * hk, -0.02 * hk)),
            "socket_throat": self.head + Vector((0, -0.1 * hk, -0.07 * hk)), "socket_body": self.C + Vector((0, -0.1, -0.02)), "socket_light": self.head + Vector((0, 0, 0.0)),
            "socket_back": self.head + Vector((0, 0.13, 0.06)), "socket_tail": self.C + Vector((0, 0.11, -0.03)), "socket_grip": self.head + Vector((0.16, -0.05, 0.0)),
            "socket_arm_l": self.head + Vector((0.13, 0, -0.02)), "socket_arm_r": self.head + Vector((-0.13, 0, -0.02)),
            "socket_limb_fl": self.C + Vector((0.07, -0.08, -0.06)), "socket_limb_fr": self.C + Vector((-0.07, -0.08, -0.06)), "socket_keepsake": self.C + Vector((0, -0.1, -0.09)),
        }
        table.update(self.sock)
        socks = {name: kit.free_socket(name, T @ V(p)) for name, p in table.items()}
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        ref = max(REF, span / SPREAD)
        path = os.path.join(OUT, self.id + ".glb")
        gl.export_objects(objs, socks, path, ref=ref)
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
        kb = os.path.getsize(path) / 1024.0
        log("%-28s %5d triangles, %2d pieces, %5.1f KB, top %.2f, across %.2f, ref %.2f%s" % (self.id, tris, len(objs), kb, (T @ top).z, span, ref, "   OVER 120" if kb > 120 else ""))


# ======================================================================================
# What it holds, and what it lives in
# ======================================================================================

def p_lamp(at, s=1.0, glow="lamp"):
    """A hand lamp hung by its bail from `at`: the field's colour behind its glass."""
    at = V(at)
    D = -Z
    parts = [band(at - Z * 0.02 * s, 0.02 * s, 0.0045 * s, "brass_key", axis=Y, n=8)]
    o = at - Z * 0.04 * s
    parts.append(turn([(0.008 * s, 0.0), (0.04 * s, 0.022 * s), (0.047 * s, 0.03 * s), (0.03 * s, 0.032 * s)], o, D, "iron_pot", n=8))
    parts.append(turn([(0.03 * s, 0.03 * s), (0.039 * s, 0.062 * s), (0.03 * s, 0.098 * s)], o, D, field(glow, 3.0), n=8))
    parts.append(turn([(0.033 * s, 0.096 * s), (0.043 * s, 0.102 * s), (0.043 * s, 0.114 * s), (0.0, 0.118 * s)], o, D, "iron_pot", n=8))
    return parts


def p_cup(c, s=1.0, lit=False, steam=True):
    """A cup, upright, its waist at c; what is in it; the steam off it (returned apart)."""
    c = V(c)
    parts = [turn([(0.0, -0.046 * s), (0.03 * s, -0.045 * s), (0.036 * s, -0.036 * s), (0.044 * s, 0.0), (0.05 * s, 0.04 * s), (0.044 * s, 0.04 * s), (0.039 * s, 0.022 * s)], c, Z, "bone_dish", n=9)]
    parts.append(turn([(0.041 * s, 0.026 * s), (0.0, 0.028 * s)], c, Z, (field("cup", 2.4) if lit else mat("leather_book_dark")), n=9))
    parts.append(band(c + Vector((0.054 * s, 0, 0.0)), 0.02 * s, 0.006 * s, "bone_dish", axis=Y, n=7))
    wisps = []
    if steam:
        for k, (dx, h) in enumerate(((-0.012, 0.12), (0.014, 0.09))):
            b0 = c + Vector((dx * s, 0.004 * k, 0.05 * s))
            wisps.append(soft(g.tongue([b0, b0 + Vector((0.014 * s, 0, h * 0.4 * s)), b0 + Vector((-0.012 * s, 0, h * 0.75 * s)), b0 + Vector((0.006 * s, 0, h * s))],
                                       [0.014 * s, 0.022 * s, 0.017 * s, 0.003 * s], thick=0.5, normal=Y), "steam_pale"))
    return parts, wisps


def p_coat(a, s0=0.45, s1=0.85, drop=0.2, width=0.16):
    """Somebody's coat, folded once over an arm: it hangs either side of the arm, the collar uppermost."""
    P0, _ = a.at(s0)
    P1, _ = a.at(s1)
    along = (P1 - P0).normalized()
    mid = (P0 + P1) / 2 + Z * (a.r_at((s0 + s1) / 2) + 0.01)
    side = along.cross(Z).normalized()
    half = (P1 - P0).length / 2 + 0.02
    rows = []
    for t in (-1.0, -0.7, -0.38, -0.1, 0.1, 0.38, 0.7, 1.0):
        z = -drop * (abs(t) ** 1.3) * (1.0 if t < 0 else 0.8)
        off = side * (width * 0.5 * t * (0.45 + 0.55 * abs(t)))
        flare = 1.0 + 0.2 * abs(t)
        rows.append([mid + along * (half * flare * u_) + off + Z * (z + 0.008 * math.sin(u_ * 3.0 + t * 4.0)) for u_ in (-1.0, -0.33, 0.33, 1.0)])
    parts = cloth(rows, "cloth_coat", "cloth_coat_light")
    parts.append(rod(mid - along * half * 0.75 + Z * 0.01, mid + along * half * 0.75 + Z * 0.01, 0.017, "cloth_coat_light", n=5))
    return parts


def key_plate(at, d, across, L, material="brass_key", thick=None):
    """A key, flat: its bow at `at`, its shaft along d, its bit to the side `across`."""
    w = 0.05 * L
    pts = []
    for ang in (25, 70, 115, 160, 205, 250, 295, 335):
        t = math.radians(ang)
        pts.append((0.2 * L + 0.2 * L * math.cos(t), 0.2 * L * math.sin(t)))
    pts += [(0.7 * L, -w), (0.7 * L, -w - 0.2 * L), (0.79 * L, -w - 0.2 * L), (0.79 * L, -w - 0.09 * L), (0.88 * L, -w - 0.09 * L), (0.88 * L, -w - 0.2 * L), (0.98 * L, -w - 0.2 * L), (L, w)]
    return plate(pts, at, d, -V(across), thick or 0.07 * L, material)


def key_bit(at, d, across, s, material, teeth=2, thick=0.012):
    """The working end of a key: a flag on the side of a shaft that runs along d through `at`."""
    if teeth == 2:
        pts = [(0, 0), (0.1 * s, 0), (0.1 * s, -0.085 * s), (0.068 * s, -0.085 * s), (0.068 * s, -0.045 * s), (0.036 * s, -0.045 * s), (0.036 * s, -0.085 * s), (0, -0.085 * s)]
    elif teeth == 3:
        pts = [(0, 0), (0.12 * s, 0), (0.12 * s, -0.07 * s), (0.095 * s, -0.07 * s), (0.095 * s, -0.04 * s), (0.07 * s, -0.04 * s), (0.07 * s, -0.09 * s), (0.045 * s, -0.09 * s), (0.045 * s, -0.04 * s),
               (0.02 * s, -0.04 * s), (0.02 * s, -0.075 * s), (0, -0.075 * s)]
    else:
        pts = [(0, 0), (0.09 * s, 0), (0.09 * s, -0.1 * s), (0.05 * s, -0.1 * s), (0.05 * s, -0.06 * s), (0, -0.06 * s)]
    return plate(list(reversed(pts)), at, d, -V(across), thick, material)


def p_keyring(at, s=1.0, n=4):
    """A ring of keys hung from `at`."""
    at = V(at)
    c = at - Z * 0.036 * s
    parts = [band(c, 0.036 * s, 0.0045 * s, "brass_key", axis=Y, n=10)]
    for k in range(n):
        a = math.radians(-40 + 80 * k / max(1, n - 1))
        d = Vector((math.sin(a), 0.2 * (k % 2) - 0.1, -math.cos(a))).normalized()
        parts.append(key_plate(c + d * 0.03 * s, d, Vector((math.cos(a), 0, math.sin(a))), 0.105 * s * (1.0 - 0.14 * (k % 2)), "brass_key" if k % 2 == 0 else "iron_pot_light"))
    return parts


def p_book(c, w=0.36, d=0.26, open_=True, x=X, y=Y, thick=0.03, cover="leather_book", lines_=0, ribbon=None):
    """An open book, its spine along y at c (or shut: a block)."""
    c, x, y = V(c), V(x).normalized(), V(y).normalized()
    up = x.cross(y).normalized()
    parts = []
    if not open_:
        Rm = Matrix((x, y, up)).transposed()
        parts.append(hard(g.box(c, (w, d, thick), rot=Rm), cover))
        parts.append(hard(g.box(c + x * w * 0.03, (w * 0.98, d * 0.92, thick * 0.66), rot=Rm), "paper_page"))
        return parts
    for sg in (1, -1):
        rows = []
        for t in (0.0, 0.5, 1.0):
            rows.append([c + x * (sg * w * 0.52 * t) + y * (d * 0.53 * v_) + up * (-thick * 0.5 + 0.014 * t * t) for v_ in (-1.0, 1.0)])
        parts += cloth(rows if sg < 0 else [list(reversed(r_)) for r_ in rows], cover, cover, smooth=False)
        tops, bases = [], []
        for t in (0.02, 0.22, 0.55, 0.85, 1.0):
            px = sg * w * 0.5 * t
            lift = thick * (0.62 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7 + 0.3)
            bases.append([c + x * px + y * (d * 0.49 * v_) + up * (-thick * 0.5 + 0.004) for v_ in (-1.0, 1.0)])
            tops.append([p + up * lift for p in bases[-1]])
        top, _ = sheet(tops if sg < 0 else [list(reversed(r_)) for r_ in tops], two=False)
        parts.append((top[0], top[1], mat("paper_page"), True))
        ev, ef = [], []
        for e_, outward in ((0, -1), (1, 1)):       # the two ends of the block of pages
            off = len(ev)
            for i in range(len(tops)):
                ev += [tops[i][e_], bases[i][e_]]
            for i in range(len(tops) - 1):
                f = (off + 2 * i, off + 2 * i + 2, off + 2 * i + 3, off + 2 * i + 1)
                ef.append(f if sg == outward else tuple(reversed(f)))
        off = len(ev)                               # and its fore-edge
        ev += [tops[-1][0], tops[-1][1], bases[-1][1], bases[-1][0]]
        f = (off, off + 1, off + 2, off + 3)
        ef.append(f if sg < 0 else tuple(reversed(f)))
        parts.append((ev, ef, mat("paper_edge"), False))
        # lines of writing
        lv, lf = [], []
        for q in range(lines_):
            v0 = 0.36 - 0.72 * q / max(1, lines_ - 1)
            t0, t1 = 0.22, (0.86 if (q + (0 if sg < 0 else 1)) % 3 else 0.62)
            pts = []
            for t in (t0, t1):
                lift = thick * (0.62 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7 + 0.3) - thick * 0.5 + 0.007
                for dv in (0.022, -0.022):
                    pts.append(c + x * (sg * w * 0.5 * t) + y * (d * (v0 + dv)) + up * lift)
            off = len(lv)
            lv += pts
            lf.append((off, off + 1, off + 3, off + 2) if sg > 0 else (off + 2, off + 3, off + 1, off))
        if lv:
            parts.append((lv, lf, mat("ink_wet"), False))
    if ribbon:
        b0 = c - y * d * 0.5 + up * thick * 0.2
        parts += cloth([[b0 + x * 0.012, b0 - x * 0.012], [b0 + x * 0.014 - y * 0.05 - up * 0.02, b0 - x * 0.014 - y * 0.05 - up * 0.02], [b0 + x * 0.004 - y * 0.085 - up * 0.07, b0 - x * 0.02 - y * 0.08 - up * 0.07]], ribbon)
    return parts


def p_splint(a, s0, s1):
    """An arm bound straight: two slats of wood along it and turns of linen round both."""
    P0, f0 = a.at(s0)
    P1, _ = a.at(s1)
    d, oo, b = f0
    L = (P1 - P0).length
    r = a.r_at(s0)
    parts = []
    for sg in (1, -1):
        parts.append(plate([(0, -0.016), (L, -0.012), (L, 0.012), (0, 0.016)], P0 + b * sg * (r + 0.004), d, oo, 0.009, "wood_pale"))
    for q in range(4):
        t = (q + 0.5) / 4
        rr = a.r_at(s0 + (s1 - s0) * t) + 0.012
        parts.append(turn([(rr, -0.016), (rr * 1.04, 0.0), (rr, 0.016)], P0 + d * L * t, d, "cloth_linen", n=7, squash=(1.0, 1.15)))
    return parts


def p_sling(L, B, R, width=0.11):
    """A sling: a band of linen from one side of its neck, under what it carries, to the other."""
    L, B, R = V(L), V(B), V(R)
    ctrl = B * 2 - (L + R) / 2
    rows = []
    for q in range(9):
        t = q / 8
        p = L * (1 - t) ** 2 + ctrl * 2 * t * (1 - t) + R * t * t
        w = width * (0.22 + 0.78 * math.sin(math.pi * t) ** 1.6)
        rows.append([p + Y * (w * 0.5) + Z * 0.0, p - Y * (w * 0.5) - Z * (w * 0.12)])
    return cloth(rows, "cloth_linen", "cloth_linen_dark")


def p_pot(c, s=1.0, lit=True):
    """A cooking pot, round in the belly, carried by its rim; what is in it shows the field's colour."""
    c = V(c)
    prof = [(0.0, -0.115), (0.07, -0.108), (0.118, -0.07), (0.135, -0.02), (0.13, 0.03), (0.116, 0.056), (0.128, 0.066), (0.128, 0.076), (0.108, 0.076), (0.104, 0.05)]
    parts = [turn([(r * s, h * s) for r, h in prof], c, Z, "iron_pot", n=12)]
    parts.append(turn([(0.106 * s, 0.046 * s), (0.0, 0.052 * s)], c, Z, field("soup", 2.2) if lit else mat("leather_book"), n=12))
    for sg in (1, -1):
        parts.append(band(c + Vector((sg * 0.135 * s, 0, 0.045 * s)), 0.022 * s, 0.006 * s, "iron_pot_light", axis=Y, n=6))
    return parts


def p_ladle(grip, d, s=1.0):
    """A ladle, its handle through `grip` along d, its bowl at the far end, open upward."""
    grip, d = V(grip), V(d).normalized()
    end = grip + d * 0.2 * s
    parts = [rod(grip - d * 0.06 * s, end, 0.008 * s, "iron_pot_light", n=4)]
    parts.append(turn([(0.0, -0.036 * s), (0.03 * s, -0.028 * s), (0.043 * s, -0.008 * s), (0.045 * s, 0.004 * s), (0.038 * s, 0.004 * s), (0.0, -0.016 * s)], end + d * 0.03 * s, Z, "iron_pot_light", n=8))
    return parts


def p_bowls(c, n=3, s=1.0):
    """Bowls, one in another, standing at c."""
    c = V(c)
    parts = []
    for q in range(n):
        o = c + Z * (0.017 * q * s)
        if q < n - 1:
            parts.append(turn([(0.03 * s, 0.0), (0.058 * s, 0.022 * s), (0.064 * s, 0.036 * s), (0.058 * s, 0.036 * s)], o, Z, "bone_dish" if q % 2 == 0 else "bone_shell", n=9))
        else:
            parts.append(turn([(0.0, 0.0), (0.03 * s, 0.002), (0.058 * s, 0.022 * s), (0.064 * s, 0.036 * s), (0.057 * s, 0.036 * s), (0.03 * s, 0.012 * s), (0.0, 0.01 * s)], o, Z, "bone_dish", n=9))
    return parts


def p_post(top, h, r=0.06):
    """A mooring post: a timber with an iron band, its foot dark with wet."""
    top = V(top)
    vs, fs, tg = spun([(r * 0.86, -h), (r, -h * 0.92), (r, -h * 0.45), (r, -0.085), (r * 1.1, -0.075), (r * 1.1, -0.04), (r, -0.03), (r * 0.82, 0.0), (0.0, 0.012)], top, Z, n=8)
    mats = [mat("wood_dark") if i <= 1 else (mat("iron_pot_light") if i == 4 else mat("wood_post")) for i, k in tg]
    return [(vs, fs, mats, True)]


def p_hammer(at, d, s=1.0, across=X):
    at, d = V(at), V(d).normalized()
    ac = (V(across) - d * d.dot(V(across))).normalized()
    Rm = Matrix((ac, d.cross(ac), d)).transposed()
    return [rod(at, at + d * 0.14 * s, 0.009 * s, "wood_pale", n=4), hard(g.box(at + d * 0.15 * s, (0.085 * s, 0.034 * s, 0.036 * s), rot=Rm), "iron_pot_light")]


def p_quill(at, d, s=1.0, face=Y):
    """A quill: its nib at `at`, its feather away along d."""
    at, d = V(at), V(d).normalized()
    return [rod(at, at + d * 0.2 * s, 0.0045 * s, "feather_quill", n=3, r1=0.002 * s),
            soft(g.blade(at + d * 0.045 * s, at + d * 0.22 * s, 0.052 * s, thick=0.004 * s, normal=face, belly=0.45), "feather_quill"),
            rod(at - d * 0.012 * s, at + d * 0.012 * s, 0.006 * s, "ink_wet", n=3, r1=0.001)]


def p_needle(at, d, s=1.0, thread="cloth_linen"):
    at, d = V(at), V(d).normalized()
    u, v = frame(d)
    end = at + d * 0.15 * s
    return [rod(at, end, 0.0045 * s, "steel_pin", n=3, r1=0.001),
            wire([at + d * 0.01 * s, at - d * 0.03 * s + u * 0.03 * s, at - d * 0.01 * s + u * 0.07 * s + v * 0.02 * s, at - d * 0.06 * s + u * 0.09 * s], 0.003 * s, thread, n=3)]


def p_spoon(at, d, s=1.0):
    at, d = V(at), V(d).normalized()
    u, v = frame(d)
    return [rod(at, at + d * 0.12 * s, 0.007 * s, "wood_pale", n=4), blob(at + d * 0.15 * s, 1.0, "wood_pale", n=6, m=4, scale=(0.03 * s, 0.012 * s, 0.04 * s), axis=d, u=u)]


def p_brush(at, d, s=1.0):
    at, d = V(at), V(d).normalized()
    return [rod(at, at + d * 0.12 * s, 0.008 * s, "wood_dark", n=4), rod(at + d * 0.12 * s, at + d * 0.14 * s, 0.01 * s, "brass_key", n=4),
            turn([(0.011 * s, 0.0), (0.014 * s, 0.02 * s), (0.0, 0.06 * s)], at + d * 0.14 * s, d, "ink_wet", n=5)]


def p_plate(c, normal, r=0.17, up=Z):
    """A plate, its face to `normal`, mended: the seam is the field's light."""
    c, nz = V(c), V(normal).normalized()
    u, v = frame(nz, up)
    parts = [turn([(0.0, -0.012), (r * 0.5, -0.014), (r * 0.62, -0.006), (r * 0.94, 0.016), (r, 0.022), (r * 0.9, 0.024), (r * 0.6, 0.004), (r * 0.5, -0.002), (0.0, 0.0)], c, nz, "bone_dish", n=12, u=u)]
    seam = [(-0.72, 0.55), (-0.3, 0.2), (-0.36, -0.08), (0.1, -0.2), (0.22, -0.52), (0.6, -0.72)]
    for (x0, y0), (x1, y1) in zip(seam, seam[1:]):
        h0, h1 = (0.012 if abs(x0) + abs(y0) > 0.75 else 0.004), (0.012 if abs(x1) + abs(y1) > 0.75 else 0.004)
        parts.append(rod(c + (u * x0 + v * y0) * r + nz * (h0 + 0.004), c + (u * x1 + v * y1) * r + nz * (h1 + 0.004), 0.008, field("seam", 3.0), n=3))
    return parts


def bottle(c, axis, R, H, rn, hn, n=14, u=None, window=(), glass="glass_bottle", pale="glass_bottle_pale", dark="glass_bottle_dark", hi=None, mouth=True, floor=True):
    """A bottle standing at c along its axis: a body R by H, a shoulder, a neck rn by hn, a lip.
    window: the sides of its body left open, with the far wall seen through them. mouth: open."""
    c, axis = V(c), V(axis).normalized()
    prof = [(R * 0.6, 0.0), (R * 0.95, H * 0.03), (R, H * 0.12), (R, H * 0.45), (R, H * 0.78), (R * 0.9, H * 0.9), (R * 0.6, H), (rn, H * 1.08),
            (rn, H * 1.08 + hn * 0.72), (rn * 1.3, H * 1.08 + hn * 0.78), (rn * 1.3, H * 1.08 + hn), (rn * 0.85, H * 1.08 + hn)]
    vs, fs, tg = spun(prof, c, axis, n=n, u=u)
    keep, mats = [], []
    for f, (i, k) in zip(fs, tg):
        if (k in window and 1 <= i <= 5) or (mouth and i == len(prof)):
            continue
        keep.append(f)
        mats.append(mat(pale) if (hi is not None and k == hi and 2 <= i <= 4) or i in (8, 9) else mat(glass))
    parts = [(vs, keep, mats, True)]
    if window:
        vs, fs, tg = spun([(r * 0.94, h) for r, h in prof[1:8]], c, axis, n=n, u=u)
        parts.append((vs, [tuple(reversed(f)) for f, (i, k) in zip(fs, tg) if 0 <= i < 6 and k not in window], mat(dark), True))
        if floor:
            parts.append(turn([(R * 0.9, H * 0.035), (0.0, H * 0.04)], c, axis, dark, n=n, u=u))
    if mouth:
        parts.append(inside([(rn * 0.85, H * 1.08 + hn * 0.3), (rn * 0.85, H * 1.08 + hn)], c, axis, dark, n=n, u=u))
    return parts, c + axis * (H * 1.08 + hn)


def p_ship(c, L, x=X):
    """A ship for a bottle: a hull, three masts, every sail set, a pennant in its Path's colour."""
    c, x = V(c), V(x).normalized()
    y = Z.cross(x).normalized()
    hull = g.tongue([c - x * L * 0.5 + Z * L * 0.07, c - x * L * 0.33, c + x * L * 0.1, c + x * L * 0.4, c + x * L * 0.52 + Z * L * 0.09], [0.004, L * 0.17, L * 0.2, L * 0.16, L * 0.02], thick=0.9, normal=Z)
    parts = [hard(hull, "wood_dark")]
    for mx, mh in ((-0.26, 0.5), (0.03, 0.64), (0.3, 0.46)):
        b0 = c + x * L * mx + Z * L * 0.04
        parts.append(rod(b0, b0 + Z * L * mh, L * 0.012, "wood_pale", n=3))
        for z0, z1, w in ((0.1, 0.56, 0.26), (0.6, 0.92, 0.18)):
            rows = []
            for t in (0.0, 0.5, 1.0):
                z = b0.z + L * mh * (z0 + (z1 - z0) * t)
                ww = L * w * (1.0 - 0.25 * t)
                bow = L * 0.05 * math.sin(math.pi * t)
                rows.append([Vector((0, 0, z)) + Vector((b0.x, b0.y, 0)) + x * (-ww * 0.5) - y * bow * 0.6, Vector((0, 0, z)) + Vector((b0.x, b0.y, 0)) - y * (bow + L * 0.02),
                             Vector((0, 0, z)) + Vector((b0.x, b0.y, 0)) + x * (ww * 0.5) - y * bow * 0.6])
            parts += cloth(rows, "cloth_sail", "paper_edge")
    top = c + x * L * 0.03 + Z * L * 0.68
    parts += cloth([[top, top + Z * L * 0.07], [top - x * L * 0.14 + Z * L * 0.035, top - x * L * 0.14 + Z * L * 0.04]], "accent", "accent_dark")
    return parts


def p_paper(c, x, y, w, h, curl=0.02):
    """A sheet of paper, lying in the plane of x and y, one corner lifting."""
    c, x, y = V(c), V(x).normalized(), V(y).normalized()
    up = x.cross(y).normalized()
    rows = []
    for v_ in (-0.5, 0.0, 0.5):
        rows.append([c + x * (w * u_) + y * (h * v_) + up * (curl * max(0.0, u_ + v_) ** 2 * 4.0) for u_ in (-0.5, 0.0, 0.5)])
    return cloth(rows, "paper_page", "paper_edge", smooth=False)


def p_shell(c, axis, r, deep=0.3):
    """Half of a great shell: ribbed outside, pale within; its hollow looks along `axis`."""
    c, axis = V(c), V(axis).normalized()
    prof = [(0.0, -deep * r), (0.42 * r, -deep * 0.86 * r), (0.76 * r, -deep * 0.5 * r), (r, 0.0)]
    vs, fs, tg = spun(prof, c, axis, n=12)
    parts = [(vs, fs[:-1], [mat("bone_shell_dark") if k % 2 else mat("bone_shell") for i, k in tg[:-1]], True)]
    parts.append(inside([(0.0, -deep * r + 0.012), (0.42 * r, -deep * 0.86 * r + 0.012), (0.76 * r, -deep * 0.5 * r + 0.01), (r * 0.99, 0.0)], c, axis, "bone_dish", n=12))
    return parts


def p_helm(c, s=1.0, back=0.2):
    """An old kettle-hat: a dome, a brim, a ridge over the crown, a dent. Pushed back a little, so that a face shows under it."""
    c = V(c)
    axis = Vector((0, math.sin(back), math.cos(back)))
    u = Vector((0, -1, 0))
    prof = [(0.235, -0.03), (0.225, -0.012), (0.148, 0.0), (0.142, 0.035), (0.13, 0.095), (0.098, 0.145), (0.05, 0.172), (0.0, 0.18)]
    vs, fs, tg = spun([(r * s, h * s) for r, h in prof], c, axis, n=14, u=u)
    mats = []
    for i, k in tg:
        dent = (i in (3, 4) and k in (11, 12)) or (i == 4 and k == 10)
        mats.append(mat("iron_helm_dark") if dent or i == 1 else mat("iron_helm"))
    # the dent itself: those points pushed in
    uu, vv = frame(axis, u)
    for q, p in enumerate(vs):
        ring, k = q // 14, q % 14
        if ring in (4, 5) and k in (11, 12) and q < 14 * 7:
            vs[q] = p - (p - c - axis * (p - c).dot(axis)).normalized() * 0.022 * s
    parts = [(vs, fs[:-1], mats[:-1], True)]
    parts.append(inside([(r * s * 0.97, h * s - 0.004) for r, h in prof[:5]], c, axis, "iron_helm_dark", n=14, u=u))
    ridge = [c + axis * (0.02 * s) + uu * 0.146 * s, c + axis * (0.1 * s) + uu * 0.132 * s, c + axis * (0.165 * s) + uu * 0.08 * s, c + axis * 0.19 * s, c + axis * (0.165 * s) - uu * 0.08 * s,
             c + axis * (0.1 * s) - uu * 0.132 * s, c + axis * (0.02 * s) - uu * 0.146 * s]
    parts.append(hard(g.tube(ridge, [0.012 * s] * 7, n=4), "iron_helm_dark"))
    return parts, axis


def cloud(c, r, seed=0.0, n=5, mats=("ink_cloud", "ink_cloud_edge"), squash=0.8, spread=1.0):
    """A cloud: round lobes about a middle (ink on the air, weather in a glass)."""
    c = V(c)
    parts = [blob(c, r, mats[0], n=8, m=5, scale=(1.0, 0.9, squash))]
    for k in range(n):
        a = seed + k * 2.399
        rr = r * (0.5 + 0.22 * math.sin(seed * 3.1 + k * 1.7))
        p = c + Vector((math.cos(a) * r * 0.82 * spread, math.sin(a * 1.3) * r * 0.35, math.sin(a) * r * 0.62 * squash * spread))
        parts.append(blob(p, rr, mats[(k + 1) % len(mats)], n=7, m=4, scale=(1.0, 0.9, squash)))
    return parts


def p_stone(c, r, material, seed=0.0, flat=0.7):
    a = seed * 2.1
    return blob(c, r, material, n=6, m=4, scale=(1.0 + 0.15 * math.sin(a), 0.85, flat), u=Vector((math.cos(a), math.sin(a), 0)))


def p_sprig(base, h=0.11):
    """A small green thing, growing."""
    base = V(base)
    parts = [wire([base, base + Vector((0.006, 0, h * 0.5)), base + Vector((-0.004, 0.004, h))], 0.006, "leaf_sprig_dark", n=4, r1=0.003)]
    for sg, z, L in ((1, 0.55, 0.075), (-1, 0.8, 0.06), (1, 1.0, 0.045)):
        b0 = base + Vector((0, 0, h * z))
        parts.append(soft(g.blade(b0, b0 + Vector((sg * L, -0.01, L * 0.55)), L * 0.62, normal=Vector((0, -1, 0.5)), belly=0.45, thick=0.004), "leaf_sprig"))
    return parts


# ======================================================================================
# The poses: one a form. Its face is kept clear: an arm that is raised goes up from the side.
# ======================================================================================

POSES = {}


def pose(name):
    def deco(fn):
        POSES[name] = fn
        return fn
    return deco


@pose("inkling")
def _inkling(O):
    """The Starter: a thumb of an octopus, nearly clear, all eyes; its arms in tight curls, one raised and crooked like a question."""
    O.body()
    # its heart: the field, seen through it
    hp, rad = O.mantle_point(0.42, -30, 0.96)
    O.mantle_parts.append(blob(hp, 0.05, field("heart", 2.2), n=7, m=4, scale=(1.0, 1.0, 1.25), axis=rad))
    O.arm(2, 124, [(0.45, 25, -10), (0.55, -265, 0)], L=1.15, n=12, suckers=(0.5, 0.95))        # the question
    O.arm(0, 62, [(0.4, -25, 12), (0.6, 280, 10)], L=1.0, n=11, suckers=(0.5, 1.0))
    O.arm(1, 70, [(0.45, -15, -16), (0.55, 260, -10)], L=0.95, n=11, suckers=(0.5, 1.0))
    O.arm(3, 96, [(0.4, -30, 0), (0.6, 300, 12)], L=0.95, n=11)
    O.arm(4, 50, [(0.4, -10, 10), (0.6, 280, 0)], L=0.9, n=10, pieces=1)
    O.arm(5, 58, [(0.4, -10, 10), (0.6, 270, 0)], L=0.9, n=10, pieces=1)
    O.pair(3, 40, [(0.5, 20, 0), (0.5, 240, 0)], L=0.85, n=8, pieces=1)


# --- Many-hands: the round octopus, marigold, with every arm full ------------------------

@pose("many-hands")
def _many_hands(O):
    """Round, mottled, every arm full: a lamp, a cup, somebody's coat; and one arm empty, held a little toward you."""
    O.lid_slant = 1.0
    O.body()
    lamp = O.arm(3, 110, [(0.2, 0, 0), (0.3, 40, -8), (0.2, 25, 0), (0.3, 215, 0)], L=1.3, n=12, suckers=(0.68, 1.0))
    hook = lamp.centre(0.2) - Z * 0.02
    O.mover("sway", "lamp", p_lamp(hook, 1.0), hook, parent=lamp)
    cup = O.arm(2, 96, [(0.5, 22, -8), (0.1, -44, 0), (0.4, 0, -335)], L=1.15, n=13)
    parts, wisps = p_cup(cup.centre(0.4) + Z * 0.012, 0.95)
    O.hold(cup, parts + wisps)
    O.arm(0, 80, [(0.5, 12, 26), (0.28, 30, 0), (0.22, 80, 0)], L=1.05, n=12, suckers=(0.3, 1.0), pieces=3, still=0.2)     # the empty one
    coat = O.arm(1, 84, [(0.5, 12, 30), (0.5, 40, 10)], L=1.0, n=10, pieces=1, still=0.4)
    O.hold(coat, p_coat(coat, 0.46, 0.9, drop=0.2))
    O.arm(4, 62, [(0.45, -30, 0), (0.55, 250, 10)], L=0.9, n=9, pieces=1)
    O.arm(5, 58, [(0.5, -20, 0), (0.5, 230, -10)], L=0.9, n=9, pieces=1)
    O.pair(3, 34, [(0.5, 10, 0), (0.5, 200, 0)], L=0.85, n=7, pieces=1)


@pose("cup-bearer")
def _cup_bearer(O):
    """One arm straight up with a steaming cup, level and still, whatever the other seven are doing."""
    O.lid_slant = 1.0
    O.body()
    cup = O.arm(2, 104, [(0.15, 0, 0), (0.13, 74, 0), (0.33, 4, 0), (0.07, -86, 0), (0.32, 0, -338)], L=1.7, n=16, wave=False, suckers=(0.3, 0.6))
    c = cup.centre(0.3) + Z * 0.014
    parts, wisps = p_cup(c, 0.95, lit=True)
    O.static.extend(parts)
    O.mover("sway", "steam", wisps, c + Z * 0.05)
    O.arm(0, 58, [(0.4, -20, 24), (0.6, 250, 0)], L=1.0, n=11, suckers=(0.5, 1.0))
    O.arm(1, 76, [(0.5, 24, 20), (0.5, -210, -30)], L=1.05, n=11)
    O.arm(3, 102, [(0.5, 34, 20), (0.5, 230, 0)], L=1.1, n=11, suckers=(0.5, 1.0))
    O.arm(4, 44, [(0.5, -30, 0), (0.5, 200, 20)], L=1.0, n=9, pieces=1)
    O.arm(5, 64, [(0.45, -20, -10), (0.55, 260, 0)], L=0.95, n=10)
    O.arm(6, 24, [(0.6, 16, 0), (0.4, 160, 0)], L=0.95, n=8, pieces=1)
    O.arm(7, 36, [(0.5, -10, 0), (0.5, 210, 0)], L=0.9, n=8, pieces=1)


@pose("splints")
def _splints(O):
    """It stands on two arms bound straight as splints; a third hangs in a sling it tied itself."""
    O.lid_slant = 1.0
    O.body()
    for i in (4, 5):
        leg = O.arm(i, 11, [(1, 0, 0)], L=1.75, n=4, wave=False, r=0.95, tipr=0.014)
        O.static.extend(p_splint(leg, 0.14, 0.95))
    C = O.C
    hurt = O.arm_pts(0, [C + Vector((-0.1, -0.15, -0.035)), C + Vector((-0.02, -0.21, -0.085)), C + Vector((0.075, -0.2, -0.07)), C + Vector((0.11, -0.16, -0.03))], wave=False, n=9)
    O.static.extend(p_sling(O.head + Vector((0.1, 0.03, 0.045)), C + Vector((0.0, -0.215, -0.125)), O.head + Vector((-0.1, 0.03, 0.045))))
    O.static.append(blob(O.head + Vector((0.1, 0.035, 0.05)), 0.02, "cloth_linen", n=6, m=4))
    roll = O.arm(3, 112, [(0.5, 30, 10), (0.1, -40, 0), (0.4, 0, 330)], L=1.0, n=12)
    rc = roll.centre(0.4)
    O.hold(roll, [turn([(0.012, -0.035), (0.033, -0.035), (0.033, 0.035), (0.012, 0.035)], rc, Z, "cloth_linen", n=8)] + cloth([[rc + Vector((0.033, 0, 0.03)), rc + Vector((0.033, 0, -0.03))],
                 [rc + Vector((0.05, 0.01, 0.025 - 0.07)), rc + Vector((0.05, 0.01, -0.035 - 0.07))], [rc + Vector((0.04, 0.0, 0.02 - 0.15)), rc + Vector((0.045, 0.0, -0.04 - 0.15))]], "cloth_linen", "cloth_linen_dark"))
    O.arm(2, 70, [(0.4, -20, 20), (0.6, 240, 0)], L=0.95, n=10, suckers=(0.5, 1.0))
    O.arm(1, 60, [(0.45, -20, -10), (0.55, 230, -10)], L=0.85, n=9, pieces=1)
    O.pair(3, 30, [(0.5, 10, 0), (0.5, 190, 0)], L=0.8, n=8, pieces=1)


@pose("last-served")
def _last_served(O):
    """A pot carried by its rim against its own skin, a ladle up in one arm, bowls stacked down three more."""
    O.lid_slant = 1.0
    O.body()
    C = O.C
    pc = C + Vector((0.0, -0.235, -0.15))
    O.static.extend(p_pot(pc, 1.0))
    for i, sx in ((0, -1), (1, 1)):
        rim = pc + Vector((sx * 0.118, 0.03, 0.078))
        O.arm_pts(i, [C + Vector((sx * 0.13, -0.11, -0.01)), rim + Vector((sx * 0.03, 0.0, 0.03)), rim + Vector((-sx * 0.012, -0.02, 0.012)), rim + Vector((-sx * 0.03, -0.035, -0.04))], wave=False, n=9, toward=pc)
    lad = O.arm(2, 112, [(0.2, 0, 0), (0.32, 44, -10), (0.1, -40, 0), (0.38, 0, -330)], L=1.3, n=13)
    O.hold(lad, p_ladle(lad.centre(0.36) - Z * 0.03, Vector((-0.25, -0.1, 0.96)), 1.05))
    for i, (out, n_b, L) in ((3, (104, 3, 1.2)), (5, (86, 2, 1.1)), (7, (70, 1, 1.0))):
        tray = O.arm(i, out, [(0.5, 28, 6), (0.1, -40, 0), (0.4, 0, 330)], L=L, n=11, pieces=1, still=0.35)
        O.hold(tray, p_bowls(tray.centre(0.38) + Z * 0.02, n_b))
    O.arm(4, 52, [(0.45, -30, 0), (0.55, 240, 10)], L=0.9, n=9, suckers=(0.6, 1.0))
    O.arm(6, 30, [(0.5, 10, 0), (0.5, 200, 0)], L=0.85, n=8, pieces=1)


@pose("outstretched")
def _outstretched(O):
    """Gone pale so that it can be found, an arm stretched out to each side, feeling for a shoulder; the rest let down together."""
    O.body()
    for i in (2, 3):
        O.arm(i, 94, [(0.7, 5, 8), (0.3, 35, -40)], L=1.5, n=10, still=0.22, pieces=2, suckers=(0.55, 0.9), lit=(0.9, 1.01), tipr=0.012)
    for i, out in ((0, 16), (1, 13), (4, 15), (5, 12), (6, 13), (7, 16)):
        O.arm(i, out, [(0.65, 10, 0), (0.35, -70, 0)], L=1.25, n=8, pieces=1, still=0.35)


@pose("lifeline")
def _lifeline(O):
    """Its arms knotted to one another into one long line, a loop left open at each end for a hand."""
    O.body()
    for sg, i in ((-1, 2), (1, 3)):
        rise = 18 if sg < 0 else -22
        rope = O.arm(i, 92 + rise, [(0.24, 0, 0), (0.36, -rise * 1.2, 0), (0.4, -345, 0)], L=2.25, r=1.25, n=17, still=0.44, pieces=2, knots=(0.25, 0.43), tipr=0.016,
                     swell=((0.25, 0.03, 0.75), (0.43, 0.028, 0.65)), suckers=None)
        k1, _ = rope.at(0.25)
        k2, _ = rope.at(0.43)
        for j in (i - 2, i + 2):
            p0, dr = O.root(j)
            O.arm_pts(j, [p0 + dr * 0.07 + Vector((sg * 0.05, 0, 0.0)), (p0 + k1) / 2 + Vector((0, 0, -0.02)), k1], wave=False, n=6, tipr=0.02)
        p0, dr = O.root(i + 4)
        O.arm_pts(i + 4, [p0 + dr * 0.06 + Vector((sg * 0.08, 0.02, -0.01)), k1 + Vector((0, 0.05, -0.04)), k2], wave=False, n=7, tipr=0.02)


@pose("holdfast")
def _holdfast(O):
    """Wound about a mooring post, and one arm far longer than the rest, ringed with old grip-marks: the one it offers."""
    O.lid_slant = 1.0
    O.body()
    C = O.C
    top = C + Vector((0, 0.03, -0.04))
    O.static.extend(p_post(top, 0.62, 0.062))
    ax = lambda p: Vector((top.x - p.x, top.y - p.y, 0))
    for i, (sweep, drop) in ((0, (300, 0.36)), (3, (-250, 0.46)), (4, (210, 0.2)), (5, (-230, 0.3)), (6, (170, 0.12)), (7, (-150, 0.54))):
        a0 = -AZ[i]
        pts = helix(top + Vector((0, 0, -0.05)), -Z, 0.095, a0 + (30 if sweep > 0 else -30), sweep, drop, n=8, u=Vector((0, -1, 0)), r1=0.075)
        O.arm_pts(i, pts, toward=ax, wave=False, n=12, tipr=0.01)
    O.arm(2, 94, [(0.3, 6, -24), (0.4, 20, 12), (0.3, -34, 0)], L=2.3, r=1.15, n=16, still=0.2, pieces=3, suckers=(0.5, 1.0), tipr=0.014)
    O.arm(1, 70, [(0.5, 10, 20), (0.5, 230, 0)], L=0.95, n=10)


@pose("upraised")
def _upraised(O):
    """Four arms lifted, a ring of light turning over each; its eyes on none of them."""
    O.lid_slant = -0.6
    O.body()
    for q, (i, up, sd) in enumerate(((2, 56, -10), (3, 56, -10), (4, 76, 14), (5, 76, 14))):
        a = O.arm(i, 100, [(0.16, 0, 0), (0.2, up, 0), (0.44, 14, sd), (0.2, -30, 0)], L=1.4 if i < 4 else 1.25, n=12, suckers=(0.45, 0.9))
        c = a.tip + a.dir * 0.02 + Z * 0.03
        tiltv = (Z + Vector((0.3 * (1 if q % 2 else -1), 0.2, 0))).normalized()
        O.mover("spin", "ring", [band(c, 0.066, 0.009, field("ring", 3.0), axis=tiltv, n=12)], c, side="r" if q % 2 else "", n=q, parent=a)
    O.arm(0, 52, [(0.45, -20, 20), (0.55, 240, 0)], L=0.95, n=10, suckers=(0.55, 1.0))
    O.arm(1, 60, [(0.45, -16, 16), (0.55, 230, 0)], L=0.95, n=10)
    O.pair(3, 30, [(0.5, 10, 0), (0.5, 190, 0)], L=0.85, n=8, pieces=1)


@pose("wheel")
def _wheel(O):
    """Every arm a spoke with a different tool at its end, and each at its own work."""
    O.lean = 62
    O.body()
    C = O.C
    hub = O.head + Vector((0, 0.03, -0.03))
    tools = (p_hammer, p_quill, p_needle, p_spoon, None, None, p_brush, None)
    order = (3, 5, 4, 2, 0, 6, 7, 1)
    for q, i in enumerate(order):
        th = math.radians(22.5 + 45 * q)
        d = Vector((math.cos(th), 0.0, math.sin(th)))
        p0, dr = O.root(i)
        a = O.arm_pts(i, [p0 + dr * 0.07, hub + d * 0.2 + Vector((0, 0.03 if d.z > 0.3 else -0.03, 0)), hub + d * 0.36, hub + d * 0.47 * O.k_arm], n=9, pieces=1, still=0.4, suckers=(0.45, 0.85) if d.z < 0.3 else None,
                      tipr=0.012, o0=Vector((0, 1, 0)))
        at = a.tip - a.dir * 0.02
        if q == 4:
            O.hold(a, [key_plate(at, a.dir, Z.cross(a.dir), 0.2)])
        elif q == 5:
            O.hold(a, p_book(at + a.dir * 0.07, 0.11, 0.15, open_=False, x=a.dir, y=Y.cross(a.dir), thick=0.035))
        elif q == 7:
            O.mover("sway", "lamp", p_lamp(at + a.dir * 0.02, 0.8), at + a.dir * 0.02, parent=a)
        else:
            O.hold(a, tools[q](at, a.dir, 1.25))


@pose("mended-plate")
def _mended_plate(O):
    """One arm does nothing but hold up a mended plate, its seam bright; the other seven are shut like fists."""
    O.body()
    C = O.C
    hold = O.arm(4, 104, [(0.14, 0, 0), (0.14, 76, 0), (0.5, 8, -16), (0.22, 50, 0)], L=1.95, n=12, wave=False, suckers=(0.3, 0.8))
    pc = hold.tip + Vector((0.03, -0.06, 0.03))
    O.static.extend(p_plate(pc, Vector((-0.42, -0.62, 0.66)), 0.18))
    for i, out, L in ((0, 66, 0.86), (1, 72, 0.84), (2, 96, 0.9), (3, 98, 0.9), (5, 78, 0.84), (6, 50, 0.8), (7, 54, 0.8)):
        O.arm(i, out, [(0.34, -10, 0), (0.66, -440, 0)], L=L, n=11, pieces=1, still=0.3)


# --- Latch-lifter: the long-armed one, peacock, banded -----------------------------------

@pose("latch-lifter")
def _latch_lifter(O):
    """Long, narrow, banded; arms as fine as wire at the tips, feeling along an edge; a ring of keys on one."""
    O.lid_slant = -1.0
    O.body()
    ring = O.arm(3, 112, [(0.18, 0, 0), (0.3, 50, 0), (0.22, 10, 0), (0.3, 205, 0)], L=1.0, n=13, tipr=0.004)
    hook = ring.centre(0.22) - Z * 0.022
    O.mover("sway", "keys", p_keyring(hook, 1.15), hook, parent=ring)
    O.arm(0, 70, [(0.4, 30, 10), (0.35, -75, 0), (0.25, 170, 0)], L=1.0, n=13, tipr=0.003, pieces=3, still=0.2, suckers=(0.2, 0.6))
    O.arm(1, 58, [(0.35, 36, 14), (0.4, -70, 10), (0.25, 150, 0)], L=1.05, n=13, tipr=0.003)
    O.arm(2, 50, [(0.3, 45, 0), (0.4, -70, 14), (0.3, 130, 0)], L=1.05, n=12, tipr=0.003)
    O.arm(4, 30, [(0.4, 25, 0), (0.3, -45, 0), (0.3, 100, 20)], L=1.0, n=10, tipr=0.003)
    O.arm(5, 26, [(0.4, 20, 0), (0.3, -40, 0), (0.3, 95, -20)], L=0.95, n=10, tipr=0.003)
    O.pair(3, 14, [(0.6, 12, 0), (0.4, 80, 0)], L=0.95, n=8, pieces=1, tipr=0.003)


@pose("bottled")
def _bottled(O):
    """It lives in a bottle a third its size: one eye at the neck, its arms folded in like letters, two tips out over the lip."""
    lean = Vector((-0.2, -0.55, 0.81)).normalized()
    base = Vector((0, 0.1, 0.0))
    R, H, rn, hn = 0.17, 0.33, 0.07, 0.13
    win = (11, 12, 13, 0, 1)
    u = Vector((0, -1, 0))
    parts, top = bottle(base, lean, R, H, rn, hn, n=14, u=u, window=win, hi=3)
    O.static.extend(parts)
    uu, vv = frame(lean, u)
    # itself, inside: the mantle fills the belly of the bottle and breathes there
    mc = base + lean * H * 0.36
    O.mantle_at, O.mantle_top = mc, top
    vs, fs, tg = ball(mc, 1.0, n=10, m=6, scale=(R * 0.8, R * 0.8, H * 0.33), axis=lean, u=u)
    O.mantle_parts.append((vs, fs, [O.m("L") if (i in (2, 3) and k % 3 == 0) else O.m("S") for i, k in tg], True))
    # arms folded flat against the glass, like letters
    for q, (ang, z) in enumerate(((-55, 0.2), (15, 0.16), (-20, 0.66), (40, 0.6))):
        a = math.radians(ang)
        c = base + lean * (H * z) + (uu * math.cos(a) + vv * math.sin(a)) * R * 0.72
        nrm = (uu * math.cos(a) + vv * math.sin(a))
        pts = helix(c, nrm, 0.012, 40 * q, 560, 0.012, n=14, u=lean, r1=0.058)
        O.arm_pts(q + 4, list(reversed(pts)), root=False, wave=False, n=13, r=0.62, tipr=0.006, toward=c + nrm * 0.3, suckers=(0.3, 0.9))
    # its eye, at the neck
    O.head, O.k_head = top - lean * 0.06, 1.0
    E = top - lean * 0.012
    O.static.append(turn([(rn * 0.84, -0.09), (rn * 0.84, -0.02), (rn * 0.6, 0.0)], E, lean, O.m("H"), n=10, u=u))
    O.eye(E, lean, 0.047, "bar", "r", -1, up=-u, brow=False, lid=0.16)
    # and two arms out over the lip, feeling about
    for i, (ang, out_) in ((0, (-80, 1)), (1, (130, -1))):
        a = math.radians(ang)
        rad = uu * math.cos(a) + vv * math.sin(a)
        p0 = top - lean * 0.07 + rad * rn * 0.5
        lip = top + rad * rn * 1.0
        if i == 0:
            pts = [p0, lip + lean * 0.03, lip + rad * 0.06 + lean * 0.0, lip + rad * 0.09 - lean * 0.07, lip + rad * 0.06 - lean * 0.14, lip + rad * 0.1 - lean * 0.19]
        else:
            pts = [p0, lip + lean * 0.05, lip + rad * 0.05 + lean * 0.13, lip + rad * 0.12 + lean * 0.17, lip + rad * 0.17 + lean * 0.13, lip + rad * 0.15 + lean * 0.08]
        O.arm_pts(i, pts, root=False, n=11, r=0.58, still=0.25, pieces=2, tipr=0.004, o0=-rad, suckers=(0.3, 0.8))
    O.sock = {"socket_head": top, "socket_eyes": E + lean * 0.03, "socket_back": base + lean * H * 0.5 - u * R, "socket_light": mc}
    O.C = base + lean * H * 0.5


@pose("bottle-post")
def _bottle_post(O):
    """A corked bottle with a rolled paper in it rides high in one arm; another arm is always writing the next."""
    O.lid_slant = -1.0
    O.body()
    C = O.C
    up = O.arm(2, 106, [(0.16, 0, 0), (0.2, 62, 0), (0.34, 12, -8), (0.3, -230, 0)], L=1.35, n=13, tipr=0.005, suckers=(0.4, 0.75))
    bc = up.centre(0.24)
    ax = Vector((-0.35, -0.15, 0.92)).normalized()
    parts, top = bottle(bc - ax * 0.1, ax, 0.05, 0.13, 0.021, 0.045, n=9, window=(7, 8, 0), glass="glass_clear", pale="glass_flesh", dark="glass_clear_dark", mouth=False, floor=False)
    parts.append(turn([(0.02, -0.01), (0.024, 0.02), (0.0, 0.024)], top, ax, "wax_cork", n=7))
    parts.append(turn([(0.022, 0.0), (0.022, 0.1), (0.0, 0.102)], bc - ax * 0.085, ax, "paper_page", n=7))
    parts.append(band(bc - ax * 0.03, 0.024, 0.005, "accent", axis=ax, n=7))
    O.hold(up, parts)
    sheet_c = C + Vector((-0.12, -0.27, -0.07))
    tray = O.arm_pts(0, [C + Vector((-0.1, -0.14, -0.03)), sheet_c + Vector((0.0, 0.05, -0.02)), sheet_c + Vector((0.01, -0.06, -0.018)), sheet_c + Vector((0.06, -0.1, -0.012))], wave=False, n=9, tipr=0.004)
    O.static.extend(p_paper(sheet_c, Vector((1, 0.1, 0.0)), Vector((-0.1, 1, 0.25)), 0.2, 0.15))
    nib = sheet_c + Vector((0.03, 0.0, 0.006))
    pen = O.arm_pts(1, [C + Vector((0.1, -0.15, 0.0)), nib + Vector((0.13, 0.0, 0.1)), nib + Vector((0.07, 0.02, 0.13)), nib + Vector((0.035, 0.02, 0.085))], n=10, still=0.4, pieces=1, tipr=0.005)
    O.hold(pen, p_quill(nib, Vector((0.3, 0.2, 0.93)), 1.15, face=Vector((0.2, -1, 0))))
    O.arm(3, 44, [(0.3, 40, 0), (0.4, -70, -10), (0.3, 130, 0)], L=1.0, n=11, tipr=0.003)
    O.arm(4, 30, [(0.4, 25, 0), (0.3, -45, 0), (0.3, 100, 20)], L=0.95, n=9, tipr=0.003)
    O.arm(5, 24, [(0.4, 20, 0), (0.3, -40, 0), (0.3, 95, -20)], L=1.0, n=9, tipr=0.003)
    O.pair(3, 13, [(0.6, 12, 0), (0.4, 80, 0)], L=0.9, n=7, pieces=1, tipr=0.003)


@pose("ship-bearer")
def _ship_bearer(O):
    """A great bottle on its back with a ship in it, every sail set; its own mantle is the sea the ship rides."""
    O.lid_slant = -1.0
    O.body(mantle=False)
    C = O.C
    ax = Vector((-1, 0.0, 0.1)).normalized()
    R, H, rn, hn = 0.2, 0.46, 0.07, 0.15
    bc = O.head + Vector((0.24, 0.1, 0.3))
    u = Vector((0, -1, 0.0))
    parts, top = bottle(bc, ax, R, H, rn, hn, n=14, u=u, window=(13, 0, 1, 2, 3), hi=5, mouth=False)
    parts.append(turn([(rn * 0.8, -0.01), (rn * 0.95, 0.03), (0.0, 0.036)], top, ax, "wax_cork", n=8))
    O.static.extend(parts)
    mid = bc + ax * H * 0.5
    # the sea in the bottle: its own mantle, which breathes
    O.mantle_at = mid - Z * R * 0.55
    O.mantle_top = mid + Z * R
    vs, fs, tg = ball(mid - Z * R * 0.62, 1.0, n=10, m=4, scale=(H * 0.4, R * 0.74, R * 0.3), axis=Z, u=ax)
    O.mantle_parts.append((vs, fs, [O.m("P") if (i >= 2 and k % 3 == 0) else O.m("S") for i, k in tg], True))
    O.static.extend(p_ship(mid - Z * R * 0.42 + ax * 0.02, 0.3, x=-ax))
    # a neck of its own skin up into the bottle, and four arms that carry it
    O.static.append(turn([(0.085, -0.02), (0.07, 0.07), (0.06, 0.16)], O.head + Vector((0, 0.03, 0.06)), Vector((0, 0.12, 1)), O.m("S"), n=9))
    under = lambda p: Vector((0, mid.y - p.y, mid.z - p.z))
    for i, (x_, a0, sweep) in ((2, (-0.2, 72, -66)), (3, (0.2, 76, -70)), (4, (-0.07, 106, 66)), (5, (0.1, 104, 70))):
        c = Vector((mid.x + x_, mid.y, mid.z))
        pts = helix(c, X, R + 0.03, a0, sweep, 0.03 * (1 if x_ > 0 else -1), n=5, u=Vector((0, -1, 0)))
        p0, dr = O.root(i)
        O.arm_pts(i, [p0 + dr * 0.1 + Vector((0, 0.03, 0.02))] + pts, wave=False, n=10, tipr=0.004, toward=under)
    O.arm(0, 60, [(0.35, 36, 14), (0.4, -70, 10), (0.25, 150, 0)], L=0.95, n=12, tipr=0.003, suckers=(0.2, 0.6))
    O.arm(1, 46, [(0.3, 45, 0), (0.4, -70, 14), (0.3, 130, 0)], L=1.0, n=12, tipr=0.003)
    O.pair(3, 16, [(0.5, 16, 0), (0.5, 90, 10)], L=0.95, n=8, pieces=1, tipr=0.003)
    O.sock = {"socket_head": mid + Z * R, "socket_back": mid + Vector((0, R, 0))}


@pose("key-fan")
def _key_fan(O):
    """Each arm ends in a different key, grown that way, and it holds five of them fanned like a hand of cards."""
    O.lid_slant = -1.0
    O.body()
    C = O.C
    hub = O.head + Vector((-0.1, 0.05, 0.0))
    keys = ((2, "brass_key"), (3, "accent_pale"), (1, "brass_key"), (2, "iron_pot_light"), (3, "brass_key"))
    for q, i in enumerate((0, 2, 4, 6, 7)):
        th = math.radians(168 - 21 * q)
        d = Vector((math.cos(th), -0.1 + 0.05 * q, math.sin(th))).normalized()
        p0, dr = O.root(i)
        L = (0.46 + 0.05 * math.sin(q * 1.9)) * O.k_arm / 1.3
        a = O.arm_pts(i, [p0 + dr * 0.08 + Vector((-0.02, 0.02, 0.0)), hub + d * 0.16, hub + d * (0.16 + L * 0.5), hub + d * (0.16 + L)], n=9, pieces=1, still=0.35, tipr=0.011, r=0.9, o0=Vector((0, 1, 0)))
        tip, dd = a.tip, a.dir
        side = dd.cross(Y).normalized()
        teeth, m_ = keys[q]
        O.hold(a, [rod(tip - dd * 0.01, tip + dd * 0.2, 0.011, m_, n=5), key_bit(tip + dd * 0.09, dd, side, 1.15, m_, teeth),
                   band(tip + dd * 0.01, 0.019, 0.007, m_, axis=dd, n=7)])
    O.arm(1, 50, [(0.3, 40, 10), (0.4, -70, 10), (0.3, 140, 0)], L=1.0, n=12, tipr=0.003, suckers=(0.2, 0.6))
    O.arm(3, 40, [(0.3, 45, 0), (0.4, -70, -14), (0.3, 130, 0)], L=1.05, n=12, tipr=0.003)
    O.arm(5, 22, [(0.4, 20, 0), (0.3, -40, 0), (0.3, 95, -20)], L=1.0, n=9, tipr=0.003)


@pose("signalman")
def _signalman(O):
    """It sits atop a signal lever with an arm on each of the others, under a small lamp that shows the field's colour."""
    O.lid_slant = -1.0
    O.body()
    C = O.C
    base_z = -0.46
    O.static.append(hard(g.box(C + Vector((0, 0.02, base_z)), (0.66, 0.2, 0.06)), "iron_pot"))
    O.static.append(hard(g.box(C + Vector((0, 0.02, base_z + 0.04)), (0.6, 0.13, 0.03)), "iron_pot_light"))
    O.static.append(rod(C + Vector((0, 0.02, base_z + 0.03)), C + Vector((0, 0.02, -0.02)), 0.016, "iron_pot_light", n=5))
    handles = []
    for q, (x_, pull) in enumerate(((-0.26, -0.2), (-0.13, 0.22), (0.13, -0.24), (0.26, 0.18))):
        b0 = C + Vector((x_, 0.02, base_z + 0.03))
        topp = b0 + Vector((0, -math.sin(pull) * 0.31, math.cos(pull) * 0.31))
        O.static.append(rod(b0, topp, 0.012, "iron_pot_light", n=4))
        O.static.append(rod(topp, topp + (topp - b0).normalized() * 0.07, 0.019, "brass_key" if q % 2 else "wood_pale", n=6))
        handles.append(topp + (topp - b0).normalized() * 0.03)
    for i, h in ((2, handles[0]), (0, handles[1]), (1, handles[2]), (3, handles[3])):
        p0, dr = O.root(i)
        side = 1 if h.x > 0 else -1
        O.arm_pts(i, [p0 + dr * 0.08 + Vector((0, 0, -0.02)), (p0 + h) / 2 + Vector((side * 0.05, -0.02, 0.0)), h + Vector((side * 0.03, 0.0, 0.03)), h + Vector((0.0, -0.03, 0.0)), h + Vector((-side * 0.03, 0.0, -0.02)),
                      h + Vector((0, 0.03, 0.0))], wave=False, n=11, tipr=0.006, toward=h)
    # the lamp over it, on an iron neck from the frame
    neck = [C + Vector((0.3, 0.1, base_z)), C + Vector((0.34, 0.14, -0.1)), C + Vector((0.3, 0.14, 0.34)), C + Vector((0.18, 0.1, 0.56)), C + Vector((0.05, 0.02, 0.6))]
    O.static.append(wire(neck, 0.012, "iron_pot", n=4))
    hook = neck[-1] - Z * 0.012
    O.mover("sway", "lamp", p_lamp(hook, 1.0), hook)
    O.arm(4, 50, [(0.4, 30, 0), (0.6, 200, 20)], L=0.9, n=9, tipr=0.004)
    O.arm(5, 40, [(0.4, 30, 0), (0.6, -190, 20)], L=0.9, n=9, tipr=0.004)
    O.pair(3, 26, [(0.5, 16, 0), (0.5, 120, 0)], L=0.8, n=7, pieces=1, tipr=0.004)


@pose("skeleton-key")
def _skeleton_key(O):
    """Thin as wire and pale as bone, and the shape of what it is: its arms a ring, one long arm let straight down, a single plain key at the end of it."""
    O.lid_slant = -1.0
    O.body()
    C = O.C
    rr = 0.15
    cen = C + Vector((0, 0.0, -rr - 0.02))
    low = cen - Z * rr
    for i, sg in ((2, -1), (3, 1), (4, -1), (5, 1)):
        back = 0.0 if i < 4 else 0.03
        pts = helix(cen + Vector((0, back, 0)), Y, rr * (1.0 if i < 4 else 0.8), -90, sg * 178 * (1.0 if i < 4 else 0.94), 0.0, n=8, u=X)
        O.arm_pts(i, pts[1:], wave=False, n=11, r=0.95 if i < 4 else 0.7, tipr=0.012, toward=cen + Vector((0, back, 0)), bare=i >= 4)
    half = helix(cen + Vector((0, -0.036, 0)), Y, rr * 0.98, -90, -176, 0.0, n=6, u=X)[1:]
    shaft = O.arm_pts(0, half + [low + Vector((0, -0.012, -0.09)), low + Vector((0, 0, -0.36)), low + Vector((0, 0, -0.68))], n=13, still=0.52, pieces=2, r=0.85, tipr=0.014, bare=True)
    O.hold(shaft, [key_bit(shaft.tip + Z * 0.115, -Z, Vector((-1, 0, 0)), 1.5, "accent", 2, thick=0.016), band(shaft.tip + Z * 0.13, 0.02, 0.007, "accent_dark", axis=Z, n=7)])
    collar = helix(low + Vector((0, 0, -0.012)), -Z, 0.03, 200, 700, 0.07, n=12, u=Vector((0, -1, 0)))
    p0, dr = O.root(1)
    O.arm_pts(1, helix(cen + Vector((0, -0.036, 0)), Y, rr * 0.98, -90, 172, 0.0, n=6, u=X)[1:] + collar, wave=False, n=14, r=0.8, tipr=0.007, toward=lambda p: Vector((low.x - p.x, low.y - p.y, 0)))
    O.pair(3, 60, [(0.3, 0, 0), (0.7, -400, 0)], L=0.42, n=8, pieces=1, tipr=0.004)


@pose("shell-carrier")
def _shell_carrier(O):
    """The two halves of a great shell, one either side, and it tiptoes on the tips of two arms like someone late."""
    O.lid_slant = -1.0
    O.body()
    C = O.C
    for sg, i in ((-1, 2), (1, 3)):
        a = O.arm(i, 112, [(0.3, 0, 0), (0.4, 30, 10), (0.3, -100, 0)], L=0.9, n=9, wave=False, tipr=0.012)
        sc = C + Vector((sg * 0.31, 0.0, 0.1))
        O.hold(a, p_shell(sc, Vector((-sg, 0.1, 0.12)), 0.23, deep=0.42))
        j = i + 2
        p0, dr = O.root(j)
        O.arm_pts(j, [p0 + dr * 0.1, sc + Vector((sg * 0.02, 0.2, -0.08)), sc + Vector((sg * 0.07, 0.12, -0.2)), sc + Vector((sg * 0.02, -0.02, -0.235))], wave=False, n=9, tipr=0.008, toward=sc)
    O.arm_pts(0, [C + Vector((-0.07, -0.12, -0.06)), C + Vector((-0.1, -0.2, -0.2)), C + Vector((-0.06, -0.16, -0.36)), C + Vector((-0.08, -0.2, -0.47))], n=8, tipr=0.006, still=0.45, pieces=1)
    O.arm_pts(7, [C + Vector((0.06, 0.13, -0.06)), C + Vector((0.07, 0.24, -0.16)), C + Vector((0.04, 0.2, -0.33)), C + Vector((0.05, 0.28, -0.47))], n=8, tipr=0.006, still=0.45, pieces=1)
    O.arm(1, 60, [(0.4, -20, -10), (0.6, 250, 0)], L=0.8, n=9, pieces=1)
    O.arm(6, 50, [(0.4, -20, 0), (0.6, 250, 0)], L=0.75, n=8, pieces=1)


@pose("gardener")
def _gardener(O):
    """A low wall of shells and bright stones round it, and a small green thing growing in the middle; it is bringing one more stone."""
    O.lid_slant = 0.6
    O.body()
    C = O.C
    gz = -0.085
    g0 = C + Vector((0, -0.04, gz))
    O.static.append(turn([(0.0, -0.11), (0.16, -0.095), (0.31, -0.05), (0.39, -0.012), (0.4, 0.0), (0.0, 0.006)], g0, Z, "earth_bed", n=12))
    kinds = ("stone_wall", "bone_shell", "accent", "stone_wall_pale", "bone_shell_dark", "accent_pale", "stone_wall_dark", "bone_shell", "accent_light", "stone_wall", "bone_dish", "accent")
    for q in range(12):
        a = 2 * math.pi * (q + 0.3) / 12
        r_ = 0.05 + 0.012 * math.sin(q * 2.7)
        O.static.append(p_stone(g0 + Vector((math.cos(a) * 0.36, math.sin(a) * 0.36, r_ * 0.55)), r_, kinds[q], seed=q, flat=0.8))
    O.static.extend(p_sprig(g0 + Vector((-0.1, -0.22, 0.0)), 0.13))
    lift = O.arm(2, 112, [(0.2, 0, 0), (0.36, 50, -10), (0.1, -40, 0), (0.34, 0, -330)], L=1.2, n=12)
    O.hold(lift, [p_stone(lift.centre(0.3) + Z * 0.02, 0.055, "accent_light", seed=3.0, flat=0.8)])
    tend = O.arm_pts(0, [C + Vector((-0.09, -0.13, -0.02)), g0 + Vector((-0.16, -0.14, 0.035)), g0 + Vector((-0.17, -0.24, 0.03)), g0 + Vector((-0.1, -0.29, 0.03)), g0 + Vector((-0.045, -0.24, 0.035))], n=10, still=0.35, pieces=1,
                     suckers=(0.3, 0.8))
    for i, out in ((1, 84), (3, 88), (4, 86), (5, 84), (6, 84), (7, 86)):
        O.arm(i, out, [(0.5, -10, 6), (0.5, 150 if i % 2 else 190, -10)], L=0.72, n=8, pieces=1, still=0.45)


@pose("beard")
def _beard(O):
    """An old dented helmet sits on it like a house; two gold eyes under the brim, and its arms below like a beard."""
    O.lid = 0.0
    O.body(mantle=False)
    C = O.C
    parts, axis = p_helm(O.head + Vector((0, 0.035, 0.078)), 1.0, back=0.24)
    O.static.extend(parts)
    O.mantle_at = None
    O.sock = {"socket_head": O.head + Vector((0, 0.06, 0.27)), "socket_back": O.head + Vector((0, 0.2, 0.1))}
    spread = (-78, -50, -24, 0, 24, 50, 78, 180)
    for q, i in enumerate((4, 2, 0, 6, 1, 3, 5, 7)):
        az = spread[q]
        if az == 180:
            O.arm(i, 30, [(0.5, 10, 0), (0.5, 150, 0)], L=0.8, n=7, pieces=1, az=az)
            continue
        Lk = 1.25 - 0.4 * (abs(az) / 78.0) ** 1.3
        O.arm(i, 20, [(0.3, 22, 0), (0.4, -34, 6), (0.3, 80 + 40 * (q % 2), 0)], L=Lk, n=10, pieces=2, still=0.25, az=az, suckers=(0.72, 1.0) if abs(az) < 30 else None)


# --- Sleeps-on-it: the one with ear-fins and a web, amethyst ------------------------------

@pose("dozing")
def _dozing(O):
    """Asleep on an open book: a bell with ears, its arms and their web spread over the pages."""
    O.root_coat = 0.0
    O.body()
    for i in range(8):
        O.arm(i, 92, [(0.5, -8, 0), (0.5, -55, 14 if i % 3 else -10)], L=1.0, n=8, pieces=1, still=0.55)
    O.web(to=0.55)
    O.static.extend(p_book(O.C + Vector((0, -0.03, -0.07)), w=0.84, d=0.56, thick=0.06, lines_=4, ribbon="accent_light"))
    O.tilt = 0.2


@pose("comb")
def _comb(O):
    """It hangs like a bell, its arms let straight down in a row; pale marks down each, and one of them lit: the hour."""
    O.root_coat = 0.0
    O.body()
    C = O.C
    order = (4, 2, 0, 6, 7, 1, 3, 5)
    for q, i in enumerate(order):
        x_ = -0.21 + 0.06 * q
        L = 0.42 + 0.035 * q
        p0, dr = O.root(i)
        hour = 0.36 + 0.07 * q
        O.arm_pts(i, [p0 + dr * 0.05 + Vector((0, 0, -0.03)), C + Vector((x_, -0.02 + 0.012 * (q % 2), -0.14)), C + Vector((x_, -0.02, -0.14 - L * 0.5)), C + Vector((x_ + 0.006, -0.02, -0.14 - L))],
                  n=10, still=0.3, pieces=2, tipr=0.007, lit=(hour, hour + 0.07), o0=Vector((0, 1, 0)))
    O.web(to=0.3, sag=0.1)


@pose("parasol")
def _parasol(O):
    """It hangs perfectly still, its web spread between its arms like a parasol."""
    O.root_coat = 0.0
    O.no_fins = True
    O.body()
    O.fins("ear", 1.2, still=True)
    for i in range(8):
        O.arm(i, 104, [(0.55, -34, 0), (0.33, -30, 0), (0.12, 60, 0)], L=1.25, n=9, wave=False, tipr=0.008)
    O.web(to=0.86, sag=0.22, top="S")
    rim = O.arms[2].at(0.86)[0]
    rr = math.hypot(rim.x, rim.y)
    O.static.append(band(Vector((0, 0, rim.z - 0.05)), rr * 1.12, 0.006, field("still", 2.2), n=20))


@pose("tucked")
def _tucked(O):
    """Drawn up tall and gone clear as glass; weather inside it, cloud and a small light; its arms tucked up under it."""
    O.lid = 0.0
    O.root_coat = 0.0
    O.body(mantle=False)
    O.mantle(window=(13, 14, 15, 0, 1))
    N, ax, R, H = O.mantle_at, O.mantle_axis, O.mantle_R, O.mantle_H
    sky = cloud(N + ax * H * 0.56, R * 0.4, seed=1.0, n=4, mats=("mist_cloud", "mist_cloud_dark"), squash=0.7) + cloud(N + ax * H * 0.3 + Vector((0.03, 0, 0)), R * 0.3, seed=2.4, n=3, mats=("mist_cloud_dark", "mist_cloud"), squash=0.7)
    O.mover("spin", "weather", sky, N + ax * H * 0.45, parent="mantle")
    O.mover("pulse", "light", [blob(N + ax * H * 0.42 + Vector((-0.02, -0.02, 0)), 0.03, field("storm", 3.2), n=7, m=4)], N + ax * H * 0.42 + Vector((-0.02, -0.02, 0)), parent="mantle")
    for i in range(8):
        O.arm(i, 74 + 10 * (i % 2), [(0.26, -6, 0), (0.74, -410, 0)], L=0.74, n=10, pieces=1, still=0.3)


@pose("writer")
def _writer(O):
    """A slow cloud of ink hangs by it in the shape of the last thing it thought, and the arm that wrote it is black to the elbow."""
    O.root_coat = 0.0
    O.body()
    pen = O.arm(2, 106, [(0.2, 0, 0), (0.3, 40, -6), (0.5, 20, 0)], L=1.35, n=11, still=0.4, pieces=2, ink=0.48, tipr=0.007)
    tip = pen.tip
    cc = tip + Vector((-0.1, -0.02, 0.1))
    # the thought, in ink: a ring that has not quite closed, and a mote of the field in it
    blot = [blob(p, r_, "ink_cloud" if q % 2 else "ink_cloud_edge", n=7, m=4, scale=(1, 0.8, 0.9)) for q, (p, r_) in enumerate(
        [(cc + Vector((math.cos(a) * 0.1, 0.01 * math.sin(a * 2), math.sin(a) * 0.1)), 0.036 + 0.014 * math.sin(a * 1.7)) for a in [math.radians(t) for t in (-70, -25, 20, 65, 110, 155, 200, 245)]])]
    blot.append(blob(cc, 0.022, field("thought", 3.2), n=6, m=4))
    blot.append(soft(g.tongue([tip + Vector((-0.012, 0, 0.012)), tip + Vector((-0.03, 0, 0.03)), cc + Vector((0.07, 0, -0.075))], [0.006, 0.02, 0.034], thick=0.6, normal=Y), "ink_cloud"))
    O.mover("bob", "ink", blot, cc)
    for i, out in ((0, 40), (1, 46), (3, 62), (4, 40), (5, 44), (6, 30), (7, 30)):
        O.arm(i, out, [(0.5, 10, 0), (0.5, 90 + 40 * (i % 3), 10)], L=0.95, n=9, pieces=1, still=0.42)
    O.web(to=0.4)


@pose("in-the-blot")
def _in_the_blot(O):
    """The ink round it never clears: two eyes look out of the cloud, and the outline of a thing that has not happened yet."""
    O.lid = 0.0
    O.root_coat = 0.0
    O.body()
    C = O.C
    hc = O.head
    lobes = [((-0.2, 0.06, 0.1), 0.15), ((0.19, 0.08, 0.06), 0.15), ((-0.08, 0.12, 0.33), 0.13), ((0.13, 0.14, 0.3), 0.12), ((-0.24, 0.06, -0.1), 0.11), ((0.24, 0.07, -0.12), 0.1), ((0.0, 0.12, -0.14), 0.13),
             ((-0.32, 0.05, 0.02), 0.07), ((0.31, 0.08, 0.16), 0.07)]
    ink = [blob(hc + Vector(p), r_, "ink_cloud" if q % 3 else "ink_cloud_edge", n=8, m=5, scale=(1, 0.75, 0.92)) for q, (p, r_) in enumerate(lobes)]
    for q, (x_, z_, L) in enumerate(((-0.18, -0.24, 0.13), (0.06, -0.3, 0.17), (0.25, -0.22, 0.1))):      # it drips
        b0 = hc + Vector((x_, 0.05, z_))
        ink.append(soft(g.tongue([b0 + Z * 0.05, b0, b0 - Z * L * 0.6, b0 - Z * L], [0.03, 0.045, 0.03, 0.004], thick=0.8, normal=Y), "ink_cloud"))
    O.static.extend(ink)
    # what has not happened yet, drawn in the field's light on the ink: a door, standing open
    sig = hc + Vector((-0.2, -0.065, 0.12))
    for p0, p1 in (((-0.05, -0.07), (-0.05, 0.07)), ((-0.05, 0.07), (0.04, 0.07)), ((0.04, 0.07), (0.04, -0.07)), ((0.04, 0.07), (0.085, 0.045)), ((0.085, 0.045), (0.085, -0.09)), ((0.085, -0.09), (0.04, -0.07))):
        O.static.append(rod(sig + Vector((p0[0], -0.012 * abs(p0[0]) * 0, p0[1])), sig + Vector((p1[0], 0, p1[1])), 0.006, field("omen", 3.0), n=3))
    for i, (out, L) in ((0, (50, 1.2)), (1, (56, 1.15)), (2, (84, 1.3)), (3, (88, 1.25)), (4, (70, 1.0)), (5, (64, 1.0))):
        O.arm(i, out, [(0.45, 6, 8), (0.55, 150 + 30 * (i % 2), 0)], L=L, n=10, pieces=1, still=0.5, suckers=(0.6, 1.0) if i < 2 else None)


@pose("copyist")
def _copyist(O):
    """A thick book open across four arms, and two more writing in it, very small and very straight."""
    O.root_coat = 0.0
    O.body()
    C = O.C
    bx = Vector((1, 0, 0))
    by = Vector((0, 0.72, 0.69))
    bc = C + Vector((0, -0.33, -0.14))
    w, d = 0.56, 0.38
    O.static.extend(p_book(bc, w, d, x=bx, y=by, thick=0.075, lines_=5, ribbon="accent"))
    up = bx.cross(by)
    for i, sx in ((0, -0.22), (1, 0.22), (2, -0.52), (3, 0.52)):
        p0, dr = O.root(i)
        sgx = 1 if sx > 0 else -1
        if abs(sx) < 0.4:       # two under its near edge
            edge = bc + bx * (w * sx) - by * (d * 0.53) - up * 0.035
            over = edge + by * 0.06 + up * 0.09
            pts = [p0 + dr * 0.07 + Vector((0, 0, -0.05)), edge - up * 0.03 + by * 0.06, edge - by * 0.015, over]
        else:                   # two at its sides
            edge = bc + bx * (w * sx) + by * (d * 0.1) - up * 0.035
            over = edge - bx * sgx * 0.06 + up * 0.09
            pts = [p0 + dr * 0.09 + Vector((0, 0, -0.03)), edge - up * 0.03 - bx * sgx * 0.05, edge + bx * sgx * 0.02, over]
        O.arm_pts(i, pts, wave=False, n=9, tipr=0.007, toward=bc)
    for i, sx in ((4, -1), (5, 1)):
        nib = bc + bx * (sx * w * 0.22) + by * (d * (0.1 if sx < 0 else -0.14)) + up * 0.05
        p0, dr = O.root(i)
        pen = O.arm_pts(i, [p0 + dr * 0.12 + Vector((0, -0.04, 0.02)), nib + Vector((sx * 0.14, 0.0, 0.1)), nib + Vector((sx * 0.07, -0.01, 0.12)), nib + Vector((sx * 0.03, -0.01, 0.07))], n=10, still=0.45, pieces=1, tipr=0.006)
        O.hold(pen, p_quill(nib, Vector((sx * 0.3, -0.1, 0.95)), 1.2, face=Vector((0, -1, 0.2))))
    O.pair(3, 34, [(0.5, 10, 0), (0.5, 150, 0)], L=0.9, n=8, pieces=1)


@pose("chandelier")
def _chandelier(O):
    """Clear as glass, its arms turned up like a chandelier, and one small light inside that is on its way down an arm."""
    O.lid = 0.0
    O.root_coat = 0.0
    O.body(mantle=False)
    O.mantle(window=(13, 14, 15, 0, 1))
    N, ax, R, H = O.mantle_at, O.mantle_axis, O.mantle_R, O.mantle_H
    O.mover("pulse", "thought", [blob(N + ax * H * 0.45, 0.032, field("thought", 3.2), n=8, m=5)], N + ax * H * 0.45, parent="mantle")
    for i in range(8):
        O.arm(i, 76, [(0.3, -26, 0), (0.42, 142, 0), (0.28, 16, 0)], L=1.05, n=10, pieces=2 if i < 4 else 1, still=0.34, tipr=0.011, lit=(0.5, 0.62) if i == 2 else None, suckers=(0.4, 0.75) if i in (0, 1) else None)
    O.web(to=0.3, sag=0.2)


@pose("ring-of-lights")
def _ring_of_lights(O):
    """A separate small light at the tip of each arm, held out in a ring: its eight minds, and they do not agree."""
    O.lid = 0.0
    O.root_coat = 0.0
    O.body(mantle=False)
    O.mantle(window=(13, 14, 15, 0, 1))
    N, ax, R, H = O.mantle_at, O.mantle_axis, O.mantle_R, O.mantle_H
    O.mantle_parts.append(blob(N + ax * H * 0.45, 0.03, field("thought", 2.6), n=7, m=4))
    for i in range(8):
        a = O.arm(i, 98, [(0.6, -16, 0), (0.25, 60, 0), (0.15, 40, 0)], L=1.02, n=10, pieces=2, still=0.3, tipr=0.012, suckers=(0.5, 0.9) if i in (0, 1) else None)
        c = a.tip + a.dir * 0.035
        O.mover("pulse", "mind%d" % i, [blob(c, 0.03, field("mind", 3.2), n=7, m=4)], c, parent=a)


@pose("cloaked")
def _cloaked(O):
    """Dark as deep water, a web drawn round its arms like a cloak, great fins, and one cold light where the arms meet."""
    O.root_coat = 0.0
    O.body()
    C = O.C
    for i in range(8):
        out = 30 if i in (0, 1) else (24 if i < 6 else 20)
        O.arm(i, out, [(0.35, 26, 4 if i > 1 else -10), (0.45, -30, 0), (0.2, 40, 0)], L=1.3, n=9, pieces=1, still=0.78, tipr=0.006)
    ring = [O.arms[k] for k in (0, 2, 4, 6, 7, 5, 3, 1)]
    O.web(arms=ring, to=0.78, sag=0.18, top="S", under="P", closed=False)
    c = C + Vector((0, -0.05, -0.1))
    O.mover("pulse", "cold", [blob(c, 0.042, field("cold", 3.4), n=8, m=5)], c)


def build(form_id, level, spec, base):
    O = Octo(form_id, level, spec)
    name = spec.get("arms") or "inkling"
    fn = POSES.get(name)
    if fn is None:
        log("NO POSE:", name, "for", form_id)
        fn = POSES["inkling"]
    fn(O)
    st, size = opt(spec.get("fins"))
    if st and O.mantle_style and not getattr(O, "no_fins", False):
        O.fins(st, size)
    O.finish()


def register(builders):
    builders["octopus"] = build


# ======================================================================================
# Its gifts: what a hybrid of another base wears to say it is half this
# (game/assets/genius/gifts/octopus-<feature>.glb; made at the socket's origin, in the
# kit's size, a body 0.72 tall; the pieces keep their names, so they move on the wearer too)
#
#     python tools/blender/lines_octopus.py gifts
# ======================================================================================

def _gift(O):
    """The objects of a thing built with an Octo, where it was built (no ground, no sockets)."""
    gl = lines()
    objs, static = [], list(O.static)
    chains = []
    for a in O.arms:
        pcs, has_still = O._arm_parts(a)
        if has_still or not a.wave:
            static.extend(pcs[0][2])
            pcs = pcs[1:]
        chains.append((a, pcs))
    objs.append(make("octopus_gift", static))
    for a, pcs in chains:
        parent = None
        for q, (j0, j1, parts) in enumerate(pcs):
            ob = make("wave_arm%d_%d" % (a.i, q), parts)
            d, oo, b = a.fr[j0]
            turned(ob, a.pts[j0], Matrix((b, d, b.cross(d))).transposed())
            if parent is not None:
                gl.child_of(ob, parent)
            parent = ob
            objs.append(ob)
    for kind, what, parts, pivot_, side, n_, par, rot in O.movers:
        ob = make("%s_%s%s" % (kind, what, "_" + side if side else ""), parts)
        turned(ob, pivot_, rot)
        objs.append(ob)
    return objs


def gift_many_arms():
    """Arms that curl and hold: four of an octopus's, out of the back of whatever wears them,
    their pale suckered sides turned out. They take the wearer's own Path's colour."""
    O = Octo("gift", 2, {"accent": "marigold", "skin": ["bands", 1.0]})
    O.root_coat = 0.0
    O.k_girth = 1.15
    O.static.append(blob((0, 0.0, -0.01), 0.075, O.m("S"), n=8, m=4, scale=(1.2, 1.0, 0.6)))
    for i, (x_, az, out, turns, L) in enumerate(((-0.05, -78, 150, [(0.45, -20, 10), (0.55, 250, 0)], 1.0), (0.05, 78, 150, [(0.45, -20, 10), (0.55, 250, 0)], 1.0),
                                                 (-0.035, -140, 128, [(0.5, 30, 0), (0.5, -230, 20)], 0.85), (0.035, 140, 128, [(0.5, 30, 0), (0.5, -230, 20)], 0.85))):
        O.arm(i, out, turns, L=L, az=az, root=Vector((x_, 0.02 * (i // 2), 0.0)), n=12, pieces=2, still=0.25, suckers=(0.2, 1.0), tipr=0.008)
    return _gift(O)


def gift_bar_eyes():
    """Gold eyes with a bar for a pupil: two of them on their turrets, wide of the wearer's own, a ring of the field round each."""
    O = Octo("gift", 2, {"accent": "marigold"})
    O.k_head = 1.0
    for sg, side in ((-1, "r"), (1, "l")):
        e = Vector((sg * 0.5, -0.84, 0.16)).normalized()
        E = Vector((sg * 0.062, -0.012, 0.012))
        O.eye(E, e, 0.036, "bar", side, sg)
    O.static.append(soft(g.tube([(-0.06, 0.012, 0.03), (-0.03, 0.0, 0.05), (0.03, 0.0, 0.05), (0.06, 0.012, 0.03)], [0.012, 0.016, 0.016, 0.012], n=5), O.m("T")))
    return _gift(O)


GIFTS = {"octopus-many-arms": gift_many_arms, "octopus-bar-eyes": gift_bar_eyes}


def gifts():
    gl = lines()
    for name, fn in GIFTS.items():
        gl.accent({"accent": "marigold"})
        objs = fn()
        path = os.path.join(kit.OUT, "gifts", name + ".glb")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        log("wrote", os.path.relpath(path, kit.ROOT), "%d KB" % (os.path.getsize(path) // 1024))


if __name__ == "__main__":
    if sys.argv[1:] == ["gifts"]:
        import genius_lines  # noqa: F401  (it registers the families, this one among them)
        import lines_octopus
        genius_lines._palette_of("octopus")
        lines_octopus.gifts()
    else:
        print(__doc__)
