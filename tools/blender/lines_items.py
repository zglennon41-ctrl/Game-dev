"""WILDLINE genius lines, the items of power: the Lantern, the Astrolabe and the Bell
(docs/genius-evolutions.md, "The items of power"). genius_lines.py loads this file
(register()) and builds one model a form from the `body` of its node in
data/genius-bases/<base>.json.

An item is an instrument, and every form of it is a different instrument: its vessel (or
plate, or bell), how it holds itself up, what stands between you and its light, what it
has been given to do its work with. It is also alive, so every form has a face: an eye in
the metal, and legs or a posture where it has grown them.

What every model here keeps to, beside the contract's own:
  - It is built in the kit's units and brought to the kit's size by `ref_top`, the top of
    the instrument's own body; what it carries above that (a post, a crown of rays) stands
    above its stage's height.
  - `carry`: an empty where a hand or a hook takes it (the lantern's ring, the astrolabe's
    ring, the bell's handle or the eye of its yoke). It is not turned: the instrument hangs
    below it, upright, facing -Y like the body, so the game can hang any form of any of
    the three from a hand, a belt or a bracket by putting `carry` there. How tall it is in
    the hand is the form's `held` (metres, in its `body`).
  - The coat's roles are taken from the look of the silhouette the form is drawn as
    (data/genius-looks.json, bodies): a lantern's main metal is its partner's brass, a
    bell's its partner's bronze; glass, enamel, wax, rope and wood keep their own colours.
  - A turned thing is round (shaded round, its rims crisp); a cut or forged thing keeps its
    planes.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
import genius_forms2 as f2  # noqa: E402
import genius_relics as gr  # noqa: E402
from genius_kit import mat, field, STAND  # noqa: E402

gl = None       # genius_lines, found by register()

kit.PALETTE.update({
    "glass_green": ((0.08, 0.3, 0.17), 0.2, 0.0), "glass_red": ((0.42, 0.07, 0.06), 0.2, 0.0), "glass_blue": ((0.1, 0.18, 0.42), 0.2, 0.0),
    "glass_clear": ((0.62, 0.72, 0.74), 0.1, 0.0), "enamel_green": ((0.1, 0.26, 0.18), 0.3, 0.0), "enamel_blue": ((0.1, 0.16, 0.3), 0.3, 0.0),
    "enamel_night": ((0.03, 0.035, 0.07), 0.35, 0.0), "enamel_red": ((0.4, 0.09, 0.07), 0.35, 0.0),
    "verdigris": ((0.24, 0.42, 0.36), 0.9, 0.0), "wax_red": ((0.45, 0.08, 0.07), 0.6, 0.0), "white_hot": ((0.95, 0.94, 0.88), 0.2, 0.0),
    "dial_face": ((0.74, 0.69, 0.56), 0.6, 0.0), "soot": ((0.035, 0.03, 0.03), 0.95, 0.0), "rope": ((0.42, 0.34, 0.22), 0.95, 0.0),
    "reed": ((0.3, 0.33, 0.16), 0.9, 0.0), "weed": ((0.12, 0.24, 0.14), 0.9, 0.0), "crepe": ((0.03, 0.03, 0.035), 0.95, 0.0),
    "cloth_red": ((0.36, 0.1, 0.08), 0.95, 0.0), "skin_keeper": ((0.5, 0.4, 0.33), 0.7, 0.0), "ribbon": ((0.5, 0.12, 0.1), 0.9, 0.0),
    "mist": ((0.5, 0.52, 0.53), 0.95, 0.0), "tin": ((0.42, 0.43, 0.44), 0.35, 0.8),
})


def log(*a):
    print("[lines_items]", *a)


# ======================================================================================
# The small kit: items are (geometry, material) or (geometry, material, shade)
# ======================================================================================

ROUND, FLAT, SOFT = "round", "flat", "soft"
SOFT_MATS = ("cloth", "smoke", "shade", "mist", "rope", "cord", "ribbon", "crepe", "weed", "reed", "wool", "skin")
LOOKS = None


def roles(silhouette):
    """The materials of a silhouette's coat by role (main, under, trim), from the looks."""
    global LOOKS
    if LOOKS is None:
        with open(os.path.join(kit.ROOT, "data", "genius-looks.json")) as f:
            LOOKS = json.load(f)
    return {role: name for name, role in LOOKS["bodies"].get(silhouette, {}).get("roles", {}).items()}


class Metals:
    """The metals a form is made of: its coat's where its silhouette's coat is metal, and
    the kit's brass, iron and dark where it is not (a keeper's coat is wool; its lamp is brass)."""

    def __init__(self, silhouette, fallback=("metal_brass", "metal_iron", "metal_dark")):
        r = roles(silhouette)
        names = [r.get(k, "") for k in ("main", "under", "trim")]
        self.coat = r
        self.main, self.under, self.trim = (mat(n if n.startswith("metal") else fb) for n, fb in zip(names, fallback))


def TR(at=(0, 0, 0), rot=None, s=None):
    """A placement: turned (Euler x, y, z), scaled (a number or three), then moved."""
    M = Matrix.Translation(V(at))
    if rot is not None:
        M = M @ Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
    if s is not None:
        M = M @ (Matrix.Scale(s, 4) if isinstance(s, (int, float)) else Matrix.Diagonal((s[0], s[1], s[2], 1.0)))
    return M


def put(items, M):
    return [(g.moved(i[0], M),) + tuple(i[1:]) for i in items if i and i[0] and i[0][0]]


def phase(n):
    """The turn that puts a flat side of an n-sided lathe to the front."""
    return 0.0 if n % 4 == 2 else math.pi / n


def turned(profile, n=12, centre=(0, 0, 0), caps=True):
    return g.lathe(profile, n=n, centre=centre, caps=caps, phase=phase(n))


def hoop(c, r, t, n=14, sides=3, u=X, v=Y):
    return f2.band(c, r, r, t, n=n, u=u, v=v, sides=sides)


def rod(a, b, r, n=4, r1=None):
    return g.tube([V(a), V(b)], [r, r if r1 is None else r1], n=n)


def ball(c, r, sub=1, scale=(1, 1, 1)):
    return g.ico(c, r, sub=sub, scale=scale)


def disc(c, r, t, n=14, facing=Y):
    """A flat round plate about c, its faces looking along `facing` (Y: to the front and back)."""
    geo = g.lathe([(0.0, -t / 2), (r, -t / 2), (r, t / 2), (0.0, t / 2)], n=n, phase=phase(n))
    f = V(facing).normalized()
    R = Matrix.Identity(4) if abs(f.dot(Z)) > 0.999 else Z.rotation_difference(f).to_matrix().to_4x4()
    return g.moved(geo, Matrix.Translation(V(c)) @ R)


def chain(a, b, size=0.02, sag=0.0):
    """Links from a to b (hanging a little if sag)."""
    a, b = V(a), V(b)
    n = max(2, int((b - a).length / (size * 1.7)))
    geo = None
    d = (b - a).normalized()
    side = d.cross(Z if abs(d.dot(Z)) < 0.9 else X).normalized()
    up = side.cross(d).normalized()
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t) + Z * (-sag * math.sin(math.pi * t))
        geo = g.merge(geo, f2.band(p, size * 0.6, size, size * 0.24, n=5, u=(side if i % 2 else up), v=d, sides=3))
    return geo


def eye(c, r, metals, facing=(0, -1, 0), heavy=False, dark=False):
    """Where it is alive: an iris of the field in a dark socket, a slit down it, a lid of its
    own metal; a heavy lid for one that is old or sits up late; a dark eye, lit only in its
    slit, for one that keeps a dark face turned outward."""
    c, f = V(c), V(facing).normalized()
    side = f.cross(Z).normalized() if abs(f.dot(Z)) < 0.9 else X
    up = side.cross(f).normalized()
    R4 = Matrix((side, f, up)).transposed().to_4x4()
    items = [(f2.band(c, r * 1.2, r * 1.2, r * 0.22, n=10, u=side, v=up, sides=4), metals.trim, ROUND)]
    items.append((g.moved(ball((0, 0, 0), r, sub=1, scale=(1.0, 0.42, 1.0)), Matrix.Translation(c) @ R4), mat("enamel_night") if dark else field("eyes", 3.6), ROUND))
    pup = ball((0, 0, 0), r * 0.5, sub=0, scale=(0.4, 0.5, 1.5))
    items.append((g.moved(pup, Matrix.Translation(c + f * (r * 0.34)) @ R4), field("eyes", 3.6) if dark else mat("eye_dark")))
    lid = 0.95 if heavy else 0.42
    a, b = c - side * (r * 1.12) + f * (r * 0.3) + up * (r * 0.5), c + side * (r * 1.12) + f * (r * 0.3) + up * (r * 0.5)
    mid = c + up * (r * (1.08 - lid * 0.45)) + f * (r * 0.52)
    items.append((g.tongue([a, mid, b], [r * 0.22, r * lid, r * 0.22], thick=0.45, normal=f + up * 0.4), metals.main))
    return items


def lens(c, r, metals, facing=(0, -1, 0), pupil=False, glow="eyes", strength=3.6, deep=0.5):
    """A lens in a rim, lit from behind; with a pupil where it is the thing's eye."""
    c, f = V(c), V(facing).normalized()
    side = f.cross(Z).normalized() if abs(f.dot(Z)) < 0.9 else X
    up = side.cross(f).normalized()
    R = Matrix((side, f, up)).transposed().to_4x4()
    items = [(g.moved(ball((0, 0, 0), r * 0.92, sub=1, scale=(1.0, deep, 1.0)), Matrix.Translation(c) @ R), field(glow, strength), ROUND)]
    items.append((f2.band(c, r, r, r * 0.17, n=10, u=side, v=up, sides=3), metals.main, ROUND))
    if pupil:
        items.append((g.moved(ball((0, 0, 0), r * 0.36, sub=0, scale=(0.55, 0.5, 1.6)), Matrix.Translation(c + f * (r * deep * 0.8)) @ R), mat("eye_dark")))
    return items


def _object(name, geo, material, shade):
    ob = g.to_object(name, geo, material, smooth=(shade != FLAT))
    if shade == ROUND:
        ob.data.set_sharp_from_angle(angle=math.radians(42))
    return ob


def pieces(name, items):
    """One object from items; each is shaded as it is made (turned things round, the rest
    by their stuff)."""
    obs = []
    for i, it in enumerate(items):
        if not it or not it[0] or not it[0][0]:
            continue
        geo, material = it[0], it[1]
        shade = it[2] if len(it) > 2 else (SOFT if material.name.startswith(SOFT_MATS) else (ROUND if material.name.startswith("field") else FLAT))
        obs.append(_object("%s_%d" % (name, i), geo, material, shade))
    return g.join(name, obs)


def bounds(items):
    pts = [p for it in items if it and it[0] for p in it[0][0]]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def finish(form_id, items, anchors, wings=None, ref=None):
    """Stand it on the ground, bring it to the kit's size by its `ref` (the top of its own
    body), give it its sockets and its `carry`, and write it."""
    lo, hi = bounds(items + [w for ws in (wings or {}).values() for w in ws])
    ref = (ref if ref is not None else hi.z) - lo.z
    # a thing much wider than it is tall is stood smaller, so that it is not a room across
    wide = max(hi.x - lo.x, hi.y - lo.y)
    ref = max(ref, 0.62 * wide)
    k = STAND / ref
    M = Matrix.Scale(k, 4) @ Matrix.Translation((0, 0, -lo.z))
    items = put(items, M)
    fix = lambda p: M @ V(p)  # noqa: E731
    obs = [pieces(form_id.replace("-", "_"), items)]
    for name, parts in (wings or {}).items():
        w = pieces(name, put(parts, M))
        kit.set_origin(w, fix(anchors[name]))
        obs.append(w)
    top, face, light = fix(anchors["top"]), fix(anchors["face"]), fix(anchors["light"])
    half = max(0.08, min(0.3, (hi.x - lo.x) * k / 2))
    back = fix(anchors.get("back", (0, hi.y, anchors["face"][2])))
    table = {
        "socket_head": [tuple(top)], "socket_eyes": [tuple(face + Vector((0, -0.01, 0.05)))], "socket_mouth": [tuple(face + Vector((0, -0.01, -0.03)))],
        "socket_grip": [(half + 0.03, face.y * 0.5, face.z)], "socket_throat": [tuple(face + Vector((0, -0.005, -0.08)))], "socket_light": [tuple(light)],
        "socket_back": [tuple(back)], "socket_body": [tuple(face + Vector((0, -0.01, -0.12)))], "socket_tail": [tuple(back + Vector((0, 0.01, -0.1)))],
        "socket_arm_l": [(half, 0, face.z)], "socket_arm_r": [(-half, 0, face.z)],
        "socket_limb_fl": [(half * 0.6, face.y * 0.6, 0.04)], "socket_limb_fr": [(-half * 0.6, face.y * 0.6, 0.04)],
        "socket_hand_l": [(half * 0.6, face.y * 0.6, 0.06), kit.HAND_ON_PAW_L], "socket_hand_r": [(-half * 0.6, face.y * 0.6, 0.06), kit.HAND_ON_PAW_R],
        "socket_keepsake": [tuple(fix(anchors["keepsake"]) if "keepsake" in anchors else face + Vector((0, -0.01, -0.16)))],
    }
    sockets = kit._sockets(table)
    sockets["carry"] = kit.free_socket("carry", fix(anchors["carry"]))
    path = os.path.join(gl.OUT, form_id + ".glb")
    gl.export_objects(obs, sockets, path, ref=STAND)
    size = os.path.getsize(path) // 1024
    if size > 80:
        log("OVER BUDGET", form_id, size, "KB")
    return size


def flame(style, c, s=1.0, lean=0.0):
    """The light itself. c is where it burns from; s its size."""
    c = V(c)
    if style == "candle":
        geo = g.lathe([(0.0, 0.0), (0.03, 0.025), (0.036, 0.06), (0.02, 0.11), (0.0, 0.17)], n=6)
        return put([(geo, field("core", 4.5), ROUND)], TR(c, rot=(lean, 0, 0), s=s))
    if style == "low":
        return [(ball(c + Z * 0.02 * s, 0.03 * s, sub=1, scale=(1, 1, 1.2)), field("core", 3.4), ROUND)]
    if style == "tall":
        geo = g.lathe([(0.0, 0.0), (0.04, 0.04), (0.05, 0.11), (0.03, 0.22), (0.012, 0.31), (0.0, 0.36)], n=6)
        return put([(geo, field("core", 4.8), ROUND)], TR(c, s=s))
    if style == "clear":
        geo = g.lathe([(0.0, 0.0), (0.022, 0.04), (0.026, 0.12), (0.012, 0.26), (0.0, 0.34)], n=5)
        return put([(geo, field("core", 4.8), ROUND)], TR(c, s=s))
    if style == "star":        # white at the instant: a burst of points round a white heart
        items = [(ball(c + Z * 0.07 * s, 0.045 * s, sub=1), mat("white_hot"), ROUND)]
        pts = None
        for i in range(10):
            a, b = i * 2.39996, math.acos(1 - 2 * (i + 0.5) / 10)
            d = Vector((math.sin(b) * math.cos(a), math.sin(b) * math.sin(a), math.cos(b)))
            L = (0.17 + 0.07 * (i % 3)) * s
            pts = g.merge(pts, g.blade(c + Z * 0.07 * s + d * 0.03 * s, c + Z * 0.07 * s + d * L, 0.05 * s, normal=d.cross(Z if abs(d.z) < 0.9 else X)))
        return items + [(pts, field("flare", 5.0))]
    if style == "cold":        # a colour the surface has no name for: a dark heart in a pale light
        return [(ball(c + Z * 0.07 * s, 0.07 * s, sub=1, scale=(0.85, 0.85, 1.3)), field("core", 4.5), ROUND),
                (ball(c + Z * 0.07 * s, 0.036 * s, sub=0, scale=(1, 1, 1.5)), mat("enamel_night")),
                (hoop(c + Z * 0.07 * s, 0.1 * s, 0.008 * s, n=10), field("seam", 2.2))]
    if style == "root":        # post-blue at the root
        geo = g.lathe([(0.0, 0.07), (0.04, 0.09), (0.03, 0.17), (0.0, 0.24)], n=6)
        root = g.lathe([(0.0, 0.0), (0.035, 0.02), (0.044, 0.06), (0.04, 0.09), (0.0, 0.09)], n=6)
        return put([(geo, field("core", 4.6), ROUND), (root, mat("glass_blue"), ROUND)], TR(c, s=s))
    if style == "points":      # a crown of small steady points
        items = []
        for i in range(8):
            a = 2 * math.pi * i / 8
            items += flame("candle", c + Vector((math.cos(a) * 0.1 * s, math.sin(a) * 0.1 * s, 0)), 0.45 * s)
        return items
    if style == "coal":
        items = []
        for i, (dx, dy) in enumerate(((0, 0), (0.035, 0.02), (-0.03, 0.025), (0.01, -0.035))):
            items.append((ball(c + Vector((dx * s, dy * s, 0.02 * s + 0.012 * (i % 2))), 0.03 * s, sub=0), field("ember", 2.6) if i != 2 else mat("coal")))
        return items
    if style == "flat":        # white and flat
        return [(g.box(c + Z * 0.01 * s, (0.34 * s, 0.12 * s, 0.02 * s)), field("core", 4.2), FLAT)]
    # the heart: a faceted light loose in its chamber
    return [(ball(c + Z * 0.075 * s, 0.056 * s, sub=1, scale=(0.85, 0.85, 1.25)), field("core", 4.5), ROUND)]


# ======================================================================================
# The Lantern
# ======================================================================================

