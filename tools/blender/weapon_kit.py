"""WILDLINE weapon kit: the weapons of the three cities and the Academy's disciplines, built in
Blender and exported where the game looks for them. Modelled on tools/blender/wild_kit.py.
Run headless with Blender's Python module:

    python tools/blender/weapon_kit.py                      # every weapon
    python tools/blender/weapon_kit.py cutlass pistol       # some weapons
    python tools/blender/weapon_kit.py --sheet /tmp/weapons_sheet.png   # also a contact sheet
    python tools/blender/weapon_kit.py --hands /tmp/weapons_in_hand.png # also the in-hand check

Conventions (the game relies on them; they are KayKit's, measured from sword_1handed.gltf and
crossbow_1handed.gltf, so a model drops in where a KayKit one hung with no offset):
  - One .glb per weapon at game/assets/weapons/<name>.glb, origin at the grip, scale in the
    game's units (people are about 2.4 tall; KayKit's one-handed sword is 1.41 from origin to
    tip and 1.78 overall).
  - The game hangs the model under a BoneAttachment3D on handslot.r or handslot.l with an
    identity transform. In the slot's frame (glTF, Y up): +Y is the fist's axis, out of the
    thumb side (a blade runs along +Y; a grip runs along -Y below the origin, about 0.37 long);
    +X is along the fingers, the knuckle side (a true edge faces +X, a hammer face sits on +X,
    a curved blade bows its tip toward -X); +Z is out of the back of the hand (the flat of a
    blade faces +-Z; KayKit's crossbow points its barrel along +Z with its top at +Y, and so do
    the guns and bows here: a bow's limbs run along +-Y with the string at -Z).
  - Blender is Z up and the glTF export turns (x, y, z) into (x, z, -y), so in this file a
    blade runs along +Z, its edge faces +X, a barrel runs along -Y with its top at +Z.
  - Flat-shaded low poly, no textures, under 1.5k triangles each. Materials by name from a
    small palette (steel, iron, brass, wood, dark_wood, leather, bone, glass, cloth); a
    material named field_glow marks what should glow in the game (muzzles, the astrolabe's
    ring, the lantern's flame, the glass blade's edge).
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "weapons")
PEOPLE = os.path.join(ROOT, "game", "assets", "people")
KAYKIT = os.path.join(ROOT, "game", "assets", "kaykit", "weapons")
BUDGET = 1500

# Linear colour, roughness, metallic. Muted earths and worn metals; the field's colour carries the eye.
PALETTE = {
    "steel": ((0.40, 0.42, 0.45), 0.38, 0.9),
    "iron": ((0.065, 0.065, 0.08), 0.62, 0.7),
    "brass": ((0.40, 0.23, 0.06), 0.45, 0.85),
    "wood": ((0.21, 0.125, 0.06), 0.85, 0.0),
    "dark_wood": ((0.075, 0.048, 0.03), 0.8, 0.0),
    "leather": ((0.12, 0.055, 0.035), 0.75, 0.0),
    "bone": ((0.56, 0.49, 0.37), 0.6, 0.0),
    "glass": ((0.015, 0.035, 0.045), 0.08, 0.0),
    "cloth": ((0.14, 0.12, 0.17), 0.9, 0.0),
}
TRIS = {}  # weapon name -> triangle count, for the report
HPI = math.pi / 2


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, rough=0.8, metallic=0.0, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = strength
    return m


def palette_material(name, rng):
    """A palette material, its colour nudged a little for this weapon so no two match exactly."""
    if name.startswith("field"):
        return material(name, (0.9, 0.85, 0.7, 1), 0.4, 0.0, emission=(1.0, 0.85, 0.6, 1), strength=2.0)
    base, rough, metallic = PALETTE[name]
    v = rng.uniform(0.92, 1.08)
    col = tuple(min(1.0, c * v * rng.uniform(0.96, 1.04)) for c in base) + (1,)
    return material(name, col, rough, metallic)


def xform(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1))


def along(a, b):
    """The Euler that turns +Z toward b - a (for a cylinder from a to b)."""
    return Vector(b).__sub__(Vector(a)).to_track_quat("Z", "Y").to_euler()


class Piece:
    """One exported mesh, grown from flat-shaded primitives, each face tagged with a palette material."""

    def __init__(self, name):
        self.name = name
        self.rng = random.Random(name)
        self.bm = bmesh.new()
        self.mats = []

    def mat_index(self, name):
        m = bpy.data.materials.get(name)
        if m is None:
            m = palette_material(name, self.rng)
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, bm, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        """Take a temporary bmesh into the piece, placed, flat and tagged with mat (a palette
        name, or a function of the placed face returning one)."""
        bmesh.ops.transform(bm, matrix=xform(loc, rot, scale), verts=bm.verts[:])
        idx = None if callable(mat) else self.mat_index(mat)
        for f in bm.faces:
            f.smooth = False
            f.material_index = self.mat_index(mat(f)) if callable(mat) else idx
        mesh = bpy.data.meshes.new("tmp")
        bm.to_mesh(mesh)
        bm.free()
        self.bm.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)

    def retag(self, mat, chance, where=lambda f: True):
        idx = self.mat_index(mat)
        for f in self.bm.faces:
            if where(f) and self.rng.random() < chance:
                f.material_index = idx

    # --- primitives ------------------------------------------------------------------------

    def box(self, mat, size, loc, rot=(0, 0, 0)):
        """A block centred at loc."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        self.add(bm, mat, loc, rot, size)

    def cone(self, mat, r1, r2, h, loc, rot=(0, 0, 0), segs=8, scale=(1, 1, 1)):
        """A cylinder or cone standing on loc along its local +Z, rotated about its base."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segs, radius1=r1, radius2=r2, depth=h)
        bmesh.ops.transform(bm, matrix=Matrix.Translation((0, 0, h / 2)), verts=bm.verts[:])
        self.add(bm, mat, loc, rot, scale)

    def rod(self, mat, r, z0, z1, x=0.0, y=0.0, r2=None, segs=6):
        """A cylinder along Z from z0 to z1 at (x, y): hafts, grips, shanks."""
        self.cone(mat, r, r if r2 is None else r2, z1 - z0, (x, y, z0), segs=segs)

    def bar(self, mat, a, b, r, r2=None, segs=4):
        """A cylinder from point a to point b: limbs, tines, ribs, lines."""
        self.cone(mat, r, r if r2 is None else r2, (Vector(b) - Vector(a)).length, a, rot=along(a, b), segs=segs)

    def sphere(self, mat, r, loc, scale=(1, 1, 1), sub=1, jitter=0.0):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        if jitter:
            for v in bm.verts:
                v.co += v.co.normalized() * self.rng.uniform(-jitter, jitter) * r
        self.add(bm, mat, loc, scale=scale)

    def prism(self, mat, pts, thick, loc=(0, 0, 0), rot=(0, 0, 0), y=0.0):
        """A flat plate: a polygon in the XZ plane ((x, z) points, counter-clockwise seen from
        -Y), extruded `thick` along Y about y. Hooks, fan leaves, sickle blades, barbs."""
        bm = bmesh.new()
        verts = [bm.verts.new((x, y - thick / 2, z)) for x, z in pts]
        face = bm.faces.new(verts)
        ext = bmesh.ops.extrude_face_region(bm, geom=[face])
        top = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, thick, 0), verts=top)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        self.add(bm, mat, loc, rot)

    def loft(self, mat, rings, closed=False, cap_start=True, cap_end=True, loc=(0, 0, 0), rot=(0, 0, 0)):
        """Skin a list of rings (each a list of points, all the same length) into a tube. A ring
        may be a single point repeated: that end becomes a tip. closed joins the last ring
        back to the first (a torus)."""
        bm = bmesh.new()
        vrings = []
        for ring in rings:
            if all(Vector(p) == Vector(ring[0]) for p in ring):
                v = bm.verts.new(ring[0])
                vrings.append([v] * len(ring))
            else:
                vrings.append([bm.verts.new(p) for p in ring])
        n = len(rings[0])
        pairs = list(zip(vrings, vrings[1:]))
        if closed:
            pairs.append((vrings[-1], vrings[0]))
        for a, b in pairs:
            for i in range(n):
                j = (i + 1) % n
                quad = []
                for v in (a[i], a[j], b[j], b[i]):
                    if v not in quad:
                        quad.append(v)
                if len(quad) >= 3:
                    bm.faces.new(quad)
        if not closed:
            if cap_start and len(set(vrings[0])) > 2:
                bm.faces.new(list(reversed(vrings[0])))
            if cap_end and len(set(vrings[-1])) > 2:
                bm.faces.new(vrings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        self.add(bm, mat, loc, rot)

    def torus(self, mat, R, r, loc, rot=(0, 0, 0), segs=12, rings=4, sweep=2 * math.pi, start=0.0):
        """A ring in the XY plane centred at loc; sweep < 2 pi for an arc (open ends) from angle start."""
        full = sweep >= 2 * math.pi - 1e-6
        rings_ = []
        count = segs if full else segs + 1
        for i in range(count):
            a = start + sweep * i / segs
            c = Vector((math.cos(a) * R, math.sin(a) * R, 0))
            radial = Vector((math.cos(a), math.sin(a), 0))
            rings_.append([c + radial * (r * math.cos(b)) + Vector((0, 0, r * math.sin(b))) for b in (2 * math.pi * k / rings for k in range(rings))])
        self.loft(mat, rings_, closed=full, loc=loc, rot=rot)

    def blade(self, mat, z0, length, width, thick, curve=0.0, tip=0.15, kind="wedge", taper=0.75, stations=5, edge_mat=None, flare=0.0):
        """A blade along +Z from z0: `kind` wedge (one edge, on +X, a thick spine on -X), diamond
        (two edges) or glass (a diamond with a bevelled edge strip tagged edge_mat). `curve`
        bows the tip toward -X (the spine side, as a saber does); `taper` is the width left
        at the start of the tip; `flare` widens the blade mid-way (a leaf blade)."""
        rings = []
        body = length - tip
        e = width * 0.22
        for s in range(stations + 1):
            f = s / stations
            z = z0 + body * f
            cx = -curve * f * f
            w = width * (1 - (1 - taper) * f) * (1 + flare * math.sin(math.pi * f))
            t = thick * (1 - 0.35 * f)
            if kind == "wedge":
                prof = [(-w * 0.45, t), (-w * 0.45, -t), (w * 0.55, 0)]
            elif kind == "diamond":
                prof = [(-w, 0), (0, t), (w, 0), (0, -t)]
            else:
                prof = [(-w, 0), (-w * 0.3, t), (w - e, t * 0.35), (w, 0), (w - e, -t * 0.35), (-w * 0.3, -t)]
            rings.append([Vector((cx + x, y, z)) for x, y in prof])
        tip_x = -curve * (1 + tip / max(body, 1e-6)) ** 2
        if kind == "wedge":
            tip_x += width * 0.3  # a saber's point sweeps toward the edge
        rings.append([Vector((tip_x, 0, z0 + length))] * len(rings[0]))
        if kind == "glass" and edge_mat:
            def tag(face, _w=width, _z0=z0, _body=body, _curve=curve, _e=e):
                c = face.calc_center_median()
                f = max(0.0, min(1.0, (c.z - _z0) / _body))
                w = _w * (1 - (1 - taper) * f)
                return edge_mat if c.x + _curve * f * f > w - _e * 0.95 else mat
            self.loft(tag, rings)
        else:
            self.loft(mat, rings)

    def finish(self):
        """The piece as one object, ready to export or render."""
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
        return [obj]


def export(path, objects):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects if o.type == "MESH")
    print("wrote", os.path.relpath(path, ROOT), tris, "tris")


# ======================================================================================
# Shared parts
# ======================================================================================

def grip(p, z0, z1, r=0.042, mat="leather", wraps=3, segs=8):
    """A wrapped grip along Z with a few raised turns of binding."""
    p.rod(mat, r, z0, z1, segs=segs)
    for i in range(wraps):
        z = z0 + (z1 - z0) * (i + 0.5) / wraps
        p.rod(mat, r * 1.12, z - 0.012, z + 0.012, segs=segs)


def pommel(p, z, r, mat="brass"):
    p.sphere(mat, r, (0, 0, z), sub=1)


def haft(p, z0, z1, r=0.03, mat="wood", butt="iron"):
    """A pole along Z with an iron shoe at the butt."""
    p.rod(mat, r, z0 + 0.06, z1, segs=7)
    p.rod(butt, r * 1.1, z0, z0 + 0.06, r2=r * 0.95, segs=7)


def collar(p, z, r, h=0.05, mat="brass", segs=8):
    p.rod(mat, r, z, z + h, segs=segs)


def coil(p, R, r, loc, loops=3, pitch=0.03, rot=(0, 0, 0), mat="leather"):
    """A coiled line: a few rings stacked along their axis, each a little off the last."""
    for i in range(loops):
        p.torus(mat, R * p.rng.uniform(0.94, 1.06), r, (loc[0] + p.rng.uniform(-0.01, 0.01), loc[1] + p.rng.uniform(-0.01, 0.01), loc[2] + i * pitch),
                rot=(rot[0] + p.rng.uniform(-0.08, 0.08), rot[1] + p.rng.uniform(-0.08, 0.08), rot[2]), segs=10, rings=4)


def gun_grip(p, drop=0.3, rake=0.35, mat="dark_wood"):
    """A pistol grip hanging from the origin, raked back (+Y), with a brass butt cap."""
    p.box(mat, (0.085, 0.11, drop), (0, math.sin(rake) * drop * 0.5, -drop * 0.5 * math.cos(rake)), rot=(rake, 0, 0))
    p.sphere("brass", 0.05, (0, math.sin(rake) * drop, -drop * math.cos(rake)), scale=(1, 1.1, 0.6), sub=1)


def lock(p, y=0.08, z=0.1, side=1):
    """A flintlock on the right side (+X): the cock leaning back, the frizzen and pan ahead of it."""
    p.box("steel", (0.03, 0.16, 0.07), (side * 0.055, y, z))
    p.box("steel", (0.025, 0.035, 0.09), (side * 0.06, y + 0.04, z + 0.06), rot=(0.5, 0, 0))
    p.box("iron", (0.03, 0.03, 0.02), (side * 0.06, y + 0.07, z + 0.09), rot=(0.5, 0, 0))
    p.box("steel", (0.03, 0.03, 0.05), (side * 0.06, y - 0.05, z + 0.05), rot=(-0.3, 0, 0))


def trigger(p, y=0.02, z=0.0):
    p.box("steel", (0.012, 0.025, 0.045), (0, y, z - 0.035), rot=(0.4, 0, 0))
    p.box("brass", (0.012, 0.11, 0.008), (0, y, z - 0.065))
    p.box("brass", (0.012, 0.008, 0.06), (0, y - 0.05, z - 0.035))
    p.box("brass", (0.012, 0.008, 0.06), (0, y + 0.05, z - 0.035))


def barrel(p, y0, y1, r, z, r2=None, mat="steel", muzzle=True, segs=8):
    """A barrel from y0 back to y1 forward (-Y) at height z, a glowing ring at the muzzle."""
    p.cone(mat, r, r if r2 is None else r2, y0 - y1, (0, y0, z), rot=(HPI, 0, 0), segs=segs)
    if muzzle:
        rr = (r if r2 is None else r2)
        p.cone("field_glow", rr * 1.15, rr * 1.15, 0.025, (0, y1 + 0.02, z), rot=(HPI, 0, 0), segs=segs)
        p.cone("iron", rr * 1.25, rr * 1.25, 0.012, (0, y1 + 0.045, z), rot=(HPI, 0, 0), segs=segs)


def bow(p, limbs, string_y, r=0.022, mat="wood", grip_len=0.2, nock_z=None):
    """A bow along Z: limbs is a list of (y, z) stations for the upper limb from the grip out;
    the lower limb mirrors it. The string runs tip to tip at string_y (behind, +Y)."""
    grip(p, -grip_len / 2, grip_len / 2, r=r * 1.5, wraps=4)
    for sz in (-1, 1):
        prev = (0, 0, sz * grip_len / 2)
        for i, (y, z) in enumerate(limbs):
            pt = (0, y, sz * z)
            p.bar(mat, prev, pt, r * (1 - 0.5 * i / len(limbs)), r * (1 - 0.5 * (i + 1) / len(limbs)), segs=4)
            prev = pt
        p.sphere("bone", r * 0.9, prev, sub=0)
    tip_z = limbs[-1][1] if nock_z is None else nock_z
    p.bar("cloth", (0, string_y, -tip_z), (0, string_y, tip_z), 0.006, segs=3)
    p.cone("cloth", 0.012, 0.012, 0.03, (0, string_y, -0.015), rot=(0, 0, 0), segs=4)  # the nocking point


# ======================================================================================
# Blades and axes
# ======================================================================================

def cutlass(p):
    """A marshal's saber: a curved single-edged blade, a brass knuckle bow and a leather grip."""
    grip(p, -0.32, 0.06, r=0.04)
    pommel(p, -0.34, 0.05)
    p.box("brass", (0.2, 0.05, 0.035), (0.0, 0, 0.07))
    p.bar("brass", (0.1, 0, 0.07), (0.1, 0, -0.1), 0.012)
    p.bar("brass", (0.1, 0, -0.1), (0.035, 0, -0.33), 0.012)
    p.box("brass", (0.06, 0.07, 0.02), (0.05, 0, 0.07))
    p.blade("steel", 0.085, 1.12, 0.078, 0.012, curve=0.12, tip=0.22, kind="wedge", taper=0.9)
    return p


