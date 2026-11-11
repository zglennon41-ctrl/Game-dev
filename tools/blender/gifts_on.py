"""WILDLINE genius kit: a giver's gift, made again for one base it sat badly on
(docs/genius-lines.md, "How the game wears it").

A hybrid wears its first base's bodies and its second's gift. Most gifts sit well on most
bodies; a few do not: a bird's wings on a shield were two sticks and a pair of chicken feet.
So a giver may make its gift again for one receiver: game/assets/genius/gifts/
<giver>-<feature>-on-<first base>.glb, which the game hangs in place of the giver's usual
part on that base's bodies and nowhere else. Such a part may be several pieces, each under an
empty named at_<socket>: the game hangs each piece on that socket of the body, so the part
fits a body whatever its width and height (a wing at each side of a shield, a head at its top).

  python tools/blender/gifts_on.py                 # all of them
  python tools/blender/gifts_on.py hawk shield     # the Hawk's, on a Shield

The Hawk on a Shield: the shield is the breast of an eagle displayed. Wings of plate rise
from behind its rim, feathers of cut steel fanned from straight up to out and down; a
raptor's head of brass and iron stands over the top edge and looks about; two taloned feet
hang open under it. Everything is the shield's own metal; the field is in the eyes and at
the tips of the longest feathers. On its partner's arm the wings are shut down its rim and
the feet drawn up (pieces named aloft and furled: the game shows the one or the other).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genius_geo as g          # noqa: E402
import genius_kit as kit        # noqa: E402
from genius_kit import mat, field   # noqa: E402


def piece(name, items, pivot=(0, 0, 0)):
    """[(geometry, material), ...] as one object, cut planes, turning about `pivot`."""
    ob = g.pieces(name, [it for it in items if it[0]], smooth=False)
    p = Vector(pivot)
    ob.data.transform(Matrix.Translation(-p))
    ob.location = p
    return ob


def at(socket, objects):
    """The pieces that hang on one socket of the body."""
    e = kit.free_socket("at_" + socket, (0, 0, 0))
    for o in objects:
        o.parent = e
    return e


def when(state, objects):
    """Pieces that show only while the genius goes free ("aloft") or only while it is worn or
    held ("furled"): the game shows the one or the other."""
    e = kit.free_socket(state, (0, 0, 0))
    for o in objects:
        o.parent = e
    return e


def _along(pts, t):
    """A point t of the way down a line of points."""
    x = t * (len(pts) - 1)
    i = min(int(x), len(pts) - 2)
    return pts[i].lerp(pts[i + 1], x - i)


# ---- the Hawk on a Shield ----------------------------------------------------------------

def shield_wing(sg):
    """One wing, made at the shield's side rim (the socket is on the rim, six tenths of the
    way up): its arm goes up behind the rim, and the feathers fan from it, the longest
    straight up, the last out and down. sg: 1 the left (+X), -1 the right."""
    iron, steel, brass = mat("metal_iron"), mat("metal_iron_light"), mat("metal_brass")
    arm = [Vector((sg * 0.2, 0.085, 0.33)), Vector((sg * 0.14, 0.06, 0.2)), Vector((sg * 0.055, 0.04, 0.06)), Vector((-sg * 0.03, 0.035, -0.10))]
    front = (0, -1, 0.0)
    flights, coverts, scales, lit = None, None, None, None
    n = 13
    for i in range(n):
        t = i / (n - 1.0)
        th = math.radians(-4 + 140 * t ** 0.85)
        d = Vector((sg * math.sin(th), 0.2 - 0.1 * t, math.cos(th))).normalized()
        b = _along(arm, t) + Vector((0, 0.012 - 0.003 * i, 0))
        L = 0.44 - 0.2 * t ** 0.8
        flights = g.merge(flights, g.blade(b, b + d * L, 0.11 - 0.025 * t, thick=0.012, normal=front, belly=0.6))
        if i < 4:      # the field at the tips of the longest
            tip = b + d * L
            lit = g.merge(lit, g.blade(tip - d * 0.09, tip + d * 0.012, 0.036, thick=0.012, normal=front, belly=0.5))
    for i in range(8):
        t = (i + 0.3) / 8.0
        th = math.radians(6 + 132 * t ** 0.9)
        d = Vector((sg * math.sin(th), 0.12, math.cos(th))).normalized()
        b = _along(arm, t) + Vector((0, -0.006, 0))
        coverts = g.merge(coverts, g.blade(b, b + d * (0.24 - 0.08 * t), 0.1, thick=0.014, normal=front, belly=0.5))
    for i in range(7):
        t = (i + 0.1) / 7.0
        th = math.radians(18 + 118 * t)
        d = Vector((sg * math.sin(th), 0.05, math.cos(th))).normalized()
        b = _along(arm, t) + Vector((0, -0.02, 0))
        scales = g.merge(scales, g.blade(b, b + d * 0.11, 0.08, thick=0.012, normal=front, belly=0.45))
    bone = g.tube([arm[3] + Vector((0, -0.012, 0)), arm[2] + Vector((0, -0.018, 0)), arm[1] + Vector((0, -0.02, 0)), arm[0] + Vector((0, -0.02, 0)), arm[0] + Vector((sg * 0.012, -0.012, 0.05))],
                  [0.024, 0.022, 0.018, 0.014, 0.004], n=5)
    # the knuckle where it comes round the rim: a boss of iron
    knuckle = g.ico((sg * 0.012, -0.004, -0.005), 0.034, sub=1, scale=(0.9, 0.8, 1.2))
    items = [(flights, steel), (coverts, iron), (scales, brass), (bone, brass), (knuckle, iron), (lit, field("wingtips", 2.6))]
    return piece("glide_wing_%s" % ("l" if sg > 0 else "r"), items, pivot=(0, 0.03, -0.04))


def shield_wing_shut(sg):
    """The same wing shut, as it lies when the shield is on an arm: down the rim from the
    knuckle, the long feathers one over the other like the plates of a tasset, a hand's
    breadth proud of the edge."""
    iron, steel, brass = mat("metal_iron"), mat("metal_iron_light"), mat("metal_brass")
    front = (0, -1, 0.0)
    flights, coverts, scales = None, None, None
    for i in range(6):
        t = i / 5.0
        b = Vector((sg * (0.0 + 0.012 * i), 0.03 - 0.004 * i, 0.07 - 0.03 * i))
        tip = Vector((sg * (0.035 + 0.02 * t), 0.05, -0.2 - 0.3 * t))
        flights = g.merge(flights, g.blade(b, tip, 0.085, thick=0.012, normal=front, belly=0.5))
    for i in range(5):
        t = i / 4.0
        b = Vector((sg * (0.005 + 0.012 * i), 0.012, 0.1 - 0.035 * i))
        coverts = g.merge(coverts, g.blade(b, b + Vector((sg * 0.035, 0.012, -0.17)), 0.085, thick=0.014, normal=front, belly=0.45))
    for i in range(4):
        b = Vector((sg * (0.004 + 0.01 * i), -0.002, 0.125 - 0.035 * i))
        scales = g.merge(scales, g.blade(b, b + Vector((sg * 0.03, 0.006, -0.085)), 0.07, thick=0.012, normal=front, belly=0.45))
    bone = g.tube([(-sg * 0.03, 0.02, -0.08), (-sg * 0.012, 0.01, 0.07), (sg * 0.02, 0.006, 0.145), (sg * 0.06, 0.012, 0.11)], [0.022, 0.024, 0.022, 0.006], n=5)
    knuckle = g.ico((sg * 0.012, -0.004, -0.005), 0.034, sub=1, scale=(0.9, 0.8, 1.2))
    return piece("shut_wing_%s" % ("l" if sg > 0 else "r"), [(flights, steel), (coverts, iron), (scales, brass), (bone, brass), (knuckle, iron)])


def shield_head():
    """The head, made at the middle of the shield's top edge: a mantle of hackles over the
    rim, a neck, a raptor's head that looks out over the face, brow down, bill hooked."""
    iron, steel, brass, dark = mat("metal_iron"), mat("metal_iron_light"), mat("metal_brass"), mat("metal_dark")
    hackles = None
    for i in range(9):
        a = math.radians(-100 + 200 * i / 8.0)          # round the front and the sides
        out = Vector((math.sin(a), -math.cos(a) * 0.75, 0))
        b = Vector((0, 0.0, 0.035)) + out * 0.03
        hackles = g.merge(hackles, g.blade(b, b + out * 0.085 + Vector((0, 0, -0.085)), 0.062, thick=0.012, normal=out + Vector((0, 0, 0.6)), belly=0.5))
    collar = piece("mantle", [(hackles, steel), (g.tube([(0, 0.005, -0.03), (0, 0.004, 0.04)], [0.062, 0.05], n=7), iron)])

    neck = g.tube([(0, 0.004, 0.03), (0, -0.004, 0.085), (0, -0.02, 0.12)], [0.046, 0.04, 0.042], n=7)
    skull = g.ico((0, -0.04, 0.135), 0.056, sub=1, scale=(0.92, 1.22, 0.86))
    brow, eyes, sockets = None, None, None
    for sx in (1, -1):
        brow = g.merge(brow, g.blade((sx * 0.006, -0.108, 0.146), (sx * 0.066, -0.02, 0.172), 0.042, thick=0.012, normal=(sx * 0.3, -0.3, 1), belly=0.45))
        sockets = g.merge(sockets, g.ico((sx * 0.04, -0.078, 0.14), 0.02, sub=1, scale=(0.7, 1.0, 0.8)))
        eyes = g.merge(eyes, g.ico((sx * 0.046, -0.084, 0.141), 0.0125, sub=1))
    bill = g.tongue([(0, -0.085, 0.128), (0, -0.135, 0.12), (0, -0.165, 0.094), (0, -0.16, 0.058)], [0.058, 0.046, 0.026, 0.003], thick=0.85, normal=(0, 0, 1))
    jaw = g.tongue([(0, -0.08, 0.108), (0, -0.125, 0.097), (0, -0.146, 0.088)], [0.04, 0.028, 0.004], thick=0.5, normal=(0, 0, 1))
    cere = g.box((0, -0.094, 0.137), (0.05, 0.03, 0.022))
    crest = None
    for sx, back, up, w in ((0, 0.15, 0.1, 0.05), (0.03, 0.12, 0.05, 0.042), (-0.03, 0.12, 0.05, 0.042), (0.05, 0.085, 0.0, 0.036), (-0.05, 0.085, 0.0, 0.036)):
        b = Vector((sx * 0.6, -0.02, 0.172 - abs(sx) * 0.3))
        crest = g.merge(crest, g.blade(b, b + Vector((sx * 0.5, back, up)), w, thick=0.01, normal=(sx, 0.3, 1), belly=0.4))
    head = piece("turn_head", [(neck, iron), (skull, steel), (brow, brass), (sockets, dark), (eyes, field("eyes", 3.4)), (bill, brass), (jaw, dark), (cere, iron), (crest, steel)], pivot=(0, 0, 0.03))
    for ob in (collar, head):         # a head to be seen over a tower shield
        ob.data.transform(Matrix.Scale(1.25, 4))
    head.location = Vector(head.location) * 1.25
    return [collar, head]


