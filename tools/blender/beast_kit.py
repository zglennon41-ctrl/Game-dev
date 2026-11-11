"""WILDLINE beast kit: five beasts built on the Quaternius wolf's rig, so they walk, bite,
flinch and die with the wolf's animations. Run headless with Blender's Python module:

    python tools/blender/beast_kit.py              # every beast, then the contact sheet
    python tools/blender/beast_kit.py ruin-stag    # one beast
    python tools/blender/beast_kit.py sheet        # only the contact sheet, from the exported files

Method: import game/assets/quaternius/Wolf.glb, then reshape it per beast by moving groups of
vertices (by their vertex-group weights) and the matching bones' rest positions together, so the
baked animations still bend the body at its joints. New low-poly parts (antlers, fins, plates,
seams) are built in place and joined to the body with their vertices weighted to the right bone.
Materials are recoloured and renamed; any material whose name starts with "field" glows in the
game. Each beast exports to game/assets/beasts/<id>.glb with every animation kept under its
original name ("AnimalArmature|Walk" ...); the export is parsed afterwards to prove it.

World space here is Blender's: Z up, the wolf faces -Y, about 5.3 units long and 2.6 tall
(the game scales it). The IK foot bones carry baked foot positions that only fit the wolf's
own leg lengths, so every reshaped beast moves its feet onto the leg chain (fk_feet) first;
cut-wolf keeps the original weights and proves the pipeline alone changes nothing.
"""
import json
import math
import os
import struct
import sys

import bpy
import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style  # noqa: E402  (the game's one style: data/style.json, docs/style.md)
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WOLF = os.path.join(ROOT, "game", "assets", "quaternius", "Wolf.glb")
OUT = os.path.join(ROOT, "game", "assets", "beasts")
SCRATCH = os.environ.get("WILDLINE_SCRATCH", "/tmp/claude-0/-home-user-Game-dev/b1283b3f-7fcd-5800-b25d-5095be347307/scratchpad")

# The animations the game plays by name (game/scripts/world.gd), plus the pack's extras.
ANIMS = ["AnimalArmature|Attack", "AnimalArmature|Death", "AnimalArmature|Gallop", "AnimalArmature|Idle",
         "AnimalArmature|Idle_2_HeadLow", "AnimalArmature|Idle_HitReact_Left", "AnimalArmature|Idle_HitReact_Right",
         "AnimalArmature|Walk", "AnimalArmature|Eating", "AnimalArmature|Idle_2", "AnimalArmature|Gallop_Jump",
         "AnimalArmature|Jump_ToIdle"]

# The spine, tail tip to nose, for parts that run along the back.
SPINE = ["Tail8", "Tail7", "Tail6", "Tail5", "Tail4", "Tail3", "Tail2", "Tail1", "Back", "Torso", "Torso2", "Torso3",
         "Neck1", "Neck2", "Neck3", "Head"]
TORSO = ["Body", "Back", "Torso", "Torso2", "Torso3"]
NECK = ["Neck1", "Neck2", "Neck3"]
# Foot and IK helper bones whose weights move onto the leg chain for a reshaped beast.
FK_FEET = {"FF.L": "FrontLowerLeg.L", "IKFrontLeg.L": "FrontLowerLeg.L", "PoleTarget.L": "FrontUpperLeg.L", "PoleTargetBack.L": "BackUpperLeg.L",
           "FF.R": "FrontLowerLeg.R", "IKFrontLeg.R": "FrontLowerLeg.R", "PoleTarget.R": "FrontUpperLeg.R", "PoleTargetBack.R": "BackUpperLeg.R",
           "FFB.L": "BackLowerLeg.L", "IKBackLeg.L": "BackLowerLeg.L", "FFB.R": "BackLowerLeg.R", "IKBackLeg.R": "BackLowerLeg.R"}
LEG_ROOTS = {"fl": ("FrontShoulder.L", "IKFrontLeg.L", "PoleTarget.L"), "fr": ("FrontShoulder.R", "IKFrontLeg.R", "PoleTarget.R"),
             "bl": ("BackShoulder.L", "IKBackLeg.L", "PoleTargetBack.L"), "br": ("BackShoulder.R", "IKBackLeg.R", "PoleTargetBack.R")}

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def log(*a):
    print("[beast_kit]", *a)


# ======================================================================================
# The rig: the wolf, with ways to move its mesh and bones together and to grow parts on it.
# ======================================================================================

