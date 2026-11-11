"""WILDLINE genius lines, the small people: the Imp, the Sprite and the Homunculus
(docs/genius-evolutions.md, "The small people").

Each form is a small person of its own: its stature and proportions from its stage and its
`build`, its attire cut from its own skin, and what it has grown, wears and carries. They
are built on the people's rig from the human pipeline (genius_kit.SmallPerson), welded to
one skin and thinned; the few forms that are no longer people (the Imp's Marginal and what
it becomes, the Sprite's Star-burst) are modelled from plates and lights.

    python tools/blender/genius_lines.py imp
    python tools/blender/genius_lines.py sprite sprite-hob sprite-pixy

What a `body` may say, here (every slot holds a style, [style, size], [style, material],
or a list of those; a material is a role of the partner's coat, main, under or trim, or a
name from the kit's palette):

    build   age, head, legs, arms, hands, feet, limbs, bow, belly, wide, deep, shoulders,
            neck, ears, and any of MakeHuman's own details by its name (nose-scale-vert)
    skin    marks on the body itself          wear    what it is dressed in
    head    horns, hats, hair                 face    a glass, a mask, a second face
    eyes    how its eyes are lit              mouth   open, wide, pursed
    back    wings, a tail, a cloak, a pack    belt    what hangs at its hips
    right, left   what is in each hand        chest   what it holds to it or wears on it
    around  what keeps it company             coat    how its partner's coat is worn
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
STAND = 0.62            # the crown of every head, at the kit's size; the game stands it to its stage

# The colours that are these lines' own and no partner's coat: they stay as they are whatever
# coat the form wears, so a form in a shifted coat still has something that stands off it.
OWN = {
    "paper_old": ((0.55, 0.49, 0.36), 0.8, 0.0), "seal_wax": ((0.42, 0.07, 0.06), 0.4, 0.0), "tin": ((0.33, 0.34, 0.35), 0.4, 0.7),
    "slate": ((0.19, 0.2, 0.23), 0.85, 0.0), "slate_light": ((0.37, 0.38, 0.41), 0.85, 0.0), "chalk": ((0.78, 0.76, 0.7), 0.9, 0.0),
    "smoke": ((0.1, 0.095, 0.11), 1.0, 0.0), "welt": ((0.3, 0.09, 0.08), 0.6, 0.0), "tooth": ((0.76, 0.7, 0.58), 0.4, 0.0),
    "maw": ((0.13, 0.025, 0.025), 0.6, 0.0), "visor": ((0.1, 0.2, 0.14), 0.6, 0.0), "thread_red": ((0.5, 0.12, 0.1), 0.8, 0.0),
    "thread_blue": ((0.14, 0.22, 0.4), 0.8, 0.0), "thread_gold": ((0.62, 0.46, 0.14), 0.8, 0.0), "thorn": ((0.17, 0.11, 0.07), 0.5, 0.0),
    "beetle": ((0.07, 0.27, 0.19), 0.25, 0.3), "grass": ((0.36, 0.4, 0.2), 0.9, 0.0), "clay_wet": ((0.19, 0.165, 0.15), 0.35, 0.0),
    "glaze": ((0.1, 0.085, 0.075), 0.2, 0.0), "fired": ((0.36, 0.2, 0.13), 0.7, 0.0), "stone_face": ((0.47, 0.46, 0.44), 0.95, 0.0),
    "coal_lump": ((0.035, 0.032, 0.032), 0.9, 0.0), "moth": ((0.52, 0.47, 0.38), 0.95, 0.0), "soot": ((0.05, 0.048, 0.05), 1.0, 0.0),
    "wing_glass": ((0.4, 0.58, 0.66), 0.15, 0.0), "apron_hide": ((0.2, 0.105, 0.045), 0.8, 0.0), "robe_black": ((0.05, 0.046, 0.058), 0.9, 0.0),
    "homespun": ((0.34, 0.3, 0.24), 0.95, 0.0), "acorn": ((0.3, 0.2, 0.1), 0.85, 0.0),
}
PALETTE.update(OWN)

# what is soft is shaded round; what is hard keeps its planes
SOFT = ("fur", "cloth", "wool", "smoke", "shade", "tongue", "maw", "field", "cord", "leather", "ink", "clay", "fey", "hair", "hand", "moth", "welt", "soot", "grass", "fired", "glaze", "seal_wax",
        "apron_hide", "robe_black", "homespun")


def log(*a):
    print("[lines_people]", *a)


def each(v):
    """A slot's entries as [(style, size, word)]. A slot holds a style ("rag"), one entry with
    its size ([style, size] or [style, size, word]), or a list whose entries are a style or
    [style, size and word in either order]. The word is a material (a role of the partner's
    coat, or a name from the palette) or a variant, as the style reads it."""
    if v is None or v is False:
        return []
    if isinstance(v, str):
        return [(v, 1.0, None)]
    if len(v) >= 2 and isinstance(v[0], str) and isinstance(v[1], (int, float)):
        return [(v[0], float(v[1]), v[2] if len(v) > 2 else None)]
    out = []
    for x in v:
        if isinstance(x, str):
            out.append((x, 1.0, None))
        else:
            size, word = 1.0, None
            for y in x[1:]:
                if isinstance(y, (int, float)):
                    size = float(y)
                else:
                    word = y
            out.append((x[0], size, word))
    return out


# ======================================================================================
# The body: MakeHuman's small people, with more of the body open to a form
# ======================================================================================

FINGERS = ["%s_0%d" % (f, i) for f in ("index", "middle", "ring", "pinky", "thumb") for i in (1, 2, 3)]


def _reshape(h, ex, body_verts):
    """More than the kit's head, arms and legs: a form's hands, feet, the girth of its limbs,
    a bowed back. The vertices and the joints together, each by how much a bone carries it."""
    base, v = h.base, h.v
    n = len(v)

    def share(bones):
        w = np.zeros(n)
        for b in bones:
            if b in base.weights:
                idx, x = base.weights[b]
                np.add.at(w, idx, x / base.weight_total[idx])
        return np.clip(w, 0.0, 1.0)
    for sd in ("l", "r"):
        k = ex.get("hands", 1.0)
        if k != 1.0:
            c = base.joint(v, "joint-%s-hand" % sd)
            w = share(["hand_" + sd] + [f + "_" + sd for f in FINGERS])
            v += (v - c) * (k - 1.0) * w[:, None]
        k = ex.get("feet", 1.0)
        if k != 1.0:
            c = base.joint(v, "joint-%s-ankle" % sd)
            w = share(["foot_" + sd, "ball_" + sd])
            ground = v[:body_verts, 2].min()
            v[:, 0] += (v[:, 0] - c[0]) * (k - 1.0) * w
            v[:, 1] += (v[:, 1] - c[1]) * (k - 1.0) * w
            v[:, 2] += (v[:, 2] - ground) * (k - 1.0) * 0.6 * w
        k = ex.get("limbs", 1.0) * ex.get("arm_girth", 1.0)
        kf = ex.get("forearms", 1.0)
        if k != 1.0 or kf != 1.0:
            c = base.joint(v, "joint-%s-elbow" % sd)
            w = share(["upperarm_" + sd]) * (k - 1.0) + share(["lowerarm_" + sd]) * (k * kf - 1.0)
            v[:, 1] += (v[:, 1] - c[1]) * w
            v[:, 2] += (v[:, 2] - c[2]) * w
        k = ex.get("limbs", 1.0) * ex.get("leg_girth", 1.0)
        if k != 1.0:
            c = base.joint(v, "joint-%s-knee" % sd)
            w = share(["thigh_" + sd, "calf_" + sd])
            v[:, 0] += (v[:, 0] - c[0]) * (k - 1.0) * w
            v[:, 1] += (v[:, 1] - c[1]) * (k - 1.0) * w
    bow = ex.get("bow", 0.0)
    if bow:
        z0 = float(base.joint(v, "joint-l-upper-leg")[2])
        top = float(v[:body_verts, 2].max())
        t = np.clip((v[:, 2] - z0) / max(1e-6, top - z0), 0.0, 1.0)
        v[:, 1] -= bow * (top - z0) * t ** 1.6
    h.v = v


def small_person(sex, age, details, head, legs, arms, extras):
    """genius_kit.SmallPerson, its human reshaped by `extras` before the kit's own reshaping."""
    import human as hu
    real = hu.Human

    class Shaped(real):
        def __init__(inner, *a, **kw):
            real.__init__(inner, *a, **kw)
            _reshape(inner, extras, hu.BODY_VERTS)
    hu.Human = Shaped
    try:
        return kit.SmallPerson(sex, age, details, stand=STAND, keep_hands=True, head=head, legs=legs, arms=arms)
    finally:
        hu.Human = real


