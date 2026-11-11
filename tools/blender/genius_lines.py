"""WILDLINE genius lines: a body of its own for every form on a tree (docs/genius-lines.md).

A line is a thing that changes: the Starter, its three Paths, their Advancements and the
Finals are each a different creature to look at. What a form looks like is data, the `body` of its node
in data/genius-bases/<base>.json; a form wears everything its parent wears unless it says
otherwise, so something of each stage is carried into the next. This file reads those and
builds one model a form, in Blender, where the game looks for it:

    python tools/blender/genius_lines.py wolf                 # every form of the Wolf
    python tools/blender/genius_lines.py wolf wolf-red-maw    # only these forms of it
    python tools/blender/genius_lines.py --all                # every base that has a builder

Output: game/assets/genius/forms/<form id>.glb. The game wears it in place of the base's
body (game/scripts/genius/genius_body.gd); a form without one wears its base's body and
parts as before.

A body's `body`, on the wolf's rig (the keys every builder here understands are in
docs/genius-lines.md, "A body, as data"):
    build   proportions against the stage's own (legs, girth, chest, waist, neck, nape, head,
            muzzle, jaw, ears, tail, brush, body, pitch, stance)
    ears, eyes, maw, ruff, spine, tail, flags, armor, carry, paws, aura
            what it has grown or been given: a style, or [style, size], or a list of them
    coat    how its partner's coat is worn on it (the game shifts the colours; nothing here)

Conventions are the genius kit's (genius_kit.py): Z up, facing -Y, left is +X; materials
named field_* glow in the partner's Shape colour; fur_dark, fur_light and fur_ruff are the
partner's own coat; sockets ride the bones. A body also carries `ref_top`, an empty at the
crown of its head: the game stands it that tall, and what it has grown above that (a crest,
a lamp on a pole) stands above its instar's height, not inside it.
"""
import json
import math
import os
import sys

import bpy
import bmesh  # noqa: I001  (bpy brings it)
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE, STAND  # noqa: E402

ROOT = kit.ROOT
OUT = os.path.join(ROOT, "game", "assets", "genius", "forms")
BASES = os.path.join(ROOT, "data", "genius-bases")

# what the forms are made of that the kit's palette did not have: muted, a value apart
PALETTE.update({
    "fur_pale": ((0.6, 0.56, 0.48), 0.9, 0.0), "fur_mask": ((0.03, 0.028, 0.03), 0.9, 0.0), "fur_grey": ((0.27, 0.265, 0.26), 0.9, 0.0),
    "hide_maw": ((0.13, 0.025, 0.025), 0.6, 0.0), "hide_tongue": ((0.42, 0.12, 0.11), 0.5, 0.0),
    "slate": ((0.19, 0.2, 0.23), 0.85, 0.0), "slate_light": ((0.37, 0.38, 0.41), 0.85, 0.0),
    "shade_smoke": ((0.1, 0.095, 0.11), 1.0, 0.0), "hide_scar": ((0.6, 0.48, 0.44), 0.6, 0.0), "iron_bristle": ((0.15, 0.15, 0.17), 0.4, 0.8),
    "hide_baby": ((0.2, 0.185, 0.18), 0.8, 0.0), "hide_baby_dark": ((0.09, 0.082, 0.08), 0.8, 0.0), "hide_baby_pale": ((0.56, 0.52, 0.46), 0.8, 0.0),
    "cloth_stripe": ((0.34, 0.12, 0.08), 0.95, 0.0), "cloth_watch": ((0.17, 0.2, 0.3), 0.95, 0.0),
    "slate_dark": ((0.085, 0.09, 0.105), 0.85, 0.0),
})
# The Wolf's first names for five of these, which the other families' files still ask for
# (the Wolf itself wears the names above: each says what it is made of, docs/style.md).
PALETTE.update({
    "smoke": ((0.1, 0.095, 0.11), 1.0, 0.0), "maw": ((0.13, 0.025, 0.025), 0.6, 0.0), "tongue": ((0.42, 0.12, 0.11), 0.5, 0.0),
    "scar": ((0.6, 0.48, 0.44), 0.6, 0.0), "star": ((0.8, 0.78, 0.7), 0.4, 0.0), "wool_stripe": ((0.34, 0.12, 0.08), 0.95, 0.0),
})


def log(*a):
    print("[genius_lines]", *a)


def opt(v, default_size=1.0):
    """A slot's value as (style, size): "mane", ["mane", 1.3] or None."""
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


# ======================================================================================
# The wolf's rig: the four-legged lines
# ======================================================================================

import beast_kit as bk  # noqa: E402

HEAD = ("Head", "Ear1.L", "Ear1.R")
FEET = (("fl", "FF.L", "FrontLowerLeg.L"), ("fr", "FF.R", "FrontLowerLeg.R"), ("bl", "FFB.L", "BackLowerLeg.L"), ("br", "FFB.R", "BackLowerLeg.R"))


class Anat:
    """Where things are on a reshaped body, read once before anything is grown on it."""

    def __init__(self, r):
        self.r = r
        b = r.bone
        self.eye, self.nose = kit._eye(r), kit._nose(r)
        # the eye it was born with: how big it is and the way it faces (its left one)
        self.eye_r, self.eye_n = 0.07, Vector((0.74, -0.66, -0.12)).normalized()
        me, R3 = r.mesh.data, r.M.to_3x3()
        born = [p for p in me.polygons if "eyes" in me.materials[p.material_index].name.lower() and (r.M @ p.center).x > 0]
        if born:
            pts = [r.M @ me.vertices[v].co for p in born for v in p.vertices]
            self.eye_r = max(0.03, max(math.hypot(p.y - self.eye.y, p.z - self.eye.z) for p in pts))
            nn = sum(((R3 @ p.normal) * p.area for p in born), Vector())
            if nn.length > 1e-6:
                self.eye_n = nn.normalized()
        self.head, self.n1, self.n2, self.n3 = b("Head"), b("Neck1"), b("Neck2"), b("Neck3")
        self.t3, self.t2, self.t1, self.back = b("Torso3"), b("Torso2"), b("Torso"), b("Back")
        self.tail = [b("Tail%d" % i) for i in range(1, 9)]
        self.sh, self.hip = b("FrontUpperLeg.L"), b("BackUpperLeg.L")
        self.skull = r.top(self.head.y + 0.02, half_width=0.09, window=0.1)       # the crown, between the ears
        self.withers = r.top(self.t3.y)
        self.belly = r.bottom(self.t2.y, half_width=0.1)
        self.feet = {tag: b(foot) for tag, foot, _ in FEET}
        # the front of the chest, under the neck
        front = [p for p in r.world_verts() if abs(p.x) < 0.2 and self.sh.z - 0.1 < p.z < self.sh.z + 0.3 and p.y > self.n3.y]
        self.chest_y = min(p.y for p in front) if front else self.t3.y - 0.4
        # the neck's section at each of its bones: (y, centre z, half-width, half-height)
        self.neck = {}
        for name, k in (("Neck3", 0.86), ("Neck2", 0.95), ("Neck1", 1.05), ("Torso3", 1.2)):
            y = b(name).y
            top = r.top(y, half_width=0.15)
            rz = 0.31 * k
            self.neck[name] = (y, top - rz, 0.28 * k, rz)

        # the line of its back and the breadth of its flank, as they are before anything is
        # grown on it: a cloth is cut to the body, not to the mane under it
        self._ys = [self.n3.y - 0.3 + 0.1 * i for i in range(int((self.tail[1].y + 0.5 - self.n3.y) / 0.1) + 2)]
        self._tops = [r.top(y) for y in self._ys]
        self._sides = [r.side(y, t - 0.42) for y, t in zip(self._ys, self._tops)]

    def _at(self, table, y):
        i = (y - self._ys[0]) / 0.1
        i0 = max(0, min(len(table) - 2, int(i)))
        t = max(0.0, min(1.0, i - i0))
        return table[i0] * (1 - t) + table[i0 + 1] * t

    def top(self, y):
        return self._at(self._tops, y)

    def flank(self, y):
        return self._at(self._sides, y)


def _head(r):
    return r.family(*HEAD)


def stage(r, level):
    """The age of the body by its place on the line: the Starter is the young of its kind,
    a Path half-grown, an Advancement grown, a Final in its prime."""
    head, hb = _head(r), r.bone("Head")
    top = r.top(r.bone("Torso2").y)
    if level <= 1:
        r.scale(head, hb, 1.34)
        eye = kit._eye(r)
        r.deform(head, lambda p: Vector((p.x, eye.y + (p.y - eye.y) * 0.6, p.z)) if p.y < eye.y - 0.04 else p)
        r.leg_length(0.5)
        r.leg_girth(1.3)
        r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, 0.76)
        zc = (r.top(r.bone("Torso2").y) + r.bottom(r.bone("Torso2").y, half_width=0.1)) / 2
        r.scale(bk.TORSO, (0, 0, zc), (1.16, 1.0, 1.12))
        r.lengthen_chain(r.family("Tail1"), [], 0.58)
        r.scale(r.family("Tail1"), r.bone("Tail1"), (1.25, 1.0, 1.25))
        for ear in ("Ear1.L", "Ear1.R"):
            r.scale(r.family(ear), r.bone(ear), 1.2)
        # one ear up and one still deciding
        r.rotate(r.family("Ear3.R"), r.bone("Ear3.R"), X, 1.5)
        _feet(r, 1.45)
        # and large round eyes (a body with a face makes its own, and they blink)
        if not _has(r, "face", *FACES):
            e = kit._eye(r)
            eyes = None
            for sgn in (1, -1):
                eyes = g.merge(eyes, g.ico((sgn * (e.x + 0.02), e.y - 0.01, e.z - 0.01), 0.1, sub=1, scale=(0.55, 1.0, 1.05)))
            _add(r, "young_eyes", eyes, "Head", field("eyes", 3.2))
    elif level == 2:
        r.scale(head, hb, 1.13)
        r.leg_length(-0.14)
        r.leg_girth(0.95)
        r.scale(bk.TORSO, (0, 0, top), (0.94, 1.0, 0.95))
        r.lengthen_chain(r.family("Tail1"), [], 0.9)
        _feet(r, 1.15)
    elif level == 3:
        r.scale(["Torso3", "Torso2"], (0, 0, top), (1.05, 1.0, 1.04))
    else:
        r.scale(["Torso3", "Torso2"], (0, 0, top), (1.14, 1.0, 1.1))
        n2 = r.bone("Neck2")
        r.scale(bk.NECK, (0, n2.y, n2.z - 0.15), (1.14, 1.0, 1.12))
        r.scale(head, hb, 1.05)
        r.leg_girth(1.1)
        r.lengthen_chain(r.family("Tail1"), [], 1.15)


def _feet(r, k, height=0.32):
    """Bigger (or smaller) paws: each foot about its own middle."""
    for tag, foot, _ in FEET:
        f = r.bone(foot)
        r.deform(r.legs(tag), lambda p, f=f: Vector((f.x + (p.x - f.x) * k, f.y + 0.1 + (p.y - f.y - 0.1) * k, p.z)) if p.z < height else p)


def build(r, b):
    """Its own proportions, against its stage's."""
    head = _head(r)
    top = r.top(r.bone("Torso2").y)
    if "body" in b:
        r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, b["body"])
    if "legs" in b:
        r.leg_length(-(b["legs"] - 1.0) * 1.4)
    if "girth" in b:
        r.leg_girth(b["girth"])
    if "chest" in b:
        k = b["chest"]
        r.scale(["Torso3", "Torso2"], (0, 0, top), (k, 1.0, 1.0 + (k - 1.0) * 0.8))
        for tag, s in (("fl", 1), ("fr", -1)):
            r.shift(r.legs(tag), (s * (k - 1.0) * 0.3, 0, 0))
    if "waist" in b:
        k = b["waist"]
        r.scale(["Torso", "Back"], (0, 0, top), (k, 1.0, 1.0 + (k - 1.0) * 0.9))
    if "neck" in b:
        r.lengthen_chain(list(bk.NECK), head, b["neck"])
    if "nape" in b:
        n2 = r.bone("Neck2")
        r.scale(bk.NECK, (0, n2.y, n2.z - 0.15), (b["nape"], 1.0, b["nape"]))
    if "head" in b:
        r.scale(head, r.bone("Head"), b["head"])
    if "muzzle" in b:
        eye = kit._eye(r)
        r.deform(head, lambda p: Vector((p.x, eye.y + (p.y - eye.y) * b["muzzle"], p.z)) if p.y < eye.y - 0.04 else p)
    if "jaw" in b:
        eye, nose = kit._eye(r), kit._nose(r)
        k = b["jaw"]
        r.deform(head, lambda p: Vector((p.x * (1 + (k - 1) * 0.45), p.y, nose.z + (p.z - nose.z) * k)) if p.y < eye.y + 0.1 and p.z < nose.z else p)
    if "ears" in b:
        k = b["ears"]
        for ear in ("Ear1.L", "Ear1.R"):
            r.scale(r.family(ear), r.bone(ear), (1.0 + (k - 1.0) * 0.45, 1.0, k))
    if "tail" in b:
        r.lengthen_chain(r.family("Tail1"), [], b["tail"])
    if "brush" in b:
        r.scale(r.family("Tail1"), r.bone("Tail1"), (b["brush"], 1.0, b["brush"]))
    if "pitch" in b:
        r.rotate(list(bk.NECK) + head, r.bone("Neck1"), X, b["pitch"])       # more lowers the head
    if "stance" in b:
        for tag, s in (("fl", 1), ("fr", -1), ("bl", 1), ("br", -1)):
            r.shift(r.legs(tag), (s * b["stance"], 0, 0))
    if "paws" in b:
        _feet(r, b["paws"])
    if "croup" in b:                 # its rump carried low (or, negative, high): all behind the shoulders, more the further back
        ys, yh, k = r.bone("Torso3").y, r.bone("Back").y, b["croup"]
        r.deform([], lambda p: Vector((p.x, p.y, 0.3 + (p.z - 0.3) * (1.0 - k * max(0.0, min(1.25, (p.y - ys) / (yh - ys)))))) if p.z > 0.3 else p, spatial=True)


def carriage(r, spec):
    """How it carries itself (the second pass: a different black shape), put on last, so that
    everything it has grown goes with it and nothing is measured on a turned head. Its `pose`
    is a list of [what, radians]: crane (its neck lowered; less than nothing raises it), nod
    (its muzzle down at the top of its neck; less lifts it), turn (its head to its left; less,
    to its right: a share at each joint of the neck), tilt (its head on one side), tail (its
    tail raised from the root; less, tucked), curl (each joint of its tail a little more than
    the last), side (its tail carried to one side). The clips it borrows move it from wherever
    it stands, so the head and the tail may be carried anyhow; its legs are left as they are
    (it must still walk)."""
    head = _head(r)
    chain = list(bk.NECK) + head
    for what, a in each(spec.get("pose")):
        if what == "crane":
            for i, (bone, share) in enumerate((("Neck1", 0.5), ("Neck2", 0.3), ("Neck3", 0.2))):
                r.rotate(chain[i:], r.bone(bone), X, a * share)
        elif what == "nod":
            r.rotate(head, r.bone("Head"), X, a)
        elif what == "turn":
            for i, (bone, share) in enumerate((("Neck1", 0.3), ("Neck2", 0.25), ("Neck3", 0.2), ("Head", 0.25))):
                r.rotate(chain[i:], r.bone(bone), Z, a * share)
        elif what == "tilt":
            fwd = (r.bone("Head") - r.bone("Neck3")).normalized()
            r.rotate(head, r.bone("Head"), fwd, a)
        elif what == "tail":
            r.rotate(r.family("Tail1"), r.bone("Tail1"), X, a)
        elif what == "curl":
            for i in range(2, 9):
                r.rotate(r.family("Tail%d" % i), r.bone("Tail%d" % i), X, a)
        elif what == "side":
            r.rotate(r.family("Tail1"), r.bone("Tail1"), Z, a)


