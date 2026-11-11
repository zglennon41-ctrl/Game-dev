"""WILDLINE genius lines, the Fox: a fox's body of its own on the wolf's bones
(docs/genius-lines.md, "The Fox"; genius_lines.py calls this file's register).

    python tools/blender/genius_lines.py fox
    python tools/blender/genius_lines.py fox fox-kit fox-of-many-tails

Of the wolf it keeps the skeleton and the clips, and nothing else. The frame is stood as a fox
stands (lower than a wolf, its feet close under it, its head carried up on a short neck) and
then every part is its own: one skin from the back of the skull to the rump (a shallow chest,
a long back, a waist tucked up); a broad skull drawn to a long pointed muzzle, with a small
dark nose, pale cheeks and chin and tufts at the cheek; eyes set forward and aslant, each a
lit iris with a slit of a pupil under a lid that comes down toward the nose; big triangular
ears on the wolf's ear bones, dark behind and pale within; fine legs in dark stockings, on
small neat paws; and a brush as long as its body on the wolf's tail bones, which is the
line's event.

Three Paths are three foxes (a form's `fox`): `red`, the red fox (long in the leg and the
muzzle, great pointed ears, a long brush streaming level behind it); `den`, the fox of the
cold and the earth (round, short in the leg and the face, small round ears, thick in the
neck, a brush as fat as itself carried low); `silver`, the silver fox of the stories (tall
and narrow, a long neck, the tallest ears, the longest brush, carried up like a flame).

Its slots (data/genius-bases/fox.json):

  fox       red, den, silver
  stance    how it carries its neck, made before its flesh is laid (CRANES)
  build     legs, neck, body (the frame); chest, girth, waist, nape, head, muzzle, ears,
            cheeks, paws (the flesh); tail (how long its brush), brush (how fat)
  tail      how it carries its brush (TAILS): level, low, up, over, flag, s, wrap, tuck;
            and what is on it: ember, rime
  tails     two, three, many
  tip       what its tail-tips carry: light, white, ring, flame, wisp, lantern
  marks     where it wears its Path's colour: stockings, socks, ears, band, rings, tip, brush,
            dorsal, saddle, blaze, bib, mask, cheeks, flecks (a step of the colour after a colon)
  ears      one, long, great, small, laid, torn
  eyes      third, lamp, old
  whiskers  long
  mouth     sack, prize;  maw: open, fangs
  ruff      mane, crown, frost, courtier;  neck: ivy
  mask      worn, raised, half;  face: two
  back      leaves, feathers, stripe;  feet: webbed, snow;  claws: dig;  fins: fox
  carry     panniers, pole, cape (and the wolf's: lamp, tags, book)
  pose      low, high, nod, back, aside, tilt (put on last)
  rest      the Wolf's ways of resting

The wolf's own spine, paws and aura still grow on it.
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
_S = {}         # the form being built: its spec, its stations, its brushes

PALETTE.update({
    "leaf": ((0.15, 0.21, 0.1), 0.9, 0.0), "leaf_dry": ((0.24, 0.17, 0.09), 0.9, 0.0), "bark": ((0.13, 0.095, 0.065), 0.95, 0.0),
    "mask_pale": ((0.82, 0.78, 0.68), 0.5, 0.0), "mask_red": ((0.4, 0.09, 0.07), 0.6, 0.0), "cape_red": ((0.3, 0.085, 0.07), 0.95, 0.0),
    "fin": ((0.19, 0.25, 0.27), 0.4, 0.0), "ash": ((0.5, 0.49, 0.47), 1.0, 0.0), "soot": ((0.03, 0.028, 0.032), 1.0, 0.0),
    "earth": ((0.1, 0.075, 0.055), 1.0, 0.0), "fur_grey": ((0.4, 0.39, 0.38), 0.9, 0.0), "fang": ((0.86, 0.82, 0.72), 0.35, 0.0),
    # a fox's stockings, the backs of its ears and the line round its eye: nearly black, and warm
    "fur_stocking": ((0.055, 0.045, 0.045), 0.9, 0.0), "fur_liner": ((0.03, 0.026, 0.028), 0.7, 0.0),
})

NECK = ("Neck1", "Neck2", "Neck3")
N_CHAIN = ("Torso3", "Neck1", "Neck2", "Neck3", "Head")
TAIL = tuple("Tail%d" % i for i in range(1, 9))


def log(*a):
    print("[lines_fox]", *a)


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



def _has(slot, *styles):
    return any(st.partition(":")[0] in styles for st, _ in gl.each(_S["spec"].get(slot)))


# ======================================================================================
# The frame: the wolf's bones stood as a fox stands
# ======================================================================================

# what each of the three foxes is, against the red fox
KINDS = {
    "red": dict(legs=1.0, body=1.0, neck=1.0, nape=1.0, girth=1.0, depth=1.0, wide=1.0, head=1.0, muzzle=1.0, skull=1.0, ears=1.0, earw=1.0, cheeks=1.0,
                brush=1.0, fat=1.0, tail="level", stance="alert", ruff=0.0),
    "den": dict(legs=0.8, body=0.94, neck=0.8, nape=1.3, girth=1.3, depth=1.2, wide=1.24, head=1.08, muzzle=0.7, skull=1.14, ears=0.56, earw=1.5, cheeks=1.5,
                brush=0.96, fat=1.36, tail="plume", stance="level", ruff=1.0),
    "silver": dict(legs=1.03, body=1.0, neck=1.14, nape=0.88, girth=0.88, depth=0.9, wide=0.9, head=0.96, muzzle=1.1, skull=0.94, ears=1.3, earw=0.86, cheeks=0.8,
                   brush=1.22, fat=0.96, tail="up", stance="proud", ruff=0.0),
}

# how it carries its neck: how steeply each of its three lengths rises, and how far its face
# falls below the level (degrees)
CRANES = {
    "alert": (34, 44, 50, 16), "proud": (50, 62, 70, 20), "watch": (42, 54, 60, 6), "level": (16, 18, 20, 12),
    "low": (2, -6, -10, 24), "sniff": (-18, -30, -36, 44), "sky": (54, 66, 76, -30), "sly": (24, 26, 24, 26),
}

# how it carries its brush: how steeply each of its seven lengths rises, going back (degrees),
# and how far each turns aside
TAILS = {
    "level": ((-4, 4, 10, 15, 18, 19, 16), 0), "hook": ((-24, -8, 14, 36, 56, 72, 82), 0), "low": ((-64, -60, -50, -38, -24, -9, 6), 0), "up": ((40, 56, 68, 76, 80, 76, 64), 0),
    "over": ((64, 88, 110, 130, 148, 162, 172), 0), "flag": ((76, 84, 88, 90, 90, 87, 82), 0), "s": ((66, 86, 100, 86, 64, 52, 66), 0),
    "wrap": ((-40, -30, -18, -8, 0, 6, 10), 25), "plume": ((24, 38, 48, 52, 50, 42, 30), 0), "tuck": ((-80, -92, -104, -118, -132, -146, -156), 0),
}

# its age, by its stage: the kit is more tail than fox
AGES = {
    1: dict(head=1.3, muzzle=0.62, eye=1.4, ears=1.2, neck=0.8, body=0.78, legs=0.72, depth=0.95, girth=1.25, wide=1.1, brush=0.92, fat=1.3, paws=1.3),
    2: dict(head=1.1, muzzle=0.92, eye=1.15, ears=1.08, neck=0.94, body=0.95, legs=0.96, depth=0.96, girth=1.04, wide=1.0, brush=0.96, fat=1.0, paws=1.1),
    3: dict(head=1.0, muzzle=1.0, eye=1.0, ears=1.0, neck=1.0, body=1.0, legs=1.0, depth=1.0, girth=1.0, wide=1.0, brush=1.0, fat=1.0, paws=1.0),
    4: dict(head=0.97, muzzle=1.03, eye=0.95, ears=1.0, neck=1.04, body=1.02, legs=1.02, depth=1.03, girth=1.03, wide=1.03, brush=1.1, fat=1.08, paws=1.0),
}


def _b(key, default=1.0):
    return float(_S["spec"].get("build", {}).get(key, default))


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
    """The wolf's bones, stood as a fox. (The flesh is laid on them by measure.)"""
    r.arm.data.pose_position = "REST"       # built at rest, as the Wolf is
    bpy.context.view_layer.update()
    K, age = _S["K"], _S["age"]
    head = _head_bones(r)
    legs = K["legs"] * age["legs"] * _b("legs")
    r.leg_length(0.36 - 1.0 * (legs - 1.0))
    # its feet close under it, and a narrow track: a fox walks as if along a line
    for tag in ("fl", "fr", "bl", "br"):
        side = ".L" if tag[1] == "l" else ".R"
        sg = 1 if tag[1] == "l" else -1
        root = r.bone(("FrontUpperLeg" if tag[0] == "f" else "BackLeg") + side)
        bones = [b for b in r.legs(tag) if not b.startswith("PoleTarget")]
        k = 0.62 if tag[0] == "f" else 0.78
        r.deform(bones, lambda p, y0=root.y, k=k, sg=sg: Vector((p.x - sg * 0.085, y0 + (p.y - y0) * k, p.z)))
    r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, 1.04 * age["body"] * K["body"] * _b("body"))
    r.lengthen_chain(list(NECK), head, 0.92 * K["neck"] * age["neck"] * _b("neck"))
    stance = gl.opt(_S["spec"].get("stance"))[0] or K["stance"]
    _S["crane"] = CRANES[stance]
    _crane(r, _S["crane"])


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
    """One skin from the back of its skull to its rump: a neck thick with fur where it leaves
    the chest; a shallow chest; a long level back; a waist tucked up; a narrow rump."""
    K, age = _S["K"], _S["age"]
    chest = _b("chest")
    girth = _b("girth") * K["girth"] * age["girth"]
    waist = _b("waist")
    nape = _b("nape") * K["nape"]
    sh, el, hip = r.bone("FrontUpperLeg.L"), r.bone("FrontLowerLeg.L"), r.bone("BackLeg.L")
    ysh, yhip = sh.y, hip.y
    W = sh.z + 0.5                                      # its withers
    D = 0.78 * age["depth"] * K["depth"] * (1.0 + 0.3 * (chest - 1.0))
    B = W - D                                           # its brisket
    cw = chest ** 0.7 * age["wide"] * K["wide"]
    gw = girth ** 0.8 * K["wide"] ** 0.5
    mid = (ysh + yhip) / 2
    tuck = (0.24 + 0.5 * (1.0 - waist)) * D / 0.78
    # the trunk: (y, its top, its underside, its half-breadth, crest, keel, egg)
    TR = [
        (ysh + 0.04, W, B + 0.05, 0.25 * cw, 0.03, 0.16, 0.1),
        (ysh + 0.42, W - 0.03, B, 0.31 * cw * gw ** 0.5, 0.05, 0.08, 0.1),
        (mid + 0.1, W - 0.06, B + 0.1 * tuck / 0.24, 0.3 * gw, 0.03, 0.0, 0.08),
        (yhip - 0.36, W - 0.07, B + tuck, 0.235 * gw * waist ** 0.6, 0.03, 0.0, 0.0),
        (yhip - 0.02, W - 0.05, B + tuck + 0.04, 0.27 * gw ** 0.6, 0.05, 0.0, -0.06),
        (yhip + 0.24, W - 0.15, B + tuck + 0.05, 0.2 * gw ** 0.5, 0.0, 0.0, 0.0),
        (yhip + 0.4, W - 0.36, B + tuck + 0.18, 0.09, 0.0, 0.0, 0.0),
    ]
    _S["trunk"] = TR
    _S["W"], _S["B"], _S["ysh"], _S["yhip"], _S["tuck"] = W, B, ysh, yhip, tuck
    trunk = [(Vector((0, y, (zt + zb) / 2)), a, (zt - zb) / 2, c, k, e) for y, zt, zb, a, c, k, e in TR]
    # where the neck leaves the chest: from before the withers down to the breast
    wf = Vector((0, ysh - 0.14, W - 0.04))
    br = Vector((0, ysh - 0.36 * (1.0 + 0.2 * (chest - 1.0)), B + 0.22))
    base = ((wf + br) / 2, 0.24 * cw * nape ** 0.4, (wf - br).length / 2, 0.0, 0.1, 0.0)
    J = [r.bone(nm) for nm in N_CHAIN[1:]]
    fj = _frames([base[0]] + J[1:])
    neck = []
    for (p, d, u, v), a, bb, off in zip(fj[1:], (0.215, 0.19, 0.165), (0.27, 0.225, 0.19), (0.26, 0.16, 0.08)):
        neck.append((p - v * (off * bb * nape), a * nape ** 0.8, bb * nape, 0.03, 0.0, 0.0))
    inn = (J[3] + (J[3] - J[2]).normalized() * 0.12 - fj[-1][3] * 0.02, 0.12, 0.13, 0.0, 0.0, 0.0)
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
    dark, light = mat("fur_dark"), mat("fur_light")
    _add(r, "body", g.loft(rings, caps=True), ws, dark, smooth=True)
    st = _station
    # pale under it: its belly, its breast and its throat, in one bib from the chin down
    _paint(r, "body", lambda c, n: st(c)[7] == "back" and n.dot(st(c)[3]) < -0.55, light)
    _paint(r, "body", lambda c, n: st(c)[7] == "neck" and n.dot(st(c)[3]) < -0.3 + 0.35 * (1.0 - st(c)[8]), light)
    _paint(r, "body", lambda c, n: st(c)[7] == "back" and st(c)[8] < 0.1 and n.y < -0.35 and c.z < W - 0.3, light)
    _paint(r, "body", lambda c, n: st(c)[7] == "back" and 0.1 < st(c)[8] < 0.66 and n.dot(st(c)[3]) > 0.62, kit.mark("saddle", dark))


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


