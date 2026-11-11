"""WILDLINE genius lines: the Fog (docs/genius-lines.md, "The spirits").

Weather that came indoors and stayed. The Starter is a breath of it with two soft eyes; from
there each path gives it a different habit, and a mark of that habit that every form on the
path keeps:

    it wraps and covers (the Fog-shroud's line)     the cowl: the hood of a coat with nobody in it
    it stands where it was left (Lingering Mist's)  square edges, pale bands, and a stone
    it will not be held (Shifting Fog's)            the curl: a tail that is already leaving

Fog has no outline of its own, so each form is given one: rolls of grey, darker under and
paler on top, gathered into a shape, with something in it that is not fog (a post, a mask,
a lamp, a stone) and somewhere on it two eyes.

A Fog's `body` (data/genius-bases/fog.json) names its `plan`; every form is a plan of its own.
In the order of the tree:
    wisp
    coat      layer (mask, horseshoe)    folds (douse, pall)     maw (pool, thick)
    pillar    wall (drift, streamers)    graves (bust, trail)    hoops (edge, curtain)
    swirl     echo (faces, signpost)     frost (hoar, blackice)  hound (flood, storm)
"""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import mat, field
import spirits_kit as sk


def _m(B, role):
    return B.role(role) if role in ("main", "under", "trim") else mat(role)


# --- what fog is made of -------------------------------------------------------------------------
# A roll is not a thing of its own: every roll of a body is gathered, and each part of the body is
# made as one round surface a role (spirits_kit.cloud), so that a bank has one soft outline and
# not a line round every roll. A part breathes (pulse_fog...), and what is on it rides it.

def roll(B, p, r, sc=(1.15, 1.0, 0.65), role="main", turn=0.0, part=""):
    """One roll of it, in a part of the body ("" is the body itself)."""
    B.fog.setdefault(part, {}).setdefault(role, []).append((V(p), r, sc, turn))


def bank(B, c, w, d, h, seed=0.0, dark=False, part="", deep=None):
    """A bank of it about c, w wide, d deep, h high: darker under, paler on top, and its Path's
    colour in it where it is deepest (`deep`: a material; None for none)."""
    c = V(c)
    lo, mid, hi = ("under", "under", "main") if dark else ("under", "main", "trim")
    for i in range(6):
        a = seed + 2 * math.pi * i / 6
        r = 0.29 * w * (0.88 + 0.16 * math.sin(i * 2.1 + seed))
        roll(B, c + Vector((w * 0.31 * math.cos(a), d * 0.31 * math.sin(a), -h * 0.26)), r, (1.0, d / w, h / w), lo, a, part)
    roll(B, c, 0.36 * w, (1.0, d / w, 1.16 * h / w), mid, 0.0, part)
    for i in range(4):
        a = seed + 0.8 + 2 * math.pi * i / 4
        r = 0.27 * w * (0.9 + 0.14 * math.sin(i * 1.3 + seed))
        roll(B, c + Vector((w * 0.26 * math.cos(a), d * 0.26 * math.sin(a), h * 0.04)), r, (1.0, d / w, 1.1 * h / w), mid, a, part)
    for i in range(3):
        a = seed + 0.3 + 2 * math.pi * i / 3
        roll(B, c + Vector((w * 0.14 * math.cos(a), d * 0.14 * math.sin(a), h * 0.3)), 0.22 * w, (1.0, d / w, 1.1 * h / w), hi, a, part)
    if deep:
        for i in range(3):
            a = seed + 1.1 + 2 * math.pi * i / 3
            roll(B, c + Vector((w * 0.36 * math.cos(a), -abs(d * 0.34 * math.sin(a)) - d * 0.06, -h * 0.3)), 0.2 * w, (1.0, d / w, 0.8 * h / w), deep, a, part)


def on(B, geo, material, smooth=None, part=""):
    """Something that lies on a part of the fog and rides it as it breathes (the dark round an eye, a lid)."""
    if geo and geo[0]:
        B.fog_on.setdefault(part, []).append((geo, material, smooth))


def shreds(B, c, r, n=3, seed=0.0, role="main"):
    """Bits of it coming away: smaller and smaller, going up. They rise and fall."""
    geo = None
    for i in range(n):
        a = seed + i * 2.2
        p = V(c) + Vector((r * math.cos(a), r * math.sin(a), 0.03 + 0.06 * i))
        geo = g.merge(geo, g.ico(p, 0.04 - 0.008 * i, sub=1, scale=(1.3, 1.0, 0.7), rot=(0, 0, a)))
    B.nbits += 1
    B.move("bob", "shreds_" + "abcdefgh"[B.nbits % 8], [(geo, _m(B, role), True)], c)


def wisps(B, strands, w=0.05, role="main", what="wisps", pivot=None, swell=0.4):
    """Strands of it trailing off, thin enough at their ends to see past: each a line of points.
    They sway about `pivot` (the first point of the first, if none is given)."""
    geo = None
    for pts in strands:
        geo = g.merge(geo, sk.strand(sk.curve(pts, n=3), w, n=6, swell=swell))
    return B.move("sway", what, [(geo, _m(B, role), True)], strands[0][0] if pivot is None else pivot)


def ragged(B, c, rx, ry, n=5, L=0.16, w=0.045, seed=0.0, role="under", what="ragged", z=0.0, arc=(0.0, 2 * math.pi)):
    """The ragged edge of a bank: strands trailing outward and down from round it."""
    c = V(c)
    strands = []
    for i in range(n):
        a = arc[0] + (arc[1] - arc[0]) * (i + 0.5) / n + 0.3 * math.sin(seed + i * 1.7)
        d = Vector((math.cos(a), math.sin(a), 0))
        b = c + Vector((d.x * rx, d.y * ry, z))
        Li = L * (0.7 + 0.5 * ((i * 5 + int(seed * 3)) % 3) / 2.0)
        strands.append([b - d * 0.04, b + d * Li * 0.5 + Z * 0.012, b + d * Li * 0.85 + Vector((-d.y, d.x, 0)) * Li * 0.25 - Z * 0.02, b + d * Li * 1.15 + Vector((-d.y, d.x, 0)) * Li * 0.5 - Z * 0.035])
    return wisps(B, strands, w, role, what, pivot=c + Z * z)


def moved(B, start, rx=0.0, ry=0.0, rz=0.0, about=(0, 0, 0), shift=(0, 0, 0)):
    """Everything added since `start`, tilted about a point and then shifted."""
    for i in range(start, len(B.items)):
        geo, m, s = B.items[i]
        B.items[i] = (sk.shifted(sk.tilted(geo, rx, ry, rz, about), shift), m, s)


def eyes(B, c, dx, r, style="soft", patch=True, part="", what="eyes", up=None, ride=True):
    """Its eyes, on a face that looks to -Y: two lit places in two darker ones. They blink, and
    ride the part of the fog they are in."""
    c = V(c)
    r = r * 1.25          # larger than they were: a Fog is known by its eyes
    lit, stat = [], []
    if style == "pits":           # two darker places, rimmed, with very little in them
        stat.append((sk.eye_pair(c, dx, r * 1.5, scale=(1.1, 0.4, 1.0), slant=0.0), "void", True))
        rims = None
        for s in (1, -1):
            rims = g.merge(rims, sk.hoop(c + Vector((s * dx, -0.004, 0)), r * 1.75, r * 1.65, r * 0.3, n=10, u=X, v=Z, sides=4))
        stat.append((rims, "veil", True))
        lit.append((sk.eye_pair(c + Vector((0, -r * 0.5, -r * 0.2)), dx, r * 0.6, scale=(1.0, 0.5, 1.0), slant=0.0), field("eyes", 2.6), True))
    else:
        if patch:
            stat.append((sk.eye_pair(c + Vector((0, 0.008, 0)), dx, r * 1.55, scale=(1.15, 0.4, 0.95), slant=0.0), B.under, True))
        if style == "old":            # old grey eyes that count: heavy-lidded
            lit.append((_pair(c + Vector((0, -0.004, -r * 0.2)), dx, r * 0.9, (1.1, 0.5, 0.7), -0.1), field("eyes", 2.4), True))
            lids = None
            for s in (1, -1):
                p = c + Vector((s * dx, -0.008, r * 0.55))
                lids = g.merge(lids, g.tongue([p + Vector((-r * 1.5, 0, -r * 0.2)), p + Vector((0, -0.004, r * 0.3)), p + Vector((r * 1.5, 0, -r * 0.4))], [r * 0.3, r * 1.1, r * 0.3], thick=0.5, normal=(0, -1, 0.3)))
            stat.append((lids, B.trim, True))
        elif style == "shut":
            geo = None
            for s in (1, -1):
                geo = g.merge(geo, g.tongue([c + Vector((s * dx - r * 1.1, -0.008, 0.002)), c + Vector((s * dx, -0.01, -r * 0.3)), c + Vector((s * dx + r * 1.1, -0.008, 0.002))], [r * 0.2, r * 0.5, r * 0.2], thick=0.5, normal=(0, -1, 0.3)))
            lit.append((geo, field("eyes", 2.4), True))
        elif style == "wide":
            lit.append((_pair(c + Vector((0, -0.006, 0)), dx, r * 1.25, (1.0, 0.45, 1.0), 0.0), field("eyes", 2.4), True))
        else:
            lit.append((_pair(c + Vector((0, -0.004, 0)), dx, r, (1.1, 0.5, 0.85), 0.0), field("eyes", 2.4), True))
            lids = None
            for s in (1, -1):       # a lid over each: it is awake, and in no hurry
                p = c + Vector((s * dx, -0.006 - r * 0.25, r * 0.62))
                lids = g.merge(lids, g.tongue([p + Vector((-r * 1.15, r * 0.2, -r * 0.25)), p + Vector((0, 0, r * 0.12)), p + Vector((r * 1.15, r * 0.2, -r * 0.25))], [r * 0.2, r * 0.75, r * 0.2], thick=0.5, normal=(0, -1, 0.3)))
            stat.append((lids, B.under, True))
    mv = B.move("blink", what, lit, c, up=up)
    if ride:
        B.fog_riders.append((mv, part))
        for it in stat:
            on(B, *it, part=part)
    else:
        for it in stat:
            B.add(*it)
    return mv


