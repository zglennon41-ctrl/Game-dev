"""WILDLINE human: the people's bodies from MakeHuman's base mesh and its library of shape
targets (CC0; tools/blender/makehuman, credited in game/assets/CREDITS.md). The owner asked
for realistic and distinct forms; a carved sphere and a grown tube could not give them, a
sculpted human and its measured variations can.

What this module does, with numpy only (no Blender data until `mesh_object`):

  1. Loads the base mesh (19,158 vertices: the body, and helpers that ride with it: the
     joints as little cubes, the eyeballs, the lashes, a scalp).
  2. Adds targets: the macros (sex, age, muscle, weight, an ancestry mix, proportions, the
     bust) and any details by name (`nose-hump: 0.4`, `eye-epicanthus: -0.5`, `head-oval: 1`).
  3. Poses it from MakeHuman's relaxed stance into the game rig's T-pose with MakeHuman's own
     game rig and weights (forward kinematics and linear blend skinning), so the shoulders and
     hips deform as their authors meant.
  4. Scales it to the game's height and reports where the joints are, so the body kit can
     move the game rig's bones onto a real skeleton's joints.
  5. Maps MakeHuman's weights onto the game rig's bones.

World space out is Blender's: Z up, the face at -Y, the character's left at +X.
"""
import gzip
import json
import math
import os

import numpy as np
from mathutils import Vector

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "makehuman")
BODY_VERTS = 13380            # the body is the first vertices; the rest are helpers

OPPOSITES = [("decr", "incr"), ("down", "up"), ("in", "out"), ("backward", "forward"),
             ("concave", "convex"), ("compress", "uncompress")]


def _to_blender(a):
    """MakeHuman's space (Y up, the face at +Z, decimetres) to Blender's, in metres."""
    a = np.asarray(a, dtype=np.float64)
    return np.stack([a[..., 0], -a[..., 2], a[..., 1]], axis=-1) * 0.1


