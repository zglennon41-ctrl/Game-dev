"""WILDLINE faces: what makes two people of one home two people, and a face worth a close look
(docs/bodies-plan.md, "Faces, eyes and hair").

  * Face shapes as shape keys: the presets and the sliders of data/bodies.json (`faces`), each a
    set of MakeHuman's detail targets laid over the home's own form, kept to the face (the
    skull under the hair stays, so every cap and hat still fits), and carried onto whatever
    sits on the face (brows, lashes, beards, marks; the eyes move and grow with their sockets).
  * The face's shading: the skin's normals are smoothed so the cel bands fall as planes, the
    creases are lightened, and the cheeks, the nose and the ears are a little warmer (the
    vertex colour's hue; its red is the occlusion as before).
  * The eyes: an iris with a darker rim, a pupil, a catch-light, a white that is not white and
    is shaded under the upper lid; short lashes; a lid that closes (the shape key `blink`).
  * Brows with shape (shape keys on the one ribbon), marks on the skin (freckles, a mole,
    scars, kohl, a home's paint), and the hair and the beards.

World space is Blender's: Z up, the face at -Y, the character's left at +X.
"""
import json
import math
import os

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

import people_kit as pk
import human as hu

EYE_WHITE = (0.80, 0.78, 0.74, 1)
GLINT = (1.0, 1.0, 1.0, 1)
MARK_COLORS = {
    "skin_freckle": (0.42, 0.26, 0.17, 1), "skin_scar": (0.82, 0.62, 0.56, 1), "skin_mole": (0.13, 0.08, 0.06, 1),
    "skin_kohl": (0.035, 0.03, 0.035, 1), "skin_ink": (0.08, 0.1, 0.15, 1), "skin_red": (0.5, 0.11, 0.09, 1),
    "skin_ochre": (0.7, 0.47, 0.18, 1), "skin_white": (0.86, 0.84, 0.78, 1),
}
BROWS = {   # thick, arch, lift, tilt (the tail's rise), length: multipliers and offsets on the soft brow
    "straight": (1.0, 0.25, -0.06, 0.1, 1.0), "arched": (0.8, 1.7, 0.1, 0.0, 1.0), "heavy": (1.55, 0.7, -0.1, 0.0, 1.04),
    "fine": (0.55, 1.2, 0.06, 0.05, 0.94), "slant": (0.95, 0.5, 0.0, 0.32, 1.0),
}


def spec():
    try:
        return json.load(open(os.path.join(pk.ROOT, "data", "bodies.json"))).get("faces", {})
    except OSError:
        return {}


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _nsmooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _bump(s):
    s = abs(s)
    return (1.0 - s * s) ** 1.5 if s < 1.0 else 0.0


def add_key(ob, name, coords):
    if not ob.data.shape_keys:
        ob.shape_key_add(name="Basis", from_mix=False)
    key = ob.shape_key_add(name=name, from_mix=False)
    key.data.foreach_set("co", np.asarray(coords, dtype=np.float32).ravel())
    return key


def coords_of(ob):
    a = np.zeros(len(ob.data.vertices) * 3, dtype=np.float32)
    ob.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3).astype(np.float64)


def paint(ob, colors):
    me = ob.data
    if not me.color_attributes:
        me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    col = me.color_attributes[0]
    flat = np.ones((len(me.vertices), 4), dtype=np.float32)
    flat[:, :3] = colors
    col.data.foreach_set("color", flat.ravel())