def shield_talons_shut():
    """The feet drawn up and clenched under the shield's lower edge, as a bird carries them
    flying: two fists of brass and four black hooks each, close to the plate."""
    brass, claw, steel = mat("metal_brass"), mat("metal_dark"), mat("metal_iron_light")
    toes, claws, cuffs = None, None, None
    for sg in (1, -1):
        foot = Vector((sg * 0.06, -0.02, 0.015))
        cuffs = g.merge(cuffs, g.blade(foot + Vector((0, 0.01, 0.07)), foot + Vector((0, -0.02, -0.01)), 0.07, thick=0.016, normal=(0, -1, 0.2), belly=0.4))
        for dx, dy in ((0.03, -0.035), (0.0, -0.045), (-0.03, -0.035), (0.0, 0.03)):
            end = foot + Vector((dx, dy, -0.022))
            toes = g.merge(toes, g.tube([foot, end], [0.02, 0.016], n=5))
            claws = g.merge(claws, g.tongue([end, end + Vector((dx * 0.2, dy * 0.2, -0.03)), end + Vector((-dx * 0.5, -dy * 0.5, -0.055))], [0.028, 0.022, 0.002], thick=0.8))
    return [piece("shut_talons", [(cuffs, steel), (toes, brass), (claws, claw)])]


