"""WILDLINE genius lines, the armors: the Shield, the Gauntlet and the Coat, a body of its own
for every form (docs/genius-evolutions.md, "The armors"). genius_lines.py loads this file
(register()) and builds a form from the `body` of its node in data/genius-bases/<base>.json:

    python tools/blender/genius_lines.py shield
    python tools/blender/genius_lines.py gauntlet gauntlet-hammer-hand
    python tools/blender/genius_lines.py coat

These are the defensive items: a genius that is worn. So every model is made at the size it
would be worn at by one of the game's people (the weapon kit's units: a person is about 2.4
tall, a hand 0.26 long, shoulders 0.62 across), and carries an empty named `wear` where it
meets its partner:

    shield     the hand that holds it: the middle of the grip behind the boss. Its axes are
               the model's own, so on a hand slot it sits as the weapon kit's shields do (the
               grip along the fist, the face out of the back of the hand, the top up).
    gauntlet   the middle of the wrist's opening. A left hand. In the game's axes its +Y runs
               out of the thumb side and its +Z out of the back of the hand, as a hand slot's
               do, and its -X runs to the fingertips.
    coat       the nape: between the shoulders, at the base of the collar. Its axes are the
               wearer's own (up, the wearer's left, the wearer's front as the model's).

To wear one: give the model a scale of one and bring `wear` onto the place. As a body at its
partner's shoulder it is stood by `ref_top` like any other form, which is set so that the
piece is as large as its stage says and its `stands` asks (a Starter's buckler floats larger
than life so it can be seen; a tower shield a little smaller).

Conventions are the genius kit's: Z up, facing -Y, the wearer's left +X; materials named
field_* are the only light; leather, wood (the shield) or leather_dark, and metal_brass are
its partner's coat (data/genius-looks.json), and the marks its partner may show are there on
every form (a blazon and studs; stitching and a cuff; stitching and studs).
"""
import json
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
import genius_relics as rel  # noqa: E402
from genius_relics import strap, loop, ringtube  # noqa: E402

ROOT = kit.ROOT

# what these are made of that the kits' palette did not have: muted, a value apart
PALETTE.update({
    "steel_polish": ((0.27, 0.34, 0.43), 0.12, 0.9), "steel_glint": ((0.86, 0.88, 0.9), 0.08, 0.9), "steel_dark": ((0.2, 0.21, 0.25), 0.5, 0.9),
    "copper_old": ((0.3, 0.17, 0.1), 0.5, 0.8), "verdigris": ((0.2, 0.33, 0.29), 0.8, 0.2),
    "iron_dent": ((0.06, 0.06, 0.07), 0.7, 0.6), "iron_bright": ((0.42, 0.43, 0.46), 0.3, 0.8),
    "timber_grey": ((0.3, 0.29, 0.27), 0.95, 0.0), "timber_dark": ((0.15, 0.14, 0.13), 0.95, 0.0), "wood_dark": ((0.13, 0.08, 0.045), 0.85, 0.0),
    "soot": ((0.025, 0.022, 0.02), 1.0, 0.0), "moss": ((0.1, 0.15, 0.075), 0.95, 0.0), "weed": ((0.055, 0.09, 0.06), 0.95, 0.0),
    "paint_pale": ((0.7, 0.66, 0.55), 0.8, 0.0), "paint_red": ((0.36, 0.09, 0.07), 0.8, 0.0), "glass_dark": ((0.03, 0.045, 0.07), 0.08, 0.0),
    "hide_drum": ((0.62, 0.52, 0.38), 0.7, 0.0), "rope": ((0.36, 0.29, 0.19), 0.95, 0.0), "scar_pale": ((0.62, 0.5, 0.44), 0.6, 0.0),
    "cloth_grey": ((0.3, 0.3, 0.3), 0.95, 0.0), "cloth_black": ((0.035, 0.035, 0.04), 0.95, 0.0), "cloth_patch_a": ((0.3, 0.14, 0.1), 0.95, 0.0),
    "cloth_patch_b": ((0.14, 0.2, 0.26), 0.95, 0.0), "cloth_patch_c": ((0.3, 0.26, 0.14), 0.95, 0.0), "cloth_oil": ((0.035, 0.045, 0.05), 0.25, 0.0),
    "cloth_dust": ((0.4, 0.38, 0.34), 0.98, 0.0), "cloth_lining": ((0.2, 0.07, 0.06), 0.8, 0.0), "pelt_dark": ((0.12, 0.09, 0.07), 0.95, 0.0),
    "pelt_light": ((0.4, 0.33, 0.25), 0.95, 0.0), "frost": ((0.78, 0.84, 0.86), 0.2, 0.0), "wrap_linen": ((0.6, 0.55, 0.45), 0.9, 0.0),
    "thread": ((0.72, 0.68, 0.58), 0.8, 0.0), "skin_pale": ((0.66, 0.56, 0.5), 0.6, 0.0), "stamp_ink": ((0.16, 0.1, 0.2), 0.8, 0.0),
})

# what is soft is shaded round; what is hard keeps its planes (the contract's rule)
SOFT = ("fur", "cloth", "wool", "smoke", "shade", "tongue", "maw", "field", "cord", "leather", "scar", "pelt", "rope", "wrap", "skin", "thread", "hide_drum", "mark_stitch", "mark_cuff", "mark_lining")


def log(*a):
    print("[lines_armors]", *a)


def opt(v, default=1.0):
    """A slot's value as (style, size): "spike", ["spike", 1.3] or None."""
    if v is None or v is False:
        return None, 0.0
    if isinstance(v, (list, tuple)):
        return v[0], (float(v[1]) if len(v) > 1 else default)
    return v, default


def each(v):
    """A slot that may hold several: "dents", ["teeth", 1.2], or [["teeth", 1.2], "dents"]."""
    if v is None or v is False:
        return []
    if isinstance(v, str):
        return [(v, 1.0)]
    if len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], (int, float)):
        return [(v[0], float(v[1]))]
    return [opt(x) for x in v]


def Rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, "X")


def Ry(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Y")


def Rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


def T(v):
    return Matrix.Translation(Vector(v))


def moved(geo, M):
    return g.moved(geo, M)


def lathe_at(profile, centre, axis, n=8):
    """A profile of (radius, distance along the axis) spun about an axis through centre."""
    axis = V(axis).normalized()
    u, v = g._frame(axis)
    c = V(centre)
    rings = [[c + axis * d + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * r for k in range(n)] for r, d in profile]
    return g.loft(rings, caps=True)


class Piece:
    """What a form is made of, gathered by material; then one object, its hard things flat and
    its soft things round, its sockets where it says they are."""

    def __init__(self, name):
        self.name = name
        self.geo = {}            # material name -> [material, geometry]
        self.objects = []        # solids already made (a plate with its face, back and edge)
        self.sockets = {}        # name -> (place, turn or None)
        self.wear = None         # (place, turn)

    def add(self, geo, material, smooth=None):
        """Flat planes unless its stuff is soft; smooth=True for what is turned or cast round
        (a rim, a boss, a rivet, an eye), which is also a third the size on disk."""
        if not geo or not geo[0]:
            return
        soft = material.name.startswith(SOFT) if smooth is None else bool(smooth)
        key = (material.name, soft)
        cur = self.geo.get(key)
        self.geo[key] = [material, g.merge(cur[1] if cur else None, geo), soft]

    def round(self, geo, material):
        self.add(geo, material, smooth=True)

    def add_items(self, items, smooth=True):
        for geo, material in items:
            self.add(geo, material, smooth=smooth)

    def solid(self, geo, pick):
        """One closed solid whose faces take the material pick(centre, normal) gives."""
        ob = g.to_object(self.name + "_solid%d" % len(self.objects), geo, None)
        me = ob.data
        names = []
        for p in me.polygons:
            m = pick(p.center, p.normal)
            if m.name not in names:
                names.append(m.name)
                me.materials.append(m)
            p.material_index = names.index(m.name)
            p.use_smooth = m.name.startswith(SOFT)
        self.objects.append(ob)
        return ob

    def build(self, M=None):
        obs = list(self.objects)
        for i, (material, geo, soft) in enumerate(self.geo.values()):
            obs.append(g.to_object("%s_%d" % (self.name, i), geo, material, smooth=soft))
        ob = g.join(self.name, obs)
        if M is not None:
            ob.data.transform(M)
        # stand it on its lowest point
        low = min(v.co.z for v in ob.data.vertices)
        ob.data.transform(Matrix.Translation((0, 0, -low)))
        self.lift = Matrix.Translation((0, 0, -low)) @ (M if M is not None else Matrix.Identity(4))
        ob.data.update()
        return ob


def art_size(base):
    """How the game sizes this base's body against its stage's height (data/genius-bodies.json)."""
    sil = base["settled"].get("silhouette", base["silhouette"])
    with open(os.path.join(ROOT, "data", "genius-bodies.json")) as f:
        return float(json.load(f)["silhouettes"].get(sil, {}).get("artSize", 1.0))


def finish(piece, form_id, base, spec, M=None, sockets=None):
    """Join it, stand it, give it its sockets and its `wear`, and write it. It is as large on
    the page and at its partner's shoulder as its stage says and its `stands` asks."""
    import genius_lines as gl
    ob = piece.build(M)
    lo = Vector((min(v.co.x for v in ob.data.vertices), min(v.co.y for v in ob.data.vertices), 0.0))
    hi = Vector((max(v.co.x for v in ob.data.vertices), max(v.co.y for v in ob.data.vertices), max(v.co.z for v in ob.data.vertices)))
    H, W, D = hi.z, hi.x - lo.x, hi.y - lo.y
    measure = max(H, 0.62 * max(W, D))
    ref = measure * art_size(base) / float(spec.get("stands", 1.0))
    s = ref / STAND            # parts and keepsakes are made for a body that stands STAND tall
    yc, yf, yb = (lo.y + hi.y) / 2, lo.y, hi.y
    table = {
        "socket_head": (0, yc, H), "socket_eyes": (0, yf - 0.01, 0.72 * H), "socket_mouth": (0, yf - 0.01, 0.45 * H), "socket_grip": (0, yb + 0.01, 0.5 * H),
        "socket_throat": (0, yf - 0.01, 0.36 * H), "socket_light": (0, yf - 0.01, 0.24 * H), "socket_back": (0, yb + 0.01, 0.66 * H), "socket_body": (0, yf - 0.01, 0.52 * H),
        "socket_tail": (0, yb, 0.06 * H), "socket_arm_l": (hi.x + 0.01, yc, 0.62 * H), "socket_arm_r": (lo.x - 0.01, yc, 0.62 * H),
        "socket_limb_fl": (0.3 * W, yf, 0.02), "socket_limb_fr": (-0.3 * W, yf, 0.02), "socket_keepsake": (0, yf - 0.012, 0.3 * H),
    }
    size = Matrix.Diagonal((s, s, s))
    socks = {name: kit.free_socket(name, at, size) for name, at in table.items()}
    for name, (at, rot) in (sockets or {}).items():          # the builder's own, given in the piece's space before it was stood
        if name in socks:
            bpy.data.objects.remove(socks[name])
        p = piece.lift @ Vector(at)
        r3 = piece.lift.to_3x3() @ (rot if rot is not None else Matrix.Identity(3))
        socks[name] = kit.free_socket(name, p, r3 @ size)
    if piece.wear is not None:
        at, rot = piece.wear
        socks["wear"] = kit.free_socket("wear", piece.lift @ Vector(at), piece.lift.to_3x3() @ (rot if rot is not None else Matrix.Identity(3)))
    path = os.path.join(gl.OUT, form_id + ".glb")
    tris = gl.export_objects([ob], socks, path, ref=ref)
    kb = os.path.getsize(path) // 1024
    if kb > 80:
        log("OVER BUDGET", form_id, kb, "KB")
    return tris


def eye(c, r, facing=(0, -1, 0), lids=None, slit=True):
    return rel._eye(c, r, facing=facing, lids=lids, slit=slit)


# ======================================================================================
# The Shield
# ======================================================================================

def _subdiv(pts, step=None):
    out = []
    n = len(pts)
    if step is None:      # about thirty points round it, whatever its size
        per = sum((Vector(pts[i]) - Vector(pts[(i + 1) % n])).length for i in range(n))
        step = max(0.12, per / 30.0)
    for i in range(n):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % n])
        m = max(1, int(math.ceil((b - a).length / step)))
        for k in range(m):
            out.append(a + (b - a) * (k / m))
    return [(p.x, p.y) for p in out]


