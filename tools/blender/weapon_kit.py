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
  - Flat-shaded low poly (a made thing keeps its cut edges: docs/style.md), no textures, a few hundred to a thousand triangles each. Materials
    by name from a small palette (steel with a bright edge and a dark fuller, iron, brass,
    two woods, two leathers, bone, glass, cloth, paper), exported under names the game's toon
    shader reads as metal, wood, leather or cloth; a material named field_glow marks what
    should glow in the game (muzzles, the astrolabe's ring, the lantern's flame, the glass
    blade's edge).
  - Sized for the human hand (2026-11-10): people are 2.4 tall and a unit is about 0.73 m, so
    a grip is 0.054 across and about 0.23 long below the guard, a haft 0.046 across, a saber's
    blade about 0.98, a musket's barrel 1.42. The bodies' hands are closed round a grip
    (human.py, GRIP) and the hand slot sits in the hollow of the fist at its thumb side, so
    a guard rests on the fist and a pommel shows below it. The shields and the two staves are
    the kit's own now (shield_round, shield_badge, staff, oar_staff).
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
OUT = os.path.join(ROOT, "game", "assets", "weapons")
PEOPLE = os.path.join(ROOT, "game", "assets", "people")
KAYKIT = os.path.join(ROOT, "game", "assets", "kaykit", "weapons")
BUDGET = 3000

# Linear colour, roughness, metallic. Muted earths and worn metals; the field's colour carries the eye.
PALETTE = {
    "steel": ((0.46, 0.48, 0.52), 0.38, 0.9),
    "steel_edge": ((0.78, 0.80, 0.84), 0.25, 0.9),      # the ground bevel of an edge, the polish of a face
    "steel_dark": ((0.2, 0.21, 0.25), 0.5, 0.9),        # a fuller, a blued barrel, the back of a blade
    "iron": ((0.12, 0.12, 0.14), 0.62, 0.7),
    "brass": ((0.52, 0.33, 0.1), 0.45, 0.85),
    "brass_dark": ((0.3, 0.18, 0.06), 0.5, 0.85),
    "wood": ((0.3, 0.18, 0.09), 0.85, 0.0),
    "dark_wood": ((0.13, 0.08, 0.05), 0.8, 0.0),
    "leather": ((0.2, 0.1, 0.06), 0.75, 0.0),
    "leather_dark": ((0.09, 0.05, 0.035), 0.75, 0.0),
    "bone": ((0.62, 0.55, 0.42), 0.6, 0.0),
    "glass": ((0.03, 0.07, 0.09), 0.08, 0.0),
    "cloth": ((0.2, 0.17, 0.24), 0.9, 0.0),
    "cloth_red": ((0.42, 0.1, 0.09), 0.9, 0.0),
    "paper": ((0.7, 0.64, 0.5), 0.9, 0.0),
}
# The game's toon shader reads a surface from a material's name (World.surface_of): a metal
# must say so, or a blade is shaded as cloth. The palette's names stay short in this file.
EXPORT_NAME = {"steel": "metal_steel", "steel_edge": "metal_steel_edge", "steel_dark": "metal_steel_dark", "iron": "metal_iron",
               "brass": "metal_brass", "brass_dark": "metal_brass_dark", "glass": "metal_glass", "paper": "cloth_paper"}
TRIS = {}  # weapon name -> triangle count, for the report
HPI = math.pi / 2


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, rough=0.8, metallic=0.0, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    color = style.conform(name, color)      # on the ramps of what its name says it is
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
    return material(EXPORT_NAME.get(name, name), col, rough, metallic)


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
        m = bpy.data.materials.get(EXPORT_NAME.get(name, name))
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

    # --- the second vocabulary (2026-11-10): turned, cut and banded forms ------------------

    def strip_loft(self, rings, mats, cap="steel", loc=(0, 0, 0), rot=(0, 0, 0), closed=False):
        """A loft whose faces take their material from the strip they lie on: the face between
        ring points i and i+1 is mats[i]. A ring that is one point repeated is a tip."""
        bm = bmesh.new()
        vr = []
        for ring in rings:
            if all((Vector(q) - Vector(ring[0])).length < 1e-9 for q in ring):
                v = bm.verts.new(ring[0])
                vr.append([v] * len(ring))
            else:
                vr.append([bm.verts.new(q) for q in ring])
        n = len(rings[0])
        idx = {m: self.mat_index(m) for m in set(mats) | {cap}}
        pairs = list(zip(vr, vr[1:])) + ([(vr[-1], vr[0])] if closed else [])
        for ra, rb in pairs:
            for i in range(n):
                j = (i + 1) % n
                quad = []
                for v in (ra[i], ra[j], rb[j], rb[i]):
                    if v not in quad:
                        quad.append(v)
                if len(quad) >= 3:
                    try:
                        f = bm.faces.new(quad)
                        f.material_index = idx[mats[i % len(mats)]]
                    except ValueError:
                        pass
        if not closed:
            for ring, flip in ((vr[0], True), (vr[-1], False)):
                if len(set(ring)) > 2:
                    f = bm.faces.new(list(reversed(ring)) if flip else ring)
                    f.material_index = idx[cap]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.transform(bm, matrix=xform(loc, rot), verts=bm.verts[:])
        for f in bm.faces:
            f.smooth = False
        mesh = bpy.data.meshes.new("tmp")
        bm.to_mesh(mesh)
        bm.free()
        self.bm.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)
        # from_mesh keeps the material indices as set: make sure the slots exist
        return self

    def lathe(self, mat, profile, segs=10, loc=(0, 0, 0), rot=(0, 0, 0)):
        """A turned form about Z: profile is (radius, z) from the bottom up; a radius of 0 at
        an end closes it to a point. mat is one name, or one per band between profile points."""
        rings = []
        for r, z in profile:
            if r <= 1e-6:
                rings.append([Vector((0, 0, z))] * segs)
            else:
                rings.append([Vector((math.cos(2 * math.pi * k / segs) * r, math.sin(2 * math.pi * k / segs) * r, z)) for k in range(segs)])
        if isinstance(mat, (list, tuple)):
            for i in range(len(rings) - 1):
                self.loft(mat[min(i, len(mat) - 1)], rings[i:i + 2], cap_start=(i == 0), cap_end=(i == len(rings) - 2), loc=loc, rot=rot)
        else:
            self.loft(mat, rings, loc=loc, rot=rot)
        return self

    def tube(self, mat, points, radii, segs=5):
        """A tube through points, its radius given at each (or one for all): bows, guards, hooks, cords."""
        pts = [Vector(q) for q in points]
        if not isinstance(radii, (list, tuple)):
            radii = [radii] * len(pts)
        rings = []
        up = None
        for i, q in enumerate(pts):
            d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
            u = d.cross(ref).normalized() if up is None else (up - d * up.dot(d)).normalized()
            up = u
            w = d.cross(u).normalized()
            r = radii[i]
            if r <= 1e-6:
                rings.append([q] * segs)
            else:
                rings.append([q + (u * math.cos(2 * math.pi * k / segs) + w * math.sin(2 * math.pi * k / segs)) * r for k in range(segs)])
        self.loft(mat, rings)
        return self

    def slab(self, mat, pts, thick, bevel=0.25, y=0.0, loc=(0, 0, 0), rot=(0, 0, 0)):
        """A plate cut from an outline in the XZ plane ((x, z) points), `thick` along Y, its
        edges chamfered: stocks, guards, cheeks, plates."""
        cx = sum(q[0] for q in pts) / len(pts)
        cz = sum(q[1] for q in pts) / len(pts)
        b = thick * bevel
        k = 1.0 - min(0.5, b / max(1e-6, max(max(abs(q[0] - cx), abs(q[1] - cz)) for q in pts)))
        inner = [(cx + (q[0] - cx) * k, cz + (q[1] - cz) * k) for q in pts]
        rings = [[Vector((x, y - thick / 2, z)) for x, z in inner], [Vector((x, y - thick / 2 + b, z)) for x, z in pts],
                 [Vector((x, y + thick / 2 - b, z)) for x, z in pts], [Vector((x, y + thick / 2, z)) for x, z in inner]]
        self.loft(mat, rings, loc=loc, rot=rot)
        return self

    def edge_blade(self, z0, length, width, thick, kind="saber", curve=0.0, tip=0.22, taper=0.85, fuller=(0.06, 0.7), flare=0.0,
                   mat="steel", edge="steel_edge", dark="steel_dark", stations=9, x0=0.0):
        """A blade along +Z from z0 with a bright bevelled edge and, if asked, a dark fuller.
        kind "saber": one edge on +X, the spine on -X, the point at the spine's end; "sword":
        two edges and a point on the middle line. `curve` bows it toward -X; `taper` is the
        width left where the tip begins; `flare` swells it mid-way (a leaf); `fuller` is where
        along the body the groove starts and ends (None for a ridge)."""
        body = length - tip
        rings = []
        total = stations + 4
        for s_ in range(total + 1):
            f = s_ / total
            z = z0 + length * f
            fb = min(1.0, length * f / body)                     # along the body
            w = width * (1 - (1 - taper) * fb) * (1 + flare * math.sin(math.pi * fb))
            t = thick * (1 - 0.4 * f)
            if length * f > body:                               # the point: an ogive
                u = (length * f - body) / tip
                w *= max(0.0, 1 - u ** 1.7)
                t *= max(0.15, 1 - u)
            cx = x0 - curve * f * f
            g = 1.0
            if fuller:
                a, b_ = fuller
                edge_in = 0.08
                g = 0.42 if a + edge_in < fb < b_ - edge_in else (1.0 if (fb <= a or fb >= b_) else 0.42 + 0.58 * (1 - min(fb - a, b_ - fb) / edge_in))
            if kind == "saber":
                sx = cx - width * 0.5                             # the spine's line
                top = [(sx, t), (sx + w * 0.2, t), (sx + w * 0.26, t * g), (sx + w * 0.5, t * g), (sx + w * 0.56, t * 0.95), (sx + w * 0.72, t * 0.8), (sx + w, 0.0)]
                mats = [mat, dark, dark, dark, mat, edge, edge, mat, dark, dark, dark, mat, mat]
            else:
                top = [(cx - w, 0.0), (cx - w * 0.62, t * 0.6), (cx - w * 0.2, t), (cx - w * 0.13, t * g), (cx + w * 0.13, t * g), (cx + w * 0.2, t), (cx + w * 0.62, t * 0.6), (cx + w, 0.0)]
                mats = [edge, mat, dark, dark, dark, mat, edge, edge, mat, dark, dark, dark, mat, edge]
            if s_ == total:
                tipx = (cx - width * 0.5) if kind == "saber" else cx
                rings.append([Vector((tipx, 0, z))] * (2 * len(top) - (1 if kind == "saber" else 2)))
                continue
            if kind == "saber":
                ring = [Vector((x, y, z)) for x, y in top] + [Vector((x, -y, z)) for x, y in reversed(top[:-1])]
            else:
                ring = [Vector((x, y, z)) for x, y in top] + [Vector((x, -y, z)) for x, y in reversed(top[1:-1])]
            rings.append(ring)
        self.strip_loft(rings, mats, cap=mat)
        return self

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

