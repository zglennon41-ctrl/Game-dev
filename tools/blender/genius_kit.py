"""WILDLINE genius kit: the geniuses' bodies, their parts and their cards, built in Blender
and exported where the game looks for them (docs/genius-forms.md, docs/art-bible.md section 4).
Run headless with Blender's Python module:

    python tools/blender/genius_kit.py              # every body, every part, every card, the sheet
    python tools/blender/genius_kit.py field-wolf   # one form: its body and its card
    python tools/blender/genius_kit.py bodies parts # only the models
    python tools/blender/genius_kit.py cards        # only the cards, and the sheet
    python tools/blender/genius_kit.py sheet        # only the contact sheet, from the cards

How the forms are made (the second generation; the first were smooth blockouts):
  - Beasts and the engine hound are the CC0 Quaternius wolf reshaped on its own rig
    (beast_kit.py's method), so they stand, walk and run with its animations.
  - Kith and the small daemon are small people from the human pipeline (human.py: MakeHuman's
    child forms and face details) on the KayKit rig with its Idle, Walk and Run.
  - The hawk, the walking lantern, the ember and the shadow are modelled here from faceted
    plates, blades and lathes (genius_geo.py); the game moves them itself.
  - Every part is modelled here, at its socket's origin, for the character's left where it
    is one of a pair (the game mirrors it onto the right).

Conventions the game relies on (game/scripts/genius/genius_body.gd, data/genius-bodies.json):
  - Blender is Z up and the model faces -Y; the glTF export turns that into Y up, +Z forward.
    The character's left is +X.
  - A body carries sockets named socket_<name> where parts hang: empties on an unrigged body,
    empties parented to bones on a rigged one (Godot folds those into the skeleton as bones;
    the game hangs the parts from them). A socket may be turned, so a hand sits as a hand
    should on that body.
  - Materials whose names start with "field" glow in the partner's Shape colour in the game.
  - Wings are two objects named wing_l and wing_r, pivoting at the shoulder; the game beats them.
  - A socket may carry a size (the ram's broad head wears its horns larger), and a body may
    carry a feature in its own design (the stag its antlers): data/genius-bodies.json lists
    those under the silhouette's "carries", and no part is hung for them.
  - Bodies stand about 0.7 units tall here; the game scales a genius to its instar's height.
Outputs: game/assets/genius/bodies/<silhouette>.glb, parts/<feature>.glb, cards/<form>.png
"""
import json
import math
import os
import sys
import tempfile

import bpy
import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "genius")
SCRATCH = os.environ.get("WILDLINE_GENII_SCRATCH", os.path.join(tempfile.gettempdir(), "wildline-genii"))    # where the sheet goes
STAND = 0.72        # how tall a body stands here; the game scales it to its instar

# The palette: desaturated earths, a value apart from each other so the forms read under the
# cel bands; the field's materials carry the colour. (colour, roughness, metallic)
PALETTE = {
    "fur_dark": ((0.105, 0.085, 0.07), 0.92, 0.0), "fur_light": ((0.36, 0.3, 0.24), 0.9, 0.0), "fur_ruff": ((0.21, 0.185, 0.165), 0.95, 0.0),
    "fur_sleek": ((0.13, 0.09, 0.062), 0.3, 0.0), "fur_cream": ((0.55, 0.47, 0.36), 0.45, 0.0),
    "stone_hide": ((0.31, 0.31, 0.33), 0.95, 0.0), "stone_light": ((0.5, 0.49, 0.47), 0.95, 0.0), "stone_plate": ((0.17, 0.17, 0.19), 0.9, 0.0),
    "bone": ((0.7, 0.63, 0.5), 0.5, 0.0), "horn": ((0.11, 0.085, 0.07), 0.4, 0.0), "horn_ridge": ((0.3, 0.25, 0.2), 0.5, 0.0), "claw": ((0.05, 0.045, 0.04), 0.35, 0.0),
    "nose": ((0.03, 0.028, 0.03), 0.5, 0.0), "whisker": ((0.75, 0.72, 0.66), 0.5, 0.0),
    "metal_iron": ((0.12, 0.12, 0.14), 0.5, 0.75), "metal_iron_light": ((0.23, 0.23, 0.26), 0.45, 0.75), "metal_brass": ((0.62, 0.43, 0.15), 0.32, 0.85),
    "metal_copper": ((0.5, 0.24, 0.12), 0.4, 0.8), "metal_dark": ((0.05, 0.05, 0.06), 0.55, 0.6), "glass": ((0.07, 0.11, 0.13), 0.1, 0.0),
    "feather_dark": ((0.15, 0.105, 0.075), 0.9, 0.0), "feather_mid": ((0.36, 0.26, 0.17), 0.9, 0.0), "feather_pale": ((0.74, 0.67, 0.54), 0.85, 0.0),
    "beak": ((0.78, 0.6, 0.18), 0.4, 0.0), "talon": ((0.045, 0.04, 0.04), 0.3, 0.0),
    "clay": ((0.4, 0.36, 0.31), 1.0, 0.0), "clay_dark": ((0.2, 0.16, 0.13), 0.9, 0.0), "leather": ((0.2, 0.12, 0.07), 0.7, 0.0),
    "fey_skin": ((0.62, 0.7, 0.58), 0.6, 0.0), "cloth_leaf": ((0.13, 0.24, 0.13), 0.9, 0.0), "cloth_petal": ((0.3, 0.42, 0.2), 0.9, 0.0), "hair_pale": ((0.8, 0.82, 0.66), 0.7, 0.0),
    "ink": ((0.03, 0.028, 0.045), 0.35, 0.0), "ink_edge": ((0.085, 0.07, 0.12), 0.45, 0.0), "cloth_rag": ((0.2, 0.06, 0.05), 0.9, 0.0),
    "paper": ((0.72, 0.66, 0.52), 0.8, 0.0), "eye_white": ((0.85, 0.83, 0.78), 0.3, 0.0), "eye_dark": ((0.02, 0.02, 0.025), 0.2, 0.0),
    "shade": ((0.022, 0.02, 0.032), 0.9, 0.0), "shade_edge": ((0.075, 0.065, 0.1), 0.85, 0.0), "void": ((0.004, 0.004, 0.006), 1.0, 0.0),
    "hand_skin": ((0.56, 0.44, 0.36), 0.6, 0.0), "hide_red": ((0.3, 0.17, 0.09), 0.9, 0.0), "coal": ((0.04, 0.035, 0.035), 0.9, 0.0), "root": ((0.16, 0.11, 0.075), 0.9, 0.0), "bristle": ((0.1, 0.08, 0.06), 0.9, 0.0), "wood": ((0.27, 0.17, 0.09), 0.8, 0.0),
    "leather_dark": ((0.1, 0.06, 0.04), 0.75, 0.0), "ice": ((0.47, 0.56, 0.6), 0.15, 0.0), "ice_dark": ((0.27, 0.36, 0.41), 0.2, 0.0), "ice_pale": ((0.74, 0.81, 0.82), 0.12, 0.0),
    "wax": ((0.72, 0.66, 0.5), 0.35, 0.0), "cord": ((0.33, 0.25, 0.16), 0.9, 0.0), "keepsake_tint": ((0.16, 0.03, 0.025), 0.8, 0.0), "crow_dark": ((0.024, 0.023, 0.028), 0.55, 0.0),
    "crow_mid": ((0.035, 0.034, 0.042), 0.5, 0.0), "crow_pale": ((0.33, 0.32, 0.3), 0.7, 0.0), "cloth_wool": ((0.2, 0.19, 0.16), 0.95, 0.0), "cloth_dark": ((0.07, 0.065, 0.06), 0.95, 0.0),
}


def log(*a):
    print("[genius_kit]", *a)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color=None, rough=None, metallic=None):
    """A named material from the palette (or the given colour)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    c, r, mt = PALETTE.get(name, ((0.3, 0.3, 0.3), 0.8, 0.0))
    c = color or c
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    bsdf.inputs["Roughness"].default_value = r if rough is None else rough
    bsdf.inputs["Metallic"].default_value = mt if metallic is None else metallic
    return m


def field(name, strength=2.5):
    """A material of the field: it glows the partner's Shape colour in the game."""
    name = "field_" + name
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1)
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Emission Strength"].default_value = strength
    return m


def mark(region, like):
    """The material of a marking region (mask, socks, saddle...): the game shows it in the
    marking's colour or hides it in the coat's (data/genius-looks.json). Here it is born the
    colour of the coat it lies on, so a body with no look is unmarked."""
    name = "mark_" + region
    m = bpy.data.materials.get(name)
    if m:
        return m
    src = like if not isinstance(like, str) else mat(like)
    b = src.node_tree.nodes.get("Principled BSDF")
    c = b.inputs["Base Color"].default_value
    return mat(name, (c[0], c[1], c[2]), rough=b.inputs["Roughness"].default_value, metallic=b.inputs["Metallic"].default_value)


def shape_key(ob, name, move):
    """A blend shape on a finished mesh: move(world position, vertex index) gives where a
    point goes (or None to leave it). The game sets it from the genius's build."""
    if ob.data.shape_keys is None:
        ob.shape_key_add(name="Basis")
    key = ob.shape_key_add(name=name)
    M = ob.matrix_world.copy()
    Mi = M.inverted()
    for i, v in enumerate(ob.data.vertices):
        q = move(M @ v.co, i)
        if q is not None:
            key.data[i].co = Mi @ V(q)
    return key


# ======================================================================================
# A built body: what is exported, where its sockets are, how to pose it for its card
# ======================================================================================

class Built:
    def __init__(self, objects, sockets, arm=None, pose=None):
        self.objects = objects          # meshes (and the armature) to export
        self.sockets = sockets          # name -> empty
        self.arm = arm
        self.pose = pose                # a function that poses a rigged body for its card

    def export(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in self.objects + list(self.sockets.values()):
            o.select_set(True)
        if self.arm:
            bpy.context.view_layer.objects.active = self.arm
            bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                      export_animations=True, export_animation_mode="ACTIONS", export_skins=True)
        else:
            # a body with blend shapes keeps them only if modifiers are not applied (it has none)
            keyed = any(o.type == "MESH" and o.data.shape_keys for o in self.objects)
            bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=not keyed, export_yup=True)
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in self.objects if o.type == "MESH")
        log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB, sockets: %d" % (tris, os.path.getsize(path) // 1024, len(self.sockets)))
        return tris