def _pair(c, dx, r, scale, slant):
    """Two round eyes either side of c (finer than the kit's: an eye's outline is looked at)."""
    geo = None
    for s in (1, -1):
        geo = g.merge(geo, g.ico(V(c) + Vector((s * dx, 0, 0)), r, sub=2, scale=scale, rot=(0, s * -slant, 0)))
    return geo


def finish(B):
    """Make the fog: each part of it one round surface a role, breathing; what lies on it rides it."""
    made = {}
    share = max(1, sum(len(balls) for roles in B.fog.values() for balls in roles.values()))
    for part, roles in B.fog.items():
        items, mid, n = [], Vector((0, 0, 0)), 0
        for role, balls in roles.items():
            keep = int(max(140, B.budget * len(balls) / share))
            geo = sk.cloud([(p, r, sc, turn) for p, r, sc, turn in balls], res=B.res, keep=keep)
            if geo:
                items.append((geo, _m(B, role), True))
            for p, r, sc, turn in balls:
                mid += p
                n += 1
        items += B.fog_on.get(part, [])
        if not items:
            continue
        if part.startswith("still"):
            for it in items:
                B.add(*it)
        else:
            made[part] = B.move("pulse", "fog" + ("_" + part if part else ""), items, mid / max(1, n))
    for part, its in B.fog_on.items():
        if part not in B.fog:
            for it in its:
                B.add(*it)
    for mv, part in B.fog_riders:
        if part in made and mv is not None:
            mv["parent"] = made[part]


# --- what each path keeps ----------------------------------------------------------------------

def cowl(B, c, k=1.0, eye="soft", inside="accent", tails=True, what="eyes"):
    """The hood of a coat with nobody in it, its neck at c: the Fog-shroud's line, and its colour:
    the cloth is its Path's colour, darker without and brighter within, with a thread round the
    opening and two tails of it hanging that sway. Says where its eyes are."""
    c = V(c)
    prof = ((0.0, 0.09, 0.085, 0.0), (0.08, 0.115, 0.125, 0.0), (0.16, 0.1, 0.11, 0.02), (0.22, 0.055, 0.065, 0.05), (0.265, 0.008, 0.008, 0.08))
    B.add(g.loft([g.ring(c + Vector((0, yo * k, z * k)), rx * k, ry * k, n=16, u=X, v=Y, phase=math.pi / 16) for z, rx, ry, yo in prof]), "accent_dark", True)
    f = c + Vector((0, -0.092 * k, 0.092 * k))
    B.add(g.ico(f + Vector((0, 0.012 * k, 0)), 0.09 * k, sub=2, scale=(0.95, 0.42, 1.15)), _m(B, inside), True)
    B.add(g.ico(f, 0.078 * k, sub=2, scale=(0.9, 0.42, 1.14)), "void", True)
    B.add(sk.hoop(f + Vector((0, -0.03 * k, 0)), 0.081 * k, 0.1 * k, 0.009 * k, n=18, u=X, v=Z, sides=5), "accent_light", True)
    e = f + Vector((0, -0.036 * k, 0.008 * k))
    eyes(B, e, 0.033 * k, 0.0155 * k, eye, patch=False, what=what, ride=False)
    if tails:
        strands = []
        for s in (1, -1):
            b = c + Vector((s * 0.07 * k, -0.07 * k, 0.012 * k))
            strands.append([b, b + Vector((s * 0.03, -0.03, -0.07)) * k, b + Vector((s * 0.02, -0.045, -0.16)) * k, b + Vector((s * 0.045, -0.04, -0.25)) * k])
        geo = None
        for pts in strands:
            geo = g.merge(geo, g.tongue(sk.curve(pts, n=2), [0.05 * k, 0.05 * k, 0.046 * k, 0.042 * k, 0.036 * k, 0.03 * k, 0.012 * k], thick=0.3, normal=-Y))
        B.move("sway", "tails" + ("" if what == "eyes" else "_b"), [(geo, "accent", True)], c + Vector((0, -0.07 * k, 0.012 * k)))
    return e


def stone(B, c, w, h, lean=0.0, turn=0.0, thick=0.05, name=True):
    """A round-topped stone standing at c, its face to -Y: Lingering Mist's line. Something was
    here, and its name is in the stone in its Path's colour."""
    geo = g.merge(g.box((0, 0, (h - w * 0.5) * 0.5), (w, thick, h - w * 0.5)),
                  sk.shifted(sk.tilted(sk.disc((0, 0, 0), w * 0.5, thick=thick, n=12), rx=math.pi / 2), (0, thick / 2, h - w * 0.5)))
    B.add(sk.shifted(sk.tilted(geo, ry=lean, rz=turn), c), "stone_grave", False)
    if name:        # what was cut in it, and gilded
        cut = g.merge(g.box((0, -thick / 2 - 0.003, h * 0.62), (w * 0.56, 0.006, w * 0.09)), g.box((0, -thick / 2 - 0.003, h * 0.49), (w * 0.4, 0.006, w * 0.09)),
                      sk.shifted(sk.tilted(sk.hoop((0, 0, 0), w * 0.36, w * 0.36, w * 0.035, n=10, sides=3), rx=math.pi / 2), (0, -thick / 2 - 0.002, h - w * 0.5)))
        B.add(sk.shifted(sk.tilted(cut, ry=lean, rz=turn), c), "accent", False)


def curl(B, c, r, turns=0.9, w=0.07, axis=Y, start=0.0, role="main", rise=0.0, n=9, end=0.25, what=None):
    """A tail of it, curling off: Shifting Fog's line, edged in its colour. It sways."""
    pts = sk.curve(g.spiral(c, r, r * end, turns, rise, n=n, axis=axis, start=start), n=2)
    m = len(pts) - 1
    ws = [w * (1.0 - 0.92 * i / m) for i in range(m + 1)]
    ax = V(axis).normalized()
    cc = V(c)
    edge = []
    for i, p in enumerate(pts):
        out = (p - cc) - ax * (p - cc).dot(ax)
        out = out.normalized() if out.length > 1e-5 else X.copy()
        edge.append(p + out * (ws[i] * 0.92))
    B.ncurl += 1
    B.move("sway", what or ("curl_" + "abcdefgh"[B.ncurl % 8]), [(g.tube(pts, ws, n=7, flat=0.7), _m(B, role), True), (g.tube(edge[:-1], [max(0.0035, x * 0.16) for x in ws[:-1]], n=4), "accent_light", True)], pts[0])


def _done(B, top, front, mid, half, eye=None, crown=None):
    """Its frame. `top` is the height it is stood to; `crown` is where its head really ends, where that is lower."""
    B.frame(top, front=front, mid=mid, half=half)
    if crown is not None:
        B.socket("socket_head", crown)
    if eye is not None:
        B.socket("socket_eyes", V(eye) + Vector((0, -0.02, 0)))


# --- the Starter ---------------------------------------------------------------------------------

def plan_wisp(B):
    """A breath of fog that stays when the window is shut."""
    roll(B, (0, 0, 0.34), 0.14, (1.15, 1.0, 0.88), "main")
    roll(B, (0.1, 0.03, 0.27), 0.08, (1.2, 1.0, 0.7), "under")
    roll(B, (-0.07, 0.04, 0.44), 0.08, (1.2, 1.0, 0.7), "trim")
    B.add(g.tongue([(0.05, 0.08, 0.3), (0.16, 0.16, 0.22), (0.12, 0.25, 0.13), (0.03, 0.27, 0.1)], [0.13, 0.08, 0.04, 0.004], thick=0.6), B.main)
    eyes(B, (0, -0.128, 0.35), 0.05, 0.024)
    shreds(B, (0.04, 0.02, 0.5), 0.07, n=2, seed=1.0, role="trim")
    _done(B, 0.56, -0.14, 0.34, 0.15, (0, -0.128, 0.35), crown=(0, 0, 0.5))


# --- it wraps and covers ---------------------------------------------------------------------

def plan_coat(B):
    """It hangs round you like a second coat, grey and close."""
    prof = [(0.16, 0.2, 0.15), (0.3, 0.17, 0.125), (0.44, 0.15, 0.11), (0.56, 0.19, 0.115), (0.6, 0.12, 0.09)]
    B.add(g.loft([g.ring((0, 0.005, z), rx, ry, n=10, u=X, v=Y, phase=math.pi / 10) for z, rx, ry in prof]), B.main)
    e = cowl(B, (0, 0, 0.6))
    for s in (1, -1):
        # a sleeve, a cuff with nothing in it, and the coat's front edge
        B.add(g.tongue([(s * 0.18, 0, 0.55), (s * 0.25, -0.03, 0.42), (s * 0.27, -0.06, 0.26)], [0.1, 0.105, 0.085], thick=0.55, normal=(s, 0, 0.3)), B.main)
        B.add(g.ico((s * 0.27, -0.065, 0.25), 0.036, sub=1, scale=(1, 0.8, 0.5)), B.under)
        B.add(g.tongue([(s * 0.05, -0.105, 0.58), (s * 0.075, -0.125, 0.42), (s * 0.06, -0.15, 0.2)], [0.03, 0.04, 0.03], thick=0.4, normal=(s * 0.3, -1, 0)), B.trim)
    for i in range(7):        # where a hem should be, it goes back to weather
        a = 2 * math.pi * i / 7
        roll(B, (0.19 * math.cos(a), 0.14 * math.sin(a), 0.14 + 0.02 * (i % 2)), 0.075, (1.2, 1.0, 0.6), "under" if i % 2 else "main", a)
    shreds(B, (0, 0.02, 0.6), 0.2, n=3, seed=0.4)
    _done(B, 0.86, -0.15, 0.42, 0.22, e)