def _paw(x, y, k=1.0):
    """A small neat paw: an oval of a foot and four toes before it."""
    geo = g.ico((x, y - 0.03 * k, 0.07 * k), 1.0, sub=1, scale=(0.078 * k, 0.12 * k, 0.07 * k))
    for dx, dy in ((-0.05, -0.1), (-0.018, -0.135), (0.018, -0.135), (0.05, -0.1)):
        geo = g.merge(geo, g.ico((x + dx * k, y + dy * k, 0.045 * k), 1.0, sub=1, scale=(0.026 * k, 0.045 * k, 0.04 * k)))
    return geo


def _legs(r, A):
    """Four fine legs: an elbow tucked against the chest, a long forearm, a small wrist; a lean
    thigh, a hock that shows, a long straight shank; in stockings, on small paws."""
    K, age = _S["K"], _S["age"]
    gk = (_b("girth") * K["girth"]) ** 0.55 * age["girth"] ** 0.7
    pk = age["paws"] * _b("paws") * K["wide"] ** 0.5
    dark, light = mat("fur_dark"), mat("fur_light")
    sock = mat("fur_stocking")
    _S["legs"] = {}
    for tag in ("fl", "fr", "bl", "br"):
        side = ".L" if tag[1] == "l" else ".R"
        sg = 1 if tag[1] == "l" else -1
        if tag[0] == "f":
            sh, el, ft = r.bone("FrontUpperLeg" + side), r.bone("FrontLowerLeg" + side), r.bone("IKFrontLeg" + side)
            x, yf = el.x, ft.y + 0.04
            zk = el.z * 0.34                              # its wrist
            yk = el.y + (yf - el.y) * 0.72
            st = [
                (Vector((x * 0.62, sh.y + 0.02, sh.z + 0.14)), 0.1, 0.2),
                (Vector((x * 0.9, sh.y + 0.03, sh.z - 0.06)), 0.105 * gk, 0.18 * gk),
                (Vector((x, el.y + 0.03, el.z + 0.04)), 0.092 * gk, 0.145 * gk),
                (Vector((x, el.y + (yk - el.y) * 0.4 + 0.01, el.z - 0.36 * (el.z - zk))), 0.064 * gk, 0.085 * gk),
                (Vector((x, yk + 0.012, zk + 0.14)), 0.05 * gk, 0.058 * gk),
                (Vector((x, yk, zk)), 0.052 * gk, 0.06 * gk),
                (Vector((x, yf + 0.03, 0.2)), 0.045 * gk, 0.05 * gk),
                (Vector((x, yf + 0.01, 0.07)), 0.05 * gk, 0.06 * gk),
            ]
            names, joints = ["FrontUpperLeg" + side, "FrontLowerLeg" + side], [sh, el, Vector((x, yf, 0.0))]
            zsock = el.z - 0.08
            knee = st[5][0]
        else:
            hp, sf, hk, ft = r.bone("BackLeg" + side), r.bone("BackUpperLeg" + side), r.bone("BackLowerLeg" + side), r.bone("IKBackLeg" + side)
            x, yf = sf.x, ft.y - 0.05
            st = [
                (Vector((x * 0.62, hp.y + 0.02, hp.z + 0.06)), 0.11, 0.24),
                (Vector((x * 0.95, hp.y + (sf.y - hp.y) * 0.55 + 0.1, hp.z + (sf.z - hp.z) * 0.55)), 0.13 * gk, 0.27 * gk),
                (Vector((x, sf.y + 0.09, sf.z)), 0.1 * gk, 0.17 * gk),
                (sf.lerp(hk, 0.45) + Vector((0, 0.03, 0)), 0.07 * gk, 0.1 * gk),
                (sf.lerp(hk, 0.82), 0.048 * gk, 0.064 * gk),
                (hk + Vector((0, 0.012, 0.0)), 0.05 * gk, 0.074 * gk),
                (hk.lerp(Vector((x, yf + 0.04, 0.2)), 0.3), 0.043 * gk, 0.052 * gk),
                (Vector((x, yf + 0.04, 0.2)), 0.043 * gk, 0.048 * gk),
                (Vector((x, yf + 0.01, 0.07)), 0.05 * gk, 0.06 * gk),
            ]
            names, joints = ["BackLeg" + side, "BackUpperLeg" + side, "BackLowerLeg" + side], [hp, sf, hk, Vector((x, yf, 0.0))]
            zsock = hk.z + 0.12
            knee = st[5][0]
        rings = _limb(st)
        ws = [_chain_w(names, joints, c) for c, _, _ in st for _ in range(8)]
        _add(r, "leg_" + tag, g.loft(rings, caps=True), ws, dark, smooth=True)
        _paint(r, "leg_" + tag, lambda c, n, zs=zsock, sg=sg: c.z >= zs and n.x * sg < -0.5, light)
        _paint(r, "leg_" + tag, lambda c, n, zs=zsock: c.z < zs, sock)
        _add(r, "paw_" + tag, _paw(x, yf, pk), names[-1], sock, smooth=True)
        _S["legs"][tag] = dict(x=x, y=yf, zsock=zsock, top=st[1][0].z, bone=names[-1], knee=knee, sg=sg)


def _fox_eye(c, R, look, upv, pa):
    """An eye with a slit of a pupil: the ball, and what each face of it is."""
    ball, kinds = gl._eyeball(c, R, look, upv * 0.8 + look * 0.4, pa)
    look = look.normalized()
    side = look.cross(upv).normalized()
    verts, faces = ball
    out = []
    for f, kd in zip(faces, kinds):
        w = (sum((verts[i] for i in f), Vector()) / len(f) - c).normalized()
        if kd == "glint":
            out.append(kd)
        elif w.angle(look) < pa * 1.12 and abs(w.dot(side)) < 0.26 * math.sin(pa):
            out.append("pupil")
        else:
            out.append("iris")
    return ball, out


