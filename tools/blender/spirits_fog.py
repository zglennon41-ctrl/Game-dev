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

Fog looks like fog (the second pass): a roll is not a thing of its own, and each part of a body
is made as one round surface a role (spirits_kit.cloud), which breathes; its edge is ragged
with strands that sway; its eyes blink; and each path's colour is in what its fog carries and
wears (the cowl, the stones and lamps, the edge of the curl), with a roll of it in the fog
itself where the fog is deepest. A form that lies on a floor carries the floor.

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
            roll(B, c + Vector((w * 0.36 * math.cos(a), -abs(d * 0.32 * math.sin(a)) - d * 0.03, -h * 0.32)), 0.16 * w, (1.0, d / w, 0.7 * h / w), deep, a, part)


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


def eyes(B, c, dx, r, style="soft", patch=True, part="", what="eyes", up=None, ride=True, tilt=0.0):
    """Its eyes, on a face that looks to -Y (or, tilted, up out of a floor: tilt -1.57 is straight
    up): two lit places in two darker ones. They blink, and ride the part of the fog they are in."""
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
            stat.append((_pair(c + Vector((0, 0.014, 0)), dx, r * 1.5, (1.15, 0.28, 0.95), 0.0), B.under, True))
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
    if tilt:
        lit = [(sk.tilted(it[0], rx=tilt, about=c),) + tuple(it[1:]) for it in lit]
        stat = [(sk.tilted(it[0], rx=tilt, about=c),) + tuple(it[1:]) for it in stat]
        up = Vector((0, -math.sin(tilt), math.cos(tilt)))
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
            geo = sk.cloud(balls, res=B.res, keep=keep)
            if geo:
                items.append((geo, _m(B, role), True))
            for b in balls:
                if len(b) < 5:
                    mid += b[0]
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
    if not B.items and made:        # a body is one thing that stands and others that move: where all of it moves, a grain of it stands, inside
        B.add(g.ico(next(iter(made.values()))["pivot"], 0.012, sub=0), B.under, True)


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


def hanging(B, at, L=0.1, what="under"):
    """Strands of it hanging under the ground a form carries, so that the ground reads as carried."""
    at = [V(p) for p in at]
    strands = [[p, p + Vector((0.012, 0.01, -L * 0.5)), p + Vector((-0.012, 0.02, -L * (0.8 + 0.25 * (i % 2))))] for i, p in enumerate(at)]
    wisps(B, strands, w=0.045, role="under", what=what, pivot=sum(at, Vector((0, 0, 0))) / len(at), swell=0.2)


def chain(B, pts, r0, r1, sc=(1.0, 1.0, 0.8), roles=("main", "under"), part="", n=None):
    """A line of rolls from the first point to the last, r0 at one end and r1 at the other: a streamer, a limb, a drift."""
    pts = sk.curve(pts, n=2) if len(pts) > 2 else [V(p) for p in pts]
    if n:
        pts = [pts[int(round(i * (len(pts) - 1) / (n - 1)))] for i in range(n)]
    m = len(pts) - 1
    for i, p in enumerate(pts):
        roll(B, p, r0 + (r1 - r0) * i / max(1, m), sc, roles[i % len(roles)], i * 1.3, part)


# --- the Starter ---------------------------------------------------------------------------------

def plan_wisp(B):
    """A breath of fog that stays when the window is shut."""
    roll(B, (0, 0, 0.34), 0.14, (1.15, 1.0, 0.88), "main")
    roll(B, (0.1, 0.03, 0.27), 0.085, (1.2, 1.0, 0.7), "under")
    roll(B, (-0.07, 0.04, 0.44), 0.085, (1.2, 1.0, 0.7), "trim")
    roll(B, (-0.11, 0.0, 0.29), 0.07, (1.1, 1.0, 0.8), "main")
    wisps(B, [[(0.05, 0.08, 0.3), (0.16, 0.16, 0.22), (0.12, 0.25, 0.13), (0.03, 0.27, 0.07)], [(-0.07, 0.07, 0.27), (-0.15, 0.13, 0.19), (-0.1, 0.21, 0.11)]], w=0.11, what="tail")
    e = (0, -0.15, 0.355)
    eyes(B, e, 0.052, 0.024)
    shreds(B, (0.04, 0.02, 0.5), 0.07, n=2, seed=1.0, role="trim")
    _done(B, 0.56, -0.14, 0.34, 0.15, e, crown=(0, 0, 0.5))


# --- it wraps and covers ---------------------------------------------------------------------

def plan_coat(B):
    """It hangs round you like a second coat, grey and close: a coat of fog, the cowl of it cloth."""
    for z, r, m in ((0.5, 0.15, "main"), (0.4, 0.14, "under"), (0.3, 0.155, "main"), (0.2, 0.17, "under")):
        roll(B, (0, 0.01, z), r, (1.15, 0.85, 0.75), m)
    roll(B, (0, 0.0, 0.57), 0.13, (1.5, 0.8, 0.5), "trim")                      # the shoulders
    for s in (1, -1):       # the sleeves, and nothing in the cuffs
        chain(B, [(s * 0.17, 0, 0.55), (s * 0.24, -0.03, 0.42), (s * 0.26, -0.06, 0.28)], 0.065, 0.055, (1, 1, 1.2), ("main", "trim"))
        B.add(g.ico((s * 0.262, -0.075, 0.225), 0.036, sub=2, scale=(1, 0.8, 0.5)), "void", True)
    deep(B, (0, -0.07, 0.3), 0.1, (0.7, 0.5, 1.6))
    e = cowl(B, (0, 0, 0.6))
    ragged(B, (0, 0.01, 0.16), 0.17, 0.13, n=7, L=0.15, w=0.06, z=0.0, what="hem")
    shreds(B, (0, 0.02, 0.6), 0.2, n=3, seed=0.4)
    _done(B, 0.86, -0.15, 0.42, 0.22, e)


def deep(B, p, r, sc=(1.2, 1.0, 0.6), part="", step="accent_dark"):
    """Its Path's colour, in the fog itself where the fog is deepest."""
    roll(B, p, r, sc, step, 0.0, part)


def sod(B, c, r, squash=0.8, tufts=5, seed=0.0):
    """A piece of open ground: earth, and a little grass through whatever lies on it."""
    c = V(c)
    B.add(g.ico(c + Z * -0.03, r, sub=2, scale=(1.0, squash, 0.1)), "earth_grey", True)
    B.add(g.ico(c + Vector((0.02, 0.01, -0.06)), r * 0.78, sub=1, scale=(1.0, squash, 0.16)), "stone_dark", False)
    tuft = None
    for i in range(tufts):
        a = seed + i * 2.4
        p = c + Vector((r * 0.8 * math.cos(a), r * 0.8 * squash * math.sin(a), 0.0))
        for j in (-1, 0, 1):
            tuft = g.merge(tuft, g.blade(p + Vector((j * 0.012, 0, 0)), p + Vector((j * 0.035, 0.01 * j, 0.09 + 0.02 * (i % 2))), 0.018, normal=Y))
    B.add(tuft, "grass_dew", False)


def plan_layer(B):
    """It lies knee-deep and level over open ground, with the air standing clear above it. The ground goes with it."""
    sod(B, (0, 0, 0.1), 0.5, squash=0.82, tufts=0)
    B.add(g.lathe([(0.0, 0.1), (0.4, 0.1), (0.455, 0.17), (0.41, 0.238), (0.0, 0.25)], n=20), B.main, True)       # level as a table
    for i in range(10):
        a = 2 * math.pi * i / 10
        roll(B, (0.42 * math.cos(a), 0.36 * math.sin(a), 0.15), 0.1 + 0.02 * (i % 2), (1.3, 1.0, 0.5), "under" if i % 2 else "main", a)
    for i in range(4):
        a = 0.9 + 2 * math.pi * i / 4
        roll(B, (0.2 * math.cos(a), 0.18 * math.sin(a), 0.235), 0.13, (1.4, 1.0, 0.16), "trim", a)
    deep(B, (0.0, -0.33, 0.14), 0.12, (1.6, 0.6, 0.5))
    e = cowl(B, (0.0, -0.03, 0.25), 1.15)
    # what stands clear above it: a fence, and the heads of the grass
    posts = None
    for i, x in enumerate((-0.38, -0.24, -0.1)):
        posts = g.merge(posts, sk.post((x, 0.2, 0.2), 0.24 + 0.03 * (i % 2), r=0.02, n=6))
    posts = g.merge(posts, g.tube([(-0.4, 0.2, 0.37), (-0.08, 0.2, 0.36)], 0.012, n=4), g.tube([(-0.4, 0.2, 0.3), (-0.08, 0.2, 0.29)], 0.012, n=4))
    B.add(posts, "wood_grey", False)
    heads = None
    for i, (x, y) in enumerate(((0.3, 0.16), (0.36, 0.02), (0.24, 0.24), (-0.3, -0.1), (0.12, 0.3))):
        heads = g.merge(heads, g.tube([(x, y, 0.22), (x + 0.01, y, 0.31 + 0.02 * (i % 2))], 0.004, n=3), g.ico((x + 0.012, y, 0.33 + 0.02 * (i % 2)), 0.012, sub=0, scale=(0.7, 0.7, 1.6)))
    B.add(heads, "grass_dew", False)
    B.budget = 1300
    ragged(B, (0, 0, 0.13), 0.46, 0.4, n=6, L=0.13, w=0.05, what="edge")
    hanging(B, [(0.2, 0.1, 0.04), (-0.22, 0.05, 0.04), (0.0, -0.2, 0.04)])
    _done(B, 0.7, -0.17, 0.27, 0.36, e, crown=(0, 0.04, 0.56))