# how each kind stands at each stage (the Starter has a child's head; a Final is a figure)
STAGE = {
    "imp": [dict(age=0.17, head=2.05, legs=0.62, arms=1.0, belly=0.6, limbs=1.3, hands=1.3, feet=1.4), dict(age=0.26, head=1.7, legs=0.78, arms=1.08, belly=0.4, limbs=1.15, hands=1.2, feet=1.25),
            dict(age=0.34, head=1.45, legs=0.9, arms=1.12, belly=0.3, limbs=1.08, hands=1.12, feet=1.12), dict(age=0.44, head=1.26, legs=1.0, arms=1.16, belly=0.25)],
    "sprite": [dict(age=0.15, head=2.2, legs=0.62, arms=0.9, limbs=1.25, hands=1.2, feet=1.25), dict(age=0.25, head=1.8, legs=0.8, arms=0.92, limbs=1.1, hands=1.1, feet=1.1),
               dict(age=0.32, head=1.55, legs=0.92, arms=0.96), dict(age=0.42, head=1.34, legs=1.0, arms=1.0)],
    "homunculus": [dict(age=0.13, head=2.2, legs=0.52, arms=0.9, limbs=1.5, hands=1.4, feet=1.5, belly=0.5), dict(age=0.19, head=1.85, legs=0.64, arms=0.94, limbs=1.35, hands=1.35, feet=1.35, belly=0.3),
                   dict(age=0.28, head=1.6, legs=0.76, arms=0.98, limbs=1.22, hands=1.25, feet=1.25), dict(age=0.4, head=1.4, legs=0.86, arms=1.02, limbs=1.12, hands=1.15, feet=1.15)],
}
FACE = {
    "imp": {"ear-shape-pointed": 1.0, "ear-scale": 1.0, "ear-wing": 0.9, "head-invertedtriangular": 0.9, "chin-triangle": 1.0, "chin-prominent": 0.6, "nose-hump": 0.8,
            "nose-point": -0.6, "nose-scale-vert": 0.5, "mouth-scale-horiz": 1.0, "mouth-angles": 1.0, "eye-corner2": 0.9, "cheek-bones": 1.0, "cheek-volume": -0.8, "head-fat": -0.8},
    "sprite": {"ear-shape-pointed": 1.0, "ear-scale": 1.0, "ear-wing": 0.6, "eye-scale": 1.0, "chin-triangle": 0.7, "nose-scale-vert": -0.4, "nose-volume": -0.5,
               "cheek-volume": -0.2, "eye-height2": 0.5, "chin-width": -0.5, "mouth-scale-horiz": -0.3, "head-oval": 0.5},
    "homunculus": {"head-age": 0.9, "eye-bag": 0.8, "nose-scale-horiz": 0.5, "nose-volume": 0.5, "ear-scale": 0.8, "mouth-angles": -0.5, "head-fat": 0.4,
                   "eyebrows-trans-down": 0.5, "chin-jaw-drop": 0.3, "head-round": 0.6},
}
# a build's plain words, as MakeHuman's details
BUILD_DETAILS = {"belly": "stomach-pregnant", "wide": "torso-scale-horiz", "deep": "torso-scale-depth", "shoulders": "measure-shoulder-dist", "neck": "neck-scale-vert",
                 "hips": "hip-scale-horiz", "ears": "ear-scale", "vshape": "torso-vshape", "fat": "head-fat", "old": "head-age"}