class Faces:
    """The face keys of one body, and the finish of its face."""

    def __init__(self, hb, ancestry, details, build):
        self.hb = hb
        self.fit = fit = hb.humans["fit"]
        self.ancestry, self.details, self.build = ancestry, details, build
        self.R = hb.eye_r
        self.H = hb.head_h
        (x0, x1), (y0, y1), (z0, z1) = hb.head_box
        self.c = Vector((0.0, (y0 + y1) / 2 + 0.01, hb.chin_z + 0.5 * self.H))
        self.mask = self._mask(fit.v)
        n = hu.BODY_VERTS
        self._anchor = (self.mask[:n] < 0.01) & (fit.v[:n, 2] > hb.chin_z + 0.15 * self.H)
        self.keys = {}      # name -> the offsets of every vertex (the helpers too)
        self.eyes = {}      # name -> {side: (the eye's move, its growth)}
        self.builds = {}    # the builds beyond lean and heavy (human_kit._extra_build): carried here, keyed on the body there
        self.build_eyes = {}
        sp = spec()
        for p in sp.get("presets", []):
            d = dict(p.get("details", {}))
            d.update(p.get(hb.body.sex, {}))
            self.keys["face_" + p["id"]], self.eyes["face_" + p["id"]] = self._offsets(d, float(p.get("age", 0.0)))
        for s in sp.get("sliders", []):
            up, eu = self._offsets(s.get("details", {}), 0.0)
            dn, ed = self._offsets({k: -float(x) for k, x in s.get("details", {}).items()}, 0.0)
            self.keys["set_" + s["id"]] = (up - dn) / 2
            self.eyes["set_" + s["id"]] = {k: ((eu[k][0] - ed[k][0]) / 2, 1.0 + (eu[k][1] - ed[k][1]) / 2) for k in eu}
        self._kd = None

    def _mask(self, v):
        """1 on the face, 0 on the skull under the hair, behind the ears and down the neck."""
        H, c = self.H, self.c
        top = _nsmooth((c.z + 0.37 * H - v[:, 2]) / (0.13 * H))
        back = _nsmooth((c.y + 0.17 * H - v[:, 1]) / (0.17 * H))
        neck = _nsmooth((v[:, 2] - (self.hb.chin_z - 0.17 * H)) / (0.15 * H))
        return top * back * neck

    def _offsets(self, extra, age):
        fit = self.fit
        d = dict(self.details)
        for k, x in extra.items():
            d[k] = max(-1.6, min(1.6, float(d.get(k, 0.0)) + float(x)))
        h = hu.Human(self.hb.body.sex, self.ancestry, d, self.build, height=fit.height, like=fit, age=0.5 + age)
        delta = h.v - fit.v
        shift = delta[:hu.BODY_VERTS][self._anchor].mean(axis=0)
        eyes = {}
        for s in ("l", "r"):
            c0, c1 = fit.joint("joint-%s-eye" % s), h.joint("joint-%s-eye" % s)
            g = h.group("helper-%s-eye" % s)
            r1 = float(np.linalg.norm(g - g.mean(axis=0), axis=1).mean())
            eyes[s] = (c1 - c0 - shift, r1 / self.R)
        delta = (delta - shift) * self.mask[:, None]
        delta[np.linalg.norm(delta, axis=1) < 0.00012] = 0.0       # what does not move is not stored
        return delta, eyes

    # --- the keys, on the body and on what sits on the face --------------------------------

    def key_body(self, ob):
        base = self.fit.body()
        for name, d in self.keys.items():
            add_key(ob, name, base + d[:hu.BODY_VERTS])

    def carry(self, ob, least=0.0005):
        """A piece on the face takes each key from the skin under it (the four nearest
        vertices of the face); a key that does not move it is left out."""
        if self._kd is None:
            v = self.fit.body()
            self._near = np.nonzero(self.mask[:hu.BODY_VERTS] > 0.03)[0]
            self._kd = KDTree(len(self._near))
            for j, i in enumerate(self._near):
                self._kd.insert(Vector(v[i]), j)
            self._kd.balance()
        co = coords_of(ob)
        idx = np.zeros((len(co), 4), dtype=np.int64)
        w = np.zeros((len(co), 4))
        for i, p in enumerate(co):
            for j, (_, k, dist) in enumerate(self._kd.find_n(Vector(p), 4)):
                idx[i, j] = self._near[k]
                w[i, j] = 1.0 / (dist + 0.002) ** 2
        w /= w.sum(axis=1, keepdims=True)
        for name, d in list(self.keys.items()) + list(self.builds.items()):
            off = (d[idx] * w[:, :, None]).sum(axis=1)
            if np.abs(off).max() > least:
                off[np.linalg.norm(off, axis=1) < 0.00015] = 0.0
                add_key(ob, name, co + off)

    def carry_eye(self, ob, side):
        """An eye (the ball, the lid over it) moves and grows with its socket."""
        co = coords_of(ob)
        c = np.array(self.hb.eye[side])
        for name, eyes in list(self.eyes.items()) + list(self.build_eyes.items()):
            move, grow = eyes[side]
            if np.abs(move).max() > 0.0002 or abs(grow - 1.0) > 0.004:
                add_key(ob, name, c + move + (co - c) * grow)

    # --- the finish of the skin ------------------------------------------------------------

    def smooth_normals(self, ob, rounds=5):
        """The face's normals, smoothed: under bands of light a face wants planes, not every
        dimple (the nose, the lips and the lids keep more of their own; the ears all)."""
        hb = self.hb
        v = self.fit.body()
        fa = hb.face_idx
        n0 = hb.normals("fit").copy()
        head = v[:, 2] > hb.chin_z - 0.3 * self.H
        a = np.concatenate([fa[:, 0], fa[:, 1], fa[:, 2], fa[:, 3]])
        b = np.concatenate([fa[:, 1], fa[:, 2], fa[:, 3], fa[:, 0]])
        n = n0.copy()
        for _ in range(rounds):
            acc = n.copy()
            np.add.at(acc, a, n[b])
            np.add.at(acc, b, n[a])
            acc /= np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-9)
            n[head] = acc[head]
        k = np.full(len(v), 0.75)
        regions = hb.base.regions
        for region, kk in (("lips", 0.35), ("eyelids", 0.45), ("ears", 0.0), ("inside_mouth", 0.0)):
            k[np.unique(fa[regions[region]])] = kk
        # the nose keeps its sides: a column down the middle of the face, from the root to the base
        ez = hb.eye["l"].z
        nose = _nsmooth(1.0 - np.abs(v[:, 0]) / (1.5 * self.R)) * _nsmooth((v[:, 2] - (ez - 3.4 * self.R)) / (0.8 * self.R)) * _nsmooth((ez + 0.6 * self.R - v[:, 2]) / (0.8 * self.R)) * (v[:, 1] < self.c.y - 0.2 * self.H)
        k = k * (1.0 - 0.55 * nose)
        k *= _nsmooth((v[:, 2] - (hb.chin_z - 0.3 * self.H)) / (0.2 * self.H))
        out = n0 * (1.0 - k[:, None]) + n * k[:, None]
        out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)
        ob.data.normals_split_custom_set_from_vertices([tuple(float(x) for x in p) for p in out])

    def paint_skin(self, ob):
        """After the cavity bake: the face's creases lightened (a face is not a wall), the
        hollow over the eye kept, and warmth in the cheeks, the nose, the ears and the chin."""
        hb = self.hb
        v = self.fit.body()
        fa = hb.face_idx
        me = ob.data
        col = me.color_attributes[0]
        flat = np.zeros(len(me.vertices) * 4, dtype=np.float32)
        col.data.foreach_get("color", flat)
        flat = flat.reshape(-1, 4)
        occ = flat[:, 0].astype(np.float64)
        m = self.mask[:hu.BODY_VERTS]
        occ = occ + (1.0 - occ) * 0.62 * m
        R, ez = self.R, hb.eye["l"].z
        warm = np.zeros(len(v))
        for sg in (1.0, -1.0):
            ex = hb.eye["l"].x * sg
            d = np.sqrt(((v[:, 0] - (ex + 0.55 * R * sg)) / (1.9 * R)) ** 2 + ((v[:, 2] - (ez - 2.45 * R)) / (1.35 * R)) ** 2)
            warm = np.maximum(warm, 0.9 * _nsmooth(1.0 - d))
            # the hollow between the lid and the brow: a little shade, so the eye sits in
            d2 = np.sqrt(((v[:, 0] - ex) / (1.5 * R)) ** 2 + ((v[:, 2] - (ez + 0.75 * R)) / (0.45 * R)) ** 2)
            occ = occ - 0.1 * _nsmooth(1.0 - d2) * m
        dn = np.sqrt((v[:, 0] / (0.8 * R)) ** 2 + ((v[:, 2] - (ez - 2.2 * R)) / (0.9 * R)) ** 2)
        warm = np.maximum(warm, 0.6 * _nsmooth(1.0 - dn))
        dc = np.sqrt((v[:, 0] / (1.2 * R)) ** 2 + ((v[:, 2] - (hb.chin_z + 0.5 * R)) / (0.9 * R)) ** 2)
        warm = np.maximum(warm, 0.35 * _nsmooth(1.0 - dc))
        warm *= (v[:, 1] < self.c.y - 0.12 * self.H)
        warm[np.unique(fa[hb.base.regions["ears"]])] = 0.7
        warm *= (v[:, 2] > hb.chin_z - 0.05 * self.H)
        flat[:, 0] = occ
        flat[:, 1] = occ * (1.0 - 0.13 * warm)
        flat[:, 2] = occ * (1.0 - 0.15 * warm)
        col.data.foreach_set("color", flat.ravel())


