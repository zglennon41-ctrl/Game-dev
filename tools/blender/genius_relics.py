"""WILDLINE genius kit, the relics: worn equipment that is alive. A belt whose buckle is an
eye, a knife that watches from its pommel, a glove with a pulse at the wrist, and the Second
Forms they grow into (the living blade, the talon gauntlet, the tower-shield hound, the coat
that listens). Also here: the parts added with them (the Seed-marks that had no art: a grip,
a ledger, a guard; a watching eye and a shell as heritage), the keepsakes a partner gives, and
the sheet that shows one form in a spread of its looks (data/genius-looks.json).
genius_kit.py loads this file (register()); docs/genius-forms.md has the conventions.
"""
import json
import math
import os

import bpy
from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z

gk = None


def register(kit):
    global gk
    gk = kit
    kit.BODIES.update({
        "relic-buckle": buckle_body,
        "relic-knife": knife_body,
        "relic-blade": lambda: knife_body(long=True),
        "relic-glove": glove_body,
        "relic-gauntlet": lambda: glove_body(gauntlet=True),
        "relic-shield": shield_body,
        "relic-coat": coat_body,
    })
    kit.PARTS.update({"grip": grip_part, "ledger": ledger_part, "broad-guard": broad_guard_part, "watching-eye": watching_eye_part, "shell": shell_part})
    kit.KEEPSAKES.update({"collar": collar_keepsake, "ribbon": ribbon_keepsake, "charm": charm_keepsake, "bell": bell_keepsake})


def strap(points, width, thick, up=Z, closed=False):
    """A flat strap through points: `width` across (along `up`), `thick` through. Leather."""
    pts = [Vector(p) for p in points]
    m = len(pts)
    verts, faces = [], []
    for i, p in enumerate(pts):
        a = pts[(i - 1) % m] if (closed or i > 0) else pts[i]
        b = pts[(i + 1) % m] if (closed or i < m - 1) else pts[i]
        d = (b - a).normalized()
        side = Vector(up).cross(d).normalized()
        u2 = d.cross(side).normalized()
        w = width[i] if isinstance(width, (list, tuple)) else width
        verts += [p + u2 * (w / 2) + side * (thick / 2), p + u2 * (w / 2) - side * (thick / 2), p - u2 * (w / 2) - side * (thick / 2), p - u2 * (w / 2) + side * (thick / 2)]
    for i in range(m if closed else m - 1):
        j = (i + 1) % m
        for k in range(4):
            faces.append((i * 4 + k, i * 4 + (k + 1) % 4, j * 4 + (k + 1) % 4, j * 4 + k))
    if not closed:
        faces.append((3, 2, 1, 0))
        faces.append(((m - 1) * 4, (m - 1) * 4 + 1, (m - 1) * 4 + 2, (m - 1) * 4 + 3))
    return verts, faces


def loop(centre, rx, ry, n=16, u=X, v=Y):
    c = Vector(centre)
    return [c + Vector(u) * (math.cos(2 * math.pi * i / n) * rx) + Vector(v) * (math.sin(2 * math.pi * i / n) * ry) for i in range(n)]


def ringtube(centre, rx, ry, r, n=16, u=X, v=Y, sides=3):
    pts = loop(centre, rx, ry, n, u, v)
    pts.append(pts[0])
    return g.tube(pts, [r] * len(pts), n=sides, caps=False)


def _eye(c, r, facing=(0, -1, 0), lids=None, slit=True):
    """A living eye set in a thing: an iris of the field, a slit of dark, lids of the thing's
    own stuff above and below. Returns [(geo, material)...]."""
    c, f = Vector(c), Vector(facing).normalized()
    side = f.cross(Z).normalized() if abs(f.dot(Z)) < 0.9 else X
    up = side.cross(f).normalized()
    R = Matrix((side, f, up)).transposed()
    out = [(g.moved(g.ico((0, 0, 0), r, sub=1, scale=(1.0, 0.45, 1.0)), Matrix.Translation(c) @ R.to_4x4()), gk.field("eyes", 3.5))]
    if slit:
        out.append((g.moved(g.ico((0, 0, 0), r * 0.42, sub=0, scale=(0.5, 0.5, 1.7)), Matrix.Translation(c + f * (r * 0.36)) @ R.to_4x4()), gk.mat("eye_dark")))
    if lids is not None:
        for sgn in (1, -1):
            a, b = c - side * (r * 1.25) + f * (r * 0.1), c + side * (r * 1.25) + f * (r * 0.1)
            mid = c + up * (sgn * r * 0.95) + f * (r * 0.5)
            out.append((g.tongue([a, mid, b], [r * 0.16, r * 0.62, r * 0.16], thick=0.5, normal=f + up * (sgn * 0.6)), lids))
    return out


# ======================================================================================
# The relics
# ======================================================================================