def free_socket(name, at, rot=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.03
    bpy.context.collection.objects.link(e)
    e.matrix_world = Matrix.Translation(V(at)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    return e


def bone_socket(arm, name, bone, at, rot=None):
    """A socket that rides a bone: an empty parented to it, at a place (and a turn) in the world."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.03
    bpy.context.collection.objects.link(e)
    e.parent = arm
    e.parent_type = "BONE"
    e.parent_bone = bone
    bpy.context.view_layer.update()
    e.matrix_world = Matrix.Translation(V(at)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    return e


def rot_axes(x, y, z):
    """The rotation whose local axes land on the given world directions."""
    M = Matrix((V(x).normalized(), V(y).normalized(), V(z).normalized())).transposed()
    return M


# How a hand part sits (it is modelled hanging: fingers down -Z, the palm to -X, the thumb to
# the front -Y, for the character's left): on a paw planted on the ground the fingers point
# forward and the palm is down; the right side's socket is the mirror, and the game mirrors
# the part onto it.
RAM_HEAD = 1.75       # how much broader the ram's head is than the head a head part is made for
HAND_ON_PAW_L = rot_axes((0, 0, 1), (1, 0, 0), (0, 1, 0))       # local -Z -> forward (-Y), local -X -> down
HAND_ON_PAW_R = rot_axes((0, 0, -1), (-1, 0, 0), (0, 1, 0))
ACROSS_MOUTH = rot_axes((0, 0, -1), (0, 1, 0), (1, 0, 0))       # a held tool's shaft (local Z) lies across the jaw


# ======================================================================================
# The wolf's rig: beasts and the engine hound (beast_kit.py reshapes; this designs)
# ======================================================================================

def _wolf():
    import beast_kit as bk
    return bk, bk.Rig()


def _eye(r):
    """The centre of the left eye (its material's faces on +X)."""
    me = r.mesh.data
    mi = [m.name.split(".")[0] for m in me.materials].index("Eyes_Black") if "Eyes_Black" in [m.name.split(".")[0] for m in me.materials] else None
    if mi is None:
        mi = next(i for i, m in enumerate(me.materials) if "eyes" in m.name)
    pts = [r.M @ me.vertices[v].co for p in me.polygons if p.material_index == mi for v in p.vertices]
    pts = [p for p in pts if p.x > 0]
    return sum(pts, Vector()) / len(pts)


def _nose(r):
    """The tip of the muzzle."""
    pts = r.world_verts()
    y = min(p.y for p in pts)
    tip = [p for p in pts if p.y < y + 0.08]
    return Vector((0, y, sum(p.z for p in tip) / len(tip)))


def _add(r, name, geo, weights, material, smooth=False):
    r.add_part(name, geo[0], geo[1], weights, material, smooth=smooth)


def _paint(r, bones, material):
    """The faces carried by these bones take a material (a tail of cable, legs of brass)."""
    me = r.mesh.data
    idx = {r.mesh.vertex_groups[b].index for b in bones if b in r.mesh.vertex_groups}
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    slot = [m.name for m in me.materials].index(material.name)
    share = []
    for v in me.vertices:
        tot = sum(gp.weight for gp in v.groups) or 1.0
        share.append(sum(gp.weight for gp in v.groups if gp.group in idx) / tot)
    for p in me.polygons:
        if sum(share[i] for i in p.vertices) / len(p.vertices) > 0.55:
            p.material_index = slot


def _hooves(r, material, height=0.2):
    """The feet's faces take a material: hooves, iron shoes."""
    me = r.mesh.data
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    slot = [m.name for m in me.materials].index(material.name)
    for p in me.polygons:
        if (r.M @ p.center).z < height:
            p.material_index = slot


def _flat(r):
    for p in r.mesh.data.polygons:
        p.use_smooth = False


def _neck_ring(r, bone, half_width=0.34):
    """The neck's section at a bone: (y, centre z, half-width, half-height)."""
    y = r.bone(bone).y
    zt, zb = r.top(y, half_width=half_width), r.bottom(y, half_width=half_width)
    zc = (zt + zb) / 2
    return y, zc, r.side(y, zc), (zt - zb) / 2


WOLF_CLIPS = ("AnimalArmature|Idle", "AnimalArmature|Walk", "AnimalArmature|Gallop")
LOWER_LEGS = ("FrontLowerLeg.L", "FrontLowerLeg.R", "BackLowerLeg.L", "BackLowerLeg.R")


def _wolf_marks(r, coat, regions, lies_on=None):
    """Marking regions on the beast's own skin: the faces of its main coat (coat[0], or the
    material lies_on names for a region) that lie in a region take the material mark_<region>.
    Only that one material's faces, so a marking that is hidden is the coat exactly."""
    import beast_kit as bk
    me = r.mesh.data
    names = [m.name for m in me.materials]
    on = {reg: names.index((lies_on or {}).get(reg, coat[0])) for reg in regions if (lies_on or {}).get(reg, coat[0]) in names}
    eye, nose = _eye(r), _nose(r)
    w = {"socks": r._weights([b for leg in LOWER_LEGS for b in r.family(leg)]), "tailtip": r._weights(r.family("Tail4")),
         "head": r._weights(r.family("Head")), "torso": r._weights(bk.TORSO)}
    ya, yb = sorted((r.bone("Torso3").y, r.bone("Back").y))
    R = r.M.to_3x3()
    got = {}
    for p in me.polygons:
        if p.material_index not in on.values():
            continue
        c, n = r.M @ p.center, (R @ p.normal).normalized()
        share = lambda arr: sum(arr[i] for i in p.vertices) / len(p.vertices)  # noqa: E731
        region = None
        if "socks" in regions and share(w["socks"]) > 0.55:
            region = "socks"
        elif "tailtip" in regions and share(w["tailtip"]) > 0.55:
            region = "tailtip"
        elif "mask" in regions and share(w["head"]) > 0.55 and c.y < eye.y + 0.1 and c.z > nose.z - 0.06:
            region = "mask"
        elif "saddle" in regions and share(w["torso"]) > 0.55 and n.z > 0.45 and ya - 0.1 <= c.y <= yb + 0.1:
            region = "saddle"
        if region is None or on.get(region) != p.material_index:
            continue
        m = mark(region, me.materials[p.material_index])
        if m.name not in [x.name for x in me.materials]:
            me.materials.append(m)
        p.material_index = [x.name for x in me.materials].index(m.name)
        got[region] = got.get(region, 0) + 1
    log("marks", got)


def _wolf_shapes(r, tail=True):
    """The beast's build as blend shapes: heavy (a deeper belly, broader flanks), lean, and a
    longer tail."""
    import beast_kit as bk
    ob = r.mesh
    wt = r._weights(bk.TORSO + bk.NECK)
    zc = r.bone("Torso2").z
    for name, k in (("heavy", 0.18), ("lean", -0.13)):
        shape_key(ob, name, lambda p, i, k=k: Vector((p.x * (1 + k * wt[i]), p.y, zc + (p.z - zc) * (1 + k * 0.85 * wt[i]))) if wt[i] > 0.0 else None)
    if tail:
        wl = r._weights(r.family("Tail1"))
        root = r.bone("Tail1")
        shape_key(ob, "long_tail", lambda p, i: root + (p - root) * (1 + 0.4 * wl[i]) if wl[i] > 0.0 else None)


def _finish_wolf(r, extra=None, coat=None, marks=("socks", "mask", "saddle", "tailtip"), tail=True, lies_on=None):
    """Stand it, bring it to the kit's size, and put its sockets on its bones. `coat` names
    the materials of its own skin: its marking regions are cut from them."""
    r.settle()
    if coat:
        _wolf_marks(r, coat, marks, lies_on)
    eye, nose = _eye(r), _nose(r)
    hb = r.bone("Head")
    crown = r.top(hb.y + 0.06, half_width=0.25)
    t3, n1, n2 = r.bone("Torso3"), r.bone("Neck1"), r.bone("Neck2")
    sh = r.bone("FrontUpperLeg.L")
    spots = {
        "socket_head": ("Head", (0, hb.y + 0.06, crown - 0.02), None),
        "socket_eyes": ("Head", (0, eye.y - 0.1, eye.z + 0.01), None),
        "socket_mouth": ("Head", (0, nose.y + 0.16, nose.z - 0.1), None),
        "socket_grip": ("Head", (0, nose.y + 0.22, nose.z - 0.14), ACROSS_MOUTH),
        "socket_throat": ("Neck2", (0, n2.y, r.bottom(n2.y, half_width=0.08) + 0.02), None),
        "socket_light": ("Neck2", (0, (n1.y + n2.y) / 2, r.bottom((n1.y + n2.y) / 2, half_width=0.08) + 0.0), None),
        "socket_back": ("Torso3", (0, t3.y + 0.12, r.top(t3.y + 0.12) - 0.03), None),
        "socket_body": ("Torso3", (0, sh.y - 0.42, sh.z + 0.02), None),
        "socket_tail": ("Tail1", tuple(r.bone("Tail1")), None),
        "socket_arm_l": ("Torso3", (r.side(sh.y, sh.z + 0.2) + 0.02, sh.y, sh.z + 0.2), None),
        "socket_arm_r": ("Torso3", (-r.side(sh.y, sh.z + 0.2) - 0.02, sh.y, sh.z + 0.2), None),
    }
    # where a collar goes: the neck's own section, so the collar (a hoop a tenth of a unit in
    # radius, in its own XZ plane) comes out the size of this neck
    nb = r.bone("Neck2")
    chw = r.side(nb.y, nb.z)
    spots["socket_collar"] = ("Neck2", (0, nb.y, nb.z), lambda k, a=chw: Matrix.Diagonal(((a + 0.03) * k / 0.1, 1.0, (a * 1.12 + 0.03) * k / 0.1)))
    for tag, bone, foot in (("fl", "FrontLowerLeg.L", "FF.L"), ("fr", "FrontLowerLeg.R", "FF.R"), ("bl", "BackLowerLeg.L", "FFB.L"), ("br", "BackLowerLeg.R", "FFB.R")):
        f = r.bone(foot)
        spots["socket_limb_" + tag] = (bone, (f.x, f.y + 0.06, 0.12), None)
    for tag, bone, foot, rot in (("l", "FrontLowerLeg.L", "FF.L", HAND_ON_PAW_L), ("r", "FrontLowerLeg.R", "FF.R", HAND_ON_PAW_R)):
        f = r.bone(foot)
        spots["socket_hand_" + tag] = (bone, (f.x, f.y - 0.02, 0.16), rot)
    spots.update(extra or {})
    height = max(p.z for p in r.world_verts())
    k = STAND / height
    r.uniform(k)
    # a genius stands, walks and runs: the wolf's other clips stay behind
    for act in list(bpy.data.actions):
        if act.name not in WOLF_CLIPS:
            bpy.data.actions.remove(act)
    if r.arm.animation_data:
        for tr in list(r.arm.animation_data.nla_tracks):
            if tr.name not in WOLF_CLIPS:
                r.arm.animation_data.nla_tracks.remove(tr)
    # a socket may carry a size as well as a turn: a head twice as broad wears its parts twice as big
    sockets = {name: bone_socket(r.arm, name, bone, Vector(at) * k, rot(k) if callable(rot) else rot) for name, (bone, at, rot) in spots.items()}
    if coat:
        _wolf_shapes(r, tail=tail)
    return Built([r.arm, r.mesh], sockets, arm=r.arm)


def field_wolf_body():
    """The field-wolf: a lean wolf on legs a third too long, a ruff of quills round its neck,
    a second pair of eyes above the first, a seam of light down its spine."""
    bk, r = _wolf()
    head = r.family("Head", "Ear1.L", "Ear1.R")
    r.leg_length(-0.62)
    r.leg_girth(0.76)
    top = r.top(r.bone("Torso2").y)
    r.scale(bk.TORSO, (0, 0, top), (0.84, 1.0, 0.82))
    r.scale_along(head, r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.2)
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), (1.0, 1.0, 1.6))
    r.lengthen_chain(r.family("Tail1"), [], 1.15)
    c = PALETTE
    r.recolor("Main", "fur_dark", c["fur_dark"][0], rough=0.92)
    r.recolor("Main_Light", "fur_light", c["fur_light"][0], rough=0.9)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.3, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "nose", c["nose"][0], rough=0.5)
    _flat(r)
    # the ruff: three rows of quills swept back, open under the throat
    ruff, tips = mat("fur_ruff"), mat("fur_light")
    for row, (bone, n, L) in enumerate((("Neck1", 13, 0.5), ("Neck2", 12, 0.44), ("Neck3", 11, 0.36))):
        y = r.bone(bone).y
        rz = 0.3
        zc = r.top(y, half_width=0.15) - rz
        rx = 0.27
        geo = None
        for i in range(n):
            a = 0.02 * math.pi + 0.96 * math.pi * i / (n - 1)
            d = Vector((math.cos(a), 0, math.sin(a)))
            base = Vector((rx * 0.82 * d.x, y - 0.05, zc + rz * 0.82 * d.z))
            tip = base + Vector((d.x * L * 0.42, L * 0.9, d.z * L * 0.42 + 0.05))
            geo = g.merge(geo, g.blade(base, tip, 0.17 + 0.03 * (i % 2), normal=d, belly=0.3))
        _add(r, "ruff_%d" % row, geo, bone, ruff if row != 1 else tips)
    # the second eyes, small, above and behind the first
    eye = _eye(r)
    eyes = None
    for s in (1, -1):
        eyes = g.merge(eyes, g.ico((s * (eye.x - 0.035), eye.y + 0.2, eye.z + 0.13), 0.05, sub=1, scale=(0.7, 1.0, 0.75)))
    _add(r, "second_eyes", eyes, "Head", field("eyes", 3.0))
    # the seam along the spine
    r.fin("seam_spine", r.bone("Torso3").y, r.bone("Tail2").y, 0.03, field("seam", 1.6), thickness=0.07, steps=16, sink=0.05)
    return _finish_wolf(r, coat=("fur_dark", "fur_light"))


def ram_body():
    """The ram: stocky, stone-skinned, a deep chest on short thick legs, the head carried low
    and broad under a heavy brow; slabs of stone down its back; light in the cracks."""
    bk, r = _wolf()
    head = r.family("Head", "Ear1.L", "Ear1.R")
    r.scale([], (0, 0, 0), (1.28, 0.94, 1.0), spatial=True)
    r.leg_length(0.5)
    r.leg_girth(1.5)
    r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (1.1, 1.0, 1.3))
    r.lengthen_chain(bk.NECK, head, 0.72)
    r.scale(bk.NECK, r.bone("Neck1"), (1.45, 1.0, 1.35))
    r.rotate(bk.NECK + head, r.bone("Neck1"), X, math.radians(14))
    r.scale(head, r.bone("Neck3"), (1.1, 1.0, 1.14))
    for ear, sg in (("Ear1.L", 1), ("Ear1.R", -1)):
        # a ram's ears lie out to the side, under where the horns will sweep
        r.scale(r.family(ear), r.bone(ear), (0.85, 0.85, 0.7))
        r.rotate(r.family(ear), r.bone(ear), Y, sg * math.radians(72))
        r.shift(r.family(ear), (0, 0.08, -0.14))
    r.scale(r.family("Tail1"), r.bone("Tail1"), 0.3)
    c = PALETTE
    r.recolor("Main", "stone_hide", c["stone_hide"][0], rough=0.95)
    r.recolor("Main_Light", "stone_light", c["stone_light"][0], rough=0.95)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.3, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "nose", c["nose"][0], rough=0.5)
    _flat(r)
    plate = mat("stone_plate")
    # slabs down the back, each on its own bone, and one over each shoulder and haunch
    for i, b in enumerate(("Torso3", "Torso2", "Torso", "Back")):
        y = r.bone(b).y
        r.shell("slab_%d" % i, (0, y, r.top(y) - 0.2), (0.46 - 0.03 * i, 0.34, 0.26), b, plate, segments=6, rings=2)
    sy, sz = r.bone("FrontShoulder.L").y, r.bone("FrontShoulder.L").z + 0.25
    for s in (-1, 1):
        r.shell("slab_shoulder_%d" % s, (s * (r.side(sy, sz) - 0.1), sy, sz), (0.3, 0.5, 0.42), "Torso3", plate, rot=(0, s * math.radians(-72), 0), segments=6, rings=3)
    hy, hz = r.bone("BackShoulder.L").y + 0.1, r.bone("BackShoulder.L").z - 0.1
    for s in (-1, 1):
        r.shell("slab_haunch_%d" % s, (s * (r.side(hy, hz) - 0.1), hy, hz), (0.26, 0.46, 0.4), "Back", plate, rot=(0, s * math.radians(-72), 0), segments=6, rings=3)
    # the brow: a slab over the eyes, and a boss each side where the horns grow
    hb = r.bone("Head")
    eye = _eye(r)
    r.shell("brow", (0, eye.y + 0.08, eye.z + 0.1), (0.4, 0.34, 0.16), "Head", plate, rot=(math.radians(-14), 0, 0), segments=6, rings=3)
    boss = None
    for s in (1, -1):
        boss = g.merge(boss, g.ico((s * 0.3, hb.y + 0.06, eye.z + 0.2), 0.13, sub=1, scale=(1.0, 1.0, 0.8)))
    _add(r, "horn_bosses", boss, "Head", mat("horn"))
    nose = _nose(r)
    r.shell("nose_bone", (0, (nose.y + eye.y) / 2 + 0.05, (nose.z + eye.z) / 2 + 0.1), (0.17, 0.36, 0.14), "Head", mat("stone_light"), rot=(math.radians(-24), 0, 0), segments=6, rings=2)
    _hooves(r, mat("horn"))
    # cracks of light along the flanks
    seam = field("seam", 1.5)
    y0, y1 = r.bone("Torso3").y, r.bone("Back").y
    topz, botz = r.top(r.bone("Torso").y), r.bottom(r.bone("Torso").y)
    for s in (-1, 1):
        r.flank_line("crack_%d" % s, y0, y1, lambda t: botz + (topz - botz) * (0.5 + 0.1 * math.sin(t * 9.0)), seam, height=0.045, depth=0.07, steps=12, side=s)
    # the head's socket is as big as the head: the horns (a part, made for a head of ordinary
    # breadth) grow to clear it
    crown = r.top(hb.y + 0.06, half_width=0.25)
    return _finish_wolf(r, {"socket_head": ("Head", (0, hb.y + 0.06, crown - 0.04), lambda k: Matrix.Scale(RAM_HEAD, 3))},
                        coat=("stone_hide", "stone_light"), marks=("socks", "mask", "saddle"), tail=False)


def otter_body():
    """The river-otter: long and low and sleek, a round small-eared head on a thick neck, a
    heavy tail that tapers, a pale throat, whiskers; a line of light along each flank."""
    bk, r = _wolf()
    head = r.family("Head", "Ear1.L", "Ear1.R")
    body = r.body_bones()
    r.scale(body, (0, 0, 1.25), (1.06, 1.0, 0.8))
    r.scale(head, r.bone("Neck3"), (1.18, 0.82, 1.02))
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), 0.34)
    r.scale(bk.NECK, r.bone("Neck1"), (1.22, 1.0, 1.16))
    r.stretch_y(-0.6, 0.4, 1.5)
    r.leg_length(0.72)
    r.scale(r.legs(), (0, 0, 0), (1.25, 1.0, 1.0))
    r.leg_girth(1.12)
    tail = r.family("Tail1")
    r.lengthen_chain(tail, [], 1.3)
    tz = sum(r.bone(b).z for b in tail) / len(tail)
    r.scale(tail, (0, 0, tz), (2.1, 1.0, 1.55))
    r.scale(r.family("Tail5"), (0, 0, tz), (0.6, 1.0, 0.62))
    r.damp_rotations(tail, 0.5)
    c = PALETTE
    r.recolor("Main", "fur_sleek", c["fur_sleek"][0], rough=0.3)
    r.recolor("Main_Light", "fur_cream", c["fur_cream"][0], rough=0.45)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.2, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "nose", c["nose"][0], rough=0.4)
    _flat(r)
    # whiskers: three a side from the muzzle
    nose = _nose(r)
    wh = None
    for s in (1, -1):
        for j, (dz, dy) in enumerate(((0.1, 0.1), (0.0, 0.16), (-0.1, 0.1))):
            base = Vector((s * 0.16, nose.y + 0.22, nose.z - 0.04 + dz * 0.4))
            wh = g.merge(wh, g.tube([base, base + Vector((s * 0.42, dy, dz))], [0.014, 0.004], n=3))
    _add(r, "whiskers", wh, "Head", mat("whisker"))
    # the lateral lines
    line = field("seam", 1.6)
    la, lb = r.bone("Torso3").y, r.bone("Tail2").y
    mids = [(r.top(la + (lb - la) * i / 20.0, window=0.3) + r.bottom(la + (lb - la) * i / 20.0, window=0.3)) * 0.5 for i in range(21)]
    mids = [sum(mids[max(0, i - 2):i + 3]) / len(mids[max(0, i - 2):i + 3]) for i in range(21)]
    for s in (-1, 1):
        r.flank_line("lateral_%d" % s, la, lb, lambda t: mids[int(round(t * 20))], line, height=0.04, depth=0.06, steps=20, side=s)
    return _finish_wolf(r, coat=("fur_sleek", "fur_cream"))


