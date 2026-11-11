"""WILDLINE genius lines, the armors: the Coat (docs/genius-lines.md, "The armors").
lines_armors.py loads this file; what the conventions are, and what `wear` means, is said there.

A coat stands as if one of the game's people wore it and no one does: its hem at z = 0, the
wearer's middle up the Z axis, their front to -Y. `length` is from the shoulders to the hem.
Every coat keeps at its throat the clasp it grew from, and the eye in the clasp: that is where
it is alive, and it blinks.

The second pass (docs/genius-lines.md, "The second pass"):

  its Path's colour   the lining, and the trims its Path keeps (`trim`: hem, facing, cuffs,
                      collar, piping, yoke), in the materials accent*
  how it holds itself `sleeves` (a gesture for each arm), `lean` and `turn`: a coat is alive,
                      and no two stand alike
  what moves          the eye blinks, a sleeve that hangs sways, the tag on its clasp sways
  the worn piece      a coat that is worn is not the whole coat hung down a back: it is a
                      mantle, the coat's own collar and a short cape over the shoulders, in
                      its Path's cut and colour and carrying its form's sign (`worn`; Mantle)
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z
import genius_kit as kit
from genius_kit import mat, field, mark, STAND
from genius_relics import strap, ringtube
import genius_relics as rel
from lines_armors import Piece, eye, opt, each, lathe_at, art_size, SOFT, log

PI = math.pi

# How each arm is held: where the elbow and the cuff are from the shoulder, as (out to its own
# side, to the front, down). A coat with nobody in it still has a way of standing.
SLEEVES = {
    "hang": ((0.07, -0.02, 0.43), (0.08, 0.07, 0.90)),
    "flat": ((0.035, -0.01, 0.45), (0.04, 0.0, 0.97)),            # empty, pressed flat
    "trail": ((0.08, -0.02, 0.52), (0.1, 0.06, 1.2)),             # a sleeve let down for a longer arm
    "reach": ((0.07, 0.08, 0.35), (-0.06, 0.52, 0.15)),           # reaching to take hold
    "spread": ((0.34, 0.0, 0.15), (0.7, 0.05, 0.35)),             # held wide: an embrace
    "back": ((0.06, -0.2, 0.37), (0.07, -0.4, 0.75)),             # swept back
    "akimbo": ((0.32, -0.08, 0.34), (0.1, 0.1, 0.56)),            # a fist on its hip
    "tuck": ((0.17, -0.03, 0.4), (0.03, 0.13, 0.68)),             # a hand in a pocket
    "raise": ((0.24, 0.04, -0.04), (0.33, 0.1, -0.52)),           # an arm up: hailing
    "cup": ((0.27, 0.0, 0.08), (0.2, 0.06, -0.26)),               # a hand to its ear
    "throat": ((0.2, 0.14, 0.26), (0.02, 0.2, -0.02)),            # a hand to its own collar
    "point": ((0.08, 0.26, 0.26), (0.05, 0.68, 0.1)),             # level, to the front
    "hold": ((0.1, 0.14, 0.36), (0.0, 0.44, 0.4)),                # holding a thing out, low
    "fold": ((0.15, 0.15, 0.37), (-0.24, 0.25, 0.3)),             # folded across itself
    "heart": ((0.17, 0.11, 0.33), (-0.13, 0.21, 0.13)),           # a hand laid on its breast
    "behind": ((0.11, -0.15, 0.38), (-0.15, -0.21, 0.56)),        # hands behind its back
    "low": ((0.27, 0.03, 0.3), (0.48, 0.07, 0.55)),               # out and down: holding itself open
    "fore": ((0.07, 0.17, 0.4), (0.06, 0.42, 0.72)),              # swung forward in a stride
    "aft": ((0.07, -0.17, 0.4), (0.07, -0.36, 0.76)),             # swung back in a stride
    "grab": ((0.38, 0.14, 0.14), (0.92, 0.36, 0.06)),             # stretched out further than an arm goes, to take hold of a wrist
    "wrap": ((0.2, 0.2, 0.36), (-0.32, 0.27, 0.2)),               # wrapped round itself, high: it is cold
}
SWAYS = ("hang", "flat", "trail")          # a sleeve that only hangs is free to sway


class Coat(Piece):
    fit = 1.0            # how much wider its collar is than the coat's own (the worn piece's is wider)

    def __init__(self, form_id, spec):
        Piece.__init__(self, form_id)
        g_ = lambda k, d: float(spec.get(k, d))  # noqa: E731
        self.spec = spec
        self.L = g_("length", 1.5)
        self.flare, self.chest, self.waist, self.shw = g_("flare", 0.12), g_("chest", 1.0), g_("waist", 1.0), g_("shoulders", 1.0)
        self.open, self.cut, self.wave, self.rag = g_("open", 0.05), g_("cut", 0.0), g_("wave", 0.0), g_("rag", 0.0)
        self.taper = g_("taper", 0.0)
        sw, bd = spec.get("sweep", [0, 0]), spec.get("bend", [0, 0])
        self.sweep, self.bend = (float(sw[0]), float(sw[1])), (float(bd[0]), float(bd[1]))
        er = spec.get("ears", [1, 1])
        self.ears = (float(er[0]), float(er[1]))
        self.main, self.under, self.brass = mat("leather"), mat("leather_dark"), mat("metal_brass")
        self.cloth = {"oil": mat("cloth_oil"), "dust": mat("cloth_dust"), "wool": mat("cloth_wool")}.get(spec.get("mantle"))       # what its cape is made of, where it is not the coat's own stuff
        # its Path's colour (the builder has put the ramp's steps in the palette for this form)
        self.acc, self.acc_d, self.acc_l, self.acc_p, self.acc_x = mat("accent"), mat("accent_dark"), mat("accent_light"), mat("accent_pale"), mat("accent_deep")
        self.tone = spec.get("tone", "mid")
        # what it is lined with shows wherever it is turned back (collar, lapels, the front as it
        # opens): its Path's colour. A lining of the field's light stays at those edges, so the
        # coat keeps its form; `storm` is light all through; `fur` is pelt.
        kind = spec.get("lining", "plain")
        self.lining = {"plain": self.acc, "red": self.acc, "field": field("lining", 1.3), "storm": field("lining", 1.3), "fur": mat("pelt_light")}[kind]
        self.inside = self.acc_d if kind in ("field", "storm") else (self.acc if kind in ("plain", "red") else self.lining)
        self.trim = [t for t in (spec.get("trim") or [])]
        self.cuffs = {}          # side -> (where the cuff ends, the way the sleeve runs there, its radius)
        self.movers = []         # (kind, what, [(geometry, material)], pivot, side): what the game moves
        self.raw = {}            # material name -> [material, geometry]: cloth of one face (sheet)

    # --- what it is made of ---------------------------------------------------------------
    def add(self, geo, material, smooth=None):
        if smooth is None and material.name.startswith("accent"):
            smooth = True                      # the Path's colour is cloth
        Piece.add(self, geo, material, smooth)

    def solid(self, geo, pick):
        ob = Piece.solid(self, geo, pick)
        names = [m.name for m in ob.data.materials]
        for p in ob.data.polygons:
            if names[p.material_index].startswith("accent"):
                p.use_smooth = True
        return ob

    def sheet(self, geo, material):
        """Cloth of one face, its faces already turned the right way out (the game draws both
        sides of everything here; a sheet's lining, where it has one, is another sheet)."""
        if geo and geo[0]:
            cur = self.raw.get(material.name)
            self.raw[material.name] = [material, g.merge(cur[1] if cur else None, geo)]

    def flush(self):
        """The sheets as objects, to be joined with the rest."""
        for i, (material, geo) in enumerate(self.raw.values()):
            me = bpy.data.meshes.new("%s_sheet%d" % (self.name, i))
            me.from_pydata([tuple(p) for p in geo[0]], [], [tuple(f) for f in geo[1]])
            me.update()
            for p in me.polygons:
                p.use_smooth = True
            ob = bpy.data.objects.new(me.name, me)
            bpy.context.collection.objects.link(ob)
            me.materials.append(material)
            self.objects.append(ob)
        self.raw = {}

    def skin(self, outer, inner, k0, main, lining, step=1):
        """A cloth of two faces from its rings (top to edge, each from its right front round the
        back to its left front): its outside; its lining from ring k0 down; and its edge, where
        the two meet at the hem and down the two fronts."""
        self.sheet(g.loft(outer, caps=False, closed=False), main)
        last = len(outer) - 1
        idx = [i for i in range(k0, last + 1) if (i - k0) % step == 0 or i == last]      # (a lining is made of fewer rings: it is seen less)
        if len(idx) > 1:
            self.sheet(g.loft([list(reversed(inner[i])) for i in idx], caps=False, closed=False), lining)
        verts, faces = [], []

        def strip(a_pts, b_pts):
            off, m = len(verts), len(a_pts)
            verts.extend(list(a_pts) + list(b_pts))
            for i in range(m - 1):
                faces.append((off + i, off + i + 1, off + m + i + 1, off + m + i))
        strip(outer[-1], inner[-1])
        strip([outer[i][0] for i in idx], [inner[i][0] for i in idx])
        strip([inner[i][-1] for i in idx], [outer[i][-1] for i in idx])
        self.sheet((verts, faces), main)

    def band_on(self, points, width, material, up=Z, face=None):
        """A flat band lying on the cloth through points, `width` across (along `up`): one face,
        turned to look the way `face` does (or, round the coat with the angle, outward)."""
        pts = [Vector(p) for p in points]
        m = len(pts)
        verts, faces, sides = [], [], []
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]).normalized()
            side = Vector(up).cross(d).normalized()
            u2 = d.cross(side).normalized()
            w = width[i] if isinstance(width, (list, tuple)) else width
            verts += [p + u2 * (w / 2), p - u2 * (w / 2)]
            sides.append(side)
        flip = face is not None and sides[m // 2].dot(Vector(face)) < 0
        for i in range(m - 1):
            f = (2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1)
            faces.append(tuple(reversed(f)) if flip else f)
        self.sheet((verts, faces), material)

    def hand(self, default):
        """Which hand holds what it holds (`hand`: "l" or "r"): 1 its left, -1 its right."""
        return {"l": 1, "r": -1}.get(self.spec.get("hand"), default)

    def tones(self):
        """The step of its Path's colour its broad trims take, and the step of the line beside
        them: a Path wears the middle of its ramp, and each Advancement its own step of it."""
        return {"mid": (self.acc, self.acc_l), "dark": (self.acc_d, self.acc_l), "light": (self.acc_l, self.acc_d), "pale": (self.acc_p, self.acc)}[self.tone]

    def move(self, kind, what, items, pivot, side=""):
        """A piece of it the game moves (docs/genius-lines.md, "What moves")."""
        items = [(geo, m) for geo, m in items if geo and geo[0]]
        if items:
            self.movers.append((kind, what, items, Vector(pivot), side))

    def build(self, M=None):
        """One object, stood on its lowest point: and what moves is part of what stands."""
        self.flush()
        ob = Piece.build(self, M)
        low = 0.0
        for kind, what, items, pivot, side in self.movers:
            for geo, m in items:
                low = min([low] + [(self.lift @ Vector(v)).z for v in geo[0]])
        if low < 0.0:
            up = Matrix.Translation((0, 0, -low))
            ob.data.transform(up)
            ob.data.update()
            self.lift = up @ self.lift
        return ob

    def moving(self, T):
        """The pieces that move, made where the body now stands (the geometry is turned, not
        the object: a piece's own up stays the model's)."""
        import genius_lines as gl
        return [gl.moving(kind, what, [(g.moved(geo, T), m) for geo, m in items], T @ pivot, side=side) for kind, what, items, pivot, side in self.movers]

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
            rx, ry = rows[0][1], rows[0][2]
            for (d0, x0, y0), (d1, x1, y1) in zip(rows, rows[1:]):
                if d <= d1:
                    f = max(0.0, (d - d0) / (d1 - d0))
                    f = f * f * (3 - 2 * f)          # eased from one measure to the next
                    rx, ry = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                    break
        t = self.t(d)
        if self.taper:               # its skirts draw in toward the hem: a wisp
            k = max(0.06, 1.0 - self.taper * t ** 1.4)
            rx, ry = rx * k, ry * k
        w = math.sin(PI * max(0.0, min(1.0, d / self.L)))        # a bow of its whole length: most at its middle
        return rx, ry, self.sweep[0] * t * t + self.bend[0] * w, self.sweep[1] * t * t - self.bend[1] * w

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

    def fall(self, a):
        """How far below the shoulders its edge is, round it (a coat's hem is level)."""
        return self.L

    def hem(self, a, up=0.05, out=0.007):
        """A place on its edge: `up` above it, `out` from the cloth."""
        d = self.fall(a) - up
        p = self.at(d, a, out)
        if self.rag:
            p.z += self.rag * 0.16 * abs(math.sin(3.5 * a + 0.5)) * max(0.0, 1.0 - up / 0.2)
        return p

    def hem_pts(self, up=0.05, out=0.007, n=17):
        phi = self.gap(self.L - up)
        return [self.hem(-(PI - phi) + 2 * (PI - phi) * i / (n - 1), up, out) for i in range(n)]

    def shell(self, n=21, thick=0.02):
        L = self.L
        ds = [d for d in (-0.05, 0.0, 0.09, 0.2, 0.36, 0.52, 0.64, 0.77) if d < L - 0.04]
        d = 0.77
        while d + 0.2 < L - 0.04:
            d += 0.2
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
            rings.append((outer, inner))
        # where it stands open, all of what it is lined with can be seen; where it does not, a hand's breadth at its hem
        stands_open = self.open + self.cut >= 0.15
        self.skin([r[0] for r in rings], [r[1] for r in rings], 0 if stands_open else len(rings) - 3, self.main, self.inside, step=2 if stands_open else 1)
        self.round(g.ico((0, 0, L - 0.03), 0.1, sub=1, scale=(1.0, 0.9, 0.15)), mat("void"))
        # the seams of it: its partner may show them pale
        st = None
        for s in (1, -1):
            st = g.merge(st, g.tube([self.at(-0.04, s * 0.5 * PI, 0.006), self.at(0.0, s * 0.5 * PI, 0.008) + Vector((s * 0.0, 0, 0.005))], [0.005, 0.005], n=3))
        back = [self.at(d, 0.0, 0.006) for d in ds if 0.0 <= d]
        if len(back) > 1:
            st = g.merge(st, g.tube(back, [0.005] * len(back), n=3))
        self.round(st, mark("stitch", self.main))

    def trims(self):
        """Its Path's colour where it shows on the outside: the same places down a whole Path."""
        L, tr = self.L, self.trim
        ds = [d for d in (0.03, 0.2, 0.36, 0.52, 0.64, 0.77) if d < L - 0.1]
        d = 0.77
        while d + 0.2 < L - 0.1:
            d += 0.2
            ds.append(d)
        ds.append(L - 0.03)
        broad, line = self.tones()
        N = 21
        if "hem" in tr:              # a broad band at the hem, and a line above it
            self.band_on(self.hem_pts(0.075, 0.009, N), 0.13, broad)
            self.band_on(self.hem_pts(0.16, 0.011, N), 0.022, line)
        if "hem2" in tr:             # two bands
            for up in (0.045, 0.15):
                self.band_on(self.hem_pts(up, 0.009, N), 0.065, broad)
        if "dags" in tr:             # a hem of points
            phi = self.gap(L)
            m = 13
            for i in range(m):
                a = -(PI - phi - 0.08) + 2 * (PI - phi - 0.08) * i / (m - 1)
                b0, tip, nrm = self.hem(a, 0.012, 0.009), self.hem(a, 0.25, 0.011), self.normal(L - 0.1, a)
                sd = Vector((0, 0, 1)).cross(nrm).normalized() * 0.075
                self.sheet(([b0 - sd, b0 + sd, tip], [(0, 1, 2)]), broad)
            self.band_on(self.hem_pts(0.014, 0.011, N), 0.024, line)
        if "facing" in tr:           # the front edges faced with it
            for s in (1, -1):
                pts = [self.at(d, s * (PI - self.gap(d) - 0.1), 0.009) for d in ds]
                self.band_on(pts, 0.1, broad, up=X, face=(0, -1, 0))
        if "piping" in tr:           # a bright line along every edge: a dark coat's outline
            self.round(g.tube(self.hem_pts(0.012, 0.012, N), 0.013, n=4), self.acc_l)
            for s in (1, -1):
                pts = [self.at(d, s * (PI - self.gap(d) - 0.012), 0.012) for d in ds]
                self.round(g.tube(pts, 0.013, n=4), self.acc_l)
        if "yoke" in tr:             # a yoke across the shoulders
            rings, m = [], 15
            for d, out in ((-0.03, 0.01), (0.05, 0.02), (0.16, 0.024), (0.24, 0.024)):
                phi = 0.22
                rings.append([self.at(d, -(PI - phi) + 2 * (PI - phi) * i / (m - 1), out) for i in range(m)])
            self.sheet(g.loft(rings, caps=False, closed=False), broad)
            self.band_on([p + Vector((0, 0, 0.004)) for p in rings[-1]], 0.02, line)
        if "stripe" in tr:           # a stripe down each side seam
            for s in (1, -1):
                pts = [self.at(d, s * 0.5 * PI, 0.009) for d in ds]
                self.band_on(pts, 0.08, broad, up=Y, face=(s, 0, 0))
        if "spine" in tr:            # a broad stripe down the middle of the back, hem to nape
            pts = [self.at(d, 0.0, 0.009) for d in ds]
            self.band_on(pts, 0.16, broad, up=X, face=(0, 1, 0))

    def sleeve(self, side, style, arm=1.0):
        if style in (None, "none"):
            return
        s, L, shx = side, self.L, 0.3 * self.shw
        sh = Vector((s * (shx - 0.02), 0.0, L - 0.05))
        (eo, ef, ed), (co, cf, cd) = SLEEVES[style]
        el, cu = Vector((s * (shx + eo), -ef, L - ed)), Vector((s * (shx + co), -cf, L - cd))
        broad, line = self.tones()
        if style == "flat":
            path, radii = [sh, el, cu], [0.094 * arm, 0.08 * arm, 0.075 * arm]
            items = [(g.tube(path, radii, n=8, flat=0.3, up=Y), self.main)]
        else:                              # an arm's own bend: a curve through the elbow, not a hinge
            ctrl = el * 2.0 - (sh + cu) * 0.5
            path = [sh * ((1 - q) ** 2) + ctrl * (2 * q * (1 - q)) + cu * (q * q) for q in (0.0, 0.2, 0.42, 0.64, 0.84, 1.0)]
            radii = [r * arm for r in (0.1, 0.095, 0.089, 0.083, 0.078, 0.075)]
            items = [(g.tube(path, radii, n=8), self.main)]
        d = (path[-1] - path[-2]).normalized()
        if style != "flat":
            r = radii[-1]
            if "cuffs" in self.trim:       # a deep cuff turned back, in its Path's colour
                items.append((lathe_at([(r * 1.04, -0.17), (r * 1.2, -0.16), (r * 1.27, 0.004), (r * 0.92, 0.01)], path[-1], d, n=8), broad))
            else:
                items.append((lathe_at([(r * 1.02, -0.07), (r * 1.13, -0.06), (r * 1.16, 0.006), (r * 0.9, 0.008)], path[-1], d, n=8), mark("lining", self.under)))
            items.append((lathe_at([(r * 0.92, 0.0), (0.0, 0.012)], path[-1], d, n=8), mat("void")))
            if "bands" in self.trim:       # two bands of it round the upper arm
                for i in (2, 3):
                    dd = (path[i + 1] - path[i - 1]).normalized()
                    rr = radii[i]
                    items.append((lathe_at([(rr * 1.02, -0.026), (rr * 1.09, -0.02), (rr * 1.09, 0.02), (rr * 1.02, 0.026)], path[i], dd, n=8), broad))
        if style in SWAYS:                 # it hangs free, and stirs
            self.move("sway", "sleeve", items, sh, side="l" if s > 0 else "r")
        else:
            for geo, m in items:
                self.round(geo, m)
        self.cuffs[side] = (path[-1], d, radii[-1])

    # --- its collar ---------------------------------------------------------------------
    def dark(self, size):
        """The dark a high collar holds: its half-width, half-depth, half-height, and the height of its middle."""
        rim = 0.7 + 0.3 * size
        rz = 0.182 * max(1.0, size)
        return 0.66 * 0.24 * rim, 0.66 * 0.22 * rim, rz, self.L + 0.46 * size - 0.9 * rz

    def collar(self, style, size=1.0):
        L = self.L
        main, lining = self.main, self.lining
        broad, line = self.tones()
        out_m = broad if "collar" in self.trim else main
        if style in (None, "none"):
            return

        def band(z0, z1, r0, r1, gap=0.5, n=17, thick=0.016, tilt=0.0, outer=None):
            """A collar standing round the neck: open at the front, flaring as it rises."""
            rings = []
            for z, (rx, ry) in ((z0, r0), ((z0 + z1) / 2, ((r0[0] + r1[0]) / 2, (r0[1] + r1[1]) / 2)), (z1, r1)):
                ro, ri = [], []
                for i in range(n):
                    a = -(PI - gap) + 2 * (PI - gap) * i / (n - 1)
                    lift = tilt * (z - z0) * math.cos(a)          # higher at the back
                    ro.append(Vector((rx * math.sin(a), ry * math.cos(a) + 0.006, L + z + lift)))
                    ri.append(Vector(((rx - thick) * math.sin(a), (ry - thick) * math.cos(a) + 0.006, L + z + lift)))
                rings.append(ro + list(reversed(ri)))
            self.solid(g.loft(rings, caps=True, closed=True), lambda c, nrm: lining if (nrm.x * c.x + nrm.y * c.y) < -0.25 * math.hypot(c.x, c.y) else (outer or out_m))
        if style in ("turned", "whiskers", "frost"):
            band(-0.03, 0.2 * size, (0.115, 0.105), (0.175 * (0.8 + 0.2 * size), 0.16 * (0.8 + 0.2 * size)), tilt=0.25)
        elif style == "stand":
            band(-0.03, 0.09 * size, (0.112, 0.102), (0.118, 0.108), gap=0.3)
        elif style == "high":        # a collar that stands up by itself, and is full of dark, to the brim
            band(-0.03, 0.46 * size, (0.125, 0.115), (0.24 * (0.7 + 0.3 * size), 0.22 * (0.7 + 0.3 * size)), gap=0.62, tilt=0.2)
            rx, ry, rz, zc = self.dark(size)
            self.round(g.ico((0, 0.02, zc), 1.0, sub=2, scale=(rx, ry, rz)), mat("void"))
        elif style == "spread":      # spread wide, flat as a dish, to hear with
            band(-0.02, 0.12, (0.115, 0.105), (0.46 * size, 0.42 * size), gap=0.3, tilt=0.5, n=19)
        elif style in ("ear", "ears"):
            band(-0.03, 0.1, (0.112, 0.102), (0.13, 0.12), gap=0.4)
        elif style == "hood":        # a hood, and the dark where a face would be
            c = Vector((0, 0.03, L + 0.19 * size))
            self.round(g.ico(c, 0.215 * size, sub=2, scale=(0.92, 1.0, 1.12)), main)
            self.round(g.cone(c + Vector((0, 0.12 * size, 0.16 * size)), c + Vector((0, 0.3 * size, 0.12 * size)), 0.1 * size, n=7), main)       # its peak, hanging behind
            face = c + Vector((0, -0.15 * size, -0.03 * size))
            self.round(g.ico(face, 0.1 * size, sub=2, scale=(1.2, 0.82, 1.5)), mat("void"))
            self.round(ringtube(face + Vector((0, -0.04 * size, 0)), 0.124 * size, 0.154 * size, 0.022 * size, n=14, u=X, v=Z), line if "collar" in self.trim or True else main)
            band(-0.04, 0.06, (0.125, 0.115), (0.2, 0.19), gap=0.3)
        elif style == "souwester":   # an oilskin's hat, its brim long behind to shed the rain down its back; and the dark under it
            oil = self.cloth or main
            c = Vector((0, 0.02, L + 0.2 * size))
            self.round(g.ico(c + Vector((0, 0, 0.05 * size)), 0.17 * size, sub=2, scale=(1.0, 1.05, 0.95)), oil)
            rings = []
            for r_, z_, back_ in ((0.16, 0.06, 0.0), (0.3, 0.0, 0.06), (0.4, -0.075, 0.13), (0.39, -0.09, 0.13), (0.29, -0.02, 0.06), (0.15, 0.03, 0.0)):
                rings.append([c + Vector((r_ * size * math.sin(q), (r_ * (1.0 + 0.35 * max(0.0, math.cos(q))) * math.cos(q) + back_ * 0.4) * size, (z_ - 0.05 * max(0.0, math.cos(q)) * (r_ > 0.2)) * size))
                              for q in [2 * PI * i / 16 for i in range(16)]])
            self.round(g.loft(rings, caps=False, closed=True), oil)
            self.round(g.tube(rings[2] + [rings[2][0]], [0.011 * size] * 17, n=4), line)
            self.round(g.ico(c + Vector((0, -0.02, -0.07 * size)), 1.0, sub=2, scale=(0.115 * size, 0.11 * size, 0.13 * size)), mat("void"))
            band(-0.04, 0.09, (0.125, 0.115), (0.15, 0.14), gap=0.3, outer=oil)
        elif style == "fur":         # a collar of pelt
            for i in range(11):
                a = -2.4 + 4.8 * i / 10
                b0 = Vector((0.13 * math.sin(a), 0.12 * math.cos(a), L + 0.02))
                self.add(g.blade(b0, b0 + Vector((0.16 * math.sin(a), 0.15 * math.cos(a), 0.1 + 0.04 * (i % 2))) * size, 0.13, normal=Vector((math.sin(a), math.cos(a), 0.8))), mat("pelt_dark") if i % 2 else mat("pelt_light"), smooth=True)
        elif style == "cape":
            band(-0.03, 0.1, (0.112, 0.102), (0.14, 0.13), gap=0.4)
        else:
            raise ValueError("no such collar: " + str(style))
        if style in ("ear", "ears"):  # a collar shaped like the rim of an ear, either side (`ears`: how large each is)
            x0 = 0.1
            for s, k in ((1, size * self.ears[0]), (-1, size * self.ears[1])):
                path = [Vector((s * x0, 0.03, L - 0.01)), Vector((s * (x0 + 0.1 * k), 0.06, L + 0.2 * k)), Vector((s * (x0 + 0.26 * k), 0.07, L + 0.36 * k)), Vector((s * (x0 + 0.4 * k), 0.05, L + 0.3 * k)),
                        Vector((s * (x0 + 0.43 * k), 0.03, L + 0.12 * k)), Vector((s * (x0 + 0.32 * k), 0.02, L - 0.0 * k)), Vector((s * (x0 + 0.2 * k), 0.02, L - 0.02))]
                self.round(g.tube(path, [0.03, 0.036 * k, 0.04 * k, 0.04 * k, 0.036 * k, 0.03 * k, 0.02], n=7), out_m)
                self.round(g.ico(Vector((s * (x0 + 0.23 * k), 0.065, L + 0.16 * k)), 0.19 * k, sub=2, scale=(0.95, 0.1, 0.92)), lining)
                self.round(g.tube([Vector((s * (x0 + 0.14 * k), 0.04, L + 0.08 * k)), Vector((s * (x0 + 0.24 * k), 0.03, L + 0.2 * k)), Vector((s * (x0 + 0.32 * k), 0.03, L + 0.16 * k))], [0.018 * k, 0.022 * k, 0.012 * k], n=5), self.acc_d)
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

    def clasp(self, size=1.0, what="eye"):
        """The clasp it grew from, at its throat: a hook and an eye, and the eye is an eye. It
        looks out from under a heavy lid, and blinks; the tag that hangs from its ring is in
        its Path's colour, and stirs."""
        self.clasp_at(self.at(0.08, PI, 0.02), size, what)

    def clasp_at(self, c, k, what="eye"):
        f = Vector((0, -1, 0))
        r = 0.058 * k
        ec = c + Vector((-0.062 * k, -0.012, 0.0))
        # the plate the eye is set in, round; and the ring the hook closes on
        self.round(lathe_at([(r * 1.3, -0.004), (r * 1.42, 0.006), (r * 1.3, 0.016)], ec + Vector((0, 0.022, 0)), f, n=10), self.brass)
        rc = c + Vector((0.075 * k, -0.006, 0.0))
        self.round(ringtube(rc, 0.05 * k, 0.05 * k, 0.014 * k, n=10, u=X, v=Z), self.brass)
        self.round(g.tube([ec + Vector((r * 1.2, 0.0, 0.01 * k)), c + Vector((0.02 * k, -0.02, 0.022 * k)), rc + Vector((0.0, -0.012, -0.028 * k))],
                          [0.012 * k, 0.012 * k, 0.008 * k], n=4), self.brass)
        if what == "eye":
            for s in (1, -1):
                self.round(g.ico(ec + Vector((s * r * 0.95, 0.004, r * 1.05)), 0.011 * k, sub=0), mark("studs", self.main))
        # the eye: an iris of the field and its slit, which shut; a heavy lid above and a rim below, which stay
        iris = [(g.moved(g.ico((0, 0, 0), r, sub=2, scale=(1.0, 0.42, 1.0)), Matrix.Translation(ec)), field("eyes", 3.5)),
                (g.moved(g.ico((0, 0, 0), r * 0.4, sub=1, scale=(0.5, 0.5, 1.75)), Matrix.Translation(ec + f * (r * 0.33))), mat("eye_dark"))]
        self.move("blink", what, iris, ec)
        tilt = float(self.spec.get("brow", 8.0)) * PI / 180.0      # how its lid is set: lowered at its outer end, it is thinking
        a, b = ec + Vector((-r * 1.2, -r * 0.12, r * (0.5 - 1.2 * math.sin(tilt)))), ec + Vector((r * 1.2, -r * 0.12, r * (0.5 + 1.2 * math.sin(tilt))))
        mid = ec + Vector((0, -r * 0.5, r * 1.02))
        self.round(g.tongue([a, mid, b], [r * 0.2, r * 0.8, r * 0.2], thick=0.55, normal=f + Z * 0.7), self.brass)
        self.round(g.tongue([ec + Vector((-r * 1.15, -r * 0.1, -r * 0.3)), ec + Vector((0, -r * 0.42, -r * 0.98)), ec + Vector((r * 1.15, -r * 0.1, -r * 0.3))], [r * 0.14, r * 0.4, r * 0.14], thick=0.5, normal=f - Z * 0.6), self.brass)
        # a tag on a short chain, the size of a thumb
        top = rc + Vector((0.0, -0.01, -0.05 * k))
        _, line = self.tones()
        tag = [(g.merge(g.tube([top, top + Vector((0.0, -0.004, -0.045 * k))], [0.005, 0.005], n=3),
                        g.box(top + Vector((0, -0.006, -0.085 * k)), (0.05 * k, 0.008, 0.085 * k))), self.acc_l)]
        self.move("sway", "tag" if what == "eye" else "wtag", tag, top)

    def pocket(self, d, a, w=0.2, h=0.2, bulge=0.0, flap=True, material=None):
        material = material or self.main
        c, n = self.at(d, a, 0.012), self.normal(d, a)
        rz = math.atan2(-n.x, n.y)
        self.add(g.box(c + n * 0.008, (w, 0.03, h), rot=(0, 0, rz)), material)
        if bulge:
            self.round(g.ico(c + n * (0.02 + 0.03 * bulge) + Vector((0, 0, -0.02)), w * 0.42, sub=1, scale=(1.0, 0.5 * bulge + 0.2, 0.95)), material)
        if flap:
            self.add(g.box(c + n * 0.024 + Vector((0, 0, h * 0.42)), (w * 1.08, 0.022, h * 0.3), rot=(0, 0, rz)), self.acc_d)
            self.round(g.ico(c + n * 0.04 + Vector((0, 0, h * 0.3)), 0.012, sub=0), self.brass)
        return c, n


# what a mantle can carry of a coat's signs (the rest belong to the skirts and the sleeves)
ON_A_MANTLE = ("buttons", "buttons2", "offices", "pack", "dust", "stamps", "pelt", "rime", "pads", "lamp", "smoke", "lapels", "stars", "scorch",
               "epaulettes", "chain", "stock", "tokens", "whiskers", "drops", "current", "knife", "oath", "figure", "patches", "hook", "wind", "eyes", "items")


def grow(C, style, size, spec):
    L = C.L
    worn = C.fit > 1.0
    main, under, brass, lining = C.main, C.under, C.brass, C.lining
    iron = mat("metal_iron")
    if style == "belt":            # a belt, and its buckle; its end hangs free, and stirs
        d = 0.5
        phi = C.gap(d)
        pts = [C.at(d, -(PI - phi) + 2 * (PI - phi) * i / 12, 0.012) for i in range(13)]
        C.add(strap(pts, 0.06, 0.014, up=Z), under)
        bk = C.at(d, PI - phi - 0.12, 0.022)
        C.add(g.box(bk, (0.07, 0.02, 0.075)), brass)
        for i in (3, 6, 9):
            C.round(g.ico(pts[i] + (pts[i] - Vector((0, 0, pts[i].z))).normalized() * 0.008, 0.011, sub=0), mark("studs", main))
        end = bk + Vector((-0.02, -0.012, -0.03))
        C.move("sway", "belt", [(strap([end, end + Vector((-0.01, -0.004, -0.11 * size)), end + Vector((-0.02, 0.0, -0.22 * size))], 0.05, 0.012, up=X), under),
                                (g.box(end + Vector((-0.02, -0.002, -0.235 * size)), (0.056, 0.016, 0.03)), under)], end)
    elif style in ("buttons", "buttons2", "offices"):     # buttons; two rows; a button for every writ served
        rows = 1 if style == "buttons" else 2
        n = {"buttons": 4, "buttons2": 5, "offices": 11}[style]
        bottom = {"buttons": 0.62, "buttons2": 0.66, "offices": min(L - 0.12, 1.45)}[style]
        if worn:
            n, bottom = (3 if style != "offices" else 5), C.fall(PI) - 0.07
        for r_ in range(rows):
            for i in range(n):
                d = 0.14 + (bottom - 0.14) * i / (n - 1)
                a = PI - C.gap(d) - (0.1 if rows == 1 else 0.12)
                if rows == 2 and r_ == 1:
                    a = -(PI - C.gap(d) - 0.12)
                m = brass if style != "offices" or (i + r_) % 3 else field("writ", 1.8)
                C.round(g.ico(C.at(d, a, 0.014), 0.019 * size, sub=1, scale=(1, 1, 1)), m)
    elif style in ("pack", "bedroll"):   # what it carries between places: a roll at the back, and its strap
        up = 0.2 if style == "pack" and not worn else -0.06
        c = C.at(max(up, 0.02), 0.0, 0.09) + Vector((0, 0, max(0.0, -up)))
        k = size
        if worn:                   # worn, the roll lies across the top of the back, under the collar
            k = size * 0.72
            c = C.at(0.06, 0.0, 0.085 * k + 0.008, 0.0)
        C.round(g.tube([c + Vector((-0.23 * k, 0, 0)), c + Vector((-0.22 * k, 0, 0)), c, c + Vector((0.22 * k, 0, 0)), c + Vector((0.23 * k, 0, 0))], [0.03 * k, 0.078 * k, 0.085 * k, 0.078 * k, 0.03 * k], n=9), mat("cloth_wool"))
        for s in (1, -1):
            C.round(ringtube(c + Vector((s * 0.13 * k, 0, 0)), 0.09 * k, 0.09 * k, 0.013, n=10, u=Y, v=Z), C.acc_l)
        if not worn:
            C.add(strap([C.at(0.02, 0.6, 0.014), C.at(0.2, PI * 0.72, 0.016), C.at(0.46, PI - 0.45, 0.016)], 0.05, 0.012, up=Z), under)
            # a tin cup on a thong, that knocks as it walks
            top = c + Vector((0.2 * k, 0.03, -0.07 * k))
            C.move("sway", "cup", [(g.tube([top, top + Vector((0, 0, -0.08))], [0.004, 0.004], n=3), mat("metal_iron")),
                                   (lathe_at([(0.03, 0.0), (0.036, 0.008), (0.036, 0.07), (0.03, 0.07), (0.03, 0.012)], top + Vector((0, 0, -0.15)), Z, n=8), mat("metal_iron"))], top)
        else:
            C.add(strap([C.at(0.01, 0.9, 0.014), C.at(0.1, PI * 0.7, 0.016), C.at(0.2, PI - 0.5, 0.016)], 0.045, 0.012, up=Z), under)
    elif style == "frame":         # a pack-frame that stands above its shoulders, and what is lashed to it
        k = size
        for s in (1, -1):
            C.round(g.tube([C.at(0.5, s * 0.25, 0.1), C.at(0.0, s * 0.25, 0.1) + Vector((0, 0, 0.0)), C.at(0.0, s * 0.25, 0.1) + Vector((0, 0.0, 0.42 * k))], [0.016, 0.016, 0.014], n=5), mat("wood_dark"))
        for z, w in ((0.36 * k, 0.24), (0.14 * k, 0.26), (-0.2, 0.26)):
            c = C.at(0.0, 0.0, 0.11) + Vector((0, 0, z))
            C.round(g.tube([c + Vector((-w, 0.0, 0)), c + Vector((w, 0.0, 0))], [0.013, 0.013], n=4), mat("wood_dark"))
        c = C.at(0.0, 0.0, 0.17) + Vector((0, 0, 0.3 * k))
        C.round(g.tube([c + Vector((-0.26, 0, 0)), c, c + Vector((0.26, 0, 0))], [0.085, 0.1, 0.085], n=8), mat("cloth_wool"))
        for s in (1, -1):
            C.round(ringtube(c + Vector((s * 0.15, 0, 0)), 0.104, 0.104, 0.013, n=10, u=Y, v=Z), C.acc_l)
        C.round(g.ico(C.at(0.24, 0.0, 0.2), 0.19, sub=2, scale=(1.1, 0.7, 1.25)), under)
        C.add(g.box(C.at(0.2, 0.0, 0.32), (0.2, 0.03, 0.14)), C.acc_d)
        top = c + Vector((-0.24, 0.04, -0.09))
        C.move("sway", "pan", [(g.tube([top, top + Vector((0, 0, -0.1))], [0.004, 0.004], n=3), mat("cord")),
                               (g.ico(top + Vector((0, 0.0, -0.17)), 0.075, sub=1, scale=(1.0, 0.25, 1.0)), mat("metal_iron"))], top)
    elif style == "dust":          # dust on the hem from somewhere else
        C.band_on(C.hem_pts(0.07, 0.007, 17), 0.13 * size * (0.5 if worn else 1.0), mat("cloth_dust"))
    elif style == "stamps":        # a hem covered in post-marks, stamped one over another
        for row, (dd, off) in enumerate(((0.08, 0.0), (0.2, 0.5), (0.32, 0.2))[: 1 if worn else 3]):
            phi = C.gap(L - dd)
            n = 11
            for i in range(n):
                a = -(PI - phi - 0.1) + 2 * (PI - phi - 0.1) * (i + off) / n
                m = (mat("stamp_ink"), mat("paint_red"), mat("paint_pale"))[(i + row) % 3]
                C.round(g.ico(C.hem(a, dd, 0.006), (0.036 if worn else 0.05) * size, sub=1, scale=(1.0, 1.0, 1.0)), m)
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
        if worn:
            c = C.at(0.16, PI - 0.55, 0.03)
            C.round(g.tube([c, c + Vector((0.01, 0, 0.13))], [0.024, 0.018], n=6), mat("glass"))
            C.round(g.ico(c + Vector((0.01, 0, 0.145)), 0.017, sub=0), mat("wax"))
            return
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
        for row, (d, n, Lb) in enumerate(((0.02, 13, 0.22), (0.14, 15, 0.26), (0.3, 15, 0.22))[: (1 if worn else 2) + (size > 1.2)]):
            for i in range(n):
                a = -PI * 0.86 + 2 * PI * 0.86 * i / (n - 1)
                b0 = C.at(d, a, 0.0)
                nrm = C.normal(d, a)
                C.add(g.blade(b0, b0 + nrm * 0.1 * size + Vector((0, 0, -Lb * size * (0.6 if worn else 1.0))), 0.17 * size, normal=nrm + Vector((0, 0, 0.5)), belly=0.4), mat("pelt_dark") if (i + row) % 2 else mat("pelt_light"))
    elif style == "rime":          # frost that does not melt
        for i in range(12):
            a = -PI * 0.8 + 2 * PI * 0.8 * i / 11
            b0 = C.at(0.03, a, 0.02)
            nrm = C.normal(0.03, a)
            C.add(g.cone(b0, b0 + nrm * 0.07 + Vector((0, 0, 0.1 + 0.05 * (i % 3))) * size, 0.03, n=4), mat("frost"))
        C.add(strap(C.hem_pts(0.05, 0.006, 15), 0.1 * (0.6 if worn else 1.0), 0.008, up=Z), mat("frost"))
    elif style == "pads":          # padded at the elbows and shoulders with something like stone
        for s in (1, -1):
            sh = Vector((s * 0.3 * C.shw * C.fit, 0.0, L - 0.02))
            C.add(g.ico(sh + Vector((s * 0.03, 0, 0.02)), 0.15 * size, sub=1, scale=(1.1, 1.0, 0.62)), mat("stone_hide"))
            C.add(g.ico(sh + Vector((s * 0.03, 0, 0.07)), 0.09 * size, sub=0, scale=(1.1, 1.0, 0.6)), mat("stone_light"))
            if s in C.cuffs:
                p, dvec, r = C.cuffs[s]
                C.add(g.ico(p - dvec * 0.46 + Vector((s * 0.02, 0.05, 0)), 0.1 * size, sub=1, scale=(0.9, 1.0, 1.1)), mat("stone_hide"))
        C.add(g.box(C.at(0.25 if not worn else 0.16, 0.0, 0.03), (0.34, 0.06, 0.4 if not worn else 0.22)), mat("stone_plate"))
    elif style in ("lamp", "handlamp"):   # a lamp, for where the air is bad: at its collar, or held out
        r = 0.05 * size
        hs = C.hand(-1)
        if style == "handlamp" and hs in C.cuffs and not worn:
            p, dvec, rr = C.cuffs[hs]
            top = p + dvec * 0.03
            c = top + Vector((0, 0, -0.16))
            r = 0.062 * size
            C.move("sway", "lamp", [(g.tube([top, c + Vector((0, 0, r * 1.2))], [0.005, 0.005], n=3), iron),
                                    (lathe_at([(r * 0.5, 0.0), (r, 0.01), (r, 0.028), (r * 0.5, 0.034)], c + Vector((0, 0, -r - 0.03)), Z, n=8), brass),
                                    (g.ico(c, r, sub=2, scale=(1, 1, 1.15)), field("lamp", 3.6)),
                                    (lathe_at([(r * 0.85, 0.0), (r * 0.2, 0.035)], c + Vector((0, 0, r * 1.05)), Z, n=8), brass)], top)
            return
        c = C.at(0.16, PI - 0.5, 0.05)
        C.round(lathe_at([(r * 0.5, 0.0), (r, 0.01), (r, 0.028), (r * 0.5, 0.034)], c + Vector((0, 0, -r - 0.03)), Z, n=6), brass)
        C.round(g.ico(c, r, sub=1, scale=(1, 1, 1.15)), field("lamp", 3.6))
        C.round(lathe_at([(r * 0.8, 0.0), (r * 0.2, 0.03)], c + Vector((0, 0, r * 1.05)), Z, n=6), brass)
    elif style == "smoke":         # it is hard to say where it ends
        if worn:                   # worn, a few wisps trail from its points
            for i in range(5):
                a = -1.9 + 3.8 * i / 4
                b0 = C.hem(a, 0.01, 0.0)
                nrm = C.normal(C.fall(a), a)
                k = size * (0.8 + 0.3 * math.sin(i * 1.7))
                pts = [b0 + Vector((0, 0, 0.04)), b0 + nrm * 0.015 + Vector((0.01 * math.sin(i), 0, -0.04 * k)), b0 + nrm * 0.035 * k + Vector((0.02 * math.sin(i * 2.0), 0, -0.1 * k))]
                C.round(g.tongue(pts, [0.05, 0.04, 0.006], thick=0.3, normal=nrm), mat("smoke") if i % 2 else mat("shade_edge"))
            return
        for i in range(8):
            a = -2.6 + 5.2 * i / 7
            b0 = C.hem(a, 0.02, 0.0)
            nrm = C.normal(C.fall(a) - 0.02, a)
            k = size * (0.8 + 0.3 * math.sin(i * 1.7))
            pts = [b0 + Vector((0, 0, 0.1)), b0 + nrm * 0.04 * k + Vector((0, 0, -0.02)), b0 + nrm * 0.1 * k + Vector((0.03 * math.sin(i), 0, 0.12 * k)), b0 + nrm * 0.07 * k + Vector((0, 0, 0.3 * k))]
            C.add(g.tongue(pts, [0.12, 0.11, 0.07, 0.01], thick=0.3, normal=nrm), mat("smoke") if i % 3 else mat("shade_edge"), smooth=True)
    elif style == "ghost_sleeve":  # it leaves a sleeve where its partner was, and the sleeve takes the blow
        s = -1                     # where its own sleeve is not: the sleeve stands apart, an arm thrown up to ward
        base = Vector((s * (0.3 * C.shw + 0.34), -0.1, L - 0.2))
        el = base + Vector((s * 0.34, -0.06, -0.12))
        cu = el + Vector((s * 0.1, -0.1, 0.5))
        ctrl = el * 2.0 - (base + cu) * 0.5
        pts = [base * ((1 - q) ** 2) + ctrl * (2 * q * (1 - q)) + cu * (q * q) for q in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
        dv = (pts[-1] - pts[-2]).normalized()
        u_, v_ = g._frame(dv)
        its = [(g.tube(pts, [0.05, 0.085, 0.085, 0.08, 0.076, 0.074], n=8), mat("smoke")),
               (lathe_at([(0.066, 0.0), (0.0, 0.012)], pts[-1], dv, n=8), mat("void")),
               (ringtube(pts[2], 0.09, 0.09, 0.009, n=10, u=X, v=Y), field("pulse", 1.6)),
               (lathe_at([(0.076, -0.09), (0.09, -0.085), (0.094, 0.004), (0.07, 0.008)], pts[-1], dv, n=8), C.acc_l)]
        for i in range(4):         # and what is left of where it was torn from, trailing back toward the coat
            b0 = base + Vector((0.0, 0.0, 0.0))
            its.append((g.tongue([b0, b0 + Vector((-s * 0.1, 0.02 * i, 0.05 + 0.03 * i)), b0 + Vector((-s * 0.24, 0.03 * i, 0.03 * i - 0.03))], [0.1, 0.07, 0.01], thick=0.3, normal=Y), mat("shade_edge")))
        C.move("sway", "ghost", its, base)
    elif style == "knife":         # a hard straight line in the lining, a hand long
        d0 = 0.3 if not worn else 0.14
        a = PI - C.gap(d0) - 0.05
        hilt = C.at(d0, a, -0.03) + Vector((0.02, -0.02, 0))
        tip = hilt + Vector((0.0, 0.0, -0.36 * size * (0.4 if worn else 1.0)))
        C.add(g.tongue([hilt + Vector((0, 0, -0.06)), (hilt + tip) / 2, tip], [0.045, 0.04, 0.004], thick=0.2, normal=Y), mat("steel_polish"))
        C.round(g.tube([hilt + Vector((0, 0, -0.06)), hilt + Vector((0, 0, 0.06))], [0.016, 0.014], n=5), under)
        C.add(g.box(hilt + Vector((0, 0, -0.06)), (0.09, 0.02, 0.016)), brass)
        C.round(g.ico(hilt + Vector((0, 0, 0.07)), 0.018, sub=0), field("hilt", 2.6))
    elif style == "lapels":        # lapels, turned back to show what it is lined with; or cut sharp as blades
        k = size * (0.55 if worn else 1.0)
        for s in (1, -1):
            a = s * (PI - C.gap(0.1) - 0.02)
            top, low = C.at(0.0, a, 0.02), C.at(0.46 * k, s * (PI - C.gap(0.46 * k) - 0.02), 0.02)
            out = C.normal(0.2, s * (PI - 0.5))
            mid = (top + low) / 2 + out * 0.12 * k + Vector((0, -0.03, 0.05))
            C.add(g.tongue([top, mid, low], [0.05, 0.2 * k, 0.02], thick=0.14, normal=Vector((s * 0.3, -1, 0.1))), lining)
    elif style == "eyes":          # what looks out of the dark of its collar
        c_style, k = opt(spec.get("collar", "turned"))
        if worn:                   # worn, they are two points of light on the collar's rim, behind the wearer's ears
            for s in (1, -1):
                C.round(g.ico(Vector((s * 0.15 * C.fit, 0.1 * C.fit, L + 0.25 * k)), 0.024 * size, sub=1, scale=(1.2, 0.7, 0.8)), field("eyes", 4.0))
            return
        rx, ry, rz, zc = C.dark(k)
        el, az = math.radians(48), math.radians(38)       # high on the dark and to the front, over the collar's edge
        its = []
        for s in (1, -1):
            d = Vector((s * math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)))
            p = Vector((rx * d.x, 0.02 + ry * d.y, zc + rz * d.z)) + d * 0.006
            er = 0.3 * rx * min(size, 1.15)
            its.append((g.ico(p, er, sub=1, scale=(1.3, 0.6, 0.7)), field("eyes", 4.0)))
        C.move("blink", "eyes", its, (0, 0.02 - ry * 0.5, zc + rz * math.sin(el)))
    elif style == "stars":         # after dusk, the colour of whatever is behind it
        f = field("stars", 2.0)
        for i in range(14 if not worn else 8):
            a = -2.7 + 5.4 * ((i * 0.618) % 1.0)
            d = 0.25 + (L - 0.4) * ((i * 0.381 + 0.13) % 1.0) if not worn else 0.05 + (C.fall(a) - 0.1) * ((i * 0.381 + 0.13) % 1.0)
            C.round(g.ico(C.at(d, a, 0.006), 0.014 + 0.008 * (i % 3), sub=0), f)
    elif style == "wind":          # the lining is weather now, and it has been let out
        f = field("storm", 1.5)
        for i in range(7 if not worn else 3):
            d = 0.3 + 0.16 * i if not worn else 0.08 + 0.07 * i
            if d > L - 0.1 and not worn:
                break
            s = 1 if i % 2 else -1
            b0 = C.at(d, s * (PI - C.gap(d) * 0.5), -0.05)
            k = size * (0.8 + 0.3 * math.sin(i * 2.1)) * (0.45 if worn else 1.0)
            pts = [b0, b0 + Vector((s * 0.1, -0.2, 0.05)) * k, b0 + Vector((s * 0.3, -0.42, 0.16)) * k, b0 + Vector((s * 0.26, -0.62, 0.36)) * k]
            C.add(g.tongue(pts, [0.12, 0.11, 0.07, 0.01], thick=0.3, normal=Vector((0, 0.2, 1))), f if i % 2 else mat("smoke"))
    elif style == "scorch":        # black at every edge, and stiff as hide
        st = mat("soot")
        pts = C.hem_pts(0.05, 0.008, 15)
        C.add(strap(pts, 0.12 * (0.5 if worn else 1.0), 0.008, up=Z), st)
        for s in (1, -1):
            if s in C.cuffs:
                p, dvec, r = C.cuffs[s]
                C.round(g.tube([p - dvec * 0.1, p + dvec * 0.01], [r * 1.08, r * 1.2], n=7), st)
            if not worn:
                edge = [C.at(dd, s * (PI - C.gap(dd) - 0.02), 0.01) for dd in (0.05, 0.3, 0.55, min(L - 0.05, 0.8))]
                C.add(strap(edge, 0.07, 0.008, up=Y), st)
        f = field("ember", 2.6)
        C.round(g.tube([p + Vector((0, 0, 0.07 if not worn else 0.035)) for p in pts], [0.008] * len(pts), n=3), f)
        if not worn:
            C.add(strap([p + Vector((0, 0, 0.12)) for p in pts], 0.035, 0.008, up=Z), mat("cloth_dust"))
        for i in range(7):
            a = -2.6 + 5.2 * i / 6
            C.round(g.ico(C.hem(a, 0.03 + 0.03 * (i % 2), 0.016), 0.024 * size, sub=0), f)
    elif style == "epaulettes":    # the offices it has held, on its shoulders
        for s in (1, -1):
            sh = Vector((s * 0.3 * C.shw * C.fit, 0.0, L + 0.0))
            C.add(g.box(sh + Vector((-s * 0.04, 0, 0.012)), (0.2, 0.13, 0.03)), brass)
            C.add(g.box(sh + Vector((-s * 0.04, 0, 0.03)), (0.15, 0.09, 0.012)), C.acc)
            for i in range(5):
                b0 = sh + Vector((s * 0.06, -0.05 + 0.025 * i, 0.0))
                C.round(g.tube([b0, b0 + Vector((s * 0.02, 0, -0.1 * size))], [0.009, 0.007], n=4), brass)
    elif style == "chain":         # a chain of office
        geo = None
        for i in range(15):
            t = i / 14
            a = PI - 0.9 + 1.8 * t
            d = 0.06 + (0.3 if not worn else 0.2) * math.sin(PI * t)
            geo = g.merge(geo, g.ico(C.at(d, a, 0.02), 0.018 * size, sub=0, scale=(1.3, 0.6, 1.0) if i % 2 else (0.8, 0.6, 1.3)))
        C.round(geo, brass)
        C.round(g.ico(C.at(0.38 if not worn else 0.27, PI, 0.03), 0.045 * size, sub=1, scale=(1, 0.4, 1)), field("seal", 2.4))
    elif style == "oath":          # its partner's oath, stitched in the lining where only they can read it: the left breast, turned back
        f = field("oath", 2.2)
        d0 = 0.3 if not worn else 0.15
        k = size * (0.5 if worn else 1.0)
        a = PI - C.gap(d0) - 0.42
        c, n = C.at(d0, a, 0.03), C.normal(d0, a)
        rz = math.atan2(-n.x, n.y)
        C.add(g.box(c, (0.26 * k, 0.02, 0.36 * k), rot=(0, 0, rz)), C.acc_d)
        side = Vector((n.y, -n.x, 0))
        for i in range(5):
            z = 0.13 - 0.06 * i
            w = (0.1 - 0.02 * (i % 2)) * k
            C.round(g.tube([c + n * 0.014 - side * w + Vector((0, 0, z * k)), c + n * 0.014 + side * w + Vector((0, 0, z * k))], [0.007, 0.007], n=3), f)
        C.round(g.ico(c + n * 0.016 + Vector((0, 0, -0.2 * k)), 0.03 * (0.7 if worn else 1.0), sub=1, scale=(1, 1, 1)), mat("wax"))
    elif style == "stock":         # a clerk's white stock at the throat, and the points of a collar
        c = C.at(0.1, PI, 0.012)
        C.add(g.blade(c + Vector((0, 0, 0.07)), c + Vector((0, -0.01, -0.16 * size)), 0.17 * size, normal=Vector((0, -1, 0)), belly=0.3), mat("paper"))
        for s in (1, -1):
            C.add(g.blade(c + Vector((s * 0.03, 0, 0.08)), c + Vector((s * 0.14 * size, -0.01, 0.0)), 0.07, normal=Vector((0, -1, 0.3))), mat("paper"))
    elif style == "sash":          # the sash of an office, shoulder to hip
        pts = [C.at(0.02, PI * 0.56, 0.02), C.at(0.2, PI * 0.8, 0.02), C.at(0.38, PI - 0.25, 0.022), C.at(0.56, -(PI - 0.5), 0.02), C.at(0.72, -PI * 0.6, 0.02)]
        C.add(strap(pts, 0.1 * size, 0.012, up=Z), C.acc_l)
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
        if worn:                   # worn, the loop it hangs by, at the nape
            C.round(ringtube(Vector((0, 0.13 * C.fit, L + 0.03)), 0.03, 0.045, 0.008, n=10, u=X, v=Z), mat("cord"))
            return
        top = Vector((0, 0.06, L + 0.42 * size))
        C.add(g.box(top + Vector((0, 0.05, 0.06)), (0.5, 0.04, 0.12)), mat("wood_dark"))
        C.round(g.tube([top + Vector((0, 0.03, 0.06)), top + Vector((0, -0.05, 0.04)), top + Vector((0, -0.07, -0.04)), top + Vector((0, -0.03, -0.08))], [0.014, 0.014, 0.013, 0.01], n=5), iron)
        C.round(g.tube([top + Vector((0, -0.03, -0.08)), Vector((0, 0.08, L + 0.05))], [0.008, 0.008], n=4), mat("cord"))
        for s in (1, -1):
            C.round(g.ico(top + Vector((s * 0.2, 0.03, 0.06)), 0.014, sub=0), iron)
    elif style == "patches":       # mended in four different hands
        spots = [(0.3, PI * 0.72, "cloth_patch_a", 0.2), (0.9, -PI * 0.6, "cloth_patch_b", 0.26), (1.15, PI * 0.3, "cloth_patch_c", 0.22), (0.62, -PI * 0.2, "cloth_patch_a", 0.18),
                 (0.36, -PI * 0.8, "cloth_patch_c", 0.16), (1.2, -PI * 0.85, "cloth_patch_b", 0.2)]
        if worn:
            spots = [(0.12, 0.5, "cloth_patch_a", 0.13), (0.18, -0.7, "cloth_patch_b", 0.14), (0.1, PI * 0.75, "cloth_patch_c", 0.1)]
        for i, (d, a, m, w) in enumerate(spots[: int(round(4 * size)) + 1]):
            if d < C.fall(a) - 0.1:
                c, n = C.at(d, a, 0.008), C.normal(d, a)
                C.add(g.box(c, (w, 0.014, w * (0.8 + 0.3 * (i % 2))), rot=(0, 0.2 * (i - 2), math.atan2(-n.x, n.y))), mat(m))
                C.round(g.tube([c + Vector((0, 0, w * 0.5)) + n * 0.01, c + Vector((0, 0, w * 0.62)) + n * 0.012], [0.006, 0.006], n=3), mat("thread") if i % 2 else C.acc_l)
        if 1 in C.cuffs:            # and one sleeve let down for a longer arm
            p, dvec, r = C.cuffs[1]
            C.round(g.tube([p, p + dvec * 0.12], [r * 1.02, r * 0.98], n=7), mat("cloth_patch_b"))
    elif style == "figure":        # it stands as someone before stood: a little of them is still in it
        f = field("shade", 1.3)
        if worn:                   # worn, their hand is on its wearer's shoulder
            c = Vector((0.24 * C.fit, 0.02, L + 0.035))
            C.round(g.ico(c, 0.075 * size, sub=1, scale=(1.0, 1.25, 0.4)), f)
            for i in range(4):
                b0 = c + Vector((-0.045 + 0.03 * i, -0.07, 0.0))
                C.round(g.tube([b0, b0 + Vector((0, -0.07, -0.03))], [0.015, 0.011], n=4), f)
            return
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
        fit = C.fit
        tips = []
        if c_style in ("ear", "ears"):
            kk = k * (0.82 if worn else 1.0)
            x0 = 0.1 * fit
            for s in (1, -1):
                for (x, y, z) in ((0.1, 0.06, 0.2), (0.26, 0.07, 0.36), (0.4, 0.05, 0.3), (0.43, 0.03, 0.12)):
                    tips.append((Vector((s * (x0 + x * kk), y, L + z * kk)), Vector((s * (x - 0.2), 0.0, z - 0.12)).normalized()))
        else:
            r = 0.46 * k if c_style == "spread" else 0.175 * fit
            zc = L + (0.12 if c_style == "spread" else 0.2 * k)
            for i in range(9):
                a = -2.3 + 4.6 * i / 8
                tips.append((Vector((r * math.sin(a), r * 0.92 * math.cos(a), zc + 0.05 * math.cos(a))), Vector((math.sin(a), math.cos(a), 0.5)).normalized()))
        for i, (b0, dv) in enumerate(tips):
            for j in (-1, 0, 1):
                tip = b0 + (dv + Vector((0, 0, 0.5 * j))).normalized() * (0.2 + 0.05 * (i % 2)) * size
                C.round(g.tube([b0, (b0 + tip) / 2 + Vector((0, 0, 0.02)), tip], [0.006, 0.005, 0.002], n=3), mat("thread"))
    elif style == "drops":         # water stands on it in beads
        for i in range(9):
            a = -2.8 + 5.6 * ((i * 0.618) % 1.0)
            d = 0.05 + (0.5 if not worn else C.fall(a) - 0.1) * ((i * 0.381) % 1.0)
            C.round(g.ico(C.at(d, a, 0.008), 0.016, sub=0), mat("steel_glint"))
    elif style == "current":       # a hem that moves as if there were a current in the room
        C.round(g.tube(C.hem_pts(0.04, 0.01), 0.014, n=4), field("current", 1.8))
        if not worn:
            C.round(g.tube(C.hem_pts(0.2, 0.008), 0.007, n=3), field("current", 1.2))
    elif style == "mantle":        # a cape over the shoulders
        rings = []
        n = 19
        cm = C.cloth or main
        phi = 0.35
        spread = float(spec.get("cape", 1.0))          # how far it stands out at its edge: a bell
        levels = ((-0.02, 0.012, 0.0), (0.1, 0.04, 0.4), (0.3 * size, 0.07 + 0.05 * (spread - 1.0), 1.0), (0.44 * size, 0.09 + 0.16 * (spread - 1.0), 1.0))
        for d, out, wide in levels:
            outer = [C.at(max(d, -0.04), -(PI - phi) + 2 * (PI - phi) * i / (n - 1), out) + Vector((math.sin(-(PI - phi) + 2 * (PI - phi) * i / (n - 1)) * 0.07 * spread * wide, 0, 0)) for i in range(n)]
            inner = [p - (p - Vector((0, 0, p.z))).normalized() * 0.016 for p in outer]
            rings.append(outer + list(reversed(inner)))
        C.solid(g.loft(rings, caps=True, closed=True), lambda c, nrm: lining if (nrm.x * c.x + nrm.y * c.y) < -0.25 * math.hypot(c.x, c.y) else cm)
        # its edge, in its Path's colour
        edge = [p + Vector((0, 0, 0.012)) for p in rings[-1][:n]]
        C.round(g.tube(edge, [0.014] * n, n=4), C.tones()[1])
    elif style == "tails":         # cut away in front, and two long tails behind
        for s in (1, -1):
            top = C.at(L - 0.02, s * 0.34, 0.0)
            C.add(g.tongue([top + Vector((0, 0, 0.06)), top + Vector((s * 0.03, 0.05, -0.3 * size)), top + Vector((s * 0.05, 0.1, -0.62 * size))], [0.26, 0.2, 0.05], thick=0.1, normal=Y), main)
            C.round(g.tongue([top + Vector((0, -0.012, 0.04)), top + Vector((s * 0.03, 0.036, -0.3 * size)), top + Vector((s * 0.05, 0.085, -0.6 * size))], [0.2, 0.15, 0.03], thick=0.08, normal=Y), C.acc)
            C.round(g.ico(top + Vector((0, 0.03, 0.04)), 0.02, sub=0), brass)
    elif style == "pool":          # too long for whoever is in it: it lies on the ground round its hem
        for i in range(9):
            a = -2.7 + 5.4 * i / 8
            b0 = C.hem(a, 0.0, 0.0)
            nrm = C.normal(L, a)
            C.round(g.ico(b0 + nrm * 0.06 * size + Vector((0, 0, 0.02)), 0.13 * size, sub=1, scale=(1.0, 1.0, 0.24), rot=(0, 0, a)), main if i % 2 else C.acc_d)
    elif style == "fling":         # one side of it thrown open, to show what it is lined with
        s = 1 if size >= 0 else -1
        k = abs(size)
        tops = [C.at(d, s * (PI - C.gap(d) - 0.02), 0.01) for d in (0.12, 0.45, 0.8, min(L - 0.04, 1.15))]
        out = Vector((s * 1.0, -0.55, 0.0)).normalized()
        edge = []
        for j in range(len(tops) - 1):
            a0, a1 = tops[j], tops[j + 1]
            w0, w1 = 0.2 * k * (1 + j * 0.7), 0.2 * k * (1 + (j + 1) * 0.7)
            quad = ([a0, a0 + out * w0 + Vector((0, 0, 0.03 * j)), a1 + out * w1 + Vector((0, 0, 0.03 * (j + 1))), a1], [(0, 1, 2, 3), (3, 2, 1, 0)])
            C.add(quad, C.inside, smooth=True)       # what it is lined with, in its Path's colour
            edge += [quad[0][1], quad[0][2]] if j == 0 else [quad[0][2]]
            mid0, mid1 = a0 + out * w0 * 0.5 + Vector((0, 0, 0.015 * j)), a1 + out * w1 * 0.5 + Vector((0, 0, 0.015 * (j + 1)))
            C.round(g.tube([mid0 + Vector((0, -0.008, 0)), mid1 + Vector((0, -0.008, 0))], [0.012, 0.012], n=3), lining if lining.name.startswith("field") else C.acc_l)      # and a seam of it, lit where the lining is light
        C.round(g.tube([p + Vector((0, 0.004, 0)) for p in edge], [0.014] * len(edge), n=4), C.acc_l)
    elif style == "cane":          # it leans on a stick it has no hand for; a longer one is a staff
        hs = C.hand(-1)
        if hs in C.cuffs:
            p, dvec, r = C.cuffs[hs]
            top = p + Vector((0, 0, 0.05 + 0.5 * (size - 1.0)))
            C.round(g.tube([top, Vector((p.x + 0.03 * hs, p.y - 0.06, 0.0))], [0.017, 0.014], n=5), mat("wood_dark"))
            C.round(g.ico(top + Vector((0, 0, 0.02)), 0.03, sub=1), brass)
    elif style == "candle":        # a candle end, held out: it produces things when needed
        hs = C.hand(1)
        if hs in C.cuffs:
            p, dvec, r = C.cuffs[hs]
            b0 = p + dvec * 0.03
            C.round(g.tube([b0 + Vector((0, 0, -0.03)), b0 + Vector((0, 0, 0.1 * size))], [0.03 * size, 0.026 * size], n=7), mat("wax"))
            C.round(lathe_at([(0.05 * size, 0.0), (0.06 * size, 0.012), (0.03 * size, 0.014)], b0 + Vector((0, 0, -0.04)), Z, n=8), brass)
            fl = b0 + Vector((0, 0, 0.11 * size))
            C.move("flick", "flame", [(g.tongue([fl, fl + Vector((0.008, 0, 0.05 * size)), fl + Vector((0, 0, 0.12 * size))], [0.03 * size, 0.045 * size, 0.004], thick=0.8, normal=Y), field("flame", 3.4))], fl)
    elif style == "spikes":        # its shoulders cut to points, sharp as what it carries
        for s in (1, -1):
            sh = Vector((s * 0.3 * C.shw, 0.0, L - 0.02))
            tip = sh + Vector((s * 0.26 * size, 0.02, 0.16 * size))
            C.add(g.tongue([sh + Vector((-s * 0.1, 0, 0.0)), sh + Vector((s * 0.08 * size, 0.01, 0.035 * size)), tip], [0.2, 0.15, 0.01], thick=0.35, normal=Z), main)
            C.round(g.tube([sh + Vector((-s * 0.06, -0.085, 0.012)), sh + Vector((s * 0.09 * size, -0.06, 0.045 * size)), tip], [0.011, 0.011, 0.004], n=4), C.acc_l)
    elif style == "train":         # it is longer behind than any room needs: a train, laid out on the floor after it
        n = 9
        top = [C.hem(-1.25 + 2.5 * i / (n - 1), 0.03, 0.004) for i in range(n)]
        mid = [Vector((p.x * 1.12, p.y + 0.24 * size, 0.035)) for p in top]
        end = [Vector((p.x * (1.0 - 0.5 * abs(i - (n - 1) / 2) / ((n - 1) / 2)), p.y + (0.62 - 0.2 * abs(i - (n - 1) / 2) / ((n - 1) / 2)) * size, 0.012)) for i, p in enumerate(top)]
        verts = top + mid + end
        faces = []
        for j in range(2):
            for i in range(n - 1):
                a_, b_ = j * n + i, j * n + i + 1
                faces += [(a_, b_, b_ + n, a_ + n), (a_ + n, b_ + n, b_, a_)]
        C.add((verts, faces), main, smooth=True)
        C.round(g.tube([p + Vector((0, 0, 0.012)) for p in end], [0.012] * n, n=4), C.tones()[0])
        C.round(g.tube([p + Vector((0, 0, 0.014)) for p in mid], [0.008] * n, n=3), C.tones()[1])
    else:
        raise ValueError("a coat cannot grow: " + str(style))


def _clasp_alone(C, spec):
    """The Starter: a coat's clasp and the two scraps of the coat it still holds. The clasp is
    its face, one eye wide open under a brass lid; the scraps are what it has for a body: it
    holds two points of them up, turned back, like the collar it remembers, and lets the rest
    hang like sleeves."""
    brass, main = C.brass, C.main
    zc, k = 0.62, 2.0
    c = Vector((0.0, -0.03, zc))
    C.clasp_at(c, k, "eye")
    for s in (1, -1):
        root = c + Vector((s * 0.2, 0.04, 0.0))
        # the scrap of the coat's front it still holds, hanging, its end torn: it stirs
        tl = [root + Vector((0.0, 0.0, 0.1)), root + Vector((s * 0.1, 0.012, -0.15)), root + Vector((s * 0.18, 0.016, -0.35)), root + Vector((s * 0.22, 0.03, -0.54))]
        its = [(strap(tl, [0.2, 0.26, 0.24, 0.18], 0.022, up=X), main)]
        for j, dx in enumerate((-0.06, 0.0, 0.06)):
            b0 = tl[3] + Vector((dx, 0, 0.006))
            its.append((g.blade(b0, b0 + Vector((dx * 0.4 + s * 0.02, 0.0, -0.085 - 0.03 * (j % 2))), 0.065, normal=Y), main))
        its.append((g.tube([p + Vector((s * 0.09, -0.016, 0)) for p in tl], [0.007] * 4, n=3), mark("stitch", main)))
        its.append((g.tube([p + Vector((-s * 0.075, -0.016, 0)) for p in tl], [0.009] * 4, n=3), field("weave", 1.7)))
        its.append((strap([p + Vector((0, 0.016, 0)) for p in tl], [0.24, 0.3, 0.28, 0.2], 0.008, up=X), C.acc))      # its lining, showing at its edges
        C.move("sway", "scrap", its, root + Vector((0, 0, 0.1)), side="l" if s > 0 else "r")
        # a point of the collar it remembers, held up and turned back, its lining out
        wg = [root + Vector((s * 0.0, 0.0, 0.06)), root + Vector((s * 0.15, 0.03, 0.24)), root + Vector((s * 0.36, 0.075, 0.4))]
        C.round(g.tongue(wg, [0.22, 0.2, 0.02], thick=0.14, normal=Y), C.acc_l)
        C.round(g.tube([wg[0] + Vector((s * 0.04, -0.02, 0.1)), wg[1] + Vector((s * 0.02, -0.022, 0.09)), wg[2]], [0.011, 0.011, 0.004], n=4), main)
        C.round(g.tube([wg[0] + Vector((s * 0.1, -0.02, -0.08)), wg[1] + Vector((s * 0.09, -0.022, -0.07)), wg[2]], [0.008, 0.008, 0.004], n=3), mark("stitch", main))
    C.wear = (Vector((0, 0.22, zc)), None)
    return {"socket_head": ((0, 0, zc + 0.2), None), "socket_eyes": ((0, -0.06, zc + 0.02), None), "socket_back": ((0, 0.05, zc), None), "socket_body": ((0, -0.04, zc - 0.2), None)}


# ======================================================================================
# The worn piece: a mantle
# ======================================================================================
# The game's people, standing at the origin and facing -Y. Measured on alexandria-m (the men are
# all within a finger of him; the women's shoulders are a finger lower against the chest bone
# and their necks are slimmer, so on them the piece rides a little high and never cuts in):
# the top of the shoulders, the middle of the trunk front to back, the nape of the neck (where
# the empty `worn` stands), and the chest bone that carries the piece.
SHOULDER_Z = 2.0
TRUNK_Y = -0.045
NAPE = Vector((0.0, 0.079, 1.987))
CHEST = Vector((0.0, 0.029, 1.587))

# Its section at each distance below the top of the shoulders: (how far down, half its width,
# how far it stands behind the middle of the trunk, how far in front). Two fingers off the body
# all the way: up the slope of the neck, flat across the shoulders, round the point of the
# shoulder, and down the blades and the breast.
MANTLE_ROWS = ((-0.05, 0.125, 0.1, 0.105), (-0.012, 0.21, 0.118, 0.108), (0.0, 0.3, 0.128, 0.11), (0.012, 0.35, 0.134, 0.113),
               (0.05, 0.4, 0.142, 0.126), (0.1, 0.414, 0.152, 0.15), (0.17, 0.42, 0.16, 0.173), (0.25, 0.424, 0.17, 0.187), (0.34, 0.428, 0.18, 0.193))
# What a Path's mantle is cut like (docs/genius-lines.md, "A worn piece"): how far it falls down
# the back, over the arms and down the breast; how it parts in front; its folds; its edge.
CUTS = {
    # a traveller's shoulder cape: longest down the back, closed at the throat, a broad band at its hem
    "capelet": {"back": 0.34, "side": 0.16, "front": 0.25, "gap": 0.06, "part": 0.42, "flare": 0.12, "fold": 0.045, "folds": 9, "trim": ["hem"]},
    # a cowl: its hood thrown back between the shoulders, its hem cut in points, a bright line on every edge
    "cowl": {"back": 0.3, "side": 0.14, "front": 0.26, "gap": 0.1, "part": 0.3, "flare": 0.1, "fold": 0.03, "folds": 7, "points": 7, "dag": 0.3, "trim": ["piping"]},
    # a clerk's tippet: round and even, smooth, and two long banded ends down the breast
    "tippet": {"back": 0.2, "side": 0.15, "front": 0.2, "gap": 0.08, "part": 0.12, "flare": 0.05, "fold": 0.0, "folds": 0, "trim": ["ends", "yoke"]},
    # a yoke: the least of them, no wider than a collar laid flat
    "yoke": {"back": 0.13, "side": 0.1, "front": 0.13, "gap": 0.08, "part": 0.2, "flare": 0.04, "fold": 0.0, "folds": 0, "trim": ["piping"]},
    # the Starter's: no cape yet, a band of its cloth round the neck
    "scarf": {"back": 0.1, "side": 0.1, "front": 0.1, "gap": 0.2, "part": 0.0, "flare": 0.0, "fold": 0.0, "folds": 0, "trim": []},
}


def _sgn_pow(v, e):
    return math.copysign(abs(v) ** e, v)


def _smooth(e0, e1, v):
    q = max(0.0, min(1.0, (v - e0) / (e1 - e0)))
    return q * q * (3 - 2 * q)


class Mantle(Coat):
    """A coat as it is worn: its own collar and a short cape over the shoulders, longer down
    the back than over the arms, so that an arm can swing and lift under it. It is made on the
    body it is worn on (MANTLE_ROWS), close, as cloth lies: over the slope of the neck and the
    shoulders, down the blades and the breast, with the folds it falls in opening toward its
    hem. Built in a coat's own measure (its shoulders at z = L, its middle at y = 0), then set
    on the shoulders of the game's people."""
    fit = 1.2
    P = 2.5             # how square its section is: shoulders are

    def __init__(self, form_id, spec):
        w = dict(spec.get("worn") or {})
        Coat.__init__(self, form_id + "_worn", spec)
        self.w = w
        self.cutname = w.get("cut", "capelet")
        cut = dict(CUTS[self.cutname])
        cut.update({k: v for k, v in w.items() if k not in ("cut", "grown")})
        f = lambda k: float(cut[k])  # noqa: E731
        self.back, self.side, self.front = f("back"), f("side"), f("front")
        self.L = max(self.back, self.front, self.side)
        self.open, self.cut = f("gap"), f("part")
        self.flare, self.rag, self.wave, self.sweep = f("flare"), 0.0, 0.0, (0.0, 0.0)
        self.fold, self.folds = f("fold"), int(cut["folds"])
        self.points, self.dag = int(cut.get("points", 0)), float(cut.get("dag", 0.25))       # a hem cut in points
        self.trim = [t for t in cut.get("trim", [])]
        self.tone = cut.get("tone", self.tone)

    def t(self, d):
        return max(0.0, min(1.0, d / max(0.05, self.L)))

    def radii(self, d):
        rows = MANTLE_ROWS
        if d <= rows[0][0]:
            rx, rb, rf = rows[0][1:]
        elif d >= rows[-1][0]:
            k = d - rows[-1][0]
            rx, rb, rf = rows[-1][1] + 0.2 * k, rows[-1][2] + 0.3 * k, rows[-1][3] + 0.2 * k
        else:
            for (d0, x0, b0, f0), (d1, x1, b1, f1) in zip(rows, rows[1:]):
                if d <= d1:
                    q = (d - d0) / (d1 - d0)
                    rx, rb, rf = x0 + (x1 - x0) * q, b0 + (b1 - b0) * q, f0 + (f1 - f0) * q
                    break
        k = self.flare * max(0.0, d - 0.04) ** 2 / max(0.05, self.L)       # it kicks out toward its hem
        return rx + 0.4 * k, rb + 1.2 * k, rf + 0.5 * k

    def section(self, d):
        rx, rb, rf = self.radii(d)
        return rx, (rb + rf) / 2, 0.0, (rb - rf) / 2

    def normal(self, d, a):
        rx, rb, rf = self.radii(d)
        e = 2.0 * (self.P - 1.0) / self.P
        v = Vector((_sgn_pow(math.sin(a), e) / rx, _sgn_pow(math.cos(a), e) / (rb if math.cos(a) >= 0 else rf), 0.0))
        return v.normalized() if v.length > 1e-9 else Vector((0, 1, 0))

    def at(self, d, a, out=0.0, t=None):
        """A place on it: d below the top of the shoulders, at an angle a round its wearer from
        the middle of the back; t is how far down its own length that is there (its folds open
        toward its hem)."""
        rx, rb, rf = self.radii(d)
        e = 2.0 / self.P
        x = rx * _sgn_pow(math.sin(a), e)
        y = (rb if math.cos(a) >= 0 else rf) * _sgn_pow(math.cos(a), e)
        if self.fold:
            if t is None:
                t = max(0.0, min(1.0, d / max(0.05, self.fall(a))))
            k = 1.0 + self.fold * (0.5 + 0.5 * math.sin(self.folds * a + 0.7)) * t * t
            x, y = x * k, y * k
        return Vector((x, y, self.L - d)) + self.normal(d, a) * out

    def fall(self, a):
        """Longest down the back, shortest over the arms, and its two ends down the front."""
        x = abs(a)
        wb = 1.0 - _smooth(0.5, 1.25, x)
        wf = _smooth(1.9, 2.6, x)
        v = self.side + (self.back - self.side) * wb + (self.front - self.side) * wf
        if self.points:
            v *= 1.0 - self.dag * abs(math.sin(self.points * 0.5 * a + 0.3))
        return v

    def hem(self, a, up=0.05, out=0.007):
        f = self.fall(a)
        return self.at(f - up, a, out, t=max(0.0, 1.0 - up / max(0.05, f)))

    def hem_pts(self, up=0.05, out=0.007, n=33):
        phi = self.gap(self.L)
        return [self.hem(-(PI - phi) + 2 * (PI - phi) * i / (n - 1), up, out) for i in range(n)]

    def shell(self, n=33, thick=0.012):
        outer, inner = [], []
        for kind, v in (("d", -0.05), ("d", -0.012), ("t", 0.0), ("t", 0.2), ("t", 0.42), ("t", 0.66), ("t", 0.86), ("t", 1.0)):
            ro, ri = [], []
            for i in range(n):
                u = -1.0 + 2.0 * i / (n - 1)
                if kind == "d":
                    a, d, tt = u * (PI - self.open), v, 0.0
                else:
                    a = u * (PI - (self.open + self.cut * v))
                    d, tt = v * self.fall(a), v
                ro.append(self.at(d, a, 0.0, tt))
                ri.append(self.at(d, a, -thick, tt))
            outer.append(ro)
            inner.append(ri)
        # its lining shows only at its edge: the lowest third is lined, and no more is made
        self.skin(outer, inner, 5, self.cloth or self.main, self.inside)
        # the seam down its back: its partner may show it pale
        back = [self.at(d, 0.0, 0.006) for d in (0.0, self.back * 0.5, self.back - 0.02)]
        self.round(g.tube(back, 0.005, n=3), mark("stitch", self.main))

    def trims(self):
        tr = self.trim
        broad, line = self.tones()
        if "hem" in tr:              # a broad band at its edge, and a line above it
            self.band_on(self.hem_pts(0.036, 0.008), 0.058, broad)
            self.band_on(self.hem_pts(0.076, 0.009), 0.012, line)
        if "hem2" in tr:             # two narrow bands
            for up in (0.022, 0.066):
                self.band_on(self.hem_pts(up, 0.008), 0.026, broad)
        if "piping" in tr:           # a bright line along every edge: a dark mantle's outline
            self.round(g.tube(self.hem_pts(0.006, 0.008), 0.0085, n=4), self.acc_l)
            for s in (1, -1):
                pts = []
                for tt in (0.0, 0.3, 0.6, 0.9):
                    a = s * (PI - (self.open + self.cut * tt) - 0.02)
                    pts.append(self.at(tt * self.fall(a), a, 0.006, tt))
                self.round(g.tube(pts, 0.0085, n=4), self.acc_l)
        if "facing" in tr:           # its two front edges faced
            for s in (1, -1):
                pts = []
                for tt in (0.04, 0.35, 0.65, 0.96):
                    a = s * (PI - (self.open + self.cut * tt) - 0.11)
                    pts.append(self.at(tt * self.fall(a), a, 0.008, tt))
                self.band_on(pts, 0.06, broad, up=X, face=(0, -1, 0))
        if "yoke" in tr:             # a yoke: the top of it, close round the neck
            rings, m = [], 21
            for d, out in ((-0.045, 0.006), (-0.012, 0.009), (0.0, 0.01), (0.014, 0.011), (0.05, 0.011)):
                rings.append([self.at(d, -(PI - 0.2) + 2 * (PI - 0.2) * i / (m - 1), out, 0.0) for i in range(m)])
            self.sheet(g.loft(rings, caps=False, closed=False), broad)
            self.band_on([p + Vector((0, 0, 0.003)) + self.normal(0.05, -(PI - 0.2) + 2 * (PI - 0.2) * i / (m - 1)) * 0.002 for i, p in enumerate(rings[-1])], 0.012, line)
        if "points" in tr:           # a point of its colour down the middle of the back
            top, tip = self.at(0.02, 0.0, 0.009, 0.0), self.at(self.back * 0.8, 0.0, 0.009, 0.8)
            self.sheet(([top + Vector((-0.1, -0.01, 0)), top + Vector((0.1, -0.01, 0)), tip], [(1, 0, 2)]), broad)
        if "ends" in tr:             # two long ends down the breast, banded, and a tassel on each that stirs
            for s in (1, -1):
                a = s * (PI - 0.42)
                d0, d1 = self.fall(a) - 0.03, float(self.w.get("ends", 0.44))
                pts = [self.at(d, a, 0.012, 0.0) for d in (d0, (d0 + d1) / 2, d1)]
                pts[2] += Vector((0, -0.012, 0))
                self.round(strap(pts, [0.085, 0.09, 0.095], 0.011, up=X), self.cloth or self.main)
                dn = (pts[2] - pts[1]).normalized()
                for back_, m in ((0.02, line), (0.05, broad), (0.085, line)):
                    c = pts[2] - dn * back_
                    self.round(g.box(c + Vector((0, -0.004, 0)), (0.097, 0.014, 0.022 if m is broad else 0.01)), m)
                e = pts[2] + Vector((0, -0.004, 0.0))
                self.move("sway", "tassel", [(g.cone(e + Vector((0, 0, -0.085)), e + Vector((0, 0, 0.0)), 0.026, n=6), line)], e, side="l" if s > 0 else "r")

    # --- its collar: round a neck that is there, and nothing where the head is -------------
    def rim(self, a, h, flare=0.0, out=0.0):
        """A place on a collar standing from the seam at the neck: h above the seam, at an angle a
        round the neck; it widens by `flare` for each hand's height, and `out` besides."""
        rx, rb, rf = self.radii(-0.05)
        e = 2.0 / self.P
        k = 1.0 + flare * h / 0.1
        return Vector(((rx * k + out) * _sgn_pow(math.sin(a), e), ((rb if math.cos(a) >= 0 else rf) * k + out) * _sgn_pow(math.cos(a), e), self.L + 0.05 + h))

    def band(self, h_back, h_front, flare, gap, lean=0.0, n=17, thick=0.012, outer=None, inner=None):
        """A collar: h_back high at the nape and h_front at its two ends, open `gap` at the throat."""
        outer = outer or (self.acc if "collar" in self.trim else (self.cloth or self.main))
        inner = inner or self.lining
        rings = []
        for q in (0.0, 0.5, 1.0):
            ro, ri = [], []
            for i in range(n):
                a = -(PI - gap) + 2 * (PI - gap) * i / (n - 1)
                h = (h_front + (h_back - h_front) * (0.5 + 0.5 * math.cos(a))) * q - 0.014 * (1.0 - q)
                ro.append(self.rim(a, h, flare, lean * q))
                ri.append(self.rim(a, h, flare, lean * q - thick))
            rings.append(ro + list(reversed(ri)))
        self.solid(g.loft(rings, caps=True, closed=True), lambda c, nrm: inner if (nrm.x * c.x + nrm.y * c.y) < -0.2 * math.hypot(c.x, c.y) else outer)

    def collar(self, style, size=1.0):
        L = self.L
        main, lining = self.cloth or self.main, self.lining
        _, line = self.tones()
        if style in (None, "none"):
            return
        if style in ("turned", "whiskers", "frost"):       # turned up: its lining shows round the neck
            self.band(0.115 * size, 0.05 * size, 0.2, 0.85)
        elif style in ("stand", "cape", "souwester"):
            self.band(0.05, 0.045, 0.04, 0.3)
        elif style == "high":                              # to the ears, and open to the face
            self.band(0.2 * size, 0.08 * size, 0.2, 1.1, lean=0.05 * size)
        elif style == "spread":                            # spread wide and flat, to hear with: a dish laid on the shoulders
            self.band(0.055, 0.0, 0.0, 0.5, lean=0.2 * size, n=21)
        elif style in ("ear", "ears"):
            self.band(0.05, 0.04, 0.05, 0.4)
        elif style == "hood":                              # thrown back: it lies between the shoulders, open, and stirs
            k = size
            roll = [self.rim(-2.25 + 4.5 * i / 12, 0.012, 0.0, 0.03) for i in range(13)]
            self.round(g.tube(roll, [0.014 + 0.024 * math.sin(PI * i / 12) for i in range(13)], n=6), main)
            rings = []
            for z, w, dpt in ((0.075, 0.13, 0.06), (0.02, 0.165, 0.075), (-0.08, 0.15, 0.07), (-0.18, 0.095, 0.045), (-0.27, 0.012, 0.01)):
                d = -z * k
                yb = self.at(max(-0.05, d), 0.0, 0.0, 0.0).y if d > -0.05 else self.rim(0.0, -d - 0.05).y
                c = Vector((0.0, yb + dpt * k + 0.012, L + z * k))
                rings.append(g.ring(c, w * k, dpt * k, n=10, u=X, v=Y))
            bag = [(g.loft(rings, caps=True, closed=True), main)]
            top = Vector((0.0, sum(p.y for p in rings[0]) / 10, L + 0.075 * k))
            bag.append((g.ico(top + Vector((0, 0, 0.004)), 1.0, sub=1, scale=(0.105 * k, 0.045 * k, 0.012)), lining))
            bag.append((ringtube(top + Vector((0, 0, 0.004)), 0.118 * k, 0.052 * k, 0.011, n=12, u=X, v=Y), line))
            self.move("sway", "hood", bag, (0.0, rings[0][0].y - 0.06 * k, L + 0.06))
            self.band(0.035, 0.035, 0.03, 0.5)
        elif style == "fur":                               # a collar of pelt, lying out over the shoulders
            for i in range(13):
                a = -2.5 + 5.0 * i / 12
                b0 = self.rim(a, 0.03, 0.0, 0.0)
                tip = self.rim(a, 0.02 - 0.02 * (i % 2), 0.0, (0.13 + 0.03 * (i % 2)) * size)
                self.add(g.blade(b0, tip, 0.11, normal=Vector((0, 0, 1)), belly=0.45), mat("pelt_dark") if i % 2 else mat("pelt_light"), smooth=True)
        else:
            raise ValueError("no such collar: " + str(style))
        if style in ("ear", "ears"):  # the rims of two ears, standing behind its wearer's own
            el, er = self.ears
            for s, k in ((1, size * 0.6 * el), (-1, size * 0.6 * er)):
                b = self.rim(s * 1.05, 0.02, 0.0, 0.0)
                o = Vector((s * 1.0, 0.22, 0.0))            # each leans out and a little back
                up = Vector((0, 0.1, 1.0))
                P_ = lambda u, v: b + o * (u * k) + up * (v * k)  # noqa: E731
                path = [P_(-0.02, -0.03), P_(0.06, 0.2), P_(0.22, 0.37), P_(0.37, 0.32), P_(0.41, 0.14), P_(0.31, 0.01), P_(0.16, -0.03)]
                self.round(g.tube(path, [0.022, 0.028 * k + 0.008, 0.03 * k + 0.008, 0.03 * k + 0.008, 0.028 * k + 0.008, 0.024 * k + 0.006, 0.016], n=6), self.acc if "collar" in self.trim else main)
                fan = [P_(0.04, 0.0)] + [P_(u, v) for u, v in ((0.07, 0.19), (0.22, 0.34), (0.35, 0.3), (0.385, 0.14), (0.3, 0.03), (0.16, 0.0))]
                self.round((fan, [(0, i, i + 1) for i in range(1, 6)] + [(0, i + 1, i) for i in range(1, 6)]), lining)
                self.round(g.tube([P_(0.12, 0.08), P_(0.21, 0.2), P_(0.29, 0.16)], [0.012, 0.015, 0.008], n=4), self.acc_d)
        if style == "frost":         # frost on the collar that does not melt by the fire
            for i in range(9):
                a = -2.2 + 4.4 * i / 8
                b0 = self.rim(a, 0.1 * size * (0.5 + 0.5 * math.cos(a)) + 0.03, 0.2)
                self.add(g.cone(b0, b0 + Vector((0.04 * math.sin(a), 0.035 * math.cos(a), 0.05 + 0.025 * (i % 3))) * size, 0.016, n=4), mat("frost"))

    def scarf(self):
        """The Starter's: no cape yet. A band of its cloth round the neck, and its two ends
        down the front from the clasp."""
        ring = [self.rim(-(PI - 0.3) + 2 * (PI - 0.3) * i / 16, -0.035 + 0.02 * math.cos(-(PI - 0.3) + 2 * (PI - 0.3) * i / 16), 0.0, 0.012) for i in range(17)]
        self.round(strap(ring, 0.075, 0.02, up=Z), self.acc)
        self.round(g.tube([p + Vector((0, 0, 0.03)) for p in ring], [0.006] * 17, n=3), field("weave", 1.7))
        for s in (1, -1):
            top = self.at(0.05, s * (PI - 0.25), 0.012, 0.0)
            cl = [top, top + Vector((s * 0.02, -0.018, -0.1)), top + Vector((s * 0.035, -0.03, -0.2))]
            its = [(strap(cl, [0.085, 0.1, 0.075], 0.016, up=X), self.acc), (strap([p + Vector((0, 0.01, 0)) for p in cl], [0.06, 0.07, 0.05], 0.008, up=X), self.acc_d)]
            for j, dx in enumerate((-0.025, 0.0, 0.025)):
                b0 = cl[2] + Vector((dx, 0, 0.004))
                its.append((g.blade(b0, b0 + Vector((dx * 0.4, 0.0, -0.035 - 0.012 * (j % 2))), 0.03, normal=Y), self.acc))
            self.move("sway", "scrap", its, top, side="l" if s > 0 else "r")


def mantle(form_id, spec):
    """The worn piece of a form: the objects to export with it, the empty named worn first."""
    import genius_lines as gl
    M = Mantle(form_id, spec)
    c_style, c_size = opt(spec.get("collar", "turned"))
    if M.cutname == "scarf":
        M.scarf()
        M.clasp(1.0, what="weye")
    else:
        M.shell()
        M.trims()
        M.collar(c_style, c_size)
        for style, size in each(spec.get("grown")):
            if style in ON_A_MANTLE:
                grow(M, style, size, spec)
        for style, size in each(M.w.get("grown")):          # and what only the worn piece has
            grow(M, style, size, spec)
        M.clasp(float(spec.get("clasp", 1.0)) * 0.85, what="weye")
    # from the coat's own measure (its shoulders at z = L, its middle at y = 0) to the person's
    place = Matrix.Translation((0.0, TRUNK_Y, SHOULDER_Z - M.L))
    M.flush()
    obs = list(M.objects)
    for i, (material, geo, soft) in enumerate(M.geo.values()):
        obs.append(g.to_object("%s_%d" % (M.name, i), geo, material, smooth=soft))
    ob = g.join(M.name, obs)
    ob.data.transform(place)
    ob.data.update()
    return gl.worn([ob] + M.moving(place), at=NAPE)


def finish_coat(C, form_id, base, spec, M=None, sockets=None, worn=None):
    """Join it, stand it, give it its sockets, the pieces of it that move and the piece that is
    worn, and write it (lines_armors.finish, with those)."""
    import genius_lines as gl
    ob = C.build(M)
    movers = C.moving(C.lift)
    pts = [v.co for v in ob.data.vertices] + [Vector(m.location) + v.co for m in movers for v in m.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0.0))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    H, W, D = hi.z, hi.x - lo.x, hi.y - lo.y
    measure = max(H, 0.62 * max(W, D))
    ref = measure * art_size(base) / float(spec.get("stands", 1.0))
    s = ref / STAND            # parts and keepsakes are made for a body that stands STAND tall
    yc, yf, yb = (lo.y + hi.y) / 2, lo.y, hi.y
    table = {
        "socket_head": (0, yc, H), "socket_eyes": (0, yf - 0.01, 0.72 * H), "socket_mouth": (0, yf - 0.01, 0.45 * H), "socket_grip": (0, yb + 0.01, 0.5 * H),
        "socket_throat": (0, yf - 0.01, 0.36 * H), "socket_light": (0, yf - 0.01, 0.24 * H), "socket_back": (0, yb + 0.01, 0.66 * H), "socket_body": (0, yf - 0.01, 0.52 * H),
        "socket_tail": (0, yb, 0.06 * H), "socket_arm_l": (hi.x + 0.01, yc, 0.62 * H), "socket_arm_r": (lo.x - 0.01, yc, 0.62 * H),
        "socket_limb_fl": (0.3 * W, yf, 0.02), "socket_limb_fr": (-0.3 * W, yf, 0.02), "socket_keepsake": (0, yf - 0.012, 0.3 * H),
    }
    size = Matrix.Diagonal((s, s, s))
    socks = {name: kit.free_socket(name, at, size) for name, at in table.items()}
    for name, (at, rot) in (sockets or {}).items():          # the builder's own, given in the piece's space before it was stood
        if name in socks:
            bpy.data.objects.remove(socks[name])
        p = C.lift @ Vector(at)
        r3 = C.lift.to_3x3() @ (rot if rot is not None else Matrix.Identity(3))
        socks[name] = kit.free_socket(name, p, r3 @ size)
    if C.wear is not None:
        at, rot = C.wear
        socks["wear"] = kit.free_socket("wear", C.lift @ Vector(at), C.lift.to_3x3() @ (rot if rot is not None else Matrix.Identity(3)))
    path = os.path.join(gl.OUT, form_id + ".glb")
    tris = gl.export_objects([ob] + movers + list(worn or []), socks, path, ref=ref)
    kb = os.path.getsize(path) // 1024
    if kb > 120:
        log("OVER BUDGET", form_id, kb, "KB")
    return tris


def posture(spec):
    """How it holds itself: `lean` [to the front, to its left] in degrees, `turn` about its own
    height. A coat that leans, leans from its hem."""
    lean = spec.get("lean") or [0, 0]
    turn = float(spec.get("turn", 0.0))
    if not (lean[0] or lean[1] or turn):
        return None
    return Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Rotation(math.radians(float(lean[0])), 4, "X") @ Matrix.Rotation(math.radians(float(lean[1])), 4, "Y")


def build(form_id, level, spec, base):
    kit.reset()
    C = Coat(form_id, spec)
    if spec.get("kind") == "clasp":
        socks = _clasp_alone(C, spec)
        return finish_coat(C, form_id, base, spec, sockets=socks, worn=mantle(form_id, spec))
    L = C.L
    C.shell()
    sl = spec.get("sleeves", "hang")
    left, right = (sl if isinstance(sl, (list, tuple)) else (sl, sl))
    arm = float(spec.get("arm", 1.0))
    C.sleeve(1, left, arm)
    C.sleeve(-1, right, arm)
    C.trims()
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
    return finish_coat(C, form_id, base, spec, M=posture(spec), sockets=socks, worn=mantle(form_id, spec))
