"""WILDLINE genius lines: the Fiend (docs/genius-evolutions.md, "The spirits").

A wick with a temper. The Starter is a candle flame with two horns and a scowl; from there it
is a soot-black imp with a candle melted to its skull, and each path does a different thing
with the fire: lets it out (Flare-up's line: a maw, a mane of flame, things thrown and
ridden), keeps it banked (Banked Coal's: ash-grey, hunched, with letters, bottles and smoke
to read), or makes it a hearth (the Grate-fiend's: iron, a grate in its belly, stoves and
candles that are for someone else).

A Fiend's `body` (data/genius-bases/fiend.json):
    plan     wick (the Starter), imp (the default), ball, bottle, stove, candle
    build    belly, tall, head, legs (their length), lean (it leans forward), dive (it is
             tipped head-down), horn (their size), ear
    eyes     scowl, wide, old, sleepy, shut, white
    mouth    grin, maw, scowl, lamp, none
    horns    curved, stub, long, swept, ram
    crown    what is on its head: candle, flare, fuse, letters, thread, bare, none
    arms     hang, hips, crossed, out, low, up, raise, forward, down, wrap, knees, cup, grip, ride;
             "raise/hips" gives the left and the right their own
    hands    claws, small, plated, ash, fists
    legs     bowed, long, tiptoe, sit, crouch, kneel, ride
    skin     ash, iron, soot, still
    chest    grate, core, cracks
    wears    apron, necklace, bracelet, bottle
    holds    flame, hammer, writ, snuffers, coal, list
    rides    blade
    ground   hill, fires, ring, ward, puddle, heap, sift, stick, quiet, anvil
    aura     mane, smokes, steam, wings
    bottle   bound (a bottle's own: brass bands and a seal)
    stove    walker, pot, watchfire (a stove's own)
"""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import mat, field
import spirits_kit as sk
from spirits_kit import each, opt

# where the elbow and the wrist are from the shoulder, for the left arm (x outward)
POSES = {
    "hang": ((0.074, -0.02, -0.09), (0.06, -0.085, -0.158)),
    "hips": ((0.11, 0.02, -0.07), (0.035, -0.03, -0.15)),
    "crossed": ((0.075, -0.1, -0.1), (-0.07, -0.14, -0.07)),
    "out": ((0.11, -0.01, -0.02), (0.21, -0.03, 0.03)),
    "low": ((0.1, -0.01, -0.07), (0.2, -0.04, -0.12)),
    "up": ((0.09, -0.05, -0.06), (0.105, -0.11, 0.075)),
    "raise": ((0.07, -0.01, 0.1), (0.06, -0.03, 0.27)),
    "forward": ((0.05, -0.1, -0.03), (0.04, -0.22, -0.02)),
    "down": ((0.06, -0.1, -0.09), (0.045, -0.2, -0.2)),
    "wrap": ((0.09, -0.08, -0.12), (-0.03, -0.155, -0.13)),
    "knees": ((0.1, -0.05, -0.1), (0.115, -0.14, -0.17)),
    "cup": ((0.08, -0.1, -0.02), (-0.065, -0.17, 0.075)),
    "grip": ((0.09, -0.06, -0.12), (0.1, -0.13, -0.24)),
    "ride": ((0.09, 0.03, -0.07), (0.085, 0.095, -0.17)),
}


def _stage(level):
    return {2: {"head": 1.14, "tall": 0.9, "belly": 0.92, "horn": 0.8}, 3: {}}.get(level, {"tall": 1.08, "horn": 1.25, "belly": 1.05}) if level != 1 else {}