def hound_body(clockwork=False):
    """The iron hound: the wolf's frame in riveted plate. Iron hide, brass at the joints, a
    cable for a tail, a furnace behind a grille in each flank, lenses for eyes."""
    bk, r = _wolf()
    head = r.family("Head", "Ear1.L", "Ear1.R")
    r.scale([], (0, 0, 0), (1.14, 1.0, 1.0), spatial=True)
    r.leg_girth(1.18)
    hb = r.bone("Head")
    r.scale(head, (0, hb.y, r.top(hb.y, half_width=0.3)), (1.1, 1.06, 1.22))
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), (0.7, 0.7, 0.8))
    tail = r.family("Tail1")
    tz = sum(r.bone(b).z for b in tail) / len(tail)
    r.scale(tail, (0, 0, tz), (0.5, 1.0, 0.5))
    c = PALETTE
    r.recolor("Main", "metal_iron", c["metal_iron"][0], rough=0.5, metallic=0.75)
    r.recolor("Main_Light", "metal_iron_light", c["metal_iron_light"][0], rough=0.45, metallic=0.75)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.1, emission=(1, 1, 1), strength=3.5)
    r.recolor("Nose", "metal_dark", c["metal_dark"][0], rough=0.5, metallic=0.6)
    brass = mat("metal_brass")
    _paint(r, ["FrontLowerLeg.L", "FrontLowerLeg.R", "BackLowerLeg.L", "BackLowerLeg.R"], brass)
    _paint(r, tail, mat("metal_copper"))
    _hooves(r, mat("metal_dark"), 0.16)
    _flat(r)
    plate, dark = mat("metal_iron_light"), mat("metal_dark")
    # plates: the skull, the shoulders, the haunches, and a segmented back
    r.shell("plate_skull", (0, hb.y - 0.02, r.top(hb.y, half_width=0.3) - 0.06), (0.4, 0.56, 0.2), "Head", plate, rot=(math.radians(-16), 0, 0), segments=6, rings=3)
    sy, sz = r.bone("FrontShoulder.L").y, r.bone("FrontShoulder.L").z + 0.3
    for s in (-1, 1):
        r.shell("plate_shoulder_%d" % s, (s * (r.side(sy, sz) - 0.08), sy, sz), (0.3, 0.56, 0.48), "Torso3", plate, rot=(0, s * math.radians(-72), 0), segments=6, rings=3)
    hy, hz = r.bone("BackShoulder.L").y + 0.05, r.bone("BackShoulder.L").z - 0.1
    for s in (-1, 1):
        r.shell("plate_haunch_%d" % s, (s * (r.side(hy, hz) - 0.08), hy, hz), (0.28, 0.5, 0.44), "Back", plate, rot=(0, s * math.radians(-72), 0), segments=6, rings=3)
    for i, b in enumerate(("Torso3", "Torso2", "Torso", "Back")):
        y = r.bone(b).y
        r.shell("plate_back_%d" % i, (0, y, r.top(y) - 0.08), (0.36, 0.26, 0.15), b, plate, segments=6, rings=2)
        # a vent slat behind each back plate
        _add(r, "vent_%d" % i, g.box((0, y + 0.27, r.top(y + 0.27) + 0.0), (0.4, 0.05, 0.1)), b, dark)
    # the furnace: a lit box behind a brass grille in each flank
    fy = (r.bone("Torso2").y + r.bone("Torso").y) / 2
    topz, botz = r.top(fy), r.bottom(fy)
    fz = botz + (topz - botz) * 0.5
    for s in (-1, 1):
        fx = s * (r.side(fy, fz) - 0.05)
        _add(r, "furnace_%d" % s, g.box((fx, fy, fz), (0.12, 0.62, 0.42)), "Torso2", field("core", 3.5))
        grille = g.merge(*[g.box((fx + s * 0.07, fy - 0.24 + 0.16 * j, fz), (0.05, 0.035, 0.5)) for j in range(4)],
                         g.box((fx + s * 0.07, fy, fz + 0.24), (0.06, 0.72, 0.06)), g.box((fx + s * 0.07, fy, fz - 0.24), (0.06, 0.72, 0.06)))
        _add(r, "grille_%d" % s, grille, "Torso2", brass)
    # rivets round the shoulder plates, and a brass jaw strap
    riv = None
    for s in (-1, 1):
        for j in range(5):
            a = math.radians(-60 + 30 * j)
            riv = g.merge(riv, g.ico((s * (r.side(sy, sz) + 0.02), sy + 0.5 * math.sin(a), sz + 0.42 * math.cos(a) - 0.1), 0.035, sub=0))
    _add(r, "rivets", riv, "Torso3", brass)
    if clockwork:
        key = g.merge(g.tube([(0, fy, topz), (0, fy, topz + 0.36)], [0.045, 0.045], n=6), g.box((0, fy, topz + 0.5), (0.5, 0.06, 0.3)))
        _add(r, "key", key, "Torso2", brass)
    return _finish_wolf(r, coat=("metal_iron", "metal_iron_light", "metal_brass"), marks=("socks", "mask", "saddle"), tail=False, lies_on={"socks": "metal_brass"})


# ======================================================================================
# Modelled bodies: the hawk, the walking lantern, the ember, the shadow
# ======================================================================================

def paint(ob, pick, material):
    """Faces of an object that pick(centre, normal, index) keeps take a material."""
    me = ob.data
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    slot = [m.name for m in me.materials].index(material.name)
    for p in me.polygons:
        if pick(ob.matrix_world @ p.center, p.normal, p.index):
            p.material_index = slot


def _sockets(table):
    return {name: free_socket(name, at[0], at[1] if len(at) > 1 else None) for name, at in table.items()}


def hawk_body(corvid=False):
    """The hawk, on the wing: a deep-breasted body, a flat hooded head with a fierce brow, the
    breast barred, the tail fanned, the legs tucked in their feathers. The wings are a part.
    As a corvid (the hooded crow) it is black and grey, smooth-browed, shag-throated, with a
    straight heavy bill of its own."""
    if corvid:
        for name, src in (("feather_dark", "crow_dark"), ("feather_mid", "crow_mid"), ("feather_pale", "crow_pale")):
            mat(name, PALETTE[src][0], rough=PALETTE[src][1])
    dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")
    spine = [(0.22, 0.40, 0.034, 0.028), (0.14, 0.42, 0.07, 0.06), (0.02, 0.44, 0.105, 0.095), (-0.10, 0.47, 0.112, 0.105),
             (-0.19, 0.505, 0.09, 0.085), (-0.25, 0.54, 0.062, 0.06), (-0.29, 0.568, 0.064, 0.06), (-0.335, 0.582, 0.067, 0.062),
             (-0.375, 0.578, 0.052, 0.048), (-0.402, 0.566, 0.028, 0.028)]
    rings = [g.ring((0, y, z), rx, rz, n=8, u=X, v=Z, phase=math.pi / 8) for y, z, rx, rz in spine]
    body = g.to_object("hawk_body", g.loft(rings), dark)
    # the underside from the throat back is pale
    paint(body, lambda c, n, i: n.z < -0.15 and c.y > -0.3, pale)
    # the hood: the head and nape, a marking
    paint(body, lambda c, n, i: c.y < -0.245 and n.z >= -0.15, mark("hood", dark))
    items = []
    # the breast: three rows of barred feathers lying back along it
    for row, (si, n, L) in enumerate(((3, 5, 0.085), (2, 6, 0.09), (1, 4, 0.08))):
        y, zc, rx, rz = spine[si]
        geo = None
        for i in range(n):
            a = math.radians(-150 + 120 * i / (n - 1))
            d = Vector((math.cos(a), 0, math.sin(a)))
            base = Vector((rx * 0.96 * d.x, y - 0.045, zc + rz * 0.96 * d.z))
            geo = g.merge(geo, g.blade(base, base + Vector((d.x * 0.012, L, d.z * 0.012 - 0.004)), 0.06, normal=d, belly=0.5))
        items.append((geo, mid))
    # the mantle: rows of dark feathers down the back
    for si, n, L in ((4, 4, 0.1), (3, 5, 0.11), (2, 4, 0.1)):
        y, zc, rx, rz = spine[si]
        geo = None
        for i in range(n):
            a = math.radians(40 + 100 * i / (n - 1))
            d = Vector((math.cos(a), 0, math.sin(a)))
            base = Vector((rx * 0.95 * d.x, y - 0.03, zc + rz * 0.95 * d.z))
            geo = g.merge(geo, g.blade(base, base + Vector((d.x * 0.012, L, d.z * 0.012 + 0.002)), 0.07, normal=d, belly=0.5))
        items.append((geo, dark if si != 3 else mid))
    # the brow: a plate over each eye, meeting over the bill; the eyes under it
    brow, eyes = None, None
    for sgn in (1, -1):
        brow = g.merge(brow, g.blade((sgn * 0.012, -0.405, 0.6), (sgn * 0.078, -0.3, 0.604), 0.05, normal=(sgn * 0.5, -0.2, 1), belly=0.45))
        eyes = g.merge(eyes, g.ico((sgn * 0.05, -0.362, 0.585), 0.017, sub=1, scale=(0.6, 1.0, 0.9)))
    items += [(brow, dark)] if not corvid else []
    items.append((eyes, field("eyes", 3.0)))
    if corvid:
        # its own bill: straight, heavy, dark, bristled at the root; hackles at the throat
        bill = mat("talon")
        items.append((g.tube([(0, -0.395, 0.566), (0, -0.445, 0.56), (0, -0.505, 0.546)], [0.024, 0.02, 0.003], n=5, flat=0.8), bill))
        items.append((g.blade((0, -0.39, 0.585), (0, -0.44, 0.572), 0.03, normal=(0, 0, 1), belly=0.4), dark))
        hack = None
        for i, (dx, L) in enumerate(((-0.03, 0.06), (-0.012, 0.075), (0.012, 0.075), (0.03, 0.06))):
            hack = g.merge(hack, g.blade((dx, -0.33, 0.535), (dx * 1.3, -0.3, 0.535 - L), 0.03, normal=(0, -1, -0.3), belly=0.4))
        items.append((hack, mid))
    else:
        # the bill's root (the beak itself is a part) and the cere over it
        items.append((g.merge(g.box((0, -0.412, 0.572), (0.03, 0.03, 0.02)), g.blade((0, -0.4, 0.556), (0, -0.44, 0.548), 0.026, normal=(0, 0, -1))), mat("beak")))
    # the tail: seven feathers fanned, a pale band at their ends
    for i in range(7):
        a = math.radians(-33 + 11 * i)
        tipv = Vector((math.sin(a) * 0.27, math.cos(a) * 0.27, -0.03 - 0.008 * abs(i - 3)))
        base = Vector((math.sin(a) * 0.02, 0.2, 0.402 - 0.002 * abs(i - 3)))
        items.append((g.blade(base, base + tipv, 0.062, normal=(0, 0, 1), belly=0.72), mid if i % 2 == 0 else dark))
        items.append((g.blade(base + tipv * 0.8, base + tipv * 1.02, 0.05, normal=(0, 0, 1), belly=0.4, thick=0.008), mark("band", mid if corvid else pale)))
    # the legs: feathered thighs, the shanks tucked back, the feet closed
    leg_y = mat("beak") if not corvid else mat("talon")
    for sgn in (1, -1):
        items.append((g.tube([(sgn * 0.05, 0.02, 0.4), (sgn * 0.056, 0.09, 0.345), (sgn * 0.056, 0.125, 0.325)], [0.045, 0.034, 0.014], n=6), pale))
        items.append((g.tube([(sgn * 0.056, 0.12, 0.327), (sgn * 0.056, 0.185, 0.312)], [0.011, 0.009], n=5), leg_y))
        toes = None
        for dx, dy in ((-0.016, 0.03), (0.0, 0.036), (0.016, 0.03), (0.0, -0.02)):
            toes = g.merge(toes, g.tube([(sgn * 0.056, 0.185, 0.31), (sgn * 0.056 + dx, 0.185 + dy, 0.296)], [0.008, 0.005], n=4))
        items.append((toes, leg_y))
    extra = g.pieces("hawk_dress", items)
    ob = g.join("hawk_body", [body, extra])
    shape_key(ob, "long_tail", lambda p, i: Vector((p.x * 1.12, 0.2 + (p.y - 0.2) * 1.4, p.z)) if p.y > 0.202 and p.z > 0.36 else None)
    socks = _sockets({
        "socket_collar": [(0, -0.262, 0.548), Matrix.Rotation(-0.45, 3, "X") @ Matrix.Diagonal((0.74, 1.0, 0.7))],
        "socket_head": [(0, -0.33, 0.646)], "socket_eyes": [(0, -0.392, 0.588)], "socket_mouth": [(0, -0.418, 0.566)], "socket_grip": [(0, 0.19, 0.29)],
        "socket_throat": [(0, -0.27, 0.488)], "socket_light": [(0, 0.19, 0.292)], "socket_back": [(0, -0.17, 0.588)], "socket_body": [(0, -0.2, 0.415)],
        "socket_tail": [(0, 0.22, 0.4)], "socket_limb_fl": [(0.056, 0.19, 0.3)], "socket_limb_fr": [(-0.056, 0.19, 0.3)],
        "socket_hand_l": [(0.056, 0.19, 0.3)], "socket_hand_r": [(-0.056, 0.19, 0.3)], "socket_arm_l": [(0.1, -0.17, 0.52)], "socket_arm_r": [(-0.1, -0.17, 0.52)],
    })
    return Built([ob], socks)


def lantern_body():
    """The walking lantern: a six-sided brass lantern with its light loose inside it, a vented
    iron roof and a carrying ring, a gauge for a face, walking on three jointed iron legs."""
    brass, iron, dark = mat("metal_brass"), mat("metal_iron"), mat("metal_dark")
    items = []
    # base, chamber and roof
    items.append((g.lathe([(0.05, 0.3), (0.125, 0.315), (0.15, 0.355), (0.13, 0.385)], n=6), brass))
    posts, bars = None, None
    for k in range(6):
        a0, a1 = math.radians(60 * k), math.radians(60 * k + 60)
        p0 = Vector((0.12 * math.cos(a0), 0.12 * math.sin(a0), 0))
        p1 = Vector((0.12 * math.cos(a1), 0.12 * math.sin(a1), 0))
        posts = g.merge(posts, g.tube([p0 + Z * 0.38, p0 + Z * 0.605], [0.012, 0.012], n=4))
        for z in (0.43, 0.56):
            bars = g.merge(bars, g.tube([p0 + Z * z, p1 + Z * z], [0.005, 0.005], n=3))
        bars = g.merge(bars, g.tube([(p0 + p1) / 2 + Z * 0.385, (p0 + p1) / 2 + Z * 0.6], [0.004, 0.004], n=3))
    items += [(posts, brass), (bars, dark)]
    items.append((g.lathe([(0.13, 0.6), (0.158, 0.614), (0.15, 0.632)], n=6), brass))
    items.append((g.lathe([(0.168, 0.632), (0.125, 0.682), (0.058, 0.73), (0.046, 0.752)], n=6), iron))
    items.append((g.lathe([(0.062, 0.752), (0.072, 0.766), (0.034, 0.79), (0.012, 0.8)], n=6), brass))
    # vents in the roof, a ring to carry it by
    vents = None
    for k in range(6):
        a = math.radians(60 * k + 30)
        c = Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 0.7))
        vents = g.merge(vents, g.box(c, (0.012, 0.05, 0.012), rot=(0, 0, a + math.pi / 2)))
    items.append((vents, dark))
    loop = [(0.036 * math.cos(t), 0, 0.832 + 0.036 * math.sin(t)) for t in [math.radians(18 * i) for i in range(21)]]
    items.append((g.tube(loop, [0.007] * 21, n=4, caps=False), brass))
    # the light: a faceted heart loose in the chamber over a burner
    items.append((g.ico((0, 0, 0.495), 0.056, sub=1, scale=(0.85, 0.85, 1.25)), field("core", 4.5)))
    items.append((g.lathe([(0.03, 0.385), (0.036, 0.4), (0.022, 0.425)], n=6), dark))
    # the face: a gauge on the front of the base, its needle the field's
    gz = 0.345
    rim = [(0.03 * math.cos(t), -0.142, gz + 0.03 * math.sin(t)) for t in [math.radians(30 * i) for i in range(13)]]
    items.append((g.tube(rim, [0.006] * 13, n=4, caps=False), brass))
    items.append((g.ico((0, -0.136, gz), 0.026, sub=1, scale=(1, 0.25, 1)), dark))
    items.append((g.blade((0, -0.146, gz - 0.004), (0.014, -0.146, gz + 0.022), 0.008, normal=(0, -1, 0)), field("needle", 3.0)))
    rivets = None
    for k in range(6):
        a = math.radians(60 * k)
        rivets = g.merge(rivets, g.ico((0.143 * math.cos(a), 0.143 * math.sin(a), 0.352), 0.01, sub=0))
    items.append((rivets, iron))
    # three legs: hip, knee above it, the shin down to a three-clawed foot
    feet = {}
    for tag, deg in (("fl", 330), ("fr", 210), ("bl", 90)):
        a = math.radians(deg)
        d = Vector((math.cos(a), math.sin(a), 0))
        hip, knee, ankle, foot = d * 0.1 + Z * 0.335, d * 0.25 + Z * 0.43, d * 0.27 + Z * 0.06, d * 0.275 + Z * 0.012
        items.append((g.merge(g.tube([hip, knee], [0.02, 0.016], n=5), g.tube([knee, ankle], [0.016, 0.011], n=5)), iron))
        items.append((g.merge(g.ico(hip, 0.03, sub=1), g.ico(knee, 0.027, sub=1), g.ico(ankle, 0.018, sub=0)), brass))
        claws = None
        for da in (-0.9, 0.0, 0.9):
            cd = Vector((math.cos(a + da), math.sin(a + da), 0))
            claws = g.merge(claws, g.tube([ankle, foot + cd * 0.03, foot + cd * 0.06 - Z * 0.01], [0.012, 0.009, 0.002], n=4))
        items.append((claws, dark))
        feet[tag] = foot
    ob = g.pieces("lantern_body", items)
    socks = _sockets({
        "socket_head": [(0, 0, 0.87)], "socket_eyes": [(0, -0.128, 0.5)], "socket_mouth": [(0, -0.15, 0.4)], "socket_grip": [(0.17, 0, 0.45)],
        "socket_throat": [(0, -0.135, 0.615)], "socket_light": [(0, 0, 0.6)], "socket_back": [(0, 0.13, 0.56)], "socket_body": [(0, -0.155, 0.345)],
        "socket_tail": [(0, 0.15, 0.36)], "socket_limb_fl": [tuple(feet["fl"])], "socket_limb_fr": [tuple(feet["fr"])], "socket_limb_bl": [tuple(feet["bl"])],
        "socket_hand_l": [tuple(feet["fl"] + Z * 0.02), HAND_ON_PAW_L], "socket_hand_r": [tuple(feet["fr"] + Z * 0.02), HAND_ON_PAW_R],
        "socket_arm_l": [(0.16, 0, 0.5)], "socket_arm_r": [(-0.16, 0, 0.5)],
    })
    return Built([ob], socks)


