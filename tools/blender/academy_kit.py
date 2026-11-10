"""WILDLINE academy kit: the home base, built in Blender and exported where the game looks
for it (docs/home-base.md). The Academy at Alexandria in the art bible's lamplight gothic:
stone and timber with brass fittings and tall glass, warm lamps against a cool dusk. Built
on the wild kit's Piece (tools/blender/wild_kit.py). Run headless with Blender's Python
module:

    python tools/blender/academy_kit.py                      # every piece
    python tools/blender/academy_kit.py range_window bunk    # some pieces
    python tools/blender/academy_kit.py --sheet /path/sheet.png

Conventions (the game relies on them, World._build_academy_place):
  - Blender is Z up and a piece faces -Y; the glTF export turns that into the game's Y up,
    +Z forward. One .glb per piece at game/assets/academy/<name>.glb. People are 2.4 tall:
    a storey is 5, a door 3.6, a sill 1.6.
  - WALL pieces are 4 wide along X (portals 8), their inside face at y = 0 looking toward -Y
    (into the place); the building's mass lies behind, toward +Y. They may reach 1.5 into
    the place (a canopy, an arcade). A wall piece is two objects: "Plinth" (the kerb, up to
    0.9: it always shows) and "Upper" (everything above: the game hides it on the camera's
    side of the place, so tall walls never stand between the camera and the hero).
  - CORNER pieces sit on a place's corner and fill the quadrant +X, +Y outside it.
  - FLOOR pieces are 4 x 4 tiles with their top at z = 0.
  - Props stand on their origin. A prop's footprint is the game's business (the furniture
    list in data/academy.json gives each a "solid" radius).
  - Empties named light_<kind>[.n] mark where the game hangs a light: lamp (a warm lantern),
    fire (a hearth or brazier), stain (coloured glass), cool (the line's blue). An empty
    named socket_flame marks where a fire burns.
  - Flat-shaded, no textures. Materials are named so the game's toon shader finds the
    surface (stone, wood, metal, cloth) by the name; names ending _lit glow.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wild_kit as wk  # noqa: E402

ROOT = wk.ROOT
OUT = os.path.join(ROOT, "game", "assets", "academy")

# name: (colour, roughness[, emission colour, strength]). Desaturated earths; the lamps and
# the glass carry the colour.
PALETTE = {
    "stone": ((0.255, 0.24, 0.225), 0.85),
    "stone_course": ((0.17, 0.165, 0.17), 0.9),
    "stone_dress": ((0.36, 0.335, 0.30), 0.8),
    "stone_floor": ((0.29, 0.275, 0.265), 0.9),
    "stone_floor_b": ((0.235, 0.225, 0.225), 0.9),
    "plaster": ((0.46, 0.42, 0.34), 0.9),
    "plaster_dark": ((0.44, 0.38, 0.30), 0.9),
    "wood_timber": ((0.15, 0.095, 0.06), 0.85),
    "wood_plank": ((0.30, 0.20, 0.115), 0.85),
    "wood_plank_b": ((0.255, 0.165, 0.095), 0.85),
    "wood_door": ((0.21, 0.125, 0.075), 0.8),
    "slate_tile": ((0.085, 0.09, 0.105), 0.75),
    "slate_tile_b": ((0.11, 0.115, 0.13), 0.75),
    "brass_metal": ((0.62, 0.46, 0.20), 0.4),
    "iron_metal": ((0.07, 0.07, 0.085), 0.55),
    "glass_lit": ((0.7, 0.42, 0.16), 0.3, (1.0, 0.56, 0.2), 1.15),
    "glass_dim_lit": ((0.5, 0.36, 0.2), 0.3, (1.0, 0.6, 0.3), 0.9),
    "glass_night_lit": ((0.05, 0.07, 0.13), 0.2, (0.22, 0.32, 0.62), 0.5),
    "stain_amber_lit": ((0.55, 0.3, 0.06), 0.3, (0.95, 0.5, 0.08), 0.8),
    "stain_violet_lit": ((0.22, 0.1, 0.45), 0.3, (0.45, 0.2, 1.0), 0.8),
    "stain_sky_lit": ((0.08, 0.25, 0.5), 0.3, (0.15, 0.55, 1.0), 0.8),
    "stain_green_lit": ((0.08, 0.4, 0.16), 0.3, (0.15, 0.9, 0.3), 0.7),
    "stain_rose_lit": ((0.5, 0.1, 0.06), 0.3, (1.0, 0.2, 0.08), 0.8),
    "lamp_lit": ((1.0, 0.75, 0.4), 0.3, (1.0, 0.66, 0.3), 3.0),
    "flame_lit": ((1.0, 0.6, 0.25), 0.3, (1.0, 0.5, 0.16), 5.0),
    "cool_lit": ((0.5, 0.7, 1.0), 0.3, (0.45, 0.68, 1.0), 3.5),
    "cloth_red": ((0.36, 0.075, 0.065), 0.95),
    "cloth_blue": ((0.10, 0.16, 0.29), 0.95),
    "cloth_green": ((0.13, 0.21, 0.12), 0.95),
    "cloth_linen": ((0.60, 0.55, 0.45), 0.95),
    "cloth_gold": ((0.62, 0.45, 0.16), 0.9),
    "straw": ((0.50, 0.40, 0.18), 0.95),
    "rope": ((0.40, 0.32, 0.20), 0.95),
    "paper": ((0.72, 0.67, 0.55), 0.9),
    "grass": ((0.085, 0.14, 0.065), 0.95),
    "leaf": ((0.075, 0.135, 0.065), 0.9),
    "bark": ((0.14, 0.10, 0.07), 0.9),
    "dirt_yard": ((0.27, 0.21, 0.15), 0.95),
    "shadow": ((0.008, 0.008, 0.01), 1.0),
}
STAINS = ["stain_amber_lit", "stain_violet_lit", "stain_sky_lit", "stain_green_lit", "stain_rose_lit"]


def kit_material(name):
    spec = PALETTE[name]
    col = tuple(spec[0]) + (1,)
    if len(spec) > 2:
        return wk.material(name, col, spec[1], emission=tuple(spec[2]) + (1,), strength=spec[3])
    return wk.material(name, col, spec[1])


class P(wk.Piece):
    """A piece of the kit: the wild kit's Piece with the academy's palette and its shapes."""

    def mat_index(self, name):
        m = bpy.data.materials.get(name) or kit_material(name)
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def bx(self, mat, x0, x1, y0, y1, z0, z1):
        self.box(mat, (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

    def prism(self, mat, pts, a0, a1, plane="xz"):
        """A convex outline swept between a0 and a1 along the third axis. plane "xz": the outline
        is (x, z), swept along y; "yz": (y, z) along x; "xy": (x, y) along z."""
        bm = bmesh.new()
        def at(p, a):
            if plane == "xz":
                return (p[0], a, p[1])
            if plane == "yz":
                return (a, p[0], p[1])
            return (p[0], p[1], a)
        lo = [bm.verts.new(at(p, a0)) for p in pts]
        hi = [bm.verts.new(at(p, a1)) for p in pts]
        n = len(pts)
        bm.faces.new(lo)
        bm.faces.new(hi[::-1])
        for i in range(n):
            bm.faces.new((lo[i], hi[i], hi[(i + 1) % n], lo[(i + 1) % n]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        self.add(bm, mat)

    @staticmethod
    def arc(cx, hw, spring, rise, n=5):
        """The points of a pointed arch from its left springing over the apex to the right."""
        rise = max(rise, hw * 1.001)
        c = (rise * rise - hw * hw) / (2 * hw)
        R = hw + c
        a_top = math.atan2(rise, -c)
        left = []
        for i in range(n + 1):
            a = math.pi + (a_top - math.pi) * i / n
            left.append((cx + c + R * math.cos(a), spring + R * math.sin(a)))
        right = [(2 * cx - x, z) for x, z in left[-2::-1]]
        return left + right

    def arch(self, mat, cx, hw, z0, spring, rise, y0, y1, n=5):
        """A pointed-arch slab (a pane of glass, a door leaf, a recess): convex."""
        self.prism(mat, [(cx - hw, z0), (cx + hw, z0)] + self.arc(cx, hw, spring, rise, n)[::-1], y0, y1)

    def arch_ring(self, mat, cx, hw, z0, spring, rise, t, y0, y1, n=5):
        """The surround of a pointed arch: two jambs and the voussoirs, t thick."""
        self.bx(mat, cx - hw - t, cx - hw, y0, y1, z0, spring)
        self.bx(mat, cx + hw, cx + hw + t, y0, y1, z0, spring)
        inner = self.arc(cx, hw, spring, rise, n)
        outer = self.arc(cx, hw + t, spring, rise + t * 1.25, n)
        for i in range(len(inner) - 1):
            self.prism(mat, [inner[i], inner[i + 1], outer[i + 1], outer[i]], y0, y1)

    def gable(self, mat, x0, x1, y_front, y_back, z_eave, z_ridge, y_ridge=None):
        """A roof whose ridge runs along X."""
        yr = (y_front + y_back) / 2 if y_ridge is None else y_ridge
        self.prism(mat, [(y_front, z_eave), (y_back, z_eave), (yr, z_ridge)], x0, x1, plane="yz")

    def gable_front(self, mat, x0, x1, y0, y1, z_eave, z_ridge):
        """A roof whose ridge runs along Y (a gable toward the place)."""
        self.prism(mat, [(x0, z_eave), (x1, z_eave), ((x0 + x1) / 2, z_ridge)], y0, y1)

    def brace(self, mat, a, b, y, w=0.16, t=0.1):
        """A timber from a to b (x, z) on the wall face at y."""
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz)
        self.box(mat, (L, t, w), ((a[0] + b[0]) / 2, y, (a[1] + b[1]) / 2), rot=(0, -math.atan2(dz, dx), 0))

    def window(self, cx, z0, z1, w, y, glass="glass_lit", frame="wood_timber", bars=(1, 1)):
        """A rectangular casement on the wall face at y: frame, glass, glazing bars."""
        f = 0.12
        self.bx(frame, cx - w / 2 - f, cx + w / 2 + f, y - 0.09, y + 0.02, z0 - f, z1 + f)
        self.bx(glass, cx - w / 2, cx + w / 2, y - 0.11, y - 0.05, z0, z1)
        for i in range(1, bars[0] + 1):
            x = cx - w / 2 + w * i / (bars[0] + 1)
            self.bx(frame, x - 0.03, x + 0.03, y - 0.13, y - 0.1, z0, z1)
        for i in range(1, bars[1] + 1):
            z = z0 + (z1 - z0) * i / (bars[1] + 1)
            self.bx(frame, cx - w / 2, cx + w / 2, y - 0.13, y - 0.1, z - 0.03, z + 0.03)

    def lancet(self, cx, hw, z0, spring, rise, y, glass="glass_lit", stone="stone_dress", panes=None, mullion=True):
        """A pointed window on the wall face at y: a stone surround, glass (or rows of stained
        panes), a mullion and transoms in lead."""
        self.arch_ring(stone, cx, hw, z0, spring, rise, 0.16, y - 0.14, y + 0.02)
        self.bx(stone, cx - hw - 0.22, cx + hw + 0.22, y - 0.2, y + 0.02, z0 - 0.16, z0)
        if panes:
            rows = len(panes)
            for i, mat in enumerate(panes):
                a, b = z0 + (spring - z0) * i / rows, z0 + (spring - z0) * (i + 1) / rows
                if isinstance(mat, (list, tuple)):
                    self.bx(mat[0], cx - hw, cx, y - 0.08, y - 0.03, a, b)
                    self.bx(mat[1], cx, cx + hw, y - 0.08, y - 0.03, a, b)
                else:
                    self.bx(mat, cx - hw, cx + hw, y - 0.08, y - 0.03, a, b)
                self.bx("iron_metal", cx - hw, cx + hw, y - 0.1, y - 0.07, b - 0.025, b + 0.025)
            self.prism(panes[-1][0] if isinstance(panes[-1], (list, tuple)) else panes[-1], self.arc(cx, hw, spring, rise), y - 0.08, y - 0.03)
        else:
            self.arch(glass, cx, hw, z0, spring, rise, y - 0.08, y - 0.03)
        if mullion:
            self.bx("iron_metal" if panes else stone, cx - 0.035, cx + 0.035, y - 0.11, y - 0.07, z0, spring + rise * 0.9)

    def door(self, cx, hw, spring, rise, y, leaves=2, stone="stone_dress", t=0.3):
        """A pointed doorway on the wall face at y: a deep stone surround, timber leaves bound
        in brass, ring handles."""
        self.arch_ring(stone, cx, hw, 0.0, spring, rise, t, y - 0.3, y + 0.05)
        self.arch_ring("stone_course", cx, hw + t, 0.0, spring, rise + t * 1.25, 0.1, y - 0.2, y + 0.05)
        self.arch("wood_door", cx, hw, 0.0, spring, rise, y - 0.12, y)
        for z in (0.55, spring * 0.55, spring - 0.15):
            self.bx("brass_metal", cx - hw + 0.04, cx + hw - 0.04, y - 0.16, y - 0.12, z - 0.07, z + 0.07)
        if leaves == 2:
            self.bx("shadow", cx - 0.025, cx + 0.025, y - 0.14, y - 0.11, 0.0, spring + rise * 0.92)
            for sx in (-1, 1):
                self.cone("brass_metal", 0.09, 0.09, 0.05, (cx + sx * 0.22, y - 0.13, spring * 0.5), rot=(math.pi / 2, 0, 0), segs=8)
        else:
            self.cone("brass_metal", 0.09, 0.09, 0.05, (cx + hw * 0.6, y - 0.13, spring * 0.5), rot=(math.pi / 2, 0, 0), segs=8)

    def lantern(self, at, bracket=0.5, light=True, kind="lamp"):
        """A wall lantern: an iron bracket and cage, a lit glass, a light for the game."""
        x, y, z = at
        self.bx("iron_metal", x - 0.04, x + 0.04, y - bracket, y, z + 0.3, z + 0.38)
        self.brace_y("iron_metal", (y, z), (y - bracket * 0.8, z + 0.3), x)
        self.box("lamp_lit" if kind == "lamp" else "cool_lit", (0.22, 0.22, 0.3), (x, y - bracket, z + 0.1))
        self.cone("iron_metal", 0.2, 0.03, 0.14, (x, y - bracket, z + 0.25), segs=4)
        self.box("iron_metal", (0.26, 0.26, 0.04), (x, y - bracket, z - 0.07))
        if light:
            self.empty("light_%s" % kind, (x, y - bracket - 0.15, z + 0.1))

    def brace_y(self, mat, a, b, x, w=0.05):
        """A thin bar from a to b (y, z) at x."""
        dy, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dy, dz)
        self.box(mat, (w, L, w), (x, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2), rot=(math.atan2(dz, dy), 0, 0))

    def buttress(self, x, z_top, y_out=0.55, w=0.5, mat="stone_dress"):
        """A stepped buttress on the wall face."""
        self.bx(mat, x - w / 2, x + w / 2, -y_out, 0.05, 0.0, z_top * 0.55)
        self.prism(mat, [(-y_out, z_top * 0.55), (0.05, z_top * 0.55), (0.05, z_top * 0.55 + 0.4), (-y_out * 0.6, z_top * 0.55 + 0.4)], x - w / 2, x + w / 2, plane="yz")
        self.bx(mat, x - w / 2, x + w / 2, -y_out * 0.6, 0.05, z_top * 0.55 + 0.4, z_top - 0.4)
        self.prism(mat, [(-y_out * 0.6, z_top - 0.4), (0.05, z_top - 0.4), (0.05, z_top)], x - w / 2, x + w / 2, plane="yz")

    def courses(self, x0, x1, z0, z1, y, rows=4, mat="stone_course"):
        """A few dressed blocks proud of an ashlar wall, so the stone reads as laid."""
        w = x1 - x0
        for r in range(rows):
            z = z0 + (z1 - z0) * (r + 0.5) / rows
            for k in range(2):
                bw = self.rng.uniform(0.5, 0.9)
                x = x0 + 0.1 + self.rng.uniform(0, max(0.01, w - bw - 0.2))
                self.bx(mat if self.rng.random() < 0.5 else "stone_dress", x, x + bw, y - 0.035, y, z - 0.19, z + 0.19)


# ======================================================================================
# The registry
# ======================================================================================

WALLS, CORNERS, FLOORS, PROPS = {}, {}, {}, {}


def wall(fn):
    WALLS[fn.__name__] = fn
    return fn


def corner(fn):
    CORNERS[fn.__name__] = fn
    return fn


def floor(fn):
    FLOORS[fn.__name__] = fn
    return fn


def prop(fn):
    PROPS[fn.__name__] = fn
    return fn


# ======================================================================================
# The court's ranges: two storeys round the Quad. Ashlar below, timber and plaster above,
# slate over all. Depth 5 behind the wall line.
# ======================================================================================

DEPTH = 5.0
ST1 = 5.0       # the top of the ground storey
ST2 = 8.6       # the eaves


def range_base(lo, up, x0=-2.0, x1=2.0, jetty=0.25, roof=True, chimney=False):
    """The shell every range bay shares."""
    lo.bx("stone_course", x0, x1, -0.12, DEPTH, 0.0, 0.8)
    up.bx("stone", x0, x1, 0.0, DEPTH, 0.8, ST1)
    up.bx("stone_course", x0, x1, -0.1, 0.1, ST1 - 0.12, ST1 + 0.14)
    # the upper storey: plaster panels in a timber frame, jettied a little over the stone
    up.bx("plaster", x0, x1, -jetty, DEPTH, ST1 + 0.14, ST2)
    y = -jetty - 0.05
    up.bx("wood_timber", x0, x1, y, -jetty + 0.05, ST1 + 0.14, ST1 + 0.42)
    up.bx("wood_timber", x0, x1, y, -jetty + 0.05, ST2 - 0.26, ST2)
    for x in (x0 + 0.11, x1 - 0.11):
        up.bx("wood_timber", x - 0.11, x + 0.11, y, -jetty + 0.05, ST1 + 0.42, ST2 - 0.26)
    # the jetty's brackets
    for x in (x0 + 0.3, x1 - 0.3):
        up.prism("wood_timber", [(-jetty - 0.05, ST1 + 0.14), (0.0, ST1 + 0.14), (0.0, ST1 - 0.5)], x - 0.08, x + 0.08, plane="yz")
    if roof:
        up.gable("slate_tile", x0, x1, -jetty - 0.6, DEPTH + 0.5, ST2 - 0.05, ST2 + 3.3)
        up.bx("wood_timber", x0, x1, -jetty - 0.66, -jetty - 0.5, ST2 - 0.2, ST2 + 0.02)
        up.bx("stone_course", x0, x1, DEPTH / 2 - 0.36, DEPTH / 2 + 0.11, ST2 + 3.22, ST2 + 3.4)
        # a few slates of another weathering
        for i in range(5):
            x = x0 + 0.3 + up.rng.uniform(0, x1 - x0 - 1.0)
            t = up.rng.uniform(0.15, 0.8)
            yy = (-jetty - 0.6) + (DEPTH / 2 + jetty + 0.35) * t
            zz = ST2 - 0.05 + 3.35 * t
            up.box("slate_tile_b", (0.55, 0.5, 0.05), (x + 0.27, yy, zz + 0.05), rot=(math.atan2(3.35, DEPTH / 2 + jetty + 0.35), 0, 0))
    if chimney:
        up.bx("stone", 0.6, 1.5, DEPTH - 1.6, DEPTH - 0.6, ST2, ST2 + 4.4)
        up.bx("stone_course", 0.5, 1.6, DEPTH - 1.7, DEPTH - 0.5, ST2 + 4.4, ST2 + 4.62)
        for cx in (0.85, 1.25):
            up.cone("stone_dress", 0.14, 0.11, 0.45, (cx, DEPTH - 1.1, ST2 + 4.62), segs=6)


def upper_frame(up, x0, x1, jetty=0.25, window=True, braces=True):
    y = -jetty - 0.05
    mid = (ST1 + 0.42 + ST2 - 0.26) / 2
    cx = (x0 + x1) / 2
    if window:
        up.bx("wood_timber", x0 + 0.22, x1 - 0.22, y, -jetty + 0.05, mid + 0.86, mid + 1.0)
        up.window(cx, mid - 0.75, mid + 0.75, 1.3, -jetty - 0.02, bars=(1, 1))
        for sx in (-1, 1):
            xx = cx + sx * 0.95
            up.bx("wood_timber", xx - 0.07, xx + 0.07, y, -jetty + 0.05, ST1 + 0.42, ST2 - 0.26)
    else:
        up.bx("wood_timber", x0 + 0.22, x1 - 0.22, y, -jetty + 0.05, mid - 0.08, mid + 0.08)
        up.bx("wood_timber", cx - 0.08, cx + 0.08, y, -jetty + 0.05, ST1 + 0.42, ST2 - 0.26)
    if braces:
        for sx in (-1, 1):
            a = (cx + sx * (x1 - cx - 0.22), ST1 + 0.42)
            b = (cx + sx * (0.95 if window else 0.1) + sx * 0.1, mid - 0.05)
            up.brace("wood_timber", a, b, y + 0.03)


@wall
def range_plain(lo, up):
    range_base(lo, up)
    upper_frame(up, -2, 2, window=False)
    up.courses(-1.9, 1.9, 0.9, ST1 - 0.3, 0.0)
    up.buttress(-1.75, 4.3)
    lo.bx("stone_dress", -2.0, -1.5, -0.55, 0.0, 0.0, 0.9)


@wall
def range_window(lo, up):
    range_base(lo, up, chimney=True)
    upper_frame(up, -2, 2, window=True)
    up.lancet(0.0, 0.62, 1.7, 3.3, 0.95, 0.0)
    up.courses(-1.9, -0.95, 0.9, ST1 - 0.3, 0.0, rows=3)
    up.courses(0.95, 1.9, 0.9, ST1 - 0.3, 0.0, rows=3)


@wall
def range_dim(lo, up):
    """A bay whose rooms are dark: the shutters closed below, a dim window above."""
    range_base(lo, up)
    upper_frame(up, -2, 2, window=True)
    up.arch_ring("stone_dress", 0.0, 0.62, 1.7, 3.3, 0.95, 0.16, -0.14, 0.02)
    up.arch("wood_door", 0.0, 0.62, 1.7, 3.3, 0.95, -0.08, -0.03)
    up.bx("iron_metal", -0.6, 0.6, -0.1, -0.07, 2.4, 2.48)
    up.courses(-1.9, -0.95, 0.9, ST1 - 0.3, 0.0, rows=3)
    up.buttress(1.75, 4.3)
    lo.bx("stone_dress", 1.5, 2.0, -0.55, 0.0, 0.0, 0.9)


@wall
def range_door(lo, up):
    range_base(lo, up)
    upper_frame(up, -2, 2, window=True)
    up.door(0.0, 1.05, 2.5, 1.35, 0.0)
    lo.bx("stone_dress", -1.7, 1.7, -0.75, 0.0, 0.0, 0.12)
    up.lantern((1.62, -0.05, 3.0))
    up.box("brass_metal", (0.7, 0.05, 0.3), (0.0, -0.36, 4.35))


@wall
def cloister_bay(lo, up):
    """The cloister walk under the range: two pointed arches on a column, the walk in shadow
    behind, the timber storey over it."""
    jetty = 0.25
    lo.bx("stone_course", -2, 2, -1.5, DEPTH, 0.0, 0.3)
    lo.bx("stone_dress", -2, 2, -1.5, -1.0, 0.3, 0.85)
    up.bx("shadow", -2, 2, 1.6, 1.7, 0.3, ST1)
    up.bx("stone", -2, 2, 1.7, DEPTH, 0.3, ST1)
    up.bx("stone_floor_b", -2, 2, -1.0, 1.6, 0.3, 0.34)
    # the arcade stands 1.25 into the court
    for cx in (-1.0, 1.0):
        up.arch_ring("stone_dress", cx, 0.72, 0.85, 2.7, 1.1, 0.28, -1.5, -1.0)
    up.bx("stone", -2, 2, -1.45, -1.05, 3.9, ST1 - 0.75)
    for cx in (-2.0, 0.0, 2.0):
        up.cone("stone_dress", 0.2, 0.17, 1.85, (cx, -1.25, 0.85), segs=8)
        up.box("stone_course", (0.5, 0.5, 0.16), (cx, -1.25, 2.72))
    # the lean-to over the walk, then the storey above
    up.prism("slate_tile", [(-1.75, ST1 - 0.75), (0.0, ST1 - 0.75), (0.0, ST1 + 0.3)], -2, 2, plane="yz")
    up.bx("wood_timber", -2, 2, -1.8, -1.68, ST1 - 0.85, ST1 - 0.7)
    up.bx("plaster", -2, 2, 0.0, DEPTH, ST1 - 0.75, ST2)
    up.bx("wood_timber", -2, 2, -0.05, 0.05, ST2 - 0.26, ST2)
    for x in (-1.89, 1.89):
        up.bx("wood_timber", x - 0.11, x + 0.11, -0.05, 0.05, ST1 + 0.3, ST2 - 0.26)
    up.window(0.0, ST1 + 0.95, ST1 + 2.5, 1.3, -0.02, bars=(1, 1))
    up.gable("slate_tile", -2, 2, -0.6, DEPTH + 0.5, ST2 - 0.05, ST2 + 3.3)
    up.bx("stone_course", -2, 2, DEPTH / 2 - 0.3, DEPTH / 2 + 0.2, ST2 + 3.22, ST2 + 3.4)
    up.empty("light_lamp", (0.0, 0.3, 3.4))
    up.box("lamp_lit", (0.2, 0.2, 0.26), (0.0, 0.3, 3.5))
    up.bx("iron_metal", -0.02, 0.02, 0.28, 0.32, 3.6, 4.2)


@wall
def range_portal(lo, up):
    """A great door, 8 wide: a gabled porch standing out of the range, double doors."""
    for sx in (-1, 1):
        lo.bx("stone_course", sx * 4, sx * 2.6, -0.12, DEPTH, 0.0, 0.8)
        up.bx("stone", sx * 4, sx * 2.6, 0.0, DEPTH, 0.8, ST1)
        up.bx("plaster", sx * 4, sx * 2.6, -0.25, DEPTH, ST1 + 0.14, ST2)
        up.bx("wood_timber", sx * 4, sx * 2.6, -0.3, -0.2, ST2 - 0.26, ST2)
        up.bx("wood_timber", sx * 4, sx * 2.6, -0.3, -0.2, ST1 + 0.14, ST1 + 0.42)
        up.brace("wood_timber", (sx * 3.9, ST1 + 0.42), (sx * 2.75, ST2 - 0.3), -0.27)
    up.gable("slate_tile", -4, 4, -0.85, DEPTH + 0.5, ST2 - 0.05, ST2 + 3.3)
    # the porch
    lo.bx("stone_course", -2.7, 2.7, -0.75, DEPTH, 0.0, 0.8)
    up.bx("stone", -2.7, 2.7, -0.6, DEPTH, 0.8, ST2 + 0.3)
    up.gable_front("stone", -2.7, 2.7, -0.6, 2.4, ST2 + 0.3, ST2 + 3.6)
    up.gable_front("slate_tile", -3.1, 3.1, -0.9, 2.6, ST2 + 0.25, ST2 + 4.1)
    up.gable_front("stone", -2.7, 2.7, -0.62, -0.55, ST2 + 0.3, ST2 + 3.6)
    up.door(0.0, 1.7, 3.3, 2.1, -0.6, t=0.4)
    lo.bx("stone_dress", -2.6, 2.6, -1.45, -0.6, 0.0, 0.13)
    lo.bx("stone_dress", -2.3, 2.3, -1.2, -0.6, 0.13, 0.26)
    for sx in (-1, 1):
        up.buttress(sx * 2.45, 6.4, y_out=1.15, w=0.55)
        lo.bx("stone_dress", sx * 2.45 - 0.28, sx * 2.45 + 0.28, -1.15, -0.6, 0.0, 0.9)
        up.lantern((sx * 2.05, -0.65, 3.4))
    up.lancet(0.0, 0.5, ST2 - 1.9, ST2 - 0.2, 0.75, -0.6, glass="glass_lit", mullion=False)
    up.cone("brass_metal", 0.08, 0.0, 0.7, (0.0, -0.75, ST2 + 4.05), segs=6)


@wall
def library_bay(lo, up):
    """The Library's wall: stone its whole height, a tall lancet of coloured glass between
    buttresses, a parapet, a steep roof behind."""
    H = 9.6
    lo.bx("stone_course", -2, 2, -0.15, DEPTH, 0.0, 0.85)
    up.bx("stone", -2, 2, 0.0, DEPTH, 0.85, H)
    r = up.rng
    panes = []
    for i in range(6):
        a, b = r.sample(STAINS, 2)
        panes.append((a, b))
    up.lancet(0.0, 0.85, 1.9, 7.2, 1.35, 0.0, panes=panes)
    for sx in (-1, 1):
        up.buttress(sx * 1.72, H - 0.5, y_out=0.8, w=0.56)
        lo.bx("stone_dress", sx * 1.72 - 0.28, sx * 1.72 + 0.28, -0.8, 0.0, 0.0, 0.9)
        up.cone("stone_dress", 0.2, 0.0, 1.0, (sx * 1.72, -0.2, H - 0.1), segs=4)
    up.bx("stone_course", -2, 2, -0.12, 0.1, H - 0.2, H + 0.1)
    for x in (-1.0, 0.0, 1.0):
        up.bx("stone", x - 0.3, x + 0.3, -0.08, 0.3, H + 0.1, H + 0.6)
    up.gable("slate_tile", -2, 2, 0.3, DEPTH + 0.4, H, H + 4.2)
    up.bx("stone_course", -2, 2, DEPTH / 2 + 0.2, DEPTH / 2 + 0.5, H + 4.1, H + 4.3)
    up.empty("light_stain", (0.0, -1.2, 3.2))


@wall
def library_portal(lo, up):
    """The Hall's great door in the Library range, 8 wide: a gable with a rose of coloured
    glass over double doors."""
    H = 9.6
    lo.bx("stone_course", -4, 4, -0.15, DEPTH, 0.0, 0.85)
    up.bx("stone", -4, 4, 0.0, DEPTH, 0.85, H)
    up.gable_front("stone", -4, 4, -0.3, DEPTH, H, H + 4.6)
    up.gable_front("slate_tile", -4.4, 4.4, -0.1, DEPTH + 0.4, H - 0.1, H + 5.1)
    up.gable_front("stone", -4, 4, -0.34, -0.26, H, H + 4.6)
    up.bx("stone", -4, 4, -0.3, 0.0, 0.85, H)
    up.door(0.0, 1.9, 3.6, 2.4, -0.3, t=0.45)
    lo.bx("stone_dress", -3.0, 3.0, -1.5, -0.3, 0.0, 0.13)
    lo.bx("stone_dress", -2.6, 2.6, -1.2, -0.3, 0.13, 0.26)
    # the rose: a ring of coloured panes round a boss
    cz = 8.4
    up.cone("stone_dress", 1.35, 1.35, 0.14, (0.0, -0.3, cz), rot=(math.pi / 2, 0, 0), segs=16)
    for i in range(8):
        a0, a1 = 2 * math.pi * i / 8, 2 * math.pi * (i + 1) / 8
        pts = [(0.28 * math.cos(a0), cz + 0.28 * math.sin(a0)), (1.15 * math.cos(a0), cz + 1.15 * math.sin(a0)),
               (1.15 * math.cos(a1), cz + 1.15 * math.sin(a1)), (0.28 * math.cos(a1), cz + 0.28 * math.sin(a1))]
        up.prism(STAINS[i % len(STAINS)], pts, -0.5, -0.44)
        up.brace("iron_metal", (0.28 * math.cos(a0), cz + 0.28 * math.sin(a0)), (1.15 * math.cos(a0), cz + 1.15 * math.sin(a0)), -0.5, w=0.05, t=0.06)
    up.cone("brass_metal", 0.28, 0.28, 0.1, (0.0, -0.42, cz), rot=(math.pi / 2, 0, 0), segs=8)
    for sx in (-1, 1):
        up.buttress(sx * 3.6, H - 0.4, y_out=1.2, w=0.7)
        lo.bx("stone_dress", sx * 3.6 - 0.35, sx * 3.6 + 0.35, -1.2, 0.0, 0.0, 0.9)
        up.cone("stone_dress", 0.26, 0.0, 1.4, (sx * 3.6, -0.3, H - 0.1), segs=4)
        up.lantern((sx * 2.75, -0.35, 3.6))
    up.cone("brass_metal", 0.1, 0.0, 0.9, (0.0, -0.3, H + 4.95), segs=6)
    up.empty("light_stain", (0.0, -1.6, 4.0))


@wall
def gatehouse(lo, up):
    """The way to the line, 8 wide: two turrets, a great arch with the portcullis up, the
    wall-walk between."""
    H = 8.4
    lo.bx("stone_course", -4, 4, -0.2, DEPTH, 0.0, 0.85)
    up.bx("stone", -4, 4, 0.0, DEPTH, 0.85, H)
    up.arch_ring("stone_dress", 0.0, 2.1, 0.0, 3.6, 2.5, 0.45, -0.35, 0.05)
    up.arch("shadow", 0.0, 2.1, 0.0, 3.6, 2.5, -0.02, 0.03)
    # the portcullis, raised: its teeth show under the arch
    for i in range(7):
        x = -1.8 + 0.6 * i
        up.bx("iron_metal", x - 0.05, x + 0.05, -0.16, -0.08, 4.4, 6.0 - abs(x) * 0.55)
        up.cone("iron_metal", 0.07, 0.0, 0.25, (x, -0.12, 4.4), rot=(math.pi, 0, 0), segs=4)
    for z in (4.7, 5.3):
        up.bx("iron_metal", -1.9, 1.9, -0.17, -0.09, z - 0.04, z + 0.04)
    up.arch("wood_door", 0.0, 2.1, 0.0, 3.6, 2.5, -0.06, -0.02)
    for z in (0.7, 2.0, 3.3):
        up.bx("brass_metal", -2.05, 2.05, -0.1, -0.06, z - 0.08, z + 0.08)
    up.bx("shadow", -0.03, 0.03, -0.09, -0.05, 0.0, 5.9)
    # the wall-walk and its battlements
    up.bx("stone_course", -4, 4, -0.3, 0.1, H - 0.25, H + 0.05)
    for i in range(5):
        x = -2.0 + i
        if i % 2 == 0:
            up.bx("stone", x - 0.35, x + 0.35, -0.25, 0.25, H + 0.05, H + 0.75)
    for sx in (-1, 1):
        lo.cone("stone_course", 1.5, 1.5, 0.9, (sx * 3.2, -0.2, 0.0), segs=8)
        up.cone("stone", 1.35, 1.3, H + 1.6, (sx * 3.2, -0.2, 0.9), segs=8)
        up.cone("stone_course", 1.5, 1.5, 0.3, (sx * 3.2, -0.2, H + 2.4), segs=8)
        up.cone("slate_tile", 1.65, 0.0, 3.2, (sx * 3.2, -0.2, H + 2.7), segs=8)
        up.cone("brass_metal", 0.07, 0.0, 0.6, (sx * 3.2, -0.2, H + 5.85), segs=6)
        up.window(sx * 3.2, 5.6, 6.9, 0.5, -1.52, bars=(0, 1))
        up.lantern((sx * 2.0, -0.4, 3.4))
    up.box("brass_metal", (1.6, 0.06, 0.4), (0.0, -0.4, 6.75))


@wall
def tower_door(lo, up):
    """The Instructors' Tower: it stands out of the range and above it, a door at its foot,
    lit windows up its height, a lamp room under the roof."""
    H = 15.5
    w = 2.6
    lo.bx("stone_course", -w - 0.15, w + 0.15, -0.9, DEPTH + 0.6, 0.0, 0.9)
    up.bx("stone", -w, w, -0.75, DEPTH + 0.45, 0.9, H)
    up.door(0.0, 0.95, 2.4, 1.3, -0.75, leaves=1)
    lo.bx("stone_dress", -1.5, 1.5, -1.45, -0.75, 0.0, 0.13)
    up.lantern((1.55, -0.8, 3.0))
    for z, x in ((5.6, -1.2), (8.2, 1.1), (10.8, -1.0)):
        up.lancet(x, 0.38, z, z + 1.3, 0.6, -0.75, mullion=False)
    for sx in (-1, 1):
        up.bx("stone_dress", sx * w - 0.3, sx * w + 0.3, -1.05, -0.45, 0.0, H)
    for z in (5.0, 9.8):
        up.bx("stone_course", -w - 0.1, w + 0.1, -0.85, -0.7, z, z + 0.22)
    # the lamp room: timber and glass, jettied on all sides
    up.bx("wood_timber", -w - 0.45, w + 0.45, -1.2, DEPTH + 0.9, H, H + 0.3)
    up.bx("plaster", -w - 0.35, w + 0.35, -1.1, DEPTH + 0.8, H + 0.3, H + 3.2)
    up.bx("wood_timber", -w - 0.45, w + 0.45, -1.2, DEPTH + 0.9, H + 3.2, H + 3.45)
    for x in (-2.4, -0.8, 0.8, 2.4):
        up.bx("wood_timber", x - 0.1, x + 0.1, -1.16, -1.06, H + 0.3, H + 3.2)
    for x in (-1.6, 0.0, 1.6):
        up.window(x, H + 1.0, H + 2.6, 1.0, -1.1, bars=(1, 1))
    for sx in (-1, 1):
        up.bx("glass_lit", sx * (w + 0.36), sx * (w + 0.4), 0.2, 3.8, H + 1.0, H + 2.6)
    yc = (DEPTH + 0.9 - 1.2) / 2
    up.cone("slate_tile", 4.6, 0.0, 5.2, (0.0, yc, H + 3.45), rot=(0, 0, math.pi / 4), segs=4)
    up.cone("brass_metal", 0.1, 0.0, 1.2, (0.0, yc, H + 8.5), segs=6)
    up.box("brass_metal", (0.6, 0.04, 0.3), (0.3, yc, H + 9.2))
    up.empty("light_lamp.tower", (0.0, -1.6, H + 1.8))


@corner
def corner_turret(lo, up):
    """Where two ranges meet: a square stair turret, a little taller than the roofs."""
    H = 11.0
    lo.bx("stone_course", -0.4, 5.6, -0.4, 5.6, 0.0, 0.9)
    up.bx("stone", -0.25, 5.4, -0.25, 5.4, 0.9, H)
    for z in (ST1, ST2 + 0.5):
        up.bx("stone_course", -0.35, 5.5, -0.35, 5.5, z, z + 0.22)
    up.lancet(1.4, 0.34, 6.2, 7.5, 0.6, -0.25, mullion=False)
    up.cone("slate_tile", 4.5, 0.0, 4.6, (2.6, 2.6, H), rot=(0, 0, math.pi / 4), segs=4)
    up.cone("brass_metal", 0.08, 0.0, 0.8, (2.6, 2.6, H + 4.5), segs=6)


# ======================================================================================
# The Yard: a drill ground inside a curtain wall, a stand to watch from, the armoury's lean-to
# ======================================================================================

CURT = 5.4


def curtain(lo, up, x0=-2.0, x1=2.0):
    lo.bx("stone_course", x0, x1, -0.15, 1.5, 0.0, 0.9)
    up.bx("stone", x0, x1, 0.0, 1.4, 0.9, CURT)
    up.bx("stone_course", x0, x1, -0.14, 1.5, CURT - 0.2, CURT + 0.06)
    n = int(round((x1 - x0)))
    for i in range(n):
        if i % 2 == 0:
            x = x0 + i + 0.5
            up.bx("stone", x - 0.42, x + 0.42, -0.1, 0.35, CURT + 0.06, CURT + 0.8)


@wall
def curtain_wall(lo, up):
    curtain(lo, up)
    up.courses(-1.9, 1.9, 1.0, CURT - 0.4, 0.0, rows=4)
    up.buttress(1.75, 4.6)
    lo.bx("stone_dress", 1.5, 2.0, -0.55, 0.0, 0.0, 0.9)


@wall
def curtain_lamp(lo, up):
    curtain(lo, up)
    up.courses(-1.9, 1.9, 1.0, CURT - 0.4, 0.0, rows=3)
    up.lantern((0.0, -0.02, 3.3), bracket=0.6)
    # a banner hung from the wall-walk
    up.bx("wood_timber", -0.75, 0.75, -0.2, -0.12, 4.7, 4.8)
    up.bx("cloth_red", -0.6, 0.6, -0.17, -0.13, 2.9, 4.7)
    up.prism("cloth_red", [(-0.6, 2.9), (0.6, 2.9), (0.0, 2.4)], -0.17, -0.13)
    up.bx("cloth_gold", -0.6, 0.6, -0.19, -0.15, 4.3, 4.45)


@wall
def curtain_portal(lo, up):
    """The Yard's gate in the curtain, 8 wide."""
    curtain(lo, up, -4, 4)
    up.bx("stone", -2.9, 2.9, -0.4, 1.4, 0.9, CURT + 1.6)
    lo.bx("stone_course", -2.9, 2.9, -0.5, 1.5, 0.0, 0.9)
    up.door(0.0, 1.7, 3.2, 2.0, -0.4, t=0.4)
    up.bx("stone_course", -3.0, 3.0, -0.5, 1.5, CURT + 1.5, CURT + 1.75)
    for x in (-2.2, -0.75, 0.75, 2.2):
        up.bx("stone", x - 0.4, x + 0.4, -0.45, 0.0, CURT + 1.75, CURT + 2.4)
    for sx in (-1, 1):
        up.lantern((sx * 2.3, -0.45, 3.3))
    lo.bx("stone_dress", -2.4, 2.4, -1.2, -0.4, 0.0, 0.13)