class Imp:
    """A soot-black imp: where its parts are, and how it is tipped."""

    def __init__(self, B, bd, legs="bowed"):
        self.B = B
        self.items = []
        self.belly, self.tall, self.head = bd.get("belly", 1.0), bd.get("tall", 1.0), bd.get("head", 1.0)
        self.leg, self.horn, self.ear = bd.get("legs", 1.0), bd.get("horn", 1.0), bd.get("ear", 1.0)
        self.lean, self.dive = bd.get("lean", 0.0), bd.get("dive", 0.0)
        self.legs = legs
        self.hip = {"sit": 0.085, "kneel": 0.15, "crouch": 0.2}.get(legs, 0.22 * self.leg) + bd.get("lift", 0.0)
        self.zt = self.hip - 0.02 + 0.25 * self.tall          # the top of its trunk
        self.zs = self.zt - 0.03                               # its shoulders
        self.zh = self.zt + 0.095 * self.head                  # the middle of its head
        self.crown = self.zh + 0.068 * self.head               # where the candle sits
        self.top = self.zh + 0.092 * self.head
        self.hands, self.feet = {}, {}

    def add(self, geo, material, smooth=None):
        if geo and geo[0]:
            self.items.append((geo, material, smooth))

    def extend(self, items):
        for it in items:
            self.add(*it)

    def H(self, x, y, z):
        """A point given on the plain head (its middle at z 0.545), on this one."""
        return Vector((x * self.head, -0.02 + (y + 0.02) * self.head, self.zh + (z - 0.545) * self.head))

    def sh(self, s):
        return Vector((s * 0.098 * self.belly, -0.01, self.zs))

    def P(self, p):
        """Where a point of the upright imp ends, once it is leaned and tipped."""
        p = V(p)
        q = Vector((p.x, p.y - self.lean * (p.z - self.hip), p.z))
        if self.dive:
            c = Vector((0, 0, self.zt - 0.1))
            q = c + Matrix.Rotation(self.dive, 3, "X") @ (q - c)
        return q

    def emit(self):
        for geo, material, smooth in self.items:
            geo = sk.sheared(geo, self.lean, self.hip) if self.lean else geo
            if self.dive:
                geo = sk.tilted(geo, rx=self.dive, about=(0, 0, self.zt - 0.1))
            self.B.add(geo, material, smooth)
        self.items = []

    # --- the parts of it -----------------------------------------------------------------

    def trunk(self):
        B, b = self.B, self.belly
        h0, k = self.hip - 0.02, self.tall
        self.add(g.lathe([(0.045 * b, h0), (0.1 * b, h0 + 0.035 * k), (0.118 * b, h0 + 0.12 * k), (0.098 * b, h0 + 0.2 * k), (0.062, h0 + 0.25 * k)], n=8), B.main)
        self.add(g.ico((0, -0.072 * b, h0 + 0.11 * k), 0.078 * b, sub=1, scale=(1.0, 0.5, 1.12 * k)), B.under)

    def skull(self):
        B = self.B
        self.add(g.ico(self.H(0, -0.02, 0.545), 0.102 * self.head, sub=1, scale=(1.06, 0.95, 0.9)), B.main)
        e = self.ear
        if e > 0:
            for s in (1, -1):
                self.add(g.blade(self.H(s * 0.085, -0.01, 0.55), self.H(s * (0.085 + 0.14 * e), 0.04, 0.55 + 0.05 * e), 0.07 * self.head, normal=(0, -1, 0.3), belly=0.35), B.main)

    def horns(self, style="curved", size=1.0):
        k = size * self.horn
        for s in (1, -1):
            if style == "stub":
                pts, rad = [self.H(s * 0.052, -0.03, 0.618), self.H(s * 0.08, -0.025, 0.618 + 0.05 * k)], [0.026, 0.008]
            elif style == "long":
                pts, rad = [self.H(s * 0.052, -0.03, 0.618), self.H(s * 0.1, -0.02, 0.618 + 0.09 * k), self.H(s * 0.085, 0.02, 0.618 + 0.2 * k), self.H(s * 0.05, 0.04, 0.618 + 0.3 * k)], [0.022, 0.017, 0.01, 0.002]
            elif style == "swept":
                pts, rad = [self.H(s * 0.052, -0.03, 0.618), self.H(s * 0.1, 0.0, 0.618 + 0.05 * k), self.H(s * 0.13, 0.09, 0.618 + 0.07 * k), self.H(s * 0.12, 0.2 * k, 0.618 + 0.03 * k)], [0.023, 0.018, 0.011, 0.002]
            elif style == "ram":
                c = self.H(s * 0.075, 0.0, 0.6)
                pts = [c + Vector((s * 0.02 * k * (1 + i * 0.25) * math.cos(a), 0.06 * k * math.cos(a) * (1 + i * 0.1) - 0.02, 0.06 * k * math.sin(a))) + Vector((s * 0.012 * i, 0, 0)) for i, a in enumerate((2.0, 1.2, 0.4, -0.5, -1.4, -2.2))]
                rad = [0.024, 0.022, 0.019, 0.015, 0.01, 0.003]
            else:
                pts, rad = [self.H(s * 0.052, -0.03, 0.618), self.H(s * 0.092, -0.02, 0.618 + 0.057 * k), self.H(s * 0.08, 0.015, 0.618 + 0.112 * k)], [0.021, 0.015, 0.003]
            self.add(g.tube(pts, [r * self.head for r in rad], n=5), "horn", False)

    def candle(self, size=1.0, lit=1.0, drips=True):
        """The candle stub melted to its skull, its wick, its flame."""
        B, k = self.B, self.head
        c = Vector((0, -0.02, 0))
        z0 = self.crown - 0.01
        self.add(g.lathe([(0.044 * k, z0), (0.046 * k, z0 + 0.045 * k), (0.03 * k, z0 + 0.054 * k)], n=7, centre=c), "wax")
        self.add(g.tube([(0, -0.02, z0 + 0.05 * k), (0.004, -0.022, z0 + 0.08 * k)], [0.004, 0.003], n=3), "metal_dark", False)
        if lit > 0:
            f0 = Vector((0, -0.02, z0 + 0.07 * k))
            self.add(sk.flame(f0, 0.036 * k * (0.8 + 0.2 * size), 0.12 * size * lit * k, n=3, turn=0.4), field("flame", 3.0))
            self.add(g.ico(f0 + Z * 0.025 * k, 0.017 * k, sub=0, scale=(1, 1, 1.4)), field("core", 5.0))
        if drips:
            for s, a0 in ((1, 0.3), (-1, -0.2)):
                self.add(g.tongue([self.H(s * 0.04, -0.05 + a0 * 0.05, 0.63), self.H(s * 0.075, -0.07, 0.585), self.H(s * 0.082, -0.075, 0.545)], [0.03 * k, 0.026 * k, 0.004], thick=0.4, normal=(s, -0.6, 0.3)), "wax")
            dr = None
            for s in (1, -1):
                p = self.sh(s) + Vector((-s * 0.028, -0.02, 0.035))
                dr = g.merge(dr, g.tongue([p, p + Vector((s * 0.048, 0, -0.025)), p + Vector((s * 0.065, -0.01, -0.085))], [0.05, 0.06, 0.005], thick=0.35, normal=(s, 0, 0.8)))
            self.add(dr, B.mark("drips", B.main))

    def face(self, eyes="scowl", mouth="grin"):
        B, k = self.B, self.head
        if eyes == "wide":
            self.add(sk.eye_pair(self.H(0, -0.108, 0.566), 0.044 * k, 0.027 * k, scale=(1.0, 0.45, 1.0), slant=0.0), field("eyes", 4.0))
        elif eyes == "old":        # old red eyes under heavy brows
            self.add(sk.eye_pair(self.H(0, -0.108, 0.558), 0.044 * k, 0.024 * k, scale=(1.1, 0.45, 0.8), slant=0.1), field("eyes", 3.2))
            br = None
            for s in (1, -1):
                br = g.merge(br, g.tongue([self.H(s * 0.012, -0.112, 0.582), self.H(s * 0.05, -0.118, 0.592), self.H(s * 0.09, -0.1, 0.572)], [0.012, 0.024 * k, 0.01], thick=0.6, normal=(0, -1, 0.5)))
            self.add(br, "ash")
        elif eyes == "sleepy":
            self.add(sk.eye_pair(self.H(0, -0.108, 0.556), 0.043 * k, 0.022 * k, scale=(1.2, 0.45, 0.45), slant=-0.1), field("eyes", 2.4))
            lid = None
            for s in (1, -1):
                lid = g.merge(lid, g.ico(self.H(s * 0.043, -0.106, 0.572), 0.025 * k, sub=1, scale=(1.25, 0.5, 0.6)))
            self.add(lid, B.main)
        elif eyes == "shut":
            sh = None
            for s in (1, -1):
                sh = g.merge(sh, g.box(self.H(s * 0.042, -0.112, 0.56), (0.04 * k, 0.008, 0.006)))
            self.add(sh, field("eyes", 1.6))
        elif eyes == "white":      # white-hot
            self.add(sk.eye_pair(self.H(0, -0.108, 0.562), 0.042 * k, 0.025 * k, scale=(1.25, 0.45, 0.7), slant=0.35), field("eyes", 5.5))
        else:
            self.add(sk.eye_pair(self.H(0, -0.108, 0.562), 0.042 * k, 0.021 * k, scale=(1.25, 0.45, 0.62), slant=0.35), field("eyes", 4.0))
            br = None
            for s in (1, -1):
                br = g.merge(br, g.tongue([self.H(s * 0.012, -0.112, 0.572), self.H(s * 0.075, -0.108, 0.6)], [0.014, 0.008], thick=0.6, normal=(0, -1, 0.5)))
            self.add(br, B.main)
        m = self.H(0, -0.113, 0.492)
        if mouth == "maw":         # its mouth open, looking for who did it
            self.add(g.ico(self.H(0, -0.09, 0.49), 0.056 * k, sub=1, scale=(1.25, 0.6, 1.05)), "maw")
            self.add(g.ico(self.H(0, -0.075, 0.485), 0.036 * k, sub=1, scale=(1.2, 0.5, 0.9)), field("mouth", 3.6))
            teeth = None
            for i in range(4):
                x = (-0.045 + 0.03 * i) * k
                teeth = g.merge(teeth, g.cone(self.H(x / k, -0.118, 0.532), self.H(x / k, -0.122, 0.505), 0.011 * k, n=4), g.cone(self.H(x / k * 0.9, -0.116, 0.448), self.H(x / k * 0.9, -0.12, 0.472), 0.01 * k, n=4))
            self.add(teeth, "bone", False)
        elif mouth == "scowl":
            self.add(g.tongue([self.H(-0.05, -0.1, 0.487), self.H(-0.02, -0.114, 0.5), self.H(0.02, -0.114, 0.5), self.H(0.05, -0.1, 0.487)], [0.004, 0.014 * k, 0.014 * k, 0.004], thick=0.3, normal=(0, -1, 0)), field("mouth", 2.6))
        elif mouth == "lamp":      # its lower jaw is a small lamp
            self.add(g.box(self.H(0, -0.1, 0.5), (0.1 * k, 0.03, 0.012)), "metal_iron", False)
            self.extend(sk.lantern(self.H(0, -0.105, 0.5), 0.052 * k, glow="lamp", strength=3.4))
        elif mouth == "grin":
            self.add(g.tongue([self.H(-0.055, -0.097, 0.507), self.H(-0.025, -0.113, 0.492), self.H(0.025, -0.113, 0.492), self.H(0.055, -0.097, 0.507)], [0.004, 0.022 * k, 0.022 * k, 0.004], thick=0.3, normal=(0, -1, 0)), field("mouth", 3.0))
        self.mouth = m

    def arm(self, s, pose, hand="claws", w=1.0):
        B = self.B
        el_o, wr_o = POSES[pose]
        sh = self.sh(s)
        el, wr = sh + Vector((s * el_o[0], el_o[1], el_o[2])), sh + Vector((s * wr_o[0], wr_o[1], wr_o[2]))
        rad = [0.03 * w, 0.028 * w, 0.034 * w] if hand == "fists" else [0.03 * w, 0.022 * w, 0.02 * w]
        self.add(g.tube([sh, el, wr], rad, n=6), B.main, True)
        d = (wr - el).normalized()
        if hand == "small":        # small quick hands, their fingertips white
            fing, tips = None, None
            for j, off in enumerate((-0.02, -0.007, 0.007, 0.02)):
                side = d.cross(Z).normalized() if abs(d.z) < 0.9 else X
                tip = wr + d * 0.07 + side * off * 1.6
                fing = g.merge(fing, g.tube([wr, wr + d * 0.035 + side * off, tip], [0.008, 0.007, 0.004], n=4))
                tips = g.merge(tips, g.ico(tip, 0.008, sub=0))
            self.add(fing, B.main, True)
            self.add(tips, field("tips", 4.0))
        elif hand == "fists":      # fists like lumps of slag
            self.add(g.ico(wr + d * 0.03, 0.06, sub=0, scale=(1.05, 1.0, 0.92), rot=(0.4, 0.3, s * 0.5)), B.main, False)
        else:
            claws = None
            for dx in (-0.018, 0.0, 0.018):
                side = d.cross(Z).normalized() if abs(d.z) < 0.9 else X
                claws = g.merge(claws, g.tube([wr, wr + d * 0.04 + side * dx, wr + d * 0.078 + side * dx * 1.4 + Vector((0, 0, -0.012))], [0.011, 0.009, 0.002], n=4))
            self.add(claws, B.main, True)
        if hand == "plated":       # its forearms plated in bright metal
            self.add(g.tube([el + (wr - el) * 0.15, wr - d * 0.005], [0.036, 0.03], n=6), "tin", False)
            self.add(g.tube([el + (wr - el) * 0.12, el + (wr - el) * 0.24], [0.04, 0.04], n=6), "metal_brass", False)
        elif hand == "ash":        # grey to the elbows
            self.add(g.tube([el, wr + d * 0.01], [0.027, 0.025], n=6), "ash", True)
        tag = "l" if s > 0 else "r"
        self.hands[tag] = wr
        return wr

    def limbs(self):
        """Its legs, by how it is standing."""
        B, st = self.B, self.legs
        for tag, s in (("l", 1), ("r", -1)):
            hip = Vector((s * 0.055 * self.belly, 0.0, self.hip))
            if st == "sit":        # cross-legged on the ground
                knee, ank = Vector((s * 0.17, -0.07, 0.07)), Vector((-s * 0.03, -0.17, 0.04))
                self.add(g.tube([hip, knee, ank], [0.042, 0.034, 0.024], n=6), B.main, True)
                toe = ank + Vector((-s * 0.06, -0.01, 0.0))
                self.add(g.tongue([ank, toe], [0.045, 0.012], thick=0.5, normal=Z), B.main)
            elif st == "kneel":
                knee, ank = Vector((s * 0.09, -0.13, 0.04)), Vector((s * 0.1, 0.08, 0.04))
                self.add(g.tube([hip, knee, ank], [0.042, 0.034, 0.024], n=6), B.main, True)
                toe = ank + Vector((0, 0.07, -0.01))
                self.add(g.tongue([ank, toe], [0.045, 0.012], thick=0.5, normal=Z), B.main)
            elif st == "crouch":   # knees wide, its heels dug in
                knee, ank = Vector((s * 0.15, -0.1, 0.19)), Vector((s * 0.1, -0.06, 0.03))
                self.add(g.tube([hip, knee, ank], [0.042, 0.032, 0.022], n=6), B.main, True)
                toe = ank + Vector((0, -0.08, -0.025))
                self.add(g.tongue([ank + Vector((0, 0.02, -0.015)), toe], [0.05, 0.012], thick=0.5, normal=Z), B.main)
            elif st == "ride":     # sat on a slope, its knees up, its heels dug into it
                knee, ank = hip + Vector((s * 0.085, -0.13, 0.05)), hip + Vector((s * 0.035, 0.0, -0.16))
                self.add(g.tube([hip, knee, ank], [0.042, 0.032, 0.022], n=6), B.main, True)
                toe = ank + Vector((0, -0.05, -0.05))
                self.add(g.tongue([ank + Vector((0, 0.01, 0.01)), toe], [0.05, 0.012], thick=0.5, normal=(0, -0.76, 0.64)), B.main)
            elif st == "long":     # long thin legs of flame, never both on the ground
                if s > 0:
                    knee, ank = hip + Vector((0.02, -0.03, -self.hip * 0.42)), Vector((0.07, 0.02, 0.0))
                else:
                    knee, ank = hip + Vector((-0.07, -0.16, -self.hip * 0.2)), hip + Vector((-0.09, 0.02, -self.hip * 0.55))
                self.add(g.tube([hip, knee], [0.036, 0.022], n=6), B.main, True)
                self.add(g.tongue([knee, (knee + ank) / 2 + Vector((0.01, -0.02, 0)), ank], [0.04, 0.032, 0.004], thick=0.6, normal=(0, -1, 0)), field("legs", 2.6))
                toe = ank
            elif st == "tiptoe":   # it lifts each foot out of the wet
                if s > 0:
                    knee, ank = Vector((0.07, -0.035, self.hip * 0.57)), Vector((0.065, 0.0, 0.07))
                    toe = Vector((0.065, -0.03, 0.0))
                else:
                    knee, ank = Vector((-0.11, -0.13, self.hip * 0.95)), Vector((-0.1, -0.06, self.hip * 0.5))
                    toe = ank + Vector((0, -0.04, -0.07))
                self.add(g.tube([hip, knee, ank], [0.042, 0.03, 0.022], n=6), B.main, True)
                self.add(g.tongue([ank, toe], [0.04, 0.012], thick=0.5, normal=(0, -1, 0.4)), B.main)
            else:                  # bowed
                knee, ank, toe = Vector((s * 0.085, -0.045, self.hip * 0.57)), Vector((s * 0.075, 0.005, 0.04)), Vector((s * 0.078, -0.075, 0.0))
                self.add(g.tube([hip, knee, ank], [0.042, 0.03, 0.022], n=6), B.main, True)
                self.add(g.tongue([ank + Vector((0, 0.02, -0.015)), ank + Vector((0, -0.03, -0.028)), toe + Vector((0, -0.02, 0.006))], [0.04, 0.055, 0.01], thick=0.5, normal=(0, 0, 1)), B.main)
            self.feet[tag] = toe

    def tail(self, lit=True):
        B = self.B
        z = self.hip + 0.02
        pts = [(0, 0.09 * self.belly, z), (0.0, 0.2, z - 0.04), (0.03, 0.275, z + 0.02), (0.045, 0.27, z + 0.12)]
        self.add(g.tube(pts, [0.02, 0.014, 0.01, 0.006], n=5), B.main, True)
        if lit:
            t = Vector(pts[-1])
            self.add(g.tongue([t, t + Vector((0.015, -0.008, 0.045)), t + Vector((0.003, -0.002, 0.095))], [0.022, 0.034, 0.003], thick=0.5), field("flame", 3.0))


