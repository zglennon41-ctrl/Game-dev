"""WILDLINE genius lines, the armors: the Coat (docs/genius-lines.md, "The armors").
lines_armors.py loads this file; what the conventions are, and what `wear` means, is said there.

A coat stands as if one of the game's people wore it and no one does: its hem at z = 0, the
wearer's middle up the Z axis, their front to -Y. `length` is from the shoulders to the hem.
Every coat keeps at its throat the clasp it grew from, and the eye in the clasp: that is where
it is alive.
"""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z
import genius_kit as kit
from genius_kit import mat, field, mark
from genius_relics import strap, ringtube
from lines_armors import Piece, finish, eye, opt, each, lathe_at

PI = math.pi


class Coat(Piece):
    def __init__(self, form_id, spec):
        Piece.__init__(self, form_id)
        g_ = lambda k, d: float(spec.get(k, d))  # noqa: E731
        self.L = g_("length", 1.5)
        self.flare, self.chest, self.waist, self.shw = g_("flare", 0.12), g_("chest", 1.0), g_("waist", 1.0), g_("shoulders", 1.0)
        self.open, self.cut, self.wave, self.rag = g_("open", 0.05), g_("cut", 0.0), g_("wave", 0.0), g_("rag", 0.0)
        sw = spec.get("sweep", [0, 0])
        self.sweep = (float(sw[0]), float(sw[1]))
        self.main, self.under, self.brass = mat("leather"), mat("leather_dark"), mat("metal_brass")
        # what it is lined with shows wherever it is turned back (collar, lapels, cuffs). A lining of
        # the field's light stays at those edges, so the coat keeps its form; `storm` is light all through
        kind = spec.get("lining", "plain")
        plain = mark("lining", self.under)
        self.lining = {"plain": plain, "field": field("lining", 1.3), "storm": field("lining", 1.3), "red": mat("cloth_lining"), "fur": mat("pelt_light")}[kind]
        self.inside = plain if kind == "field" else self.lining
        self.cuffs = {}          # side -> (where the cuff ends, the way the sleeve runs there, its radius)

    # --- the body of the coat ------------------------------------------------------------
    def t(self, d):
        """How far down the skirt a place is: 0 at the waist, 1 at the hem."""
        return max(0.0, min(1.0, (d - 0.52) / max(0.05, self.L - 0.52)))

    def section(self, d):
        """Half-width, half-depth and middle of the coat at a distance d below the shoulders."""
        rows = ((-0.06, 0.105, 0.095), (0.0, 0.3 * self.shw, 0.15 * (0.6 + 0.4 * self.chest)), (0.2, 0.3 * self.chest * (0.5 + 0.5 * self.shw), 0.185 * self.chest),
                (0.52, 0.25 * self.waist, 0.16 * self.waist), (0.77, 0.275 * (0.5 + 0.5 * self.waist), 0.195 * (0.5 + 0.5 * self.waist)))
        if d >= rows[-1][0]:
            rx, ry = rows[-1][1] + self.flare * (d - 0.77), rows[-1][2] + 0.85 * self.flare * (d - 0.77)
        else:
            for (d0, x0, y0), (d1, x1, y1) in zip(rows, rows[1:]):
                if d <= d1:
                    f = max(0.0, (d - d0) / (d1 - d0))
                    rx, ry = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                    break
        t = self.t(d)
        return rx, ry, self.sweep[0] * t * t, self.sweep[1] * t * t

    def gap(self, d):
        """Half the opening down its front, as an angle."""
        return min(2.2, self.open + self.cut * self.t(d))

    def at(self, d, a, out=0.0):
        """A place on the coat: d below the shoulders, at an angle a round it from the middle
        of the back (pi is the middle of the front, +pi/2 the wearer's left), `out` from the cloth."""
        rx, ry, cx, cy = self.section(d)
        k = 1.0 + self.wave * math.sin(4 * a + 1.3) * self.t(d)
        n = Vector((math.sin(a) * ry, math.cos(a) * rx, 0)).normalized()
        return Vector((cx + rx * k * math.sin(a), cy + ry * k * math.cos(a), self.L - d)) + n * out

    def normal(self, d, a):
        rx, ry, cx, cy = self.section(d)
        return Vector((math.sin(a) * ry, math.cos(a) * rx, 0)).normalized()

    def shell(self, n=13, thick=0.02):
        L = self.L
        ds = [d for d in (-0.05, 0.0, 0.2, 0.52, 0.77) if d < L - 0.04]
        d = 0.77
        while d + 0.3 < L - 0.04:
            d += 0.3
            ds.append(d)
        ds.append(L)
        rings = []
        for d in ds:
            phi = self.gap(d)
            angles = [-(PI - phi) + 2 * (PI - phi) * i / (n - 1) for i in range(n)]
            outer = [self.at(d, a) for a in angles]
            inner = [self.at(d, a, -thick) for a in angles]
            if d == L and self.rag:          # a hem that has been through things
                for i, a in enumerate(angles):
                    dz = self.rag * 0.16 * abs(math.sin(3.5 * a + 0.5))
                    outer[i].z += dz
                    inner[i].z += dz
            rings.append(outer + list(reversed(inner)))
        main, lining = self.main, self.inside
        self.solid(g.loft(rings, caps=True, closed=True), lambda c, nrm: lining if (nrm.x * c.x + nrm.y * (c.y - 0.0)) < -0.25 * math.hypot(c.x, c.y) else main)
        self.round(g.ico((0, 0, L - 0.03), 0.1, sub=1, scale=(1.0, 0.9, 0.15)), mat("void"))
        # the seams of it: its partner may show them pale
        st = None
        for s in (1, -1):
            st = g.merge(st, g.tube([self.at(-0.04, s * 0.5 * PI, 0.006), self.at(0.0, s * 0.5 * PI, 0.008) + Vector((s * 0.0, 0, 0.005))], [0.005, 0.005], n=3))
        back = [self.at(d, 0.0, 0.006) for d in ds if 0.0 <= d]
        if len(back) > 1:
            st = g.merge(st, g.tube(back, [0.005] * len(back), n=3))
        self.round(st, mark("stitch", self.main))

    def sleeve(self, side, style, arm=1.0):
        if style in (None, "none"):
            return
        s, L, shx = side, self.L, 0.3 * self.shw
        sh = Vector((s * (shx - 0.02), 0.0, L - 0.05))
        path = {
            "hang": [sh, Vector((s * (shx + 0.07), 0.02, L - 0.48)), Vector((s * (shx + 0.08), -0.07, L - 0.95))],
            "flat": [sh, Vector((s * (shx + 0.035), 0.01, L - 0.5)), Vector((s * (shx + 0.04), 0.0, L - 1.02))],
            "reach": [sh, Vector((s * (shx + 0.07), -0.08, L - 0.4)), Vector((s * (shx - 0.06), -0.52, L - 0.2))],
            "spread": [sh, Vector((s * (shx + 0.34), 0.0, L - 0.2)), Vector((s * (shx + 0.7), -0.05, L - 0.4))],
            "back": [sh, Vector((s * (shx + 0.06), 0.2, L - 0.42)), Vector((s * (shx + 0.07), 0.4, L - 0.8))],
        }[style]
        radii = [0.094 * arm, 0.08 * arm, 0.075 * arm]
        self.round(g.tube(path, radii, n=7, flat=0.3 if style == "flat" else 1.0, up=Y if style == "flat" else None), self.main)
        d = (path[2] - path[1]).normalized()
        if style != "flat":
            self.round(lathe_at([(radii[2] * 1.02, -0.07), (radii[2] * 1.13, -0.06), (radii[2] * 1.16, 0.006), (radii[2] * 0.9, 0.008)], path[2], d, n=7), self.lining)
            self.round(lathe_at([(radii[2] * 0.92, 0.0), (0.0, 0.012)], path[2], d, n=7), mat("void"))
        self.cuffs[side] = (path[2], d, radii[2])

    # --- its collar ---------------------------------------------------------------------
    def dark(self, size):
        """The dark a high collar holds: its half-width, half-depth, half-height, and the height of its middle."""
        rim = 0.7 + 0.3 * size
        rz = 0.182 * max(1.0, size)
        return 0.66 * 0.24 * rim, 0.66 * 0.22 * rim, rz, self.L + 0.46 * size - 0.9 * rz

    def collar(self, style, size=1.0):
        L = self.L
        main, lining = self.main, self.lining
        if style in (None, "none"):
            return

        def band(z0, z1, r0, r1, gap=0.5, n=11, thick=0.016, tilt=0.0):
            """A collar standing round the neck: open at the front, flaring as it rises."""
            rings = []
            for z, (rx, ry) in ((z0, r0), ((z0 + z1) / 2, ((r0[0] + r1[0]) / 2, (r0[1] + r1[1]) / 2)), (z1, r1)):
                outer, inner = [], []
                for i in range(n):
                    a = -(PI - gap) + 2 * (PI - gap) * i / (n - 1)
                    lift = tilt * (z - z0) * math.cos(a)          # higher at the back
                    outer.append(Vector((rx * math.sin(a), ry * math.cos(a) + 0.006, L + z + lift)))
                    inner.append(Vector(((rx - thick) * math.sin(a), (ry - thick) * math.cos(a) + 0.006, L + z + lift)))
                rings.append(outer + list(reversed(inner)))
            self.solid(g.loft(rings, caps=True, closed=True), lambda c, nrm: lining if (nrm.x * c.x + nrm.y * c.y) < -0.25 * math.hypot(c.x, c.y) else main)
        if style in ("turned", "whiskers", "frost"):
            band(-0.03, 0.2 * size, (0.115, 0.105), (0.175 * (0.8 + 0.2 * size), 0.16 * (0.8 + 0.2 * size)), tilt=0.25)
        elif style == "stand":
            band(-0.03, 0.09 * size, (0.112, 0.102), (0.118, 0.108), gap=0.3)
        elif style == "high":        # a collar that stands up by itself
            band(-0.03, 0.46 * size, (0.125, 0.115), (0.24 * (0.7 + 0.3 * size), 0.22 * (0.7 + 0.3 * size)), gap=0.62, tilt=0.2)
            rx, ry, rz, zc = self.dark(size)       # and is full of dark, to the brim
            self.round(g.ico((0, 0.02, zc), 1.0, sub=2, scale=(rx, ry, rz)), mat("void"))
        elif style == "spread":      # spread wide, flat as a dish, to hear with
            band(-0.02, 0.12, (0.115, 0.105), (0.46 * size, 0.42 * size), gap=0.3, tilt=0.5, n=13)
        elif style in ("ear", "ears"):
            band(-0.03, 0.1, (0.112, 0.102), (0.13, 0.12), gap=0.4)
        elif style == "hood":        # a hood, and the dark where a face would be
            c = Vector((0, 0.03, L + 0.19 * size))
            self.round(g.ico(c, 0.215 * size, sub=2, scale=(0.92, 1.0, 1.12)), main)
            face = c + Vector((0, -0.15 * size, -0.03 * size))
            self.round(g.ico(face, 0.1 * size, sub=2, scale=(1.2, 0.82, 1.5)), mat("void"))
            self.round(ringtube(face + Vector((0, -0.04 * size, 0)), 0.124 * size, 0.154 * size, 0.015 * size, n=12, u=X, v=Z), main)
            band(-0.04, 0.06, (0.125, 0.115), (0.2, 0.19), gap=0.3)
        elif style == "fur":         # a collar of pelt
            for i in range(11):
                a = -2.4 + 4.8 * i / 10
                b0 = Vector((0.13 * math.sin(a), 0.12 * math.cos(a), L + 0.02))
                self.add(g.blade(b0, b0 + Vector((0.16 * math.sin(a), 0.15 * math.cos(a), 0.1 + 0.04 * (i % 2))) * size, 0.13, normal=Vector((math.sin(a), math.cos(a), 0.8))), mat("pelt_dark") if i % 2 else mat("pelt_light"))
        elif style == "cape":
            band(-0.03, 0.1, (0.112, 0.102), (0.14, 0.13), gap=0.4)
        else:
            raise ValueError("no such collar: " + str(style))
        if style in ("ear", "ears"):  # a collar shaped like the rim of an ear, either side
            for s in (1, -1):
                k = size
                path = [Vector((s * 0.1, 0.03, L - 0.01)), Vector((s * 0.2 * k, 0.06, L + 0.2 * k)), Vector((s * 0.36 * k, 0.07, L + 0.36 * k)), Vector((s * 0.5 * k, 0.05, L + 0.3 * k)),
                        Vector((s * 0.53 * k, 0.03, L + 0.12 * k)), Vector((s * 0.42 * k, 0.02, L - 0.0 * k)), Vector((s * 0.3 * k, 0.02, L - 0.02))]
                self.round(g.tube(path, [0.03, 0.036 * k, 0.04 * k, 0.04 * k, 0.036 * k, 0.03 * k, 0.02], n=6), main)
                self.round(g.ico(Vector((s * 0.33 * k, 0.065, L + 0.16 * k)), 0.19 * k, sub=1, scale=(0.95, 0.1, 0.92)), lining)
                self.round(g.tube([Vector((s * 0.24 * k, 0.04, L + 0.08 * k)), Vector((s * 0.34 * k, 0.03, L + 0.2 * k)), Vector((s * 0.42 * k, 0.03, L + 0.16 * k))], [0.018 * k, 0.022 * k, 0.012 * k], n=5), main)
        if style == "whiskers":      # fine whiskers of thread along the collar's edge, that stir at sounds
            for i in range(9):
                a = -2.3 + 4.6 * i / 8
                b0 = Vector((0.175 * math.sin(a), 0.16 * math.cos(a), L + 0.2 * size + 0.05 * math.cos(a)))
                tip = b0 + Vector((0.2 * math.sin(a), 0.16 * math.cos(a), 0.12 + 0.05 * (i % 2))) * size
                self.round(g.tube([b0, (b0 + tip) / 2 + Vector((0, 0, 0.03)), tip], [0.006, 0.005, 0.002], n=3), mat("thread"))
        if style == "frost":         # frost on the collar that does not melt by the fire
            for i in range(9):
                a = -2.3 + 4.6 * i / 8
                b0 = Vector((0.17 * math.sin(a), 0.155 * math.cos(a), L + 0.19 * size + 0.05 * math.cos(a)))
                self.add(g.cone(b0, b0 + Vector((0.06 * math.sin(a), 0.05 * math.cos(a), 0.08 + 0.04 * (i % 3))) * size, 0.022, n=4), mat("frost"))

    def clasp(self, size=1.0):
        """The clasp it grew from, at its throat, and the eye in it."""
        c = self.at(0.07, PI, 0.022)
        k = size
        for s in (1, -1):
            self.add(g.box(c + Vector((s * 0.04 * k, 0, 0)), (0.055 * k, 0.014, 0.05 * k)), self.brass)
            self.round(g.ico(c + Vector((s * 0.07 * k, -0.004, 0)), 0.012 * k, sub=0), mark("studs", self.main))
        self.round(g.tube([c + Vector((-0.03 * k, -0.01, 0.0)), c + Vector((0.0, -0.016, 0.006 * k)), c + Vector((0.03 * k, -0.01, 0.0))], [0.007 * k, 0.007 * k, 0.007 * k], n=4), self.brass)
        self.add_items(eye(c + Vector((-0.04 * k, -0.008, 0)), 0.02 * k, lids=self.brass))

    def pocket(self, d, a, w=0.2, h=0.2, bulge=0.0, flap=True, material=None):
        material = material or self.main
        c, n = self.at(d, a, 0.012), self.normal(d, a)
        rz = math.atan2(-n.x, n.y)
        self.add(g.box(c + n * 0.008, (w, 0.03, h), rot=(0, 0, rz)), material)
        if bulge:
            self.round(g.ico(c + n * (0.02 + 0.03 * bulge) + Vector((0, 0, -0.02)), w * 0.42, sub=1, scale=(1.0, 0.5 * bulge + 0.2, 0.95)), material)
        if flap:
            self.add(g.box(c + n * 0.024 + Vector((0, 0, h * 0.42)), (w * 1.08, 0.022, h * 0.3), rot=(0, 0, rz)), self.under)
            self.round(g.ico(c + n * 0.04 + Vector((0, 0, h * 0.3)), 0.012, sub=0), self.brass)
        return c, n


