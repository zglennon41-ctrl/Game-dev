"""WILDLINE genius lines, the Demon (docs/genius-lines.md, "The Demon"): a prince in exile, the
soul of one who will not be told. Thirty-one small horned people on the people's rig.

    python tools/blender/genius_lines.py demon
    python tools/blender/genius_lines.py demon demon-princeling demon-exile
    python tools/blender/lines_demon.py gifts        # what it gives a hybrid: its horns, its wings
    python tools/blender/lines_demon.py body         # the body its forms borrow their clips from

It is built on the small people's kit (lines_people.Person and its slots), which this file
loads when it first builds and does not change. What the Demon has that they have not is here
and in demon_dress.py:

    a goat's legs    the person's own thigh, shin and foot, bent to a goat's: the hock is its
                     heel, it stands on its toes, the hoof is the toe (`build.hock`, 0 to 1)
    its face         eyes of the field with a goat's level pupil, that blink; lids, brows and a
                     mouth that say which Path it is on (`eyes`, `brow`, `mouth`, `face`, `hair`)
    horns            its crown and its outline: a different pair at every form (`horns`)
    wings of skin    in its Path's colour, worn as that Path wears them: a cloak, a collar, the
                     tails of a coat, never grown (`wings`); they mantle, or beat
    a tail           that sways or wags (`tail`)
    pieces that move riding any bone, not the chest alone (Demon.rider)

A slot holds a style, [style, size], [style, size, word], or a list of those, as the small
people's do; a style the Demon has not is looked for among theirs.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE  # noqa: E402

ROOT = kit.ROOT
OUT = os.path.join(ROOT, "game", "assets", "genius", "forms")
SILHOUETTE = "daemon-prince"

GL = None           # genius_lines, whichever way it was started (set in register)
LP = None           # lines_people, loaded when the first form is built (people())
Demon = None        # the Person the Demon is (made when lines_people is loaded)

# The Demon's own colours: none of them its partner's coat, so they stay as they are whatever
# coat the form wears, and a form in a shifted coat still has something that stands off it.
# (The three roles of the coat are hide_demon, cloth_linen and cloth_coat: data/genius-looks.json.)
OWN = {
    "hide_demon": ((0.08, 0.14, 0.1), 0.6, 0.0), "cloth_linen": ((0.48, 0.44, 0.28), 0.9, 0.0), "cloth_coat": ((0.03, 0.05, 0.045), 0.85, 0.0),
    "fur_sable": ((0.1, 0.07, 0.05), 0.95, 0.0), "fur_ermine": ((0.6, 0.57, 0.48), 0.9, 0.0), "cloth_sable": ((0.028, 0.026, 0.036), 0.85, 0.0),
    "cloth_white": ((0.62, 0.6, 0.53), 0.8, 0.0), "horn_demon": ((0.26, 0.17, 0.085), 0.4, 0.0), "horn_hoof": ((0.035, 0.03, 0.03), 0.35, 0.0),
    "brass_gilt": ((0.72, 0.5, 0.15), 0.3, 0.85), "brass_crown": ((0.6, 0.42, 0.15), 0.35, 0.85), "wood_door": ((0.2, 0.12, 0.06), 0.8, 0.0),
    "wood_yoke": ((0.3, 0.2, 0.11), 0.8, 0.0), "stone_dust": ((0.4, 0.41, 0.44), 0.95, 0.0), "wood_ebony": ((0.05, 0.042, 0.05), 0.6, 0.0), "smoke_pale": ((0.16, 0.15, 0.2), 1.0, 0.0), "hide_shadow": ((0.03, 0.028, 0.035), 0.8, 0.0),
    "leaf_vine": ((0.12, 0.22, 0.1), 0.8, 0.0), "petal_rose": ((0.5, 0.12, 0.16), 0.7, 0.0), "cloth_velvet": ((0.07, 0.03, 0.05), 0.9, 0.0),
    "mask_domino": ((0.02, 0.02, 0.025), 0.5, 0.0),
}

# how it stands at each stage: a child with a child's head at the Starter, a grown figure at
# the Final (grounded proportions: a small adult, not a doll). hock: how far its legs are a goat's.
STAGE = [dict(age=0.2, head=1.82, legs=0.74, arms=0.96, limbs=1.22, hands=1.2, feet=1.0, hock=0.85),
         dict(age=0.3, head=1.5, legs=0.86, arms=1.0, limbs=1.1, hands=1.1, hock=0.95),
         dict(age=0.4, head=1.3, legs=0.94, arms=1.02, hock=1.0, faces=0.9),
         dict(age=0.5, head=1.14, legs=1.0, arms=1.04, hock=1.0, faces=0.82)]
FACE = {"ear-shape-pointed": 1.0, "ear-scale": 0.9, "ear-wing": 0.7, "cheek-bones": 0.8, "cheek-volume": -0.5, "nose-hump": 0.5, "nose-scale-vert": 0.3,
        "nose-point": -0.4, "chin-prominent": 0.5, "chin-triangle": 0.6, "head-invertedtriangular": 0.5, "eye-corner2": 0.6, "head-fat": -0.4,
        "forehead-scale-vert": 0.3}
# a build's plain words that are more than one of MakeHuman's details
MUSCLE = {"torso-muscle-pectoral": 0.9, "torso-muscle-dorsi": 0.8, "upperarm-muscle": 1.0, "upperarm-shoulder-muscle": 1.0, "lowerarm-muscle": 0.8,
          "upperleg-muscle": 0.7, "torso-vshape": 0.6, "stomach-tone": 0.6, "measure-neck-circ": 0.5}

SLOTS = {}          # slot -> {style: fn(P, size, word)}: the Demon's own; the small people's after
ORDER = ("legs", "skin", "wear", "arms", "eyes", "brow", "mouth", "face", "hair", "horns", "crown", "wings", "tail", "back", "chest", "belt", "right",
         "left", "around")
DEFAULTS = {"eyes": "lit", "legs": "bare"}


def log(*a):
    print("[lines_demon]", *a)


def slot(name, *styles):
    """A style of a slot: fn(P, size, word); P._style is the style it was called by."""
    def deco(fn):
        for st in styles:
            SLOTS.setdefault(name, {})[st] = fn
        return fn
    return deco


# ======================================================================================
# Geometry the kit has not got
# ======================================================================================

def spline(points, per=3):
    """A smooth curve through the points (Catmull-Rom), `per` steps between each two."""
    pts = [V(p) for p in points]
    if len(pts) < 3 or per < 2:
        return pts
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        for j in range(per):
            t = j / per
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def plate(points, thick=0.014, normal=None):
    """A flat panel through the points (a wing's skin between two fingers, a door's leaf): a
    closed solid, so that it is seen from both sides."""
    pts = [V(p) for p in points]
    n = V(normal) if normal is not None else (pts[1] - pts[0]).cross(pts[-1] - pts[0])
    n = n.normalized() * (thick / 2.0)
    m = len(pts)
    verts = [p + n for p in pts] + [p - n for p in pts]
    faces = [tuple(range(m)), tuple(range(2 * m - 1, m - 1, -1))]
    for i in range(m):
        j = (i + 1) % m
        faces.append((i, i + m, j + m, j))
    return verts, faces


def hoop(c, rx, ry, r, u=X, v=Y, n=12, sides=4, a0=0.0, a1=2 * math.pi):
    """A ring (or part of one, a0 to a1) of round section about c."""
    whole = abs(a1 - a0 - 2 * math.pi) < 1e-6
    pts = [V(c) + V(u) * (math.cos(a0 + (a1 - a0) * i / n) * rx) + V(v) * (math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]
    return g.tube(pts, [r] * len(pts), n=sides, caps=not whole)


def disc(c, r, normal=Y, thick=0.02, n=10):
    nrm = V(normal).normalized()
    u = nrm.cross(Z if abs(nrm.dot(Z)) < 0.9 else X).normalized()
    w = nrm.cross(u)
    c = V(c)
    return g.loft([g.ring(c - nrm * thick / 2, r, r, n=n, u=u, v=w), g.ring(c + nrm * thick / 2, r, r, n=n, u=u, v=w)])


def drape(c, radii, zs, a0, a1, thick=0.03, n=10, hem=None, trail=0.0):
    """A cloth hanging round part of a body. radii(t, a) gives (rx, ry) at t from 0 (its top)
    to 1 (its hem) and angle a; it reaches from angle a0 to a1, measured from the back (+Y)
    toward the left; hem(a) drops its edge; trail carries the hem back."""
    c = V(c)
    rings = []
    m = len(zs)
    for i, z in enumerate(zs):
        t = i / max(1, m - 1)
        angles = [a0 + (a1 - a0) * k / (n - 1) for k in range(n)]
        dz = [(hem(a) * t if hem else 0.0) for a in angles]
        back = trail * t * t
        outer, inner = [], []
        for a, d in zip(angles, dz):
            rx, ry = radii(t, a)
            outer.append(Vector((c.x + rx * math.sin(a), c.y + ry * math.cos(a) + back * max(0.0, math.cos(a)), z + d)))
            inner.append(Vector((c.x + (rx - thick) * math.sin(a), c.y + (ry - thick) * math.cos(a) + back * max(0.0, math.cos(a)), z + d)))
        rings.append(outer + inner[::-1])
    return g.loft(rings, caps=True)


def noise(v, f=7.0):
    return (np.sin(v[:, 0] * f * 1.3 + np.sin(v[:, 2] * f) * 1.7) + np.sin(v[:, 1] * f * 1.7 + np.sin(v[:, 0] * f * 0.8) * 1.3) + np.sin(v[:, 2] * f * 1.1 + np.sin(v[:, 1] * f * 1.2) * 1.9)) / 3.0


def step(a, b, t):
    """0 at a, 1 at b, smooth between (arrays)."""
    u = np.clip((t - a) / (b - a), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


# ======================================================================================
# The body: a small person with a goat's legs
# ======================================================================================

THIGH, SHIN, CANNON = 0.56, -0.66, -1.12      # how each part of the leg lies, in radians forward of straight down (the foot: of level)
CANNON_LONG = 0.85                            # how much longer the foot is, from the ankle to the ball: it is the cannon bone now


def goat_legs(h, k, body_verts):
    """A goat's hind legs, made of the person's own and nothing else: the thigh brought
    forward, the shin back, and the foot stood on its toes and drawn out long, so that the heel
    is the hock and the toe the hoof. The skin and the joints move together, so the rig's hip,
    knee, ankle and toe are still where the leg bends. k: how far (0 a person's, 1 a goat's)."""
    if k <= 0.0:
        return
    base, v = h.base, h.v
    x, z = v[:, 0].copy(), v[:, 2].copy()
    out = v.copy()

    def turn(P, ang):          # about a line through P across the body; forward is positive
        dy, dz = out[:, 1] - P[1], out[:, 2] - P[2]
        c, s = np.cos(ang), np.sin(ang)
        out[:, 1] = P[1] + dy * c + dz * s
        out[:, 2] = P[2] - dy * s + dz * c
    for sd, sg in (("l", 1.0), ("r", -1.0)):
        H, K, A = (base.joint(v, "joint-%s-%s" % (sd, n)) for n in ("upper-leg", "knee", "ankle"))
        side = step(0.0, 0.05, x * sg)                      # this leg, soft across the middle
        w_h = step(H[2] + 0.05, H[2] - 0.2, z) * side
        w_k = step(K[2] + 0.12, K[2] - 0.12, z) * side
        w_a = step(A[2] + 0.08, A[2] - 0.03, z) * side
        dy = out[:, 1] - A[1]                               # the cannon: the foot drawn out forward of the ankle
        out[:, 1] = A[1] + dy * np.where(dy < 0, 1.0 + CANNON_LONG * k * w_a, 1.0)
        out[:, 0] = A[0] + (out[:, 0] - A[0]) * (1.0 - 0.18 * k * w_a * step(0.0, -0.12, dy))      # and slimmer toward the toe
        turn(A, (CANNON - SHIN) * k * w_a)
        turn(K, (SHIN - THIGH) * k * w_k)
        turn(H, THIGH * k * w_h)
    out[:, 2] -= out[:body_verts, 2].min()
    h.v = out


def _demon_class(lp):
    class DemonPerson(lp.Person):
        """A form of the Demon being built: a small person (lines_people.Person) with a goat's
        legs, and pieces that move riding any bone."""

        def __init__(self, form_id, level, spec, roles):
            build = dict(spec.get("build", {}))
            hock = float(build.pop("hock", STAGE[level - 1].get("hock", 1.0)))
            m = float(build.pop("muscle", 0.0))
            for name, w in MUSCLE.items():
                if m:
                    build.setdefault(name, w * m)
            real = lp._reshape

            def shaped(h, ex, body_verts):
                real(h, ex, body_verts)
                goat_legs(h, hock, body_verts)
            lp._reshape = shaped
            try:
                lp.Person.__init__(self, "demon", form_id, level, dict(spec, build=build), roles)
            finally:
                lp._reshape = real
            self.hock = hock
            self.riders = []            # [(object, where it turns about, the bone it rides)]
            self.leg = self.hb.is_leg
            self.dom = np.array([d or "" for d in self.hb.dom], dtype=object)
            J = self.J
            self.hockz, self.toe = J["foot.l"].z, J["toes.l"]

        # --- pieces that move ----------------------------------------------------------

        def rider(self, kind, what, items, pivot, bone, side="", n=None, smooth=True):
            """A piece the game moves by its name (docs/genius-lines.md, "What moves"), riding a
            bone: <kind>_<what>[_l|_r][_<n>], turning about `pivot`. items: [(geometry,
            material or its name)] at the human's own size, in the rest pose. (Not a chain:
            the game takes each piece that rides a bone in as a bone of its own and moves the
            piece alone, so one piece cannot carry the next.)"""
            name = "%s_%s%s%s" % (kind, what, "_" + side if side else "", "_%d" % n if n is not None else "")
            made = [(geo, m if not isinstance(m, str) else self.material(m)) for geo, m in items if geo and geo[0]]
            ob = g.pieces(name, made, smooth=smooth)
            self.riders.append((ob, Vector(pivot), bone))
            return ob

        def side_x(self, z):
            """How far out the trunk's side is at a height."""
            return self.ring(z)[0]

        # --- finishing: as Person.finish, with every rider on its own bone -------------------

        def finish(self, path, clips=False):
            """clips: keep the rig's three clips in the file (the body its forms borrow them from)."""
            p, hb, hu = self.p, self.hb, self.p.hu
            arm, s = p.arm, p.s
            body = hu.mesh_object("Body", self.v, hb.faces, self.mats, face_material=[int(i) for i in self.fmat])
            hb.weight_body(body)
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
            dec.ratio = min(1.0, lp.TRIS[self.level - 1] * float(self.b.get("faces", 1.0)) / tris)
            dec.vertex_group = "_thin"
            dec.vertex_group_factor = 1.0
            bpy.ops.object.modifier_apply(modifier="Decimate")
            body.vertex_groups.remove(body.vertex_groups["_thin"])
            body.select_set(False)
            made = []
            for name, geo, material, bone, smooth in self.pieces:
                ob = g.to_object(name, geo, material, material.name.startswith(lp.SOFT) if smooth is None else smooth)
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
            # what the small people's own styles made as wings rides the chest, as theirs do
            riders = list(self.riders) + [(ob, root, "chest") for ob, root in self.wings]
            for ob, pivot, bone in riders:
                ob.parent = arm
                ob.parent_type = "BONE"
                ob.parent_bone = bone
                bpy.context.view_layer.update()
                ob.matrix_world = Matrix.Identity(4)
            r = p.r
            r.skinned, r.attached = [body], [ob for ob, _, _ in riders]
            r.uniform(s)
            bpy.context.view_layer.update()
            for ob, pivot, bone in riders:       # each piece's own origin where it turns, the shape left where it is
                kit.set_origin(ob, pivot * s)
            for a in list(bpy.data.actions):
                if not clips or a.name not in kit.KEEP_CLIPS:
                    bpy.data.actions.remove(a)
            if clips and arm.animation_data:
                for tr in list(arm.animation_data.nla_tracks):
                    if tr.name not in kit.KEEP_CLIPS:
                        arm.animation_data.nla_tracks.remove(tr)
            socks = {name: kit.bone_socket(arm, name, bone, Vector(at) * s, rot) for name, (bone, at, rot) in p.common_sockets().items()}
            socks["ref_top"] = kit.free_socket("ref_top", (0, 0, self.crown * s))
            arm.data.pose_position = "POSE" if clips else "REST"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            bpy.ops.object.select_all(action="DESELECT")
            for o in [arm, body] + [ob for ob, _, _ in riders] + list(socks.values()):
                o.select_set(True)
            bpy.context.view_layer.objects.active = arm
            # no clips: a form moves by its base body's, which the game fits to its proportions
            if clips:
                bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                          export_animations=True, export_animation_mode="ACTIONS", export_skins=True, export_texcoords=False)
            else:
                bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                                          export_animations=False, export_skins=True, export_texcoords=False)
            tris = sum(len(poly.vertices) - 2 for poly in body.data.polygons) + sum(len(poly.vertices) - 2 for ob, _, _ in riders for poly in ob.data.polygons)
            log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB, %d that move" % (tris, os.path.getsize(path) // 1024, len(riders)))
    return DemonPerson


