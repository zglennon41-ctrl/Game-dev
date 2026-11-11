"""The small people's lines (lines_people.py): what is in their hands, and what keeps them
company. A thing in a hand is drawn as the hand hangs at its side: the fist at the origin,
+X away from the body, -Y forward, +Z up (Person.hold turns it into the rest pose). What
stands on the ground round a form rides the root, so it does not sway with it."""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import mat, field
from lines_people import slot, _hoop, _disc, book, lantern
from people_things import M, shifted
from people_dress import arm_row


def _out(side, items):
    """Items drawn for the left hand (+X away from the body), as the right hand holds them."""
    if side == "l":
        return items
    return [(([Vector((-p[0], p[1], p[2])) for p in geo[0]], [tuple(reversed(f)) for f in geo[1]]) if geo else geo, m) for geo, m in items]


def hand_items(P, style, k, word):
    """[(geometry, material name)] for one thing in a hand; k is its size."""
    if style in ("bill", "letter-open"):
        out = [(g.box((0.03, -0.04 * k, -0.16 * k), (0.02, 0.26 * k, 0.34 * k)), "paper")]
        if style == "bill":
            out.append((g.box((0.045, -0.04 * k, -0.08 * k), (0.012, 0.2 * k, 0.03 * k)), "seal_wax"))
            for i in range(3):
                out.append((g.box((0.045, -0.04 * k, (-0.16 - 0.05 * i) * k), (0.012, 0.18 * k, 0.012 * k)), "ink"))
        else:
            out.append((_disc((0.045, -0.04 * k, -0.3 * k), 0.06 * k, normal=X, thick=0.02, n=7), "seal_wax"))
            out.append((g.blade((0.04, 0.0, -0.3 * k), (0.04, 0.06 * k, -0.56 * k), 0.05 * k, normal=X), "thread_red"))
            out.append((g.blade((0.04, -0.06 * k, -0.3 * k), (0.04, -0.12 * k, -0.52 * k), 0.05 * k, normal=X), "thread_red"))
        return out
    if style == "writ":              # a writ, rolled and sealed
        return [(g.tube([(0, 0.16 * k, -0.02), (0, -0.34 * k, -0.02)], 0.05 * k, n=7), "paper"), (_hoop((0, -0.1 * k, -0.02), 0.055 * k, 0.055 * k, 0.014, u=X, v=Z, n=7, sides=3), "seal_wax"),
                (_disc((0.0, -0.1 * k, -0.09 * k), 0.045 * k, normal=Z, thick=0.02, n=7), "seal_wax")]
    if style == "writ-long":         # a writ unrolled, and still unrolling
        pts = [(0.0, -0.02, 0.02), (0.02, -0.06, -0.5 * k), (0.04, 0.12, -0.92 * k), (0.02, 0.5 * k, -1.0 * k)]
        out = [(g.tongue(pts, [0.3 * k] * 4, thick=0.06, normal=Y), "paper"), (g.tube([(-0.17 * k, -0.02, 0.03), (0.17 * k, -0.02, 0.03)], 0.04 * k, n=6), "wood")]
        lines = None
        for i in range(5):
            lines = g.merge(lines, g.box((0.012 + 0.004 * i, -0.075 - 0.004 * i, (-0.1 - 0.075 * i) * k), (0.2 * k, 0.012, 0.014 * k)))
        out.append((lines, "ink"))
        return out
    if style == "paper-bag":
        return [(g.lathe([(0.02, -0.26 * k), (0.12 * k, -0.24 * k), (0.14 * k, -0.06 * k), (0.1 * k, 0.0), (0.12 * k, 0.03 * k)], n=6, centre=(0.02, 0, -0.04 * k)), "paper_old")]
    if style == "quill":
        return [(g.blade((0, 0.0, -0.1 * k), (0.02 * k, 0.14 * k, 0.56 * k), 0.14 * k, normal=X, belly=0.6), "feather_pale"), (g.cone((0, 0, -0.1 * k), (0, -0.02, -0.2 * k), 0.012, n=4), "void")]
    if style == "mallet":
        return [(g.tube([(0, 0, -0.1 * k), (0, 0, 0.44 * k)], 0.028 * k, n=5), "wood"), (g.box((0, 0, 0.5 * k), (0.16 * k, 0.3 * k, 0.18 * k)), "metal_iron")]
    if style == "snuffer":           # for putting lights out
        tip = Vector((0, -0.3 * k, 0.72 * k))
        return [(g.tube([(0, 0, -0.06 * k), tip], 0.016 * k, n=4), "metal_iron_light"), (g.lathe([(0.09 * k, -0.12 * k), (0.07 * k, 0.0), (0.0, 0.04 * k)], n=7, centre=tip + Vector((0, -0.05 * k, -0.02 * k))), "tin")]
    if style == "candle":
        return [(g.tube([(0, 0, -0.1 * k), (0, 0, 0.5 * k)], 0.04 * k, n=6), "paper"), (g.blade((0, 0, 0.5 * k), (0.01, 0, 0.72 * k), 0.09 * k, normal=Y, belly=0.35), "field:lamp:4.2"),
                (_disc((0, 0, -0.1 * k), 0.09 * k, normal=Z, thick=0.02, n=7), "metal_brass")]
    if style == "scales":            # a balance, hung from the hand
        out = [(g.tube([(0, 0, 0), (0, 0, -0.1 * k)], 0.012, n=3), "metal_brass"), (g.tube([(0, -0.26 * k, -0.1 * k), (0, 0.26 * k, -0.1 * k)], 0.014, n=3), "metal_brass")]
        for s in (1, -1):
            c = Vector((0, s * 0.26 * k, -0.4 * k - 0.03 * s * k))
            out.append((g.lathe([(0.02, -0.02 * k), (0.1 * k, 0.0), (0.11 * k, 0.03 * k)], n=7, centre=c), "metal_brass"))
            out.append((g.merge(g.tube([(0, s * 0.26 * k, -0.1 * k), c + Vector((0.09 * k, 0, 0.03 * k))], 0.006, n=3), g.tube([(0, s * 0.26 * k, -0.1 * k), c + Vector((-0.09 * k, 0, 0.03 * k))], 0.006, n=3)), "cord"))
        return out
    if style in ("relic", "flask"):
        if style == "relic":         # a small old thing, with the field still in it
            return [(g.ico((0.02, -0.03, -0.08 * k), 0.08 * k, sub=1, scale=(1, 0.7, 1.2)), "field:relic:3.0"), (_hoop((0.02, -0.03, -0.08 * k), 0.1 * k, 0.12 * k, 0.014, u=X, v=Z, n=8, sides=3), "metal_brass")]
        return [(g.lathe([(0.02, -0.16 * k), (0.07 * k, -0.14 * k), (0.07 * k, -0.02 * k), (0.03 * k, 0.03 * k), (0.03 * k, 0.07 * k)], n=6, centre=(0.02, -0.02, 0)), "glass"),
                (g.ico((0.02, -0.02, -0.09 * k), 0.05 * k, sub=1), "field:relic:3.0")]
    if style == "coal-fist":         # a coal glowing in its closed fist
        out = [(g.ico((0.0, -0.01, 0.0), 0.12 * k, sub=1), "field:ember:4.0")]
        lumps = None
        for i in range(4):
            a = i * 1.7
            lumps = g.merge(lumps, g.ico((0.1 * k * math.cos(a), 0.06 * k * math.sin(a), 0.1 * k * math.sin(a * 1.3)), 0.06 * k, sub=0))
        out.append((lumps, "coal_lump"))
        return out
    if style == "broken-chain":
        geo = None
        for i in range(4):
            geo = g.merge(geo, g.ico((0.0, 0.0, 0.1 * k - 0.11 * k * i), 0.06 * k, sub=1, scale=(1.0, 0.5, 1.0) if i % 2 else (0.5, 1.0, 1.0)))
        return [(geo, "metal_iron_light")]
    if style == "toll-bowl":         # a bowl held out, for what is owed
        c = Vector((0, -0.02, -0.32 * k))
        out = [(g.lathe([(0.02, -0.05 * k), (0.13 * k, -0.02 * k), (0.16 * k, 0.05 * k)], n=8, centre=c), "metal_brass"), (_disc(c + Vector((0, 0, 0.0)), 0.06 * k, normal=Z, thick=0.02, n=6), "field:coin:2.4")]
        cords = None
        for i in range(3):
            a = 2 * math.pi * i / 3
            cords = g.merge(cords, g.tube([(0, 0, 0), c + Vector((0.15 * k * math.cos(a), 0.15 * k * math.sin(a), 0.05 * k))], 0.007, n=3))
        out.append((cords, "cord"))
        return out
    if style in ("needle", "needle-lance"):
        L = (0.6 if style == "needle" else 1.5) * k
        out = [(g.tube([(0, 0, -0.14 * k if style == "needle" else -0.5 * k), (0, 0, L)], [0.016 * k, 0.004], n=4), "metal_iron_light")]
        z0 = -0.12 * k if style == "needle" else -0.46 * k
        out.append((_hoop((0, 0, z0), 0.012 * k, 0.03 * k, 0.006, u=X, v=Z, n=6, sides=3), "metal_iron_light"))
        if style == "needle":        # and its thread
            out.append((g.tube([(0, 0, z0), (0.06 * k, 0.1 * k, z0 - 0.2 * k), (-0.04 * k, 0.2 * k, z0 - 0.42 * k), (0.05 * k, 0.26 * k, z0 - 0.62 * k)], 0.008, n=3), word or "thread_red"))
        else:                        # and a pennant
            out.append((g.blade((0, 0, L * 0.8), (0, 0.34 * k, L * 0.74), 0.16 * k, normal=X, belly=0.25), word or "thread_red"))
        return out
    if style == "button-shield":     # a button for a shield
        c = Vector((0.08 * k, 0.0, 0.14 * k))
        holes = None
        for dy, dz in ((0.07, 0.07), (-0.07, 0.07), (0.07, -0.07), (-0.07, -0.07)):
            holes = g.merge(holes, _disc(c + Vector((0.02, dy * k, dz * k)), 0.035 * k, normal=X, thick=0.02, n=6))
        return [(_disc(c, 0.28 * k, normal=X, thick=0.035 * k, n=10), "bone"), (_hoop(c + Vector((0.01, 0, 0)), 0.26 * k, 0.26 * k, 0.025 * k, u=Y, v=Z, n=10, sides=4), "horn_ridge"), (holes, "void")]
    if style == "coal-shell":
        return lantern((0.0, -0.05 * k, -0.02 * k), 0.12 * k, "shell", "ember", 4.0)
    if style == "rag":
        return [(g.blade((0, 0, 0.02), (0.03, 0.04, -0.4 * k), 0.26 * k, normal=X, belly=0.5), "cloth_wool")]
    if style == "chain-lamp":        # a length of fine chain with a tiny lamp on the end
        L = 0.62 * k
        return [(g.tube([(0, 0, 0), (0.02, -0.02, -L * 0.5), (0, -0.03, -L)], 0.012, n=3), "metal_iron_light")] + lantern((0, -0.03, -L - 0.12 * k), 0.09 * k, "round", "lamp", 4.2, handle=False)
    if style == "key-ring":
        out = [(_hoop((0, 0, -0.16 * k), 0.14 * k, 0.14 * k, 0.014, u=Y, v=Z, n=10, sides=3), "metal_iron_light")]
        keys = None
        for i in range(3):
            p = Vector((0.0, (i - 1) * 0.07 * k, -0.3 * k))
            keys = g.merge(keys, g.tube([p, p + Vector((0, 0, -0.2 * k))], 0.014, n=3), g.box(p + Vector((0, 0.03 * k, -0.17 * k)), (0.012, 0.06 * k, 0.06 * k)), _hoop(p + Vector((0, 0, 0.03 * k)), 0.03 * k, 0.03 * k, 0.008, u=Y, v=Z, n=6, sides=3))
        out.append((keys, "metal_brass"))
        return out
    if style == "lantern":           # a lantern, by its ring
        s = 0.16 * k
        return lantern((0, 0, -s * 1.3 - 0.02), s, word or "round", "lamp", 4.0)
    if style == "lantern-stick":     # held up to whatever is nearest
        tip = Vector((0, -0.36 * k, 0.56 * k))
        return [(g.tube([(0, 0.02, -0.1 * k), tip], 0.016 * k, n=4), "wood")] + lantern(tip + Vector((0, -0.02, -0.2 * k)), 0.12 * k, word or "round", "lamp", 4.2)
    if style == "lantern-low":       # carried low, at the height of someone seated
        L = max(0.3, (P.armz - (P.J["handslot.l"].x - P.sx)) - 0.5 * k)
        return [(g.tube([(0, 0, 0), (0, -0.02, -L + 0.2 * k)], 0.012, n=3), "metal_iron_light")] + lantern((0, -0.02, -L), 0.15 * k, word or "cold", "lamp", 3.6)
    if style == "dial":              # a brass dial, for finding shelves
        c = Vector((0.02, -0.08 * k, -0.1 * k))
        return [(_disc(c, 0.13 * k, normal=Y, thick=0.05 * k, n=10), "metal_brass"), (_disc(c + Vector((0, -0.03 * k, 0)), 0.105 * k, normal=Y, thick=0.01, n=10), "paper"),
                (g.blade(c + Vector((0, -0.04 * k, 0)), c + Vector((0.06 * k, -0.04 * k, 0.07 * k)), 0.03 * k, normal=Y, thick=0.006), "field:seam:2.4")]
    if style == "thorn":             # a thorn as long as itself (upright: at the salute)
        if word == "upright":
            return [(g.tube([(0, 0, -0.5 * k), (0, 0, 0.5 * k), (0.02, 0, 1.6 * k)], [0.045 * k, 0.04 * k, 0.004], n=5), "thorn")]
        return [(g.tube([(0, 0.5 * k, 0.0), (0, -0.4 * k, 0.02), (0, -1.3 * k, 0.08 * k)], [0.045 * k, 0.04 * k, 0.004], n=5), "thorn")]
    if style == "short-blade":       # a short blade (wood, for practice, unless it says steel)
        m = "wood" if word != "steel" else "metal_iron_light"
        return [(g.tube([(0, 0.02, -0.1 * k), (0, -0.02, 0.1 * k)], 0.026 * k, n=5), "leather_dark"), (g.box((0, -0.02, 0.1 * k), (0.03 * k, 0.2 * k, 0.03 * k)), m),
                (g.blade((0, -0.02, 0.1 * k), (0, -0.14 * k, 0.72 * k), 0.1 * k, normal=X, belly=0.2, thick=0.02 * k), m)]
    if style in ("shot", "stone"):
        if style == "shot":          # the next shot, already in its open hand
            return [(g.ico((0, -0.02, -0.02), 0.075 * k, sub=1), "metal_dark"), (g.ico((0.0, -0.06 * k, 0.02 * k), 0.025 * k, sub=0), "field:seam:3.0")]
        return [(g.ico((0, -0.01, -0.02), 0.11 * k, sub=1, scale=(1.0, 0.8, 0.9)), "stone_face")]
    if style == "spanner":           # carried one-handed, like a club
        return [(g.tube([(0, 0, -0.16 * k), (0, 0, 0.72 * k)], 0.032 * k, n=4, flat=0.5), "metal_iron_light"), (_hoop((0, 0, 0.82 * k), 0.1 * k, 0.1 * k, 0.036 * k, u=Y, v=Z, n=8, sides=4), "metal_iron_light"),
                (_hoop((0, 0, -0.2 * k), 0.05 * k, 0.05 * k, 0.022 * k, u=Y, v=Z, n=7, sides=4), "metal_iron_light")]
    if style == "trowel":            # worn to half its width
        return [(g.tube([(0, 0.04, 0.0), (0, -0.1 * k, 0.0)], 0.028 * k, n=5), "wood"), (g.tube([(0, -0.1 * k, 0.0), (0, -0.16 * k, -0.06 * k)], 0.014 * k, n=4), "metal_iron_light"),
                (g.blade((0, -0.14 * k, -0.06 * k), (0, -0.52 * k, -0.06 * k), 0.11 * k, normal=Z, belly=0.3, thick=0.008), "metal_iron_light")]
    if style in ("chalk", "seal-stamp", "brush-tool"):
        if style == "chalk":
            return [(g.tube([(0, 0.02, 0.0), (0, -0.14 * k, 0.02)], 0.03 * k, n=5), "chalk")]
        if style == "seal-stamp":
            return [(g.tube([(0, 0, 0.1 * k), (0, 0, -0.1 * k)], 0.035 * k, n=6), "wood"), (_disc((0, 0, -0.13 * k), 0.07 * k, normal=Z, thick=0.05 * k, n=8), "metal_brass"),
                    (_disc((0, 0, -0.16 * k), 0.055 * k, normal=Z, thick=0.012, n=8), "field:seal:2.4")]
        return [(g.tube([(0, 0, -0.1 * k), (0, 0, 0.34 * k)], 0.022 * k, n=4), "wood"), (g.cone((0, 0, 0.34 * k), (0, 0, 0.56 * k), 0.06 * k, n=5), "fur_pale")]
    if style == "cup-shade":         # a dark dish before the lantern: the light goes one way only
        s = 0.16 * k
        c = Vector((0, 0, -s * 1.3 - 0.02))
        return lantern(c, s, "round", "lamp", 4.4) + [(g.lathe([(0.02, 0.0), (0.2 * k, 0.07 * k), (0.25 * k, 0.16 * k)], n=8, centre=(0, 0, 0)), "metal_dark")]
    return []


