"""The small people's lines (lines_people.py): what they have grown (horns, a tail, wings),
what they wear on their heads and faces, what they hold, carry and keep at their belts,
and what keeps them company. Every piece rides one bone. Sizes follow the body: P.t is its
trunk against a plain small person's, P.hr half the width of its head."""
import math

import numpy as np
from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import mat, field
from lines_people import slot, _hoop, _disc, book, lantern, horn_pair
from people_dress import arm_row, wall, drape, neck_c, mouth_at, cog


def M(P, items):
    """[(geometry, material name or material)] with the names made materials."""
    return [(geo, P.material(m) if isinstance(m, str) else m) for geo, m in items]


def shifted(items, d):
    d = V(d)
    return [(([V(p) + d for p in geo[0]], geo[1]) if geo else geo, m) for geo, m in items]


# ======================================================================================
# The head: horns, crowns, hats, hair
# ======================================================================================

@slot("head", "nubs", "horns-bull", "horns-quill", "horns-swept", "horns-ram", "horn-brow")
def head_horns(P, size, word):
    style = P._style
    m = P.material(word, "bone")
    k = size
    if style == "nubs":
        geo = horn_pair(P, [(0, 0, 0), (0.06, 0.0, 0.34 * k)], [0.15, 0.03], m)
    elif style == "horns-bull":      # short, thick, forward
        geo = horn_pair(P, [(0, 0, 0), (0.42 * k, -0.1 * k, 0.22 * k), (0.62 * k, -0.5 * k, 0.6 * k)], [0.17, 0.12, 0.015], m)
    elif style == "horns-quill":     # thin and straight, like pens stood in a pot
        geo = horn_pair(P, [(0, 0, 0), (0.1 * k, 0.1 * k, 0.8 * k), (0.16 * k, 0.26 * k, 1.7 * k)], [0.1, 0.065, 0.008], m)
    elif style == "horns-swept":     # long, laid back
        geo = horn_pair(P, [(0, 0, 0), (0.26 * k, 0.3 * k, 0.5 * k), (0.4 * k, 1.0 * k, 0.8 * k), (0.34 * k, 1.7 * k, 0.6 * k)], [0.14, 0.11, 0.065, 0.008], m)
    elif style == "horns-ram":       # curled at the temples
        geo = None
        hr = P.hr
        for s in (1, -1):
            c = Vector((s * hr * 0.95, P.hcy + 0.1 * hr, P.crown - 0.55 * hr))
            pts = g.spiral(c, hr * 0.5 * k, hr * 0.16 * k, 1.15, s * hr * 0.42 * k, n=10, axis=X * s, start=math.pi * 0.5)
            geo = g.merge(geo, g.tube(pts, [hr * (0.2 - 0.018 * i) * (0.7 + 0.3 * k) for i in range(len(pts))], n=5))
    else:                            # a heavy brow of horn, and what sweeps back from it
        hr = P.hr
        z = P.eye.z + 0.62 * hr
        ridge = [(-0.92 * hr, P.hy0 + 0.3 * hr, z - 0.1 * hr), (-0.5 * hr, P.hy0 + 0.02, z + 0.02), (0, P.hy0 - 0.04 * hr, z + 0.06 * hr), (0.5 * hr, P.hy0 + 0.02, z + 0.02), (0.92 * hr, P.hy0 + 0.3 * hr, z - 0.1 * hr)]
        geo = g.tube(ridge, [0.1 * hr * k, 0.16 * hr * k, 0.18 * hr * k, 0.16 * hr * k, 0.1 * hr * k], n=5)
        geo = g.merge(geo, horn_pair(P, [(0.1, -0.1, -0.1), (0.4 * k, 0.5 * k, 0.5 * k), (0.5 * k, 1.3 * k, 0.9 * k), (0.3 * k, 2.0 * k, 0.7 * k)], [0.2, 0.16, 0.1, 0.01], m))
    P.add(style, geo, m, "head")


def _crown_c(P, drop=0.3):
    return Vector((0, P.hcy, P.crown - drop * P.hr))


@slot("head", "crown-plain", "crown-coins", "crown-wire", "crown-grass", "crown-iron", "circlet")
def head_crown(P, size, word):
    style, hr = P._style, P.hr
    c = _crown_c(P, 0.5)
    r = hr * 0.86
    if style == "circlet":
        P.add("circlet", _hoop(c + Vector((0, 0, -0.05 * hr)), hr * 1.0, hr * 1.12, 0.035 * hr, u=X, v=Y, n=12, sides=3), mat("metal_brass"), "head")
        P.add("circlet_light", g.ico(c + Vector((0, -hr * 1.14, -0.05 * hr)), 0.09 * hr, sub=0), field("crown", 2.6), "head")
        return
    if style == "crown-coins":       # bent coins, overlapping
        geo = None
        n = 9
        for i in range(n):
            a = 2 * math.pi * i / n
            p = c + Vector((math.cos(a) * r, math.sin(a) * r * 1.1, 0.16 * hr * size + 0.05 * hr * (i % 2)))
            geo = g.merge(geo, _disc(p, 0.26 * hr * size, normal=(math.cos(a), math.sin(a), 0.25), thick=0.02, n=7))
        P.add("crown", geo, mat("metal_brass"), "head")
        return
    if style == "crown-wire":        # a little crown of bent wire
        pts = []
        n = 12
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            pts.append(c + Vector((math.cos(a) * r, math.sin(a) * r * 1.1, (0.34 if i % 2 else 0.06) * hr * size)))
        P.add("crown", g.tube(pts, [0.024 * hr] * len(pts), n=3, caps=False), mat("metal_brass"), "head")
        return
    if style == "crown-grass":       # plaited grass, with the ends standing
        P.add("crown_plait", _hoop(c, r * 1.02, r * 1.14, 0.07 * hr, u=X, v=Y, n=12, sides=4), mat("grass"), "head", smooth=True)
        geo = None
        for i in range(7):
            a = 2 * math.pi * i / 7 + 0.3
            b0 = c + Vector((math.cos(a) * r, math.sin(a) * r * 1.1, 0.04 * hr))
            geo = g.merge(geo, g.blade(b0, b0 + Vector((math.cos(a) * 0.2 * hr, math.sin(a) * 0.2 * hr, (0.5 + 0.2 * (i % 2)) * hr * size)), 0.14 * hr, normal=(math.cos(a), math.sin(a), 0)))
        P.add("crown_blades", geo, mat("grass"), "head", smooth=True)
        return
    m = mat("metal_brass") if style == "crown-plain" else mat("metal_iron_light")
    P.add("crown_band", wall((0, P.hcy, 0), (r, r * 1.1), (r * 1.05, r * 1.16), c.z, c.z + 0.2 * hr * size, thick=0.03 * hr, n=10), m, "head")
    geo = None
    for i in range(5):
        a = 2 * math.pi * i / 5 - math.pi / 2
        b0 = c + Vector((math.cos(a) * r * 1.03, math.sin(a) * r * 1.13, 0.2 * hr * size))
        geo = g.merge(geo, g.cone(b0, b0 + Vector((0, 0, 0.3 * hr * size)), 0.1 * hr, n=4))
    P.add("crown_points", geo, m, "head")
    if style == "crown-plain":
        P.add("crown_light", g.ico(c + Vector((0, -r * 1.14, 0.1 * hr * size)), 0.07 * hr, sub=0), field("crown", 2.6), "head")


def _hat_z(P):
    return P.eye.z + 0.95 * P.hr