def lamp_head(spec, m, s=1.0):
    """The lamp itself, standing on the origin: its vessel, what stands between you and the
    flame, its roof and its ring. Returns (items, anchors)."""
    b = spec.get("build", {})
    style, vs = gl.opt(spec.get("vessel", "hex"))
    R, H = 0.125 * b.get("w", 1.0) * vs, 0.22 * b.get("h", 1.0) * vs
    items = []
    n, z0 = 6, 0.07                 # sides; the chamber's floor
    lit = Vector((0, 0, z0 + 0.015))    # where the flame burns from
    front = R + 0.02                # how far the face of the base stands to the front
    if style in ("box", "hex", "oct"):
        n = {"box": 4, "hex": 6, "oct": 8}[style]
        items.append((turned([(R * 0.4, 0.0), (R * 1.0, 0.015), (R * 1.2, 0.05), (R * 1.04, z0)], n=n), m.main))
        for k in range(n):
            a = phase(n) + 2 * math.pi * k / n
            p = Vector((R * 0.96 * math.cos(a), R * 0.96 * math.sin(a), 0))
            items.append((rod(p + Z * z0, p + Z * (z0 + H), 0.012 if n < 8 else 0.009), m.main))
        items.append((turned([(R * 1.04, z0 + H), (R * 1.24, z0 + H + 0.015), (R * 1.18, z0 + H + 0.032)], n=n), m.main))
        z1 = z0 + H + 0.032
        front = R * 1.2 * math.cos(math.pi / n)
    elif style == "drum":           # a round dark-lantern: closed behind, open to the front
        n = 10
        items.append((turned([(R * 0.5, 0.0), (R * 1.08, 0.02), (R * 1.08, z0)], n=n), m.main, ROUND))
        back = None
        for k in range(n):
            a0, a1 = phase(n) + 2 * math.pi * k / n, phase(n) + 2 * math.pi * (k + 1) / n
            mid = (a0 + a1) / 2
            if math.sin(mid) > -0.45:       # every side but the front
                p0, p1 = Vector((R * math.cos(a0), R * math.sin(a0), 0)), Vector((R * math.cos(a1), R * math.sin(a1), 0))
                back = g.merge(back, g.loft([[p0 + Z * z0, p1 + Z * z0, p1 * 0.93 + Z * z0, p0 * 0.93 + Z * z0], [p0 + Z * (z0 + H), p1 + Z * (z0 + H), p1 * 0.93 + Z * (z0 + H), p0 * 0.93 + Z * (z0 + H)]]))
        items.append((back, m.under))
        items.append((turned([(R * 1.08, z0 + H), (R * 1.14, z0 + H + 0.02), (R * 1.0, z0 + H + 0.035)], n=n), m.main, ROUND))
        z1 = z0 + H + 0.035
        front = R * 1.08
    elif style == "safety":         # a miner's lamp: glass below in a guard, gauze above
        n = 8
        R *= 0.72
        H *= 1.5
        zm = z0 + H * 0.45
        items.append((turned([(R * 0.7, 0.0), (R * 1.25, 0.02), (R * 1.25, z0 * 0.7), (R * 1.0, z0)], n=n), m.main, ROUND))
        items.append((turned([(R * 1.12, zm - 0.012), (R * 1.12, zm + 0.012)], n=n, caps=True), m.main, ROUND))
        items.append((turned([(R * 0.9, zm + 0.012), (R * 0.84, z0 + H), (R * 0.5, z0 + H + 0.03)], n=n), m.trim, ROUND))
        for z in (zm + (z0 + H - zm) * 0.33, zm + (z0 + H - zm) * 0.66):
            items.append((hoop((0, 0, z), R * 0.9, 0.006, n=n), m.under))
        z1 = z0 + H + 0.03
        front = R * 1.25
        H = zm - z0                 # the lit part is the glass below
    elif style == "globe":          # a ball of thick glass and iron for where the dark is heavy
        n = 10
        c = Vector((0, 0, R * 1.3))
        items.append((ball(c, R * 1.3, sub=2), m.under, ROUND))
        for z, rr in ((c.z, R * 1.33), (c.z + R * 0.75, R * 1.08), (c.z - R * 0.75, R * 1.08)):
            items.append((hoop((0, 0, z), rr, 0.014, n=12, sides=4), m.main))
        items.append((turned([(R * 0.7, c.z + R * 1.2), (R * 0.5, c.z + R * 1.36), (R * 0.3, c.z + R * 1.4)], n=8), m.main, ROUND))
        z0, z1, H = c.z - R * 0.4, c.z + R * 1.4, R * 0.8
        lit = Vector((0, 0, c.z - R * 0.25))
        front = R * 1.3
    elif style == "font":           # an oil lamp: a round font, a burner, a chimney in a frame
        n = 10
        items.append((turned([(R * 0.6, 0.0), (R * 1.25, 0.02), (R * 1.35, 0.055), (R * 1.0, 0.1), (R * 0.45, 0.115)], n=n), m.main, ROUND))
        items.append((turned([(R * 0.36, 0.115), (R * 0.42, 0.135), (R * 0.3, 0.15)], n=8), m.trim, ROUND))
        z0 = 0.14
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            p = Vector((R * 0.78 * math.cos(a), R * 0.78 * math.sin(a), 0))
            items.append((g.tube([p * 0.6 + Z * 0.115, p + Z * (z0 + H * 0.3), p * 0.72 + Z * (z0 + H)], [0.008, 0.008, 0.008], n=4), m.under))
        for z, rr in ((z0 + H * 0.3, R * 0.8), (z0 + H, R * 0.58)):
            items.append((hoop((0, 0, z), rr, 0.008, n=10), m.under))
        z1 = z0 + H
        lit = Vector((0, 0, 0.15))
        front = R * 1.35
    elif style == "dome":           # low under a pierced cover
        n = 12
        items.append((turned([(R * 0.7, 0.0), (R * 1.5, 0.02), (R * 1.56, 0.05), (R * 1.42, 0.06)], n=n), m.main, ROUND))
        prof = [(R * 1.4 * math.cos(t), 0.06 + R * 1.15 * math.sin(t)) for t in (0.0, 0.35, 0.7, 1.05, 1.35)]
        items.append((turned(prof + [(R * 0.16, 0.06 + R * 1.2)], n=n), m.under, ROUND))
        z0, z1, H = 0.06, 0.06 + R * 1.2, R * 0.8
        lit = Vector((0, 0, 0.07))
        front = R * 1.56
    elif style == "cup":            # a cup on a foot, the flame stood in it behind a guard
        n = 10
        items.append((turned([(R * 0.95, 0.0), (R * 1.0, 0.015), (R * 0.3, 0.05), (R * 0.22, 0.1), (R * 0.36, 0.118), (R * 0.22, 0.136), (R * 0.5, 0.17), (R * 1.0, 0.215), (R * 1.08, 0.25), (R * 0.9, 0.25)], n=n), m.main, ROUND))
        z0 = 0.235
        for z in (z0 + 0.03, z0 + H * 0.62):
            items.append((hoop((0, 0, z), R * 0.72, 0.007, n=10), m.under))
        for k in range(3):
            a = math.pi / 2 + 2 * math.pi * k / 3
            p = Vector((R * 0.72 * math.cos(a), R * 0.72 * math.sin(a), 0))
            items.append((rod(p + Z * z0, p + Z * (z0 + H), 0.007), m.under))
        z1 = z0 + H
        front = R * 1.0
    elif style == "glasshouse":     # all glass, in many small panes, with a walk round it
        n = 8
        R *= 1.15
        H *= 1.5
        items.append((turned([(R * 0.6, 0.0), (R * 1.28, 0.02), (R * 1.28, 0.05), (R * 1.0, z0)], n=n), m.main))
        for k in range(n):
            a0, a1 = phase(n) + 2 * math.pi * k / n, phase(n) + 2 * math.pi * (k + 1) / n
            p0, p1 = Vector((R * math.cos(a0), R * math.sin(a0), 0)), Vector((R * math.cos(a1), R * math.sin(a1), 0))
            items.append((rod(p0 + Z * z0, p0 + Z * (z0 + H), 0.01), m.main))
            for t in (0.5,):
                items.append((rod(p0 + Z * (z0 + H * t), p1 + Z * (z0 + H * t), 0.005, n=3), m.trim))
            items.append((rod((p0 + p1) / 2 + Z * z0, (p0 + p1) / 2 + Z * (z0 + H), 0.005, n=3), m.trim))
            # the glass: kept very clean, a pale glint in each top pane
            items.append((g.box((p0 + p1) / 2 * 0.985 + Z * (z0 + H * 0.84), ((p1 - p0).length * 0.38, 0.004, H * 0.2), rot=(0, 0, (a0 + a1) / 2 + math.pi / 2)), mat("glass_clear")))
        items.append((turned([(R * 1.0, z0 + H), (R * 1.16, z0 + H + 0.014), (R * 1.1, z0 + H + 0.03)], n=n), m.main))
        z1 = z0 + H + 0.03
        front = R * 1.28
    elif style == "belly":          # a stove: a round iron belly with a door
        n = 10
        prof = [(R * 0.8, 0.0), (R * 1.3, 0.04), (R * 1.62, 0.14), (R * 1.62, 0.2), (R * 1.3, 0.3), (R * 0.92, 0.335), (R * 0.92, 0.36), (R * 1.05, 0.365), (R * 1.05, 0.385), (R * 0.4, 0.4)]
        items.append((turned(prof, n=n), m.main, ROUND))
        items.append((hoop((0, 0, 0.17), R * 1.64, 0.012, n=n, sides=4), m.under))
        z0, z1, H = 0.1, 0.4, 0.16
        lit = Vector((0, -R * 0.7, 0.1))
        front = R * 1.62
    elif style == "column":         # a plain tall glass and nothing else
        n = 8
        R *= 0.62
        H *= 2.3
        items.append((turned([(R * 1.5, 0.0), (R * 1.6, 0.02), (R * 1.0, 0.05), (R * 1.0, z0)], n=n), m.main, ROUND))
        for k in range(3):
            a = math.pi / 2 + 2 * math.pi * k / 3
            p = Vector((R * math.cos(a), R * math.sin(a), 0))
            items.append((rod(p + Z * z0, p + Z * (z0 + H), 0.007), m.under))
        items.append((turned([(R * 1.0, z0 + H), (R * 1.1, z0 + H + 0.012), (R * 0.9, z0 + H + 0.024)], n=n), m.main, ROUND))
        z1 = z0 + H + 0.024
        front = R * 1.6
    else:                           # "pyramid": a case that narrows upward, open at the front
        n = 4
        H *= 1.9
        items.append((turned([(R * 1.5, 0.0), (R * 1.56, 0.02), (R * 1.5, 0.045)], n=n), m.main))
        for k in range(n):
            a = phase(n) + 2 * math.pi * k / n
            d = Vector((math.cos(a), math.sin(a), 0))
            items.append((rod(d * R * 1.4 + Z * 0.045, d * R * 0.5 + Z * (0.045 + H), 0.014), m.main))
        back = [Vector((R * 0.97, R * 0.97, 0.05)), Vector((-R * 0.97, R * 0.97, 0.05)), Vector((-R * 0.36, R * 0.36, 0.045 + H)), Vector((R * 0.36, R * 0.36, 0.045 + H))]
        items.append((g.loft([back, [p + Vector((0, -0.012, 0)) for p in back]]), m.under))
        items.append((turned([(R * 0.5, 0.045 + H), (R * 0.56, 0.06 + H), (R * 0.3, 0.075 + H)], n=n), m.main))
        z0, z1 = 0.05, 0.075 + H
        front = R * 1.5 * math.cos(math.pi / 4)
    mid = (z0 + min(z1, z0 + H)) / 2

    # what stands between you and the flame
    for gstyle, gs in gl.each(spec.get("glass")):
        if gstyle == "bars":
            for k in range(n):
                a0, a1 = phase(n) + 2 * math.pi * k / n, phase(n) + 2 * math.pi * (k + 1) / n
                p0, p1 = Vector((R * 0.96 * math.cos(a0), R * 0.96 * math.sin(a0), 0)), Vector((R * 0.96 * math.cos(a1), R * 0.96 * math.sin(a1), 0))
                for t in (0.25, 0.8):
                    items.append((rod(p0 + Z * (z0 + H * t), p1 + Z * (z0 + H * t), 0.005, n=3), m.trim))
        elif gstyle == "cage":      # a guard of wire, scratched from squeezing through
            for k in range(8):
                a = 2 * math.pi * (k + 0.5) / 8
                d = Vector((math.cos(a), math.sin(a), 0))
                items.append((g.tube([d * R * 1.25 + Z * (z0 - 0.01), d * R * 1.42 + Z * (z0 + H * 0.5), d * R * 1.1 + Z * (z0 + H * 1.02)], [0.006] * 3, n=3), m.under))
            items.append((hoop((0, 0, z0 + H * 0.5), R * 1.42, 0.006, n=10), m.under))
        elif gstyle == "lens":      # a bullseye to the front
            items += lens((0, -front - 0.012, mid), min(R * 0.78, H * 0.62) * gs, m, pupil=(spec.get("face") == "lens"), glow="core", strength=4.2)
        elif gstyle == "shutter":   # leaves that open on the side you have not been
            for sgn in (1, -1):
                items.append((g.box((sgn * R * 0.86, -R * 0.82, mid), (0.012, R * 0.72, H * 0.92), rot=(0, 0, sgn * 0.55)), m.under))
        elif gstyle == "portholes":
            for a in (-math.pi / 2, -math.pi / 2 + 1.25, -math.pi / 2 - 1.25):
                d = Vector((math.cos(a), math.sin(a), 0))
                items += lens(d * (front + 0.004) + Z * (mid + 0.02), R * 0.42 * gs, m, facing=d, glow="core", strength=4.0, deep=0.35, pupil=(spec.get("face") == "lens" and d.y < -0.99))
        elif gstyle == "pierced":   # small lights where the cover is cut through
            dots = None
            for ring_i, (zt, cnt) in enumerate(((0.38, 9), (0.8, 7), (1.12, 4))):
                for k in range(cnt):
                    a = 2 * math.pi * (k + 0.5 * ring_i) / cnt
                    rr = R * 1.42 * math.cos(zt) + 0.004
                    dots = g.merge(dots, ball((rr * math.cos(a), rr * math.sin(a), 0.06 + R * 1.17 * math.sin(zt)), 0.014 * gs, sub=0))
            items.append((dots, field("pierce", 3.2)))
        elif gstyle == "gem":       # the flame stood in a cut crystal
            c = lit + Z * (H * 0.45)
            items.append((g.lathe([(0.0, -H * 0.42), (R * 0.5, -H * 0.1), (R * 0.56, H * 0.12), (0.0, H * 0.5)], n=6, centre=c), mat("glass_clear"), FLAT))
            items.append((ball(c, R * 0.3, sub=0, scale=(1, 1, 1.5)), field("core", 4.6)))
        elif gstyle == "hood":      # a hood on one side, so the light falls only where it chooses
            hood = None
            for k in range(5):
                a = math.radians(-20 + 50 * k)
                d0, d1 = Vector((math.cos(a), math.sin(a), 0)), Vector((math.cos(a + math.radians(50)), math.sin(a + math.radians(50)), 0))
                rr = R * 1.22
                hood = g.merge(hood, g.loft([[d0 * rr + Z * (z0 - 0.02), d1 * rr + Z * (z0 - 0.02), d1 * (rr + 0.01) + Z * (z0 - 0.02), d0 * (rr + 0.01) + Z * (z0 - 0.02)],
                                             [d0 * rr * 0.9 + Z * (z1 + 0.05), d1 * rr * 0.9 + Z * (z1 + 0.05), d1 * (rr * 0.9 + 0.01) + Z * (z1 + 0.05), d0 * (rr * 0.9 + 0.01) + Z * (z1 + 0.05)]]))
            items.append((hood, mat("soot")))
        elif gstyle == "signals":   # two glasses: it shows you the green
            items += lens((0, -front - 0.012, mid), R * 0.74 * gs, m, glow="core", strength=1.0)
            items.append((disc((0, -front - 0.03, mid), R * 0.6 * gs, 0.012, n=10), mat("glass_green"), ROUND))
            for sgn in (1, -1):
                d = Vector((sgn, 0, 0))
                items.append((disc(d * (front + 0.02) + Z * mid, R * 0.56 * gs, 0.012, n=10, facing=d), mat("glass_red"), ROUND))
                items.append((f2.band(d * (front + 0.012) + Z * mid, R * 0.68 * gs, R * 0.68 * gs, 0.012, n=10, u=Y, v=Z, sides=4), m.main))

    # the roof, and the ring it is carried by
    rstyle, rs = gl.opt(spec.get("roof", "vent"))
    top = z1
    if rstyle == "cap":
        items.append((turned([(R * 1.28, z1), (R * 0.2, z1 + 0.09 * rs), (0.02, z1 + 0.1 * rs)], n=n), m.under))
        top = z1 + 0.1 * rs
    elif rstyle == "vent":
        items.append((turned([(R * 1.34, z1), (R * 1.0, z1 + 0.05 * rs), (R * 0.46, z1 + 0.098 * rs), (R * 0.37, z1 + 0.12 * rs)], n=n), m.under))
        items.append((turned([(R * 0.5, z1 + 0.12 * rs), (R * 0.58, z1 + 0.134 * rs), (R * 0.27, z1 + 0.158 * rs), (0.012, z1 + 0.168 * rs)], n=n), m.main))
        top = z1 + 0.168 * rs
    elif rstyle == "hood":          # a deep hood drawn forward over the light
        hood = [(R * 1.3, z1), (R * 1.1, z1 + 0.07 * rs), (R * 0.4, z1 + 0.12 * rs), (0.02, z1 + 0.13 * rs)]
        items.append((turned(hood, n=n), m.under, ROUND))
        items.append((g.box((0, -R * 1.2, z1 + 0.005), (R * 1.9, R * 0.9, 0.014), rot=(-0.3, 0, 0)), m.under))
        top = z1 + 0.13 * rs
    elif rstyle == "gauze":         # the gauze is the roof; a hook above it
        items.append((turned([(R * 0.62, z1), (R * 0.68, z1 + 0.012), (R * 0.4, z1 + 0.03)], n=8), m.main, ROUND))
        items.append((g.tube([(0, 0, z1 + 0.03), (0, 0, z1 + 0.09 * rs), (0.03, 0, z1 + 0.115 * rs), (0.05, 0, z1 + 0.09 * rs)], [0.008, 0.008, 0.008, 0.005], n=4), m.under))
        top = z1 + 0.03
    elif rstyle == "brim":          # a wide flat brim, like a watchman's hat
        items.append((turned([(R * 2.0 * rs, z1 - 0.005), (R * 2.04 * rs, z1 + 0.006), (R * 0.9, z1 + 0.03), (R * 0.7, z1 + 0.09), (R * 0.3, z1 + 0.12), (0.02, z1 + 0.125)], n=12), m.under, ROUND))
        top = z1 + 0.125
    elif rstyle == "pagoda":
        for i, (zz, rr) in enumerate(((z1, R * 1.5), (z1 + 0.075 * rs, R * 1.05))):
            items.append((turned([(rr, zz), (rr * 0.92, zz + 0.012), (rr * 0.42, zz + 0.07 * rs), (rr * 0.36, zz + 0.078 * rs)], n=n), m.under if i == 0 else m.main))
        items.append((turned([(R * 0.2, z1 + 0.15 * rs), (0.012, z1 + 0.2 * rs)], n=6), m.main))
        top = z1 + 0.2 * rs
    elif rstyle == "dome":
        prof = [(R * 1.2 * math.cos(t), z1 + R * 1.0 * rs * math.sin(t)) for t in (0.0, 0.4, 0.8, 1.2, 1.5)]
        items.append((turned(prof, n=12), m.under, ROUND))
        items.append((ball((0, 0, z1 + R * 1.0 * rs + 0.02), 0.026, sub=1), m.main, ROUND))
        top = z1 + R * 1.0 * rs + 0.045
    elif rstyle == "crown":         # a crown of small points round the top of the glass
        items.append((turned([(R * 1.2, z1), (R * 1.26, z1 + 0.02), (R * 0.9, z1 + 0.03)], n=12), m.main, ROUND))
        pts = None
        for k in range(8):
            a = 2 * math.pi * k / 8
            d = Vector((math.cos(a), math.sin(a), 0))
            pts = g.merge(pts, g.blade(d * R * 1.1 + Z * (z1 + 0.02), d * R * 1.3 + Z * (z1 + 0.14 * rs), 0.05, normal=d))
            items.append((ball(d * R * 1.32 + Z * (z1 + 0.155 * rs), 0.016 * rs, sub=0, scale=(1, 1, 1.5)), field("core", 4.2)))
        items.append((pts, m.main))
        top = z1 + 0.03
    elif rstyle == "battlement":    # a wall-walk: square teeth round the top
        items.append((turned([(R * 1.42, z1), (R * 1.42, z1 + 0.03), (R * 1.1, z1 + 0.03)], n=n), m.main))
        teeth = None
        cnt = n * 2
        for k in range(cnt):
            a = phase(n) + 2 * math.pi * (k + 0.5) / cnt
            teeth = g.merge(teeth, g.box((R * 1.3 * math.cos(a), R * 1.3 * math.sin(a), z1 + 0.055), (0.05, 0.03, 0.05), rot=(0, 0, a + math.pi / 2)))
        items.append((teeth, m.under))
        items.append((turned([(R * 1.0, z1 + 0.03), (R * 0.3, z1 + 0.07 * rs), (0.02, z1 + 0.08 * rs)], n=n), m.under))
        top = z1 + 0.08
    elif rstyle == "ball":
        prof = [(R * 1.22 * math.cos(t), z1 + R * 0.8 * rs * math.sin(t)) for t in (0.0, 0.5, 1.0, 1.4)]
        items.append((turned(prof, n=8), m.under))
        items.append((rod((0, 0, z1 + R * 0.75 * rs), (0, 0, z1 + R * 0.8 * rs + 0.06), 0.008), m.main))
        items.append((ball((0, 0, z1 + R * 0.8 * rs + 0.085), 0.034, sub=1), m.main, ROUND))
        top = z1 + R * 0.8 * rs + 0.12
    elif rstyle == "chimney":       # a stove-pipe it is proud of, with an elbow and a cowl
        pipe = [(0, R * 0.5, z1 - 0.01), (0, R * 0.5, z1 + 0.22 * rs), (0, R * 0.2, z1 + 0.3 * rs), (0, R * 0.2, z1 + 0.44 * rs)]
        items.append((g.tube(pipe, [0.036, 0.036, 0.034, 0.034], n=7), m.under, ROUND))
        items.append((turned([(0.07, 0.0), (0.012, 0.045)], n=7, centre=(0, R * 0.2, z1 + 0.46 * rs)), m.main, ROUND))
        for z in (z1 + 0.1 * rs, z1 + 0.38 * rs):
            items.append((hoop((0, R * 0.5 if z < z1 + 0.25 * rs else R * 0.2, z), 0.04, 0.007, n=8), m.trim))
        top = z1
    elif rstyle == "canopy":        # a small roof held over the flame on rods
        for k in range(3):
            a = math.pi / 2 + 2 * math.pi * k / 3
            d = Vector((math.cos(a), math.sin(a), 0))
            items.append((rod(d * R * 0.72 + Z * z1, d * R * 0.9 + Z * (z1 + 0.11 * rs), 0.007), m.under))
        items.append((turned([(R * 1.3, z1 + 0.1 * rs), (R * 1.0, z1 + 0.135 * rs), (R * 0.2, z1 + 0.19 * rs), (0.02, z1 + 0.2 * rs)], n=10), m.main, ROUND))
        top = z1 + 0.2 * rs
    elif rstyle == "spike":
        items.append((turned([(R * 1.16, z1), (R * 0.5, z1 + 0.05), (R * 0.14, z1 + 0.09), (0.004, z1 + 0.3 * rs)], n=6), m.under))
        top = z1 + 0.09
    elif rstyle == "rays":          # it stands up and shines: a sun of brass round its head
        items.append((turned([(R * 1.1, z1), (R * 0.7, z1 + 0.05), (R * 0.2, z1 + 0.09), (0.02, z1 + 0.1)], n=10), m.under, ROUND))
        rays = None
        for k in range(12):
            a = 2 * math.pi * k / 12
            d = Vector((math.cos(a), 0, math.sin(a)))
            L = (0.2 if k % 2 == 0 else 0.13) * rs
            rays = g.merge(rays, g.blade(Vector((0, R * 0.2, mid)) + d * (R * 1.5), Vector((0, R * 0.2, mid)) + d * (R * 1.5 + L), 0.05, normal=Y))
        items.append((rays, m.main))
        items.append((f2.band((0, R * 0.2, mid), R * 1.5, R * 1.5, 0.01, n=14, u=X, v=Z, sides=3), m.main))
        top = z1 + 0.1
    ring_at = Vector((0, 0, top + 0.036))
    if rstyle not in ("gauze", "chimney"):
        items.append((f2.band(ring_at, 0.036, 0.036, 0.008, n=10, u=X, v=Z, sides=4), m.main))
    else:
        ring_at = Vector((0.03, 0, top + 0.085)) if rstyle == "gauze" else Vector((0, R * 0.2, top + 0.47 * rs))
    base_front = Vector((0, -front, 0.035))
    if style == "cup":
        base_front = Vector((0, -R * 1.07, 0.228))
    elif style == "belly":
        base_front = Vector((0, -R * 1.2, 0.318))
    elif style == "globe":
        base_front = Vector((0, -R * 0.92, R * 0.36))
    anchors = {"top": Vector((0, 0, top)), "light": lit + Z * 0.06, "carry": ring_at, "base_front": base_front, "mid": Vector((0, -front, mid)),
               "R": R, "H": H, "z0": z0, "z1": z1, "lit": lit, "front": front}
    return put(items, TR(s=s)), {k: (v * s if isinstance(v, (Vector, float)) else v) for k, v in anchors.items()}


def _leg(hip, d, L, k, foot, reach=1.0, lift=0.1):
    """One jointed leg from its hip out along d down to the ground: [(geo, material role)...]"""
    knee = hip + d * (0.13 * reach) + Z * (lift * L)
    ankle = Vector((hip.x, hip.y, 0)) + d * (0.16 * reach) + Z * 0.055
    tip = Vector((ankle.x, ankle.y, 0.012)) + d * 0.006
    out = [(g.merge(g.tube([hip, knee], [0.02 * k, 0.016 * k], n=5), g.tube([knee, ankle], [0.016 * k, 0.011 * k], n=5)), "under"),
           (g.merge(ball(hip, 0.03 * k, sub=1), ball(knee, 0.027 * k, sub=1), ball(ankle, 0.018 * k, sub=0)), "main")]
    a = math.atan2(d.y, d.x)
    if foot == "claw":
        claws = None
        for da in (-0.9, 0.0, 0.9):
            cd = Vector((math.cos(a + da), math.sin(a + da), 0))
            claws = g.merge(claws, g.tube([ankle, tip + cd * 0.03, tip + cd * 0.06 - Z * 0.01], [0.012 * k, 0.009 * k, 0.002], n=4))
        out.append((claws, "trim"))
    elif foot == "flat":            # flat and wide: once set down it does not rock
        out.append((g.lathe([(0.0, 0.0), (0.085 * k, 0.0), (0.085 * k, 0.014), (0.03, 0.03), (0.0, 0.03)], n=8, centre=(ankle.x, ankle.y, 0.0)), "trim"))
    elif foot == "web":             # wide webbed feet
        web = None
        for da in (-0.7, 0.0, 0.7):
            cd = Vector((math.cos(a + da), math.sin(a + da), 0))
            web = g.merge(web, g.tube([ankle, tip + cd * 0.11 - Z * 0.008], [0.011, 0.004], n=4))
        fan = [tip + Vector((math.cos(a + da), math.sin(a + da), 0)) * 0.1 for da in (-0.7, -0.35, 0.0, 0.35, 0.7)]
        out.append((g.loft([[ankle + Z * 0.0] + fan, [ankle - Z * 0.008] + [p - Z * 0.008 for p in fan]]), "trim"))
        out.append((web, "under"))
    else:                           # a ball
        out.append((ball(Vector((ankle.x, ankle.y, 0.02)), 0.022 * k, sub=1), "trim"))
    return out


