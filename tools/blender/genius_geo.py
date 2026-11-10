"""WILDLINE genius kit, the geometry: small builders that return (verts, faces) in world space,
so the same shape can become its own object (a part, an unrigged body) or be joined to a rigged
body and weighted to a bone. Everything is faceted on purpose: flat planes take the cel bands
and the ink line cleanly; smooth tubes do not.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def V(p):
    return p if isinstance(p, Vector) else Vector(p)


def merge(*geos):
    verts, faces = [], []
    for g in geos:
        if not g:
            continue
        vs, fs = g
        off = len(verts)
        verts.extend(vs)
        faces.extend([tuple(i + off for i in f) for f in fs])
    return verts, faces


def moved(geo, T):
    """A geometry through a 4x4 matrix."""
    return [T @ V(p) for p in geo[0]], list(geo[1])


def mirrored(geo):
    """Mirrored across X (the faces turned to keep facing out)."""
    return [Vector((-p.x, p.y, p.z)) for p in geo[0]], [tuple(reversed(f)) for f in geo[1]]


def _frame(axis):
    axis = V(axis).normalized()
    ref = Z if abs(axis.dot(Z)) < 0.92 else Y
    u = axis.cross(ref).normalized()
    v = axis.cross(u).normalized()
    return u, v


def tube(points, radii, n=6, caps=True, flat=1.0, twist=0.0, up=None):
    """A faceted tube through points with a radius at each; `flat` squashes it across its
    second axis (a strap, a feather shaft); `twist` turns the section along the way."""
    points = [V(p) for p in points]
    verts, faces = [], []
    m = len(points)
    prev_u = None
    for i, p in enumerate(points):
        d = points[min(i + 1, m - 1)] - points[max(i - 1, 0)]
        if up is not None:
            u = V(up).cross(d).normalized()
            if u.length < 1e-6:
                u, _ = _frame(d)
            v = d.normalized().cross(u).normalized()
        else:
            u, v = _frame(d)
            if prev_u is not None and u.dot(prev_u) < 0:
                u, v = -u, -v
        prev_u = u
        r = radii[i] if not isinstance(radii, (int, float)) else radii
        for k in range(n):
            a = 2 * math.pi * k / n + twist * i
            verts.append(p + (u * math.cos(a) + v * math.sin(a) * flat) * r)
    for i in range(m - 1):
        for k in range(n):
            a, b = i * n + k, i * n + (k + 1) % n
            faces.append((a, b, b + n, a + n))
    if caps:
        faces.append(tuple(range(n - 1, -1, -1)))
        faces.append(tuple(range((m - 1) * n, m * n)))
    return verts, faces


def cone(base, tip, r, n=6):
    return tube([base, tip], [r, r * 0.02], n)


def loft(rings, caps=True, closed=True):
    """Rings of points (the same count each) bridged in order."""
    verts, faces = [], []
    n = len(rings[0])
    for ring in rings:
        verts.extend(V(p) for p in ring)
    for i in range(len(rings) - 1):
        for k in range(n if closed else n - 1):
            a, b = i * n + k, i * n + (k + 1) % n
            faces.append((a, b, b + n, a + n))
    if caps and closed:
        faces.append(tuple(range(n - 1, -1, -1)))
        faces.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
    return verts, faces


def ring(centre, rx, ry, n=8, u=X, v=Y, phase=0.0):
    c = V(centre)
    return [c + V(u) * (math.cos(2 * math.pi * k / n + phase) * rx) + V(v) * (math.sin(2 * math.pi * k / n + phase) * ry) for k in range(n)]


def blade(base, tip, width, thick=None, normal=None, belly=0.38, curl=0.0):
    """A feather, a leaf, a flame's tongue, a tatter: a flat pointed plate from base to tip,
    widest `belly` of the way along, with a ridge down its middle. `normal` is the way its
    face looks; `curl` bends the tip that way."""
    base, tip = V(base), V(tip)
    d = tip - base
    L = d.length
    if normal is None:
        normal = Z if abs(d.normalized().dot(Z)) < 0.9 else Y
    n = V(normal).normalized()
    side = d.cross(n).normalized()
    n = side.cross(d).normalized()
    thick = width * 0.22 if thick is None else thick
    mid = base + d * belly
    tip = tip + n * (curl * L)
    verts = [base, mid + side * (width / 2), tip, mid - side * (width / 2), mid + n * thick + d * 0.05, mid - n * thick * 0.6]
    faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (1, 0, 5), (2, 1, 5), (3, 2, 5), (0, 3, 5)]
    return verts, faces


def tongue(points, widths, thick=0.4, normal=None):
    """A bent blade through several points (a flame, a long feather, a horn plate): a diamond
    section at each point, closing to the last."""
    points = [V(p) for p in points]
    verts, faces = [], []
    m = len(points)
    for i, p in enumerate(points):
        d = points[min(i + 1, m - 1)] - points[max(i - 1, 0)]
        nn = V(normal) if normal is not None else (Z if abs(d.normalized().dot(Z)) < 0.9 else Y)
        side = d.cross(nn).normalized()
        nn = side.cross(d).normalized()
        w = widths[i]
        verts += [p + side * (w / 2), p + nn * (w * thick / 2), p - side * (w / 2), p - nn * (w * thick / 2)]
    for i in range(m - 1):
        for k in range(4):
            a, b = i * 4 + k, i * 4 + (k + 1) % 4
            faces.append((a, b, b + 4, a + 4))
    faces.append((3, 2, 1, 0))
    faces.append(((m - 1) * 4, (m - 1) * 4 + 1, (m - 1) * 4 + 2, (m - 1) * 4 + 3))
    return verts, faces


def box(centre, size, rot=None):
    """A box of full size (x, y, z) about centre; rot is a 3x3 or Euler tuple."""
    c = V(centre)
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    R = Matrix.Identity(3)
    if rot is not None:
        R = rot if isinstance(rot, Matrix) else (Matrix.Rotation(rot[2], 3, "Z") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[0], 3, "X"))
    corners = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz), (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    verts = [c + R @ Vector(p) for p in corners]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return verts, faces


def ico(centre, r, sub=1, scale=(1, 1, 1), rot=None):
    """A faceted ball (an icosphere), scaled per axis: a gem, a coal, an eye, a joint."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    R = Matrix.Identity(3)
    if rot is not None:
        R = Matrix.Rotation(rot[2], 3, "Z") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[0], 3, "X")
    c = V(centre)
    idx = {v: i for i, v in enumerate(bm.verts)}
    verts = [c + R @ Vector((v.co.x * r * scale[0], v.co.y * r * scale[1], v.co.z * r * scale[2])) for v in bm.verts]
    faces = [tuple(idx[v] for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces


def lathe(profile, n=8, centre=(0, 0, 0), caps=True, phase=0.0):
    """A profile of (radius, z) spun about Z."""
    c = V(centre)
    rings = [[c + Vector((r * math.cos(2 * math.pi * k / n + phase), r * math.sin(2 * math.pi * k / n + phase), z)) for k in range(n)] for r, z in profile]
    return loft(rings, caps=caps)


def spiral(centre, r0, r1, turns, rise, n=14, axis=X, start=0.0, drift=(0, 0, 0)):
    """Points on a spiral about an axis: a ram's horn, a curled tail."""
    c = V(centre)
    axis = V(axis).normalized()
    u, v = _frame(axis)
    out = []
    for i in range(n + 1):
        t = i / n
        a = start + turns * 2 * math.pi * t
        r = r0 + (r1 - r0) * t
        out.append(c + (u * math.cos(a) + v * math.sin(a)) * r + axis * (rise * t) + V(drift) * t)
    return out


# --- into Blender -----------------------------------------------------------------------

def to_object(name, geo, mat, smooth=False):
    """A mesh object from a geometry (one material)."""
    verts, faces = geo
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], [tuple(f) for f in faces])
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if mat is not None:
        me.materials.append(mat)
    return ob


def join(name, objects):
    """Several mesh objects as one (their materials kept)."""
    objects = [o for o in objects if o is not None]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    ob.select_set(False)
    return ob


def pieces(name, items, smooth=False):
    """[(geometry, material), ...] as one object."""
    return join(name, [to_object("%s_%d" % (name, i), g, m, smooth) for i, (g, m) in enumerate(items) if g and g[0]])