@slot("head", "thimble", "beetle-helm", "cap-square", "cap-flat", "cap-peaked", "cap-wool", "kerchief", "hat-brim", "eyeshade", "brow-band", "acorn-cap", "lamp-roof", "lamp-band")
def head_hat(P, size, word):
    style, hr = P._style, P.hr
    cy, bz = P.hcy, _hat_z(P)
    top = P.crown
    if style == "thimble":           # a thimble for a helm
        P.add("thimble", g.lathe([(hr * 1.2, bz - 0.34 * hr), (hr * 1.14, bz - 0.26 * hr), (hr * 1.1, top - 0.1 * hr), (hr * 0.98, top + 0.2 * hr * size), (hr * 0.5, top + 0.36 * hr * size), (0.0, top + 0.38 * hr * size)], n=10, centre=(0, cy, 0)), mat("tin"), "head")
        P.add("thimble_rim", _hoop((0, cy, bz - 0.3 * hr), hr * 1.22, hr * 1.22, 0.05 * hr, u=X, v=Y, n=12, sides=4), mat("metal_iron_light"), "head")
    elif style == "beetle-helm":     # a wing-case for a helm, horned
        P.add("helm", g.ico((0, cy + 0.04 * hr, top - 0.3 * hr), hr * 1.12, sub=1, scale=(1.0, 1.14, 0.78)), mat("beetle"), "head", smooth=False)
        P.add("helm_horn", g.tube([(0, P.hy0 + 0.1 * hr, top + 0.1 * hr), (0, P.hy0 - 0.3 * hr, top + 0.5 * hr * size), (0, P.hy0 - 0.2 * hr, top + 1.0 * hr * size)], [0.14 * hr, 0.09 * hr, 0.01], n=5), mat("beetle"), "head")
    elif style == "cap-square":      # a scholar's cap
        m = P.material(word, "ink")
        P.add("cap", g.merge(g.box((0, cy + 0.02, top - 0.04 * hr), (hr * 1.7, hr * 1.9, 0.6 * hr * size)), g.box((0, cy + 0.02, top + 0.3 * hr * size), (hr * 2.3, hr * 2.4, 0.12 * hr))), m, "head")
        P.add("cap_tassel", g.tube([(0, cy, top + 0.36 * hr * size), (hr * 1.0, cy + 0.1, top + 0.34 * hr * size), (hr * 1.2, cy + 0.1, top - 0.2 * hr)], 0.035 * hr, n=3), mat("thread_gold"), "head")
    elif style in ("cap-flat", "cap-peaked"):
        m = P.material(word, "leather_dark")
        tall = 0.5 if style == "cap-flat" else 0.72
        P.add("cap", g.ico((0, cy + 0.02, top - hr * 0.36), hr * 1.06, sub=1, scale=(1.0, 1.1, tall)), m, "head", smooth=True)
        P.add("cap_peak", g.blade((0, P.hy0 + 0.3 * hr, bz - 0.02), (0, P.hy0 - 0.7 * hr * size, bz - 0.16 * hr), 1.5 * hr, normal=Z, belly=0.3, thick=0.012), m, "head")
        if style == "cap-peaked":
            P.add("cap_badge", g.ico((0, P.hy0 + 0.02, bz + 0.26 * hr), 0.12 * hr, sub=0, scale=(1, 0.5, 1)), mat("metal_brass"), "head")
    elif style == "cap-wool":        # a stocking cap, the end hanging
        m = P.material(word, "trim")
        P.add("cap", g.ico((0, cy + 0.02, top - hr * 0.3), hr * 1.08, sub=1, scale=(1.0, 1.1, 0.7)), m, "head", smooth=True)
        tail = [(0, cy + 0.1 * hr, top + 0.2 * hr), (0.5 * hr, cy + 0.5 * hr, top + 0.5 * hr * size), (1.1 * hr, cy + 0.7 * hr, top + 0.1 * hr), (1.3 * hr, cy + 0.7 * hr, top - 0.6 * hr * size)]
        P.add("cap_tail", g.tube(tail, [0.5 * hr, 0.34 * hr, 0.2 * hr, 0.1 * hr], n=6), m, "head", smooth=True)
        P.add("cap_bob", g.ico(Vector(tail[-1]) + Vector((0, 0, -0.1 * hr)), 0.2 * hr, sub=1), mat("fur_pale"), "head", smooth=True)
    elif style == "kerchief":        # a cloth tied over the hair
        m = P.material(word, "main")
        P.add("kerchief", g.ico((0, cy + 0.05 * hr, top - hr * 0.34), hr * 1.07, sub=1, scale=(1.0, 1.12, 0.72)), m, "head", smooth=True)
        P.add("kerchief_knot", g.merge(g.blade((0, P.hy1 - 0.02, bz - 0.1 * hr), (0.34 * hr, P.hy1 + 0.4 * hr, bz - 0.5 * hr), 0.3 * hr, normal=Y), g.blade((0, P.hy1 - 0.02, bz - 0.1 * hr), (-0.3 * hr, P.hy1 + 0.36 * hr, bz - 0.56 * hr), 0.3 * hr, normal=Y)), m, "head", smooth=True)
    elif style == "hat-brim":        # a low crown and a broad brim
        m = P.material(word, "cloth_dark")
        r = hr * 2.3 * size
        P.add("hat", g.merge(g.lathe([(hr * 0.6, bz + 0.04 * hr), (r, bz - 0.1 * hr), (r * 1.02, bz - 0.02 * hr), (hr * 0.6, bz + 0.16 * hr)], n=10, centre=(0, cy, 0)),
                             g.lathe([(hr * 1.14, bz + 0.06 * hr), (hr * 1.08, bz + 0.8 * hr), (hr * 0.7, bz + 1.1 * hr), (0.02, bz + 1.16 * hr)], n=10, centre=(0, cy, 0))), m, "head", smooth=True)
    elif style == "eyeshade":        # a clerk's shade over the eyes
        P.add("eyeshade_band", _hoop((0, cy, bz - 0.1 * hr), hr * 1.06, hr * 1.2, 0.05 * hr, u=X, v=Y, n=12, sides=4), mat("leather_dark"), "head")
        P.add("eyeshade", g.blade((0, P.hy0 + 0.4 * hr, bz - 0.06 * hr), (0, P.hy0 - 0.9 * hr * size, bz - 0.26 * hr), 2.0 * hr, normal=Z, belly=0.25, thick=0.012), mat("visor"), "head")
    elif style == "brow-band":       # a carrying-band worn into its brow
        P.add("brow_band", _hoop((0, cy, bz - 0.2 * hr), hr * 1.07, hr * 1.2, 0.09 * hr, u=X, v=Y, n=12, sides=4), P.material(word, "trim"), "head", smooth=True)
        for s in (1, -1):
            P.add("brow_strap_%d" % s, g.tube([(s * hr * 0.9, cy + 0.5 * hr, bz - 0.2 * hr), (s * hr * 0.7, P.rear(P.chestz) + 0.12, P.armz + 0.1)], 0.05 * hr, n=4, flat=0.4), P.material(word, "trim"), "chest", smooth=True)
    elif style == "acorn-cap":       # an acorn's cup for a cap, the stalk still on it
        m = P.material(word, "acorn")
        P.add("acorn_cap", g.lathe([(hr * 1.2, bz - 0.12 * hr), (hr * 1.24, bz + 0.2 * hr), (hr * 1.0, top + 0.1 * hr), (hr * 0.5, top + 0.3 * hr * size), (0.0, top + 0.36 * hr * size)], n=10, centre=(0, cy, 0)), m, "head")
        P.add("acorn_rim", _hoop((0, cy, bz - 0.1 * hr), hr * 1.23, hr * 1.23, 0.07 * hr, u=X, v=Y, n=12, sides=4), mat("thorn"), "head")
        P.add("acorn_stalk", g.tube([(0, cy, top + 0.3 * hr * size), (0.1 * hr, cy + 0.1 * hr, top + 0.62 * hr * size), (0.34 * hr, cy + 0.2 * hr, top + 0.78 * hr * size)], [0.1 * hr, 0.07 * hr, 0.05 * hr], n=4), mat("thorn"), "head")
    elif style == "lamp-roof":       # the roof of a lamp for a hat, its ring still on top
        r = hr * 1.75 * size
        P.add("lamp_roof", g.lathe([(r, bz - 0.04 * hr), (r, bz + 0.06 * hr), (r * 0.5, top + 0.24 * hr), (r * 0.14, top + 0.5 * hr), (r * 0.14, top + 0.66 * hr), (0.0, top + 0.72 * hr)], n=6, centre=(0, cy, 0), phase=math.pi / 6), mat("metal_brass"), "head")
        P.add("lamp_roof_ring", _hoop((0, cy, top + 0.86 * hr), 0.16 * hr, 0.16 * hr, 0.04 * hr, u=X, v=Z, n=8, sides=3), mat("metal_iron_light"), "head")
    else:                            # a lamp no bigger than a thumb, on a band
        P.add("lamp_band", _hoop((0, cy, bz - 0.1 * hr), hr * 1.06, hr * 1.2, 0.05 * hr, u=X, v=Y, n=12, sides=4), mat("leather"), "head")
        c = Vector((0, P.hy0 - 0.34 * hr, bz + 0.3 * hr))
        P.items("thumb_lamp", M(P, lantern(c, 0.44 * hr * size, "round", "lamp", 4.0, handle=False)), "head")
        P.add("thumb_lamp_arm", g.tube([(0, P.hy0 + 0.2 * hr, bz - 0.06 * hr), c + Vector((0, 0.1 * hr, -0.4 * hr * size))], 0.04 * hr, n=3), mat("metal_brass"), "head")


def scalp(P, low=0.0):
    """The skull above the hairline: high over the brow, down behind the ears to the nape."""
    v, e, hr = P.v0, P.eye, P.hr
    y, z = v[:, 1], v[:, 2]
    line = e.z + (0.82 + low) * hr - 0.9 * np.clip(y - (P.hy0 + 0.2 * hr), 0.0, None)
    line = np.maximum(line, e.z + 0.2 * hr)
    line = np.where(y > P.hcy + 0.3 * hr, P.chin + 0.36 * P.hh, line)
    return P.hb.is_head & ~P.ears & (z > line)


