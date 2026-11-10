"""WILDLINE genius kit, the kinds of the thirteen homes: two First Forms for each home, the
young of something from that home's land, craft or working life (data/forms.json, `home`).
docs/genius-forms.md, "The kinds of the thirteen homes", says what each is and why.

Eleven are beasts on the wolf's rig (so the ages in data/genius-bodies.json shape them: the
young have large heads and short legs); two beasts are modelled (a carp, a crane); two are
small people; the rest are modelled things. Every body names its coat with the palette's
material names and its marking regions with mark(<region>), as the second set does.

genius_kit.py loads this file (register()).
"""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z

gk = None       # genius_kit, given by register()
f2 = None       # genius_forms2: hoop, band, collar_at
gr = None       # genius_relics: strap, loop, ringtube, _eye


def register(kit):
    global gk, f2, gr
    import genius_forms2
    import genius_relics
    gk, f2, gr = kit, genius_forms2, genius_relics
    kit.PALETTE.update({
        "mist": ((0.5, 0.52, 0.53), 0.95, 0.0), "mist_dark": ((0.26, 0.28, 0.31), 0.95, 0.0), "mist_pale": ((0.76, 0.77, 0.75), 0.9, 0.0),
        "water": ((0.2, 0.27, 0.24), 0.18, 0.0), "water_dark": ((0.11, 0.15, 0.15), 0.25, 0.0), "water_pale": ((0.5, 0.56, 0.5), 0.15, 0.0),
        "dust": ((0.52, 0.42, 0.29), 0.95, 0.0), "dust_dark": ((0.3, 0.23, 0.16), 0.95, 0.0), "dust_pale": ((0.74, 0.66, 0.5), 0.95, 0.0),
        "scale": ((0.5, 0.3, 0.12), 0.35, 0.0), "scale_pale": ((0.78, 0.72, 0.6), 0.35, 0.0), "fin": ((0.36, 0.2, 0.1), 0.5, 0.0),
        "plume": ((0.78, 0.77, 0.73), 0.85, 0.0), "plume_dark": ((0.07, 0.07, 0.08), 0.8, 0.0),
        "reed": ((0.3, 0.33, 0.16), 0.9, 0.0), "tin": ((0.42, 0.43, 0.44), 0.35, 0.8),
    })
    kit.BODIES.update({
        "beast-cat": cat_body, "beast-ringtail": raccoon_body, "beast-paddle": beaver_body, "beast-fox": fox_body,
        "beast-boar": boar_body, "beast-mastiff": mastiff_body, "beast-riverhorse": riverhorse_body, "beast-gazelle": gazelle_body,
        "beast-mongoose": mongoose_body, "beast-horse": horse_body, "beast-camel": camel_body, "beast-carp": carp_body, "beast-crane": crane_body,
        "engine-handcar": handcar_body, "engine-buoy": buoy_body, "engine-astrolabe": astrolabe_body,
        "relic-star": star_body, "relic-horn": horn_body, "relic-woodsword": woodsword_body,
        "aspect-fog": fog_body, "aspect-flood": flood_body, "aspect-whirl": whirl_body,
        "kith-fitter": fitter_body, "kith-clerk": clerk_body, "daemon-vigil": vigil_body, "daemon-marginal": marginal_body,
    })
    kit.CARD_ZOOM.update({"crane": 1.1, "carp": 1.2})


# ======================================================================================
# Beasts on the wolf's rig
# ======================================================================================

def _beast(shape, extra=None, rough=(0.92, 0.9), marks=("socks", "mask", "saddle", "tailtip"), tail=True, hooves=False, sockets=None):
    """The wolf, reshaped by shape(bk, r), in the fur's two materials (so every coat of its
    palette paints it), with whatever extra(bk, r) hangs on it."""
    bk, r = gk._wolf()
    shape(bk, r)
    c = gk.PALETTE
    r.recolor("Main", "fur_dark", c["fur_dark"][0], rough=rough[0])
    r.recolor("Main_Light", "fur_light", c["fur_light"][0], rough=rough[1])
    r.recolor("Eyes_Black", "field_eyes", (0.03, 0.03, 0.03), rough=0.3, emission=(1, 1, 1), strength=3.0)
    r.recolor("Nose", "nose", c["nose"][0], rough=0.5)
    gk._flat(r)
    if extra:
        extra(bk, r)
    if hooves:
        gk._hooves(r, gk.mat("horn"))
    return gk._finish_wolf(r, sockets(r) if sockets else None, coat=("fur_dark", "fur_light"), marks=marks, tail=tail)


def _head(r):
    return r.family("Head", "Ear1.L", "Ear1.R")


def _ears(r, s):
    for ear in ("Ear1.L", "Ear1.R"):
        r.scale(r.family(ear), r.bone(ear), s)


def _whiskers(r, reach=0.38):
    nose = gk._nose(r)
    wh = None
    for s in (1, -1):
        for dz, dy in ((0.1, 0.1), (0.0, 0.16), (-0.1, 0.1)):
            base = Vector((s * 0.14, nose.y + 0.2, nose.z - 0.04 + dz * 0.4))
            wh = g.merge(wh, g.tube([base, base + Vector((s * reach, dy, dz))], [0.013, 0.004], n=3))
    gk._add(r, "whiskers", wh, "Head", gk.mat("whisker"))


def _tail(r):
    return r.family("Tail1")


def _tail_girth(r, s):
    tail = _tail(r)
    tz = sum(r.bone(b).z for b in tail) / len(tail)
    r.scale(tail, (0, 0, tz), s)


def cat_body():
    """The station cat: small, round-headed, big-eared, a long tail carried up; whiskers."""
    def shape(bk, r):
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (0.84, 1.0, 0.84))
        r.leg_length(0.22)
        r.leg_girth(0.8)
        r.scale(_head(r), r.bone("Neck3"), (1.18, 0.72, 1.08))
        _ears(r, (1.25, 1.0, 1.35))
        r.lengthen_chain(_tail(r), [], 1.3)
        _tail_girth(r, (0.6, 1.0, 0.6))
        r.rotate(_tail(r), r.bone("Tail1"), X, math.radians(35))
    return _beast(shape, lambda bk, r: _whiskers(r))


def raccoon_body():
    """The ring-tail: stout and low, a broad masked face, small round ears, a thick tail in
    rings."""
    def shape(bk, r):
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (1.14, 1.0, 1.06))
        r.leg_length(0.5)
        r.leg_girth(1.15)
        r.scale(_head(r), r.bone("Neck3"), (1.22, 0.84, 1.0))
        _ears(r, (0.75, 0.7, 0.6))
        _tail_girth(r, (1.9, 1.0, 1.9))

    def extra(bk, r):
        ring = gk.mark("rings", gk.mat("fur_dark"))
        for b in ("Tail2", "Tail4", "Tail6"):
            p = r.bone(b)
            gk._add(r, "ring_" + b, f2.band(p, 0.17, 0.17, 0.05, n=10, sides=4), b, ring)
        _whiskers(r, 0.3)
    return _beast(shape, extra, marks=("socks", "mask", "saddle"))


def beaver_body():
    """The beaver: round and low, a blunt head with small ears, two long teeth, a broad flat
    tail."""
    def shape(bk, r):
        r.scale(r.body_bones(), (0, 0, 1.25), (1.2, 1.0, 0.92))
        r.leg_length(0.7)
        r.leg_girth(1.25)
        r.scale(_head(r), r.bone("Neck3"), (1.2, 0.8, 1.02))
        r.scale(bk.NECK, r.bone("Neck1"), (1.25, 1.0, 1.2))
        _ears(r, 0.35)
        _tail_girth(r, (2.9, 1.0, 0.32))
        r.rotate(_tail(r), r.bone("Tail1"), X, math.radians(-22))
        r.damp_rotations(_tail(r), 0.4)

    def extra(bk, r):
        nose = gk._nose(r)
        teeth = None
        for s in (1, -1):
            teeth = g.merge(teeth, g.box((s * 0.035, nose.y + 0.1, nose.z - 0.17), (0.055, 0.03, 0.13)))
        gk._add(r, "teeth", teeth, "Head", gk.mat("beak"))
        _whiskers(r, 0.26)
    return _beast(shape, extra, rough=(0.4, 0.5), marks=("socks", "mask", "saddle"))