def plan_mask(B):
    """A blank grey face forms in it when it is looked at, and is nobody's: it is in the cowl, and its two slits are lit."""
    bank(B, (0, 0.02, 0.36), 0.5, 0.38, 0.46, seed=0.3, deep="accent_dark")
    k = 1.6
    c = Vector((0, 0.02, 0.56))
    prof = ((0.0, 0.09, 0.085, 0.0), (0.08, 0.115, 0.125, 0.0), (0.16, 0.1, 0.11, 0.02), (0.22, 0.055, 0.065, 0.05), (0.265, 0.008, 0.008, 0.08))
    B.add(g.loft([g.ring(c + Vector((0, yo * k, z * k)), rx * k, ry * k, n=16, u=X, v=Y, phase=math.pi / 16) for z, rx, ry, yo in prof]), "accent_dark", True)
    f = c + Vector((0, -0.092 * k, 0.092 * k))
    B.add(g.ico(f + Vector((0, 0.012 * k, 0)), 0.09 * k, sub=2, scale=(0.95, 0.42, 1.15)), "accent", True)
    B.add(sk.hoop(f + Vector((0, -0.03 * k, 0)), 0.081 * k, 0.1 * k, 0.009 * k, n=18, u=X, v=Z, sides=5), "accent_light", True)
    # the face: a pale blank, no mouth, two slits with the field behind them
    B.add(g.ico(f + Vector((0, -0.012, 0)), 0.072 * k, sub=2, scale=(0.84, 0.3, 1.2)), "mask_pale", True)
    e = f + Vector((0, -0.05, 0.03))
    slits = None
    for s in (1, -1):
        slits = g.merge(slits, g.tongue([e + Vector((s * 0.018, 0, 0.0)), e + Vector((s * 0.045, -0.004, -0.004)), e + Vector((s * 0.072, 0.008, 0.004))], [0.006, 0.02, 0.006], thick=0.5, normal=(0, -1, 0.2)))
    B.move("blink", "eyes", [(slits, field("eyes", 2.6), True)], e)
    # what it is covering for: a lantern shuttered to a slit, held out on an arm of it, and the nose of a boat
    chain(B, [(0.18, -0.02, 0.5), (0.25, -0.1, 0.52), (0.3, -0.14, 0.5)], 0.07, 0.045, (1, 1, 0.9), ("main", "trim"))
    at = Vector((0.3, -0.15, 0.47))
    B.move("sway", "lantern", sk.lantern(at, 0.07, lit=False, cap="accent_light", frame="metal_dark") + [(g.box(at + Vector((0, -0.04, -0.105)), (0.04, 0.012, 0.014)), field("slit", 2.8))], at)
    boat = g.tongue([(-0.4, 0.0, 0.17), (-0.3, -0.16, 0.16), (-0.12, -0.32, 0.18), (-0.02, -0.42, 0.25)], [0.05, 0.17, 0.15, 0.02], thick=0.6, normal=Z)
    B.add(boat, "wood_grey", False)
    B.add(g.tube([(-0.38, -0.05, 0.2), (-0.26, -0.21, 0.19), (-0.1, -0.36, 0.215), (-0.02, -0.425, 0.262)], 0.009, n=4), "accent", False)
    ragged(B, (0, 0.04, 0.2), 0.27, 0.2, n=5, L=0.14, w=0.05, arc=(0.3, 3.0), what="edge")
    shreds(B, (0, 0.02, 0.62), 0.3, n=3, seed=0.9)
    _done(B, 0.98, -0.18, 0.5, 0.26, e)


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
    deep(B, (0, 0.2, 0.2), 0.16, (1.8, 0.8, 0.5))
    e = cowl(B, (0, 0.26, 0.38), 1.6, "old")
    for j, (i, off) in enumerate(((0, 0.0), (1, 0.05), (7, -0.05), (8, 0.0))):
        p, r = seats[i]
        eyes(B, p + Vector((off, -r * 1.02, 0.02)), 0.038, 0.014, "old", what="eyes_" + "abcd"[j])
    B.budget = 1200
    for s in (1, -1):       # the piles of the harbour it came into, and the rope on them
        B.add(sk.post((s * 0.5, -0.2, 0.08), 0.4, r=0.03, n=6), "wood_grey", False)
        B.add(sk.hoop((s * 0.5, -0.2, 0.4), 0.04, 0.04, 0.01, n=8, sides=4), "accent", False)
        tip = seats[0 if s > 0 else 8][0]
        wisps(B, [[tip + Vector((0, -0.08, 0)), tip + Vector((-s * 0.06, -0.2, -0.02)), tip + Vector((-s * 0.16, -0.28, -0.04)), tip + Vector((-s * 0.26, -0.3, -0.06))]], w=0.09, role="main", what="arm_" + ("l" if s > 0 else "r"))
    _done(B, 0.8, -0.33, 0.34, 0.46, e)


def plan_folds(B):
    """It moves in slow folds like water, and things passing through it come out slower."""
    for i, (z, w, y, m) in enumerate(((0.52, 0.2, 0.06, "trim"), (0.43, 0.27, 0.02, "main"), (0.33, 0.33, -0.03, "under"), (0.23, 0.37, -0.09, "main"), (0.14, 0.4, -0.15, "under"))):
        for x in (-1.0, -0.33, 0.33, 1.0):       # each fold a long roll, lower and further out than the last
            roll(B, (x * w, y + 0.04 * abs(x), z - 0.03 * abs(x)), 0.1 + 0.012 * i, (1.5, 0.9, 0.62), m, 0.0)
    deep(B, (0, -0.2, 0.2), 0.11, (2.2, 0.5, 0.5))
    e = cowl(B, (0, 0.07, 0.56), 1.15)
    for s in (1, -1):       # the scroll of a wave at its foot
        pts = g.spiral((s * 0.34, -0.2, 0.15), 0.085, 0.02, 0.8, 0.0, n=8, axis=Y, start=math.pi if s > 0 else 0.0)
        B.move("sway", "scroll", [(g.tube(sk.curve(pts, n=2), _spread_w(0.045, 0.004, 17), n=6, flat=1.4), B.trim, True)], pts[0], side="l" if s > 0 else "r")
    ragged(B, (0, -0.1, 0.1), 0.42, 0.2, n=5, L=0.12, w=0.05, arc=(3.5, 5.9), what="edge")
    _done(B, 0.87, -0.2, 0.44, 0.4, e)


