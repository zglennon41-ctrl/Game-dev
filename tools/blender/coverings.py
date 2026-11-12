"""WILDLINE coverings: cloth worn over the hair, for any head of any home
(docs/representation-plan.md, "Hair and head coverings").

A covering is not one home's headgear: it is a choice every person has (data/creation.json,
look.coverings), in their home's own cloth. Each is laid on the head it is for: rays are cast
in at the head from all round, ring by ring from the crown down, so the cloth tents over the
ears and follows the skull, the jaw and the neck; it is lifted off the skin, wound or folded,
and given a thickness. Pieces are named Cover_<id> and hang from the head bone; one that
comes down over the jaw and the neck takes the face's and the builds' shape keys from the
skin under it (faces.py, carry).

  wrap    cloth wound over the hair and tucked: above the ears, a knot at the front
  scarf   a headscarf: over the hair, the ears and the neck, close about the face

World space is Blender's: Z up, the face at -Y, the character's left at +X.
"""
import json
import math
import os

import bmesh
from mathutils import Vector

import people_kit as pk
import hair as hr
import wardrobe

N = 30      # points round the head


def spec():
    """The coverings the creator offers (data/creation.json, look.coverings)."""
    try:
        return json.load(open(os.path.join(pk.ROOT, "data", "creation.json")))["look"].get("coverings", [])
    except (KeyError, OSError):
        return []


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _lay(hb, c, H, rows, z_of, lift, axis_y, skip=None, reach=None, top=0.0):
    """Cloth laid on the head: rows[i] is how far down a ring is (0 at the crown, 1 at the
    hem), z_of(theta, u) its height at an angle (theta 0 at the face, +-pi at the back),
    lift(theta, z) how far it stands off the skin, axis_y(z) where the head's (or the neck's)
    middle is at a height. skip(theta, i) leaves a face out (the opening for the face);
    reach(z) holds the cloth in (the neck's does not wander out over the shoulders).
    Returns the mesh as a bmesh."""
    bvh = hb.bvh("all", "fit")
    R0 = 0.95 * H
    thetas = [-math.pi + 2 * math.pi * (j + 0.5) / N for j in range(N)]
    rad, zs = [], []
    for u in rows:
        rr, zz = [], []
        for th in thetas:
            z = z_of(th, u)
            d = Vector((math.sin(th), -math.cos(th), 0.0))
            axis = Vector((c.x, axis_y(z), z))
            hit = bvh.ray_cast(axis + d * R0, -d, R0)[0]
            r = (hit - axis).length if hit is not None else 0.0
            if reach is not None:
                r = min(r, reach(z))
            rr.append(r)
            zz.append(z)
        rad.append(rr)
        zs.append(zz)
    # cloth does not follow every hollow: each point is at least the mean of its neighbours
    for _ in range(2):
        for rr in rad:
            blurred = [0.25 * rr[j - 1] + 0.5 * rr[j] + 0.25 * rr[(j + 1) % N] for j in range(N)]
            for j in range(N):
                rr[j] = max(rr[j], blurred[j])
    bm = bmesh.new()
    grid = []
    for i, u in enumerate(rows):
        ring = []
        for j, th in enumerate(thetas):
            z = zs[i][j]
            d = Vector((math.sin(th), -math.cos(th), 0.0))
            axis = Vector((c.x, axis_y(z), z))
            p = axis + d * rad[i][j]
            out = (p - Vector((c.x, axis_y(c.z), c.z))).normalized() if z > c.z else d
            ring.append(bm.verts.new(p + out * lift(th, z)))
        grid.append(ring)
    faces = []
    for i in range(len(rows) - 1):
        for j in range(N):
            k = (j + 1) % N
            mid = 0.5 * (thetas[j] + thetas[k]) if k else math.pi
            if skip is not None and skip(mid, i):
                continue
            faces.append(bm.faces.new((grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j])))
    apex = bm.verts.new(Vector((c.x, axis_y(hb.crown_z), hb.crown_z + top)))
    for j in range(N):
        faces.append(bm.faces.new((apex, grid[0][(j + 1) % N], grid[0][j])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _wrap(hb, c, H):
    """Cloth wound over the hair: from above the brow, over the top of the ears, to the nape;
    full at the crown where the hair is gathered under it, and knotted at the front."""
    crown = hb.crown_z - 0.02 * H

    def line(th):
        a = abs(th) / math.pi
        return (c.z + 0.31 * H) * (1 - a) ** 2 + (c.z + 0.07 * H) * 2 * a * (1 - a) + (c.z - 0.3 * H) * a * a

    def z_of(th, u):
        return crown - (crown - line(th)) * u

    def lift(th, z):
        full = 0.034 * H + 0.075 * H * _smooth((z - (c.z + 0.2 * H)) / (0.28 * H))
        wound = 1.0 + 0.2 * math.sin(2 * math.pi * (z - c.z) / (0.12 * H) + 2.0 * th)
        return full * wound
    rows = [0.12, 0.26, 0.4, 0.53, 0.65, 0.76, 0.86, 0.94, 1.0]
    bm = _lay(hb, c, H, rows, z_of, lift, lambda z: c.y, top=0.1 * H)
    # the knot: the two ends tucked over one another above the brow, a little to one side
    knot = bmesh.new()
    kz = c.z + 0.4 * H
    hit = hb.bvh("all", "fit").ray_cast(Vector((c.x + 0.06 * H, c.y - H, kz)), Vector((0, 1, 0)), H)[0]
    k = Vector((c.x + 0.06 * H, (hit.y if hit is not None else c.y - 0.3 * H) - 0.05 * H, kz))
    hr._ball(knot, k, 0.085 * H, 0.05 * H, 0.06 * H)
    hr._ball(knot, k + Vector((-0.1 * H, 0.02 * H, 0.03 * H)), 0.07 * H, 0.04 * H, 0.04 * H)
    hr._ball(knot, k + Vector((0.085 * H, 0.035 * H, -0.03 * H)), 0.06 * H, 0.035 * H, 0.045 * H)
    return [(bm, 0), (knot, 0)]


def _scarf(hb, c, H):
    """A headscarf: over the hair, the ears and the neck, close about the face from the brow
    to under the chin, and loose where it gathers at the throat."""
    crown = hb.crown_z - 0.02 * H
    base = c.z - 0.7 * H
    chin = hb.chin_z
    neck_y = float(hb.humans["fit"].joint("joint-neck")[1])
    wide = 0.225 * math.pi      # half the face's opening, as an angle about the head

    def brow(th):
        t = min(1.0, abs(th) / wide)
        return c.z + 0.3 * H - 0.07 * H * t * t

    def jaw(th):
        t = min(1.0, abs(th) / wide)
        return chin - 0.035 * H + 0.2 * H * t * t

    def z_of(th, u):
        if u <= 0.5:
            return crown - (crown - brow(th)) * (u / 0.5)
        if u <= 0.6:
            return brow(th) - (brow(th) - jaw(th)) * ((u - 0.5) / 0.1)
        return jaw(th) - (jaw(th) - base) * ((u - 0.6) / 0.4)

    def axis_y(z):
        return c.y + (neck_y - c.y) * _smooth((c.z - 0.3 * H - z) / (0.3 * H))

    def lift(th, z):
        loose = _smooth((c.z - 0.4 * H - z) / (0.2 * H))
        folds = 1.0 + 0.28 * loose * math.sin(9.0 * th + 0.7)
        # the ears stand out between the rays that find the head: the cloth clears them
        ear = hr._bump((abs(th) / math.pi - 0.5) / 0.2) * hr._bump((z - (c.z - 0.02 * H)) / (0.2 * H))
        return (0.026 * H + 0.04 * H * loose) * folds + 0.045 * H * ear

    def reach(z):
        return 0.6 * H if z > c.z - 0.5 * H else 0.3 * H
    rows = [0.07, 0.15, 0.24, 0.33, 0.42, 0.5, 0.52, 0.54, 0.56, 0.58, 0.6, 0.68, 0.76, 0.84, 0.92, 1.0]
    first, last = rows.index(0.5), rows.index(0.6)      # the rings from the brow to the jaw: open before the face, closed over the ears
    bm = _lay(hb, c, H, rows, z_of, lift, axis_y, skip=lambda th, i: first <= i < last and abs(th) < wide, reach=reach, top=0.02 * H)
    return [(bm, 0)]


SHAPES = {"wrap": _wrap, "scarf": _scarf}


def coverings(hb, centre):
    """Every covering the data names, on this head: objects named Cover_<id>, in the home's
    cloth (its first colour, the knot or the band in its second)."""
    import body_kit as bk
    body = hb.body
    D = bk.home_dress(body.home) or {}
    colors = list(D.get("colors", {}))
    chord = [n for n in D.get("chordColors", []) if n in colors] or colors
    out = []
    for cv in spec():
        make = SHAPES.get(cv.get("shape", cv["id"]))
        if make is None:
            continue
        names = [cv.get("color") if cv.get("color") in colors else (chord[0] if chord else None),
                 cv.get("trim") if cv.get("trim") in colors else (chord[1] if len(chord) > 1 else (chord[0] if chord else None))]
        mats = [wardrobe.material(body.home, D, n) if n else body.mats["tunic"] for n in names]
        ob = wardrobe._merge("Cover_%s" % cv["id"], make(hb, centre, hb.head_h))
        wardrobe._slots(ob, mats)
        if cv.get("follows", False):        # it lies on the jaw and the neck: it goes where they go
            hb.visage.carry(ob)
        out.append(ob)
    return out
