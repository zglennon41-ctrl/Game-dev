"""The small people's lines (lines_people.py): their eyes and mouths, the marks on their skin,
and what they are dressed in. A garment is cut from the body's own skin (pushed out and
painted), so a dressed body is still one skin; what hangs free of the body (a skirt, a
collar, a cloak) is a piece that rides a bone."""
import math

import numpy as np
from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import mat, field
from lines_people import slot, _hoop, _disc

# ======================================================================================
# Eyes and mouths
# ======================================================================================

@slot("eyes", "lit", "big", "dim", "far")
def eyes_lit(P, size, word):
    """Each kind has its own eyes, so a face reads on its own skin: the imp's are alight from
    lid to lid in a dark face, with a slit down them; the sprite's are large and dark in a
    pale one, with a light in each; the homunculus's are dark, with the light sunk in them."""
    style = P._style
    k = size * (1.25 if style == "big" else 1.0)
    if P.kind == "imp":
        P.eyes(field("eyes" if style != "dim" else "eyes_dim", 3.6), mat("void"), k * 1.22, cut="slit")
    elif P.kind == "sprite":
        if style == "far":           # fixed on something a long way off: pale, and the dark of them small
            P.eyes(mat("eye_white"), mat("void"), k * 1.5, cut="dot")
        else:
            P.eyes(mat("eye_dark"), field("eyes", 4.0), k * 1.55, cut="glint")
    else:
        P.eyes(mat("eye_dark"), field("eyes", {"lit": 3.6, "big": 4.0, "dim": 1.6, "far": 4.4}[style]), k)


@slot("eyes", "black")
def eyes_black(P, size, word):
    """Black from lid to lid, catching no light; the skin round them paler (on a pale face,
    smudged dark), so it shows."""
    P.eyes(mat("void"), mat("void"), size * (1.2 if P.kind != "sprite" else 1.6))
    e = P.eye
    near = np.minimum(np.linalg.norm(P.v0 - np.array([e.x, e.y, e.z]), axis=1), np.linalg.norm(P.v0 - np.array([-e.x, e.y, e.z]), axis=1))
    if P.kind == "sprite":
        P.paint(P.headv & (near < P.eye_r * 2.9 * size), mat("smoke"))
    else:
        P.paint(P.headv & (near < P.eye_r * 3.4 * size), mat("paper_old"))
        P.paint(P.headv & (near < P.eye_r * 2.0 * size), mat("void"))


@slot("eyes", "old")
def eyes_old(P, size, word):
    """Old and wet: pale, with the light sunk in them, and bags under."""
    P.eyes(mat("eye_white"), field("eyes_dim", 1.3), size)
    e, r = P.eye, P.eye_r
    bags = None
    for s in (1, -1):
        bags = g.merge(bags, g.ico(Vector((s * e.x, e.y - r * 0.45, e.z - r * 1.45)), r * 0.9, sub=1, scale=(1.35, 0.5, 0.5)))
    P.add("eye_bags", bags, P.skin, "head", smooth=True)


@slot("eyes", "shut")
def eyes_shut(P, size, word):
    e, r = P.eye, P.eye_r
    lids = None
    for s in (1, -1):
        lids = g.merge(lids, g.ico(Vector((s * e.x, e.y - r * 0.5, e.z)), r * 1.05, sub=1, scale=(1.25, 0.6, 0.4)))
    P.add("eye_lids", lids, mat("void"), "head", smooth=True)


def mouth_at(P):
    z = float(P.mouth[2]) - 0.075 * P.hr
    return Vector((0, P.front(z) - 0.002, z))


@slot("mouth", "open", "wide", "pursed", "tongue")
def mouth(P, size, word):
    style, hr = P._style, P.hr
    c = mouth_at(P)
    w, h = {"open": (0.3, 0.26), "wide": (0.74, 0.26), "pursed": (0.13, 0.12), "tongue": (0.3, 0.2)}[style]
    P.add("mouth", g.ico(c + Vector((0, 0.012 * hr, 0)), hr * size, sub=1, scale=(w, 0.2, h)), mat("maw"), "head", smooth=True)
    if style == "wide":          # teeth, in a row
        teeth = None
        n = 7
        for i in range(n):
            t = -1.0 + 2.0 * (i + 0.5) / n
            teeth = g.merge(teeth, g.box(c + Vector((t * hr * 0.56 * size, -0.2 * hr * size * (1.0 - 0.75 * t * t) + 0.02 * hr, 0.05 * hr * size)), (0.13 * hr * size, 0.05 * hr, 0.15 * hr * size)))
        P.add("teeth", teeth, mat("tooth"), "head")
    if style == "tongue":
        P.add("tongue", g.blade(c + Vector((0.04 * hr, -0.1 * hr, 0)), c + Vector((0.14 * hr, -0.34 * hr, -0.22 * hr)), 0.14 * hr, normal=(0, -0.4, 1)), mat("tongue"), "head", smooth=True)


# ======================================================================================
# The skin: marks on the body itself
# ======================================================================================

def noise(v, f=7.0):
    return (np.sin(v[:, 0] * f * 1.3 + np.sin(v[:, 2] * f) * 1.7) + np.sin(v[:, 1] * f * 1.7 + np.sin(v[:, 0] * f * 0.8) * 1.3) + np.sin(v[:, 2] * f * 1.1 + np.sin(v[:, 1] * f * 1.2) * 1.9)) / 3.0


def arm_row(P, x):
    """The arm's section at a distance out: (x, half-depth, half-height)."""
    return P.hb._row(P.hb.rings("arm", "fit"), x)


@slot("skin", "script")
def skin_script(P, size, word):
    """The lines of its ledger, ruled in light round the chest and down each arm."""
    lit = field("script", 2.2)
    n_trunk = max(1, int(round(3 * size)))
    z0, z1 = P.hipz + 0.26 * P.t, P.neckz - 0.14 * P.t
    for i in range(n_trunk):
        z = z0 + (z1 - z0) * (i + 0.5) / n_trunk
        hw, hd, yo = P.ring(z)
        P.add("script_t%d" % i, _hoop((0, yo, z), hw + 0.014, hd + 0.014, 0.013, u=X, v=Y, n=12, sides=3), lit, "chest" if z > P.J["chest"].z else "spine")
    n_arm = max(1, int(round(2 * size)))
    for s, tag in ((1, "l"), (-1, "r")):
        for i in range(n_arm):
            x = P.ex + (P.wx - P.ex) * (0.25 + 0.5 * i / max(1, n_arm - 1)) if n_arm > 1 else (P.ex + P.wx) / 2
            row = arm_row(P, x)
            P.add("script_a%s%d" % (tag, i), _hoop((s * x, P.army, P.armz), row[1] + 0.013, row[2] + 0.013, 0.012, u=Y, v=Z, n=8, sides=3), lit, "lowerarm." + tag)