# ======================================================================================
# The eyes, the lids, the lashes, the brows
# ======================================================================================

EYE_RINGS = [(4.5, "pupil"), (9.5, "pupil"), (14.0, "iris"), (19.5, "iris"), (25.0, "iris"), (29.5, "iris_rim"),
             (34.0, "eye_white"), (42.0, "eye_white"), (54.0, "eye_white"), (68.0, "eye_white"), (84.0, "eye_white"), (102.0, "eye_white")]


def _mat(mats, name, color):
    if name not in mats:
        mats[name] = pk._material(name, color, rough=0.85)
    return mats[name]


def eyeball(name, c, R, mats, seg=24):
    """An eye that looks ahead: rings about the gaze, so the pupil and the iris are true
    circles; the iris has a darker rim; a catch-light sits up and to one side; the white is
    shaded toward the upper lid."""
    names = ["eye_white", "iris", "pupil", "iris_rim", "eye_glint"]
    slot = {n: i for i, n in enumerate(names)}
    bm = bmesh.new()

    def at(polar, az, r=R):
        s, co = math.sin(math.radians(polar)), math.cos(math.radians(polar))
        return Vector((c.x + r * s * math.cos(az), c.y - r * co, c.z + r * s * math.sin(az)))
    pole = bm.verts.new(at(0.0, 0.0))
    rings = []
    for polar, _ in EYE_RINGS:
        rings.append([bm.verts.new(at(polar, 2 * math.pi * k / seg)) for k in range(seg)])
    for k in range(seg):
        f = bm.faces.new((pole, rings[0][(k + 1) % seg], rings[0][k]))
        f.material_index = slot["pupil"]
    for i in range(len(rings) - 1):
        for k in range(seg):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
            f.material_index = slot[EYE_RINGS[i + 1][1]]
    # the catch-light: a small disc just off the cornea, up and to the character's right
    g = (at(15.0, math.radians(125.0)) - c).normalized()
    u = g.cross(Vector((0, 0, 1))).normalized()
    w = g.cross(u).normalized()
    gc = c + g * R * 1.012
    centre = bm.verts.new(gc)
    disc = [bm.verts.new(gc + (u * math.cos(2 * math.pi * k / 8) + w * math.sin(2 * math.pi * k / 8)) * R * 0.085) for k in range(8)]
    for k in range(8):
        f = bm.faces.new((centre, disc[k], disc[(k + 1) % 8]))
        f.material_index = slot["eye_glint"]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for n, colr in (("eye_white", EYE_WHITE), ("iris", None), ("pupil", None), ("iris_rim", (0.03, 0.025, 0.02, 1)), ("eye_glint", GLINT)):
        me.materials.append(mats[n] if colr is None else _mat(mats, n, colr))
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    co = coords_of(ob)
    up = (co[:, 2] - c.z) / R
    shade = 1.0 - 0.42 * _nsmooth((up - 0.02) / 0.5)
    paint(ob, np.repeat(shade[:, None], 3, axis=1))
    return ob


