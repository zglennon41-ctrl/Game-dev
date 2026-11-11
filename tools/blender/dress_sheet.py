"""WILDLINE dress sheet: the dress of the homes drawn quickly, with no game and no export, to
design by (docs/bodies-plan.md, "Dress as culture"). Each body is built as body_kit builds it,
stood in a clip's pose, and drawn flat from the front and from behind; the same again as white
shapes on black (the test of a silhouette) and blurred (the test of a colour chord).

    python tools/blender/dress_sheet.py OUT_DIR [home ...] [wear=plain|formal|master] [anim=Idle] [at=0.0] [sex=m|f]

It writes OUT_DIR/<home>-<sex>-<wear>.png for each body (front and back), and sheet.png,
mask.png and blur.png of every card found in OUT_DIR for that wear. The game's own picture
of the same is game/tests/dress_sheet.tscn.
"""
import json
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import body_kit as bk  # noqa: E402
import style  # noqa: E402
import wardrobe  # noqa: E402

W, H = 260, 470          # one view
SS = 2                   # drawn larger and brought down, for soft edges
BACK = (22, 20, 19)


def _worn(name, wear):
    if "__in_" not in name:
        return True
    return wear in name[name.index("__in_") + 5:].split("_")


def triangles(body, wear, anim, at, skin):
    """Every triangle of the dressed body in its pose: (points (n, 3, 3), colours (n, 3) sRGB)."""
    r = body.r
    arm = r.arm
    arm.data.pose_position = "POSE"
    act = bpy.data.actions.get(anim)
    scene = bpy.context.scene
    if act is not None:
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = act
        f0, f1 = act.frame_range
        scene.frame_set(int(round(f0 + at * (f1 - f0))))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts, cols = [], []
    for ob in list(r.skinned) + list(r.attached):
        if ob.type != "MESH":
            continue
        n = ob.name
        if n.startswith("Hair_") and not n.startswith("Hair_crop" if body.sex == "m" else "Hair_tail"):
            continue
        if n.startswith("Beard_") or not _worn(n, wear):
            continue
        if n.startswith("Hair_") and not n.endswith("_fall") and any(o.name.startswith("Headgear_") and _worn(o.name, wear) and "headband" not in o.name for o in r.attached):
            continue
        oe = ob.evaluated_get(dg)
        me = oe.to_mesh()
        me.calc_loop_triangles()
        M = np.array(oe.matrix_world)
        co = np.array([v.co[:] for v in me.vertices])
        co = co @ M[:3, :3].T + M[:3, 3]
        mcol = []
        for m in me.materials:
            c = (0.5, 0.5, 0.5)
            if m is not None:
                if m.name.split(".")[0] in ("skin",):
                    c = skin
                elif m.name.split(".")[0] == "lips":
                    c = tuple(x * 0.82 for x in skin)
                else:
                    bsdf = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
                    c = style.to_srgb(bsdf.inputs["Base Color"].default_value[:3]) if bsdf else (0.5, 0.5, 0.5)
            mcol.append(c)
        for t in me.loop_triangles:
            pts.append(co[list(t.vertices)])
            cols.append(mcol[t.material_index] if t.material_index < len(mcol) else (0.5, 0.5, 0.5))
        oe.to_mesh_clear()
    return np.array(pts), np.array(cols)


def draw(pts, cols, yaw, height):
    """One view, flat: turned by yaw about the body's axis, lit from the upper left, nearest last."""
    from PIL import Image, ImageDraw
    c, s = math.cos(yaw), math.sin(yaw)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    p = pts @ R.T
    nrm = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    ln = np.linalg.norm(nrm, axis=1)
    ok = ln > 1e-12
    nrm[ok] /= ln[ok][:, None]
    facing = nrm[:, 1] < 0.05            # the eye is at -y
    L = np.array([-0.45, -0.6, 0.66])
    L /= np.linalg.norm(L)
    shade = 0.42 + 0.62 * np.clip(nrm @ L, 0, 1)
    scale = (H * SS * 0.9) / height
    order = np.argsort(-p[:, :, 1].mean(axis=1))      # far to near
    img = Image.new("RGB", (W * SS, H * SS), BACK)
    mask = Image.new("L", (W * SS, H * SS), 0)
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mask)
    for i in order:
        if not (ok[i] and facing[i]):
            continue
        xy = [(W * SS / 2 + q[0] * scale, H * SS * 0.96 - q[2] * scale) for q in p[i]]
        col = tuple(int(max(0, min(255, 255 * v * shade[i]))) for v in cols[i])
        d.polygon(xy, fill=col)
        dm.polygon(xy, fill=255)
    return img.resize((W, H), Image.LANCZOS), mask.resize((W, H), Image.LANCZOS)


def card(home, sex, wear, anim, at, out):
    from PIL import Image
    bpy.ops.wm.read_factory_settings(use_empty=True)
    body = bk.Body(home, sex).build()
    tones = json.load(open(os.path.join(bk.ROOT, "data", "creation.json")))["look"]["skinTones"]
    pal = json.load(open(os.path.join(bk.ROOT, "data", "bodies.json")))["homes"][home].get("palette", ["olive"])
    skin = tuple(tones[pal[len(pal) // 2]])
    pts, cols = triangles(body, wear, anim, at, skin)
    tris = {o.name: len(o.data.polygons) for o in body.r.skinned if o.name.startswith("Dress_")}
    img = Image.new("RGB", (W * 2, H), BACK)
    msk = Image.new("L", (W * 2, H), 0)
    for i, yaw in enumerate((-0.45, math.pi + 0.6)):
        a, b = draw(pts, cols, yaw, 2.5)
        img.paste(a, (i * W, 0))
        msk.paste(b, (i * W, 0))
    img.save(os.path.join(out, "%s-%s-%s.png" % (home, sex, wear)))
    msk.save(os.path.join(out, "%s-%s-%s.mask.png" % (home, sex, wear)))
    print("[dress_sheet]", home, sex, wear, "faces", tris, flush=True)


def sheet(out, wear):
    """Every card of one wear in OUT_DIR, a column a home: the men over the women."""
    from PIL import Image, ImageFilter
    homes = [h for h in bk.HOMES if os.path.exists(os.path.join(out, "%s-m-%s.png" % (h, wear))) or os.path.exists(os.path.join(out, "%s-f-%s.png" % (h, wear)))]
    if not homes:
        return
    for kind, mode in (("", "RGB"), (".mask", "L")):
        big = Image.new(mode, (W * 2 * len(homes), H * 2), BACK if mode == "RGB" else 0)
        for i, h in enumerate(homes):
            for j, sex in enumerate(("m", "f")):
                p = os.path.join(out, "%s-%s-%s%s.png" % (h, sex, wear, kind))
                if os.path.exists(p):
                    big.paste(Image.open(p), (i * W * 2, j * H))
        big.save(os.path.join(out, ("sheet-%s.png" if not kind else "mask-%s.png") % wear))
        if not kind:
            big.filter(ImageFilter.GaussianBlur(14)).save(os.path.join(out, "blur-%s.png" % wear))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if "=" not in a]
    kv = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    out = args[0]
    os.makedirs(out, exist_ok=True)
    wear = kv.get("wear", "plain")
    for home in args[1:]:
        for sex in ([kv["sex"]] if "sex" in kv else ["m", "f"]):
            card(home, sex, wear, kv.get("anim", "Idle"), float(kv.get("at", "0.0")), out)
    sheet(out, wear)