class Base:
    """The base mesh and everything read once."""
    _one = None

    @classmethod
    def get(cls):
        if cls._one is None:
            cls._one = cls()
        return cls._one

    def __init__(self):
        verts, faces, groups = [], [], []
        group = None
        with open(os.path.join(DATA, "base.obj")) as f:
            for line in f:
                if line.startswith("v "):
                    p = line.split()
                    verts.append((float(p[1]), float(p[2]), float(p[3])))
                elif line.startswith("g "):
                    group = line.split()[1]
                elif line.startswith("f "):
                    faces.append(tuple(int(t.split("/")[0]) - 1 for t in line.split()[1:]))
                    groups.append(group)
        self.verts = _to_blender(verts)
        self.faces = faces
        self.face_groups = groups
        self.body_faces = [f for f, g in zip(faces, groups) if g == "body"]
        vg = json.load(open(os.path.join(DATA, "basemesh_vertex_groups.json")))
        self.vgroups = {k: np.array([i for a, b in spans for i in range(a, b + 1)]) for k, spans in vg.items()}
        self.rig = json.load(open(os.path.join(DATA, "rig.game_engine.json")))
        w = json.load(gzip.open(os.path.join(DATA, "weights.game_engine.json.gz"), "rt"))["weights"]
        self.weights = {b: (np.array([i for i, _ in rows], dtype=np.int64), np.array([x for _, x in rows])) for b, rows in w.items() if rows}
        total = np.zeros(len(self.verts))
        for idx, x in self.weights.values():
            np.add.at(total, idx, x)
        self.weight_total = np.where(total > 1e-9, total, 1.0)
        self.regions = json.load(open(os.path.join(DATA, "regions.json")))
        self.macro = json.load(open(os.path.join(DATA, "targets", "macrodetails", "macro.json")))["macrotargets"]
        self.index = {}
        for root, _, files in os.walk(os.path.join(DATA, "targets")):
            for fn in files:
                if fn.endswith(".target.gz"):
                    rel = os.path.relpath(os.path.join(root, fn), os.path.join(DATA, "targets"))[:-len(".target.gz")]
                    self.index[rel.replace(os.sep, "/")] = os.path.join(root, fn)
        self.by_stem = {}
        for rel in self.index:
            if not rel.startswith(("macrodetails", "breast/female")):
                self.by_stem[rel.split("/")[-1]] = rel
        self._cache = {}
        # the bones in an order where a parent comes before its children
        self.order = []
        todo = [b for b, d in self.rig.items() if not d["parent"]]
        while todo:
            b = todo.pop(0)
            self.order.append(b)
            todo += [c for c, d in self.rig.items() if d["parent"] == b]

    def target(self, rel):
        if rel not in self._cache:
            idx, d = [], []
            with gzip.open(self.index[rel], "rt") as f:
                for line in f:
                    p = line.split()
                    if len(p) == 4 and not line.startswith("#"):
                        idx.append(int(p[0]))
                        d.append((float(p[1]), float(p[2]), float(p[3])))
            self._cache[rel] = (np.array(idx, dtype=np.int64), _to_blender(d) if d else np.zeros((0, 3)))
        return self._cache[rel]

    # --- naming the targets -----------------------------------------------------------

    def _parts(self, var, value):
        """A macro variable's value as {component name: weight} (macro.json)."""
        out = {}
        for part in self.macro[var]["parts"]:
            lo, hi = part["lowest"], part["highest"]
            if lo <= value <= hi:
                t = min(1.0, max(0.0, (value - lo) / (hi - lo)))
                out[part["low"]] = out.get(part["low"], 0.0) + (1.0 - t)
                out[part["high"]] = out.get(part["high"], 0.0) + t
        return out

    def macro_targets(self, gender, muscle, weight, ancestry, age=0.5, proportions=0.5, height=0.5, cup=0.5, firmness=0.5):
        """The macro targets and their weights for one form, as MakeHuman combines them."""
        g, a = self._parts("gender", gender), self._parts("age", age)
        m, w = self._parts("muscle", muscle), self._parts("weight", weight)
        total = sum(ancestry.values()) or 1.0
        out = {}

        def add(rel, k):
            if k > 1e-6 and rel in self.index:
                out[rel] = out.get(rel, 0.0) + k
        for gn, gk in g.items():
            for an, ak in a.items():
                for rn, rk in ancestry.items():
                    add("macrodetails/%s-%s-%s" % (rn, gn, an), gk * ak * rk / total)
                for mn, mk in m.items():
                    for wn, wk in w.items():
                        k = gk * ak * mk * wk
                        stem = "%s-%s-%s-%s" % (gn, an, mn, wn)
                        add("macrodetails/universal-" + stem, k)
                        for pn, pk_ in self._parts("proportions", proportions).items():
                            if pn:
                                add("macrodetails/proportions/%s-%s" % (stem, pn), k * pk_)
                        for hn, hk in self._parts("height", height).items():
                            if hn:
                                add("macrodetails/height/%s-%s" % (stem, hn), k * hk)
                        for cn, ck in self._parts("cupsize", cup).items():
                            for fn, fk in self._parts("firmness", firmness).items():
                                add("breast/%s-%s-%s" % (stem, cn, fn), k * ck * fk)
        return out

    def detail_targets(self, details):
        """Details by their short names: `nose-hump: 0.4` is nose-hump-incr at 0.4, a negative
        value its opposite; a name without a side is both sides; a single target (head-oval)
        takes its value as it is."""
        out = {}
        for key, value in (details or {}).items():
            value = float(value)
            if abs(value) < 1e-6:
                continue
            names = [key] if (key in self.by_stem or any(key + "-" + s in self.by_stem for pair in OPPOSITES for s in pair)) else ["l-" + key, "r-" + key]
            for name in names:
                if name in self.by_stem:
                    if value > 0:
                        out[self.by_stem[name]] = value
                    continue
                for neg, pos in OPPOSITES:
                    if name + "-" + pos in self.by_stem or name + "-" + neg in self.by_stem:
                        stem = name + "-" + (pos if value > 0 else neg)
                        if stem not in self.by_stem:
                            raise KeyError("no target %s" % stem)
                        out[self.by_stem[stem]] = abs(value)
                        break
                else:
                    raise KeyError("no MakeHuman target for the detail '%s'" % key)
        return out

    def knows(self, key):
        try:
            self.detail_targets({key: 1.0})
            return True
        except KeyError:
            return False

    def shaped(self, targets):
        v = self.verts.copy()
        for rel, k in targets.items():
            idx, d = self.target(rel)
            v[idx] += d * k
        return v

    def joint(self, v, name):
        return v[self.vgroups[name]].mean(axis=0)


