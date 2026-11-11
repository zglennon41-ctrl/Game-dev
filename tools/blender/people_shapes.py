"""The small people's lines (lines_people.py): the forms that are no longer people.

The Imp's Marginal moved into the margins of a book, and what it becomes stays there: a book
open in the air, and a thin thing of ink come up out of its gutter (genius_homes.py's
marginal, grown three ways). The Sprite's Star-burst is no longer one light but a drift of
them. Neither has a rig: the game floats them, as it does their silhouettes
(daemon-marginal, aspect-wisps)."""
import math
import os

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
import genius_kit as kit
from genius_kit import mat, field
import genius_homes as gh
from lines_people import _hoop, _disc, OUT, ROOT, log


def _export(name, items, sockets, ref, path):
    ob = g.pieces(name, [(geo, m) for geo, m in items if geo and geo[0]])
    for poly in ob.data.polygons:
        poly.use_smooth = ob.data.materials[poly.material_index].name.startswith(("ink", "field", "shade", "smoke"))
    sockets = dict(sockets)
    sockets["ref_top"] = kit.free_socket("ref_top", (0, 0, ref))
    tris = kit.Built([ob], sockets).export(path)
    return tris


def _open_book(zc, k, lines=6, marks=0):
    """A book lying open in the air at zc, k its size. [(geometry, material)]"""
    paper, lea = mat("paper"), mat("leather")
    items = []
    for s in (1, -1):
        T = Matrix.Translation((s * 0.005, 0, zc)) @ Matrix.Rotation(s * math.radians(-14), 4, "Y")
        items.append((g.moved(g.box((s * 0.15 * k, 0, 0.0), (0.3 * k, 0.4 * k, 0.035 * k)), T), paper))
        items.append((g.moved(g.box((s * 0.155 * k, 0, -0.024 * k), (0.32 * k, 0.42 * k, 0.014 * k)), T), kit.mark("cover", lea)))
        ruled = None
        for i in range(lines):
            ruled = g.merge(ruled, g.box((s * 0.15 * k, (-0.14 + 0.28 * i / max(1, lines - 1)) * k, 0.019 * k), ((0.2 - 0.03 * (i % 2)) * k, 0.008 * k, 0.004)))
        items.append((g.moved(ruled, T), field("script", 2.2)))
        if marks:                     # what it has written in the margins
            notes = None
            for i in range(marks):
                notes = g.merge(notes, g.box((s * 0.275 * k, (-0.15 + 0.3 * i / max(1, marks - 1)) * k, 0.02 * k), (0.035 * k, 0.03 * k, 0.004)))
            items.append((g.moved(notes, T), field("gloss", 2.8)))
    return items