def buckle_body():
    """The watch-buckle: a broad belt buckled round a waist that is not there. The buckle's
    plate is an eye that opens; a line of the field beats along the leather; the free end
    hangs past the keeper, tipped in brass."""
    lea, dark, brass = gk.mat("leather"), gk.mat("leather_dark"), gk.mat("metal_brass")
    zc, rx, ry = 0.44, 0.2, 0.15
    items = []
    items.append((strap(loop((0, 0, zc), rx, ry, n=20), 0.09, 0.016, closed=True), lea))
    for dz in (0.034, -0.034):
        items.append((ringtube((0, 0, zc + dz), rx + 0.009, ry + 0.009, 0.0035, n=20), gk.mark("stitch", lea)))
    items.append((ringtube((0, 0, zc), rx + 0.0095, ry + 0.0095, 0.005, n=20), gk.field("pulse", 1.8)))
    studs = None
    for i in range(9):
        a = math.radians(20 + 17.5 * i)
        for dz in (0.018, -0.018):
            studs = g.merge(studs, g.ico(((rx + 0.01) * math.cos(a), (ry + 0.01) * math.sin(a), zc + dz), 0.009, sub=0))
    items.append((studs, gk.mark("studs", lea)))
    # the buckle: a brass frame standing proud of the belt, the eye in it, the prong across
    by = -ry - 0.02
    frame = loop((0, by, zc), 0.098, 0.074, n=12, u=X, v=Z)
    frame.append(frame[0])
    items.append((g.tube(frame, [0.015] * len(frame), n=5, caps=False), brass))
    items.append((g.ico((0, by + 0.012, zc), 0.07, sub=1, scale=(1.25, 0.2, 0.95)), dark))
    items += _eye((0, by - 0.004, zc), 0.046, lids=lea)
    items.append((g.tube([(-0.098, by - 0.014, zc - 0.058), (0.0, by - 0.02, zc - 0.066), (0.098, by - 0.014, zc - 0.058)], [0.006, 0.006, 0.004], n=4), brass))
    # the keeper and the free end
    items.append((strap([(0.118, by + 0.02, zc + 0.052), (0.126, by - 0.006, zc + 0.052), (0.126, by - 0.006, zc - 0.052), (0.118, by + 0.02, zc - 0.052)], 0.03, 0.012, up=X), dark))
    tail = [(0.1, by + 0.004, zc), (0.165, by - 0.012, zc - 0.012), (0.2, by - 0.004, zc - 0.11), (0.192, by + 0.004, zc - 0.22), (0.186, by + 0.006, zc - 0.27)]
    items.append((strap(tail, [0.08, 0.08, 0.078, 0.07, 0.03], 0.014, up=(0.3, -1, 0)), lea))
    items.append((g.ico((0.186, by + 0.004, zc - 0.268), 0.022, sub=0, scale=(1.0, 0.5, 1.2)), brass))
    holes = None
    for k in range(3):
        holes = g.merge(holes, g.ico((0.198 - 0.004 * k, by - 0.012, zc - 0.1 - 0.045 * k), 0.008, sub=0, scale=(1, 0.5, 1)))
    items.append((holes, dark))
    # a ring on its hip with nothing hung from it yet
    items.append((ringtube((-rx - 0.012, 0.02, zc - 0.062), 0.006, 0.024, 0.005, n=10, u=X, v=Z), brass))
    ob = g.pieces("buckle_body", items)
    socks = gk._sockets({
        "socket_head": [(0, 0, zc + 0.06)], "socket_eyes": [(0, by - 0.03, zc)], "socket_mouth": [(0, by - 0.02, zc - 0.07)], "socket_grip": [(0.19, by, zc - 0.28)],
        "socket_throat": [(0, by, zc - 0.09)], "socket_light": [(0, 0, zc)], "socket_back": [(0, ry + 0.02, zc)], "socket_body": [(0, by - 0.01, zc - 0.11)],
        "socket_tail": [(0, ry + 0.02, zc - 0.03)], "socket_arm_l": [(rx + 0.02, 0, zc)], "socket_arm_r": [(-rx - 0.02, 0, zc)],
        "socket_limb_fl": [(0.1, -0.05, zc - 0.06)], "socket_limb_fr": [(-0.1, -0.05, zc - 0.06)], "socket_keepsake": [(-rx - 0.014, 0.02, zc - 0.088)],
    })
    return gk.Built([ob], socks)


