"""WILDLINE head: a skull from three silhouettes (the profile, the front, the back) blended
round the head, then the features: carved eye sockets with eyelids and eyeballs, a nose with
a bridge, a tip and nostril wings, lips with a cupid's bow, ears with a helix and a lobe, the
chin and the jaw's corners, cheekbones and temples. The home's face parameters and the sex
reshape it. Built for the body kit, at the top of the anatomy's neck.

World space is Blender's: Z up, the face at -Y. The head is 0.32 tall (7.5 heads in 2.4),
crown to chin; the eyes sit at its middle, as on a real skull.
"""
import math

import bpy
import bmesh
from mathutils import Vector

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
        (-90, 0.42), (-77, 0.46), (-62, 0.57 * (0.96 if fem else 1.0)),  # under the jaw, the chin's point
        (-50, 0.54), (-38, 0.49), (-30, 0.47),                           # the chin's front, the lower lip
        (-22, 0.44), (-12, 0.41), (0, 0.39),                             # the upper lip, the nose's base, the eyes
        (14, 0.40 + 0.015 * brow), (28, 0.42), (43, 0.44),               # the brow, the forehead
        (62, 0.47), (78, 0.49), (90, 0.50),                              # the crown
    ]
    side = [
        (-90, 0.42), (-75, 0.46), (-58, 0.44 * (0.94 if fem else jaw)),  # under the jaw, the jaw's angle
        (-40, 0.39 * (0.95 if fem else jaw)), (-25, 0.37), (-12, 0.36),  # the jaw, the cheek
        (0, 0.36 * cheek), (15, 0.37), (30, 0.39), (49, 0.45),           # the ear's level, the temple, the skull's side
        (70, 0.49), (90, 0.50),
    ]
    back = [
        (-90, 0.42), (-77, 0.45), (-62, 0.42), (-50, 0.39), (-35, 0.38), # the nape
        (-18, 0.385), (-5, 0.39), (7, 0.395), (22, 0.41), (36, 0.43),    # the occiput
        (55, 0.46), (75, 0.49), (90, 0.50),                              # the crown
    ]
    return front, side, back


def skull(centre, sex, fp, segments=64, rings=44):
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
        # the head is taller than wide: the vertical component uses the height, the horizontal the width
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
        pt((sg * 0.17, -0.37, 0.02), 0.15, -0.05, (1.25, 1, 0.8))            # eye socket
        pt((sg * 0.3, -0.26, -0.07), 0.15, 0.03 * fp("cheek"), (1, 1, 1))    # cheekbone
        pt((sg * 0.33, -0.08, 0.26), 0.17, -0.025, (1, 1, 1.3))              # temple
        pt((sg * 0.27, 0.02, -0.4), 0.15, 0.025 * (fp("jaw") - 0.4), (1, 1, 1))  # the jaw's angle
        pt((sg * 0.21, -0.33, -0.2), 0.12, -0.02, (1, 1, 1.2))               # the cheek's hollow
        pt((sg * 0.09, -0.42, -0.16), 0.08, -0.015, (1.4, 1, 0.6))           # the nasolabial fold
    pt((0, -0.4, 0.14), 0.2, 0.025 * fp("brow"), (2.2, 1, 0.5))              # the brow ridge
    pt((0, -0.33, -0.45), 0.12, 0.03 * (0.85 if fem else 1.0), (1, 1, 1))    # the chin
    pt((0, -0.41, -0.34), 0.07, -0.02, (1.6, 1, 0.5))                        # under the lower lip
    pt((0, -0.4, 0.04), 0.08, -0.012, (1.2, 1, 0.8))                         # between the eyes
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