@slot("head", "crest", "hair-wig", "seam", "brush-ear", "pens-ears", "screwdriver-ear", "quill-ear", "twigs", "veil", "brow-ridge")
def head_more(P, size, word):
    style, hr = P._style, P.hr
    cy, top = P.hcy, P.crown
    if style == "crest":             # the sprite's hair: a cap of it on the skull, and pale leaves over (long, spiky, flame, swept)
        hair = P.material("trim")
        m = hair if word != "flame" else field("crest", 1.6)
        P.wear(scalp(P), hair, 0.028)
        geo = None
        rows = ((0.0, 0.5, 1.0), (-0.42, 0.34, 0.9), (0.42, 0.34, 0.9), (-0.74, 0.14, 0.74), (0.74, 0.14, 0.74), (0.0, 0.2, 1.2), (-0.3, -0.05, 1.0), (0.3, -0.05, 1.0))
        for i, (dx, lift, L) in enumerate(rows):
            base = Vector((dx * hr, P.hy0 + (0.42 + 0.28 * (i // 2)) * hr, top - (0.25 + abs(dx) * 0.5) * hr))
            if word == "spiky":
                tip = base + Vector((dx * 0.9, 0.3, 0.9 * L + 0.5 * lift)) * hr * size
            elif word == "long":
                tip = base + Vector((dx * 0.5, 1.6 * L, -0.9 * L)) * hr * size
            elif word == "swept":
                tip = base + Vector((1.5 * L, 0.6 * L, 0.3 * lift)) * hr * size
            else:
                tip = base + Vector((dx * 0.6, 1.2 * L, 1.1 * lift)) * hr * size
            geo = g.merge(geo, g.blade(base, tip, 0.62 * hr, normal=(dx, -0.2, 1), belly=0.4))
        P.add("crest", geo, m, "head", smooth=True)
        # what of it shows from the front: a lock before each ear, or leaves over the brow
        front = None
        if word == "long":
            for s in (1, -1):
                b0 = Vector((s * hr * 0.9, P.hy0 + 0.62 * hr, P.eye.z + 0.62 * hr))
                front = g.merge(front, g.tongue([b0, b0 + Vector((s * 0.16 * hr, -0.08 * hr, -0.8 * hr)), b0 + Vector((s * 0.08 * hr, -0.04 * hr, -1.75 * hr * size))], [0.46 * hr, 0.4 * hr, 0.05 * hr], thick=0.4, normal=(s, -1, 0)))
        else:
            for dx in (-0.5, 0.0, 0.5):
                b0 = Vector((dx * hr, P.hy0 + (0.3 + 0.3 * dx * dx) * hr, P.eye.z + 0.86 * hr))
                d = {"spiky": Vector((dx * 0.6, -0.4, 0.8)), "swept": Vector((0.9, -0.24, 0.24)), "flame": Vector((dx * 0.3, -0.12, 1.1))}.get(word, Vector((dx * 0.24, -0.26, -0.36)))
                front = g.merge(front, g.blade(b0, b0 + d * hr * size, 0.5 * hr, normal=(dx, -1, 0.3), belly=0.4))
        P.add("crest_front", front, m, "head", smooth=True)
    elif style == "hair-wig":        # hair, as people have it
        P.add("wig", g.ico((0, cy + 0.08 * hr, top - 0.34 * hr), hr * 1.1, sub=1, scale=(1.02, 1.16, 0.8)), P.material(word, "leather_dark"), "head", smooth=True)
    elif style == "seam":            # the maker's seam over the crown, where the mould closed
        y0, y1 = P.hy0, P.hy1
        pts = [(0, y0 + (y1 - y0) * t, top + 0.012 - P.hh * (2 * t - 1) ** 2 * 0.17) for t in [0.14 + 0.08 * i for i in range(10)]]
        P.add("mould_seam", g.tube(pts, [0.03 * hr * size] * len(pts), n=4), field("seam", 1.8), "head")
    elif style in ("brush-ear", "screwdriver-ear", "quill-ear"):
        b0 = Vector((hr * 1.02, cy - 0.1 * hr, P.eye.z + 0.1 * hr))
        tip = b0 + Vector((0.08 * hr, 0.5 * hr, 1.0 * hr)) * size
        if style == "brush-ear":
            P.add("ear_brush", g.tube([b0 + Vector((0, -0.3 * hr, -0.5 * hr)), tip], 0.04 * hr, n=4), mat("wood"), "head")
            P.add("ear_brush_tip", g.cone(tip, tip + Vector((0.03 * hr, 0.16 * hr, 0.34 * hr)), 0.09 * hr, n=5), mat("fur_pale"), "head")
        elif style == "screwdriver-ear":
            P.add("ear_driver", g.tube([b0 + Vector((0, -0.3 * hr, -0.5 * hr)), b0 + (tip - b0) * 0.4, tip], [0.085 * hr, 0.085 * hr, 0.025 * hr], n=5), mat("metal_brass"), "head")
        else:
            P.add("ear_quill", g.blade(b0 + Vector((0, -0.2 * hr, -0.3 * hr)), tip + Vector((0, 0.3 * hr, 0.5 * hr)), 0.3 * hr, normal=X, belly=0.6), mat("feather_pale"), "head", smooth=True)
    elif style == "pens-ears":       # a pen behind each ear
        geo = None
        for s in (1, -1):
            b0 = Vector((s * hr * 1.02, cy - 0.4 * hr, P.eye.z - 0.3 * hr))
            geo = g.merge(geo, g.blade(b0, b0 + Vector((s * 0.1 * hr, 0.9 * hr, 1.4 * hr)) * size, 0.26 * hr, normal=X, belly=0.6))
        P.add("ear_pens", geo, mat("feather_pale"), "head", smooth=True)
    elif style == "twigs":           # what the brush left in it
        geo = None
        for i in range(5):
            a = 0.6 + i * 1.2
            b0 = Vector((math.cos(a) * hr * 0.7, cy + math.sin(a) * hr * 0.6, top - 0.2 * hr))
            geo = g.merge(geo, g.tube([b0, b0 + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.6)) * hr * size, b0 + Vector((math.cos(a) * 0.7, math.sin(a) * 0.2, 0.9)) * hr * size], [0.05 * hr, 0.035 * hr, 0.01], n=3))
        P.add("twigs", geo, mat("thorn"), "head")
    elif style == "veil":            # a dark cloth from the horns down the back
        P.add("veil", drape((0, cy + 0.1 * hr, 0), lambda t: (hr * (1.05 + 0.5 * t), hr * (1.2 + 0.4 * t)), [top + 0.1 * hr, top - 0.6 * hr, P.neckz - 0.3 * P.t * size], -1.5, 1.5, thick=0.02, n=8), P.material(word, "shade"), "head", smooth=True)
    else:                            # a thick ridge of fired clay over the brow
        z = P.eye.z + 0.6 * hr
        pts = [(-0.95 * hr, P.hy0 + 0.34 * hr, z - 0.12 * hr), (-0.5 * hr, P.hy0 + 0.02, z), (0, P.hy0 - 0.06 * hr, z + 0.04 * hr), (0.5 * hr, P.hy0 + 0.02, z), (0.95 * hr, P.hy0 + 0.34 * hr, z - 0.12 * hr)]
        P.add("brow_ridge", g.tube(pts, [0.12 * hr * size, 0.2 * hr * size, 0.22 * hr * size, 0.2 * hr * size, 0.12 * hr * size], n=5), P.material(word, "fired"), "head", smooth=True)


# ======================================================================================
# The face
# ======================================================================================

@slot("face", "glass", "spectacles", "loupe", "goggles")
def face_glasses(P, size, word):
    style = P._style
    e, r, hr = P.eye, P.eye_r, P.hr
    brass = mat("metal_brass")
    if style == "glass":             # a glass no bigger than a button, screwed into one eye
        c = Vector((-e.x, e.y - r * 1.1, e.z))
        P.add("glass_rim", _hoop(c, r * 1.5 * size, r * 1.5 * size, r * 0.24, u=X, v=Z, n=10, sides=4), brass, "head")
        P.add("glass", _disc(c + Vector((0, -0.004, 0)), r * 1.4 * size, normal=Y, thick=0.008, n=10), field("glass", 1.4), "head")
        P.add("glass_cord", g.tube([c + Vector((-r * 1.5 * size, 0, 0)), c + Vector((-hr * 0.9, hr * 0.5, -hr * 0.9)), Vector((-0.5 * P.sx, P.front(P.chestz, -0.5 * P.sx) - 0.03, P.neckz - 0.1))], 0.012, n=3), mat("cord"), "head")
    elif style == "spectacles":      # round, and too large (low: looked over the top of)
        drop = r * 1.5 if word == "low" else 0.0
        geo = None
        for s in (1, -1):
            c = Vector((s * e.x, e.y - r * 1.25 - drop * 0.4, e.z - drop))
            geo = g.merge(geo, _hoop(c, r * 1.9 * size, r * 1.9 * size, r * 0.2, u=X, v=Z, n=10, sides=3))
        geo = g.merge(geo, g.tube([(-e.x + r * 1.9 * size, e.y - r * 1.25 - drop * 0.4, e.z - drop), (e.x - r * 1.9 * size, e.y - r * 1.25 - drop * 0.4, e.z - drop)], r * 0.16, n=3))
        for s in (1, -1):
            geo = g.merge(geo, g.tube([(s * (e.x + r * 1.9 * size), e.y - r * 1.2 - drop * 0.4, e.z - drop), (s * hr * 1.02, P.hcy, e.z + 0.1 * hr)], r * 0.14, n=3))
        P.add("spectacles", geo, brass, "head")
    elif style == "loupe":           # a glass on a band, for looking very closely
        P.add("loupe_band", _hoop((0, P.hcy, e.z + 0.5 * hr), hr * 1.05, hr * 1.2, 0.04 * hr, u=X, v=Y, n=12, sides=3), mat("leather"), "head")
        c = Vector((-e.x, e.y - r * 2.2, e.z))
        P.add("loupe", g.lathe([(r * 1.3, 0.0), (r * 1.7 * size, -r * 2.0), (r * 1.9 * size, -r * 2.1)], n=8, centre=(0, 0, 0)), brass, "head")
        P.pieces[-1] = (P.pieces[-1][0], ([Vector((c.x + p.x, c.y + p.z + r * 1.0, c.z + p.y)) for p in P.pieces[-1][1][0]], P.pieces[-1][1][1]), brass, "head", None)
        P.add("loupe_glass", _disc(c + Vector((0, -r * 1.1, 0)), r * 1.6 * size, normal=Y, thick=0.008, n=8), field("glass", 1.6), "head")
    else:                            # goggles, pushed up
        z = P.eye.z + 0.9 * hr
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, _hoop((s * 0.42 * hr, P.hy0 + 0.02, z), 0.3 * hr * size, 0.26 * hr * size, 0.07 * hr, u=X, v=Z, n=10, sides=4))
        P.add("goggles", geo, brass, "head")
        P.add("goggles_strap", _hoop((0, P.hcy, z), hr * 1.05, hr * 1.2, 0.04 * hr, u=X, v=Y, n=12, sides=3), mat("leather_dark"), "head")
        lens = None
        for s in (1, -1):
            lens = g.merge(lens, _disc((s * 0.42 * hr, P.hy0 + 0.0, z), 0.24 * hr * size, normal=Y, thick=0.01, n=8))
        P.add("goggles_glass", lens, mat("glass"), "head")


def _face_plate(P, kx=1.0, kz=1.0, drop=0.0):
    """A plate over the face: an ellipsoid shell before it."""
    e, hr = P.eye, P.hr
    c = Vector((0, P.hy0 + 0.42 * hr, e.z - 0.2 * hr - drop))
    return g.ico(c, hr, sub=2, scale=(0.84 * kx, 0.62, 1.02 * kz)), c


@slot("face", "mask-smooth", "tin-mask", "face-mask", "blank-half", "second-face", "big-eye", "big-ear", "beard", "thumbprint", "mouth-light", "dents")
def face_more(P, size, word):
    style = P._style
    e, r, hr = P.eye, P.eye_r, P.hr
    if style in ("mask-smooth", "tin-mask", "face-mask"):
        m = {"mask-smooth": P.material(word, "glaze"), "tin-mask": mat("tin"), "face-mask": P.material(word, "hand_skin")}[style]
        geo, c = _face_plate(P)
        verts = [p for p in geo[0]]
        keep = [i for i, p in enumerate(verts) if p.y < c.y + 0.1 * hr]
        idx = {i: k for k, i in enumerate(keep)}
        faces = [tuple(idx[i] for i in f) for f in geo[1] if all(i in idx for i in f)]
        P.add("mask", ([verts[i] for i in keep], faces), m, "head", smooth=(style != "tin-mask"))
        slits = None
        for s in (1, -1):
            slits = g.merge(slits, g.ico((s * e.x, c.y - 0.6 * hr, e.z), r * 1.0, sub=1, scale=(1.5, 0.5, 0.55 if style != "face-mask" else 0.9)))
        P.add("mask_eyes", slits, field("eyes", 3.4) if style != "mask-smooth" else mat("void"), "head", smooth=True)
        if style == "face-mask":     # the join, where it is tied on
            P.add("mask_tie", _hoop((0, P.hcy, e.z), hr * 1.04, hr * 1.2, 0.03 * hr, u=X, v=Y, n=12, sides=3), mat("cord"), "head")
            P.add("mask_mouth", g.ico((0, c.y - 0.58 * hr, P.mouth.z - 0.06 * hr), hr * 0.2, sub=1, scale=(1.2, 0.3, 0.3)), mat("maw"), "head", smooth=True)
        if style == "tin-mask":
            P.add("mask_rivets", g.merge(*[g.ico((s * 0.6 * hr, c.y - 0.4 * hr, e.z + dz * hr), 0.05 * hr, sub=0) for s in (1, -1) for dz in (0.5, -0.6)]), mat("metal_iron_light"), "head", smooth=True)
    elif style == "blank-half":      # half the face not finished
        geo, c = _face_plate(P, 1.0, 1.0)
        verts = geo[0]
        keep = [i for i, p in enumerate(verts) if p.y < c.y + 0.1 * hr and p.x < 0.04 * hr * (2.0 - size)]
        idx = {i: k for k, i in enumerate(keep)}
        faces = [tuple(idx[i] for i in f) for f in geo[1] if all(i in idx for i in f)]
        P.add("blank_half", ([verts[i] for i in keep], faces), P.material(word, "clay_wet"), "head", smooth=True)
    elif style == "second-face":     # a second small face on the back of its head
        c = Vector((0, P.hy1 - 0.1 * hr, e.z + 0.05 * hr))
        P.add("second_face", g.ico(c, hr * 0.62 * size, sub=1, scale=(1.0, 0.42, 1.2)), P.skin, "head", smooth=True)
        eyes = None
        for s in (1, -1):
            eyes = g.merge(eyes, g.ico(c + Vector((s * 0.22 * hr * size, 0.24 * hr * size, 0.14 * hr * size)), 0.1 * hr * size, sub=1, scale=(1, 0.5, 1)))
        P.add("second_eyes", eyes, field("eyes", 3.4), "head", smooth=True)
        P.add("second_mouth", g.ico(c + Vector((0, 0.24 * hr * size, -0.3 * hr * size)), 0.16 * hr * size, sub=1, scale=(1.2, 0.3, 0.4)), mat("maw"), "head", smooth=True)
    elif style == "big-eye":         # one eye larger than the other, and it does not blink
        c = Vector((e.x, e.y - r * 0.3, e.z))
        P.add("big_eye", g.ico(c, r * 2.1 * size, sub=1), mat("eye_white"), "head", smooth=True)
        P.add("big_eye_light", g.ico(c + Vector((0, -r * 1.5 * size, 0)), r * 1.25 * size, sub=1, scale=(1, 0.5, 1)), field("eyes", 4.4), "head", smooth=True)
        P.add("big_eye_pupil", g.ico(c + Vector((0, -r * 2.1 * size, 0)), r * 0.5 * size, sub=0, scale=(1, 0.4, 1)), mat("void"), "head", smooth=True)
    elif style == "big-ear":         # one ear larger than the other, cupped
        c = Vector((hr * 1.1, P.hcy - 0.1 * hr, e.z + 0.1 * hr))
        P.add("big_ear", g.lathe([(0.04 * hr, 0.0), (0.6 * hr * size, 0.5 * hr * size), (0.9 * hr * size, 0.56 * hr * size)], n=8, centre=(0, 0, 0)), P.skin, "head", smooth=True)
        geo = P.pieces[-1][1]
        R = Matrix.Rotation(math.radians(-70), 3, "Y") @ Matrix.Rotation(math.radians(-25), 3, "Z")
        P.pieces[-1] = (P.pieces[-1][0], ([c + R @ p for p in geo[0]], geo[1]), P.skin, "head", True)
    elif style == "beard":
        c = mouth_at(P)
        P.add("beard", g.tongue([c + Vector((0, 0.0, -0.16 * hr)), c + Vector((0, -0.06 * hr, -0.6 * hr * size)), c + Vector((0, 0.05 * hr, -1.2 * hr * size))], [0.8 * hr, 0.66 * hr, 0.06 * hr], thick=0.5, normal=Y), P.material(word, "hair_pale"), "head", smooth=True)
    elif style == "thumbprint":      # the maker's thumbprint still in its forehead
        z = e.z + 0.75 * hr
        c = Vector((0.1 * hr, P.front(z, 0.1 * hr) - 0.004, z))
        geo = g.merge(_hoop(c, 0.26 * hr * size, 0.34 * hr * size, 0.022 * hr, u=X, v=Z, n=10, sides=3), _hoop(c, 0.14 * hr * size, 0.2 * hr * size, 0.02 * hr, u=X, v=Z, n=8, sides=3))
        P.add("thumbprint", geo, field("seam", 1.8), "head")
        P.add("thumbprint_dent", g.ico(c + Vector((0, 0.02, 0)), 0.3 * hr * size, sub=1, scale=(0.9, 0.2, 1.2)), mat("clay_dark"), "head", smooth=True)
    elif style == "mouth-light":     # its light held between its teeth
        c = mouth_at(P)
        P.add("mouth_light", g.ico(c + Vector((0, -0.12 * hr, 0)), 0.2 * hr * size, sub=1), field("lamp", 4.2), "head", smooth=True)
        P.add("mouth_light_ring", _hoop(c + Vector((0, -0.12 * hr, 0)), 0.24 * hr * size, 0.24 * hr * size, 0.03 * hr, u=X, v=Y, n=8, sides=3), mat("metal_brass"), "head")
    else:                            # dents, where the practice blows fell
        geo = None
        for i, (x, z) in enumerate(((0.3, 0.5), (-0.4, 0.1), (0.1, -0.5))):
            zz = e.z + z * hr
            geo = g.merge(geo, g.ico((x * hr, P.hy0 + 0.02 * hr - 0.002, zz), 0.16 * hr * size, sub=1, scale=(1, 0.2, 1)))
        P.add("dents_face", geo, mat("clay_dark"), "head", smooth=True)
        geo = None
        for i, (x, z) in enumerate(((0.1, 0.0), (-0.12, -0.25), (0.02, 0.2))):
            zz = P.chestz + z * P.t
            geo = g.merge(geo, g.ico((x, P.front(zz, x) - 0.05, zz), 0.07 * size * P.t, sub=1, scale=(1, 0.3, 1)))
        P.add("dents_body", geo, mat("clay_dark"), "chest", smooth=True)


# ======================================================================================
# The back: a tail, wings, and what is carried there
# ======================================================================================

@slot("back", "tail")
def back_tail(P, size, word):
    """The imp's tail, and what it ends in: a spade, a hook, a pen's nib, a seal, an iron ball."""
    t = P.t * size
    hz = P.hipz - 0.04 * P.t
    b0 = Vector((0, P.rear(hz) - 0.02, hz))
    pts = [b0, b0 + Vector((0.02, 0.24, -0.12)) * t, b0 + Vector((0.1, 0.52, -0.06)) * t, b0 + Vector((0.22, 0.72, 0.2)) * t, b0 + Vector((0.26, 0.76, 0.52)) * t]
    P.add("tail", g.tube(pts, [0.06 * P.t, 0.05 * P.t, 0.04 * P.t, 0.03 * P.t, 0.022 * P.t], n=5), P.skin, "hips", smooth=True)
    tip, d = pts[-1], (pts[-1] - pts[-2]).normalized()
    word = word or "spade"
    if word == "spade":
        P.add("tail_tip", g.blade(tip - d * 0.02, tip + d * 0.26 * t, 0.2 * t, normal=X, belly=0.35), P.skin, "hips")
    elif word == "hook":
        P.add("tail_tip", g.tube([tip, tip + d * 0.14 * t, tip + d * 0.2 * t + Vector((0.14, 0.02, 0.0)) * t, tip + d * 0.06 * t + Vector((0.2, 0.02, 0.0)) * t], [0.04 * t, 0.04 * t, 0.03 * t, 0.004], n=4), mat("metal_iron_light"), "hips")
    elif word == "nib":
        P.add("tail_tip", g.blade(tip - d * 0.02, tip + d * 0.34 * t, 0.14 * t, normal=X, belly=0.3, thick=0.012), mat("metal_brass"), "hips")
        P.add("tail_nib_slit", g.box(tip + d * 0.2 * t, (0.035 * t, 0.012, 0.2 * t), rot=None), mat("void"), "hips")
    elif word == "seal":
        P.add("tail_tip", _disc(tip + d * 0.08 * t, 0.12 * t, normal=d, thick=0.08 * t, n=8), mat("metal_brass"), "hips")
        P.add("tail_seal", _disc(tip + d * 0.13 * t, 0.085 * t, normal=d, thick=0.02, n=8), field("seal", 2.2), "hips")
    else:
        P.add("tail_tip", g.ico(tip + d * 0.1 * t, 0.13 * t, sub=1), mat("metal_iron"), "hips")


WING_SHAPES = {
    # (how far out, how far back, how far up, width) for each blade of the left wing, in trunk heights
    "bud": [((0.36, 0.16, 0.26), 0.24)],
    "glass": [((0.62, 0.3, 0.42), 0.24), ((0.5, 0.26, -0.22), 0.19)],
    "beetle": [((0.6, 0.36, 0.22), 0.42), ((0.56, 0.3, -0.3), 0.3)],          # the case held open, and the wing under it
    "moth": [((0.7, 0.26, 0.5), 0.6), ((0.56, 0.22, -0.36), 0.5)],
    "dragonfly": [((0.95, 0.3, 0.4), 0.2), ((0.9, 0.36, 0.12), 0.18), ((0.74, 0.3, -0.2), 0.17)],
    "pages": [((0.56, 0.3, 0.5), 0.4), ((0.6, 0.26, 0.1), 0.4), ((0.46, 0.24, -0.3), 0.36)],
    "light": [((0.8, 0.34, 0.66), 0.3), ((0.72, 0.3, 0.14), 0.26), ((0.5, 0.26, -0.34), 0.2)],
    "elytra": [((0.34, 0.34, -0.3), 0.4), ((0.66, 0.3, 0.3), 0.2)],
}
# what each blade is made of: one material for them all, or one each. A wing of glass is not a
# light (every light on a body burns alike, and a wing of light is a blur): it is clear, and
# the light runs in its veins. Only a wing called light is light.
WING_MADE = {"bud": "wing_glass", "glass": "wing_glass", "beetle": ("beetle", "wing_glass"), "moth": "moth", "dragonfly": "wing_glass", "pages": "paper",
             "light": "field:wing:2.4", "elytra": ("beetle", "wing_glass"), "soot": "soot", "eyed": "moth"}


@slot("back", "wings")
def back_wings(P, size, word):
    """Wings, each its own piece (the game beats them): bud, glass, beetle, moth, dragonfly,
    pages, light, elytra; frost (one rimed, one sooted), soot, eyed (a moth's, with eyes)."""
    word = word or "glass"
    shape = {"frost": "moth", "soot": "moth", "eyed": "moth"}.get(word, word)
    k = P.t * size
    backz = P.J["chest"].z + 0.3 * P.t
    backy = P.rear(backz) + 0.01
    for tag, s in (("l", 1), ("r", -1)):
        root = Vector((s * 0.07 * P.t, backy, backz))
        made = ("ice_pale" if s > 0 else "soot") if word == "frost" else WING_MADE[word]
        items = []
        for i, ((dx, dy, dz), w) in enumerate(WING_SHAPES[shape]):
            b0 = root + Vector((0, 0, -0.04 * i * P.t))
            tip = b0 + Vector((s * dx, dy, dz)) * k
            belly = 0.55 if shape != "dragonfly" else 0.5
            mm = made if isinstance(made, str) else made[min(i, len(made) - 1)]
            items.append((g.blade(b0, tip, w * k, normal=(0, -1, 0.2 if dz > 0 else -0.2), belly=belly, thick=0.014), mm))
            if mm == "wing_glass":             # the light in its veins: one down the middle, one to each edge
                mid = b0 + (tip - b0) * belly
                side = (tip - b0).cross(Vector((0, -1, 0))).normalized() * (w * k * 0.4)
                veins = g.tube([b0, mid, tip], [0.016 * k, 0.012 * k, 0.004], n=3)
                for sgn in (1, -1):
                    veins = g.merge(veins, g.tube([b0 + (tip - b0) * 0.12, mid + side * sgn], [0.009 * k, 0.003], n=3))
                items.append((veins, "field:wing:1.6"))
            if mm == "beetle":                 # the seam of the case, bright
                items.append((g.tube([b0 + Vector((0, -0.012, 0)), tip + Vector((0, -0.012, 0))], [0.012 * k, 0.004], n=3), "metal_brass"))
            if mm == "moth":                   # paler toward the body, as a moth's are
                items.append((g.blade(b0 + Vector((0, -0.006, 0)), b0 + (tip - b0) * 0.62 + Vector((0, -0.006, 0)), w * k * 0.6, normal=(0, -1, 0.2 if dz > 0 else -0.2), belly=belly, thick=0.016), "feather_pale"))
            if word == "eyed" and i == 0:      # an eye on the wing
                c = b0 + (tip - b0) * 0.62 + Vector((0, -0.02, 0))
                items.append((_disc(c, 0.11 * k, normal=Y, thick=0.02, n=8), "void"))
                items.append((_disc(c + Vector((0, -0.012, 0)), 0.055 * k, normal=Y, thick=0.02, n=6), "field:eyes:3.0"))
            if word == "frost" and s > 0:      # rime along its edge
                rime = None
                for j in range(4):
                    q = b0 + (tip - b0) * (0.35 + 0.18 * j)
                    rime = g.merge(rime, g.cone(q, q + Vector((0, 0.02, -0.14 * k)), 0.03 * k, n=4))
                items.append((rime, "ice"))
            if word == "pages" and i < 2:      # ruled, as pages are
                lines = None
                for j in range(3):
                    q = b0 + (tip - b0) * (0.4 + 0.14 * j) + Vector((0, -0.012, 0))
                    lines = g.merge(lines, g.box(q, (w * k * 0.5, 0.006, 0.012 * k), rot=(0, -math.atan2(dz, dx * s) if s > 0 else math.atan2(dz, dx * -s) + math.pi, 0)))
                items.append((lines, "ink"))
        P.wing(tag, items, root)


@slot("back", "welts")
def back_welts(P, size, word):
    """Its back ridged with welts gone hard as plate."""
    geo, alt = None, None
    for i in range(5):
        z = P.hipz + (P.neckz - P.hipz) * (0.16 + 0.19 * i)
        y = P.rear(z) + 0.02
        hw = P.ring(z)[0]
        pl = g.ico((0, y, z), 1.0, sub=1, scale=(hw * 0.86 * size, 0.07 * size, 0.1 * P.t), rot=(0.3, 0, 0))
        if i % 2:
            alt = g.merge(alt, pl)
        else:
            geo = g.merge(geo, pl)
    P.add("welts", geo, P.material(word, "welt"), "chest", smooth=False)
    P.add("welts_b", alt, mat("horn_ridge"), "chest", smooth=False)


def _back_y(P, z=None):
    return P.rear(P.chestz if z is None else z)


@slot("back", "pack", "pack-frame", "bundle", "book-stack", "card-drawers", "thread-spool", "hod", "satchel-back")
def back_pack(P, size, word):
    style = P._style
    t = P.t * size
    by = _back_y(P) + 0.03
    zc = (P.hipz + P.neckz) / 2 + 0.06 * P.t
    lea, wood = P.material("trim") if P.kind == "homunculus" else mat("leather"), mat("wood")
    if style == "pack-frame":        # a carrying frame, nothing on it yet
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, g.tube([(s * 0.16 * t, by + 0.04, P.hipz), (s * 0.16 * t, by + 0.06, P.neckz + 0.25 * t)], 0.028, n=4))
        for z in (P.hipz + 0.1 * t, zc, P.neckz + 0.12 * t):
            geo = g.merge(geo, g.tube([(-0.18 * t, by + 0.05, z), (0.18 * t, by + 0.05, z)], 0.024, n=4))
        P.add("pack_frame", geo, wood, "chest")
    elif style in ("pack", "bundle"):
        h = 0.62 * t if style == "pack" else 0.4 * t
        c = Vector((0, by + 0.2 * t, zc + 0.12 * t))
        P.add("pack", g.ico(c, 1.0, sub=1, scale=(0.3 * t, 0.2 * t, h * 0.62)), mat("cloth_wool"), "chest", smooth=True)
        P.add("pack_roll", g.tube([c + Vector((-0.34 * t, 0, h * 0.66)), c + Vector((0.34 * t, 0, h * 0.66))], 0.1 * t, n=7), P.material(word, "cloth_rag"), "chest", smooth=True)
        P.add("pack_straps", g.merge(_hoop(c, 0.31 * t, h * 0.63, 0.02, u=X, v=Z, n=10, sides=3), _hoop(c, 0.21 * t, h * 0.63, 0.02, u=Y, v=Z, n=10, sides=3)), lea, "chest", smooth=True)
        if style == "pack" and size > 1.1:      # and what hangs from it
            P.add("pack_pot", g.lathe([(0.02, 0.0), (0.09 * t, 0.02), (0.1 * t, 0.12 * t), (0.07 * t, 0.14 * t)], n=7, centre=c + Vector((0.34 * t, 0.02, -h * 0.5))), mat("metal_dark"), "chest")
            P.items("pack_lamp", M(P, lantern(c + Vector((-0.36 * t, 0.02, -h * 0.36)), 0.08 * t, "round", "lamp", 3.2)), "chest")
    elif style == "book-stack":      # books, strapped one on another
        c = Vector((0, by + 0.17 * t, P.hipz + 0.12 * t))
        for i in range(int(round(3 + size))):
            w = (0.4 - 0.03 * (i % 2)) * t
            P.items("stack_%d" % i, M(P, book(c + Vector((0.02 * (i % 2), 0, 0.14 * t * i)), w, 0.12 * t, 0.3 * t, rot=(0, 0, 0.1 * (i % 3 - 1)), cover=("leather", "leather_dark", "cloth_rag", "visor")[i % 4])), "chest")
        P.add("stack_strap", _hoop(c + Vector((0, 0, 0.14 * t * 1.5)), 0.03 + 0.17 * t, 0.14 * t * 2.6, 0.018, u=Y, v=Z, n=10, sides=3), mat("leather"), "chest", smooth=True)
    elif style == "card-drawers":    # a cabinet of small drawers
        c = Vector((0, by + 0.16 * t, zc + 0.08 * t))
        P.add("drawers", g.box(c, (0.5 * t, 0.26 * t, 0.66 * t)), wood, "chest")
        fronts, pulls = None, None
        for i in range(3):
            for j in range(4):
                p = c + Vector(((i - 1) * 0.155 * t, 0.134 * t, (j - 1.5) * 0.15 * t))
                fronts = g.merge(fronts, g.box(p, (0.13 * t, 0.02, 0.12 * t)))
                pulls = g.merge(pulls, g.ico(p + Vector((0, 0.02, 0)), 0.02 * t, sub=0))
        P.add("drawer_fronts", fronts, mat("paper_old"), "chest")
        P.add("drawer_pulls", pulls, mat("metal_brass"), "chest", smooth=True)
    elif style == "thread-spool":    # a spool of thread, as big as its back
        c = Vector((0, by + 0.16 * t, zc))
        P.add("spool", g.lathe([(0.2 * t, -0.24 * t), (0.2 * t, -0.2 * t), (0.07 * t, -0.19 * t), (0.07 * t, 0.19 * t), (0.2 * t, 0.2 * t), (0.2 * t, 0.24 * t)], n=8, centre=c), wood, "chest")
        P.add("spool_thread", g.lathe([(0.15 * t, -0.18 * t), (0.17 * t, 0.0), (0.15 * t, 0.18 * t)], n=8, centre=c), P.material(word, "thread_red"), "chest", smooth=True)
    elif style == "hod":             # a hod of dressed stone on its shoulder
        c = Vector((0.1 * t, by + 0.14 * t, P.neckz + 0.14 * t))
        P.add("hod", g.merge(g.box(c, (0.5 * t, 0.3 * t, 0.05 * t), rot=(0.25, 0, 0)), g.box(c + Vector((0, 0.15 * t, 0.12 * t)), (0.5 * t, 0.05 * t, 0.26 * t), rot=(0.25, 0, 0)),
                             g.tube([c + Vector((0, 0.04, -0.02)), c + Vector((0, 0.1 * t, -0.6 * t))], 0.03, n=4)), wood, "chest")
        blocks = None
        for i, (dx, dz) in enumerate(((-0.13, 0.1), (0.12, 0.1), (0.0, 0.26))):
            blocks = g.merge(blocks, g.box(c + Vector((dx * t, 0.02, dz * t)), (0.22 * t, 0.2 * t, 0.14 * t), rot=(0.25, 0, 0.1 * (i - 1))))
        P.add("hod_stone", blocks, mat("stone_face"), "chest")
    else:                            # a satchel, on the back
        c = Vector((0, by + 0.1 * t, zc - 0.04 * t))
        P.add("satchel", g.box(c, (0.4 * t, 0.16 * t, 0.36 * t)), lea, "chest", smooth=False)
        P.add("satchel_flap", g.box(c + Vector((0, 0.086 * t, 0.06 * t)), (0.42 * t, 0.02, 0.26 * t)), mat("leather_dark"), "chest", smooth=False)