def knife_body(long=False):
    """The kept knife: a short knife riding point-down in its sheath, a hand's breadth drawn,
    an eye in its pommel that is always open. Long, it is the living blade: a sword in a
    brass-shod scabbard, half out, its edge a line of the field."""
    lea, dark, brass, steel = gk.mat("leather"), gk.mat("leather_dark"), gk.mat("metal_brass"), gk.mat("metal_iron_light")
    Ls = 0.36 if not long else 0.52             # the sheath's length
    z0 = 0.1
    zt = z0 + Ls                                # the sheath's mouth
    draw = 0.1 if not long else 0.2
    w = 0.044 if not long else 0.04
    items = []
    sheath = g.loft([g.ring((0, 0, z), rx, ryy, n=6, u=X, v=Y) for z, rx, ryy in ((z0, 0.01, 0.007), (z0 + 0.07, w * 0.72, 0.012), (zt - 0.04, w, 0.015), (zt, w + 0.004, 0.017))])
    items.append((sheath, lea))
    items.append((g.loft([g.ring((0, 0, z), rx, ryy, n=6, u=X, v=Y) for z, rx, ryy in ((z0 - 0.012, 0.004, 0.004), (z0 + 0.012, 0.017, 0.011), (z0 + 0.06, w * 0.7, 0.0135))]), brass))
    items.append((g.loft([g.ring((0, 0, z), rx, ryy, n=6, u=X, v=Y) for z, rx, ryy in ((zt - 0.03, w + 0.004, 0.0175), (zt + 0.004, w + 0.008, 0.02))], caps=False), brass))
    # stitching up one edge, a line of the field up the face
    items.append((g.tube([(w * 0.74, -0.012, z0 + 0.08), (w + 0.002, -0.015, zt - 0.045)], [0.0035, 0.0035], n=3), gk.mark("stitch", lea)))
    items.append((g.tube([(0, -0.014, z0 + 0.09), (0.004, -0.017, (z0 + zt) / 2), (0, -0.018, zt - 0.05)], [0.003, 0.005, 0.003], n=3), gk.field("pulse", 1.8)))
    # the frog: a loop of strap to hang it by
    items.append((strap([(0, 0.016, zt - 0.05), (0, 0.05, zt - 0.03), (0, 0.055, zt + 0.03), (0, 0.02, zt + 0.0)], 0.036, 0.008, up=X), dark))
    # the blade showing above the mouth, its edge alight
    items.append((g.box((0, 0, zt + draw / 2), (w * 1.5, 0.007, draw)), steel))
    items.append((g.box((-w * 0.76, 0, zt + draw / 2), (0.006, 0.01, draw)), gk.field("edge", 2.5)))
    if long:
        items.append((g.box((0, 0, zt + draw / 2), (0.01, 0.011, draw)), gk.mat("metal_iron")))
    zg = zt + draw
    # guard, grip, pommel
    gw = 0.14 if not long else 0.24
    items.append((g.box((0, 0, zg + 0.008), (gw, 0.026, 0.02)), brass))
    if long:
        for s in (1, -1):
            items.append((g.tube([(s * gw / 2, 0, zg + 0.008), (s * (gw / 2 + 0.03), 0, zg - 0.012)], [0.012, 0.007], n=5), brass))
    Lg = 0.1 if not long else 0.15
    items.append((g.tube([(0, 0, zg + 0.018), (0, 0, zg + 0.018 + Lg * 0.5), (0, 0, zg + 0.018 + Lg)], [0.018, 0.02, 0.016], n=6, flat=0.8), dark))
    wraps = None
    for k in range(4 if not long else 6):
        zz = zg + 0.03 + (Lg - 0.024) * k / (3 if not long else 5)
        wraps = g.merge(wraps, ringtube((0, 0, zz), 0.021, 0.018, 0.004, n=8))
    items.append((wraps, gk.mark("wrap", dark)))
    zp = zg + 0.018 + Lg + 0.02
    items.append((g.ico((0, 0, zp), 0.031, sub=1, scale=(1.0, 0.8, 0.95)), brass))
    items += _eye((0, -0.02, zp), 0.02, lids=brass)
    ob = g.pieces("knife_body", items)
    socks = gk._sockets({
        "socket_head": [(0, 0, zp + 0.035)], "socket_eyes": [(0, -0.04, zp)], "socket_mouth": [(0, -0.02, zg)], "socket_grip": [(0, 0, zg + 0.07)],
        "socket_throat": [(0, -0.022, zt - 0.02)], "socket_light": [(0, -0.03, (z0 + zt) / 2)], "socket_back": [(0, 0.06, zt)], "socket_body": [(0, -0.022, zt - 0.1)],
        "socket_tail": [(0, 0, z0)], "socket_arm_l": [(gw / 2 + 0.01, 0, zg + 0.008)], "socket_arm_r": [(-gw / 2 - 0.01, 0, zg + 0.008)],
        "socket_limb_fl": [(0.02, -0.01, z0 + 0.03)], "socket_limb_fr": [(-0.02, -0.01, z0 + 0.03)], "socket_keepsake": [(0, 0.056, zt - 0.03)],
    })
    return gk.Built([ob], socks)