def lamp_stand(spec, m, R):
    """How it holds itself up. Returns (items, where the lamp sits: a placement, extras)."""
    b = spec.get("build", {})
    style, ss = gl.opt(spec.get("stand", "legs"))
    L, k = b.get("legs", 1.0) * ss, b.get("girth", 1.0)
    items, role = [], {"main": m.main, "under": m.under, "trim": m.trim}

    def legs(n, hip_z, foot="claw", reach=1.0, lift=0.1, turn=0.0, hip_r=None, stride=0.0):
        for i in range(n):
            a = math.radians(turn) + (math.radians(330 - 120 * i) if n == 3 else math.pi / 4 + i * math.pi / 2)
            d = Vector((math.cos(a), math.sin(a), 0))
            hip = d * (R * 0.8 if hip_r is None else hip_r) + Z * hip_z
            r_i = reach * (1.0 + (stride if d.y < 0 else -stride * 0.4))
            for geo, rl in _leg(hip, d, hip_z, k, foot, reach=r_i, lift=lift):
                items.append((geo, role[rl], ROUND))

    foot = spec.get("feet", "claw")
    if style in ("legs", "stride"):
        z = 0.34 * L
        legs(3, z, foot, stride=(0.5 if style == "stride" else 0.0))
        return items, TR((0, 0, z - 0.035)), {}
    if style == "four":
        z = 0.3 * L
        legs(4, z, foot, reach=0.9)
        return items, TR((0, 0, z - 0.035)), {}
    if style == "stilts":           # straight and thin
        z = 0.42 * L
        for i in range(3):
            a = math.radians(330 - 120 * i)
            d = Vector((math.cos(a), math.sin(a), 0))
            items.append((rod(d * R * 0.7 + Z * z, d * (R + 0.09) + Z * 0.0, 0.011 * k, r1=0.006 * k), m.under))
            items.append((ball(d * R * 0.7 + Z * z, 0.022 * k, sub=1), m.main))
        return items, TR((0, 0, z - 0.03)), {}
    if style == "crab":             # knees out and high, for where the roof is low
        z = 0.2 * L
        legs(4, z, foot, reach=1.6, lift=0.75)
        return items, TR((0, 0, z - 0.035)), {}
    if style == "fold":             # sat down on its legs, like a hen
        z = 0.1 * L
        legs(3, z, foot, reach=0.75, lift=1.1)
        return items, TR((0, 0, z - 0.03)), {}
    if style == "bow":              # short and bowed, under a weight
        z = 0.11 * L
        legs(4, z, foot if foot != "claw" else "ball", reach=0.7, lift=0.2, hip_r=R * 1.2)
        return items, TR((0, 0, z - 0.03)), {}
    if style == "arm":              # the lamp carried high on one long jointed arm
        legs(3, 0.2, foot, reach=0.9)
        items.append((turned([(0.07, 0.17), (0.08, 0.2), (0.05, 0.24)], n=8), m.main, ROUND))
        H = 0.62 * L
        p = [Vector((0, 0, 0.23)), Vector((0.13, 0.06, 0.23 + H * 0.5)), Vector((0.02, -0.02, 0.23 + H)), Vector((0.19, -0.08, 0.23 + H * 1.08))]
        items.append((g.tube(p, [0.018 * k, 0.015 * k, 0.013 * k, 0.012 * k], n=5), m.under))
        for q in p[1:3]:
            items.append((ball(q, 0.028 * k, sub=1), m.main))
        return items, TR(p[3] + Vector((0, 0, -0.01))), {"post_top": p[3]}
    if style == "neck":             # a weighted foot and a long neck that bends over a page
        items.append((turned([(0.0, 0.0), (0.15, 0.0), (0.16, 0.02), (0.13, 0.05), (0.05, 0.075), (0.0, 0.075)], n=10), m.main, ROUND))
        for i in range(3):
            a = math.radians(330 - 120 * i)
            items.append((ball((0.14 * math.cos(a), 0.14 * math.sin(a), 0.012), 0.022, sub=0), m.trim))
        H = 0.55 * L
        p = [Vector((0, 0.06, 0.07)), Vector((0, 0.12, 0.07 + H * 0.5)), Vector((0, 0.06, 0.07 + H * 0.95)), Vector((0, -0.1, 0.07 + H * 1.1)), Vector((0, -0.24, 0.07 + H * 0.98))]
        items.append((g.tube(p, [0.02 * k, 0.017 * k, 0.015 * k, 0.014 * k, 0.014 * k], n=6), m.under, ROUND))
        for q in p[1:4]:
            items.append((hoop(q, 0.022 * k, 0.006, n=6), m.main))
        # the lamp hangs from the neck's end, turned down toward the page
        return items, TR(p[4] + Vector((0, -0.012, -0.012)), rot=(-0.64, 0, 0)), {"post_top": p[3], "base": Vector((0, -0.05, 0.075)), "hang": True}
    if style == "post":             # a lamp on a post
        legs(3, 0.1, "flat" if foot == "claw" else foot, reach=0.7, lift=0.5, hip_r=0.04)
        H = 0.95 * L
        items.append((turned([(0.06, 0.05), (0.07, 0.09), (0.03, 0.14), (0.022, H * 0.5), (0.02, H), (0.04, H + 0.012)], n=7), m.under, ROUND))
        items.append((g.box((0, 0, H * 0.78), (0.2, 0.016, 0.016)), m.main))
        return items, TR((0, 0, H + 0.01)), {"post_top": Vector((0, 0, H))}
    if style == "mast":             # a signal mast
        legs(3, 0.12, "flat" if foot == "claw" else foot, reach=1.0, lift=0.4, hip_r=0.05)
        H = 0.9 * L
        items.append((turned([(0.05, 0.07), (0.035, 0.14), (0.022, H), (0.03, H + 0.012)], n=6), m.under, ROUND))
        items.append((turned([(0.0, 0.0), (0.12, 0.0), (0.12, 0.012), (0.0, 0.012)], n=8, centre=(0, 0, H * 0.62)), m.trim))
        for kx in range(4):
            a = math.pi / 4 + kx * math.pi / 2
            items.append((rod((0.11 * math.cos(a), 0.11 * math.sin(a), H * 0.62), (0.11 * math.cos(a), 0.11 * math.sin(a), H * 0.62 + 0.06), 0.005, n=3), m.trim))
        return items, TR((0, 0, H + 0.01)), {"post_top": Vector((0, 0, H))}
    if style == "stem":             # a foot, a knop and a column
        H = 0.34 * L
        items.append((turned([(0.0, 0.0), (0.13, 0.0), (0.14, 0.018), (0.05, 0.05), (0.028, 0.1), (0.045, 0.13), (0.028, 0.16), (0.024, H - 0.03), (0.05, H)], n=10), m.main, ROUND))
        for i in range(3):
            a = math.radians(330 - 120 * i)
            items.append((ball((0.125 * math.cos(a), 0.125 * math.sin(a), 0.012), 0.024, sub=0), m.trim))
        return items, TR((0, 0, H - 0.005)), {"stem": H}
    if style == "float":            # it rides the water that is not there
        z, fr = 0.34 * L, 0.21 * b.get("float", 1.0)
        items.append((turned([(0.0, z - fr * 0.95), (fr * 0.48, z - fr * 0.8), (fr, z - fr * 0.38), (fr, z - 0.02), (fr * 0.72, z + 0.02), (0.0, z + 0.02)], n=10), m.main, ROUND))
        items.append((turned([(fr + 0.003, z - fr * 0.33), (fr + 0.003, z - 0.03)], n=10, caps=False), kit.mark("band", m.under), ROUND))
        tower = 0.12 * b.get("tower", 1.0)
        for kx in range(4):
            a = math.pi / 4 + kx * math.pi / 2
            items.append((rod((fr * 0.7 * math.cos(a), fr * 0.7 * math.sin(a), z + 0.015), (R * 0.9 * math.cos(a), R * 0.9 * math.sin(a), z + tower), 0.011), m.under))
        if tower > 0.2:
            items.append((hoop((0, 0, z + tower * 0.5), (fr * 0.7 + R * 0.9) / 2, 0.007, n=8), m.under))
        return items, TR((0, 0, z + tower - 0.01)), {"float": z, "under": Vector((0, 0, z - fr * 0.95)), "fr": fr}
    if style == "keeper":           # it grew a keeper to carry it
        return items, TR(), {}
    return items, TR(), {}          # none: it has left its glass behind


def keeper(m, spec, s=1.0):
    """A small keeper in a long coat: [(geo, material)], and where its hands are. The coat
    is its partner's (the lamplighter's wool); its lamp is not in this."""
    coat, dark, leather = mat(m.coat.get("main", "cloth_wool")), mat(m.coat.get("under", "cloth_dark")), mat(m.coat.get("trim", "leather"))
    style, ks = gl.opt(spec.get("keeper", "plain"))
    h = 0.6 * ks
    items = [(turned([(0.0, 0.0), (0.2, 0.0), (0.19, 0.02), (0.13, h * 0.42), (0.1, h * 0.66), (0.085, h * 0.8), (0.0, h * 0.82)], n=10), coat, SOFT)]
    items.append((turned([(0.203, 0.0), (0.203, 0.03)], n=10, caps=False), dark, SOFT))
    items.append((hoop((0, 0, h * 0.5), 0.127, 0.012, n=10, sides=4), leather))
    head = Vector((0, -0.01, h * 0.93))
    items.append((ball(head, 0.085, sub=1, scale=(0.95, 1.0, 1.05)), mat("skin_keeper"), ROUND))
    # the hood: over the head and down the back
    hood = [(0.1 * math.cos(t), 0.11 * math.sin(t)) for t in (0.0, 0.5, 1.0, 1.4)]
    items.append((g.moved(turned(hood + [(0.012, 0.118)], n=8), TR(head + Vector((0, 0.022, -0.012)), rot=(0.35, 0, 0))), dark, SOFT))
    for sgn in (1, -1):
        items.append((ball(head + Vector((sgn * 0.034, -0.076, 0.008)), 0.013, sub=0), field("eyes", 3.2)))
    anchors = {"head": head + Z * 0.1, "hand_l": Vector((0.12, -0.2, h * 0.62)), "hand_r": Vector((-0.12, -0.2, h * 0.62)), "h": h}
    for sgn, key in ((1, "hand_l"), (-1, "hand_r")):
        sh = Vector((sgn * 0.09, -0.02, h * 0.74))
        if style in ("high", "veiled") and sgn == -1:   # it holds the lamp high, and a little behind
            anchors[key] = Vector((sgn * 0.14, 0.02, h * 1.08))
        if style == "both" and sgn == 1:
            anchors[key] = Vector((0.2, -0.1, h * 0.72))
        items.append((g.tube([sh, (sh + anchors[key]) / 2 + Vector((sgn * 0.02, 0, -0.03)), anchors[key]], [0.04, 0.034, 0.028], n=6), coat, SOFT))
        items.append((ball(anchors[key], 0.026, sub=0), mat("skin_keeper")))
    if style == "veiled":           # a veil over its face
        items.append((g.moved(turned([(0.0, 0.0), (0.07, -0.02), (0.085, -0.12), (0.08, -0.2)], n=6, caps=False), TR(head + Vector((0, -0.04, 0.07)), rot=(0.25, 0, 0))), mat("mist"), SOFT))
    return put(items, TR(s=s)), {kx: (v * s if isinstance(v, Vector) else v * s) for kx, v in anchors.items()}


def lamp_gear(spec, m, items, A, P, extra):
    """What it has been given to do its work with. A: the lamp's own anchors, placed (P);
    extra: what its stand gave it."""
    R, front = A["R"], A["front"]
    at = lambda p: P @ V(p)  # noqa: E731
    mid_l, base_l = A["mid"], A["base_front"]
    for style, s in gl.each(spec.get("carry")):
        if style == "ring":         # its light falls in a clean ring with an edge you could draw
            rr = 0.36 * s
            items.append((hoop((0, 0, 0.012), rr, 0.012, n=20, sides=3), field("ring", 2.6)))
            items.append((hoop((0, 0, 0.008), rr + 0.03, 0.008, n=20, sides=3), m.trim))
        elif style == "hoops":      # a ring of light that tightens and opens like breathing
            c = A["swing"] if "swing" in A else at(A["lit"] + Z * (A["H"] * 0.5))
            for i, (rr, tilt) in enumerate(((0.17, 0.25), (0.25, -0.2), (0.33, 0.12))):
                u = Matrix.Rotation(tilt, 3, "Y") @ X
                items.append((f2.band(c, rr * s, rr * s, 0.008, n=16, u=u, v=Y, sides=3), field("ring", 2.4) if i != 1 else m.main))
        elif style == "lens-arm":   # a lens that swings out on an arm when something interests it
            for i, (sgn, rr, out) in enumerate(((1, 0.07, 0.3), (-1, 0.045, 0.2))[: (2 if s > 1.1 else 1)]):
                a0 = at(Vector((sgn * R * 0.9, 0, A["z1"] - 0.02)))
                a1 = a0 + Vector((sgn * 0.12, -0.02, 0.1))
                a2 = at(Vector((sgn * 0.04, -front - out * s, mid_l.z + 0.02)))
                items.append((g.tube([a0, a1, a2], [0.012, 0.01, 0.008], n=4), m.under))
                items.append((ball(a1, 0.02, sub=0), m.main))
                items += lens(a2, rr * s, m, glow="eyes", strength=2.2, deep=0.3)
        elif style == "scale":      # it knows at a glance what is worth keeping
            a0 = at(Vector((-R * 0.9, 0, A["z1"] - 0.03)))
            a1 = a0 + Vector((-0.2 * s, -0.04, 0.03))
            items.append((rod(a0, a1, 0.009), m.under))
            for dx, dy in ((0.05, 0), (-0.05, 0), (0, 0.05)):
                items.append((rod(a1, a1 + Vector((dx, dy, -0.17 * s)), 0.003, n=3), m.trim))
            items.append((turned([(0.0, 0.0), (0.075, 0.012), (0.08, 0.02), (0.0, 0.012)], n=8, centre=a1 + Vector((0, 0, -0.19 * s))), m.main, ROUND))
            items.append((ball(a1 + Vector((0, 0, -0.165 * s)), 0.024, sub=0), field("find", 2.4)))
        elif style == "reflector":  # a mirror behind the flame
            c = at(A["lit"] + Vector((0, R * 0.9, A["H"] * 0.5)))
            prof = [(0.0, 0.0), (R * 1.1 * s, -0.03 * s), (R * 1.9 * s, -0.12 * s), (R * 2.0 * s, -0.12 * s), (R * 1.2 * s, -0.022 * s), (0.0, 0.012)]
            items.append((g.moved(g.lathe(prof, n=12), TR(c, rot=(-math.pi / 2, 0, 0))), m.main, ROUND))
        elif style == "rods":       # two rods of carbon that meet at the flame
            c = at(A["lit"] + Z * (A["H"] * 0.45))
            for sgn in (1, -1):
                items.append((rod(c + Vector((sgn * 0.035, 0, 0)), c + Vector((sgn * (R + 0.1) * s, 0, -0.1)), 0.011), mat("soot")))
                items.append((ball(c + Vector((sgn * (R + 0.1) * s, 0, -0.1)), 0.022, sub=0), m.main))
        elif style == "cloak":      # a hood and a half-cape, so that its light is its own business
            top = at(A["top"])
            pts = []
            for i in range(6):
                a = math.radians(20 + 32 * i)
                pts.append((math.cos(a), math.sin(a)))
            rings = []
            Rc = max(R, 0.1)
            for zf, rr in ((0.03, Rc * 0.6), (-0.1, Rc * 1.5), (-0.36 * s, Rc * 2.0), (-0.66 * s, Rc * 2.5)):
                rings.append([top + Vector((px * rr, py * rr * 1.0 + Rc * 0.2, zf)) for px, py in pts])
            cape = g.loft(rings, caps=False, closed=False)
            inner = g.loft([[p * 0.985 + top * 0.015 + Vector((0, -0.006, 0)) for p in ring] for ring in reversed(rings)], caps=False, closed=False)
            items.append((g.merge(cape, inner), mat("cloth_red"), SOFT))
            items.append((ball(top + Vector((max(R, 0.1) * 0.6, max(R, 0.1) * 0.2, 0.02)), 0.022, sub=0), m.main))
        elif style == "rag":        # there is a rag tucked under one foot
            items.append((g.tongue([(0.2, -0.16, 0.012), (0.27, -0.2, 0.03), (0.33, -0.2, 0.012)], [0.07, 0.09, 0.05], thick=0.3, normal=Z), mat("cloth_rag"), SOFT))
        elif style == "mirror":     # a plain bright disc behind it: nothing false keeps its shape
            c = at(Vector((0, R * 1.5, A["z0"] + A["H"] * 0.62)))
            items.append((disc(c, 0.21 * s, 0.014, n=14), mat("tin"), ROUND))
            items.append((f2.band(c, 0.215 * s, 0.215 * s, 0.012, n=14, u=X, v=Z, sides=4), m.main))
            items.append((rod(c + Vector((0, 0.01, -0.2 * s)), at(Vector((0, R * 0.9, 0.02))), 0.01), m.under))
        elif style == "scroll":     # what was sworn, wound round the stem
            h0 = extra.get("stem", 0.3)
            pts = g.spiral((0, 0, h0 * 0.42), 0.05, 0.05, 2.2, h0 * 0.5, n=14, axis=Z)
            items.append((g.tongue(pts, [0.05] * len(pts), thick=0.12, normal=Z), mat("paper"), SOFT))
            items.append((g.tongue([pts[0], pts[0] + Vector((0.08, -0.05, -0.05)), pts[0] + Vector((0.1, -0.08, -0.12))], [0.05, 0.05, 0.04], thick=0.12, normal=Y), mat("paper"), SOFT))
        elif style == "seals":      # seals on their ribbons
            c = extra["base"] + Vector((0, -0.11, 0.0)) if "base" in extra else at(A["base_front"])
            for i, dx in enumerate((-0.08, 0.0, 0.08)[: max(1, int(round(2 * s)))]):
                p = c + Vector((dx, -0.02, 0.0))
                items.append((g.tongue([p, p + Vector((0, -0.01, -0.07)), p + Vector((dx * 0.2, -0.012, -0.13))], [0.022, 0.022, 0.02], thick=0.2, normal=Y), mat("ribbon"), SOFT))
                items.append((disc(p + Vector((dx * 0.2, -0.016, -0.15)), 0.03, 0.012, n=8), mat("wax_red"), ROUND))
        elif style == "pilot":      # the spark it was handed, kept apart in a cup of its own
            c = at(Vector((R * 1.35, -R * 0.3, A["z0"] - 0.03)))
            items.append((turned([(0.0, 0.0), (0.03, 0.01), (0.04, 0.04), (0.03, 0.04)], n=6, centre=c), m.main, ROUND))
            items.append((rod(c, at(Vector((R * 0.8, 0, A["z0"] - 0.05))), 0.007), m.under))
            items += flame("low", c + Z * 0.03, 0.8)
        elif style == "book":       # the paper it is reading, and the ledger it keeps
            c = extra.get("base", Vector((0, -0.1, 0.07)))
            items.append((g.box(c + Vector((0, -0.14, 0.012)), (0.3 * s, 0.2 * s, 0.024), rot=(0.0, 0, 0.12)), mat("leather_dark")))
            items.append((g.box(c + Vector((0, -0.14, 0.03)), (0.27 * s, 0.18 * s, 0.014), rot=(0.0, 0, 0.12)), mat("paper")))
        elif style == "shade":      # a shade it tilts to stop the glare
            c = at(A["top"] + Z * -0.02)
            prof = [(R * 2.1 * s, -0.11 * s), (R * 2.16 * s, -0.1 * s), (R * 0.9, 0.0), (R * 0.5, 0.012)]
            items.append((g.moved(g.lathe(prof, n=10), TR(c) @ P.to_3x3().to_4x4()), mat("enamel_green"), ROUND))
        elif style == "wide-shade":  # one long flat shade over a long flat light
            c = at(A["top"])
            items.append((g.moved(g.box((0, 0, 0), (0.52 * s, 0.2, 0.016)), TR(c) @ P.to_3x3().to_4x4()), mat("enamel_green")))
            for sgn in (1, -1):
                items.append((g.moved(g.box((sgn * 0.26 * s, 0, -0.045), (0.016, 0.2, 0.09)), TR(c) @ P.to_3x3().to_4x4()), mat("enamel_green")))
            items += put(flame("flat", (0, 0, -0.03), 1.3 * s), TR(c) @ P.to_3x3().to_4x4())
        elif style == "kettle":     # it keeps one warm for whoever comes in
            c = at(A["top"] + Vector((0, -R * 0.5, -0.012)))
            items.append((turned([(0.03, 0.0), (0.06, 0.012), (0.066, 0.04), (0.04, 0.06), (0.012, 0.066)], n=8, centre=c), m.trim, ROUND))
            items.append((g.tube([c + Vector((0, -0.06, 0.03)), c + Vector((0, -0.1, 0.05)), c + Vector((0, -0.115, 0.075))], [0.012, 0.009, 0.006], n=4), m.trim))
            items.append((f2.band(c + Z * 0.075, 0.04, 0.03, 0.005, n=8, u=X, v=Z, sides=3), m.under))
        elif style == "door":       # a little door, with the fire seen through its bars
            c = at(Vector((0, -front + 0.01, A["z0"] + A["H"] * 0.5)))
            items.append((g.box(c + Vector((0, -0.006, 0)), (R * 1.25, 0.014, A["H"] * 1.15)), kit.mark("enamel", m.under)))
            items.append((g.box(c + Vector((0, -0.015, 0.012)), (R * 0.95, 0.008, A["H"] * 0.6)), field("ember", 2.8), FLAT))
            for dx in (-0.3, 0.0, 0.3):
                items.append((rod(c + Vector((dx * R, -0.022, -A["H"] * 0.3)), c + Vector((dx * R, -0.022, A["H"] * 0.33)), 0.007, n=3), m.under))
            items.append((ball(c + Vector((R * 0.52, -0.02, -A["H"] * 0.42)), 0.016, sub=0), m.trim))
        elif style == "gallery":    # a rail to walk round the glass
            z = P.translation.z + 0.045
            rr = R * 1.5
            items.append((hoop((0, 0, z + 0.06), rr, 0.006, n=16), m.under))
            for kx in range(8):
                a = 2 * math.pi * kx / 8
                items.append((rod((rr * math.cos(a), rr * math.sin(a), z), (rr * math.cos(a), rr * math.sin(a), z + 0.06), 0.005, n=3), m.under))
            items.append((turned([(R * 1.1, z - 0.012), (rr + 0.02, z - 0.012), (rr + 0.02, z), (R * 1.1, z)], n=8), m.trim))
        elif style == "semaphore":  # an arm it can raise against things with teeth
            top = extra.get("post_top", at(A["top"]))
            c = Vector((0.03, 0, top.z * 0.83))
            items.append((g.box(c + Vector((0.16 * s, 0, 0.05)), (0.3 * s, 0.014, 0.07), rot=(0, -0.45, 0)), mat("enamel_red")))
            items.append((g.box(c + Vector((0.29 * s, 0, 0.11)), (0.05, 0.016, 0.075), rot=(0, -0.45, 0)), mat("dial_face")))
            items.append((ball(c, 0.03, sub=0), m.main))
        elif style == "halo":       # a ring round the lamp, where the post's own light would be
            c = at(A["lit"] + Z * (A["H"] * 0.5))
            items.append((f2.band(c, R * 2.0 * s, R * 2.0 * s, 0.012, n=16, u=X, v=Z, sides=3), field("ring", 2.4)))
            for a in (0.6, 2.54):
                items.append((rod(c + Vector((math.cos(a) * R, 0, math.sin(a) * R)), c + Vector((math.cos(a) * R * 2.0 * s, 0, math.sin(a) * R * 2.0 * s)), 0.006, n=3), m.under))
        elif style == "chain":      # a chain under it, and weed on the chain
            u = extra.get("under", Vector((0, 0, 0.1)))
            end = u + Vector((0.05, 0.03, -0.42 * s))
            items.append((chain(u, end, size=0.026), m.under))
            items.append((ball(end + Z * -0.03, 0.04, sub=0), m.under))
            weed = None
            for i in range(5):
                p = u.lerp(end, 0.2 + 0.18 * i)
                weed = g.merge(weed, g.tongue([p, p + Vector((0.05 * math.sin(i * 2.0), 0.04 * math.cos(i * 2.0), -0.06)), p + Vector((0.07 * math.sin(i * 2.0 + 0.5), 0.07 * math.cos(i * 2.0), -0.15))], [0.03, 0.036, 0.01], thick=0.3))
            items.append((weed, mat("weed"), SOFT))
        elif style == "paddles":    # wide webbed feet under the float, one put out to try the ground
            z = extra.get("float", 0.3)
            for sgn, fwd in ((1, -0.16), (-1, 0.04)):
                hip = Vector((sgn * 0.09, -0.02, z - 0.16))
                for geo, rl in _leg(hip + Vector((0, fwd, 0)), Vector((sgn * 0.3, -1 if fwd < 0 else -0.2, 0)).normalized(), 0.2, 0.9, "web", reach=0.8 if fwd < 0 else 0.4, lift=0.1):
                    items.append((geo, {"main": m.main, "under": m.under, "trim": m.trim}[rl], ROUND))
        elif style == "reeds":
            z = extra.get("float", 0.3)
            reeds = None
            for i in range(5):
                a = 2.2 + 0.5 * i
                p = Vector((0.2 * math.cos(a), 0.2 * math.sin(a), z - 0.03))
                reeds = g.merge(reeds, g.blade(p, p + Vector((0.03 * math.cos(a), 0.03 * math.sin(a), 0.2 + 0.05 * (i % 3))), 0.03, normal=Vector((math.cos(a), math.sin(a), 0))))
            items.append((reeds, mat("reed"), SOFT))
        elif style == "pendulum":   # it keeps the time: an arm that swings, the flame at its end
            c = at(Vector((0, -front * 0.5, 0.06)))
            tip = c + Vector((0.2 * s, -0.02, 0.5 * s))
            items.append((rod(c, tip, 0.008), m.under))
            items.append((g.box(c.lerp(tip, 0.45), (0.05, 0.03, 0.06), rot=(0, -0.38, 0)), m.main))
            items += flame("heart", tip - Z * 0.03, 0.9)
            A["swing"] = tip
        elif style == "clock":      # the hours of the night on its font
            c = at(A["base_front"] + Vector((0, -0.006, 0.02)))
            items.append((disc(c, 0.06 * s, 0.01, n=12), mat("enamel_night"), ROUND))
            items.append((g.blade(c + Vector((0, -0.008, 0)), c + Vector((0.03, -0.008, 0.035)), 0.012, normal=(0, -1, 0)), m.main))
            items.append((ball(c + Vector((-0.02, -0.008, 0.02)), 0.014, sub=0, scale=(1, 0.4, 1)), mat("dial_face")))
        elif style == "taper":      # a taper, already lit
            hand = extra.get("hand_l", Vector((0.12, -0.2, 0.4)))
            tip = hand + Vector((0.1, -0.12, 0.62 * s))
            items.append((rod(hand + Vector((-0.02, 0.03, -0.12)), tip, 0.008), mat("wood")))
            items += flame("candle", tip, 0.55, lean=0.2)
        elif style == "yoke":       # the lights it has lit from its own, carried on a pole
            sh = extra.get("head", Vector((0, 0, 0.6))) + Vector((0, 0.06, -0.14))
            a, b2 = sh + Vector((0.36 * s, 0.02, 0.04)), sh + Vector((-0.36 * s, 0.02, 0.04))
            items.append((g.tube([a, sh + Z * 0.02, b2], [0.01, 0.012, 0.01], n=4), mat("wood")))
            for i, t in enumerate((0.0, 0.3, 0.7, 1.0)):
                p = a.lerp(b2, t)
                drop = 0.12 + 0.05 * (i % 2)
                items.append((rod(p, p - Z * drop, 0.003, n=3), m.trim))
                items += put(small_lamp(m, lit=True), TR(p - Z * (drop + 0.1), s=0.55))