def _pole(P, name, foot, tip, r, material, mid=None):
    pts = [foot] + ([mid] if mid is not None else []) + [tip]
    P.add(name, g.tube(pts, [r] * len(pts), n=5), material, "chest")


@slot("back", "lamp-pole", "lamp-pole-behind", "crook-lantern", "tap-pole", "broom", "hammer-long", "spanner-back", "litter-poles", "toll-pole", "stakes", "winding-key", "smoke", "lantern-behind")
def back_poles(P, size, word):
    style = P._style
    t = P.t
    by = _back_y(P) + 0.05
    top = P.crown
    wood = mat("wood")
    if style == "lamp-pole":         # a lamplighter's pole, bending over its head, the light before it
        crook = [(0.0, by, P.hipz + 0.05), (0.0, by + 0.03, P.neckz), (0.0, by, top + 0.25 * size), (0.0, P.hcy - 0.1, top + 0.55 * size), (0.0, P.hy0 - 0.4, top + 0.48 * size), (0.0, P.hy0 - 0.56, top + 0.26 * size)]
        P.add("pole", g.tube(crook, [0.024, 0.024, 0.02, 0.018, 0.015, 0.012], n=5), wood, "chest")
        P.items("pole_lamp", M(P, lantern(Vector(crook[-1]) + Vector((0, 0, -0.2 * t)), 0.13 * t * size, word or "round", "lamp", 4.2)), "chest")
    elif style == "lamp-pole-behind":   # held out behind it, for someone to follow
        pts = [(0.14, P.front(P.chestz) - 0.2, P.armz - 0.2), (0.16, by, P.armz + 0.18), (0.18, by + 0.9 * size, P.armz + 0.5), (0.18, by + 1.5 * size, P.armz + 0.42)]
        P.add("pole", g.tube(pts, [0.024, 0.024, 0.02, 0.016], n=5), wood, "chest")
        P.add("pole_light", g.ico(Vector(pts[-1]) + Vector((0, 0.06, -0.02)), 0.14 * t * size, sub=1), field("lamp", 3.0), "chest", smooth=True)
        P.add("pole_light_ring", _hoop(Vector(pts[-1]) + Vector((0, 0.06, -0.02)), 0.17 * t * size, 0.17 * t * size, 0.016, u=X, v=Z, n=8, sides=3), mat("metal_brass"), "chest")
    elif style == "crook-lantern":   # a lantern hung on a long crook, away from itself
        pts = [(-0.12, by, P.hipz + 0.1), (-0.14, by - 0.02, P.armz + 0.1), (-0.3 - 0.4 * size, P.hcy - 0.5 * size, top + 0.5 * size), (-0.5 - 0.6 * size, P.hy0 - 0.6 * size, top + 0.34 * size), (-0.56 - 0.66 * size, P.hy0 - 0.7 * size, top + 0.12 * size)]
        P.add("crook", g.tube(pts, [0.024, 0.024, 0.02, 0.016, 0.012], n=5), wood, "chest")
        P.items("crook_lamp", M(P, lantern(Vector(pts[-1]) + Vector((0, 0, -0.24 * t)), 0.15 * t * (0.8 + 0.2 * size), word or "round", "lamp", 4.0)), "chest")
    elif style == "tap-pole":        # a long pole for tapping at windows
        _pole(P, "tap_pole", Vector((-0.2, by, P.footz + 0.2)), Vector((-0.3, by - 0.1, top + 1.3 * size)), 0.022, wood)
        P.add("tap_knob", g.merge(g.ico((-0.3, by - 0.1, top + 1.3 * size), 0.05, sub=0), g.tube([(-0.3, by - 0.1, top + 1.3 * size), (-0.3, by - 0.34, top + 1.36 * size)], 0.01, n=3)), mat("metal_iron_light"), "chest")
    elif style == "broom":           # a broom of its own making
        foot, tip = Vector((0.24, by, P.hipz - 0.2)), Vector((-0.2, by + 0.05, top + 0.5 * size))
        _pole(P, "broom", foot, tip, 0.024, wood)
        d = (tip - foot).normalized()
        twigs = None
        for i in range(8):
            a = 2 * math.pi * i / 8
            off = Vector((math.cos(a), 0.4 * math.sin(a), 0)) * 0.12 * size
            twigs = g.merge(twigs, g.cone(tip - d * 0.02 + off * 0.3, tip + d * 0.42 * size + off, 0.035, n=3))
        P.add("broom_head", twigs, mat("thorn"), "chest")
        P.add("broom_tie", g.ico(tip + d * 0.03, 0.065, sub=0), mat("cord"), "chest")
    elif style in ("hammer-long", "spanner-back"):
        foot, tip = Vector((0.26, by, P.hipz - 0.1)), Vector((-0.24, by + 0.04, top + 0.3 * size))
        d = (tip - foot).normalized()
        if style == "hammer-long":   # a long-handled hammer, for sounding the rail
            _pole(P, "hammer", foot, tip, 0.026, wood)
            side = d.cross(Y).normalized()
            P.add("hammer_head", g.box(tip, (0.36 * size * t, 0.13 * t, 0.14 * t), rot=Matrix((side, Y, d)).transposed()), mat("metal_iron"), "chest")
        else:                        # a spanner as long as your arm
            P.add("spanner", g.tube([foot, tip], 0.03 * size, n=4, flat=0.5), mat("metal_iron_light"), "chest")
            P.add("spanner_jaw", _hoop(tip + d * 0.1 * size * t, 0.1 * size * t, 0.1 * size * t, 0.035 * size, u=X, v=Z, n=8, sides=4), mat("metal_iron_light"), "chest")
            P.add("spanner_ring", _hoop(foot - d * 0.05, 0.06 * size * t, 0.06 * size * t, 0.025, u=X, v=Z, n=8, sides=4), mat("metal_iron_light"), "chest")
    elif style == "litter-poles":    # the poles of a litter, and its cloth rolled between them
        for s in (1, -1):
            _pole(P, "litter_%d" % s, Vector((s * 0.13, by + 0.02, P.hipz - 0.36)), Vector((s * 0.13, by + 0.08, top + 0.5 * size)), 0.026, wood)
        P.add("litter_roll", g.tube([(0, by + 0.07, P.hipz), (0, by + 0.1, P.neckz + 0.1)], 0.1 * t, n=7), mat("cloth_wool"), "chest", smooth=True)
    elif style == "toll-pole":       # the bar of a gate, striped
        a, b = Vector((-0.6 * size, by, P.armz + 0.34)), Vector((0.75 * size, by, P.armz - 0.1))
        n = 6
        for i in range(n):
            p0, p1 = a + (b - a) * i / n, a + (b - a) * (i + 1) / n
            P.add("toll_%d" % i, g.tube([p0, p1], 0.035, n=5), mat("paper") if i % 2 else mat("seal_wax"), "chest")
        P.add("toll_weight", g.box(a, (0.14, 0.1, 0.16)), mat("metal_iron"), "chest")
    elif style == "stakes":          # ward-stakes in a bundle, their heads lit
        geo, lit = None, None
        for i in range(3):
            foot = Vector((-0.12 + 0.12 * i, by + 0.02, P.hipz))
            tip = Vector((-0.3 + 0.3 * i, by + 0.06, top + (0.14 + 0.1 * (i % 2)) * size))
            geo = g.merge(geo, g.tube([foot, tip], 0.022, n=4))
            lit = g.merge(lit, g.ico(tip, 0.045, sub=0))
        P.add("stakes", geo, wood, "chest")
        P.add("stake_heads", lit, field("ward", 2.6), "chest")
    elif style == "winding-key":     # a key between its shoulders, to wind it by
        c = Vector((0, by, P.chestz + 0.06))
        P.add("key_stem", g.tube([c, c + Vector((0, 0.3 * size * t, 0))], 0.035, n=5), mat("metal_brass"), "chest")
        geo = None
        for s in (1, -1):
            geo = g.merge(geo, _hoop(c + Vector((s * 0.15 * size * t, 0.34 * size * t, 0)), 0.13 * size * t, 0.17 * size * t, 0.03, u=X, v=Z, n=10, sides=4))
        P.add("key_wings", geo, mat("metal_brass"), "chest")
    elif style == "smoke":           # smoke going up off it
        geo = None
        for i in range(4):
            x = -0.15 + 0.1 * i
            p0 = Vector((x, by - 0.02, P.neckz - 0.1 + 0.05 * (i % 2)))
            k = size * (0.8 + 0.2 * (i % 2))
            geo = g.merge(geo, g.tongue([p0, p0 + Vector((x * 0.5, 0.14, 0.3)) * k, p0 + Vector((-x, 0.3, 0.64)) * k, p0 + Vector((x * 0.6, 0.4, 1.0)) * k], [0.16, 0.14, 0.09, 0.02], thick=0.35, normal=X))
        P.add("smoke", geo, mat("smoke"), "chest", smooth=True)
    else:                            # its lantern, held just behind its back
        c = Vector((0.1, by + 0.14 * t, P.hipz + 0.16 * t))
        P.items("lantern_behind", M(P, lantern(c, 0.13 * t * size, word or "round", "lamp", 3.8)), "hips")