def grow(C, style, size, spec):
    L = C.L
    main, under, brass, lining = C.main, C.under, C.brass, C.lining
    iron = mat("metal_iron")
    if style == "belt":            # a belt, and its buckle
        d = 0.5
        phi = C.gap(d)
        pts = [C.at(d, -(PI - phi) + 2 * (PI - phi) * i / 12, 0.012) for i in range(13)]
        C.add(strap(pts, 0.06, 0.014, up=Z), under)
        C.add(g.box(C.at(d, PI - phi - 0.12, 0.022), (0.07, 0.02, 0.075)), brass)
        for i in (3, 6, 9):
            C.round(g.ico(pts[i] + C.normal(d, 0) * 0.0 + (pts[i] - Vector((0, 0, pts[i].z))).normalized() * 0.008, 0.011, sub=0), mark("studs", main))
    elif style in ("buttons", "buttons2", "offices"):     # buttons; two rows; a button for every writ served
        rows = 1 if style == "buttons" else 2
        n = {"buttons": 4, "buttons2": 5, "offices": 11}[style]
        bottom = {"buttons": 0.62, "buttons2": 0.66, "offices": min(L - 0.12, 1.45)}[style]
        for r_ in range(rows):
            for i in range(n):
                d = 0.14 + (bottom - 0.14) * i / (n - 1)
                a = PI - C.gap(d) - (0.1 if rows == 1 else (0.12 + 0.26 * r_)) if rows == 1 or True else 0
                if rows == 2 and r_ == 1:
                    a = -(PI - C.gap(d) - 0.12)
                m = brass if style != "offices" or (i + r_) % 3 else field("writ", 1.8)
                C.round(g.ico(C.at(d, a, 0.014), 0.017 * size, sub=0, scale=(1, 1, 1)), m)
    elif style == "pack":          # what it carries between places: a roll at the back, and its strap
        c = C.at(0.2, 0.0, 0.09)
        C.round(g.tube([c + Vector((-0.2, 0, 0)), c, c + Vector((0.2, 0, 0))], [0.075 * size, 0.085 * size, 0.075 * size], n=7), mat("cloth_wool"))
        for s in (1, -1):
            C.round(ringtube(c + Vector((s * 0.12, 0, 0)), 0.088 * size, 0.088 * size, 0.008, n=8, u=Y, v=Z), under)
        C.add(strap([C.at(0.02, 0.6, 0.014), C.at(0.2, PI * 0.72, 0.016), C.at(0.46, PI - 0.45, 0.016)], 0.05, 0.012, up=Z), under)
    elif style == "dust":          # dust on the hem from somewhere else
        d = L - 0.07
        phi = C.gap(d)
        pts = [C.at(d, -(PI - phi) + 2 * (PI - phi) * i / 14, 0.006) for i in range(15)]
        C.add(strap(pts, 0.13 * size, 0.008, up=Z), mat("cloth_dust"))
    elif style == "stamps":        # a hem covered in post-marks, stamped one over another
        for row, (dd, off) in enumerate(((0.08, 0.0), (0.2, 0.5), (0.32, 0.2))):
            d = L - dd
            phi = C.gap(d)
            n = 11
            for i in range(n):
                a = -(PI - phi - 0.1) + 2 * (PI - phi - 0.1) * (i + off) / n
                m = (mat("stamp_ink"), mat("paint_red"), mat("paint_pale"))[(i + row) % 3]
                C.round(g.ico(C.at(d, a, 0.006), 0.05 * size, sub=1, scale=(1.0, 1.0, 1.0)), m)
        for s in (1, -1):
            if s in C.cuffs:
                p, dvec, r = C.cuffs[s]
                C.round(g.ico(p - dvec * 0.2 + Vector((s * r, 0, 0)), 0.04, sub=1, scale=(0.3, 1.0, 1.0)), mat("stamp_ink"))
    elif style == "pockets":       # more pockets than were sewn, and some of them occupied
        spots = [(0.86, PI * 0.7, 0.22, 0.24, 1.0), (0.86, -PI * 0.7, 0.22, 0.24, 0.8), (0.26, PI * 0.76, 0.14, 0.14, 0.6), (0.26, -PI * 0.76, 0.14, 0.14, 0.0),
                 (1.12, PI * 0.42, 0.2, 0.2, 0.9), (1.12, -PI * 0.42, 0.2, 0.2, 0.5), (0.6, PI * 0.5, 0.13, 0.15, 0.7), (0.6, -PI * 0.5, 0.13, 0.15, 0.4), (0.7, 0.0, 0.2, 0.2, 0.6)]
        stuff = [m for m in (under, mat("cloth_patch_c"), under, mat("cloth_patch_b"))]
        for i, (d, a, w, h, b) in enumerate(spots[: int(round(6 * size))]):
            if d < L - 0.12:
                C.pocket(d, a, w, h, bulge=b, material=stuff[i % 4])
    elif style == "items":         # what has turned up in them
        c, n = C.at(0.76, PI * 0.7, 0.03), C.normal(0.76, PI * 0.7)
        C.round(g.tube([c, c + Vector((0.01, 0, 0.2))], [0.03, 0.022], n=6), mat("glass"))                    # a bottle
        C.round(g.ico(c + Vector((0.01, 0, 0.22)), 0.02, sub=0), mat("wax"))
        c2 = C.at(0.76, -PI * 0.7, 0.04)
        C.round(g.tube([c2 + Vector((0, 0, -0.02)), c2 + Vector((-0.03, -0.03, 0.26))], [0.026, 0.02], n=6), brass)   # a glass for looking through
        C.round(g.ico(c2 + Vector((-0.03, -0.03, 0.27)), 0.024, sub=1), field("glass", 1.8))
        c3 = C.at(0.18, PI * 0.76, 0.04)
        C.add(g.box(c3 + Vector((0, 0, 0.06)), (0.09, 0.02, 0.12), rot=(0, 0.2, 0.3)), mat("paper"))          # a letter
        c4 = C.at(1.02, PI * 0.42, 0.06)
        C.round(g.ico(c4 + Vector((0, 0, 0.06)), 0.05, sub=1), field("lost", 2.4))                               # and something it lost last season
    elif style == "pelt":          # a pelt has grown through the cloth at the shoulders
        for row, (d, n, Lb) in enumerate(((0.02, 13, 0.22), (0.14, 15, 0.26), (0.3, 15, 0.22))[: 2 + (size > 1.2)]):
            for i in range(n):
                a = -PI * 0.86 + 2 * PI * 0.86 * i / (n - 1)
                b0 = C.at(d, a, 0.0)
                nrm = C.normal(d, a)
                C.add(g.blade(b0, b0 + nrm * 0.1 * size + Vector((0, 0, -Lb * size)), 0.17 * size, normal=nrm + Vector((0, 0, 0.5)), belly=0.4), mat("pelt_dark") if (i + row) % 2 else mat("pelt_light"))
    elif style == "rime":          # frost that does not melt
        for i in range(12):
            a = -PI * 0.8 + 2 * PI * 0.8 * i / 11
            b0 = C.at(0.03, a, 0.02)
            nrm = C.normal(0.03, a)
            C.add(g.cone(b0, b0 + nrm * 0.07 + Vector((0, 0, 0.1 + 0.05 * (i % 3))) * size, 0.03, n=4), mat("frost"))
        d = L - 0.05
        phi = C.gap(d)
        pts = [C.at(d, -(PI - phi) + 2 * (PI - phi) * i / 14, 0.006) for i in range(15)]
        C.add(strap(pts, 0.1, 0.008, up=Z), mat("frost"))
    elif style == "pads":          # padded at the elbows and shoulders with something like stone
        for s in (1, -1):
            sh = Vector((s * 0.3 * C.shw, 0.0, L - 0.02))
            C.add(g.ico(sh + Vector((s * 0.03, 0, 0.02)), 0.15 * size, sub=1, scale=(1.1, 1.0, 0.62)), mat("stone_hide"))
            C.add(g.ico(sh + Vector((s * 0.03, 0, 0.07)), 0.09 * size, sub=0, scale=(1.1, 1.0, 0.6)), mat("stone_light"))
            if s in C.cuffs:
                p, dvec, r = C.cuffs[s]
                C.add(g.ico(p - dvec * 0.46 + Vector((s * 0.02, 0.05, 0)), 0.1 * size, sub=1, scale=(0.9, 1.0, 1.1)), mat("stone_hide"))
        C.add(g.box(C.at(0.25, 0.0, 0.03), (0.34, 0.06, 0.4)), mat("stone_plate"))
    elif style == "lamp":          # a lamp at its collar, for where the air is bad
        c = C.at(0.16, PI - 0.5, 0.05)
        r = 0.05 * size
        C.round(lathe_at([(r * 0.5, 0.0), (r, 0.01), (r, 0.028), (r * 0.5, 0.034)], c + Vector((0, 0, -r - 0.03)), Z, n=6), brass)
        C.round(g.ico(c, r, sub=1, scale=(1, 1, 1.15)), field("lamp", 3.6))
        C.round(lathe_at([(r * 0.8, 0.0), (r * 0.2, 0.03)], c + Vector((0, 0, r * 1.05)), Z, n=6), brass)
    elif style == "smoke":         # it is hard to say where it ends
        d = L - 0.02
        for i in range(8):
            a = -2.6 + 5.2 * i / 7
            b0 = C.at(d, a, 0.0)
            nrm = C.normal(d, a)
            k = size * (0.8 + 0.3 * math.sin(i * 1.7))
            pts = [b0 + Vector((0, 0, 0.1)), b0 + nrm * 0.04 * k + Vector((0, 0, -0.02)), b0 + nrm * 0.1 * k + Vector((0.03 * math.sin(i), 0, 0.12 * k)), b0 + nrm * 0.07 * k + Vector((0, 0, 0.3 * k))]
            C.add(g.tongue(pts, [0.12, 0.11, 0.07, 0.01], thick=0.3, normal=nrm), mat("smoke") if i % 3 else mat("shade_edge"))
    elif style == "ghost_sleeve":  # it leaves a sleeve where its partner was, and the sleeve takes the blow
        s = -1
        base = Vector((s * (0.3 * C.shw + 0.34), -0.1, L - 0.3))
        pts = [base, base + Vector((s * 0.06, -0.02, -0.42)), base + Vector((s * 0.02, -0.08, -0.86))]
        C.round(g.tube(pts, [0.085, 0.075, 0.07], n=7), mat("smoke"))
        C.round(lathe_at([(0.076, 0.0), (0.0, 0.012)], pts[2], (pts[2] - pts[1]).normalized(), n=7), mat("void"))
        for i in range(4):
            b0 = base + Vector((0.0, 0.0, 0.02))
            C.add(g.tongue([b0, b0 + Vector((-s * 0.1, 0.02 * i, 0.06 + 0.03 * i)), b0 + Vector((-s * 0.22, 0.03 * i, 0.04 * i))], [0.1, 0.07, 0.01], thick=0.3, normal=Y), mat("shade_edge"))
        C.round(ringtube(pts[1], 0.082, 0.082, 0.006, n=8, u=X, v=Y), field("pulse", 1.6))
    elif style == "knife":         # a hard straight line in the lining, a hand long
        d0 = 0.3
        a = PI - C.gap(d0) - 0.05
        hilt = C.at(d0, a, -0.03) + Vector((0.02, -0.02, 0))
        tip = hilt + Vector((0.0, 0.0, -0.36 * size))
        C.add(g.tongue([hilt + Vector((0, 0, -0.06)), (hilt + tip) / 2, tip], [0.045, 0.04, 0.004], thick=0.2, normal=Y), mat("steel_polish"))
        C.round(g.tube([hilt + Vector((0, 0, -0.06)), hilt + Vector((0, 0, 0.06))], [0.016, 0.014], n=5), under)
        C.add(g.box(hilt + Vector((0, 0, -0.06)), (0.09, 0.02, 0.016)), brass)
        C.round(g.ico(hilt + Vector((0, 0, 0.07)), 0.018, sub=0), field("hilt", 2.6))
    elif style == "lapels":        # lapels, turned back to show what it is lined with; or cut sharp as blades
        for s in (1, -1):
            a = s * (PI - C.gap(0.1) - 0.02)
            top, low = C.at(0.0, a, 0.02), C.at(0.46 * size, s * (PI - C.gap(0.46 * size) - 0.02), 0.02)
            out = C.normal(0.2, s * (PI - 0.5))
            mid = (top + low) / 2 + out * 0.12 * size + Vector((0, -0.03, 0.05))
            C.add(g.tongue([top, mid, low], [0.05, 0.2 * size, 0.02], thick=0.14, normal=Vector((s * 0.3, -1, 0.1))), lining)
    elif style == "eyes":          # what looks out of the dark of its collar
        c_style, k = opt(spec.get("collar", "turned"))
        rx, ry, rz, zc = C.dark(k)
        el, az = math.radians(48), math.radians(38)       # high on the dark and to the front, over the collar's edge
        for s in (1, -1):
            d = Vector((s * math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)))
            p = Vector((rx * d.x, 0.02 + ry * d.y, zc + rz * d.z)) + d * 0.006
            er = 0.27 * rx * min(size, 1.15)
            C.round(g.ico(p, er, sub=1, scale=(1.3, 0.6, 0.7)), field("eyes", 4.0))
    elif style == "stars":         # after dusk, the colour of whatever is behind it
        f = field("stars", 2.0)
        for i in range(14):
            a = -2.7 + 5.4 * ((i * 0.618) % 1.0)
            d = 0.25 + (L - 0.4) * ((i * 0.381 + 0.13) % 1.0)
            C.round(g.ico(C.at(d, a, 0.006), 0.014 + 0.008 * (i % 3), sub=0), f)
    elif style == "wind":          # the lining is weather now, and it has been let out
        f = field("storm", 1.5)
        for i in range(7):
            d = 0.3 + 0.16 * i
            if d > L - 0.1:
                break
            s = 1 if i % 2 else -1
            b0 = C.at(d, s * (PI - C.gap(d) * 0.5), -0.05)
            k = size * (0.8 + 0.3 * math.sin(i * 2.1))
            pts = [b0, b0 + Vector((s * 0.1, -0.2, 0.05)) * k, b0 + Vector((s * 0.3, -0.42, 0.16)) * k, b0 + Vector((s * 0.26, -0.62, 0.36)) * k]
            C.add(g.tongue(pts, [0.12, 0.11, 0.07, 0.01], thick=0.3, normal=Vector((0, 0.2, 1))), f if i % 2 else mat("smoke"))
    elif style == "scorch":        # black at every edge, and stiff as hide
        st = mat("soot")
        d = L - 0.05
        phi = C.gap(d)
        pts = [C.at(d, -(PI - phi) + 2 * (PI - phi) * i / 14, 0.008) + Vector((0, 0, 0.06 * abs(math.sin(3.5 * (-(PI - phi) + 2 * (PI - phi) * i / 14) + 0.5)) * C.rag)) for i in range(15)]
        C.add(strap(pts, 0.12, 0.008, up=Z), st)
        for s in (1, -1):
            if s in C.cuffs:
                p, dvec, r = C.cuffs[s]
                C.round(g.tube([p - dvec * 0.1, p + dvec * 0.01], [r * 1.08, r * 1.2], n=7), st)
            edge = [C.at(dd, s * (PI - C.gap(dd) - 0.02), 0.01) for dd in (0.05, 0.3, 0.55, min(L - 0.05, 0.8))]
            C.add(strap(edge, 0.07, 0.008, up=Y), st)
        f = field("ember", 2.6)
        C.round(g.tube([p + Vector((0, 0, 0.07)) for p in pts], [0.008] * len(pts), n=3), f)
        C.add(strap([p + Vector((0, 0, 0.12)) for p in pts], 0.035, 0.008, up=Z), mat("cloth_dust"))
        for i in range(7):
            a = -2.6 + 5.2 * i / 6
            C.round(g.ico(C.at(L - 0.03 - 0.03 * (i % 2), a, 0.016), 0.024 * size, sub=0), f)
    elif style == "epaulettes":    # the offices it has held, on its shoulders
        for s in (1, -1):
            sh = Vector((s * 0.3 * C.shw, 0.0, L + 0.0))
            C.add(g.box(sh + Vector((-s * 0.04, 0, 0.012)), (0.2, 0.13, 0.03)), brass)
            for i in range(5):
                b0 = sh + Vector((s * 0.06, -0.05 + 0.025 * i, 0.0))
                C.round(g.tube([b0, b0 + Vector((s * 0.02, 0, -0.1 * size))], [0.009, 0.007], n=4), brass)
    elif style == "chain":         # a chain of office
        geo = None
        for i in range(15):
            t = i / 14
            a = PI - 0.9 + 1.8 * t
            d = 0.06 + 0.3 * math.sin(PI * t)
            geo = g.merge(geo, g.ico(C.at(d, a, 0.02), 0.018 * size, sub=0, scale=(1.3, 0.6, 1.0) if i % 2 else (0.8, 0.6, 1.3)))
        C.round(geo, brass)
        C.round(g.ico(C.at(0.38, PI, 0.03), 0.045 * size, sub=1, scale=(1, 0.4, 1)), field("seal", 2.4))
    elif style == "oath":          # its partner's oath, stitched in the lining where only they can read it: the left breast, turned back
        f = field("oath", 2.2)
        a = PI - C.gap(0.3) - 0.42
        c, n = C.at(0.3, a, 0.03), C.normal(0.3, a)
        rz = math.atan2(-n.x, n.y)
        C.add(g.box(c, (0.26 * size, 0.02, 0.36 * size), rot=(0, 0, rz)), mat("cloth_lining"))
        side = Vector((n.y, -n.x, 0))
        for i in range(5):
            z = 0.13 - 0.06 * i
            w = (0.1 - 0.02 * (i % 2)) * size
            C.round(g.tube([c + n * 0.014 - side * w + Vector((0, 0, z * size)), c + n * 0.014 + side * w + Vector((0, 0, z * size))], [0.007, 0.007], n=3), f)
        C.round(g.ico(c + n * 0.016 + Vector((0, 0, -0.2 * size)), 0.03, sub=1, scale=(1, 1, 1)), mat("wax"))
    elif style == "stock":         # a clerk's white stock at the throat, and the points of a collar
        c = C.at(0.1, PI, 0.012)
        C.add(g.blade(c + Vector((0, 0, 0.07)), c + Vector((0, -0.01, -0.16 * size)), 0.17 * size, normal=Vector((0, -1, 0)), belly=0.3), mat("paper"))
        for s in (1, -1):
            C.add(g.blade(c + Vector((s * 0.03, 0, 0.08)), c + Vector((s * 0.14 * size, -0.01, 0.0)), 0.07, normal=Vector((0, -1, 0.3))), mat("paper"))
    elif style == "sash":          # the sash of an office, shoulder to hip
        pts = [C.at(0.02, PI * 0.56, 0.02), C.at(0.2, PI * 0.8, 0.02), C.at(0.38, PI - 0.25, 0.022), C.at(0.56, -(PI - 0.5), 0.02), C.at(0.72, -PI * 0.6, 0.02)]
        C.add(strap(pts, 0.1 * size, 0.012, up=Z), mat("paint_red"))
        C.round(g.ico(C.at(0.7, -PI * 0.62, 0.04), 0.04, sub=1, scale=(1, 0.5, 1)), brass)
    elif style == "tug":           # one cuff worn thin where it takes hold of a wrist
        if 1 in C.cuffs:
            p, dvec, r = C.cuffs[1]
            C.round(g.tube([p - dvec * 0.02, p + dvec * 0.03], [r * 1.14, r * 1.1], n=7), mat("thread"))
            u_, v_ = g._frame(dvec)
            for i in range(4):          # the cuff closing like fingers
                a = 0.6 + i * 0.5
                b0 = p + (u_ * math.cos(a) + v_ * math.sin(a)) * r * 0.9
                C.round(g.tube([b0, b0 + dvec * 0.07 * size + (u_ * math.cos(a) + v_ * math.sin(a)) * 0.03, b0 + dvec * 0.12 * size - (u_ * math.cos(a) + v_ * math.sin(a)) * 0.03], [0.02, 0.018, 0.01], n=5), main)
            C.round(ringtube(p - dvec * 0.08, r * 1.06, r * 1.06, 0.006, n=8, u=u_, v=v_), field("pulse", 2.2))
            # and what it has hold of: the place a wrist would be, shown in light
            C.round(ringtube(p + dvec * 0.085 * size, 0.062 * size, 0.062 * size, 0.013, n=10, u=dvec, v=u_, sides=4), field("pulse", 2.6))
    elif style == "hook":          # left on a hook in another room
        top = Vector((0, 0.06, L + 0.42 * size))
        C.add(g.box(top + Vector((0, 0.05, 0.06)), (0.5, 0.04, 0.12)), mat("wood_dark"))
        C.round(g.tube([top + Vector((0, 0.03, 0.06)), top + Vector((0, -0.05, 0.04)), top + Vector((0, -0.07, -0.04)), top + Vector((0, -0.03, -0.08))], [0.014, 0.014, 0.013, 0.01], n=5), iron)
        C.round(g.tube([top + Vector((0, -0.03, -0.08)), Vector((0, 0.08, L + 0.05))], [0.008, 0.008], n=4), mat("cord"))
        for s in (1, -1):
            C.round(g.ico(top + Vector((s * 0.2, 0.03, 0.06)), 0.014, sub=0), iron)
    elif style == "patches":       # mended in four different hands
        spots = [(0.3, PI * 0.72, "cloth_patch_a", 0.2), (0.9, -PI * 0.6, "cloth_patch_b", 0.26), (1.15, PI * 0.3, "cloth_patch_c", 0.22), (0.62, -PI * 0.2, "cloth_patch_a", 0.18),
                 (0.36, -PI * 0.8, "cloth_patch_c", 0.16), (1.2, -PI * 0.85, "cloth_patch_b", 0.2)]
        for i, (d, a, m, w) in enumerate(spots[: int(round(4 * size)) + 1]):
            if d < L - 0.14:
                c, n = C.at(d, a, 0.008), C.normal(d, a)
                C.add(g.box(c, (w, 0.014, w * (0.8 + 0.3 * (i % 2))), rot=(0, 0.2 * (i - 2), math.atan2(-n.x, n.y))), mat(m))
                C.round(g.tube([c + Vector((0, 0, w * 0.5)) + n * 0.01, c + Vector((0, 0, w * 0.62)) + n * 0.012], [0.006, 0.006], n=3), mat("thread") if i % 2 else mat("cloth_lining"))
        if 1 in C.cuffs:            # and one sleeve let down for a longer arm
            p, dvec, r = C.cuffs[1]
            C.round(g.tube([p, p + dvec * 0.12], [r * 1.02, r * 0.98], n=7), mat("cloth_patch_b"))
    elif style == "figure":        # it stands as someone before stood: a little of them is still in it
        f = field("shade", 1.3)
        C.round(g.ico(Vector((0, 0.0, L + 0.2 * size)), 0.12 * size, sub=2, scale=(0.85, 0.95, 1.15)), f)
        C.round(g.tube([Vector((0, 0, L - 0.02)), Vector((0, 0, L + 0.1 * size))], [0.06, 0.05], n=6), f)
        for s in (1, -1):
            if s in C.cuffs:
                p, dvec, r = C.cuffs[s]
                C.round(g.ico(p + dvec * 0.05, r * 0.8, sub=1, scale=(1, 1, 1.3)), f)
    elif style == "tokens":        # twelve small marks inside the collar, one from each
        for i in range(12):
            a = -PI * 0.86 + 2 * PI * 0.86 * i / 11
            c = C.at(0.1, a, 0.016)
            m = (brass, mat("bone"), mat("cloth_patch_a"), field("token", 2.0), mat("cloth_patch_b"), mat("wax"))[i % 6]
            C.round(g.ico(c, 0.026 * size, sub=0, scale=(1.0, 1.0, 1.2)), m)
            C.round(g.tube([c + Vector((0, 0, 0.02)), c + Vector((0, 0, 0.07))], [0.004, 0.004], n=3), mat("thread"))
    elif style == "whiskers":      # fine whiskers of thread along the collar's edge, that stir at sounds
        c_style, k = opt(spec.get("collar", "turned"))
        tips = []
        if c_style in ("ear", "ears"):
            for s in (1, -1):
                for (x, y, z) in ((0.2, 0.06, 0.2), (0.36, 0.07, 0.36), (0.5, 0.05, 0.3), (0.53, 0.03, 0.12)):
                    tips.append((Vector((s * x * k, y, L + z * k)), Vector((s * (x - 0.3), 0.0, z - 0.12)).normalized()))
        else:
            r = 0.46 * k if c_style == "spread" else 0.175
            zc = L + (0.12 if c_style == "spread" else 0.2 * k)
            for i in range(9):
                a = -2.3 + 4.6 * i / 8
                tips.append((Vector((r * math.sin(a), r * 0.92 * math.cos(a), zc + 0.05 * math.cos(a))), Vector((math.sin(a), math.cos(a), 0.5)).normalized()))
        for i, (b0, dv) in enumerate(tips):
            for j in (-1, 0, 1):
                tip = b0 + (dv + Vector((0, 0, 0.5 * j))).normalized() * (0.2 + 0.05 * (i % 2)) * size
                C.round(g.tube([b0, (b0 + tip) / 2 + Vector((0, 0, 0.02)), tip], [0.006, 0.005, 0.002], n=3), mat("thread"))
    elif style == "drops":         # water stands on it in beads
        for i in range(12):
            a = -2.8 + 5.6 * ((i * 0.618) % 1.0)
            d = 0.05 + 0.5 * ((i * 0.381) % 1.0)
            C.round(g.ico(C.at(d, a, 0.008), 0.016, sub=0), mat("steel_glint"))
    elif style == "current":       # a hem that moves as if there were a current in the room
        d = L - 0.04
        phi = C.gap(d)
        pts = [C.at(d, -(PI - phi) + 2 * (PI - phi) * i / 16, 0.01) for i in range(17)]
        C.round(g.tube(pts, [0.014] * 17, n=4), field("current", 1.8))
        pts2 = [C.at(d - 0.16, -(PI - phi) + 2 * (PI - phi) * i / 16, 0.008) for i in range(17)]
        C.round(g.tube(pts2, [0.007] * 17, n=3), field("current", 1.2))
    elif style == "mantle":        # a cape over the shoulders
        rings = []
        n = 13
        for d, out in ((-0.02, 0.012), (0.1, 0.04), (0.3 * size, 0.07), (0.44 * size, 0.09)):
            phi = 0.35
            outer = [C.at(max(d, -0.04), -(PI - phi) + 2 * (PI - phi) * i / (n - 1), out) + Vector((math.sin(-(PI - phi) + 2 * (PI - phi) * i / (n - 1)) * 0.06 * (d > 0.05), 0, 0)) for i in range(n)]
            inner = [p - (p - Vector((0, 0, p.z))).normalized() * 0.016 for p in outer]
            rings.append(outer + list(reversed(inner)))
        C.solid(g.loft(rings, caps=True, closed=True), lambda c, nrm: lining if (nrm.x * c.x + nrm.y * c.y) < -0.25 * math.hypot(c.x, c.y) else (main if spec.get("mantle") != "oil" else mat("cloth_oil")))
    else:
        raise ValueError("a coat cannot grow: " + str(style))