@wall
def stand_bay(lo, up):
    """The stand: a timber gallery against the curtain where the cohort watches a bout."""
    curtain(lo, up)
    lo.bx("wood_plank", -2, 2, -1.5, 0.0, 0.0, 0.55)
    lo.bx("wood_timber", -2, 2, -1.55, -1.45, 0.45, 0.6)
    up.bx("wood_plank_b", -2, 2, -0.75, 0.0, 0.55, 1.15)
    lo.bx("wood_plank_b", -1.9, 1.9, -1.35, -0.95, 0.55, 0.9)
    up.bx("wood_plank_b", -1.9, 1.9, -0.6, -0.2, 1.15, 1.5)
    for x in (-1.9, 1.9):
        up.bx("wood_timber", x - 0.09, x + 0.09, -1.5, -1.32, 0.55, 4.0)
        up.brace("wood_timber", (x, 3.2), (x - (0.7 if x > 0 else -0.7), 4.0), -1.41)
    up.bx("wood_timber", -2, 2, -1.52, -1.3, 3.95, 4.15)
    up.prism("slate_tile", [(-1.9, 4.1), (0.0, 4.1), (0.0, 5.0)], -2, 2, plane="yz")
    up.bx("wood_timber", -2, 2, -1.95, -1.85, 4.02, 4.2)