def small_lamp(m, lit=True):
    """A little square lamp, hanging from the origin."""
    items = [(turned([(0.06, -0.012), (0.075, 0.0), (0.02, 0.05), (0.008, 0.06)], n=4, centre=(0, 0, 0.1)), m.under),
             (turned([(0.04, 0.0), (0.07, 0.012), (0.06, 0.03)], n=4), m.main)]
    for kx in range(4):
        a = math.pi / 4 + kx * math.pi / 2
        items.append((rod((0.055 * math.cos(a), 0.055 * math.sin(a), 0.03), (0.055 * math.cos(a), 0.055 * math.sin(a), 0.09), 0.006, n=3), m.main))
    if lit:
        items.append((ball((0, 0, 0.06), 0.026, sub=0, scale=(1, 1, 1.3)), field("core", 4.0)))
    return items


def build_lantern(form_id, level, spec, base, silhouette):
    m = Metals(silhouette)
    b = spec.get("build", {})
    stand_style = gl.opt(spec.get("stand", "legs"))[0]
    if stand_style == "none":       # no lamp at all any more: a few small lights
        return build_wisps(form_id, spec, m)
    head, A = lamp_head(spec, m, s=b.get("head", 1.0))
    R = A["R"]
    items, P, extra = lamp_stand(spec, m, R)
    if stand_style == "keeper":
        fig, K = keeper(m, spec, s=b.get("keeper", 1.0))
        items += fig
        extra.update(K)
        kstyle = gl.opt(spec.get("keeper", "plain"))[0]
        hand = K["hand_r"]
        # the lamp hangs from a crook the keeper holds out, like something owed
        pole_top = hand + (Vector((0.02, -0.16, 0.22)) if kstyle not in ("high", "veiled") else Vector((0.02, 0.0, 0.5)))
        items.append((g.tube([hand + Vector((0, 0.05, -0.2)), hand, pole_top, pole_top + Vector((0, -0.07, 0.03)), pole_top + Vector((0, -0.1, -0.02))], [0.009] * 5, n=4), mat("wood")))
        P = TR(pole_top + Vector((0, -0.1, -0.03)))
        extra["post_top"] = pole_top
        extra["hang"] = True
    if extra.get("hang"):       # it hangs by its ring
        P = P @ TR((0, 0, -A["carry"].z))
    lean = b.get("lean", 0.0)
    if lean:
        P = P @ Matrix.Rotation(lean, 4, "X")
    items += put(head, P)
    at = lambda p: P @ V(p)  # noqa: E731
    # the flame
    fstyle, fs = gl.opt(spec.get("flame", "heart"))
    if fstyle not in ("none", "gem") and "pendulum" not in [c for c, _ in gl.each(spec.get("carry"))] and "wide-shade" not in [c for c, _ in gl.each(spec.get("carry"))]:
        items += put(flame(fstyle, A["lit"], fs, lean=b.get("curious", 0.0)), P)
    # where it is alive
    face_style, fsz = gl.opt(spec.get("face", "eye"))
    face_at = at(A["base_front"])
    if stand_style == "keeper":
        face_at = Vector((0, -0.09, extra["head"].z - 0.1))
    elif face_style in ("eye", "lids"):
        r_eye = 0.034 * fsz
        c = at(A["base_front"] + Vector((0, -0.004, 0.0)))
        if A["base_front"].z < r_eye * 1.2:
            c.z = P.translation.z + r_eye * 1.3
        items += eye(c, r_eye, m, facing=(P.to_3x3() @ Vector((0, -1, 0))), heavy=(face_style == "lids"))
        face_at = c
    elif face_style == "gauge":
        c = at(A["base_front"] + Vector((0, -0.006, 0.0)))
        items.append((f2.band(c, 0.03, 0.03, 0.006, n=10, u=X, v=Z, sides=4), m.main))
        items.append((ball(c + Vector((0, 0.004, 0)), 0.026, sub=1, scale=(1, 0.25, 1)), m.trim))
        items.append((g.blade(c + Vector((0, -0.006, -0.004)), c + Vector((0.014, -0.006, 0.022)), 0.008, normal=(0, -1, 0)), field("needle", 3.0)))
        face_at = c
    elif face_style == "lens":
        face_at = at(A["mid"])
    lamp_gear(spec, m, items, A, P, extra)
    top = at(A["top"])
    ref = max(top.z, extra.get("post_top", top).z if stand_style in ("post", "mast", "arm", "neck") else top.z)
    if stand_style == "keeper":
        ref = extra["head"].z
    anchors = {"top": Vector((0, 0, ref)), "face": face_at, "light": at(A["light"]), "carry": at(A["carry"]), "back": Vector((0, R + 0.02, face_at.z))}
    if stand_style == "keeper":
        anchors["carry"] = extra["post_top"]
    return finish(form_id, items, anchors, ref=ref)


def build_wisps(form_id, spec, m):
    """No lamp at all any more: a few small lights that keep changing which is the real one."""
    dark, edge = mat(m.coat.get("main", "coal")), mat(m.coat.get("under", "shade_edge"))
    items = []
    spots = [(0.0, -0.05, 0.42, 1.0), (0.2, 0.06, 0.6, 0.7), (-0.22, 0.0, 0.3, 0.8), (0.1, 0.16, 0.2, 0.55), (-0.1, 0.12, 0.72, 0.6), (0.26, -0.1, 0.25, 0.45)]
    for i, (x, y, z, s) in enumerate(spots):
        c = Vector((x, y, z))
        items.append((g.lathe([(0.0, -0.05 * s), (0.045 * s, 0.0), (0.03 * s, 0.07 * s), (0.0, 0.13 * s)], n=6, centre=c), field("core", 4.4 if i == 0 else 3.0), ROUND))
        tail = [c + Vector((0, 0.02, -0.04 * s)), c + Vector((0.03 * math.sin(i * 2.0), 0.08 * s, -0.12 * s)), c + Vector((-0.02, 0.16 * s, -0.2 * s)), c + Vector((0.01, 0.2 * s, -0.3 * s))]
        items.append((g.tongue(tail, [0.07 * s, 0.06 * s, 0.035 * s, 0.006], thick=0.5, normal=Y), dark if i % 2 else edge, SOFT))
    # all that is left of the lamp: the ring it was carried by, hanging in the air
    ring_at = Vector((0, -0.05, 0.62))
    items.append((f2.band(ring_at, 0.045, 0.045, 0.009, n=10, u=X, v=Z, sides=4), mat("metal_brass")))
    items.append((g.tongue([ring_at - Z * 0.04, ring_at + Vector((0.01, 0.03, -0.12)), ring_at + Vector((0, 0.05, -0.17))], [0.03, 0.022, 0.004], thick=0.5, normal=Y), edge, SOFT))
    anchors = {"top": Vector((0, 0, 0.78)), "face": Vector((0, -0.1, 0.44)), "light": Vector((0, -0.05, 0.44)), "carry": ring_at + Z * 0.045}
    return finish(form_id, items, anchors, ref=0.78)


# ======================================================================================
# The Astrolabe
# ======================================================================================

def annulus(c, r0, r1, t, n=14, facing=Y):
    """A flat ring plate about c, its faces looking along `facing`."""
    geo = g.lathe([(r0, -t / 2), (r1, -t / 2), (r1, t / 2), (r0, t / 2), (r0, -t / 2)], n=n, phase=phase(n), caps=False)
    f = V(facing).normalized()
    Rm = Matrix.Identity(4) if abs(f.dot(Z)) > 0.999 else Z.rotation_difference(f).to_matrix().to_4x4()
    return g.moved(geo, Matrix.Translation(V(c)) @ Rm)


def loop_tube(pts, r, sides=4):
    pts = [V(p) for p in pts]
    return g.tube(pts + [pts[0]], [r] * (len(pts) + 1), n=sides, caps=False)


def flat_bar(a, b, w, t, normal=Y):
    """A flat bar from a to b, w wide, t thick through `normal`."""
    a, b = V(a), V(b)
    d = (b - a)
    n = V(normal).normalized()
    side = d.cross(n).normalized() * (w / 2)
    n = n * (t / 2)
    ring = lambda p: [p + side + n, p - side + n, p - side - n, p + side - n]  # noqa: E731
    return g.loft([ring(a), ring(b)])


def gear(c, r, teeth=10, t=0.014, facing=Y):
    geo = g.lathe([(r * 0.3, -t / 2), (r, -t / 2), (r, t / 2), (r * 0.3, t / 2), (r * 0.3, -t / 2)], n=teeth, caps=False)
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        geo = g.merge(geo, g.box((r * 1.08 * math.cos(a), r * 1.08 * math.sin(a), 0), (r * 0.24, r * 0.2, t), rot=(0, 0, a)))
    f = V(facing).normalized()
    Rm = Matrix.Identity(4) if abs(f.dot(Z)) > 0.999 else Z.rotation_difference(f).to_matrix().to_4x4()
    return g.moved(geo, Matrix.Translation(V(c)) @ Rm)


def astro_plate(spec, m):
    """The instrument's own body, about its pin. Returns (items, A): A says where its pin
    is (c), how big it is (R), where its face and its top are."""
    b = spec.get("build", {})
    style, ps = gl.opt(spec.get("plate", "disc"))
    R = 0.2 * ps * b.get("r", 1.0)
    c = Vector((0, 0, 0.6))
    it = []
    A = {"c": c, "R": R, "style": style, "eye": c + Vector((0, -0.022, 0)), "eye_r": R * 0.2, "top": c + Z * R, "facing": Vector((0, -1, 0)), "front": -0.02, "low": c - Z * R}
    enamel = kit.mark("enamel", m.trim)
    if style == "disc":
        it.append((disc(c, R, 0.03, n=16), m.main, ROUND))
        it.append((f2.band(c, R, R, 0.017, n=16, u=X, v=Z, sides=4), m.main))
        it.append((annulus(c + Y * -0.017, R * 0.74, R * 0.93, 0.006, n=16), enamel, ROUND))
        it.append((f2.band(c + Y * 0.02, R * 0.6, R * 0.6, 0.006, n=14, u=X, v=Z, sides=3), field("seam", 1.6)))
    elif style == "sector":         # a frame like a slice of a circle, its scale along the rim
        p = c + Z * R * 0.95
        L = R * 2.05
        ang = math.radians(33)
        ends = [p + Vector((math.sin(s * ang), 0, -math.cos(s * ang))) * L for s in (-1, 1)]
        for e in ends:
            it.append((flat_bar(p, e, 0.03, 0.016), m.main))
        for rr, w in ((L, 0.036), (L * 0.84, 0.016)):
            arc = [p + Vector((math.sin(a), 0, -math.cos(a))) * rr for a in [math.radians(-33 + 66 * i / 8) for i in range(9)]]
            for a0, a1 in zip(arc, arc[1:]):
                it.append((flat_bar(a0, a1, w, 0.014), m.main if rr == L else m.under))
        it.append((flat_bar(p + Vector((-math.sin(ang), 0, -math.cos(ang))) * L * 0.5, p + Vector((math.sin(ang), 0, -math.cos(ang))) * L * 0.5, 0.02, 0.012), m.under))
        ticks = None
        for i in range(13):
            a = math.radians(-31 + 62 * i / 12)
            d = Vector((math.sin(a), 0, -math.cos(a)))
            ticks = g.merge(ticks, flat_bar(p + d * L * 0.86 + Y * -0.012, p + d * L * (0.97 if i % 3 == 0 else 0.92) + Y * -0.012, 0.008, 0.006))
        it.append((ticks, m.trim))
        it.append((disc(p, R * 0.3, 0.036, n=10), m.main, ROUND))
        it.append((g.tube([p + Vector((0, 0.02, -L * 0.3)), p + Vector((0, 0.09, -L * 0.42)), p + Vector((0, 0.09, -L * 0.62)), p + Vector((0, 0.02, -L * 0.74))], [0.016] * 4, n=5), mat("wood"), ROUND))
        A.update({"eye": p + Vector((0, -0.024, 0)), "eye_r": R * 0.2, "top": p + Z * R * 0.3, "pivot": p, "L": L, "low": p - Z * L, "c": p - Z * L * 0.5})
    elif style == "rings":          # open rings and wires to look through
        it.append((f2.band(c, R, R, 0.016, n=18, u=X, v=Z, sides=4), m.main))
        for a in (0, math.pi / 2):
            d = Vector((math.cos(a), 0, math.sin(a)))
            it.append((rod(c - d * R, c + d * R, 0.005, n=3), m.trim))
        lead = c + Vector((R * 0.3, -0.07, R * 0.22))
        it.append((f2.band(lead, R * 0.48, R * 0.48, 0.011, n=14, u=X, v=Z, sides=4), m.under))
        for a in (0.9, 2.6, 4.4):
            d = Vector((math.cos(a), 0, math.sin(a)))
            it.append((rod(lead + d * R * 0.48, c + d * R * 0.98, 0.005, n=3), m.under))
        it.append((disc(c, R * 0.27, 0.03, n=10), m.main, ROUND))
        A.update({"eye_r": R * 0.17, "lead": lead})
    elif style == "sphere":         # rings turn round it; this is what they turn round
        rb = R * 0.34
        it.append((ball(c, rb, sub=2), m.main, ROUND))
        ax = Vector((math.sin(0.4), 0, math.cos(0.4)))
        it.append((rod(c - ax * R * 1.08, c + ax * R * 1.08, 0.007), m.under))
        for s in (1, -1):
            it.append((ball(c + ax * R * 1.08 * s, 0.016, sub=0), m.main))
        A.update({"eye": c + Vector((0, -rb * 0.96, 0)), "eye_r": rb * 0.55, "top": c + Z * R * 1.02})
    elif style == "globe":          # a whole sphere, one face of it dark
        rg = R * 0.86
        it.append((ball(c, rg, sub=2), m.main, ROUND))
        cap = g.lathe([(rg * 1.012 * math.sin(t), rg * 1.012 * math.cos(t)) for t in (0.0, 0.3, 0.6, 0.9, 1.15)], n=12)
        it.append((g.moved(cap, TR(c, rot=(math.pi / 2, 0, 0))), mat("enamel_night"), ROUND))
        A.update({"eye": c + Vector((0, -rg * 1.0, 0)), "eye_r": rg * 0.3, "top": c + Z * rg})
    elif style == "shield":         # a broad dial, twelve marks round it
        it.append((disc(c, R, 0.06, n=12), m.main, ROUND))
        it.append((f2.band(c + Y * -0.02, R, R, 0.026, n=12, u=X, v=Z, sides=4), m.under))
        boss = None
        for i in range(12):
            a = 2 * math.pi * i / 12
            boss = g.merge(boss, ball(c + Vector((R * 0.8 * math.cos(a), -0.034, R * 0.8 * math.sin(a))), R * 0.085 * (1.5 if i % 3 == 0 else 1.0), sub=0))
        it.append((boss, m.under))
        dome = g.lathe([(R * 0.36, 0.0), (R * 0.3, 0.02), (R * 0.16, 0.036), (0.0, 0.04)], n=10)
        it.append((g.moved(dome, TR(c + Y * -0.03, rot=(math.pi / 2, 0, 0))), m.main, ROUND))
        A.update({"eye": c + Vector((0, -0.066, 0)), "eye_r": R * 0.2, "front": -0.035})
    elif style == "wave":           # a line round its edge that is never in the same place twice
        it.append((disc(c, R * 0.9, 0.03, n=16), m.main, ROUND))
        wave = [c + Vector((math.cos(a), 0, math.sin(a))) * (R * (1.0 + 0.085 * math.sin(7 * a))) for a in [2 * math.pi * i / 42 for i in range(42)]]
        it.append((loop_tube(wave, 0.017, sides=4), mat("enamel_blue")))
        wave2 = [c + Y * -0.018 + Vector((math.cos(a), 0, math.sin(a))) * (R * (0.74 + 0.05 * math.sin(7 * a + 1.3))) for a in [2 * math.pi * i / 42 for i in range(42)]]
        it.append((loop_tube(wave2, 0.006, sides=3), field("seam", 2.0)))
    elif style == "eclipse":        # one disc stands exactly in front of another
        it.append((disc(c + Y * 0.02, R, 0.024, n=16), m.main, ROUND))
        rays = None
        for i in range(16):
            a = 2 * math.pi * i / 16
            d = Vector((math.cos(a), 0, math.sin(a)))
            rays = g.merge(rays, g.blade(c + Y * 0.02 + d * R * 0.96, c + Y * 0.02 + d * R * (1.42 if i % 2 == 0 else 1.2), R * 0.2, normal=Y))
        it.append((rays, field("corona", 2.4)))
        dark = c + Vector((R * 0.13, -0.022, R * 0.05))
        it.append((disc(dark, R * 0.93, 0.03, n=16), mat("soot"), ROUND))
        A.update({"eye": dark + Vector((0, -0.02, 0)), "eye_r": R * 0.15, "top": c + Z * R * 1.0})
    elif style == "book":           # thin plates that turn like pages, fanned
        piv = c - Z * R * 0.95
        rp = R * 0.72
        for i, deg in enumerate((-50, 50, -25, 25, 0)):
            a = math.radians(deg)
            cc = piv + Vector((math.sin(a), 0, math.cos(a))) * R * 1.0 + Y * (0.03 - 0.014 * i)
            it.append((disc(cc, rp, 0.011, n=14), m.main if i % 2 == 0 else m.under, ROUND))
            scr = None
            for k in range(3):
                d = Vector((math.cos(a + 0.5 * k), 0, -math.sin(a + 0.5 * k)))
                scr = g.merge(scr, flat_bar(cc + Y * -0.008 - d * rp * 0.6, cc + Y * -0.008 + d * rp * 0.6, 0.006, 0.004))
            it.append((scr, m.trim))
        it.append((ball(piv + Y * -0.01, R * 0.16, sub=1), m.under, ROUND))
        top = piv + Z * R * 1.0 + Y * -0.026
        A.update({"c": top, "eye": top + Vector((0, -0.01, 0)), "eye_r": R * 0.22, "top": piv + Z * (R * 1.0 + rp), "low": piv - Z * R * 0.16, "pivot": piv})
    elif style == "strip":          # a long folded strip of plates, notched
        head = c + Z * R * 1.2
        it.append((disc(head, R * 0.62, 0.026, n=12), m.main, ROUND))
        it.append((f2.band(head, R * 0.62, R * 0.62, 0.014, n=12, u=X, v=Z, sides=4), m.under))
        w, h = R * 1.25, R * 0.62
        z = head.z - R * 0.62
        notch = None
        for i in range(7):
            s = 1 if i % 2 == 0 else -1
            top_p, bot_p = Vector((0, -s * 0.045, z)), Vector((0, s * 0.045, z - h))
            it.append((flat_bar(top_p, bot_p, w, 0.011, normal=Vector((0, 1, s * 0.3))), m.main if i % 2 == 0 else m.under))
            for sx in (1, -1):
                notch = g.merge(notch, g.box((top_p + bot_p) / 2 + Vector((sx * w * 0.5, 0, 0)), (0.02, 0.03, h * 0.3)))
            z -= h
        it.append((notch, m.trim))
        A.update({"c": head, "eye": head + Vector((0, -0.02, 0)), "eye_r": R * 0.2, "top": head + Z * R * 0.62, "low": Vector((0, 0, z))})
    elif style == "board":          # a tall board, a hand on it for every post
        w, h = R * 1.5, R * 4.0
        it.append((g.box(c, (w, 0.035, h)), m.main))
        it.append((g.box(c + Z * (h / 2 + 0.012), (w * 1.16, 0.05, 0.03)), m.under))
        ped = [c + Vector((-w * 0.58, 0, h / 2 + 0.027)), c + Vector((w * 0.58, 0, h / 2 + 0.027)), c + Vector((0, 0, h / 2 + 0.027 + w * 0.42))]
        it.append((g.loft([[p + Y * 0.02 for p in ped], [p - Y * 0.02 for p in ped]]), m.under))
        hands = None
        for i in range(5):
            cc = c + Vector((0, -0.02, h * 0.34 - h * 0.17 * i))
            it.append((disc(cc, w * 0.3, 0.012, n=10), mat("dial_face"), ROUND))
            a = 0.7 + 1.1 * i
            hands = g.merge(hands, g.blade(cc + Y * -0.01, cc + Y * -0.01 + Vector((math.cos(a), 0, math.sin(a))) * w * 0.27, 0.016, normal=(0, -1, 0)))
        it.append((hands, mat("eye_dark")))
        eye_c = c + Vector((0, -0.024, h / 2 + 0.027 + w * 0.15))
        A.update({"eye": eye_c, "eye_r": w * 0.13, "top": c + Z * (h / 2 + 0.03 + w * 0.42), "low": c - Z * h / 2, "R": w * 0.6})
    elif style == "table":          # a level table on three legs, and a glass to sight along it
        t = Vector((0, 0, 0.62))
        it.append((disc(t, R * 1.15, 0.022, n=14, facing=Z), m.main, ROUND))
        it.append((hoop(t, R * 1.15, 0.012, n=14, sides=4), m.under))
        it.append((turned([(0.05, -0.07), (0.06, -0.02), (0.03, 0.0)], n=8, centre=t), m.under, ROUND))
        for i in range(3):
            a = math.radians(330 - 120 * i)
            d = Vector((math.cos(a), math.sin(a), 0))
            it.append((rod(t + d * 0.04 - Z * 0.05, d * 0.34 + Z * 0.012, 0.013, r1=0.009), m.under, ROUND))
            it.append((g.lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.012), (0.0, 0.024)], n=8, centre=d * 0.34), m.trim))
        for s in (1, -1):
            it.append((flat_bar(t + Vector((s * 0.07, 0, 0.01)), t + Vector((s * 0.07, 0, 0.16)), 0.03, 0.012, normal=X), m.under))
        tube = [t + Vector((0, 0.14, 0.15)), t + Vector((0, -0.2, 0.15))]
        it.append((g.tube(tube, [0.034, 0.042], n=8), m.main, ROUND))
        it += lens(tube[1] + Y * -0.004, 0.04, m, pupil=True, glow="eyes", strength=3.4)
        it.append((g.tube([t + Vector((-0.12, -0.1, 0.03)), t + Vector((0.12, -0.1, 0.03))], [0.016, 0.016], n=6), mat("glass_clear"), ROUND))
        it.append((ball(t + Vector((0.02, -0.1, 0.03)), 0.02, sub=0, scale=(1.5, 1, 1)), field("level", 3.4)))
        A.update({"c": t, "eye": tube[1], "eye_r": 0.0, "top": t + Z * 0.2, "low": Vector((0, 0, 0)), "front": -0.2, "table": True})
    elif style == "case":           # closed, with a clasp, and a small window showing today
        it.append((disc(c, R * 0.95, 0.1, n=8), m.main))
        it.append((f2.band(c, R * 0.97, R * 0.97, 0.012, n=8, u=X, v=Z, sides=4), m.trim))
        for z in (-0.5, 0.0, 0.5):
            it.append((g.tube([c + Vector((-R * 0.93, -0.03, z * R)), c + Vector((-R * 0.93, 0.03, z * R))], [0.018, 0.018], n=6), m.under, ROUND))
        it.append((g.box(c + Vector((R * 0.9, 0, 0)), (0.05, 0.13, R * 0.34)), m.under))
        it.append((ball(c + Vector((R * 0.93, -0.066, 0)), 0.018, sub=0), m.trim))
        studs = None
        for a in (0.6, 2.2, 3.9, 5.5):
            studs = g.merge(studs, ball(c + Vector((R * 0.66 * math.cos(a), -0.052, R * 0.66 * math.sin(a))), 0.02, sub=0))
        it.append((studs, m.under))
        win = c + Vector((0, -0.05, R * 0.12))
        it.append((annulus(win, R * 0.3, R * 0.42, 0.016, n=10), m.under, ROUND))
        A.update({"eye": win + Vector((0, -0.002, 0)), "eye_r": R * 0.25, "front": -0.05})
    elif style == "ball":           # a sphere with a band of seals round its middle
        rb = R * 0.82
        it.append((ball(c, rb, sub=2), m.main, ROUND))
        it.append((hoop(c, rb * 1.02, 0.03, n=14, sides=4), m.under))
        for i in range(8):
            a = 2 * math.pi * (i + 0.5) / 8
            d = Vector((math.cos(a), math.sin(a), 0))
            it.append((disc(c + d * (rb * 1.02 + 0.03), 0.042, 0.016, n=8, facing=d), mat("wax_red"), ROUND))
        it.append((turned([(rb * 0.3, 0.0), (rb * 0.22, 0.03), (0.02, 0.045)], n=8, centre=c + Z * rb * 0.95), m.under, ROUND))
        A.update({"eye": c + Vector((0, -rb * 0.86, rb * 0.5)), "eye_r": rb * 0.26, "top": c + Z * (rb + 0.03), "facing": Vector((0, -0.86, 0.5)).normalized()})
    elif style == "rose":           # a star of eight points
        it.append((disc(c, R * 0.5, 0.034, n=12), m.main, ROUND))
        for i in range(8):
            a = math.pi / 2 + 2 * math.pi * i / 8
            d = Vector((math.cos(a), 0, math.sin(a)))
            it.append((g.blade(c + d * R * 0.2, c + d * R * (1.3 if i % 2 == 0 else 0.86), R * 0.42, thick=0.02, normal=Y, belly=0.3), m.main if i % 2 == 0 else m.under))
        it.append((f2.band(c + Y * -0.006, R * 0.72, R * 0.72, 0.008, n=16, u=X, v=Z, sides=3), m.trim))
        A.update({"top": c + Z * R * 1.3, "eye_r": R * 0.2})
    elif style == "worn":           # a dial with no numbers, only worn places where numbers were
        chip = [0, 0, 0.1, 0.22, 0.06, 0, 0, 0.04, 0, 0.14, 0.3, 0.12, 0, 0, 0.05, 0]
        ring_f = [c + Y * -0.018 + Vector((math.cos(2 * math.pi * i / 16), 0, math.sin(2 * math.pi * i / 16))) * R * (1 - chip[i]) for i in range(16)]
        ring_b = [p + Y * 0.036 for p in ring_f]
        it.append((g.loft([ring_f, ring_b]), m.main))
        it.append((flat_bar(c + Vector((-R * 0.5, -0.02, R * 0.6)), c + Vector((R * 0.1, -0.02, -R * 0.7)), 0.012, 0.006), mat("soot")))
        patches = None
        for a, rr in ((0.5, 0.6), (2.4, 0.7), (4.4, 0.55), (5.6, 0.75)):
            patches = g.merge(patches, ball(c + Vector((R * rr * math.cos(a), -0.02, R * rr * math.sin(a))), R * 0.17, sub=0, scale=(1, 0.14, 0.8)))
        it.append((patches, mat("verdigris")))
        A.update({"top": c + Z * R * 0.98})
    elif style == "dome":           # the heavens as they were, held over whoever stands under
        d0 = c + Z * R * 0.2
        rd = R * 1.5
        outer = [(rd * math.cos(t), rd * 0.8 * math.sin(t)) for t in (0.0, 0.35, 0.7, 1.05, 1.4, 1.57)]
        inner = [(rd * 0.95 * math.cos(t), rd * 0.76 * math.sin(t)) for t in (1.4, 1.05, 0.7, 0.35, 0.0)]
        it.append((turned(outer + inner, n=12, centre=d0, caps=False), m.under, ROUND))
        it.append((hoop(d0, rd, 0.014, n=12, sides=4), m.main))
        stars = None
        for i in range(16):
            a, t = i * 2.39996, 0.25 + 1.1 * ((i * 7) % 16) / 16
            p = d0 + Vector((rd * 1.01 * math.cos(t) * math.cos(a), rd * 1.01 * math.cos(t) * math.sin(a), rd * 0.81 * math.sin(t)))
            stars = g.merge(stars, ball(p, 0.014 + 0.006 * (i % 3), sub=0))
        it.append((stars, field("stars", 2.6)))
        hub = d0 - Z * R * 0.55
        it.append((rod(d0 + Z * rd * 0.76, hub, 0.006), m.trim))
        it.append((disc(hub, R * 0.5, 0.03, n=12), m.main, ROUND))
        A.update({"c": hub, "eye": hub + Vector((0, -0.022, 0)), "eye_r": R * 0.17, "top": d0 + Z * rd * 0.8, "low": hub - Z * R * 0.5, "R": rd * 0.8})
    else:                           # "chart": a great plate crowded with fine lines
        w, h = R * 3.0, R * 1.9
        it.append((g.box(c, (w, 0.02, h)), m.main))
        for s in (1, -1):
            it.append((g.tube([c + Vector((s * w / 2, 0, -h / 2 - 0.03)), c + Vector((s * w / 2, 0, h / 2 + 0.03))], [0.034, 0.034], n=7), m.under, ROUND))
            for zz in (1, -1):
                it.append((ball(c + Vector((s * w / 2, 0, zz * (h / 2 + 0.045))), 0.026, sub=0), m.trim))
        lines = None
        for i in range(8):
            z = -h * 0.4 + h * 0.8 * i / 7
            pts = [c + Vector((-w * 0.44 + w * 0.88 * k / 6, -0.014, z + 0.03 * math.sin(k * 1.3 + i * 0.9))) for k in range(7)]
            if i in (2, 3):
                pts = pts[:3]       # where it turned round, it draws nothing
            lines = g.merge(lines, g.tube(pts, [0.005] * len(pts), n=3))
        it.append((lines, m.trim))
        it.append((g.box(c + Vector((w * 0.2, -0.012, -h * 0.1)), (w * 0.3, 0.006, h * 0.26)), mat("dial_face")))
        hub = c + Vector((-w * 0.22, -0.02, h * 0.12))
        it.append((disc(hub, R * 0.42, 0.02, n=12), m.under, ROUND))
        A.update({"eye": hub + Vector((0, -0.014, 0)), "eye_r": R * 0.15, "top": c + Z * (h / 2), "low": c - Z * (h / 2), "R": h / 2, "hub": hub})

    # what lies over the plate
    rstyle, rs = gl.opt(spec.get("rete"))
    cc, Rr = A["c"], A["R"]
    if style in ("disc", "shield", "wave"):
        y = A["front"] - 0.004
        if rstyle == "ticks":
            ticks = None
            for k in range(12):
                a = 2 * math.pi * k / 12
                d = Vector((math.cos(a), 0, math.sin(a)))
                ticks = g.merge(ticks, flat_bar(cc + Y * y + d * Rr * 0.74, cc + Y * y + d * Rr * 0.9, 0.012, 0.006))
            it.append((ticks, m.under))
        elif rstyle == "fret":      # the fretted plate: two rings off the centre and three pointers
            for cx, cz, rr in ((0.0, 0.14, 0.62), (0.14, -0.2, 0.4)):
                it.append((f2.band(cc + Vector((cx * Rr, y, cz * Rr)), rr * Rr, rr * Rr, 0.007, n=14, u=X, v=Z, sides=3), m.under))
            for a in (0.5, 2.3, 4.2):
                d = Vector((math.cos(a), 0, math.sin(a)))
                it.append((g.blade(cc + Y * y + d * Rr * 0.24, cc + Y * y + d * Rr * 0.8, Rr * 0.15, normal=(0, -1, 0), thick=0.004), m.under))
        elif rstyle == "hours":
            marks = None
            for k in range(12):
                a = 2 * math.pi * k / 12
                d = Vector((math.cos(a), 0, math.sin(a)))
                marks = g.merge(marks, flat_bar(cc + Y * y + d * Rr * 0.5, cc + Y * y + d * Rr * 0.66, 0.02 if k % 3 == 0 else 0.01, 0.006))
            it.append((marks, m.trim))
    return it, A