def features(centre, sex, fp, mats):
    """The eyes with lids, the nose, the lips, the ears: pieces about the skull. The face
    plane is at centre.y - 0.39 H; the eyes at centre.z."""
    H = HEAD_HEIGHT
    fem = sex == "f"
    skin, white, iris = mats["skin"], mats["eye_white"], mats["iris"]
    out = []
    face = centre.y - 0.39 * H
    # eyes: the ball set into the socket, the iris on its front, lids as thin arcs over it
    for sg in (1, -1):
        side = "l" if sg > 0 else "r"
        ex = sg * 0.17 * H
        ec = Vector((centre.x + ex, face + 0.045 * H, centre.z + 0.02 * H))
        out.append(_ellipsoid("Eye_%s" % side, ec, 0.058 * H, 0.058 * H, 0.058 * H, white))
        out.append(_ellipsoid("Iris_%s" % side, ec + Vector((0, -0.052 * H, 0)), 0.028 * H, 0.01 * H, 0.028 * H, iris))
        for name, dz, tilt in (("Lid_upper", 0.04, 1), ("Lid_lower", -0.035, -1)):
            pts = []
            for k in range(9):
                t = k / 8.0
                x = ex + (t - 0.5) * 0.15 * H
                bulge = math.sin(t * math.pi)
                pts.append(Vector((centre.x + x, ec.y - 0.052 * H * bulge, ec.z + dz * H + tilt * 0.01 * H * bulge)))
            out.append(_ob("%s_%s" % (name, side), pk._tube_bm(pts, [0.009 * H] * 9, segments=6), skin))
    # the nose: a loft from the bridge between the eyes down to the tip, then the wings
    nl, nw = fp("nose"), fp("noseWidth")
    rings = []
    spine = [(0.05, 0.0, 0.03, 0.02), (-0.02, -0.015, 0.036, 0.03), (-0.09, -0.04, 0.046, 0.04), (-0.15, -0.07, 0.058 * nw, 0.045), (-0.185, -0.08, 0.052 * nw, 0.035), (-0.205, -0.055, 0.036 * nw, 0.02)]
    for z, dy, hw, hd in spine:
        c = Vector((centre.x, face + dy * H * nl + 0.01 * H, centre.z + z * H * nl))
        rings.append((c, Vector((hw * H, 0, 0)), Vector((0, -hd * H * 0.7, hd * H * 0.7))))
    out.append(_loft_ob("Nose", rings, skin))
    for sg in (1, -1):
        out.append(_ellipsoid("Nostril_%s" % ("l" if sg > 0 else "r"), Vector((centre.x + sg * 0.062 * nw * H, face - 0.035 * H * nl, centre.z - 0.17 * H * nl)), 0.032 * H, 0.038 * H, 0.028 * H, skin))
    # the lips: two arcs on the mouth, the upper with a cupid's bow
    lf = fp("lips") * (1.12 if fem else 1.0)
    for name, dz, r, bow in (("Lip_upper", -0.255, 0.012, True), ("Lip_lower", -0.285, 0.014, False)):
        pts = []
        n = 11
        for k in range(n):
            t = k / (n - 1.0)
            x = (t - 0.5) * 0.24 * H
            curve = math.sin(t * math.pi)
            dip = 0.007 * H * math.cos((t - 0.5) * math.pi * 3) if bow else 0.0
            pts.append(Vector((centre.x + x, face - 0.005 * H - 0.025 * H * curve, centre.z + dz * H + dip)))
        rad = [r * H * lf * (0.4 + 0.6 * math.sin(k / (n - 1.0) * math.pi)) for k in range(n)]
        out.append(_ob(name, pk._tube_bm(pts, rad, segments=8), skin))
    # the ears: a helix round the back from the top, a concha, a lobe; flat against the side
    es = fp("ears")
    for sg in (1, -1):
        side = "l" if sg > 0 else "r"
        ec = Vector((centre.x + sg * 0.35 * H, centre.y + 0.03 * H, centre.z - 0.01 * H))
        pts = []
        n = 12
        for k in range(n):
            t = k / (n - 1.0)
            a = math.pi * (0.95 - 0.95 * t)   # from the top-front over the back down to the lobe
            pts.append(ec + Vector((sg * 0.02 * H * math.sin(a), 0.07 * H * es * math.cos(a), 0.1 * H * es * math.sin(a))))
        out.append(_ob("Ear_%s" % side, pk._tube_bm(pts, [0.014 * H * es] * n, segments=6), skin))
        out.append(_ellipsoid("Concha_%s" % side, ec + Vector((0, 0.0, 0.0)), 0.014 * H, 0.045 * H * es, 0.065 * H * es, skin))
        out.append(_ellipsoid("Earlobe_%s" % side, ec + Vector((0, -0.01 * H, -0.085 * H * es)), 0.016 * H, 0.03 * H * es, 0.028 * H * es, skin))
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
    pieces = features(centre, sex, fp, mats)
    return ob, pieces, centre