@wall
def armoury_bay(lo, up):
    """The armoury's lean-to: blades and poles racked under a roof against the curtain."""
    curtain(lo, up)
    for x in (-1.9, 1.9):
        up.bx("wood_timber", x - 0.09, x + 0.09, -1.45, -1.27, 0.0, 3.7)
    up.bx("wood_timber", -2, 2, -1.47, -1.25, 3.65, 3.85)
    up.prism("slate_tile", [(-1.85, 3.8), (0.0, 3.8), (0.0, 4.7)], -2, 2, plane="yz")
    up.bx("wood_plank", -1.7, 1.7, -0.25, -0.12, 0.9, 1.05)
    up.bx("wood_plank", -1.7, 1.7, -0.25, -0.12, 2.3, 2.45)
    r = up.rng
    for i in range(7):
        x = -1.5 + 0.5 * i
        if i % 3 == 2:
            up.bx("wood_plank_b", x - 0.035, x + 0.035, -0.4, -0.33, 0.1, 3.3)
            up.cone("iron_metal", 0.07, 0.0, 0.4, (x, -0.36, 3.3), segs=4)
        else:
            L = r.uniform(1.4, 1.9)
            up.bx("iron_metal", x - 0.05, x + 0.05, -0.38, -0.34, 1.15, 1.15 + L)
            up.bx("brass_metal", x - 0.16, x + 0.16, -0.4, -0.32, 1.08, 1.15)
            up.bx("wood_door", x - 0.04, x + 0.04, -0.39, -0.33, 0.7, 1.08)
    for sx in (-1, 1):
        up.cone("wood_plank", 0.34, 0.3, 0.8, (sx * 1.3, -0.9, 0.0), segs=8)
        up.cone("iron_metal", 0.35, 0.35, 0.05, (sx * 1.3, -0.9, 0.55), segs=8)
    up.lantern((0.0, -0.02, 3.0), bracket=0.5)


