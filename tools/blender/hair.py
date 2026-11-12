"""WILDLINE hair: the styles and the beards, grown from the head's own surface
(docs/bodies-plan.md, "Faces, eyes and hair").

A cap is the scalp above a hairline, lifted along its normals: thin and broken at the edge
(strands, not a helmet's rim), full at the crown, and furrowed along the way the hair is
combed (out from the crown, back to a tie, down from a parting, in rows), so the bands of
light fall as strands. What hangs from a cap (a fall, a bob, a tail, a plait, locs, a knot)
is its own piece: under headgear the cap hides and the fall still hangs. Pieces are named
Hair_<style>_cap, Hair_<style>_top (hidden under headgear too) and Hair_<style>_fall;
beards Beard_<style> and Beard_<style>_hang.

World space is Blender's: Z up, the face at -Y, the character's left at +X.
"""
import math

import bpy
import bmesh
from mathutils import Vector, Matrix

import people_kit as pk

HAIR_STYLES = ["crop", "short", "curls", "coils", "rows", "locs", "bob", "long", "tail", "braid", "twins", "knot", "topknot", "crest",
               "afro", "plaits", "coilknots", "fade", "thin"]
BEARD_STYLES = ["stubble", "moustache", "goatee", "short", "full"]


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _bump(s):
    s = abs(s)
    return (1.0 - s * s) ** 1.5 if s < 1.0 else 0.0


def _ob(name, bm, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = pk._bm_object(name, bm, mat)
    pk._smooth(ob)
    return ob


class Scalp:
    """The head's surface, made finer, to cut hair from."""

    def __init__(self, surf_ob, centre, H, fine=True):
        bm = bmesh.new()
        bm.from_mesh(surf_ob.data)
        keep_above = centre.z - 0.95 * H
        low = [v for v in bm.verts if v.co.z < keep_above]
        bmesh.ops.delete(bm, geom=low, context="VERTS")
        if fine:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
        me = bpy.data.meshes.new("Scalp")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.update()
        self.P = [v.co.copy() for v in me.vertices]
        self.N = [n.vector.copy() for n in me.vertex_normals]
        self.polys = [list(p.vertices) for p in me.polygons]
        bpy.data.meshes.remove(me)
        self.c, self.H = centre, H

    def shell(self, name, field, lift, mat):
        """The surface where field(p, n) > 0, cut along the zero line and lifted by
        lift(p, n, f) along the normal, with a skirt back down to the skin at its edge."""
        P, N = self.P, self.N
        F = [field(P[i], N[i]) for i in range(len(P))]
        bm = bmesh.new()
        made, source, crossing = {}, {}, {}

        def vert_of(i):
            if i not in made:
                made[i] = bm.verts.new(P[i] + N[i] * lift(P[i], N[i], F[i]))
                source[made[i]] = P[i]
            return made[i]

        def cross(i, j):
            key = (min(i, j), max(i, j))
            if key not in crossing:
                t = F[i] / (F[i] - F[j])
                p = P[i].lerp(P[j], t)
                n = N[i].lerp(N[j], t).normalized()
                v = bm.verts.new(p + n * lift(p, n, 0.0))
                source[v] = p
                crossing[key] = v
            return crossing[key]

        for idx in self.polys:
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
        rim = [e for e in bm.edges if e.is_boundary]
        if rim:
            geom = bmesh.ops.extrude_edge_only(bm, edges=rim)
            for v in [g for g in geom["geom"] if isinstance(g, bmesh.types.BMVert)]:
                for e in v.link_edges:
                    o = e.other_vert(v)
                    if o in source:
                        v.co = source[o]
                        break
        return _ob(name, bm, mat)


def _curtain(name, levels, mat, n=26, clumps=9.0, groove=0.07, jag=0.0, seed=0.0):
    """Hair that hangs: a crescent about the back of the head, lofted down. A level is
    (z, centre y, half-width x, half-depth y, half-angle in degrees about the back, thickness);
    the outside is furrowed in clumps and the hem is broken into locks."""
    bm = bmesh.new()
    outer, inner = [], []
    for li, (z, cy, rx, ry, half, th) in enumerate(levels):
        ro, ri = [], []
        last = li == len(levels) - 1
        for j in range(n + 1):
            u = j / float(n)
            a = math.radians(-half + 2 * half * u)
            g = 1.0 + groove * (0.65 * math.sin(clumps * 2 * math.pi * u + seed) + 0.35 * math.sin(2.3 * clumps * 2 * math.pi * u + 1.7 + seed))
            edge = min(1.0, 6.0 * min(u, 1.0 - u) + 0.25)       # the two front edges thin away
            dz = -jag * abs(math.sin(clumps * math.pi * u + seed * 2.0)) if last else 0.0
            ro.append(bm.verts.new(Vector((rx * g * math.sin(a), cy + ry * g * math.cos(a), z + dz))))
            t = th * edge
            ri.append(bm.verts.new(Vector(((rx - t) * math.sin(a), cy + (ry - t) * math.cos(a), z + dz * 0.6))))
        outer.append(ro)
        inner.append(ri)
    for i in range(len(levels) - 1):
        for j in range(n):
            bm.faces.new((outer[i][j], outer[i][j + 1], outer[i + 1][j + 1], outer[i + 1][j]))
            bm.faces.new((inner[i][j + 1], inner[i][j], inner[i + 1][j], inner[i + 1][j + 1]))
        bm.faces.new((outer[i][0], outer[i + 1][0], inner[i + 1][0], inner[i][0]))
        bm.faces.new((outer[i + 1][n], outer[i][n], inner[i][n], inner[i + 1][n]))
    for j in range(n):
        bm.faces.new((outer[0][j + 1], outer[0][j], inner[0][j], inner[0][j + 1]))
        bm.faces.new((outer[-1][j], outer[-1][j + 1], inner[-1][j + 1], inner[-1][j]))
    return _ob(name, bm, mat)


def _tube(bm, points, radii, segments=8, lobes=0, depth=0.0):
    """A tube through points; with lobes, its ring is furrowed (strands gathered together)."""
    rings = []
    Z, X = Vector((0, 0, 1)), Vector((1, 0, 0))
    for i, (p, r) in enumerate(zip(points, radii)):
        d = (points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized()
        u = d.cross(Z if abs(d.dot(Z)) < 0.9 else X).normalized()
        w = d.cross(u).normalized()
        ring = []
        for k in range(segments):
            a = 2 * math.pi * k / segments
            rr = r * (1.0 + depth * math.sin(lobes * a)) if lobes else r
            ring.append(bm.verts.new(p + (u * math.cos(a) + w * math.sin(a)) * rr))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(segments):
            bm.faces.new((a[k], a[(k + 1) % segments], b[(k + 1) % segments], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])


def _ball(bm, c, rx, ry, rz, rot=None, u=10, v=6):
    made = bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)["verts"]
    bmesh.ops.scale(bm, vec=(rx, ry, rz), verts=made)
    if rot is not None:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=made)
    bmesh.ops.translate(bm, vec=c, verts=made)