def glove_body(gauntlet=False):
    """The worn glove: a left-hand glove standing on its cuff, the fingers a little curled as
    if a hand had just left it, a line of the field beating round the wrist. Grown, it is the
    talon relic: lames of brass down the back of the hand, a hawk's talon on every finger."""
    lea, dark, brass = gk.mat("leather"), gk.mat("leather_dark"), gk.mat("metal_brass")
    items = []
    rings = [(0.12, 0.1, 0.074), (0.17, 0.092, 0.066), (0.24, 0.074, 0.052), (0.3, 0.066, 0.045), (0.4, 0.086, 0.04), (0.47, 0.084, 0.034)]
    hand = g.loft([g.ring((0, 0, z), rx, ryy, n=10, u=X, v=Y, phase=math.pi / 10) for z, rx, ryy in rings])
    items.append((hand, lea))
    items.append((g.loft([g.ring((0, 0, z), rx, ryy, n=10, u=X, v=Y, phase=math.pi / 10) for z, rx, ryy in ((0.112, 0.106, 0.08), (0.14, 0.104, 0.078), (0.172, 0.096, 0.07))], caps=False), gk.mark("cuff", dark)))
    items.append((g.ico((0, 0, 0.122), 0.09, sub=1, scale=(1.0, 0.72, 0.12)), gk.mat("void")))
    # the wrist: a strap and its buckle, and the pulse
    items.append((strap(loop((0, 0, 0.275), 0.074, 0.052, n=14), 0.026, 0.008, closed=True), dark))
    items.append((g.box((0.02, -0.056, 0.275), (0.034, 0.012, 0.034)), brass))
    items.append((ringtube((0, 0, 0.305), 0.069, 0.048, 0.005, n=14), gk.field("pulse", 1.8)))
    # the fingers, each of three joints, curling forward; the thumb standing off
    tips = []
    for i, (x, L) in enumerate(((-0.062, 0.13), (-0.021, 0.165), (0.021, 0.155), (0.062, 0.115))):
        base = Vector((x, 0.0, 0.465))
        pts = [base, base + Vector((0, -0.004, L * 0.42)), base + Vector((0, -0.022, L * 0.76)), base + Vector((0, -0.05, L))]
        items.append((g.tube(pts, [0.021, 0.019, 0.017, 0.012], n=6), lea))
        tips.append(pts)
    th = [Vector((0.082, 0.0, 0.36)), Vector((0.128, -0.014, 0.41)), Vector((0.148, -0.036, 0.468)), Vector((0.146, -0.058, 0.512))]
    items.append((g.tube(th, [0.026, 0.023, 0.019, 0.013], n=6), lea))
    # stitching: three lines down the back of the hand (it shows us its back)
    st = None
    for x in (-0.042, 0.0, 0.042):
        st = g.merge(st, g.tube([(x, -0.036, 0.46), (x * 0.82, -0.044, 0.39), (x * 0.6, -0.047, 0.32)], [0.0035] * 3, n=3))
    items.append((st, gk.mark("stitch", lea)))
    if gauntlet:
        # lames of brass over the back of the hand and the cuff; a stone of the field; talons
        for k, (z, wd) in enumerate(((0.44, 0.15), (0.4, 0.16), (0.36, 0.15), (0.32, 0.13))):
            items.append((g.box((0, -0.046 - 0.004 * (k % 2), z), (wd, 0.012, 0.05), rot=(math.radians(8), 0, 0)), brass))
        items.append((g.box((0, -0.066, 0.2), (0.15, 0.014, 0.1), rot=(math.radians(-8), 0, 0)), brass))
        items.append((g.ico((0, -0.058, 0.39), 0.02, sub=1, scale=(1, 0.5, 1.2)), gk.field("core", 4.0)))
        for pts in tips + [th]:
            a, b = pts[-2], pts[-1]
            d = (b - a).normalized()
            items.append((g.tube([a + d * 0.005, b + d * 0.01, b + d * 0.05 + Vector((0, -0.03, -0.006))], [0.02, 0.014, 0.002], n=5), gk.mat("talon")))
            items.append((ringtube((a + b) / 2, 0.021, 0.021, 0.005, n=8), brass))
    ob = g.pieces("glove_body", items)
    socks = gk._sockets({
        "socket_head": [(0, -0.02, 0.64)], "socket_eyes": [(0, -0.055, 0.41)], "socket_mouth": [(0, -0.05, 0.34)], "socket_grip": [(0, 0.045, 0.4)],
        "socket_throat": [(0, -0.056, 0.27)], "socket_light": [(0, 0.05, 0.42)], "socket_back": [(0, 0.05, 0.36)], "socket_body": [(0, -0.07, 0.2)],
        "socket_tail": [(0, 0.075, 0.14)], "socket_arm_l": [(0.1, 0, 0.3)], "socket_arm_r": [(-0.1, 0, 0.3)],
        "socket_limb_fl": [(0.05, -0.03, 0.13)], "socket_limb_fr": [(-0.05, -0.03, 0.13)], "socket_keepsake": [(-0.03, -0.058, 0.262)],
        "socket_collar": [(0, 0, 0.255), Matrix.Rotation(math.pi / 2, 3, "X") @ Matrix.Diagonal((0.82, 1.0, 0.6))],
    })
    return gk.Built([ob], socks)