def ember_body():
    """The ember: no body, a heart of the field in a cradle of cracked coal, five tongues of
    flame turning round it and seven lower ones, cinders adrift, a thread of smoke."""
    flame, wisp, coal = field("flame", 3.0), field("wisp", 1.6), mat("coal")
    items = [(g.ico((0, 0, 0.4), 0.058, sub=1, scale=(0.9, 0.9, 1.15)), field("core", 5.0))]
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        h = 0.72 + 0.05 * ((i * 3) % 4)
        pts = [(0.05 * math.cos(a), 0.05 * math.sin(a), 0.34), (0.095 * math.cos(a + 0.25), 0.095 * math.sin(a + 0.25), 0.47),
               (0.06 * math.cos(a + 0.75), 0.06 * math.sin(a + 0.75), 0.61), (0.012 * math.cos(a + 1.2), 0.012 * math.sin(a + 1.2), h)]
        items.append((g.tongue(pts, [0.07, 0.095, 0.06, 0.004], thick=0.42, normal=(math.cos(a), math.sin(a), 0)), flame))
    for i in range(7):
        a = 2 * math.pi * i / 7
        pts = [(0.095 * math.cos(a), 0.095 * math.sin(a), 0.3), (0.15 * math.cos(a + 0.2), 0.15 * math.sin(a + 0.2), 0.39),
               (0.12 * math.cos(a + 0.7), 0.12 * math.sin(a + 0.7), 0.5 + 0.03 * (i % 3))]
        items.append((g.tongue(pts, [0.055, 0.07, 0.004], thick=0.4, normal=(math.cos(a), math.sin(a), 0)), wisp))
    coals, cracks = g.ico((0, 0, 0.27), 0.075, sub=0, scale=(1.1, 1.1, 0.6)), None
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.5
        coals = g.merge(coals, g.ico((0.1 * math.cos(a), 0.1 * math.sin(a), 0.285 + 0.012 * (i % 2)), 0.048, sub=0, scale=(1.0, 0.8, 0.75), rot=(0.3 * i, 0.5 * i, a)))
        cracks = g.merge(cracks, g.ico((0.066 * math.cos(a + 0.5), 0.066 * math.sin(a + 0.5), 0.3), 0.016, sub=0))
    items += [(coals, coal), (cracks, field("crack", 2.5))]
    cinders = None
    for i, (a, rr, z) in enumerate(((0.4, 0.2, 0.52), (1.9, 0.17, 0.66), (3.2, 0.21, 0.44), (4.6, 0.16, 0.74), (5.6, 0.19, 0.6))):
        cinders = g.merge(cinders, g.ico((rr * math.cos(a), rr * math.sin(a), z), 0.011 + 0.003 * (i % 2), sub=0))
    items.append((cinders, field("cinder", 3.0)))
    smoke = None
    for i, a in enumerate((0.9, 3.0, 5.0)):
        pts = [(0.02 * math.cos(a), 0.02 * math.sin(a), 0.7), (0.05 * math.cos(a + 0.6), 0.05 * math.sin(a + 0.6), 0.78), (0.03 * math.cos(a + 1.4), 0.03 * math.sin(a + 1.4), 0.86 + 0.02 * i)]
        smoke = g.merge(smoke, g.tongue(pts, [0.03, 0.035, 0.003], thick=0.4))
    items.append((smoke, mat("shade_edge")))
    ob = g.pieces("ember_body", items)
    socks = _sockets({
        "socket_head": [(0, 0, 0.8)], "socket_eyes": [(0, -0.07, 0.425)], "socket_mouth": [(0, -0.075, 0.37)], "socket_grip": [(0.14, 0, 0.4)],
        "socket_throat": [(0, -0.07, 0.34)], "socket_light": [(0, 0, 0.4)], "socket_back": [(0, 0.1, 0.46)], "socket_body": [(0, -0.1, 0.38)],
        "socket_tail": [(0, 0.11, 0.3)], "socket_arm_l": [(0.15, 0, 0.42)], "socket_arm_r": [(-0.15, 0, 0.42)],
        "socket_limb_fl": [(0.08, -0.06, 0.24)], "socket_limb_fr": [(-0.08, -0.06, 0.24)],
    })
    return Built([ob], socks)


def shadow_body(daemon=False):
    """The shadow: a hooded figure with nothing in the hood but two eyes; the cloak falls in
    flat folds to a hem of tatters that never reach the ground; long sleeves end in fingers.
    As a daemon (the One Behind) it is ink, broad in the shoulder, its cloak ruled with script."""
    shade, edge = (mat("ink"), mat("ink_edge")) if daemon else (mat("shade"), mat("shade_edge"))
    w = 1.3 if daemon else 1.0
    prof = [(0.87, 0.01, 0.01, 0.075), (0.82, 0.05, 0.06, 0.05), (0.75, 0.092, 0.105, 0.02), (0.67, 0.104, 0.118, 0.0), (0.6, 0.085, 0.09, 0.0),
            (0.555, 0.13, 0.098, 0.005), (0.5, 0.152, 0.1, 0.008), (0.41, 0.145, 0.092, 0.012), (0.3, 0.112, 0.075, 0.012), (0.2, 0.072, 0.052, 0.012)]
    prof = [(z, rx * (w if 0.38 < z < 0.58 else 1.0), ry * (1.0 + (w - 1.0) * 0.5 if 0.38 < z < 0.58 else 1.0), yo) for z, rx, ry, yo in prof]
    rings = [g.ring((0, yo, z), rx, ry, n=10, u=X, v=Y, phase=math.pi / 10) for z, rx, ry, yo in prof][::-1]
    cloak = g.to_object("shadow_cloak", g.loft(rings), shade)
    # alternate folds a shade lighter, so the cloak reads as cloth and not as a cone
    paint(cloak, lambda c, n, i: (int((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi) * 10) % 2 == 0) and abs(n.z) < 0.85, edge)
    items = []
    # nothing in the hood: a void, a rim, two eyes
    items.append((g.ico((0, -0.086, 0.672), 0.075, sub=1, scale=(0.92, 0.42, 1.18)), mat("void")))
    # the cowl's edge: two folds that meet in a point over the brow and fall past the chin
    for sgn in (1, -1):
        items.append((g.tongue([(0, -0.1, 0.785), (sgn * 0.066, -0.118, 0.72), (sgn * 0.078, -0.116, 0.64), (sgn * 0.04, -0.1, 0.575)], [0.02, 0.034, 0.032, 0.012], thick=0.5, normal=(sgn * 0.3, -1, 0)), edge))
    eyes = None
    for sgn in (1, -1):
        eyes = g.merge(eyes, g.ico((sgn * 0.03, -0.121, 0.682), 0.017, sub=1, scale=(1.25, 0.4, 0.4), rot=(0, sgn * -0.3, 0)))
    items.append((eyes, field("eyes", 3.5)))
    # the hem: tatters hanging, each its own length
    for i in range(10):
        a = 2 * math.pi * (i + 0.5) / 10
        d = Vector((math.cos(a), math.sin(a) * 0.72, 0))
        L = 0.14 + 0.05 * ((i * 7) % 4)
        pts = [d * 0.072 + Z * 0.21, d * 0.085 + Z * (0.21 - L * 0.5), d * (0.06 + 0.02 * (i % 2)) + Z * (0.21 - L) + Vector((0.015 * math.sin(i), 0.02, 0))]
        items.append((g.tongue(pts, [0.05, 0.04, 0.003], thick=0.3, normal=d), shade if i % 2 else edge))
    # the sleeves and their fingers
    if daemon:
        script = None
        for z, rx, ry, yo in prof[5:9]:
            loop = g.ring((0, yo, z - 0.02), rx + 0.004, ry + 0.004, n=10, u=X, v=Y, phase=math.pi / 10)
            script = g.merge(script, g.tube(list(loop) + [loop[0]], [0.007] * 11, n=3, caps=False))
        items.append((script, field("script", 2.2)))
    for sgn in (1, -1):
        sh, el, wr = Vector((sgn * 0.165 * w, 0.0, 0.51)), Vector((sgn * (0.235 * w), -0.045, 0.39)), Vector((sgn * (0.262 * w), -0.1, 0.285))
        items.append((g.tongue([sh, el, wr + Vector((0, 0, -0.02))], [0.1, 0.1, 0.075], thick=0.5, normal=(sgn, 0, 0.3)), shade))
        fingers = None
        for j, (dx, dy) in enumerate(((-0.022, -0.02), (0.0, -0.03), (0.022, -0.02))):
            fingers = g.merge(fingers, g.tongue([wr, wr + Vector((sgn * 0.01 + dx, dy, -0.06)), wr + Vector((sgn * 0.005 + dx * 1.6, dy * 2.2, -0.125 - 0.012 * (j == 1)))], [0.016, 0.012, 0.002], thick=0.5))
        items.append((fingers, edge))
    # threads rising off the shoulders
    wisps = None
    for sgn, y in ((1, 0.03), (-1, 0.05), (1, 0.08)):
        b = Vector((sgn * 0.13, y, 0.54))
        wisps = g.merge(wisps, g.tongue([b, b + Vector((sgn * 0.03, 0.03, 0.07)), b + Vector((sgn * 0.01, 0.06, 0.15))], [0.03, 0.022, 0.002], thick=0.3))
    items.append((wisps, edge))
    ob = g.join("shadow_body", [cloak, g.pieces("shadow_dress", items)])
    socks = _sockets({
        "socket_head": [(0, 0.05, 0.86)], "socket_eyes": [(0, -0.128, 0.682)], "socket_mouth": [(0, -0.122, 0.63)], "socket_grip": [(-0.262, -0.1, 0.27)],
        "socket_throat": [(0, -0.09, 0.57)], "socket_light": [(0, -0.15, 0.4)], "socket_back": [(0, 0.11, 0.5)], "socket_body": [(0, -0.1, 0.46)],
        "socket_tail": [(0, 0.07, 0.2)], "socket_arm_l": [(0.262, -0.1, 0.285)], "socket_arm_r": [(-0.262, -0.1, 0.285)],
        "socket_hand_l": [(0.262, -0.1, 0.285)], "socket_hand_r": [(-0.262, -0.1, 0.285)], "socket_limb_fl": [(0.05, 0, 0.08)], "socket_limb_fr": [(-0.05, 0, 0.08)],
    })
    return Built([ob], socks)


# ======================================================================================
# Small people: kith and the small daemon, from the human pipeline on the KayKit rig
# ======================================================================================

KEEP_CLIPS = ("Idle", "Walking_A", "Running_A")
# How a hand part sits at the wrist of an arm held out in the rig's rest pose (see HAND_ON_PAW).
HAND_ON_ARM_L = rot_axes((0, 0, 1), (0, 1, 0), (-1, 0, 0))
HAND_ON_ARM_R = rot_axes((0, 0, -1), (0, 1, 0), (1, 0, 0))
GRIP_IN_HAND_R = rot_axes((1, 0, 0), (0, 0, -1), (0, 1, 0))      # a held tool's working end (local -Z) points forward out of the fist


