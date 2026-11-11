"""The Demon's line (lines_demon.py): what it is dressed in, what it wears on its head and
its back and at its belt, what is in its hands, what has become of its arms, and what keeps it
company. A garment is cut from the body's own skin (pushed out and painted), so it sits as the
skin sits and nothing shows through it; what hangs free is short, or hangs behind, or is its
own wings. Its knees come forward as a goat's do, so nothing here is a closed skirt."""
import math

import numpy as np
from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z, V
from genius_kit import mat, field
from lines_demon import slot, spline, plate, hoop, disc, drape, noise, mouth_at


def neck_c(P):
    return Vector((0, P.J["head"].y + 0.02, P.neckz))


def buttons(P, n, z0, z1, material="brass_gilt", x=0.0, out=0.05):
    geo = None
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        geo = g.merge(geo, g.ico((x, P.front(z, x) - out, z), 0.024 * P.t, sub=0, scale=(1, 0.5, 1)))
    P.add("buttons", geo, mat(material), "chest", smooth=False)


def arm_row(P, x):
    """The arm's section at a distance out: (x, half-depth, half-height)."""
    return P.hb._row(P.hb.rings("arm", "fit"), x)


# ======================================================================================
# What it is dressed in
# ======================================================================================

@slot("wear", "loincloth")
def wear_loincloth(P, size, word):
    """A band of linen at its hips, and a flap before and behind."""
    m = P.material(word, "under")
    P.wear(P.trunk(P.hipz - 0.1 * P.t, P.hipz + 0.17 * P.t), m, 0.03)
    hw, hd, yo = P.ring(P.hipz)
    P.add("loin_front", g.blade((0, yo - hd - 0.04, P.hipz + 0.12 * P.t), (0.02, yo - hd - 0.05 - 0.26 * size * P.t, P.hipz - 0.4 * size * P.t), 0.9 * hw, normal=(0, -1, 0.4), belly=0.34), m, "hips", smooth=True)
    P.add("loin_back", g.blade((0, yo + hd + 0.04, P.hipz + 0.12 * P.t), (0, yo + hd + 0.1, P.hipz - 0.34 * size * P.t), 1.2 * hw, normal=Y, belly=0.34), m, "hips", smooth=True)


@slot("wear", "breeches")
def wear_breeches(P, size, word):
    """Breeches to the knee."""
    z = P.v0[:, 2]
    P.wear(~P.arm & ~P.headv & (z > P.kneez - 0.07) & (z < P.hipz + 0.12 * P.t), P.material(word, "cloth_sable"), 0.028)


@slot("wear", "shirt")
def wear_shirt(P, size, word):
    P.wear(P.trunk(P.hipz, P.neckz) | P.sleeves(0.0, P.wx - 0.06), P.material(word, "under"), 0.024)


def peplum(P, name, z_top, z_bot, flare, material, n=12):
    """A short stiff skirt to a doublet: wider before, where the thighs come forward."""
    hw, hd, yo = P.ring(z_top)
    rings = []
    for i in range(3):
        t = i / 2.0
        z = z_top + (z_bot - z_top) * t
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n
            fwd = max(0.0, -math.sin(a))
            k = flare * t * (1.0 + 1.6 * fwd)
            ring.append(Vector(((hw + 0.04 + k) * math.cos(a), yo + (hd + 0.04 + k) * math.sin(a), z)))
        rings.append(ring)
    P.add(name, g.loft(rings, caps=True), material, "hips", smooth=True)


@slot("wear", "doublet")
def wear_doublet(P, size, word):
    """A close black doublet to the wrists, buttoned in brass, with a short skirt to it piped
    in its Path's colour."""
    m = P.material(word, "cloth_sable")
    P.wear(P.trunk(P.hipz - 0.02, P.neckz + 0.03) | P.sleeves(0.0, P.wx - 0.05), m, 0.036)
    peplum(P, "doublet_skirt", P.hipz + 0.14 * P.t, P.hipz - 0.1 * P.t, 0.07 * P.t, m)
    hw, hd, yo = P.ring(P.hipz + 0.15 * P.t)
    P.add("doublet_piping", hoop((0, yo, P.hipz + 0.15 * P.t), hw + 0.05, hd + 0.05, 0.02 * P.t, n=14, sides=4), mat("accent_light"), "hips", smooth=True)
    buttons(P, 4, P.hipz + 0.2 * P.t, P.neckz - 0.08 * P.t, "brass_crown")
    c = neck_c(P)
    r = 0.11 * P.t + 0.03
    P.add("doublet_collar", hoop((c.x, c.y, P.neckz + 0.03 * P.t), r + 0.02, r + 0.02, 0.034 * P.t, n=10, sides=4), m, "chest", smooth=True)
    for s, tag in ((1, "l"), (-1, "r")):       # a roll at each shoulder, and a white cuff
        P.add("doublet_roll_" + tag, g.ico((s * (P.sx + 0.03), P.army, P.armz + 0.05), 0.15 * P.t, sub=1, scale=(0.8, 1.0, 0.9)), m, "chest", smooth=True)
        row = arm_row(P, P.wx - 0.06)
        P.add("doublet_cuff_" + tag, hoop((s * (P.wx - 0.06), P.army, P.armz), row[1] + 0.04, row[2] + 0.04, 0.024, u=Y, v=Z, n=8, sides=4), mat("cloth_white"), "lowerarm." + tag, smooth=True)


@slot("wear", "waistcoat")
def wear_waistcoat(P, size, word):
    """A waistcoat in its Path's colour: plain, striped, or left open over a full belly."""
    m = mat("accent")
    mask = P.trunk(P.hipz + 0.03 * P.t, P.neckz - 0.1 * P.t)
    hw = P.ring(P.chestz)[0]
    if word == "open":
        mask &= ~((np.abs(P.v0[:, 0]) < 0.34 * hw) & (P.v0[:, 1] < P.J["chest"].y))
    P.wear(mask, m, 0.034)
    if word == "striped":
        P.paint(mask & (np.mod(P.v0[:, 0] + 10.0, 0.11 * P.t) < 0.05 * P.t), mat("accent_dark"))
    if word != "open":
        buttons(P, 4, P.hipz + 0.1 * P.t, P.chestz + 0.06 * P.t, "brass_gilt", out=0.045)