# ======================================================================================
# Hair, from the skull itself: a cap is the skull's own surface above the hairline, copied
# and pushed out along its normals, so it fits the carved head exactly; the falls (long,
# braid, bun, tail) are tubes from the cap. Styles: crop, long, braid, knot, tail; beards:
# short, full (on the jaw's own surface the same way).
# ======================================================================================

HAIR_STYLES = ["crop", "long", "braid", "knot", "tail"]
BEARD_STYLES = ["short", "full"]


def _shell(skull_ob, name, keep, thickness, mat):
    """The part of the skull where keep(world_position, world_normal) holds, as its own
    closed shell pushed out by `thickness`."""
    me = skull_ob.data
    normals = [n.vector.copy() for n in me.vertex_normals]
    M = skull_ob.matrix_world
    inside = [keep(M @ v.co, normals[i]) for i, v in enumerate(me.vertices)]
    bm = bmesh.new()
    index = {}
    for i, v in enumerate(me.vertices):
        if inside[i]:
            index[i] = bm.verts.new(M @ v.co + normals[i] * thickness)
    for poly in me.polygons:
        if all(inside[i] for i in poly.vertices):
            try:
                bm.faces.new([index[i] for i in poly.vertices])
            except ValueError:
                pass
    # the rim: a skirt down to the skull, so the cap has an edge rather than a floating sheet
    rim = [e for e in bm.edges if e.is_boundary]
    if rim:
        source = {index[i]: (M @ me.vertices[i].co) for i in index}
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
    hairline_side = centre.z + 0.05 * H     # over the ears at the sides
    nape = centre.z - 0.2 * H               # down the nape at the back

    def above_hairline(p, n):
        # the hairline runs from high at the brow, over the ear, down to the nape
        a = math.atan2(abs(p.x - centre.x), -(p.y - centre.y)) / math.pi   # 0 face .. 1 back
        line = hairline_front * (1 - a) ** 2 + hairline_side * 2 * a * (1 - a) + nape * a * a
        return p.z > line and not (n.y < -0.6 and p.z < centre.z + 0.32 * H)
    for style in HAIR_STYLES:
        out.append(_shell(skull_ob, "Hair_%s_cap" % style, above_hairline, 0.014, mat_hair))
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
            low = p.z < centre.z - 0.22 * H and p.z > chin_z - 0.02 * H
            frontish = (p.y - centre.y) < 0.1 * H
            not_mouth = not (abs(p.x - centre.x) < 0.14 * H and p.z > centre.z - 0.33 * H)
            return low and frontish and not_mouth and (p.z < centre.z - (0.28 + depth) * H or abs(p.x - centre.x) > 0.12 * H)
        beard = _shell(skull_ob, "Beard_%s" % style, on_jaw, 0.012 if style == "short" else 0.02, mat_hair)
        out.append(beard)
    if True:
        # the full beard hangs below the chin
        pts = [Vector((centre.x, face + 0.08 * H, chin_z - 0.02 * H)), Vector((centre.x, face + 0.05 * H, chin_z - 0.2 * H)), Vector((centre.x, face + 0.04 * H, chin_z - 0.38 * H))]
        hang = _ob("Beard_full_hang", pk._tube_bm(pts, [0.12 * H, 0.1 * H, 0.05 * H], segments=10), mat_hair)
        out.append(hang)
    return out