@corner
def curtain_corner(lo, up):
    """A round tower on the curtain's corner."""
    lo.cone("stone_course", 2.6, 2.6, 0.9, (0.9, 0.9, 0.0), segs=10)
    up.cone("stone", 2.4, 2.3, CURT + 1.2, (0.9, 0.9, 0.9), segs=10)
    up.cone("stone_course", 2.55, 2.55, 0.3, (0.9, 0.9, CURT + 2.1), segs=10)
    up.cone("slate_tile", 2.8, 0.0, 3.0, (0.9, 0.9, CURT + 2.4), segs=10)


# ======================================================================================
# The Gate: the Academy's own platform on the line. Station walls with a canopy, the great
# arch the line leaves by.
# ======================================================================================

STN = 6.4


def station(lo, up, x0=-2.0, x1=2.0, canopy=True):
    lo.bx("stone_course", x0, x1, -0.15, 2.0, 0.0, 0.9)
    up.bx("stone", x0, x1, 0.0, 1.9, 0.9, STN)
    up.bx("stone_course", x0, x1, -0.14, 2.0, STN - 0.2, STN + 0.1)
    up.gable("slate_tile", x0, x1, -0.3, 2.3, STN + 0.05, STN + 1.5)
    if canopy:
        # iron brackets and a glazed canopy over the platform
        for x in (x0 + 0.2, x1 - 0.2):
            up.bx("iron_metal", x - 0.05, x + 0.05, -1.5, 0.0, 4.3, 4.4)
            up.brace_y("iron_metal", (0.0, 3.3), (-1.3, 4.3), x, w=0.07)
        up.prism("glass_night_lit", [(-1.6, 4.4), (0.0, 4.4), (0.0, 4.95)], x0, x1, plane="yz")
        up.bx("iron_metal", x0, x1, -1.66, -1.56, 4.3, 4.5)
        for i in range(int(x1 - x0)):
            x = x0 + i + 0.5
            up.brace_y("iron_metal", (0.0, 4.97), (-1.6, 4.42), x, w=0.05)