@slot("right", *"bill letter-open writ writ-long paper-bag quill mallet snuffer candle scales relic flask coal-fist broken-chain toll-bowl needle needle-lance button-shield coal-shell rag chain-lamp key-ring lantern lantern-stick lantern-low dial thorn short-blade shot stone spanner trowel chalk seal-stamp brush-tool cup-shade".split())
def right_hand(P, size, word):
    _hand(P, "r", size, word)


@slot("left", *"bill letter-open writ writ-long paper-bag quill mallet snuffer candle scales relic flask coal-fist broken-chain toll-bowl needle needle-lance button-shield coal-shell rag chain-lamp key-ring lantern lantern-stick lantern-low dial thorn short-blade shot stone spanner trowel chalk seal-stamp brush-tool cup-shade".split())
def left_hand(P, size, word):
    _hand(P, "l", size, word)


def _hand(P, side, size, word):
    style = P._style
    k = (0.45 + 0.55 * P.t) * size
    items = hand_items(P, style, k, word)
    if style == "cup-shade":         # the dish stands before the lamp, on its side
        dish = items[-1]
        s = 0.16 * k
        geo = ([Vector((p.x, -(p.z) - 0.14 * k, p.y - s * 1.3)) for p in dish[0][0]], dish[0][1])
        items = items[:-1] + [(geo, dish[1])]
    P.hold(side, style, M(P, _out(side, items)))