def _plait(bm, top, length, width, sway=0.0, lean=Vector((0, 0, 0))):
    """A plait: links laid over one another left and right, narrowing to a tied end."""
    n = max(5, int(length / (width * 0.62)))
    for i in range(n):
        t = i / float(n - 1)
        w = width * (1.0 - 0.45 * t)
        side = 1.0 if i % 2 == 0 else -1.0
        p = top + Vector((side * 0.2 * w + sway * math.sin(t * 2.6), 0.0, -length * t)) + lean * t
        _ball(bm, p, 0.56 * w, 0.42 * w, 0.62 * (length / n) * 1.25, Matrix.Rotation(side * 0.5, 3, "Y"), u=8, v=5)
    end = top + Vector((0, 0, -length)) + lean
    _tube(bm, [end + Vector((0, 0, 0.3 * width)), end, end - Vector((0, 0, 0.5 * width)), end - Vector((0, 0, 0.95 * width))],
          [0.28 * width, 0.22 * width, 0.33 * width, 0.05 * width], segments=7)


def hair(surf_ob, centre, sex, H, mat, back_y=None):
    """Every style and beard on this head. `back_y(z)` is where the body's back is at a
    height (the long fall hangs clear of it)."""
    S = Scalp(surf_ob, centre, H)
    c = centre
    out = []
    back = c.y + 0.39 * H
    front_line, side_line, nape = c.z + 0.3 * H, c.z + 0.06 * H, c.z - 0.2 * H

    def hairline(p, n, front=0.0, jag=0.016, nape_up=0.0):
        a = math.atan2(abs(p.x - c.x), -(p.y - c.y)) / math.pi          # 0 at the face, 1 at the back
        line = (front_line + front * H) * (1 - a) ** 2 + side_line * 2 * a * (1 - a) + (nape + nape_up * H) * a * a
        line += 0.032 * H * _bump((a - 0.22) / 0.12)                    # the temples
        line -= 0.02 * H * _bump(a / 0.07)                              # a soft point at the middle of the brow
        s = 1.0 if p.x >= c.x else -1.0
        line += jag * H * (0.6 * abs(math.sin(41.0 * a * math.pi + s)) + 0.4 * abs(math.sin(97.0 * a * math.pi + 1.3 * s)) - 0.5)
        f = p.z - line
        if n.y < -0.6:
            f = min(f, p.z - (c.z + 0.32 * H + front * H))
        return f

    def fill(f, edge, full, reach=0.1):
        return edge + (full - edge) * _smooth(f / (reach * H))

    def about(axis):
        axis = axis.normalized()
        e1 = axis.cross(Vector((1, 0, 0)) if abs(axis.x) < 0.8 else Vector((0, 0, 1))).normalized()
        e2 = axis.cross(e1)

        def u(p):
            q = p - c
            return math.atan2(q.dot(e1), q.dot(e2)), math.acos(max(-1.0, min(1.0, q.normalized().dot(axis))))
        return u

    def strands(u, k, pole=None):
        g = 0.62 * math.sin(k * u) + 0.38 * math.sin(2.0 * k * u + 1.9)
        if pole is not None:        # where the strands meet (a crown, a tie) they close up
            g *= _smooth(pole / 0.5)
        return g

    crown = about(Vector((0.04, 0.42, 0.9)))
    tie_back = about(Vector((0.0, 0.8, 0.45)))
    tie_up = about(Vector((0.0, 0.25, 1.0)))

    def lift_whorl(vol, depth, k=30):
        def lift(p, n, f):
            u, pole = crown(p)
            return fill(f, 0.0016, vol * H) * (1.0 + depth * strands(u, k, pole))
        return lift

    def lift_tied(flow, vol, depth, k=34):
        def lift(p, n, f):
            u, pole = flow(p)
            return fill(f, 0.0016, vol * H) * (1.0 + depth * strands(u, k, pole))
        return lift

    def lift_parted(vol, depth, x0=0.0, k=24.0):
        def lift(p, n, f):
            top = _smooth((p.z - (c.z + 0.2 * H)) / (0.15 * H))
            d = (p.x - c.x - x0 * H) / H
            part = _bump(d / 0.035) * top                       # the parting: the scalp nearly shows
            swell = _bump((abs(d) - 0.11) / 0.1) * top          # and the hair rises either side of it
            u = (p.y - c.y) / H + 0.25 * abs(d)                 # the strands fall across, a little back
            return fill(f, 0.0016, vol * H) * (1.0 + depth * strands(u * 2 * math.pi, k)) * (1.0 - 0.8 * part) * (1.0 + 0.35 * swell)
        return lift

    def lift_noise(vol, depth, scale, reach=0.1, ball=0.0):
        def lift(p, n, f):
            q = (p - c) * (scale / H)
            g = math.sin(q.x * 1.0 + 1.3) * math.sin(q.y * 1.13 + 2.1) * math.sin(q.z * 0.94 + 0.7) + 0.5 * math.sin(q.x * 2.1 + q.z * 1.7) * math.sin(q.y * 2.3 + 0.4)
            t = fill(f, 0.0016, vol * H, reach) * (1.0 + depth * g)
            if ball > 0.0:      # an afro: toward a round about the head, not a coat on it
                r = (p - c).length
                t += ball * _smooth(f / (reach * H)) * max(0.0, 0.5 * H * 1.02 - r)
            return t
        return lift

    def lift_rows(vol, depth, rows=9.0):
        def lift(p, n, f):
            a = math.atan2(p.x - c.x, p.z - (c.z - 0.1 * H))        # rows run from the brow back over the crown
            return fill(f, 0.0016, vol * H, 0.05) * (1.0 + depth * math.sin(rows * 2.0 * a))
        return lift

    def cap(style, field, lift, kind="cap"):
        out.append(S.shell("Hair_%s_%s" % (style, kind), field, lift, mat))

    # the caps -------------------------------------------------------------------------
    cap("crop", lambda p, n: hairline(p, n, jag=0.01), lift_whorl(0.016, 0.3, 26))
    cap("short", lambda p, n: hairline(p, n), lift_parted(0.05, 0.2, x0=0.14))
    cap("curls", lambda p, n: hairline(p, n, jag=0.03), lift_noise(0.075, 0.45, 26.0))
    cap("coils", lambda p, n: hairline(p, n, front=-0.01, jag=0.03), lift_noise(0.15, 0.2, 30.0, reach=0.16, ball=0.55))
    cap("rows", lambda p, n: hairline(p, n, jag=0.006), lift_rows(0.02, 0.55))
    cap("locs", lambda p, n: hairline(p, n, jag=0.012), lift_whorl(0.024, 0.5, 20))
    for style in ("bob", "long", "twins"):
        cap(style, lambda p, n: hairline(p, n), lift_parted(0.04, 0.2))
    for style in ("tail", "braid", "knot"):
        cap(style, lambda p, n: hairline(p, n, front=0.01, jag=0.012), lift_tied(tie_back, 0.028, 0.26))
    cap("topknot", lambda p, n: hairline(p, n, front=0.01, jag=0.012), lift_tied(tie_up, 0.026, 0.26))

    def crest_field(p, n):
        d = abs(p.x - c.x) / H
        return min(hairline(p, n, jag=0.012), (0.17 - d) * H if p.z > c.z - 0.12 * H else -1.0)
    cap("crest", crest_field, lift_tied(tie_back, 0.07, 0.22, 30))

    # what hangs -----------------------------------------------------------------------
    def clear(z, y_out):
        """The fall's centre pushed back so its inside clears the body's back."""
        return y_out if back_y is None else max(y_out, back_y(z) + 0.02)

    lv = []
    for dz, rx, ry, half, th in ((0.16, 0.345, 0.375, 118, 0.05), (-0.08, 0.385, 0.4, 116, 0.07), (-0.34, 0.39, 0.38, 104, 0.085),
                                 (-0.62, 0.36, 0.3, 82, 0.085), (-0.92, 0.37, 0.2, 64, 0.075), (-1.2, 0.35, 0.15, 56, 0.06), (-1.42, 0.3, 0.11, 50, 0.03)):
        z = c.z + dz * H
        cy = c.y + 0.03 * H
        if dz < -0.5:
            cy = clear(z, cy + ry * H) - ry * H + 0.045 * H
        lv.append((z, cy, rx * H, ry * H, half, th * H))
    out.append(_curtain("Hair_long_fall", lv, mat, clumps=11.0, groove=0.06, jag=0.07 * H))
    lv = [(c.z + dz * H, c.y + 0.02 * H, rx * H, ry * H, half, th * H) for dz, rx, ry, half, th in
          ((0.16, 0.345, 0.375, 124, 0.05), (-0.06, 0.4, 0.41, 126, 0.08), (-0.3, 0.425, 0.42, 124, 0.1), (-0.47, 0.4, 0.4, 120, 0.1), (-0.56, 0.35, 0.36, 116, 0.07))]
    out.append(_curtain("Hair_bob_fall", lv, mat, clumps=10.0, groove=0.055, jag=0.02 * H, seed=1.0))

    # tail: gathered high at the back, tied, swinging out and down
    bm = bmesh.new()
    g = Vector((c.x, back - 0.07 * H, c.z + 0.2 * H))
    pts = [g + Vector((0, 0.02 * H + 0.3 * H * math.sin(math.pi * min(1.0, i / 7.0) * 0.8), 0.02 * H - (i / 9.0) ** 1.25 * 1.05 * H)) for i in range(10)]
    rad = [H * r for r in (0.05, 0.062, 0.09, 0.1, 0.098, 0.09, 0.078, 0.062, 0.04, 0.012)]
    _tube(bm, pts, rad, segments=12, lobes=6, depth=0.1)
    _tube(bm, [pts[0] + Vector((0, -0.01 * H, 0.012 * H)), pts[1] + Vector((0, 0.002 * H, -0.005 * H))], [0.07 * H, 0.07 * H], segments=10)
    out.append(_ob("Hair_tail_fall", bm, mat))

    # braid: one plait from the nape
    bm = bmesh.new()
    _plait(bm, Vector((c.x, back - 0.06 * H, c.z - 0.12 * H)), 1.2 * H, 0.14 * H, lean=Vector((0, 0.03 * H if back_y is None else max(0.0, back_y(c.z - 1.3 * H) + 0.07 * H - (back - 0.06 * H)), 0)))
    out.append(_ob("Hair_braid_fall", bm, mat))

    # twins: a plait behind each ear, down over the back of the shoulders
    bm = bmesh.new()
    for sg in (1.0, -1.0):
        top = Vector((c.x + sg * 0.3 * H, c.y + 0.2 * H, c.z - 0.2 * H))
        y_end = top.y if back_y is None else max(top.y, back_y(c.z - 1.2 * H) + 0.055 * H)
        _plait(bm, top, 1.0 * H, 0.105 * H, lean=Vector((sg * 0.1 * H, y_end - top.y, 0)))
    out.append(_ob("Hair_twins_fall", bm, mat))

    # knot: a coiled bun high at the back, pinned
    bm = bmesh.new()
    kc = Vector((c.x, back - 0.07 * H, c.z + 0.24 * H))
    tilt = Matrix.Rotation(math.radians(-38), 3, "X")
    for i in range(3):
        r = (0.15 - 0.035 * i) * H
        ring = [kc + tilt @ Vector((r * math.cos(a), r * math.sin(a), (0.03 + 0.045 * i) * H)) for a in [2 * math.pi * k / 12 for k in range(13)]]
        _tube(bm, ring, [(0.055 - 0.008 * i) * H] * 13, segments=7)
    _ball(bm, kc + tilt @ Vector((0, 0, 0.1 * H)), 0.09 * H, 0.09 * H, 0.07 * H, tilt)
    out.append(_ob("Hair_knot_fall", bm, mat))

    # topknot: drawn up to the crown, bound, and folded forward
    bm = bmesh.new()
    tc = Vector((c.x, c.y + 0.14 * H, c.z + 0.5 * H))
    _tube(bm, [tc + Vector((0, 0, -0.03 * H)), tc + Vector((0, 0, 0.05 * H))], [0.085 * H, 0.06 * H], segments=10, lobes=5, depth=0.12)
    _tube(bm, [tc + Vector((0, 0, 0.04 * H)), tc + Vector((0, -0.01 * H, 0.1 * H)), tc + Vector((0, -0.08 * H, 0.135 * H)), tc + Vector((0, -0.17 * H, 0.105 * H)), tc + Vector((0, -0.21 * H, 0.07 * H))],
          [0.05 * H, 0.06 * H, 0.062 * H, 0.05 * H, 0.02 * H], segments=10, lobes=5, depth=0.12)
    _tube(bm, [tc + Vector((0, 0, 0.03 * H)), tc + Vector((0, 0, 0.055 * H))], [0.068 * H, 0.068 * H], segments=10)
    out.append(_ob("Hair_topknot_top", bm, mat))

    # locs: ropes from all over the scalp, to the shoulders at the back
    import random
    rnd = random.Random(11)
    bm = bmesh.new()
    count = 0
    for i, (p, n) in enumerate(zip(S.P, S.N)):
        if i % 9 != 0 or hairline(p, n, jag=0.0) < 0.035 * H:
            continue
        a = math.atan2(abs(p.x - c.x), -(p.y - c.y)) / math.pi
        if a < 0.4:
            continue    # none down over the face: the front of the crown is the cap's
        count += 1
        out_dir = Vector((p.x - c.x, p.y - c.y, 0.0))
        out_dir = out_dir.normalized() if out_dir.length > 1e-4 else Vector((0, 1, 0))
        length = (0.5 + 0.55 * a + rnd.uniform(-0.08, 0.08)) * H
        end_z = max(p.z - length, c.z - (0.42 + 0.5 * a) * H)
        r_out = max(0.47 * H, math.hypot(p.x - c.x, p.y - c.y) + 0.035 * H)
        pts = [p + n * 0.012 * H]
        for t in (0.3, 0.6, 1.0):
            z = p.z + (end_z - p.z) * t
            reach = r_out * (1.0 - 0.1 * t) * (0.86 if z < c.z - 0.3 * H else 1.0)
            pts.append(Vector((c.x + out_dir.x * reach, c.y + 0.03 * H + out_dir.y * reach + rnd.uniform(-0.01, 0.01) * H, z)))
        _tube(bm, pts, [0.03 * H, 0.03 * H, 0.028 * H, 0.02 * H], segments=6)
    out.append(_ob("Hair_locs_fall", bm, mat))

    # rows: the rows end in short plaits at the nape
    bm = bmesh.new()
    for i in range(7):
        a = math.radians(-66 + 22 * i)
        top = Vector((c.x + 0.3 * H * math.sin(a), c.y + 0.02 * H + 0.33 * H * math.cos(a), c.z - 0.2 * H))
        _tube(bm, [top + Vector((0, -0.02 * H, 0.05 * H)), top, top + Vector((0, 0.02 * H, -0.16 * H)), top + Vector((0, 0.03 * H, -0.3 * H))], [0.02 * H, 0.024 * H, 0.02 * H, 0.008 * H], segments=5)
    out.append(_ob("Hair_rows_fall", bm, mat))

    # more textures and cuts (docs/representation-plan.md) --------------------------------
    # afro: a full round of hair about the head, standing well off it
    ac = c + Vector((0.0, 0.04 * H, 0.16 * H))

    def lift_afro(p, n, f, R=0.6):
        q = (p - c) * (24.0 / H)
        g = math.sin(q.x + 1.3) * math.sin(q.y * 1.13 + 2.1) * math.sin(q.z * 0.94 + 0.7) + 0.5 * math.sin(q.x * 2.1 + q.z * 1.7) * math.sin(q.y * 2.3 + 0.4)
        return 0.0016 + _smooth(f / (0.17 * H)) * max(0.05 * H, R * H - (p - ac).length) * (1.0 + 0.05 * g)
    # these caps are cut from the head's own mesh, not made finer: a quarter of the points
    # (every style is in every person's file; the web build has a ceiling)
    C = Scalp(surf_ob, centre, H, fine=False)

    def cap_light(style, field, lift):
        out.append(C.shell("Hair_%s_cap" % style, field, lift, mat))
    cap_light("afro", lambda p, n: hairline(p, n, front=-0.012, jag=0.0), lift_afro)

    # plaits: many long thin braids, in rows on the scalp and down past the shoulders
    cap_light("plaits", lambda p, n: hairline(p, n, jag=0.0), lift_whorl(0.012, 0.0, 20))
    rnd2 = random.Random(23)
    bm = bmesh.new()
    for i, (p, n) in enumerate(zip(S.P, S.N)):
        if i % 9 != 0 or hairline(p, n, jag=0.0) < 0.03 * H:
            continue
        a = math.atan2(abs(p.x - c.x), -(p.y - c.y)) / math.pi
        if a < 0.36:
            continue    # none over the face
        out_dir = Vector((p.x - c.x, p.y - c.y, 0.0))
        out_dir = out_dir.normalized() if out_dir.length > 1e-4 else Vector((0, 1, 0))
        end_z = c.z - (0.55 + 0.85 * a + rnd2.uniform(-0.06, 0.06)) * H
        r_out = max(0.46 * H, math.hypot(p.x - c.x, p.y - c.y) + 0.03 * H)
        pts = [p + n * 0.01 * H]
        for t in (0.3, 0.65, 1.0):
            z = p.z + (end_z - p.z) * t
            reach = r_out * (1.0 - 0.14 * t) * (0.8 if z < c.z - 0.35 * H else 1.0)
            y = c.y + 0.03 * H + out_dir.y * reach + rnd2.uniform(-0.008, 0.008) * H
            if back_y is not None and z < c.z - 0.5 * H and out_dir.y > 0.2:
                y = max(y, back_y(z) + 0.03 * H)       # down the back, clear of it
            pts.append(Vector((c.x + out_dir.x * reach, y, z)))
        _tube(bm, pts, [0.022 * H, 0.022 * H, 0.02 * H, 0.012 * H], segments=4)
    out.append(_ob("Hair_plaits_fall", bm, mat))

    # coilknots: the hair parted in sections, each wound into a small knot on the scalp
    cap_light("coilknots", lambda p, n: hairline(p, n, jag=0.0), lift_whorl(0.012, 0.0, 22))
    bm = bmesh.new()
    spots = []
    for i, (p, n) in enumerate(zip(S.P, S.N)):
        if hairline(p, n, jag=0.0) < 0.07 * H or any((p - q).length < 0.23 * H for q in spots):
            continue
        spots.append(p)
        base = p + n * 0.012 * H
        up = n.lerp(Vector((0, 0, 1)), 0.25).normalized()
        _ball(bm, base + up * 0.022 * H, 0.078 * H, 0.078 * H, 0.05 * H, u=8, v=5)
        _ball(bm, base + up * 0.052 * H, 0.056 * H, 0.056 * H, 0.04 * H, u=8, v=4)
    out.append(_ob("Hair_coilknots_top", bm, mat))

    # fade: full on top, the sides and the back cut down to the skin
    def fade_field(p, n):
        a = math.atan2(abs(p.x - c.x), -(p.y - c.y)) / math.pi
        return min(hairline(p, n, jag=0.008), p.z - (c.z + (0.22 + 0.06 * a) * H))
    cap("fade", fade_field, lift_noise(0.05, 0.3, 30.0, reach=0.16))

    # thin: gone from the crown, kept round the sides and the back
    cap_light("thin", lambda p, n: min(hairline(p, n, jag=0.0), (c.z + 0.3 * H) - p.z), lift_whorl(0.013, 0.0, 26))

    # the beards -----------------------------------------------------------------------
    chin_z = c.z - 0.5 * H
    J = Scalp(surf_ob, centre, H, fine=False)       # the face's own mesh is fine enough for a beard

    def jaw(p, n, depth=0.0, width=1.0):
        low = min(c.z - 0.22 * H - p.z, p.z - (chin_z - 0.02 * H))
        frontish = 0.1 * H - (p.y - c.y)
        not_mouth = max(abs(p.x - c.x) - 0.14 * H, (c.z - 0.33 * H) - p.z)
        cut = max(c.z - (0.28 + depth) * H - p.z, abs(p.x - c.x) - 0.12 * H)
        wide = (width * 0.5 * H - abs(p.x - c.x)) if width < 1.0 else 1.0
        return min(low, frontish, not_mouth, cut, wide)

    def lip(p, n, wide=0.15):
        """Over the upper lip: from under the nose to the lip's edge."""
        return min(p.z - (c.z - 0.262 * H), (c.z - 0.2 * H) - p.z, wide * H - abs(p.x - c.x), (c.y - 0.25 * H) - p.y)

    def beard(name, field, thick, reach=0.05):
        out.append(J.shell(name, field, lambda p, n, f: 0.0012 + (thick - 0.0012) * _smooth(f / (reach * H)) * (1.0 + 0.12 * math.sin(60.0 * (p.x - c.x) / H * 2 * math.pi / 6.0)), mat))

    beard("Beard_stubble", lambda p, n: max(jaw(p, n, 0.06), lip(p, n, 0.17)), 0.0016, 0.02)
    beard("Beard_moustache", lambda p, n: lip(p, n), 0.011, 0.025)
    beard("Beard_goatee", lambda p, n: max(jaw(p, n, 0.0, 0.3), lip(p, n, 0.13)), 0.012)
    beard("Beard_short", lambda p, n: max(jaw(p, n, 0.08), lip(p, n)), 0.011)
    beard("Beard_full", lambda p, n: max(jaw(p, n, 0.0), lip(p, n, 0.16)), 0.02)
    face = c.y - 0.39 * H
    for style, drop, r0 in (("full", 0.36, 0.12),):
        bm = bmesh.new()
        pts = [Vector((c.x, face + 0.09 * H, chin_z + 0.03 * H)), Vector((c.x, face + 0.06 * H, chin_z - 0.4 * drop * H)), Vector((c.x, face + 0.05 * H, chin_z - 0.8 * drop * H)), Vector((c.x, face + 0.05 * H, chin_z - drop * H))]
        _tube(bm, pts, [r0 * H, r0 * 0.86 * H, r0 * 0.5 * H, 0.012 * H], segments=12, lobes=6, depth=0.09)
        out.append(_ob("Beard_%s_hang" % style, bm, mat))
    return out