@slot("wear", "tailcoat", "gown")
def wear_tailcoat(P, size, word):
    """A coat cut away in front to show the waistcoat, with lapels in its Path's colour (its
    tails are its own wings). parti: of two halves. A gown is the same worn long and open, to
    the hocks behind (bell: a host's, wide as a bell)."""
    style = P._style
    coat = mat("cloth_coat")
    hw = P.ring(P.chestz)[0]
    x, y = P.v0[:, 0], P.v0[:, 1]
    body = P.trunk(P.hipz + 0.02, P.neckz + 0.03) & ~((np.abs(x) < 0.5 * hw) & (y < P.J["chest"].y))
    mask = body | P.sleeves(0.0, P.wx - 0.06)
    P.wear(mask, coat, 0.052)
    if word == "parti":
        P.paint(mask & (x > 0), mat("accent_dark"))
    c = neck_c(P)
    for s, tag in ((1, "l"), (-1, "r")):
        # the lapel: from the collar down the edge of the coat to the waist
        zt, zb = P.neckz - 0.02 * P.t, P.hipz + 0.22 * P.t
        xa = s * 0.5 * hw
        pts = [Vector((s * 0.16 * P.t, P.front(zt, s * 0.1) - 0.05, zt)), Vector((xa * 1.08, P.front((zt + zb) / 2, xa) - 0.062, (zt + zb) / 2 + 0.1 * P.t)), Vector((xa * 0.9, P.front(zb, xa * 0.9) - 0.058, zb))]
        P.add("lapel_" + tag, g.tongue(pts, [0.07 * P.t, 0.17 * P.t, 0.05 * P.t], thick=0.22, normal=Y), mat("accent_light") if not (word == "parti" and s > 0) else coat, "chest", smooth=True)
        row = arm_row(P, P.wx - 0.07)
        P.add("coat_cuff_" + tag, hoop((s * (P.wx - 0.07), P.army, P.armz), row[1] + 0.055, row[2] + 0.055, 0.03, u=Y, v=Z, n=8, sides=4), coat if not (word == "parti" and s > 0) else mat("accent_dark"), "lowerarm." + tag, smooth=True)
    r = 0.11 * P.t + 0.04
    P.add("coat_collar", hoop((c.x, c.y + 0.02, P.neckz + 0.02 * P.t), r + 0.03, r + 0.03, 0.04 * P.t, n=10, sides=4, a0=-math.pi * 0.1, a1=math.pi * 1.1), coat, "chest", smooth=True)
    if style == "gown":
        sw = P.sx + 0.06
        z0, z1 = P.armz - 0.04, max(P.hockz + 0.02, P.hipz - 0.9 * P.t * size)
        bell = 0.3 if word == "bell" else 0.1
        geo = drape((0, c.y + 0.03, 0), lambda t, a: (0.14 + (sw + bell * t * P.t - 0.14) * min(1.0, t * 3.2) ** 0.7, 0.14 + (sw * 0.84 + (bell + 0.08) * t * P.t - 0.14) * min(1.0, t * 3.2) ** 0.7),
                    [z0 + 0.12, z0 - 0.1 * P.t, (z0 + z1) / 2, z1], -math.pi * 0.6, math.pi * 0.6, thick=0.03, n=11)
        P.add("gown", geo, coat, "chest", smooth=True)
        hemr = sw + bell * P.t
        P.add("gown_hem", hoop((0, c.y + 0.03, z1 + 0.02), hemr + 0.012, hemr * 0.84 + (bell + 0.08) * P.t * 0.6 + 0.04, 0.022 * P.t, u=Y, v=X, n=12, sides=3, a0=-math.pi * 0.6, a1=math.pi * 0.6), mat("accent_light"), "chest", smooth=True)


@slot("wear", "cravat", "bands")
def wear_cravat(P, size, word):
    """White at its throat: a tied cravat (napkin: tucked in, for the table), or a judge's bands."""
    white = mat("cloth_white")
    z = P.neckz - 0.05 * P.t
    y = P.front(z) - 0.035
    if P._style == "bands":
        for s in (1, -1):
            P.add("bands_%d" % s, g.box((s * 0.045 * P.t, P.front(z - 0.12 * P.t) - 0.05, z - 0.1 * P.t), (0.07 * P.t, 0.02, 0.22 * P.t), rot=(0.1, 0, s * 0.08)), white, "chest", smooth=False)
        return
    P.add("cravat_knot", g.ico((0, y - 0.01, z), 0.065 * P.t, sub=1, scale=(1.2, 0.7, 0.8)), white, "chest", smooth=True)
    if word == "napkin":
        zb = P.hipz + 0.5 * P.t
        P.add("napkin", g.blade((0, y, z), (0, P.front(zb) - 0.07, zb - 0.1 * P.t * size), 0.5 * P.t * size, normal=Y, belly=0.55, thick=0.02), white, "chest", smooth=True)
        return
    for s in (1, -1):
        P.add("cravat_fall_%d" % s, g.blade((s * 0.02, y, z), (s * 0.07 * P.t, P.front(z - 0.22 * P.t, s * 0.05) - 0.06, z - 0.26 * P.t * size), 0.12 * P.t, normal=Y, belly=0.6, thick=0.018), white, "chest", smooth=True)


@slot("wear", "cuffs", "glove", "bracers")
def wear_wrists(P, size, word):
    """Cuffs in its Path's colour; one white glove; bracers of leather or iron."""
    ax = np.abs(P.v0[:, 0])
    style = P._style
    if style == "cuffs":
        P.wear(P.sleeves(P.wx - 0.17, P.wx - 0.02), mat("accent_light"), 0.056)
    elif style == "glove":
        P.wear((P.hand | (P.arm & (ax > P.wx - 0.1))) & (P.v0[:, 0] > 0), mat("cloth_white"), 0.018)
    else:
        m = mat("metal_iron_light") if word == "iron" else mat("leather_dark")
        P.wear(P.sleeves(P.ex + 0.07, P.wx - 0.03), m, 0.045 * size)
        for s, tag in ((1, "l"), (-1, "r")):
            for xx in (P.ex + 0.09, P.wx - 0.05):
                row = arm_row(P, xx)
                P.add("bracer_band_%s_%d" % (tag, int(xx * 100)), hoop((s * xx, P.army, P.armz), row[1] + 0.05 * size, row[2] + 0.05 * size, 0.022, u=Y, v=Z, n=8, sides=4),
                      mat("brass_crown") if word != "iron" else mat("metal_iron"), "lowerarm." + tag, smooth=False)


@slot("wear", "belt", "belt-wide")
def wear_belt(P, size, word):
    wide = P._style == "belt-wide"
    z = P.hipz + 0.15 * P.t
    hw, hd, yo = P.ring(z)
    P.wear(P.trunk(z - (0.1 if wide else 0.05) * P.t, z + (0.1 if wide else 0.05) * P.t), mat("leather_dark"), 0.05)
    k = 2.0 if wide else 1.0
    P.add("buckle", g.box((0, yo - hd - 0.06, z), (0.11 * P.t * k, 0.03, 0.1 * P.t * k)), mat("brass_crown"), "hips", smooth=False)