@slot("skin", "cracks")
def skin_cracks(P, size, word):
    """It burns under the skin, and shows through where the skin has split."""
    nz = noise(P.v0, 9.0)
    P.paint((np.abs(nz) < 0.07 * size) & ~P.headv & (P.v0[:, 2] > P.footz + 0.2), field("ember", 2.6))


@slot("skin", "crackle")
def skin_crackle(P, size, word):
    """A glaze crazed like old porcelain."""
    nz = noise(P.v0, 11.0)
    P.paint(np.abs(nz) < 0.06 * size, mat("glaze") if word != "light" else field("seam", 1.2))


@slot("skin", "rough")
def skin_rough(P, size, word):
    """Not finished: the clay is as the hands left it."""
    k = 0.035 * size * np.where(P.headv, 0.4, 1.0)
    P.v += P.n * (noise(P.v0, 13.0) * k)[:, None]


@slot("skin", "clay-legs")
def skin_clay_legs(P, size, word):
    """Clay to the knees: the legs have not been brought out of the lump yet."""
    m = P.below(P.kneez + 0.14 * size * P.t)
    P.wear(m, mat("clay_wet"), 0.1 * size * P.t)
    P.v[m] += P.n[m] * (noise(P.v0[m], 15.0) * 0.035)[:, None]


@slot("skin", "ink-arms", "iron-arms", "stone-arms", "glow-hands", "wax-nails", "glow-fingers", "terms-palms", "white-gloves")
def skin_arms(P, size, word):
    style = P._style
    ax = np.abs(P.v0[:, 0])
    hx = P.J["hand.l"].x
    if style == "ink-arms":           # ink to its elbows
        P.paint(P.arm & (ax > P.ex - 0.04), mat("void"))
    elif style == "iron-arms":        # gone to dull iron from the wrists up
        P.wear(P.arm & (ax < P.wx - 0.02), mat("metal_iron"), 0.02)
        P.wear(P.trunk(P.chestz - 0.1 * P.t, P.neckz + 0.02) & (ax > P.sx - 0.16), mat("metal_iron"), 0.02)
        for s, tag in ((1, "l"), (-1, "r")):
            row = arm_row(P, P.wx - 0.04)
            P.add("manacle_" + tag, _hoop((s * (P.wx - 0.04), P.army, P.armz), row[1] + 0.045, row[2] + 0.045, 0.036, u=Y, v=Z, n=8, sides=4), mat("metal_iron_light"), "lowerarm." + tag)
            riv = None
            for k in range(3):
                x = P.sx + (P.ex - P.sx) * (0.25 + 0.3 * k)
                riv = g.merge(riv, g.ico((s * x, P.army, P.armz + arm_row(P, x)[2] + 0.03), 0.028, sub=0))
            P.add("rivets_" + tag, riv, mat("metal_iron_light"), "upperarm." + tag, smooth=True)
    elif style == "stone-arms":       # its forearms faced with flat stone
        P.wear(P.arm & (ax > P.ex) & (ax < P.wx - 0.02), mat("stone_face"), 0.05 * size)
        for s, tag in ((1, "l"), (-1, "r")):
            x = (P.ex + P.wx) / 2
            row = arm_row(P, x)
            P.add("stone_" + tag, g.box((s * x, P.army, P.armz + row[2] + 0.06), ((P.wx - P.ex) * 0.86, row[1] * 2.8, 0.07)), mat("stone_face"), "lowerarm." + tag)
    elif style in ("glow-hands", "terms-palms"):   # its palms hold a light (they face down, with the arms out)
        P.paint(P.hand & (P.n[:, 2] < -0.2), field("palms", 2.4 * size))
    elif style == "glow-fingers":
        P.paint(P.hand & (ax > hx + (P.wx - P.ex) * 0.2), field("palms", 2.6 * size))
    elif style == "wax-nails":
        P.paint(P.hand & (ax > hx + (P.wx - P.ex) * 0.26), mat("seal_wax"))
    elif style == "white-gloves":
        P.wear(P.hand | (P.arm & (ax > P.wx - 0.1)), mat("paper"), 0.012)


