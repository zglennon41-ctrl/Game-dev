"""WILDLINE body kit: the people of the thirteen cities, built as the game's own bodies on
the KayKit bones so the seventy-six animations keep playing (docs/bodies-plan.md). Run
headless with Blender's Python module:

    python tools/blender/body_kit.py                 # every body this file knows, then the sheet
    python tools/blender/body_kit.py alexandria-m    # one body
    python tools/blender/body_kit.py sheet           # only the sheet, from the exported files
    python tools/blender/body_kit.py parts           # the parts the bloods' marks hang on the sockets

Method: import a KayKit body with the people kit, reshape its bones to grounded proportions
(the people kit's method), throw KayKit's meshes away, and grow our own body around the bones:
each limb, the torso and the head a loft of elliptical rings along the bone chain, the hands
and feet their own lofts. Every vertex is weighted by hand to the bones of its chain, blended
across each joint, so the baked animations bend it where KayKit's bent. Three builds of each
body (lean, fit, heavy) are three ring tables of the same topology; lean and heavy become
shape keys the game blends by the player's slider. Eyes and hair hang from the head bone;
sockets (empties) hang where blood marks and the changes of instars will. Skin, tunic,
trousers and boots are plain materials: the game tints the skin by the chosen tone.

World space is Blender's: Z up, the body faces -Y, the rest pose a T-pose, 2.4 units tall.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import people_kit as pk  # noqa: E402
import anatomy as an  # noqa: E402
import head as hd  # noqa: E402
import wardrobe  # noqa: E402

ROOT = pk.ROOT
OUT = os.path.join(ROOT, "game", "assets", "people")
SCRATCH = pk.SCRATCH

HOMES = ["alexandria", "columbia", "cahokia", "lunden", "colonia", "tiber", "khemet", "baghdad", "varanasi", "jiangnan", "kazan", "timbuktu", "edo"]
SEXES = ["m", "f"]
BUILDS = ["lean", "fit", "heavy"]
SEGMENTS = 16

# The deform bones, by chain, with the joint each pair meets at (world Z for the trunk and legs,
# world X for the arms; the joint is the child's head).
DEFORM = {
    "trunk": ["hips", "spine", "chest", "head"],
    "arm.l": ["upperarm.l", "lowerarm.l", "wrist.l", "hand.l"],
    "arm.r": ["upperarm.r", "lowerarm.r", "wrist.r", "hand.r"],
    "leg.l": ["upperleg.l", "lowerleg.l", "foot.l", "toes.l"],
    "leg.r": ["upperleg.r", "lowerleg.r", "foot.r", "toes.r"],
}
BLEND = 0.07   # how far either side of a joint two bones share a vertex (v1 lofts)
# v2: the blend half-width at each joint of a chain, in order (the elbow and the knee wide,
# so a bend folds over a stretch of skin rather than creasing at a line)
# A bend folds the skin on its inner side and stretches it on the outer: the blend is narrow
# on the folding side (the elbow's front, the knee's back, the hip's front) so the fold does
# not pass through itself, and wide on the stretching side (the point of the elbow, the
# kneecap, the glute) so the stretch spreads.
BLENDS = {"trunk": [0.08, 0.09, 0.04], "arm": [0.05, 0.05, 0.04], "leg": [0.05, 0.06]}
BLEND_WIDE = {"arm": 0.11, "leg": 0.12}

SKIN = (0.72, 0.52, 0.40, 1)        # a middle tone; the game sets the chosen one
TUNIC = (0.30, 0.26, 0.34, 1)
TROUSERS = (0.16, 0.15, 0.17, 1)
BOOTS = (0.12, 0.09, 0.07, 1)
EYE_WHITE = (0.92, 0.9, 0.86, 1)
IRIS = (0.12, 0.09, 0.07, 1)
HAIR = (0.16, 0.11, 0.08, 1)
LIPS = (0.6, 0.38, 0.36, 1)         # the game tints it from the skin tone
PUPIL = (0.02, 0.02, 0.02, 1)


def log(*a):
    print("[body_kit]", *a)


# ======================================================================================
# The ring tables: where the body is, by sex and build. Units are world units on the rig
# the people kit makes (hips at 1.113, knee 0.57, ankle 0.12, shoulder 1.817 at x 0.151,
# elbow 0.518, wrist 0.913, neck 2.028). A ring is (centre, half-width x, half-depth y) for
# the trunk and legs (lofted along Z), (centre, half-depth y, half-height z) for the arms
# (lofted along X) and the feet (lofted along Y).
# ======================================================================================

def girth(build, part):
    """How much thicker or thinner than fit a build is, by part."""
    if build == "fit":
        return 1.0
    table = {
        "lean": {"trunk": 0.9, "shoulders": 0.92, "waist": 0.9, "limb": 0.86, "neck": 0.94},
        "heavy": {"trunk": 1.14, "shoulders": 1.2, "waist": 1.1, "limb": 1.22, "neck": 1.1},
    }
    return table[build][part]


# The garments are cut on these rings; the anatomy (v2) stands this much wider than the v1
# lofts did, so the rings take the same girth (width, depth) by region.
FIT = {"trunk": (1.36, 1.5), "shoulders": (1.22, 1.3), "neck": (1.3, 1.3), "arm": (1.1, 1.1), "leg": (1.6, 1.55), "ankle": (1.15, 1.15)}


def _fit(rings, region):
    kx, ky = FIT[region]
    return [(r[0], r[1] * kx, r[2] * ky) + tuple(r[3:]) for r in rings]


def trunk_rings(sex, build):
    g = lambda part: girth(build, part)  # noqa: E731
    fem = sex == "f"
    rings = [
        # z, half-width, half-depth, y-offset
        (0.98, 0.145 * g("trunk"), 0.10 * g("trunk"), 0.0),
        (1.07, (0.185 if fem else 0.165) * g("trunk"), (0.125 if fem else 0.115) * g("trunk"), 0.0),
        (1.19, (0.16 if fem else 0.15) * g("waist"), (0.11 if fem else 0.105) * g("waist"), 0.0),
        (1.31, (0.105 if fem else 0.135) * g("waist"), (0.09 if fem else 0.10) * g("waist"), 0.0),
        (1.46, (0.125 if fem else 0.155) * g("trunk"), (0.1 if fem else 0.115) * g("trunk"), 0.0),
        (1.60, (0.16 if fem else 0.175) * g("trunk"), (0.14 if fem else 0.125) * g("trunk"), -0.02 if fem else 0.0),
        (1.72, (0.175 if fem else 0.205) * g("trunk"), (0.125 if fem else 0.135) * g("trunk"), -0.005),
        (1.84, (0.19 if fem else 0.235) * g("shoulders"), (0.11 if fem else 0.125) * g("shoulders"), 0.0),
        (1.93, (0.125 if fem else 0.155) * g("shoulders"), (0.09 if fem else 0.1) * g("shoulders"), 0.0),
        (1.99, (0.055 if fem else 0.065) * g("neck"), (0.06 if fem else 0.068) * g("neck"), 0.01),
        (2.05, (0.05 if fem else 0.06) * g("neck"), (0.056 if fem else 0.064) * g("neck"), 0.01),
    ]
    if Body.ANATOMY:
        # the garments on the anatomy's own measured rings, a margin out, the neck from v1
        out = []
        for z, hw, hd, yo in rings:
            if z <= 1.93:
                rx, ry, yc = an._ring_at(z, sex, build)
                out.append((z, rx + 0.016, ry + 0.016, yc))
            else:
                out.append((z, hw * FIT["neck"][0], hd * FIT["neck"][1], yo))
        return out
    return rings


def head_rings(sex):
    fem = sex == "f"
    # z, half-width, half-depth, y-offset: a carved head 0.32 tall (7.5 heads in 2.4), the
    # jaw narrower, the brow broad; the face is at -Y.
    return [
        (2.04, 0.052, 0.058, 0.01),
        (2.085, (0.062 if fem else 0.07), (0.075 if fem else 0.082), -0.004),
        (2.13, (0.08 if fem else 0.086), (0.09 if fem else 0.096), 0.0),
        (2.2, (0.092 if fem else 0.097), (0.102 if fem else 0.107), 0.005),
        (2.27, (0.094 if fem else 0.099), (0.105 if fem else 0.109), 0.01),
        (2.34, (0.082 if fem else 0.087), (0.092 if fem else 0.097), 0.012),
        (2.4, 0.03, 0.035, 0.012),
    ]


def arm_rings(sex, build):
    k = girth(build, "limb")
    fem = sex == "f"
    s = 0.9 if fem else 1.0
    # x, half-depth y, half-height z
    rings = [
        (0.135, 0.075 * s * k, 0.08 * s * k),
        (0.21, 0.08 * s * k, 0.085 * s * k),
        (0.36, 0.065 * s * k, 0.07 * s * k),
        (0.518, 0.054 * s * k, 0.058 * s * k),
        (0.64, 0.06 * s * k, 0.062 * s * k),
        (0.82, 0.046 * s * k, 0.05 * s * k),
        (0.925, 0.038 * s, 0.042 * s),
    ]
    if Body.ANATOMY:
        # the elbow sits further out on the anatomy's rig (people_kit, "elbow")
        sh, old_el, new_el, wr = 0.151, 0.518, 0.575, 0.913

        def ax(x):
            if x <= sh or x >= wr:
                return x
            return sh + (x - sh) * (new_el - sh) / (old_el - sh) if x <= old_el else new_el + (x - old_el) * (wr - new_el) / (wr - old_el)
        return [(ax(r[0]),) + tuple(r[1:]) for r in _fit(rings, "arm")]
    return rings


def hand_rings(sex):
    s = 0.92 if sex == "f" else 1.0
    # x, half-width y, half-thickness z: a mitten, the palm flat
    return [
        (0.94, 0.04 * s, 0.03 * s),
        (0.99, 0.052 * s, 0.026 * s),
        (1.05, 0.05 * s, 0.022 * s),
        (1.1, 0.03 * s, 0.015 * s),
    ]


def leg_rings(sex, build):
    k = girth(build, "limb")
    fem = sex == "f"
    s = 0.95 if fem else 1.0
    # z, half-width x, half-depth y
    rings = [
        (1.09, 0.095 * s * k, 0.105 * s * k),
        (0.95, 0.09 * s * k, 0.098 * s * k),
        (0.75, 0.075 * s * k, 0.08 * s * k),
        (0.57, 0.062 * s * k, 0.068 * s * k),
        (0.42, 0.068 * s * k, 0.075 * s * k),
        (0.25, 0.048 * s * k, 0.055 * s * k),
        (0.14, 0.042 * s, 0.048 * s),
    ]
    if Body.ANATOMY:
        return _fit(rings[:6], "leg") + _fit(rings[6:], "ankle")
    return rings


def foot_rings(sex):
    s = 0.92 if sex == "f" else 1.0
    # y (heel +, toe -), half-width x, half-height z, z of the centre
    return [
        (0.09, 0.045 * s, 0.05 * s, 0.06),
        (0.0, 0.05 * s, 0.055 * s, 0.062),
        (-0.12, 0.052 * s, 0.04 * s, 0.045),
        (-0.24, 0.045 * s, 0.025 * s, 0.03),
    ]


# ======================================================================================
# Lofts
# ======================================================================================

def loft(name, rings, material_of=None):
    """A closed tube through `rings`, each (centre Vector, u Vector, v Vector): vertex k of a
    ring is centre + u cos + v sin. Faces bridge consecutive rings; the ends are capped.
    material_of(ring_index) gives each band its material slot."""
    bm = bmesh.new()
    loops = []
    for c, u, v in rings:
        ring = []
        for k in range(SEGMENTS):
            a = 2 * math.pi * k / SEGMENTS
            ring.append(bm.verts.new(c + u * math.cos(a) + v * math.sin(a)))
        loops.append(ring)
    faces = []
    for i, (a, b) in enumerate(zip(loops, loops[1:])):
        for k in range(SEGMENTS):
            f = bm.faces.new((a[k], a[(k + 1) % SEGMENTS], b[(k + 1) % SEGMENTS], b[k]))
            f.material_index = material_of(i) if material_of else 0
            faces.append(f)
    f0 = bm.faces.new(loops[0][::-1])
    f0.material_index = material_of(0) if material_of else 0
    f1 = bm.faces.new(loops[-1])
    f1.material_index = material_of(len(rings) - 2) if material_of else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def rings_z(table):
    """Trunk and leg tables: (z, half-width, half-depth, y-offset) lofted along Z."""
    out = []
    for r in table:
        z, hw, hd = r[0], r[1], r[2]
        yo = r[3] if len(r) > 3 else 0.0
        out.append((Vector((0, yo, z)), Vector((hw, 0, 0)), Vector((0, hd, 0))))
    return out


def rings_x(table, z, sign):
    """Arm and hand tables: (x, half-depth y, half-height z) lofted along X at height z."""
    return [(Vector((sign * x, 0, z)), Vector((0, hd, 0)), Vector((0, 0, hz))) for x, hd, hz in table]


def rings_y(table, x):
    """Foot tables: (y, half-width x, half-height z, z of the centre) lofted along Y."""
    return [(Vector((x, y, zc)), Vector((hw, 0, 0)), Vector((0, 0, hz))) for y, hw, hz, zc in table]


# ======================================================================================
# Dress: the home's outfit (data/bodies.json, dress) as shells on the body's own rings, so a
# garment fits every build and takes the lean and heavy keys with the body; headgear hangs
# from the head bone and the look's toggle shows or hides it.
# ======================================================================================

def home_dress(home):
    import json
    try:
        return json.load(open(os.path.join(ROOT, "data", "bodies.json")))["homes"][home].get("dress", {})
    except (KeyError, OSError):
        return {}


def _shell(rings, grow, lo=0, hi=None):
    """Rings lo..hi of a (z, hw, hd, yo) table, each grown by `grow` across."""
    sub = rings[lo:(hi + 1 if hi is not None else None)]
    return [(z, hw + grow, hd + grow, yo) for z, hw, hd, yo in sub]


def _skirt(z_top, hw, hd, yo, hem, flare, steps=4):
    """A loft from a ring down to the hem, widening by `flare`."""
    out = []
    for i in range(steps + 1):
        t = i / steps
        k = 1.0 + (flare - 1.0) * t
        out.append((z_top + (hem - z_top) * t, hw * k, hd * k, yo))
    return out


# ======================================================================================
# Finish: a cavity occlusion baked into every mesh's vertex colour (the shader darkens by
# it), and folds displaced into the garments (docs/graphics-comparison.md).
# ======================================================================================

def bake_cavity(ob, radius=0.06, strength=1.0):
    """Vertex colour = how open the surface is: a vertex whose neighbours lie above its
    tangent plane (a crease, an armpit, under a collar) goes dark; a ridge stays light.
    Cheap, no ray casts; reads as ambient occlusion under the bands."""
    me = ob.data
    normals = [n.vector.copy() for n in me.vertex_normals]
    coords = [v.co.copy() for v in me.vertices]
    nbrs = [set() for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nbrs[a].add(b)
        nbrs[b].add(a)
    occ = [1.0] * len(coords)
    for i, p in enumerate(coords):
        if not nbrs[i]:
            continue
        acc = 0.0
        for j in nbrs[i]:
            d = coords[j] - p
            L = d.length
            if L < 1e-6:
                continue
            acc += max(0.0, d.dot(normals[i]) / L)
        cav = acc / len(nbrs[i])          # 0 flat or convex, up to ~1 in a crease
        occ[i] = max(0.35, 1.0 - cav * 2.2 * strength)
    # a little spread, so the darkening is soft
    for _ in range(2):
        new = occ[:]
        for i in range(len(occ)):
            if nbrs[i]:
                new[i] = 0.5 * occ[i] + 0.5 * sum(occ[j] for j in nbrs[i]) / len(nbrs[i])
        occ = new
    if not me.color_attributes:
        me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    col = me.color_attributes[0]
    for i, c in enumerate(col.data):
        c.color = (occ[i], occ[i], occ[i], 1.0)


def displace_folds(ob, amplitude=0.006, around=9.0, along=14.0, seed=0.0):
    """Folds down a garment: the shell's vertices pushed in and out along their normals by
    a wave round the body and a slower one down it, so a coat hangs rather than fits."""
    me = ob.data
    normals = [n.vector.copy() for n in me.vertex_normals]
    for v, n in zip(me.vertices, normals):
        p = ob.matrix_world @ v.co
        a = math.atan2(p.y, p.x) if (abs(p.x) + abs(p.y)) > 1e-6 else 0.0
        w = math.sin(a * around + seed) * (0.6 + 0.4 * math.sin(p.z * along + seed * 0.7))
        v.co = v.co + n * (amplitude * w)


# ======================================================================================
# Weights: every vertex to the bones of its chain, blended across the joints
# ======================================================================================

def weight_chain(ob, joints, axis, bones, sign=1.0):
    """Vertex groups for a chain lofted along `axis` ("z" or "x"): bones[i] owns the stretch
    from joints[i] to joints[i+1] (the last to the end); across each joint the two bones share
    the vertex over BLEND either side. For the arms the axis is signed by side."""
    groups = {b: ob.vertex_groups.new(name=b) for b in bones}
    for v in ob.data.vertices:
        p = ob.matrix_world @ v.co
        t = (p.z if axis == "z" else sign * p.x)
        weights = {}
        for i, b in enumerate(bones):
            lo = joints[i] if i > 0 else -1e9
            hi = joints[i + 1] if i + 1 < len(bones) else 1e9
            w = 1.0
            if lo > -1e8:
                w *= _smooth((t - lo) / BLEND)
            if hi < 1e8:
                w *= 1.0 - _smooth((t - hi) / BLEND)
            if w > 1e-4:
                weights[b] = w
        total = sum(weights.values()) or 1.0
        for b, w in weights.items():
            groups[b].add([v.index], w / total, "REPLACE")


def _smooth(x):
    x = max(-1.0, min(1.0, x))
    x = (x + 1.0) / 2.0
    return x * x * (3.0 - 2.0 * x)


def _s01(t):
    """A smooth step from 0 at t <= 0 to 1 at t >= 1."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def weight_all(ob, bone, w=1.0):
    g = ob.vertex_groups.new(name=bone)
    g.add([v.index for v in ob.data.vertices], w, "REPLACE")