@slot("wear", "sash")
def wear_sash(P, size, word):
    """A sash from the right shoulder to the left hip, as an order is worn, knotted at the hip."""
    m = P.material(word, "accent")
    hw, hd, yo = P.ring(P.chestz - 0.1 * P.t)
    zc = (P.armz + P.hipz) / 2 + 0.08 * P.t
    u = Vector((hw + 0.02, 0, -(P.armz - P.hipz) * 0.42)).normalized()
    P.add("sash", hoop((0, yo, zc), math.hypot(hw + 0.035, (P.armz - P.hipz) * 0.42), hd + 0.045, 0.036 * size * P.t, u=u, v=Y, n=14, sides=4), m, "chest", smooth=True)
    hx = P.ring(P.hipz + 0.14 * P.t)[0]
    b0 = Vector((hx + 0.03, yo - 0.02, P.hipz + 0.16 * P.t))
    P.add("sash_knot", g.ico(b0, 0.06 * P.t, sub=1), m, "hips", smooth=True)
    P.add("sash_end", g.blade(b0, b0 + Vector((0.06, 0.03, -0.3 * P.t)), 0.12 * P.t, normal=(1, -0.3, 0), belly=0.6), m, "hips", smooth=True)


@slot("wear", "collar-fur", "ruff", "scarf-long")
def wear_neck(P, size, word):
    """Round its neck: a collar of white fur, spotted (a rank's); a starched ruff; a long scarf
    that trails."""
    style = P._style
    c = neck_c(P)
    if style == "collar-fur":
        z = P.neckz - 0.05 * P.t
        P.add("collar_fur", hoop((0, c.y + 0.02, z), P.sx * 0.92, P.sx * 0.74, 0.095 * size * P.t, n=14, sides=5), mat("fur_ermine"), "chest", smooth=True)
        spots = None
        for i in range(9):
            a = 2 * math.pi * (i + 0.5) / 9
            spots = g.merge(spots, g.ico((P.sx * 0.94 * math.cos(a), c.y + 0.02 + P.sx * 0.76 * math.sin(a), z + 0.07 * P.t * (1 if i % 2 else -0.2)), 0.035 * P.t, sub=0, scale=(1, 1, 1.5)))
        P.add("collar_spots", spots, mat("fur_sable"), "chest", smooth=True)
    elif style == "ruff":
        n = 16
        r0, r1 = 0.11 * P.t + 0.02, (0.11 * P.t + 0.02) + 0.24 * P.t * size
        z = P.neckz + 0.04 * P.t
        top, bot, itop, ibot = [], [], [], []
        for k in range(n):
            a = 2 * math.pi * k / n
            wob = 0.05 * P.t * (1 if k % 2 else -1)
            top.append(Vector((r1 * math.cos(a), c.y + r1 * math.sin(a), z + wob + 0.014)))
            bot.append(Vector((r1 * math.cos(a), c.y + r1 * math.sin(a), z + wob - 0.014)))
            itop.append(Vector((r0 * math.cos(a), c.y + r0 * math.sin(a), z + 0.03)))
            ibot.append(Vector((r0 * math.cos(a), c.y + r0 * math.sin(a), z - 0.03)))
        P.add("ruff", g.loft([itop, top, bot, ibot, itop], caps=False), mat("cloth_white"), "chest", smooth=False)
    else:
        m = mat("accent")
        r = 0.11 * P.t + 0.05
        P.add("scarf", hoop((c.x, c.y, P.neckz - 0.01), r, r, 0.055 * P.t, n=10, sides=5), m, "chest", smooth=True)
        b0 = Vector((0.06, c.y + r, P.neckz - 0.02))
        pts = [b0, b0 + Vector((0.05, 0.3, -0.05)) * P.t, b0 + Vector((0.12, 0.62, -0.3)) * P.t * size, b0 + Vector((0.1, 0.9, -0.36)) * P.t * size]
        P.rider("sway", "scarf", [(g.tongue(spline(pts, 2), [0.13 * P.t, 0.14 * P.t, 0.15 * P.t, 0.15 * P.t, 0.14 * P.t, 0.12 * P.t, 0.05 * P.t], thick=0.2, normal=Z), m)], b0, "chest")


@slot("wear", "harness", "door-straps")
def wear_straps(P, size, word):
    """Leather over its chest: one strap and a ring (harness), or two crossed, for what it
    carries on its back."""
    m = mat("leather_dark")
    hw, hd, yo = P.ring(P.chestz - 0.1 * P.t)
    zc = (P.armz + P.hipz) / 2 + 0.08 * P.t
    for s in ((1,) if P._style == "harness" else (1, -1)):
        u = Vector((s * (hw + 0.02), 0, (P.armz - P.hipz) * 0.42)).normalized()
        P.add("strap_%d" % s, hoop((0, yo, zc), math.hypot(hw + 0.03, (P.armz - P.hipz) * 0.42), hd + 0.036, 0.03 * size * P.t, u=u, v=Y, n=14, sides=4), m, "chest", smooth=True)
    z = P.chestz - 0.06 * P.t
    P.add("strap_ring", hoop((0, P.front(z) - 0.055, z), 0.06 * P.t, 0.06 * P.t, 0.016 * P.t, u=X, v=Z, n=8, sides=3), mat("brass_crown"), "chest", smooth=False)


@slot("wear", "pauldron", "pauldrons-stone")
def wear_pauldron(P, size, word):
    """A plate on its left shoulder (iron), or both shoulders set like stones."""
    stone = P._style == "pauldrons-stone"
    m = mat("stone_dust") if stone else mat("metal_iron_light")
    for s, tag in (((1, "l"), (-1, "r")) if stone else ((1, "l"),)):
        c = (s * (P.sx + 0.03), P.army, P.armz + 0.08)
        P.add("pauldron_" + tag, g.ico(c, 0.2 * size * P.t, sub=1, scale=(1.15, 1.05, 0.66), rot=(0, s * -0.35, 0)), m, "chest", smooth=False)
        if not stone:
            P.add("pauldron_rim_" + tag, hoop((s * (P.sx + 0.03), P.army, P.armz + 0.0), 0.22 * P.t, 0.2 * P.t, 0.02 * P.t, n=10, sides=3), mat("brass_crown"), "chest", smooth=False)


@slot("wear", "war-kilt")
def wear_war_kilt(P, size, word):
    """A wide belt, and straps hanging from it all round, in its Path's colour and in leather
    turn about; they lie out over its thighs in front."""
    z = P.hipz + 0.16 * P.t
    hw, hd, yo = P.ring(z)
    P.wear(P.trunk(z - 0.09 * P.t, z + 0.09 * P.t), mat("leather_dark"), 0.05)
    P.add("kilt_plate", g.box((0, yo - hd - 0.065, z), (0.2 * P.t, 0.035, 0.18 * P.t)), mat("brass_crown"), "hips", smooth=False)
    a_geo, b_geo, studs = None, None, None
    n = 12
    L = 0.44 * P.t * size
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        d = Vector((math.sin(a), math.cos(a), 0))
        fwd = max(0.0, -math.cos(a))
        base = Vector((d.x * (hw + 0.045), yo + d.y * (hd + 0.045), z - 0.06 * P.t))
        tip = base + d * L * (0.12 + 0.62 * fwd * fwd) + Vector((0, 0, -L * (1.0 - 0.34 * fwd)))
        bl = g.blade(base, tip, 0.2 * P.t, normal=d + Vector((0, 0, 0.3 + 0.5 * fwd)), belly=0.7, thick=0.03)
        if i % 2:
            a_geo = g.merge(a_geo, bl)
        else:
            b_geo = g.merge(b_geo, bl)
        studs = g.merge(studs, g.ico(base.lerp(tip, 0.72) + d * 0.03, 0.026 * P.t, sub=0))
    P.add("kilt_a", a_geo, mat("accent"), "hips", smooth=False)
    P.add("kilt_b", b_geo, mat("accent_dark"), "hips", smooth=False)
    P.add("kilt_studs", studs, mat("brass_crown"), "hips", smooth=False)