def fox_body():
    """The dock fox: slight and quick, a narrow muzzle, tall ears, a brush as big as the
    rest of it."""
    def shape(bk, r):
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (0.8, 1.0, 0.82))
        r.leg_girth(0.7)
        r.leg_length(0.12)
        r.scale(_head(r), r.bone("Neck3"), (0.9, 1.08, 0.92))
        _ears(r, (1.1, 1.0, 1.75))
        r.lengthen_chain(_tail(r), [], 1.22)
        _tail_girth(r, (1.75, 1.0, 1.75))
        r.rotate(_tail(r), r.bone("Tail1"), X, math.radians(-18))
    return _beast(shape, lambda bk, r: _whiskers(r, 0.3))


def boar_body():
    """The boar: all shoulder, a long wedge of a head carried low, a ridge of bristle down
    the back, tusks."""
    def shape(bk, r):
        r.scale([], (0, 0, 0), (1.18, 0.96, 1.0), spatial=True)
        r.leg_length(0.42)
        r.leg_girth(1.25)
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (1.05, 1.0, 1.22))
        r.lengthen_chain(bk.NECK, _head(r), 0.74)
        r.scale(bk.NECK, r.bone("Neck1"), (1.4, 1.0, 1.3))
        r.rotate(bk.NECK + _head(r), r.bone("Neck1"), X, math.radians(12))
        r.scale(_head(r), r.bone("Neck3"), (1.05, 1.22, 1.05))
        _ears(r, (0.9, 0.9, 0.75))
        r.scale(_tail(r), r.bone("Tail1"), 0.34)

    def extra(bk, r):
        r.fin("bristles", r.bone("Neck2").y, r.bone("Back").y, 0.2, gk.mat("fur_ruff"), thickness=0.1, steps=16, sink=0.06, serrate=True)
        nose = gk._nose(r)
        tusks = None
        for s in (1, -1):
            base = Vector((s * 0.13, nose.y + 0.2, nose.z - 0.1))
            tusks = g.merge(tusks, g.tube([base, base + Vector((s * 0.07, -0.03, 0.1)), base + Vector((s * 0.09, 0.02, 0.24))], [0.04, 0.032, 0.006], n=5))
        gk._add(r, "tusks", tusks, "Head", gk.mat("bone"))
    return _beast(shape, extra, marks=("socks", "saddle"), tail=False, hooves=True)


def mastiff_body():
    """The wall-mastiff: a big square dog, deep in the chest, a heavy head, ears that hang."""
    def shape(bk, r):
        r.scale([], (0, 0, 0), (1.2, 1.0, 1.04), spatial=True)
        r.leg_girth(1.34)
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (1.0, 1.0, 1.16))
        r.scale(bk.NECK, r.bone("Neck1"), (1.35, 1.0, 1.25))
        r.scale(_head(r), r.bone("Neck3"), (1.28, 0.9, 1.18))
        for ear, sg in (("Ear1.L", 1), ("Ear1.R", -1)):
            r.scale(r.family(ear), r.bone(ear), (1.0, 0.9, 0.9))
            r.rotate(r.family(ear), r.bone(ear), Y, sg * math.radians(100))
            r.shift(r.family(ear), (0, 0.04, -0.1))
        _tail_girth(r, (0.75, 1.0, 0.75))
    return _beast(shape)


def riverhorse_body():
    """The river-horse: a barrel on four posts, hardly a neck, a muzzle as wide as its head,
    ears and tail too small for it."""
    def shape(bk, r):
        r.scale([], (0, 0, 0), (1.42, 1.0, 1.0), spatial=True)
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (1.0, 1.0, 1.3))
        r.leg_length(0.72)
        r.leg_girth(1.6)
        r.lengthen_chain(bk.NECK, _head(r), 0.62)
        r.scale(bk.NECK, r.bone("Neck1"), (1.5, 1.0, 1.4))
        r.scale(_head(r), r.bone("Neck3"), (1.35, 1.12, 1.18))
        _ears(r, 0.32)
        r.scale(_tail(r), r.bone("Tail1"), 0.26)

    def extra(bk, r):
        nose = gk._nose(r)
        r.shell("muzzle", (0, nose.y + 0.2, nose.z - 0.02), (0.36, 0.3, 0.22), "Head", gk.mat("fur_light"), segments=8, rings=3)
        pegs = None
        for s in (1, -1):
            pegs = g.merge(pegs, g.cone((s * 0.2, nose.y + 0.16, nose.z - 0.14), (s * 0.22, nose.y + 0.12, nose.z + 0.02), 0.04, n=5))
        gk._add(r, "pegs", pegs, "Head", gk.mat("bone"))
    return _beast(shape, extra, rough=(0.45, 0.5), marks=("socks", "saddle"), tail=False)


def gazelle_body():
    """The gazelle: all leg and neck, a small fine head held high, long ears, ringed horns
    that lean back and out."""
    def shape(bk, r):
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (0.76, 1.0, 0.84))
        r.leg_length(-0.5)
        r.leg_girth(0.58)
        r.lengthen_chain(bk.NECK, _head(r), 1.3)
        r.scale(bk.NECK, r.bone("Neck1"), (0.8, 1.0, 0.8))
        r.rotate(bk.NECK + _head(r), r.bone("Neck1"), X, math.radians(-26))
        r.rotate(_head(r), r.bone("Neck3"), X, math.radians(22))
        r.scale(_head(r), r.bone("Neck3"), (0.86, 0.96, 0.9))
        _ears(r, (1.0, 1.0, 1.5))
        r.scale(_tail(r), r.bone("Tail1"), 0.4)

    def extra(bk, r):
        hb = r.bone("Head")
        crown = r.top(hb.y + 0.06, half_width=0.25)
        horns, rings = None, None
        for s in (1, -1):
            pts = [Vector((s * 0.09, hb.y + 0.08, crown - 0.04)), Vector((s * 0.15, hb.y + 0.2, crown + 0.3)), Vector((s * 0.2, hb.y + 0.42, crown + 0.58)), Vector((s * 0.15, hb.y + 0.5, crown + 0.82))]
            horns = g.merge(horns, g.tube(pts, [0.055, 0.045, 0.03, 0.006], n=6))
            for k in range(5):
                p = pts[0].lerp(pts[2], (k + 0.6) / 5.6)
                rings = g.merge(rings, g.ico(p, 0.058 - 0.004 * k, sub=0, scale=(1, 1, 0.35)))
        gk._add(r, "horns", horns, "Head", gk.mat("horn"))
        gk._add(r, "horn_rings", rings, "Head", gk.mat("horn_ridge"))
    return _beast(shape, extra, marks=("socks", "mask", "saddle"), tail=False, hooves=True)


def mongoose_body():
    """The mongoose: long and low, a pointed face, small ears, a tail as long as its body
    that tapers from a thick root."""
    def shape(bk, r):
        r.scale(r.body_bones(), (0, 0, 1.25), (0.96, 1.0, 0.8))
        r.stretch_y(-0.6, 0.4, 1.32)
        r.leg_length(0.66)
        r.leg_girth(0.9)
        r.scale(_head(r), r.bone("Neck3"), (0.92, 1.02, 0.9))
        _ears(r, 0.42)
        r.lengthen_chain(_tail(r), [], 1.45)
        _tail_girth(r, (1.5, 1.0, 1.5))
        r.scale(r.family("Tail5"), r.bone("Tail5"), (0.55, 1.0, 0.55))
        r.damp_rotations(_tail(r), 0.5)
    return _beast(shape, lambda bk, r: _whiskers(r, 0.24), marks=("socks", "saddle", "tailtip"))