def skin_to(ob, arm):
    ob.parent = arm
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm


# ======================================================================================
# A body
# ======================================================================================

def home_face(home, sex):
    """The face parameters of a home and sex (data/bodies.json), 1.0 everywhere if unknown."""
    import json
    try:
        homes = json.load(open(os.path.join(ROOT, "data", "bodies.json")))["homes"]
        return dict(homes[home]["face"][sex])
    except (KeyError, OSError):
        return {}


class Body:
    def __init__(self, home, sex):
        self.home, self.sex = home, sex
        self.id = "%s-%s" % (home, sex)
        self.face_p = home_face(home, sex)
        self.r = pk.reshape(pk.Rig("Knight"))
        # The feminine figure stands 7.25 heads: a touch shorter on the same head.
        self.k = 1.0
        if sex == "f":
            self.k = 7.25 / 7.5
            self.r.uniform(self.k)
        # KayKit's meshes and accessories go; the bones and every action stay.
        for o in self.r.skinned + self.r.attached:
            bpy.data.objects.remove(o)
        self.r.skinned = []
        self.r.attached = []
        self.mats = {n: pk._material(n, c, rough=0.85) for n, c in
                     [("skin", SKIN), ("tunic", TUNIC), ("trousers", TROUSERS), ("boots", BOOTS), ("eye_white", EYE_WHITE), ("iris", IRIS),
                      ("hair", HAIR), ("lips", LIPS), ("pupil", PUPIL)]}
        self.parts = {}

    # --- the meshes ------------------------------------------------------------------

    def joint(self, bone, axis):
        b = self.r.arm.data.bones[bone]
        p = self.r.MA @ b.head_local
        return p.z if axis == "z" else abs(p.x)

    def fp(self, key):
        return float(self.face_p.get(key, 1.0))

    def carved_head(self, rings):
        """The home's carving on the head's rings: the jaw ring narrower or broader, the
        cheek ring wider, the whole head longer (rings above the jaw stretched up)."""
        out = []
        jaw, cheek, length = self.fp("jaw"), self.fp("cheek"), self.fp("headLength")
        base = rings[0][0]
        for i, r in enumerate(rings):
            z, hw, hd, yo = r
            k = 1.0
            if i == 1:
                k = jaw
            elif i == 2:
                k = (jaw + cheek) / 2.0
            elif i == 3:
                k = cheek
            z2 = base + (z - base) * length if i >= 2 else z
            out.append((z2, hw * k, hd * (1.0 + (k - 1.0) * 0.5), yo))
        return out

    def scaled(self, rings, head=False):
        """The ring tables are written for the masculine rig; the feminine rig is k times
        smaller everywhere but the head, which keeps its size and sits on the scaled neck."""
        k = self.k
        out = []
        for r in rings:
            if head:
                dz = r[0] - 2.04
                out.append((2.04 * k + dz,) + tuple(r[1:]))
            else:
                out.append(tuple(x * k for x in r))
        return out

    ANATOMY = True   # v2: one continuous body from the skeleton graph (anatomy.py)

    def build_meshes(self, build):
        """The body's meshes for one build, all named; returns {name: object}."""
        if self.ANATOMY:
            return self.build_anatomy(build)
        sex = self.sex
        mats = [self.mats[n] for n in ["skin", "tunic", "trousers", "boots", "eye_white", "iris"]]
        slot = {n: i for i, n in enumerate(["skin", "tunic", "trousers", "boots", "eye_white", "iris"])}

        def add(ob):
            for m in mats:
                ob.data.materials.append(m)
            return ob

        objs = {}
        tr = self.scaled(trunk_rings(sex, build))
        trunk = add(loft("Body", rings_z(tr), lambda i: slot["trousers"] if i < 2 else (slot["tunic"] if i < 8 else slot["skin"])))
        objs["Body"] = trunk
        head = add(loft("Head", rings_z(self.scaled(self.carved_head(head_rings(sex)), head=True)), lambda i: slot["skin"]))
        objs["Head"] = head
        z_arm = self.joint("upperarm.l", "z")
        for side, sign in (("l", 1), ("r", -1)):
            arm = add(loft("Arm_" + side, rings_x(self.scaled(arm_rings(sex, build)), z_arm, sign), lambda i: slot["tunic"] if i < 2 else slot["skin"]))
            objs["Arm_" + side] = arm
            hand = add(loft("Hand_" + side, rings_x(self.scaled(hand_rings(sex)), z_arm, sign), lambda i: slot["skin"]))
            objs["Hand_" + side] = hand
            x_leg = sign * self.joint("upperleg.l", "x")
            lr = [(Vector((x_leg, 0, 0)) + c, u, v) for c, u, v in rings_z(self.scaled(leg_rings(sex, build)))]
            leg = add(loft("Leg_" + side, lr, lambda i: slot["trousers"] if i < 5 else slot["boots"]))
            objs["Leg_" + side] = leg
            foot = add(loft("Foot_" + side, rings_y(self.scaled(foot_rings(sex)), x_leg), lambda i: slot["boots"]))
            objs["Foot_" + side] = foot
        self.dress_pieces(objs, build, add, slot)
        return objs

    def build_anatomy(self, build):
        """One continuous body (anatomy.py), its materials by region; the builds are made from
        the fit body by displacement, so lean and heavy share its topology for the shape keys."""
        sex = self.sex
        names = ["skin", "tunic", "trousers", "boots", "eye_white", "iris"]
        mats = [self.mats[n] for n in names]
        slot = {n: i for i, n in enumerate(names)}
        k = self.k
        ob = an.grow("Body", an.graph(sex, "fit"), subdiv=2, smooth=2)
        an.reloft_trunk(ob, sex, "fit")
        if k != 1.0:
            for v in ob.data.vertices:
                v.co = v.co * k
        an.carve(ob, [(c * k, r * k, st * k * (1.0 if build == "fit" else {"lean": 0.6, "heavy": 1.5}[build]), a) for c, r, st, a in an.carving(sex, "fit", self.face_p)])
        # The build: a girth change along the normals, by region (the face keeps its carving).
        if build != "fit":
            g_trunk = {"lean": -0.012, "heavy": 0.022}[build] * k
            g_limb = {"lean": -0.009, "heavy": 0.016}[build] * k
            normals = [n.vector.copy() for n in ob.data.vertex_normals]
            for v, n in zip(ob.data.vertices, normals):
                p = ob.matrix_world @ v.co
                if p.z > 2.03 * k:
                    continue
                limb = abs(p.x) > 0.17 * k or p.z < 1.1 * k
                v.co = v.co + n * (g_limb if limb else g_trunk)
        for m in mats:
            ob.data.materials.append(m)
        # Materials by region: underclothes on the trunk and legs, boots on the feet, skin elsewhere.
        for poly in ob.data.polygons:
            c = ob.matrix_world @ poly.center
            if c.z < 0.17 * k:
                poly.material_index = slot["boots"]
            elif c.z < 1.1 * k and abs(c.x) < 0.3 * k:
                poly.material_index = slot["trousers"]
            elif 1.1 * k <= c.z < 1.93 * k and abs(c.x) < 0.17 * k:
                poly.material_index = slot["tunic"]
            else:
                poly.material_index = slot["skin"]
        objs = {"Body": ob}
        # The head: head.py's skull set on the neck (the chin just above the neck's top),
        # full size on the feminine rig too (7.25 heads); its pieces hang from the head bone.
        head_ob, pieces, centre = hd.build_head(2.085 * k, sex, self.face_p, self.mats)
        objs["Head"] = head_ob
        if build == "fit":
            # the pieces hang from the head bone once, with their plain names; the other
            # builds' copies (the head does not change with the build) go at once
            self.head_pieces = pieces
            self.head_centre = centre
        else:
            for ob2 in pieces:
                bpy.data.objects.remove(ob2)
        pts = [head_ob.matrix_world @ v.co for v in head_ob.data.vertices]
        self.head_box = ((min(p.x for p in pts), max(p.x for p in pts)), (min(p.y for p in pts), max(p.y for p in pts)), (min(p.z for p in pts), max(p.z for p in pts)))
        self.dress_pieces(objs, build, None, slot)
        return objs

    def _head_box(self, ob):
        k = self.k
        pts = [ob.matrix_world @ v.co for v in ob.data.vertices if (ob.matrix_world @ v.co).z > 2.065 * k]
        return ((min(p.x for p in pts), max(p.x for p in pts)), (min(p.y for p in pts), max(p.y for p in pts)), (min(p.z for p in pts), max(p.z for p in pts)))

    def head_extents(self):
        """The head's box: from the Head loft (v1) or the body above the neck (v2)."""
        if self.ANATOMY:
            return self.head_box
        head = self.parts["Head"]
        return (self.r.extent([head], 0), self.r.extent([head], 1), self.r.extent([head], 2))

    def weights_at(self, p):
        """The bone weights of one point of the body: the head above the neck, the arms out
        past the shoulders, the legs below the hips, the trunk between, each chain blended
        across its joints; the shoulder shared between the upper arm and the chest (so the
        deltoid and a sleeve's top rise with the arm, the ribs stay), the hip between the
        thigh and the pelvis, the toes taking the front of the foot."""
        k = self.k
        if p.z > 2.045 * k:
            return {"head": 1.0}
        zj = [self.joint(b, "z") for b in DEFORM["trunk"]]
        trunk = _chain_weights(p.z, zj, DEFORM["trunk"], BLENDS["trunk"])
        ax = abs(p.x)
        # the arm's share: out past the shoulder, and not down the ribs under the armpit
        arm = 0.0
        if ax > 0.12 * k and p.z > 1.5 * k:
            arm = _s01((ax - 0.13 * k) / (0.12 * k))
            if ax < 0.32 * k:
                arm *= _s01((p.z - 1.58 * k) / (0.17 * k))
        if arm > 1e-3:
            side = "l" if p.x > 0 else "r"
            bones = DEFORM["arm." + side]
            xj = [self.joint(b, "x") for b in bones]
            blends = list(BLENDS["arm"])
            if p.y > 0.0:
                blends[0] = BLEND_WIDE["arm"]      # the elbow's point is behind
            limb = _chain_weights(ax, xj, bones, blends)
            return _mix(trunk, limb, arm)
        # the leg's share: below the hips, and not the crotch's middle
        leg = 0.0
        if p.z < 1.13 * k and (ax > 0.015 * k or p.z < 0.85 * k):
            hip_band = 0.08 if p.y < 0.0 else 0.16   # the fold at the hip's front, the stretch at the glute
            leg = _s01((1.12 * k - p.z) / (hip_band * k))
            if p.z > 0.85 * k:
                # the crotch's middle stays with the pelvis (only up there: a boot's inner
                # side or a wide hem passes the midline lower down and belongs to its leg)
                leg *= _s01((ax - 0.015 * k) / (0.05 * k))
        if leg > 1e-3:
            side = "l" if p.x > 0 else "r"
            bones = DEFORM["leg." + side][:3]
            lz = [self.joint(b, "z") for b in bones]
            blends = list(BLENDS["leg"])
            if p.y < 0.0:
                blends[0] = BLEND_WIDE["leg"]      # the kneecap is in front
            limb = _chain_weights_down(p.z, lz, bones, blends)
            # the toes: the front of the foot, so the foot rolls
            if p.z < 0.07 * k and p.y < -0.05 * k and "foot." + side in limb:
                t = _s01((-p.y - 0.05 * k) / (0.06 * k))
                f = limb["foot." + side]
                limb["foot." + side] = f * (1.0 - t)
                limb["toes." + side] = f * t
            return _mix(trunk, limb, leg)
        return trunk

    def weight_anatomy(self, ob):
        """Every vertex of a mesh to the bones by where it is (weights_at)."""
        groups = {}
        for chain in DEFORM.values():
            for b in chain:
                groups[b] = ob.vertex_groups.new(name=b)
        for v in ob.data.vertices:
            weights = self.weights_at(ob.matrix_world @ v.co)
            total = sum(weights.values()) or 1.0
            for b, w in weights.items():
                if w > 1e-4:
                    groups[b].add([v.index], w / total, "REPLACE")

    def dress_pieces(self, objs, build, add, slot):
        """The home's garments (wardrobe.py), on the body's own rings."""
        return wardrobe.dress_pieces(self, objs, build, slot)

    def headgear(self):
        """The home's headgear (wardrobe.py), hung from the head bone."""
        return wardrobe.headgear(self)

    def weight(self, objs):
        r = self.r
        if self.ANATOMY:
            self.weight_anatomy(objs["Body"])
            weight_all(objs["Head"], "head")
            self._weight_dress(objs)
            for o in objs.values():
                skin_to(o, r.arm)
                r.skinned.append(o)
            return
        zj = [self.joint(b, "z") for b in DEFORM["trunk"]]
        weight_chain(objs["Body"], zj, "z", DEFORM["trunk"])
        weight_all(objs["Head"], "head")
        for side, sign in (("l", 1), ("r", -1)):
            xj = [self.joint(b, "x") for b in DEFORM["arm." + side]]
            weight_chain(objs["Arm_" + side], xj, "x", DEFORM["arm." + side], sign)
            weight_all(objs["Hand_" + side], "hand." + side)
            lz = [self.joint(b, "z") for b in DEFORM["leg." + side]]
            # The leg's chain runs downward: reverse so the stretches read low to high.
            bones = DEFORM["leg." + side][:3]
            joints = lz[:3]
            weight_chain_down(objs["Leg_" + side], joints, bones)
            weight_all(objs["Foot_" + side], "foot." + side)
        self._weight_dress(objs)
        for o in objs.values():
            skin_to(o, r.arm)
            r.skinned.append(o)

    def _weight_dress(self, objs):
        zj = [self.joint(b, "z") for b in DEFORM["trunk"]]
        for name, chain in getattr(self, "chains", {}).items():
            ob = objs[name]
            if self.ANATOMY:
                self.weight_anatomy(ob)
            elif chain == "trunk":
                weight_chain(ob, zj, "z", DEFORM["trunk"])
            elif chain.startswith("arm."):
                side = chain[-1]
                sign = 1 if side == "l" else -1
                weight_chain(ob, [self.joint(b, "x") for b in DEFORM[chain]], "x", DEFORM[chain], sign)
            elif chain.startswith("leg."):
                lz = [self.joint(b, "z") for b in DEFORM[chain]]
                weight_chain_down(ob, lz[:3], DEFORM[chain][:3])

    def shape_keys(self):
        """Three builds of every mesh with the same topology: fit is the base, lean and heavy
        its shape keys."""
        fit = self.build_meshes("fit")
        for build in ("lean", "heavy"):
            other = self.build_meshes(build)
            for name, ob in fit.items():
                if not ob.data.shape_keys:
                    ob.shape_key_add(name="Basis", from_mix=False)
                key = ob.shape_key_add(name=build, from_mix=False)
                src = other[name].data.vertices
                for i, v in enumerate(ob.data.vertices):
                    key.data[i].co = src[i].co
            for ob in other.values():
                bpy.data.objects.remove(ob)
        return fit

    # --- what hangs from the head --------------------------------------------------------

    def eyes(self):
        (x0, x1), (y0, y1), (z0, z1) = self.head_extents()
        hw, hh = (x1 - x0) / 2, z1 - z0
        cz = z0 + hh * 0.56
        pieces = []
        for sign in (1, -1):
            for name, mat, rad, forward in (("Eye", "eye_white", 0.0155, 0.0), ("Iris", "iris", 0.0085, 0.0095)):
                bm = bmesh.new()
                bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=rad)
                # The face is at -Y: the eye sits in its socket, carved into the head, a little inset.
                yf = y0 + 0.02 - forward
                bmesh.ops.translate(bm, vec=Vector((sign * hw * 0.42, yf, cz)), verts=bm.verts)
                ob = pk._bm_object("%s_%s" % (name, "l" if sign > 0 else "r"), bm, self.mats[mat])
                pk._smooth(ob)
                pieces.append(ob)
        return pieces

    def face(self):
        """The carved features: a brow ridge, a nose, lips and ears, each a small mesh at the
        front of the head, sized by the home's parameters. Skin material, so the tone covers them."""
        (x0, x1), (y0, y1), (z0, z1) = self.head_extents()
        hw, hh = (x1 - x0) / 2, z1 - z0
        front = y0
        skin = self.mats["skin"]
        pieces = []
        # the brow is carved into the head itself (anatomy.py); no piece for it.
        # the nose: a wedge down the middle, longer or shorter, wider or narrower
        nose, nw = self.fp("nose"), self.fp("noseWidth")
        nz_top = z0 + hh * 0.57
        nz_tip = nz_top - 0.065 * nose
        pts = [Vector((0, front + 0.006, nz_top)), Vector((0, front - 0.008 * nose, (nz_top + nz_tip) / 2)), Vector((0, front - 0.018 * nose, nz_tip))]
        rad = [0.009 * nw, 0.013 * nw, 0.016 * nw]
        ob = pk._bm_object("Face_nose", pk._tube_bm(pts, rad, segments=8), skin)
        pk._smooth(ob)
        pieces.append(ob)
        # the lips: two short tubes across the mouth, fuller for full lips
        lips = self.fp("lips")
        mz = z0 + hh * 0.33
        for name, dz, r in (("Face_lip_upper", 0.006, 0.007 * lips), ("Face_lip_lower", -0.006, 0.009 * lips)):
            pts2 = [Vector((-hw * 0.3, front - 0.004, mz + dz)), Vector((0, front - 0.009 * lips, mz + dz)), Vector((hw * 0.3, front - 0.004, mz + dz))]
            ob2 = pk._bm_object(name, pk._tube_bm(pts2, [r * 0.6, r, r * 0.6], segments=8), skin)
            pk._smooth(ob2)
            pieces.append(ob2)
        # the ears: flattened discs at the sides, at eye height
        ears = self.fp("ears")
        ez = z0 + hh * 0.55
        for sign in (1, -1):
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.022 * ears)
            bmesh.ops.scale(bm, vec=(0.35, 0.9, 1.25), verts=bm.verts)
            bmesh.ops.translate(bm, vec=Vector((sign * (hw * 0.98 + 0.004), (y0 + y1) / 2 + 0.01, ez)), verts=bm.verts)
            ob3 = pk._bm_object("Face_ear_%s" % ("l" if sign > 0 else "r"), bm, skin)
            pk._smooth(ob3)
            pieces.append(ob3)
        return pieces

    def sockets(self):
        """Empties where marks and changes hang, each on its bone (docs/bodies-plan.md)."""
        (x0, x1), (y0, y1), (z0, z1) = self.head_extents()
        body = self.parts["Body"]
        by0, by1 = self.r.extent([body], 1)
        chest_z = self.joint("chest", "z") + 0.12 * self.k
        hips_z = self.joint("hips", "z")
        wrist = self.joint("wrist.l", "x")
        z_arm = self.joint("upperarm.l", "z")
        spec = [
            ("socket_head", "head", Vector((0, (y0 + y1) / 2, z1))),
            ("socket_eyes", "head", Vector((0, y0, z0 + (z1 - z0) * 0.56))),
            ("socket_throat", "head", Vector((0, y0 + 0.02, z0 - 0.02))),
            ("socket_back", "chest", Vector((0, by1, chest_z))),
            ("socket_light", "chest", Vector((0, by0, chest_z))),
            ("socket_tail", "hips", Vector((0, by1, hips_z + 0.02))),
            ("socket_hand_l", "hand.l", Vector((wrist + 0.03, 0, z_arm))),
            ("socket_hand_r", "hand.r", Vector((-wrist - 0.03, 0, z_arm))),
        ]
        out = []
        for name, bone, at in spec:
            e = bpy.data.objects.new(name, None)
            e.empty_display_type = "PLAIN_AXES"
            e.empty_display_size = 0.05
            bpy.context.collection.objects.link(e)
            e.location = at
            out.append((e, bone))
        return out

    def hang(self, pieces):
        """Parent each (object, bone) to its bone, keeping its place in the world."""
        bpy.context.view_layer.update()
        for ob, bone in pieces:
            ob.parent = self.r.arm
            ob.parent_type = "BONE"
            ob.parent_bone = bone
            bpy.context.view_layer.update()
            ob.matrix_world = Matrix.Identity(4) @ Matrix.Translation(ob.location) if ob.type == "EMPTY" else Matrix.Identity(4)
            self.r.attached.append(ob)

    # --- build and export ---------------------------------------------------------------

    def build(self):
        self.parts = self.shape_keys()
        # the finish: folds in the hanging garments, the cavity occlusion in every mesh
        for name, ob in self.parts.items():
            if name.startswith("Dress_") and any(w in name for w in ("coat", "robe", "kaftan", "kilt", "wrapskirt", "hakama", "tunic", "vest")):
                displace_folds(ob, 0.006, 9.0, 14.0, float(hash(name) % 7))
            bake_cavity(ob)
        self.weight(self.parts)
        if self.ANATOMY:
            self.hang([(e, "head") for e in self.head_pieces])
            self.hang(list(getattr(self, "dress_rigid", [])))
        else:
            self.hang([(e, "head") for e in self.eyes()])
            self.hang([(f, "head") for f in self.face()])
        self.hang([(h, "head") for h in self.headgear()])
        self.hang(self.sockets())
        self.r.head_box = self.head_extents()
        if self.ANATOMY:
            hair_mat = self.mats["hair"]
            centre = self.head_centre
            pieces = hd.hair(self.parts["Head"], centre, self.sex, lambda k: float(self.face_p.get(k, 1.0)), hair_mat)
            self.hang([(h, "head") for h in pieces])
            self.r.measured["hair"] = len(pieces)
        else:
            pk.add_hair(self.r)
        self.r.measured["body"] = self.id
        (_, _), (_, _), (hz0, hz1) = self.head_extents()
        self.r.measured["heads_tall"] = round(self.r.extent()[1] / (hz1 - hz0), 2)
        return self

    def export(self):
        path = os.path.join(OUT, self.id + ".glb")
        os.makedirs(OUT, exist_ok=True)
        self.r.arm.data.pose_position = "POSE"
        bpy.ops.object.select_all(action="DESELECT")
        for o in [self.r.arm] + self.r.skinned + self.r.attached:
            o.select_set(True)
        bpy.context.view_layer.objects.active = self.r.arm
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                                  export_animations=True, export_animation_mode="ACTIONS", export_skins=True,
                                  export_morph=True, export_morph_normal=False, export_materials="EXPORT")
        info = pk.check_glb(path, os.path.join(pk.SRC, "Knight.glb"), require_texture=False, require_accessories=False)
        info["sockets"] = sorted(o.name for o in self.r.attached if o.type == "EMPTY")
        info["shape_keys"] = sorted({k.name for o in self.r.skinned if o.data.shape_keys for k in o.data.shape_keys.key_blocks if k.name != "Basis"})
        log("wrote", os.path.relpath(path, ROOT), "%d KB" % (os.path.getsize(path) // 1024), self.r.measured)
        return info


def _chain_weights(t, joints, bones, blends=None):
    """The weights of one position along a chain lofted upward (see weight_chain); blends[i]
    is the half-width of the blend at joints[i + 1]."""
    weights = {}
    for i, b in enumerate(bones):
        lo = joints[i] if i > 0 else -1e9
        hi = joints[i + 1] if i + 1 < len(bones) else 1e9
        w = 1.0
        if lo > -1e8:
            w *= _smooth((t - lo) / (blends[i - 1] if blends else BLEND))
        if hi < 1e8:
            w *= 1.0 - _smooth((t - hi) / (blends[i] if blends else BLEND))
        if w > 1e-4:
            weights[b] = w
    return weights


def _chain_weights_down(z, joints, bones, blends=None):
    weights = {}
    for i, b in enumerate(bones):
        hi = joints[i] if i > 0 else 1e9
        lo = joints[i + 1] if i + 1 < len(bones) else -1e9
        w = 1.0
        if hi < 1e8:
            w *= 1.0 - _smooth((z - hi) / (blends[i - 1] if blends else BLEND))
        if lo > -1e8:
            w *= _smooth((z - lo) / (blends[i] if blends else BLEND))
        if w > 1e-4:
            weights[b] = w
    return weights


def _mix(a, b, t):
    """Two weight sets blended: (1 - t) of a, t of b."""
    out = {}
    for k, w in a.items():
        out[k] = out.get(k, 0.0) + w * (1.0 - t)
    for k, w in b.items():
        out[k] = out.get(k, 0.0) + w * t
    return out


def weight_chain_down(ob, joints, bones):
    """A chain lofted down Z (the legs): bones[i] owns the stretch below joints[i]."""
    groups = {b: ob.vertex_groups.new(name=b) for b in bones}
    for v in ob.data.vertices:
        z = (ob.matrix_world @ v.co).z
        weights = {}
        for i, b in enumerate(bones):
            hi = joints[i] if i > 0 else 1e9
            lo = joints[i + 1] if i + 1 < len(bones) else -1e9
            w = 1.0
            if hi < 1e8:
                w *= 1.0 - _smooth((z - hi) / BLEND)
            if lo > -1e8:
                w *= _smooth((z - lo) / BLEND)
            if w > 1e-4:
                weights[b] = w
        total = sum(weights.values()) or 1.0
        for b, w in weights.items():
            groups[b].add([v.index], w / total, "REPLACE")


def build(body_id):
    home, sex = body_id.rsplit("-", 1)
    return Body(home, sex).build().export()


# ======================================================================================
# The sheet: both sexes, three builds, bare and in motion
# ======================================================================================

def render_sheet(home="alexandria", samples=32, res=(400, 640)):
    cards = os.path.join(SCRATCH, "body_cards")
    row = []
    for sex in SEXES:
        glb = os.path.join(OUT, "%s-%s.glb" % (home, sex))
        for build in BUILDS:
            row.append(pk.render_card(glb, "%s %s %s" % (home, sex, build), os.path.join(cards, "%s_%s_%s.png" % (home, sex, build)),
                                      anim="Idle", samples=samples, res=res, hair="crop", headgear=False, shape_key=build))
    motion = []
    for sex in SEXES:
        glb = os.path.join(OUT, "%s-%s.glb" % (home, sex))
        motion.append(pk.render_card(glb, "%s %s run" % (home, sex), os.path.join(cards, "%s_%s_run.png" % (home, sex)), anim="Running_A", at=0.3, samples=samples, res=res, hair="long", headgear=False))
        motion.append(pk.render_card(glb, "%s %s slice" % (home, sex), os.path.join(cards, "%s_%s_slice.png" % (home, sex)), anim="1H_Melee_Attack_Slice_Horizontal", at=0.45, samples=samples, res=res, hair="tail", headgear=False))
        motion.append(pk.render_card(glb, "%s %s close" % (home, sex), os.path.join(cards, "%s_%s_close.png" % (home, sex)), anim="Idle", samples=samples, res=res, hair="knot", headgear=False, focus=0.72))
    pk.tile(row + motion, os.path.join(SCRATCH, "body_sheet.png"), 6, res)




# ======================================================================================
# Parts: what a blood's marks hang on the sockets (data/people-features.json). Each is built
# at its socket's origin in the body's frame (Z up, the face at -Y; a hand part in the left
# hand's frame, +X along the fingers; the game mirrors it for the right) and exported alone.
# ======================================================================================

PARTS_OUT = os.path.join(OUT, "parts")
HORN = (0.62, 0.52, 0.4, 1)   # bone-pale, so it reads against dark hair and skin
HIDE = (0.38, 0.12, 0.1, 1)
FEATHER = (0.9, 0.88, 0.82, 1)
SCALE = (0.25, 0.5, 0.38, 1)
FUR = (0.42, 0.3, 0.18, 1)
GILL = (0.55, 0.3, 0.32, 1)


def _ob(name, bm, mat):
    return pk._bm_object(name, bm, mat)


def part_horns():
    mat = pk._material("horn", HORN, rough=0.6)
    out = []
    for sign in (1, -1):
        pts = [Vector((sign * 0.045, 0.0, -0.02)), Vector((sign * 0.07, -0.01, 0.05)), Vector((sign * 0.09, -0.03, 0.12)), Vector((sign * 0.085, -0.07, 0.17))]
        ob = _ob("Horn_%s" % ("l" if sign > 0 else "r"), pk._tube_bm(pts, [0.022, 0.017, 0.011, 0.003]), mat)
        pk._smooth(ob)
        out.append(ob)
    return out


def part_tail():
    mat = pk._material("hide", HIDE, rough=0.8)
    pts = [Vector((0, 0.02, 0.0)), Vector((0, 0.16, -0.08)), Vector((0, 0.28, -0.24)), Vector((0, 0.3, -0.42)), Vector((0, 0.24, -0.56))]
    tail = _ob("Tail", pk._tube_bm(pts, [0.03, 0.026, 0.02, 0.014, 0.008]), mat)
    pk._smooth(tail)
    tip = _ob("Tail_tip", pk._box_bm(Vector((-0.035, 0.2, -0.64)), Vector((0.035, 0.28, -0.56)), taper=(0.2, 0.6)), mat)
    return [tail, tip]


def part_wings():
    mat = pk._material("feather", FEATHER, rough=0.9)
    out = []
    for sign in (1, -1):
        # A folded wing: a flat loft along the wing's spine, broad in the middle, from the back.
        spine = [Vector((sign * 0.03, 0.02, 0.02)), Vector((sign * 0.16, 0.08, 0.2)), Vector((sign * 0.3, 0.12, 0.26)), Vector((sign * 0.34, 0.16, 0.0)), Vector((sign * 0.3, 0.18, -0.3)), Vector((sign * 0.22, 0.18, -0.5))]
        chord = [0.03, 0.08, 0.1, 0.12, 0.09, 0.03]
        rings = []
        for p, c in zip(spine, chord):
            rings.append((p, Vector((0, 0.012, 0)), Vector((c * 0.5 * sign, 0, c * 0.2))))
        ob = loft("Wing_%s" % ("l" if sign > 0 else "r"), rings)
        ob.data.materials.append(mat)
        out.append(ob)
    return out


def _scales(name, centres, r, mat):
    out = []
    for i, c in enumerate(centres):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=r)
        bmesh.ops.scale(bm, vec=(1.0, 0.45, 1.0), verts=bm.verts)
        bmesh.ops.translate(bm, vec=c, verts=bm.verts)
        ob = _ob("%s_%d" % (name, i), bm, mat)
        pk._smooth(ob)
        out.append(ob)
    return out


def part_scales_throat():
    mat = pk._material("scale", SCALE, rough=0.5)
    cs = [Vector((x, -0.004 + abs(x) * 0.3, z)) for z in (0.0, -0.03, -0.055) for x in (-0.04, -0.013, 0.013, 0.04)]
    return _scales("Scale", cs, 0.014, mat)


def part_scales_hand():
    mat = pk._material("scale", SCALE, rough=0.5)
    cs = [Vector((x, y, 0.022)) for x in (0.03, 0.07, 0.11) for y in (-0.02, 0.02)]
    out = []
    for i, c in enumerate(cs):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.013)
        bmesh.ops.scale(bm, vec=(1.0, 1.0, 0.4), verts=bm.verts)
        bmesh.ops.translate(bm, vec=c, verts=bm.verts)
        ob = _ob("Scale_%d" % i, bm, mat)
        pk._smooth(ob)
        out.append(ob)
    return out