# ======================================================================================
# Shared parts. Sizes are for the human hand (people are 2.4 tall, a unit is about 0.73 m):
# a grip is 0.054 across, a haft 0.046, a one-handed grip 0.23 long below the guard.
# ======================================================================================

GRIP_R = 0.027
HAFT_R = 0.023


def grip(p, z0, z1, r=GRIP_R, mat="leather", band="leather_dark", wraps=5, segs=8, swell=0.14):
    """A handle along Z with a slight swell, wound in two tones."""
    n = max(2, wraps * 2)
    prof = [(r * (1 + swell * math.sin(math.pi * i / n)), z0 + (z1 - z0) * i / n) for i in range(n + 1)]
    p.lathe([mat if i % 2 == 0 else band for i in range(n)], prof, segs=segs)


def ferrule(p, z, r=GRIP_R, h=0.02, mat="brass", segs=8):
    """A turned ring: where a grip meets a guard, a haft its head."""
    p.lathe(mat, [(r * 1.04, z), (r * 1.22, z + h * 0.3), (r * 1.22, z + h * 0.7), (r * 1.04, z + h)], segs=segs)


def pommel(p, z, r=0.04, mat="brass", style="scent"):
    """The end of a hilt, turned: scent (a stopper), cap (a low dome), ball, or ring."""
    if style == "ring":
        p.torus(mat, r, r * 0.26, (0, 0, z - r), rot=(HPI, 0, 0), segs=10, rings=4)
    elif style == "cap":
        p.lathe(mat, [(r, z + 0.012), (r * 1.05, z), (r * 0.8, z - r * 0.5), (0.0, z - r * 0.72)], segs=8)
    elif style == "ball":
        p.lathe(mat, [(r * 0.5, z + 0.005), (r * 0.9, z - r * 0.35), (r, z - r * 0.9), (r * 0.8, z - r * 1.5), (r * 0.3, z - r * 1.85), (0.0, z - r * 1.95)], segs=8)
    else:
        p.lathe(mat, [(r * 0.62, z + 0.006), (r, z - r * 0.5), (r * 0.92, z - r * 1.1), (r * 0.5, z - r * 1.7), (r * 0.42, z - r * 2.0), (0.0, z - r * 2.15)], segs=8)


def quillons(p, z, half, mat="brass", r=0.016, droop=0.0, finial=0.022, block=(0.07, 0.05, 0.045)):
    """A cross-guard: a block on the blade's shoulder and two tapering arms along X, their
    ends turned toward the blade by `droop`, a small knob on each."""
    p.box(mat, block, (0, 0, z))
    for sx in (-1, 1):
        pts = [(sx * block[0] * 0.4, 0, z), (sx * half * 0.6, 0, z + droop * 0.25), (sx * half, 0, z + droop)]
        p.tube(mat, pts, [r, r * 0.85, r * 0.6], segs=6)
        if finial:
            p.sphere(mat, finial, pts[-1], sub=1)


def knuckle_bow(p, z_top, z_bot, reach, mat="brass", r=0.011, x0=0.0):
    """A bar from the guard's front (+X) round to the pommel."""
    pts = []
    for i in range(7):
        t = i / 6.0
        x = x0 + reach * (1 - t) ** 0.55 * (1.0 if t < 0.999 else 0.0) + 0.02 * t
        zc = z_top + (z_bot - z_top) * (t ** 1.25)
        pts.append((x, 0, zc))
    p.tube(mat, pts, r, segs=5)


def haft(p, z0, z1, r=HAFT_R, mat="wood", butt="iron", bands=(), band_mat="leather_dark", spike=True):
    """A pole along Z with a shoe at the butt and any bindings named by height."""
    p.rod(mat, r, z0 + 0.07, z1, segs=7)
    if spike:
        p.lathe(butt, [(0.0, z0 - 0.02), (r * 0.7, z0 + 0.02), (r * 1.18, z0 + 0.05), (r * 1.18, z0 + 0.085), (r * 1.02, z0 + 0.09)], segs=7)
    else:
        p.lathe(butt, [(r * 0.8, z0), (r * 1.2, z0 + 0.02), (r * 1.2, z0 + 0.08), (r * 1.02, z0 + 0.085)], segs=7)
    for zb in bands:
        p.lathe(band_mat, [(r * 1.03, zb - 0.04), (r * 1.2, zb - 0.03), (r * 1.2, zb + 0.03), (r * 1.03, zb + 0.04)], segs=7)


def socket(p, z, r=HAFT_R, h=0.16, top=0.014, mat="steel_dark", langets=0.0):
    """Where a head is fitted to a haft: a tapering sleeve with a ring, and langets down the wood."""
    p.lathe(mat, [(r * 1.3, z), (r * 1.42, z + 0.012), (r * 1.3, z + 0.03), (max(top, 0.008), z + h)], segs=7)
    if langets:
        for sy in (-1, 1):
            p.box(mat, (r * 0.9, 0.006, langets), (0, sy * r * 1.02, z - langets / 2))


def coil(p, R, r, loc, loops=3, pitch=0.03, rot=(0, 0, 0), mat="leather"):
    """A coiled line: a few rings stacked along their axis, each a little off the last."""
    for i in range(loops):
        p.torus(mat, R * p.rng.uniform(0.94, 1.06), r, (loc[0] + p.rng.uniform(-0.01, 0.01), loc[1] + p.rng.uniform(-0.01, 0.01), loc[2] + i * pitch),
                rot=(rot[0] + p.rng.uniform(-0.08, 0.08), rot[1] + p.rng.uniform(-0.08, 0.08), rot[2]), segs=10, rings=4)


# --- guns: barrels along -Y, the top at +Z, the grip hanging from the origin -------------

def stock(p, outline, thick, mat="wood", bevel=0.3):
    """A stock cut from its side view: (y, z) points, y back toward the shoulder."""
    p.slab(mat, outline, thick, bevel=bevel, rot=(0, 0, HPI))


def pistol_grip(p, drop=0.24, rake=0.42, mat="dark_wood", cap="brass", thick=0.058):
    """A curved pistol butt hanging from the origin, raked back (+Y), with a cap."""
    c, s_ = math.cos(rake), math.sin(rake)
    out = []
    for t, w in ((0.0, 0.062), (0.3, 0.05), (0.65, 0.05), (1.0, 0.064)):
        cy, cz = s_ * drop * t + 0.02 * math.sin(math.pi * t), -c * drop * t
        out.append((cy - w * c, cz - w * s_))
    back = []
    for t, w in ((1.0, 0.064), (0.65, 0.05), (0.3, 0.05), (0.0, 0.062)):
        cy, cz = s_ * drop * t + 0.02 * math.sin(math.pi * t), -c * drop * t
        back.append((cy + w * c, cz + w * s_))
    stock(p, out + back, thick, mat)
    by, bz = s_ * drop + 0.0, -c * drop
    p.lathe(cap, [(0.0, -0.022), (0.04, -0.012), (0.046, 0.0), (0.04, 0.014)], segs=8, loc=(0, by, bz), rot=(rake, 0, 0))


def barrel(p, y0, length, r, z, mat="steel_dark", breech=0.3, swell=1.28, flare=1.0, glow=True, segs=8):
    """A barrel from y0 forward (-Y) at height z: a heavier breech, a turned band, a muzzle
    ring and the field's light in the bore."""
    L = length
    rm = r * flare
    prof = [(r * swell, 0.0), (r * swell, L * breech), (r * 1.12, L * breech + 0.012), (r, L * breech + 0.03),
            (rm if flare != 1.0 else r * 0.92, L - 0.05), (rm * 1.2, L - 0.04), (rm * 1.2, L - 0.012), (rm, L)]
    p.lathe(mat, prof, segs=segs, loc=(0, y0, z), rot=(HPI, 0, 0))
    if glow:
        p.cone("field_glow", rm * 0.72, rm * 0.72, 0.012, (0, y0 - L + 0.004, z), rot=(HPI, 0, 0), segs=segs)