def plan_layer(B):
    """It lies knee-deep and level over open ground, with the air standing clear above it."""
    B.add(g.lathe([(0.0, 0.1), (0.4, 0.1), (0.47, 0.16), (0.42, 0.235), (0.0, 0.25)], n=14), B.main)
    for i in range(8):
        a = 2 * math.pi * i / 8
        roll(B, (0.41 * math.cos(a), 0.41 * math.sin(a), 0.12), 0.11, (1.3, 1.0, 0.45), "under", a)
    for i in range(5):
        a = 0.4 + 2 * math.pi * i / 5
        roll(B, (0.22 * math.cos(a), 0.2 * math.sin(a), 0.245), 0.13, (1.3, 1.0, 0.14), "trim", a)
    # the hood of the coat it was, standing up out of it
    for s in (1, -1):
        roll(B, (s * 0.12, -0.02, 0.27), 0.08, (1.2, 1.0, 0.6), "main")
    e = cowl(B, (0.0, -0.04, 0.27), 1.1)
    # and what stands clear above it
    posts = None
    for i, x in enumerate((-0.36, -0.22, -0.08)):
        posts = g.merge(posts, sk.post((x, 0.2, 0.2), 0.22 + 0.03 * (i % 2), r=0.02, n=5))
    posts = g.merge(posts, g.tube([(-0.38, 0.2, 0.36), (-0.06, 0.2, 0.35)], [0.012, 0.012], n=4))
    B.add(posts, "timber", False)
    _done(B, 0.7, -0.17, 0.27, 0.36, e, crown=(0, 0.04, 0.56))


def plan_mask(B):
    """A blank grey face forms in it when it is looked at, and is nobody's."""
    bank(B, (0, 0.02, 0.38), 0.5, 0.38, 0.5, seed=0.3)
    prof = ((0.0, 0.16, 0.14, 0.0), (0.1, 0.17, 0.16, 0.0), (0.2, 0.13, 0.13, 0.03), (0.27, 0.06, 0.07, 0.06), (0.31, 0.01, 0.01, 0.09))
    B.add(g.loft([g.ring((0, yo, 0.58 + z), rx, ry, n=10, u=X, v=Y, phase=math.pi / 10) for z, rx, ry, yo in prof]), B.main)
    f = Vector((0, -0.15, 0.66))
    B.add(g.ico(f + Vector((0, 0.03, 0)), 0.12, sub=1, scale=(0.9, 0.4, 1.2)), B.under)
    B.add(sk.hoop(f + Vector((0, -0.012, 0)), 0.108, 0.142, 0.014, n=10, u=X, v=Z, sides=4), B.trim, True)
    # the face: a pale blank with two slits and no mouth
    B.add(g.ico(f + Vector((0, -0.012, 0)), 0.092, sub=1, scale=(0.84, 0.3, 1.22)), "mask_pale")
    B.add(sk.eye_pair(f + Vector((0, -0.038, 0.028)), 0.03, 0.017, scale=(1.25, 0.4, 0.45), slant=0.0), "void")
    # what it is covering for: a lantern shuttered to a slit, and the nose of a boat
    B.add(g.tongue([(0.18, -0.02, 0.56), (0.25, -0.1, 0.56), (0.27, -0.12, 0.5)], [0.1, 0.07, 0.04], thick=0.6), B.main)
    B.extend(sk.lantern(Vector((0.27, -0.12, 0.5)), 0.06, lit=False))
    B.add(g.box((0.27, -0.153, 0.41), (0.034, 0.01, 0.012)), field("slit", 2.6))
    B.add(g.tongue([(-0.36, -0.02, 0.2), (-0.26, -0.16, 0.18), (-0.1, -0.32, 0.2), (-0.02, -0.4, 0.25)], [0.05, 0.16, 0.14, 0.02], thick=0.6, normal=Z), "timber", False)
    shreds(B, (0, 0.02, 0.62), 0.26, n=4, seed=0.9)
    _done(B, 0.9, -0.18, 0.5, 0.26, f + Vector((0, -0.04, 0.028)))


def plan_horseshoe(B):
    """It comes in low and quickly from all sides at once. There are old grey eyes in it that count."""
    seats = []
    for i in range(9):
        a = math.pi * (-0.32 + 1.64 * i / 8)
        p = Vector((0.38 * math.cos(a), 0.3 * math.sin(a) + 0.04, 0.26 + 0.04 * math.sin(i * 1.3)))
        r = 0.13 + 0.025 * math.sin(i * 2.0)
        roll(B, p, r, (1.1, 1.0, 0.8), "main" if i % 2 else "under", a)
        roll(B, p + Vector((0, 0, r * 0.62)), r * 0.7, (1.1, 1.0, 0.6), "trim", a)
        seats.append((p, r))
    B.add(sk.disc((0, 0.04, 0.15), 0.34, thick=0.03, n=12, squash=0.8), B.under)
    e = cowl(B, (0, 0.26, 0.36), 1.6, "old")
    for i, off in ((0, 0.0), (1, 0.05), (7, -0.05), (8, 0.0)):
        p, r = seats[i]
        eyes(B, p + Vector((off, -r * 0.9, 0.02)), 0.036, 0.014, "old")
    for s in (1, -1):       # the piles of the harbour it came into
        B.add(sk.post((s * 0.5, -0.2, 0.08), 0.4, r=0.03, n=6), "timber", False)
        B.add(sk.hoop((s * 0.5, -0.2, 0.4), 0.04, 0.04, 0.008, n=8, sides=3), "cord", False)
    _done(B, 0.78, -0.33, 0.34, 0.46, e)


def plan_folds(B):
    """It moves in slow folds like water, and things passing through it come out slower."""
    roll(B, (0, 0.08, 0.38), 0.26, (1.2, 0.6, 1.1), "under")
    for i, (z, w, m) in enumerate(((0.56, 0.3, "trim"), (0.46, 0.38, "main"), (0.36, 0.44, "under"), (0.26, 0.4, "main"), (0.17, 0.3, "under"))):
        pts = [Vector((x * w, -0.05 * (1 - abs(x)) - 0.018 * i, z - 0.07 * (1 - x * x))) for x in (-1.0, -0.5, 0.0, 0.5, 1.0)]
        B.add(g.tongue(pts, [0.1, 0.2, 0.22, 0.2, 0.1], thick=0.55, normal=-Y), _m(B, m))
    for s in (1, -1):
        B.add(g.tongue([(s * 0.3, 0.0, 0.62), (s * 0.4, 0.0, 0.46), (s * 0.44, 0.02, 0.28), (s * 0.36, 0.03, 0.12)], [0.1, 0.14, 0.12, 0.02], thick=0.6, normal=(s, 0, 0.3)), B.main)
        roll(B, (s * 0.15, 0.04, 0.6), 0.1, (1.2, 1.0, 0.7), "main")
    e = cowl(B, (0, 0.03, 0.6), 1.1)
    for s in (1, -1):       # the scroll of a wave at its foot
        pts = g.spiral((s * 0.3, -0.08, 0.16), 0.08, 0.02, 0.8, 0.0, n=8, axis=Y, start=math.pi if s > 0 else 0.0)
        B.add(g.tube(pts, [0.04, 0.04, 0.036, 0.032, 0.028, 0.022, 0.016, 0.01, 0.004], n=5, flat=1.5), B.trim)
    _done(B, 0.89, -0.16, 0.44, 0.4, e)


def plan_douse(B):
    """Rime at its edges and steam at its heart. It hisses, faintly, all the time."""
    bank(B, (0, 0, 0.36), 0.54, 0.42, 0.34, seed=0.6)
    e = cowl(B, (0, -0.02, 0.46), 1.25)
    rime = None
    for i in range(13):         # an icicle fringe, all the way round
        a = 2 * math.pi * i / 13
        d = Vector((math.cos(a), math.sin(a) * 0.8, 0))
        b0 = Vector((0, 0, 0.3)) + d * 0.27
        rime = g.merge(rime, sk.crystal(b0, b0 + d * (0.1 + 0.04 * (i % 3)) + Z * (-0.1 - 0.03 * (i % 2)), 0.022, n=4))
    for i in range(6):          # and on the hood's rim
        a = math.pi * (0.15 + 0.7 * i / 5)
        d = Vector((math.cos(a), 0, math.sin(a)))
        b0 = Vector((0, -0.165, 0.575)) + Vector((d.x * 0.1, 0, d.z * 0.125))
        rime = g.merge(rime, sk.crystal(b0, b0 + d * 0.05 + Vector((0, -0.02, 0)), 0.012, n=4))
    B.add(rime, "ice_pale", False)
    for i, (x, y, z, r) in enumerate(((0.03, 0.13, 0.84, 0.07), (-0.05, 0.15, 0.96, 0.055), (0.03, 0.16, 1.06, 0.04))):
        B.add(sk.puff((x, y, z), r, k=2, seed=i * 1.3), "steam")       # the steam of it, going up behind the hood
    # what it has just put out
    B.add(g.tube([(0.1, -0.36, 0.16), (0.24, -0.2, 0.24), (0.36, -0.06, 0.28)], [0.022, 0.024, 0.02], n=5), "soot", False)
    B.add(g.ico((0.09, -0.37, 0.155), 0.03, sub=0), "ash_dark", False)
    B.add(sk.puff((0.08, -0.38, 0.22), 0.035, k=2, seed=0.5), "steam")
    _done(B, 0.8, -0.22, 0.42, 0.3, e)


