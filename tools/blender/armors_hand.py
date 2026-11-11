"""WILDLINE genius lines, the armors: the Gauntlet (docs/genius-lines.md, "The armors").
lines_armors.py loads this file; what the conventions are, and what `wear` means, is said there.

A gauntlet is a left hand in its own space: the middle of the wrist at the origin, the fingers
along +Z, the back of the hand to -Y (the front), the thumb at +X. A form's `body` says how
broad it is (`bulk`), how its fingers lie (`fingers`), how the whole hand is held (`hold`), what
it is made of (`stuff`), its `cuff`, its `plates`, and what it has `grown` or holds.
"""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z
import genius_kit as kit
from genius_kit import mat, field, mark
from genius_relics import strap, loop, ringtube
from lines_armors import Piece, finish, eye, opt, each, Rx, Ry, Rz, lathe_at

# a left hand's fingers, first to little: where each stands on the knuckles, how long, how thick
FX = (0.046, 0.016, -0.015, -0.045)
FL = (0.118, 0.13, 0.12, 0.094)
FR = (0.0185, 0.019, 0.018, 0.016)
# how the fingers lie: (first, middle, ring, little: 0 straight to 1 closed), the thumb (0 out to 1 folded), the spread
POSES = {
    "rest": ((0.34, 0.4, 0.44, 0.5), 0.3, 0.02), "open": ((0.06, 0.05, 0.08, 0.12), 0.1, 0.07), "flat": ((0.0, 0.0, 0.0, 0.0), 0.35, 0.0),
    "spread": ((0.04, 0.02, 0.04, 0.06), 0.0, 0.16), "fist": ((1.0, 1.0, 1.0, 1.0), 1.0, 0.0), "pinch": ((0.66, 0.26, 0.3, 0.36), 0.8, 0.03),
    "point": ((0.0, 1.0, 1.0, 1.0), 0.95, 0.0), "beckon": ((0.56, 0.95, 1.0, 1.0), 0.85, 0.0), "sign": ((0.0, 0.03, 1.0, 1.0), 0.9, 0.06),
    "grip": ((0.7, 0.72, 0.74, 0.76), 0.6, 0.0), "claw": ((0.44, 0.46, 0.46, 0.5), 0.3, 0.14), "cup": ((0.36, 0.38, 0.4, 0.44), 0.25, 0.05),
    "knock": ((0.86, 1.0, 1.0, 1.0), 1.0, 0.0), "shake": ((0.22, 0.26, 0.3, 0.34), 0.05, 0.02),
}
# how the whole hand is held: turned from standing on its cuff with its back to the front
HOLDS = {
    "up": lambda: Matrix.Identity(4),
    "palm_front": lambda: Rz(180),                  # the palm to the front, a hand held up
    "palm_up": lambda: Rx(90),                      # open, palm up, the fingers ahead
    "palm_down": lambda: Rx(90) @ Rz(180),          # the back up, the fingers ahead: a fist that rides closed, a hand laid flat
    "side": lambda: Ry(-90),                        # the fingers to one side (the wearer's right), the thumb up
    "down": lambda: Rx(180),                        # reaching down
    "reach": lambda: Rx(118),                       # reaching ahead and down, the palm up
}


