"""WILDLINE genius lines: the Ember (docs/genius-evolutions.md, "The spirits").

Fire with nothing under it. The Starter is one coal with a small flame and two eyes; from there
it is a flame with a heart, the coal it began as at its foot with its eyes lit in the coal, and
something dark to be seen against, and
each path gives the fire a different temper: kept (Kept Fire's line: steady, round, in a ring
of stones, a pot, a window, a shell of its own scale), small and stubborn (the Rushlight's:
thin, upright, pale, with the things of study and of signalling), or spent all at once
(Wildfire's: ragged, leaning, thrown, running along the ground).

Fire glows in the partner's Shape colour and a body that is all glow reads as nothing, so
every flame here has three layers: a smoky fringe (the coat's under colour), the lit tongues,
and a heart; and every form stands on, in or behind something that is not fire.

An Ember's `body` (data/genius-bases/ember.json):
    plan     spark (the Starter), flame (the default), window, hollow, mast, wax, wheel, lash,
             star, dart (a comet, with ring: impact), line, mouth, whirl
    build    r (how wide the flame is), h (how tall), n (how many tongues), lean and side (it
             leans forward and aside), lift (how high its foot is), ragged; long (a dart's)
    eyes     dark, pale, old, one, none
    bed      what it burns on: coals, stones, logs, sticks, rush, bowl, basket, pot, book,
             lamp, frost
    shell    scale, petals, clinker, cage
    crown    twelve
    wings    thin
    ring     ground, dial, impact
    has      andirons, fireback, gimbal, pages, flashes, chain, hand, shimmer, cinders
    smoke    thread, stream
"""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import mat, field
import spirits_kit as sk
from spirits_kit import each, opt


class Fire:
    """A flame: where its foot and its heart are."""

    def __init__(self, B, bd):
        self.B = B
        self.r, self.h, self.n = bd.get("r", 0.085), bd.get("h", 0.36), int(bd.get("n", 5))
        self.lean = (bd.get("side", 0.0), -bd.get("lean", 0.0))
        self.foot = Vector((0, 0, 0.24 + bd.get("lift", 0.0)))
        self.heart = self.foot + Vector((self.lean[0], self.lean[1], 1.0)) * (self.h * 0.24)
        self.top = self.foot.z + self.h * 1.25
        self.width = 0.2

    def tip(self, t=1.0):
        return self.foot + Vector((self.lean[0], self.lean[1], 1.0)) * (self.h * t)


def fire(B, c, r, h, n=5, lean=(0, 0), turn=0.0, fringe=True, heart=True, strength=2.8, ragged=0.0):
    """A flame at c in three layers: the smoky fringe, the lit tongues, the heart."""
    c = V(c)
    tall = None if not ragged else ragged
    if fringe:
        B.add(sk.flame(c + Vector((0, 0.012, 0)), r * 1.2, h * 0.78, n=max(3, n - 1), turn=turn + 0.7, lean=lean, tall=tall), B.under)
    B.add(sk.flame(c, r, h, n=n, turn=turn, lean=lean, tall=tall), field("flame", strength))
    if heart:
        B.add(g.ico(c + Vector((lean[0], lean[1], 1.0)) * (h * 0.24), r * 0.5, sub=1, scale=(1, 1, 1.4)), field("core", 5.0))


def eyes_on(B, c, r, style="dark"):
    """Its face: the coal it began as, of radius r at c, and its eyes lit in the coal. A flame
    has no face of its own that can be seen; every Ember keeps its coal, and looks out of that."""
    if not style or style == "none":
        return
    c = V(c)
    B.add(g.ico(c, r, sub=1, scale=(1.08, 0.92, 0.9)), B.main, False)
    f = c + Vector((0, -r * 0.82, r * 0.12))
    if style == "pale":           # two pale points
        B.add(sk.eye_pair(f, r * 0.42, r * 0.22, scale=(1.0, 0.5, 1.0), slant=0.0), "bone")
    elif style == "old":          # the look of something that has seen many dawns
        B.add(sk.eye_pair(f + Vector((0, 0, -r * 0.04)), r * 0.42, r * 0.25, scale=(1.2, 0.45, 0.5), slant=-0.15), field("eyes", 3.4))
        br = None
        for s in (1, -1):
            br = g.merge(br, g.tongue([f + Vector((s * r * 0.1, -r * 0.1, r * 0.3)), f + Vector((s * r * 0.5, -r * 0.14, r * 0.36)), f + Vector((s * r * 0.9, 0.0, r * 0.14))], [r * 0.12, r * 0.26, r * 0.1], thick=0.6, normal=(0, -1, 0.4)))
        B.add(br, "ash")
    elif style == "one":          # one eye, watching
        B.add(g.ico(f + Vector((0, -r * 0.02, 0)), r * 0.46, sub=1, scale=(1.2, 0.4, 0.9)), field("eyes", 4.2))
        B.add(g.ico(f + Vector((0, -r * 0.18, 0)), r * 0.17, sub=0, scale=(0.7, 0.5, 1.3)), "void")
    else:
        B.add(sk.eye_pair(f, r * 0.42, r * 0.26, scale=(1.2, 0.45, 0.7), slant=0.3), field("eyes", 4.2))


def coals(B, c, r, n=6, lit=True):
    """A bed of coals about c."""
    c = V(c)
    geo, cracks = g.ico(c, r * 0.7, sub=0, scale=(1.1, 1.1, 0.6)), None
    for i in range(n):
        a = 2 * math.pi * i / n + 0.5
        geo = g.merge(geo, g.ico(c + Vector((r * 0.95 * math.cos(a), r * 0.95 * math.sin(a), 0.012 + 0.012 * (i % 2))), r * 0.46, sub=0, scale=(1.0, 0.8, 0.75), rot=(0.3 * i, 0.5 * i, a)))
        cracks = g.merge(cracks, g.ico(c + Vector((r * 0.62 * math.cos(a + 0.5), r * 0.62 * math.sin(a + 0.5), 0.03)), r * 0.15, sub=0))
    B.add(geo, B.main, False)
    if lit:
        B.add(cracks, field("crack", 2.5))


def cinders(B, c, r, n=5, seed=0.0):
    geo = None
    for i in range(n):
        a = seed + i * 2.4
        geo = g.merge(geo, g.ico(V(c) + Vector((r * (0.8 + 0.3 * math.sin(i)) * math.cos(a), r * (0.8 + 0.3 * math.sin(i)) * math.sin(a), 0.12 * i + 0.05)), 0.011 + 0.003 * (i % 2), sub=0))
    B.add(geo, field("cinder", 3.0))


# --- plans -------------------------------------------------------------------------------------

def plan_spark(B, spec):
    """The Starter: a coal's worth of fire with nothing under it."""
    F = Fire(B, {"r": 0.05, "h": 0.2, "n": 3, "lift": 0.07})
    c = Vector((0, 0, 0.23))
    B.add(g.ico(c, 0.09, sub=1, scale=(1.1, 1.0, 0.85)), B.main, False)
    cracks = None
    for i, (a, b) in enumerate(((0.6, 0.5), (2.2, 0.1), (3.9, 0.6), (5.2, 0.2))):
        p0 = c + Vector((0.095 * math.cos(a) * math.cos(b), 0.085 * math.sin(a) * math.cos(b), 0.075 * math.sin(b)))
        p1 = c + Vector((0.095 * math.cos(a + 0.6) * math.cos(b - 0.5), 0.085 * math.sin(a + 0.6) * math.cos(b - 0.5), 0.075 * math.sin(b - 0.5)))
        cracks = g.merge(cracks, g.tube([p0, (p0 + p1) / 2 * 1.0 + (((p0 + p1) / 2) - c) * 0.06, p1], [0.004, 0.008, 0.003], n=3))
    B.add(cracks, field("crack", 2.8))
    B.add(sk.eye_pair(c + Vector((0, -0.086, 0.012)), 0.036, 0.022, scale=(1.1, 0.5, 0.9), slant=0.1), field("eyes", 4.2))
    fire(B, c + Vector((0, 0.0, 0.06)), 0.042, 0.12, n=3, fringe=False, turn=0.4)
    cinders(B, c + Vector((0, 0, 0.05)), 0.13, n=3, seed=1.0)
    F.heart, F.top = c, 0.5
    B.frame(0.5, front=-0.1, mid=0.23, half=0.1)
    B.socket("socket_eyes", c + Vector((0, -0.095, 0.012)))
    return F


def plan_flame(B, spec):
    bd = {2: {"r": 0.085, "h": 0.34}, 3: {"r": 0.095, "h": 0.42}}.get(B.level, {"r": 0.105, "h": 0.5})
    bd = dict(bd)
    bd.update(spec.get("build", {}))
    F = Fire(B, bd)
    return F