def plan_pall(B):
    """A heavy grey that lies like a blanket, with a cold still place at the centre."""
    def rr(w, d, z, n=12, wob=0.0):
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            cx, cy = math.cos(a), math.sin(a)
            r = (1.0 / max(abs(cx) / w, abs(cy) / d)) * (1.0 - 0.28 * abs(cx * cy)) * (1.0 + wob * (1 if i % 2 else -1))
            pts.append(Vector((cx * r, cy * r, z)))
        return pts
    B.add(g.loft([rr(0.4, 0.3, 0.06, wob=0.09), rr(0.34, 0.26, 0.2, wob=0.05), rr(0.3, 0.22, 0.36), rr(0.26, 0.19, 0.4), rr(0.08, 0.06, 0.43)]), B.main)
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        d = Vector((math.cos(a) * 0.4, math.sin(a) * 0.3, 0))
        B.add(g.blade(Vector((0, 0, 0.1)) + d * 0.9, Vector((0, 0, 0.04)) + d * 1.16, 0.14, normal=Z, belly=0.4), B.under)
    for sx in (1, -1):
        for sy in (1, -1):
            roll(B, (sx * 0.32, sy * 0.24, 0.09), 0.055, (1, 1, 0.9), "trim")
    B.add(sk.hoop((0, 0, 0.3), 0.325, 0.245, 0.006, n=14, sides=3), B.trim, False)
    # the cold still place, and the hood bowed over it
    c = Vector((0, -0.16, 0.52))
    B.add(g.ico(c, 0.066, sub=0, scale=(1, 1, 1.25)), field("core", 3.2), False)
    B.add(sk.hoop((c.x, c.y, 0.425), 0.1, 0.08, 0.014, n=10, sides=4), "ice_pale", False)
    n = len(B.items)
    e = cowl(B, (0, 0.09, 0.39), 1.35, "old")
    moved(B, n, rx=-0.1, about=(0, 0.09, 0.39))
    _done(B, 0.76, -0.24, 0.3, 0.36, e + Vector((0, -0.03, -0.01)), crown=(0, 0.14, 0.74))


def plan_maw(B):
    """A low dense grey with a hollow in it like an open mouth. Candles dim when it passes."""
    prof = ((0.1, 0.3, 0.26, 0.0), (0.26, 0.34, 0.3, 0.0), (0.42, 0.28, 0.27, 0.03), (0.54, 0.15, 0.17, 0.09), (0.62, 0.02, 0.02, 0.17))
    B.add(g.loft([g.ring((0, 0.03 + yo, z), rx, ry, n=12, u=X, v=Y, phase=math.pi / 12) for z, rx, ry, yo in prof]), B.main)
    for i in range(7):
        a = 2 * math.pi * i / 7
        roll(B, (0.3 * math.cos(a), 0.03 + 0.27 * math.sin(a), 0.13), 0.13, (1.2, 1.0, 0.6), "under", a)
    # the hood is all mouth now
    m = Vector((0, -0.2, 0.27))
    B.add(g.ico(m, 0.17, sub=1, scale=(1.3, 0.5, 0.9)), "void")
    B.add(sk.hoop(m + Vector((0, -0.07, 0)), 0.215, 0.15, 0.028, n=12, u=X, v=Z, sides=5), B.trim, True)
    e = Vector((0, -0.215, 0.475))
    eyes(B, e, 0.075, 0.018, "soft")
    # the candle it has just passed
    B.extend(sk.candle((0.36, -0.3, 0.12), 0.1, 0.024, lit=0.0))
    B.add(g.tongue([(0.36, -0.3, 0.235), (0.39, -0.32, 0.25), (0.44, -0.34, 0.245)], [0.014, 0.02, 0.003], thick=0.5), field("flame", 1.6))
    B.add(sk.disc((0.36, -0.3, 0.11), 0.05, thick=0.01, n=7), "metal_dark", False)
    _done(B, 0.66, -0.26, 0.34, 0.34, e, crown=(0, 0.1, 0.56))


def plan_pool(B):
    """It lies along the floor, darker than fog should be, with two darker places that watch upward."""
    B.add(sk.disc((0, 0, 0.05), 0.46, thick=0.07, n=14, squash=0.72), B.under)
    for i in range(6):
        a = 0.5 + 2 * math.pi * i / 6
        roll(B, (0.3 * math.cos(a), 0.2 * math.sin(a), 0.11), 0.15, (1.3, 1.0, 0.28), "main" if i % 2 else "under", a)
    # the hood, fallen on its back
    h = Vector((0, -0.16, 0.16))
    roll(B, h, 0.17, (1.15, 1.0, 0.55), "main")
    B.add(g.tongue([h + Vector((0, 0.1, 0.04)), h + Vector((0.03, 0.26, 0.02)), h + Vector((0.08, 0.4, -0.04))], [0.2, 0.12, 0.01], thick=0.5, normal=Z), B.main)
    e = h + Vector((0, -0.1, 0.055))
    n = len(B.items)
    eyes(B, e, 0.062, 0.028, "pits")
    moved(B, n, rx=-0.6, about=e)
    B.add(sk.hoop((0, 0, 0.1), 0.47, 0.34, 0.006, n=18, sides=3), "veil", False)      # where it ends: you would not see it else
    # the place it is the bottom of: a set of timbers, and a lamp that went out
    B.add(g.merge(sk.post((-0.28, 0.24, 0.08), 0.42, r=0.03, n=5, cap=False), sk.post((0.28, 0.24, 0.08), 0.42, r=0.03, n=5, cap=False), g.box((0, 0.24, 0.52), (0.7, 0.07, 0.06))), "timber", False)
    lamp = sk.lantern(Vector((0, 0, 0.13)), 0.07, lit=False)
    for geo, m in lamp:
        B.add(sk.shifted(sk.tilted(geo, ry=1.35, about=(0, 0, 0.06)), (0.3, -0.3, 0.05)), m, False)
    _done(B, 0.66, -0.3, 0.16, 0.4, e, crown=h + Vector((0, 0, 0.1)))


def plan_thick(B):
    """It is thick enough to push against. Hands moved through it leave a slow wake."""
    bank(B, (0, 0.04, 0.42), 0.46, 0.38, 0.6, seed=0.2, dark=True)
    e = cowl(B, (0, -0.02, 0.64), 1.3)
    for s in (1, -1):     # two hands of it, webbed, pushing
        wr = Vector((s * 0.3, -0.24, 0.42))
        B.add(g.tongue([(s * 0.2, 0.0, 0.52), (s * 0.3, -0.1, 0.46), wr], [0.12, 0.1, 0.08], thick=0.6, normal=(s, 0, 0.3)), B.main)
        palm = wr + Vector((0, -0.035, 0.03))
        B.add(g.ico(palm, 0.06, sub=1, scale=(1.0, 0.4, 1.1)), B.trim)
        tips = [wr + Vector((s * math.sin(a) * 0.15, -0.06, 0.04 + math.cos(a) * 0.15)) for a in (-0.6, -0.2, 0.2, 0.6)]
        fan, web = None, None
        for t in tips:
            fan = g.merge(fan, g.tongue([palm, t], [0.03, 0.012], thick=0.5, normal=-Y))
        for t0, t1 in zip(tips, tips[1:]):
            web = g.merge(web, g.tongue([palm, (t0 + t1) * 0.43 + palm * 0.14], [0.02, (t1 - t0).length * 0.8], thick=0.08, normal=-Y))
        B.add(fan, B.trim)
        B.add(web, B.under, False)
        # the wake it leaves
        pts = g.spiral((s * 0.3, 0.2, 0.26), 0.1, 0.03, 0.9, 0.0, n=8, axis=Z, start=0.0 if s > 0 else math.pi)
        B.add(g.tube(pts, [0.05, 0.05, 0.045, 0.04, 0.034, 0.026, 0.018, 0.01, 0.004], n=5, flat=0.6), B.main)
    bub = None
    for x, y, z, r in ((0.2, -0.1, 0.86, 0.028), (-0.22, -0.04, 0.94, 0.02), (0.26, 0.02, 1.0, 0.016), (-0.16, -0.12, 1.04, 0.012)):
        bub = g.merge(bub, g.ico((x, y, z), r, sub=1))
    B.add(bub, B.trim)
    _done(B, 0.98, -0.22, 0.5, 0.32, e)


# --- it stands where it was left -------------------------------------------------------------

def plan_pillar(B):
    """It hangs in one spot in still air and does not thin."""
    B.add(g.lathe([(0.0, 0.1), (0.13, 0.15), (0.17, 0.3), (0.14, 0.5), (0.16, 0.66), (0.1, 0.8), (0.0, 0.86)], n=12), B.main)
    for z, r in ((0.3, 0.172), (0.52, 0.146), (0.67, 0.162)):
        B.add(g.lathe([(r, -0.03), (r + 0.012, 0.0), (r, 0.03)], n=12, centre=(0, 0, z), caps=False), B.trim)
    for i in range(5):
        a = 2 * math.pi * i / 5
        roll(B, (0.13 * math.cos(a), 0.13 * math.sin(a), 0.14), 0.07, (1.2, 1.0, 0.6), "under", a)
    # it listens: one side of it opens like a horn
    c = Vector((0.13, 0.0, 0.62))
    B.add(g.loft([g.ring(c + X * off, r, r * 1.1, n=10, u=Y, v=Z) for off, r in ((0.0, 0.03), (0.06, 0.06), (0.13, 0.11), (0.18, 0.17))], caps=False), B.trim)
    B.add(g.loft([g.ring(c + X * off, r, r * 1.1, n=10, u=Y, v=Z) for off, r in ((0.18, 0.17), (0.17, 0.14), (0.07, 0.05))], caps=False), B.under)
    e = Vector((0, -0.15, 0.59))
    eyes(B, e, 0.045, 0.018)
    stone(B, (-0.22, -0.16, 0.08), 0.12, 0.26, lean=0.08)
    _done(B, 0.86, -0.17, 0.5, 0.2, e)