def people():
    """The small people's kit, loaded when it is first needed (after every family has been
    registered, so that its colours stay its own family's), and the Demon's tables put where
    its Person looks for them."""
    global LP, Demon
    if LP is None:
        import lines_people as lp
        LP = lp
        lp.STAGE["demon"] = STAGE
        lp.FACE["demon"] = FACE
        lp.SKIN["demon"] = "main"
        Demon = _demon_class(lp)
        import demon_dress  # noqa: F401   what it wears and carries
    return LP


# ======================================================================================
# The legs: fur, and hooves
# ======================================================================================

def _hoof(P, sd, sg, material):
    """A cloven hoof over the toes of one foot: two claws side by side, the wall sloping
    forward, the sole on the ground."""
    toe = (P.dom == "ball_" + sd)
    if not toe.any():
        return
    tv = P.v0[toe]
    x0, x1, y0, y1 = float(tv[:, 0].min()), float(tv[:, 0].max()), float(tv[:, 1].min()), float(tv[:, 1].max())
    zt = float(tv[:, 2].max())
    cx, w = (x0 + x1) / 2, max(0.09, (x1 - x0)) * 1.08
    top = min(zt, 0.24) * 0.92 + 0.02
    # the toes themselves are drawn in, to lie inside the horn
    c = np.array([cx, (y0 + y1) / 2 + 0.02, top * 0.6])
    P.v[toe] = c + (P.v[toe] - c) * np.array([0.6, 0.75, 0.8])
    geo = None
    for half in (1, -1):
        hx = cx + half * w * 0.27
        rings = []
        for t, (rx, ry, fwd) in zip((1.0, 0.45, 0.0), ((0.2, 0.36, 0.0), (0.24, 0.44, -0.08), (0.27, 0.5, -0.16))):
            cy = (y0 + y1) / 2 + 0.03 + fwd * (y1 - y0) * 1.2
            ring = g.ring((hx + half * (1 - t) * w * 0.04, cy, top * t), w * rx, max(0.07, (y1 - y0)) * ry * 1.25, n=7, phase=0.3)
            rings.append(ring)
        geo = g.merge(geo, g.loft(rings))
    P.add("hoof_" + sd, geo, material, "toes." + sd, smooth=False)
    # the coronet: a band where the horn meets the leg
    P.add("coronet_" + sd, hoop((cx, (y0 + y1) / 2 + 0.035, top), w * 0.5, max(0.07, (y1 - y0)) * 0.5, 0.022, n=8, sides=4), mat("fur_sable"), "toes." + sd, smooth=True)