def _draw_flame(B, F, spec):
    eyes, _ = opt(spec.get("eyes", "dark"))
    shell = [st for st, _ in each(spec.get("shell"))]
    fire(B, F.foot, F.r, F.h, n=F.n, lean=F.lean, ragged=spec.get("build", {}).get("ragged", 0.0))
    if eyes and eyes != "none" and "clinker" not in shell:
        # its coal, at the front of its foot, where the tongues do not cross it
        rr = max(F.r * 0.6, 0.042)
        out = 1.3 if "scale" in shell else 0.8
        ringed = max([size for st, size in each(spec.get("bed")) if st == "stones"] or [0.0])      # it looks out over its ring of stones
        at = F.foot + Vector((0, -max(F.r * out, 0.036), rr * 0.7 + 0.05 * ringed))
        eyes_on(B, at, rr, eyes)
        F.eye_at = at + Vector((0, -rr, rr * 0.12))


def plan_window(B, spec):
    """A single ember behind glass, with a pale heart. Frost on the pane does not form near it."""
    F = Fire(B, {"r": 0.04, "h": 0.14, "n": 3})
    w, h, z0 = 0.2, 0.46, 0.2
    frame = g.merge(g.box((w, 0, z0 + h / 2), (0.05, 0.07, h)), g.box((-w, 0, z0 + h / 2), (0.05, 0.07, h)), g.box((0, -0.02, z0 - 0.02), (2 * w + 0.16, 0.14, 0.05)))
    B.add(frame, "timber", False)
    B.add(sk.arc((0, 0, z0 + h), w, w * 0.9, 0.0, math.pi, 0.028, n=8, u=X, v=Z, sides=4), "timber", False)
    bars = g.merge(g.box((0, 0, z0 + h / 2 + 0.06), (0.022, 0.03, h + 0.16)), g.box((0, 0, z0 + h * 0.36), (2 * w, 0.03, 0.022)), g.box((0, 0, z0 + h * 0.74), (2 * w, 0.03, 0.022)))
    B.add(bars, "timber", False)
    # the glass: dark, and behind the frame
    B.add(g.box((0, 0.025, z0 + h / 2), (2 * w, 0.012, h)), "pane", False)
    B.add(sk.shifted(sk.tilted(sk.disc((0, 0, 0), w - 0.01, thick=0.012, n=12), rx=math.pi / 2), (0, 0.031, z0 + h)), "pane", False)
    # frost in the corners of it, and none near the ember
    frost = None
    for sx, zz in ((1, 0.9), (-1, 0.9), (1, 0.55), (-1, 0.6), (0.2, 1.2), (-0.3, 1.16)):
        base = Vector((sx * (w - 0.03), -0.012, z0 + h * zz))
        for k in range(3):
            a = 2.4 + k * 0.7 if sx > 0 else 0.75 - k * 0.7
            frost = g.merge(frost, g.blade(base, base + Vector((math.cos(a) * 0.1, -0.004, math.sin(a) * 0.1)), 0.03, normal=-Y, belly=0.4))
    B.add(frost, "ice_pale", False)
    # the ember, on the sill behind the glass
    c = Vector((0.0, -0.035, z0 + 0.075))
    B.add(g.ico(c, 0.06, sub=1, scale=(1.1, 0.8, 0.85)), B.main, False)
    B.add(g.ico(c + Vector((0, -0.03, 0.01)), 0.03, sub=1), "ice_pale")
    B.add(sk.eye_pair(c + Vector((0, -0.056, 0.012)), 0.024, 0.012, scale=(1.1, 0.5, 0.9), slant=0.1), "void")
    fire(B, c + Vector((0, 0, 0.04)), 0.04, 0.16, n=3, fringe=False)
    B.add(sk.hoop(c + Vector((0, -0.01, 0.0)), 0.11, 0.1, 0.006, n=12, u=X, v=Z, sides=3), field("halo", 1.6))
    F.heart, F.top, F.foot = c, z0 + h + w * 0.9, c
    B.frame(F.top, front=-0.08, mid=z0 + h * 0.5, half=w + 0.04)
    B.socket("socket_eyes", c + Vector((0, -0.07, 0.012)))
    return F


def plan_hollow(B, spec):
    """It burns pale and gives no heat: a flame you can see through."""
    F = Fire(B, {"r": 0.1, "h": 0.52, "n": 3})
    c = F.foot
    # the outline of a flame, and nothing in it
    for k, (m, w) in enumerate(((field("cold", 2.2), 0.03), ("ice_pale", 0.022), (field("cold", 2.2), 0.03))):
        a = 2 * math.pi * k / 3 + 0.5
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [c + d * 0.03, c + d * 0.13 + Z * 0.1, c + d * 0.15 + Z * 0.24, c + d * 0.09 + Z * 0.42, c + sk.rotz(d, 0.6) * 0.03 + Z * 0.56, c + Z * 0.66]
        B.add(g.tongue(pts, [w, w * 1.5, w * 1.5, w * 1.2, w * 0.8, 0.003], thick=0.35, normal=d), m)
    B.add(g.ico(c + Z * 0.26, 0.026, sub=1), "bone")
    B.add(g.ico(c + Vector((0, -0.02, 0.26)), 0.011, sub=0), "void")
    frost = None
    for i in range(10):
        a = 2 * math.pi * i / 10
        frost = g.merge(frost, g.blade(c + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), -0.03)), c + Vector((0.22 * math.cos(a + 0.12), 0.22 * math.sin(a + 0.12), -0.05 + 0.012 * (i % 3))), 0.07, normal=(0, 0, 1), belly=0.55))
    B.add(frost, "ice_pale", False)
    B.add(sk.hoop(c + Z * -0.04, 0.3, 0.3, 0.005, n=18, sides=3), "veil", False)
    F.heart, F.top = c + Z * 0.26, c.z + 0.66
    B.frame(F.top, front=-0.14, mid=c.z + 0.26, half=0.16)
    B.socket("socket_eyes", c + Vector((0, -0.03, 0.26)))
    return F


def plan_mast(B, spec):
    """A pale flame that sits on the highest point of anything."""
    F = Fire(B, {"r": 0.07, "h": 0.36, "n": 3})
    B.add(g.tube([(0, 0, 0.12), (0, 0, 0.95)], [0.03, 0.02], n=6), "timber", False)
    B.add(g.tube([(-0.26, 0, 0.66), (0.26, 0, 0.66)], [0.016, 0.016], n=5), "timber", False)
    for z in (0.2, 0.5, 0.66, 0.9):
        B.add(g.lathe([(0.034 - 0.01 * z, -0.012), (0.036 - 0.01 * z, 0.012)], n=6, centre=(0, 0, z), caps=False), "metal_iron", False)
    ropes = None
    for s in (1, -1):
        ropes = g.merge(ropes, g.tube([(s * 0.25, 0, 0.66), (0, 0, 0.93)], [0.005, 0.005], n=3), g.tube([(s * 0.25, 0, 0.66), (s * 0.08, 0.0, 0.2)], [0.005, 0.005], n=3))
    B.add(ropes, "cord", False)
    # the prow it stands on, and the black water
    B.add(g.tongue([(0, 0.2, 0.1), (0, 0.0, 0.14), (0, -0.2, 0.2), (0, -0.34, 0.3)], [0.2, 0.22, 0.14, 0.02], thick=0.5, normal=Z), "timber", False)
    B.add(sk.disc((0, -0.02, 0.0), 0.36, thick=0.02, n=12, squash=0.8), "water_dark")
    B.add(sk.hoop((0, -0.3, 0.025), 0.1, 0.07, 0.005, n=10, sides=3), "water_pale", False)
    # the fire at the masthead: forked, and at the ends of the yard
    top = Vector((0, 0, 0.95))
    for i, (dx, hh) in enumerate(((0.0, 0.36), (0.09, 0.24), (-0.1, 0.27))):
        b0 = top + Vector((dx * 0.3, 0, 0))
        B.add(g.tongue([b0, b0 + Vector((dx * 0.8, 0, hh * 0.45)), b0 + Vector((dx * 1.5, 0.01, hh * 0.8)), b0 + Vector((dx * 1.2, 0, hh))], [0.05, 0.06, 0.035, 0.003], thick=0.4, normal=-Y), field("cold", 2.6) if i != 1 else mat("ice_pale"))
    B.add(g.ico(top + Z * 0.06, 0.035, sub=1, scale=(1, 1, 1.3)), field("core", 4.6))
    eyes_on(B, top + Z * 0.06, 0.035, "dark")
    for s in (1, -1):
        b0 = Vector((s * 0.26, 0, 0.66))
        B.add(sk.flame(b0, 0.026, 0.12, n=3, turn=s), field("cold", 2.4))
    F.heart, F.top, F.foot = top + Z * 0.06, 0.98, top
    B.frame(0.98, front=-0.08, mid=0.6, half=0.2)
    B.socket("socket_eyes", top + Vector((0, -0.04, 0.065)))
    return F