class SmallPerson:
    """A person of the field: MakeHuman's child forms, shaped by details, on the game's rig
    with three clips, at the kit's size. The builder dresses it and names its sockets."""

    def __init__(self, sex, age, details, build=(0.5, 0.5), stand=STAND, cup=0.5, keep_hands=False, head=1.0, legs=1.0, arms=1.0):
        import numpy as np
        import people_kit as pk
        import human as hu
        import human_kit as hk
        self.np, self.pk, self.hu, self.hk = np, pk, hu, hk

        class Stub:
            pass
        body = Stub()
        body.home, body.sex, body.k, body.HUMAN = "genius", sex, 1.0, True
        body.r = pk.reshape(pk.Rig("Knight"))
        for o in body.r.skinned + body.r.attached:
            bpy.data.objects.remove(o)
        body.r.skinned, body.r.attached = [], []
        self.r = body.r
        self.arm = body.r.arm
        ancestry = {"african": 0.34, "asian": 0.33, "caucasian": 0.33}
        real_form, real_human = hk.home_form, hu.Human

        class Small(real_human):
            """The human, then the proportions of a small person of the field: the head grown
            about the neck, the legs shortened under the hips (the vertices and the joints
            together, each by how much the head or the legs carry it)."""
            def __init__(inner, sex_, ancestry_, details_=None, build_=(0.5, 0.5), height=2.4, like=None, **kw):
                real_human.__init__(inner, sex_, ancestry_, details_, build, height=height, cup=cup, proportions=0.5, like=like, age=age)
                base, v = inner.base, inner.v
                n = len(v)

                def share(bones):
                    w = np.zeros(n)
                    for b in bones:
                        if b in base.weights:
                            idx, x = base.weights[b]
                            np.add.at(w, idx, x / base.weight_total[idx])
                    return np.clip(w, 0.0, 1.0)
                if head != 1.0:
                    c = base.joint(v, "joint-neck") * 0.4 + base.joint(v, "joint-head") * 0.6
                    w = share(["head"])
                    v += (v - c) * (head - 1.0) * w[:, None]
                if arms != 1.0:
                    for sd, sg in (("l", 1.0), ("r", -1.0)):
                        c = base.joint(v, "joint-%s-shoulder" % sd)
                        w = share([b for b in base.weights if b.endswith("_" + sd) and b.split("_")[0] in ("upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb")])
                        v[:, 0] += (v[:, 0] - c[0]) * (arms - 1.0) * w
                if legs != 1.0:
                    hip = float(base.joint(v, "joint-l-upper-leg")[2])
                    z = v[:, 2]
                    v[:, 2] = np.where(z < hip, z * legs, z - hip * (1.0 - legs))
                top = v[:hu.BODY_VERTS, 2].max()
                inner.v = v * (height / top)
        hk.home_form = lambda home, sex_: (ancestry, details)
        hu.Human = Small
        try:
            self.hb = hk.HumanBody(body)
        finally:
            hk.home_form, hu.Human = real_form, real_human
        self.s = stand / 2.4
        hb = self.hb
        stems = [(d or "").rpartition("_")[0] if (d or "")[-2:] in ("_l", "_r") else (d or "") for d in hb.dom]
        self.is_hand = np.array([st.split("_")[0] in ("hand", "index", "middle", "ring", "pinky", "thumb") for st in stems])
        self.keep_hands = keep_hands
        self.skinned, self.rigid = [], []
        self.pivots = {}
        self.body = None

    # --- at the human's own size (2.4), before the kit's -------------------------------

    def make_body(self, material):
        hb, hu = self.hb, self.hu
        ob = hu.mesh_object("Body", hb.humans["fit"].body(), hb.faces, [material])
        hb.weight_body(ob)
        self.body = ob
        self.skinned.append(ob)
        return ob

    def shell(self, name, mask, material, thickness=0.03):
        """A garment cut from the body's own surface where mask(vertex positions) holds."""
        ob = self.hb.shell(name, mask, "fit", thickness)
        ob.data.materials.append(material)
        self.hb.weight_like_body(ob)
        self.skinned.append(ob)
        return ob

    def piece(self, name, geo, material, bone, smooth=False):
        """A rigid piece (geometry in the human's space) that rides one bone."""
        ob = g.to_object(name, geo, material, smooth) if isinstance(geo, tuple) else geo
        ob.name = name
        self.rigid.append((ob, bone))
        return ob

    def eyes(self, white, iris, pupil):
        mats = {"eye_white": white, "iris": iris, "pupil": pupil, "hair": white, "lash": pupil}
        for ob in self.hb.head_pieces(mats):
            if ob.name.startswith("Eye_"):
                self.rigid.append((ob, "head"))
            else:
                bpy.data.objects.remove(ob)

    def finish(self, sockets, decimate=0.22):
        """Cut the hands off at the wrist (the hands are a part), bring everything to the kit's
        size, thin the mesh, keep three clips, and put the sockets on the bones."""
        np, pk = self.np, self.pk
        r, arm, s = self.r, self.arm, self.s
        if not self.keep_hands:
            bm = bmesh.new()
            bm.from_mesh(self.body.data)
            bm.verts.ensure_lookup_table()
            doomed = [f for f in bm.faces if all(self.is_hand[v.index] for v in f.verts)]
            bmesh.ops.delete(bm, geom=doomed, context="FACES")
            loose = [v for v in bm.verts if not v.link_faces]
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
            bm.to_mesh(self.body.data)
            bm.free()
        for ob in self.skinned:
            ob.parent = arm
            mod = ob.modifiers.new("Armature", "ARMATURE")
            mod.object = arm
        bpy.context.view_layer.update()
        for ob, bone in self.rigid:
            ob.parent = arm
            ob.parent_type = "BONE"
            ob.parent_bone = bone
            bpy.context.view_layer.update()
            ob.matrix_world = Matrix.Identity(4)
        r.skinned = list(self.skinned)
        r.attached = [ob for ob, _ in self.rigid]
        r.uniform(s)
        bpy.context.view_layer.update()
        for ob, at in self.pivots.items():
            set_origin(ob, Vector(at) * s)
        # thin the body: a quarter-height person does not need a full person's faces
        if decimate and decimate < 1.0:
            bpy.ops.object.select_all(action="DESELECT")
            for ob in self.skinned:      # the body, and the garments cut from its surface
                ob.select_set(True)
                bpy.context.view_layer.objects.active = ob
                dec = ob.modifiers.new("Decimate", "DECIMATE")
                dec.ratio = decimate
                bpy.ops.object.modifier_move_to_index(modifier="Decimate", index=0)
                bpy.ops.object.modifier_apply(modifier="Decimate")
                ob.select_set(False)
        for ob in self.skinned:
            for poly in ob.data.polygons:
                poly.use_smooth = False
        for a in list(bpy.data.actions):
            if a.name not in KEEP_CLIPS:
                bpy.data.actions.remove(a)
        if arm.animation_data:
            for tr in list(arm.animation_data.nla_tracks):
                if tr.name not in KEEP_CLIPS:
                    arm.animation_data.nla_tracks.remove(tr)
        socks = {name: bone_socket(arm, name, bone, Vector(at) * s, rot) for name, (bone, at, rot) in sockets.items()}

        def pose():
            # the card stands it at ease, not in the rig's rest pose
            act = bpy.data.actions.get("Idle")
            if act and arm.animation_data:
                arm.data.pose_position = "POSE"
                for tr in arm.animation_data.nla_tracks:
                    tr.mute = True
                arm.animation_data.action = act
                if hasattr(arm.animation_data, "action_slot") and getattr(act, "slots", None):
                    arm.animation_data.action_slot = act.slots[0]
                bpy.context.scene.frame_set(1)
                bpy.context.view_layer.update()
        arm.data.pose_position = "POSE"
        return Built([arm] + self.skinned + [ob for ob, _ in self.rigid], socks, arm=arm, pose=pose)

    # --- where things are (at the human's own size) ------------------------------------

    def common_sockets(self):
        hb = self.hb
        J = hb.J
        (x0, x1), (y0, y1), (z0, z1) = hb.head_box
        eye = hb.eye["l"]
        mouth = hb.humans["fit"].joint("joint-mouth")
        chest_z = J["chest"].z + 0.2
        neck_z = hb.trunk_z[9]
        hip_z = J["hips"].z
        out = {
            "socket_head": ("head", (0, (y0 + y1) / 2 - 0.01, z1 - 0.005), None),
            "socket_eyes": ("head", (0, eye.y - hb.eye_r * 1.25, eye.z), None),
            "socket_mouth": ("head", (0, hb.front_y(0.0, float(mouth[2]) - 0.012) - 0.004, float(mouth[2]) - 0.012), None),
            "socket_throat": ("chest", (0, hb.front_y(0.0, neck_z + 0.02) - 0.005, neck_z + 0.02), None),
            "socket_body": ("chest", (0, hb.front_y(0.0, chest_z) - 0.005, chest_z), None),
            "socket_back": ("chest", (0, hb.front_y(0.0, chest_z + 0.12, back=True) + 0.005, chest_z + 0.12), None),
            "socket_tail": ("hips", (0, hb.front_y(0.0, hip_z - 0.06, back=True) + 0.0, hip_z - 0.06), None),
            "socket_arm_l": ("upperarm.l", (J["upperarm.l"].x + 0.06, J["upperarm.l"].y, J["upperarm.l"].z + 0.09), None),
            "socket_arm_r": ("upperarm.r", (J["upperarm.r"].x - 0.06, J["upperarm.r"].y, J["upperarm.r"].z + 0.09), None),
            "socket_hand_l": ("hand.l", tuple(J["wrist.l"]), HAND_ON_ARM_L),
            "socket_hand_r": ("hand.r", tuple(J["wrist.r"]), HAND_ON_ARM_R),
            "socket_limb_fl": ("foot.l", (J["foot.l"].x, J["foot.l"].y - 0.06, 0.05), None),
            "socket_limb_fr": ("foot.r", (J["foot.r"].x, J["foot.r"].y - 0.06, 0.05), None),
            "socket_grip": ("hand.r", tuple(J["handslot.r"]), GRIP_IN_HAND_R),
            "socket_light": ("hand.l", tuple(J["handslot.l"] + Vector((0, 0, -0.03))), HAND_ON_ARM_L),
        }
        return out

    def trunk_mask(self, z_lo, z_hi, front_only=False):
        hb = self.hb
        arm, head = hb.is_arm, (hb.is_head | hb.is_neck)
        yc = hb.J["chest"].y

        def mask(v):
            m = (v[:, 2] > z_lo) & (v[:, 2] < z_hi) & ~arm & ~head
            if front_only:
                m &= v[:, 1] < yc + 0.02
            return m
        return mask

    def heart(self, material, rim=None, drop=0.08):
        """The heart-light every kith carries: a small stone of the field set in the chest."""
        hb = self.hb
        z = hb.J["chest"].z + 0.2 - drop
        y = hb.front_y(0.0, z)
        self.piece("heart_light", g.ico((0, y - 0.012, z), 0.05, sub=1, scale=(1.0, 0.45, 1.2)), material, "chest")
        if rim is not None:
            loop = [(0.062 * math.cos(t), y - 0.012, z + 0.072 * math.sin(t)) for t in [math.radians(30 * i) for i in range(13)]]
            self.piece("heart_rim", g.tube(loop, [0.012] * 13, n=4, caps=False), rim, "chest")


def sprite_body():
    """The lantern-sprite: a slight child of the field with long pointed ears and wide lit eyes,
    a leaf-green shift with a hem of petals, a crest of pale leaves for hair, and two pairs of
    glass wings that never stop."""
    p = SmallPerson("m", 0.3, {"ear-shape-pointed": 1.0, "ear-scale": 1.0, "ear-wing": 0.6, "eye-scale": 1.0, "chin-triangle": 0.7, "nose-scale-vert": -0.4,
                              "nose-volume": -0.5, "cheek-volume": -0.2, "eye-height2": 0.5, "chin-width": -0.5, "mouth-scale-horiz": -0.3, "head-oval": 0.5},
                    build=(0.3, 0.3), stand=0.62, head=1.5, legs=0.88, arms=0.92)
    hb, J = p.hb, p.hb.J
    p.make_body(mat("fey_skin"))
    p.eyes(field("eyes_dim", 1.2), field("eyes", 3.5), field("eyes", 3.5))
    hipz, neckz = J["upperleg.l"].z, hb.trunk_z[9]
    p.shell("shift", p.trunk_mask(hipz - 0.16, neckz - 0.02), mat("cloth_leaf"), 0.03)
    # the hem: petals hanging from the hips, each its own length
    z, hw, hd, yo = hb.rings("trunk", "fit")[1]
    petals = None
    for i in range(9):
        a = 2 * math.pi * (i + 0.5) / 9
        d = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((d.x * (hw + 0.02), yo + d.y * (hd + 0.02), hipz - 0.1))
        petals = g.merge(petals, g.blade(base, base + d * (0.1 + 0.03 * (i % 2)) + Vector((0, 0, -0.32 - 0.07 * (i % 3))), 0.2, normal=d, belly=0.45))
    p.piece("hem_petals", petals, mat("cloth_petal"), "hips")
    # the crest: pale leaves swept back from the brow
    (x0, x1), (y0, y1), (z0, z1) = hb.head_box
    crest = None
    for i, (dx, lift, L) in enumerate(((0.0, 0.16, 0.3), (-0.07, 0.11, 0.27), (0.07, 0.11, 0.27), (-0.12, 0.05, 0.22), (0.12, 0.05, 0.22), (0.0, 0.07, 0.36))):
        base = Vector((dx, y0 + 0.07 + 0.05 * (i // 2), z1 - 0.045 - abs(dx) * 0.5))
        crest = g.merge(crest, g.blade(base, base + Vector((dx * 0.5, L, lift)), 0.12, normal=(dx, -0.2, 1), belly=0.4))
    p.piece("crest", crest, mat("hair_pale"), "head")
    p.heart(field("heart", 3.0), drop=0.02)
    # the wings: two blades a side, pivoting at the shoulder blade
    backz = J["chest"].z + 0.3
    backy = hb.front_y(0.0, backz, back=True) + 0.01
    for tag, sg in (("l", 1), ("r", -1)):
        root = Vector((sg * 0.07, backy, backz))
        geo = g.merge(g.blade(root, root + Vector((sg * 0.62, 0.3, 0.42)), 0.24, normal=(0, -1, 0.2), belly=0.55, thick=0.012),
                      g.blade(root + Vector((0, 0, -0.04)), root + Vector((sg * 0.5, 0.26, -0.22)), 0.19, normal=(0, -1, -0.2), belly=0.55, thick=0.012))
        ob = g.to_object("wing_" + tag, geo, field("wing", 1.2))
        p.piece("wing_" + tag, ob, None, "chest")
        p.pivots[ob] = root
    socks = p.common_sockets()
    return p.finish(socks)


def homunculus_body():
    """The homunculus: made, not born. A big-headed little man of fired clay with an old face,
    a potter's leather apron, a brass-ringed stone of the field set in his chest."""
    p = SmallPerson("m", 0.19, {"head-age": 0.9, "eye-bag": 0.8, "nose-scale-horiz": 0.5, "nose-volume": 0.5, "ear-scale": 0.8, "mouth-angles": -0.5,
                               "head-fat": 0.4, "eyebrows-trans-down": 0.5, "chin-jaw-drop": 0.3, "head-round": 0.6}, stand=0.58, head=1.55, legs=0.7, arms=0.92)
    hb, J = p.hb, p.hb.J
    p.make_body(mat("clay"))
    p.eyes(mat("eye_dark"), field("eyes", 3.0), mat("eye_dark"))
    hipz, neckz, chestz = J["upperleg.l"].z, hb.trunk_z[9], J["chest"].z
    p.shell("apron", p.trunk_mask(hipz - 0.34, chestz + 0.16, front_only=True), mat("leather"), 0.035)
    p.shell("belt", p.trunk_mask(hipz + 0.1, hipz + 0.2), mat("clay_dark"), 0.045)
    p.shell("breeches", p.trunk_mask(hipz - 0.3, hipz + 0.12), mat("clay_dark"), 0.02)
    p.heart(field("heart", 3.0), rim=mat("metal_brass"), drop=-0.1)
    # the maker's seam: a line of the field over the crown, where the mould closed
    (x0, x1), (y0, y1), (z0, z1) = hb.head_box
    seam = [(0, y0 + (y1 - y0) * t, z1 - 0.004 - 0.5 * (z1 - z0) * (2 * t - 1) ** 2 * 0.35) for t in [0.18 + 0.07 * i for i in range(11)]]
    p.piece("mould_seam", g.tube(seam, [0.012] * 11, n=4), field("seam", 1.6), "head")
    socks = p.common_sockets()
    return p.finish(socks)


def imp_body(tall=False):
    """The ledger-imp: gaunt and ink-black, long-eared and grinning, the lines of its ledger
    ruled in light across its chest and arms, a rag at its hips and the book on its belt."""
    p = SmallPerson("m", 0.42 if tall else 0.25, {"ear-shape-pointed": 1.0, "ear-scale": 1.0, "ear-wing": 0.9, "head-invertedtriangular": 0.9, "chin-triangle": 1.0,
                                                   "chin-prominent": 0.6, "nose-hump": 0.8, "nose-point": -0.6, "nose-scale-vert": 0.5, "mouth-scale-horiz": 1.0,
                                                   "mouth-angles": 1.0, "eye-corner2": 0.9, "cheek-bones": 1.0, "cheek-volume": -0.8, "head-fat": -0.8,
                                                   "stomach-pregnant": 0.35},
                    build=(0.5, 0.5) if not tall else (0.3, 0.2), stand=0.64 if not tall else 0.82, keep_hands=True,
                    head=1.32 if not tall else 1.12, legs=0.82 if not tall else 1.0, arms=1.12)
    hb, J = p.hb, p.hb.J
    np = p.np
    p.make_body(mat("ink"))
    p.eyes(mat("eye_dark"), field("eyes", 4.0), mat("eye_dark"))
    hipz, neckz = J["upperleg.l"].z, hb.trunk_z[9]
    p.shell("rag", p.trunk_mask(hipz - 0.22, hipz + 0.14), mat("cloth_rag"), 0.03)
    # the ledger's lines: ruled round the chest, and down each arm
    arm, head = hb.is_arm, (hb.is_head | hb.is_neck)

    def ruled(v):
        on_trunk = (v[:, 2] > hipz + 0.2) & (v[:, 2] < neckz - 0.06) & ~arm & ~head & (np.mod(v[:, 2], 0.14) < 0.062)
        on_arm = arm & (np.abs(v[:, 0]) > J["upperarm.l"].x + 0.08) & (np.abs(v[:, 0]) < J["wrist.l"].x - 0.03) & (np.mod(np.abs(v[:, 0]), 0.14) < 0.062)
        return on_trunk | on_arm
    p.shell("script", ruled, field("script", 2.2), 0.008)
    # the book: on the left hip, strapped shut
    z, hw, hd, yo = hb.rings("trunk", "fit")[1]
    bx = hw + 0.05
    p.piece("ledger", g.box((bx, yo, hipz + 0.02), (0.07, 0.2, 0.26)), mat("leather"), "hips")
    p.piece("ledger_pages", g.box((bx + 0.004, yo - 0.008, hipz + 0.02), (0.05, 0.2, 0.23)), mat("paper"), "hips")
    p.piece("ledger_clasp", g.box((bx, yo - 0.1, hipz + 0.02), (0.085, 0.02, 0.06)), field("clasp", 2.0), "hips")
    socks = p.common_sockets()
    return p.finish(socks)


def set_origin(ob, at):
    """Move an object's origin to a point in the world without moving its shape."""
    M = ob.matrix_world.copy()
    new = M.copy()
    new.translation = V(at)
    inv = new.inverted()
    for v in ob.data.vertices:
        v.co = inv @ (M @ v.co)
    ob.matrix_world = new
    bpy.context.view_layer.update()


# ======================================================================================
# Second Forms a student can reach at the Gate: built from the same three families
# ======================================================================================

def stag_body():
    """The crowned stag: tall on fine legs, the neck long and carried high, a narrow head,
    hooves; antlers with the field at every point, and a ring of light held between them."""
    bk, r = _wolf()
    head = r.family("Head", "Ear1.L", "Ear1.R")
    r.leg_length(-0.5)
    r.leg_girth(0.8)
    top = r.top(r.bone("Torso2").y)
    r.scale(bk.TORSO, (0, 0, top), (0.95, 1.0, 1.06))
    r.lengthen_chain(bk.NECK, head, 1.35)
    r.rotate(bk.NECK + head, r.bone("Neck1"), X, math.radians(-24))
    r.rotate(head, r.bone("Neck3"), X, math.radians(20))
    r.scale(head, r.bone("Neck3"), (0.86, 1.0, 0.92))
    for ear, sg in (("Ear1.L", 1), ("Ear1.R", -1)):
        r.scale(r.family(ear), r.bone(ear), (1.0, 1.0, 1.25))
        r.rotate(r.family(ear), r.bone(ear), Y, sg * math.radians(48))
    r.scale(r.family("Tail1"), r.bone("Tail1"), 0.28)
    c = PALETTE
    r.recolor("Main", "hide_red", c["hide_red"][0], rough=0.9)
    r.recolor("Main_Light", "fur_cream", c["fur_cream"][0], rough=0.85)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.3, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "nose", c["nose"][0], rough=0.5)
    _flat(r)
    _hooves(r, mat("horn"))
    hb = r.bone("Head")
    crown = r.top(hb.y + 0.06, half_width=0.25)
    beams, points = None, None
    for sg in (1, -1):
        base = Vector((sg * 0.13, hb.y + 0.1, crown - 0.06))
        b1, b2, b3 = base + Vector((sg * 0.2, 0.2, 0.42)), base + Vector((sg * 0.42, 0.16, 0.86)), base + Vector((sg * 0.38, -0.1, 1.24))
        beams = g.merge(beams, g.tube([base, b1, b2, b3], [0.06, 0.05, 0.04, 0.014], n=5))
        tines = [(base + Vector((sg * 0.02, 0.02, 0.1)), base + Vector((sg * 0.1, -0.34, 0.3))), (b1, b1 + Vector((sg * 0.08, -0.34, 0.26))),
                 (b2, b2 + Vector((sg * 0.16, -0.26, 0.3))), (b2.lerp(b3, 0.5), b2.lerp(b3, 0.5) + Vector((sg * 0.2, 0.2, 0.28)))]
        for a, b in tines:
            beams = g.merge(beams, g.tube([a, a.lerp(b, 0.6) + Vector((0, 0, 0.03)), b], [0.036, 0.026, 0.01], n=5))
        for tip in [b3] + [b for _, b in tines]:
            points = g.merge(points, g.ico(tip, 0.035, sub=0))
    _add(r, "antlers", beams, "Head", mat("bone"))
    _add(r, "antler_points", points, "Head", field("points", 3.0))
    cz, cy = crown + 0.7, hb.y + 0.2
    loop = [(0.24 * math.cos(t), cy + 0.2 * math.sin(t), cz + 0.05 * math.sin(t)) for t in [2 * math.pi * i / 16 for i in range(17)]]
    _add(r, "crown", g.tube(loop, [0.022] * 17, n=4, caps=False), "Head", field("crown", 3.5))
    r.fin("seam_spine", r.bone("Torso3").y, r.bone("Tail1").y, 0.03, field("seam", 1.6), thickness=0.07, steps=14, sink=0.05)
    return _finish_wolf(r, coat=("hide_red", "fur_cream"), tail=False)


def harrier_body():
    """The harrier: the hawk come down to hunt on foot. A coursing beast, lean and deep in the
    chest on long legs, a narrow head, a crest of feathers from brow to shoulder, the forefeet
    armed with hooked claws, a fan of feathers for a tail."""
    bk, r = _wolf()
    head = r.family("Head", "Ear1.L", "Ear1.R")
    r.leg_length(-0.45)
    r.leg_girth(0.74)
    top = r.top(r.bone("Torso2").y)
    r.scale(bk.TORSO, (0, 0, top), (0.82, 1.0, 0.86))
    r.scale_along(head, r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.25)
    r.scale(head, r.bone("Neck3"), (0.84, 1.0, 0.9))
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), 0.35)
    c = PALETTE
    r.recolor("Main", "feather_dark", c["feather_dark"][0], rough=0.9)
    r.recolor("Main_Light", "feather_pale", c["feather_pale"][0], rough=0.85)
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.3, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "beak", c["beak"][0], rough=0.4)
    _flat(r)
    # the crest: feathers down the midline from the brow to the shoulders, the tallest on the crown
    crest, tips = None, None
    hb = r.bone("Head")
    stations = [(hb.y - 0.12, 0.3), (hb.y + 0.1, 0.52), (r.bone("Neck3").y, 0.5), (r.bone("Neck2").y, 0.42), (r.bone("Neck1").y, 0.36), (r.bone("Torso3").y, 0.28)]
    for y, L in stations:
        z = r.top(y, half_width=0.12) - 0.05
        for dx in (-0.07, 0.0, 0.07):
            base = Vector((dx, y, z))
            tip = base + Vector((dx * 1.5, L * 0.75, L * 0.7))
            crest = g.merge(crest, g.blade(base, tip, 0.15, normal=(dx * 4, -0.5, 1), belly=0.4))
            tips = g.merge(tips, g.blade(base.lerp(tip, 0.78), base.lerp(tip, 1.03), 0.09, normal=(dx * 4, -0.5, 1), belly=0.4, thick=0.02))
    _add(r, "crest", crest, "Neck3", mat("feather_mid"))
    _add(r, "crest_tips", tips, "Neck3", field("tips", 2.2))
    # the tail's fan
    tb = r.bone("Tail3")
    fan = None
    for i in range(5):
        a = math.radians(-30 + 15 * i)
        fan = g.merge(fan, g.blade(tb, tb + Vector((math.sin(a) * 0.8, math.cos(a) * 0.8, -0.1)), 0.2, normal=(0, 0, 1), belly=0.7))
    _add(r, "tail_fan", fan, "Tail3", mat("feather_mid"))
    # the ground-claws: three hooks on each forefoot
    claws = {}
    for foot, bone in (("FF.L", "FrontLowerLeg.L"), ("FF.R", "FrontLowerLeg.R")):
        f = r.bone(foot)
        geo = None
        for dx in (-0.09, 0.0, 0.09):
            geo = g.merge(geo, g.tongue([(f.x + dx, f.y - 0.12, 0.12), (f.x + dx * 1.3, f.y - 0.3, 0.17), (f.x + dx * 1.4, f.y - 0.4, 0.02)], [0.05, 0.04, 0.004], thick=0.7, normal=(0, 0, 1)))
        _add(r, "claws_" + foot, geo, bone, mat("talon"))
    r.fin("seam_spine", r.bone("Torso2").y, r.bone("Tail2").y, 0.03, field("seam", 1.6), thickness=0.07, steps=14, sink=0.05)
    return _finish_wolf(r, coat=("feather_dark", "feather_pale"))