def lid(name, c, R, mats, seg=18):
    """A closed lid: a cap of skin over the eye with the lashes' line across it. It lies
    inside the eyeball, out of sight, and the shape key `blink` brings it out over it."""
    bm = bmesh.new()
    rows = []
    n_rows = 9
    for i in range(n_rows + 1):
        el = math.radians(-62.0 + 124.0 * i / n_rows)
        row = []
        for k in range(seg + 1):
            az = math.radians(-78.0 + 156.0 * k / seg)
            row.append(bm.verts.new(Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))))
        rows.append(row)
    line = 2     # the lashes' line: the rows just under the middle
    for i in range(n_rows):
        for k in range(seg):
            f = bm.faces.new((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]))
            f.material_index = 1 if i == line else 0
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mats["skin"])
    me.materials.append(mats["lash"])
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    unit = coords_of(ob)
    cc = np.array(c)
    ob.data.vertices.foreach_set("co", (cc + unit * R * 0.8).astype(np.float32).ravel())
    add_key(ob, "blink", cc + unit * R * 1.045)
    return ob


def lashes(hb, side, mats):
    """MakeHuman's lash strips, cut short (they are made for a painted texture; solid, they
    are a black bar): the upper lid's a dark edge, the lower's a line."""
    fit, base = hb.humans["fit"], hb.base
    lids = np.unique(hb.face_idx[base.regions["eyelids"]])
    kd = KDTree(len(lids))
    for j, i in enumerate(lids):
        kd.insert(Vector(fit.v[i]), j)
    kd.balance()
    pts, quads = [], []
    for part, keep in (("2", 0.42), ("1", 0.12)):
        faces = [f for f, g in zip(base.faces, base.face_groups) if g == "helper-%s-eyelashes-%s" % (side, part)]
        used = sorted({i for f in faces for i in f})
        p = fit.v[used].copy()
        dist = np.array([kd.find(Vector(q))[2] for q in p])
        roots = np.nonzero(dist < np.percentile(dist, 45))[0]
        for i in range(len(p)):
            if i in roots:
                continue
            r = roots[np.argmin(np.linalg.norm(p[roots] - p[i], axis=1))]
            p[i] = p[r] + (p[i] - p[r]) * keep
        remap = {i: j + len(pts) for j, i in enumerate(used)}
        quads += [tuple(remap[i] for i in f) for f in faces]
        pts += [tuple(q) for q in p]
    n = len(pts)
    back = [tuple(i + n for i in q[::-1]) for q in quads]
    return hu.mesh_object("Lash_" + side, np.array(pts + pts), quads + back, [mats["lash"]])


