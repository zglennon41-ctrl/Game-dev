"""WILDLINE genius lines, the Stag: a deer's body of its own on the wolf's bones
(docs/genius-lines.md, "The Stag"; genius_lines.py calls this file's register).

    python tools/blender/genius_lines.py stag
    python tools/blender/genius_lines.py stag stag-fawn stag-twelve-point

Of the wolf it keeps the skeleton and the clips, and nothing else. The frame is stood as a
deer stands (long legs straight under it, the hind feet brought forward under the hip, a long
neck carried upright) and then every part is its own: one skin from the back of the skull to
the rump (a deep chest, withers, a tucked waist, a high croup); a narrow wedge of a head with
a deer's muzzle, big eyes set at the sides, large cupped ears on the wolf's ear bones; legs
with a knee and a hock, long cannon bones, a fetlock, a cloven hoof and dew-claws; a short
tail; and antlers, which are the line's event.

Three Paths are three deer (a form's `deer`): `red`, the red stag (a maned neck, heavy before,
its beams swept up and back to a crown of points); `wood`, the forest giant (high withers and
a sloping back, a long face with a heavy nose, a bell at the throat, palmate antlers);
`white`, the white-tail (slender, a long upright neck, great ears, a flag of a tail, its beams
curving forward like the ribs of a basket).

Its slots (data/genius-bases/stag.json):

  deer      red, wood, white
  stance    how it carries its neck, made before its flesh is laid (CRANES)
  build     legs, neck, body (the frame); chest, girth, waist, nape, head, muzzle, ears,
            withers, croup, antlers (the flesh)
  crown     the shape of its antlers (ANTLERS); horn, what they are made of; hung, what is in them
  marks     where it wears its Path's colour: neck, mane, saddle, blanket, dorsal, stripes, bib,
            throat, rump, belly, stockings, socks, bands, blaze, mask, ears, dapple, tines,
            burrs (a step of the colour after a colon)
  ears      one, laid, droop, torn
  eyes      far, old, third, shut
  tail      flag, down
  neck      mane, bell, ivy, garland, teeth
  maw       open
  throat, breath, hide, back, legs, flank, chest, armor
  pose      low, high, nod, back, aside, tilt (put on last)
  rest      the Wolf's ways of resting that a deer has: point, stride, lie

The wolf's own spine, paws, carry and aura still grow on it.
"""
import math
import os
import sys

import bpy  # noqa: F401  (Blender's module first: mathutils comes with it)
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE, STAND  # noqa: E402

gl = None       # genius_lines as it is running (register sets it)
_S = {}         # the form being built: its spec, its stations, its rack

PALETTE.update({
    "leaf": ((0.15, 0.21, 0.1), 0.9, 0.0), "moss": ((0.2, 0.29, 0.12), 1.0, 0.0), "weed": ((0.1, 0.19, 0.13), 0.6, 0.0),
    "petal": ((0.78, 0.72, 0.62), 0.6, 0.0), "bark": ((0.13, 0.095, 0.065), 0.95, 0.0), "bark_light": ((0.27, 0.2, 0.13), 0.95, 0.0),
    "velvet": ((0.27, 0.18, 0.12), 1.0, 0.0), "lichen": ((0.56, 0.6, 0.46), 0.9, 0.0), "ash": ((0.5, 0.49, 0.47), 1.0, 0.0),
    "ribbon_a": ((0.32, 0.1, 0.08), 0.9, 0.0), "ribbon_b": ((0.13, 0.19, 0.3), 0.9, 0.0), "ribbon_c": ((0.33, 0.27, 0.09), 0.9, 0.0),
    "earth": ((0.1, 0.075, 0.055), 1.0, 0.0), "wet": ((0.06, 0.055, 0.05), 0.25, 0.0), "knee": ((0.42, 0.41, 0.4), 0.9, 0.0),
    # antler: the beam is the brown of a rubbed antler and its points are polished pale
    "antler": ((0.42, 0.31, 0.2), 0.55, 0.0), "antler_tip": ((0.82, 0.76, 0.62), 0.4, 0.0), "antler_pale": ((0.8, 0.77, 0.7), 0.45, 0.0),
    "antler_dark": ((0.1, 0.08, 0.07), 0.45, 0.0), "antler_ice": ((0.62, 0.74, 0.8), 0.15, 0.0), "antler_stone": ((0.37, 0.38, 0.41), 0.85, 0.0),
    "antler_wood": ((0.24, 0.17, 0.1), 0.95, 0.0), "hide_tear": ((0.05, 0.04, 0.04), 0.7, 0.0),
})

NECK = ("Neck1", "Neck2", "Neck3")
N_CHAIN = ("Torso3", "Neck1", "Neck2", "Neck3", "Head")


def log(*a):
    print("[lines_stag]", *a)


# ======================================================================================
# Small things
# ======================================================================================

def _add(r, name, geo, weights, material, smooth=None):
    """A piece joined to the body; what it covers of the body's faces is kept by its name."""
    n0 = len(r.mesh.data.polygons)
    gl._add(r, name, geo, weights, material, smooth)
    _S.setdefault("parts", {})[name] = (n0, len(r.mesh.data.polygons))


def _head_bones(r):
    return r.family("Head", "Ear1.L", "Ear1.R")


def _perp(d):
    """Across a direction: (to the left, to the back of it)."""
    d = V(d).normalized()
    u = X - d * X.dot(d)
    u = u.normalized() if u.length > 1e-4 else Y.copy()
    v = Z - d * Z.dot(d)
    v = v.normalized() if v.length > 0.2 else (Y - d * Y.dot(d)).normalized()
    return u, v


def _hoop(centre, normal, radius, thick=0.02, n=16, sides=4):
    u, v = _perp(normal)
    pts = [V(centre) + (u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n)) * radius for i in range(n + 1)]
    return g.tube(pts, [thick] * (n + 1), n=sides, caps=False)


def _cr(pts, n=3):
    """A smooth line through points (Catmull-Rom), n steps to a span (or a list: steps for each)."""
    pts = [V(p) for p in pts]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        steps = n if isinstance(n, int) else n[i - 1]
        for k in range(steps):
            t = k / steps
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1].copy())
    return out


def _frames(line):
    """[(point, the way it runs, its left, its top)] along a line, carried without a twist."""
    out, prev = [], None
    n = len(line)
    for i, p in enumerate(line):
        d = line[min(i + 1, n - 1)] - line[max(i - 1, 0)]
        d = d.normalized() if d.length > 1e-7 else (prev[0].copy() if prev else Y.copy())
        if prev is None:
            u, v = _perp(d)
        else:
            q = prev[0].rotation_difference(d)
            u = q @ prev[1]
            u = (u - d * u.dot(d)).normalized()
            v = q @ prev[2]
            v = (v - d * v.dot(d) - u * v.dot(u)).normalized()
        prev = (d, u, v)
        out.append((V(p), d, u, v))
    return out


def _chain_w(names, joints, p):
    """Which bones of a chain carry a point: names[i] runs from joints[i] to joints[i + 1]."""
    best, s = 1e9, 0.0
    for i in range(len(joints) - 1):
        a, ab = joints[i], joints[i + 1] - joints[i]
        f = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
        dist = (p - (a + ab * f)).length
        if dist < best - 1e-7:
            best, s = dist, i + f
    ws = [(nm, max(0.0, 1.0 - abs(s - (j + 0.5)))) for j, nm in enumerate(names)]
    tot = sum(w for _, w in ws)
    if tot < 1e-6:
        return [(names[0] if s < 1 else names[-1], 1.0)]
    return [(nm, w / tot) for nm, w in ws if w > 1e-4]


def _ring(c, u, v, a, b, m=14, crest=0.0, keel=0.0, egg=0.0):
    """Points round a section, from its left over its top: a across, b up and down; crest draws
    its top to a ridge, keel its underside; egg makes it broadest below its middle."""
    out = []
    for j in range(m):
        th = 2 * math.pi * j / m
        cs, sn = math.cos(th), math.sin(th)
        up, dn = max(0.0, sn), max(0.0, -sn)
        k = 1.0 + crest * up ** 6 + keel * dn ** 6
        wide = 1.0 - 0.25 * crest * up ** 2 - 0.3 * keel * dn ** 2 - egg * up ** 1.5 + 0.5 * egg * dn * (1.0 - dn)
        out.append(c + u * (a * cs * wide) + v * (b * sn * k))
    return out


def _along(pts, t):
    """The point a share t of the way along a line through points."""
    lens = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    want = max(0.0, min(1.0, t)) * sum(lens)
    for i, L in enumerate(lens):
        if want <= L or i == len(lens) - 1:
            return pts[i].lerp(pts[i + 1], want / L if L > 1e-9 else 0.0)
        want -= L
    return pts[-1]


def _slot(r, material):
    me = r.mesh.data
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    return [m.name for m in me.materials].index(material.name)


def _paint(r, part, pick, material):
    """Of a named piece's faces, those that pass pick(centre, normal) take a material."""
    if part not in _S.get("parts", {}):
        return 0
    n0, n1 = _S["parts"][part]
    slot = _slot(r, material)
    R = r.M.to_3x3()
    polys = r.mesh.data.polygons
    n = 0
    for i in range(n0, n1):
        p = polys[i]
        if pick(r.M @ p.center, (R @ p.normal).normalized()):
            p.material_index = slot
            n += 1
    return n


def _am(step=""):
    return mat("accent" + ("_" + step if step else ""))


def _station(c):
    """The place along its body (of _S["body"]) nearest a point."""
    return min(_S["body"], key=lambda s: (s[0] - c).length_squared)


def _on(s, deg, lift=0.0):
    """A point on its skin at one place along it, deg round from its left over its top (90 its
    back, 270 its belly), and the way the skin faces there."""
    p, d, u, v, a, b = s[:6]
    th = math.radians(deg)
    cs, sn = math.cos(th), math.sin(th)
    n = (u * (cs / max(1e-6, a)) + v * (sn / max(1e-6, b))).normalized()
    return p + u * (a * cs) + v * (b * sn) + n * lift, n