# --- plans -------------------------------------------------------------------------------------

def plan_wick(B, spec):
    """The Starter: a candle flame with two horns and a scowl."""
    I = Imp(B, {})
    # the candle it stands on
    B.add(g.lathe([(0.075, 0.0), (0.07, 0.02), (0.058, 0.03), (0.06, 0.2), (0.05, 0.215), (0.02, 0.2)], n=8), "wax")
    dr = None
    for i, (a, L) in enumerate(((0.5, 0.11), (2.3, 0.07), (4.1, 0.14), (5.4, 0.05))):
        p = Vector((0.06 * math.cos(a), 0.06 * math.sin(a), 0.205))
        dr = g.merge(dr, g.tongue([p, p + Vector((0.008 * math.cos(a), 0.008 * math.sin(a), -L * 0.6)), p + Vector((0.004 * math.cos(a), 0.004 * math.sin(a), -L))], [0.03, 0.034, 0.012], thick=0.5, normal=(math.cos(a), math.sin(a), 0)))
    B.add(dr, B.mark("drips", mat("wax")))
    B.add(sk.disc((0, 0, 0), 0.12, thick=0.014, n=10), "metal_dark", False)
    B.add(g.tube([(0, 0, 0.2), (0.004, 0, 0.235)], [0.006, 0.004], n=3), "metal_dark", False)
    # the flame is the fiend
    c = Vector((0, 0, 0.23))
    B.add(g.lathe([(0.0, 0.0), (0.07, 0.035), (0.092, 0.1), (0.07, 0.19), (0.03, 0.27), (0.0, 0.34)], n=8, centre=c), field("flame", 2.4))
    B.add(sk.flame(c + Vector((0, 0.01, 0.0)), 0.085, 0.3, n=4, turn=0.8), B.under)
    B.add(g.ico(c + Vector((0, 0, 0.09)), 0.04, sub=1, scale=(1, 1, 1.3)), field("core", 5.0))
    face = c + Vector((0, -0.086, 0.115))
    eyes, brows = None, None
    for s in (1, -1):
        eyes = g.merge(eyes, g.ico(face + Vector((s * 0.034, 0, 0)), 0.02, sub=1, scale=(1.2, 0.5, 0.7), rot=(0, s * -0.4, 0)))
        brows = g.merge(brows, g.tongue([face + Vector((s * 0.008, -0.006, 0.012)), face + Vector((s * 0.062, -0.002, 0.044))], [0.016, 0.01], thick=0.6, normal=(0, -1, 0.4)))
    B.add(eyes, "void")
    B.add(brows, B.main)
    B.add(g.tongue([face + Vector((-0.036, 0.004, -0.06)), face + Vector((0, -0.004, -0.045)), face + Vector((0.036, 0.004, -0.06))], [0.005, 0.016, 0.005], thick=0.4, normal=(0, -1, 0)), "void")
    for s in (1, -1):
        B.add(g.tube([c + Vector((s * 0.052, -0.01, 0.2)), c + Vector((s * 0.088, -0.006, 0.255)), c + Vector((s * 0.078, 0.012, 0.31))], [0.02, 0.014, 0.003], n=5), "horn", False)
        B.add(g.tube([c + Vector((s * 0.08, -0.02, 0.09)), c + Vector((s * 0.125, -0.03, 0.06)), c + Vector((s * 0.095, -0.05, 0.03))], [0.014, 0.012, 0.012], n=5), B.main, True)
    I.top, I.zs, I.zh = 0.57, 0.3, 0.35
    I.hands = {"l": c + Vector((0.095, -0.05, 0.03)), "r": c + Vector((-0.095, -0.05, 0.03))}
    B.frame(0.52, front=-0.1, mid=0.33, half=0.11)
    B.socket("socket_eyes", face + Vector((0, -0.012, 0)))
    B.socket("socket_head", (0, 0, 0.54))
    return I


def plan_imp(B, spec):
    bd = dict(_stage(B.level))
    bd.update(spec.get("build", {}))
    legs, _ = opt(spec.get("legs", "bowed"))
    I = Imp(B, bd, legs)
    I.trunk()
    I.skull()
    hs, hk = opt(spec.get("horns", "curved"))
    I.horns(hs or "curved", hk or 1.0)
    crown, ck = opt(spec.get("crown", "candle"))
    I.crown_style, I.crown_size = crown, ck
    if crown in ("candle", "flare", "letters", "thread"):
        I.candle(size={"flare": 2.4}.get(crown, 1.0) * (ck if crown in ("candle", "flare") else 1.0))
    elif crown == "bare":      # the stub is there, and not alight
        I.candle(lit=0.0)
    eyes, _ = opt(spec.get("eyes", "scowl"))
    mouth, _ = opt(spec.get("mouth", "grin"))
    I.face(eyes, mouth)
    hand, _ = opt(spec.get("hands", "claws"))
    pose, _ = opt(spec.get("arms", "hang"))
    pl, pr = (pose.split("/") + [pose])[:2] if pose else ("hang", "hang")
    wide = 1.3 if hand == "fists" else 1.0
    I.arm(1, pl, hand, wide)
    I.arm(-1, pr, hand, wide)
    I.limbs()
    tail, _ = opt(spec.get("tail", "flame"))
    if tail != "none":
        I.tail(lit=tail == "flame")     # "dark": its tail is there, and not alight
    return I


def _crack_lines(c, r, n=6, seed=0.0, squash=(1, 1, 1)):
    """Cracks over a ball about c, the glow showing through."""
    geo = None
    for i in range(n):
        a, b = seed + i * 2.4, 0.5 + 0.9 * math.sin(i * 1.7 + seed)
        p0 = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b))) * r
        a2, b2 = a + 0.5, b - 0.55
        p1 = Vector((math.cos(a2) * math.cos(b2), math.sin(a2) * math.cos(b2), math.sin(b2))) * r
        mid = ((p0 + p1) / 2).normalized() * r
        pts = [Vector((p.x * squash[0], p.y * squash[1], p.z * squash[2])) + V(c) for p in (p0, mid, p1)]
        geo = g.merge(geo, g.tube(pts, [0.004, 0.009, 0.003], n=3))
    return geo


def plan_ball(B, spec):
    """Balled tight, its claws dug in, hot, waiting to be thrown."""
    bd = {"ball": 1.0, "lift": 0.0, "dive": 0.0}
    bd.update(spec.get("build", {}))
    k = bd["ball"]
    I = Imp(B, {"dive": bd["dive"]})
    c = Vector((0, 0, 0.2 * k + 0.03 + bd["lift"]))
    I.c, I.r = c, 0.17 * k
    I.add(g.ico(c, 0.17 * k, sub=1, scale=(1.0, 0.95, 0.95)), B.main)
    I.add(_crack_lines(c, 0.168 * k, n=7, seed=0.6), field("crack", 2.8))
    # the face of it, low on the front
    f = c + Vector((0, -0.15 * k, 0.03 * k))
    I.add(sk.eye_pair(f + Vector((0, 0, 0.02 * k)), 0.05 * k, 0.026 * k, scale=(1.25, 0.45, 0.6), slant=0.35), field("eyes", 4.2))
    I.add(g.tongue([f + Vector((-0.06 * k, 0.012, -0.05 * k)), f + Vector((-0.025 * k, -0.004, -0.065 * k)), f + Vector((0.025 * k, -0.004, -0.065 * k)), f + Vector((0.06 * k, 0.012, -0.05 * k))], [0.004, 0.022 * k, 0.022 * k, 0.004], thick=0.3, normal=(0, -1, 0)), field("mouth", 3.0))
    for s in (1, -1):
        I.add(g.tube([c + Vector((s * 0.07, -0.06, 0.14)) * k, c + Vector((s * 0.115, -0.05, 0.21)) * k, c + Vector((s * 0.1, 0.0, 0.27)) * k], [0.024 * k, 0.016 * k, 0.003], n=5), "horn", False)
        # its arms and legs wrapped round itself
        I.add(g.tube([c + Vector((s * 0.15, 0.03, 0.06)) * k, c + Vector((s * 0.165, -0.08, -0.0)) * k, c + Vector((s * 0.1, -0.155, -0.04)) * k], [0.03 * k, 0.026 * k, 0.02 * k], n=6), B.under, True)
        I.add(sk.fingers(c + Vector((s * 0.1, -0.155, -0.04)) * k, Vector((-s * 0.5, -0.5, -0.4)), n=3, L=0.06 * k, spread=0.018, r=0.011, hook=0.4), B.main)
        I.add(g.tube([c + Vector((s * 0.1, 0.06, -0.1)) * k, c + Vector((s * 0.15, -0.05, -0.12)) * k, c + Vector((s * 0.07, -0.13, -0.13)) * k], [0.036 * k, 0.03 * k, 0.02 * k], n=6), B.under, True)
        I.hands["l" if s > 0 else "r"] = c + Vector((s * 0.1, -0.155, -0.04)) * k
    tail = [c + Vector((0, 0.16, -0.02)) * k, c + Vector((0.12, 0.15, 0.03)) * k, c + Vector((0.19, 0.03, 0.09)) * k, c + Vector((0.16, -0.05, 0.16)) * k]
    I.add(g.tube(tail, [0.02, 0.015, 0.011, 0.006], n=5), B.main, True)
    I.add(g.tongue([tail[-1], tail[-1] + Vector((0.01, -0.01, 0.045)), tail[-1] + Vector((0.0, 0.0, 0.1))], [0.022, 0.034, 0.003], thick=0.5), field("flame", 3.0))
    I.top, I.zs, I.zh, I.zt, I.hip = c.z + 0.17 * k, c.z, c.z + 0.03, c.z + 0.1, c.z - 0.1
    I.crown_style = "none"
    B.frame(I.top, front=-0.16 * k, mid=c.z, half=0.18 * k)
    B.socket("socket_eyes", f + Vector((0, -0.015, 0.02)))
    return I