def flintlock(p, y=0.06, z=0.11, side=1, x=0.034):
    """A flintlock on the right side (+X): the plate, the cock drawn back with its flint, the
    frizzen and the pan ahead of it."""
    xs = side * x
    p.slab("steel", [(-0.1, -0.03), (0.09, -0.035), (0.11, 0.0), (0.06, 0.028), (-0.09, 0.03)], 0.014, rot=(0, 0, HPI), loc=(xs, y, z))
    # the cock: a goose-neck leaning back
    pts = [(xs + side * 0.012, y + 0.035, z + 0.0), (xs + side * 0.012, y + 0.06, z + 0.05), (xs + side * 0.012, y + 0.03, z + 0.085), (xs + side * 0.012, y - 0.005, z + 0.09)]
    p.tube("steel_dark", pts, [0.014, 0.011, 0.01, 0.012], segs=4)
    p.box("bone", (0.014, 0.03, 0.01), (xs + side * 0.012, y - 0.02, z + 0.088))
    # the frizzen and the pan
    p.box("steel", (0.016, 0.012, 0.055), (xs + side * 0.012, y - 0.065, z + 0.045), rot=(0.25, 0, 0))
    p.box("steel_dark", (0.022, 0.04, 0.012), (xs + side * 0.014, y - 0.05, z + 0.012))


def trigger(p, y=0.02, z=0.0, mat="brass", size=1.0):
    """A trigger in its bow."""
    p.tube("steel", [(0, y - 0.004, z - 0.005), (0, y + 0.004, z - 0.03), (0, y - 0.006, z - 0.05)], [0.007, 0.006, 0.004], segs=4)
    pts = [(0, y + 0.06 * size * math.cos(a), z - 0.012 - 0.062 * size * math.sin(a)) for a in [math.pi * i / 6 for i in range(7)]]
    p.tube(mat, pts, 0.006, segs=4)


def ramrod(p, y0, length, z, r=0.007):
    p.cone("steel", r, r, length, (0, y0, z), rot=(HPI, 0, 0), segs=5)
    p.cone("brass", r * 1.6, r * 1.6, 0.02, (0, y0 - length, z), rot=(HPI, 0, 0), segs=5)


def band(p, y, z, r, mat="brass", w=0.022, segs=8):
    """A barrel band about the barrel and the fore-stock."""
    p.cone(mat, r, r, w, (0, y + w / 2, z), rot=(HPI, 0, 0), segs=segs)


def bow(p, limbs, string_y, width=0.036, thick=0.02, mat="wood", grip_len=0.2, tip_mat="bone", belly=None):
    """A bow along Z: limbs is a list of (y, z) stations for the upper limb from the grip out
    (the lower mirrors it), flat in section and tapering; the string runs nock to nock at
    string_y (behind, +Y), served at the middle."""
    grip(p, -grip_len / 2, grip_len / 2, r=0.024, wraps=4)
    for zf in (-grip_len / 2 - 0.012, grip_len / 2 - 0.006):
        ferrule(p, zf, r=0.024, h=0.018, mat="leather_dark")
    n = len(limbs)
    for sz in (-1, 1):
        rings = []
        pts = [(0.0, grip_len / 2)] + list(limbs)
        for i, (y, z) in enumerate(pts):
            f = i / n
            w = width * (1 - 0.6 * f)
            t = thick * (1 - 0.45 * f)
            rings.append([Vector((-w, y - t * 0.3, sz * z)), Vector((0, y - t, sz * z)), Vector((w, y - t * 0.3, sz * z)), Vector((w * 0.8, y + t, sz * z)), Vector((-w * 0.8, y + t, sz * z))])
        p.strip_loft(rings, [mat, mat, belly or mat, belly or mat, belly or mat], cap=mat)
        ty, tz = pts[-1]
        p.box(tip_mat, (0.03, 0.03, 0.05), (0, ty, sz * (tz + 0.012)))
    tip_z = limbs[-1][1]
    p.tube("paper", [(0, limbs[-1][0] + 0.004, -tip_z), (0, string_y, -tip_z * 0.5), (0, string_y, tip_z * 0.5), (0, limbs[-1][0] + 0.004, tip_z)], 0.0045, segs=3)
    p.cone("cloth_red", 0.008, 0.008, 0.09, (0, string_y, -0.045), segs=4)


# ======================================================================================
# Blades and their kin
# ======================================================================================

def cutlass(p):
    """A marshal's saber: a curved single-edged blade with a fuller, a brass knuckle bow, a wound grip."""
    grip(p, -0.21, 0.02, wraps=5)
    ferrule(p, 0.02, h=0.022)
    pommel(p, -0.215, 0.036, style="cap")
    p.slab("brass", [(-0.06, 0.035), (0.11, 0.035), (0.13, 0.05), (0.11, 0.066), (-0.07, 0.066), (-0.085, 0.05)], 0.05, bevel=0.3)
    knuckle_bow(p, 0.05, -0.235, 0.125)
    p.edge_blade(0.066, 0.98, 0.074, 0.011, kind="saber", curve=0.13, tip=0.24, taper=0.92, fuller=(0.04, 0.62), x0=0.005)
    return p


def rapier(p):
    """A Lunden rapier: a cup hilt, long quillons, a knuckle bow, a narrow diamond blade."""
    grip(p, -0.19, 0.0, r=0.021, mat="cloth", band="steel_dark", wraps=7, segs=6)
    pommel(p, -0.195, 0.033, "steel", style="scent")
    p.lathe("steel", [(0.022, 0.005), (0.07, 0.012), (0.105, 0.04), (0.112, 0.075), (0.108, 0.08), (0.1, 0.045), (0.066, 0.02), (0.022, 0.014)], segs=12)
    quillons(p, 0.02, 0.2, mat="steel", r=0.01, finial=0.014, block=(0.04, 0.03, 0.025))
    knuckle_bow(p, 0.02, -0.21, 0.11, mat="steel", r=0.008)
    p.box("steel_dark", (0.03, 0.014, 0.07), (0, 0, 0.115))                    # the ricasso inside the cup
    p.edge_blade(0.14, 1.22, 0.02, 0.01, kind="sword", tip=0.18, taper=0.55, fuller=None)
    return p


def gladius(p):
    """A short broad legion blade: a ridged bone grip, a round wooden pommel, a leaf blade with a mid-rib."""
    p.lathe(["bone"] * 9, [(0.024, -0.19), (0.03, -0.17), (0.024, -0.145), (0.03, -0.12), (0.024, -0.095), (0.03, -0.07), (0.024, -0.045), (0.03, -0.02), (0.026, 0.0)], segs=8)
    p.lathe("dark_wood", [(0.0, -0.275), (0.04, -0.262), (0.054, -0.232), (0.04, -0.2), (0.026, -0.19)], segs=8)
    p.lathe("brass", [(0.012, -0.29), (0.02, -0.28), (0.0, -0.272)], segs=6)
    p.slab("dark_wood", [(-0.085, 0.0), (0.085, 0.0), (0.075, 0.045), (-0.075, 0.045)], 0.066, bevel=0.3)
    p.box("brass", (0.15, 0.07, 0.008), (0, 0, 0.049))
    p.edge_blade(0.053, 0.74, 0.04, 0.012, kind="sword", tip=0.22, taper=0.95, fuller=None, flare=0.16)
    return p


def glass_blade(p):
    """A straight blade of dark glass in brass fittings; the edge carries the field's light."""
    grip(p, -0.21, 0.02, mat="leather_dark", band="brass_dark", wraps=4)
    ferrule(p, 0.02)
    ferrule(p, -0.225)
    pommel(p, -0.225, 0.034, style="ball")
    quillons(p, 0.058, 0.115, r=0.014, droop=0.03, finial=0.018, block=(0.075, 0.05, 0.04))
    p.edge_blade(0.078, 1.02, 0.034, 0.013, kind="sword", tip=0.2, taper=0.82, fuller=None, mat="glass", edge="field_glow", dark="glass")
    p.box("brass", (0.05, 0.03, 0.06), (0, 0, 0.105))
    return p


def katana(p):
    """A long two-handed curve: a wrapped grip with its diamonds, an iron guard, a brass collar."""
    n = 15
    prof = [(0.024 + (0.002 if i % 2 else 0.0), -0.34 + 0.38 * i / n) for i in range(n + 1)]
    p.lathe(["cloth" if i % 2 == 0 else "paper" for i in range(n)], prof, segs=6)
    p.lathe("iron", [(0.0, -0.362), (0.022, -0.356), (0.027, -0.34)], segs=6)
    p.lathe("iron", [(0.03, 0.04), (0.07, 0.043), (0.074, 0.049), (0.07, 0.055), (0.03, 0.058)], segs=10)   # the guard
    p.lathe("brass", [(0.03, 0.058), (0.031, 0.1), (0.022, 0.104)], segs=6)                                  # the collar
    p.edge_blade(0.1, 0.98, 0.052, 0.01, kind="saber", curve=0.11, tip=0.14, taper=0.9, fuller=None, x0=0.004)
    return p