def marginal(form_id, level, spec):
    """rises: how the thing of ink comes up out of the book. climbs (its hands on the page
    edges), reads (tall, its eyes far apart, looking past the page), points (one long finger
    and a single eye riding above it)."""
    ink, edge = mat("ink"), mat("ink_edge")
    rises = spec.get("rises", "climbs")
    zc = 0.3
    k = float(spec.get("book", 1.0))
    items = _open_book(zc, k, lines=6 if rises == "climbs" else 8, marks=0 if rises == "climbs" else (5 if rises == "reads" else 3))
    eyes = field("eyes", 3.6)
    hd = Vector((0, -0.07, zc + 0.39))
    if rises == "climbs":
        neck = [(0, 0.02, zc), (0.0, 0.06, zc + 0.14), (0.02, 0.0, zc + 0.26), (0.0, -0.05, zc + 0.36)]
        items.append((g.tube(neck, [0.05, 0.036, 0.03, 0.034], n=6), ink))
        items.append((g.ico(hd, 0.06, sub=1, scale=(0.9, 1.25, 0.9)), ink))
        horns, lit = None, None
        for s in (1, -1):
            horns = g.merge(horns, g.tube([hd + Vector((s * 0.035, 0.02, 0.04)), hd + Vector((s * 0.07, 0.05, 0.11)), hd + Vector((s * 0.05, 0.09, 0.17))], [0.016, 0.011, 0.002], n=4))
            lit = g.merge(lit, g.ico(hd + Vector((s * 0.03, -0.055, 0.012)), 0.013, sub=0))
            arm = [(s * 0.03, 0.04, zc + 0.2), (s * 0.16, -0.02, zc + 0.2), (s * 0.27 * k, -0.12, zc + 0.08)]
            items.append((g.tube(arm, [0.02, 0.014, 0.01], n=5), ink))
            fingers = None
            for i in range(4):
                fingers = g.merge(fingers, g.tube([arm[2], Vector(arm[2]) + Vector((s * (0.02 + 0.012 * i), -0.05 + 0.03 * i, -0.045))], [0.008, 0.002], n=3))
            items.append((fingers, edge))
        items += [(horns, edge), (lit, eyes)]
        top = hd.z + 0.19
    elif rises == "reads":           # the Glossator
        neck = [(0, 0.03, zc), (0.02, 0.1, zc + 0.2), (-0.02, 0.08, zc + 0.42), (0.0, -0.02, zc + 0.6), (0.0, -0.12, zc + 0.66)]
        items.append((g.tube(neck, [0.06, 0.04, 0.032, 0.03, 0.036], n=6), ink))
        hd = Vector((0, -0.16, zc + 0.67))
        items.append((g.ico(hd, 0.06, sub=1, scale=(2.3, 1.1, 0.8)), ink))       # a head as wide as a line of print
        lit, lids, horns = None, None, None
        for s in (1, -1):
            c = hd + Vector((s * 0.15, -0.03, 0.0))
            items.append((g.tube([hd + Vector((s * 0.09, 0, 0)), c + Vector((s * 0.04, -0.02, 0.01))], [0.03, 0.036], n=5), ink))
            lit = g.merge(lit, g.ico(c + Vector((s * 0.05, -0.045, 0.01)), 0.03, sub=1))
            lids = g.merge(lids, _hoop(c + Vector((s * 0.05, -0.05, 0.01)), 0.036, 0.036, 0.006, u=X, v=Z, n=8, sides=3))
            horns = g.merge(horns, g.tube([hd + Vector((s * 0.06, 0.04, 0.03)), hd + Vector((s * 0.1, 0.12, 0.12)), hd + Vector((s * 0.06, 0.22, 0.16))], [0.018, 0.012, 0.002], n=4))
            arm = [(s * 0.03, 0.06, zc + 0.26), (s * 0.2, 0.0, zc + 0.3), (s * 0.3 * k, -0.14, zc + 0.1)]
            items.append((g.tube(arm, [0.02, 0.014, 0.01], n=5), ink))
        items += [(lit, eyes), (lids, edge), (horns, edge)]
        # the pen it annotates with, and the ribbons that keep its places
        items.append((g.blade((0.3 * k, -0.14, zc + 0.1), (0.36 * k, -0.02, zc + 0.44), 0.07, normal=X, belly=0.6), mat("feather_pale")))
        marks = None
        for i, x in enumerate((-0.2, -0.08, 0.06, 0.19)):
            marks = g.merge(marks, g.tongue([(x * k, 0.2 * k, zc - 0.01), (x * k, 0.23 * k, zc - 0.12), (x * k + 0.01, 0.22 * k, zc - (0.26 + 0.05 * (i % 2)))], [0.03, 0.03, 0.03], thick=0.2, normal=Y))
        items.append((marks, mat("seal_wax")))
        top = hd.z + 0.2
    else:                            # the Errata: one long finger, and an eye above it
        arm = [(0, 0.04, zc), (0.02, 0.12, zc + 0.2), (0.0, 0.1, zc + 0.44), (0.0, -0.04, zc + 0.6), (0.0, -0.2, zc + 0.6)]
        items.append((g.tube(arm, [0.07, 0.05, 0.045, 0.05, 0.055], n=6), ink))
        fist = Vector(arm[-1])
        items.append((g.ico(fist + Vector((0, -0.03, 0)), 0.07, sub=1, scale=(1.0, 1.1, 0.9)), ink))
        items.append((g.tube([fist + Vector((0, -0.06, 0.02)), fist + Vector((0, -0.26, 0.0)), fist + Vector((0, -0.46, -0.06))], [0.03, 0.022, 0.006], n=5), edge))
        curled = None
        for i in range(3):
            curled = g.merge(curled, g.tube([fist + Vector((0.02 * (i - 1), -0.08, -0.03)), fist + Vector((0.025 * (i - 1), -0.1, -0.08)), fist + Vector((0.02 * (i - 1), -0.04, -0.09))], [0.02, 0.018, 0.012], n=4))
        items.append((curled, edge))
        eye = fist + Vector((0, -0.02, 0.2))
        items.append((g.ico(eye, 0.075, sub=1), mat("eye_white")))
        items.append((g.ico(eye + Vector((0, -0.055, 0.0)), 0.046, sub=1, scale=(1, 0.5, 1)), eyes))
        items.append((g.ico(eye + Vector((0, -0.076, 0.0)), 0.018, sub=0, scale=(1, 0.4, 1)), mat("void")))
        items.append((g.merge(g.blade(eye + Vector((-0.09, 0, 0.03)), eye + Vector((0.09, 0, 0.03)), 0.09, normal=Z, belly=0.5, thick=0.012), g.tube([fist + Vector((0, 0, 0.06)), eye + Vector((0, 0.02, -0.07))], 0.012, n=3)), edge))
        # the corrections it has made, struck through and set right
        carets = None
        for i, (x, y) in enumerate(((0.16, -0.1), (-0.12, 0.02), (0.2, 0.12))):
            p = Vector((x * k, y * k, zc + 0.03 + abs(x) * 0.25))
            carets = g.merge(carets, g.blade(p, p + Vector((0.03, 0, 0.07)), 0.02, normal=Y, thick=0.006), g.blade(p + Vector((0.06, 0, 0)), p + Vector((0.03, 0, 0.07)), 0.02, normal=Y, thick=0.006))
        items.append((carets, field("gloss", 3.0)))
        hd = eye
        top = eye.z + 0.1
    items.append((g.tongue([(0, 0.03, zc + 0.02), (0.03, 0.12, zc - 0.1), (0.0, 0.1, zc - 0.24)], [0.05, 0.03, 0.003], thick=0.5, normal=(0, 1, 0)), kit.mark("drip", ink)))
    socks = gh._table(top, -0.13, zc + 0.3, 0.3, {"socket_head": [tuple(hd + Z * 0.06), Matrix.Scale(0.5, 3)], "socket_eyes": [tuple(hd + Vector((0, -0.06, 0.012))), Matrix.Scale(0.5, 3)],
                                                  "socket_mouth": [tuple(hd + Vector((0, -0.07, -0.02))), Matrix.Scale(0.5, 3)], "socket_light": [(0, 0, zc + 0.03)], "socket_keepsake": [(0, -0.2, zc - 0.03)]})
    path = os.path.join(OUT, form_id + ".glb")
    tris = _export(form_id, items, socks, zc + 0.5, path)
    log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