def plan_bottle(B, spec):
    """It lives in an old stopped flask, its light pressed small against the glass."""
    bd = {"big": 1.0}
    bd.update(spec.get("build", {}))
    k = bd["big"]
    bound = any(st == "bound" for st, _ in each(spec.get("bottle")))
    I = Imp(B, {})
    z0 = 0.1 if not bound else 0.07
    prof = [(0.05, 0.0), (0.14, 0.03), (0.185, 0.14), (0.17, 0.27), (0.1, 0.36), (0.055, 0.41), (0.05, 0.5), (0.062, 0.52), (0.06, 0.54)]
    B.add(g.lathe([(r * k, z0 + z * k) for r, z in prof], n=10), "pane", True)
    top = z0 + 0.54 * k
    B.add(g.lathe([(0.05 * k, top - 0.01), (0.056 * k, top + 0.03 * k), (0.045 * k, top + 0.06 * k), (0.0, top + 0.065 * k)], n=8), "cord")
    # the light of it, where the glass is thin: a band round the belly, and its face
    B.add(g.lathe([(0.187 * k, z0 + 0.13 * k), (0.19 * k, z0 + 0.155 * k)], n=10, caps=False), field("glow", 1.8))
    f = Vector((0, -0.172 * k, z0 + 0.24 * k))
    if not bound:
        B.add(sk.eye_pair(f, 0.05 * k, 0.03 * k, scale=(1.2, 0.4, 0.75), slant=0.3), field("eyes", 4.0))
        B.add(g.tongue([f + Vector((-0.06 * k, 0.014, -0.065 * k)), f + Vector((-0.025 * k, -0.006, -0.08 * k)), f + Vector((0.025 * k, -0.006, -0.08 * k)), f + Vector((0.06 * k, 0.014, -0.065 * k))], [0.004, 0.022 * k, 0.022 * k, 0.004], thick=0.3, normal=(0, -1, 0)), field("mouth", 3.0))
        # two palms flat against the inside of the glass
        palms = None
        for s in (1, -1):
            p = Vector((s * 0.12 * k, -0.13 * k, z0 + 0.13 * k))
            palms = g.merge(palms, g.ico(p, 0.028 * k, sub=1, scale=(1.0, 0.4, 1.1)), sk.fingers(p + Vector((0, -0.004, 0.01)), Vector((s * 0.15, -0.05, 1)), n=3, L=0.05 * k, spread=0.016, r=0.01))
        B.add(palms, B.main)
        # its horns have gone through the shoulder of it, its legs through the bottom, its tail up the neck
        for s in (1, -1):
            B.add(g.tube([Vector((s * 0.07 * k, -0.02, z0 + 0.34 * k)), Vector((s * 0.13 * k, -0.02, z0 + 0.42 * k)), Vector((s * 0.12 * k, 0.01, z0 + 0.5 * k))], [0.022 * k, 0.015 * k, 0.003], n=5), "horn", False)
            hip, foot = Vector((s * 0.06 * k, 0, z0 + 0.02)), Vector((s * 0.08 * k, -0.01, 0.03))
            B.add(g.tube([hip, foot], [0.03, 0.022], n=6), B.main, True)
            B.add(g.tongue([foot + Vector((0, 0.02, -0.01)), foot + Vector((0, -0.07, -0.028))], [0.05, 0.012], thick=0.5, normal=Z), B.main)
            I.feet["l" if s > 0 else "r"] = foot
        t0 = Vector((0, 0, top + 0.06 * k))
        B.add(g.tube([t0, t0 + Vector((0.02, 0, 0.05)), t0 + Vector((0.0, 0.01, 0.1))], [0.012, 0.01, 0.006], n=5), B.main, True)
        B.add(sk.flame(t0 + Vector((0, 0.01, 0.09)), 0.03, 0.1, n=3), field("flame", 3.0))
    I.z0, I.k, I.face_at = z0, k, f
    I.top, I.zs, I.zh, I.zt, I.hip = top + 0.06 * k, z0 + 0.3 * k, z0 + 0.24 * k, z0 + 0.4 * k, z0
    I.hands = {"l": Vector((0.19 * k, 0, z0 + 0.2 * k)), "r": Vector((-0.19 * k, 0, z0 + 0.2 * k))}
    I.crown_style = "none"
    B.frame(I.top, front=-0.19 * k, mid=z0 + 0.22 * k, half=0.19 * k)
    B.socket("socket_eyes", f + Vector((0, -0.015, 0)))
    return I


def bottle_bound(B, I, size):
    """A brass-bound bottle, hot to hold: nobody is at home."""
    z0, k = I.z0, I.k
    for z, r in ((0.05, 0.158), (0.2, 0.188), (0.33, 0.135)):
        B.add(sk.hoop((0, 0, z0 + z * k), r * k, r * k, 0.012 * k, n=12, sides=4), "metal_brass", False)
    straps = None
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        straps = g.merge(straps, g.tube([d * 0.158 * k + Z * (z0 + 0.05 * k), d * 0.19 * k + Z * (z0 + 0.14 * k), d * 0.188 * k + Z * (z0 + 0.2 * k), d * 0.135 * k + Z * (z0 + 0.33 * k), d * 0.06 * k + Z * (z0 + 0.42 * k)], [0.012 * k] * 5, n=4))
    B.add(straps, "metal_brass", False)
    # it looks out through a gap between the bands, and will not come out
    f = I.face_at + Vector((0, -0.004, 0.02 * k))
    B.add(g.box(f + Vector((0, 0.012, 0)), (0.16 * k, 0.02, 0.05 * k)), "void", False)
    B.add(sk.eye_pair(f + Vector((0, -0.004, 0)), 0.042 * k, 0.02 * k, scale=(1.2, 0.4, 0.6), slant=-0.2), field("eyes", 4.0))
    # the stopper waxed and chained
    top = z0 + 0.54 * k
    B.add(g.lathe([(0.06 * k, top + 0.02 * k), (0.066 * k, top + 0.055 * k), (0.03 * k, top + 0.085 * k), (0.0, top + 0.09 * k)], n=8), "wax_red")
    B.add(sk.chain([Vector((0.05 * k, -0.03, top + 0.05 * k)), Vector((0.1 * k, -0.06, z0 + 0.42 * k)), Vector((0.14 * k, -0.07, z0 + 0.33 * k))], link=0.014 * k, n=7), "metal_iron_light", False)
    feet = None
    for i in range(3):
        a = math.pi / 2 + i * 2 * math.pi / 3
        feet = g.merge(feet, g.ico((0.12 * k * math.cos(a), 0.12 * k * math.sin(a), 0.035), 0.04 * k, sub=1))
    B.add(feet, "metal_brass", False)
    st = None
    for i, (x, y) in enumerate(((0.05, 0.02), (-0.04, -0.01))):
        st = g.merge(st, sk.smoke_thread((x * k, y, top + 0.09 * k), 0.16 * k, sway=0.02, w=0.03, n=4))
    B.add(st, "steam")


def plan_stove(B, spec):
    """An iron stove with horns cast into the lid and a red eye behind the door."""
    bd = {"tall": 1.0, "legs": 1.0, "wide": 1.0}
    bd.update(spec.get("build", {}))
    kinds = [st for st, _ in each(spec.get("stove"))]
    walker, pot, watch = "walker" in kinds, "pot" in kinds, "watchfire" in kinds
    t, w = bd["tall"], bd["wide"]
    iron, lite, brass, dark = B.main, B.under, B.trim, mat("metal_dark")
    I = Imp(B, {})
    lz = 0.15 * bd["legs"] * (2.6 if walker else 1.0)      # the height of the belly's foot
    z = lambda v: lz + (v - 0.15) * t  # noqa: E731
    B.add(g.lathe([(0.085 * w, z(0.15)), (0.17 * w, z(0.2)), (0.215 * w, z(0.3)), (0.2 * w, z(0.42)), (0.152 * w, z(0.5)), (0.13 * w, z(0.522))], n=10), iron, False)
    B.add(g.lathe([(0.2205 * w, z(0.28)), (0.225 * w, z(0.3)), (0.2165 * w, z(0.33))], n=10, caps=False), B.mark("band", iron), False)
    B.add(g.lathe([(0.14 * w, z(0.52)), (0.168 * w, z(0.53)), (0.162 * w, z(0.546)), (0.05 * w, z(0.552)), (0.0, z(0.556))], n=10), lite, False)
    # horns cast into the lid
    for s in (1, -1):
        B.add(g.tube([Vector((s * 0.08 * w, -0.02, z(0.545))), Vector((s * 0.15 * w, -0.02, z(0.6))), Vector((s * 0.14 * w, 0.01, z(0.69)))], [0.03, 0.022, 0.004], n=5), iron, False)
    # the door, and what is behind it
    dz = z(0.315)
    if watch:                  # the door stands open, and the light reaches further than it should
        B.add(g.box((0, -0.19 * w, dz), (0.19, 0.03, 0.2)), "void", False)
        B.add(g.ico((0, -0.19 * w, dz), 0.085, sub=1, scale=(1.0, 0.5, 1.05)), field("core", 4.6))
        B.add(sk.flame(Vector((0, -0.2 * w, dz - 0.08)), 0.07, 0.2, n=3, lean=(0, -0.25)), field("flame", 3.2))
        B.add(g.box((0.19 * w, -0.25 * w, dz), (0.03, 0.18, 0.2), rot=(0, 0, -0.5)), B.mark("enamel", lite), False)
    else:
        B.add(g.box((0, -0.203 * w, dz), (0.17, 0.04, 0.17)), B.mark("enamel", lite), False)
        B.add(g.box((0, -0.222 * w, dz), (0.118, 0.012, 0.11)), "void", False)
        # one red eye behind the bars
        B.add(g.ico((0, -0.224 * w, dz), 0.04, sub=1, scale=(1.25, 0.3, 0.8)), field("eyes", 4.2))
        B.add(g.ico((0, -0.232 * w, dz), 0.013, sub=0, scale=(0.6, 0.4, 1.6)), "void")
        bars = g.merge(*[g.box((-0.045 + 0.03 * j, -0.231 * w, dz), (0.009, 0.012, 0.118)) for j in range(4)], g.box((0, -0.231 * w, dz + 0.057), (0.13, 0.014, 0.012)), g.box((0, -0.231 * w, dz - 0.057), (0.13, 0.014, 0.012)))
        B.add(bars, dark, False)
        B.add(g.merge(g.tube([(0.098, -0.225 * w, dz + 0.015), (0.098, -0.25 * w, dz + 0.015), (0.098, -0.25 * w, dz - 0.02)], [0.008, 0.008, 0.008], n=4)), brass, False)
    # two vents over the door
    vents, rims = None, None
    for s in (1, -1):
        c = Vector((s * 0.062 * w, -0.176 * w, z(0.44)))
        vents = g.merge(vents, g.ico(c, 0.02, sub=1, scale=(1.0, 0.5, 1.0)))
        rims = g.merge(rims, sk.hoop(c + Vector((0, -0.006, 0)), 0.024, 0.024, 0.006, n=8, u=X, v=Z, sides=3))
    B.add(vents, field("vents", 2.4))
    B.add(rims, brass, True)
    riv = None
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        riv = g.merge(riv, g.ico((0.205 * w * math.cos(a), 0.205 * w * math.sin(a), z(0.42)), 0.011, sub=0))
    B.add(riv, brass, True)
    # the pipe
    if pot:                    # the pipe goes out behind, and a pot rides on the lid
        B.add(g.tube([(0, 0.13 * w, z(0.5)), (0, 0.24 * w, z(0.56)), (0, 0.26 * w, z(0.78))], [0.045, 0.045, 0.04], n=8), lite, False)
        ptop = Vector((0, 0.26 * w, z(0.78)))
        B.add(g.lathe([(0.1, 0.0), (0.125, 0.03), (0.12, 0.12), (0.128, 0.13)], n=8, centre=(0, -0.01, z(0.556))), "metal_iron_light", False)
        B.add(g.lathe([(0.13, 0.0), (0.09, 0.03), (0.02, 0.045), (0.025, 0.07), (0.0, 0.075)], n=8, centre=(0, -0.01, z(0.556) + 0.13)), brass, False)
        for s in (1, -1):
            B.add(sk.arc((s * 0.128, -0.01, z(0.556) + 0.09), 0.03, 0.025, -math.pi / 2, math.pi / 2, 0.008, n=5, u=X * s, v=Z, sides=3), brass, False)
        st = None
        for i, (x, y) in enumerate(((0.06, -0.05), (-0.05, 0.0), (0.0, -0.08))):
            st = g.merge(st, sk.smoke_thread((x, y, z(0.556) + 0.16), 0.16 + 0.04 * i, sway=0.025, w=0.035, n=4))
        B.add(st, "steam")
    else:
        B.add(g.tube([(0, 0.075, z(0.54)), (0, 0.075, z(0.74) + (0.12 if watch else 0.0))], [0.046, 0.042], n=8), lite, False)
        ptop = Vector((0, 0.075, z(0.74) + (0.12 if watch else 0.0)))
    B.add(g.lathe([(0.08, 0.025), (0.05, 0.05), (0.012, 0.066)], n=8, centre=ptop), iron, False)
    struts = None
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        struts = g.merge(struts, g.tube([ptop + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), -0.005)), ptop + Vector((0.05 * math.cos(a), 0.05 * math.sin(a), 0.032))], [0.005, 0.005], n=3))
    B.add(struts, dark, False)
    B.add(g.merge(g.ico(ptop + Vector((0.0, 0.055, 0.035)), 0.026, sub=0, scale=(1.0, 1.0, 0.8)), g.ico(ptop + Vector((0.02, 0.11, 0.06)), 0.034, sub=0, scale=(1.0, 1.1, 0.8), rot=(0.4, 0.2, 0.3)),
                  g.ico(ptop + Vector((-0.012, 0.18, 0.095)), 0.042, sub=0, scale=(1.0, 1.1, 0.75), rot=(0.1, 0.5, 1.0))), "smoke")
    if watch:                  # a lamp for a crown, between the horns
        B.extend(sk.lantern(Vector((0, -0.02, z(0.556) + 0.2)), 0.085, glow="lamp", strength=3.8))
        B.add(sk.arc((0, -0.02, z(0.556) + 0.2), 0.075 * w, 0.05, 0.0, math.pi, 0.008, n=6, u=X, v=Z, sides=3), brass, False)
    # three legs
    for tag, deg in (("fl", 320), ("fr", 220), ("bl", 90)):
        a = math.radians(deg)
        d = Vector((math.cos(a), math.sin(a), 0))
        if walker:             # jointed, and it has not spilled
            hip, knee, ank, foot = d * 0.15 * w + Z * (lz + 0.03), d * 0.36 + Z * (lz + 0.12), d * 0.3 + Z * (lz * 0.45), d * 0.36 + Z * 0.02
            B.add(g.tube([hip, knee, ank, foot], [0.03, 0.026, 0.022, 0.018], n=5), iron, False)
            B.add(sk.gear(knee, 0.06, teeth=8, thick=0.03, axis=d.cross(Z)), brass, False)
            B.add(g.merge(g.ico(ank, 0.03, sub=1), g.ico(foot + d * 0.012, 0.045, sub=1, scale=(1.0, 1.0, 0.5))), brass, True)
        else:
            hip, knee, foot = d * 0.14 * w + Z * (lz + 0.035), d * 0.245 * w + Z * (lz * 0.83), d * 0.25 * w + Z * 0.02
            B.add(g.tube([hip, knee, foot], [0.03, 0.026, 0.02], n=6), iron, False)
            B.add(g.merge(g.ico(knee, 0.034, sub=1), g.ico(foot + d * 0.012, 0.04, sub=1, scale=(1.0, 1.0, 0.5))), brass, True)
        I.feet[tag] = foot
    I.top, I.zs, I.zh, I.zt, I.hip = z(0.556), z(0.36), z(0.44), z(0.5), lz
    I.hands = {"l": Vector((0.225 * w, 0, z(0.36))), "r": Vector((-0.225 * w, 0, z(0.36)))}
    I.crown_style = "none"
    B.frame(I.top, front=-0.22 * w, mid=z(0.36), half=0.22 * w)
    B.socket("socket_eyes", (0, -0.2 * w, z(0.44)))
    B.socket("socket_mouth", (0, -0.24 * w, dz))
    for tag in ("fl", "fr", "bl"):
        B.socket("socket_limb_" + tag, I.feet[tag])
    return I