def war_fan(p):
    """An iron war fan, half open: steel ribs from a brass pivot, dark leaves, a bright edge."""
    grip(p, -0.2, 0.06, r=0.022, mat="leather_dark", band="iron", wraps=4, segs=6)
    p.lathe("brass", [(0.0, -0.02), (0.03, -0.012), (0.03, 0.012), (0.0, 0.02)], segs=8, loc=(0, 0, 0.09), rot=(HPI, 0, 0))
    n = 8
    R, Ri = 0.6, 0.2
    for i in range(n):
        a = HPI * 1.15 * i / (n - 1) - 0.1
        tip = (math.sin(a) * R, 0, 0.09 + math.cos(a) * R)
        p.tube("steel", [(0, 0, 0.09), tip], [0.011, 0.006], segs=4)
    k = 14
    ang = [HPI * 1.15 * j / k - 0.1 for j in range(k + 1)]
    leaf = [(math.sin(a) * (R - 0.03), 0.09 + math.cos(a) * (R - 0.03)) for a in ang] + [(math.sin(a) * Ri, 0.09 + math.cos(a) * Ri) for a in reversed(ang)]
    p.prism("cloth", leaf, 0.008)
    rim = [(math.sin(a) * (R + 0.012), 0.09 + math.cos(a) * (R + 0.012)) for a in ang] + [(math.sin(a) * (R - 0.03), 0.09 + math.cos(a) * (R - 0.03)) for a in reversed(ang)]
    p.prism("steel_edge", rim, 0.01)
    p.torus("cloth_red", 0.028, 0.006, (0, 0, -0.23), rot=(HPI, 0, 0), segs=8, rings=3)
    return p


def sickle(p):
    """A khemet grower's reaping sickle: a short turned haft, a crescent blade with its edge inside the curve."""
    grip(p, -0.2, 0.2, r=0.024, mat="wood", band="wood", wraps=2, segs=7, swell=0.1)
    ferrule(p, 0.19, r=0.024, h=0.05, mat="iron")
    p.lathe("iron", [(0.0, -0.225), (0.03, -0.215), (0.028, -0.2)], segs=7)
    p.tube("iron", [(0, 0, 0.23), (-0.012, 0, 0.3), (-0.012, 0, 0.36)], [0.02, 0.016, 0.012], segs=6)
    k = 12
    spine, edge, mid = [], [], []
    for i in range(k + 1):
        t = i / k
        a = -0.35 + 2.3 * t
        cx, cz = 0.27, 0.42
        r_out = 0.3 - 0.02 * t
        w = 0.1 * (1 - t ** 1.6) + 0.004
        spine.append((cx - math.cos(a) * r_out, cz + math.sin(a) * r_out * 1.02))
        mid.append((cx - math.cos(a) * (r_out - w * 0.6), cz + math.sin(a) * (r_out - w * 0.6) * 1.02))
        edge.append((cx - math.cos(a) * (r_out - w), cz + math.sin(a) * (r_out - w) * 1.02))
    p.prism("steel", spine + list(reversed(mid)), 0.012)
    p.prism("steel_edge", mid + list(reversed(edge)), 0.006)
    return p


def ledger_book(p):
    """An iron-bound ledger the size of a buckler, held by a strap on its back: the covers face
    out of the hand, the spine on the wrist side; pages, raised bands, corners, a clasp."""
    cz = 0.24
    W, H, T = 0.52, 0.7, 0.1
    p.box("paper", (W - 0.03, T - 0.03, H - 0.04), (0.012, 0, cz))                         # the page block
    for sy in (-1, 1):
        p.slab("leather", [(-W / 2, cz - H / 2), (W / 2 + 0.01, cz - H / 2), (W / 2 + 0.01, cz + H / 2), (-W / 2, cz + H / 2)], 0.016, bevel=0.3, y=sy * (T / 2 - 0.004))
    p.lathe("leather", [(T / 2 + 0.004, -H / 2), (T / 2 + 0.004, H / 2)], segs=8, loc=(-W / 2, 0, cz))   # the rounded spine
    for dz in (-0.24, -0.08, 0.08, 0.24):
        p.lathe("leather_dark", [(T / 2 + 0.012, -0.012), (T / 2 + 0.012, 0.012)], segs=8, loc=(-W / 2, 0, cz + dz))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (W / 2 - 0.035) + (0.01 if sx > 0 else 0.0), cz + sz * (H / 2 - 0.04)
            p.box("brass", (0.09, T + 0.012, 0.1), (x, 0, z))
    p.box("iron", (0.07, T + 0.014, 0.06), (W / 2 - 0.01, 0, cz))                           # the clasp
    p.box("brass", (0.03, T + 0.02, 0.03), (W / 2 + 0.005, 0, cz))
    p.lathe("brass", [(0.0, 0.0), (0.05, 0.004), (0.035, 0.016), (0.0, 0.02)], segs=8, loc=(0.0, -T / 2 - 0.004, cz), rot=(HPI, 0, 0))   # a boss on the face
    p.box("cloth_red", (0.02, 0.006, 0.16), (0.1, 0.0, cz - H / 2 - 0.06))                 # the ribbon
    p.box("leather_dark", (0.07, 0.02, 0.24), (0, T / 2 + 0.018, 0.02))                    # the strap behind
    p.box("leather_dark", (0.14, 0.018, 0.06), (0, T / 2 + 0.018, cz + 0.2))
    return p


# ======================================================================================
# Paired light weapons
# ======================================================================================

def needle(p):
    """An examiner's needle: long, steel, a ring pommel to spin it on a finger."""
    p.torus("steel", 0.036, 0.008, (0, 0, -0.165), rot=(HPI, 0, 0), segs=10, rings=4)
    grip(p, -0.125, 0.03, r=0.016, mat="cloth_red", band="leather_dark", wraps=5, segs=6, swell=0.2)
    ferrule(p, 0.03, r=0.016, h=0.02)
    p.lathe("steel", [(0.016, 0.05), (0.012, 0.09), (0.008, 0.4), (0.0, 0.62)], segs=6)
    p.lathe("steel_edge", [(0.0085, 0.4), (0.0, 0.62)], segs=6)
    return p


def pen_knife(p):
    """A scribe's pen-knife: dark wood scales pinned to a tang, brass bolsters, a short keen blade."""
    for sy in (-1, 1):
        p.slab("dark_wood", [(-0.016, -0.16), (0.02, -0.165), (0.024, -0.02), (-0.018, -0.02)], 0.012, bevel=0.35, y=sy * 0.01)
    p.box("steel", (0.036, 0.008, 0.15), (0.002, 0, -0.09))
    for z in (-0.13, -0.085, -0.04):
        p.cone("brass", 0.005, 0.005, 0.034, (0.002, 0.017, z), rot=(HPI, 0, 0), segs=5)
    p.slab("brass", [(-0.02, -0.02), (0.026, -0.02), (0.024, 0.01), (-0.018, 0.01)], 0.034, bevel=0.3)
    p.slab("brass", [(-0.018, -0.185), (0.022, -0.19), (0.02, -0.16), (-0.016, -0.16)], 0.032, bevel=0.3)
    p.edge_blade(0.01, 0.27, 0.036, 0.006, kind="saber", tip=0.09, taper=0.9, fuller=None, x0=0.004)
    return p


def compass_dividers(p):
    """Brass dividers held like a dagger: the hinge in the fist, the steel points out."""
    p.lathe("brass", [(0.0, -0.03), (0.032, -0.022), (0.032, 0.022), (0.0, 0.03)], segs=8, loc=(0, 0, -0.06), rot=(HPI, 0, 0))
    p.cone("steel", 0.01, 0.01, 0.07, (0, 0.035, -0.06), rot=(HPI, 0, 0), segs=6)
    p.lathe("brass", [(0.014, -0.16), (0.02, -0.14), (0.014, -0.1)], segs=6)
    p.sphere("brass", 0.018, (0, 0, -0.17), sub=1)
    for sx in (-1, 1):
        p.slab("brass", [(sx * 0.008, -0.05), (sx * 0.03, -0.05), (sx * 0.1, 0.3), (sx * 0.085, 0.33), (sx * 0.07, 0.3)][::sx], 0.02, bevel=0.3)
        p.lathe("brass_dark", [(0.016, 0.0), (0.016, 0.03)], segs=6, loc=(sx * 0.09, 0, 0.31), rot=(0, sx * 0.21, 0))
        p.lathe("steel_edge", [(0.011, 0.0), (0.0, 0.24)], segs=5, loc=(sx * 0.094, 0, 0.33), rot=(0, sx * 0.21, 0))
    p.torus("brass_dark", 0.2, 0.005, (0, 0, -0.06), rot=(HPI, 0, 0), segs=10, rings=3, sweep=0.62, start=HPI - 0.31)
    p.sphere("iron", 0.012, (0.062, 0, 0.13), sub=0)
    return p


def fist_wrap(p):
    """A fighter's wrapped fist: cloth wound round the hand in two tones, a brass plate with
    studs over the knuckles (+X), a bar across the palm inside, a laced cuff at the wrist (-X)."""
    n = 6
    prof = [(0.058 + (0.004 if i % 2 else 0.0), -0.078 + 0.156 * i / n) for i in range(n + 1)]
    p.lathe(["cloth" if i % 2 == 0 else "paper" for i in range(n)], prof, segs=10)
    p.slab("brass", [(0.05, -0.08), (0.08, -0.066), (0.088, 0.0), (0.08, 0.066), (0.05, 0.08)], 0.1, bevel=0.25)
    for z in (-0.054, -0.018, 0.018, 0.054):
        p.lathe("brass_dark", [(0.015, 0.0), (0.011, 0.016), (0.0, 0.03)], segs=6, loc=(0.084, 0, z), rot=(0, HPI, 0))
    p.lathe(["leather_dark", "leather", "leather_dark"], [(0.05, 0.0), (0.054, 0.03), (0.05, 0.1), (0.046, 0.13)], segs=10, loc=(-0.05, 0, 0), rot=(0, -HPI, 0))
    for k in range(3):
        p.box("paper", (0.012, 0.01, 0.05), (-0.085 - k * 0.03, -0.052, 0.0), rot=(0.5 if k % 2 else -0.5, 0, 0))
    return p