def _clasp_alone(C, spec):
    """The Starter: a coat's clasp and the scrap of cloth it still holds."""
    brass, main, under = C.brass, C.main, C.under
    zc = 0.25
    for s in (1, -1):
        # a plate of brass, a hand's breadth across, its corners worn round
        pts = [(s * 0.02, -0.04), (s * 0.03, 0.048), (s * 0.1, 0.06), (s * 0.15, 0.03), (s * 0.15, -0.03), (s * 0.1, -0.06)]
        if s < 0:
            pts = list(reversed(pts))
        rings = [[Vector((x, y0, zc + z)) for x, z in pts] for y0 in (-0.016, 0.006)]
        C.add(g.loft(rings, caps=True, closed=True), brass)
        for dz in (-0.036, 0.0, 0.036):
            C.round(g.ico(Vector((s * 0.132, -0.018, zc + dz)), 0.009, sub=0), mark("studs", main))
        # the scrap of the coat it still holds, hanging from it, its end torn
        cl = [Vector((s * 0.115, 0.014, zc + 0.05)), Vector((s * 0.15, 0.022, zc - 0.05)), Vector((s * 0.175, 0.02, zc - 0.15)), Vector((s * 0.215, 0.03, zc - 0.24))]
        C.add(strap(cl, [0.13, 0.16, 0.15, 0.1], 0.018, up=X), main)
        for j, dx in enumerate((-0.036, 0.0, 0.036)):
            b0 = cl[3] + Vector((dx, 0, 0.004))
            C.add(g.blade(b0, b0 + Vector((dx * 0.4 + s * 0.012, 0.0, -0.045 - 0.016 * (j % 2))), 0.042, normal=Y), main)
        C.round(g.tube([p + Vector((s * 0.045, -0.013, 0)) for p in cl[:3]], [0.005] * 3, n=3), mark("stitch", main))
        C.round(g.tube([p + Vector((-s * 0.045, -0.013, 0)) for p in cl], [0.005] * 4, n=3), field("weave", 1.7))
    # the hook and the ring it closes on, and the one small eye in the metal
    C.round(g.tube([Vector((-0.04, -0.018, zc + 0.005)), Vector((0.0, -0.034, zc + 0.022)), Vector((0.05, -0.026, zc + 0.012)), Vector((0.055, -0.018, zc - 0.02))], [0.012, 0.012, 0.011, 0.008], n=5), brass)
    C.round(ringtube(Vector((0.07, -0.018, zc)), 0.03, 0.03, 0.008, n=10, u=X, v=Z), brass)
    C.add_items(eye(Vector((-0.09, -0.02, zc)), 0.034, lids=brass))
    C.wear = (Vector((0, 0.22, zc)), None)
    return {"socket_head": ((0, 0, zc + 0.06), None), "socket_eyes": ((0, -0.03, zc + 0.02), None), "socket_back": ((0, 0.03, zc), None), "socket_body": ((0, -0.03, zc - 0.06), None)}


