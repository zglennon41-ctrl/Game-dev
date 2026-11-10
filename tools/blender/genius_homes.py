"""WILDLINE: the home's hand. What each of the thirteen homes puts on a genius raised there
(docs/genius-signature.md, "The home's hand"): a small piece hung at its collar or throat,
drawn from the home's own dress (data/bodies.json, dress), so a genius says where its partner
is from as well as what it is.

    python tools/blender/genius_homes.py            # every home's piece, and the band
    python tools/blender/genius_homes.py edo tiber  # some

Each is game/assets/genius/trappings/<home>.glb, hanging down from its origin and facing the
front (-Y here), about the size of the charm. Materials are named home_main, home_second and
home_metal: the game colours them from the home's dress colours (main, second, and the metal
or the home's third colour). band.glb is a plain neck band for bodies with a collar socket.
"""
import math
import os
import sys

import bpy
import bmesh  # noqa: E402  (bmesh is importable once bpy is)
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "game", "assets", "genius", "trappings")


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def mats():
    return {"main": mat("home_main", (0.3, 0.3, 0.4)), "second": mat("home_second", (0.8, 0.75, 0.6)),
            "metal": mat("home_metal", (0.7, 0.58, 0.28), rough=0.4, metal=0.6)}


def ob(name, bm, material):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    return o


def disc(r, thick, at=(0, 0, 0), segments=20):
    """A disc facing the front."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r, radius2=r, depth=thick)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(at)) @ Matrix.Rotation(math.pi / 2, 4, "X"), verts=bm.verts)
    return bm


def ball(r, at=(0, 0, 0), squash=(1, 1, 1), sub=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * squash[0], v.co.y * squash[1], v.co.z * squash[2])) + Vector(at)
    return bm


def box(size, at=(0, 0, 0), rot_y=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot_y, 4, "Y") @ Matrix.Diagonal(Vector((size[0], size[1], size[2], 1))), verts=bm.verts)
    return bm


def ring(r, tube, at=(0, 0, 0), start=0.0, end=2 * math.pi, segments=24, around="Y"):
    """A ring (or an arc of one) facing the front; around="Z" lays it flat."""
    bm = bmesh.new()
    n = max(3, int(segments * (end - start) / (2 * math.pi)))
    loops = []
    for i in range(n + 1):
        a = start + (end - start) * i / n
        c = Vector((r * math.cos(a), 0, r * math.sin(a))) if around == "Y" else Vector((r * math.cos(a), r * math.sin(a), 0))
        out = c.normalized()
        up = Vector((0, 1, 0)) if around == "Y" else Vector((0, 0, 1))
        loop = [bm.verts.new(c + (out * math.cos(2 * math.pi * k / 8) + up * math.sin(2 * math.pi * k / 8)) * tube + Vector(at)) for k in range(8)]
        loops.append(loop)
    for i in range(n):
        a, b = loops[i], loops[i + 1]
        for k in range(8):
            bm.faces.new((a[k], a[(k + 1) % 8], b[(k + 1) % 8], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def star(points, r_out, r_in, thick, at=(0, 0, 0)):
    bm = bmesh.new()
    front, back = [], []
    for i in range(points * 2):
        a = math.pi / 2 + math.pi * i / points
        r = r_out if i % 2 == 0 else r_in
        front.append(bm.verts.new(Vector((r * math.cos(a), -thick / 2, r * math.sin(a))) + Vector(at)))
        back.append(bm.verts.new(Vector((r * math.cos(a), thick / 2, r * math.sin(a))) + Vector(at)))
    cf = bm.verts.new(Vector((0, -thick, 0)) + Vector(at))
    cb = bm.verts.new(Vector((0, thick / 2, 0)) + Vector(at))
    n = points * 2
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((cf, front[i], front[j]))
        bm.faces.new((cb, back[j], back[i]))
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def tail(length, width, at, lean=0.0, thick=0.006):
    """A hanging tail of cloth: a thin strip from `at` downward, leaning to one side."""
    bm = bmesh.new()
    steps = 4
    rows = []
    for i in range(steps + 1):
        t = i / steps
        c = Vector(at) + Vector((lean * t * length, 0.004 * math.sin(t * 3.0), -length * t))
        w = width * (1.0 + 0.25 * t)
        rows.append([bm.verts.new(c + Vector((-w / 2, -thick / 2, 0))), bm.verts.new(c + Vector((w / 2, -thick / 2, 0))),
                     bm.verts.new(c + Vector((w / 2, thick / 2, 0))), bm.verts.new(c + Vector((-w / 2, thick / 2, 0)))])
    for a, b in zip(rows, rows[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rows[-1])
    bm.faces.new(rows[0][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def tuft(n, length, r, at):
    out = []
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) * 0.32
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=0.001, depth=length)
        d = Vector((math.cos(a), 0, math.sin(a)))
        rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(at) + d * length / 2) @ rot, verts=bm.verts)
        out.append(bm)
    return out


# --- The thirteen: each returns [(name, bmesh, material key)] ---------------------------

def alexandria():
    """The Academy's brass tag on a grey loop: the cohort's, the same on everyone."""
    return [("loop", ring(0.014, 0.004, (0, 0, -0.014)), "main"), ("tag", box((0.042, 0.006, 0.056), (0, 0, -0.058)), "metal"),
            ("stud", ball(0.006, (0, -0.005, -0.04)), "second")]


def columbia():
    """A marshal's star on a blue rosette."""
    return [("rosette", disc(0.034, 0.006, (0, 0, -0.04)), "main"), ("star", star(5, 0.04, 0.017, 0.006, (0, -0.006, -0.04)), "metal")]


