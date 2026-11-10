"""WILDLINE wardrobe: each home's outfit (data/bodies.json, dress) built on a body of the body
kit. Garments are shells on the body's own rings in the home's colours, with trim bands at
hem, cuff or collar, stripes, cuffs, wraps, scarves and gloves; rigid pieces (buttons, a
badge, a sash's knot and tails, tools at the belt, pauldrons, pteruges) are built once with
the fit body and hung from their bones; the headgear (cap, hat, turban, fur hat, scholar's
cap, hood, headband, helm, with a peak, a band, a jewel, a crest or goggles) hangs from the
head. The data is the design: every piece, colour and trim is the owner's to change.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import people_kit as pk


def _sphere_bm(c, r):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return bm


def _ring_bm(c, r, thick, n=16):
    """A ring in the x-z plane (facing -y) about c: goggles, buckles."""
    pts = [c + Vector((r * math.cos(2 * math.pi * k / n), 0, r * math.sin(2 * math.pi * k / n))) for k in range(n + 1)]
    return pk._tube_bm(pts, [thick] * (n + 1), segments=6)


def dress_pieces(body, objs, build, slot):
    """The garments for one build into objs (named Dress_<n>_<type>), their chains into
    body.chains, the rigid pieces into body.dress_rigid (fit build only)."""
    import body_kit as bk
    D = bk.home_dress(body.home)
    if not D:
        return
    sex = body.sex
    colors = D.get("colors", {})
    mats = {}
    for cname, c in colors.items():
        mats[cname] = pk._material("dress_%s_%s" % (body.home, cname), tuple(c) + (1,), rough=0.9 if cname != "metal" else 0.45)
    tr = body.rings("trunk", build)
    ar = body.rings("arm", build)
    lr = body.rings("leg", build)
    human = body.human if body.HUMAN else None
    z_arm = body.joint("upperarm.l", "z")
    y_arm = body.joint("upperarm.l", "y") if human else 0.0
    top_i = 9 if human else 8      # the human's garments close at the base of the neck

    def fy(i):
        """The front of trunk ring i."""
        return tr[i][3] - tr[i][2]

    def low(z):
        """A height written for the old legs (a hem), on this body's."""
        return human.map_z(z / body.k) if human else z
    x_leg = body.joint("upperleg.l", "x")
    k = body.k
    if not hasattr(body, "chains"):
        body.chains = {}
    if not hasattr(body, "dress_rigid"):
        body.dress_rigid = []
    n = 0

    def put(name, ob, chain, cname, trim=None, fit=True):
        ob.data.materials.clear()
        ob.data.materials.append(mats.get(cname, body.mats["tunic"]))
        ob.data.materials.append(mats.get(trim, mats.get(cname, body.mats["tunic"])))
        objs[name] = ob
        body.chains[name] = chain
        if human and fit:
            human.refine(ob)
            human.conform(ob, chain, build)

    def band_loft(name, rings, trim_rings=()):
        return bk.loft(name, rings, (lambda i: 1 if i in trim_rings else 0))

    def sleeves(kk, cname, wide=False, trim=None, cuffs=None):
        if kk <= 0:
            return
        for side, sign in (("l", 1), ("r", -1)):
            rings = []
            for i, (x, hd, hz) in enumerate(ar[:kk + 1]):
                g = 0.02 + (0.03 if wide and i == kk else 0.0)
                rings.append((x, hd + g, hz + g))
            banded = bool(cuffs or trim)
            if banded:
                x_end, hd_e, hz_e = rings[-1]
                rings.append((x_end + 0.03, hd_e + 0.006, hz_e + 0.006))
            ob = band_loft("Dress_%d_sleeve_%s" % (n, side), bk.rings_x(rings, z_arm, sign, y_arm), (len(rings) - 2,) if banded else ())
            put("Dress_%d_sleeve_%s" % (n, side), ob, "arm." + side, cname, cuffs or trim)

    def rigid(ob, bone, cname):
        ob.data.materials.clear()
        ob.data.materials.append(mats.get(cname, body.mats["tunic"]))
        if build == "fit":
            body.dress_rigid.append((ob, bone))
        else:
            bpy.data.objects.remove(ob)

    for piece in D.get("pieces", []):
        n += 1
        t, cname = piece["type"], piece["color"]
        trim = piece.get("trim")
        hem = low(float(piece.get("hem", 0.5)) * k)
        if t in ("tunic", "vest"):
            rings = bk.rings_z(bk._shell(tr, 0.024, 1, top_i))
            ob = band_loft("Dress_%d_%s" % (n, t), rings, (0,) if trim else ())
            put("Dress_%d_%s" % (n, t), ob, "trunk", cname, trim)
            if t == "tunic":
                sleeves(int(piece.get("sleeves", 2)), cname, bool(piece.get("wide", False)), trim, piece.get("cuffs"))
        elif t in ("coat", "robe", "kaftan"):
            top = bk._shell(tr, 0.026, 2, top_i)
            z2, hw2, hd2, yo2 = top[0]
            flare = {"coat": 1.25, "robe": 1.15, "kaftan": 1.3}[t]
            skirt = bk._skirt(z2, hw2, hd2, yo2, hem, flare)
            all_rings = skirt[::-1][:-1] + top
            ob = band_loft("Dress_%d_%s" % (n, t), bk.rings_z(all_rings), (0,) if trim else ())
            put("Dress_%d_%s" % (n, t), ob, "trunk", cname, trim)
            sleeves(int(piece.get("sleeves", 6)), cname, bool(piece.get("wide", t == "robe")), trim, piece.get("cuffs"))
        elif t in ("kilt", "wrapskirt"):
            z2, hw2, hd2, yo2 = tr[1]
            rings = bk._skirt(z2, hw2 + 0.014, hd2 + 0.014, yo2, hem, 1.2)[::-1]
            stripes = piece.get("stripes")
            if stripes:
                ob = bk.loft("Dress_%d_%s" % (n, t), bk.rings_z(rings), (lambda i: i % 2))
                put("Dress_%d_%s" % (n, t), ob, "trunk", cname, stripes)
            else:
                ob = band_loft("Dress_%d_%s" % (n, t), bk.rings_z(rings), (0,) if trim else ())
                put("Dress_%d_%s" % (n, t), ob, "trunk", cname, trim)
        elif t == "cuirass":
            ob = band_loft("Dress_%d_cuirass" % n, bk.rings_z(bk._shell(tr, 0.03, 4, top_i)), (0,) if trim else ())
            put("Dress_%d_cuirass" % n, ob, "trunk", cname, trim)
        elif t == "apron":
            z_hi = tr[6][0]
            z_lo = low(0.6 * k)
            w = tr[3][1] + 0.02
            ob = pk._bm_object("Dress_%d_apron" % n, pk._box_bm(Vector((-w, fy(3) - 0.035, z_lo)), Vector((w, fy(3) + 0.0, z_hi)), taper=(1.1, 1.0)), body.mats["tunic"])
            put("Dress_%d_apron" % n, ob, "trunk", cname)
        elif t == "hakama":
            for side, sign in (("l", 1), ("r", -1)):
                rings = [(z, hw * 1.6 + 0.02, hd * 1.5 + 0.02) for z, hw, hd in lr[:6]]
                ob = bk.loft("Dress_%d_hakama_%s" % (n, side), [(Vector((sign * x_leg, 0, 0)) + c, u, v) for c, u, v in bk.rings_z(rings)])
                put("Dress_%d_hakama_%s" % (n, side), ob, "leg." + side, cname)
        elif t in ("greaves", "boots", "sandals"):
            for side, sign in (("l", 1), ("r", -1)):
                lo_i = 4 if t != "sandals" else 5
                rings = [(z, hw + 0.012, hd + 0.012) for z, hw, hd in lr[lo_i:]]
                banded = t == "boots" and bool(trim or piece.get("cuffs"))
                if banded:
                    z_top, hw_t, hd_t = rings[0]
                    rings = [(z_top + 0.04 * k, hw_t + 0.01, hd_t + 0.01)] + rings
                ob = band_loft("Dress_%d_%s_%s" % (n, t, side), [(Vector((sign * x_leg, 0, 0)) + c, u, v) for c, u, v in bk.rings_z(rings)], (0,) if banded else ())
                put("Dress_%d_%s_%s" % (n, t, side), ob, "leg." + side, cname, trim or piece.get("cuffs"))
        elif t in ("belt", "sash", "obi"):
            z2, hw2, hd2, yo2 = tr[3]
            h = {"belt": 0.03, "sash": 0.07, "obi": 0.09}[t]
            stripes = piece.get("stripes")
            rings = [(z2 - h + (2 * h) * i / 4.0, hw2 + 0.02, hd2 + 0.02, yo2) for i in range(5)]
            ob = bk.loft("Dress_%d_%s" % (n, t), bk.rings_z(rings), (lambda i: i % 2) if stripes else None)
            put("Dress_%d_%s" % (n, t), ob, "trunk", cname, stripes)
        elif t == "collar":
            z2, hw2, hd2, yo2 = tr[9]
            w = piece.get("wide", 1.0)
            wide = (1.8 if w else 1.0) if isinstance(w, bool) else float(w)
            g = 0.03 * wide
            if human:
                # cut from the body: a band at the neck's base, out over the shoulders when it is broad
                z2, hw2 = body.rings("trunk", "fit")[9][:2]      # the cut is the fit body's, on every build
                ob = human.shell("Dress_%d_collar" % n, human.neck_mask(z2 - 0.045 * wide * k, z2 + 0.03 * k, hw2 + 0.035 * k + 0.11 * (wide - 1) * k), build, 0.014 * k)
                put("Dress_%d_collar" % n, ob, "trunk", cname, fit=False)
            else:
                ob = bk.loft("Dress_%d_collar" % n, bk.rings_z([(z2 - 0.05 * wide, hw2 + g + 0.04 * (wide - 1), hd2 + g + 0.04 * (wide - 1), yo2), (z2 + 0.05, hw2 + 0.02, hd2 + 0.02, yo2)]))
                put("Dress_%d_collar" % n, ob, "trunk", cname)
        elif t == "scarf":
            z2, hw2, hd2, yo2 = tr[9]
            if human:
                zf, hwf = body.rings("trunk", "fit")[9][:2]
                ring = human.shell("Dress_%d_scarf" % n, human.neck_mask(zf - 0.05 * k, zf + 0.035 * k, hwf + 0.05 * k), build, 0.024 * k)
                put("Dress_%d_scarf" % n, ring, "trunk", cname, fit=False)
            else:
                ring = bk.loft("Dress_%d_scarf" % n, bk.rings_z([(z2 - 0.04, hw2 + 0.035, hd2 + 0.035, yo2), (z2 + 0.03, hw2 + 0.03, hd2 + 0.03, yo2)]))
                put("Dress_%d_scarf" % n, ring, "trunk", cname)
            tail = pk._bm_object("Dress_%d_scarf_tail" % n, pk._box_bm(Vector((0.02, fy(7) - 0.055, tr[5][0])), Vector((0.1, fy(7) - 0.03, z2 - 0.03)), taper=(1.2, 1.0)), body.mats["tunic"])
            put("Dress_%d_scarf_tail" % n, tail, "trunk", cname, fit=False)
        elif t == "wrap":
            z_hi, z_lo = tr[8][0], tr[2][0]
            us = [i / 8.0 for i in range(9)] if human else (0.0, 0.25, 0.5, 0.75, 1.0)
            pts = []
            for u in us:
                x, z = 0.14 * (1 - u) - 0.16 * u, z_hi * (1 - u) + z_lo * u
                y = (human.front_y(x, z) - 0.012) if human else (fy(7) * (1 - u) + fy(2) * u) - 0.03
                pts.append(Vector((x, y, z)))
            ob = pk._bm_object("Dress_%d_wrap" % n, pk._tube_bm(pts, [0.04 if human else 0.045] * len(pts), segments=8), body.mats["tunic"])
            pk._smooth(ob)
            put("Dress_%d_wrap" % n, ob, "trunk", cname, fit=False)
        elif t == "gloves":
            x_w = body.joint("wrist.l", "x")
            for side, sign in (("l", 1), ("r", -1)):
                rings = [(x_w - 0.03, 0.045, 0.04), (x_w + 0.03, 0.05, 0.03), (x_w + 0.13, 0.055, 0.028), (x_w + 0.18, 0.035, 0.02)]
                ob = bk.loft("Dress_%d_glove_%s" % (n, side), bk.rings_x(rings, z_arm, sign, y_arm))
                put("Dress_%d_glove_%s" % (n, side), ob, "arm." + side, cname)
        # --- rigid pieces, hung from bones ---
        elif t == "buttons":
            z_top, z_bot = tr[7][0], tr[3][0]
            count = int(piece.get("count", 5))
            for i in range(count):
                u = i / max(1, count - 1)
                z = z_top * (1 - u) + z_bot * u
                front = (human.front_y(0.0, z) if human else fy(7 if u < 0.5 else 3))
                ob = pk._bm_object("Dress_%d_button_%d" % (n, i), _sphere_bm(Vector((0.0, front - 0.03, z)), 0.014), body.mats["tunic"])
                rigid(ob, "chest" if u < 0.5 else "spine", cname)
        elif t == "badge":
            z2 = tr[7][0]
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.025, radius2=0.025, depth=0.012)
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
            z2 = tr[6][0] if human else z2
            bmesh.ops.translate(bm, vec=Vector((0.09, (human.front_y(0.09, z2) if human else fy(7)) - 0.032, z2)), verts=bm.verts)
            ob = pk._bm_object("Dress_%d_badge" % n, bm, body.mats["tunic"])
            rigid(ob, "chest", cname)
        elif t == "sashknot":
            z2, hw2, hd2, yo2 = tr[3]
            knot = pk._bm_object("Dress_%d_knot" % n, pk._box_bm(Vector((hw2 - 0.01, yo2 - 0.03, z2 - 0.03)), Vector((hw2 + 0.06, yo2 + 0.04, z2 + 0.04))), body.mats["tunic"])
            rigid(knot, "spine", cname)
            for i, dx in enumerate((0.0, 0.035)):
                tail = pk._bm_object("Dress_%d_tail_%d" % (n, i), pk._box_bm(Vector((hw2 + dx, yo2 - 0.01, z2 - 0.3 - 0.06 * i)), Vector((hw2 + 0.03 + dx, yo2 + 0.02, z2 - 0.02))), body.mats["tunic"])
                rigid(tail, "spine", cname)
        elif t == "toolloop":
            z2, hw2, hd2, yo2 = tr[3]
            for i, (r, h) in enumerate(((0.012, 0.1), (0.009, 0.14))):
                bm = bmesh.new()
                bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r, depth=h)
                bmesh.ops.translate(bm, vec=Vector((-hw2 - 0.02 - 0.03 * i, yo2 + 0.01, z2 - h / 2)), verts=bm.verts)
                ob = pk._bm_object("Dress_%d_tool_%d" % (n, i), bm, body.mats["tunic"])
                rigid(ob, "spine", cname)
        elif t == "pauldrons":
            x_s = body.joint("upperarm.l", "x")
            for side, sign in (("l", 1), ("r", -1)):
                bm = bmesh.new()
                bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.095)
                bmesh.ops.scale(bm, vec=(1.0, 0.95, 0.7), verts=bm.verts)
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, -0.01), plane_no=(0, 0, 1), clear_inner=True)
                bmesh.ops.translate(bm, vec=Vector((sign * (x_s + 0.06), y_arm, z_arm + 0.03)), verts=bm.verts)
                ob = pk._bm_object("Dress_%d_pauldron_%s" % (n, side), bm, body.mats["tunic"])
                pk._smooth(ob)
                rigid(ob, "upperarm." + side, cname)
        elif t == "pteruges":
            z2, hw2, hd2, yo2 = tr[2]
            count = int(piece.get("count", 10))
            for i in range(count):
                a = 2 * math.pi * (i + 0.5) / count
                cx, cy = (hw2 + 0.025) * math.cos(a), (hd2 + 0.025) * math.sin(a) + yo2
                strip = pk._bm_object("Dress_%d_strip_%d" % (n, i), pk._box_bm(Vector((-0.02, -0.006, -0.22 * k)), Vector((0.02, 0.006, 0.0)), taper=(0.9, 1.0)), body.mats["tunic"])
                strip.rotation_euler = (0, 0, math.atan2(math.cos(a), -math.sin(a)) + math.pi / 2)
                strip.location = Vector((cx, cy, z2))
                bpy.context.view_layer.update()
                strip.data.transform(strip.matrix_world)
                strip.matrix_world = Matrix.Identity(4)
                rigid(strip, "hips", cname)

    # --- shoes: over the feet unless the home goes in sandals -----------------------
    if human and not any(p.get("type") == "sandals" for p in D.get("pieces", [])):
        cname = next((p["color"] for p in D.get("pieces", []) if p.get("type") in ("boots", "greaves")), None)
        for name, ob in human.shoes(build, mats.get(cname, body.mats["boots"])).items():
            objs[name] = ob
            body.chains[name] = "leg." + name[-1]