def rapier(p):
    """A Lunden rapier: a cup hilt, long quillons, a narrow diamond blade."""
    grip(p, -0.3, 0.04, r=0.03, mat="cloth", wraps=6, segs=6)
    pommel(p, -0.33, 0.045, "steel")
    p.cone("steel", 0.11, 0.035, 0.1, (0, 0, -0.045), segs=12)
    p.box("steel", (0.38, 0.018, 0.018), (0, 0, 0.05))
    p.bar("steel", (0.16, 0, 0.05), (0.1, 0, -0.14), 0.009)
    p.bar("steel", (0.1, 0, -0.14), (0.035, 0, -0.3), 0.009)
    p.blade("steel", 0.06, 1.34, 0.03, 0.012, tip=0.12, kind="diamond", taper=0.55)
    return p


def gladius(p):
    """A short broad legion blade: a ridged wooden grip, a round bone pommel, a leaf blade."""
    grip(p, -0.27, 0.03, r=0.04, mat="wood", wraps=4, segs=8)
    p.sphere("bone", 0.055, (0, 0, -0.3), sub=1)
    p.box("dark_wood", (0.15, 0.075, 0.045), (0, 0, 0.04))
    p.blade("steel", 0.062, 0.72, 0.07, 0.013, tip=0.2, kind="diamond", taper=0.95, flare=0.12)
    return p