def shield_body():
    """The tower-shield hound: a tall curved shield faced in leather, and where its boss
    should be, a hound's muzzle of brass with the teeth showing; two eyes over it, two corners
    pricked like ears. It stands between."""
    lea, wood, brass, dark = gk.mat("leather"), gk.mat("wood"), gk.mat("metal_brass"), gk.mat("metal_dark")
    zc, H, hw = 0.42, 0.62, 0.2

    def face(x):
        return -0.02 + 0.6 * x * x          # the face bows toward the front in the middle
    arc = [(x, face(x), zc) for x in [hw * (i / 4.0 - 1.0) for i in range(9)]]
    items = []
    items.append((strap(arc, H, 0.022, up=Z), lea))
    items.append((strap([(x, y + 0.018, z) for x, y, z in arc], H - 0.02, 0.016, up=Z), wood))
    # the rim: brass round the edge; the ears: the top corners drawn up to points
    edge = [(x, face(x) - 0.004, zc + H / 2) for x, _, _ in arc] + [(x, face(x) - 0.004, zc - H / 2) for x, _, _ in reversed(arc)]
    edge.append(edge[0])
    items.append((g.tube(edge, [0.012] * len(edge), n=4, caps=False), brass))
    for s in (1, -1):
        items.append((g.blade((s * (hw - 0.07), face(hw - 0.07) - 0.002, zc + H / 2 - 0.01), (s * (hw - 0.01), face(hw) + 0.02, zc + H / 2 + 0.12), 0.11, normal=(0, -1, 0.2), belly=0.3), lea))
    # the blazon: a chevron across the lower half; studs down each side
    ch = None
    for s in (1, -1):
        pts = [(0.0, face(0.0) - 0.014, zc - 0.07), (s * 0.085, face(0.085) - 0.014, zc - 0.16), (s * 0.17, face(0.17) - 0.014, zc - 0.25)]
        ch = g.merge(ch, strap(pts, 0.07, 0.008, up=(0, -1, 0)))
    items.append((ch, gk.mark("blazon", lea)))
    studs = None
    for s in (1, -1):
        for k in range(6):
            studs = g.merge(studs, g.ico((s * (hw - 0.035), face(hw - 0.035) - 0.012, zc - 0.25 + 0.1 * k), 0.012, sub=0))
    items.append((studs, gk.mark("studs", wood)))
    # the hound: brow, eyes, the muzzle standing out of the shield, the jaw a little dropped
    zm = zc + 0.08
    muzzle = g.loft([g.ring((0, y, z), rx, rz, n=6, u=X, v=Z, phase=math.pi / 6) for y, z, rx, rz in ((-0.03, zm, 0.085, 0.07), (-0.11, zm - 0.01, 0.06, 0.05), (-0.19, zm - 0.02, 0.044, 0.036), (-0.21, zm - 0.022, 0.03, 0.026))])
    items.append((muzzle, brass))
    items.append((g.ico((0, -0.214, zm - 0.008), 0.02, sub=1, scale=(1.2, 0.8, 0.8)), dark))
    jaw = g.loft([g.ring((0, y, z), rx, rz, n=6, u=X, v=Z, phase=math.pi / 6) for y, z, rx, rz in ((-0.03, zm - 0.085, 0.07, 0.022), (-0.11, zm - 0.085, 0.05, 0.018), (-0.18, zm - 0.078, 0.032, 0.012))])
    items.append((jaw, brass))
    fangs = None
    for s in (1, -1):
        fangs = g.merge(fangs, g.cone((s * 0.03, -0.175, zm - 0.048), (s * 0.03, -0.18, zm - 0.1), 0.012, n=4), g.cone((s * 0.022, -0.15, zm - 0.07), (s * 0.022, -0.152, zm - 0.036), 0.009, n=4),
                        g.cone((s * 0.05, -0.12, zm - 0.052), (s * 0.05, -0.122, zm - 0.082), 0.008, n=4))
    items.append((fangs, gk.mat("bone")))
    items.append((g.box((0, -0.1, zm - 0.062), (0.07, 0.14, 0.012)), gk.field("mouth", 2.5)))
    for s in (1, -1):
        items += _eye((s * 0.085, face(0.085) - 0.016, zm + 0.115), 0.028, slit=True)
        items.append((g.blade((s * 0.03, face(0.03) - 0.02, zm + 0.135), (s * 0.15, face(0.15) - 0.016, zm + 0.18), 0.05, normal=(0, -1, 0.5), belly=0.45), brass))
    # the grip at its back: you can hold it
    items.append((strap([(0, 0.045, zc + 0.1), (0, 0.095, zc + 0.05), (0, 0.095, zc - 0.05), (0, 0.045, zc - 0.1)], 0.04, 0.012, up=X), gk.mat("leather_dark")))
    ob = g.pieces("shield_body", items)
    socks = gk._sockets({
        "socket_head": [(0, -0.02, zc + H / 2 + 0.02)], "socket_eyes": [(0, -0.05, zm + 0.12)], "socket_mouth": [(0, -0.2, zm - 0.06)], "socket_grip": [(0, 0.1, zc)],
        "socket_throat": [(0, -0.05, zm - 0.12)], "socket_light": [(0, -0.05, zc - 0.2)], "socket_back": [(0, 0.06, zc + 0.2)], "socket_body": [(0, -0.04, zc - 0.16)],
        "socket_tail": [(0, 0.03, zc - H / 2)], "socket_arm_l": [(hw + 0.01, face(hw), zc + 0.1)], "socket_arm_r": [(-hw - 0.01, face(hw), zc + 0.1)],
        "socket_limb_fl": [(0.12, face(0.12), zc - H / 2)], "socket_limb_fr": [(-0.12, face(0.12), zc - H / 2)], "socket_keepsake": [(0, -0.12, zm - 0.1)],
    })
    return gk.Built([ob], socks)