# ======================================================================================
# Pole weapons (long along Z, the hand at the origin)
# ======================================================================================

def pilum(p):
    """A legion throwing spear: a wooden shaft, a pyramid block, a long thin iron shank and a small head."""
    haft(p, -0.75, 0.72, bands=(0.0,))
    p.lathe("iron", [(HAFT_R * 1.5, 0.7), (HAFT_R * 1.9, 0.72), (HAFT_R * 1.9, 0.8), (0.016, 0.9)], segs=4)
    p.rod("steel_dark", 0.011, 0.9, 1.55, segs=6)
    p.edge_blade(1.53, 0.2, 0.026, 0.012, kind="sword", tip=0.12, taper=0.9, fuller=None, flare=0.25)
    return p


def lance(p):
    """A rider's lance: a tapering shaft, a steel vamplate before the hand, a leaf head and a pennon."""
    p.rod("wood", 0.032, -0.6, 1.5, r2=0.016, segs=8)
    p.lathe("brass", [(0.0, -0.64), (0.03, -0.62), (0.038, -0.59), (0.032, -0.56)], segs=8)
    grip(p, -0.14, 0.14, r=0.034, wraps=5)
    p.lathe(["steel", "steel_edge", "steel"], [(0.04, 0.16), (0.15, 0.3), (0.158, 0.31), (0.04, 0.2)], segs=12)
    socket(p, 1.44, r=0.018, h=0.1)
    p.edge_blade(1.52, 0.3, 0.036, 0.012, kind="sword", tip=0.18, taper=0.9, fuller=None, flare=0.2)
    p.prism("cloth_red", [(0.02, 1.2), (0.34, 1.26), (0.2, 1.31), (0.36, 1.37), (0.02, 1.42)], 0.006)
    return p


def naginata(p):
    """A curved single-edged blade on a long dark haft: a brass collar, a small guard, bindings."""
    haft(p, -0.9, 0.9, mat="dark_wood", butt="brass", bands=(-0.3, 0.3, 0.7))
    ferrule(p, 0.86, r=HAFT_R, h=0.08)
    p.lathe("iron", [(0.026, 0.945), (0.05, 0.95), (0.05, 0.962), (0.026, 0.966)], segs=8)
    p.edge_blade(0.966, 0.66, 0.066, 0.011, kind="saber", curve=0.12, tip=0.2, taper=0.95, fuller=(0.05, 0.5), x0=0.006)
    return p


def harpoon(p):
    """A river harpoon: a barbed head on an iron shank, the line run to a coil at the butt."""
    haft(p, -0.9, 0.82, butt="brass", bands=(0.0, 0.4))
    socket(p, 0.8, h=0.1, top=0.014, mat="iron")
    p.rod("iron", 0.013, 0.9, 1.16, segs=6)
    p.edge_blade(1.14, 0.3, 0.034, 0.012, kind="sword", tip=0.2, taper=1.0, fuller=None)
    for sx in (-1, 1):
        p.prism("steel", [(sx * 0.03, 1.2), (sx * 0.1, 1.04), (sx * 0.02, 1.1)][::sx], 0.01)
    p.torus("iron", 0.02, 0.005, (0.03, 0, 0.84), rot=(HPI, 0, 0), segs=6, rings=3)
    p.tube("paper", [(0.035, 0, 0.82), (0.04, 0.01, 0.3), (0.035, 0, -0.3), (0.05, 0, -0.7)], 0.006, segs=4)
    coil(p, 0.055, 0.009, (0, 0, -0.84), loops=4, pitch=0.022, mat="paper")
    return p


def boat_hook(p):
    """A pilot's boat-hook: a spike and a curled hook on a long ash pole."""
    haft(p, -0.9, 0.9, bands=(0.0,), spike=False)
    socket(p, 0.86, h=0.1, top=0.016, mat="iron", langets=0.14)
    p.lathe("iron", [(0.016, 0.96), (0.0, 1.22)], segs=6)
    pts = [(0.0, 0, 0.93), (0.07, 0, 1.03), (0.16, 0, 1.06), (0.23, 0, 1.0), (0.24, 0, 0.9), (0.19, 0, 0.84), (0.14, 0, 0.86)]
    p.tube("iron", pts, [0.02, 0.019, 0.017, 0.015, 0.012, 0.009, 0.0], segs=5)
    return p


def grapple_hook(p):
    """An aeronaut's grapple: three curled tines on a short haft, the line coiled about it."""
    haft(p, -0.3, 0.34, mat="dark_wood", butt="brass", spike=False)
    socket(p, 0.3, h=0.1, top=0.02, mat="iron")
    p.sphere("iron", 0.03, (0, 0, 0.42), sub=1)
    for i in range(3):
        a = i * 2 * math.pi / 3 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((0, 0, 0.42))
        pts = [base, base + d * 0.03 + Vector((0, 0, 0.12)), base + d * 0.13 + Vector((0, 0, 0.2)), base + d * 0.24 + Vector((0, 0, 0.14)), base + d * 0.27 + Vector((0, 0, 0.02))]
        p.tube("iron", pts, [0.016, 0.015, 0.013, 0.01, 0.0], segs=5)
    p.torus("iron", 0.026, 0.006, (0, 0, -0.33), rot=(HPI, 0, 0), segs=8, rings=3)
    coil(p, 0.05, 0.01, (0, 0, -0.2), loops=6, pitch=0.021, mat="paper")
    p.tube("paper", [(0.05, 0, -0.2), (0.09, 0.02, -0.34), (0.02, 0, -0.36)], 0.007, segs=4)
    return p


def whip(p):
    """A stock whip: a plaited stock with a brass cap, the lash in a loose coil, a cracker at its end."""
    grip(p, -0.22, 0.2, r=0.022, mat="leather", band="leather_dark", wraps=8, segs=7, swell=0.08)
    pommel(p, -0.22, 0.03, style="cap")
    p.torus("leather_dark", 0.04, 0.006, (0, 0, -0.27), rot=(0, HPI, 0), segs=8, rings=3)
    pts = []
    for i in range(34):
        t = i / 33.0
        a = t * 2 * math.pi * 2.6
        R = 0.2 - 0.05 * t
        pts.append((0.1 + math.cos(a + 2.2) * R + 0.02, (t - 0.5) * 0.08, 0.34 + math.sin(a + 2.2) * R))
    pts = [(0, 0, 0.2), (0.02, -0.03, 0.3)] + pts
    p.tube("leather", pts, [0.016 * (1 - 0.75 * i / (len(pts) - 1)) for i in range(len(pts))], segs=5)
    p.tube("cloth_red", [pts[-1], (pts[-1][0] + 0.05, pts[-1][1], pts[-1][2] - 0.12)], [0.004, 0.0], segs=3)
    return p


def staff(p):
    """A walker's staff: ash, shod with iron, a cord grip, a knot of the wood at its head."""
    haft(p, -0.95, 0.9, r=0.025, bands=(), spike=False)
    grip(p, -0.12, 0.12, r=0.028, mat="cloth", band="leather_dark", wraps=5, segs=7, swell=0.05)
    p.lathe("wood", [(0.025, 0.9), (0.04, 0.95), (0.05, 1.0), (0.04, 1.06), (0.0, 1.09)], segs=7)
    p.torus("brass", 0.03, 0.008, (0, 0, 0.9), segs=8, rings=3)
    return p


def oar_staff(p):
    """A river pilot's oar-staff: a pole whose head is a narrow blade of an oar, bound in brass."""
    haft(p, -0.95, 0.75, r=0.025, bands=(0.35,), spike=False)
    grip(p, -0.12, 0.12, r=0.028, wraps=5, segs=7, swell=0.05)
    p.slab("wood", [(-0.025, 0.74), (0.025, 0.74), (0.07, 0.92), (0.075, 1.3), (0.05, 1.42), (-0.05, 1.42), (-0.075, 1.3), (-0.07, 0.92)], 0.03, bevel=0.35)
    p.slab("brass", [(-0.055, 1.38), (0.055, 1.38), (0.05, 1.43), (-0.05, 1.43)], 0.036, bevel=0.2)
    p.box("dark_wood", (0.012, 0.034, 0.5), (0, 0, 1.1))
    return p


def ward_staff(p):
    """A grower's staff with a seed-pod head: the husk split in three, the bright seed showing, dry leaves."""
    haft(p, -0.9, 0.98, mat="dark_wood", butt="brass", bands=(0.0,), spike=False)
    p.lathe("dark_wood", [(HAFT_R, 0.96), (0.04, 1.0), (0.05, 1.04)], segs=7)
    for i in range(3):
        a = i * 2 * math.pi / 3
        pts = [(math.cos(a) * 0.04, math.sin(a) * 0.04, 1.03), (math.cos(a) * 0.14, math.sin(a) * 0.14, 1.16), (math.cos(a) * 0.13, math.sin(a) * 0.13, 1.3), (math.cos(a) * 0.03, math.sin(a) * 0.03, 1.44)]
        p.tube("dark_wood", pts, [0.035, 0.07, 0.06, 0.0], segs=5)
    p.lathe("field_glow", [(0.0, 1.1), (0.05, 1.16), (0.06, 1.24), (0.04, 1.32), (0.0, 1.37)], segs=7)
    for a in (1.05, 3.14, 5.24):
        p.prism("bone", [(0.03, 1.0), (0.26, 1.02), (0.3, 1.1), (0.1, 1.12)], 0.008, rot=(0, 0, a))
    return p


