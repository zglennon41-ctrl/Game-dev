"""WILDLINE proportions: where a built body's joints are, against an adult's (docs/bodies-plan.md,
"Proportions" and "The human base"). Run headless with Blender's Python module:

    python tools/blender/measure.py                  # alexandria-m and alexandria-f
    python tools/blender/measure.py edo-f            # one body

The bodies are MakeHuman's human now, so their girths are a sculptor's and are not second-
guessed here; what this checks is the rig: that the game's bones sit on a real skeleton's
joints (the earlier rigs had the hips at 0.46 of the height and the knee at 0.24). Heights
are fractions of the stature; a value more than a twentieth off the adult's is marked.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import people_kit as pk  # noqa: E402

OUT = os.path.join(pk.ROOT, "game", "assets", "people")

LANDMARKS = [
    ("ankle height", "foot.l", 0.045),
    ("knee height", "lowerleg.l", 0.285),
    ("hip joint height", "upperleg.l", 0.53),
    ("shoulder joint height", "upperarm.l", 0.81),
    ("neck pivot height", "head", 0.87),
]


def measure(body_id):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, body_id + ".glb"))
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    body = bpy.data.objects["Body"]
    zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
    stature = max(zs) - min(zs)
    head = lambda b: arm.matrix_world @ arm.data.bones[b].head_local  # noqa: E731
    rows = [("stature (units)", stature, None)]
    for name, bone, adult in LANDMARKS:
        rows.append((name, head(bone).z / stature, adult))
    rows.append(("upper arm + forearm", ((head("lowerarm.l") - head("upperarm.l")).length + (head("wrist.l") - head("lowerarm.l")).length) / stature, 0.31))
    rows.append(("thigh : shin", (head("upperleg.l") - head("lowerleg.l")).length / (head("lowerleg.l") - head("foot.l")).length, 1.0))
    return rows


if __name__ == "__main__":
    for body_id in (sys.argv[1:] or ["alexandria-m", "alexandria-f"]):
        print(body_id)
        for name, v, adult in measure(body_id):
            if adult is None:
                print("  %-24s %.3f" % (name, v))
            else:
                print("  %-24s %.3f  adult %.3f%s" % (name, v, adult, "" if abs(v - adult) <= 0.05 * max(adult, 0.2) else "  <-- off"))