def _head(r, A):
    """Its head: a broad skull and cheeks drawn to a long fine muzzle; a small dark nose; pale
    cheeks, lips and chin; eyes set forward and aslant, with a slit pupil, a lid that comes
    down toward the nose and a dark line from each corner; tufts at the cheek; big
    triangular ears on the wolf's ear bones."""
    sp, K, age, level = _S["spec"], _S["K"], _S["age"], _S["level"]
    S = 1.1 * age["head"] * K["head"] * _b("head")
    mz = K["muzzle"] * age["muzzle"] * _b("muzzle")
    sk = K["skull"]
    hb = r.bone("Head")
    phi = math.radians(_S["crane"][3])
    f = Vector((0, -math.cos(phi), -math.sin(phi)))       # toward its nose
    up = Vector((0, -math.sin(phi), math.cos(phi)))       # out of the top of its head

    def P(x, a, h):
        return hb + (X * x + f * a + up * h) * S
    _S["P"], _S["HS"], _S["hf"], _S["hup"] = P, S, f, up
    a0 = 0.3                                               # the eye; before it the muzzle is drawn out or kept short
    m = lambda a: a0 + (a - a0) * mz                       # noqa: E731
    yn = m(0.86)
    # along it from the poll: (how far forward, its top, its underside, its half-breadth)
    SK = [(-0.06, 0.04, -0.1, 0.1 * sk), (0.05, 0.155, -0.17, 0.185 * sk), (0.17, 0.185, -0.2, 0.225 * sk), (a0, 0.15, -0.19, 0.19 * sk),
          (m(0.42), 0.09, -0.15, 0.105 * sk ** 0.5), (m(0.54), 0.062, -0.125, 0.07), (m(0.68), 0.048, -0.108, 0.056),
          (m(0.8), 0.038, -0.094, 0.046), (yn, 0.026, -0.08, 0.036), (yn + 0.04, -0.005, -0.058, 0.018)]
    rings = []
    mm = 10
    for a, zt, zb, w in SK:
        zc, hh = (zt + zb) / 2 + 0.02, (zt - zb) / 2
        ring = []
        for j in range(mm):
            th = 2 * math.pi * j / mm
            cs, sn = math.cos(th), math.sin(th)
            ring.append(P(w * math.copysign(abs(cs) ** 0.8, cs) * (1.0 - 0.3 * max(0.0, sn) ** 2), a, zc - 0.02 + hh * math.copysign(abs(sn) ** 0.85, sn)))
        rings.append(ring)
    dark, light = mat("fur_dark"), mat("fur_light")
    _add(r, "head", g.loft(rings, caps=True), "Head", dark, smooth=True)
    along = lambda c: (c - hb).dot(f) / S                  # noqa: E731
    _paint(r, "head", lambda c, n: n.dot(up) < -0.35 and along(c) > 0.1, light)                      # its chin and jaw
    _paint(r, "head", lambda c, n: along(c) > m(0.4) and n.dot(up) < 0.35, light)                    # its lips and the sides of its muzzle
    _paint(r, "head", lambda c, n: 0.12 < along(c) <= m(0.42) and n.dot(up) < 0.05 and abs(n.x) > 0.3, light)   # its cheeks
    _paint(r, "head", lambda c, n: n.dot(up) > 0.72 and 0.16 < along(c) < m(0.7), kit.mark("mask", dark))
    _S["skull"] = P(0, 0.1, 0.18)
    _S["SK"], _S["m"], _S["yn"] = SK, m, yn
    # its nose, the line of its mouth (turned up at the corner: it is pleased with itself)
    _add(r, "nose_pad", g.ico(P(0, yn + 0.03, -0.012), 1.0, sub=1, scale=(0.04 * S, 0.042 * S, 0.036 * S), rot=(-phi, 0, 0)), "Head", mat("nose"), smooth=True)
    open_ = gl.opt(sp.get("maw"))[0] == "open"
    geo = None
    for sg in (1, -1):
        pts = [P(sg * (SK[i][3] * 0.95 + 0.004), SK[i][0], SK[i][2] + dz) for i, dz in ((4, 0.075), (5, 0.04), (6, 0.036), (7, 0.034), (8, 0.03))]
        geo = g.merge(geo, g.tube(pts, [0.004, 0.008, 0.008, 0.007, 0.004], n=4))
    if not open_:
        _add(r, "mouth", geo, "Head", mat("fur_liner"), smooth=True)
    else:                         # its mouth open: the lower jaw dropped, the dark of it, small teeth
        jaw = [[P(sg * w, a, h) for sg, w, h in ((1, 0.8 * SK[i][3], -0.03), (1, 0.6 * SK[i][3], -0.07), (-1, 0.6 * SK[i][3], -0.07), (-1, 0.8 * SK[i][3], -0.03))]
               for i, a in ((4, SK[4][0]), (6, SK[6][0]), (8, SK[8][0] - 0.02))]
        hinge = P(0, SK[4][0], SK[4][2] + 0.05)
        Rj = Matrix.Rotation(-0.4, 3, X)
        drop = [[hinge + Rj @ (q - hinge) - up * 0.035 * S for q in ring] for ring in jaw]
        _add(r, "jaw", g.loft(drop, caps=True), "Head", light, smooth=True)
        _add(r, "maw", g.ico(P(0, m(0.6), -0.1), 1.0, sub=1, scale=(0.045 * S, 0.17 * S * mz, 0.03 * S), rot=(-phi + 0.2, 0, 0)), "Head", mat("hide_maw"), smooth=True)
    # the eyes
    style = gl.opt(sp.get("eyes"))[0]
    Re = 0.062 * S * age["eye"] * (1.25 if style == "lamp" else 1.0)
    liner = mat("fur_liner")
    eye_m = {"iris": field("eyes", 3.6 if style != "lamp" else 4.6), "pupil": mat("eye_dark"), "glint": mat("eye_white")}
    lidk = {"old": 0.46, "lamp": 0.0}.get(style, 0.3 if level > 1 else 0.06)
    ex, eh = 0.128 * sk, 0.082
    for sg, tag in ((1, "l"), (-1, "r")):
        s = P(sg * ex, a0 + 0.0, eh)
        out = (X * sg * 0.66 + f * 0.56 + up * 0.5).normalized()
        c = s - out * (Re * 0.5)
        look = (X * sg * 0.42 + f * 0.9 + up * 0.08).normalized()
        ball, kinds = _fox_eye(c, Re, look, up, math.radians(50))
        gl._later(r, "blink", "eye", None, c, "Head", side=tag, solid=(ball, [eye_m[k] for k in kinds]))
        # the dark rim it is set in, drawn long: back and up from its outer corner, forward and
        # down the muzzle from its inner
        e1 = (f * 0.8 - X * sg * 0.5 - up * 0.34).normalized()      # along the eye, toward the nose
        e2 = out.cross(e1).normalized()
        _add(r, "eye_rim_" + tag, gl._lens(s - out * (Re * 0.34), out, e1, e2, Re * 1.55, Re * 1.12, Re * 0.2), "Head", liner, smooth=True)
        o0 = s - e1 * (Re * 1.2) - out * 0.012
        _add(r, "liner_" + tag, g.blade(o0, o0 - e1 * (0.15 * S) + up * (0.035 * S) + X * sg * 0.02 * S, 0.04 * S, normal=out, belly=0.3), "Head", liner, smooth=True)
        t0 = s + e1 * (Re * 1.15) - out * 0.012
        _add(r, "tear_" + tag, g.blade(t0, P(sg * SK[5][3] * 0.9, SK[5][0], 0.035), 0.034 * S, normal=(out + up).normalized(), belly=0.3), "Head", liner, smooth=True)
        if lidk > 0.0:            # its lid: down toward the nose, up toward the ear
            lu = (up * 0.82 - X * sg * 0.36 + f * 0.34 + out * 0.1).normalized()
            _add(r, "lid_" + tag, gl._lid(c, Re * 1.1, lu, math.acos(max(-0.6, min(0.97, 0.9 * (1.0 - 2.0 * lidk) / 1.1)))), "Head", dark if style != "old" else mat("fur_grey"), smooth=True)
        if level > 1:             # and a brow over it, the same way
            b0 = s + up * (Re * 1.5) + e1 * (Re * 1.3) + out * 0.004
            _add(r, "brow_" + tag, g.blade(b0, b0 - e1 * (Re * 3.4) + up * (Re * 1.0), 0.05 * S, normal=(out + up * 0.6).normalized(), belly=0.4),
                 "Head", light if style == "old" else dark, smooth=True)
    A.eye = P(ex, a0, eh)
    A.eye_r, A.eye_n = Re, (X * 0.66 + f * 0.56 + up * 0.5).normalized()
    A.nose = P(0, yn + 0.04, -0.03)
    # tufts at its cheeks: pale, swept back and down
    ck = K["cheeks"] * _b("cheeks") * (0.7 if level == 1 else 1.0)
    geo = None
    for sg in (1, -1):
        for i in range(4):
            b0 = P(sg * 0.19 * sk, 0.2 - 0.045 * i, -0.02 - 0.04 * i)
            d = (X * sg * (0.8 - 0.1 * i) - f * (0.5 + 0.1 * i) - up * (0.1 + 0.2 * i)).normalized()
            geo = g.merge(geo, g.blade(b0 - d * 0.03, b0 + d * (0.2 + 0.02 * i) * S * ck, 0.13 * S * ck ** 0.5, normal=(X * sg * 0.5 + f * 0.6 + up * 0.5), belly=0.35))
    _add(r, "cheeks", geo, "Head", light, smooth=True)
    # its whiskers
    wl = 1.0
    for st_, sz in gl.each(sp.get("whiskers")):
        wl = 1.0 + 0.9 * sz
    if "whiskers" in sp or level > 1:
        wh = None
        for sg in (1, -1):
            for k, (dy, dz) in enumerate(((0.1, 0.07), (0.02, 0.0), (0.08, -0.08))):
                b0 = P(sg * SK[6][3] * 0.95, SK[6][0] + 0.01 * k, -0.04)
                tip = b0 + (X * sg * 0.26 - f * dy + up * dz) * (S * wl)
                wh = g.merge(wh, g.tube([b0, b0.lerp(tip, 0.5) - up * 0.012, tip], [0.006, 0.005, 0.002], n=3))
        _add(r, "whiskers", wh, "Head", mat("whisker"))
    # the ears: tall triangles cupped forward, on the wolf's ear bones, so they flick as its did
    how = {st_: sz for st_, sz in gl.each(sp.get("ears"))}
    ek = K["ears"] * age["ears"] * _b("ears")
    ew = K["earw"]
    if "long" in how:
        ek *= 1.0 + 0.3 * how["long"]
    if "great" in how:
        ek *= 1.0 + 0.5 * how["great"]
        ew *= 1.0 + 0.2 * how["great"]
    if "small" in how:
        ek *= 1.0 - 0.3 * how["small"]
    _S["ear_in"] = []
    for sg, tag, side in ((1, "l", ".L"), (-1, "r", ".R")):
        root = P(sg * 0.125 * sk, 0.075, 0.13)
        d = (X * sg * 0.36 + up * 0.92 - f * 0.12).normalized()
        op = (f * 0.86 + X * sg * 0.5 + up * 0.1)              # the way its cup opens
        L = 0.46 * S * ek
        if "one" in how and sg < 0:                            # one ear turned behind, listening there
            d = (X * sg * 0.62 + up * 0.7 - f * 0.4).normalized()
            op = (-f * 0.5 + X * sg * 0.85)
        if "laid" in how:
            k = how["laid"]
            d = (X * sg * 0.36 + up * (0.92 - 0.7 * k) - f * (0.12 + 0.8 * k)).normalized()
            op = (X * sg * 0.8 + up * 0.5 + f * 0.2)
        if "torn" in how and sg < 0:
            L *= 0.6
        op = (op - d * op.dot(d)).normalized()
        es = d.cross(op).normalized()
        round_ = ew > 1.2
        prof = ((0.0, 0.8), (0.16, 1.0), (0.4, 0.86), (0.66, 0.56), (0.86, 0.26), (1.0, 0.03)) if not round_ else \
               ((0.0, 0.8), (0.18, 1.0), (0.45, 0.98), (0.72, 0.78), (0.92, 0.42), (1.0, 0.1))
        rings = []
        for t, wk in prof:
            c = root + d * (L * t) + op * (0.03 * S * math.sin(math.pi * t))
            hw, cup = 0.155 * S * ew * ek ** 0.4 * wk, 0.07 * S * wk
            rings.append([c - es * hw, c - es * hw * 0.62 - op * cup, c - op * cup * 1.25, c + es * hw * 0.62 - op * cup, c + es * hw, c - op * cup * 0.2])
        fam = r.family("Ear1" + side)
        old = [r.bone(nm) for nm in fam]
        d0 = (old[-1] - old[0])
        Rm = d0.normalized().rotation_difference(d).to_matrix()
        kL = L * 0.8 / max(1e-6, d0.length)
        r.deform(fam, lambda p, o=old[0], Rm=Rm, kL=kL, root=root: root + Rm @ (p - o) * kL, rot=Rm)
        joints = [r.bone(nm) for nm in fam] + [root + d * L]
        ws = [_chain_w(fam, joints, q) for ring in rings for q in ring]
        _add(r, "ear_" + tag, g.loft(rings, caps=True), ws, mat("fur_stocking"), smooth=True)
        _paint(r, "ear_" + tag, lambda c, n, op=op: n.dot(op) > 0.25, light)
        _paint(r, "ear_" + tag, lambda c, n, op=op, root=root, d=d, L=L: n.dot(op) <= 0.25 and (c - root).dot(d) < 0.42 * L, dark)
        _S["ear_in"].append(("ear_" + tag, op, root, d, L))
        # a tuft of pale fur in it
        tb = root + d * (L * 0.1) + op * 0.02
        tuft = g.merge(g.blade(tb, tb + d * (L * 0.5) + op * 0.02 - es * 0.03 * S, 0.07 * S, normal=op, belly=0.3),
                       g.blade(tb + es * 0.03 * S, tb + d * (L * 0.36) + op * 0.03 + es * 0.06 * S, 0.06 * S, normal=op, belly=0.3))
        _add(r, "eartuft_" + tag, tuft, [_chain_w(fam, joints, q) for q in tuft[0]], light, smooth=True)
    _S["ear_top"] = max(P(0.125, 0.075, 0.13).z + 0.46 * S * ek, _S["skull"].z)