def astro_arms(spec, m, it, A):
    c, R = A["c"], A["R"]
    y = A["front"] - 0.016
    for style, s in gl.each(spec.get("arms")):
        if style == "rule":         # the rule across its face
            d = Vector((math.cos(0.42), 0, math.sin(0.42)))
            it.append((flat_bar(c + Y * y - d * R * 1.02, c + Y * y + d * R * 1.02, R * 0.13, 0.008), m.trim))
            for sg in (1, -1):
                it.append((g.box(c + Y * (y - 0.012) + d * R * 0.9 * sg, (0.012, 0.03, R * 0.16), rot=(0, -0.42, 0)), m.trim))
        elif style == "lens":       # one arm ends in a lens, held out toward the furthest thing in view
            p0 = c + Vector((R * 0.5, y, R * 0.3))
            p1 = c + Vector((R * 1.15, y - 0.06, R * 0.75))
            p2 = c + Vector((R * 1.5 * s, y - 0.2 * s, R * 0.55))
            it.append((g.tube([p0, p1, p2], [0.012, 0.01, 0.008], n=4), m.under))
            it.append((ball(p1, 0.018, sub=0), m.main))
            it += lens(p2 + Vector((0, -0.01, 0)), R * 0.4 * s, m, glow="eyes", strength=2.4, deep=0.3)
            A["lens"] = p2
        elif style in ("tube", "long-tube"):    # a glass to look through, along its top
            L = R * (1.5 if style == "tube" else 3.4) * s
            top = A["top"] + Vector((0, 0, 0.035 if A["style"] != "sector" else 0.02))
            a, b2 = top + Y * (L * 0.36), top - Y * (L * 0.64)
            if style == "tube":
                it.append((g.tube([a, b2], [R * 0.11, R * 0.15], n=8), m.main, ROUND))
            else:                   # drawn out in three lengths
                q1, q2 = a.lerp(b2, 0.36), a.lerp(b2, 0.7)
                it.append((g.tube([a, q1], [R * 0.1, R * 0.1], n=8), m.under, ROUND))
                it.append((g.tube([q1, q2], [R * 0.14, R * 0.14], n=8), m.main, ROUND))
                it.append((g.tube([q2, b2], [R * 0.18, R * 0.21], n=8), m.under, ROUND))
                for q in (q1, q2):
                    it.append((f2.band(q, R * 0.19, R * 0.19, 0.008, n=8, u=X, v=Z, sides=3), m.trim))
            it += lens(b2 + Y * -0.004, R * (0.15 if style == "tube" else 0.2), m, glow="eyes", strength=3.0, deep=0.3)
            for q in (a.lerp(b2, 0.3), a.lerp(b2, 0.62 if style == "tube" else 0.45)):
                it.append((rod(q, Vector((q.x, min(q.y, 0.0) * 0.2, A["top"].z - 0.02)), 0.008), m.trim))
            A["tube_top"] = top + Z * R * 0.2
        elif style == "pointer":    # a pointer it runs down the scale, clicking
            p, L = A.get("pivot", c), A.get("L", R)
            d = Vector((math.sin(0.2), 0, -math.cos(0.2)))
            it.append((flat_bar(p + Y * -0.02, p + Y * -0.02 + d * L * 1.02, 0.022, 0.008), m.trim))
            it.append((g.box(p + Y * -0.024 + d * L * 0.93, (0.07, 0.016, 0.05), rot=(0, -0.2, 0)), m.main))
            it.append((ball(p + Y * -0.04 + d * L * 0.93, 0.014, sub=0), field("needle", 3.0)))
        elif style == "bead":       # its pointer rests a hand's breadth ahead of what it tracks
            lead = A.get("lead", c + Vector((R * 0.3, -0.07, R * 0.22)))
            it.append((rod(c + Y * -0.02, lead, 0.006, n=3), m.trim))
            it.append((ball(lead, R * 0.1, sub=1), field("needle", 3.4), ROUND))
        elif style == "needle":     # a single needle that points at people's feet
            top = c - Z * R * 0.3
            tip = c - Z * (R * 1.2 + 0.26 * s) + Y * -0.03
            it.append((g.tube([top, c - Z * R * 1.05, tip], [0.02, 0.03, 0.003], n=4), m.trim))
            it.append((ball(c - Z * R * 1.05, 0.04, sub=0), m.main))
            # and the scale it reads on, like a thing that weighs
            L = R * 1.2 + 0.2 * s
            arc = [c + Y * -0.02 + Vector((math.sin(a), 0, -math.cos(a))) * L for a in [math.radians(-38 + 76 * i / 8) for i in range(9)]]
            for a0, a1 in zip(arc, arc[1:]):
                it.append((flat_bar(a0, a1, 0.03, 0.012), m.main))
            for i in (0, 4, 8):
                it.append((flat_bar(arc[i], arc[i] + (c - arc[i]).normalized() * 0.06, 0.012, 0.012), m.under))
            for sg in (0, 8):
                it.append((rod(c + Y * -0.02, arc[sg], 0.005, n=3), m.under))
            A["low"] = tip
        elif style in ("hands", "tide-hands"):  # hands on its face
            yy = y - 0.01
            for i, (a, L, w) in enumerate(((1.9, 0.78, 0.13), (0.5, 0.5, 0.17))):
                d = Vector((math.cos(a), 0, math.sin(a)))
                if style == "tide-hands" and i == 0:    # one hand points at high water: it is drawn like water
                    pts = [c + Y * yy + d * R * L * t + Vector((-d.z, 0, d.x)) * (R * 0.07 * math.sin(t * 9)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
                    it.append((g.tube(pts, [0.012, 0.011, 0.01, 0.008, 0.003], n=4), mat("enamel_blue")))
                elif style == "tide-hands":             # and one points at you
                    it.append((g.tube([c + Y * yy, c + Y * (yy - R * 0.9)], [0.016, 0.003], n=5), m.trim))
                else:
                    it.append((g.blade(c + Y * yy - d * R * 0.1, c + Y * yy + d * R * L, R * w, normal=(0, -1, 0), thick=0.006, belly=0.25), m.trim))
        elif style == "dividers":   # a pair of dividers, hung like legs
            hip = A["low"] + Vector((0, -0.01, 0.03))
            for sg in (1, -1):
                it.append((g.tube([hip, hip + Vector((sg * 0.07, 0, -0.16 * s)), hip + Vector((sg * 0.1, 0, -0.34 * s))], [0.014, 0.012, 0.002], n=4), m.under))
            it.append((ball(hip, 0.024, sub=1), m.main, ROUND))
            A["low"] = hip + Vector((0, 0, -0.34 * s))
        elif style == "pantograph":  # jointed arms that draw what it has worked out
            p0 = c + Vector((R * 0.9, -0.03, -R * 0.2))
            p1, p2, p3 = p0 + Vector((0.22, -0.02, 0.12)), p0 + Vector((0.2, -0.04, -0.14)), p0 + Vector((0.42, -0.06, -0.03))
            for a0, a1 in ((p0, p1), (p0, p2), (p1, p3), (p2, p3)):
                it.append((flat_bar(a0, a1, 0.018, 0.008), m.under))
            for q in (p0, p1, p2):
                it.append((ball(q, 0.014, sub=0), m.main))
            it.append((g.cone(p3, p3 + Vector((0.02, -0.01, -0.1)), 0.012, n=4), m.trim))
            it.append((ball(p3 + Vector((0.02, -0.01, -0.1)), 0.012, sub=0), field("needle", 3.2)))
        elif style == "broken-hand":
            d = Vector((math.cos(2.2), 0, math.sin(2.2)))
            it.append((g.blade(c + Y * y, c + Y * y + d * R * 0.4, R * 0.14, normal=(0, -1, 0), thick=0.006), m.trim))


def astro_rings(spec, m, it, A):
    c, R = A["c"], A["R"]
    for style, s in gl.each(spec.get("rings")):
        if style == "orbit":        # rings inside rings, never touching
            for i, (rr, tilt, lean, w) in enumerate(((1.0, 0.0, 0.35, 0.014), (0.82, 1.1, -0.3, 0.012), (0.62, 0.5, 1.2, 0.01))[: (3 if s >= 1.0 else 2)]):
                u = Matrix.Rotation(lean, 3, "Y") @ (Matrix.Rotation(tilt, 3, "Z") @ X)
                v = Matrix.Rotation(lean, 3, "Y") @ (Matrix.Rotation(tilt, 3, "Z") @ Vector((0, 0.34, 0.94)))
                it.append((f2.band(c, R * rr * s, R * rr * s, w, n=18, u=u, v=v, sides=4), m.main if i != 1 else m.under))
                it.append((ball(c + u * R * rr * s, 0.022 - 0.004 * i, sub=1), m.under if i != 1 else m.main, ROUND))
            A["top"] = c + Z * R * 1.02 * max(1.0, s)
        elif style == "cage":       # a cage of turning hoops
            for i, a in enumerate((0.0, math.pi / 3, 2 * math.pi / 3)):
                u = Vector((math.cos(a), math.sin(a), 0))
                it.append((f2.band(c, R, R, 0.012, n=18, u=u, v=Z, sides=4), m.main))
            it.append((hoop(c, R * 1.0, 0.03, n=18, sides=4), m.under))
            for zz in (0.45, -0.45):
                it.append((hoop(c + Z * R * zz, R * math.sqrt(1 - zz * zz), 0.009, n=16, sides=3), m.under))
            ecl = Matrix.Rotation(0.41, 3, "X")
            it.append((f2.band(c, R * 1.04, R * 1.04, 0.022, n=18, u=X, v=ecl @ Y, sides=4), field("seam", 1.3)))
            marks = None
            for k in range(12):
                a = 2 * math.pi * k / 12
                marks = g.merge(marks, g.box(c + Vector((R * 1.03 * math.cos(a), R * 1.03 * math.sin(a), 0)), (0.016, 0.03, 0.045), rot=(0, 0, a)))
            it.append((marks, m.trim))
            A["top"] = c + Z * R * 1.0
        elif style == "ellipse":    # it goes round at arm's length, and slows on the far side
            u = Matrix.Rotation(0.3, 3, "Y") @ X
            v = Matrix.Rotation(-0.35, 3, "X") @ Y
            off = u * R * 0.5 * s
            it.append((f2.band(c + off, R * 1.7 * s, R * 1.05 * s, 0.01, n=22, u=u, v=v, sides=3), m.under))
            moon = c + off + u * R * 1.7 * s
            it.append((ball(moon, R * 0.2, sub=1), m.main, ROUND))
            it.append((ball(moon + Y * -R * 0.17, R * 0.08, sub=0), field("needle", 3.0)))
            it.append((ball(c + off - u * R * 1.7 * s, R * 0.11, sub=0), m.trim))
            it.append((rod(c, moon, 0.005, n=3), m.trim))
        elif style == "horizon":    # a flat ring round its middle, the watches marked on it
            it.append((annulus(c, R * 0.95, R * 1.3 * s, 0.016, n=16, facing=Z), m.under, ROUND))
            marks = None
            for k in range(12):
                a = 2 * math.pi * k / 12
                d = Vector((math.cos(a), math.sin(a), 0))
                marks = g.merge(marks, g.cone(c + d * R * 1.28 * s, c + d * R * (1.5 if k % 3 == 0 else 1.38) * s, 0.02, n=4))
            it.append((marks, m.trim))


def astro_wings(spec, m, A):
    """What it flies on. Returns {name: items} (wing_l and wing_r beat) and items that do not."""
    c, R = A["c"], A["R"]
    style, s = gl.opt(spec.get("wings"))
    wings, still, at = {}, [], {}
    if style in ("leaves", "glider"):   # leaves of brass that open like a fan
        for name, sg in (("wing_l", 1), ("wing_r", -1)):
            root = c + Vector((sg * R * 0.92, 0.02, R * 0.2))
            parts = [(ball(root, R * 0.13, sub=0), m.under)]
            n = 5 if style == "leaves" else 3
            for i in range(n):
                if style == "leaves":
                    a = math.radians(-18 + 26 * i)
                    d = Vector((sg * math.cos(a), 0.12, math.sin(a)))
                    L, w = R * (1.9 - 0.16 * i) * s, R * 0.56
                else:
                    a = math.radians(4 + 9 * i)
                    d = Vector((sg * math.cos(a), 0.3 + 0.25 * i, math.sin(a)))
                    L, w = R * (3.0 - 0.5 * i) * s, R * 0.5
                parts.append((g.blade(root + d * R * 0.08, root + d * L, w, normal=(0, -1, 0.15), belly=0.6, thick=0.008), m.main if i % 2 == 0 else m.under))
            wings[name] = parts
            at[name] = root
    elif style == "vanes":          # thin vanes of brass: it rides the air
        for sg in (1, -1):
            root = c + Vector((sg * R * 0.5, 0.03, R * 0.3))
            for i in range(3):
                d = Vector((sg * 1.0, 0.25 + 0.3 * i, 0.22 - 0.2 * i)).normalized()
                still.append((g.blade(root + Vector((0, 0.05 * i, -0.05 * i)), root + Vector((0, 0.05 * i, -0.05 * i)) + d * R * (2.6 - 0.45 * i) * s, R * 0.5, normal=(0, -0.3, 1), belly=0.55, thick=0.006), m.main if i != 1 else m.under))
            still.append((ball(root, R * 0.12, sub=0), m.under))
    elif style == "fins":           # it swims: fins at its sides and a tail
        for sg in (1, -1):
            root = c + Vector((sg * R * 0.9, 0.0, -R * 0.1))
            for i, (dz, L) in enumerate(((0.5, 0.9), (0.0, 1.15), (-0.5, 0.9))):
                still.append((g.blade(root, root + Vector((sg * 1.0, 0.25, dz)).normalized() * R * L * s, R * 0.36, normal=(0, -1, 0), belly=0.5, thick=0.006), mat("enamel_blue") if i == 1 else m.under))
        tail = c + Vector((0, 0.02, -R * 0.95))
        for dx in (-0.5, 0.0, 0.5):
            still.append((g.blade(tail, tail + Vector((dx, 0.1, -1.0)).normalized() * R * 0.9 * s, R * 0.3, normal=(0, -1, 0), belly=0.5, thick=0.006), m.under if dx else mat("enamel_blue")))
        A["low"] = tail - Z * R * 0.9 * s
    return wings, still, at


def astro_gear(spec, m, it, A):
    c, R = A["c"], A["R"]
    y = A["front"] - 0.012
    for style, s in gl.each(spec.get("carry")):
        if style == "fob":          # a chain, as a thing kept in a pocket has
            a0 = A["top"] + Z * 0.05
            it.append((chain(a0, a0 + Vector((R * 1.3, 0.04, -R * 0.2)), size=0.016, sag=R * 0.5), m.under))
        elif style == "gears":      # wheels where it works things out
            p = A.get("pivot", c + Vector((R * 0.5, 0, -R * 0.5)))
            it.append((gear(p + Vector((R * 0.52, 0.03, -R * 0.1)), R * 0.32, teeth=10), m.under))
            it.append((gear(p + Vector((R * 0.2, 0.034, -R * 0.56)), R * 0.2, teeth=8), m.trim))
        elif style == "dial2":      # a second, smaller dial that turns backward
            p = A["low"] + Vector((R * 0.9, -0.01, R * 0.5))
            it.append((disc(p, R * 0.42, 0.024, n=12), m.main, ROUND))
            it.append((f2.band(p, R * 0.42, R * 0.42, 0.011, n=12, u=X, v=Z, sides=4), m.under))
            it.append((g.blade(p + Y * -0.016, p + Y * -0.016 + Vector((-0.6, 0, 0.5)) * R * 0.36, R * 0.09, normal=(0, -1, 0), thick=0.005), field("needle", 3.0)))
            it.append((flat_bar(A.get("pivot", c) + Vector((0.05, 0.012, -R * 0.8)), p, 0.014, 0.008), m.under))
        elif style == "plumb":      # a line and a weight, to know which way is down
            top = A["low"] + Vector((-R * 0.4, 0, 0.04)) if not A.get("table") else A["c"] - Z * 0.07
            it.append((rod(top, top - Z * 0.26, 0.003, n=3), mat("rope")))
            it.append((g.lathe([(0.0, 0.0), (0.03, -0.02), (0.022, -0.05), (0.0, -0.1)], n=6, centre=top - Z * 0.26), m.main, ROUND))
            if not A.get("table"):
                A["low"] = top - Z * 0.36
        elif style == "lines":      # faint lines hang in the air round it for a moment after it turns
            geo = None
            for i, (a0, a1, rr, yy) in enumerate(((0.3, 1.5, 1.5, -0.1), (1.9, 2.9, 1.75, 0.04), (3.3, 4.6, 1.45, -0.06), (5.0, 6.0, 1.9, 0.08), (0.9, 2.2, 2.1, 0.0))):
                pts = [c + Vector((math.cos(a0 + (a1 - a0) * t / 6) * R * rr * s, yy, math.sin(a0 + (a1 - a0) * t / 6) * R * rr * s)) for t in range(7)]
                geo = g.merge(geo, g.tube(pts, [0.004, 0.007, 0.008, 0.008, 0.008, 0.007, 0.004], n=3))
                geo = g.merge(geo, ball(pts[-1], 0.016, sub=0))
            it.append((geo, field("lines", 2.2)))
        elif style == "vane":       # a small vane on top that never stops moving
            base = A.get("tube_top", A["top"] + Z * 0.06)
            top = base + Z * R * 0.9
            it.append((rod(base - Z * 0.03, top, 0.007), m.under))
            it.append((flat_bar(top + Vector((-R * 0.8, 0.1, 0)), top + Vector((R * 0.7, -0.1, 0)), 0.014, 0.008, normal=Z), m.main))
            it.append((g.blade(top + Vector((-R * 0.8, 0.1, 0)), top + Vector((-R * 1.3, 0.16, 0)), R * 0.5, normal=Vector((0.15, 1, 0)), belly=0.8, thick=0.006), m.main))
            it.append((g.cone(top + Vector((R * 0.7, -0.1, 0)), top + Vector((R * 1.05, -0.15, 0)), 0.03, n=4), m.trim))
            A["tube_top"] = top
        elif style == "cups":       # cups that turn in the wind
            hub = A["top"] + Vector((-R * 0.9, 0.02, 0.1))
            it.append((rod(A["top"] + Vector((-R * 0.5, 0, -0.03)), hub, 0.007), m.under))
            for i in range(3):
                a = 0.4 + 2 * math.pi * i / 3
                d = Vector((math.cos(a), math.sin(a), 0))
                it.append((rod(hub, hub + d * R * 0.6, 0.005, n=3), m.under))
                cup = g.lathe([(0.0, 0.0), (R * 0.16, 0.02), (R * 0.2, 0.07), (R * 0.16, 0.07), (0.0, 0.02)], n=6)
                it.append((g.moved(cup, TR(hub + d * R * 0.6, rot=(math.pi / 2, 0, a))), m.main, ROUND))
        elif style == "telltales":
            for sg in (1, -1):
                p = c + Vector((sg * R, 0, -R * 0.1))
                it.append((g.tongue([p, p + Vector((sg * 0.05, 0.1, -0.1)), p + Vector((sg * 0.02, 0.22, -0.16)), p + Vector((sg * 0.06, 0.34, -0.3))], [0.03, 0.03, 0.026, 0.012], thick=0.2, normal=Z), mat("ribbon"), SOFT))
        elif style == "eyes3":      # it turns to each of your friends in order
            for i, a in enumerate((0.4, 2.2, 4.0)):
                d = Vector((math.cos(a), -0.25, math.sin(a))).normalized()
                p = c + d * R * 1.6 * s
                it.append((rod(c + d * R * 0.8, p, 0.008), m.under))
                it += lens(p + Y * -0.012, R * 0.3, m, glow="eyes", strength=3.0, deep=0.35, pupil=True)
        elif style == "trumpet":    # it calls each target by name
            p = c + Vector((0, -0.03, -R * 0.75))
            horn = g.lathe([(0.012, 0.0), (0.02, 0.1), (0.045, 0.19), (0.085, 0.24), (0.07, 0.24), (0.03, 0.17), (0.012, 0.09)], n=8)
            it.append((g.moved(horn, TR(p, rot=(2.2, 0, 0))), m.main, ROUND))
        elif style == "headlamp":   # a small light of its own, facing down the line
            p = c + Vector((0, -0.02, -R * 1.25))
            it.append((rod(c - Z * R * 0.9, p + Z * 0.06, 0.008), m.under))
            it.append((g.tube([p + Y * 0.08, p + Y * -0.05], [0.05, 0.07], n=8), m.under, ROUND))
            it += lens(p + Y * -0.055, 0.066, m, glow="core", strength=4.4, deep=0.4)
            it.append((turned([(0.075, 0.0), (0.02, 0.04)], n=6, centre=p + Z * 0.06), m.trim))
            A["low"] = p - Z * 0.07
        elif style == "escapement":  # it ticks ahead of any clock: the wheel and the anchor, laid bare
            p = c + Vector((R * 1.25, 0.02, R * 0.25))
            it.append((gear(p, R * 0.5, teeth=14, t=0.012), m.under))
            it.append((g.tube([p + Vector((-R * 0.45, -0.02, R * 0.62)), p + Vector((0, -0.02, R * 0.8)), p + Vector((R * 0.45, -0.02, R * 0.62))], [0.012, 0.016, 0.012], n=4), m.trim))
            bob = p + Vector((R * 0.42, -0.02, -R * 1.25))
            it.append((rod(p + Vector((0, -0.02, R * 0.8)), bob, 0.006, n=3), m.trim))
            it.append((disc(bob, R * 0.2, 0.02, n=10), m.main, ROUND))
            it.append((flat_bar(c + Vector((R * 0.3, 0.02, 0)), p, 0.018, 0.008), m.under))
        elif style == "foot":       # it stands on one of its marks
            p = A["low"] + Z * 0.01
            it.append((g.lathe([(0.0, -0.09), (0.09, -0.09), (0.1, -0.075), (0.03, -0.03), (0.03, 0.0)], n=8, centre=p), m.under, ROUND))
            A["low"] = p - Z * 0.09
        elif style == "striker":    # it wakes you a minute before you are needed
            p = c + Vector((R * 1.15, -0.02, R * 0.75))
            it.append((g.lathe([(0.012, 0.05), (0.04, 0.035), (0.06, 0.0), (0.05, 0.0), (0.02, 0.03)], n=8, centre=p), m.under, ROUND))
            it.append((g.tube([c + Vector((R * 0.6, 0, R * 0.5)), p + Z * 0.07, p + Z * 0.05], [0.007, 0.007, 0.007], n=3), m.trim))
            it.append((ball(p + Vector((0.05, 0, 0.0)), 0.014, sub=0), m.trim))
        elif style == "moon":       # where the moon is, which the water knows
            a = 0.9
            p = c + Vector((math.cos(a), -0.1, math.sin(a))) * R * 1.32 * s
            it.append((rod(c + Y * -0.02, p, 0.005, n=3), m.trim))
            it.append((ball(p, R * 0.2 * s, sub=1), mat("dial_face"), ROUND))
            it.append((ball(p + Vector((R * 0.07, 0.01, 0)), R * 0.2 * s, sub=1, scale=(0.9, 1.02, 1.0)), mat("enamel_night"), ROUND))
        elif style == "seals":
            pass
        elif style == "stamp":      # the seal it presses, on its chain
            a0 = c + Vector((R * 0.8, 0, -R * 0.2))
            end = a0 + Vector((R * 0.35, -0.03, -R * 1.15))
            it.append((chain(a0, end, size=0.018), m.under))
            it.append((g.lathe([(0.0, 0.0), (0.035, 0.0), (0.035, -0.02), (0.016, -0.04), (0.016, -0.09), (0.03, -0.11), (0.0, -0.12)], n=8, centre=end), m.main, ROUND))
            A["low"] = Vector((0, 0, min(A["low"].z, end.z - 0.12)))
        elif style == "star":       # one bright point that does not move when the rest turns
            a = 0.95
            p = c + Vector((math.cos(a), 0, math.sin(a))) * R * 0.92 + Y * -0.05
            pts = None
            for i in range(8):
                b2 = 2 * math.pi * i / 8
                pts = g.merge(pts, g.blade(p, p + Vector((math.cos(b2), -0.1, math.sin(b2))) * R * (0.5 if i % 2 == 0 else 0.26) * s, R * 0.14, normal=(0, -1, 0)))
            it.append((pts, field("star", 4.6)))
            it.append((ball(p, R * 0.11, sub=1), mat("white_hot"), ROUND))
            it.append((rod(c + Y * -0.02, p, 0.006, n=3), m.trim))
        elif style == "crown":      # small points round its rim
            pts = None
            for i in range(16):
                a = 2 * math.pi * i / 16 + 0.2
                d = Vector((math.cos(a), 0, math.sin(a)))
                pts = g.merge(pts, ball(c + d * R * 0.72 + Y * -0.02, 0.012, sub=0))
            it.append((pts, m.trim))
        elif style == "cord":       # hung on a frayed cord, the ring long gone
            top = A["top"]
            it.append((g.tube([top - Z * 0.02, top + Vector((0.02, 0, 0.06)), top + Vector((-0.01, 0, 0.12))], [0.008, 0.007, 0.006], n=4), mat("rope"), SOFT))
            it.append((g.tongue([top + Z * 0.02, top + Vector((0.05, 0.02, -0.02)), top + Vector((0.07, 0.03, -0.07))], [0.012, 0.012, 0.004], thick=0.5), mat("rope"), SOFT))


def build_astrolabe(form_id, level, spec, base, silhouette):
    m = Metals(silhouette)
    it, A = astro_plate(spec, m)
    astro_rings(spec, m, it, A)
    astro_arms(spec, m, it, A)
    wings, still, wing_at = astro_wings(spec, m, A)
    it += still
    astro_gear(spec, m, it, A)
    # where it is alive: an eye where the pin goes through
    fstyle, fs = gl.opt(spec.get("face", "eye"))
    if fstyle != "none" and A["eye_r"] > 0:
        it += eye(A["eye"], A["eye_r"] * fs, m, facing=A["facing"], heavy=(fstyle == "lids"), dark=(fstyle == "dark"))
    # the ring it hangs by, on its throne
    top = A.get("tube_top", A["top"])
    cords = [st for st, _ in gl.each(spec.get("carry"))]
    carry = top + Z * 0.05
    if "cord" in cords:
        carry = A["top"] + Vector((-0.01, 0, 0.12))
    else:
        it.append((g.box(top + Z * 0.01, (0.05, 0.022, 0.03)), m.main))
        it.append((f2.band(top + Z * 0.052, 0.03, 0.03, 0.008, n=10, u=X, v=Z, sides=4), m.main))
    low = A["low"]
    anchors = {"top": top, "face": A["eye"], "light": A["c"], "carry": carry, "back": A["c"] + Y * 0.04}
    anchors.update(wing_at)
    return finish(form_id, it, anchors, wings=wings, ref=top.z)


# ======================================================================================
# The Bell
# ======================================================================================

# a bell's outline from its crown down to its lip (radius, height above the lip), and how thick it is cast
BELLS = {
    "hand": ([(0.02, 0.2), (0.045, 0.19), (0.055, 0.15), (0.06, 0.1), (0.075, 0.05), (0.1, 0.015), (0.112, 0.0)], 0.012),
    "ship": ([(0.03, 0.26), (0.075, 0.245), (0.09, 0.2), (0.095, 0.14), (0.11, 0.08), (0.14, 0.03), (0.168, 0.0)], 0.016),
    "pot": ([(0.04, 0.2), (0.12, 0.19), (0.16, 0.15), (0.18, 0.09), (0.185, 0.03), (0.2, 0.0)], 0.016),
    "tower": ([(0.03, 0.3), (0.09, 0.285), (0.105, 0.24), (0.105, 0.17), (0.12, 0.1), (0.15, 0.045), (0.192, 0.0)], 0.018),
    "great": ([(0.04, 0.34), (0.12, 0.32), (0.14, 0.27), (0.14, 0.19), (0.16, 0.11), (0.2, 0.05), (0.25, 0.0)], 0.04),
    "gong": ([(0.02, 0.1), (0.09, 0.09), (0.14, 0.06), (0.165, 0.02), (0.172, 0.0)], 0.012),
    "flare": ([(0.02, 0.24), (0.05, 0.225), (0.055, 0.17), (0.06, 0.12), (0.085, 0.07), (0.14, 0.03), (0.225, 0.0)], 0.012),
    "barrel": ([(0.04, 0.28), (0.12, 0.265), (0.165, 0.21), (0.18, 0.14), (0.17, 0.07), (0.16, 0.03), (0.176, 0.0)], 0.03),
    "long": ([(0.02, 0.42), (0.05, 0.405), (0.058, 0.33), (0.062, 0.22), (0.07, 0.12), (0.095, 0.04), (0.132, 0.0)], 0.012),
    "tall": ([(0.03, 0.4), (0.085, 0.385), (0.1, 0.33), (0.105, 0.2), (0.115, 0.08), (0.13, 0.03), (0.146, 0.0)], 0.014),
}


class Bell:
    """One bell, cast: its shell about its own axis (the lip at 0, the crown at H)."""

    def __init__(self, style, s, material, n=12, hollow=True):
        prof, t = BELLS.get(style, BELLS["ship"])
        self.prof = [(r * s, z * s) for r, z in prof]
        self.t = t * s
        self.H, self.R = self.prof[0][1], self.prof[-1][0]
        inner = [(max(0.004, r - self.t), z + self.t * 0.25) for r, z in reversed(self.prof[1:])] + [(0.0, self.H - self.t * 1.3)]
        if not hollow:              # a small one, seen from outside only
            inner = [(self.R - self.t, self.t * 0.6), (0.0, self.t * 0.6)]
        shell = [(0.0, self.H)] + self.prof + inner
        self.items = [(g.lathe(shell, n=n, phase=phase(n)), material, ROUND)]

    def r_at(self, z):
        p = self.prof
        for (r0, z0), (r1, z1) in zip(p, p[1:]):
            if z1 <= z <= z0:
                t = (z0 - z) / max(1e-6, z0 - z1)
                return r0 + (r1 - r0) * t
        return p[-1][0]

    def on(self, z, a, out=0.0):
        """A point on its skin at height z, at angle a round it (0 is the front, -Y)."""
        r = self.r_at(z) + out
        return Vector((r * math.sin(a), -r * math.cos(a), z))


def bell_tongue(bell, style, s, m):
    """What it is rung with, in the bell's own frame."""
    H, R, t = bell.H, bell.R, bell.t
    top = Vector((0, 0, H - t * 1.5))
    it = []
    if style in ("ball", "trembling", "fist", "long"):
        end = {"ball": -0.015, "trembling": -0.03, "fist": 0.05, "long": -0.3}[style] * (s if style == "long" else 1.0)
        rb = {"ball": 0.034, "trembling": 0.03, "fist": 0.06, "long": 0.03}[style] * s
        sway = Vector((0.02 if style == "trembling" else 0.0, 0, 0))
        tip = Vector((0, 0, end)) + sway
        it.append((rod(top, tip + Z * rb * 0.6, (0.012 if style == "fist" else 0.007) * s), m.under))
        if style == "long":         # one cold note: a long rod and a weight like a drop
            it.append((g.lathe([(0.0, 0.07), (0.022, 0.03), (0.034, -0.01), (0.02, -0.045), (0.0, -0.06)], n=7, centre=tip), m.under, ROUND))
        else:
            it.append((ball(tip, rb, sub=1), field("voice", 3.6) if style == "trembling" else m.under, ROUND))
    elif style == "row":            # a row of different small tongues, and it chooses among them
        for i, x in enumerate((-0.6, -0.3, 0.0, 0.3, 0.6)):
            p0 = Vector((x * R * 0.8, 0, H * 0.55))
            p1 = Vector((x * R * 0.9, 0, -0.01 - 0.012 * (i % 3)))
            it.append((rod(p0, p1, 0.006), m.under))
            shape = (ball(p1, 0.026, sub=0), g.box(p1, (0.03, 0.03, 0.06)), ball(p1, 0.034, sub=1), g.cone(p1 + Z * 0.03, p1 - Z * 0.05, 0.022, n=4), f2.band(p1, 0.022, 0.022, 0.007, n=6, u=X, v=Z, sides=3))[i]
            it.append((shape, field("voice", 3.2) if i == 2 else (m.trim if i % 2 else m.under)))
    return it


def bell_local(spec, m, bell, forward):
    """What is part of the bell itself and turns with it."""
    H, R = bell.H, bell.R
    it = []
    for style, s in gl.each(spec.get("carry")):
        if style == "teeth":        # a hard bright mouth
            teeth = None
            for k in range(12):
                a = 2 * math.pi * (k + 0.5) / 12
                d = Vector((math.sin(a), -math.cos(a), 0))
                teeth = g.merge(teeth, g.cone(d * (R - bell.t * 0.5) + Z * 0.004, d * (R - bell.t * 0.2) - Z * 0.05 * s, 0.022 * s, n=4))
            it.append((teeth, m.trim))
        elif style == "band":       # a painted band
            z = H * 0.42
            it.append((g.lathe([(bell.r_at(z + 0.03) + 0.004, z + 0.03), (bell.r_at(z - 0.03) + 0.004, z - 0.03)], n=12, phase=phase(12), caps=False), kit.mark("band", m.under), ROUND))
        elif style == "bumps":      # dented outward from the inside
            bumps = None
            for i, (z, a) in enumerate(((0.62, 0.6), (0.5, 2.0), (0.7, 3.4), (0.42, 4.6), (0.56, 5.6), (0.36, 1.2))):
                bumps = g.merge(bumps, ball(bell.on(H * z, a, out=-0.012), 0.04 * s, sub=1))
            it.append((bumps, m.main, ROUND))
        elif style == "dent":       # where the ladle has struck it for years
            it.append((ball(bell.on(H * 0.5, 0.9, out=0.0), 0.035 * s, sub=1, scale=(1, 1, 1.2)), mat("soot"), ROUND))
        elif style == "marks":      # hammer marks all over it
            marks = None
            for i in range(14):
                z, a = H * (0.2 + 0.6 * ((i * 5) % 14) / 14), i * 2.39996
                marks = g.merge(marks, ball(bell.on(z, a, out=0.002), 0.022, sub=0, scale=(1, 1, 0.8)))
            it.append((marks, m.under))
        elif style == "brow":       # a brow of bronze above the lip
            arc = [bell.on(H * 0.2, a, out=0.035 * s) for a in (-1.25, -0.8, -0.4, 0.0, 0.4, 0.8, 1.25)]
            it.append((g.tube(arc, [0.02, 0.034, 0.042, 0.046, 0.042, 0.034, 0.02], n=5, flat=0.7), m.trim, ROUND))
        elif style == "horns":
            for sg in (1, -1):
                b0 = bell.on(H * 0.62, sg * 1.2)
                it.append((g.tube([b0, b0 + Vector((sg * 0.09, -0.02, 0.05)) * s, b0 + Vector((sg * 0.13, -0.08, 0.15)) * s], [0.034 * s, 0.024 * s, 0.003], n=5), mat("horn"), ROUND))
        elif style == "studs":
            studs = None
            for k in range(10):
                studs = g.merge(studs, ball(bell.on(H * 0.74, 2 * math.pi * k / 10, out=0.004), 0.018, sub=0))
            it.append((studs, m.trim))
        elif style == "inscription":  # what was cast into it
            blocks = None
            for k in range(16):
                if k % 4 == 3:
                    continue
                blocks = g.merge(blocks, g.box(bell.on(H * 0.6, 2 * math.pi * k / 16, out=0.004), (0.03, 0.012, 0.04), rot=(0, 0, 2 * math.pi * k / 16)))
            it.append((blocks, m.under))
            for z in (H * 0.7, H * 0.5):
                it.append((hoop((0, 0, z), bell.r_at(z) + 0.004, 0.008, n=12), m.under, ROUND))
        elif style == "plaques":    # the names it keeps, plate by plate
            plates = None
            for row, z in enumerate((0.62, 0.44)):
                for k in range(9):
                    a = 2 * math.pi * (k + 0.5 * row) / 9
                    plates = g.merge(plates, g.box(bell.on(H * z, a, out=0.004), (0.055, 0.01, 0.04), rot=(0.25, 0, a)))
            it.append((plates, m.trim))
        elif style == "verdigris":  # green at the rim
            it.append((g.lathe([(bell.r_at(0.045) + 0.004, 0.05), (R + 0.006, 0.0), (R - bell.t * 0.4, -0.004)], n=12, phase=phase(12), caps=False), mat("verdigris"), ROUND))
        elif style == "drops":      # beaded with wet in any weather
            drops = None
            for k in range(7):
                a = 2 * math.pi * k / 7 + 0.3
                d = Vector((math.sin(a), -math.cos(a), 0))
                drops = g.merge(drops, g.lathe([(0.0, 0.0), (0.012, -0.02), (0.008, -0.035), (0.0, -0.042)], n=5, centre=d * (R - 0.004)))
            it.append((drops, mat("glass_clear"), ROUND))
        elif style == "icicles":
            ice = None
            for k in range(9):
                a = 2 * math.pi * k / 9
                d = Vector((math.sin(a), -math.cos(a), 0))
                ice = g.merge(ice, g.cone(d * (R - 0.004) + Z * 0.004, d * (R - 0.006) - Z * (0.05 + 0.04 * (k % 3)) * s, 0.014, n=4))
            it.append((ice, mat("ice_pale")))
        elif style == "ribbons":    # crepe tied round its crown
            it.append((hoop((0, 0, H * 0.93), bell.r_at(H * 0.93) + 0.008, 0.014, n=10), mat("crepe"), SOFT))
            for sg in (1, -1):
                b0 = bell.on(H * 0.93, sg * 1.6, out=0.01)
                it.append((g.tongue([b0, b0 + Vector((sg * 0.05, 0.02, -0.12)), b0 + Vector((sg * 0.07, 0.05, -0.3 * s)), b0 + Vector((sg * 0.05, 0.08, -0.46 * s))], [0.05, 0.05, 0.045, 0.02], thick=0.15, normal=X), mat("crepe"), SOFT))
        elif style == "doors":      # like a door closing slowly: two leaves, half shut over its face
            for sg in (1, -1):
                c = bell.on(H * 0.52, sg * 0.42, out=0.012)
                it.append((g.box(c, (bell.r_at(H * 0.5) * 0.55, 0.012, H * 0.3), rot=(0.12, 0, sg * 0.42 + sg * 0.25)), m.trim))
        elif style == "sight":      # a bead to aim it by
            it.append((rod(bell.on(H * 0.2, 0.0), bell.on(H * 0.2, 0.0, out=0.06), 0.006), m.trim))
            it.append((ball(bell.on(H * 0.2, 0.0, out=0.07), 0.016, sub=0), field("needle", 3.0)))
            it.append((rod(bell.on(H * 0.8, 0.0), bell.on(H * 0.8, 0.0, out=0.05), 0.006), m.trim))
            it.append((f2.band(bell.on(H * 0.8, 0.0, out=0.065), 0.018, 0.018, 0.005, n=8, u=X, v=Y, sides=3), m.trim))
        elif style == "fin":        # so that what it says goes straight
            for a in (math.pi, math.pi / 2, -math.pi / 2):
                b0 = bell.on(H * 0.9, a)
                d = Vector((math.sin(a), -math.cos(a), 0))
                it.append((g.blade(b0 - Z * 0.03, b0 + d * 0.1 * s + Z * 0.12 * s, 0.1 * s, normal=d.cross(Z), belly=0.5, thick=0.008), m.trim))
        elif style == "chains":     # a ring of small links round its crown, and what hangs from them
            it.append((hoop((0, 0, H * 0.9), bell.r_at(H * 0.9) + 0.012, 0.014, n=10, sides=4), m.trim, ROUND))
            for k in range(3):
                a = math.pi / 3 + k * 2 * math.pi / 3
                top = bell.on(H * 0.9, a, out=0.016)
                end = bell.on(0.02, a, out=0.06) - Z * 0.12 * s
                it.append((chain(top, end, size=0.04), m.under, ROUND))
                it.append((g.lathe([(0.0, 0.02), (0.03, 0.0), (0.03, -0.04), (0.0, -0.06)], n=6, centre=end), m.trim, ROUND))
        elif style == "selector":   # the wheel it chooses by
            it.append((gear(Vector((0, 0, H + 0.02)), R * 0.45, teeth=8, t=0.016, facing=Z), m.trim))
    # where it is alive
    fstyle, fs = gl.opt(spec.get("face", "eye"))
    faces = []
    if fstyle != "none":
        re_ = max(0.022, R * 0.2) * fs
        if forward:                 # a mouth, and an eye either side above it
            for sg in (1, -1):
                p = bell.on(H * 0.42, sg * 0.95, out=-0.004)
                d = Vector((math.sin(sg * 0.95), -math.cos(sg * 0.95), 0.0))
                it += eye(p, re_ * 0.9, m, facing=d, heavy=(fstyle == "lids"))
                faces.append(p)
        else:
            z = H * (0.5 if R > 0.13 else 0.42)
            p = bell.on(z, 0.0, out=-0.004)
            it += eye(p, re_, m, facing=(0, -1, 0.12), heavy=(fstyle == "lids"))
            faces.append(p)
    return it, faces


def bell_hang(spec, m, bell, crown, P, forward):
    """What holds it up. crown: where its crown is in the world. Returns (items, anchors)."""
    style, s = gl.opt(spec.get("hang", "none"))
    H, R = bell.H, bell.R
    it = []
    wood = mat("wood")
    A = {"top": crown + Z * 0.02, "carry": crown + Z * 0.05}
    side = R + 0.07

    def ring_at(p):
        it.append((f2.band(p + Z * 0.035, 0.032, 0.032, 0.008, n=10, u=X, v=Z, sides=4), m.trim, ROUND))
        A["top"], A["carry"] = p, p + Z * 0.035

    if style == "handle":           # a hand-bell: a turned handle
        h = g.lathe([(0.02, 0.0), (0.03, 0.02), (0.018, 0.05), (0.027, 0.1), (0.02, 0.15), (0.012, 0.165), (0.0, 0.17)], n=8)
        it.append((g.moved(h, P @ TR((0, 0, H))), wood, ROUND))
        it.append((g.moved(g.lathe([(0.024, -0.004), (0.032, 0.006), (0.024, 0.016)], n=8), P @ TR((0, 0, H))), m.trim, ROUND))
        top = P @ Vector((0, 0, H + 0.17))
        A["top"], A["carry"] = top, P @ Vector((0, 0, H + 0.1))
    elif style in ("yoke", "wheel", "beam", "headstock"):   # hung from a stock, rung by a rope
        thick = {"yoke": 0.045, "wheel": 0.055, "beam": 0.05, "headstock": 0.1}[style] * max(1.0, s)
        half = {"yoke": side, "wheel": side + 0.03, "beam": R * 3.4, "headstock": side + 0.05}[style]
        c = crown + Z * (thick / 2 + 0.012)
        it.append((g.box(c, (half * 2, thick * 0.9, thick)), wood))
        for sg in (1, -1):
            it.append((g.tube([c + Vector((sg * half, 0, 0)), c + Vector((sg * (half + 0.035), 0, 0))], [thick * 0.26, thick * 0.26], n=6), m.under, ROUND))
        # the straps that hold the bell to it
        for sg in (1, -1):
            it.append((loop_tube([c + Vector((sg * R * 0.3, -thick * 0.5, thick * 0.52)), c + Vector((sg * R * 0.3, thick * 0.5, thick * 0.52)), c + Vector((sg * R * 0.3, thick * 0.5, -thick * 0.6)), c + Vector((sg * R * 0.3, -thick * 0.5, -thick * 0.6))], 0.008, sides=3), m.under))
        if style == "yoke":
            it.append((g.tube([c + Vector((half, 0, 0)), c + Vector((half + 0.1, 0.0, 0.07))], [0.012, 0.01], n=4), m.under))
            A["rope"] = c + Vector((half + 0.1, 0, 0.07))
        elif style == "wheel":      # a wheel that turns it through its changes
            wc = c + Vector((-(half + 0.035), 0, 0))
            rw = R * 1.55 * s
            it.append((f2.band(wc, rw, rw, 0.014, n=18, u=Y, v=Z, sides=4), wood))
            for k in range(6):
                a = math.pi / 6 + k * math.pi / 3
                it.append((rod(wc, wc + Vector((0, math.cos(a), math.sin(a))) * rw, 0.008), wood))
            it.append((gear(c + Vector((half + 0.05, 0, 0)), 0.07, teeth=8, t=0.016, facing=X), m.trim))
            A["rope"] = wc + Vector((-0.01, -rw, 0))
            A["top"] = wc + Z * rw
        elif style == "beam":       # eight small bells along its yoke, smallest to largest
            for i in range(8):
                x = (-1 if i < 4 else 1) * (R * 1.35 + (R * 2.0) * ((i % 4) / 3.0))
                k = 0.36 + 0.07 * (i % 4 if i < 4 else 3 - i % 4)
                sb = Bell("ship", k * (R / 0.168), m.main, n=8, hollow=False)
                top = c + Vector((x, 0, -thick / 2 - 0.035))
                it += put(sb.items + [(ball(Vector((0, 0, -0.006)), 0.02 * k / 0.4, sub=0), m.under)], TR(top - Z * sb.H))
                it.append((rod(top, top + Z * 0.04, 0.006, n=3), m.under))
        elif style == "headstock":  # a great stock, strapped in iron, and the loops the bell is cast with
            for x in (-0.6, 0.6):
                it.append((loop_tube([c + Vector((x * half, -thick * 0.5, thick * 0.52)), c + Vector((x * half, thick * 0.5, thick * 0.52)), c + Vector((x * half, thick * 0.5, -thick * 0.52)), c + Vector((x * half, -thick * 0.5, -thick * 0.52))], 0.012, sides=4), m.under))
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                d = Vector((math.cos(a), math.sin(a), 0))
                it.append((f2.band(crown + d * R * 0.2 + Z * 0.0, 0.03, 0.035, 0.012, n=8, u=d, v=Z, sides=4), m.main, ROUND))
        ring_at(c + Z * (thick / 2))
        if style == "wheel":
            A["top"] = c + Vector((0, 0, R * 1.55 * s))
    elif style == "frame":          # hung in a frame that stands on a broad foot
        ht = crown.z + 0.03
        base = crown.z - H - 0.14 * s
        for sg in (1, -1):
            for fy in (1, -1):
                it.append((flat_bar(Vector((sg * (side + 0.01), fy * R * 0.9, base)), Vector((sg * side, 0, ht + 0.03)), 0.03, 0.026, normal=X), wood))
            it.append((g.box(Vector((sg * (side + 0.01), 0, base + (ht - base) * 0.4)), (0.024, R * 1.1, 0.024)), wood))
        it.append((g.box(Vector((0, 0, ht + 0.02)), (side * 2 + 0.07, 0.045, 0.045)), wood))
        it.append((g.box(Vector((0, 0, base - 0.012)), (side * 2 + 0.16, R * 2.2, 0.03)), m.under))
        ring_at(Vector((0, 0, ht + 0.045)))
        A["rope"] = Vector((side * 0.5, 0, ht))
        A["frame"] = (side, base, ht)
    elif style == "cradle":         # carried in a cradle, on a short column
        py = crown.z - H * 0.25
        for sg in (1, -1):
            it.append((g.tube([Vector((sg * 0.06, 0, crown.z - H - 0.2)), Vector((sg * (side + 0.02), 0, crown.z - H - 0.08)), Vector((sg * (side + 0.02), 0, py))], [0.024, 0.022, 0.018], n=6), m.under, ROUND))
            it.append((ball(Vector((sg * (side + 0.02), 0, py)), 0.03, sub=1), m.trim, ROUND))
            it.append((rod(Vector((sg * (side + 0.02), 0, py)), P @ Vector((sg * bell.r_at(H * 0.75), 0, H * 0.75)), 0.012), m.under))
        it.append((turned([(0.1, 0.0), (0.11, 0.02), (0.06, 0.05), (0.05, 0.16), (0.075, 0.2)], n=8, centre=(0, 0, crown.z - H - 0.38)), m.under, ROUND))
        ring_at(crown + Z * 0.012)
        A["rope"] = P @ Vector((0, 0.02, H * 0.2))
    elif style == "hook":           # hung from a hook on a short chain
        top = crown + Z * 0.17 * s
        it.append((chain(crown + Z * 0.05, top - Z * 0.02, size=0.022), m.under))
        it.append((g.tube([crown + Z * 0.0, crown + Vector((0.03, 0, 0.03)), crown + Vector((0, 0, 0.06))], [0.01, 0.01, 0.01], n=4), m.trim))
        ring_at(top)
    elif style == "crane":          # it hangs itself from any hook near a fire
        post = crown + Vector((side + 0.14, 0.02, 0))
        arm = crown.z + 0.16
        it.append((g.box(Vector((post.x, post.y, arm - 0.26)), (0.04, 0.04, 0.62)), m.under))
        it.append((g.tube([Vector((post.x, post.y, arm)), Vector((0.02, 0, arm)), Vector((-0.03, 0, arm - 0.02))], [0.016, 0.014, 0.012], n=5), m.under))
        it.append((g.tube([Vector((post.x, post.y, arm - 0.3)), Vector((post.x - 0.12, post.y, arm - 0.12)), Vector((post.x - 0.2, 0, arm - 0.01))], [0.01, 0.01, 0.01], n=4), m.under))
        it.append((g.tube(g.spiral(Vector((post.x - 0.07, post.y, arm - 0.09)), 0.055, 0.012, 1.25, 0.0, n=10, axis=Y), [0.008] * 11, n=3), m.under))
        it.append((g.tube([crown + Z * 0.0, crown + Vector((0.03, 0, 0.05)), crown + Vector((0, 0, 0.1)), Vector((0, 0, arm - 0.015))], [0.009] * 4, n=4), m.trim))
        A["top"], A["carry"] = Vector((post.x, post.y, arm + 0.05)), Vector((post.x, post.y, arm + 0.05))
        it.append((f2.band(Vector((post.x, post.y, arm + 0.085)), 0.03, 0.03, 0.008, n=10, u=X, v=Z, sides=4), m.trim, ROUND))
    elif style == "clock":          # it sits on the hours: a dial, and a hammer to strike them
        cc = crown - Z * (H + 0.17)
        rc = 0.16 * s
        it.append((disc(cc, rc, 0.11, n=14), m.main, ROUND))
        it.append((f2.band(cc + Y * -0.05, rc, rc, 0.016, n=14, u=X, v=Z, sides=4), m.trim, ROUND))
        it.append((disc(cc + Y * -0.058, rc * 0.86, 0.008, n=14), mat("dial_face"), ROUND))
        marks = None
        for k in range(12):
            a = 2 * math.pi * k / 12
            d = Vector((math.cos(a), 0, math.sin(a)))
            marks = g.merge(marks, flat_bar(cc + Y * -0.064 + d * rc * 0.66, cc + Y * -0.064 + d * rc * 0.8, 0.012, 0.004))
        it.append((marks, mat("eye_dark")))
        for a, L in ((1.25, 0.62), (2.6, 0.42)):
            d = Vector((math.cos(a), 0, math.sin(a)))
            it.append((g.blade(cc + Y * -0.068 - d * rc * 0.08, cc + Y * -0.068 + d * rc * L, rc * 0.12, normal=(0, -1, 0), thick=0.005, belly=0.25), mat("eye_dark")))
        for sg in (1, -1):
            it.append((rod(cc + Vector((sg * rc * 0.5, 0, rc * 0.8)), crown + Vector((sg * R * 0.5, 0, -H + 0.01)), 0.012), m.under))
            it.append((ball(cc + Vector((sg * rc * 0.62, 0, -rc * 0.95)), 0.03, sub=0), m.trim))
        hp = cc + Vector((rc + 0.03, 0, rc * 0.5))
        head = crown + Vector((R + 0.035, 0, -H * 0.5))
        it.append((g.tube([hp, hp + Vector((0.06, 0, 0.1)), head], [0.009, 0.008, 0.007], n=4), m.under))
        it.append((g.tube([head + Vector((0.03, 0, 0)), head - Vector((0.03, 0, 0))], [0.022, 0.022], n=6), m.trim, ROUND))
        ring_at(crown + Z * 0.012)
        it += eye(cc + Y * -0.066, rc * 0.22, m)
        A["dial"] = cc + Y * -0.066
    elif style == "belfry":         # under a little arch of its own
        ht = crown.z + 0.05
        base = crown.z - H - 0.05
        for sg in (1, -1):
            it.append((g.box(Vector((sg * (side + 0.02), 0, (base + ht) / 2)), (0.04, 0.07, ht - base)), m.under))
        arch = [Vector((math.cos(a) * (side + 0.02), 0, ht + math.sin(a) * (side + 0.02) * 0.8)) for a in [math.pi * i / 8 for i in range(9)]]
        it.append((g.tube(arch, [0.03] * 9, n=4, flat=1.3), m.under))
        it.append((g.box(Vector((0, 0, base - 0.012)), (side * 2 + 0.12, 0.11, 0.025)), m.under))
        roof = [Vector((-(side + 0.1), 0, ht + (side + 0.02) * 0.5)), Vector((0, 0, ht + (side + 0.02) * 1.15)), Vector((side + 0.1, 0, ht + (side + 0.02) * 0.5))]
        for a0, a1 in zip(roof, roof[1:]):
            it.append((flat_bar(a0, a1, 0.14, 0.014, normal=(a1 - a0).cross(Y)), m.trim))
        it.append((rod(crown, Vector((0, 0, ht + (side + 0.02) * 0.8)), 0.008), m.trim))
        ring_at(roof[1] + Z * 0.0)
    elif style == "post":           # it hangs from a post's bracket as if the bracket had been made for it
        px = side + 0.12
        top = crown.z + 0.3
        it.append((g.box(Vector((px, 0.02, crown.z - H * 0.75)), (0.07, 0.07, (top - crown.z) + H * 1.5 + 0.3)), wood))
        it.append((turned([(0.06, 0.0), (0.065, 0.015), (0.02, 0.04)], n=4, centre=(px, 0.02, top + 0.16)), m.under))
        it.append((g.tube([Vector((px, 0.02, crown.z + 0.16)), Vector((0.03, 0, crown.z + 0.16)), Vector((0, 0, crown.z + 0.12))], [0.014, 0.012, 0.01], n=4), m.under))
        it.append((g.tube(g.spiral(Vector((px * 0.55, 0.01, crown.z + 0.08)), 0.07, 0.014, 1.3, 0.0, n=10, axis=Y), [0.008] * 11, n=3), m.under))
        it.append((rod(crown, Vector((0, 0, crown.z + 0.12)), 0.008), m.trim))
        A["top"], A["carry"] = Vector((px, 0.02, top + 0.2)), Vector((0, 0, crown.z + 0.17))
        A["post"] = Vector((px, 0.02, top + 0.2))
    elif style in ("float", "tower"):   # it rides a float, in a cage
        fr = (0.22 if style == "float" else 0.27) * s
        fz = crown.z - H - (0.1 if style == "float" else 0.14)
        it.append((turned([(0.0, fz - fr * 0.9), (fr * 0.5, fz - fr * 0.76), (fr, fz - fr * 0.36), (fr, fz - 0.02), (fr * 0.74, fz + 0.02), (0.0, fz + 0.02)], n=10), m.main, ROUND))
        it.append((turned([(fr + 0.003, fz - fr * 0.32), (fr + 0.003, fz - 0.04)], n=10, caps=False), kit.mark("band", m.under), ROUND))
        topz = crown.z + (0.07 if style == "float" else 0.36)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            d = Vector((math.cos(a), math.sin(a), 0))
            it.append((rod(d * fr * 0.78 + Z * (fz + 0.01), d * (0.05 if style == "float" else 0.04) + Z * topz, 0.012), m.under))
        for z in ((fz + topz) / 2, crown.z):
            rr = fr * 0.78 + (0.05 - fr * 0.78) * ((z - fz) / (topz - fz))
            it.append((hoop((0, 0, z), rr, 0.008, n=8), m.under, ROUND))
        it.append((rod(crown, Vector((0, 0, min(topz, crown.z + 0.07))), 0.008), m.trim))
        ring_at(Vector((0, 0, topz + 0.01)))
        A["under"] = Vector((0, 0, fz - fr * 0.9))
        A["cage_top"] = Vector((0, 0, topz))
    else:                           # held by nothing: the ring cast on its crown
        ring_at(crown + Z * 0.004)
    return it, A


def bell_gear(spec, m, it, bell, B, A, crown, forward):
    """What it has been given. B maps a point of the bell to the world."""
    H, R = bell.H, bell.R
    lip = B(Vector((0, 0, 0)))
    for style, s in gl.each(spec.get("carry")):
        if style == "rope":         # the rope it is rung by
            top = A.get("rope", crown + Vector((R + 0.1, 0, 0.05)))
            pts = [top, top + Vector((0.02, -0.01, -0.2)), top + Vector((0.0, -0.02, -0.42 * s)), top + Vector((0.03, -0.03, -0.6 * s))]
            it.append((g.tube(pts, [0.011] * 4, n=5), mat("rope"), SOFT))
            it.append((ball(pts[-1], 0.026, sub=0), mat("rope")))
            it.append((ball(pts[2], 0.02, sub=0), mat("ribbon")))
        elif style == "foot":       # a broad foot that it plants in doorways
            if "frame" in A:
                side, base, ht = A["frame"]
                for sg in (1, -1):
                    it.append((g.lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.02), (0.04, 0.04)], n=8, centre=(sg * (side + 0.1), 0, base - 0.05)), m.trim, ROUND))
        elif style == "lamp":       # a lamp hung under its lip that swings as it rings
            hook = lip + Vector((0, -R * 0.5, -0.02)) if not forward else B(Vector((0, R * 0.9, 0.02)))
            it += put(small_lamp(m), TR(hook - Z * 0.2, s=1.05 * s))
            it.append((rod(hook, hook - Z * 0.085, 0.004, n=3), m.under))
        elif style == "pennons":    # the convoy's flags
            for sg in (1, -1):
                p = A["top"] + Vector((sg * 0.02, 0, 0.0))
                it.append((g.tongue([p, p + Vector((sg * 0.1, 0.03, 0.02)), p + Vector((sg * 0.22, 0.05, -0.03)), p + Vector((sg * 0.3, 0.06, 0.0))], [0.07, 0.07, 0.06, 0.01], thick=0.12, normal=Y), mat("ribbon"), SOFT))
        elif style == "scroll":     # a strip of names round its waist, and a mark by each
            z = H * 0.55
            pts = [B(bell.on(z - 0.01 * i, -1.9 + 0.62 * i, out=0.012)) for i in range(7)]
            pts += [pts[-1] + Vector((-0.07, -0.03, -0.12)), pts[-1] + Vector((-0.1, -0.05, -0.3)), pts[-1] + Vector((-0.07, -0.06, -0.44))]
            it.append((g.tongue(pts, [0.075] * 9 + [0.06], thick=0.1, normal=Z), mat("paper"), SOFT))
            marks = None
            for i in range(1, 6):
                marks = g.merge(marks, ball(B(bell.on(z - 0.01 * i, -1.9 + 0.62 * i, out=0.02)), 0.012, sub=0))
            it.append((marks, mat("eye_dark")))
        elif style == "abacus":     # it counts heads, and will not go on one short
            if "frame" in A:
                side, base, ht = A["frame"]
                z = base + (ht - base) * 0.2
                it.append((rod(Vector((-side, -0.01, z)), Vector((side, -0.01, z)), 0.006), m.under))
                beads = None
                for k, x in enumerate((-0.8, -0.62, -0.44, -0.26, 0.5, 0.7)):
                    beads = g.merge(beads, ball(Vector((x * side, -0.01, z)), 0.022, sub=0))
                it.append((beads, mat("ribbon")))
        elif style == "ladle":      # the ladle that has struck it for years
            hook = crown + Vector((R + 0.03, -0.02, 0.06))
            it.append((rod(hook, hook - Z * (H * 0.9), 0.008), m.under))
            it.append((g.lathe([(0.0, -0.03), (0.04, -0.02), (0.05, 0.02), (0.042, 0.02), (0.0, -0.012)], n=7, centre=hook - Z * (H * 0.9 + 0.01)), m.under, ROUND))
            it.append((rod(crown + Z * 0.03, hook, 0.006), m.under))
        elif style == "sound":      # a low ring you feel in the breastbone before you hear it
            for i in range(3):
                it.append((hoop(lip - Z * (0.05 + 0.075 * i), R * (1.05 + 0.3 * i) * s, 0.009 - 0.002 * i, n=18), field("ring", 2.6 - 0.6 * i)))
        elif style == "cushion":
            it.append((g.lathe([(0.0, 0.0), (0.07, 0.0), (0.085, 0.02), (0.07, 0.045), (0.0, 0.05)], n=8, centre=crown + Z * 0.004), mat("cloth_red"), SOFT))
        elif style == "mallet":
            p = lip + Vector((-(R + 0.1), -0.03, 0.12))
            it.append((rod(p, p + Vector((-0.02, 0.0, 0.28)), 0.009), mat("wood")))
            it.append((ball(p, 0.04, sub=1, scale=(1, 1, 1.2)), mat("cloth_red"), ROUND))
        elif style == "tags":       # the names it is rung for, hung round its lip
            tags = None
            for k in range(9):
                a = -1.9 + 0.48 * k
                p = B(bell.on(0.012, a, out=0.0))
                tags = g.merge(tags, flat_bar(p, p + Vector((0.0, -0.004, -0.085 - 0.02 * (k % 2))), 0.036, 0.006, normal=Vector((math.sin(a), -math.cos(a), 0))))
            it.append((tags, m.trim))
        elif style == "taper":      # a stub of candle on it, lit
            p = A["top"] + Vector((0.07, 0, -0.01))
            it.append((rod(p, p + Z * 0.06, 0.012, n=5), mat("wax")))
            it += flame("candle", p + Z * 0.06, 0.4)
        elif style == "soot":       # blacked by the fire it hangs by
            it.append((g.moved(g.lathe([(0.0, H + 0.002), (bell.r_at(H * 0.94) + 0.003, H * 0.94 + 0.003), (bell.r_at(H * 0.8) + 0.003, H * 0.8)], n=12, phase=phase(12), caps=False), B.M), mat("soot"), ROUND))
        elif style == "hourglass":  # the watches of the night, in sand
            p = crown + Vector((-(R + 0.12), -0.02, -H * 0.3))
            it.append((g.lathe([(0.04, 0.07), (0.035, 0.04), (0.008, 0.0), (0.035, -0.04), (0.04, -0.07)], n=7, centre=p), mat("glass_clear"), ROUND))
            for z in (0.075, -0.075):
                it.append((disc(p + Z * z, 0.05, 0.012, n=7, facing=Z), m.trim, ROUND))
            for a in (0.5, 2.6, 4.7):
                it.append((rod(p + Vector((0.045 * math.cos(a), 0.045 * math.sin(a), -0.075)), p + Vector((0.045 * math.cos(a), 0.045 * math.sin(a), 0.075)), 0.004, n=3), m.trim))
            it.append((rod(p + Z * 0.08, crown + Vector((-(R * 0.5), 0, 0.06)), 0.004, n=3), mat("rope")))
        elif style == "cowl":       # a hood over it, falling in folds
            rings = []
            for zf, rr, back in ((1.12, 0.3, 0.0), (0.98, 0.72, 0.01), (0.7, 1.12, 0.02), (0.3, 1.3, 0.03), (-0.05, 1.42, 0.05)):
                ring = []
                for k in range(9):
                    a = math.radians(-125 + 250 * k / 8) + math.pi
                    fold = 1.0 + 0.07 * math.sin(k * 2.3) * (1.0 - zf)
                    ring.append(B(Vector((math.sin(a) * bell.r_at(H * 0.6) * rr * fold, -math.cos(a) * bell.r_at(H * 0.6) * rr * fold + back, H * zf))))
                rings.append(ring)
            outer = g.loft(rings, caps=False, closed=False)
            inner = g.loft([[p + (B(Vector((0, 0, H * 0.5))) - p).normalized() * 0.012 for p in ring] for ring in reversed(rings)], caps=False, closed=False)
            it.append((g.merge(outer, inner), mat("cloth_wool"), SOFT))
        elif style == "post-lamp":  # the post's own light
            p = A.get("post", A["top"])
            it += put(small_lamp(m), TR(p + Z * 0.0, s=1.3))
        elif style == "fork":       # a clean high note: a fork that sings it
            base = A["top"] + Z * 0.0
            for sg in (1, -1):
                it.append((g.tube([base, base + Vector((sg * 0.05, 0, 0.07)), base + Vector((sg * 0.05, 0, 0.42 * s))], [0.014, 0.014, 0.011], n=4), m.trim))
            it.append((ball(base + Vector((0, 0, 0.36 * s)), 0.03, sub=1), field("voice", 3.4), ROUND))
            A["top"] = base + Z * 0.42 * s
            A["carry"] = base + Vector((0, 0, 0.44 * s))
        elif style == "damper":
            p = B(bell.on(H * 0.3, 1.57, out=0.03))
            it.append((ball(p, 0.035, sub=0, scale=(0.6, 1, 1)), mat("cloth_red")))
            it.append((rod(p, p + Vector((0.08, 0, 0.12)), 0.006, n=3), m.under))
        elif style == "dish":       # it rings, then tilts, then waits: a great ear to hear what comes back
            c = B(Vector((0, 0, H * 0.75)))
            prof = [(0.0, 0.0), (R * 1.2 * s, -0.035 * s), (R * 2.3 * s, -0.17 * s), (R * 2.36 * s, -0.165 * s), (R * 1.24 * s, -0.022 * s), (0.0, 0.016)]
            it.append((g.moved(g.lathe(prof, n=14), B.M @ TR((0, 0, H * 0.78))), m.under, ROUND))
            for k in range(3):
                a = math.pi / 2 + 2 * math.pi * k / 3
                it.append((rod(B(Vector((math.cos(a) * R * 1.9 * s, math.sin(a) * R * 1.9 * s, H * 0.78 - 0.12 * s))), B(bell.on(H * 0.1, a + math.pi / 2)), 0.006, n=3), m.trim))
        elif style == "line":       # a line and a lead, to sound with
            top = crown + Vector((R * 0.6, 0.03, 0.0))
            end = top - Z * (H + 0.42 * s)
            it.append((rod(top, end, 0.004, n=3), mat("rope")))
            it.append((g.lathe([(0.0, 0.03), (0.03, 0.0), (0.03, -0.07), (0.0, -0.09)], n=6, centre=end), m.under, ROUND))
            for k in (0.3, 0.55, 0.8):
                it.append((ball(top.lerp(end, k), 0.012, sub=0), mat("ribbon")))
        elif style == "hammers":    # hammers that swing against it from outside
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                d = Vector((math.cos(a), math.sin(a), 0))
                top = A.get("cage_top", crown + Z * 0.06) + d * 0.045
                head = crown + d * (R + 0.03) - Z * (H * 0.82)
                it.append((rod(top, head, 0.006, n=3), m.under))
                it.append((ball(head, 0.03, sub=0), m.trim))
        elif style == "topmark":    # the mark pilots know it by, and its light
            p = A.get("cage_top", A["top"])
            it.append((rod(p, p + Z * 0.16, 0.008), m.under))
            it.append((g.lathe([(0.0, 0.0), (0.07, 0.05), (0.0, 0.1)], n=8, centre=p + Z * 0.14), kit.mark("band", m.under), ROUND))
            it.append((ball(p + Z * 0.27, 0.03, sub=0), field("core", 4.2)))
            A["top"] = p + Z * 0.14
            A["carry"] = p + Z * 0.3
        elif style == "chain":      # a chain under it, and weed on the chain
            u = A.get("under", lip - Z * 0.1)
            end = u + Vector((0.05, 0.03, -0.36 * s))
            it.append((chain(u, end, size=0.026), m.under))
            it.append((ball(end - Z * 0.03, 0.04, sub=0), m.under))
            weed = None
            for i in range(4):
                p = u.lerp(end, 0.2 + 0.2 * i)
                weed = g.merge(weed, g.tongue([p, p + Vector((0.05 * math.sin(i * 2.0), 0.04 * math.cos(i * 2.0), -0.06)), p + Vector((0.07 * math.sin(i * 2.0 + 0.5), 0.07 * math.cos(i * 2.0), -0.15))], [0.03, 0.036, 0.01], thick=0.3))
            it.append((weed, mat("weed"), SOFT))
        elif style == "ghosts":     # you hear it from the wrong side: the bell, and where it seems to be
            for i, (dx, dy, k) in enumerate(((R * 2.3, 0.1, 0.9), (-R * 2.0, 0.22, 0.72))):
                off = Vector((dx, dy, 0.03 * i))
                for z in (0.0, 0.3, 0.6, 0.88):
                    it.append((hoop(crown + off + (B(Vector((0, 0, H * z))) - crown) * k, bell.r_at(H * z) * k, 0.006, n=12), mat("mist"), SOFT))
                for a in (0.0, 1.57, 3.14, 4.71):
                    pts = [B(bell.on(H * z, a)) for z in (0.0, 0.3, 0.6, 0.88, 1.0)]
                    pts = [crown + off + (p - crown) * k for p in pts]
                    it.append((g.tube(pts, [0.004] * 5, n=3), mat("mist"), SOFT))
                if i == 0:          # and its voice is in the wrong one
                    it.append((ball(crown + off - Z * H * 0.95 * k, 0.034, sub=1), field("voice", 3.8), ROUND))
        elif style == "hammer":     # a hammer raised against it
            piv = crown + Vector((R * 0.5, 0.04, 0.09))
            head = B(bell.on(H * 0.35, -1.57 if forward else 1.57, out=0.09))
            it.append((g.tube([crown + Z * 0.02, piv, head], [0.01, 0.01, 0.009], n=4), m.under))
            hd = (head - piv).normalized().cross(Y).normalized()
            it.append((g.tube([head - hd * 0.045, head + hd * 0.045], [0.03, 0.03], n=6), m.trim, ROUND))
        elif style == "anvil":      # a face to be struck on, a horn and a heel
            top = crown + Z * 0.0
            it.append((g.box(top + Z * 0.045, (R * 2.5 * s, R * 1.25, 0.09)), m.main))
            it.append((g.box(top + Z * 0.095, (R * 2.5 * s, R * 1.25, 0.014)), m.under))
            horn = [(0.0, 0.0), (0.045, 0.0), (0.02, 0.2 * s), (0.0, 0.26 * s)]
            it.append((g.moved(g.lathe(horn, n=7), TR(top + Vector((R * 1.24 * s, 0, 0.05)), rot=(0, math.pi / 2, 0))), m.main, ROUND))
            it.append((g.box(top + Vector((-R * 1.4 * s, 0, 0.065)), (R * 0.4, R * 1.0, 0.05)), m.main))
            A["top"] = top + Z * 0.1
            A["carry"] = top + Z * 0.1
        elif style == "smiths":     # the hammers that made it what it is, and it shows them off
            for sg in (1, -1):
                p = A["top"] + Vector((sg * R * 0.7, -0.02, 0.0))
                it.append((rod(p, p + Vector((sg * 0.2, -0.04, 0.3)), 0.011), mat("wood")))
                it.append((g.box(p + Vector((sg * 0.2, -0.04, 0.3)), (0.11, 0.055, 0.06), rot=(0, sg * -0.6, 0)), m.under))
        elif style == "cloud":      # the air round it is close: weather clings to it
            cloud = None
            for i, (dx, dy, dz, rr) in enumerate(((0.0, 0.04, 0.03, 0.12), (0.13, 0.0, -0.01, 0.1), (-0.14, 0.02, 0.0, 0.11), (0.05, -0.1, -0.02, 0.09), (-0.06, 0.12, 0.04, 0.09), (0.2, 0.08, -0.05, 0.07), (-0.22, -0.05, -0.04, 0.07))):
                cloud = g.merge(cloud, ball(B(Vector((0, 0, H * 0.95))) + Vector((dx, dy, dz + 0.05)) * s, rr * s, sub=1))
            it.append((cloud, mat("smoke"), SOFT))
            A["top"] = B(Vector((0, 0, H * 0.95))) + Z * 0.16 * s
            A["carry"] = A["top"] + Z * 0.03
        elif style == "bolts":      # when it rings there is weather
            for i, (a, L) in enumerate(((0.5, 0.34), (2.4, 0.4), (4.2, 0.3))):
                d = Vector((math.cos(a), 0.2, math.sin(a) * 0.5 - 0.6)).normalized()
                side_v = d.cross(Y).normalized()
                p = B(Vector((0, 0, H * 0.9))) + Vector((math.cos(a) * 0.12, 0.0, 0.04))
                pts = [p, p + d * L * 0.3 * s + side_v * 0.05, p + d * L * 0.55 * s - side_v * 0.04, p + d * L * s]
                it.append((g.tongue(pts, [0.04, 0.05, 0.035, 0.004], thick=0.25, normal=Y), field("bolt", 4.0)))
        elif style == "crest":      # horn only: a crest along its back
            pass
        elif style == "coldcore":
            pass