# --- small builders ---------------------------------------------------------------------

# what is soft is shaded round (fur, cloth, smoke, light); what is hard keeps its planes
SOFT = ("fur", "cloth", "shade", "hide", "field", "cord", "leather", "wool", "smoke", "tongue", "maw", "scar")


def _add(r, name, geo, weights, material, smooth=None):
    if geo and geo[0]:
        if smooth is None:
            smooth = material.name.startswith(SOFT)
        kit._add(r, name, geo, weights, material, smooth=smooth)


def _weld(r):
    """One welded skin, shaded round (beast_kit's)."""
    r.weld()



def _spine_w(r, geo):
    """Weights for a piece that lies along the back: each point by where it is along the spine."""
    return [r.spine_weights(p.y) for p in geo[0]]


def _paint(r, pick, material):
    """The faces of the body that pass pick(centre, normal) take a material."""
    me = r.mesh.data
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    slot = [m.name for m in me.materials].index(material.name)
    R = r.M.to_3x3()
    n = 0
    for p in me.polygons:
        if pick(r.M @ p.center, (R @ p.normal).normalized()):
            p.material_index = slot
            n += 1
    return n


def _paint_on(r, bones, pick, material, share=0.55):
    """The faces carried by these bones that pass pick(centre, normal) take a material."""
    me = r.mesh.data
    w = r._weights(bones)
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    slot = [m.name for m in me.materials].index(material.name)
    R = r.M.to_3x3()
    n = 0
    for p in me.polygons:
        if sum(w[i] for i in p.vertices) / len(p.vertices) > share and pick(r.M @ p.center, (R @ p.normal).normalized()):
            p.material_index = slot
            n += 1
    return n


def _am(step=""):
    """Its Path's colour (docs/genius-lines.md, "A Path's colour"): accent, or a step of it."""
    return mat("accent" + ("_" + step if step else ""))


def _trim(r, default, step=""):
    """What a thing given to it is made of: its Path's colour where its body says `trim`,
    else what it always was (the Wolf's kin are built through here and say no such thing)."""
    return _am(step) if getattr(r, "_spec", {}).get("trim") else mat(default)


def _has(r, slot, *styles):
    """Whether the body being built has one of these styles in a slot."""
    return any(st.partition(":")[0] in styles for st, _ in each(getattr(r, "_spec", {}).get(slot)))


def _later(r, kind, what, items, pivot, bone, side="", n=None, solid=None, under=None):
    """A piece that moves by its name (docs/genius-lines.md, "What moves"): it is made as the
    body is, and put on its bone once the body has been brought to size. items are
    [(geometry, material), ...]; or solid is (geometry, [the material of each face]), for a
    thing of one closed skin and several materials (an eye). under: the name of a piece made
    before it that it rides (a lamp's light breathes inside the lamp that sways)."""
    if not hasattr(r, "_late"):
        return
    r._late.append({"kind": kind, "what": what, "items": items, "pivot": Vector(pivot), "bone": bone, "side": side, "n": n, "solid": solid, "under": under})


def _solid(name, geo, mats, smooth=True):
    """One mesh of several materials: mats[i] is the material of face i."""
    verts, faces = geo
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], [tuple(f) for f in faces])
    names = []
    for m in mats:
        if m.name not in names:
            names.append(m.name)
            me.materials.append(m)
    for p, m in zip(me.polygons, mats):
        p.material_index = names.index(m.name)
        p.use_smooth = smooth
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def _ring_blades(r, name, ring, bone, n, L, width, material, a0=0.02, a1=0.98, sweep=0.9, out=0.42, lift=0.05, belly=0.3, grow=1.0, alt=None, wobble=0.0):
    """Blades standing round a section of the neck (ring = y, centre z, half-width, half-height),
    from angle a0 to a1 (in half-turns: 0 is the left side, 0.5 the top, 1 the right), swept back."""
    y, zc, rx, rz = ring
    geo, geo2 = None, None
    for i in range(n):
        a = math.pi * (a0 + (a1 - a0) * i / max(1, n - 1))
        d = Vector((math.cos(a), 0, math.sin(a)))
        Li = L * (1.0 + wobble * math.sin(i * 2.4 + 0.7))
        base = Vector((rx * 0.82 * grow * d.x, y - 0.05, zc + rz * 0.82 * grow * d.z))
        tip = base + Vector((d.x * Li * out, Li * sweep, d.z * Li * out + lift))
        bl = g.blade(base, tip, width * (1.0 + 0.2 * (i % 2)), normal=d, belly=belly)
        if alt is not None and i % 2 == 1:
            geo2 = g.merge(geo2, bl)
        else:
            geo = g.merge(geo, bl)
    _add(r, name, geo, bone, material)
    if geo2:
        _add(r, name + "_b", geo2, bone, alt)


def _lock(base, out, L, width, lie=0.9, lift=0.2, droop=0.2, back=Y):
    """One lock of fur: it stands out a little from where it grows (out), lies back along the
    body, and falls at its tip."""
    base, out = V(base), V(out).normalized()
    mid = base + out * (L * lift) + V(back) * (L * lie * 0.5)
    tip = base + out * (L * lift * 0.3) + V(back) * (L * lie) - Z * (L * droop)
    return g.tongue([base, mid, tip], [width * 0.85, width, width * 0.06], thick=0.16, normal=out)


def _locks(r, name, ring, bone, n, L, width, material, a0=0.04, a1=0.96, lie=0.9, lift=0.13, droop=0.2, grow=1.0, alt=None, wobble=0.3, seed=0.0):
    """Fur round a section of the neck (ring = y, centre z, half-width, half-height), from angle
    a0 to a1 (in half-turns: 0 is its left side, 0.5 the top, 1 its right): locks, no two the
    same length, so that its edge is broken as fur's is (the second pass, rule 4)."""
    y, zc, rx, rz = ring
    geo, geo2 = None, None
    for i in range(n):
        a = math.pi * (a0 + (a1 - a0) * (i + 0.22 * math.sin(i * 5.1 + seed)) / max(1, n - 1))
        d = Vector((math.cos(a), 0, math.sin(a)))
        Li = L * (1.0 + wobble * math.sin(i * 2.4 + 0.7 + seed))
        base = Vector((rx * 0.84 * grow * d.x, y - 0.04, zc + rz * 0.84 * grow * d.z))
        lock = _lock(base, d, Li, width * (1.0 + 0.25 * math.sin(i * 3.7 + seed)), lie=lie, lift=lift, droop=droop * (0.35 + 0.65 * abs(d.x)))
        if alt is not None and i % 2 == 1:
            geo2 = g.merge(geo2, lock)
        else:
            geo = g.merge(geo, lock)
    _add(r, name, geo, bone, material)
    if geo2:
        _add(r, name + "_b", geo2, bone, alt)


def _cheeks(r, A, size, material):
    """The fur of its cheeks: a wolf's face is broad under the ears."""
    e = A.eye
    geo = None
    for s in (1, -1):
        for i, (dy, dz, L) in enumerate(((0.2, -0.16, 0.3), (0.26, -0.04, 0.26), (0.14, -0.27, 0.24))):
            y, z = e.y + dy, e.z + dz
            b0 = Vector((s * (r.side(y, z, window=0.08) - 0.03), y, z))
            geo = g.merge(geo, _lock(b0, Vector((s, 0, -0.25)), L * size, 0.2 * size, lie=0.8, lift=0.22, droop=0.3 + 0.12 * i))
    _add(r, "cheeks", geo, "Head", material)


def _sheet(r, name, ys, section, material, thick=0.035):
    """A cloth laid along the back: section(y) gives the outer points across it, left to right;
    the cloth has a thickness, so it is seen from both sides, and it moves with the spine."""
    rings, weights = [], []
    for y in ys:
        outer = [V(p) for p in section(y)]
        mid = sum(outer, Vector()) / len(outer)
        inner = []
        for p in outer:
            d = (mid - p)
            d = d.normalized() if d.length > 1e-6 else Vector((0, 0, -1))
            inner.append(p + d * thick)
        ring = outer + list(reversed(inner))
        rings.append(ring)
        weights.extend([r.spine_weights(y)] * len(ring))
    geo = g.loft(rings, caps=True)
    _add(r, name, geo, weights, material)


def _lantern(at, s, glow_name="lamp", strength=3.2):
    """A small caged lamp hanging from `at`: [(geometry, material), ...]."""
    at = V(at)
    c = at + Vector((0, 0, -s * 1.5))
    items = [
        (g.tube([at, at + Vector((0, 0, -s * 0.55))], s * 0.07, n=5), mat("metal_iron")),
        (g.lathe([(s * 0.12, s * 0.95), (s * 0.5, s * 0.6), (s * 0.56, s * 0.52)], n=6, centre=c), mat("metal_brass")),
        (g.lathe([(s * 0.52, -s * 0.62), (s * 0.3, -s * 0.8)], n=6, centre=c), mat("metal_brass")),
        (g.ico(c, s * 0.36, sub=1, scale=(1, 1, 1.25)), field(glow_name, strength)),
    ]
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p = c + Vector((math.cos(a) * s * 0.5, math.sin(a) * s * 0.5, 0))
        items.append((g.tube([p + Vector((0, 0, -s * 0.62)), p + Vector((0, 0, s * 0.55))], s * 0.05, n=4), mat("metal_iron")))
    return items


def _add_items(r, name, items, bone):
    for i, (geo, material) in enumerate(items):
        _add(r, "%s_%d" % (name, i), geo, bone, material)


# --- what a body grows -------------------------------------------------------------------

def grow_ears(r, A, style, size):
    L, Rr = r.family("Ear1.L"), r.family("Ear1.R")
    if style == "tunnel":            # large, cupped, turned to the front
        for ear in ("Ear1.L", "Ear1.R"):
            r.scale(r.family(ear), r.bone(ear), (1.0 + 0.9 * size, 1.0, 1.0 + 1.1 * size))
    elif style == "tall":            # narrow and very tall
        for ear in ("Ear1.L", "Ear1.R"):
            r.scale(r.family(ear), r.bone(ear), (0.9, 1.0, 1.0 + 1.0 * size))
    elif style == "back":            # laid back along the neck
        for ear in ("Ear1.L", "Ear1.R"):
            r.rotate(r.family(ear), r.bone(ear), X, -0.95)
            r.scale(r.family(ear), r.bone(ear), (0.9, 1.0 + 0.3 * size, 1.0))
    elif style == "split":           # one to the front, one always turned behind
        r.scale(L, r.bone("Ear1.L"), (1.25, 1.0, 1.0 + 0.5 * size))
        r.scale(Rr, r.bone("Ear1.R"), (1.25, 1.0, 1.0 + 0.5 * size))
        r.rotate(L, r.bone("Ear1.L"), X, 0.3)
        r.rotate(Rr, r.bone("Ear1.R"), X, -1.0)
    elif style == "torn":            # one cut short
        r.scale(Rr, r.bone("Ear1.R"), (1.0, 1.0, 0.55))
    elif style == "hound":           # long, hanging
        for ear, s in (("Ear1.L", 1), ("Ear1.R", -1)):
            r.scale(r.family(ear), r.bone(ear), (1.3, 1.0, 1.0 + 0.7 * size))
            r.rotate(r.family(ear), r.bone(ear), Y, s * 2.3)


def _jaw_line(r, A):
    y = A.nose.y + 0.3
    zb, zt = r.bottom(y, half_width=0.14, window=0.1), r.top(y, half_width=0.14, window=0.1)
    return zb, zt


def grow_maw(r, A, style, size):
    head = "Head"
    zb, zt = _jaw_line(r, A)
    if style in ("open", "glow"):
        # the lower jaw swings down about its hinge; what tears between the jaws is the mouth
        angle = 0.34 * size
        hinge = Vector((0, A.eye.y + 0.1, zb + 0.5 * (zt - zb)))
        zcut = zb + 0.42 * (zt - zb)
        Rm = Matrix.Rotation(angle, 3, X)
        me = r.mesh.data
        wh = r._weights(_head(r))
        moved = set()
        for i, v in enumerate(me.vertices):
            p = r.M @ v.co
            if wh[i] > 0.5 and p.y < hinge.y and p.z < zcut:
                v.co = r.Minv @ (hinge + Rm @ (p - hinge))
                moved.add(i)
        maw = mat("hide_maw")
        if maw.name not in [m.name for m in me.materials]:
            me.materials.append(maw)
        slot = [m.name for m in me.materials].index(maw.name)
        for poly in me.polygons:
            k = sum(1 for i in poly.vertices if i in moved)
            if 0 < k < len(poly.vertices):
                poly.material_index = slot
        # the tongue, and the dark behind it
        t0 = Vector((0, hinge.y - 0.05, zcut - 0.05))
        tip = hinge + Rm @ (Vector((0, A.nose.y + 0.12, zcut - 0.02)) - hinge)
        _add(r, "tongue", g.tongue([t0, (t0 + tip) / 2 + Vector((0, 0, 0.03)), tip], [0.2, 0.18, 0.1], thick=0.3, normal=Z), head, mat("hide_tongue"))
        if style == "glow":
            c = Vector((0, hinge.y - 0.12, zcut - 0.02))
            if _own(r):
                _later(r, "pulse", "throat", [(g.ico(c, 0.13 * size, sub=2, scale=(1.0, 1.3, 0.8)), field("throat", 3.6))], c, "Head")
            else:
                _add(r, "throat_light", g.ico(c, 0.13 * size, sub=1, scale=(1.0, 1.3, 0.8)), head, field("throat", 3.6))
        # the lower fangs
        low = None
        for s in (1, -1):
            b0 = hinge + Rm @ (Vector((s * 0.1, A.nose.y + 0.2, zcut - 0.02)) - hinge)
            low = g.merge(low, g.cone(b0, b0 + Vector((0, 0.02, 0.14 * size)), 0.035, n=5))
        _add(r, "fangs_low", low, head, mat("bone"))
    if style in ("fangs", "open", "glow"):
        up = None
        zc = zb + 0.45 * (zt - zb)
        for s in (1, -1):
            b0 = Vector((s * 0.115, A.nose.y + 0.19, zc + 0.02))
            up = g.merge(up, g.cone(b0, b0 + Vector((0, -0.03, -0.22 * size)), 0.045 * (0.8 + 0.2 * size), n=5))
            if size > 1.2:
                b1 = Vector((s * 0.14, A.nose.y + 0.36, zc + 0.02))
                up = g.merge(up, g.cone(b1, b1 + Vector((0, -0.02, -0.13 * size)), 0.035, n=5))
        _add(r, "fangs", up, head, mat("bone"))