def plan_candle(B, spec):
    """A tall still flame with a cold heart, on a candle that has a face."""
    I = Imp(B, {})
    brass = "metal_brass"
    B.add(g.lathe([(0.15, 0.0), (0.13, 0.02), (0.05, 0.05), (0.03, 0.1), (0.055, 0.13), (0.03, 0.16), (0.03, 0.22), (0.13, 0.25), (0.14, 0.27), (0.05, 0.28)], n=10), brass, False)
    B.add(g.lathe([(0.085, 0.27), (0.09, 0.5), (0.086, 0.82), (0.07, 0.84), (0.03, 0.825)], n=10), "wax")
    dr = None
    for i, (a, L) in enumerate(((0.4, 0.2), (1.6, 0.12), (2.9, 0.26), (4.0, 0.16), (5.2, 0.3), (5.9, 0.1))):
        p = Vector((0.086 * math.cos(a), 0.086 * math.sin(a), 0.83))
        dr = g.merge(dr, g.tongue([p, p + Vector((0.01 * math.cos(a), 0.01 * math.sin(a), -L * 0.6)), p + Vector((0.006 * math.cos(a), 0.006 * math.sin(a), -L))], [0.036, 0.04, 0.014], thick=0.5, normal=(math.cos(a), math.sin(a), 0)))
    B.add(dr, B.mark("drips", mat("wax")))
    # the face in the wax, and its horns through it
    f = Vector((0, -0.089, 0.62))
    B.add(sk.eye_pair(f, 0.036, 0.02, scale=(1.2, 0.45, 0.45), slant=-0.12), field("eyes", 2.8))
    B.add(g.box(f + Vector((0, 0.002, -0.06)), (0.07, 0.03, 0.012)), "metal_iron", False)
    B.extend(sk.lantern(f + Vector((0, -0.004, -0.06)), 0.04, glow="lamp", strength=3.0))
    for s in (1, -1):
        B.add(g.tube([Vector((s * 0.06, -0.03, 0.74)), Vector((s * 0.125, -0.03, 0.8)), Vector((s * 0.115, 0.0, 0.89))], [0.022, 0.015, 0.003], n=5), "horn", False)
        B.add(g.tube([Vector((s * 0.085, -0.02, 0.5)), Vector((s * 0.14, -0.05, 0.44)), Vector((s * 0.09, -0.1, 0.4))], [0.022, 0.018, 0.016], n=5), B.main, True)
    B.add(g.ico(Vector((0, -0.1, 0.395)), 0.04, sub=1, scale=(1.5, 0.8, 0.8)), B.main)
    # the flame: tall, still, a cold heart in it
    c = Vector((0, 0, 0.845))
    B.add(g.tube([c - Z * 0.02, c + Z * 0.035], [0.006, 0.004], n=3), "metal_dark", False)
    B.add(g.lathe([(0.0, 0.0), (0.03, 0.04), (0.036, 0.12), (0.024, 0.24), (0.0, 0.34)], n=8, centre=c + Z * 0.03), "ice_pale", True)
    B.add(sk.flame(c + Z * 0.02, 0.062, 0.46, n=4, turn=0.3, tall=0.0, thick=0.3), field("flame", 2.8))
    I.top, I.zs, I.zh, I.zt, I.hip = 0.86, 0.5, 0.62, 0.8, 0.27
    I.hands = {"l": Vector((0.09, -0.1, 0.4)), "r": Vector((-0.09, -0.1, 0.4))}
    I.crown_style = "none"
    B.frame(0.86, front=-0.1, mid=0.55, half=0.12)
    B.socket("socket_eyes", f + Vector((0, -0.015, 0)))
    return I


PLANS = {"wick": plan_wick, "imp": plan_imp, "ball": plan_ball, "bottle": plan_bottle, "stove": plan_stove, "candle": plan_candle}


# --- what it has ---------------------------------------------------------------------------------
# A style is given the Body and the imp. What moves with the imp (what it wears and holds) is
# added to the imp, so it leans and tips with it; what stands on the ground is added to the Body.

def crown_flare(B, I, size):
    """Twice the size it was a moment ago: the flame on its head goes up and back in a mane."""
    geo, dark = None, None
    for i in range(6):
        a = math.pi * (0.15 + 0.7 * i / 5)
        b0 = I.H(0.07 * math.cos(a), 0.05 + 0.03 * math.sin(a), 0.6)
        L = (0.2 + 0.07 * math.sin(i * 1.9)) * size
        tg = g.tongue([b0, b0 + Vector((0.05 * math.cos(a), 0.06, L * 0.5)), b0 + Vector((0.03 * math.cos(a), 0.14, L))], [0.07, 0.06, 0.004], thick=0.45, normal=(math.cos(a), 0.4, 0))
        if i % 2:
            dark = g.merge(dark, tg)
        else:
            geo = g.merge(geo, tg)
    I.add(geo, field("flame", 2.8))
    I.add(dark, B.under)
    for s in (1, -1):
        p = I.sh(s) + Vector((0, 0.03, 0.03))
        I.add(g.tongue([p, p + Vector((s * 0.05, 0.05, 0.1)) * size, p + Vector((s * 0.03, 0.1, 0.22)) * size], [0.06, 0.05, 0.004], thick=0.45, normal=(s, 0.3, 0)), field("flame", 2.4))


def crown_fuse(B, I, size):
    """A short black wick stands up from its head, always a little alight at the tip."""
    b0 = I.H(0, -0.02, 0.63)
    pts = [b0, b0 + Vector((0.0, 0.0, 0.07 * size)), b0 + Vector((0.035, 0.0, 0.13 * size)), b0 + Vector((0.03, 0.01, 0.19 * size))]
    I.add(g.tube(pts, [0.016, 0.013, 0.011, 0.009], n=5), "soot", True)
    I.add(g.lathe([(0.03, 0.0), (0.034, 0.012), (0.018, 0.02)], n=6, centre=b0), "metal_dark", False)
    t = pts[-1]
    sp = g.ico(t, 0.018, sub=0)
    for i in range(5):
        a = i * 2 * math.pi / 5
        d = Vector((math.cos(a), 0.3 * math.sin(a * 2), math.sin(a)))
        sp = g.merge(sp, g.blade(t + d * 0.012, t + d * 0.06 * size, 0.018, normal=Y))
    I.add(sp, field("spark", 4.2))


def crown_letters(B, I, size):
    """Letters of fire hang over its head like a crown."""
    c = I.H(0, -0.02, 0.545)
    R = 0.19 * size
    geo = None
    for i in range(7):
        a = math.pi * (0.08 + 0.84 * i / 6)
        p = c + Vector((R * math.cos(a), 0.0, 0.17 + R * math.sin(a)))
        t = Vector((-math.sin(a), 0, math.cos(a)))     # along the arc
        n = Vector((math.cos(a), 0, math.sin(a)))      # outward
        k = 0.034 * size
        strokes = (((0, -1), (0, 1)), ((0, 1), (0.8, 0.2)), ((0, 0), (0.7, -0.8))) if i % 3 == 0 else ((((-0.6, -1), (0, 1)), ((0, 1), (0.6, -1)), ((-0.3, 0), (0.3, 0))) if i % 3 == 1 else (((-0.5, 1), (0.5, 1)), ((0, 1), (0, -1)), ((-0.5, -1), (0.5, -1))))
        for (x0, y0), (x1, y1) in strokes:
            geo = g.merge(geo, g.tube([p + t * x0 * k + n * y0 * k, p + t * x1 * k + n * y1 * k], [0.006, 0.006], n=3))
    I.add(geo, field("letters", 3.2))