def _brow_rows(hb, bvh, side, sg, fem, style=None, n=14):
    c, R = hb.eye[side], hb.eye_r
    thick_k, arch_k, lift, tilt, length = BROWS.get(style, (1.0, 1.0, 0.0, 0.0, 1.0))
    thick = (0.2 if fem else 0.29) * R * thick_k
    rows = [[], [], []]
    for i in range(n):
        t = i / (n - 1.0)
        x = c.x + sg * (-1.2 + 3.25 * t * length) * R
        arch = (0.5 if fem else 0.34) * arch_k
        z = c.z + ((1.52 if fem else 1.4) + lift + arch * math.sin(min(1.0, t / 0.66) * math.pi / 2) - (0.5 - tilt) * max(0.0, t - 0.66) / 0.34 + tilt * t) * R
        half = thick * (0.35 + 0.65 * math.sin(min(1.0, t / 0.16) * math.pi / 2)) * (1.0 - 0.85 * max(0.0, t - 0.45) / 0.55)
        for j, dz in enumerate((half, 0.0, -half)):
            hit, nrm, _, _ = bvh.ray_cast(Vector((x, -2.0, z + dz)), Vector((0, 1, 0)))
            if hit is None:
                hit, nrm = Vector((x, c.y - R, z + dz)), Vector((0, -1, 0))
            rows[j].append(hit + nrm * (0.0013 if j == 1 else 0.0005))
    return rows


def brow(hb, side, sg, mats):
    """The brow: a ribbon of hair on the brow's bone, thin at the root, thick by a sixth,
    arched past the middle and drawn to a point; its other shapes are shape keys."""
    fem = hb.body.sex == "f"
    bvh = hb.bvh("all", "fit")
    rows = _brow_rows(hb, bvh, side, sg, fem)
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in row] for row in rows]
    for j in range(2):
        for i in range(len(rows[0]) - 1):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    ob = pk._bm_object("Brow_" + side, bm, mats["hair"])
    for style in BROWS:
        r2 = _brow_rows(hb, bvh, side, sg, fem, style)
        add_key(ob, "brow_" + style, np.array([tuple(p) for row in r2 for p in row]))
    return ob