def cahokia():
    """The river's woven sash, knotted, in ochre and red."""
    return [("knot", ball(0.022, (0, 0, -0.02), (1.2, 0.7, 0.9)), "second"), ("tail_a", tail(0.11, 0.028, (-0.008, 0, -0.03), -0.25), "second"),
            ("tail_b", tail(0.09, 0.026, (0.01, -0.004, -0.03), 0.3), "metal")]


def lunden():
    """A docker's red scarf, knotted at the throat."""
    return [("knot", ball(0.026, (0, 0, -0.022), (1.25, 0.8, 0.85)), "second"), ("end_a", tail(0.085, 0.045, (-0.012, 0, -0.034), -0.35), "second"),
            ("end_b", tail(0.07, 0.042, (0.014, -0.004, -0.034), 0.4), "second")]


def colonia():
    """A lens from the engine-works on a leather tab."""
    return [("tab", box((0.03, 0.006, 0.05), (0, 0, -0.025)), "main"), ("rim", ring(0.03, 0.006, (0, -0.004, -0.07)), "metal"),
            ("glass", disc(0.026, 0.004, (0, -0.004, -0.07)), "second")]


def tiber():
    """A bronze disc on a red cord: what a child of the old walls is given."""
    return [("cord", ring(0.02, 0.0035, (0, 0, -0.02)), "main"), ("disc", disc(0.032, 0.008, (0, 0, -0.07)), "metal"),
            ("boss", ball(0.012, (0, -0.006, -0.07), (1, 0.5, 1)), "metal")]


def khemet():
    """The growers' broad collar: bands of gold and green."""
    return [("band_a", ring(0.045, 0.007, (0, 0, 0.0), math.pi * 1.08, math.pi * 1.92), "metal"),
            ("band_b", ring(0.061, 0.007, (0, 0, 0.0), math.pi * 1.1, math.pi * 1.9), "second"),
            ("band_c", ring(0.077, 0.007, (0, 0, 0.0), math.pi * 1.12, math.pi * 1.88), "metal")]


def baghdad():
    """A jewel at the brow of a turban, worn at the throat: a drop of gold on blue cloth."""
    drop = ball(0.02, (0, -0.004, -0.06), (0.8, 0.6, 1.5))
    return [("cloth", ball(0.024, (0, 0, -0.018), (1.4, 0.7, 0.7)), "second"), ("drop", drop, "metal"), ("fold", ring(0.026, 0.005, (0, 0, -0.018), math.pi, 2 * math.pi), "main")]


def varanasi():
    """A string of saffron beads."""
    out = []
    for i in range(9):
        a = math.pi * (1.08 + 0.84 * i / 8)
        out.append(("bead_%d" % i, ball(0.011 if i != 4 else 0.015, (0.06 * math.cos(a), 0, 0.075 * math.sin(a) + 0.01)), "main" if i != 4 else "second"))
    return out


def jiangnan():
    """A jade ring on a plum cord, with a tassel."""
    return [("cord", box((0.005, 0.005, 0.03), (0, 0, -0.015)), "main"), ("jade", ring(0.026, 0.008, (0, 0, -0.055)), "metal"),
            ("tassel", tail(0.06, 0.016, (0, 0, -0.082), 0.0), "main")]


def kazan():
    """A tuft of fur under an ochre band: the steppe's."""
    return [("band", box((0.05, 0.012, 0.02), (0, 0, -0.012)), "second")] + [("fur_%d" % i, bm, "metal") for i, bm in enumerate(tuft(5, 0.075, 0.012, (0, 0, -0.022)))]


def timbuktu():
    """A satchel no bigger than a hand, on an indigo strap: something to carry a page in."""
    return [("strap", box((0.012, 0.005, 0.04), (0, 0, -0.02)), "main"), ("satchel", box((0.058, 0.02, 0.046), (0, 0, -0.062)), "metal"),
            ("flap", box((0.06, 0.006, 0.022), (0, -0.012, -0.05)), "second"), ("clasp", ball(0.006, (0, -0.016, -0.058)), "main")]


def edo():
    """A cord knotted at the hip, worn at the throat: two loops and two tails."""
    return [("loop_l", ring(0.02, 0.006, (-0.022, 0, -0.02)), "metal"), ("loop_r", ring(0.02, 0.006, (0.022, 0, -0.02)), "metal"),
            ("knot", ball(0.012, (0, -0.002, -0.02)), "metal"), ("tail_l", tail(0.08, 0.014, (-0.006, 0, -0.028), -0.2), "second"),
            ("tail_r", tail(0.08, 0.014, (0.006, 0, -0.028), 0.2), "second")]


def band():
    """A plain neck band for a body with a collar socket: the piece hangs from it."""
    return [("band", ring(0.105, 0.012, (0, 0, 0)), "main"), ("bead", ball(0.012, (0, -0.004, -0.105)), "metal")]


HOMES = {"alexandria": alexandria, "columbia": columbia, "cahokia": cahokia, "lunden": lunden, "colonia": colonia, "tiber": tiber,
         "khemet": khemet, "baghdad": baghdad, "varanasi": varanasi, "jiangnan": jiangnan, "kazan": kazan, "timbuktu": timbuktu,
         "edo": edo, "band": band}


def build(which=None):
    os.makedirs(OUT, exist_ok=True)
    for home, fn in HOMES.items():
        if which and home not in which:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        M = mats()
        obs = [ob("%s_%s" % (home, name), bm, M[key]) for name, bm, key in fn()]
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.object.join()
        bpy.context.view_layer.objects.active.name = home
        path = os.path.join(OUT, home + ".glb")
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_animations=False, export_materials="EXPORT")
        print("[genius_homes] wrote", os.path.relpath(path, ROOT), "%d KB" % max(1, os.path.getsize(path) // 1024))


if __name__ == "__main__":
    build([a for a in sys.argv[1:]] or None)