@slot("skin", "ink-hands", "fired-hands", "stone-knuckles", "thread-fingers", "wrist-gears", "flat-arms", "webbed-feet", "clawed-feet")
def skin_hands(P, size, word):
    style = P._style
    ax = np.abs(P.v0[:, 0])
    hx, hk = P.J["hand.l"].x, P.b.get("hands", 1.0)
    if style == "ink-hands":          # ink to the wrists
        P.paint(P.hand | (P.arm & (ax > P.wx - 0.06)), mat("void"))
    elif style == "fired-hands":      # its hands are better finished than the rest of it
        P.paint(P.hand | (P.arm & (ax > P.wx - 0.05)), mat("fired"))
    elif style == "stone-knuckles":   # knuckles like river stones
        P.paint(P.hand, mat("stone_face"))
    elif style == "thread-fingers":   # its fingers tabbed with coloured thread
        for s, tag in ((1, "l"), (-1, "r")):
            for i, m in enumerate(("thread_red", "thread_blue", "thread_gold")):
                p = Vector((s * (hx + 0.1 * hk), P.army + (i - 1) * 0.05 * hk, P.armz - 0.01))
                P.add("thread_%s%d" % (tag, i), g.merge(_hoop(p, 0.035 * hk, 0.035 * hk, 0.012, u=Y, v=Z, n=6, sides=3), g.tube([p, p + Vector((s * (0.26 + 0.07 * i) * size, 0.012 * (i - 1), -0.01))], 0.009, n=3)), mat(m), "hand." + tag)
    elif style == "wrist-gears":      # small gears turn at its wrists
        for s, tag in ((1, "l"), (-1, "r")):
            row = arm_row(P, P.wx - 0.03)
            P.add("wrist_gear_" + tag, cog((s * (P.wx - 0.03), P.army - row[1] - 0.025, P.armz), 0.09 * size, Y), mat("metal_brass"), "lowerarm." + tag)
            P.add("wrist_gear2_" + tag, cog((s * (P.wx - 0.03), P.army, P.armz + row[2] + 0.025), 0.07 * size, Z), mat("metal_brass"), "lowerarm." + tag)
    elif style == "flat-arms":        # arms made long and flat, for carrying
        for s, tag in ((1, "l"), (-1, "r")):
            x0, x1 = P.ex - 0.02, hx + 0.16 * hk
            P.add("flat_arm_" + tag, g.box((s * (x0 + x1) / 2, P.army, P.armz), (x1 - x0, 0.34 * size * P.t, 0.09)), P.skin, "lowerarm." + tag, smooth=False)
            P.add("flat_arm_band_" + tag, g.box((s * (x0 + 0.06), P.army, P.armz), (0.07, 0.36 * size * P.t, 0.11)), P.material("trim"), "lowerarm." + tag, smooth=False)
    elif style == "clawed-feet":      # heavy clawed feet, for its size
        # where the foot itself is: the low part of the leg, on the character's left
        foot = P.below(P.footz + 0.02) & (P.v0[:, 0] > 0)
        fx0, fx1 = float(P.v0[foot, 0].min()), float(P.v0[foot, 0].max())
        toe_y = float(P.v0[foot, 1].min())
        w = fx1 - fx0
        for s, tag in ((1, "l"), (-1, "r")):
            claws = None
            for i in range(3):
                x = fx0 + w * (0.2 + 0.3 * i)
                b0 = Vector((s * x, toe_y + 0.05, 0.05))
                claws = g.merge(claws, g.cone(b0, b0 + Vector((s * (i - 1) * 0.03, -0.75 * w * size, -0.035)), 0.2 * w, n=5))
            P.add("claws_" + tag, claws, mat("bone"), "foot." + tag)
    else:                             # webbed feet
        for s, tag in ((1, "l"), (-1, "r")):
            f = P.J["foot.l"]
            P.add("web_" + tag, g.blade((s * f.x, f.y + 0.02, 0.035), (s * f.x * 1.2, f.y - 0.5 * size * P.t - 0.1, 0.02), 0.42 * size * P.t + 0.1, normal=Z, belly=0.72, thick=0.02), P.skin, "foot." + tag, smooth=True)


@slot("wear", "harness")
def wear_harness(P, size, word):
    """Straps over both shoulders and a band across the chest: what a load is hung from."""
    m = P.material(word, "trim")
    hw, hd, yo = P.ring(P.chestz - 0.12 * P.t)
    P.add("harness_band", _hoop((0, yo, P.chestz - 0.12 * P.t), hw + 0.03, hd + 0.03, 0.03 * size, u=X, v=Y, n=12, sides=4), m, "chest", smooth=True)
    for s in (1, -1):
        x = s * P.sx * 0.62
        pts = [(x, P.rear(P.chestz - 0.12 * P.t, x) + 0.03, P.chestz - 0.12 * P.t), (x, P.rear(P.armz - 0.02, x) + 0.035, P.armz - 0.02), (x, P.J["chest"].y, P.armz + 0.14 * P.t),
               (x, P.front(P.armz - 0.02, x) - 0.035, P.armz - 0.02), (x, P.front(P.chestz - 0.12 * P.t, x) - 0.03, P.chestz - 0.12 * P.t)]
        P.add("harness_strap_%d" % s, g.tube(pts, [0.03 * size] * 5, n=4, flat=0.45), m, "chest", smooth=True)
    P.add("harness_ring", _hoop((0, P.front(P.chestz - 0.12 * P.t) - 0.05, P.chestz - 0.12 * P.t), 0.05, 0.05, 0.014, u=X, v=Z, n=8, sides=3), mat("metal_iron_light"), "chest")


@slot("skin", "white-knees", "ink-feet", "wet-legs", "scratched-legs")
def skin_legs(P, size, word):
    style = P._style
    z = P.v0[:, 2]
    if style == "white-knees":
        P.paint(P.below(P.kneez + 0.1 * P.t) & (z > P.kneez - 0.1 * P.t) & (P.v0[:, 1] < 0.0), mat("chalk"))
    elif style == "ink-feet":
        P.paint(P.below(P.footz + 0.16 * size), mat("void"))
    elif style == "wet-legs":
        P.paint(P.below(P.kneez * size), mat("glaze"))
    elif style == "scratched-legs":
        P.paint(P.below(P.hipz) & (np.abs(noise(P.v0, 23.0)) < 0.1), mat("chalk"))


@slot("skin", "patch")
def skin_patch(P, size, word):
    """Fresh grey clay over the chest, where the last patch went in."""
    wet = mat("clay_wet") if word != "pale" else mat("chalk")
    m = P.trunk(P.chestz - 0.3 * size * P.t, P.chestz + 0.2 * size * P.t, front=True) & (np.abs(P.v0[:, 0]) < 0.2 * size)
    P.wear(m, wet, 0.04)
    if size > 1.0:               # and the patches before that one: a shoulder, a thigh, the side of its head
        ax = np.abs(P.v0[:, 0])
        P.wear(P.arm & (P.v0[:, 0] > 0) & (ax > P.sx - 0.02) & (ax < P.sx + (P.ex - P.sx) * 0.7), wet, 0.035)
        P.wear(P.below(P.hipz - 0.02) & (P.v0[:, 0] < 0) & (P.v0[:, 2] > P.kneez + 0.04) & (P.v0[:, 1] < P.J["upperleg.l"].y + 0.02), wet, 0.035)
        P.wear(P.headv & ~P.ears & (P.v0[:, 0] > 0.35 * P.hr) & (P.v0[:, 2] > P.eye.z + 0.5 * P.hr), wet, 0.03)
    # the edge of the patch, where it was thumbed in
    hw = min(0.2 * size, P.ring(P.chestz)[0] * 0.9)
    z0, z1 = P.chestz - 0.3 * size * P.t, P.chestz + 0.2 * size * P.t
    rim = [(x, P.front(z, x) - 0.035, z) for x, z in ((-hw, z0), (hw, z0), (hw, z1), (-hw, z1), (-hw, z0))]
    P.add("patch_rim", g.tube(rim, [0.016] * len(rim), n=3, caps=False), mat("stone_face") if word != "pale" else mat("slate"), "chest")