# ======================================================================================
# The chest: what it holds to it, or wears on it
# ======================================================================================

@slot("chest", "book-hug", "book-flat", "book-clasped", "book-open", "lantern-hug", "lantern-heart", "lantern-peek", "thimble-string")
def chest_held(P, size, word):
    style = P._style
    t = P.t * size
    z = (P.hipz + P.neckz) / 2 + 0.04 * P.t
    fy = P.front(z)
    if style == "book-hug":          # a book held shut with both arms
        P.items("book", M(P, book((0, fy - 0.1 * t, z), 0.44 * t, 0.56 * t, 0.15 * t, rot=(0.12, 0, 0), cover=P.roles.get("under", "leather"), clasp="field:clasp:2.0")), "chest")
    elif style == "book-flat":       # shut, and tied round with a ribbon
        P.items("book", M(P, book((0, fy - 0.08 * t, z - 0.06 * t), 0.46 * t, 0.5 * t, 0.12 * t, rot=(0.1, 0, 0), cover=P.roles.get("under", "leather"))), "chest")
        P.add("book_ribbon", g.merge(g.box((0, fy - 0.08 * t, z - 0.06 * t), (0.07 * t, 0.14 * t, 0.53 * t), rot=(0.1, 0, 0)), g.box((0, fy - 0.08 * t, z - 0.06 * t), (0.49 * t, 0.14 * t, 0.07 * t), rot=(0.1, 0, 0))), mat("paper"), "chest")
    elif style == "book-clasped":    # shut and clasped, the clasps holding a light
        c = Vector((0, fy - 0.1 * t, z))
        P.items("book", M(P, book(c, 0.5 * t, 0.64 * t, 0.17 * t, rot=(0.1, 0, 0), cover=P.roles.get("under", "leather"))), "chest")
        geo = None
        for dz in (-0.2, 0.0, 0.2):
            geo = g.merge(geo, g.box(c + Vector((0, 0, dz * t)), (0.54 * t, 0.2 * t, 0.05 * t), rot=(0.1, 0, 0)))
        P.add("book_clasps", geo, mat("metal_brass"), "chest")
        P.add("book_lock", g.ico(c + Vector((0, -0.1 * t, 0)), 0.06 * t, sub=0, scale=(1, 0.5, 1.2)), field("clasp", 2.6), "chest")
    elif style == "book-open":       # open in its hands, and read
        c = Vector((0, fy - 0.2 * t, z + 0.02 * t))
        for s in (1, -1):
            T = Matrix.Translation(c) @ Matrix.Rotation(-0.9, 4, "X") @ Matrix.Rotation(s * math.radians(-12), 4, "Y")
            P.add("open_page_%d" % s, g.moved(g.box((s * 0.15 * t, 0, 0), (0.3 * t, 0.4 * t, 0.03 * t)), T), mat("paper"), "chest")
            P.add("open_cover_%d" % s, g.moved(g.box((s * 0.155 * t, 0, -0.022 * t), (0.32 * t, 0.42 * t, 0.014 * t)), T), P.material(word, "leather"), "chest")
            lines = None
            for k in range(4):
                lines = g.merge(lines, g.box((s * 0.15 * t, (-0.12 + 0.075 * k) * t, 0.018 * t), (0.2 * t, 0.012 * t, 0.006)))
            P.add("open_lines_%d" % s, g.moved(lines, T), mat("ink"), "chest")
    elif style == "lantern-hug":     # a lantern it holds in both arms and will not put down
        P.items("lantern", M(P, lantern((0, fy - 0.2 * t, z + 0.02 * t), 0.2 * t, word or "round", "lamp", 4.2)), "chest")
    elif style == "lantern-heart":   # the light is in its chest now
        c = Vector((0, P.front(P.chestz - 0.05 * P.t) - 0.02, P.chestz - 0.05 * P.t))
        P.add("heart_frame", _hoop(c, 0.13 * t, 0.17 * t, 0.025, u=X, v=Z, n=10, sides=4), mat("metal_brass"), "chest")
        P.add("heart_flame", g.ico(c + Vector((0, 0.0, 0)), 0.11 * t, sub=1, scale=(0.9, 0.5, 1.3)), field("lamp", 4.4), "chest", smooth=True)
        P.add("heart_bars", g.merge(g.box(c + Vector((0, -0.02, 0)), (0.02, 0.02, 0.33 * t)), g.box(c + Vector((0, -0.02, 0)), (0.25 * t, 0.02, 0.02))), mat("metal_brass"), "chest")
    elif style == "lantern-peek":    # only its lantern out, at the collar's edge
        P.items("lantern", M(P, lantern((0.0, P.hy0 - 0.45 * P.hr, P.chin + 0.1 * P.hh), 0.11 * t, "round", "lamp", 4.0)), "chest")
    else:                            # a thimble on a string round its neck
        c = Vector((0, fy - 0.05 * t, z + 0.06 * t))
        P.add("thimble_string", g.tube([neck_c(P) + Vector((0.1, 0, 0)), c + Vector((0, 0, 0.08 * t)), neck_c(P) + Vector((-0.1, 0, 0))], 0.01, n=3), mat("cord"), "chest")
        P.items("thimble", M(P, lantern(c, 0.11 * t, "thimble", "oil", 3.0)), "chest")


