"""WILDLINE head: a skull from three silhouettes (the profile, the front, the back) blended
round the head, then the features. v3 (the owner: faces first): the eyes are set into the
sockets with eyelids that wrap the ball, lashes and a pupil; the brows are hair; the nose and
the mouth are surface patches that follow the skull (a bridge that reads in profile, a tip,
the wings; lips with a cupid's bow and corners set into the cheeks); the hair is cut along
the hairline rather than stepped. The home's face parameters and the sex reshape it. Built
for the body kit, at the top of the anatomy's neck.

World space is Blender's: Z up, the face at -Y. The head is 0.32 tall (7.5 heads in 2.4),
crown to chin; the eyes sit at its middle, as on a real skull.
"""
import math

import bpy
import bmesh
from mathutils import Vector
from mathutils.kdtree import KDTree

import people_kit as pk

HEAD_HEIGHT = 0.32


def _interp(curve, e):
    """Linear interpolation of (elevation_degrees, radius) pairs, clamped."""
    if e <= curve[0][0]:
        return curve[0][1]
    if e >= curve[-1][0]:
        return curve[-1][1]
    for (e0, r0), (e1, r1) in zip(curve, curve[1:]):
        if e0 <= e <= e1:
            t = (e - e0) / (e1 - e0)
            t = t * t * (3 - 2 * t)
            return r0 + (r1 - r0) * t
    return curve[-1][1]


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def silhouettes(sex, fp):
    """The three radius curves (elevation from the head's centre, in degrees, bottom to top),
    in units of the head's height. The centre is the skull's middle: the eyes at its height,
    the face 0.39 ahead of it, the occiput 0.39 behind, the sides 0.36 out, the crown 0.5 up,
    the chin 0.5 down and a little forward (a real skull's proportions)."""
    fem = sex == "f"
    jaw = fp("jaw")
    cheek = fp("cheek")
    brow = fp("brow")
    front = [
        (-90, 0.42), (-77, 0.46), (-62, 0.56 * (0.96 if fem else 1.0)),  # under the jaw, the chin's point
        (-50, 0.53), (-38, 0.49), (-30, 0.465),                          # the chin's front, the lower lip
        (-22, 0.44), (-12, 0.41), (0, 0.39),                             # the upper lip, the nose's base, the eyes
        (14, 0.40 + 0.015 * brow), (28, 0.42), (43, 0.44),               # the brow, the forehead
        (62, 0.47), (78, 0.49), (90, 0.50),                              # the crown
    ]
    side = [
        (-90, 0.42), (-75, 0.46), (-58, 0.47 * (0.94 if fem else jaw)),  # under the jaw, the jaw's angle
        (-40, 0.42 * (0.95 if fem else jaw)), (-25, 0.385), (-12, 0.37),  # the jaw, the cheek
        (0, 0.36 * cheek), (15, 0.37), (30, 0.39), (49, 0.45),           # the ear's level, the temple, the skull's side
        (70, 0.49), (90, 0.50),
    ]
    back = [
        (-90, 0.42), (-77, 0.45), (-62, 0.42), (-50, 0.39), (-35, 0.38), # the nape
        (-18, 0.385), (-5, 0.39), (7, 0.395), (22, 0.41), (36, 0.43),    # the occiput
        (55, 0.46), (75, 0.49), (90, 0.50),                              # the crown
    ]
    return front, side, back


def skull(centre, sex, fp, segments=96, rings=66):
    """A sphere reshaped by the silhouettes: at each direction the radius blends the front,
    side and back curves by the azimuth."""
    front, side, back = silhouettes(sex, fp)
    H = HEAD_HEIGHT * fp("headLength")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        e = math.degrees(math.asin(max(-1.0, min(1.0, d.z))))
        # the azimuth from the front (-Y): 0 at the face, 90 at the side, 180 at the back
        a = math.degrees(math.atan2(abs(d.x), -d.y))
        rf, rs, rb = _interp(front, e), _interp(side, e), _interp(back, e)
        if a <= 90:
            t = a / 90.0
            w = math.sin(t * math.pi / 2) ** 2
            r = rf * (1 - w) + rs * w
        else:
            t = (a - 90) / 90.0
            w = math.sin(t * math.pi / 2) ** 2
            r = rs * (1 - w) + rb * w
        v.co = centre + d * (r * H)
    return bm