class Rig:
    def __init__(self, fk_feet=True, weld=False):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=WOLF)
        self.arm = bpy.data.objects["AnimalArmature"]
        self.mesh = bpy.data.objects["Wolf"]
        self.M = self.mesh.matrix_world.copy()          # mesh local -> world
        self.Minv = self.M.inverted()
        self.MA = self.arm.matrix_world.copy()          # armature space -> world
        self.MAinv = self.MA.inverted()
        self.parts = []
        # Nothing but the body and its skeleton is exported.
        for o in list(bpy.data.objects):
            if o.type == "MESH" and o is not self.mesh:
                bpy.data.objects.remove(o)
        self._edit(lambda ebs: [setattr(eb, "use_connect", False) for eb in ebs])
        if weld:
            self.weld()
        if fk_feet:
            self.fk_feet()

    def weld(self):
        """The wolf comes with every face's corners its own (it was made flat). Welded, the body
        is one skin, shaded round (docs/style.md: smooth where it is flesh), and a third the
        size on disk."""
        me = self.mesh.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bm.to_mesh(me)
        bm.free()
        for name in ("custom_normal", "sharp_face", "sharp_edge"):
            if name in me.attributes:
                me.attributes.remove(me.attributes[name])
        for p in me.polygons:
            p.use_smooth = True
        me.update()

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

    def legs(self, *tags):
        """Bones of the legs named by tag (fl, fr, bl, br), feet and IK helpers included."""
        return [b for t in (tags or ("fl", "fr", "bl", "br")) for b in self.family(*LEG_ROOTS[t])]

    def body_bones(self):
        legs = set(self.legs())
        return [b for b in self.all_bones() if b not in legs]

    def bone(self, name):
        """A bone's rest position in world space."""
        return self.MA @ self.arm.data.bones[name].head_local

    # --- weights ------------------------------------------------------------------------

    def _weights(self, bones):
        idx = {self.mesh.vertex_groups[b].index for b in bones if b in self.mesh.vertex_groups}
        out = []
        for v in self.mesh.data.vertices:
            w = sum(g.weight for g in v.groups if g.group in idx)
            out.append(min(1.0, w))
        return out

    def fk_feet(self):
        """Move the foot and IK helper weights onto the leg chain, so the feet follow the legs
        whatever their new length (the IK bones' baked foot positions only fit the wolf)."""
        vgs = self.mesh.vertex_groups
        for src, dst in FK_FEET.items():
            if src not in vgs or dst not in vgs:
                continue
            s, d = vgs[src], vgs[dst]
            for v in self.mesh.data.vertices:
                w = 0.0
                for g in v.groups:
                    if g.group == s.index:
                        w = g.weight
                if w > 0:
                    cur = 0.0
                    for g in v.groups:
                        if g.group == d.index:
                            cur = g.weight
                    d.add([v.index], cur + w, "REPLACE")
                    s.remove([v.index])

    # --- deformation: mesh and bones move together --------------------------------------

    def deform(self, bones, T, rot=None, spatial=False):
        """Move the vertices weighted to `bones` by T (world space -> world space), each by its
        weight, and the rest positions of those bones with them. `rot` is the world rotation
        part of T when T is a rotation, so the bones turn with the flesh. With spatial=True the
        map applies to every vertex and bone whatever its weights."""
        names = set(self.all_bones() if spatial else bones)
        weights = None if spatial else self._weights(names)
        for i, v in enumerate(self.mesh.data.vertices):
            w = 1.0 if spatial else weights[i]
            if w <= 0:
                continue
            p = self.M @ v.co
            v.co = self.Minv @ (p + (T(p) - p) * w)

        def move(ebs):
            for eb in ebs:
                if eb.name not in names:
                    continue
                head = self.MA @ eb.head
                new_head = self.MAinv @ T(head)
                if rot is not None:
                    ra = (self.MAinv.to_3x3() @ rot @ self.MA.to_3x3()).normalized()
                    m = eb.matrix.copy()
                    m.translation = Vector((0, 0, 0))
                    m = ra.to_4x4() @ m
                    m.translation = new_head
                    eb.matrix = m
                else:
                    delta = new_head - eb.head
                    eb.head = eb.head + delta
                    eb.tail = eb.tail + delta
        self._edit(move)

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

    def rotate(self, bones, pivot, axis, angle):
        pivot = Vector(pivot)
        R = Matrix.Rotation(angle, 3, Vector(axis))
        self.deform(bones, lambda p: pivot + R @ (p - pivot), rot=R)

    def stretch_y(self, y0, y1, k):
        """Lengthen the whole body between y0 and y1 (a spatial map: everything behind moves back)."""
        def T(p):
            if p.y < y0:
                return p
            if p.y <= y1:
                return Vector((p.x, y0 + k * (p.y - y0), p.z))
            return Vector((p.x, p.y + (k - 1.0) * (y1 - y0), p.z))
        self.deform([], T, spatial=True)

    def leg_length(self, drop):
        """Shorten the legs by `drop` world units (negative lengthens them): each leg scales
        toward the ground about its own attachment height, and the body comes down (or up) by
        the same amount, so the feet stay on the ground."""
        for tag in ("fl", "fr", "bl", "br"):
            h = self.bone(LEG_ROOTS[tag][0]).z
            k = 1.0 - drop / h
            self.scale(self.legs(tag), (0, 0, 0), (1, 1, k))
        self.shift(self.body_bones(), (0, 0, -drop))

    def leg_girth(self, k):
        """Thicker (k > 1) or thinner legs, each about its own axis."""
        for tag in ("fl", "fr", "bl", "br"):
            bones = self.legs(tag)
            heads = [self.bone(b) for b in bones if not b.startswith(("IK", "PoleTarget"))]
            c = sum(heads, Vector()) / len(heads)
            self.scale(bones, (c.x, c.y, 0), (k, k, 1))

    def lengthen_chain(self, chain, tip, k):
        """Stretch a chain of bones (first to last) along its own axis by k, carrying the tip
        bones (the head on a neck, say) along unchanged."""
        pivot = self.bone(chain[0])
        end = self.bone(tip[0]) if tip else self.bone(chain[-1])
        axis = end - pivot
        self.scale_along(chain, pivot, axis, k)
        if tip:
            self.shift(tip, axis * (k - 1.0))

    def uniform(self, k):
        """The whole beast k times as big, baked foot and root motion included."""
        self.scale([], (0, 0, 0), k, spatial=True)
        for a in bpy.data.actions:
            for layer in a.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fc in cb.fcurves:
                            if fc.data_path.endswith(".location"):
                                for kp in fc.keyframe_points:
                                    kp.co[1] *= k
                                    kp.handle_left[1] *= k
                                    kp.handle_right[1] *= k

    def damp_rotations(self, bones, factor):
        """Quieten the animated rotation of some bones: each key turns `factor` of the way
        from rest (1 = as the wolf does it, 0 = never moves). For a tail that would otherwise
        swing through the ground on a beast that lies low."""
        from mathutils import Quaternion
        names = set(bones)
        for a in bpy.data.actions:
            for layer in a.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        by_bone = {}
                        for fc in cb.fcurves:
                            if fc.data_path.endswith(".rotation_quaternion"):
                                b = fc.data_path.split('"')[1]
                                if b in names:
                                    by_bone.setdefault(b, {})[fc.array_index] = fc
                        for b, comps in by_bone.items():
                            if len(comps) < 4:
                                continue
                            n = min(len(comps[i].keyframe_points) for i in range(4))
                            for k in range(n):
                                q = Quaternion([comps[i].keyframe_points[k].co[1] for i in range(4)])
                                q2 = Quaternion().slerp(q, factor)
                                for i in range(4):
                                    kp = comps[i].keyframe_points[k]
                                    d = q2[i] - kp.co[1]
                                    kp.co[1] += d
                                    kp.handle_left[1] += d
                                    kp.handle_right[1] += d

    def settle(self):
        """Stand the beast on the ground: its lowest point at Z = 0."""
        low = min((self.M @ v.co).z for v in self.mesh.data.vertices)
        if abs(low) > 1e-4:
            self.shift([], (0, 0, -low), spatial=True)

    # --- reading the shape -------------------------------------------------------------

    def world_verts(self):
        return [self.M @ v.co for v in self.mesh.data.vertices]

    def _near(self, pick, window):
        """Vertices passing pick(p, window); the window widens until some are found, so a
        query between two rings of a sparse mesh never comes back empty."""
        verts = self.world_verts()
        for _ in range(6):
            pts = [p for p in verts if pick(p, window)]
            if pts:
                return pts
            window *= 1.6
        return verts

    def top(self, y, half_width=0.18, window=0.14):
        """The height of the back at y."""
        return max(p.z for p in self._near(lambda p, w: abs(p.x) < half_width * (w / window) and abs(p.y - y) < w, window))

    def bottom(self, y, half_width=0.18, window=0.14):
        return min(p.z for p in self._near(lambda p, w: abs(p.x) < half_width * (w / window) and abs(p.y - y) < w, window))

    def side(self, y, z, window=0.14):
        """How far the flank reaches out at (y, z)."""
        return max(abs(p.x) for p in self._near(lambda p, w: abs(p.y - y) < w and abs(p.z - z) < w, window))

    def spine_weights(self, y):
        """Which spine bones carry a point at y along the back: the two around it, blended."""
        heads = [(self.bone(b).y, b) for b in SPINE]
        heads.sort()
        if y <= heads[0][0]:
            return [(heads[0][1], 1.0)]
        if y >= heads[-1][0]:
            return [(heads[-1][1], 1.0)]
        for (y0, b0), (y1, b1) in zip(heads, heads[1:]):
            if y0 <= y <= y1:
                t = (y - y0) / max(1e-6, y1 - y0)
                return [(b0, 1.0 - t), (b1, t)]
        return [(heads[-1][1], 1.0)]

    # --- parts: built in world space, joined to the body, weighted to bones -----------

    def add_part(self, name, verts, faces, weights, mat, smooth=True):
        """verts in world space; weights is a bone name for the whole part or a list, one per
        vertex, of [(bone, weight), ...]."""
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = smooth
        obj = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat)
        groups = {}
        if isinstance(weights, str):
            groups[weights] = [(i, 1.0) for i in range(len(verts))]
        else:
            for i, ws in enumerate(weights):
                for b, w in ws:
                    groups.setdefault(b, []).append((i, w))
        for b, items in groups.items():
            vg = obj.vertex_groups.new(name=b)
            for i, w in items:
                vg.add([i], w, "REPLACE")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        self.mesh.select_set(True)
        bpy.context.view_layer.objects.active = self.mesh
        bpy.ops.object.join()
        self.mesh.select_set(False)
        self.parts.append(name)

    def strip(self, name, columns, weights, mat, smooth=False):
        """A thin closed box along a path: each column is four world points round its
        section (a loop), weights one entry per column."""
        verts, faces, ws = [], [], []
        for col, w in zip(columns, weights):
            verts.extend(col)
            ws.extend([w] * 4)
        n = len(columns)
        for i in range(n - 1):
            for j in range(4):
                a, b = i * 4 + j, i * 4 + (j + 1) % 4
                faces.append((a, b, b + 4, a + 4))
        faces.append((3, 2, 1, 0))
        last = (n - 1) * 4
        faces.append((last, last + 1, last + 2, last + 3))
        self.add_part(name, verts, faces, ws, mat, smooth=smooth)

    def fin(self, name, y0, y1, height, mat, thickness=0.05, steps=18, sink=0.08, serrate=False, under=False):
        """A fin standing on the back (or hanging under the belly) from y0 to y1; height is a
        number or a function of t in [0, 1]."""
        cols, ws = [], []
        for i in range(steps + 1):
            t = i / steps
            y = y0 + (y1 - y0) * t
            h = height(t) if callable(height) else height
            if serrate and i % 2 == 1:
                h *= 0.25
            base = self.bottom(y) + sink if under else self.top(y) - sink
            d = -1.0 if under else 1.0
            z0, z1 = base, base + d * (h + sink)
            tw = thickness * (0.35 if abs(h) < 1e-3 else 1.0)
            cols.append([Vector((-tw / 2, y, z0)), Vector((tw / 2, y, z0)), Vector((tw * 0.15, y, z1)), Vector((-tw * 0.15, y, z1))])
            ws.append(self.spine_weights(y))
        self.strip(name, cols, ws, mat)

    def flank_line(self, name, y0, y1, z_at, mat, height=0.06, depth=0.08, steps=14, side=1):
        """A ridge along one flank from y0 to y1 at height z_at(t), pressed into the hide."""
        cols, ws = [], []
        for i in range(steps + 1):
            t = i / steps
            y = y0 + (y1 - y0) * t
            z = z_at(t) if callable(z_at) else z_at
            x = side * (self.side(y, z) + 0.01)
            xin = x - side * depth
            cols.append([Vector((xin, y, z - height / 2)), Vector((x, y, z - height / 2)), Vector((x, y, z + height / 2)), Vector((xin, y, z + height / 2))])
            ws.append(self.spine_weights(y))
        self.strip(name, cols, ws, mat)

    def tube(self, p0, p1, r0, r1, n=6):
        """Vertices and faces of a tapered tube from p0 to p1 (world space); a closed low-poly cone."""
        p0, p1 = Vector(p0), Vector(p1)
        axis = (p1 - p0).normalized()
        ref = Z if abs(axis.dot(Z)) < 0.9 else X
        u = axis.cross(ref).normalized()
        v = axis.cross(u)
        verts, faces = [], []
        for i in range(n):
            a = 2 * math.pi * i / n
            verts.append(p0 + (u * math.cos(a) + v * math.sin(a)) * r0)
        for i in range(n):
            a = 2 * math.pi * i / n
            verts.append(p1 + (u * math.cos(a) + v * math.sin(a)) * r1)
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
        faces.append(tuple(range(n - 1, -1, -1)))
        faces.append(tuple(range(n, 2 * n)))
        return verts, faces

    def tubes(self, name, segments, bone, mat, n=6):
        """Many tubes [(p0, p1, r0, r1), ...] as one part on one bone."""
        verts, faces = [], []
        for p0, p1, r0, r1 in segments:
            vs, fs = self.tube(p0, p1, r0, r1, n)
            off = len(verts)
            verts.extend(vs)
            faces.extend([tuple(i + off for i in f) for f in fs])
        self.add_part(name, verts, faces, bone, mat, smooth=False)

    def shell(self, name, centre, size, bone, mat, rot=(0, 0, 0), segments=12, rings=6):
        """A domed plate: the top half of a sphere, scaled to size (half-extents), turned by rot."""
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.02], context="VERTS")
        bm.verts.ensure_lookup_table()
        R = Matrix.Rotation(rot[0], 4, X) @ Matrix.Rotation(rot[1], 4, Y) @ Matrix.Rotation(rot[2], 4, Z)
        S = Matrix.Diagonal(Vector(size)).to_4x4()
        T = Matrix.Translation(Vector(centre)) @ R @ S
        verts = [T @ v.co for v in bm.verts]
        idx = {v: i for i, v in enumerate(bm.verts)}
        faces = [tuple(idx[v] for v in f.verts) for f in bm.faces]
        bm.free()
        self.add_part(name, verts, faces, bone, mat, smooth=True)

    # --- materials ------------------------------------------------------------------------

    def recolor(self, old, name, color, rough=0.8, metallic=0.0, emission=None, strength=0.0):
        m = bpy.data.materials[old]
        m.name = name
        self._set_material(m, color, rough, metallic, emission, strength)
        return m

    @staticmethod
    def material(name, color, rough=0.8, metallic=0.0, emission=None, strength=0.0):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        Rig._set_material(m, color, rough, metallic, emission, strength)
        return m

    @staticmethod
    def _set_material(m, color, rough, metallic, emission, strength):
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        color = style.conform(m.name, color)      # on the ramps of what its name says it is
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metallic
        if emission:
            bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1)
            bsdf.inputs["Emission Strength"].default_value = strength

    # --- export -----------------------------------------------------------------------------

    def export(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        self.arm.select_set(True)
        self.mesh.select_set(True)
        bpy.context.view_layer.objects.active = self.arm
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                                  export_animations=True, export_animation_mode="ACTIONS", export_skins=True)
        info = check_glb(path)
        log("wrote", os.path.relpath(path, ROOT), "%d faces, %d KB, parts: %s" % (len(self.mesh.data.polygons), os.path.getsize(path) // 1024, ", ".join(self.parts) or "none"))
        return info


def check_glb(path):
    """Parse the exported file and prove the game will find what it needs: every animation
    under its wolf name, a skin, and the mesh bound to it."""
    d = open(path, "rb").read()
    length = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + length])
    names = [a.get("name") for a in j.get("animations", [])]
    missing = [a for a in ANIMS if a not in names]
    skins = j.get("skins", [])
    mesh_nodes = [n for n in j["nodes"] if "mesh" in n]
    skinned = [n for n in mesh_nodes if "skin" in n]
    problems = []
    if missing:
        problems.append("missing animations: %s" % missing)
    if not skins:
        problems.append("no skins")
    if not skinned:
        problems.append("mesh node has no skin")
    if problems:
        raise RuntimeError("%s: %s" % (path, "; ".join(problems)))
    return {"animations": names, "joints": len(skins[0]["joints"]), "mesh_nodes": len(mesh_nodes), "materials": [m.get("name") for m in j.get("materials", [])]}