def coat_body():
    """The coat that listens: a long coat standing as if someone wore it, and no one does.
    The collar is turned up high round nothing; the sleeves hang, the cuffs are empty; a
    thread of the field runs in the weave at the hem and round the collar's edge."""
    lea, dark, brass = gk.mat("leather"), gk.mat("leather_dark"), gk.mat("metal_brass")
    lining = gk.mark("lining", dark)
    prof = [(0.1, 0.2, 0.15, 0.015), (0.2, 0.175, 0.13, 0.012), (0.34, 0.135, 0.1, 0.005), (0.46, 0.118, 0.09, 0.0), (0.55, 0.15, 0.09, 0.0), (0.6, 0.1, 0.075, 0.0), (0.615, 0.07, 0.06, 0.0)]
    rings = [g.ring((0, yo, z), rx, ryy, n=12, u=X, v=Y, phase=math.pi / 12) for z, rx, ryy, yo in prof]
    coat = g.to_object("coat_shell", g.loft(rings), lea)
    gk.paint(coat, lambda c, n, i: n.z < -0.9, gk.mat("void"))
    gk.paint(coat, lambda c, n, i: abs(c.x) < 0.03 and c.y < 0 and abs(n.z) < 0.6 and c.z < 0.56, dark)
    items = []
    # the collar: a high ring, flared, its inside lined, nothing in it but a dark and a light
    items.append((g.loft([g.ring((0, 0.004, z), rx, ryy, n=12, u=X, v=Y, phase=math.pi / 12) for z, rx, ryy in ((0.6, 0.088, 0.07), (0.69, 0.118, 0.098), (0.735, 0.128, 0.108))], caps=False), lea))
    items.append((g.loft([g.ring((0, 0.004, z), rx, ryy, n=12, u=X, v=Y, phase=math.pi / 12) for z, rx, ryy in ((0.735, 0.124, 0.104), (0.69, 0.108, 0.088), (0.615, 0.07, 0.058))], caps=False), lining))
    items.append((g.ico((0, 0.004, 0.622), 0.07, sub=1, scale=(1.0, 0.85, 0.25)), gk.mat("void")))
    items.append((ringtube((0, 0.004, 0.737), 0.127, 0.107, 0.004, n=16), gk.field("weave", 1.8)))
    items.append((g.ico((0, -0.01, 0.66), 0.022, sub=1, scale=(1.6, 0.7, 0.55)), gk.field("eyes", 2.5)))
    # sleeves: hanging, a little bent, the cuffs turned back to show the lining
    for s in (1, -1):
        sh, el, cu = Vector((s * 0.15, 0.0, 0.55)), Vector((s * 0.215, -0.02, 0.41)), Vector((s * 0.205, -0.065, 0.275))
        items.append((g.tube([sh, el, cu], [0.058, 0.05, 0.052], n=7), lea))
        items.append((g.tube([cu + Vector((0, 0.006, 0.03)), cu + Vector((0, -0.004, -0.012))], [0.058, 0.06], n=7, caps=False), lining))
        items.append((g.ico(cu + Vector((0, -0.004, -0.012)), 0.05, sub=1, scale=(1, 1, 0.2)), gk.mat("void")))
    # lapels, buttons, a belt
    for s in (1, -1):
        items.append((g.blade((s * 0.02, -0.078, 0.6), (s * 0.085, -0.094, 0.47), 0.085, normal=(s * 0.3, -1, 0.1), belly=0.35), lining))
    btn = None
    for k in range(4):
        z = 0.44 - 0.085 * k
        btn = g.merge(btn, g.ico((0.045, -0.1 - 0.012 * k - 0.002 * k * k, z), 0.012, sub=0, scale=(1, 0.5, 1)))
    items.append((btn, brass))
    items.append((strap(loop((0, 0.002, 0.42), 0.128, 0.098, n=14), 0.034, 0.01, closed=True), dark))
    items.append((g.box((-0.02, -0.1, 0.42), (0.05, 0.014, 0.046)), brass))
    # stitching: the shoulder seams and down the back; the weave alight at the hem
    st = None
    for s in (1, -1):
        st = g.merge(st, g.tube([(s * 0.1, 0.0, 0.606), (s * 0.152, 0.0, 0.556)], [0.004, 0.004], n=3), g.tube([(s * 0.07, -0.128, 0.2), (s * 0.085, -0.142, 0.11)], [0.004, 0.004], n=3))
    st = g.merge(st, g.tube([(0, 0.092, 0.55), (0, 0.094, 0.46), (0, 0.11, 0.34), (0, 0.145, 0.2)], [0.004] * 4, n=3))
    items.append((st, gk.mark("stitch", lea)))
    items.append((ringtube((0, 0.015, 0.108), 0.203, 0.153, 0.005, n=18), gk.field("weave", 1.8)))
    ob = g.join("coat_body", [coat, g.pieces("coat_dress", items)])
    socks = gk._sockets({
        "socket_head": [(0, 0.0, 0.745)], "socket_eyes": [(0, -0.09, 0.69)], "socket_mouth": [(0, -0.09, 0.63)], "socket_grip": [(-0.205, -0.07, 0.26)],
        "socket_throat": [(0, -0.085, 0.585)], "socket_light": [(0.205, -0.07, 0.24)], "socket_back": [(0, 0.1, 0.5)], "socket_body": [(0, -0.105, 0.5)],
        "socket_tail": [(0, 0.15, 0.2)], "socket_arm_l": [(0.19, 0, 0.56)], "socket_arm_r": [(-0.19, 0, 0.56)],
        "socket_hand_l": [(0.205, -0.065, 0.27)], "socket_hand_r": [(-0.205, -0.065, 0.27)], "socket_limb_fl": [(0.08, -0.05, 0.11)], "socket_limb_fr": [(-0.08, -0.05, 0.11)],
        "socket_keepsake": [(0.0, -0.105, 0.55)],
    })
    return gk.Built([ob], socks)


# ======================================================================================
# Parts added with these forms (frames: docs/genius-forms.md). The first three are Seed-marks
# that had nothing to show for themselves on an art body.
# ======================================================================================

def grip_part():
    """A grip worn to the hand, on its back: a handle bound in leather, to lift it by."""
    arc = [(0, -0.055, 0.0), (0, -0.05, 0.035), (0, -0.02, 0.058), (0, 0.02, 0.058), (0, 0.05, 0.035), (0, 0.055, 0.0)]
    items = [(g.tube(arc, [0.012] * 6, n=6), gk.mat("leather_dark"))]
    wraps = None
    for (y, z) in ((-0.03, 0.053), (-0.01, 0.06), (0.01, 0.06), (0.03, 0.053)):
        wraps = g.merge(wraps, g.tube([(0, y - 0.005, z), (0, y + 0.005, z)], [0.0145, 0.0145], n=6))
    items.append((wraps, gk.mat("leather")))
    feet = g.merge(g.lathe([(0.02, 0.0), (0.017, 0.012)], n=6, centre=(0, -0.055, -0.002)), g.lathe([(0.02, 0.0), (0.017, 0.012)], n=6, centre=(0, 0.055, -0.002)))
    items.append((feet, gk.mat("metal_brass")))
    items.append((g.ico((0, 0, 0.068), 0.008, sub=0), gk.field("stud", 3.0)))
    return [gk._part("grip", items)]