class Placer:
    """A point of the bell, in the world."""

    def __init__(self, M):
        self.M = M

    def __call__(self, p):
        return self.M @ V(p)


def build_horn(form_id, spec, m):
    """It grew a throat and a flare of brass: a horn, and it knows it."""
    it = []
    path = [Vector((0.0, 0.34, 0.5)), Vector((0.0, 0.32, 0.3)), Vector((0.0, 0.2, 0.14)), Vector((0.0, 0.0, 0.1)), Vector((0.0, -0.2, 0.2)), Vector((0.0, -0.34, 0.4)), Vector((0.0, -0.42, 0.62))]
    radii = [0.014, 0.022, 0.034, 0.05, 0.07, 0.1, 0.13]
    it.append((g.tube(path, radii, n=10, caps=False), m.main, ROUND))
    d = (path[-1] - path[-2]).normalized()
    flare = g.lathe([(0.13, 0.0), (0.17, 0.035), (0.25, 0.085), (0.27, 0.09), (0.19, 0.035), (0.12, -0.01)], n=12, caps=False)
    Rm = Z.rotation_difference(d).to_matrix().to_4x4()
    it.append((g.moved(flare, Matrix.Translation(path[-1]) @ Rm), kit.mark("rim", m.main), ROUND))
    it.append((ball(path[-1] - d * 0.03, 0.1, sub=1, scale=(1, 1, 0.5)), mat("soot"), ROUND))
    it.append((g.moved(g.lathe([(0.022, 0.0), (0.03, 0.02), (0.018, 0.04), (0.012, 0.07)], n=8), TR(path[0], rot=(0.1, 0, 0))), m.under, ROUND))
    for i in (2, 4):
        it.append((f2.band(path[i], radii[i] + 0.006, radii[i] + 0.006, 0.01, n=10, u=X, v=(path[i + 1] - path[i - 1]).normalized().cross(X), sides=4), kit.mark("bands", m.main), ROUND))
    # a crest along its back, the way a thing that calls across valleys would wear one
    for i, t in enumerate((0.42, 0.52, 0.62, 0.72, 0.82, 0.92)):
        k = t * (len(path) - 1)
        a, b2 = path[int(k)], path[min(len(path) - 1, int(k) + 1)]
        p = a.lerp(b2, k - int(k))
        rr = radii[int(k)] + (radii[min(len(radii) - 1, int(k) + 1)] - radii[int(k)]) * (k - int(k))
        n = (b2 - a).normalized().cross(X).normalized()
        if n.z < 0:
            n = -n
        it.append((g.blade(p + n * rr * 0.8, p + n * (rr + 0.1 + 0.03 * i) + (b2 - a).normalized() * -0.04, 0.09, normal=X, belly=0.4, thick=0.01), m.under))
    # the banner it carries
    top = path[4] + Vector((0, 0, -0.07))
    it.append((g.tongue([top, top + Vector((0.01, 0.0, -0.14)), top + Vector((-0.01, 0.02, -0.3)), top + Vector((0.02, 0.0, -0.42))], [0.2, 0.2, 0.18, 0.04], thick=0.06, normal=Y), mat("ribbon"), SOFT))
    it.append((rod(path[3] + Vector((0, 0, -0.045)), path[5] + Vector((0, 0, -0.1)), 0.008), m.under))
    for sg in (1, -1):
        p = path[5] + Vector((sg * 0.1, 0.05, 0.02))
        it += eye(p, 0.036, m, facing=Vector((sg, -0.3, 0.2)))
    strap = [path[1] + Vector((0, 0, 0.02)), Vector((0, 0.1, 0.8)), Vector((0, -0.1, 0.82)), path[5] + Vector((0, 0, 0.1))]
    it.append((g.tube(strap, [0.012] * 4, n=4), mat("leather"), SOFT))
    carry = Vector((0, 0, 0.83))
    it.append((f2.band(carry + Z * 0.03, 0.03, 0.03, 0.008, n=10, u=X, v=Z, sides=4), m.under, ROUND))
    anchors = {"top": Vector((0, 0, 0.76)), "face": path[5] + Vector((0, -0.08, 0.05)), "light": path[-1], "carry": carry + Z * 0.03, "back": path[0]}
    return finish(form_id, it, anchors, ref=0.76)