@slot("skin", "mends")
def skin_mends(P, size, word):
    """More rivet and patch than clay: each mend left where it shows."""
    t = P.t
    plates = [("chest", (0.09, P.front(P.chestz, 0.09) - 0.02, P.chestz), (0.2 * t, 0.05, 0.24 * t), "tin"),
              ("chest", (-0.12, P.front(P.chestz - 0.2 * t, -0.12) - 0.02, P.chestz - 0.22 * t), (0.18 * t, 0.05, 0.16 * t), "metal_brass"),
              ("hips", (0.14, P.front(P.hipz, 0.14) - 0.02, P.hipz + 0.02), (0.18 * t, 0.05, 0.2 * t), "metal_iron_light"),
              ("head", (-0.5 * P.hr, P.hy0 + 0.02, P.crown - 0.3 * P.hh), (0.6 * P.hr, 0.05, 0.36 * P.hr), "tin")]
    riv = {}
    for i, (bone, c, sz, m) in enumerate(plates):
        P.add("mend_%d" % i, g.box(c, sz, rot=(0, 0.2 * (i % 2) - 0.1, 0)), mat(m), bone)
        for dx in (-0.36, 0.36):
            for dz in (-0.36, 0.36):
                riv[bone] = g.merge(riv.get(bone), g.ico((c[0] + dx * sz[0], c[1] - sz[1] * 0.5, c[2] + dz * sz[2]), 0.02, sub=0))
    for bone, geo in riv.items():
        P.add("mend_rivets_" + bone, geo, mat("metal_dark"), bone, smooth=True)
    for s, tag in ((1, "l"), (-1, "r")):
        x = P.sx + (P.ex - P.sx) * 0.5
        row = arm_row(P, x)
        P.add("mend_band_" + tag, _hoop((s * x, P.army, P.armz), row[1] + 0.03, row[2] + 0.03, 0.03, u=Y, v=Z, n=8, sides=4), mat("tin" if s > 0 else "metal_brass"), "upperarm." + tag)


@slot("skin", "scorch-marks")
def skin_scorch(P, size, word):
    """Scorch marks in the shape of wounds, each with a small number beside it."""
    lit, paper = field("scorch", 2.4), mat("paper")
    spots = [("chest", 0.1, P.chestz + 0.02, 0.5), ("chest", -0.08, P.chestz - 0.22 * P.t, -0.6), ("spine", 0.05, P.hipz + 0.3 * P.t, 0.3)]
    for i, (bone, x, z, tilt) in enumerate(spots):
        c = Vector((x, P.front(z, x) - 0.012, z))
        d = Vector((math.cos(tilt), 0, math.sin(tilt))) * 0.13 * size
        P.add("scorch_%d" % i, g.blade(c - d, c + d, 0.07 * size, normal=Y, belly=0.5, thick=0.012), lit, bone)
        P.add("scorch_no_%d" % i, g.box(c + Vector((0.13 * (1 if x < 0 else -1), -0.004, 0.08)), (0.07, 0.012, 0.08), rot=(0, 0.2, 0)), paper, bone)
    for s, tag in ((1, "l"), (-1, "r")):
        x = P.sx + (P.ex - P.sx) * 0.55
        c = Vector((s * x, P.army - arm_row(P, x)[1] - 0.012, P.armz))
        P.add("scorch_arm_" + tag, g.blade(c - Vector((0.1, 0, 0.02)), c + Vector((0.1, 0, 0.02)), 0.06, normal=Y, belly=0.5, thick=0.012), lit, "upperarm." + tag)


@slot("skin", "tear-tracks")
def skin_tears(P, size, word):
    e, r = P.eye, P.eye_r
    geo = None
    for s in (1, -1):
        b0 = Vector((s * e.x, e.y - r * 0.7, e.z - r * 1.1))
        geo = g.merge(geo, g.blade(b0, b0 + Vector((s * 0.01, 0.01, -0.55 * P.hr * size)), 0.08 * P.hr, normal=Y, belly=0.3, thick=0.006))
    P.add("tear_tracks", geo, field("eyes_dim", 1.0), "head")


def cog(c, r, axis, teeth=8, thick=0.035):
    """A small toothed wheel about an axis."""
    axis = V(axis).normalized()
    u = axis.cross(Z if abs(axis.dot(Z)) < 0.9 else X).normalized()
    w = axis.cross(u)
    c = V(c)
    # one toothed outline, front and back (a third of the faces of a wheel with a box for each tooth)
    rings = []
    for side in (-0.5, 0.5):
        ring = []
        for k in range(teeth * 2):
            a = math.pi * k / teeth
            rr = r * (1.08 if k % 2 == 0 else 0.7)
            ring.append(c + axis * thick * side + (u * math.cos(a) + w * math.sin(a)) * rr)
        rings.append(ring)
    return g.loft(rings)


@slot("skin", "cogs")
def skin_cogs(P, size, word):
    """Small cogs turn in its joints."""
    brass = mat("metal_brass")
    J = P.J
    for s, tag in ((1, "l"), (-1, "r")):
        P.add("cog_elbow_" + tag, cog((s * P.ex, P.army - arm_row(P, P.ex)[1] - 0.02, P.armz), 0.085 * size, Y), brass, "lowerarm." + tag)
        P.add("cog_knee_" + tag, cog((s * (J["lowerleg.l"].x + 0.1 * P.b.get("limbs", 1.0)), J["lowerleg.l"].y, P.kneez), 0.09 * size, X), brass, "lowerleg." + tag)
        P.add("cog_shoulder_" + tag, cog((s * (P.sx + 0.02), P.army - 0.02, P.armz + 0.12), 0.1 * size, (s * 0.3, -0.5, 0.8)), brass, "upperarm." + tag)