def _spread_w(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def plan_douse(B):
    """Rime at its edges and steam at its heart. It hisses, faintly, all the time."""
    bank(B, (0, 0, 0.34), 0.54, 0.42, 0.32, seed=0.6, deep="accent_dark")
    e = cowl(B, (0, -0.02, 0.45), 1.25)
    rime = None
    for i in range(13):         # an icicle fringe, all the way round
        a = 2 * math.pi * i / 13
        d = Vector((math.cos(a), math.sin(a) * 0.8, 0))
        b0 = Vector((0, 0, 0.28)) + d * 0.27
        rime = g.merge(rime, sk.crystal(b0, b0 + d * (0.1 + 0.04 * (i % 3)) + Z * (-0.1 - 0.03 * (i % 2)), 0.022, n=4))
    B.add(rime, "ice_pale", True)
    puffs = [None, None]
    for i, (x, y, z, r) in enumerate(((0.03, 0.14, 0.86, 0.075), (-0.06, 0.16, 0.99, 0.06), (0.04, 0.17, 1.1, 0.045))):       # the steam of it, going up behind the hood
        puffs[i % 2] = g.merge(puffs[i % 2], sk.cloud([((x, y, z), r, (1.2, 1.0, 0.75)), ((x + r * 0.8, y, z + r * 0.2), r * 0.7), ((x - r * 0.7, y + 0.02, z + r * 0.3), r * 0.6)], res=0.022))
    B.move("bob", "steam_a", [(puffs[0], "steam", True)], (0, 0.15, 0.9))
    B.move("bob", "steam_b", [(puffs[1], "steam", True)], (0, 0.15, 1.0))
    # what it has just put out: a brand, black and wet, the last of its smoke going
    B.add(g.tube([(0.1, -0.38, 0.14), (0.24, -0.22, 0.22), (0.36, -0.08, 0.26)], [0.022, 0.024, 0.02], n=6), "wood_black", False)
    B.add(g.ico((0.09, -0.39, 0.135), 0.032, sub=1), "ash_dark", False)
    wisps(B, [[(0.09, -0.39, 0.16), (0.07, -0.4, 0.24), (0.1, -0.41, 0.31), (0.06, -0.4, 0.38)]], w=0.03, role="trim", what="smoke")
    ragged(B, (0, 0, 0.2), 0.3, 0.24, n=4, L=0.12, w=0.045, arc=(0.4, 2.8), what="edge")
    _done(B, 0.8, -0.22, 0.42, 0.3, e)


def plan_pall(B):
    """A heavy grey that lies like a blanket over what has fallen, with a cold still place at the
    middle of it; the hood is at the head of it and looks down its length."""
    for i in range(5):          # what it covers: long, low, and not to be moved off
        t = i / 4.0
        roll(B, (-0.32 + 0.6 * t, 0.0, 0.2 + 0.02 * math.sin(t * 3.1)), 0.16 - 0.03 * t, (1.3, 1.5, 0.8), "main", 0.0)
    for i in range(6):
        t = i / 5.0
        for s in (1, -1):       # the blanket's edge, where it comes down to the ground
            roll(B, (-0.4 + 0.74 * t, s * 0.21, 0.1), 0.085, (1.4, 0.9, 0.8), "under", 0.0)
    roll(B, (0.42, 0.0, 0.11), 0.09, (0.9, 1.5, 0.8), "under")
    # the border of it, in its Path's colour, and the cold still place
    B.add(g.tube(sk.curve([(-0.42, -0.31, 0.075), (-0.1, -0.325, 0.07), (0.25, -0.31, 0.07), (0.5, -0.2, 0.07), (0.54, 0.0, 0.07)], n=3), 0.013, n=5), "accent", True)
    c = Vector((0.1, -0.02, 0.345))
    B.add(sk.hoop(c + Z * -0.012, 0.11, 0.085, 0.014, n=14, sides=4), "ice_pale", True)
    B.move("pulse", "cold", [(g.ico(c + Z * 0.03, 0.045, sub=2, scale=(1, 1, 1.15)), field("core", 3.0), True)], c + Z * 0.03)
    frost = None
    for i in range(7):
        a = 2 * math.pi * i / 7
        frost = g.merge(frost, sk.crystal(c + Vector((0.1 * math.cos(a), 0.08 * math.sin(a), -0.01)), c + Vector((0.17 * math.cos(a), 0.14 * math.sin(a), -0.035)), 0.014, n=4))
    B.add(frost, "ice_pale", True)
    e = cowl(B, (-0.34, 0.0, 0.33), 1.35, "old")
    ragged(B, (0.05, 0, 0.09), 0.5, 0.3, n=7, L=0.1, w=0.05, what="edge")
    _done(B, 0.76, -0.24, 0.3, 0.36, e + Vector((0, -0.03, -0.01)), crown=(-0.34, 0.06, 0.68))


def plan_maw(B):
    """A low dense grey with a hollow in it like an open mouth: the hood is all mouth now. Candles dim when it passes."""
    for i in range(7):
        a = 2 * math.pi * i / 7
        roll(B, (0.3 * math.cos(a), 0.03 + 0.27 * math.sin(a), 0.15), 0.14, (1.2, 1.0, 0.7), "under", a)
    roll(B, (0, 0.05, 0.3), 0.27, (1.1, 1.0, 0.85), "main")
    roll(B, (0, 0.1, 0.46), 0.17, (1.0, 1.0, 0.8), "main")
    roll(B, (0.02, 0.17, 0.57), 0.09, (1.0, 1.0, 0.9), "trim")
    m = Vector((0, -0.2, 0.27))
    B.fog[""]["main"].append((m + Vector((0, -0.03, 0)), 0.15, (1.25, 0.7, 0.85), 0.0, -1))       # the hollow
    B.add(g.ico(m + Vector((0, 0.03, 0)), 0.17, sub=2, scale=(1.25, 0.45, 0.88)), "accent", True)
    B.add(g.ico(m + Vector((0, 0.012, 0)), 0.15, sub=2, scale=(1.25, 0.45, 0.86)), "void", True)
    B.add(sk.hoop(m + Vector((0, -0.055, 0)), 0.2, 0.14, 0.022, n=18, u=X, v=Z, sides=6), "accent_dark", True)
    B.add(sk.hoop(m + Vector((0, -0.075, 0)), 0.19, 0.13, 0.007, n=18, u=X, v=Z, sides=4), "accent_light", True)
    e = Vector((0, -0.2, 0.5))
    eyes(B, e, 0.075, 0.02, "soft")
    # the candle it has just passed: bent over, nearly out
    at = Vector((0.38, -0.3, 0.1))
    B.add(sk.disc(at, 0.055, thick=0.012, n=8), "accent_light", False)
    B.add(g.lathe([(0.024, 0.0), (0.025, 0.09), (0.016, 0.105)], n=7, centre=at + Z * 0.012), "wax", True)
    t = at + Z * 0.125
    B.move("flick", "flame", [(g.tongue([t, t + Vector((0.03, -0.01, 0.014)), t + Vector((0.075, -0.02, 0.01))], [0.014, 0.02, 0.003], thick=0.5), field("flame", 1.8), True)], t, up=(0.94, -0.2, 0.25))
    ragged(B, (0, 0.03, 0.1), 0.36, 0.32, n=6, L=0.12, w=0.05, what="edge")
    _done(B, 0.66, -0.26, 0.34, 0.34, e, crown=(0, 0.12, 0.62))


def plan_pool(B):
    """It lies along the cellar floor, darker than fog should be, with two darker places that watch
    upward; and it has come up the first of the stairs. The floor and the stair go with it."""
    B.extend(sk.flags((0, -0.06, 0.06), 0.9, 0.62, nx=3, ny=2))
    steps = g.merge(g.box((0, 0.34, 0.1), (0.9, 0.2, 0.09)), g.box((0, 0.5, 0.19), (0.9, 0.16, 0.09)))
    B.add(steps, "stone_step", False)
    for i in range(7):
        a = 0.5 + 2 * math.pi * i / 7
        roll(B, (0.28 * math.cos(a), -0.06 + 0.2 * math.sin(a), 0.1), 0.14, (1.35, 1.0, 0.3), "mist_black" if i % 2 else "under", a)
    roll(B, (0, -0.06, 0.11), 0.2, (1.4, 1.0, 0.32), "mist_black")
    chain(B, [(0.1, 0.1, 0.12), (0.14, 0.26, 0.17), (0.1, 0.36, 0.2)], 0.11, 0.07, (1.3, 1.0, 0.4), ("mist_black", "under"))        # up the first stair
    # the hood, fallen on its back, and the two places in it
    h = Vector((-0.02, -0.14, 0.15))
    B.add(g.ico(h, 0.15, sub=2, scale=(1.05, 1.25, 0.34)), "accent_dark", True)
    B.add(g.ico(h + Vector((0, -0.02, 0.012)), 0.12, sub=2, scale=(1.0, 1.15, 0.3)), "void", True)
    B.add(sk.hoop(h + Vector((0, -0.02, 0.035)), 0.125, 0.145, 0.009, n=18, sides=5), "accent_light", True)
    B.add(g.tongue([h + Vector((0, 0.16, 0.01)), h + Vector((0.03, 0.27, 0.0)), h + Vector((0.09, 0.36, -0.02))], [0.16, 0.1, 0.01], thick=0.3, normal=Z), "accent_dark", True)
    e = h + Vector((0, -0.03, 0.05))
    eyes(B, e, 0.05, 0.022, "pits", tilt=-1.25, ride=False)
    # the lamp that went out
    lamp = sk.lantern(Vector((0, 0, 0.13)), 0.07, lit=False, cap="accent_light")
    for geo, m in lamp:
        B.add(sk.shifted(sk.tilted(geo, ry=1.35, about=(0, 0, 0.06)), (0.32, -0.27, 0.06)), m, False)
    ragged(B, (0, -0.06, 0.09), 0.4, 0.27, n=6, L=0.1, w=0.045, role="mist_black", arc=(2.6, 6.6), what="edge")
    hanging(B, [(0.3, -0.2, 0.02), (-0.3, -0.1, 0.02), (0.0, 0.3, 0.02), (-0.32, 0.36, 0.05)])
    _done(B, 0.66, -0.3, 0.16, 0.4, e, crown=h + Vector((0, 0, 0.1)))


def plan_thick(B):
    """It is thick enough to push against. Hands moved through it leave a slow wake."""
    bank(B, (0, 0.04, 0.42), 0.46, 0.38, 0.6, seed=0.2, dark=True, deep="accent_dark")
    e = cowl(B, (0, -0.02, 0.66), 1.3)
    for s in (1, -1):     # two hands of it, webbed, pushing
        wr = Vector((s * 0.3, -0.24, 0.42))
        chain(B, [(s * 0.2, 0.0, 0.52), (s * 0.3, -0.1, 0.46), wr], 0.075, 0.055, (1, 1, 1), ("main", "trim"))
        palm = wr + Vector((0, -0.035, 0.03))
        B.add(g.ico(palm, 0.06, sub=2, scale=(1.0, 0.4, 1.1)), B.trim, True)
        tips = [wr + Vector((s * math.sin(a) * 0.15, -0.06, 0.04 + math.cos(a) * 0.15)) for a in (-0.6, -0.2, 0.2, 0.6)]
        fan, web = None, None
        for t in tips:
            fan = g.merge(fan, g.tube([palm, (palm + t) * 0.5 + Vector((0, -0.012, 0)), t], [0.016, 0.013, 0.007], n=5))
        for t0, t1 in zip(tips, tips[1:]):
            web = g.merge(web, g.tongue([palm, (t0 + t1) * 0.43 + palm * 0.14], [0.02, (t1 - t0).length * 0.8], thick=0.08, normal=-Y))
        B.add(fan, B.trim, True)
        B.add(web, "accent", True)
        curl(B, (s * 0.3, 0.2, 0.26), 0.1, turns=0.9, w=0.05, axis=Z, start=0.0 if s > 0 else math.pi, n=8, end=0.3, what="wake_" + ("l" if s > 0 else "r"))       # the wake it leaves
    bub = None
    for x, y, z, r in ((0.2, -0.1, 0.9, 0.028), (-0.22, -0.04, 0.98, 0.02), (0.26, 0.02, 1.04, 0.016), (-0.16, -0.12, 1.08, 0.012)):
        bub = g.merge(bub, g.ico((x, y, z), r, sub=1))
    B.move("bob", "bubbles", [(bub, B.trim, True)], (0, -0.05, 0.95))
    ragged(B, (0, 0.04, 0.16), 0.24, 0.2, n=5, L=0.12, w=0.05, what="edge")
    _done(B, 1.0, -0.22, 0.5, 0.32, e)


# --- it stands where it was left -------------------------------------------------------------

def plan_pillar(B):
    """It hangs in one spot in still air and does not thin; sounds from long ago carry in it, and it listens for them."""
    for i, (z, r, m) in enumerate(((0.2, 0.15, "under"), (0.32, 0.165, "main"), (0.46, 0.15, "trim"), (0.58, 0.16, "main"), (0.7, 0.14, "trim"), (0.8, 0.1, "main"))):
        roll(B, (0.012 * math.sin(i * 2.0), 0.0, z), r, (1.0, 0.95, 0.72), m, i)
    deep(B, (0, -0.05, 0.3), 0.1, (1.0, 0.6, 1.0), step="accent_light")
    # it listens: an ear-trumpet of old brass, out of the side of it
    c = Vector((0.1, 0.0, 0.62))
    horn = [g.ring(c + X * off + Z * off * 0.25, r, r * 1.08, n=14, u=Y, v=Z) for off, r in ((0.0, 0.022), (0.07, 0.035), (0.14, 0.07), (0.2, 0.13), (0.23, 0.18))]
    B.add(g.loft(horn, caps=False), "accent", True)
    B.add(g.loft([g.ring(c + X * off + Z * off * 0.25, r, r * 1.08, n=14, u=Y, v=Z) for off, r in ((0.23, 0.18), (0.21, 0.14), (0.1, 0.045))], caps=False), "accent_dark", True)
    B.add(sk.hoop(c + X * 0.23 + Z * 0.058, 0.18, 0.195, 0.008, n=18, u=Y, v=Z, sides=5), "accent_light", True)
    e = Vector((0, -0.165, 0.585))
    eyes(B, e, 0.047, 0.019)
    stone(B, (-0.23, -0.17, 0.07), 0.13, 0.28, lean=0.08)
    ragged(B, (0, 0, 0.14), 0.14, 0.13, n=5, L=0.13, w=0.05, what="edge")
    _done(B, 0.9, -0.17, 0.5, 0.2, e)


def plan_wall(B):
    """A flat grey wall across a gap, square at the edges, like a door with no handle: fog, between two gateposts."""
    for j in range(4):
        for i in range(4):
            roll(B, (-0.21 + 0.14 * i, 0.0, 0.2 + 0.17 * j), 0.105, (1.0, 0.42, 1.0), ("main", "trim")[(i + j) % 2], 0.0)
    deep(B, (0, 0.0, 0.17), 0.075, (2.6, 0.5, 0.6), step="accent_light")
    B.add(g.box((0, 0, 0.83), (0.62, 0.1, 0.028)), B.trim, False)                 # its top, ruled
    for s in (1, -1):
        B.add(g.merge(g.box((s * 0.37, 0, 0.44), (0.11, 0.11, 0.68)), g.box((s * 0.37, 0, 0.79), (0.14, 0.14, 0.04))), "stone_grave", False)
        B.add(g.merge(g.cone((s * 0.37, 0, 0.81), (s * 0.37, 0, 0.9), 0.075, n=4), g.box((s * 0.37, -0.058, 0.6), (0.07, 0.008, 0.1))), "accent", False)
    e = Vector((0, -0.062, 0.62))
    eyes(B, e, 0.06, 0.02, patch=False)
    ragged(B, (0, -0.02, 0.13), 0.3, 0.05, n=5, L=0.12, w=0.05, arc=(3.4, 6.0), what="edge")
    _done(B, 0.9, -0.08, 0.46, 0.4, e)


def plan_drift(B):
    """It lies banked along the post like snow against a wall, with the lamp showing through as a low sun."""
    for i in range(8):
        t = i / 7
        x = -0.44 + 0.66 * t
        r = 0.1 + 0.11 * t
        roll(B, (x, 0.02 * math.sin(i * 2.0), 0.12 + 0.28 * t), r, (1.2, 1.3, 0.85), "main" if i % 2 else "under", i)
        roll(B, (x + 0.02, -0.02, 0.12 + 0.28 * t + r * 0.6), r * 0.72, (1.2, 1.3, 0.6), "trim", i)
    for dx, dz, r in ((-0.14, -0.04, 0.06), (0.12, -0.1, 0.055)):
        deep(B, (0.04 + dx, -0.17, 0.44 + dz), r, (1.0, 0.6, 1.0), step="accent_pale")
    B.add(g.merge(g.box((0.36, 0.1, 0.4), (0.1, 0.5, 0.6)), g.box((0.36, 0.1, 0.715), (0.13, 0.54, 0.03))), "stone_grave", False)
    B.add(g.tube([(0.08, 0.02, 0.1), (0.08, 0.02, 0.9)], [0.024, 0.02], n=6), "accent_dark", False)
    B.add(g.tube([(0.08, 0.02, 0.88), (0.08, -0.06, 0.94), (0.08, -0.14, 0.92)], 0.014, n=4), "accent_dark", False)
    B.add(g.merge(g.box((0.36, 0.1, 0.735), (0.14, 0.56, 0.016)), sk.hoop((0.08, 0.02, 0.5), 0.028, 0.028, 0.008, n=8, sides=4)), "accent", False)
    at = Vector((0.08, -0.14, 0.92))
    B.move("sway", "lamp", sk.lantern(at, 0.07, glow="lamp", strength=3.4, cap="accent", frame="accent_dark"), at)
    # the lamp, seen through it: a low sun
    sun = Vector((0.04, -0.23, 0.44))
    B.move("pulse", "sun", [(g.ico(sun, 0.085, sub=2, scale=(1.0, 0.25, 1.0)), field("sun", 2.0), True), (sk.hoop(sun + Vector((0, -0.01, 0)), 0.13, 0.13, 0.011, n=18, u=X, v=Z, sides=4), "accent_light", True)], sun)
    e = Vector((-0.25, -0.17, 0.3))
    eyes(B, e, 0.047, 0.018)
    ragged(B, (-0.3, 0, 0.12), 0.2, 0.14, n=4, L=0.14, w=0.05, arc=(1.8, 5.0), what="edge")
    _done(B, 0.94, -0.2, 0.4, 0.44, e, crown=(-0.1, 0, 0.56))


def plan_streamers(B):
    """It comes in off the water over the quay, low and all at once, and reaches up the land in
    long streamers; the wind has its back, and there is salt in it."""
    for i in range(5):         # the body of it, heaped on the quay and over its edge
        x = -0.3 + 0.15 * i
        roll(B, (x, 0.3, 0.36 + 0.03 * math.sin(i * 2.0)), 0.14, (1.1, 1.0, 0.75), "main" if i % 2 else "under", i)
        roll(B, (x + 0.03, 0.14, 0.3), 0.12, (1.1, 1.2, 0.7), "trim" if i % 2 else "main", i)
    first = None
    for j, (x, L, w) in enumerate(((0.0, 1.0, 1.0), (0.27, 0.74, 0.8), (-0.27, 0.62, 0.74))):       # and the streamers, each lower and thinner as it goes
        pts = [Vector((x + 0.03 * math.sin(i * 1.3 + j), 0.06 - 0.5 * L * i / 4, 0.27 - 0.11 * i / 4 + 0.02 * math.sin(i * 1.9 + j))) for i in range(5)]
        for i, p in enumerate(pts):
            roll(B, p, (0.1, 0.092, 0.084, 0.078, 0.086)[i] * w, (1.0, 1.5, 0.66), ("main", "trim")[i % 2] if j == 0 else ("under", "main")[i % 2], 0.0)
        deep(B, pts[2] + Vector((0, 0, -0.035 * w)), 0.06 * w, (1.0, 2.2, 0.6), step="accent_light")
        if j == 0:
            first = pts[4] + Vector((0, -0.118 * w, 0.02))
            eyes(B, first, 0.04, 0.017)
    back = [[Vector((x, 0.36, 0.44)), Vector((x + 0.02, 0.46, 0.5)), Vector((x - 0.01, 0.58, 0.5)), Vector((x + 0.02, 0.7, 0.46))] for x in (-0.24, -0.08, 0.08, 0.22)]
    wisps(B, back, w=0.032, role="trim", what="spray", pivot=(0, 0.36, 0.46), swell=0.1)
    B.budget = 1300
    # the quay it comes in over: the coping, a bollard with a ring in it, the mark of the highest tide, the harbour light
    B.add(g.box((0.0, 0.38, 0.11), (0.86, 0.2, 0.2)), "stone_grave", False)
    B.add(g.box((0.0, 0.38, 0.22), (0.9, 0.24, 0.03)), "stone_step", False)
    B.add(g.lathe([(0.045, 0.0), (0.038, 0.08), (0.056, 0.1), (0.045, 0.135), (0.0, 0.14)], n=8, centre=(0.37, 0.3, 0.235)), "accent", False)
    B.add(sk.hoop((0.37, 0.268, 0.13), 0.045, 0.045, 0.01, n=10, u=X, v=Z, sides=4), "accent_light", False)
    B.add(g.merge(g.box((-0.26, 0.277, 0.15), (0.2, 0.008, 0.022)), g.box((-0.26, 0.277, 0.1), (0.13, 0.008, 0.022))), "accent", False)
    post = Vector((-0.38, 0.42, 0.235))
    B.add(g.tube([post, post + Z * 0.5], [0.016, 0.013], n=6), "metal_iron", False)
    B.move("sway", "light", sk.lantern(post + Vector((0.0, -0.05, 0.56)), 0.075, glow="lamp", strength=3.2, cap="accent", frame="accent_dark") + [(g.tube([post + Z * 0.5, post + Vector((0, -0.03, 0.57)), post + Vector((0, -0.05, 0.56))], 0.009, n=4), mat("metal_iron"))], post + Vector((0.0, -0.05, 0.56)))
    salt = None
    for x, y, z in ((0.1, 0.1, 0.56), (-0.12, 0.3, 0.6), (0.2, 0.3, 0.56), (-0.3, 0.0, 0.42), (0.3, -0.1, 0.4)):
        salt = g.merge(salt, g.ico((x, y, z), 0.012, sub=0))
    B.move("bob", "salt", [(salt, "bone", False)], (0, 0.1, 0.5))
    ragged(B, (0, -0.2, 0.15), 0.34, 0.24, n=4, L=0.1, w=0.04, arc=(3.6, 5.8), what="edge")
    _done(B, 0.8, -0.5, 0.36, 0.4, first, crown=(0, 0.3, 0.52))


def plan_graves(B):
    """Figures stand in it at the edge of sight. It looks at them with old eyes and does not point them out."""
    bank(B, (0, 0, 0.2), 0.74, 0.5, 0.2, seed=0.5, deep="accent_light")
    for j, (x, y, hh) in enumerate(((-0.2, 0.16, 0.52), (0.04, 0.22, 0.62), (0.26, 0.14, 0.48))):       # a robe, a bowed head, and no more than that
        for z, r in ((0.12, 0.085), (0.3, 0.07), (0.48, 0.062), (0.62, 0.05)):
            roll(B, (x, y, 0.18 + hh * z), r, (1.0, 0.85, 1.3), "trim", 0.0, "figs")
        roll(B, (x, y - 0.012, 0.16 + hh * 0.9), 0.05, (0.9, 0.95, 1.1), "trim", 0.0, "figs")
    stone(B, (-0.3, -0.21, 0.1), 0.17, 0.36, lean=0.16)
    at = Vector((-0.12, -0.3, 0.135))       # the lamp left at the stone, at the lamp hour
    B.add(g.lathe([(0.045, 0.0), (0.045, 0.016), (0.02, 0.03), (0.016, 0.06)], n=8, centre=at), "accent", False)
    B.add(sk.hoop(at + Vector((0, 0, 0.004)), 0.1, 0.085, 0.009, n=14, sides=4), "accent_light", True)
    for dx, dy in ((0.14, 0.02), (-0.06, 0.07)):
        deep(B, (at.x + dx, at.y + dy, 0.13), 0.07, (1.3, 0.9, 0.6), step="accent_light")
    B.move("flick", "flame", [(g.tongue([at + Z * 0.06, at + Vector((0.004, 0, 0.085)), at + Z * 0.125], [0.018, 0.026, 0.002], thick=0.7, normal=Y), field("flame", 2.8), True)], at + Z * 0.06)
    e = Vector((0.1, -0.265, 0.25))
    eyes(B, e, 0.052, 0.017, "old")
    ragged(B, (0, 0, 0.12), 0.38, 0.26, n=6, L=0.12, w=0.05, what="edge")
    _done(B, 0.8, -0.27, 0.26, 0.4, e)


def plan_bust(B):
    """It holds a lit shape for a breath after a shade has gone: a turned head, a shoulder, in paler
    fog and a line of light; the names stand at its foot, and it watches the shape go."""
    bank(B, (0.02, 0.06, 0.2), 0.78, 0.46, 0.2, seed=0.8, deep="accent_light")
    # the shape it is holding: waist, shoulders, neck, a head turned away
    c = Vector((0.08, 0.08, 0.0))
    for p, r, sc in (((0, 0, 0.3), 0.1, (1.1, 0.7, 1.2)), ((0, 0, 0.42), 0.115, (1.25, 0.7, 1.0)), ((0, 0, 0.53), 0.1, (1.75, 0.66, 0.6)), ((0.01, 0, 0.62), 0.045, (1.0, 0.9, 1.3)),
                     ((0.025, 0.005, 0.74), 0.082, (0.92, 1.0, 1.12))):
        roll(B, c + Vector(p), r, sc, "trim", 0.0, "shape")
    y = c.y - 0.085
    line = [Vector((c.x + x, y, z)) for x, z in ((0.185, 0.47), (0.17, 0.55), (0.08, 0.59), (0.05, 0.63), (0.08, 0.68), (0.105, 0.75), (0.07, 0.82), (0.02, 0.84), (-0.04, 0.8), (-0.06, 0.74), (-0.095, 0.7),
                                                 (-0.055, 0.68), (-0.04, 0.63), (-0.07, 0.59), (-0.16, 0.56), (-0.185, 0.47))]
    B.move("pulse", "light", [(g.tube(sk.curve(line, n=2), 0.0075, n=4), field("shade", 3.0), True)], c + Z * 0.62)
    e = Vector((-0.24, -0.2, 0.27))
    eyes(B, e, 0.05, 0.017, "old")
    for i, x in enumerate((-0.06, 0.14, 0.34)):      # the names
        stone(B, (x, -0.3, 0.07), 0.13, 0.16 + 0.02 * (i % 2), lean=0.06 * (i - 1), thick=0.04)
    ragged(B, (0, 0.04, 0.12), 0.4, 0.24, n=6, L=0.12, w=0.05, what="edge")
    _done(B, 0.86, -0.22, 0.4, 0.3, e, crown=c + Vector((0.025, 0, 0.84)))


def plan_trail(B):
    """It hangs in a line along the path, and old prints show in it as if just made. The path goes with it."""
    path = g.tongue([(0.02, -0.56, 0.05), (-0.04, -0.2, 0.05), (0.04, 0.2, 0.05), (0.0, 0.72, 0.05)], [0.34, 0.4, 0.38, 0.3], thick=0.12, normal=Z)
    B.add(path, "earth_grey", False)
    for i in range(7):
        t = i / 6
        r = 0.125 - 0.05 * t
        roll(B, (0.05 * math.sin(i * 1.4), -0.26 + 0.86 * t, 0.2 + 0.03 * math.sin(i)), r, (1.1, 1.5, 0.75), "main" if i % 2 else "under")
    head = Vector((0, -0.38, 0.4))
    chain(B, [(0, -0.28, 0.24), (0, -0.35, 0.32), head], 0.1, 0.11, (1, 1, 0.95), ("main", "trim"))
    for y in (-0.16, 0.1, 0.36):
        deep(B, (0.0, y, 0.13), 0.075, (1.5, 1.2, 0.6), step="accent_light")
    e = head + Vector((0, -0.125, 0.012))
    eyes(B, e, 0.05, 0.018, "wide")
    pads, toes = None, None
    for i in range(5):
        p = Vector((0.15 * (1 if i % 2 else -1), -0.5 + 0.22 * i, 0.062))
        pads = g.merge(pads, g.ico(p, 0.03, sub=1, scale=(1.0, 1.1, 0.3)))
        for dx in (-0.03, 0.0, 0.03):
            toes = g.merge(toes, g.ico(p + Vector((dx, -0.045, 0)), 0.012, sub=0, scale=(1, 1, 0.4)))
    B.move("pulse", "prints", [(g.merge(pads, toes), field("print", 2.8), True)], (0, 0, 0.062))
    rings = None
    for i in range(5):
        rings = g.merge(rings, sk.hoop((0.15 * (1 if i % 2 else -1), -0.51 + 0.22 * i, 0.058), 0.055, 0.07, 0.008, n=10, sides=4))
    B.add(rings, "accent", True)
    # the waymark at the far end of it, its top stone painted
    cairn = None
    for i, (r, z) in enumerate(((0.085, 0.1), (0.07, 0.19), (0.055, 0.27))):
        cairn = g.merge(cairn, g.ico((0.02 * (-1) ** i, 0.62, z), r, sub=1, scale=(1.2, 1.0, 0.6), rot=(0, 0, i * 1.1)))
    B.add(cairn, "stone_grave", False)
    B.add(g.ico((0.0, 0.62, 0.335), 0.05, sub=1, scale=(1.1, 1.0, 0.7)), "accent", False)
    B.add(g.merge(sk.hoop((0.0, 0.62, 0.19), 0.085, 0.07, 0.008, n=10, sides=4), sk.hoop((0.02, 0.62, 0.1), 0.105, 0.088, 0.008, n=10, sides=4)), "accent_light", False)
    ragged(B, (0.0, 0.3, 0.16), 0.1, 0.3, n=4, L=0.1, w=0.04, arc=(-0.6, 0.6), what="edge")
    hanging(B, [(0.0, -0.4, 0.0), (0.05, 0.1, 0.0), (-0.03, 0.55, 0.0)])
    _done(B, 0.64, -0.5, 0.26, 0.24, e, crown=head + Vector((0, 0, 0.11)))


def plan_hoops(B):
    """It is thinner than it was and very still: three thin rounds of it about a small heart, and a plumb line that does not swing."""
    c = Vector((0, 0, 0.5))
    for u, v in ((X, Y), (X, Z), (Y, Z)):
        B.add(sk.hoop(c, 0.3, 0.3, 0.016, n=24, u=u, v=v, sides=6), B.trim, True)
    B.add(sk.tilted(sk.hoop(c, 0.24, 0.24, 0.007, n=20, sides=4), rx=0.7, ry=0.3, about=c), "accent_light", True)
    roll(B, c, 0.1, (1.0, 1.0, 0.92), "main")
    roll(B, c + Vector((0.03, 0.03, -0.06)), 0.07, (1.1, 1.0, 0.7), "under")
    e = c + Vector((0, -0.105, 0.012))
    eyes(B, e, 0.034, 0.014, "shut", patch=False)
    # nothing in it moves: a plumb line, hanging dead straight, its bob of old gold
    B.add(g.tube([(0, 0, 0.8), (0, 0, 0.61)], 0.004, n=3), "cord", False)
    B.add(g.tube([(0, 0, 0.4), (0, 0, 0.3)], 0.004, n=3), "cord", False)
    B.add(g.lathe([(0.0, 0.0), (0.03, 0.05), (0.022, 0.08), (0.006, 0.09)], n=8, centre=(0, 0, 0.21)), "accent", False)
    _done(B, 0.82, -0.3, 0.5, 0.3, e)


def plan_edge(B):
    """A clean grey bank, straight as a rule, with the air stood still along it, and the marks of where you should not go."""
    for i in range(7):
        x = -0.42 + 0.14 * i
        roll(B, (x, 0.02, 0.28), 0.11, (1.0, 0.5, 1.5), "main" if i % 2 else "under")
        roll(B, (x, 0.02, 0.52), 0.1, (1.0, 0.45, 1.3), "trim" if i % 2 else "main")
    deep(B, (0, 0.03, 0.17), 0.075, (4.2, 0.5, 0.6), step="accent_light")
    B.add(g.box((0, 0.02, 0.675), (1.0, 0.07, 0.026)), B.trim, False)             # its top, ruled
    stakes, flags = None, None
    for x in (-0.24, 0.2, 0.44):
        stakes = g.merge(stakes, sk.post((x, -0.16, 0.1), 0.32, r=0.012, n=5))
        flags = g.merge(flags, g.blade((x, -0.165, 0.4), (x + 0.11, -0.175, 0.365), 0.075, normal=Y, belly=0.2))
    B.add(stakes, "wood_grey", False)
    B.move("sway", "flags", [(flags, "accent", False)], (0.2, -0.165, 0.4))
    stone(B, (-0.44, -0.15, 0.1), 0.13, 0.3)
    e = Vector((0, -0.045, 0.5))
    eyes(B, e, 0.07, 0.02, "shut", patch=False)
    ragged(B, (0, 0.0, 0.14), 0.46, 0.05, n=6, L=0.1, w=0.045, arc=(3.4, 6.0), what="edge")
    _done(B, 0.72, -0.06, 0.4, 0.5, e)


def plan_curtain(B):
    """It parts in the middle like a curtain, and a single clear eye of open air looks through."""
    for s in (1, -1):
        for j, (x, m) in enumerate(((0.46, "under"), (0.36, "main"), (0.27, "trim"))):       # each fold of it hangs, and is gathered at the tie
            for z, dx, r in ((0.82, 0.0, 0.075), (0.68, -0.01, 0.07), (0.56, 0.0, 0.058), (0.45, 0.03, 0.045), (0.34, 0.07, 0.06), (0.22, 0.1, 0.075), (0.13, 0.12, 0.08)):
                roll(B, (s * (x + dx), -0.012 * j, z), r, (1.0, 0.75, 1.3), m, 0.0, "l" if s > 0 else "r")
        B.add(sk.hoop((s * 0.385, -0.01, 0.45), 0.13, 0.062, 0.016, n=14, sides=5), "accent", True)             # the tie
        B.move("sway", "tassel", [(g.merge(g.tube([(s * 0.5, -0.03, 0.45), (s * 0.52, -0.035, 0.36)], 0.006, n=4), g.lathe([(0.0, 0.0), (0.02, -0.02), (0.026, -0.075), (0.0, -0.08)], n=7, centre=(s * 0.52, -0.035, 0.36))), "accent_light", True)],
               (s * 0.5, -0.03, 0.45), side="l" if s > 0 else "r")
    for x in (-0.42, -0.21, 0.0, 0.21, 0.42):       # the pelmet of it
        roll(B, (x, -0.02, 0.9 - 0.04 * (1 - (x / 0.42) ** 2)), 0.085, (1.5, 0.8, 0.75), "main", 0.0, "still")
    # the eye of open air
    c = Vector((0, 0.0, 0.52))
    loop = [c + Vector((0.19 * math.cos(a), 0, 0.115 * math.sin(a) * (1.0 - 0.25 * abs(math.cos(a))))) for a in [2 * math.pi * i / 20 for i in range(21)]]
    B.add(g.tube(loop, 0.011, n=5, caps=False), B.trim, True)
    B.move("blink", "eye", [(g.ico(c, 0.062, sub=2, scale=(1.0, 0.4, 1.0)), field("eyes", 3.4), True), (g.ico(c + Vector((0, -0.022, 0)), 0.024, sub=2, scale=(1.0, 0.5, 1.0)), "void", True)], c)
    # the sill it hangs over
    B.add(g.merge(g.box((0, 0.0, 0.08), (1.12, 0.2, 0.06)), g.box((0, -0.02, 0.03), (1.2, 0.28, 0.05))), "stone_grave", False)
    B.add(g.box((0, -0.162, 0.03), (1.0, 0.008, 0.022)), "accent", False)
    hanging(B, [(-0.4, 0.0, 0.0), (0.0, 0.0, 0.0), (0.4, 0.0, 0.0)])
    _done(B, 0.96, -0.06, 0.52, 0.5, c)


# --- it will not be held ---------------------------------------------------------------------

def plan_swirl(B):
    """It will not hold a shape. Look at one part and the rest has moved, off toward water."""
    head = Vector((-0.12, 0, 0.5))
    roll(B, head, 0.17, (1.1, 1.0, 0.9), "main")
    roll(B, head + Vector((0.02, 0.02, 0.12)), 0.11, (1.2, 1.0, 0.6), "trim")
    chain(B, [head + Vector((0.1, 0.02, -0.02)), (0.18, 0.06, 0.5), (0.32, 0.08, 0.4), (0.33, 0.06, 0.24)], 0.13, 0.085, (1.0, 0.9, 0.9), ("main", "under"))
    deep(B, head + Vector((0.06, -0.06, -0.09)), 0.1, (1.2, 0.8, 0.7))
    curl(B, (0.2, 0.04, 0.24), 0.13, turns=0.9, w=0.085, start=0.2, role="under", what="curl")
    e = head + Vector((-0.03, -0.185, 0.02))
    eyes(B, e, 0.052, 0.019)
    wisps(B, [[(0.4, 0.09, 0.46), (0.5, 0.12, 0.5), (0.6, 0.17, 0.47), (0.68, 0.22, 0.52)], [(0.38, 0.09, 0.36), (0.5, 0.14, 0.34), (0.6, 0.2, 0.38)]], w=0.07, role="trim", what="going")
    shreds(B, (0.2, 0.05, 0.6), 0.16, n=3, seed=0.2)
    _done(B, 0.68, -0.17, 0.42, 0.34, e)


def _mouth(B, c, r, facing=(0, -1, 0)):
    """A round mouth in it, open, speaking: lined with its Path's colour."""
    c, d = V(c), V(facing).normalized()
    side = d.cross(Z).normalized()
    a = math.atan2(-d.x, d.y)
    B.add(g.ico(c - d * r * 0.1, r * 1.12, sub=2, scale=(1.0, 0.5, 1.0), rot=(0, 0, a)), "accent", True)
    B.add(g.ico(c - d * r * 0.2, r, sub=2, scale=(1.0, 0.5, 1.0), rot=(0, 0, a)), "void", True)
    B.add(sk.hoop(c + d * r * 0.3, r * 1.05, r * 1.05, r * 0.24, n=12, u=side, v=Z, sides=5), B.trim, True)


def plan_echo(B):
    """It has a voice, and the voice is always the last speaker's, from the wrong side of the room."""
    bank(B, (-0.2, 0.0, 0.42), 0.36, 0.3, 0.38, seed=0.4, deep="accent_dark")
    curl(B, (-0.2, 0.02, 0.2), 0.11, turns=0.8, w=0.08, start=0.6, role="under")
    e = Vector((-0.2, -0.175, 0.53))
    eyes(B, e, 0.047, 0.017)
    _mouth(B, (-0.2, -0.175, 0.4), 0.05)
    # the other end of it, over there, saying it back
    c2 = Vector((0.32, 0.06, 0.62))
    roll(B, c2, 0.12, (1.1, 1.0, 0.85), "main", 0.0, "b")
    roll(B, c2 + Vector((0.02, 0.0, 0.08)), 0.08, (1.2, 1.0, 0.6), "trim", 0.0, "b")
    curl(B, c2 + Vector((0.06, 0.02, -0.16)), 0.09, turns=0.8, w=0.07, start=2.4, role="under")
    d = Vector((-0.5, -0.86, 0)).normalized()
    _mouth(B, c2 + Vector((-0.075, -0.115, 0.0)), 0.042, facing=d)
    wisps(B, [[Vector((-0.06, 0.04, 0.5)), Vector((0.06, 0.08, 0.57)), Vector((0.2, 0.07, 0.62))]], w=0.045, role="under", what="thread", swell=0.0)
    rings = None
    o = c2 + Vector((-0.09, -0.14, 0.0))
    side = d.cross(Z).normalized()
    for i, rr in enumerate((0.07, 0.11, 0.15)):
        rings = g.merge(rings, sk.hoop(o + d * (0.03 + 0.065 * i), rr, rr, 0.007, n=14, u=side, v=Z, sides=4))
    B.move("pulse", "voice", [(rings, "accent_light", True)], o)
    _done(B, 0.76, -0.18, 0.46, 0.4, e, crown=(-0.2, 0, 0.62))


def _face(B, c, s, lit=2.4, what="eyes"):
    """A face formed in it: a brow, a nose, two hollows that blink, a mouth."""
    c = V(c)
    roll(B, c + Vector((0, 0.03, 0)), 0.13 * s, (0.95, 0.5, 1.25), "main", 0.0, "still")
    roll(B, c + Vector((0, -0.03 * s, 0.07 * s)), 0.1 * s, (1.3, 0.45, 0.32), "trim", 0.0, "still")
    B.add(g.tube([c + Vector((0, -0.075 * s, 0.06 * s)), c + Vector((0, -0.108 * s, 0.0)), c + Vector((0, -0.085 * s, -0.03 * s))], [0.012 * s, 0.024 * s, 0.016 * s], n=6), B.trim, True)
    B.add(sk.eye_pair(c + Vector((0, -0.072 * s, 0.03 * s)), 0.05 * s, 0.03 * s, scale=(1.2, 0.4, 0.7), slant=-0.1), B.under, True)
    e = c + Vector((0, -0.084 * s, 0.026 * s))
    B.move("blink", what, [(_pair(e, 0.05 * s, 0.014 * s, (1.0, 0.5, 1.0), 0.0), field("eyes", lit), True)], e)
    B.add(g.ico(c + Vector((0, -0.072 * s, -0.075 * s)), 0.03 * s, sub=2, scale=(1.6, 0.5, 0.5)), "accent_dark", True)
    return e


def plan_faces(B):
    """A face forms in it that is nearly somebody you know, and then a second behind the first."""
    bank(B, (0, 0.06, 0.36), 0.44, 0.34, 0.46, seed=0.9, deep="accent_dark")
    curl(B, (0.12, 0.04, 0.2), 0.15, turns=0.85, w=0.1, start=0.4, role="under")
    c = Vector((-0.03, -0.16, 0.5))
    e = _face(B, c, 1.2)
    _face(B, Vector((0.17, 0.04, 0.8)), 0.8, what="eyes_b")
    chain(B, [(0.1, 0.06, 0.56), (0.15, 0.08, 0.66), (0.17, 0.08, 0.72)], 0.08, 0.06, (1, 0.8, 1), ("main",), "still")
    # it beckons
    pts = [Vector((-0.2, -0.02, 0.4)), Vector((-0.34, -0.16, 0.38)), Vector((-0.38, -0.3, 0.46)), Vector((-0.33, -0.36, 0.56))]
    hand = g.merge(g.tube(sk.curve(pts, n=2), _spread_w(0.06, 0.028, 7), n=7), sk.fingers(pts[-1], Vector((0.4, 0.3, 0.8)), n=4, L=0.1, spread=0.02, r=0.018, hook=-0.3))
    B.move("sway", "hand", [(hand, B.main, True)], pts[0])
    _done(B, 0.94, -0.24, 0.5, 0.3, e)


def plan_signpost(B):
    """It was foggy on their road. It was not on yours: the post at the fork, the fog about the branch not taken, and its ledger of arrivals."""
    B.add(sk.disc((0, -0.08, 0.02), 0.44, thick=0.04, n=14, squash=0.9), "stone_sett", False)
    cob = None
    for i in range(6):      # the road, as far as it goes
        cob = g.merge(cob, g.ico((0.05 * (-1) ** i, -0.14 - 0.07 * i, 0.062), 0.05 - 0.004 * i, sub=1, scale=(1.2, 1.0, 0.25), rot=(0, 0, i)))
    B.add(cob, "stone_flag_pale", False)
    B.add(g.tube([(0, 0, 0.06), (0.01, 0, 0.86)], [0.03, 0.024], n=6), "wood_grey", False)
    B.add(g.cone((0.01, 0, 0.86), (0.01, 0, 0.92), 0.03, n=6), "wood_grey", False)
    for z, a, L, blank in ((0.76, 0.3, 0.3, False), (0.64, 2.6, 0.26, True), (0.52, -1.2, 0.28, False)):
        d = Vector((math.cos(a), math.sin(a), 0))
        R = Matrix.Rotation(a, 3, "Z")
        mid = Vector((0.01, 0, z)) + d * (L / 2 + 0.02)
        name = "paper_pale" if blank else "wood_grey_pale"
        B.add(g.box(mid, (L, 0.016, 0.07), rot=R), name, False)
        B.add(g.cone(mid + d * (L / 2), mid + d * (L / 2 + 0.06), 0.04, n=4), name, False)
        if not blank:
            n = d.cross(Z)
            B.add(g.merge(g.box(mid + n * 0.01 + Z * 0.012, (L * 0.7, 0.006, 0.009), rot=R), g.box(mid + n * 0.01 - Z * 0.014, (L * 0.5, 0.006, 0.009), rot=R)), "accent", False)
    # the ledger of arrivals, hung on it: one column is all blanks
    c, s = Vector((0.0, -0.05, 0.36)), 0.16
    R = Matrix.Rotation(0.1, 3, "Z") @ Matrix.Rotation(-0.15, 3, "X")
    book = [(g.box(c, (s * 0.78, s * 0.2, s), rot=R), "accent_dark"), (g.box(c + R @ Vector((0, 0, -s * 0.03)), (s * 0.7, s * 0.14, s * 1.0), rot=R), "paper"),
            (g.box(c + R @ Vector((0, -s * 0.11, 0)), (s * 0.84, s * 0.03, s * 0.14), rot=R), "accent_light"), (g.tube([(0.0, -0.03, 0.5), (0.0, -0.05, 0.44)], 0.005, n=3), "cord")]
    B.move("sway", "ledger", book, (0.0, -0.03, 0.5))
    curl(B, (0.0, 0, 0.14), 0.26, turns=1.6, w=0.09, axis=Z, start=2.2, rise=0.56, n=14, end=0.4)
    for i in range(6):
        a = 2 * math.pi * i / 6
        roll(B, (0.26 * math.cos(a), 0.22 * math.sin(a), 0.15), 0.11, (1.2, 1.0, 0.6), "under" if i % 2 else "main", a)
    deep(B, (0.1, -0.2, 0.13), 0.09, (1.4, 0.8, 0.6))
    h = Vector((-0.2, -0.16, 0.24))
    roll(B, h, 0.1, (1.1, 1.0, 0.9), "main")
    e = h + Vector((0, -0.112, 0.012))
    eyes(B, e, 0.04, 0.016)
    hanging(B, [(0.2, 0.1, -0.02), (-0.22, 0.0, -0.02), (0.0, -0.3, -0.02)])
    _done(B, 0.92, -0.26, 0.4, 0.32, e, crown=(0.01, 0, 0.92))


def plan_frost(B):
    """White needles on every edge of it, growing while you watch, and the flag it has settled on."""
    B.add(sk.disc((0, 0, 0.1), 0.36, thick=0.04, n=7, squash=0.84), "stone_sett", False)
    for i, (x, y, z, r) in enumerate(((0.0, 0.0, 0.36, 0.16), (0.16, 0.04, 0.3, 0.12), (-0.17, 0.02, 0.3, 0.13), (0.03, 0.02, 0.5, 0.11))):
        roll(B, (x, y, z), r, (1.15, 1.0, 0.75), "main" if i % 2 == 0 else "under", i)
    deep(B, (0.0, -0.08, 0.26), 0.1, (1.4, 0.7, 0.6))
    curl(B, (0.22, 0.04, 0.3), 0.12, turns=0.8, w=0.08, start=3.4, role="under")
    needles = None
    c = Vector((0, 0.01, 0.38))
    for i in range(22):
        a, b = i * 2.399, -0.3 + 1.2 * ((i * 7) % 10) / 10.0
        d = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b) * 0.9, math.sin(b)))
        b0 = c + Vector((d.x * 0.24, d.y * 0.19, d.z * 0.16))
        needles = g.merge(needles, sk.crystal(b0, b0 + d * (0.11 + 0.05 * (i % 3)), 0.016, n=4))
    B.add(needles, "frost_white", True)
    frost = None
    for i in range(9):
        a = 2 * math.pi * i / 9
        frost = g.merge(frost, g.blade((0.1 * math.cos(a), 0.09 * math.sin(a), 0.142), (0.33 * math.cos(a + 0.12), 0.28 * math.sin(a + 0.12), 0.142), 0.07, normal=(0, 0, 1), belly=0.55))
    B.add(frost, "frost_white", False)
    e = Vector((0, -0.175, 0.385))
    eyes(B, e, 0.05, 0.017, "wide")
    hanging(B, [(0.15, 0.05, 0.06), (-0.16, 0.02, 0.06), (0.0, -0.15, 0.06)])
    _done(B, 0.64, -0.18, 0.38, 0.26, e)