@slot("wear", "paint")
def wear_paint(P, size, word):
    """Its Path's colour on its own hide: a band round each arm, a mark down the chest, and a
    stripe under the eyes."""
    m = mat("accent")
    x, y, z = P.v0[:, 0], P.v0[:, 1], P.v0[:, 2]
    ax = np.abs(x)
    span = P.ex - P.sx
    P.paint(P.sleeves(P.sx + 0.34 * span, P.sx + 0.56 * span) | P.sleeves(P.sx + 0.7 * span, P.sx + 0.82 * span), m)
    chev = P.trunk(P.hipz + 0.3 * P.t, P.neckz - 0.05 * P.t, front=True) & (np.abs(z - (P.chestz + 0.12 * P.t - 1.1 * ax)) < 0.07 * P.t * size) & (ax < P.ring(P.chestz)[0] * 0.9)
    P.paint(chev, m)
    e, hr = P.eye, P.hr
    P.paint(P.headv & ~P.ears & (y < P.hcy - 0.1 * hr) & (np.abs(z - (e.z - 0.62 * hr)) < 0.15 * hr), m)


# ======================================================================================
# The skin's own marks
# ======================================================================================

@slot("skin", "stone-dust", "ribs")
def skin_marks(P, size, word):
    """Plaster and stone dust set on whatever of it faces up; or its ribs standing out."""
    x, z = P.v0[:, 0], P.v0[:, 2]
    if P._style == "stone-dust":
        up = (P.n[:, 2] > 0.25) & ~P.headv & (z > P.chestz - 0.2 * P.t * size)
        P.paint(up, mat("stone_dust"))
        P.v[up] += P.n[up] * (np.abs(noise(P.v0[up], 19.0)) * 0.03 * size)[:, None]
    else:
        side = P.trunk(P.hipz + 0.34 * P.t, P.chestz + 0.12 * P.t) & (np.abs(x) > 0.08 * P.t)
        gap = np.mod(z, 0.1 * P.t) < 0.045 * P.t
        P.paint(side & gap, mat("hide_shadow"))
        P.v[side & ~gap] += P.n[side & ~gap] * 0.02


# ======================================================================================
# What it wears on its head
# ======================================================================================

def crown_c(P, drop=0.56):
    return Vector((0, P.hcy, P.crown - drop * P.hr))


def crown_band(c, rx, ry, z0, z1, a0, a1, thick, n=14):
    """Part of a band about a head: from angle a0 to a1 (0 is its left; a quarter turn its back)."""
    rings = []
    for (kx, ky, z) in ((rx, ry, z0), (rx * 1.04, ry * 1.04, z1), (rx * 1.04 - thick, ry * 1.04 - thick, z1), (rx - thick, ry - thick, z0)):
        rings.append([Vector((c.x + kx * math.cos(a0 + (a1 - a0) * k / n), c.y + ky * math.sin(a0 + (a1 - a0) * k / n), c.z + z)) for k in range(n + 1)])
    verts, faces = [], []
    m = n + 1
    for ring in rings:
        verts.extend(ring)
    for i in range(4):
        j = (i + 1) % 4
        for k in range(n):
            faces.append((i * m + k, i * m + k + 1, j * m + k + 1, j * m + k))
    faces.append((0, m, 2 * m, 3 * m))
    faces.append((4 * m - 1, 3 * m - 1, 2 * m - 1, m - 1))
    return verts, faces


@slot("crown", "broken", "mended", "iron")
def crown_worn(P, size, word):
    """The crown: a third of it gone and the rest cracked, and worn anyway (broken); mended
    with wire and worn straight; or a band of iron with nothing to it at all."""
    style, hr = P._style, P.hr
    c = crown_c(P)
    rx, ry = hr * 0.93, hr * 1.02
    tall = 0.26 * hr * size
    whole = style != "broken"
    a0, a1 = (0.0, 2 * math.pi) if whole else (math.pi * 0.72, math.pi * 2.28)      # what is gone is over its left ear
    m = mat("metal_iron_light") if style == "iron" else mat("brass_crown")
    tilt = Matrix.Rotation(0.0 if whole else 0.14, 4, "Y")
    T = Matrix.Translation(c) @ tilt @ Matrix.Translation(-c)
    P.add("crown_band", g.moved(crown_band(c, rx, ry, 0.0, tall, a0, a1, 0.035 * hr, n=14 if whole else 10), T), m, "head", smooth=False)
    if style == "iron":
        riv = None
        for i in range(8):
            a = 2 * math.pi * i / 8
            riv = g.merge(riv, g.ico(c + Vector((rx * 1.04 * math.cos(a), ry * 1.04 * math.sin(a), tall * 0.5)), 0.045 * hr, sub=0))
        P.add("crown_rivets", riv, mat("metal_iron"), "head", smooth=False)
        return
    pts = None
    n = 7 if whole else 5
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n
        b0 = c + Vector((rx * 1.03 * math.cos(a), ry * 1.03 * math.sin(a), tall))
        high = (0.4 if whole else 0.3 + 0.12 * (i % 2)) * hr * size
        pts = g.merge(pts, g.blade(b0 + Vector((0, 0, -0.03 * hr)), b0 + Vector((math.cos(a) * 0.05 * hr, math.sin(a) * 0.05 * hr, high)), 0.24 * hr, normal=(math.cos(a), math.sin(a), 0), belly=0.3, thick=0.03 * hr))
    P.add("crown_points", g.moved(pts, T), m, "head", smooth=False)
    # the stone at the front of it: the one light it keeps
    front = c + Vector((0, -ry * 1.06, tall * 0.5))
    P.add("crown_stone", g.moved(g.ico(front, 0.085 * hr, sub=0, scale=(1, 0.6, 1.2)), T), field("crown", 2.6), "head", smooth=False)
    crack = c + Vector((rx * 1.05 * math.cos(-math.pi * 0.28), ry * 1.05 * math.sin(-math.pi * 0.28), tall * 0.5))
    if style == "broken":
        P.add("crown_crack", g.moved(g.box(crack, (0.03 * hr, 0.05 * hr, tall * 1.1), rot=(0, 0.3, -math.pi * 0.28)), T), mat("void"), "head", smooth=False)
    else:                       # wire, where it was mended: three stitches over the crack
        wire = None
        for k in (-1, 0, 1):
            wire = g.merge(wire, hoop(crack + Vector((0, 0, k * tall * 0.3)), 0.05 * hr, 0.05 * hr, 0.012 * hr, u=Vector((math.cos(-math.pi * 0.28 + math.pi / 2), math.sin(-math.pi * 0.28 + math.pi / 2), 0)), v=Z, n=6, sides=3))
        P.add("crown_wire", wire, mat("metal_iron_light"), "head", smooth=False)


