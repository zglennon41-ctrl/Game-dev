"""WILDLINE human kit: the body kit's bodies made from the human (human.py) instead of grown.
One continuous body with its head, on the game rig moved to the human's real joints, with
MakeHuman's weights; eyes, brows and lashes hung from the head; the hair cut from the scalp;
the garments measured from the body and laid on its true surface (docs/bodies-plan.md,
"The human base").
"""
import json
import math
import os

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

import people_kit as pk
import human as hu
import head as hd

# The three builds the player's slider blends: (muscle, weight) on MakeHuman's scales.
BUILD_FORMS = {"lean": (0.32, 0.36), "fit": (0.62, 0.5), "heavy": (0.98, 0.68)}
ARM_BONES = ("upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb")
LEG_BONES = ("thigh", "calf", "foot", "ball")


def home_form(home, sex):
    """The ancestry mix and the details of a home's people (data/bodies.json, form)."""
    try:
        form = json.load(open(os.path.join(pk.ROOT, "data", "bodies.json")))["homes"][home].get("form", {})
    except (KeyError, OSError):
        form = {}
    ancestry = form.get("ancestry", {"african": 0.34, "asian": 0.33, "caucasian": 0.33})
    details = dict(form.get("details", {}))
    details.update(form.get(sex, {}))
    return ancestry, details


def retarget(r, J):
    """Move the game rig's bones onto the human's joints, each keeping its direction (so the
    baked rotations mean what they meant), the helpers with their limbs; the baked translations
    scale with the legs and arms they belong to."""
    old = {b: r.bone(b).copy() for b in J if b in r.arm.data.bones}
    follow = {}
    for s in ("l", "r"):
        follow.update({"kneeIK." + s: "lowerleg." + s, "elbowIK." + s: "lowerarm." + s, "handIK." + s: "wrist." + s})
        for b in ("control-toe-roll", "control-heel-roll", "control-foot-roll", "heelIK", "IK-foot", "IK-toe"):
            follow["%s.%s" % (b, s)] = "foot." + s

    def move(ebs):
        delta = {}
        for eb in ebs:
            if eb.name in J:
                delta[eb.name] = (r.MAinv @ J[eb.name]) - eb.head
        for eb in ebs:
            d = delta.get(eb.name) or delta.get(follow.get(eb.name, ""))
            if d is not None:
                eb.head = eb.head + d
                eb.tail = eb.tail + d
    r._edit(move)
    bpy.context.view_layer.update()
    hip = J["upperleg.l"].z / old["upperleg.l"].z
    thigh = (J["upperleg.l"] - J["lowerleg.l"]).length / (old["upperleg.l"] - old["lowerleg.l"]).length
    shin = (J["lowerleg.l"] - J["foot.l"]).length / (old["lowerleg.l"] - old["foot.l"]).length
    arm = (J["wrist.l"] - J["upperarm.l"]).length / (old["wrist.l"] - old["upperarm.l"]).length
    factors = {"hips": hip, "root": hip}
    for s in ("l", "r"):
        factors["upperleg." + s] = thigh
        factors["lowerleg." + s] = shin
        for b in ("kneeIK", "control-toe-roll"):
            factors["%s.%s" % (b, s)] = hip
        for b in ("upperarm", "lowerarm", "elbowIK", "wrist", "hand", "handslot", "handIK"):
            factors["%s.%s" % (b, s)] = arm
    r.scale_location_keys(factors)
    r.measured["retarget"] = {"hip": round(hip, 3), "thigh": round(thigh, 3), "shin": round(shin, 3), "arm": round(arm, 3)}