def _fern(root, tip, w, n=6, normal=Y):
    """A fern of frost: a rib, and barbs either side of it, shorter toward the tip."""
    root, tip = V(root), V(tip)
    d = tip - root
    side = d.cross(V(normal))
    side = side.normalized() if side.length > 1e-5 else X.copy()
    geo = g.tube([root, root + d * 0.5, tip], [w * 0.12, w * 0.09, w * 0.02], n=4)
    for i in range(n):
        t = 0.14 + 0.76 * i / (n - 1)
        p = root + d * t
        L = w * (1.0 - 0.75 * t)
        for s in (1, -1):
            geo = g.merge(geo, g.blade(p, p + side * s * L + d.normalized() * L * 0.6, w * 0.26, normal=normal, belly=0.3))
    return geo


def plan_hoar(B):
    """It grows along the inside of the window overnight, in the pattern of ferns, with a cold at
    the root of them. The window goes with it; its eyes look out through the clear of the glass."""
    w, h, y = 0.3, 0.42, 0.0
    c = Vector((0, y, 0.52))
    B.add(g.box(c, (2 * w, 0.02, 2 * h)), "pane", False)
    frame = g.merge(g.box(c + Vector((w + 0.025, 0, 0)), (0.06, 0.07, 2 * h + 0.11)), g.box(c - Vector((w + 0.025, 0, 0)), (0.06, 0.07, 2 * h + 0.11)),
                    g.box(c + Vector((0, 0, h + 0.025)), (2 * w + 0.11, 0.07, 0.06)), g.box(c - Vector((0, 0, h + 0.025)), (2 * w + 0.16, 0.11, 0.06)))
    B.add(frame, "accent_dark", False)
    B.add(g.merge(g.box(c, (0.03, 0.04, 2 * h)), g.box(c + Vector((0, 0, 0.05)), (2 * w, 0.04, 0.03))), "accent", False)       # the glazing bars
    B.add(g.box(c + Vector((0, -0.052, -h - 0.002)), (2 * w + 0.14, 0.012, 0.02)), "accent_light", False)
    # the ferns: from the low corner, up and across
    root = c + Vector((-w + 0.03, -0.014, -h + 0.03))
    ferns, small = None, None
    for i, (a, L) in enumerate(((0.12, 0.5), (0.42, 0.66), (0.72, 0.74), (1.02, 0.62), (1.32, 0.46))):
        tip = root + Vector((math.cos(a) * L * 0.86, 0, math.sin(a) * L))
        ferns = g.merge(ferns, _fern(root, tip, 0.13))
    for x, z, a in ((0.2, 0.3, 2.4), (0.24, -0.1, 2.9), (-0.05, 0.36, -1.8)):
        p = c + Vector((x, -0.014, z))
        small = g.merge(small, _fern(p, p + Vector((math.cos(a) * 0.16, 0, math.sin(a) * 0.16)), 0.06, n=4))
    B.add(ferns, "frost_white", False)
    B.add(small, "frost_white", False)
    B.move("pulse", "cold", [(g.ico(root + Vector((0.0, -0.01, 0.0)), 0.05, sub=2, scale=(1, 0.5, 1)), field("core", 3.4), True)], root)
    e = c + Vector((0.13, -0.016, 0.21))
    B.move("blink", "eyes", [(_pair(e, 0.045, 0.024, (1.0, 0.35, 0.9), 0.0), field("eyes", 2.8), True)], e)
    # the fog of the room it came out of, at the sill, already going
    for i, (x, r) in enumerate(((-0.2, 0.09), (0.0, 0.1), (0.2, 0.085))):
        roll(B, (x, -0.1, 0.07), r, (1.3, 0.9, 0.6), "main" if i % 2 else "under")
    curl(B, (0.3, -0.1, 0.12), 0.1, turns=0.8, w=0.07, start=3.2, role="under")
    _done(B, 1.0, -0.12, 0.5, 0.36, e)


