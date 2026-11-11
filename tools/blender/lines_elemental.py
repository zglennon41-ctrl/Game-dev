"""WILDLINE genius lines, the Elemental: the elements as people (docs/genius-lines.md, "The Elemental").

Tiny demigods, a forearm tall, each the small god of something: of Earth, of Sea, of Sky.
A form is a grown, heroic figure at a small size, built on the small people's kit
(lines_people.Person: MakeHuman's body on the game's people's rig), and the element is in
the body, not only held: hair that is water or cloud or flame, flesh of stone with seams of
the field, a mantle of weed or rain or stones, and its own ground under it (it floats, and
brings what it stands on: a slab, a wave, a cloud).

    python tools/blender/genius_lines.py elemental
    python tools/blender/genius_lines.py elemental elemental-tor elemental-berg
    python tools/blender/lines_elemental.py gifts        # what it gives a hybrid

Three things here are this family's own, and any line of people may want them:

  a stance   Each form holds a pose of its own. The pose is baked into the model's rest, less
             what the borrowed Idle clip will add to it (the game gives a form its base
             body's clip as a turn from rest: genius_body.gd, _borrow_clips), so in the game
             it stands as it was posed and still breathes. The base's own body
             (bodies/aspect-demigod.glb, written with the Starter) carries only the Idle: an
             Elemental does not pedal the air when it follows, it glides as it stands.
  what moves Pieces that ride a bone and are moved by their names (genius_lines.moving's
             names: blink_, sway_, glide_, flick_, spin_, pulse_, bob_): F.move().
  a face     Eyes with lids that blink, brows and a mouth, each Path a temperament.

What a `body` may say, here (a slot holds a style, [style, size], [style, size, word], or a
list of those):

    figure   "woman" (the Sea's); build  the small people's proportions, and muscle, weight
    stance   how it holds itself              flesh   marks on the body itself
    hair     the element, as hair             crown   what it wears on its head
    wear     wrap, sash, mantle, cloak...     under   what it stands on or rises from
    right, left, both   what it holds         back    what stands behind it
    chest, belt         what it wears there   around  what keeps it company
    face     its temperament                  eyes    lit, dark
    shape    "storm": no longer a person      accent, accent2, coat
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE  # noqa: E402

ROOT = kit.ROOT
OUT = os.path.join(ROOT, "game", "assets", "genius", "forms")
BODIES = os.path.join(ROOT, "game", "assets", "genius", "bodies")
GIFT_DIR = os.path.join(ROOT, "game", "assets", "genius", "gifts")
SIL = "aspect-demigod"

# What an Elemental is made of that is its own and no partner's coat (so a shifted coat has
# something beside it that does not shift). Each name says what the stuff is (docs/style.md).
OWN = {
    "stone_flesh": ((0.36, 0.34, 0.32), 0.85, 0.0), "cloth_wrap": ((0.62, 0.58, 0.5), 0.95, 0.0), "stone_band": ((0.13, 0.13, 0.14), 0.8, 0.0),
    "stone_basalt": ((0.1, 0.1, 0.115), 0.85, 0.0), "stone_slab": ((0.27, 0.25, 0.23), 0.95, 0.0), "stone_pale": ((0.6, 0.58, 0.54), 0.9, 0.0),
    "slag_dark": ((0.045, 0.04, 0.04), 0.7, 0.0), "earth_loam": ((0.12, 0.085, 0.06), 1.0, 0.0), "moss_green": ((0.2, 0.27, 0.12), 0.95, 0.0),
    "moss_pale": ((0.42, 0.5, 0.3), 0.95, 0.0), "straw_wheat": ((0.72, 0.62, 0.36), 0.9, 0.0), "root_brown": ((0.2, 0.13, 0.08), 0.85, 0.0),
    "bone_thorn": ((0.74, 0.68, 0.56), 0.5, 0.0), "bone_shell": ((0.78, 0.74, 0.66), 0.4, 0.0), "leather_apron": ((0.2, 0.105, 0.045), 0.8, 0.0),
    "brass_band": ((0.62, 0.43, 0.15), 0.32, 0.85), "iron_head": ((0.14, 0.14, 0.16), 0.5, 0.75), "wood_haft": ((0.27, 0.17, 0.09), 0.8, 0.0),
    "steel_edge": ((0.62, 0.64, 0.68), 0.3, 0.8), "rope_line": ((0.4, 0.32, 0.2), 0.9, 0.0),
    "water_deep": ((0.03, 0.055, 0.07), 0.2, 0.0), "water_mid": ((0.09, 0.16, 0.19), 0.2, 0.0), "water_foam": ((0.8, 0.84, 0.87), 0.4, 0.0),
    "ice_clear": ((0.56, 0.78, 0.72), 0.12, 0.0), "ice_blue": ((0.2, 0.3, 0.38), 0.15, 0.0), "ice_white": ((0.84, 0.88, 0.92), 0.2, 0.0),
    "weed_dark": ((0.1, 0.16, 0.1), 0.6, 0.0), "mist_cloud": ((0.66, 0.69, 0.74), 1.0, 0.0), "mist_white": ((0.86, 0.88, 0.92), 1.0, 0.0),
    "mist_storm": ((0.13, 0.14, 0.18), 1.0, 0.0), "cloth_sail": ((0.8, 0.75, 0.62), 0.95, 0.0),
}
PALETTE.update(OWN)

# what is soft is shaded round; what is hard keeps its planes
SOFT = ("cloth", "mist", "water", "moss", "leather", "accent", "field", "eye", "weed", "rope", "straw", "earth", "root")
H = 2.4                 # the human's own size, at which everything is made before the kit's
TRIS = [2500, 2900, 3300, 3600]      # how many faces a body keeps, by stage

# How it stands at each stage: grown at every one (a tiny demigod is an adult a forearm tall;
# the art bible is grounded proportions), the Starter a youth, the Final heroic.
STAGE = [dict(age=0.38, head=1.42, legs=0.9, arms=0.98, hands=1.14, feet=1.1), dict(age=0.44, head=1.3, legs=0.95, arms=1.0, hands=1.1, feet=1.06),
         dict(age=0.5, head=1.2, legs=1.0, arms=1.0, hands=1.06), dict(age=0.5, head=1.14, legs=1.03, arms=1.0, hands=1.04)]
FACE = {"head-oval": 0.4, "chin-prominent": 0.4, "cheek-bones": 0.6, "nose-scale-vert": 0.3, "nose-hump": 0.2, "eye-scale": 0.6, "ear-scale": -0.2,
        "mouth-scale-horiz": 0.2, "head-fat": -0.4, "chin-jaw-drop": 0.2}
# a temperament, as MakeHuman's own details: the brows and the mouth are pieces (face())
TEMPER = {
    "steady": {"mouth-angles": -0.2, "chin-width": 0.4, "head-rectangular": 0.5},
    "old": {"mouth-angles": -0.3, "head-age": 0.6, "chin-width": 0.4, "head-rectangular": 0.5},
    "stern": {"mouth-angles": -0.6, "cheek-volume": 0.4},
    "soft": {"mouth-angles": 0.5, "head-oval": 0.7, "chin-triangle": 0.3, "cheek-volume": 0.2},
    "keen": {"mouth-angles": 0.7, "chin-triangle": 0.7, "head-invertedtriangular": 0.5, "eye-corner2": 0.5},
}


def log(*a):
    print("[lines_elemental]", *a)


def _lp():
    import lines_people as lp       # the small people's kit: read when a form is built, never changed
    return lp


def each(v):
    return _lp().each(v)


def rnd(i, k=0.0):
    x = math.sin(i * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x)


def unit(v):
    return Vector(v).normalized()


# ======================================================================================
# Geometry that is this family's own
# ======================================================================================

def lump(c, r, seed=0, sub=1, scale=(1, 1, 1), rough=0.2):
    """A stone: a faceted ball, no two faces alike."""
    vs, fs = g.ico(c, r, sub=sub, scale=scale)
    c = V(c)
    return [c + (p - c) * (1.0 + rough * (2.0 * rnd(i + 1, seed + 0.37) - 1.0)) for i, p in enumerate(vs)], fs


def cloud(c, r, n=5, seed=0, flat=0.72, sub=1):
    """A cloud: a few balls run together, flat underneath."""
    c = V(c)
    geo = g.ico(c, r * 0.7, sub=sub, scale=(1.2, 0.95, flat))
    for i in range(n):
        a = 2 * math.pi * (i + 0.4 * rnd(i, seed)) / n
        rr = r * (0.4 + 0.2 * rnd(i, seed + 1))
        p = c + Vector((math.cos(a) * r * 0.74, math.sin(a) * r * 0.5, (rnd(i, seed + 2) - 0.3) * r * 0.36))
        geo = g.merge(geo, g.ico(p, rr, sub=max(0, sub - (i % 2)), scale=(1, 1, 0.85)))
    return geo


def prism(base, top, r, n=6, taper=1.0, phase=0.0):
    """A column of n sides from base to top (a basalt column, a shard of ice, a crystal)."""
    base, top = V(base), V(top)
    u, v = g._frame(top - base)
    rings = [g.ring(base, r, r, n=n, u=u, v=v, phase=phase), g.ring(top, r * taper, r * taper, n=n, u=u, v=v, phase=phase)]
    return g.loft(rings)


def shard(base, tip, r, n=5, belly=0.3):
    """A pointed crystal: widest a little way up, then to a point."""
    base, tip = V(base), V(tip)
    mid = base + (tip - base) * belly
    u, v = g._frame(tip - base)
    rings = [g.ring(base, r * 0.6, r * 0.6, n=n, u=u, v=v), g.ring(mid, r, r, n=n, u=u, v=v), g.ring(tip, r * 0.03, r * 0.03, n=n, u=u, v=v)]
    return g.loft(rings)


def hoop(c, rx, ry, r, u=X, v=Y, n=14, sides=4):
    pts = [V(c) + V(u) * (math.cos(2 * math.pi * i / n) * rx) + V(v) * (math.sin(2 * math.pi * i / n) * ry) for i in range(n + 1)]
    return g.tube(pts, [r] * len(pts), n=sides, caps=False)


def disc(c, r, normal=Y, thick=0.02, n=16):
    nrm = unit(normal)
    u = nrm.cross(Z if abs(nrm.dot(Z)) < 0.9 else X).normalized()
    w = nrm.cross(u)
    c = V(c)
    return g.loft([g.ring(c - nrm * thick / 2, r, r, n=n, u=u, v=w), g.ring(c + nrm * thick / 2, r, r, n=n, u=u, v=w)])


def ribbon(points, widths, normal=None, thick=0.25):
    return g.tongue(points, widths, thick=thick, normal=normal)


def bolt(a, b, w, seed=0, n=4, normal=Y):
    """A stroke of lightning from a to b: it goes by corners."""
    a, b = V(a), V(b)
    d = b - a
    side = d.cross(V(normal)).normalized()
    pts = [a]
    for i in range(1, n):
        t = i / n
        pts.append(a + d * t + side * (d.length * 0.16 * (1 if i % 2 else -1) * (0.6 + 0.8 * rnd(i, seed))))
    pts.append(b)
    return g.tongue(pts, [w * 0.5] + [w] * (n - 1) + [w * 0.06], thick=0.5, normal=normal)


# ======================================================================================
# A figure being built
# ======================================================================================

class Fig:
    """One form: the small people's Person (its skin, painted and padded, and the pieces that
    ride its bones), and what this family adds: pieces that move, a stance, a face."""

    def __init__(self, form_id, level, spec):
        lp = _lp()
        lp.STAGE["elemental"], lp.SKIN["elemental"] = STAGE, "main"
        temper = self.temper = (each(spec.get("face")) or [("steady", 1.0, None)])[0][0]
        lp.FACE["elemental"] = dict(FACE, **TEMPER.get(temper, {}))
        b = dict(spec.get("build", {}))
        muscle, weight = b.pop("muscle", 0.6), b.pop("weight", 0.5)
        if spec.get("figure") == "woman":
            b["sex"] = "f"
        real = kit.SmallPerson

        def shaped(*a, **kw):       # the kit's small person, with a build of its own
            kw["build"] = (muscle, weight)
            return real(*a, **kw)
        kit.SmallPerson = shaped
        try:
            self.P = lp.Person("elemental", form_id, level, dict(spec, build=b), lp._roles(SIL))
        finally:
            kit.SmallPerson = real
        self.form_id, self.level, self.spec = form_id, level, spec
        self.woman = spec.get("figure") == "woman"
        self.movers = []            # (name, [(geo, material)], bone, pivot, smooth, up)
        self.pole = _pole_of(self.P)
        self.pose = STANCES[(each(spec.get("stance")) or [("attend", 1.0, None)])[0][0]](self)
        self.seat = self.pose.get("seat", 0.0)      # how high the lowest of it is: what it stands or sits on is made there

    # --- materials -----------------------------------------------------------------------

    def m(self, token):
        if not isinstance(token, str):
            return token
        return self.P.material(token)

    # --- pieces ------------------------------------------------------------------------------

    def add(self, name, geo, material, bone, smooth=None):
        """A piece that rides one bone as part of the one skin (made in the rest pose, at the human's own size)."""
        material = self.m(material)
        self.P.add(name, geo, material, bone, material.name.startswith(SOFT) if smooth is None else smooth)

    def move(self, kind, what, items, pivot, bone, side="", n=None, smooth=None, up=None):
        """A piece the game moves by its name (docs/genius-lines.md, "What moves"), riding a bone.
        up: the way its own up points (a flame that leans, a wheel that faces the front)."""
        import genius_lines as gl
        assert kind in gl.MOVES, kind
        name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else "")
        items = [(geo, self.m(mm)) for geo, mm in items if geo and geo[0]]
        if items:
            self.movers.append((name, items, bone, Vector(pivot), smooth, None if up is None else unit(up)))

    # --- finishing -------------------------------------------------------------------------

    def finish(self, path, clip=False):
        """The body thinned and joined with its pieces, the movers on their bones, the stance
        struck and baked, the sockets; written with no clip (a form) or with the Idle (the
        base's body, which every form borrows it from)."""
        P = self.P
        p, hb, hu = P.p, P.hb, P.p.hu
        arm, s = p.arm, p.s
        body = hu.mesh_object("Body", P.v, hb.faces, P.mats, face_material=[int(i) for i in P.fmat])
        hb.weight_body(body)
        w = np.where(P.hand, 1.0, np.where(hb.is_head, 0.3, 0.75))
        w[P.ears] = 0.55
        vg = body.vertex_groups.new(name="_thin")
        for value in (1.0, 0.75, 0.55, 0.3):
            vg.add([int(i) for i in np.nonzero(w == value)[0]], value, "REPLACE")
        tris = sum(len(poly.vertices) - 2 for poly in body.data.polygons)
        bpy.ops.object.select_all(action="DESELECT")
        body.select_set(True)
        bpy.context.view_layer.objects.active = body
        dec = body.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = min(1.0, TRIS[self.level - 1] / tris)
        dec.vertex_group = "_thin"
        dec.vertex_group_factor = 1.0
        bpy.ops.object.modifier_apply(modifier="Decimate")
        body.vertex_groups.remove(body.vertex_groups["_thin"])
        body.select_set(False)
        made = []
        for name, geo, material, bone, smooth in P.pieces:
            ob = g.to_object(name, geo, material, bool(smooth))
            ob.vertex_groups.new(name=bone).add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
            made.append(ob)
        if made:
            bpy.ops.object.select_all(action="DESELECT")
            for ob in made:
                ob.select_set(True)
            body.select_set(True)
            bpy.context.view_layer.objects.active = body
            bpy.ops.object.join()
            body.select_set(False)
        body.parent = arm
        mod = body.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        bpy.context.view_layer.update()
        movers = []
        for name, items, bone, pivot, smooth, up in self.movers:
            ob = g.pieces(name, items, smooth=False)
            for poly in ob.data.polygons:
                poly.use_smooth = ob.data.materials[poly.material_index].name.startswith(SOFT) if smooth is None else bool(smooth)
            R = Matrix.Identity(4) if up is None else Z.rotation_difference(up).to_matrix().to_4x4()
            ob.data.transform(R.inverted())
            ob.parent = arm
            ob.parent_type = "BONE"
            ob.parent_bone = bone
            bpy.context.view_layer.update()
            ob.matrix_world = R
            movers.append(ob)
        r = p.r
        r.skinned, r.attached = [body], movers
        r.uniform(s)
        bpy.context.view_layer.update()
        for ob, (_, _, _, pivot, _, _) in zip(movers, self.movers):
            kit.set_origin(ob, pivot * s)
        socks = {name: kit.bone_socket(arm, name, bone, Vector(at) * s, rot) for name, (bone, at, rot) in p.common_sockets().items()}
        socks["ref_top"] = kit.free_socket("ref_top", (0, 0, P.crown * s))
        strike(arm, self.pose, s)
        _bake(arm, body)
        for a in list(bpy.data.actions):
            if not (clip and a.name == "Idle"):
                bpy.data.actions.remove(a)
        if arm.animation_data:
            for tr in list(arm.animation_data.nla_tracks):
                if not (clip and tr.name == "Idle"):
                    arm.animation_data.nla_tracks.remove(tr)
        arm.data.pose_position = "POSE" if clip else "REST"
        if clip and arm.animation_data:
            for tr in arm.animation_data.nla_tracks:
                tr.mute = False
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in [arm, body] + movers + list(socks.values()):
            o.select_set(True)
        bpy.context.view_layer.objects.active = arm
        if clip:
            bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                      export_animations=True, export_animation_mode="ACTIONS", export_skins=True, export_texcoords=False)
        else:       # no clips: a form moves by its base body's, which the game fits to it
            bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                      export_animations=False, export_skins=True, export_texcoords=False)
        tris = sum(len(poly.vertices) - 2 for ob in [body] + movers for poly in ob.data.polygons)
        log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB, %d that move" % (tris, os.path.getsize(path) // 1024, len(movers)))