# ======================================================================================
# What it is dressed in
# ======================================================================================

def wall(c, r0, r1, z0, z1, thick=0.02, n=12):
    """A thin-walled band about a vertical axis through c: radii (x, y) r0 at z0, r1 at z1."""
    c = V(c)

    def ring(r, z):
        return [Vector((c.x + r[0] * math.cos(2 * math.pi * k / n), c.y + r[1] * math.sin(2 * math.pi * k / n), z)) for k in range(n)]
    rings = [ring(r0, z0), ring(r1, z1), ring((r1[0] - thick, r1[1] - thick), z1), ring((r0[0] - thick, r0[1] - thick), z0)]
    rings.append(rings[0])
    return g.loft(rings, caps=False)


def drape(c, radii, zs, a0, a1, thick=0.03, n=10, hem=None, trail=0.0):
    """A cloth hanging round part of a body. radii(t) gives (rx, ry) at t from 0 (its top) to 1
    (its hem); it reaches from angle a0 to a1, measured from the back (+Y) toward the left;
    hem(a) drops its edge; trail carries the hem back along the ground."""
    c = V(c)
    rings = []
    m = len(zs)
    for i, z in enumerate(zs):
        t = i / max(1, m - 1)
        rx, ry = radii(t)
        angles = [a0 + (a1 - a0) * k / (n - 1) for k in range(n)]
        dz = [(hem(a) * t if hem else 0.0) for a in angles]
        back = trail * t * t
        outer = [Vector((c.x + rx * math.sin(a), c.y + ry * math.cos(a) + back * max(0.0, math.cos(a)), z + d)) for a, d in zip(angles, dz)]
        inner = [Vector((c.x + (rx - thick) * math.sin(a), c.y + (ry - thick) * math.cos(a) + back * max(0.0, math.cos(a)), z + d)) for a, d in zip(reversed(angles), reversed(dz))]
        rings.append(outer + inner)
    return g.loft(rings, caps=True)


def skirt(P, name, z_top, z_bot, flare, material, n=12, scallop=0.0, steps=4, bone="hips"):
    """A skirt, a coat's tails, a robe below the waist: a cone from the body's own section."""
    hw, hd, yo = P.ring(z_top)
    rings = []
    for i in range(steps + 1):
        t = i / steps
        z = z_top + (z_bot - z_top) * t
        k = t ** 0.85
        rx, ry = hw + 0.035 + flare * k, hd + 0.035 + flare * k
        rings.append([Vector((rx * math.cos(2 * math.pi * j / n), yo + ry * math.sin(2 * math.pi * j / n), z + scallop * t * math.sin(6 * math.pi * j / n))) for j in range(n)])
    P.add(name, g.loft(rings, caps=True), material, bone, smooth=True)


@slot("wear", "rag")
def wear_rag(P, size, word):
    m = P.material(word, "trim")
    P.wear(P.trunk(P.hipz - 0.24 * size * P.t, P.hipz + 0.14 * P.t), m, 0.03)
    hw, hd, yo = P.ring(P.hipz)
    P.add("rag_flap", g.blade((0, yo - hd - 0.035, P.hipz + 0.1 * P.t), (0.02, yo - hd - 0.07, P.hipz - 0.4 * size * P.t), 1.5 * hw, normal=Y, belly=0.3), m, "hips", smooth=True)


@slot("wear", "kilt")
def wear_kilt(P, size, word):
    m = P.material(word, "trim")
    P.wear(P.trunk(P.hipz - 0.06, P.hipz + 0.18 * P.t), m, 0.035)
    skirt(P, "kilt", P.hipz + 0.12 * P.t, max(P.footz + 0.1, P.hipz - 0.5 * size * P.t), 0.1 * P.t, m)


@slot("wear", "shift")
def wear_shift(P, size, word):
    """The sprite's own dress: a shift, and a hem of petals each its own length."""
    under, main = P.material(word, "under"), P.material("main")
    P.wear(P.trunk(P.hipz - 0.16 * P.t, P.neckz - 0.02), under, 0.03)
    hw, hd, yo = P.ring(P.hipz)
    petals = None
    for i in range(9):
        a = 2 * math.pi * (i + 0.5) / 9
        d = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((d.x * (hw + 0.02), yo + d.y * (hd + 0.02), P.hipz - 0.08 * P.t))
        petals = g.merge(petals, g.blade(base, base + d * (0.12 + 0.03 * (i % 2)) * size * P.t + Vector((0, 0, -(0.32 + 0.07 * (i % 3)) * size * P.t)), 0.9 * hw, normal=d, belly=0.45))
    P.add("hem_petals", petals, main, "hips", smooth=True)


@slot("wear", "tunic")
def wear_tunic(P, size, word):
    m = P.material(word, "under")
    P.wear(P.trunk(P.hipz - 0.1 * P.t, P.neckz) | P.sleeves(0.0, P.ex - 0.04), m, 0.03)
    skirt(P, "tunic_skirt", P.hipz + 0.1 * P.t, P.hipz - 0.3 * size * P.t, 0.07 * P.t, m)


@slot("wear", "shirt", "shirt-rolled")
def wear_shirt(P, size, word):
    m = P.material(word, "under")
    to = P.wx - 0.06 if P._style == "shirt" else P.ex + 0.03
    P.wear(P.trunk(P.hipz, P.neckz) | P.sleeves(0.0, to), m, 0.025)
    if P._style == "shirt-rolled":       # the sleeves rolled to the elbow
        for s, tag in ((1, "l"), (-1, "r")):
            row = arm_row(P, P.ex + 0.03)
            P.add("roll_" + tag, _hoop((s * (P.ex + 0.03), P.army, P.armz), row[1] + 0.035, row[2] + 0.035, 0.035, u=Y, v=Z, n=8, sides=4), m, "lowerarm." + tag, smooth=True)


def buttons(P, n, z0, z1, material="metal_brass", x=0.0):
    geo = None
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        geo = g.merge(geo, g.ico((x, P.front(z, x) - 0.045, z), 0.022 * P.t, sub=0, scale=(1, 0.5, 1)))
    P.add("buttons", geo, mat(material), "chest", smooth=True)


