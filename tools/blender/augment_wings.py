"""WILDLINE Augments, a first proof: living wings worn on the body, through the five stages
(docs/genius-types.md, "Augments"; data/genius.json, equipment.augments.wings).

    python tools/blender/augment_wings.py            # all five
    python tools/blender/augment_wings.py 3          # one stage (0 Baby .. 4 Final)

Output: game/assets/genius/augments/wings-<stage>.glb. The game hangs it on the bone between
its partner's shoulder blades (game/scripts/genius/augment.gd).

An Augment is held to the rule of every equipment genius: it is the same size at every stage.
The frame of the wing (its arm, its wrist, its reach) is made once and never changes; what a
stage gives it is what it shows:

  0 Baby         down on the arm, and bare quills where the flight feathers will be
  1 Starter      the quills have their vanes: plain flight feathers; an eye opens at each wrist
  2 Path         a second row over the first, banded; sinews of the field down the arm
  3 Advancement  coverts over the shoulder, an eye of the field on every third feather
  4 Final        every feather edged with the field; strings of sinew from the last feathers;
                 a third eye between the wings, and gills at their roots that breathe

The model, in the genius kit's way: Z up, the wearer faces -Y, so the wings stand at +Y (the
back); the origin is the place between the shoulder blades. Each wing is an object of its own
(wing_l at +X, wing_r) with its origin at its root, and what moves on it is its child, named
as every moving piece is (blink_*, pulse_*, sway_*: docs/genius-lines.md, "What moves").
In game units: a person stands about 2.4.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as gk  # noqa: E402
import genius_relics as gr  # noqa: E402

ROOT = gk.ROOT
OUT = os.path.join(ROOT, "game", "assets", "genius", "augments")

# the frame of a left wing, never changed by a stage: root, elbow, wrist, the end of the hand
ROOT_AT = Vector((0.075, 0.05, 0.0))
ELBOW = Vector((0.2, 0.2, 0.3))
WRIST = Vector((0.4, 0.26, 0.42))
HAND = Vector((0.5, 0.3, 0.2))
PRIMARIES = 7
SECONDARIES = 6
FACE = Vector((0.15, 1.0, 0.1))        # which way a feather's face looks: back, and a little out


def _mirror(geo):
    verts, faces = geo
    return [Vector((-p.x, p.y, p.z)) for p in (V(q) for q in verts)], [tuple(reversed(f)) for f in faces]


def _feather_roots():
    """Where each flight feather grows from and where it ends: the primaries from the hand
    (they sweep down and a little back, the longest outermost), the secondaries from the
    forearm (shorter, toward the body). The same at every stage."""
    out = []
    for i in range(PRIMARIES):
        t = i / (PRIMARIES - 1.0)
        base = WRIST.lerp(HAND, 0.15 + 0.85 * t)
        tip = base + Vector((0.1 - 0.04 * t, 0.1 + 0.05 * t, -(0.62 + 0.3 * t)))
        out.append(("primary", i, base, tip, 0.085))
    for i in range(SECONDARIES):
        t = i / (SECONDARIES - 1.0)
        base = WRIST.lerp(ELBOW, 0.12 + 0.88 * t)
        tip = base + Vector((0.03 - 0.07 * t, 0.12 - 0.02 * t, -(0.6 - 0.14 * t)))
        out.append(("secondary", i, base, tip, 0.1))
    return out


def build(stage):
    gk.reset()
    pale, mid, dark = gk.mat("feather_pale"), gk.mat("feather_mid"), gk.mat("feather_dark")
    skin = gk.mat("hide_baby_pale", (0.56, 0.52, 0.46), 0.8, 0.0)
    feathers = _feather_roots()
    wing = []                   # [(geometry, material)] of the left wing itself
    moving = []                 # (name, [(geometry, material)], pivot) children of the left wing
    # the arm: bone under skin, a knuckle at the wrist
    wing.append((g.tube([ROOT_AT, ELBOW, WRIST, HAND], [0.05, 0.042, 0.034, 0.018], n=6), skin))
    wing.append((g.ico(WRIST, 0.045, sub=1), skin))
    # down along the arm at every stage (the Baby is all down)
    down = None
    for k in range(9):
        t = k / 8.0
        c = ROOT_AT.lerp(ELBOW, t * 2.0) if t < 0.5 else ELBOW.lerp(WRIST, (t - 0.5) * 2.0)
        down = g.merge(down, g.ico(c + Vector((0, 0.03, -0.035)), 0.062 - 0.012 * t, sub=1, scale=(1.0, 0.8, 1.15)))
    wing.append((down, pale))
    # the flight feathers: quills in the Baby, vanes after
    edges = None
    ocelli = []
    for kind, i, base, tip, width in feathers:
        if stage == 0:
            wing.append((g.tube([base, base.lerp(tip, 0.55) + Vector((0, 0.02, 0)), tip], [0.011, 0.008, 0.003], n=4), pale))
            wing.append((g.blade(base.lerp(tip, 0.72), tip, 0.03, normal=FACE, belly=0.4), pale))
            continue
        banded = stage >= 2 and kind == "secondary"
        wing.append((g.blade(base, tip, width, normal=FACE, belly=0.5, thick=0.008), mid if (kind == "primary" and i % 2) else pale))
        wing.append((g.tube([base, tip], [0.007, 0.002], n=3), dark))
        if banded:              # a band across each secondary, a hand's breadth from its end
            b0, b1 = base.lerp(tip, 0.62), base.lerp(tip, 0.8)
            wing.append((g.blade(b0, b1 + (tip - base).normalized() * 0.04, width * 0.92, normal=FACE + Vector((0, 0.4, 0)), belly=0.5, thick=0.01), dark))
        if stage >= 3 and i % 3 == 1:       # an eye of the field on the feather, as on a moth's wing
            c = base.lerp(tip, 0.7) + FACE.normalized() * 0.012
            ocelli += gr._eye(c, 0.026, facing=FACE)
        if stage >= 4:          # the field along the feather's outer edge
            side = (tip - base).cross(FACE).normalized()
            edges = g.merge(edges, g.tube([base.lerp(tip, 0.35) + side * width * 0.42, base.lerp(tip, 0.6) + side * width * 0.46, tip], [0.004, 0.004, 0.002], n=3))
    if ocelli:
        moving.append(("pulse_ocelli", ocelli, WRIST))
    if edges:
        moving.append(("pulse_edges", [(edges, gk.field("edge", 2.2))], WRIST))
    if stage >= 2:
        # a second row over the first: shorter feathers from the forearm and the hand
        for k in range(8):
            t = k / 7.0
            base = HAND.lerp(ELBOW, 0.05 + 0.9 * t) + Vector((0, 0.035, 0.0))
            tip = base + Vector((0.02 - 0.03 * t, 0.07, -0.3))
            wing.append((g.blade(base, tip, 0.085, normal=FACE, belly=0.5, thick=0.01), mid if k % 2 else dark))
        # sinews of the field down the arm, breathing
        vein = g.merge(g.tube([ROOT_AT + Vector((0, 0.052, 0.01)), ELBOW + Vector((0, 0.046, 0.012)), WRIST + Vector((0, 0.04, 0.012))], 0.006, n=3),
                       g.tube([ELBOW + Vector((0, 0.046, 0.012)), ELBOW.lerp(WRIST, 0.5) + Vector((0, 0.05, -0.06))], [0.005, 0.002], n=3))
        moving.append(("pulse_vein", [(vein, gk.field("vein", 2.2))], ROOT_AT))
    if stage >= 1:
        # an eye at the wrist, looking back
        c = WRIST + Vector((0.0, 0.046, 0.0))
        moving.append(("blink_eye", gr._eye(c, 0.03, facing=(0.1, 1, 0), lids=skin), c))
    if stage >= 3:
        # coverts over the shoulder: a mantle of short dark feathers at the root
        for k in range(5):
            a = -0.5 + 0.35 * k
            base = ROOT_AT.lerp(ELBOW, 0.1 + 0.16 * k) + Vector((0, 0.06, 0.03))
            wing.append((g.blade(base, base + Vector((0.05 * math.sin(a), 0.06, -0.2 - 0.02 * k)), 0.09, normal=FACE, belly=0.45, thick=0.012), dark))
    if stage >= 4:
        # strings of sinew from the last feathers (they hang inside the wing's own length)
        for n, idx in enumerate((PRIMARIES - 1, PRIMARIES - 3)):
            _, _, base, tip, _ = feathers[idx]
            top = base.lerp(tip, 0.55)
            pts = [top, top + Vector((0.02, 0.03, -0.12)), top + Vector((-0.015, 0.04, -0.24)), top + Vector((0.01, 0.035, -0.34))]
            moving.append(("sway_sinew%s" % "ab"[n], [(g.tube(pts, [0.006, 0.005, 0.004, 0.003], n=4), gk.mat("cloth_sinew", (0.6, 0.5, 0.36), 0.7, 0.0)), (g.ico(pts[-1], 0.013, sub=0), gk.field("vein", 2.4))], top))
        # gills at the root that breathe
        gills = None
        for k in range(3):
            gills = g.merge(gills, g.box(ROOT_AT.lerp(ELBOW, 0.18 + 0.12 * k) + Vector((0.0, 0.05, 0.035)), (0.008, 0.01, 0.045)))
        moving.append(("pulse_breath", [(gills, gk.field("breath", 2.0))], ROOT_AT))

    objects = []
    for side, name in ((1, "wing_l"), (-1, "wing_r")):
        flip = (lambda geo: geo) if side == 1 else _mirror
        at = lambda p: Vector((side * V(p).x, V(p).y, V(p).z))          # noqa: E731
        ob = g.pieces(name, [(flip(geo), m) for geo, m in wing])
        gk.set_origin(ob, at(ROOT_AT))
        ob.name = name
        objects.append(ob)
        for mname, items, pivot in moving:
            child = g.pieces("%s_%s" % (mname, "l" if side == 1 else "r"), [(flip(geo), m) for geo, m in items])
            gk.set_origin(child, at(pivot))
            child.name = "%s_%s" % (mname, "l" if side == 1 else "r")
            child.parent = ob
            child.matrix_parent_inverse = ob.matrix_world.inverted()
            objects.append(child)
    if stage >= 4:
        # a third eye between the wings, on a boss of the same skin
        c = Vector((0, 0.07, 0.06))
        boss = g.pieces("root", [(g.ico(Vector((0, 0.03, 0.05)), 0.07, sub=1, scale=(1.3, 0.6, 1.0)), skin)], smooth=True)
        objects.append(boss)
        eye = g.pieces("blink_third", gr._eye(c, 0.036, facing=(0, 1, 0), lids=skin))
        gk.set_origin(eye, c)
        eye.name = "blink_third"
        objects.append(eye)
    else:
        objects.append(g.pieces("root", [(g.ico(Vector((0, 0.03, 0.04)), 0.055, sub=1, scale=(1.3, 0.6, 1.0)), skin)], smooth=True))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "wings-%d.glb" % stage)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects)
    pts = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    size = [max(q[i] for q in pts) - min(q[i] for q in pts) for i in range(3)]
    print("[augment_wings] wrote %s: %d triangles, %d KB, %.2f wide, %.2f deep, %.2f tall" % (os.path.relpath(path, ROOT), tris, os.path.getsize(path) // 1024, size[0], size[1], size[2]))


if __name__ == "__main__":
    which = [int(a) for a in sys.argv[1:] if a.isdigit()] or [0, 1, 2, 3, 4]
    for st in which:
        build(st)
