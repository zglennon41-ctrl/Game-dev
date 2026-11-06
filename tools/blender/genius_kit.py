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

def render_card(form, objects, path, rim=(0.42, 0.9, 0.55)):
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
    # The field's materials glow in the Shape's colour on the card, as they do in the game,
    # and never so bright that they wash out to white.
    for m in bpy.data.materials:
        if m.name.startswith("field") and m.use_nodes:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Emission Color"].default_value = (rim[0], rim[1], rim[2], 1)
                bsdf.inputs["Emission Strength"].default_value = min(1.6, bsdf.inputs["Emission Strength"].default_value * 0.4 + 0.4)
                bsdf.inputs["Base Color"].default_value = (rim[0] * 0.25, rim[1] * 0.25, rim[2] * 0.25, 1)
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



# ======================================================================================
# The other First Forms: generic bodies and the parts their features need.
# ======================================================================================

STONE = (0.16, 0.15, 0.14, 1)
FUR = (0.08, 0.06, 0.045, 1)
SLEEK = (0.07, 0.06, 0.05, 1)
IRON = (0.06, 0.06, 0.065, 1)
BRASS = (0.26, 0.17, 0.07, 1)
INK = (0.015, 0.012, 0.018, 1)
SKIN = (0.22, 0.16, 0.12, 1)
CLOTH = (0.12, 0.08, 0.06, 1)


def field(name, strength=3.0, rough=0.4):
    return material("field_" + name, (0.02, 0.02, 0.02, 1), rough, emission=(1, 1, 1, 1), strength=strength)


def quad_body(name, mat, length=0.9, height=0.55, girth=0.11, head=0.09, neck=0.1, leg=0.3, tail=0.3, leg_r=0.028):
    """A four-legged body along -Y (the front), standing on Z = 0, with its sockets."""
    half = length / 2.0
    spine = [((0, half, height * 0.9), girth * 0.6), ((0, half * 0.5, height), girth), ((0, 0, height * 1.02), girth * 1.05),
             ((0, -half * 0.55, height), girth), ((0, -half * 0.9, height * 1.05), girth * 0.75),
             ((0, -half - neck * 0.6, height + neck * 0.7), girth * 0.6), ((0, -half - neck - head * 0.6, height + neck * 0.9), head)]
    body = skin_body(name + "_body", spine, mat)
    objs = [body]
    for sx in (-1, 1):
        for sy, tag in ((-half * 0.7, "f"), (half * 0.7, "b")):
            objs.append(skin_body("leg_%s%s" % (tag, "l" if sx < 0 else "r"),
                                  [((sx * girth * 0.8, sy, height * 0.8), leg_r * 1.6), ((sx * girth * 1.05, sy, height * 0.45), leg_r), ((sx * girth * 1.1, sy, 0.03), leg_r * 0.9)],
                                  mat, subdiv=1))
    if tail > 0:
        objs.append(skin_body(name + "_tail", [((0, half, height * 0.9), girth * 0.45), ((0, half + tail * 0.6, height * 1.05), girth * 0.3), ((0, half + tail, height * 1.15), girth * 0.12)], mat, subdiv=1))
    hz = height + neck * 0.9
    hy = -half - neck - head * 0.6
    socks = [socket("socket_head", (0, hy, hz + head * 0.9)), socket("socket_eyes", (0, hy - head * 0.85, hz + head * 0.25)),
             socket("socket_back", (0, 0, height + girth)), socket("socket_body", (0, -half * 0.4, height - girth * 0.4)),
             socket("socket_throat", (0, hy + head * 0.5, hz - head * 0.6)), socket("socket_light", (0, -half * 0.2, height + girth * 1.1)),
             socket("socket_limb_fl", (-girth * 1.1, -half * 0.7, 0.03)), socket("socket_limb_fr", (girth * 1.1, -half * 0.7, 0.03)),
             socket("socket_limb_bl", (-girth * 1.1, half * 0.7, 0.03)), socket("socket_limb_br", (girth * 1.1, half * 0.7, 0.03)),
             socket("socket_arm_l", (-girth * 1.3, -half * 0.6, height * 0.6)), socket("socket_arm_r", (girth * 1.3, -half * 0.6, height * 0.6))]
    return objs + socks