def chord_body():
    """The chord: no body. Three rings of the field, each tilted from the last, turning about one
    bright note; smaller notes ride the rings, and a dark tine stands under them like a fork."""
    at = Vector((0, 0, 0.46))
    items = [(g.ico(at, 0.05, sub=1), field("core", 5.0))]
    notes = None
    for i, (rad, tilt, turn) in enumerate(((0.27, 0.25, 0.0), (0.2, 1.15, 0.7), (0.13, -1.0, 2.3))):
        M = Matrix.Rotation(turn, 3, "Z") @ Matrix.Rotation(tilt, 3, "X")
        loop = [at + M @ Vector((rad * math.cos(t), rad * math.sin(t), 0)) for t in [2 * math.pi * k / 20 for k in range(21)]]
        items.append((g.tube(loop, [0.013 - 0.002 * i] * 21, n=4, caps=False), field("ring_%d" % i, 2.6 - 0.5 * i)))
        for t in (0.6 + i, 3.4 + i * 1.7):
            notes = g.merge(notes, g.ico(at + M @ Vector((rad * math.cos(t), rad * math.sin(t), 0)), 0.03 - 0.004 * i, sub=0, scale=(1, 1, 1.4)))
    items.append((notes, field("note", 4.0)))
    fork = g.merge(g.tube([(0, 0, 0.05), (0, 0, 0.17)], [0.012, 0.014], n=5), g.tube([(0.0, 0, 0.17), (0.045, 0, 0.2), (0.045, 0, 0.31)], [0.012, 0.011, 0.007], n=5),
                   g.tube([(0.0, 0, 0.17), (-0.045, 0, 0.2), (-0.045, 0, 0.31)], [0.012, 0.011, 0.007], n=5))
    items.append((fork, mat("metal_dark")))
    ob = g.pieces("chord_body", items)
    socks = _sockets({
        "socket_head": [(0, 0, 0.76)], "socket_eyes": [(0, -0.06, 0.47)], "socket_mouth": [(0, -0.06, 0.42)], "socket_grip": [(0.2, 0, 0.44)],
        "socket_throat": [(0, -0.05, 0.36)], "socket_light": [(0, 0, 0.46)], "socket_back": [(0, 0.1, 0.48)], "socket_body": [(0, -0.08, 0.4)],
        "socket_tail": [(0, 0.1, 0.3)], "socket_arm_l": [(0.2, 0, 0.46)], "socket_arm_r": [(-0.2, 0, 0.46)],
        "socket_limb_fl": [(0.06, -0.04, 0.2)], "socket_limb_fr": [(-0.06, -0.04, 0.2)],
    })
    return Built([ob], socks)


def stooping_kith_body():
    """The stooping kith: a small warrior of the field, hooded and mantled in hawk's feathers,
    lean and quick, a jerkin of leather, the heart-light at the breast."""
    p = SmallPerson("m", 0.34, {"ear-shape-pointed": 1.0, "ear-scale": 0.7, "chin-triangle": 0.5, "nose-hump": 0.6, "eye-corner2": 0.6, "cheek-bones": 0.6,
                               "cheek-volume": -0.4}, build=(0.55, 0.35), stand=0.66, keep_hands=True, head=1.3, legs=0.92, arms=0.96)
    hb, J = p.hb, p.hb.J
    np = p.np
    p.make_body(mat("hand_skin"))
    p.eyes(field("eyes_dim", 1.2), field("eyes", 3.5), field("eyes", 3.5))
    hipz, neckz = J["upperleg.l"].z, hb.trunk_z[9]
    p.shell("jerkin", p.trunk_mask(hipz - 0.2, neckz - 0.03), mat("leather"), 0.03)
    p.shell("belt", p.trunk_mask(hipz + 0.1, hipz + 0.18), mat("clay_dark"), 0.045)
    (x0, x1), (y0, y1), (z0, z1) = hb.head_box
    eye = hb.eye["l"]
    head = hb.is_head
    p.shell("hood", lambda v: head & ((v[:, 2] > eye.z + 0.028) | (v[:, 1] > (y0 + y1) / 2 - 0.005)), mat("feather_dark"), 0.03)
    p.shell("leggings", p.trunk_mask(J["foot.l"].z + 0.1, hipz - 0.12), mat("clay_dark"), 0.018)
    # the hood's peak: a short hooked point over the brow, like a bill
    p.piece("hood_peak", g.tongue([(0, y0 + 0.07, z1 - 0.03), (0, y0 - 0.01, eye.z + 0.13), (0, y0 - 0.05, eye.z + 0.06)], [0.13, 0.09, 0.004], thick=0.4, normal=(0, -0.3, 1)), mat("feather_dark"), "head")
    # the mantle: two rows of feathers from the collar over the shoulders and down the back
    z, hw, hd, yo = hb.rings("trunk", "fit")[-1]
    for row, (n, L, out, m) in enumerate(((11, 0.36, 0.2, "feather_mid"), (10, 0.52, 0.15, "feather_dark"))):
        geo = None
        for i in range(n):
            a = math.radians(20 + 320 * i / (n - 1)) - math.pi / 2      # open at the throat
            d = Vector((math.cos(a), -math.sin(a), 0))
            base = Vector((d.x * (hw * 0.55), yo + d.y * (hd * 0.7), neckz + 0.02 - 0.03 * row))
            geo = g.merge(geo, g.blade(base, base + d * (out + 0.1 * abs(d.x)) + Vector((0, 0, -L)), 0.2, normal=d + Vector((0, 0, 0.6)), belly=0.5))
        p.piece("mantle_%d" % row, geo, mat(m), "chest")
    p.heart(field("heart", 3.0), drop=0.02)
    socks = p.common_sockets()
    return p.finish(socks, decimate=0.17)      # it wears more than the others: thin it further


BODIES = {
    "beast-crowned": stag_body,
    "beast-ground-hunter": harrier_body,
    "aspect-chord": chord_body,
    "kith-small-warrior": stooping_kith_body,
    "daemon-tall": lambda: imp_body(tall=True),
    "daemon-shadow": lambda: shadow_body(daemon=True),
    "kith-fey": sprite_body,
    "kith-homunculus": homunculus_body,
    "daemon-small": imp_body,
    "beast-flier": hawk_body,
    "engine-lantern": lantern_body,
    "aspect-flame": ember_body,
    "aspect-shadow": shadow_body,
    "beast-runner": field_wolf_body,
    "beast-grazer": ram_body,
    "beast-swimmer": otter_body,
    "engine-quadruped": hound_body,
}


# ======================================================================================
# Looking at them
# ======================================================================================

