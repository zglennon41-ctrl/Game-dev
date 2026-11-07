"""WILDLINE body kit: the people of the thirteen cities, built as the game's own bodies on
the KayKit bones so the seventy-six animations keep playing (docs/bodies-plan.md). Run
headless with Blender's Python module:

    python tools/blender/body_kit.py                 # every body this file knows, then the sheet
    python tools/blender/body_kit.py alexandria-m    # one body
    python tools/blender/body_kit.py sheet           # only the sheet, from the exported files

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
BLEND = 0.07   # how far either side of a joint two bones share a vertex

SKIN = (0.72, 0.52, 0.40, 1)        # a middle tone; the game sets the chosen one
TUNIC = (0.30, 0.26, 0.34, 1)
TROUSERS = (0.16, 0.15, 0.17, 1)
BOOTS = (0.12, 0.09, 0.07, 1)
EYE_WHITE = (0.92, 0.9, 0.86, 1)
IRIS = (0.12, 0.09, 0.07, 1)


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
    return [
        (0.135, 0.075 * s * k, 0.08 * s * k),
        (0.21, 0.08 * s * k, 0.085 * s * k),
        (0.36, 0.065 * s * k, 0.07 * s * k),
        (0.518, 0.054 * s * k, 0.058 * s * k),
        (0.64, 0.06 * s * k, 0.062 * s * k),
        (0.82, 0.046 * s * k, 0.05 * s * k),
        (0.925, 0.038 * s, 0.042 * s),
    ]


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
    return [
        (1.09, 0.095 * s * k, 0.105 * s * k),
        (0.95, 0.09 * s * k, 0.098 * s * k),
        (0.75, 0.075 * s * k, 0.08 * s * k),
        (0.57, 0.062 * s * k, 0.068 * s * k),
        (0.42, 0.068 * s * k, 0.075 * s * k),
        (0.25, 0.048 * s * k, 0.055 * s * k),
        (0.14, 0.042 * s, 0.048 * s),
    ]


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

class Body:
    def __init__(self, home, sex):
        self.home, self.sex = home, sex
        self.id = "%s-%s" % (home, sex)
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
                     [("skin", SKIN), ("tunic", TUNIC), ("trousers", TROUSERS), ("boots", BOOTS), ("eye_white", EYE_WHITE), ("iris", IRIS)]}
        self.parts = {}

    # --- the meshes ------------------------------------------------------------------

    def joint(self, bone, axis):
        b = self.r.arm.data.bones[bone]
        p = self.r.MA @ b.head_local
        return p.z if axis == "z" else abs(p.x)

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

    def build_meshes(self, build):
        """The body's meshes for one build, all named; returns {name: object}."""
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
        head = add(loft("Head", rings_z(self.scaled(head_rings(sex), head=True)), lambda i: slot["skin"]))
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
        return objs

    def weight(self, objs):
        r = self.r
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
        for o in objs.values():
            skin_to(o, r.arm)
            r.skinned.append(o)

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
        head = self.parts["Head"]
        x0, x1 = self.r.extent([head], 0)
        y0, y1 = self.r.extent([head], 1)
        z0, z1 = self.r.extent([head], 2)
        hw, hh = (x1 - x0) / 2, z1 - z0
        cz = z0 + hh * 0.56
        pieces = []
        for sign in (1, -1):
            for name, mat, rad, forward in (("Eye", "eye_white", 0.02, 0.0), ("Iris", "iris", 0.011, 0.012)):
                bm = bmesh.new()
                bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=rad)
                # The face is at -Y: the eye sits in the front of the head, a little inset.
                yf = y0 + 0.012 - forward
                bmesh.ops.translate(bm, vec=Vector((sign * hw * 0.42, yf, cz)), verts=bm.verts)
                ob = pk._bm_object("%s_%s" % (name, "l" if sign > 0 else "r"), bm, self.mats[mat])
                pk._smooth(ob)
                pieces.append(ob)
        return pieces

    def sockets(self):
        """Empties where marks and changes hang, each on its bone (docs/bodies-plan.md)."""
        head = self.parts["Head"]
        x0, x1 = self.r.extent([head], 0)
        y0, y1 = self.r.extent([head], 1)
        z0, z1 = self.r.extent([head], 2)
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
        self.weight(self.parts)
        self.hang([(e, "head") for e in self.eyes()])
        self.hang(self.sockets())
        pk.add_hair(self.r)
        self.r.measured["body"] = self.id
        self.r.measured["heads_tall"] = round(self.r.extent()[1] / (self.r.extent(self.r.mesh_named("Head"), 2)[1] - self.r.extent(self.r.mesh_named("Head"), 2)[0]), 2)
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


if __name__ == "__main__":
    args = sys.argv[1:]
    want_sheet = not args or "sheet" in args
    wanted = [a for a in args if a != "sheet"] or (["alexandria-m", "alexandria-f"] if not args else [])
    results = {}
    for body_id in wanted:
        results[body_id] = build(body_id)
    for body_id, info in results.items():
        log(body_id, info)
    if want_sheet:
        render_sheet()