# ======================================================================================
# The pose: MakeHuman's stance to the game rig's T-pose
# ======================================================================================

def _rot_between(a, b):
    q = Vector(a).normalized().rotation_difference(Vector(b).normalized())
    return np.array(q.to_matrix())


def _rot_axis(axis, angle):
    from mathutils import Matrix
    return np.array(Matrix.Rotation(angle, 3, Vector(axis).normalized()))


def _about(point, R):
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = point - R @ point
    return M


def pose_matrices(base, v, aim, roll=None, curl=0.0):
    """Forward kinematics: each bone named in `aim` turned (the least turn) so it points along
    its aim, in order from the root; `roll` turns a bone about its own aim after that; `curl`
    closes the fingers a little. Returns {bone: 4x4} taking rest positions to posed ones."""
    A = {}
    roll = roll or {}
    for b in base.order:
        d = base.rig[b]
        Ap = A.get(d["parent"], np.eye(4))
        M = Ap
        finger = curl and b.split("_")[0] in ("index", "middle", "ring", "pinky")
        if b in aim or finger:
            h = base.joint(v, d["head"]["cube_name"])
            t = base.joint(v, d["tail"]["cube_name"])
            h2 = Ap[:3, :3] @ h + Ap[:3, 3]
            t2 = Ap[:3, :3] @ t + Ap[:3, 3]
            R = np.eye(3)
            if b in aim:
                R = _rot_between(t2 - h2, aim[b])
                if b in roll:
                    R = _rot_axis(aim[b], roll[b]) @ R
            if finger:
                side = 1.0 if b.endswith("_l") else -1.0
                R = _rot_axis((0, 1, 0), side * curl) @ R
            M = _about(h2, R) @ Ap
        A[b] = M
    return A


def skin(base, v, A):
    """Linear blend skinning of every vertex (helpers and joints too) by MakeHuman's weights."""
    out = np.zeros_like(v)
    for b, (idx, w) in base.weights.items():
        M = A.get(b, np.eye(4))
        out[idx] += (v[idx] @ M[:3, :3].T + M[:3, 3]) * (w / base.weight_total[idx])[:, None]
    untouched = np.ones(len(v), dtype=bool)
    for idx, _ in base.weights.values():
        untouched[idx] = False
    out[untouched] = v[untouched]
    return out


# Where each game-rig bone's pivot sits on the human (a joint, or a point between two).
RIG_JOINTS = {
    "hips": ("joint-pelvis",), "spine": ("joint-spine-4",), "chest": ("joint-spine-2",),
    "head": ("joint-neck", "joint-head", 0.6),
    "upperarm.l": ("joint-l-shoulder",), "lowerarm.l": ("joint-l-elbow",), "wrist.l": ("joint-l-hand",),
    "upperarm.r": ("joint-r-shoulder",), "lowerarm.r": ("joint-r-elbow",), "wrist.r": ("joint-r-hand",),
    "upperleg.l": ("joint-l-upper-leg",), "lowerleg.l": ("joint-l-knee",), "foot.l": ("joint-l-ankle",), "toes.l": ("joint-l-foot-1",),
    "upperleg.r": ("joint-r-upper-leg",), "lowerleg.r": ("joint-r-knee",), "foot.r": ("joint-r-ankle",), "toes.r": ("joint-r-foot-1",),
}
TRUNK_BONES = ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "clavicle_r", "Root")