def part_gill_lines():
    mat = pk._material("gill", GILL, rough=0.7)
    out = []
    for sign in (1, -1):
        for i, y in enumerate((-0.02, 0.0, 0.02)):
            lo = Vector((sign * 0.052 - 0.006, y - 0.004, -0.06))
            hi = Vector((sign * 0.052 + 0.006, y + 0.004, -0.02))
            out.append(_ob("Gill_%s_%d" % ("l" if sign > 0 else "r", i), pk._box_bm(lo, hi), mat))
    return out


def part_fur_ears():
    mat = pk._material("fur", FUR, rough=0.95)
    out = []
    for sign in (1, -1):
        pts = [Vector((sign * 0.06, 0.0, -0.02)), Vector((sign * 0.085, 0.0, 0.06)), Vector((sign * 0.1, -0.01, 0.14))]
        ob = _ob("Ear_%s" % ("l" if sign > 0 else "r"), pk._tube_bm(pts, [0.03, 0.02, 0.004], segments=8), mat)
        pk._smooth(ob)
        out.append(ob)
    return out


def part_claws():
    mat = pk._material("horn", HORN, rough=0.6)
    out = []
    for i, y in enumerate((-0.033, -0.011, 0.011, 0.033)):
        pts = [Vector((0.12, y, -0.004)), Vector((0.155, y, -0.01)), Vector((0.175, y, -0.022))]
        ob = _ob("Claw_%d" % i, pk._tube_bm(pts, [0.009, 0.006, 0.0015], segments=6), mat)
        pk._smooth(ob)
        out.append(ob)
    return out