def grow_eyes(r, A, style, size):
    e = A.eye
    near = lambda c: min((c - Vector((sg * e.x, e.y, e.z))).length for sg in (1, -1))  # noqa: E731
    if style == "dark":              # dark all round the eyes, and paler round that, so it shows on any coat
        _paint(r, lambda c, n: near(c) < 0.5 * size and c.y < A.head.y + 0.1, mat("fur_pale"))
        _paint(r, lambda c, n: near(c) < 0.3 * size and c.y < A.head.y + 0.05, mat("fur_mask"))
    elif style == "lamp":            # eyes that give the lamp back
        geo, rim = None, None
        for s in (1, -1):
            c = Vector((s * (e.x + 0.05), e.y - 0.02, e.z + 0.01))
            geo = g.merge(geo, g.ico(c, 0.17 * size, sub=1, scale=(0.5, 1.0, 1.0)))
            rim = g.merge(rim, g.loft([g.ring(c + Vector((s * -0.01, 0, 0)), 0.25 * size, 0.25 * size, n=8, u=Y, v=Z), g.ring(c + Vector((s * 0.06, 0, 0)), 0.19 * size, 0.19 * size, n=8, u=Y, v=Z)], caps=True))
        _paint(r, lambda c, n: near(c) < 0.45 and c.y < A.head.y + 0.05, mat("fur_mask"))
        if _has(r, "face", *FACES):       # its face makes the eyes themselves, and they blink
            return
        _add(r, "lamp_rims", rim, "Head", mat("metal_brass"))
        _add(r, "lamp_eyes", geo, "Head", field("eyes", 4.6))
    elif style == "old":             # older than the rest of it: pale brows, a grey muzzle
        geo = None
        for s in (1, -1):
            for i in range(2):
                b0 = Vector((s * (e.x - 0.01 + 0.03 * i), e.y - 0.02 + 0.08 * i, e.z + 0.07))
                geo = g.merge(geo, g.blade(b0, b0 + Vector((s * (0.08 + 0.04 * i), 0.2 + 0.05 * i, 0.07 + 0.03 * i)) * size, 0.07, normal=Vector((s, 0, 0.6))))
        if not _has(r, "face", *FACES):       # (a face's own mark over the eye goes pale and long)
            _add(r, "brows", geo, "Head", mat("fur_pale"))
        _paint(r, lambda c, n: c.y < A.nose.y + 0.34, mat("fur_grey"))
    elif style == "third":           # a third eye-mark, pale, in the fur of its brow
        c = Vector((0, e.y + 0.02, e.z + 0.2))
        up = Vector((0, 0.42, 0.9)).normalized()
        _add(r, "third_mark", g.blade(c - up * 0.2 * size, c + up * 0.26 * size, 0.2 * size, normal=Vector((0, -0.9, 0.42)), belly=0.45), "Head", _trim(r, "fur_pale", "pale"))
        _add(r, "third_eye", g.ico(c + Vector((0, -0.05, 0.02)), 0.065 * size, sub=1, scale=(0.75, 0.6, 1.25)), "Head", field("eyes", 4.0))
    elif style == "far":             # bright, long, under a dark brow
        geo, vis = None, None
        for s in (1, -1):
            c = Vector((s * (e.x + 0.02), e.y - 0.02, e.z))
            geo = g.merge(geo, g.ico(c, 0.085 * size, sub=1, scale=(0.6, 1.7, 0.7)))
            vis = g.merge(vis, g.box(c + Vector((s * 0.02, 0.0, 0.11)), (0.2, 0.42, 0.05), rot=(0.25, s * -0.5, 0)))
        if not _has(r, "face", *FACES):       # (a face makes its eyes long and lowers its lids)
            _add(r, "far_eyes", geo, "Head", field("eyes", 4.0))
            _add(r, "brow_shade", vis, "Head", mat("horn"))
    elif style == "second":          # a second pair, small, above and behind the first
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.ico((s * (e.x - 0.035), e.y + 0.2, e.z + 0.13), 0.05 * size, sub=1, scale=(0.7, 1.0, 0.75)))
        _add(r, "second_eyes", geo, "Head", field("eyes", 3.0))


def grow_ruff(r, A, style, size):
    # the Wolf's own ruffs, as fur with a broken edge (the second pass): tuft, fur, shag
    if style == "tuft":              # a pup's: one soft row
        _locks(r, "ruff", A.neck["Neck2"], "Neck2", 9, 0.36 * size, 0.26, mat("fur_ruff"), lift=0.2, lie=0.75, droop=0.12, seed=1.0)
        _cheeks(r, A, 0.8 * size, mat("fur_light"))
    elif style == "scruff":          # a lean one's: a short row at the root of its neck, and its cheeks
        _locks(r, "ruff", A.neck["Neck1"], "Neck1", 10, 0.38 * size, 0.24, mat("fur_ruff"), a0=0.0, a1=1.0, lift=0.14, droop=0.2, seed=0.6)
        _cheeks(r, A, 0.9 * size, mat("fur_light"))
    elif style == "fur":             # a grown wolf's ruff: three rows of locks, and its cheeks
        for row, (bone, n, L) in enumerate((("Neck1", 10, 0.56), ("Neck2", 9, 0.48), ("Neck3", 8, 0.38))):
            _locks(r, "ruff_%d" % row, A.neck[bone], bone, n + 2, L * size, 0.27, mat("fur_ruff") if row != 1 else mat("fur_light"),
                   a0=0.0, a1=1.0, lift=0.15, droop=0.24, seed=row * 1.7)
        _cheeks(r, A, size, mat("fur_light"))
    elif style == "shag":            # a full mane of it, down to the shoulders and under the throat
        rows = (("Neck3", 9, 0.5, 0.0), ("Neck2", 11, 0.66, -0.16), ("Neck1", 12, 0.8, -0.26), ("Torso3", 12, 0.78, -0.2))
        for row, (bone, n, L, under) in enumerate(rows):
            _locks(r, "mane_%d" % row, A.neck[bone], bone, n + 2, L * size, 0.33, mat("fur_ruff"), a0=under, a1=1.0 - under,
                   lift=0.17, droop=0.34, alt=mat("fur_light") if row % 2 else None, wobble=0.34, seed=row * 2.3)
        _cheeks(r, A, 1.25 * size, mat("fur_ruff"))
        fl = None                     # the forelock, between the ears
        for i, x in enumerate((-0.1, 0.02, 0.12)):
            b0 = Vector((x, A.head.y - 0.06, A.skull - 0.04))
            fl = g.merge(fl, _lock(b0, Vector((x * 2, -0.2, 1)), (0.34 + 0.06 * i) * size, 0.18, lie=0.8, lift=0.4, droop=0.0))
        _add(r, "forelock", fl, "Head", mat("fur_ruff"))
    elif style == "pup":
        _ring_blades(r, "ruff", A.neck["Neck2"], "Neck2", 9, 0.3 * size, 0.2, mat("fur_ruff"), sweep=0.7, out=0.6)
    elif style == "quills":
        for row, (bone, n, L) in enumerate((("Neck1", 13, 0.5), ("Neck2", 12, 0.44), ("Neck3", 11, 0.36))):
            _ring_blades(r, "ruff_%d" % row, A.neck[bone], bone, n, L * size, 0.18, mat("fur_ruff") if row != 1 else mat("fur_light"))
    elif style == "mane":            # a full mane, down to the shoulders and under the throat
        rows = (("Neck3", 13, 0.5, 0.0), ("Neck2", 15, 0.62, -0.18), ("Neck1", 17, 0.74, -0.3), ("Torso3", 17, 0.7, -0.22))
        for row, (bone, n, L, under) in enumerate(rows):
            _ring_blades(r, "mane_%d" % row, A.neck[bone], bone, n + 4, L * size, 0.27, mat("fur_ruff"), a0=under, a1=1.0 - under,
                         sweep=0.8, out=0.42, lift=-0.14, belly=0.4, alt=mat("fur_light") if row % 2 else None, wobble=0.12)
        # the forelock, between the ears
        fl = None
        for i, x in enumerate((-0.1, 0.0, 0.1)):
            b0 = Vector((x, A.head.y - 0.08, A.skull - 0.03))
            fl = g.merge(fl, g.blade(b0, b0 + Vector((x * 0.6, 0.36 * size, 0.2 * size)), 0.17, normal=Vector((x * 2, -0.3, 1))))
        _add(r, "forelock", fl, "Head", mat("fur_ruff"))
    elif style == "crown":           # a pale ring of fur standing up round its head
        y = A.head.y + 0.16
        ring = (y, A.skull - 0.36, 0.36, 0.36)
        _ring_blades(r, "crown", ring, "Head", 15, 0.5 * size, 0.2, mat("fur_pale"), a0=-0.12, a1=1.12, sweep=0.22, out=1.0, lift=0.0, belly=0.36, wobble=0.1,
                     alt=_am("light") if _own(r) and r._spec.get("trim") else None)
        if size > 1.15:               # a second, longer ring behind the first
            _ring_blades(r, "crown2", (y + 0.16, ring[1], 0.38, 0.38), "Neck3", 13, 0.72 * size, 0.24, mat("fur_cream"), a0=-0.1, a1=1.1, sweep=0.34, out=1.0, lift=0.0, belly=0.36, wobble=0.14)
    elif style == "slate":           # the fur over its shoulders gone grey and hard as slate
        top = A.withers
        spots = [((0, A.t3.y - 0.18, top + 0.02), (0.3, 0.34, 0.075), 0.0, "Torso3"), ((0, A.t3.y + 0.3, r.top(A.t3.y + 0.3) + 0.02), (0.3, 0.34, 0.075), 0.0, "Torso3"),
                 ((0, A.n1.y - 0.05, r.top(A.n1.y - 0.05, half_width=0.15) + 0.02), (0.25, 0.28, 0.07), 0.0, "Neck1")]
        for s in (1, -1):
            spots += [((s * 0.3, A.t3.y + 0.02, top - 0.14), (0.26, 0.36, 0.07), s * 0.75, "Torso3"), ((s * 0.47, A.t3.y + 0.0, top - 0.48), (0.24, 0.36, 0.07), s * 1.3, "Torso3"),
                      ((s * 0.29, A.t3.y + 0.48, top - 0.16), (0.22, 0.3, 0.06), s * 0.8, "Torso2")]
        for i, (c, sc, roll, bone) in enumerate(spots):
            k = 0.8 + 0.2 * size
            geo = g.ico(c, 1.0, sub=1, scale=(sc[0] * k, sc[1] * k, sc[2] * (1.0 + 0.5 * (size - 1.0))), rot=(0.0, roll, 0.0))
            _add(r, "slate_%d" % i, geo, bone, mat(("slate_dark" if i % 2 else "slate") if _own(r) else ("slate" if i % 2 else "slate_light")))
    elif style == "frost":           # white rime standing on its ruff
        for row, (bone, n, L) in enumerate((("Neck1", 12, 0.6), ("Neck2", 11, 0.5), ("Neck3", 9, 0.38))):
            _ring_blades(r, "rime_%d" % row, A.neck[bone], bone, n, L * size, 0.15, mat("ice_pale"), sweep=0.5, out=0.85, lift=0.1, belly=0.2, alt=mat("ice"), wobble=0.3)
    elif style == "ember":           # the ruff glows from underneath, like coals under ash
        for row, (bone, n, L) in enumerate((("Neck1", 13, 0.58), ("Neck2", 12, 0.5), ("Neck3", 11, 0.4))):
            _ring_blades(r, "ember_in_%d" % row, A.neck[bone], bone, n, L * 0.72 * size, 0.2, field("ember", 2.4), grow=0.96)
            _ring_blades(r, "ember_out_%d" % row, A.neck[bone], bone, n - 1, L * size, 0.19, mat("coal"), grow=1.08, a0=0.06, a1=0.94, alt=mat("fur_grey"))


def _cape(r, A, name, y0, y1, drop, material, steps=9, off=0.05, flare=0.1, hem=0.06):
    """A cloth over the back: round the top of the body to where the flank is widest, then
    hanging to its hem."""
    def section(y):
        top = A.top(y)
        zc = top - 0.42
        w = A.flank(y) + off
        t = (y - y0) / max(1e-6, y1 - y0)
        pts = []
        for j in range(11):
            u = -1.0 + 2.0 * j / 10
            a, sgn = abs(u), (1 if u > 0 else -1)
            if a <= 0.5:
                th = (a / 0.5) * math.pi / 2
                pts.append(Vector((sgn * w * math.sin(th), y, zc + (top + off - zc) * math.cos(th))))
            else:
                d = (a - 0.5) / 0.5
                pts.append(Vector((sgn * (w + flare * d), y, zc - d * (drop + hem * math.sin(t * 11.0 + j * 1.7)))))
        return pts
    ys = [y0 + (y1 - y0) * i / steps for i in range(steps + 1)]
    _sheet(r, name, ys, section, material)