def head_pieces(hb, mats, faces):
    out = []
    for s, sg in (("l", 1.0), ("r", -1.0)):
        eye = eyeball("Eye_" + s, hb.eye[s], hb.eye_r, mats)
        faces.carry_eye(eye, s)
        cover = lid("Lid_" + s, hb.eye[s], hb.eye_r, mats)
        b = brow(hb, s, sg, mats)
        faces.carry(b)
        lash = lashes(hb, s, mats)
        faces.carry(lash)
        out += [eye, cover, b, lash]
    for m in marks(hb, mats):
        faces.carry(m)
        out.append(m)
    return out


# ======================================================================================
# Marks: small things laid on the skin (shown by the look's `marks`)
# ======================================================================================

class _Decal:
    def __init__(self, hb, lift=0.0007):
        self.bvh = hb.bvh("all", "fit")
        self.bm = bmesh.new()
        self.lift = lift

    def on(self, x, z):
        hit, nrm, _, _ = self.bvh.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
        if hit is None:
            return None
        return hit + nrm * self.lift

    def dot(self, x, z, r, sides=7):
        c = self.on(x, z)
        ring = [self.on(x + r * math.cos(2 * math.pi * k / sides), z + r * math.sin(2 * math.pi * k / sides)) for k in range(sides)]
        if c is None or any(p is None for p in ring) or max((p - c).length for p in ring) > 4 * r:
            return
        cv = self.bm.verts.new(c)
        rv = [self.bm.verts.new(p) for p in ring]
        for k in range(sides):
            self.bm.faces.new((cv, rv[k], rv[(k + 1) % sides]))

    def stroke(self, pts, widths):
        """A ribbon through (x, z) points on the face, widths[i] across at each."""
        rows = []
        for i, (x, z) in enumerate(pts):
            ax, az = pts[max(i - 1, 0)]
            bx, bz = pts[min(i + 1, len(pts) - 1)]
            dx, dz = bx - ax, bz - az
            L = math.hypot(dx, dz) or 1.0
            nx, nz = -dz / L, dx / L
            h = widths[i] / 2
            row = [self.on(x + nx * h, z + nz * h), self.on(x, z), self.on(x - nx * h, z - nz * h)]
            if any(p is None for p in row):
                return
            rows.append([self.bm.verts.new(p) for p in row])
        for a, b in zip(rows, rows[1:]):
            for j in range(2):
                self.bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))

    def done(self, name, mat):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        if sum(f.normal.y for f in self.bm.faces) > 0:
            bmesh.ops.reverse_faces(self.bm, faces=self.bm.faces[:])
        for f in self.bm.faces:
            f.smooth = True
        return pk._bm_object(name, self.bm, mat)


def _line(a, b, n=6):
    return [(a[0] + (b[0] - a[0]) * i / (n - 1.0), a[1] + (b[1] - a[1]) * i / (n - 1.0)) for i in range(n)]


def _taper(n, w):
    return [w * (0.25 + 0.75 * math.sin(math.pi * i / (n - 1.0))) for i in range(n)]