@wall
def station_wall(lo, up):
    station(lo, up)
    up.lancet(0.0, 0.6, 1.7, 3.0, 0.9, 0.0)
    up.courses(-1.9, -0.9, 1.0, 4.0, 0.0, rows=3)
    up.courses(0.9, 1.9, 1.0, 4.0, 0.0, rows=3)


@wall
def station_bench(lo, up):
    station(lo, up)
    up.courses(-1.9, 1.9, 2.6, 4.0, 0.0, rows=2)
    # a bench against the wall, a board of notices over it
    lo.bx("wood_plank", -1.4, 1.4, -0.75, -0.2, 0.55, 0.65)
    for x in (-1.25, 1.25):
        lo.bx("iron_metal", x - 0.05, x + 0.05, -0.7, -0.25, 0.0, 0.55)
    up.bx("wood_plank", -1.4, 1.4, -0.26, -0.18, 0.9, 1.4)
    up.bx("wood_timber", -1.1, 1.1, -0.1, 0.0, 1.9, 3.3)
    r = up.rng
    for i in range(5):
        x, z = r.uniform(-0.9, 0.7), r.uniform(2.0, 2.9)
        up.bx("paper", x, x + r.uniform(0.25, 0.4), -0.13, -0.1, z, z + r.uniform(0.25, 0.4))
    up.lantern((0.0, -0.02, 3.5), bracket=0.5)


@wall
def station_clock(lo, up):
    station(lo, up)
    up.cone("brass_metal", 0.75, 0.75, 0.16, (0.0, -0.06, 3.2), rot=(math.pi / 2, 0, 0), segs=14)
    up.cone("glass_dim_lit", 0.62, 0.62, 0.05, (0.0, -0.2, 3.2), rot=(math.pi / 2, 0, 0), segs=14)
    up.brace("iron_metal", (0.0, 3.2), (0.0, 3.65), -0.24, w=0.05, t=0.03)
    up.brace("iron_metal", (0.0, 3.2), (0.3, 3.0), -0.24, w=0.05, t=0.03)
    up.courses(-1.9, 1.9, 1.0, 2.2, 0.0, rows=2)


@wall
def station_portal(lo, up):
    """The door from the platform back to the Quad, 8 wide."""
    station(lo, up, -4, 4, canopy=False)
    up.bx("stone", -2.8, 2.8, -0.35, 1.9, 0.9, STN + 1.2)
    up.gable_front("stone", -2.8, 2.8, -0.35, 1.9, STN + 1.2, STN + 3.2)
    up.gable_front("slate_tile", -3.15, 3.15, -0.6, 2.2, STN + 1.15, STN + 3.65)
    up.gable_front("stone", -2.8, 2.8, -0.37, -0.3, STN + 1.2, STN + 3.2)
    up.door(0.0, 1.7, 3.2, 2.0, -0.35, t=0.4)
    lo.bx("stone_dress", -2.4, 2.4, -1.15, -0.35, 0.0, 0.13)
    for sx in (-1, 1):
        up.lantern((sx * 2.3, -0.4, 3.3))
    up.box("brass_metal", (1.3, 0.05, 0.34), (0.0, -0.4, 6.1))


@wall
def line_arch(lo, up):
    """Where the line leaves: a great arch, 8 wide, open on the dark, the signal burning blue."""
    H = 9.0
    lo.bx("stone_course", -4, -2.6, -0.2, 2.2, 0.0, 0.9)
    lo.bx("stone_course", 2.6, 4, -0.2, 2.2, 0.0, 0.9)
    for sx in (-1, 1):
        up.bx("stone", sx * 4, sx * 2.6, 0.0, 2.1, 0.9, H)
        up.bx("stone_dress", sx * 2.6 - 0.35, sx * 2.6 + 0.35, -0.5, 0.2, 0.0, H - 2.4)
    inner = up.arc(0.0, 2.6, 4.2, 2.9)
    for i in range(len(inner) - 1):
        a, b = inner[i], inner[i + 1]
        up.prism("stone", [a, b, (b[0], H), (a[0], H)], 0.0, 2.1)
    up.arch_ring("stone_dress", 0.0, 2.6, 0.0, 4.2, 2.9, 0.5, -0.4, 0.05)
    up.arch("shadow", 0.0, 2.6, 0.0, 4.2, 2.9, 2.0, 2.05)
    up.bx("stone_course", -4, 4, -0.3, 2.2, H - 0.25, H + 0.05)
    for i in range(8):
        if i % 2 == 0:
            x = -3.5 + i
            up.bx("stone", x - 0.4, x + 0.4, -0.25, 0.3, H + 0.05, H + 0.8)
    # the portcullis up in its slot, the signal on its bracket
    for i in range(9):
        x = -2.2 + 0.55 * i
        up.bx("iron_metal", x - 0.05, x + 0.05, 0.3, 0.38, 7.2 - abs(x) * 0.5, 7.9)
    up.bx("brass_metal", -1.2, 1.2, -0.46, -0.4, 7.55, 8.0)
    up.lantern((-3.2, -0.02, 4.0), bracket=0.9, kind="cool")
    up.lantern((3.2, -0.02, 4.0), bracket=0.9)


# ======================================================================================
# Indoors: the Dormitory and the Hearth Hall. Stone to the knee, a timber wainscot, plaster
# between posts, 6.4 to the wall-plate; the roof is trusses in the dark.
# ======================================================================================

HALL = 6.4


def hall(lo, up, x0=-2.0, x1=2.0, posts=True):
    lo.bx("stone_course", x0, x1, 0.0, 0.7, 0.0, 0.9)
    lo.bx("wood_timber", x0, x1, -0.08, 0.0, 0.0, 0.32)
    up.bx("wood_plank_b", x0, x1, -0.05, 0.7, 0.9, 1.9)
    up.bx("wood_timber", x0, x1, -0.1, 0.0, 1.85, 2.0)
    up.bx("plaster", x0, x1, 0.0, 0.7, 1.9, HALL)
    up.bx("wood_timber", x0, x1, -0.14, 0.75, HALL - 0.3, HALL)
    if posts:
        for x in (x0, x1):
            up.bx("wood_timber", x - 0.13, x + 0.13, -0.14, 0.05, 0.9, HALL - 0.3)
    n = int(x1 - x0)
    for i in range(1, n):
        x = x0 + i
        up.bx("wood_timber", x - 0.02, x + 0.02, -0.07, -0.04, 0.95, 1.85)


@wall
def hall_wall(lo, up):
    hall(lo, up)
    up.brace("wood_timber", (-1.87, HALL - 1.6), (-0.6, HALL - 0.3), -0.03)
    up.brace("wood_timber", (1.87, HALL - 1.6), (0.6, HALL - 0.3), -0.03)


@wall
def hall_sconce(lo, up):
    hall(lo, up)
    up.box("brass_metal", (0.3, 0.05, 0.5), (0.0, -0.03, 3.3))
    up.lantern((0.0, -0.02, 3.2), bracket=0.4)


@wall
def hall_window(lo, up):
    hall(lo, up)
    up.lancet(0.0, 0.62, 2.3, 4.3, 0.95, 0.0, glass="glass_night_lit", stone="stone_dress")
    up.bx("wood_plank", -0.9, 0.9, -0.3, 0.0, 2.1, 2.2)