SKIN = {"imp": "main", "sprite": "fey_skin", "homunculus": "clay"}
TRIS = [2300, 2700, 3100, 3500]      # how many faces a body keeps, by stage


class Person:
    """One form being built: the body's own skin (painted and padded where it is dressed),
    the pieces that ride its bones, its wings, and where everything is."""

    def __init__(self, kind, form_id, level, spec, roles):
        self.kind, self.form_id, self.level, self.spec, self.roles = kind, form_id, level, spec, roles
        b = dict(STAGE[kind][level - 1])
        for key, value in spec.get("build", {}).items():
            # its proportions are said against its stage's own (a head of 1.2 is a fifth larger
            # than that stage's), so a line carries them down as it grows; the rest are as given
            b[key] = b.get(key, 1.0) * value if key in ("head", "legs", "arms", "hands", "feet", "limbs") else value
        details = dict(FACE[kind])
        for key, name in BUILD_DETAILS.items():
            if key in b:
                details[name] = b[key]
        details.update({key: value for key, value in b.items() if "-" in key})      # MakeHuman's own details, by their names
        extras = {k: b[k] for k in ("hands", "feet", "limbs", "arm_girth", "leg_girth", "forearms", "bow") if k in b}
        self.b = b
        self.p = p = small_person(b.get("sex", "m"), b["age"], details, b["head"], b["legs"], b["arms"], extras)
        self.hb = hb = p.hb
        self.J = J = hb.J
        fit = hb.humans["fit"]
        self.v0 = fit.body().copy()
        self.v = self.v0.copy()
        self.n = hb.normals("fit")
        self.fa = hb.face_idx
        self.arm, self.leg, self.headv, self.hand = hb.is_arm, hb.is_leg, (hb.is_head | hb.is_neck), p.is_hand
        self.ears = np.zeros(len(self.v0), dtype=bool)
        self.ears[np.unique(self.fa[hb.base.regions["ears"]])] = True
        self.mats = []
        self.fmat = np.zeros(len(self.fa), dtype=np.int64)
        self.pieces, self.wings = [], []
        # where things are (the human's own size: 2.4 to the crown)
        (x0, x1), (y0, y1), (z0, z1) = hb.head_box
        self.hr = (x1 - x0) / 2                       # half the head's width
        self.hy0, self.hy1 = y0, y1                   # the brow, the back of the head
        self.hcy = (y0 + y1) / 2
        self.chin, self.crown = z0, z1
        self.hh = z1 - z0
        self.eye, self.eye_r = hb.eye["l"], hb.eye_r
        self.mouth = Vector(fit.joint("joint-mouth"))
        self.hipz, self.neckz, self.chestz = J["upperleg.l"].z, hb.trunk_z[9], J["chest"].z + 0.2
        self.kneez, self.footz = J["lowerleg.l"].z, J["foot.l"].z
        self.sx, self.ex, self.wx = J["upperarm.l"].x, J["lowerarm.l"].x, J["wrist.l"].x
        self.armz, self.army = J["upperarm.l"].z, J["upperarm.l"].y
        self.t = (self.neckz - self.hipz) / 0.84      # how big its trunk is against the plain small person's (a great head leaves less)
        self.skin = self.material(SKIN[kind])
        self.mi(self.skin)

    # --- materials ---------------------------------------------------------------------

    def material(self, token, default=None):
        """A material by a role of the partner's coat (main, under, trim), by its own name, or
        field:<name>[:strength] for a light."""
        token = token or default
        if token in self.roles:
            return mat(self.roles[token])
        if token.startswith("field"):
            parts = token.split(":")
            return field(parts[1] if len(parts) > 1 else "light", float(parts[2]) if len(parts) > 2 else 2.5)
        return mat(token)

    def mi(self, material):
        if material not in self.mats:
            self.mats.append(material)
        return self.mats.index(material)

    # --- the skin: painted, and padded where it is dressed ---------------------------------

    def paint(self, mask, material):
        self.fmat[mask[self.fa].all(axis=1)] = self.mi(material)

    def wear(self, mask, material, thick=0.03):
        """A garment cut from the body's own skin: where the mask holds, the skin is pushed out
        and takes the cloth's material. It is one skin, so nothing shows through it."""
        self.v[mask] += self.n[mask] * thick
        self.paint(mask, material)

    def trunk(self, z0, z1, front=False, back=False):
        v = self.v0
        m = (v[:, 2] > z0) & (v[:, 2] < z1) & ~self.arm & ~self.headv
        yc = self.J["chest"].y
        if front:
            m &= v[:, 1] < yc + 0.02
        if back:
            m &= v[:, 1] > yc - 0.02
        return m

    def sleeves(self, x0, x1):
        """The arms between two distances out from the middle."""
        ax = np.abs(self.v0[:, 0])
        return self.arm & (ax > x0) & (ax < x1)

    def below(self, z):
        return ~self.arm & ~self.headv & (self.v0[:, 2] < z)

    def front(self, z, x=0.0):
        return self.hb.front_y(x, z)

    def rear(self, z, x=0.0):
        return self.hb.front_y(x, z, back=True)

    def ring(self, z):
        """The trunk's section at a height: (half-width, half-depth, y of its middle)."""
        r = self.hb._row(self.hb.rings("trunk", "fit"), z)
        return r[1], r[2], r[3]

    # --- pieces ------------------------------------------------------------------------

    def add(self, name, geo, material, bone, smooth=None):
        """A piece that rides one bone (geometry at the human's own size, in the rest pose)."""
        if geo and geo[0]:
            self.pieces.append((name, geo, material if not isinstance(material, str) else self.material(material), bone, smooth))

    def items(self, name, items, bone):
        for i, (geo, material) in enumerate(items):
            self.add("%s_%d" % (name, i), geo, material, bone)

    def hold(self, side, name, items):
        """Things in a hand, drawn as the hand hangs at its side (the fist at the origin, up is
        +Z, forward -Y, away from the body is +X for the left hand and -X for the right)."""
        slot = self.J["handslot." + side]
        s = 1.0 if side == "l" else -1.0

        def to_rest(p):
            p = V(p)
            return Vector((slot.x - s * p.z, slot.y + p.y, slot.z + s * p.x))
        for i, (geo, material) in enumerate(items):
            if geo and geo[0]:
                self.add("%s_%s_%d" % (name, side, i), ([to_rest(p) for p in geo[0]], geo[1]), material, "hand." + side)

    def wing(self, tag, items, root):
        """A wing: its own object, pivoting at its root; the game beats it."""
        ob = g.pieces("wing_" + tag, [(geo, m if not isinstance(m, str) else self.material(m)) for geo, m in items if geo and geo[0]])
        for poly in ob.data.polygons:
            poly.use_smooth = False
        self.wings.append((ob, Vector(root)))

    # --- the eyes ----------------------------------------------------------------------

    def eyes(self, white, iris, size=1.0, pupil=None, cut="round"):
        """Two eyes: a ball in each socket and what is in front of it. cut: round (the light of
        the eye, in front), slit (the whole ball alight and a slit down it, as a goat's), glint
        (a dark ball, large, with one small light in it)."""
        r = self.eye_r * 1.04 * size
        ball, lit, dot = None, None, None
        for s in (1, -1):
            c = Vector((s * self.eye.x, self.eye.y - self.eye_r * 0.45 * (size - 1.0), self.eye.z))
            ball = g.merge(ball, g.ico(c, r, sub=1))
            if cut == "slit":
                lit = g.merge(lit, g.ico(c + Vector((0, -r * 0.8, 0)), r * 0.5, sub=1, scale=(0.3, 0.6, 1.5)))
            elif cut == "glint":
                lit = g.merge(lit, g.ico(c + Vector((s * r * 0.26, -r * 0.8, r * 0.3)), r * 0.3, sub=0, scale=(1.0, 0.6, 1.0)))
            elif cut == "dot":
                lit = g.merge(lit, g.ico(c + Vector((0, -r * 0.84, 0)), r * 0.34, sub=1, scale=(1.0, 0.5, 1.0)))
            else:
                f = c + Vector((0, -r * 0.62, 0))
                lit = g.merge(lit, g.ico(f, r * 0.62, sub=1, scale=(1.0, 0.55, 1.0)))
                if pupil is not None:
                    dot = g.merge(dot, g.ico(f + Vector((0, -r * 0.3, 0)), r * 0.26, sub=0, scale=(1.0, 0.5, 1.0)))
        self.add("eye_balls", ball, white, "head", smooth=True)
        self.add("eye_lights", lit, iris, "head", smooth=True)
        if dot:
            self.add("eye_pupils", dot, pupil, "head", smooth=True)

    # --- finishing ---------------------------------------------------------------------

    def finish(self, path):
        p, hb, hu = self.p, self.hb, self.p.hu
        arm, s = p.arm, p.s
        body = hu.mesh_object("Body", self.v, hb.faces, self.mats, face_material=[int(i) for i in self.fmat])
        hb.weight_body(body)
        # thin it: the hands first, the face last
        w = np.where(self.hand, 1.0, np.where(hb.is_head, 0.3, 0.75))
        ears = np.zeros(len(self.v), dtype=bool)
        ears[np.unique(self.fa[hb.base.regions["ears"]])] = True
        w[ears] = 0.55
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
        wings = []
        for ob, root in self.wings:
            ob.parent = arm
            ob.parent_type = "BONE"
            ob.parent_bone = "chest"
            bpy.context.view_layer.update()
            ob.matrix_world = Matrix.Identity(4)
            wings.append(ob)
        r = p.r
        r.skinned, r.attached = [body], wings
        r.uniform(s)
        bpy.context.view_layer.update()
        for ob, root in self.wings:
            kit.set_origin(ob, root * s)
        for a in list(bpy.data.actions):
            bpy.data.actions.remove(a)
        socks = {name: kit.bone_socket(arm, name, bone, Vector(at) * s, rot) for name, (bone, at, rot) in p.common_sockets().items()}
        socks["ref_top"] = kit.free_socket("ref_top", (0, 0, self.crown * s))
        arm.data.pose_position = "REST"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in [arm, body] + wings + list(socks.values()):
            o.select_set(True)
        bpy.context.view_layer.objects.active = arm
        # no clips: a form moves by its base body's, which the game fits to its proportions
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                  export_animations=False, export_skins=True, export_texcoords=False)
        tris = sum(len(poly.vertices) - 2 for poly in body.data.polygons) + sum(len(poly.vertices) - 2 for ob in wings for poly in ob.data.polygons)
        log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