def _rrect(w, h, rt, rb, rbl=None, n=4):
    """A rectangle with rounded corners, from the bottom right round to the bottom left."""
    hw = w / 2
    rbl = rb if rbl is None else rbl
    pts = []
    for cx, cz, r, a0 in ((hw - rb, rb, rb, -90), (hw - rt, h - rt, rt, 0), (-hw + rt, h - rt, rt, 90), (-hw + rbl, rbl, rbl, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return _subdiv(pts)


def _bez(a, c, b, n=6):
    return [((1 - t) ** 2 * a[0] + 2 * t * (1 - t) * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * c[1] + t * t * b[1]) for t in [k / n for k in range(n)]]


def outline(shape, w, h):
    """The shield's edge as (x, z) round it, its foot at z = 0. Returns (points, the middle a
    face is fanned from)."""
    hw = w / 2
    if shape in ("round", "oval", "drum"):
        n = 22
        return [(hw * math.sin(2 * math.pi * i / n), h / 2 - (h / 2) * math.cos(2 * math.pi * i / n)) for i in range(n)], (0, h / 2)
    if shape == "tower":
        return _rrect(w, h, 0.42 * hw, 0.14 * hw), (0, h / 2)
    if shape == "door":
        return _rrect(w, h, hw * 0.98, 0.03, n=6), (0, h * 0.5)
    if shape == "rect":
        return _rrect(w, h, 0.04, 0.03, n=1), (0, h * 0.5)
    if shape == "wide":
        return _rrect(w, h, 0.46 * h, 0.2 * h, n=5), (0, h * 0.5)
    if shape == "board":
        return _rrect(w, h, 0.06, 0.06, n=2), (0, h * 0.5)
    if shape == "carriage":
        return _rrect(w, h, 0.12 * hw, 0.06, rbl=0.75 * hw, n=5), (0, h * 0.55)
    if shape == "coffin":
        return _subdiv([(-0.29 * w, 0), (0.29 * w, 0), (0.5 * w, 0.72 * h), (0.33 * w, h), (-0.33 * w, h), (-0.5 * w, 0.72 * h)]), (0, 0.58 * h)
    if shape == "heater":
        pts = [(0, 0)] + _bez((0, 0), (hw, 0.12 * h), (hw, 0.56 * h))[1:] + [(hw, 0.56 * h), (hw, h - 0.04), (hw - 0.04, h), (-hw + 0.04, h), (-hw, h - 0.04), (-hw, 0.56 * h)] + _bez((-hw, 0.56 * h), (-hw, 0.12 * h), (0, 0))[1:]
        return _subdiv(pts), (0, 0.62 * h)
    if shape == "kite":
        top = [(hw * math.cos(math.radians(a)), h - hw + hw * math.sin(math.radians(a))) for a in range(0, 181, 20)]
        pts = [(0, 0)] + _bez((0, 0), (hw * 0.95, 0.3 * h), (hw, h - hw))[1:] + top + _bez((-hw, h - hw), (-hw * 0.95, 0.3 * h), (0, 0))[1:]
        return _subdiv(pts), (0, 0.62 * h)
    raise ValueError("no such shield: " + shape)


class Shield(Piece):
    def __init__(self, form_id, spec):
        Piece.__init__(self, form_id)
        shape, w, h = spec.get("shape", ["round", 0.36, 0.36])
        self.shape, self.w, self.h = shape, float(w), float(h)
        self.curve, self.dome, self.vee = float(spec.get("curve", 0.0)), float(spec.get("dome", 0.0)), float(spec.get("vee", 0.0))
        self.thick = float(spec.get("thick", 0.035))
        self.out, self.c = outline(shape, self.w, self.h)
        self.zc = self.c[1]
        self.u = max(0.3, min(self.w, self.h))           # the size fittings are cut to
        # how it is held as it floats: leaned forward (its top toward the front) and turned
        self.M = Rz(float(spec.get("yaw", 0.0))) @ Rx(float(spec.get("lean", 0.0)))
        self.Mi = self.M.inverted()

    def y(self, x, z):
        """How far the face stands forward at (x, z): the front is -Y."""
        u = min(1.0, abs(2 * x / self.w))
        v = (z - self.zc) / (self.h / 2)
        return -(self.curve * (1 - u * u) + self.dome * max(0.0, 1 - u * u - v * v) + self.vee * (1 - u))

    def P(self, x, z, proud=0.0):
        return Vector((x, self.y(x, z) - proud, z))

    def B(self, x, z, proud=0.0):
        return Vector((x, self.y(x, z) + self.thick + proud, z))

    def inside(self, x, z, margin=0.08):
        """Is (x, z) on the face, a margin in from its edge?"""
        cx, cz = self.c
        k = 1.0 + margin / max(0.05, math.hypot(x - cx, z - cz))
        px, pz = cx + (x - cx) * k, cz + (z - cz) * k
        n, inside = len(self.out), False
        for i in range(n):
            (x0, z0), (x1, z1) = self.out[i], self.out[(i + 1) % n]
            if (z0 > pz) != (z1 > pz) and px < x0 + (pz - z0) * (x1 - x0) / (z1 - z0):
                inside = not inside
        return inside

    def half(self, z):
        """Half its width at a height."""
        xs = [abs(x0 + (z - z0) * (x1 - x0) / (z1 - z0)) for (x0, z0), (x1, z1) in zip(self.out, self.out[1:] + self.out[:1]) if (z0 > z) != (z1 > z)]
        return max(xs) if xs else 0.0

    def plate(self, face, back, edge, rings=2, thick=None, out=None, c=None, scale=1.0, proud=0.0):
        """The board itself: one solid, its face, its back and its edge each their own stuff."""
        out = self.out if out is None else out
        cx, cz = self.c if c is None else c
        t = self.thick if thick is None else thick
        n = len(out)
        verts = []
        for dy in (0.0, t):
            verts.append(self.P(cx, cz, proud) + Vector((0, dy, 0)))
            for k in range(1, rings + 1):
                f = scale * k / rings
                for (x, z) in out:
                    verts.append(self.P(cx + (x - cx) * f, cz + (z - cz) * f, proud) + Vector((0, dy, 0)))
        nb = 1 + rings * n
        faces = []
        for o in (0, nb):
            for i in range(n):
                faces.append((o, o + 1 + i, o + 1 + (i + 1) % n))
            for k in range(rings - 1):
                a0, b0 = o + 1 + k * n, o + 1 + (k + 1) * n
                for i in range(n):
                    faces.append((a0 + i, b0 + i, b0 + (i + 1) % n, a0 + (i + 1) % n))
        fo, bo = 1 + (rings - 1) * n, nb + 1 + (rings - 1) * n
        for i in range(n):
            faces.append((fo + i, bo + i, bo + (i + 1) % n, fo + (i + 1) % n))
        return self.solid((verts, faces), lambda ctr, nrm: face if nrm.y < -0.3 else (back if nrm.y > 0.3 else edge))

    def rim(self, material, r=None, proud=0.0, out=None):
        out = self.out if out is None else out
        r = (self.thick / 2 + 0.012) if r is None else r
        pts = [self.P(x, z, proud) + Vector((0, self.thick / 2, 0)) for x, z in out]
        pts.append(pts[0])
        self.round(g.tube(pts, [r] * len(pts), n=4, caps=False), material)

    def hband(self, z, x0, x1, width, material, proud=0.012, thick=0.018, n=7):
        self.add(strap([self.P(x0 + (x1 - x0) * i / n, z, proud) for i in range(n + 1)], width, thick, up=Z), material)

    def vband(self, x, z0, z1, width, material, proud=0.012, thick=0.018, n=4):
        self.add(strap([self.P(x, z0 + (z1 - z0) * i / n, proud) for i in range(n + 1)], width, thick, up=X), material)

    def line(self, a, b, width, material, proud=0.012, thick=0.014, n=5):
        """A straight stroke on the face from (x, z) to (x, z)."""
        pts = [self.P(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, proud) for i in range(n + 1)]
        self.add(strap(pts, width, thick, up=Y), material)

    def disc(self, x, z, r, material, proud=0.0, squash=0.22, sub=1):
        self.round(g.ico(self.P(x, z, proud), r, sub=sub, scale=(1, squash, 1)), material)

    def stud(self, x, z, r, material):
        self.round(g.ico(self.P(x, z, 0.008), r, sub=0), material)

    def eye(self, x, z, r, lids=None):
        self.add_items(eye(self.P(x, z, 0.004), r, lids=lids))

    def grip(self, z=None, material=None):
        z = self.zc if z is None else z
        k = min(1.0, self.u / 0.6)
        pts = [self.B(0, z + 0.11 * k, 0.0), self.B(0, z + 0.07 * k, 0.07 * k), self.B(0, z - 0.07 * k, 0.07 * k), self.B(0, z - 0.11 * k, 0.0)]
        self.round(g.tube(pts, [0.018 * k + 0.004] * 4, n=6), material or mat("leather"))
        self.wear = (self.B(0, z, 0.07 * k), None)


# --- what a shield's face is made of: (face, back, edge) -------------------------------------

def _faces():
    return {
        "iron": (mat("metal_iron_light"), mat("wood"), mat("metal_iron")),
        "leather": (mat("leather"), mat("wood"), mat("wood")),
        "wood": (mat("wood"), mat("wood_dark"), mat("wood_dark")),
        "polish": (mat("steel_polish"), mat("wood"), mat("metal_brass")),
        "glass": (mat("glass_dark"), mat("wood"), mat("metal_brass")),
        "stone": (mat("stone_hide"), mat("stone_plate"), mat("stone_plate")),
        "timber": (mat("timber_grey"), mat("timber_dark"), mat("timber_dark")),
        "black": (mat("soot"), mat("wood_dark"), mat("soot")),
        "hide": (mat("hide_drum"), mat("wood"), mat("wood")),
        "steel": (mat("iron_bright"), mat("wood"), mat("metal_iron")),
        "copper": (mat("copper_old"), mat("wood"), mat("metal_iron")),
    }


def _planks(S, material, n=None, z0=0.04, z1=None):
    """The joints between its boards."""
    z1 = S.h - 0.04 if z1 is None else z1
    n = n or max(2, int(round(S.w / 0.2)))
    for i in range(1, n):
        x = -S.w / 2 + S.w * i / n
        hz = [z for z in (z0, z1)]
        # keep the joint on the board where the top is arched
        top = z1
        while top > z0 and not S.inside(x, top, 0.02):
            top -= 0.05
        if top - hz[0] > 0.1:
            S.vband(x, hz[0], top, 0.016, material, proud=0.002, thick=0.012)


def _studs_and_blazon(S, style="chevron"):
    """What its partner may show on it: a blazon across the face and studs round it."""
    bl, st = mark("blazon", mat("wood")), mark("studs", mat("wood"))
    hw, h, zc = S.w / 2, S.h, S.zc
    if style == "chevron":
        for s in (1, -1):
            S.line((0, zc - 0.34 * h * 0.5), (s * hw * 0.62, zc - 0.34 * h * 0.5 - hw * 0.42), 0.09 * S.u, bl, proud=0.006)
    elif style == "bar":
        z = 0.3 * h
        S.hband(z, -S.half(z) * 0.82, S.half(z) * 0.82, 0.1 * S.u, bl, proud=0.006, thick=0.012)
    elif style == "arc":
        pts = [(hw * 0.7 * math.cos(math.radians(a)), 0.22 * h + 0.3 * h * math.sin(math.radians(a))) for a in range(200, 341, 20)]
        for a, b in zip(pts, pts[1:]):
            S.line(a, b, 0.07 * S.u, bl, proud=0.006, n=2)
    elif style == "ring":
        S.add(g.tube([S.P(0.26 * S.w * math.cos(2 * math.pi * i / 14), zc + 0.26 * S.w * math.sin(2 * math.pi * i / 14), 0.008) for i in range(15)], 0.022 * S.u + 0.006, n=4, caps=False), bl)
    n = len(S.out)
    k = max(1, n // 12)
    cx, cz = S.c
    for i in range(0, n, k):
        x, z = S.out[i]
        S.stud(cx + (x - cx) * 0.9, cz + (z - cz) * 0.9, 0.012 + 0.008 * S.u, st)


# --- the boss, where it is alive -----------------------------------------------------------

def _boss(S, style, size):
    zc, u = S.zc, S.u * size
    c = S.P(0, zc)
    brass, iron = mat("metal_brass"), mat("metal_iron")
    if style == "none":
        return
    if style in ("eye", "dome", "spike", "ram", "flat"):
        r = 0.2 * u
        S.round(lathe_at([(r, 0.0), (r * 0.92, 0.03 * u), (r * 0.6, 0.11 * u), (r * 0.2, 0.15 * u)], c, -Y, n=10), brass if style != "flat" else mat("iron_bright"))
        S.round(lathe_at([(r * 1.22, -0.004), (r * 1.2, 0.02 * u), (r * 0.98, 0.022 * u)], c, -Y, n=10), iron)
    if style in ("eye", "ram"):
        S.add_items(eye(c + Vector((0, -0.145 * u, 0)), 0.078 * u, lids=brass))
    elif style == "dome":
        S.round(g.ico(c + Vector((0, -0.15 * u, 0)), 0.03 * u, sub=0), field("stud", 3.0))
    elif style == "spike":
        tip = c + Vector((0, -0.62 * u, 0))
        S.round(g.cone(c + Vector((0, -0.1 * u, 0)), tip, 0.085 * u, n=6), mat("iron_bright"))
        S.round(g.ico(tip + Vector((0, 0.03 * u, 0)), 0.035 * u, sub=1, scale=(0.8, 1.6, 0.8)), field("tip", 3.4))
        for s in (1, -1):
            S.add_items(eye(S.P(s * 0.16 * u, zc + 0.26 * u, 0.006), 0.045 * u, lids=brass))
    elif style == "flat":
        S.round(lathe_at([(r * 1.5, 0.12 * u), (r * 1.55, 0.16 * u), (r * 1.45, 0.2 * u), (0.01, 0.2 * u)], c, -Y, n=16), mat("steel_glint"))
        for dx, dz, ln, ang in ((-0.1, 0.12, 0.3, 0.5), (0.06, -0.04, 0.42, 0.42), (-0.02, -0.16, 0.26, 0.56)):      # and the scuffs of what it walked into
            S.add(g.box(c + Vector((dx * u, -0.203 * u, dz * u)), (ln * u, 0.006, 0.014 * u), rot=(0, ang, 0)), mat("iron_dent"))
        for s in (1, -1):
            S.add_items(eye(S.P(s * 0.3 * u, zc + 0.34 * u, 0.006), 0.05 * u, lids=iron))
    if style == "ram":
        # two curled horns either side of the boss
        horn, ridge = mat("horn"), mat("horn_ridge")
        for s in (1, -1):
            base = c + Vector((s * 0.2 * u, -0.07 * u, 0.1 * u))
            pts = g.spiral(base + Vector((s * 0.2 * u, 0, -0.04 * u)), 0.22 * u, 0.1 * u, 1.15, s * 0.16 * u, n=12, axis=X * s, start=math.radians(100), drift=(0, -0.1 * u, 0))
            radii = [0.085 * u * (1 - 0.82 * (i / 12.0)) for i in range(13)]
            S.round(g.tube(pts, radii, n=6), horn)
            for i in range(2, 11, 2):
                S.round(g.tube([pts[i], pts[i] + (pts[i + 1] - pts[i]) * 0.3], [radii[i] * 1.14, radii[i] * 1.1], n=6), ridge)
        S.add(g.box(c + Vector((0, -0.05 * u, 0.3 * u)), (0.5 * u, 0.07 * u, 0.1 * u), rot=(math.radians(-12), 0, 0)), iron)
    if style == "hound":
        # a hound's muzzle of brass where the boss should be, the jaw a little dropped
        zm = zc + 0.06 * u
        yf = S.y(0, zm)
        k = u
        muzzle = g.loft([g.ring((0, yf + dy * k, zm + dz * k), rx * k, rz * k, n=6, u=X, v=Z, phase=math.pi / 6) for dy, dz, rx, rz in ((-0.02, 0.0, 0.19, 0.16), (-0.2, -0.02, 0.135, 0.115), (-0.38, -0.04, 0.1, 0.08), (-0.43, -0.045, 0.07, 0.06))])
        S.add(muzzle, brass)
        S.round(g.ico((0, yf - 0.44 * k, zm - 0.02 * k), 0.045 * k, sub=1, scale=(1.2, 0.8, 0.8)), mat("metal_dark"))
        jaw = g.loft([g.ring((0, yf + dy * k, zm + dz * k), rx * k, rz * k, n=6, u=X, v=Z, phase=math.pi / 6) for dy, dz, rx, rz in ((-0.02, -0.2, 0.16, 0.05), (-0.2, -0.2, 0.115, 0.04), (-0.36, -0.185, 0.075, 0.028))])
        S.add(jaw, brass)
        fangs = None
        for s in (1, -1):
            fangs = g.merge(fangs, g.cone((s * 0.07 * k, yf - 0.36 * k, zm - 0.1 * k), (s * 0.07 * k, yf - 0.37 * k, zm - 0.22 * k), 0.028 * k, n=4),
                            g.cone((s * 0.05 * k, yf - 0.3 * k, zm - 0.16 * k), (s * 0.05 * k, yf - 0.305 * k, zm - 0.08 * k), 0.02 * k, n=4),
                            g.cone((s * 0.11 * k, yf - 0.24 * k, zm - 0.115 * k), (s * 0.11 * k, yf - 0.245 * k, zm - 0.185 * k), 0.018 * k, n=4))
        S.add(fangs, mat("bone"))
        S.add(g.box((0, yf - 0.2 * k, zm - 0.14 * k), (0.15 * k, 0.3 * k, 0.025 * k)), field("mouth", 2.5))
        for s in (1, -1):
            S.add_items(eye(S.P(s * 0.2 * k, zm + 0.27 * k, 0.006), 0.062 * k, lids=brass))
            S.add(g.blade(S.P(s * 0.07 * k, zm + 0.31 * k, 0.012), S.P(s * 0.34 * k, zm + 0.41 * k, 0.012), 0.11 * k, normal=(0, -1, 0.5), belly=0.45), brass)
    if style == "ring":
        # a ring handle nobody uses
        top = S.P(0, zc + 0.12 * u, 0.02)
        S.round(lathe_at([(0.07 * u, 0.0), (0.05 * u, 0.03 * u), (0.02 * u, 0.045 * u)], top, -Y, n=8), iron)
        S.round(ringtube(top + Vector((0, -0.045 * u, -0.17 * u)), 0.15 * u, 0.17 * u, 0.026 * u, n=14, u=X, v=Z, sides=5), iron)
        for s in (1, -1):
            S.add_items(eye(S.P(s * 0.13 * u, zc + 0.36 * u, 0.004), 0.04 * u, lids=mat("stone_light")))


# --- what a shield has grown or been given ------------------------------------------------

def _dents(S, n, seed=1.0, hammered=False):
    k = 0
    for i in range(n * 4):
        x = (S.w / 2) * 0.82 * math.sin(i * 2.4 * seed + 0.7)
        z = S.zc + (S.h / 2) * 0.82 * math.sin(i * 1.7 * seed + 2.1)
        if not S.inside(x, z, 0.1 * S.u) or (abs(x) < 0.24 * S.u and abs(z - S.zc) < 0.24 * S.u):
            continue
        r = ((0.05 + 0.03 * math.sin(i * 3.1)) * S.u + 0.01) * (1.5 if hammered else 1.0)
        S.disc(x, z, r, mat("iron_dent"), proud=-0.004, squash=0.2)
        if hammered:        # each one hammered back out, and still showing
            S.disc(x + 0.12 * r, z + 0.12 * r, r * 0.62, mat("iron_bright"), proud=0.006, squash=0.3, sub=1)
        k += 1
        if k >= n:
            break


def grow_shield(S, style, size, spec):
    w, h, hw, zc, u = S.w, S.h, S.w / 2, S.zc, S.u
    iron, brass, lea, wood, bone = mat("metal_iron"), mat("metal_brass"), mat("leather"), mat("wood"), mat("bone")
    if style == "dents":
        _dents(S, int(3 * size), seed=1.0)
    elif style == "hammered":
        _dents(S, int(7 * size), seed=1.37, hammered=True)
    elif style == "patches":       # plates riveted over what broke
        for i, (fx, fz, a) in enumerate(((0.52, 0.72, 12), (-0.5, 0.3, -8), (0.3, -0.62, 20))[: max(1, int(round(3 * size)))]):
            x, z = fx * hw, zc + fz * h / 2
            S.add(g.box(S.P(x, z, 0.014), (0.26 * u, 0.02, 0.2 * u), rot=(0, math.radians(a), 0)), mat("metal_iron_light"))
            for dx, dz in ((-0.1, -0.07), (0.1, -0.07), (-0.1, 0.07), (0.1, 0.07)):
                S.stud(x + dx * u, z + dz * u, 0.014, iron)
        S.line((-hw * 0.7, zc + 0.36 * h), (hw * 0.2, zc + 0.44 * h), 0.05 * u, iron, proud=0.012)
    elif style == "notch":         # a bite out of its top corner, and the rim bent round it
        x, z = hw * 0.72, h - 0.1 * h
        S.round(g.ico(S.P(x, z, 0.0) + Vector((0, S.thick / 2, 0)), 0.16 * u * size, sub=1, scale=(1, 0.5, 1)), mat("soot"))
    elif style == "teeth":         # the rim grown teeth, all the way round
        n = len(S.out)
        cx, cz = S.c
        step = max(1, n // int(18 * size))
        for i in range(0, n, step):
            x, z = S.out[i]
            d = Vector((x - cx, 0, z - cz)).normalized()
            base = S.P(x, z, 0.0) + Vector((0, S.thick / 2, 0))
            S.round(g.cone(base, base + d * (0.07 * u) + Vector((0, -0.16 * u, 0)), 0.035 * u, n=4), bone)
    elif style == "jaws":          # it holds them a little open: the board split across, a mouth between
        gap = 0.07 * h * size
        zj = zc - 0.02 * h
        hwj = S.half(zj) * 0.94
        S.hband(zj, -hwj, hwj, gap * 1.5, mat("maw"), proud=0.01, thick=0.03)
        S.hband(zj, -hwj * 0.9, hwj * 0.9, gap * 0.5, field("mouth", 2.6), proud=0.022, thick=0.02)
        n = max(5, int(hwj * 2 / (0.13 * u)))
        for i in range(n + 1):
            x = -hwj * 0.92 + 2 * hwj * 0.92 * i / n
            for sgn in (1, -1):
                b0 = S.P(x + (0.03 * u if sgn < 0 else 0.0), zj + sgn * gap * 0.75, 0.03)
                S.round(g.cone(b0, b0 + Vector((0, -0.05 * u, -sgn * gap * 0.95)), 0.04 * u, n=4), bone)
        for s in (1, -1):
            S.add_items(eye(S.P(s * 0.26 * hw, zj + 0.2 * h, 0.006), 0.06 * u, lids=iron))
    elif style == "strap":         # a long strap to carry it by, a long way out
        pts = [S.B(hw * 0.88 * math.cos(math.radians(a)), zc + 0.16 * h + 0.92 * h * math.sin(math.radians(a)), 0.03 + 0.08 * math.sin(math.radians(a))) for a in range(180, -1, -20)]
        S.add(strap(pts, 0.1 * u + 0.02, 0.016, up=Y), lea)
        S.round(g.ico(pts[len(pts) // 2] + Vector((0, 0, -0.02)), 0.05 * u, sub=0, scale=(1.4, 0.6, 0.7)), brass)
        S.round(g.tube([S.B(-hw * 0.5, zc - 0.3 * h, 0.03), S.B(0, zc - 0.36 * h, 0.09), S.B(hw * 0.5, zc - 0.3 * h, 0.03)], [0.07 * u, 0.085 * u, 0.07 * u], n=7), mat("cloth_wool"))
    elif style == "worn":          # a rim worn smooth and bright by one hand
        cx, cz = S.c
        pts = [S.P(cx + (x - cx) * 1.0, cz + (z - cz) * 1.0, 0.004) + Vector((0, S.thick / 2, 0)) for x, z in S.out if x > hw * 0.25 and z > zc * 0.7]
        if len(pts) > 2:
            S.round(g.tube(pts, [S.thick / 2 + 0.022] * len(pts), n=5), mat("steel_glint"))
    elif style == "spine":         # an iron spine down its middle
        S.vband(0, 0.03 * h, h * 0.97, 0.09 * u, iron, proud=0.014, thick=0.03)
    elif style == "bars":          # iron from the boss to the rim
        for a in range(8):
            ang = math.radians(22.5 + 45 * a)
            x1, z1 = 0.45 * w * math.cos(ang), zc + 0.45 * h * math.sin(ang)
            while not S.inside(x1, z1, 0.03) and (abs(x1) > 0.05 or abs(z1 - zc) > 0.05):
                x1, z1 = x1 * 0.93, zc + (z1 - zc) * 0.93
            S.line((0.2 * u * math.cos(ang), zc + 0.2 * u * math.sin(ang)), (x1, z1), 0.05 * u, iron, proud=0.012)
    elif style == "brow":          # a lowered brow of horn along its top
        z = h * 0.9
        hwz = S.half(z)
        for s in (1, -1):
            S.add(g.tongue([S.P(s * 0.03, z, 0.03), S.P(s * hwz * 0.6, z + 0.06 * u, 0.07), S.P(s * (hwz + 0.14 * u), z - 0.02 * u, 0.02)], [0.16 * u, 0.2 * u, 0.05 * u], thick=0.5, normal=(0, -1, 0.5)), mat("horn"))
    elif style == "footbar":       # a ram's foot of iron along its bottom, for walking into things
        S.add(g.box(S.P(0, 0.05 * h, 0.04), (S.half(0.08 * h) * 1.7, 0.12 * u, 0.1 * h)), iron)
    elif style == "frame":         # a mirror's frame, with a finial above and below
        S.round(lathe_at([(0.05 * u, 0.0), (0.09 * u, 0.07 * u), (0.03 * u, 0.15 * u), (0.055 * u, 0.2 * u), (0.0, 0.27 * u)], S.P(0, h - 0.01, 0) + Vector((0, S.thick / 2, 0)), Z, n=6), brass)
        S.round(lathe_at([(0.05 * u, 0.0), (0.08 * u, 0.05 * u), (0.0, 0.14 * u)], S.P(0, 0.01, 0) + Vector((0, S.thick / 2, 0)), -Z, n=6), brass)
        for s in (1, -1):
            S.round(g.ico(S.P(s * S.half(zc), zc, 0.0) + Vector((s * 0.03, S.thick / 2, 0)), 0.05 * u, sub=0), brass)
    elif style == "glints":        # the room in it, a little bent
        gl_ = mat("steel_glint")
        S.line((-0.24 * w, zc + 0.3 * h), (-0.02 * w, zc + 0.36 * h), 0.14 * u, gl_, proud=0.003, thick=0.006)
        S.line((-0.26 * w, zc + 0.14 * h), (-0.06 * w, zc + 0.19 * h), 0.07 * u, gl_, proud=0.003, thick=0.006)
        S.line((0.1 * w, zc - 0.3 * h), (0.26 * w, zc - 0.22 * h), 0.09 * u, gl_, proud=0.003, thick=0.006)
        S.add_items(eye(S.P(0, zc + 0.02 * h, 0.006), 0.07 * u, lids=mat("steel_polish")))
    elif style == "ripples":       # a ripple in the polish that moves when it is struck
        cx, cz = 0.08 * w, zc + 0.08 * h
        for k, r in enumerate((0.1, 0.2, 0.3, 0.4)):
            pts = []
            for i in range(17):
                a = 2 * math.pi * i / 16
                x, z = cx + r * w * math.cos(a) * size, cz + r * w * 1.15 * math.sin(a) * size
                if S.inside(x, z, 0.03):
                    pts.append(S.P(x, z, 0.008))
                elif len(pts) > 1:
                    S.round(g.tube(pts, [0.012 * u + 0.004] * len(pts), n=3, caps=False), field("ripple", 1.6) if k % 2 == 0 else mat("steel_glint"))
                    pts = []
                else:
                    pts = []
            if len(pts) > 1:
                S.round(g.tube(pts, [0.012 * u + 0.004] * len(pts), n=3, caps=False), field("ripple", 1.6) if k % 2 == 0 else mat("steel_glint"))
        S.round(g.ico(S.P(cx, cz, 0.01), 0.04 * u, sub=1, scale=(1, 0.4, 1)), field("ripple", 3.0))
    elif style == "tines":         # the blow, handed back: prongs curling out of one side
        for k in range(3):
            z = zc + (0.3 - 0.3 * k) * h
            x0 = S.half(z)
            pts = [S.P(x0, z, 0.0), S.P(x0 + 0.18 * u, z + 0.05 * u, 0.1 * u), S.P(x0 + 0.26 * u, z + 0.16 * u, 0.3 * u), S.P(x0 + 0.16 * u, z + 0.2 * u, 0.46 * u)]
            S.round(g.tube(pts, [0.04 * u, 0.035 * u, 0.026 * u, 0.006], n=5), mat("steel_polish"))
    elif style == "vision":        # the room in its face, a moment ahead
        f = field("vision", 1.5)
        S.add(g.box(S.P(0.02 * w, zc - 0.1 * h, 0.006), (0.2 * w, 0.012, 0.4 * h)), f)                       # a door, opening
        S.add(g.box(S.P(0.02 * w + 0.13 * w, zc - 0.1 * h, 0.01), (0.1 * w, 0.012, 0.36 * h), rot=(0, 0, math.radians(18))), mat("glass_dark"))
        for k in range(5):
            a = math.radians(40 + 25 * k)
            S.round(g.ico(S.P(0.34 * w * math.cos(a), zc + 0.36 * h * math.sin(a), 0.006), 0.022 * u, sub=0), f)
        S.add_items(eye(S.P(0, zc + 0.3 * h, 0.006), 0.085 * u, lids=brass))
    elif style == "hood":          # a cowl of dark cloth over its top
        z0 = h * 0.72
        pts = []
        for a in range(0, 181, 20):
            x = (S.half(z0) + 0.05) * math.cos(math.radians(a))
            pts.append((x, z0 + (h - z0 + 0.1 * u) * math.sin(math.radians(a))))
        rings = []
        for dy in (-0.14 * u, 0.0, S.thick + 0.05):
            rings.append([Vector((x, S.y(0, z0) * 0.3 + dy, z)) for x, z in pts])
        S.add(g.loft(rings, caps=False, closed=False), mat("cloth_dark"))
    elif style == "hinges":        # iron straps across its boards
        for fz in (0.24, 0.66):
            z = fz * h
            hwz = S.half(z)
            S.hband(z, -hwz * 0.98, hwz * 0.7, 0.07 * u, iron, proud=0.012)
            S.disc(hwz * 0.72, z, 0.055 * u, iron, proud=0.012, squash=0.3, sub=0)
            for fx in (-0.8, -0.3, 0.2):
                S.stud(hwz * fx, z, 0.014, mat("iron_bright"))
    elif style == "bar":           # a bar across its back
        z = zc + 0.02 * h
        hwz = S.half(z) + 0.14 * u * size
        S.add(g.box(S.B(0, z, 0.07), (hwz * 2, 0.09 * u, 0.12 * u)), mat("wood_dark"))
        for s in (1, -1):
            S.add(g.box(S.B(s * hwz * 0.62, z, 0.06), (0.06 * u, 0.14 * u, 0.2 * u)), iron)
            S.add(g.box(Vector((s * hwz, S.y(0, z) + S.thick + 0.07, z)), (0.05 * u, 0.11 * u, 0.15 * u)), iron)
    elif style == "peep":          # a grille it looks through
        z = 0.74 * h
        S.add(g.box(S.P(0, z, 0.004), (0.3 * u, 0.02, 0.17 * u)), mat("soot"))
        S.add_items(eye(S.P(0, z, 0.012), 0.055 * u, lids=None))
        for dx in (-0.1, 0.0, 0.1):
            S.vband(dx * u, z - 0.085 * u, z + 0.085 * u, 0.018 * u + 0.004, iron, proud=0.022, thick=0.012, n=1)
        S.add(g.box(S.P(0, z + 0.1 * u, 0.012), (0.36 * u, 0.03, 0.035 * u)), iron)
        S.add(g.box(S.P(0, z - 0.1 * u, 0.012), (0.36 * u, 0.03, 0.035 * u)), iron)
    elif style == "foot":          # a foot it stands on
        S.add(g.box(S.P(0, 0.015, 0.0) + Vector((0, 0.1 * u, 0)), (0.42 * w, 0.5 * u * size, 0.05 * u)), iron)
        S.round(g.tube([S.B(0, 0.42 * h, 0.0), Vector((0, S.y(0, 0) + 0.4 * u * size, 0.03))], [0.03 * u, 0.035 * u], n=5), mat("wood_dark"))
        for s in (1, -1):
            S.round(g.cone(Vector((s * 0.16 * w, S.y(0, 0) - 0.02, 0.03)), Vector((s * 0.16 * w, S.y(0, 0) - 0.02, -0.12 * u)), 0.04 * u, n=4), iron)
    elif style == "slit":          # a slit to see over, and what looks through it
        z = 0.86 * h
        hwz = S.half(z) * 0.62
        S.add(g.box(S.P(0, z, 0.004), (hwz * 2, 0.02, 0.06 * u)), mat("soot"))
        for s in (1, -1):
            S.add_items(eye(S.P(s * hwz * 0.45, z, 0.012), 0.04 * u, slit=False))
        S.hband(z + 0.06 * u, -hwz * 1.15, hwz * 1.15, 0.035 * u, iron, proud=0.014)
        S.hband(z - 0.06 * u, -hwz * 1.15, hwz * 1.15, 0.035 * u, iron, proud=0.014)
    elif style == "number":        # a number painted on it, as the roster counts it
        p = mat("paint_pale")
        z = 0.48 * h
        pr = (w / 5 * 0.54 + 0.012) if spec.get("face") == "timber" else 0.012       # proud of the posts, where it is a palisade
        S.vband(-0.16 * w, z - 0.09 * h, z + 0.09 * h, 0.06 * u, p, proud=pr, thick=0.008)
        S.vband(0.04 * w, z - 0.09 * h, z + 0.09 * h, 0.06 * u, p, proud=pr, thick=0.008)
        S.line((0.04 * w, z + 0.09 * h), (0.2 * w, z + 0.09 * h), 0.06 * u, p, proud=pr, thick=0.008, n=2)
        S.line((0.2 * w, z + 0.09 * h), (0.04 * w, z - 0.02 * h), 0.06 * u, p, proud=pr, thick=0.008, n=2)
    elif style == "merlons":       # battlements along its top
        n = 3
        for i in range(n):
            x = -hw * 0.72 + hw * 1.44 * i / (n - 1)
            S.add(g.box(S.P(x, h + 0.06 * u * size, 0.0) + Vector((0, S.thick / 2, 0)), (0.3 * hw, S.thick + 0.05, 0.18 * u * size)), mat("stone_light"))
        S.hband(h - 0.02, -hw * 0.98, hw * 0.98, 0.07 * u, mat("stone_plate"), proud=0.03, thick=0.05)
    elif style == "turrets":       # a turret at each top corner
        for s in (1, -1):
            c = S.P(s * hw * 0.98, h * 0.78, 0.0) + Vector((0, S.thick / 2, 0))
            S.round(lathe_at([(0.085 * u, 0.0), (0.085 * u, 0.36 * u), (0.11 * u, 0.4 * u), (0.11 * u, 0.46 * u)], c, Z, n=7), mat("stone_light"))
            S.round(lathe_at([(0.13 * u, 0.46 * u), (0.0, 0.7 * u)], c, Z, n=7), mat("slate") if "slate" in PALETTE else mat("stone_plate"))
            S.add(g.box(c + Vector((0, -0.085 * u, 0.3 * u)), (0.03 * u, 0.02, 0.08 * u)), field("window", 2.0))
    elif style == "wicket":        # a small door in its face that it opens to look through
        z0, ww, wh = 0.2 * h, 0.34 * w, 0.36 * h
        S.add(g.box(S.P(0, z0 + wh / 2, 0.004), (ww, 0.02, wh)), mat("soot"))
        S.add(g.box(S.P(0, z0 + wh * 0.62, 0.008), (ww * 0.7, 0.014, wh * 0.4)), field("within", 1.4))
        S.add_items(eye(S.P(0, z0 + wh * 0.62, 0.02), 0.06 * u, lids=None))
        door = g.box((ww / 2, 0, wh / 2), (ww, 0.03, wh))
        Mh = T(S.P(-ww / 2, z0, 0.02)) @ Rz(-62)
        S.add(moved(door, Mh), wood)
        S.add(moved(g.box((ww / 2, -0.02, wh * 0.7), (ww * 0.9, 0.012, 0.035)), Mh), iron)
        S.add(moved(g.box((ww / 2, -0.02, wh * 0.25), (ww * 0.9, 0.012, 0.035)), Mh), iron)
        S.add(g.box(S.P(0, z0 + wh + 0.03 * u, 0.012), (ww * 1.2, 0.04, 0.06 * u)), mat("stone_light"))
    elif style == "portcullis":    # iron teeth along its foot
        n = max(4, int(w / (0.16 * u)))
        for i in range(n + 1):
            x = -hw * 0.86 + hw * 1.72 * i / n
            b0 = S.P(x, 0.02, 0.0) + Vector((0, S.thick / 2, 0))
            S.round(g.cone(b0, b0 + Vector((0, 0, -0.16 * u * size)), 0.04 * u, n=4), iron)
    elif style == "lintel":        # a lintel over it, like the beam over a door
        z = h * 0.86
        S.add(g.box(S.P(0, z, 0.03) + Vector((0, S.thick / 2, 0)), (w * 1.24, S.thick + 0.12 * u, 0.13 * u)), mat("wood_dark"))
        for s in (1, -1):
            S.add(g.box(S.P(s * w * 0.56, z - 0.1 * u, 0.02) + Vector((0, S.thick / 2, 0)), (0.07 * u, S.thick + 0.1 * u, 0.14 * u)), iron)
    elif style == "sign":          # its partner's ward, alight on its face like a house mark
        f = field("ward", 2.4 * min(1.4, size))
        z = h * 0.6
        r = 0.2 * u * size
        S.round(g.tube([S.P(r * math.cos(2 * math.pi * i / 12), z + r * math.sin(2 * math.pi * i / 12), 0.012) for i in range(13)], 0.02 * u, n=4, caps=False), f)
        S.line((0, z - r * 1.5), (0, z + r * 1.5), 0.035 * u, f, proud=0.012, thick=0.012, n=3)
        S.line((-r * 0.75, z + r * 0.45), (r * 0.75, z + r * 0.45), 0.035 * u, f, proud=0.012, thick=0.012, n=2)
        S.line((-r * 0.5, z - r * 0.5), (r * 0.5, z - r * 0.5), 0.035 * u, f, proud=0.012, thick=0.012, n=2)
    elif style == "pane":          # the air a pace in front of it, standing thick
        f = field("air", 1.1)
        d = -0.42 * u * size
        pts = [Vector((x * 0.94, S.y(0, zc) + d, z * 0.94 + 0.02)) for x, z in S.out]
        pts.append(pts[0])
        S.round(g.tube(pts, [0.016 * u] * len(pts), n=4, caps=False), f)
        for fz in (0.3, 0.5, 0.7):
            hwz = S.half(fz * h) * 0.9
            S.round(g.tube([Vector((-hwz, S.y(0, zc) + d, fz * h)), Vector((hwz, S.y(0, zc) + d, fz * h))], [0.008 * u, 0.008 * u], n=3), f)
        for s in (1, -1):
            S.round(g.tube([S.P(s * hw * 0.8, 0.04, 0.0), Vector((s * hw * 0.8, S.y(0, zc) + d, 0.03))], [0.02 * u, 0.02 * u], n=4), iron)
    elif style == "feet":          # two feet to stand on when it is left in charge
        for s in (1, -1):
            S.round(g.tube([Vector((s * hw * 0.6, S.y(0, 0) - 0.3 * u, 0.0)), S.P(s * hw * 0.6, 0.06 * h, 0.0) + Vector((0, S.thick / 2, 0)), Vector((s * hw * 0.6, S.y(0, 0) + S.thick + 0.36 * u, 0.0))], [0.04 * u, 0.05 * u, 0.04 * u], n=5), iron)
    elif style == "crest":         # a crest across its face that was not there before the oath
        a, b = (-S.half(0.78 * h) * 0.9, 0.78 * h), (S.half(0.3 * h) * 0.9, 0.3 * h)
        S.line(a, b, 0.16 * u * size, brass, proud=0.012, thick=0.016, n=6)
        S.line((a[0], a[1] - 0.11 * u), (b[0], b[1] - 0.11 * u), 0.03 * u, mat("paint_red"), proud=0.016, thick=0.01, n=6)
        zs = 0.56 * h
        star = None
        for k in range(5):
            ang = math.pi / 2 + 2 * math.pi * k / 5
            star = g.merge(star, g.blade(S.P(0, zs, 0.03), S.P(0.19 * u * math.cos(ang), zs + 0.19 * u * math.sin(ang), 0.03), 0.09 * u, normal=(0, -1, 0)))
        S.add(star, field("oath", 2.2))
    elif style == "plumes":        # and a crest standing on its top
        for k, (dx, L) in enumerate(((-0.12, 0.3), (0.0, 0.42), (0.12, 0.3))):
            b0 = S.P(dx * u, h - 0.02, 0.0) + Vector((0, S.thick / 2, 0))
            S.add(g.blade(b0, b0 + Vector((dx * u * 1.6, 0.05 * u, L * u * size)), 0.14 * u, normal=(0, -1, 0), belly=0.5), mat("paint_red") if k != 1 else brass)
    elif style == "ribbons":       # the seals of it, hanging
        for s in (1, -1):
            b0 = S.P(s * 0.3 * w, 0.2 * h, 0.014)
            S.add(strap([b0, b0 + Vector((s * 0.02, -0.02, -0.16 * u)), b0 + Vector((s * 0.05, -0.01, -0.3 * u))], 0.06 * u, 0.008, up=Y), mat("paint_red"))
            S.round(g.ico(b0 + Vector((s * 0.05, -0.02, -0.33 * u)), 0.045 * u, sub=0, scale=(1, 0.4, 1)), mat("wax"))
    elif style == "panel":         # a panel cut into the stone
        S.plate(mat("stone_plate"), mat("stone_plate"), mat("stone_light"), rings=1, thick=0.012, scale=0.72, proud=0.008)
        S.vband(0, 0.2 * h, 0.8 * h, 0.035 * u, mat("stone_light"), proud=0.02, thick=0.012)
        S.hband(0.62 * h, -0.2 * w, 0.2 * w, 0.035 * u, mat("stone_light"), proud=0.02, thick=0.012, n=2)
    elif style == "moss":          # moss at its foot
        for i in range(7):
            x = -hw * 0.62 + hw * 1.24 * i / 6
            z = (0.05 + 0.04 * math.sin(i * 2.3)) * h
            if S.inside(x, z, 0.01):
                S.disc(x, z, (0.06 + 0.025 * math.sin(i * 1.3)) * u, mat("moss"), proud=0.004, squash=0.22, sub=1)
    elif style == "chains":        # it hangs: two chains to a bar over the hearth
        topz = h + 0.42 * u * size
        S.round(g.tube([Vector((-hw * 0.9, S.y(0, h) + S.thick / 2, topz)), Vector((hw * 0.9, S.y(0, h) + S.thick / 2, topz))], [0.03 * u, 0.03 * u], n=5), iron)
        for s in (1, -1):
            x = s * hw * 0.7
            for k in range(5):
                z = h + (topz - h) * (k + 0.5) / 5
                S.round(g.ico(Vector((x, S.y(x, h) + S.thick / 2, z)), 0.04 * u, sub=0, scale=(1.0, 0.5, 1.3) if k % 2 else (0.5, 1.0, 1.3)), iron)
    elif style == "soot":          # smoke-darkened on one side from hanging over the hearth
        edge = -0.06 * w
        left = [(x, z) for x, z in S.out if x <= edge] + [(edge, h * 0.02), (edge + 0.1 * w, h * 0.3), (edge - 0.04 * w, h * 0.55), (edge + 0.08 * w, h * 0.8), (edge, h * 0.98)]
        cx = -hw * 0.55
        left = sorted(left, key=lambda p: math.atan2(p[1] - zc, p[0] - cx))
        st = mat("soot")
        S.plate(st, st, st, rings=1, thick=0.004, out=left, c=(cx, zc), proud=0.006)
    elif style == "embers":        # the hearth's light along its lower edge
        f = field("ember", 2.4)
        S.hband(0.05 * h, -S.half(0.05 * h) * 0.9, S.half(0.05 * h) * 0.9, 0.03 * u, f, proud=0.014, thick=0.012)
        for i in range(5):
            x = -hw * 0.7 + hw * 1.4 * i / 4
            b0 = S.P(x, 0.06 * h, 0.012)
            S.add(g.blade(b0, b0 + Vector((0.02 * math.sin(i * 2.0), -0.01, (0.14 + 0.06 * math.sin(i * 1.7)) * u)), 0.06 * u, normal=(0, -1, 0)), f)
    elif style == "lattice":       # a gate's iron lattice
        nx = max(3, int(w / (0.22 * u)))
        for i in range(nx + 1):
            x = -hw * 0.82 + hw * 1.64 * i / nx
            top = h * 0.96
            while top > 0.1 and not S.inside(x, top, 0.03):
                top -= 0.05
            S.vband(x, 0.02, top, 0.035 * u, iron, proud=0.016, thick=0.022)
        for fz in (0.2, 0.42, 0.64):
            S.hband(fz * h, -S.half(fz * h) * 0.94, S.half(fz * h) * 0.94, 0.035 * u, iron, proud=0.022, thick=0.02)
    elif style == "eyes2":         # only a pair of eyes at head height
        for s in (1, -1):
            S.round(g.ico(S.P(s * 0.17 * w, 0.8 * h, 0.03), 0.07 * u * size, sub=1, scale=(1.3, 0.4, 0.75)), field("eyes", 4.2))
            S.round(g.ico(S.P(s * 0.17 * w, 0.8 * h, 0.05), 0.03 * u * size, sub=0, scale=(0.5, 0.5, 1.5)), mat("eye_dark"))
    elif style == "ribs":          # ribs like the fingers of a hand held over something
        for k in range(5):
            a = math.radians(-56 + 28 * k)
            x1, z1 = math.sin(a) * hw * 0.92, 0.12 * h + math.cos(a) * h * 0.82
            while not S.inside(x1, z1, 0.02):
                x1, z1 = x1 * 0.95, 0.12 * h + (z1 - 0.12 * h) * 0.95
            S.line((0, 0.12 * h), (x1, z1), 0.07 * u, wood, proud=0.014, thick=0.026, n=6)
            S.stud(x1, z1, 0.03 * u, brass)
    elif style in ("poles", "poles4"):     # poles to carry it high by: it rides above head height, like a roof
        spots = [(s * hw * 0.78, 0.5 * h) for s in (1, -1)] if style == "poles" else [(s * hw * 0.8, fz * h) for s in (1, -1) for fz in (0.14, 0.86)]
        tops = [S.M @ S.B(x, z, 0.0) for x, z in spots]
        ground = min(p.z for p in tops) - 1.25 * size
        for p in tops:
            foot = Vector((p.x, p.y, ground))
            S.round(g.tube([S.Mi @ p, S.Mi @ foot], [0.034 * u, 0.038 * u], n=6), mat("wood_dark"))
            S.round(g.ico(S.Mi @ p, 0.06 * u, sub=0), brass)
            S.round(g.tube([S.Mi @ foot, S.Mi @ (foot + Vector((0, 0, 0.08 * u)))], [0.05 * u, 0.045 * u], n=6), brass)
        if style == "poles4":      # and braced, so that it can be set down over people
            for a, b in ((0, 2), (1, 3)):
                pa, pb = tops[a] + Vector((0, 0, -0.5 * size)), tops[b] + Vector((0, 0, -0.5 * size))
                pa.z = pb.z = min(pa.z, pb.z)
                S.round(g.tube([S.Mi @ pa, S.Mi @ pb], [0.022 * u, 0.022 * u], n=5), mat("wood_dark"))
    elif style == "shingles":      # rows of shingle, like a roof
        rows = 4
        for rr in range(rows):
            z = h * (0.14 + 0.72 * rr / (rows - 1))
            hwz = S.half(z) * 0.94
            n = max(3, int(2 * hwz / (0.2 * u)))
            for i in range(n):
                x = -hwz + (2 * hwz) * (i + 0.5 + 0.5 * (rr % 2)) / (n + 0.5)
                if S.inside(x, z, 0.04):
                    S.add(g.box(S.P(x, z, 0.012 + 0.006 * rr), (2 * hwz / (n + 0.5) * 0.94, 0.018, h * 0.24), rot=(math.radians(-6), 0, 0)), mat("timber_grey") if (i + rr) % 3 else mat("timber_dark"))
    elif style == "flange":        # a wing of iron on the side the road is
        z0, z1 = 0.3 * h, 0.82 * h
        pts = [S.P(S.half(z0) * 0.96, z0, 0.0), S.P(S.half(zc) + 0.2 * u * size, zc, -0.08 * u), S.P(S.half(z1) * 0.96, z1, 0.0)]
        S.add(g.tongue(pts, [0.03, 0.24 * u * size, 0.03], thick=0.2, normal=(0, -1, 0)), iron)
    elif style == "eye_top":       # an eye high on it, that watches the road
        z = 0.78 * h
        S.round(lathe_at([(0.12 * u, 0.0), (0.1 * u, 0.03 * u), (0.05 * u, 0.05 * u)], S.P(0, z, 0.0), -Y, n=8), brass)
        S.add_items(eye(S.P(0, z, 0.05 * u), 0.075 * u * size, lids=brass))
    elif style == "window":        # a carriage door's window, and its handle, and its step
        z0, z1 = 0.56 * h, 0.9 * h
        S.add(g.box(S.P(0, (z0 + z1) / 2, 0.006), (w * 0.62, 0.02, z1 - z0)), mat("glass_dark"))
        S.hband(z0, -w * 0.33, w * 0.33, 0.04 * u, brass, proud=0.014, n=3)
        S.hband(z1, -w * 0.33, w * 0.33, 0.04 * u, brass, proud=0.014, n=3)
        for s in (1, -1):
            S.vband(s * w * 0.32, z0, z1, 0.04 * u, brass, proud=0.014, n=1)
        S.add(g.box(S.P(-0.1 * w, (z0 + z1) / 2 + 0.03, 0.012), (w * 0.3, 0.012, (z1 - z0) * 0.86)), mat("cloth_lining"))      # the curtain, half drawn
        S.round(g.tube([S.P(0.26 * w, 0.46 * h, 0.012), S.P(0.26 * w, 0.44 * h, 0.07 * u), S.P(0.26 * w, 0.38 * h, 0.07 * u), S.P(0.26 * w, 0.36 * h, 0.012)], [0.018 * u] * 4, n=5), brass)
        S.add(g.box(S.P(0, 0.03 * h, 0.1 * u), (w * 0.6, 0.2 * u, 0.03 * u)), iron)
        S.add_items(eye(S.P(-0.22 * w, 0.46 * h, 0.01), 0.05 * u * size, lids=brass))
    elif style == "cutwater":      # an edge of iron down its middle, to part the river
        S.vband(0, 0.01 * h, 0.99 * h, 0.06 * u, iron, proud=0.03, thick=0.07, n=8)
        for fz in (0.25, 0.5, 0.75):
            S.stud(0, fz * h, 0.03 * u, mat("iron_bright"))
    elif style == "waterline":     # a green line across its face at the height of the last high water
        z = 0.6 * h
        hwz = S.half(z) * 0.985
        S.hband(z, -hwz, hwz, 0.06 * u * size, mat("moss"), proud=0.01, thick=0.014, n=10)
        S.hband(z - 0.06 * u, -hwz, hwz, 0.02 * u, mat("paint_pale"), proud=0.01, thick=0.012, n=10)
        for i in range(10):          # weed, and what grows below the line
            x = -hw * 0.74 + hw * 1.48 * i / 9
            zz = (0.1 + 0.4 * abs(math.sin(i * 2.3))) * h
            if S.inside(x, zz, 0.02):
                S.disc(x, zz, 0.07 * u, mat("verdigris") if i % 2 else mat("weed"), proud=0.004, squash=0.2, sub=1)
        for s in (1, -1):
            b0 = S.P(s * S.half(0.2 * h) * 0.7, 0.2 * h, 0.01)
            S.add(g.tongue([b0, b0 + Vector((s * 0.04, -0.03, -0.14 * u)), b0 + Vector((s * 0.1, -0.02, -0.3 * u))], [0.05 * u, 0.04 * u, 0.01], thick=0.4, normal=(0, -1, 0)), mat("weed"))
    elif style == "mooring":       # rings to moor by
        for s in (1, -1):
            c = S.P(s * S.half(0.78 * h) * 0.6, 0.78 * h, 0.02)
            S.round(ringtube(c + Vector((0, -0.01, -0.06 * u)), 0.06 * u, 0.07 * u, 0.016 * u, n=10, u=X, v=Z, sides=4), iron)
    elif style == "ears":          # its top corners pricked like ears
        z = h * 0.97
        for s in (1, -1):
            x = s * (S.half(h * 0.9) - 0.1 * u)
            S.add(g.blade(S.P(x - s * 0.1 * u, z - 0.06 * u, 0.0) + Vector((0, S.thick / 2, 0)), S.P(x + s * 0.08 * u, z + 0.3 * u * size, 0.0) + Vector((0, S.thick / 2 + 0.03, 0)), 0.24 * u, normal=(0, -1, 0.2), belly=0.3), lea)
    elif style == "torn_ear":      # one ear notched by something years ago
        z = h * 0.97
        x = (S.half(h * 0.9) - 0.1 * u)
        S.round(g.ico(S.P(x + 0.06 * u, z + 0.2 * u, 0.0) + Vector((0, S.thick / 2, 0)), 0.07 * u, sub=0), mat("soot"))
    elif style == "ruff":          # a ruff of bristle round its rim
        n = len(S.out)
        cx, cz = S.c
        step = max(1, n // int(26 * min(1.3, size)))
        for i in range(0, n, step):
            x, z = S.out[i]
            d = Vector((x - cx, 0, z - cz)).normalized()
            base = S.P(x, z, 0.0) + Vector((0, S.thick / 2, 0)) - d * 0.02
            L = (0.2 + 0.07 * math.sin(i * 2.1)) * u * size
            S.add(g.blade(base, base + d * L + Vector((0, 0.06 * u, 0)), 0.1 * u, normal=(0, -1, 0), belly=0.3), mat("pelt_dark") if i % (2 * step) else mat("pelt_light"))
    elif style == "scars3":        # its scars come in sets
        sc = mat("scar_pale")
        for (fx, fz, a) in ((-0.4, 0.62, 28), (0.36, 0.3, -30), (0.2, 0.8, 18))[: max(1, int(round(3 * size)))]:
            for k in (-1, 0, 1):
                x0, z0 = fx * hw + k * 0.06 * u, fz * h
                dx, dz = math.sin(math.radians(a)) * 0.28 * u, -math.cos(math.radians(a)) * 0.28 * u
                if S.inside(x0, z0, 0.02) and S.inside(x0 + dx, z0 + dz, 0.02):
                    S.line((x0, z0), (x0 + dx, z0 + dz), 0.022 * u, sc, proud=0.01, thick=0.01, n=3)
    elif style == "tokens":        # what it has kept of each of them, hung along its foot
        n = 7
        for i in range(n):
            x = -hw * 0.6 + hw * 1.2 * i / (n - 1)
            z = 0.02
            while not S.inside(x, z + 0.02, 0.0) and z < h * 0.5:
                z += 0.03
            b0 = S.P(x, z, 0.0) + Vector((0, S.thick / 2, 0))
            S.round(g.cone(b0, b0 + Vector((0.01 * math.sin(i * 3.0), -0.01, -(0.13 + 0.05 * (i % 2)) * u)), 0.03 * u, n=4), bone if i % 3 else mat("claw"))
    elif style == "old":           # grey at the muzzle, and brows gone pale
        zm = zc + 0.06 * u
        for s in (1, -1):
            S.add(g.blade(S.P(s * 0.1 * u, zm + 0.36 * u, 0.02), S.P(s * 0.4 * u, zm + 0.44 * u, 0.02), 0.09 * u, normal=(0, -1, 0.4)), mat("paint_pale"))
        S.round(g.ico((0, S.y(0, zm) - 0.4 * u, zm - 0.0 * u), 0.085 * u, sub=1, scale=(1.3, 1.0, 0.7)), mat("metal_iron_light"))
    elif style == "lacing":        # a drum's lacing round its side
        n = 14
        r = hw
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 0.5) / n
            p0 = Vector((r * 1.01 * math.sin(a0), S.y(0, zc) + 0.0, zc - r * 1.01 * math.cos(a0)))
            p1 = Vector((r * 1.01 * math.sin(a1), S.y(0, zc) + S.thick, zc - r * 1.01 * math.cos(a1)))
            p2 = Vector((r * 1.01 * math.sin(2 * math.pi * (i + 1) / n), S.y(0, zc), zc - r * 1.01 * math.cos(2 * math.pi * (i + 1) / n)))
            S.round(g.tube([p0, p1, p2], [0.012 * u, 0.012 * u, 0.012 * u], n=3), mat("rope"))
        for dy in (0.0, S.thick):
            S.round(ringtube((0, S.y(0, zc) + dy, zc), r * 1.0, r * 1.0, 0.03 * u, n=22, u=X, v=Z, sides=4), mat("wood_dark"))
    elif style == "beaters":       # it has learned to strike itself
        for s in (1, -1):
            sh = Vector((s * hw * 0.92, S.y(0, zc) + S.thick / 2, zc + 0.3 * h))
            el = sh + Vector((s * 0.26 * u, -0.2 * u, 0.3 * u * size))
            hd = Vector((s * hw * 0.42, S.y(0, zc) - 0.2 * u, zc + 0.36 * h))
            S.round(g.tube([sh, el, hd], [0.03 * u, 0.026 * u, 0.022 * u], n=5), mat("wood_dark"))
            S.round(g.ico(hd, 0.085 * u, sub=1), lea)
            S.round(g.ico(sh, 0.05 * u, sub=0), brass)
    elif style == "boards":        # wide boards either side, to be always in the way
        for s in (1, -1):
            c = Vector((s * (hw + 0.3 * u * size), S.y(0, zc) + S.thick / 2 + 0.04, zc))
            S.add(g.box(c, (0.5 * u * size, S.thick * 0.8, h * 0.66), rot=(0, 0, math.radians(s * 16))), wood)
            S.add(g.box(c + Vector((0, -0.02, 0.2 * h)), (0.52 * u * size, S.thick, 0.05 * u), rot=(0, 0, math.radians(s * 16))), iron)
            S.add(g.box(c + Vector((0, -0.02, -0.2 * h)), (0.52 * u * size, S.thick, 0.05 * u), rot=(0, 0, math.radians(s * 16))), iron)
    elif style == "mouth":         # a mouth in the hide, to boom with
        S.round(g.ico(S.P(0, zc - 0.14 * h, 0.004), 0.13 * u * size, sub=1, scale=(1.3, 0.12, 0.8)), mat("maw"))
        S.round(g.ico(S.P(0, zc - 0.14 * h, 0.012), 0.07 * u * size, sub=1, scale=(1.3, 0.12, 0.7)), field("mouth", 2.2))
        for s in (1, -1):
            S.add_items(eye(S.P(s * 0.22 * w, zc + 0.16 * h, 0.006), 0.06 * u, lids=mat("hide_drum")))
    elif style == "seam":          # a seam of light down the middle, where the halves meet
        S.vband(0, 0.04 * h, 0.96 * h, 0.03 * u, field("pulse", 2.2), proud=0.01, thick=0.03, n=6)
    else:
        raise ValueError("a shield cannot grow: " + str(style))


def _posts(S, spec):
    """A section of palisade: posts side by side, pointed, bound with rope."""
    w, h, n = S.w, S.h, 5
    tg, td = mat("timber_grey"), mat("timber_dark")
    for i in range(n):
        x = -w / 2 + w * (i + 0.5) / n
        r = w / n * 0.54
        top = h * (0.9 + 0.1 * math.sin(i * 2.4 + 1.0))
        S.round(lathe_at([(r, 0.0), (r, top - r * 1.6), (0.0, top)], S.P(x, 0, 0.0) + Vector((0, S.thick, 0)), Z, n=6), tg if i % 2 else td)
    for fz in (0.26, 0.7):
        S.hband(fz * h, -w / 2 * 1.02, w / 2 * 1.02, 0.07 * S.u, mat("rope"), proud=w / n * 0.54 - S.thick + 0.012, thick=0.03, n=10)
    for s in (1, -1):
        S.add_items(eye(S.P(s * w / n, 0.82 * h, w / n * 0.5), 0.045 * S.u, slit=False))


def _tiles(S, spec, size):
    """Overlapping plates, like tiles, that spread when they are needed."""
    w, h, u = S.w, S.h, S.u
    rows, cols = 3, 5
    lea, brass, iron = mat("leather"), mat("metal_brass"), mat("metal_iron")
    for rr in range(rows):
        for cc in range(cols - (rr % 2)):
            fx = (cc + 0.5 + 0.5 * (rr % 2)) / cols - 0.5
            x = fx * w * (0.86 + 0.07 * rr)
            z = h * (0.16 + 0.34 * rr)
            tw, th = w / cols * 1.16, h * 0.42
            hexa = [(tw * 0.5 * math.sin(2 * math.pi * k / 6), th * 0.5 - th * 0.5 * math.cos(2 * math.pi * k / 6)) for k in range(6)]
            verts, faces = [], []
            proud = 0.02 + 0.03 * rr
            for dy in (0.0, 0.022):
                verts.append(S.P(x, z, proud) + Vector((0, dy, 0)))
                for (hx, hz) in hexa:
                    verts.append(S.P(x + hx, z - th / 2 + hz, proud) + Vector((0, dy, 0)))
            for o in (0, 7):
                for k in range(6):
                    faces.append((o, o + 1 + k, o + 1 + (k + 1) % 6))
            for k in range(6):
                faces.append((1 + k, 8 + k, 8 + (k + 1) % 6, 1 + (k + 1) % 6))
            S.solid((verts, faces), lambda ctr, nrm, rr=rr, cc=cc: (lea if (rr + cc) % 2 else mat("wood")) if nrm.y < -0.3 else (mat("wood_dark") if nrm.y > 0.3 else iron))
            S.round(g.ico(S.P(x, z, proud + 0.012), 0.035 * u, sub=0), brass)
    S.add_items(eye(S.P(0, h * 0.5, 0.11), 0.07 * u, lids=brass))


def _halves(S, spec, face):
    """Two halves, a hand apart: one takes what lands, the other is what it spared."""
    f, b, e = face
    hw = S.w / 2
    gap = 0.035 * S.u
    left = [(x, z) for x, z in S.out if x <= -gap] + [(-gap, S.h * 0.02), (-gap, S.h * 0.98)]
    right = [(x, z) for x, z in S.out if x >= gap] + [(gap, S.h * 0.98), (gap, S.h * 0.02)]

    def ordered(pts, cx):
        return sorted(pts, key=lambda p: math.atan2(p[1] - S.zc, p[0] - cx))
    S.plate(mat("metal_iron_light"), b, mat("metal_iron"), out=ordered(left, -hw * 0.5), c=(-hw * 0.5, S.zc))
    S.plate(f, b, e, out=ordered(right, hw * 0.5), c=(hw * 0.5, S.zc))
    for i in range(6):          # the dents of what it took for them
        x = -hw * (0.2 + 0.62 * abs(math.sin(i * 2.2)))
        z = S.h * (0.16 + 0.68 * abs(math.sin(i * 1.5 + 0.6)))
        if S.inside(x, z, 0.05):
            S.disc(x, z, 0.07 * S.u, mat("iron_dent"), proud=-0.002, squash=0.2)
    for k in range(4):          # and what holds the halves together
        z = S.h * (0.2 + 0.2 * k)
        S.add(g.box(S.P(0, z, 0.012), (0.2 * S.u, 0.02, 0.04 * S.u)), mat("metal_brass"))


def build_shield(form_id, level, spec, base):
    kit.reset()
    S = Shield(form_id, spec)
    face = _faces()[spec.get("face", "iron")]
    made = [s for s, _ in each(spec.get("grown"))]
    if "posts" in made:
        _posts(S, spec)
    elif "tiles" in made:
        _tiles(S, spec, 1.0)
    elif "halves" in made:
        _halves(S, spec, face)
    else:
        S.plate(*face)
    rim_style, rim_r = opt(spec.get("rim", "iron"), 0.0)
    if rim_style not in (None, "none") and not ({"posts", "tiles", "halves"} & set(made)):
        S.rim({"iron": mat("metal_iron"), "brass": mat("metal_brass"), "stone": mat("stone_light"), "timber": mat("timber_dark"), "black": mat("soot"), "leather": mat("leather"), "polish": mat("steel_glint")}[rim_style],
              r=(rim_r or None))
    if spec.get("face") in ("wood", "timber") and "posts" not in made:
        _planks(S, mat("wood_dark") if spec.get("face") == "wood" else mat("timber_dark"))
    blazon = spec.get("blazon", "chevron")
    if blazon and blazon != "none":
        _studs_and_blazon(S, blazon)
    for style, size in each(spec.get("grown")):
        if style not in ("posts", "tiles", "halves"):
            grow_shield(S, style, size, spec)
    b_style, b_size = opt(spec.get("boss", "eye"))
    if b_style:
        _boss(S, b_style, b_size)
    S.grip(z=(float(spec["grip"]) * S.h if spec.get("grip") else None))
    return finish(S, form_id, base, spec, M=S.M)


def register(builders):
    """The three lines of armor. The Gauntlet and the Coat are files of their own beside this
    one (armors_hand.py, armors_coat.py); they are loaded here, once this file is whole."""
    import armors_hand
    import armors_coat
    builders.update({"shield": build_shield, "gauntlet": armors_hand.build, "coat": armors_coat.build})