def headgear(body):
    """The home's headgear, if any, hung from the head bone: Headgear_<type>, with a band or a
    peak in the trim colour when the data names one, goggles or a crest if asked."""
    import body_kit as bk
    D = bk.home_dress(body.home)
    hg = D.get("headgear")
    if not hg:
        return []
    (x0, x1), (y0, y1), (z0, z1) = body.head_extents()
    hw, hd, hh = (x1 - x0) / 2, (y1 - y0) / 2, z1 - z0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c = Vector((cx, cy, z0 + hh * 0.62))
    colors = D["colors"]

    def mat_of(cn):
        return pk._material("dress_%s_%s" % (body.home, cn), tuple(colors.get(cn, [0.3, 0.3, 0.3])) + (1,), rough=0.9 if cn != "metal" else 0.45)
    mat = mat_of(hg["color"])
    trim = mat_of(hg["trim"]) if hg.get("trim") else mat
    t = hg["type"]
    out = []

    def ring(name, z, rx, ry, thick, m):
        pts = []
        nn = 28
        for kk in range(nn + 1):
            a = 2 * math.pi * kk / nn
            pts.append(Vector((cx + rx * math.cos(a), cy + ry * math.sin(a), z)))
        ob = pk._bm_object(name, pk._tube_bm(pts, [thick] * (nn + 1), segments=8), m)
        pk._smooth(ob)
        return ob

    def dome(name, centre, rx, ry, rz, cut_z, tilt, m):
        ob = pk._bm_object(name, pk._cap_bm(centre, rx, ry, rz, cut_z, tilt), m)
        pk._smooth(ob)
        return ob

    if t == "cap":
        out.append(dome("Headgear_cap", c, hw * 1.12, hd * 1.1, hh * 0.46, z0 + hh * 0.72, 0.1, mat))
        if hg.get("peak", False):
            out.append(pk._bm_object("Headgear_cap_peak", pk._box_bm(Vector((cx - hw * 0.8, y0 - 0.08, z0 + hh * 0.7)), Vector((cx + hw * 0.8, y0 + 0.02, z0 + hh * 0.72)), taper=(0.6, 1.0)), trim))
    elif t == "hat":
        out.append(dome("Headgear_hat", Vector((cx, cy, c.z + hh * 0.05)), hw * 1.1, hd * 1.08, hh * 0.55, z0 + hh * 0.7, 0.0, mat))
        brim = bmesh.new()
        bmesh.ops.create_cone(brim, cap_ends=True, segments=24, radius1=hw * 1.9, radius2=hw * 1.9, depth=0.01)
        bmesh.ops.scale(brim, vec=(1.0, hd / hw, 1.0), verts=brim.verts)
        bmesh.ops.translate(brim, vec=Vector((cx, cy, z0 + hh * 0.7)), verts=brim.verts)
        out.append(pk._bm_object("Headgear_hat_brim", brim, mat))
        out.append(ring("Headgear_hat_band", z0 + hh * 0.76, hw * 1.11, hd * 1.09, 0.012, trim))
    elif t == "turban":
        for i, (r, dz) in enumerate(((1.25, 0.7), (1.28, 0.82), (1.12, 0.94))):
            out.append(ring("Headgear_turban_%d" % i, z0 + hh * dz, hw * r * 0.9, hd * r * 0.9, hw * 0.3, mat if i != 1 else trim))
        out.append(dome("Headgear_turban_top", Vector((cx, cy, c.z + hh * 0.1)), hw * 1.05, hd * 1.02, hh * 0.45, z0 + hh * 0.9, 0.0, mat))
        if hg.get("jewel", False):
            out.append(pk._bm_object("Headgear_turban_jewel", _sphere_bm(Vector((cx, y0 - hw * 0.25, z0 + hh * 0.84)), 0.02), mat_of("metal") if "metal" in colors else trim))
    elif t == "furhat":
        out.append(dome("Headgear_furhat", Vector((cx, cy, c.z + hh * 0.22)), hw * 1.28, hd * 1.22, hh * 0.62, z0 + hh * 0.66, 0.0, mat))
        out.append(ring("Headgear_furhat_band", z0 + hh * 0.7, hw * 1.3, hd * 1.24, 0.025, trim))
    elif t == "scholarcap":
        out.append(dome("Headgear_scholarcap", c, hw * 1.1, hd * 1.08, hh * 0.42, z0 + hh * 0.74, 0.0, mat))
        out.append(pk._bm_object("Headgear_scholarcap_board", pk._box_bm(Vector((cx - hw * 1.25, cy - hd * 1.05, z1 - 0.012)), Vector((cx + hw * 1.25, cy + hd * 1.05, z1 + 0.012))), trim))
    elif t == "hood":
        out.append(dome("Headgear_hood", Vector((cx, cy + 0.01, c.z)), hw * 1.25, hd * 1.2, hh * 0.6, z0 + hh * 0.3, 0.5, mat))
    elif t == "headband":
        out.append(ring("Headgear_headband", z0 + hh * 0.72, hw * 1.08, hd * 1.06, 0.014, mat))
    elif t == "helm":
        out.append(dome("Headgear_helm", c, hw * 1.15, hd * 1.12, hh * 0.5, z0 + hh * 0.6, 0.0, mat))
        out.append(ring("Headgear_helm_rim", z0 + hh * 0.6, hw * 1.18, hd * 1.15, 0.012, mat))
        if hg.get("crest", False):
            pts = [Vector((cx, cy + hd * 0.8 - hd * 1.6 * u, z1 + 0.02 + 0.07 * math.sin(math.pi * u))) for u in (0.0, 0.25, 0.5, 0.75, 1.0)]
            crest = pk._bm_object("Headgear_helm_crest", pk._tube_bm(pts, [0.03, 0.04, 0.045, 0.04, 0.03], segments=6), trim)
            pk._smooth(crest)
            out.append(crest)
    if hg.get("goggles", False):
        out.append(ring("Headgear_goggles_band", z0 + hh * 0.74, hw * 1.13, hd * 1.11, 0.008, mat_of("second") if "second" in colors else trim))
        for sg in (1, -1):
            out.append(pk._bm_object("Headgear_goggle_%s" % ("l" if sg > 0 else "r"), _ring_bm(Vector((cx + sg * hw * 0.45, y0 - 0.012, z0 + hh * 0.76)), 0.03, 0.008), mat_of("metal") if "metal" in colors else trim))
    return out