# ======================================================================================
# Small builders: things made once and worn by many
# ======================================================================================

def _box(c, size, rot=None):
    return g.box(c, size, rot=rot)


def _disc(c, r, normal=Y, thick=0.02, n=10):
    """A flat round plate facing `normal`."""
    nrm = V(normal).normalized()
    u = nrm.cross(Z if abs(nrm.dot(Z)) < 0.9 else X).normalized()
    w = nrm.cross(u)
    c = V(c)
    return g.loft([g.ring(c - nrm * thick / 2, r, r, n=n, u=u, v=w), g.ring(c + nrm * thick / 2, r, r, n=n, u=u, v=w)])


def _hoop(c, rx, rz, r, u=X, v=Z, n=14, sides=4):
    pts = [V(c) + V(u) * (math.cos(2 * math.pi * i / n) * rx) + V(v) * (math.sin(2 * math.pi * i / n) * rz) for i in range(n + 1)]
    return g.tube(pts, [r] * len(pts), n=sides, caps=False)


def book(c, w, h, t, rot=None, cover="leather", pages="paper", clasp=None, slips=0, spine=1):
    """A closed book about c: w across (x), t thick (y), h tall (z), turned by rot (Euler).
    [(geometry, material name)]"""
    c = V(c)
    R = Matrix.Identity(3) if rot is None else (Matrix.Rotation(rot[2], 3, "Z") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[0], 3, "X"))
    out = [(g.box(c, (w, t, h), rot=R), cover),
           (g.box(c + R @ Vector((spine * -w * 0.03, 0, 0)), (w * 0.96, t * 0.74, h * 1.03), rot=R), pages)]
    if clasp:
        out.append((g.box(c + R @ Vector((spine * -w * 0.42, 0, 0)), (w * 0.2, t * 1.16, h * 0.16), rot=R), clasp))
    slip = None
    for i in range(slips):
        z = (-0.36 + 0.72 * (i + 0.5) / slips) * h
        slip = g.merge(slip, g.box(c + R @ Vector((spine * -w * (0.52 + 0.05 * (i % 2)), (i % 3 - 1) * t * 0.18, z)), (w * 0.22, t * 0.06, h * 0.1), rot=R))
    if slip:
        out.append((slip, "paper"))
    return out