def crown_thread(B, I, size):
    """Its smoke goes up in one straight thread, and bends near the top."""
    b0 = I.H(0, -0.02, 0.66) + Vector((0, 0, 0.1))
    I.add(sk.smoke_thread(b0, 0.62 * size, sway=0.006, w=0.022, n=6, bend=(0.72, 0.13, -0.05)), "smoke")


def skin_ash(B, I, size):
    """Grey with ash: it lies on its head and its shoulders."""
    geo = g.ico(I.H(0, 0.0, 0.62), 0.07 * I.head * size, sub=1, scale=(1.25, 1.1, 0.5))
    for s in (1, -1):
        geo = g.merge(geo, g.ico(I.sh(s) + Vector((s * 0.01, 0.01, 0.03)), 0.055 * size, sub=1, scale=(1.2, 1.1, 0.55)))
    geo = g.merge(geo, g.ico(Vector((0, 0.07 * I.belly, I.zs - 0.03)), 0.085 * size * I.belly, sub=1, scale=(1.1, 0.7, 0.9)))
    I.add(geo, "ash")


def skin_iron(B, I, size):
    """A skin of cooled iron, cracked, the glow showing through the cracks."""
    plates = None
    b = I.belly
    spots = [(I.H(0, 0.01, 0.625), (0.085, 0.085, 0.035), (0, 0, 0)), (Vector((0, 0.09 * b, I.zs - 0.04)), (0.1 * b, 0.05, 0.1), (0.2, 0, 0)), (Vector((0, -0.105 * b, I.zs - 0.07)), (0.085 * b, 0.035, 0.07), (-0.15, 0, 0))]
    for s in (1, -1):
        spots += [(I.sh(s) + Vector((s * 0.02, 0.0, 0.025)), (0.06, 0.06, 0.04), (0, s * 0.5, 0)), (Vector((s * 0.105 * b, 0.0, I.hip + 0.07)), (0.045, 0.09, 0.06), (0, 0, 0))]
        if "l" in I.hands:
            wr = I.hands["l" if s > 0 else "r"]
            spots.append((wr + Vector((0, 0.01, 0.045)), (0.036, 0.036, 0.05), (0, 0, 0)))
    for c, sc, rot in spots:
        plates = g.merge(plates, g.ico(c, 1.0, sub=0, scale=tuple(v * size for v in sc), rot=rot))
    I.add(plates, "clinker", False)
    I.add(_crack_lines(Vector((0, 0, I.zs - 0.08)), 0.122 * b, n=8, seed=1.1, squash=(1.0, 1.0, 1.15)), field("crack", 3.0))
    I.add(_crack_lines(I.H(0, -0.02, 0.545), 0.105 * I.head, n=4, seed=0.3), field("crack", 3.0))
    # what it has hold of runs
    for tag in ("l", "r"):
        if tag in I.hands:
            wr = I.hands[tag]
            I.add(g.tongue([wr + Vector((0, -0.02, -0.03)), wr + Vector((0.005, -0.02, -0.09)), wr + Vector((0, -0.02, -0.15))], [0.022, 0.026, 0.004], thick=0.6, normal=-Y), field("melt", 2.6))


def skin_soot(B, I, size):
    """Scorched: soot up its front."""
    b, k, h0 = I.belly, I.tall, I.hip - 0.02
    # its belly gone black (over the paler one it had), and the lick of it up its chest
    geo = g.ico((0, -0.074 * b, h0 + 0.105 * k), 0.08 * b, sub=1, scale=(1.04, 0.52, 1.1 * k))
    for x, z0, L in ((-0.03, 0.16, 0.09), (0.035, 0.17, 0.07)):
        p = Vector((x * b, -0.1 * b, h0 + z0 * k))
        geo = g.merge(geo, g.tongue([p, p + Vector((0.008, 0.016, L * 0.6 * size)), p + Vector((-0.004, 0.045, L * size))], [0.05 * size, 0.035 * size, 0.004], thick=0.2, normal=(0, -1, 0.2)))
    I.add(geo, "soot")


def skin_still(B, I, size):
    """A body gone grey and still."""
    geo = g.ico(I.H(0, 0.0, 0.62), 0.085 * I.head, sub=1, scale=(1.2, 1.1, 0.45))
    for s in (1, -1):
        geo = g.merge(geo, g.ico(I.sh(s) + Vector((s * 0.012, 0.01, 0.03)), 0.05, sub=1, scale=(1.2, 1.1, 0.5)))
    I.add(geo, "ash_pale")


def chest_grate(B, I, size):
    """It burns low and even behind a grate."""
    c = Vector((0, -0.105 * I.belly, I.hip + 0.1 * I.tall))
    w, h = 0.12 * size * I.belly, 0.1 * size
    I.add(g.box(c + Vector((0, 0.02, 0)), (w, 0.03, h)), field("core", 3.4))
    bars = None
    for j in range(4):
        bars = g.merge(bars, g.box(c + Vector((-w / 2 + w * (j + 0.5) / 4, 0.0, 0)), (0.012, 0.016, h + 0.012)))
    bars = g.merge(bars, g.box(c + Vector((0, 0.0, h / 2 + 0.006)), (w + 0.03, 0.02, 0.016)), g.box(c + Vector((0, 0.0, -h / 2 - 0.006)), (w + 0.03, 0.02, 0.016)),
                   g.box(c + Vector((w / 2 + 0.008, 0.0, 0)), (0.016, 0.02, h + 0.03)), g.box(c + Vector((-w / 2 - 0.008, 0.0, 0)), (0.016, 0.02, h + 0.03)))
    I.add(bars, "metal_iron", False)


def chest_core(B, I, size):
    """One red point in it."""
    c = Vector((0, -0.118 * I.belly, I.hip + 0.13 * I.tall))
    I.add(g.ico(c, 0.024 * size, sub=1), field("core", 5.0))
    I.add(sk.hoop(c + Vector((0, -0.004, 0)), 0.045 * size, 0.045 * size, 0.005, n=10, u=X, v=Z, sides=3), "ash_dark", False)


def chest_cracks(B, I, size):
    """The red shows through."""
    I.add(_crack_lines(Vector((0, 0, I.zs - 0.08)), 0.122 * I.belly, n=6, seed=2.0, squash=(1.0, 1.0, 1.15)), field("crack", 2.6 * size))


def wears_apron(B, I, size):
    """A leather apron."""
    b = I.belly
    z1, z0 = I.zs - 0.01, I.hip - 0.07 * size
    I.add(g.tongue([Vector((0, -0.075, z1)), Vector((0, -0.128 * b, (z0 + z1) / 2 + 0.03)), Vector((0, -0.12 * b, z0 + 0.03)), Vector((0, -0.1, z0))], [0.1, 0.19 * b, 0.2 * b, 0.17 * b], thick=0.12, normal=-Y), "leather")
    I.add(sk.hoop((0, 0, I.hip + 0.11 * I.tall), 0.12 * b, 0.12 * b, 0.008, n=10, sides=3), "leather_dark", False)
    for s in (1, -1):
        I.add(g.tube([Vector((s * 0.05, -0.08, z1)), I.H(s * 0.05, 0.04, 0.47)], [0.008, 0.008], n=3), "leather_dark", False)


def wears_necklace(B, I, size):
    """A string of small coals hangs from its neck, each on its own link, each still lit."""
    a, b = I.sh(1) + Vector((-0.03, -0.03, 0.03)), I.sh(-1) + Vector((0.03, -0.03, 0.03))
    pts = sk.sag(a + Vector((0, -0.06, 0)), b + Vector((0, -0.06, 0)), 0.3 * size, n=8)
    pts = [p + Vector((0, -0.05 * math.sin(math.pi * i / 8), 0)) for i, p in enumerate(pts)]
    I.add(g.tube(pts, [0.005] * len(pts), n=3), "metal_iron", False)
    coals, lit = None, None
    for i, p in enumerate(pts[1:-1]):
        c = p + Vector((0, -0.008, -0.03))
        coals = g.merge(coals, g.ico(c, 0.026, sub=0, scale=(1.0, 0.85, 1.1), rot=(i, i * 2, 0)))
        lit = g.merge(lit, g.ico(c + Vector((0, -0.016, 0.0)), 0.013, sub=0))
    I.add(coals, "soot", False)
    I.add(lit, field("coal", 3.6))


def wears_bracelet(B, I, size):
    """A chain of small bright links round its wrist, and a length of it reaching for yours."""
    wr = I.hands.get("l", I.sh(1) + Vector((0.06, -0.085, -0.158)))
    I.add(sk.hoop(wr + Vector((0, 0.012, 0)), 0.03, 0.03, 0.008, n=8, u=X, v=Z, sides=3), field("chain", 3.2))
    pts = sk.sag(wr + Vector((0, -0.01, -0.02)), wr + Vector((0.08, -0.3 * size, -0.02)), 0.11, n=6)
    I.add(sk.chain(pts, link=0.016, n=9), field("chain", 2.6))
    I.add(sk.hoop(wr + Vector((0.08, -0.3 * size - 0.035, -0.02)), 0.036, 0.036, 0.007, n=8, u=Y, v=Z, sides=3), field("chain", 3.2))
    # and the mark of it burned on its chest
    c = Vector((0, -0.12 * I.belly, I.hip + 0.13 * I.tall))
    I.add(sk.hoop(c, 0.036, 0.036, 0.006, n=8, u=X, v=Z, sides=3), field("brand", 3.0))
    I.add(g.box(c, (0.008, 0.008, 0.09)), field("brand", 3.0))


def wears_bottle(B, I, size):
    """The bottle it came out of, carried on its back."""
    c = Vector((0, 0.15 * I.belly, I.hip + 0.03))
    k = 0.62 * size
    prof = [(0.05, 0.0), (0.14, 0.03), (0.185, 0.14), (0.17, 0.27), (0.1, 0.36), (0.055, 0.41), (0.05, 0.5), (0.062, 0.52), (0.06, 0.54)]
    I.add(g.lathe([(r * k, z * k) for r, z in prof], n=8, centre=c), "pane", True)
    I.add(g.lathe([(0.05 * k, 0.53 * k), (0.056 * k, 0.57 * k), (0.0, 0.6 * k)], n=6, centre=c), "cord")
    I.add(g.lathe([(0.187 * k, 0.13 * k), (0.19 * k, 0.155 * k)], n=8, centre=c, caps=False), field("glow", 1.6))
    for s in (1, -1):
        I.add(g.tube([c + Vector((s * 0.08, -0.06, 0.2 * k)), I.sh(s) + Vector((0, 0.0, 0.03)), I.sh(s) + Vector((-s * 0.02, -0.06, -0.02))], [0.009] * 3, n=3), "leather", False)