def biped_body(name, mat, height=0.62, bulk=0.07, head=0.07, arm=0.22, leg=0.22):
    """A small person of the field: torso, head, arms, legs, facing -Y."""
    hips = leg + 0.02
    chest = hips + height * 0.32
    torso = skin_body(name + "_torso", [((0, 0, hips), bulk * 0.9), ((0, 0, (hips + chest) / 2), bulk), ((0, 0, chest), bulk * 1.05), ((0, 0, chest + 0.03), bulk * 0.55)], mat)
    headobj = skin_body(name + "_head", [((0, 0, chest + 0.06), head * 0.5), ((0, -0.01, chest + 0.06 + head * 0.9), head), ((0, 0, chest + 0.06 + head * 1.6), head * 0.7)], mat)
    objs = [torso, headobj]
    for sx in (-1, 1):
        tag = "l" if sx < 0 else "r"
        objs.append(skin_body("arm_" + tag, [((sx * bulk * 1.05, 0, chest), bulk * 0.35), ((sx * (bulk + arm * 0.5), -0.02, chest - arm * 0.45), bulk * 0.28), ((sx * (bulk + arm * 0.7), -0.06, chest - arm), bulk * 0.25)], mat, subdiv=1))
        objs.append(skin_body("leg_" + tag, [((sx * bulk * 0.5, 0, hips), bulk * 0.4), ((sx * bulk * 0.6, 0, hips * 0.5), bulk * 0.3), ((sx * bulk * 0.65, -0.02, 0.03), bulk * 0.3)], mat, subdiv=1))
    top = chest + 0.06 + head * 1.6
    socks = [socket("socket_head", (0, 0, top + 0.02)), socket("socket_eyes", (0, -head * 0.95, chest + 0.06 + head * 0.95)),
             socket("socket_back", (0, bulk * 1.1, chest - 0.02)), socket("socket_body", (0, -bulk * 1.05, chest - height * 0.12)),
             socket("socket_throat", (0, -bulk * 0.6, chest + 0.03)), socket("socket_light", (0, -bulk * 1.1, chest - 0.02)),
             socket("socket_arm_l", (-(bulk + arm * 0.7), -0.06, chest - arm)), socket("socket_arm_r", ((bulk + arm * 0.7), -0.06, chest - arm)),
             socket("socket_limb_fl", (-bulk * 0.65, -0.02, 0.03)), socket("socket_limb_fr", (bulk * 0.65, -0.02, 0.03))]
    return objs + socks


def box(name, size, at, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=at)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.rotation_euler = rot
    o.data.materials.append(mat)
    o.select_set(False)
    return o


def lantern_body():
    """A walking lantern: a brass housing with a lit core, on three root-like legs."""
    brass = material("brass", BRASS, 0.45)
    glass = material("glass", (0.3, 0.35, 0.4, 1), 0.1)
    core = field("core", 5.0)
    objs = [box("housing", (0.26, 0.26, 0.3), (0, 0, 0.5), brass), box("cap", (0.32, 0.32, 0.05), (0, 0, 0.68), brass),
            cone("finial", (0, 0, 0.7), (0, 0, 0.84), 0.09, brass)]
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        objs.append(box("post_%d%d" % (sx, sy), (0.03, 0.03, 0.3), (sx * 0.12, sy * 0.12, 0.5), brass))
    objs.append(sphere("core", (0, 0, 0.5), 0.085, core))
    for i, a in enumerate((0.0, 2.1, 4.2)):
        objs.append(skin_body("leg_%d" % i, [((math.sin(a) * 0.08, math.cos(a) * 0.08, 0.36), 0.03), ((math.sin(a) * 0.16, math.cos(a) * 0.16, 0.18), 0.022), ((math.sin(a) * 0.2, math.cos(a) * 0.2, 0.02), 0.02)], brass, subdiv=1))
    socks = [socket("socket_head", (0, 0, 0.9)), socket("socket_eyes", (0, -0.14, 0.56)), socket("socket_back", (0, 0.15, 0.55)),
             socket("socket_body", (0, -0.15, 0.45)), socket("socket_throat", (0, -0.14, 0.62)), socket("socket_light", (0, 0, 0.5)),
             socket("socket_limb_fl", (-0.17, -0.1, 0.02)), socket("socket_limb_fr", (0.17, -0.1, 0.02)), socket("socket_limb_bl", (0, 0.2, 0.02)),
             socket("socket_arm_l", (-0.18, 0, 0.5)), socket("socket_arm_r", (0.18, 0, 0.5))]
    return objs + socks