def grow_spine(r, A, style, size):
    y0, y1 = A.t3.y + 0.05, A.tail[1].y
    if style == "seam":
        r.fin("seam_spine", A.t3.y, A.tail[1].y, 0.03, field("seam", 1.6), thickness=0.07, steps=16, sink=0.05)
    elif style in ("ridge", "quills", "iron", "frost", "ember"):
        n = {"ridge": 13, "quills": 9, "iron": 12, "frost": 11, "ember": 12}[style]
        L = {"ridge": 0.3, "quills": 0.55, "iron": 0.34, "frost": 0.42, "ember": 0.36}[style] * size
        m = {"ridge": mat("fur_ruff"), "quills": mat("fur_ruff"), "iron": mat("iron_bristle"), "frost": mat("ice_pale"), "ember": mat("coal")}[style]
        geo = None
        ws = []
        for i in range(n):
            t = i / (n - 1)
            y = (A.n2.y if style != "ridge" else A.n1.y) * (1 - t) + y1 * t
            Li = L * (1.0 - 0.45 * t) * (1.0 + 0.2 * math.sin(i * 2.1))
            b0 = Vector((0, y, r.top(y, half_width=0.12) - 0.04))
            bl = g.blade(b0, b0 + Vector((0, Li * 0.75, Li * 0.85)), 0.2, normal=X, belly=0.34)
            geo = g.merge(geo, bl)
            ws.extend([r.spine_weights(y)] * len(bl[0]))
        _add(r, "spine_" + style, geo, ws, m)
        if style == "ember":
            r.fin("seam_spine", A.t3.y, A.tail[1].y, 0.05, field("seam", 2.2), thickness=0.09, steps=16, sink=0.05)
    elif style == "crest":           # the Wolf's own: the fur of its back standing a little, lock over lock
        n = max(5, int(round(10 * size)))
        geo, ws = None, []
        for i in range(n):
            t = i / (n - 1)
            y = A.n1.y * (1 - t) + (y1 - 0.15) * t
            b0 = Vector((0.03 * math.sin(i * 2.6), y, r.top(y, half_width=0.12) - 0.06))
            lk = _lock(b0, Z, (0.4 - 0.12 * t) * (0.6 + 0.4 * size) * (1.0 + 0.25 * math.sin(i * 2.1)), 0.22, lie=0.9, lift=0.42 * size, droop=0.06)
            geo = g.merge(geo, lk)
            ws.extend([r.spine_weights(y)] * len(lk[0]))
        _add(r, "spine_crest", geo, ws, mat("fur_ruff"))
    elif style == "plates":
        n = 6
        for i in range(n):
            t = i / (n - 1)
            y = y0 + (y1 - 0.2 - y0) * t
            w = 0.36 * (1.0 - 0.3 * t) * (0.8 + 0.2 * size)
            geo = g.box((0, y, r.top(y) + 0.035), (w, 0.3, 0.07), rot=(0.12, 0, 0))
            _add(r, "plate_%d" % i, geo, [r.spine_weights(y)] * 8, mat(("slate_dark" if i % 2 else "slate") if _own(r) else ("slate" if i % 2 else "slate_light")))
    elif style == "smoke" and _own(r):   # its fur smokes faintly with the weather: broad wisps, and they move
        for i in range(6):
            t = i / 5
            y = A.n1.y * (1 - t) + (y1 - 0.25) * t
            x = 0.14 * math.sin(i * 1.9)
            p0 = Vector((x, y, r.top(y, half_width=0.2) - 0.08))
            k = size * (0.62 + 0.22 * math.sin(i * 1.3 + 1.0))
            pts = [p0, p0 + Vector((x * 0.5, 0.2, 0.3)) * k, p0 + Vector((-x * 1.4, 0.34, 0.66)) * k, p0 + Vector((x * 0.8, 0.62, 0.95)) * k]
            tg = g.tongue(pts, [0.34, 0.3, 0.2, 0.03], thick=0.5, normal=X)
            bone = max(r.spine_weights(y), key=lambda bw: bw[1])[0]
            _later(r, "flick", "smoke%d" % i, [(tg, field("smoke", 0.7) if i == 3 else mat("shade_smoke"))], p0, bone)
    elif style == "smoke":           # its fur smokes faintly with the weather
        geo, lit = None, None
        ws, wl = [], []
        for i in range(9):
            t = i / 8
            y = A.n1.y * (1 - t) + (y1 - 0.2) * t
            x = 0.16 * math.sin(i * 1.9)
            p0 = Vector((x, y, r.top(y, half_width=0.2) - 0.06))
            k = size * (0.8 + 0.3 * math.sin(i * 1.3 + 1.0))
            pts = [p0, p0 + Vector((x * 0.5, 0.14, 0.3)) * k, p0 + Vector((-x, 0.42, 0.62)) * k, p0 + Vector((x * 0.6, 0.66, 0.98)) * k]
            tg = g.tongue(pts, [0.19, 0.16, 0.1, 0.02], thick=0.35, normal=X)
            if i == 4:
                lit = g.merge(lit, tg)
                wl.extend([r.spine_weights(y)] * len(tg[0]))
            else:
                geo = g.merge(geo, tg)
                ws.extend([r.spine_weights(y)] * len(tg[0]))
        _add(r, "smoke", geo, ws, mat("shade_smoke"))
        _add(r, "smoke_lit", lit, wl, field("smoke", 0.7))
    elif style == "stars":           # a night's worth of pale points along its back
        geo, ws = None, []
        for i in range(16):
            t = i / 15
            y = A.n1.y * (1 - t) + y1 * t
            x = 0.24 * math.sin(i * 2.7 + 0.4)
            z = r.top(y, half_width=0.3) - 0.03 - 0.45 * abs(x)
            st = g.ico((x * 1.25, y, z), 0.035 + 0.012 * (i % 3), sub=0)
            geo = g.merge(geo, st)
            ws.extend([r.spine_weights(y)] * len(st[0]))
        _add(r, "stars", geo, ws, field("stars", 2.0))


def reshape_tail(r, style, size):
    fam = r.family("Tail1")
    if style == "whip":              # thin and long
        r.scale(fam, r.bone("Tail1"), (0.42, 1.0, 0.42))
        r.lengthen_chain(fam, [], 1.3 * size)
    elif style == "short":
        r.lengthen_chain(fam, [], 0.55)


def grow_tail(r, A, style, size):
    tb = [r.bone("Tail%d" % i) for i in range(1, 9)]
    if style == "flag":              # feathered underneath, like a banner
        geo = None
        for i in range(1, 8):
            b0 = tb[i] + Vector((0, 0, -0.04))
            L = (0.42 + 0.12 * math.sin(i * 1.3)) * size
            geo = g.blade(b0, b0 + Vector((0, 0.16, -L)), 0.3, normal=X, belly=0.4)
            _add(r, "tailflag_%d" % i, geo, "Tail%d" % (i + 1), _trim(r, "fur_pale", "light") if i >= 5 else mat("fur_light"))
    elif style == "smoke" and _own(r):   # it goes to smoke at the end: broad wisps, and they move
        for i in range(4, 8):
            b0 = tb[i]
            k = size * (0.6 + 0.12 * i)
            pts = [b0, b0 + Vector((0.05, 0.2, 0.18)) * k, b0 + Vector((-0.09, 0.4, 0.44)) * k, b0 + Vector((0.05, 0.5, 0.7)) * k]
            _later(r, "flick", "tailsmoke%d" % (i - 4), [(g.tongue(pts, [0.3, 0.26, 0.17, 0.03], thick=0.5, normal=X), mat("shade_smoke"))], b0, "Tail%d" % (i + 1))
    elif style == "smoke":           # it goes to smoke at the end
        for i in range(4, 8):
            b0 = tb[i]
            k = size * (0.7 + 0.15 * i)
            pts = [b0, b0 + Vector((0.05, 0.2, 0.16)) * k, b0 + Vector((-0.08, 0.42, 0.42)) * k, b0 + Vector((0.04, 0.5, 0.72)) * k]
            _add(r, "tailsmoke_%d" % i, g.tongue(pts, [0.17, 0.15, 0.09, 0.02], thick=0.35, normal=X), "Tail%d" % (i + 1), mat("shade_smoke"))
    elif style == "lamp":            # a tail-lamp, like the last car's
        tip = tb[7]
        post = [tip, tip + Vector((0, 0.1, 0.28 * size)), tip + Vector((0, 0.3, 0.36 * size))]
        _add(r, "taillamp_arm", g.tube(post, 0.035, n=5), "Tail8", mat("metal_iron"))
        _hang_lamp(r, "taillamp", post[-1], 0.17 * size, "Tail8")
    elif style == "rings":           # pale rings round it
        for i in (2, 4, 6):
            c = tb[i]
            rad = max(0.08, r.top(c.y, half_width=0.2, window=0.1) - c.z) + 0.035
            d = (tb[min(7, i + 1)] - tb[i - 1]).normalized() if _own(r) else Y      # (the Wolf's lie across its tail however it is carried)
            u = X if abs(d.dot(X)) < 0.9 else Z
            v = d.cross(u).normalized()
            u = v.cross(d).normalized()
            if _own(r):
                rad = 0.115 + 0.012 * (6 - i)
            nn = 12 if _own(r) else 8
            geo = g.loft([g.ring(c - d * 0.07, rad, rad, n=nn, u=u, v=v), g.ring(c + d * 0.07, rad, rad, n=nn, u=u, v=v)], caps=True)
            _add(r, "tailring_%d" % i, geo, "Tail%d" % (i + 1), _trim(r, "fur_pale", "pale"))
    elif style == "ember":           # a coal at the end of it
        tip = tb[7]
        _add(r, "tail_coal", g.ico(tip + Vector((0, 0.05, 0)), 0.15 * size, sub=1, scale=(0.9, 1.3, 0.9)), "Tail8", field("ember", 2.6))
        geo = None
        for k in range(5):
            a = k * 2 * math.pi / 5
            d = Vector((math.cos(a), 0, math.sin(a)))
            geo = g.merge(geo, g.blade(tip + d * 0.07, tip + d * 0.16 + Vector((0, 0.42 * size, 0)), 0.14, normal=d))
        _add(r, "tail_ash", geo, "Tail8", mat("coal"))


def grow_flags(r, A, style, size):
    """Long flags of fur from the shoulders, streaming back like wings."""
    m = field("flags", 1.6) if style == "light" else mat("fur_pale" if style == "pale" else "fur_light")
    for s, tag in ((1, "l"), (-1, "r")):
        root = Vector((s * 0.3, A.t3.y, A.withers - 0.2))
        geo, under = None, None
        for i in range(6):
            L = (1.0 + 0.3 * i) * size
            b0 = root + Vector((0, 0.1 * i, -0.035 * i))
            tip = b0 + Vector((s * (0.34 - 0.03 * i), L * 0.94, 0.36 - 0.11 * i))
            bl = g.blade(b0, tip, 0.2 + 0.035 * i, normal=Vector((s * 0.8, 0, 0.6)), belly=0.3, curl=-0.05)
            if i % 2:
                under = g.merge(under, bl)
            else:
                geo = g.merge(geo, bl)
        _add(r, "flag_" + tag, geo, _spine_w(r, geo), m)
        _add(r, "flag2_" + tag, under, _spine_w(r, under), _trim(r, "fur_ruff") if style != "light" else m)


def grow_armor(r, A, style, size):
    e = A.eye
    if style == "brow":              # a flat plate across the brow
        c = Vector((0, e.y + 0.08, e.z + 0.2))
        _add(r, "brow_plate", g.box(c, (0.56 * size, 0.56, 0.08), rot=(0.5, 0, 0)), "Head", mat("slate" if _own(r) else "slate_light"))
        _add(r, "brow_ridge", g.box(c + Vector((0, -0.02, 0.05)), (0.1, 0.6, 0.08), rot=(0.5, 0, 0)), "Head", _trim(r, "slate"))
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.box(c + Vector((s * 0.3, 0.1, -0.12)), (0.08, 0.4, 0.3), rot=(0.5, 0, s * 0.1)))
        _add(r, "brow_cheeks", geo, "Head", mat("slate_dark" if _own(r) else "slate"))
    elif style == "chest":           # a flat plate across the chest
        c = Vector((0, A.chest_y - 0.05, A.sh.z + 0.12))
        _add(r, "chest_plate", g.box(c, (0.74 * size, 0.09, 0.66 * size), rot=(-0.22, 0, 0)), "Torso3", mat("slate" if _own(r) else "slate_light"))
        _add(r, "chest_boss", g.box(c + Vector((0, -0.06, 0.0)), (0.2, 0.08, 0.5 * size), rot=(-0.22, 0, 0)), "Torso3", _trim(r, "slate"))
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.box(c + Vector((s * 0.43 * size, 0.16, 0.04)), (0.09, 0.44, 0.56 * size), rot=(-0.1, 0, s * -0.5)))
        _add(r, "chest_wings", geo, "Torso3", mat("slate_dark" if _own(r) else "slate"))
    elif style == "chain":           # a length of chain at its throat
        y, zc, rx, rz = A.neck["Neck2"]
        geo = None
        n = 14
        for i in range(n):
            a = 2 * math.pi * i / n
            c = Vector((math.cos(a) * (rx + 0.03), y, zc + math.sin(a) * (rz + 0.03)))
            geo = g.merge(geo, g.ico(c, 0.075 * size, sub=1, scale=(1.0, 0.5, 1.0) if i % 2 else (0.55, 1.0, 1.0)))
        p = p0 = Vector((0, y - 0.03, zc - rz - 0.03))
        hang = None
        for i in range(5):
            p = p + Vector((0, 0.0, -0.12 * size))
            hang = g.merge(hang, g.ico(p, 0.07 * size, sub=1, scale=(1.0, 0.5, 1.0) if i % 2 else (0.5, 1.0, 1.0)))
        weight = g.lathe([(0.02, 0.1), (0.1, 0.02), (0.13, -0.1), (0.05, -0.16)], n=8 if _own(r) else 6, centre=p + Vector((0, 0, -0.14 * size)))
        if _own(r):                  # what hangs of it swings, and rings on the low note
            _add(r, "chain", geo, "Neck2", mat("metal_iron"))
            _later(r, "sway", "chain", [(hang, mat("metal_iron")), (weight, _trim(r, "metal_iron_light"))], p0, "Neck2")
        else:
            _add(r, "chain", g.merge(geo, hang), "Neck2", mat("metal_iron"))
            _add(r, "chain_weight", weight, "Neck2", mat("metal_iron_light"))
    elif style == "harness":         # a strap round the chest and a tag
        y = A.t3.y + 0.3
        zt, zb = r.top(y), r.bottom(y, half_width=0.1)
        zc, rz, rx = (zt + zb) / 2, (zt - zb) / 2 + 0.035, r.side(y, (zt + zb) / 2) + 0.035
        geo = g.loft([g.ring((0, y - 0.07, zc), rx, rz, n=12, u=X, v=Z), g.ring((0, y + 0.07, zc), rx, rz, n=12, u=X, v=Z)], caps=False)
        _add(r, "harness", geo, "Torso3", _trim(r, "leather"))
        _add(r, "harness_tag", g.ico((0, A.chest_y - 0.04, A.sh.z + 0.2), 0.09, sub=1, scale=(1.0, 0.4, 1.2)), "Torso3", mat("metal_brass"))
    elif style == "scars":           # healed lines across the coat
        m = _trim(r, "hide_scar")
        for i, (side, ya, yb, za, zb) in enumerate(((1, -0.6, 0.5, 0.25, -0.1), (1, -0.3, 0.7, -0.05, 0.2), (-1, -0.7, 0.2, 0.05, 0.3), (-1, -0.1, 0.8, 0.3, -0.05), (1, 0.2, 0.9, -0.2, -0.3))):
            zmid = (A.withers + A.belly) / 2
            r.flank_line("scar_%d" % i, A.t3.y + ya + 0.6, A.t3.y + yb + 0.6, lambda t, za=za, zb=zb, zmid=zmid: zmid + 0.25 + za + (zb - za) * t, m, height=0.05 * size, depth=0.06, side=side)
        geo = g.box((e.x * 0.5, e.y - 0.25, e.z - 0.02), (0.05, 0.36, 0.05), rot=(0.3, 0, 0.5))
        _add(r, "scar_muzzle", geo, "Head", m)


def _own(r):
    """Whether the body being built is the Wolf's own (another animal on its rig is built
    through here too, and what its styles do for it is not changed)."""
    return getattr(r, "_own", False)


def _hang_lamp(r, name, at, s, bone, strength=3.4, glow_name="lamp"):
    """A lamp hung on the body. The Wolf's own sways on its hook, its light breathes, and its
    cap is enamelled in its Path's colour; another animal's hangs as it always did."""
    if not _own(r):
        _add_items(r, name, _lantern(at, s, glow_name, strength), bone)
        return
    at = V(at)
    c = at + Vector((0, 0, -s * 1.5))
    cap, iron, brass = _trim(r, "metal_brass"), mat("metal_iron"), mat("metal_brass")
    items = [
        (g.tube([at, at + Vector((0, 0, -s * 0.55))], s * 0.07, n=5), iron),
        (g.lathe([(s * 0.12, s * 0.95), (s * 0.5, s * 0.6), (s * 0.56, s * 0.52)], n=8, centre=c), cap),
        (g.lathe([(s * 0.52, -s * 0.62), (s * 0.3, -s * 0.8)], n=8, centre=c), brass),
    ]
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p = c + Vector((math.cos(a) * s * 0.5, math.sin(a) * s * 0.5, 0))
        items.append((g.tube([p + Vector((0, 0, -s * 0.62)), p + Vector((0, 0, s * 0.55))], s * 0.05, n=4), iron))
    _later(r, "sway", name, items, at, bone)
    _later(r, "pulse", name + "_light", [(g.ico(c, s * 0.36, sub=2, scale=(1, 1, 1.25)), field(glow_name, strength))], c, bone, under="sway_" + name)