def plan_wax(B, spec):
    """It burns red as wax, with a drip that never falls."""
    F = Fire(B, {"r": 0.05, "h": 0.22, "n": 3})
    R = Matrix.Rotation(0.35, 3, "Y")
    base, tip = Vector((0.12, 0, 0.3)), Vector((0.12, 0, 0.3)) + R @ Vector((0, 0, 0.42))
    B.add(g.tube([base, tip], [0.036, 0.034], n=6), "wax_red", False)
    B.add(g.ico(tip, 0.04, sub=1, scale=(1.0, 1.0, 0.6)), "wax_red")
    # the drip that never falls
    d0 = tip + Vector((-0.03, -0.01, -0.01))
    B.add(g.tongue([d0, d0 + Vector((-0.012, 0, -0.06)), d0 + Vector((-0.014, 0, -0.13))], [0.03, 0.022, 0.03], thick=0.9), "wax_red")
    B.add(g.ico(d0 + Vector((-0.014, 0, -0.15)), 0.026, sub=1, scale=(1, 1, 1.25)), "wax_red")
    c = tip + Vector((0.0, 0, 0.02))
    fire(B, c, 0.05, 0.24, n=3)
    eyes_on(B, c + Z * 0.058, 0.026, "dark")
    # what it seals: a letter, a seal, a ribbon, the stamp
    lc = Vector((-0.05, -0.02, 0.2))
    B.add(g.box(lc, (0.3, 0.2, 0.014), rot=(0.0, -0.12, 0.3)), "paper", False)
    B.add(g.box(lc + Vector((0, 0, 0.012)), (0.3, 0.012, 0.01), rot=(0.0, -0.12, 0.3 + 0.6)), "ash", False)
    B.add(g.lathe([(0.0, 0.0), (0.04, 0.004), (0.045, 0.012), (0.0, 0.018)], n=9, centre=lc + Vector((-0.02, -0.01, 0.01))), "wax_red")
    B.add(g.ico(lc + Vector((-0.02, -0.01, 0.03)), 0.012, sub=0), field("seal", 3.0))
    for a in (0.4, -0.5):
        p = lc + Vector((-0.02, -0.03, 0.008))
        B.add(g.tongue([p, p + Vector((0.03 * a, -0.1, -0.03)), p + Vector((0.1 * a, -0.17, -0.1))], [0.03, 0.03, 0.02], thick=0.2, normal=Z), "cloth_rag")
    s0 = Vector((-0.2, 0.08, 0.2))
    B.add(g.lathe([(0.03, 0.0), (0.027, 0.02), (0.012, 0.03), (0.012, 0.09), (0.024, 0.12), (0.0, 0.135)], n=6, centre=s0), "metal_brass", False)
    F.heart, F.top, F.foot = c + Z * 0.058, tip.z + 0.26, c
    B.frame(F.top, front=-0.1, mid=0.42, half=0.2)
    B.socket("socket_eyes", c + Vector((0, -0.03, 0.06)))
    return F


def plan_wheel(B, spec):
    """It does not stay in one place but runs in a ring from point to point, brighter each lap."""
    F = Fire(B, {"r": 0.07, "h": 0.2})
    c = Vector((0, 0, 0.5))
    R = 0.3
    ring = sk.hoop(c, R, R, 0.01, n=22, u=X, v=Z, sides=3)
    B.add(sk.tilted(ring, rz=0.35, about=c), "metal_dark", False)
    last = None
    for i in range(8):
        a = math.pi / 2 + 2 * math.pi * (i + 1) / 8
        k = 0.3 + 0.7 * (i + 1) / 8
        p = sk.rotz(c + Vector((R * math.cos(a), 0, R * math.sin(a))), 0.35)
        out = (p - c).normalized()
        tang = sk.rotz(Vector((-math.sin(a), 0, math.cos(a))), 0.35)
        B.add(g.tongue([p - tang * 0.03 * k, p + out * 0.06 * k, p + out * 0.11 * k - tang * 0.11 * k, p + out * 0.1 * k - tang * 0.24 * k], [0.07 * k, 0.1 * k, 0.07 * k, 0.004], thick=0.45, normal=-Y), field("flame", 2.0 + 1.2 * k))
        B.add(g.ico(p, 0.035 * k, sub=1), field("core", 4.6) if i == 7 else B.main)
        last = p
    eyes_on(B, last, 0.036, "dark")
    cinders(B, c + Vector((0, 0, -0.35)), 0.24, n=4, seed=2.0)
    F.heart, F.top, F.foot = last, c.z + R + 0.12, c
    B.frame(F.top, front=-0.08, mid=c.z, half=R)
    B.socket("socket_eyes", last + Vector((0, -0.04, 0)))
    return F


def plan_lash(B, spec):
    """A long tongue of flame that wraps whatever you hold, and leaves a bright edge on it."""
    F = Fire(B, {"r": 0.07, "h": 0.3})
    a, b = Vector((0.16, 0, 0.14)), Vector((-0.12, 0, 0.92))
    d = (b - a).normalized()
    B.add(g.blade(a + d * 0.16, b, 0.11, thick=0.016, normal=-Y, belly=0.2), "metal_dark", False)
    B.add(g.box(a + d * 0.15, (0.2, 0.03, 0.03), rot=(0, -0.37, 0)), "metal_iron", False)
    B.add(g.tube([a, a + d * 0.14], [0.02, 0.018], n=6), "leather_dark", False)
    B.add(g.ico(a - d * 0.01, 0.028, sub=1), "metal_iron", False)
    B.add(g.tube([a + d * 0.2 + Vector((0.05, -0.012, 0.02)), b + Vector((0, -0.012, 0))], [0.005, 0.003], n=3), field("edge", 2.8))
    # the lash, wound up the blade
    pts, ws = [], []
    side = Vector((d.z, 0, -d.x))
    n = 16
    for i in range(n + 1):
        t = i / n
        ang = t * 2 * math.pi * 2.3
        p = a + d * (0.2 + 0.62 * t) + side * (0.085 * math.cos(ang)) + Y * (0.085 * math.sin(ang))
        pts.append(p)
        ws.append(0.07 * (0.5 + 0.5 * math.sin(math.pi * min(1.0, t * 1.15))) + 0.01)
    B.add(g.tongue(pts, ws, thick=0.35), field("flame", 2.8))
    head = pts[-1] + d * 0.05
    B.add(g.ico(head, 0.05, sub=1, scale=(1, 1, 1.2)), field("core", 4.8))
    B.add(sk.flame(head, 0.05, 0.2, n=3, lean=(-0.3, 0)), field("flame", 2.8))
    B.add(sk.flame(head + Vector((0, 0.012, 0)), 0.062, 0.15, n=3, turn=1.0, lean=(-0.3, 0)), B.under)
    eyes_on(B, head, 0.05, "dark")
    cinders(B, Vector((0, 0, 0.3)), 0.2, n=4, seed=0.4)
    F.heart, F.top, F.foot = head, head.z + 0.22, a
    B.frame(F.top, front=-0.12, mid=0.55, half=0.2)
    B.socket("socket_eyes", head + Vector((0, -0.055, 0)))
    return F


def plan_star(B, spec):
    """At arm's length it has a colour. Close to, it is white, with no colour at all at the centre."""
    F = Fire(B, {"r": 0.1, "h": 0.2})
    c = Vector((0, 0, 0.5))
    B.add(g.ico(c, 0.1, sub=1), "bone")
    lit, pale = None, None
    dirs = []
    for i in range(14):
        a, b = i * 2.399, math.asin(-0.85 + 1.7 * (i + 0.5) / 14)
        dirs.append(Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b))))
    for i, d in enumerate(dirs):
        L = 0.2 + 0.12 * ((i * 5) % 3) / 2
        bl = g.cone(c + d * 0.085, c + d * (0.085 + L), 0.035, n=4)
        if i % 3 == 0:
            pale = g.merge(pale, bl)
        else:
            lit = g.merge(lit, bl)
    B.add(lit, field("flame", 3.2), False)
    B.add(pale, "bone", False)
    eyes_on(B, c, 0.1, "dark")
    # what it has been close to: scorched plate, turning round it
    plates = None
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        p = c + Vector((0.42 * math.cos(a), 0.42 * math.sin(a), 0.1 * math.sin(a * 2)))
        plates = g.merge(plates, g.box(p, (0.1, 0.012, 0.13), rot=(0.3 * i, 0.2, a + 1.57)))
    B.add(sk.tilted(plates, rx=0.3, about=c), "soot", False)
    B.add(sk.tilted(sk.hoop(c, 0.42, 0.42, 0.005, n=22, sides=3), rx=0.3, about=c), field("halo", 1.8))
    F.heart, F.top, F.foot = c, c.z + 0.36, c
    B.frame(c.z + 0.2, front=-0.12, mid=c.z, half=0.2)
    B.socket("socket_eyes", c + Vector((0, -0.105, 0.012)))
    return F