# ======================================================================================
# The brush: the line's event
# ======================================================================================

BRUSH = ((0.0, 0.3), (0.1, 0.52), (0.24, 0.84), (0.42, 1.0), (0.6, 0.98), (0.76, 0.8), (0.88, 0.52), (0.96, 0.24), (1.0, 0.03))


def _prof(t):
    for (t0, k0), (t1, k1) in zip(BRUSH, BRUSH[1:]):
        if t <= t1:
            return k0 + (k1 - k0) * (t - t0) / (t1 - t0)
    return BRUSH[-1][1]


def _carry_tail(r):
    """Lay the wolf's tail bones along its brush: at its root, to its length, each length of it
    at its pitch."""
    sp, K, age = _S["spec"], _S["K"], _S["age"]
    tr = _S["trunk"]
    root = Vector((0, tr[-2][0] + 0.04, tr[-2][1] - 0.1))
    fam = list(TAIL)
    r.deform(fam, lambda p, t1=r.bone("Tail1"): p + (root - t1))
    now = (r.bone("Tail8") - r.bone("Tail1")).length * 8 / 7
    want = 2.5 * K["brush"] * age["brush"] * _b("tail") * _S["age"]["body"] ** 0.5
    r.lengthen_chain(fam, [], want / now)
    pitch = list(TAILS[K["tail"]][0])
    yaw = TAILS[K["tail"]][1]
    for style, size in gl.each(sp.get("tail")):
        if style in TAILS:
            base = TAILS["level"][0]
            pitch = [b + (p - b) * size for b, p in zip(base, TAILS[style][0])]
            yaw = TAILS[style][1] * size
    for i in range(7):
        a, b = r.bone(TAIL[i]), r.bone(TAIL[i + 1])
        turn = pitch[i] - math.degrees(math.atan2(b.z - a.z, b.y - a.y))
        if abs(turn) > 0.01:
            r.rotate(fam[i:], a, X, math.radians(turn))
    if yaw:
        for i in range(1, 8):
            r.rotate(fam[i:], r.bone(TAIL[i]), Z, math.radians(yaw))
    J = [r.bone(nm) for nm in TAIL]
    J.append(J[-1] + (J[-1] - J[-2]))
    _S["tail_root"], _S["tail_joints"], _S["tail_len"] = root, J, want