def _mane(r, bones, long=0.3, lean=0.5):
    geo = None
    for b in bones:
        p = r.bone(b)
        top = r.top(p.y, half_width=0.1)
        for k, dy in enumerate((-0.1, 0.0, 0.1)):
            base = Vector((0, p.y + dy, max(top, p.z) - 0.04))
            geo = g.merge(geo, g.blade(base, base + Vector((0.03 * (k - 1), long * lean, long)), 0.28, normal=(1, 0, 0), belly=0.45))
    gk._add(r, "mane", geo, bones[len(bones) // 2], gk.mat("fur_ruff"))


def horse_body():
    """The steppe horse: short, deep-chested and tough, a long head on a strong neck, a
    stiff mane, a tail that hangs to the hocks."""
    def shape(bk, r):
        r.leg_length(-0.55)
        r.leg_girth(0.86)
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (1.0, 1.0, 1.12))
        r.lengthen_chain(bk.NECK, _head(r), 1.5)
        r.scale(bk.NECK, r.bone("Neck1"), (1.05, 1.0, 1.25))
        r.rotate(bk.NECK + _head(r), r.bone("Neck1"), X, math.radians(-34))
        r.rotate(_head(r), r.bone("Neck3"), X, math.radians(40))
        r.scale_along(_head(r), r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.4)
        r.scale(_head(r), r.bone("Neck3"), (0.86, 1.0, 1.0))
        _ears(r, (0.7, 0.8, 1.0))
        r.lengthen_chain(_tail(r), [], 1.25)
        _tail_girth(r, (1.3, 1.0, 1.3))
        r.rotate(_tail(r), r.bone("Tail1"), X, math.radians(-68))
        r.damp_rotations(_tail(r), 0.35)

    def extra(bk, r):
        _mane(r, ["Neck1", "Neck2", "Neck3", "Head"], long=0.34, lean=0.7)
        gk._paint(r, _tail(r), gk.mat("fur_ruff"))
    return _beast(shape, extra, marks=("socks", "mask", "saddle"), tail=False, hooves=True)


def camel_body():
    """The camel: a long way up. Long legs, a hump, a long neck curved up to a small proud
    head, heavy lids."""
    def shape(bk, r):
        r.leg_length(-0.72)
        r.leg_girth(0.8)
        r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (0.92, 1.0, 1.08))
        r.lengthen_chain(bk.NECK, _head(r), 1.85)
        r.scale(bk.NECK, r.bone("Neck1"), (0.9, 1.0, 0.95))
        r.rotate(bk.NECK + _head(r), r.bone("Neck1"), X, math.radians(-48))
        r.rotate(_head(r), r.bone("Neck3"), X, math.radians(50))
        r.scale(_head(r), r.bone("Neck3"), (0.88, 1.05, 0.9))
        _ears(r, 0.5)
        _tail_girth(r, (0.5, 1.0, 0.5))
        r.rotate(_tail(r), r.bone("Tail1"), X, math.radians(-62))
        r.damp_rotations(_tail(r), 0.3)

    def extra(bk, r):
        y = (r.bone("Torso2").y + r.bone("Torso").y) / 2
        top = r.top(y)
        r.shell("hump", (0, y, top + 0.02), (0.36, 0.52, 0.5), "Torso2", gk.mat("fur_dark"), segments=8, rings=4)
        r.shell("hump_tuft", (0, y, top + 0.24), (0.22, 0.32, 0.2), "Torso2", gk.mat("fur_ruff"), segments=6, rings=3)
    return _beast(shape, extra, marks=("socks", "saddle"), tail=False)


# ======================================================================================
# Beasts that are modelled: a carp, a crane
# ======================================================================================

def _table(top, front, mid, half=0.12, extra=None):
    """The usual sockets of a thing with no rig: its top, its front (a y, negative), its
    middle height, its half-width."""
    t = {"socket_head": [(0, 0, top)], "socket_eyes": [(0, front, mid + 0.06)], "socket_mouth": [(0, front, mid)], "socket_grip": [(half + 0.04, front * 0.5, mid)],
         "socket_throat": [(0, front, mid - 0.06)], "socket_light": [(0, 0, mid)], "socket_back": [(0, -front, mid + 0.04)], "socket_body": [(0, front, mid - 0.1)],
         "socket_tail": [(0, -front, mid - 0.1)], "socket_arm_l": [(half, 0, mid)], "socket_arm_r": [(-half, 0, mid)],
         "socket_limb_fl": [(half * 0.6, front * 0.6, mid - 0.2)], "socket_limb_fr": [(-half * 0.6, front * 0.6, mid - 0.2)], "socket_keepsake": [(0, front, mid - 0.14)]}
    t.update(extra or {})
    return gk._sockets(t)


def carp_body():
    """The carp: a deep golden fish that swims in the air at your shoulder. Barbels, a fan of
    a tail, patches on its back; its side fins beat."""
    sc, pale, fin = gk.mat("scale"), gk.mat("scale_pale"), gk.mat("fin")
    zc = 0.42
    prof = [(-0.3, 0.012, 0.02), (-0.27, 0.05, 0.06), (-0.18, 0.085, 0.115), (-0.05, 0.095, 0.14), (0.1, 0.075, 0.115), (0.22, 0.04, 0.065), (0.29, 0.018, 0.035)]
    body = g.loft([g.ring((0, y, zc + 0.01 * math.sin(y * 9)), w, h, n=10, u=X, v=Z) for y, w, h in prof])
    items = [(body, sc)]
    items.append((g.loft([g.ring((0, y, zc - h * 0.55), w * 0.8, h * 0.5, n=8, u=X, v=Z) for y, w, h in prof[1:6]]), pale))
    # patches on the back and the head
    patch = None
    for y, x, r_ in ((-0.2, 0.02, 0.055), (-0.04, -0.03, 0.075), (0.11, 0.03, 0.055)):
        patch = g.merge(patch, g.ico((x, y, zc + 0.115), r_, sub=1, scale=(1.2, 1.4, 0.35)))
    items.append((patch, gk.mark("patches", sc)))
    # tail: a fan of five; dorsal and belly fins
    tail = None
    for i in range(5):
        a = math.radians(-44 + 22 * i)
        tail = g.merge(tail, g.blade((0, 0.28, zc), (0, 0.28 + 0.2 * math.cos(a), zc + 0.24 * math.sin(a)), 0.11, normal=(1, 0, 0), belly=0.6, thick=0.008))
    items.append((tail, fin))
    items.append((g.tongue([(0, -0.14, zc + 0.12), (0, -0.02, zc + 0.24), (0, 0.14, zc + 0.11)], [0.02, 0.16, 0.02], thick=0.12, normal=(1, 0, 0)), fin))
    items.append((g.blade((0, 0.1, zc - 0.1), (0, 0.2, zc - 0.2), 0.08, normal=(1, 0, 0), thick=0.008), gk.mark("tips", fin)))
    barb, eyes = None, None
    for s in (1, -1):
        barb = g.merge(barb, g.tube([(s * 0.03, -0.29, zc - 0.03), (s * 0.07, -0.33, zc - 0.07), (s * 0.08, -0.31, zc - 0.13)], [0.008, 0.006, 0.002], n=4))
        eyes = g.merge(eyes, g.ico((s * 0.052, -0.25, zc + 0.03), 0.018, sub=1, scale=(0.5, 1, 1)))
    items += [(barb, pale), (eyes, gk.field("eyes", 3.0))]
    items.append((f2.band((0, -0.17, zc), 0.088, 0.118, 0.006, n=12, sides=3), gk.field("seam", 1.6)))
    ob = g.pieces("carp_body", items)
    gk.shape_key(ob, "heavy", lambda p, i: Vector((p.x * 1.2, p.y, zc + (p.z - zc) * 1.15)) if abs(p.y) < 0.24 else None)
    gk.shape_key(ob, "lean", lambda p, i: Vector((p.x * 0.82, p.y, zc + (p.z - zc) * 0.9)) if abs(p.y) < 0.24 else None)
    wings = []
    for tag, s in (("l", 1), ("r", -1)):
        sh = Vector((s * 0.085, -0.13, zc - 0.03))
        w = g.pieces("wing_" + tag, [(g.blade(sh, sh + Vector((s * 0.16, 0.1, -0.06)), 0.1, normal=(0, 0, 1), belly=0.6, thick=0.008), fin)])
        gk.set_origin(w, sh)
        wings.append(w)
    socks = _table(zc + 0.2, -0.3, zc, 0.1, {"socket_tail": [(0, 0.28, zc)], "socket_back": [(0, 0.0, zc + 0.15)], "socket_keepsake": [(0, -0.16, zc - 0.13)],
                                             "socket_collar": f2.collar_at((0, -0.2, zc), 0.08, 0.11)})
    return gk.Built([ob] + wings, socks)