def _back(y):
    """The height of its back at y, and the breadth of its barrel there."""
    tr = _S["trunk"]
    if y <= tr[0][0]:
        return tr[0][1], tr[0][3]
    for a, b in zip(tr, tr[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / max(1e-6, b[0] - a[0])
            return a[1] + (b[1] - a[1]) * t, a[3] + (b[3] - a[3]) * t
    return tr[-1][1], tr[-1][3]


def _flank(y, z):
    """How far its flank reaches out at (y, z)."""
    tr = _S["trunk"]
    row = min(tr, key=lambda q: abs(q[0] - y))
    zc, hb = (row[1] + row[2]) / 2, (row[1] - row[2]) / 2
    return row[3] * math.sqrt(max(0.05, 1.0 - min(1.0, abs(z - zc) / max(1e-6, hb)) ** 2))


# ======================================================================================
# The frame: the wolf's bones stood as a deer stands
# ======================================================================================

# what each of the three deer is, against the red stag
KINDS = {
    "red": dict(neck=1.5, nape=1.12, withers=0.0, croup=0.0, slope=0.0, girth=1.0, legs=1.0, muzzle=1.0, nose=1.0, ears=1.0, bell=0.0, tail="down", stance="alert"),
    "wood": dict(neck=1.3, nape=1.3, withers=0.2, croup=-0.12, slope=0.1, girth=1.08, legs=1.1, muzzle=1.22, nose=1.6, ears=0.95, bell=1.0, tail="stub", stance="level"),
    "white": dict(neck=1.5, nape=0.86, withers=-0.04, croup=0.03, slope=0.0, girth=0.88, legs=1.02, muzzle=0.95, nose=0.9, ears=1.3, bell=0.0, tail="flag", stance="watch"),
}

# how it carries its neck: how steeply each of its three lengths rises, and how far its face
# falls below the level (degrees)
CRANES = {
    "alert": (48, 58, 62, 26), "proud": (56, 68, 76, 32), "watch": (60, 70, 76, 18), "level": (28, 34, 38, 24),
    "tilt": (6, -4, -12, 66), "low": (20, 14, 8, 40), "bell": (52, 46, 36, -16), "graze": (-22, -40, -52, 72),
    "sky": (58, 70, 80, -34), "bow": (40, 30, 10, 58), "reach": (34, 26, 18, 8),
}

# its age, by its stage: the fawn is all leg, eye and ear; the Final is deep before
AGES = {
    1: dict(head=1.26, muzzle=0.72, eye=1.4, ears=1.3, neck=0.72, nape=0.8, body=0.76, depth=0.72, girth=0.8, knee=1.25, wide=0.82),
    2: dict(head=1.1, muzzle=0.92, eye=1.15, ears=1.1, neck=0.9, nape=0.9, body=0.94, depth=0.92, girth=0.9, knee=1.08, wide=0.92),
    3: dict(head=1.0, muzzle=1.0, eye=1.0, ears=1.0, neck=1.0, nape=1.0, body=1.0, depth=1.0, girth=1.0, knee=1.0, wide=1.0),
    4: dict(head=0.97, muzzle=1.0, eye=0.95, ears=0.95, neck=1.0, nape=1.12, body=1.02, depth=1.06, girth=1.06, knee=1.0, wide=1.06),
}


def _crane(r, pitches):
    """Carry the neck so: each of its three lengths at its pitch."""
    head = _head_bones(r)
    for i in range(3):
        a, b = r.bone(N_CHAIN[i + 1]), r.bone(N_CHAIN[i + 2])
        now = math.degrees(math.atan2(b.z - a.z, a.y - b.y))
        turn = pitches[i] - now
        if abs(turn) > 0.01:
            r.rotate(list(NECK[i:]) + head, a, X, -math.radians(turn))


def frame(r):
    """The wolf's bones, stood as a deer. (The flesh is laid on them by measure.)"""
    r.arm.data.pose_position = "REST"       # built at rest, as the Wolf is: what rides a bone is put where the bone rests
    bpy.context.view_layer.update()
    K, age = _S["K"], _S["age"]
    head = _head_bones(r)
    r.leg_length(-0.5 * K["legs"])
    # its legs straight under it: the hind feet brought forward under the hip (a wolf stands
    # with its hocks far out behind), the fore feet under the elbow, and a narrower track
    for tag in ("fl", "fr", "bl", "br"):
        side = ".L" if tag[1] == "l" else ".R"
        sg = 1 if tag[1] == "l" else -1
        root = r.bone(("FrontUpperLeg" if tag[0] == "f" else "BackLeg") + side)
        bones = [b for b in r.legs(tag) if not b.startswith("PoleTarget")]
        k = 0.5 if tag[0] == "f" else 0.6
        r.deform(bones, lambda p, y0=root.y, k=k, sg=sg: Vector((p.x - sg * 0.05, y0 + (p.y - y0) * k, p.z)))
    r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, 1.26 * age["body"])
    r.lengthen_chain(list(NECK), head, K["neck"] * age["neck"])
    stance = gl.opt(_S["spec"].get("stance"))[0] or K["stance"]
    _S["crane"] = CRANES[stance]
    _crane(r, _S["crane"])
    r.scale(r.family("Tail1"), r.bone("Tail1"), 0.3)


def ages(r, level):
    pass        # its age is in its flesh (AGES)


def _strip(r):
    """Take the wolf's own skin away: every face of it."""
    import bmesh
    me = r.mesh.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=list(bm.verts), context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()


# ======================================================================================
# The flesh
# ======================================================================================

def _body(r, A):
    """One skin from the back of its skull to its rump: a neck deep where it leaves the chest
    and fine under the jaw; withers; a chest as deep as the elbow; a waist tucked up behind
    it; a croup as high as the withers, falling to the tail."""
    sp, K, age = _S["spec"], _S["K"], _S["age"]
    b = sp.get("build", {})
    chest = float(b.get("chest", 1.0))
    girth = float(b.get("girth", 1.0)) * K["girth"]
    waist = float(b.get("waist", 1.0))
    nape = float(b.get("nape", 1.0)) * K["nape"] * age["nape"]
    sh, el, hip = r.bone("FrontUpperLeg.L"), r.bone("FrontLowerLeg.L"), r.bone("BackLeg.L")
    ysh, yhip = sh.y, hip.y
    W0 = sh.z + 0.8                                   # the withers of a plain deer on these legs
    W = W0 + K["withers"] + float(b.get("withers", 0.0))
    D = (W0 - (el.z - 0.05)) * age["depth"] * (1.0 + 0.16 * (chest - 1.0))
    B = W0 - D                                        # the brisket
    cr = K["croup"] + float(b.get("croup", 0.0))
    cw = chest ** 0.7 * age["wide"]
    gw = girth ** 0.8 * age["wide"]
    mid = (ysh + yhip) / 2
    tuck = (0.3 + 0.5 * (1.0 - waist)) * age["depth"]
    # the trunk: (y, its top, its underside, its half-breadth, crest, keel, egg)
    TR = [
        (ysh + 0.1, W, B + 0.02, 0.34 * cw, 0.05, 0.22, 0.12),
        (ysh + 0.5, W - 0.08 - 0.5 * K["withers"], B, 0.44 * cw * gw ** 0.5, 0.1, 0.1, 0.1),
        (mid + 0.12, W - 0.11 - 0.9 * K["withers"] + 0.3 * cr, B + 0.12 * tuck / 0.3, 0.47 * gw, 0.04, 0.0, 0.1),
        (yhip - 0.38, W - 0.13 - K["withers"] + 0.7 * cr, B + tuck, 0.39 * gw * waist ** 0.6, 0.05, 0.0, 0.0),
        (yhip - 0.02, W - 0.04 - K["withers"] + cr, B + tuck + 0.06, 0.41 * gw ** 0.6, 0.1, 0.0, -0.08),
        (yhip + 0.28, W - 0.17 - K["withers"] + cr, B + tuck + 0.02, 0.31 * gw ** 0.5, 0.0, 0.0, 0.0),
        (yhip + 0.44, W - 0.5 - K["withers"] + cr, B + tuck + 0.2, 0.14, 0.0, 0.0, 0.0),
    ]
    _S["trunk"] = TR
    _S["W"], _S["B"], _S["W0"], _S["ysh"], _S["yhip"] = W, B, W0, ysh, yhip
    trunk = [(Vector((0, y, (zt + zb) / 2)), a, (zt - zb) / 2, c, k, e) for y, zt, zb, a, c, k, e in TR]
    # where the neck leaves the chest: from before the withers down to the breast
    wf = Vector((0, ysh - 0.2, W - 0.06 - 0.3 * K["withers"]))
    br = Vector((0, ysh - 0.44 * (1.0 + 0.2 * (chest - 1.0)), B + 0.3))
    base = ((wf + br) / 2, 0.29 * cw * nape ** 0.3, (wf - br).length / 2, 0.0, 0.12, 0.0)
    # the neck: its joints
    J = [r.bone(nm) for nm in N_CHAIN[1:]]
    fj = _frames([base[0]] + J[1:])
    neck = []
    for (p, d, u, v), a, bb, off in zip(fj[1:], (0.215, 0.175, 0.145), (0.34, 0.25, 0.2), (0.3, 0.2, 0.1)):
        k = nape if bb > 0.2 else nape ** 0.5
        neck.append((p - v * (off * bb * k), a * k ** 0.6, bb * k, 0.05, 0.0, 0.0))
    inn = (J[3] + (J[3] - J[2]).normalized() * 0.14 - fj[-1][3] * 0.02, 0.1, 0.12, 0.0, 0.0, 0.0)
    ctrl = [inn] + list(reversed(neck)) + [base] + trunk
    steps = [2, 3, 3, 3, 3] + [2, 2, 2, 2, 2, 1]
    line = _cr([c[0] for c in ctrl], steps)
    size, shape, zone = [], [], []
    for i, n in enumerate(steps):
        for k in range(n):
            f = k / n
            size.append((ctrl[i][1] + (ctrl[i + 1][1] - ctrl[i][1]) * f, ctrl[i][2] + (ctrl[i + 1][2] - ctrl[i][2]) * f))
            shape.append(tuple(ctrl[i][q] + (ctrl[i + 1][q] - ctrl[i][q]) * f for q in (3, 4, 5)))
            zone.append("neck" if i < 4 else "back")
    size.append((ctrl[-1][1], ctrl[-1][2]))
    shape.append(ctrl[-1][3:6])
    zone.append("back")
    nj = [base[0]] + J + [J[3] + (J[3] - J[2]) * 0.5]
    fr = _frames(line)
    rings, ws, body = [], [], []
    m = 14
    nn = zone.count("neck")
    for i, (p, d, u, v) in enumerate(fr):
        a, bb = max(0.01, size[i][0]), max(0.01, size[i][1])
        if zone[i] == "neck":
            w = _chain_w(N_CHAIN, nj, p)
            t = 1.0 - i / max(1, nn)                    # 0 at the chest, 1 under the skull
        else:
            w = r.spine_weights(p.y)
            t = (i - nn) / max(1, len(fr) - nn - 1)     # 0 at the withers, 1 at the tail
        rings.append(_ring(p, u, v, a, bb, m=m, crest=shape[i][0], keel=shape[i][1], egg=shape[i][2]))
        ws.extend([w] * m)
        body.append((p, d, u, v, a, bb, w, zone[i], t))
    _S["body"] = body
    _S["neckline"] = [s for s in body if s[7] == "neck"]
    _add(r, "body", g.loft(rings, caps=True), ws, mat("hide_red"), smooth=True)
    cream = mat("fur_cream")
    # its underside, the patch round its tail and the patch at its throat are pale
    _paint(r, "body", lambda c, n: _station(c)[7] == "back" and n.dot(_station(c)[3]) < -0.62 and c.y > ysh + 0.2, cream)
    _paint(r, "body", lambda c, n: c.y > yhip + 0.16 and n.y > 0.3 and c.z > B + tuck + 0.12, cream)
    _paint(r, "body", lambda c, n: _station(c)[7] == "neck" and 0.62 < _station(c)[8] < 0.95 and n.dot(_station(c)[3]) < -0.45, cream)
    _paint(r, "body", lambda c, n: _station(c)[7] == "back" and 0.1 < _station(c)[8] < 0.62 and n.dot(_station(c)[3]) > 0.6, kit.mark("saddle", mat("hide_red")))


def _limb(st, n=8):
    """Rings down a leg: each (centre, half-breadth across it, half-depth fore and aft)."""
    line = [V(c) for c, _, _ in st]
    rings = []
    for i, (c, rx, ry) in enumerate(st):
        d = (line[min(i + 1, len(line) - 1)] - line[max(i - 1, 0)]).normalized()
        v = d.cross(X)
        v = v.normalized() if v.length > 1e-5 else Y.copy()
        rings.append([V(c) + X * (rx * math.cos(2 * math.pi * k / n)) + v * (ry * math.sin(2 * math.pi * k / n)) for k in range(n)])
    return rings


def _hoof(x, y, k=1.0, splay=1.0):
    """A cloven hoof: two toes pointed before, and two dew-claws behind the fetlock."""
    geo = None
    for sx in (1, -1):
        dx = sx * 0.034 * k * splay
        geo = g.merge(geo, g.tube([(x + dx, y + 0.05 * k, 0.17 * k), (x + dx * 1.2, y - 0.03 * k, 0.085 * k), (x + dx * 1.35 * splay, y - 0.13 * k, 0.03 * k)],
                                  [0.04 * k, 0.05 * k, 0.026 * k], n=6))
        geo = g.merge(geo, g.cone((x + dx * 0.9, y + 0.07 * k, 0.3 * k), (x + dx * 1.3, y + 0.12 * k, 0.17 * k), 0.022 * k, n=4))
    return geo


def _legs(r, A):
    """Four legs of a deer: the forearm and the gaskin lean, a knee and a hock that show, long
    cannon bones, a fetlock, a pastern sloping to a small cloven hoof."""
    sp, K, age = _S["spec"], _S["K"], _S["age"]
    gk = 1.3 * float(sp.get("build", {}).get("girth", 1.0)) ** 0.7 * K["girth"] ** 0.5 * age["girth"]
    kn = age["knee"]
    hoofk = float(sp.get("build", {}).get("hooves", 1.0))
    splay = 1.5 if _has("legs", "feather") or hoofk > 1.2 else 1.0
    socks = kit.mark("socks", mat("hide_red"))
    cream = mat("fur_cream")
    _S["legs"] = {}
    for tag in ("fl", "fr", "bl", "br"):
        side = ".L" if tag[1] == "l" else ".R"
        sg = 1 if tag[1] == "l" else -1
        if tag[0] == "f":
            sh, el, ft = r.bone("FrontUpperLeg" + side), r.bone("FrontLowerLeg" + side), r.bone("IKFrontLeg" + side)
            x, yf = el.x, ft.y + 0.03
            zk = el.z * 0.5
            yk = el.y + (yf - el.y) * 0.5 - 0.02
            zf = 0.31
            st = [
                (Vector((x * 0.85, sh.y, sh.z + 0.18)), 0.17, 0.3),
                (Vector((x, el.y + 0.04, el.z + 0.1)), 0.135 * gk, 0.22 * gk),
                (Vector((x, el.y + (yk - el.y) * 0.35 + 0.01, el.z - 0.3 * (el.z - zk))), 0.092 * gk, 0.125 * gk),
                (Vector((x, yk + 0.005, zk + 0.16)), 0.062 * gk, 0.074 * gk),
                (Vector((x, yk - 0.012, zk)), 0.068 * gk * kn, 0.08 * gk * kn),
                (Vector((x, yk + 0.004, zk - 0.15)), 0.048 * gk, 0.056 * gk),
                (Vector((x, yf + 0.03, zf + 0.22)), 0.044 * gk, 0.05 * gk),
                (Vector((x, yf + 0.04, zf)), 0.056 * gk, 0.066 * gk),
                (Vector((x, yf, 0.15 * hoofk)), 0.05 * gk, 0.056 * gk),
            ]
            names, joints = ["FrontUpperLeg" + side, "FrontLowerLeg" + side], [sh, el, Vector((x, yf, 0.0))]
            zsock = zk + 0.1
        else:
            hp, sf, hk, ft = r.bone("BackLeg" + side), r.bone("BackUpperLeg" + side), r.bone("BackLowerLeg" + side), r.bone("IKBackLeg" + side)
            x, yf = sf.x, ft.y - 0.02
            zf = 0.31
            st = [
                (Vector((x * 0.8, hp.y + 0.04, hp.z + 0.12)), 0.19, 0.36),
                (Vector((x * 0.95, hp.y + (sf.y - hp.y) * 0.55 + 0.12, hp.z + (sf.z - hp.z) * 0.55)), 0.17 * gk, 0.33 * gk),
                (Vector((x, sf.y + 0.1, sf.z)), 0.125 * gk, 0.2 * gk),
                (sf.lerp(hk, 0.42) + Vector((0, 0.03, 0)), 0.088 * gk, 0.125 * gk),
                (sf.lerp(hk, 0.8), 0.058 * gk, 0.078 * gk),
                (hk + Vector((0, 0.012, 0.0)), 0.062 * gk * kn, 0.092 * gk * kn),
                (hk.lerp(Vector((x, yf + 0.05, zf)), 0.22), 0.048 * gk, 0.058 * gk),
                (hk.lerp(Vector((x, yf + 0.05, zf)), 0.62), 0.044 * gk, 0.05 * gk),
                (Vector((x, yf + 0.05, zf)), 0.056 * gk, 0.066 * gk),
                (Vector((x, yf, 0.15 * hoofk)), 0.05 * gk, 0.056 * gk),
            ]
            names, joints = ["BackLeg" + side, "BackUpperLeg" + side, "BackLowerLeg" + side], [hp, sf, hk, Vector((x, yf, 0.0))]
            zsock = hk.z + 0.1
        rings = _limb(st)
        ws = [_chain_w(names, joints, c) for c, _, _ in st for _ in range(8)]
        _add(r, "leg_" + tag, g.loft(rings, caps=True), ws, mat("hide_red"), smooth=True)
        _paint(r, "leg_" + tag, lambda c, n, zs=zsock: c.z < zs, socks)
        _paint(r, "leg_" + tag, lambda c, n, zs=zsock, sg=sg: c.z >= zs and n.x * sg < -0.55, cream)
        _add(r, "hoof_" + tag, _hoof(x, yf, hoofk, splay), names[-1], mat("horn"), smooth=False)
        _S["legs"][tag] = dict(x=x, y=yf, zsock=zsock, top=st[1][0].z, bone=names[-1], knee=st[4][0] if tag[0] == "f" else st[5][0], fet=zf)


def _head(r, A):
    """Its head: a narrow wedge, deep at the jaw and fine at the muzzle, a dark pad to its nose
    and a pale chin; eyes at the sides of it, large, with a lid and a tear-line; great cupped
    ears on the wolf's ear bones."""
    sp, K, age, level = _S["spec"], _S["K"], _S["age"], _S["level"]
    b = sp.get("build", {})
    S = 1.0 * age["head"] * float(b.get("head", 1.0))
    mz = K["muzzle"] * age["muzzle"] * float(b.get("muzzle", 1.0))
    nz = K["nose"]
    hb = r.bone("Head")
    phi = math.radians(_S["crane"][3])
    f = Vector((0, -math.cos(phi), -math.sin(phi)))       # toward its nose
    up = Vector((0, -math.sin(phi), math.cos(phi)))       # out of the top of its head

    def P(x, a, h):
        return hb + (X * x + f * a + up * h) * S
    _S["P"], _S["HS"], _S["hf"], _S["hup"] = P, S, f, up
    a0 = 0.34                                              # the eye; before it the muzzle is drawn out or kept short
    m = lambda a: a0 + (a - a0) * mz                       # noqa: E731
    yn = m(0.74)
    # along it from the poll: (how far forward, its top, its underside, its half-breadth)
    SK = [(-0.05, 0.05, -0.1, 0.09), (0.05, 0.15, -0.19, 0.15), (0.2, 0.18, -0.25, 0.172), (a0, 0.155, -0.235, 0.165),
          (m(0.47), 0.105, -0.19, 0.122), (m(0.6), 0.068, -0.15 - 0.02 * (nz - 1), 0.09 + 0.012 * (nz - 1)),
          (m(0.7), 0.05 + 0.018 * (nz - 1), -0.13 - 0.05 * (nz - 1), 0.08 + 0.03 * (nz - 1)),
          (yn, 0.03 + 0.012 * (nz - 1), -0.115 - 0.05 * (nz - 1), 0.066 + 0.03 * (nz - 1)),
          (yn + 0.045, -0.012, -0.085 - 0.04 * (nz - 1), 0.04 + 0.02 * (nz - 1))]
    rings = []
    mm = 10
    for a, zt, zb, w in SK:
        zc, hh = (zt + zb) / 2 + 0.02, (zt - zb) / 2
        ring = []
        for j in range(mm):
            th = 2 * math.pi * j / mm
            cs, sn = math.cos(th), math.sin(th)
            ring.append(P(w * math.copysign(abs(cs) ** 0.8, cs) * (1.0 - 0.22 * max(0.0, -sn)), a, zc - 0.02 + hh * math.copysign(abs(sn) ** 0.85, sn)))
        rings.append(ring)
    _add(r, "head", g.loft(rings, caps=True), "Head", mat("hide_red"), smooth=True)
    cream = mat("fur_cream")
    _paint(r, "head", lambda c, n: n.dot(up) < -0.5 and (c - hb).dot(f) > 0.16 * S, cream)                 # its chin and jaw
    _paint(r, "head", lambda c, n: m(0.585) * S < (c - hb).dot(f) < m(0.7) * S and n.dot(up) < 0.6, cream)  # a pale band behind its nose
    _paint(r, "head", lambda c, n: n.dot(up) > 0.7 and 0.2 * S < (c - hb).dot(f) < m(0.62) * S, kit.mark("mask", mat("hide_red")))
    _S["skull"] = P(0, 0.12, 0.17)
    # the pad of its nose, its nostrils, the line of its mouth
    nw = SK[-2][3]
    _add(r, "nose_pad", g.ico(P(0, yn + 0.022, -0.012 + 0.012 * (nz - 1)), 1.0, sub=1, scale=(nw * 0.95 * S, 0.05 * S, (0.05 + 0.02 * (nz - 1)) * S), rot=(-phi, 0, 0)), "Head", mat("nose"), smooth=True)
    geo = None
    for sg in (1, -1):
        pts = [P(sg * SK[i][3] * 0.9, SK[i][0], SK[i][2] + 0.062 + 0.012 * (i - 4)) for i in (4, 5, 6, 7)]
        geo = g.merge(geo, g.tube(pts, [0.005, 0.009, 0.009, 0.005], n=4))
    if gl.opt(sp.get("maw"))[0] != "open":
        _add(r, "mouth", geo, "Head", mat("nose"), smooth=True)
    else:                         # it bells: the lower jaw dropped, the dark of its mouth
        jaw = [[P(sg * w, a, h) for sg, w, h in ((1, 0.8 * SK[i][3], -0.02), (1, 0.6 * SK[i][3], -0.07), (-1, 0.6 * SK[i][3], -0.07), (-1, 0.8 * SK[i][3], -0.02))]
               for i, a in ((4, SK[4][0]), (6, SK[6][0]), (7, SK[7][0] - 0.01))]
        hinge = P(0, SK[4][0], SK[4][2] + 0.05)
        Rj = Matrix.Rotation(-0.42, 3, X)
        drop = [[hinge + Rj @ (q - hinge) - up * 0.05 * S for q in ring] for ring in jaw]
        _add(r, "jaw", g.loft(drop, caps=True), "Head", cream, smooth=True)
        _add(r, "maw", g.ico(P(0, m(0.6), -0.13), 1.0, sub=1, scale=(0.06 * S, 0.14 * S * mz, 0.035 * S), rot=(-phi + 0.2, 0, 0)), "Head", mat("hide_maw"), smooth=True)
    # the eyes
    style = gl.opt(sp.get("eyes"))[0]
    Re = 0.068 * S * age["eye"] * (1.12 if style == "far" else 1.0)
    dark = mat("fur_mask")
    eye_m = {"iris": field("eyes", 3.4), "pupil": mat("eye_dark"), "glint": mat("eye_white")}
    lidk = {"old": 0.42, "shut": 0.9, "far": 0.0}.get(style, 0.16 if level > 1 else 0.0)
    for sg, tag in ((1, "l"), (-1, "r")):
        s = P(sg * 0.158, a0 - 0.02, 0.07)
        out = (X * sg * 0.9 + f * 0.3 + up * 0.26).normalized()
        c = s - out * (Re * 0.42)
        look = (X * sg * 0.72 + f * 0.62 + up * 0.1).normalized()
        ball, kinds = gl._eyeball(c, Re, look, up * 0.8 + f * 0.4, math.radians(44 if level > 1 else 50))
        gl._later(r, "blink", "eye", None, c, "Head", side=tag, solid=(ball, [eye_m[k] for k in kinds]))
        # a pale ring round it, a lid over it, the tear-line before it
        _add(r, "eye_ring_" + tag, gl._lens(s - out * 0.012, out, f, out.cross(f), Re * 1.5, Re * 1.3, Re * 0.2), "Head", cream if style != "old" else mat("fur_pale"), smooth=True)
        if lidk > 0.0:
            lu = (up * 0.9 - f * 0.25 + out * 0.2).normalized()
            _add(r, "lid_" + tag, gl._lid(c, Re * 1.1, lu, math.acos(max(-0.6, min(0.97, 0.9 * (1.0 - 2.0 * lidk) / 1.1)))), "Head", dark, smooth=True)
        t0 = s + f * (Re * 1.25) - up * (Re * 0.5)
        _add(r, "tear_" + tag, g.blade(t0 - out * 0.004, t0 + f * (0.12 * S) - up * (0.05 * S) - X * sg * 0.022 * S - out * 0.004, 0.035 * S, normal=out, belly=0.35), "Head", mat("hide_tear"), smooth=True)
    A.eye = P(0.158, a0 - 0.02, 0.07)
    A.eye_r, A.eye_n = Re, (X * 0.9 + f * 0.3 + up * 0.26).normalized()
    A.nose = P(0, yn + 0.04, -0.03)
    # the ears: each a cupped leaf, standing out and up from behind the eye; the wolf's ear
    # bones are laid along them, so they flick as its did
    ek = K["ears"] * age["ears"] * float(b.get("ears", 1.0))
    how = gl.opt(sp.get("ears"))[0]
    for sg, tag, side in ((1, "l", ".L"), (-1, "r", ".R")):
        root = P(sg * 0.135, 0.095, 0.1)
        d = (X * sg * 0.86 + up * 0.46 - f * 0.22).normalized()
        op = (f * 0.75 + X * sg * 0.45 + up * 0.1)             # the way its cup opens
        L = 0.52 * S * ek
        if how == "one" and sg < 0:                            # one ear turned behind
            d = (X * sg * 0.5 + up * 0.5 - f * 0.72).normalized()
            op = (-f * 0.6 + X * sg * 0.7)
        elif how == "laid":
            d = (X * sg * 0.3 + up * 0.25 - f * 0.92).normalized()
            op = (X * sg * 0.8 + up * 0.5)
        elif how == "droop":
            d = (X * sg * 0.9 - up * 0.42 - f * 0.1).normalized()
            op = (f * 0.7 - up * 0.6)
        elif how == "torn" and sg < 0:
            L *= 0.55
        op = (op - d * op.dot(d)).normalized()
        es = d.cross(op).normalized()
        prof = ((0.0, 0.5), (0.14, 0.82), (0.36, 1.0), (0.62, 0.84), (0.84, 0.48), (1.0, 0.06))
        rings = []
        for t, wk in prof:
            c = root + d * (L * t) + op * (0.03 * S * math.sin(math.pi * t))
            hw, cup = 0.14 * S * ek ** 0.5 * wk, 0.08 * S * wk
            rings.append([c - es * hw, c - es * hw * 0.62 - op * cup, c - op * cup * 1.25, c + es * hw * 0.62 - op * cup, c + es * hw, c - op * cup * 0.2])
        # the wolf's ear bones, laid along it
        fam = r.family("Ear1" + side)
        old = [r.bone(nm) for nm in fam]
        d0 = (old[-1] - old[0])
        Rm = d0.normalized().rotation_difference(d).to_matrix()
        kL = L * 0.8 / max(1e-6, d0.length)
        r.deform(fam, lambda p, o=old[0], Rm=Rm, kL=kL, root=root: root + Rm @ (p - o) * kL, rot=Rm)
        joints = [r.bone(nm) for nm in fam] + [root + d * L]
        ws = [_chain_w(fam, joints, q) for ring in rings for q in ring]
        _add(r, "ear_" + tag, g.loft(rings, caps=True), ws, mat("hide_red"), smooth=True)
        _paint(r, "ear_" + tag, lambda c, n, op=op: n.dot(op) > 0.25, cream)
        _S.setdefault("ear_in", []).append(("ear_" + tag, op))


def _tail(r, A):
    """A short tail: a leaf of fur, dark above and pale under; a white-tail's is a flag."""
    sp, K = _S["spec"], _S["K"]
    how = gl.opt(sp.get("tail"))[0] or K["tail"]
    tr = _S["trunk"]
    root = Vector((0, tr[-2][0] + 0.1, tr[-2][1] - 0.12))
    # the wolf's tail bones, brought to it
    fam = r.family("Tail1")
    t1 = r.bone("Tail1")
    r.deform(fam, lambda p: p + (root - t1))
    if how == "flag":             # carried straight up, its pale underside shown behind it
        pts = [root, root + Vector((0, 0.1, 0.2)), root + Vector((0, 0.13, 0.46)), root + Vector((0, 0.09, 0.66))]
        geo = g.tongue(pts, [0.16, 0.25, 0.23, 0.05], thick=0.3, normal=Y)
        _add(r, "tail", geo, "Tail1", mat("fur_cream"), smooth=True)
        _paint(r, "tail", lambda c, n: n.y < -0.2, kit.mark("tailtip", mat("hide_red")))
    else:
        L = 0.3 if how == "stub" else 0.42
        pts = [root + Vector((0, -0.05, 0.03)), root + Vector((0, 0.1, -0.06)), root + Vector((0, 0.15, -L * 0.6)), root + Vector((0, 0.13, -L))]
        geo = g.tongue(pts, [0.12, 0.19, 0.17, 0.04], thick=0.35, normal=Y)
        _add(r, "tail", geo, "Tail1", mat("fur_cream"), smooth=True)
        _paint(r, "tail", lambda c, n: n.y > 0.1, kit.mark("tailtip", mat("hide_red")))
    _S["tail_root"] = root


# ======================================================================================
# The antlers
# ======================================================================================
#
# A shape: beam, the points of the main beam from the pedicle, each (out, back, up); tines,
# each (how far along the beam, the way it points, how long[, how it curls up]); thick, against
# a plain antler; palm, (from, to, breadth, the way the palm spreads) for a palmate one, whose
# tines after `from` stand on the palm's edge; cut, {side: how far along} for a broken beam.
# Lengths are in heads (a head is 0.8 long).

ANTLERS = {
    # the red stag's: beams swept out, back and up, a brow tine over the face, a crown of points
    "spikes": dict(beam=[(0.1, 0.06, 0.3), (0.26, 0.02, 0.62), (0.34, -0.14, 0.92)], tines=[(0.22, (0.25, -1, 0.5), 0.34)], thick=1.25),
    "lock": dict(beam=[(0.22, 0.1, 0.34), (0.56, 0.2, 0.72), (0.8, 0.12, 1.2), (0.82, -0.14, 1.58)],
                 tines=[(0.08, (0.15, -1, 0.3), 0.6, 0.5), (0.3, (0.5, -0.9, 0.35), 0.5, 0.5), (0.58, (0.7, -0.6, 0.5), 0.46, 0.4), (0.84, (-0.3, -0.5, 0.9), 0.4)], thick=1.5),
    "royal": dict(beam=[(0.26, 0.12, 0.44), (0.72, 0.34, 0.94), (1.04, 0.44, 1.56), (1.06, 0.26, 2.16), (0.84, -0.06, 2.6)],
                  tines=[(0.05, (0.3, -1, 0.45), 0.74, 0.6), (0.17, (0.6, -1, 0.4), 0.56, 0.6), (0.42, (0.8, -0.7, 0.6), 0.62, 0.5),
                         (0.8, (0.9, -0.2, 0.7), 0.5), (0.9, (0.3, 0.7, 0.9), 0.46), (0.97, (-0.6, -0.4, 1), 0.44)], thick=1.5),
    "broken": dict(beam=[(0.26, 0.12, 0.44), (0.72, 0.34, 0.94), (1.04, 0.44, 1.56), (1.06, 0.26, 2.16), (0.84, -0.06, 2.6)],
                   tines=[(0.05, (0.3, -1, 0.45), 0.74, 0.6), (0.17, (0.6, -1, 0.4), 0.56, 0.6), (0.42, (0.8, -0.7, 0.6), 0.62, 0.5),
                          (0.8, (0.9, -0.2, 0.7), 0.5), (0.9, (0.3, 0.7, 0.9), 0.46), (0.97, (-0.6, -0.4, 1), 0.44)], thick=1.45, cut={1: 0.4}),
    "swept": dict(beam=[(0.14, 0.3, 0.26), (0.34, 0.9, 0.52), (0.46, 1.6, 0.66), (0.44, 2.2, 0.62)],
                  tines=[(0.1, (0.2, -0.6, 0.8), 0.3), (0.42, (0.4, 0.5, 0.9), 0.4), (0.68, (0.3, 0.6, 0.8), 0.36), (0.88, (0.5, 0.7, 0.6), 0.28)], thick=1.0),
    "plough": dict(beam=[(0.4, -0.1, 0.3), (0.9, -0.3, 0.62), (1.24, -0.5, 1.04), (1.36, -0.56, 1.5)],
                   tines=[(0.08, (0.1, -1, 0.1), 0.56, 0.2), (0.42, (0.2, -1, 0.0), 0.4, 0.1), (0.6, (0.3, -1, 0.1), 0.42, 0.1), (0.78, (0.4, -1, 0.3), 0.42), (0.92, (0.5, -0.8, 0.6), 0.4),
                          (1.0, (0.4, -0.2, 1), 0.4)], thick=1.7, palm=(0.36, 1.0, 0.5, (0.25, -0.9, -0.15))),
    "wisp": dict(beam=[(0.14, 0.4, 0.32), (0.3, 1.2, 0.62), (0.36, 2.1, 0.8), (0.3, 3.0, 0.86), (0.2, 3.8, 0.8)],
                 tines=[(0.25, (0.3, 0.6, 0.9), 0.4), (0.5, (0.4, 0.8, 0.7), 0.44), (0.72, (0.3, 0.9, 0.6), 0.4)], thick=0.7),
    # the wapiti's: long beams laid back, dagger points standing up from them
    "lyre": dict(beam=[(0.3, 0.2, 0.46), (0.66, 0.6, 1.0), (0.7, 1.0, 1.6), (0.46, 1.3, 2.1)],
                 tines=[(0.05, (0.2, -1, 0.4), 0.6, 0.5), (0.2, (0.4, -1, 0.5), 0.5, 0.5), (0.42, (0.3, -0.7, 0.9), 0.5), (0.62, (0.1, -0.5, 1), 0.7), (0.8, (0, -0.3, 1), 0.44)], thick=1.1),
    "pillar": dict(beam=[(0.18, 0.1, 0.6), (0.34, 0.18, 1.2), (0.4, 0.2, 1.84), (0.36, 0.16, 2.4)],
                   tines=[(0.08, (0.3, -1, 0.3), 0.5, 0.5), (0.3, (1, -0.2, 0.35), 0.44), (0.5, (1, 0, 0.35), 0.4), (0.7, (1, 0.1, 0.4), 0.36), (0.88, (1, 0.1, 0.5), 0.3)], thick=1.4),
    "wide": dict(beam=[(0.5, 0.1, 0.4), (1.2, 0.3, 0.8), (1.8, 0.5, 1.36), (2.1, 0.5, 2.0), (2.1, 0.3, 2.6)],
                 tines=[(0.05, (0.2, -1, 0.4), 0.7, 0.5), (0.2, (0.3, -1, 0.5), 0.6, 0.5), (0.42, (0.1, -0.7, 0.9), 0.6), (0.6, (-0.1, -0.5, 1), 0.8), (0.78, (-0.3, -0.3, 1), 0.56), (0.92, (-0.6, 0, 1), 0.4)], thick=1.35),
    # the forest giant's: palms
    "branch": dict(beam=[(0.3, 0.1, 0.36), (0.66, 0.2, 0.7), (0.96, 0.26, 1.1)],
                   tines=[(0.12, (0.2, -1, 0.5), 0.4, 0.5), (0.6, (0.6, -0.7, 0.7), 0.36), (0.78, (0.8, 0, 0.8), 0.36), (0.94, (0.5, 0.6, 0.8), 0.34)], thick=1.2, palm=(0.45, 1.0, 0.36, (0.5, 0.1, 0.9))),
    "fallow": dict(beam=[(0.3, 0.12, 0.4), (0.62, 0.3, 0.9), (0.8, 0.4, 1.5), (0.84, 0.4, 2.1)],
                   tines=[(0.08, (0.2, -1, 0.4), 0.5, 0.6), (0.3, (0.5, -1, 0.4), 0.4, 0.5), (0.56, (0.3, 0.9, 0.5), 0.36), (0.7, (0.2, 1, 0.6), 0.36), (0.84, (0.2, 0.9, 0.9), 0.36), (0.96, (0.3, 0.4, 1), 0.36), (1.0, (0.4, -0.5, 1), 0.3)],
                   thick=1.2, palm=(0.48, 1.0, 0.5, (0.15, 1, 0.2))),
    "tree": dict(beam=[(0.24, 0.1, 0.5), (0.46, 0.24, 1.1), (0.86, 0.3, 1.6), (1.0, 0.5, 2.2), (1.3, 0.4, 2.7)],
                 tines=[(0.14, (0.6, -0.8, 0.5), 0.6, 0.4), (0.3, (-0.4, 0.5, 0.9), 0.56), (0.46, (0.9, 0.3, 0.6), 0.7, 0.5), (0.6, (-0.2, -0.7, 0.9), 0.6), (0.72, (0.8, 0.6, 0.6), 0.56), (0.86, (-0.5, 0.3, 1), 0.5), (0.95, (0.7, -0.5, 0.7), 0.44)], thick=1.35),
    "palm": dict(beam=[(0.5, 0.0, 0.26), (1.1, 0.1, 0.5), (1.7, 0.3, 0.86), (2.1, 0.5, 1.3)],
                 tines=[(0.08, (0.4, -1, 0.3), 0.5, 0.3), (0.2, (0.6, -1, 0.5), 0.46, 0.3), (0.5, (0.3, -1, 0.7), 0.4), (0.64, (0.6, -0.7, 0.9), 0.44), (0.78, (0.8, -0.3, 1), 0.44), (0.9, (0.9, 0.1, 1), 0.44), (1.0, (0.8, 0.6, 0.8), 0.4)],
                 thick=1.5, palm=(0.34, 1.0, 0.8, (0.1, -0.6, 0.8))),
    "slim": dict(beam=[(0.14, 0.12, 0.6), (0.34, 0.26, 1.3), (0.4, 0.2, 2.0), (0.3, 0.02, 2.6)],
                 tines=[(0.07, (0.2, -1, 0.5), 0.5, 0.6), (0.4, (0.5, -0.8, 0.7), 0.44), (0.7, (0.6, 0.3, 0.9), 0.4), (0.88, (-0.5, 0.4, 0.9), 0.3)], thick=0.8),
    "eye": dict(beam=[(0.4, 0.06, 0.4), (0.84, 0.1, 1.0), (0.9, 0.1, 1.7), (0.56, 0.06, 2.4), (0.1, 0.02, 2.66)],
                tines=[(0.06, (0.2, -1, 0.4), 0.46, 0.5), (0.3, (1, -0.2, 0.2), 0.36), (0.5, (1, 0, 0.5), 0.34), (0.7, (0.8, 0, 0.9), 0.3)], thick=0.95),
    "droop": dict(beam=[(0.5, 0.1, 0.4), (1.1, 0.24, 0.6), (1.6, 0.36, 0.44), (1.96, 0.46, 0.06), (2.1, 0.5, -0.4)],
                  tines=[(0.2, (0, -0.2, 1), 0.4), (0.4, (0.2, 0, 1), 0.36), (0.6, (0.4, 0.1, 0.9), 0.3), (0.8, (0.8, 0.1, 0.5), 0.26)], thick=1.0),
    "gnarl": dict(beam=[(0.3, 0.0, 0.34), (0.56, -0.16, 0.7), (0.56, 0.1, 1.1), (0.8, 0.0, 1.36)],
                  tines=[(0.25, (0.9, -0.5, 0.3), 0.36), (0.5, (-0.4, 0.7, 0.6), 0.36), (0.72, (0.8, 0.4, 0.4), 0.4), (0.9, (-0.3, -0.7, 0.7), 0.3)], thick=2.1),
    "briar": dict(beam=[(0.36, 0.0, 0.46), (0.76, -0.1, 1.0), (0.9, 0.2, 1.6), (0.7, 0.4, 2.2), (0.9, 0.3, 2.7)],
                  tines=[(0.14, (0.9, -0.6, 0.3), 0.56), (0.32, (-0.4, 0.7, 0.6), 0.5), (0.5, (0.9, 0.1, 0.5), 0.6), (0.66, (0.3, -0.8, 0.6), 0.5), (0.8, (-0.6, 0.2, 0.8), 0.46), (0.92, (0.8, 0.5, 0.5), 0.4)], thick=1.8),
    "rime": dict(beam=[(0.4, 0.1, 0.4), (0.9, 0.3, 0.9), (1.2, 0.5, 1.6), (1.2, 0.5, 2.3)],
                 tines=[(0.06, (0.2, -1, 0.3), 0.7, 0.4), (0.24, (0.5, -1, 0.4), 0.5, 0.4), (0.55, (0.3, 0.9, 0.5), 0.4), (0.7, (0.2, 1, 0.7), 0.44), (0.84, (0.1, 0.8, 1), 0.44), (0.95, (0.3, 0.2, 1), 0.44), (1.0, (0.5, -0.6, 1), 0.4)],
                 thick=1.3, palm=(0.5, 1.0, 0.6, (0.1, 1, 0.3))),
    # the white-tail's: beams that come forward round the face, their points standing up
    "watch": dict(beam=[(0.3, 0.2, 0.4), (0.62, 0.1, 0.8), (0.72, -0.3, 1.0), (0.56, -0.7, 1.02)], tines=[(0.14, (0.1, -0.3, 1), 0.3), (0.5, (0.1, 0, 1), 0.44), (0.76, (0, 0, 1), 0.34)], thick=1.0),
    "crook": dict(beam=[(0.36, 0.26, 0.5), (0.8, 0.3, 1.1), (1.0, 0.0, 1.7), (0.8, -0.5, 2.0), (0.5, -0.8, 1.8), (0.44, -0.74, 1.46)],
                  tines=[(0.1, (0.1, -0.4, 1), 0.4), (0.3, (0.3, 0.2, 1), 0.5), (0.48, (0.5, 0.2, 0.9), 0.4)], thick=1.15),
    "roof": dict(beam=[(0.5, 0.0, 0.3), (1.2, -0.2, 0.52), (1.9, -0.6, 0.5), (2.4, -1.2, 0.36), (2.5, -1.8, 0.2)],
                 tines=[(0.16, (0.2, 1, 0.3), 0.6), (0.36, (0.5, 0.9, 0.3), 0.7), (0.56, (0.8, 0.6, 0.3), 0.7), (0.76, (1, 0.2, 0.2), 0.6), (0.3, (0, -0.3, 1), 0.3), (0.6, (0, -0.2, 1), 0.3)],
                 thick=1.4, palm=(0.2, 1.0, 0.5, (0.5, 0.8, 0.1))),
    "bracket": dict(beam=[(0.24, 0.2, 0.5), (0.5, 0.24, 1.1), (0.6, 0.0, 1.66), (0.44, -0.4, 1.9)],
                    tines=[(0.08, (0.12, -1, 0.3), 1.1, 0.35), (0.45, (0.2, 0.1, 1), 0.44), (0.72, (0.1, 0, 1), 0.4)], thick=1.1),
    "cradle": dict(beam=[(0.4, 0.3, 0.4), (0.9, 0.3, 0.86), (1.1, -0.1, 1.3), (0.9, -0.6, 1.5), (0.5, -0.9, 1.46)],
                   tines=[(0.12, (0, -0.2, 1), 0.4), (0.34, (-0.2, 0.1, 1), 0.6), (0.56, (-0.3, 0, 1), 0.66), (0.76, (-0.3, 0, 1), 0.56)], thick=1.2),
    "stone": dict(beam=[(0.3, 0.1, 0.44), (0.66, 0.1, 0.9), (0.8, -0.2, 1.36), (0.66, -0.6, 1.56)], tines=[(0.3, (0.2, 0, 1), 0.44), (0.62, (0.1, 0, 1), 0.44), (0.86, (0, 0, 1), 0.36)], thick=2.3),
    "candles": dict(beam=[(0.36, 0.2, 0.3), (0.84, 0.1, 0.56), (1.16, -0.3, 0.7), (1.2, -0.8, 0.72)],
                    tines=[(0.14, (0, 0, 1), 0.44), (0.4, (0, 0, 1), 0.6), (0.62, (0, 0, 1), 0.7), (0.82, (0, 0, 1), 0.6), (1.0, (0, 0, 1), 0.5)], thick=0.9),
    "rack": dict(beam=[(0.5, 0.3, 0.44), (1.16, 0.3, 0.96), (1.56, -0.1, 1.5), (1.5, -0.7, 1.86), (1.1, -1.1, 1.9)],
                 tines=[(0.08, (0.1, -0.5, 1), 0.44), (0.26, (0.3, 0.2, 1), 0.7), (0.44, (0.4, 0.1, 1), 0.8), (0.62, (0.3, 0, 1), 0.7), (0.8, (0.1, 0, 1), 0.56)], thick=1.35),
    "elder": dict(beam=[(0.44, 0.3, 0.44), (1.0, 0.4, 0.96), (1.36, 0.1, 1.6), (1.3, -0.5, 2.1), (0.9, -1.0, 2.26)],
                  tines=[(0.07, (0.1, -1, 0.5), 0.6, 0.5), (0.24, (0.4, 0.3, 1), 0.6), (0.42, (0.5, 0.3, 1), 0.7), (0.6, (0.5, 0.1, 1), 0.66), (0.78, (0.3, 0, 1), 0.56), (0.92, (0, -0.2, 1), 0.44)],
                  thick=1.5, palm=(0.3, 0.86, 0.36, (0.4, 0.3, 0.9))),
}
HORN = {"bone": ("antler", "antler_tip"), "velvet": ("velvet", "velvet"), "stone": ("antler_stone", "antler_stone"), "ice": ("antler_ice", "ice_pale"),
        "dark": ("antler_dark", "antler_tip"), "wood": ("antler_wood", "antler_tip"), "pale": ("antler_pale", "antler_pale")}
RACK_BY_LEVEL = {1: 0.0, 2: 0.62, 3: 0.84, 4: 1.0}


def _antler(sg, base, P, size, F):
    """One antler from its pedicle: (the beam's geometry, the tines', the palm's), its points,
    its beam, its tines (root, tip). F: (out, back, up) made a way in the world."""
    beam = _cr([V(base)] + [V(base) + F(sg * x, y, z) * size for x, y, z in P["beam"]], 3)
    cut = P.get("cut", {}).get(sg)
    rb = 0.078 * P.get("thick", 1.0) * (0.55 + 0.45 * size)
    n = len(beam)
    full = list(beam)
    radius = lambda t: rb * (1.0 - 0.7 * t ** 0.85) + 0.006           # noqa: E731
    palm = P.get("palm")
    pdir = None
    if palm:
        pdir = F(sg * palm[3][0], palm[3][1], palm[3][2]).normalized()

    def edge(t):
        """Where a tine at t stands: on the beam, or on the palm's edge."""
        a = _along(full, t)
        if palm and palm[0] - 0.01 <= t and cut is None:
            k = (t - palm[0]) / max(1e-6, palm[1] - palm[0])
            return a + pdir * (palm[2] * size * (0.35 + 0.65 * math.sin(math.pi * min(1.0, 0.15 + 0.8 * k))))
        return a
    tines, tgeo = [], None
    for tn in P.get("tines", ()):
        t, (x, y, z), L = tn[0], tn[1], tn[2]
        curl = tn[3] if len(tn) > 3 else 0.25
        if cut is not None and t > cut:
            continue
        a = edge(t)
        d = F(sg * x, y, z).normalized()
        tip = a + d * (L * size) + F(0, 0, 1) * (curl * L * size * 0.5)
        mid = a + d * (L * size * 0.55) - F(0, 0, 1) * (curl * L * size * 0.08)
        rt = max(0.016, radius(t) * 0.78)
        pts = _cr([a, mid, tip], 2)
        tgeo = g.merge(tgeo, g.tube(pts, [rt * (1.0 - 0.9 * (i / (len(pts) - 1)) ** 1.3) + 0.004 for i in range(len(pts))], n=5))
        tines.append((a, tip))
    if cut is not None:
        m = max(2, int(cut * (n - 1)) + 1)
        beam = beam[:m] + [_along(full, cut)]
    radii = [radius(i / (n - 1)) for i in range(len(beam))]
    if cut is not None:
        radii[-1] *= 1.2
    # the burr: a rough ring where the antler leaves the pedicle
    d0 = (beam[1] - beam[0]).normalized()
    bgeo = g.merge(g.tube(beam, radii, n=6), g.tube([beam[0] + d0 * 0.01, beam[0] + d0 * 0.05, beam[0] + d0 * 0.09], [rb * 1.2, rb * 1.5, rb * 1.1], n=8))
    tips = [] if cut is not None else [beam[-1]]
    tips += [b for _, b in tines]
    pgeo = None
    if palm and cut is None:
        rings = []
        for i in range(9):
            k = i / 8
            t = palm[0] + (palm[1] - palm[0]) * k
            a = _along(full, t)
            e = edge(t)
            w = (e - a)
            L = w.length
            wd = w / max(1e-6, L)
            dd = (_along(full, min(1.0, t + 0.03)) - _along(full, max(0.0, t - 0.03))).normalized()
            nr = dd.cross(wd).normalized()
            th = 0.028 * (0.6 + 0.4 * size)
            a2 = a - wd * radius(t) * 0.5
            rings.append([a2 + nr * th, a2.lerp(e, 0.5) + nr * th * 0.8, e, a2.lerp(e, 0.5) - nr * th * 0.8, a2 - nr * th])
        pgeo = g.loft(rings, caps=True)
    return (bgeo, tgeo, pgeo), tips, full if cut is None else beam, tines


def grow_crown(r, A, shape, size):
    """Its antlers. A fawn has two buttons under the skin; a Path's are young; a Final's are
    half as large again as an Advancement's."""
    sp, level = _S["spec"], _S["level"]
    P, S = _S["P"], _S["HS"]
    kind = gl.opt(sp.get("horn"))[0] or "bone"
    mb, mt = (mat(nm) for nm in HORN[kind])
    k = size * float(sp.get("build", {}).get("antlers", 1.0))
    # the antler's own frame: the head's, as a head is carried at rest, so that a rack stands
    # up from a level head and goes down with a lowered one
    phi = math.radians(_S["crane"][3] - 26.0)
    fa = Vector((0, -math.cos(phi), -math.sin(phi)))
    ua = Vector((0, -math.sin(phi), math.cos(phi)))
    F = lambda x, y, z: (X * x - fa * y + ua * z) * 0.8                 # noqa: E731
    rack = {"tips": [], "beams": [], "tines": [], "mid": P(0, 0.12, 0.17), "size": k, "F": F, "up": ua}
    if shape == "bumps":
        geo = None
        for sg in (1, -1):
            c = P(sg * 0.085, 0.13, 0.15)
            geo = g.merge(geo, g.ico(c, 0.05 * S * size, sub=1, scale=(1, 1, 1.3)))
            rack["tips"].append((c + ua * 0.06, sg))
        _add(r, "buttons", geo, "Head", mat("velvet"), smooth=True)
    else:
        k *= RACK_BY_LEVEL[level] if level < 4 else 1.0
        beams, tines, palms, peds = None, None, None, None
        for sg in (1, -1):
            base = P(sg * 0.09, 0.13, 0.165)
            peds = g.merge(peds, g.tube([P(sg * 0.085, 0.13, 0.1), base + ua * 0.02], [0.06 * S, 0.052 * S], n=7))
            (bg, tg, pg), tips, beam, tn = _antler(sg, base, ANTLERS[shape], k * S, F)
            beams, tines, palms = g.merge(beams, bg), g.merge(tines, tg), g.merge(palms, pg)
            rack["tips"] += [(p, sg) for p in tips]
            rack["beams"].append((sg, beam))
            rack["tines"] += [(a, b, sg) for a, b in tn]
        _add(r, "pedicles", peds, "Head", mat("hide_red"), smooth=True)
        _add(r, "antlers", beams, "Head", mb, smooth=True)
        _add(r, "tines", tines, "Head", mt, smooth=True)
        if palms:
            _add(r, "palms", palms, "Head", mb, smooth=True)
    _S["rack"] = rack


# ======================================================================================
# Its Path's colour (docs/genius-lines.md, "A Path's colour")
# ======================================================================================

def _has(slot, *styles):
    return any(st.partition(":")[0] in styles for st, _ in gl.each(_S["spec"].get(slot)))


def _lenses(r, name, spots, material):
    """Flat spots lying on its skin: [(station, degrees round, radius)]."""
    geo, ws = None, []
    for s, deg, rad in spots:
        p, n = _on(s, deg, 0.004)
        d = s[1]
        fw = (d - n * d.dot(n)).normalized()
        le = gl._lens(p, n, fw, n.cross(fw), rad * 1.15, rad, 0.012)
        geo = g.merge(geo, le)
        ws.extend([s[6]] * len(le[0]))
    _add(r, name, geo, ws, material, smooth=True)


def grow_marks(r, A, style, size):
    """Where it wears its Path's colour: the faces of its own skin painted, or spots laid on it."""
    what, _, step = style.partition(":")
    m = _am(step)
    body = _S["body"]
    st = _station
    yhip, B = _S["yhip"], _S["B"]

    def bd(pick):
        _paint(r, "body", pick, m)

    def legs(pick):
        for tag, L in _S["legs"].items():
            _paint(r, "leg_" + tag, lambda c, n, L=L: pick(c, n, L), m)
    if what == "neck":            # the whole neck, as a stag's darkens for the rut
        bd(lambda c, n: st(c)[7] == "neck" and st(c)[8] > 0.06)
    elif what == "nape":
        bd(lambda c, n: st(c)[7] == "neck" and n.dot(st(c)[3]) > 0.1)
    elif what == "throat":
        bd(lambda c, n: st(c)[7] == "neck" and st(c)[8] > 0.1 and n.dot(st(c)[3]) < -0.15)
    elif what == "bib":           # the breast and the foot of the neck
        bd(lambda c, n: (st(c)[7] == "neck" and st(c)[8] < 0.42 and n.dot(st(c)[3]) < 0.0) or (st(c)[7] == "back" and st(c)[8] < 0.1 and n.y < -0.2))
    elif what == "saddle":
        bd(lambda c, n: st(c)[7] == "back" and 0.04 < st(c)[8] < 0.74 and n.dot(st(c)[3]) > 0.35)
    elif what == "blanket":
        bd(lambda c, n: st(c)[7] == "back" and 0.04 < st(c)[8] < 0.82 and n.dot(st(c)[3]) > -0.3)
    elif what == "dorsal":        # a stripe down its spine, from the poll to the tail
        bd(lambda c, n: n.dot(st(c)[3]) > 0.78)
        _paint(r, "tail", lambda c, n: True, m)
    elif what == "stripes":
        bd(lambda c, n: st(c)[7] == "back" and 0.08 < st(c)[8] < 0.9 and body.index(st(c)) % 2 == 0 and -0.3 < n.dot(st(c)[3]) < 0.9)
    elif what == "rump":
        bd(lambda c, n: c.y > yhip + 0.12 and n.y > 0.2)
        _paint(r, "tail", lambda c, n: True, m)
    elif what == "belly":
        bd(lambda c, n: st(c)[7] == "back" and n.dot(st(c)[3]) < -0.45)
    elif what == "stockings":     # the whole leg below the body
        legs(lambda c, n, L: c.z < L["top"])
    elif what == "socks":
        legs(lambda c, n, L: c.z < L["zsock"])
    elif what == "bands":         # a band above each knee and hock, and one at the fetlock
        legs(lambda c, n, L: L["zsock"] - 0.02 < c.z < L["zsock"] + 0.3 or L["fet"] - 0.08 < c.z < L["fet"] + 0.22)
    elif what == "blaze":
        f, up, hb = _S["hf"], _S["hup"], r.bone("Head")
        _paint(r, "head", lambda c, n: n.dot(up) > 0.45 and (c - hb).dot(f) > 0.16 * _S["HS"], m)
    elif what == "mask":
        f, hb = _S["hf"], r.bone("Head")
        _paint(r, "head", lambda c, n: (c - hb).dot(f) > 0.4 * _S["HS"], m)
    elif what == "ears":
        for part, op in _S.get("ear_in", []):
            _paint(r, part, lambda c, n, op=op: n.dot(op) > 0.25, m)
    elif what == "tail":
        _paint(r, "tail", lambda c, n: True, m)
    elif what == "dapple":        # spots along its flanks, as a fallow buck's or a fawn's
        spots = []
        back = [s for s in body if s[7] == "back" and 0.08 < s[8] < 0.86]
        for i, s in enumerate(back):
            for k, deg in enumerate((58, 32, 8)):
                if (i + k) % 2:
                    continue
                rad = (0.075 - 0.012 * k) * size * (1.0 + 0.2 * math.sin(i * 2.1 + k))
                spots += [(s, deg + 5 * math.sin(i * 1.7), rad), (s, 180 - deg - 5 * math.sin(i * 1.7), rad)]
        _lenses(r, "dapple", spots, m)
    elif what == "tines":         # the points of its antlers
        _paint(r, "tines", lambda c, n: True, m)
    elif what == "palms":
        _paint(r, "palms", lambda c, n: True, m)
    elif what == "burrs":         # bands round its beams
        rack = _S.get("rack")
        geo = None
        for sg, beam in (rack or {}).get("beams", []):
            for t in (0.07, 0.14, 0.21) if size <= 1.0 else (0.07, 0.14, 0.21, 0.28, 0.35):
                c = _along(beam, t)
                d = _along(beam, t + 0.02) - c
                geo = g.merge(geo, _hoop(c, d, 0.11 * (1.0 - 0.5 * t) * (0.6 + 0.4 * rack["size"]), 0.02, n=10, sides=4))
        if geo:
            _add(r, "burrs", geo, "Head", m, smooth=True)
    elif what != "mane":          # (a mane is the neck's: it takes the colour where this says so)
        log("NO SUCH MARK:", what)


# ======================================================================================
# What it has grown or been given
# ======================================================================================

def _neck_at(t):
    """The place on its neck a share t of the way from the chest to the skull."""
    return min(_S["neckline"], key=lambda s: abs(s[8] - t))


def _collar(s, wide=0.04, lift=0.02, n=14):
    rings = [[_on(s, 360.0 * j / n, lift)[0] + s[1] * (k * wide) for j in range(n)] for k in (-1, 1)]
    return g.loft(rings, caps=False)


def grow_neck(r, A, style, size):
    nl = _S["neckline"]
    if style == "mane":           # a stag's mane: long hair under the throat and round the foot of the neck
        step = next((st.partition(":")[2] for st, _ in gl.each(_S["spec"].get("marks")) if st.partition(":")[0] == "mane"), None)
        m1 = _am(step or "dark") if step is not None else mat("hide_red")
        m2 = _am({"": "dark", "dark": "", "light": "pale", "pale": "light", "deep": "dark"}.get(step or "dark", "")) if step is not None else mat("fur_cream")
        g1, g2, w1, w2 = None, None, [], []
        for i, s in enumerate(nl):
            t = s[8]
            if not 0.08 < t < 0.92 or i % 2:
                continue
            for k, deg in enumerate((222, 258, 282, 318)):
                p, n = _on(s, deg + 8 * math.sin(i * 1.3), -0.015)
                L = 0.3 * size * (0.7 + 0.6 * (1.0 - t)) * (1.0 + 0.25 * math.sin(i * 2.3 + k * 1.9))
                # a lock: out from the skin a little, then hanging, its end turned in toward the chest
                mid = p + n * (0.1 * L) - Z * (0.5 * L) + s[1] * (0.12 * L)
                tip = p - n * (0.02 * L) - Z * L + s[1] * (0.34 * L)
                lk = g.tongue([p, mid, tip], [0.2 * (0.7 + 0.3 * size), 0.17 * (0.7 + 0.3 * size), 0.025], thick=0.3, normal=n)
                if (i // 2 + k) % 2:
                    g2, w2 = g.merge(g2, lk), w2 + [s[6]] * len(lk[0])
                else:
                    g1, w1 = g.merge(g1, lk), w1 + [s[6]] * len(lk[0])
        _add(r, "mane", g1, w1, m1, smooth=True)
        _add(r, "mane_b", g2, w2, m2, smooth=True)
    elif style == "bell":         # a bell on a collar
        s = _neck_at(0.42)
        _add(r, "collar", _collar(s, 0.045 * size), [s[6]] * 28, _am("dark") if _S["spec"].get("accent") else mat("leather_dark"), smooth=False)
        p, n = _on(s, 270, 0.03)
        c = p + Vector((0, 0, -0.14 * size))
        bell = g.lathe([(0.03, 0.14), (0.09, 0.1), (0.13, -0.04), (0.17, -0.12)], n=8, centre=c)
        gl._later(r, "sway", "bell", [(g.moved(bell, Matrix.Translation(c) @ Matrix.Scale(size, 4) @ Matrix.Translation(-c)), mat("metal_brass")),
                                      (g.ico(c + Vector((0, 0, -0.13 * size)), 0.045 * size, sub=1), mat("metal_iron"))], p, s[6][0][0], hang=True)
    elif style == "ivy":          # ivy grown round its neck
        stem, leaves, ws, wl = [], None, [], []
        use = [s for s in nl if 0.12 < s[8] < 0.9]
        for i, s in enumerate(use):
            p, n = _on(s, 40 + 95.0 * i, 0.02)
            stem.append(p)
            ws.append(s[6])
            for k in (-1, 1):
                q, nq = _on(s, 40 + 95.0 * i + 38 * k, 0.015)
                lf = g.blade(q, q + (nq * 0.4 + s[1] * 0.5 * k - Z * 0.5).normalized() * 0.2 * size, 0.15 * size, normal=nq, belly=0.4)
                leaves = g.merge(leaves, lf)
                wl.extend([s[6]] * len(lf[0]))
        tube = g.tube(stem, [0.018] * len(stem), n=4)
        _add(r, "ivy_stem", tube, [w for w in ws for _ in range(4)], mat("bark"), smooth=True)
        _add(r, "ivy", leaves, wl, _am("dark") if _S["spec"].get("accent") else mat("leaf"), smooth=False)
    elif style == "garland":      # a garland of flowers round the foot of its neck
        s = _neck_at(0.2)
        petals, hearts, n = None, None, 11
        for j in range(n):
            p, nn = _on(s, 360.0 * j / n, 0.03)
            petals = g.merge(petals, g.ico(p, 0.085 * size, sub=1, scale=(1, 1, 0.7)))
            hearts = g.merge(hearts, g.ico(p + nn * 0.05 * size, 0.036 * size, sub=0))
        _add(r, "garland", petals, [s[6]] * len(petals[0]), mat("petal"), smooth=True)
        _add(r, "garland_hearts", hearts, [s[6]] * len(hearts[0]), _am("light") if _S["spec"].get("accent") else mat("beak"), smooth=True)
    elif style == "teeth":        # a cord of teeth
        s = _neck_at(0.36)
        _add(r, "cord", _collar(s, 0.016, 0.02), [s[6]] * 28, mat("cord"), smooth=False)
        geo = None
        for j, deg in enumerate((205, 228, 250, 270, 290, 312, 335)):
            p, n = _on(s, deg, 0.03)
            geo = g.merge(geo, g.cone(p, p + (n * 0.3 - Z).normalized() * (0.13 + 0.05 * (j % 2)) * size, 0.03 * size, n=4))
        _add(r, "cord_teeth", geo, [s[6]] * len(geo[0]), mat("bone"), smooth=True)
    else:
        log("NO SUCH NECK:", style)


def grow_hung(r, A, style, size):
    """What is in its antlers."""
    rack = _S.get("rack")
    if not rack:
        return
    tips, beams, tines, mid, cs, F, ua = rack["tips"], rack["beams"], rack["tines"], rack["mid"], rack["size"], rack["F"], rack["up"]
    H = "Head"
    acc = bool(_S["spec"].get("accent"))
    if style == "points":         # the field at every point
        geo = None
        for p, _ in tips:
            geo = g.merge(geo, g.ico(p, 0.04 * size, sub=1))
        _add(r, "points", geo, H, field("points", 3.0), smooth=True)
    elif style == "moss":         # moss on the beams, hanging
        geo, hang = None, None
        for sg, beam in beams:
            for k, t in enumerate((0.2, 0.48, 0.74)):
                c = _along(beam, t)
                geo = g.merge(geo, g.ico(c + ua * 0.04, (0.1 - 0.012 * k) * size, sub=1, scale=(1.2, 1.2, 0.7)))
                hang = g.merge(hang, g.blade(c, c + Vector((sg * 0.03, 0.02, -(0.26 + 0.1 * (k % 2)) * size)), 0.11, normal=Y, belly=0.5))
        _add(r, "crown_moss", geo, H, _am() if acc else mat("moss"), smooth=True)
        _add(r, "crown_moss_hang", hang, H, _am("dark") if acc else mat("moss"), smooth=False)
    elif style == "leaves":
        geo = None
        for i, (p, sg) in enumerate(tips):
            for k in range(2):
                geo = g.merge(geo, g.blade(p, p + Vector((sg * (0.14 + 0.1 * k), 0.12 - 0.14 * k, 0.2 - 0.06 * k)) * size, 0.17 * size, normal=Vector((0, 0.5, 1)), belly=0.45))
        _add(r, "crown_leaves", geo, H, _am("dark") if acc else mat("leaf"), smooth=False)
    elif style == "flowers":      # its crown flowers by midsummer
        petals, hearts = None, None
        spots = [p for p, _ in tips]
        for sg, beam in beams:
            spots += [_along(beam, t) + Vector((sg * 0.05, -0.05, 0.05)) for t in (0.3, 0.55, 0.8)]
        for p in spots:
            petals = g.merge(petals, g.ico(p, 0.11 * size, sub=0, scale=(1, 1, 0.6)))
            hearts = g.merge(hearts, g.ico(p + Vector((0, 0, 0.04 * size)), 0.045 * size, sub=0))
        _add(r, "crown_petals", petals, H, mat("petal"), smooth=True)
        _add(r, "crown_hearts", hearts, H, field("bloom", 2.4), smooth=True)
    elif style == "weed":         # river weed in its tines
        geo = None
        for i, (p, sg) in enumerate(tips):
            L = (0.6 + 0.4 * math.sin(i * 1.7) ** 2) * size
            geo = g.merge(geo, g.tongue([p, p + Vector((sg * 0.03, 0.03, -L * 0.5)), p + Vector((sg * -0.02, 0.06, -L))], [0.11, 0.13, 0.02], thick=0.25, normal=Y))
        _add(r, "crown_weed", geo, H, _am("dark") if acc else mat("weed"), smooth=False)
    elif style == "briar":        # briar grown through it, in flower
        canes, thorns, flowers = None, None, None
        for side in (1, -1):
            ts = [p for p, sg in tips if sg == side]
            for a, b in zip(ts, ts[1:] + ts[:1]):
                top = (a + b) / 2 + Vector((side * 0.16, 0.0, 0.3)) * size
                pts = [a, a.lerp(top, 0.6) + Vector((0, 0, 0.05)), top, b.lerp(top, 0.6) + Vector((0, 0, 0.05)), b]
                canes = g.merge(canes, g.tube(pts, [0.024] * 5, n=4, caps=False))
                for q in pts[1:4]:
                    thorns = g.merge(thorns, g.cone(q, q + Vector((side * 0.1, -0.06, 0.09)), 0.026, n=4))
                flowers = g.merge(flowers, g.ico(top, 0.085 * size, sub=1, scale=(1, 1, 0.6)))
        _add(r, "briar", canes, H, _am("deep") if acc else mat("bark"), smooth=True)
        _add(r, "briar_thorns", thorns, H, _am("light") if acc else mat("bark_light"), smooth=False)
        _add(r, "briar_flowers", flowers, H, mat("petal"), smooth=True)
    elif style == "birds":        # small birds nest in it
        for k, (sg, beam) in enumerate(beams):
            c = _along(beam, 0.5 + 0.2 * k) + ua * 0.12
            body = g.merge(g.ico(c, 0.1, sub=1, scale=(0.8, 1.2, 0.85)), g.ico(c + Vector((0, -0.1, 0.07)), 0.065, sub=1),
                           g.blade(c + Vector((0, 0.08, 0.0)), c + Vector((0, 0.26, 0.06)), 0.09, normal=Z))
            items = [(body, mat("feather_pale" if k else "feather_mid")), (g.cone(c + Vector((0, -0.15, 0.07)), c + Vector((0, -0.22, 0.06)), 0.02, n=4), mat("beak"))]
            gl._later(r, "turn", "bird", items, c, H, n=k)
    elif style == "lamp":         # a lamp hangs from one brow-tine
        right = [b for a, b, sg in tines if sg == -1] or [p for p, _ in tips]
        at = right[0]
        s = 0.22 * size
        c = at + Vector((0, 0, -s * 1.5))
        items = [(g.tube([at, at + Vector((0, 0, -s * 0.55))], s * 0.07, n=5), mat("metal_iron")),
                 (g.lathe([(s * 0.12, s * 0.95), (s * 0.5, s * 0.6), (s * 0.56, s * 0.52)], n=8, centre=c), _am() if acc else mat("metal_brass")),
                 (g.lathe([(s * 0.52, -s * 0.62), (s * 0.3, -s * 0.8)], n=8, centre=c), mat("metal_brass"))]
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            p = c + Vector((math.cos(a) * s * 0.5, math.sin(a) * s * 0.5, 0))
            items.append((g.tube([p + Vector((0, 0, -s * 0.62)), p + Vector((0, 0, s * 0.55))], s * 0.05, n=4), mat("metal_iron")))
        gl._later(r, "sway", "crownlamp", items, at, H, hang=True)
        gl._later(r, "pulse", "crownlamp_light", [(g.ico(c, s * 0.36, sub=2, scale=(1, 1, 1.25)), field("lamp", 3.6))], c, H, under="sway_crownlamp")
    elif style == "flame":        # a small flame sits in the fork of its crown
        c = mid + ua * (0.62 * cs)
        _add(r, "crown_dish", g.lathe([(0.03, -0.1), (0.16, -0.06), (0.21, 0.0)], n=8, centre=c), H, mat("metal_dark"), smooth=False)
        fl = None
        for dx, h in ((0.0, 0.56), (0.09, 0.36), (-0.08, 0.4)):
            f0 = c + Vector((dx, 0, 0.0))
            fl = g.merge(fl, g.tongue([f0, f0 + Vector((dx * 0.4, 0, h * 0.45 * size)), f0 + Vector((-dx * 0.3, 0, h * size))], [0.18 * size, 0.16 * size, 0.02], thick=0.7, normal=Y))
        gl._later(r, "flick", "crownflame", [(fl, field("flame", 3.6))], c, H)
    elif style == "ring":         # a pale ring hangs in its crown
        c = mid + ua * (0.9 * cs) + Vector((0, 0.05, 0))
        gl._later(r, "bob", "crownring", [(_hoop(c, Vector((0, 1, 0.15)), 0.3 * size, 0.03, n=18), field("crown", 3.5))], c, H)
    elif style == "halo":         # the air rings round its head
        c = mid + ua * (0.5 * cs)
        fwd = -Y
        _add(r, "halo", _hoop(c, Y, 1.1 * size, 0.034, n=24), H, field("ring", 3.2), smooth=True)
        _add(r, "halo2", _hoop(c + fwd * 0.55 - Z * 0.2, Y, 0.62 * size, 0.026, n=18), H, field("ring", 2.6), smooth=True)
        _add(r, "halo3", _hoop(c + fwd * 1.0 - Z * 0.35, Y, 0.32 * size, 0.02, n=14), H, field("ring", 2.2), smooth=True)
    elif style == "script":       # lines of small writing cut into the beam
        geo = None
        for sg, beam in beams:
            for t in (0.1, 0.18, 0.26, 0.34, 0.42, 0.5, 0.58, 0.66, 0.74):
                c = _along(beam, t)
                d = _along(beam, t + 0.02) - c
                geo = g.merge(geo, _hoop(c, d, 0.105 * (1.0 - 0.6 * t), 0.016, n=8, sides=3))
        _add(r, "script", geo, H, field("script", 2.8), smooth=False)
    elif style == "ribbons":      # a ribbon for each of the cohort
        for i, (p, sg) in enumerate(tips):
            L = (0.5 + 0.3 * math.sin(i * 2.3) ** 2) * size
            strip = g.tongue([p, p + Vector((sg * 0.05, 0.05, -L * 0.5)), p + Vector((sg * -0.03, 0.1, -L))], [0.1, 0.1, 0.08], thick=0.2, normal=Y)
            m = (_am(("", "light", "dark")[i % 3]) if acc and i % 2 == 0 else mat(("ribbon_a", "ribbon_b", "ribbon_c")[i % 3]))
            gl._later(r, "sway", "ribbon", [(strip, m)], p, H, n=i)
    elif style == "tokens":       # teeth, tags and bits of collar, on wire
        wire, hung, bright = None, None, None
        for side in (1, -1):
            ts = [p for p, sg in tips if sg == side]
            for a, b in zip(ts, ts[1:]):
                sag = (a + b) / 2 + Vector((0, 0, -0.14))
                wire = g.merge(wire, g.tube([a, sag, b], [0.009] * 3, n=3, caps=False))
                for k, t in enumerate((0.25, 0.5, 0.75)):
                    q = a.lerp(sag, t * 2) if t < 0.5 else sag.lerp(b, t * 2 - 1)
                    tok = g.blade(q, q + Vector((0, 0.0, -(0.2 + 0.06 * k) * size)), 0.11 * size, normal=Y, belly=0.55)
                    if k == 1:
                        bright = g.merge(bright, tok)
                    else:
                        hung = g.merge(hung, tok)
        _add(r, "token_wire", wire, H, mat("metal_iron"), smooth=False)
        _add(r, "tokens", hung, H, mat("bone"), smooth=False)
        _add(r, "tokens_b", bright, H, _am("light") if acc else mat("metal_brass"), smooth=False)
    elif style == "icicles":      # frost on every tine
        geo = None
        for i, (p, sg) in enumerate(tips):
            geo = g.merge(geo, g.cone(p, p + Vector((0, 0, -(0.3 + 0.14 * math.sin(i * 1.3) ** 2) * size)), 0.045, n=5))
        for sg, beam in beams:
            for t in (0.3, 0.45, 0.6, 0.75, 0.9):
                c = _along(beam, t)
                geo = g.merge(geo, g.cone(c, c + Vector((0, 0, -0.26 * size)), 0.04, n=5))
        _add(r, "icicles_crown", geo, H, mat("ice_pale"), smooth=False)
    elif style == "lichen":       # lichen on its crown
        geo = None
        for sg, beam in beams:
            for k, t in enumerate((0.2, 0.42, 0.63, 0.85)):
                c = _along(beam, t)
                geo = g.merge(geo, g.ico(c + Vector((sg * 0.05, -0.04, 0.05)), 0.13 * size, sub=1, scale=(1, 1, 0.4), rot=(0.6, 0.3 * k, 0)))
        _add(r, "lichen", geo, H, _am("pale") if acc else mat("lichen"), smooth=True)
    elif style == "candles":      # small cold lights at its points
        wax = None
        for i, (p, sg) in enumerate(tips):
            wax = g.merge(wax, g.tube([p - ua * 0.02, p + Vector((0, 0, 0.14 * size))], 0.036, n=6))
            f0 = p + Vector((0, 0, 0.14 * size))
            lit = g.tongue([f0, f0 + Vector((0, 0, 0.1 * size)), f0 + Vector((0, 0, 0.27 * size))], [0.09 * size, 0.085 * size, 0.01], thick=0.8, normal=Y)
            gl._later(r, "flick", "candle", [(lit, field("flame", 3.4))], f0, H, n=i)
        _add(r, "candle_wax", wax, H, _am("pale") if acc else mat("wax"), smooth=True)
    elif style == "eye":          # the crown closes round an eye of light
        c = mid + ua * (1.5 * cs * 0.8) + Vector((0, 0.04, 0))
        _add(r, "crown_eyelid", g.blade(c + Vector((0, 0.03, -0.42 * size)), c + Vector((0, 0.03, 0.42 * size)), 0.6 * size, normal=Y, belly=0.5), H, _am("pale") if acc else mat("fur_pale"), smooth=True)
        gl._later(r, "pulse", "crowneye", [(g.ico(c, 0.19 * size, sub=2, scale=(1.0, 0.5, 1.5)), field("eyes", 3.8))], c, H)
    elif style == "cloth":        # old pale strips hanging from it, like lichen from a branch
        geo = None
        for sg, beam in beams:
            for k in range(8):
                c = _along(beam, 0.2 + 0.1 * k)
                L = (0.4 + 0.3 * math.sin(k * 1.9) ** 2) * size
                geo = g.merge(geo, g.tongue([c, c + Vector((0, 0.03, -L * 0.5)), c + Vector((sg * 0.02, 0.05, -L))], [0.11, 0.11, 0.03], thick=0.2, normal=Y))
        _add(r, "crown_cloth", geo, H, _am("pale") if acc else mat("lichen"), smooth=False)
    elif style == "fawnlight":    # whoever is smallest is walking under it
        c = Vector((0.0, r.bone("Head").y + 0.1, 0.42))
        items = [(g.ico(c, 0.16 * size, sub=1, scale=(0.8, 1.3, 1.0)), field("mote", 3.0)), (g.ico(c + Vector((0, -0.2, 0.15)), 0.1 * size, sub=1), field("mote", 3.0)),
                 (g.cone(c + Vector((0.05, -0.2, 0.22)), c + Vector((0.1, -0.16, 0.4)), 0.035, n=4), field("mote", 3.0)),
                 (g.cone(c + Vector((-0.05, -0.2, 0.22)), c + Vector((-0.1, -0.16, 0.4)), 0.035, n=4), field("mote", 3.0))]
        for dx, dy in ((0.06, -0.1), (-0.06, -0.1), (0.06, 0.12), (-0.06, 0.12)):
            items.append((g.tube([c + Vector((dx, dy, -0.05)), c + Vector((dx, dy, -0.4))], 0.022, n=4), field("mote", 3.0)))
        gl._later(r, "bob", "fawnlight", items, c, "Torso3")
    else:
        log("NO SUCH HUNG:", style)


def grow_throat(r, A, style, size):
    """A throat that swells before it calls."""
    s = _neck_at(0.6)
    p, n = _on(s, 270, -0.08 * size)
    c = p
    acc = bool(_S["spec"].get("accent"))
    gl._later(r, "pulse", "throat", [(g.ico(c, 0.19 * size, sub=2, scale=(0.9, 0.9, 1.3)), mat("hide_red"))], c, s[6][0][0])
    q = c + n * 0.18 * size
    _add(r, "throat_seam", g.blade(q + Z * 0.2 * size, q - Z * 0.22 * size, 0.07, normal=n, belly=0.5), [s[6]] * 6, field("voice", 2.2), smooth=True)


def grow_breath(r, A, style, size):
    n = A.nose
    geo = None
    if style == "wisp":           # you see its breath before you see it
        for d, rad, dx, dz in ((0.16, 0.055, 0.02, -0.03), (0.4, 0.085, -0.04, 0.02), (0.7, 0.115, 0.05, 0.12), (0.98, 0.075, -0.03, 0.26)):
            geo = g.merge(geo, g.ico(n + Vector((dx, -d * size, -0.05 + dz * size)), rad * size, sub=2, scale=(1.0, 1.3, 0.8)))
    else:                         # breath that hangs behind it
        for k, (dx, L) in enumerate(((0.3, 1.5), (-0.3, 1.2), (0.36, 2.2))):
            p0 = n + Vector((dx * 0.4, 0.2, 0.05))
            geo = g.merge(geo, g.tongue([p0, p0 + Vector((dx, L * 0.3, 0.2)) * size, p0 + Vector((dx * 1.3, L * 0.7, 0.3)) * size, p0 + Vector((dx, L, 0.2)) * size],
                                        [0.08, 0.2, 0.18, 0.02], thick=0.5, normal=X))
    gl._later(r, "flick", "breath", [(geo, mat("ash"))], n, "Head")


def grow_hide(r, A, style, size):
    """Its hide stands in thick plates lapped along the flank, like bark."""
    acc = bool(_S["spec"].get("accent"))
    back = [s for s in _S["body"] if s[7] == "back" and 0.02 < s[8] < 0.9]
    dark, pale, wd, wp = None, None, [], []
    for i, s in enumerate(back):
        for row, deg in enumerate((60, 26, -8)):
            if (i + row) % 2:
                continue
            for dg in (deg, 180 - deg):
                p, n = _on(s, dg, 0.025)
                d = s[1] * 0.45 - s[3] * 0.9
                d = (d - n * d.dot(n)).normalized()
                bl = g.blade(p - d * 0.14 * size, p + d * 0.34 * size, 0.34 * size, thick=0.05 * size, normal=n, belly=0.42)
                if (i // 2 + row) % 2:
                    dark, wd = g.merge(dark, bl), wd + [s[6]] * len(bl[0])
                else:
                    pale, wp = g.merge(pale, bl), wp + [s[6]] * len(bl[0])
    _add(r, "bark", dark, wd, _am("deep") if acc else mat("bark"), smooth=False)
    _add(r, "bark_b", pale, wp, mat("bark_light"), smooth=False)


def grow_back(r, A, style, size):
    ysh, yhip = _S["ysh"], _S["yhip"]
    acc = bool(_S["spec"].get("accent"))
    if style == "moss":           # moss on its back
        geo, ws = None, []
        for i in range(10):
            y = ysh + 0.0 + (yhip - ysh + 0.2) * i / 9
            x = 0.16 * math.sin(i * 2.1)
            top, wide = _back(y)
            b = g.ico((x, y, top - 0.5 * abs(x) * abs(x) / max(0.1, wide) + 0.0), (0.22 - 0.05 * (i % 2)) * size, sub=1, scale=(1.1, 1.3, 0.42))
            geo = g.merge(geo, b)
            ws.extend([r.spine_weights(y)] * len(b[0]))
        _add(r, "back_moss", geo, ws, _am() if acc else mat("moss"), smooth=True)
    elif style == "spots":        # a fawn's dappled back
        spots = []
        back = [s for s in _S["body"] if s[7] == "back" and 0.06 < s[8] < 0.88]
        for i, s in enumerate(back):
            for k, deg in enumerate((64, 40)):
                if (i + k) % 2:
                    continue
                spots += [(s, deg, 0.06 * size), (s, 180 - deg, 0.06 * size)]
        _lenses(r, "spots", spots, mat("fur_cream"))
    else:
        log("NO SUCH BACK:", style)


def grow_legs(r, A, style, size):
    if style == "mould":          # leaf-mould to the hock
        for tag, L in _S["legs"].items():
            _paint(r, "leg_" + tag, lambda c, n, L=L: c.z < L["zsock"] * 0.8, mat("earth"))
    elif style == "knees":        # its knees are grey with standing
        for tag, L in _S["legs"].items():
            _paint(r, "leg_" + tag, lambda c, n, L=L: abs(c.z - L["knee"].z) < 0.16, mat("knee"))
    elif style == "wet":          # wet to the chest
        for tag, L in _S["legs"].items():
            _paint(r, "leg_" + tag, lambda c, n, L=L: c.z < L["top"] - 0.1, mat("wet"))
        _paint(r, "body", lambda c, n: c.z < _S["B"] + 0.2 and n.z < -0.2, mat("wet"))
    elif style == "feather":      # broad hooves, feathered at the fetlock
        for tag, L in _S["legs"].items():
            geo = None
            for k in range(6):
                a = k * math.pi / 3
                b0 = Vector((L["x"] + 0.05 * math.cos(a), L["y"] + 0.04 + 0.05 * math.sin(a), L["fet"] + 0.08))
                geo = g.merge(geo, g.blade(b0, b0 + Vector((0.13 * math.cos(a), 0.13 * math.sin(a), -0.26)) * size, 0.13, normal=Vector((math.cos(a), math.sin(a), 0.3)), belly=0.4))
            _add(r, "fetlock_" + tag, geo, L["bone"], mat("fur_cream"), smooth=True)
    else:
        log("NO SUCH LEGS:", style)


def grow_flank(r, A, style, size):
    """One flank worn smooth and faintly bright where twelve hands have touched it."""
    zmid = (_S["W"] + _S["B"]) / 2 + 0.12
    y0 = (_S["ysh"] + _S["yhip"]) / 2
    for sg in (1, -1):
        geo = None
        for k, (dy, dz) in enumerate(((0.0, 0.0), (0.42, 0.14), (0.26, -0.26), (-0.3, -0.12), (0.66, -0.1))):
            y, z = y0 + dy, zmid + dz
            x = sg * (_flank(y, z) + 0.012)
            geo = g.merge(geo, g.ico((x, y, z), 0.1 * size, sub=1, scale=(0.18, 1.0, 1.1)))
            for f in range(4):
                geo = g.merge(geo, g.ico((x, y - 0.09 + 0.06 * f, z + 0.14 + 0.02 * math.sin(f * 1.6)), 0.035 * size, sub=0, scale=(0.3, 1.0, 1.8)))
        _add(r, "hands_%d" % sg, geo, "Torso2", field("hands", 1.5), smooth=True)


def grow_chest(r, A, style, size):
    """A plough before its chest, like the one on the front of the car."""
    cy, zs = A.chest_y, r.bone("FrontUpperLeg.L").z
    apex = Vector((0, cy - 0.75 * size, 0.42))
    geo = g.tube([apex, apex + Vector((0, 0.1, 0.55))], [0.05, 0.05], n=5)
    for sg in (1, -1):
        for k in range(5):
            t = k / 4
            geo = g.merge(geo, g.tube([apex + Vector((0, 0.02, 0.1 + 0.5 * t)), Vector((sg * (0.5 + 0.1 * t), cy + 0.25, 0.5 + 0.75 * t))], [0.04, 0.04], n=4))
        geo = g.merge(geo, g.tube([Vector((sg * 0.5, cy + 0.25, 0.5)), Vector((sg * 0.6, cy + 0.25, 1.25)), Vector((sg * 0.3, cy + 0.2, zs + 0.25))], [0.05, 0.05, 0.05], n=5))
    _add(r, "plough", geo, "Torso3", mat("metal_iron"), smooth=False)
    gl._later(r, "pulse", "ploughlamp", [(g.ico(apex + Vector((0, 0.0, 0.66)), 0.1, sub=1), field("lamp", 3.2))], apex + Vector((0, 0.0, 0.66)), "Torso3")


def grow_armor(r, A, style, size):
    P, S, up, f = _S["P"], _S["HS"], _S["hup"], _S["hf"]
    acc = bool(_S["spec"].get("accent"))
    if style == "brow":           # the brow thick, a boss of horn between the pedicles, scuffed
        c = P(0, 0.2, 0.19)
        phi = math.atan2(-f.z, -f.y)
        _add(r, "brow_boss", g.ico(c, 1.0, sub=1, scale=(0.15 * S * size, 0.13 * S * size, 0.05 * S), rot=(-phi, 0, 0)), "Head", mat("antler"), smooth=True)
        geo = None
        for dx in (-0.06, 0.02, 0.07):
            geo = g.merge(geo, g.blade(c + (X * dx - f * 0.08 + up * 0.045) * S, c + (X * (dx + 0.03) + f * 0.1 + up * 0.04) * S, 0.02 * S, normal=up))
        _add(r, "brow_scuffs", geo, "Head", mat("antler_tip"), smooth=False)
    elif style == "scars":        # old cuts across its shoulder and flank
        geo, ws = None, []
        back = [s for s in _S["body"] if s[7] == "back" and 0.05 < s[8] < 0.7]
        for i, (k, deg, L) in enumerate(((1, 30, 0.5), (3, 150, 0.6), (4, 10, 0.44), (6, 165, 0.5), (2, 60, 0.4), (7, 120, 0.4))):
            s = back[min(k, len(back) - 1)]
            p, n = _on(s, deg, 0.012)
            d = (s[1] * 0.6 - s[3] * 0.8).normalized()
            d = (d - n * d.dot(n)).normalized()
            bl = g.blade(p - d * L * 0.5 * size, p + d * L * 0.5 * size, 0.07 * size, normal=n, belly=0.5)
            geo = g.merge(geo, bl)
            ws.extend([s[6]] * len(bl[0]))
        _add(r, "scars", geo, ws, _am("light") if acc else mat("scar"), smooth=True)
    else:
        log("NO SUCH ARMOR:", style)


def grow_eyes(r, A, style, size):
    if style == "third":          # a pale mark like an eye on its brow
        P, S, up, f = _S["P"], _S["HS"], _S["hup"], _S["hf"]
        c = P(0, 0.2, 0.185)
        acc = bool(_S["spec"].get("accent"))
        _add(r, "third_lid", gl._lens(c, up, f, X, 0.1 * S * size, 0.07 * S * size, 0.016), "Head", _am("pale") if acc else mat("fur_pale"), smooth=True)
        gl._later(r, "pulse", "thirdeye", [(gl._lens(c + up * 0.012, up, f, X, 0.06 * S * size, 0.035 * S * size, 0.014), field("eyes", 3.6))], c, "Head")


OWN = (("marks", grow_marks), ("neck", grow_neck), ("hung", grow_hung), ("throat", grow_throat), ("breath", grow_breath), ("hide", grow_hide), ("back", grow_back),
       ("legs", grow_legs), ("flank", grow_flank), ("chest", grow_chest), ("armor", grow_armor), ("eyes", grow_eyes))


# ======================================================================================
# The build
# ======================================================================================

def _reread(r, A):
    b = r.bone
    A.head, A.n1, A.n2, A.n3 = b("Head"), b("Neck1"), b("Neck2"), b("Neck3")
    A.t3, A.t2, A.t1, A.back = b("Torso3"), b("Torso2"), b("Torso"), b("Back")
    A.tail = [b("Tail%d" % i) for i in range(1, 9)]
    A.sh, A.hip = b("FrontUpperLeg.L"), b("BackUpperLeg.L")
    A.feet = {tag: b(foot) for tag, foot, _ in gl.FEET}


def measure(r, A):
    """The deer itself, laid on the frame in the wolf's place; and what the wolf's own styles
    read of a body, read of this one."""
    sp = _S["spec"]
    _strip(r)
    _reread(r, A)
    _body(r, A)
    A.withers, A.belly = _S["W"], _S["B"]
    A._ys = [_S["ysh"] - 0.7 + 0.1 * i for i in range(int((_S["yhip"] - _S["ysh"] + 1.4) / 0.1) + 2)]
    A._tops = [_back(y)[0] for y in A._ys]
    A._sides = [_flank(y, _back(y)[0] - 0.42) for y in A._ys]
    A.chest_y = _S["ysh"] - 0.44
    for name in ("Neck3", "Neck2", "Neck1", "Torso3"):
        s = _station(r.bone(name))
        A.neck[name] = (s[0].y, s[0].z, s[4], s[5])
    _legs(r, A)
    _head(r, A)
    _tail(r, A)
    A.skull = _S["skull"].z
    for shape, size in gl.each(sp.get("crown")):
        grow_crown(r, A, shape, size)
    for slot, table in OWN:
        for style, size in gl.each(sp.get(slot)):
            fn = table.get(style.partition(":")[0]) if isinstance(table, dict) else table
            if fn:
                fn(r, A, style, size)
            else:
                log("NO SUCH", slot.upper() + ":", style)
    # it is stood by the height a plain deer of its legs carries its head at, however it
    # carries its own: a lowered head does not make it a larger deer
    _S["true_skull"] = A.skull
    A.skull = _S["W0"] * 1.25


# the slots the wolf's own builder is not to see (they are this file's, or mean another thing here)
MINE = ("deer", "stance", "crown", "horn", "hung", "marks", "ears", "eyes", "tail", "neck", "maw", "throat", "breath", "hide", "back", "legs",
        "flank", "chest", "armor", "pose", "rest", "face", "fur", "feet", "ruff", "flags")
FRAME_KEYS = ("legs", "neck", "body", "stance")


def _pose(r, spec):
    """How it carries its head, put on last: everything grown on the head and neck goes too."""
    head, neck = _head_bones(r), list(NECK)
    for style, size in gl.each(spec.get("pose")):
        if style == "low":
            r.rotate(neck + head, r.bone("Neck1"), X, 0.4 * size)
        elif style == "high":
            r.rotate(neck + head, r.bone("Neck1"), X, -0.3 * size)
        elif style == "nod":
            r.rotate(head, r.bone("Head"), X, 0.4 * size)
        elif style == "back":         # looking back over its shoulder
            for i, b in enumerate(neck):
                r.rotate(neck[i:] + head, r.bone(b), Z, -0.38 * size)
            r.rotate(head, r.bone("Head"), Z, -0.3 * size)
        elif style == "aside":
            r.rotate(neck[1:] + head, r.bone("Neck2"), Z, -0.3 * size)
            r.rotate(head, r.bone("Head"), Z, -0.3 * size)
        elif style == "tilt":
            r.rotate(head, r.bone("Head"), Y, -0.45 * size)


def build(form_id, level, spec, base):
    _S.clear()
    _S["level"], _S["spec"] = level, spec
    _S["K"] = KINDS[spec.get("deer", "red")]
    _S["age"] = AGES[level]
    wspec = {k: v for k, v in spec.items() if k not in MINE}
    wspec["build"] = {k: v for k, v in spec.get("build", {}).items() if k in FRAME_KEYS}
    r, sockets = gl.wolf_form(form_id, level, wspec, species=frame, coat=("hide_red", "fur_cream"), marks=(), ages=ages, measure=measure)
    k = STAND / (_S["W0"] * 1.25)
    # the sockets on its head stand where its head is, not where a plain deer's would be
    hb = r.bone("Head")
    bpy.context.view_layer.update()
    if "socket_head" in sockets:
        sockets["socket_head"].matrix_world = Matrix.Translation((0, hb.y, _S["true_skull"] * k - 0.02))
    _pose(r, spec)
    path = os.path.join(gl.OUT, form_id + ".glb")
    if gl.rest(r, spec):
        gl.export_resting(r, sockets, path)
    else:
        gl.export(r, sockets, path)


def register(builders):
    global gl
    for name in ("genius_lines", "__main__"):
        m = sys.modules.get(name)
        if m is not None and getattr(m, "BUILDERS", None) is builders:
            gl = m
    builders["stag"] = build
