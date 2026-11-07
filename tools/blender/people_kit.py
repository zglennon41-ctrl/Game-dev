"""WILDLINE people kit: the five KayKit "Adventurers" bodies reshaped from chibi to grounded
proportions on their own rig, so every animation the game plays by name still plays. Run
headless with Blender's Python module:

    python tools/blender/people_kit.py              # every body, then the contact sheets
    python tools/blender/people_kit.py Knight       # one body
    python tools/blender/people_kit.py sheet        # only the sheets, from the exported files
    python tools/blender/people_kit.py hair         # the hair and beard sheet, from the exported Knight

Method (the beast kit's): import game/assets/kaykit/<Body>.glb, then move groups of vertices by
their vertex-group weights together with the rest positions of the matching bones, so the baked
animations still bend the body at its joints. Rigid accessories parented to bones (helmet, hat,
cape, the hidden weapons on the hand slots) are carried along in world space and stay parented
to the same bones, so Godot still finds them as BoneAttachment3D nodes. Baked translation keys
(the hips' bounce, the root, the IK helpers) are scaled with the limb they belong to, so Idle,
Walking and Running neither sink nor float. Textures and materials are left exactly as imported
and embedded again on export. Every bone name and animation name survives; the export is
parsed afterwards to prove it.

World space here is Blender's: Z up, the body faces -Y, the rest pose a T-pose. KayKit's chibi
stands 2.3 units with a 1.1-unit head (about two heads tall); PROPORTIONS below turns that
into a figure of six heads and more (see `measure`), then scales it back to HEIGHT units so the
game's camera, hit volumes and the weapons on the hand slots fit as before.
"""
import json
import math
import os
import struct
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "game", "assets", "kaykit")
OUT = os.path.join(ROOT, "game", "assets", "people")
SCRATCH = os.environ.get("WILDLINE_SCRATCH", "/tmp/claude-0/-home-user-Game-dev/b1283b3f-7fcd-5800-b25d-5095be347307/scratchpad")

BODIES = ["Knight", "Mage", "Rogue", "Rogue_Hooded", "Barbarian"]

# The animations the game plays by name (game/scripts/world.gd).
ANIMS = ["Idle", "Walking_A", "Running_A", "Walking_Backwards", "Blocking", "Block_Hit", "Hit_A", "Hit_B", "Death_A",
         "1H_Melee_Attack_Slice_Horizontal", "1H_Melee_Attack_Slice_Diagonal", "1H_Melee_Attack_Chop", "2H_Melee_Attack_Chop",
         "2H_Melee_Attack_Spin", "2H_Melee_Attack_Slam", "1H_Ranged_Shoot", "Spellcast_Shoot", "Spellcast_Raise", "Dodge_Forward",
         "Dodge_Backward", "Running_Strafe_Left", "Running_Strafe_Right", "Death_A_Pose", "1H_Ranged_Aiming", "2H_Ranged_Aiming",
         "Spellcasting"]
# Accessory nodes the game shows (world.gd hides every other bone attachment).
ACCESSORY_WORDS = ("Helmet", "Hat", "Cape", "Hood")
# The hair and beards built below hang from the head bone too; the game shows the one the look names.
HAIR_WORDS = ("Hair_", "Beard_")
# The one-handed weapon each body carries in the file, shown on the motion sheet only.
WEAPON_SHOWN = {"Knight": "1H_Sword", "Mage": "1H_Wand", "Rogue": "Knife", "Rogue_Hooded": "Knife", "Barbarian": "1H_Axe"}

# The reshaping, in the chibi's units (hip joint at 0.519, ankle at 0.145, knee at 0.292,
# shoulder at 1.107, neck at 1.241, crown at 2.315). Designers tune these.
PROPORTIONS = {
    "head": (0.37, 0.39, 0.42),   # head and whatever hangs from the head bone (helmet, hat), about the neck joint
    "head_lift": 0.06,            # a little neck: the head carried up off the shoulders
    "thigh": 2.9,                 # hip to knee, along the leg
    "shin": 3.7,                  # knee to ankle; the foot keeps its height
    "leg_girth": 0.9,             # legs thinner across
    "torso": 1.45,                # hip joint to neck, along the spine
    "torso_width": 0.86,          # shoulders and hips narrower
    "arm_girth": 0.8,             # arms thinner across
    "hang": 0.5,                  # where the fingertips hang: 0 = hip joint, 1 = knee
    "height": 2.4,                # the finished body, crown of the bare head, in model units
}

# Bone groups. The leg and arm IK helpers hang off the root with baked positions of their own
# and deform nothing; they are carried along so the file stays tidy.
LEG_HELPERS = {"l": ["kneeIK.l", "control-toe-roll.l"], "r": ["kneeIK.r", "control-toe-roll.r"]}
ARM_HELPERS = {"l": ["elbowIK.l", "handIK.l"], "r": ["elbowIK.r", "handIK.r"]}
TORSO = ["hips", "spine", "chest"]

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def log(*a):
    print("[people_kit]", *a)