@slot("left", "book-arm", "book-grown", "edge-hand")
@slot("right", "barrel-arm", "edge-hand")
def arm_things(P, size, word):
    """What an arm has become, or has grown into it: these ride the forearm, not the hand."""
    style = P._style
    s, tag = (1, "l") if style in ("book-arm", "book-grown") or (style == "edge-hand" and P._slot == "left") else (-1, "r")
    k = (0.45 + 0.55 * P.t) * size
    if style == "book-arm":          # a clasped book under one arm, thick with slips
        hw, hd, yo = P.ring(P.chestz - 0.2 * P.t)
        c = Vector((s * (hw + 0.07 * k), yo - 0.04, P.chestz - 0.24 * P.t))
        P.items("book_arm", M(P, book(c, 0.14 * k, 0.4 * k, 0.5 * k, rot=(0.25, 0, 0), cover=P.roles.get("under", "leather"), clasp="metal_brass", slips=5, spine=s)), "chest")
    elif style == "book-grown":      # the book grown into the crook of its arm
        x = (P.ex + P.wx) / 2
        c = Vector((s * x, P.army, P.armz + arm_row(P, x)[2] + 0.07 * k))
        P.items("book_grown", M(P, book(c, 0.5 * k, 0.14 * k, 0.38 * k, cover=P.roles.get("under", "leather"), clasp="field:clasp:2.4", spine=-s)), "lowerarm." + tag)
        veins = None
        for i in range(3):
            xx = P.sx + (P.ex - P.sx) * (0.3 + 0.3 * i)
            row = arm_row(P, xx)
            veins = g.merge(veins, _hoop((s * xx, P.army, P.armz), row[1] + 0.014, row[2] + 0.014, 0.012, u=Y, v=Z, n=8, sides=3))
        P.add("book_veins", veins, field("script", 2.4), "upperarm." + tag)
    elif style == "edge-hand":       # its guard hand is edged, like a blade
        hx = P.J["hand.l"].x
        b0, tip = Vector((s * (P.ex + 0.06), P.army, P.armz + 0.02)), Vector((s * (hx + 0.55 * k), P.army - 0.02, P.armz))
        P.add("edge_hand", g.blade(b0, tip, 0.26 * k, normal=Y, belly=0.3, thick=0.03), mat("metal_iron_light"), "lowerarm." + tag)
        P.add("edge_line", g.tube([b0 + Vector((0, 0, 0.11 * k)), tip], 0.008, n=3), field("seam", 2.4), "lowerarm." + tag)
    else:                            # one forearm made into a barrel
        hx = P.J["hand.l"].x
        a, b = Vector((s * (P.ex + 0.02), P.army, P.armz)), Vector((s * (hx + 0.62 * k), P.army, P.armz))
        P.add("barrel", g.tube([a, b], 0.1 * k, n=8), mat("metal_iron"), "lowerarm." + tag)
        P.add("barrel_bore", _disc(b + Vector((s * 0.004, 0, 0)), 0.06 * k, normal=X, thick=0.01, n=8), mat("void"), "lowerarm." + tag)
        bands = None
        for t in (0.12, 0.5, 0.92):
            bands = g.merge(bands, _hoop(a + (b - a) * t, 0.112 * k, 0.112 * k, 0.022 * k, u=Y, v=Z, n=8, sides=4))
        P.add("barrel_bands", bands, mat("metal_brass"), "lowerarm." + tag)
        P.add("barrel_sight", g.box(b + Vector((-s * 0.06 * k, 0, 0.13 * k)), (0.03 * k, 0.02, 0.05 * k)), mat("metal_brass"), "lowerarm." + tag)