@slot("chest", "badge", "wall-plate", "heart", "heart-glow", "ember-heart", "seal", "dial", "clock", "pattern-ring", "terms")
def chest_worn(P, size, word):
    style = P._style
    t = P.t * size
    z = P.chestz - 0.04 * P.t
    fy = P.front(z)
    c = Vector((0, fy - 0.03, z))
    if style == "badge":             # a brass badge, polished thin
        P.add("badge", _disc(Vector((0.09 * P.t, P.front(z, 0.09 * P.t) - 0.035, z + 0.04 * P.t)), 0.1 * t, normal=Y, thick=0.025, n=8), mat("metal_brass"), "chest")
        if size > 1.4:               # a plate, stamped with every post it has put right
            pc = Vector((0, P.front(z - 0.1 * P.t) - 0.05, z - 0.08 * P.t))
            P.add("plate", g.box(pc, (0.3 * P.t * size * 0.6, 0.03, 0.36 * P.t * size * 0.6), rot=(0.08, 0, 0)), mat("metal_brass"), "chest")
            st = None
            for i in range(3):
                for j in range(4):
                    st = g.merge(st, g.ico(pc + Vector(((i - 1) * 0.07 * P.t, -0.02, (j - 1.5) * 0.07 * P.t)), 0.018 * P.t, sub=0))
            P.add("plate_stamps", st, mat("metal_dark"), "chest", smooth=True)
    elif style == "wall-plate":      # a flat plate strapped to its front (and its back), engraved too small to read
        zc = (P.kneez + P.neckz) / 2
        h = (P.neckz - P.kneez) * 0.96
        hw = P.ring(P.chestz)[0]
        for tag, y in (("front", P.front(P.chestz) - 0.1), ("back", P.rear(P.chestz) + 0.1)):
            P.add("wall_" + tag, g.box((0, y, zc), (hw * 2.5 * size, 0.06, h)), mat("slate_light"), "chest")
            if tag == "front":
                lines = None
                for i in range(7):
                    lines = g.merge(lines, g.box((0, y - 0.034, zc + h * (0.36 - 0.11 * i)), (hw * 2.0 * size * (0.9 if i % 3 else 0.6), 0.01, 0.018)))
                P.add("wall_lines", lines, field("script", 1.6), "chest")
        for s in (1, -1):
            P.add("wall_strap_%d" % s, g.tube([(s * hw * 0.9, P.front(P.chestz) - 0.1, P.neckz - 0.06), (s * hw * 0.9, P.J["chest"].y, P.neckz + 0.12), (s * hw * 0.9, P.rear(P.chestz) + 0.1, P.neckz - 0.06)], 0.035, n=4, flat=0.4), mat("leather"), "chest", smooth=True)
    elif style in ("heart", "heart-glow", "ember-heart"):
        k = {"heart": 0.05, "heart-glow": 0.075, "ember-heart": 0.09}[style] * (0.7 + 0.3 * size) * (P.t + 0.3)
        P.add("heart_light", g.ico(c + Vector((0, 0.012, 0)), k, sub=1, scale=(1.0, 0.5, 1.2)), field("heart" if style != "ember-heart" else "ember", 3.0 if style != "ember-heart" else 3.8), "chest", smooth=True)
        if word != "bare" and style == "heart":
            P.add("heart_rim", _hoop(c + Vector((0, 0.0, 0)), k * 1.3, k * 1.5, k * 0.24, u=X, v=Z, n=10, sides=4), mat("metal_brass"), "chest")
        if style == "ember-heart":   # the ribs of it showing
            ribs = None
            for dz in (-1.0, 0.0, 1.0):
                ribs = g.merge(ribs, g.box(c + Vector((0, -0.01, dz * k * 0.8)), (k * 3.0, 0.03, k * 0.26)))
            P.add("heart_ribs", ribs, mat("coal_lump"), "chest")
    elif style == "seal":            # a seal on a ribbon
        P.add("seal_ribbon", g.tube([neck_c(P) + Vector((0.09, -0.06, 0)), c + Vector((0, -0.02, -0.02)), neck_c(P) + Vector((-0.09, -0.06, 0))], 0.016, n=3, flat=0.4), mat("seal_wax"), "chest", smooth=True)
        P.add("seal", _disc(c + Vector((0, -0.03, -0.06 * t)), 0.07 * t, normal=Y, thick=0.03, n=8), mat("metal_brass"), "chest")
        P.add("seal_face", _disc(c + Vector((0, -0.05, -0.06 * t)), 0.045 * t, normal=Y, thick=0.012, n=6), field("seal", 2.2), "chest")
    elif style in ("dial", "clock"): # a dial on its chest, that turns to point
        P.add("dial_case", _disc(c + Vector((0, -0.02, 0)), 0.15 * t, normal=Y, thick=0.05, n=10), mat("metal_brass"), "chest")
        P.add("dial_face", _disc(c + Vector((0, -0.05, 0)), 0.12 * t, normal=Y, thick=0.01, n=10), mat("paper") if style == "dial" else field("clock", 1.6), "chest")
        hand = g.merge(g.blade(c + Vector((0, -0.06, 0)), c + Vector((0.07 * t, -0.06, 0.08 * t)), 0.035 * t, normal=Y, thick=0.006))
        if style == "clock":
            hand = g.merge(hand, g.blade(c + Vector((0, -0.06, 0)), c + Vector((-0.05 * t, -0.06, 0.03 * t)), 0.03 * t, normal=Y, thick=0.006))
        P.add("dial_hand", hand, mat("void") if style == "clock" else field("seam", 2.2), "chest")
    elif style == "pattern-ring":    # a ring of the Pattern's light, turning round its chest
        hw, hd, yo = P.ring(z)
        u = Vector((1, 0, 0.22)).normalized()
        P.add("pattern_ring", _hoop((0, yo, z), (hw + 0.14) * (0.8 + 0.2 * size), (hd + 0.14) * (0.8 + 0.2 * size), 0.016, u=u, v=Y, n=16, sides=3), field("pattern", 2.6), "chest")
        beads = None
        for k in range(5):
            a = 2 * math.pi * k / 5 + 0.4
            beads = g.merge(beads, g.ico(Vector((0, yo, z)) + u * math.cos(a) * (hw + 0.14) * (0.8 + 0.2 * size) + Y * math.sin(a) * (hd + 0.14) * (0.8 + 0.2 * size), 0.04, sub=0))
        P.add("pattern_beads", beads, field("pattern", 3.2), "chest")
    else:                            # its partner's Terms, pressed into its chest in a neat hand
        lines = None
        for i in range(5):
            zz = z + (0.14 - 0.075 * i) * P.t
            w = (0.26 if i % 2 == 0 else 0.2) * t
            lines = g.merge(lines, g.box((0.0 if i % 2 == 0 else -0.03 * t, P.front(zz) - 0.012, zz), (w, 0.012, 0.022 * P.t)))
        P.add("terms", lines, field("script", 2.2), "chest")