# ======================================================================================
# The rig: one KayKit body, with ways to move its meshes, accessories and bones together.
# ======================================================================================

class Rig:
    def __init__(self, body):
        self.body = body
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, body + ".glb"))
        self.arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
        scene_objects = set(bpy.context.scene.objects)
        # The skinned meshes (body, head, arms, legs) and the rigid accessories parented to bones.
        self.skinned = [o for o in scene_objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
        self.attached = [o for o in scene_objects if o.type == "MESH" and o.parent is self.arm and o.parent_type == "BONE"]
        # Anything else the importer made (an unexported icosphere) stays out of the export.
        for o in list(bpy.data.objects):
            if o.type == "MESH" and o not in self.skinned and o not in self.attached:
                bpy.data.objects.remove(o)
        self.MA = self.arm.matrix_world.copy()
        self.MAinv = self.MA.inverted()
        # Build in the rest pose: the accessories' world matrices must come from the rest bones.
        self.arm.data.pose_position = "REST"
        self._edit(lambda ebs: [setattr(eb, "use_connect", False) for eb in ebs])
        bpy.context.view_layer.update()
        self.key_factors = {}       # bone -> factor for its baked location keys
        self.measured = {}

    # --- bones ------------------------------------------------------------------------

    def _edit(self, fn):
        """Run fn(edit_bones) with the armature in edit mode."""
        bpy.ops.object.select_all(action="DESELECT")
        self.arm.select_set(True)
        bpy.context.view_layer.objects.active = self.arm
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            fn(self.arm.data.edit_bones)
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
            self.arm.select_set(False)

    def all_bones(self):
        return [b.name for b in self.arm.data.bones]

    def family(self, *roots):
        """The named bones and every bone under them."""
        out = []
        for r in roots:
            stack = [self.arm.data.bones[r]]
            while stack:
                b = stack.pop()
                out.append(b.name)
                stack.extend(b.children)
        return out

    def bone(self, name):
        """A bone's rest position (its head) in world space."""
        return self.MA @ self.arm.data.bones[name].head_local

    def legs(self, side=None):
        sides = [side] if side else ["l", "r"]
        return [b for s in sides for b in self.family("upperleg." + s, *LEG_HELPERS[s])]

    def arms(self, side=None):
        sides = [side] if side else ["l", "r"]
        return [b for s in sides for b in self.family("upperarm." + s, *ARM_HELPERS[s])]

    def head(self):
        return self.family("head")

    def others(self, *groups):
        """Every bone but the root and the given groups."""
        skip = {"root"} | {b for g in groups for b in g}
        return [b for b in self.all_bones() if b not in skip]

    # --- deformation: meshes, accessories and bones move together -------------------

    def _weights(self, mesh, bones):
        idx = {mesh.vertex_groups[b].index for b in bones if b in mesh.vertex_groups}
        return [min(1.0, sum(g.weight for g in v.groups if g.group in idx)) for v in mesh.data.vertices]

    def deform(self, bones, T, spatial=False):
        """Move the vertices weighted to `bones` by T (world space -> world space), each by its
        weight; the accessories parented to those bones with them, whole; and the rest positions
        of the bones. Bone directions are kept, so the baked rotations still mean the same.
        With spatial=True the map applies to everything whatever its weights."""
        names = set(self.all_bones() if spatial else bones)
        for o in self.skinned:
            M = o.matrix_world
            Minv = M.inverted()
            weights = None if spatial else self._weights(o, names)
            for i, v in enumerate(o.data.vertices):
                w = 1.0 if spatial else weights[i]
                if w <= 0:
                    continue
                p = M @ v.co
                v.co = Minv @ (p + (T(p) - p) * w)
        targets = {}
        for o in self.attached:
            if spatial or o.parent_bone in names:
                W = o.matrix_world.copy()
                targets[o] = [T(W @ v.co) for v in o.data.vertices]

        def move(ebs):
            for eb in ebs:
                if eb.name not in names:
                    continue
                head = self.MA @ eb.head
                delta = (self.MAinv @ T(head)) - eb.head
                eb.head = eb.head + delta
                eb.tail = eb.tail + delta
        self._edit(move)
        bpy.context.view_layer.update()
        for o, pts in targets.items():
            Winv = o.matrix_world.inverted()
            for v, p in zip(o.data.vertices, pts):
                v.co = Winv @ p

    def scale(self, bones, pivot, s, spatial=False):
        pivot = Vector(pivot)
        s = Vector(s) if not isinstance(s, (int, float)) else Vector((s, s, s))
        self.deform(bones, lambda p: pivot + Vector((s.x * (p.x - pivot.x), s.y * (p.y - pivot.y), s.z * (p.z - pivot.z))), spatial=spatial)

    def shift(self, bones, d, spatial=False):
        d = Vector(d)
        self.deform(bones, lambda p: p + d, spatial=spatial)

    def scale_along(self, bones, pivot, axis, k):
        pivot = Vector(pivot)
        n = Vector(axis).normalized()
        self.deform(bones, lambda p: p + n * ((k - 1.0) * (p - pivot).dot(n)))

    def lengthen_chain(self, chain, tip, pivot, end, k):
        """Stretch a chain of bones along the axis from pivot to end by k, carrying the tip bones
        (a hand on an arm) along unchanged."""
        axis = end - pivot
        self.scale_along(chain, pivot, axis, k)
        if tip:
            self.shift(tip, axis * (k - 1.0))

    # --- the baked animation ---------------------------------------------------------------

    def scale_location_keys(self, factors):
        """Multiply the baked location keys of each bone by its factor (pose-space keys are
        relative to the rest position, so a raised hip keeps its bounce and gets it scaled)."""
        for a in bpy.data.actions:
            for layer in a.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fc in cb.fcurves:
                            if not fc.data_path.endswith(".location"):
                                continue
                            b = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
                            k = factors.get(b, 1.0)
                            if abs(k - 1.0) < 1e-9:
                                continue
                            for kp in fc.keyframe_points:
                                kp.co[1] *= k
                                kp.handle_left[1] *= k
                                kp.handle_right[1] *= k

    def uniform(self, k):
        """The whole body k times as big, baked translation keys included."""
        self.scale([], (0, 0, 0), k, spatial=True)
        self.scale_location_keys({b: k for b in self.all_bones()})

    # --- reading the shape -------------------------------------------------------------

    def extent(self, objects=None, axis=2):
        pts = [o.matrix_world @ v.co for o in (objects or self.skinned) for v in o.data.vertices]
        return min(p[axis] for p in pts), max(p[axis] for p in pts)

    def mesh_named(self, word):
        return [o for o in self.skinned if word in o.name]

    def measure(self):
        """Height, head height and heads-tall of the bare body (helmets and hats not counted)."""
        lo, hi = self.extent()
        head_lo, head_hi = self.extent(self.mesh_named("Head"))
        return {"height": round(hi - lo, 3), "head": round(head_hi - head_lo, 3), "heads_tall": round((hi - lo) / max(1e-6, head_hi - head_lo), 2),
                "hip": round(self.bone("upperleg.l").z, 3), "knee": round(self.bone("lowerleg.l").z, 3), "shoulder": round(self.bone("upperarm.l").z, 3)}

    # --- export -----------------------------------------------------------------------------

    def export(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.arm.data.pose_position = "POSE"
        bpy.ops.object.select_all(action="DESELECT")
        for o in [self.arm] + self.skinned + self.attached:
            o.select_set(True)
        bpy.context.view_layer.objects.active = self.arm
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                                  export_animations=True, export_animation_mode="ACTIONS", export_skins=True,
                                  export_image_format="AUTO", export_materials="EXPORT")
        info = check_glb(path, os.path.join(SRC, self.body + ".glb"))
        log("wrote", os.path.relpath(path, ROOT), "%d KB" % (os.path.getsize(path) // 1024), self.measured)
        return info


# ======================================================================================
# The reshaping: chibi to grounded, every body the same way.
# ======================================================================================

def reshape(r, P=PROPORTIONS):
    before = r.measure()
    legs, arms, head = r.legs(), r.arms(), r.head()
    # --- legs: thigh and shin stretched along the leg about the ankle; the foot keeps its height.
    za, zk, zh = r.bone("foot.l").z, r.bone("lowerleg.l").z, r.bone("upperleg.l").z
    kt, ks = P["thigh"], P["shin"]

    def leg_z(z):
        if z <= za:
            return z
        if z <= zk:
            return za + ks * (z - za)
        return za + ks * (zk - za) + kt * (z - zk)
    r.deform(legs, lambda p: Vector((p.x, p.y, leg_z(p.z))))
    rise = leg_z(zh) - zh
    # Everything above the hips rides up with them, so the feet stay on the ground.
    r.shift(r.others(legs), (0, 0, rise))
    for s, sign in (("l", 1), ("r", -1)):
        x = r.bone("upperleg." + s).x
        r.scale(r.legs(s), (x, 0, 0), (P["leg_girth"], P["leg_girth"], 1))
    hip_ratio = r.bone("upperleg.l").z / zh
    # --- torso: longer along the spine about the hip joint, narrower across; the arms and head
    # carried up with their joints, the limbs in with the narrower shoulders and hips.
    z0 = r.bone("upperleg.l").z
    w, k_torso = P["torso_width"], P["torso"]
    z_shoulder, z_neck = r.bone("upperarm.l").z, r.bone("head").z
    x_shoulder, x_hip = r.bone("upperarm.l").x, r.bone("upperleg.l").x
    r.scale(TORSO, (0, 0, z0), (w, 1, k_torso))
    for s, sign in (("l", 1), ("r", -1)):
        r.shift(r.arms(s), (-sign * (1 - w) * x_shoulder, 0, (k_torso - 1) * (z_shoulder - z0)))
        r.shift(r.legs(s), (-sign * (1 - w) * x_hip, 0, 0))
    r.shift(head, (0, 0, (k_torso - 1) * (z_neck - z0)))
    # --- head: smaller about the neck joint, then lifted a little to give it a neck.
    neck = r.bone("head")
    r.scale(head, (0, neck.y, neck.z), P["head"])
    r.shift(head, (0, 0, P["head_lift"]))
    # --- arms: long enough that the fingertips hang where `hang` says between hip and knee.
    for s, sign in (("l", 1), ("r", -1)):
        shoulder, wrist = r.bone("upperarm." + s), r.bone("wrist." + s)
        arm_mesh = r.mesh_named("Arm" + ("Left" if s == "l" else "Right"))
        xlo, xhi = r.extent(arm_mesh, axis=0)
        fingertip = xhi if sign > 0 else xlo
        hand_len = abs(fingertip - wrist.x)
        z_hang = r.bone("upperleg." + s).z + P["hang"] * (r.bone("lowerleg." + s).z - r.bone("upperleg." + s).z)
        reach = shoulder.z - z_hang
        k_arm = max(1.0, (reach - hand_len) / max(1e-6, abs(wrist.x - shoulder.x)))
        chain = ["upperarm." + s, "lowerarm." + s, "elbowIK." + s]
        tip = ["wrist." + s, "hand." + s, "handslot." + s, "handIK." + s]
        r.lengthen_chain(chain, tip, shoulder, wrist, k_arm)
        r.scale(r.arms(s), (0, shoulder.y, shoulder.z), (1, P["arm_girth"], P["arm_girth"]))
        for b in chain + tip:
            r.key_factors[b] = k_arm
        r.measured["arm_" + s] = round(k_arm, 2)
    # --- the baked translations: the hips' bounce and the root with the hip height, the thighs'
    # own keys with the thigh, the IK helpers with their limb.
    for b in ("hips", "root") + tuple(b for s in LEG_HELPERS for b in LEG_HELPERS[s]):
        r.key_factors[b] = hip_ratio
    for s in ("l", "r"):
        r.key_factors["upperleg." + s] = kt
        r.key_factors["lowerleg." + s] = ks
    r.scale_location_keys(r.key_factors)
    # --- the finished body back to the game's size.
    tall = r.measure()
    k = P["height"] / tall["height"]
    r.uniform(k)
    r.measured.update({"before": before, "after": r.measure(), "uniform": round(k, 3), "hip_ratio": round(hip_ratio, 2)})
    return r


def check_glb(path, src_path=None, require_texture=True, require_accessories=True):
    """Parse the exported file and prove the game will find what it needs: every animation
    under its name, a skin, the meshes bound to it, and the accessory nodes the source had."""
    def parse(p):
        d = open(p, "rb").read()
        length = struct.unpack("<I", d[12:16])[0]
        return json.loads(d[20:20 + length])
    j = parse(path)
    names = [a.get("name") for a in j.get("animations", [])]
    # The game's names the source has must survive (KayKit has no 2H_Melee_Attack_Slam, say).
    have = [a.get("name") for a in parse(src_path).get("animations", [])] if src_path else ANIMS
    missing = [a for a in ANIMS if a in have and a not in names]
    skins = j.get("skins", [])
    mesh_nodes = [n for n in j["nodes"] if "mesh" in n]
    skinned = [n for n in mesh_nodes if "skin" in n]
    node_names = [n.get("name", "") for n in j["nodes"]]
    accessories = sorted(n for n in node_names if any(w in n for w in ACCESSORY_WORDS))
    problems = []
    if missing:
        problems.append("missing animations: %s" % missing)
    if not skins:
        problems.append("no skins")
    if not skinned:
        problems.append("mesh node has no skin")
    bones = set()
    if skins:
        bones = {node_names[i] for i in skins[0]["joints"]}
        for b in ("handslot.r", "handslot.l", "head"):
            if b not in bones:
                problems.append("no bone %s" % b)
    if src_path:
        sj = parse(src_path)
        s_names = [n.get("name", "") for n in sj["nodes"]]
        s_acc = sorted(n for n in s_names if any(w in n for w in ACCESSORY_WORDS))
        lost = [n for n in s_acc if n not in accessories]
        if lost and require_accessories:
            problems.append("accessory nodes lost: %s" % lost)
        s_bones = {s_names[i] for i in sj["skins"][0]["joints"]}
        if s_bones != bones:
            problems.append("bones changed: %s" % sorted(s_bones ^ bones))
        s_anims = [a.get("name") for a in sj.get("animations", [])]
        lost_anims = [a for a in s_anims if a not in names]
        if lost_anims:
            problems.append("animations lost: %s" % lost_anims)
        # Each accessory still hangs from the bone it hung from.
        def parent_of(nodes, i):
            for pi, n in enumerate(nodes):
                if i in n.get("children", []):
                    return nodes[pi].get("name")
            return None
        for i, n in enumerate(j["nodes"]):
            nm = n.get("name", "")
            if "mesh" in n and "skin" not in n and nm in s_names:
                si = s_names.index(nm)
                if parent_of(sj["nodes"], si) != parent_of(j["nodes"], i):
                    problems.append("%s moved from bone %s to %s" % (nm, parent_of(sj["nodes"], si), parent_of(j["nodes"], i)))
    images = j.get("images", [])
    if require_texture and (not images or not all("bufferView" in im or "uri" in im for im in images)):
        problems.append("no texture image")
    if problems:
        raise RuntimeError("%s: %s" % (path, "; ".join(problems)))
    return {"animations": len(names), "joints": len(skins[0]["joints"]), "skinned_meshes": len(skinned), "accessories": accessories,
            "materials": [m.get("name") for m in j.get("materials", [])], "images": [(im.get("name"), im.get("mimeType"), "embedded" if "bufferView" in im else im.get("uri")) for im in images]}


# ======================================================================================
# Hair and beards: low-poly pieces hung from the head bone, one node per style, the game
# shows the one the character's look names and tints it. Each is built about the head mesh
# as measured after the reshaping, so every body wears the same styles at the same place.
# A style with a fall (long, braid, tail) is two nodes: the cap, hidden under a helmet, and
# the fall, which hangs from under it either way.
# ======================================================================================

HAIR_STYLES = ["crop", "long", "braid", "knot", "tail"]
BEARD_STYLES = ["short", "full"]


def _bm_object(name, bm, material):
    import bmesh  # noqa: F401 - bmesh is used by the callers; imported here to keep the module light
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def _smooth(ob):
    for poly in ob.data.polygons:
        poly.use_smooth = True


def _cap_bm(c, rx, ry, rz, cut_z, tilt):
    """The top of a squashed sphere about centre c, cut by a plane through z=cut_z that
    tilts down toward the back (+Y) by `tilt`: a hairline higher at the brow than the nape."""
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=10, radius=1.0)
    bmesh.ops.scale(bm, vec=(rx, ry, rz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    no = Vector((0, -tilt, 1)).normalized()
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, c.y, cut_z), plane_no=no, clear_inner=True)
    # Close the cut with a flat underside so the cap is solid from every angle.
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges)
    return bm


def _tube_bm(points, radii, segments=10):
    """A tube through `points` (world), ring radius radii[i] at each: braids and tails."""
    import bmesh
    bm = bmesh.new()
    rings = []
    for i, (p, r) in enumerate(zip(points, radii)):
        d = (points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized()
        u = d.cross(Z if abs(d.dot(Z)) < 0.9 else X).normalized()
        w = d.cross(u).normalized()
        ring = []
        for k in range(segments):
            a = 2 * math.pi * k / segments
            ring.append(bm.verts.new(p + (u * math.cos(a) + w * math.sin(a)) * r))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(segments):
            bm.faces.new((a[k], a[(k + 1) % segments], b[(k + 1) % segments], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _box_bm(lo, hi, taper=(1.0, 1.0)):
    """A box from lo to hi (world); the bottom face scaled across by taper (x, y) about its centre."""
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    c = (lo + hi) / 2
    sz = hi - lo
    for v in bm.verts:
        t = v.co.z + 0.5  # 0 at the bottom, 1 at the top
        kx = taper[0] + (1 - taper[0]) * t
        ky = taper[1] + (1 - taper[1]) * t
        v.co = Vector((c.x + v.co.x * sz.x * kx, c.y + v.co.y * sz.y * ky, c.z + v.co.z * sz.z))
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=min(sz) * 0.18, segments=2, affect="EDGES")
    return bm


def add_hair(r):
    """Every style on the body, each hung from the head bone. The game shows one."""
    heads = r.mesh_named("Head")
    x0, x1 = r.extent(heads, 0)
    y0, y1 = r.extent(heads, 1)
    z0, z1 = r.extent(heads, 2)
    hw, hd, hh = (x1 - x0) / 2, (y1 - y0) / 2, z1 - z0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    brow = z0 + hh * 0.66               # the hairline at the brow, above the eyes
    crown = Vector((cx, cy + hd * 0.05, z0 + hh * 0.62))
    chin = z0 + hh * 0.08
    front = y0                          # the face is at -Y
    back = y1
    hair = _material("hair", (0.16, 0.11, 0.08), rough=0.85)
    pieces = []

    def cap(name):
        bm = _cap_bm(crown, hw * 1.08, hd * 1.07, hh * 0.46, brow, 0.5)
        ob = _bm_object(name, bm, hair)
        _smooth(ob)
        return ob

    for style in HAIR_STYLES:
        pieces.append(cap("Hair_%s_cap" % style))
    # long: a fall down the back to the shoulder blades, wider at the bottom
    pieces.append(_bm_object("Hair_long_fall", _box_bm(Vector((cx - hw * 1.0, back - hd * 0.5, z0 - hh * 0.75)), Vector((cx + hw * 1.0, back + hd * 0.25, brow + hh * 0.3)), taper=(1.1, 0.7)), hair))
    # braid: a plait from the nape, thick and thin by turns
    n = 9
    pts = [Vector((cx, back + hd * 0.2 + 0.02 * math.sin(i / 2.0), brow + hh * 0.1 - (i / (n - 1)) * hh * 1.25)) for i in range(n)]
    rad = [hw * (0.3 if i % 2 == 0 else 0.22) * (1.0 - 0.35 * i / (n - 1)) for i in range(n)]
    ob = _bm_object("Hair_braid_fall", _tube_bm(pts, rad), hair)
    _smooth(ob)
    pieces.append(ob)
    # knot: a bun high on the back of the head
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
    bmesh.ops.scale(bm, vec=(hw * 0.5, hd * 0.45, hh * 0.22), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((cx, back + hd * 0.25, z0 + hh * 0.86)), verts=bm.verts)
    ob = _bm_object("Hair_knot_fall", bm, hair)
    _smooth(ob)
    pieces.append(ob)
    # tail: a high tail that swings out and down behind
    pts = [Vector((cx, back + hd * 0.15 + hd * 0.9 * math.sin(math.pi * i / 8.0), z0 + hh * 0.85 - (i / 7.0) * hh * 0.95)) for i in range(8)]
    rad = [hw * 0.34 * (1.0 - 0.6 * i / 7.0) for i in range(8)]
    ob = _bm_object("Hair_tail_fall", _tube_bm(pts, rad), hair)
    _smooth(ob)
    pieces.append(ob)
    # beards: short along the jaw; full, hanging to the collarbone
    pieces.append(_bm_object("Beard_short", _box_bm(Vector((cx - hw * 0.92, front - hd * 0.03, z0 - hh * 0.03)), Vector((cx + hw * 0.92, front + hd * 0.6, z0 + hh * 0.16)), taper=(0.85, 0.85)), hair))
    pieces.append(_bm_object("Beard_full", _box_bm(Vector((cx - hw * 0.85, front - hd * 0.08, z0 - hh * 0.5)), Vector((cx + hw * 0.85, front + hd * 0.6, z0 + hh * 0.2)), taper=(0.5, 0.5)), hair))
    bpy.context.view_layer.update()
    for ob in pieces:
        ob.parent = r.arm
        ob.parent_type = "BONE"
        ob.parent_bone = "head"
        bpy.context.view_layer.update()
        ob.matrix_world = Matrix.Identity(4)
    r.attached += pieces
    r.measured["hair"] = len(pieces)
    return pieces


def build(body):
    r = reshape(Rig(body))
    add_hair(r)
    return r.export(os.path.join(OUT, body + ".glb"))


# ======================================================================================
# The contact sheets: moonlit cards, the five bodies before and after, and in motion.
# ======================================================================================

def _material(name, color, rough=0.8, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1)
    bsdf.inputs["Roughness"].default_value = rough
    if emission:
        bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return m


def render_card(glb, label, path, anim=None, at=0.0, weapon=None, samples=32, res=(400, 640), hair=None, beard=None, headgear=True, focus=0.0, shape_key=None, after_import=None, shown_prefixes=()):
    """One body from a file, three-quarter from the front right, in moonlight with a faint lamp
    from the other side; in the rest pose, or `at` (0..1) of the way through `anim`. The
    accessories are shown as the game shows them (helmet, hat, cape, hood), plus `weapon`."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=glb)
    arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    if after_import:
        after_import(scene)
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        if o not in set(scene.objects) or o.name.startswith("Icosphere"):
            o.hide_render = True
        elif o.name.startswith(tuple(shown_prefixes)) if shown_prefixes else False:
            o.hide_render = False
        elif o.parent_type == "BONE" or (o.parent is not None and o.parent.type == "EMPTY"):
            shown = (any(w in o.name for w in ACCESSORY_WORDS) and headgear) or (weapon and o.name == weapon) or o.name.startswith(("Eye", "Iris"))
            if o.name.startswith("Hair_"):
                shown = hair is not None and o.name.startswith("Hair_%s_" % hair) and (headgear is False or o.name.endswith("_fall"))
            elif o.name.startswith("Beard_"):
                shown = beard is not None and o.name == "Beard_%s" % beard
            o.hide_render = not shown
    # A build: the named shape key all the way on (the body kit's lean and heavy).
    for o in bpy.data.objects:
        if o.type == "MESH" and o.data.shape_keys:
            for k in o.data.shape_keys.key_blocks:
                k.value = 1.0 if (shape_key and k.name == shape_key) else 0.0
    frame = 1
    if arm and arm.animation_data:
        arm.animation_data.action = None
        for t in arm.animation_data.nla_tracks:
            t.mute = not (anim and t.name == anim)
            if anim and t.name == anim and t.strips:
                s = t.strips[0]
                frame = int(round(s.frame_start + at * (s.frame_end - s.frame_start)))
        for pb in arm.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((9e9, 9e9, 9e9))
    hi = Vector((-9e9, -9e9, -9e9))
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        oe = o.evaluated_get(dg)
        for v in oe.to_mesh().vertices:
            w = oe.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        oe.to_mesh_clear()
    log(label, anim or "rest", "frame", frame, "bounds", tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
    # The ground, wet slate, with a ruled line at the feet so a sunk or floating foot shows.
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(_material("ground", (0.03, 0.032, 0.04), rough=0.55))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.002))
    bpy.context.active_object.scale = (4.0, 0.01, 1.0)
    bpy.context.active_object.data.materials.append(_material("rule", (0.5, 0.45, 0.3), rough=1.0, emission=(0.9, 0.8, 0.6), strength=0.8))
    try:
        fc = bpy.data.curves.new(label, type="FONT")
        fc.body = label
        fc.size = 0.3
        fc.align_x = "CENTER"
        fo = bpy.data.objects.new("label", fc)
        fo.location = Vector(((lo.x + hi.x) / 2, lo.y - 0.6, 0.01))
        bpy.context.collection.objects.link(fo)
        fo.data.materials.append(_material("label", (0.85, 0.75, 0.55), rough=1.0, emission=(0.9, 0.8, 0.6), strength=0.6))
    except Exception as e:  # noqa: BLE001 - a missing font only loses the label
        log("no label:", e)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z / 2))
    size = max(hi.z, 1.0)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 60
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    from bpy_extras.object_utils import world_to_camera_view
    direction = Vector((0.8, -1.0, 0.35)).normalized()
    aim = centre
    # `focus`: fit the frame from this height up (0.75 frames the head and shoulders).
    zlo = hi.z * focus
    if focus > 0:
        aim = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (zlo + hi.z) / 2))
        size = max(hi.z - zlo, 0.5)
    corners = [Vector((x, y, z)) for x in (lo.x - 0.05, hi.x + 0.05) for y in (lo.y - (0.7 if focus == 0 else 0.1), hi.y + 0.05) for z in (zlo, hi.z + 0.05)]
    dist = size * 1.0
    for _ in range(100):
        cam.location = aim + direction * dist
        cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        ndc = [world_to_camera_view(scene, cam, c) for c in corners]
        if all(0.02 < p.x < 0.98 and 0.02 < p.y < 0.98 for p in ndc):
            break
        dist *= 1.03

    def light(name, kind, at, color, energy, size_=1.0):
        ld = bpy.data.lights.new(name, kind)
        ld.color = color
        ld.energy = energy
        if kind == "AREA":
            ld.size = size_
        if kind == "SUN":
            ld.angle = math.radians(4)
        lo_ = bpy.data.objects.new(name, ld)
        lo_.location = at
        lo_.rotation_euler = (centre - Vector(at)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(lo_)

    light("moon", "SUN", centre + Vector((size * 0.5, size * 0.9, size * 1.2)), (0.55, 0.64, 1.0), 2.0)
    light("lamp", "AREA", centre + Vector((-size * 1.2, -size * 1.2, size * 0.7)), (1.0, 0.6, 0.35), 55 * size * size, size * 0.4)
    light("fill", "AREA", centre + Vector((size * 1.0, -size * 1.2, size * 0.4)), (0.45, 0.55, 0.95), 60 * size * size, size * 0.7)
    world = bpy.data.worlds.new("night")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.015, 0.03, 1)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4 if os.environ.get("WILDLINE_FAST") else samples
    scene.cycles.use_denoising = False
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Filmic" if "Filmic" in [i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "AgX"
    scene.view_settings.look = "None"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def tile(cards, path, cols, res):
    import numpy as np
    w, h = res
    rows = (len(cards) + cols - 1) // cols
    sheet = np.zeros((rows * h, cols * w, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    for i, card in enumerate(cards):
        img = bpy.data.images.load(card)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
        r, c = i // cols, i % cols
        y0 = (rows - 1 - r) * h
        sheet[y0:y0 + h, c * w:c * w + w] = px[:h, :w]
        bpy.data.images.remove(img)
    out = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    out.pixels = sheet.ravel().tolist()
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    log("wrote", path)


def render_sheets(bodies=None, samples=32, res=(400, 640)):
    """Two sheets: the five before (KayKit) over the five after (ours), standing at the start
    of Idle; then the five after mid-stride in Running_A over mid-swing in
    1H_Melee_Attack_Slice_Horizontal, the one-handed weapon in hand."""
    bodies = bodies or BODIES
    cards = os.path.join(SCRATCH, "people_cards")
    rest = [render_card(os.path.join(SRC, b + ".glb"), b + " (KayKit)", os.path.join(cards, b + "_before.png"), anim="Idle", samples=samples, res=res) for b in bodies]
    rest += [render_card(os.path.join(OUT, b + ".glb"), b, os.path.join(cards, b + "_after.png"), anim="Idle", samples=samples, res=res) for b in bodies]
    tile(rest, os.path.join(SCRATCH, "people_sheet.png"), len(bodies), res)
    motion = [render_card(os.path.join(OUT, b + ".glb"), b + " run", os.path.join(cards, b + "_run.png"), anim="Running_A", at=0.3, weapon=WEAPON_SHOWN.get(b), samples=samples, res=res) for b in bodies]
    motion += [render_card(os.path.join(OUT, b + ".glb"), b + " slice", os.path.join(cards, b + "_slice.png"), anim="1H_Melee_Attack_Slice_Horizontal", at=0.45, weapon=WEAPON_SHOWN.get(b), samples=samples, res=res) for b in bodies]
    tile(motion, os.path.join(SCRATCH, "people_sheet_motion.png"), len(bodies), res)


def render_hair_sheet(body="Knight", samples=32, res=(400, 640)):
    """One body wearing every hair style bare-headed, then under its headgear, then the beards."""
    cards = os.path.join(SCRATCH, "people_cards")
    glb = os.path.join(OUT, body + ".glb")
    row1 = [render_card(glb, "%s %s" % (body, h), os.path.join(cards, "hair_%s.png" % h), anim="Idle", samples=samples, res=res, hair=h, headgear=False) for h in HAIR_STYLES]
    row2 = [render_card(glb, "%s %s, helm" % (body, h), os.path.join(cards, "hair_%s_helm.png" % h), anim="Idle", samples=samples, res=res, hair=h, headgear=True) for h in HAIR_STYLES]
    row3 = [render_card(glb, "%s bare" % body, os.path.join(cards, "hair_bare.png"), anim="Idle", samples=samples, res=res, hair=None, headgear=False)]
    row3 += [render_card(glb, "%s %s beard" % (body, b), os.path.join(cards, "beard_%s.png" % b), anim="Idle", samples=samples, res=res, hair="crop", beard=b, headgear=False) for b in BEARD_STYLES]
    row3 += [render_card(glb, "%s run, braid" % body, os.path.join(cards, "hair_run.png"), anim="Running_A", at=0.3, samples=samples, res=res, hair="braid", beard="short", headgear=False)]
    row3 += [render_card(glb, "%s slice, long" % body, os.path.join(cards, "hair_slice.png"), anim="1H_Melee_Attack_Slice_Horizontal", at=0.45, weapon=WEAPON_SHOWN.get(body), samples=samples, res=res, hair="long", headgear=False)]
    row4 = [render_card(glb, "%s %s, close" % (body, h), os.path.join(cards, "hair_%s_close.png" % h), anim="Idle", samples=samples, res=res, hair=h, beard=("full" if h == "crop" else "short" if h == "tail" else None), headgear=False, focus=0.72) for h in HAIR_STYLES]
    tile(row1 + row2 + row3 + row4, os.path.join(SCRATCH, "people_sheet_hair.png"), len(HAIR_STYLES), res)


if __name__ == "__main__":
    args = sys.argv[1:]
    want_sheet = not args or "sheet" in args
    want_hair = "hair" in args
    wanted = [a for a in args if a not in ("sheet", "hair")] or (BODIES if not args else [])
    results = {}
    for body in wanted:
        results[body] = build(body)
    for body, info in results.items():
        log(body, info)
    if want_sheet:
        render_sheets()
    if want_hair:
        render_hair_sheet()