def plan_dart(B, spec):
    """Two short wings of flame, swept back: it is gone as soon as it is pointed."""
    bd = {"long": 1.0}
    bd.update(spec.get("build", {}))
    k = bd["long"]
    comet = any(st == "impact" for st, _ in each(spec.get("ring")))
    F = Fire(B, {"r": 0.08, "h": 0.2})
    c = Vector((0, -0.12, 0.55 if not comet else 0.4))
    tilt = -0.2 if not comet else -0.55         # nose down
    items = []
    head = g.merge(g.ico(Vector((0, 0, 0)), 0.1, sub=1, scale=(0.9, 1.25, 0.85)), g.cone(Vector((0, -0.09, 0)), Vector((0, -0.26, -0.01)), 0.07, n=6))
    items.append((head, B.main, False))
    items.append((_cracks(Vector((0, 0, 0)), 0.1, 6, 0.9, (0.9, 1.25, 0.85)), field("crack", 3.0), None))
    if comet:
        items.append((g.ico(Vector((0, -0.02, 0)), 0.075, sub=1, scale=(0.9, 1.3, 0.85)), mat("bone"), None))
    items.append((sk.eye_pair(Vector((0, -0.125, 0.03)), 0.045, 0.022, scale=(1.2, 0.6, 0.6), slant=0.35), field("eyes", 4.4), None))
    for s in (1, -1):
        wing = None
        for i in range(3 if not comet else 2):
            b0 = Vector((s * 0.07, 0.0 + 0.05 * i, 0.02))
            wing = g.merge(wing, g.tongue([b0, b0 + Vector((s * 0.16, 0.12, 0.05)) * (1 - 0.15 * i), b0 + Vector((s * 0.26, 0.36, 0.07)) * (1 - 0.15 * i)], [0.1, 0.09, 0.004], thick=0.25, normal=Z))
        items.append((wing, field("wings", 2.8), None))
    tail, dark = None, None
    n = 3 if not comet else 5
    for i in range(n):
        a = 2 * math.pi * i / n
        off = Vector((0.045 * math.cos(a), 0.06, 0.04 * math.sin(a)))
        L = (0.5 + 0.12 * (i % 2)) * k
        tg = g.tongue([off, off * 1.6 + Vector((0, L * 0.4, 0.01)), off * 1.3 + Vector((0, L * 0.75, 0.0)), off * 0.4 + Vector((0, L, 0))], [0.1, 0.11, 0.07, 0.004], thick=0.4, normal=(math.cos(a), 0, math.sin(a)))
        if i % 3 == 2:
            dark = g.merge(dark, tg)
        else:
            tail = g.merge(tail, tg)
    items.append((tail, field("flame", 2.8), None))
    items.append((dark, B.under, None))
    R = Matrix.Rotation(tilt, 3, "X")
    for geo, m, sm in items:
        if geo:
            B.add(([c + R @ V(p) for p in geo[0]], geo[1]), m, sm)
    F.heart, F.top, F.foot = c, c.z + 0.3 + 0.5 * k * math.sin(-tilt), c
    B.frame(c.z + 0.14 + 0.5 * k * math.sin(-tilt), front=c.y - 0.24, mid=c.z, half=0.2)
    B.socket("socket_eyes", c + R @ Vector((0, -0.14, 0.03)))
    F.nose = c + R @ Vector((0, -0.26, -0.01))
    return F


def _cracks(c, r, n, seed, squash=(1, 1, 1)):
    geo = None
    for i in range(n):
        a, b = seed + i * 2.4, 0.5 + 0.9 * math.sin(i * 1.7 + seed)
        p0 = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b))) * r
        a2, b2 = a + 0.5, b - 0.55
        p1 = Vector((math.cos(a2) * math.cos(b2), math.sin(a2) * math.cos(b2), math.sin(b2))) * r
        mid = ((p0 + p1) / 2).normalized() * r
        geo = g.merge(geo, g.tube([Vector((p.x * squash[0], p.y * squash[1], p.z * squash[2])) + V(c) for p in (p0, mid, p1)], [0.004, 0.009, 0.003], n=3))
    return geo


def plan_line(B, spec):
    """A low wide flame that runs along the ground in a line and puts down runners."""
    F = Fire(B, {"r": 0.07, "h": 0.2})
    z0 = 0.06
    B.add(sk.disc((0, 0.14, z0 - 0.03), 0.44, thick=0.02, n=12, squash=0.5), "soot")
    stub = None
    for i in range(14):
        x, y = -0.38 + 0.058 * i, 0.12 + 0.07 * math.sin(i * 1.7)
        stub = g.merge(stub, g.cone((x, y, z0 - 0.01), (x + 0.01, y + 0.01, z0 + 0.05 + 0.02 * (i % 3)), 0.012, n=3))
    B.add(stub, "stubble", False)
    mid = None
    for i in range(7):
        t = (i - 3) / 3.0
        p = Vector((0.36 * t, -0.04 - 0.12 * (1 - t * t), z0))
        k = 1.0 - 0.45 * abs(t)
        fire(B, p, 0.06 * k, 0.26 * k, n=3, turn=i * 1.1, lean=(0.0, -0.25), heart=(i == 3))
        if i == 3:
            mid = p + Vector((0, -0.25, 1.0)) * (0.26 * 0.24)
    eyes_on(B, mid, 0.03, "dark")
    # the runners it puts down, and the grass it has not reached yet
    run, buds = None, None
    for i, (x, L) in enumerate(((-0.3, 0.2), (-0.14, 0.3), (0.02, 0.24), (0.18, 0.32), (0.32, 0.18))):
        p0 = Vector((x, -0.16, z0 - 0.02))
        pts = [p0, p0 + Vector((0.03, -L * 0.35, 0.0)), p0 + Vector((-0.03, -L * 0.7, 0.0)), p0 + Vector((0.02, -L, 0.0))]
        run = g.merge(run, g.tube(pts, [0.012, 0.01, 0.008, 0.005], n=3))
        buds = g.merge(buds, g.ico(pts[-1] + Z * 0.01, 0.016, sub=0))
    B.add(run, field("runner", 2.4))
    B.add(buds, field("cinder", 3.6))
    grass = None
    for i in range(9):
        x = -0.4 + 0.1 * i
        b0 = Vector((x, -0.5 - 0.03 * (i % 2), z0 - 0.03))
        grass = g.merge(grass, g.blade(b0, b0 + Vector((0.03 * math.sin(i), 0.04, 0.14 + 0.04 * (i % 3))), 0.03, normal=Y, belly=0.3))
    B.add(grass, "grass_dry")
    F.heart, F.top, F.foot = mid, z0 + 0.34, Vector((0, -0.16, z0))
    B.frame(z0 + 0.3, front=-0.3, mid=z0 + 0.1, half=0.36)
    B.socket("socket_eyes", mid + Vector((0, -0.04, 0)))
    return F