def ledger_part():
    """A ledger, at its chest: a small book strapped shut, hung on a thong."""
    items = [(g.box((0, -0.024, -0.05), (0.075, 0.03, 0.095)), gk.mat("leather")),
             (g.box((0.003, -0.024, -0.05), (0.066, 0.024, 0.086)), gk.mat("paper")),
             (g.box((0, -0.041, -0.05), (0.082, 0.006, 0.02)), gk.mat("leather_dark")),
             (g.ico((0, -0.046, -0.05), 0.01, sub=0), gk.field("clasp", 2.5)),
             (g.tube([(-0.03, -0.01, 0.0), (-0.02, -0.02, -0.006)], [0.004, 0.004], n=3), gk.mat("cord")),
             (g.tube([(0.03, -0.01, 0.0), (0.02, -0.02, -0.006)], [0.004, 0.004], n=3), gk.mat("cord"))]
    return [gk._part("ledger", items)]


def broad_guard_part():
    """A broad guarding stance, on its shoulder: a plate of iron rimmed in brass (the left)."""
    plate = g.ico((0.012, 0, 0.0), 0.075, sub=1, scale=(0.32, 1.0, 0.95))
    rim = ringtube((0.012, 0, 0.0), 0.076, 0.072, 0.008, n=10, u=Y, v=Z)
    items = [(plate, gk.mat("metal_iron_light")), (rim, gk.mat("metal_brass")), (g.ico((0.038, 0, 0.0), 0.014, sub=0), gk.field("stud", 3.0)),
             (g.box((0.03, 0, -0.045), (0.012, 0.11, 0.012)), gk.mat("metal_dark"))]
    return [gk._part("broad-guard", items)]


def watching_eye_part():
    """An eye that opens in it: a third eye, upright, lidded, between its own."""
    items = _eye((0, -0.004, 0.03), 0.02, lids=gk.mat("horn_ridge"))
    return [gk._part("watching-eye", items)]


def shell_part():
    """A shell, on its back: one great scute, ringed, the rest remembered."""
    items = [(g.ico((0, 0, 0.0), 0.11, sub=1, scale=(1.0, 1.25, 0.34)), gk.mat("stone_plate")),
             (g.ico((0, 0, 0.022), 0.066, sub=1, scale=(1.0, 1.25, 0.3)), gk.mat("stone_hide")),
             (g.ico((0, 0, 0.038), 0.03, sub=0, scale=(1.0, 1.25, 0.3)), gk.mat("stone_light")),
             (ringtube((0, 0, 0.004), 0.108, 0.135, 0.005, n=14), gk.field("seam", 1.6))]
    return [gk._part("shell", items)]


# ======================================================================================
# Keepsakes: what a partner gives a genius to wear. Modelled at the socket's origin; the
# material keepsake_tint takes the colour the partner chose. A collar is a hoop a tenth of a
# unit in radius in its own XZ plane: a body's socket_collar gives it the size of its neck.
# ======================================================================================

def collar_keepsake():
    tint = gk.mat("keepsake_tint")
    items = [(strap(loop((0, 0, 0), 0.1, 0.1, n=16, u=X, v=Z), 0.03, 0.01, up=Y, closed=True), tint),
             (g.box((0.03, 0, 0.1), (0.03, 0.036, 0.012)), gk.mat("metal_brass")),
             (ringtube((0, -0.004, -0.122), 0.018, 0.018, 0.005, n=8, u=X, v=Z), gk.mat("metal_brass")),
             (g.ico((0, -0.004, -0.15), 0.011, sub=0), gk.field("stud", 3.0))]
    return [gk._part("collar", items)]


def ribbon_keepsake():
    tint = gk.mat("keepsake_tint")
    items = [(g.ico((0, -0.012, 0), 0.014, sub=0), tint)]
    for s in (1, -1):
        items.append((g.tongue([(0, -0.012, 0), (s * 0.03, -0.02, 0.022), (s * 0.055, -0.014, 0.006), (s * 0.03, -0.012, -0.012), (0, -0.012, 0)], [0.016, 0.03, 0.026, 0.024, 0.012], thick=0.25, normal=(0, -1, 0)), tint))
        items.append((g.tongue([(0, -0.014, -0.004), (s * 0.02, -0.02, -0.06), (s * 0.032, -0.016, -0.125)], [0.016, 0.024, 0.026], thick=0.2, normal=(0, -1, 0)), tint))
    return [gk._part("ribbon", items)]