def _leg_masks(P):
    z = P.v0[:, 2]
    low = P.leg & (z < P.hipz - 0.05)
    return low, z


@slot("legs", "bare", "shag", "gaiters", "wraps", "smoke")
def legs(P, size, word):
    """Its legs: bare hide, a goat's shag from the thigh to the hock, a rider's gaiters on the
    cannon, a walker's wraps, or going to smoke below the knee. The hooves: dark horn, or gilt."""
    style = P._style
    low, z = _leg_masks(P)
    fur = mat("fur_sable")
    if style == "shag":
        top = P.kneez + (P.hipz - P.kneez) * 0.62 * min(1.2, size)
        m = low & (z < top) & (z > P.hockz - 0.02)
        P.wear(m, fur, 0.022 * size)
        P.v[m] += P.n[m] * (noise(P.v0[m], 21.0) * 0.02 * size)[:, None]
        for s, tag in ((1, "l"), (-1, "r")):
            K, A = P.J["lowerleg." + tag], P.J["foot." + tag]
            tufts = None
            for i in range(4):          # down the back of the shin, each longer than the one above
                t = 0.2 + 0.24 * i
                b0 = K.lerp(A, t) + Vector((0, 0.07 * P.b.get("limbs", 1.0), 0))
                tufts = g.merge(tufts, g.blade(b0, b0 + Vector((s * 0.015 * (i % 2), 0.13 * size, -0.2 * size)), 0.15 * size, normal=(0, 1, 0.5), belly=0.4))
            P.add("shag_" + tag, tufts, fur, "lowerleg." + tag, smooth=True)
            # the thigh's own: a skirt of it over the knee
            T = P.J["upperleg." + tag]
            th = None
            for i in range(3):
                b0 = T.lerp(K, 0.55 + 0.16 * i) + Vector((s * 0.1 * P.b.get("limbs", 1.0), 0.02, 0))
                th = g.merge(th, g.blade(b0, b0 + Vector((s * 0.1 * size, 0.06, -0.2 * size)), 0.16 * size, normal=(s, 0, 0.4), belly=0.4))
            P.add("shag_thigh_" + tag, th, fur, "upperleg." + tag, smooth=True)
    elif style == "gaiters":
        m = low & (z < P.hockz + 0.03) & ~np.isin(P.dom, ("ball_l", "ball_r"))
        P.wear(m, mat("cloth_sable"), 0.018)
        for s, tag in ((1, "l"), (-1, "r")):
            A, B = P.J["foot." + tag], P.J["toes." + tag]
            studs = None
            for i in range(3):
                q = A.lerp(B, 0.25 + 0.25 * i)
                studs = g.merge(studs, g.ico(q + Vector((s * 0.085, 0.0, 0.0)), 0.022, sub=0))
            P.add("gaiter_studs_" + tag, studs, mat("brass_crown"), "foot." + tag, smooth=False)
    elif style == "wraps":
        m = low & (z < P.hockz + 0.2) & (z > P.hockz - 0.25) & ~np.isin(P.dom, ("ball_l", "ball_r"))
        P.wear(m, P.material("under"), 0.016)
    elif style == "smoke":
        m = low & (z < P.kneez - 0.02)
        P.paint(m, mat("smoke_pale"))
        P.v[m] += P.n[m] * (noise(P.v0[m], 17.0) * 0.03)[:, None]
    for sd in ("l", "r"):
        if style != "smoke":
            _hoof(P, sd, 1.0 if sd == "l" else -1.0, mat("brass_gilt") if word == "gilt" else mat("horn_hoof"))
    # the fetlock: a tuft over the back of each hoof
    if style in ("shag", "bare"):
        for s, tag in ((1, "l"), (-1, "r")):
            B = P.J["toes." + tag]
            b0 = Vector((B.x, B.y + 0.07, B.z + 0.05))
            P.add("fetlock_" + tag, g.blade(b0, b0 + Vector((0, 0.1, -0.1)), 0.11, normal=(0, 1, 0.6), belly=0.4), fur, "foot." + tag, smooth=True)


# ======================================================================================
# The face: eyes that blink, lids, brows, a mouth
# ======================================================================================

# how far the upper lid comes down over the eye (0 none, 1 shut), and how far the lower comes up
LIDS = {"lit": (0.16, 0.0), "big": (0.0, 0.0), "wide": (0.0, 0.0), "hooded": (0.4, 0.0), "narrow": (0.3, 0.24), "far": (0.12, 0.0)}
EYE_SIZE = {"lit": 1.6, "big": 1.8, "wide": 1.85, "hooded": 1.6, "narrow": 1.5, "far": 1.65}
# each brow, for the character's left: (how high its inner end, its outer end, how heavy); the right the same unless given
BROWS = {"level": ((0.0, 0.02, 1.0),), "proud": ((0.06, 0.26, 0.9),), "wry": ((0.12, 0.42, 0.9), (-0.02, 0.0, 1.0)), "fierce": ((-0.2, 0.22, 1.35),),
         "glad": ((0.2, 0.3, 0.8),), "calm": ((0.14, 0.06, 0.8),), "sad": ((0.3, 0.0, 0.9),)}


def eye_at(P, s, k):
    return Vector((s * P.eye.x, P.eye.y - P.eye_r * 0.35 * (k - 1.0), P.eye.z))


@slot("eyes", "lit", "big", "wide", "hooded", "narrow", "far")
def eyes(P, size, word):
    """Eyes of the field with a goat's level pupil, in dark sockets. The eye is a piece of its
    own, so it blinks; the lids are the face's, and say how it looks at you."""
    style = P._style
    k = size * EYE_SIZE[style]
    r = P.eye_r * k
    up, lowl = LIDS[style]
    P.eye_k, P.eye_style = k, style
    lit = field("eyes", 3.6 if style != "far" else 4.2)
    for s, tag in ((1, "l"), (-1, "r")):
        c = eye_at(P, s, k)
        ball = g.ico(c + Vector((0, -r * 0.66, 0)), r, sub=2, scale=(1.12, 0.6, 0.88))
        bar = g.box(c + Vector((0, -r * 1.2, 0)), (r * 0.96, r * 0.14, r * 0.2))
        P.rider("blink", "eye", [(ball, lit), (bar, mat("void"))], c, "head", side=tag)
        if getattr(P, "headless", False):       # eyes in a fire: no sockets, no lids
            continue
        P.add("eye_socket_" + tag, g.ico(c + Vector((0, -r * 0.3, 0)), r * 1.1, sub=1, scale=(1.16, 0.5, 0.92)), mat("void"), "head", smooth=True)
        if up > 0.0:        # the upper lid, of its own hide: a cap over the top of the eye
            lid = g.ico(c + Vector((0, -r * 0.62, r * (1.1 - 0.9 * up))), r * 1.1, sub=1, scale=(1.26, 0.78, 0.46))
            P.add("lid_" + tag, lid, P.skin, "head", smooth=True)
        if lowl > 0.0:
            lid = g.ico(c + Vector((0, -r * 0.6, -r * (1.1 - 0.8 * lowl))), r * 1.06, sub=1, scale=(1.2, 0.74, 0.4))
            P.add("lid_low_" + tag, lid, P.skin, "head", smooth=True)


@slot("brow", "level", "proud", "wry", "fierce", "glad", "calm", "sad")
def brow(P, size, word):
    """Its brows: what it thinks of what it is looking at."""
    k = getattr(P, "eye_k", 1.3)
    r = P.eye_r * k
    spec = BROWS[P._style]
    for i, (s, tag) in enumerate(((1, "l"), (-1, "r"))):
        inner, outer, heavy = spec[min(i, len(spec) - 1)]
        c = eye_at(P, s, k)
        z0 = c.z + r * (1.2 + inner * 2.0)
        z1 = c.z + r * (1.14 + outer * 2.0)
        pts = [Vector((s * (abs(c.x) - r * 1.25), c.y - r * 1.3, z0)), Vector((s * abs(c.x), c.y - r * 1.42, (z0 + z1) / 2 + r * 0.16)),
               Vector((s * (abs(c.x) + r * 1.45), c.y - r * 0.8, z1))]
        P.add("brow_" + tag, g.tube(spline(pts, 3), [r * 0.2 * heavy * size, r * 0.24 * heavy * size, r * 0.23 * heavy * size, r * 0.2 * heavy * size,
                                                     r * 0.16 * heavy * size, r * 0.11 * heavy * size, r * 0.04], n=5, flat=0.7), mat("fur_sable"), "head", smooth=True)