def part_trim():
    """The rank's trim: a collar ring at the neck's base and a band at each cuff would need
    the arms; the collar alone reads at the game's distance. Material "trim": the game colours
    it by the archetype's Shape."""
    mat = pk._material("trim", (0.85, 0.7, 0.3, 1), rough=0.5)
    pts = []
    n = 20
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        pts.append(Vector((0.085 * math.cos(a), 0.075 * math.sin(a) + 0.01, -0.055 - 0.01 * math.cos(a))))
    ob = _ob("Trim_collar", pk._tube_bm(pts, [0.012] * (n + 1), segments=8), mat)
    pk._smooth(ob)
    return [ob]


def part_cape():
    """A cloak from the shoulders to the calves, hung from the back socket; material "cape",
    which the game colours by the look (and threads with the bonded genius's colour)."""
    mat = pk._material("cape", (0.5, 0.42, 0.36, 1), rough=0.95)
    rings = []
    spine = [(0.0, 0.03), (0.08, 0.02), (0.3, 0.015), (0.6, 0.02), (0.85, 0.03)]   # drop below the socket, y-offset back
    widths = [0.2, 0.24, 0.26, 0.3, 0.34]
    for (drop, back), w in zip(spine, widths):
        rings.append((Vector((0, back, -drop)), Vector((w / 2, 0, 0)), Vector((0, 0.012, 0))))
    ob = loft("Cape", rings)
    ob.data.materials.append(mat)
    return [ob]