def _hung(r, name, items, pivot, bone):
    """Things that hang from the body: on the Wolf's own they sway about where they hang from."""
    if _own(r):
        _later(r, "sway", name, items, pivot, bone)
    else:
        _add_items(r, name, items, bone)


def grow_carry(r, A, style, size):
    y, zc, rx, rz = A.neck["Neck1"]
    throat = Vector((0, (A.n1.y + A.n2.y) / 2, r.bottom((A.n1.y + A.n2.y) / 2, half_width=0.08)))
    if style == "lamp":              # a lamp riding at its collar
        _collar(r, A, _trim(r, "leather", "dark"))
        _hang_lamp(r, "lamp", throat + Vector((0, -0.02, 0.02)), 0.2 * size, "Neck1")
    elif style == "book":            # a closed book hanging at its neck
        _collar(r, A, _trim(r, "leather_dark", "dark"))
        c = Vector((0, A.chest_y - 0.1, A.sh.z + 0.22))
        s = size
        items = [(g.box(c, (0.42 * s, 0.14 * s, 0.52 * s), rot=(-0.18, 0, 0)), mat("leather_dark")),
                 (g.box(c + Vector((0, 0.0, -0.02 * s)), (0.36 * s, 0.1 * s, 0.53 * s), rot=(-0.18, 0, 0)), mat("paper")),
                 (g.box(c + Vector((0, -0.075 * s, 0.0)), (0.46 * s, 0.03, 0.09 * s), rot=(-0.18, 0, 0)), _trim(r, "metal_brass", "light")),
                 (g.ico(c + Vector((0, -0.09 * s, 0.0)), 0.07 * s, sub=1, scale=(1, 0.5, 1)), field("seal", 1.8))]
        if _own(r):                  # and a ribbon to mark its place
            p0 = c + Vector((0.1 * s, 0.0, -0.26 * s))
            items.append((g.tongue([p0, p0 + Vector((0.02, -0.02, -0.14 * s)), p0 + Vector((-0.02, -0.03, -0.3 * s))], [0.07 * s, 0.07 * s, 0.05 * s], thick=0.3, normal=-Y), _am("")))
        geo = None
        for sx in (1, -1):
            geo = g.merge(geo, g.tube([c + Vector((sx * 0.17 * s, 0.02, 0.26 * s)), Vector((sx * (rx + 0.02), y - 0.04, zc - rz * 0.4))], 0.03, n=5))
        if _own(r):                  # the straps swing with the book
            items.append((geo, mat("leather")))
            _later(r, "sway", "book", items, Vector((0, y - 0.04, zc - rz * 0.4)), "Torso3")
        else:
            for i, (ig, im) in enumerate(items):
                _add(r, ("book", "book_pages", "book_clasp", "book_seal")[i], ig, "Torso3", im)
            _add(r, "book_straps", geo, "Neck1", mat("leather"))
    elif style in ("tags", "knots"):  # a cord of tokens, or of knots
        _collar(r, A, _trim(r, "cord", "dark"))
        geo, geo2 = None, None
        n = 9 if style == "tags" else 5
        for i in range(n):
            a = math.pi * (1.12 + 0.76 * i / (n - 1))
            b0 = Vector((math.cos(a) * (rx + 0.04), y, zc + math.sin(a) * (rz + 0.04)))
            if style == "tags":
                bl = g.blade(b0, b0 + Vector((0, -0.03, -0.22 * size)), 0.13 * size, normal=Y, belly=0.55)
                if i % 2:
                    geo2 = g.merge(geo2, bl)
                else:
                    geo = g.merge(geo, bl)
            else:
                L = (0.3 + 0.12 * (i % 2)) * size
                geo = g.merge(geo, g.tube([b0, b0 + Vector((0, -0.02, -L))], 0.022, n=4))
                for k in range(1, 3 + i % 2):
                    geo2 = g.merge(geo2, g.ico(b0 + Vector((0, -0.02, -L * k / (2.5 + i % 2))), 0.045, sub=0))
        if _own(r):                  # each hangs from the cord, and they swing together
            m1 = mat("bone") if style == "tags" else _am("dark")
            m2 = _am("") if style == "tags" else _am("light")
            _later(r, "sway", style, [(geo, m1), (geo2, m2)], Vector((0, y, zc - rz * 0.3)), "Neck1")
        else:
            _add(r, style, geo, "Neck1", mat("bone") if style == "tags" else mat("cord"))
            _add(r, style + "_b", geo2, "Neck1", mat("metal_brass") if style == "tags" else mat("fur_pale"))
    elif style == "post":            # a lamp on a post, carried on its back
        foot = Vector((0, A.t3.y + 0.12, A.withers - 0.08))
        topp = foot + Vector((0, 0.16, 1.5 * size))
        arm = topp + Vector((0, -0.4 * size, 0.12 * size))
        _add(r, "post", g.tube([foot, topp, arm], [0.055, 0.045, 0.035], n=8 if _own(r) else 6), "Torso3", mat("wood"))
        _add(r, "post_foot", g.lathe([(0.16, 0.0), (0.1, 0.1), (0.06, 0.16)], n=8 if _own(r) else 6, centre=foot), "Torso3", mat("metal_brass"))
        if _own(r):                  # a band of its Path's colour round the post, as a post on the line is painted
            for i, h in enumerate((0.42, 0.56)):
                c = foot + (topp - foot) * h
                _add(r, "post_band_%d" % i, g.lathe([(0.062, -0.06), (0.062, 0.06)], n=8, centre=c), "Torso3", _am("light" if i else ""))
        _hang_lamp(r, "postlamp", arm, 0.24 * size, "Torso3", strength=3.8)
    elif style == "cloak":           # a watch-cloak over the shoulders and back
        y1 = A.t1.y if size < 1.2 else A.back.y + 0.1
        _cape(r, A, "cloak", A.n1.y, y1, 0.5 * size, _trim(r, "cloth_watch", "dark"))
        if _own(r):                  # banded at its hem
            _cape(r, A, "cloak_band", y1 - 0.3, y1 - 0.1, 0.5 * size, _am("light"), steps=3, off=0.062)
        _add(r, "cloak_clasp", g.ico(Vector((0, A.chest_y - 0.02, A.sh.z + 0.42)), 0.08, sub=1, scale=(1, 0.5, 1)), "Torso3", mat("metal_brass"))
    elif style == "shroud":          # a cloak of shadow, tattered at the hem
        _cape(r, A, "shroud", A.n1.y, A.back.y + 0.2, 0.62 * size, _trim(r, "shade_edge", "deep"), hem=0.14, flare=0.14)
    elif style == "rug":             # a woven rug across its back
        _cape(r, A, "rug", A.t3.y + 0.12, A.t1.y + 0.3, 0.4 * size, mat("cloth_wool"), hem=0.0, flare=0.03)
        if _own(r):                  # woven in bands of its Path's colour
            y0, span = A.t3.y + 0.12, A.t1.y + 0.3 - (A.t3.y + 0.12)
            for i, (ta, tb, step) in enumerate(((0.14, 0.3, ""), (0.44, 0.56, "light"), (0.7, 0.86, ""))):
                _cape(r, A, "rug_stripe_%d" % i, y0 + span * ta, y0 + span * tb, 0.385 * size, _am(step), steps=2, hem=0.0, flare=0.034, off=0.066)
        else:
            _cape(r, A, "rug_stripe", A.t3.y + 0.42, A.t1.y + 0.0, 0.34 * size, mat("cloth_stripe"), steps=5, hem=0.0, flare=0.04, off=0.07)
    elif style == "bell":            # a bell at its throat
        _collar(r, A, _trim(r, "leather", "dark"))
        c = throat + Vector((0, -0.02, -0.16 * size))
        _hung(r, "bell", [(g.lathe([(0.03, 0.14), (0.09, 0.1), (0.13, -0.04), (0.17, -0.12)], n=7, centre=c), mat("metal_brass"))], throat, "Neck1")
    elif style == "bird":            # a small bird that has taken it for a stone, in its Path's colour: it looks about
        s = size
        c = Vector((0.0, A.head.y + 0.04, A.skull + 0.1 * s))
        hc = c + Vector((0, -0.11 * s, 0.1 * s))
        items = [(g.ico(c, 0.115 * s, sub=2, scale=(0.82, 1.25, 0.85)), _am("")),
                 (g.ico(c + Vector((0, -0.05 * s, -0.03 * s)), 0.09 * s, sub=1, scale=(0.75, 1.0, 0.8)), _am("pale")),
                 (g.ico(hc, 0.07 * s, sub=2), _am("")),
                 (g.cone(hc + Vector((0, -0.055 * s, -0.005)), hc + Vector((0, -0.14 * s, -0.02 * s)), 0.024 * s, n=5), mat("beak")),
                 (g.blade(c + Vector((0, 0.1 * s, 0.03 * s)), c + Vector((0, 0.34 * s, 0.1 * s)), 0.1 * s, normal=Z), _am("dark"))]
        for sx in (1, -1):
            items.append((g.blade(c + Vector((sx * 0.085 * s, -0.06 * s, 0.03 * s)), c + Vector((sx * 0.1 * s, 0.2 * s, 0.0)), 0.12 * s, normal=Vector((sx, 0, 0.3))), _am("dark")))
            items.append((g.ico(hc + Vector((sx * 0.045 * s, -0.035 * s, 0.015 * s)), 0.016 * s, sub=0), mat("eye_dark")))
        _later(r, "turn", "bird", items, c + Vector((0, 0, -0.09 * s)), "Head")


def _collar(r, A, material):
    y, zc, rx, rz = A.neck["Neck1"]
    n = 16 if _own(r) else 12
    geo = g.loft([g.ring((0, y - 0.05, zc), rx + 0.04, rz + 0.04, n=n, u=X, v=Z), g.ring((0, y + 0.05, zc), rx + 0.05, rz + 0.05, n=n, u=X, v=Z)], caps=False)
    _add(r, "collar", geo, "Neck1", material)


def grow_paws(r, A, style, size):
    if style == "set":               # broad, planted, clawed
        _feet(r, 1.0 + 0.3 * size)
        for tag, foot, bone in FEET if not _has(r, "feet", "toes") else ():
            f = r.bone(foot)
            cl = None
            for dx in (-0.09, 0.0, 0.09):
                b0 = Vector((f.x + dx, f.y - 0.02, 0.07))
                cl = g.merge(cl, g.cone(b0, b0 + Vector((dx * 0.3, -0.2 * size, -0.06)), 0.04, n=5))
            _add(r, "claws_" + tag, cl, bone, mat("claw"))
        _legs_painted(r, A, 0.34, mat("fur_mask"))
    elif style == "grease":          # rail grease on all four feet
        _legs_painted(r, A, 0.62 * size, mat("coal"))
    elif style == "shade":           # its feet go to shadow and make no sound
        _legs_painted(r, A, 0.7 * size, mat("shade"))
        for tag, foot, bone in FEET:
            f = r.bone(foot)
            geo = None
            for k in range(3):
                a = k * 2.1
                b0 = Vector((f.x + 0.1 * math.cos(a), f.y + 0.1 + 0.1 * math.sin(a), 0.1))
                geo = g.merge(geo, g.tongue([b0, b0 + Vector((0.03, 0.12, 0.2)), b0 + Vector((-0.03, 0.22, 0.42))], [0.14, 0.1, 0.02], thick=0.35, normal=X))
            _add(r, "footshade_" + tag, geo, bone, mat("shade_edge"))
    elif style == "frost":           # rime to the hock
        _legs_painted(r, A, 0.55 * size, mat("ice_pale"))


def _legs_painted(r, A, height, material):
    legs = r._weights(r.legs())
    me = r.mesh.data
    keep = {i for i, v in enumerate(me.vertices) if legs[i] > 0.5}
    slot_of = lambda p: all(i in keep for i in p.vertices)  # noqa: E731
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    slot = [m.name for m in me.materials].index(material.name)
    for p in me.polygons:
        if slot_of(p) and (r.M @ p.center).z < height:
            p.material_index = slot


def grow_aura(r, A, style, size):
    if style == "windows":           # its coat holds a light, like a window seen from the road
        zmid = (A.withers + A.belly) / 2 + 0.1
        for s, tag in ((1, "l"), (-1, "r")):
            for i, y in enumerate((A.t3.y + 0.42, A.t3.y + 0.95)):
                x = s * (r.side(y, zmid) + 0.012)
                w, h = 0.34 * size, 0.42 * size
                _add(r, "window_%s%d" % (tag, i), g.box((x, y, zmid), (0.03, w, h)), [r.spine_weights(y)] * 8, field("window", 1.5))
                bars = g.merge(g.box((x + s * 0.012, y, zmid), (0.03, 0.035, h + 0.04)), g.box((x + s * 0.012, y, zmid + 0.04), (0.03, w + 0.04, 0.035)),
                               g.box((x + s * 0.008, y, zmid + h / 2 + 0.02), (0.035, w + 0.07, 0.05)), g.box((x + s * 0.008, y, zmid - h / 2 - 0.02), (0.035, w + 0.07, 0.05)))
                _add(r, "windowbars_%s%d" % (tag, i), bars, [r.spine_weights(y)] * len(bars[0]), mat("fur_mask"))
    elif style == "motes":           # small lights that keep it company
        spots = ((0.5, A.n2.y + 0.1, A.skull + 0.3), (-0.42, A.t3.y + 0.2, A.withers + 0.5), (0.3, A.t2.y + 0.2, A.withers + 0.36))
        for i, c in enumerate(spots[: max(1, int(round(2 * size)))]):
            c = Vector(c)
            tail = g.tongue([c + Vector((0, 0.06, 0)), c + Vector((0.03, 0.26, -0.06)), c + Vector((-0.02, 0.46, -0.02))], [0.13, 0.09, 0.02], thick=0.4, normal=X)
            if _own(r):
                _later(r, "bob", "mote%d" % i, [(g.ico(c, 0.09, sub=2), field("mote", 3.0)), (tail, mat("shade_edge"))], c, "Torso3" if i else "Neck2")
                continue
            _add(r, "mote_%d" % i, g.ico(c, 0.09, sub=1), "Torso3" if i else "Neck2", field("mote", 3.0))
            _add(r, "mote_tail_%d" % i, tail, "Torso3" if i else "Neck2", mat("shade_edge"))
    elif style == "followers":       # smaller lights that walk in its tracks, one behind another
        y0 = A.tail[3].y
        for i in range(max(1, int(round(3 * size)))):
            rad = 0.2 - 0.03 * i
            c = Vector((0.14 * math.sin(i * 2.2 + 0.5), y0 + 0.5 * i, rad * 1.05))
            items = [(g.ico(c, rad, sub=2, scale=(0.9, 1.1, 0.9)), field("mote", 3.0))]
            for sx in (1, -1):       # each with the ears of what it will be
                b0 = c + Vector((sx * rad * 0.45, -rad * 0.5, rad * 0.62))
                items.append((g.blade(b0, b0 + Vector((sx * rad * 0.3, -rad * 0.1, rad * 0.75)), rad * 0.6, normal=-Y), mat("shade_edge")))
            items.append((g.tongue([c + Vector((0, rad * 0.8, 0)), c + Vector((0.03, rad * 1.6, rad * 0.3)), c + Vector((-0.02, rad * 2.1, rad * 0.9))], [rad * 0.7, rad * 0.5, rad * 0.1], thick=0.5, normal=X), mat("shade_edge")))
            _later(r, "bob", "follower%d" % i, items, c, "Body")
    elif style == "cold":            # a cold light in its chest, and ice where its breath should be
        c = Vector((0, A.chest_y - 0.02, A.sh.z + 0.16))
        if _own(r):                  # (the Wolf's breathes)
            _later(r, "pulse", "core", [(g.ico(c, 0.14 * size, sub=2, scale=(0.6, 0.5, 1.5)), field("core", 3.0))], c, "Torso3")
        else:
            _add(r, "cold_core", g.ico(c, 0.14 * size, sub=1, scale=(0.6, 0.5, 1.5)), "Torso3", field("core", 3.0))
        geo = None
        for i in range(7):
            y = A.t3.y + 0.2 + 0.24 * i
            b0 = Vector((0.06 * math.sin(i * 2.0), y, r.bottom(y, half_width=0.1) + 0.03))
            geo = g.merge(geo, g.cone(b0, b0 + Vector((0, 0.02, -(0.2 + 0.1 * math.sin(i * 1.7)) * size)), 0.045, n=5))
        _add(r, "icicles", geo, _spine_w(r, geo), mat("ice"))
        jaw = None
        zb, _ = _jaw_line(r, A)
        for i in range(3):
            b0 = Vector((0.07 * (i - 1), A.nose.y + 0.3 + 0.1 * i, zb + 0.02))
            jaw = g.merge(jaw, g.cone(b0, b0 + Vector((0, 0, -0.16 * size)), 0.035, n=5))
        _add(r, "icicles_jaw", jaw, "Head", mat("ice_pale"))
    elif style == "crescent":        # a pale crescent standing over its head
        c = Vector((0, A.head.y - 0.12, A.skull + 0.34 * size)) if _own(r) else Vector((0, A.head.y + 0.1, A.skull + 0.2 * size))
        geo = None
        n = 9
        for i in range(n):
            a = math.pi * (0.08 + 0.84 * i / (n - 1))
            d = Vector((math.cos(a), 0, math.sin(a)))
            w = 0.16 * math.sin(math.pi * (i + 0.5) / n) + 0.03
            geo = g.merge(geo, g.box(c + d * 0.42 * size + Vector((0, 0, -0.25 * size)), (0.2 * size, 0.07, w), rot=(0, -(a - math.pi / 2), 0)))
        if _own(r):
            _later(r, "bob", "crescent", [(geo, _trim(r, "fur_pale", "pale")), (g.ico(c + Vector((0, 0, 0.02)), 0.07 * size, sub=2), field("moon", 3.0))], c, "Torso3")
        else:
            _add(r, "crescent", geo, "Head", mat("fur_pale"))
            _add(r, "crescent_light", g.ico(c + Vector((0, 0, 0.02)), 0.07 * size, sub=1), "Head", field("moon", 3.0))