def brush_staff(p):
    """An examiner's staff tipped with a great brush: a brass ferrule, pale bristles, the tip ink-dark."""
    haft(p, -0.9, 0.9, butt="brass", bands=(0.0,), spike=False)
    p.lathe(["brass", "brass_dark", "brass"], [(HAFT_R * 1.1, 0.88), (0.045, 0.92), (0.05, 1.0), (0.058, 1.04)], segs=8)
    p.lathe(["bone", "bone", "iron"], [(0.056, 1.04), (0.075, 1.16), (0.05, 1.32), (0.0, 1.5)], segs=8)
    p.torus("cloth_red", 0.03, 0.007, (0, 0, 0.86), segs=8, rings=3)
    p.tube("cloth_red", [(0.03, 0, 0.86), (0.05, 0, 0.74), (0.04, 0.01, 0.66)], [0.006, 0.006, 0.012], segs=4)
    return p


def lantern_staff(p):
    """A staff with a brass lantern hung from a crook at its head, the flame lit behind glass."""
    haft(p, -0.9, 1.06, mat="dark_wood", bands=(0.0,))
    socket(p, 1.0, h=0.08, top=0.016, mat="iron")
    p.tube("iron", [(0, 0, 1.06), (0.02, 0, 1.2), (0.12, 0, 1.27), (0.22, 0, 1.22), (0.24, 0, 1.12)], [0.014, 0.013, 0.012, 0.011, 0.009], segs=5)
    for i in range(2):
        p.torus("iron", 0.016, 0.004, (0.24, 0, 1.09 - i * 0.028), rot=(HPI if i % 2 else 0, 0, 0), segs=6, rings=3)
    lx, lz = 0.24, 0.9
    p.lathe("field_glow", [(0.04, lz - 0.08), (0.05, lz), (0.04, lz + 0.08)], segs=6, loc=(lx, 0, 0))
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        p.box("brass", (0.01, 0.01, 0.17), (lx + math.cos(a) * 0.056, math.sin(a) * 0.056, lz))
    p.lathe("brass", [(0.03, lz - 0.115), (0.066, lz - 0.1), (0.066, lz - 0.082), (0.05, lz - 0.08)], segs=6, loc=(lx, 0, 0))
    p.lathe("brass", [(0.066, lz + 0.08), (0.07, lz + 0.09), (0.03, lz + 0.14), (0.012, lz + 0.15), (0.012, lz + 0.165)], segs=6, loc=(lx, 0, 0))
    return p


# ======================================================================================
# Heavy
# ======================================================================================

def maul(p):
    """A long-hafted war hammer: a faceted iron head banded in brass, a bright face on the
    knuckle side, a beak behind, langets down the haft."""
    haft(p, -0.6, 0.96, r=0.027, mat="dark_wood", bands=(-0.3,))
    grip(p, -0.16, 0.16, r=0.03, wraps=6)
    for sy in (-1, 1):
        p.box("iron", (0.03, 0.007, 0.34), (0, sy * 0.03, 0.66))
    hz = 0.9
    prof = [(0.06, -0.19), (0.085, -0.17), (0.085, -0.05), (0.07, -0.03), (0.07, 0.03), (0.085, 0.05), (0.085, 0.16), (0.092, 0.175), (0.092, 0.2)]
    p.lathe(["steel_edge", "iron", "brass", "iron", "brass", "iron", "steel", "steel_edge"], prof, segs=8, loc=(0, 0, hz), rot=(0, HPI, 0))
    p.lathe("steel", [(0.05, 0.0), (0.03, 0.08), (0.0, 0.2)], segs=4, loc=(-0.19, 0, hz), rot=(0, -HPI, 0))
    p.lathe("iron", [(0.03, 0.0), (0.034, 0.05), (0.0, 0.12)], segs=6, loc=(0, 0, hz + 0.08))
    return p


def engine_arm(p):
    """An engineer's piston arm: a brass cylinder banded in iron drives a hammer head; a gauge
    with the field's light, vents, a pressure flask at the back; the hand in a bracket."""
    grip(p, -0.11, 0.11, r=0.028, mat="leather_dark", band="leather", wraps=4)
    p.slab("iron", [(-0.05, -0.17), (0.05, -0.17), (0.05, -0.13), (-0.02, -0.13), (-0.02, 0.13), (0.05, 0.13), (0.05, 0.17), (-0.05, 0.17)], 0.05, bevel=0.2, y=0.045)
    p.lathe(["iron", "brass", "iron", "brass", "iron"], [(0.066, 0.17), (0.066, 0.2), (0.06, 0.21), (0.06, 0.36), (0.066, 0.37), (0.066, 0.4), (0.06, 0.41), (0.06, 0.52), (0.068, 0.53), (0.068, 0.57)][::1], segs=10)
    p.rod("steel_edge", 0.022, 0.57, 0.74, segs=8)
    for sx in (-1, 1):
        p.rod("steel", 0.01, 0.17, 0.72, x=sx * 0.085, segs=5)
        p.sphere("brass", 0.016, (sx * 0.085, 0, 0.72), sub=0)
    hz = 0.82
    p.lathe(["steel_edge", "iron", "brass", "iron"], [(0.062, -0.2), (0.085, -0.18), (0.085, 0.05), (0.07, 0.07), (0.07, 0.15), (0.05, 0.17)], segs=8, loc=(0, 0, hz), rot=(0, -HPI, 0))
    p.lathe("brass", [(0.03, 0.0), (0.036, 0.008), (0.036, 0.02), (0.0, 0.024)], segs=8, loc=(0.062, 0, 0.3), rot=(0, HPI, 0))
    p.cone("field_glow", 0.026, 0.026, 0.006, (0.086, 0, 0.3), rot=(0, HPI, 0), segs=8)
    for sy in (-1, 1):
        p.lathe("brass_dark", [(0.016, 0.0), (0.022, 0.07), (0.016, 0.08)], segs=6, loc=(-0.02, sy * 0.06, 0.46), rot=(sy * -HPI, 0, 0))
    p.lathe("brass", [(0.0, -0.42), (0.04, -0.4), (0.05, -0.33), (0.04, -0.24), (0.02, -0.2), (0.02, -0.17)], segs=8)
    p.tube("brass_dark", [(0.0, 0.03, -0.3), (0.0, 0.1, -0.2), (0.0, 0.1, 0.1), (0.0, 0.06, 0.2)], 0.01, segs=4)
    return p


# ======================================================================================
# Ranged (barrels along -Y here, +Z in the game, like KayKit's crossbow)
# ======================================================================================

def pistol(p):
    """A Columbia service pistol: a flintlock in walnut, a blued barrel with a brass band and cap."""
    pistol_grip(p, drop=0.24, rake=0.5, mat="wood")
    stock(p, [(0.1, 0.03), (0.11, 0.09), (0.02, 0.105), (-0.28, 0.085), (-0.29, 0.05), (-0.1, 0.035), (-0.02, 0.0), (0.05, -0.02)], 0.056, mat="wood")
    barrel(p, 0.09, 0.47, 0.021, 0.115, breech=0.28)
    band(p, -0.2, 0.1, 0.033)
    p.lathe("brass", [(0.03, 0.0), (0.034, 0.02), (0.02, 0.035)], segs=8, loc=(0, -0.265, 0.07), rot=(HPI, 0, 0))
    flintlock(p, y=0.03, z=0.085)
    trigger(p, y=0.0, z=0.02)
    ramrod(p, -0.02, 0.32, 0.05)
    p.box("brass", (0.01, 0.014, 0.014), (0, -0.35, 0.142))
    return p


def air_pistol(p):
    """A Lunden dock-yard air pistol: a brass air flask under a slim barrel, a valve wheel, a gauge."""
    pistol_grip(p, drop=0.22, rake=0.38, mat="leather_dark", cap="steel")
    stock(p, [(0.09, 0.03), (0.09, 0.1), (-0.08, 0.1), (-0.1, 0.06), (-0.03, 0.0), (0.04, -0.015)], 0.052, mat="steel")
    barrel(p, 0.08, 0.6, 0.015, 0.125, mat="steel", breech=0.18, swell=1.5)
    p.lathe(["brass", "brass", "brass_dark", "brass"], [(0.0, 0.0), (0.034, 0.02), (0.04, 0.08), (0.04, 0.26), (0.03, 0.3), (0.016, 0.31)], segs=10, loc=(0, -0.1, 0.07), rot=(-HPI, 0, 0))
    for y in (-0.2, -0.32):
        p.box("steel", (0.02, 0.014, 0.07), (0, y, 0.098))
    p.torus("brass", 0.028, 0.006, (0, 0.105, 0.085), rot=(HPI, 0, 0), segs=8, rings=3)
    for a in (0.0, HPI):
        p.box("brass", (0.056, 0.008, 0.008), (0, 0.105, 0.085), rot=(0, a, 0))
    p.lathe("brass", [(0.022, 0.0), (0.026, 0.006), (0.026, 0.016), (0.0, 0.02)], segs=8, loc=(0.026, 0.0, 0.07), rot=(0, HPI, 0))
    p.cone("field_glow", 0.018, 0.018, 0.005, (0.046, 0.0, 0.07), rot=(0, HPI, 0), segs=8)
    trigger(p, y=0.0, z=0.02, mat="steel")
    return p