@slot("crown", "wreath")
def crown_wreath(P, size, word):
    """A wreath of leaves hung from horn to horn, that swings as it walks."""
    hr = P.hr
    k = 1.2
    a = Vector((1.36 * hr * k, P.hcy - 0.2 * hr, P.crown + 0.3 * hr * k))
    b = Vector((-a.x, a.y, a.z))
    mid = Vector((0, a.y - 0.1 * hr, P.crown + 0.02 * hr))
    line = spline([a, a.lerp(mid, 0.6) + Vector((0, 0, -0.1 * hr)), mid, b.lerp(mid, 0.6) + Vector((0, 0, -0.1 * hr)), b], 3)
    leaves, fruit = None, None
    for i, q in enumerate(line):
        for sg in (1, -1):
            leaves = g.merge(leaves, g.blade(q, q + Vector((0.1 * sg * hr, -0.1 * hr * (i % 2), -0.3 * hr * (0.7 + 0.3 * (i % 3)))), 0.2 * hr, normal=(0, -1, 0.3 * sg), belly=0.4))
        if i % 3 == 1:
            fruit = g.merge(fruit, g.ico(q + Vector((0, -0.06 * hr, -0.14 * hr)), 0.075 * hr, sub=1))
    P.rider("sway", "wreath", [(g.tube(line, [0.025 * hr] * len(line), n=3), "leaf_vine"), (leaves, "leaf_vine"), (fruit, "accent_light")], Vector((0, a.y, a.z)), "head")


@slot("crown", "flame")
def crown_flame(P, size, word):
    """No head: where it was, a crown of flame (demon_form has already drawn the head in under
    the collar, and the eyes hang in the fire). The heart of it is the field's light; the
    tongues round it are its Path's colour."""
    hr = P.hr
    c = Vector((0, P.hcy, P.chin + 0.1 * P.hh))
    top = P.crown - c.z
    core = [(0.0, 0.0, 1.35), (0.34, -0.1, 0.9), (-0.34, -0.1, 0.94)]
    for i, (dx, dy, tall) in enumerate(core):
        b0 = c + Vector((dx * hr, dy * hr, 0))
        P.rider("flick", "crown", [(g.blade(b0, b0 + Vector((dx * 0.2 * hr, 0, tall * top * size)), 0.56 * hr, normal=Y, belly=0.3, thick=0.2 * hr), field("flame", 2.6))], b0, "head", n=i)
    for i in range(7):          # the points of the crown: round the fire, leaning out
        a = -math.pi / 2 + math.pi / 7 + 2 * math.pi * i / 7
        d = Vector((math.cos(a), math.sin(a) * 0.9, 0))
        b0 = c + d * hr * 0.62
        tall = (0.74 + 0.3 * max(0.0, -math.sin(a)) + 0.12 * (i % 2)) * top * size
        P.rider("flick", "crownpoint", [(g.blade(b0, b0 + d * hr * 0.3 + Vector((0, 0, tall)), 0.42 * hr, normal=d, belly=0.3, thick=0.1 * hr), mat("accent_light" if i % 2 else "accent"))], b0, "head", n=i)


# ======================================================================================
# What it carries on its back
# ======================================================================================

def door_leaf(c, w, h, t, paint, R=None, bars=False):
    """A door's leaf about c, w wide, h tall, facing along Y: planks, two iron straps, a ring.
    [(geometry, material name)]"""
    R = R or Matrix.Identity(3)

    def at(p):
        return c + R @ Vector(p)
    items = [(g.box(c, (w, t, h), rot=R), paint)]
    grooves, iron = None, None
    for k in (-1, 0, 1):
        for sy in (1, -1):
            grooves = g.merge(grooves, g.box(at((k * w * 0.25, sy * t * 0.5, 0)), (w * 0.025, t * 0.12, h * 0.94), rot=R))
    for zz in ((-0.3, 0.3) if not bars else (-0.34, 0.0, 0.34)):
        for sy in (1, -1):
            iron = g.merge(iron, g.box(at((0, sy * t * 0.56, zz * h)), (w * (1.04 if bars else 0.92), t * 0.2, h * (0.09 if bars else 0.06)), rot=R))
    studs = None
    for zz in ((-0.3, 0.3) if not bars else (-0.34, 0.0, 0.34)):
        for k in (-0.36, 0.0, 0.36):
            studs = g.merge(studs, g.ico(at((k * w, t * 0.7, zz * h)), w * 0.035, sub=0), g.ico(at((k * w, -t * 0.7, zz * h)), w * 0.035, sub=0))
    ring = hoop(at((w * 0.3, t * 0.75, -0.02 * h)), w * 0.09, w * 0.09, w * 0.02, u=R @ X, v=R @ Z, n=8, sides=3)
    return items + [(grooves, "void"), (iron, "metal_iron"), (studs, "metal_iron_light"), (ring, "brass_crown")]


def _back_y(P, z):
    return P.rear(z)


@slot("back", "door")
def back_door(P, size, word):
    """The door it left by, strapped to its back in its frame, hinges and all; painted its
    Path's colour. shut; or ajar: a hand open, and the light of the field through the gap."""
    w = (2 * P.sx + 0.26) * size
    h = (P.neckz - P.hipz) * 1.5 * size
    zc = P.hipz - 0.06 * P.t + h / 2
    y = _back_y(P, P.chestz) + 0.16 * P.t
    c = Vector((0, y, zc))
    t = 0.06 * P.t
    frame = g.merge(g.box(c + Vector((-(w / 2 + 0.035), 0, 0)), (0.07, t * 1.5, h + 0.07)), g.box(c + Vector(((w / 2 + 0.035), 0, 0)), (0.07, t * 1.5, h + 0.07)),
                    g.box(c + Vector((0, 0, h / 2 + 0.035)), (w + 0.2, t * 1.7, 0.08)), g.box(c + Vector((0, 0, -h / 2 - 0.02)), (w + 0.14, t * 1.5, 0.05)))
    P.add("door_frame", frame, mat("wood_door"), "chest", smooth=False)
    if word == "ajar":
        ang = 0.5
        R = Matrix.Rotation(ang, 3, "Z")
        hinge = c + Vector((-w / 2, 0, 0))
        leaf_c = hinge + R @ Vector((w / 2, 0, 0))
        for i, (geo, m) in enumerate(door_leaf(leaf_c, w, h, t, "accent", R=R)):
            P.add("door_%d" % i, geo, P.material(m), "chest", smooth=False)
        P.add("door_light", g.box(c + Vector((0, -t * 0.2, 0)), (w * 0.96, t * 0.3, h * 0.97)), field("door", 2.4), "chest", smooth=False)
    else:
        for i, (geo, m) in enumerate(door_leaf(c + Vector((0, t * 0.2, 0)), w, h, t, "accent")):
            P.add("door_%d" % i, geo, P.material(m), "chest", smooth=False)