# --- its Path's colour on its body, a face, and feet (the second pass) ----------------------

def _across(A, y, off=0.03, reach=0.5, n=9):
    """Points over the top of the body at y, from flank to flank (reach: how far down each
    side, as a share of the half-turn from the spine to the widest of the flank)."""
    top = A.top(y)
    zc = top - 0.42
    w = A.flank(y) + off
    pts = []
    for j in range(n):
        th = (-1.0 + 2.0 * j / (n - 1)) * math.pi / 2 * (reach / 0.5)
        pts.append(Vector((w * math.sin(th), y, zc + (top + off - zc) * math.cos(th))))
    return pts


def grow_marks(r, A, style, size):
    """Where a wolf wears its Path's colour (the second pass, rule 1). A style may name a step
    of the colour after a colon: "saddle:light", "bars:pale". Some are the body's own faces
    painted (saddle, blanket, mask, muzzle, blaze, socks, stockings, bands, tailtip, ears,
    bib, under); some are fur laid on it, for an edge the body's own faces cannot draw
    (stripe, bars, chevrons, dapple, rings, hackles)."""
    style, _, step = style.partition(":")
    m = _am(step)
    torso, head, legs = list(bk.TORSO), _head(r), r.legs()
    ya, yb = A.t3.y, A.back.y
    zm = (A.withers + A.belly) / 2
    if style == "saddle":            # over the shoulders and along the back
        _paint_on(r, torso + ["Neck1"], lambda c, n: n.z > 0.62 - 0.3 * size and ya - 0.3 <= c.y <= yb + 0.2, m, share=0.4)
    elif style == "blanket":         # the same, down to the middle of the flank
        _paint_on(r, torso, lambda c, n: c.z > zm + 0.16 - 0.16 * size and n.z > -0.25 and ya - 0.2 <= c.y <= yb + 0.25, m, share=0.4)
    elif style == "mask":            # across the eyes and down the top of the muzzle
        _paint_on(r, head, lambda c, n: c.y < A.eye.y + 0.14 * size and c.z > A.eye.z - 0.1 and n.z > -0.2, m)
    elif style == "muzzle":          # the whole muzzle, as if it had been dipped
        _paint_on(r, head, lambda c, n: c.y < A.nose.y + 0.3 * size, m)
    elif style == "blaze":           # a stripe from the nose to between the ears
        _paint_on(r, head + ["Neck3"], lambda c, n: abs(c.x) < 0.09 * size and n.z > 0.2, m, share=0.4)
    elif style == "socks":
        _paint_on(r, legs, lambda c, n: c.z < 0.36 * size, m)
    elif style == "stockings":
        _paint_on(r, legs, lambda c, n: c.z < 0.74 * size, m)
    elif style == "bands":           # two rings round each leg
        _paint_on(r, legs, lambda c, n: 0.16 < c.z < 0.16 + 0.17 * size or 0.5 < c.z < 0.5 + 0.17 * size, m)
    elif style == "tailtip":
        _paint_on(r, r.family("Tail%d" % (6 if size < 0.9 else 5 if size < 1.3 else 3)), lambda c, n: True, m, share=0.5)
    elif style == "ears":            # the inside of its ears
        _paint_on(r, r.family("Ear1.L") + r.family("Ear1.R"), lambda c, n: n.y < -0.1, m, share=0.5)
    elif style == "bib":             # the front of its chest
        _paint_on(r, torso + list(bk.NECK), lambda c, n: n.y < -0.2 and c.z < A.sh.z + 0.5 * size and c.y < A.t3.y + 0.15, m, share=0.4)
    elif style == "under":           # its belly, its throat and the inside of its legs
        _paint_on(r, torso + list(bk.NECK), lambda c, n: n.z < -0.3, m, share=0.4)
        _paint_on(r, legs, lambda c, n: c.z > 0.3 and n.x * c.x < 0 and abs(n.x) > 0.35, m)
    elif style == "stripe":          # a stripe laid down its spine
        r.fin("mark_stripe", A.n1.y - 0.1, A.tail[0].y + 0.1, 0.014, m, thickness=0.2 * size, steps=18, sink=0.03)
    elif style == "bars":            # bars across its back
        n = max(2, int(round(4 * size)))
        y0, y1 = ya + 0.05, yb + 0.05
        for i in range(n):
            y = y0 + (y1 - y0) * (i + 0.5) / n
            w = 0.085 + 0.02 * math.sin(i * 1.7)
            _sheet(r, "mark_bar_%d" % i, [y - w, y, y + w], lambda yy, y=y, w=w: _across(A, yy, off=0.022, reach=0.5 * (0.72 if abs(yy - y) > 1e-6 else 0.86)), m, thick=0.03)
    elif style == "chevrons":        # chevrons down each flank, pointing the way it runs
        n = max(2, int(round(3 * size)))
        for sgn, tag in ((1, "l"), (-1, "r")):
            for i in range(n):
                y0 = ya + 0.15 + (yb - ya - 0.2) * i / max(1, n - 1)
                r.flank_line("mark_chev_%s%d_a" % (tag, i), y0, y0 + 0.24, lambda t: zm + 0.3 - 0.2 * t, m, height=0.075, depth=0.05, steps=4, side=sgn)
                r.flank_line("mark_chev_%s%d_b" % (tag, i), y0, y0 + 0.24, lambda t: zm - 0.1 + 0.2 * t, m, height=0.075, depth=0.05, steps=4, side=sgn)
    elif style == "dapple":          # dapples on the shoulder and the haunch
        geo, ws = None, []
        spots = [(ya + 0.02, 0.22, 0.11), (ya + 0.24, 0.02, 0.085), (ya + 0.4, 0.26, 0.07), (yb - 0.38, 0.2, 0.075), (yb - 0.12, 0.3, 0.1), (yb + 0.02, 0.04, 0.09), (yb - 0.3, -0.06, 0.06)]
        for sgn in (1, -1):
            for y, dz, rad in spots[: max(3, int(round(len(spots) * min(1.0, size))))]:
                z = zm + dz
                d = g.ico((sgn * (r.side(y, z) + 0.004), y, z), rad * (0.8 + 0.2 * size), sub=1, scale=(0.22, 1.0, 1.0))
                geo = g.merge(geo, d)
                ws.extend([r.spine_weights(y)] * len(d[0]))
        _add(r, "mark_dapple", geo, ws, m, smooth=True)
    elif style == "rings":           # rings round its tail
        tb = A.tail
        for i in (2, 4, 6):
            c = tb[i]
            rad = max(0.08, r.top(c.y, half_width=0.2, window=0.1) - c.z) + 0.03
            d = (tb[min(7, i + 1)] - tb[i - 1]).normalized()
            u = X
            v = d.cross(u).normalized()
            geo = g.loft([g.ring(c - d * 0.07, rad, rad, n=8, u=u, v=v), g.ring(c + d * 0.07, rad, rad, n=8, u=u, v=v)], caps=True)
            _add(r, "mark_ring_%d" % i, geo, "Tail%d" % (i + 1), m, smooth=True)
    elif style == "hackles":         # the fur along its neck and shoulders, standing in its colour
        geo, ws = None, []
        n = max(5, int(round(9 * size)))
        for i in range(n):
            t = i / (n - 1)
            y = A.n3.y * (1 - t) + (A.t3.y + 0.5) * t
            L = 0.3 * size * (1.0 - 0.3 * abs(t - 0.45)) * (1.0 + 0.2 * math.sin(i * 2.3))
            b0 = Vector((0, y, r.top(y, half_width=0.12) - 0.04))
            bl = g.blade(b0, b0 + Vector((0, L * 0.7, L * 0.9)), 0.21, normal=X, belly=0.34)
            geo = g.merge(geo, bl)
            ws.extend([r.spine_weights(y)] * len(bl[0]))
        _add(r, "mark_hackles", geo, ws, m, smooth=True)


# How each face looks (the second pass, rule 4). The game draws an ink line two pixels wide
# round every piece of a body, whatever its size, so a face is made of few pieces and large ones:
# an eye is one ball (its pupil and the light on it are its own faces, not pieces laid on it),
# and what is said round it is said by its lids and by a mark in its Path's colour.
#   r      the ball of its eye against the eye it was born with
#   sunk   how much of the ball is in the head
#   gaze   where it looks: out to its own side, ahead, up
#   pupil  the pupil's half-angle on the ball, in degrees
#   lid    how much of the eye its upper lid covers, and how the lid leans (more lowers its
#          inner end, as a frown does; less, its outer)
#   under  the same of its lower lid
#   mark   what its Path's colour does round the eye: "pips" over it, as a hound has (it looks
#          at who is here); a "slash" over it and a tear-line down the muzzle, as a courser has
#          (it looks at one thing); a crescent "under" it (it has not slept, and does not look
#          at you)
#   smile  how much the corner of its mouth turns up
FACES = {
    "young": {"r": 2.0, "sunk": 0.5, "gaze": (0.62, 0.74, 0.2), "pupil": 30, "lid": (0.0, 0.0), "under": (0.0, 0.0), "mark": None, "smile": 0.05},
    "open": {"r": 1.9, "sunk": 0.56, "gaze": (0.68, 0.7, 0.1), "pupil": 24, "lid": (0.14, -0.22), "under": (0.0, 0.0), "mark": "pips", "smile": 0.05},
    "fixed": {"r": 1.9, "sunk": 0.58, "gaze": (0.25, 0.96, -0.06), "pupil": 19, "lid": (0.3, 0.5), "under": (0.13, 0.2), "mark": "slash", "smile": -0.03},
    "aside": {"r": 1.9, "sunk": 0.58, "gaze": (0.78, -0.42, 0.34), "pupil": 22, "lid": (0.42, -0.08), "under": (0.0, 0.0), "mark": "under", "smile": 0.0},
}
DARK_COATS = ("night", "blood", "iron", "slate", "ember")


def _lens(c, n, u, v, a, b, t, sub=1):
    """A flattened ball lying on a skin: half-widths a along u and b along v, t thick along n."""
    c = V(c)
    vs, fs = g.ico((0, 0, 0), 1.0, sub=sub)
    if u.cross(v).dot(n) < 0:
        fs = [tuple(reversed(f)) for f in fs]
    return [c + u * (p.x * a) + v * (p.y * b) + n * (p.z * t) for p in vs], fs


def _eyeball(c, R, d, toward, pa, n=12):
    """The ball of an eye with its pole where it looks: (geometry, what each face is: "pupil",
    "glint" (the light on it, toward `toward`) or "iris"). One closed skin."""
    c, d = V(c), V(d).normalized()
    u, v = g._frame(d)
    rest = math.pi - 1.3 * pa
    ths = [0.4 * pa, 0.75 * pa, pa, 1.3 * pa, 1.3 * pa + rest * 0.3, 1.3 * pa + rest * 0.62]
    at = lambda th, k: d * math.cos(th) + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * math.sin(th)  # noqa: E731
    verts = [c + d * R] + [c + at(th, k) * R for th in ths for k in range(n)] + [c - d * R]
    t = V(toward) - d * V(toward).dot(d)
    spark = (d * math.cos(0.8 * pa) + t.normalized() * math.sin(0.8 * pa)).normalized() if t.length > 1e-6 else d

    def kind(th, k):
        way = at(th, k).normalized()
        return "glint" if way.angle(spark) < 0.5 * pa else ("pupil" if th < pa else "iris")

    faces, kinds = [], []
    for k in range(n):
        faces.append((0, 1 + k, 1 + (k + 1) % n))
        kinds.append("pupil")
    for i in range(len(ths) - 1):
        for k in range(n):
            a, b = 1 + i * n + k, 1 + i * n + (k + 1) % n
            faces.append((a, a + n, b + n, b))
            kinds.append(kind((ths[i] + ths[i + 1]) / 2, k + 0.5))
    last = 1 + (len(ths) - 1) * n
    for k in range(n):
        faces.append((last + k, len(verts) - 1, last + (k + 1) % n))
        kinds.append("iris")
    return (verts, faces), kinds


def _lid(c, R, axis, angle, n=12):
    """A lid: the part of a ball that lies within `angle` of `axis`, closed underneath, so that
    its edge is a shelf over the eye."""
    eps = R * 0.02
    prof = [(eps, R)] + [(R * math.sin(angle * i / 3), R * math.cos(angle * i / 3)) for i in (1, 2, 3)] + [(eps, R * math.cos(angle))]
    turn = Z.rotation_difference(V(axis).normalized()).to_matrix().to_4x4()
    return g.moved(g.lathe(prof, n=n, caps=True), Matrix.Translation(V(c)) @ turn)