def musket(p):
    """A long Columbia musket: a full walnut stock with a comb and a brass butt-plate, three
    bands, the lock at the wrist, a ramrod under the barrel."""
    stock(p, [(0.5, -0.2), (0.52, -0.02), (0.3, 0.05), (0.16, 0.075), (0.06, 0.1), (-1.06, 0.085), (-1.08, 0.045), (-0.16, 0.03), (-0.03, -0.01), (0.1, -0.04), (0.26, -0.12)], 0.06, mat="wood")
    p.slab("brass", [(0.515, -0.21), (0.535, -0.015), (0.505, -0.02), (0.49, -0.2)], 0.066, bevel=0.2, rot=(0, 0, HPI))
    barrel(p, 0.12, 1.42, 0.02, 0.112, breech=0.22)
    for y in (-0.36, -0.7, -1.02):
        band(p, y, 0.095, 0.036)
    ramrod(p, -0.2, 1.05, 0.045)
    flintlock(p, y=0.04, z=0.08)
    trigger(p, y=-0.02, z=0.0, size=1.15)
    p.box("brass", (0.008, 0.014, 0.016), (0, -1.24, 0.138))
    p.tube("leather", [(0.012, -0.98, 0.035), (0.03, -0.5, -0.06), (0.012, 0.3, -0.1)], 0.01, segs=4)    # the sling
    return p


def bolt_thrower(p):
    """An engineer's heavy crossbow: an iron tiller, a steel prod across the front, the string
    drawn to the nut, a bolt in the groove, a brass magazine and a cocking lever."""
    stock(p, [(0.5, -0.2), (0.52, -0.03), (0.28, 0.04), (0.06, 0.09), (-0.95, 0.09), (-0.97, 0.03), (-0.2, 0.02), (-0.03, -0.01), (0.1, -0.04), (0.26, -0.12)], 0.064, mat="dark_wood")
    p.slab("iron", [(0.515, -0.21), (0.535, -0.025), (0.505, -0.03), (0.49, -0.2)], 0.07, bevel=0.2, rot=(0, 0, HPI))
    p.box("steel_dark", (0.03, 0.98, 0.012), (0, -0.45, 0.096))
    p.box("iron", (0.1, 0.07, 0.07), (0, -0.92, 0.07))
    for sx in (-1, 1):
        p.tube("steel", [(sx * 0.04, -0.93, 0.075), (sx * 0.26, -0.9, 0.075), (sx * 0.44, -0.8, 0.075), (sx * 0.52, -0.68, 0.075)], [0.022, 0.018, 0.013, 0.009], segs=5)
        p.tube("paper", [(sx * 0.52, -0.68, 0.075), (0.0, -0.2, 0.1)], 0.005, segs=3)
    p.lathe("brass", [(0.022, -0.02), (0.022, 0.02)], segs=8, loc=(0, -0.2, 0.1), rot=(0, HPI, 0))           # the nut
    p.cone("wood", 0.008, 0.008, 0.6, (0, -0.22, 0.108), rot=(HPI, 0, 0), segs=5)                              # the bolt
    p.lathe("steel_edge", [(0.014, 0.0), (0.0, 0.07)], segs=4, loc=(0, -0.82, 0.108), rot=(HPI, 0, 0))
    p.cone("field_glow", 0.012, 0.012, 0.012, (0, -0.815, 0.108), rot=(HPI, 0, 0), segs=6)
    p.slab("brass", [(-0.16, 0.0), (0.16, 0.0), (0.14, 0.1), (-0.14, 0.1)], 0.07, bevel=0.2, rot=(0, 0, HPI), loc=(0, -0.42, 0.115))
    p.tube("iron", [(0, 0.06, -0.03), (0, -0.2, -0.09), (0, -0.4, -0.08)], 0.01, segs=5)
    p.sphere("brass", 0.02, (0, -0.4, -0.08), sub=0)
    p.tube("iron", [(0, -0.93, 0.03), (0, -1.0, -0.02), (0, -0.93, -0.07), (0, -0.87, -0.02), (0, -0.92, 0.03)], 0.008, segs=4)   # the stirrup
    trigger(p, y=-0.02, z=0.0, mat="iron", size=1.1)
    return p


def seed_sling(p):
    """A short seed-sling gun: a flared brass muzzle, a seed hopper on top, a stubby walnut stock."""
    pistol_grip(p, drop=0.22, rake=0.55, mat="wood")
    stock(p, [(0.14, 0.02), (0.15, 0.1), (-0.2, 0.09), (-0.22, 0.045), (-0.04, 0.0), (0.06, -0.02)], 0.062, mat="wood")
    p.lathe(["steel_dark", "brass_dark", "brass", "brass", "brass_dark"], [(0.036, 0.0), (0.036, 0.16), (0.03, 0.18), (0.04, 0.34), (0.085, 0.5), (0.095, 0.52), (0.09, 0.53)], segs=10, loc=(0, 0.1, 0.12), rot=(HPI, 0, 0))
    p.cone("field_glow", 0.07, 0.05, 0.02, (0, -0.4, 0.12), rot=(HPI, 0, 0), segs=10)
    p.lathe(["brass", "brass_dark", "brass"], [(0.03, 0.0), (0.05, 0.03), (0.055, 0.09), (0.03, 0.11), (0.0, 0.115)], segs=8, loc=(0, -0.02, 0.15))
    flintlock(p, y=0.05, z=0.09, x=0.038)
    trigger(p, y=0.0, z=0.01)
    return p


def bow_short(p):
    """A rider's recurve: short and stout, horn on the belly, the tips curled forward."""
    bow(p, [(-0.07, 0.3), (-0.1, 0.5), (-0.04, 0.66), (0.06, 0.76)], string_y=-0.005, width=0.04, thick=0.018, mat="dark_wood", grip_len=0.18, belly="bone")
    return p


def bow_long(p):
    """A tall bow: a single stave near the height of its archer, leather at the grip, horn nocks."""
    bow(p, [(-0.03, 0.4), (-0.05, 0.8), (-0.02, 1.08)], string_y=0.1, width=0.03, thick=0.022, mat="wood", grip_len=0.22)
    return p


def astrolabe(p):
    """A brass astrolabe held like a bow: the ring stands in the bow's plane, its rim through
    the fist and the rest of it out in front, a pierced rete and a sighting arm across it;
    the inner ring glows."""
    R = 0.4
    cy = -R
    p.torus("brass", R, 0.024, (0, cy, 0), rot=(0, HPI, 0), segs=20, rings=5)
    for k in range(12):
        a = 2 * math.pi * k / 12
        p.box("brass_dark", (0.05, 0.012, 0.012), (0, cy + math.cos(a) * R, math.sin(a) * R), rot=(-a, 0, 0))
    p.torus("field_glow", R - 0.045, 0.01, (0, cy, 0), rot=(0, HPI, 0), segs=20, rings=4)
    p.torus("brass", 0.21, 0.01, (0.0, cy + 0.05, 0.04), rot=(0, HPI, 0), segs=14, rings=4)
    p.torus("brass_dark", 0.12, 0.008, (0.0, cy - 0.08, -0.06), rot=(0, HPI, 0), segs=12, rings=4)
    for a in (0.4, 1.9, 3.5, 5.0):
        p.tube("brass", [(0, cy, 0), (0, cy + math.cos(a) * (R - 0.05), math.sin(a) * (R - 0.05))], [0.008, 0.005], segs=4)
    p.tube("steel", [(0.014, cy - 0.33, -0.2), (0.014, cy + 0.33, 0.2)], 0.008, segs=4)
    for s_ in (-1, 1):
        p.box("steel", (0.03, 0.02, 0.05), (0.014, cy + s_ * 0.3, s_ * 0.18), rot=(-0.55, 0, 0))
    p.lathe("brass_dark", [(0.0, -0.02), (0.03, -0.012), (0.03, 0.012), (0.0, 0.02)], segs=8, loc=(0, cy, 0), rot=(0, HPI, 0))
    grip(p, -0.09, 0.09, r=0.03, wraps=3)
    p.torus("brass", 0.035, 0.007, (0, cy, R + 0.05), rot=(0, HPI, 0), segs=8, rings=3)
    return p


def chakram(p):
    """A thrown steel ring: a flat band ground to a bright edge all round, a wrapped grip
    where the hand holds it."""
    R, Ri = 0.3, 0.235
    rings = []
    n = 24
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((0, 0, R))
        rings.append([c + d * Ri + Vector((0, 0.008, 0)), c + d * (R - 0.025) + Vector((0, 0.009, 0)), c + d * R, c + d * (R - 0.025) - Vector((0, 0.009, 0)), c + d * Ri - Vector((0, 0.008, 0))])
    p.strip_loft(rings, ["steel", "steel_edge", "steel_edge", "steel", "steel_dark"], closed=True)
    grip(p, -0.07, 0.07, r=0.02, mat="cloth_red", band="leather_dark", wraps=4, segs=6, swell=0.05)
    return p


# ======================================================================================
# Shields (carried on the off hand: the face out of the back of the hand, -Y here, +Z in the game)
# ======================================================================================

def _shield_fittings(p, y):
    """The grip and the arm strap behind a shield at depth y."""
    p.tube("leather_dark", [(0.0, y - 0.02, -0.1), (0.0, y - 0.07, -0.05), (0.0, y - 0.07, 0.05), (0.0, y - 0.02, 0.1)], 0.014, segs=5)