@slot("wear", "waistcoat")
def wear_waistcoat(P, size, word):
    P.wear(P.trunk(P.hipz + 0.04 * P.t, P.neckz - 0.1 * P.t), P.material(word, "trim"), 0.035)
    buttons(P, 3, P.hipz + 0.12 * P.t, P.chestz + 0.05 * P.t)


@slot("wear", "coat")
def wear_coat(P, size, word):
    """A coat with tails: size is how far they fall (1 to the thigh, 2 to the knee, 3 to the shin)."""
    m = P.material(word, "trim")
    P.wear(P.trunk(P.hipz - 0.02, P.neckz + 0.02) | P.sleeves(0.0, P.wx - 0.06), m, 0.04)
    skirt(P, "coat_tails", P.hipz + 0.12 * P.t, max(P.footz + 0.12, P.hipz - 0.34 * size * P.t), 0.05 * P.t + 0.03 * size, m)
    buttons(P, 3, P.hipz + 0.16 * P.t, P.chestz + 0.08 * P.t)
    for s, tag in ((1, "l"), (-1, "r")):      # turned-back cuffs
        row = arm_row(P, P.wx - 0.07)
        P.add("cuff_" + tag, _hoop((s * (P.wx - 0.07), P.army, P.armz), row[1] + 0.05, row[2] + 0.05, 0.03, u=Y, v=Z, n=8, sides=4), m, "lowerarm." + tag, smooth=True)


@slot("wear", "robe")
def wear_robe(P, size, word):
    """A robe to the feet, with wide sleeves."""
    m = P.material(word, "main")
    P.wear(P.trunk(P.hipz - 0.05, P.neckz + 0.02) | P.sleeves(0.0, P.wx - 0.05), m, 0.045)
    skirt(P, "robe_skirt", P.hipz + 0.14 * P.t, P.footz + 0.1 + (1.0 - min(1.0, size)) * (P.kneez - P.footz), 0.1 * P.t, m, scallop=0.012)
    for s, tag in ((1, "l"), (-1, "r")):      # sleeves that open like bells
        row = arm_row(P, P.wx - 0.06)
        x0, x1 = s * (P.ex + 0.04), s * (P.wx - 0.02)
        rings = [g.ring((x0, P.army, P.armz), row[1] + 0.05, row[2] + 0.05, n=8, u=Y, v=Z), g.ring((x1, P.army, P.armz - 0.05), row[1] + 0.1, row[2] + 0.13, n=8, u=Y, v=Z)]
        P.add("bell_" + tag, g.loft(rings, caps=True), m, "lowerarm." + tag, smooth=True)


@slot("wear", "apron")
def wear_apron(P, size, word):
    """A bib and a skirt in front, a strap round the neck."""
    m = P.material(word, "trim")
    yc = P.J["chest"].y
    front = (P.v0[:, 1] < yc - 0.01) & ~P.arm & ~P.headv
    P.wear(front & (P.v0[:, 2] > P.hipz - 0.02) & (P.v0[:, 2] < P.chestz + 0.1 * P.t) & (np.abs(P.v0[:, 0]) < P.ring(P.chestz)[0] * 0.8), m, 0.035)
    hw, hd, yo = P.ring(P.hipz + 0.1 * P.t)
    zb = max(P.footz + 0.16, P.hipz - 0.5 * size * P.t)
    P.add("apron_skirt", drape((0, yo, 0), lambda t: (hw + 0.04 + 0.03 * t, hd + 0.045 + 0.04 * t), [P.hipz + 0.14 * P.t, (P.hipz + zb) / 2, zb], math.pi - 1.25, math.pi + 1.25, thick=0.025, n=7), m, "hips", smooth=True)
    P.add("apron_tie", _hoop((0, yo, P.hipz + 0.13 * P.t), hw + 0.045, hd + 0.045, 0.02, u=X, v=Y, n=12, sides=3), m, "hips", smooth=True)


@slot("wear", "breeches", "hose", "boots")
def wear_legs(P, size, word):
    z = P.v0[:, 2]
    if P._style == "breeches":
        P.wear(~P.arm & ~P.headv & (z > P.kneez - 0.04) & (z < P.hipz + 0.12 * P.t), P.material(word, "under"), 0.03)
    elif P._style == "hose":
        P.wear(P.below(P.hipz + 0.05) & (z > P.footz + 0.12), P.material(word, "under"), 0.012)
    else:
        top = P.footz + (P.kneez - P.footz) * 0.62 * size
        P.wear(P.below(top), P.material(word, "under"), 0.03)
        for s, tag in ((1, "l"), (-1, "r")):
            lx = P.J["lowerleg.l"].x * s
            rr = 0.1 * P.b.get("limbs", 1.0)
            P.add("boot_top_" + tag, _hoop((lx, P.J["lowerleg.l"].y, top), rr + 0.03, rr + 0.03, 0.028, u=X, v=Y, n=8, sides=4), P.material(word, "under"), "lowerleg." + tag, smooth=True)


@slot("wear", "gloves", "cuffs", "sleeve-guards", "bracers")
def wear_arms(P, size, word):
    ax = np.abs(P.v0[:, 0])
    style = P._style
    if style == "gloves":
        P.wear(P.hand | (P.arm & (ax > P.wx - 0.12 * size)), P.material(word, "under"), 0.02)
    elif style == "cuffs":
        P.wear(P.sleeves(P.wx - 0.17, P.wx - 0.02), P.material(word, "paper"), 0.05)
    elif style == "sleeve-guards":
        P.wear(P.sleeves(P.ex - 0.02, P.wx - 0.03), P.material(word, "paper"), 0.035)
    else:
        P.wear(P.sleeves(P.ex + 0.06, P.wx - 0.03), P.material(word, "under"), 0.045 * size)


@slot("wear", "belt", "sash")
def wear_belt(P, size, word):
    hw, hd, yo = P.ring(P.hipz + 0.15 * P.t)
    if P._style == "belt":
        m = P.material(word, "under")
        P.wear(P.trunk(P.hipz + 0.1 * P.t, P.hipz + 0.2 * P.t), m, 0.05)
        P.add("buckle", g.box((0, yo - hd - 0.06, P.hipz + 0.15 * P.t), (0.1 * P.t, 0.03, 0.1 * P.t)), mat("metal_brass"), "hips")
    else:
        m = P.material(word, "trim")
        P.wear(P.trunk(P.hipz + 0.1 * P.t, P.hipz + 0.26 * P.t), m, 0.055)
        P.add("sash_end", g.blade((hw * 0.7, yo - hd * 0.6 - 0.05, P.hipz + 0.16 * P.t), (hw * 0.9, yo - hd * 0.6 - 0.08, P.hipz - 0.3 * size * P.t), 0.12 * P.t, normal=(0.4, -1, 0), belly=0.6), m, "hips", smooth=True)