def glass_blade(p):
    """A straight blade of dark glass in brass fittings; the edge carries the field's light."""
    grip(p, -0.34, 0.05, r=0.04, wraps=2)
    collar(p, -0.36, 0.045, 0.03)
    collar(p, -0.02, 0.045, 0.03)
    pommel(p, -0.38, 0.045)
    p.box("brass", (0.19, 0.05, 0.035), (0, 0, 0.065))
    p.blade("glass", 0.08, 1.15, 0.062, 0.015, tip=0.16, kind="glass", taper=0.85, edge_mat="field_glow")
    return p


def katana(p):
    """A long two-handed curve: a wrapped oval grip, an iron tsuba, a brass habaki."""
    p.cone("leather", 0.035, 0.035, 0.56, (0, 0, -0.52), segs=8, scale=(1.35, 1, 1))
    for i in range(7):
        z = -0.48 + i * 0.075
        p.box("cloth", (0.1, 0.06, 0.02), (0, 0, z), rot=(0, 0, 0.3 if i % 2 else -0.3))
    p.cone("iron", 0.04, 0.04, 0.025, (0, 0, -0.545), segs=8, scale=(1.35, 1, 1))
    p.cone("iron", 0.085, 0.085, 0.012, (0, 0, 0.045), segs=12, scale=(1, 0.95, 1))
    p.cone("brass", 0.03, 0.03, 0.05, (0, 0, 0.057), segs=6, scale=(1.5, 1, 1))
    p.blade("steel", 0.1, 1.42, 0.06, 0.012, curve=0.13, tip=0.18, kind="wedge", taper=0.9)
    return p


def war_fan(p):
    """An iron war fan, half open: steel ribs from a brass pivot, iron leaves, a brass rim."""
    p.rod("iron", 0.024, -0.22, 0.1, segs=6)
    p.cone("brass", 0.03, 0.03, 0.035, (0, 0.017, 0.1), rot=(HPI, 0, 0), segs=8)
    n = 7
    for i in range(n):
        a = HPI * i / (n - 1)
        tip = (math.sin(a) * 0.56, 0, 0.1 + math.cos(a) * 0.56)
        p.bar("steel", (0, 0, 0.1), tip, 0.011, 0.006, segs=4)
    outer = [(math.sin(HPI * k / 12) * 0.56, 0.1 + math.cos(HPI * k / 12) * 0.56) for k in range(13)]
    inner = [(math.sin(HPI * k / 12) * 0.26, 0.1 + math.cos(HPI * k / 12) * 0.26) for k in range(12, -1, -1)]
    p.prism("iron", outer + inner, 0.01)
    rim_out = [(math.sin(HPI * k / 12) * 0.575, 0.1 + math.cos(HPI * k / 12) * 0.575) for k in range(13)]
    rim_in = [(math.sin(HPI * k / 12) * 0.545, 0.1 + math.cos(HPI * k / 12) * 0.545) for k in range(12, -1, -1)]
    p.prism("brass", rim_out + rim_in, 0.014)
    p.torus("brass", 0.03, 0.006, (0, 0, -0.24), rot=(HPI, 0, 0), segs=8, rings=3)
    return p