def _bounds(objects):
    lo, hi = Vector((9, 9, 9)), Vector((-9, -9, -9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if o.type != "MESH":
            continue
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        for v in me.vertices:
            w = oe.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        oe.to_mesh_clear()
    return lo, hi


def render(path, objects, rim=(0.42, 0.9, 0.55), res=(768, 1024), samples=48, view=(0.8, -1.25, 0.35), card=True, zoom=1.0):
    """The card's portrait (dark ground, a rim of the field's colour from behind, a warm key),
    or with card=False a plain lit look for judging the form."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    world = scene.world or bpy.data.worlds.new("card")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.014, 0.012, 0.016, 1) if card else (0.05, 0.055, 0.07, 1)
    lo, hi = _bounds(objects)
    centre = (lo + hi) / 2
    size = max((hi - lo).length, 0.3)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 60
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    d = V(view).normalized()
    aspect = res[0] / res[1]
    right = Vector((0, 0, 1)).cross(d).normalized()
    up = d.cross(right).normalized()
    hx = hy = hz = 0.0
    for cx in (lo.x, hi.x):
        for cy in (lo.y, hi.y):
            for cz in (lo.z, hi.z):
                q = Vector((cx, cy, cz)) - centre
                hx, hy, hz = max(hx, abs(q.dot(right))), max(hy, abs(q.dot(up))), max(hz, abs(q.dot(d)))
    tan_v = 18.0 / cam_data.lens if aspect < 1 else 18.0 / cam_data.lens / aspect
    cam.location = centre + d * ((max(hy / tan_v, hx / (tan_v * aspect)) * 1.02 + hz * 0.6) / zoom)
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    # a ground to stand on, a little below, so the form has a place
    bpy.ops.mesh.primitive_plane_add(size=40, location=(centre.x, centre.y, min(lo.z, 0.0) - 0.002))
    ground = bpy.context.active_object
    ground.data.materials.append(mat("card_ground", (0.02, 0.018, 0.022) if card else (0.09, 0.09, 0.1), rough=0.6))

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
    s2 = size * size
    if card:
        light("key", "AREA", centre + Vector((-size * 1.4, -size * 1.6, size * 1.3)), (1.0, 0.8, 0.58), 19 * s2, size)
        light("rim", "AREA", centre + Vector((size * 0.9, size * 1.6, size * 1.0)), rim, 70 * s2, size * 0.8)
        light("fill", "AREA", centre + Vector((size * 1.7, -size * 0.7, size * 0.1)), (0.5, 0.6, 0.95), 4.5 * s2, size)
    else:
        light("key", "AREA", centre + Vector((-size * 1.2, -size * 1.8, size * 1.6)), (1.0, 0.95, 0.88), 110 * s2, size * 1.5)
        light("fill", "AREA", centre + Vector((size * 1.8, -size * 0.8, size * 0.6)), (0.75, 0.82, 1.0), 40 * s2, size * 1.5)
        light("rim", "AREA", centre + Vector((size * 0.6, size * 1.8, size * 1.2)), rim, 60 * s2, size)
    # the field's materials in the Shape's colour, as the game shows them, never washed to white
    for m in bpy.data.materials:
        if m.name.startswith("field") and m.use_nodes:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                st = bsdf.inputs["Emission Strength"].default_value
                bsdf.inputs["Emission Color"].default_value = (rim[0], rim[1], rim[2], 1)
                bsdf.inputs["Emission Strength"].default_value = min(1.1, st * 0.22 + 0.3)
                bsdf.inputs["Base Color"].default_value = (rim[0] * 0.25, rim[1] * 0.25, rim[2] * 0.25, 1)
    scene.view_settings.view_transform = "Filmic" if "Filmic" in [i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "AgX"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    log("rendered", path)


def hang(part_objects, socket, mirror=False):
    """Put a part's objects on a socket, as the game does."""
    M = socket.matrix_world.copy()
    if mirror:
        M = M @ Matrix.Diagonal((-1, 1, 1, 1))
    for o in part_objects:
        o.matrix_world = M @ o.matrix_world
    return part_objects


def tile(paths, out, cols, cell):
    """A contact sheet: each picture scaled to a cell, in rows."""
    import numpy as np
    w, h = cell
    rows = (len(paths) + cols - 1) // cols
    sheet_px = np.zeros((rows * h, cols * w, 4), dtype=np.float32)
    sheet_px[..., 3] = 1.0
    for i, path in enumerate(paths):
        img = bpy.data.images.load(path)
        if tuple(img.size) != (w, h):
            img.scale(w, h)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        r, c = i // cols, i % cols
        y0 = (rows - 1 - r) * h
        sheet_px[y0:y0 + h, c * w:c * w + w] = px
        bpy.data.images.remove(img)
    img = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    img.pixels = sheet_px.ravel().tolist()
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    log("wrote", out)


# ======================================================================================
# Parts: one per feature, modelled at its socket's origin (docs/genius-forms.md has the
# frames). A part of a pair is modelled for the character's left; the game mirrors it.
# ======================================================================================

def _part(name, items, pivot=None):
    ob = g.pieces(name, items)
    if pivot is not None:
        set_origin(ob, pivot)
    return ob


def wings_part():
    """Two wings, each a bone with three ranks of feathers: coverts, secondaries, and long
    fingered primaries with the field at their tips. They pivot at the shoulder."""
    dark, mid, pale = mat("feather_dark"), mat("feather_mid"), mat("feather_pale")
    out = []
    for tag, sg in (("l", 1), ("r", -1)):
        sh = Vector((sg * 0.055, 0.0, -0.02))
        el, wr, tip = sh + Vector((sg * 0.2, -0.05, 0.03)), sh + Vector((sg * 0.42, -0.085, 0.03)), sh + Vector((sg * 0.6, -0.02, 0.01))
        items = [(g.tube([sh, el, wr, tip], [0.024, 0.02, 0.015, 0.006], n=5), dark)]
        sec, cov, prim, tips = None, None, None, None
        up = Vector((0, 0, 1))
        # secondaries: from the shoulder to the wrist, pointing back
        for i in range(8):
            t = i / 7.0
            base = (sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)) + Vector((0, 0.01, -0.004))
            L = 0.2 + 0.07 * math.sin(t * math.pi)
            sec = g.merge(sec, g.blade(base, base + Vector((sg * 0.03 * t, L, -0.02)), 0.075, normal=up, belly=0.6, thick=0.008))
        # coverts over their roots
        for i in range(9):
            t = i / 8.0
            base = (sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)) + Vector((0, -0.005, 0.008))
            cov = g.merge(cov, g.blade(base, base + Vector((sg * 0.02 * t, 0.1 + 0.02 * (i % 2), 0.0)), 0.06, normal=up, belly=0.5, thick=0.012))
        # primaries: fingers fanned from the wrist
        for i in range(7):
            a = math.radians(84 - 13 * i)
            d = Vector((sg * math.cos(a), math.sin(a), -0.04))
            L = 0.26 + 0.045 * math.sin((i + 1) / 8.0 * math.pi)
            base = wr.lerp(tip, i / 9.0) + Vector((0, 0.005, -0.004))
            prim = g.merge(prim, g.blade(base, base + d * L, 0.052, normal=up, belly=0.55, thick=0.007))
            tips = g.merge(tips, g.blade(base + d * L * 0.8, base + d * L * 1.03, 0.04, normal=up, belly=0.4, thick=0.009))
        items += [(sec, mid), (prim, dark), (cov, dark), (tips, field("tips", 2.5))]
        # a pale bar across the secondaries
        bar = None
        for i in range(8):
            t = i / 7.0
            base = (sh.lerp(el, t * 2) if t < 0.5 else el.lerp(wr, t * 2 - 1)) + Vector((sg * 0.012 * t, 0.115, -0.006))
            bar = g.merge(bar, g.blade(base, base + Vector((0, 0.045, -0.004)), 0.06, normal=up, belly=0.5, thick=0.01))
        items.append((bar, pale))
        out.append(_part("wing_" + tag, items, pivot=sh))
    return out


def beak_part():
    """A raptor's bill: the upper mandible hooked over the lower, dark at the point."""
    upper = g.tongue([(0, 0.012, 0.008), (0, -0.03, 0.006), (0, -0.058, -0.012)], [0.04, 0.034, 0.02], thick=0.8, normal=(0, 0, 1))
    hook = g.tongue([(0, -0.054, -0.01), (0, -0.07, -0.028), (0, -0.064, -0.05)], [0.02, 0.014, 0.002], thick=0.8, normal=(0, -1, 0.3))
    lower = g.tongue([(0, 0.01, -0.012), (0, -0.03, -0.018), (0, -0.05, -0.022)], [0.03, 0.024, 0.004], thick=0.5, normal=(0, 0, -1))
    return [_part("beak", [(upper, mat("beak")), (lower, mat("beak")), (hook, mat("talon"))])]


def talons_part():
    """A raptor's foot: three toes forward and one back, each ending in a hooked claw."""
    toes, claws = None, None
    for dx, dy in ((0.02, -0.03), (0.0, -0.04), (-0.02, -0.03), (0.0, 0.03)):
        mid = Vector((dx, dy, -0.012))
        toes = g.merge(toes, g.tube([(0, 0, 0), mid], [0.01, 0.008], n=4))
        claws = g.merge(claws, g.tongue([mid, mid + Vector((dx * 0.5, dy * 0.5, -0.016)), mid + Vector((dx * 0.35, dy * 0.35, -0.04))], [0.012, 0.009, 0.001], thick=0.7))
    return [_part("talons", [(toes, mat("beak")), (claws, mat("talon"))])]


def far_eyes_part():
    """Eyes that see far: a brass band across the brow carrying a great lens over the left
    eye, and two small eyes of the field above."""
    brass = mat("metal_brass")
    band = [(0.075 * math.sin(t), -0.004 - 0.02 * math.cos(t) + 0.02, 0.022) for t in [math.radians(-70 + 14 * i) for i in range(11)]]
    rim = [(0.036 + 0.026 * math.cos(t), -0.012, 0.0 + 0.026 * math.sin(t)) for t in [math.radians(30 * i) for i in range(13)]]
    items = [(g.tube(band, [0.006] * 11, n=4, flat=1.8), brass), (g.tube(rim, [0.006] * 13, n=4, caps=False), brass),
             (g.ico((0.036, -0.012, 0.0), 0.023, sub=1, scale=(1, 0.3, 1)), field("lens", 2.2)),
             (g.tube([(0.036, -0.012, 0.026), (0.03, -0.002, 0.03)], [0.005, 0.005], n=4), brass)]
    eyes = None
    for sx in (-0.022, 0.018):
        eyes = g.merge(eyes, g.ico((sx, -0.008, 0.045), 0.009, sub=1, scale=(1.2, 0.6, 0.8)))
    items.append((eyes, field("eyes", 3.0)))
    return [_part("far_eyes", items)]


def horn_brow_part():
    """A ram's horns: each rises from the brow, sweeps back and down behind the ear and round
    to the front again, ridged all the way, pale at the point; a low plate of brow between."""
    horn, ridge = mat("horn_ridge"), mat("horn")
    c = Vector((0.074, 0.03, -0.085))
    n = 16
    pts, radii = [], []
    for i in range(n + 1):
        t = i / float(n)
        a = -0.9 + 2 * math.pi * 1.2 * t          # 0 is up; it turns back (+Y), down, then forward
        rr = 0.1 - 0.046 * t
        pts.append(c + Vector((0.014 + 0.095 * t * t, math.sin(a) * rr, math.cos(a) * rr)))
        radii.append(0.041 * (1 - t) ** 0.8 * (1.0 if i % 2 == 0 else 0.86) + 0.003)
    left = g.tube(pts[:-3], radii[:-3], n=6)
    tipl = g.tube(pts[-4:], [radii[-4] * 1.02, radii[-3], radii[-2], 0.002], n=6)
    brow = g.tongue([(0, 0.04, 0.0), (0, -0.01, 0.004), (0, -0.07, -0.022)], [0.09, 0.11, 0.06], thick=0.25, normal=(0, -0.3, 1))
    return [_part("horn_brow", [(g.merge(left, g.mirrored(left)), horn), (g.merge(tipl, g.mirrored(tipl)), mat("bone")), (brow, ridge)])]


def horns_part():
    """A daemon's horns: short, swept up and back, ringed."""
    left = g.tube([(0.034, 0.0, -0.012), (0.058, 0.008, 0.04), (0.06, 0.032, 0.085), (0.046, 0.06, 0.12)], [0.02, 0.016, 0.011, 0.002], n=5)
    ring = g.tube([(0.04, 0.002, 0.0), (0.045, 0.004, 0.012)], [0.024, 0.022], n=5)
    return [_part("horns", [(g.merge(left, g.mirrored(left)), mat("horn")), (g.merge(ring, g.mirrored(ring)), field("ring", 1.6))])]


def broad_chest_part():
    """A breastplate grown on: a keeled plate over the chest with a seam of the field down it."""
    plate = g.tongue([(0, 0.01, 0.1), (0, -0.022, 0.03), (0, -0.018, -0.05), (0, 0.012, -0.12)], [0.15, 0.23, 0.19, 0.06], thick=0.3, normal=(0, -1, 0))
    seam = g.tongue([(0, -0.03, 0.07), (0, -0.05, 0.0), (0, -0.036, -0.09)], [0.014, 0.018, 0.004], thick=0.6, normal=(0, -1, 0))
    studs = None
    for sx, sz in ((0.075, 0.05), (-0.075, 0.05), (0.06, -0.045), (-0.06, -0.045)):
        studs = g.merge(studs, g.ico((sx, -0.03, sz), 0.012, sub=0))
    return [_part("broad_chest", [(plate, mat("stone_plate")), (seam, field("seam", 1.8)), (studs, mat("bone"))])]


def long_legs_part():
    """A spur of bone up the back of each leg, a bead of the field at its root."""
    spur = g.tongue([(0, 0.014, 0.0), (0, 0.03, 0.07), (0, 0.022, 0.17)], [0.03, 0.022, 0.003], thick=0.6, normal=(0, 1, 0))
    return [_part("long_legs", [(spur, mat("bone")), (g.ico((0, 0.02, 0.012), 0.011, sub=0), field("bead", 2.5))])]


def fangs_part():
    """Two long fangs from the upper jaw."""
    left = g.tongue([(0.024, 0.006, 0.004), (0.026, -0.004, -0.028), (0.021, 0.004, -0.058)], [0.016, 0.011, 0.001], thick=0.7, normal=(1, 0, 0))
    return [_part("fangs", [(g.merge(left, g.mirrored(left)), mat("bone"))])]


def fins_part():
    """A fin at the heel: three rays and the web between them."""
    rays, web = None, None
    tips = [Vector((0.03, 0.085, 0.055)), Vector((0.0, 0.1, 0.03)), Vector((-0.03, 0.085, 0.01))]
    root = Vector((0, 0.012, 0.03))
    for t in tips:
        rays = g.merge(rays, g.tube([root, t], [0.008, 0.002], n=4))
    for a, b in zip(tips, tips[1:]):
        web = g.merge(web, g.blade(root, (a + b) / 2 * 0.94 + root * 0.06, (a - b).length * 0.8, normal=(a - root).cross(b - root), belly=0.75, thick=0.003))
    return [_part("fins", [(rays, mat("fur_sleek")), (web, field("web", 1.0))])]


def small_hands_part():
    """Small clever hands: a real hand (the human's own, at a child's size) under a cuff.
    Modelled hanging from the wrist: the fingers down, the palm to -X, the thumb to the front."""
    import numpy as np
    import human as hu
    h = hu.Human("m", {"african": 0.34, "asian": 0.33, "caucasian": 0.33}, build=(0.4, 0.4), height=2.4, age=0.3, proportions=0.5)
    base = h.base
    names = np.empty(hu.BODY_VERTS, dtype=object)
    best = np.zeros(hu.BODY_VERTS)
    for b, (idx, w) in base.weights.items():
        keep = idx < hu.BODY_VERTS
        i, x = idx[keep], w[keep]
        better = x > best[i]
        best[i[better]] = x[better]
        names[i[better]] = b
    hand = np.array([(nm or "").endswith("_l") and (nm or "").split("_")[0] in ("hand", "index", "middle", "ring", "pinky", "thumb") for nm in names])
    faces = [f for f in base.body_faces if all(hand[i] for i in f)]
    used = sorted({i for f in faces for i in f})
    remap = {i: j for j, i in enumerate(used)}
    wrist = Vector(h.joint("joint-l-hand"))
    R = HAND_ON_ARM_L.transposed()          # the world's T-pose arm into the part's hanging frame
    k = 0.3
    verts = [R @ (Vector(h.v[i]) - wrist) * k for i in used]
    geo = (verts, [tuple(remap[i] for i in f) for f in faces])
    hand_ob = g.to_object("hand", geo, mat("hand_skin"), smooth=False)
    # thin it: a part's budget is small
    bpy.ops.object.select_all(action="DESELECT")
    hand_ob.select_set(True)
    bpy.context.view_layer.objects.active = hand_ob
    dec = hand_ob.modifiers.new("Decimate", "DECIMATE")
    dec.ratio = 0.3
    bpy.ops.object.modifier_apply(modifier="Decimate")
    hand_ob.select_set(False)
    cuff = g.to_object("cuff", g.lathe([(0.017, 0.012), (0.021, 0.008), (0.021, -0.006), (0.017, -0.01)], n=8), mat("metal_brass"))
    bead = g.to_object("cuff_bead", g.ico((0, -0.021, 0.001), 0.006, sub=0), field("bead", 2.5))
    return [g.join("small_hands", [hand_ob, cuff, bead])]


def lantern_part():
    """A hand lantern on two links of chain: four posts, a peaked cap, the field for its flame."""
    brass, dark = mat("metal_brass"), mat("metal_dark")
    items = []
    ring = [(0.012 * math.cos(t), 0, -0.012 + 0.012 * math.sin(t)) for t in [math.radians(40 * i) for i in range(10)]]
    link = [(0, 0.008 * math.cos(t), -0.034 + 0.01 * math.sin(t)) for t in [math.radians(40 * i) for i in range(10)]]
    items.append((g.merge(g.tube(ring, [0.003] * 10, n=3, caps=False), g.tube(link, [0.003] * 10, n=3, caps=False)), dark))
    items.append((g.lathe([(0.004, -0.045), (0.034, -0.062), (0.036, -0.068)], n=4, phase=math.pi / 4), brass))
    posts = None
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        posts = g.merge(posts, g.tube([(sx * 0.022, sy * 0.022, -0.068), (sx * 0.022, sy * 0.022, -0.128)], [0.0035, 0.0035], n=3))
    items.append((posts, brass))
    items.append((g.lathe([(0.036, -0.128), (0.036, -0.136), (0.02, -0.142)], n=4, phase=math.pi / 4), brass))
    items.append((g.ico((0, 0, -0.1), 0.017, sub=1, scale=(0.85, 0.85, 1.3)), field("flame", 5.0)))
    return [_part("lantern", items)]


def voice_part():
    """A voice you can see: a small bell at the throat and two arcs of sound before it."""
    brass = mat("metal_brass")
    items = [(g.lathe([(0.004, 0.0), (0.012, -0.006), (0.018, -0.024), (0.024, -0.032)], n=6, caps=False), brass),
             (g.ico((0, 0, -0.034), 0.007, sub=0), field("clapper", 3.0))]
    arcs = None
    for rad, y in ((0.034, -0.03), (0.05, -0.05)):
        arc = [(rad * math.sin(t), y - 0.012 * math.cos(t), -0.02 + rad * 0.55 * math.cos(t) - rad * 0.3) for t in [math.radians(-60 + 15 * i) for i in range(9)]]
        arcs = g.merge(arcs, g.tube(arc, [0.004] * 9, n=3))
    items.append((arcs, field("voice", 2.5)))
    return [_part("voice", items)]