def crane_body():
    """The crane: tall on stilts, a long neck in an S, a spear of a bill, a dark fall of
    plumes over its tail, a cap of red skin left bare; its wings beat slow."""
    wh, dark = gk.mat("plume"), gk.mat("plume_dark")
    bz = 0.4
    items = [(g.ico((0, 0.02, bz), 0.12, sub=2, scale=(0.72, 1.35, 0.8), rot=(math.radians(-14), 0, 0)), wh)]
    neck = [(0, -0.12, bz + 0.04), (0, -0.2, bz + 0.12), (0, -0.16, bz + 0.2), (0, -0.14, bz + 0.27), (0, -0.2, bz + 0.31)]
    items.append((g.tube(neck, [0.045, 0.03, 0.024, 0.022, 0.026], n=7), wh))
    items.append((g.tube(neck[1:4], [0.031, 0.025, 0.023], n=7, caps=False), gk.mark("throat", wh)))
    items.append((g.ico((0, -0.215, bz + 0.315), 0.034, sub=1, scale=(0.85, 1.3, 0.9)), wh))
    items.append((g.ico((0, -0.21, bz + 0.343), 0.022, sub=0, scale=(1, 1.2, 0.4)), gk.mark("crown", wh)))
    items.append((g.tube([(0, -0.25, bz + 0.31), (0, -0.38, bz + 0.29)], [0.014, 0.002], n=5), gk.mat("beak")))
    eyes = None
    for s in (1, -1):
        eyes = g.merge(eyes, g.ico((s * 0.026, -0.235, bz + 0.322), 0.008, sub=0))
    items.append((eyes, gk.field("eyes", 3.0)))
    plumes = None
    for i in range(6):
        a = math.radians(-30 + 12 * i)
        plumes = g.merge(plumes, g.blade((math.sin(a) * 0.03, 0.14, bz + 0.05), (math.sin(a) * 0.12, 0.3, bz - 0.06 - 0.02 * abs(i - 2.5)), 0.07, normal=(0, 0, 1), belly=0.55, curl=-0.12))
    items.append((plumes, dark))
    for s in (1, -1):
        hip, knee, foot = Vector((s * 0.04, 0.03, bz - 0.07)), Vector((s * 0.045, 0.06, 0.2)), Vector((s * 0.045, 0.02, 0.012))
        items.append((g.tube([hip, knee, foot], [0.02, 0.011, 0.009], n=5), dark))
        toes = None
        for dx, dy in ((-0.03, -0.06), (0.0, -0.075), (0.03, -0.06), (0.0, 0.03)):
            toes = g.merge(toes, g.tube([foot, foot + Vector((dx, dy, -0.008))], [0.008, 0.004], n=4))
        items.append((toes, dark))
    # the wings folded along its sides (a crane on the ground does not beat them): long
    # feathers lying back from the shoulder, the last of them dark
    for s in (1, -1):
        sh = Vector((s * 0.085, -0.07, bz + 0.06))
        fe, tips = None, None
        for i in range(7):
            t = i / 6.0
            base = sh + Vector((s * 0.012 * math.sin(t * math.pi), 0.03 * i, -0.012 * i))
            L = 0.16 + 0.05 * math.sin(t * math.pi)
            fe = g.merge(fe, g.blade(base, base + Vector((s * 0.01, L, -0.035)), 0.075, normal=(s, 0, 0.35), belly=0.5, thick=0.008))
            if i > 3:
                tips = g.merge(tips, g.blade(base + Vector((s * 0.012, L * 0.6, -0.02)), base + Vector((s * 0.014, L * 1.2, -0.05)), 0.06, normal=(s, 0, 0.35), belly=0.5, thick=0.008))
        items += [(fe, wh), (tips, gk.mark("tips", dark)), (g.ico(sh + Vector((0, 0.02, 0)), 0.035, sub=1, scale=(0.6, 1.5, 1.0)), wh)]
    ob = g.pieces("crane_body", items)
    wings = []
    socks = _table(bz + 0.37, -0.25, bz + 0.3, 0.1, {
        "socket_head": [(0, -0.21, bz + 0.36), Matrix.Scale(0.45, 3)], "socket_eyes": [(0, -0.25, bz + 0.325), Matrix.Scale(0.45, 3)], "socket_mouth": [(0, -0.27, bz + 0.305), Matrix.Scale(0.45, 3)],
        "socket_throat": [(0, -0.21, bz + 0.12)], "socket_light": [(0, -0.13, bz)], "socket_back": [(0, 0.0, bz + 0.1)], "socket_body": [(0, -0.1, bz - 0.04)],
        "socket_tail": [(0, 0.16, bz + 0.04)], "socket_limb_fl": [(0.045, -0.03, 0.03)], "socket_limb_fr": [(-0.045, -0.03, 0.03)], "socket_keepsake": [(0, -0.18, bz + 0.1)],
        "socket_collar": f2.collar_at((0, -0.17, bz + 0.2), 0.026, 0.026, tilt=0.2)})
    return gk.Built([ob] + wings, socks)


# ======================================================================================
# Engines
# ======================================================================================

def handcar_body():
    """The handcar: a pump-trolley of the line, the size of a dog. A plank deck on four iron
    wheels, the rocking beam and its handles, a lamp on a post at the front."""
    iron, lite, brass, wood = gk.mat("metal_iron"), gk.mat("metal_iron_light"), gk.mat("metal_brass"), gk.mat("wood")
    items = [(g.box((0, 0, 0.2), (0.34, 0.56, 0.035)), wood), (g.box((0, 0, 0.172), (0.26, 0.6, 0.03)), iron)]
    items.append((g.merge(g.box((0.172, 0, 0.2), (0.012, 0.56, 0.05)), g.box((-0.172, 0, 0.2), (0.012, 0.56, 0.05))), gk.mark("band", lite)))
    wheels, hubs = None, None
    for y in (-0.19, 0.19):
        items.append((g.tube([(-0.2, y, 0.1), (0.2, y, 0.1)], [0.016, 0.016], n=6), lite))
        for s in (1, -1):
            wheels = g.merge(wheels, g.moved(g.lathe([(0.0, -0.012), (0.1, -0.012), (0.108, 0.0), (0.1, 0.012), (0.0, 0.012)], n=12), Matrix.Translation((s * 0.2, y, 0.1)) @ Matrix.Rotation(math.pi / 2, 4, "Y")))
            hubs = g.merge(hubs, g.ico((s * 0.216, y, 0.1), 0.026, sub=0, scale=(0.5, 1, 1)))
    items += [(wheels, iron), (hubs, brass)]
    # the pump: a column, the beam across it, a handle at each end
    items.append((g.merge(g.box((0, 0, 0.33), (0.07, 0.07, 0.24)), g.box((0, 0, 0.45), (0.1, 0.05, 0.03))), iron))
    beam = Matrix.Rotation(math.radians(14), 4, "X")
    items.append((g.moved(g.box((0, 0, 0), (0.035, 0.6, 0.035)), Matrix.Translation((0, 0, 0.47)) @ beam), lite))
    for s in (1, -1):
        p = Matrix.Translation((0, 0, 0.47)) @ beam @ Vector((0, s * 0.3, 0))
        items.append((g.tube([p - X * 0.14, p + X * 0.14], [0.016, 0.016], n=6), wood))
    items.append((g.merge(g.box((0.03, 0.02, 0.37), (0.02, 0.14, 0.02)), g.ico((0.045, 0.0, 0.3), 0.045, sub=0, scale=(0.4, 1, 1))), gk.mat("metal_brass")))
    # the lamp, and a tail-lamp of the field
    items.append((g.tube([(0, -0.26, 0.2), (0, -0.27, 0.4)], [0.012, 0.012], n=5), iron))
    items.append((g.lathe([(0.02, 0.4), (0.05, 0.41), (0.05, 0.5), (0.03, 0.53), (0.0, 0.55)], n=6, centre=(0, -0.27, 0)), brass))
    items.append((g.ico((0, -0.3, 0.455), 0.036, sub=1, scale=(1, 0.6, 1)), gk.field("core", 4.0)))
    items.append((g.ico((0, 0.285, 0.21), 0.022, sub=0), gk.field("eyes", 2.5)))
    ob = g.pieces("handcar_body", items)
    socks = _table(0.56, -0.3, 0.3, 0.2, {"socket_light": [(0, -0.3, 0.455)], "socket_back": [(0, 0.12, 0.23)], "socket_body": [(0, -0.2, 0.23)],
                                          "socket_limb_fl": [(0.2, -0.19, 0.1)], "socket_limb_fr": [(-0.2, -0.19, 0.1)], "socket_limb_bl": [(0.2, 0.19, 0.1)], "socket_limb_br": [(-0.2, 0.19, 0.1)],
                                          "socket_keepsake": [(0, -0.27, 0.36)]})
    return gk.Built([ob], socks)