def plan_blackice(B):
    """Clear and dark and smooth as glass, lying flat across the top step. You see the step through it and not it."""
    B.add(g.box((0, 0.02, 0.12), (0.94, 0.56, 0.12)), "stone_step", False)
    B.add(g.box((0, -0.36, 0.045), (0.94, 0.24, 0.09)), "stone_worn", False)
    B.add(g.merge(g.box((0, 0.02, 0.183), (0.012, 0.56, 0.006)), g.box((-0.3, 0.02, 0.183), (0.012, 0.56, 0.006)), g.box((0.3, 0.02, 0.183), (0.012, 0.56, 0.006))), "stone_dark", False)      # the joints of the step

    def slab(r, n, phase, thick, role, rx=0.0, ry=0.0, at=(0, 0, 0), sq=1.0):
        """A plate of it, and the line of its edge, which is all of it you see."""
        rim = g.ring((0, 0, thick), r * 0.95, r * 0.95 * sq, n=n, phase=phase)
        plate = sk.scaled(g.lathe([(r, 0.0), (r * 0.95, thick), (0.0, thick * 1.1)], n=n, phase=phase), (1, sq, 1))
        for geo, m in ((plate, _m(B, role)), (g.tube(rim + [rim[0]], 0.006, n=4), mat("accent_light"))):
            B.add(sk.shifted(sk.tilted(geo, rx=rx, ry=ry), at), m, False)
    slab(0.44, 9, 0.3, 0.02, "under", at=(0, 0.02, 0.182), sq=0.58)
    slab(0.2, 5, 0.9, 0.022, "main", rx=-0.5, ry=0.2, at=(-0.26, 0.2, 0.25))       # a plate of it, heaved up
    cracks = None
    for a, L in ((0.3, 0.36), (1.5, 0.2), (2.6, 0.38), (3.9, 0.22), (5.1, 0.24)):
        p1 = Vector((math.cos(a) * L, 0.02 + math.sin(a) * L * 0.58, 0.206))
        mid = p1 * 0.5 + Vector((-math.sin(a) * 0.04, math.cos(a) * 0.04, 0.103))
        cracks = g.merge(cracks, g.tube([Vector((0.02, 0.0, 0.206)), Vector((mid.x, mid.y, 0.206)), p1], [0.005, 0.004, 0.002], n=3))
    B.add(cracks, "frost_white", False)
    e = Vector((0.04, -0.1, 0.208))
    B.move("blink", "eyes", [(sk.tilted(_pair(e, 0.06, 0.03, (1.2, 0.3, 0.8), 0.0), rx=-1.35, about=e), field("eyes", 2.6), True)], e, up=(0, 0.975, 0.22))
    # the fog it was, going off the edge of the step
    for i, (x, y, r) in enumerate(((0.36, 0.2, 0.08), (0.42, 0.06, 0.065))):
        roll(B, (x, y, 0.24), r, (1.2, 1.0, 0.6), "main")
    curl(B, (0.44, 0.1, 0.3), 0.09, turns=0.8, w=0.06, start=2.6, role="main")
    hanging(B, [(0.3, 0.1, 0.06), (-0.3, 0.1, 0.06), (0.0, -0.3, 0.0)])
    _done(B, 0.62, -0.3, 0.12, 0.4, e, crown=(-0.14, 0.2, 0.4))


