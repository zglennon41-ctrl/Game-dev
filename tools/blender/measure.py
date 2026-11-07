"""WILDLINE proportions: measure a built body and its head against adult anthropometry
(docs/bodies-plan.md, "Proportions"). Run headless with Blender's Python module:

    python tools/blender/measure.py                  # alexandria-m and alexandria-f
    python tools/blender/measure.py edo-f            # one body

Body measures are in body units (2.4 tall for 175 cm); the head's in head-heights (H).
The adult column is the acceptance test: a value more than a tenth off is marked.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import people_kit as pk  # noqa: E402

OUT = os.path.join(pk.ROOT, "game", "assets", "people")
H = 0.32

# (name, how, adult masculine, adult feminine); "how" is (kind, level): width across at a
# height, the depth front to back, a limb's thickness at an x, or a bone length.
BODY = [
    ("neck width", ("width", 2.0), 0.165, 0.145),
    ("chest width", ("width", 1.62), 0.41, 0.39),
    ("waist width", ("width", 1.3), 0.36, 0.33),
    ("hips width", ("width", 1.05), 0.46, 0.50),
    ("hips depth", ("depth", 1.05), 0.32, 0.32),
    ("thigh, one", ("side", 0.72), 0.23, 0.25),
    ("calf, one", ("side", 0.4), 0.165, 0.165),
    ("upper arm", ("arm", 0.39), 0.13, 0.12),
    ("forearm", ("arm", 0.75), 0.115, 0.10),
    ("wrist", ("arm", 0.9), 0.075, 0.068),
    ("upper arm length", ("bone", ("upperarm.l", "lowerarm.l")), 0.45, 0.45),
    ("forearm length", ("bone", ("lowerarm.l", "wrist.l")), 0.36, 0.36),
]
HEAD = [
    ("head width at the eyes", 0.0, 0.65),
    ("jaw width", -0.38, 0.47),
    ("chin width", -0.45, 0.3),
]


def measure(body_id):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, body_id + ".glb"))
    sex = body_id.rsplit("-", 1)[1]
    k = 1.0 if sex == "m" else 7.25 / 7.5
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    body = bpy.data.objects["Body"]
    P = [body.matrix_world @ v.co for v in body.data.vertices]
    rows = []
    for name, (kind, lvl), am, af in BODY:
        adult = am if sex == "m" else af
        if kind == "bone":
            a = arm.matrix_world @ arm.data.bones[lvl[0]].head_local
            b = arm.matrix_world @ arm.data.bones[lvl[1]].head_local
            v = (b - a).length / k
        elif kind == "arm":
            band = [p for p in P if abs(p.x - lvl * k) < 0.012 and p.z > 1.6 * k]
            v = (max(p.z for p in band) - min(p.z for p in band)) / k if band else 0.0
        else:
            band = [p for p in P if abs(p.z - lvl * k) < 0.02 and abs(p.x) < 0.33]
            if kind == "side":
                band = [p for p in band if p.x > 0.02]
            if not band:
                v = 0.0
            elif kind == "depth":
                v = (max(p.y for p in band) - min(p.y for p in band)) / k
            else:
                v = (max(p.x for p in band) - min(p.x for p in band)) / k
        rows.append((name, v, adult))
    head = bpy.data.objects["Head"]
    Q = [head.matrix_world @ v.co for v in head.data.vertices]
    top, bottom = max(q.z for q in Q), min(q.z for q in Q)
    hh = top - bottom
    cz = bottom + 0.5 * hh
    for name, lvl, adult in HEAD:
        band = [q for q in Q if abs((q.z - cz) / hh - lvl) < 0.02]
        v = (max(q.x for q in band) - min(q.x for q in band)) / hh if band else 0.0
        rows.append((name + " (H)", v, adult))
    eyes = [bpy.data.objects[n] for n in ("Eye_l", "Eye_r") if n in bpy.data.objects]
    if len(eyes) == 2:
        from mathutils import Vector
        c = [sum((o.matrix_world @ v.co for v in o.data.vertices), Vector((0, 0, 0))) / len(o.data.vertices) for o in eyes]
        rows.append(("pupils apart (H)", abs(c[0].x - c[1].x) / hh, 0.29))
    return rows


if __name__ == "__main__":
    ids = sys.argv[1:] or ["alexandria-m", "alexandria-f"]
    for body_id in ids:
        print(body_id)
        for name, v, adult in measure(body_id):
            flag = "" if abs(v - adult) <= 0.1 * adult else "  <-- off"
            print("  %-26s %.3f  adult %.3f%s" % (name, v, adult, flag))
