"""WILDLINE fit check: does every piece of dress sit on its body and move with it? Measured,
not judged by eye (docs/dress-fit.md).

    python tools/blender/fit_check.py                      # every body of every home, the table, exit 1 on a failure
    python tools/blender/fit_check.py columbia-m tiber-f   # some bodies
    python tools/blender/fit_check.py --all                # also what is cut from the game, to see whether it fits yet (data/bodies.json, a piece's cutUntilFits)
    python tools/blender/fit_check.py --md docs/dress-fit-table.md   # write the table as well
    npm run check:fit

Each body is built as body_kit builds it (the same code that writes the game's files), stood
in the rest pose and in the clips the game plays (idle, walk, run, a strafe, a slice, a chop,
a spin, the dodges, which go down into a crouch, blocking, casting, aiming, a hit), at the fit build and, for idle and the run, lean and
heavy. Every piece is sampled with points spread over its surface, and each point is measured:

  (deep fails only when more than a twentieth of the piece is sunk.)
  sunk   the point lies inside the body, or under a garment that is worn beneath its piece
         (a cloak under the coat it should hang over). share = how much of the piece is sunk
         deeper than its cloth is thick; deep = how deep the worst twentieth goes.
  float  how far the nearest tenth of the piece is from what it lies on: a piece that touches
         nothing is floating.
  jut    how far the farthest twentieth stands off what it lies on: a collar or a scarf that
         juts out.
  drift  how much a point's distance from the body changes between the rest pose and a clip:
         a piece that does not move with the body.

Lengths are in the kit's units (a body is 2.4 tall; 0.01 is about 7 mm on a person 1.8 m
tall). The limits are LIMITS below, by the kind of piece. Each point is measured from the part
of the body it lies on in the rest pose (the trunk and legs, or an arm): an arm may brush the
trunk's dress, and the chin a collar (a hand through a skirt is the animation's, not the
garment's). Nothing is measured against the head.
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOMES = ["alexandria", "columbia", "cahokia", "lunden", "colonia", "tiber", "khemet", "baghdad", "varanasi", "jiangnan", "kazan", "timbuktu", "edo"]

# clip, where in it (0..1)
POSES = [("Idle", 0.0), ("Walking_A", 0.25), ("Running_A", 0.3), ("Running_A", 0.8), ("Running_Strafe_Left", 0.3),
         ("1H_Melee_Attack_Slice_Horizontal", 0.45), ("2H_Melee_Attack_Chop", 0.4), ("2H_Melee_Attack_Spin", 0.5),
         ("Dodge_Forward", 0.5), ("Dodge_Backward", 0.5), ("Blocking", 0.5), ("Spellcasting", 0.5), ("2H_Ranged_Aiming", 0.5), ("Hit_A", 0.4)]
BUILD_POSES = [("Idle", 0.0), ("Running_A", 0.3)]       # what lean and heavy are also stood in

# What lies over what is the wardrobe's (wardrobe.LAYER): a piece must stay outside every piece
# of a lower layer worn with it.
# The kind of each piece, which sets its limits.
SNUG = ("collar", "scarf", "belt", "sash", "obi", "strap", "wrap", "patch", "armlets", "beads", "chain", "brooch", "badge",
        "buttons", "cuirass", "vest", "gloves", "shoes", "boots", "greaves", "sandals", "puttees")
BULKY = ("furcollar", "roll", "satchel", "pauldrons", "holster", "coil", "sashknot", "toolloop", "bow", "tassel", "disc", "wings", "pteruges")
HANG = ("cloak", "mantle", "cape")                    # hangs from its top: the top is held to the snug limits
NECK = ("collar", "scarf", "furcollar", "beads", "chain", "brooch")
STIFF = ("roll", "wings")             # stiff by nature (a case slung on a strap, starched shoulders): not held to drift

THICK = 0.014          # sunk no deeper than this is the cloth's own thickness
REACH = 0.09           # how far above a point a garment worn beneath is looked for
LIMITS = {
    # kind: (sunk share, sunk deep, float, jut, drift)   None: not held to it
    "cloth": (0.12, 0.045, None, None, None),          # a tunic, a coat, a skirt, trousers, an apron, a tabard
    "snug": (0.15, 0.035, 0.02, 0.07, 0.05),           # lies on the body
    "neck": (0.15, 0.035, 0.02, 0.08, 0.04),            # lies on the neck and shoulders
    "bulky": (0.6, 0.06, 0.035, None, 0.08),           # a solid thing that rests on the body: half of it faces in
    "hang": (0.10, 0.035, 0.03, 0.09, 0.06),           # float, jut and drift are of its top quarter
    "fall": (0.15, 0.04, None, None, None),            # what hangs from headgear below the chin
    "part": (0.15, 0.035, 0.03, 0.09, 0.06),           # a part on a socket (the creator's cloak, an echo at the collar)
}
HARD_SUNK = 0.6        # a solid piece on one bone sits half in the cloth: only held to not being swallowed
PARTS = {"echo-ruff": "socket_throat", "echo-charm": "socket_throat", "echo-gorget": "socket_throat", "trim": "socket_throat"}
COLS = ("sunk", "deep", "float", "jut", "drift")


def kind_of(ptype, sub):
    if sub == "part":
        return "part"
    if sub == "fall":
        return "fall"
    if ptype in HANG:
        return "hang"
    if ptype in NECK:
        return "neck"
    if ptype in BULKY:
        return "bulky"
    if ptype in SNUG:
        return "snug"
    return "cloth"


# ======================================================================================
# One body (in Blender)
# ======================================================================================

def measure(body_id, with_cut=False):
    import bpy
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    sys.path.insert(0, HERE)
    import body_kit as bk
    import wardrobe

    home, sex = body_id.rsplit("-", 1)
    if with_cut:
        wardrobe.WITH_CUT = True
    body = bk.Body(home, sex).build()
    arm = body.r.arm
    D = bk.home_dress(home)
    pieces = wardrobe.pieces_all(D, sex)       # both cuts of the home's dress: a body may wear either (docs/representation-plan.md)
    rng = np.random.default_rng(7)
    scene = bpy.context.scene
    k = body.k

    def wears(p):
        return tuple(p.get("in", wardrobe.TAGS))

    def layer_of(p, hard):
        if p["type"] in ("shoes", "cape"):
            return wardrobe.LAYER[p["type"]]
        return wardrobe.layer_of(D, p.get("sex", sex), p)

    body_ob = body.parts["Body"]
    is_arm_v = np.asarray(body.human.is_arm, dtype=bool)

    # --- the groups to measure: (label, object, vertex spans, layer, chain, wears, kind) ---
    groups = []
    for mesh_name, spans in getattr(body, "dress_spans", {}).items():
        ob = body.parts[mesh_name]
        by = {}
        for name, start, end, chain in spans:
            bits = name.split("__in_")[0].split("_")
            n = int(bits[1])
            # 0: the shoes every body wears unless it goes bare; 99: the cloak the creator offers every body
            p = {"type": "shoes"} if n == 0 else ({"type": "cape", "in": ["plain", "formal"]} if n == 99 else pieces[n - 1])
            sub = "sleeves" if bits[2] == "sleeve" else ""
            weights = getattr(body, "dress_weights", {}).get(name)
            hard = isinstance(weights, str) or p["type"] in wardrobe.PINNED or p["type"] in wardrobe.DANGLE or p["type"] == "beads"
            key = (n, sub)
            other = " (the %s cut)" % p["sex"] if p.get("sex", sex) != sex else ""
            g = by.setdefault(key, {"label": ("%d %s%s%s" % (n, p["type"], " sleeves" if sub else "", other)) if n != 99 else "the creator's cloak", "type": p["type"], "ob": ob, "spans": [], "of": p.get("sex", ""),
                                    "layer": layer_of(p, hard), "arm": chain.startswith("arm") or (isinstance(weights, str) and "arm" in weights),
                                    "wears": wears(p), "kind": kind_of(p["type"], sub), "hard": hard, "cut": bool(p.get("cutUntilFits"))})
            g["spans"].append((start, end))
        groups += list(by.values())
    (hx0, hx1), (hy0, hy1), (hz0, hz1) = body.head_extents()
    for ob in body.r.attached:
        if ob.type == "MESH" and ob.name.startswith("Headgear_"):
            tags = ob.name.split("__in_")[1].split("_") if "__in_" in ob.name else list(wardrobe.TAGS)
            groups.append({"label": "head " + ob.name.split("__in_")[0][9:], "type": ob.name.split("__in_")[0][9:], "ob": ob, "spans": [(0, len(ob.data.vertices))],
                           "layer": 8, "arm": False, "wears": tuple(tags), "kind": "fall", "below": hz0 - 0.01, "rigid": True, "hard": False, "cut": False})
    # a covering over the hair (coverings.py): what of it lies below the chin, on the neck
    for ob in list(body.r.attached) + list(body.r.skinned):
        if ob.type == "MESH" and ob.name.startswith("Cover_"):
            groups.append({"label": "cover " + ob.name[6:], "type": ob.name[6:], "ob": ob, "spans": [(0, len(ob.data.vertices))],
                           "layer": 0, "arm": False, "wears": tuple(wardrobe.TAGS), "kind": "fall", "below": hz0 - 0.01, "rigid": ob in body.r.attached, "hard": False, "cut": False})
    sockets = {o.name: o for o in body.r.attached if o.type == "EMPTY"}
    feats = json.load(open(os.path.join(ROOT, "data", "people-features.json")))["features"]
    cut_parts = {f.get("part") for f in feats.values() if f.get("cutUntilFits")}
    for part, sock in PARTS.items():
        path = os.path.join(ROOT, "game", "assets", "people", "parts", part + ".glb")
        if not os.path.exists(path) or sock not in sockets:
            continue
        if part in cut_parts and not with_cut:      # cut from the game (data/people-features.json): not hung, not measured
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        bpy.context.view_layer.update()
        import bmesh
        bm = bmesh.new()
        for o in new:
            if o.type == "MESH":
                o.data.transform(o.matrix_world)
                bm.from_mesh(o.data)
        me = bpy.data.meshes.new("Part_" + part)
        bm.to_mesh(me)
        bm.free()
        for o in new:
            bpy.data.objects.remove(o)
        o = bpy.data.objects.new("Part_" + part, me)
        bpy.context.collection.objects.link(o)
        o.parent = sockets[sock]
        o.matrix_parent_inverse.identity()
        groups.append({"label": "part " + part, "type": part, "ob": o, "spans": [(0, len(me.vertices))], "layer": 9, "arm": False,
                       "wears": ("plain", "formal"), "kind": "part", "rigid": True, "hard": False, "cut": part in cut_parts})
    bpy.context.view_layer.update()

    # --- sample points on each group, fixed for every pose ---
    def rest_co(ob):
        co = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        return co @ M[:3, :3].T + M[:3, 3]

    for g in groups:
        ob = g["ob"]
        me = ob.data
        me.calc_loop_triangles()
        tris = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", tris)
        tris = tris.reshape(-1, 3)
        keep = np.zeros(len(tris), dtype=bool)
        for s, e in g["spans"]:
            keep |= ((tris >= s) & (tris < e)).all(axis=1)
        tris = tris[keep]
        co = rest_co(ob)
        a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
        area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
        if "below" in g:
            low = (np.stack([a, b, c])[:, :, 2].max(axis=0) < g["below"])
            tris, area = tris[low], area[low]
        if len(tris) == 0 or area.sum() <= 0:
            g["tris"] = None
            continue
        n = int(min(700, max(80, area.sum() / (0.012 ** 2))))
        pick = rng.choice(len(tris), size=n, p=area / area.sum())
        u, v = rng.random(n), rng.random(n)
        flip = u + v > 1
        u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
        g["tris"] = tris[pick]
        g["bary"] = np.stack([1 - u - v, u, v], axis=1)
        g["all_tris"] = tris
    groups = [g for g in groups if g.get("tris") is not None]

    def posed(ob, dg):
        oe = ob.evaluated_get(dg)
        me = oe.to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        oe.to_mesh_clear()
        co = co.reshape(-1, 3)
        M = np.array(oe.matrix_world)
        return co @ M[:3, :3].T + M[:3, 3]

    body_me = body_ob.data
    body_polys = [tuple(p.vertices) for p in body_me.polygons]
    body_face_arm = np.array([all(is_arm_v[i] for i in f) for f in body_polys])
    is_head_v = np.asarray(body.human.is_head, dtype=bool)
    body_face_head = np.array([all(is_head_v[i] for i in f) for f in body_polys])

    def set_build(build):
        for ob in body.r.skinned:
            keys = ob.data.shape_keys
            if keys:
                for kb in keys.key_blocks:
                    if kb.name in ("lean", "heavy"):
                        kb.value = 1.0 if kb.name == build else 0.0
                    elif kb.name != "Basis":
                        kb.value = 0.0      # the other builds and the face's shapes: not drawn here

    def stand(anim, at):
        if anim is None:
            arm.data.pose_position = "REST"
        else:
            arm.data.pose_position = "POSE"
            act = bpy.data.actions.get(anim)
            if arm.animation_data is None:
                arm.animation_data_create()
            arm.animation_data.action = act
            f0, f1 = act.frame_range
            scene.frame_set(int(round(f0 + at * (f1 - f0))))
        bpy.context.view_layer.update()
        return bpy.context.evaluated_depsgraph_get()

    def one_pose(anim, at, rest_gap=None):
        dg = stand(anim, at)
        bco = posed(body_ob, dg)
        # two bodies: the trunk and legs for what is worn on them, the arms for what is worn on
        # the arms. A hand hanging by the hip is not what a sash's knot lies on.
        bpts = [tuple(p) for p in bco]
        whole = BVHTree.FromPolygons(bpts, body_polys)
        bvhs = {False: BVHTree.FromPolygons(bpts, [f for f, a, h in zip(body_polys, body_face_arm, body_face_head) if not a and not h]),
                True: BVHTree.FromPolygons(bpts, [f for f, a in zip(body_polys, body_face_arm) if a])}
        cos = {}
        for g in groups:
            if g["ob"].name not in cos:
                cos[g["ob"].name] = posed(g["ob"], dg)
        out = {}
        gaps = {}
        for g in groups:
            co = cos[g["ob"].name]
            P = (co[g["tris"]] * g["bary"][:, :, None]).sum(axis=1)
            # what is worn beneath this piece, as one surface
            under_pts, under_faces = [], []
            base = 0
            for u in groups:
                # a piece lies on its own cut's pieces and on what both cuts wear; what both wear, on this body's cut
                if u.get("of") and u["of"] != (g.get("of") or sex):
                    continue
                if u is g or u["layer"] >= g["layer"] or not set(u["wears"]) & set(g["wears"]) or not wardrobe.worn_together(g["type"], u["type"]):
                    continue
                if u["arm"] != g["arm"]:
                    continue
                uc = cos[u["ob"].name]
                used = np.unique(u["all_tris"])
                remap = {int(i): base + j for j, i in enumerate(used)}
                under_pts += [tuple(p) for p in uc[used]]
                under_faces += [tuple(remap[int(i)] for i in t) for t in u["all_tris"]]
                base += len(used)
            ubvh = BVHTree.FromPolygons(under_pts, under_faces) if under_faces else None
            sunk = np.zeros(len(P))
            gap = np.zeros(len(P))
            if "on_arm" not in g:       # in the rest pose: which part of the body each point lies on
                g["on_arm"] = [bool(body_face_arm[whole.find_nearest(Vector(p))[2]]) for p in P]
            for i, p in enumerate(P):
                pv = Vector(p)
                loc, nrm, idx, dist = whole.find_nearest(pv)
                d = pv - loc
                inside = d.dot(nrm) < 0.0
                if bool(body_face_arm[idx]) != g["on_arm"][i] or body_face_head[idx]:
                    # the nearest of the body is not the part this point lies on (a hand by the
                    # hip, an arm against the breast, the chin over a collar): a brush, and the
                    # point is measured from its own part
                    loc, nrm, idx, dist = bvhs[g["on_arm"][i]].find_nearest(pv)
                    d = pv - loc
                    inside = False
                    if d.dot(nrm) < 0.0:
                        d = nrm * dist
                s = dist if inside else 0.0
                gp = 0.0 if inside else dist
                if ubvh is not None:
                    out_dir = nrm if (inside or dist < 1e-6) else d.normalized()
                    o = pv + out_dir * 1e-4
                    far = 0.0
                    left = REACH
                    while left > 0.0:
                        hit = ubvh.ray_cast(o, out_dir, left)
                        if hit[0] is None:
                            break
                        far += hit[3] + 1e-4
                        left -= hit[3] + 1e-4
                        o = hit[0] + out_dir * 1e-4
                    if far > 0.0:
                        s = max(s, far)
                    un = ubvh.find_nearest(pv)
                    if un[0] is not None:
                        gp = min(gp, un[3]) if not inside else 0.0
                    if far > 0.0:
                        gp = 0.0
                sunk[i] = s
                gap[i] = gp
            gaps[g["label"]] = gap
            sel = np.ones(len(P), dtype=bool)
            if g["kind"] == "hang":         # float, jut and drift of what it hangs from: its top quarter
                z = (rest_z[g["label"]] if rest_z else P[:, 2])
                sel = z > np.quantile(z, 0.75)
            row = {"sunk": float((sunk > THICK).mean()), "deep": float(np.quantile(sunk, 0.95)),
                   "float": float(np.quantile(gap[sel], 0.10)), "jut": float(np.quantile(gap[sel], 0.95))}
            if rest_gap is not None:
                row["drift"] = float(np.quantile(np.abs(gap - rest_gap[g["label"]])[sel], 0.95))
            out[g["label"]] = row
        return out, gaps, {g["label"]: (cos[g["ob"].name][g["tris"]] * g["bary"][:, :, None]).sum(axis=1)[:, 2] for g in groups}

    rest_z = None
    set_build("fit")
    _, _, rest_z = one_pose(None, 0.0)
    rest_rows, rest_gap, _ = one_pose(None, 0.0)
    result = {g["label"]: {"type": g["type"], "kind": g["kind"], "wears": list(g["wears"]), "hard": g["hard"], "cut": g["cut"], "poses": {"rest": rest_rows[g["label"]]}} for g in groups}
    for anim, at in POSES:
        rows, _, _ = one_pose(anim, at, rest_gap)
        for label, row in rows.items():
            result[label]["poses"]["%s@%.2f" % (anim, at)] = row
    for build in ("lean", "heavy"):
        set_build(build)
        _, bgap, _ = one_pose(None, 0.0)
        for anim, at in BUILD_POSES:
            rows, _, _ = one_pose(anim, at, bgap)
            for label, row in rows.items():
                result[label]["poses"]["%s@%.2f %s" % (anim, at, build)] = row
    return result


# ======================================================================================
# The table
# ======================================================================================

def judge(piece):
    """The worst of each measure over the poses, where, and what fails."""
    lim = list(LIMITS[piece["kind"]])
    if piece.get("hard") and piece["kind"] != "bulky":
        lim[0] = max(lim[0], HARD_SUNK)
        lim[1] = max(lim[1], 0.06)
    worst = {}
    for pose, row in piece["poses"].items():
        for c in COLS:
            if c in row and (c not in worst or row[c] > worst[c][0]):
                worst[c] = (row[c], pose)
    if piece["type"] in STIFF:
        lim[4] = None
    fails = [c for c, l in zip(COLS, lim) if l is not None and c in worst and worst[c][0] > l]
    if "deep" in fails and worst["sunk"][0] <= 0.06:        # about a twentieth of a piece or less: an edge, not a fault
        fails.remove("deep")
    return worst, fails


def table(results, md=False):
    lines = []
    head = ("body", "piece", "worn", "kind", "sunk", "deep", "float", "jut", "drift", "verdict", "worst in")
    rows = []
    bad = 0
    for body_id in sorted(results, key=lambda b: (HOMES.index(b.rsplit("-", 1)[0]), b)):
        for label, piece in sorted(results[body_id].items(), key=lambda kv: (not kv[0][0].isdigit(), int(kv[0].split()[0]) if kv[0][0].isdigit() else 0, kv[0])):
            worst, fails = judge(piece)
            w = piece["wears"]
            worn = "always" if len(w) == 3 else "+".join(w)
            verdict = ("CUT " if piece.get("cut") else "") + ("FAIL " + ",".join(fails) if fails else "ok")
            if fails and not piece.get("cut"):
                bad += 1
            where = worst[fails[0]][1] if fails else ""
            rows.append((body_id, label, worn, piece["kind"], "%.0f%%" % (100 * worst["sunk"][0]), "%.3f" % worst["deep"][0], "%.3f" % worst["float"][0],
                         "%.3f" % worst["jut"][0], "%.3f" % worst.get("drift", (0, ""))[0], verdict, where))
    if md:
        lines.append("| " + " | ".join(head) + " |")
        lines.append("|" + "---|" * len(head))
        lines += ["| " + " | ".join(r) + " |" for r in rows]
    else:
        wid = [max(len(str(x)) for x in col) for col in zip(head, *rows)] if rows else [len(h) for h in head]
        fmt = "  ".join("%%-%ds" % w for w in wid)
        lines.append(fmt % head)
        lines += [fmt % r for r in rows]
    return "\n".join(lines), bad, len(rows)


def main():
    args = sys.argv[1:]
    if "--one" in args:
        i = args.index("--one")
        res = measure(args[i + 1], with_cut="--all" in args)
        json.dump(res, open(args[i + 2], "w"))
        return 0
    md_path = args[args.index("--md") + 1] if "--md" in args else None
    json_path = args[args.index("--json") + 1] if "--json" in args else None
    jobs = int(args[args.index("--jobs") + 1]) if "--jobs" in args else 2
    skip = set()
    for flag in ("--md", "--json", "--jobs"):
        if flag in args:
            skip |= {args.index(flag), args.index(flag) + 1}
    ids = [a for i, a in enumerate(args) if i not in skip and not a.startswith("--")] or ["%s-%s" % (h, s) for h in HOMES for s in "mf"]
    tmp = os.environ.get("WILDLINE_FIT_TMP") or os.path.join(ROOT, ".godot", "fit")
    os.makedirs(tmp, exist_ok=True)
    results, running, queue = {}, [], list(ids)
    failed = []
    while queue or running:
        while queue and len(running) < jobs:
            b = queue.pop(0)
            out = os.path.join(tmp, b + ".json")
            if os.path.exists(out):
                os.remove(out)
            cmd = [sys.executable, os.path.abspath(__file__), "--one", b, out] + (["--all"] if "--all" in args else [])
            running.append((b, out, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
        b, out, proc = running.pop(0)
        log = proc.communicate()[0]
        if proc.returncode != 0 or not os.path.exists(out):
            failed.append(b)
            print("fit: %s could not be built\n%s" % (b, log[-3000:]), file=sys.stderr)
            continue
        results[b] = json.load(open(out))
        print("fit: measured %s (%d pieces)" % (b, len(results[b])), file=sys.stderr)
    text, bad, total = table(results)
    print(text)
    if json_path:
        json.dump(results, open(json_path, "w"), indent=1)
    if md_path:
        mdt, _, _ = table(results, md=True)
        open(md_path, "w").write("# The dress fit table\n\nWritten by `npm run check:fit -- --md %s` (tools/blender/fit_check.py; what the columns mean and the limits: docs/dress-fit.md). Lengths in the kit's units: 0.01 is about 7 mm on a person.\n\n%s\n" % (os.path.relpath(md_path, ROOT), mdt))
    if failed:
        print("fit: could not build %s" % ", ".join(failed))
        return 2
    if bad:
        print("fit: %d of %d pieces do not fit" % (bad, total))
        return 1
    print("fit: all good (%d pieces on %d bodies)" % (total, len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