# ======================================================================================
# The belt
# ======================================================================================

def _hip(P, side=1, dz=0.0):
    z = P.hipz + 0.1 * P.t + dz
    hw, hd, yo = P.ring(z)
    return Vector((side * (hw + 0.05), yo, z))


@slot("belt", "book", "chain-tags", "lantern", "lantern-front", "purse", "pouch", "tools", "keys", "kettle", "satchel", "ledger-chained", "chalk-ring", "bandage-rolls", "pincushion", "seals", "shot-pouch")
def belt_things(P, size, word):
    style = P._style
    t = P.t * size
    hw, hd, yo = P.ring(P.hipz + 0.1 * P.t)
    left, right = _hip(P, 1), _hip(P, -1)
    front = Vector((0, yo - hd - 0.05, P.hipz + 0.08 * P.t))
    if style == "book":              # its book, on the hip, strapped shut
        P.items("belt_book", M(P, book(left + Vector((0.03 * t, 0, -0.08 * t)), 0.09 * t, 0.3 * t, 0.24 * t, cover=P.roles.get("under", "leather"), clasp="field:clasp:2.0")), "hips")
    elif style == "chain-tags":      # a fine chain looped at its belt, a tag on each link
        n = int(round(7 * size))
        pts, tags, alt = [], None, None
        for i in range(n + 1):
            a = math.pi * (1.0 + i / n)
            p = Vector((math.cos(a) * (hw + 0.04), yo - hd * 0.5 + math.sin(a) * (hd * 0.6 + 0.05), P.hipz + 0.1 * P.t - 0.16 * P.t * math.sin(math.pi * i / n)))
            pts.append(p)
            if 0 < i < n:
                tg = g.box(p + Vector((0, -0.015, -0.07 * P.t)), (0.055 * P.t, 0.012, 0.1 * P.t), rot=(0, 0, 0.3 * (i % 3 - 1)))
                if i % 2:
                    tags = g.merge(tags, tg)
                else:
                    alt = g.merge(alt, tg)
        P.add("belt_chain", g.tube(pts, [0.014] * len(pts), n=3, caps=False), mat("metal_iron_light"), "hips")
        P.add("belt_tags", tags, mat("paper"), "hips")
        P.add("belt_tags_b", alt, mat("metal_brass"), "hips")
    elif style in ("lantern", "lantern-front"):
        c = (right + Vector((-0.06 * t, -0.04, -0.14 * t))) if style == "lantern" else Vector((0, yo - hd - 0.16 * t, P.kneez + 0.06))
        P.items("belt_lantern", M(P, lantern(c, 0.1 * t if style == "lantern" else 0.15 * t, word or "round", "lamp", 3.8)), "hips")
        if style == "lantern-front":
            P.add("lantern_chain", g.tube([front, c + Vector((0, 0, 0.19 * t))], 0.012, n=3), mat("metal_iron_light"), "hips")
    elif style in ("purse", "pouch", "shot-pouch"):
        c = right + Vector((-0.03 * t, -0.03, -0.1 * t))
        P.add("pouch", g.ico(c, 0.12 * t, sub=1, scale=(0.8, 0.7, 1.0)), P.material(word, "leather"), "hips", smooth=True)
        P.add("pouch_neck", _hoop(c + Vector((0, 0, 0.09 * t)), 0.05 * t, 0.045 * t, 0.014, u=X, v=Y, n=6, sides=3), mat("cord"), "hips")
        if style == "purse":
            P.add("purse_coin", _disc(c + Vector((0.0, -0.09 * t, 0.0)), 0.045 * t, normal=Y, thick=0.014, n=6), mat("metal_brass"), "hips")
    elif style == "tools":           # the handles of things, in loops
        geo = None
        for i in range(3):
            p = front + Vector(((i - 1) * 0.13 * P.t, 0, 0))
            geo = g.merge(geo, g.tube([p + Vector((0, -0.02, 0.1 * t)), p + Vector((0, -0.02, -0.22 * t))], 0.022, n=4))
        P.add("belt_tools", geo, mat("metal_iron_light"), "hips")
    elif style in ("keys", "seals"):
        c = left + Vector((0.02, -0.04, -0.06 * t))
        P.add("key_ring", _hoop(c, 0.07 * t, 0.07 * t, 0.012, u=Y, v=Z, n=8, sides=3), mat("metal_iron_light"), "hips")
        geo = None
        for i in range(4):
            p = c + Vector((0.0, (i - 1.5) * 0.04 * t, -0.07 * t))
            if style == "keys":
                geo = g.merge(geo, g.tube([p, p + Vector((0.01, 0, -0.16 * t))], 0.014, n=3), g.box(p + Vector((0.01, 0.02 * t, -0.14 * t)), (0.012, 0.045 * t, 0.045 * t)))
            else:
                geo = g.merge(geo, _disc(p + Vector((0.012, 0, -0.07 * t)), 0.04 * t, normal=X, thick=0.02, n=6))
        P.add("belt_" + style, geo, mat("metal_brass") if style == "keys" else mat("seal_wax"), "hips")
    elif style == "kettle":
        c = Vector((0, yo + hd + 0.14 * t, P.hipz + 0.1 * P.t))
        P.add("kettle", g.lathe([(0.03, -0.1 * t), (0.13 * t, -0.08 * t), (0.15 * t, 0.02), (0.1 * t, 0.1 * t), (0.03, 0.12 * t)], n=8, centre=c), mat("metal_dark"), "hips", smooth=True)
        P.add("kettle_spout", g.tube([c + Vector((0.1 * t, 0, 0)), c + Vector((0.26 * t, 0, 0.1 * t))], [0.03 * t, 0.016 * t], n=4), mat("metal_dark"), "hips")
        P.add("kettle_handle", _hoop(c + Vector((0, 0, 0.1 * t)), 0.1 * t, 0.1 * t, 0.014, u=X, v=Z, n=8, sides=3), mat("metal_iron_light"), "hips")
    elif style == "satchel":         # a satchel of papers bigger than its chest
        c = left + Vector((0.1 * t, -0.02, -0.12 * t))
        P.add("satchel", g.box(c, (0.2 * t, 0.42 * t, 0.4 * t)), P.material(word, "leather"), "hips", smooth=False)
        P.add("satchel_strap", g.tube([c + Vector((0, 0, 0.2 * t)), Vector((-P.sx * 0.6, P.J["chest"].y, P.armz + 0.06))], 0.03, n=4, flat=0.4), P.material(word, "leather"), "chest", smooth=True)
        papers = None
        for i in range(4):
            papers = g.merge(papers, g.box(c + Vector(((i - 1.5) * 0.035 * t, (i % 2 - 0.5) * 0.08 * t, 0.24 * t + 0.02 * i)), (0.02, 0.34 * t, 0.18 * t), rot=(0, 0.1 * (i - 1.5), 0)))
        P.add("satchel_papers", papers, mat("paper"), "hips")
    elif style == "ledger-chained":  # a ledger chained to its belt
        c = left + Vector((0.07 * t, -0.06, -0.3 * t))
        P.items("ledger", M(P, book(c, 0.12 * t, 0.36 * t, 0.3 * t, cover="leather_dark", clasp="metal_brass", slips=3)), "hips")
        pts = [left + Vector((0, -0.02, 0.02)), left + Vector((0.1 * t, -0.06, -0.08 * t)), c + Vector((0, 0, 0.16 * t))]
        P.add("ledger_chain", g.tube(pts, 0.018, n=3), mat("metal_iron_light"), "hips")
    elif style == "chalk-ring":      # a ring of chalk and cord at its hip
        c = left + Vector((0.03, -0.02, -0.16 * t))
        P.add("cord_coil", g.merge(_hoop(c, 0.14 * t, 0.14 * t, 0.022, u=Y, v=Z, n=10, sides=4), _hoop(c + Vector((0.02, 0, 0)), 0.12 * t, 0.12 * t, 0.022, u=Y, v=Z, n=10, sides=4)), mat("cord"), "hips", smooth=True)
        P.add("chalk", g.tube([c + Vector((0.04, 0.02, 0.1 * t)), c + Vector((0.04, 0.02, -0.12 * t))], 0.03, n=5), mat("chalk"), "hips")
    elif style == "bandage-rolls":
        geo = None
        for i in range(3):
            p = front + Vector(((i - 1) * 0.14 * P.t, 0.0, -0.02))
            geo = g.merge(geo, g.tube([p + Vector((0, -0.02, 0.06 * t)), p + Vector((0, -0.02, -0.08 * t))], 0.05 * t, n=7))
        P.add("bandage_rolls", geo, mat("paper"), "hips", smooth=True)
    else:                            # a pincushion
        c = front + Vector((0.12 * P.t, -0.02, 0))
        P.add("pincushion", g.ico(c, 0.07 * t, sub=1, scale=(1, 0.7, 0.9)), mat("thread_red"), "hips", smooth=True)
        pins = None
        for i in range(4):
            a = i * 1.4
            pins = g.merge(pins, g.tube([c, c + Vector((0.06 * math.cos(a), -0.08, 0.06 * math.sin(a))) * t * 1.6], 0.006, n=3))
        P.add("pins", pins, mat("metal_iron_light"), "hips")