def build_bell(form_id, level, spec, base, silhouette):
    m = Metals(silhouette, fallback=("metal_iron", "metal_iron_light", "metal_brass"))
    style, bs = gl.opt(spec.get("bell", "hand"))
    if style == "horn":
        return build_horn(form_id, spec, m)
    # the bell itself is cast in the coat's third metal (the brass of an iron-and-brass coat,
    # the copper of a blued one): from here on `main` is the bell's own metal and `trim` its ironwork
    m.main, m.trim = m.trim, m.main
    b = spec.get("build", {})
    bell = Bell(style, bs, m.main)
    pose, amount = gl.opt(spec.get("pose", "hang"), 0.0)
    forward = pose == "forward" and amount >= 0.4
    crown = Vector((0, 0, 1.0))
    rot = Matrix.Rotation(-(math.pi / 2) * amount, 4, "X") if pose == "forward" else (Matrix.Rotation(amount, 4, "Y") if pose == "swing" else Matrix.Rotation(amount, 4, "X"))
    P = Matrix.Translation(crown) @ rot @ Matrix.Translation((0, 0, -bell.H))
    B = Placer(P)
    local = list(bell.items)
    tstyle, ts = gl.opt(spec.get("tongue", "ball"))
    local += bell_tongue(bell, tstyle, ts, m)
    extra, faces = bell_local(spec, m, bell, forward)
    local += extra
    it = put(local, P)
    hang, A = bell_hang(spec, m, bell, crown, P, forward)
    it += hang
    bell_gear(spec, m, it, bell, B, A, crown, forward)
    tilt = b.get("tilt", 0.0)
    if tilt:                        # it tilts with a swell that is not there
        lo, hi = bounds(it)
        T = Matrix.Translation((0, 0, lo.z)) @ Matrix.Rotation(tilt, 4, "Y") @ Matrix.Translation((0, 0, -lo.z))
        it = put(it, T)
        A = {k: (T @ v if isinstance(v, Vector) else v) for k, v in A.items()}
        B = Placer(T @ P)
    face = B(faces[0]) if faces else B(bell.on(bell.H * 0.5, 0.0))
    if "dial" in A:
        face = A["dial"]
    if forward and faces:
        face = (B(faces[0]) + B(faces[1])) / 2 + Vector((0, -0.02, 0))
    anchors = {"top": A["top"], "face": face, "light": B(Vector((0, 0, bell.H * 0.3))), "carry": A["carry"], "back": crown + Y * (bell.R + 0.02) - Z * bell.H * 0.5}
    return finish(form_id, it, anchors, ref=A["top"].z)


