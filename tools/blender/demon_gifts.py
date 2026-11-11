"""The Demon's line (lines_demon.py): what it gives a hybrid, and the body its forms borrow
their clips from.

    python tools/blender/lines_demon.py gifts     # game/assets/genius/gifts/demon-horns.glb, demon-wings.glb
    python tools/blender/lines_demon.py body      # game/assets/genius/bodies/daemon-prince.glb

A hybrid that has turned toward the Demon wears the Demon's own horns and its own wings on
whatever body it has (docs/genius-lines.md, "How the game wears it"). Other bases give horns
and wings too, so these say whose they are: the horns stand through a crown that has broken,
and the wings are skin, with a claw at the wrist, and mantle. A part is modelled at its
socket's origin, at the kit's size, facing the way the kit faces.

The body is the Princeling's own, with the rig's three clips left in it: a form of the line
has none, and the game fits these to it (genius_body.gd, _borrow_clips)."""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE  # noqa: E402

GIFT_DIR = os.path.join(kit.ROOT, "game", "assets", "genius", "gifts")
BODY_DIR = os.path.join(kit.ROOT, "game", "assets", "genius", "bodies")


def _ld():
    import lines_demon
    return lines_demon


def horns_gift():
    """The Demon's horns: two long ringed horns swept up and back, pale at the point, standing
    through a crown that has lost a third of itself and is worn anyway."""
    ld = _ld()
    dark, pale = None, None
    for s in (1, -1):
        path = ld.spline([Vector((s * 0.05, 0.0, -0.012)), Vector((s * 0.1, 0.01, 0.07)), Vector((s * 0.13, 0.06, 0.16)), Vector((s * 0.1, 0.13, 0.25)), Vector((s * 0.12, 0.17, 0.34))], 3)
        a, b = ld.horn(path, 0.034, ridged=0.16, n=6)
        dark, pale = g.merge(dark, a), g.merge(pale, b)
    c = Vector((0, 0.0, -0.005))
    import demon_dress as dd
    band = dd.crown_band(c, 0.092, 0.1, 0.0, 0.032, math.pi * 0.72, math.pi * 2.28, 0.006, n=10)
    pts = None
    for i in range(5):
        a = math.pi * (0.72 + 1.56 * (i + 0.5) / 5)
        b0 = c + Vector((0.095 * math.cos(a), 0.103 * math.sin(a), 0.03))
        pts = g.merge(pts, g.blade(b0, b0 + Vector((math.cos(a) * 0.006, math.sin(a) * 0.006, 0.04 + 0.014 * (i % 2))), 0.03, normal=(math.cos(a), math.sin(a), 0), belly=0.3, thick=0.005))
    stone = g.ico(c + Vector((0, -0.104, 0.016)), 0.011, sub=0, scale=(1, 0.6, 1.2))
    return [(dark, mat("horn_demon")), (pale, mat("bone")), (g.merge(band, pts), mat("brass_crown")), (stone, field("crown", 2.6))]


def wings_gift():
    """The Demon's wings: skin on long fingers, a claw at each wrist, held half open; they
    mantle. Each is a piece of its own that the game moves (glide_wing_l, glide_wing_r)."""
    out = []
    for tag, s in (("l", 1), ("r", -1)):
        R = Vector((s * 0.045, 0.0, -0.01))
        E, W = R + Vector((s * 0.15, 0.06, 0.16)), R + Vector((s * 0.3, 0.1, 0.36))
        tips = [W + Vector((s * 0.3, 0.03, -0.02)), W + Vector((s * 0.25, 0.06, -0.26)), W + Vector((s * 0.1, 0.07, -0.44)), W + Vector((s * -0.08, 0.05, -0.5))]
        body = R + Vector((0, 0.02, -0.22))
        skin, fingers = None, None
        pts = tips + [body]
        ld = _ld()
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            sag = a.lerp(b, 0.5).lerp(W, 0.2)
            skin = g.merge(skin, ld.plate([W, a, sag, b], 0.008))
        skin = g.merge(skin, ld.plate([R, E, W, tips[0].lerp(W, 0.3)], 0.008))
        for F in tips:
            fingers = g.merge(fingers, g.tube([W, W.lerp(F, 0.5), F], [0.011, 0.008, 0.003], n=4))
        arm = g.tube([R, E, W], [0.022, 0.018, 0.013], n=5)
        claw = g.cone(W, W + Vector((s * 0.01, -0.01, 0.06)), 0.013, n=4)
        ob = g.pieces("glide_wing_" + tag, [(skin, mat("hide_wing")), (arm, mat("horn_demon")), (fingers, mat("bone")), (claw, mat("claw"))])
        kit.set_origin(ob, R)
        out.append(ob)
    return out


GIFTS = {"demon-horns": horns_gift, "demon-wings": wings_gift}


def build_gift(name):
    kit.reset()
    PALETTE.update(_ld().OWN)
    PALETTE["hide_wing"] = ((0.2, 0.035, 0.06), 0.7, 0.0)
    made = GIFTS[name]()
    objs = made if made and not isinstance(made[0], tuple) else [g.pieces(name.replace("-", "_"), made)]
    path = os.path.join(GIFT_DIR, name + ".glb")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    print("[demon_gifts] wrote", os.path.relpath(path, kit.ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


def build_body():
    """The Princeling's body, with the rig's clips in it."""
    import genius_lines as gl
    ld = _ld()
    with open(os.path.join(kit.ROOT, "data", "genius-bases", "demon.json")) as f:
        base = json.load(f)
    form_id, level, spec = gl.forms_of(base)[0]
    gl._palette_of("demon")
    gl.accent(spec)
    ld.palette()
    ld.demon_form(form_id, level, spec, ld.SILHOUETTE, path=os.path.join(BODY_DIR, ld.SILHOUETTE + ".glb"), clips=True)


def main(args):
    if not args or "body" in args:
        build_body()
    for name in GIFTS:
        if not args or "gifts" in args or name in args:
            build_gift(name)


if __name__ == "__main__":
    main(sys.argv[1:])