def plan_hound(B):
    """It runs low and fast across open ground on long streaming legs, ahead of any wind: fog in
    the shape of a hound, and it has a collar."""
    roll(B, (0, -0.12, 0.5), 0.16, (0.85, 1.3, 1.0), "main")           # a deep chest
    roll(B, (0, 0.06, 0.52), 0.12, (0.8, 1.5, 0.82), "under")
    roll(B, (0, 0.22, 0.535), 0.085, (0.7, 1.4, 0.7), "main")           # and not much behind it
    roll(B, (0, 0.0, 0.61), 0.085, (0.8, 2.6, 0.45), "trim")
    deep(B, (0, -0.1, 0.42), 0.09, (0.8, 1.4, 0.6))
    head = Vector((0, -0.37, 0.62))
    chain(B, [(0, -0.2, 0.56), (0, -0.29, 0.6), head], 0.08, 0.068, (0.9, 1.1, 0.9), ("main",))
    chain(B, [head + Vector((0, -0.06, -0.012)), head + Vector((0, -0.13, -0.03)), head + Vector((0, -0.2, -0.048)), head + Vector((0, -0.26, -0.062))], 0.05, 0.026, (0.85, 1.3, 0.75), ("main",))
    B.add(g.ico(head + Vector((0, -0.292, -0.062)), 0.015, sub=1), "void", True)
    B.add(sk.hoop((0, -0.265, 0.585), 0.075, 0.08, 0.014, n=12, u=X, v=Vector((0, 0.4, 0.92)).normalized(), sides=5), "accent", True)       # its collar
    B.add(g.ico((0, -0.3, 0.515), 0.018, sub=1, scale=(1, 0.5, 1.2)), "accent_light", True)
    ears = None
    for s in (1, -1):
        ears = g.merge(ears, g.blade(head + Vector((s * 0.045, 0.02, 0.045)), head + Vector((s * 0.085, 0.17, 0.15)), 0.07, normal=(s, 0, 1), belly=0.3))
    B.move("sway", "ears", [(ears, B.trim, True)], head + Vector((0, 0.03, 0.05)))
    for s in (1, -1):       # the legs: reaching in front, streaming behind
        tag = "l" if s > 0 else "r"
        wisps(B, [[(s * 0.09, -0.16, 0.42), (s * 0.1, -0.3, 0.3), (s * 0.1, -0.37, 0.16), (s * 0.1, -0.53, 0.04)]], w=0.1, role="main", what="fore_" + tag, swell=0.1)
        wisps(B, [[(s * 0.09, 0.22, 0.44), (s * 0.11, 0.32, 0.28), (s * 0.11, 0.5, 0.2), (s * 0.1, 0.72, 0.06)]], w=0.11, role="under", what="hind_" + tag, swell=0.1)
    curl(B, (0.0, 0.42, 0.56), 0.1, turns=0.7, w=0.08, axis=X, start=2.6, role="main", what="tail")
    wisps(B, [[(0.0, -0.05, 0.66), (0.01, 0.1, 0.72), (0.0, 0.26, 0.7)], [(0.0, 0.12, 0.62), (-0.01, 0.28, 0.67), (0.0, 0.44, 0.64)]], w=0.05, role="trim", what="mane")
    e = head + Vector((0, -0.092, 0.036))
    B.move("blink", "eyes", [(_pair(e, 0.042, 0.02, (1.0, 0.9, 0.7), 0.25), field("eyes", 2.8), True)], e)
    B.fog_riders.append((B.movers[-1], ""))
    _done(B, 0.74, -0.5, 0.48, 0.2, e, crown=head + Vector((0, 0.02, 0.08)))