def build(form_id, level, spec, base):
    kit.reset()
    C = Coat(form_id, spec)
    if spec.get("kind") == "clasp":
        socks = _clasp_alone(C, spec)
        return finish(C, form_id, base, spec, sockets=socks)
    L = C.L
    C.shell()
    sl = spec.get("sleeves", "hang")
    left, right = (sl if isinstance(sl, (list, tuple)) else (sl, sl))
    arm = float(spec.get("arm", 1.0))
    C.sleeve(1, left, arm)
    C.sleeve(-1, right, arm)
    c_style, c_size = opt(spec.get("collar", "turned"))
    C.collar(c_style, c_size)
    for style, size in each(spec.get("grown")):
        grow(C, style, size, spec)
    C.clasp(float(spec.get("clasp", 1.0)))
    C.wear = (Vector((0, 0.1, L - 0.02)), None)
    socks = {
        "socket_head": ((0, 0.0, L + 0.22), None), "socket_eyes": ((0, -0.12, L + 0.12), None), "socket_mouth": ((0, -0.12, L + 0.04), None),
        "socket_throat": ((0, -0.13, L - 0.06), None), "socket_light": (tuple(C.at(0.3, PI, 0.03)), None), "socket_back": (tuple(C.at(0.2, 0.0, 0.03)), None),
        "socket_body": (tuple(C.at(0.4, PI, 0.03)), None), "socket_tail": (tuple(C.at(L - 0.1, 0.0, 0.02)), None),
        "socket_arm_l": ((0.3 * C.shw + 0.04, 0, L - 0.02), None), "socket_arm_r": ((-0.3 * C.shw - 0.04, 0, L - 0.02), None),
        "socket_limb_fl": (tuple(C.at(L - 0.02, PI * 0.8, 0.0)), None), "socket_limb_fr": (tuple(C.at(L - 0.02, -PI * 0.8, 0.0)), None),
        "socket_keepsake": (tuple(C.at(0.22, PI, 0.03)), None),
    }
    for s, tag in ((1, "l"), (-1, "r")):
        if s in C.cuffs:
            socks["socket_hand_" + tag] = (tuple(C.cuffs[s][0]), None)
    socks["socket_grip"] = socks.get("socket_hand_r", socks["socket_back"])
    return finish(C, form_id, base, spec, sockets=socks)