@wall
def hall_banner(lo, up):
    hall(lo, up)
    up.bx("brass_metal", -0.85, 0.85, -0.18, -0.12, 5.25, 5.33)
    col = up.rng.choice(["cloth_red", "cloth_blue", "cloth_green"])
    up.bx(col, -0.7, 0.7, -0.16, -0.12, 2.6, 5.25)
    up.prism(col, [(-0.7, 2.6), (0.7, 2.6), (0.0, 2.0)], -0.16, -0.12)
    up.bx("cloth_gold", -0.7, 0.7, -0.18, -0.14, 4.6, 4.8)
    up.cone("cloth_gold", 0.3, 0.3, 0.03, (0.0, -0.17, 3.6), rot=(math.pi / 2, 0, 0), segs=6)


@wall
def hall_door(lo, up):
    hall(lo, up)
    up.door(0.0, 1.05, 2.5, 1.35, 0.0, t=0.26)
    up.lantern((1.6, -0.02, 3.2), bracket=0.4)


@wall
def hall_portal(lo, up):
    hall(lo, up, -4, 4)
    up.door(0.0, 1.7, 3.2, 2.0, 0.0, t=0.4)
    for sx in (-1, 1):
        up.lantern((sx * 2.6, -0.02, 3.4), bracket=0.45)


@wall
def hall_hearth(lo, up):
    """The great hearth, 8 wide: a stone breast, an arched mouth, the fire, a mantel in brass."""
    hall(lo, up, -4, 4)
    lo.bx("stone_course", -2.9, 2.9, -1.2, 0.0, 0.0, 0.3)
    lo.bx("stone_dress", -2.7, 2.7, -1.5, -1.2, 0.0, 0.18)
    up.bx("stone", -2.7, 2.7, -0.7, 0.7, 0.3, 4.4)
    lo.bx("stone", -2.7, 2.7, -0.7, 0.7, 0.3, 0.9)
    up.prism("stone", [(-2.7, 4.4), (2.7, 4.4), (1.5, HALL + 0.6), (-1.5, HALL + 0.6)], -0.6, 0.7)
    up.arch("shadow", 0.0, 1.5, 0.3, 2.0, 1.25, -0.74, -0.68)
    up.arch_ring("stone_dress", 0.0, 1.5, 0.3, 2.0, 1.25, 0.34, -0.9, -0.66)
    up.bx("stone_dress", -2.9, 2.9, -1.0, -0.6, 3.75, 4.0)
    up.bx("brass_metal", -2.5, 2.5, -1.02, -0.98, 3.82, 3.93)
    # the fire: logs on irons, the flame, its light
    for sx in (-1, 1):
        lo.bx("iron_metal", sx * 0.7 - 0.04, sx * 0.7 + 0.04, -1.0, -0.3, 0.3, 0.5)
        lo.cone("brass_metal", 0.07, 0.07, 0.5, (sx * 0.7, -1.0, 0.3), segs=6)
    lo.cone("bark", 0.14, 0.14, 1.7, (-0.85, -0.65, 0.62), rot=(0, math.pi / 2, 0), segs=6)
    lo.cone("bark", 0.12, 0.12, 1.5, (-0.75, -0.45, 0.78), rot=(0, math.pi / 2, 0.2), segs=6)
    up.cone("flame_lit", 0.5, 0.0, 1.1, (0.0, -0.55, 0.9), segs=5)
    up.cone("flame_lit", 0.3, 0.0, 0.8, (-0.5, -0.5, 0.9), segs=5)
    up.cone("flame_lit", 0.26, 0.0, 0.7, (0.55, -0.5, 0.9), segs=5)
    up.empty("light_fire", (0.0, -1.4, 1.6))
    up.empty("socket_flame", (0.0, -0.55, 0.9))
    # arms above the mantel
    up.cone("brass_metal", 0.6, 0.6, 0.08, (0.0, -0.72, 5.2), rot=(math.pi / 2, 0, 0), segs=6)
    up.cone("cloth_red", 0.44, 0.44, 0.1, (0.0, -0.74, 5.2), rot=(math.pi / 2, 0, 0), segs=6)


@corner
def hall_corner(lo, up):
    lo.bx("stone_course", -0.2, 0.9, -0.2, 0.9, 0.0, 0.9)
    up.bx("wood_timber", -0.2, 0.9, -0.2, 0.9, 0.9, HALL)


def truss(p, span):
    """A king-post truss across the hall: its tie beam at the wall-plate, braces, the rafters."""
    h = span / 2
    z0 = HALL - 0.15
    rise = span * 0.3
    p.bx("wood_timber", -h, h, -0.16, 0.16, z0, z0 + 0.34)
    p.bx("wood_timber", -0.14, 0.14, -0.14, 0.14, z0 + 0.34, z0 + rise)
    for sx in (-1, 1):
        p.brace("wood_timber", (sx * h, z0 + 0.3), (0.0, z0 + rise), 0.0, w=0.26, t=0.26)
        p.brace("wood_timber", (sx * h * 0.5, z0 + 0.34), (0.0, z0 + rise * 0.62), 0.0, w=0.16, t=0.18)
        p.brace("wood_timber", (sx * h, z0 - 1.3), (sx * (h - 1.5), z0 + 0.1), 0.0, w=0.2, t=0.2)
    p.bx("iron_metal", -0.2, 0.2, -0.18, 0.18, z0 + 0.05, z0 + 0.28)


@prop
def truss_12(p):
    truss(p, 12.0)


@prop
def truss_20(p):
    truss(p, 20.0)


@prop
def chandelier(p):
    """An iron ring of lamps on its chain, hung from a truss (its origin is the floor under it)."""
    z = 4.3
    p.bx("iron_metal", -0.025, 0.025, -0.025, 0.025, z + 0.2, HALL)
    for i in range(10):
        a0, a1 = 2 * math.pi * i / 10, 2 * math.pi * (i + 1) / 10
        mx, my = (math.cos(a0) + math.cos(a1)) / 2 * 0.95, (math.sin(a0) + math.sin(a1)) / 2 * 0.95
        p.box("iron_metal", (0.62, 0.07, 0.07), (mx, my, z), rot=(0, 0, (a0 + a1) / 2 + math.pi / 2))
    for i in range(5):
        a = 2 * math.pi * i / 5
        x, y = 0.95 * math.cos(a), 0.95 * math.sin(a)
        p.box("lamp_lit", (0.14, 0.14, 0.2), (x, y, z + 0.15))
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        dx, dy = 0.95 * math.cos(a), 0.95 * math.sin(a)
        L = math.hypot(0.95, 1.1)
        tilt = math.atan2(0.95, 1.1)
        p.box("iron_metal", (0.03, 0.03, L), (dx / 2, dy / 2, z + 0.55), rot=(tilt * math.sin(a), -tilt * math.cos(a), 0))
    p.empty("light_lamp", (0.0, 0.0, z - 0.3))


# ======================================================================================
# Floors: 4 x 4 tiles, their top at z = 0
# ======================================================================================

def slabs(p, rows, mats, gap=0.035, relief=0.012, thick=0.3):
    """Flagstones: rows of slabs of uneven width, two stones, the joints open."""
    r = p.rng
    p.bx("stone_course", -2, 2, -2, 2, -thick, -0.03)
    y = -2.0
    for h in rows:
        x = -2.0
        while x < 2.0 - 1e-6:
            w = min(r.choice([0.8, 1.0, 1.2, 1.4, 2.0]), 2.0 - x)
            if 2.0 - (x + w) < 0.5:
                w = 2.0 - x
            p.bx(r.choice(mats), x + gap, x + w - gap, y + gap, y + h - gap, -0.1, r.uniform(-relief, 0.0))
            x += w
        y += h


@floor
def floor_flags(p):
    slabs(p, [1.0, 1.2, 0.8, 1.0], ["stone_floor", "stone_floor", "stone_floor_b"])


@floor
def floor_hall(p):
    slabs(p, [2.0, 2.0], ["stone_floor", "stone_floor_b"], gap=0.03)


@floor
def floor_boards(p):
    r = p.rng
    p.bx("shadow", -2, 2, -2, 2, -0.3, -0.04)
    y = -2.0
    while y < 2.0 - 1e-6:
        w = 0.4
        x = -2.0
        while x < 2.0 - 1e-6:
            L = min(r.choice([1.6, 2.0, 2.4, 4.0]), 2.0 - x)
            if 2.0 - (x + L) < 0.6:
                L = 2.0 - x
            p.bx(r.choice(["wood_plank", "wood_plank", "wood_plank_b"]), x + 0.012, x + L - 0.012, y + 0.012, y + w - 0.012, -0.1, r.uniform(-0.008, 0.0))
            x += L
        y += w


@floor
def floor_yard(p):
    p.ground("dirt_yard", relief=0.025)
    for _ in range(5):
        p.rock("stone_floor_b", p.rng.uniform(0.04, 0.09), (p.rng.uniform(-1.8, 1.8), p.rng.uniform(-1.8, 1.8), 0.0), scale=(1, 1, 0.5), sub=1)


@floor
def floor_lawn(p):
    p.ground("grass", relief=0.03)
    for _ in range(7):
        p.tuft("leaf", (p.rng.uniform(-1.8, 1.8), p.rng.uniform(-1.8, 1.8), 0.0), n=3, h=0.16, spread=0.1)


@floor
def floor_platform(p):
    slabs(p, [1.0, 1.0, 1.0, 1.0], ["stone_floor", "stone_floor_b"], gap=0.03)


@floor
def floor_ballast(p):
    """The bed of the line: cinders between the platforms, lower than them."""
    p.ground("stone_course", relief=0.03)
    for _ in range(26):
        p.rock("stone_floor_b" if p.rng.random() < 0.6 else "shadow", p.rng.uniform(0.05, 0.1), (p.rng.uniform(-1.9, 1.9), p.rng.uniform(-1.9, 1.9), 0.02), scale=(1, 1, 0.5), sub=1)


# ======================================================================================
# Furniture and the court's fittings
# ======================================================================================

@prop
def lamp_post(p):
    """An iron post and a lantern: the Academy's light after dusk."""
    p.cone("iron_metal", 0.24, 0.16, 0.3, (0, 0, 0), segs=8)
    p.cone("iron_metal", 0.075, 0.055, 3.5, (0, 0, 0.3), segs=6)
    p.cone("iron_metal", 0.12, 0.12, 0.08, (0, 0, 1.3), segs=6)
    p.bx("iron_metal", -0.4, 0.4, -0.03, 0.03, 3.5, 3.56)
    p.cone("iron_metal", 0.2, 0.26, 0.08, (0, 0, 3.8), segs=4)
    p.box("lamp_lit", (0.3, 0.3, 0.42), (0, 0, 4.1))
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        p.bx("iron_metal", sx * 0.15 - 0.015, sx * 0.15 + 0.015, sy * 0.15 - 0.015, sy * 0.15 + 0.015, 3.88, 4.32)
    p.cone("iron_metal", 0.3, 0.04, 0.24, (0, 0, 4.32), segs=4)
    p.cone("brass_metal", 0.035, 0.0, 0.2, (0, 0, 4.56), segs=5)
    p.empty("light_lamp", (0, 0, 4.0))