def plan_flood(B):
    """Water, knee-deep, with the fog standing on it. Roots and fence-posts show through, and the mark of how high it came."""
    B.add(g.lathe([(0.44, 0.06), (0.4, 0.1), (0.26, 0.19), (0.12, 0.25), (0.0, 0.27)], n=20), B.main, True)
    B.add(g.lathe([(0.5, 0.05), (0.46, 0.068), (0.0, 0.07)], n=20), B.under, True)
    rip = g.merge(sk.hoop((0, 0, 0.14), 0.34, 0.34, 0.006, n=22, sides=4), sk.hoop((0, 0, 0.235), 0.2, 0.2, 0.006, n=18, sides=4))
    B.move("pulse", "ripples", [(rip, B.trim, True)], (0, 0, 0.18))
    posts = None
    for i, (x, y, lean) in enumerate(((-0.34, -0.12, 0.1), (-0.12, -0.2, -0.06), (0.12, -0.24, 0.12))):
        posts = g.merge(posts, g.tube([(x, y, 0.08), (x + lean * 0.3, y, 0.44 + 0.03 * i)], [0.026, 0.021], n=6))
    posts = g.merge(posts, g.tube([(-0.32, -0.12, 0.36), (-0.13, -0.2, 0.38), (0.14, -0.24, 0.37)], 0.012, n=4))
    B.add(posts, "wood_grey", False)
    marks = None
    for i, z in enumerate((0.2, 0.26, 0.32)):       # the gauge on the middle post: each mark a day's rise
        marks = g.merge(marks, sk.hoop((-0.12 - 0.014 * (z - 0.08) / 0.36, -0.2, z), 0.027, 0.027, 0.006, n=8, sides=4))
    B.add(marks, "accent_light", False)
    roots = None
    for a, rr in ((0.6, 0.3), (1.6, 0.34), (2.5, 0.3), (-0.4, 0.36)):
        d = Vector((math.cos(a), math.sin(a), 0))
        roots = g.merge(roots, g.tube([d * (rr - 0.14) + Z * 0.16, d * rr + Z * 0.26, d * (rr + 0.12) + Z * 0.08], [0.02, 0.016, 0.006], n=5))
    B.add(roots, B.mark("reeds", mat("reed")), True)
    # the fog, standing on it, and already going
    for i, (x, y, z, r) in enumerate(((0.0, 0.04, 0.44, 0.15), (0.17, 0.06, 0.39, 0.1), (-0.16, 0.08, 0.41, 0.11), (0.02, 0.04, 0.56, 0.09))):
        roll(B, (x, y, z), r, (1.2, 1.0, 0.6), "mist" if i % 2 == 0 else "mist_pale", i)
    deep(B, (0.0, -0.06, 0.36), 0.09, (1.5, 0.7, 0.5))
    curl(B, (0.2, 0.06, 0.52), 0.1, turns=0.8, w=0.07, start=3.0, role="mist")
    e = Vector((0.0, -0.3, 0.185))
    B.move("blink", "eyes", [(_pair(e, 0.052, 0.02, (1.1, 0.6, 0.75), 0.0), field("eyes", 2.8), True)], e)
    _done(B, 0.7, -0.32, 0.3, 0.44, e, crown=(0, 0.04, 0.66))