class Hand(Piece):
    def __init__(self, form_id, spec):
        Piece.__init__(self, form_id)
        self.k = k = float(spec.get("bulk", 1.0))
        self.pw, self.pl, self.pt = 0.13 * k, 0.142 * (0.85 + 0.15 * k), 0.05 * k
        self.fl = float(spec.get("fingers_long", 1.0)) * (0.9 + 0.1 * k)
        hold = spec.get("hold", "up")
        name, extra = (hold[0], hold[1:]) if isinstance(hold, (list, tuple)) else (hold, [])
        M = HOLDS[name]()
        if extra:           # and then leaned: about X, Y, Z, in degrees, in the world
            ex = list(extra) + [0, 0, 0]
            M = Rz(ex[2]) @ Ry(ex[1]) @ Rx(ex[0]) @ M
        self.M = M
        self.Mi = M.inverted().to_3x3()
        self.down = (self.Mi @ Vector((0, 0, -1))).normalized()       # the world's down, in the hand's space
        self.up = -self.down
        self.tips = []
        self.cuff_len = 0.07
        stuff = spec.get("stuff", "leather")
        self.skin, self.under = {
            "leather": (mat("leather"), mat("leather_dark")), "iron": (mat("metal_iron_light"), mat("metal_iron")), "stone": (mat("stone_hide"), mat("stone_plate")),
            "bare": (mat("skin_pale"), mat("wrap_linen")), "dark": (mat("leather_dark"), mat("leather")), "cloth": (mat("cloth_wool"), mat("cloth_dark")),
        }[stuff]

    # --- the hand itself ---------------------------------------------------------------
    def finger_points(self, i, curl, splay, long=1.0):
        x0 = FX[i] * self.pw / 0.13
        L = FL[i] * self.fl * long
        r = FR[i] * self.k
        sx = splay * (FX[i] / 0.045)
        p = Vector((x0, 0.0, self.pl))
        pts, th, ths = [p], 0.0, []
        for seg, frac in enumerate((0.44, 0.31, 0.25)):
            th += (1.25, 1.5, 1.05)[seg] * curl
            p = p + Vector((sx, math.sin(th), math.cos(th))).normalized() * (L * frac)
            pts.append(p)
            ths.append(th)
        return pts, [r, r * 0.95, r * 0.86, r * 0.62], ths

    def fingers(self, pose, long_first=1.0, plated=None):
        self.pose = POSES[pose] if isinstance(pose, str) else pose
        curls, thumb, splay = self.pose
        for i in range(4):
            pts, radii, ths = self.finger_points(i, curls[i], splay, long_first if i == 0 else 1.0)
            self.round(g.tube(pts, radii, n=6), self.skin)
            self.tips.append((pts[-1], (pts[-1] - pts[-2]).normalized(), radii[-1]))
            if plated is not None:           # a lame over the back of each joint
                for seg in range(3):
                    a, b = pts[seg], pts[seg + 1]
                    th = ths[seg]
                    back = Vector((0, -math.cos(th), math.sin(th)))
                    self.add(g.box((a + b) / 2 + back * radii[seg] * 0.9, (radii[seg] * 2.3, 0.012 * self.k, (b - a).length * 0.82), rot=(-th, 0, 0)), plated)
        # the thumb: out to the side, or folded across
        k = self.k
        base = Vector((self.pw * 0.44, 0.012 * k, 0.045 * k))
        out_m, out_t = base + Vector((0.05, 0.0, 0.035)) * k, base + Vector((0.088, -0.006, 0.088)) * k
        fold_m, fold_t = base + Vector((0.034, 0.04, 0.05)) * k, base + Vector((-0.03, 0.066, 0.086)) * k
        tp = [base, out_m.lerp(fold_m, thumb), out_t.lerp(fold_t, thumb)]
        self.round(g.tube(tp, [0.024 * k, 0.021 * k, 0.014 * k], n=6), self.skin)
        self.round(g.ico(base + Vector((-0.012, 0.004, 0.01)) * k, 0.03 * k, sub=1, scale=(1.0, 0.8, 1.2)), self.skin)
        self.thumb_tip = (tp[-1], (tp[-1] - tp[-2]).normalized(), 0.014 * k)
        if plated is not None:
            self.add(g.box((tp[0] + tp[1]) / 2 + Vector((0.006, -0.02 * k, 0)), (0.05 * k, 0.012 * k, 0.045 * k), rot=(0, math.radians(-40), 0)), plated)

    def palm(self):
        k, pw, pl, pt = self.k, self.pw, self.pl, self.pt
        rings = [g.ring((0, 0, z), rx, ry, n=8, u=X, v=Y, phase=math.pi / 8) for z, rx, ry in ((0.0, 0.05 * k, 0.038 * k), (0.34 * pl, pw * 0.47, pt * 0.52), (0.76 * pl, pw * 0.5, pt * 0.5), (pl + 0.004, pw * 0.49, pt * 0.42))]
        self.round(g.loft(rings), self.skin)
        # the wrist: a strap and its buckle, and the pulse that has been there since it was a glove
        self.add(strap(loop((0, 0, 0.018 * k), 0.056 * k, 0.043 * k, n=12), 0.024 * k, 0.008, closed=True), mat("leather_dark"))
        self.add(g.box((0.014 * k, -0.047 * k, 0.018 * k), (0.03 * k, 0.012, 0.03 * k)), mat("metal_brass"))
        self.round(ringtube((0, 0, 0.04 * k), 0.058 * k, 0.045 * k, 0.0055 * k, n=12), field("pulse", 1.9))
        # stitching down the back of the hand: its partner may show it pale
        st = None
        for x in (-0.034, 0.0, 0.034):
            st = g.merge(st, g.tube([(x * k, -pt * 0.5 - 0.004, pl * 0.92), (x * k * 0.8, -pt * 0.52 - 0.004, pl * 0.55), (x * k * 0.6, -pt * 0.5 - 0.002, pl * 0.22)], [0.0036 * k] * 3, n=3))
        self.round(st, mark("stitch", mat("leather")))

    def cuff(self, style, L):
        k = self.k
        self.cuff_len = L
        lea, dark, brass, iron = mat("leather"), mat("leather_dark"), mat("metal_brass"), mat("metal_iron")
        r0x, r0y = 0.055 * k, 0.043 * k

        def ringz(z, f):
            return g.ring((0, 0, z), r0x * f, r0y * f, n=10, u=X, v=Y, phase=math.pi / 10)
        if style == "glove":           # a short soft cuff, turned back
            self.round(g.loft([ringz(0.006, 1.0), ringz(-L * 0.5, 1.22), ringz(-L, 1.36)]), mark("cuff", dark))
            self.round(g.ico((0, 0, -L - 0.002), r0x * 1.26, sub=1, scale=(1.0, 0.78, 0.08)), mat("void"))
        elif style in ("flare", "sleeve"):       # a gauntlet's cuff, stiff and flared; or an old soft sleeve
            m = lea if style == "flare" else mat("cloth_wool")
            self.round(g.loft([ringz(0.006, 1.02), ringz(-L * 0.35, 1.3), ringz(-L, 1.85)]), m)
            self.round(g.loft([ringz(-L + 0.012, 1.9), ringz(-L - 0.012, 1.95)], caps=False), mark("cuff", dark))
            self.round(g.ico((0, 0, -L - 0.004), r0x * 1.8, sub=1, scale=(1.0, 0.78, 0.06)), mat("void"))
            if style == "flare":
                self.round(ringtube((0, 0, -L * 0.36), r0x * 1.33, r0y * 1.33, 0.006 * k, n=12), brass)
        elif style in ("plate", "arm"):          # lames of iron; or a whole forearm of them, to the elbow
            n = 3 if style == "plate" else 5
            for i in range(n):
                z0, z1 = -L * i / n, -L * (i + 1) / n
                f0, f1 = 1.12 + 0.5 * i / n, 1.3 + 0.5 * (i + 1) / n
                self.add(g.loft([ringz(z0 + 0.012, f0), ringz(z1, f1)]), mat("metal_iron_light") if i % 2 == 0 else iron)
            self.round(ringtube((0, 0, -L), r0x * (1.3 + 0.5), r0y * (1.3 + 0.5), 0.007 * k, n=12), brass)
            self.round(g.ico((0, 0, -L - 0.004), r0x * 1.7, sub=1, scale=(1.0, 0.78, 0.06)), mat("void"))
            if style == "arm":         # the elbow's cap
                self.round(g.ico((0, r0y * 2.2, -L + 0.03), 0.06 * k, sub=1, scale=(1.0, 0.7, 1.2)), mat("metal_iron_light"))
        elif style == "wrap":          # linen wound round the wrist and up the arm, the ends loose
            for i in range(int(L / (0.03 * k)) + 1):
                z = -0.03 * k * i
                self.round(ringtube((0, 0, z + 0.006 * (i % 2)), r0x * (1.04 + 0.012 * i), r0y * (1.04 + 0.012 * i), 0.014 * k, n=10), mat("wrap_linen"))
            self.round(g.ico((0, 0, -L - 0.01), r0x * 1.1, sub=1, scale=(1.0, 0.78, 0.08)), mat("void"))
            for sgn, ln in ((1, 0.11), (-1, 0.07)):
                b0 = Vector((sgn * r0x * 0.9, 0.03 * k, -L * 0.7))
                tail = [b0, b0 + Vector((sgn * 0.025, 0.03, 0.0)) * k + self.down * 0.02 * k, b0 + Vector((sgn * 0.04, 0.05, 0.0)) * k + self.down * ln * 0.55 * k, b0 + Vector((sgn * 0.03, 0.07, 0)) * k + self.down * ln * k]
                self.add(strap(tail, 0.028 * k, 0.005, up=X), mat("wrap_linen"))
        elif style == "stone":         # gone to stone to the wrist, and banded where the stone stops
            self.add(g.loft([ringz(0.01, 1.16), ringz(-L * 0.5, 1.3), ringz(-L, 1.24)]), mat("stone_plate"))
            self.round(ringtube((0, 0, -L), r0x * 1.28, r0y * 1.28, 0.012 * k, n=12), iron)
            self.round(g.ico((0, 0, -L - 0.006), r0x * 1.18, sub=1, scale=(1.0, 0.78, 0.06)), mat("void"))
        else:
            raise ValueError("no such cuff: " + str(style))

    def plates(self, style, size=1.0):
        k, pw, pl, pt = self.k, self.pw, self.pl, self.pt
        iron, light, brass = mat("metal_iron"), mat("metal_iron_light"), mat("metal_brass")
        if style == "back":            # plates across the back of the hand
            for i, fz in enumerate((0.9, 0.66, 0.42, 0.2)):
                self.add(g.box((0, -pt * 0.5 - 0.008 - 0.003 * (i % 2), pl * fz), (pw * (1.04 - 0.06 * i), 0.014 * k, pl * 0.27), rot=(math.radians(7), 0, 0)), light if i % 2 == 0 else iron)
        elif style == "knuckles":      # a ridge over the knuckles
            for i in range(4):
                self.round(g.ico((FX[i] * pw / 0.13, -pt * 0.3, pl + 0.004), 0.021 * k * size, sub=1, scale=(1.0, 1.0, 0.8)), light)
        elif style == "bar":           # a bar of brass across the knuckles, dented in four places
            self.add(g.box((0, -pt * 0.1, pl + 0.012 * k), (pw * 1.14, pt * 1.3, 0.04 * k * size)), brass)
            for i in range(4):
                self.round(g.ico((FX[i] * pw / 0.13, -pt * 0.1 - pt * 0.62, pl + 0.012 * k), 0.012 * k, sub=0, scale=(1.0, 0.4, 1.0)), mat("metal_dark"))
                self.round(g.ico((FX[i] * pw / 0.13, -pt * 0.1, pl + 0.034 * k * size), 0.016 * k, sub=0, scale=(1.0, 1.0, 0.6)), brass)
        elif style == "palm":          # the palm gone to dark iron
            self.round(g.ico((0, pt * 0.5 + 0.004, pl * 0.52), pw * 0.47 * size, sub=1, scale=(1.0, 0.16, 1.12)), mat("metal_dark"))
            self.round(ringtube((0, pt * 0.5 + 0.012, pl * 0.52), pw * 0.4 * size, pw * 0.44 * size, 0.006 * k, n=12, u=X, v=Z), iron)
            self.round(g.ico((0, pt * 0.5 + 0.02, pl * 0.52), pw * 0.12 * size, sub=1, scale=(1.0, 0.4, 1.0)), light)
            if size > 1.2:             # a second ring, where it has been struck most
                self.round(ringtube((0, pt * 0.5 + 0.016, pl * 0.52), pw * 0.22 * size, pw * 0.24 * size, 0.005 * k, n=12, u=X, v=Z), light)
        elif style == "pad":           # a broad padded palm, to catch with
            self.round(g.ico((0, pt * 0.5 + 0.004, pl * 0.5), pw * 0.46 * size, sub=1, scale=(1.0, 0.24, 1.1)), mat("leather_dark"))
            for i in range(4):
                self.round(g.ico((FX[i] * pw / 0.13, pt * 0.42, pl * 0.96), 0.02 * k, sub=0, scale=(1.0, 0.5, 1.0)), mat("leather_dark"))
        else:
            raise ValueError("no such plates: " + str(style))

    def grip_centre(self):
        return Vector((0.0, self.pt * 0.5 + 0.034 * self.k, self.pl * 0.86))