def grow_face(r, A, style, size):
    """Its face (the second pass, rule 4). Each eye is a ball of the field's light set in the
    head, a piece of its own so that it blinks, with its pupil where it is looking: open looks
    at who is here, fixed at one thing ahead of it, aside over its shoulder and past you; young
    is all eye. Its lids and a mark in its Path's colour say the rest. Then the corner of its
    mouth and the pad of its nose."""
    f = FACES[style]
    e, er, n0 = A.eye, A.eye_r, A.eye_n
    spec = getattr(r, "_spec", {})
    me = r.mesh.data
    names = [m.name for m in me.materials]
    dark = mat("fur_mask")
    # the eye it was born with becomes the dark of its socket: what is seen when it shuts
    slot = next((i for i, nm in enumerate(names) if nm.startswith("field_eyes")), None)
    if slot is not None:
        if dark.name not in names:
            me.materials.append(dark)
        di = [m.name for m in me.materials].index(dark.name)
        for p in me.polygons:
            if p.material_index == slot:
                p.material_index = di
    lamp, far, old = _has(r, "eyes", "lamp"), _has(r, "eyes", "far"), _has(r, "eyes", "old")
    R = er * f["r"] * size * (1.3 if lamp else 1.0)
    sunk = 0.42 if lamp else f["sunk"]
    vis = math.sqrt(max(0.0, 1.0 - sunk * sunk))          # what shows of the ball, in radii
    log("face", style, "born %.3f ball %.3f faces (%.2f %.2f %.2f) at (%.2f %.2f %.2f)" % (er, R, n0.x, n0.y, n0.z, e.x, e.y, e.z))
    am = mat("fur_pale") if old else _am("light" if spec.get("coat") in DARK_COATS else "")
    eye_m = {"iris": field("eyes", 4.4 if lamp else 3.4), "pupil": mat("eye_dark"), "glint": mat("eye_white")}

    def on_skin(p, lift=0.005):
        """A point at the side of the head, brought out to its skin."""
        return Vector(((1 if p.x > 0 else -1) * (r.side(p.y, p.z, window=0.05) + lift), p.y, p.z))

    for sgn, tag in ((1, "l"), (-1, "r")):
        n = Vector((sgn * n0.x, n0.y, n0.z))
        fw = (-Y - n * (-Y).dot(n)).normalized()          # toward the nose, along the head
        up = (Z - n * Z.dot(n) - fw * Z.dot(fw)).normalized()
        s = Vector((sgn * e.x, e.y, e.z))                 # on its skin
        c = s - n * (R * sunk)
        # where it looks; a pupil keeps most of itself in what shows of the ball
        gx, gy, gz = f["gaze"]
        d = Vector((sgn * gx, -gy, gz)).normalized()
        pa = math.radians(f["pupil"] * (0.8 if lamp else 1.0))
        lim = max(0.05, math.acos(sunk) - pa * 0.8)
        if d.angle(n) > lim:
            d = Matrix.Rotation(lim, 3, n.cross(d).normalized()) @ n
        ball, kinds = _eyeball(c, R, d, up * 0.8 + fw * 0.5, pa)
        if far:                                           # long, as one that looks a long way
            ball = ([c + fw * ((p - c).dot(fw) * 1.3) + up * ((p - c).dot(up) * 0.78) + n * (p - c).dot(n) for p in ball[0]], ball[1])
        _later(r, "blink", "eye", None, c, "Head", side=tag, solid=(ball, [eye_m[k] for k in kinds]))
        q, lean = f["lid"]
        q2, lean2 = f["under"]
        if far:
            q, q2 = q + 0.1, q2 + 0.08
        if lamp:                                          # a lamp's eye has a rim and no lid
            a0, a1, rim = R * vis * 1.02, R * vis * 1.3, None
            rings = [g.ring(s + n * h, rad, rad, n=14, u=fw, v=up * sgn) for h, rad in ((-0.02, a1), (R * 0.2, a1 * 0.96), (R * 0.2, a0), (-0.02, a0))]
            rim = g.loft(rings + [rings[0]], caps=False)
            _add(r, "eye_rim_" + tag, rim, "Head", _trim(r, "metal_brass", "light"), smooth=False)
        else:
            Rl = R * 1.1
            if q > 0.0:
                lu = (up * math.cos(lean) + fw * math.sin(lean) + n * 0.12).normalized()
                _add(r, "lid_" + tag, _lid(c, Rl, lu, math.acos(max(-0.6, min(0.97, R * vis * (1.0 - 2.0 * q) / Rl)))), "Head", dark, smooth=True)
            if q2 > 0.0:
                ld = (-up * math.cos(lean2) + fw * math.sin(lean2) + n * 0.12).normalized()
                _add(r, "lid_under_" + tag, _lid(c, Rl * 0.99, ld, math.acos(max(-0.6, min(0.97, R * vis * (1.0 - 2.0 * q2) / Rl)))), "Head", dark, smooth=True)
        # its Path's colour round the eye
        mk = None if lamp else f["mark"]
        skin_n = (n + up * 0.6).normalized()
        if mk == "pips":
            # a brow, its inner end a little the higher: it is listening (an old one's is pale, long, and falls at its outer end)
            a0 = on_skin(s + up * (R * vis + er * (0.7 if old else 1.0)) - fw * (er * (2.1 if old else 1.4)), 0.008)
            a1 = on_skin(s + up * (R * vis + er * 1.3) + fw * (er * 1.2), 0.008)
            _add(r, "brow_" + tag, g.blade(a0, a1, er * (0.85 if old else 0.66), normal=skin_n, belly=0.6), "Head", am, smooth=True)
        elif mk == "slash":
            a0 = on_skin(s + up * (R * vis + er * 0.75) - fw * (R * 0.9), 0.008)
            a1 = on_skin(s + up * (R * vis * 0.55) + fw * (R * vis + er * 0.9), 0.008)
            _add(r, "slash_" + tag, g.blade(a0, a1, er * 1.0, normal=skin_n, belly=0.42), "Head", am, smooth=True)
            b0 = on_skin(s - up * (R * vis * 0.35) + fw * (R * vis + er * 0.35), 0.008)
            b1 = on_skin(Vector((s.x, A.nose.y + 0.24, b0.z - (b0.z - (A.nose.z - 0.02)) * 0.8)), 0.008)
            _add(r, "tear_" + tag, g.blade(b0, b1, er * 0.7, normal=n, belly=0.3), "Head", am, smooth=True)
        elif mk == "under":
            p = on_skin(s - up * (R * vis + er * 0.6) + fw * (er * 0.2))
            nn = (n - up * 0.25).normalized()
            _add(r, "undereye_" + tag, _lens(p, nn, fw, nn.cross(fw), R * 1.05, er * 0.5, er * 0.22), "Head", am, smooth=True)
    zb, zt = _jaw_line(r, A)
    # the corner of its mouth (a jaw that hangs open has drawn its own)
    if not _has(r, "maw", "open", "glow"):
        zj = zb + 0.42 * (zt - zb)
        geo = None
        for sgn in (1, -1):
            pts = []
            for t in (0.4, 0.6, 0.78, 0.92):
                y = A.nose.y + 0.03 + (e.y - 0.02 - A.nose.y) * t
                zz = zj + f["smile"] * ((t - 0.4) / 0.52) ** 2
                pts.append(Vector((sgn * (r.side(y, zz, window=0.08) - 0.004), y, zz)))
            geo = g.merge(geo, g.tube(pts, [0.006, 0.011, 0.011, 0.004], n=4, caps=True))
        _add(r, "mouth", geo, "Head", mat("nose"), smooth=True)
    # the pad of its nose
    nw = max(0.035, r.side(A.nose.y + 0.03, A.nose.z, window=0.05))
    _add(r, "nose_pad", g.ico(A.nose + Vector((0, 0.014, 0.01)), 1.0, sub=1, scale=(nw * 0.82, 0.04, nw * 0.62)), "Head", mat("nose"), smooth=False)


def grow_feet(r, A, style, size):
    """Its feet (the second pass, rule 4): toes, and a claw to each."""
    if style != "toes":
        return
    for tag, foot, bone in FEET:
        f = r.bone(foot)
        hw = max(0.07, r.side(f.y, 0.08, window=0.1) - abs(f.x))
        toes, claws = None, None
        for j in range(4):
            u = (j - 1.5) / 1.5                      # across the paw, -1 to 1
            x = f.x + u * hw * 0.74
            back = 0.035 * abs(u)                    # the outer toes sit a little behind the middle two
            c = Vector((x, f.y - 0.075 * size + back, 0.058))
            toes = g.merge(toes, g.ico(c, hw * 0.33, sub=1, scale=(0.9, 1.5, 0.85)))
            b0 = c + Vector((0, -hw * 0.36, 0.012))
            claws = g.merge(claws, g.cone(b0, b0 + Vector((u * 0.012, -0.085 * size, -0.05)), hw * 0.13, n=5))
        _add(r, "toes_" + tag, toes, bone, mat("fur_light"), smooth=True)
        _add(r, "toeclaws_" + tag, claws, bone, mat("claw"), smooth=True)


def grow_fur(r, A, style, size):
    """Its coat as fur (the second pass, rule 4): tufts at the root of its ears, and a brush to
    its tail, fullest past the middle, in the colour its tail-tip is marked with."""
    if style != "coat":
        return
    for s, ear in ((1, "Ear1.L"), (-1, "Ear1.R")):
        eb = r.bone(ear)
        geo = None
        for i, (dx, L) in enumerate(((-0.06, 0.2), (0.02, 0.27), (0.1, 0.19))):
            b0 = eb + Vector((s * dx, -0.06, 0.0))
            geo = g.merge(geo, _lock(b0, Vector((s * (0.2 + dx * 3), -0.7, 0.3)), L * size, 0.085, lie=0.9, lift=0.3, droop=0.0, back=Z))
        _add(r, "eartuft_" + ("l" if s > 0 else "r"), geo, ear, mat("fur_light"))
    if _has(r, "tail", "whip", "short", "smoke"):
        return
    tip = None
    for st, _ in each(getattr(r, "_spec", {}).get("marks")):
        if st.partition(":")[0] == "tailtip":
            tip = _am(st.partition(":")[2])
    tb = A.tail
    for i in range(2, 8):
        c = tb[i]
        d = (tb[min(7, i + 1)] - tb[i - 1]).normalized()
        u, v = g._frame(d)
        full = 0.62 + 0.38 * math.sin(math.pi * (i - 1.5) / 6.0)
        geo = None
        for k in range(2):
            a = k * math.pi + i * 0.95
            out = u * math.cos(a) + v * math.sin(a)
            geo = g.merge(geo, _lock(c + out * 0.05, out, 0.52 * full * size, 0.25 * full, lie=0.95, lift=0.2, droop=0.0, back=d))
        _add(r, "brush_%d" % i, geo, "Tail%d" % (i + 1), tip if (tip is not None and i >= 4) else mat("fur_dark"))


# A family of lines may add styles of its own without touching the ones here (lines_*.py):
#   GROWS[(slot, style)] = fn(r, A, size)      grown on the body once it has its shape
#   SHAPES[(slot, style)] = fn(r, size)        part of its shape, before it is measured
GROWS = {}
SHAPES = {}

# what is grown on a body once it has its shape, in this order (ears and the tail's own length
# are part of its shape, and come before it is measured)
# (marks first: they are the body's own faces, painted before anything is joined to it)
SLOTS = (("marks", grow_marks), ("maw", grow_maw), ("eyes", grow_eyes), ("face", grow_face), ("paws", grow_paws), ("feet", grow_feet), ("fur", grow_fur),
         ("armor", grow_armor), ("spine", grow_spine), ("ruff", grow_ruff), ("tail", grow_tail), ("flags", grow_flags), ("carry", grow_carry),
         ("aura", grow_aura))


def _spots(r, A):
    """Where the sockets go, read from the body before anything is grown on it (genius_kit's)."""
    eye, nose, hb = A.eye, A.nose, A.head
    t3, n1, n2, sh = A.t3, A.n1, A.n2, A.sh
    spots = {
        "socket_head": ("Head", (0, hb.y + 0.06, A.skull - 0.02), None),
        "socket_eyes": ("Head", (0, eye.y - 0.1, eye.z + 0.01), None),
        "socket_mouth": ("Head", (0, nose.y + 0.16, nose.z - 0.1), None),
        "socket_grip": ("Head", (0, nose.y + 0.22, nose.z - 0.14), kit.ACROSS_MOUTH),
        "socket_throat": ("Neck2", (0, n2.y, r.bottom(n2.y, half_width=0.08) + 0.02), None),
        "socket_light": ("Neck2", (0, (n1.y + n2.y) / 2, r.bottom((n1.y + n2.y) / 2, half_width=0.08)), None),
        "socket_back": ("Torso3", (0, t3.y + 0.12, r.top(t3.y + 0.12) - 0.03), None),
        "socket_body": ("Torso3", (0, sh.y - 0.42, sh.z + 0.02), None),
        "socket_tail": ("Tail1", tuple(r.bone("Tail1")), None),
        "socket_arm_l": ("Torso3", (r.side(sh.y, sh.z + 0.2) + 0.02, sh.y, sh.z + 0.2), None),
        "socket_arm_r": ("Torso3", (-r.side(sh.y, sh.z + 0.2) - 0.02, sh.y, sh.z + 0.2), None),
    }
    nb = r.bone("Neck2")
    chw = r.side(nb.y, nb.z)
    spots["socket_collar"] = ("Neck2", (0, nb.y, nb.z), lambda k, a=chw: Matrix.Diagonal(((a + 0.03) * k / 0.1, 1.0, (a * 1.12 + 0.03) * k / 0.1)))
    for tag, bone, foot in (("fl", "FrontLowerLeg.L", "FF.L"), ("fr", "FrontLowerLeg.R", "FF.R"), ("bl", "BackLowerLeg.L", "FFB.L"), ("br", "BackLowerLeg.R", "FFB.R")):
        f = r.bone(foot)
        spots["socket_limb_" + tag] = (bone, (f.x, f.y + 0.06, 0.12), None)
    for tag, bone, foot, rot in (("l", "FrontLowerLeg.L", "FF.L", kit.HAND_ON_PAW_L), ("r", "FrontLowerLeg.R", "FF.R", kit.HAND_ON_PAW_R)):
        f = r.bone(foot)
        spots["socket_hand_" + tag] = (bone, (f.x, f.y - 0.02, 0.16), rot)
    return spots