def brush_part():
    """A writing brush, held: a wooden shaft, a brass ferrule, the bristles wet with the field."""
    items = [(g.tube([(0, 0, 0.12), (0, 0, -0.045)], [0.007, 0.009], n=6), mat("wood")),
             (g.tube([(0, 0, -0.04), (0, 0, -0.06)], [0.011, 0.012], n=6), mat("metal_brass")),
             (g.tongue([(0, 0, -0.058), (0, 0, -0.085), (0, 0, -0.118)], [0.024, 0.028, 0.014], thick=1.0, normal=(0, 1, 0)), mat("bristle")),
             (g.tongue([(0, 0, -0.112), (0, 0, -0.14)], [0.015, 0.001], thick=1.0, normal=(0, 1, 0)), field("ink", 2.5)),
             (g.ico((0, 0, 0.125), 0.009, sub=0), mat("metal_brass"))]
    return [_part("brush", items)]


def old_eyes_part():
    """Old eyes: round spectacles in brass wire, their glass faintly lit, pinched on the nose."""
    brass = mat("metal_brass")
    wire, glass = None, None
    for sgn in (1, -1):
        rim = [(sgn * 0.024 + 0.018 * math.cos(t), -0.01, 0.018 * math.sin(t)) for t in [math.radians(30 * i) for i in range(13)]]
        wire = g.merge(wire, g.tube(rim, [0.003] * 13, n=4, caps=False), g.tube([(sgn * 0.041, -0.01, 0.002), (sgn * 0.058, 0.02, 0.006)], [0.0025, 0.0025], n=3))
        glass = g.merge(glass, g.ico((sgn * 0.024, -0.009, 0), 0.016, sub=1, scale=(1, 0.18, 1)))
    wire = g.merge(wire, g.tube([(-0.008, -0.011, 0.006), (0, -0.014, 0.011), (0.008, -0.011, 0.006)], [0.003, 0.003, 0.003], n=4))
    return [_part("old_eyes", [(wire, brass), (glass, field("lens", 1.2))])]


def roots_part():
    """Roots for feet: four tendrils feeling outward over the ground."""
    geo = None
    for i, a in enumerate((0.3, 1.9, 3.4, 4.9)):
        d = Vector((math.cos(a), math.sin(a), 0))
        geo = g.merge(geo, g.tube([(0, 0, 0.03), d * 0.04 + Z * 0.012, d * (0.08 + 0.02 * (i % 2)) + Z * 0.004, d * 0.11 + Vector((0.01 * math.sin(i), 0.01, 0.0))], [0.012, 0.009, 0.005, 0.001], n=4))
    return [_part("roots", [(geo, mat("root")), (g.ico((0, 0, 0.03), 0.012, sub=0), field("bead", 2.0))])]


def cold_core_part():
    """A cold core: shards of ice-pale light standing round the heart of the lantern."""
    shards = None
    for i in range(5):
        a = 2 * math.pi * i / 5
        base = Vector((0.045 * math.cos(a), 0.045 * math.sin(a), -0.135))
        shards = g.merge(shards, g.blade(base, base + Vector((0.012 * math.cos(a), 0.012 * math.sin(a), 0.05 + 0.02 * (i % 2))), 0.02, normal=(math.cos(a), math.sin(a), 0), belly=0.35, thick=0.008))
    return [_part("cold_core", [(shards, field("cold", 2.0))])]


def tail_part():
    """A daemon's tail: long, curling up, a barb of the field at its end."""
    pts = [(0, 0.0, 0.0), (0, 0.07, -0.035), (0, 0.15, -0.04), (0, 0.215, 0.0), (0, 0.235, 0.065), (0, 0.205, 0.115)]
    barb = g.blade((0, 0.205, 0.11), (0, 0.165, 0.17), 0.05, normal=(1, 0, 0), belly=0.4, thick=0.012)
    return [_part("tail", [(g.tube(pts, [0.016, 0.014, 0.012, 0.01, 0.008, 0.006], n=5), mat("ink")), (barb, field("barb", 2.2))])]


def ember_part():
    """An ember carried: a coal split open on the field, three small flames standing on it."""
    items = [(g.ico((0, 0, -0.01), 0.03, sub=0, scale=(1.1, 1.0, 0.8)), mat("coal")), (g.ico((0, 0, -0.004), 0.021, sub=0), field("crack", 4.0))]
    fl = None
    for i, a in enumerate((0.4, 2.5, 4.6)):
        fl = g.merge(fl, g.tongue([(0.012 * math.cos(a), 0.012 * math.sin(a), 0.01), (0.02 * math.cos(a + 0.4), 0.02 * math.sin(a + 0.4), 0.04), (0.006 * math.cos(a + 1.0), 0.006 * math.sin(a + 1.0), 0.075 + 0.012 * i)], [0.02, 0.024, 0.002], thick=0.5))
    items.append((fl, field("flame", 4.0)))
    return [_part("ember", items)]


def glow_part():
    """A glow: a broken ring of the field's light, tilted, with motes on it."""
    arcs, motes = None, None
    for i in range(4):
        a0 = 2 * math.pi * i / 4 + 0.2
        arc = [(0.17 * math.cos(a0 + t), 0.17 * math.sin(a0 + t), 0.03 * math.sin(a0 + t)) for t in [0.2 * j for j in range(6)]]
        arcs = g.merge(arcs, g.tube(arc, [0.002, 0.006, 0.007, 0.007, 0.006, 0.002], n=4))
        motes = g.merge(motes, g.ico((0.17 * math.cos(a0 + 1.25), 0.17 * math.sin(a0 + 1.25), 0.03 * math.sin(a0 + 1.25)), 0.009, sub=0))
    return [_part("glow", [(arcs, field("glow", 2.0)), (motes, field("mote", 3.0))])]


def short_blade_part():
    """A short leaf-bladed knife, held point forward: a wrapped grip, a brass guard, an edge of the field."""
    blade = g.tongue([(0, 0, -0.03), (0, 0, -0.09), (0, 0, -0.2)], [0.03, 0.042, 0.002], thick=0.25, normal=(1, 0, 0))
    edge = g.tongue([(0, -0.012, -0.05), (0, -0.02, -0.1), (0, -0.002, -0.2)], [0.006, 0.006, 0.001], thick=0.9, normal=(1, 0, 0))
    items = [(g.tube([(0, 0, 0.06), (0, 0, -0.02)], [0.009, 0.01], n=6), mat("leather")), (g.box((0, 0, -0.025), (0.016, 0.06, 0.012)), mat("metal_brass")),
             (blade, mat("metal_iron_light")), (edge, field("edge", 2.0)), (g.ico((0, 0, 0.066), 0.012, sub=0), mat("metal_brass"))]
    return [_part("short_blade", items)]


def chain_part():
    """A chain from the wrist: six links hanging, a seal of the field at the end."""
    links = None
    for i in range(6):
        z = -0.02 - 0.03 * i
        loop = [((0.011 * math.cos(t)) if i % 2 == 0 else 0.0, (0.011 * math.cos(t)) if i % 2 else 0.0, z + 0.018 * math.sin(t)) for t in [math.radians(45 * k) for k in range(9)]]
        links = g.merge(links, g.tube(loop, [0.0042] * 9, n=3, caps=False))
    seal = g.ico((0, 0, -0.215), 0.022, sub=0, scale=(1.0, 0.4, 1.2))
    return [_part("chain", [(links, mat("metal_dark")), (seal, field("seal", 2.5))])]


def gears_part():
    """Works showing at the breast: a brass cog and a smaller iron one meshed with it, a jewel
    of the field at the hub."""
    def cog(c, r, teeth, depth, material):
        c = Vector(c)
        geo = g.tube([c + Vector((0, 0.0, 0)), c + Vector((0, -depth, 0))], [r, r], n=teeth)
        for i in range(teeth):
            a = 2 * math.pi * (i + 0.5) / teeth
            geo = g.merge(geo, g.box(c + Vector((math.cos(a) * r * 1.08, -depth / 2, math.sin(a) * r * 1.08)), (r * 0.32, depth * 0.9, r * 0.32), rot=(0, -a, 0)))
        return (geo, material)
    items = [cog((0.0, -0.012, 0.0), 0.062, 10, 0.022, mat("metal_brass")), cog((0.085, -0.014, -0.045), 0.036, 7, 0.018, mat("metal_iron_light")),
             (g.ico((0, -0.04, 0), 0.018, sub=0), field("hub", 3.0)), (g.ico((0.085, -0.036, -0.045), 0.01, sub=0), mat("metal_brass"))]
    return [_part("gears", items)]


PARTS = {"short-blade": short_blade_part, "chain": chain_part, "gears": gears_part,
         "wings": wings_part, "beak": beak_part, "talons": talons_part, "far-eyes": far_eyes_part, "horn-brow": horn_brow_part, "horns": horns_part,
         "broad-chest": broad_chest_part, "long-legs": long_legs_part, "fangs": fangs_part, "fins": fins_part, "small-hands": small_hands_part,
         "lantern": lantern_part, "voice": voice_part, "brush": brush_part, "old-eyes": old_eyes_part, "roots": roots_part, "cold-core": cold_core_part,
         "tail": tail_part, "ember": ember_part, "glow": glow_part}


# ======================================================================================
# Forms: a body, its parts on their sockets, a card
# ======================================================================================

def _data(name):
    with open(os.path.join(ROOT, "data", name + ".json")) as f:
        return json.load(f)


def form_spec(form_id):
    return next(x for x in _data("forms") if x["id"] == form_id)


def sockets_for(feature, built):
    """The sockets a feature's part hangs on, as the game chooses them (genius_body.gd)."""
    cfg = _data("genius-bodies")
    named = [sn for sn in cfg.get("featureSockets", {}).get(feature, []) if sn in built.sockets]
    if named:
        return named
    slot = next((f["slot"] for f in _data("features") if f["id"] == feature), "body")
    socks = cfg["slotSockets"].get(slot, [])
    have = [sn for sn in socks if sn in built.sockets]
    if not have:
        return []
    return have if len(socks) > 1 else have[:1]


def is_right(socket_name):
    return socket_name.endswith("_r") or socket_name.endswith("fr") or socket_name.endswith("br")


def assemble(form_id):
    """The form in one scene: its body built, posed, and every part it has art for hung."""
    spec = form_spec(form_id)
    reset()
    built = BODIES[spec["silhouette"]]()
    if built.pose:
        built.pose()
    shown = [o for o in built.objects if o.type == "MESH"]
    carried = _data("genius-bodies")["silhouettes"].get(spec["silhouette"], {}).get("carries", [])
    for feature in spec["features"]:
        if feature not in PARTS or feature in carried:
            continue
        for sn in sockets_for(feature, built):
            objs = PARTS[feature]()
            hang(objs, built.sockets[sn], mirror=is_right(sn))
            shown += objs
    # wings are drawn lifted, as the game beats them (the left about the way it faces)
    for o in list(bpy.data.objects):
        if o.name in ("wing_l", "wing_r") and o.type == "MESH" and built.arm is None:
            o.matrix_world = o.matrix_world @ Matrix.Rotation((-1 if o.name == "wing_l" else 1) * 0.7, 4, "Y")
    bpy.context.view_layer.update()
    return built, shown


def build_body(silhouette):
    reset()
    built = BODIES[silhouette]()
    return built.export(os.path.join(OUT, "bodies", silhouette + ".glb"))


def build_part(feature):
    reset()
    objs = PARTS[feature]()
    path = os.path.join(OUT, "parts", feature + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    log("wrote", os.path.relpath(path, ROOT), "%d triangles" % tris)
    return tris


SHAPE_RIMS = {"beast": (0.95, 0.68, 0.25), "kith": (0.5, 1.0, 0.6), "engine": (1.0, 0.42, 0.15), "daemon": (0.75, 0.45, 1.0), "aspect": (0.55, 0.85, 1.0), "relic": (0.85, 0.85, 1.0)}


CARD_VIEWS = {"hawk": (1.15, -0.95, 0.3), "griffin": (1.15, -0.95, 0.3), "crow": (1.15, -0.95, 0.3), "storm-crow": (1.15, -0.95, 0.3), "thinking-gun": (1.3, -0.75, 0.3),
              "clockwork-wren": (1.1, -1.0, 0.3), "brass-kite": (1.1, -1.0, 0.3), "tortoise": (0.95, -1.15, 0.4), "cairn-back": (0.95, -1.15, 0.4), "wisp-train": (1.2, -0.9, 0.25)}
CARD_ZOOM = {"hawk": 1.3, "griffin": 1.3, "crow": 1.3, "storm-crow": 1.3, "clockwork-wren": 1.2, "brass-kite": 1.2, "tortoise": 1.15, "cairn-back": 1.15}      # a spread of wings leaves the box around it mostly empty


def build_card(form_id, path=None, res=(768, 1024), samples=48, card=True, view=None):
    view = view or CARD_VIEWS.get(form_id, (0.8, -1.25, 0.35))
    built, shown = assemble(form_id)
    spec = form_spec(form_id)
    path = path or os.path.join(OUT, "cards", form_id + ".png")
    render(path, shown, rim=SHAPE_RIMS.get(spec.get("expression", ""), (0.42, 0.9, 0.55)), res=res, samples=samples, card=card, view=view, zoom=CARD_ZOOM.get(form_id, 1.0))
    return path


FIRST_FORMS = ["hawk", "ram", "field-wolf", "otter", "lantern-sprite", "homunculus", "iron-hound", "walking-lantern", "ledger-imp", "ember", "shadow"]


def forms_with_art():
    """The forms the kit draws: First and Second Forms whose silhouette has a body here. (A
    later form may wear one of these bodies in the game until it has its own, but it gets no
    card that would show it as something it is not.)"""
    return [f["id"] for f in _data("forms") if f["silhouette"] in BODIES and int(f["instars"]["min"]) <= 2]


def sheet(forms=None, out=None, cell=(384, 512)):
    paths = [os.path.join(OUT, "cards", f + ".png") for f in (forms or forms_with_art())]
    paths = [p for p in paths if os.path.exists(p)]
    tile(paths, out or os.path.join(SCRATCH, "genius_sheet.png"), 6, cell)


def _more():
    """The second set of forms, the relics, the parts added with them and the keepsakes."""
    import genius_forms2
    import genius_relics
    kit = sys.modules[__name__]
    genius_forms2.register(kit)
    genius_relics.register(kit)


KEEPSAKES = {}
_more()


if __name__ == "__main__":
    # no arguments: every body, every part, every card, the sheet. Otherwise any of:
    # bodies | parts | cards | sheet | <form id>... (a form id builds that form's body and card),
    # or: keepsakes (the keepsakes), or: looks <form> [n] (a sheet of one form's looks)
    args = sys.argv[1:]
    if args and args[0] == "keepsakes":
        import genius_relics
        for kid in KEEPSAKES:
            genius_relics.build_keepsake(kid)
        sys.exit(0)
    if args and args[0] == "looks":
        # looks <form> [how many]: one form in a spread of the looks the game would give it
        import genius_relics
        n = int(args[2]) if len(args) > 2 else 8
        worn = ["", "collar", "ribbon", "charm", "bell"]
        tints = ["oxblood", "indigo", "moss", "ochre", "bone"]
        looks = [{"seed": 1000003 * (i + 1) + 77 * i * i, "coat": 0, "marks": {}, "keepsake": worn[i % 5], "keepsakeColor": tints[i % 5]} for i in range(n)]
        genius_relics.look_sheet(args[1], looks, os.path.join(SCRATCH, "genius_looks_%s.png" % args[1]))
        sys.exit(0)
    words = [a for a in args if a in ("bodies", "parts", "cards", "sheet")]
    forms = [a for a in args if a not in words] or forms_with_art()
    everything = not args
    if everything or "bodies" in words or (forms and not words):
        sils = []
        for f in forms:
            sil = form_spec(f)["silhouette"]
            if sil not in sils:
                sils.append(sil)
        for sil in sils:
            build_body(sil)
    if everything or "parts" in words:
        for f in PARTS:
            build_part(f)
    if everything or "cards" in words or (forms and not words):
        for f in forms:
            build_card(f)
    if everything or "cards" in words or "sheet" in words:
        sheet()