# ======================================================================================
# The stance: struck on the rig, and baked into its rest
# ======================================================================================

def strike(arm, pose, s):
    """Pose the rig as the form stands in the game at the Idle's first frame: start from that
    frame of the borrowed clip (so a limb the stance does not name hangs as the clip has it),
    turn what the stance names, then take the clip's own turn off every bone again. What is
    left is the rest the game adds the clip to (final = rest x the clip's turn = the stance)."""
    MW = arm.matrix_world
    MWi = MW.inverted()
    act = bpy.data.actions.get("Idle")
    delta = {}
    arm.data.pose_position = "POSE"
    if act and arm.animation_data:
        for tr in arm.animation_data.nla_tracks:
            tr.mute = True
        arm.animation_data.action = act
        if hasattr(arm.animation_data, "action_slot") and getattr(act, "slots", None):
            arm.animation_data.action_slot = act.slots[0]
        bpy.context.scene.frame_set(int(act.frame_range[0]))
        bpy.context.view_layer.update()
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"
            delta[pb.name] = (pb.rotation_quaternion.copy(), pb.location.copy())
        arm.animation_data.action = None
        for pb in arm.pose.bones:       # and it stays as that frame had it
            pb.rotation_quaternion, pb.location = delta[pb.name][0].copy(), delta[pb.name][1].copy()
        bpy.context.view_layer.update()

    def world(name):
        return MW @ arm.pose.bones[name].matrix

    def at(name):
        return world(name).translation.copy()

    def set_world(name, M):
        arm.pose.bones[name].matrix = MWi @ M
        bpy.context.view_layer.update()

    def turn(name, e):
        if not e:
            return
        M = world(name)
        hd = M.translation.copy()
        R = Matrix.Rotation(math.radians(e[2]), 4, "Z") @ Matrix.Rotation(math.radians(e[1]), 4, "Y") @ Matrix.Rotation(math.radians(e[0]), 4, "X")
        set_world(name, Matrix.Translation(hd) @ R @ Matrix.Translation(-hd) @ M)

    def aim(name, d, roll=0.0):
        M = world(name)
        hd = M.translation.copy()
        y = (M.to_3x3() @ Y).normalized()
        d = unit(d)
        R = y.rotation_difference(d).to_matrix().to_4x4()
        if roll:
            R = Matrix.Rotation(math.radians(roll), 4, d) @ R
        set_world(name, Matrix.Translation(hd) @ R @ Matrix.Translation(-hd) @ M)

    def limb(upper, lower, end, tip, spec, joints):
        if not spec:
            return
        if spec[0] == "dir":
            aim(upper, spec[1])
            aim(lower, spec[2])
            if len(spec) > 3 and spec[3] is not None:
                aim(end, spec[3])
            return
        # reach: the wrist (or the ankle) brought to a point, the elbow (the knee) toward a hint
        target = spec[1](joints) if callable(spec[1]) else Vector(spec[1]) * s
        S = at(upper)
        l1, l2 = (at(lower) - S).length, (at(tip) - at(lower)).length
        d = target - S
        dist = min(max(d.length, abs(l1 - l2) + 1e-4), l1 + l2 - 1e-4)
        n = d.normalized()
        a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
        hgt = math.sqrt(max(0.0, l1 * l1 - a * a))
        hint = Vector(spec[2])
        hp = hint - n * hint.dot(n)
        hp = hp.normalized() if hp.length > 1e-6 else g._frame(n)[0]
        E = S + n * a + hp * hgt
        aim(upper, E - S)
        aim(lower, (S + n * dist) - at(lower))
        if len(spec) > 3 and spec[3] is not None:
            aim(end, spec[3])

    turn("hips", pose.get("hips"))
    turn("spine", pose.get("spine"))
    turn("chest", pose.get("chest"))
    turn("head", pose.get("head"))
    joints = {}
    for sd in ("l", "r"):
        limb("upperleg." + sd, "lowerleg." + sd, "foot." + sd, "foot." + sd, pose.get("leg_" + sd), joints)
        joints["knee_" + sd] = at("lowerleg." + sd)
        joints["ankle_" + sd] = at("foot." + sd)
    for sd in ("l", "r"):
        limb("upperarm." + sd, "lowerarm." + sd, "hand." + sd, "wrist." + sd, pose.get("arm_" + sd), joints)
    for pb in arm.pose.bones:
        if pb.name in delta:
            q, loc = delta[pb.name]
            pb.rotation_quaternion = pb.rotation_quaternion @ q.inverted()
            pb.location = pb.location - loc
    bpy.context.view_layer.update()


def _bake(arm, body):
    """What it was posed as becomes how it is made: the skin takes the pose, and the pose becomes the rest."""
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Armature")
    body.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.select_set(False)
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    bpy.context.view_layer.update()


def mir(spec):
    """A limb's spec for the other side."""
    if not spec:
        return spec
    fl = lambda v: v if v is None or callable(v) else (-v[0], v[1], v[2])
    return (spec[0],) + tuple(fl(v) for v in spec[1:])


def both(spec):
    return {"l": spec, "r": mir(spec)}


STANCES = {}
FLAT = (0.16, -0.67, -0.72)      # a foot set flat on its ground, turned out a little
TOES = (0.06, -0.42, -0.9)       # a foot hanging, as of one who floats
RFLAT, RTOES = (-FLAT[0], FLAT[1], FLAT[2]), (-TOES[0], TOES[1], TOES[2])


def stance(name):
    def deco(fn):
        STANCES[name] = fn
        return fn
    return deco


def _legs(out, l, r=None):
    out["leg_l"], out["leg_r"] = l, (mir(l) if r is None else r)
    return out


def _arms(out, l, r=None):
    out["arm_l"], out["arm_r"] = l, (mir(l) if r is None else r)
    return out


def _on_knee(sd):
    return lambda j: j["knee_" + sd] + Vector((0, -0.01, 0.045)) * (j["knee_l"] - j["ankle_l"]).length / 0.5


@stance("attend")
def _attend(F):
    """Standing on the air with its chin up."""
    out = {"head": (-7, 0, 0), "chest": (-3, 0, 0)}
    _arms(out, ("dir", (0.2, 0.06, -1), (0.14, -0.1, -1)))
    return _legs(out, ("dir", (0.05, -0.02, -1), (0.03, 0.06, -1), TOES), ("dir", (-0.04, 0.04, -1), (-0.02, 0.12, -1), RTOES))


@stance("folded")
def _folded(F):
    """Planted, with its arms folded."""
    out = {"head": (3, 0, 0)}
    _arms(out, ("dir", (0.3, -0.36, -0.88), (-0.94, -0.33, 0.1)), ("dir", (-0.3, -0.42, -0.86), (0.93, -0.36, -0.06)))
    return _legs(out, ("dir", (0.2, 0.0, -1), (0.07, 0.03, -1), FLAT))


@stance("planted")
def _planted(F):
    """Fists on its hips, feet wide."""
    P = F.P
    hw, hd, yo = P.ring(P.hipz + 0.1 * P.t)
    out = {"head": (4, 0, 0), "chest": (-4, 0, 0)}
    _arms(out, ("reach", (hw + 0.05, yo - 0.02, P.hipz + 0.12 * P.t), (1.0, 0.75, 0.1)))
    return _legs(out, ("dir", (0.3, 0.0, -1), (0.1, 0.03, -1), FLAT))


@stance("column")
def _column(F):
    """As a carved figure stands: arms straight down, feet together."""
    out = {"head": (0, 0, 0)}
    _arms(out, ("dir", (0.08, 0.02, -1), (0.02, -0.04, -1)))
    return _legs(out, ("dir", (0.0, 0.0, -1), (0.0, 0.03, -1), (0.05, -0.68, -0.72)))


@stance("seated")
def _seated(F):
    """Cross-legged, its hands on its knees."""
    P = F.P
    out = {"seat": P.hipz - 0.17 * P.t, "head": (2, 0, 0)}
    _legs(out, ("dir", (0.78, -0.58, -0.22), (-0.92, -0.3, -0.24)), ("dir", (-0.78, -0.58, -0.22), (0.93, -0.04, -0.36)))
    return _arms(out, ("reach", _on_knee("l"), (0.8, 0.5, -0.2)), ("reach", _on_knee("r"), (-0.8, 0.5, -0.2)))


@stance("offer")
def _offer(F):
    """Its hands held out low, open."""
    out = {"head": (5, 0, 0)}
    _arms(out, ("dir", (0.34, -0.2, -0.92), (0.3, -0.92, 0.12)))
    return _legs(out, ("dir", (0.12, 0.0, -1), (0.05, 0.03, -1), FLAT))


@stance("carry")
def _carry(F):
    """A sheaf in the crook of its left arm, its right hand out with the sickle."""
    out = {"head": (2, 0, 6), "chest": (0, 0, 5)}
    _arms(out, ("dir", (0.2, -0.12, -1), (-0.3, -0.85, 0.42)), ("dir", (-0.55, -0.25, -0.8), (-0.4, -0.8, 0.45)))
    return _legs(out, ("dir", (0.14, 0.0, -1), (0.05, 0.03, -1), FLAT))


@stance("guard")
def _guard(F):
    """Its arms spread low to either side: nothing gets past."""
    out = {"head": (6, 0, 0), "chest": (4, 0, 0)}
    _arms(out, ("dir", (0.8, -0.12, -0.58), (0.78, -0.3, -0.55)))
    return _legs(out, ("dir", (0.32, 0.0, -1), (0.1, 0.03, -1), FLAT))


@stance("shoulder")
def _shoulder(F):
    """A long hammer over its right shoulder, its left fist on its hip."""
    P = F.P
    hw, hd, yo = P.ring(P.hipz + 0.1 * P.t)
    out = {"head": (0, 0, 8), "chest": (-3, 0, 0)}
    _arms(out, ("reach", (hw + 0.05, yo - 0.02, P.hipz + 0.12 * P.t), (1.0, 0.75, 0.1)),
          ("reach", (-P.sx * 0.72, P.front(P.chestz) - 0.2, P.armz - 0.12 * P.t), (-0.7, 0.2, -1.0)))
    return _legs(out, ("dir", (0.24, 0.0, -1), (0.08, 0.03, -1), FLAT))


@stance("wrath")
def _wrath(F):
    """Fists down and out, its head back."""
    out = {"head": (-12, 0, 0), "chest": (-8, 0, 0)}
    _arms(out, ("dir", (0.6, 0.12, -0.8), (0.5, -0.2, -0.85)))
    return _legs(out, ("dir", (0.12, 0.0, -1), (0.04, 0.03, -1), FLAT))


@stance("flow")
def _flow(F):
    """Its weight on one hip, one hand lifted, palm up."""
    out = {"hips": (0, 4, 0), "chest": (0, -7, 0), "head": (0, 5, 8)}
    _arms(out, ("dir", (0.5, -0.22, -0.84), (0.42, -0.62, 0.66)), ("dir", (-0.28, 0.1, -1), (-0.22, -0.22, -1)))
    return _legs(out, ("dir", (0.02, -0.03, -1), (0.0, 0.05, -1), TOES), ("dir", (-0.08, 0.0, -1), (0.02, 0.06, -1), RTOES))


@stance("stroll")
def _stroll(F):
    """In the middle of a step that is going round something."""
    out = {"chest": (0, 0, -12), "head": (0, 0, 14)}
    _arms(out, ("dir", (0.25, 0.28, -0.93), (0.2, 0.02, -1)), ("dir", (-0.22, -0.32, -0.92), (-0.16, -0.6, -0.78)))
    return _legs(out, ("dir", (0.03, -0.36, -0.93), (0.02, 0.12, -1), TOES), ("dir", (-0.03, 0.22, -0.97), (-0.02, 0.52, -0.85), RTOES))


@stance("pole")
def _pole(F):
    """Both hands on a pole set down over the side."""
    P = F.P
    a, b = F.pole
    out = {"chest": (4, 0, -14), "head": (2, 0, 10)}
    _arms(out, ("reach", tuple(a + (b - a) * 0.3 + Vector((0, 0.04, 0))), (0.6, 0.3, -1.0)), ("reach", tuple(a + (b - a) * 0.52 + Vector((0, 0.04, 0))), (-0.8, 0.3, -0.6)))
    return _legs(out, ("dir", (0.12, -0.22, -0.97), (0.05, 0.1, -1), FLAT), ("dir", (-0.16, 0.16, -0.97), (-0.06, 0.2, -0.98), RFLAT))


@stance("open")
def _open(F):
    """Its arms open, its head back: here it comes."""
    out = {"chest": (-7, 0, 0), "head": (-9, 0, 0)}
    _arms(out, ("dir", (0.86, -0.12, -0.5), (0.78, -0.42, 0.46)))
    return _legs(out, ("dir", (0.03, 0.0, -1), (0.0, 0.03, -1), TOES))


@stance("stiff")
def _stiff(F):
    """Gone hard and still: straight arms held a little off its sides."""
    out = {"head": (0, 0, 0)}
    _arms(out, ("dir", (0.44, 0.0, -0.9), (0.44, -0.02, -0.9)))
    return _legs(out, ("dir", (0.16, 0.0, -1), (0.06, 0.03, -1), FLAT))


@stance("stride")
def _stride(F):
    """Leaning into a slow stride that never finishes."""
    out = {"hips": (16, 0, 0), "head": (-10, 0, 0)}
    _arms(out, ("dir", (0.18, 0.42, -0.89), (0.14, 0.26, -0.95)), ("dir", (-0.18, -0.52, -0.84), (-0.12, -0.78, -0.62)))
    return _legs(out, ("dir", (0.05, -0.56, -0.83), (0.03, 0.06, -1), FLAT), ("dir", (-0.05, 0.46, -0.89), (-0.03, 0.66, -0.75), RTOES))


@stance("drift")
def _drift(F):
    """As a thing hangs in deep water: arms out and lifting, one knee bent."""
    out = {"head": (6, 0, -6), "chest": (3, 0, 0)}
    _arms(out, ("dir", (0.78, 0.05, -0.58), (0.74, -0.18, 0.52)), ("dir", (-0.8, 0.0, -0.48), (-0.85, -0.2, 0.2)))
    return _legs(out, ("dir", (0.1, -0.32, -0.94), (0.05, 0.46, -0.89), TOES), ("dir", (-0.08, 0.06, -1), (-0.04, 0.22, -0.97), RTOES))


@stance("hang")
def _hang(F):
    """Bent over its own light, its arms and legs trailing."""
    out = {"chest": (16, 0, 0), "head": (8, 0, 0)}
    _arms(out, ("dir", (0.24, -0.16, -0.96), (0.12, -0.42, -0.9)))
    return _legs(out, ("dir", (0.06, 0.2, -0.98), (0.03, 0.5, -0.86), TOES))


@stance("yoke")
def _yoke(F):
    """A bar across its shoulders, a hand over each end of it."""
    P = F.P
    y, z = P.rear(P.armz) + 0.07, P.armz + 0.1 * P.t
    out = {"head": (6, 0, 0), "chest": (5, 0, 0)}
    _arms(out, ("reach", (P.sx + 0.36, y - 0.03, z + 0.03), (0.2, 0.3, -1.0)))
    return _legs(out, ("dir", (0.2, 0.0, -1), (0.07, 0.03, -1), FLAT))


@stance("lean")
def _lean(F):
    """Leaning into a wind that comes from its right, one arm up against it."""
    out = {"hips": (4, -9, 0), "head": (0, 4, -10)}
    _arms(out, ("dir", (0.5, 0.3, -0.8), (0.62, 0.2, -0.75)), ("dir", (-0.62, -0.42, -0.6), (0.2, -0.52, 0.82)))
    return _legs(out, ("dir", (0.14, -0.1, -0.98), (0.22, 0.3, -0.92), TOES), ("dir", (-0.02, -0.26, -0.96), (0.06, 0.36, -0.92), RTOES))


@stance("fly")
def _fly(F):
    """Stretched out along the wind as if lying on it."""
    out = {"hips": (68, 0, 0), "chest": (-10, 0, 0), "head": (-48, 0, 0)}
    _arms(out, ("dir", (0.3, 0.9, -0.3), (0.16, 0.96, -0.2)), ("dir", (-0.22, -0.9, 0.36), (-0.1, -0.95, 0.3)))
    return _legs(out, ("dir", (0.06, 0.95, -0.28), (0.03, 0.98, -0.16), (0.02, 0.9, -0.42)), ("dir", (-0.08, 0.9, -0.42), (-0.03, 0.99, 0.08), (-0.02, 0.9, -0.42)))


@stance("blow")
def _blow(F):
    """Leaning out over its own breath, fists on its hips."""
    P = F.P
    hw, hd, yo = P.ring(P.hipz + 0.1 * P.t)
    out = {"hips": (20, 0, 0), "head": (-12, 0, 0)}
    _arms(out, ("dir", (0.62, 0.42, -0.62), (-0.42, -0.2, -0.86)))
    return _legs(out, ("dir", (0.14, 0.1, -0.98), (0.06, 0.36, -0.92), TOES))


@stance("brood")
def _brood(F):
    """Tall and quiet, its hands behind its back."""
    P = F.P
    out = {"head": (9, 0, 0)}
    _arms(out, ("reach", (0.04, P.rear(P.hipz + 0.1) + 0.06, P.hipz + 0.1 * P.t), (1.0, 0.7, 0.0)))
    return _legs(out, ("dir", (0.03, 0.0, -1), (0.0, 0.03, -1), TOES))


@stance("throw")
def _throw(F):
    """One arm drawn back to throw, the other pointing where."""
    out = {"hips": (0, 0, -8), "chest": (-4, 0, -24), "head": (0, 0, 26)}
    _arms(out, ("dir", (0.42, -0.86, -0.1), (0.3, -0.92, 0.12)), ("dir", (-0.66, 0.5, 0.42), (0.05, 0.42, 0.9)))
    return _legs(out, ("dir", (0.12, -0.5, -0.85), (0.05, 0.22, -0.97), TOES), ("dir", (-0.12, 0.46, -0.88), (-0.05, 0.62, -0.78), RTOES))


@stance("greet")
def _greet(F):
    """Arms flung up and open, to the day."""
    out = {"head": (-8, 0, 0), "chest": (-5, 0, 0)}
    _arms(out, ("dir", (0.82, -0.05, 0.42), (0.52, -0.16, 0.84)))
    return _legs(out, ("dir", (0.04, -0.04, -1), (0.0, 0.1, -1), TOES), ("dir", (-0.04, 0.03, -1), (0.0, 0.16, -1), RTOES))


@stance("hieratic")
def _hieratic(F):
    """Square to you, as a figure on a wall: hands a little out, palms forward."""
    out = {"head": (0, 0, 0)}
    _arms(out, ("dir", (0.22, 0.0, -1), (0.26, -0.36, -0.9)))
    return _legs(out, ("dir", (0.0, 0.0, -1), (0.0, 0.03, -1), (0.05, -0.68, -0.72)))


@stance("knee-up")
def _knee_up(F):
    """Sitting half turned away, one knee up and an arm across it."""
    P = F.P
    out = {"seat": P.hipz - 0.17 * P.t, "hips": (0, 0, 34), "head": (4, 0, -20)}
    _legs(out, ("dir", (0.2, -0.72, 0.5), (0.02, -0.12, -1), FLAT), ("dir", (-0.66, -0.7, -0.2), (0.9, -0.2, -0.3)))
    return _arms(out, ("reach", _on_knee("l"), (0.9, 0.2, 0.3)), ("dir", (-0.4, 0.4, -0.84), (-0.2, 0.3, -0.93)))


# ======================================================================================
# The styles
# ======================================================================================

STYLES = {}          # slot -> {style: fn(F, size, word)}
ORDER = ("flesh", "wear", "eyes", "face", "hair", "crown", "chest", "belt", "back", "under", "right", "left", "both", "around")


def style(slot, *names):
    def deco(fn):
        for nm in names:
            STYLES.setdefault(slot, {})[nm] = fn
        return fn
    return deco


def _noise(v, f=7.0):
    return (np.sin(v[:, 0] * f * 1.3 + np.sin(v[:, 2] * f) * 1.7) + np.sin(v[:, 1] * f * 1.7 + np.sin(v[:, 0] * f * 0.8) * 1.3) + np.sin(v[:, 2] * f * 1.1 + np.sin(v[:, 1] * f * 1.2) * 1.9)) / 3.0


def _limbs(P, arms=0.0, legs=0.0):
    """The arms beyond a way out and the legs below a height (0 for none of either)."""
    v = P.v0
    m = np.zeros(len(v), dtype=bool)
    if arms:
        m |= P.arm & (np.abs(v[:, 0]) > arms + 0.05 * _noise(v, 9.0))
    if legs:
        m |= ~P.arm & ~P.headv & (v[:, 2] < legs + 0.06 * _noise(v, 9.0))
    return m


# --- the flesh -------------------------------------------------------------------------------

@style("flesh", "seams")
def flesh_seams(F, size, word):
    """Seams where the stone has settled: ore in them, and the field in the deepest."""
    P = F.P
    n = _noise(P.v0, 6.0)
    body = ~P.headv & ~P.hand
    P.paint(body & (np.abs(n) < 0.05 * size), mat("accent"))
    P.paint(body & (np.abs(n) < 0.014 * size), field("seam", 2.2))


@style("flesh", "cracks")
def flesh_cracks(F, size, word):
    """Cracked like cooling slag, and the fire showing in the cracks."""
    P = F.P
    n = _noise(P.v0, 5.0)
    body = ~P.headv & ~P.hand
    P.paint(body & (np.abs(n) < 0.085 * size), mat("accent_dark"))
    P.paint(body & (np.abs(n) < 0.04 * size), mat("accent_light"))
    P.paint(body & (np.abs(n) < 0.016 * size), field("seam", 2.6))


@style("flesh", "slag-limbs", "earth-legs", "deep-limbs", "rime", "storm-shoulders")
def flesh_limbs(F, size, word):
    """What its limbs have gone to: slag to the elbows and knees; earth to the knees; the dark of
    deep water; rime; and a storm's dark across the shoulders."""
    P = F.P
    st = F._style
    if st == "slag-limbs":
        P.paint(_limbs(P, P.ex - 0.05, P.kneez + 0.05), mat("slag_dark"))
    elif st == "earth-legs":
        P.paint(_limbs(P, 0.0, P.kneez + 0.12), mat("earth_loam"))
        n = _noise(P.v0, 11.0)
        P.paint(_limbs(P, 0.0, P.kneez + 0.2) & (n > 0.25), mat("moss_green"))
    elif st == "deep-limbs":
        P.paint(_limbs(P, P.ex - 0.02, P.kneez + 0.08), mat("water_deep"))
        n = _noise(P.v0, 13.0)
        P.paint(_limbs(P, P.ex + 0.05, P.kneez - 0.05) & (n > 0.52), mat("accent_light"))
    elif st == "rime":
        P.paint(_limbs(P, P.wx - 0.2, P.footz + 0.42), mat("ice_white"))
        n = _noise(P.v0, 12.0)
        P.paint(~P.headv & ~P.hand & (n > 0.5), mat("ice_clear"))
    else:
        v = P.v0
        P.paint(~P.headv & (v[:, 2] > P.chestz + 0.02 + 0.07 * _noise(v, 8.0)) & (np.abs(v[:, 0]) < P.ex), mat("mist_storm"))
        n = _noise(v, 10.0)
        P.paint(~P.headv & (v[:, 2] > P.chestz) & (np.abs(n) < 0.03), field("seam", 2.4))


@style("flesh", "lava")
def flesh_lava(F, size, word):
    """Fire running down from its shoulders, slow, cooling toward the elbows."""
    P = F.P
    v = P.v0
    n = _noise(v * np.array([2.2, 2.2, 0.55]), 6.0)
    up = ~P.headv & ~P.hand & (v[:, 2] > P.chestz - 0.16) & (np.abs(v[:, 0]) < P.ex + 0.04)
    P.paint(up & (n > 0.08), mat("accent"))
    P.paint(up & (n > 0.3), mat("accent_light"))
    P.paint(up & (n > 0.5), field("lava", 2.8))


@style("flesh", "glow-hands")
def flesh_glow_hands(F, size, word):
    P = F.P
    P.paint(P.hand & (np.abs(P.v0[:, 0]) > P.wx + 0.1) & (_noise(P.v0, 30.0) > 0.0), field("hands", 2.4))


@style("flesh", "fins")
def flesh_fins(F, size, word):
    """Fins at its forearms and its calves, and its Path's colour scaled over its shins."""
    P = F.P
    n = _noise(P.v0, 14.0)
    P.paint(_limbs(P, P.wx - 0.24, P.kneez - 0.1) & ~P.hand & (n > 0.1), mat("accent"))
    for sg, tag in ((1, "l"), (-1, "r")):
        x = sg * (P.ex + 0.5 * (P.wx - P.ex))
        F.add("fin_arm_" + tag, g.blade((x - sg * 0.12, P.army + 0.04, P.armz), (x + sg * 0.1, P.army + 0.3 * size, P.armz + 0.03), 0.2 * size, normal=Z, belly=0.4, thick=0.012), "accent_light", "lowerarm." + tag)
        lx = sg * P.J["lowerleg.l"].x
        z = P.kneez - 0.2
        F.add("fin_leg_" + tag, g.blade((lx, P.J["lowerleg.l"].y + 0.06, z + 0.1), (lx + sg * 0.02, P.J["lowerleg.l"].y + 0.32 * size, z - 0.16), 0.22 * size, normal=X, belly=0.4, thick=0.012), "accent_light", "lowerleg." + tag)


@style("flesh", "ribs")
def flesh_ribs(F, size, word):
    """Its ribs show like a lantern's bars, and the light is behind them."""
    P = F.P
    v = P.v0
    z0, z1 = P.hipz + 0.3 * P.t, P.chestz + 0.16 * P.t
    front = P.trunk(z0, z1, front=True) & (np.abs(v[:, 0]) < P.ring(P.chestz)[0] * 0.86)
    band = np.sin((v[:, 2] - z0) / (z1 - z0) * math.pi * 5.0 + np.abs(v[:, 0]) * 3.0)
    P.paint(front & (band > 0.55), field("ribs", 2.0))
    P.paint(front & (band <= 0.55) & (band > -0.2), mat("accent_dark"))


@style("flesh", "barnacles")
def flesh_barnacles(F, size, word):
    """Barnacles to the elbow, and a few on the shoulders."""
    P = F.P
    for sg, tag in ((1, "l"), (-1, "r")):
        geo = None
        for i in range(7):
            x = sg * (P.ex - 0.04 + (P.wx - P.ex) * (i + 0.5) / 7)
            a = 2.4 * i
            d = Vector((0, math.cos(a), math.sin(a)))
            row = _lp().people_dress.arm_row(P, abs(x))
            b0 = Vector((x, P.army, P.armz)) + Vector((0, d.y * row[1], d.z * row[2]))
            geo = g.merge(geo, g.tube([b0 - d * 0.01, b0 + d * 0.035 * size], [0.04 * size, 0.022 * size], n=5))
        F.add("barnacles_" + tag, geo, "bone_shell", "lowerarm." + tag, smooth=False)
        geo = None
        for i in range(3):
            b0 = Vector((sg * (P.sx - 0.03 + 0.06 * i), P.army + 0.03 * (i - 1), P.armz + 0.1 * P.t))
            geo = g.merge(geo, g.tube([b0, b0 + Vector((sg * 0.01, 0, 0.04 * size))], [0.045 * size, 0.024 * size], n=5))
        F.add("barnacles_sh_" + tag, geo, "bone_shell", "chest", smooth=False)


# --- eyes, brows, mouth -------------------------------------------------------------------

@style("eyes", "lit", "dark")
def eyes(F, size, word):
    """Eyes with lids. Each eye is its own piece and shuts (blink_eye_l, blink_eye_r); behind it
    is the lid it shuts to. lit: the field in the iris. dark: wide and dark, a light sunk in."""
    P = F.P
    k = 1.42 * size * (1.2 if F._style == "dark" else 1.0)
    r = P.eye_r * 1.04 * k
    skin = P.skin
    lids, shut = None, None
    for sg, tag in ((1, "l"), (-1, "r")):
        c = Vector((sg * P.eye.x, P.eye.y - P.eye_r * 0.4 * (k - 1.0), P.eye.z))
        f = c + Vector((0, -r * 0.62, 0))
        if F._style == "dark":
            items = [(g.ico(c, r, sub=1), "eye_dark"), (g.ico(f + Vector((sg * r * 0.2, -r * 0.2, r * 0.22)), r * 0.24, sub=0, scale=(1, 0.6, 1)), field("eyes", 4.0))]
        else:
            items = [(g.ico(c, r, sub=1), "eye_white"), (g.ico(f, r * 0.66, sub=1, scale=(1.0, 0.55, 1.0)), field("eyes", 3.6)),
                     (g.ico(f + Vector((0, -r * 0.3, 0)), r * 0.27, sub=0, scale=(1.0, 0.5, 1.0)), "eye_dark")]
        F.move("blink", "eye", items, c, "head", side=tag, smooth=True)
        shut = g.merge(shut, g.ico(c + Vector((0, r * 0.16, 0)), r * 0.99, sub=1))
        # the upper lid: lower for the steady and the old, lifted at the outer corner for the keen
        drop = {"steady": 0.8, "old": 0.7, "stern": 0.74, "soft": 0.86, "keen": 0.94}.get(F.temper, 0.82)
        tilt = {"keen": -0.3, "stern": 0.26, "soft": 0.1}.get(F.temper, 0.0) * sg
        lids = g.merge(lids, g.ico(c + Vector((0, -r * 0.1, r * drop)), r * 1.08, sub=1, scale=(1.16, 1.0, 0.56), rot=(0.25, tilt, 0)))
    F.add("eye_shut", shut, skin, "head", smooth=True)
    F.add("eye_lids", lids, skin, "head", smooth=True)


def face(F):
    """Brows and a mouth: each Path a temperament you can see."""
    P = F.P
    t = F.temper
    hr, e, r = P.hr, P.eye, P.eye_r * 1.45
    # (inner end's lift, outer end's lift, thickness, how far out) in eye radii
    inn, outr, thick, reach = {"steady": (1.5, 1.55, 0.5, 2.3), "old": (1.4, 1.7, 0.62, 2.5), "stern": (1.12, 1.9, 0.5, 2.3), "soft": (1.75, 1.6, 0.3, 2.2),
                               "keen": (1.3, 2.15, 0.34, 2.4)}.get(t, (1.5, 1.6, 0.4, 2.3))
    brows = None
    for sg in (1, -1):
        a = Vector((sg * (e.x - r * 0.95), e.y - r * 0.95, e.z + r * inn))
        b = Vector((sg * (e.x + r * 0.2), e.y - r * 0.9, e.z + r * (0.5 * (inn + outr) + 0.22)))
        c = Vector((sg * (e.x + r * (reach - 1.0)), e.y - r * 0.25, e.z + r * outr))
        brows = g.merge(brows, g.tube([a, b, c], [r * thick * 0.5, r * thick * 0.46, r * thick * 0.2], n=5, flat=0.7))
    F.add("brows", brows, "trim" if not getattr(F, "brow", None) else F.brow, "head", smooth=True)
    z = float(P.mouth[2]) - 0.07 * hr
    y = P.front(z) - 0.004
    w = 0.34 * hr
    lift = {"steady": 0.0, "old": -0.04, "stern": -0.1, "soft": 0.07, "keen": 0.1}.get(t, 0.0) * hr
    skew = 0.05 * hr if t == "keen" else 0.0
    pts = [(-w, y + 0.03 * hr, z + lift - skew), (-w * 0.5, y + 0.004, z + lift * 0.3 - skew * 0.4), (0, y - 0.004, z), (w * 0.5, y + 0.004, z + lift * 0.3 + skew * 0.4), (w, y + 0.03 * hr, z + lift + skew)]
    F.add("mouth", g.tube(pts, [0.012 * hr, 0.03 * hr, 0.034 * hr, 0.03 * hr, 0.012 * hr], n=4, flat=0.55), "stone_band", "head", smooth=True)


@style("face", "steady", "old", "stern", "soft", "keen")
def face_temper(F, size, word):
    pass        # the temperament is read when the figure is made (Fig.temper) and drawn by face()


@style("face", "beard")
def face_beard(F, size, word):
    """A beard of cloud, streaming back over one shoulder."""
    P = F.P
    hr = P.hr
    c = Vector((0, P.hy0 + 0.25 * hr, P.chin + 0.05 * hr))
    geo = cloud(c + Vector((0, -0.1 * hr, -0.02)), 0.6 * hr * size, n=4, seed=3, sub=1)
    pts = [c + Vector((0.2 * hr, 0.3 * hr, -0.3 * hr)), c + Vector((0.9 * hr, 1.3 * hr, -0.2 * hr)), c + Vector((1.5 * hr, 2.6 * hr, 0.3 * hr)), c + Vector((1.7 * hr, 4.0 * hr * size, 0.9 * hr))]
    F.add("beard", geo, "mist_white", "head", smooth=True)
    tail = None
    for i, p in enumerate(pts[1:]):
        tail = g.merge(tail, cloud(p, (0.62 - 0.11 * i) * hr * size, n=4, seed=5 + i, sub=1 if i < 2 else 0))
    F.move("sway", "beard", [(tail, "mist_white")], c + Vector((0.2 * hr, 0.3 * hr, 0)), "head", smooth=True)


# --- hair: the element ----------------------------------------------------------------------

def _scalp(F, material, thick=0.022):
    pt = _lp().people_things
    F.P.wear(pt.scalp(F.P), F.m(material), thick)


def _head(F):
    P = F.P
    return P.hr, P.hcy, P.crown, P.hy0, P.hy1


@style("hair", "wisps")
def hair_wisps(F, size, word):
    """Not yet any element's: pale wisps that lie over to one side, in a wind that is not in the room."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "mist_cloud")
    geo = None
    for i in range(7):
        dx = -0.7 + 1.4 * i / 6
        b0 = Vector((dx * hr * 0.8, y0 + (0.35 + 0.5 * abs(dx)) * hr, top - (0.12 + 0.3 * dx * dx) * hr))
        tip = b0 + Vector((0.9 + 0.3 * rnd(i), 0.5 + 0.4 * rnd(i, 2), 0.25 + 0.5 * rnd(i, 3))) * hr * size
        geo = g.merge(geo, ribbon([b0, b0 + (tip - b0) * 0.5 + Vector((0, 0, 0.18 * hr)), tip], [0.5 * hr, 0.42 * hr, 0.05 * hr], normal=(dx, -0.3, 1), thick=0.4))
    F.move("glide", "hair", [(geo, "mist_white")], (0, cy, top - 0.2 * hr), "head", side="l", smooth=True)


@style("hair", "crystals")
def hair_crystals(F, size, word):
    """Ore come up through the scalp: short crystals of its Path's colour."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "accent_deep")
    geo, tips = None, None
    for i in range(9):
        a = 2 * math.pi * i / 9 + 0.3
        rad = (0.3 + 0.42 * (i % 3) / 2) * hr
        b0 = Vector((math.cos(a) * rad, cy + 0.1 * hr + math.sin(a) * rad * 1.1, top - 0.14 * hr - 0.5 * rad * rad / hr))
        d = Vector((math.cos(a) * 0.5, math.sin(a) * 0.5 + 0.12, 1.0)).normalized()
        L = (0.5 + 0.5 * rnd(i, 4)) * hr * size
        geo = g.merge(geo, shard(b0 - d * 0.03, b0 + d * L, 0.15 * hr, n=5))
        tips = g.merge(tips, shard(b0 + d * L * 0.62, b0 + d * L * 1.02, 0.07 * hr, n=5, belly=0.1))
    F.add("crystals", geo, "accent", "head", smooth=False)
    F.add("crystal_tips", tips, "accent_pale", "head", smooth=False)


@style("hair", "leaves")
def hair_leaves(F, size, word):
    """Leaves for hair, the gold of the turning year, over moss."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "moss_green")
    a_geo, b_geo = None, None
    for i in range(13):
        a = 2 * math.pi * i / 13
        ring = 0.86 if i % 2 else 0.5
        b0 = Vector((math.cos(a) * ring * hr, cy + 0.08 * hr + math.sin(a) * ring * hr * 1.05, top - (0.1 + 0.5 * ring * ring) * hr))
        d = Vector((math.cos(a) * (0.7 if i % 2 else 0.3), math.sin(a) * (0.7 if i % 2 else 0.3) + 0.2, 0.75 if i % 2 else 1.0)).normalized()
        leaf = g.blade(b0, b0 + d * (0.62 + 0.3 * rnd(i, 5)) * hr * size, 0.42 * hr * size, normal=(-d.x, -d.y, 0.6), belly=0.45, curl=-0.12)
        if i % 3 == 0:
            b_geo = g.merge(b_geo, leaf)
        else:
            a_geo = g.merge(a_geo, leaf)
    F.move("sway", "hair", [(a_geo, "accent"), (b_geo, "accent_light")], (0, cy, top - 0.3 * hr), "head", smooth=True)


@style("hair", "flame")
def hair_flame(F, size, word):
    """Hair that is a low flame: its Path's colour, and the field at the heart of it."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "slag_dark")
    outer, inner = None, None
    for i in range(8):
        a = 2 * math.pi * i / 8
        rad = 0.5 * hr * (0.4 + 0.6 * (i % 2))
        b0 = Vector((math.cos(a) * rad, cy + 0.1 * hr + math.sin(a) * rad, top - 0.2 * hr))
        L = (0.8 + 0.55 * rnd(i, 6)) * hr * size
        lean = Vector((math.cos(a) * 0.2, math.sin(a) * 0.2 + 0.18, 1.0)).normalized()
        outer = g.merge(outer, ribbon([b0, b0 + lean * L * 0.5 + Vector((0.05 * hr, 0, 0)), b0 + lean * L], [0.42 * hr, 0.36 * hr, 0.03 * hr], normal=(math.cos(a), math.sin(a), 0.1), thick=0.6))
    c = Vector((0, cy + 0.1 * hr, top - 0.12 * hr))
    inner = ribbon([c, c + Vector((0, 0.04 * hr, 0.45 * hr * size)), c + Vector((0.03 * hr, 0.1 * hr, 0.95 * hr * size))], [0.5 * hr, 0.4 * hr, 0.03 * hr], normal=Y, thick=0.9)
    F.move("flick", "hair", [(outer, "accent"), (inner, field("flame", 3.0))], (0, cy + 0.1 * hr, top - 0.22 * hr), "head", smooth=True)


@style("hair", "water")
def hair_water(F, size, word):
    """Hair that is running water: it falls down its back and does not stop falling."""
    P = F.P
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "accent_dark")
    fall = (top - P.hipz) * (0.78 * size)
    a_geo, b_geo, foam = None, None, None
    for i in range(7):
        dx = -1.0 + 2.0 * i / 6
        b0 = Vector((dx * hr * 0.82, cy + (0.5 - 0.3 * dx * dx) * hr, top - (0.16 + 0.42 * dx * dx) * hr))
        mid = Vector((dx * hr * 1.05, y1 + (0.34 - 0.2 * dx * dx) * hr, top - fall * 0.42))
        low = Vector((dx * hr * (0.9 + 0.25 * math.sin(i * 1.7)), y1 + (0.5 + 0.2 * math.sin(i * 2.3)) * hr, top - fall * (0.84 + 0.16 * rnd(i, 7))))
        lock = ribbon([b0, b0 + (mid - b0) * 0.4 + Vector((0, 0.3 * hr, 0.06 * hr)), mid, low], [0.5 * hr, 0.56 * hr, 0.5 * hr, 0.1 * hr], normal=(dx * 0.4, 1, 0.1), thick=0.42)
        if i % 2:
            b_geo = g.merge(b_geo, lock)
        else:
            a_geo = g.merge(a_geo, lock)
        foam = g.merge(foam, g.ico(low, 0.1 * hr, sub=0))
    for sg in (1, -1):          # a lock before each ear, down over the collar-bone
        b0 = Vector((sg * hr * 0.92, y0 + 0.62 * hr, P.eye.z + 0.7 * hr))
        a_geo = g.merge(a_geo, ribbon([b0, b0 + Vector((sg * 0.16 * hr, -0.1 * hr, -0.9 * hr)), b0 + Vector((sg * 0.22 * hr, -0.3 * hr, -2.2 * hr * min(1.2, size)))], [0.4 * hr, 0.36 * hr, 0.05 * hr], normal=(sg, -1, 0), thick=0.42))
    F.move("sway", "hair", [(a_geo, "accent"), (b_geo, "accent_light"), (foam, "water_foam")], (0, cy + 0.2 * hr, top - 0.25 * hr), "head", smooth=True)


@style("hair", "weed")
def hair_weed(F, size, word):
    """Weed for hair, standing up as it does under water."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "weed_dark")
    for k in range(3):
        geo, tips = None, None
        for i in range(3):
            j = k * 3 + i
            a = 2 * math.pi * j / 9
            b0 = Vector((math.cos(a) * 0.5 * hr, cy + 0.1 * hr + math.sin(a) * 0.55 * hr, top - 0.2 * hr))
            L = (2.0 + 0.9 * rnd(j, 8)) * hr * size
            sw = Vector((math.cos(a + 1.0), math.sin(a + 1.0), 0)) * 0.28 * hr
            pts = [b0, b0 + Vector((0, 0, L * 0.33)) + sw, b0 + Vector((0, 0, L * 0.66)) - sw * 0.8, b0 + Vector((0, 0, L)) + sw * 0.9]
            geo = g.merge(geo, ribbon(pts, [0.3 * hr, 0.4 * hr, 0.34 * hr, 0.05 * hr], normal=(math.cos(a), math.sin(a), 0), thick=0.3))
            tips = g.merge(tips, g.ico(pts[-1], 0.07 * hr, sub=0))
        F.move("sway", "hair", [(geo, "accent" if k != 1 else "weed_dark"), (tips, "accent_pale")], (0, cy + 0.1 * hr, top - 0.25 * hr), "head", n=k, smooth=True)


@style("hair", "wind")
def hair_wind(F, size, word):
    """Hair that streams out sideways, in a wind nobody else can feel (forward: the way you are going)."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "accent_light")
    way = Vector((0.25, -1.0, 0.15)) if word == "forward" else Vector((1.0, 0.3, 0.12))
    a_geo, b_geo = None, None
    for i in range(8):
        dx = -0.8 + 1.6 * i / 7
        b0 = Vector((dx * hr * 0.75, cy + (0.1 + 0.4 * math.cos(i * 1.9)) * hr, top - (0.14 + 0.36 * dx * dx) * hr))
        L = (1.9 + 1.3 * rnd(i, 9)) * hr * size
        up = Vector((0, 0, (0.35 - 0.12 * i % 3) * hr))
        pts = [b0, b0 + way * L * 0.3 + up, b0 + way * L * 0.66 + up * 0.4 + Vector((0, 0.1 * hr * math.sin(i), 0)), b0 + way * L + Vector((0, 0, 0.22 * hr * math.sin(i * 2.1)))]
        lock = ribbon(pts, [0.46 * hr, 0.44 * hr, 0.3 * hr, 0.03 * hr], normal=(0, -0.3, 1) if word != "forward" else (1, 0, 0.3), thick=0.4)
        if i % 3 == 0:
            b_geo = g.merge(b_geo, lock)
        else:
            a_geo = g.merge(a_geo, lock)
    if word == "forward":
        F.move("sway", "hair", [(a_geo, "accent_pale"), (b_geo, "accent")], (0, cy, top - 0.25 * hr), "head", smooth=True)
    else:
        F.move("glide", "hair", [(a_geo, "accent_pale"), (b_geo, "accent")], (0, cy, top - 0.25 * hr), "head", side="l", smooth=True)


@style("hair", "rays")
def hair_rays(F, size, word):
    """Rays for hair: they stand out round the back of its head like the first of the sun."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "accent_pale")
    c = Vector((0, cy + 0.2 * hr, top - 0.62 * hr))
    a_geo, b_geo = None, None
    n = 11
    for i in range(n):
        a = math.pi * (-0.12 + 1.24 * i / (n - 1))
        d = Vector((math.cos(a), 0.12, math.sin(a)))
        L = (1.35 if i % 2 == 0 else 0.85) * hr * size
        ray = g.blade(c + d * hr * 0.7, c + d * (hr * 0.9 + L), 0.3 * hr, normal=Y, belly=0.25, thick=0.02 * hr)
        if i % 2:
            b_geo = g.merge(b_geo, ray)
        else:
            a_geo = g.merge(a_geo, ray)
    F.move("pulse", "rays", [(a_geo, "accent2_light"), (b_geo, "accent2")], c, "head", smooth=False)


@style("hair", "spikes")
def hair_spikes(F, size, word):
    """Hair that stands straight up and crackles."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "accent_light")
    geo, sparks = None, None
    for i in range(9):
        a = 2 * math.pi * i / 9
        rad = 0.5 * hr * (0.35 + 0.65 * (i % 2))
        b0 = Vector((math.cos(a) * rad, cy + 0.1 * hr + math.sin(a) * rad, top - 0.2 * hr))
        L = (1.5 + 0.9 * rnd(i, 10)) * hr * size
        d = Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 1.0)).normalized()
        geo = g.merge(geo, g.blade(b0, b0 + d * L, 0.3 * hr, normal=(math.cos(a), math.sin(a), 0), belly=0.2))
        if i % 3 == 0:
            sparks = g.merge(sparks, bolt(b0 + d * L * 0.9, b0 + d * (L + 0.55 * hr) + Vector((math.cos(a), math.sin(a), 0)) * 0.3 * hr, 0.1 * hr, seed=i, n=3, normal=(math.sin(a), -math.cos(a), 0)))
    F.move("flick", "hair", [(geo, "accent_pale"), (sparks, field("sparks", 3.4))], (0, cy + 0.1 * hr, top - 0.25 * hr), "head", smooth=False)


# --- crowns ---------------------------------------------------------------------------------

@style("crown", "columns")
def crown_columns(F, size, word):
    """A crown of basalt columns, no two a height, lichen on their tops."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "stone_band")
    geo, caps = None, None
    n = 8
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        rad = 0.74 * hr
        b0 = Vector((math.cos(a) * rad, cy + 0.06 * hr + math.sin(a) * rad * 1.08, top - 0.52 * hr))
        hgt = (0.75 + 0.75 * rnd(i, 11) + (0.35 if math.sin(a) > 0.3 else 0.0)) * hr * size
        geo = g.merge(geo, prism(b0, b0 + Vector((math.cos(a) * 0.05 * hr, math.sin(a) * 0.05 * hr, hgt)), 0.3 * hr, n=6, phase=a))
        if i % 2 == 0:
            caps = g.merge(caps, prism(b0 + Vector((0, 0, hgt)), b0 + Vector((0, 0, hgt + 0.07 * hr)), 0.3 * hr, n=6, phase=a, taper=0.8))
    F.add("crown", geo, "stone_basalt", "head", smooth=False)
    F.add("crown_caps", caps, "accent", "head", smooth=False)


@style("crown", "peak")
def crown_peak(F, size, word):
    """A peak for a crown, with snow on it."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "stone_band")
    c = Vector((0, cy + 0.1 * hr, top - 0.36 * hr))
    hgt = 2.5 * hr * size
    rock = g.lathe([(1.02 * hr, 0.0), (0.84 * hr, 0.3 * hgt), (0.5 * hr, 0.62 * hgt), (0.2 * hr, 0.86 * hgt), (0.0, hgt)], n=7, centre=c, phase=0.3)
    rock = ([p + Vector((0.06 * hr * math.sin(p.z * 9.0), 0.05 * hr * math.cos(p.z * 7.0), 0)) for p in rock[0]], rock[1])
    snow = g.lathe([(0.56 * hr, 0.6 * hgt), (0.25 * hr, 0.86 * hgt), (0.0, hgt + 0.03 * hr)], n=7, centre=c + Vector((0, 0, 0.012)), phase=0.3, caps=False)
    F.add("peak", rock, "stone_slab", "head", smooth=False)
    F.add("peak_snow", snow, "ice_white", "head", smooth=False)
    F.add("peak_band", hoop(c + Vector((0, 0, 0.05 * hr)), 1.05 * hr, 1.05 * hr, 0.07 * hr, n=10, sides=4), "accent", "head", smooth=False)


@style("crown", "wheat")
def crown_wheat(F, size, word):
    """A crown of wheat-ears on a band."""
    hr, cy, top, y0, y1 = _head(F)
    c = Vector((0, cy + 0.06 * hr, top - 0.5 * hr))
    F.add("wheat_band", hoop(c, 1.02 * hr, 1.1 * hr, 0.07 * hr, n=12, sides=4), "accent_dark", "head", smooth=False)
    stalks, ears = None, None
    n = 11
    for i in range(n):
        a = 2 * math.pi * i / n
        b0 = c + Vector((math.cos(a) * 1.0 * hr, math.sin(a) * 1.08 * hr, 0))
        d = Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, 1.0)).normalized()
        L = (1.0 + 0.5 * rnd(i, 12)) * hr * size
        stalks = g.merge(stalks, g.tube([b0, b0 + d * L], [0.035 * hr, 0.025 * hr], n=3))
        for j in range(3):
            q = b0 + d * (L + (j - 0.4) * 0.22 * hr)
            ears = g.merge(ears, g.ico(q, 0.13 * hr, sub=0, scale=(0.8, 0.8, 1.5)))
    F.add("wheat_stalks", stalks, "straw_wheat", "head", smooth=True)
    F.move("sway", "wheat", [(ears, "accent_light")], c, "head", smooth=False)


@style("crown", "crater")
def crown_crater(F, size, word):
    """The top of its head open like a crater, and burning."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "slag_dark", 0.03)
    c = Vector((0, cy + 0.1 * hr, top - 0.3 * hr))
    rim = None
    n = 9
    for i in range(n):
        a = 2 * math.pi * i / n
        b0 = c + Vector((math.cos(a) * 0.72 * hr, math.sin(a) * 0.8 * hr, -0.2 * hr))
        tip = c + Vector((math.cos(a) * 0.92 * hr, math.sin(a) * 1.0 * hr, (0.5 + 0.5 * rnd(i, 13)) * hr * size))
        rim = g.merge(rim, shard(b0, tip, 0.34 * hr, n=4, belly=0.4))
    F.add("crater", rim, "slag_dark", "head", smooth=False)
    F.add("crater_lip", hoop(c + Vector((0, 0, 0.12 * hr)), 0.7 * hr, 0.78 * hr, 0.09 * hr, n=10, sides=4), "accent_light", "head", smooth=False)
    fire, glow = None, None
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.4
        b0 = c + Vector((math.cos(a) * 0.3 * hr, math.sin(a) * 0.3 * hr, 0.1 * hr))
        L = (1.2 + 0.9 * rnd(i, 14)) * hr * size
        fire = g.merge(fire, ribbon([b0, b0 + Vector((0.08 * hr * math.cos(a), 0.08 * hr * math.sin(a), L * 0.5)), b0 + Vector((0, 0.1 * hr, L))], [0.44 * hr, 0.36 * hr, 0.03 * hr], normal=(math.cos(a), math.sin(a), 0), thick=0.7))
    glow = ribbon([c, c + Vector((0, 0, 0.6 * hr * size)), c + Vector((0.03 * hr, 0.05 * hr, 1.25 * hr * size))], [0.55 * hr, 0.42 * hr, 0.03 * hr], normal=Y, thick=0.9)
    F.move("flick", "fire", [(fire, "accent"), (glow, field("flame", 3.2))], c, "head", smooth=True)


@style("crown", "shards")
def crown_shards(F, size, word):
    """A crown of clear shards of ice."""
    hr, cy, top, y0, y1 = _head(F)
    _scalp(F, "ice_white")
    geo, alt = None, None
    n = 9
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        b0 = Vector((math.cos(a) * 0.7 * hr, cy + 0.06 * hr + math.sin(a) * 0.76 * hr, top - 0.46 * hr))
        d = Vector((math.cos(a) * 0.42, math.sin(a) * 0.42, 1.0)).normalized()
        L = (1.2 + 1.0 * rnd(i, 15) + (0.5 if math.sin(a) > 0.2 else 0)) * hr * size
        sh = shard(b0, b0 + d * L, 0.2 * hr, n=4, belly=0.22)
        if i % 2:
            alt = g.merge(alt, sh)
        else:
            geo = g.merge(geo, sh)
    F.add("shards", geo, "ice_clear", "head", smooth=False)
    F.add("shards_b", alt, "accent_pale", "head", smooth=False)


@style("crown", "lure")
def crown_lure(F, size, word):
    """A lure of light, hung before its brow on a long stalk."""
    hr, cy, top, y0, y1 = _head(F)
    b0 = Vector((0, y0 + 0.5 * hr, top - 0.12 * hr))
    pts = [b0, b0 + Vector((0, -0.3 * hr, 1.0 * hr)) * size, b0 + Vector((0, -1.5 * hr, 1.35 * hr)) * size, b0 + Vector((0, -2.3 * hr, 0.6 * hr)) * size, b0 + Vector((0, -2.45 * hr, -0.1 * hr)) * size]
    stalk = g.tube(pts, [0.09 * hr, 0.07 * hr, 0.05 * hr, 0.035 * hr, 0.03 * hr], n=5)
    lamp = g.ico(pts[-1] + Vector((0, 0, -0.26 * hr)), 0.3 * hr * size, sub=1, scale=(1, 1, 1.25))
    cage = hoop(pts[-1] + Vector((0, 0, -0.26 * hr)), 0.33 * hr * size, 0.33 * hr * size, 0.03 * hr, u=X, v=Y, n=8, sides=3)
    F.move("sway", "lure", [(stalk, "accent"), (lamp, field("lure", 3.8)), (cage, "accent_pale")], b0, "head", smooth=True)


@style("crown", "anvil")
def crown_anvil(F, size, word):
    """A tower of cloud worn like a headdress, flat on top; small lightnings run in it."""
    hr, cy, top, y0, y1 = _head(F)
    c = Vector((0, cy + 0.1 * hr, top - 0.1 * hr))
    dark = g.merge(cloud(c + Vector((0, 0, 0.2 * hr)), 1.15 * hr * size, n=5, seed=20), cloud(c + Vector((0.1 * hr, 0, 1.0 * hr * size)), 1.3 * hr * size, n=5, seed=21))
    pale = g.merge(cloud(c + Vector((0, 0, 1.95 * hr * size)), 1.75 * hr * size, n=6, seed=22, flat=0.6), g.ico(c + Vector((0, 0, 2.5 * hr * size)), 2.5 * hr * size, sub=1, scale=(1.0, 0.72, 0.2)))
    bolts = g.merge(bolt(c + Vector((0.5 * hr, -1.0 * hr * size, 1.5 * hr * size)), c + Vector((0.1 * hr, -1.08 * hr * size, 0.4 * hr)), 0.14 * hr, seed=1),
                    bolt(c + Vector((-0.8 * hr, -0.95 * hr * size, 1.25 * hr * size)), c + Vector((-0.5 * hr, -1.0 * hr * size, 0.55 * hr)), 0.1 * hr, seed=2, n=3))
    F.move("pulse", "anvil", [(dark, "mist_storm"), (pale, "mist_cloud"), (bolts, field("bolt", 3.6))], c, "head", smooth=True)


# --- what it wears ----------------------------------------------------------------------------

@style("wear", "wrap")
def wear_wrap(F, size, word):
    """A wrap at its hips: its partner's coat again, in cloth, with a fall before and behind."""
    P = F.P
    cloth = F.m("under")
    P.wear(P.trunk(P.hipz - 0.2 * size * P.t, P.hipz + 0.15 * P.t), cloth, 0.03)
    hw, hd, yo = P.ring(P.hipz)
    F.add("wrap_front", g.blade((0, yo - hd - 0.03, P.hipz + 0.12 * P.t), (0.02, yo - hd - 0.07, P.hipz - 0.46 * size * P.t), 1.45 * hw, normal=Y, belly=0.36), cloth, "hips", smooth=True)
    F.add("wrap_back", g.blade((0, yo + hd + 0.03, P.hipz + 0.1 * P.t), (-0.02, yo + hd + 0.08, P.hipz - 0.4 * size * P.t), 1.4 * hw, normal=Y, belly=0.36), cloth, "hips", smooth=True)
    F.add("wrap_belt", hoop((0, yo, P.hipz + 0.15 * P.t), hw + 0.035, hd + 0.04, 0.03 * P.t, n=12, sides=4), "trim", "hips", smooth=False)


@style("wear", "band")
def wear_band(F, size, word):
    """A band across the chest."""
    P = F.P
    P.wear(P.trunk(P.chestz - 0.1 * P.t, P.chestz + 0.13 * P.t), F.m(word or "under"), 0.022)


@style("wear", "sash")
def wear_sash(F, size, word):
    """A sash of its Path's colour, its end hanging."""
    P = F.P
    P.wear(P.trunk(P.hipz + 0.1 * P.t, P.hipz + 0.27 * P.t), mat("accent"), 0.05)
    hw, hd, yo = P.ring(P.hipz + 0.15 * P.t)
    b0 = Vector((hw * 0.72, yo - hd * 0.62 - 0.05, P.hipz + 0.17 * P.t))
    end = g.blade(b0, b0 + Vector((0.05, -0.04, -0.5 * size * P.t)), 0.16 * P.t, normal=(0.4, -1, 0), belly=0.62)
    tip = g.blade(b0 + Vector((0.04, -0.045, -0.36 * size * P.t)), b0 + Vector((0.055, -0.05, -0.53 * size * P.t)), 0.12 * P.t, normal=(0.4, -1, 0), belly=0.4)
    F.move("sway", "sash", [(end, "accent_dark"), (tip, "accent_light")], b0, "hips", smooth=True)


@style("wear", "kilt")
def wear_kilt(F, size, word):
    """A kilt banded with its Path's colour: to the knee at 1, to the feet near 1.7."""
    P = F.P
    pd = _lp().people_dress
    z0 = P.hipz + 0.13 * P.t
    z1 = max(P.footz + 0.05, P.hipz - 0.52 * size * P.t)
    P.wear(P.trunk(P.hipz - 0.08, P.hipz + 0.2 * P.t), mat("accent_dark"), 0.035)
    hw, hd, yo = P.ring(z0)
    steps = 6
    rings, mats = [], []
    for i in range(steps + 1):
        t = i / steps
        z = z0 + (z1 - z0) * t
        k = t ** 0.8
        fl = (0.1 if size < 1.4 else 0.06) * P.t
        rings.append([Vector(((hw + 0.035 + fl * k) * math.cos(2 * math.pi * j / 12), yo + (hd + 0.035 + fl * k) * math.sin(2 * math.pi * j / 12), z)) for j in range(12)])
    for i in range(steps):
        band = g.loft([rings[i], rings[i + 1]], caps=(i == steps - 1))
        F.add("kilt_%d" % i, band, ("accent", "accent_dark", "accent", "accent_light", "accent", "accent_dark")[i % 6], "hips", smooth=True)


@style("wear", "mantle")
def wear_mantle(F, size, word):
    """Over its shoulders: flat stones laid like slates (stones), or moss with leaves in it (moss)."""
    P = F.P
    c = Vector((0, P.J["head"].y + 0.03, P.neckz))
    sw = P.sx + 0.09
    if word == "stones":
        geo, gold = None, None
        for row in range(2):
            n = 7 + 2 * row
            for i in range(n):
                a = math.pi * (-0.98 + 1.96 * i / (n - 1))
                rad = (0.62 + 0.42 * row) * sw * size
                p = Vector((math.sin(a) * rad * 1.08, c.y + 0.02 + math.cos(a) * rad * 0.8, P.armz + (0.13 - 0.16 * row) * P.t - 0.03 * abs(math.sin(a)) * row))
                plate = lump(p, 0.2 * sw * size, seed=row * 10 + i, sub=0, scale=(1.25, 1.25, 0.34), rough=0.14)
                plate = g.moved(plate, Matrix.Translation(p) @ Matrix.Rotation(-0.5 * math.sin(a) * (0.5 + 0.5 * row), 4, "Y") @ Matrix.Rotation(0.4 * math.cos(a) * row, 4, "X") @ Matrix.Translation(-p))
                if (i + row) % 4 == 0:
                    gold = g.merge(gold, plate)
                else:
                    geo = g.merge(geo, plate)
        F.add("mantle", geo, "stone_slab", "chest", smooth=False)
        F.add("mantle_ore", gold, "accent", "chest", smooth=False)
    else:
        pd = _lp().people_dress
        z0, z1 = P.neckz + 0.02, P.armz - 0.2 * size * P.t
        cape = pd.drape((0, c.y + 0.02, 0), lambda t: (0.12 + (sw + 0.07 - 0.12) * t ** 0.6, 0.12 + (sw * 0.8 - 0.12) * t ** 0.6), [z0, (z0 + z1) / 2 + 0.05, z1], -math.pi * 0.96, math.pi * 0.96, thick=0.035, n=12)
        F.add("mantle", cape, "moss_green", "chest", smooth=True)
        leaves, pale = None, None
        for i in range(11):
            a = math.pi * (-0.92 + 1.84 * i / 10)
            b0 = Vector((math.sin(a) * (sw + 0.06), c.y + 0.02 + math.cos(a) * sw * 0.8, z1 + 0.04))
            d = Vector((math.sin(a) * 0.5, math.cos(a) * 0.5, -1.0)).normalized()
            leaf = g.blade(b0, b0 + d * (0.2 + 0.1 * rnd(i, 16)) * P.t * size, 0.15 * P.t, normal=(math.sin(a), math.cos(a), 0.3), belly=0.45)
            if i % 3:
                leaves = g.merge(leaves, leaf)
            else:
                pale = g.merge(pale, leaf)
        F.move("sway", "mantle", [(leaves, "accent"), (pale, "accent_light")], (0, c.y, z1 + 0.06), "chest", smooth=True)


@style("wear", "apron")
def wear_apron(F, size, word):
    """A smith's apron: leather, to the knee."""
    P = F.P
    lea = mat("leather_apron")
    P.wear(P.trunk(P.hipz - 0.04, P.chestz + 0.12 * P.t, front=True) & (np.abs(P.v0[:, 0]) < P.ring(P.chestz)[0] * 0.8), lea, 0.035)
    hw, hd, yo = P.ring(P.hipz)
    z1 = P.kneez - 0.02
    F.add("apron", ribbon([(0, yo - hd - 0.05, P.hipz + 0.16 * P.t), (0, yo - hd - 0.09, (P.hipz + z1) / 2), (0, yo - hd - 0.1, z1)], [1.7 * hw, 1.9 * hw, 1.7 * hw], normal=Y, thick=0.08), lea, "hips", smooth=True)
    F.add("apron_tie", hoop((0, yo, P.hipz + 0.2 * P.t), hw + 0.04, hd + 0.045, 0.022 * P.t, n=12, sides=4), "accent", "hips", smooth=False)


@style("wear", "bracers")
def wear_bracers(F, size, word):
    """Its forearms banded with brass."""
    P = F.P
    pd = _lp().people_dress
    for sg, tag in ((1, "l"), (-1, "r")):
        geo = None
        for k in range(3):
            x = P.ex + (P.wx - P.ex) * (0.3 + 0.28 * k)
            row = pd.arm_row(P, x)
            geo = g.merge(geo, hoop((sg * x, P.army, P.armz), row[1] + 0.022, row[2] + 0.022, 0.026 * size, u=Y, v=Z, n=8, sides=4))
        F.add("bracers_" + tag, geo, "brass_band", "lowerarm." + tag, smooth=False)


@style("wear", "pauldrons")
def wear_pauldrons(F, size, word):
    """Plates of ice on its shoulders, edged and angular."""
    P = F.P
    for sg, tag in ((1, "l"), (-1, "r")):
        c = Vector((sg * (P.sx + 0.02), P.army, P.armz + 0.08 * P.t))
        plate = g.merge(shard(c + Vector((-sg * 0.14, 0, -0.03)), c + Vector((sg * 0.34 * size, 0.02, 0.2 * size)), 0.17 * size, n=4, belly=0.4),
                        shard(c + Vector((-sg * 0.1, 0.05, -0.02)), c + Vector((sg * 0.2 * size, 0.2, 0.3 * size)), 0.11 * size, n=4, belly=0.4),
                        shard(c + Vector((-sg * 0.1, -0.05, -0.02)), c + Vector((sg * 0.24 * size, -0.16, 0.14 * size)), 0.11 * size, n=4, belly=0.4))
        F.add("pauldron_" + tag, plate, "ice_clear", "chest", smooth=False)
    F.add("gorget", hoop((0, P.J["head"].y + 0.03, P.neckz - 0.03), 0.17 * P.t, 0.17 * P.t, 0.04 * P.t, n=8, sides=4), "accent", "chest", smooth=False)


@style("wear", "stole")
def wear_stole(F, size, word):
    """A long stole that loops out behind it like a river seen from a hill."""
    P = F.P
    c = Vector((0, P.J["head"].y + 0.03, P.neckz))
    sw = P.sx
    w = 0.2 * P.t
    # over the shoulders, down the back, then out behind in bends
    front = None
    for sg in (1, -1):
        front = g.merge(front, ribbon([(sg * sw * 0.55, P.front(P.chestz, sg * sw * 0.5) - 0.04, P.chestz - 0.12 * P.t), (sg * sw * 0.6, c.y - 0.02, P.armz + 0.09 * P.t), (sg * sw * 0.45, P.rear(P.armz) + 0.05, P.armz - 0.05 * P.t)],
                                      [w * 0.7, w, w], normal=(0, -0.3, 1), thick=0.22))
    F.add("stole_yoke", front, "accent", "chest", smooth=True)
    by = P.rear(P.chestz) + 0.06
    L = 2.2 * size * P.t
    pts, pts2 = [], []
    for i in range(9):
        t = i / 8
        pts.append(Vector((0.55 * math.sin(t * math.pi * 2.3) * (0.25 + t) * L * 0.5, by + t * L * 0.62, P.chestz - 0.05 - t * (P.chestz - P.hipz + 0.3 * P.t) + 0.12 * math.sin(t * 7.0) * P.t)))
    half = 5
    a_geo = ribbon(pts[:half], [w, w * 1.1, w * 1.2, w * 1.25, w * 1.3], normal=Z, thick=0.2)
    b_geo = ribbon(pts[half - 1:], [w * 1.3, w * 1.3, w * 1.2, w * 0.9, w * 0.2], normal=Z, thick=0.2)
    edge = g.tube(pts, [0.02 * P.t] * 9, n=3)
    F.move("sway", "stole", [(a_geo, "accent"), (b_geo, "accent_light"), (edge, "water_foam")], (0, by, P.chestz), "chest", smooth=True)


@style("wear", "scarf")
def wear_scarf(F, size, word):
    """A scarf of its Path's colour, its ends streaming out sideways."""
    P = F.P
    c = Vector((0, P.J["head"].y + 0.02, P.neckz - 0.01))
    r = 0.105 * P.t + 0.035
    F.add("scarf", hoop(c, r + 0.03, r + 0.03, 0.06 * P.t, n=10, sides=5), "accent", "chest", smooth=True)
    b0 = c + Vector((r * 0.8, 0.05, 0))
    L = 1.5 * size * P.t
    a_geo = ribbon([b0, b0 + Vector((0.3 * L, 0.06, 0.08 * P.t)), b0 + Vector((0.66 * L, 0.12, -0.02 * P.t)), b0 + Vector((L, 0.1, 0.1 * P.t))], [0.17 * P.t, 0.2 * P.t, 0.19 * P.t, 0.05 * P.t], normal=Z, thick=0.2)
    b_geo = ribbon([b0 + Vector((0, 0.05, -0.04)), b0 + Vector((0.26 * L, 0.16, -0.14 * P.t)), b0 + Vector((0.72 * L, 0.22, -0.2 * P.t))], [0.15 * P.t, 0.17 * P.t, 0.04 * P.t], normal=Z, thick=0.2)
    F.move("glide", "scarf", [(a_geo, "accent"), (b_geo, "accent_dark")], b0, "chest", side="l", smooth=True)


@style("wear", "cloak")
def wear_cloak(F, size, word):
    """A long cloak from the shoulders. wind: it never hangs down (it is made hanging; a body laid
    along the wind lays it there too). ice: a sheet of ice that drags stones. dusk: the colour of the hour."""
    P = F.P
    c = Vector((0, P.J["head"].y + 0.03, P.neckz))
    sw = P.sx + 0.06
    by = P.rear(P.armz) + 0.04
    z0 = P.armz + 0.06 * P.t
    F.add("cloak_yoke", hoop((0, c.y + 0.01, P.neckz - 0.02), 0.19 * P.t, 0.19 * P.t, 0.05 * P.t, n=10, sides=4), "accent_dark", "chest", smooth=True)
    if word == "ice":
        L = (z0 - P.footz) * 1.0
        pts = [Vector((0, by, z0)), Vector((0, by + 0.12, z0 - L * 0.4)), Vector((0, by + 0.5 * size, z0 - L * 0.8)), Vector((0, by + 1.3 * size, P.footz + 0.08)), Vector((0, by + 2.1 * size, P.footz + 0.03))]
        sheet = ribbon(pts, [sw * 1.7, sw * 2.2, sw * 2.6, sw * 2.9, sw * 1.2], normal=(0, 1, 0.3), thick=0.14)
        F.add("cloak", sheet, "ice_clear", "chest", smooth=False)
        F.add("cloak_band", ribbon([p + Vector((0, 0.012, 0.012)) for p in pts[1:4]], [sw * 0.5, sw * 0.6, sw * 0.6], normal=(0, 1, 0.3), thick=0.12), "accent", "chest", smooth=False)
        rocks = None
        for i in range(5):
            p = Vector(((-0.9 + 0.45 * i) * sw * 1.1, by + (1.2 + 0.5 * rnd(i, 17)) * size, P.footz + 0.1))
            rocks = g.merge(rocks, lump(p, (0.1 + 0.08 * rnd(i, 18)) * size, seed=i, sub=0))
        F.add("cloak_stones", rocks, "stone_basalt", "chest", smooth=False)
        return
    L = (z0 - P.footz) * (1.12 * size if word == "wind" else 0.9 * size)
    n = 5
    a_geo, b_geo = None, None
    for i in range(n):
        dx = -1.0 + 2.0 * i / (n - 1)
        fl = 0.16 * math.sin(i * 2.4)
        pts = [Vector((dx * sw * 0.8, by + 0.02 * abs(dx), z0 - 0.03 * abs(dx))), Vector((dx * sw * 1.0, by + 0.16 + 0.05 * fl, z0 - L * 0.35)),
               Vector((dx * sw * (1.15 + fl), by + 0.26 - 0.1 * fl, z0 - L * 0.7)), Vector((dx * sw * (1.2 + 1.5 * fl), by + 0.2 + 0.3 * fl, z0 - L * (0.92 + 0.08 * math.cos(i * 1.9))))]
        strip = ribbon(pts, [sw * 0.52, sw * 0.6, sw * 0.62, sw * (0.12 if word == "wind" else 0.5)], normal=(0, 1, 0), thick=0.14)
        if i % 2:
            b_geo = g.merge(b_geo, strip)
        else:
            a_geo = g.merge(a_geo, strip)
    if word == "dusk":
        F.move("sway", "cloak", [(a_geo, "accent"), (b_geo, "accent2_dark")], (0, by, z0), "chest", smooth=True)
    else:
        F.move("sway", "cloak", [(a_geo, "accent"), (b_geo, "accent_dark")], (0, by, z0), "chest", smooth=True)


@style("wear", "menhir")
def wear_menhir(F, size, word):
    """It has become the stone people steer by: a standing stone, and the figure in high relief on its face."""
    P = F.P
    by = P.rear(P.chestz) - 0.06
    sw = P.sx + 0.2
    top = P.crown + 0.42 * P.hh
    prof = [(-0.34, 0.92), (0.0, 1.0), (0.3 * (top + 0.3), 1.08), (0.62 * (top + 0.3), 1.02), (0.86 * (top + 0.3), 0.86), (0.97 * (top + 0.3), 0.6), (top, 0.0)]
    rings = []
    for z, k in prof:
        ring = []
        for j in range(8):
            a = 2 * math.pi * j / 8 + 0.2
            wob = 1.0 + 0.1 * math.sin(j * 2.3 + z * 3.0)
            ring.append(Vector((math.cos(a) * sw * k * wob, by + 0.3 + math.sin(a) * 0.34 * k * wob, z - 0.02 + (0.05 * math.sin(j * 1.7) if 0 < k < 1 else 0))))
        rings.append(ring)
    F.add("menhir", g.loft(rings), "stone_slab", "root", smooth=False)
    # lichen, and a line of the field cut down it
    spots = None
    for i in range(6):
        z = 0.2 + (top - 0.5) * rnd(i, 19)
        sg = 1 if i % 2 else -1
        spots = g.merge(spots, g.ico((sg * sw * (0.78 + 0.1 * rnd(i, 20)), by + 0.2 - 0.1 * rnd(i, 21), z), 0.12 + 0.06 * rnd(i, 22), sub=0, scale=(0.5, 1, 1)))
    F.add("menhir_lichen", spots, "accent", "root", smooth=False)
    F.add("menhir_band", hoop((0, by + 0.3, 0.26), sw * 1.03, 0.37, 0.035, n=10, sides=4), "accent_dark", "root", smooth=False)
    for sg in (1, -1):
        F.add("menhir_rune_%d" % sg, bolt((sg * sw * 0.7, by - 0.03, top - 0.5), (sg * sw * 0.82, by - 0.04, P.hipz), 0.05, seed=sg + 3, n=5), field("seam", 2.4), "root", smooth=False)


# --- chest and belt --------------------------------------------------------------------------

@style("chest", "heart")
def chest_heart(F, size, word):
    """A stone of its Path's colour set in its chest, and the field breathing in it."""
    P = F.P
    z = P.chestz + 0.03
    y = P.front(z) - 0.012
    c = Vector((0, y, z))
    F.move("pulse", "heart", [(g.ico(c, 0.062 * P.t * size, sub=1, scale=(1.0, 0.5, 1.25)), field("heart", 2.6))], c, "chest", smooth=False)
    F.add("heart_rim", hoop(c + Vector((0, 0.008, 0)), 0.078 * P.t * size, 0.095 * P.t * size, 0.016 * P.t, u=X, v=Z, n=8, sides=4), "accent_light", "chest", smooth=False)


@style("chest", "flower")
def chest_flower(F, size, word):
    """One flower, kept out of reach in the middle of the thorns."""
    P = F.P
    c = Vector((0, P.front(P.chestz) - 0.2, P.chestz + 0.05))
    petals = None
    for i in range(6):
        a = 2 * math.pi * i / 6
        d = Vector((math.cos(a), -0.35, math.sin(a))).normalized()
        petals = g.merge(petals, g.blade(c, c + d * 0.17 * size, 0.13 * size, normal=(0, -1, 0), belly=0.6, curl=-0.2))
    F.move("pulse", "flower", [(petals, "accent2_light"), (g.ico(c + Vector((0, -0.03, 0)), 0.045 * size, sub=1), field("heart", 2.8))], c, "chest", smooth=True)
    F.add("flower_stem", g.tube([c, c + Vector((0, 0.1, -0.1)), Vector((0, P.front(P.chestz - 0.2) - 0.01, P.chestz - 0.2))], [0.014, 0.016, 0.018], n=4), "root_brown", "chest", smooth=True)


@style("belt", "line")
def belt_line(F, size, word):
    """A sounding-line coiled at its hip, with its weight."""
    P = F.P
    hw, hd, yo = P.ring(P.hipz + 0.1 * P.t)
    c = Vector((hw + 0.05, yo - 0.02, P.hipz + 0.02))
    coil = None
    for k in range(3):
        coil = g.merge(coil, hoop(c + Vector((0.012 * k, 0, 0)), 0.09 * size, 0.11 * size, 0.016, u=Y, v=Z, n=10, sides=3))
    F.add("line_coil", coil, "rope_line", "hips", smooth=True)
    drop = g.tube([c + Vector((0.02, 0, -0.1)), c + Vector((0.03, -0.01, -0.42 * size))], 0.01, n=3)
    lead = g.lathe([(0.0, 0.0), (0.045, -0.03), (0.035, -0.12), (0.0, -0.15)], n=6, centre=c + Vector((0.03, -0.01, -0.42 * size)))
    F.move("sway", "line", [(drop, "rope_line"), (lead, "accent_pale")], c + Vector((0.02, 0, -0.1)), "hips", smooth=False)


# --- what stands behind it ---------------------------------------------------------------------

@style("back", "briars")
def back_briars(F, size, word):
    """Briars grown from its back in arches, each thorn as long as its hand."""
    P = F.P
    by = P.rear(P.chestz) + 0.02
    root = Vector((0, by, P.chestz))
    for sg, tag in ((1, "l"), (-1, "r")):
        stems, thorns, leaves = None, None, None
        for k in range(3):
            reach = (0.75 + 0.3 * k) * size
            rise = (0.95 - 0.28 * k) * size
            pts = []
            for i in range(8):
                t = i / 7
                pts.append(root + Vector((sg * (0.08 + reach * math.sin(t * math.pi * 0.62) * (0.4 + t)), 0.16 * math.sin(t * math.pi) + 0.05 * k, rise * math.sin(t * math.pi * 0.95) * 1.2 - 0.5 * k * t * size - 0.1 * t)))
            stems = g.merge(stems, g.tube(pts, [0.045 - 0.004 * i for i in range(8)], n=5))
            for i in range(1, 8):
                d = (pts[i] - pts[i - 1]).normalized()
                out = d.cross(Y).normalized() * (1 if i % 2 else -1)
                thorns = g.merge(thorns, g.cone(pts[i], pts[i] + out * 0.15 * size + d * 0.03, 0.03, n=4))
                if i % 2 == 0:
                    leaves = g.merge(leaves, g.blade(pts[i], pts[i] - out * 0.2 * size + Vector((0, -0.05, 0)), 0.12 * size, normal=Y, belly=0.45))
        F.move("sway", "briars", [(stems, "root_brown"), (thorns, "bone_thorn"), (leaves, "accent")], root, "chest", side=tag, smooth=False)


@style("back", "disc")
def back_disc(F, size, word):
    """The sun behind it: low (half risen behind its shoulders), high (upright behind its head), sunk (down behind one shoulder)."""
    P = F.P
    hr = P.hr
    r = 0.62 * size
    y = P.rear(P.armz) + 0.2
    if word == "high":
        c = Vector((0, P.hcy + 0.9 * hr, P.crown - 0.5 * P.hh))
        r *= 0.92
    elif word == "sunk":
        c = Vector((-0.55, y + 0.25, F.seat + 0.22))
    else:
        c = Vector((0, y, P.armz - 0.1))
    plate = disc(c, r, normal=Y, thick=0.035, n=20)
    core = disc(c + Vector((0, -0.022, 0)), r * 0.62, normal=Y, thick=0.02, n=16)
    rim = hoop(c + Vector((0, -0.02, 0)), r * 0.94, r * 0.94, 0.03, u=X, v=Z, n=20, sides=3)
    F.add("disc", plate, "accent2", "root" if word == "sunk" else "chest", smooth=False)
    F.add("disc_core", core, "accent2_light", "root" if word == "sunk" else "chest", smooth=False)
    F.add("disc_rim", rim, field("sun", 3.0), "root" if word == "sunk" else "chest", smooth=False)
    rays, alt = None, None
    n = 16
    for i in range(n):
        a = 2 * math.pi * i / n
        if word == "sunk" and math.sin(a) < -0.2:
            continue
        d = Vector((math.cos(a), 0, math.sin(a)))
        ray = g.blade(c + d * r * 1.04, c + d * r * (1.5 if i % 2 == 0 else 1.28), 0.2 * r, normal=Y, belly=0.3, thick=0.012)
        if i % 2:
            alt = g.merge(alt, ray)
        else:
            rays = g.merge(rays, ray)
    F.move("spin", "rays", [(rays, "accent2_light"), (alt, "accent2")], c, "root" if word == "sunk" else "chest", smooth=False, up=(0, 1, 0))


# --- what it stands on, or rises from -----------------------------------------------------------

def _slab(c, r, depth, seed=0, n=9):
    """A piece of ground that has come away: flat above, broken below."""
    c = V(c)
    prof = [(0.0, 0.0), (0.84, 0.0), (1.0, -0.12), (0.9, -0.36), (0.6, -0.68), (0.25, -0.92), (0.0, -1.0)]
    rings = []
    for k, t in prof[1:-1]:
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n + 0.2 * seed
            wob = 1.0 + (0.16 * (rnd(j, seed + t) - 0.5) if t < -0.05 else 0.06 * (rnd(j, seed) - 0.5))
            ring.append(c + Vector((math.cos(a) * r * k * wob, math.sin(a) * r * 0.86 * k * wob, t * depth + (0.05 * depth * (rnd(j, seed + 5) - 0.5) if t < -0.05 else 0))))
        rings.append(ring)
    top = g.loft([[c + Vector((0, 0, 0.0))] * n, rings[0]], caps=False)
    under = g.loft(rings + [[c + Vector((0.04 * r, 0, -depth))] * n], caps=False)
    return top, under


@style("under", "slab")
def under_slab(F, size, word):
    """Its own ground: a slab of stone that has come away and floats under it. tor: with boulders;
    ridge: the top of a ridge; roots: with roots hanging; magma: with the fire showing below."""
    P = F.P
    r = 0.56 * size * (1.0 + 0.6 * (word == "ridge"))
    c = Vector((0, 0.02, F.seat - 0.012))
    top, under = _slab(c, r, 0.62 * size, seed=3 + F.level)
    F.add("slab_top", top, "stone_slab" if word != "roots" else "moss_green", "root", smooth=False)
    F.add("slab_under", under, "stone_basalt" if word != "roots" else "earth_loam", "root", smooth=False)
    F.add("slab_ore", hoop(c + Vector((0, 0, -0.07 * size)), r * 1.0, r * 0.86, 0.03 * size, n=9, sides=3), "accent", "root", smooth=False)
    if word == "tor":
        rocks = None
        for i in range(5):
            a = 0.9 + 1.25 * i
            rocks = g.merge(rocks, lump(c + Vector((math.cos(a) * r * 0.78, math.sin(a) * r * 0.62 + 0.1, 0.1)), (0.13 + 0.09 * rnd(i, 23)) * size, seed=i + 2, sub=0, scale=(1, 1, 1.3)))
        F.add("slab_rocks", rocks, "stone_basalt", "root", smooth=False)
    elif word == "ridge":
        flank = None
        for sg in (1, -1):
            flank = g.merge(flank, shard(c + Vector((sg * r * 0.5, 0, -0.1)), c + Vector((sg * r * 1.5, 0.05, -0.55 * size)), 0.34 * size, n=5, belly=0.2))
        F.add("slab_flank", flank, "stone_slab", "root", smooth=False)
    elif word == "roots":
        roots = None
        for i in range(6):
            a = 2 * math.pi * i / 6 + 0.5
            b0 = c + Vector((math.cos(a) * r * 0.5, math.sin(a) * r * 0.42, -0.4 * size))
            L = (0.5 + 0.4 * rnd(i, 24)) * size
            roots = g.merge(roots, g.tube([b0, b0 + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, -L * 0.5)), b0 + Vector((math.cos(a + 0.6) * 0.16, math.sin(a + 0.6) * 0.16, -L))], [0.05 * size, 0.032 * size, 0.008], n=4))
        F.move("sway", "roots", [(roots, "root_brown")], c + Vector((0, 0, -0.4 * size)), "root", smooth=True)
    elif word == "magma":
        glow = None
        for i in range(5):
            a = 2 * math.pi * i / 5
            glow = g.merge(glow, bolt(c + Vector((math.cos(a) * r * 0.9, math.sin(a) * r * 0.76, -0.14 * size)), c + Vector((math.cos(a + 0.3) * r * 0.3, math.sin(a + 0.3) * r * 0.26, -0.58 * size)), 0.07 * size, seed=i, n=3,
                                       normal=(math.cos(a), math.sin(a), 0.4)))
        F.add("slab_magma", glow, field("seam", 2.6), "root", smooth=False)


@style("under", "cone")
def under_cone(F, size, word):
    """It stands waist-deep in its own mountain, and the fire runs down it."""
    P = F.P
    z0 = P.hipz + 0.05
    c = Vector((0, 0.03, 0))
    prof = [(0.3 * P.t, z0), (0.42, z0 - 0.3), (0.62, P.kneez - 0.1), (0.95 * size, 0.1), (1.25 * size, -0.42), (0.8 * size, -0.62), (0.0, -0.7)]
    rock = g.lathe(prof, n=9, centre=c, phase=0.2)
    rock = ([p + Vector((0.05 * math.sin(p.z * 8.0 + p.x * 5.0), 0.05 * math.cos(p.z * 6.0 + p.y * 4.0), 0)) for p in rock[0]], rock[1])
    F.add("cone", rock, "slag_dark", "root", smooth=False)
    lava, hot = None, None
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.7
        pts = []
        for j in range(5):
            t = j / 4
            rad = 0.32 * P.t + (1.22 * size - 0.32 * P.t) * t ** 1.5 + 0.03
            z = z0 - (z0 + 0.38) * t
            aa = a + 0.22 * math.sin(t * 5.0 + i)
            pts.append(c + Vector((math.cos(aa) * rad, math.sin(aa) * rad, z)))
        strip = ribbon(pts, [0.2, 0.22, 0.26, 0.24, 0.1], normal=(math.cos(a), math.sin(a), 0.5), thick=0.2)
        lava = g.merge(lava, strip)
        hot = g.merge(hot, g.tube([p + Vector((math.cos(a), math.sin(a), 0.4)) * 0.02 for p in pts[:3]], [0.035, 0.03, 0.02], n=3))
    F.add("cone_lava", lava, "accent", "root", smooth=True)
    F.add("cone_hot", hot, field("lava", 2.8), "root", smooth=False)


@style("under", "wave")
def under_wave(F, size, word):
    """Below the knee it is a wave that never breaks (deep: of dark water)."""
    P = F.P
    zk = P.kneez + 0.05
    c = Vector((0, 0.03, 0))
    body_m, crest_m = ("water_deep", "accent_dark") if word == "deep" else ("accent_dark", "accent")
    prof = [(0.12, zk + 0.04), (0.22, zk - 0.18), (0.36 * size, zk * 0.45), (0.6 * size, 0.06), (0.7 * size, -0.2), (0.5 * size, -0.42), (0.0, -0.55)]
    F.add("wave_body", g.lathe(prof, n=12, centre=c, caps=False), body_m, "root", smooth=True)
    curl, foam = None, None
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.4
        pts = []
        for j in range(6):
            t = j / 5
            aa = a + t * 1.9
            rad = (0.72 - 0.16 * t) * size
            pts.append(c + Vector((math.cos(aa) * rad, math.sin(aa) * rad, -0.22 + (zk * 0.72 + 0.2) * t ** 0.8)))
        tip = pts[-1] + Vector((math.cos(a + 2.4) * 0.14, math.sin(a + 2.4) * 0.14, -0.1)) * size
        curl = g.merge(curl, ribbon(pts + [tip], [0.3 * size, 0.38 * size, 0.36 * size, 0.3 * size, 0.24 * size, 0.16 * size, 0.03], normal=(math.cos(a + 1.0), math.sin(a + 1.0), 0.3), thick=0.3))
        foam = g.merge(foam, g.ico(tip, 0.07 * size, sub=0), g.ico(pts[-1] + Vector((0, 0, 0.05)), 0.055 * size, sub=0))
    F.move("spin", "wave", [(curl, crest_m), (foam, "water_foam")], c, "root", smooth=True)


@style("under", "surge")
def under_surge(F, size, word):
    """The whole sea making up its mind: a wave taller than itself that leans forward over it and does not fall."""
    P = F.P
    z0 = P.hipz + 0.14 * P.t
    c = Vector((0, 0.05, 0))
    mound = g.lathe([(0.2 * P.t, z0 + 0.03), (0.34, z0 - 0.2), (0.62 * size, P.kneez), (0.95 * size, 0.2), (1.1 * size, -0.2), (0.7 * size, -0.5), (0.0, -0.6)], n=12, centre=c, caps=False)
    F.add("surge_mound", mound, "accent_dark", "root", smooth=True)
    top = P.crown + 0.95 * size
    spine = [Vector((0, 0.5 * size, -0.3)), Vector((0, 0.95 * size, P.kneez)), Vector((0, 1.05 * size, P.chestz)), Vector((0, 0.8 * size, P.crown + 0.3)), Vector((0, 0.25 * size, top)), Vector((0, -0.4 * size, top - 0.12 * size)),
             Vector((0, -0.72 * size, top - 0.5 * size))]
    widths = [2.0 * size, 2.3 * size, 2.3 * size, 2.1 * size, 1.8 * size, 1.3 * size, 0.2 * size]
    wave = ribbon(spine, widths, normal=(0, 1, 0), thick=0.24)
    inner = ribbon([p + Vector((0, -0.03, -0.02)) for p in spine[1:6]], [w * 0.6 for w in widths[1:6]], normal=(0, 1, 0), thick=0.2)
    foam = None
    for i in range(9):
        t = -1.0 + 2.0 * i / 8
        p = spine[-2] + Vector((t * widths[-2] * 0.48, -0.22 * size * (1 - t * t), -0.1 * size - 0.2 * size * (1 - t * t)))
        foam = g.merge(foam, g.ico(p, (0.1 + 0.05 * rnd(i, 25)) * size, sub=0))
    F.move("sway", "surge", [(wave, "accent"), (inner, "accent_light"), (foam, "water_foam")], (0, 0.9 * size, P.kneez), "root", smooth=True)


@style("under", "boat")
def under_boat(F, size, word):
    """A boat that is only a curl of water, and a lantern at its bow."""
    P = F.P
    L = 1.25 * size
    hull = ribbon([(0, 0.62 * L, 0.34), (0, 0.42 * L, 0.02), (0, 0.0, -0.1), (0, -0.55 * L, -0.02), (0, -0.92 * L, 0.3), (0, -1.02 * L, 0.62)], [0.1, 0.6 * size, 0.82 * size, 0.62 * size, 0.3 * size, 0.04], normal=(0, 0, -1), thick=0.42)
    keel = ribbon([(0, 0.4 * L, -0.04), (0, 0.0, -0.3), (0, -0.6 * L, -0.12)], [0.3 * size, 0.56 * size, 0.2 * size], normal=(0, 0, -1), thick=0.5)
    F.add("boat", hull, "accent_dark", "root", smooth=True)
    F.add("boat_keel", keel, "water_deep", "root", smooth=True)
    rim = g.tube([(0.36 * size, 0.3 * L, 0.06), (0.43 * size, 0, 0.0), (0.32 * size, -0.5 * L, 0.06), (0.1 * size, -0.9 * L, 0.3)], 0.03, n=4)
    F.add("boat_rim", g.merge(rim, g.mirrored(rim)), "water_foam", "root", smooth=True)
    c = Vector((0, -1.02 * L, 0.84))
    lamp = [(g.ico(c, 0.085 * size, sub=1, scale=(1, 1, 1.25)), field("lamp", 3.6)), (hoop(c + Vector((0, 0, -0.1 * size)), 0.07 * size, 0.07 * size, 0.014, n=6, sides=3), "accent_pale"),
            (g.cone(c + Vector((0, 0, 0.1 * size)), c + Vector((0, 0, 0.2 * size)), 0.075 * size, n=6), "accent_pale"), (g.tube([c + Vector((0, 0, -0.1 * size)), (0, -1.02 * L, 0.6)], 0.014, n=3), "accent_pale")]
    F.move("sway", "lantern", lamp, (0, -1.02 * L, 0.62), "root", smooth=False)


@style("under", "floe")
def under_floe(F, size, word):
    """A raft of ice."""
    c = Vector((0, 0.02, F.seat - 0.012))
    r = 0.8 * size
    top = [c + Vector((math.cos(2 * math.pi * j / 7 + 0.3) * r * (1.0 + 0.16 * (rnd(j, 26) - 0.5)), math.sin(2 * math.pi * j / 7 + 0.3) * r * 0.82, 0)) for j in range(7)]
    low = [p + Vector((0, 0, -0.16 * size)) + (p - c) * 0.07 for p in top]
    deep = [c + (p - c) * 0.55 + Vector((0, 0, -0.42 * size)) for p in top]
    F.add("floe_top", g.loft([[c] * 7, top], caps=False), "ice_white", "root", smooth=False)
    F.add("floe_side", g.loft([top, low], caps=False), "ice_clear", "root", smooth=False)
    F.add("floe_under", g.loft([low, deep, [c + Vector((0, 0, -0.52 * size))] * 7], caps=False), "ice_blue", "root", smooth=False)
    F.add("floe_line", hoop(c + Vector((0, 0, -0.17 * size)), r * 1.07, r * 0.88, 0.022 * size, n=7, sides=3), "accent", "root", smooth=False)
    sh = None
    for i in range(3):
        a = 2.2 + 1.1 * i
        b0 = c + Vector((math.cos(a) * r * 0.72, math.sin(a) * r * 0.6, 0))
        sh = g.merge(sh, shard(b0, b0 + Vector((math.cos(a) * 0.12, math.sin(a) * 0.1, (0.3 + 0.24 * rnd(i, 27)) * size)), 0.09 * size, n=4))
    F.add("floe_shards", sh, "ice_clear", "root", smooth=False)


@style("under", "berg")
def under_berg(F, size, word):
    """The tenth part shows: it sits on the tip of a great block that hangs under it, with a cold light deep inside."""
    c = Vector((0, 0.05, F.seat - 0.012))
    n = 7

    def ring(k, z, seed):
        return [c + Vector((math.cos(2 * math.pi * j / n + 0.4) * k * (1.0 + 0.2 * (rnd(j, seed) - 0.5)), math.sin(2 * math.pi * j / n + 0.4) * k * 0.84 * (1.0 + 0.2 * (rnd(j, seed + 1) - 0.5)), z)) for j in range(n)]
    tip = ring(0.5 * size, 0.0, 30)
    line = ring(0.72 * size, -0.42 * size, 31)
    belly = ring(1.28 * size, -1.5 * size, 32)
    low = ring(0.82 * size, -2.6 * size, 33)
    F.add("berg_tip", g.loft([[c] * n, tip, line], caps=False), "ice_white", "root", smooth=False)
    F.add("berg_belly", g.loft([line, belly], caps=False), "ice_clear", "root", smooth=False)
    F.add("berg_low", g.loft([belly, low, [c + Vector((0.1, 0, -3.3 * size))] * n], caps=False), "ice_blue", "root", smooth=False)
    F.add("berg_line", hoop(c + Vector((0, 0, -0.42 * size)), 0.78 * size, 0.66 * size, 0.03 * size, n=n, sides=3), "accent", "root", smooth=False)
    core = g.merge(bolt(c + Vector((0.1, -1.0 * size, -0.9 * size)), c + Vector((-0.12, -0.92 * size, -2.3 * size)), 0.16 * size, seed=4, n=4), bolt(c + Vector((0.72 * size, -0.62 * size, -1.3 * size)), c + Vector((0.5 * size, -0.6 * size, -2.2 * size)), 0.1 * size, seed=5, n=3, normal=(0.6, -0.8, 0)))
    F.move("pulse", "core", [(core, field("cold", 2.6))], c + Vector((0, -0.9 * size, -1.6 * size)), "root", smooth=False)


@style("under", "cloud")
def under_cloud(F, size, word):
    """A cloud under its feet. storm: dark, with a stroke under it; bank: a long bank of it."""
    c = Vector((0, 0.05, F.seat - 0.2 * size))
    if word == "bank":
        geo = g.merge(cloud(c, 0.5 * size, n=5, seed=40), cloud(c + Vector((0.62 * size, 0.1, -0.05)), 0.42 * size, n=4, seed=41), cloud(c + Vector((-0.66 * size, 0.06, -0.03)), 0.44 * size, n=4, seed=42))
        F.move("pulse", "cloud", [(geo, "mist_cloud"), (cloud(c + Vector((0.1, 0.02, -0.14 * size)), 0.52 * size, n=4, seed=43, sub=0), "accent_pale")], c, "root", smooth=True)
        return
    geo = cloud(c, 0.56 * size, n=6, seed=44 + F.level)
    items = [(geo, "mist_storm" if word == "storm" else "mist_cloud"), (cloud(c + Vector((0.05, 0.02, -0.12 * size)), 0.4 * size, n=4, seed=45, sub=0), "accent_dark" if word == "storm" else "accent_pale")]
    if word == "storm":
        items.append((bolt(c + Vector((0.1, -0.16, -0.2 * size)), c + Vector((-0.12, -0.2, -0.95 * size)), 0.12 * size, seed=7), field("bolt", 3.6)))
    F.move("pulse", "cloud", items, c, "root", smooth=True)


# --- what it holds ------------------------------------------------------------------------------

@style("right", "hammer")
def hold_hammer(F, size, word):
    """A hammer as long as itself, over its right shoulder."""
    P = F.P
    grip = Vector((-P.sx * 0.72, P.front(P.chestz) - 0.2, P.armz - 0.12 * P.t))
    sh = Vector((-P.sx * 0.86, P.army + 0.02, P.armz + 0.14 * P.t))
    d = (sh - grip).normalized()
    end = grip - d * 0.3
    head = sh + d * 1.05 * size
    F.add("hammer_haft", g.tube([end, head], 0.04, n=6), "wood_haft", "chest", smooth=False)
    u, v = g._frame(d)
    R = kit.rot_axes(u, v, d)
    F.add("hammer_head", g.box(head, (0.5 * size, 0.26 * size, 0.26 * size), rot=R), "iron_head", "chest", smooth=False)
    F.add("hammer_band", hoop(head - d * 0.16 * size, 0.06, 0.06, 0.02, u=u, v=v, n=6, sides=3), "brass_band", "chest", smooth=False)
    for sg in (1, -1):
        F.add("hammer_face_%d" % sg, g.box(head + u * sg * 0.25 * size, (0.03, 0.2 * size, 0.2 * size), rot=R), field("seam", 2.4), "chest", smooth=False)


@style("right", "sickle")
def hold_sickle(F, size, word):
    """A sickle, in the hand that is held out (it rides the forearm)."""
    P = F.P
    # made in the rest pose at the right fist: the haft down the hand's own forward, the blade hooking up
    slot = P.J["handslot.r"]
    c = Vector(slot)
    F.add("sickle_haft", g.tube([c + Vector((0, 0.1, 0)), c + Vector((0, -0.2 * size, 0))], 0.03, n=5), "wood_haft", "hand.r", smooth=False)
    pts = [c + Vector((0, -0.2 * size, 0)) + Vector((0.34 * size * math.sin(t) * -1, -0.3 * size * (1 - math.cos(t)), 0.0)) for t in [0.0, 0.5, 1.0, 1.6, 2.2, 2.7]]
    F.add("sickle_blade", ribbon(pts, [0.05, 0.1 * size, 0.12 * size, 0.11 * size, 0.08 * size, 0.01], normal=Z, thick=0.12), "steel_edge", "hand.r", smooth=False)


@style("left", "sheaf")
def hold_sheaf(F, size, word):
    """A sheaf in the crook of its arm."""
    P = F.P
    c = Vector((P.sx * 0.5, P.front(P.chestz, P.sx * 0.4) - 0.14, P.chestz - 0.12 * P.t))
    d = Vector((0.32, -0.1, 1.0)).normalized()
    stalks, ears = None, None
    for i in range(9):
        a = 2 * math.pi * i / 9
        o = Vector((math.cos(a), math.sin(a), 0)) * 0.07 * size
        top = c + d * 0.62 * size + o * 2.6
        stalks = g.merge(stalks, g.tube([c - d * 0.36 * size + o * 1.2, c + o * 0.6, top], [0.03, 0.026, 0.02], n=3))
        ears = g.merge(ears, g.ico(top + d * 0.08, 0.06 * size, sub=0, scale=(0.8, 0.8, 1.9)))
    F.add("sheaf", stalks, "straw_wheat", "chest", smooth=True)
    F.add("sheaf_ears", ears, "accent_light", "chest", smooth=False)
    u, v = g._frame(d)
    F.add("sheaf_tie", hoop(c, 0.1 * size, 0.1 * size, 0.022, u=u, v=v, n=8, sides=3), "accent_dark", "chest", smooth=False)


@style("both", "pole")
def hold_pole(F, size, word):
    """A long pole, set down over the side."""
    a, b = F.pole
    F.add("pole", g.tube([a, b], [0.03, 0.036], n=5), "wood_haft", "chest", smooth=False)
    F.add("pole_tip", g.tube([b, b + (b - a).normalized() * 0.1], [0.045, 0.02], n=5), "accent_pale", "chest", smooth=False)


@style("both", "anchor")
def hold_anchor(F, size, word):
    """An anchor carried across its shoulders, and a chain from one arm of it."""
    P = F.P
    y, z = P.rear(P.armz) + 0.07, P.armz + 0.1 * P.t
    w = P.sx + 0.5
    iron = g.tube([(-w, y, z), (w * 1.05, y, z)], 0.042, n=6)
    iron = g.merge(iron, hoop((-w - 0.09, y, z), 0.09, 0.09, 0.025, u=X, v=Z, n=8, sides=4))
    arms = None
    for sg in (1, -1):
        pts = [Vector((w * 1.05, y, z)), Vector((w * 1.2, y, z + sg * 0.26 * size)), Vector((w * 0.98, y, z + sg * 0.5 * size)), Vector((w * 0.74, y, z + sg * 0.55 * size))]
        arms = g.merge(arms, g.tube(pts, [0.045, 0.04, 0.036, 0.02], n=5))
        arms = g.merge(arms, g.blade(pts[-1] + Vector((0.06, 0, 0)), pts[-1] + Vector((-0.2 * size, 0, sg * 0.04)), 0.2 * size, normal=Y, belly=0.4, thick=0.02))
    F.add("anchor", g.merge(iron, arms), "iron_head", "chest", smooth=False)
    F.add("anchor_stock", g.tube([(-w * 0.7, y - 0.3 * size, z), (-w * 0.7, y + 0.3 * size, z)], 0.035, n=5), "accent", "chest", smooth=False)
    links = None
    for i in range(7):
        c = Vector((-w - 0.09, y, z - 0.13 - 0.13 * i))
        links = g.merge(links, hoop(c, 0.05, 0.075, 0.016, u=(X if i % 2 else Y), v=Z, n=6, sides=3))
    F.move("sway", "chain", [(links, "iron_head"), (g.ico((-w - 0.09, y, z - 0.13 * 8.2), 0.075, sub=0), field("find", 2.6))], (-w - 0.09, y, z - 0.08), "chest", smooth=False)


@style("both", "sail")
def hold_sail(F, size, word):
    """A small full sail on a yard across its shoulders."""
    P = F.P
    y, z = P.rear(P.armz) + 0.07, P.armz + 0.1 * P.t
    w = P.sx + 0.52
    F.add("yard", g.tube([(-w, y, z), (w, y, z)], 0.035, n=5), "wood_haft", "chest", smooth=False)
    mast_top = z + 1.55 * size
    F.add("mast", g.tube([(0, y + 0.03, z - 0.05), (0, y + 0.03, mast_top)], [0.04, 0.028], n=5), "wood_haft", "chest", smooth=False)
    F.add("top_yard", g.tube([(-w * 0.8, y + 0.02, mast_top - 0.06), (w * 0.8, y + 0.02, mast_top - 0.06)], 0.028, n=5), "wood_haft", "chest", smooth=False)
    rows = []
    for i in range(5):
        t = i / 4
        zz = z + 0.03 + (mast_top - 0.09 - z) * t
        ww = w * (1.0 - 0.2 * t)
        belly = -0.5 * size * math.sin(t * math.pi) - 0.02
        rows.append([Vector((-ww, y, zz)), Vector((-ww * 0.5, y + belly * 0.8, zz)), Vector((0, y + belly, zz)), Vector((ww * 0.5, y + belly * 0.8, zz)), Vector((ww, y, zz))])
    sail = g.loft(rows, caps=False, closed=False)
    stripe = g.loft([[p + Vector((0, -0.012, 0)) for p in rows[1][1:4]], [p + Vector((0, -0.012, 0)) for p in rows[2][1:4]], [p + Vector((0, -0.012, 0)) for p in rows[3][1:4]]], caps=False, closed=False)
    F.move("pulse", "sail", [(sail, "cloth_sail"), (stripe, "accent")], (0, y, z + 0.7 * size), "chest", smooth=True)


@style("right", "bolt")
def hold_bolt(F, size, word):
    """A forked stroke of lightning, held like a spear (it rides the hand that throws it)."""
    P = F.P
    c = Vector(P.J["handslot.r"])
    a, b = c + Vector((0, 0.95 * size, 0.0)), c + Vector((0, -1.3 * size, 0.0))
    main = bolt(a, b, 0.2 * size, seed=11, n=5, normal=Z)
    fork = bolt(c + Vector((0, -0.5 * size, 0)), c + Vector((0.42 * size, -1.05 * size, 0)), 0.11 * size, seed=12, n=3, normal=Z)
    F.move("flick", "bolt", [(g.merge(main, fork), field("bolt", 4.0)), (g.tube([c + Vector((0, 0.12, 0)), c + Vector((0, -0.12, 0))], 0.045, n=5), "accent_pale")], c, "hand.r", smooth=False, up=(0, -1, 0))


# --- what keeps it company ------------------------------------------------------------------------

def _axis(F):
    P = F.P
    return Vector((0, P.J["chest"].y, P.chestz))


@style("around", "cloudlet")
def around_cloudlet(F, size, word):
    """A wisp of cloud that keeps to its shoulder, and rains now and then."""
    P = F.P
    c = Vector((P.sx + 0.42, P.army - 0.05, P.crown + 0.05))
    drops = None
    for i in range(4):
        p = c + Vector(((i - 1.5) * 0.11, 0.03 * (i % 2), -0.3 - 0.11 * (i % 3)))
        drops = g.merge(drops, g.blade(p + Vector((0, 0, 0.1)), p, 0.05, normal=Y, belly=0.75))
    F.move("bob", "cloudlet", [(cloud(c, 0.3 * size, n=5, seed=50), "mist_cloud"), (drops, field("rain", 2.6))], c, "chest", smooth=True)


@style("around", "stones", "embers", "sparks", "fish", "bubbles")
def around_ring(F, size, word):
    """What goes round it: stones that keep their distance; embers; sparks; small pale fish; bubbles rising."""
    P = F.P
    st = F._style
    c = _axis(F)
    if st == "bubbles":
        geo = None
        for i in range(7):
            a = 2.4 * i
            p = c + Vector((math.cos(a) * (0.5 + 0.3 * rnd(i, 60)), math.sin(a) * 0.4, -0.5 + 1.5 * rnd(i, 61)))
            geo = g.merge(geo, g.ico(p, 0.035 + 0.035 * rnd(i, 62), sub=1))
        F.move("bob", "bubbles", [(geo, "accent_pale")], c, "root", smooth=True)
        return
    n = {"stones": 5, "embers": 7, "sparks": 5, "fish": 6}[st]
    rad = {"stones": 1.0, "embers": 0.95, "sparks": 0.8, "fish": 0.9}[st] * size
    geo, alt = None, None
    for i in range(n):
        a = 2 * math.pi * i / n
        p = c + Vector((math.cos(a) * rad, math.sin(a) * rad, 0.3 * math.sin(a * 2 + i)))
        if st == "stones":
            one = lump(p, 0.1 + 0.07 * rnd(i, 63), seed=i + 4, sub=0, scale=(1, 0.8, 1.3))
        elif st == "embers":
            one = g.ico(p + Vector((0, 0, 0.5 * rnd(i, 64) - 0.1)), 0.035 + 0.03 * rnd(i, 65), sub=0)
        elif st == "sparks":
            t = Vector((-math.sin(a), math.cos(a), 0))
            one = bolt(p - t * 0.14, p + t * 0.14 + Vector((0, 0, 0.1)), 0.07, seed=i, n=3, normal=(math.cos(a), math.sin(a), 0))
        else:
            t = Vector((-math.sin(a), math.cos(a), 0))
            one = g.merge(g.ico(p, 0.06, sub=0, scale=(1, 1, 0.7), rot=(0, 0, a + math.pi / 2)), g.blade(p - t * 0.05, p - t * 0.16, 0.09, normal=(math.cos(a), math.sin(a), 0), belly=0.8))
            one = (list(one[0]), list(one[1]))
        if i % 2 and st in ("stones", "fish"):
            alt = g.merge(alt, one)
        else:
            geo = g.merge(geo, one)
    made = {"stones": ("stone_basalt", "accent"), "embers": (field("ember", 3.0), None), "sparks": (field("sparks", 3.4), None), "fish": ("bone_shell", "accent_pale")}[st]
    F.move("spin", st, [(geo, made[0])] + ([(alt, made[1])] if alt else []), c, "root", smooth=False)


@style("around", "streams")
def around_streams(F, size, word):
    """Two thin streams off its shoulders, one each way."""
    P = F.P
    for sg, tag in ((1, "l"), (-1, "r")):
        b0 = Vector((sg * (P.sx + 0.02), P.army, P.armz + 0.09 * P.t))
        pts = [b0, b0 + Vector((sg * 0.3, 0.02, -0.03)) * size, b0 + Vector((sg * 0.6, 0.04, -0.4)) * size, b0 + Vector((sg * 0.74, 0.06, -1.0)) * size, Vector((sg * (P.sx + 0.8 * size), P.army + 0.06, F.seat - 0.3))]
        water = ribbon(pts, [0.09, 0.11, 0.1, 0.085, 0.05], normal=(0, -1, 0.2), thick=0.6)
        F.move("sway", "stream", [(water, "water_foam"), (g.ico(pts[-1], 0.08, sub=0), "ice_white")], b0, "chest", side=tag, smooth=True)


@style("around", "breath")
def around_breath(F, size, word):
    """Its breath, going out ahead of it, white."""
    P = F.P
    z = float(P.mouth[2]) - 0.07 * P.hr
    c = Vector((0, P.front(z) - 0.03, z))
    geo, snow = None, None
    for i in range(5):
        a = 2 * math.pi * i / 5
        o = Vector((math.cos(a), 0, math.sin(a)))
        pts = [c + o * 0.02, c + Vector((0, -0.5 * size, 0)) + o * 0.16 * size, c + Vector((0, -1.15 * size, 0)) + o * 0.34 * size, c + Vector((0, -1.7 * size, 0)) + o * 0.42 * size]
        geo = g.merge(geo, ribbon(pts, [0.05, 0.2 * size, 0.26 * size, 0.04], normal=o, thick=0.3))
        snow = g.merge(snow, g.ico(pts[-1] + Vector((0, -0.1, 0)), 0.045, sub=0), g.ico(pts[-2] + o * 0.1, 0.035, sub=0))
    F.move("pulse", "breath", [(geo, "mist_white"), (snow, "ice_white")], c, "head", smooth=True)


# ======================================================================================
# A form that is no longer a person: the Tempest
# ======================================================================================

def storm(form_id, level, spec):
    """The whole storm: a turning cloud lit from inside, with a calm face high up in it where the
    eye would be. No rig: its bands turn, each its own way (spin_), and its eyes shut now and then."""
    import genius_lines as gl
    kit.reset()
    hgt = 0.62
    objs = []
    # the funnel: bands of cloud, wider as they rise, each turning against the next
    for k in range(4):
        z = 0.1 + 0.115 * k
        rad = 0.07 + 0.052 * k
        dark = k % 2 == 0
        geo, veil = None, None
        for i in range(5 + k):
            a = 2 * math.pi * i / (5 + k) + 0.5 * k
            p = Vector((math.cos(a) * rad, math.sin(a) * rad, z + 0.02 * math.sin(i * 2.0)))
            geo = g.merge(geo, g.ico(p, 0.052 + 0.012 * k, sub=1, scale=(1.3, 1.0, 0.72), rot=(0, 0, a + math.pi / 2)))
            if i % 2 == 0:
                veil = g.merge(veil, g.blade(p, p + Vector((-math.sin(a), math.cos(a), 0.1)) * (0.13 + 0.02 * k), 0.06, normal=(math.cos(a), math.sin(a), 0.3), belly=0.3))
        objs.append(gl.moving("spin", "band", [(geo, mat("mist_storm" if dark else "accent_dark")), (veil, mat("accent_light" if dark else "mist_cloud"))], (0, 0, z), side="r" if k % 2 else "", n=k))
    tail = g.tube([(0, 0, 0.11), (0.02, 0.01, 0.05), (-0.01, 0.0, 0.0), (0.015, 0, -0.05)], [0.05, 0.034, 0.02, 0.004], n=7)
    objs.append(gl.moving("wag", "tail", [(tail, mat("mist_storm"))], (0, 0, 0.11)))
    # the head of the storm: an anvil of cloud, and the light inside it
    c = Vector((0, 0, 0.56))
    top = g.merge(cloud(c, 0.2, n=7, seed=70), cloud(c + Vector((0, 0.02, 0.07)), 0.24, n=6, seed=71, flat=0.5), g.ico(c + Vector((0, 0.02, 0.12)), 0.33, sub=1, scale=(1.0, 0.75, 0.18)))
    under = cloud(c + Vector((0, 0, -0.07)), 0.19, n=6, seed=72)
    objs.append(gl.moving("pulse", "crown", [(top, mat("mist_cloud")), (under, mat("mist_storm"))], c))
    inner = g.merge(bolt((0.08, -0.13, 0.5), (0.02, -0.15, 0.2), 0.035, seed=1, n=4), bolt((-0.14, -0.1, 0.47), (-0.08, -0.13, 0.27), 0.026, seed=2, n=3), bolt((0.17, 0.02, 0.44), (0.12, -0.02, 0.24), 0.026, seed=3, n=3, normal=(1, 0.3, 0)))
    objs.append(gl.moving("flick", "light", [(inner, field("bolt", 3.6))], (0, -0.1, 0.2), smooth=False))
    # the face it keeps for your sake: calm, in the eye of it
    f = Vector((0, -0.17, 0.53))
    fr = 0.085
    face_geo = g.ico(f, fr, sub=2, scale=(0.86, 0.5, 1.12))
    nose = g.blade(f + Vector((0, -fr * 0.46, fr * 0.2)), f + Vector((0, -fr * 0.62, -fr * 0.3)), fr * 0.3, normal=(1, 0, 0), belly=0.7, thick=fr * 0.2)
    brows, mouth = None, None
    for sg in (1, -1):
        brows = g.merge(brows, g.tube([f + Vector((sg * fr * 0.1, -fr * 0.5, fr * 0.44)), f + Vector((sg * fr * 0.4, -fr * 0.46, fr * 0.52)), f + Vector((sg * fr * 0.7, -fr * 0.3, fr * 0.42))], [fr * 0.07, fr * 0.07, fr * 0.03], n=4))
    mouth = g.tube([f + Vector((-fr * 0.28, -fr * 0.44, -fr * 0.56)), f + Vector((0, -fr * 0.5, -fr * 0.6)), f + Vector((fr * 0.28, -fr * 0.44, -fr * 0.56))], [fr * 0.02, fr * 0.05, fr * 0.02], n=4, flat=0.6)
    face_ob = g.pieces("face", [(face_geo, mat("stone_flesh")), (nose, mat("stone_flesh")), (brows, mat("stone_band")), (mouth, mat("stone_band")),
                                (hoop(f + Vector((0, 0.01, 0)), fr * 0.95, fr * 1.2, fr * 0.14, u=X, v=Z, n=12, sides=4), mat("accent"))], smooth=True)
    objs.append(face_ob)
    for sg, tag in ((1, "l"), (-1, "r")):
        e = f + Vector((sg * fr * 0.38, -fr * 0.42, fr * 0.2))
        objs.append(gl.moving("blink", "eye", [(g.ico(e, fr * 0.2, sub=1, scale=(1.2, 0.6, 0.9)), mat("eye_white")), (g.ico(e + Vector((0, -fr * 0.08, 0)), fr * 0.12, sub=1, scale=(1, 0.6, 1)), field("eyes", 3.8))], e, side=tag))
    # what turns round it: rain, and leaves it has picked up
    rain, bits = None, None
    for i in range(8):
        a = 2 * math.pi * i / 8
        p = Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.16 + 0.2 * rnd(i, 73)))
        rain = g.merge(rain, g.blade(p + Vector((0.02, 0, 0.07)), p, 0.02, normal=(math.cos(a), math.sin(a), 0), belly=0.7))
        if i % 2:
            bits = g.merge(bits, g.blade(p + Vector((0, 0, 0.12)), p + Vector((-math.sin(a) * 0.06, math.cos(a) * 0.06, 0.15)), 0.04, normal=(math.cos(a), math.sin(a), 0.2), belly=0.5))
    objs.append(gl.moving("spin", "rain", [(rain, mat("accent_pale")), (bits, mat("accent"))], (0, 0, 0.25)))
    socks = kit._sockets({
        "socket_head": [tuple(c + Z * 0.14)], "socket_eyes": [tuple(f + Vector((0, -0.05, 0.02)))], "socket_mouth": [tuple(f + Vector((0, -0.05, -0.05)))], "socket_grip": [(0.2, 0, 0.3)],
        "socket_throat": [(0, -0.12, 0.42)], "socket_light": [(0, -0.2, 0.3)], "socket_back": [(0, 0.2, 0.4)], "socket_body": [(0, -0.2, 0.3)], "socket_tail": [(0, 0.05, 0.02)],
        "socket_arm_l": [(0.22, 0, 0.36)], "socket_arm_r": [(-0.22, 0, 0.36)], "socket_limb_fl": [(0.08, -0.05, 0.05)], "socket_limb_fr": [(-0.08, -0.05, 0.05)],
    })
    gl.export_objects(objs, socks, os.path.join(OUT, form_id + ".glb"), ref=hgt)


# ======================================================================================
# The line
# ======================================================================================

def figure(form_id, level, spec):
    F = Fig(form_id, level, spec)
    for slot in ORDER:
        entries = each(spec.get(slot))
        if slot == "eyes" and not entries:
            entries = [("lit", 1.0, None)]
        for st, size, word in entries:
            fn = STYLES.get(slot, {}).get(st)
            if fn is None:
                log("!! %s: no %s called %s" % (form_id, slot, st))
                continue
            F._style, F._slot = st, slot
            fn(F, size, word)
        if slot == "face":
            face(F)
    return F


def _pole_of(P):
    """Where the ferry's pole lies: from above its left shoulder down over the right side."""
    return Vector((P.sx * 0.9, P.front(P.chestz) - 0.34, P.crown + 0.5)), Vector((-P.sx * 2.2, P.front(P.hipz) - 0.3, -0.75))


def build(form_id, level, spec, base):
    """One form: a small god, unless its body says it has another shape now."""
    PALETTE.update(OWN)
    try:
        if spec.get("shape") == "storm":
            storm(form_id, level, spec)
            return
        kit.reset()
        F = figure(form_id, level, spec)
        F.finish(os.path.join(OUT, form_id + ".glb"))
        if level == 1:      # and the base's own body: the same figure, with the Idle every form borrows
            kit.reset()
            figure(form_id, level, spec).finish(os.path.join(BODIES, SIL + ".glb"), clip=True)
    except Exception:
        if not os.environ.get("WILDLINE_KEEP_GOING"):
            raise
        import traceback
        log("!! %s failed" % form_id)
        traceback.print_exc()


def register(builders):
    builders["elemental"] = build
