"""WILDLINE wild kit: the outdoor places of the line, built in Blender and exported where the
game looks for them. Ground tiles, edge pieces, props and set pieces for four zones on a
railway through hills, a river ruin, a junction and a river crossing, at night under the moon.
Modelled on tools/blender/genius_kit.py. Run headless with Blender's Python module:

    python tools/blender/wild_kit.py                   # every piece
    python tools/blender/wild_kit.py tree_oak set_den  # some pieces
    python tools/blender/wild_kit.py --sheet /tmp/wild_sheet.png   # also a contact sheet

Conventions (the game relies on them):
  - Blender is Z up and the model faces -Y; the glTF export turns that into the game's Y up,
    +Z forward. One .glb per piece at game/assets/wild/<name>.glb.
  - Origin at the ground centre of the piece's footprint; the top of a ground tile is at
    y = 0 in the game (a few centimetres of relief above it); ground_water's top is at -0.08.
  - Ground tiles are 4 x 4 m. Edge pieces are 4 m wide along X, about 2 m deep, with their
    back at +Y and their face toward -Y (the inside of the arena).
  - The railway runs along X in every piece that has one (ground_ballast's ties lie across
    it, rail_car and set_car are long along X, set_junction's gantry spans the line with its
    legs at +Y and -Y). Rotate the whole line together.
  - Flat-shaded low poly, no textures. Materials are named from a small palette (moss, grass,
    bark, leaf, stone, ruin, water, iron, bone, earth, reed, shadow) and vary slightly in
    colour from piece to piece. Materials whose names start with "field" glow and the game
    tints them (lamps). set_post carries an empty named socket_flame at its top.
  - Budgets: props and tiles under 2k triangles, set pieces under 8k.
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style  # noqa: E402  (the game's one style: data/style.json, docs/style.md)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "wild")

# The art bible's earths, linear-ish: muted so the field's colour and the lamps carry the eye.
PALETTE = {
    "moss": ((0.15, 0.24, 0.11), 0.9),
    "grass": ((0.20, 0.27, 0.10), 0.9),
    "bark": ((0.15, 0.10, 0.065), 0.9),
    "leaf": ((0.10, 0.21, 0.085), 0.85),
    "stone": ((0.30, 0.29, 0.27), 0.85),
    "ruin": ((0.36, 0.31, 0.25), 0.8),
    "water": ((0.015, 0.05, 0.065), 0.15),
    "iron": ((0.085, 0.085, 0.105), 0.55),
    "bone": ((0.56, 0.49, 0.37), 0.6),
    "earth": ((0.18, 0.125, 0.075), 0.95),
    "reed": ((0.36, 0.32, 0.14), 0.85),
    "shadow": ((0.004, 0.004, 0.005), 1.0),
}
TRIS = {}  # piece name -> triangle count, for the report


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, rough=0.8, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    color = style.conform(name, color)      # on the ramps of what its name says it is
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = strength
    return m


def palette_material(name, rng, tint=(1, 1, 1)):
    """A palette material, its colour nudged a little for this piece so no two pieces match."""
    if name.startswith("field"):
        return material(name, (0.9, 0.85, 0.7, 1), 0.4, emission=(1.0, 0.85, 0.6, 1), strength=2.0)
    base, rough = PALETTE[name]
    v = rng.uniform(0.88, 1.12)
    col = tuple(min(1.0, c * v * t * rng.uniform(0.94, 1.06)) for c, t in zip(base, tint)) + (1,)
    if name == "water":
        return material(name, col, rough, emission=(0.03, 0.14, 0.16, 1), strength=0.12)
    return material(name, col, rough)


def xform(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1))


class Piece:
    """One exported mesh, grown from flat-shaded primitives, each face tagged with a palette material."""

    def __init__(self, name):
        self.name = name
        self.rng = random.Random(name)
        self.bm = bmesh.new()
        self.mats = []
        self.tints = {}
        self.empties = []
        self.frame = Matrix.Identity(4)  # a transform every primitive goes through (a listing wreck)

    def tint(self, mat, rgb):
        """Shift one material for this piece (pines bluer, mud darker)."""
        self.tints[mat] = rgb

    def mat_index(self, name):
        m = bpy.data.materials.get(name)
        if m is None:
            m = palette_material(name, self.rng, self.tints.get(name, (1, 1, 1)))
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, bm, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        """Take a temporary bmesh into the piece, placed, flat and tagged with mat."""
        bmesh.ops.transform(bm, matrix=self.frame @ xform(loc, rot, scale), verts=bm.verts[:])
        idx = self.mat_index(mat)
        for f in bm.faces:
            f.smooth = False
            f.material_index = idx
        mesh = bpy.data.meshes.new("tmp")
        bm.to_mesh(mesh)
        bm.free()
        self.bm.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)

    def retag(self, mat, chance, where=lambda f: True):
        """Speckle: retag some faces that pass `where` to another material (moss on stone, cinders on ballast)."""
        idx = self.mat_index(mat)
        for f in self.bm.faces:
            if where(f) and self.rng.random() < chance:
                f.material_index = idx

    # --- primitives, every one placed by its base unless said otherwise ---------------------

    def box(self, mat, size, loc, rot=(0, 0, 0)):
        """A block centred at loc."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        self.add(bm, mat, loc, rot, size)

    def block(self, mat, size, loc, rot=(0, 0, 0)):
        """A block standing on loc (its base centre), rotated about that base."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.transform(bm, matrix=Matrix.Translation((0, 0, 0.5)), verts=bm.verts[:])
        self.add(bm, mat, loc, rot, size)

    def cone(self, mat, r1, r2, h, loc, rot=(0, 0, 0), segs=8):
        """A cylinder or cone standing on loc, rotated about its base."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segs, radius1=r1, radius2=r2, depth=h)
        bmesh.ops.transform(bm, matrix=Matrix.Translation((0, 0, h / 2)), verts=bm.verts[:])
        self.add(bm, mat, loc, rot)

    def rock(self, mat, r, loc, scale=(1, 1, 1), rot=(0, 0, 0), jitter=0.22, sub=2):
        """A boulder: a jittered icosphere, centred at loc."""
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        for v in bm.verts:
            v.co += v.co.normalized() * self.rng.uniform(-jitter, jitter) * r
            v.co.x += self.rng.uniform(-0.04, 0.04) * r
        self.add(bm, mat, loc, rot, scale)

    def chunk(self, mat, size, loc, rot=(0, 0, 0), jitter=0.12, cuts=1):
        """A craggy block: a cube cut and jittered, standing on loc. Cliffs, broken stone."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        if cuts > 0:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
        for v in bm.verts:
            if v.co.z > -0.49:
                v.co += Vector((self.rng.uniform(-jitter, jitter), self.rng.uniform(-jitter, jitter), self.rng.uniform(-jitter, jitter)))
        bmesh.ops.transform(bm, matrix=Matrix.Translation((0, 0, 0.5)), verts=bm.verts[:])
        self.add(bm, mat, loc, rot, size)

    def shell(self, mat, outline, height, flare=1.1, inset=1.0, z=0.0, inward=False):
        """An open tub: an outline on the ground raised into flared walls with no top (a hull).
        Faces point outward, or inward for a lining."""
        bm = bmesh.new()
        verts = [bm.verts.new((x * inset, y * inset, z)) for x, y in outline]
        bottom = bm.faces.new(verts)
        ext = bmesh.ops.extrude_face_region(bm, geom=[bottom])
        for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
            v.co.z = z + height
            v.co.x *= flare
            v.co.y *= flare
        bmesh.ops.delete(bm, geom=[g for g in ext["geom"] if isinstance(g, bmesh.types.BMFace)], context="FACES_ONLY")
        centre = Vector((0, 0, z + height * 0.5))
        bm.normal_update()
        for f in bm.faces:
            out = (f.calc_center_median() - centre).dot(f.normal) > 0
            if out == inward:
                f.normal_flip()
        self.add(bm, mat)

    def ground(self, mat, size=4.0, segs=6, relief=0.03, low=None, skirt=0.25):
        """A tile's top: a grid at z = 0 with a little relief inside (the rim stays at 0 so tiles
        meet), and a skirt hanging below the rim so slopes never show the void."""
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=segs, y_segments=segs, size=size / 2)
        half = size / 2 - 1e-4
        for v in bm.verts:
            if abs(v.co.x) < half and abs(v.co.y) < half:
                v.co.z = self.rng.uniform(low if low is not None else -relief, relief)
                v.co.x += self.rng.uniform(-0.08, 0.08)
                v.co.y += self.rng.uniform(-0.08, 0.08)
        rim = [e for e in bm.edges if e.is_boundary]
        ext = bmesh.ops.extrude_edge_only(bm, edges=rim)
        verts = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, 0, -skirt), verts=verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        self.add(bm, mat)

    def blade(self, mat, h, w, loc, lean=(0, 0), segs=3):
        """A grass blade or reed: a thin three-sided spike, leaning."""
        self.cone(mat, w, 0.0, h, loc, rot=(lean[0], lean[1], self.rng.uniform(0, 6.28)), segs=segs)

    def tuft(self, mat, at, n=5, h=0.35, spread=0.14):
        for _ in range(n):
            a = self.rng.uniform(0, 6.28)
            d = self.rng.uniform(0, spread)
            self.blade(mat, h * self.rng.uniform(0.6, 1.2), 0.035, (at[0] + math.cos(a) * d, at[1] + math.sin(a) * d, at[2]), lean=(self.rng.uniform(-0.35, 0.35), self.rng.uniform(-0.35, 0.35)))

    def reeds(self, at, n=9, h=1.6, spread=0.3, mat="reed"):
        """A clump of reeds with dark seed-heads."""
        for _ in range(n):
            a = self.rng.uniform(0, 6.28)
            d = self.rng.uniform(0, spread)
            hh = h * self.rng.uniform(0.7, 1.15)
            lean = (self.rng.uniform(-0.18, 0.18), self.rng.uniform(-0.18, 0.18))
            base = (at[0] + math.cos(a) * d, at[1] + math.sin(a) * d, at[2])
            self.blade(mat, hh, 0.03, base, lean=lean)
            if self.rng.random() < 0.6:
                tip = Euler((lean[0], lean[1], 0)).to_matrix() @ Vector((0, 0, hh * 0.86))
                self.box("bark", (0.05, 0.05, 0.16), (base[0] + tip.x, base[1] + tip.y, base[2] + tip.z), rot=(lean[0], lean[1], 0))

    def branches(self, chain, mat):
        """Branches grown by the skin modifier (no smoothing: chunky, woodcut). chain is
        [(position, radius, parent_index), ...]."""
        mesh = bpy.data.meshes.new("branches")
        obj = bpy.data.objects.new("branches", mesh)
        bpy.context.collection.objects.link(obj)
        bm = bmesh.new()
        verts = []
        for i, p in enumerate(chain):
            v = bm.verts.new(Vector(p[0]))
            verts.append(v)
            parent = p[2] if len(p) > 2 else i - 1
            if parent >= 0:
                bm.edges.new((verts[parent], v))
        bm.to_mesh(mesh)
        bm.free()
        obj.modifiers.new("skin", "SKIN")
        for i, p in enumerate(chain):
            obj.data.skin_vertices[0].data[i].radius = (p[1], p[1])
        obj.data.skin_vertices[0].data[0].use_root = True
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier="skin")
        obj.select_set(False)
        idx = self.mat_index(mat)
        for poly in obj.data.polygons:
            poly.material_index = idx
            poly.use_smooth = False
        self.bm.from_mesh(obj.data)
        bpy.data.objects.remove(obj)
        bpy.data.meshes.remove(mesh)

    def empty(self, name, at):
        e = bpy.data.objects.new(name, None)
        e.empty_display_size = 0.2
        e.location = at
        bpy.context.collection.objects.link(e)
        self.empties.append(e)
        return e

    def finish(self):
        """The piece as one object (plus its empties), ready to export or render."""
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-5)
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in self.mats:
            mesh.materials.append(m)
        for poly in mesh.polygons:
            poly.use_smooth = False
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        TRIS[self.name] = sum(len(p.vertices) - 2 for p in mesh.polygons)
        return [obj] + self.empties


def export(path, objects):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects if o.type == "MESH")
    print("wrote", os.path.relpath(path, ROOT), tris, "tris")


# ======================================================================================
# Trees (shared by props and treelines)
# ======================================================================================

def oak(p, at, h=7.0, spread=1.0, canopies=5):
    """An oak: a thick trunk forking into branches, a crown of lumpy canopies."""
    x, y, z = at
    r = h / 7.0
    chain = [((x, y, z - 0.1), 0.42 * r), ((x, y, z + h * 0.18), 0.34 * r), ((x + 0.1 * r, y, z + h * 0.36), 0.28 * r)]
    for i in range(4):
        a = i * 1.57 + p.rng.uniform(-0.4, 0.4)
        d = h * 0.26 * spread
        chain.append(((x + math.cos(a) * d * 0.5, y + math.sin(a) * d * 0.5, z + h * 0.5), 0.16 * r, 2))
        chain.append(((x + math.cos(a) * d, y + math.sin(a) * d, z + h * 0.66), 0.08 * r, len(chain) - 1))
    p.branches(chain, "bark")
    for i in range(canopies):
        a = i * 6.28 / canopies + p.rng.uniform(-0.3, 0.3)
        d = h * 0.2 * spread * (0 if i == canopies - 1 else 1)
        rad = h * p.rng.uniform(0.2, 0.26) * spread
        zz = z + h * (0.78 if i == canopies - 1 else p.rng.uniform(0.62, 0.72))
        p.rock("leaf", rad, (x + math.cos(a) * d, y + math.sin(a) * d, zz), scale=(1, 1, 0.75), jitter=0.18, sub=2)


def pine(p, at, h=9.0, tiers=4):
    """A pine: a straight trunk under a stack of cones."""
    x, y, z = at
    p.cone("bark", 0.28 * h / 9, 0.1 * h / 9, h * 0.62, (x, y, z - 0.05), segs=7)
    for i in range(tiers):
        f = i / tiers
        rad = h * (0.24 - 0.15 * f) * p.rng.uniform(0.9, 1.1)
        base = z + h * (0.22 + 0.58 * f)
        p.cone("leaf", rad, 0.0, h * 0.3, (x + p.rng.uniform(-0.1, 0.1), y + p.rng.uniform(-0.1, 0.1), base), rot=(p.rng.uniform(-0.05, 0.05), p.rng.uniform(-0.05, 0.05), 0), segs=8)


def dead_tree(p, at, h=6.5):
    """A dead tree: a gnarled trunk, bare branches, a split crown."""
    x, y, z = at
    r = h / 6.5
    chain = [((x, y, z - 0.1), 0.3 * r), ((x + 0.1, y, z + h * 0.25), 0.24 * r), ((x + 0.25, y - 0.1, z + h * 0.5), 0.17 * r), ((x + 0.5, y - 0.2, z + h * 0.75), 0.1 * r), ((x + 0.9, y - 0.3, z + h), 0.03 * r)]
    for i, (a, k, lift) in enumerate(((0.9, 1, 0.35), (3.6, 2, 0.3), (2.2, 2, 0.4), (5.2, 3, 0.3))):
        px, py, pz = chain[k][0]
        d = h * 0.22
        chain.append(((px + math.cos(a) * d * 0.6, py + math.sin(a) * d * 0.6, pz + h * lift * 0.5), 0.07 * r, k))
        chain.append(((px + math.cos(a) * d, py + math.sin(a) * d, pz + h * lift), 0.025 * r, len(chain) - 1))
    p.branches(chain, "bark")
    # A stub where a limb broke off.
    p.cone("bark", 0.09 * r, 0.05 * r, 0.8 * r, (x + 0.1, y, z + h * 0.3), rot=(-1.3, 0.2, 0), segs=6)


# ======================================================================================
# Ground tiles
# ======================================================================================

def ground_grass_a(p):
    p.ground("grass", relief=0.03)
    p.retag("moss", 0.18, lambda f: f.calc_center_median().z > -0.1)
    return p


def ground_grass_b(p):
    p.ground("grass", relief=0.035)
    p.retag("moss", 0.15, lambda f: f.calc_center_median().z > -0.1)
    for _ in range(11):
        p.tuft("grass", (p.rng.uniform(-1.8, 1.8), p.rng.uniform(-1.8, 1.8), 0.0))
    return p


def ground_grass_rocky(p):
    p.ground("grass", relief=0.04)
    p.retag("earth", 0.12, lambda f: f.calc_center_median().z > -0.1)
    for _ in range(6):
        r = p.rng.uniform(0.18, 0.42)
        p.rock("stone", r, (p.rng.uniform(-1.6, 1.6), p.rng.uniform(-1.6, 1.6), r * 0.25), scale=(1.2, 1.0, 0.7))
    for _ in range(4):
        p.tuft("grass", (p.rng.uniform(-1.8, 1.8), p.rng.uniform(-1.8, 1.8), 0.0), n=3)
    return p


def ground_earth(p):
    p.ground("earth", relief=0.04)
    p.retag("moss", 0.08, lambda f: f.calc_center_median().z > -0.1)
    p.retag("stone", 0.05, lambda f: f.calc_center_median().z > -0.1)
    for _ in range(3):
        p.rock("stone", 0.12, (p.rng.uniform(-1.7, 1.7), p.rng.uniform(-1.7, 1.7), 0.03), scale=(1.3, 1, 0.6))
    return p


def ground_ruin_floor(p):
    p.ground("earth", relief=0.02, low=-0.07)
    n = 4
    pitch = 4.0 / n
    for i in range(n):
        for j in range(n):
            if p.rng.random() < 0.14:
                continue  # a flagstone lost to the roots
            cx = -2 + pitch * (i + 0.5) + p.rng.uniform(-0.03, 0.03)
            cy = -2 + pitch * (j + 0.5) + p.rng.uniform(-0.03, 0.03)
            tilt = (p.rng.uniform(-0.03, 0.03), p.rng.uniform(-0.03, 0.03), p.rng.uniform(-0.04, 0.04))
            if p.rng.random() < 0.3:  # cracked in two
                off = p.rng.uniform(0.15, 0.3)
                p.block("ruin", (pitch * 0.45, pitch * 0.9, 0.08), (cx - off, cy, -0.06), rot=tilt)
                p.block("ruin", (pitch * 0.4, pitch * 0.88, 0.07), (cx + off * 0.9, cy + 0.05, -0.065), rot=(tilt[0], -tilt[1], tilt[2] + 0.06))
            else:
                p.block("ruin", (pitch * 0.9, pitch * 0.9, 0.08), (cx, cy, -0.06), rot=tilt)
    p.retag("moss", 0.1, lambda f: f.calc_center_median().z > -0.1)
    for _ in range(3):
        p.tuft("grass", (p.rng.uniform(-1.7, 1.7), p.rng.uniform(-1.7, 1.7), -0.04), n=3, h=0.25)
    return p


def ground_ballast(p):
    """A rail bed: crushed stone crowned down the middle, timber ties across it. No rails."""
    p.ground("stone", relief=0.02, segs=8)
    # The crown: inside verts rise toward y = 0.
    for v in p.bm.verts:
        if abs(v.co.x) < 1.99 and abs(v.co.y) < 1.99:
            v.co.z += 0.05 * (1 - abs(v.co.y) / 2.0)
    p.retag("earth", 0.22, lambda f: f.calc_center_median().z > -0.1)
    p.retag("iron", 0.1, lambda f: f.calc_center_median().z > -0.1)
    for i in range(6):
        x = -1.75 + i * 0.7 + p.rng.uniform(-0.03, 0.03)
        p.block("bark", (0.24, 2.5, 0.15), (x, p.rng.uniform(-0.03, 0.03), -0.02), rot=(0, 0, p.rng.uniform(-0.03, 0.03)))
    return p


def ground_reeds(p):
    p.tint("earth", (0.8, 0.85, 0.9))
    p.ground("earth", relief=0.02, low=-0.05)
    for _ in range(5):
        p.reeds((p.rng.uniform(-1.6, 1.6), p.rng.uniform(-1.6, 1.6), -0.02), n=8, h=p.rng.uniform(1.2, 1.7))
    p.retag("moss", 0.1, lambda f: f.calc_center_median().z > -0.1)
    return p


def ground_water(p):
    p.box("water", (4.0, 4.0, 0.3), (0, 0, -0.23))
    return p


def ground_mud(p):
    p.tint("earth", (0.75, 0.8, 0.85))
    p.ground("earth", relief=0.0, low=-0.06, segs=8)
    for _ in range(3):
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=7, radius=p.rng.uniform(0.35, 0.6))
        p.add(bm, "water", (p.rng.uniform(-1.3, 1.3), p.rng.uniform(-1.3, 1.3), 0.012), scale=(1.3, 1, 1))
    p.retag("moss", 0.05, lambda f: f.calc_center_median().z > -0.1)
    return p


# ======================================================================================
# Edge pieces: 4 m along X, back at +Y, face toward -Y
# ======================================================================================

def berm(p, mat="earth", top="moss"):
    p.rock(mat, 1.0, (0, 0.5, -0.35), scale=(2.6, 1.5, 0.75), jitter=0.12, sub=2)
    p.retag(top, 0.5, lambda f: f.normal.z > 0.4)


def edge_treeline(p):
    berm(p)
    for x, y, h in ((-1.4, 0.7, 5.0), (0.0, 0.4, 5.6), (1.35, 0.8, 4.6), (0.7, -0.4, 3.2)):
        oak(p, (x, y, 0.2), h=h, spread=0.75, canopies=3)
    for _ in range(3):
        p.rock("leaf", 0.5, (p.rng.uniform(-1.8, 1.8), p.rng.uniform(-0.9, 0.0), 0.3), scale=(1.3, 1, 0.8), sub=1)
    return p


def edge_treeline_pine(p):
    p.tint("leaf", (0.85, 0.9, 1.1))
    berm(p)
    for x, y, h in ((-1.5, 0.6, 7.0), (-0.2, 0.9, 8.0), (1.2, 0.5, 6.5), (0.6, -0.5, 4.5)):
        pine(p, (x, y, 0.2), h=h, tiers=4)
    return p


def edge_rocks(p):
    p.rock("earth", 1.0, (0, 0.6, -0.5), scale=(2.6, 1.4, 0.6), jitter=0.1, sub=1)
    for x, y, r, sz in ((-1.4, 0.4, 1.0, (1.3, 1.0, 0.9)), (0.2, 0.6, 1.2, (1.4, 1.1, 1.1)), (1.5, 0.3, 0.9, (1.1, 1.0, 0.8)),
                        (-0.5, -0.5, 0.55, (1.2, 1.0, 0.7)), (0.9, -0.6, 0.45, (1, 1, 0.7)), (-1.7, -0.3, 0.4, (1, 1, 0.6))):
        p.rock("stone", r, (x, y, r * sz[2] * 0.7), scale=sz, rot=(0, 0, p.rng.uniform(0, 3)), sub=2)
    p.retag("moss", 0.25, lambda f: f.normal.z > 0.5)
    return p


def edge_ruin_wall(p):
    """Broken masonry: courses of blocks, the top line fallen away, rubble at the foot."""
    profile = [1.4, 2.4, 3.0, 2.6, 1.8, 1.0, 0.6]  # wall height along X
    cols = 6
    bw, bh, bd = 4.0 / cols, 0.42, 0.6
    for c in range(cols):
        x = -2 + bw * 0.5 + c * (4.0 / cols) * 1.0
        hmax = profile[c] if c < len(profile) else 1.0
        z = 0.0
        row = 0
        while z + bh * 0.5 < hmax:
            off = (bw * 0.5 if row % 2 else 0) * 0.3
            h = bh * p.rng.uniform(0.9, 1.1)
            if z + h > hmax:
                h = max(0.15, hmax - z)
            p.block("ruin", (bw * 0.96, bd, h * 0.96), (x + off, 0.2 + p.rng.uniform(-0.02, 0.02), z), rot=(0, 0, p.rng.uniform(-0.03, 0.03)))
            z += h
            row += 1
    for _ in range(7):
        s = p.rng.uniform(0.2, 0.45)
        p.chunk("ruin", (s * 1.4, s, s * 0.8), (p.rng.uniform(-2, 2), p.rng.uniform(-0.9, -0.3), 0), rot=(0, 0, p.rng.uniform(0, 3)), cuts=0)
    p.retag("moss", 0.08, lambda f: True)
    return p


def edge_reeds(p):
    p.tint("earth", (0.8, 0.85, 0.9))
    p.rock("earth", 1.0, (0, 0.6, -0.45), scale=(2.6, 1.3, 0.55), jitter=0.1, sub=1)
    for x, y in ((-1.6, 0.3), (-0.8, 0.6), (0.0, 0.2), (0.8, 0.7), (1.6, 0.3), (-1.2, -0.3), (0.4, -0.4), (1.3, -0.4)):
        p.reeds((x, y, 0.0), n=8, h=p.rng.uniform(1.5, 2.1), spread=0.32)
    return p


def edge_fence(p):
    """A leaning post-and-rail fence along X, a rail down and a post gone."""
    xs = [-1.8, -0.6, 0.6, 1.8]
    posts = []
    for i, x in enumerate(xs):
        lean = (p.rng.uniform(-0.12, 0.12), p.rng.uniform(-0.1, 0.1), 0)
        h = 1.3 if i != 2 else 0.5  # a stump where a post broke
        p.block("bark", (0.16, 0.14, h), (x, 0.0, -0.05), rot=lean)
        posts.append((x, lean, h))
    for z in (0.55, 1.05):
        for i in range(len(xs) - 1):
            x0, x1 = xs[i], xs[i + 1]
            if i == 1 and z > 1.0:
                # the fallen rail, one end on the ground
                p.block("bark", (0.07, 0.12, 1.4), (x0 - 0.1, -0.15, 0.1), rot=(0, 1.2, 0.2))
                continue
            if i == 2 and z > 1.0:
                continue
            p.box("bark", (x1 - x0 + 0.1, 0.12, 0.07), ((x0 + x1) / 2, 0.0, z + p.rng.uniform(-0.04, 0.04)), rot=(0, p.rng.uniform(-0.03, 0.03), 0))
    for _ in range(4):
        p.tuft("grass", (p.rng.uniform(-1.9, 1.9), p.rng.uniform(-0.3, 0.3), -0.02), n=4)
    return p


def edge_cliff(p):
    """A rock face: a jagged craggy mass 5 m tall with boulders at its foot."""
    p.chunk("stone", (4.3, 2.0, 5.0), (0, 0.3, -0.3), jitter=0.13, cuts=3)
    p.chunk("stone", (2.4, 1.2, 1.6), (-0.9, -0.5, 3.4), jitter=0.1, cuts=1)
    p.chunk("stone", (1.6, 1.0, 1.2), (1.2, -0.4, 4.4), jitter=0.1, cuts=1)
    p.retag("moss", 0.3, lambda f: f.normal.z > 0.5)
    p.retag("earth", 0.1, lambda f: True)
    for x, r in ((-1.6, 0.55), (0.4, 0.4), (1.5, 0.65)):
        p.rock("stone", r, (x, -1.25, r * 0.6), scale=(1.2, 1, 0.8), sub=2)
    return p


# ======================================================================================
# Props
# ======================================================================================

def tree_oak(p):
    oak(p, (0, 0, 0), h=7.2, spread=1.0, canopies=5)
    return p


def tree_pine(p):
    p.tint("leaf", (0.85, 0.9, 1.1))
    pine(p, (0, 0, 0), h=9.5, tiers=5)
    return p


def tree_dead(p):
    p.tint("bark", (0.8, 0.8, 0.85))
    dead_tree(p, (0, 0, 0), h=6.5)
    return p


def tree_willow(p):
    """A willow: a leaning trunk, a low wide crown and a curtain of hanging strands."""
    p.branches([((0, 0, -0.1), 0.45), ((0.2, 0, 1.5), 0.36), ((0.5, -0.1, 3.0), 0.28), ((0.6, -0.2, 4.0), 0.2),
                ((1.6, 0.4, 4.4), 0.12, 2), ((-0.6, -0.5, 4.2), 0.12, 2)], "bark")
    p.rock("leaf", 2.6, (0.5, -0.1, 4.6), scale=(1.2, 1.1, 0.55), jitter=0.12, sub=2)
    for i in range(22):
        a = i * 6.28 / 22 + p.rng.uniform(-0.1, 0.1)
        rx, ry = 2.9 * math.cos(a) + 0.5, 2.6 * math.sin(a) - 0.1
        top = 4.3 + p.rng.uniform(-0.3, 0.3)
        length = p.rng.uniform(2.6, 3.9)
        p.cone("leaf", 0.09, 0.03, length, (rx, ry, top), rot=(math.pi + p.rng.uniform(-0.08, 0.08), p.rng.uniform(-0.08, 0.08), 0), segs=3)
    return p


def boulder_a(p):
    p.rock("stone", 1.0, (0, 0, 0.6), scale=(1.4, 1.1, 0.85), jitter=0.2, sub=3)
    p.retag("moss", 0.3, lambda f: f.normal.z > 0.5)
    return p


def boulder_b(p):
    p.rock("stone", 0.8, (-0.4, 0.2, 0.55), scale=(1.2, 1.0, 0.95), jitter=0.24, rot=(0, 0, 0.7), sub=2)
    p.rock("stone", 0.5, (0.7, -0.3, 0.3), scale=(1.3, 1.0, 0.7), jitter=0.2, sub=2)
    p.rock("stone", 0.3, (0.1, -0.8, 0.18), scale=(1.2, 1.0, 0.7), jitter=0.2, sub=2)
    p.retag("moss", 0.25, lambda f: f.normal.z > 0.5)
    return p


def stump(p):
    p.cone("bark", 0.5, 0.42, 0.65, (0, 0, -0.05), segs=9)
    p.cone("bone", 0.4, 0.4, 0.03, (0, 0, 0.6), segs=9)
    for a in (0.3, 1.9, 3.4, 5.0):
        p.cone("bark", 0.16, 0.05, 0.6, (math.cos(a) * 0.35, math.sin(a) * 0.35, 0.05), rot=(0, 1.35, a), segs=5)
    p.tuft("moss", (0.45, 0.3, 0.0), n=4, h=0.25)
    return p


def bush(p):
    for x, y, r in ((0, 0, 0.75), (-0.5, 0.25, 0.55), (0.5, -0.2, 0.5), (0.1, 0.5, 0.45)):
        p.rock("leaf", r, (x, y, r * 0.8), scale=(1.1, 1.0, 0.85), jitter=0.2, sub=2)
    return p


def fern(p):
    p.tint("leaf", (1.15, 1.2, 0.9))
    for i in range(8):
        a = i * 0.785 + p.rng.uniform(-0.2, 0.2)
        length = p.rng.uniform(0.7, 1.0)
        p.block("leaf", (0.16, 0.03, length), (0, 0, 0.05), rot=(0, 1.0 + p.rng.uniform(-0.15, 0.15), a))
        # a wider leaflet halfway along
        d = length * 0.55
        tip = Euler((0, 1.0, a)).to_matrix() @ Vector((0, 0, d))
        p.block("leaf", (0.3, 0.03, 0.2), (tip.x, tip.y, tip.z + 0.05), rot=(0, 1.0, a))
    return p


def ruin_column(p):
    p.block("ruin", (1.2, 1.2, 0.3), (0, 0, -0.05))
    p.block("ruin", (0.95, 0.95, 0.15), (0, 0, 0.25))
    z = 0.4
    for i, h in enumerate((1.0, 0.9, 0.8)):
        p.cone("ruin", 0.36 - i * 0.015, 0.345 - i * 0.015, h, (p.rng.uniform(-0.02, 0.02), p.rng.uniform(-0.02, 0.02), z), segs=10)
        z += h
    # The broken top: a last drum cut at an angle.
    p.cone("ruin", 0.33, 0.33, 0.5, (0, 0, z), rot=(0.12, -0.08, 0), segs=10)
    # A fallen drum beside it.
    p.cone("ruin", 0.33, 0.33, 0.8, (1.0, -0.7, 0.33), rot=(1.5708, 0, 0.6), segs=10)
    p.retag("moss", 0.08, lambda f: True)
    return p


def ruin_arch(p):
    """Two piers and a round arch of voussoirs, 4.5 m tall, a stone missing from the crown."""
    for sx in (-1, 1):
        p.block("ruin", (0.8, 0.9, 0.3), (sx * 1.65, 0, -0.05))
        z = 0.25
        for i in range(5):
            h = 0.44
            p.block("ruin", (0.7, 0.8, h * 0.97), (sx * 1.65 + p.rng.uniform(-0.02, 0.02), p.rng.uniform(-0.02, 0.02), z))
            z += h
        p.block("ruin", (0.9, 0.95, 0.25), (sx * 1.65, 0, z))
    spring = 2.7
    r = 1.65
    n = 9
    for i in range(n):
        if i == 4:
            continue  # the keystone has gone
        a = math.pi * (i + 0.5) / n
        p.box("ruin", (0.55, 0.8, 0.45), (-math.cos(a) * r, 0, spring + math.sin(a) * r), rot=(0, -(a - math.pi / 2), 0))
    p.chunk("ruin", (0.6, 0.5, 0.4), (0.3, -0.6, 0), rot=(0, 0, 0.4), cuts=0)
    p.retag("moss", 0.08, lambda f: True)
    return p


def signal_post(p):
    """A railway semaphore: a 5 m iron post, the arm at the top, a lamp and a ladder."""
    p.cone("stone", 0.35, 0.3, 0.35, (0, 0, -0.05), segs=6)
    p.cone("iron", 0.09, 0.06, 5.0, (0, 0, 0.3), segs=6)
    p.box("iron", (0.1, 0.1, 0.7), (0, 0, 4.9))
    p.box("iron", (1.3, 0.06, 0.24), (0.6, 0.1, 4.75), rot=(0, 0.35, 0))   # the arm, dropped: the line is clear or forgotten
    p.box("field_lamp", (0.14, 0.14, 0.18), (0, -0.14, 4.6))
    p.box("iron", (0.2, 0.22, 0.26), (0, -0.14, 4.6 + 0.0), rot=(0, 0, 0))
    p.box("field_lamp", (0.22, 0.1, 0.16), (0, -0.29, 4.6))
    p.cone("iron", 0.16, 0.0, 0.14, (0, -0.14, 4.73), segs=4)
    for sx in (-1, 1):
        p.box("iron", (0.03, 0.03, 4.3), (sx * 0.16, 0.14, 2.3))
    for i in range(10):
        p.box("iron", (0.36, 0.03, 0.03), (0, 0.14, 0.4 + i * 0.42))
    return p


def rail_car(p):
    """A wrecked wooden rail car, listing, its roof split and planks gone."""
    L, W, H = 5.0, 2.4, 2.2
    p.frame = xform((0, 0, 0.1), (0.1, 0.0, 0.04))  # the whole wreck lists toward -Y
    p.box("iron", (L * 0.9, 0.3, 0.3), (0, -0.4, 0.45))
    p.box("iron", (L * 0.9, 0.3, 0.3), (0, 0.4, 0.45))
    for sx in (-1, 1):
        p.box("iron", (0.6, W * 0.9, 0.35), (sx * 1.7, 0, 0.3))
    floor_z = 0.65
    p.box("bark", (L, W, 0.14), (0, 0, floor_z))
    pw = 0.3
    n = int(L / pw)
    for sy in (-1, 1):
        for i in range(n):
            if p.rng.random() < 0.18:
                continue
            h = H * p.rng.uniform(0.6, 1.0) if p.rng.random() < 0.3 else H
            x = -L / 2 + pw * (i + 0.5)
            p.block("bark", (pw * 0.92, 0.05, h), (x, sy * W / 2, floor_z + 0.07), rot=(p.rng.uniform(-0.04, 0.04), 0, 0))
    for sx in (-1, 1):
        for i in range(int(W / pw)):
            if p.rng.random() < 0.15:
                continue
            y = -W / 2 + pw * (i + 0.5)
            p.block("bark", (0.05, pw * 0.92, H * p.rng.uniform(0.85, 1.0)), (sx * L / 2, y, floor_z + 0.07))
    for sy in (-1, 1):
        for z in (0.5, 1.5):
            p.box("iron", (L + 0.1, 0.03, 0.08), (0, sy * (W / 2 + 0.03), floor_z + z))
    # The roof: two halves, one sagged in.
    p.box("bark", (L * 0.55, W + 0.3, 0.09), (-L * 0.24, 0.05, floor_z + H + 0.1), rot=(0.1, 0.04, 0))
    p.box("bark", (L * 0.45, W + 0.3, 0.09), (L * 0.3, 0.3, floor_z + H - 0.45), rot=(0.55, -0.12, 0))
    p.frame = Matrix.Identity(4)
    p.retag("moss", 0.06, lambda f: f.normal.z > 0.5)
    for _ in range(3):
        p.block("bark", (0.3, 0.06, p.rng.uniform(0.8, 1.6)), (p.rng.uniform(-2.5, 2.5), p.rng.uniform(-2.2, -1.6), 0.0), rot=(p.rng.uniform(1.2, 1.5), 0, p.rng.uniform(0, 3)))
    return p


def lamp_post(p):
    """A dead iron street lamp, 3.5 m, its glass dark."""
    p.cone("iron", 0.26, 0.17, 0.45, (0, 0, -0.05), segs=8)
    p.cone("iron", 0.09, 0.055, 2.55, (0, 0, 0.4), segs=6)
    p.cone("iron", 0.12, 0.08, 0.12, (0, 0, 0.4), segs=6)
    p.box("iron", (0.05, 0.05, 0.42), (0, -0.2, 3.0), rot=(-1.1, 0, 0))
    p.block("shadow", (0.32, 0.32, 0.42), (0, 0, 2.9))
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        p.block("iron", (0.03, 0.03, 0.44), (sx * 0.17, sy * 0.17, 2.9))
    p.box("iron", (0.4, 0.4, 0.04), (0, 0, 2.9))
    p.cone("iron", 0.27, 0.03, 0.22, (0, 0, 3.32), segs=4)
    p.cone("iron", 0.02, 0.02, 0.15, (0, 0, 3.5), segs=4)
    return p


def cairn(p):
    z = -0.05
    for i, r in enumerate((0.55, 0.5, 0.42, 0.36, 0.3, 0.24, 0.18)):
        h = r * 0.55
        p.rock("stone", r, (p.rng.uniform(-0.05, 0.05), p.rng.uniform(-0.05, 0.05), z + h * 0.5), scale=(1.1, 1.0, 0.5), rot=(0, 0, p.rng.uniform(0, 3)), jitter=0.15, sub=2)
        z += h * 0.9
    p.retag("moss", 0.15, lambda f: f.normal.z > 0.6)
    return p


def bones(p):
    """A scatter of large bones: a skull, a ribcage and long bones, something a beast left."""
    p.rock("bone", 0.32, (0.9, -0.6, 0.26), scale=(1.3, 1.0, 0.85), jitter=0.16, rot=(0, 0.1, 0.6), sub=2)
    p.box("bone", (0.5, 0.26, 0.12), (1.15, -0.55, 0.07), rot=(0, 0, 0.6))
    p.cone("bone", 0.05, 0.02, 0.22, (1.25, -0.75, 0.3), rot=(0.4, 0, 0.6), segs=4)
    p.cone("bone", 0.05, 0.02, 0.22, (1.0, -0.95, 0.3), rot=(0.4, 0, 0.6), segs=4)
    for i in range(6):
        y = -0.4 + i * 0.3
        rr = 0.55 - abs(i - 2.5) * 0.06
        chain = [((-0.9, y, 0.05), 0.035), ((-0.9 - rr * 0.6, y, rr * 0.6), 0.03), ((-0.9 - rr * 1.1, y, rr * 1.1), 0.025), ((-0.9 - rr * 1.9, y, rr * 1.2), 0.02)]
        p.branches(chain, "bone")
    p.branches([((-1.0, -0.5, 0.06), 0.06), ((-1.0, 1.0, 0.06), 0.05)], "bone")
    for (x, y, a) in ((0.3, 0.7, 0.4), (-0.2, -1.1, 1.9), (0.9, 0.9, 2.8)):
        p.cone("bone", 0.05, 0.05, 0.9, (x, y, 0.05), rot=(1.5708, 0, a), segs=5)
        for t in (0.0, 0.9):
            e = Euler((1.5708, 0, a)).to_matrix() @ Vector((0, 0, t))
            p.rock("bone", 0.085, (x + e.x, y + e.y, 0.06), jitter=0.15, sub=1)
    return p


def fence_post(p):
    p.block("bark", (0.16, 0.14, 1.25), (0, 0, -0.05), rot=(0.1, -0.06, 0))
    p.block("bark", (0.07, 0.12, 0.7), (0.3, 0, 0.75), rot=(0, 1.2, 0))
    p.tuft("grass", (0.1, -0.15, -0.02), n=3)
    return p


# ======================================================================================
# Set pieces
# ======================================================================================

def set_den(p):
    """A mouth of rocks 5 m wide, 2.5 m tall, dark inside, bones at the lip."""
    p.rock("earth", 1.0, (0, 1.0, -0.6), scale=(3.0, 2.0, 0.8), jitter=0.1, sub=1)
    # The darkness: a hollow behind the mouth.
    p.block("shadow", (2.6, 2.6, 2.3), (0, 1.3, -0.1))
    # The ring of boulders around the opening (2.2 m wide, 2 m tall).
    ring = [(-2.3, 0.3, 0.9, (1.2, 1.2, 1.0)), (-1.65, 0.1, 1.0, (1.1, 1.1, 1.0)), (2.3, 0.3, 0.9, (1.2, 1.2, 1.0)), (1.65, 0.1, 1.0, (1.1, 1.1, 1.0)),
            (-1.5, 0.5, 0.8, (1.2, 1.4, 1.2)), (1.5, 0.5, 0.8, (1.2, 1.4, 1.2)), (-0.9, 0.5, 0.85, (1.3, 1.4, 0.9)), (0.9, 0.5, 0.85, (1.3, 1.4, 0.9)),
            (0.0, 0.6, 0.9, (1.9, 1.4, 0.7))]
    for i, (x, y, r, sz) in enumerate(ring):
        if i < 4:
            z = r * sz[2] * 0.75
        elif i < 6:
            z = 1.4
        elif i < 8:
            z = 1.9
        else:
            z = 2.25
        p.rock("stone", r, (x, y, z), scale=sz, rot=(0, 0, p.rng.uniform(0, 3)), jitter=0.2, sub=3 if i == 8 else 2)
    p.rock("stone", 0.7, (-2.6, 1.3, 0.5), scale=(1.2, 1.1, 0.9), sub=2)
    p.rock("stone", 0.7, (2.6, 1.3, 0.5), scale=(1.2, 1.1, 0.9), sub=2)
    p.rock("stone", 1.2, (0, 1.7, 2.2), scale=(1.6, 1.2, 0.7), jitter=0.15, sub=2)
    p.retag("moss", 0.2, lambda f: f.normal.z > 0.5)
    p.retag("earth", 0.1, lambda f: True)
    # Bones at the lip.
    p.rock("bone", 0.26, (-0.8, -0.9, 0.2), scale=(1.3, 1.0, 0.85), jitter=0.16, rot=(0, 0.1, -0.5), sub=2)
    p.box("bone", (0.4, 0.22, 0.1), (-0.6, -0.95, 0.06), rot=(0, 0, -0.5))
    for (x, y, a) in ((0.6, -1.0, 0.4), (-0.1, -1.4, 1.9), (1.3, -0.8, 2.6), (-1.6, -1.1, 0.2)):
        p.cone("bone", 0.045, 0.045, 0.8, (x, y, 0.05), rot=(1.5708, 0, a), segs=5)
        for t in (0.0, 0.8):
            e = Euler((1.5708, 0, a)).to_matrix() @ Vector((0, 0, t))
            p.rock("bone", 0.075, (x + e.x, y + e.y, 0.06), jitter=0.15, sub=1)
    for i in range(4):
        p.branches([((0.2 + i * 0.25, -1.6, 0.03), 0.03), ((0.2 + i * 0.25, -1.9, 0.3), 0.025), ((0.2 + i * 0.25, -2.3, 0.35), 0.02)], "bone")
    return p


def set_bridge(p):
    """The broken end of a stone bridge: 6 m of deck on an arch, parapets, ending in air at +X."""
    deck_z = 0.6
    # The abutment and arch under the deck, down into the water.
    p.block("ruin", (1.6, 3.2, 1.6), (-2.2, 0, -1.0))
    p.block("ruin", (1.2, 3.0, 1.4), (1.0, 0, -1.4))
    n = 9
    r = 1.7
    for i in range(n):
        a = math.pi * (i + 0.5) / n
        if i > 6:
            continue  # the arch fell with the deck
        p.box("ruin", (0.5, 3.0, 0.5), (-0.6 - math.cos(a) * r, 0, -1.4 + math.sin(a) * r), rot=(0, -(a - math.pi / 2), 0))
    # The deck, flagstones, the far ones broken off.
    for i in range(7):
        for j in range(4):
            x = -3 + 0.9 * (i + 0.5)
            if i == 6 and p.rng.random() < 0.6:
                continue
            if i == 5 and j in (0, 3) and p.rng.random() < 0.5:
                continue
            p.block("ruin", (0.86, 0.7, 0.14), (x, -1.2 + j * 0.8, deck_z - 0.14 + p.rng.uniform(-0.02, 0.02)), rot=(p.rng.uniform(-0.02, 0.02), p.rng.uniform(-0.02, 0.02), 0))
    p.block("ruin", (6.0, 3.0, 0.4), (0, 0, deck_z - 0.5))
    # Parapets, broken toward the end.
    for sy in (-1, 1):
        x = -3.0
        while x < 2.4:
            w = p.rng.uniform(0.6, 0.9)
            h = 0.9 if x < 0.5 else max(0.0, 0.9 - (x - 0.5) * 0.5 * p.rng.uniform(0.6, 1.4))
            if h > 0.12:
                p.block("ruin", (w * 0.95, 0.35, h), (x + w / 2, sy * 1.45, deck_z), rot=(0, 0, p.rng.uniform(-0.02, 0.02)))
            x += w
    # The jagged end: stones hanging over the gap, rubble below.
    p.chunk("ruin", (0.9, 0.8, 0.5), (3.0, -0.8, deck_z - 0.5), rot=(0.1, 0.3, 0.2), cuts=0)
    p.chunk("ruin", (0.7, 0.6, 0.4), (2.8, 0.9, deck_z - 0.45), rot=(-0.1, 0.25, -0.3), cuts=0)
    for _ in range(4):
        s = p.rng.uniform(0.3, 0.6)
        p.chunk("ruin", (s * 1.3, s, s * 0.8), (p.rng.uniform(2.0, 3.8), p.rng.uniform(-1.2, 1.2), -1.6), rot=(0, 0, p.rng.uniform(0, 3)), cuts=0)
    # The ramp up from the bank.
    p.block("earth", (1.6, 3.4, 0.5), (-3.3, 0, -0.1), rot=(0, -0.25, 0))
    p.retag("moss", 0.08, lambda f: True)
    return p


def set_junction(p):
    """A signal gantry spanning the line (which runs along X), 6 m between its legs at +Y and
    -Y, two signal heads hung from the beam, and a switch stand beside the line."""
    for sy in (-1, 1):
        p.block("stone", (0.8, 0.8, 0.4), (0.0, sy * 3.0, -0.05))
        for sx in (-1, 1):
            p.block("iron", (0.12, 0.12, 5.2), (sx * 0.25, sy * 3.0, 0.3))
        for z in (1.4, 2.8, 4.2):
            p.box("iron", (0.6, 0.06, 0.06), (0, sy * 3.0, z))
            p.block("iron", (0.06, 0.06, 0.7), (-0.25, sy * 3.0, z - 0.6), rot=(0, 0.75, 0))
    # The beam: a lattice of two chords and diagonals.
    for sz in (0, 1):
        p.box("iron", (0.14, 6.6, 0.14), (0, 0, 5.45 + sz * 0.5))
    for i in range(10):
        y = -3.0 + i * 0.66 + 0.33
        p.box("iron", (0.07, 0.07, 0.55), (0, y, 5.7), rot=(0.7 if i % 2 else -0.7, 0, 0))
    # Signal heads hung from the beam, facing down the line (-X).
    for y in (-1.6, 1.4):
        p.box("iron", (0.08, 0.08, 1.4), (0, y, 4.8))
        p.box("iron", (0.1, 0.5, 0.9), (-0.12, y, 4.4))
        p.box("field_lamp", (0.06, 0.2, 0.2), (-0.2, y, 4.6))
        p.box("shadow", (0.06, 0.2, 0.2), (-0.2, y, 4.2))
    p.box("iron", (0.06, 0.06, 1.3), (0, 0, 6.5), rot=(0.1, 0, 0))
    # The switch stand beside the line.
    p.block("iron", (0.4, 0.4, 0.15), (-1.2, -2.3, -0.02))
    p.cone("iron", 0.06, 0.05, 1.3, (-1.2, -2.3, 0.1), segs=6)
    p.box("iron", (0.05, 0.9, 0.05), (-1.2, -2.0, 0.55), rot=(0.6, 0, 0))
    p.box("iron", (0.05, 0.4, 0.4), (-1.2, -2.3, 1.55))
    p.box("field_lamp", (0.08, 0.14, 0.14), (-1.2, -2.3, 1.55))
    return p


def set_crossing(p):
    """A barge hull beached on a mud bank, 7 m long along X, listing toward -Y, planked and ribbed."""
    p.tint("earth", (0.8, 0.85, 0.9))
    p.rock("earth", 1.0, (0.5, 1.6, -0.5), scale=(4.2, 2.0, 0.65), jitter=0.1, sub=2)
    p.frame = xform((0, 0.3, 0.1), (-0.22, 0.04, 0.08))  # the hull lists toward -Y, stern down
    outline = [(-3.5, -0.6), (-2.6, -1.25), (2.4, -1.3), (3.4, -0.7), (3.5, 0.0), (3.4, 0.7), (2.4, 1.3), (-2.6, 1.25), (-3.5, 0.6)]
    p.shell("bark", outline, 1.15, flare=1.1)
    p.shell("shadow", outline, 1.0, flare=1.1, inset=0.96, z=0.12, inward=True)
    # Ribs across the inside, the gunwale, planks and iron straps outside.
    for x in (-2.4, -1.4, -0.4, 0.6, 1.6, 2.5):
        for sy in (-1, 1):
            p.box("bark", (0.1, 0.08, 1.0), (x, sy * 1.22, 0.6))
        p.box("bark", (0.12, 2.3, 0.1), (x, 0, 0.14))
    for sy in (-1, 1):
        for i, (z, L) in enumerate(((0.4, 5.6), (0.8, 5.9))):
            p.box("bark", (L, 0.08, 0.04), (0, sy * (1.3 + 0.06 * (1 + i * 0.4)), z))
        p.box("bark", (6.0, 0.18, 0.08), (0, sy * 1.38, 1.17))
        for x in (-2.0, 0.2, 2.2):
            p.box("iron", (0.06, 0.1, 1.1), (x, sy * 1.33, 0.6))
    p.cone("bark", 0.12, 0.09, 1.6, (-0.5, 0, 0.2), rot=(0, 0.3, 0), segs=6)
    p.frame = Matrix.Identity(4)
    # A mooring post on the bank.
    p.block("bark", (0.22, 0.22, 1.3), (3.4, 2.2, 0.0), rot=(0.08, 0.1, 0.3))
    for x, y in ((-3.0, 2.3), (-1.6, 2.6), (2.0, 2.7)):
        p.reeds((x, y, 0.05), n=7, h=1.5)
    return p


def set_post(p):
    """A 3 m iron lamp column with an empty socket_flame at its crown, where the game puts a blue flame."""
    p.cone("stone", 0.42, 0.36, 0.3, (0, 0, -0.05), segs=8)
    p.cone("iron", 0.2, 0.14, 0.3, (0, 0, 0.25), segs=8)
    p.cone("iron", 0.11, 0.07, 2.3, (0, 0, 0.55), segs=8)
    p.cone("iron", 0.14, 0.1, 0.12, (0, 0, 1.6), segs=8)
    p.cone("iron", 0.09, 0.16, 0.2, (0, 0, 2.8), segs=8)
    for i in range(4):
        a = i * 1.5708 + 0.785
        p.cone("iron", 0.03, 0.02, 0.45, (math.cos(a) * 0.14, math.sin(a) * 0.14, 2.95), rot=(0, 0.65, a), segs=4)
    # The crown: a flared iron cup, dark inside, where the flame sits.
    p.cone("iron", 0.16, 0.27, 0.16, (0, 0, 2.95), segs=8)
    p.cone("shadow", 0.22, 0.22, 0.01, (0, 0, 3.11), segs=8)
    p.empty("socket_flame", (0, 0, 3.12))
    return p


def set_car(p):
    """The line car: a 6 m passenger car, long along X, its open door on the -Y side with steps,
    lamps at both ends."""
    L, W = 6.0, 2.6
    fz = 0.7  # floor top
    # The underframe and trucks (no wheels).
    p.box("iron", (L * 0.95, W * 0.9, 0.22), (0, 0, fz - 0.11))
    for sx in (-1, 1):
        p.box("iron", (1.4, W * 0.75, 0.42), (sx * 2.0, 0, 0.3))
    p.box("bark", (L, W, 0.06), (0, 0, fz + 0.03))
    # Walls: a wainscot band, pillars between windows, dark panes, a frieze above.
    win_z0, win_z1 = fz + 0.95, fz + 1.85
    roof_z = fz + 2.25
    n = 6
    pitch = L / n
    door_i = 2  # the bay on the -Y side that is the door
    for sy in (-1, 1):
        for i in range(n):
            x = -L / 2 + pitch * (i + 0.5)
            is_door = sy < 0 and i == door_i
            if not is_door:
                p.box("bark", (pitch, 0.08, win_z0 - fz), (x, sy * W / 2, (fz + win_z0) / 2))
                p.box("shadow", (pitch * 0.72, 0.04, win_z1 - win_z0), (x, sy * (W / 2 - 0.04), (win_z0 + win_z1) / 2))
            else:
                # the open doorway: dark inside, the door swung out
                p.box("shadow", (pitch * 0.7, 0.04, roof_z - fz - 0.1), (x, sy * (W / 2 - 0.1), (fz + roof_z) / 2))
                p.block("bark", (0.08, 0.95, roof_z - fz - 0.3), (x - pitch * 0.38, -W / 2 - 0.45, fz + 0.1), rot=(0, 0, 0.0))
                p.block("iron", (0.9, 0.3, 0.12), (x, -W / 2 - 0.3, fz - 0.4))
                p.block("iron", (0.9, 0.3, 0.12), (x, -W / 2 - 0.6, fz - 0.75))
            p.box("bark", (0.12, 0.12, roof_z - fz), (x - pitch / 2, sy * W / 2, (fz + roof_z) / 2))
        p.box("bark", (0.12, 0.12, roof_z - fz), (L / 2, sy * W / 2, (fz + roof_z) / 2))
        p.box("bark", (L, 0.1, roof_z - win_z1), (0, sy * W / 2, (win_z1 + roof_z) / 2))
        p.box("iron", (L + 0.1, 0.03, 0.06), (0, sy * (W / 2 + 0.05), fz + 0.5))
    # Ends: panelled, a lamp on each.
    for sx in (-1, 1):
        p.box("bark", (0.1, W, roof_z - fz), (sx * L / 2, 0, (fz + roof_z) / 2))
        p.box("shadow", (0.04, 0.7, 0.8), (sx * (L / 2 + 0.04), 0, win_z0 + 0.45))
        p.box("iron", (0.25, 0.25, 0.32), (sx * (L / 2 + 0.2), 0, roof_z - 0.35))
        p.box("field_lamp", (0.16, 0.16, 0.2), (sx * (L / 2 + 0.22), 0, roof_z - 0.35))
        p.cone("iron", 0.2, 0.02, 0.14, (sx * (L / 2 + 0.2), 0, roof_z - 0.19), segs=4)
        p.box("iron", (0.5, 1.2, 0.08), (sx * (L / 2 + 0.3), 0, fz - 0.05))  # the end platform
        p.box("iron", (0.04, 1.2, 0.04), (sx * (L / 2 + 0.55), 0, fz + 0.5))
        for sy in (-1, 1):
            p.box("iron", (0.04, 0.04, 0.55), (sx * (L / 2 + 0.55), sy * 0.6, fz + 0.25))
    # The roof: a slab, a shallow clerestory, a ridge.
    p.box("bark", (L + 0.4, W + 0.3, 0.1), (0, 0, roof_z + 0.05))
    p.box("bark", (L * 0.75, W * 0.45, 0.32), (0, 0, roof_z + 0.26))
    p.box("bark", (L * 0.8, W * 0.5, 0.06), (0, 0, roof_z + 0.45))
    p.box("iron", (0.3, 0.3, 0.4), (-L * 0.3, 0, roof_z + 0.6))  # a stove chimney
    return p


# ======================================================================================
# The catalogue
# ======================================================================================

GROUND = {"ground_grass_a": ground_grass_a, "ground_grass_b": ground_grass_b, "ground_grass_rocky": ground_grass_rocky, "ground_earth": ground_earth,
          "ground_ruin_floor": ground_ruin_floor, "ground_ballast": ground_ballast, "ground_reeds": ground_reeds, "ground_water": ground_water, "ground_mud": ground_mud}
EDGES = {"edge_treeline": edge_treeline, "edge_treeline_pine": edge_treeline_pine, "edge_rocks": edge_rocks, "edge_ruin_wall": edge_ruin_wall,
         "edge_reeds": edge_reeds, "edge_fence": edge_fence, "edge_cliff": edge_cliff}
PROPS = {"tree_oak": tree_oak, "tree_pine": tree_pine, "tree_dead": tree_dead, "tree_willow": tree_willow, "boulder_a": boulder_a, "boulder_b": boulder_b,
         "stump": stump, "bush": bush, "fern": fern, "ruin_column": ruin_column, "ruin_arch": ruin_arch, "signal_post": signal_post, "rail_car": rail_car,
         "lamp_post": lamp_post, "cairn": cairn, "bones": bones, "fence_post": fence_post}
SETS = {"set_den": set_den, "set_bridge": set_bridge, "set_junction": set_junction, "set_crossing": set_crossing, "set_post": set_post, "set_car": set_car}
PIECES = {}
PIECES.update(GROUND)
PIECES.update(EDGES)
PIECES.update(PROPS)
PIECES.update(SETS)
BUDGET = {name: (8000 if name in SETS else 4000 if name in EDGES else 2000) for name in PIECES}


def build(name):
    reset()
    objs = PIECES[name](Piece(name)).finish()
    tris = TRIS[name]
    if tris > BUDGET[name]:
        print("WARNING: %s has %d triangles, over its budget of %d" % (name, tris, BUDGET[name]))
    return objs


# --- The contact sheet ----------------------------------------------------------------

def render_card(name, objects, path, size_px=(320, 256)):
    """One cell of the sheet: three-quarter view under the moon, a faint warm lamp from the front."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = size_px
    scene.render.film_transparent = False
    world = scene.world or bpy.data.worlds.new("night")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.014, 0.025, 1)
    lo = Vector((9e9,) * 3)
    hi = Vector((-9e9,) * 3)
    for o in objects:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    centre = (lo + hi) / 2
    size = max((hi - lo).length, 1.0)
    # A dark ground under everything, and the name on it.
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(centre.x, centre.y, min(lo.z, -0.3) - 0.01))
    ground = bpy.context.active_object
    ground.data.materials.append(material("sheet_ground", (0.03, 0.028, 0.025, 1), 0.95))
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 42
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = centre + Vector((size * 0.8, -size * 1.15, size * 0.6))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    label = bpy.data.curves.new("label", type="FONT")
    label.body = name
    label.size = size * 0.11
    label.align_x = "CENTER"
    lab = bpy.data.objects.new("label", label)
    lab.data.materials.append(material("sheet_text", (0.9, 0.85, 0.7, 1), 0.5, emission=(0.95, 0.87, 0.7, 1), strength=1.0))
    bpy.context.collection.objects.link(lab)
    lab.parent = cam  # pinned to the bottom of the frame
    lab.location = (0, -0.36, -1.2)
    label.size = 0.07

    def light(kind, at, color, energy, size_=1.0):
        ld = bpy.data.lights.new(kind, kind)
        ld.color = color
        ld.energy = energy
        if kind == "AREA":
            ld.size = size_
        lo_ = bpy.data.objects.new(kind, ld)
        lo_.location = at
        lo_.rotation_euler = (centre - Vector(at)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(lo_)

    light("SUN", centre + Vector((-size, -size * 0.5, size * 1.6)), (0.55, 0.62, 0.95), 2.2)
    light("AREA", centre + Vector((size * 1.5, -size * 1.2, size * 0.3)), (1.0, 0.6, 0.3), 18 * size * size, size)
    for m in bpy.data.materials:
        if m.name.startswith("field") and m.use_nodes:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Emission Color"].default_value = (0.42, 0.6, 1.0, 1)
            bsdf.inputs["Emission Strength"].default_value = 3.0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def compose_sheet(cells, path, cell=(320, 256), cols=8):
    """Stitch the cell renders into one PNG, row by row in catalogue order."""
    import numpy as np
    rows = (len(cells) + cols - 1) // cols
    W, H = cell[0] * cols, cell[1] * rows
    sheet = np.zeros((H, W, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    for i, cpath in enumerate(cells):
        img = bpy.data.images.load(cpath)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
        r, c = divmod(i, cols)
        y0 = H - (r + 1) * cell[1]  # Blender images are bottom-up
        sheet[y0:y0 + cell[1], c * cell[0]:(c + 1) * cell[0]] = px
        bpy.data.images.remove(img)
    out = bpy.data.images.new("sheet", W, H, alpha=True)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    print("wrote", path)


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
        export(os.path.join(OUT, name + ".glb"), objs)
        if sheet:
            cell = os.path.join(os.path.dirname(sheet), "wild_cells", name + ".png")
            render_card(name, objs, cell)
            cells.append(cell)
    if sheet:
        reset()
        compose_sheet(cells, sheet)
    print("triangles:", ", ".join("%s %d" % (n, TRIS[n]) for n in wanted))