def plan_wall(B):
    """A flat grey wall across a gap, square at the edges, like a door with no handle."""
    B.add(g.box((0, 0, 0.47), (0.56, 0.09, 0.7)), B.main, False)
    B.add(g.merge(g.box((0, -0.047, 0.62), (0.4, 0.01, 0.24)), g.box((0, -0.047, 0.3), (0.4, 0.01, 0.24))), B.under, False)
    B.add(g.box((0, 0, 0.83), (0.6, 0.11, 0.03)), B.trim, False)
    for s in (1, -1):
        B.add(g.merge(g.box((s * 0.36, 0, 0.42), (0.11, 0.11, 0.64)), g.box((s * 0.36, 0, 0.75), (0.14, 0.14, 0.04)), g.cone((s * 0.36, 0, 0.77), (s * 0.36, 0, 0.86), 0.075, n=4)), "stone_grave", False)
    for i in range(6):
        roll(B, (-0.3 + 0.12 * i, -0.04 + 0.05 * (i % 2), 0.13), 0.075, (1.2, 1.0, 0.55), "under" if i % 2 else "trim")
    e = Vector((0, -0.054, 0.66))
    eyes(B, e, 0.06, 0.018, patch=False)
    _done(B, 0.86, -0.08, 0.46, 0.4, e)


def plan_drift(B):
    """It lies banked along the post like snow against a wall, with the lamp showing through as a low sun."""
    for i in range(8):
        t = i / 7
        x = -0.44 + 0.66 * t
        r = 0.1 + 0.11 * t
        roll(B, (x, 0.02 * math.sin(i * 2.0), 0.12 + 0.28 * t), r, (1.2, 1.3, 0.85), "main" if i % 2 else "under", i)
        roll(B, (x + 0.02, -0.02, 0.12 + 0.28 * t + r * 0.6), r * 0.72, (1.2, 1.3, 0.6), "trim", i)
    B.add(g.merge(g.box((0.36, 0.1, 0.4), (0.1, 0.5, 0.6)), g.box((0.36, 0.1, 0.715), (0.13, 0.54, 0.03))), "stone_grave", False)
    B.add(g.tube([(0.08, 0.02, 0.1), (0.08, 0.02, 0.9)], [0.02, 0.018], n=6), "metal_iron", False)
    B.add(g.tube([(0.08, 0.02, 0.88), (0.08, -0.06, 0.94), (0.08, -0.14, 0.92)], [0.012, 0.012, 0.012], n=4), "metal_iron", False)
    B.extend(sk.lantern(Vector((0.08, -0.14, 0.92)), 0.065, glow="lamp", strength=3.4))
    # the lamp, seen through it: a low sun
    sun = Vector((0.06, -0.2, 0.46))
    B.add(g.ico(sun, 0.1, sub=1, scale=(1.0, 0.25, 1.0)), field("sun", 2.2))
    B.add(sk.hoop(sun + Vector((0, -0.01, 0)), 0.15, 0.15, 0.006, n=14, u=X, v=Z, sides=3), field("halo", 1.4))
    e = Vector((-0.24, -0.16, 0.3))
    eyes(B, e, 0.045, 0.016)
    _done(B, 0.92, -0.2, 0.4, 0.44, e, crown=(-0.1, 0, 0.56))


def plan_streamers(B):
    """It comes in off the water in long finned streamers."""
    first = None
    for j, (x, z, L, w) in enumerate(((0.0, 0.5, 1.0, 1.0), (0.26, 0.34, 0.8, 0.8), (-0.24, 0.3, 0.74, 0.75))):
        pts = [Vector((x + 0.04 * math.sin(i * 1.3 + j), -0.4 * L + 0.8 * L * i / 5, z + 0.04 * math.sin(i * 1.9 + j))) for i in range(6)]
        B.add(g.tongue(pts, [0.14 * w, 0.2 * w, 0.2 * w, 0.16 * w, 0.1 * w, 0.01], thick=0.7, normal=Z), _m(B, "main" if j == 0 else "under"))
        fins = None
        for i in range(1, 5):
            b0 = pts[i] + Vector((0, 0, 0.055 * w))
            fins = g.merge(fins, g.blade(b0, b0 + Vector((0, 0.12, 0.11 * w)), 0.09 * w, normal=X, belly=0.35))
        B.add(fins, B.trim)
        head = pts[0] + Vector((0, -0.03, 0.0))
        roll(B, head, 0.1 * w, (1.0, 1.2, 0.85), "main")
        e = head + Vector((0, -0.105 * w, 0.02))
        eyes(B, e, 0.036 * w, 0.014 * w)
        first = first or e
    # the quay it comes in over
    B.add(g.box((0.0, 0.36, 0.14), (0.7, 0.16, 0.16)), "stone_grave", False)
    B.add(g.box((0.0, 0.36, 0.23), (0.74, 0.2, 0.03)), "stone_grave", False)
    B.add(sk.hoop((0.28, 0.25, 0.13), 0.04, 0.04, 0.009, n=8, u=X, v=Z, sides=4), "metal_iron", False)
    salt = None
    for x, y, z in ((0.1, 0.1, 0.66), (-0.12, 0.3, 0.6), (0.2, 0.3, 0.5), (-0.3, 0.0, 0.46)):
        salt = g.merge(salt, g.ico((x, y, z), 0.012, sub=0))
    B.add(salt, "bone", False)
    _done(B, 0.72, -0.46, 0.4, 0.36, first, crown=(0, -0.4, 0.6))


def plan_graves(B):
    """Figures stand in it at the edge of sight."""
    bank(B, (0, 0, 0.2), 0.74, 0.5, 0.2, seed=0.5)
    for x, y, hh in ((-0.2, 0.16, 0.52), (0.04, 0.22, 0.62), (0.26, 0.14, 0.48)):       # a robe, a bowed head, and no more than that
        B.add(g.lathe([(0.0, 0.0), (0.09, 0.02), (0.07, hh * 0.42), (0.078, hh * 0.66), (0.03, hh * 0.76)], n=8, centre=(x, y, 0.16)), B.trim)
        B.add(g.ico((x, y - 0.012, 0.16 + hh * 0.86), 0.052, sub=1, scale=(0.9, 0.95, 1.1)), B.trim)
    stone(B, (-0.3, -0.2, 0.1), 0.17, 0.36, lean=0.16)
    e = Vector((0.08, -0.25, 0.25))
    eyes(B, e, 0.05, 0.016, "old")
    _done(B, 0.78, -0.27, 0.26, 0.4, e)


def plan_bust(B):
    """It holds a lit shape for a breath after a shade has gone: a shoulder, a turned head."""
    bank(B, (0, 0.06, 0.44), 0.52, 0.36, 0.62, seed=0.8)
    # the shape it is holding: a head turned away, a neck, a shoulder
    y = -0.2
    pts = [Vector((x, y, z)) for x, z in ((0.19, 0.3), (0.12, 0.36), (0.05, 0.4), (0.04, 0.46), (0.085, 0.52), (0.09, 0.6), (0.04, 0.66), (-0.03, 0.66), (-0.08, 0.61), (-0.1, 0.55), (-0.13, 0.52),
                                           (-0.09, 0.5), (-0.08, 0.45), (-0.05, 0.41), (-0.1, 0.37), (-0.2, 0.31))]
    B.add(g.tube(pts, [0.008] * len(pts), n=3), field("shade", 3.0))
    B.add(g.ico((0, y + 0.03, 0.56), 0.085, sub=1, scale=(1.0, 0.3, 1.25)), B.trim)
    B.add(g.ico((0, y + 0.04, 0.37), 0.13, sub=1, scale=(1.5, 0.3, 0.6)), B.trim)
    for s in (1, -1):
        roll(B, (s * 0.2, y + 0.0, 0.3), 0.09, (1.0, 0.8, 0.9), "main")
    e = Vector((0, -0.12, 0.76))
    eyes(B, e, 0.055, 0.016, "old")
    for i, x in enumerate((-0.22, 0.0, 0.22)):      # the names
        stone(B, (x, -0.3, 0.08), 0.13, 0.15 + 0.02 * (i % 2), lean=0.06 * (i - 1), thick=0.04)
    _done(B, 0.86, -0.22, 0.5, 0.28, e)


def plan_trail(B):
    """It hangs in a line along the ground, and old prints show in it as if just made."""
    for i in range(7):
        t = i / 6
        r = 0.13 - 0.05 * t
        roll(B, (0.05 * math.sin(i * 1.4), -0.3 + 0.9 * t, 0.2 + 0.03 * math.sin(i)), r, (1.1, 1.5, 0.75), "main" if i % 2 else "under")
    head = Vector((0, -0.4, 0.4))
    B.add(g.tongue([(0, -0.3, 0.22), (0, -0.37, 0.32), head], [0.2, 0.17, 0.16], thick=0.8, normal=-Y), B.main)
    roll(B, head, 0.12, (1.0, 1.0, 0.9), "trim")
    e = head + Vector((0, -0.11, 0.01))
    eyes(B, e, 0.05, 0.017, "wide")
    pads, toes = None, None
    for i in range(5):
        p = Vector((0.17 * (1 if i % 2 else -1), -0.5 + 0.22 * i, 0.07))
        pads = g.merge(pads, g.ico(p, 0.03, sub=1, scale=(1.0, 1.1, 0.3)))
        for dx in (-0.03, 0.0, 0.03):
            toes = g.merge(toes, g.ico(p + Vector((dx, -0.045, 0)), 0.012, sub=0, scale=(1, 1, 0.4)))
    B.add(pads, field("print", 2.8))
    B.add(toes, field("print", 2.8))
    # the waymark at the far end of it
    cairn = None
    for i, (r, z) in enumerate(((0.08, 0.1), (0.065, 0.19), (0.05, 0.27), (0.03, 0.33))):
        cairn = g.merge(cairn, g.ico((0.02 * (-1) ** i, 0.62, z), r, sub=0, scale=(1.2, 1.0, 0.6), rot=(0, 0, i * 1.1)))
    B.add(cairn, "stone_grave", False)
    _done(B, 0.64, -0.5, 0.26, 0.24, e, crown=head + Vector((0, 0, 0.11)))


