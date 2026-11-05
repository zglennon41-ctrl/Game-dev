"""WILDLINE genius kit: builds genius bodies and parts in Blender and exports them where the
game looks for them (docs/art-bible.md, section 8). Run headless with Blender's Python module:

    python tools/blender/genius_kit.py            # every form this file knows how to build
    python tools/blender/genius_kit.py hawk       # one form

Conventions (the game relies on them):
  - Blender is Z up and the model faces -Y; the glTF export turns that into the game's Y up, +Z forward.
  - A body carries empties named socket_<name> where parts hang (data/genius-bodies.json).
  - Materials whose names start with "field" glow in the partner's Shape colour in the game.
  - Wing parts are two objects named wing_l and wing_r, pivoting at the shoulder, so the game can beat them.
Outputs: game/assets/genius/bodies/<silhouette>.glb, parts/<feature>.glb, cards/<form>.png
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "genius")

# The art bible's palette, linear-ish.
UMBER = (0.06, 0.045, 0.035, 1)
BONE = (0.55, 0.48, 0.36, 1)
HORN = (0.05, 0.04, 0.035, 1)
FEATHER = (0.09, 0.07, 0.055, 1)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, rough=0.8, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = strength
    return m


def skin_body(name, chain, mat, subdiv=2, flatten=None):
    """A smooth organic shape grown from points: chain is [(position, radius), ...] in a line,
    or [(position, radius, parent_index), ...] for branches."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    verts = []
    for i, p in enumerate(chain):
        v = bm.verts.new(Vector(p[0]))
        verts.append(v)
        parent = p[2] if len(p) > 2 else (i - 1)
        if parent >= 0:
            bm.edges.new((verts[parent], v))
    bm.to_mesh(mesh)
    bm.free()
    skin = obj.modifiers.new("skin", "SKIN")
    for i, p in enumerate(chain):
        r = p[1]
        obj.data.skin_vertices[0].data[i].radius = (r, r) if not isinstance(r, tuple) else r
    obj.data.skin_vertices[0].data[0].use_root = True
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = subdiv
    sub.render_levels = subdiv
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for mname in ("skin", "smooth"):
        bpy.ops.object.modifier_apply(modifier=mname)
    if flatten:
        obj.scale = flatten
        bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    obj.select_set(False)
    return obj


def slab(name, outline, thickness, mat, z=0.0, subdiv=1):
    """A flat shape cut from an outline (points in the XY plane), given thickness and smoothed:
    wings, tail fans, plates."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in outline]
    face = bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=[face])
    bm.to_mesh(mesh)
    bm.free()
    sol = obj.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = thickness
    sol.offset = 0.0
    if subdiv > 0:
        sub = obj.modifiers.new("smooth", "SUBSURF")
        sub.levels = subdiv
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier="solid")
    if subdiv > 0:
        bpy.ops.object.modifier_apply(modifier="smooth")
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    obj.select_set(False)
    return obj


def cone(name, base, tip, radius, mat, verts=12):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=0.0, depth=(Vector(tip) - Vector(base)).length)
    obj = bpy.context.active_object
    obj.name = name
    d = Vector(tip) - Vector(base)
    obj.location = Vector(base) + d / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    return obj


def sphere(name, at, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=at)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    return obj


def socket(name, at):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location = at
    bpy.context.collection.objects.link(e)
    return e


def export(path, objects):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    print("wrote", os.path.relpath(path, ROOT), sum(len(o.data.polygons) for o in objects if o.type == "MESH"), "faces")


def group(name, children):
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for c in children:
        c.parent = root
    return root


# --- The hawk: the First Form of something that watches from above ----------------

def hawk_body():
    body_mat = material("body", FEATHER, 0.85)
    # Tail to head along -Y (the front), Z up.
    chain = [((0, 0.3, 0.38), 0.03), ((0, 0.18, 0.42), 0.075), ((0, 0.03, 0.47), 0.13), ((0, -0.1, 0.51), 0.14),
             ((0, -0.19, 0.58), 0.08), ((0, -0.24, 0.66), 0.09), ((0, -0.29, 0.69), 0.075)]
    body = skin_body("hawk_body", chain, body_mat)
    # Tail fan.
    fan = slab("hawk_tail", [(-0.04, 0.3), (-0.13, 0.52), (-0.06, 0.55), (0.0, 0.53), (0.06, 0.55), (0.13, 0.52), (0.04, 0.3)], 0.02, body_mat, z=0.37)
    fan.rotation_euler = (0.25, 0, 0)
    # Legs.
    legs = []
    for side in (-1, 1):
        legs.append(skin_body("leg_%s" % ("l" if side < 0 else "r"), [((side * 0.05, 0.0, 0.42), 0.035), ((side * 0.06, 0.0, 0.3), 0.018), ((side * 0.06, -0.02, 0.22), 0.012)], material("horn", HORN, 0.5), subdiv=1))
    sockets = [socket("socket_head", (0, -0.27, 0.77)), socket("socket_eyes", (0, -0.34, 0.71)), socket("socket_back", (0, -0.03, 0.58)),
               socket("socket_body", (0, -0.12, 0.47)), socket("socket_throat", (0, -0.23, 0.6)), socket("socket_light", (0, -0.14, 0.5)),
               socket("socket_limb_fl", (-0.06, -0.02, 0.22)), socket("socket_limb_fr", (0.06, -0.02, 0.22)),
               socket("socket_arm_l", (-0.12, -0.03, 0.55)), socket("socket_arm_r", (0.12, -0.03, 0.55))]
    return [body, fan] + legs + sockets


def wings_part():
    """Two wings cut from a feathered outline, pivoting at the shoulder; the primaries' tips glow."""
    mat = material("body", FEATHER, 0.85)
    tips = material("field_tips", (0.02, 0.02, 0.02, 1), 0.6, emission=(1, 1, 1, 1), strength=2.5)
    outline = [(0, -0.07), (-0.16, -0.11), (-0.34, -0.1), (-0.52, -0.04), (-0.62, 0.02), (-0.55, 0.06), (-0.5, 0.1),
               (-0.44, 0.09), (-0.4, 0.15), (-0.33, 0.12), (-0.27, 0.18), (-0.2, 0.13), (-0.12, 0.15), (0, 0.08)]
    objs = []
    for side, tag in ((-1, "l"), (1, "r")):
        m = 1 if side < 0 else -1
        pts = [(x * m, y) for x, y in outline]
        w = slab("wing_%s" % tag, pts, 0.025, mat)
        for i, (x, y) in enumerate(((-0.6, 0.02), (-0.52, 0.09), (-0.42, 0.14))):
            tip = slab("primary_%s%d" % (tag, i), [(x * 0.92 * m, y - 0.025), (x * 1.04 * m, y), (x * 0.92 * m, y + 0.025), (x * 0.86 * m, y)], 0.03, tips, subdiv=0)
            tip.parent = w
        objs.append(w)
    return objs