def mouth_at(P):
    z = float(P.mouth[2]) - 0.075 * P.hr
    return Vector((0, P.front(z) - 0.004, z))


@slot("mouth", "set", "smile", "grin", "tusks", "fangs", "open", "grin-tusks")
def mouth(P, size, word):
    """Its mouth: set, smiling on one side, grinning, tusked from below, fanged from above, open."""
    style, hr = P._style, P.hr
    c = mouth_at(P)
    w = 0.42 * hr * size
    dark, tooth = mat("void"), mat("bone")

    def lip(lift_l, lift_r, thick=0.045):
        pts = [c + Vector((-w, 0.05 * hr, lift_r * hr)), c + Vector((-w * 0.5, -0.012 * hr, lift_r * hr * 0.25)), c + Vector((0, -0.03 * hr, 0)),
               c + Vector((w * 0.5, -0.012 * hr, lift_l * hr * 0.25)), c + Vector((w, 0.05 * hr, lift_l * hr))]
        P.add("mouth_line", g.tube(spline(pts, 2), [thick * hr * 0.5] + [thick * hr] * 7 + [thick * hr * 0.5], n=4, flat=0.6), dark, "head", smooth=True)
    if style == "set":
        lip(-0.03, -0.03)
    elif style == "smile":
        lip(0.16, 0.03)
        P.add("fang_show", g.cone(c + Vector((w * 0.62, -0.03 * hr, 0.02 * hr)), c + Vector((w * 0.6, -0.04 * hr, -0.1 * hr)), 0.03 * hr, n=4), tooth, "head")
    elif style in ("grin", "grin-tusks", "open"):
        tall = {"grin": 0.16, "grin-tusks": 0.16, "open": 0.34}[style] * size
        wide = 1.25 if style != "open" else 0.95
        P.add("mouth", g.ico(c + Vector((0, 0.03 * hr, -tall * hr * 0.3)), hr, sub=1, scale=(w / hr * wide, 0.16, tall)), mat("maw"), "head", smooth=True)
        teeth = None
        n = 6
        for row, zt in ((1, 0.0), (-1, -tall * hr * 0.62)):
            for i in range(n):
                t = -1.0 + 2.0 * (i + 0.5) / n
                teeth = g.merge(teeth, g.box(c + Vector((t * w * wide * 0.8, -0.05 * hr * (1.0 - 0.7 * t * t), zt - row * 0.035 * hr)),
                                             (w * wide * 0.22, 0.04 * hr, 0.08 * hr)))
        P.add("teeth", teeth, tooth, "head")
    else:
        lip(-0.05, -0.05, 0.05)
    if style in ("tusks", "grin-tusks"):        # two from below, standing up over the lip
        geo = None
        for s in (1, -1):
            b0 = c + Vector((s * w * 0.72, -0.01 * hr, -0.05 * hr))
            geo = g.merge(geo, g.tube([b0, b0 + Vector((s * 0.03 * hr, -0.05 * hr, 0.12 * hr * size)), b0 + Vector((s * 0.02 * hr, -0.03 * hr, 0.27 * hr * size))],
                                      [0.055 * hr, 0.045 * hr, 0.006], n=5))
        P.add("tusks", geo, tooth, "head")
    if style == "fangs":
        geo = None
        for s in (1, -1):
            b0 = c + Vector((s * w * 0.5, -0.03 * hr, 0.0))
            geo = g.merge(geo, g.cone(b0, b0 + Vector((0, -0.01 * hr, -0.2 * hr * size)), 0.04 * hr, n=4))
        P.add("fangs", geo, tooth, "head")


def scalp(P, low=0.0):
    """The skull above the hairline: high over the brow, down behind the ears to the nape."""
    v, e, hr = P.v0, P.eye, P.hr
    y, z = v[:, 1], v[:, 2]
    line = e.z + (0.82 + low) * hr - 0.9 * np.clip(y - (P.hy0 + 0.2 * hr), 0.0, None)
    line = np.maximum(line, e.z + 0.2 * hr)
    line = np.where(y > P.hcy + 0.3 * hr, P.chin + 0.36 * P.hh, line)
    return P.hb.is_head & ~P.ears & (z > line)


@slot("hair", "slick", "long", "mane")
def hair(P, size, word):
    """Hair: oiled flat with a peak (slick), worn long down the nape, or a mane like a bull's."""
    style, hr = P._style, P.hr
    fur = mat("fur_sable")
    P.wear(scalp(P, 0.12 if style == "slick" else 0.0), fur, 0.02 if style == "slick" else 0.035)
    top, cy = P.crown, P.hcy
    if style == "slick":         # a widow's peak, and the back of it to the collar
        P.add("hair_peak", g.blade((0, P.hy0 + 0.22 * hr, top - 0.3 * hr), (0, P.hy0 - 0.02 * hr, top - 0.78 * hr), 0.5 * hr, normal=(0, -1, 0.5), belly=0.3), fur, "head", smooth=True)
        P.add("hair_back", g.blade((0, P.hy1 - 0.05 * hr, top - 0.9 * hr), (0, P.hy1 + 0.12 * hr, P.chin - 0.1 * hr * size), 1.1 * hr, normal=(0, 1, 0.2), belly=0.35), fur, "head", smooth=True)
        return
    geo = None
    if style == "long":
        for i, dx in enumerate((-0.62, -0.32, 0.0, 0.32, 0.62)):
            b0 = Vector((dx * hr, P.hy1 - 0.1 * hr, top - (0.55 + 0.25 * abs(dx)) * hr))
            pts = [b0, b0 + Vector((dx * 0.1 * hr, 0.34 * hr, -0.6 * hr)), b0 + Vector((dx * 0.25 * hr, 0.3 * hr, -(1.5 + 0.3 * (i % 2)) * hr * size))]
            geo = g.merge(geo, g.tongue(spline(pts, 2), [0.42 * hr, 0.46 * hr, 0.42 * hr, 0.3 * hr, 0.08 * hr], thick=0.4, normal=Y))
        P.add("hair_long", geo, fur, "head", smooth=True)
    else:                        # a mane: a crest from the brow over the crown and down between the shoulders
        cz, rz, ry = top - 0.5 * P.hh, 0.5 * P.hh, (P.hy1 - P.hy0) / 2
        for i in range(9):
            t = i / 8.0
            a = -0.6 + 3.0 * t                               # from over the brow, across the crown, down the nape
            b0 = Vector((0, cy + math.sin(a) * ry * 0.96, cz + math.cos(a) * rz * 0.98)) if a < 2.0 else Vector((0, cy + ry * 0.8, cz + math.cos(2.0) * rz - (a - 2.0) * rz * 1.3))
            for dx in (-0.3, 0.0, 0.3):
                tip = b0 + Vector((dx * hr * 1.6, 0.42 * hr * size, (0.34 - 0.5 * t) * hr * size))
                geo = g.merge(geo, g.blade(b0 + Vector((dx * hr, 0, -abs(dx) * 0.3 * hr)), tip, 0.4 * hr * size, normal=(dx, -0.3, 1), belly=0.4))
        P.add("mane", geo, fur, "head", smooth=True)