def charm_keepsake():
    cord = g.merge(g.tube([(-0.02, 0, 0.0), (0, -0.01, -0.03)], [0.0035, 0.0035], n=3), g.tube([(0.02, 0, 0.0), (0, -0.01, -0.03)], [0.0035, 0.0035], n=3))
    disc = g.moved(g.lathe([(0.004, -0.006), (0.03, -0.004), (0.03, 0.004), (0.004, 0.006)], n=8), Matrix.Translation((0, -0.012, -0.058)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    items = [(cord, gk.mat("keepsake_tint")), (disc, gk.mat("metal_brass")), (g.ico((0, -0.019, -0.058), 0.011, sub=0, scale=(1, 0.5, 1)), gk.field("stud", 3.0))]
    return [gk._part("charm", items)]


def bell_keepsake():
    items = [(strap([(-0.022, 0, 0.0), (0, -0.012, -0.012), (0.022, 0, 0.0)], 0.018, 0.006, up=Z), gk.mat("keepsake_tint")),
             (g.lathe([(0.006, 0.0), (0.02, -0.008), (0.03, -0.034), (0.034, -0.05), (0.03, -0.054)], n=8, centre=(0, -0.014, -0.014)), gk.mat("metal_brass")),
             (g.ico((0, -0.014, -0.066), 0.009, sub=0), gk.mat("metal_dark")),
             (g.box((0, -0.046, -0.052), (0.006, 0.012, 0.022)), gk.mat("metal_dark"))]
    return [gk._part("bell", items)]


def build_keepsake(kid):
    gk.reset()
    objs = gk.KEEPSAKES[kid]()
    path = os.path.join(gk.OUT, "keepsakes", kid + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    gk.log("wrote", os.path.relpath(path, gk.ROOT), "%d triangles" % sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs))


# ======================================================================================
# Looks: the game's rules for how one genius differs from another (genius_look.gd), here so a
# sheet can show a form as the game will paint it. Keep the two in step.
# ======================================================================================

def _hash(text):
    h = 5381
    for ch in text:
        h = (h * 33 + ord(ch)) & 0xFFFFFFFF
    return h


def roll(seed, salt):
    return (_hash("%d|%s" % (seed, salt)) % 100003) / 100003.0


def _lin(hexcol):
    def ch(i):
        c = int(hexcol[i:i + 2], 16) / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (ch(1), ch(3), ch(5))


def resolve_look(look, form, silhouette):
    L = gk._data("genius-looks")
    body = L["bodies"].get(silhouette, {})
    seed = int(look.get("seed", 0))
    pal = list(L["palettes"].get(L["forms"].get(form, {}).get("coats", body.get("coats", "")), []))
    pal.sort(key=lambda c: roll(seed, "coat:" + c["id"]))
    offered = pal[:L["born"]["coatsOffered"]]
    coat = offered[max(0, min(int(look.get("coat", 0)), len(offered) - 1))] if offered else {}
    regions = sorted(body.get("marks", {}).keys(), key=lambda r: roll(seed, "mark:" + r))
    marks, n = {}, 0
    for r in regions:
        on = roll(seed, "mark:" + r) < L["born"]["markChance"] and n < L["born"]["marksMax"]
        marks[r] = on
        n += 1 if on else 0
    for r, v in look.get("marks", {}).items():
        if r in marks:
            marks[r] = bool(v)
    colors = {}
    if coat:
        for m, role in body.get("roles", {}).items():
            colors[m] = coat[role]
        for r, spec in body.get("marks", {}).items():
            colors["mark_" + r] = coat["mark"] if marks.get(r) else coat[spec["on"]]
    kc = next((c for c in L["keepsakeColors"] if c["id"] == look.get("keepsakeColor", "")), L["keepsakeColors"][0])
    colors["keepsake_tint"] = kc["color"]
    props = {p["id"]: roll(seed, "prop-a:" + p["id"]) + roll(seed, "prop-b:" + p["id"]) - 1.0 for p in L["proportions"]}
    keep = next((k for k in L["keepsakes"] if k["id"] == look.get("keepsake", "")), None)
    return {"coat": coat, "colors": colors, "marks": marks, "proportions": props, "keepsake": keep, "L": L}


def wear_look(built, shown, look, form, silhouette):
    """Paint a built form as the game would: coat, markings, build, keepsake."""
    res = resolve_look(look, form, silhouette)
    for m in bpy.data.materials:
        name = m.name.split(".")[0]
        if name in res["colors"] and m.use_nodes:
            c = _lin(res["colors"][name])
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    for p in res["L"]["proportions"]:
        v = max(-1.0, min(1.0, res["proportions"][p["id"]]))
        want = p["shapes"][0] if v < 0 else p["shapes"][1]
        for o in shown:
            if o.type == "MESH" and o.data.shape_keys:
                for sh in p["shapes"]:
                    kb = o.data.shape_keys.key_blocks.get(sh) if sh else None
                    if kb:
                        kb.value = abs(v) if sh == want else 0.0
    k = res["keepsake"]
    if k and k["id"] in gk.KEEPSAKES:
        for sn in k["sockets"]:
            if sn in built.sockets:
                shown += gk.hang(gk.KEEPSAKES[k["id"]](), built.sockets[sn])
                break
    bpy.context.view_layer.update()
    return res


def look_sheet(form_id, looks, out, cell=(384, 512), cols=4, samples=32, view=None):
    """One form in a spread of its looks: [{seed, coat, marks, keepsake, keepsakeColor}, ...]."""
    spec = gk.form_spec(form_id)
    paths = []
    for i, look in enumerate(looks):
        built, shown = gk.assemble(form_id)
        res = wear_look(built, shown, look, form_id, spec["silhouette"])
        path = os.path.join(gk.SCRATCH, "look_%s_%02d.png" % (form_id, i))
        gk.render(path, shown, rim=gk.SHAPE_RIMS.get(spec["expression"], (0.42, 0.9, 0.55)), res=(cell[0] * 2, cell[1] * 2), samples=samples, card=False,
                  view=view or gk.CARD_VIEWS.get(form_id, (0.8, -1.25, 0.35)), zoom=gk.CARD_ZOOM.get(form_id, 1.0))
        gk.log("look", i, json.dumps({"coat": res["coat"].get("id"), "marks": [m for m, on in res["marks"].items() if on], "build": round(res["proportions"].get("build", 0), 2), "keepsake": look.get("keepsake", "")}))
        paths.append(path)
    gk.tile(paths, out, cols, cell)