def sickle(p):
    """A khemet grower's reaping sickle: a short wooden haft, a crescent blade curving to the edge side."""
    p.rod("wood", 0.03, -0.3, 0.24, segs=7)
    p.rod("iron", 0.034, 0.22, 0.31, segs=7)
    p.sphere("iron", 0.032, (0, 0, -0.3), scale=(1, 1, 0.5), sub=0)
    spine = [(-0.035, 0.3), (-0.02, 0.48), (0.05, 0.64), (0.18, 0.75), (0.34, 0.76), (0.48, 0.68), (0.57, 0.55)]
    edge = [(0.53, 0.55), (0.44, 0.63), (0.31, 0.68), (0.18, 0.65), (0.1, 0.56), (0.05, 0.44), (0.035, 0.3)]
    p.prism("steel", spine + edge, 0.012)
    return p


def ledger_book(p):
    """An iron-bound ledger the size of a shield, held by a strap on its back: covers facing
    out of the hand (+Z in the game), the spine on the wrist side."""
    cz = 0.3
    p.box("leather", (0.72, 0.11, 0.92), (0, 0, cz))
    p.box("bone", (0.7, 0.085, 0.9), (0.03, 0, cz))
    p.box("leather", (0.08, 0.13, 0.92), (-0.34, 0, cz))  # the spine
    for sx in (-0.33, 0.33):
        for sz in (cz - 0.43, cz + 0.43):
            p.box("iron", (0.12, 0.135, 0.12), (sx, 0, sz))
    for sz in (cz - 0.28, cz, cz + 0.28):
        p.box("iron", (0.1, 0.135, 0.05), (-0.3, 0, sz))
    for sz in (cz - 0.2, cz + 0.2):
        p.box("brass", (0.07, 0.14, 0.06), (0.35, 0, sz))
    p.box("iron", (0.12, 0.03, 0.12), (0, 0.065, cz))
    p.box("leather", (0.09, 0.03, 0.26), (0, 0.075, 0.02))
    p.box("leather", (0.16, 0.025, 0.08), (0, 0.075, 0.5))
    return p


# ======================================================================================
# Paired light weapons
# ======================================================================================

def needle(p):
    """An examiner's needle: long, steel, a ring pommel to spin it on a finger."""
    p.torus("steel", 0.05, 0.011, (0, 0, -0.14), rot=(HPI, 0, 0), segs=10, rings=4)
    p.rod("leather", 0.02, -0.09, 0.05, segs=6)
    collar(p, 0.05, 0.022, 0.03, segs=6)
    p.rod("steel", 0.013, 0.08, 0.6, r2=0.0, segs=6)
    return p


def pen_knife(p):
    """A scribe's pen-knife: a dark wood handle with brass bolsters, a short wedge blade."""
    p.box("dark_wood", (0.032, 0.05, 0.2), (0, 0, -0.085))
    p.box("brass", (0.034, 0.052, 0.025), (0, 0, 0.017))
    p.box("brass", (0.034, 0.052, 0.025), (0, 0, -0.19))
    p.blade("steel", 0.03, 0.3, 0.036, 0.007, tip=0.07, kind="wedge", taper=0.9)
    return p


def compass_dividers(p):
    """Brass dividers held like a dagger: the hinge in the fist, the points out."""
    p.cone("brass", 0.034, 0.034, 0.05, (0, 0.025, -0.06), rot=(HPI, 0, 0), segs=8)
    p.box("brass", (0.07, 0.03, 0.08), (0, 0, -0.03))
    for sx in (-1, 1):
        p.bar("brass", (sx * 0.02, 0, -0.02), (sx * 0.11, 0, 0.36), 0.017, 0.012, segs=5)
        p.bar("steel", (sx * 0.11, 0, 0.36), (sx * 0.13, 0, 0.56), 0.012, 0.0, segs=5)
    p.torus("brass", 0.26, 0.006, (0, 0, -0.03), rot=(HPI, 0, 0), segs=8, rings=3, sweep=0.9, start=HPI - 0.45)
    p.sphere("iron", 0.016, (0, 0, 0.23), sub=0)
    return p


def fist_wrap(p):
    """A wrapped fist with a brass knuckle bar: a short model that sits over the hand, the bar
    on the knuckle side (+X), a leather cuff at the wrist (-X)."""
    p.sphere("cloth", 0.14, (0.02, 0, 0), scale=(1.1, 0.8, 1.2), sub=1, jitter=0.06)
    for i, z in enumerate((-0.09, -0.03, 0.03, 0.09)):
        p.box("leather", (0.3, 0.24, 0.022), (0.02, 0, z), rot=(0.25 if i % 2 else -0.25, 0, 0.1 if i % 2 else -0.1))
    p.cone("leather", 0.11, 0.1, 0.12, (-0.22, 0, 0), rot=(0, HPI, 0), segs=8, scale=(1, 0.8, 1))
    p.cone("brass", 0.07, 0.07, 0.02, (-0.24, 0, 0), rot=(0, HPI, 0), segs=8, scale=(1, 0.8, 1))
    p.box("brass", (0.05, 0.11, 0.2), (0.17, 0, 0.0))
    for z in (-0.07, -0.023, 0.023, 0.07):
        p.cone("brass", 0.02, 0.012, 0.03, (0.19, 0, z), rot=(0, HPI, 0), segs=6)
    return p


# ======================================================================================
# Pole weapons (long along Z, the hand at the origin)
# ======================================================================================

def pilum(p):
    """A legion throwing spear: a wooden shaft, a pyramid socket, a long thin iron shank."""
    haft(p, -0.7, 0.78, r=0.028)
    p.cone("iron", 0.045, 0.028, 0.14, (0, 0, 0.76), segs=4)
    p.cone("iron", 0.028, 0.02, 0.05, (0, 0, 0.9), segs=4)
    p.rod("steel", 0.012, 0.95, 1.6, segs=6)
    p.blade("steel", 1.58, 0.22, 0.03, 0.012, tip=0.1, kind="diamond", taper=0.8)
    return p


def lance(p):
    """A rider's lance, 2.2 long: a tapering shaft, a steel vamplate before the hand, a pennon."""
    p.rod("wood", 0.038, -0.6, 1.45, r2=0.018, segs=7)
    p.sphere("brass", 0.045, (0, 0, -0.6), scale=(1, 1, 0.7), sub=0)
    grip(p, -0.16, 0.16, r=0.042, wraps=4)
    p.cone("steel", 0.05, 0.17, 0.16, (0, 0, 0.18), segs=10)
    p.cone("steel", 0.17, 0.17, 0.015, (0, 0, 0.34), segs=10)
    p.cone("steel", 0.024, 0.0, 0.2, (0, 0, 1.44), segs=6)
    p.prism("cloth", [(0.02, 1.22), (0.3, 1.33), (0.02, 1.4)], 0.008)
    return p