# ======================================================================================
# The beasts. World units: the wolf stands 2.6 tall, nose at y = -2.55, tail tip at y = 2.7.
# ======================================================================================

def cut_wolf():
    """The wolf untouched, through the same pipeline: the control."""
    r = Rig(fk_feet=False, weld=True)
    return r


def river_thing():
    """Low and long: a slick blue-black otter-crocodile with a fin ridge down its back, a flat
    paddle tail and small glowing eyes."""
    r = Rig(weld=True)
    head = r.family("Head", "Ear1.L", "Ear1.R")
    body = r.body_bones()
    # Flattened about the belly line, so the legs still meet the body where they did.
    r.scale(body, (0, 0, 1.25), (1.0, 1.0, 0.72))
    # A longer, lower snout; the ears gone to nubs.
    r.scale_along(head, r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.4)
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), 0.3)
    # A long body: the belly stretched, the hindquarters and tail carried back.
    r.stretch_y(-0.6, 0.4, 1.6)
    # Short splayed legs, the body down near the ground.
    r.leg_length(0.62)
    r.scale(r.legs(), (0, 0, 0), (1.35, 1.0, 1.0))
    r.leg_girth(1.15)
    # The tail: longer, then flattened into a paddle from the third joint out.
    tail = r.family("Tail1")
    r.lengthen_chain(tail, [], 1.35)
    paddle = r.family("Tail3")
    pz = sum(r.bone(b).z for b in paddle) / len(paddle)
    r.scale(paddle, (0, 0, pz), (2.6, 1.0, 0.38))
    # A low body: the paddle only follows the wolf's tail swing part of the way, so it stays
    # off the ground when the beast walks.
    r.damp_rotations(tail, 0.6)
    # Materials: wet blue-black hide, eyes that glow.
    hide = r.recolor("Main", "river_hide", (0.022, 0.034, 0.05), rough=0.3)
    r.recolor("Main_Light", "river_hide_light", (0.05, 0.085, 0.1), rough=0.35)
    r.recolor("Eyes_Black", "field_eyes", (0.05, 0.1, 0.12), rough=0.3, emission=(0.45, 0.85, 1.0), strength=3.0)
    r.recolor("Nose", "river_nose", (0.015, 0.015, 0.02), rough=0.5)
    # The fin ridge, serrated, from the neck to the root of the paddle.
    r.fin("fin_ridge", r.bone("Neck2").y, r.bone("Tail3").y, lambda t: 0.3 * math.sin(math.pi * (0.1 + 0.9 * t)) ** 0.6 + 0.04, hide, thickness=0.06, steps=22, serrate=True)
    r.settle()
    return r