@slot("face", "goatee", "half-mask", "nose-ring", "back-face", "back-mouth")
def face(P, size, word):
    """What else its face has: a small pointed beard, a half-mask, a ring in its nose; and at
    the back of its head a second face, or a second mouth."""
    style, hr = P._style, P.hr
    if style == "goatee":
        c = Vector((0, P.front(P.chin + 0.06 * P.hh) - 0.01, P.chin + 0.05 * P.hh))
        P.add("goatee", g.tongue([c, c + Vector((0, -0.05 * hr, -0.2 * hr * size)), c + Vector((0, -0.12 * hr, -0.46 * hr * size))], [0.3 * hr, 0.22 * hr, 0.02 * hr], thick=0.7, normal=Y),
              mat("fur_sable"), "head", smooth=True)
    elif style == "half-mask":
        e = P.eye
        k = getattr(P, "eye_k", 1.3)
        band = P.headv & ~P.ears & (np.abs(P.v0[:, 2] - e.z) < P.eye_r * k * 1.9) & (P.v0[:, 1] < P.hcy)
        P.wear(band, mat("mask_domino"), 0.012)
        for s in (1, -1):         # its corners, turned up
            b0 = Vector((s * (e.x + P.eye_r * k * 1.7), e.y + 0.1 * hr, e.z))
            P.add("mask_wing_%d" % s, g.blade(b0, b0 + Vector((s * 0.34 * hr, 0.16 * hr, 0.3 * hr)), 0.3 * hr, normal=(s * 0.3, -1, 0), belly=0.4, thick=0.012), mat("mask_domino"), "head")
    elif style == "nose-ring":
        z = P.mouth.z + 0.16 * hr
        c = Vector((0, P.front(z + 0.05 * hr) - 0.02 * hr, z))
        P.add("nose_ring", hoop(c, 0.11 * hr * size, 0.13 * hr * size, 0.022 * hr, u=X, v=Z, n=10, sides=4, a0=-math.pi * 0.25, a1=math.pi * 1.25), mat("brass_crown"), "head")
    else:                        # at the back of its head
        e = P.eye
        y = P.hy1 - 0.04 * hr
        r = P.eye_r * 1.2
        if style == "back-face":
            for s, tag in ((1, "l"), (-1, "r")):
                c = Vector((s * e.x * 0.9, y - 0.12 * hr * abs(e.x) / hr, e.z + 0.1 * hr))
                P.add("back_socket_" + tag, g.ico(c, r * 1.15, sub=1, scale=(1.15, 0.5, 0.9)), mat("void"), "head", smooth=True)
                P.rider("blink", "backeye", [(g.ico(c + Vector((0, r * 0.2, 0)), r, sub=1, scale=(1.1, 0.55, 0.8)), field("eyes", 3.0)),
                                             (g.box(c + Vector((0, r * 0.62, 0)), (r * 1.1, r * 0.14, r * 0.28)), mat("void"))], c, "head", side=tag)
                bz = c.z + r * 1.25
                P.add("back_brow_" + tag, g.tube([Vector((s * (abs(c.x) - r * 1.2), y + 0.03 * hr, bz + r * 0.5)), Vector((s * (abs(c.x) + r * 1.3), y - 0.1 * hr, bz))], [r * 0.3, r * 0.14], n=4), mat("fur_sable"), "head", smooth=True)
            mz = P.mouth.z
            P.add("back_mouth", g.tube([Vector((-0.3 * hr, y + 0.02 * hr, mz + 0.1 * hr)), Vector((0, y + 0.08 * hr, mz)), Vector((0.3 * hr, y + 0.02 * hr, mz + 0.14 * hr))], [0.03 * hr, 0.045 * hr, 0.03 * hr], n=4), mat("void"), "head", smooth=True)
        else:                    # a wide mouth of its own, talking
            mz = P.mouth.z + 0.1 * hr
            c = Vector((0, y + 0.02 * hr, mz))
            P.add("back_maw", g.ico(c, hr, sub=1, scale=(0.56 * size, 0.2, 0.24 * size)), mat("maw"), "head", smooth=True)
            teeth = None
            for row in (1, -1):
                for i in range(5):
                    t = -1.0 + 2.0 * (i + 0.5) / 5
                    teeth = g.merge(teeth, g.box(c + Vector((t * 0.46 * hr * size, 0.14 * hr * (1.0 - 0.6 * t * t), row * 0.13 * hr * size)), (0.15 * hr * size, 0.05 * hr, 0.1 * hr)))
            P.add("back_teeth", teeth, mat("bone"), "head")
            for s, tag in ((1, "l"), (-1, "r")):
                c2 = Vector((s * e.x * 0.9, y - 0.14 * hr, e.z + 0.14 * hr))
                P.add("back_socket_" + tag, g.ico(c2, r * 1.15, sub=1, scale=(1.15, 0.5, 0.9)), mat("void"), "head", smooth=True)
                P.rider("blink", "backeye", [(g.ico(c2 + Vector((0, r * 0.2, 0)), r, sub=1, scale=(1.1, 0.55, 0.8)), field("eyes", 3.0))], c2, "head", side=tag)


# ======================================================================================
# Horns: its crown and its outline. A different pair at every form.
# ======================================================================================

def _curl(turns, r0, r1, out, n=14, start=-0.5, fwd=1.0, lift=0.0):
    """A ram's curl about the temple, in head half-widths: from the top of the turn, back, down
    and round to the front (fwd -1: the other way), drawing out sideways as it goes."""
    pts = []
    for i in range(n + 1):
        t = i / n
        a = start + turns * 2 * math.pi * t
        r = r0 + (r1 - r0) * t
        pts.append((out * t * t + 0.06, fwd * math.sin(a) * r, math.cos(a) * r - r0 * 0.9 + lift * t))
    return pts


def _screw(turns, r, tall, n=16):
    return [(0.1 + r * math.cos(2 * math.pi * turns * i / n) * (1 - 0.5 * i / n), r * math.sin(2 * math.pi * turns * i / n) * (1 - 0.5 * i / n), tall * i / n) for i in range(n + 1)]


# style -> what stands on the left of the brow (and on the right, if it is not the same): each
# horn (where it roots: brow, temple or mid; its path in head half-widths; how thick; ridged)
HORNS = {
    "buds": [("brow", [(0, 0, 0), (0.05, 0, 0.2), (0.07, -0.02, 0.36)], 0.17, 0.0)],
    "prongs": [("brow", [(0, 0, 0), (0.12, 0.03, 0.45), (0.2, 0.0, 0.98)], 0.16, 0.0)],
    "lyre": [("brow", [(0, 0, 0), (0.38, 0.1, 0.5), (0.52, 0.26, 1.1), (0.3, 0.36, 1.7), (0.44, 0.3, 2.3)], 0.16, 0.12)],
    "spires": [("brow", [(0.1, 0, 0), (0.22, 0.05, 1.0), (0.3, 0.1, 2.3)], 0.14, 0.12)],
    "swept": [("brow", [(0, 0, 0), (0.3, 0.3, 0.46), (0.44, 0.95, 0.78), (0.4, 1.7, 0.66)], 0.15, 0.1)],
    "back": [("brow", [(0, 0, 0), (0.2, 0.42, 0.26), (0.26, 1.0, 0.3), (0.2, 1.5, 0.14)], 0.14, 0.0)],
    "antelope": [("brow", [(0, 0, 0), (0.14, 0.5, 0.7), (0.26, 1.3, 1.6), (0.34, 2.1, 2.45)], 0.14, 0.16)],
    "crescent": [("brow", [(0, 0, 0), (0.36, 0.0, 0.3), (0.44, 0.0, 0.76), (0.2, 0.0, 1.08)], 0.13, 0.0)],
    "hooks": [("brow", [(0, 0, 0), (0.2, 0.05, 0.5), (0.26, -0.3, 0.9), (0.2, -0.66, 0.76)], 0.13, 0.0)],
    "stubs": [("brow", [(0, 0, 0), (0.26, 0, 0.2), (0.42, -0.05, 0.4)], 0.24, 0.0)],
    "wide": [("brow", [(0, 0, 0), (0.7, 0, 0.14), (1.3, -0.1, 0.46), (1.55, -0.2, 1.02)], 0.18, 0.0)],
    "rapier": [("brow", [(0, 0, 0), (0.12, -0.5, 0.9), (0.2, -1.1, 2.0)], 0.1, 0.0)],
    "forward": [("brow", [(0, 0, 0), (0.42, -0.14, 0.2), (0.56, -0.6, 0.44), (0.5, -1.02, 0.62)], 0.2, 0.1)],
    "great-bull": [("brow", [(0, 0, 0), (0.9, 0, 0.1), (1.7, -0.15, 0.5), (2.0, -0.3, 1.26)], 0.21, 0.0)],
    "low": [("brow", [(0, 0, -0.06), (0.62, 0.05, -0.2), (1.22, 0, -0.22), (1.62, -0.12, 0.26)], 0.23, 0.1)],
    "ox": [("brow", [(0, 0, 0), (0.8, -0.1, 0.2), (1.5, -0.6, 0.5), (1.82, -1.22, 0.92)], 0.19, 0.0)],
    "spiral": [("brow", _screw(2.2, 0.14, 1.9), 0.12, 0.0)],
    "curled": [("temple", _curl(1.15, 0.36, 0.14, 0.34), 0.15, 0.12)],
    "ram": [("temple", _curl(1.3, 0.56, 0.22, 0.5), 0.25, 0.16)],
    "wig": [("temple", _curl(1.5, 0.5, 0.2, 0.3), 0.22, 0.0), ("temple", [(q[0] + 0.02, q[1] + 0.12, q[2] - 0.62) for q in _curl(1.3, 0.38, 0.14, 0.22)], 0.2, 0.0)],
    "stag": [("brow", [(0, 0, 0), (0.3, 0.2, 0.7), (0.56, 0.36, 1.4), (0.5, 0.3, 2.12)], 0.12, 0.0),
             ("brow", [(0.1, 0.06, 0.24), (0.2, -0.3, 0.5), (0.24, -0.5, 0.86)], 0.07, 0.0),
             ("brow", [(0.36, 0.25, 0.9), (0.74, 0.3, 1.2), (0.9, 0.3, 1.6)], 0.07, 0.0),
             ("brow", [(0.55, 0.35, 1.4), (0.8, 0.5, 1.74), (0.84, 0.56, 2.1)], 0.06, 0.0)],
}
# the pairs that are not a pair: (the left, the right)
HORNS_ODD = {
    "single": ("swept", [("brow", [(0, 0, 0), (0.08, 0.03, 0.2), (0.12, 0.05, 0.34)], 0.16, 0.0, "snapped")]),
    "broken": ([("brow", [(0, 0, 0), (0.14, 0.05, 0.3), (0.22, 0.08, 0.52)], 0.19, 0.0, "snapped")], [("brow", [(0, 0, 0), (0.1, 0.03, 0.2), (0.14, 0.05, 0.3)], 0.19, 0.0, "snapped")]),
    "both-ways": ([("temple", _curl(1.1, 0.46, 0.18, 0.4, fwd=-1.0), 0.17, 0.12)], [("temple", _curl(1.1, 0.46, 0.18, 0.4, fwd=1.0), 0.17, 0.12)]),
}


HORN_K = 1.4        # how much larger a Demon's horns are than the small people's: they are its outline