def plan_mouth(B, spec):
    """A wide mouth of flame, low to the ground, with black stubble behind it."""
    F = Fire(B, {"r": 0.1, "h": 0.3})
    z0 = 0.05
    B.add(sk.disc((0, 0.2, z0 - 0.03), 0.5, thick=0.02, n=12, squash=0.6), "soot")
    stub = None
    for i in range(18):
        x, y = -0.42 + 0.05 * i, 0.16 + 0.1 * math.sin(i * 1.7) + 0.08 * (i % 2)
        stub = g.merge(stub, g.cone((x, y, z0 - 0.01), (x + 0.01, y + 0.01, z0 + 0.05 + 0.02 * (i % 3)), 0.012, n=3))
    B.add(stub, "stubble", False)
    # the jaws: an arch of tongues, and a row under it
    c = Vector((0, -0.05, z0))
    up, dark, low = None, None, None
    n = 11
    for i in range(n):
        a = math.pi * (0.06 + 0.88 * i / (n - 1))
        p = c + Vector((0.4 * math.cos(a), 0.0, 0.36 * math.sin(a)))
        out = Vector((math.cos(a), 0, math.sin(a)))
        tg = g.tongue([p - out * 0.02, p + out * 0.1 + Vector((0, -0.03, 0)), p + out * 0.24 + Vector((0, 0.04, 0.02))], [0.12, 0.11, 0.004], thick=0.4, normal=-Y)
        tooth = g.blade(p + Vector((0, -0.01, 0)), p - out * 0.11 + Vector((0, -0.04, 0)), 0.055, normal=-Y, belly=0.3)
        if i % 3 == 1:
            dark = g.merge(dark, tg)
        else:
            up = g.merge(up, tg)
        low = g.merge(low, tooth)
    for i in range(7):
        x = -0.3 + 0.1 * i
        low = g.merge(low, g.blade(Vector((x, -0.08, z0)), Vector((x + 0.01, -0.1, z0 + 0.09 + 0.03 * (i % 2))), 0.06, normal=-Y, belly=0.3))
    B.add(up, field("flame", 2.8))
    B.add(dark, B.under)
    B.add(low, field("teeth", 3.4))
    throat = g.lathe([(0.36, 0.0), (0.2, 0.05), (0.0, 0.07)], n=12)
    B.add(([Vector((p.x, c.y + 0.03 + p.z, z0 + abs(p.y) * 0.92)) for p in throat[0]], throat[1]), "void")
    ec = c + Vector((0, -0.02, 0.5))
    B.add(sk.eye_pair(ec, 0.11, 0.035, scale=(1.3, 0.5, 0.6), slant=0.4), field("eyes", 4.6))
    smoke = None
    for i, (x, hh) in enumerate(((-0.3, 0.5), (-0.1, 0.66), (0.12, 0.58), (0.32, 0.46))):
        smoke = g.merge(smoke, sk.smoke_thread((x, 0.3, z0), hh, sway=0.05, w=0.09, n=5))
    B.add(smoke, "smoke")
    F.heart, F.top, F.foot = ec, z0 + 0.62, c
    B.frame(z0 + 0.6, front=-0.12, mid=z0 + 0.25, half=0.4)
    B.socket("socket_eyes", ec + Vector((0, -0.03, 0)))
    return F


def plan_whirl(B, spec):
    """A turning column of flame on one foot, with the air standing clear and still round it."""
    F = Fire(B, {"r": 0.1, "h": 0.8})
    B.add(g.tube([(0, 0, 0.1), (0.01, 0, 0.4), (-0.01, 0.01, 0.72), (0, 0, 0.98)], [0.01, 0.022, 0.018, 0.004], n=4), field("core", 4.4))
    for k, m in enumerate((field("flame", 2.8), B.main, B.under, field("flame", 2.4))):
        pts = g.spiral((0, 0, 0.08), 0.04, 0.26, 2.3, 0.86, n=30, axis=Z, start=2 * math.pi * k / 4)
        wid = [0.014 + 0.06 * (i / 30.0) for i in range(31)]
        B.add(g.tube(pts, wid, n=4, flat=0.3, up=Z), m)
    top = None
    for i in range(6):
        a = 2 * math.pi * i / 6
        b0 = Vector((0.22 * math.cos(a), 0.22 * math.sin(a), 0.9))
        top = g.merge(top, g.tongue([b0, b0 + Vector((-0.08 * math.sin(a), 0.08 * math.cos(a), 0.1)), b0 + Vector((-0.2 * math.sin(a), 0.2 * math.cos(a), 0.2))], [0.08, 0.07, 0.004], thick=0.4, normal=(math.cos(a), math.sin(a), 0)))
    B.add(top, field("flame", 2.8))
    grit, grass = None, None
    for i in range(12):
        a, t = i * 2.4, (i % 6) / 6.0
        c = Vector(((0.1 + 0.2 * t) * math.cos(a), (0.1 + 0.2 * t) * math.sin(a), 0.18 + 0.7 * t))
        if i % 3:
            grit = g.merge(grit, g.ico(c, 0.014, sub=0, rot=(a, a * 2, 0)))
        else:
            grass = g.merge(grass, g.blade(c, c + Vector((0.08 * math.sin(a), -0.08 * math.cos(a), 0.03)), 0.016, normal=(0, 0, 1)))
    B.add(grit, B.under, False)
    B.add(grass, B.mark("grass", mat("reed")))
    B.add(g.lathe([(0.12, 0.04), (0.07, 0.065), (0.0, 0.075)], n=9), B.under)
    # the air stands clear round it
    B.add(sk.hoop((0, 0, 0.05), 0.42, 0.42, 0.006, n=22, sides=3), "veil", False)
    B.add(sk.hoop((0, 0, 0.05), 0.5, 0.5, 0.004, n=24, sides=3), "veil", False)
    ec = Vector((0, -0.1, 0.5))
    B.add(sk.eye_pair(ec, 0.045, 0.024, scale=(1.2, 0.5, 0.6), slant=0.35), "void")
    B.add(g.ico(ec + Vector((0, 0.035, 0)), 0.085, sub=1, scale=(1.2, 0.6, 0.8)), field("core", 4.6))
    F.heart, F.top, F.foot = ec, 1.1, Vector((0, 0, 0.1))
    B.frame(1.0, front=-0.14, mid=0.5, half=0.24)
    B.socket("socket_eyes", ec + Vector((0, -0.03, 0)))
    return F


PLANS = {"spark": plan_spark, "flame": plan_flame, "window": plan_window, "hollow": plan_hollow, "mast": plan_mast, "wax": plan_wax, "wheel": plan_wheel,
         "lash": plan_lash, "star": plan_star, "dart": plan_dart, "line": plan_line, "mouth": plan_mouth, "whirl": plan_whirl}


# --- what a flame burns on, in, and with -------------------------------------------------------

def bed_coals(B, F, size):
    coals(B, F.foot + Vector((0, 0, -0.03)), 0.105 * size)
    B.add(sk.disc(F.foot + Vector((0, 0, -0.075)), 0.19 * size, thick=0.02, n=10), "ash")


def bed_stones(B, F, size):
    """A ring of scorched stones travels with it."""
    c = F.foot + Vector((0, 0, -0.07))
    stones = None
    n = 7 if size < 1.2 else 9
    for i in range(n):
        a = 2 * math.pi * i / n
        stones = g.merge(stones, g.ico(c + Vector((0.22 * size * math.cos(a), 0.22 * size * math.sin(a), 0.0)), 0.062 * (1.0 + 0.2 * (i % 2)), sub=0, scale=(1.1, 1.0, 0.75), rot=(i * 0.7, i * 1.1, a)))
    B.add(stones, "stone_hide", False)
    B.add(sk.disc(c + Vector((0, 0, -0.04)), 0.27 * size, thick=0.02, n=10), "soot")
    coals(B, F.foot + Vector((0, 0, -0.03)), 0.09 * size, n=5)
    F.width = 0.28 * size


def bed_logs(B, F, size):
    c = F.foot + Vector((0, 0, -0.03))
    logs = None
    for i in range(3):
        a = i * math.pi / 3 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        logs = g.merge(logs, g.tube([c - d * 0.17 * size + Z * (0.0 + 0.02 * i), c + d * 0.17 * size + Z * (0.06 + 0.02 * i)], [0.032, 0.028], n=6))
    B.add(logs, "wood", False)


def bed_sticks(B, F, size):
    """It has no hearth: what it is burning lies where it fell."""
    c = F.foot + Vector((0, 0, -0.05))
    logs, ends = None, None
    for i, (a, x, y) in enumerate(((0.3, 0.06, 0.0), (1.9, -0.1, 0.08), (2.8, 0.14, 0.12), (4.4, -0.04, -0.12))):
        d = Vector((math.cos(a), math.sin(a), 0.12 * (i % 2)))
        p = c + Vector((x, y, 0))
        logs = g.merge(logs, g.tube([p - d * 0.11 * size, p + d * 0.11 * size], [0.024, 0.02], n=5))
        ends = g.merge(ends, g.ico(p + d * 0.115 * size, 0.018, sub=0))
    B.add(logs, "soot", False)
    B.add(ends, field("crack", 2.8))


def bed_rush(B, F, size):
    """A rush, in the iron nip that holds it."""
    c = F.foot
    B.add(g.tube([c + Vector((0, 0, -0.26 * size)), c], [0.008, 0.006], n=4), "grass_dry", False)
    B.add(g.box(c + Vector((0, 0.05, -0.34 * size)), (0.14, 0.14, 0.04)), "timber", False)
    B.add(g.tube([c + Vector((0, 0.05, -0.33 * size)), c + Vector((0, 0.05, -0.12 * size)), c + Vector((0, 0.01, -0.09 * size))], [0.009, 0.008, 0.007], n=4), "metal_iron", False)
    B.add(g.box(c + Vector((0, 0.0, -0.09 * size)), (0.03, 0.03, 0.02)), "metal_iron", False)
    F.width = 0.1