def neck_c(P):
    return Vector((0, P.J["head"].y + 0.02, P.neckz))


@slot("wear", "collar", "scarf", "muffler", "collar-fur")
def wear_neck(P, size, word):
    style = P._style
    c = neck_c(P)
    r = 0.105 * P.t + 0.03
    if style == "collar":         # a standing collar, stiff
        P.add("collar", wall((c.x, c.y, 0), (r, r), (r + 0.05 * size, r + 0.05 * size), P.neckz - 0.06 * P.t, P.neckz + 0.12 * size * P.t, thick=0.015, n=10), P.material(word, "paper"), "chest")
    elif style == "scarf":
        m = P.material(word, "trim")
        P.add("scarf", _hoop((c.x, c.y, P.neckz - 0.01), r + 0.03, r + 0.03, 0.055 * size * P.t, u=X, v=Y, n=10, sides=5), m, "chest", smooth=True)
        P.add("scarf_end", g.blade((0.08, c.y - r - 0.05, P.neckz - 0.02), (0.14, c.y - r - 0.09, P.neckz - 0.5 * size * P.t), 0.13 * P.t, normal=(0.2, -1, 0), belly=0.7), m, "chest", smooth=True)
    elif style == "muffler":      # a collar it rides in: a coat's collar, turned up, with only its head out
        m = P.material(word, "trim")
        sw = P.sx + 0.1
        zt = P.chin - 0.05 * P.hh + 0.12 * P.hh * (size - 1.0)
        P.add("muffler", wall((0, c.y, 0), (sw, sw * 0.86), (P.hr * 1.5, P.hr * 1.62), P.hipz + 0.1 * P.t, zt, thick=0.06, n=12), m, "chest", smooth=True)
        P.add("muffler_roll", _hoop((0, c.y, zt), P.hr * 1.52, P.hr * 1.64, 0.075, u=X, v=Y, n=12, sides=5), m, "chest", smooth=True)
        # the wings of the collar, standing behind its ears
        for s in (1, -1):
            P.add("muffler_wing_%d" % s, g.blade((s * P.hr * 1.2, c.y + P.hr * 0.9, zt - 0.05), (s * P.hr * 1.7, c.y + P.hr * 1.3, zt + 0.5 * P.hh * size), 1.5 * P.hr, normal=(s * 0.5, 1, 0), belly=0.4, thick=0.04), m, "chest", smooth=True)
        P.add("muffler_button", g.ico((0, c.y - P.hr * 1.66, zt - 0.14 * P.t), 0.05 * P.t, sub=1, scale=(1, 0.5, 1)), mat("metal_brass"), "chest", smooth=True)
    else:                         # a collar of fur, over the shoulders
        P.add("collar_fur", _hoop((0, c.y + 0.02, P.neckz - 0.05 * P.t), P.sx * 0.9, P.sx * 0.72, 0.09 * size * P.t, u=X, v=Y, n=12, sides=5), P.material(word, "fur_pale"), "chest", smooth=True)


@slot("wear", "stole", "tabard")
def wear_front(P, size, word):
    m = P.material(word, "trim")
    if P._style == "stole":       # two bands from the shoulders down the front
        geo = None
        for s in (1, -1):
            x = s * 0.5 * P.sx
            pts = [(x, neck_c(P).y + 0.06, P.neckz + 0.0), (x * 1.05, P.front(P.chestz, x) - 0.035, P.chestz), (x * 1.1, P.front(P.hipz + 0.2 * P.t, x) - 0.04, P.hipz + 0.2 * P.t), (x * 1.15, P.front(P.hipz, x) - 0.06, P.hipz - 0.36 * size * P.t)]
            geo = g.merge(geo, g.tongue(pts, [0.1 * P.t] * 3 + [0.11 * P.t], thick=0.25, normal=Y))
        P.add("stole", geo, m, "chest", smooth=True)
    else:                         # a panel before and behind, over the head
        P.wear(P.trunk(P.hipz + 0.05, P.neckz - 0.02) & (np.abs(P.v0[:, 0]) < P.ring(P.chestz)[0] * 0.72), m, 0.035)
        hw, hd, yo = P.ring(P.hipz + 0.08 * P.t)
        zb = P.hipz - 0.4 * size * P.t
        for tag, a in (("front", math.pi), ("back", 0.0)):
            P.add("tabard_" + tag, drape((0, yo, 0), lambda t: (hw + 0.04, hd + 0.045 + 0.02 * t), [P.hipz + 0.1 * P.t, zb], a - 0.75, a + 0.75, thick=0.025, n=5), m, "hips", smooth=True)