def ruin_stag():
    """Tall and gaunt on long legs, pale bone-grey, a wide rack of antlers, a long neck."""
    r = Rig(weld=True)
    head = r.family("Head", "Ear1.L", "Ear1.R")
    # Legs half again as long and thin; the body carried up with them.
    r.leg_length(-0.75)
    r.leg_girth(0.72)
    # Gaunt: a narrow, shallow barrel, the back line kept.
    top = r.top(r.bone("Torso2").y)
    r.scale(TORSO, (0, 0, top), (0.78, 1.0, 0.82))
    # A long neck, raised; the head a little longer, the ears tall.
    r.lengthen_chain(NECK, head, 1.75)
    r.rotate(NECK + head, r.bone("Neck1"), X, math.radians(-28))
    r.scale_along(head, r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.15)
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), (1.1, 1.1, 1.5))
    # A short tail.
    r.scale(r.family("Tail1"), r.bone("Tail1"), 0.35)
    # Materials.
    r.recolor("Main", "stag_hide", (0.26, 0.24, 0.21), rough=0.92)
    r.recolor("Main_Light", "stag_hide_light", (0.4, 0.37, 0.32), rough=0.9)
    r.recolor("Eyes_Black", "stag_eyes", (0.01, 0.01, 0.01), rough=0.3)
    r.recolor("Nose", "stag_nose", (0.06, 0.05, 0.045), rough=0.6)
    bone_mat = r.material("stag_antler", (0.42, 0.39, 0.33), rough=0.85)
    # The rack: a beam each side sweeping up and back, three tines forward off each.
    hb = r.bone("Head")
    crown_z = r.top(hb.y, half_width=0.3) - 0.04
    segs = []
    for s in (-1, 1):
        base = Vector((s * 0.13, hb.y + 0.02, crown_z))
        k1 = base + Vector((s * 0.22, 0.2, 0.42))
        k2 = k1 + Vector((s * 0.3, 0.25, 0.48))
        k3 = k2 + Vector((s * 0.28, 0.1, 0.42))
        segs += [(base, k1, 0.07, 0.055), (k1, k2, 0.055, 0.042), (k2, k3, 0.042, 0.018)]
        for a, b, L in ((base, k1, 0.42), (k1, k2, 0.5), (k2, k3, 0.38)):
            root = (a + b) / 2
            tip = root + Vector((s * 0.1, -0.45, 0.35)).normalized() * L
            segs.append((root, tip, 0.038, 0.012))
    r.tubes("antlers", segs, "Head", bone_mat)
    r.settle()
    return r