def aspect_body(kind):
    """The field with no body: a core and wisps. The game adds the particles."""
    core = field("core", 0.6 if kind == "flame" else 0.2)
    wisp = material("field_wisp" if kind == "flame" else "field_shade", (0.02, 0.02, 0.02, 1), 0.5, emission=(1, 1, 1, 1), strength=0.8 if kind == "flame" else 0.3)
    husk = material("husk", (0.03, 0.025, 0.03, 1), 0.9)
    objs = [sphere("core", (0, 0, 0.45), 0.09, core)]
    # Tongues of the field, standing up from the core like flame, or hanging like shadow.
    for i in range(7):
        a = i * 0.898
        up = 1.0 if kind == "flame" else -0.6
        pts = [(0, 0), (-0.07, 0.14 * up), (-0.03, (0.34 + 0.06 * (i % 3)) * up), (0.06, 0.16 * up)]
        w = slab("wisp_%d" % i, pts, 0.035, wisp if i % 2 == 0 else husk, z=0.0)
        w.location = (math.sin(a) * 0.09, math.cos(a) * 0.09, 0.45 if kind == "flame" else 0.62)
        # Standing up (or hanging), turned to face outward from the core.
        w.rotation_euler = (math.pi / 2 - 0.2, 0, a)
        objs.append(w)
    if kind == "shadow":
        objs.append(sphere("head", (0, 0, 0.66), 0.11, husk))
    socks = [socket("socket_head", (0, 0, 0.85)), socket("socket_eyes", (0, -0.16, 0.56)), socket("socket_back", (0, 0.14, 0.55)),
             socket("socket_body", (0, -0.1, 0.45)), socket("socket_throat", (0, -0.12, 0.6)), socket("socket_light", (0, 0, 0.5))]
    return objs + socks


# --- Parts -----------------------------------------------------------------------------

def horn_brow_part():
    m = material("horn", HORN, 0.5)
    return [skin_body("horn_%s" % t, [((s * 0.03, 0.0, 0.0), 0.028), ((s * 0.09, 0.02, 0.05), 0.022), ((s * 0.13, 0.08, 0.02), 0.014), ((s * 0.11, 0.12, -0.04), 0.008)], m, subdiv=1) for s, t in ((-1, "l"), (1, "r"))]


def horns_part():
    m = material("horn", HORN, 0.5)
    return [cone("horn_%s" % t, (s * 0.04, 0, 0), (s * 0.08, -0.02, 0.16), 0.022, m, verts=8) for s, t in ((-1, "l"), (1, "r"))]


def broad_chest_part():
    m = material("plate", STONE, 0.7)
    p = slab("chest_plate", [(-0.14, -0.1), (-0.17, 0.02), (-0.1, 0.1), (0.1, 0.1), (0.17, 0.02), (0.14, -0.1), (0, -0.14)], 0.04, m)
    p.rotation_euler = (math.pi / 2, 0, 0)
    return [p]


def long_legs_part():
    m = material("horn", HORN, 0.5)
    return [cone("greave", (0, 0, 0.0), (0, 0, 0.14), 0.03, m, verts=8)]


def fangs_part():
    m = material("bone", BONE, 0.4)
    return [cone("fang_%s" % t, (s * 0.03, -0.09, -0.06), (s * 0.03, -0.1, -0.11), 0.012, m, verts=6) for s, t in ((-1, "l"), (1, "r"))]