PARTS = {
    "trim": part_trim, "cape": part_cape,
    "horns": part_horns, "tail": part_tail, "wings": part_wings, "scales-throat": part_scales_throat,
    "scales-hand": part_scales_hand, "gill-lines": part_gill_lines, "fur-ears": part_fur_ears, "claws": part_claws,
}


def build_parts(which=None):
    os.makedirs(PARTS_OUT, exist_ok=True)
    for pid, fn in PARTS.items():
        if which and pid not in which:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obs = fn()
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        path = os.path.join(PARTS_OUT, pid + ".glb")
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_animations=False, export_materials="EXPORT")
        log("wrote", os.path.relpath(path, ROOT), "%d KB" % max(1, os.path.getsize(path) // 1024), "%d objects" % len(obs))


# ======================================================================================
# The blood sheet: every blood that shows, on both bodies, its marks hung and its skin tinted
# as the game does it (data/bloods.json marks, data/people-features.json).
# ======================================================================================

def _features_data():
    import json
    feats = json.load(open(os.path.join(ROOT, "data", "people-features.json")))["features"]
    bloods = json.load(open(os.path.join(ROOT, "data", "bloods.json")))
    return feats, bloods


def render_blood_card(glb, label, path, marks, feats, samples=32, res=(400, 640), focus=0.0):
    """A body card with the marks of one blood: the parts imported and parented to their
    sockets, the skin and iris tinted."""
    def dress(scene):
        skin = bpy.data.materials.get("skin")
        iris = bpy.data.materials.get("iris")
        tone = Vector((0.66, 0.49, 0.35))
        arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
        for fid in marks:
            f = feats[fid]
            if f["kind"] == "tint":
                t = Vector(f["tint"])
                tone = tone.lerp(t, f.get("strength", 0.5))
            elif f["kind"] == "eyes" and iris:
                iris.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = tuple(f["iris"]) + (1,)
                if f.get("emission", 0) > 0:
                    iris.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = tuple(f["iris"]) + (1,)
                    iris.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = f["emission"]
            elif f["kind"] == "glow" and skin:
                skin.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = tuple(f["glow"]) + (1,)
                skin.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = f.get("strength", 0.35) * 2.0
            elif f["kind"] == "part" and arm:
                for sock in f["sockets"]:
                    before = set(bpy.data.objects)
                    bpy.ops.import_scene.gltf(filepath=os.path.join(PARTS_OUT, f["part"] + ".glb"))
                    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
                    sock_ob = bpy.data.objects.get(sock)
                    for o in new:
                        o.name = "Part_" + o.name
                        if sock_ob is not None:
                            o.parent = sock_ob
                            o.matrix_parent_inverse = Matrix.Identity(4)
                            if sock.endswith("_r"):
                                o.scale.x = -1.0
                        else:
                            o.parent = arm
                            o.parent_type = "BONE"
                            o.parent_bone = sock
        if skin:
            skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (tone.x, tone.y, tone.z, 1)
    return pk.render_card(glb, label, path, anim="Idle", samples=samples, res=res, hair="crop", headgear=False, focus=focus, after_import=dress, shown_prefixes=("Part_",))


def render_blood_sheet(home="alexandria", samples=24, res=(360, 560)):
    feats, bloods = _features_data()
    cards = os.path.join(SCRATCH, "blood_cards")
    showing = [b for b in bloods if b.get("marks")]
    out = []
    for b in showing:
        for sex in SEXES:
            glb = os.path.join(OUT, "%s-%s.glb" % (home, sex))
            out.append(render_blood_card(glb, "%s %s" % (b["name"], sex), os.path.join(cards, "%s_%s.png" % (b["id"], sex)), b["marks"], feats, samples=samples, res=res, focus=0.55))
    pk.tile(out, os.path.join(SCRATCH, "blood_sheet.png"), 6, res)


def render_faces_sheet(samples=24, res=(300, 420)):
    """Every home's two faces, close, bare-headed."""
    cards = os.path.join(SCRATCH, "face_cards")
    out = []
    for home in HOMES:
        for sex in SEXES:
            glb = os.path.join(OUT, "%s-%s.glb" % (home, sex))
            if not os.path.exists(glb):
                continue
            out.append(pk.render_card(glb, "%s %s" % (home, sex), os.path.join(cards, "%s_%s.png" % (home, sex)), anim="Idle", samples=samples, res=res, hair="crop", headgear=False, focus=0.88, view=(0.45, -1.0, 0.2)))
    pk.tile(out, os.path.join(SCRATCH, "faces_sheet.png"), 8, res)


if __name__ == "__main__":
    args = sys.argv[1:]
    want_sheet = not args or "sheet" in args
    if not args or "parts" in args:
        build_parts()
    wanted = [a for a in args if a not in ("sheet", "parts", "bloods", "faces")] or (["%s-%s" % (h, x) for h in HOMES for x in SEXES] if not args else [])
    if "all" in wanted:
        wanted = ["%s-%s" % (h, x) for h in HOMES for x in SEXES]
    results = {}
    for body_id in wanted:
        results[body_id] = build(body_id)
    for body_id, info in results.items():
        log(body_id, info)
    if want_sheet:
        render_sheet()
    if "bloods" in args:
        render_blood_sheet()
    if "faces" in args:
        render_faces_sheet()