def buoy_body():
    """The bell-buoy: a float in a painted band, a cage of four struts, a bell hung in it and
    a light on top; a length of chain trails under it where the river was."""
    iron, lite, brass = gk.mat("metal_iron"), gk.mat("metal_iron_light"), gk.mat("metal_brass")
    items = [(g.lathe([(0.0, 0.14), (0.1, 0.17), (0.2, 0.26), (0.2, 0.32), (0.14, 0.36), (0.0, 0.36)], n=10), iron)]
    items.append((g.lathe([(0.203, 0.27), (0.203, 0.315)], n=10, caps=False), gk.mark("band", lite)))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        items.append((g.tube([(0.15 * math.cos(a), 0.15 * math.sin(a), 0.35), (0.05 * math.cos(a), 0.05 * math.sin(a), 0.66)], [0.012, 0.01], n=4), lite))
    items.append((f2.band((0, 0, 0.5), 0.1, 0.1, 0.008, n=10, v=Y, sides=3), lite))
    items.append((g.lathe([(0.012, 0.56), (0.03, 0.55), (0.05, 0.5), (0.07, 0.44), (0.078, 0.42), (0.07, 0.42)], n=10), brass))
    items.append((g.ico((0, 0, 0.43), 0.018, sub=0), iron))
    items.append((g.lathe([(0.04, 0.66), (0.04, 0.68), (0.02, 0.7)], n=6), iron))
    items.append((g.ico((0, 0, 0.73), 0.04, sub=1), gk.field("core", 4.5)))
    chain = None
    for k in range(6):
        c = Vector((0.012 * math.sin(k * 1.3), 0.012 * math.cos(k * 1.7), 0.12 - 0.022 * k))
        chain = g.merge(chain, f2.band(c, 0.014, 0.02, 0.005, n=6, u=(X if k % 2 else Y), sides=3))
    items.append((chain, lite))
    items.append((f2.band((0, 0, 0.2), 0.135, 0.135, 0.006, n=12, v=Y, sides=3), gk.field("seam", 1.6)))
    ob = g.pieces("buoy_body", items)
    return gk.Built([ob], _table(0.78, -0.2, 0.3, 0.2, {"socket_light": [(0, 0, 0.73)], "socket_keepsake": [(0, -0.14, 0.4)]}))


def astrolabe_body():
    """The astrolabe: a brass disc that stands on its edge and turns to look at you. A fretted
    plate over it, a rule across, a ring to hang it by; where the pin goes through, an eye."""
    brass, dark, lite = gk.mat("metal_brass"), gk.mat("metal_dark"), gk.mat("metal_iron_light")
    zc, R = 0.4, 0.22
    spin = Matrix.Translation((0, 0, zc)) @ Matrix.Rotation(math.pi / 2, 4, "X")
    items = [(g.moved(g.lathe([(0.0, -0.014), (R, -0.014), (R, 0.014), (0.0, 0.014)], n=20), spin), brass)]
    items.append((g.moved(g.lathe([(R * 0.86, 0.016), (R, 0.016), (R, 0.022), (R * 0.86, 0.022)], n=20, caps=False), Matrix.Translation((0, -0.036, zc)) @ Matrix.Rotation(math.pi / 2, 4, "X")), gk.mark("enamel", dark)))
    ticks = None
    for k in range(24):
        a = 2 * math.pi * k / 24
        ticks = g.merge(ticks, g.box((R * 0.93 * math.cos(a), -0.024, zc + R * 0.93 * math.sin(a)), (0.008, 0.006, 0.03 if k % 6 else 0.05), rot=(0, -a + math.pi / 2, 0)))
    items.append((ticks, lite))
    # the fretted plate: two off-centre rings and three pointers
    for cx, cz, rr in ((0.0, 0.03, 0.15), (0.03, -0.05, 0.09)):
        items.append((f2.band((cx, -0.022, zc + cz), rr, rr, 0.007, n=16, sides=3), lite))
    for a in (0.5, 2.3, 4.2):
        items.append((g.blade((0.05 * math.cos(a), -0.024, zc + 0.05 * math.sin(a)), (0.17 * math.cos(a), -0.024, zc + 0.17 * math.sin(a)), 0.03, normal=(0, -1, 0), thick=0.004), lite))
    items.append((g.box((0, -0.034, zc), (0.42, 0.006, 0.026), rot=(0, math.radians(24), 0)), dark))
    items += gr._eye((0, -0.04, zc), 0.032, lids=brass)
    items.append((g.box((0, 0, zc + R + 0.012), (0.05, 0.02, 0.03)), brass))
    items.append((f2.band((0, 0, zc + R + 0.055), 0.03, 0.03, 0.007, n=10, sides=4), brass))
    items.append((f2.band((0, 0.016, zc), R * 0.6, R * 0.6, 0.005, n=16, sides=3), gk.field("seam", 1.6)))
    ob = g.pieces("astrolabe_body", items)
    return gk.Built([ob], _table(zc + R + 0.09, -0.05, zc, R, {"socket_keepsake": [(0, -0.02, zc - R - 0.02)], "socket_back": [(0, 0.03, zc)]}))


# ======================================================================================
# Relics
# ======================================================================================