# ======================================================================================
# What keeps it company
# ======================================================================================

@slot("around", "motes", "ring-lights", "gear-halo", "coals", "shades", "wedge", "little-ones", "afterglow", "light-ring", "ward-ring", "standing-air", "lamp-glass", "small-weather", "strings")
def around(P, size, word):
    style, hr, t = P._style, P.hr, P.t
    top = P.crown
    if style == "motes":             # small lights that keep it company
        spots = ((0.62, 0.1, top + 0.1), (-0.5, 0.3, P.armz + 0.3), (0.4, 0.4, P.armz - 0.1), (-0.66, 0.0, top - 0.2))
        for i, c in enumerate(spots[: max(1, int(round(size)))]):
            c = Vector(c)
            P.add("mote_%d" % i, g.ico(c, 0.07, sub=1), field("mote", 3.0), "root", smooth=True)
            P.add("mote_tail_%d" % i, g.tongue([c + Vector((0, 0.05, 0)), c + Vector((0.03, 0.22, -0.06)), c + Vector((-0.02, 0.4, -0.02))], [0.11, 0.08, 0.02], thick=0.4, normal=X), mat("shade_edge"), "root", smooth=True)
    elif style == "ring-lights":     # as many small lights as it has people to mind, in a ring round its head
        n = max(3, int(round(size)))
        geo = None
        for i in range(n):
            a = 2 * math.pi * i / n
            geo = g.merge(geo, g.ico((math.cos(a) * hr * 2.2, P.hcy + math.sin(a) * hr * 2.2, P.eye.z + 0.6 * hr + 0.16 * hr * math.sin(3 * a)), 0.2 * hr, sub=1))
        P.add("ring_lights", geo, field("mote", 3.2), "head", smooth=True)
        P.add("ring_thread", _hoop((0, P.hcy, P.eye.z + 0.6 * hr), hr * 2.2, hr * 2.2, 0.012 * hr, u=X, v=Y, n=16, sides=3), mat("shade_edge"), "head")
    elif style == "gear-halo":       # a ring of fine teeth, turning slowly round its head
        c = Vector((0, P.hcy + 0.05 * hr, top + 0.16 * hr))
        r = hr * 1.75 * size
        u = Vector((1, 0, 0.0))
        v = Vector((0, 0.94, 0.34))
        w = u.cross(v).normalized()
        teeth = 10
        rings = []
        for rad, lift in ((1.0, -0.5), (1.0, 0.5), (0.86, 0.5), (0.86, -0.5)):
            ring = []
            for i in range(teeth * 2):
                a = math.pi * i / teeth
                rr = r * (rad * (1.14 if i % 2 == 0 else 1.0) if rad == 1.0 else rad)
                ring.append(c + (u * math.cos(a) + v * math.sin(a)) * rr + w * lift * 0.09 * hr)
            rings.append(ring)
        rings.append(rings[0])
        P.add("gear_halo", g.loft(rings, caps=False), mat("metal_brass"), "head")
        spokes = None
        for i in range(3):
            a = math.pi * i / 3
            d = u * math.cos(a) + v * math.sin(a)
            spokes = g.merge(spokes, g.tube([c - d * r * 0.86, c + d * r * 0.86], 0.025 * hr, n=3))
        P.add("gear_spokes", spokes, mat("metal_brass"), "head")
    elif style == "coals":           # it sits in the coals to the waist
        r = (P.sx + 0.34) * size
        P.add("coal_bed", g.lathe([(r * 1.1, 0.0), (r, 0.12), (r * 0.8, P.hipz * 0.5), (r * 0.5, P.hipz * 0.84), (0.0, P.hipz * 0.9)], n=9, centre=(0, 0.02, 0)), mat("coal_lump"), "root", smooth=False)
        lit, dark = None, None
        for i in range(14):
            a = i * 2.4
            rr = r * (0.5 + 0.5 * ((i * 7) % 5) / 5.0)
            z = P.hipz * 0.9 * (1.0 - rr / (r * 1.1)) + 0.06
            lump = g.ico((rr * math.cos(a), 0.02 + rr * math.sin(a), z), 0.09 + 0.03 * (i % 3), sub=0)
            if i % 2:
                lit = g.merge(lit, lump)
            else:
                dark = g.merge(dark, lump)
        P.add("coals_lit", lit, field("ember", 3.4), "root")
        P.add("coals_dark", dark, mat("coal_lump"), "root")
    elif style == "shades":          # the dead, who come in behind it
        n = max(1, int(round(size)))
        for i in range(n):
            x = (i - (n - 1) / 2) * 0.7 + 0.1
            y = 0.7 + 0.34 * abs(i - (n - 1) / 2) + (0.5 * i if word == "line" else 0.0)
            if word == "line":
                x = 0.18 + 0.1 * (i % 2)
            h = top * (0.74 + 0.08 * (i % 2))
            P.add("shade_%d" % i, g.lathe([(0.22, 0.0), (0.16, h * 0.3), (0.12, h * 0.72), (0.15, h * 0.84), (0.11, h * 0.96), (0.0, h)], n=7, centre=(x, y, 0)), mat("shade_edge"), "root", smooth=True)
            P.add("shade_eye_%d" % i, g.ico((x, y - 0.12, h * 0.88), 0.035, sub=0), field("eyes_dim", 1.6), "root")
    elif style == "wedge":           # smaller genii, flying in a wedge behind it
        n = max(2, int(round(size)))
        body, wings = None, None
        for i in range(n):
            row = i // 2 + 1
            s = 1 if i % 2 == 0 else -1
            c = Vector((s * 0.42 * row, 0.45 * row, P.armz + 0.12 * row))
            body = g.merge(body, g.ico(c, 0.075, sub=1, scale=(0.8, 0.8, 1.2)))
            for ws in (1, -1):
                wings = g.merge(wings, g.blade(c + Vector((0, 0.03, 0.04)), c + Vector((ws * 0.2, 0.1, 0.14)), 0.09, normal=(0, -1, 0.2), belly=0.55, thick=0.008))
        P.add("wedge", body, field("mote", 3.0), "root", smooth=True)
        P.add("wedge_wings", wings, field("wing", 1.0), "root")
    elif style == "little-ones":     # little clay things on wheels, carrying its tools and watching its hands
        n = max(1, int(round(size)))
        clay, wood, eyes, tools = None, None, None, None
        for i in range(n):
            c = Vector((0.55 - 0.5 * i, 0.55 + 0.26 * (i % 2), 0.0))
            k = 0.2 + 0.03 * (i % 2)
            clay = g.merge(clay, g.ico(c + Vector((0, 0, k * 1.0)), k, sub=1, scale=(0.9, 0.9, 0.8)), g.ico(c + Vector((0, -k * 0.2, k * 2.0)), k * 0.62, sub=1))
            for ws in (1, -1):
                wood = g.merge(wood, _disc(c + Vector((ws * k * 0.9, 0, k * 0.42)), k * 0.42, normal=X, thick=0.05, n=8))
                eyes = g.merge(eyes, g.ico(c + Vector((ws * k * 0.24, -k * 0.74, k * 2.1)), k * 0.11, sub=0))
            tools = g.merge(tools, g.tube([c + Vector((k * 0.3, 0.1, k * 1.6)), c + Vector((k * 0.5, 0.2, k * 3.3 + 0.1 * (i % 2)))], 0.022, n=4))
        P.add("little_ones", clay, P.skin, "root", smooth=True)
        P.add("little_wheels", wood, mat("wood"), "root")
        P.add("little_eyes", eyes, field("eyes", 3.4), "root")
        P.add("little_tools", tools, mat("metal_iron_light"), "root")
    elif style == "afterglow":       # a ring of afterglow hangs where it last flared
        c = Vector((-0.86 * size, 0.5, P.armz + 0.1))
        P.add("afterglow", _hoop(c, 0.5 * size, 0.5 * size, 0.024, u=Vector((0.8, 0.6, 0)), v=Z, n=16, sides=3), field("flare", 2.4), "root")
        P.add("afterglow_2", _hoop(c + Vector((-0.1, 0.1, 0)), 0.66 * size, 0.66 * size, 0.012, u=Vector((0.8, 0.6, 0)), v=Z, n=16, sides=3), field("flare_dim", 1.0), "root")
        rays = None
        for i in range(6):
            a = 2 * math.pi * i / 6 + 0.3
            d = Vector((0.8, 0.6, 0)) * math.cos(a) + Z * math.sin(a)
            rays = g.merge(rays, g.blade(c + d * 0.1 * size, c + d * 0.38 * size, 0.06, normal=Vector((-0.6, 0.8, 0)), belly=0.3, thick=0.006))
        P.add("afterglow_rays", rays, field("flare", 2.0), "root")
    elif style in ("light-ring", "ward-ring"):
        r = (P.sx + 0.6) * size
        P.add("ground_ring", _hoop((0, 0.02, 0.03), r, r, 0.022, u=X, v=Y, n=20, sides=3), field("ring", 2.4) if style == "light-ring" else mat("chalk"), "root")
        if style == "ward-ring":     # and the marks it is knotted with
            marks = None
            for i in range(4):
                a = math.pi / 4 + i * math.pi / 2
                marks = g.merge(marks, g.box((math.cos(a) * r, 0.02 + math.sin(a) * r, 0.05), (0.14, 0.05, 0.03), rot=(0, 0, a)))
            P.add("ward_marks", marks, field("ward", 2.6), "root")
    elif style == "standing-air":    # the air stands still round it
        c = Vector((0, 0.0, P.chestz))
        for i, (tilt, r) in enumerate(((0.0, 0.62), (0.9, 0.74), (-0.9, 0.86))):
            u = Vector((math.cos(tilt), 0, math.sin(tilt)))
            P.add("still_%d" % i, _hoop(c, r * size, r * size, 0.012, u=u, v=Y, n=20, sides=3), field("still", 1.4), "root")
    elif style == "lamp-glass":      # it sits inside a lamp's glass
        r = (P.sx + 0.26) * size
        z0, z1 = P.hipz - 0.06, top + 0.14
        c = neck_y = P.J["chest"].y
        brass = mat("metal_brass")
        bars = None
        for i in range(6):
            a = 2 * math.pi * i / 6 + math.pi / 6
            bars = g.merge(bars, g.tube([(r * math.cos(a), c + r * math.sin(a), z0), (r * 0.94 * math.cos(a), c + r * 0.94 * math.sin(a), z1)], 0.022, n=4))
        P.add("glass_bars", bars, brass, "chest")
        P.add("glass_base", g.lathe([(r * 0.5, z0 - 0.12), (r * 1.06, z0 - 0.04), (r * 1.06, z0 + 0.02), (r * 0.5, z0 + 0.02)], n=6, centre=(0, c, 0), phase=math.pi / 6), brass, "chest")
        P.add("glass_roof", g.lathe([(r * 1.14, z1 - 0.02), (r * 1.14, z1 + 0.03), (r * 0.6, z1 + 0.26 * size), (r * 0.16, z1 + 0.4 * size), (r * 0.16, z1 + 0.5 * size), (0.0, z1 + 0.56 * size)], n=6, centre=(0, c, 0), phase=math.pi / 6), brass, "chest")
        P.add("glass_ring", _hoop((0, c, z1 + 0.62 * size), 0.08, 0.08, 0.02, u=X, v=Z, n=8, sides=3), mat("metal_iron_light"), "chest")
    elif style == "small-weather":   # it sneezes small weather
        c = Vector((0.1 * hr, P.hcy, top + 0.9 * hr))
        cloud = None
        for dx, dy, dz, rr in ((0.0, 0.0, 0.0, 0.7), (0.7, 0.1, -0.06, 0.5), (-0.66, -0.06, -0.1, 0.52), (0.2, 0.3, 0.26, 0.44)):
            cloud = g.merge(cloud, g.ico(c + Vector((dx, dy, dz)) * hr * size, rr * hr * size, sub=1))
        P.add("weather_cloud", cloud, mat("smoke") if word != "pale" else mat("ice_pale"), "head", smooth=True)
        bits = None
        for i in range(5):
            p = c + Vector(((i - 2) * 0.34, 0.05 * (i % 2), -0.74 - 0.26 * (i % 2))) * hr * size
            bits = g.merge(bits, g.ico(p, 0.07 * hr, sub=0) if word != "storm" else g.blade(p + Vector((0, 0, 0.2 * hr)), p + Vector((0.1 * hr, 0, -0.3 * hr)), 0.1 * hr, normal=Y, thick=0.01))
        P.add("weather_fall", bits, mat("ice_pale") if word != "storm" else field("bolt", 3.4), "head")
    else:                            # strings, as if it were moved from above
        up = 0.55 * size
        P.add("string_head", g.tube([(0, P.hcy, top), (0, P.hcy, top + up)], 0.012, n=3), field("seam", 1.6), "head")
        P.add("string_bar", g.merge(g.tube([(-0.46 * size, P.hcy, top + up), (0.46 * size, P.hcy, top + up)], 0.035, n=4), g.tube([(0, P.hcy - 0.26 * size, top + up), (0, P.hcy + 0.26 * size, top + up)], 0.035, n=4)), mat("wood"), "head")
        for sd, tag in ((1, "l"), (-1, "r")):      # from the bar's ends to its wrists (they hang from the head, as the bar does)
            P.add("string_" + tag, g.tube([(sd * 0.46 * size, P.hcy, top + up), (sd * P.sx * 1.3, P.army, P.armz + 0.1)], 0.012, n=3), field("seam", 1.6), "head")