def horn(path, r0, ridged=0.0, n=6, blunt=0.04, split=0.62, snapped=False, up=None):
    """One horn along a path: (its dark length, its pale point). It tapers, and a ridged one
    is ringed as a ram's or an antelope's is."""
    m = len(path)
    radii = []
    for i in range(m):
        t = i / (m - 1)
        r = r0 * ((1 - t) ** 0.8 * (1 - blunt) + blunt) if not snapped else r0 * (1.0 - 0.3 * t)
        if ridged and 0 < i < m - 2 and i % 2:
            r *= 1 + ridged
        radii.append(r)
    if snapped:
        return g.tube(path, radii, n=n, up=up), None
    k = max(1, min(m - 2, int(round(split * (m - 1)))))
    return g.tube(path[:k + 1], radii[:k + 1], n=n, up=up), g.tube(path[k:], radii[k:], n=n, up=up)


def horn_root(P, where):
    hr = P.hr
    if where == "temple":
        return Vector((0.9 * hr, P.hcy + 0.08 * hr, P.crown - 0.55 * hr))
    if where == "mid":
        return Vector((0.0, P.hy0 + 0.34 * hr, P.crown - 0.12 * hr))
    return Vector((0.55 * hr, P.hcy - 0.12 * hr, P.crown - 0.26 * hr))


def grow_horns(P, specs, s, k, word, tag):
    """The horns of one side (s: 1 its left, -1 its right)."""
    hr = P.hr
    dark, pale = None, None
    bands = None
    for spec in specs:
        where, pts, r0, ridged = spec[:4]
        snapped = len(spec) > 4 and spec[4] == "snapped"
        root = horn_root(P, where)
        scale = k * HORN_K if where != "temple" else (0.6 + 0.4 * k) * 1.2
        path = [Vector((s * (root.x + q[0] * hr * scale), root.y + q[1] * hr * scale, root.z + q[2] * hr * scale)) for q in pts]
        path = spline(path, 2) if len(path) < 9 else path
        a, b = horn(path, r0 * hr * (0.7 + 0.3 * k) * 1.2, ridged, snapped=snapped, up=(X * s if where == "temple" else None))
        dark, pale = g.merge(dark, a), g.merge(pale, b)
        P.horn_tip = getattr(P, "horn_tip", {})
        P.horn_tip.setdefault(tag, path[-1])
        if word == "banded" or (word == "iron" and snapped):
            m = len(path)
            for f in ((0.22, 0.42) if not snapped else (0.9,)):
                i = max(1, min(m - 2, int(f * (m - 1))))
                d = (path[i + 1] - path[i - 1]).normalized()
                u = d.cross(Z if abs(d.dot(Z)) < 0.9 else X).normalized()
                rr = r0 * hr * (0.7 + 0.3 * k) * 1.2 * ((1 - i / (m - 1)) ** 0.8 if not snapped else 1.0 - 0.3 * i / (m - 1)) * 1.12
                bands = g.merge(bands, hoop(path[i], rr, rr, rr * 0.2, u=u, v=d.cross(u), n=8, sides=4))
    P.add("horn_" + tag, dark, mat("horn_demon"), "head", smooth=True)
    tip = {"gilt": mat("brass_gilt"), "ember": field("horn", 2.6)}.get(word, mat("bone"))
    P.add("horn_tip_" + tag, pale, tip, "head", smooth=True)
    if bands:
        P.add("horn_bands_" + tag, bands, mat("accent_light") if word == "banded" else mat("metal_iron_light"), "head", smooth=True)


@slot("horns", *(list(HORNS) + list(HORNS_ODD)))
def horns(P, size, word):
    style = P._style
    if style in HORNS_ODD:
        left, right = HORNS_ODD[style]
        left = HORNS[left] if isinstance(left, str) else left
        right = HORNS[right] if isinstance(right, str) else right
    else:
        left = right = HORNS[style]
    grow_horns(P, left, 1, size, word, "l")
    grow_horns(P, right, -1, size, word, "r")
    if word == "gate":          # half of the last gate it came through, still hanging from its left horn
        hr = P.hr
        top = P.horn_tip["l"] + Vector((-0.1 * hr, 0, -0.5 * hr))
        bars, cross = None, None
        for i in range(4):
            x = top.x + (i - 1.5) * 0.36 * hr
            bars = g.merge(bars, g.tube([Vector((x, top.y, top.z + 0.1 * hr)), Vector((x, top.y + 0.04 * hr, top.z - (1.7 - 0.3 * (i % 2)) * hr))], 0.055 * hr, n=4))
        for dz in (-0.2, -1.0):
            cross = g.merge(cross, g.box(top + Vector((0, 0.02 * hr, dz * hr)), (1.5 * hr, 0.07 * hr, 0.14 * hr)))
        ring = hoop(P.horn_tip["l"] + Vector((0, 0, -0.3 * hr)), 0.2 * hr, 0.26 * hr, 0.035 * hr, u=X, v=Z, n=8, sides=4)
        P.rider("sway", "gate", [(bars, "metal_iron_light"), (cross, "metal_iron_light"), (ring, "brass_crown")], P.horn_tip["l"], "head", smooth=False)


@slot("horns", "mono")
def horns_mono(P, size, word):
    """One horn, from the middle of the brow."""
    hr = P.hr
    size *= 1.3
    root = horn_root(P, "mid")
    path = spline([root, root + Vector((0, -0.2, 0.7)) * hr * size, root + Vector((0, -0.12, 1.7)) * hr * size], 3)
    a, b = horn(path, 0.19 * hr, 0.14)
    P.add("horn_mid", a, mat("horn_demon"), "head", smooth=False)
    P.add("horn_mid_tip", b, mat("bone"), "head", smooth=False)


@slot("horns", "ring")
def horns_ring(P, size, word):
    """A crown of its own horns: seven in a ring about its head, the two in front the tallest."""
    hr = P.hr
    c = Vector((0, P.hcy, P.crown - 0.42 * hr))
    dark, pale = None, None
    for i in range(7):
        a = -math.pi / 2 + math.pi / 7.0 + 2 * math.pi * i / 7.0        # one either side of the front, one at the back
        front = max(0.0, -math.sin(a))
        d = Vector((math.cos(a), math.sin(a) * 1.08, 0))
        b0 = c + d * hr * 0.84
        tall = (0.95 + 1.0 * front) * hr * size
        path = spline([b0, b0 + d * hr * 0.26 + Vector((0, 0, tall * 0.5)), b0 + d * hr * 0.08 + Vector((0, 0, tall))], 2)
        x, y = horn(path, 0.15 * hr, 0.0)
        dark, pale = g.merge(dark, x), g.merge(pale, y)
    P.add("horn_ring", dark, mat("horn_demon"), "head", smooth=True)
    P.add("horn_ring_tips", pale, mat("bone"), "head", smooth=True)
    P.add("horn_ring_band", hoop(c + Vector((0, 0, 0.02 * hr)), hr * 0.86, hr * 0.94, 0.06 * hr, n=14, sides=4), mat("horn_demon"), "head", smooth=False)


@slot("horns", "four", "double")
def horns_two_pair(P, size, word):
    """Two pair: one forward and one back (four), or a small pair over a great one (double)."""
    if P._style == "four":
        fore = [("brow", [(0, -0.1, 0), (0.26, -0.34, 0.5), (0.32, -0.86, 0.84)], 0.14, 0.0)]
        aft = [("brow", [(0.05, 0.3, -0.02), (0.3, 0.7, 0.4), (0.36, 1.3, 0.72)], 0.14, 0.0)]
    else:
        fore = [("brow", [(0, 0, -0.04), (0.8, 0, 0.0), (1.42, -0.12, 0.34), (1.62, -0.24, 0.92)], 0.21, 0.0)]
        aft = [("brow", [(-0.12, 0.1, 0.1), (0.12, 0.1, 0.6), (0.32, 0.06, 1.12)], 0.13, 0.0)]
    for s, tag in ((1, "l"), (-1, "r")):
        grow_horns(P, fore, s, size, word, "fore_" + tag)
        grow_horns(P, aft, s, size, word, "aft_" + tag)


@slot("horns", "boss")
def horns_boss(P, size, word):
    """Two horns grown forward until they met: one boss, like the head of a ram for gates."""
    hr = P.hr
    k = size
    for s, tag in ((1, "l"), (-1, "r")):
        grow_horns(P, [("temple", [(0.0, 0.1, 0.1), (0.28, -0.3, 0.42), (0.1, -1.0, 0.36), (-0.52, -1.5, 0.12)], 0.3, 0.14)], s, k, None, tag)
    c = Vector((0, P.hy0 - 0.62 * hr * k, P.eye.z + 0.62 * hr))
    P.add("horn_boss", g.ico(c, hr * 0.5 * k, sub=1, scale=(1.25, 0.8, 0.9)), mat("horn_demon"), "head", smooth=False)
    P.add("horn_boss_face", g.ico(c + Vector((0, -0.2 * hr * k, 0)), hr * 0.36 * k, sub=1, scale=(1.2, 0.6, 0.9)), mat("bone"), "head", smooth=False)