def holds_flame(B, I, size):
    """It holds its own flame overhead like a lamp."""
    wr = I.hands.get("l", Vector((0.16, -0.04, I.zs + 0.27)))
    c = wr + Vector((0, 0.0, 0.03))
    I.add(g.lathe([(0.02, 0.0), (0.06 * size, 0.02), (0.075 * size, 0.07), (0.07 * size, 0.08)], n=7, centre=c), "metal_iron", False)
    I.add(sk.flame(c + Z * 0.05, 0.06 * size, 0.26 * size, n=4, turn=0.2), field("flame", 3.2))
    I.add(sk.flame(c + Z * 0.05, 0.075 * size, 0.2 * size, n=3, turn=1.3), B.under)
    I.add(g.ico(c + Z * 0.09, 0.03 * size, sub=1, scale=(1, 1, 1.4)), field("core", 5.0))


def holds_hammer(B, I, size):
    """A tiny hammer of the same bright metal."""
    wr = I.hands.get("r", Vector((-0.16, -0.1, I.zs)))
    top = wr + Vector((-0.01, -0.02, 0.15 * size))
    I.add(g.tube([wr + Vector((0, 0, -0.03)), top], [0.009, 0.009], n=4), "wood", False)
    I.add(g.box(top, (0.085 * size, 0.04 * size, 0.04 * size)), "tin", False)


def holds_writ(B, I, size):
    """A writ, and a seal that looks untouched until you hold it to the light."""
    wl, wr = I.hands.get("l", Vector((0.1, -0.2, I.zs))), I.hands.get("r", Vector((-0.1, -0.2, I.zs)))
    c = wl + Vector((-0.02, -0.03, 0.02))
    I.add(g.box(c, (0.13 * size, 0.012, 0.17 * size), rot=(0.25, 0, 0.1)), "paper", False)
    I.add(g.ico(c + Vector((0.01, -0.01, -0.05 * size)), 0.024 * size, sub=1, scale=(1, 0.4, 1)), "wax_red")
    I.add(g.tongue([c + Vector((0.01, -0.012, -0.06 * size)), c + Vector((0.02, -0.014, -0.11 * size)), c + Vector((0.01, -0.012, -0.15 * size))], [0.014, 0.014, 0.004], thick=0.3, normal=-Y), "cloth_rag")
    s0 = wr + Vector((0.0, -0.02, 0.0))
    I.add(g.lathe([(0.022, -0.03), (0.02, -0.01), (0.01, 0.0), (0.01, 0.05), (0.02, 0.07), (0.0, 0.08)], n=6, centre=s0), "metal_brass", False)


def holds_snuffers(B, I, size):
    """It trims the letters when they blur."""
    wr = I.hands.get("r", Vector((-0.1, -0.1, I.zs + 0.1)))
    for a in (0.25, -0.25):
        d = Vector((0.3 + a, -0.1, 1.0)).normalized()
        I.add(g.blade(wr, wr + d * 0.13 * size, 0.022, thick=0.006, normal=-Y, belly=0.3), "metal_iron_light", False)
        I.add(sk.hoop(wr - d * 0.03, 0.014, 0.014, 0.004, n=6, u=X, v=Z, sides=3), "metal_iron_light", False)


def holds_coal(B, I, size):
    """It blows on one of them."""
    c = I.H(0, -0.2, 0.48)
    I.add(g.ico(c, 0.03 * size, sub=0, scale=(1.1, 0.9, 0.9)), "soot", False)
    I.add(g.ico(c + Vector((0, 0.012, 0.012)), 0.02 * size, sub=0), field("coal", 4.0))
    I.add(sk.flame(c + Vector((0, -0.01, 0.02)), 0.02, 0.07, n=3, lean=(0, -0.5)), field("flame", 3.0))


def holds_list(B, I, size):
    """The list of who it is waiting for."""
    c = I.sh(-1) + Vector((-0.045, -0.06, -0.1))
    I.add(g.tube([c + Vector((0, -0.07, 0.0)), c + Vector((0, 0.07, 0.0))], [0.024, 0.024], n=6), "paper", False)
    I.add(g.tongue([c + Vector((0, -0.07, -0.02)), c + Vector((0.004, -0.085, -0.09)), c + Vector((0, -0.075, -0.16))], [0.09, 0.09, 0.08], thick=0.06, normal=-Y), "paper", False)
    lines = None
    for i in range(4):
        lines = g.merge(lines, g.box(c + Vector((0, -0.084, -0.05 - 0.028 * i)), (0.06, 0.004, 0.006)))
    I.add(lines, "soot", False)


def rides_blade(B, I, size):
    """It clings along the flat of a blade: a sword stood in the ground at a lean, and the fiend sat on the flat of it."""
    up = Vector((0, 0.643, 0.766))                   # the way the blade runs, point to hilt
    n = Vector((0, -0.766, 0.643))                   # the way its flat looks
    seat = Vector((0, 0.1, I.hip))
    tip, hilt = seat - up * (I.hip / up.z), seat + up * 0.72 * size
    w = 0.34 * size
    run = tip - hilt
    B.add(g.tongue([hilt, hilt + run * 0.3, hilt + run * 0.82, tip], [w * 0.9, w, w * 0.86, 0.02], thick=0.09, normal=n), "metal_iron_light", False)
    B.add(g.tube([hilt + n * 0.016, hilt + run * 0.8 + n * 0.016], [0.012, 0.004], n=3), "metal_dark", False)
    for s in (1, -1):
        B.add(g.tube([hilt + Vector((s * w * 0.45, 0.0, 0.0)), hilt + run * 0.3 + Vector((s * w * 0.5, 0, 0.0)), hilt + run * 0.82 + Vector((s * w * 0.43, 0, 0.0)), tip], [0.006, 0.006, 0.006, 0.002], n=3), field("edge", 2.4))
    R = Matrix(((1, 0, 0), (0, -n.y, up.y), (0, -n.z, up.z)))     # the blade's own axes: across, through, along
    B.add(g.box(hilt + up * 0.012, (0.52 * size, 0.05, 0.045), rot=R), "metal_brass", False)
    B.add(g.tube([hilt + up * 0.03, hilt + up * 0.2], [0.026, 0.022], n=6), "leather_dark", False)
    B.add(g.ico(hilt + up * 0.23, 0.04, sub=1), "metal_brass", True)
    I.frame_top = (hilt + up * 0.27).z                # it is small on it: the blade is the height of the pair


def ground_hill(B, I, size):
    """The highest thing near: a heap of stones under it."""
    stones = None
    for i, (x, y, z, r) in enumerate(((0.0, 0.0, -0.05, 0.17), (0.17, 0.04, -0.12, 0.13), (-0.16, -0.03, -0.13, 0.14), (0.04, 0.17, -0.14, 0.12), (-0.03, -0.17, -0.15, 0.12), (0.25, -0.1, -0.2, 0.09), (-0.26, 0.11, -0.2, 0.1), (0.1, -0.25, -0.21, 0.08))):
        stones = g.merge(stones, g.ico((x * size, y * size, z * size), r * size, sub=0, scale=(1.1, 1.0, 0.75), rot=(i * 0.7, i * 1.3, i)))
    B.add(stones, "stone_hide", False)


def ground_sling(B, I, size):
    """It sits in the pouch of a sling, like a coal waiting to be thrown."""
    c = getattr(I, "c", Vector((0, 0, 0.2)))
    r = getattr(I, "r", 0.17)
    B.add(g.lathe([(0.0, -r - 0.02), (r * 0.75, -r * 0.92), (r * 1.06, -r * 0.4), (r * 1.1, -r * 0.2)], n=8, centre=c), "leather")
    knot = c + Vector((0, 0.34, 0.36)) * size
    cords = None
    for s in (1, -1):
        cords = g.merge(cords, g.tube([c + Vector((s * r * 1.08, 0, -r * 0.25)), c + Vector((s * r * 0.8, 0.16, 0.14)), knot], [0.008, 0.008, 0.008], n=4))
    cords = g.merge(cords, g.tube([knot, knot + Vector((0.03, 0.14, -0.14)), Vector((0.02, c.y + 0.62 * size, 0.01))], [0.008, 0.008, 0.008], n=4), g.ico(knot, 0.02, sub=0))
    B.add(cords, "cord", False)


def ground_fires(B, I, size):
    """It leaves a line of small fires."""
    for i, (y, k) in enumerate(((0.26, 1.0), (0.46, 0.75), (0.63, 0.5))):
        c = Vector((0.04 * (-1) ** i, y * size, 0.0))
        B.add(sk.flame(c, 0.045 * k, 0.16 * k, n=3, turn=i), field("flame", 2.8))
        B.add(sk.flame(c, 0.055 * k, 0.1 * k, n=3, turn=i + 1.0), B.under)
        B.add(sk.disc(c, 0.06 * k, thick=0.008, n=7), "soot")


def _fire_ring(c, R, n, h, w, tilt=0.0):
    c = V(c)
    geo = None
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.cos(a), math.sin(a), 0))
        hh = h * (0.75 + 0.5 * abs(math.sin(i * 1.7)))
        geo = g.merge(geo, g.tongue([c + d * R, c + d * R * 1.03 + Vector((-d.y, d.x, 0)) * w * 0.6 + Z * hh * 0.5, c + d * R + Z * hh], [w, w * 0.9, w * 0.08], thick=0.5, normal=d))
    return sk.tilted(geo, rx=tilt, about=c) if tilt else geo


def ground_ring(B, I, size):
    """A ring of fire turns round it, a little wider each time it has been lit."""
    c = Vector((0, 0, I.hip + 0.03))
    B.add(sk.tilted(sk.hoop(c, 0.4 * size, 0.4 * size, 0.012, n=18, sides=3), rx=0.22, about=c), field("ring", 3.0))
    B.add(_fire_ring(c, 0.4 * size, 16, 0.12, 0.07, tilt=0.22), field("flame", 2.6))
    B.add(sk.tilted(sk.hoop(c + Z * 0.0, 0.27 * size, 0.27 * size, 0.008, n=14, sides=3), rx=-0.3, about=c), field("ring", 2.0))


def ground_ward(B, I, size):
    """A low ring of flame burns round its feet wherever it stops."""
    c = Vector((0, 0, 0.0))
    B.add(sk.hoop(c + Z * 0.012, 0.3 * size, 0.3 * size, 0.012, n=18, sides=3), field("ward", 3.0))
    B.add(_fire_ring(c, 0.3 * size, 18, 0.085, 0.06), field("ward", 2.4))
    B.add(_fire_ring(c, 0.33 * size, 9, 0.05, 0.05), "ice_pale")


def ground_puddle(B, I, size):
    """Meltwater runs from its feet."""
    B.add(sk.disc((0.02, -0.02, 0.0), 0.3 * size, thick=0.01, n=12, squash=0.85), "water")
    B.add(sk.hoop((0.07, -0.02, 0.012), 0.1, 0.09, 0.005, n=10, sides=3), "water_pale", False)
    B.add(sk.hoop((0.07, -0.02, 0.012), 0.19, 0.17, 0.004, n=12, sides=3), "water_pale", False)
    ice = None
    for i, (x, y, h) in enumerate(((0.27, 0.1, 0.12), (-0.25, 0.08, 0.16), (-0.2, -0.2, 0.08), (0.24, -0.16, 0.1))):
        ice = g.merge(ice, sk.crystal((x * size, y * size, 0.0), (x * size * 1.1, y * size * 1.1, h), 0.035, n=4))
    B.add(ice, "ice", False)