def plan_hoops(B):
    """It is thinner than it was and very still."""
    c = Vector((0, 0, 0.5))
    for u, v in ((X, Y), (X, Z), (Y, Z)):
        B.add(sk.hoop(c, 0.3, 0.3, 0.014, n=18, u=u, v=v, sides=4), B.trim, True)
    B.add(sk.tilted(sk.hoop(c, 0.24, 0.24, 0.008, n=16, sides=3), rx=0.7, ry=0.3, about=c), "veil", False)
    roll(B, c, 0.09, (1.0, 1.0, 0.9), "main")
    e = c + Vector((0, -0.086, 0.01))
    eyes(B, e, 0.03, 0.012, "shut")
    # nothing in it moves: a plumb line, hanging dead straight
    B.add(g.tube([(0, 0, 0.8), (0, 0, 0.59)], [0.004, 0.004], n=3), "cord", False)
    B.add(g.tube([(0, 0, 0.41), (0, 0, 0.32)], [0.004, 0.004], n=3), "cord", False)
    B.add(g.tube([(0, 0, 0.32), (0, 0, 0.29), (0, 0, 0.22)], [0.012, 0.03, 0.002], n=6), "stone_grave", False)
    _done(B, 0.82, -0.3, 0.5, 0.3, e)


def plan_edge(B):
    """A clean grey wall, straight as a rule, with the air stood still along it."""
    B.add(g.box((0, 0.02, 0.4), (0.96, 0.05, 0.54)), B.main, False)
    B.add(g.box((0, 0.02, 0.68), (0.98, 0.07, 0.03)), B.trim, False)
    B.add(g.box((0, 0.02, 0.14), (0.98, 0.07, 0.03)), B.under, False)
    arches = None
    for i in range(4):
        x = -0.33 + 0.22 * i
        arches = g.merge(arches, sk.arc((x, -0.012, 0.16), 0.085, 0.38, 0.0, math.pi, 0.01, n=8, u=X, v=Z, sides=3))
    B.add(arches, B.trim, False)
    stakes, flags = None, None
    for x in (-0.22, 0.22, 0.44):
        stakes = g.merge(stakes, sk.post((x, -0.16, 0.1), 0.3, r=0.012, n=4))
        flags = g.merge(flags, g.blade((x, -0.16, 0.38), (x + 0.09, -0.17, 0.35), 0.06, normal=Y, belly=0.2))
    B.add(stakes, "timber", False)
    B.add(flags, "mask_pale")
    stone(B, (-0.44, -0.14, 0.1), 0.13, 0.3)
    e = Vector((0, -0.01, 0.56))
    eyes(B, e, 0.07, 0.018, "shut", patch=False)
    _done(B, 0.72, -0.06, 0.4, 0.5, e)


def plan_curtain(B):
    """It parts in the middle like a curtain, and a single clear eye of open air looks through."""
    for s in (1, -1):
        for j, (x, m) in enumerate(((0.44, "under"), (0.34, "main"), (0.25, "trim"))):
            pts = [Vector((s * x, 0.0, 0.86)), Vector((s * (x - 0.02), -0.01 * j, 0.62)), Vector((s * (x + 0.03), -0.01 * j, 0.46)), Vector((s * (x + 0.07), 0.0, 0.3)), Vector((s * (x + 0.1), 0.0, 0.14))]
            B.add(g.tongue(pts, [0.11, 0.12, 0.08, 0.13, 0.15], thick=0.6, normal=-Y), _m(B, m))
        B.add(sk.hoop((s * 0.37, -0.01, 0.45), 0.15, 0.06, 0.016, n=12, sides=4), "cord", False)
    pts = [Vector((x * 0.5, -0.03, 0.9 - 0.06 * (1 - x * x))) for x in (-1.0, -0.5, 0.0, 0.5, 1.0)]
    B.add(g.tongue(pts, [0.1, 0.14, 0.16, 0.14, 0.1], thick=0.5, normal=-Y), B.main)
    # the eye of open air
    c = Vector((0, 0.0, 0.52))
    loop = [c + Vector((0.19 * math.cos(a), 0, 0.115 * math.sin(a) * (1.0 - 0.25 * abs(math.cos(a))))) for a in [2 * math.pi * i / 16 for i in range(17)]]
    B.add(g.tube(loop, [0.012] * 17, n=4, caps=False), B.trim, True)
    B.add(g.ico(c, 0.06, sub=1, scale=(1.0, 0.4, 1.0)), field("eyes", 3.4))
    B.add(g.ico(c + Vector((0, -0.02, 0)), 0.024, sub=1, scale=(1.0, 0.5, 1.0)), "void")
    # the sill it hangs over
    B.add(g.merge(g.box((0, 0.0, 0.08), (1.12, 0.2, 0.06)), g.box((0, -0.02, 0.03), (1.2, 0.28, 0.05))), "stone_grave", False)
    _done(B, 0.96, -0.06, 0.52, 0.5, c)


# --- it will not be held ---------------------------------------------------------------------

def plan_swirl(B):
    """It will not hold a shape. Look at one part and the rest has moved."""
    head = Vector((-0.12, 0, 0.5))
    roll(B, head, 0.17, (1.1, 1.0, 0.9), "main")
    roll(B, head + Vector((0.02, 0.02, 0.12)), 0.11, (1.2, 1.0, 0.6), "trim")
    pts = [head + Vector((0.08, 0.02, -0.02)), Vector((0.14, 0.06, 0.5)), Vector((0.32, 0.08, 0.38)), Vector((0.3, 0.06, 0.2)), Vector((0.12, 0.02, 0.12)), Vector((-0.02, 0.0, 0.18)), Vector((0.0, 0.0, 0.27))]
    B.add(g.tongue(pts, [0.24, 0.22, 0.18, 0.14, 0.1, 0.06, 0.01], thick=0.7, normal=-Y), B.main)
    B.add(g.tongue([p + Vector((0, 0.03, 0.0)) for p in pts[1:6]], [0.26, 0.22, 0.17, 0.12, 0.04], thick=0.5, normal=-Y), B.under)
    for i, (x, y, z, r) in enumerate(((0.46, 0.1, 0.5, 0.07), (0.56, 0.14, 0.42, 0.05), (0.62, 0.2, 0.5, 0.035))):
        roll(B, (x, y, z), r, (1.2, 1.0, 0.7), "trim" if i % 2 else "main")
    e = head + Vector((-0.03, -0.15, 0.02))
    eyes(B, e, 0.05, 0.018)
    shreds(B, (0.2, 0.05, 0.56), 0.16, n=3, seed=0.2)
    _done(B, 0.68, -0.17, 0.42, 0.34, e)


def _mouth(B, c, r, facing=(0, -1, 0)):
    """A round mouth in it, open, speaking."""
    c, d = V(c), V(facing).normalized()
    side = d.cross(Z).normalized()
    B.add(g.ico(c - d * r * 0.2, r, sub=1, scale=(1.0, 0.5, 1.0), rot=(0, 0, math.atan2(-d.x, d.y))), "void")
    B.add(sk.hoop(c + d * r * 0.3, r * 1.05, r * 1.05, r * 0.26, n=10, u=side, v=Z, sides=5), B.trim, True)


def plan_echo(B):
    """It has a voice, and the voice is always the last speaker's, from the wrong side of the room."""
    bank(B, (-0.2, 0.0, 0.42), 0.36, 0.3, 0.38, seed=0.4)
    curl(B, (-0.2, 0.02, 0.2), 0.11, turns=0.8, w=0.08, start=0.6, role="under")
    e = Vector((-0.2, -0.15, 0.52))
    eyes(B, e, 0.045, 0.015)
    _mouth(B, (-0.2, -0.155, 0.4), 0.05)
    # the other end of it, over there, saying it back
    c2 = Vector((0.32, 0.06, 0.62))
    roll(B, c2, 0.12, (1.1, 1.0, 0.85), "main")
    roll(B, c2 + Vector((0.02, 0.0, 0.08)), 0.08, (1.2, 1.0, 0.6), "trim")
    curl(B, c2 + Vector((0.06, 0.02, -0.16)), 0.09, turns=0.8, w=0.07, start=2.4, role="under")
    d = Vector((-0.5, -0.86, 0)).normalized()
    _mouth(B, c2 + Vector((-0.07, -0.1, 0.0)), 0.042, facing=d)
    B.add(g.tongue([Vector((-0.06, 0.04, 0.5)), Vector((0.08, 0.08, 0.6)), Vector((0.2, 0.07, 0.62))], [0.06, 0.03, 0.05], thick=0.5), B.under)
    rings = None
    o = c2 + Vector((-0.09, -0.13, 0.0))
    side = d.cross(Z).normalized()
    for i, rr in enumerate((0.07, 0.11, 0.15)):
        rings = g.merge(rings, sk.hoop(o + d * (0.03 + 0.065 * i), rr, rr, 0.007, n=12, u=side, v=Z, sides=3))
    B.add(rings, B.trim, False)
    _done(B, 0.76, -0.18, 0.46, 0.4, e, crown=(-0.2, 0, 0.62))


def _face(B, c, s, lit=2.4):
    """A face formed in it: a brow, a nose, two hollows, a mouth."""
    c = V(c)
    roll(B, c + Vector((0, 0.03, 0)), 0.13 * s, (0.95, 0.5, 1.25), "main")
    roll(B, c + Vector((0, -0.03 * s, 0.07 * s)), 0.1 * s, (1.3, 0.45, 0.32), "trim")
    B.add(g.tongue([c + Vector((0, -0.065 * s, 0.06 * s)), c + Vector((0, -0.095 * s, 0.0)), c + Vector((0, -0.07 * s, -0.03 * s))], [0.02 * s, 0.045 * s, 0.03 * s], thick=0.8, normal=X), B.trim)
    B.add(sk.eye_pair(c + Vector((0, -0.058 * s, 0.03 * s)), 0.05 * s, 0.03 * s, scale=(1.2, 0.4, 0.7), slant=-0.1), B.under)
    B.add(sk.eye_pair(c + Vector((0, -0.068 * s, 0.026 * s)), 0.05 * s, 0.012 * s, scale=(1.0, 0.5, 1.0), slant=0.0), field("eyes", lit))
    B.add(g.ico(c + Vector((0, -0.058 * s, -0.075 * s)), 0.03 * s, sub=1, scale=(1.6, 0.5, 0.5)), B.under)