def carving(centre, sex, fp):
    """Displacement points on the skull, about `centre` (the skull's middle; the face plane
    is 0.39 of the height ahead of it, the eyes at its height)."""
    H = HEAD_HEIGHT
    fem = sex == "f"
    P = []

    def pt(off, r, s, aniso=(1, 1, 1)):
        P.append((centre + Vector(off) * H, r * H, s * H, Vector(aniso)))

    for sg in (1, -1):
        pt((sg * 0.17, -0.37, 0.02), 0.16, -0.06, (1.3, 1, 0.85))            # eye socket: the lids fill it
        pt((sg * 0.17, -0.38, -0.1), 0.09, 0.012, (1.3, 1, 0.7))             # the cheek under the eye
        pt((sg * 0.3, -0.26, -0.07), 0.15, 0.03 * fp("cheek"), (1, 1, 1))    # cheekbone
        pt((sg * 0.33, -0.08, 0.26), 0.17, -0.025, (1, 1, 1.3))              # temple
        pt((sg * 0.27, 0.02, -0.4), 0.15, 0.025 * (fp("jaw") - 0.4), (1, 1, 1))  # the jaw's angle
        pt((sg * 0.21, -0.33, -0.2), 0.12, -0.02, (1, 1, 1.2))               # the cheek's hollow
        pt((sg * 0.09, -0.42, -0.16), 0.08, -0.012, (1.4, 1, 0.6))           # the nasolabial fold
        pt((sg * 0.09, -0.4, 0.1), 0.08, 0.012 * fp("brow"), (1.4, 1, 0.5))  # the brow's bone over each eye
    pt((0, -0.4, 0.14), 0.2, 0.02 * fp("brow"), (2.2, 1, 0.5))               # the brow ridge
    pt((0, -0.33, -0.45), 0.12, 0.03 * (0.85 if fem else 1.0), (1, 1, 1))    # the chin
    pt((0, -0.41, -0.34), 0.07, -0.02, (1.6, 1, 0.5))                        # under the lower lip
    pt((0, -0.4, 0.04), 0.07, -0.014, (1.1, 1, 0.8))                         # between the eyes, the root of the nose
    pt((0, -0.42, -0.12), 0.06, -0.012, (1.0, 1, 0.8))                       # the philtrum
    return P


def carve(ob, points):
    me = ob.data
    normals = [n.vector.copy() for n in me.vertex_normals]
    for v, n in zip(me.vertices, normals):
        p = ob.matrix_world @ v.co
        d = 0.0
        for c, r, s, a in points:
            q = p - c
            q = Vector((q.x / a.x, q.y / a.y, q.z / a.z))
            t = q.length / r
            if t < 1.0:
                w = 1.0 - t * t
                d += s * w * w
        if d != 0.0:
            v.co = v.co + n * d
    me.update()


def _ob(name, bm, mat):
    ob = pk._bm_object(name, bm, mat)
    pk._smooth(ob)
    return ob