def naginata(p):
    """A curved single-edged blade on a long dark haft with a brass collar."""
    haft(p, -0.9, 0.9, r=0.03, mat="dark_wood")
    collar(p, 0.86, 0.04, 0.1)
    p.blade("steel", 0.96, 0.7, 0.075, 0.013, curve=0.1, tip=0.2, kind="wedge", taper=0.9)
    return p


def harpoon(p):
    """A river harpoon: a barbed head on an iron shank, the line coiled at the butt."""
    haft(p, -0.9, 0.85, r=0.03, butt="brass")
    collar(p, 0.82, 0.035, 0.06, mat="iron")
    p.rod("iron", 0.018, 0.88, 1.18, segs=6)
    p.blade("steel", 1.16, 0.32, 0.045, 0.012, tip=0.12, kind="diamond", taper=0.9)
    for sx in (-1, 1):
        p.prism("steel", [(sx * 0.02, 1.2), (sx * 0.1, 1.04), (sx * 0.02, 1.09)], 0.012)
    coil(p, 0.065, 0.012, (0, 0, -0.84), loops=4, pitch=0.028)
    p.torus("leather", 0.14, 0.011, (0.1, 0, -0.62), rot=(HPI, 0, 0.3), segs=10, rings=4)
    p.bar("leather", (0.0, 0, -0.72), (0.1, 0, -0.76), 0.011, segs=3)
    return p


def boat_hook(p):
    """A pilot's boat-hook: a spike and a curled hook on a long ash pole."""
    haft(p, -0.9, 0.9, r=0.03)
    collar(p, 0.86, 0.036, 0.08, mat="iron")
    p.cone("iron", 0.022, 0.0, 0.3, (0, 0, 0.94), segs=6)
    hook = [(0.0, 0.9), (0.04, 1.0), (0.12, 1.06), (0.2, 1.03), (0.25, 0.95), (0.25, 0.86), (0.22, 0.82), (0.21, 0.92), (0.16, 0.98), (0.1, 0.99), (0.06, 0.93), (0.04, 0.86)]
    p.prism("iron", hook, 0.028)
    return p


def grapple_hook(p):
    """An aeronaut's grapple: three curled tines on a short haft, the line coiled around it."""
    haft(p, -0.3, 0.36, r=0.028, mat="dark_wood", butt="brass")
    collar(p, 0.32, 0.04, 0.06, mat="iron")
    for i in range(3):
        a = i * 2 * math.pi / 3 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((0, 0, 0.36))
        pts = [base + Vector((0, 0, 0.16)), base + d * 0.12 + Vector((0, 0, 0.26)), base + d * 0.24 + Vector((0, 0, 0.2)), base + d * 0.27 + Vector((0, 0, 0.08))]
        prev = base
        for k, pt in enumerate(pts):
            p.bar("iron", prev, pt, 0.016 - k * 0.003, 0.016 - (k + 1) * 0.003, segs=4)
            prev = pt
    coil(p, 0.065, 0.012, (0, 0, -0.2), loops=5, pitch=0.026)
    p.torus("leather", 0.1, 0.01, (0.08, 0, -0.3), rot=(HPI, 0, 0.5), segs=10, rings=4)
    return p


def whip(p):
    """A stock whip: a leather stock with a brass cap, the lash hanging in a loose coil."""
    p.rod("leather", 0.03, -0.24, 0.3, r2=0.022, segs=7)
    p.sphere("brass", 0.034, (0, 0, -0.25), scale=(1, 1, 0.6), sub=0)
    p.torus("leather", 0.05, 0.007, (0, 0, -0.29), rot=(0, HPI, 0), segs=8, rings=3)
    for i in range(3):
        p.torus("leather", 0.2 + i * 0.012, 0.011, (0.1 + i * 0.01, (i - 1) * 0.022, 0.26), rot=(HPI + (i - 1) * 0.12, 0, (i - 1) * 0.1), segs=12, rings=4)
    p.bar("leather", (0, 0, 0.3), (0.1, 0.02, 0.46), 0.016, 0.011, segs=4)
    p.bar("leather", (0.08, -0.03, 0.06), (0.2, -0.04, -0.28), 0.009, 0.004, segs=4)
    return p


def ward_staff(p):
    """A grower's staff with a seed-pod head: the husk split, the seeds and a few dry leaves showing."""
    haft(p, -0.9, 1.0, r=0.03, mat="dark_wood", butt="brass")
    p.rod("dark_wood", 0.045, 0.95, 1.05, r2=0.07, segs=7)
    p.sphere("dark_wood", 0.15, (0, 0, 1.2), scale=(0.85, 0.85, 1.25), sub=1, jitter=0.1)
    p.retag("bone", 0.35, lambda f: f.calc_center_median().z > 1.2)
    p.sphere("bone", 0.08, (0.03, 0, 1.32), sub=1, jitter=0.15)
    for a in (0.4, 2.3, 4.1):
        tip = (math.cos(a) * 0.2, math.sin(a) * 0.2, 1.42)
        p.bar("bone", (math.cos(a) * 0.06, math.sin(a) * 0.06, 1.05), tip, 0.02, 0.0, segs=3)
    for a in (1.2, 3.4, 5.4):
        p.prism("bone", [(0.03, 1.0), (0.3, 1.12), (0.06, 1.2)], 0.01, rot=(0, 0, a))
    return p


def brush_staff(p):
    """An examiner's staff tipped with a great brush, its bristles ink-stained at the tip."""
    haft(p, -0.9, 0.92, r=0.03, mat="wood", butt="brass")
    collar(p, 0.9, 0.055, 0.14)
    p.rod("brass", 0.065, 1.03, 1.05, segs=8)
    p.cone("bone", 0.075, 0.025, 0.4, (0, 0, 1.04), segs=8)
    p.retag("iron", 1.0, lambda f: f.calc_center_median().z > 1.3)
    for a in (0.5, 1.9, 3.3, 4.7):
        p.bar("bone", (math.cos(a) * 0.06, math.sin(a) * 0.06, 1.06), (math.cos(a) * 0.05, math.sin(a) * 0.05, 1.36), 0.012, 0.004, segs=3)
    return p


def lantern_staff(p):
    """A staff with a brass lantern hung from a hook at the head, its flame lit."""
    haft(p, -0.9, 1.08, r=0.03, mat="dark_wood")
    collar(p, 1.0, 0.036, 0.1, mat="iron")
    p.bar("iron", (0, 0, 1.08), (0.2, 0, 1.06), 0.014, segs=5)
    p.bar("iron", (0.2, 0, 1.06), (0.24, 0, 0.98), 0.012, 0.008, segs=5)
    for i in range(3):
        p.torus("iron", 0.02, 0.005, (0.24, 0, 0.95 - i * 0.03), rot=(HPI if i % 2 else 0, 0, 0), segs=6, rings=3)
    lx, lz = 0.24, 0.74
    p.box("field_glow", (0.09, 0.09, 0.13), (lx, 0, lz))
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        p.box("brass", (0.018, 0.018, 0.17), (lx + sx * 0.055, sy * 0.055, lz))
    p.box("brass", (0.14, 0.14, 0.02), (lx, 0, lz - 0.09))
    p.cone("brass", 0.1, 0.03, 0.06, (lx, 0, lz + 0.08), segs=4)
    p.rod("brass", 0.02, lz + 0.13, lz + 0.17, x=lx, segs=5)
    p.box("brass", (0.05, 0.05, 0.01), (lx, 0, lz + 0.175))
    return p