def star_body():
    """The tin star: a marshal's badge that nobody is wearing. Five points, a ring round
    them, a pin behind; in the boss an eye that opens."""
    tin, brass, dark = gk.mat("tin"), gk.mat("metal_brass"), gk.mat("metal_dark")
    zc, R = 0.42, 0.2
    items = []
    star = None
    for k in range(5):
        a = math.pi / 2 + 2 * math.pi * k / 5
        star = g.merge(star, g.blade((0, 0, zc), (R * math.cos(a), 0, zc + R * math.sin(a)), 0.15, normal=(0, -1, 0), belly=0.36, thick=0.02))
        items.append((g.ico((R * 1.03 * math.cos(a), -0.004, zc + R * 1.03 * math.sin(a)), 0.02, sub=0), brass))
    items.append((star, tin))
    items.append((f2.band((0, 0.004, zc), R * 0.7, R * 0.7, 0.012, n=20, sides=4), gk.mark("ring", tin)))
    items.append((g.moved(g.lathe([(0.0, -0.02), (0.07, -0.016), (0.075, 0.0), (0.0, 0.0)], n=12), Matrix.Translation((0, 0, zc)) @ Matrix.Rotation(-math.pi / 2, 4, "X")), dark))
    items += gr._eye((0, -0.024, zc), 0.042, lids=tin)
    items.append((g.tube([(-0.09, 0.02, zc + 0.02), (0.1, 0.022, zc - 0.01)], [0.006, 0.002], n=4), brass))
    items.append((f2.band((0, 0.008, zc), R * 0.7, R * 0.7, 0.005, n=20, sides=3), gk.field("pulse", 1.8)))
    ob = g.pieces("star_body", items)
    return gk.Built([ob], _table(zc + R + 0.03, -0.03, zc, R, {"socket_keepsake": [(0, -0.01, zc - R * 0.85)]}))


def horn_body():
    """The signal-horn: a great curve of brass, round on itself like a G, a bar of wood across
    to carry it by; the note sits in the bell as a light."""
    brass, lite, wood = gk.mat("metal_brass"), gk.mat("metal_iron_light"), gk.mat("wood")
    zc = 0.42
    pts, rad = [], []
    for i in range(22):
        t = i / 21.0
        a = math.radians(-70 + 300 * t)
        rr = 0.25 - 0.03 * t
        pts.append(Vector((rr * math.cos(a), 0.05 * (t - 0.5), zc + rr * math.sin(a))))
        rad.append(0.012 + 0.03 * t ** 2)
    items = [(g.tube(pts, rad, n=7), brass)]
    end, d = pts[-1], (pts[-1] - pts[-2]).normalized()
    side = d.cross(Y).normalized()
    R = Matrix((side, d.cross(side).normalized(), d)).transposed().to_4x4()      # the bell's axis (a lathe's Z) along the horn's end
    items.append((g.moved(g.lathe([(0.04, 0.0), (0.06, 0.03), (0.1, 0.06), (0.13, 0.07)], n=12, caps=False), Matrix.Translation(end) @ R), brass))
    items.append((g.moved(g.lathe([(0.128, 0.068), (0.134, 0.074)], n=12, caps=False), Matrix.Translation(end) @ R), gk.mark("rim", brass)))
    items.append((g.ico(end + d * 0.03, 0.036, sub=1), gk.field("core", 4.0)))
    items.append((g.cone(pts[0], pts[0] - (pts[1] - pts[0]).normalized() * 0.05, 0.018, n=6), lite))
    items.append((g.tube([pts[3] + Y * 0.0, pts[14]], [0.014, 0.014], n=6), wood))
    for k in (5, 11, 17):
        items.append((g.ico(pts[k], rad[k] * 1.5, sub=0, scale=(1, 1, 1)), gk.mark("bands", brass)))
    ob = g.pieces("horn_body", items)
    return gk.Built([ob], _table(zc + 0.3, -0.06, zc, 0.26, {"socket_grip": [tuple((pts[3] + pts[14]) / 2)], "socket_keepsake": [tuple(pts[11] - Z * 0.04)]}))


def woodsword_body():
    """The wooden sword: a practice blade of oak, curved a little, the grip bound in cord, a
    tie of cloth at the pommel; a line of the field where the edge would be."""
    wood, cord, dark = gk.mat("wood"), gk.mat("cord"), gk.mat("leather_dark")
    pts = [Vector((0.0, 0.0, 0.06 + 0.07 * i + 0.0)) + Y * (-0.045 * math.sin(i / 9.0 * math.pi * 0.9)) for i in range(10)]
    items = [(g.tube(pts[3:], [0.02, 0.021, 0.021, 0.02, 0.018, 0.013, 0.003], n=6, flat=0.55, up=Y), wood)]
    items.append((g.tube(pts[:4], [0.017, 0.019, 0.019, 0.019], n=6, flat=0.8, up=Y), dark))
    wraps = None
    for k in range(7):
        p = pts[0].lerp(pts[3], (k + 0.5) / 7.0)
        wraps = g.merge(wraps, f2.band(p, 0.021, 0.018, 0.004, n=8, v=Y, sides=3))
    items.append((wraps, gk.mark("wrap", cord)))
    items.append((g.ico(pts[3], 0.03, sub=0, scale=(1.2, 0.8, 0.3)), wood))
    edge = [p + Y * -0.021 for p in pts[3:]]
    items.append((g.tube(edge, [0.003] * len(edge), n=3), gk.field("pulse", 2.0)))
    items.append((g.merge(g.blade(pts[0], pts[0] + Vector((0.06, 0.03, -0.05)), 0.03, normal=(0, 1, 0)), g.blade(pts[0], pts[0] + Vector((-0.03, 0.05, -0.055)), 0.03, normal=(1, 0, 0))), gk.mark("tie", cord)))
    items += gr._eye(tuple(pts[4] + Vector((0.013, 0, 0))), 0.012, facing=(1, 0, 0))
    ob = g.pieces("woodsword_body", items)
    top = pts[-1].z
    return gk.Built([ob], _table(top, -0.05, 0.4, 0.05, {"socket_grip": [tuple(pts[1])], "socket_keepsake": [tuple(pts[0] - Z * 0.02)], "socket_light": [tuple(pts[6])]}))


# ======================================================================================
# Aspects
# ======================================================================================

def fog_body():
    """Fog: a bank of it that has come ashore and stayed with you. Rolls of grey, paler above,
    a lamp somewhere inside it; shreds lifting off."""
    mist, dark, pale = gk.mat("mist"), gk.mat("mist_dark"), gk.mat("mist_pale")
    items = [(g.ico((0, 0, 0.36), 0.05, sub=1), gk.field("core", 4.5))]
    for i, (x, y, z, r_, sc, m) in enumerate(((0.0, 0.0, 0.3, 0.2, (1.2, 1.0, 0.62), mist), (0.13, 0.05, 0.24, 0.15, (1.3, 0.9, 0.55), dark), (-0.14, -0.03, 0.26, 0.16, (1.2, 1.0, 0.5), dark),
                                              (0.05, -0.1, 0.42, 0.14, (1.25, 0.9, 0.5), pale), (-0.07, 0.08, 0.46, 0.13, (1.2, 1.0, 0.45), pale), (0.0, 0.0, 0.56, 0.1, (1.3, 1.0, 0.4), pale))):
        items.append((g.ico((x, y, z), r_, sub=1, scale=sc, rot=(0, 0, 0.5 * i)), m))
    shreds = None
    for i, (a, rr, z) in enumerate(((0.4, 0.2, 0.6), (1.9, 0.24, 0.5), (3.3, 0.22, 0.66), (4.6, 0.25, 0.44), (5.6, 0.18, 0.7))):
        c = Vector((rr * math.cos(a), rr * math.sin(a), z))
        shreds = g.merge(shreds, g.tongue([c, c + Vector((0.05, 0.02, 0.05)), c + Vector((0.02, 0.07, 0.11))], [0.03, 0.05, 0.004], thick=0.25, normal=(math.cos(a), math.sin(a), 0.3)))
    items.append((shreds, mist))
    items.append((g.lathe([(0.3, 0.1), (0.2, 0.12), (0.0, 0.13)], n=10), dark))
    ob = g.pieces("fog_body", items)
    return gk.Built([ob], _table(0.7, -0.14, 0.36, 0.2))