def shield_talons():
    """The feet, made at the foot of the shield's back: two legs in trousers of plate come
    from behind its lower edge, and each foot hangs open, three hooked claws forward and one
    back, each as long as its toe."""
    steel, brass, claw = mat("metal_iron_light"), mat("metal_brass"), mat("metal_dark")
    trousers, shanks, toes, claws = None, None, None, None
    for sg in (1, -1):
        hip = Vector((sg * 0.06, -0.005, 0.07))
        ankle = Vector((sg * 0.085, -0.035, -0.045))
        foot = ankle + Vector((0, -0.012, -0.05))
        for k in range(5):
            a = math.radians(-70 + 35 * k)
            out = Vector((sg * math.sin(a) * 0.5 + sg * 0.3, -math.cos(a), 0)).normalized()
            trousers = g.merge(trousers, g.blade(hip + out * 0.015, ankle + out * 0.03 + Vector((0, 0, 0.012)), 0.06, thick=0.014, normal=out, belly=0.4))
        shanks = g.merge(shanks, g.tube([ankle + Vector((0, 0.004, 0.04)), foot], [0.02, 0.022], n=5))
        for dx, dy in ((0.062, -0.07), (0.0, -0.092), (-0.062, -0.07), (0.0, 0.07)):
            knuck = foot + Vector((dx * 0.75, dy * 0.75, -0.012))
            end = foot + Vector((dx, dy, -0.028))
            toes = g.merge(toes, g.tube([foot, knuck, end], [0.02, 0.017, 0.014], n=5))
            claws = g.merge(claws, g.tongue([end, end + Vector((dx * 0.35, dy * 0.35, -0.03)), end + Vector((dx * 0.3, dy * 0.3, -0.085)), end + Vector((-dx * 0.1, -dy * 0.1, -0.11))],
                                            [0.03, 0.026, 0.016, 0.002], thick=0.8))
    return [piece("sway_talons", [(trousers, steel), (shanks, brass), (toes, brass), (claws, claw)], pivot=(0, 0, 0.07))]