# ======================================================================================
# Heavy
# ======================================================================================

def maul(p):
    """A long-hafted war hammer: an iron head with a steel face on the knuckle side, a spike behind."""
    haft(p, -0.55, 0.98, r=0.034, mat="dark_wood")
    grip(p, -0.16, 0.16, r=0.042, wraps=4)
    for sy in (-1, 1):
        p.box("iron", (0.03, 0.012, 0.5), (0, sy * 0.036, 0.6))
    collar(p, 0.62, 0.042, 0.04, mat="brass")
    p.box("iron", (0.44, 0.15, 0.2), (0, 0, 0.88))
    p.box("steel", (0.05, 0.17, 0.22), (0.24, 0, 0.88))
    p.cone("steel", 0.065, 0.0, 0.2, (-0.22, 0, 0.88), rot=(0, -HPI, 0), segs=6)
    for sy in (-1, 1):
        p.box("brass", (0.3, 0.02, 0.05), (0.02, sy * 0.08, 0.88))
    return p


def engine_arm(p):
    """An engineer's piston arm: a brass cylinder driving an iron hammer head, vents at the back,
    the hand in a bracket at the origin."""
    grip(p, -0.14, 0.14, r=0.04, wraps=3)
    p.box("iron", (0.12, 0.05, 0.36), (0, 0.07, 0.0))
    p.box("iron", (0.24, 0.14, 0.05), (0, 0.04, 0.2))
    p.box("iron", (0.24, 0.14, 0.05), (0, 0.04, -0.2))
    p.rod("brass", 0.075, 0.23, 0.62, segs=8)
    for z in (0.26, 0.58):
        p.rod("iron", 0.082, z, z + 0.035, segs=8)
    for sx in (-1, 1):
        p.rod("steel", 0.014, 0.22, 0.75, x=sx * 0.1, segs=5)
    p.rod("steel", 0.03, 0.62, 0.76, segs=6)
    p.box("iron", (0.42, 0.14, 0.18), (0, 0, 0.85))
    p.box("steel", (0.05, 0.16, 0.2), (0.23, 0, 0.85))
    p.box("iron", (0.08, 0.1, 0.12), (-0.24, 0, 0.85))
    for sy in (-1, 1):
        p.cone("brass", 0.02, 0.025, 0.1, (-0.03, sy * 0.08, 0.5), rot=(sy * -HPI, 0, 0), segs=6)
    p.cone("brass", 0.04, 0.04, 0.015, (0.09, 0, 0.42), rot=(0, HPI, 0), segs=8)
    p.cone("field_glow", 0.028, 0.028, 0.01, (0.105, 0, 0.42), rot=(0, HPI, 0), segs=8)
    p.box("iron", (0.1, 0.08, 0.2), (0, 0.03, -0.36))
    p.rod("brass", 0.03, -0.5, -0.26, segs=6)
    return p


# ======================================================================================
# Ranged (barrels along -Y here, +Z in the game, like KayKit's crossbow)
# ======================================================================================

def pistol(p):
    """A Columbia service pistol: flintlock, walnut, a steel barrel with a brass band."""
    gun_grip(p, drop=0.3, rake=0.4)
    p.box("iron", (0.09, 0.3, 0.1), (0, 0.02, 0.1))
    p.box("wood", (0.075, 0.42, 0.07), (0, -0.14, 0.08))
    barrel(p, 0.08, -0.56, 0.032, 0.14, r2=0.028)
    p.cone("brass", 0.04, 0.04, 0.03, (0, -0.25, 0.14), rot=(HPI, 0, 0), segs=8)
    lock(p, y=0.08, z=0.12)
    trigger(p, y=0.02, z=0.03)
    p.box("brass", (0.02, 0.02, 0.02), (0, 0.14, 0.18))
    p.cone("steel", 0.008, 0.008, 0.5, (0, -0.02, 0.04), rot=(HPI, 0, 0), segs=4)  # the ramrod, under the barrel
    return p


def air_pistol(p):
    """A Lunden dock-yard air pistol: a brass air tank under the barrel, a valve wheel at the breech."""
    gun_grip(p, drop=0.28, rake=0.3, mat="leather")
    p.box("steel", (0.08, 0.28, 0.09), (0, 0.02, 0.1))
    barrel(p, 0.06, -0.5, 0.024, 0.15, segs=8)
    p.cone("brass", 0.05, 0.05, 0.38, (0, 0.0, 0.07), rot=(HPI, 0, 0), segs=8)
    p.sphere("brass", 0.05, (0, -0.38, 0.07), scale=(1, 0.6, 1), sub=1)
    p.torus("brass", 0.035, 0.007, (0, 0.17, 0.12), rot=(HPI, 0, 0), segs=8, rings=3)
    for a in (0, HPI):
        p.box("brass", (0.07, 0.01, 0.01), (0, 0.17, 0.12), rot=(0, a, 0))
    p.cone("brass", 0.028, 0.028, 0.012, (0.045, 0.0, 0.12), rot=(0, HPI, 0), segs=8)
    p.cone("glass", 0.02, 0.02, 0.006, (0.057, 0.0, 0.12), rot=(0, HPI, 0), segs=8)
    trigger(p, y=0.02, z=0.04)
    return p


def musket(p):
    """A long Columbia musket: a full wooden stock, barrel bands, the lock at the wrist."""
    p.box("wood", (0.09, 0.5, 0.17), (0, 0.33, -0.05), rot=(-0.18, 0, 0))   # the butt stock, dropping back
    p.box("brass", (0.095, 0.03, 0.18), (0, 0.58, -0.1), rot=(-0.18, 0, 0))
    p.box("wood", (0.08, 0.3, 0.12), (0, 0.05, 0.03))                      # the wrist
    p.box("wood", (0.075, 1.1, 0.075), (0, -0.5, 0.07))                     # the fore-stock
    barrel(p, 0.15, -1.3, 0.03, 0.125, r2=0.026)
    for y in (-0.3, -0.65, -1.0):
        p.cone("brass", 0.045, 0.045, 0.03, (0, y, 0.11), rot=(HPI, 0, 0), segs=8)
    p.cone("steel", 0.008, 0.008, 1.0, (0, -0.1, 0.02), rot=(HPI, 0, 0), segs=4)  # the ramrod
    lock(p, y=-0.02, z=0.09)
    trigger(p, y=-0.06, z=-0.02)
    p.box("brass", (0.02, 0.02, 0.025), (0, 0.1, 0.17))
    return p