def shield_round(p):
    """A marshal's round shield: planks under a painted face, an iron rim, a brass boss, rivets."""
    R = 0.42
    yf = 0.07
    n = 16
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        mat = "wood" if k % 2 == 0 else "dark_wood"
        rings = [[Vector((0, yf - 0.02, 0)), Vector((math.cos(a0) * R, yf - 0.035, math.sin(a0) * R)), Vector((math.cos(a1) * R, yf - 0.035, math.sin(a1) * R))],
                 [Vector((0, yf + 0.03, 0)), Vector((math.cos(a0) * R, yf, math.sin(a0) * R)), Vector((math.cos(a1) * R, yf, math.sin(a1) * R))]]
        p.loft(mat, rings)
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        quarter = "cloth_red" if (k // 4) % 2 == 0 else "paper"
        p.loft(quarter, [[Vector((0, yf + 0.034, 0)), Vector((math.cos(a0) * (R - 0.03), yf + 0.006, math.sin(a0) * (R - 0.03))), Vector((math.cos(a1) * (R - 0.03), yf + 0.006, math.sin(a1) * (R - 0.03)))],
                         [Vector((0, yf + 0.036, 0)), Vector((math.cos(a0) * (R - 0.03), yf + 0.008, math.sin(a0) * (R - 0.03))), Vector((math.cos(a1) * (R - 0.03), yf + 0.008, math.sin(a1) * (R - 0.03)))]])
    p.torus("iron", R, 0.022, (0, yf - 0.015, 0), rot=(HPI, 0, 0), segs=20, rings=5)
    p.lathe(["brass_dark", "brass", "brass"], [(0.11, 0.0), (0.1, 0.02), (0.06, 0.07), (0.0, 0.09)], segs=10, loc=(0, yf + 0.025, 0), rot=(-HPI, 0, 0))
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        p.sphere("brass", 0.014, (math.cos(a) * (R - 0.07), yf + 0.012, math.sin(a) * (R - 0.07)), sub=0)
    _shield_fittings(p, yf - 0.02)
    return p


def shield_badge(p):
    """A marshal's badge shield: a heater of iron-bound oak with the star of the office in brass."""
    yf = 0.07
    out = [(-0.3, 0.38), (0.3, 0.38), (0.31, 0.05), (0.22, -0.25), (0.0, -0.5), (-0.22, -0.25), (-0.31, 0.05)]
    p.slab("dark_wood", out, 0.045, bevel=0.2, y=yf)
    inner = [(x * 0.86, z * 0.86 - 0.01) for x, z in out]
    p.slab("leather", inner, 0.01, bevel=0.1, y=yf + 0.026)
    rim = out + [out[0]]
    p.tube("iron", [(x, yf + 0.012, z) for x, z in rim], 0.016, segs=4)
    star = []
    for k in range(10):
        a = math.pi / 2 + 2 * math.pi * k / 10
        r = 0.15 if k % 2 == 0 else 0.062
        star.append((math.cos(a) * r, 0.02 + math.sin(a) * r))
    p.slab("brass", star, 0.02, bevel=0.3, y=yf + 0.04)
    p.lathe("brass_dark", [(0.03, 0.0), (0.02, 0.014), (0.0, 0.02)], segs=8, loc=(0, yf + 0.048, 0.02), rot=(-HPI, 0, 0))
    for x, z in ((-0.24, 0.32), (0.24, 0.32), (-0.2, -0.18), (0.2, -0.18)):
        p.sphere("iron", 0.014, (x, yf + 0.034, z), sub=0)
    _shield_fittings(p, yf - 0.02)
    return p


def _mirror_y(fn):
    """The shields are drawn with the face toward +Y; the hand wants it toward -Y."""
    def build_it(p):
        fn(p)
        bmesh.ops.scale(p.bm, vec=(1, -1, 1), verts=p.bm.verts[:])
        bmesh.ops.reverse_faces(p.bm, faces=p.bm.faces[:])
        return p
    build_it.__doc__ = fn.__doc__
    return build_it


shield_round = _mirror_y(shield_round)
shield_badge = _mirror_y(shield_badge)


# ======================================================================================
# The catalogue
# ======================================================================================

BLADES = {"cutlass": cutlass, "rapier": rapier, "gladius": gladius, "glass_blade": glass_blade, "katana": katana,
          "war_fan": war_fan, "sickle": sickle, "ledger_book": ledger_book}
PAIRED = {"needle": needle, "pen_knife": pen_knife, "compass_dividers": compass_dividers, "fist_wrap": fist_wrap}
POLES = {"pilum": pilum, "lance": lance, "naginata": naginata, "harpoon": harpoon, "boat_hook": boat_hook,
         "grapple_hook": grapple_hook, "whip": whip, "staff": staff, "oar_staff": oar_staff, "ward_staff": ward_staff,
         "brush_staff": brush_staff, "lantern_staff": lantern_staff}
HEAVY = {"maul": maul, "engine_arm": engine_arm}
RANGED = {"pistol": pistol, "air_pistol": air_pistol, "musket": musket, "bolt_thrower": bolt_thrower, "seed_sling": seed_sling,
          "bow_short": bow_short, "bow_long": bow_long, "astrolabe": astrolabe, "chakram": chakram}
SHIELDS = {"shield_round": shield_round, "shield_badge": shield_badge}
WEAPONS = {}
for group in (BLADES, PAIRED, POLES, HEAVY, RANGED, SHIELDS):
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
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.034, 0.05, 1)
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


def render_card(name, objects, path, size_px=(400, 320)):
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
    ground.data.materials.append(material("sheet_ground", (0.07, 0.068, 0.07, 1), 0.95))
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 42
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = centre + Vector((size * 0.25, -size * 1.05, size * 0.75))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    label(name, cam, k=max(0.3, size * 0.55))
    # a clear key from above the camera, a warm lamp low at the front, a cool rim: the forms read
    light("SUN", centre + Vector((-size * 0.4, -size * 1.0, size * 1.6)), centre, (1.0, 0.97, 0.92), 3.2)
    light("AREA", centre + Vector((size * 1.5, -size * 1.2, size * 0.4)), centre, (1.0, 0.62, 0.34), 30 * size * size, size)
    light("AREA", centre + Vector((-size * 1.2, size * 1.4, size * 0.9)), centre, (0.5, 0.62, 1.0), 40 * size * size, size)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def compose_sheet(cells, path, cell=(400, 320), cols=6):
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

HAND_BODY = "alexandria-m.glb"
HAND_CHECKS = [  # (label, right hand, left hand, animation, frame fraction)
    ("saber and shield (idle)", "cutlass", "shield_round", "Idle", 0.5),
    ("katana (2H idle)", "katana", None, "2H_Melee_Idle", 0.5),
    ("naginata (2H idle)", "naginata", None, "2H_Melee_Idle", 0.5),
    ("maul (chop)", "maul", None, "2H_Melee_Attack_Chop", 0.35),
    ("pistol (aiming)", "pistol", None, "1H_Ranged_Aiming", 0.6),
    ("musket (2H aiming)", "musket", None, "2H_Ranged_Aiming", 0.6),
    ("long bow (2H aiming)", "bow_long", None, "2H_Ranged_Aiming", 0.6),
    ("fists (idle)", "fist_wrap", "fist_wrap", "Unarmed_Idle", 0.5),
    ("ledger and pen-knife (idle)", "pen_knife", "ledger_book", "Idle", 0.5),
]


def render_hand(title, right, left, action, frac, path, size_px=(560, 640), close=False):
    """A person with the weapons hung from the hand slots exactly as the game hangs them: the
    slot's transform and the model's with no offset. Blender's importer converts a weapon's
    vertices to Z up but leaves the bone's axes as the glTF node's, so the hung object gets a
    -90 degree turn about X to put its Blender coordinates back on its glTF ones."""
    reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(PEOPLE, HAND_BODY), bone_heuristic="BLENDER")
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
    for o in bpy.data.objects:
        if o.type == "MESH" and (o.name.startswith(("Beard_", "Headgear_")) or (o.name.startswith("Hair_") and not o.name.startswith("Hair_crop"))):
            o.hide_render = True
    for model, slot in ((right, "handslot.r"), (left, "handslot.l")):
        if not model:
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, model + ".glb"))
        for o in bpy.data.objects:
            if o not in before and o.type == "MESH":
                o.matrix_basis = Matrix.Rotation(-HPI, 4, "X")
                c = o.constraints.new("CHILD_OF")
                c.target = arm
                c.subtarget = slot
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
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = size_px
    bpy.context.view_layer.update()
    hand = arm.matrix_world @ arm.pose.bones["handslot.r"].head
    centre = Vector(hand) if close else Vector((0, -0.2, 1.3))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    bpy.context.collection.objects.link(cam)
    cam.location = centre + (Vector((-0.75, -0.95, 0.35)) if close else Vector((-2.3, -3.6, 1.0)))   # front-right of the character, which faces -Y
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    label(title, cam, size=0.05, k=0.4 if close else 1.0)
    light("SUN", centre + Vector((-2, -3, 5)), centre, (1.0, 0.97, 0.92), 3.0)
    light("AREA", centre + Vector((3, -4, 1)), centre, (1.0, 0.62, 0.34), 500, 2.0)
    light("AREA", centre + Vector((-3, 3, 2)), centre, (0.5, 0.62, 1.0), 500, 2.0)
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(material("sheet_ground", (0.07, 0.068, 0.07, 1), 0.95))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_hands(path):
    cells = []
    for i, (title, right, left, action, frac) in enumerate(HAND_CHECKS):
        for close in (False, True):
            cell = os.path.join(os.path.dirname(path), "hand_cells", "%d%s.png" % (i, "c" if close else ""))
            os.makedirs(os.path.dirname(cell), exist_ok=True)
            render_hand(title, right, left, action, frac, cell, close=close)
            cells.append(cell)
    reset()
    compose_sheet(cells, path, cell=(560, 640), cols=6)


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
