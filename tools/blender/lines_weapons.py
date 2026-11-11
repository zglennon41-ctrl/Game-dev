"""WILDLINE genius lines, the weapons: the Blade, the Gun and the Bow (docs/genius-lines.md,
"The weapons"). Every form of these three lines is a different weapon to look at and to
hold. genius_lines.py loads this file (register()); what a form looks like is the `body` of
its node in data/genius-bases/<base>.json.

    python tools/blender/genius_lines.py blade
    python tools/blender/genius_lines.py gun gun-pocket-piece gun-law

A weapon genius is its own weapon (HANDOFF.md §9, "Three types of genius"), so each model is
built twice over in one file:

  - **As a weapon**, in the weapon kit's own frame and scale (tools/blender/weapon_kit.py:
    people are 2.4 tall, a unit is about 0.73 m; in Blender a blade runs along +Z from the
    hand with its true edge to +X and its flats to +-Y; a gun's barrel runs along -Y with its
    top at +Z; a bow's limbs run along +-Z with its back to -Y and its string at +Y; the
    origin is where the hand slot sits, at the thumb side of the fist). That frame is kept in
    the model as an empty named `grip`. `grip_off` is where the second hand goes (the lower
    grip of a long hilt, a gun's fore-end, the nock of a bowstring), in the same turn.
  - **As a body**, floating beside its partner the way its base always has: a blade hangs
    point-down (the wooden swords stand point-up, at the salute), a gun rides level with its
    muzzle to the front, a bow stands upright with its arrow of light to the front. The
    standing guns stand on their own legs.

To put one in a hand the game gives the model the inverse of `grip`'s transform under the
hand slot, at scale 1, and then treats it as it treats the weapon kit's own model of that
type (guns and bows take the same quarter turn the kit's take). It need not know which form
it is.

How large it floats: `ref_top` is set so that an Advancement or a Final, at the Form it is
earned at, floats at exactly the size it is in the hand (the weapon kit's units are the
game's), a Path a tenth larger and the Starter a third larger (they are small things and must
be seen); it grows from there as every genius does. `show` in a body makes one form larger
or smaller than that.

Everything is hard and keeps its planes (the weapon kit's look: bright ground edges, dark
fullers, turned brass, cut stocks); cloth, cord and smoke are shaded round. Light is only
ever a material named field_*.
"""
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as gk  # noqa: E402
import genius_relics as gr  # noqa: E402
import weapon_kit as wk  # noqa: E402

ROOT = gk.ROOT
HPI = math.pi / 2
STANDS = {1: 0.6, 2: 0.8, 3: 1.0, 4: 1.3}    # data/genius.json, size, by level
LARGER = {1: 1.35, 2: 1.1, 3: 1.0, 4: 1.0}   # how much larger than in the hand a form floats, by level

# What the weapon kit's palette did not have. Muted, a value apart; a metal says so in its
# exported name, or the game shades a blade as cloth.
wk.PALETTE.update({
    "oak": ((0.34, 0.23, 0.12), 0.85, 0.0), "oak_pale": ((0.56, 0.46, 0.31), 0.85, 0.0), "bark": ((0.09, 0.07, 0.05), 0.95, 0.0),
    "steel_grey": ((0.27, 0.28, 0.3), 0.75, 0.5), "night": ((0.012, 0.012, 0.02), 1.0, 0.0), "verdigris": ((0.17, 0.3, 0.23), 0.7, 0.3),
    "green_steel": ((0.17, 0.25, 0.15), 0.6, 0.6), "moss": ((0.12, 0.19, 0.08), 0.95, 0.0), "mud": ((0.17, 0.13, 0.085), 0.95, 0.0),
    "horn": ((0.1, 0.08, 0.065), 0.4, 0.0), "sinew": ((0.6, 0.5, 0.36), 0.7, 0.0), "ice": ((0.5, 0.6, 0.65), 0.15, 0.0),
    "copper": ((0.5, 0.24, 0.12), 0.4, 0.8), "rag": ((0.27, 0.24, 0.17), 0.95, 0.0), "crepe": ((0.03, 0.03, 0.04), 0.95, 0.0),
    "cord": ((0.33, 0.25, 0.16), 0.9, 0.0), "soot": ((0.045, 0.04, 0.04), 0.9, 0.0), "stone": ((0.3, 0.3, 0.32), 0.95, 0.0),
    "sand": ((0.4, 0.34, 0.25), 0.95, 0.0), "gut": ((0.62, 0.56, 0.42), 0.8, 0.0), "eye_lid": ((0.3, 0.19, 0.07), 0.5, 0.8),
    "tin": ((0.5, 0.5, 0.47), 0.5, 0.8), "gourd": ((0.5, 0.36, 0.16), 0.7, 0.0), "feather": ((0.45, 0.42, 0.36), 0.9, 0.0),
    "feather_dark": ((0.12, 0.1, 0.09), 0.9, 0.0), "cloth_green": ((0.14, 0.2, 0.13), 0.9, 0.0), "wax": ((0.72, 0.66, 0.5), 0.35, 0.0),
    "walnut": ((0.27, 0.16, 0.085), 0.85, 0.0), "iron_light": ((0.23, 0.23, 0.26), 0.45, 0.75),
    # marking regions (data/genius-looks.json: the game shows each in the coat's marking colour, or hides it in the coat's own)
    "mark_wrap": ((0.09, 0.05, 0.035), 0.75, 0.0), "mark_tips": ((0.1, 0.08, 0.065), 0.4, 0.0), "mark_inlay": ((0.27, 0.16, 0.085), 0.85, 0.0),
    "mark_blazon": ((0.23, 0.23, 0.26), 0.45, 0.75), "mark_band": ((0.12, 0.12, 0.14), 0.62, 0.7), "mark_stitch": ((0.2, 0.1, 0.06), 0.75, 0.0),
})
wk.EXPORT_NAME.update({
    "oak": "wood_oak", "oak_pale": "wood_oak_pale", "bark": "wood_bark", "steel_grey": "metal_steel_grey", "verdigris": "metal_verdigris",
    "green_steel": "metal_green_steel", "copper": "metal_copper", "tin": "metal_tin", "eye_lid": "metal_lid", "gourd": "wood_gourd",
    "stone": "stone_block", "sand": "stone_sandbag", "night": "night_blade", "crepe": "cloth_crepe", "rag": "cloth_rag", "cord": "cloth_cord",
    "gut": "cloth_gut", "mud": "cloth_mud", "moss": "cloth_moss", "soot": "cloth_soot", "ice": "ice", "sinew": "cloth_sinew",
    "feather_dark": "feather_dark", "cloth_green": "cloth_green", "wax": "cloth_wax", "walnut": "wood_walnut", "iron_light": "metal_iron_light",
})

# The partner's own coat (data/genius-looks.json, bodies): the materials the game recolours.
# A knife or a blade wears it on its grip (leather, the wrap its marking) and its brass; a
# wooden sword and a bow in their wood; a gun in its iron and its brass (the standing guns
# in their plate as well). Everything else here keeps the colour it was made.


def log(*a):
    print("[lines_weapons]", *a)


def _gl():
    """genius_lines, as it is already loaded (it loads this file, so this file must not load it)."""
    m = sys.modules.get("genius_lines")
    if m is None or not hasattr(m, "export_objects"):
        m = sys.modules.get("__main__")
        if m is None or not hasattr(m, "export_objects"):
            import genius_lines as m  # noqa: F811
    return m


def opt(v, default_size=1.0):
    """A slot's value as (style, size): "bar", ["bar", 1.3] or None."""
    if v is None or v is False:
        return None, 0.0
    if isinstance(v, (list, tuple)):
        return v[0], float(v[1]) if len(v) > 1 else default_size
    return v, default_size


def each(v):
    """A slot that may hold several: "rings", ["rings", 1.2], or [["rings", 1.2], "glow"]."""
    if v is None or v is False:
        return []
    if isinstance(v, str):
        return [(v, 1.0)]
    if len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], (int, float)):
        return [(v[0], float(v[1]))]
    return [opt(x) for x in v]


def _silhouette(base, form_id):
    """The silhouette a form stands under: its own, or the nearest one above it on its line
    (the starter's, where no form on the way names one), as the game reads it."""
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
    root = dict(base["settled"])
    root["paths"] = base["paths"]
    return walk(root, base["silhouette"]) or base["silhouette"]


_BODIES = None


def _art_size(sil):
    global _BODIES
    if _BODIES is None:
        with open(os.path.join(ROOT, "data", "genius-bodies.json")) as f:
            _BODIES = json.load(f)["silhouettes"]
    return float(_BODIES.get(sil, {}).get("artSize", 1.0))


def _ref(base, form_id, level, show=1.0):
    """Where ref_top goes, in the kit's units: the game stands the body so that this height is
    its stage's, which leaves the weapon floating `LARGER[level] * show` times life size."""
    return STANDS[level] * _art_size(_silhouette(base, form_id)) / (LARGER[level] * show)


# ======================================================================================
# Putting a weapon together: the kit's piece, what is alive on it, its pose, its sockets
# ======================================================================================

def _round(name):
    """A weapon-kit colour as the material of something shaded round (a stud, a bag, a lump)."""
    if name not in wk.PALETTE:
        return gk.mat(name)
    c, rough, metal = wk.PALETTE[name]
    return gk.mat(wk.EXPORT_NAME.get(name, name), c, rough, metal)


def _disc(c, r, n=5, facing=(0, -1, 0)):
    """A flat round face, looking the way it faces: a chamber's mouth, a bore."""
    u, v = g._frame(facing)
    c = V(c)
    return [c + u * (math.cos(2 * math.pi * k / n) * r) + v * (math.sin(2 * math.pi * k / n) * r) for k in range(n)], [tuple(range(n))]