def bolt_thrower(p):
    """An engineer's heavy crossbow-rifle: an iron frame, a steel prod across the front, a
    brass magazine on top and a cocking lever under the stock."""
    p.box("dark_wood", (0.1, 0.5, 0.18), (0, 0.33, -0.06), rot=(-0.15, 0, 0))
    p.box("iron", (0.1, 0.03, 0.19), (0, 0.58, -0.1), rot=(-0.15, 0, 0))
    p.box("iron", (0.1, 1.3, 0.1), (0, -0.4, 0.06))
    p.box("steel", (0.06, 1.2, 0.03), (0, -0.4, 0.125))
    p.box("brass", (0.09, 0.32, 0.1), (0, -0.2, 0.18))
    for y in (-0.3, -0.2, -0.1):
        p.box("iron", (0.1, 0.01, 0.1), (0, y, 0.18))
    p.box("iron", (0.14, 0.1, 0.16), (0, -1.0, 0.06))
    for sx in (-1, 1):
        p.bar("steel", (sx * 0.06, -1.0, 0.07), (sx * 0.4, -0.9, 0.07), 0.025, 0.012, segs=4)
        p.bar("steel", (sx * 0.4, -0.9, 0.07), (sx * 0.56, -0.78, 0.07), 0.012, 0.008, segs=4)
    p.bar("cloth", (-0.56, -0.78, 0.07), (0.56, -0.78, 0.07), 0.006, segs=3)
    p.cone("field_glow", 0.034, 0.034, 0.025, (0, -1.07, 0.13), rot=(HPI, 0, 0), segs=8)
    p.cone("iron", 0.04, 0.04, 0.012, (0, -1.045, 0.13), rot=(HPI, 0, 0), segs=8)
    p.bar("iron", (0, 0.1, -0.08), (0, -0.35, -0.16), 0.012, segs=5)
    p.box("brass", (0.03, 0.05, 0.03), (0, -0.36, -0.17))
    trigger(p, y=-0.02, z=-0.02)
    return p


def seed_sling(p):
    """A short seed-sling gun: a flared brass muzzle, a seed hopper on top, a stubby stock."""
    gun_grip(p, drop=0.26, rake=0.45)
    p.box("wood", (0.09, 0.32, 0.12), (0, 0.08, 0.06))
    p.box("wood", (0.08, 0.25, 0.08), (0, -0.2, 0.06))
    p.cone("brass", 0.04, 0.095, 0.42, (0, -0.2, 0.13), rot=(HPI, 0, 0), segs=10)
    p.cone("field_glow", 0.1, 0.1, 0.025, (0, -0.605, 0.13), rot=(HPI, 0, 0), segs=10)
    p.cone("iron", 0.11, 0.11, 0.015, (0, -0.63, 0.13), rot=(HPI, 0, 0), segs=10)
    p.cone("iron", 0.045, 0.045, 0.22, (0, 0.02, 0.13), rot=(HPI, 0, 0), segs=8)
    p.box("brass", (0.1, 0.12, 0.08), (0, -0.08, 0.22))
    p.sphere("brass", 0.05, (0, -0.08, 0.26), scale=(1, 1.2, 0.6), sub=1)
    lock(p, y=0.08, z=0.1)
    trigger(p, y=0.03, z=0.0)
    return p


def bow_short(p):
    """A rider's recurve: short, stout, the tips curled forward."""
    bow(p, [(-0.11, 0.32), (-0.08, 0.5), (0.05, 0.6), (-0.03, 0.67)], string_y=0.05, r=0.024, mat="dark_wood", grip_len=0.18, nock_z=0.6)
    for sz in (-1, 1):
        p.box("bone", (0.03, 0.05, 0.05), (0, 0.0, sz * 0.6))
    return p


def bow_long(p):
    """A tall bow: a single stave, 1.9 from tip to tip, leather at the grip."""
    bow(p, [(-0.07, 0.45), (-0.04, 0.78), (0.05, 0.95)], string_y=0.05, r=0.024, mat="wood", grip_len=0.22)
    return p


def astrolabe(p):
    """A brass astrolabe held like a bow: the ring stands in the bow's plane, its rim through
    the fist and the rest of it out in front (+Z in the game), a rete and a sighting arm
    across it; the inner ring glows."""
    R = 0.42
    cy = -R
    p.torus("brass", R, 0.028, (0, cy, 0), rot=(0, HPI, 0), segs=16, rings=5)
    p.torus("field_glow", R - 0.045, 0.012, (0, cy, 0), rot=(0, HPI, 0), segs=16, rings=4)
    p.torus("brass", 0.2, 0.012, (0.0, cy + 0.04, 0.05), rot=(0, HPI, 0), segs=12, rings=4)
    p.bar("brass", (0, cy - 0.3, -0.2), (0, cy + 0.3, 0.2), 0.014, segs=4)
    p.bar("brass", (0, cy - 0.22, 0.3), (0, cy + 0.26, -0.24), 0.01, segs=4)
    for s_ in (-1, 1):
        p.box("brass", (0.045, 0.03, 0.06), (0, cy + s_ * 0.24, s_ * 0.16), rot=(-0.6, 0, 0))
    p.cone("iron", 0.035, 0.035, 0.03, (-0.015, cy, 0), rot=(0, HPI, 0), segs=8)
    grip(p, -0.1, 0.1, r=0.04, wraps=3)
    p.torus("brass", 0.04, 0.008, (0, cy, R + 0.06), rot=(0, HPI, 0), segs=8, rings=3)
    return p


def chakram(p):
    """A thrown steel ring: a sharp outer rim, a wrapped grip where the hand holds it."""
    R, Ri = 0.3, 0.23
    rings = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        d = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((0, 0, R))
        rings.append([c + d * Ri + Vector((0, 0.012, 0)), c + d * Ri - Vector((0, 0.012, 0)), c + d * R])
    p.loft("steel", rings, closed=True)
    p.cone("leather", 0.03, 0.03, 0.16, (0, 0, -0.08), segs=6, scale=(1.2, 1, 1))
    p.torus("brass", 0.035, 0.008, (0, 0, 0.09), rot=(0, 0, 0), segs=8, rings=3)
    p.torus("brass", 0.035, 0.008, (0, 0, -0.09), rot=(0, 0, 0), segs=8, rings=3)
    return p


# ======================================================================================
# The catalogue
# ======================================================================================

BLADES = {"cutlass": cutlass, "rapier": rapier, "gladius": gladius, "glass_blade": glass_blade, "katana": katana,
          "war_fan": war_fan, "sickle": sickle, "ledger_book": ledger_book}
PAIRED = {"needle": needle, "pen_knife": pen_knife, "compass_dividers": compass_dividers, "fist_wrap": fist_wrap}
POLES = {"pilum": pilum, "lance": lance, "naginata": naginata, "harpoon": harpoon, "boat_hook": boat_hook,
         "grapple_hook": grapple_hook, "whip": whip, "ward_staff": ward_staff, "brush_staff": brush_staff, "lantern_staff": lantern_staff}
HEAVY = {"maul": maul, "engine_arm": engine_arm}
RANGED = {"pistol": pistol, "air_pistol": air_pistol, "musket": musket, "bolt_thrower": bolt_thrower, "seed_sling": seed_sling,
          "bow_short": bow_short, "bow_long": bow_long, "astrolabe": astrolabe, "chakram": chakram}
WEAPONS = {}
for group in (BLADES, PAIRED, POLES, HEAVY, RANGED):
    WEAPONS.update(group)


def build(name):
    reset()
    objs = WEAPONS[name](Piece(name)).finish()
    if TRIS[name] > BUDGET:
        print("WARNING: %s has %d triangles, over its budget of %d" % (name, TRIS[name], BUDGET))
    return objs


# --- The contact sheet ----------------------------------------------------------------