def _ellipsoid(name, c, rx, ry, rz, mat, u=12, v=8, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.scale(bm, vec=(rx, ry, rz), verts=bm.verts)
    if rot is not None:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return _ob(name, bm, mat)


class Surface:
    """The skull's surface, to set pieces on: the nearest points' position and normal."""

    def __init__(self, ob):
        me = ob.data
        M = ob.matrix_world
        self.pos = [M @ v.co for v in me.vertices]
        self.nrm = [n.vector.copy() for n in me.vertex_normals]
        self.kd = KDTree(len(self.pos))
        for i, p in enumerate(self.pos):
            self.kd.insert(p, i)
        self.kd.balance()

    def at(self, p, k=5):
        found = self.kd.find_n(p, k)
        tw = 0.0
        pos = Vector((0, 0, 0))
        nrm = Vector((0, 0, 0))
        for co, i, d in found:
            w = 1.0 / (d + 1e-4)
            tw += w
            pos += co * w
            nrm += self.nrm[i] * w
        return pos / tw, nrm.normalized()

    def on(self, p, lift=0.0):
        """The point of the surface nearest p, lifted along the normal."""
        pos, n = self.at(p)
        return pos + n * lift, n


def _patch(name, surf, xs, zs, origin, height, mats, material_of=None):
    """A heightfield patch laid on the skull: a grid over (x, z) about `origin` (the face
    plane), each vertex the surface's point there lifted by height(x, z) along its normal.
    The border's height is zero, so the patch melts into the skin."""
    bm = bmesh.new()
    grid = []
    for z in zs:
        row = []
        for x in xs:
            p = origin + Vector((x, 0, z))
            pos, n = surf.on(p, 0.0012 + height(x, z))
            row.append(bm.verts.new(pos))
        grid.append(row)
    faces = []
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            faces.append((f, (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # the normals face out of the head (-Y at the face): flip if they point in
    out = Vector((0, -1, 0))
    if sum(f.normal.dot(out) for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    for m in mats:
        me.materials.append(m)
    if material_of is not None:
        for poly, (f, cx, cz) in zip(me.polygons, faces):
            poly.material_index = material_of(cx, cz)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    pk._smooth(ob)
    return ob


def _bump(s, p=1.5):
    s = abs(s)
    return (1.0 - s * s) ** p if s < 1.0 else 0.0


def _eyelids(name, ec, R, Rball, open_w, up, low, tilt, sg, mat):
    """A shell about the eyeball with an almond opening: the lids. The opening's rim turns
    in to the ball, so the lid has an edge. `up` and `low` are the opening's half-heights,
    `open_w` its half-width, `tilt` lifts the outer corner."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=18, radius=R)
    # the sphere's poles along X, so the almond's corners fall on the dense rows
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "Y"), verts=bm.verts)

    def inside(co):
        if co.y > -0.1 * R:
            return False
        s = co.x / open_w
        if abs(s) >= 1.0:
            return False
        lid_up = up * (1 - s * s) ** 0.55 + tilt * (s * sg)
        lid_low = -low * (1 - s * s) ** 0.7 + tilt * (s * sg) * 0.6
        return lid_low < co.z < lid_up

    kill = [f for f in bm.faces if all(inside(v.co) for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    rim = [e for e in bm.edges if e.is_boundary]
    if rim:
        geom = bmesh.ops.extrude_edge_only(bm, edges=rim)
        for v in [g for g in geom["geom"] if isinstance(g, bmesh.types.BMVert)]:
            v.co = v.co.normalized() * (Rball * 0.98)
    bmesh.ops.translate(bm, vec=ec, verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _ob(name, bm, mat)


def features(skull_ob, centre, sex, fp, mats):
    """The eyes with lids, lashes and pupils, the brows, the nose, the mouth, the ears: pieces
    about the skull. The face plane is at centre.y - 0.39 H; the eyes at centre.z."""
    H = HEAD_HEIGHT
    fem = sex == "f"
    skin, white, iris = mats["skin"], mats["eye_white"], mats["iris"]
    hair = mats.get("hair", skin)
    lips_mat = mats.get("lips", skin)
    pupil = mats.get("pupil", iris)
    surf = Surface(skull_ob)
    out = []
    face = centre.y - 0.39 * H
    # the eyes: the ball set into the socket, the iris and pupil on its front, the lids a
    # shell round it with an almond opening (the upper lid rests on the top of the iris)
    Rb = 0.056 * H
    for sg in (1, -1):
        side = "l" if sg > 0 else "r"
        ex = sg * 0.17 * H
        ec = Vector((centre.x + ex, face + 0.066 * H, centre.z + 0.015 * H))
        out.append(_ellipsoid("Eye_%s" % side, ec, Rb, Rb, Rb, white, u=20, v=12))
        out.append(_ellipsoid("Iris_%s" % side, ec + Vector((0, -0.05 * H, 0)), 0.027 * H, 0.009 * H, 0.027 * H, iris, u=16, v=8))
        out.append(_ellipsoid("Pupil_%s" % side, ec + Vector((0, -0.0565 * H, 0)), 0.012 * H, 0.004 * H, 0.012 * H, pupil, u=12, v=6))
        open_w = 0.08 * H
        up, low = (0.032 if fem else 0.03) * H, 0.022 * H
        out.append(_eyelids("Lid_%s" % side, ec, 0.064 * H, Rb, open_w, up, low, 0.006 * H, sg, skin))
        # lashes: a dark line along the upper lid's edge
        pts = []
        n = 11
        for k in range(n):
            s = -0.95 + 1.9 * k / (n - 1.0)
            z = up * (1 - s * s) ** 0.55 + 0.006 * H * s * sg
            x = s * open_w
            y = -math.sqrt(max(1e-6, (0.0645 * H) ** 2 - x * x - z * z))
            pts.append(ec + Vector((x, y, z + 0.002 * H)))
        out.append(_ob("Lash_%s" % side, pk._tube_bm(pts, [0.0035 * H * (0.5 + 0.5 * math.sin(k / (n - 1.0) * math.pi)) for k in range(n)], segments=5), hair))
        # the brow: a hair stroke on the brow's bone, thick at the root, arched at two thirds
        pts = []
        n = 12
        for k in range(n):
            t = k / (n - 1.0)
            x = ex + sg * (-0.09 + 0.26 * t) * H
            z = centre.z + (0.085 + 0.045 * math.sin(t ** 0.9 * math.pi) - 0.01 * t) * H
            pos, nrm = surf.on(Vector((centre.x + x, face, z)), 0.005 * H)
            pts.append(pos)
        rad = [0.011 * H * fp("brow") * (1.0 - 0.45 * (k / (n - 1.0)) ** 2) for k in range(n)]
        out.append(_ob("Brow_%s" % side, pk._tube_bm(pts, rad, segments=6), hair))
    # the nose: a patch on the face from between the eyes to under the tip. The ridge rises
    # from the root to the tip and narrows at the middle; the tip is a bulb; the wings flare
    nl, nw = fp("nose"), fp("noseWidth")
    ridge = [(0.1, 0.0), (0.06, 0.016), (0.02, 0.036), (-0.04, 0.058), (-0.1, 0.082), (-0.15, 0.105), (-0.185, 0.118), (-0.21, 0.085), (-0.235, 0.03), (-0.25, 0.0)]
    width = [(0.1, 0.055), (0.03, 0.042), (-0.06, 0.04), (-0.13, 0.05), (-0.185, 0.064), (-0.22, 0.06), (-0.25, 0.05)]

    def nose_h(x, z):
        u = z / (H * nl)
        xw = x / (H * nw)
        p = _interp(ridge, u) * H
        w = _interp(width, u)
        h = p * _bump(xw / w, 1.3)
        # the wings, either side of the tip, a little behind it
        for sg in (1, -1):
            dx, dz = (xw - sg * 0.072) / 0.045, (u + 0.18) / 0.05
            h = max(h, 0.075 * H * _bump(math.sqrt(dx * dx + dz * dz), 1.6))
        # the nostrils' shadow under the wings
        for sg in (1, -1):
            dx, dz = (xw - sg * 0.045) / 0.028, (u + 0.215) / 0.025
            h -= 0.01 * H * _bump(math.sqrt(dx * dx + dz * dz), 1.5)
        return max(0.0, h)

    xs = [(-0.14 + 0.28 * i / 27.0) * H * nw for i in range(28)]
    zs = [(-0.255 + 0.36 * j / 35.0) * H * nl for j in range(36)]
    out.append(_patch("Nose", surf, xs, zs, Vector((centre.x, face, centre.z)), nose_h, [skin]))
    # the mouth: a patch with two lip mounds either side of the mouth's line, the upper with a
    # cupid's bow, both tapering into the corners, the corners set a little into the cheeks
    lf = fp("lips") * (1.12 if fem else 1.0)
    half = 0.125 * H
    zm0 = -0.262 * H

    def zline(x):
        return zm0 - 0.012 * H * (x / half) ** 2

    def mouth_h(x, z):
        s = x / half
        if abs(s) >= 1.0:
            # the corner's dimple just past the lips
            d = math.sqrt(((abs(s) - 1.0) * half / (0.03 * H)) ** 2 + ((z - zline(x)) / (0.02 * H)) ** 2)
            return -0.005 * H * _bump(d, 1.2)
        taper = (1 - s * s) ** 0.6
        zm = zline(x)
        bow = 1.0 - 0.3 * _bump(s / 0.22, 1.0)
        up_t = 0.032 * H * bow * lf
        low_t = 0.04 * H * lf
        h = 0.0
        if z >= zm:
            h = 0.013 * H * lf * taper * _bump((z - zm) / up_t - 0.0, 1.0) * (0.75 + 0.25 * bow)
        else:
            h = 0.016 * H * lf * taper * _bump((zm - z) / low_t, 1.0)
        # the mouth's line
        h -= 0.006 * H * _bump((z - zm) / (0.0045 * H), 1.0) * (0.5 + 0.5 * taper)
        return h

    def mouth_mat(cx, cz):
        s = cx / half
        if abs(s) >= 0.98:
            return 0
        zm = zline(cx)
        if zm - 0.034 * H * lf < cz < zm + 0.028 * H * lf * (1.0 - 0.3 * _bump(s / 0.22, 1.0)):
            return 1
        return 0

    xs = [(-0.17 + 0.34 * i / 33.0) * H for i in range(34)]
    zs = [(-0.335 + 0.135 * j / 21.0) * H for j in range(22)]
    out.append(_patch("Mouth", surf, xs, zs, Vector((centre.x, face, centre.z)), mouth_h, [skin, lips_mat], mouth_mat))
    # the ears: a helix round the back from the top, a concha, a lobe; flat against the side
    es = fp("ears")
    for sg in (1, -1):
        side = "l" if sg > 0 else "r"
        ec = Vector((centre.x + sg * 0.355 * H, centre.y + 0.04 * H, centre.z - 0.03 * H))
        pts = []
        n = 12
        for k in range(n):
            t = k / (n - 1.0)
            a = math.pi * (0.95 - 0.95 * t)   # from the top-front over the back down to the lobe
            pts.append(ec + Vector((sg * 0.02 * H * math.sin(a), 0.07 * H * es * math.cos(a), 0.1 * H * es * math.sin(a))))
        out.append(_ob("Ear_%s" % side, pk._tube_bm(pts, [0.015 * H * es] * n, segments=6), skin))
        out.append(_ellipsoid("Concha_%s" % side, ec, 0.012 * H, 0.05 * H * es, 0.07 * H * es, skin))
        out.append(_ellipsoid("Earlobe_%s" % side, ec + Vector((0, -0.01 * H, -0.09 * H * es)), 0.016 * H, 0.03 * H * es, 0.028 * H * es, skin))
    return out


def _loft_ob(name, rings, mat, segments=12):
    bm = bmesh.new()
    loops = []
    for c, u, v in rings:
        ring = []
        for k in range(segments):
            a = 2 * math.pi * k / segments
            ring.append(bm.verts.new(c + u * math.cos(a) + v * math.sin(a)))
        loops.append(ring)
    for a_, b_ in zip(loops, loops[1:]):
        for k in range(segments):
            bm.faces.new((a_[k], a_[(k + 1) % segments], b_[(k + 1) % segments], b_[k]))
    bm.faces.new(loops[0][::-1])
    bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _ob(name, bm, mat)


def build_head(chin_z, sex, face, mats):
    """The whole head, chin at chin_z on the body's axis: {name: object}. The skull is one
    object named Head (skinned to the head bone by the kit); the rest hang from it."""
    fp = lambda k: float((face or {}).get(k, 1.0))  # noqa: E731
    H = HEAD_HEIGHT * fp("headLength")
    centre = Vector((0, 0.04, chin_z + 0.5 * H))
    bm = skull(centre, sex, fp)
    ob = _ob("Head", bm, mats["skin"])
    carve(ob, carving(centre, sex, fp))
    pieces = features(ob, centre, sex, fp, mats)
    return ob, pieces, centre


# ======================================================================================
# Hair, from the skull itself: a cap is the skull's own surface above the hairline, cut
# along it and pushed out along its normals (thin at the line, thick at the crown), so it
# fits the carved head with a clean edge; the falls (long, braid, bun, tail) are tubes from
# the cap. Styles: crop, long, braid, knot, tail; beards: short, full (the jaw's surface).
# ======================================================================================

HAIR_STYLES = ["crop", "long", "braid", "knot", "tail"]
BEARD_STYLES = ["short", "full"]


def _shell(skull_ob, name, field, thickness, mat):
    """The part of the skull where field(world_position, world_normal) > 0, cut along the
    zero line, as its own shell pushed out by thickness(field_value)."""
    me = skull_ob.data
    normals = [n.vector.copy() for n in me.vertex_normals]
    M = skull_ob.matrix_world
    P = [M @ v.co for v in me.vertices]
    F = [field(P[i], normals[i]) for i in range(len(P))]
    bm = bmesh.new()
    made = {}
    source = {}

    def vert_of(i):
        if i not in made:
            made[i] = bm.verts.new(P[i] + normals[i] * thickness(F[i]))
            source[made[i]] = P[i]
        return made[i]

    crossing = {}

    def cross(i, j):
        key = (min(i, j), max(i, j))
        if key not in crossing:
            t = F[i] / (F[i] - F[j])
            p = P[i].lerp(P[j], t)
            n = normals[i].lerp(normals[j], t).normalized()
            v = bm.verts.new(p + n * thickness(0.0))
            source[v] = p
            crossing[key] = v
        return crossing[key]

    for poly in me.polygons:
        idx = list(poly.vertices)
        if all(F[i] <= 0 for i in idx):
            continue
        ring = []
        for a, b in zip(idx, idx[1:] + idx[:1]):
            if F[a] > 0:
                ring.append(vert_of(a))
            if (F[a] > 0) != (F[b] > 0):
                ring.append(cross(a, b))
        if len(ring) >= 3:
            try:
                bm.faces.new(ring)
            except ValueError:
                pass
    # the rim: a skirt down to the skull, so the cap has an edge rather than a floating sheet
    rim = [e for e in bm.edges if e.is_boundary]
    if rim:
        geom = bmesh.ops.extrude_edge_only(bm, edges=rim)
        for v in [g for g in geom["geom"] if isinstance(g, bmesh.types.BMVert)]:
            for e in v.link_edges:
                o = e.other_vert(v)
                if o in source:
                    v.co = source[o]
                    break
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me2 = bpy.data.meshes.new(name)
    bm.to_mesh(me2)
    bm.free()
    ob = bpy.data.objects.new(name, me2)
    bpy.context.collection.objects.link(ob)
    me2.materials.append(mat)
    pk._smooth(ob)
    return ob


def hair(skull_ob, centre, sex, fp, mat_hair):
    """Every style on the head, hung from the head bone by the kit: the caps and the falls."""
    H = HEAD_HEIGHT * fp("headLength")
    out = []
    face = centre.y - 0.39 * H
    hairline_front = centre.z + 0.3 * H     # above the brow at the front
    hairline_side = centre.z + 0.06 * H     # over the ears at the sides
    nape = centre.z - 0.2 * H               # down the nape at the back

    def above_hairline(p, n):
        # the hairline runs from high at the brow, over the ear, down to the nape; the
        # temples recede a little either side of the brow
        a = math.atan2(abs(p.x - centre.x), -(p.y - centre.y)) / math.pi   # 0 face .. 1 back
        line = hairline_front * (1 - a) ** 2 + hairline_side * 2 * a * (1 - a) + nape * a * a
        line += 0.03 * H * _bump((a - 0.22) / 0.12, 1.0)
        f = p.z - line
        # not down the face
        if n.y < -0.6:
            f = min(f, (p.z - (centre.z + 0.32 * H)))
        return f

    def cap_thickness(f):
        return 0.004 + 0.018 * _smooth(f / (0.09 * H))

    for style in HAIR_STYLES:
        out.append(_shell(skull_ob, "Hair_%s_cap" % style, above_hairline, cap_thickness, mat_hair))
    back = centre.y + 0.39 * H
    # long: a fall down the back and the sides to the shoulder blades
    rings = []
    for i, (dz, w, d) in enumerate(((0.25, 0.36, 0.42), (0.0, 0.38, 0.4), (-0.35, 0.4, 0.3), (-0.8, 0.42, 0.22), (-1.2, 0.44, 0.16))):
        c = Vector((centre.x, centre.y + 0.08 * H + (0.42 - d) * 0.5 * H * (1 if i > 0 else 0), centre.z + dz * H))
        rings.append((c, Vector((w * 0.5 * H, 0, 0)), Vector((0, d * 0.5 * H, 0))))
    out.append(_loft_ob("Hair_long_fall", rings, mat_hair, segments=14))
    # braid: a plait from the nape, thick and thin by turns
    n = 10
    pts = [Vector((centre.x, back - 0.02 * H + 0.02 * H * math.sin(i / 1.5), centre.z - 0.25 * H - (i / (n - 1.0)) * 1.1 * H)) for i in range(n)]
    rad = [0.07 * H * (1.0 if i % 2 == 0 else 0.75) * (1.0 - 0.4 * i / (n - 1.0)) for i in range(n)]
    out.append(_ob("Hair_braid_fall", pk._tube_bm(pts, rad, segments=8), mat_hair))
    # knot: a bun high on the back of the head
    out.append(_ellipsoid("Hair_knot_fall", Vector((centre.x, back - 0.08 * H, centre.z + 0.3 * H)), 0.16 * H, 0.14 * H, 0.12 * H, mat_hair))
    # tail: a high tail that swings out and down
    pts = [Vector((centre.x, back - 0.1 * H + 0.3 * H * math.sin(math.pi * i / 9.0), centre.z + 0.25 * H - (i / 8.0) * 0.9 * H)) for i in range(9)]
    rad = [0.09 * H * (1.0 - 0.6 * i / 8.0) for i in range(9)]
    out.append(_ob("Hair_tail_fall", pk._tube_bm(pts, rad, segments=8), mat_hair))
    # beards: the jaw's own surface, short along the jaw, full down to the collar
    chin_z = centre.z - 0.5 * H
    for style, depth in (("short", 0.1), ("full", 0.0)):
        def on_jaw(p, n, depth=depth):
            low = min(centre.z - 0.22 * H - p.z, p.z - (chin_z - 0.02 * H))
            frontish = 0.1 * H - (p.y - centre.y)
            not_mouth = max(abs(p.x - centre.x) - 0.14 * H, (centre.z - 0.33 * H) - p.z)
            cut = max(centre.z - (0.28 + depth) * H - p.z, abs(p.x - centre.x) - 0.12 * H)
            return min(low, frontish, not_mouth, cut)
        thick = 0.012 if style == "short" else 0.02
        beard = _shell(skull_ob, "Beard_%s" % style, on_jaw, lambda f, t=thick: 0.003 + (t - 0.003) * _smooth(f / (0.05 * H)), mat_hair)
        out.append(beard)
    # the full beard hangs below the chin
    pts = [Vector((centre.x, face + 0.08 * H, chin_z - 0.02 * H)), Vector((centre.x, face + 0.05 * H, chin_z - 0.2 * H)), Vector((centre.x, face + 0.04 * H, chin_z - 0.38 * H))]
    hang = _ob("Beard_full_hang", pk._tube_bm(pts, [0.12 * H, 0.1 * H, 0.05 * H], segments=10), mat_hair)
    out.append(hang)
    return out