def hawk_wings_on_shield():
    return [at("socket_arm_l", [when("aloft", [shield_wing(1)]), when("furled", [shield_wing_shut(1)])]),
            at("socket_arm_r", [when("aloft", [shield_wing(-1)]), when("furled", [shield_wing_shut(-1)])]),
            at("socket_head", shield_head())]


def hawk_talons_on_shield():
    return [at("socket_tail", [when("aloft", shield_talons()), when("furled", shield_talons_shut())])]


# giver, first base -> feature -> its builder
MADE = {("hawk", "shield"): {"wings": hawk_wings_on_shield, "talons": hawk_talons_on_shield}}


def build(giver, first, feature):
    kit.reset()
    roots = MADE[(giver, first)][feature]()
    path = os.path.join(kit.OUT, "gifts", "%s-%s-on-%s.glb" % (giver, feature, first))
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for r in roots:
        r.select_set(True)
        for o in r.children_recursive:
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    kit.log("wrote", os.path.relpath(path, kit.ROOT), "%d KB" % (os.path.getsize(path) // 1024))


if __name__ == "__main__":
    want = sys.argv[1:]
    for (giver, first), feats in MADE.items():
        if want and (giver not in want or (len(want) > 1 and first not in want)):
            continue
        for feature in feats:
            build(giver, first, feature)