def flood_body():
    """The flood: a rise of brown water that stands by you. It swells from a spread of silt,
    curls over at the top; reeds come up through it, and the field runs in the crest."""
    water, dark, pale = gk.mat("water"), gk.mat("water_dark"), gk.mat("water_pale")
    items = [(g.lathe([(0.28, 0.08), (0.24, 0.1), (0.15, 0.2), (0.11, 0.36), (0.1, 0.48), (0.07, 0.56), (0.0, 0.58)], n=10), water)]
    items.append((g.lathe([(0.34, 0.07), (0.3, 0.085), (0.0, 0.09)], n=10), dark))
    crest = g.spiral((0, -0.07, 0.56), 0.07, 0.02, 0.85, 0.0, n=10, axis=X, start=math.radians(60))
    items.append((g.tube([p + X * 0.0 for p in crest], [0.07, 0.068, 0.064, 0.058, 0.05, 0.042, 0.034, 0.026, 0.018, 0.01, 0.003], n=7, flat=1.6), pale))
    items.append((g.tube([p + Vector((0, -0.005, 0.0)) for p in crest[:8]], [0.008] * 8, n=3), gk.field("seam", 2.5)))
    drops = None
    for a, rr, z in ((0.6, 0.2, 0.42), (2.0, 0.17, 0.52), (3.6, 0.21, 0.36), (5.0, 0.16, 0.6), (4.2, 0.24, 0.3)):
        drops = g.merge(drops, g.ico((rr * math.cos(a), rr * math.sin(a), z), 0.018, sub=0, scale=(1, 1, 1.5)))
    items.append((drops, pale))
    reeds = None
    for a, rr, h in ((0.9, 0.2, 0.5), (1.3, 0.24, 0.62), (2.6, 0.22, 0.44), (4.0, 0.2, 0.56), (5.5, 0.23, 0.4)):
        b = Vector((rr * math.cos(a), rr * math.sin(a), 0.09))
        reeds = g.merge(reeds, g.blade(b, b + Vector((0.03 * math.cos(a), 0.03 * math.sin(a), h)), 0.03, normal=(math.cos(a), math.sin(a), 0), belly=0.3))
    items.append((reeds, gk.mark("reeds", gk.mat("reed"))))
    eyes = None
    for s in (1, -1):
        eyes = g.merge(eyes, g.ico((s * 0.04, -0.1, 0.42), 0.014, sub=0))
    items.append((eyes, gk.field("eyes", 3.0)))
    ob = g.pieces("flood_body", items)
    return gk.Built([ob], _table(0.68, -0.12, 0.4, 0.14))


def whirl_body():
    """The dust-devil: a column of wind that has picked up the steppe. Three ribbons of dust
    wound up it, widening, grass and grit carried round; a thread of the field up its middle."""
    dust, dark, pale = gk.mat("dust"), gk.mat("dust_dark"), gk.mat("dust_pale")
    items = [(g.tube([(0, 0, 0.1), (0.01, 0, 0.36), (-0.01, 0.01, 0.62), (0, 0, 0.82)], [0.006, 0.012, 0.01, 0.003], n=4), gk.field("core", 4.0))]
    for k, m in enumerate((dust, dark, pale)):
        pts = g.spiral((0, 0, 0.08), 0.05, 0.24, 2.2, 0.72, n=30, axis=Z, start=2 * math.pi * k / 3)
        wid = [0.012 + 0.05 * (i / 30.0) for i in range(31)]
        items.append((g.tube(pts, wid, n=4, flat=0.3, up=Z), m))
    grit, grass = None, None
    for i in range(12):
        a, t = i * 2.4, (i % 6) / 6.0
        c = Vector(((0.1 + 0.17 * t) * math.cos(a), (0.1 + 0.17 * t) * math.sin(a), 0.16 + 0.6 * t))
        if i % 3:
            grit = g.merge(grit, g.ico(c, 0.012, sub=0, rot=(a, a * 2, 0)))
        else:
            grass = g.merge(grass, g.blade(c, c + Vector((0.07 * math.sin(a), -0.07 * math.cos(a), 0.03)), 0.014, normal=(0, 0, 1)))
    items += [(grit, dark), (grass, gk.mark("grass", gk.mat("reed")))]
    items.append((g.lathe([(0.18, 0.05), (0.1, 0.07), (0.0, 0.08)], n=9), dark))
    ob = g.pieces("whirl_body", items)
    return gk.Built([ob], _table(0.84, -0.12, 0.42, 0.18))


# ======================================================================================
# Small people: the fitter, the clerk
# ======================================================================================

def fitter_body():
    """The fitter: a kith of the engine-works, as tall as your knee. A leather apron to the
    shins, a cap, goggles pushed up, a spanner as long as its arm across its back."""
    p = gk.SmallPerson("m", 0.35, {"head-round": 0.5, "nose-scale-vert": 0.3, "ear-scale": 0.5, "chin-prominent": 0.3, "cheek-volume": 0.3},
                       build=(0.6, 0.55), stand=0.56, keep_hands=True, head=1.4, legs=0.82, arms=1.0)
    hb, J = p.hb, p.hb.J
    mat, field = gk.mat, gk.field
    p.make_body(mat("hand_skin"))
    p.eyes(mat("eye_white"), field("eyes", 3.0), mat("eye_dark"))
    hipz, neckz, footz = J["upperleg.l"].z, hb.trunk_z[9], J["foot.l"].z
    arm = hb.is_arm
    p.shell("shirt", p.trunk_mask(hipz - 0.05, neckz - 0.01), mat("cloth_wool"), 0.022)
    p.shell("apron", lambda v: ~arm & (v[:, 2] > footz + 0.3) & (v[:, 2] < neckz - 0.12) & (v[:, 1] < hb.front_y(0.0, hipz) + 0.2), mat("leather"), 0.04)
    p.shell("boots", lambda v: ~arm & (v[:, 2] < footz + 0.34), mat("leather_dark"), 0.026)
    p.shell("belt", p.trunk_mask(hipz + 0.1, hipz + 0.17), mat("leather_dark"), 0.055)
    (x0, x1), (y0, y1), (z0, z1) = hb.head_box
    cy, eye = (y0 + y1) / 2, hb.eye["l"]
    cr = (x1 - x0) / 2
    p.piece("cap", g.ico((0, cy + 0.02, z1 - cr * 0.36), cr * 1.02, sub=1, scale=(1.0, 1.08, 0.5)), mat("leather_dark"), "head")
    p.piece("cap_peak", g.blade((0, y0 + 0.06, z1 - cr * 0.42), (0, y0 - 0.16, z1 - cr * 0.5), 0.3, normal=(0, 0, 1), belly=0.3, thick=0.01), mat("leather_dark"), "head")
    gog = None
    for s in (1, -1):
        gog = g.merge(gog, f2.band((s * 0.09, y0 + 0.01, z1 - cr * 0.2), 0.07, 0.06, 0.016, n=10, sides=4))
    p.piece("goggles", gog, mat("metal_brass"), "head")
    by = hb.front_y(0.0, hipz + 0.3, back=True) + 0.05
    sp = g.merge(g.box((0, by, hipz + 0.32), (0.05, 0.03, 0.62), rot=(0, math.radians(24), 0)),
                 f2.band((0.15, by, hipz + 0.64), 0.07, 0.07, 0.022, n=8, sides=4))
    p.piece("spanner", sp, mat("metal_iron_light"), "chest")
    p.heart(field("heart", 3.0), drop=0.0)
    return p.finish(p.common_sockets(), decimate=0.15)