def plan_storm(B):
    """A grey wall with a bright ring turning inside it, and light flickering behind."""
    for i in range(6):
        a = 2 * math.pi * i / 6
        roll(B, (0.34 * math.cos(a), 0.2 * math.sin(a), 0.36), 0.2, (1.2, 1.0, 0.7), "under", a)
    roll(B, (0, 0.02, 0.56), 0.26, (1.1, 0.8, 1.1), "main")
    roll(B, (0.14, 0.03, 0.72), 0.2, (1.1, 0.8, 0.9), "main")
    roll(B, (-0.14, 0.03, 0.74), 0.19, (1.1, 0.8, 0.9), "under")
    for i in range(3):
        deep(B, (-0.26 + 0.26 * i, -0.12, 0.3), 0.12, (1.2, 0.7, 0.5))
    # the anvil of it
    roll(B, (0, 0, 0.95), 0.44, (1.2, 0.95, 0.2), "trim", 0.0, "anvil")
    for i in range(8):
        a = 2 * math.pi * i / 8
        roll(B, (0.5 * math.cos(a), 0.4 * math.sin(a), 0.96), 0.12, (1.3, 1.0, 0.5), "main" if i % 2 else "trim", a, "anvil")
    curl(B, (0.5, 0.0, 0.84), 0.12, turns=0.8, w=0.09, start=1.2, role="main")
    # the ring, in the hollow of it: it turns
    c = Vector((0, -0.23, 0.58))
    B.fog[""]["main"].append((c + Vector((0, 0.0, 0)), 0.13, (1.0, 0.6, 1.0), 0.0, -1))
    B.add(g.ico(c + Vector((0, 0.08, 0)), 0.15, sub=2, scale=(1.0, 0.45, 1.0)), "void", True)
    B.move("spin", "ring", [(sk.hoop(c, 0.11, 0.11, 0.014, n=18, u=X, v=Z, sides=5), field("ring", 3.4), True), (g.ico(c + Vector((0.11, 0, 0)), 0.022, sub=1), field("ring", 3.4), True)], c, up=(0.2, -0.95, 0.24))
    e = c + Vector((0, -0.02, 0.215))
    eyes(B, e, 0.075, 0.019, "wide")
    bolt = None
    for x0, y0 in ((0.22, -0.1), (-0.26, -0.04)):
        p = Vector((x0, y0, 0.3))
        pts = [p, p + Vector((0.05, 0, -0.08)), p + Vector((-0.02, 0, -0.13)), p + Vector((0.04, 0, -0.2)), p + Vector((0.0, 0, -0.27))]
        bolt = g.merge(bolt, g.tube(pts, [0.012, 0.01, 0.009, 0.007, 0.002], n=4))
    B.move("flick", "bolt", [(bolt, field("bolt", 4.2), False)], (0, -0.07, 0.3), up=(0, 0, -1))
    rain = None
    for i in range(9):
        x, y = -0.36 + 0.09 * i, 0.1 * math.sin(i * 1.7)
        rain = g.merge(rain, g.tube([(x, y, 0.26), (x - 0.05, y, 0.06)], [0.004, 0.003], n=3))
    B.move("bob", "rain", [(rain, "veil", False)], (0, 0, 0.2))
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