def plan_faces(B):
    """A face forms in it that is nearly somebody you know, and then a second behind the first."""
    bank(B, (0, 0.06, 0.38), 0.44, 0.34, 0.5, seed=0.9)
    curl(B, (0.12, 0.04, 0.2), 0.15, turns=0.85, w=0.1, start=0.4, role="under")
    c = Vector((-0.03, -0.14, 0.5))
    _face(B, c, 1.2)
    _face(B, Vector((0.17, 0.04, 0.78)), 0.8)
    B.add(g.tongue([Vector((0.1, 0.06, 0.56)), Vector((0.15, 0.08, 0.66)), Vector((0.17, 0.08, 0.72))], [0.16, 0.12, 0.1], thick=0.7, normal=-Y), B.main)
    # it beckons
    pts = [Vector((-0.2, -0.02, 0.4)), Vector((-0.34, -0.16, 0.38)), Vector((-0.38, -0.3, 0.46)), Vector((-0.33, -0.36, 0.56))]
    B.add(g.tongue(pts, [0.12, 0.09, 0.07, 0.05], thick=0.7), B.main)
    B.add(sk.fingers(pts[-1], Vector((0.4, 0.3, 0.8)), n=4, L=0.09, spread=0.02, r=0.016, hook=-0.3), B.trim)
    _done(B, 0.92, -0.24, 0.5, 0.3, c + Vector((0, -0.08, 0.03)))


def plan_signpost(B):
    """It was foggy on their road. It was not on yours."""
    B.add(g.tube([(0, 0, 0.08), (0.01, 0, 0.86)], [0.03, 0.024], n=6), "timber", False)
    B.add(g.cone((0.01, 0, 0.86), (0.01, 0, 0.92), 0.03, n=6), "timber", False)
    for z, a, L, blank in ((0.76, 0.3, 0.3, False), (0.64, 2.6, 0.26, True), (0.52, -1.2, 0.28, False)):
        d = Vector((math.cos(a), math.sin(a), 0))
        R = Matrix.Rotation(a, 3, "Z")
        mid = Vector((0.01, 0, z)) + d * (L / 2 + 0.02)
        B.add(g.box(mid, (L, 0.016, 0.07), rot=R), "ash_pale" if blank else "timber", False)
        B.add(g.cone(mid + d * (L / 2), mid + d * (L / 2 + 0.06), 0.04, n=4), "ash_pale" if blank else "timber", False)
        if not blank:
            n = d.cross(Z)
            B.add(g.merge(g.box(mid + n * 0.01 + Z * 0.012, (L * 0.7, 0.006, 0.008), rot=R), g.box(mid + n * 0.01 - Z * 0.014, (L * 0.5, 0.006, 0.008), rot=R)), "soot", False)
    # the ledger of arrivals, hung on it
    B.extend(sk.book(Vector((0.0, -0.05, 0.36)), 0.14, rot=(-0.15, 0, 0.1), cover="leather"))
    B.add(g.tube([(0.0, -0.03, 0.5), (0.0, -0.05, 0.43)], [0.005, 0.005], n=3), "cord", False)
    curl(B, (0.0, 0, 0.12), 0.26, turns=1.6, w=0.09, axis=Z, start=2.2, rise=0.56, n=14, end=0.4)
    for i in range(6):
        a = 2 * math.pi * i / 6
        roll(B, (0.26 * math.cos(a), 0.22 * math.sin(a), 0.14), 0.11, (1.2, 1.0, 0.6), "under" if i % 2 else "main", a)
    cob = None
    for i in range(5):      # the road, as far as it goes
        cob = g.merge(cob, g.ico((0.04 * (-1) ** i, -0.3 - 0.1 * i, 0.07), 0.05 - 0.006 * i, sub=0, scale=(1.2, 1.0, 0.3), rot=(0, 0, i)))
    B.add(cob, "stone_hide", False)
    h = Vector((-0.2, -0.16, 0.22))
    roll(B, h, 0.1, (1.1, 1.0, 0.9), "main")
    e = h + Vector((0, -0.09, 0.01))
    eyes(B, e, 0.04, 0.015)
    _done(B, 0.92, -0.26, 0.4, 0.32, e, crown=(0.01, 0, 0.92))


def plan_frost(B):
    """White needles on every edge of it, growing while you watch."""
    for i, (x, y, z, r) in enumerate(((0.0, 0.0, 0.36, 0.16), (0.16, 0.04, 0.3, 0.12), (-0.17, 0.02, 0.3, 0.13), (0.03, 0.02, 0.5, 0.11))):
        roll(B, (x, y, z), r, (1.15, 1.0, 0.75), "main" if i % 2 == 0 else "under", i)
    curl(B, (0.22, 0.04, 0.3), 0.12, turns=0.8, w=0.08, start=3.4, role="under")
    needles = None
    c = Vector((0, 0.01, 0.38))
    for i in range(22):
        a, b = i * 2.399, -0.3 + 1.2 * ((i * 7) % 10) / 10.0
        d = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b) * 0.9, math.sin(b)))
        b0 = c + Vector((d.x * 0.26, d.y * 0.2, d.z * 0.17))
        needles = g.merge(needles, sk.crystal(b0, b0 + d * (0.1 + 0.05 * (i % 3)), 0.016, n=4))
    B.add(needles, B.trim, False)
    frost = None
    for i in range(9):
        a = 2 * math.pi * i / 9
        frost = g.merge(frost, g.blade((0.06 * math.cos(a), 0.06 * math.sin(a), 0.2), (0.3 * math.cos(a + 0.12), 0.3 * math.sin(a + 0.12), 0.17 + 0.012 * (i % 3)), 0.07, normal=(0, 0, 1), belly=0.55))
    B.add(frost, B.trim, False)
    e = Vector((0, -0.15, 0.38))
    eyes(B, e, 0.05, 0.016, "wide")
    _done(B, 0.64, -0.18, 0.38, 0.26, e)


def _feather(root, tip, w, n=5):
    """A feather of ice: a shaft, and barbs either side."""
    root, tip = V(root), V(tip)
    d = tip - root
    side = d.cross(Y)
    side = side.normalized() if side.length > 1e-5 else X
    geo = g.tube([root, root + d * 0.5, tip], [w * 0.16, w * 0.12, w * 0.02], n=4)
    for i in range(n):
        t = 0.2 + 0.7 * i / (n - 1)
        p = root + d * t
        L = w * (1.0 - 0.6 * abs(t - 0.45))
        for s in (1, -1):
            geo = g.merge(geo, g.blade(p, p + side * s * L + d.normalized() * L * 0.5, w * 0.3, normal=Y, belly=0.3))
    return geo


def plan_hoar(B):
    """Long white feathers of ice with a cold at the root."""
    root = Vector((-0.06, 0, 0.22))
    for i, (a, L) in enumerate(((-0.75, 0.42), (-0.4, 0.56), (-0.05, 0.68), (0.3, 0.76), (0.65, 0.72), (1.0, 0.6), (1.3, 0.46))):
        tip = root + Vector((math.sin(a) * L, 0.06 * math.cos(i * 1.5), math.cos(a) * L))
        B.add(_feather(root + Vector((math.sin(a) * 0.04, 0, 0.03)), tip, 0.12), _m(B, "trim" if i % 2 == 0 else "main"), False)
    B.add(g.ico(root + Vector((0, -0.02, 0.02)), 0.065, sub=1, scale=(1, 0.8, 1.2)), field("core", 3.6))
    ring = None
    for i in range(7):
        a = 2 * math.pi * i / 7
        d = Vector((math.cos(a), math.sin(a), 0))
        ring = g.merge(ring, sk.crystal(root + d * 0.05, root + d * 0.14 + Z * -0.12, 0.022, n=4))
    B.add(ring, B.under, False)
    e = root + Vector((0, -0.078, 0.03))
    B.add(sk.eye_pair(e, 0.027, 0.012, scale=(1.2, 0.5, 0.6), slant=0.2), "void")
    for i in range(5):
        a = 2 * math.pi * i / 5
        roll(B, (root.x + 0.16 * math.cos(a), 0.12 * math.sin(a), 0.1), 0.06, (1.2, 1.0, 0.5), "under", a)
    _done(B, 0.98, -0.12, 0.4, 0.3, e)


def plan_blackice(B):
    """Clear and dark and smooth as glass, lying flat."""
    def slab(r, n, phase, thick, role, rx=0.0, ry=0.0, at=(0, 0, 0)):
        """A plate of it, and the white line of its edge, which is all of it you see."""
        rim = g.ring((0, 0, thick), r * 0.95, r * 0.95, n=n, phase=phase)
        for geo, m in ((g.lathe([(r, 0.0), (r * 0.95, thick), (0.0, thick * 1.1)], n=n, phase=phase), _m(B, role)), (g.tube(rim + [rim[0]], 0.006, n=3), mat("steam"))):
            B.add(sk.shifted(sk.tilted(geo, rx=rx, ry=ry), at), m, False)
    slab(0.46, 7, 0.3, 0.036, "under", at=(0, 0, 0.05))
    # slabs of it heaved up
    slab(0.3, 5, 0.9, 0.03, "main", rx=-0.95, ry=0.2, at=(-0.14, 0.24, 0.26))
    slab(0.18, 4, 0.4, 0.025, "main", rx=-0.6, ry=-0.5, at=(0.3, 0.16, 0.17))
    cracks = None
    for a, L in ((0.3, 0.4), (1.5, 0.3), (2.6, 0.42), (3.9, 0.36), (5.1, 0.3)):
        p1 = Vector((math.cos(a) * L, math.sin(a) * L, 0.094))
        mid = p1 * 0.5 + Vector((-math.sin(a) * 0.05, math.cos(a) * 0.05, 0))
        cracks = g.merge(cracks, g.tube([Vector((0.02, -0.02, 0.094)), mid, p1], [0.006, 0.005, 0.002], n=3))
    B.add(cracks, B.trim, False)
    e = Vector((0.02, -0.26, 0.1))
    B.add(sk.eye_pair(e, 0.06, 0.03, scale=(1.2, 0.9, 0.2), slant=0.0), field("eyes", 2.4))
    for i, (x, y) in enumerate(((0.3, -0.2), (-0.34, -0.1), (0.1, 0.3))):
        B.add(sk.crystal((x, y, 0.08), (x * 1.1, y * 1.1, 0.2 + 0.05 * i), 0.03, n=4), B.trim, False)
    _done(B, 0.62, -0.3, 0.12, 0.4, e, crown=(-0.14, 0.2, 0.5))