def clerk_body():
    """The clerk: a small scholar of the halls. A long robe with white cuffs, a square cap,
    a roll of paper under its sash, ink to the wrists."""
    p = gk.SmallPerson("f", 0.3, {"head-oval": 0.5, "eye-scale": 0.3, "nose-scale-vert": -0.2, "ear-scale": 0.3, "cheek-volume": 0.2},
                       build=(0.35, 0.4), stand=0.56, keep_hands=True, head=1.4, legs=0.85, arms=1.0)
    hb, J = p.hb, p.hb.J
    mat, field = gk.mat, gk.field
    p.make_body(mat("hand_skin"))
    p.eyes(mat("eye_white"), field("eyes", 3.0), mat("eye_dark"))
    hipz, neckz, footz = J["upperleg.l"].z, hb.trunk_z[9], J["foot.l"].z
    arm, head = hb.is_arm, (hb.is_head | hb.is_neck)
    wx = abs(J["wrist.l"].x)
    p.shell("robe", lambda v: ~head & (v[:, 2] > footz + 0.1) & (v[:, 2] < neckz + 0.02) & (~arm | (abs(v[:, 0]) < wx - 0.12)), mat("cloth_dark"), 0.045)
    p.shell("cuffs", lambda v: arm & (abs(v[:, 0]) > wx - 0.16) & (abs(v[:, 0]) < wx - 0.04), mat("paper"), 0.05)
    p.shell("sash", p.trunk_mask(hipz + 0.12, hipz + 0.22), mat("cloth_rag"), 0.062)
    (x0, x1), (y0, y1), (z0, z1) = hb.head_box
    cy = (y0 + y1) / 2
    cr = (x1 - x0) / 2
    p.piece("cap", g.merge(g.box((0, cy + 0.02, z1 - 0.02), (cr * 1.7, cr * 1.9, 0.1)), g.box((0, cy + 0.02, z1 + 0.05), (cr * 2.1, cr * 2.2, 0.025))), mat("ink"), "head")
    fy = hb.front_y(0.0, hipz + 0.2) - 0.07
    p.piece("scroll", g.tube([(-0.2, fy, hipz + 0.2), (0.22, fy - 0.01, hipz + 0.26)], [0.04, 0.04], n=7), mat("paper"), "chest")
    p.heart(field("heart", 3.0), drop=0.0)
    return p.finish(p.common_sockets(), decimate=0.15)


# ======================================================================================
# Daemons: the vigil, the marginal
# ======================================================================================

def vigil_body():
    """The vigil: what sits up with you. A hooded shape gone down on its heels, the robe
    pooled round it, no face in the hood but one light; a lamp held in two hands in its lap."""
    shade, edge = gk.mat("shade"), gk.mat("shade_edge")
    items = [(g.lathe([(0.3, 0.0), (0.27, 0.03), (0.2, 0.12), (0.16, 0.26), (0.15, 0.36), (0.1, 0.44), (0.0, 0.46)], n=10), shade)]
    hem = None
    for i in range(10):
        a = 2 * math.pi * i / 10
        hem = g.merge(hem, g.blade((0.22 * math.cos(a), 0.22 * math.sin(a), 0.05), (0.38 * math.cos(a + 0.2), 0.38 * math.sin(a + 0.2), 0.0), 0.16, normal=(0, 0, 1), belly=0.4))
    items.append((hem, gk.mark("hem", edge)))
    items.append((g.ico((0, -0.01, 0.52), 0.11, sub=1, scale=(1.0, 1.1, 1.05)), shade))
    items.append((g.ico((0, -0.06, 0.5), 0.085, sub=1, scale=(0.9, 0.7, 1.0)), gk.mat("void")))
    items.append((g.tongue([(0, 0.02, 0.62), (0, 0.1, 0.56), (0, 0.16, 0.42)], [0.02, 0.1, 0.01], thick=0.4, normal=(0, 1, 0.5)), edge))
    items.append((g.ico((0, -0.115, 0.505), 0.02, sub=1), gk.field("eyes", 4.0)))
    for s in (1, -1):
        items.append((g.tube([(s * 0.15, -0.02, 0.36), (s * 0.17, -0.16, 0.24), (s * 0.06, -0.22, 0.2)], [0.05, 0.04, 0.03], n=6), shade))
        items.append((g.ico((s * 0.045, -0.225, 0.2), 0.03, sub=0, scale=(1, 1, 0.7)), edge))
    items.append((g.lathe([(0.02, 0.2), (0.045, 0.21), (0.045, 0.27), (0.02, 0.3), (0.0, 0.31)], n=6, centre=(0, -0.23, 0)), gk.mat("metal_dark")))
    items.append((g.ico((0, -0.23, 0.245), 0.03, sub=1), gk.field("core", 4.5)))
    ob = g.pieces("vigil_body", items)
    return gk.Built([ob], _table(0.64, -0.13, 0.4, 0.17, {"socket_light": [(0, -0.23, 0.245)], "socket_eyes": [(0, -0.12, 0.505)], "socket_mouth": [(0, -0.12, 0.46)],
                                                           "socket_hand_l": [(0.045, -0.225, 0.2)], "socket_hand_r": [(-0.045, -0.225, 0.2)]}))


def marginal_body():
    """The marginal: what lives in the margins of a book and wants to be read. A book lies
    open in the air; out of its gutter climbs a thin thing of ink, horned, long-handed, its
    hands on the page edges; the lines of the page are the field."""
    ink, edge, paper, lea = gk.mat("ink"), gk.mat("ink_edge"), gk.mat("paper"), gk.mat("leather")
    zc = 0.3
    items = []
    for s in (1, -1):
        T = Matrix.Translation((s * 0.005, 0, zc)) @ Matrix.Rotation(s * math.radians(-14), 4, "Y")
        items.append((g.moved(g.box((s * 0.15, 0, 0.0), (0.3, 0.4, 0.035)), T), paper))
        items.append((g.moved(g.box((s * 0.155, 0, -0.024), (0.32, 0.42, 0.014)), T), gk.mark("cover", lea)))
        lines = None
        for k in range(6):
            lines = g.merge(lines, g.box((s * 0.15, -0.14 + 0.055 * k, 0.019), (0.2 - 0.03 * (k % 2), 0.008, 0.004)))
        items.append((g.moved(lines, T), gk.field("script", 2.2)))
    neck = [(0, 0.02, zc + 0.0), (0.0, 0.06, zc + 0.14), (0.02, 0.0, zc + 0.26), (0.0, -0.05, zc + 0.36)]
    items.append((g.tube(neck, [0.05, 0.036, 0.03, 0.034], n=6), ink))
    hd = Vector((0, -0.07, zc + 0.39))
    items.append((g.ico(hd, 0.06, sub=1, scale=(0.9, 1.25, 0.9)), ink))
    horns, eyes = None, None
    for s in (1, -1):
        horns = g.merge(horns, g.tube([hd + Vector((s * 0.035, 0.02, 0.04)), hd + Vector((s * 0.07, 0.05, 0.11)), hd + Vector((s * 0.05, 0.09, 0.17))], [0.016, 0.011, 0.002], n=4))
        eyes = g.merge(eyes, g.ico(hd + Vector((s * 0.03, -0.055, 0.012)), 0.012, sub=0))
        arm = [(s * 0.03, 0.04, zc + 0.2), (s * 0.16, -0.02, zc + 0.2), (s * 0.27, -0.12, zc + 0.08)]
        items.append((g.tube(arm, [0.02, 0.014, 0.01], n=5), ink))
        fingers = None
        for k in range(4):
            fingers = g.merge(fingers, g.tube([arm[2], Vector(arm[2]) + Vector((s * (0.02 + 0.012 * k), -0.05 + 0.03 * k, -0.045))], [0.008, 0.002], n=3))
        items.append((fingers, edge))
    items += [(horns, edge), (eyes, gk.field("eyes", 3.5))]
    items.append((g.tongue([(0, 0.03, zc + 0.02), (0.03, 0.12, zc - 0.1), (0.0, 0.1, zc - 0.24)], [0.05, 0.03, 0.003], thick=0.5, normal=(0, 1, 0)), gk.mark("drip", ink)))
    ob = g.pieces("marginal_body", items)
    return gk.Built([ob], _table(zc + 0.5, -0.13, zc + 0.3, 0.3, {"socket_head": [tuple(hd + Z * 0.06), Matrix.Scale(0.5, 3)], "socket_eyes": [tuple(hd + Vector((0, -0.06, 0.012))), Matrix.Scale(0.5, 3)],
                                                                    "socket_mouth": [tuple(hd + Vector((0, -0.07, -0.02))), Matrix.Scale(0.5, 3)], "socket_light": [(0, 0, zc + 0.03)], "socket_keepsake": [(0, -0.2, zc - 0.03)]}))