@slot("back", "throne")
def back_throne(P, size, word):
    """The back of a throne, strapped behind its shoulders: tall, with two posts and a cushion
    of its Path's colour studded in brass."""
    w = (2 * P.sx + 0.2) * size
    z0, z1 = P.hipz + 0.05 * P.t, P.crown + 0.5 * P.hh * size
    y = _back_y(P, P.chestz) + 0.14 * P.t
    wood = mat("wood_door")
    c = Vector((0, y, (z0 + z1) / 2))
    h = z1 - z0
    P.add("throne_back", g.box(c, (w, 0.07 * P.t, h)), wood, "chest", smooth=False)
    P.add("throne_cushion", g.box(c + Vector((0, -0.03 * P.t, 0.02 * h)), (w * 0.74, 0.07 * P.t, h * 0.74)), mat("accent"), "chest", smooth=True)
    P.add("throne_cushion_back", g.box(c + Vector((0, 0.03 * P.t, 0.02 * h)), (w * 0.74, 0.05 * P.t, h * 0.74)), mat("accent_dark"), "chest", smooth=False)
    posts, knobs, studs = None, None, None
    for s in (1, -1):
        px = s * (w / 2 + 0.03)
        posts = g.merge(posts, g.box((px, y, c.z + 0.06 * h), (0.09 * P.t, 0.1 * P.t, h * 1.12)))
        knobs = g.merge(knobs, g.ico((px, y, z1 + 0.14 * h), 0.085 * P.t, sub=1, scale=(1, 1, 1.3)))
        for k in range(5):
            studs = g.merge(studs, g.ico((s * w * 0.37, y - 0.07 * P.t, c.z + (-0.3 + 0.16 * k) * h), 0.022 * P.t, sub=0))
    crest = g.blade((-w * 0.36, y, z1 - 0.01), (0, y, z1 + 0.2 * h), 0.2 * P.t, normal=Y, belly=0.5, thick=0.06 * P.t)
    crest = g.merge(crest, g.blade((w * 0.36, y, z1 - 0.01), (0, y, z1 + 0.2 * h), 0.2 * P.t, normal=Y, belly=0.5, thick=0.06 * P.t))
    P.add("throne_posts", posts, wood, "chest", smooth=False)
    P.add("throne_crest", crest, wood, "chest", smooth=False)
    P.add("throne_knobs", knobs, mat("brass_crown"), "chest", smooth=False)
    P.add("throne_studs", studs, mat("brass_crown"), "chest", smooth=False)


@slot("back", "spines")
def back_spines(P, size, word):
    """Horns down its back, from the nape to between the shoulders."""
    dark, pale = None, None
    for i in range(5):
        z = P.neckz - 0.02 - 0.17 * i * P.t
        b0 = Vector((0, _back_y(P, z) - 0.01, z))
        L = (0.34 - 0.04 * i) * P.t * size
        tip = b0 + Vector((0, 0.8 * L, 0.6 * L))
        mid = b0.lerp(tip, 0.6)
        dark = g.merge(dark, g.tube([b0, mid], [0.06 * P.t, 0.035 * P.t], n=5))
        pale = g.merge(pale, g.tube([mid, tip], [0.035 * P.t, 0.004], n=5))
    P.add("spines", dark, mat("horn_demon"), "chest", smooth=False)
    P.add("spine_tips", pale, mat("bone"), "chest", smooth=False)


# ======================================================================================
# On its chest, at its belt
# ======================================================================================

@slot("chest", "order", "chain-of-office", "flower")
def chest_worn(P, size, word):
    """A star of rank; a chain of office with its jewel; a flower at the collar."""
    style = P._style
    if style == "order":
        z = P.chestz + 0.02 * P.t
        x = 0.13 * P.t
        c = Vector((x, P.front(z, x) - 0.05, z))
        star = None
        for k in range(4):
            a = math.pi * k / 4
            d = Vector((math.cos(a), 0, math.sin(a))) * 0.1 * P.t * size
            star = g.merge(star, g.blade(c - d, c + d, 0.05 * P.t, normal=Y, belly=0.5, thick=0.014))
        P.add("order_star", star, mat("brass_gilt"), "chest", smooth=False)
        P.add("order_stone", g.ico(c + Vector((0, -0.016, 0)), 0.032 * P.t, sub=0), field("order", 2.4), "chest", smooth=False)
    elif style == "chain-of-office":
        c = neck_c(P)
        zc = P.chestz + 0.02 * P.t
        links = None
        n = 16
        for i in range(n):
            a = 2 * math.pi * i / n
            fr = max(0.0, -math.sin(a))
            p = Vector((P.sx * 0.86 * math.cos(a), c.y + 0.02 + P.sx * 0.72 * math.sin(a), P.neckz - 0.08 * P.t - fr * fr * (P.neckz - zc) * 0.9))
            if fr > 0.5:
                p.y = P.front(p.z, p.x) - 0.045
            links = g.merge(links, g.ico(p, 0.036 * P.t, sub=0, scale=(1.2, 1.0, 0.8)))
        P.add("chain_links", links, mat("brass_gilt"), "chest", smooth=False)
        j = Vector((0, P.front(zc - 0.06 * P.t) - 0.06, zc - 0.08 * P.t))
        P.add("chain_jewel_set", disc(j, 0.075 * P.t, normal=Y, thick=0.02, n=8), mat("brass_gilt"), "chest", smooth=False)
        P.add("chain_jewel", g.ico(j + Vector((0, -0.016, 0)), 0.04 * P.t, sub=0), field("jewel", 2.4), "chest", smooth=False)
    else:
        z = P.chestz + 0.14 * P.t
        x = 0.2 * P.t
        c = Vector((x, P.front(z, x) - 0.085, z))
        bloom = None
        for k in range(5):
            a = 2 * math.pi * k / 5
            bloom = g.merge(bloom, g.ico(c + Vector((math.cos(a), 0, math.sin(a))) * 0.04 * P.t, 0.045 * P.t, sub=0))
        P.add("flower", g.merge(bloom, g.ico(c + Vector((0, -0.02, 0)), 0.04 * P.t, sub=0)), mat("petal_rose"), "chest", smooth=True)
        P.add("flower_leaf", g.blade(c, c + Vector((0.1, 0.0, -0.12)) * P.t, 0.07 * P.t, normal=Y, belly=0.4, thick=0.01), mat("leaf_vine"), "chest", smooth=True)