def lantern(c, s, style="round", glow="lamp", strength=3.4, handle=True):
    """A lamp about c, s its half-height. Styles: round, square (a window with someone home),
    jar (a storm kept in it), shutter (tin, half open), eye (an eye painted on the glass),
    cold (rimed), thimble, shell (a coal in a nutshell). [(geometry, material name)]"""
    c = V(c)
    light = "field:%s:%s" % (glow, strength)
    out = []
    if style in ("round", "eye", "cold", "shutter"):
        frame = "metal_brass" if style != "cold" else "ice_dark"
        out.append((g.lathe([(s * 0.28, -s * 0.95), (s * 0.6, -s * 0.8), (s * 0.6, -s * 0.66)], n=6, centre=c), frame))
        out.append((g.lathe([(s * 0.66, s * 0.62), (s * 0.4, s * 0.86), (s * 0.1, s * 1.04)], n=6, centre=c), frame))
        bars = None
        for k in range(6):
            a = math.radians(60 * k)
            bars = g.merge(bars, g.tube([c + Vector((s * 0.55 * math.cos(a), s * 0.55 * math.sin(a), -s * 0.68)), c + Vector((s * 0.55 * math.cos(a), s * 0.55 * math.sin(a), s * 0.64))], s * 0.05, n=3))
        out.append((bars, frame if style != "cold" else "ice"))
        out.append((g.ico(c, s * 0.42, sub=1, scale=(0.9, 0.9, 1.3)), light))
        if style == "eye":
            f = c + Vector((0, -s * 0.5, 0))
            out.append((g.blade(f + Vector((-s * 0.5, 0, 0)), f + Vector((s * 0.5, 0, 0)), s * 0.5, normal=Y, belly=0.5, thick=0.004), "void"))
            out.append((g.ico(f + Vector((0, -0.012, 0)), s * 0.13, sub=0, scale=(1, 0.4, 1.3)), light))
        if style == "cold":
            rime = None
            for k in range(5):
                a = math.radians(72 * k + 20)
                b0 = c + Vector((s * 0.6 * math.cos(a), s * 0.6 * math.sin(a), -s * 0.7))
                rime = g.merge(rime, g.cone(b0, b0 + Vector((0, 0, -s * (0.5 + 0.2 * (k % 2)))), s * 0.09, n=4))
            out.append((rime, "ice_pale"))
        if style == "shutter":
            sh = None
            for k in range(4):
                a = math.radians(90 * k + 45)
                d = Vector((math.cos(a), math.sin(a), 0))
                sh = g.merge(sh, g.box(c + d * s * 0.72, (s * 0.7, s * 0.05, s * 1.3), rot=(0, 0, a + math.pi / 2 + 0.5)))
            out.append((sh, "tin"))
    elif style == "square":
        out.append((g.box(c, (s * 1.3, s * 0.7, s * 1.7)), "metal_dark"))
        out.append((g.box(c + Vector((0, -s * 0.06, 0)), (s * 1.08, s * 0.7, s * 1.46)), light))
        bars = g.merge(g.box(c + Vector((0, -s * 0.38, 0)), (s * 0.08, s * 0.08, s * 1.5)), g.box(c + Vector((0, -s * 0.38, s * 0.1)), (s * 1.12, s * 0.08, s * 0.08)),
                       g.box(c + Vector((0, -s * 0.4, -s * 0.86)), (s * 1.5, s * 0.16, s * 0.1)))
        out.append((bars, "metal_dark"))
        out.append((g.blade(c + Vector((-s * 0.8, 0, s * 0.85)), c + Vector((0, 0, s * 1.5)), s * 0.6, normal=Y, belly=0.5), "metal_dark"))
        out.append((g.blade(c + Vector((s * 0.8, 0, s * 0.85)), c + Vector((0, 0, s * 1.5)), s * 0.6, normal=Y, belly=0.5), "metal_dark"))
    elif style == "jar":
        out.append((g.lathe([(s * 0.5, -s * 0.9), (s * 0.66, -s * 0.6), (s * 0.66, s * 0.4), (s * 0.4, s * 0.72), (s * 0.4, s * 0.86)], n=8, centre=c), "glass"))
        out.append((g.lathe([(s * 0.46, s * 0.86), (s * 0.46, s * 1.02), (s * 0.1, s * 1.06)], n=8, centre=c), "tin"))
        cloud = None
        for k, (dx, dy, dz, rr) in enumerate(((0.0, -0.3, 0.1, 0.42), (0.26, -0.1, -0.2, 0.36), (-0.24, -0.16, -0.1, 0.34), (0.05, 0.2, 0.3, 0.32))):
            cloud = g.merge(cloud, g.ico(c + Vector((dx, dy, dz)) * s * 1.2, s * rr * 1.05, sub=1))
        out.append((cloud, "smoke"))
        bolt = [c + Vector((s * 0.1, -s * 0.72, s * 0.5)), c + Vector((-s * 0.16, -s * 0.74, s * 0.12)), c + Vector((s * 0.12, -s * 0.74, -s * 0.05)), c + Vector((-s * 0.08, -s * 0.72, -s * 0.5))]
        out.append((g.tongue(bolt, [s * 0.05, s * 0.16, s * 0.14, s * 0.02], thick=0.3, normal=Y), light))
    elif style == "thimble":
        out.append((g.lathe([(s * 0.5, s * 0.5), (s * 0.44, -s * 0.3), (s * 0.3, -s * 0.5), (0.0, -s * 0.52)], n=8, centre=c), "tin"))
        out.append((_disc(c + Vector((0, 0, s * 0.42)), s * 0.42, normal=Z, thick=0.01, n=8), light))
        handle = False
    elif style == "shell":
        out.append((g.lathe([(s * 0.7, s * 0.2), (s * 0.62, -s * 0.2), (s * 0.3, -s * 0.5), (0.0, -s * 0.56)], n=7, centre=c), "wood"))
        out.append((g.ico(c + Vector((0, 0, s * 0.1)), s * 0.42, sub=1, scale=(1, 1, 0.8)), light))
        handle = False
    if handle:
        out.append((_hoop(c + Vector((0, 0, s * 1.18)), s * 0.26, s * 0.2, s * 0.045, u=X, v=Z, n=8, sides=3), "metal_iron"))
    return out