def fins_part():
    m = material("fin", SLEEK, 0.6)
    f = slab("fin", [(-0.01, -0.02), (-0.09, 0.0), (-0.1, 0.04), (0.0, 0.06), (0.02, 0.0)], 0.012, m)
    return [f]


def small_hands_part():
    m = material("skin", SKIN, 0.7)
    objs = [sphere("palm", (0, -0.01, 0), 0.025, m)]
    for i in range(3):
        objs.append(cone("finger_%d" % i, (-0.015 + i * 0.015, -0.025, 0), (-0.02 + i * 0.02, -0.065, -0.01), 0.007, m, verts=6))
    return objs


def lantern_part():
    brass = material("brass", BRASS, 0.45)
    core = field("core", 5.0)
    return [box("cage", (0.06, 0.06, 0.085), (0, 0, 0), brass), sphere("flame", (0, 0, 0), 0.025, core), box("ring", (0.03, 0.01, 0.01), (0, 0, 0.055), brass)]


def voice_part():
    m = field("voice", 2.5)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.008, location=(0, -0.01, 0), rotation=(math.pi / 2, 0, 0))
    o = bpy.context.active_object
    o.name = "voice_ring"
    o.data.materials.append(m)
    o.select_set(False)
    return [o]


def brush_part():
    m = material("bristle", FUR, 0.9)
    return [cone("brush", (0, 0, 0), (0, 0, -0.16), 0.03, m, verts=10), box("ferrule", (0.03, 0.03, 0.03), (0, 0, 0.01), material("brass", BRASS, 0.45))]


def old_eyes_part():
    eye = field("eye", 1.2)
    lid = material("skin", SKIN, 0.8)
    objs = []
    for s in (-1, 1):
        objs.append(sphere("eye_%d" % s, (s * 0.04, 0, 0), 0.016, eye))
        l = sphere("lid_%d" % s, (s * 0.04, 0.004, 0.006), 0.019, lid)
        l.scale = (1, 1, 0.5)
        objs.append(l)
    return objs


def roots_part():
    m = material("root", (0.1, 0.07, 0.05, 1), 0.9)
    return [cone("root_%d" % i, (0, 0, 0.02), (math.sin(a) * 0.08, math.cos(a) * 0.08, -0.02), 0.012, m, verts=6) for i, a in enumerate((0, 2.1, 4.2))]


def cold_core_part():
    return [sphere("cold_core", (0, 0, 0), 0.05, field("cold", 2.0, 0.2))]


def tail_part():
    m = material("skin", SKIN, 0.7)
    return [skin_body("tail", [((0, 0, 0), 0.02), ((0, 0.1, -0.03), 0.016), ((0, 0.2, -0.02), 0.012), ((0, 0.26, 0.02), 0.02)], m, subdiv=1)]


def ember_part():
    return [sphere("ember", (0, 0, 0), 0.04, field("ember", 6.0))]


def glow_part():
    m = field("glow", 1.5)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.006, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = "halo"
    o.data.materials.append(m)
    o.select_set(False)
    return [o]


PARTS = {"horn-brow": horn_brow_part, "horns": horns_part, "broad-chest": broad_chest_part, "long-legs": long_legs_part, "fangs": fangs_part,
         "fins": fins_part, "small-hands": small_hands_part, "lantern": lantern_part, "voice": voice_part, "brush": brush_part,
         "old-eyes": old_eyes_part, "roots": roots_part, "cold-core": cold_core_part, "tail": tail_part, "ember": ember_part, "glow": glow_part,
         "wings": wings_part, "beak": beak_part, "talons": talons_part, "far-eyes": far_eyes_part}

PART_SOCKETS = {"horn-brow": ["socket_head"], "horns": ["socket_head"], "broad-chest": ["socket_body"], "long-legs": ["socket_limb_fl", "socket_limb_fr", "socket_limb_bl", "socket_limb_br"],
                "fangs": ["socket_head"], "fins": ["socket_limb_fl", "socket_limb_fr", "socket_limb_bl", "socket_limb_br"], "small-hands": ["socket_arm_l", "socket_arm_r"],
                "lantern": ["socket_light"], "voice": ["socket_throat"], "brush": ["socket_arm_r"], "old-eyes": ["socket_eyes"], "roots": ["socket_limb_fl", "socket_limb_fr", "socket_limb_bl"],
                "cold-core": ["socket_light"], "tail": ["socket_back"], "ember": ["socket_light"], "glow": ["socket_light"],
                "wings": ["socket_back"], "beak": ["socket_head"], "talons": ["socket_limb_fl", "socket_limb_fr"], "far-eyes": ["socket_eyes"]}