# ======================================================================================
# The lines
# ======================================================================================

def _silhouettes(base):
    """form id -> the silhouette it is drawn as (its own, or the nearest one named above it)."""
    out = {}

    def walk(n, sil):
        sil = n.get("silhouette", sil)
        out[n["id"]] = sil
        for key in ("prongs", "finishes"):
            for c in n.get(key, []):
                walk(c, sil)
    walk(base["settled"], base["silhouette"])
    for p in base["paths"]:
        walk(p, base["settled"].get("silhouette", base["silhouette"]))
    return out


_SILS = {}


def _builder(fn):
    def build(form_id, level, spec, base):
        if base["id"] not in _SILS:
            _SILS[base["id"]] = _silhouettes(base)
        kit.reset()
        size = fn(form_id, level, spec, base, _SILS[base["id"]][form_id])
        log(form_id, "%d KB" % size)
    return build


def register(builders):
    global gl
    main = sys.modules.get("__main__")
    gl = main if getattr(main, "BUILDERS", None) is builders else sys.modules["genius_lines"]
    builders["lantern"] = _builder(build_lantern)
    builders["astrolabe"] = _builder(build_astrolabe)
    builders["bell"] = _builder(build_bell)


# ======================================================================================
# The gifts: what a hybrid of one of these wears, bold enough to say whose it is
# ======================================================================================
# A part is built at its socket's origin, for a body of the kit's size (docs/art-bible.md).
#   python tools/blender/lines_items.py gifts

def gift_lantern():
    """The Lantern's: a caged lamp on a hook and two links, a hand tall, its flame the field's.
    Hung from the light's socket (under a beast's neck, at a thing's heart)."""
    brass, iron, dark = mat("metal_brass"), mat("metal_iron"), mat("metal_dark")
    it = [(g.tube([(0, 0, 0.0), (0.018, 0, -0.012), (0.0, 0, -0.03)], [0.006, 0.006, 0.006], n=4), iron)]
    it.append((chain((0, 0, -0.03), (0, 0, -0.085), size=0.016), iron))
    z = -0.09
    it.append((turned([(0.012, z), (0.03, z - 0.012), (0.075, z - 0.05), (0.082, z - 0.058)], n=6), iron))
    it.append((turned([(0.07, z - 0.058), (0.076, z - 0.066), (0.062, z - 0.072)], n=6), brass))
    for k in range(6):
        a = 2 * math.pi * k / 6
        p = Vector((0.06 * math.cos(a), 0.06 * math.sin(a), 0))
        it.append((rod(p + Z * (z - 0.072), p + Z * (z - 0.17), 0.006, n=3), brass))
    it.append((hoop((0, 0, z - 0.12), 0.06, 0.004, n=6), dark))
    it.append((turned([(0.062, z - 0.17), (0.078, z - 0.18), (0.07, z - 0.195), (0.03, z - 0.205)], n=6), brass))
    it.append((ball((0, 0, z - 0.125), 0.034, sub=1, scale=(0.85, 0.85, 1.3)), field("flame", 5.0), ROUND))
    it.append((turned([(0.014, z - 0.165), (0.02, z - 0.158), (0.01, z - 0.15)], n=6), dark))
    return it


def gift_bell():
    """The Bell's: a bell at the throat, as a belled cat wears one, its tongue the field's."""
    brass, iron = mat("metal_brass"), mat("metal_iron")
    it = [(f2.band((0, 0, -0.012), 0.014, 0.014, 0.005, n=8, u=X, v=Z, sides=3), iron)]
    b = Bell("ship", 0.5, brass, n=10)
    it += put(b.items, TR((0, -0.012, -0.03 - b.H), rot=(-0.18, 0, 0)))
    it.append((hoop((0, -0.012, -0.03 - b.H * 0.45), b.r_at(b.H * 0.45) + 0.003, 0.005, n=10), iron, ROUND))
    it.append((ball((0, -0.008, -0.04 - b.H), 0.02, sub=1), field("clapper", 3.4), ROUND))
    return it


def gift_voice():
    """The Bell's: a voice you can see. Rings of sound going out in front of the throat, each
    wider than the last."""
    it = []
    for i, (y, rr) in enumerate(((-0.05, 0.035), (-0.1, 0.06), (-0.155, 0.09))):
        arc = [Vector((rr * math.sin(t), y - 0.02 * math.cos(t), -0.02 + rr * 0.8 * math.cos(t))) for t in [math.radians(-70 + 17.5 * k) for k in range(9)]]
        it.append((g.tube(arc, [0.003] + [0.007 - 0.001 * i] * 7 + [0.003], n=3), field("voice", 2.8 - 0.5 * i)))
    it.append((g.moved(g.lathe([(0.008, 0.0), (0.014, 0.02), (0.03, 0.04), (0.024, 0.04), (0.008, 0.012)], n=7), TR((0, 0, -0.015), rot=(math.pi / 2, 0, 0))), mat("metal_brass"), ROUND))
    return it


def gift_far_eyes():
    """The Astrolabe's: a band of brass across the brow, a great lens on an arm before the
    left eye, a sighting tube over the right."""
    brass, iron = mat("metal_brass"), mat("metal_iron_light")
    band = [(0.085 * math.sin(t), 0.02 - 0.03 * math.cos(t), 0.03) for t in [math.radians(-75 + 15 * i) for i in range(11)]]
    it = [(g.tube(band, [0.008] * 11, n=4, flat=1.8), brass)]
    c = Vector((0.05, -0.05, 0.0))
    it.append((g.tube([(0.06, -0.008, 0.03), (0.07, -0.04, 0.034), c + Vector((0.02, 0.0, 0.03))], [0.006, 0.006, 0.005], n=4), iron))
    it.append((f2.band(c, 0.04, 0.04, 0.007, n=12, u=X, v=Z, sides=4), brass, ROUND))
    it.append((ball(c, 0.036, sub=1, scale=(1, 0.3, 1)), field("lens", 2.6), ROUND))
    it.append((ball(c + Y * -0.012, 0.012, sub=0, scale=(0.5, 0.5, 1.5)), mat("eye_dark")))
    it.append((g.tube([(-0.045, 0.01, 0.004), (-0.05, -0.085, 0.002)], [0.017, 0.022], n=7), brass, ROUND))
    it.append((ball((-0.05, -0.088, 0.002), 0.017, sub=0, scale=(1, 0.4, 1)), field("lens", 2.6)))
    return it


def gift_gears():
    """The Astrolabe's: its works, worn at the breast. A great wheel and a lesser one in
    mesh, a dial over them with one hand, a jewel of the field at the hub."""
    brass, iron, dark = mat("metal_brass"), mat("metal_iron_light"), mat("metal_dark")
    it = [(gear((0, -0.014, 0), 0.085, teeth=12, t=0.022), brass)]
    it.append((gear((0.115, -0.012, -0.06), 0.05, teeth=8, t=0.018), iron))
    it.append((gear((-0.085, -0.012, -0.085), 0.036, teeth=7, t=0.016), dark))
    it.append((f2.band((0, -0.03, 0), 0.055, 0.055, 0.006, n=12, u=X, v=Z, sides=3), iron, ROUND))
    it.append((g.blade((0, -0.034, 0), (0.03, -0.034, 0.045), 0.014, normal=(0, -1, 0), thick=0.004), dark))
    it.append((ball((0, -0.036, 0), 0.018, sub=0), field("hub", 3.2)))
    return it


GIFTS = {"lantern": gift_lantern, "bell": gift_bell, "voice": gift_voice, "far-eyes": gift_far_eyes, "gears": gift_gears}


def build_gifts(only=None):
    for feature, fn in GIFTS.items():
        if only and feature not in only:
            continue
        kit.reset()
        ob = pieces(feature.replace("-", "_"), fn())
        path = os.path.join(kit.OUT, "parts", feature + ".glb")
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        log("wrote", os.path.relpath(path, kit.ROOT), "%d KB" % (os.path.getsize(path) // 1024))


if __name__ == "__main__":
    if sys.argv[1:2] == ["gifts"]:
        build_gifts(set(sys.argv[2:]) or None)