def horn_pair(P, pts, radii, material, n=5):
    """Two horns from the corners of the brow: pts and radii are in head half-widths, for the
    left; the right is the mirror."""
    hr = P.hr
    base = Vector((0.55 * hr, P.hcy - 0.1 * hr, P.crown - 0.26 * hr))
    geo = None
    for s in (1, -1):
        path = [Vector((s * (base.x + q[0] * hr), base.y + q[1] * hr, base.z + q[2] * hr)) for q in pts]
        geo = g.merge(geo, g.tube(path, [r * hr for r in radii], n=n))
    return geo


# ======================================================================================
# The lines
# ======================================================================================

def _roles(silhouette):
    """The partner's coat on a body: role (main, under, trim) -> the material that wears it."""
    with open(os.path.join(ROOT, "data", "genius-looks.json")) as f:
        looks = json.load(f)
    return {role: name for name, role in looks["bodies"].get(silhouette, {}).get("roles", {}).items()}


def _silhouettes(base):
    """form id -> the silhouette it is counted as (a form that names one passes it down)."""
    out = {}

    def walk(n, sil):
        sil = n.get("silhouette", sil)
        out[n["id"]] = sil
        for key in ("paths", "prongs", "finishes"):
            for c in n.get(key, []):
                walk(c, sil)
    walk(dict(base["settled"], paths=base["paths"]), base["silhouette"])
    return out