def wolf_form(form_id, level, spec, species=None, coat=("fur_dark", "fur_light"), marks=("socks", "mask", "saddle", "tailtip"), ages=None, measure=None):
    """One form on the wolf's rig: its stage, its build, what it has grown. Another animal on
    the same rig gives its own shape (species), the names of its coat's two materials (the
    look's roles for its body), its marking regions, its own ages in place of the wolf's, and
    measure(r, A) to correct what is read of a body the wolf's readings do not fit."""
    _, r = kit._wolf()
    r._spec, r._late = spec, []      # what it is being built to, and the pieces put on its bones at the end
    r._own = species is None         # the Wolf itself: what is new in the second pass is its own
    if r._own:
        # The rig comes in standing in a frame of one of its clips, not at rest, and what is put
        # on a bone is put where the bone stands then: the game, which has only its rest, would
        # find a lamp hung at a tail's end a hand away from the tail. The Wolf is built at rest.
        r.arm.data.pose_position = "REST"
        bpy.context.view_layer.update()
    _weld(r)
    c = PALETTE
    r.recolor("Main", coat[0], c.get(coat[0], c["fur_dark"])[0], rough=0.92)
    r.recolor("Main_Light", coat[1], c.get(coat[1], c["fur_light"])[0], rough=0.9)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.3, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "nose", c["nose"][0], rough=0.5)
    if species:
        species(r)
    (ages or stage)(r, level)
    build(r, spec.get("build", {}))
    for slot in spec:
        for style, size in (each(spec.get(slot)) if slot not in ("build", "coat") else []):
            if (slot, style) in SHAPES:
                SHAPES[(slot, style)](r, size)
    for style, size in each(spec.get("ears")):
        grow_ears(r, None, style, size)
    for style, size in each(spec.get("tail")):
        reshape_tail(r, style, size)
    r.settle()
    kit._wolf_marks(r, coat, marks)
    A = Anat(r)
    if measure:
        measure(r, A)
    spots = _spots(r, A)
    ref = A.skull
    for slot, fn in SLOTS:
        for style, size in each(spec.get(slot)):
            if (slot, style) in GROWS:
                GROWS[(slot, style)](r, A, size)
            else:
                fn(r, A, style, size)
    for slot in spec:      # slots only a family knows
        if slot not in dict(SLOTS) and slot not in ("build", "coat", "ears"):
            for style, size in each(spec.get(slot)):
                if (slot, style) in GROWS:
                    GROWS[(slot, style)](r, A, size)
    # bring it to the kit's size by the crown of its head, and put its sockets on its bones
    k = STAND / ref
    r.uniform(k)
    sockets = {name: kit.bone_socket(r.arm, name, bone, Vector(at) * k, rot(k) if callable(rot) else rot) for name, (bone, at, rot) in spots.items()}
    sockets["ref_top"] = kit.free_socket("ref_top", (0, 0, STAND))
    # what moves by its name rides its bone, and goes out with the body (export takes whatever
    # is in sockets)
    made = {}
    for i, piece in enumerate(r._late):
        ob = _on_bone(r, piece, k, made)
        made[ob.name] = ob
        sockets["piece_%d" % i] = ob
    return r, sockets


def _on_bone(r, piece, k, made=None):
    """A piece made with the body, now that the body is its size: a mesh of its own on a bone."""
    if piece.get("solid"):
        geo, mats = piece["solid"]
        assert piece["kind"] in MOVES, piece["kind"]
        name = "%s_%s%s%s" % (piece["kind"], piece["what"], "_" + piece["side"] if piece["side"] else "", "_%d" % piece["n"] if piece["n"] is not None else "")
        ob = set_origin(_solid(name, ([Vector(v) * k for v in geo[0]], geo[1]), mats), piece["pivot"] * k)
    else:
        items = [(([Vector(v) * k for v in geo[0]], geo[1]), m) for geo, m in piece["items"]]
        ob = moving(piece["kind"], piece["what"], items, piece["pivot"] * k, side=piece["side"], n=piece["n"])
    if piece.get("under") and made and piece["under"] in made:
        return child_of(ob, made[piece["under"]])
    at = Matrix.Translation(piece["pivot"] * k)      # where set_origin has just stood it
    ob.parent = r.arm
    ob.parent_type = "BONE"
    ob.parent_bone = piece["bone"]
    bpy.context.view_layer.update()
    ob.matrix_world = at
    return ob


def export(r, sockets, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in [r.arm, r.mesh] + list(sockets.values()):
        o.select_set(True)
    bpy.context.view_layer.objects.active = r.arm
    # no clips: a form moves by its base body's, which the game fits to its proportions
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                              export_animations=False, export_skins=True, export_texcoords=False)
    tris = sum(len(p.vertices) - 2 for p in r.mesh.data.polygons)
    log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


# ======================================================================================
# The lines
# ======================================================================================

# --- what moves, and what is worn (docs/genius-lines.md, "What moves", "A worn piece") -------

MOVES = ("beat", "glide", "sway", "wave", "wag", "spin", "flick", "pulse", "bob", "turn", "blink")


def set_origin(ob, pivot):
    """Put a piece's own origin at a point of the model: that is what it turns about. (For a
    piece that still stands where it was made, with no parent.)"""
    p = Vector(pivot)
    ob.data.transform(Matrix.Translation(-p))
    ob.location = p
    return ob


def child_of(ob, parent):
    """Make one piece ride another, each staying where it stands."""
    bpy.context.view_layer.update()
    ob.parent = parent
    ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def moving(kind, what, items, pivot, smooth=True, side="", n=None, parent=None):
    """A piece of a body that the game moves by its name: <kind>_<what>[_l|_r][_<n>], about
    `pivot` (a wing's root, the hook a lamp hangs by, the base of a flame, the middle of an
    eye). items: [(geometry, material), ...] made where the piece stands in the model.

      beat   a wing: it flaps about the way the body faces (give side "l" or "r")
      glide  the same, slow and shallow: a wing held out, a fin
      sway   what hangs or trails: a slow pendulum
      wave   one piece of a chain that nods, each after the one before (n: its place, from 0)
      wag    the same from side to side: a fish's body, a tail
      spin   it turns about its own up (side "r" turns the other way)
      flick  a flame: it stretches and gutters along its own up
      pulse  it breathes: a little larger, a little smaller
      bob    it rises and falls along its own up
      turn   a head that looks about: slowly left and right about its own up
      blink  an eye: now and then it shuts along its own up (all of a body's together)

    A piece's own up is Blender's Z as it is made (do not turn the object; turn the geometry).
    Pieces of one chain are made children of one another with parent=, root first."""
    assert kind in MOVES, kind
    name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else "")
    ob = g.pieces(name, items, smooth=smooth)
    set_origin(ob, pivot)
    if parent is not None:
        child_of(ob, parent)
    return ob


def worn(objects, at=(0, 0, 0), rot=None):
    """The piece of a genius that is shown when it is worn, in place of everything else of it
    (a mantle on the shoulders where a whole coat would not sit): an empty named worn that
    holds the objects. It is made at `at`, turned `rot`, and that place is put on the place it
    is worn (data/genius-types.json, mounts) as it lies: so make the piece where it would sit on
    a person standing at the origin facing -Y, and give the point of them it hangs from (the
    nape of the neck, say). Returns the empty and the objects, all to be exported."""
    e = bpy.data.objects.new("worn", None)
    e.empty_display_size = 0.05
    bpy.context.collection.objects.link(e)
    e.matrix_world = Matrix.Translation(Vector(at)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    for ob in objects:
        if ob.parent is None:
            child_of(ob, e)
    return [e] + list(objects)


def export_objects(objects, sockets, path, ref=STAND):
    """A body with no rig: its meshes and its sockets (empties), and ref_top at the height
    the game should stand it to."""
    sockets = dict(sockets)
    sockets["ref_top"] = kit.free_socket("ref_top", (0, 0, ref))
    return kit.Built(objects, sockets).export(path)


def build_baby():
    """The Baby: everyone's genius from the night the field wakes until the rite. A small round
    thing of pale matter with a face, the field in its eyes, in its belly and at the tip of
    its tail; it has not yet been born into a form. One model, for everyone."""
    kit.reset()
    skin, dark = mat("hide_baby"), mat("hide_baby_dark")
    R = STAND / 1.85
    c = Vector((0, 0, R * 0.95))
    items = [(g.ico(c, R, sub=2, scale=(1.0, 0.95, 0.9)), skin)]
    items.append((g.ico(c + Vector((0, -R * 0.58, -R * 0.34)), R * 0.46, sub=2, scale=(1.0, 0.62, 0.86)), field("heart", 2.2)))
    for sg in (1, -1):
        items.append((g.ico(c + Vector((sg * R * 0.36, -R * 0.74, R * 0.26)), R * 0.25, sub=2, scale=(0.95, 0.6, 1.15)), field("eyes", 3.8)))
        items.append((g.blade(c + Vector((sg * R * 0.42, 0.02, R * 0.66)), c + Vector((sg * R * 0.86, 0.12, R * 1.5)), R * 0.46, normal=Vector((0, -1, 0.2)), belly=0.42), skin))
        items.append((g.blade(c + Vector((sg * R * 0.66, 0.04, R * 1.12)), c + Vector((sg * R * 0.9, 0.11, R * 1.56)), R * 0.26, normal=Vector((0, -1, 0.2)), belly=0.42), mat("hide_baby_pale")))
        items.append((g.ico(Vector((sg * R * 0.36, -R * 0.3, R * 0.12)), R * 0.2, sub=1, scale=(1.0, 1.35, 0.7)), dark))
    t0 = c + Vector((0, R * 0.78, -R * 0.25))
    pts = [t0, t0 + Vector((0, R * 0.55, R * 0.05)), t0 + Vector((0, R * 0.9, R * 0.55)), t0 + Vector((0, R * 0.62, R * 1.12))]
    items.append((g.tongue(pts, [R * 0.44, R * 0.36, R * 0.24, R * 0.07], thick=0.75, normal=X), skin))
    items.append((g.ico(pts[-1], R * 0.15, sub=1), field("tail", 3.0)))
    ob = g.pieces("baby", items, smooth=True)
    export_objects([ob], {}, os.path.join(OUT, "baby.glb"), ref=STAND)


# --- the Wolf's gift: what a hybrid wears of it on another base's body ---------------------

def fangs_gift():
    """Fangs anyone can see: two long from above, two short from below."""
    up = g.tongue([(0.03, 0.0, 0.008), (0.035, -0.012, -0.052), (0.027, 0.0, -0.125)], [0.032, 0.023, 0.002], thick=0.7, normal=(1, 0, 0))
    low = g.tongue([(0.021, -0.022, -0.085), (0.023, -0.028, -0.05), (0.02, -0.022, -0.02)], [0.017, 0.013, 0.002], thick=0.7, normal=(1, 0, 0))
    return [kit._part("fangs", [(g.merge(up, g.mirrored(up)), mat("bone")), (g.merge(low, g.mirrored(low)), mat("bone"))])]


def ruff_gift():
    """A wolf's ruff, round the throat of whatever wears it."""
    geo, geo2 = None, None
    n = 13
    for i in range(n):
        a = math.pi * (-0.15 + 1.3 * i / (n - 1))
        d = Vector((math.cos(a), 0, math.sin(a)))
        base = Vector((0.1 * d.x, 0.0, 0.09 + 0.1 * d.z))
        L = 0.19 * (1.0 + 0.15 * math.sin(i * 2.3))
        bl = g.blade(base, base + Vector((d.x * L * 0.6, L * 0.75, d.z * L * 0.6)), 0.085, normal=d, belly=0.32)
        if i % 2:
            geo2 = g.merge(geo2, bl)
        else:
            geo = g.merge(geo, bl)
    return [kit._part("ruff", [(geo, mat("fur_ruff")), (geo2, mat("fur_light"))])]


GIFTS = {"fangs": fangs_gift, "ruff": ruff_gift}


def build_wolf(form_id, level, spec, base):
    r, sockets = wolf_form(form_id, level, spec)
    carriage(r, spec)
    export(r, sockets, os.path.join(OUT, form_id + ".glb"))


# base id -> build(form id, level, body, base): writes game/assets/genius/forms/<form id>.glb
BUILDERS = {"wolf": build_wolf}


_BASE = {}        # the palette every family starts from: the kit's and the Wolf's
_OWN = {}         # family file -> what it adds to the palette or makes its own shade of
_FAMILY = {}      # base id -> its family file


def _families():
    """Every other family of lines is a file of its own beside this one, lines_<family>.py,
    with register(builders): it adds its bases to BUILDERS (and its styles to GROWS and
    SHAPES). One file a family, so the families can be worked on at once.

    A family's colours are its own. Two families may each call a colour "moss" or "glaze" and
    mean different things by it, so what a family puts in the palette is kept apart, and a
    base is built on the kit's palette and its own family's and nobody else's (_palette_of)."""
    _BASE.update(PALETTE)
    for name in sorted(f[:-3] for f in os.listdir(HERE) if f.startswith("lines_") and f.endswith(".py")):
        PALETTE.clear()
        PALETTE.update(_BASE)
        before = set(BUILDERS)
        __import__(name).register(BUILDERS)
        _OWN[name] = {k: v for k, v in PALETTE.items() if _BASE.get(k) != v}
        for b in set(BUILDERS) - before:
            _FAMILY[b] = name
    for own in _OWN.values():       # outside a build, every name can be looked up
        PALETTE.update(own)


def _palette_of(base_id):
    """The palette a base is built on: the kit's, the Wolf's, and its own family's."""
    PALETTE.clear()
    PALETTE.update(_BASE)
    PALETTE.update(_OWN.get(_FAMILY.get(base_id), {}))


def _palette_kept(base_id):
    """What a family put in the palette while building (a file of its own, read when first
    needed) is its own from then on."""
    fam = _FAMILY.get(base_id)
    if fam:
        _OWN[fam].update({k: v for k, v in PALETTE.items() if _BASE.get(k) != v and not k.startswith("accent")})


ACCENT_STEPS = (("", 2), ("_deep", 0), ("_dark", 1), ("_light", 3), ("_pale", 4))


def accent(spec):
    """A Path's colour, for the form about to be built (docs/genius-lines.md, "A Path's
    colour"): the body's `accent` names a ramp of data/style.json, and the materials accent,
    accent_deep, accent_dark, accent_light and accent_pale are its five steps (accent2* the
    same of `accent2`). A builder asks for mat("accent_dark") and need know nothing else; the
    game puts the same colours on at load, from the data, so a Path's colour can be changed
    without a rebuild."""
    import style
    for key in ("accent", "accent2"):
        ramp = spec.get(key) or spec.get("accent") or "bone"
        for suffix, step in ACCENT_STEPS:
            PALETTE[key + suffix] = (tuple(style.ramp(ramp, step)[:3]), 0.7, 0.0)


def merged(parent, own):
    """A form wears what its parent wears, unless it says otherwise (null takes a thing off)."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in parent.items()}
    for k, v in own.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def forms_of(base):
    """[(form id, level, the body it wears with everything carried down the line)]"""
    out = []
    s = base["settled"]
    s1 = merged({}, s.get("body", {}))
    out.append((s["id"], 1, s1))
    for p in base["paths"]:
        s2 = merged(s1, p.get("body", {}))
        out.append((p["id"], 2, s2))
        for q in p["prongs"]:
            s3 = merged(s2, q.get("body", {}))
            out.append((q["id"], 3, s3))
            for f in q["finishes"]:
                out.append((f["id"], 4, merged(s3, f.get("body", {}))))
    return out


def build_base(base_id, only=None):
    with open(os.path.join(BASES, base_id + ".json")) as f:
        base = json.load(f)
    if base_id not in BUILDERS:
        log("no builder yet for", base_id)
        return
    _palette_of(base_id)
    for form_id, level, spec in forms_of(base):
        if only and form_id not in only:
            continue
        accent(spec)
        BUILDERS[base_id](form_id, level, spec, base)
    _palette_kept(base_id)


_families()

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "gifts":       # the parts a hybrid wears of the bases built here
        kit.PARTS.update(GIFTS)
        for feature in GIFTS:
            kit.build_part(feature)
    elif args and args[0] == "baby":
        build_baby()
    elif not args or args[0] == "--all":
        build_baby()
        for b in sorted(BUILDERS):
            build_base(b)
    else:
        build_base(args[0], set(args[1:]) or None)