def bed_bowl(B, F, size):
    """A stone bowl: where the hand goes."""
    c = F.foot + Vector((0, 0, -0.17))
    B.add(g.lathe([(0.07, 0.0), (0.09, 0.02), (0.05, 0.05), (0.07, 0.1), (0.2 * size, 0.15), (0.21 * size, 0.18), (0.16 * size, 0.165), (0.0, 0.13)], n=10, centre=c), "stone_light", False)
    coals(B, F.foot + Vector((0, 0, -0.03)), 0.09)
    F.width = 0.22 * size


def bed_basket(B, F, size):
    """An iron basket on a pole: a beacon."""
    c = F.foot + Vector((0, 0, -0.06))
    bars = None
    for i in range(8):
        a = 2 * math.pi * i / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        bars = g.merge(bars, g.tube([c + d * 0.06, c + d * 0.14 * size + Z * 0.06, c + d * 0.16 * size + Z * 0.16], [0.008, 0.008, 0.008], n=3))
    B.add(bars, "metal_iron", False)
    for z, r in ((0.16, 0.16), (0.08, 0.145), (0.0, 0.065)):
        B.add(sk.hoop(c + Z * z, r * size, r * size, 0.009, n=10, sides=3), "metal_iron", False)
    coals(B, F.foot + Vector((0, 0, -0.02)), 0.085 * size, n=5)
    # the pole, its three feet, the pegs to climb it by
    foot = c + Z * -0.46
    B.add(g.tube([c, foot + Z * 0.1], [0.02, 0.024], n=6), "timber", False)
    legs, pegs = None, None
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        legs = g.merge(legs, g.tube([foot + Z * 0.2, foot + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.0))], [0.016, 0.016], n=4))
    for i in range(3):
        pegs = g.merge(pegs, g.tube([c + Vector((-0.05, 0, -0.1 - 0.09 * i)), c + Vector((0.05, 0, -0.1 - 0.09 * i))], [0.007, 0.007], n=3))
    B.add(legs, "timber", False)
    B.add(pegs, "metal_iron", False)
    F.width = 0.2 * size


def bed_pot(B, F, size):
    """It rides in a pierced iron pot on a chain."""
    c = F.foot + Vector((0, 0, 0.0))
    r = 0.17 * size
    B.add(g.ico(c, r, sub=1, scale=(1.0, 1.0, 0.92)), "metal_iron", False)
    B.add(g.lathe([(r * 0.5, r * 0.78), (r * 0.56, r * 0.86), (r * 0.5, r * 0.9)], n=8, centre=c, caps=False), "metal_brass", False)
    B.add(g.lathe([(r * 0.4, -r * 0.86), (r * 0.5, -r * 1.02), (0.0, -r * 1.02)], n=8, centre=c), "metal_iron", False)
    # where it is pierced, the fire shows
    holes = None
    for i in range(12):
        a, b = i * 2.399, math.asin(-0.6 + 1.3 * (i + 0.5) / 12)
        d = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b) * 0.92))
        holes = g.merge(holes, g.ico(c + d * r * 0.97, r * 0.13, sub=0, scale=(1, 1, 1)))
    B.add(holes, field("holes", 3.6))
    # and two of the piercings are its eyes
    B.add(sk.eye_pair(c + Vector((0, -r * 0.93, r * 0.2)), r * 0.36, r * 0.2, scale=(1.3, 0.5, 0.6), slant=0.3), field("eyes", 4.6))
    top = c + Z * (r * 3.3)
    ch = None
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        ch = g.merge(ch, sk.chain([c + Vector((r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), r * 0.82)), top], link=0.016, n=9))
    B.add(ch, "metal_iron_light", False)
    B.add(sk.hoop(top + Z * 0.03, 0.035, 0.035, 0.008, n=8, u=X, v=Z, sides=3), "metal_brass", False)
    F.pot_top = c + Z * r * 0.85
    F.width = r


def bed_book(B, F, size):
    """It burns over a page and has never singed one."""
    c = F.foot + Vector((0, -0.02, -0.075))
    for s in (1, -1):
        B.add(g.box(c + Vector((s * 0.105 * size, 0, 0.012)), (0.2 * size, 0.27 * size, 0.022), rot=(0.0, s * 0.16, 0)), "paper", False)
        B.add(g.box(c + Vector((s * 0.105 * size, 0, -0.008)), (0.22 * size, 0.29 * size, 0.016), rot=(0.0, s * 0.16, 0)), "leather_dark", False)
    ink, old = None, None
    for s in (1, -1):
        for i in range(4):
            ln = g.box(c + Vector((s * 0.105 * size, 0.08 * size - 0.05 * size * i, 0.027 + 0.004)), (0.14 * size, 0.008, 0.004), rot=(0.0, s * 0.16, 0))
            if (i + (s > 0)) % 3 == 0:
                old = g.merge(old, ln)
            else:
                ink = g.merge(ink, ln)
    B.add(ink, "soot", False)
    B.add(old, field("ink", 2.6))
    F.width = 0.22 * size


def bed_lamp(B, F, size):
    """A signalling lamp: it speaks in flashes."""
    c = F.foot + Vector((0, 0, 0.06))
    w = 0.13 * size
    frame = None
    for sx in (1, -1):
        for sy in (1, -1):
            frame = g.merge(frame, g.box(c + Vector((sx * w, sy * w, 0.02)), (0.022, 0.022, 0.34 * size)))
    frame = g.merge(frame, g.box(c + Vector((0, 0, -0.15 * size)), (2 * w + 0.05, 2 * w + 0.05, 0.03)), g.box(c + Vector((0, 0, 0.19 * size)), (2 * w + 0.05, 2 * w + 0.05, 0.03)))
    B.add(frame, "metal_iron", False)
    B.add(g.lathe([(w * 1.2, 0.0), (w * 0.5, 0.06), (0.03, 0.08), (0.03, 0.11)], n=4, centre=c + Z * 0.2 * size, phase=math.pi / 4), "metal_iron", False)
    B.add(sk.hoop(c + Z * (0.2 * size + 0.14), 0.04, 0.04, 0.008, n=8, u=X, v=Z, sides=3), "metal_brass", False)
    B.add(g.box(c + Vector((0, w, 0.02)), (2 * w, 0.012, 0.3 * size)), "metal_dark", False)
    slats = None
    for i in range(4):
        slats = g.merge(slats, g.box(c + Vector((0, -w - 0.01, -0.1 * size + 0.075 * size * i)), (2 * w, 0.06, 0.008), rot=(0.7, 0, 0)))
    B.add(slats, "metal_brass", False)
    F.width = w + 0.03
    F.top = max(F.top, c.z + 0.2 * size + 0.17)


def bed_frost(B, F, size):
    frost = None
    for i in range(10):
        a = 2 * math.pi * i / 10
        frost = g.merge(frost, g.blade(F.foot + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), -0.03)), F.foot + Vector((0.2 * size * math.cos(a + 0.12), 0.2 * size * math.sin(a + 0.12), -0.05 + 0.012 * (i % 3))), 0.07, normal=(0, 0, 1), belly=0.55))
    B.add(frost, "ice_pale", False)


def shell_scale(B, F, size):
    """A dark skin like fire-scale has formed over it, and the flame shows at the cracks."""
    c = F.foot
    for tier, (n, r0, z0, L) in enumerate(((7, 0.13, 0.0, 0.2), (6, 0.115, 0.1, 0.2), (5, 0.09, 0.2, 0.17))):
        geo = None
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * tier) / n
            d = Vector((math.cos(a), math.sin(a), 0))
            b0 = c + d * r0 * size + Z * z0 * size
            geo = g.merge(geo, g.blade(b0, b0 + (d * -0.03 + Z * L) * size, 0.095 * size, thick=0.02, normal=d, belly=0.35))
        B.add(geo, "clinker" if tier % 2 == 0 else "clinker_light", False)
    f = F.heart + Vector((0, -F.r * 1.25 * size, 0.01))
    B.add(sk.eye_pair(f, 0.032, 0.016, scale=(1.3, 0.5, 0.5), slant=0.3), field("eyes", 4.6))
    F.width = 0.15 * size


def shell_petals(B, F, size):
    """What it came back out of lies open round its foot."""
    c = F.foot
    geo = None
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.2
        d = Vector((math.cos(a), math.sin(a), 0))
        b0 = c + d * 0.08 * size + Z * -0.02
        geo = g.merge(geo, g.blade(b0, b0 + (d * 0.17 + Z * (0.05 + 0.03 * (i % 2))) * size, 0.1 * size, thick=0.02, normal=Z, belly=0.4))
    B.add(geo, "clinker", False)
    F.width = 0.26 * size