def plan_hound(B):
    """It runs low and fast across open ground on long streaming legs, ahead of any wind."""
    roll(B, (0, -0.12, 0.5), 0.16, (0.85, 1.3, 1.0), "main")           # a deep chest
    roll(B, (0, 0.16, 0.51), 0.11, (0.8, 1.7, 0.8), "under")            # and not much behind it
    roll(B, (0, 0.0, 0.6), 0.09, (0.8, 2.6, 0.45), "trim")
    head = Vector((0, -0.37, 0.62))
    B.add(g.tube([(0, -0.2, 0.56), (0, -0.3, 0.61), head], [0.09, 0.07, 0.06], n=6), B.main, True)
    roll(B, head, 0.085, (0.85, 1.25, 0.85), "main")
    B.add(g.tongue([head + Vector((0, -0.06, -0.01)), head + Vector((0, -0.15, -0.03)), head + Vector((0, -0.21, -0.045))], [0.1, 0.07, 0.03], thick=0.75, normal=Z), B.main)
    for s in (1, -1):
        B.add(g.blade(head + Vector((s * 0.05, 0.03, 0.05)), head + Vector((s * 0.08, 0.22, 0.12)), 0.06, normal=(s, 0, 1), belly=0.3), B.trim)
        # the legs: reaching in front, streaming behind
        B.add(g.tube([(s * 0.09, -0.16, 0.42), (s * 0.1, -0.3, 0.3), (s * 0.1, -0.35, 0.15), (s * 0.1, -0.52, 0.04)], [0.05, 0.035, 0.024, 0.004], n=5), B.main, True)
        B.add(g.tube([(s * 0.09, 0.2, 0.44), (s * 0.11, 0.3, 0.27), (s * 0.11, 0.48, 0.2), (s * 0.1, 0.7, 0.06)], [0.055, 0.04, 0.026, 0.004], n=5), B.under, True)
    curl(B, (0.0, 0.42, 0.54), 0.1, turns=0.7, w=0.08, axis=X, start=2.6, role="main")
    e = head + Vector((0, -0.085, 0.035))
    B.add(sk.eye_pair(e, 0.04, 0.018, scale=(1.0, 0.9, 0.7), slant=0.25), field("eyes", 2.8))
    streaks = None
    for x, z in ((0.2, 0.3), (-0.22, 0.38)):
        streaks = g.merge(streaks, g.tongue([(x, 0.1, z), (x, 0.36, z + 0.02), (x, 0.62, z)], [0.004, 0.03, 0.004], thick=0.3, normal=Z))
    B.add(streaks, "veil")
    _done(B, 0.74, -0.5, 0.48, 0.2, e, crown=head + Vector((0, 0.02, 0.08)))


def plan_flood(B):
    """Brown water, knee-deep, with the fog standing on it. Roots and fence-posts show through."""
    B.add(g.lathe([(0.44, 0.06), (0.4, 0.1), (0.26, 0.2), (0.12, 0.27), (0.0, 0.29)], n=12), B.main)
    B.add(g.lathe([(0.5, 0.05), (0.46, 0.068), (0.0, 0.07)], n=12), B.under)
    for r, z in ((0.34, 0.145), (0.2, 0.245)):
        B.add(sk.hoop((0, 0, z), r, r, 0.006, n=16, sides=3), B.trim, False)
    posts = None
    for i, (x, y, lean) in enumerate(((-0.34, -0.12, 0.1), (-0.12, -0.2, -0.06), (0.12, -0.24, 0.12))):
        posts = g.merge(posts, g.tube([(x, y, 0.08), (x + lean * 0.3, y, 0.42 + 0.03 * i)], [0.024, 0.02], n=5))
    posts = g.merge(posts, g.tube([(-0.32, -0.12, 0.34), (-0.13, -0.2, 0.36), (0.14, -0.24, 0.35)], [0.012, 0.012, 0.012], n=4))
    B.add(posts, "timber", False)
    roots = None
    for a, rr in ((0.6, 0.3), (1.6, 0.34), (2.5, 0.3), (-0.4, 0.36)):
        d = Vector((math.cos(a), math.sin(a), 0))
        roots = g.merge(roots, g.tube([d * (rr - 0.14) + Z * 0.16, d * rr + Z * 0.26, d * (rr + 0.12) + Z * 0.08], [0.02, 0.016, 0.006], n=4))
    B.add(roots, B.mark("reeds", mat("reed")), False)
    # the fog, standing on it, and already going
    for i, (x, y, z, r) in enumerate(((0.0, 0.04, 0.46, 0.15), (0.17, 0.06, 0.4, 0.1), (-0.16, 0.08, 0.42, 0.11), (0.02, 0.04, 0.58, 0.09))):
        B.add(g.ico((x, y, z), r, sub=1, scale=(1.2, 1.0, 0.6), rot=(0, 0, i)), mat("mist" if i % 2 == 0 else "mist_pale"))
    curl(B, (0.2, 0.06, 0.52), 0.1, turns=0.8, w=0.07, start=3.0, role="mist")
    e = Vector((0.0, -0.3, 0.19))
    B.add(sk.eye_pair(e, 0.05, 0.017, scale=(1.1, 0.6, 0.7), slant=0.0), field("eyes", 2.8))
    _done(B, 0.7, -0.32, 0.3, 0.44, e, crown=(0, 0.04, 0.66))


def plan_storm(B):
    """A grey wall with a bright ring turning inside it, and light flickering behind."""
    for i in range(6):
        a = 2 * math.pi * i / 6
        roll(B, (0.34 * math.cos(a), 0.2 * math.sin(a), 0.36), 0.2, (1.2, 1.0, 0.7), "under", a)
    roll(B, (0, 0.02, 0.56), 0.26, (1.1, 0.8, 1.1), "main")
    roll(B, (0.14, 0.03, 0.72), 0.2, (1.1, 0.8, 0.9), "main")
    roll(B, (-0.14, 0.03, 0.74), 0.19, (1.1, 0.8, 0.9), "under")
    # the anvil of it
    B.add(g.lathe([(0.0, 0.84), (0.34, 0.86), (0.54, 0.93), (0.58, 0.98), (0.48, 1.03), (0.0, 1.05)], n=12), B.trim)
    for i in range(7):
        a = 2 * math.pi * i / 7
        roll(B, (0.48 * math.cos(a), 0.4 * math.sin(a), 0.97), 0.11, (1.3, 1.0, 0.5), "main" if i % 2 else "trim", a)
    curl(B, (0.5, 0.0, 0.84), 0.12, turns=0.8, w=0.09, start=1.2, role="main")
    # the ring, in the hollow of it
    c = Vector((0, -0.21, 0.58))
    B.add(g.ico(c + Vector((0, 0.07, 0)), 0.15, sub=1, scale=(1.0, 0.45, 1.0)), "void")
    B.add(sk.tilted(sk.hoop(c, 0.11, 0.11, 0.014, n=14, u=X, v=Z, sides=4), rz=0.3, ry=0.2, about=c), field("ring", 3.4))
    e = c + Vector((0, 0.0, 0.21))
    eyes(B, e, 0.075, 0.018, "wide")
    bolt = None
    for x0, y0 in ((0.22, -0.1), (-0.26, -0.04)):
        p = Vector((x0, y0, 0.3))
        pts = [p, p + Vector((0.05, 0, -0.08)), p + Vector((-0.02, 0, -0.13)), p + Vector((0.04, 0, -0.2)), p + Vector((0.0, 0, -0.27))]
        bolt = g.merge(bolt, g.tube(pts, [0.012, 0.01, 0.009, 0.007, 0.002], n=3))
    B.add(bolt, field("bolt", 4.2))
    rain = None
    for i in range(9):
        x, y = -0.36 + 0.09 * i, 0.1 * math.sin(i * 1.7)
        rain = g.merge(rain, g.tube([(x, y, 0.26), (x - 0.05, y, 0.06)], [0.004, 0.003], n=3))
    B.add(rain, "veil", False)
    _done(B, 1.05, -0.24, 0.56, 0.5, e)


PLANS = {"wisp": plan_wisp, "coat": plan_coat, "layer": plan_layer, "mask": plan_mask, "horseshoe": plan_horseshoe, "folds": plan_folds, "douse": plan_douse,
         "pall": plan_pall, "maw": plan_maw, "pool": plan_pool, "thick": plan_thick, "pillar": plan_pillar, "wall": plan_wall, "drift": plan_drift,
         "streamers": plan_streamers, "graves": plan_graves, "bust": plan_bust, "trail": plan_trail, "hoops": plan_hoops, "edge": plan_edge, "curtain": plan_curtain,
         "swirl": plan_swirl, "echo": plan_echo, "faces": plan_faces, "signpost": plan_signpost, "frost": plan_frost, "hoar": plan_hoar, "blackice": plan_blackice,
         "hound": plan_hound, "flood": plan_flood, "storm": plan_storm}


def build(form_id, level, spec, base):
    B = sk.Body(form_id, level, spec, base)
    B.fog, B.fog_on, B.fog_riders, B.nbits, B.ncurl = {}, {}, [], 0, 0
    B.budget, B.res = 1500, 0.04          # how many corners its fog may have, and how fine it is cut
    plan = spec.get("plan", "wisp")
    if plan not in PLANS:
        sk.log("no such plan", plan, "on", form_id)
        plan = "wisp"
    PLANS[plan](B)
    finish(B)
    B.export()