def ground_heap(B, I, size):
    """It lies under its own ash."""
    geo = None
    for i, (x, y, r) in enumerate(((0.16, 0.08, 0.1), (-0.17, 0.06, 0.11), (0.02, 0.2, 0.12), (0.2, -0.08, 0.07), (-0.2, -0.1, 0.07))):
        geo = g.merge(geo, g.ico((x * size, y * size, 0.01), r * size, sub=1, scale=(1.2, 1.1, 0.5), rot=(0, 0, i)))
    B.add(geo, "ash")
    B.add(sk.disc((0, 0.02, 0), 0.3 * size, thick=0.012, n=10), "ash_dark")


def ground_sift(B, I, size):
    """What has burned, in a heap in front of it."""
    c = Vector((0, -0.27, 0.0))
    B.add(g.lathe([(0.15 * size, 0.0), (0.1 * size, 0.035), (0.04 * size, 0.07), (0.0, 0.08)], n=9, centre=c), "ash")
    B.add(sk.disc(c, 0.2 * size, thick=0.008, n=10), "ash_dark")
    fl = None
    for i, (x, z) in enumerate(((-0.03, 0.14), (0.02, 0.19), (0.05, 0.12), (-0.05, 0.22))):
        fl = g.merge(fl, g.ico(c + Vector((x, 0.04, z)), 0.01, sub=0))
    B.add(fl, "ash_pale", False)
    B.add(g.ico(c + Vector((0.03, -0.02, 0.055)), 0.014, sub=0), field("coal", 3.0))


def ground_stick(B, I, size):
    """A chamberstick: a saucer with a ring to carry it by."""
    B.add(g.lathe([(0.1, 0.0), (0.24 * size, 0.02), (0.26 * size, 0.06), (0.245 * size, 0.062), (0.22 * size, 0.035), (0.0, 0.03)], n=12), "metal_brass", False)
    B.add(sk.hoop((0.29 * size, 0.0, 0.07), 0.05, 0.05, 0.012, n=10, u=X, v=Z, sides=4), "metal_brass", False)


def ground_quiet(B, I, size):
    B.add(sk.hoop((0, 0, 0.01), 0.3 * size, 0.3 * size, 0.006, n=18, sides=3), "ash_pale", False)
    B.add(sk.hoop((0, 0, 0.01), 0.4 * size, 0.4 * size, 0.004, n=20, sides=3), "ash", False)
    geo = None
    for i, (x, y, r) in enumerate(((0.12, 0.1, 0.07), (-0.13, 0.08, 0.08), (0.0, 0.17, 0.07))):
        geo = g.merge(geo, g.ico((x, y, 0.0), r, sub=1, scale=(1.2, 1.1, 0.4)))
    B.add(geo, "ash")


def ground_anvil(B, I, size):
    """A small anvil, and a thing on it still bright."""
    c = Vector((0.0, -0.26, 0.0))
    B.add(g.merge(g.box(c + Z * 0.03, (0.14, 0.1, 0.06)), g.box(c + Z * 0.09, (0.07, 0.06, 0.07)), g.box(c + Z * 0.15, (0.2, 0.09, 0.05)), g.cone(c + Vector((0.1, 0, 0.15)), c + Vector((0.2, 0, 0.16)), 0.03, n=5)), "metal_iron", False)
    B.add(g.box(c + Vector((-0.02, 0, 0.182)), (0.1, 0.02, 0.012)), field("work", 3.4))


def aura_mane(B, I, size):
    crown_flare(B, I, size)


def aura_smokes(B, I, size):
    """Smoke trails off it in several directions at once, and there are small flames in the smoke."""
    c = Vector((0, 0.02, I.zs))
    for i, (a, up) in enumerate(((0.3, 0.3), (1.5, 0.55), (2.7, 0.3), (4.0, 0.42), (5.3, 0.5))):
        d = Vector((math.cos(a), math.sin(a) * 0.7 + 0.2, 0))
        p0 = c + d * 0.1
        pts = [p0, p0 + d * 0.14 * size + Z * up * 0.25, p0 + d * 0.33 * size + Z * up * 0.4, p0 + d * 0.5 * size + Z * up * 0.75 * size]
        B.add(g.tongue(pts, [0.05, 0.07, 0.06, 0.035], thick=0.4), "smoke")
        t = pts[-1]
        B.add(sk.flame(t + Vector((0, 0, -0.01)), 0.035, 0.11, n=3, turn=i), field("flame", 3.0))
        horns = None
        for s in (1, -1):
            horns = g.merge(horns, g.cone(t + Vector((s * 0.022, -0.01, 0.03)), t + Vector((s * 0.045, -0.01, 0.075)), 0.009, n=4))
        B.add(horns, "horn", False)
        B.add(sk.eye_pair(t + Vector((0, -0.03, 0.02)), 0.014, 0.006, scale=(1.2, 0.5, 0.7), slant=0.3), "void")


def aura_steam(B, I, size):
    """It steams."""
    geo = None
    for i, (x, y, h) in enumerate(((0.21, 0.04, 0.5), (-0.22, 0.0, 0.62), (0.08, 0.22, 0.7))):       # it comes off the wet in puffs, smaller as they go up
        for j in range(3):
            t = (j + 1) / 3.0
            geo = g.merge(geo, sk.puff((x * size + 0.03 * math.sin(i + j * 2.0), y * size, (0.08 + (h - 0.08) * t) * size), 0.06 - 0.012 * j, k=2, seed=i + j))
    B.add(geo, "steam")


def aura_wings(B, I, size):
    """Two ragged wings of flame it can only fall with."""
    c = getattr(I, "c", Vector((0, 0, I.zs)))
    r = getattr(I, "r", 0.12)
    for s in (1, -1):
        root = c + Vector((s * r * 0.75, 0.05, r * 0.5))
        lit, dark = None, None
        for i in range(6):
            a = 0.25 + 0.3 * i
            L = (0.34 + 0.07 * math.sin(i * 2.2) + 0.03 * i) * size
            d = Vector((s * math.cos(a), 0.45, math.sin(a))).normalized()
            tg = g.tongue([root + d * 0.02 * i, root + d * L * 0.5 + Vector((0, 0.03, 0.03)), root + d * L + Vector((0, 0.08, 0.02))], [0.1, 0.085, 0.004], thick=0.25, normal=(0, -1, 0.2))
            if i % 3 == 1:
                dark = g.merge(dark, tg)
            else:
                lit = g.merge(lit, tg)
        I.add(lit, field("wings", 2.6))
        I.add(dark, B.under)
    # white at the heart of it, and its fall behind it
    I.add(g.ico(c + Vector((0, -0.02, 0.0)), r * 0.45, sub=1), "bone")
    trail = None
    for i, (x, L) in enumerate(((0.0, 0.5), (0.07, 0.36), (-0.08, 0.4))):
        b0 = c + Vector((x, 0.1, r * 0.8))
        trail = g.merge(trail, g.tongue([b0, b0 + Vector((x * 0.5, 0.1, L * 0.5)) * size, b0 + Vector((0, 0.16, L)) * size], [0.09, 0.07, 0.004], thick=0.4, normal=(0, -1, 0.3)))
    I.add(trail, field("flame", 2.6))


STYLES = {
    ("crown", "flare"): crown_flare, ("crown", "fuse"): crown_fuse, ("crown", "letters"): crown_letters, ("crown", "thread"): crown_thread,
    ("skin", "ash"): skin_ash, ("skin", "iron"): skin_iron, ("skin", "soot"): skin_soot, ("skin", "still"): skin_still,
    ("chest", "grate"): chest_grate, ("chest", "core"): chest_core, ("chest", "cracks"): chest_cracks,
    ("wears", "apron"): wears_apron, ("wears", "necklace"): wears_necklace, ("wears", "bracelet"): wears_bracelet, ("wears", "bottle"): wears_bottle,
    ("holds", "flame"): holds_flame, ("holds", "hammer"): holds_hammer, ("holds", "writ"): holds_writ, ("holds", "snuffers"): holds_snuffers,
    ("holds", "coal"): holds_coal, ("holds", "list"): holds_list,
    ("rides", "blade"): rides_blade,
    ("ground", "hill"): ground_hill, ("ground", "sling"): ground_sling, ("ground", "fires"): ground_fires, ("ground", "ring"): ground_ring, ("ground", "ward"): ground_ward,
    ("ground", "puddle"): ground_puddle, ("ground", "heap"): ground_heap, ("ground", "sift"): ground_sift, ("ground", "stick"): ground_stick,
    ("ground", "quiet"): ground_quiet, ("ground", "anvil"): ground_anvil,
    ("aura", "mane"): aura_mane, ("aura", "smokes"): aura_smokes, ("aura", "steam"): aura_steam, ("aura", "wings"): aura_wings,
    ("bottle", "bound"): bottle_bound,
}
SLOTS = ("crown", "skin", "chest", "wears", "holds", "rides", "ground", "aura", "bottle")
IMP_ONLY = {"crown", "skin", "chest", "wears", "holds", "rides"}
CAN = {"imp": set(SLOTS) - {"bottle"}, "wick": set(), "ball": {"ground", "aura"}, "bottle": {"bottle", "ground"}, "stove": {"ground"}, "candle": {"ground", "aura"}}


def build(form_id, level, spec, base):
    B = sk.Body(form_id, level, spec, base)
    B.ground = True
    plan = spec.get("plan", "wick" if level <= 1 else "imp")
    I = PLANS[plan](B, spec)
    for slot in SLOTS:
        for style, size in each(spec.get(slot)):
            if slot not in CAN.get(plan, set()):
                continue
            fn = STYLES.get((slot, style))
            if fn is None:
                if not (slot == "crown" and style in ("candle", "bare", "none")):
                    sk.log("no such style", slot, style, "on", form_id)
                continue
            fn(B, I, size)
    if plan == "imp":
        top = I.P(Vector((0, -0.02, I.top + (0.05 if getattr(I, "crown_style", "") in ("candle", "bare", "flare", "letters", "thread") else 0.0)))).z
        top = max(top, getattr(I, "frame_top", 0.0))
        B.frame(top, front=I.P(I.H(0, -0.12, 0.5)).y, mid=I.zs - 0.08, half=0.13 * I.belly)
        B.socket("socket_eyes", I.P(I.H(0, -0.118, 0.564)))
        B.socket("socket_mouth", I.P(I.H(0, -0.118, 0.5)))
        B.socket("socket_head", I.P(Vector((0, -0.02, I.top + 0.05))))
        B.socket("socket_back", I.P(Vector((0, 0.1 * I.belly, I.zs - 0.02))))
        B.socket("socket_tail", I.P(Vector((0, 0.09, I.hip + 0.02))))
        for tag in ("l", "r"):
            if tag in I.hands:
                B.socket("socket_hand_" + tag, I.P(I.hands[tag]))
            if tag in I.feet:
                B.socket("socket_limb_f" + tag, I.feet[tag] + Vector((0, 0.02, 0.03)))
        if "r" in I.hands:
            B.socket("socket_grip", I.P(I.hands["r"] + Vector((0, -0.02, -0.03))))
        if "l" in I.hands:
            B.socket("socket_light", I.P(I.hands["l"] + Vector((0, -0.03, -0.06))))
    I.emit()
    B.export()