@slot("horns", "wreath")
def horns_wreath(P, size, word):
    """Its own stag's horns, and a wreath of others, no two alike, from brow to nape."""
    hr = P.hr
    for s, tag in ((1, "l"), (-1, "r")):
        grow_horns(P, HORNS["stag"], s, size * 0.9, None, tag)
    c = Vector((0, P.hcy, P.crown - 0.5 * hr))
    dark, pale = None, None
    kinds = ([(0, 0, 0), (0.3, 0, 0.3), (0.42, 0, 0.74)], [(0, 0, 0), (0.4, 0, 0.1), (0.72, 0, 0.36), (0.74, 0, 0.7)], [(0, 0, 0), (0.2, 0, 0.5), (0.5, 0, 0.62)],
             [(0, 0, 0), (0.5, 0, 0.3), (0.92, 0, 0.3)])
    for i in range(11):
        ang = math.pi * (-0.34 + 1.68 * i / 10.0)                    # round the back of the head, temple to temple
        out = Vector((math.cos(ang), math.sin(ang) * 1.08, 0))
        b0 = c + out * hr * 0.92 + Vector((0, 0, -0.14 * hr * math.sin(ang) ** 2))
        kind = kinds[i % len(kinds)]
        path = spline([b0 + out * q[0] * hr * size * 1.2 + Vector((0, 0, q[2] * hr * size * 1.2)) for q in kind], 2)
        x, y = horn(path, (0.11 + 0.03 * (i % 3)) * hr, 0.1 * (i % 2))
        dark, pale = g.merge(dark, x), g.merge(pale, y)
    P.add("horn_wreath", dark, mat("horn_demon"), "head", smooth=True)
    P.add("horn_wreath_tips", pale, mat("bone"), "head", smooth=True)


# ======================================================================================
# Wings of skin, in its Path's colour
# ======================================================================================

def wing_geo(P, R, E, W, tips, s, body=None, torn=(), bars=0, trim=False):
    """One wing: its arm (shoulder R, elbow E, wrist W) and a finger to each tip, with the skin
    between. [(geometry, material name)]. body: where the last panel is made fast to the back.
    torn: panels left out. bars: bands of a lighter step across the skin. trim: a paler hem."""
    n = (E - R).cross(W - E)
    n = n.normalized() if n.length > 1e-6 else Y
    arm = g.tube([R, E, W], [0.05 * P.t, 0.04 * P.t, 0.03 * P.t], n=5)
    fingers, skin, hem, bar = None, None, None, None
    pts = list(tips) + ([body] if body is not None else [])
    for i, F in enumerate(tips):
        mid = W.lerp(F, 0.5) + n * 0.0
        fingers = g.merge(fingers, g.tube([W, mid, F], [0.024 * P.t, 0.018 * P.t, 0.006 * P.t], n=4))
    for i in range(len(pts) - 1):
        if i in torn:
            continue
        a, b = pts[i], pts[i + 1]
        sag = a.lerp(b, 0.5).lerp(W, 0.2)          # the hem between two fingers hangs in toward the wrist
        skin = g.merge(skin, plate([W, a, sag, b], 0.016))
        if trim:
            hem = g.merge(hem, g.tube([a, a.lerp(sag, 0.5).lerp(a.lerp(b, 0.25), 0.3), sag, sag.lerp(b, 0.5).lerp(a.lerp(b, 0.75), 0.3), b], [0.016 * P.t] * 5, n=3))
        for j in range(bars):
            f = 0.42 + 0.22 * j
            bar = g.merge(bar, plate([W.lerp(a, f), W.lerp(a, f + 0.09), W.lerp(sag, f + 0.07), W.lerp(b, f + 0.09), W.lerp(b, f), W.lerp(sag, f - 0.02)], 0.024))
    # the skin from the arm to the first finger, and the claw at the wrist
    skin = g.merge(skin, plate([R, E, W, tips[0].lerp(W, 0.3)], 0.016)) if len(tips) else skin
    claw = g.cone(W, W + (W - E).normalized() * 0.04 * P.t + Vector((0, -0.02, 0.12 * P.t)), 0.03 * P.t, n=4)
    return [(skin, "accent"), (bar, "accent_pale"), (hem, "accent_light"), (arm, "main"), (fingers, "main"), (claw, "bone")]


def wing_root(P, s):
    backz = P.J["chest"].z + 0.3 * P.t
    return Vector((s * 0.1 * P.t, P.rear(backz) + 0.01, backz))


@slot("wings", "buds", "cape", "high", "half", "spread", "cloak", "tails", "fan", "stubs")
def wings(P, size, word):
    """Its wings, as its Path wears them: buds that beat to no purpose; a cape over its
    shoulders; a collar standing behind its head (high); half open; spread; a cloak to the
    ground; the tails of its coat (fan: spread behind it like a courtier's skirts; odd: one a
    tail and one a cape); stubs that never grew. They mantle (glide), or beat."""
    k = P.t * size
    t = P.t
    for tag, s in (("l", 1), ("r", -1)):
        style = P._style
        if word == "odd":
            style = "cape" if s > 0 else "tails"
        R = wing_root(P, s)
        sw = P.sx
        back = R.y
        torn, bars, trim, body = (), 0, False, None

        def at(x, y, z):
            return Vector((s * x, y, z))
        if style == "buds":
            E, W = R + Vector((s * 0.14, 0.1, 0.12)) * k, R + Vector((s * 0.3, 0.16, 0.34)) * k
            tips = [W + Vector((s * 0.3, 0.04, 0.0)) * k, W + Vector((s * 0.22, 0.06, -0.26)) * k, W + Vector((s * 0.04, 0.05, -0.36)) * k]
            body = R + Vector((0, 0.02, -0.14)) * k
        elif style == "stubs":
            E, W = R + Vector((s * 0.22, 0.14, 0.2)) * k, R + Vector((s * 0.5, 0.2, 0.46)) * k
            tips = [W + Vector((s * 0.4, 0.05, 0.02)) * k, W + Vector((s * 0.34, 0.08, -0.32)) * k, W + Vector((s * 0.12, 0.08, -0.5)) * k, W + Vector((s * -0.12, 0.05, -0.5)) * k]
            torn = (1,)
        elif style == "half":
            E, W = R + Vector((s * 0.3, 0.2, 0.42)) * k, R + Vector((s * 0.58, 0.3, 0.9)) * k
            tips = [W + Vector((s * 0.56, 0.1, -0.06)) * k, W + Vector((s * 0.46, 0.16, -0.62)) * k, W + Vector((s * 0.2, 0.16, -1.04)) * k, W + Vector((s * -0.12, 0.1, -1.22)) * k]
            body = R + Vector((0, 0.03, -0.5)) * k
        elif style == "spread":
            E, W = R + Vector((s * 0.46, 0.14, 0.36)) * k, R + Vector((s * 0.98, 0.22, 0.78)) * k
            tips = [W + Vector((s * 0.95, 0.06, 0.26)) * k, W + Vector((s * 0.9, 0.12, -0.44)) * k, W + Vector((s * 0.5, 0.14, -0.96)) * k, W + Vector((s * -0.06, 0.12, -1.22)) * k]
            body = R + Vector((0, 0.03, -0.72)) * k
            bars = 2 if word == "barred" else 0
        elif style == "cape":
            # folded over its shoulders: the wrist stands above the shoulder, a finger down before it, the rest down its back
            W = at(sw * 0.8, P.army + 0.03 * t, P.armz + 0.34 * k)
            E = at(sw * 0.4, back + 0.14 * t, P.armz - 0.22 * t)
            hemz = P.hipz + (0.34 - 0.5 * size) * t
            fy = P.front(P.armz - 0.1 * t, sw * 0.6)
            tips = [at(sw * 0.62, fy - 0.1 * t, P.armz - 0.26 * k), at(sw + 0.26 * k, P.army - 0.02 * t, P.armz - 0.42 * k), at(sw + 0.16 * k, back + 0.22 * t, hemz + 0.12 * t),
                    at(sw * 0.4, back + 0.3 * t, hemz - 0.1 * t)]
            tips += [at(-0.03 if word == "split" else -0.1 * t, back + 0.28 * t, hemz + (0.34 * t if word == "split" else -0.02 * t))]
            if word == "split":
                tips[3] = at(sw * 0.56, back + 0.27 * t, hemz + 0.05 * t)
            trim = word == "trimmed"
        elif style == "high":
            # mantled: the wrists up behind its ears like the points of a collar
            W = at(sw * 0.95, back + 0.04 * t, P.chin + 0.74 * P.hh * size)
            E = at(sw * 0.5, back + 0.16 * t, P.armz - 0.16 * t)
            hemz = P.hipz - 0.1 * t * size
            fy = P.front(P.armz - 0.1 * t, sw * 0.6)
            tips = [at(sw * 0.66, fy - 0.09 * t, P.armz - 0.2 * k), at(sw + 0.3 * k, P.army, P.armz - 0.36 * k), at(sw + 0.18 * k, back + 0.22 * t, hemz + 0.3 * t), at(sw * 0.6, back + 0.29 * t, hemz),
                    at(-0.08 * t, back + 0.3 * t, hemz - 0.1 * t)]
            trim = True
        elif style == "cloak":
            # wrapped round it to the ground, and open only a hand down the front
            W = at(sw * 0.8, back + 0.02 * t, P.armz + 0.34 * k)
            E = at(sw * 0.4, back + 0.14 * t, P.armz - 0.2 * t)
            hemz = 0.18
            rx = sw + 0.34 * k
            tips = [at(0.16, P.front(P.chestz) - 0.34 * t, hemz + 0.3), at(rx * 0.86, P.army - 0.34 * t, hemz + 0.1), at(rx, P.army + 0.1 * t, hemz), at(rx * 0.74, back + 0.4 * t, hemz + 0.06),
                    at(-0.1 * t, back + 0.5 * t, hemz + 0.12)]
        elif style == "fan":
            # the tails of its coat held out behind it, as a courtier holds a skirt
            W = at(0.18 * t, back + 0.1 * t, P.hipz + 0.3 * t)
            E = at(0.12 * t, back + 0.06 * t, P.J["chest"].z + 0.44 * t)
            tips = [at(sw + 0.52 * k, back + 0.06 * t, P.hipz + 0.16 * t), at(sw + 0.42 * k, back + 0.36 * t, P.hipz - 0.36 * t), at(sw * 0.7 + 0.1 * k, back + 0.62 * t, P.hipz - 0.62 * t),
                    at(0.03 * t, back + 0.54 * t, P.hipz - 0.5 * t)]
            trim = True
        else:
            # the tails of its coat: folded shut down its back, the wrist in the small of it
            W = at(0.17 * t, back + 0.1 * t, P.hipz + 0.3 * t)
            E = at(0.12 * t, back + 0.06 * t, P.J["chest"].z + 0.44 * t)
            hemz = max(P.hockz - 0.2, P.hipz - 0.95 * t * size)
            tips = [at(0.36 * t + 0.08 * k, back + 0.14 * t, P.hipz - 0.08 * t), at(0.34 * t + 0.1 * k, back + 0.36 * t * size, (P.hipz + hemz) / 2 - 0.1 * t), at(0.16 * t + 0.05 * k, back + 0.5 * t * size, hemz),
                    at(0.03 * t, back + 0.22 * t, (P.hipz + hemz) / 2 + 0.1 * t)]
        items = wing_geo(P, R, E, W, tips, s, body=body, torn=torn, bars=bars, trim=trim)
        if style in ("tails", "fan") and word != "lined":      # the tails of a coat are a step darker than its waistcoat
            items = [(geo, "accent_dark" if m == "accent" else m) for geo, m in items]
        if word == "parti" and s < 0:
            items = [(geo, "cloth_coat" if m in ("accent", "accent_dark") else m) for geo, m in items]
        P.rider("beat" if style == "buds" else "glide", "wing", items, R, "chest", side=tag, smooth=False)