def molted_hound():
    """Bigger than the wolf, patchy dark fur with bare seams along the back and flanks that
    glow faintly; a heavier jaw."""
    r = Rig(fk_feet=False, weld=True)
    r.uniform(1.25)
    head = r.family("Head", "Ear1.L", "Ear1.R")
    # A heavy jaw: the head grows down from its crown; the neck thickens to carry it.
    hb = r.bone("Head")
    r.scale(head, (0, hb.y, r.top(hb.y, half_width=0.3)), (1.18, 1.12, 1.3))
    r.scale(NECK, r.bone("Neck1"), (1.3, 1.0, 1.22))
    # Materials: the belly's light material becomes bare molted skin.
    r.recolor("Main", "hound_fur", (0.06, 0.045, 0.035), rough=0.95)
    r.recolor("Main_Light", "hound_bare", (0.17, 0.11, 0.09), rough=0.75)
    r.recolor("Eyes_Black", "hound_eyes", (0.01, 0.01, 0.01), rough=0.3)
    r.recolor("Nose", "hound_nose", (0.02, 0.02, 0.02), rough=0.5)
    seams = r.material("field_seams", (0.12, 0.05, 0.03), rough=0.5, emission=(1.0, 0.42, 0.18), strength=1.3)
    # Seams: one along the spine, two along each flank, pressed into the hide.
    r.fin("seam_spine", r.bone("Neck1").y, r.bone("Back").y, 0.05, seams, thickness=0.09, steps=16, sink=0.06)
    y0, y1 = r.bone("Torso3").y - 0.1, r.bone("Back").y + 0.3
    top, bot = r.top(r.bone("Torso").y), r.bottom(r.bone("Torso").y)
    for side in (-1, 1):
        r.flank_line("seam_flank_hi_%d" % side, y0, y1, lambda t: bot + (top - bot) * (0.72 + 0.1 * math.sin(t * 7)), seams, height=0.07, side=side)
        r.flank_line("seam_flank_lo_%d" % side, y0 + 0.4, y1 - 0.3, lambda t: bot + (top - bot) * (0.42 + 0.12 * math.sin(t * 5 + 1)), seams, height=0.06, side=side)
    r.settle()
    return r