class Human:
    """One form (sex, build, a home's ancestry and details), posed and at the game's size."""

    def __init__(self, sex, ancestry, details=None, build=(0.5, 0.5), height=2.4, cup=0.5, proportions=0.6, like=None, age=0.5):
        base = self.base = Base.get()
        self.sex = sex
        muscle, weight = build
        # age: 0.5 is a young adult; below it MakeHuman's child and baby forms (the genius kit's
        # small people; only the average build's targets are kept for those ages)
        targets = base.macro_targets(1.0 if sex == "m" else 0.0, muscle, weight, ancestry, age=age, proportions=proportions, cup=cup, firmness=0.6)
        targets.update(base.detail_targets(details))
        self.targets = targets
        v = base.shaped(targets)
        if like is None:
            self.A = self._pose(v)
            posed = skin(base, v, self.A)
            body = posed[:BODY_VERTS]
            ground = body[:, 2].min()
            hip = 0.5 * (base.joint(posed, "joint-l-upper-leg") + base.joint(posed, "joint-r-upper-leg"))
            self.scale = height / (body[:, 2].max() - ground)
            self.offset = np.array([hip[0], hip[1], ground])
        else:
            # another build of the same person: the same pose and size, so only the form differs
            self.A, self.scale, self.offset = like.A, like.scale, like.offset
            posed = skin(base, v, self.A)
        self.v = (posed - self.offset) * self.scale
        self.height = height

    def _pose(self, v):
        base = self.base
        aim = {}
        for s, sg in (("l", 1.0), ("r", -1.0)):
            for b in ("upperarm", "lowerarm", "hand"):
                aim["%s_%s" % (b, s)] = (sg, 0.0, 0.0)
            aim["thigh_" + s] = (0.0, -0.02, -1.0)
            aim["calf_" + s] = (0.0, 0.035, -1.0)
            aim["ball_" + s] = (0.0, -1.0, 0.0)
        # first pass: see where the foot and the palm end up, then level them
        A = pose_matrices(base, v, aim)
        p = skin(base, v, A)
        roll = {}
        for s, sg in (("l", 1.0), ("r", -1.0)):
            # the foot: its sole flat. The ankle-to-ball line keeps its own slope; the ball is aimed forward
            ankle, ball = base.joint(p, "joint-%s-ankle" % s), base.joint(p, "joint-%s-foot-1" % s)
            d = ball - ankle
            aim["foot_" + s] = (0.0, -math.hypot(d[0], d[1]), d[2])
            # the palm: down. Its normal from the knuckles; the turn it needs about the arm's line
            wrist = base.joint(p, "joint-%s-hand" % s)
            index, pinky = base.joint(p, "joint-%s-finger-2-1" % s), base.joint(p, "joint-%s-finger-5-1" % s)
            n = np.cross(index - wrist, pinky - wrist) * sg     # out of the back of the hand
            ang = math.atan2(n[1], n[2]) * sg                   # the turn about +-X that brings it to +Z
            roll["upperarm_" + s] = ang * 0.35
            roll["lowerarm_" + s] = ang * 0.4
            roll["hand_" + s] = ang * 0.25
            # the fingers: together, a slight fan (the index to the front, the little finger back)
            for f, fan in (("index", -0.05), ("middle", 0.0), ("ring", 0.05), ("pinky", 0.11)):
                aim["%s_01_%s" % (f, s)] = (sg, fan, 0.0)
        return pose_matrices(base, v, aim, roll, curl=math.radians(13))

    # --- reading it ---------------------------------------------------------------------

    def joint(self, name):
        return self.base.joint(self.v, name)

    def rig_joints(self):
        """Where the game rig's bones pivot on this body."""
        out = {}
        for bone, spec in RIG_JOINTS.items():
            p = self.joint(spec[0])
            if len(spec) == 3:
                p = p + (self.joint(spec[1]) - p) * spec[2]
            out[bone] = Vector(p)
        for s, sg in (("l", 1.0), ("r", -1.0)):
            wrist = self.joint("joint-%s-hand" % s)
            knuckle = self.joint("joint-%s-finger-3-1" % s)
            out["hand." + s] = Vector(wrist + (knuckle - wrist) * 0.45)
            # the grip: under the palm, between the wrist and the knuckles
            out["handslot." + s] = Vector(wrist + (knuckle - wrist) * 0.8 + np.array([0.0, 0.0, -0.035]))
        return out

    def body(self):
        return self.v[:BODY_VERTS]

    def group(self, name):
        return self.v[self.base.vgroups[name]]

    def rig_weights(self):
        """Per body vertex {game-rig bone: weight}, from MakeHuman's game-rig weights: the limbs
        bone for bone; the trunk's share laid again along the game rig's three trunk bones by
        height; the neck shared between the chest and the head; the hand between wrist and hand."""
        base = self.base
        n = BODY_VERTS
        W = {}

        def add(bone, idx, w):
            keep = idx < n
            a = W.setdefault(bone, np.zeros(n))
            np.add.at(a, idx[keep], w[keep])
        direct = {"thigh": "upperleg", "calf": "lowerleg", "foot": "foot", "ball": "toes", "upperarm": "upperarm", "lowerarm": "lowerarm"}
        trunk = np.zeros(n)
        neck = np.zeros(n)
        hand = {"l": np.zeros(n), "r": np.zeros(n)}
        for b, (idx, w) in base.weights.items():
            w = w / base.weight_total[idx]
            stem, _, side = b.rpartition("_")
            if b in ("pelvis", "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "Root"):
                keep = idx < n
                np.add.at(trunk, idx[keep], w[keep])
            elif b == "neck_01":
                keep = idx < n
                np.add.at(neck, idx[keep], w[keep])
            elif b == "head":
                add("head", idx, w)
            elif stem in direct:
                add("%s.%s" % (direct[stem], side), idx, w)
            else:   # the hand and its fingers
                keep = idx < n
                np.add.at(hand[side], idx[keep], w[keep])
        J = self.rig_joints()
        z = self.body()[:, 2]
        x = self.body()[:, 0]

        def step(t):
            t = np.clip(t, 0.0, 1.0)
            return t * t * (3 - 2 * t)
        # the trunk: hips below the spine's pivot, chest above the chest's, the spine between
        band = 0.07 * self.height / 2.4
        up1 = step((z - (J["spine"].z - band)) / (2 * band))
        up2 = step((z - (J["chest"].z - band)) / (2 * band))
        W["hips"] = W.get("hips", np.zeros(n)) + trunk * (1 - up1)
        W["spine"] = trunk * up1 * (1 - up2)
        W["chest"] = trunk * up2
        # the neck: the chest at its base, the head at the skull
        z0, z1 = self.joint("joint-neck")[2], self.joint("joint-head")[2]
        t = step((z - z0) / max(1e-6, z1 - z0))
        W["chest"] = W["chest"] + neck * (1 - t)
        W["head"] = W.get("head", np.zeros(n)) + neck * t
        for s, sg in (("l", 1.0), ("r", -1.0)):
            xj = J["hand." + s].x * sg
            t = step((x * sg - (xj - 0.025)) / 0.05)
            W["wrist." + s] = hand[s] * (1 - t)
            W["hand." + s] = hand[s] * t
        return W

    def dominant(self):
        """Per body vertex, the MakeHuman bone that holds it most: for telling the trunk from
        the arms and the legs."""
        base = self.base
        best = np.zeros(BODY_VERTS)
        name = np.empty(BODY_VERTS, dtype=object)
        for b, (idx, w) in base.weights.items():
            keep = idx < BODY_VERTS
            i, x = idx[keep], w[keep]
            better = x > best[i]
            best[i[better]] = x[better]
            name[i[better]] = b
        return name


def mesh_object(name, verts, faces, materials=(), face_material=None):
    """A Blender mesh object from arrays (smooth shaded)."""
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(float(x) for x in p) for p in verts], [], [tuple(int(i) for i in f) for f in faces])
    me.update()
    for m in materials:
        me.materials.append(m)
    if face_material is not None:
        for poly, mi in zip(me.polygons, face_material):
            poly.material_index = mi
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob
