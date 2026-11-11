"""WILDLINE genius lines, the Angel (docs/genius-lines.md, "The Angel").

The soul of one who answers to something larger than themselves: the picture of conscience.
A small person on the small people's kit (lines_people.py), with what that kit has not got:
wings of feather (and of steel, paper, blades and light) that are its outline and change at
every stage, a halo of the field's light (the one thing of it that is its partner's), a face
with eyes that blink, and a robe that is its partner's coat. Four of its Finals are no
longer people: two hands, a horn, a pair of scales, a wheel of eyes.

    python tools/blender/genius_lines.py angel
    python tools/blender/genius_lines.py angel angel-scruple angel-clarion
    python tools/blender/lines_angel.py body          # game/assets/genius/bodies/kith-angel.glb (the clips its forms move by)
    python tools/blender/lines_angel.py gifts         # game/assets/genius/gifts/angel-halo.glb, angel-wings.glb

What a `body` may say, here (a slot holds a style, [style, size], or a list of them):

    build   the small people's: age, head, legs, arms, wide, belly, bow, shoulders, neck,
            arm_girth...; and small (how tall it stands against its stage: 0.74)
    hair    down, cropped, swept, curls, bound, long, bare
    eyes    open, wide, lowered, shut, light      brows   level, raised, stern, soft
    mouth   closed, small, open, line             face    blindfold, band-up, light, lamp
    halo    slipped, ring, tilted, plate, rayed, coin, hung
    wings   pairs, the upper first: [pose, size, make]; makes: down, feather, steel, blades,
            paper, light, eyed; the poses are POSES, below
    marks   where its Path's colour lies on the wings, and which step of it:
            [coverts | tips | bars | edge, accent | accent_light | accent_dark | ...]
    robe    smock, tunic, robe, gown, wound       over    sash, hem, tabard, stole, cowl, collar,
            cord, baldric, case, pauldrons, bracers, gorget
    right, left   buckler, lamp-staff, trumpet, great-horn, scroll, quill, scales, pan,
            sword-down, sword-up                  belt    sword-bound
    bears   arch, yoke                            pose    hand-up
    shape   hands, horn, beam, wheel (a Final that is no longer a person)
    coat    how its partner's coat is worn (a shift of data/genius-looks.json)
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
import style  # noqa: E402
import lines_people as lp  # noqa: E402
from lines_people import Person, each, _hoop, _disc  # noqa: E402
import people_dress as pd  # noqa: E402
import people_things as pt  # noqa: E402

GL = None           # genius_lines, whichever way it was started (set in register)
ROOT = kit.ROOT
OUT = os.path.join(ROOT, "game", "assets", "genius", "forms")
SIL = "kith-angel"
STAND = lp.STAND
rad = math.radians


def log(*a):
    print("[lines_angel]", *a)


def _c(hx):
    """A colour written as it is seen ('#RRGGBB'), as the palette keeps it (linear)."""
    return tuple(style.to_linear(style.rgb(hx)))


# The Angel's own colours. Its body is white and bone and no partner's coat: only its robe
# (cloth_robe, cloth_lining) and its hair (hair_angel) are the roles of data/genius-looks.json.
OWN = {
    "bone_angel": (_c("#E8E0CF"), 0.6, 0.0), "brow_angel": (_c("#4A3B30"), 0.8, 0.0),
    "cloth_robe": (_c("#34406A"), 0.9, 0.0), "cloth_lining": (_c("#E2DDD0"), 0.9, 0.0), "hair_angel": (_c("#A8843C"), 0.7, 0.0),
    "feather_angel": (_c("#EDE6D8"), 0.85, 0.0), "feather_angel_shade": (_c("#BDB5A6"), 0.9, 0.0), "feather_down": (_c("#F2ECDC"), 1.0, 0.0),
    "feather_pin": (_c("#8C8577"), 0.8, 0.0),
    "steel_feather": (_c("#8A8F99"), 0.4, 0.8), "steel_feather_dark": (_c("#5A5F6A"), 0.45, 0.8), "steel_blade": (_c("#B8BEC8"), 0.3, 0.85),
    "paper_angel": (_c("#E8DFC8"), 0.85, 0.0), "brass_horn": (_c("#B8923A"), 0.32, 0.85), "wood_staff": (_c("#5A3D22"), 0.8, 0.0),
    "stone_arch": (_c("#8A8782"), 0.95, 0.0), "stone_arch_dark": (_c("#5E5C59"), 0.95, 0.0), "leather_angel": (_c("#5A3A22"), 0.75, 0.0),
}
PALETTE.update(OWN)

# what is soft is shaded round; what is hard keeps its planes
SOFT = ("bone_angel", "brow", "cloth", "hair", "feather", "maw", "field", "accent", "leather", "paper", "eye")

# how it stands at each stage: a fledgling, a youth, a grown figure, one in its prime (grounded
# proportions: "tiny" is its scale, not its shape)
lp.STAGE["angel"] = [dict(age=0.2, head=1.5, legs=0.74, arms=0.95, limbs=1.12, hands=1.15, feet=1.15), dict(age=0.4, head=1.24, legs=0.96, arms=1.0),
                     dict(age=0.5, head=1.17, legs=1.0, arms=1.0), dict(age=0.56, head=1.1, legs=1.04, arms=1.0)]
lp.FACE["angel"] = {"head-oval": 0.6, "eye-scale": 0.7, "ear-scale": -0.4, "nose-volume": -0.3, "nose-scale-vert": -0.2, "cheek-bones": 0.4, "chin-width": -0.3,
                    "mouth-scale-horiz": -0.2}
lp.SKIN["angel"] = "bone_angel"
# how it may stand otherwise than at ease: [(bone, the way it is to point, in the world, and how far it is then
# turned about itself)], parents first
STANCES = {
    # one hand raised before its shoulder, palm out: stop; or, do not be afraid
    "hand-up": [("upperarm.r", (-0.8, -0.36, -0.48), 0), ("lowerarm.r", (-0.3, -0.34, 0.89), 0), ("hand.r", (-0.16, -0.1, 0.98), 0)],
}
TRIS = [2000, 2300, 2600, 2900]        # how many faces the body keeps, by stage (its wings want the rest)
WING = [0.62, 0.95, 1.08, 1.2]         # how long a wing is, by stage, at the human's own size (2.4 to the crown)


def opt(v, size=1.0):
    """A slot as (style, size, word): a style, [style, size], or [style, size, word]."""
    if v is None or v is False:
        return None, size, None
    if isinstance(v, str):
        return v, size, None
    word = None
    for y in v[1:]:
        if isinstance(y, (int, float)):
            size = float(y)
        else:
            word = y
    return v[0], size, word


def _turn_frame(ob, up):
    """Make a piece's own up point along `up` without moving its shape: what the game spins
    it about, stretches it along, or blinks it shut along."""
    R = Vector((0, 0, 1)).rotation_difference(Vector(up).normalized()).to_matrix().to_4x4()
    M = ob.matrix_world.copy()
    Ri = R.inverted()
    for v in ob.data.vertices:
        v.co = Ri @ v.co
    ob.matrix_world = M @ R
    bpy.context.view_layer.update()


def _roles():
    with open(os.path.join(ROOT, "data", "genius-looks.json")) as f:
        looks = json.load(f)
    return {role: name for name, role in looks["bodies"].get(SIL, {}).get("roles", {}).items()}


# ======================================================================================
# The body: a small person with pieces the game moves
# ======================================================================================

class Angel(Person):
    """A small person (lines_people.Person) with what the Angel adds to one: pieces that ride
    a bone and are moved by their names (wings, lids, a halo, what hangs), and a body that may
    stand smaller than its stage."""

    def __init__(self, form_id, level, spec):
        Person.__init__(self, "angel", form_id, level, spec, _roles())
        self.silhouette = SIL
        self.movers = []
        self.L = WING[level - 1] * self.t ** 0.5

    def move(self, kind, what, items, pivot, bone, side="", n=None, up=None):
        """A piece the game moves by its name (docs/genius-lines.md, "What moves"), riding a
        bone. items: [(geometry, material[, smooth])] in the rest pose at the human's own size;
        pivot: the point it turns about; up: the way its own up points where that is not Z."""
        name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else "")
        items = [it for it in items if it[0] and it[0][0]]
        if items:
            self.movers.append((name, items, Vector(pivot), bone, up))

    def held(self, side, p):
        """A point drawn as the hand hangs (the fist at the origin, up +Z, forward -Y, away
        from the body +X, for either hand), where it is in the rest pose."""
        slot = self.J["handslot." + side]
        s = 1.0 if side == "l" else -1.0
        p = V(p)
        return Vector((slot.x - s * p.z, slot.y + p.y, slot.z + p.x))

    def grip(self, side, name, items):
        """Things in a hand that do not move in it: [(geometry, material[, smooth])], drawn as
        the hand hangs."""
        for i, it in enumerate(items):
            if it[0] and it[0][0]:
                self.add("%s_%s_%d" % (name, side, i), ([self.held(side, q) for q in it[0][0]], it[0][1]), it[1], "hand." + side, it[2] if len(it) > 2 else None)

    def hold_move(self, side, kind, what, items, pivot, n=None):
        """A piece in a hand that the game moves: drawn as the hand hangs, hung by `pivot`."""
        s = 1.0 if side == "l" else -1.0
        out = []
        for it in items:
            if it[0] and it[0][0]:
                out.append((([self.held(side, p) for p in it[0][0]], it[0][1]),) + tuple(it[1:]))
        self.move(kind, what, out, self.held(side, pivot), "hand." + side, side=side, n=n, up=(-s, 0, 0))

    def repose(self, arm, body, turns):
        """Stand it otherwise than its kind stands: turns is [(bone, the way it is to point in
        the world, degrees it is then turned about itself)], parents first. A form has no clips of its own:
        the game moves it by its base body's, as far from its rest as they are from theirs. So
        the rest is made the one which, moved as the idle moves it, comes to the pose wanted:
        the skin is set in it, and the bones' rest with it."""
        bpy.context.view_layer.objects.active = arm
        arm.data.pose_position = "POSE"
        old = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        act = bpy.data.actions.get("Idle")
        ad = arm.animation_data
        if act and ad:
            for tr in ad.nla_tracks:
                tr.mute = True
            ad.action = act
            if hasattr(ad, "action_slot") and getattr(act, "slots", None):
                ad.action_slot = act.slots[0]
            bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        idle = {pb.name: pb.matrix_basis.to_quaternion() for pb in arm.pose.bones}
        if os.environ.get("ANGEL_DEBUG"):
            log("actions", [a.name for a in bpy.data.actions][:8], "anim", bool(ad), "bones", [b.name for b in arm.pose.bones if "arm" in b.name or "hand" in b.name or "wrist" in b.name])
            log("idle upperarm.r", tuple(round(x, 2) for x in idle["upperarm.r"]), "lowerarm.r", tuple(round(x, 2) for x in idle["lowerarm.r"]))
        # (the clip is let go before the bones are turned, or the next look at the scene puts them back)
        held = {pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones}
        if ad:
            ad.action = None
        for pb in arm.pose.bones:
            pb.matrix_basis = held[pb.name]
        bpy.context.view_layer.update()
        to_arm = arm.matrix_world.to_3x3().inverted()
        if os.environ.get("ANGEL_DEBUG"):
            log("arm world", [tuple(round(x, 2) for x in r) for r in arm.matrix_world.to_3x3()])
            for bn, _, _ in turns:
                log(bn, "idle points", tuple(round(x, 2) for x in (arm.matrix_world.to_3x3() @ arm.pose.bones[bn].matrix.to_3x3() @ Vector((0, 1, 0)))))
        for bone, way, twist in turns:
            pb = arm.pose.bones[bone]
            M = pb.matrix.copy()
            head = Matrix.Translation(M.translation)
            now = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
            way = (to_arm @ Vector(way)).normalized()
            R = Matrix.Rotation(rad(twist), 4, way) @ now.rotation_difference(way).to_matrix().to_4x4()
            pb.matrix = head @ R @ head.inverted() @ M
            bpy.context.view_layer.update()
        want = {bone: arm.pose.bones[bone].matrix_basis.to_quaternion() for bone, _, _ in turns}
        if os.environ.get("ANGEL_DEBUG"):
            for bn, _, _ in turns:
                log(bn, "turned points", tuple(round(x, 2) for x in (arm.matrix_world.to_3x3() @ arm.pose.bones[bn].matrix.to_3x3() @ Vector((0, 1, 0)))))
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"
            pb.location, pb.scale = (0, 0, 0), (1, 1, 1)
            pb.rotation_quaternion = (want[pb.name] @ idle[pb.name].inverted()) if pb.name in want else (1, 0, 0, 0)
        bpy.context.view_layer.update()
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
        W = arm.matrix_world
        if os.environ.get("ANGEL_DEBUG"):
            for pb in arm.pose.bones:
                pb.matrix_basis = held[pb.name]
            bpy.context.view_layer.update()
            for bn, _, _ in turns:
                log(bn, "at ease now points", tuple(round(x, 2) for x in (W.to_3x3() @ arm.pose.bones[bn].matrix.to_3x3() @ Vector((0, 1, 0)))))
            for pb in arm.pose.bones:
                pb.matrix_basis = Matrix.Identity(4)
            bpy.context.view_layer.update()
            for bn, _, _ in turns:
                b = arm.data.bones[bn]
                log(bn, "lay", tuple(round(x, 2) for x in (old[bn].to_3x3() @ Vector((0, 1, 0)))), "now", tuple(round(x, 2) for x in (b.matrix_local.to_3x3() @ Vector((0, 1, 0)))),
                    "want", tuple(round(x, 2) for x in want[bn]), "idle", tuple(round(x, 2) for x in idle[bn]))
        return {b.name: W @ b.matrix_local @ old[b.name].inverted() @ W.inverted() for b in arm.data.bones}

    def finish(self, path, clips=False):
        p, hb, hu = self.p, self.hb, self.p.hu
        arm, s = p.arm, p.s
        body = hu.mesh_object("Body", self.v, hb.faces, self.mats, face_material=[int(i) for i in self.fmat])
        hb.weight_body(body)
        # thin it: the hands first, the face last
        w = np.where(self.hand, 1.0, np.where(hb.is_head, 0.3, 0.75))
        w[self.ears] = 0.55
        vg = body.vertex_groups.new(name="_thin")
        for value in (1.0, 0.75, 0.55, 0.3):
            vg.add([int(i) for i in np.nonzero(w == value)[0]], value, "REPLACE")
        tris = sum(len(poly.vertices) - 2 for poly in body.data.polygons)
        bpy.ops.object.select_all(action="DESELECT")
        body.select_set(True)
        bpy.context.view_layer.objects.active = body
        dec = body.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = min(1.0, TRIS[self.level - 1] * float(self.b.get("faces", 1.0)) / tris)
        dec.vertex_group = "_thin"
        dec.vertex_group_factor = 1.0
        bpy.ops.object.modifier_apply(modifier="Decimate")
        body.vertex_groups.remove(body.vertex_groups["_thin"])
        body.select_set(False)
        # the pieces: each rides its bone, as part of the one skin
        made = []
        for name, geo, material, bone, smooth in self.pieces:
            ob = g.to_object(name, geo, material, material.name.startswith(SOFT) if smooth is None else smooth)
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
        # what the game moves: each its own mesh on its bone, turning about its own origin
        moved = []
        for name, items, pivot, bone, up in self.movers:
            obs = []
            for i, it in enumerate(items):
                m = it[1] if not isinstance(it[1], str) else self.material(it[1])
                obs.append(g.to_object("%s_%d" % (name, i), it[0], m, it[2] if len(it) > 2 else m.name.startswith(SOFT)))
            ob = g.join(name, obs)
            ob.parent = arm
            ob.parent_type = "BONE"
            ob.parent_bone = bone
            bpy.context.view_layer.update()
            ob.matrix_world = Matrix.Identity(4)
            moved.append((ob, pivot, up, bone))
        shifted = {}
        if self.spec.get("pose"):
            shifted = self.repose(arm, body, STANCES[self.spec["pose"]])
        moved = [(ob, shifted[bone] @ pivot if bone in shifted else pivot, up) for ob, pivot, up, bone in moved]
        r = p.r
        r.skinned, r.attached = [body], [m[0] for m in moved]
        r.uniform(s)
        bpy.context.view_layer.update()
        for ob, pivot, up in moved:
            kit.set_origin(ob, pivot * s)
            if up is not None:
                _turn_frame(ob, up)
        for a in list(bpy.data.actions):
            if not clips or a.name not in kit.KEEP_CLIPS:
                bpy.data.actions.remove(a)
        if clips and arm.animation_data:
            for tr in list(arm.animation_data.nla_tracks):
                if tr.name not in kit.KEEP_CLIPS:
                    arm.animation_data.nla_tracks.remove(tr)
        socks = {}
        for name, (bone, at, rot) in p.common_sockets().items():
            if bone in shifted:      # a socket on a bone that was stood otherwise goes with it
                at = shifted[bone] @ Vector(at)
                rot = shifted[bone].to_3x3() @ (rot if rot is not None else Matrix.Identity(3))
            socks[name] = kit.bone_socket(arm, name, bone, Vector(at) * s, rot)
        # a body that stands smaller than its stage has its measure above its head
        socks["ref_top"] = kit.free_socket("ref_top", (0, 0, self.crown * s / float(self.b.get("small", 1.0))))
        arm.data.pose_position = "POSE" if clips else "REST"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in [arm, body] + [m[0] for m in moved] + list(socks.values()):
            o.select_set(True)
        bpy.context.view_layer.objects.active = arm
        if clips:       # the base's own body: the three clips every form of the line moves by
            bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                      export_animations=True, export_animation_mode="ACTIONS", export_skins=True, export_texcoords=False)
        else:           # no clips: a form moves by its base body's, which the game fits to its proportions
            bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                      export_animations=False, export_skins=True, export_texcoords=False)
        tris = sum(len(poly.vertices) - 2 for poly in body.data.polygons) + sum(len(poly.vertices) - 2 for m in moved for poly in m[0].data.polygons)
        log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB, %d that move" % (tris, os.path.getsize(path) // 1024, len(moved)))


# ======================================================================================
# The face: eyes that blink, brows, a mouth; each Path a temperament you can see
# ======================================================================================

def _on_face(P, x, z, out=0.0):
    """The point of its face at (x, z), `out` proud of the skin."""
    return Vector((x, P.front(z, x) - out, z))


def eye_at(P, s):
    """Where an eye lies: on the skin over the socket (the head's skin is whole across it, and
    domed: an eye is a lens laid on that dome, its middle just under the skin)."""
    return _on_face(P, s * P.eye.x, P.eye.z, -0.1 * P.eye_r)


def eyes(P, style_):
    """open (level and steady), wide (the white all round), lowered (a lid half down), shut,
    light (plain light from lid to lid). Each eye is its own piece, and blinks.

    The game inks whatever stands proud of the skin and gives anything called an eye a hard
    highlight, which on a face this small makes spectacles of a white ball with a dark middle.
    So an eye is one dark lens (not of the eye's material), with one point of white, as a
    woodcut has it; only a wide eye shows its white."""
    size = {"open": 1.0, "wide": 1.2, "lowered": 1.0, "shut": 1.0, "light": 1.05}.get(style_, 1.0) * (1.12 if P.level == 1 else 1.0)
    r = P.eye_r * 1.25 * size
    lens = (1.0, 0.42, 0.8)
    shut, lid = None, None
    for s, tag in ((1, "l"), (-1, "r")):
        c = eye_at(P, s)
        if style_ == "shut":        # the line of its lashes, on a lid
            pts = [c + Vector((-s * r * 0.95, r * 0.16, r * 0.1)), c + Vector((0, -r * 0.2, -r * 0.2)), c + Vector((s * r * 0.95, r * 0.2, r * 0.14))]
            shut = g.merge(shut, g.tube(pts, [r * 0.1, r * 0.16, r * 0.09], n=4))
            continue
        if style_ == "lowered":
            lid = g.merge(lid, g.ico(c + Vector((0, -r * 0.04, r * 0.5)), r, sub=1, scale=(1.12, 0.5, 0.56)))
        if style_ == "light":
            items = [(g.ico(c, r, sub=1, scale=lens), field("eyes", 3.6))]
        elif style_ == "wide":
            f = c + Vector((0, -r * 0.22, 0))
            items = [(g.ico(c, r, sub=1, scale=(1.0, 0.42, 0.92)), mat("eye_white")), (g.ico(f, r * 0.5, sub=1, scale=(1.0, 0.5, 1.0)), mat("void"))]
        else:
            items = [(g.ico(c, r, sub=1, scale=lens), mat("void")),
                     (g.ico(c + Vector((s * r * 0.3, -r * 0.36, r * (0.26 if style_ != "lowered" else 0.0))), r * 0.2, sub=0, scale=(1.0, 0.5, 1.0)), mat("bone_angel"))]
        P.move("blink", "eye", items, c, "head", side=tag)
    if shut:
        P.add("lashes", shut, mat("brow_angel"), "head", smooth=True)
    if lid:
        P.add("lids", lid, P.skin, "head", smooth=True)
    return r


def brows(P, style_, r):
    """level, raised (the inner ends up: it is about to speak), stern (drawn down), soft."""
    if not style_ or style_ == "none":
        return
    r = P.eye_r * 1.25
    din, dout = {"level": (0.0, 0.0), "raised": (0.8, 0.35), "stern": (-0.6, 0.3), "soft": (0.35, -0.1)}.get(style_, (0.0, 0.0))
    geo = None
    for s in (1, -1):
        z0, z1 = P.eye.z + r * (1.5 + din), P.eye.z + r * (1.62 + dout)
        x0, x1 = s * P.eye.x * 0.34, s * (P.eye.x + r * 1.15)
        a, b = _on_face(P, x0, z0), _on_face(P, x1, z1)
        m = _on_face(P, (x0 + x1) / 2, (z0 + z1) / 2 + r * 0.14)
        geo = g.merge(geo, g.tube([a, m, b], [r * 0.15, r * 0.17, r * 0.09], n=5, flat=0.7))
    P.add("brows", geo, mat("brow_angel"), "head", smooth=True)


def mouth(P, style_):
    """closed, small, open (it is already speaking), line (it has said what it will say)."""
    if not style_:
        return
    hr = P.hr
    c = pd.mouth_at(P)
    w, h = {"closed": (0.26, 0.045), "small": (0.14, 0.075), "open": (0.22, 0.2), "line": (0.38, 0.035)}.get(style_, (0.26, 0.045))
    P.add("mouth", g.ico(c + Vector((0, 0.02 * hr, 0)), hr, sub=1, scale=(w, 0.16, h)), mat("maw"), "head", smooth=True)


def face(P, spec):
    """What stands in place of a face, or over it: blindfold (a band tied over the eyes),
    band-up (the same, pushed up on the brow), light (a light where the face was, in a cowl),
    lamp (a lamp where the head was)."""
    kind, size, word = opt(spec.get("face"))
    v, e, hr = P.v0, P.eye, P.hr
    r = P.eye_r * 1.35
    if kind in ("blindfold", "band-up"):
        z0, z1 = (e.z - r * 1.3, e.z + r * 1.5) if kind == "blindfold" else (e.z + r * 2.1, e.z + r * 4.2)
        band = P.hb.is_head & (v[:, 2] > z0) & (v[:, 2] < z1) & ~P.ears
        P.wear(band, mat("accent"), 0.035)
        # the knot behind, and its two ends down the back
        zk = (z0 + z1) / 2
        k = Vector((0, P.hy1 + 0.05 * hr, zk))
        P.add("band_knot", g.ico(k, 0.2 * hr, sub=1, scale=(1.2, 0.8, 1.0)), mat("accent_dark"), "head", smooth=True)
        ends = None
        for s in (1, -1):
            pts = [k + Vector((s * 0.06 * hr, 0.02, 0)), k + Vector((s * 0.3 * hr, 0.16 * hr, -0.9 * hr)), k + Vector((s * 0.42 * hr, 0.2 * hr, -2.0 * hr * size))]
            ends = g.merge(ends, g.tongue(pts, [0.26 * hr, 0.3 * hr, 0.22 * hr], thick=0.2, normal=Y))
        P.move("sway", "band", [(ends, mat("accent"))], k, "head")
    if kind == "light":
        # a cowl, and nothing in it but light
        fa = (v[:, 1] < e.y + 0.3 * hr) & (v[:, 2] < e.z + 1.0 * hr) & (np.abs(v[:, 0]) < 0.82 * hr)
        P.wear(P.headv & ~fa, P.material("main"), 0.05)
        P.paint(P.headv & fa, mat("void"))
        c = Vector((0, P.hy0 + 0.08 * hr, e.z - 0.1 * hr))
        P.move("pulse", "face", [(g.ico(c, hr, sub=2, scale=(0.72, 0.3, 0.92)), field("face", 3.4))], c, "head")
        P.add("cowl_rim", _hoop((0, P.hy0 + 0.22 * hr, e.z - 0.02 * hr), 0.9 * hr, 1.12 * hr, 0.09 * hr, u=X, v=Z, n=12, sides=4), P.material("under"), "head", smooth=True)
    if kind == "lamp":
        # a lamp where its head was: six panes of light in a frame of brass, a roof over, a collar under
        c = Vector((0, P.hcy, (P.chin + P.crown) / 2))
        R, H = hr * 1.34, P.hh * 0.62
        panes = g.lathe([(R * 0.86, -H), (R * 0.98, -H * 0.2), (R * 0.98, H * 0.5), (R * 0.84, H)], n=6, centre=c, phase=math.pi / 6)
        bars = None
        for k in range(6):
            a = math.pi / 6 + math.pi / 3 * k
            d = Vector((math.cos(a), math.sin(a), 0))
            bars = g.merge(bars, g.tube([c + d * R * 0.9 - Z * H, c + d * R * 1.03 - Z * H * 0.2, c + d * R * 1.03 + Z * H * 0.5, c + d * R * 0.88 + Z * H], R * 0.07, n=4))
        for z, k in ((-H, 0.9), (H, 0.88), (-H * 0.2, 1.03)):
            bars = g.merge(bars, _hoop(c + Z * z, R * k, R * k, R * 0.06, u=X, v=Y, n=6, sides=4))
        P.add("lamp_frame", bars, mat("brass_horn"), "head", smooth=False)
        P.add("lamp_roof", g.lathe([(R * 1.12, H), (R * 0.6, H * 1.42), (R * 0.14, H * 1.72), (R * 0.2, H * 1.9), (0.0, H * 2.0)], n=6, centre=c, phase=math.pi / 6), mat("brass_horn"), "head", smooth=False)
        P.add("lamp_foot", g.lathe([(R * 0.5, -H * 1.5), (R * 0.95, -H * 1.12), (R * 0.9, -H)], n=6, centre=c, phase=math.pi / 6), mat("brass_horn"), "head", smooth=False)
        P.move("pulse", "lamp", [(panes, field("lamp", 3.2), True)], c, "head")
        fl = c + Z * (-H * 0.5)
        P.move("flick", "flame", [(g.blade(fl + Y * (-R * 1.0), fl + Y * (-R * 1.0) + Z * H * 1.2, R * 0.6, normal=Y, belly=0.34, thick=R * 0.2), mat("eye_white"))], fl + Y * (-R * 1.0), "head")
    return kind


# ======================================================================================
# Hair
# ======================================================================================

def hair(P, spec):
    """down (the fledgling's: tufts of it), cropped, swept (blown back), curls, bound (a knot
    behind), long (to the shoulders), bare."""
    kind, size, word = opt(spec.get("hair"))
    if not kind or kind == "bare":
        return
    hr, top, cy = P.hr, P.crown, P.hcy
    if kind == "down":
        m = mat("feather_down")
        P.wear(pt.scalp(P), m, 0.03)
        geo = None
        for i, (dx, dy, dz, rr) in enumerate(((0.0, 0.0, 0.16, 0.42), (-0.5, 0.1, 0.02, 0.36), (0.5, 0.1, 0.02, 0.36), (0.0, 0.62, -0.05, 0.4), (0.0, -0.56, 0.02, 0.3), (-0.34, -0.38, 0.06, 0.26), (0.36, -0.36, 0.05, 0.27))):
            geo = g.merge(geo, g.ico((dx * hr, cy + dy * hr, top - 0.14 * hr + dz * hr), rr * hr * size, sub=1))
        geo = g.merge(geo, g.blade((0.05 * hr, cy - 0.1 * hr, top + 0.1 * hr), (0.3 * hr, cy + 0.2 * hr, top + 0.66 * hr), 0.2 * hr, normal=Y, belly=0.5))
        P.add("down", geo, m, "head", smooth=True)
        return
    m = P.material("trim")
    P.wear(pt.scalp(P), m, 0.032)
    geo = None
    if kind == "cropped":
        for dx in (-0.62, -0.22, 0.2, 0.6):
            b0 = Vector((dx * hr, P.hy0 + (0.2 + 0.3 * dx * dx) * hr, P.eye.z + 1.02 * hr))
            geo = g.merge(geo, g.blade(b0 + Vector((0, 0.06, 0.1)) * hr, b0 + Vector((dx * 0.2 + 0.12, -0.14, -0.06)) * hr, 0.5 * hr, normal=(dx, -1, 0.3), belly=0.4))
        for s in (1, -1):
            b0 = Vector((s * 0.93 * hr, P.hy0 + 0.66 * hr, P.eye.z + 0.5 * hr))
            geo = g.merge(geo, g.blade(b0, b0 + Vector((s * 0.04, -0.04, -0.6)) * hr, 0.36 * hr, normal=(s, -0.3, 0), belly=0.4))
    elif kind == "swept":
        for i, (dx, lift, L) in enumerate(((0.0, 0.5, 1.5), (-0.44, 0.38, 1.35), (0.44, 0.38, 1.35), (-0.78, 0.16, 1.1), (0.78, 0.16, 1.1), (0.0, 0.16, 1.7), (-0.4, 0.0, 1.4), (0.4, 0.0, 1.4))):
            b0 = Vector((dx * hr, P.hy0 + (0.34 + 0.26 * (i // 3)) * hr, top - (0.2 + abs(dx) * 0.5) * hr))
            geo = g.merge(geo, g.blade(b0, b0 + Vector((dx * 0.4, 1.25 * L, 0.5 * lift + 0.1)) * hr * size, 0.66 * hr, normal=(dx, -0.2, 1), belly=0.45))
    elif kind == "curls":
        n = 11
        for i in range(n):
            a = math.pi * (0.08 + 0.84 * i / (n - 1))          # round the back of the head, ear to ear
            d = Vector((math.cos(a), math.sin(a) * 1.1, 0))
            for j, (dz, rr) in enumerate(((0.52, 0.3), (0.02, 0.32), (-0.44, 0.26))):
                if j == 2 and (i < 2 or i > n - 3):
                    continue
                geo = g.merge(geo, g.ico(Vector((d.x * 0.92 * hr, cy + 0.05 * hr + d.y * 0.86 * hr, P.eye.z + (0.5 + dz) * hr)), rr * hr * size, sub=1))
        for dx in (-0.5, 0.0, 0.5):
            geo = g.merge(geo, g.ico(Vector((dx * hr, P.hy0 + (0.24 + 0.2 * dx * dx) * hr, P.eye.z + 1.12 * hr)), 0.27 * hr, sub=1))
    elif kind == "bound":
        k = Vector((0, P.hy1 - 0.02 * hr, P.eye.z + 0.9 * hr))
        geo = g.merge(g.ico(k, 0.4 * hr * size, sub=1, scale=(1.0, 0.9, 1.0)), _hoop(k + Vector((0, -0.2 * hr, -0.12 * hr)), 0.28 * hr, 0.28 * hr, 0.06 * hr, u=X, v=Z, n=8, sides=3))
    elif kind == "long":
        geo = pd.drape((0, cy + 0.1 * hr, 0), lambda t: (hr * (1.04 + 0.2 * t), hr * (1.14 + 0.2 * t)), [top - 0.3 * hr, P.eye.z - 0.3 * hr, P.neckz - 0.26 * P.t * size], -1.75, 1.75, thick=0.03, n=9)
    P.add("hair", geo, m, "head", smooth=True)


# ======================================================================================
# The halo: the field's light, the one thing of it that is its partner's
# ======================================================================================

def halo(P, spec):
    """slipped (too big for it, and over one eye), ring, tilted (blown back), plate (upright
    behind the head), rayed (the same, with rays), coin (no bigger than one), hung (from
    what it bears)."""
    kind, size, word = opt(spec.get("halo"))
    if not kind:
        return
    hr, top, cy = P.hr, P.crown, P.hcy
    light = field("halo", 3.2)
    R = 0.98 * hr * size
    tube = 0.085 * hr * (0.8 + 0.2 * size)
    if kind in ("ring", "tilted", "slipped", "coin", "hung"):
        tilt = {"ring": (-0.16, 0.0), "tilted": (-0.62, 0.0), "slipped": (0.34, 0.5), "coin": (-0.1, 0.0), "hung": (0.0, 0.0)}[kind]
        c = {"ring": Vector((0, cy + 0.05 * hr, top + 0.5 * hr)), "tilted": Vector((0, cy + 0.5 * hr, top + 0.38 * hr)),
             "slipped": Vector((0.3 * hr, cy - 0.1 * hr, top - 0.02 * hr)), "coin": Vector((0, cy, top + 0.32 * hr)),
             "hung": Vector((0, cy + 0.2 * hr, top + 0.7 * hr))}[kind]
        if kind == "coin":
            R, tube = 0.36 * hr * size, 0.05 * hr
        M = Matrix.Rotation(tilt[0], 3, "X") @ Matrix.Rotation(tilt[1], 3, "Y")
        u, v = M @ X, M @ Y
        geo = _hoop(c, R, R, tube, u=u, v=v, n=18, sides=5)
        items = [(geo, light, True)]
        if kind == "hung":          # the chain it hangs by
            items.append((g.tube([c + Z * 0.02, c + Z * (0.7 * hr)], 0.02 * hr, n=3), mat("brass_horn"), False))
            for k in range(3):
                a = 2 * math.pi * k / 3
                items.append((g.tube([c + Vector((R * math.cos(a), R * math.sin(a), 0)), c + Z * (0.5 * hr)], 0.012 * hr, n=3), mat("brass_horn"), False))
            P.move("sway", "halo", items, c + Z * (0.7 * hr), "head")
        elif kind == "slipped":
            P.move("sway", "halo", items, c + Vector((-0.6 * hr, 0, 0.2 * hr)), "head")
        else:
            P.move("bob", "halo", items, c, "head")
    else:
        # upright behind the head, as the old pictures have it
        c = Vector((0, P.hy1 + 0.12 * hr, P.eye.z + 0.25 * hr))
        R = 1.5 * hr * size
        items = [(_hoop(c, R, R, tube, u=X, v=Z, n=22, sides=5), light, True)]
        if kind == "rayed":
            rays = None
            n = 12
            for k in range(n):
                a = 2 * math.pi * (k + 0.5) / n
                d = Vector((math.cos(a), 0, math.sin(a)))
                L = R * (0.62 if k % 2 else 0.4)
                rays = g.merge(rays, g.blade(c + d * (R + tube * 1.6), c + d * (R + tube * 1.6 + L), R * 0.2, normal=Y, belly=0.3, thick=tube * 0.5))
            items.append((rays, light, True))
            P.move("spin", "halo", items, c, "head", up=(0, 1, 0))
        else:
            items.append((_hoop(c, R * 0.84, R * 0.84, tube * 0.45, u=X, v=Z, n=22, sides=3), mat("brass_horn"), False))
            P.move("pulse", "halo", items, c, "head")


# ======================================================================================
# Wings: its outline
# ======================================================================================

# A pose is the wing's bones and how its long feathers stand on them, in lengths of the wing:
#   arm    [(out from the body, up[, forward])...]: shoulder, elbow, wrist (smoothed)
#   span   which part of the arm carries the long feathers (0 the shoulder, 1 the tip)
#   fan    the way they point at the shoulder and at the tip: degrees from straight down,
#          toward the way the arm runs (90 straight out, 180 straight up)
#   lens   how long they are at the shoulder, the middle and the tip
#   n      how many; yaw: how far the whole wing is swung back (+) or forward (-)
#   at     where it is rooted: shoulder, mid, hip; still: it does not move (it bears a load)
#   l, r   a pose that is not the same on both sides names one for each
BASE_POSE = dict(arm=[(0, 0), (0.4, 0.22), (0.9, 0.2)], span=(0.1, 1.0), fan=(0, 78), lens=(0.6, 0.72, 0.5), n=10, yaw=10, ease=1.0, lean=0.06, at="shoulder", wide=1.0, move="glide")
POSES = {
    "stubs": dict(arm=[(0, 0), (0.34, 0.34), (0.62, 0.46)], span=(0.3, 1.0), fan=(20, 100), lens=(0.4, 0.46, 0.34), n=4, yaw=14, wide=0.6, move="beat"),
    "nubs": dict(arm=[(0, 0), (0.2, 0.4), (0.26, 0.7)], fan=(150, 178), lens=(0.26, 0.3, 0.24), n=4, yaw=10),
    "raised": dict(arm=[(0, 0), (0.24, 0.42), (0.38, 0.95)], fan=(6, 172), lens=(0.78, 0.72, 0.62), n=11, yaw=18, ease=1.25),
    "half": dict(arm=[(0, 0), (0.3, 0.3), (0.62, 0.5)], fan=(4, 122), lens=(0.74, 0.76, 0.55), n=10, yaw=16),
    "spread": dict(arm=[(0, 0), (0.4, 0.22), (0.9, 0.2)], fan=(0, 78), lens=(0.6, 0.72, 0.5), n=10, yaw=10),
    "wide": dict(arm=[(0, 0), (0.5, 0.28), (1.12, 0.3)], fan=(0, 86), lens=(0.62, 0.82, 0.6), n=12, yaw=8),
    "level": dict(arm=[(0, 0), (0.5, 0.02), (1.25, 0.0)], fan=(0, 22), lens=(0.3, 0.3, 0.24), n=13, yaw=0, lean=0.0),
    "folded": dict(arm=[(0, 0), (0.22, 0.46), (0.36, 0.2)], fan=(-4, 8), lens=(1.0, 1.3, 1.36), n=7, yaw=22),
    "low": dict(arm=[(0, 0), (0.3, 0.12), (0.52, -0.1)], fan=(0, 36), lens=(0.8, 0.9, 0.74), n=8, yaw=20),
    "braced": dict(arm=[(0, 0), (0.3, 0.14), (0.55, -0.05)], fan=(18, 46), lens=(0.9, 1.2, 1.26), n=8, yaw=30),
    "planted": dict(arm=[(0, 0), (0.24, 0.18), (0.48, 0.1)], span=(0.3, 1.0), fan=(0, 3), lens=(1.2, 1.32, 1.24), n=5, yaw=-4, wide=1.25, lean=0.0),
    "pillars": dict(arm=[(0, 0), (0.26, 0.36), (0.4, 0.8)], span=(0.0, 1.0), fan=(8, 176), lens=(0.66, 0.4, 0.36), n=10, yaw=4, lean=0.0, ease=0.45, still=True),
    "closed": dict(arm=[(0, 0, 0), (0.46, 0.1, 0.1), (0.5, 0.04, 0.5), (0.1, 0.0, 0.7)], span=(0.34, 1.0), fan=(0, 0), lens=(1.15, 1.34, 1.3), n=9, yaw=0, lean=0.0),
    "over-face": dict(arm=[(0, 0, 0), (0.3, 0.42, 0.0), (0.32, 0.62, 0.3), (0.03, 0.68, 0.44)], span=(0.52, 1.0), fan=(0, 0), lens=(0.44, 0.5, 0.46), n=6, yaw=0, lean=0.0),
    "over-feet": dict(arm=[(0, 0, 0), (0.4, -0.26, 0.08), (0.42, -0.62, 0.4), (0.06, -0.74, 0.5)], span=(0.5, 1.0), fan=(0, 0), lens=(0.6, 0.66, 0.6), n=6, yaw=0, lean=0.0, at="mid"),
    "display": dict(arm=[(0, 0), (0.24, 0.3), (0.42, 0.52)], span=(0.0, 1.0), fan=(-6, 166), lens=(0.95, 1.0, 0.9), n=11, yaw=8),
    "sunrise": dict(arm=[(0, 0), (0.12, 0.3), (0.22, 0.55)], fan=(126, 178), lens=(0.9, 1.0, 0.86), n=7, yaw=5),
    "sunrise-low": dict(arm=[(0, 0), (0.25, 0.12), (0.46, 0.2)], fan=(60, 112), lens=(0.8, 0.9, 0.8), n=6, yaw=12, at="mid"),
    "rise": dict(arm=[(0, 0), (0.18, 0.4), (0.26, 0.8)], fan=(140, 186), lens=(0.6, 0.7, 0.6), n=7, yaw=6),
    "fall": dict(arm=[(0, 0), (0.2, -0.3), (0.3, -0.66)], fan=(-6, 42), lens=(0.6, 0.72, 0.62), n=7, yaw=6, at="hip"),
    "signal-up": dict(arm=[(0, 0), (0.55, 0.62), (1.1, 1.24)], yaw=4),
    "signal-down": dict(arm=[(0, 0), (0.6, -0.34), (1.2, -0.68)], yaw=4, at="mid"),
    "swift": dict(arm=[(0, 0), (0.2, 0.3), (0.5, 0.76), (0.62, 1.28)], fan=(20, 172), lens=(0.5, 0.42, 0.6), n=11, yaw=22, wide=0.8),
    "cupped": dict(arm=[(0, 0, 0), (0.3, 0.4, 0.0), (0.5, 0.78, 0.26)], fan=(118, 186), lens=(0.5, 0.56, 0.46), n=8, yaw=0),
    "pages": dict(arm=[(0, 0), (0.36, 0.36), (0.82, 0.46)], fan=(0, 96), lens=(0.8, 0.92, 0.76), n=6, yaw=10),
    "mantled": dict(l=dict(arm=[(0, 0, 0), (0.3, 0.5, 0.1), (0.56, 0.86, 0.46)], fan=(8, 150), lens=(0.72, 0.72, 0.6), n=10, yaw=0),
                    r=dict(arm=[(0, 0), (0.2, 0.26), (0.36, 0.1)], fan=(0, 30), lens=(0.82, 0.92, 0.8), n=7, yaw=24)),
    "uneven": dict(l=dict(arm=[(0, 0, 0), (0.3, 0.3, 0.16), (0.6, 0.5, 0.5)], fan=(4, 122), lens=(0.74, 0.76, 0.55), n=10, yaw=-8),
                   r=dict(arm=[(0, 0), (0.4, 0.22), (0.9, 0.2)], fan=(0, 78), lens=(0.6, 0.72, 0.5), n=10, yaw=14)),
    "whisper": dict(l=dict(arm=[(0, 0, 0), (0.36, 0.3, 0.1), (0.42, 0.52, 0.56)], span=(0.4, 1.0), fan=(160, 186), lens=(0.4, 0.46, 0.4), n=6, yaw=0),
                    r=dict(arm=[(0, 0), (0.12, 0.3), (0.22, 0.12)], fan=(-3, 9), lens=(0.8, 1.0, 1.0), n=5, yaw=28)),
    "plucked": dict(l=dict(arm=[(0, 0), (0.4, 0.22), (0.9, 0.2)], fan=(0, 78), lens=(0.6, 0.72, 0.5), n=10, yaw=10),
                    r=dict(arm=[(0, 0), (0.4, 0.22), (0.9, 0.2)], fan=(0, 78), lens=(0.34, 0.4, 0.26), n=6, yaw=10, bare=True, wide=0.16)),
}


def _curve(pts, n):
    """A polyline smoothed through its points (Catmull-Rom), n points to a span."""
    if len(pts) < 3:
        return list(pts)
    q = [pts[0] * 2 - pts[1]] + list(pts) + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(q) - 2):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return out


def _lengths(pts):
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + (b - a).length)
    return acc


def _along(pts, acc, s):
    """The point a share s of the way along a polyline, and the way it runs there."""
    d = max(0.0, min(1.0, s)) * acc[-1]
    for i in range(len(pts) - 1):
        if d <= acc[i + 1] or i == len(pts) - 2:
            seg = pts[i + 1] - pts[i]
            L = max(1e-9, acc[i + 1] - acc[i])
            return pts[i] + seg * ((d - acc[i]) / L), seg / L


def wing(root, side, pose, L, make="feather", marks=None):
    """One wing, as {part: geometry}: arm, flight (its long feathers), coverts and lesser (the
    two ranks over their roots), and where its Path's colour lies (tips, bars), its eyes."""
    pose = dict(BASE_POSE, **pose)
    yaw = rad(pose["yaw"])
    cy, sy = math.cos(yaw), math.sin(yaw)
    pts = []
    for q in pose["arm"]:
        u, w, f = q[0], q[1], (q[2] if len(q) > 2 else 0.0)
        pts.append(root + Vector((side * u * cy, u * sy - f, w)) * L)
    arm = _curve(pts, 4)
    acc = _lengths(arm)
    out = {"arm": g.tube(arm, [L * (0.05 - 0.036 * i / (len(arm) - 1)) for i in range(len(arm))], n=5)}
    n = int(pose["n"])
    t0, t1 = pose["span"]
    a0, a1 = pose["fan"]
    l0, lm, l1 = pose["lens"]
    out_h = Vector((side * cy, sy, 0))          # the way the wing runs where its arm stands upright
    step = acc[-1] * (t1 - t0) / n
    turn = abs(rad(a1 - a0)) / n
    narrow = {"blades": 0.5, "light": 0.5, "paper": 1.0}.get(make, 1.0) * pose["wide"]
    flight, cov, less, tips, bars, eyes_d, eyes_l, lines = None, None, None, None, None, None, None, None
    if make == "light":
        along = (arm[-1] - arm[0])
        reach = along.length
        along = along / reach
        nrm = Vector((0, -1, 0))
        side_v = along.cross(nrm).normalized()
        for k, (da, ln, wd) in enumerate(((0.0, 1.0, 0.16), (0.2, 0.74, 0.12), (-0.2, 0.74, 0.12))):
            d = (along * math.cos(da) + side_v * math.sin(da)).normalized()
            flight = g.merge(flight, g.blade(arm[0] + nrm * 0.004 * k, arm[0] + d * reach * ln, reach * wd, thick=reach * 0.012, normal=nrm, belly=0.36))
        out.update(flight=flight, coverts=None, lesser=None, tips=None, bars=None, eyes_dark=None, eyes_light=None, lines=None)
        return out
    for i in range(n):
        t = (i + 0.5) / n
        base, tan = _along(arm, acc, t0 + (t1 - t0) * t)
        h = Vector((tan.x, tan.y, 0))
        h = h.normalized() if h.length > 0.35 else out_h
        a = rad(a0 + (a1 - a0) * t ** pose["ease"])
        d = (h * math.sin(a) - Z * math.cos(a) + Y * pose["lean"]).normalized()
        nrm = h.cross(Z)
        if nrm.y > 0.05 or (abs(nrm.y) <= 0.05 and nrm.x * side < 0):
            nrm = -nrm              # its face is the side that is seen: the front, or the outside
        Lf = L * (l0 + (lm - l0) * 2 * t if t < 0.5 else lm + (l1 - lm) * (2 * t - 1))
        w = max(L * (0.1 if not pose.get("bare") else 0.02), 1.55 * max(step, 0.62 * Lf * turn)) * narrow
        b = base + nrm * (L * 0.006 * (i % 3))
        if make == "paper":         # a page, square at its end
            flight = g.merge(flight, g.tongue([b, b + d * Lf * 0.5, b + d * Lf], [w * 0.8, w, w * 0.94], thick=0.05, normal=nrm))
            side_v = d.cross(nrm).normalized()
            for k in range(4):
                c = b + d * Lf * (0.3 + 0.17 * k) + nrm * (w * 0.04)
                lines = g.merge(lines, g.tube([c - side_v * w * 0.36, c + side_v * w * (0.36 - 0.14 * (k % 2))], L * 0.012, n=3))
        elif make in ("blades", "steel"):
            flight = g.merge(flight, g.blade(b, b + d * Lf, w, thick=w * (0.2 if make == "blades" else 0.1), normal=nrm, belly=0.3 if make == "blades" else 0.72))
        else:
            flight = g.merge(flight, g.blade(b, b + d * Lf, w, thick=w * 0.13, normal=nrm, belly=0.62))
        if pose.get("bare"):
            continue
        if make != "light":
            cov = g.merge(cov, g.blade(base + nrm * L * 0.022, base + nrm * L * 0.022 + d * Lf * 0.46, w * 1.12, thick=w * 0.14, normal=nrm, belly=0.6))
            less = g.merge(less, g.blade(base + nrm * L * 0.04, base + nrm * L * 0.04 + d * Lf * 0.22, w * 1.1, thick=w * 0.16, normal=nrm, belly=0.55))
        if t > 0.3:
            tips = g.merge(tips, g.blade(b + nrm * L * 0.012 + d * Lf * 0.6, b + nrm * L * 0.012 + d * Lf * 1.04, w * 0.94, thick=w * 0.1, normal=nrm, belly=0.5))
        bars = g.merge(bars, g.blade(b + nrm * L * 0.012 + d * Lf * 0.5, b + nrm * L * 0.012 + d * Lf * 0.76, w * 0.98, thick=w * 0.1, normal=nrm, belly=0.5))
        if make == "eyed":
            c = b + d * Lf * 0.76 + nrm * (w * 0.1)
            eyes_d = g.merge(eyes_d, _disc(c, w * 0.44, normal=nrm, thick=w * 0.05, n=8))
            eyes_l = g.merge(eyes_l, _disc(c + nrm * w * 0.04, w * 0.22, normal=nrm, thick=w * 0.05, n=8))
    out.update(flight=flight, coverts=cov, lesser=less, tips=tips, bars=bars, eyes_dark=eyes_d, eyes_light=eyes_l, lines=lines)
    return out


def down_wing(root, side, pose, L):
    """The fledgling's: more down than feather. Puffs along a short arm, each smaller than the
    last, and the first pins showing under them."""
    pose = dict(BASE_POSE, **pose)
    w = wing(root, side, pose, L)
    arm = _curve([root + Vector((side * q[0], 0.03 * i, q[1])) * L for i, q in enumerate(pose["arm"])], 4)
    acc = _lengths(arm)
    puffs = None
    for i, s in enumerate((0.0, 0.22, 0.44, 0.66, 0.86, 1.0)):
        p, _ = _along(arm, acc, s)
        puffs = g.merge(puffs, g.ico(p + Vector((0, 0.01, -0.02 * L)), L * (0.27 - 0.034 * i), sub=1, scale=(1.0, 0.6, 1.0)))
        if 0 < i < 5:
            puffs = g.merge(puffs, g.ico(p + Vector((-side * 0.05 * L, 0.02, -0.2 * L)), L * (0.2 - 0.028 * i), sub=1, scale=(1.0, 0.6, 1.0)))
    return {"puffs": puffs, "pins": w["flight"]}


def wing_items(P_or_none, parts, make, marks, material=None):
    """[(geometry, material, smooth)] for one wing: what it is made of, and its Path's colour."""
    M = material or (lambda name: mat(name))
    zone = marks[0] if marks else None
    step = marks[1] if marks and len(marks) > 1 else "accent"
    white, shade = M("feather_angel"), M("feather_angel_shade")
    items = []
    if make == "down":
        return [(parts["puffs"], M("feather_down"), True), (parts["pins"], M("feather_pin"), True)]
    if make == "light":
        return [(parts["flight"], field("wing", 2.4), True)]
    if make == "paper":
        items = [(parts["arm"], M("wood_staff"), False), (parts["flight"], M("paper_angel"), False), (parts["lines"], M(step), False),
                 (parts["coverts"], M("accent_pale"), False), (parts["lesser"], M("paper_angel"), False)]
        return items
    if make in ("steel", "blades"):
        plate = M("steel_blade" if make == "blades" else "steel_feather")
        items = [(parts["arm"], M("steel_feather_dark"), False), (parts["flight"], plate, False),
                 (parts["coverts"], M(step) if zone in ("coverts", "bars") else M("steel_feather_dark"), False), (parts["lesser"], M("steel_feather_dark"), False)]
        if zone == "tips":
            items.append((parts["tips"], M(step), False))
        return items
    items = [(parts["arm"], M(step) if zone == "edge" else white, True), (parts["flight"], white, True),
             (parts["coverts"], M(step) if zone == "coverts" else shade, True), (parts["lesser"], M(step) if zone == "edge" else white, True)]
    if zone == "tips":
        items.append((parts["tips"], M(step), True))
    if zone == "bars":
        items.append((parts["bars"], M(step), True))
    if make == "eyed":
        items += [(parts["eyes_dark"], M("void"), True), (parts["eyes_light"], field("eyes", 3.0), True)]
    return items


def wings(P, spec):
    """Every pair it has, the upper first; each wing its own piece, which the game moves."""
    pairs = spec.get("wings") or []
    if pairs and isinstance(pairs[0], str):
        pairs = [pairs]
    backz = P.J["chest"].z + 0.3 * P.t
    for k, pair in enumerate(pairs):
        name, size, make = opt(pair)
        make = make or "feather"
        pose = POSES[name]
        for tag, s in (("l", 1), ("r", -1)):
            ps = dict(BASE_POSE, **(pose.get(tag) or pose))
            z = {"shoulder": backz, "mid": backz - 0.3 * P.t, "hip": P.hipz + 0.16 * P.t}[ps["at"]]
            root = Vector((s * 0.085 * P.t, P.rear(z) + 0.012, z))
            L = P.L * size
            if make == "down":
                parts = down_wing(root, s, ps, L)
            else:
                parts = wing(root, s, ps, L, make, spec.get("marks"))
            items = wing_items(P, parts, make, spec.get("marks"))
            what = "wing" if k == 0 else "wing%d" % (k + 1)
            if ps.get("still"):
                for i, it in enumerate(items):
                    P.add("%s_%s_%d" % (what, tag, i), it[0], it[1], "chest", smooth=it[2])
            else:
                P.move(ps["move"], what, items, root, "chest", side=tag)


# ======================================================================================
# The robe: its partner's coat
# ======================================================================================

def skirt(P, name, z_top, z_bot, flare, material, n=16, steps=5, pleats=6, hem=None, bone="hips"):
    """What hangs from the waist: a cone from the body's own section, pleated; hem: a band
    of another material at its foot."""
    hw, hd, yo = P.ring(z_top)
    rings = []
    for i in range(steps + 1):
        t = i / steps
        z = z_top + (z_bot - z_top) * t
        k = t ** 0.85
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n
            fold = 1.0 + 0.07 * k * math.cos(pleats * a)
            ring.append(Vector(((hw + 0.035 + flare * k) * fold * math.cos(a), yo + (hd + 0.035 + flare * k) * fold * math.sin(a), z + 0.012 * t * math.sin(pleats * a))))
        rings.append(ring)
    if hem is None:
        P.add(name, g.loft(rings, caps=True), material, bone, smooth=True)
        return
    P.add(name, g.loft(rings[:-1], caps=True), material, bone, smooth=True)
    grow = lambda ring, k: [Vector((p.x * k, yo + (p.y - yo) * k, p.z)) for p in ring]
    P.add(name + "_hem", g.loft([grow(rings[-2], 1.012), grow(rings[-1], 1.012)], caps=True), hem, bone, smooth=True)


def robe(P, spec):
    """smock (the fledgling's, cut for someone larger), tunic (to the knee), robe (to the
    feet and past them: it does not walk), gown (straight, with a train), wound (a scroll)."""
    kind, size, word = opt(spec.get("robe"))
    if not kind:
        return
    over = [e[0] for e in each(spec.get("over"))]
    main, lining = P.material("main"), P.material("under")
    hem = mat("accent") if "hem" in over else None
    waist = P.hipz + 0.14 * P.t
    if kind == "smock":
        P.wear(P.trunk(P.hipz - 0.05, P.neckz + 0.02) | P.sleeves(0.0, P.wx - 0.02), main, 0.05)
        skirt(P, "smock", waist, P.footz + 0.42 * (P.kneez - P.footz), 0.2 * P.t, main, pleats=5, hem=lining)
        sleeve_bells(P, main, lining, 0.12, long=0.12)
        collar_ring(P, lining, 0.05)
    elif kind == "tunic":
        P.wear(P.trunk(P.hipz - 0.05, P.neckz + 0.0) | P.sleeves(0.0, P.ex + 0.02), main, 0.04)
        skirt(P, "tunic", waist, P.kneez + 0.06 - 0.3 * (size - 1.0), 0.1 * P.t, main, hem=hem or lining)
        collar_ring(P, lining, 0.04)
        for s, tag in ((1, "l"), (-1, "r")):
            row = pd.arm_row(P, P.ex + 0.02)
            P.add("cuff_" + tag, _hoop((s * (P.ex + 0.02), P.army, P.armz), row[1] + 0.045, row[2] + 0.045, 0.03, u=Y, v=Z, n=8, sides=4), lining, "upperarm." + tag, smooth=True)
    elif kind in ("robe", "gown"):
        P.wear(P.trunk(P.hipz - 0.05, P.neckz + 0.02) | P.sleeves(0.0, P.wx - 0.05), main, 0.045)
        if kind == "robe":
            skirt(P, "robe", waist, P.footz - 0.16, 0.13 * P.t, main, hem=hem)
            sleeve_bells(P, main, lining, 0.1)
            collar_ring(P, lining, 0.045)
        else:
            skirt(P, "gown", waist, P.footz - 0.5 * size, 0.05 * P.t, main, pleats=8, hem=hem, steps=6)
            sleeve_bells(P, main, lining, 0.05)
            c = pd.neck_c(P)
            rr = 0.105 * P.t + 0.03
            P.add("collar", pd.wall((c.x, c.y, 0), (rr, rr), (rr + 0.05, rr + 0.05), P.neckz - 0.06 * P.t, P.neckz + 0.13 * P.t, thick=0.015, n=10), lining, "chest", smooth=False)
    elif kind == "wound":
        wound(P)


def sleeve_bells(P, main, lining, wide, long=0.0):
    """Sleeves that open like bells, the lining showing in their mouths."""
    for s, tag in ((1, "l"), (-1, "r")):
        row = pd.arm_row(P, P.wx - 0.06)
        x0, x1 = s * (P.ex + 0.04), s * (P.wx - 0.02 + long)
        r0 = g.ring((x0, P.army, P.armz), row[1] + 0.05, row[2] + 0.05, n=8, u=Y, v=Z)
        r1 = g.ring((x1, P.army, P.armz - wide * 0.5), row[1] + wide, row[2] + wide * 1.3, n=8, u=Y, v=Z)
        P.add("bell_" + tag, g.loft([r0, r1], caps=False), main, "lowerarm." + tag, smooth=True)
        r2 = g.ring((x1 - s * 0.012, P.army, P.armz - wide * 0.5), row[1] + wide * 0.94, row[2] + wide * 1.24, n=8, u=Y, v=Z)
        r3 = g.ring((x1 - s * 0.05, P.army, P.armz - wide * 0.3), row[1] + 0.02, row[2] + 0.02, n=8, u=Y, v=Z)
        P.add("bell_in_" + tag, g.loft([r1, r2, r3], caps=False), lining, "lowerarm." + tag, smooth=True)


def collar_ring(P, material, r):
    c = pd.neck_c(P)
    rr = 0.105 * P.t + 0.04
    P.add("neckline", _hoop((c.x, c.y, P.neckz - 0.02 * P.t), rr + 0.01, rr + 0.01, r * P.t, u=X, v=Y, n=10, sides=4), material, "chest", smooth=True)


def wound(P):
    """Its own scroll, wound round it from heel to shoulder, and the end still running."""
    paper = mat("paper_angel")
    P.wear(P.trunk(P.footz, P.neckz + 0.02) | P.below(P.hipz + 0.1) | P.sleeves(0.0, P.ex), paper, 0.03)
    turns = 7
    z0, z1 = P.footz - 0.1, P.neckz - 0.05
    hw0, hd0, yo0 = P.ring(P.hipz)
    pts, rings = [], []
    n = turns * 10
    for i in range(n + 1):
        t = i / n
        z = z0 + (z1 - z0) * t
        if z > P.hipz:
            hw, hd, yo = P.ring(z)
        else:               # below the hips: the legs together, narrowing to the heels
            k = 0.72 + 0.28 * (z - z0) / (P.hipz - z0)
            hw, hd, yo = hw0 * k, hd0 * k, yo0
        a = 2 * math.pi * turns * t
        out = Vector((math.cos(a), math.sin(a), 0))
        c = Vector(((hw + 0.07) * out.x, yo + (hd + 0.07) * out.y, z))
        pts.append(c)
        h = 0.085 * P.t
        rings.append([c - Z * h, c - Z * h + out * 0.03, c + Z * h + out * 0.03, c + Z * h])
    P.add("scroll_wound", g.loft(rings, caps=True), paper, "spine", smooth=False)
    edge = g.merge(g.tube([q + Z * 0.085 * P.t for q in pts[::2]], 0.022, n=3), g.tube([q - Z * 0.085 * P.t for q in pts[::2]], 0.022, n=3))
    P.add("scroll_edge", edge, mat("accent"), "spine", smooth=False)
    words = None
    for i in range(2, n - 1, 3):
        q, q2 = pts[i], pts[i + 1]
        o = Vector((q.x, q.y - yo0, 0)).normalized() * 0.036
        words = g.merge(words, g.tube([q + o + Z * 0.03 * P.t, q2 + o + Z * 0.03 * P.t], 0.014, n=3), g.tube([q + o - Z * 0.03 * P.t, q.lerp(q2, 0.6) + o - Z * 0.03 * P.t], 0.014, n=3))
    P.add("scroll_words", words, mat("accent_dark"), "spine", smooth=False)
    # the end of it, still unrolling behind
    top = pts[-1]
    tail = [top, top + Vector((0.2, 0.3, 0.3)), top + Vector((0.5, 0.75, 0.2)), top + Vector((0.65, 1.2, 0.55)), top + Vector((0.5, 1.6, 0.4))]
    P.move("sway", "scroll", [(g.tongue(tail, [0.3 * P.t] * 5, thick=0.1, normal=Z), paper, False),
                               (g.tube([q + Z * 0.02 for q in tail], 0.03, n=3), mat("accent"), False)], top, "chest")


def over(P, spec):
    """What it wears over the robe, and where its Path's colour is on its body: sash, hem (with
    the robe), tabard, stole, cowl, collar, cord, baldric, case, pauldrons, bracers, gorget."""
    acc, dark, pale, light = mat("accent"), mat("accent_dark"), mat("accent_pale"), mat("accent_light")
    v = P.v0
    waist = P.hipz + 0.15 * P.t
    for kind, size, word in each(spec.get("over")):
        if kind == "sash":
            P.wear(P.trunk(P.hipz + 0.07 * P.t, P.hipz + 0.27 * P.t), acc, 0.06)
            hw, hd, yo = P.ring(waist)
            b0 = Vector((hw * 0.72, yo - hd * 0.62 - 0.05, waist))
            P.move("sway", "sash", [(g.tongue([b0, b0 + Vector((0.03, -0.03, -0.3 * P.t)), b0 + Vector((0.07, -0.02, -0.62 * P.t * size))], [0.13 * P.t, 0.15 * P.t, 0.17 * P.t], thick=0.22, normal=(0.4, -1, 0)), acc, True),
                                    (g.box(b0 + Vector((0.07, -0.02, -0.64 * P.t * size)), (0.18 * P.t, 0.03, 0.05 * P.t)), pale, False)], b0, "hips")
            P.add("sash_knot", g.ico(b0, 0.07 * P.t, sub=1, scale=(1.0, 0.7, 1.0)), dark, "hips", smooth=True)
        elif kind == "cord":
            hw, hd, yo = P.ring(waist)
            P.add("cord", _hoop((0, yo, waist), hw + 0.05, hd + 0.05, 0.022 * P.t, u=X, v=Y, n=14, sides=4), acc, "hips", smooth=True)
            b0 = Vector((-hw * 0.5, yo - hd - 0.05, waist))
            ends = None
            for dx, L in ((-0.03, 0.56), (0.05, 0.44)):
                ends = g.merge(ends, g.tube([b0, b0 + Vector((dx, -0.02, -L * P.t * 0.5)), b0 + Vector((dx * 1.6, 0.0, -L * P.t))], 0.018 * P.t, n=4))
                ends = g.merge(ends, g.ico(b0 + Vector((dx * 1.6, 0.0, -L * P.t)), 0.04 * P.t, sub=0))
            P.move("sway", "cord", [(ends, acc, True)], b0, "hips")
        elif kind == "tabard":
            # a panel before and behind in its colour, a paler disc on the breast
            mid = np.abs(v[:, 0]) < P.ring(P.chestz)[0] * 0.7
            P.wear(P.trunk(P.hipz + 0.05, P.neckz - 0.03) & mid, acc, 0.06)
            hw, hd, yo = P.ring(P.hipz + 0.08 * P.t)
            zb = P.kneez + 0.12
            for tag, a in (("front", math.pi), ("back", 0.0)):
                geo = pd.drape((0, yo, 0), lambda t: (hw + 0.06 + 0.02 * t, hd + 0.07 + 0.05 * t), [P.hipz + 0.12 * P.t, (P.hipz + zb) / 2, zb], a - 0.8, a + 0.8, thick=0.025, n=6)
                P.add("tabard_" + tag, geo, acc, "hips", smooth=True)
            zc = P.chestz + 0.02 * P.t
            P.add("tabard_sun", _disc((0, P.front(zc) - 0.075, zc), 0.1 * P.t, normal=Y, thick=0.02, n=10), pale, "chest", smooth=False)
            P.add("tabard_edge", pd.drape((0, yo, 0), lambda t: (hw + 0.066 + 0.02, hd + 0.076 + 0.05), [zb + 0.07, zb], math.pi - 0.8, math.pi + 0.8, thick=0.03, n=6), dark, "hips", smooth=True)
        elif kind == "stole":
            geo, ends = None, None
            for s in (1, -1):
                x = s * 0.5 * P.sx
                zk = P.kneez + 0.3 * (P.hipz - P.kneez) * (1.0 - size) + 0.02
                pts = [(x, pd.neck_c(P).y + 0.06, P.neckz + 0.03), (x * 1.05, P.front(P.chestz, x) - 0.07, P.chestz), (x * 1.1, P.front(P.hipz + 0.2 * P.t, x) - 0.085, P.hipz + 0.2 * P.t),
                       (x * 1.16, P.front(P.hipz, x) - 0.12, P.hipz - 0.3 * P.t), (x * 1.2, P.front(P.hipz, x) - 0.16, zk)]
                geo = g.merge(geo, g.tongue(pts, [0.12 * P.t] * 4 + [0.14 * P.t], thick=0.25, normal=Y))
                ends = g.merge(ends, g.box((x * 1.2, P.front(P.hipz, x) - 0.165, zk + 0.07), (0.15 * P.t, 0.035, 0.05)))
                ends = g.merge(ends, g.box((x * 1.2, P.front(P.hipz, x) - 0.165, zk + 0.16), (0.15 * P.t, 0.035, 0.022)))
            P.add("stole", geo, acc, "chest", smooth=True)
            P.add("stole_ends", ends, pale, "chest", smooth=False)
            back = pd.drape((0, pd.neck_c(P).y + 0.02, 0), lambda t: (0.5 * P.sx + 0.07 * P.t, 0.13 + 0.05 * t), [P.neckz + 0.05, P.neckz - 0.02], -1.2, 1.2, thick=0.03, n=7)
            P.add("stole_back", back, acc, "chest", smooth=True)
        elif kind == "cowl":
            c = pd.neck_c(P)
            P.add("cowl", _hoop((0, c.y + 0.03, P.neckz - 0.02), 0.2 * P.t + 0.04, 0.22 * P.t + 0.05, 0.075 * P.t, u=X, v=Y, n=12, sides=5), P.material("under"), "chest", smooth=True)
            P.add("cowl_hood", g.ico((0, c.y + 0.24 * P.t, P.neckz + 0.0), 0.19 * P.t, sub=1, scale=(1.0, 0.8, 1.1)), P.material("under"), "chest", smooth=True)
        elif kind == "collar":
            c = pd.neck_c(P)
            rr = 0.105 * P.t + 0.04
            P.add("collar_high", pd.wall((c.x, c.y, 0), (rr + 0.03, rr + 0.03), (rr + 0.1, rr + 0.1), P.neckz - 0.08 * P.t, P.neckz + 0.16 * P.t, thick=0.018, n=10), acc, "chest", smooth=False)
        elif kind == "baldric":
            hw, hd, yo = P.ring(P.chestz - 0.1 * P.t)
            zc = (P.armz + P.hipz) / 2 + 0.08 * P.t
            u = Vector((hw + 0.02, 0, (P.armz - P.hipz) * 0.42)).normalized()
            P.add("baldric", _hoop((0, yo, zc), math.hypot(hw + 0.045, (P.armz - P.hipz) * 0.42), hd + 0.06, 0.035, u=u, v=Y, n=12, sides=4), dark, "chest", smooth=True)
        elif kind == "case":
            # a sealed case across its back, for what it carries
            zc = (P.armz + P.hipz) / 2 + 0.1 * P.t
            y = P.rear(zc) + 0.14
            a, b = Vector((-0.34 * P.t, y, zc - 0.3 * P.t)), Vector((0.36 * P.t, y, zc + 0.34 * P.t))
            P.add("case", g.tube([a, b], 0.085 * P.t, n=7), mat("leather_angel"), "chest", smooth=False)
            caps = g.merge(g.tube([a, a + (b - a) * 0.1], 0.095 * P.t, n=7), g.tube([b + (a - b) * 0.1, b], 0.095 * P.t, n=7))
            P.add("case_caps", caps, acc, "chest", smooth=False)
            hw, hd, yo = P.ring(P.chestz - 0.1 * P.t)
            u = Vector((hw + 0.02, 0, -(P.armz - P.hipz) * 0.42)).normalized()
            P.add("case_strap", _hoop((0, yo, zc - 0.05), math.hypot(hw + 0.045, (P.armz - P.hipz) * 0.42), hd + 0.06, 0.028, u=u, v=Y, n=12, sides=4), mat("leather_angel"), "chest", smooth=True)
        elif kind == "pauldrons":
            for s, tag in ((1, "l"), (-1, "r")):
                c = (s * (P.sx + 0.03), P.army, P.armz + 0.08)
                P.add("pauldron_" + tag, g.ico(c, 0.17 * size * P.t, sub=1, scale=(1.2, 1.05, 0.62), rot=(0, s * -0.35, 0)), mat("steel_feather"), "chest", smooth=False)
                P.add("pauldron_rim_" + tag, _hoop((c[0] + s * 0.02, c[1], c[2] - 0.04), 0.17 * P.t, 0.16 * P.t, 0.02, u=Y, v=Vector((s * 0.8, 0, -0.5)).normalized(), n=8, sides=3), acc, "chest", smooth=False)
        elif kind == "bracers":
            ax = np.abs(v[:, 0])
            P.wear(P.sleeves(P.ex + 0.07, P.wx - 0.03), mat("leather_angel"), 0.045)
            for s, tag in ((1, "l"), (-1, "r")):
                row = pd.arm_row(P, P.wx - 0.05)
                P.add("bracer_" + tag, _hoop((s * (P.wx - 0.05), P.army, P.armz), row[1] + 0.05, row[2] + 0.05, 0.022, u=Y, v=Z, n=8, sides=4), acc, "lowerarm." + tag, smooth=True)
        elif kind == "gorget":
            c = pd.neck_c(P)
            rr = 0.105 * P.t + 0.04
            P.add("gorget", pd.wall((c.x, c.y, 0), (rr + 0.1, rr + 0.09), (rr + 0.02, rr + 0.02), P.neckz - 0.1 * P.t, P.neckz + 0.07 * P.t, thick=0.02, n=8), mat("steel_feather"), "chest", smooth=False)


# ======================================================================================
# What is in its hands (drawn as the hand hangs: the fist at the origin, up +Z, forward -Y,
# away from the body +X), what is at its belt, and what it bears
# ======================================================================================

def lantern(c, s):
    """A round lamp about c, s its half-height: [(geometry, material name, smooth)]"""
    c = V(c)
    out = [(g.lathe([(s * 0.28, -s * 0.95), (s * 0.6, -s * 0.8), (s * 0.6, -s * 0.66)], n=6, centre=c), "brass_horn", False),
           (g.lathe([(s * 0.66, s * 0.62), (s * 0.4, s * 0.86), (s * 0.1, s * 1.04)], n=6, centre=c), "brass_horn", False)]
    bars = None
    for k in range(6):
        a = rad(60 * k)
        bars = g.merge(bars, g.tube([c + Vector((s * 0.55 * math.cos(a), s * 0.55 * math.sin(a), -s * 0.68)), c + Vector((s * 0.55 * math.cos(a), s * 0.55 * math.sin(a), s * 0.64))], s * 0.05, n=3))
    out.append((bars, "brass_horn", False))
    out.append((g.ico(c, s * 0.44, sub=1, scale=(0.9, 0.9, 1.3)), "field:lamp:3.6", True))
    out.append((_hoop(c + Vector((0, 0, s * 1.18)), s * 0.26, s * 0.2, s * 0.045, u=X, v=Z, n=8, sides=3), "brass_horn", False))
    return out


def hands(P, spec):
    for side, key in (("r", "right"), ("l", "left")):
        kind, size, word = opt(spec.get(key))
        if not kind:
            continue
        k = (0.5 + 0.5 * P.t) * size
        s = 1.0 if side == "l" else -1.0
        acc, pale, dark = "accent", "accent_pale", "accent_dark"
        if kind == "buckler":
            # a small round shield, on the forearm: its boss its Path's colour
            c = Vector((0.1, 0.0, 0.16 * k))
            items = [(_disc(c, 0.36 * k, normal=X, thick=0.05, n=12), "paper_angel", False), (_hoop(c + X * 0.02, 0.36 * k, 0.36 * k, 0.03 * k, u=Y, v=Z, n=12, sides=4), "steel_feather", False),
                     (g.ico(c + X * 0.035, 0.13 * k, sub=1, scale=(0.5, 1, 1)), acc, False), (_hoop(c + X * 0.03, 0.22 * k, 0.22 * k, 0.018 * k, u=Y, v=Z, n=12, sides=3), acc, False)]
            P.grip(side, kind, items)
        elif kind == "lamp-staff":
            # a lamp on a staff half as tall again as itself, hung from a crook
            top = Vector((0, -0.05, 2.5 * k))
            crook = [top, top + Vector((0, -0.12, 0.2)) * k, top + Vector((0, -0.34, 0.26)) * k, top + Vector((0, -0.5, 0.12)) * k]
            items = [(g.tube([(0, 0.02, -1.0 * k), (0, 0, 0), top], 0.03 * k, n=5), "wood_staff", False), (g.tube(crook, [0.028 * k, 0.024 * k, 0.02 * k, 0.016 * k], n=4), "brass_horn", False),
                     (_hoop((0, 0, 0.9 * k), 0.045 * k, 0.045 * k, 0.014 * k, u=X, v=Y, n=6, sides=3), acc, False), (_hoop((0, 0, 1.6 * k), 0.045 * k, 0.045 * k, 0.014 * k, u=X, v=Y, n=6, sides=3), acc, False)]
            P.grip(side, kind, items)
            hook = crook[-1]
            sz = 0.2 * k
            P.hold_move(side, "sway", "lamp", [(it[0], P.material(it[1]), it[2]) for it in lantern(hook + Vector((0, 0, -sz * 1.45)), sz)], hook)
        elif kind == "trumpet":
            # a herald's long horn, held upright at its side, a pennon of its colour hanging from it
            pts = [Vector((0, 0, -0.34 * k)), Vector((0, 0, 0.5 * k)), Vector((0, -0.02, 1.7 * k)), Vector((0, -0.04, 2.15 * k)), Vector((0, -0.05, 2.34 * k))]
            items = [(g.tube(pts, [0.022 * k, 0.026 * k, 0.04 * k, 0.1 * k, 0.2 * k], n=8, caps=False), "brass_horn", False),
                     (g.ico(pts[0], 0.045 * k, sub=1, scale=(1, 1, 0.6)), "brass_horn", False), (_hoop(pts[2], 0.05 * k, 0.05 * k, 0.014 * k, u=X, v=Y, n=6, sides=3), acc, False),
                     (_hoop((0, 0, 0.6 * k), 0.036 * k, 0.036 * k, 0.012 * k, u=X, v=Y, n=6, sides=3), acc, False)]
            P.grip(side, kind, items)
            h0 = pts[2] + Vector((0.03, 0, -0.03))
            flag = g.tongue([h0, h0 + Vector((0.03, 0.02, -0.34)) * k, h0 + Vector((0.0, 0.05, -0.7)) * k], [0.34 * k, 0.36 * k, 0.3 * k], thick=0.08, normal=X)
            mark = _disc(h0 + Vector((0.03, 0.02, -0.34)) * k + X * 0.02, 0.085 * k, normal=X, thick=0.03, n=8)
            P.hold_move(side, "sway", "pennon", [(flag, mat(acc), True), (mark, mat(pale), False)], h0)
        elif kind == "great-horn":
            # a horn longer than itself, flared like a lily, carried against one shoulder
            pts = [Vector((0.0, -0.1, -0.2)) * k, Vector((0, 0, 0)), Vector((-0.1, 0.16, 0.9)) * k, Vector((-0.16, 0.42, 1.8)) * k, Vector((-0.14, 0.74, 2.5)) * k, Vector((-0.1, 0.96, 2.86)) * k, Vector((-0.08, 1.08, 3.02)) * k]
            items = [(g.tube(pts, [0.03 * k, 0.035 * k, 0.06 * k, 0.11 * k, 0.2 * k, 0.38 * k, 0.56 * k], n=10, caps=False), "brass_horn", False),
                     (_hoop(pts[3], 0.125 * k, 0.125 * k, 0.02 * k, u=X, v=Vector((0, 0.96, -0.28)), n=8, sides=3), acc, False),
                     (_hoop(pts[2], 0.075 * k, 0.075 * k, 0.018 * k, u=X, v=Vector((0, 0.98, -0.2)), n=8, sides=3), acc, False)]
            P.grip(side, kind, items)
            h0 = pts[3] + Vector((0.0, 0.0, -0.13 * k))
            flag = g.tongue([h0, h0 + Vector((0.0, 0.04, -0.4)) * k, h0 + Vector((0.02, 0.1, -0.86)) * k], [0.5 * k, 0.52 * k, 0.4 * k], thick=0.06, normal=X)
            P.hold_move(side, "sway", "pennon", [(flag, mat(acc), True), (g.box(h0 + Vector((0.02, 0.1, -0.9)) * k, (0.03, 0.38 * k, 0.05 * k)), mat(pale), False)], h0)
        elif kind == "scroll":
            # an open scroll, the loose end trailing below it
            rod = [(g.tube([(0, -0.24 * k, 0.0), (0, 0.24 * k, 0.0)], 0.035 * k, n=6), "wood_staff", False), (g.ico((0, -0.26 * k, 0), 0.05 * k, sub=0), acc, False), (g.ico((0, 0.26 * k, 0), 0.05 * k, sub=0), acc, False)]
            P.grip(side, kind, rod)
            pts = [Vector((0.03, 0, 0)), Vector((0.07, 0.0, -0.5)) * k, Vector((0.1, 0.04, -1.0)) * k, Vector((0.05, 0.14, -1.4)) * k, Vector((0.12, 0.3, -1.7)) * k]
            page = g.tongue(pts, [0.42 * k] * 5, thick=0.05, normal=X)
            lines = None
            for i in range(7):
                q = pts[0].lerp(pts[2], (i + 1) / 8.0) + X * 0.025
                lines = g.merge(lines, g.box(q, (0.012, (0.3 - 0.06 * (i % 3)) * k, 0.016 * k)))
            P.hold_move(side, "sway", "scroll", [(page, mat("paper_angel"), False), (lines, mat(acc), False)], pts[0])
        elif kind == "quill":
            items = [(g.blade((0, 0.0, -0.06 * k), (0.03 * k, 0.2 * k, 0.9 * k), 0.3 * k, normal=X, belly=0.62), "feather_angel"), (g.blade((0.01, 0.1 * k, 0.5 * k), (0.035 * k, 0.21 * k, 0.94 * k), 0.24 * k, normal=X, belly=0.5), acc),
                     (g.cone((0, 0, -0.06 * k), (0, -0.02, -0.26 * k), 0.02, n=4), acc)]
            P.grip(side, kind, items)
        elif kind == "scales":
            # a balance hung from the fist: the beam fore and aft, a pan at either end
            hook = Vector((0.0, 0.0, -0.1 * k))
            beam_z = -0.34 * k
            half = 0.46 * k
            items = [(g.tube([hook, Vector((0, 0, beam_z))], 0.014 * k, n=4), mat("brass_horn"), False),
                     (g.tube([Vector((0.0, -half, beam_z + 0.02 * k)), Vector((0, 0, beam_z + 0.05 * k)), Vector((0.0, half, beam_z + 0.02 * k))], [0.018 * k, 0.03 * k, 0.018 * k], n=5), mat("brass_horn"), False),
                     (g.ico((0, 0, beam_z + 0.05 * k), 0.05 * k, sub=0), mat(acc), False)]
            for sy_ in (-1, 1):
                top = Vector((0, sy_ * half, beam_z + 0.02 * k))
                pc = top + Vector((0, 0, -0.5 * k))
                items.append((g.lathe([(0.02 * k, -0.07 * k), (0.15 * k, -0.045 * k), (0.2 * k, 0.0)], n=8, centre=pc), mat("brass_horn"), False))
                items.append((_disc(pc + Z * (-0.02 * k), 0.15 * k, normal=Z, thick=0.012, n=8), mat(acc), False))
                ch = None
                for j in range(3):
                    a = 2 * math.pi * j / 3 + 0.5
                    ch = g.merge(ch, g.tube([top, pc + Vector((0.19 * k * math.cos(a), 0.19 * k * math.sin(a), 0))], 0.007 * k, n=3))
                items.append((ch, mat("brass_horn"), False))
            P.hold_move(side, "sway", "scales", items, hook)
        elif kind == "pan":
            # one pan, heaped with its own feathers
            hook = Vector((0.0, 0.0, -0.1 * k))
            pc = Vector((0.0, -0.1 * k, -0.74 * k))
            items = [(g.lathe([(0.03 * k, -0.1 * k), (0.26 * k, -0.06 * k), (0.34 * k, 0.0)], n=10, centre=pc), mat("brass_horn"), False)]
            ch = None
            for j in range(3):
                a = 2 * math.pi * j / 3 + 0.5
                ch = g.merge(ch, g.tube([hook, pc + Vector((0.33 * k * math.cos(a), 0.33 * k * math.sin(a), 0))], 0.008 * k, n=3))
            items.append((ch, mat("brass_horn"), False))
            heap = None
            for j in range(9):
                a = 2.4 * j
                b0 = pc + Vector((0.14 * k * math.cos(a), 0.14 * k * math.sin(a), 0.0))
                heap = g.merge(heap, g.blade(b0, b0 + Vector((0.2 * math.cos(a + 0.6), 0.2 * math.sin(a + 0.6), 0.1 + 0.05 * (j % 3))) * k, 0.12 * k, normal=Z, belly=0.6))
            items.append((heap, mat("feather_angel"), True))
            items.append((g.blade(pc + Z * 0.03, pc + Vector((0.05, -0.1, 0.34)) * k, 0.13 * k, normal=Y, belly=0.6), mat(acc), True))
            P.hold_move(side, "sway", "pan", items, hook)
        elif kind in ("sword-down", "sword-up"):
            d = Vector((0, 0, -1)) if kind == "sword-down" else Vector((0.05, -0.34, 0.94)).normalized()
            L = (2.25 if kind == "sword-down" else 2.3) * k
            g0 = d * (0.13 * k)
            across = Vector((0, 1, 0)) if kind == "sword-down" else Vector((1, 0, 0))
            flat = d.cross(across).normalized()
            items = [(g.tube([-d * 0.2 * k, g0], 0.03 * k, n=6), "leather_angel"), (g.ico(-d * 0.24 * k, 0.06 * k, sub=1), acc),
                     (g.box(g0, (0.05 * k, 0.05 * k, 0.05 * k)), "brass_horn"),
                     (g.tube([g0 - across * 0.26 * k, g0 + across * 0.26 * k], 0.03 * k, n=4), "brass_horn"),
                     (g.tongue([g0, g0 + d * L * 0.5, g0 + d * L * 0.9, g0 + d * L], [0.15 * k, 0.13 * k, 0.1 * k, 0.01 * k], thick=0.22, normal=flat), "steel_blade"),
                     (g.tongue([g0 + flat * 0.012, g0 + flat * 0.012 + d * L * 0.62], [0.045 * k, 0.02 * k], thick=0.3, normal=flat), acc)]
            P.grip(side, kind, items)


def belt(P, spec):
    kind, size, word = opt(spec.get("belt"))
    if kind == "sword-bound":
        # the sword at its hip, tied into the scabbard with a cord of its colour
        hw, hd, yo = P.ring(P.hipz + 0.12 * P.t)
        a = Vector((hw + 0.07, yo - 0.02, P.hipz + 0.2 * P.t))
        d = Vector((0.12, 0.34, -0.93)).normalized()
        L = 1.5 * P.t
        P.add("scabbard", g.tongue([a, a + d * L * 0.6, a + d * L], [0.15 * P.t, 0.13 * P.t, 0.05 * P.t], thick=0.4, normal=X), mat("leather_angel"), "hips", smooth=False)
        P.add("scabbard_tip", g.cone(a + d * L * 0.94, a + d * L * 1.06, 0.05 * P.t, n=5), mat("brass_horn"), "hips", smooth=False)
        up = -d
        hilt = g.merge(g.tube([a, a + up * 0.3 * P.t], 0.03 * P.t, n=6), g.tube([a + up * 0.04 - Y * 0.2 * P.t, a + up * 0.04 + Y * 0.2 * P.t], 0.028 * P.t, n=4), g.ico(a + up * 0.33 * P.t, 0.055 * P.t, sub=1))
        P.add("hilt", hilt, mat("brass_horn"), "hips", smooth=False)
        knots = None
        for q in (0.0, 0.12, 0.24):
            knots = g.merge(knots, _hoop(a + d * q * P.t, 0.085 * P.t, 0.05 * P.t, 0.02 * P.t, u=Y, v=X, n=8, sides=3))
        knots = g.merge(knots, g.ico(a + up * 0.05 + X * 0.05, 0.05 * P.t, sub=0))
        P.add("peace_knots", knots, mat("accent"), "hips", smooth=True)
        P.move("sway", "knot", [(g.tube([a + X * 0.05, a + Vector((0.09, -0.02, -0.34 * P.t)), a + Vector((0.07, 0.0, -0.5 * P.t))], 0.018 * P.t, n=4), mat("accent"), True),
                                (g.ico(a + Vector((0.07, 0.0, -0.52 * P.t)), 0.04 * P.t, sub=0), mat("accent_pale"), False)], a + X * 0.05, "hips")


def bears(P, spec):
    kind, size, word = opt(spec.get("bears"))
    if kind == "arch":
        # a pointed arch of stone, borne on its two raised wings: two arcs that meet over its head
        L = P.L
        backz = P.J["chest"].z + 0.3 * P.t
        y = P.rear(backz) + 0.03
        foot = 0.4 * L + 0.085 * P.t
        z0 = backz + 0.8 * L + 0.38 * L
        stone, dark = mat("stone_arch"), mat("stone_arch_dark")
        geo, alt = None, None
        n = 6
        R = foot * 1.9                       # each arc struck from beyond the other springing: a lancet
        for s in (1, -1):
            cx = -s * (R - foot)
            a1 = math.acos((R - foot) / R)
            for i in range(n):
                t0_, t1_ = a1 * i / n, a1 * (i + 1) / n
                pa = Vector((cx + s * R * math.cos(t0_), y, z0 + R * math.sin(t0_)))
                pb = Vector((cx + s * R * math.cos(t1_), y, z0 + R * math.sin(t1_)))
                blk = g.tube([pa, pb], 0.15 * P.t, n=4, flat=0.9, up=Y)
                if i % 2:
                    alt = g.merge(alt, blk)
                else:
                    geo = g.merge(geo, blk)
            # the capital each arc springs from, on the wing's wrist
            geo = g.merge(geo, g.box((s * foot, y, z0 - 0.06), (0.36 * P.t, 0.3 * P.t, 0.12)))
            alt = g.merge(alt, g.box((s * foot, y, z0 - 0.16), (0.26 * P.t, 0.24 * P.t, 0.09)))
        top = z0 + R * math.sin(math.acos((R - foot) / R))
        P.add("arch", geo, stone, "chest", smooth=False)
        P.add("arch_alt", alt, dark, "chest", smooth=False)
        P.add("arch_key", g.box((0, y, top + 0.02), (0.22 * P.t, 0.32 * P.t, 0.3 * P.t)), mat("accent"), "chest", smooth=False)
    elif kind == "yoke":
        # the beam of its scales across its shoulders, a pan hanging on either side
        z = P.neckz + 0.02
        y = P.rear(P.neckz - 0.05) + 0.06
        half = 1.25 * P.t
        P.add("yoke", g.tube([(-half, y, z - 0.03), (-half * 0.4, y, z + 0.03), (0, y - 0.02, z + 0.05), (half * 0.4, y, z + 0.03), (half, y, z - 0.03)], [0.03, 0.045, 0.055, 0.045, 0.03], n=6), mat("brass_horn"), "chest", smooth=False)
        P.add("yoke_mid", g.ico((0, y - 0.04, z + 0.05), 0.085, sub=0), mat("accent"), "chest", smooth=False)
        for s, tag in ((1, "l"), (-1, "r")):
            top = Vector((s * half, y, z - 0.03))
            pc = top + Vector((0, 0, -1.15 * P.t))
            items = [(g.lathe([(0.03, -0.1), (0.24, -0.06), (0.32, 0.0)], n=10, centre=pc), mat("brass_horn"), False), (_disc(pc + Z * (-0.03), 0.24, normal=Z, thick=0.014, n=10), mat("accent"), False)]
            ch = None
            for j in range(3):
                a = 2 * math.pi * j / 3 + 0.5
                ch = g.merge(ch, g.tube([top, pc + Vector((0.31 * math.cos(a), 0.31 * math.sin(a), 0))], 0.009, n=3))
            items.append((ch, mat("brass_horn"), False))
            P.move("sway", "pan", items, top, "chest", side=tag)


# ======================================================================================
# One form
# ======================================================================================

def angel_form(form_id, level, spec, path=None, clips=False):
    P = Angel(form_id, level, spec)
    robe(P, spec)
    over(P, spec)
    masked = face(P, spec)
    if masked not in ("light", "lamp"):
        if masked != "blindfold":
            r = eyes(P, spec.get("eyes") or "open")
        else:
            r = P.eye_r * 1.25
        brows(P, spec.get("brows"), r)
        mouth(P, spec.get("mouth"))
    hair(P, spec)
    halo(P, spec)
    wings(P, spec)
    hands(P, spec)
    belt(P, spec)
    bears(P, spec)
    P.finish(path or os.path.join(OUT, form_id + ".glb"), clips=clips)
    return P


def build(form_id, level, spec, base):
    """One form: a small person with wings, unless its body says it has another shape now."""
    PALETTE.update(lp.OWN)
    PALETTE.update(OWN)
    try:
        shape = spec.get("shape")
        if shape:
            kit.reset()
            SHAPES[shape](form_id, level, spec)
        else:
            angel_form(form_id, level, spec)
    except Exception:
        if not os.environ.get("WILDLINE_KEEP_GOING"):     # while the line is being worked on: say which form failed, and go on
            raise
        import traceback
        log("!! %s failed" % form_id)
        traceback.print_exc()


# ======================================================================================
# The Finals that are no longer people (built at the kit's size: a body stands STAND tall)
# ======================================================================================

def _piece(kind, what, items, pivot, side="", n=None, up=None, parent=None):
    """A piece of a body with no rig that the game moves by its name: items [(geometry,
    material, smooth)], turning about pivot; up: its own up, where that is not Z."""
    name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else "")
    ob = g.join(name, [g.to_object("%s_%d" % (name, i), it[0], it[1], it[2] if len(it) > 2 else True) for i, it in enumerate(items) if it[0] and it[0][0]])
    GL.set_origin(ob, pivot)
    bpy.context.view_layer.update()
    if up is not None:
        _turn_frame(ob, up)
    if parent is not None:
        GL.child_of(ob, parent)
    return ob


def _still(name, items):
    return g.join(name, [g.to_object("%s_%d" % (name, i), it[0], it[1], it[2] if len(it) > 2 else True) for i, it in enumerate(items) if it[0] and it[0][0]])


def _shape_out(form_id, objects, c0, top=None):
    """Write a body with no rig: its pieces, the usual sockets about its middle, its measure."""
    c0 = V(c0)
    socks = kit._sockets({
        "socket_head": [tuple(c0 + Z * 0.2)], "socket_eyes": [tuple(c0 + Vector((0, -0.1, 0.1)))], "socket_mouth": [tuple(c0 + Vector((0, -0.1, 0.04)))], "socket_grip": [tuple(c0 + Vector((-0.14, 0, 0)))],
        "socket_throat": [tuple(c0 + Vector((0, -0.08, -0.05)))], "socket_light": [tuple(c0)], "socket_back": [tuple(c0 + Vector((0, 0.1, 0.05)))], "socket_body": [tuple(c0 + Vector((0, -0.1, -0.02)))],
        "socket_tail": [tuple(c0 + Vector((0, 0.12, -0.05)))], "socket_arm_l": [tuple(c0 + Vector((0.12, 0, 0.02)))], "socket_arm_r": [tuple(c0 + Vector((-0.12, 0, 0.02)))],
        "socket_limb_fl": [tuple(c0 + Vector((0.07, -0.04, -0.12)))], "socket_limb_fr": [tuple(c0 + Vector((-0.07, -0.04, -0.12)))],
    })
    path = os.path.join(OUT, form_id + ".glb")
    tris = GL.export_objects(objects, socks, path, ref=top or STAND)
    log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


def _wing_pair(what, root, L, pose, make="feather", marks=None, kind="glide", parent=None, sides=(("l", 1), ("r", -1))):
    out = []
    for tag, sg in sides:
        ps = dict(BASE_POSE, **(POSES[pose].get(tag) or POSES[pose]))
        r0 = Vector((sg * abs(root[0]), root[1], root[2]))
        out.append(_piece(kind, what, wing_items(None, wing(r0, sg, ps, L, make, marks), make, marks), r0, side=tag, parent=parent))
    return out


def _hand(palm, k, sg):
    """A great hand, palm up, its fingers toward the front and a little curled: [(geometry, material, smooth)].
    palm: the middle of the palm; k: its length; sg: +1 the left hand (its thumb toward the middle)."""
    bone = mat("bone_angel")
    c = V(palm)
    items = [(g.ico(c, k * 0.5, sub=2, scale=(0.82, 1.0, 0.3)), bone, True),
             (g.ico(c + Vector((-sg * k * 0.2, k * 0.2, -k * 0.02)), k * 0.3, sub=1, scale=(0.9, 1.0, 0.42)), bone, True)]      # the heel of the thumb
    fingers = None
    for i, (dx, L) in enumerate(((-0.33, 0.52), (-0.11, 0.62), (0.11, 0.58), (0.32, 0.44))):
        b0 = c + Vector((sg * dx * k, -k * 0.42, 0.0))
        d = Vector((sg * dx * 0.3, -1.0, 0.0)).normalized()
        pts = [b0, b0 + d * L * k * 0.42 + Z * k * 0.05, b0 + d * L * k * 0.78 + Z * k * 0.2, b0 + d * L * k * 0.96 + Z * k * 0.42]
        fingers = g.merge(fingers, g.tube(pts, [k * 0.1, k * 0.092, k * 0.08, k * 0.06], n=6))
        fingers = g.merge(fingers, g.ico(pts[-1], k * 0.062, sub=1))
    t0 = c + Vector((-sg * k * 0.4, k * 0.06, 0.0))
    tp = [t0, t0 + Vector((-sg * 0.22, -0.26, 0.1)) * k, t0 + Vector((-sg * 0.28, -0.5, 0.26)) * k]
    fingers = g.merge(fingers, g.tube(tp, [k * 0.12, k * 0.1, k * 0.07], n=6), g.ico(tp[-1], k * 0.072, sub=1))
    items.append((fingers, bone, True))
    # the wrist, in a cuff of its partner's coat with a band of its Path's colour
    w0 = c + Vector((0, k * 0.5, 0))
    items.append((g.tube([c + Vector((0, k * 0.3, 0)), w0, w0 + Vector((0, k * 0.28, -k * 0.04))], [k * 0.3, k * 0.26, k * 0.25], n=8, flat=0.62), bone, True))
    items.append((g.tube([w0 + Vector((0, k * 0.14, -k * 0.02)), w0 + Vector((0, k * 0.5, -k * 0.1)), w0 + Vector((0, k * 0.72, -k * 0.2))], [k * 0.31, k * 0.36, k * 0.42], n=8, flat=0.66), mat("cloth_robe"), True))
    items.append((g.tube([w0 + Vector((0, k * 0.1, -k * 0.015)), w0 + Vector((0, k * 0.2, -k * 0.035))], [k * 0.33, k * 0.33], n=8, flat=0.66), mat("accent"), True))
    return items


def shape_hands(form_id, level, spec):
    """Upholding Hands: two great hands, palms up, a wing at each wrist, the halo turning between."""
    k = 0.3
    obs = []
    for tag, sg in (("l", 1), ("r", -1)):
        palm = Vector((sg * 0.2, -sg * 0.12, 0.23 + sg * 0.07))
        items = _hand((0, 0, 0), k, sg)
        # each hand tipped a little toward the other, to make a cup of the two
        T = Matrix.Translation(palm) @ Matrix.Rotation(sg * -0.34, 4, "Y") @ Matrix.Rotation(0.2, 4, "X") @ Matrix.Rotation(sg * -0.62, 4, "Z")
        items = [(g.moved(it[0], T),) + tuple(it[1:]) for it in items]
        hand = _piece("bob", "hand", items, palm, side=tag)
        obs.append(hand)
        root = palm + Vector((sg * 0.03, k * 0.62, 0.02))
        ps = dict(BASE_POSE, **POSES["raised"])
        obs.append(_piece("glide", "wing", wing_items(None, wing(root, sg, ps, 0.36, "feather", ["coverts", "accent"]), "feather", ["coverts", "accent"]), root, side=tag, parent=hand))
    c = Vector((0, -0.06, 0.4))
    ring = [(_hoop(c, 0.1, 0.1, 0.012, u=X, v=Y, n=18, sides=5), field("halo", 3.2), True)]
    rays = None
    for i in range(8):
        a = 2 * math.pi * i / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        rays = g.merge(rays, g.blade(c + d * 0.118, c + d * (0.15 if i % 2 else 0.17), 0.03, normal=Z, belly=0.3, thick=0.006))
    ring.append((rays, field("halo", 3.2), True))
    obs.append(_piece("spin", "halo", ring, c))
    _shape_out(form_id, obs, (0, 0, 0.3), top=0.56)


def shape_horn(form_id, level, spec):
    """Unblown Horn: a great pale horn, bell forward, three pairs of wings along it, the
    field's light far down in its throat."""
    pale, brass, acc = mat("paper_angel"), mat("brass_horn"), mat("accent")
    pts = [Vector((0.0, 0.44, 0.2)), Vector((0.0, 0.3, 0.22)), Vector((0.0, 0.1, 0.27)), Vector((0.0, -0.1, 0.33)), Vector((0.0, -0.24, 0.4)), Vector((0.0, -0.33, 0.46)), Vector((0.0, -0.37, 0.5))]
    radii = [0.016, 0.026, 0.042, 0.064, 0.094, 0.135, 0.18]
    turn = Matrix.Rotation(rad(48), 3, "Z")
    pts = [turn @ q for q in pts]
    side = turn @ X
    items = [(g.tube(pts, radii, n=12, caps=False), pale, True), (g.ico(pts[0], 0.026, sub=1, scale=(1, 0.7, 1)), brass, False)]
    bands = None
    for i in (1, 2, 3, 4):
        d = (pts[i + 1] - pts[i - 1]).normalized()
        u = d.cross(side).normalized()
        bands = g.merge(bands, _hoop(pts[i], radii[i] + 0.006, radii[i] + 0.006, 0.007, u=side, v=u, n=10, sides=3))
    items.append((bands, brass, False))
    d = (pts[-1] - pts[-2]).normalized()
    u = d.cross(side).normalized()
    items.append((_hoop(pts[-1], radii[-1], radii[-1], 0.012, u=side, v=u, n=14, sides=4), acc, True))
    horn = _still("horn", items)
    obs = [horn]
    # its light, far down in its throat; and its halo, where a mouth would be
    obs.append(_piece("pulse", "throat", [(g.ico(pts[4] + d * 0.02, 0.07, sub=1), field("throat", 3.4), True)], pts[4]))
    obs.append(_piece("bob", "halo", [(_hoop(pts[-1] + d * 0.07, radii[-1] * 0.72, radii[-1] * 0.72, 0.011, u=side, v=u, n=18, sides=5), field("halo", 3.2), True)], pts[-1] + d * 0.07))
    for k, (i, L, pose) in enumerate(((1, 0.2, "half"), (3, 0.27, "raised"), (4, 0.34, "raised"))):
        # each pair rooted on the horn's back, either side of it (the horn lies aslant, so the roots are not mirrors)
        for tag, sg in (("l", 1), ("r", -1)):
            root = pts[i] + side * (sg * radii[i] * 0.7) + Vector((0, 0, radii[i] * 0.5))
            ps = dict(BASE_POSE, **POSES[pose])
            obs.append(_piece("glide", "wing" if k == 0 else "wing%d" % (k + 1), wing_items(None, wing(root, sg, ps, L, "feather", ["tips", "accent"]), "feather", ["tips", "accent"]), root, side=tag))
    h0 = pts[3] + Vector((0, 0, -radii[3]))
    flag = g.tongue([h0, h0 + Vector((0.0, 0.02, -0.11)), h0 + Vector((0.01, 0.04, -0.22))], [0.13, 0.14, 0.1], thick=0.06, normal=X)
    obs.append(_piece("sway", "pennon", [(flag, acc, True), (g.box(h0 + Vector((0.01, 0.04, -0.23)), (0.012, 0.1, 0.014)), mat("accent_pale"), False)], h0))
    _shape_out(form_id, obs, (0, 0, 0.33), top=0.6)


def _pan(top, drop, r):
    """A pan of its scales hung from `top` on three chains: [(geometry, material, smooth)]"""
    pc = V(top) + Vector((0, 0, -drop))
    items = [(g.lathe([(r * 0.1, -r * 0.32), (r * 0.76, -r * 0.2), (r, 0.0)], n=10, centre=pc), mat("brass_horn"), False), (_disc(pc + Z * (-r * 0.1), r * 0.74, normal=Z, thick=r * 0.05, n=10), mat("accent"), False)]
    ch = None
    for j in range(3):
        a = 2 * math.pi * j / 3 + 0.5
        ch = g.merge(ch, g.tube([V(top), pc + Vector((r * 0.97 * math.cos(a), r * 0.97 * math.sin(a), 0))], r * 0.03, n=3))
    items.append((ch, mat("brass_horn"), False))
    return items


def shape_beam(form_id, level, spec):
    """Level Beam: an upright of bone, a pair of wings for a beam, two pans on chains."""
    bone, brass, acc = mat("bone_angel"), mat("brass_horn"), mat("accent")
    top = Vector((0, 0, 0.5))
    post = [(g.lathe([(0.1, 0.0), (0.085, 0.02), (0.03, 0.05), (0.022, 0.2), (0.03, 0.22), (0.02, 0.26), (0.016, 0.46), (0.03, 0.48), (0.0, 0.5)], n=8, centre=(0, 0, 0.04)), bone, True),
            (g.lathe([(0.026, 0.2), (0.034, 0.22), (0.024, 0.26), (0.021, 0.36)], n=8, centre=(0, 0, 0.04), caps=False), acc, True), (g.lathe([(0.102, 0.0), (0.088, 0.022), (0.036, 0.05)], n=8, centre=(0, 0, 0.04), caps=False), mat("accent_dark"), True),
            (g.cone(top + Z * 0.02, top + Z * 0.12, 0.012, n=4), brass, False)]
    obs = [_still("upright", post)]
    obs.append(_piece("pulse", "halo", [(_hoop(top + Y * 0.02, 0.085, 0.085, 0.009, u=X, v=Z, n=18, sides=5), field("halo", 3.2), True)], top))
    # the beam: the two wings, as one piece that trembles toward level
    items = []
    tips = {}
    for tag, sg in (("l", 1), ("r", -1)):
        r0 = top + Vector((sg * 0.012, 0.012, 0))
        ps = dict(BASE_POSE, **POSES["level"])
        parts = wing(r0, sg, ps, 0.33, "feather", ["bars", "accent"])
        items += wing_items(None, parts, "feather", ["bars", "accent"]) + [(parts["coverts"], mat("accent_dark"), True)]
        tips[tag] = r0 + Vector((sg * 1.22 * 0.33, 0, 0.0))
    items.append((g.ico(top, 0.03, sub=1), brass, False))
    beam = _piece("sway", "beam", items, top)
    obs.append(beam)
    for tag in ("l", "r"):
        obs.append(_piece("sway", "pan", _pan(tips[tag], 0.24, 0.085), tips[tag], side=tag, parent=beam))
    _shape_out(form_id, obs, (0, 0, 0.36), top=0.56)


def shape_wheel(form_id, level, spec):
    """Eye-wheel: two rings of bone turning one inside the other, both rims set with open eyes
    of the field, on four small wings."""
    bone, acc = mat("bone_angel"), mat("accent")
    c = Vector((0, 0, 0.36))
    obs = []
    for k, (R, tube, n, axis, tag) in enumerate(((0.25, 0.022, 12, Vector((0.25, -0.9, 0.35)), ""), (0.165, 0.018, 8, Vector((-0.5, -0.6, -0.62)), "r"))):
        axis = axis.normalized()
        u = axis.cross(Z).normalized()
        v = axis.cross(u).normalized()
        items = [(_hoop(c, R, R, tube, u=u, v=v, n=28, sides=6), bone, True), (_hoop(c + axis * tube * 0.9, R, R, tube * 0.34, u=u, v=v, n=28, sides=3), acc, False),
                 (_hoop(c - axis * tube * 0.9, R, R, tube * 0.34, u=u, v=v, n=28, sides=3), acc, False)]
        whites, irises = None, None
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n
            out = u * math.cos(a) + v * math.sin(a)
            along = (-u * math.sin(a) + v * math.cos(a))
            p = c + out * (R + tube * 0.8)
            M3 = Matrix((along, axis, out)).transposed()          # an eye lying on the rim: long the way the rim runs, looking out
            eye = g.ico((0, 0, 0), tube * 1.25, sub=1, scale=(1.5, 0.9, 0.55))
            whites = g.merge(whites, ([p + M3 @ q for q in eye[0]], eye[1]))
            ir = g.ico((0, 0, tube * 0.42), tube * 0.62, sub=1, scale=(1.0, 1.0, 0.5))
            irises = g.merge(irises, ([p + M3 @ q for q in ir[0]], ir[1]))
        items += [(whites, mat("eye_white"), True), (irises, field("eyes", 3.4), True)]
        obs.append(_piece("spin", "ring" if k == 0 else "ring2", items, c, side=tag, up=axis))
    obs += _wing_pair("wing", c + Vector((0.17, 0.03, 0.17)), 0.24, "raised", marks=["bars", "accent"])
    obs += _wing_pair("wing2", c + Vector((0.17, 0.03, -0.17)), 0.22, "fall", marks=["bars", "accent"])
    _shape_out(form_id, obs, c, top=0.6)


SHAPES = {"hands": shape_hands, "horn": shape_horn, "beam": shape_beam, "wheel": shape_wheel}


def register(builders):
    global GL
    for name in ("genius_lines", "__main__"):
        m = sys.modules.get(name)
        if m is not None and getattr(m, "BUILDERS", None) is builders:
            GL = m
    if GL is None:
        import genius_lines
        GL = genius_lines
    builders["angel"] = build


# ======================================================================================
# The base's own body, and what it gives a hybrid
# ======================================================================================

def base_body():
    """game/assets/genius/bodies/kith-angel.glb: the Starter, with the three clips every form
    of the line moves by (a form has none of its own: the game fits these to it)."""
    with open(os.path.join(ROOT, "data", "genius-bases", "angel.json")) as f:
        base = json.load(f)
    spec = base["settled"]["body"]
    GL._palette_of("angel")
    GL.accent(spec)
    PALETTE.update(lp.OWN)
    PALETTE.update(OWN)
    angel_form("kith-angel", 1, spec, path=os.path.join(ROOT, "game", "assets", "genius", "bodies", SIL + ".glb"), clips=True)


def gift_halo():
    """The Angel's halo, over the head of whatever wears it: a ring of the field, rayed so that
    it reads on a wolf."""
    c = Vector((0, 0.01, 0.12))
    M = Matrix.Rotation(-0.2, 3, "X")
    u, v = M @ X, M @ Y
    light = field("halo", 3.4)
    items = [(_hoop(c, 0.12, 0.12, 0.016, u=u, v=v, n=20, sides=5), light, True)]
    rays = None
    for i in range(10):
        a = 2 * math.pi * i / 10
        d = u * math.cos(a) + v * math.sin(a)
        rays = g.merge(rays, g.blade(c + d * 0.142, c + d * (0.2 if i % 2 else 0.175), 0.04, normal=u.cross(v), belly=0.3, thick=0.008))
    items.append((rays, light, True))
    return [_piece("bob", "halo", items, c)]


def gift_wings():
    """The Angel's wings, on the back of whatever wears them: white, raised, the coverts in the
    wearer's own Path's colour."""
    return _wing_pair("wing", Vector((0.05, 0.0, -0.01)), 0.46, "raised", marks=["coverts", "accent"])


GIFTS = {"angel-halo": gift_halo, "angel-wings": gift_wings}


def build_gifts():
    out = os.path.join(ROOT, "game", "assets", "genius", "gifts")
    GL._palette_of("angel")
    GL.accent({"accent": "gold"})
    PALETTE.update(OWN)
    for name, make in GIFTS.items():
        kit.reset()
        objs = make()
        path = os.path.join(out, name + ".glb")
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        tris = sum(sum(len(q.vertices) - 2 for q in o.data.polygons) for o in objs)
        log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


if __name__ == "__main__":
    import genius_lines  # noqa: F401   (it registers every family, this one among them, as lines_angel)
    me = sys.modules["lines_angel"]
    what = sys.argv[1:] or ["body", "gifts"]
    if "body" in what:
        me.base_body()
    if "gifts" in what:
        me.build_gifts()