def shell_clinker(B, F, size):
    """A coal banked behind plates of its own clinker."""
    c = F.foot + Vector((0, 0, 0.02))
    B.add(g.ico(c, 0.19 * size, sub=1, scale=(1.2, 1.0, 0.82)), B.main, False)
    plates = None
    for i in range(12):
        a, b = i * 2.399, 0.15 + 1.2 * (i / 12.0)
        d = Vector((math.cos(a) * math.cos(b) * 1.2, math.sin(a) * math.cos(b), math.sin(b) * 0.82))
        plates = g.merge(plates, g.ico(c + d * 0.19 * size, 0.085 * size, sub=0, scale=(1.0, 1.0, 0.3), rot=(math.sin(a) * (1.2 - b) * 0.8, -math.cos(a) * (1.2 - b) * 0.8, a)))
    B.add(plates, "clinker_light", False)
    B.add(_cracks(c, 0.2 * size, 7, 0.4, (1.2, 1.0, 0.82)), field("crack", 3.0))
    f = c + Vector((0, -0.185 * size, 0.02))
    B.add(g.box(f + Vector((0, 0.01, 0)), (0.17 * size, 0.02, 0.04)), "void", False)
    B.add(sk.eye_pair(f, 0.045 * size, 0.02, scale=(1.3, 0.5, 0.6), slant=0.2), field("eyes", 4.6))
    # it burns where the plates do not meet
    for i, (x, y, hh) in enumerate(((0.07, 0.02, 0.13), (-0.09, 0.05, 0.1), (0.0, -0.06, 0.08))):
        B.add(sk.flame(c + Vector((x * size, y * size, 0.14 * size)), 0.03, hh, n=3, turn=i), field("flame", 2.8))
    F.heart = c
    F.top = c.z + 0.2 * size
    F.width = 0.24 * size


def shell_cage(B, F, size):
    """It lives in a small cage of turning wheels it built for itself, and breathes through the gaps."""
    c = F.heart + Vector((0, 0, 0.02))
    r = 0.2 * size
    B.add(sk.hoop(c, r, r, 0.012, n=14, u=X, v=Z, sides=4), "metal_brass", False)
    B.add(sk.hoop(c, r, r, 0.012, n=14, u=Y, v=Z, sides=4), "metal_iron", False)
    B.add(sk.hoop(c, r, r, 0.012, n=14, u=X, v=Y, sides=4), "metal_iron", False)
    B.add(sk.gear(c + Vector((r + 0.01, 0, 0)), 0.085 * size, teeth=9, thick=0.028, axis=X), "metal_brass", False)
    B.add(sk.gear(c + Vector((-0.11, -0.13, 0.12)) * size, 0.065 * size, teeth=8, thick=0.024, axis=Vector((-0.5, -0.6, 0.6))), "metal_iron_light", False)
    B.add(sk.gear(c + Vector((0, r * 0.2, r + 0.01)), 0.075 * size, teeth=8, thick=0.026, axis=Z), "metal_brass", False)
    B.add(g.lathe([(0.03, 0.0), (0.03, 0.09), (0.045, 0.1), (0.045, 0.12)], n=6, centre=c + Vector((0.0, r * 0.2, r + 0.03))), "metal_iron", False)
    jets = None
    for a, up in ((0.9, 0.3), (2.4, -0.1), (4.2, 0.5)):
        d = Vector((math.cos(a), math.sin(a) * 0.5 - 0.5, up)).normalized()
        jets = g.merge(jets, g.tongue([c + d * r * 0.7, c + d * (r + 0.07), c + d * (r + 0.2)], [0.05, 0.07, 0.004], thick=0.45))
    B.add(jets, field("flame", 2.8))
    F.width = r + 0.1 * size
    F.top = max(F.top, c.z + r + 0.15)


def crown_twelve(B, F, size):
    """Twelve small tongues of flame stand in a crown, each a slightly different colour."""
    c = F.foot + Vector((0, 0, 0.02))
    kinds = (field("flame", 2.6), mat("ash_pale"), field("wisp", 1.6), mat("wax_red"), field("flame", 3.2), mat("mist_pale"))
    for k, m in enumerate(kinds):
        geo = None
        for i in range(12):
            if i % 6 != k:
                continue
            a = 2 * math.pi * i / 12
            d = Vector((math.cos(a), math.sin(a), 0))
            b0 = c + d * 0.2 * size
            geo = g.merge(geo, g.tongue([b0, b0 + d * 0.03 + Z * 0.08 * size, b0 + d * 0.01 + Z * (0.17 + 0.02 * (i % 3)) * size], [0.05, 0.06, 0.004], thick=0.5, normal=d))
        B.add(geo, m)


def wings_thin(B, F, size):
    """Two thin wings of flame stand up at its back."""
    c = F.heart
    for s in (1, -1):
        lit = None
        for i in range(3):
            b0 = c + Vector((s * 0.03, 0.05, 0.02 * i))
            tip = b0 + Vector((s * (0.2 + 0.07 * i), 0.1, 0.5 - 0.1 * i)) * size
            lit = g.merge(lit, g.tongue([b0, (b0 + tip) / 2 + Vector((s * 0.05, 0.02, -0.02)), tip], [0.05, 0.065, 0.004], thick=0.25, normal=(0, -1, 0.2)))
        B.add(lit, field("wings", 2.6))
    B.add(g.ico(c, F.r * 0.56, sub=1, scale=(1, 1, 1.4)), "bone")
    F.top = max(F.top, c.z + 0.52 * size)


def ring_ground(B, F, size):
    """The light it throws ends in a clean edge, like a line drawn on the ground."""
    c = Vector((0, 0, F.foot.z - 0.09))
    B.add(sk.hoop(c, 0.36 * size, 0.36 * size, 0.008, n=22, sides=3), field("edge", 3.0))
    st = None
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        st = g.merge(st, g.ico(c + Vector((0.3 * size * math.cos(a), 0.3 * size * math.sin(a), 0.0)), 0.03, sub=0, scale=(1, 1, 0.8), rot=(i, i * 2, 0)))
    B.add(st, "stone_hide", False)
    F.width = max(F.width, 0.38 * size)


def ring_dial(B, F, size):
    """A ring of faint figures turns round it like a dial, in a hand nobody now uses."""
    c = F.heart + Vector((0, 0, -0.02))
    R = 0.3 * size
    ring = sk.hoop(c, R, R, 0.009, n=22, sides=3)
    marks = None
    for i in range(12):
        a = 2 * math.pi * i / 12
        p = c + Vector((R * math.cos(a), R * math.sin(a), 0.0))
        t = Vector((-math.sin(a), math.cos(a), 0))
        k = 0.03
        for (x0, y0), (x1, y1) in ((((0, -1), (0, 1)), ((0, 1), (0.8, 0.3))) if i % 3 == 0 else ((((-0.6, -1), (0, 1)), ((0, 1), (0.6, -1))) if i % 3 == 1 else (((-0.5, 0.8), (0.5, 0.8)), ((0, 0.8), (0, -1))))):
            marks = g.merge(marks, g.tube([p + t * x0 * k + Z * (y0 * k + 0.045), p + t * x1 * k + Z * (y1 * k + 0.045)], [0.005, 0.005], n=3))
    B.add(sk.tilted(ring, rx=0.3, ry=0.12, about=c), "metal_brass", False)
    B.add(sk.tilted(marks, rx=0.3, ry=0.12, about=c), field("figures", 2.6))
    B.add(sk.tilted(sk.hoop(c, R * 0.8, R * 0.8, 0.005, n=18, sides=3), rx=0.3, ry=0.12, about=c), "ash", False)
    F.width = max(F.width, R + 0.04)


def ring_impact(B, F, size):
    """A ring of light spreads wherever it stops."""
    nose = getattr(F, "nose", F.foot)
    c = Vector((nose.x, nose.y - 0.02, 0.03))
    B.add(sk.hoop(c, 0.3 * size, 0.3 * size, 0.012, n=20, sides=3), field("edge", 3.2))
    B.add(sk.hoop(c, 0.18 * size, 0.18 * size, 0.008, n=14, sides=3), field("edge", 2.2))
    deb = None
    for i in range(6):
        a = i * 1.1 + 0.3
        deb = g.merge(deb, g.ico(c + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.03 + 0.03 * (i % 3))), 0.02 + 0.008 * (i % 2), sub=0, rot=(i, i * 2, 0)))
    B.add(deb, "soot", False)
    B.add(sk.disc(c + Z * -0.02, 0.2 * size, thick=0.012, n=10), "soot")


def has_andirons(B, F, size):
    """Firedogs, either side."""
    for s in (1, -1):
        c = F.foot + Vector((s * 0.2 * size, -0.02, -0.08))
        B.add(g.tube([c + Vector((0, 0.16, 0.0)), c + Vector((0, 0.16, 0.04)), c + Vector((0, -0.08, 0.04)), c + Vector((0, -0.1, 0.19 * size))], [0.014, 0.014, 0.014, 0.012], n=4), "metal_iron", False)
        B.add(g.ico(c + Vector((0, -0.1, 0.21 * size)), 0.03, sub=1), "metal_brass", False)
        B.add(g.tube([c + Vector((0, -0.08, 0.04)), c + Vector((0, -0.08, 0.0))], [0.014, 0.014], n=4), "metal_iron", False)
    F.width = max(F.width, 0.24 * size)