def night(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    scene.render.film_transparent = False
    world = scene.world or bpy.data.worlds.new("night")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.014, 0.025, 1)
    for m in bpy.data.materials:
        if m.name.startswith("field") and m.use_nodes:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Emission Color"].default_value = (0.42, 0.6, 1.0, 1)
            bsdf.inputs["Emission Strength"].default_value = 3.0


def light(kind, at, aim, color, energy, size_=1.0):
    ld = bpy.data.lights.new(kind, kind)
    ld.color = color
    ld.energy = energy
    if kind == "AREA":
        ld.size = size_
    lo = bpy.data.objects.new(kind, ld)
    lo.location = at
    lo.rotation_euler = (Vector(aim) - Vector(at)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(lo)


def label(name, cam, size=0.07, k=1.0):
    """The name, pinned to the bottom of the frame k times the usual distance ahead of the camera."""
    curve = bpy.data.curves.new("label", type="FONT")
    curve.body = name
    curve.align_x = "CENTER"
    curve.size = size * k
    lab = bpy.data.objects.new("label", curve)
    lab.data.materials.append(material("sheet_text", (0.9, 0.85, 0.7, 1), 0.5, 0.0, emission=(0.95, 0.87, 0.7, 1), strength=1.0))
    bpy.context.collection.objects.link(lab)
    lab.parent = cam
    lab.location = (0, -0.36 * k, -1.2 * k)


def render_card(name, objects, path, size_px=(320, 256)):
    """One cell of the sheet: the weapon laid on its side, a three-quarter view from above under
    the moon with a faint warm lamp from the front, and its name."""
    scene = bpy.context.scene
    night(scene)
    scene.render.resolution_x, scene.render.resolution_y = size_px
    obj = objects[0]
    dims = obj.dimensions
    axis = max(range(3), key=lambda i: dims[i])
    if axis == 2:
        obj.rotation_euler = (0, -HPI, 0)     # a blade along Z lies along -X, its edge up
    elif axis == 1:
        obj.rotation_euler = (0, 0, -HPI)     # a barrel along -Y points along -X, its lock side to the camera
    bpy.context.view_layer.update()
    lo = Vector((9e9,) * 3)
    hi = Vector((-9e9,) * 3)
    for c in obj.bound_box:
        w = obj.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w))
        hi = Vector(map(max, hi, w))
    centre = (lo + hi) / 2
    size = max((hi - lo).length, 0.5)
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(centre.x, centre.y, lo.z - 0.02))
    ground = bpy.context.active_object
    ground.data.materials.append(material("sheet_ground", (0.03, 0.028, 0.025, 1), 0.95))
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 42
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = centre + Vector((size * 0.25, -size * 1.05, size * 0.75))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    label(name, cam, k=max(0.3, size * 0.55))
    light("SUN", centre + Vector((-size, -size * 0.5, size * 1.6)), centre, (0.55, 0.62, 0.95), 2.4)
    light("AREA", centre + Vector((size * 1.5, -size * 1.2, size * 0.4)), centre, (1.0, 0.6, 0.3), 14 * size * size, size)
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


# --- The in-hand check ------------------------------------------------------------------

HAND_CHECKS = [  # (label, model path, animation, frame fraction)
    ("kaykit sword (idle)", os.path.join(KAYKIT, "sword_1handed.gltf"), "Idle", 0.5),
    ("cutlass (idle)", os.path.join(OUT, "cutlass.glb"), "Idle", 0.5),
    ("lance (2H idle)", os.path.join(OUT, "lance.glb"), "2H_Melee_Idle", 0.5),
    ("kaykit crossbow (aiming)", os.path.join(KAYKIT, "crossbow_1handed.gltf"), "1H_Ranged_Aiming", 0.6),
    ("pistol (aiming)", os.path.join(OUT, "pistol.glb"), "1H_Ranged_Aiming", 0.6),
    ("bow_long (2H aiming)", os.path.join(OUT, "bow_long.glb"), "2H_Ranged_Aiming", 0.6),
]


def render_hand(title, weapon_path, action, frac, path, size_px=(640, 640)):
    """Knight.glb with the weapon hung from handslot.r exactly as the game hangs it: the slot's
    transform and the model's with no offset. Blender's importer converts the weapon's
    vertices to Z up but leaves the bone's axes as the glTF node's, so the hung object gets a
    -90 degree turn about X to put its Blender coordinates back on its glTF ones."""
    reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(PEOPLE, "Knight.glb"), bone_heuristic="BLENDER")
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
    for o in bpy.data.objects:
        if o.type == "MESH" and any(k in o.name for k in ("Sword", "Shield")):
            o.hide_render = True
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=weapon_path)
    for o in bpy.data.objects:
        if o not in before and o.type == "MESH":
            o.matrix_basis = Matrix.Rotation(-HPI, 4, "X")
            c = o.constraints.new("CHILD_OF")
            c.target = arm
            c.subtarget = "handslot.r"
            c.inverse_matrix = Matrix.Identity(4)
    a = bpy.data.actions[action]
    arm.animation_data_create()
    arm.animation_data.action = a
    try:
        arm.animation_data.action_slot = a.slots[0]
    except Exception:
        pass
    f0, f1 = a.frame_range
    bpy.context.scene.frame_set(int(f0 + (f1 - f0) * frac))
    scene = bpy.context.scene
    night(scene)
    scene.cycles.samples = 16
    scene.render.resolution_x, scene.render.resolution_y = size_px
    centre = Vector((0, -0.2, 1.25))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    bpy.context.collection.objects.link(cam)
    cam.location = centre + Vector((-2.6, -3.0, 1.3))   # front-right of the character, which faces -Y
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    label(title, cam, size=0.06)
    light("SUN", centre + Vector((-3, -2, 5)), centre, (0.55, 0.62, 0.95), 3.0)
    light("AREA", centre + Vector((3, -4, 1)), centre, (1.0, 0.6, 0.3), 400, 2.0)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(material("sheet_ground", (0.03, 0.028, 0.025, 1), 0.95))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_hands(path):
    cells = []
    for i, (title, model, action, frac) in enumerate(HAND_CHECKS):
        cell = os.path.join(os.path.dirname(path), "hand_cells", "%d.png" % i)
        os.makedirs(os.path.dirname(cell), exist_ok=True)
        render_hand(title, model, action, frac, cell)
        cells.append(cell)
    reset()
    compose_sheet(cells, path, cell=(640, 640), cols=3)


if __name__ == "__main__":
    args = sys.argv[1:]
    sheet = hands = None
    if "--sheet" in args:
        i = args.index("--sheet")
        sheet = args[i + 1]
        args = args[:i] + args[i + 2:]
    if "--hands" in args:
        i = args.index("--hands")
        hands = args[i + 1]
        args = args[:i] + args[i + 2:]
    wanted = args or list(WEAPONS)
    cells = []
    for name in wanted:
        objs = build(name)
        export(os.path.join(OUT, name + ".glb"), objs)
        if sheet:
            cell = os.path.join(os.path.dirname(sheet), "weapon_cells", name + ".png")
            render_card(name, objs, cell)
            cells.append(cell)
    if sheet:
        reset()
        compose_sheet(cells, sheet)
    if hands:
        render_hands(hands)
    print("triangles:", ", ".join("%s %d" % (n, TRIS[n]) for n in wanted))