@slot("chest", "belly-mouth")
def chest_belly_mouth(P, size, word):
    """A second mouth, across its belly: wide, with good teeth."""
    z = P.hipz + 0.36 * P.t
    hw, hd, yo = P.ring(z)
    w, tall = hw * 0.8 * size, 0.15 * P.t * size
    c = Vector((0, P.front(z) - 0.0, z))
    P.add("belly_maw", g.ico(c + Vector((0, 0.03, 0)), 1.0, sub=2, scale=(w, 0.09, tall)), mat("maw"), "spine", smooth=True)
    lips = [c + Vector((w * 1.04 * math.cos(a), -0.035 - 0.05 * abs(math.sin(a)) + 0.1 * (1 - abs(math.sin(a))) * abs(math.cos(a)) ** 3, tall * 1.1 * math.sin(a))) for a in [2 * math.pi * k / 14 for k in range(15)]]
    P.add("belly_lips", g.tube(lips, [0.035 * P.t] * len(lips), n=5, caps=False), P.skin, "spine", smooth=True)
    teeth = None
    n = 7
    for row in (1, -1):
        for i in range(n):
            t = -1.0 + 2.0 * (i + 0.5) / n
            b0 = c + Vector((t * w * 0.8, -0.04, row * tall * 0.8 * math.sqrt(max(0.0, 1.0 - t * t * 0.7))))
            teeth = g.merge(teeth, g.cone(b0, b0 + Vector((0, -0.02, -row * tall * 0.66)), w * 0.1, n=4))
    P.add("belly_teeth", teeth, mat("bone"), "spine", smooth=False)


@slot("chest", "yoke")
def chest_yoke(P, size, word):
    """Half a broken yoke round its neck, and a length of the chain it was led by, swinging."""
    c = neck_c(P)
    z = P.neckz - 0.03 * P.t
    r = P.sx * 0.86
    wood = mat("wood_yoke")
    pts = [Vector((r * math.cos(a), c.y + 0.03 + r * 0.82 * math.sin(a), z + 0.05 * P.t * math.sin(a))) for a in [math.pi * (-0.3 + 1.42 * k / 10.0) for k in range(11)]]
    P.add("yoke", g.tube(pts, [0.085 * P.t * size] * 9 + [0.07 * P.t, 0.05 * P.t], n=6), wood, "chest", smooth=False)
    end = pts[0]
    P.add("yoke_break", g.cone(end, end + Vector((0.1, -0.08, -0.04)) * P.t, 0.06 * P.t, n=4), wood, "chest", smooth=False)
    P.add("yoke_iron", hoop(pts[2], 0.1 * P.t, 0.1 * P.t, 0.024 * P.t, u=Y, v=Z, n=8, sides=4), mat("metal_iron"), "chest", smooth=False)
    b0 = pts[2] + Vector((0, -0.06 * P.t, -0.1 * P.t))
    links = None
    for k in range(5):
        q = b0 + Vector((0, 0, -0.11 * k * P.t))
        links = g.merge(links, hoop(q, 0.04 * P.t, 0.06 * P.t, 0.014 * P.t, u=(X if k % 2 else Y), v=Z, n=6, sides=3))
    P.rider("sway", "chain", [(links, "metal_iron_light")], b0, "chest", smooth=False)


@slot("belt", "key", "crown")
def belt_hung(P, size, word):
    """At its belt: the key of the door it left by, on a ring, swinging; or the crown, taken off."""
    z = P.hipz + 0.14 * P.t
    hw, hd, yo = P.ring(z)
    if P._style == "key":
        b0 = Vector((hw + 0.05, yo - 0.02, z))
        iron = "metal_iron_light"
        items = [(hoop(b0 + Vector((0, 0, -0.07 * P.t)), 0.07 * P.t * size, 0.07 * P.t * size, 0.016 * P.t, u=Y, v=Z, n=8, sides=3), iron),
                 (g.tube([b0 + Vector((0, 0, -0.14 * P.t)), b0 + Vector((0, 0, -0.5 * P.t * size))], 0.022 * P.t, n=5), iron),
                 (g.box(b0 + Vector((0, -0.05 * P.t, -0.44 * P.t * size)), (0.03 * P.t, 0.1 * P.t, 0.1 * P.t)), iron),
                 (g.box(b0 + Vector((0, -0.04 * P.t, -0.36 * P.t * size)), (0.03 * P.t, 0.07 * P.t, 0.035 * P.t)), iron)]
        P.rider("sway", "key", items, b0, "hips", smooth=False)
    else:
        c = Vector((-(hw + 0.07), yo + 0.02, z - 0.1 * P.t))
        r = 0.17 * P.t * size
        T = Matrix.Translation(c) @ Matrix.Rotation(1.25, 4, "Y") @ Matrix.Translation(-c)
        pts = None
        for i in range(5):
            a = math.pi * (0.7 + 1.5 * (i + 0.5) / 5)
            b0 = c + Vector((r * math.cos(a), r * math.sin(a), 0.07 * P.t))
            pts = g.merge(pts, g.blade(b0, b0 + Vector((0, 0, 0.11 * P.t)), 0.08 * P.t, normal=(math.cos(a), math.sin(a), 0), belly=0.3, thick=0.012))
        P.add("belt_crown", g.moved(g.merge(crown_band(c, r, r, 0.0, 0.08 * P.t, math.pi * 0.7, math.pi * 2.2, 0.014, n=9), pts), T), mat("brass_crown"), "hips", smooth=False)


# ======================================================================================
# Its arms, and what is in its hands
# ======================================================================================