def has_fireback(B, F, size):
    """An old iron plate stands behind it, with an arch to its top."""
    c = F.foot + Vector((0, 0.17, -0.08))
    w, h = 0.24 * size, 0.2 * size
    B.add(g.box(c + Z * (h / 2), (2 * w, 0.03, h)), "metal_iron", False)
    half = sk.disc((0, 0, 0), w, thick=0.03, n=14)
    half = ([Vector((p.x, c.y - 0.015 + p.z, c.z + h + max(0.0, p.y))) for p in half[0]], half[1])
    B.add(half, "metal_iron", False)
    B.add(sk.arc(c + Vector((0, -0.02, h)), w * 0.7, w * 0.7, 0.2, math.pi - 0.2, 0.01, n=8, u=X, v=Z, sides=3), "rust", False)
    F.width = max(F.width, w)
    F.top = max(F.top, c.z + h + w)


def has_gimbal(B, F, size):
    """It leans, always the same way: the rings it hangs in let it."""
    c = F.heart + Vector((0, 0, -0.02))
    B.add(sk.tilted(sk.hoop(c, 0.21 * size, 0.21 * size, 0.01, n=16, u=X, v=Z, sides=4), rz=0.3, about=c), "metal_brass", False)
    B.add(sk.tilted(sk.hoop(c, 0.18 * size, 0.18 * size, 0.008, n=14, u=X, v=Y, sides=4), rx=0.25, about=c), "metal_iron_light", False)
    top = c + Z * 0.21 * size
    B.add(g.tube([top, top + Z * 0.07], [0.01, 0.01], n=4), "metal_brass", False)
    B.add(sk.hoop(top + Z * 0.1, 0.03, 0.03, 0.008, n=8, u=X, v=Z, sides=3), "metal_brass", False)
    # the pointer: the way out
    d = Vector((F.lean[0], F.lean[1], 0))
    d = d.normalized() if d.length > 1e-4 else Vector((0, -1, 0))
    p0 = c + d * 0.22 * size
    B.add(g.cone(p0, p0 + d * 0.13, 0.03, n=4), "metal_brass", False)
    F.width = max(F.width, 0.34 * size)
    F.top = max(F.top, top.z + 0.13)


def has_pages(B, F, size):
    """What was written under what was written."""
    c = F.foot + Vector((0, -0.02, -0.2))
    for i in range(3):
        B.add(g.box(c + Vector((0.03 * i - 0.03, 0.02 * i, -0.012 * i)), (0.42 * size, 0.3 * size, 0.008), rot=(0, 0, 0.25 * i - 0.3)), "paper" if i != 1 else "ash_pale", False)


def has_flashes(B, F, size):
    """Long and short, with pauses left for a reply."""
    c = F.foot + Vector((0, -0.2, 0.08))
    geo = None
    for i, L in enumerate((0.11, 0.04, 0.11, 0.04, 0.04)):
        p = c + Vector((-0.02 * i, -0.09 - 0.1 * i, 0.03 * i))
        geo = g.merge(geo, g.box(p, (L * size, 0.02, 0.03)))
    B.add(geo, field("signal", 3.2))


def has_chain(B, F, size):
    """A chain of darker fire coiled in it."""
    pts = []
    for i in range(14):
        t = i / 13
        a = t * 2 * math.pi * 1.6
        pts.append(F.foot + Vector((F.r * 1.5 * (1 - 0.45 * t) * math.cos(a), F.r * 1.5 * (1 - 0.45 * t) * math.sin(a), F.h * 0.8 * t)))
    B.add(sk.chain(pts, link=0.024, n=17), "metal_dark", False)


def has_hand(B, F, size):
    """Where you put your hand in it, the shape of the hand stays."""
    c = F.heart + Vector((0, -F.r * 0.9, 0.06))
    B.add(g.ico(c, 0.034 * size, sub=1, scale=(1.0, 0.3, 1.1)), "mask_pale")
    fing = None
    for i, a in enumerate((-0.6, -0.25, 0.05, 0.35, 0.95)):
        d = Vector((math.sin(a), 0, math.cos(a)))
        L = (0.065 if i != 4 else 0.045) * size
        fing = g.merge(fing, g.tongue([c + d * 0.025 * size, c + d * (0.025 * size + L)], [0.016 * size, 0.011 * size], thick=0.4, normal=-Y))
    B.add(fing, "mask_pale")


def has_shimmer(B, F, size):
    """Heat comes off it in a slow shimmer."""
    geo = None
    for i, (x, y) in enumerate(((0.12, 0.05), (-0.14, 0.0), (0.02, 0.14), (-0.04, -0.1))):
        geo = g.merge(geo, sk.smoke_thread(F.foot + Vector((x, y, 0.16)), 0.36 * size, sway=0.03, w=0.022, n=6))
    B.add(geo, "veil")
    F.top = max(F.top, F.foot.z + 0.5 * size)


def has_cinders(B, F, size):
    cinders(B, F.foot + Vector((0, 0, 0.1)), 0.2 * size, n=5, seed=0.5)


def smoke_thread_(B, F, size):
    B.add(sk.smoke_thread(F.tip(1.15), 0.3 * size, sway=0.02, w=0.03, n=5), B.under)


def smoke_stream(B, F, size):
    """Streaming smoke: it is already leaning toward the next thing."""
    geo = None
    for i, (dz, L) in enumerate(((0.0, 0.5), (0.12, 0.62), (-0.1, 0.4))):
        b0 = F.tip(0.7) + Vector((0, 0.04, dz))
        d = Vector((-F.lean[0], -F.lean[1] + 0.2, 0.25)).normalized()
        geo = g.merge(geo, g.tongue([b0, b0 + d * L * 0.4 * size + Z * 0.05, b0 + d * L * 0.75 * size + Z * 0.02, b0 + d * L * size + Z * 0.1], [0.07, 0.1, 0.09, 0.02], thick=0.4, normal=Z))
    B.add(geo, "smoke")


STYLES = {
    ("bed", "coals"): bed_coals, ("bed", "stones"): bed_stones, ("bed", "logs"): bed_logs, ("bed", "sticks"): bed_sticks, ("bed", "rush"): bed_rush,
    ("bed", "bowl"): bed_bowl, ("bed", "basket"): bed_basket, ("bed", "pot"): bed_pot, ("bed", "book"): bed_book, ("bed", "lamp"): bed_lamp, ("bed", "frost"): bed_frost,
    ("shell", "scale"): shell_scale, ("shell", "petals"): shell_petals, ("shell", "clinker"): shell_clinker, ("shell", "cage"): shell_cage,
    ("crown", "twelve"): crown_twelve, ("wings", "thin"): wings_thin,
    ("ring", "ground"): ring_ground, ("ring", "dial"): ring_dial, ("ring", "impact"): ring_impact,
    ("has", "andirons"): has_andirons, ("has", "fireback"): has_fireback, ("has", "gimbal"): has_gimbal, ("has", "pages"): has_pages, ("has", "flashes"): has_flashes,
    ("has", "chain"): has_chain, ("has", "hand"): has_hand, ("has", "shimmer"): has_shimmer, ("has", "cinders"): has_cinders,
    ("smoke", "thread"): smoke_thread_, ("smoke", "stream"): smoke_stream,
}
SLOTS = ("bed", "shell", "crown", "wings", "ring", "has", "smoke")
CAN = {"flame": set(SLOTS), "dart": {"ring"}, "spark": set()}


def build(form_id, level, spec, base):
    B = sk.Body(form_id, level, spec, base)
    plan = spec.get("plan", "spark" if level <= 1 else "flame")
    F = PLANS[plan](B, spec)
    if plan == "flame":
        shells = [st for st, _ in each(spec.get("shell"))]
        if "clinker" not in shells:
            _draw_flame(B, F, spec)
    for slot in SLOTS:
        for style, size in each(spec.get(slot)):
            if slot not in CAN.get(plan, set()):
                continue
            fn = STYLES.get((slot, style))
            if fn is None:
                sk.log("no such style", slot, style, "on", form_id)
                continue
            fn(B, F, size)
    if plan == "flame":
        B.frame(F.top, front=-max(0.1, F.r * 1.3), mid=F.heart.z, half=max(0.12, F.width))
        B.socket("socket_eyes", getattr(F, "eye_at", F.heart + Vector((0, -F.r * 0.55, 0.01))))
        B.socket("socket_light", F.heart)
    B.export()