@slot("wear", "mantle", "cloak", "shadow-cloak")
def wear_cloak(P, size, word):
    style = P._style
    c = neck_c(P)
    sw = P.sx + 0.07
    if style == "mantle":         # a short cape over the shoulders, all round
        m = P.material(word, "under")
        z0, z1 = P.neckz + 0.02, P.armz - 0.2 * size * P.t
        P.add("mantle", drape((0, c.y + 0.02, 0), lambda t: (0.12 + (sw + 0.05 - 0.12) * t ** 0.6, 0.12 + (sw * 0.78 - 0.12) * t ** 0.6), [z0, (z0 + z1) / 2 + 0.05, z1], -math.pi * 0.96, math.pi * 0.96, thick=0.03, n=12), m, "chest", smooth=True)
    else:
        shadow = style == "shadow-cloak"
        m = mat("shade") if shadow else P.material(word, "trim")
        z0 = P.neckz + 0.01
        z1 = (0.03 if shadow else max(P.footz + 0.12, P.kneez - 0.1)) if size >= 1.0 else P.hipz - 0.1
        zs = [z0, P.armz - 0.1, (P.armz + z1) / 2, z1]
        hem = (lambda a: 0.07 * math.sin(a * 7.0)) if shadow else None
        wide = 1.0 + 0.35 * (size - 1.0) if shadow else 1.0
        P.add("cloak", drape((0, c.y + 0.03, 0), lambda t: (0.13 + (sw * wide + 0.1 * t - 0.13) * min(1.0, t * 3.0) ** 0.7, 0.13 + (sw * 0.8 * wide + 0.14 * t - 0.13) * min(1.0, t * 3.0) ** 0.7),
                             zs, -math.pi * 0.62, math.pi * 0.62, thick=0.03, n=11, hem=hem, trail=(0.5 * size if shadow else 0.0)), m, "chest", smooth=True)
        if shadow:                # and its edge, coming apart
            tat = None
            for k in range(7):
                a = -1.6 + 3.2 * k / 6
                b0 = Vector((sw * wide * 1.1 * math.sin(a), c.y + 0.03 + (sw * 0.9 * wide + 0.14) * math.cos(a) + 0.5 * size * max(0.0, math.cos(a)), 0.1))
                tat = g.merge(tat, g.blade(b0, b0 + Vector((0.16 * math.sin(a), 0.3 * max(0.2, math.cos(a)), -0.06)), 0.2, normal=Z, belly=0.4))
            P.add("cloak_tatters", tat, mat("shade_edge"), "chest", smooth=True)


@slot("wear", "hood")
def wear_hood(P, size, word):
    """A hood up over the head; the face in it."""
    m = P.material(word, "trim") if word != "shade" else mat("shade")
    e = P.eye
    face = (P.v0[:, 1] < e.y + 0.1 * P.hr) & (P.v0[:, 2] < e.z + 0.9 * P.hr) & (np.abs(P.v0[:, 0]) < 0.8 * P.hr)
    P.wear(P.headv & ~face, m, 0.05 * size)
    c = neck_c(P)
    P.add("hood_cowl", _hoop((0, c.y, P.neckz - 0.02), 0.19 * P.t + 0.04, 0.19 * P.t + 0.04, 0.06 * P.t, u=X, v=Y, n=10, sides=5), m, "chest", smooth=True)


@slot("wear", "bandolier")
def wear_bandolier(P, size, word):
    m = P.material(word, "under")
    hw, hd, yo = P.ring(P.chestz - 0.1 * P.t)
    zc = (P.armz + P.hipz) / 2 + 0.08 * P.t
    u = Vector((hw + 0.02, 0, (P.armz - P.hipz) * 0.42)).normalized()
    P.add("bandolier", _hoop((0, yo, zc), math.hypot(hw + 0.03, (P.armz - P.hipz) * 0.42), hd + 0.035, 0.03 * size, u=u, v=Y, n=12, sides=4), m, "chest", smooth=True)


@slot("wear", "pauldrons", "beetle-plates", "strap-plates")
def wear_plates(P, size, word):
    style = P._style
    m = P.material(word, {"pauldrons": "under", "beetle-plates": "beetle", "strap-plates": "under"}[style])
    for s, tag in ((1, "l"), (-1, "r")):
        c = (s * (P.sx + 0.02), P.army, P.armz + 0.07)
        P.add("pauldron_" + tag, g.ico(c, 0.16 * size * P.t, sub=1, scale=(1.15, 1.0, 0.62), rot=(0, s * -0.35, 0)), m, "chest", smooth=False)
    if style == "beetle-plates":     # and a breastplate, in two wing-cases
        for s, tag in ((1, "l"), (-1, "r")):
            x = s * 0.09 * P.t
            P.add("breast_" + tag, g.ico((x, P.front(P.chestz - 0.05 * P.t, x) - 0.02, P.chestz - 0.06 * P.t), 0.2 * size * P.t, sub=1, scale=(0.62, 0.4, 1.0), rot=(0.1, 0, s * 0.1)), m, "chest", smooth=False)
    if style == "strap-plates":      # the straps the plates ride on
        hw, hd, yo = P.ring(P.chestz)
        for s in (1, -1):
            pts = [(s * P.sx * 0.7, P.rear(P.chestz, s * 0.1) + 0.04, P.hipz + 0.25 * P.t), (s * P.sx * 0.8, yo, P.armz + 0.1), (s * P.sx * 0.7, P.front(P.chestz, s * 0.1) - 0.04, P.hipz + 0.25 * P.t)]
            P.add("strap_%d" % s, g.tube(pts, [0.035, 0.035, 0.035], n=4, flat=0.4), P.material("trim"), "chest", smooth=True)


@slot("wear", "padding")
def wear_padding(P, size, word):
    """Quilted, like a pell's own padding."""
    m = P.material(word, "cloth_wool")
    P.wear(P.trunk(P.hipz - 0.08, P.neckz - 0.02) | P.sleeves(0.0, P.ex), m, 0.06 * size)
    for i in range(3):
        z = P.hipz + (P.neckz - P.hipz) * (0.2 + 0.28 * i)
        hw, hd, yo = P.ring(z)
        P.add("quilt_%d" % i, _hoop((0, yo, z), hw + 0.062 * size, hd + 0.062 * size, 0.012, u=X, v=Y, n=12, sides=3), mat("leather_dark"), "chest" if z > P.J["chest"].z else "spine")


@slot("wear", "bandages")
def wear_bandages(P, size, word):
    m = P.material(word, "paper")
    for i in range(int(round(2 * size))):
        z = P.hipz + (P.neckz - P.hipz) * (0.3 + 0.2 * i)
        hw, hd, yo = P.ring(z)
        P.add("bandage_%d" % i, _hoop((0, yo, z), hw + 0.02, hd + 0.02, 0.035, u=Vector((1, 0, 0.18 * (1 - 2 * (i % 2)))).normalized(), v=Y, n=12, sides=4), m, "chest" if z > P.J["chest"].z else "spine", smooth=True)
    x = P.sx + (P.ex - P.sx) * 0.6
    row = arm_row(P, x)
    P.add("bandage_arm", _hoop((x, P.army, P.armz), row[1] + 0.025, row[2] + 0.025, 0.04, u=Y, v=Z, n=8, sides=4), m, "upperarm.l", smooth=True)