@slot("arms", "gilded", "four", "smoke")
def arms(P, size, word):
    """Its right arm gone to gold from the fingers to the elbow; a second pair, folded across
    its chest above the first; or both going to smoke below the elbow."""
    style = P._style
    x = P.v0[:, 0]
    ax = np.abs(x)
    if style == "gilded":
        m = P.arm & (x < 0) & (ax > P.ex - 0.02)
        P.wear(m, mat("brass_gilt"), 0.012)
        row = arm_row(P, P.ex)
        P.add("gilt_band", hoop((-P.ex + 0.02, P.army, P.armz), row[1] + 0.035, row[2] + 0.035, 0.026, u=Y, v=Z, n=8, sides=4), mat("brass_crown"), "lowerarm.r", smooth=False)
    elif style == "smoke":
        m = P.arm & (ax > P.ex + 0.04)
        P.paint(m, mat("shade"))
        P.v[m] += P.n[m] * (noise(P.v0[m], 17.0) * 0.03)[:, None]
    else:
        rr = 0.085 * P.b.get("limbs", 1.0) * P.b.get("arm_girth", 1.0)
        zf = P.chestz - 0.06 * P.t
        yf = P.front(zf) - rr * 1.2
        for s, tag in ((1, "l"), (-1, "r")):
            sh = Vector((s * P.sx * 0.9, P.army - 0.04, P.armz + 0.1 * P.t))
            el = Vector((s * (P.sx + 0.1), P.army - 0.2 * P.t, zf - 0.02 * P.t))
            fore = Vector((-s * P.sx * 0.36, yf - (0.07 if s > 0 else 0.0), zf + s * 0.045 * P.t))
            P.add("arm2_upper_" + tag, g.tube(spline([sh, sh.lerp(el, 0.5) + Vector((s * 0.06, 0, 0.02)), el], 2), [rr * 1.25, rr * 1.3, rr * 1.2, rr * 1.1, rr], n=7), P.skin, "chest", smooth=True)
            P.add("arm2_fore_" + tag, g.tube([el, el.lerp(fore, 0.5) + Vector((0, -0.03, 0)), fore], [rr * 1.05, rr * 0.95, rr * 0.8], n=7), P.skin, "chest", smooth=True)
            P.add("arm2_elbow_" + tag, g.ico(el, rr * 1.12, sub=1), P.skin, "chest", smooth=True)
            P.add("arm2_hand_" + tag, g.ico(fore + Vector((-s * 0.07, 0.0, 0.0)), rr * 1.25 * P.b.get("hands", 1.0) ** 0.5, sub=1, scale=(1.25, 0.8, 0.9)), P.skin, "chest", smooth=True)
            P.add("arm2_band_" + tag, hoop(el.lerp(fore, 0.3), rr * 1.25, rr * 1.25, 0.022, u=Y, v=Z, n=8, sides=4), mat("accent"), "chest", smooth=False)


@slot("right", "coin-light", "cup")
@slot("left", "coin-light", "cup")
def held(P, size, word):
    """In a hand: a small light, offered; a cup that is somehow always full."""
    side = "l" if P._slot == "left" else "r"
    if P._style == "coin-light":
        c = Vector((0.0, -0.03, 0.2 * size))
        P.hold(side, "offer", [(g.ico(c, 0.085 * size, sub=1), field("offer", 3.2)),
                               (hoop(c, 0.13 * size, 0.13 * size, 0.014, u=X, v=Y, n=10, sides=3), mat("brass_gilt")),
                               (g.tube([Vector((0, 0, 0.02)), c + Vector((0, 0, -0.1 * size))], 0.012, n=3), mat("brass_gilt"))])
    else:
        s = size
        bowl = g.lathe([(0.025 * s, 0.1), (0.1 * s, 0.17), (0.14 * s, 0.3), (0.14 * s, 0.4), (0.125 * s, 0.4), (0.12 * s, 0.31), (0.02 * s, 0.2)], n=8, centre=(0, -0.01, -0.06))
        stem = g.lathe([(0.1 * s, -0.16), (0.03 * s, -0.12), (0.025 * s, 0.1)], n=6, centre=(0, -0.01, -0.06))
        P.hold(side, "cup", [(bowl, mat("brass_gilt")), (stem, mat("brass_gilt")), (disc((0, -0.01, 0.31), 0.118 * s, normal=Z, thick=0.02, n=8), field("wine", 2.0))])


@slot("left", "door-shield")
def held_door(P, size, word):
    """The door, come round onto its arm: barred across in iron, and bolted."""
    w = (2 * P.sx + 0.2) * size * 0.8
    h = (P.neckz - P.hipz) * 1.32 * size
    c = Vector((-0.3 * w, -0.26, 0.3 * h))
    items = door_leaf(c, w, h, 0.08 * P.t, "wood_door", bars=True)
    bolt = g.box(c + Vector((0.1 * w, -0.08 * P.t, 0.0)), (w * 0.5, 0.05 * P.t, 0.06 * P.t))
    P.hold("l", "doorshield", [(geo, P.material(m)) for geo, m in items] + [(bolt, mat("metal_iron_light"))])


# ======================================================================================
# What keeps it company
# ======================================================================================

@slot("around", "mouths")
def around_mouths(P, size, word):
    """Small mouths in the air about its head, each with an opinion."""
    hr = P.hr
    c = Vector((0, P.hcy, P.eye.z + 0.4 * hr))
    for i in range(5):
        a = math.pi * (0.05 + 0.9 * i / 4.0)             # an arc over it, from its right to its left
        q = c + Vector((math.cos(a) * 2.5 * hr, -0.3 * hr - 0.2 * hr * math.sin(a), math.sin(a) * 1.7 * hr + 0.25 * hr * (i % 2)))
        w = (0.34 + 0.08 * (i % 3)) * hr * size
        maw = g.ico(q, 1.0, sub=1, scale=(w, w * 0.34, w * (0.3 + 0.16 * (i % 2))))
        lips = [q + Vector((w * 1.08 * math.cos(b), -w * 0.16, w * (0.36 + 0.16 * (i % 2)) * math.sin(b))) for b in [2 * math.pi * k / 10 for k in range(11)]]
        teeth = None
        for k in range(4):
            t = -1.0 + 2.0 * (k + 0.5) / 4
            teeth = g.merge(teeth, g.box(q + Vector((t * w * 0.7, -w * 0.3, w * 0.14)), (w * 0.26, w * 0.1, w * 0.2)))
        P.rider("bob", "mouth", [(maw, "maw"), (g.tube(lips, [w * 0.13] * len(lips), n=4, caps=False), "main"), (teeth, "bone")], q, "chest", n=i)


@slot("around", "smoke-edges")
def around_smoke(P, size, word):
    """It is going to smoke at its edges: elbows, knees, the ends of things."""
    J = P.J
    spots = [(J["lowerarm.l"], "lowerarm.l", 0.13), (J["lowerarm.r"], "lowerarm.r", 0.13), (J["lowerleg.l"], "lowerleg.l", 0.14), (J["lowerleg.r"], "lowerleg.r", 0.14),
             (J["wrist.l"], "hand.l", 0.12), (J["wrist.r"], "hand.r", 0.12), (J["foot.l"], "foot.l", 0.15), (J["foot.r"], "foot.r", 0.15)]
    for i, (p, bone, r) in enumerate(spots):
        puffs = None
        for k in range(3):
            d = Vector((math.sin(i * 2.1 + k * 2.4), 0.6 * math.cos(i * 1.3 + k * 1.9), math.cos(i * 0.7 + k * 2.2) * 0.8)) * r * 0.9 * size
            puffs = g.merge(puffs, g.ico(Vector(p) + d, r * (0.8 - 0.14 * k) * size, sub=1))
        P.add("smoke_%d" % i, puffs, mat("shade") if i % 2 else mat("shade_edge"), bone, smooth=True)
    embers = None
    for i in range(7):
        p = Vector(spots[i % len(spots)][0]) + Vector((0.12 * math.sin(i * 1.9), 0.1 * math.cos(i * 2.3), 0.16 + 0.05 * (i % 3)))
        embers = g.merge(embers, g.ico(p, 0.022, sub=0))
    P.rider("bob", "embers", [(embers, field("ember", 3.0))], Vector((0, 0, P.hipz)), "hips", smooth=False)