def grow(Hn, style, size, spec):
    k, pw, pl, pt = Hn.k, Hn.pw, Hn.pl, Hn.pt
    iron, light, brass, dark = mat("metal_iron"), mat("metal_iron_light"), mat("metal_brass"), mat("leather_dark")
    L = Hn.cuff_len
    dn, up = Hn.down, Hn.up
    gc = Hn.grip_centre()
    curls = Hn.pose[0]
    if style == "loupe":           # a jeweller's glass on a stalk at the wrist
        b0 = Vector((-0.05 * k, -0.03 * k, 0.0))
        p1, p2 = b0 + Vector((-0.05, -0.05, 0.07)) * k * size, b0 + Vector((-0.02, -0.1, 0.17)) * k * size
        Hn.round(g.tube([b0, p1, p2], [0.007 * k, 0.006 * k, 0.006 * k], n=5), brass)
        ax = Vector((0.3, -1.0, 0.1)).normalized()
        Hn.round(lathe_at([(0.036 * k * size, 0.0), (0.04 * k * size, 0.012 * k), (0.03 * k * size, 0.03 * k), (0.03 * k * size, 0.0)], p2, ax, n=8), brass)
        Hn.round(g.ico(p2 + ax * 0.012 * k, 0.03 * k * size, sub=1, scale=(1.0, 0.35, 1.0)), field("glass", 1.6))
    elif style == "tools":         # what it keeps in the cuff's loops
        for i, (x, ln, m) in enumerate(((0.05, 0.09, iron), (0.02, 0.12, mat("wood")), (-0.035, 0.1, light))):
            b0 = Vector((x * k * 1.4, -0.062 * k, -L * 0.3))
            Hn.round(g.tube([b0 + Vector((0, 0, -0.04 * k)), b0 + Vector((0, -0.004, ln * k))], [0.008 * k, 0.007 * k], n=5), m)
            if i == 0:
                Hn.add(g.box(b0 + Vector((0, -0.004, ln * k + 0.012 * k)), (0.034 * k, 0.012, 0.022 * k)), iron)
        Hn.add(strap([Vector((0.075 * k, -0.045 * k, -L * 0.34)), Vector((0.0, -0.072 * k, -L * 0.34)), Vector((-0.075 * k, -0.045 * k, -L * 0.34))], 0.02 * k, 0.006, up=Z), dark)
    elif style == "gears":         # small gears turn at the knuckles when it flexes
        for i in range(4):
            c = Vector((FX[i] * pw / 0.13, -pt * 0.5 - 0.006, pl * 0.98))
            r = (0.02 + 0.004 * (i % 2)) * k * size
            Hn.add(lathe_at([(r, 0.0), (r, 0.012 * k), (r * 0.4, 0.014 * k)], c, -Y, n=8), brass)
            for t in range(6):
                a = 2 * math.pi * t / 6 + i
                Hn.add(g.box(c + Vector((math.cos(a) * r * 1.1, -0.006 * k, math.sin(a) * r * 1.1)), (0.008 * k, 0.01 * k, 0.008 * k), rot=(0, -a, 0)), brass)
            Hn.round(g.ico(c + Vector((0, -0.014 * k, 0)), 0.006 * k, sub=0), iron)
    elif style == "wrench":        # a spanner in its grip
        ax = Vector((1, 0, 0))
        a, b = gc - ax * 0.13 * k * size, gc + ax * 0.15 * k * size
        Hn.add(g.box((a + b) / 2, ((b - a).length, 0.014 * k, 0.03 * k)), light)
        Hn.add(g.box(b + Vector((0.02 * k, 0, 0)), (0.05 * k, 0.016 * k, 0.075 * k)), light)                 # the open jaw, at the thumb's side
        Hn.add(g.box(b + Vector((0.034 * k, 0, 0)), (0.034 * k, 0.02 * k, 0.03 * k)), mat("soot"))
        Hn.round(ringtube(a - ax * 0.026 * k, 0.03 * k, 0.03 * k, 0.011 * k, n=8, u=X, v=Z), light)          # and the ring end
    elif style == "pulse_palm":    # a pulse in the palm, in time with the line
        c = Vector((0, pt * 0.5 + 0.006, pl * 0.5))
        Hn.round(g.ico(c, pw * 0.2 * size, sub=1, scale=(1.0, 0.25, 1.0)), field("pulse", 2.6))
        for r in (0.3, 0.42):
            Hn.round(ringtube(c + Vector((0, 0.004, 0)), pw * r * size, pw * r * size, 0.004 * k, n=12, u=X, v=Z), field("pulse", 1.4))
    elif style == "wire":          # a coil of line-wire at the cuff, and the glass it is tied off to
        for i in range(5):
            Hn.round(ringtube((0, 0, -L * (0.3 + 0.1 * i)), 0.055 * k * (1.4 + 0.1 * i), 0.043 * k * (1.4 + 0.1 * i), 0.006 * k, n=12), mat("metal_copper"))
        for sgn in (1, -1):
            c = Vector((sgn * 0.085 * k, 0, -L * 0.92))
            Hn.round(lathe_at([(0.012 * k, 0.0), (0.026 * k, 0.012 * k), (0.016 * k, 0.03 * k), (0.026 * k, 0.045 * k), (0.008 * k, 0.06 * k)], c, Vector((sgn, 0, 0)), n=7), mat("glass"))
    elif style == "wheels":        # small wheels at the heel of the hand
        for sgn in (1, -1):
            c = Vector((sgn * 0.035 * k, pt * 0.5 + 0.02 * k, 0.012 * k))
            Hn.round(lathe_at([(0.03 * k * size, -0.008 * k), (0.03 * k * size, 0.008 * k)], c, X, n=10), iron)
            Hn.round(g.ico(c, 0.01 * k, sub=0), brass)
        Hn.add(g.box((0, pt * 0.5 + 0.02 * k, 0.012 * k), (0.1 * k, 0.008 * k, 0.008 * k)), iron)
    elif style == "lever":         # a points lever, in its grip: its foot below, its knob above
        a, b = gc + dn * 0.42 * size, gc - dn * 0.36 * size
        Hn.round(g.tube([a, gc, b], [0.018 * k, 0.015 * k, 0.012 * k], n=6), iron)
        Hn.round(g.ico(b, 0.034 * k, sub=1), brass)
        u_, v_ = g._frame(dn)
        Hn.add(g.loft([[a + (u_ * cx + v_ * cy) * 0.09 * k - dn * 0.05 * k for cx, cy in ((1, 1), (-1, 1), (-1, -1), (1, -1))], [a + (u_ * cx + v_ * cy) * 0.13 * k for cx, cy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]]), mat("metal_dark"))
    elif style == "worn_tips":     # fingertips worn through, and something older than leather showing under
        for tip, d, r in Hn.tips + [Hn.thumb_tip]:
            Hn.round(g.tube([tip - d * 0.022 * k, tip - d * 0.004], [r * 1.3, r * 1.22], n=6), mat("bone"))
            Hn.round(g.ico(tip - d * 0.004, r * 1.22, sub=1), mat("bone"))
            if size > 0.5:             # and what is under the bone: a claw; a careful hand keeps its own short
                Hn.round(g.cone(tip, tip + d * 0.03 * k * size + Vector((0, 0.01 * k, 0)), r * 0.8, n=5), mat("talon"))
    elif style == "rope":          # a coil of rope and a hook, for going down into ruins
        for i in range(4):
            Hn.round(ringtube((0, 0, -L * (0.45 + 0.12 * i)), 0.055 * k * (1.5 + 0.1 * i), 0.043 * k * (1.5 + 0.1 * i), 0.01 * k, n=10), mat("rope"))
        b0 = Vector((0.07 * k, -0.05 * k, -L * 0.9))
        Hn.round(g.tube([b0, b0 + dn * 0.06 * k, b0 + dn * 0.1 * k + Vector((0.03 * k, 0, 0)), b0 + dn * 0.07 * k + Vector((0.055 * k, 0, 0))], [0.008 * k, 0.008 * k, 0.007 * k, 0.003 * k], n=5), iron)
    elif style == "phial":         # something a thousand years old, lifted out whole
        c = Vector((0.0, pt * 0.5 + 0.075 * k * size, pl * 0.72))
        Hn.round(lathe_at([(0.0, -0.05 * k), (0.045 * k * size, -0.035 * k), (0.058 * k * size, 0.0), (0.04 * k * size, 0.04 * k), (0.016 * k, 0.06 * k), (0.02 * k, 0.085 * k), (0.0, 0.086 * k)], c, Vector((0, 1, 0)), n=8), mat("glass"))
        Hn.round(g.ico(c, 0.03 * k * size, sub=1), field("old", 2.4))
        Hn.round(g.ico((0, pt * 0.5 + 0.006, pl * 0.5), pw * 0.4, sub=1, scale=(1.0, 0.2, 1.0)), mat("cloth_wool"))
    elif style == "lamp":          # a small lamp on the knuckle of the first finger
        c = Vector((FX[0] * pw / 0.13, -pt * 0.5 - 0.014 * k, pl + 0.01 * k))
        r = 0.03 * k * size
        Hn.round(lathe_at([(r * 0.5, 0.0), (r, 0.006 * k), (r, 0.016 * k), (r * 0.5, 0.02 * k)], c, -Y, n=6), brass)
        Hn.round(g.ico(c - Y * (0.018 * k + r * 0.9), r * 1.05, sub=1), field("lamp", 3.6))
        Hn.round(lathe_at([(r * 0.72, 0.0), (r * 0.25, 0.012 * k)], c - Y * (0.018 * k + r * 1.8), -Y, n=6), brass)
    elif style == "keys":          # a ring of keys at the wrist
        b0 = Vector((-0.058 * k, -0.02 * k, 0.0))
        Hn.round(ringtube(b0 + dn * 0.03 * k, 0.03 * k, 0.03 * k, 0.004 * k, n=10, u=X, v=dn), iron)
        for i in range(3):
            a = b0 + dn * 0.058 * k + Vector(((i - 1) * 0.018 * k, 0, 0))
            Hn.round(g.tube([a, a + dn * 0.08 * k], [0.005 * k, 0.005 * k], n=4), brass if i % 2 else iron)
            Hn.round(g.ico(a + dn * 0.085 * k + Vector((0.008 * k, 0, 0)), 0.011 * k, sub=0, scale=(1.4, 0.5, 1.0)), brass if i % 2 else iron)
    elif style == "ring_wrist":    # a ring of light round the wrist that brightens when it presses down
        Hn.round(ringtube((0, 0, -0.02 * k), 0.12 * k * size, 0.1 * k * size, 0.009 * k, n=16), field("ward", 2.6))
        Hn.round(ringtube((0, 0, -0.05 * k), 0.15 * k * size, 0.13 * k * size, 0.004 * k, n=16), field("ward", 1.4))
    elif style == "seams":         # stone, grey and seamed
        st = None
        for (a, b) in (((-0.06, 0.2), (0.05, 0.5)), ((0.04, 0.5), (-0.02, 0.9)), ((-0.05, 0.62), (-0.062, 1.0))):
            st = g.merge(st, g.tube([Vector((a[0] * k, -pt * 0.5 - 0.004, a[1] * pl)), Vector((b[0] * k, -pt * 0.5 - 0.004, b[1] * pl))], [0.005 * k, 0.003 * k], n=3))
        Hn.round(st, mat("stone_light"))
        # the stone it is setting, under its knuckles, and the light pressed out round the fist
        zs = pl + 0.02 + 0.02 * k
        Hn.add(g.box((0, 0.022 * k, zs + 0.026 * k), (pw * 1.7 * size, pt * 3.7 * size, 0.052 * k)), mat("stone_plate"))
        Hn.add(g.box((0, 0.022 * k, zs + 0.058 * k), (pw * 1.5 * size, pt * 3.2 * size, 0.012 * k)), mat("stone_hide"))
        Hn.round(ringtube((0, 0.022 * k, zs - 0.004 * k), pw * 0.7 * size, pt * 1.55 * size, 0.007 * k, n=14), field("ward", 2.2))
    elif style == "sixth":         # a finger it does not share with its partner, tipped like a brush
        base = Vector((pw * 0.5, -0.004, pl * 0.72))
        d = Vector((0.5, -0.05, 0.86)).normalized()
        p1, p2 = base + d * 0.06 * k, base + d * 0.11 * k * size
        Hn.round(g.tube([base, p1, p2], [0.017 * k, 0.015 * k, 0.012 * k], n=6), Hn.skin)
        Hn.round(g.tube([p2 - d * 0.004, p2 + d * 0.016 * k], [0.013 * k, 0.013 * k], n=6), brass)
        Hn.round(g.cone(p2 + d * 0.014 * k, p2 + d * 0.075 * k * size, 0.014 * k, n=6), field("brush", 2.8))
    elif style == "ember_heel":    # the fist glows at the heel like iron just out of the fire
        c = Vector((-pw * 0.5, pt * 0.2, pl * 0.5))
        Hn.round(g.ico(c, 0.05 * k * size, sub=1, scale=(0.5, 1.0, 1.4)), field("ember", 3.0))
        for i in range(3):
            b0 = c + Vector((-0.01 * k, (i - 1) * 0.02 * k, 0.0))
            Hn.add(g.blade(b0, b0 + up * (0.07 + 0.03 * i) * k + Vector((-0.03 * k, 0, 0)), 0.03 * k, normal=Y), field("ember", 2.0))
    elif style == "face_plate":    # a hammer's face on the heel of the fist, and its peen on the other side
        Hn.add(g.box((-pw * 0.5 - 0.03 * k * size, pt * 0.3, pl * 0.55), (0.07 * k * size, pt * 2.5, pl * 1.25)), mat("metal_dark"))
        Hn.add(g.box((-pw * 0.5 - 0.068 * k * size, pt * 0.3, pl * 0.55), (0.012 * k, pt * 2.2, pl * 1.1)), mat("metal_iron_light"))
        Hn.add(g.box((pw * 0.5 + 0.022 * k * size, pt * 0.3, pl * 0.55), (0.05 * k * size, pt * 1.9, pl * 0.9)), mat("metal_dark"))
        Hn.add(g.box((0, pt * 0.3, pl * 1.2), (pw * 1.2, pt * 2.3, 0.03 * k)), mat("metal_iron"))
    elif style == "split":         # split knuckles that have healed pale, and the palm bound
        for i in range(4):
            Hn.round(g.ico((FX[i] * pw / 0.13, -pt * 0.34, pl + 0.006), 0.014 * k * size, sub=0, scale=(1.3, 1.0, 0.5)), mat("scar_pale"))
        for i in range(3):
            Hn.round(ringtube((0, 0, pl * (0.3 + 0.2 * i)), pw * 0.52, pt * 0.58, 0.012 * k, n=10), mat("wrap_linen"))
    elif style == "scars":         # fine scars across the palm, all in one direction
        sc = None
        for i in range(5):
            z = pl * (0.2 + 0.15 * i)
            sc = g.merge(sc, g.tube([Vector((-pw * 0.4, pt * 0.5 + 0.004, z)), Vector((pw * 0.36, pt * 0.5 + 0.004, z + 0.02 * k))], [0.003 * k, 0.003 * k], n=3))
        Hn.round(sc, mat("scar_pale"))
    elif style == "shard":         # the sharp end of the problem, held
        ax = Vector((1.0, 0.0, 0.34)).normalized()
        a, b = gc - ax * 0.2 * size, gc + ax * 0.34 * size
        n = Vector((0, 1, 0))
        side = ax.cross(n).normalized()
        Hn.add(g.tongue([a, (a + b) / 2, b, b + ax * 0.07 * k], [0.07 * k, 0.075 * k, 0.06 * k, 0.004], thick=0.16, normal=n), mat("steel_polish"))
        Hn.add(g.tongue([a + side * 0.03 * k, (a + b) / 2 + side * 0.034 * k, b + side * 0.026 * k], [0.012 * k, 0.012 * k, 0.008 * k], thick=0.5, normal=n), mat("steel_glint"))
    elif style == "chain":         # a length of chain from the wrist, wrapped twice round the forearm
        geo = None
        turns, n = 2.0, 18
        for i in range(n + 1):
            t = i / n
            a = 2 * math.pi * turns * t
            z = -L * (0.12 + 0.7 * t)
            f = 1.34 + 0.4 * (0.12 + 0.7 * t)
            c = Vector((0.055 * k * f * math.cos(a), 0.043 * k * f * math.sin(a), z))
            geo = g.merge(geo, g.ico(c, 0.014 * k * size, sub=0, scale=(1.0, 0.6, 1.4) if i % 2 else (0.6, 1.0, 1.4)))
        p = Vector((0.055 * k * 1.7, 0.0, -L * 0.82))
        for i in range(5):
            p = p + dn * 0.03 * k
            geo = g.merge(geo, g.ico(p, 0.014 * k * size, sub=0, scale=(1.0, 0.6, 1.4) if i % 2 else (0.6, 1.0, 1.4)))
        Hn.round(geo, iron)
        Hn.round(g.tube([p + dn * 0.02 * k, p + dn * 0.07 * k, p + dn * 0.1 * k + Vector((0.03 * k, 0, 0)), p + dn * 0.07 * k + Vector((0.055 * k, 0, 0))], [0.008 * k, 0.008 * k, 0.007 * k, 0.003 * k], n=5), light)
    elif style == "roots":         # roots of light from each fingertip when it grips
        f = field("roots", 2.4)
        for j, (tip, d, r) in enumerate(Hn.tips + [Hn.thumb_tip]):
            for b in range(2):
                side = Vector((math.sin(j * 2.0 + b * 3.0), math.cos(j * 1.3 + b * 2.0), 0)) * 0.05 * k
                pts = [tip, tip + d * 0.03 * k + dn * 0.03 * k * size, tip + d * 0.03 * k + dn * (0.09 + 0.03 * b) * k * size + side, tip + dn * (0.16 + 0.04 * ((j + b) % 3)) * k * size + side * 2.2]
                Hn.round(g.tube(pts, [r * 0.7, r * 0.5, r * 0.32, 0.002], n=4), f)
    elif style == "nails":         # blunt curved nails
        for tip, d, r in Hn.tips + [Hn.thumb_tip]:
            Hn.round(g.tube([tip - d * 0.01, tip + d * 0.02 * k * size, tip + d * 0.034 * k * size + Vector((0, 0.016 * k, 0))], [r * 1.02, r * 0.9, r * 0.36], n=5), mat("horn_ridge"))
    elif style == "tuft":          # the scruff it has hold of
        for i in range(7):
            a = i * 0.9
            b0 = gc + Vector((math.cos(a) * 0.03 * k, 0.0, math.sin(a) * 0.02 * k))
            Hn.add(g.blade(b0, b0 + Vector((math.cos(a) * 0.06, 0.1 + 0.03 * (i % 3), math.sin(a) * 0.05)) * k * size, 0.05 * k, normal=Vector((math.sin(a), 0.2, math.cos(a)))), mat("pelt_dark") if i % 2 else mat("pelt_light"))
    elif style == "glow":          # a light it carries in its palm
        c = Vector((0, pt * 0.5 + 0.035 * k * size, pl * 0.55))
        Hn.round(g.ico(c, 0.032 * k * size, sub=1), field("palm", 3.2))
        Hn.round(g.ico((0, pt * 0.5 + 0.004, pl * 0.52), pw * 0.3, sub=1, scale=(1.0, 0.16, 1.0)), field("palm", 1.2))
    elif style == "eye_back":      # an eye in the back of the hand, half-lidded
        Hn.add_items(eye(Vector((0, -pt * 0.5 - 0.002, pl * 0.52)), 0.03 * k * size, facing=(0, -1, 0), lids=Hn.skin))
        Hn.round(g.ico(Vector((0, -pt * 0.5 - 0.012, pl * 0.52 + 0.018 * k * size)), 0.03 * k * size, sub=1, scale=(1.2, 0.5, 0.55)), Hn.skin)
    elif style == "worn_palm":     # a palm worn smooth by other people's hands
        Hn.round(g.ico((0, pt * 0.5 + 0.003, pl * 0.5), pw * 0.42 * size, sub=1, scale=(1.0, 0.16, 1.12)), mat("skin_pale"))
        for i in range(4):
            Hn.round(g.ico((FX[i] * pw / 0.13, pt * 0.4, pl * 0.98), 0.016 * k, sub=0, scale=(1.0, 0.5, 1.0)), mat("skin_pale"))
    elif style == "loop":          # a loop of cord at the wrist, to be hauled up by
        b0 = Vector((0, 0.05 * k, -0.01 * k))
        Hn.round(ringtube(b0 + Vector((0, 0.05 * k, 0)) + dn * 0.02 * k, 0.05 * k * size, 0.07 * k * size, 0.006 * k, n=12, u=Y, v=dn), mat("cord"))
    elif style == "warm":          # it is warm: you can feel it from a pace away
        c = Vector((0, pt * 0.5 + 0.012, pl * 0.5))
        Hn.round(g.ico(c, pw * 0.36 * size, sub=1, scale=(1.0, 0.2, 1.1)), field("ember", 2.4))
        for i in range(4):
            b0 = Vector(((i - 1.5) * 0.04 * k, -pt * 0.5 - 0.004, pl * (0.3 + 0.2 * (i % 2))))
            pts = [b0, b0 + up * 0.05 * k + Vector((0.01 * k, 0, 0)), b0 + up * 0.11 * k * size + Vector((-0.012 * k, 0, 0)), b0 + up * 0.17 * k * size]
            Hn.add(g.tongue(pts, [0.02 * k, 0.018 * k, 0.012 * k, 0.002], thick=0.4, normal=Vector((0, -1, 0))), field("ember", 1.2))
    elif style == "bands":         # a band on every finger: it has a sign for each thing
        for i in range(4):
            pts, radii, ths = Hn.finger_points(i, curls[i], 0.0)
            c = (pts[0] + pts[1]) / 2
            u_, v_ = g._frame((pts[1] - pts[0]).normalized())
            Hn.round(ringtube(c, radii[0] * 1.12, radii[0] * 1.12, 0.004 * k, n=8, u=u_, v=v_), brass if i % 2 else field("sign", 2.0))
    elif style == "tassels":       # ribbons at the cuff, that move when it signs
        for i, sgn in enumerate((1, -1, 1)):
            b0 = Vector((sgn * 0.07 * k * (1.0 - 0.4 * (i // 2)), 0.02 * k * (i - 1), -L * 0.85))
            Hn.add(strap([b0, b0 + dn * 0.035 * k + Vector((sgn * 0.016 * k, 0, 0)), b0 + dn * 0.08 * k * size + Vector((sgn * 0.04 * k, 0.01, 0))], 0.026 * k, 0.005, up=Y), mat("cloth_lining") if i != 1 else mat("thread"))
    elif style == "post":          # it is the arm of a fingerpost: a post under it, and a board that says where
        b0 = Vector((0, 0, -L * 0.6))
        foot = b0 + dn * 0.62 * size
        Hn.add(g.tube([b0 + up * 0.05 * k, foot], [0.03 * k, 0.034 * k], n=4), mat("timber_grey"))
        Hn.add(g.tube([foot, foot + dn * 0.03 * k], [0.09 * k, 0.1 * k], n=4), mat("timber_dark"))
        Hn.add(g.cone(b0 + up * 0.05 * k, b0 + up * 0.11 * k, 0.036 * k, n=4), mat("timber_dark"))
        fwd = Hn.Mi @ Vector((0, -1, 0))
        brd = b0 + dn * 0.22 * size + fwd * 0.036 * k
        Hn.add(g.tongue([brd - Vector((0, 0, 0.16 * k)), brd, brd + Vector((0, 0, 0.16 * k))], [0.07 * k, 0.07 * k, 0.07 * k], thick=0.14, normal=fwd), mat("paint_pale"))
    elif style == "lens":          # a sighting-glass at the end of the long finger
        tip, d, r = Hn.tips[0]
        c = tip + d * 0.03 * k
        u_, v_ = g._frame(d)
        Hn.round(ringtube(c, 0.03 * k * size, 0.03 * k * size, 0.005 * k, n=10, u=u_, v=v_), brass)
        Hn.round(g.ico(c, 0.024 * k * size, sub=1), field("glass", 1.8))
    elif style == "pale_palm":     # a dark glove with a pale palm, so that it can be seen to turn
        Hn.round(g.ico((0, pt * 0.5 + 0.004, pl * 0.52), pw * 0.46, sub=1, scale=(1.0, 0.16, 1.14)), mat("skin_pale"))
        for i in range(4):
            pts, radii, ths = Hn.finger_points(i, curls[i], 0.0)
            a, b = pts[0], pts[1]
            front = Vector((0, math.cos(ths[0]), -math.sin(ths[0])))
            Hn.round(g.ico((a + b) / 2 + front * radii[0] * 0.6, radii[0] * 0.95, sub=0, scale=(1.0, 0.6, 1.6)), mat("skin_pale"))
    elif style == "band_light":    # a band of light round the fourth finger
        pts, radii, ths = Hn.finger_points(2, curls[2], 0.0)
        c = pts[0] + (pts[1] - pts[0]) * 0.4
        u_, v_ = g._frame((pts[1] - pts[0]).normalized())
        Hn.round(ringtube(c, radii[0] * 1.2, radii[0] * 1.2, 0.006 * k * size, n=8, u=u_, v=v_), field("oath", 3.4))
    elif style == "ribbon":        # the ribbon it was bound with when it swore
        b0 = Vector((0.056 * k, 0, -0.01 * k))
        Hn.add(strap(loop((0, 0, -0.012 * k), 0.058 * k, 0.045 * k, n=12), 0.02 * k, 0.006, closed=True), mat("cloth_lining"))
        for sgn in (1, -1):
            Hn.add(strap([b0, b0 + dn * 0.06 * k + Vector((0.02 * k, sgn * 0.01, 0)), b0 + dn * 0.15 * k * size + Vector((0.03 * k, sgn * 0.03 * k, 0))], 0.022 * k, 0.005, up=Y), mat("cloth_lining"))
    elif style == "cuff_other":    # a fine chain from its wrist that ends in an open cuff, for someone else
        geo = None
        p = Vector((-0.05 * k, 0.03 * k, -0.01 * k))
        for i in range(7):
            p = p + dn * 0.024 * k
            geo = g.merge(geo, g.ico(p, 0.01 * k, sub=0, scale=(1.0, 0.6, 1.4) if i % 2 else (0.6, 1.0, 1.4)))
        Hn.round(geo, brass)
        R = 0.07 * k * size
        c = p + dn * (R + 0.014 * k)
        u_ = (Hn.Mi @ Vector((1, 0, 0))).normalized()
        fwd = (Hn.Mi @ Vector((0, -1, 0))).normalized()
        # a band like its own cuff's, hanging open at the bottom: whoever takes it closes it
        arc = [c + (u_ * math.sin(a) - dn * math.cos(a)) * R for a in [math.radians(x) for x in range(-150, 151, 25)]]
        Hn.add(strap(arc, 0.055 * k * size, 0.012 * k, up=fwd), brass)
        Hn.round(g.ico(c - dn * R, 0.017 * k, sub=0), mat("metal_iron"))
        for e in (arc[0], arc[-1]):
            Hn.round(g.ico(e, 0.015 * k, sub=0), field("oath", 2.6))
    elif style == "ghost":         # some evenings it fills out, as if another hand were in it
        f = field("shade", 1.6)
        for tip, d, r in Hn.tips + [Hn.thumb_tip]:
            Hn.round(g.tube([tip - d * 0.01, tip + d * 0.03 * k * size, tip + d * 0.055 * k * size], [r * 0.9, r * 0.8, r * 0.3], n=5), f)
        Hn.round(g.ico((0, 0, -L - 0.004), 0.05 * k, sub=1, scale=(1.0, 0.78, 0.2)), f)
        Hn.round(g.ico((0, -pt * 0.5 - 0.002, pl * 0.5), pw * 0.2, sub=1, scale=(1.0, 0.2, 1.3)), f)
    elif style == "wisps":         # and what is in it leaves by the cuff
        for i in range(5):
            a = i * 1.3
            b0 = Vector((0.05 * k * math.cos(a), 0.04 * k * math.sin(a), -L))
            pts = [b0, b0 + dn * 0.05 * k + Vector((0.02 * k * math.sin(a), 0, 0)), b0 + dn * 0.12 * k * size + Vector((-0.03 * k * math.cos(a), 0.02 * k, 0)), b0 + dn * (0.2 + 0.03 * (i % 2)) * k * size]
            Hn.add(g.tongue(pts, [0.03 * k, 0.026 * k, 0.016 * k, 0.002], thick=0.4, normal=Vector((math.cos(a), math.sin(a), 0))), mat("shade_edge") if i % 2 else field("shade", 1.0))
    elif style == "patch":         # mended at the back, where it went soft
        Hn.add(g.box((0.01 * k, -pt * 0.5 - 0.004, pl * 0.4), (pw * 0.5, 0.008, pl * 0.34), rot=(0, math.radians(10), 0)), mark("cuff", dark))
    elif style == "stripes":       # bands of warning round a lineman's cuff
        for i in range(3):
            Hn.round(ringtube((0, 0, -L * (0.5 + 0.17 * i)), 0.055 * k * (1.5 + 0.12 * i), 0.043 * k * (1.5 + 0.12 * i), 0.01 * k, n=12), mat("paint_pale"))
    elif style == "spur":          # a climbing spur at the heel
        b0 = Vector((-pw * 0.4, pt * 0.3, 0.02 * k))
        Hn.round(g.cone(b0, b0 + Vector((-0.02, 0.09, -0.03)) * k * size, 0.014 * k, n=5), light)
    elif style == "rivets":        # rivets round the iron
        for i in range(8):
            a = 2 * math.pi * i / 8
            Hn.round(g.ico((pw * 0.38 * size * math.cos(a), pt * 0.5 + 0.014, pl * 0.52 + pw * 0.42 * size * math.sin(a)), 0.008 * k, sub=0), light)
    else:
        raise ValueError("a gauntlet cannot grow: " + str(style))


def build(form_id, level, spec, base):
    kit.reset()
    Hn = Hand(form_id, spec)
    plated = {"iron": mat("metal_iron_light"), "brass": mat("metal_brass"), "dark": mat("metal_dark")}.get(spec.get("finger_plates"))
    Hn.palm()
    Hn.fingers(spec.get("fingers", "rest"), long_first=float(spec.get("long_first", 1.0)), plated=plated)
    c_style, c_len = opt(spec.get("cuff", ["glove", 0.07]), 0.07)
    Hn.cuff(c_style, c_len * Hn.k)
    for style, size in each(spec.get("plates")):
        Hn.plates(style, size)
    for style, size in each(spec.get("grown")):
        grow(Hn, style, size, spec)
    k, pw, pl, pt, L = Hn.k, Hn.pw, Hn.pl, Hn.pt, Hn.cuff_len
    # a left hand: +Y out of the thumb side and +Z out of the back, in the game's axes, as a hand slot's are
    Hn.wear = (Vector((0, 0, 0)), Matrix.Rotation(math.radians(90), 3, "Y"))
    socks = {
        "socket_head": ((0, 0, pl + 0.13 * k), None), "socket_eyes": ((0, -pt * 0.5 - 0.012, pl * 0.6), None), "socket_mouth": ((0, -pt * 0.5 - 0.012, pl * 0.25), None),
        "socket_grip": ((0, pt * 0.5 + 0.02, pl * 0.5), None), "socket_throat": ((0, -0.05 * k, 0.0), None), "socket_light": ((0, pt * 0.5 + 0.02, pl * 0.55), None),
        "socket_back": ((0, pt * 0.5 + 0.02, pl * 0.3), None), "socket_body": ((0, -0.07 * k, -L * 0.5), None), "socket_tail": ((0, 0.06 * k, -L), None),
        "socket_arm_l": ((pw * 0.5 + 0.02, 0, pl * 0.4), None), "socket_arm_r": ((-pw * 0.5 - 0.02, 0, pl * 0.4), None),
        "socket_limb_fl": ((0.04 * k, -0.03 * k, -L), None), "socket_limb_fr": ((-0.04 * k, -0.03 * k, -L), None), "socket_keepsake": ((-0.03 * k, -0.052 * k, 0.0), None),
    }
    return finish(Hn, form_id, base, spec, M=Hn.M, sockets=socks)