@prop
def bench(p):
    p.bx("wood_plank", -1.1, 1.1, -0.26, 0.26, 0.5, 0.58)
    p.bx("wood_plank_b", -1.1, 1.1, 0.2, 0.28, 0.58, 1.05)
    for x in (-0.95, 0.95):
        p.bx("stone_dress", x - 0.1, x + 0.1, -0.26, 0.3, 0.0, 0.5)


@prop
def notice_board(p):
    """The board: a roofed frame on two posts, the postings pinned to it."""
    for x in (-1.25, 1.25):
        p.bx("wood_timber", x - 0.09, x + 0.09, -0.09, 0.09, 0.0, 3.1)
        p.bx("stone_dress", x - 0.2, x + 0.2, -0.2, 0.2, 0.0, 0.3)
    p.bx("wood_plank_b", -1.2, 1.2, -0.04, 0.04, 1.0, 2.7)
    p.bx("wood_timber", -1.3, 1.3, -0.07, 0.07, 2.7, 2.84)
    p.bx("wood_timber", -1.3, 1.3, -0.07, 0.07, 0.9, 1.02)
    p.prism("slate_tile", [(-0.55, 3.05), (0.55, 3.05), (0.0, 3.5)], -1.55, 1.55, plane="yz")
    p.bx("brass_metal", -0.5, 0.5, -0.09, -0.05, 2.5, 2.66)
    r = p.rng
    for i in range(9):
        x, z = -1.05 + (i % 5) * 0.44 + r.uniform(-0.05, 0.05), 1.15 + (i // 5) * 0.62 + r.uniform(-0.05, 0.08)
        w, h = r.uniform(0.28, 0.38), r.uniform(0.36, 0.5)
        p.box("paper" if i % 4 else "cloth_linen", (w, 0.02, h), (x + w / 2, -0.06, z + h / 2), rot=(0, r.uniform(-0.08, 0.08), 0))
        p.box("brass_metal" if i % 3 else "cloth_red", (0.05, 0.03, 0.05), (x + w / 2, -0.08, z + h - 0.04))
    p.lantern((0.0, -0.3, 3.0), bracket=0.01, light=True)


@prop
def brazier_great(p):
    """The fire that never goes out, in the middle of the Quad: a stone drum, an iron bowl."""
    p.cone("stone_course", 1.5, 1.5, 0.22, (0, 0, 0), segs=12)
    p.cone("stone_dress", 1.15, 1.15, 0.22, (0, 0, 0.22), segs=12)
    p.cone("stone", 0.55, 0.45, 0.9, (0, 0, 0.44), segs=8)
    p.cone("iron_metal", 0.5, 0.95, 0.5, (0, 0, 1.34), segs=10)
    p.cone("brass_metal", 0.98, 0.98, 0.08, (0, 0, 1.8), segs=10)
    p.cone("shadow", 0.86, 0.86, 0.04, (0, 0, 1.86), segs=10)
    p.cone("flame_lit", 0.5, 0.0, 1.0, (0, 0, 1.85), segs=5)
    p.cone("flame_lit", 0.3, 0.0, 0.75, (0.3, 0.15, 1.85), segs=5)
    p.cone("flame_lit", 0.28, 0.0, 0.65, (-0.28, -0.2, 1.85), segs=5)
    p.empty("light_fire", (0, 0, 2.6))
    p.empty("socket_flame", (0, 0, 1.9))


@prop
def tree_court(p):
    """A court tree in a stone ring: an old plane, pollarded."""
    p.cone("stone_dress", 1.25, 1.25, 0.4, (0, 0, 0), segs=10)
    p.cone("dirt_yard", 1.05, 1.05, 0.04, (0, 0, 0.4), segs=10)
    wk.oak(p, (0, 0, 0.4), h=9.5, spread=0.8, canopies=5)


@prop
def ward_stone(p):
    """A standing stone of the Academy's ward: its sign cut in it and lit."""
    p.cone("stone_course", 0.6, 0.6, 0.2, (0, 0, 0), segs=6)
    p.cone("stone", 0.36, 0.26, 1.9, (0, 0, 0.2), segs=6)
    p.cone("stone_dress", 0.26, 0.0, 0.4, (0, 0, 2.1), segs=6)
    p.box("cool_lit", (0.16, 0.05, 0.5), (0, -0.3, 1.3))
    p.box("cool_lit", (0.4, 0.05, 0.12), (0, -0.31, 1.45))


@prop
def ward_post(p):
    """A post of the ward ring in the Yard: a low stone with the ward's light on it."""
    p.cone("stone_course", 0.24, 0.2, 0.7, (0, 0, 0), segs=6)
    p.cone("brass_metal", 0.21, 0.21, 0.06, (0, 0, 0.7), segs=6)
    p.cone("cool_lit", 0.1, 0.0, 0.26, (0, 0, 0.76), segs=5)


@prop
def training_post(p):
    """A pell: an oak post bound with rope, cut and re-cut."""
    p.cone("stone_course", 0.4, 0.4, 0.12, (0, 0, 0), segs=8)
    p.cone("wood_plank", 0.17, 0.15, 2.5, (0, 0, 0.1), segs=7)
    for z in (0.9, 1.5, 2.1):
        p.cone("rope", 0.2, 0.2, 0.22, (0, 0, z), segs=7)
    p.box("wood_plank_b", (1.2, 0.1, 0.12), (0, 0, 1.95))
    p.cone("iron_metal", 0.18, 0.16, 0.06, (0, 0, 2.58), segs=7)


@prop
def training_dummy(p):
    """A straw figure on a post with an old shield: something to hit that does not hit back."""
    p.cone("stone_course", 0.42, 0.42, 0.12, (0, 0, 0), segs=8)
    p.cone("wood_plank_b", 0.07, 0.07, 1.3, (0, 0, 0.1), segs=6)
    p.cone("straw", 0.3, 0.42, 1.0, (0, 0, 1.2), segs=8)
    p.cone("rope", 0.36, 0.36, 0.08, (0, 0, 1.55), segs=8)
    p.rock("straw", 0.26, (0, 0, 2.5), scale=(1, 1, 1.1), jitter=0.08, sub=1)
    p.box("wood_plank_b", (1.5, 0.09, 0.09), (0, 0, 2.05))
    p.cone("wood_door", 0.44, 0.44, 0.07, (-0.62, -0.14, 1.85), rot=(math.pi / 2, 0, 0), segs=10)
    p.cone("iron_metal", 0.12, 0.05, 0.1, (-0.62, -0.22, 1.85), rot=(math.pi / 2, 0, 0), segs=8)
    p.cone("cloth_red", 0.3, 0.3, 0.02, (-0.62, -0.19, 1.85), rot=(math.pi / 2, 0, 0), segs=4)


@prop
def weapon_rack(p):
    """A free-standing rack: practice blades and staves."""
    for x in (-1.0, 1.0):
        p.bx("wood_timber", x - 0.06, x + 0.06, -0.3, 0.3, 0.0, 0.12)
        p.bx("wood_timber", x - 0.05, x + 0.05, -0.05, 0.05, 0.0, 2.0)
    for z in (0.7, 1.8):
        p.bx("wood_plank", -1.05, 1.05, -0.06, 0.06, z, z + 0.1)
    r = p.rng
    for i in range(6):
        x = -0.8 + 0.32 * i
        lean = 0.12
        if i % 2:
            p.box("wood_plank_b", (0.06, 0.06, 2.3), (x, -0.12, 1.15), rot=(lean, 0, 0))
        else:
            L = r.uniform(1.2, 1.5)
            p.box("iron_metal", (0.09, 0.03, L), (x, -0.12, 0.75 + L / 2), rot=(lean, 0, 0))
            p.box("brass_metal", (0.3, 0.05, 0.06), (x, -0.1, 0.72), rot=(lean, 0, 0))
            p.box("wood_door", (0.06, 0.05, 0.36), (x, -0.08, 0.52), rot=(lean, 0, 0))


@prop
def barrel(p):
    p.cone("wood_plank", 0.36, 0.42, 0.5, (0, 0, 0), segs=10)
    p.cone("wood_plank", 0.42, 0.36, 0.5, (0, 0, 0.5), segs=10)
    for z in (0.12, 0.5, 0.86):
        p.cone("iron_metal", 0.43 if z == 0.5 else 0.39, 0.43 if z == 0.5 else 0.39, 0.05, (0, 0, z), segs=10)
    p.cone("wood_plank_b", 0.33, 0.33, 0.02, (0, 0, 0.98), segs=10)


@prop
def chest(p):
    """A footlocker: every student has one at the bunk's foot."""
    p.bx("wood_plank", -0.55, 0.55, -0.3, 0.3, 0.05, 0.5)
    p.prism("wood_plank_b", [(-0.3, 0.5), (0.3, 0.5), (0.22, 0.66), (-0.22, 0.66)], -0.55, 0.55, plane="yz")
    for x in (-0.4, 0.4):
        p.bx("iron_metal", x - 0.04, x + 0.04, -0.32, 0.32, 0.05, 0.52)
    p.box("brass_metal", (0.12, 0.04, 0.14), (0, -0.31, 0.42))
    for x in (-0.5, 0.5):
        p.bx("wood_timber", x - 0.05, x + 0.05, -0.28, 0.28, 0.0, 0.05)


@prop
def bunk(p):
    """A bunk for two: timber posts, two beds with blankets, a ladder. Long along Y."""
    r = p.rng
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.bx("wood_timber", sx * 0.62 - 0.07, sx * 0.62 + 0.07, sy * 1.2 - 0.07, sy * 1.2 + 0.07, 0.0, 3.0)
    for z, cloth in ((0.55, r.choice(["cloth_red", "cloth_blue", "cloth_green"])), (2.0, r.choice(["cloth_blue", "cloth_green", "cloth_red"]))):
        p.bx("wood_plank", -0.62, 0.62, -1.2, 1.2, z, z + 0.14)
        p.bx("cloth_linen", -0.55, 0.55, -1.12, 1.12, z + 0.14, z + 0.32)
        p.bx(cloth, -0.58, 0.58, -0.75, 1.14, z + 0.3, z + 0.4)
        p.bx("cloth_linen", -0.4, 0.4, -1.08, -0.78, z + 0.32, z + 0.46)
        for sx in (-1, 1):
            p.bx("wood_timber", sx * 0.62 - 0.03, sx * 0.62 + 0.03, -1.2, 1.2, z + 0.4, z + 0.52)
    for sy in (-1, 1):
        p.bx("wood_plank_b", -0.62, 0.62, sy * 1.2 - 0.03, sy * 1.2 + 0.03, 2.5, 2.9)
        p.bx("wood_plank_b", -0.62, 0.62, sy * 1.2 - 0.03, sy * 1.2 + 0.03, 1.0, 1.4)
    # the ladder at the foot
    for x in (-0.25, 0.25):
        p.bx("wood_timber", x - 0.03, x + 0.03, 1.26, 1.32, 0.0, 2.2)
    for z in (0.45, 0.9, 1.35, 1.8):
        p.bx("wood_timber", -0.25, 0.25, 1.26, 1.32, z, z + 0.05)


@prop
def stove(p):
    """The dormitory's iron stove, its pipe up into the roof, the door glowing."""
    p.cone("stone_course", 0.75, 0.75, 0.1, (0, 0, 0), segs=8)
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        p.bx("iron_metal", sx * 0.3 - 0.04, sx * 0.3 + 0.04, sy * 0.3 - 0.04, sy * 0.3 + 0.04, 0.1, 0.35)
    p.cone("iron_metal", 0.45, 0.42, 1.0, (0, 0, 0.35), segs=8)
    p.cone("iron_metal", 0.5, 0.5, 0.07, (0, 0, 1.35), segs=8)
    p.cone("iron_metal", 0.13, 0.13, 5.0, (0, 0.15, 1.4), segs=6)
    p.box("flame_lit", (0.3, 0.05, 0.26), (0, -0.44, 0.8))
    p.box("iron_metal", (0.4, 0.04, 0.05), (0, -0.46, 0.96))
    p.box("iron_metal", (0.05, 0.04, 0.3), (0, -0.47, 0.8))
    p.cone("brass_metal", 0.16, 0.2, 0.22, (0.2, -0.1, 1.42), segs=8)
    p.empty("light_fire", (0, -0.9, 1.0))


@prop
def rug(p):
    p.bx("cloth_red", -1.6, 1.6, -1.0, 1.0, 0.0, 0.035)
    p.bx("cloth_gold", -1.4, 1.4, -0.8, 0.8, 0.03, 0.045)
    p.bx("cloth_blue", -1.25, 1.25, -0.65, 0.65, 0.04, 0.055)
    p.bx("cloth_gold", -0.3, 0.3, -0.3, 0.3, 0.05, 0.062)


@prop
def desk(p):
    """A writing desk and its stool, a lamp and papers."""
    p.bx("wood_plank", -0.8, 0.8, -0.4, 0.4, 1.0, 1.08)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.bx("wood_timber", sx * 0.7 - 0.05, sx * 0.7 + 0.05, sy * 0.32 - 0.05, sy * 0.32 + 0.05, 0.0, 1.0)
    p.bx("wood_plank_b", -0.75, 0.75, 0.3, 0.38, 0.5, 1.0)
    p.box("paper", (0.4, 0.3, 0.02), (-0.25, 0.0, 1.09), rot=(0, 0, 0.2))
    p.box("paper", (0.3, 0.22, 0.02), (0.1, -0.1, 1.1), rot=(0, 0, -0.3))
    p.cone("brass_metal", 0.1, 0.07, 0.08, (0.5, 0.15, 1.08), segs=6)
    p.box("lamp_lit", (0.12, 0.12, 0.2), (0.5, 0.15, 1.26))
    p.cone("brass_metal", 0.1, 0.02, 0.1, (0.5, 0.15, 1.36), segs=6)
    p.cone("wood_plank_b", 0.24, 0.24, 0.07, (0.0, -0.75, 0.62), segs=8)
    for i in range(3):
        a = 2.1 * i
        p.cone("wood_timber", 0.03, 0.04, 0.62, (0.16 * math.cos(a), -0.75 + 0.16 * math.sin(a), 0.0), segs=5)
    p.empty("light_lamp.small", (0.5, 0.15, 1.5))


@prop
def table_long(p):
    """A hall table: trestles under a long board, bowls and a jug. Long along X."""
    p.bx("wood_plank", -2.4, 2.4, -0.55, 0.55, 1.0, 1.1)
    for x in (-1.9, 0.0, 1.9):
        p.bx("wood_timber", x - 0.06, x + 0.06, -0.5, 0.5, 0.88, 1.0)
        for sy in (-1, 1):
            p.box("wood_timber", (0.1, 0.1, 1.0), (x, sy * 0.3, 0.46), rot=(sy * 0.28, 0, 0))
    p.bx("wood_timber", -1.9, 1.9, -0.04, 0.04, 0.4, 0.5)
    r = p.rng
    for i in range(6):
        x, y = -2.0 + i * 0.8 + r.uniform(-0.1, 0.1), r.choice([-0.3, 0.3])
        p.cone("wood_plank_b", 0.1, 0.15, 0.07, (x, y, 1.1), segs=8)
    p.cone("brass_metal", 0.1, 0.13, 0.3, (0.3, 0.0, 1.1), segs=8)
    p.cone("brass_metal", 0.06, 0.05, 0.12, (-0.9, 0.05, 1.1), segs=6)
    p.box("lamp_lit", (0.05, 0.05, 0.16), (-0.9, 0.05, 1.3))


@prop
def bench_long(p):
    p.bx("wood_plank_b", -2.3, 2.3, -0.2, 0.2, 0.52, 0.6)
    for x in (-1.9, 0.0, 1.9):
        p.bx("wood_timber", x - 0.05, x + 0.05, -0.18, 0.18, 0.0, 0.52)
    p.bx("wood_timber", -1.9, 1.9, -0.03, 0.03, 0.2, 0.28)


@prop
def rite_bowl(p):
    """The Hearth Hall's bowl, where the rite is read: a broad basin on a carved drum."""
    p.cone("stone_course", 1.2, 1.2, 0.16, (0, 0, 0), segs=12)
    p.cone("stone_dress", 0.95, 0.95, 0.14, (0, 0, 0.16), segs=12)
    p.cone("stone", 0.42, 0.34, 0.55, (0, 0, 0.3), segs=8)
    p.cone("stone", 0.4, 1.0, 0.36, (0, 0, 0.85), segs=12)
    p.cone("brass_metal", 1.03, 1.03, 0.07, (0, 0, 1.21), segs=12)
    p.cone("shadow", 0.9, 0.9, 0.03, (0, 0, 1.27), segs=12)
    for i in range(6):
        a = 2 * math.pi * i / 6
        p.box("brass_metal", (0.1, 0.03, 0.2), (0.38 * math.cos(a), 0.38 * math.sin(a), 0.6), rot=(0, 0, a + math.pi / 2))
    p.empty("socket_flame", (0, 0, 1.3))


@prop
def buffer_stop(p):
    """Where the Academy's line ends: timber baulks, iron, a red lamp."""
    for y in (-0.72, 0.72):
        p.box("iron_metal", (0.14, 0.14, 1.5), (0.3, y, 0.7), rot=(0, 0.55, 0))
        p.box("iron_metal", (0.14, 0.14, 1.3), (-0.25, y, 0.6))
    p.bx("wood_timber", -0.45, -0.1, -1.1, 1.1, 0.95, 1.4)
    p.bx("iron_metal", -0.5, -0.44, -1.0, 1.0, 1.05, 1.3)
    for y in (-0.6, 0.6):
        p.cone("iron_metal", 0.16, 0.16, 0.14, (-0.5, y, 1.17), rot=(0, -math.pi / 2, 0), segs=8)
    p.box("flame_lit", (0.16, 0.16, 0.2), (-0.28, 0.0, 1.55))
    p.cone("iron_metal", 0.14, 0.02, 0.12, (-0.28, 0.0, 1.65), segs=4)


@prop
def signal_lamp(p):
    """A signal of the line: a tall iron post, an arm, the blue lamp that says the way is held."""
    p.cone("iron_metal", 0.3, 0.2, 0.3, (0, 0, 0), segs=8)
    p.cone("iron_metal", 0.09, 0.07, 5.2, (0, 0, 0.3), segs=6)
    p.bx("iron_metal", -0.04, 0.04, -1.3, 0.1, 4.9, 5.05)
    p.bx("cloth_red", -0.03, 0.03, -1.3, -0.75, 4.8, 5.15)
    p.box("cool_lit", (0.26, 0.26, 0.34), (0, 0, 5.7))
    p.cone("iron_metal", 0.24, 0.03, 0.2, (0, 0, 5.87), segs=4)
    p.box("iron_metal", (0.3, 0.3, 0.05), (0, 0, 5.5))
    for z in (1.0, 1.6, 2.2, 2.8, 3.4, 4.0):
        p.bx("iron_metal", -0.2, 0.2, 0.06, 0.1, z, z + 0.04)
    p.empty("light_cool", (0, -0.2, 5.6))


@prop
def luggage(p):
    """Trunks and a bag on the platform: someone is always leaving or arriving."""
    p.bx("wood_door", -0.6, 0.6, -0.35, 0.35, 0.0, 0.6)
    for x in (-0.45, 0.45):
        p.bx("brass_metal", x - 0.04, x + 0.04, -0.37, 0.37, 0.0, 0.62)
    p.box("cloth_blue", (0.8, 0.5, 0.4), (0.15, 0.05, 0.8), rot=(0, 0, 0.3))
    p.bx("wood_plank", 0.75, 1.35, -0.25, 0.25, 0.0, 0.42)
    p.box("iron_metal", (0.62, 0.52, 0.03), (1.05, 0.0, 0.43))
    p.rock("cloth_linen", 0.28, (-0.2, -0.65, 0.22), scale=(1.2, 0.8, 0.8), jitter=0.1, sub=1)


@prop
def hedge(p):
    """A clipped hedge, 4 long along X: the lawn's border."""
    p.bx("leaf", -2, 2, -0.3, 0.3, 0.0, 0.8)
    for i in range(8):
        p.rock("grass", 0.2, (-1.75 + i * 0.5, p.rng.uniform(-0.1, 0.1), 0.8), scale=(1.3, 1.4, 0.5), jitter=0.2, sub=1)


@prop
def platform_edge(p):
    """The platform's lip over the line, 4 long along X: a kerb with a painted edge."""
    p.bx("stone_dress", -2, 2, -0.3, 0.0, -0.35, 0.02)
    p.bx("paper", -2, 2, -0.3, -0.22, 0.0, 0.03)


PIECES = {}
PIECES.update(WALLS)
PIECES.update(CORNERS)
PIECES.update(FLOORS)
PIECES.update(PROPS)


def build(name):
    """Build one piece into an empty scene and return its objects."""
    wk.reset()
    if name in WALLS or name in CORNERS:
        lo, up = P("Plinth"), P("Upper")
        lo.rng.seed(name + "/lo")
        up.rng.seed(name + "/up")
        PIECES[name](lo, up)
        objs = lo.finish() + up.finish()
        wk.TRIS[name] = wk.TRIS.pop("Plinth", 0) + wk.TRIS.pop("Upper", 0)
        return objs
    p = P(name)
    PIECES[name](p)
    return p.finish()


if __name__ == "__main__":
    args = sys.argv[1:]
    sheet = None
    if "--sheet" in args:
        i = args.index("--sheet")
        sheet = args[i + 1]
        args = args[:i] + args[i + 2:]
    wanted = args or list(PIECES)
    cells = []
    for name in wanted:
        objs = build(name)
        wk.export(os.path.join(OUT, name + ".glb"), objs)
        if sheet:
            cell = os.path.join(os.path.dirname(sheet), "academy_cells", name + ".png")
            wk.render_card(name, objs, cell)
            cells.append(cell)
    if sheet:
        wk.reset()
        wk.compose_sheet(cells, sheet)
    print("triangles:", ", ".join("%s %d" % (n, wk.TRIS.get(n, 0)) for n in wanted))