def post_breaker():
    """Massive and squat: armoured shoulder and skull plates, a short tail, a deep chest;
    about 1.4 times the wolf's bulk."""
    r = Rig(weld=True)
    head = r.family("Head", "Ear1.L", "Ear1.R")
    # Broad and long, then down on shorter, thicker legs.
    r.scale([], (0, 0, 0), (1.3, 1.12, 1.0), spatial=True)
    r.leg_length(0.3)
    r.leg_girth(1.35)
    # A deep chest, hanging from the back line.
    r.scale(TORSO, (0, 0, r.top(r.bone("Torso2").y)), (1.08, 1.0, 1.32))
    # A big skull on a thick neck; the ears small; a stump of a tail.
    r.scale(head, r.bone("Neck3"), 1.2)
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), 0.6)
    r.scale(NECK, r.bone("Neck1"), (1.45, 1.0, 1.35))
    r.scale(r.family("Tail1"), r.bone("Tail1"), 0.35)
    # Materials.
    r.recolor("Main", "breaker_hide", (0.075, 0.062, 0.052), rough=0.9)
    r.recolor("Main_Light", "breaker_hide_light", (0.13, 0.11, 0.09), rough=0.85)
    r.recolor("Eyes_Black", "breaker_eyes", (0.01, 0.01, 0.01), rough=0.3)
    r.recolor("Nose", "breaker_nose", (0.02, 0.02, 0.02), rough=0.5)
    iron = r.material("iron_hide", (0.11, 0.11, 0.13), rough=0.62, metallic=0.6)
    # Plates: one hung over each shoulder on the chest's bone, a skull plate over the brow,
    # and a low ridge of three down the spine.
    sy = r.bone("FrontShoulder.L").y
    top = r.top(sy)
    sz = top - 0.42
    sx = r.side(sy, sz)
    for s in (-1, 1):
        r.shell("plate_shoulder_%d" % s, (s * (sx - 0.1), sy, sz), (0.3, 0.62, 0.5), "Torso2", iron, rot=(0, s * math.radians(-70), 0))
    hb = r.bone("Head")
    r.shell("plate_skull", (0, hb.y - 0.05, r.top(hb.y, half_width=0.3) - 0.07), (0.44, 0.6, 0.2), "Head", iron, rot=(math.radians(-18), 0, 0))
    for b in ("Torso", "Torso2", "Torso3"):
        y = r.bone(b).y
        r.shell("plate_%s" % b.lower(), (0, y, r.top(y) - 0.07), (0.34, 0.3, 0.14), b, iron)
    r.settle()
    return r


def current_eel():
    """The wolf rig stretched long and thin, legs shrunk to stubs, a ribbon fin along the whole
    back and tail, dark green-black, a glowing lateral line."""
    r = Rig(weld=True)
    head = r.family("Head", "Ear1.L", "Ear1.R")
    # Long and thin.
    r.scale([], (0, 0, 0), (0.55, 1.75, 0.62), spatial=True)
    # Legs to stubs, the body on the ground.
    r.leg_length(0.82 * r.bone("FrontShoulder.L").z)
    r.leg_girth(0.7)
    # A tapered head, no ears to speak of; the tail drawn out and tapered.
    r.scale(head, r.bone("Neck3"), (0.85, 1.35, 0.8))
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), 0.15)
    r.lengthen_chain(r.family("Tail1"), [], 1.45)
    r.scale(r.family("Tail5"), r.bone("Tail5"), (0.55, 1.0, 0.55))
    # The wolf swings its tail low when it walks; a long tail on a body this low would go
    # through the ground, so the eel's tail only follows a third of the way.
    r.damp_rotations(r.family("Tail1"), 0.25)
    # Materials.
    hide = r.recolor("Main", "eel_hide", (0.03, 0.065, 0.05), rough=0.3)
    r.recolor("Main_Light", "eel_hide_light", (0.05, 0.11, 0.075), rough=0.35)
    r.recolor("Eyes_Black", "eel_eyes", (0.01, 0.01, 0.01), rough=0.2)
    r.recolor("Nose", "eel_nose", (0.015, 0.02, 0.02), rough=0.4)
    line = r.material("field_line", (0.05, 0.12, 0.09), rough=0.4, emission=(0.35, 1.0, 0.7), strength=2.2)
    # The lateral line, from the jaw hinge to the tail, measured on the bare body before the
    # fins change what "top" means.
    la, lb = r.bone("Neck3").y, r.bone("Tail7").y
    raw = [(r.top(la + (lb - la) * i / 30.0, window=0.45) + r.bottom(la + (lb - la) * i / 30.0, window=0.45)) * 0.52 for i in range(31)]
    # Smoothed: the stretched mesh's rings are far apart, and a line that hops between them reads as a zigzag.
    mids = [sum(raw[max(0, i - 2):i + 3]) / len(raw[max(0, i - 2):i + 3]) for i in range(31)]
    for side in (-1, 1):
        r.flank_line("lateral_line_%d" % side, la, lb, lambda t: mids[int(round(t * 30))], line, height=0.05, depth=0.06, steps=30, side=side)
    # The ribbon fin along the whole back and tail, a shorter one under the tail.
    y0, y1 = r.bone("Neck1").y, r.bone("Tail8").y + 0.2
    r.fin("fin_back", y0, y1, lambda t: 0.08 + 0.42 * math.sin(math.pi * (0.08 + 0.92 * t)) ** 0.7, hide, thickness=0.05, steps=36, sink=0.06)
    r.fin("fin_under", r.bone("Tail1").y, y1, lambda t: 0.04 + 0.16 * math.sin(math.pi * t) ** 0.7, hide, thickness=0.05, steps=20, sink=0.05, under=True)
    r.settle()
    return r


BEASTS = {"cut-wolf": cut_wolf, "river-thing": river_thing, "ruin-stag": ruin_stag, "molted-hound": molted_hound,
          "post-breaker": post_breaker, "current-eel": current_eel}


def build(beast_id):
    r = BEASTS[beast_id]()
    return r.export(os.path.join(OUT, beast_id + ".glb"))


# ======================================================================================
# The contact sheet: one moonlit card per beast at a three-quarter angle, tiled three by two.
# ======================================================================================

def _skinned(objects):
    return [o for o in objects if o.type == "MESH" and not o.hide_render and any(m.type == "ARMATURE" for m in o.modifiers)]


def render_card(bid, path, walk=False, samples=48, res=(640, 480)):
    """One beast from the exported file, three-quarter from the front right, in moonlight with
    a faint lamp from the other side; in the rest pose, or a frame of the Walk."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, bid + ".glb"))
    arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    if arm and arm.animation_data:
        arm.animation_data.action = None
        for t in arm.animation_data.nla_tracks:
            t.mute = not (walk and t.name.endswith("|Walk"))
        # Pose bones keep whatever the importer last evaluated; back to the rest pose.
        for pb in arm.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)
    scene.frame_set(12 if walk else 1)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((9e9, 9e9, 9e9))
    hi = Vector((-9e9, -9e9, -9e9))
    for o in _skinned(bpy.data.objects):
        oe = o.evaluated_get(dg)
        for v in oe.to_mesh().vertices:
            w = oe.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        oe.to_mesh_clear()
    log(bid, "walk" if walk else "rest", "bounds", tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
    # The ground, wet slate, and the name on it in front of the beast.
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(Rig.material("ground", (0.03, 0.032, 0.04), rough=0.55))
    try:
        fc = bpy.data.curves.new(bid, type="FONT")
        fc.body = bid
        fc.size = 0.55
        fc.align_x = "CENTER"
        fo = bpy.data.objects.new("label", fc)
        fo.location = Vector(((lo.x + hi.x) / 2, lo.y - 0.9, 0.01))
        bpy.context.collection.objects.link(fo)
        fo.data.materials.append(Rig.material("label", (0.85, 0.75, 0.55), rough=1.0, emission=(0.9, 0.8, 0.6), strength=0.6))
    except Exception as e:  # noqa: BLE001 - a missing font only loses the label
        log("no label:", e)
    centre = (lo + hi) / 2
    size = max((hi - lo).length, 1.0)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    # Three-quarter from the front right, a little above; pulled back until the beast and its
    # name sit inside the frame with a margin.
    from bpy_extras.object_utils import world_to_camera_view
    direction = Vector((0.75, -1.0, 0.5)).normalized()
    aim = centre + Vector((0, 0, -size * 0.06))
    corners = [Vector((x, y, z)) for x in (lo.x - 0.2, hi.x + 0.2) for y in (lo.y - 1.4, hi.y + 0.2) for z in (0, hi.z + 0.2)]
    dist = size * 0.6
    for _ in range(80):
        cam.location = aim + direction * dist
        cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        ndc = [world_to_camera_view(scene, cam, c) for c in corners]
        if all(0.05 < p.x < 0.95 and 0.05 < p.y < 0.95 for p in ndc):
            break
        dist *= 1.04

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

    # Moonlight: a cool blue key from high behind-right, a faint warm lamp from the front-left,
    # a soft blue fill so the shadow side keeps its shape.
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


def render_sheet(path, ids=None, walk=False, samples=48, cols=3, res=(640, 480)):
    """The six cards tiled into one image."""
    import numpy as np
    ids = ids or list(BEASTS)
    cards = [render_card(bid, os.path.join(SCRATCH, "beast_cards", bid + ("_walk" if walk else "") + ".png"), walk=walk, samples=samples, res=res) for bid in ids]
    w, h = res
    rows = (len(cards) + cols - 1) // cols
    sheet = np.zeros((rows * h, cols * w, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    for i, card in enumerate(cards):
        img = bpy.data.images.load(card)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
        r, c = i // cols, i % cols
        # Image rows run bottom-up in Blender; the first card goes top-left.
        y0 = (rows - 1 - r) * h
        sheet[y0:y0 + h, c * w:c * w + w] = px[:h, :w]
        bpy.data.images.remove(img)
    out = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    out.pixels = sheet.ravel().tolist()
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    log("wrote", path)


if __name__ == "__main__":
    args = sys.argv[1:]
    want_sheet = not args or "sheet" in args
    wanted = [a for a in args if a != "sheet"] or (list(BEASTS) if not args else [])
    results = {}
    for bid in wanted:
        results[bid] = build(bid)
    for bid, info in results.items():
        log(bid, "animations:", len(info["animations"]), "joints:", info["joints"], "materials:", info["materials"])
    if want_sheet:
        render_sheet(os.path.join(SCRATCH, "beasts_sheet.png"))
        render_sheet(os.path.join(SCRATCH, "beasts_sheet_walk.png"), walk=True, samples=24)