# ======================================================================================
# A tail
# ======================================================================================

# its line from the root, in trunk heights: (back, up) at each point; and how thick at the root
TAILS = {
    "tuft": ([(0.0, 0.0), (0.26, -0.1), (0.52, -0.02), (0.68, 0.26), (0.66, 0.56)], 0.05),
    "spade": ([(0.0, 0.0), (0.24, -0.16), (0.56, -0.24), (0.86, -0.06), (0.96, 0.3)], 0.05),
    "curl": ([(0.0, 0.0), (0.2, -0.06), (0.44, 0.1), (0.5, 0.42), (0.34, 0.66), (0.14, 0.6)], 0.042),
    "whip": ([(0.0, 0.0), (0.3, -0.2), (0.7, -0.36), (1.1, -0.3), (1.36, -0.02), (1.42, 0.36)], 0.045),
    "barb": ([(0.0, 0.0), (0.3, -0.06), (0.7, 0.04), (1.1, 0.26), (1.46, 0.56)], 0.04),
    "bull": ([(0.0, 0.0), (0.16, -0.12), (0.26, -0.44), (0.3, -0.8), (0.36, -1.08)], 0.075),
    "smoke": ([(0.0, 0.0), (0.26, -0.12), (0.56, -0.1), (0.82, 0.1)], 0.055),
    "flame": ([(0.0, 0.0), (0.24, -0.14), (0.56, -0.16), (0.84, 0.04), (0.92, 0.36)], 0.05),
}


@slot("tail", *TAILS)
def tail(P, size, word):
    """Its tail: tufted, spaded, held up in a curl, a long whip, a barb like a sword's point, a
    bull's with a heavy tuft, or ending in smoke or a flame. It sways; a young one wags."""
    style = P._style
    line, r0 = TAILS[style]
    t = P.t * size
    hz = P.hipz - 0.04 * P.t
    b0 = Vector((0, P.rear(hz) - 0.03, hz))
    side = 0.14 if style in ("curl", "tuft") else 0.06
    pts = spline([b0 + Vector((side * q[0] * t, q[0] * t, max(q[1] * t, 0.14 - b0.z))) for q in line], 3)        # (it does not go through the ground)
    m = len(pts)
    radii = [r0 * P.t * (1.0 - 0.62 * i / (m - 1)) for i in range(m)]
    tip, d = pts[-1], (pts[-1] - pts[-2]).normalized()
    end = word if word in ("spade", "tuft") else {"tuft": "tuft", "spade": "spade", "curl": "tuft", "whip": "spade", "bull": "tuft"}.get(style, style)
    fur = "fur_sable"
    ends = []
    if end == "spade":
        ends.append((g.blade(tip - d * 0.03, tip + d * 0.3 * t, 0.22 * t, normal=X, belly=0.36, thick=0.03), "main"))
    elif end == "tuft":
        tuft = None
        big = 1.7 if style == "bull" else 1.0
        for a in (-0.5, 0.0, 0.5):
            dd = (d + Vector((a * 0.5, 0, 0)) + Vector((0, 0.3 * abs(a), -0.2 * abs(a)))).normalized()
            tuft = g.merge(tuft, g.blade(tip - d * 0.03, tip + dd * 0.26 * t * big, 0.15 * t * big, normal=X if a == 0 else (0.3, 1, 0), belly=0.42))
        ends.append((tuft, fur))
    elif end == "barb":
        ends.append((g.blade(tip - d * 0.02, tip + d * 0.34 * t, 0.2 * t, normal=X, belly=0.24, thick=0.03), "bone"))
        back = None
        for sg in (1, -1):
            up = d.cross(X).normalized() * sg
            back = g.merge(back, g.cone(tip + d * 0.06 * t + up * 0.06 * t, tip - d * 0.1 * t + up * 0.16 * t, 0.03 * t, n=4))
        ends.append((back, "bone"))
    elif end == "smoke":
        puffs = None
        for i in range(4):
            q = tip + d * (0.1 + 0.16 * i) * t + Vector((0.05 * (i % 2), 0, 0.06 * i * t))
            puffs = g.merge(puffs, g.ico(q, (0.11 - 0.018 * i) * t, sub=1))
        ends.append((puffs, "smoke_pale"))
    whole = [(g.tube(pts, radii, n=6), "main")] + ends
    if style == "flame":                       # the tail keeps still, and the flame at its end does not
        for i, (geo, m_) in enumerate(whole):
            P.add("tail_%d" % i, geo, P.material(m_), "hips", smooth=True)
        fl = None
        for a, L in ((0.0, 0.4), (0.5, 0.26), (-0.5, 0.24)):
            fl = g.merge(fl, g.blade(tip - d * 0.02, tip + (Vector((a * 0.3, 0.08, 1.0))).normalized() * L * t, 0.17 * t, normal=Y, belly=0.36))
        P.rider("flick", "tailflame", [(fl, field("flame", 2.8))], tip, "hips")
        return
    P.rider("wag" if word == "wag" else "sway", "tail", whole, b0, "hips")
    if style == "smoke":                       # and a wisp let go of, a little way off
        P.rider("bob", "tailsmoke", [(g.ico(tip + d * 0.62 * t + Vector((0, 0, 0.26 * t)), 0.075 * t, sub=1), "shade_edge")], tip, "hips")


# ======================================================================================
# The lines
# ======================================================================================

def demon_form(form_id, level, spec, silhouette, path=None, clips=False):
    lp = people()
    P = Demon(form_id, level, spec, lp._roles(silhouette))
    P.silhouette = silhouette
    # a form whose head is a crown of flame has none: it is drawn in under the collar
    P.headless = any(st == "flame" for st, _, _ in lp.each(spec.get("crown")))
    if P.headless:
        head = P.hb.is_head
        c = np.array([0.0, P.J["head"].y, P.neckz + 0.02])
        P.v[head] = c + (P.v[head] - c) * 0.2
    for name in ORDER:
        entries = lp.each(spec.get(name))
        if not entries and name in DEFAULTS and name not in spec:
            entries = [(DEFAULTS[name], 1.0, None)]
        for style, size, word in entries:
            fn = SLOTS.get(name, {}).get(style) or lp.SLOTS.get(name, {}).get(style)
            if fn is None:
                log("!! %s: no %s called %s" % (form_id, name, style))
                continue
            P._style, P._slot = style, name
            fn(P, size, word)
    P.finish(path or os.path.join(OUT, form_id + ".glb"), clips=clips)


def palette():
    """The colours a Demon is built on: the kit's and the Wolf's (as every base), the small
    people's (it wears some of what they wear), and its own."""
    lp = people()
    PALETTE.update(getattr(GL, "_OWN", {}).get("lines_people", {}) if GL is not None else {})
    PALETTE.update(lp.OWN)
    PALETTE.update(OWN)


def build(form_id, level, spec, base):
    lp = people()
    palette()
    try:
        demon_form(form_id, level, spec, lp._silhouettes(base)[form_id])
    except Exception:
        if not os.environ.get("WILDLINE_KEEP_GOING"):     # while a line is being worked on: say which form failed, and go on
            raise
        import traceback
        log("!! %s failed" % form_id)
        traceback.print_exc()


def register(builders):
    global GL
    for name in ("genius_lines", "__main__"):
        m = sys.modules.get(name)
        if m is not None and getattr(m, "BUILDERS", None) is builders:
            GL = m
    PALETTE.update(OWN)
    builders["demon"] = build


if __name__ == "__main__":
    import genius_lines
    GL = genius_lines
    import demon_gifts
    demon_gifts.main(sys.argv[1:])