def starburst(form_id, level, spec):
    """Not one light but a drift of them, each with a little of its grin; the lantern they came
    out of still hangs in the middle, open."""
    # only the lights themselves are light: a streak or a wing that burned too would make one blur of them all
    flame, wisp, dark, brass = field("flame", 3.2), mat("wing_glass"), mat("void"), mat("metal_brass")
    n = int(spec.get("lights", 13))
    c0 = Vector((0, 0, 0.44))
    items = []
    lights, grins, tails, wings = None, None, None, None

    def one(c, r, d):
        nonlocal lights, grins, tails, wings
        lights = g.merge(lights, g.ico(c, r, sub=1))
        for s in (1, -1):
            grins = g.merge(grins, g.ico(c + Vector((s * r * 0.34, -r * 0.86, r * 0.26)), r * 0.15, sub=0, scale=(1, 0.5, 1.3)))
            wings = g.merge(wings, g.blade(c + Vector((s * r * 0.5, r * 0.4, r * 0.3)), c + Vector((s * r * 2.3, r * 1.0, r * 1.5)), r * 0.9, normal=(0, -1, 0.2), belly=0.55, thick=0.004))
        grins = g.merge(grins, g.tube([c + Vector((-r * 0.5, -r * 0.82, -r * 0.14)), c + Vector((0, -r * 0.98, -r * 0.4)), c + Vector((r * 0.5, -r * 0.82, -r * 0.14))], r * 0.07, n=3))
        if d.length > 1e-6:           # the streak it came down on
            tails = g.merge(tails, g.blade(c - d.normalized() * r * 0.8, c - d.normalized() * (r * 0.8 + d.length * 0.55), r * 1.3, normal=Y, belly=0.25, thick=0.004))
    one(c0 + Vector((0, -0.02, 0.08)), 0.075, Vector((0, 0, 0)))
    for i in range(n):
        a = i * 2.39996            # the golden angle: no two in a line
        h = -0.5 + 1.0 * (i + 0.5) / n
        rad = 0.24 + 0.26 * ((i * 5) % 7) / 7.0
        d = Vector((math.cos(a) * math.sqrt(1 - h * h), math.sin(a) * math.sqrt(1 - h * h) * 0.7, h * 0.9 + 0.2)) * rad
        one(c0 + d, 0.028 + 0.02 * ((i * 3) % 4) / 4.0, d)
    items += [(lights, flame), (grins, dark), (tails, wisp), (wings, wisp)]
    # the lantern, open and empty
    cage = g.merge(_hoop(c0 + Z * -0.07, 0.075, 0.075, 0.007, u=X, v=Y, n=10, sides=3), _hoop(c0 + Z * 0.06, 0.062, 0.062, 0.007, u=X, v=Y, n=10, sides=3))
    for i in range(4):
        a = math.pi / 4 + math.pi / 2 * i
        cage = g.merge(cage, g.tube([c0 + Vector((0.075 * math.cos(a), 0.075 * math.sin(a), -0.07)), c0 + Vector((0.062 * math.cos(a) * (1.5 if i == 0 else 1.0), 0.062 * math.sin(a) * (1.5 if i == 0 else 1.0), 0.06)),
                                     c0 + Vector((0.03 * math.cos(a), 0.03 * math.sin(a), 0.16))], [0.005, 0.005, 0.004], n=3))
    items.append((cage, brass))
    socks = kit._sockets({
        "socket_head": [tuple(c0 + Z * 0.2)], "socket_eyes": [tuple(c0 + Vector((0, -0.08, 0.1)))], "socket_mouth": [tuple(c0 + Vector((0, -0.08, 0.05)))], "socket_grip": [tuple(c0 + Vector((0.12, 0, 0)))],
        "socket_throat": [tuple(c0 + Vector((0, -0.08, -0.05)))], "socket_light": [tuple(c0)], "socket_back": [tuple(c0 + Vector((0, 0.1, 0.05)))], "socket_body": [tuple(c0 + Vector((0, -0.1, -0.02)))],
        "socket_tail": [tuple(c0 + Vector((0, 0.12, -0.05)))], "socket_arm_l": [tuple(c0 + Vector((0.11, 0, 0.02)))], "socket_arm_r": [tuple(c0 + Vector((-0.11, 0, 0.02)))],
        "socket_limb_fl": [tuple(c0 + Vector((0.06, -0.04, -0.11)))], "socket_limb_fr": [tuple(c0 + Vector((-0.06, -0.04, -0.11)))], "socket_keepsake": [tuple(c0 + Vector((0, -0.085, -0.062)))],
    })
    path = os.path.join(OUT, form_id + ".glb")
    tris = _export(form_id, items, socks, 0.72, path)
    log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))