class Weapon:
    """One weapon being built in the weapon kit's frame."""

    def __init__(self, name):
        wk.reset()
        self.name = name
        self.p = wk.Piece(name)
        self.hard = []          # [(geometry, material)] from the genius kit: eyes, lids, light
        self.soft = []          # the same, shaded round: cloth, cord, smoke
        self.wings = {}         # "wing_l" / "wing_r" -> ([(geometry, material)], pivot)
        self.marks = {}         # named places in the kit's frame, for sockets
        self.off = None         # where the second hand goes, in the kit's frame

    def light(self, geo, name="glow", strength=2.6):
        self.hard.append((geo, gk.field(name, strength)))

    def bead(self, mat, r, at, scale=(1, 1, 1), sub=1, rot=None):
        """A small round thing (a stud, a knee, a lump of mud), shaded round: twelve points
        where a faceted ball spends sixty."""
        self.soft.append((g.ico(at, r, sub=sub, scale=scale, rot=rot), _round(mat)))

    def eye(self, at, r, facing=(0, -1, 0), look="open", lids="metal_brass"):
        """Where it is alive: an eye of the field set in the thing, lidded in its own stuff."""
        lm = gk.mat(lids)
        if look == "closed":
            c, f = V(at), V(facing).normalized()
            side = f.cross(Z).normalized() if abs(f.dot(Z)) < 0.9 else X
            a, b = c - side * (r * 1.3), c + side * (r * 1.3)
            self.hard.append((g.tongue([a, c + f * (r * 0.55) - Z * (r * 0.15), b], [r * 0.2, r * 1.5, r * 0.2], thick=0.5, normal=f), lm))
            self.hard.append((g.tube([a + f * (r * 0.3), c + f * (r * 0.75) - Z * (r * 0.5), b + f * (r * 0.3)], r * 0.07, n=3), gk.mat("eye_dark")))
            return
        items = gr._eye(at, r * (0.82 if look == "old" else 1.0), facing=facing, lids=lm, slit=(look != "dark"))
        if look == "dark":
            # a lens gone dark as a pupil: the dark over the light, a thin ring of it left
            c, f = V(at), V(facing).normalized()
            items.append((g.ico(c + f * (r * 0.22), r * 0.8, sub=1, scale=(1.0, 1.0, 1.0)), gk.mat("eye_dark")))
        if look == "old":
            # heavy lids, and a brow over it
            c, f = V(at), V(facing).normalized()
            side = f.cross(Z).normalized() if abs(f.dot(Z)) < 0.9 else X
            items.append((g.tongue([c - side * (r * 1.4) + Z * (r * 0.9), c + Z * (r * 1.25) + f * (r * 0.6), c + side * (r * 1.4) + Z * (r * 0.9)], [r * 0.3, r * 0.9, r * 0.3], thick=0.6, normal=f + Z * 0.4), lm))
        self.hard += items

    def finish(self, F, ref, extra_sockets=None, mid=None):
        """Join it, pose it by F (the kit's frame to where it floats), and write its sockets:
        the usual ones of a thing with no rig, `grip`, `grip_off`, and ref_top through
        genius_lines.export_objects. Returns (objects, sockets, ref)."""
        objs = self.p.finish()
        if self.hard:
            objs.append(g.pieces(self.name + "_hard", self.hard))
        if self.soft:
            objs.append(g.pieces(self.name + "_soft", self.soft, smooth=True))
        ob = g.join(self.name, objs)
        ob.data.transform(F)
        ob.matrix_world = Matrix.Identity(4)
        ob.data.update()
        out = [ob]
        for wname, (items, pivot) in self.wings.items():
            w = g.pieces(wname, items)
            w.data.transform(F)
            w.matrix_world = Matrix.Identity(4)
            w.data.update()
            gk.set_origin(w, F @ V(pivot))
            w.name = wname
            out.append(w)
        pts = [v.co.copy() for o in out for v in o.data.vertices]
        lo = Vector((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
        hi = Vector((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
        M = {k: F @ V(v) for k, v in self.marks.items()}
        c = M.get("mid", (lo + hi) / 2) if mid is None else F @ V(mid)
        front = lo.y - 0.01
        half = max(abs(lo.x), abs(hi.x))
        table = {
            "socket_head": [(c.x, c.y, hi.z + 0.01)], "socket_eyes": [tuple(M.get("eye", Vector((c.x, front, c.z + 0.06))))],
            "socket_mouth": [tuple(M.get("mouth", Vector((c.x, front, c.z))))], "socket_grip": [tuple(M.get("hold", c))],
            "socket_throat": [tuple(M.get("throat", Vector((c.x, front, c.z - 0.06))))], "socket_light": [tuple(M.get("light", c))],
            "socket_back": [tuple(M.get("back", Vector((c.x, hi.y + 0.01, c.z + 0.04))))], "socket_body": [tuple(M.get("body", Vector((c.x, front, c.z - 0.1))))],
            "socket_tail": [tuple(M.get("tail", Vector((c.x, c.y, lo.z))))],
            "socket_arm_l": [tuple(M.get("arm_l", Vector((half, c.y, c.z))))], "socket_arm_r": [tuple(M.get("arm_r", Vector((-half, c.y, c.z))))],
            "socket_limb_fl": [(half * 0.6, front * 0.6, lo.z + (hi.z - lo.z) * 0.25)], "socket_limb_fr": [(-half * 0.6, front * 0.6, lo.z + (hi.z - lo.z) * 0.25)],
            "socket_keepsake": [tuple(M.get("keepsake", Vector((c.x, front, c.z - 0.14))))],
        }
        # a socket carries something of the size of the thing (the kit's parts are made for a body
        # 0.72 tall; a weapon is long, not large, so it is the root of its length that counts)
        k = max(0.9, min(1.3, math.sqrt(max(hi.z - lo.z, hi.y - lo.y) / gk.STAND)))
        size = Matrix.Diagonal((k, k, k))
        socks = gk._sockets({name: [at[0], size] for name, at in table.items()})
        grip = bpy.data.objects.new("grip", None)
        grip.empty_display_size = 0.05
        bpy.context.collection.objects.link(grip)
        grip.matrix_world = F
        socks["grip"] = grip
        if self.off is not None:
            off = bpy.data.objects.new("grip_off", None)
            off.empty_display_size = 0.05
            bpy.context.collection.objects.link(off)
            off.matrix_world = F @ Matrix.Translation(V(self.off))
            socks["grip_off"] = off
        socks.update(extra_sockets or {})
        return out, socks, ref


def _export(form_id, objects, sockets, ref):
    gl = _gl()
    path = os.path.join(gl.OUT, form_id + ".glb")
    tris = gl.export_objects(objects, sockets, path, ref=ref)
    kb = os.path.getsize(path) // 1024
    if kb > 80:
        log("OVER BUDGET: %s is %d KB (%d triangles)" % (form_id, kb, tris))
    return tris


# ======================================================================================
# The Blade
# ======================================================================================

STEEL = {
    "steel": ("steel", "steel_edge", "steel_dark"), "bright": ("steel_edge", "steel_edge", "steel"), "grey": ("steel_grey", "steel_grey", "steel_dark"),
    "night": ("night", "night", "night"), "oak": ("wood", "oak_pale", "wood"), "pale": ("oak_pale", "oak_pale", "oak"),
    "green": ("green_steel", "steel_edge", "moss"), "dark": ("steel_dark", "steel", "iron"), "hot": ("steel_dark", "field_glow", "iron"),
}
WRAPS = {"leather": ("leather", "mark_wrap"), "cord": ("cord", "leather_dark"), "wire": ("leather", "steel_dark"), "cloth": ("cloth", "steel_dark"),
         "bone": ("bone", "bone"), "wood": ("oak", "oak"), "worn": ("leather", "leather"), "red": ("cloth_red", "leather_dark"),
         "dark": ("leather_dark", "mark_wrap"), "green": ("cloth_green", "leather_dark"), "pale": ("oak_pale", "oak_pale"), "crepe": ("crepe", "leather_dark")}


def _slab(p, z0, L, spine, edge, thick, mats, stations=10, notch=None):
    """A single-edged blade along +Z from functions of f in [0, 1]: spine(f) and edge(f) are
    the x of its back and of its edge. Where they meet it comes to a point. notch = (count,
    depth, from, to): a ragged edge, a tooth to each."""
    mat, bright, dark = mats
    fs = [i / stations for i in range(stations + 1)]
    if notch:
        n, depth, f0, f1 = notch
        fs = sorted(set(fs + [f0 + (f1 - f0) * (k + 0.5) / n for k in range(n)] + [f0 + (f1 - f0) * k / n for k in range(n + 1)]))
    rings = []
    for f in fs:
        z = z0 + L * f
        sx, ex = spine(f), edge(f)
        if notch:
            n, depth, f0, f1 = notch
            if f0 < f < f1:
                u = (f - f0) / (f1 - f0) * n
                if abs(u - round(u)) < 1e-6:              # the bottom of a notch
                    ex -= depth
        w = ex - sx
        t = thick * (1 - 0.3 * f)
        if w < 1e-4:
            rings.append([Vector((sx, 0, z))] * 7)
            continue
        top = [(sx, t), (sx + w * 0.3, t), (sx + w * 0.72, t * 0.8), (ex, 0.0)]
        rings.append([Vector((x, y, z)) for x, y in top] + [Vector((x, -y, z)) for x, y in reversed(top[:-1])])
    p.strip_loft(rings, [mat, mat, bright, bright, mat, mat, dark], cap=mat)


def _board(p, z0, L, half, thick, mats, stations=9, fuller=True):
    """A two-edged blade from half(f), its half-width along its length (a board, a leaf, a bar)."""
    mat, bright, dark = mats
    rings = []
    for i in range(stations + 1):
        f = i / stations
        z = z0 + L * f
        w = half(f)
        t = thick * (1 - 0.3 * f)
        if w < 1e-4:
            rings.append([Vector((0, 0, z))] * 14)
            continue
        gt = t * (0.5 if fuller and 0.06 < f < 0.8 else 1.0)
        top = [(-w, 0.0), (-w * 0.72, t * 0.7), (-w * 0.3, t), (-w * 0.22, gt), (w * 0.22, gt), (w * 0.3, t), (w * 0.72, t * 0.7), (w, 0.0)]
        rings.append([Vector((x, y, z)) for x, y in top] + [Vector((x, -y, z)) for x, y in reversed(top[1:-1])])
    m = [bright, mat, dark, dark, dark, mat, bright]
    p.strip_loft(rings, m + m, cap=mat)


def _blade_shape(shape, W, curve):
    """spine(f), edge(f) for the single-edged shapes."""
    if shape == "knife":           # an ordinary knife: a straight back dropping to the point, a belly
        return (lambda f: -W / 2 + W * 0.3 * max(0.0, (f - 0.62) / 0.38) ** 2 - curve * f * f,
                lambda f: W / 2 - W * 0.7 * max(0.0, (f - 0.5) / 0.5) ** 1.7 - curve * f * f)
    if shape == "cleaver":         # heavy toward the point: it widens all the way, and is cut off short
        return (lambda f: -W / 2 - curve * f * f,
                lambda f: (-W / 2 + W * (1.0 + 1.25 * f) if f < 0.8 else -W / 2 + W * (1.0 + 1.25 * 0.8) * (1 - (f - 0.8) / 0.2)) - curve * f * f)
    if shape == "belly":           # a curved belly to the edge, like something made for one job
        return (lambda f: -W / 2 - curve * f * f + W * 0.5 * max(0.0, (f - 0.75) / 0.25) ** 2,
                lambda f: -W / 2 - curve * f * f + W * (0.75 + 0.95 * math.sin(math.pi * min(1.0, f * 1.02)) ** 0.8) * (1.0 if f < 0.7 else max(0.0, 1 - ((f - 0.7) / 0.3) ** 1.6)) + W * 0.5 * max(0.0, (f - 0.75) / 0.25) ** 2 * (1 if f >= 0.999 else 0))
    if shape == "hook":            # a brush-hook: broad, and its end comes round to the front in a beak
        return (lambda f: -W / 2 + W * 1.25 * max(0.0, (f - 0.72) / 0.28) ** 1.6,
                lambda f: (W / 2 + W * 0.35 * f if f < 0.78 else W / 2 + W * 0.35 * 0.78 + W * 0.75 * math.sin(math.pi * (f - 0.78) / 0.44)) if f < 0.999 else -W / 2 + W * 1.25)
    if shape == "bar":             # no point at all
        return (lambda f: -W / 2, lambda f: W / 2)
    if shape == "clip":            # a long straight back and a clipped point
        return (lambda f: -W / 2 - curve * f * f + (W * 0.55 * ((f - 0.8) / 0.2) if f > 0.8 else 0.0),
                lambda f: W / 2 - curve * f * f - (W * 0.45 * ((f - 0.86) / 0.14) ** 1.5 if f > 0.86 else 0.0))
    # "saber": the kit's own curved blade is used instead of this
    return (lambda f: -W / 2 - curve * f * f, lambda f: W / 2 - curve * f * f - W * max(0.0, (f - 0.8) / 0.2) ** 1.6)


def _blade_guard(w, style, size, z, metal="brass"):
    p = w.p
    if style in (None, "none"):
        wk.ferrule(p, z - 0.012, h=0.024, mat=metal)
        return 0.0
    if style == "bar":
        wk.quillons(p, z, 0.11 * size, mat=metal, r=0.014, droop=0.0)
    elif style == "droop":
        wk.quillons(p, z, 0.12 * size, mat=metal, r=0.015, droop=0.045 * size)
    elif style == "wide":          # a wide guard grown like a pair of shoulders
        h = 0.2 * size
        p.slab(metal, [(-h, z - 0.02), (h, z - 0.02), (h * 1.06, z + 0.012), (h * 0.62, z + 0.06), (-h * 0.62, z + 0.06), (-h * 1.06, z + 0.012)], 0.058, bevel=0.3)
        for sx in (-1, 1):
            p.sphere(metal, 0.03 * size, (sx * h * 1.04, 0, z - 0.004), sub=1)
            p.tube(metal, [(sx * h * 0.55, 0, z + 0.055), (sx * h * 0.8, 0, z + 0.12 * size), (sx * h * 0.7, 0, z + 0.2 * size)], [0.014, 0.011, 0.006], segs=5)
    elif style == "sail":          # shoulders, and a sail from them to the pommel: it is in the way before you move it
        h = 0.2 * size
        p.slab(metal, [(-h, z - 0.02), (h, z - 0.02), (h * 1.06, z + 0.012), (h * 0.62, z + 0.06), (-h * 0.62, z + 0.06), (-h * 1.06, z + 0.012)], 0.058, bevel=0.3)
        p.slab("steel", [(0.03, z - 0.02), (h * 1.02, z - 0.02), (h * 0.9, z - 0.1 * size), (0.05, z - 0.21 * size)], 0.012, bevel=0.2)
        p.slab("steel", [(-0.03, z - 0.02), (-h * 1.02, z - 0.02), (-h * 0.9, z - 0.1 * size), (-0.05, z - 0.21 * size)][::-1], 0.012, bevel=0.2)
        for sx in (-1, 1):
            p.sphere(metal, 0.03 * size, (sx * h * 1.04, 0, z - 0.004), sub=1)
            p.tube(metal, [(sx * h * 0.55, 0, z + 0.055), (sx * h * 0.8, 0, z + 0.12 * size), (sx * h * 0.7, 0, z + 0.2 * size)], [0.014, 0.011, 0.006], segs=5)
    elif style == "cup":           # a duellist's cup, its quillons and its bow
        k = size
        p.lathe("steel", [(0.022, z - 0.03), (0.07 * k, z - 0.022), (0.105 * k, z + 0.005), (0.112 * k, z + 0.04), (0.108 * k, z + 0.045), (0.1 * k, z + 0.01), (0.066 * k, z - 0.014), (0.022, z - 0.02)], segs=10)
        wk.quillons(p, z - 0.014, 0.19 * k, mat="steel", r=0.01, finial=0.014, block=(0.04, 0.03, 0.025))
    elif style == "shell":         # a shell on the knuckle side
        k = size
        rings = []
        for i in range(6):
            a = -0.5 + i * 0.36
            rings.append([Vector((0.02 + 0.1 * k * math.cos(b) * (0.5 + 0.5 * math.cos(a * 0.9)), 0.085 * k * math.sin(a), z - 0.02 + 0.1 * k * math.sin(b))) for b in (0.0, 0.6, 1.2)])
        p.loft(metal, rings)
        wk.quillons(p, z, 0.1 * k, mat=metal, r=0.012)
    elif style == "disc":          # a round guard
        k = size
        p.lathe(metal, [(0.03, z - 0.008), (0.075 * k, z - 0.005), (0.08 * k, z + 0.001), (0.075 * k, z + 0.007), (0.03, z + 0.01)], segs=10)
    elif style == "knuckle":       # a bar and a bow to the pommel
        wk.quillons(p, z, 0.1 * size, mat=metal, r=0.013)
    elif style == "ring":          # a bar with a ring to each flat
        wk.quillons(p, z, 0.12 * size, mat=metal, r=0.013, droop=0.02)
        for sy in (-1, 1):
            p.torus(metal, 0.04 * size, 0.008, (0, sy * 0.036 * size, z + 0.03), rot=(0, HPI, 0), segs=8, rings=3)
    elif style == "hook":          # prongs turned up the blade, to catch another
        wk.quillons(p, z, 0.1 * size, mat=metal, r=0.014)
        for sx in (-1, 1):
            p.tube(metal, [(sx * 0.1 * size, 0, z), (sx * 0.115 * size, 0, z + 0.07 * size), (sx * 0.085 * size, 0, z + 0.2 * size)], [0.013, 0.011, 0.005], segs=5)
    elif style == "wood":          # a practice sword's guard: a leather-faced block
        p.slab("oak", [(-0.07 * size, z - 0.014), (0.07 * size, z - 0.014), (0.062 * size, z + 0.014), (-0.062 * size, z + 0.014)], 0.07, bevel=0.3)
        p.box("leather_dark", (0.13 * size, 0.074, 0.008), (0, 0, z + 0.016))
    elif style == "block":         # a cleaver's bolster
        p.slab(metal, [(-0.05 * size, z - 0.02), (0.07 * size, z - 0.02), (0.085 * size, z + 0.02), (-0.05 * size, z + 0.02)], 0.05, bevel=0.3)
    elif style == "crescent":      # horns turned toward the point
        pts = [(0.17 * size * math.sin(a), 0, z + 0.11 * size * (1 - math.cos(a))) for a in [-1.25 + 2.5 * i / 8 for i in range(9)]]
        p.tube(metal, pts, [0.006, 0.012, 0.016, 0.018, 0.02, 0.018, 0.016, 0.012, 0.006], segs=5)
    return 0.11 * size


def _blade_pommel(w, style, size, z, metal="brass"):
    p = w.p
    r = 0.036 * size
    if style in ("scent", "cap", "ball", "ring"):
        wk.pommel(p, z, r, metal, style=style)
        return z - r * 2.0
    if style == "disc":            # a wheel
        p.lathe(metal, [(0.0, -0.016), (r * 0.7, -0.014), (r * 1.15, -0.006), (r * 1.15, 0.006), (r * 0.7, 0.014), (0.0, 0.016)], segs=10, loc=(0, 0, z - r * 1.0), rot=(HPI, 0, 0))
        return z - r * 2.15
    if style == "spike":
        p.lathe(metal, [(0.0, z - r * 3.2), (r * 0.5, z - r * 1.2), (r * 0.9, z - r * 0.4), (r * 0.62, z + 0.006)], segs=6)
        return z - r * 3.2
    if style == "knot":            # the wood's own knot
        p.sphere("oak", r * 1.1, (0, 0, z - r * 0.7), scale=(1.0, 0.9, 0.9), sub=1, jitter=0.12)
        return z - r * 1.8
    if style == "eye":             # a ball to hold an eye
        p.sphere(metal, r * 1.05, (0, 0, z - r * 0.9), scale=(1.0, 0.85, 0.95), sub=1)
        return z - r * 1.95
    wk.ferrule(p, z - 0.006, h=0.02, mat=metal)
    return z - 0.01


def build_blade(form_id, level, spec, base):
    """One form of the Blade, from its body."""
    w = Weapon(form_id)
    p = w.p
    pose = spec.get("pose", "down")
    Rp = {"up": Matrix.Identity(4), "slant": Matrix.Rotation(math.pi - 0.62, 4, "Y"), "cross": Matrix.Rotation(HPI, 4, "Y")}.get(pose, Matrix.Rotation(math.pi, 4, "Y"))
    dn = (Rp.to_3x3().transposed() @ Vector((0, 0, -1))).normalized()      # which way is down for it, in its own frame
    B = dict({"kind": "sword", "len": 0.8, "width": 0.03, "thick": 0.011, "curve": 0.0, "tip": 0.2, "taper": 0.8, "flare": 0.0, "fuller": True, "steel": "steel"}, **spec.get("blade", {}))
    H = dict({"len": 0.21, "wrap": "leather", "metal": "brass"}, **spec.get("hilt", {}))
    mats = STEEL[B["steel"]]
    metal = H["metal"]
    glen = float(H["len"])
    a, b = WRAPS[H["wrap"]]
    if H.get("grooved"):           # worn to the shape of a hand
        n = 8
        prof = [(wk.GRIP_R * (1.12 - 0.3 * abs(math.sin(math.pi * 4 * i / n))), -glen + (glen + 0.02) * i / n) for i in range(n + 1)]
        p.lathe([a if i % 2 == 0 else b for i in range(n)], prof, segs=8)
    else:
        wk.grip(p, -glen, 0.02, mat=a, band=b, wraps=max(3, int(round(glen / 0.045))), r=wk.GRIP_R * float(H.get("thick", 1.0)))
    gstyle, gsize = opt(spec.get("guard", "bar"))
    zg = 0.045
    _blade_guard(w, gstyle, gsize, zg, metal)
    if gstyle in ("knuckle", "cup"):
        wk.knuckle_bow(p, zg, -glen - 0.01, 0.12 * gsize, mat=("steel" if gstyle == "cup" else metal), r=0.009)
    pstyle, psize = opt(spec.get("pommel", "cap"))
    zend = _blade_pommel(w, pstyle, psize, -glen, metal)
    # the blade
    z0 = 0.066 if gstyle not in (None, "none") else 0.03
    L, W, T = float(B["len"]), float(B["width"]), float(B["thick"])
    kind = B["kind"]
    spine = edge = None
    estyle, esize = opt(spec.get("edge"))
    notch = None
    if estyle in ("notched", "old-notch"):
        n = int(round((7 if estyle == "notched" else 5) * max(1.0, L / 0.8)))
        notch = (n, W * (0.22 if estyle == "notched" else 0.42) * esize, 0.12, 0.84)
    if kind == "sword":
        p.edge_blade(z0, L, W, T, kind="sword", tip=B["tip"], taper=B["taper"], fuller=((0.05, 0.62) if B["fuller"] else None), flare=B["flare"], mat=mats[0], edge=mats[1], dark=mats[2])
        spine, edge = (lambda f: -W * (1 - (1 - B["taper"]) * f)), (lambda f: W * (1 - (1 - B["taper"]) * f))
    elif kind == "saber" and not notch:
        p.edge_blade(z0, L, W, T, kind="saber", curve=B["curve"], tip=B["tip"], taper=B["taper"], fuller=((0.04, 0.62) if B["fuller"] else None), mat=mats[0], edge=mats[1], dark=mats[2], x0=0.005)
        spine, edge = (lambda f: -W / 2 - B["curve"] * f * f), (lambda f: W / 2 - B["curve"] * f * f)
    elif kind == "board":
        style = B.get("point", "ogive")
        f0 = 1.0 - B["tip"] / L
        if style == "round":       # worn round from being planted
            half = lambda f: W * (1.0 if f < f0 else math.sqrt(max(0.0, 1 - ((f - f0) / (1 - f0)) ** 2)))  # noqa: E731
        elif style == "square":
            half = lambda f: W * (1.0 if f < 0.999 else 0.0)  # noqa: E731
        else:
            half = lambda f: W * (1 - (1 - B["taper"]) * min(1.0, f / f0)) * (1.0 if f < f0 else max(0.0, 1 - ((f - f0) / (1 - f0)) ** 1.6))  # noqa: E731
        _board(p, z0, L, half, T, mats, stations=12 if style == "round" else 9, fuller=B["fuller"])
        spine, edge = (lambda f: -half(min(f, 0.99))), (lambda f: half(min(f, 0.99)))
    else:
        spine, edge = _blade_shape(B.get("shape", kind), W, B["curve"])
        _slab(p, z0, L, spine, edge, T, mats, stations=10, notch=notch)
    at = lambda f, x=0.0: Vector((x, 0, z0 + L * f))  # noqa: E731
    mid_x = lambda f: (spine(f) + edge(f)) / 2  # noqa: E731
    face = T + 0.004
    # the edge
    if estyle == "old-notch":      # more notch than edge, and each notch bright
        n, depth, f0, f1 = notch
        for k in range(n + 1):
            f = f0 + (f1 - f0) * k / n
            w.light(g.ico((edge(f) - depth * 0.45, 0, z0 + L * f), depth * 0.6, sub=0, scale=(1.0, max(0.5, (T + 0.006) / (depth * 0.6)), 1.0)), "notch", 2.6)
    elif estyle == "light":        # its edge a line of the field
        pts = [Vector((edge(f) + 0.002, 0, z0 + L * f)) for f in (0.04, 0.3, 0.55, 0.78, 0.93)]
        w.light(g.tube(pts, 0.0045 * esize, n=3), "edge", 2.5)
    elif estyle == "temper":       # heat or frost on the steel, never the same twice
        pts = [Vector((edge(f) - W * 0.34 + W * 0.1 * math.sin(f * 23.0), 0, z0 + L * f)) for f in [0.06 + 0.84 * i / 12 for i in range(13)]]
        w.light(g.tube(pts[:7], [0.011 * esize] * 7, n=4, flat=1.9, up=Z), "temper", 2.6)
        w.hard.append((g.tube(pts[6:], [0.011 * esize] * 7, n=4, flat=1.9, up=Z), gk.mat("ice_pale")))
        fr = None
        for i, f in enumerate((0.62, 0.72, 0.82, 0.9)):
            b0 = Vector((spine(f), 0, z0 + L * f))
            fr = g.merge(fr, g.cone(b0, b0 + Vector((-0.05 - 0.02 * (i % 2), 0, 0.03)), 0.014, n=4))
        w.hard.append((fr, gk.mat("ice")))
    elif estyle == "blunt":        # an edge it keeps blunt: a line of the field where one would be
        pts = [Vector((edge(f) + 0.003, 0, z0 + L * f)) for f in (0.06, 0.4, 0.75, 0.94)]
        w.light(g.tube(pts, 0.0035, n=3), "edge", 1.6)
    # what is cut into it
    for cstyle, csize in each(spec.get("cut")):
        if cstyle == "tally":      # fine marks along the flat in two columns
            n = int(8 * csize)
            dark, lit = None, None
            for k in range(n):
                f = 0.1 + 0.5 * k / max(1, n - 1)
                wd = (edge(f) - spine(f))
                for col, sgn in ((0, -1), (1, 1)):
                    c = Vector((mid_x(f) + sgn * wd * 0.2, 0, z0 + L * f))
                    bx = g.box(c, (wd * 0.22, face * 2, 0.007), rot=(0, 0.5 if (k % 5 == 4) else 0.0, 0))
                    if col == 0:
                        dark = g.merge(dark, bx)
                    else:
                        lit = g.merge(lit, bx)
            w.hard.append((dark, gk.mat("metal_dark")))
            w.light(lit, "tally", 2.2)
        elif cstyle == "names":    # the names, cut small, from the guard to halfway up
            n = int(13 * csize)
            cuts = None
            for k in range(n):
                f = 0.07 + 0.45 * k / max(1, n - 1)
                wd = (edge(f) - spine(f))
                frac = 0.35 + 0.3 * abs(math.sin(k * 2.3))
                cuts = g.merge(cuts, g.box(Vector((mid_x(f) - wd * 0.3 + wd * frac * 0.5, 0, z0 + L * f)), (wd * frac, face * 2, 0.011)))
            w.light(cuts, "names", 2.0)
        elif cstyle == "line":     # a line of light up the flat that stops where it is looking
            f1 = 0.72
            w.light(g.box(Vector((mid_x(0.4), 0, z0 + L * (0.05 + f1) / 2)), (0.007, face * 2, L * (f1 - 0.05))), "sight", 2.6)
            w.light(g.ico(Vector((mid_x(f1), 0, z0 + L * f1)), 0.02 * csize, sub=0, scale=(1.0, face * 55, 1.3)), "sight", 3.0)
        elif cstyle == "core":     # a cold light at the root of the blade
            c = Vector((mid_x(0.05), 0, z0 + 0.06))
            w.light(g.ico(c, 0.022 * csize, sub=0, scale=(0.8, face * 60, 1.5)), "core", 3.0)
        elif cstyle == "plates":   # straps across it, riveted, as on a door
            for f in (0.16, 0.44, 0.72):
                wd = edge(f) - spine(f)
                p.box("iron", (wd + 0.016, T * 2 + 0.016, 0.05 * csize), (mid_x(f), 0, z0 + L * f))
                for sx in (-0.3, 0.3):
                    w.bead("brass", 0.012, (mid_x(f) + sx * wd, -(T + 0.01), z0 + L * f))
        elif cstyle == "bands":    # bound where it has split, and worn pale between
            for f in (0.22, 0.5, 0.74):
                wd = edge(f) - spine(f)
                p.box("cord", (wd + 0.014, T * 2 + 0.014, 0.04 * csize), (mid_x(f), 0, z0 + L * f))
        elif cstyle == "pulse":    # a pulse along the flat
            pts = []
            for i in range(11):
                f = 0.1 + 0.62 * i / 10
                dx = (0.0, 0.0, 0.35, -0.5, 0.2, 0.0, 0.0, 0.35, -0.5, 0.2, 0.0)[i] * (edge(f) - spine(f)) * 0.7
                pts.append(Vector((mid_x(f) + dx, 0, z0 + L * f)))
            w.light(g.tube(pts, [0.006 * csize] * len(pts), n=4, flat=face / (0.006 * csize) * 1.1, up=Z), "pulse", 2.4)
    # what rides its back
    for sstyle, ssize in each(spec.get("spine")):
        if sstyle == "rings":      # links along its spine that clink once for each beat
            n = int(round(5 * ssize * max(1.0, L / 0.9)))
            for k in range(n):
                f = 0.2 + 0.62 * k / max(1, n - 1)
                R = 0.034
                p.torus("brass" if k % 2 else "steel", R, 0.0065, (spine(f) - R * 0.62, 0, z0 + L * f - R * 0.3), rot=(HPI, 0, 0), segs=7, rings=3)
        elif sstyle == "oak":      # one strip of oak left along the back, kept
            pts = [Vector((spine(f) - 0.008, 0, z0 + L * f)) for f in (0.02, 0.3, 0.6, 0.82)]
            p.tube("wood", pts, [0.016, 0.016, 0.014, 0.008], segs=4)
            for f in (0.12, 0.45, 0.72):
                p.box("brass", (0.04, T * 2 + 0.014, 0.014), (spine(f) + 0.004, 0, z0 + L * f))
        elif sstyle == "glow":     # a soft light along the back edge, the side that faces friends
            pts = [Vector((spine(f) - 0.004, 0, z0 + L * f)) for f in (0.03, 0.3, 0.6, 0.86)]
            w.light(g.tube(pts, [0.011 * ssize, 0.011 * ssize, 0.009 * ssize, 0.004], n=4), "back", 2.0)
        elif sstyle == "hook":     # a hooked back
            f = 0.66
            x, z = spine(f), z0 + L * f
            p.prism(mats[0], [(x + 0.01, z - 0.05), (x - 0.11 * ssize, z + 0.02), (x - 0.15 * ssize, z - 0.07 * ssize), (x - 0.1 * ssize, z - 0.13 * ssize), (x - 0.085 * ssize, z - 0.06 * ssize), (x - 0.05, z - 0.04), (x + 0.01, z - 0.14)], T * 1.3)
        elif sstyle == "saw":      # teeth along the back
            for k in range(int(7 * ssize)):
                f = 0.2 + 0.5 * k / 6
                p.prism(mats[0], [(spine(f) + 0.004, z0 + L * f - 0.022), (spine(f) - 0.028, z0 + L * f), (spine(f) + 0.004, z0 + L * f + 0.022)], T * 1.2)
    # where it is alive
    estyle2, er = opt(spec.get("eye", "blade"))
    er *= 1.0 + 0.2 * (level - 1)
    look = spec.get("eyelook", "open")
    if estyle2 == "blade":
        f = 0.085 / L
        c = Vector((mid_x(f), -(T + 0.006), z0 + 0.085))
        w.eye(c, 0.021 * er, look=look, lids=("metal_iron_light" if B["steel"] not in ("oak", "pale") else "wood"))
        w.marks["eye"] = c + Vector((0, -0.02, 0))
    elif estyle2 == "guard":
        c = Vector((0, -0.034, zg + (0.015 if gstyle in ("wide", "sail") else 0.0)))
        if gstyle == "cup":
            c = Vector((0, -0.108 * gsize, zg + 0.022))
        elif gstyle == "disc":
            c = Vector((0, -0.05 * gsize - 0.012, zg + 0.012))
        w.eye(c, 0.024 * er, look=look, lids=("metal_iron_light" if metal in ("steel", "iron") else "metal_brass"))
        w.marks["eye"] = c + Vector((0, -0.02, 0))
        if spec.get("lens"):       # a glass over the eye, to read by
            w.hard.append((gr.ringtube(c + Vector((0, -0.016, 0)), 0.04 * er, 0.04 * er, 0.006, n=10, u=X, v=Z), gk.mat("metal_brass")))
            w.hard.append((g.tube([c + Vector((0.04 * er, -0.016, 0)), c + Vector((0.07 * er, 0.0, -0.02))], 0.005, n=3), gk.mat("metal_brass")))
    elif estyle2 == "pommel":
        c = Vector((0, -0.03 * psize, -glen - 0.036 * psize * 0.9))
        w.eye(c, 0.022 * er * psize, look=look)
        w.marks["eye"] = c + Vector((0, -0.02, 0))
    elif estyle2 == "knot":        # a knot in the wood, like an old eye
        f = 0.3
        c = Vector((mid_x(f), -(T + 0.004), z0 + L * f))
        w.hard.append((g.ico(c + Vector((0, 0.006, 0)), 0.034 * er, sub=1, scale=(1.0, 0.35, 1.25)), gk.mat("wood")))
        w.eye(c + Vector((0, -0.006, 0)), 0.017 * er, look="old", lids="wood")
        w.marks["eye"] = c + Vector((0, -0.02, 0))
    # what hangs from it
    for hstyle, hsize in each(spec.get("hang")):
        if hstyle == "tassel":     # a tie of cloth at the pommel
            c = Vector((0, 0, zend + 0.01)) + Vector((0, 0.02, 0))
            side = Vector((1, 0, 0)) if abs(dn.x) < 0.5 else Vector((0, 0, 1))
            tie = None
            for k, (sx, ln) in enumerate(((0.022, 0.2), (-0.018, 0.28), (0.004, 0.14))[: 2 + (hsize > 1.3)]):
                mid = c + side * sx + Vector((0, 0.03 + 0.012 * k, 0)) + dn * 0.03
                tie = g.merge(tie, g.tongue([c, mid, mid + dn * ln * hsize * 0.55 + side * sx * 1.4, mid + dn * ln * hsize + side * sx * 2.4], [0.035, 0.07, 0.062, 0.02], thick=0.14, normal=Y))
            tie = g.merge(tie, g.ico(c + dn * 0.004, 0.022, sub=1))
            cloth = spec.get("cloth", "cloth_rag")
            w.soft.append((tie, gk.mark("tie", "cord") if cloth == "tie" else gk.mat(cloth)))
        elif hstyle == "whetstone":  # a whetstone on a cord, for the voice it has
            c0 = Vector((-0.1, 0, zg))
            c1 = c0 + Vector((-0.04, -0.01, 0)) + dn * 0.16 * hsize
            w.soft.append((g.tube([c0, (c0 + c1) / 2 + Vector((-0.02, 0, 0)), c1], 0.005, n=3), gk.mat("cord")))
            w.hard.append((g.box(c1 + dn * 0.07, (0.05, 0.022, 0.13), rot=(0, 0.15, 0)), gk.mat("stone_plate")))
        elif hstyle == "sheath":   # a plain sheath, worn at the mouth, the catch always off
            cover = float(spec.get("sheathed", 0.8))
            s0, s1 = 1.0 - cover, 1.0
            ringsS = []
            for f in [s0 + (s1 - s0) * i / 5 for i in range(6)] + [1.03]:
                sx, ex = spine(min(f, 0.995)), edge(min(f, 0.995))
                wd = max(0.012, ex - sx) / 2 + 0.01
                cx = (sx + ex) / 2
                ringsS.append([Vector((cx + wd * math.cos(a), (T + 0.012) * math.sin(a), z0 + L * f)) for a in [2 * math.pi * k / 6 for k in range(6)]])
            p.loft("leather", ringsS)
            fm = s0
            sx, ex = spine(fm), edge(fm)
            p.loft("leather_dark", [[Vector(((sx + ex) / 2 + ((ex - sx) / 2 + 0.016) * math.cos(a), (T + 0.018) * math.sin(a), z0 + L * fm + dz)) for a in [2 * math.pi * k / 6 for k in range(6)]] for dz in (-0.006, 0.03)])
            # the catch, hanging open
            c0 = Vector((ex + 0.014, -(T + 0.012), z0 + L * fm + 0.012))
            c1 = c0 + Vector((0.05, -0.02, 0)) + dn * 0.03
            c2 = c0 + Vector((0.07, -0.02, 0)) + dn * 0.12
            w.soft.append((g.tongue([c0, c1, c2], [0.026, 0.026, 0.022], thick=0.25, normal=(0, -1, 0)), gk.mat("leather_dark")))
            w.hard.append((g.ico(c2 + Vector((0, -0.008, 0)), 0.012, sub=0), gk.mat("metal_brass")))
            # the frog: a loop to hang it by
            fb = min(0.95, fm + 0.2)
            w.soft.append((gr.strap([(mid_x(fb), T + 0.014, z0 + L * fb), (mid_x(fb), T + 0.05, z0 + L * fb - 0.03), (mid_x(fb), T + 0.055, z0 + L * fb - 0.1), (mid_x(fb), T + 0.016, z0 + L * fb - 0.08)], 0.04, 0.008, up=X), gk.mat("leather_dark")))
        elif hstyle == "wrap":     # a dark wrap it has never let you change
            f0, f1 = 0.02, 0.2 * hsize
            ringsW = []
            for f in (f0, (f0 + f1) / 2, f1):
                sx, ex = spine(f), edge(f)
                ringsW.append([Vector(((sx + ex) / 2 + ((ex - sx) / 2 + 0.006) * math.cos(a), (T + 0.008) * math.sin(a), z0 + L * f)) for a in [2 * math.pi * k / 6 for k in range(6)]])
            p.loft(spec.get("wrapmat", "crepe"), ringsW)
        elif hstyle == "smoke":    # edge-on it cannot be seen: it goes to shadow along its length
            for k, f in enumerate((0.25, 0.5, 0.72, 0.9)):
                b0 = Vector((spine(f), 0, z0 + L * f))
                s = (1 if k % 2 else -1)
                w.soft.append((g.tongue([b0, b0 + Vector((-0.05, s * 0.03, -0.04)) * hsize, b0 + Vector((-0.12, s * 0.05, -0.13)) * hsize, b0 + Vector((-0.14, s * 0.02, -0.26)) * hsize], [0.06, 0.055, 0.035, 0.008], thick=0.35, normal=Y), gk.mat("shade_edge")))
        elif hstyle == "endring":  # a ring at its far end too: it is held across, like a bar
            p.torus("iron", 0.06 * hsize, 0.012, (mid_x(0.99), 0, z0 + L + 0.05 * hsize), rot=(HPI, 0, 0), segs=8, rings=3)
            p.box("iron", (0.13, T * 2 + 0.02, 0.05), (mid_x(0.99), 0, z0 + L - 0.03))
        elif hstyle == "chain":    # a length of chain from the pommel
            c = Vector((0, 0.03, zend + 0.02))
            links = None
            for k in range(int(6 * hsize)):
                c = c + dn * 0.05 + Vector((0.012 * math.sin(k * 1.3), 0.006 if k < 2 else 0.0, 0))
                links = g.merge(links, g.ico(c, 0.024, sub=0, scale=(1.0, 0.45, 1.0) if k % 2 else (0.45, 1.0, 1.0)))
            w.hard.append((links, gk.mat("metal_iron")))
    # its pose, floating
    top = z0 + L
    gap = 0.08
    k_show = LARGER[level] * float(spec.get("show", 1.0))
    hip = max(gap, 1.15 / k_show - (top - zend))
    if pose == "up":
        F = Matrix.Translation((0, 0, -zend + hip))
    elif pose == "slant":          # at a slant, as if already halfway there
        low = min((Rp @ Vector((x, 0, z))).z for x, z in ((0, top), (-0.2, 0.05), (0.2, 0.05), (0, zend)))
        F = Matrix.Translation((-math.sin(0.62) * (top + zend) / 2, 0, -low + gap)) @ Rp
    elif pose == "cross":          # crosswise, never upright
        F = Matrix.Translation((-(top + zend) / 2, 0, 1.1 / k_show)) @ Rp
    elif pose == "planted":        # point-down, to the ground
        F = Matrix.Translation((0, 0, top)) @ Rp
    else:
        F = Matrix.Translation((0, 0, top + hip)) @ Rp
    w.marks.update({"hold": (0, 0, -glen / 2), "mouth": (0, -0.04, zg), "throat": (0, -(T + 0.02), z0 + 0.12), "light": (mid_x(0.5), -(T + 0.02), z0 + L * 0.5),
                    "back": (0, 0.05, zg), "body": (mid_x(0.35), -(T + 0.02), z0 + L * 0.35), "tail": (mid_x(0.98), 0, top),
                    "arm_l": (-0.12 * gsize - 0.01, 0, zg), "arm_r": (0.12 * gsize + 0.01, 0, zg), "keepsake": (0, -0.035, -glen * 0.85), "mid": (0, 0, z0 + L * 0.3)})
    if pose in ("up", "cross"):
        w.marks["arm_l"], w.marks["arm_r"] = w.marks["arm_r"], w.marks["arm_l"]
    if glen >= 0.36:
        w.off = (0, 0, -glen + 0.09)
    objs, socks, ref = w.finish(F, _ref(base, form_id, level, float(spec.get("show", 1.0))))
    _export(form_id, objs, socks, ref)


# ======================================================================================
# The Gun
# ======================================================================================

def _barrel(p, x, y0, L, r, z, mat="steel_dark", breech=0.25, swell=1.28, flare=1.0, glow=True, segs=8):
    """A barrel from y0 forward (-Y) at (x, z): the weapon kit's, anywhere across the gun."""
    rm = r * flare
    prof = [(r * swell, 0.0), (r * swell, L * breech), (r * 1.12, L * breech + 0.012), (r, L * breech + 0.03),
            (rm if flare != 1.0 else r * 0.92, L - 0.05), (rm * 1.2, L - 0.04), (rm * 1.2, L - 0.012), (rm, L)]
    p.lathe(mat, prof, segs=segs, loc=(x, y0, z), rot=(HPI, 0, 0))
    if glow:
        p.cone("field_glow", rm * 0.72, rm * 0.72, 0.012, (x, y0 - L + 0.004, z), rot=(HPI, 0, 0), segs=segs)


def _sleeve(p, mat, y0, y1, r, z, x=0.0, segs=8):
    """A band or a sleeve about the barrel from y0 forward to y1."""
    p.cone(mat, r, r, abs(y0 - y1), (x, max(y0, y1), z), rot=(HPI, 0, 0), segs=segs)


def _scope(w, y_back, y_front, z, r, look="open", rim="brass", hood=0.0, back_lens=True, x=0.0):
    """Its lens: a glass on two rings, the field in it. It is the gun's eye."""
    p = w.p
    p.cone(rim, r, r * 0.9, y_back - y_front, (x, y_back, z), rot=(HPI, 0, 0), segs=8)
    for y in (y_back - (y_back - y_front) * 0.22, y_back - (y_back - y_front) * 0.78):
        p.box("steel_dark", (0.014, 0.02, r + 0.03), (x, y, z - r * 0.5 - 0.015))
        _sleeve(p, "steel_dark", y + 0.008, y - 0.008, r * 1.12, z, x=x)
    c = Vector((x, y_front - 0.003, z))
    w.hard.append((g.ico(c, r * 0.84, sub=1, scale=(1.0, 0.35, 1.0)), gk.field("eyes", 3.6)))
    if look == "dark":         # gone dark as a pupil: a ring of light round the dark
        w.hard.append((g.ico(c + Vector((0, -r * 0.2, 0)), r * 0.62, sub=1, scale=(1.0, 0.35, 1.0)), gk.mat("eye_dark")))
    else:
        w.hard.append((g.ico(c + Vector((0, -r * 0.26, 0)), r * 0.3, sub=0, scale=(0.5, 0.4, 1.6)), gk.mat("eye_dark")))
    if hood:
        p.cone("steel_dark", r * 1.08, r * 1.3, hood, (x, y_front + 0.002, z), rot=(HPI, 0, 0), segs=8)
    if back_lens:
        w.hard.append((g.ico(Vector((x, y_back + 0.003, z)), r * 0.86, sub=1, scale=(1.0, 0.3, 1.0)), gk.field("eyes", 3.0)))
    w.marks["eye"] = c + Vector((0, -0.03, 0))


def _rifle_stock(p, Lb, mat, plate="brass", z=0.0, butt=1.0, fore=0.74):
    """The musket's stock, for a barrel of length Lb: the butt behind the hand, the fore-end
    under the barrel for `fore` of its length."""
    f = -0.12 - (Lb - 0.12) * fore
    b = butt
    wk.stock(p, [(0.5 * b, -0.2 * b + z), (0.52 * b, -0.02 + z), (0.3 * b, 0.05 + z), (0.16, 0.075 + z), (0.06, 0.1 + z), (f, 0.085 + z), (f - 0.02, 0.045 + z),
                 (-0.16, 0.03 + z), (-0.03, -0.01 + z), (0.1, -0.04 + z), (0.26 * b, -0.12 * b + z)], 0.06, mat=mat)
    p.slab(plate, [(0.515 * b, -0.21 * b + z), (0.535 * b, -0.015 + z), (0.505 * b, -0.02 + z), (0.49 * b, -0.2 * b + z)], 0.066, bevel=0.2, rot=(0, 0, HPI))
    p.slab("mark_inlay", [(0.2 * b, -0.02 * b + z), (0.42 * b, -0.06 * b + z), (0.43 * b, -0.1 * b + z), (0.24 * b, -0.055 * b + z)], 0.066, bevel=0.1, rot=(0, 0, HPI))
    return f


def _cog(p, mat, c, r, axis="x", teeth=8):
    """A cog, seen from the side: a toothed disc."""
    pts = []
    for i in range(teeth):
        for da, rr in ((-0.3, 0.8), (-0.17, 1.12), (0.17, 1.12), (0.3, 0.8)):
            a = 2 * math.pi * (i + da) / teeth
            pts.append((math.cos(a) * r * rr, math.sin(a) * r * rr))
    p.prism(mat, pts, 0.016, loc=tuple(c), rot=(0, 0, HPI) if axis == "x" else (0, 0, 0))


def _lamp(w, at, s, bone=None, shade=False):
    """A small caged lamp hanging from `at`."""
    p = w.p
    at = Vector(at)
    c = at + Vector((0, 0, -s * 1.5))
    p.bar("iron", at, at + Vector((0, 0, -s * 0.6)), s * 0.07, segs=4)
    p.lathe("brass", [(s * 0.12, s * 0.95), (s * 0.5, s * 0.6), (s * 0.56, s * 0.52)], segs=6, loc=c)
    p.lathe("brass", [(s * 0.3, -s * 0.8), (s * 0.52, -s * 0.62)], segs=6, loc=c)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        q = c + Vector((math.cos(a) * s * 0.5, math.sin(a) * s * 0.5, 0))
        p.bar("iron", q + Vector((0, 0, -s * 0.62)), q + Vector((0, 0, s * 0.55)), s * 0.05, segs=4)
    w.light(g.ico(c, s * 0.36, sub=1, scale=(1, 1, 1.25)), "lamp", 3.4)
    if shade:                  # a flame seen through cloth
        for k in range(5):
            a = math.pi * (0.1 + 0.8 * k / 4)
            b0 = c + Vector((math.cos(a) * s * 0.75, 0.0 + math.sin(a) * s * 0.75, s * 0.9))
            w.soft.append((g.blade(b0, b0 + Vector((math.cos(a) * s * 0.25, math.sin(a) * s * 0.25, -s * 2.4)), s * 0.7, normal=Vector((math.cos(a), math.sin(a), 0.2)), belly=0.5), gk.mat("cloth_wool")))


def _legs(w, kind, size, y, zt, H):
    """What a gun stands or goes on, hanging from (0, y, zt) down to -H in the gun's frame."""
    p = w.p
    if kind == "bipod":        # long thin legs, folded under it
        for sx in (-1, 1):
            p.tube("steel_dark", [(sx * 0.02, y, zt), (sx * 0.035, y + 0.3 * size, zt - 0.05), (sx * 0.05, y + 0.62 * size, zt - 0.02)], [0.011, 0.009, 0.007], segs=4)
            p.box("iron", (0.03, 0.05, 0.016), (sx * 0.05, y + 0.64 * size, zt - 0.02))
        p.box("steel_dark", (0.06, 0.04, 0.03), (0, y, zt + 0.005))
    elif kind in ("stride", "level"):   # long legs, always in the middle of a stride
        hip = Vector((0, y, zt))
        p.box("brass", (0.12, 0.07, 0.05), hip)
        for sx, lead in ((-1, 1), (1, -1)):
            h = hip + Vector((sx * 0.06, 0, -0.01))
            if kind == "stride":
                knee = h + Vector((sx * 0.03, -lead * 0.2 * size, -H * 0.42))
                foot = h + Vector((sx * 0.04, -lead * 0.36 * size, -H))
            else:              # it carries itself level: a leg that folds like a spring
                knee = h + Vector((sx * 0.05, 0.22 * size, -H * 0.38))
                foot = h + Vector((sx * 0.06, -lead * 0.12 * size - 0.05, -H))
            p.tube("steel_dark", [h, knee, foot + Vector((0, 0.03, 0.05))], [0.02, 0.016, 0.011], segs=5)
            w.bead("brass", 0.028, knee)
            p.box("iron", (0.05, 0.14, 0.03), foot + Vector((0, -0.03, 0.015)))
            if kind == "level":
                p.tube("brass", [h + Vector((0, 0.02, -0.03)), knee + Vector((0, -0.07, 0.05))], 0.008, segs=3)
    elif kind == "wheels":     # small wheels, as on a tender
        for yy in (y - 0.2 * size, y + 0.2 * size):
            p.bar("iron", (-0.17, yy, zt - H + 0.07), (0.17, yy, zt - H + 0.07), 0.012, segs=4)
            for sx in (-1, 1):
                p.lathe(["iron", "steel", "iron"], [(0.02, -0.014), (0.075 * size, -0.014), (0.075 * size, 0.014), (0.02, 0.014)], segs=8, loc=(sx * 0.17, yy, zt - H + 0.07), rot=(0, HPI, 0))
        p.box("dark_wood", (0.3, 0.6 * size, 0.04), (0, y, zt - H + 0.16))
        for yy in (y - 0.14 * size, y + 0.14 * size):
            p.bar("iron", (0, yy, zt - H + 0.18), (0, y, zt), 0.014, segs=4)
        for sy in (-1, 1):
            p.box("iron", (0.07, 0.03, 0.05), (0, y + sy * 0.31 * size, zt - H + 0.17))
    elif kind == "tripod":     # legs and a spine: it stands like something on duty
        head = Vector((0, y, zt - H * 0.42))
        p.bar("iron", (0, y, zt), head, 0.03 * size, r2=0.036 * size, segs=6)
        p.lathe("brass", [(0.05 * size, -0.02), (0.06 * size, 0.0), (0.04 * size, 0.03)], segs=6, loc=head)
        p.lathe("brass", [(0.04 * size, -0.03), (0.055 * size, 0.0), (0.03 * size, 0.02)], segs=6, loc=(0, y, zt - 0.02))
        feet = []
        for a in (math.pi / 2, math.pi / 2 + 2.2, math.pi / 2 - 2.2):
            foot = Vector((math.cos(a) * H * 0.42, y + math.sin(a) * H * 0.42, zt - H))
            knee = head.lerp(foot, 0.5) + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.06 * H))
            p.tube("steel_dark", [head, knee, foot + Vector((0, 0, 0.03))], [0.026 * size, 0.022 * size, 0.018 * size], segs=5)
            w.bead("brass", 0.03 * size, knee)
            p.box("iron", (0.1 * size, 0.1 * size, 0.03), foot + Vector((0, 0, 0.015)))
            band_at = knee.lerp(foot, 0.5)
            p.cone("mark_band", 0.024 * size, 0.022 * size, 0.07, tuple(band_at), rot=wk.along(knee, foot), segs=5)
            feet.append(foot)
        return feet
    return []


def build_gun(form_id, level, spec, base):
    """One form of the Gun, from its body."""
    w = Weapon(form_id)
    p = w.p
    G = dict({"frame": "pocket", "barrel": 0.2, "bore": 0.02, "barrels": 1, "muzzle": 1.0, "butt": 1.0}, **spec.get("gun", {}))
    bm, trim = "iron", "brass"
    wood = G.get("wood", "walnut")
    frame = G["frame"]
    Lb, r = float(G["barrel"]), float(G["bore"])
    zb = 0.113                     # the barrel's height over the hand
    y0 = 0.09                      # the breech
    rear = 0.12                    # how far it reaches behind the hand
    low = -0.25                    # its lowest point, in its own frame
    balance = -0.2                 # where its weight is, along it
    lock = G.get("lock", "flint")
    # the frame: what the hand holds, and what carries the barrel
    if frame == "pocket":
        wk.pistol_grip(p, drop=0.17, rake=0.62, mat=wood, thick=0.052)
        wk.stock(p, [(0.07, 0.025), (0.08, 0.088), (0.0, 0.1), (-0.13, 0.085), (-0.14, 0.05), (-0.03, 0.0), (0.03, -0.015)], 0.05, mat=wood)
        y0, zb = 0.07, 0.108
        wk.trigger(p, y=-0.005, z=0.02, size=0.8)
        rear, low, balance = 0.2, -0.2, -0.02
    elif frame == "revolver":
        wk.pistol_grip(p, drop=0.22 * G["butt"], rake=0.48, mat=wood, thick=0.056)
        zb = 0.125
        cr = float(G.get("wheel", 0.05))
        cl = 0.125
        yc = -0.015
        # the frame: a strap over the wheel and one under it, the shield behind, the yoke the barrel is screwed into
        p.box(trim, (0.028, cl + 0.07, 0.014), (0, yc - cl / 2 - 0.005, zb + cr + 0.012))
        p.box(trim, (0.034, cl + 0.07, 0.016), (0, yc - cl / 2 - 0.005, zb - cr - 0.012))
        p.slab(trim, [(0.12, 0.0), (0.13, zb + cr + 0.02), (0.02, zb + cr + 0.02), (0.02, zb - cr - 0.02), (-0.04, -0.01), (0.04, -0.03)], 0.046, bevel=0.3, rot=(0, 0, HPI))
        p.box(trim, (0.042, 0.036, 2 * cr + 0.05), (0, yc - cl - 0.02, zb))
        n = int(G.get("chambers", 6))
        p.lathe(["steel_dark", "steel", "steel_dark"], [(cr * 0.5, 0.0), (cr, 0.006), (cr, cl - 0.006), (cr * 0.5, cl)], segs=n * 2, loc=(0, yc, zb), rot=(HPI, 0, 0))
        for k in range(n):     # its flutes
            a = 2 * math.pi * k / n
            p.box("steel_dark", (0.012, cl * 0.6, 0.012), (math.sin(a) * cr, yc - cl * 0.62, zb + math.cos(a) * cr), rot=(0, a, 0))
        closed = G.get("closed")
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            c = (math.sin(a) * cr * 0.62, yc - cl - 0.001, zb + math.cos(a) * cr * 0.62)
            if closed is not None and k == 0:   # one chamber is always closed. It was not always
                p.cone("iron", cr * 0.26, cr * 0.26, 0.012, c, rot=(HPI, 0, 0), segs=6)
                w.light(g.ico(Vector(c) + Vector((0, -0.012, 0)), cr * 0.12, sub=0), "seal", 2.2)
            else:
                w.hard.append((_disc(Vector(c) + Vector((0, -0.003, 0)), cr * 0.2, n=6), gk.mat("metal_dark")))
        y0 = yc - cl - 0.01
        wk.trigger(p, y=0.0, z=0.022)
        rear, low, balance = 0.24, -0.26, -0.12
    elif frame in ("rifle", "carbine"):
        fore = _rifle_stock(p, Lb, wood, plate=trim, butt=G["butt"], fore=(0.74 if frame == "rifle" else 0.5))
        y0, zb = 0.12, 0.112
        wk.trigger(p, y=-0.02, z=0.0, size=1.15)
        for k in range(3 if Lb > 1.0 else 2):
            yb = -0.3 - (abs(fore) - 0.36) * k / 2.0
            if yb > fore + 0.04:
                wk.band(p, yb, 0.095, 0.036, mat=trim)
        rear, low, balance = 0.54 * G["butt"], -0.22 * G["butt"], -0.42
        w.off = (0, -0.4 - 0.1 * Lb, 0.03)
    elif frame == "pole":          # a hand-cannon on a tiller
        p.tube(wood, [(0, 0.55, -0.1), (0, 0.2, 0.02), (0, -0.05, 0.07), (0, -0.3 * Lb, 0.07)], [0.028, 0.03, 0.034, 0.03], segs=6)
        p.lathe("iron", [(0.034, 0.0), (0.04, 0.02), (0.03, 0.04)], segs=6, loc=(0, 0.57, -0.105), rot=(-HPI + 0.3, 0, 0))
        y0, zb = 0.06, 0.125
        for yb in (-0.02, -0.2 * Lb, -0.32 * Lb):
            wk.band(p, yb, 0.1, r * 1.6 + 0.02, mat="iron")
        rear, low, balance = 0.6, -0.14, -0.3
        w.off = (0, -0.3, 0.05)
    elif frame == "wall":          # a wall-gun: a heavy barrel in a cradle, a spade to hold it by
        p.slab("iron", [(0.1, 0.04), (0.12, 0.17), (-0.5, 0.17), (-0.55, 0.06), (-0.1, 0.03)], 0.09, bevel=0.25, rot=(0, 0, HPI))
        p.tube("iron", [(0, 0.1, 0.1), (0, 0.2, 0.06), (0, 0.22, -0.04)], [0.02, 0.018, 0.016], segs=5)
        wk.grip(p, -0.16, 0.0, mat="leather_dark", band="iron", wraps=4)
        p.box("iron", (0.05, 0.05, 0.03), (0, 0.0, 0.01))
        p.tube("iron", [(0, 0.22, -0.04), (0, 0.12, -0.17), (0, 0.0, -0.165)], 0.014, segs=4)
        y0, zb = 0.1, 0.125
        rear, low, balance = 0.24, -0.2, -0.36
        w.off = (0, -0.3, 0.19)
    # the barrel, or barrels
    nb = int(G["barrels"])
    flare = float(G["muzzle"])
    for k in range(nb):
        x = (k - (nb - 1) / 2.0) * r * 2.3
        _barrel(p, x, y0, Lb, r, zb, mat=bm, breech=(0.22 if Lb > 0.6 else 0.3), flare=flare)
    ym = y0 - Lb                   # the muzzle
    if frame in ("pocket",):
        wk.band(p, ym + Lb * 0.45, zb - 0.008, r * 1.5, mat=trim)
    w.marks.update({"mouth": (0, ym - 0.02, zb), "hold": (0, 0.0, -0.08), "light": (0, y0 - Lb * 0.5, zb + r + 0.02), "back": (0, rear, zb - 0.05),
                    "tail": (0, rear, low * 0.5), "arm_l": (-0.05, 0.03, zb - 0.03), "arm_r": (0.05, 0.03, zb - 0.03), "throat": (0, ym + Lb * 0.3, zb - r - 0.03),
                    "body": (0, y0 - Lb * 0.3, zb - r - 0.04), "keepsake": (0, 0.03, -0.07), "mid": (0, balance, zb)})
    # the lock
    if lock == "flint":
        wk.flintlock(p, y=y0 - 0.06, z=zb - 0.03)
    elif lock == "hammer":         # a hammer worn smooth and bright
        hs = float(G.get("hammer", 1.0))
        p.tube("steel_edge", [(0, 0.1, zb - 0.02), (0, 0.13, zb + 0.05 * hs), (0, 0.09, zb + 0.1 * hs), (0, 0.13, zb + 0.15 * hs)], [0.016, 0.014, 0.012, 0.016], segs=5)
    elif lock == "cogs":           # an open nest of cogs, the field at the hub of the largest
        _cog(p, "iron", (0.04, y0 - 0.1, zb - 0.01), 0.05)
        _cog(p, "steel_dark", (0.045, y0 - 0.02, zb - 0.03), 0.034, teeth=6)
        w.light(g.ico((0.056, y0 - 0.1, zb - 0.01), 0.012, sub=0), "core", 4.0)
    elif lock == "thumb":          # a wheel it turns with a thumb of brass, idly
        p.tube("brass", [(0.03, 0.09, zb + 0.02), (0.045, 0.03, zb + 0.09), (0.03, -0.04, zb + 0.062)], [0.012, 0.011, 0.009], segs=4)
        w.bead("brass", 0.016, (0.03, -0.045, zb + 0.058))
        p.tube("steel_edge", [(0, 0.1, zb - 0.02), (0, 0.12, zb + 0.05), (0, 0.09, zb + 0.085)], [0.014, 0.012, 0.014], segs=4)
    # its lens: the one steady eye
    sight, ss = opt(spec.get("sight", "lens"))
    look = spec.get("eyelook", "open")
    top = zb + r * 1.3
    if sight == "lens":
        Ls = min(0.5, 0.12 + Lb * 0.25) * ss
        _scope(w, y0 - 0.0, y0 - Ls, top + 0.03 * ss + 0.012, 0.017 * (0.8 + 0.2 * ss), look=look)
    elif sight == "long":          # the far eye
        Ls = min(0.8, 0.2 + Lb * 0.3) * ss
        _scope(w, y0 + 0.04, y0 + 0.04 - Ls, top + 0.036, 0.022 * ss, look=look, hood=0.05)
    elif sight == "wide":          # one wide unblinking lens, set high
        zs = top + 0.2 * ss
        p.box("steel_dark", (0.03, 0.05, 0.2 * ss), (0, y0 - 0.12, top + 0.1 * ss))
        _scope(w, y0 - 0.02, y0 - 0.26, zs, 0.055 * ss, look=look, hood=0.04, back_lens=True)
    elif sight == "dark":          # a lens gone dark as a pupil
        Ls = min(0.7, 0.2 + Lb * 0.28)
        _scope(w, y0 + 0.04, y0 + 0.04 - Ls, top + 0.045 * ss, 0.034 * ss, look="dark", hood=0.09)
    elif sight == "two":           # two lenses, facing opposite ways
        zs = top + 0.16
        p.box("brass", (0.03, 0.04, 0.16), (0, y0 - 0.12, top + 0.08))
        _scope(w, y0 - 0.12, y0 - 0.32, zs, 0.034 * ss, look=look, back_lens=False)
        _scope(w, y0 - 0.12, y0 + 0.08, zs, 0.034 * ss, look=look, back_lens=False)
        w.marks["eye"] = Vector((0, y0 - 0.35, zs))
    # what it has grown or been given
    H = float(spec.get("height", 0.0))
    feet = []
    for style, s in each(spec.get("grows")):
        if style in ("bipod", "stride", "level", "wheels", "tripod"):
            yl = {"bipod": ym + Lb * 0.35, "tripod": -0.3}.get(style, balance)
            zt = {"bipod": zb - r - 0.035, "tripod": 0.04}.get(style, 0.0 if frame != "revolver" else -0.02)
            feet = _legs(w, style, s, yl, zt, H) or feet
            low = min(low, zt - H)
        elif style == "gimbal":    # it carries itself level however the ground goes
            c = (0, balance, zb - 0.01)
            p.torus("brass", 0.17 * s, 0.01, c, rot=(0, HPI, 0), segs=12, rings=3)
            p.torus("steel_dark", 0.2 * s, 0.008, c, rot=(HPI, 0, 0.5), segs=12, rings=3)
            p.cone("glass", 0.014, 0.014, 0.12, (0.04, balance + 0.06, zb + r + 0.03), rot=(HPI, 0, 0), segs=6)
            w.light(g.ico((0.04, balance + 0.01, zb + r + 0.03), 0.012, sub=0), "level", 3.0)
        elif style == "drum":      # a wheel of chambers a hand across; one is always closed. It was not always
            cr, cl = 0.13 * s, 0.2
            yc = y0 + 0.02
            n = 5
            p.lathe(["steel_dark", "steel", "steel_dark"], [(cr * 0.4, 0.0), (cr, 0.008), (cr, cl - 0.008), (cr * 0.4, cl)], segs=n * 2, loc=(0, yc, zb), rot=(HPI, 0, 0))
            for k in range(n):
                a = 2 * math.pi * (k + 0.5) / n
                c = (math.sin(a) * cr * 0.62, yc - cl - 0.001, zb + math.cos(a) * cr * 0.62)
                if k == 0:
                    p.cone("iron", cr * 0.27, cr * 0.27, 0.02, c, rot=(HPI, 0, 0), segs=6)
                    w.light(gr.ringtube(Vector(c) + Vector((0, -0.022, 0)), cr * 0.2, cr * 0.2, 0.006, n=8, u=X, v=Z), "seal", 2.4)
                    p.box("brass", (0.012, 0.01, cr * 0.5), (c[0], c[1] - 0.022, c[2]), rot=(0, 0.6, 0))
                else:
                    w.hard.append((_disc(Vector(c) + Vector((0, -0.003, 0)), cr * 0.2, n=6), gk.mat("metal_dark")))
        elif style == "mud":       # mud to the breech
            f0 = y0 - Lb * 0.3
            p.lathe("mud", [(r * 1.5, 0.0), (r * 1.9, 0.05), (r * 1.7, Lb * 0.3), (r * 1.4, Lb * 0.55), (r * 1.15, Lb * 0.64)], segs=6, loc=(0, f0, zb - 0.012), rot=(HPI, 0, 0))
            for k in range(5):
                w.bead("mud", 0.03 + 0.012 * (k % 3), (0.03 * math.sin(k * 2.0), 0.3 - 0.16 * k, 0.0 + 0.035 * math.cos(k * 1.3)), scale=(0.8, 1.6, 0.7))
        elif style == "round":     # a single round carried in the open, a name scratched on the case
            c = Vector((0.052, -0.12, zb - 0.02))
            p.lathe(["brass", "brass", "copper"], [(0.03 * s, 0.0), (0.032 * s, 0.01), (0.032 * s, 0.2 * s), (0.02 * s, 0.24 * s), (0.0, 0.3 * s)], segs=7, loc=tuple(c + Vector((0, 0.1 * s, 0))), rot=(HPI, 0, 0))
            for yy in (0.05, -0.07):
                p.box("steel_dark", (0.03, 0.02, 0.085 * s), tuple(c + Vector((-0.012, yy * s, 0))))
            marks = None
            for k in range(4):
                marks = g.merge(marks, g.box(c + Vector((0.033 * s, 0.07 * s - 0.035 * s * k, 0.005 * math.sin(k * 2.0))), (0.004, 0.022 * s, 0.006), rot=(0.3 * math.sin(k * 1.7), 0, 0)))
            w.light(marks, "name", 2.4)
        elif style == "rags":      # it is the colour of whatever is behind it
            mats = ("cloth_wool", "cloth_leaf", "cloth_dark")
            n = int(11 * s)
            for k in range(n):
                t = k / max(1, n - 1)
                y = rear * 0.8 - (rear * 0.8 - ym * 0.94) * t
                a = k * 2.4
                rr = 0.06 if y > -0.1 else 0.035
                b0 = Vector((math.cos(a) * rr * 0.5, y, zb - 0.01 + math.sin(a) * rr * 0.5 + (0.03 if y < -0.1 else -0.02)))
                tip = b0 + Vector((math.cos(a) * 0.1, 0.05 * math.sin(k * 1.3), -0.13 - 0.07 * (k % 3)))
                w.soft.append((g.blade(b0, tip, 0.1, normal=Vector((math.cos(a), 0.3, 0.4)), belly=0.45), gk.mat(mats[k % 3])))
            p.lathe("rag", [(r * 1.5, 0.0), (r * 1.7, Lb * 0.3), (r * 1.45, Lb * 0.6)], segs=6, loc=(0, y0 - Lb * 0.2, zb), rot=(HPI, 0, 0))
        elif style == "works":     # its works tick over: cogs, and a drum to feed them
            _cog(p, "brass", (0.045, y0 - 0.14, zb - 0.005), 0.06 * s, teeth=7)
            _cog(p, "brass_dark", (-0.045, y0 - 0.1, zb - 0.02), 0.05 * s, teeth=6)
            w.light(g.ico((0.06, y0 - 0.14, zb - 0.005), 0.014, sub=0), "core", 4.0)
            p.lathe(["steel_dark", "brass", "steel_dark"], [(0.03, -0.035), (0.11 * s, -0.035), (0.11 * s, 0.035), (0.03, 0.035)], segs=10, loc=(0, y0 - 0.26, zb - 0.16 * s), rot=(0, HPI, 0))
            _sleeve(p, "steel", y0 - Lb * 0.3, y0 - Lb * 0.8, r * 1.7, zb)
            for k in range(3):
                _sleeve(p, "steel_dark", y0 - Lb * (0.38 + 0.16 * k), y0 - Lb * (0.38 + 0.16 * k) - 0.02, r * 1.85, zb, segs=6)
        elif style == "vanes":     # thin vanes it uses only to get up to a ledge
            for tag, sx in (("wing_l", 1), ("wing_r", -1)):
                root = Vector((sx * 0.04, y0 - 0.18, zb + 0.02))
                items = [(g.tube([root, root + Vector((sx * 0.1, 0, 0.04))], 0.012, n=4), gk.mat("metal_brass"))]
                for k in range(4):
                    b0 = root + Vector((sx * 0.08, 0.02 - 0.03 * k, 0.03))
                    tip = b0 + Vector((sx * (0.5 + 0.1 * k) * s, 0.16 + 0.14 * k, 0.16 - 0.05 * k))
                    items.append((g.blade(b0, tip, 0.11 + 0.02 * k, thick=0.004, normal=Vector((0, -0.2, 1)), belly=0.5), gk.mat("metal_iron_light" if k % 2 else "metal_brass")))
                    items.append((g.tube([b0, tip], [0.006, 0.002], n=3), gk.mat("metal_dark")))
                w.wings[tag] = (items, tuple(root))
        elif style == "screen":    # its glass shows you the night, grey and plain
            c = Vector((0, y0 + 0.12, top + 0.06))
            p.slab("brass", [(-0.1 * s, -0.075 * s), (0.1 * s, -0.075 * s), (0.1 * s, 0.075 * s), (-0.1 * s, 0.075 * s)], 0.022, bevel=0.3, loc=tuple(c))
            p.box("tin", (0.17 * s, 0.006, 0.12 * s), tuple(c + Vector((0, 0.012, 0))))
            lines = None
            for k in range(3):
                lines = g.merge(lines, g.box(c + Vector((-0.04 * s + 0.04 * s * k, 0.017, -0.01 * s + 0.02 * s * (k % 2))), (0.012 * s, 0.004, 0.05 * s + 0.02 * s * k)))
            w.hard.append((lines, gk.mat("metal_dark")))
            p.box("steel_dark", (0.03, 0.1, 0.03), tuple(c + Vector((0, -0.05, -0.03))))
        elif style == "frost":     # a breath of frost at the muzzle
            _sleeve(p, "ice", ym + Lb * 0.3, ym + 0.02, r * 1.35, zb)
            ice = None
            for k in range(7):
                a = 2 * math.pi * k / 7
                d = Vector((math.cos(a), 0, math.sin(a)))
                b0 = Vector((0, ym + 0.04, zb)) + d * r * 1.2
                ice = g.merge(ice, g.cone(b0, b0 + d * (0.05 + 0.03 * (k % 2)) * s + Vector((0, -0.07 * s, 0)), 0.014, n=4))
            for k in range(4):
                b0 = Vector((0.01 * math.sin(k * 2.0), ym + Lb * (0.08 + 0.07 * k), zb - r * 1.2))
                ice = g.merge(ice, g.cone(b0, b0 + Vector((0, 0, -0.06 - 0.02 * (k % 2))), 0.012, n=4))
            w.hard.append((ice, gk.mat("ice_pale")))
            w.light(g.ico((0, y0 - 0.02, zb + r * 1.5), 0.02, sub=0, scale=(1, 1.6, 0.6)), "core", 3.0)
        elif style == "rings":     # bright rings round the barrel, one for each beat
            n = 6
            geo = None
            for k in range(n):
                y = y0 - Lb * (0.3 + 0.6 * k / (n - 1))
                geo = g.merge(geo, g.moved(g.lathe([(r * 1.25, -0.012), (r * 1.55, -0.008), (r * 1.55, 0.008), (r * 1.25, 0.012)], n=8), Matrix.Translation((0, y, zb)) @ Matrix.Rotation(HPI, 4, "X")))
            w.light(geo, "beat", 2.8)
        elif style == "wire":      # a stock of wire, to steady a long barrel
            p.tube("steel", [(0, 0.1, 0.05), (0, 0.45 * s, 0.0), (0, 0.5 * s, -0.16), (0, 0.44 * s, -0.17), (0, 0.12, -0.06)], 0.01, segs=4)
            p.box("leather_dark", (0.04, 0.03, 0.17), (0, 0.5 * s, -0.08))
            rear, low = 0.52 * s, min(low, -0.2)
        elif style == "patches":   # a patched barrel, each patch a different metal
            mats = ("copper", "tin", "brass", "iron", "copper", "tin")
            n = int(4 * s)
            for k in range(n):
                y = y0 - Lb * (0.2 + 0.68 * k / max(1, n - 1))
                _sleeve(p, mats[k % 6], y + 0.045, y - 0.045, r * (1.3 + 0.12 * (k % 2)), zb, segs=6)
                w.bead("steel_dark", 0.009, (r * 1.2, y + 0.02, zb + r * 0.6))
        elif style == "smoke":     # it loads with whatever the field gives it
            for k in range(3):
                b0 = Vector((0, ym - 0.01, zb))
                d = (-0.04 + 0.04 * k)
                w.soft.append((g.tongue([b0, b0 + Vector((d, -0.07, 0.07)) * s, b0 + Vector((d * 2, -0.1, 0.2)) * s, b0 + Vector((d * 1.2, -0.06, 0.34)) * s], [0.05, 0.07, 0.05, 0.01], thick=0.4, normal=Y), gk.mat("smoke" if k != 1 else "shade_edge")))
        elif style == "hot":       # the barrel glows dull at the muzzle and ticks as it cools
            geo = g.moved(g.lathe([(r * 1.12, 0.0), (r * 1.3, 0.02), (r * 1.3, Lb * 0.2), (r * 1.1, Lb * 0.22)], n=8), Matrix.Translation((0, ym + Lb * 0.23, zb)) @ Matrix.Rotation(HPI, 4, "X"))
            w.light(geo, "heat", 2.2)
            for k in range(5):
                y = ym + Lb * (0.3 + 0.07 * k)
                _sleeve(p, "iron", y + 0.006, y - 0.006, r * (2.3 - 0.12 * k) * s, zb)
        elif style == "odd":       # not one part matches another
            _barrel(p, 0.0, y0 - 0.02, Lb * 0.55, r * 1.5, zb - r * 2.6, mat="brass", flare=1.5)
            p.lathe(["tin", "copper"], [(0.02, 0.0), (0.03, 0.02), (0.085, 0.12), (0.09, 0.13)], segs=7, loc=(0, y0 - 0.1, zb + r))
            p.tube("copper", [(0.03, y0 - 0.3, zb + 0.03 * math.sin(k)) for k in range(0)] or [(0.035, y0 - 0.22, zb + 0.02), (0.05, y0 - 0.3, zb + 0.05), (0.035, y0 - 0.38, zb + 0.02), (0.05, y0 - 0.46, zb + 0.05), (0.035, y0 - 0.54, zb + 0.02)], 0.009, segs=3)
            _cog(p, "brass", (-0.04, y0 - 0.05, zb - 0.02), 0.045, teeth=7)
        elif style == "hands":     # small hands of brass do the fitting
            for sx, reach in ((1, -0.26), (-1, -0.08)):
                sh = Vector((sx * 0.035, y0 - 0.02, zb + 0.03))
                el = sh + Vector((sx * 0.1, -0.03, 0.09))
                wr = Vector((sx * 0.06, y0 + reach, zb + 0.07))
                p.tube("brass", [sh, el, wr], [0.011, 0.009, 0.008], segs=4)
                w.bead("brass_dark", 0.014, el)
                p.box("brass", (0.03, 0.036, 0.022), wr + Vector((0, -0.02, -0.004)))
                for f in (-1, 0, 1):
                    p.bar("brass", wr + Vector((f * 0.009, -0.035, 0)), wr + Vector((f * 0.012, -0.06, -0.012)), 0.004, segs=3)
            p.bar("steel", (0.06, y0 - 0.3, zb + 0.062), (0.06, y0 - 0.4, zb + 0.09), 0.006, segs=3)
            p.box("steel", (0.012, 0.03, 0.03), (0.06, y0 - 0.41, zb + 0.095))
        elif style == "lamp":      # a lamp bracket on its shoulder; it stands with the light behind it
            a0 = Vector((0, -0.3 + 0.0, 0.0))
            arm = [a0 + Vector((0, 0.02, -0.1)), a0 + Vector((0.2, 0.2, 0.25 * s)), a0 + Vector((0.2, 0.42, 0.3 * s))]
            p.tube("iron", arm, 0.014, segs=4)
            _lamp(w, arm[-1], 0.1 * s, shade=False)
        elif style == "veil":      # a steady glow at its back, like a post-flame seen through cloth
            a0 = Vector((0, -0.3, 0.0))
            arm = [a0 + Vector((0, 0.02, -0.1)), a0 + Vector((0.0, 0.3, 0.42 * s)), a0 + Vector((0.0, 0.52, 0.46 * s))]
            p.tube("iron", arm, 0.016, segs=4)
            _lamp(w, arm[-1], 0.14 * s, shade=True)
        elif style == "writ":      # a plate on its chest with a writ nailed to it
            c = Vector((0, -0.3 - 0.07, -H * 0.24))
            p.slab("iron", [(-0.17 * s, -0.2 * s), (0.17 * s, -0.2 * s), (0.19 * s, 0.1 * s), (0.1 * s, 0.22 * s), (-0.1 * s, 0.22 * s), (-0.19 * s, 0.1 * s)], 0.03, bevel=0.3, loc=tuple(c))
            p.box("paper", (0.2 * s, 0.008, 0.26 * s), tuple(c + Vector((0, -0.02, -0.01))))
            ink = None
            for k in range(5):
                ink = g.merge(ink, g.box(c + Vector((0.01 * math.sin(k), -0.026, 0.085 * s - 0.04 * s * k)), ((0.15 - 0.02 * (k % 2)) * s, 0.004, 0.012 * s)))
            w.hard.append((ink, gk.mat("metal_dark")))
            w.light(g.ico(c + Vector((0.05 * s, -0.03, -0.11 * s)), 0.024 * s, sub=0, scale=(1, 0.4, 1)), "seal", 2.4)
            w.bead("brass", 0.012, c + Vector((0, -0.028, 0.115 * s)))
        elif style == "shield":    # a plate grown across its front, with one slot for the barrel
            ys = y0 - Lb * 0.42
            hw, hh = 0.36 * s, 0.34 * s
            for sx in (-1, 1):
                p.slab("iron_light", [(sx * (r + 0.02), -hh * 0.8), (sx * hw, -hh * 0.8), (sx * hw * 1.08, hh * 0.5), (sx * hw * 0.7, hh), (sx * (r + 0.02), hh)][::sx], 0.03, bevel=0.3, loc=(0, ys, zb))
                p.box("mark_blazon", (hw * 0.5, 0.012, 0.05), (sx * hw * 0.52, ys - 0.018, zb - hh * 0.3), rot=(0, sx * 0.55, 0))
            p.box("iron_light", (2 * r + 0.05, 0.03, hh * 0.8 - r - 0.012), (0, ys, zb - r - 0.012 - (hh * 0.8 - r - 0.012) / 2))
            p.box("iron_light", (2 * r + 0.05, 0.03, hh - r - 0.012), (0, ys, zb + r + 0.012 + (hh - r - 0.012) / 2))
            for sx in (-1, 1):
                for zz in (-hh * 0.55, hh * 0.6):
                    w.bead("brass", 0.016, (sx * hw * 0.8, ys - 0.02, zb + zz))
            p.box("steel_dark", (hw * 1.3, 0.012, 0.03), (0, ys - 0.016, zb + hh * 0.72))
        elif style == "mantlet":   # a plate taller than you, a worn place where a shoulder leans
            ys = y0 - Lb * 0.36
            hw, top_z, bot_z = 0.5 * s, zb + 0.75 * s, -H + 0.04
            for sx in (-1, 1):
                p.slab("iron_light", [(sx * (r + 0.02), bot_z), (sx * hw, bot_z), (sx * hw * 1.05, top_z - 0.25), (sx * hw * 0.6, top_z), (sx * (r + 0.02), top_z)][::sx], 0.04, bevel=0.25, loc=(0, ys, 0))
                p.box("mark_blazon", (hw * 0.55, 0.014, 0.07), (sx * hw * 0.5, ys - 0.024, zb - 0.62), rot=(0, sx * 0.55, 0))
            p.box("iron_light", (2 * r + 0.05, 0.04, zb - r - 0.012 - bot_z), (0, ys, (zb - r - 0.012 + bot_z) / 2))
            p.box("iron_light", (2 * r + 0.05, 0.04, top_z - zb - r - 0.012), (0, ys, (top_z + zb + r + 0.012) / 2))
            p.box("field_glow", (hw * 0.9, 0.012, 0.022), (0, ys - 0.022, top_z - 0.2))
            p.box("steel_dark", (hw * 1.1, 0.02, 0.05), (0, ys - 0.02, top_z - 0.2))
            for zz in (bot_z + 0.2, zb - 0.3, zb + 0.4):
                p.box("iron", (hw * 2.0, 0.05, 0.045), (0, ys, zz))
            p.box("steel_edge", (0.2, 0.012, 0.3), (-hw * 0.5, ys + 0.022, zb + 0.2))        # the worn place
            for sx in (-1, 1):
                p.lathe(["iron", "steel", "iron"], [(0.02, -0.02), (0.1, -0.02), (0.1, 0.02), (0.02, 0.02)], segs=8, loc=(sx * hw * 0.9, ys + 0.06, -H + 0.1), rot=(0, HPI, 0))
                p.bar("iron", (sx * hw * 0.9, ys + 0.03, -H + 0.1), (sx * hw * 0.5, ys + 0.3, -H + 0.04), 0.014, segs=4)
        elif style == "walls":     # it has dug itself in: small walls round its feet
            n = 7
            for k in range(n):
                a = math.pi * (0.15 + 1.7 * k / (n - 1)) + math.pi / 2 + math.pi
                c = Vector((math.cos(a) * H * 0.62 * s, -0.3 + math.sin(a) * H * 0.62 * s, -H + 0.07))
                w.bead("sand", 0.16 * s, c, scale=(1.0, 0.6, 0.46), rot=(0, 0, a + HPI))
                if k % 2 == 0:
                    w.bead("sand", 0.14 * s, c + Vector((0.02, 0, 0.12 * s)), scale=(1.0, 0.6, 0.46), rot=(0, 0, a + HPI + 0.3))
            for k in range(3):
                a = -math.pi / 2 + (k - 1) * 0.5
                c = Vector((math.cos(a) * H * 0.78 * s, -0.3 + math.sin(a) * H * 0.78 * s, -H + 0.1))
                p.box("stone", (0.3 * s, 0.14, 0.22), tuple(c), rot=(0, 0, a + HPI))
        elif style == "horn":      # it clears its throat
            geo = [(r * 1.1, 0.0), (r * 1.3, 0.1), (r * 2.0, 0.2), (r * 3.6 * s, 0.3), (r * 3.9 * s, 0.31)]
            p.lathe(["brass", "brass", "brass", "brass_dark"], geo, segs=10, loc=(0, ym + 0.12, zb), rot=(HPI, 0, 0))
            w.light(g.moved(g.lathe([(r * 2.4 * s, 0.0), (r * 3.2 * s, 0.01), (r * 2.4 * s, 0.02)], n=10), Matrix.Translation((0, ym - 0.16, zb)) @ Matrix.Rotation(HPI, 4, "X")), "voice", 2.0)
        elif style == "flag":      # a signal, plainly
            pole = [Vector((0, -0.3, 0.0)), Vector((0, -0.3 + 0.1, 0.55 * s))]
            p.bar("dark_wood", pole[0], pole[1], 0.012, segs=4)
            w.soft.append((g.tongue([pole[1] + Vector((0, 0, -0.02)), pole[1] + Vector((0.02, 0.14, -0.05)), pole[1] + Vector((0.0, 0.3, -0.1))], [0.16, 0.15, 0.1], thick=0.06, normal=X), gk.mat("cloth_rag")))
        elif style == "badge":     # a ring of small points above its sight, like a badge worn high
            c = Vector((0, y0 - 0.16, top + 0.2 * s))
            p.bar("brass", (0, y0 - 0.16, top), tuple(c + Vector((0, 0, -0.07 * s))), 0.012, segs=4)
            p.torus("brass", 0.07 * s, 0.012, tuple(c), rot=(HPI, 0, 0), segs=10, rings=3)
            pts = None
            for k in range(7):
                a = 2 * math.pi * k / 7 + math.pi / 2
                d = Vector((math.cos(a), 0, math.sin(a)))
                pts = g.merge(pts, g.cone(c + d * 0.07 * s, c + d * 0.14 * s, 0.018 * s, n=4))
            w.hard.append((pts, gk.mat("metal_brass")))
            w.light(g.ico(c, 0.03 * s, sub=0, scale=(1, 0.5, 1)), "badge", 3.0)
        elif style == "wisps":     # a shade has been at it
            for k in range(3):
                b0 = Vector((0.03 * math.sin(k * 2.0), y0 - 0.05 - 0.12 * k, zb + 0.08))
                w.soft.append((g.tongue([b0, b0 + Vector((0.03, 0.06, 0.1)) * s, b0 + Vector((-0.03, 0.16, 0.22)) * s, b0 + Vector((0.02, 0.22, 0.36)) * s], [0.06, 0.07, 0.045, 0.008], thick=0.4, normal=X), gk.mat("shade_edge")))
    # its pose, floating level (or standing on what it has grown)
    k_show = LARGER[level] * float(spec.get("show", 1.0))
    front, back = ym - 0.05, rear
    if H > 0.0:
        yc = 0.3 if any(st == "tripod" for st, _ in each(spec.get("grows"))) else -balance
        F = Matrix.Translation((0, yc, H))
    else:
        F = Matrix.Translation((0, -(front + back) / 2, -low + 1.0 / k_show))
    objs, socks, ref = w.finish(F, _ref(base, form_id, level, float(spec.get("show", 1.0))))
    _export(form_id, objs, socks, ref)


# ======================================================================================
# The Bow
# ======================================================================================

def _limb_y(t, bend, recurve):
    """How far back (+Y, toward the hand that draws) a limb is at t of its length: it bends
    back all the way, and a recurve turns its tips to the front again."""
    return bend * t ** 1.6 - recurve * max(0.0, t - 0.68) ** 2 / 0.32 ** 2


def _arrow(w, nock, d, L, s=1.0, style="light", name="pulse"):
    """The arrow that is not wood: a line of the field from the string, pointing where it means to go."""
    nock, d = Vector(nock), Vector(d).normalized()
    head = nock + d * L
    side = d.cross(Z).normalized() if abs(d.dot(Z)) < 0.95 else X
    up = side.cross(d).normalized()
    geo = g.tube([nock, head], [0.008 * s, 0.008 * s], n=5)
    if style == "fire":            # it carries the element: a tongue of it at the head
        for k in range(5):
            a = 2 * math.pi * k / 5
            o = (side * math.cos(a) + up * math.sin(a))
            geo = g.merge(geo, g.blade(head - d * 0.06 * s + o * 0.012, head + d * (0.2 + 0.05 * (k % 2)) * s + o * 0.05 * s, 0.07 * s, normal=o, belly=0.4))
        geo = g.merge(geo, g.ico(head, 0.04 * s, sub=0))
    else:
        geo = g.merge(geo, g.cone(head, head + d * 0.11 * s, 0.028 * s, n=4))
    for a in (0.0, 2.1, 4.2):
        nrm = side * math.cos(a) + up * math.sin(a)
        geo = g.merge(geo, g.blade(nock + d * 0.015, nock + d * 0.13 * s + nrm * 0.045 * s, 0.035 * s, normal=nrm.cross(d), belly=0.5, thick=0.004))
    w.light(geo, name, 2.6)
    return head


def build_bow(form_id, level, spec, base):
    """One form of the Bow, from its body."""
    w = Weapon(form_id)
    p = w.p
    B = dict({"len": 0.45, "bend": 0.2, "recurve": 0.0, "width": 0.034, "thick": 0.02, "wood": "wood", "belly": None, "grip": 0.2, "lower": 1.0,
              "shoulders": 1.0, "rough": 0.0, "wrap": "dark", "tips": "mark_tips"}, **spec.get("bow", {}))
    half, bend, rec = float(B["len"]), float(B["bend"]), float(B["recurve"])
    wood, belly = B["wood"], B["belly"] or B["wood"]
    gl = float(B["grip"])
    a, b = WRAPS[B["wrap"]]
    limb = B.get("limb", "stave")
    W = float(B["width"])

    def width_at(t):
        """Half the breadth of a limb at t of its length, seen from the front: it is what a bow's outline is."""
        if limb == "leaf":         # a flat bow: its limbs widest a third of the way out
            return W * (0.55 + 0.95 * math.sin(math.pi * min(1.0, t / 0.55) * 0.5)) * (1.0 if t < 0.55 else 1.0 - 0.82 * (t - 0.55) / 0.45)
        if limb == "paddle":       # broad in the shoulder, like something that can carry weight
            return W * (1.55 if t < 0.5 else 1.55 - 1.25 * (t - 0.5) / 0.5) * (0.7 + 0.3 * min(1.0, t / 0.14))
        if limb == "scroll":       # slender, a thing made to sound
            return W * (1.0 - 0.45 * t)
        return W * (1 - 0.62 * t) * (1.0 + (B["shoulders"] - 1.0) * max(0.0, 1 - t * 2.6))

    wk.grip(p, -gl / 2, gl / 2, r=0.027 * (1.0 + 0.25 * (limb == "paddle")), mat=a, band=b, wraps=4)
    for zf in (-gl / 2 - 0.012, gl / 2 - 0.006):
        wk.ferrule(p, zf, r=0.027 * (1.0 + 0.25 * (limb == "paddle")), h=0.018, mat="leather_dark")
    n = 9
    tips = {}
    curve = {}
    for sz, hl in ((1, half), (-1, half * float(B["lower"]))):
        rings = []
        pts = []
        for i in range(n + 1):
            t = i / n
            z = gl / 2 + (hl - gl / 2) * t
            y = _limb_y(t, bend * hl, rec * hl * 0.3) + B["rough"] * 0.03 * math.sin(i * 2.3 + sz)
            wd = width_at(t)
            th = B["thick"] * (1 - 0.45 * t)
            x = B["rough"] * 0.02 * math.sin(i * 1.7 + 2 * sz)
            rings.append([Vector((x - wd, y - th * 0.3, sz * z)), Vector((x, y - th, sz * z)), Vector((x + wd, y - th * 0.3, sz * z)), Vector((x + wd * 0.8, y + th, sz * z)), Vector((x - wd * 0.8, y + th, sz * z))])
            pts.append(Vector((x, y, sz * z)))
        p.strip_loft(rings, [wood, wood, belly, belly, belly], cap=wood)
        tips[sz] = pts[-1]
        curve[sz] = pts
        tm = B["tips"]
        if tm == "horn-long":      # horn at the tips, long ears of it turned to the front
            e0 = pts[-1]
            e1 = e0 + Vector((0, -0.07 * hl, sz * 0.16 * hl))
            p.tube("horn", [e0 - Vector((0, 0, sz * 0.04)), e0 + (e1 - e0) * 0.5 + Vector((0, 0.01, 0)), e1], [0.022, 0.018, 0.008], segs=5)
            tips[sz] = e0
        elif tm == "scroll":       # its tips turned in a scroll, like the head of a fiddle
            c = pts[-1] + Vector((0, 0.0, sz * 0.045))
            p.lathe(["brass", "wood", "brass"], [(0.0, -0.016), (0.035, -0.014), (0.062, -0.006), (0.062, 0.006), (0.035, 0.014), (0.0, 0.016)], segs=9, loc=tuple(c), rot=(HPI, 0, 0))
            w.bead("brass", 0.018, c + Vector((0, -0.016, 0)))
            p.bar("brass", tuple(c + Vector((-0.07, 0, -sz * 0.06))), tuple(c + Vector((0.07, 0, -sz * 0.06))), 0.008, segs=4)
            for sx in (-1, 1):
                w.bead("brass", 0.014, c + Vector((sx * 0.075, 0, -sz * 0.06)))
        elif tm:
            p.box(tm, (0.034, 0.034, 0.06), (pts[-1].x, pts[-1].y, pts[-1].z + sz * 0.012))
    up, lo = tips[1], tips[-1]
    at = lambda sz, t: curve[sz][min(n, max(0, int(round(t * n))))]  # noqa: E731
    # the string
    sstyle, ss = opt(spec.get("string", "plain"))
    draw = float(spec.get("draw", 0.05)) * half
    sy = (up.y + lo.y) / 2 + draw
    nock = Vector((0, sy, 0.0))
    smat = {"dark": "crepe", "wires": "steel"}.get(sstyle, "gut")
    if sstyle in ("plain", "wrapped", "dark", "ring", "tremble", "twitch", "hair"):
        r_s = 0.0045 if sstyle != "hair" else 0.0025
        mids = [Vector((0, sy, lo.z * 0.5)), Vector((0, sy, up.z * 0.5))]
        if sstyle == "tremble":    # it trembles for a long time after anyone has touched it
            mids = [Vector((0.03 * math.sin(k * 2.2) * ss, sy + 0.02 * math.cos(k * 3.1), lo.z + (up.z - lo.z) * (k + 1) / 10)) for k in range(9)]
        elif sstyle == "twitch":   # never quite still: a kink that runs along it
            mids = [Vector((0, sy, lo.z * 0.5)), Vector((0.0, sy + 0.01, up.z * 0.12)), Vector((0.07 * ss, sy + 0.05, up.z * 0.2)), Vector((-0.05 * ss, sy - 0.02, up.z * 0.28)), Vector((0, sy, up.z * 0.4)), Vector((0, sy, up.z * 0.7))]
        pts = [lo + Vector((0, 0.004, 0))] + mids + [up + Vector((0, 0.004, 0))]
        if sstyle == "hair":       # not gut or wire: a hair, or a thread from a sleeve
            w.light(g.tube(pts, r_s * 1.6, n=3), "oath", 2.2)
        else:
            p.tube(smat, pts, r_s, segs=3)
            p.cone("cloth_red" if sstyle != "dark" else "crepe", 0.008, 0.008, 0.09, (0, sy, -0.045), segs=4)
        if sstyle == "wrapped":    # wrapped where it would otherwise slap
            for z in (lo.z * 0.72, up.z * 0.72):
                w.soft.append((g.ico((0, sy * 0.72 + (up.y if z > 0 else lo.y) * 0.28, z), 0.035 * ss, sub=1, scale=(1.0, 1.0, 1.5)), gk.mat("fur_ruff")))
            for sz, tp in ((1, up), (-1, lo)):
                p.cone("rag", 0.02, 0.016, 0.1, (tp.x, tp.y, tp.z - sz * 0.13 if sz == 1 else tp.z + 0.03), segs=5)
        elif sstyle == "ring":     # a soft ring of light round the middle of the string
            w.light(gr.ringtube((0, sy, 0.0), 0.085 * ss, 0.085 * ss, 0.011, n=12, u=X, v=Y), "hum", 2.4)
            w.light(gr.ringtube((0, sy, 0.0), 0.15 * ss, 0.15 * ss, 0.006, n=12, u=X, v=Y), "hum", 1.6)
    elif sstyle == "glow":         # a steady glow in the string that does not flicker all night
        w.light(g.tube([lo + Vector((0, 0.004, 0)), Vector((0, sy, 0)), up + Vector((0, 0.004, 0))], 0.011 * ss, n=4), "vigil", 2.6)
    elif sstyle == "wires":        # it hums with the line's wires
        for k in (-1, 0, 1):
            p.tube("steel", [lo + Vector((k * 0.02, 0.004, 0)), Vector((k * 0.02, sy, 0)), up + Vector((k * 0.02, 0.004, 0))], 0.003, segs=3)
        for sz, tp in ((1, up), (-1, lo)):
            p.lathe(["paper", "paper"], [(0.012, -0.03), (0.03, -0.012), (0.03, 0.012), (0.012, 0.03)], segs=6, loc=(tp.x, tp.y, tp.z - sz * 0.05), rot=(0, HPI, 0))
    w.off = tuple(nock)
    # the arrow of light on the string
    astyle, asz = opt(spec.get("arrow", "light"))
    La = (0.5 + 0.35 * half) * asz
    arrow_tip = nock + Vector((0, -La, 0))
    if astyle in ("light", "fire"):
        arrow_tip = _arrow(w, nock, (0, -1, 0), La, s=0.9 + 0.25 * half, style=astyle)
    elif astyle == "up":           # it points up and a little out, always, at the horizon
        arrow_tip = _arrow(w, nock, (0, -0.62, 0.78), La * 1.15, s=0.9 + 0.25 * half)
    elif astyle == "many":         # everything at once, to everyone
        for k, ang in enumerate((-0.5, -0.25, 0.0, 0.25, 0.5)):
            tip = _arrow(w, nock + Vector((0, 0, 0.03 * (k - 2))), (0.25 * math.sin(k * 2.0) * 0.0, -math.cos(ang), math.sin(ang)), La * (1.0 - 0.12 * abs(k - 2)), s=0.8 + 0.2 * half)
            if k == 2:
                arrow_tip = tip
    elif astyle == "threads":      # thin bright threads trail from its arrows, like sewing
        arrow_tip = _arrow(w, nock, (0, -1, 0), La, s=0.9 + 0.25 * half)
        th = [nock, nock + Vector((0.05, 0.06, -0.1)), nock + Vector((-0.04, 0.1, -0.24)), nock + Vector((0.06, 0.07, -0.4)), nock + Vector((-0.02, 0.12, -0.55)), nock + Vector((0.03, 0.1, -0.7 * half - 0.2))]
        w.light(g.tube(th, 0.0045, n=3), "thread", 2.0)
        w.light(g.tube([arrow_tip, arrow_tip + Vector((0.05, 0.1, -0.12)), arrow_tip + Vector((-0.03, 0.22, -0.3))], 0.004, n=3), "thread", 2.0)
    # the eye in its grip, looking down the arrow
    estyle, er = opt(spec.get("eye", "grip"))
    er *= 1.0 + 0.2 * (level - 1)
    look = spec.get("eyelook", "open")
    ec = Vector((0.0, -0.034, -0.03))
    if estyle == "grip":
        w.eye(ec, 0.016 * er, look=look, lids="leather_dark")
    w.marks["eye"] = ec + Vector((0, -0.02, 0))
    # what rides on it
    for style, s in each(spec.get("rides")):
        if style == "bark":        # limbs scuffed with bark; it smells of outdoors
            for sz in (1, -1):
                for t in (0.3, 0.62):
                    c = at(sz, t)
                    p.cone("bark", width_at(t) * 1.25, width_at(t) * 1.15, 0.13 * s, (c.x, c.y, c.z - 0.065 * s), segs=5, scale=(1.0, 0.6, 1.0))
            c = at(1, 0.45)
            leaves = g.merge(g.blade(c + Vector((0.02, 0, 0)), c + Vector((0.13, -0.03, 0.09)) * s, 0.06, normal=Y), g.blade(c + Vector((0.02, 0, 0)), c + Vector((0.1, 0.02, -0.05)) * s, 0.05, normal=Y))
            w.soft.append((leaves, gk.mat("cloth_petal")))
        elif style == "arrows":    # old arrows bound along its back, each with a different fletching
            fl = ("feather_dark", "cloth_rag", "bone", "cloth_petal")
            for k in range(int(3 * s)):
                x = (k - 1) * 0.022
                a0 = at(1, 0.15) + Vector((x, -0.035, 0))
                a1 = at(1, 0.82) + Vector((x * 0.6, -0.03, 0))
                p.bar("oak_pale", a0, a1, 0.006, segs=3)
                p.cone("steel", 0.012, 0.0, 0.05, tuple(a1), rot=wk.along(a0, a1), segs=4)
                d = (a1 - a0).normalized()
                for sgn in (1, -1):
                    w.hard.append((g.blade(a0 + d * 0.01, a0 + d * 0.11 + Vector((sgn * 0.03, -0.012, 0)), 0.03, normal=Y, belly=0.5, thick=0.003), gk.mat(fl[k % 4])))
            for t in (0.22, 0.5, 0.76):
                c = at(1, t)
                p.cone("cord", 0.05, 0.05, 0.02, (c.x, c.y - 0.02, c.z), segs=6, scale=(1.0, 0.8, 1.0))
        elif style == "ear":       # its grip has an ear of its own, pressed toward the ground
            c = Vector((0.03, -0.01, -gl / 2 - 0.02))
            ear = g.tongue([c, c + Vector((0.07, -0.04, -0.1)) * s, c + Vector((0.09, -0.07, -0.26)) * s, c + Vector((0.04, -0.08, -0.4)) * s], [0.05, 0.12 * s, 0.11 * s, 0.02], thick=0.22, normal=(0.4, -1, 0))
            w.soft.append((ear, gk.mat("leather")))
            w.soft.append((g.tongue([c + Vector((0.03, -0.035, -0.08)) * s, c + Vector((0.075, -0.075, -0.24)) * s, c + Vector((0.045, -0.09, -0.34)) * s], [0.02, 0.05 * s, 0.01], thick=0.2, normal=(0.4, -1, 0)), gk.mat("hand_skin")))
        elif style == "sinew":     # sinew on the back, none of it bought
            for sz in (1, -1):
                for t in (0.2, 0.42, 0.64):
                    c = at(sz, t)
                    p.cone("sinew", width_at(t) * 1.2, width_at(t) * 1.2, 0.05, (c.x, c.y, c.z - 0.025), segs=5, scale=(1.0, 0.6, 1.0))
            p.tube("bone", [(0.0, -0.03, gl / 2 - 0.02), (0.05, -0.08, gl / 2 + 0.04), (0.04, -0.14, gl / 2 + 0.12)], [0.018, 0.013, 0.004], segs=5)
            p.tube("bone", [(0.035, -0.07, gl / 2 + 0.02), (0.09, -0.1, gl / 2 + 0.05)], [0.011, 0.003], segs=4)
        elif style == "vanes":     # small vanes at the tips that turn in a breeze
            for sz, tp in ((1, up), (-1, lo)):
                c = tp + Vector((0, -0.01, sz * 0.05))
                w.bead("brass", 0.014, c)
                geo = None
                for k in range(4):
                    a = k * HPI + 0.4
                    d = Vector((math.cos(a), 0, math.sin(a)))
                    geo = g.merge(geo, g.blade(c, c + d * 0.13 * s + Vector((0, -0.03, 0)), 0.07 * s, thick=0.004, normal=Vector((0.3, -1, 0)), belly=0.6))
                w.hard.append((geo, gk.mat("feather_pale")))
        elif style == "wings":     # never still: it sways as if walking
            for tag, sx in (("wing_l", 1), ("wing_r", -1)):
                root = Vector((sx * 0.02, 0.0, 0.02))
                items = []
                for k in range(5):
                    b0 = root + Vector((sx * 0.01, 0.0, 0.05 - 0.035 * k))
                    tip = b0 + Vector((sx * (0.34 + 0.07 * k) * s, 0.05 + 0.03 * k, 0.2 - 0.12 * k))
                    items.append((g.blade(b0, tip, 0.1 + 0.012 * k, thick=0.006, normal=Vector((0, -1, 0.2)), belly=0.45), gk.mat("feather_pale" if k % 2 else "feather_mid")))
                w.wings[tag] = (items, tuple(root))
        elif style == "sight":     # a ring to look at the skyline through
            c = Vector((0.0, -0.06, gl / 2 + 0.22 * s))
            p.bar("brass", (0, -0.03, gl / 2), tuple(c - Vector((0, 0, 0.075 * s))), 0.008, segs=4)
            p.torus("brass", 0.075 * s, 0.009, tuple(c), rot=(HPI, 0, 0), segs=10, rings=3)
            w.light(g.merge(g.box(c, (0.004, 0.004, 0.14 * s)), g.box(c, (0.14 * s, 0.004, 0.004))), "sight", 2.4)
        elif style == "fletch":    # a fan of small bright fletchings along its upper limb
            geo = None
            m = int(7 * s)
            for k in range(m):
                c = at(1, 0.25 + 0.65 * k / max(1, m - 1))
                geo = g.merge(geo, g.blade(c + Vector((0.01, -0.01, 0)), c + Vector((0.2 + 0.04 * (k % 2), -0.05, 0.1)) * (0.8 + 0.2 * s), 0.085, thick=0.005, normal=Y, belly=0.5))
            w.light(geo, "fletch", 2.2)
        elif style == "brazier":   # it leaves a mark where it stood: the element rides with it
            c = Vector((0.0, -0.05, -gl / 2 - 0.2 * s))
            p.bar("iron", (0, -0.02, -gl / 2), tuple(c + Vector((0, 0, 0.07 * s))), 0.006, segs=3)
            p.lathe(["iron", "iron"], [(0.02 * s, -0.07 * s), (0.07 * s, -0.03 * s), (0.08 * s, 0.05 * s)], segs=7, loc=tuple(c))
            w.light(g.ico(c + Vector((0, 0, 0.045 * s)), 0.058 * s, sub=1, scale=(1.0, 1.0, 0.6)), "coals", 2.8)
            for sz in (1,):
                for t in (0.55, 0.8):
                    cc = at(sz, t)
                    p.cone("soot", width_at(t) * 1.25, width_at(t) * 1.2, 0.14, (cc.x, cc.y, cc.z - 0.07), segs=5, scale=(1.0, 0.6, 1.0))
        elif style == "feet":      # flat feet on its lower limb, set to brace against a moving floor
            c = lo + Vector((0, 0.0, -0.04))
            p.box("iron", (0.3 * s, 0.14 * s, 0.03), tuple(c))
            for sx in (-1, 1):
                p.bar("iron", tuple(c + Vector((sx * 0.13 * s, 0, 0.0))), tuple(at(-1, 0.55) + Vector((sx * 0.01, 0, 0))), 0.009, segs=4)
                p.box("iron", (0.06, 0.2 * s, 0.022), tuple(c + Vector((sx * 0.13 * s, -0.03, -0.01))))
            p.torus("iron", 0.06 * s, 0.009, tuple(c + Vector((0, -0.02, -0.02))), rot=(HPI, 0, HPI), segs=8, rings=3, sweep=math.pi, start=math.pi)
        elif style == "lamp":      # a small lamp at the grip
            _lamp(w, Vector((0.05, -0.02, -gl / 2 + 0.01)), 0.075 * s)
        elif style == "quiver":    # a quiver that always looks full
            q0 = at(-1, 0.2) + Vector((-0.06, 0.03, 0))
            q1 = at(-1, 0.78) + Vector((-0.07, 0.03, 0))
            p.cone("leather", 0.05 * s, 0.038 * s, (q0 - q1).length, tuple(q1), rot=wk.along(q1, q0), segs=6)
            p.cone("leather_dark", 0.054 * s, 0.054 * s, 0.03, tuple(q0 - (q0 - q1).normalized() * 0.03), rot=wk.along(q1, q0), segs=6)
            geo = None
            d = (q0 - q1).normalized()
            for k in range(5):
                o = Vector((0.022 * math.cos(k * 1.3), 0.022 * math.sin(k * 1.3), 0)) * s
                geo = g.merge(geo, g.tube([q0 + o, q0 + o + d * (0.1 + 0.02 * (k % 2))], 0.005, n=3))
                for sgn in (1, -1):
                    geo = g.merge(geo, g.blade(q0 + o + d * 0.03, q0 + o + d * 0.13 + Vector((sgn * 0.025, 0, 0)), 0.03, thick=0.003, normal=Y, belly=0.5))
            w.light(geo, "quiver", 2.0)
        elif style == "insulators":  # the line's own pots, where its wires are made fast
            for sz in (1, -1):
                for t in (0.35, 0.65):
                    c = at(sz, t)
                    p.lathe(["paper", "paper", "paper"], [(0.014, 0.0), (0.034, 0.012), (0.03, 0.03), (0.016, 0.045)], segs=6, loc=(c.x, c.y - 0.02, c.z), rot=(HPI, 0, 0))
        elif style == "spool":     # a reel of bright thread
            c = Vector((0.0, -0.02, gl / 2 + 0.07))
            p.lathe(["brass", "paper", "brass"], [(0.012, -0.045), (0.045 * s, -0.04), (0.045 * s, -0.032), (0.028 * s, -0.03), (0.028 * s, 0.03), (0.045 * s, 0.032), (0.045 * s, 0.04), (0.012, 0.045)], segs=7, loc=tuple(c), rot=(0, HPI, 0))
            w.light(g.moved(g.lathe([(0.03 * s, -0.028), (0.036 * s, 0.0), (0.03 * s, 0.028)], n=7, caps=False), Matrix.Translation(c) @ Matrix.Rotation(HPI, 4, "Y")), "thread", 2.0)
        elif style == "gourd":     # a drawn string is a note: it has a gourd to speak through
            c = Vector((0.0, 0.05 * s, -gl / 2 - 0.03))
            w.bead("gourd", 0.11 * s, c + Vector((0, 0.06 * s, -0.05 * s)), scale=(1.0, 0.9, 1.05), sub=2)
            w.hard.append((g.ico(c + Vector((0, -0.04 * s, -0.05 * s)), 0.04 * s, sub=1, scale=(1.0, 0.3, 1.0)), gk.mat("eye_dark")))
            w.light(gr.ringtube(c + Vector((0, -0.045 * s, -0.05 * s)), 0.046 * s, 0.046 * s, 0.006, n=10, u=X, v=Z), "voice", 2.0)
        elif style == "roots":     # fine roots of light trail from its lower limb into the ground
            geo = None
            for k in range(5):
                a = k * 1.3
                r0 = lo + Vector((0, 0, 0.02))
                r1 = lo + Vector((0.06 * math.cos(a), 0.05 * math.sin(a), -0.07))
                r2 = lo + Vector((0.16 * math.cos(a) * s, 0.14 * math.sin(a) * s, -0.11 - 0.02 * (k % 2)))
                geo = g.merge(geo, g.tube([r0, r1, r2], [0.007, 0.005, 0.002], n=3))
            w.light(geo, "roots", 2.2)
        elif style == "candle":    # one low note, held from dusk to light
            c = Vector((0.0, -0.05, gl / 2 + 0.03))
            p.lathe(["brass", "brass"], [(0.045 * s, 0.0), (0.05 * s, 0.01), (0.02 * s, 0.02)], segs=7, loc=tuple(c))
            p.cone("wax", 0.02 * s, 0.018 * s, 0.1 * s, tuple(c + Vector((0, 0, 0.015))), segs=6)
            w.light(g.blade(c + Vector((0, 0, 0.115 * s)), c + Vector((0, 0, 0.2 * s)), 0.035 * s, normal=Y, belly=0.35, thick=0.012), "candle", 3.0)
        elif style == "tip-eyes":  # an eye at each tip as well as the grip, and the three do not agree
            for sz, tp, face in ((1, up, (0.5, -1, 0.3)), (-1, lo, (-0.6, -1, -0.2))):
                c = tp + Vector((0, -0.01, sz * 0.07))
                w.bead(wood, 0.05 * s, c)
                w.eye(c + Vector(face).normalized() * 0.04 * s, 0.024 * s * (1.0 + 0.2 * (level - 1)), facing=face, look="open", lids="leather_dark")
        elif style == "token":     # strung with something given: a ribbon of it tied on, and a small crown
            c = at(1, 0.7)
            w.soft.append((g.merge(g.tongue([c, c + Vector((0.06, 0.02, -0.08)), c + Vector((0.08, 0.03, -0.24)) * 1.0], [0.035, 0.04, 0.012], thick=0.15, normal=Y),
                                   g.tongue([c, c + Vector((-0.04, 0.03, -0.1)), c + Vector((-0.03, 0.05, -0.3))], [0.035, 0.04, 0.012], thick=0.15, normal=Y)), gk.mat("cloth_petal")))
            cc = up + Vector((0, 0, 0.05))
            p.torus("brass", 0.04 * s, 0.008, tuple(cc), segs=8, rings=3)
            pts = None
            for k in range(5):
                a2 = 2 * math.pi * k / 5
                pts = g.merge(pts, g.cone(cc + Vector((math.cos(a2), math.sin(a2), 0)) * 0.04 * s, cc + Vector((math.cos(a2) * 1.25, math.sin(a2) * 1.25, 1.6)) * 0.04 * s, 0.011, n=4))
            w.hard.append((pts, gk.mat("metal_brass")))
        elif style == "knot":      # the oath does the pulling: a cord of it round the grip, and its light where a string was
            p.torus("cord", 0.04, 0.012, (0, 0, gl / 2 + 0.03), segs=6, rings=3)
            p.torus("cord", 0.04, 0.012, (0, 0, -gl / 2 - 0.03), segs=6, rings=3)
            w.soft.append((g.merge(g.tongue([(0.03, 0, gl / 2 + 0.03), (0.07, 0.02, gl / 2 - 0.06), (0.06, 0.03, gl / 2 - 0.2)], [0.02, 0.022, 0.008], thick=0.4, normal=Y),
                                   g.tongue([(0.03, 0, -gl / 2 - 0.03), (0.06, 0.02, -gl / 2 - 0.12), (0.04, 0.03, -gl / 2 - 0.26)], [0.02, 0.022, 0.008], thick=0.4, normal=Y)), gk.mat("cord")))
            geo = None
            for k in range(7):
                q = lo.lerp(up, (k + 0.5) / 7) + Vector((0, 0.004, 0))
                geo = g.merge(geo, g.ico(q, 0.011 * s, sub=1))
            w.soft.append((geo, gk.field("oath", 2.0)))
        elif style == "crepe":     # a dark wrap on the upper limb that it has never let you change
            for t in (0.3, 0.5, 0.7):
                c = at(1, t)
                p.cone("crepe", width_at(t) * 1.3, width_at(t) * 1.25, 0.2 * half, (c.x, c.y, c.z - 0.1 * half), segs=4, scale=(1.0, 0.6, 1.0))
            c = at(1, 0.3)
            w.soft.append((g.merge(g.tongue([c, c + Vector((0.07, 0.04, -0.12)), c + Vector((0.1, 0.07, -0.4)) * s, c + Vector((0.06, 0.1, -0.62)) * s], [0.05, 0.07, 0.06, 0.012], thick=0.12, normal=Y),
                                   g.tongue([c, c + Vector((-0.05, 0.05, -0.14)), c + Vector((-0.08, 0.09, -0.36)) * s], [0.05, 0.06, 0.012], thick=0.12, normal=Y)), gk.mat("cloth_dark")))
            c2 = at(1, 0.85)
            w.soft.append((g.tongue([c2, c2 + Vector((0.04, 0.08, 0.1)), c2 + Vector((-0.03, 0.18, 0.24)), c2 + Vector((0.02, 0.24, 0.4))], [0.06, 0.07, 0.045, 0.008], thick=0.4, normal=X), gk.mat("shade_edge")))
        elif style == "needle":    # its nerves are quicker than its thoughts
            c = Vector((0.0, -0.035, gl / 2 + 0.05))
            p.box("brass", (0.07, 0.03, 0.04), tuple(c))
            w.light(g.tube([c, c + Vector((0.12 * s, -0.01, 0.1 * s)), c + Vector((0.2 * s, -0.01, 0.05 * s))], [0.006, 0.004, 0.002], n=3), "nerve", 2.4)
        elif style == "bands":     # iron about the limbs, to carry the weight of the draw
            for sz in (1, -1):
                for t in (0.18, 0.4):
                    c = at(sz, t)
                    p.box("iron", (width_at(t) * 2 + 0.016, B["thick"] * 2 + 0.016, 0.04), (c.x, c.y, c.z))
        elif style == "cloth":     # a strip of red, to be found by
            c = at(-1, 0.75)
            w.soft.append((g.tongue([c, c + Vector((0.05, 0.03, -0.1)), c + Vector((0.07, 0.05, -0.28)) * s], [0.04, 0.045, 0.012], thick=0.15, normal=Y), gk.mat("cloth_rag")))
    # its pose: upright, its arrow to the front
    gap = 0.1
    F = Matrix.Translation((0, 0, -min(lo.z, -half * float(B["lower"])) + 0.06 + gap))
    w.marks.update({"mouth": tuple(arrow_tip), "hold": (0, 0, 0), "light": tuple(nock.lerp(arrow_tip, 0.5)), "back": (0, sy + 0.03, 0.1), "throat": (0, -0.04, -gl / 2 - 0.05),
                    "body": (0, -0.04, -gl), "tail": tuple(lo), "arm_l": (-0.06, 0, 0.0), "arm_r": (0.06, 0, 0.0), "keepsake": tuple(at(-1, 0.3) + Vector((0, -0.03, 0))), "mid": (0, 0, 0)})
    objs, socks, ref = w.finish(F, _ref(base, form_id, level, float(spec.get("show", 1.0))))
    _export(form_id, objs, socks, ref)


# ======================================================================================
# The gifts: what a hybrid wears of the Blade, the Gun or the Bow (data/genius-bases, hybrid.gift).
# Parts, the genius kit's way: at the socket's origin, for the left where one of a pair, made
# for a body 0.72 tall. Bold: an Edged Wolf must look edged from across a yard.
# ======================================================================================

def short_blade_part():
    """A short blade, carried: a real one, half as long as the thing that carries it is tall;
    a wrapped grip, a brass guard and pommel, an edge of the field. Its shaft is the socket's Z."""
    blade = g.tongue([(0, 0, -0.05), (0, 0, -0.22), (0, 0, -0.5)], [0.055, 0.08, 0.004], thick=0.2, normal=(1, 0, 0))
    edge = g.tongue([(0, -0.022, -0.08), (0, -0.038, -0.24), (0, -0.004, -0.5)], [0.012, 0.012, 0.002], thick=0.9, normal=(1, 0, 0))
    fuller = g.box((0, 0.004, -0.2), (0.022, 0.012, 0.24))
    items = [(g.tube([(0, 0, 0.1), (0, 0, -0.03)], [0.016, 0.018], n=6), gk.mat("leather")), (g.box((0, 0, -0.04), (0.03, 0.14, 0.024)), gk.mat("metal_brass")),
             (blade, gk.mat("metal_iron_light")), (fuller, gk.mat("metal_iron")), (edge, gk.field("edge", 2.4)), (g.ico((0, 0, 0.115), 0.024, sub=0), gk.mat("metal_brass"))]
    for sy in (-1, 1):
        items.append((g.ico((0, sy * 0.075, -0.04), 0.016, sub=0), gk.mat("metal_brass")))
    return [gk._part("short_blade", items)]


def edge_part():
    """An edge: a blade standing from the shoulder and swept back, long as a forearm, its edge
    a line of the field. For the left; the game mirrors it."""
    pts = [Vector((0.0, 0.0, 0.0)), Vector((0.07, 0.1, 0.09)), Vector((0.12, 0.3, 0.15)), Vector((0.13, 0.56, 0.1))]
    blade = g.tongue(pts, [0.08, 0.13, 0.1, 0.004], thick=0.14, normal=(1, 0, 0.25))
    edge = g.tube([q + Vector((0.0, -0.01, 0.062 * w)) for q, w in zip(pts, (0.6, 1.0, 0.8, 0.0))], [0.007, 0.008, 0.006, 0.002], n=3)
    spine = g.tube([q + Vector((0.0, 0.01, -0.05 * w)) for q, w in zip(pts, (0.6, 1.0, 0.8, 0.0))], [0.01, 0.01, 0.008, 0.002], n=4)
    items = [(blade, gk.mat("metal_iron_light")), (edge, gk.field("edge", 2.6)), (spine, gk.mat("metal_iron")),
             (g.ico((0, 0, 0), 0.055, sub=1, scale=(0.7, 1.0, 1.0)), gk.mat("metal_brass")), (g.ico((0.035, 0, 0), 0.02, sub=0), gk.field("edge", 2.6))]
    return [gk._part("edge", items)]


def gears_part():
    """Works showing at the breast: a great brass cog, two smaller meshed with it, a jewel of
    the field at the hub, a key to wind it by."""
    def cog(c, r, teeth, depth, material):
        c = Vector(c)
        geo = g.tube([c + Vector((0, 0.0, 0)), c + Vector((0, -depth, 0))], [r, r], n=teeth)
        for i in range(teeth):
            a = 2 * math.pi * (i + 0.5) / teeth
            geo = g.merge(geo, g.box(c + Vector((math.cos(a) * r * 1.1, -depth / 2, math.sin(a) * r * 1.1)), (r * 0.34, depth * 0.9, r * 0.3), rot=(0, -a, 0)))
        return (geo, material)
    items = [cog((0.0, -0.02, 0.0), 0.125, 10, 0.03, gk.mat("metal_brass")), cog((0.165, -0.024, -0.085), 0.07, 7, 0.026, gk.mat("metal_iron_light")),
             cog((-0.15, -0.022, 0.09), 0.055, 6, 0.024, gk.mat("metal_copper")),
             (g.ico((0, -0.06, 0), 0.034, sub=0), gk.field("hub", 3.0)), (g.ico((0.165, -0.055, -0.085), 0.018, sub=0), gk.mat("metal_brass")),
             (g.tube([(0, -0.05, 0), (0, -0.13, 0)], [0.012, 0.012], n=4), gk.mat("metal_iron")),
             (g.box((0, -0.14, 0), (0.11, 0.014, 0.05)), gk.mat("metal_iron"))]
    return [gk._part("gears", items)]


def sight_glass_part():
    """A sight-glass: a brass glass as long as its head, borne over the brow on two legs, the
    field in its lens. Whatever wears it has decided to look a long way off."""
    brass, dark = gk.mat("metal_brass"), gk.mat("metal_dark")
    z = 0.085
    items = [(g.tube([(0, 0.14, z), (0, -0.02, z), (0, -0.22, z)], [0.036, 0.04, 0.05], n=8), brass),
             (g.tube([(0, -0.215, z), (0, -0.27, z)], [0.056, 0.062], n=8, caps=False), dark),
             (g.ico((0, -0.225, z), 0.046, sub=1, scale=(1.0, 0.35, 1.0)), gk.field("lens", 3.0)),
             (g.ico((0, -0.238, z), 0.016, sub=0, scale=(0.5, 0.4, 1.6)), gk.mat("eye_dark")),
             (g.ico((0, 0.145, z), 0.03, sub=1, scale=(1.0, 0.3, 1.0)), gk.field("lens", 2.2)),
             (g.tube([(0, 0.08, z), (0, 0.072, z)], [0.046, 0.046], n=8), dark), (g.tube([(0, -0.1, z), (0, -0.108, z)], [0.05, 0.05], n=8), dark)]
    for y in (0.076, -0.104):
        for sx in (-1, 1):
            items.append((g.tube([(sx * 0.03, y, z - 0.03), (sx * 0.055, y, 0.0)], [0.008, 0.008], n=4), dark))
    items.append((g.tube([(0.04, 0.0, z + 0.02), (0.075, 0.0, z + 0.05)], [0.007, 0.007], n=4), brass))
    items.append((g.ico((0.08, 0.0, z + 0.055), 0.018, sub=0), brass))
    return [gk._part("sight_glass", items)]


def far_eyes_part():
    """Eyes that see far: a brass band across the brow carrying a great lens over each eye,
    one pushed up, and two small eyes of the field above."""
    brass = gk.mat("metal_brass")
    band = [(0.12 * math.sin(t), -0.006 - 0.032 * math.cos(t) + 0.032, 0.035) for t in [math.radians(-70 + 14 * i) for i in range(11)]]
    items = [(g.tube(band, [0.01] * 11, n=4, flat=1.8), brass)]
    for cx, cz, lit in ((0.058, 0.0, 2.6), (-0.058, 0.05, 1.8)):
        rim = [(cx + 0.044 * math.cos(t), -0.02, cz + 0.044 * math.sin(t)) for t in [math.radians(36 * i) for i in range(11)]]
        items.append((g.tube(rim, [0.009] * 11, n=4, caps=False), brass))
        items.append((g.ico((cx, -0.02, cz), 0.04, sub=1, scale=(1, 0.3, 1)), gk.field("lens", lit)))
    eyes = None
    for sx in (-0.03, 0.03):
        eyes = g.merge(eyes, g.ico((sx, -0.012, 0.085), 0.015, sub=1, scale=(1.2, 0.6, 0.8)))
    items.append((eyes, gk.field("eyes", 3.0)))
    return [gk._part("far_eyes", items)]


def fletching_part():
    """Fletching of the field: three pairs of flights standing along its back, swept the way
    it has come from, like the feathers of an arrow that is already somewhere else."""
    lit, rib = None, None
    for k in range(3):
        y = 0.02 + 0.13 * k
        for sx in (-1, 1):
            b0 = Vector((sx * 0.02, y, 0.0))
            tip = b0 + Vector((sx * (0.1 + 0.02 * k), 0.24, 0.2 - 0.03 * k))
            lit = g.merge(lit, g.blade(b0, tip, 0.13, thick=0.008, normal=Vector((sx * 0.8, -0.3, 0.5)), belly=0.5))
            rib = g.merge(rib, g.tube([b0, tip], [0.008, 0.002], n=3))
    top = g.blade(Vector((0, 0.0, 0.01)), Vector((0, 0.36, 0.3)), 0.15, thick=0.008, normal=X, belly=0.5)
    items = [(lit, gk.field("fletch", 1.6)), (top, gk.field("fletch", 1.6)), (rib, gk.mat("feather_pale")),
             (g.tube([(0, -0.02, 0.0), (0, 0.4, 0.02)], [0.016, 0.01], n=5), gk.mat("wood"))]
    return [gk._part("fletching", items)]


GIFTS = {"short-blade": short_blade_part, "edge": edge_part, "gears": gears_part, "sight-glass": sight_glass_part, "far-eyes": far_eyes_part, "fletching": fletching_part}


# ======================================================================================
# The families
# ======================================================================================

def register(builders):
    builders.update({"blade": build_blade, "gun": build_gun, "bow": build_bow})
    gk.PARTS.update(GIFTS)


if __name__ == "__main__":
    # python tools/blender/lines_weapons.py parts: the six gifts, as parts
    if sys.argv[1:] == ["parts"]:
        gk.PARTS.update(GIFTS)
        for feature in GIFTS:
            gk.build_part(feature)
    else:
        print("usage: python tools/blender/lines_weapons.py parts   (the forms are built by genius_lines.py blade|gun|bow)")