def marks(hb, mats):
    """Every mark on every body (the creator offers a home its own): `Mark_<id>`."""
    import random
    R = hb.eye_r
    ex, ez = hb.eye["l"].x, hb.eye["l"].z
    mouth_z = float(hb.humans["fit"].body()[np.unique(hb.face_idx[hb.base.regions["lips"]])][:, 2].mean())
    out = []

    def mat(n):
        return _mat(mats, n, MARK_COLORS[n])
    # freckles: across the nose and the cheeks
    d = _Decal(hb)
    rnd = random.Random(7)
    for _ in range(64):
        x = rnd.uniform(-1.0, 1.0)
        z = rnd.uniform(0.0, 1.0)
        px = x * (ex + 1.5 * R)
        pz = ez - (0.95 + 1.75 * z * (0.45 + 0.55 * abs(x))) * R
        if abs(px) < 0.45 * R and z > 0.5:
            continue
        d.dot(px, pz, rnd.uniform(0.028, 0.06) * R, sides=6)
    out.append(d.done("Mark_freckles", mat("skin_freckle")))
    # a mole under the left eye; a beauty mark by the mouth
    d = _Decal(hb)
    d.dot(ex + 0.9 * R, ez - 1.35 * R, 0.07 * R)
    out.append(d.done("Mark_mole", mat("skin_mole")))
    d = _Decal(hb)
    d.dot(-(ex * 0.72), mouth_z + 0.45 * R, 0.065 * R)
    out.append(d.done("Mark_beauty", mat("skin_mole")))
    # scars: through the left brow; across the right cheek; a nick in the lip's line at the chin
    d = _Decal(hb, 0.0009)
    n = 7
    d.stroke(_line((ex + 0.75 * R, ez + 2.35 * R), (ex + 0.25 * R, ez + 0.95 * R), n), _taper(n, 0.11 * R))
    d.stroke(_line((ex + 0.2 * R, ez - 0.75 * R), (ex + 0.05 * R, ez - 1.3 * R), n), _taper(n, 0.09 * R))
    out.append(d.done("Mark_scar-brow", mat("skin_scar")))
    d = _Decal(hb, 0.0009)
    n = 9
    d.stroke(_line((-ex - 1.5 * R, ez - 1.3 * R), (-ex + 0.5 * R, ez - 2.6 * R), n), _taper(n, 0.13 * R))
    out.append(d.done("Mark_scar-cheek", mat("skin_scar")))
    # kohl: a dark line along both lids, drawn out past the outer corner
    d = _Decal(hb, 0.0006)
    for sg in (1.0, -1.0):
        n = 9
        up = [(sg * (ex + (-1.05 + 2.5 * i / (n - 1.0)) * R), ez + (0.02 + 0.55 * math.sin(math.pi * min(1.0, i / (n - 2.0)) * 0.9) + 0.12 * max(0, i - (n - 2))) * R) for i in range(n)]
        d.stroke(up, [0.05 * R + 0.1 * R * math.sin(math.pi * i / (n - 1.0)) for i in range(n)])
        lo = [(sg * (ex + (-0.95 + 2.2 * i / (n - 1.0)) * R), ez - (0.12 + 0.36 * math.sin(math.pi * i / (n - 1.0))) * R) for i in range(n)]
        d.stroke(lo, [0.035 * R + 0.06 * R * math.sin(math.pi * i / (n - 1.0)) for i in range(n)])
    out.append(d.done("Mark_kohl", mat("skin_kohl")))
    # a dot between the brows
    d = _Decal(hb)
    d.dot(0.0, ez + 1.75 * R, 0.16 * R, sides=10)
    out.append(d.done("Mark_brow-dot", mat("skin_red")))
    # three lines down the chin
    d = _Decal(hb)
    n = 6
    for x in (-0.42, 0.0, 0.42):
        d.stroke(_line((x * R, mouth_z - 0.75 * R), (x * R * 0.8, mouth_z - 2.0 * R), n), _taper(n, 0.1 * R))
    out.append(d.done("Mark_chin-lines", mat("skin_ink")))
    # two bars of ochre under each eye
    d = _Decal(hb)
    n = 6
    for sg in (1.0, -1.0):
        for dz in (1.35, 1.75):
            d.stroke(_line((sg * (ex - 0.55 * R), ez - dz * R), (sg * (ex + 1.25 * R), ez - (dz - 0.12) * R), n), _taper(n, 0.14 * R))
    out.append(d.done("Mark_cheek-bars", mat("skin_ochre")))
    # three fine cuts on each cheek, healed pale
    d = _Decal(hb, 0.0009)
    n = 5
    for sg in (1.0, -1.0):
        for k in range(3):
            x0 = sg * (ex + (0.5 + 0.38 * k) * R)
            d.stroke(_line((x0, ez - 1.75 * R), (x0 + sg * 0.12 * R, ez - 2.5 * R), n), _taper(n, 0.07 * R))
    out.append(d.done("Mark_cheek-cuts", mat("skin_scar")))
    # red at the outer corner of each eye
    d = _Decal(hb, 0.0006)
    n = 6
    for sg in (1.0, -1.0):
        d.stroke(_line((sg * (ex + 0.95 * R), ez + 0.05 * R), (sg * (ex + 1.95 * R), ez + 0.5 * R), n), [0.2 * R * (1.0 - i / (n - 0.5)) + 0.02 * R for i in range(n)])
    out.append(d.done("Mark_eye-red", mat("skin_red")))
    # a white line down the brow and the nose
    d = _Decal(hb)
    n = 9
    d.stroke(_line((0.0, ez + 3.0 * R), (0.0, ez - 1.5 * R), n), [0.12 * R] * n)
    out.append(d.done("Mark_brow-line", mat("skin_white")))
    return out