def lower_arms(r):
    """The KayKit clips hold the arms well out from the sides: they were posed for a round toy
    body. On a human the standing and moving clips read stiff, so in the clips named in
    data/rules.json (motion.armsDown) the upper arms are brought down toward the sides by a
    fixed turn about the chest's forward axis, composed into every key."""
    try:
        spec = json.load(open(os.path.join(pk.ROOT, "data", "rules.json")))["motion"]["armsDown"]
    except (KeyError, OSError):
        return
    clips = set(spec.get("clips", []))
    angle = math.radians(float(spec.get("degrees", 0.0)))
    if not clips or abs(angle) < 1e-6:
        return
    from mathutils import Quaternion
    delta = {}
    for s, sg in (("l", 1.0), ("r", -1.0)):
        R = r.arm.data.bones["upperarm." + s].matrix_local.to_3x3()
        delta["upperarm." + s] = (R.inverted() @ Matrix.Rotation(sg * angle, 3, "Y") @ R).to_quaternion()
    done = 0
    for a in bpy.data.actions:
        if a.name not in clips:
            continue
        for layer in a.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for bone, dq in delta.items():
                        path = 'pose.bones["%s"].rotation_quaternion' % bone
                        fcs = sorted([fc for fc in cb.fcurves if fc.data_path == path], key=lambda fc: fc.array_index)
                        if len(fcs) != 4 or len({len(fc.keyframe_points) for fc in fcs}) != 1:
                            continue
                        for i in range(len(fcs[0].keyframe_points)):
                            q = dq @ Quaternion([fc.keyframe_points[i].co[1] for fc in fcs])
                            for c, fc in enumerate(fcs):
                                kp = fc.keyframe_points[i]
                                d = q[c] - kp.co[1]
                                kp.co[1] += d
                                kp.handle_left[1] += d
                                kp.handle_right[1] += d
                        for fc in fcs:
                            fc.update()
                        done += 1
    r.measured["arms_down"] = done


class HumanBody:
    """What the body kit's Body keeps when it is built from the human."""

    def __init__(self, body):
        self.body = body
        ancestry, details = home_form(body.home, body.sex)
        H = 2.4 * body.k
        fit = hu.Human(body.sex, ancestry, details, BUILD_FORMS["fit"], height=H)
        self.humans = {"fit": fit}
        for b in ("lean", "heavy"):
            self.humans[b] = hu.Human(body.sex, ancestry, details, BUILD_FORMS[b], height=H, like=fit)
        self.base = fit.base
        self.J = fit.rig_joints()
        retarget(body.r, self.J)
        lower_arms(body.r)
        self.dom = fit.dominant()
        stems = np.array([(d or "").rpartition("_")[0] if (d or "")[-2:] in ("_l", "_r") else (d or "") for d in self.dom], dtype=object)
        sides = np.array([(d or "")[-1] if (d or "")[-2:] in ("_l", "_r") else "" for d in self.dom], dtype=object)
        self.is_arm = np.isin(stems, ARM_BONES + ("index_01", "index_02", "index_03", "middle_01", "middle_02", "middle_03", "ring_01", "ring_02", "ring_03", "pinky_01", "pinky_02", "pinky_03", "thumb_01", "thumb_02", "thumb_03"))
        self.is_leg = np.isin(stems, LEG_BONES)
        self.is_head = np.array([d == "head" for d in self.dom])
        self.is_neck = np.array([d == "neck_01" for d in self.dom])
        self.side = sides
        self.faces = self.base.body_faces
        self.face_idx = np.array(self.faces)            # all quads
        self._bvh = {}
        self._tables = {}
        self._weights = None
        self._landmarks()

    # --- landmarks ----------------------------------------------------------------------

    def _landmarks(self):
        fit = self.humans["fit"]
        v = fit.body()
        k = self.body.k
        self.eye = {s: Vector(fit.joint("joint-%s-eye" % s)) for s in ("l", "r")}
        helper = fit.group("helper-l-eye")
        self.eye_r = float(np.linalg.norm(helper - helper.mean(axis=0), axis=1).mean())
        mouth = fit.joint("joint-mouth")
        front = v[(np.abs(v[:, 0]) < 0.03 * k) & (v[:, 1] < mouth[1] + 0.02 * k) & (v[:, 2] > fit.joint("joint-neck")[2] + 0.02 * k)]
        self.chin_z = float(front[:, 2].min())
        self.crown_z = float(v[:, 2].max())
        self.head_h = self.crown_z - self.chin_z
        ears = np.zeros(len(v), dtype=bool)
        ears[np.unique(self.face_idx[self.base.regions["ears"]])] = True
        head = v[(v[:, 2] > self.chin_z) & ~ears & ~self.is_arm]
        bvh = self.bvh("trunk", "fit")
        brow = bvh.ray_cast(Vector((0, -2, self.eye["l"].z + 1.9 * self.eye_r)), Vector((0, 1, 0)))[0]
        y0 = brow.y if brow is not None else float(head[:, 1].min())
        self.head_box = ((float(head[:, 0].min()), float(head[:, 0].max())), (y0, float(head[:, 1].max())), (self.chin_z, self.crown_z))
        # the trunk's levels, the same on every build: under the crotch, the hips, up to the neck
        zh, zs = self.J["upperleg.l"].z, self.J["upperarm.l"].z
        znb = float(fit.joint("joint-neck")[2])
        mid = v[(np.abs(v[:, 0]) < 0.015 * k) & (v[:, 2] < zh) & (v[:, 2] > 0.5 * zh)]
        self.crotch_z = float(mid[:, 2].min()) if len(mid) else zh - 0.12 * k
        f = [-0.06, 0.11, 0.28, 0.49, 0.69, 0.86]
        self.trunk_z = [self.crotch_z - 0.03 * k] + [zh + (zs - zh) * t for t in f] + [zs + 0.03 * k, zs + 0.55 * (znb - zs), znb + 0.02 * k, znb + 0.09 * k]
        xs, xe, xw = self.J["upperarm.l"].x, self.J["lowerarm.l"].x, self.J["wrist.l"].x

        def ax(x):   # the old arm levels to the human's arm
            if x <= 0.518:
                return xs + (x - 0.151) * (xe - xs) / (0.518 - 0.151)
            return xe + (x - 0.518) * (xw - xe) / (0.913 - 0.518)
        self.arm_x = [ax(x) for x in (0.135, 0.21, 0.36, 0.518, 0.64, 0.82, 0.925)]
        zk, za = self.J["lowerleg.l"].z, self.J["foot.l"].z

        def lz(z):
            if z >= 0.57:
                return zk + (z - 0.57) * (zh - zk) / (1.113 - 0.57)
            return za + (z - 0.12) * (zk - za) / (0.57 - 0.12)
        self.leg_z = [lz(z) for z in (1.09, 0.95, 0.75, 0.57, 0.42, 0.25, 0.14)]
        self.map_z = lz      # a height written for the old legs (a hem), on these
        self.arm_c = (self.J["upperarm.l"].y, self.J["upperarm.l"].z)

    # --- surfaces -----------------------------------------------------------------------

    def bvh(self, kind, build):
        """The body's surface for ray casts: the trunk (everything but the arms), the arms, or
        one leg."""
        key = (kind, build)
        if key not in self._bvh:
            v = self.humans[build].body()
            fa = self.face_idx
            arm = self.is_arm[fa].all(axis=1)
            if kind == "trunk":
                keep = ~arm
            elif kind == "arms":
                keep = self.is_arm[fa].any(axis=1)
            elif kind == "all":
                keep = np.ones(len(fa), dtype=bool)
            else:
                s = kind[-1]
                keep = (self.is_leg[fa] & (self.side[fa] == s)).all(axis=1)
            self._bvh[key] = BVHTree.FromPolygons([tuple(p) for p in v], [tuple(f) for f in fa[keep]])
        return self._bvh[key]

    def front_y(self, x, z, back=False):
        """The trunk's front (or back) surface at (x, z)."""
        d = -1.0 if back else 1.0
        hit = self.bvh("trunk", "fit").ray_cast(Vector((x, -2.0 * d, z)), Vector((0, d, 0)))[0]
        return hit.y if hit is not None else 0.0

    # --- the ring tables the garments are cut on, measured from the body -----------------

    def rings(self, kind, build):
        key = (kind, build)
        if key in self._tables:
            return self._tables[key]
        v = self.humans[build].body()
        k = self.body.k
        band = 0.014 * k
        out = []
        if kind == "trunk":
            trunk = ~self.is_arm
            for i, z in enumerate(self.trunk_z):
                sel = v[trunk & (np.abs(v[:, 2] - z) < band)]
                if i >= 9:      # the neck: not the jaw above it
                    sel = sel[np.abs(sel[:, 0]) < 0.11 * k]
                if len(sel) < 4:
                    out.append(out[-1][:0] + (z,) + out[-1][1:] if out else (z, 0.15 * k, 0.1 * k, 0.0))
                    continue
                hw = float(np.abs(sel[:, 0]).max())
                y0, y1 = float(sel[:, 1].min()), float(sel[:, 1].max())
                out.append((z, hw, (y1 - y0) / 2, (y0 + y1) / 2))
        elif kind == "arm":
            yc, zc = self.arm_c
            arm = self.is_arm & (self.side == "l")
            for x in self.arm_x:
                sel = v[arm & (np.abs(v[:, 0] - x) < band)]
                if len(sel) < 4:
                    out.append(None)
                    continue
                out.append((x, float(np.abs(sel[:, 1] - yc).max()), float(np.abs(sel[:, 2] - zc).max())))
            nxt = next(r for r in out if r is not None)
            out = [r if r is not None else (self.arm_x[i], nxt[1] * 1.05, nxt[2] * 1.05) for i, r in enumerate(out)]
        else:
            x_leg = self.J["upperleg.l"].x
            leg = (self.is_leg & (self.side == "l")) | ((v[:, 0] > 0.01 * k) & ~self.is_arm & (v[:, 2] < self.J["upperleg.l"].z + 0.05 * k))
            for z in self.leg_z:
                sel = v[leg & (np.abs(v[:, 2] - z) < band)]
                if len(sel) < 4:
                    out.append((z, 0.08 * k, 0.09 * k))
                    continue
                out.append((z, float(np.abs(sel[:, 0] - x_leg).max()), float(np.abs(sel[:, 1]).max())))
        self._tables[key] = out
        return out

    @staticmethod
    def _row(table, t):
        """A table's row at level t (its first column), interpolated; the ends hold."""
        rows = sorted(table, key=lambda r: r[0])
        if t <= rows[0][0]:
            return rows[0]
        if t >= rows[-1][0]:
            return rows[-1]
        for a, b in zip(rows, rows[1:]):
            if a[0] <= t <= b[0]:
                u = (t - a[0]) / max(1e-9, b[0] - a[0])
                return tuple(x + (y - x) * u for x, y in zip(a, b))
        return rows[-1]

    def normals(self, build):
        """The body's vertex normals for one build."""
        if not hasattr(self, "_normals"):
            self._normals = {}
        if build not in self._normals:
            v = self.humans[build].body()
            fa = self.face_idx
            fn = np.cross(v[fa[:, 2]] - v[fa[:, 0]], v[fa[:, 3]] - v[fa[:, 1]])
            n = np.zeros_like(v)
            for c in range(4):
                np.add.at(n, fa[:, c], fn)
            self._normals[build] = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        return self._normals[build]

    def shell(self, name, mask, build, thickness):
        """A garment cut from the body itself: the faces whose vertices `mask` (a function of
        the fit body's vertex positions) keeps, pushed out along the normals. It fits exactly
        and keeps its topology across the builds."""
        fitv = self.humans["fit"].body()
        v = self.humans[build].body()
        fa = self.face_idx
        vm = mask(fitv) & ~self.is_head
        keep = vm[fa].all(axis=1)
        used = np.unique(fa[keep])
        remap = -np.ones(len(v), dtype=np.int64)
        remap[used] = np.arange(len(used))
        pts = v[used] + self.normals(build)[used] * thickness
        return hu.mesh_object(name, pts, remap[fa[keep]])

    def neck_mask(self, z_lo, z_hi, reach):
        """Vertices round the base of the neck: between two heights and within `reach` of
        the neck's axis (a standing collar is narrow, a broad collar lies out on the shoulders)."""
        cx, cy = 0.0, float(self.humans["fit"].joint("joint-neck")[1])
        arm = self.is_arm

        def mask(v):
            r = np.hypot(v[:, 0] - cx, v[:, 1] - cy)
            return (v[:, 2] > z_lo) & (v[:, 2] < z_hi) & (r < reach) & ~arm
        return mask

    @staticmethod
    def refine(ob):
        """Halve a garment's faces each way, so it can follow the body between its rings."""
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        # a loft's end caps would be drawn onto the body as a ragged membrane: open the ends
        caps = [f for f in bm.faces if len(f.verts) > 4]
        if caps:
            bmesh.ops.delete(bm, geom=caps, context="FACES_ONLY")
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
        bm.to_mesh(ob.data)
        bm.free()
        for poly in ob.data.polygons:
            poly.use_smooth = True

    def conform(self, ob, chain, build, least=0.009):
        """Lay a garment on the body's true surface: each vertex keeps the distance its loft
        gave it from the measured ring, but from the nearest point of the body, so cloth
        follows the chest, the shoulders and the calves instead of an ellipse round them.
        Cloth that stands well off the body (a skirt's flare, a wide sleeve) is left to hang."""
        kind = "trunk" if chain == "trunk" else ("arm" if chain.startswith("arm") else "leg")
        table = self.rings(kind, build)
        bvh = self.bvh("all", build)
        M, Mi = ob.matrix_world, ob.matrix_world.inverted()
        x_leg = self.J["upperleg.l"].x
        yc, zc = self.arm_c
        for vert in ob.data.vertices:
            p = M @ vert.co
            if kind == "trunk":
                z, a, b, yo = self._row(table, p.z)
                ca, sa = p.x, p.y - yo
            elif kind == "arm":
                x, a, b = self._row(table, abs(p.x))
                ca, sa = p.y - yc, p.z - zc
            else:
                z, a, b = self._row(table, p.z)[:3]
                ca, sa = p.x - (x_leg if chain[-1] == "l" else -x_leg), p.y
            r = math.hypot(ca, sa)
            if r < 1e-5:
                continue
            off = r - 1.0 / math.sqrt((ca / r / a) ** 2 + (sa / r / b) ** 2)      # what the loft stood off its ring
            w = 1.0 - min(1.0, max(0.0, (off - 0.045) / 0.05))
            if w <= 0.0:
                continue
            loc, nrm, _, _ = bvh.find_nearest(p)
            if loc is None:
                continue
            out = p - loc
            n = out.normalized() if (out.length > 1e-5 and out.dot(nrm) > 0.0) else nrm
            target = loc + n * max(off, least)
            vert.co = Mi @ p.lerp(target, w)
        ob.data.update()

    # --- the meshes ---------------------------------------------------------------------

    def body_object(self, build, mats, slot, bare_feet):
        """The body of one build, painted: skin, the lips, and the underclothes (an undershirt
        on the trunk, trousers from the waist to the ankle, the foot as a boot unless bare)."""
        v = self.humans[build].body()
        fitv = self.humans["fit"].body()
        k = self.body.k
        fa = self.face_idx
        cz = fitv[fa][:, :, 2].mean(axis=1)
        zh, zs = self.J["upperleg.l"].z, self.J["upperarm.l"].z
        waist = zh + 0.14 * (zs - zh)
        neck = self.trunk_z[9] - 0.03 * k
        ankle = self.J["foot.l"].z + 0.035 * k
        arm_f = self.is_arm[fa].any(axis=1)
        head_f = (self.is_head | self.is_neck)[fa].all(axis=1)
        fm = np.full(len(fa), slot["skin"])
        fm[(cz < waist) & ~arm_f] = slot["trousers"]
        fm[(cz >= waist) & (cz < neck) & ~arm_f & ~head_f] = slot["tunic"]
        if not bare_feet:
            fm[cz < ankle] = slot["boots"]
        else:
            fm[cz < ankle] = slot["skin"]
        fm[self.base.regions["lips"]] = slot["lips"]
        return hu.mesh_object("Body", v, self.faces, mats, fm)

    def weights(self):
        if self._weights is None:
            W = self.humans["fit"].rig_weights()
            names = sorted(W)
            A = np.stack([W[n] for n in names], axis=1)
            # the four strongest bones a vertex, as the engine keeps
            order = np.argsort(-A, axis=1)[:, :4]
            top = np.take_along_axis(A, order, axis=1)
            top = top / np.maximum(top.sum(axis=1, keepdims=True), 1e-9)
            self._weights = (names, order, top)
        return self._weights

    def weight_body(self, ob):
        names, order, top = self.weights()
        groups = {n: ob.vertex_groups.new(name=n) for n in names}
        for i in range(order.shape[0]):
            for j in range(4):
                w = float(top[i, j])
                if w > 1e-3:
                    groups[names[order[i, j]]].add([i], w, "REPLACE")

    def weight_like_body(self, ob):
        """A garment's vertices take the weights of the body under them (the three nearest
        body vertices, by distance)."""
        names, order, top = self.weights()
        if not hasattr(self, "_kd"):
            v = self.humans["fit"].body()
            self._kd = KDTree(len(v))
            for i, p in enumerate(v):
                self._kd.insert(Vector(p), i)
            self._kd.balance()
        groups = {}
        M = ob.matrix_world
        for vert in ob.data.vertices:
            acc = {}
            for _, i, d in self._kd.find_n(M @ vert.co, 3):
                wd = 1.0 / (d + 1e-3)
                for j in range(4):
                    w = float(top[i, j])
                    if w > 1e-3:
                        acc[names[order[i, j]]] = acc.get(names[order[i, j]], 0.0) + w * wd
            best = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
            total = sum(w for _, w in best) or 1.0
            for n, w in best:
                if n not in groups:
                    groups[n] = ob.vertex_groups.new(name=n)
                groups[n].add([vert.index], w / total, "REPLACE")

    # --- what hangs from the head ---------------------------------------------------------

    def head_pieces(self, mats):
        """The eyeballs (white, iris, pupil), the brows laid on the brow's bone, the lashes."""
        out = []
        R = self.eye_r
        fem = self.body.sex == "f"
        bvh = self.bvh("all", "fit")
        for s, sg in (("l", 1.0), ("r", -1.0)):
            c = self.eye[s]
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=R)
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
            for f in bm.faces:
                ang = math.acos(max(-1.0, min(1.0, -f.calc_center_median().normalized().y)))
                f.material_index = 2 if ang < 0.2 else (1 if ang < 0.52 else 0)
                f.smooth = True
            bmesh.ops.translate(bm, vec=c, verts=bm.verts)
            me = bpy.data.meshes.new("Eye_" + s)
            bm.to_mesh(me)
            bm.free()
            for m in (mats["eye_white"], mats["iris"], mats["pupil"]):
                me.materials.append(m)
            ob = bpy.data.objects.new("Eye_" + s, me)
            bpy.context.collection.objects.link(ob)
            out.append(ob)
            # the brow: a ribbon on the skin, thick at the root, arched past the middle, thin at the tail
            n = 12
            thick = (0.26 if fem else 0.34) * R
            rows = [[], [], []]
            for i in range(n):
                t = i / (n - 1.0)
                x = c.x + sg * (-1.25 + 3.3 * t) * R
                z = c.z + ((1.5 if fem else 1.38) + (0.5 if fem else 0.36) * math.sin(min(1.0, t / 0.68) * math.pi / 2) - 0.45 * max(0.0, t - 0.68) / 0.32) * R
                half = thick * (0.7 + 0.3 * math.sin(min(1.0, t / 0.2) * math.pi / 2)) * (1.0 - 0.75 * max(0.0, t - 0.5) / 0.5)
                for j, dz in enumerate((half, 0.0, -half)):
                    hit, nrm, _, _ = bvh.ray_cast(Vector((x, -2.0, z + dz)), Vector((0, 1, 0)))
                    if hit is None:
                        hit, nrm = Vector((x, c.y - R, z + dz)), Vector((0, -1, 0))
                    rows[j].append(hit + nrm * (0.0016 if j == 1 else 0.0006))
            bm = bmesh.new()
            vs = [[bm.verts.new(p) for p in row] for row in rows]
            for j in range(2):
                for i in range(n - 1):
                    f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
                    f.smooth = True
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            if sum(f.normal.y for f in bm.faces) > 0:
                bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
            out.append(pk._bm_object("Brow_" + s, bm, mats["hair"]))
            # the lashes: MakeHuman's own strips along the lids, both faces shown
            fit = self.humans["fit"]
            faces = [f for f, g in zip(self.base.faces, self.base.face_groups) if g and g.startswith("helper-%s-eyelashes" % s)]
            used = sorted({i for f in faces for i in f})
            remap = {i: j for j, i in enumerate(used)}
            quads = [tuple(remap[i] for i in f) for f in faces]
            back = [tuple(i + len(used) for i in q[::-1]) for q in quads]
            lash = hu.mesh_object("Lash_" + s, np.concatenate([fit.v[used], fit.v[used]]), quads + back, [mats["lash"]])
            out.append(lash)
        return out

    def head_surface(self):
        """The head and neck as their own mesh (no ears, no inside of the mouth), for the hair
        and the beards to be cut from; removed after."""
        fit = self.humans["fit"]
        v = fit.body()
        fa = self.face_idx
        skip = np.zeros(len(fa), dtype=bool)
        for region in ("ears", "inside_mouth"):
            skip[self.base.regions[region]] = True
        keep = (v[fa][:, :, 2].min(axis=1) > self.chin_z - 0.25 * self.head_h) & ~self.is_arm[fa].any(axis=1) & ~skip
        used = np.unique(fa[keep])
        remap = -np.ones(len(v), dtype=np.int64)
        remap[used] = np.arange(len(used))
        return hu.mesh_object("HeadSurface", v[used], remap[fa[keep]])

    def hair(self, mat):
        surf = self.head_surface()
        (x0, x1), (y0, y1), (z0, z1) = self.head_box
        centre = Vector((0.0, (y0 + y1) / 2 + 0.01, z0 + 0.5 * self.head_h))
        ratio = self.head_h / hd.HEAD_HEIGHT
        pieces = hd.hair(surf, centre, self.body.sex, lambda key: ratio if key == "headLength" else 1.0, mat)
        bpy.data.objects.remove(surf)
        return pieces, centre

    def sockets(self):
        (x0, x1), (y0, y1), (z0, z1) = self.head_box
        J = self.J
        k = self.body.k
        chest_z = J["chest"].z + 0.14 * k
        hips_z = J["hips"].z
        neck_z = self.trunk_z[9] + 0.03 * k
        spec = [
            ("socket_head", "head", Vector((0, (y0 + y1) / 2, z1))),
            ("socket_eyes", "head", Vector((0, y0, self.eye["l"].z))),
            ("socket_throat", "head", Vector((0, self.front_y(0.0, neck_z), neck_z))),
            ("socket_back", "chest", Vector((0, self.front_y(0.0, chest_z, back=True), chest_z))),
            ("socket_light", "chest", Vector((0, self.front_y(0.0, chest_z), chest_z))),
            ("socket_tail", "hips", Vector((0, self.front_y(0.0, hips_z - 0.04 * k, back=True), hips_z - 0.04 * k))),
            ("socket_hand_l", "hand.l", Vector(J["wrist.l"]) + Vector((0.03, 0, 0))),
            ("socket_hand_r", "hand.r", Vector(J["wrist.r"]) + Vector((-0.03, 0, 0))),
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

    def shoes(self, build, mat):
        """A shoe over each foot: a loft from the heel to the toes on the foot's own outline."""
        import body_kit as bk
        v = self.humans[build].body()
        k = self.body.k
        out = {}
        ankle = self.J["foot.l"].z
        for s, sg in (("l", 1.0), ("r", -1.0)):
            foot = v[(v[:, 0] * sg > 0) & (v[:, 2] < ankle + 0.01 * k) & self.is_leg]
            y0, y1 = float(foot[:, 1].min()), float(foot[:, 1].max())
            rings = []
            n = 8
            for i in range(n + 1):
                t = i / float(n)
                y = y1 + (y0 - y1) * t            # from the heel (+Y) to the toes (-Y)
                sel = foot[np.abs(foot[:, 1] - y) < 0.02 * k]
                if len(sel) < 3:
                    continue
                xa, xb = float(sel[:, 0].min()), float(sel[:, 0].max())
                top = min(float(sel[:, 2].max()), ankle * (0.85 if t < 0.55 else 0.85 - 0.35 * (t - 0.55) / 0.45))
                end = min(1.0, 0.45 + 2.2 * min(t, 1.0 - t))     # the heel and the toe cap round off
                hw = ((xb - xa) / 2 + 0.008 * k) * end
                hz = (top / 2 + 0.006 * k) * (0.6 + 0.4 * end)
                rings.append((Vector(((xa + xb) / 2, y, hz - 0.002)), Vector((hw, 0, 0)), Vector((0, 0, hz))))
            ob = bk.loft("Dress_0_shoe_" + s, rings)
            ob.data.materials.append(mat)
            out["Dress_0_shoe_" + s] = ob
        return out