SLOTS = {}          # slot -> {style: fn(P, size, word)}
ORDER = ("skin", "wear", "eyes", "mouth", "face", "head", "back", "chest", "belt", "right", "left", "around")


def person_form(kind, form_id, level, spec, silhouette):
    P = Person(kind, form_id, level, spec, _roles(silhouette))
    P.silhouette = silhouette
    for slot in ORDER:
        entries = each(spec.get(slot))
        if slot == "eyes" and not entries:
            entries = [("lit", 1.0, None)]
        for style, size, word in entries:
            fn = SLOTS.get(slot, {}).get(style)
            if fn is None:
                log("!! %s: no %s called %s" % (form_id, slot, style))
                continue
            P._style, P._slot = style, slot
            fn(P, size, word)
    P.finish(os.path.join(OUT, form_id + ".glb"))


def build(form_id, level, spec, base):
    """One form: a small person, unless its body says it has another shape now."""
    shape = spec.get("shape")
    PALETTE.update(OWN)          # these lines' own colours, whatever another family has since called its own
    try:
        if shape in ("marginal", "starburst"):
            kit.reset()
            getattr(people_shapes, shape)(form_id, level, spec)
        else:
            person_form(base["id"], form_id, level, spec, _silhouettes(base)[form_id])
    except Exception:
        if not os.environ.get("WILDLINE_KEEP_GOING"):     # while a line is being worked on: say which form failed, and go on
            raise
        import traceback
        log("!! %s failed" % form_id)
        traceback.print_exc()


def register(builders):
    for b in ("imp", "sprite", "homunculus"):
        builders[b] = build


def slot(name, *styles):
    """A style of a slot: fn(P, size, word); P._style is the style it was called by."""
    def deco(fn):
        for st in styles:
            SLOTS.setdefault(name, {})[st] = fn
        return fn
    return deco


# the styles themselves, a file to a subject (they are part of this family, not families of
# their own, so their names do not begin lines_)
import people_dress    # noqa: E402,F401   eyes, mouths, the skin's marks, what it is dressed in
import people_things   # noqa: E402,F401   horns and hats, wings and tails, what it wears at its chest and its belt
import people_carry    # noqa: E402,F401   what is in its hands, and what keeps it company
import people_shapes   # noqa: E402,F401   the forms that are no longer people