def _brush(r, name, M=None, fat=1.0, long=1.0, shag=True):
    """One brush along the tail bones (or, by M, turned about its root from there): a spindle
    of fur, thin at the root, thickest past its middle, drawn to a point; shaggy under."""
    K, age = _S["K"], _S["age"]
    J = _S["tail_joints"]
    root = J[0]
    line = _cr(J, 2)
    if long != 1.0:
        line = [root + (p - root) * long for p in line]
    if M is not None:
        line = [root + M @ (p - root) for p in line]
    fr = _frames(line)
    lens = [0.0]
    for a, b in zip(line, line[1:]):
        lens.append(lens[-1] + (b - a).length)
    R = 0.37 * K["fat"] * age["fat"] * _b("brush") * fat
    mm = 10
    rings, ws, stations = [], [], []
    for i, (p, d, u, v) in enumerate(fr):
        t = lens[i] / lens[-1]
        rad = max(0.008, R * _prof(t))
        # (the weights are the bones' own places along the brush it was turned from)
        q = root + (M.inverted() @ (p - root) if M is not None else (p - root)) / long
        w = _chain_w(list(TAIL), J, q)
        rings.append(_ring(p, u, v, rad, rad * 1.04, m=mm, egg=0.08))
        ws.extend([w] * mm)
        stations.append((p, d, u, v, rad, w, t))
    dark, light = mat("fur_dark"), mat("fur_light")
    _add(r, name, g.loft(rings, caps=True), ws, dark, smooth=True)
    near = lambda c: min(stations, key=lambda s: (s[0] - c).length_squared)   # noqa: E731
    _paint(r, name, lambda c, n: near(c)[6] > 0.8, kit.mark("tailtip", light))
    _paint(r, name, lambda c, n: near(c)[6] <= 0.8 and n.dot(near(c)[3]) < -0.75 and near(c)[6] > 0.1, light)
    if shag:                      # locks of fur standing off it, back along it: its outline is fur
        geo, wg, geo2, wg2 = None, [], None, []
        for i, s in enumerate(stations):
            p, d, u, v, rad, w, t = s
            if not 0.2 < t < 0.9 or i % 2:
                continue
            for k, deg in enumerate((250, 290, 20, 160, 90)):
                if (i // 2 + k) % 2 and k > 1:
                    continue
                th = math.radians(deg + 14 * math.sin(i * 1.7 + k))
                n = u * math.cos(th) + v * math.sin(th)
                b0 = p + n * (rad * 0.8)
                bl = g.blade(b0, b0 + (d * 0.95 + n * 0.32).normalized() * (rad * 0.9), rad * 0.55, normal=n, belly=0.35)
                if t > 0.74:
                    geo2, wg2 = g.merge(geo2, bl), wg2 + [w] * len(bl[0])
                else:
                    geo, wg = g.merge(geo, bl), wg + [w] * len(bl[0])
        if geo:
            _add(r, name + "_shag", geo, wg, dark, smooth=True)
        if geo2:
            _add(r, name + "_shag_tip", geo2, wg2, kit.mark("tailtip", light), smooth=True)
    _S.setdefault("brushes", []).append((name, stations, near))
    end = stations[-1]
    _S.setdefault("tips", []).append((end[0], end[1]))


def _tail(r, A):
    sp = _S["spec"]
    _carry_tail(r)
    J = _S["tail_joints"]
    root = J[0]
    m = (J[-1] - root).normalized()
    ax = m.cross(X)
    ax = ax.normalized() if ax.length > 1e-4 else Y.copy()
    many = gl.opt(sp.get("tails"))[0]
    if many == "two":             # two, carried so that you will notice
        for i, a in enumerate((0.36, -0.36)):
            _brush(r, "brush_%d" % i, Matrix.Rotation(a, 3, ax), fat=0.9)
    elif many == "three":
        for i, (a, k) in enumerate(((0.0, 1.0), (0.5, 0.9), (-0.5, 0.9))):
            _brush(r, "brush_%d" % i, Matrix.Rotation(a, 3, ax) if a else None, fat=0.86, long=k)
    elif many == "many":          # nine, fanned behind it like a hand of cards
        for i, a in enumerate((0.0, 0.3, -0.3, 0.6, -0.6, 0.9, -0.9, 1.2, -1.2)):
            lean = Matrix.Rotation(-0.1 * abs(a), 3, X)
            _brush(r, "brush_%d" % i, lean @ Matrix.Rotation(a, 3, ax) if a else None, fat=0.74, long=1.0 - 0.1 * abs(a), shag=i < 1)
    else:
        _brush(r, "brush_0")


def _tips():
    return _S.get("tips", [])


def grow_tip(r, A, style, size):
    """What its tail-tips carry."""
    for i, (p, d) in enumerate(_tips()):
        bone = "Tail8"
        if style == "light":      # a light riding at the tip
            c = p + d * 0.14
            gl._later(r, "pulse", "tiplight", [(g.ico(c, 0.11 * size, sub=2), field("foxfire", 3.6))], c, bone, n=i)
        elif style == "white":    # a white tip that carries a light of its own, and bobs
            _add(r, "tipmop_%d" % i, g.ico(p - d * 0.14, 0.3 * size, sub=2, scale=(0.9, 0.9, 1.1)), bone, mat("fur_pale"), smooth=True)
            c = p + d * 0.26 * size
            gl._later(r, "bob", "tiplight", [(g.ico(c, 0.12 * size, sub=2), field("foxfire", 3.8))], c, bone, n=i)
        elif style == "ring":     # a thin ring of light spinning round it
            c = p - d * 0.2
            Rm = Z.rotation_difference(d).to_matrix().to_4x4()
            ring = g.moved(g.merge(_hoop((0, 0, 0), Z, 0.44 * size, 0.028), _hoop((0, 0, 0.1), Z + X * 0.4, 0.33 * size, 0.02)), Matrix.Translation(c) @ Rm)
            gl._later(r, "spin", "tipring", [(ring, field("ring", 3.4))], c, bone, n=i)
            _add(r, "tiplight_%d" % i, g.ico(p + d * 0.08, 0.08 * size, sub=1), bone, field("foxfire", 3.4))
        elif style == "flame":    # a small steady flame
            f0 = p - d * 0.04
            outer = g.tongue([f0, f0 + Vector((0.04, 0, 0.24 * size)), f0 + Vector((-0.03, 0, 0.5 * size)), f0 + Vector((0.01, 0, 0.74 * size))],
                             [0.26 * size, 0.24 * size, 0.13 * size, 0.02], thick=0.7, normal=Y)
            inner = g.tongue([f0 + Y * 0.0, f0 + Vector((0.02, 0, 0.16 * size)), f0 + Vector((0.0, 0, 0.4 * size))], [0.14 * size, 0.12 * size, 0.02], thick=0.9, normal=Y)
            gl._later(r, "flick", "tipflame", [(outer, field("flame", 3.0)), (inner, field("flame_heart", 4.4))], f0, bone, n=i)
            _add(r, "tipwick_%d" % i, g.ico(f0, 0.06 * size, sub=0), bone, mat("coal"))
        elif style == "wisp":     # a light that floats a little above where it should be
            c = p + Vector((0, 0, 0.4 * size))
            items = [(g.ico(c, 0.14 * size, sub=2, scale=(0.9, 0.9, 1.2)), field("foxfire", 3.8)),
                     (g.tongue([c + Vector((0, 0, -0.1)), c + Vector((0.04, 0, -0.22)), c + Vector((-0.02, 0, -0.34))], [0.11, 0.07, 0.01], thick=0.6, normal=Y), field("foxfire_tail", 2.2))]
            gl._later(r, "bob", "wisp", items, c, bone, n=i)
        elif style == "lantern":  # a small lamp hung from the end of it
            away = Vector((d.x, d.y, 0.0))
            away = away.normalized() if away.length > 0.3 else Y.copy()
            hook = p + d * 0.08 + away * 0.14 + Z * 0.1
            _add(r, "tiphook_%d" % i, g.tube([p - d * 0.14, p + d * 0.06 + Z * 0.06, hook], [0.026, 0.024, 0.02], n=4), bone, mat("metal_brass"))
            gl._later(r, "sway", "tiplamp", gl._lantern(hook + Vector((0, 0, -0.06)), 0.3 * size, "lamp", 3.6), hook, bone, n=i, hang=True)
        else:
            log("NO SUCH TIP:", style)


def grow_tail(r, A, style, size):
    """What is on its brush (how it is carried is its frame's)."""
    if style in TAILS:
        return
    acc = bool(_S["spec"].get("accent"))
    if style == "ember":          # the tip of its tail is a live coal, held away from the bedding
        for i, (name, stations, near) in enumerate(_S.get("brushes", [])):
            _paint(r, name, lambda c, n, near=near: near(c)[6] > 0.72, mat("coal"))
            _paint(r, name + "_shag_tip", lambda c, n: True, mat("coal"))
            p, d = _tips()[i]
            c = p - d * 0.16
            gl._later(r, "pulse", "ember", [(g.ico(c, 0.17 * size, sub=1, scale=(0.9, 0.9, 1.1)), field("ember", 3.8))], c, "Tail8", n=i)
            geo = None
            for k in range(5):
                a = k * 1.9
                q = c + Vector((0.16 * math.cos(a), 0.12 * math.sin(a), 0.16 + 0.11 * k)) * size
                geo = g.merge(geo, g.ico(q, 0.03 * size * (1.0 - 0.1 * k), sub=0))
            gl._later(r, "flick", "sparks", [(geo, field("ember_sparks", 3.2))], c, "Tail8", n=i)
    elif style == "rime":         # white rime standing on its brush
        for name, stations, near in _S.get("brushes", []):
            geo, ws, geo2, ws2 = None, [], None, []
            for i, s in enumerate(stations):
                p, d, u, v, rad, w, t = s
                if t < 0.22 or i % 2 == 0:
                    continue
                for k in range(5):
                    th = math.pi * (0.1 + 0.8 * k / 4) + 0.3 * math.sin(i * 1.3)
                    n = u * math.cos(th) + v * math.sin(th)
                    b0 = p + n * rad * 0.85
                    bl = g.blade(b0, b0 + n * (0.24 * size) + d * 0.08, 0.1, normal=d, belly=0.2)
                    if (i // 2 + k) % 2:
                        geo, ws = g.merge(geo, bl), ws + [w] * len(bl[0])
                    else:
                        geo2, ws2 = g.merge(geo2, bl), ws2 + [w] * len(bl[0])
            _add(r, name + "_rime", geo, ws, mat("ice_pale"), smooth=False)
            _add(r, name + "_rime_b", geo2, ws2, _am("pale") if acc else mat("ice"), smooth=False)
    else:
        log("NO SUCH TAIL:", style)


# ======================================================================================
# Its Path's colour (docs/genius-lines.md, "A Path's colour")
# ======================================================================================

def grow_marks(r, A, style, size):
    """Where it wears its Path's colour: the faces of its own skin and its brush, painted."""
    what, _, step = style.partition(":")
    m = _am(step)
    st = _station
    f, up, hb, S = _S["hf"], _S["hup"], r.bone("Head"), _S["HS"]

    def bd(pick):
        _paint(r, "body", pick, m)

    def legs(pick):
        for tag, L in _S["legs"].items():
            _paint(r, "leg_" + tag, lambda c, n, L=L: pick(c, n, L), m)

    def brush(pick, mm=None, shag=None):
        for name, stations, near in _S.get("brushes", []):
            _paint(r, name, lambda c, n, near=near: pick(near(c), n), mm or m)
            if shag is not None:
                for part, t in ((name + "_shag", 0.5), (name + "_shag_tip", 0.85)):
                    if shag(t):
                        _paint(r, part, lambda c, n: True, mm or m)
    if what == "stockings":       # the whole of its stockings, and its paws
        legs(lambda c, n, L: c.z < L["zsock"])
        for tag in _S["legs"]:
            _paint(r, "paw_" + tag, lambda c, n: True, m)
    elif what == "socks":         # the foot of each stocking
        legs(lambda c, n, L: c.z < L["zsock"] * 0.5)
        for tag in _S["legs"]:
            _paint(r, "paw_" + tag, lambda c, n: True, m)
    elif what == "garters":       # a band at the top of each stocking
        legs(lambda c, n, L: L["zsock"] - 0.02 < c.z < L["zsock"] + 0.16 * size)
    elif what == "ears":          # the backs of its ears
        for part, op, root, d, L in _S["ear_in"]:
            _paint(r, part, lambda c, n, op=op, root=root, d=d, L=L: n.dot(op) <= 0.25 and (c - root).dot(d) > 0.3 * L, m)
    elif what == "inner":         # the inside of its ears
        for part, op, root, d, L in _S["ear_in"]:
            _paint(r, part, lambda c, n, op=op: n.dot(op) > 0.25, m)
    elif what == "band":          # a band round its brush before the tip
        brush(lambda s, n: 0.8 - 0.2 * size < s[6] <= 0.8)
    elif what == "rings":         # rings down its brush
        brush(lambda s, n: 0.18 < s[6] <= 0.8 and int(s[6] * (5 + 3 * size)) % 2 == 1)
    elif what == "tip":           # the tip of its brush
        brush(lambda s, n: s[6] > 0.8, shag=lambda t: t > 0.8)
    elif what == "brush":         # its brush from the middle, deepening to the tip
        brush(lambda s, n: 0.42 < s[6] <= 0.62, _am("deep"))
        brush(lambda s, n: 0.62 < s[6] <= 0.8, _am(""), shag=lambda t: t < 0.8)
        brush(lambda s, n: s[6] > 0.8, _am("light"), shag=lambda t: t > 0.8)
    elif what == "dorsal":        # a stripe from its brow down its back and along its brush
        bd(lambda c, n: n.dot(st(c)[3]) > 0.8)
        brush(lambda s, n: n.dot(s[3]) > 0.7 and 0.04 < s[6] <= 0.8)
        _paint(r, "head", lambda c, n: n.dot(up) > 0.8 and abs(c.x) < 0.07 * S and (c - hb).dot(f) < _S["m"](0.75) * S, m)
    elif what == "saddle":
        bd(lambda c, n: st(c)[7] == "back" and 0.06 < st(c)[8] < 0.7 and n.dot(st(c)[3]) > 0.3)
    elif what == "cross":         # the cross fox's: down its back and across its shoulders
        bd(lambda c, n: n.dot(st(c)[3]) > 0.74 or (st(c)[7] == "back" and st(c)[8] < 0.16 and n.dot(st(c)[3]) > -0.2))
    elif what == "bib":           # its breast and throat
        bd(lambda c, n: (st(c)[7] == "neck" and n.dot(st(c)[3]) < -0.3 + 0.35 * (1.0 - st(c)[8])) or (st(c)[7] == "back" and st(c)[8] < 0.1 and n.y < -0.35 and c.z < _S["W"] - 0.3))
    elif what == "blaze":         # a stroke up its face
        _paint(r, "head", lambda c, n: n.dot(up) > 0.6 and 0.14 * S < (c - hb).dot(f), m)
    elif what == "mask":          # across its eyes
        _paint(r, "head", lambda c, n: 0.2 * S < (c - hb).dot(f) < _S["m"](0.46) * S and n.dot(up) > -0.2, m)
    elif what == "cheeks":
        _paint(r, "cheeks", lambda c, n: True, m)
    elif what == "flecks":        # flecks of it through its coat, along its flanks
        spots = []
        back = [s for s in _S["body"] if s[7] == "back" and 0.06 < s[8] < 0.88]
        for i, s in enumerate(back):
            for k, deg in enumerate((60, 34, 10)):
                if (i + k) % 2:
                    continue
                rad = (0.06 - 0.01 * k) * size * (1.0 + 0.2 * math.sin(i * 2.1 + k))
                spots += [(s, deg + 5 * math.sin(i * 1.7), rad), (s, 180 - deg - 5 * math.sin(i * 1.7), rad)]
        _lenses(r, "flecks", spots, m)
    else:
        log("NO SUCH MARK:", what)


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


# ======================================================================================
# What it has grown or been given
# ======================================================================================

def _neck_at(t):
    """The place on its neck a share t of the way from the chest to the skull."""
    return min(_S["neckline"], key=lambda s: abs(s[8] - t))


def grow_ruff(r, A, style, size):
    nl = _S["neckline"]
    acc = bool(_S["spec"].get("accent"))
    if style == "mane":           # a thick ruff of fur at its throat and round the foot of its neck
        g1, g2, w1, w2 = None, None, [], []
        for i, s in enumerate(nl):
            t = s[8]
            if not 0.06 < t < 0.9 or i % 2:
                continue
            for k, deg in enumerate((202, 230, 256, 284, 310, 338)):
                p, n = _on(s, deg + 6 * math.sin(i * 1.3), -0.01)
                L = 0.3 * size * (0.7 + 0.6 * (1.0 - t)) * (1.0 + 0.25 * math.sin(i * 2.3 + k * 1.9))
                mid = p + n * (0.42 * L) - Z * (0.3 * L) + s[1] * (0.3 * L)
                tip = p + n * (0.46 * L) - Z * (0.75 * L) + s[1] * (0.6 * L)
                lk = g.tongue([p, mid, tip], [0.15 * (0.7 + 0.3 * size), 0.13 * (0.7 + 0.3 * size), 0.015], thick=0.3, normal=n)
                if (i // 2 + k) % 2:
                    g2, w2 = g.merge(g2, lk), w2 + [s[6]] * len(lk[0])
                else:
                    g1, w1 = g.merge(g1, lk), w1 + [s[6]] * len(lk[0])
        _add(r, "ruff", g1, w1, mat("fur_light"), smooth=True)
        _add(r, "ruff_b", g2, w2, mat("fur_light"), smooth=True)
    elif style == "crown":        # a crest of fur standing between its ears and down its nape
        geo, ws = None, []
        P, S, up, f = _S["P"], _S["HS"], _S["hup"], _S["hf"]
        for k in range(3):
            b0 = P(0, 0.16 - 0.08 * k, 0.17)
            geo = g.merge(geo, g.blade(b0, b0 + (up * 0.9 - f * (0.2 + 0.25 * k)).normalized() * (0.26 - 0.03 * k) * size * 1.4, 0.1 * S, normal=X, belly=0.35))
        ws = ["Head"] * 0
        _add(r, "crest_head", geo, "Head", _am("light") if acc else mat("fur_pale"), smooth=True)
        geo, ws = None, []
        for i, s in enumerate(nl):
            if not 0.2 < s[8] < 0.98:
                continue
            p, n = _on(s, 90, -0.01)
            bl = g.blade(p, p + (n * 0.9 + s[1] * 0.45).normalized() * (0.2 + 0.1 * s[8]) * size * 1.4, 0.1, normal=X, belly=0.35)
            geo, ws = g.merge(geo, bl), ws + [s[6]] * len(bl[0])
        _add(r, "crest", geo, ws, _am() if acc else mat("fur_pale"), smooth=True)
    elif style == "frost":        # rime standing in its ruff
        s = _neck_at(0.5)
        geo, geo2 = None, None
        for j in range(14):
            p, n = _on(s, 360.0 * j / 14, 0.0)
            bl = g.blade(p, p + (n * 0.9 + s[1] * 0.4).normalized() * (0.26 + 0.07 * (j % 3)) * size, 0.12, normal=s[1], belly=0.25)
            if j % 2:
                geo = g.merge(geo, bl)
            else:
                geo2 = g.merge(geo2, bl)
        _add(r, "ruff_rime", geo, [s[6]] * len(geo[0]), mat("ice_pale"), smooth=False)
        _add(r, "ruff_rime_b", geo2, [s[6]] * len(geo2[0]), mat("ice"), smooth=False)
    elif style == "courtier":     # a stiff pale ruff, pleated, all the way round
        s = _neck_at(0.62)
        n_ = 16
        rings = [[], []]
        for j in range(n_):
            p, n = _on(s, 360.0 * j / n_, 0.0)
            zig = 0.05 if j % 2 else -0.05
            rings[0].append(p - n * 0.02 + s[1] * 0.0)
            rings[1].append(p + n * (0.3 * size) + s[1] * zig)
        geo = g.merge(g.loft([rings[0], rings[1]], caps=False), g.loft([[q + s[1] * 0.03 for q in rings[1]], [q + s[1] * 0.03 for q in rings[0]]], caps=False))
        _add(r, "ruff_court", geo, [s[6]] * len(geo[0]), mat("fur_pale"), smooth=False)
    else:
        log("NO SUCH RUFF:", style)


def grow_neck(r, A, style, size):
    nl = _S["neckline"]
    if style == "ivy":            # ivy grown round its neck
        stem, leaves, ws, wl = [], None, [], []
        use = [s for s in nl if 0.1 < s[8] < 0.92]
        for i, s in enumerate(use):
            p, n = _on(s, 40 + 95.0 * i, 0.02)
            stem.append(p)
            ws.append(s[6])
            for k in (-1, 1):
                q, nq = _on(s, 40 + 95.0 * i + 38 * k, 0.015)
                lf = g.blade(q, q + (nq * 0.5 + s[1] * 0.5 * k - Z * 0.4).normalized() * 0.2 * size, 0.15 * size, normal=nq, belly=0.4)
                leaves = g.merge(leaves, lf)
                wl.extend([s[6]] * len(lf[0]))
        tube = g.tube(stem, [0.016] * len(stem), n=4)
        _add(r, "ivy_stem", tube, [w for w in ws for _ in range(4)], mat("bark"), smooth=True)
        _add(r, "ivy", leaves, wl, mat("leaf"), smooth=False)
    else:
        log("NO SUCH NECK:", style)


def grow_eyes(r, A, style, size):
    P, S, up, f = _S["P"], _S["HS"], _S["hup"], _S["hf"]
    acc = bool(_S["spec"].get("accent"))
    if style == "third":          # a pale mark like an eye on its brow, that seems to follow you
        c = P(0, 0.2, 0.19)
        _add(r, "third_lid", gl._lens(c, up, f, X, 0.1 * S * size, 0.065 * S * size, 0.016), "Head", _am("pale") if acc else mat("fur_pale"), smooth=True)
        gl._later(r, "pulse", "thirdeye", [(gl._lens(c + up * 0.012, up, f, X, 0.06 * S * size, 0.03 * S * size, 0.014), field("eyes", 3.8))], c, "Head")
    elif style == "lamp":         # eyes that give the lamp back: wide, round, rimmed in brass
        e = A.eye
        geo = None
        for sg in (1, -1):
            c = Vector((sg * e.x, e.y, e.z))
            n = Vector((sg * A.eye_n.x, A.eye_n.y, A.eye_n.z))
            geo = g.merge(geo, _hoop(c - n * 0.01, n, A.eye_r * 1.25, 0.014 * size, n=10, sides=4))
        _add(r, "lamp_rims", geo, "Head", mat("metal_brass"), smooth=True)
    elif style == "old":          # old eyes in a young face: grey about the muzzle
        m = _S["m"]
        _paint(r, "head", lambda c, n: (c - r.bone("Head")).dot(f) > m(0.5) * S, mat("fur_grey"))
    else:
        log("NO SUCH EYES:", style)


def grow_maw(r, A, style, size):
    P, S, SK = _S["P"], _S["HS"], _S["SK"]
    if style in ("open", "fangs"):   # (open: its jaw is its head's own) the points of its teeth
        geo = None
        for sg in (1, -1):
            for i, L in ((7, 0.07), (6, 0.04)) if style == "fangs" else ((7, 0.045),):
                b0 = P(sg * SK[i][3] * 0.8, SK[i][0], SK[i][2] + 0.03)
                geo = g.merge(geo, g.cone(b0, b0 - _S["hup"] * (L * S * (0.7 + 0.5 * size)) + _S["hf"] * 0.01, 0.014 * S, n=4))
        _add(r, "teeth", geo, "Head", mat("fang"), smooth=True)
    else:
        log("NO SUCH MAW:", style)


def grow_mouth(r, A, style, size):
    P, S, yn = _S["P"], _S["HS"], _S["yn"]
    c = P(0, yn - 0.04, -0.1)
    if style == "sack":           # something in its mouth, held very gently
        items = [(g.ico(c + Vector((0, 0, -0.26 * size)), 0.2 * size, sub=2, scale=(1.0, 0.9, 1.2)), mat("paper")),
                 (g.tube([c + Vector((0, 0, -0.07 * size)), c + Vector((0, 0, 0.03))], [0.08 * size, 0.04 * size], n=6), mat("cord")),
                 (_hoop(c + Vector((0, 0, -0.07 * size)), Z, 0.07 * size, 0.02, n=8), _am() if _S["spec"].get("accent") else mat("cape_red"))]
        gl._later(r, "sway", "sack", items, c, "Head", hang=True)
    elif style == "prize":        # something bright that was somebody else's
        items = [(g.ico(c + Vector((0, 0, -0.12 * size)), 0.1 * size, sub=1, scale=(1.1, 0.45, 1.3)), field("prize", 3.0)),
                 (_hoop(c + Vector((0, 0, -0.12 * size)), Y, 0.13 * size, 0.02, n=10), mat("metal_brass"))]
        gl._later(r, "sway", "prize", items, c, "Head", hang=True)
    else:
        log("NO SUCH MOUTH:", style)


def grow_mask(r, A, style, size):
    """A pale mask that is not quite the shape of the face beneath: worn, pushed up, or half."""
    P, S, up, f, SK, m = _S["P"], _S["HS"], _S["hup"], _S["hf"], _S["SK"], _S["m"]
    a0 = 0.3
    if style == "raised":         # pushed up on its head, for now: it looks at the sky
        O, fw, upm = P(0, 0.02, 0.2), (f * 0.5 + up * 0.86).normalized(), (up * 0.5 - f * 0.86).normalized()
    else:
        O, fw, upm = P(0, 0.0, 0.0), f, up

    def Q(x, a, h):
        return O + (X * x + fw * a + upm * h) * (S * (0.9 + 0.1 * size)) if style == "raised" else P(x, a, h)
    half = style == "half"
    # a shell over the brow, the eyes and the muzzle: rows from the brow to the nose
    rows = [(0.1, 0.19, 0.245, 0.02), (0.22, 0.215, 0.25, -0.03), (a0, 0.19, 0.225, -0.07), (m(0.44), 0.135, 0.14, -0.07), (m(0.6), 0.1, 0.095, -0.06), (m(0.78), 0.085, 0.07, -0.05), (m(0.92), 0.06, 0.04, -0.03)]
    cols = ((-1.0, 0.0), (-0.92, 0.55), (-0.6, 0.9), (0.0, 1.0)) if half else ((-1.0, 0.0), (-0.92, 0.55), (-0.6, 0.9), (0.0, 1.0), (0.6, 0.9), (0.92, 0.55), (1.0, 0.0))
    rings = []
    for a, top, w, low in rows:
        face = [Q(cx * w, a, low + (top - low) * ch + 0.035) for cx, ch in cols]
        rings.append(face + [q - upm * 0.02 * S for q in reversed(face)])
    _add(r, "mask", g.loft(rings, caps=True), "Head", mat("mask_pale"), smooth=False)
    slits, marks, ears, cord, sparks = None, None, None, None, None
    for sg in ((-1,) if half else (1, -1)):
        nx = (X * sg * 0.8 + upm * 0.6).normalized()
        e0, e1 = Q(sg * 0.235, a0 - 0.12, 0.13), Q(sg * 0.12, a0 + 0.13, 0.125)
        slits = g.merge(slits, g.blade(e0 + nx * 0.035, e1 + nx * 0.035, 0.12 * S, thick=0.03, normal=nx, belly=0.5))
        sparks = g.merge(sparks, g.ico(e0.lerp(e1, 0.5) + nx * 0.05, 0.028 * S, sub=0))
        marks = g.merge(marks, g.blade(Q(sg * 0.25, a0 - 0.06, 0.03) + nx * 0.035, Q(sg * 0.14, a0 + 0.2, 0.0) + nx * 0.035, 0.09 * S, thick=0.03, normal=nx, belly=0.5))
        marks = g.merge(marks, g.blade(Q(sg * 0.1, m(0.62), 0.11), Q(sg * 0.07, m(0.92), 0.08), 0.06 * S, thick=0.03, normal=upm, belly=0.5))
        marks = g.merge(marks, g.blade(Q(sg * 0.12, 0.22, 0.25), Q(sg * 0.16, 0.04, 0.24), 0.1 * S, thick=0.03, normal=upm, belly=0.5))
        # the mask has ears of its own, a little wrong for the ears beneath
        ears = g.merge(ears, g.blade(Q(sg * 0.14, 0.12, 0.2), Q(sg * 0.24, 0.02, 0.44), 0.16 * S, normal=fw, belly=0.3))
        if style != "raised":     # and a red cord ties it on
            cord = g.merge(cord, g.tube([Q(sg * 0.24, 0.14, 0.02), Q(sg * 0.2, 0.0, 0.03), Q(sg * 0.06, -0.12, 0.06), Q(sg * 0.1, -0.2, -0.06), Q(sg * 0.13, -0.24, -0.22)], [0.016, 0.016, 0.02, 0.016, 0.01], n=4))
    _add(r, "mask_ears", ears, "Head", mat("mask_pale"), smooth=False)
    _add(r, "mask_eyes", slits, "Head", mat("coal"))
    _add(r, "mask_sparks", sparks, "Head", field("eyes", 3.8))
    _add(r, "mask_marks", marks, "Head", _am() if _S["spec"].get("accent") else mat("mask_red"))
    if cord:
        _add(r, "mask_cord", cord, "Head", mat("mask_red"), smooth=True)
    if not half:
        _add(r, "mask_brow", g.blade(Q(0, 0.3, 0.2), Q(0, 0.12, 0.235), 0.07 * S, normal=upm, belly=0.5), "Head", field("brow", 2.8))


def grow_face(r, A, style, size):
    """Seen from the left and from the right it is not the same fox."""
    if style != "two":
        log("NO SUCH FACE:", style)
        return
    other = mat("fur_mask")
    for part in ["body", "head"] + ["leg_fr", "leg_br"] + [n for n, _, _ in _S.get("brushes", [])]:
        mats = r.mesh.data.materials
        dark = [m.name for m in mats].index("fur_dark")
        n0, n1 = _S["parts"][part]
        slot = _slot(r, other)
        for i in range(n0, n1):
            p = r.mesh.data.polygons[i]
            if p.material_index == dark and (r.M @ p.center).x < -0.004:
                p.material_index = slot


def grow_back(r, A, style, size):
    back = [s for s in _S["body"] if s[7] == "back" and 0.02 < s[8] < 0.9]
    if style == "leaves":         # leaves in its coat from the far side of things
        geo, geo2, ws, ws2 = None, None, [], []
        for i, s in enumerate(back):
            deg = 90 + 50 * math.sin(i * 2.3 + 0.5)
            p, n = _on(s, deg, 0.0)
            bl = g.blade(p, p + (n * 0.6 + s[1] * 0.7 + Z * 0.3).normalized() * 0.22 * size, 0.15 * size, normal=n + X * 0.3, belly=0.45)
            if i % 3 == 1:
                geo2, ws2 = g.merge(geo2, bl), ws2 + [s[6]] * len(bl[0])
            else:
                geo, ws = g.merge(geo, bl), ws + [s[6]] * len(bl[0])
        _add(r, "leaves", geo, ws, mat("leaf"))
        _add(r, "leaves_dry", geo2, ws2, mat("leaf_dry"))
    elif style == "feathers":     # there is usually a feather somewhere on it
        for i, (k, deg, L) in enumerate(((1, 70, 0.5), (len(back) // 2, 118, 0.42), (len(back) - 2, 80, 0.46))):
            s = back[k]
            p, n = _on(s, deg, -0.01)
            bl = g.blade(p, p + (n * 0.8 + s[1] * 0.6).normalized() * L * size, 0.13 * size, normal=X, belly=0.5)
            _add(r, "feather_%d" % i, bl, [s[6]] * len(bl[0]), mat("feather_pale"))
    elif style == "stripe":       # a pale stripe down its back, as a digger has
        _paint(r, "body", lambda c, n: n.dot(_station(c)[3]) > 0.84, mat("fur_pale"))
        hb = r.bone("Head")
        _paint(r, "head", lambda c, n: n.dot(_S["hup"]) > 0.6 and abs(c.x) < 0.06 * _S["HS"], mat("fur_pale"))
    else:
        log("NO SUCH BACK:", style)


def grow_feet(r, A, style, size):
    if style == "webbed":         # webbed, and leaving rings
        for tag, L in _S["legs"].items():
            pad = g.ico((L["x"], L["y"] - 0.05, 0.035), 1.0, sub=1, scale=(0.17 * size, 0.23 * size, 0.03))
            _add(r, "web_" + tag, pad, L["bone"], mat("fur_light"), smooth=True)
            c = Vector((L["x"], L["y"] - 0.05, 0.02))
            gl._later(r, "pulse", "ripple", [(_hoop(c, Z, 0.3 * size, 0.012, n=12, sides=3), field("ripple", 1.8))], c, L["bone"], side=tag[1], n=0 if tag[0] == "f" else 1)
    elif style == "snow":         # furred to the pad, and leaving no print
        for tag, L in _S["legs"].items():
            geo = g.ico((L["x"], L["y"] - 0.03, 0.09), 1.0, sub=1, scale=(0.13 * size, 0.19 * size, 0.1))
            for k in range(5):
                a = math.pi * (0.1 + 0.2 * k)
                b0 = Vector((L["x"] + 0.09 * math.cos(a), L["y"] - 0.03 - 0.12 * math.sin(a), 0.1))
                geo = g.merge(geo, g.blade(b0, b0 + Vector((0.09 * math.cos(a), -0.1 * math.sin(a), -0.09)), 0.09, normal=Z, belly=0.4))
            _add(r, "snowpaw_" + tag, geo, L["bone"], mat("fur_pale"), smooth=True)
            _paint(r, "leg_" + tag, lambda c, n, L=L: c.z < L["zsock"], mat("fur_pale"))
    else:
        log("NO SUCH FEET:", style)


def grow_claws(r, A, style, size):
    """Broad earth-stained forepaws, for going in after what is hidden."""
    for tag in ("fl", "fr"):
        L = _S["legs"][tag]
        _add(r, "digpaw_" + tag, g.ico((L["x"], L["y"] - 0.05, 0.08), 1.0, sub=1, scale=(0.14 * size, 0.19 * size, 0.085)), L["bone"], mat("earth"), smooth=True)
        cl = None
        for dx in (-0.09, -0.03, 0.03, 0.09):
            b0 = Vector((L["x"] + dx, L["y"] - 0.17, 0.08))
            cl = g.merge(cl, g.cone(b0, b0 + Vector((dx * 0.25, -0.2 * size, -0.07)), 0.03, n=5))
        _add(r, "digclaws_" + tag, cl, L["bone"], mat("claw"))
        _paint(r, "leg_" + tag, lambda c, n, L=L: c.z < L["zsock"] * 0.8, mat("earth"))
    _add(r, "dirty_nose", g.ico(A.nose + Vector((0, 0.0, 0.0)), 0.05 * _S["HS"], sub=1), "Head", mat("earth"), smooth=True)


def grow_fins(r, A, style, size):
    """A finned brush and a fin down its back, like something that crosses water for a living."""
    acc = bool(_S["spec"].get("accent"))
    for name, stations, near in _S.get("brushes", []):
        for sgn in (1, -1):
            geo, ws = None, []
            for i, s in enumerate(stations):
                p, d, u, v, rad, w, t = s
                if not 0.3 < t < 0.97 or i % 2:
                    continue
                b0 = p + v * (sgn * rad * 0.7)
                bl = g.blade(b0, b0 + v * (sgn * (0.3 - 0.1 * t) * size) + d * 0.2, 0.3, normal=u, belly=0.4)
                geo, ws = g.merge(geo, bl), ws + [w] * len(bl[0])
            _add(r, "%s_fin_%d" % (name, sgn), geo, ws, _am("light") if acc and sgn > 0 else mat("fin"), smooth=False)
    geo, ws = None, []
    for i, s in enumerate([s for s in _S["body"] if s[7] == "back" and 0.08 < s[8] < 0.8]):
        p, n = _on(s, 90, -0.02)
        bl = g.blade(p, p + (n * 0.8 + s[1] * 0.6).normalized() * (0.16 + 0.12 * math.sin(s[8] * math.pi)) * size, 0.26, normal=X, belly=0.35)
        geo, ws = g.merge(geo, bl), ws + [s[6]] * len(bl[0])
    _add(r, "backfin", geo, ws, mat("fin"), smooth=False)


def grow_carry(r, A, style, size):
    W, ysh, yhip = _S["W"], _S["ysh"], _S["yhip"]
    if style == "panniers":       # what the line dropped, in two bags
        y = ysh + 0.55
        top, wide = _back(y)
        gl._cape(r, A, "pannier_strap", y - 0.08, y + 0.08, 0.36, mat("leather"), steps=2, hem=0.0, flare=0.02)
        for sg in (1, -1):
            c = Vector((sg * (wide + 0.1), y, top - 0.42))
            _add(r, "pannier_%d" % sg, g.ico(c, 1.0, sub=1, scale=(0.14 * size, 0.25 * size, 0.22 * size)), "Torso2", mat("leather"), smooth=True)
            _add(r, "pannier_flap_%d" % sg, g.box(c + Vector((sg * 0.08, 0, 0.11)), (0.13 * size, 0.42 * size, 0.17 * size), rot=(0, sg * 0.5, 0)), "Torso2", mat("leather_dark"))
            _add(r, "pannier_pin_%d" % sg, g.ico(c + Vector((sg * 0.15, 0, 0.03)), 0.04, sub=0), "Torso2", mat("metal_brass"))
    elif style == "pole":         # a ferryman's pole, and its lamp
        a = Vector((0.16, ysh - 0.8, W + 0.12))
        b = Vector((-0.2, yhip + 1.1, W + 0.6))
        _add(r, "pole", g.tube([a, b], [0.04, 0.035], n=6), "Torso3", mat("wood"))
        for k, t in enumerate((0.36, 0.6)):
            c = a.lerp(b, t)
            _add(r, "pole_lash_%d" % k, _hoop(c, b - a, 0.055, 0.018, n=8), "Torso3", mat("cord"))
        gl._later(r, "sway", "polelamp", gl._lantern(b + Vector((0, 0.02, -0.1)), 0.18 * size, "lamp", 3.4), b, "Torso3", hang=True)
    elif style == "cape":         # a short cape, as a storyteller wears
        gl._cape(r, A, "cape", ysh - 0.2, ysh + 0.75, 0.42 * size, _am("deep") if _S["spec"].get("accent") else mat("cape_red"), hem=0.03)
        _add(r, "cape_clasp", g.ico(Vector((0, A.chest_y - 0.02, _S["B"] + 0.5)), 0.06, sub=1, scale=(1, 0.5, 1)), "Torso3", mat("metal_brass"))
    else:
        gl.grow_carry(r, A, style, size)


OWN = (("marks", grow_marks), ("tail", grow_tail), ("tip", grow_tip), ("maw", grow_maw), ("eyes", grow_eyes), ("mask", grow_mask), ("face", grow_face),
       ("ruff", grow_ruff), ("neck", grow_neck), ("mouth", grow_mouth), ("back", grow_back), ("feet", grow_feet), ("claws", grow_claws), ("fins", grow_fins),
       ("carry", grow_carry))


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
    """The fox itself, laid on the frame in the wolf's place; and what the wolf's own styles
    read of a body, read of this one."""
    sp = _S["spec"]
    _strip(r)
    _reread(r, A)
    _body(r, A)
    A.withers, A.belly = _S["W"], _S["B"]
    A._ys = [_S["ysh"] - 0.7 + 0.1 * i for i in range(int((_S["yhip"] - _S["ysh"] + 1.4) / 0.1) + 2)]
    A._tops = [_back(y)[0] for y in A._ys]
    A._sides = [_flank(y, _back(y)[0] - 0.3) for y in A._ys]
    A.chest_y = _S["ysh"] - 0.36
    for name in ("Neck3", "Neck2", "Neck1", "Torso3"):
        s = _station(r.bone(name))
        A.neck[name] = (s[0].y, s[0].z, s[4], s[5])
    _legs(r, A)
    _head(r, A)
    _tail(r, A)
    _reread(r, A)
    A.skull = _S["skull"].z
    for slot, fn in OWN:
        for style, size in gl.each(sp.get(slot)):
            fn(r, A, style, size)
    # it is stood by the height a plain fox of its legs carries its head at, however it
    # carries its own, and whatever it has grown: a lowered head does not make a larger fox
    _S["true_skull"] = A.skull
    A.skull = _S["W"] * 1.3


# the slots the wolf's own builder is not to see (they are this file's, or mean another thing here)
MINE = ("fox", "stance", "tails", "tip", "marks", "ears", "eyes", "tail", "neck", "maw", "mouth", "mask", "face", "ruff", "back", "feet", "claws", "fins",
        "carry", "whiskers", "pose", "rest", "fur", "flags", "armor")


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
                r.rotate(neck[i:] + head, r.bone(b), Z, -0.4 * size)
            r.rotate(head, r.bone("Head"), Z, -0.34 * size)
        elif style == "aside":
            r.rotate(neck[1:] + head, r.bone("Neck2"), Z, -0.3 * size)
            r.rotate(head, r.bone("Head"), Z, -0.3 * size)
        elif style == "tilt":         # its head on one side: listening
            r.rotate(head, r.bone("Head"), Y, -0.45 * size)


def build(form_id, level, spec, base):
    _S.clear()
    _S["level"], _S["spec"] = level, spec
    _S["K"] = KINDS[spec.get("fox", "red")]
    _S["age"] = AGES[level]
    wspec = {k: v for k, v in spec.items() if k not in MINE}
    wspec["build"] = {}
    r, sockets = gl.wolf_form(form_id, level, wspec, species=frame, coat=("fur_dark", "fur_light"), marks=(), ages=ages, measure=measure)
    k = STAND / (_S["W"] * 1.3)
    # the sockets on its head stand where its head is, not where a plain fox's would be
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
    builders["fox"] = build