def beak_part():
    # Hangs from socket_head (the crown): the beak itself sits down at the face.
    return [cone("beak", (0, -0.07, -0.08), (0, -0.17, -0.12), 0.03, material("bone", BONE, 0.4))]


def talons_part():
    mat = material("horn", HORN, 0.4)
    return [cone("talon_%d" % i, (0, 0, 0), (math.sin(a) * 0.05, -math.cos(a) * 0.05, -0.03), 0.01, mat, verts=6) for i, a in enumerate((-0.6, 0, 0.6, math.pi))]


def far_eyes_part():
    eye = material("field_eye", (0.02, 0.02, 0.02, 1), 0.2, emission=(1, 1, 1, 1), strength=2.5)
    ring = material("bone", BONE, 0.4)
    objs = []
    for side in (-1, 1):
        objs.append(sphere("eye_%d" % side, (side * 0.045, 0, 0), 0.016, eye))
        r = sphere("ring_%d" % side, (side * 0.045, 0.006, 0), 0.028, ring)
        r.scale = (1, 0.5, 1)
        objs.append(r)
    return objs


# --- Cards --------------------------------------------------------------------------

def render_card(form, objects, path, rim=(0.62, 0.95, 0.7)):
    """The card's portrait: three-quarter view, dark ground, warm key, a rim of field light."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.render.resolution_x = 384
    scene.render.resolution_y = 512
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("card") if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.01, 0.012, 1)
    # Frame the subject.
    lo = Vector((9, 9, 9))
    hi = Vector((-9, -9, -9))
    for o in objects:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    centre = (lo + hi) / 2
    size = max((hi - lo).length, 0.3)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 55
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = centre + Vector((size * 0.75, -size * 1.25, size * 0.35))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    def light(name, kind, at, color, energy, size_=1.0):
        ld = bpy.data.lights.new(name, kind)
        ld.color = color
        ld.energy = energy
        if kind == "AREA":
            ld.size = size_
        lo_ = bpy.data.objects.new(name, ld)
        lo_.location = at
        lo_.rotation_euler = (centre - Vector(at)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(lo_)

    light("key", "AREA", centre + Vector((-size * 1.5, -size * 1.5, size * 1.2)), (1.0, 0.72, 0.45), 150 * size * size, size)
    light("rim", "AREA", centre + Vector((size * 0.8, size * 1.6, size * 0.9)), rim, 140 * size * size, size * 0.8)
    light("fill", "AREA", centre + Vector((size * 1.6, -size * 0.6, -size * 0.2)), (0.55, 0.62, 0.9), 12 * size * size, size)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("wrote", os.path.relpath(path, ROOT))


def build_hawk():
    reset()
    export(os.path.join(OUT, "bodies", "beast-flier.glb"), hawk_body())
    for feature, maker in (("wings", wings_part), ("beak", beak_part), ("talons", talons_part), ("far-eyes", far_eyes_part)):
        reset()
        objs = maker()
        export(os.path.join(OUT, "parts", feature + ".glb"), objs + [c for o in objs for c in o.children])
    # The card: the hawk assembled, its parts on its sockets.
    reset()
    body = hawk_body()
    sockets = {o.name: o for o in body if o.type == "EMPTY"}
    meshes = [o for o in body if o.type == "MESH"]
    for feature, maker, sock in (("wings", wings_part, ["socket_back"]), ("beak", beak_part, ["socket_head"]),
                                 ("talons", talons_part, ["socket_limb_fl", "socket_limb_fr"]), ("far-eyes", far_eyes_part, ["socket_eyes"])):
        for s in sock:
            for o in maker():
                o.location = Vector(o.location) + sockets[s].location
                if o.name.startswith("wing_"):
                    o.rotation_euler = (0.25, (1.05 if o.name.endswith("l") else -1.05), 0)
                meshes.append(o)
                meshes.extend(o.children)
    render_card("hawk", meshes, os.path.join(OUT, "cards", "hawk.png"))


FORMS = {"hawk": build_hawk}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(FORMS)
    for f in wanted:
        FORMS[f]()