BODIES = {
    "beast-flier": hawk_body,
    "beast-grazer": lambda: quad_body("ram", material("stone_hide", STONE, 0.85), length=0.8, height=0.5, girth=0.13, head=0.09, neck=0.08, tail=0.08),
    "beast-runner": lambda: quad_body("wolf", material("fur", FUR, 0.9), length=0.9, height=0.52, girth=0.095, head=0.08, neck=0.12, tail=0.32, leg_r=0.024),
    "beast-swimmer": lambda: quad_body("otter", material("sleek", SLEEK, 0.35), length=0.85, height=0.3, girth=0.1, head=0.07, neck=0.06, tail=0.4, leg_r=0.02),
    "engine-quadruped": lambda: quad_body("hound", material("iron", IRON, 0.4), length=0.9, height=0.55, girth=0.12, head=0.09, neck=0.1, tail=0.1, leg_r=0.03),
    "kith-fey": lambda: biped_body("fey", material("fey_skin", (0.2, 0.22, 0.18, 1), 0.7), height=0.6, bulk=0.05, head=0.07),
    "kith-homunculus": lambda: biped_body("homunculus", material("clay", (0.2, 0.14, 0.1, 1), 0.9), height=0.55, bulk=0.085, head=0.085),
    "daemon-small": lambda: biped_body("imp", material("ink_skin", INK, 0.3), height=0.6, bulk=0.06, head=0.07),
    "engine-lantern": lantern_body,
    "aspect-flame": lambda: aspect_body("flame"),
    "aspect-shadow": lambda: aspect_body("shadow"),
}

FIRST_FORMS = {"hawk": "beast-flier", "ram": "beast-grazer", "field-wolf": "beast-runner", "otter": "beast-swimmer", "lantern-sprite": "kith-fey",
               "homunculus": "kith-homunculus", "iron-hound": "engine-quadruped", "walking-lantern": "engine-lantern", "ledger-imp": "daemon-small",
               "ember": "aspect-flame", "shadow": "aspect-shadow"}


def form_features(form_id):
    import json
    with open(os.path.join(ROOT, "data", "forms.json")) as f:
        for x in json.load(f):
            if x["id"] == form_id:
                return x["features"]
    return []


def build_form(form_id):
    """A First Form: its body, each of its parts that is not yet built, and its card."""
    sil = FIRST_FORMS[form_id]
    reset()
    export(os.path.join(OUT, "bodies", sil + ".glb"), BODIES[sil]())
    feats = [f for f in form_features(form_id) if f in PARTS]
    for feature in feats:
        reset()
        objs = PARTS[feature]()
        export(os.path.join(OUT, "parts", feature + ".glb"), objs + [c for o in objs for c in o.children])
    # The card: the body with its parts on their sockets.
    reset()
    body = BODIES[sil]()
    sockets = {o.name: o for o in body if o.type == "EMPTY"}
    meshes = [o for o in body if o.type == "MESH"]
    for feature in feats:
        for sname in PART_SOCKETS.get(feature, ["socket_body"]):
            if sname not in sockets:
                continue
            for o in PARTS[feature]():
                o.location = Vector(o.location) + sockets[sname].location
                if o.name.startswith("wing_"):
                    o.rotation_euler = (0.25, (1.05 if o.name.endswith("l") else -1.05), 0)
                meshes.append(o)
                meshes.extend(o.children)
    render_card(form_id, meshes, os.path.join(OUT, "cards", form_id + ".png"))


for _f in FIRST_FORMS:
    if _f != "hawk":
        FORMS[_f] = (lambda fid: (lambda: build_form(fid)))(_f)


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(FORMS)
    for f in wanted:
        FORMS[f]()
