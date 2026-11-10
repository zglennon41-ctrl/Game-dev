"""WILDLINE genius kit, the second set of forms: more First Forms for the rite's bowl (a crow,
a tortoise, a fledgling kith, a clockwork wren, a hearth-stove, a wick-fiend, a whisperer, rime)
and the Second Forms that follow them (a lamplighter, a train of wisps), and the engines that
were placeholders (the shield-faced engine, the thinking gun). The relics, the parts and the
keepsakes are in genius_relics.py. docs/genius-forms.md has the conventions; genius_kit.py has
the palette, the sockets and the cards, and loads this file (register()).

Every body here names its coat with the palette's material names (data/genius-looks.json maps
them to the coat's roles) and its marking regions with mark(<region>): the game paints both.
"""
import math

from mathutils import Matrix, Vector

import genius_geo as g
from genius_geo import X, Y, Z

gk = None       # genius_kit, given by register()


def register(kit):
    global gk
    gk = kit
    kit.BODIES.update({
        "beast-corvid": lambda: kit.hawk_body(corvid=True),
        "beast-shell": tortoise_body,
        "engine-flier": wren_body,
        "engine-stove": stove_body,
        "daemon-wick": wick_body,
        "daemon-whisper": whisper_body,
        "aspect-frost": rime_body,
        "aspect-wisps": wisps_body,
        "engine-sentinel": sentinel_body,
        "engine-weapon": gun_body,
        "kith-fledgling": fledgling_body,
        "kith-lamplighter": lamplighter_body,
    })


def hoop(centre, rx, rz, n=16, u=X, v=Z, turn=0.0):
    """A closed loop of points (the first repeated at the end), for a tube with no caps."""
    c = Vector(centre)
    return [c + Vector(u) * (math.cos(turn + 2 * math.pi * i / n) * rx) + Vector(v) * (math.sin(turn + 2 * math.pi * i / n) * rz) for i in range(n + 1)]


def band(centre, rx, rz, r, n=16, u=X, v=Z, sides=4, flat=1.0):
    pts = hoop(centre, rx, rz, n, u, v)
    return g.tube(pts, [r] * len(pts), n=sides, caps=False, flat=flat)


def collar_at(centre, rx, rz, tilt=0.0):
    """A collar's socket: where the neck is and how big round (the collar part is a hoop of
    radius 0.1 in its own XZ plane; tilt leans the hoop's top back about X)."""
    R = Matrix.Rotation(tilt, 3, "X") @ Matrix.Diagonal((rx / 0.1, 1.0, rz / 0.1))
    return [tuple(centre), R]


# ======================================================================================
# Beasts
# ======================================================================================

def tortoise_body():
    """The cairn-tortoise: a low dome of stone scutes on four stumped legs, an old head on a
    long neck, a little cairn stacked on its back with a light in the gap between the stones."""
    hide, light, plate = gk.mat("stone_hide"), gk.mat("stone_light"), gk.mat("stone_plate")
    W, L, cy = 0.235, 0.30, 0.03

    def dome(x, y):
        q = max(0.0, 1.0 - (x / W) ** 2 - ((y - cy) / L) ** 2)
        return 0.165 + 0.232 * q ** 0.55
    items = []
    prof = [(1.0, 0.150), (1.03, 0.172), (0.94, 0.245), (0.76, 0.315), (0.5, 0.366), (0.2, 0.392)]
    shell = g.loft([g.ring((0, cy, z), W * f, L * f, n=12, u=X, v=Y, phase=math.pi / 12) for f, z in prof])
    items.append((shell, plate))
    items.append((g.loft([g.ring((0, cy, z), W * f, L * f, n=12, u=X, v=Y, phase=math.pi / 12) for f, z in ((0.8, 0.128), (0.9, 0.14), (0.9, 0.151))]), light))
    # the scutes: five down the spine, four a side, a ring in the middle of each
    scutes, rings = None, None
    spots = [(0, cy + dy, 0.058) for dy in (-0.19, -0.095, 0.0, 0.095, 0.19)] + [(s * 0.125, cy + dy, 0.052) for s in (1, -1) for dy in (-0.14, -0.047, 0.047, 0.14)]
    for x, y, r in spots:
        z = dome(x, y)
        tiltx, tilty = -(y - cy) * 2.2, x * 2.6
        scutes = g.merge(scutes, g.ico((x, y, z - 0.006), r, sub=1, scale=(1.0, 0.9, 0.34), rot=(tiltx, tilty, 0)))
        rings = g.merge(rings, g.ico((x, y, z + 0.012), r * 0.5, sub=0, scale=(1.0, 0.9, 0.3), rot=(tiltx, tilty, 0)))
    items += [(scutes, hide), (rings, gk.mark("rings", hide))]
    # the marginals round the rim, and a line of light where the dome sits on them
    rim = None
    for i in range(14):
        a = 2 * math.pi * (i + 0.5) / 14
        rim = g.merge(rim, g.box((math.cos(a) * W * 1.02, cy + math.sin(a) * L * 1.02, 0.172), (0.03, 0.105, 0.036), rot=(0, 0, a)))
    items.append((rim, hide))
    items.append((band((0, cy, 0.2), W * 1.0, L * 1.0, 0.007, n=20, v=Y, sides=3), gk.field("seam", 1.6)))
    # legs: thick, bowed out, three claws to each
    feet = {}
    for tag, sx, y in (("fl", 1, -0.15), ("fr", -1, -0.15), ("bl", 1, 0.2), ("br", -1, 0.2)):
        fy = y + (-0.045 if y < 0 else 0.03)
        hip, knee, foot = Vector((sx * 0.15, y, 0.17)), Vector((sx * 0.215, fy, 0.085)), Vector((sx * 0.222, fy, 0.0))
        items.append((g.tube([hip, knee], [0.066, 0.058], n=7), hide))
        items.append((g.tube([knee, foot + Z * 0.012, foot], [0.058, 0.06, 0.05], n=7), gk.mark("socks", hide)))
        claws = None
        for dx in (-0.03, 0.0, 0.03):
            claws = g.merge(claws, g.cone(foot + Vector((dx, -0.045, 0.022)), foot + Vector((dx * 1.3, -0.085, 0.004)), 0.014, n=4))
        items.append((claws, gk.mat("claw")))
        feet[tag] = foot
    # the neck and the head: a blunt beak, heavy brows, eyes of the field
    neck = [(0, -0.2, 0.2), (0, -0.31, 0.235), (0, -0.395, 0.29)]
    items.append((g.tube(neck, [0.07, 0.056, 0.05], n=8), hide))
    for s in (1, -1):
        items.append((g.tongue([(s * 0.064, -0.215, 0.215), (s * 0.053, -0.31, 0.248), (s * 0.046, -0.385, 0.3)], [0.022, 0.022, 0.012], thick=0.3, normal=(s, 0, 0.2)), gk.mark("stripes", hide)))
    items.append((g.ico((0, -0.447, 0.312), 0.064, sub=1, scale=(0.95, 1.28, 0.84)), hide))
    items.append((g.ico((0, -0.462, 0.287), 0.047, sub=1, scale=(0.92, 1.25, 0.5)), light))
    items.append((g.blade((0, -0.5, 0.3), (0, -0.548, 0.282), 0.05, normal=(0, 0, 1), belly=0.3), gk.mat("horn_ridge")))
    brow, eyes = None, None
    for s in (1, -1):
        brow = g.merge(brow, g.blade((s * 0.012, -0.5, 0.345), (s * 0.066, -0.43, 0.35), 0.036, normal=(s * 0.4, -0.2, 1), belly=0.5))
        eyes = g.merge(eyes, g.ico((s * 0.048, -0.468, 0.328), 0.015, sub=1, scale=(0.6, 1.0, 0.8)))
    items += [(brow, plate), (eyes, gk.field("eyes", 3.0))]
    items.append((g.cone((0, cy + L * 0.96, 0.19), (0, cy + L + 0.1, 0.12), 0.032, n=5), hide))
    # the cairn: three stones, and a light between the lowest two
    for i, (x, y, z, r, sc) in enumerate(((0.0, cy, 0.418, 0.058, (1.0, 0.85, 0.45)), (0.008, cy + 0.006, 0.456, 0.042, (0.9, 1.0, 0.5)), (-0.004, cy, 0.487, 0.027, (1.0, 0.9, 0.65)))):
        items.append((g.ico((x, y, z), r, sub=1, scale=sc, rot=(0.2 * i, 0.3, 0.9 * i)), light if i != 1 else hide))
    items.append((g.ico((0.004, cy + 0.003, 0.437), 0.02, sub=0), gk.field("core", 4.0)))
    ob = g.pieces("tortoise_body", items)

    def in_dome(p):
        return p.z > 0.2 and (p.x / W) ** 2 + ((p.y - cy) / L) ** 2 < 1.1 and not (p.y < -0.19 and abs(p.x) < 0.085 and p.z < 0.31)
    gk.shape_key(ob, "heavy", lambda p, i: Vector((p.x * 1.05, p.y, 0.2 + (p.z - 0.2) * 1.28)) if in_dome(p) else None)
    gk.shape_key(ob, "lean", lambda p, i: Vector((p.x, p.y, 0.2 + (p.z - 0.2) * 0.8)) if in_dome(p) else None)
    socks = gk._sockets({
        "socket_head": [(0, -0.44, 0.366), Matrix.Scale(0.5, 3)], "socket_eyes": [(0, -0.505, 0.332), Matrix.Scale(0.6, 3)], "socket_mouth": [(0, -0.53, 0.292), Matrix.Scale(0.6, 3)],
        "socket_grip": [(0, -0.51, 0.282), gk.ACROSS_MOUTH],
        "socket_throat": [(0, -0.33, 0.186)], "socket_light": [(0, -0.3, 0.17)], "socket_back": [(0, -0.12, 0.372)], "socket_body": [(0, -0.265, 0.17)],
        "socket_tail": [(0, cy + L * 0.96, 0.19)], "socket_arm_l": [(0.225, -0.08, 0.26)], "socket_arm_r": [(-0.225, -0.08, 0.26)],
        "socket_limb_fl": [tuple(feet["fl"] + Vector((0, -0.03, 0.03)))], "socket_limb_fr": [tuple(feet["fr"] + Vector((0, -0.03, 0.03)))],
        "socket_limb_bl": [tuple(feet["bl"] + Vector((0, -0.03, 0.03)))], "socket_limb_br": [tuple(feet["br"] + Vector((0, -0.03, 0.03)))],
        "socket_hand_l": [tuple(feet["fl"] + Vector((0, -0.05, 0.03))), gk.HAND_ON_PAW_L], "socket_hand_r": [tuple(feet["fr"] + Vector((0, -0.05, 0.03))), gk.HAND_ON_PAW_R],
        "socket_collar": collar_at((0, -0.3, 0.232), 0.066, 0.066, tilt=-0.3),
    })
    return gk.Built([ob], socks)


# ======================================================================================
# Engines
# ======================================================================================

def wren_body():
    """The clockwork wren (and the brass kite it grows into): a riveted brass egg of a bird, a
    needle bill, one eye a lens and the other a sight-glass, a winding key in its back, a cog
    turning in a port in its flank, wings of plate that beat."""
    brass, iron, dark = gk.mat("metal_brass"), gk.mat("metal_iron"), gk.mat("metal_dark")
    items = []
    items.append((g.ico((0, 0, 0.45), 0.112, sub=1, scale=(0.9, 1.25, 0.95)), brass))
    items.append((g.ico((0, -0.152, 0.532), 0.068, sub=1, scale=(1.0, 1.05, 0.95)), brass))
    items.append((band((0, -0.1, 0.497), 0.06, 0.055, 0.012, n=10, sides=4), iron))
    items.append((g.tube([(0, -0.205, 0.527), (0, -0.25, 0.521), (0, -0.315, 0.512)], [0.02, 0.013, 0.002], n=4), dark))
    # the eyes: a lens on the left, the sight-glass on the right
    items.append((g.ico((0.047, -0.192, 0.548), 0.017, sub=1, scale=(0.7, 1.0, 1.0)), gk.field("eyes", 3.5)))
    items.append((band((0.05, -0.192, 0.548), 0.02, 0.02, 0.005, n=8, u=Y, sides=3), iron))
    items.append((g.tube([(-0.044, -0.175, 0.548), (-0.054, -0.245, 0.551)], [0.023, 0.02], n=6), iron))
    items.append((g.ico((-0.0545, -0.247, 0.551), 0.016, sub=1, scale=(1.0, 0.5, 1.0)), gk.field("eyes", 3.5)))
    # the breast: an enamelled plate; a seam round the middle with its rivets
    items.append((g.ico((0, -0.088, 0.4), 0.07, sub=1, scale=(0.95, 0.5, 0.92)), gk.mark("enamel", brass)))
    items.append((band((0, 0.0, 0.45), 0.103, 0.108, 0.006, n=14, sides=3), iron))
    riv = None
    for i in range(10):
        a = 2 * math.pi * i / 10
        riv = g.merge(riv, g.ico((0.108 * math.cos(a), 0.012, 0.45 + 0.113 * math.sin(a)), 0.008, sub=0))
    items.append((riv, iron))
    # the port in its left flank: a dark well, a cog in it, a bead of the field at its hub
    cog = g.lathe([(0.012, 0.0), (0.034, 0.0), (0.034, 0.012), (0.012, 0.012)], n=8)
    teeth = None
    for i in range(8):
        a = 2 * math.pi * i / 8
        teeth = g.merge(teeth, g.box((0.038 * math.cos(a), 0.038 * math.sin(a), 0.006), (0.014, 0.012, 0.012), rot=(0, 0, a)))
    T = Matrix.Translation((0.094, 0.03, 0.445)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
    items.append((g.moved(g.merge(cog, teeth), T), iron))
    items.append((g.ico((0.09, 0.03, 0.445), 0.05, sub=1, scale=(0.3, 1.0, 1.0)), dark))
    items.append((g.ico((0.108, 0.03, 0.445), 0.011, sub=0), gk.field("core", 4.0)))
    # the key
    items.append((g.merge(g.tube([(0, 0.035, 0.545), (0, 0.045, 0.635)], [0.009, 0.009], n=5),
                          band((0.032, 0.045, 0.665), 0.026, 0.03, 0.007, n=8, sides=3), band((-0.032, 0.045, 0.665), 0.026, 0.03, 0.007, n=8, sides=3)), iron))
    # the tail: three plates, fanned
    for i, deg in enumerate((-22, 0, 22)):
        a = math.radians(deg)
        base = Vector((math.sin(a) * 0.02, 0.125, 0.445))
        items.append((g.blade(base, base + Vector((math.sin(a) * 0.2, math.cos(a) * 0.2, 0.035)), 0.06, normal=(0, 0, 1), belly=0.7), brass if i == 1 else iron))
    # legs of wire, tucked
    for s in (1, -1):
        items.append((g.tube([(s * 0.04, 0.0, 0.36), (s * 0.046, 0.035, 0.295), (s * 0.046, -0.005, 0.252)], [0.008, 0.006, 0.006], n=4), dark))
        toes = None
        for dx, dy in ((-0.016, -0.03), (0.0, -0.036), (0.016, -0.03), (0.0, 0.022)):
            toes = g.merge(toes, g.tube([(s * 0.046, -0.005, 0.252), (s * 0.046 + dx, -0.005 + dy, 0.24)], [0.005, 0.003], n=3))
        items.append((toes, dark))
    ob = g.pieces("wren_body", items)
    gk.shape_key(ob, "long_tail", lambda p, i: Vector((p.x * 1.15, 0.125 + (p.y - 0.125) * 1.45, p.z)) if p.y > 0.127 and p.z > 0.41 else None)
    # the wings: plates, five to a wing, each its own object so the game can beat it
    wings = []
    for name, s in (("wing_l", 1), ("wing_r", -1)):
        root = Vector((s * 0.088, -0.01, 0.5))
        geo = g.ico(root, 0.024, sub=0)
        parts = [(geo, iron)]
        for i in range(5):
            a = math.radians(8 + 17 * i)
            d = Vector((s * math.cos(a), math.sin(a), 0.02))
            Lf = 0.27 - 0.028 * i
            parts.append((g.blade(root + d * 0.012, root + d * Lf, 0.07, normal=(0, 0, 1), belly=0.62), brass if i % 2 == 0 else iron))
        w = g.pieces(name, parts)
        gk.set_origin(w, root)
        wings.append(w)
    socks = gk._sockets({
        "socket_head": [(0, -0.15, 0.598)], "socket_eyes": [(0, -0.218, 0.55)], "socket_mouth": [(0, -0.222, 0.522)], "socket_grip": [(0, -0.005, 0.238)],
        "socket_throat": [(0, -0.125, 0.452)], "socket_light": [(0, -0.02, 0.33)], "socket_back": [(0, -0.02, 0.556)], "socket_body": [(0, -0.07, 0.352)],
        "socket_tail": [(0, 0.125, 0.445)], "socket_arm_l": [(0.1, 0, 0.47)], "socket_arm_r": [(-0.1, 0, 0.47)],
        "socket_limb_fl": [(0.046, -0.005, 0.25)], "socket_limb_fr": [(-0.046, -0.005, 0.25)], "socket_hand_l": [(0.046, -0.005, 0.25)], "socket_hand_r": [(-0.046, -0.005, 0.25)],
        "socket_collar": collar_at((0, -0.1, 0.497), 0.072, 0.066, tilt=-0.5),
    })
    return gk.Built([ob] + wings, socks)


def stove_body():
    """The hearth-stove: a pot-bellied iron stove walking on three bowed legs, its fire behind
    the bars of its door, two round vents over the door for eyes, a pipe with a rain cap."""
    iron, lite, brass, dark = gk.mat("metal_iron"), gk.mat("metal_iron_light"), gk.mat("metal_brass"), gk.mat("metal_dark")
    items = []
    items.append((g.lathe([(0.085, 0.15), (0.17, 0.2), (0.215, 0.3), (0.2, 0.42), (0.152, 0.5), (0.13, 0.522)], n=10), iron))
    items.append((g.lathe([(0.2205, 0.28), (0.225, 0.3), (0.2165, 0.33)], n=10, caps=False), gk.mark("band", iron)))
    items.append((g.lathe([(0.14, 0.52), (0.168, 0.53), (0.162, 0.546), (0.05, 0.552)], n=10), lite))
    items.append((g.lathe([(0.02, 0.552), (0.03, 0.567), (0.012, 0.582)], n=6, centre=(0, -0.06, 0)), brass))
    # the door: a plate, the fire behind four bars, a latch
    items.append((g.box((0, -0.203, 0.315), (0.17, 0.04, 0.17)), gk.mark("enamel", lite)))
    items.append((g.box((0, -0.222, 0.315), (0.118, 0.012, 0.11)), gk.field("core", 4.0)))
    bars = g.merge(*[g.box((-0.045 + 0.03 * j, -0.229, 0.315), (0.011, 0.012, 0.118)) for j in range(4)], g.box((0, -0.229, 0.372), (0.13, 0.014, 0.012)), g.box((0, -0.229, 0.258), (0.13, 0.014, 0.012)))
    items.append((bars, dark))
    items.append((g.merge(g.tube([(0.098, -0.225, 0.33), (0.098, -0.25, 0.33), (0.098, -0.25, 0.295)], [0.008, 0.008, 0.008], n=4), g.box((-0.088, -0.224, 0.36), (0.012, 0.016, 0.03)), g.box((-0.088, -0.224, 0.27), (0.012, 0.016, 0.03))), brass))
    # the eyes: two vents, rimmed
    eyes, rims = None, None
    for s in (1, -1):
        c = Vector((s * 0.062, -0.176, 0.44))
        eyes = g.merge(eyes, g.ico(c, 0.024, sub=1, scale=(1.0, 0.5, 1.0)))
        rims = g.merge(rims, band(c + Vector((0, -0.006, 0)), 0.027, 0.027, 0.006, n=8, sides=3))
    items += [(eyes, gk.field("eyes", 3.5)), (rims, brass)]
    # the pipe, its collar and its cap; a thread of smoke
    items.append((g.tube([(0, 0.075, 0.54), (0, 0.075, 0.74)], [0.046, 0.042], n=8), lite))
    items.append((g.lathe([(0.052, 0.6), (0.056, 0.61), (0.052, 0.62)], n=8, centre=(0, 0.075, 0), caps=False), brass))
    items.append((g.lathe([(0.08, 0.765), (0.05, 0.79), (0.012, 0.806)], n=8, centre=(0, 0.075, 0)), iron))
    struts = None
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        struts = g.merge(struts, g.tube([(0.04 * math.cos(a), 0.075 + 0.04 * math.sin(a), 0.735), (0.05 * math.cos(a), 0.075 + 0.05 * math.sin(a), 0.772)], [0.005, 0.005], n=3))
    items.append((struts, dark))
    smoke = g.merge(g.ico((0.0, 0.13, 0.775), 0.026, sub=0, scale=(1.0, 1.0, 0.8)), g.ico((0.02, 0.185, 0.8), 0.034, sub=0, scale=(1.0, 1.1, 0.8), rot=(0.4, 0.2, 0.3)),
                    g.ico((-0.012, 0.255, 0.835), 0.042, sub=0, scale=(1.0, 1.1, 0.75), rot=(0.1, 0.5, 1.0)))
    items.append((smoke, gk.mat("shade_edge")))
    riv = None
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        riv = g.merge(riv, g.ico((0.205 * math.cos(a), 0.205 * math.sin(a), 0.42), 0.011, sub=0))
    items.append((riv, brass))
    # three legs
    feet = {}
    for tag, deg in (("fl", 320), ("fr", 220), ("bl", 90)):
        a = math.radians(deg)
        d = Vector((math.cos(a), math.sin(a), 0))
        hip, knee, foot = d * 0.14 + Z * 0.185, d * 0.245 + Z * 0.125, d * 0.25 + Z * 0.02
        items.append((g.tube([hip, knee, foot], [0.03, 0.026, 0.02], n=6), iron))
        items.append((g.merge(g.ico(knee, 0.034, sub=1), g.ico(foot + d * 0.012, 0.04, sub=1, scale=(1.0, 1.0, 0.5))), brass))
        feet[tag] = foot
    ob = g.pieces("stove_body", items)

    def belly(p, k):
        r = math.hypot(p.x, p.y)
        if not (0.2 < p.z < 0.5) or r > 0.26:
            return None
        f = 1.0 + k * math.sin(math.pi * (p.z - 0.2) / 0.3)
        return Vector((p.x * f, p.y * f, p.z))
    gk.shape_key(ob, "heavy", lambda p, i: belly(p, 0.16))
    gk.shape_key(ob, "lean", lambda p, i: belly(p, -0.12))
    socks = gk._sockets({
        "socket_head": [(0, -0.05, 0.556)], "socket_eyes": [(0, -0.2, 0.442)], "socket_mouth": [(0, -0.24, 0.3)], "socket_grip": [(0.21, -0.05, 0.36)],
        "socket_throat": [(0, -0.19, 0.49)], "socket_light": [(0, -0.09, 0.6)], "socket_back": [(0, 0.19, 0.42)], "socket_body": [(0, -0.2, 0.2)],
        "socket_tail": [(0, 0.2, 0.26)], "socket_arm_l": [(0.225, 0, 0.36)], "socket_arm_r": [(-0.225, 0, 0.36)],
        "socket_limb_fl": [tuple(feet["fl"])], "socket_limb_fr": [tuple(feet["fr"])], "socket_limb_bl": [tuple(feet["bl"])],
        "socket_hand_l": [tuple(feet["fl"] + Z * 0.03), gk.HAND_ON_PAW_L], "socket_hand_r": [tuple(feet["fr"] + Z * 0.03), gk.HAND_ON_PAW_R],
        "socket_keepsake": [(0, -0.19, 0.5)],
    })
    return gk.Built([ob], socks)


def sentinel_body():
    """The shield-faced engine: a squat iron walker with no head, a heater shield bolted where
    a face would be, a slit of light across it; wall-plates on its shoulders, a boiler behind."""
    iron, lite, brass, dark = gk.mat("metal_iron"), gk.mat("metal_iron_light"), gk.mat("metal_brass"), gk.mat("metal_dark")
    items = []
    items.append((g.lathe([(0.1, 0.3), (0.17, 0.33), (0.19, 0.45), (0.17, 0.57), (0.11, 0.62)], n=8, phase=math.pi / 8), iron))
    items.append((g.lathe([(0.193, 0.42), (0.197, 0.45), (0.19, 0.48)], n=8, phase=math.pi / 8, caps=False), gk.mark("band", iron)))
    # the shield: a heater, bossed, a visor slit of the field, a blazon across it
    sh = [(-0.15, 0.7), (0.15, 0.7), (0.158, 0.54), (0.1, 0.4), (0.0, 0.33), (-0.1, 0.4), (-0.158, 0.54)]
    front = [Vector((x, -0.2 - 0.03 * (1 - (x / 0.16) ** 2), z)) for x, z in sh]
    back = [p + Vector((0, 0.03, 0)) for p in front]
    n = len(sh)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    items.append(((front + back, faces), lite))
    rimpts = [p + Vector((0, -0.006, 0)) for p in front] + [front[0] + Vector((0, -0.006, 0))]
    items.append((g.tube(rimpts, [0.012] * len(rimpts), n=4, caps=False), brass))
    items.append((g.box((0, -0.236, 0.585), (0.2, 0.012, 0.022)), gk.field("eyes", 3.5)))
    items.append((g.merge(g.box((0, -0.24, 0.607), (0.24, 0.014, 0.016)), g.box((0, -0.24, 0.563), (0.24, 0.014, 0.016))), dark))
    chev = g.merge(g.box((0.055, -0.238, 0.47), (0.15, 0.012, 0.034), rot=(0, math.radians(32), 0)), g.box((-0.055, -0.238, 0.47), (0.15, 0.012, 0.034), rot=(0, math.radians(-32), 0)))
    items.append((chev, gk.mark("blazon", lite)))
    items.append((g.ico((0, -0.245, 0.4), 0.026, sub=1, scale=(1.0, 0.5, 1.0)), brass))
    for s in (1, -1):
        items.append((g.tube([(s * 0.06, -0.16, 0.56), (s * 0.06, -0.21, 0.56)], [0.018, 0.018], n=5), dark))
    # shoulders: wall-plates; arms ending in fists of plate
    for s in (1, -1):
        items.append((g.box((s * 0.235, 0.0, 0.56), (0.07, 0.2, 0.17), rot=(0, s * math.radians(-14), 0)), lite))
        items.append((g.box((s * 0.262, 0.0, 0.575), (0.016, 0.21, 0.05), rot=(0, s * math.radians(-14), 0)), gk.mark("band", iron)))
        sh_, el, wr = Vector((s * 0.2, 0.0, 0.52)), Vector((s * 0.255, -0.02, 0.4)), Vector((s * 0.25, -0.07, 0.3))
        items.append((g.tube([sh_, el, wr], [0.04, 0.034, 0.04], n=6), iron))
        items.append((g.merge(g.ico(el, 0.042, sub=1), g.ico(sh_, 0.05, sub=1)), brass))
        items.append((g.box(wr + Vector((0, -0.02, -0.035)), (0.085, 0.095, 0.09)), lite))
    # legs: thick, kneed in brass, broad feet
    feet = {}
    for tag, s in (("l", 1), ("r", -1)):
        hip, knee, ank = Vector((s * 0.1, 0.01, 0.31)), Vector((s * 0.13, -0.03, 0.18)), Vector((s * 0.125, 0.02, 0.055))
        items.append((g.tube([hip, knee, ank], [0.058, 0.05, 0.045], n=7), iron))
        items.append((g.ico(knee, 0.058, sub=1), brass))
        items.append((g.box((s * 0.125, -0.015, 0.027), (0.12, 0.2, 0.054)), lite))
        items.append((g.box((s * 0.125, -0.105, 0.02), (0.1, 0.03, 0.04)), dark))
        feet[tag] = Vector((s * 0.125, -0.03, 0.0))
    # the boiler on its back, its stack, its gauge
    items.append((g.tube([(0, 0.17, 0.36), (0, 0.17, 0.6)], [0.085, 0.08], n=8), lite))
    items.append((g.tube([(0.04, 0.2, 0.6), (0.04, 0.2, 0.74)], [0.028, 0.032], n=6), dark))
    items.append((g.merge(band((0, 0.17, 0.43), 0.088, 0.088, 0.008, n=10, v=Y, sides=3), band((0, 0.17, 0.55), 0.086, 0.086, 0.008, n=10, v=Y, sides=3)), brass))
    riv = None
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        riv = g.merge(riv, g.ico((0.172 * math.cos(a), 0.172 * math.sin(a), 0.34), 0.012, sub=0))
    items.append((riv, brass))
    ob = g.pieces("sentinel_body", items)
    socks = gk._sockets({
        "socket_head": [(0, -0.05, 0.63)], "socket_eyes": [(0, -0.245, 0.588)], "socket_mouth": [(0, -0.25, 0.44)], "socket_grip": [(-0.25, -0.1, 0.27), gk.GRIP_IN_HAND_R],
        "socket_throat": [(0, -0.2, 0.33)], "socket_light": [(0.25, -0.1, 0.24)], "socket_back": [(0, 0.26, 0.5)], "socket_body": [(0, -0.2, 0.3)],
        "socket_tail": [(0, 0.2, 0.33)], "socket_arm_l": [(0.275, 0, 0.6)], "socket_arm_r": [(-0.275, 0, 0.6)],
        "socket_limb_fl": [tuple(feet["l"] + Vector((0, -0.07, 0.03)))], "socket_limb_fr": [tuple(feet["r"] + Vector((0, -0.07, 0.03)))],
        "socket_hand_l": [(0.25, -0.09, 0.265), gk.HAND_ON_ARM_L], "socket_hand_r": [(-0.25, -0.09, 0.265), gk.HAND_ON_ARM_R],
        "socket_keepsake": [(0, -0.215, 0.32)],
    })
    return gk.Built([ob], socks)


def gun_body():
    """The thinking gun: a long gun that carries itself, muzzle to the front. An octagon barrel
    of iron in a walnut stock, its lock an open nest of cogs, a sight-glass along the top with
    the field in its lens, the hammer forever half-cocked."""
    iron, wood, brass, dark = gk.mat("metal_iron"), gk.mat("wood"), gk.mat("metal_brass"), gk.mat("metal_dark")
    z0 = 0.45
    items = []
    items.append((g.tube([(0, 0.02, z0 + 0.012), (0, -0.52, z0 + 0.012)], [0.026, 0.021], n=8), iron))
    # a muzzle ring of brass
    items.append((g.moved(g.lathe([(0.024, 0.0), (0.031, 0.012), (0.024, 0.026)], n=8, caps=False), Matrix.Translation((0, -0.5, z0 + 0.012)) @ Matrix.Rotation(math.pi / 2, 4, "X")), brass))
    items.append((g.ico((0, -0.522, z0 + 0.012), 0.014, sub=0), dark))
    # the stock: fore-end under the barrel, the wrist, the butt dropping behind
    fore = g.loft([g.ring((0, y, z0 - 0.02), 0.03, 0.026, n=6, u=X, v=Z, phase=math.pi / 6) for y in (-0.33, -0.2, 0.02)])
    items.append((fore, wood))
    butt = g.loft([g.ring((0, y, z), rx, rz, n=6, u=X, v=Z, phase=math.pi / 6) for y, z, rx, rz in ((0.02, z0 - 0.012, 0.034, 0.04), (0.12, z0 - 0.03, 0.028, 0.034), (0.24, z0 - 0.075, 0.03, 0.058), (0.34, z0 - 0.1, 0.032, 0.075))])
    items.append((butt, wood))
    items.append((g.box((0, 0.345, z0 - 0.1), (0.07, 0.014, 0.16)), brass))
    for s in (1, -1):
        items.append((g.tongue([(s * 0.033, 0.05, z0 - 0.02), (s * 0.031, 0.18, z0 - 0.058), (s * 0.034, 0.31, z0 - 0.095)], [0.012, 0.014, 0.01], thick=0.3, normal=(s, 0, 0)), gk.mark("inlay", wood)))
    # the lock: a plate, three cogs, a bead of the field at the hub of the largest, the hammer
    items.append((g.box((0.036, 0.03, z0 - 0.005), (0.012, 0.15, 0.07)), brass))
    for (cy_, cz_, r_, mt) in ((0.0, z0 + 0.0, 0.03, iron), (0.052, z0 - 0.012, 0.02, dark), (0.076, z0 + 0.016, 0.014, iron)):
        cog = g.lathe([(0.006, 0.0), (r_, 0.0), (r_, 0.01), (0.006, 0.01)], n=8)
        teeth = None
        for i in range(8):
            a = 2 * math.pi * i / 8
            teeth = g.merge(teeth, g.box(((r_ + 0.004) * math.cos(a), (r_ + 0.004) * math.sin(a), 0.005), (0.012, 0.009, 0.01), rot=(0, 0, a)))
        items.append((g.moved(g.merge(cog, teeth), Matrix.Translation((0.043, cy_, cz_)) @ Matrix.Rotation(math.pi / 2, 4, "Y")), mt))
    items.append((g.ico((0.056, 0.0, z0), 0.009, sub=0), gk.field("core", 4.0)))
    items.append((g.tongue([(0.0, 0.07, z0 + 0.03), (0.0, 0.085, z0 + 0.07), (0.0, 0.05, z0 + 0.085)], [0.02, 0.016, 0.01], thick=0.6, normal=(1, 0, 0)), dark))
    items.append((g.tube([(0, 0.06, z0 - 0.045), (0, 0.075, z0 - 0.085), (0, 0.13, z0 - 0.085), (0, 0.145, z0 - 0.05)], [0.005] * 4, n=3), brass))
    items.append((g.tube([(0, 0.095, z0 - 0.045), (0, 0.105, z0 - 0.072)], [0.006, 0.004], n=3), dark))
    # the sight-glass: a tube on two rings, a lens of the field at each end
    sz = z0 + 0.062
    items.append((g.tube([(0, 0.03, sz), (0, -0.2, sz)], [0.017, 0.015], n=8), brass))
    items.append((g.merge(g.ico((0, -0.204, sz), 0.0135, sub=1, scale=(1.0, 0.4, 1.0)), g.ico((0, 0.034, sz), 0.015, sub=1, scale=(1.0, 0.4, 1.0))), gk.field("eyes", 3.5)))
    items.append((g.merge(g.box((0, -0.14, z0 + 0.04), (0.012, 0.018, 0.03)), g.box((0, -0.02, z0 + 0.04), (0.012, 0.018, 0.03))), dark))
    items.append((g.merge(band((0, -0.14, sz), 0.019, 0.019, 0.004, n=8, sides=3), band((0, -0.02, sz), 0.02, 0.02, 0.004, n=8, sides=3)), dark))
    items.append((g.box((0, -0.5, z0 + 0.042), (0.006, 0.012, 0.02)), brass))
    # a ramrod under the barrel, two bands holding barrel to stock
    items.append((g.tube([(0, -0.02, z0 - 0.048), (0, -0.4, z0 - 0.018)], [0.006, 0.006], n=4), dark))
    for y in (-0.31, -0.16):
        items.append((band((0, y, z0 - 0.002), 0.034, 0.04, 0.005, n=8, sides=3), brass))
    ob = g.pieces("gun_body", items)
    socks = gk._sockets({
        "socket_head": [(0, 0.0, z0 + 0.085)], "socket_eyes": [(0, -0.21, sz)], "socket_mouth": [(0, -0.53, z0 + 0.012)], "socket_grip": [(0, 0.1, z0 - 0.09)],
        "socket_throat": [(0, -0.3, z0 - 0.05)], "socket_light": [(0, -0.36, z0 + 0.05)], "socket_back": [(0, 0.16, z0 + 0.0)], "socket_body": [(0, -0.1, z0 - 0.05)],
        "socket_tail": [(0, 0.35, z0 - 0.1)], "socket_arm_l": [(0.05, 0.03, z0)], "socket_arm_r": [(-0.04, 0.03, z0)],
        "socket_limb_fl": [(0.03, -0.2, z0 - 0.05)], "socket_limb_fr": [(-0.03, -0.2, z0 - 0.05)], "socket_keepsake": [(0, 0.1, z0 - 0.088)],
    })
    return gk.Built([ob], socks)


# ======================================================================================
# Daemons
# ======================================================================================

def wick_body():
    """The wick-fiend: a squat soot-black imp with a candle stub melted to its skull between
    its horns, the wick alight; a grin of the same fire, wax run down over its shoulders, a
    thin tail with a flame at its tip."""
    coal, under, horn, wax = gk.mat("coal"), gk.mat("shade_edge"), gk.mat("horn"), gk.mat("wax")
    flame = gk.field("flame", 3.0)
    items = []
    items.append((g.lathe([(0.045, 0.2), (0.1, 0.235), (0.118, 0.32), (0.098, 0.4), (0.062, 0.45)], n=8), coal))
    items.append((g.ico((0, -0.072, 0.31), 0.078, sub=1, scale=(1.0, 0.5, 1.12)), under))
    items.append((g.ico((0, -0.02, 0.545), 0.102, sub=1, scale=(1.06, 0.95, 0.9)), coal))
    for s in (1, -1):
        items.append((g.blade((s * 0.085, -0.01, 0.55), (s * 0.225, 0.04, 0.6), 0.07, normal=(0, -1, 0.3), belly=0.35), coal))
        items.append((g.tube([(s * 0.052, -0.03, 0.618), (s * 0.092, -0.02, 0.675), (s * 0.08, 0.015, 0.73)], [0.021, 0.015, 0.003], n=5), horn))
    # the candle, its wick, its flame
    items.append((g.lathe([(0.044, 0.61), (0.046, 0.655), (0.03, 0.664)], n=7, centre=(0, -0.02, 0)), wax))
    items.append((g.tube([(0, -0.02, 0.66), (0.004, -0.022, 0.69)], [0.004, 0.003], n=3), gk.mat("metal_dark")))
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.4
        pts = [(0.012 * math.cos(a), -0.02 + 0.012 * math.sin(a), 0.68), (0.03 * math.cos(a + 0.3), -0.02 + 0.03 * math.sin(a + 0.3), 0.725), (0.006 * math.cos(a + 1.0), -0.02 + 0.006 * math.sin(a + 1.0), 0.8 + 0.02 * i)]
        items.append((g.tongue(pts, [0.028, 0.045, 0.003], thick=0.45, normal=(math.cos(a), math.sin(a), 0)), flame))
    items.append((g.ico((0, -0.02, 0.705), 0.017, sub=0, scale=(1, 1, 1.4)), gk.field("core", 5.0)))
    # wax run down: a little always, more as a marking
    for s, a0 in ((1, 0.3), (-1, -0.2)):
        items.append((g.tongue([(s * 0.04, -0.05 + a0 * 0.05, 0.63), (s * 0.075, -0.07, 0.585), (s * 0.082, -0.075, 0.545)], [0.03, 0.026, 0.004], thick=0.4, normal=(s, -0.6, 0.3)), wax))
    drips = None
    for s in (1, -1):
        drips = g.merge(drips, g.tongue([(s * 0.07, -0.03, 0.455), (s * 0.118, -0.03, 0.43), (s * 0.135, -0.04, 0.37)], [0.05, 0.06, 0.005], thick=0.35, normal=(s, 0, 0.8)))
        drips = g.merge(drips, g.tongue([(s * 0.04, -0.07, 0.45), (s * 0.05, -0.105, 0.4), (s * 0.045, -0.112, 0.34)], [0.04, 0.04, 0.004], thick=0.35, normal=(0, -1, 0.3)))
    drips = g.merge(drips, g.tongue([(0, 0.06, 0.46), (0, 0.105, 0.41), (0, 0.11, 0.33)], [0.06, 0.06, 0.005], thick=0.35, normal=(0, 1, 0.3)))
    items.append((drips, gk.mark("drips", coal)))
    # the face
    eyes = None
    for s in (1, -1):
        eyes = g.merge(eyes, g.ico((s * 0.042, -0.108, 0.562), 0.021, sub=1, scale=(1.25, 0.45, 0.62), rot=(0, s * -0.35, 0)))
    items.append((eyes, gk.field("eyes", 4.0)))
    items.append((g.tongue([(-0.055, -0.097, 0.507), (-0.025, -0.113, 0.492), (0.025, -0.113, 0.492), (0.055, -0.097, 0.507)], [0.004, 0.022, 0.022, 0.004], thick=0.3, normal=(0, -1, 0)), gk.field("mouth", 3.0)))
    # arms, hands of three claws; bowed legs
    hands, feet = {}, {}
    for tag, s in (("l", 1), ("r", -1)):
        sh, el, wr = Vector((s * 0.098, -0.01, 0.42)), Vector((s * 0.172, -0.03, 0.33)), Vector((s * 0.158, -0.095, 0.262))
        items.append((g.tube([sh, el, wr], [0.03, 0.022, 0.02], n=6), coal))
        claws = None
        for dx in (-0.018, 0.0, 0.018):
            claws = g.merge(claws, g.tube([wr, wr + Vector((dx, -0.035, -0.03)), wr + Vector((dx * 1.4, -0.045, -0.07))], [0.011, 0.009, 0.002], n=4))
        items.append((claws, coal))
        hands[tag] = wr
        hip, knee, ank, toe = Vector((s * 0.055, 0.0, 0.22)), Vector((s * 0.085, -0.045, 0.125)), Vector((s * 0.075, 0.005, 0.04)), Vector((s * 0.078, -0.075, 0.0))
        items.append((g.tube([hip, knee, ank], [0.042, 0.03, 0.022], n=6), coal))
        items.append((g.tongue([ank + Vector((0, 0.02, -0.015)), ank + Vector((0, -0.03, -0.028)), toe + Vector((0, -0.02, 0.006))], [0.04, 0.055, 0.01], thick=0.5, normal=(0, 0, 1)), coal))
        feet[tag] = toe
    tail = [(0, 0.09, 0.24), (0.0, 0.2, 0.2), (0.03, 0.275, 0.26), (0.045, 0.27, 0.36)]
    items.append((g.tube(tail, [0.02, 0.014, 0.01, 0.006], n=5), coal))
    items.append((g.tongue([(0.045, 0.27, 0.355), (0.06, 0.262, 0.4), (0.048, 0.268, 0.45)], [0.022, 0.034, 0.003], thick=0.5), flame))
    ob = g.pieces("wick_body", items)
    socks = gk._sockets({
        "socket_head": [(0, -0.02, 0.64)], "socket_eyes": [(0, -0.118, 0.564)], "socket_mouth": [(0, -0.118, 0.5)], "socket_grip": [tuple(hands["r"] + Vector((0, -0.02, -0.03))), gk.GRIP_IN_HAND_R],
        "socket_throat": [(0, -0.085, 0.435)], "socket_light": [tuple(hands["l"] + Vector((0, -0.03, -0.06)))], "socket_back": [(0, 0.1, 0.4)], "socket_body": [(0, -0.115, 0.33)],
        "socket_tail": [(0, 0.09, 0.24)], "socket_arm_l": [(0.13, -0.01, 0.44)], "socket_arm_r": [(-0.13, -0.01, 0.44)],
        "socket_hand_l": [tuple(hands["l"]), gk.HAND_ON_ARM_L], "socket_hand_r": [tuple(hands["r"]), gk.HAND_ON_ARM_R],
        "socket_limb_fl": [tuple(feet["l"] + Vector((0, 0.02, 0.03)))], "socket_limb_fr": [tuple(feet["r"] + Vector((0, 0.02, 0.03)))],
        "socket_collar": collar_at((0, -0.012, 0.452), 0.075, 0.07),
    })
    return gk.Built([ob], socks)


def whisper_body():
    """The whisperer: small enough to ride a shoulder. A hood with no eyes in it, only a mouth
    of light; a hand raised beside the mouth; and on the back of the hood a pale second face
    that watches the way you came."""
    ink, edge, bone = gk.mat("ink"), gk.mat("ink_edge"), gk.mat("bone")
    prof = [(0.82, 0.012, 0.012, 0.03), (0.77, 0.06, 0.066, 0.01), (0.69, 0.1, 0.11, -0.01), (0.6, 0.108, 0.118, 0.0), (0.52, 0.075, 0.08, 0.0),
            (0.47, 0.115, 0.09, 0.005), (0.4, 0.13, 0.092, 0.01), (0.31, 0.105, 0.075, 0.012), (0.22, 0.066, 0.05, 0.012)]
    rings = [g.ring((0, yo, z), rx, ry, n=10, u=X, v=Y, phase=math.pi / 10) for z, rx, ry, yo in prof][::-1]
    cloak = g.to_object("whisper_cloak", g.loft(rings), ink)
    gk.paint(cloak, lambda c, n, i: (int((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi) * 10) % 2 == 0) and abs(n.z) < 0.85 and c.z < 0.5, edge)
    items = []
    items.append((g.ico((0, -0.082, 0.61), 0.078, sub=1, scale=(0.92, 0.42, 1.1)), gk.mat("void")))
    for s in (1, -1):
        items.append((g.tongue([(0, -0.098, 0.72), (s * 0.07, -0.118, 0.66), (s * 0.082, -0.114, 0.585), (s * 0.04, -0.098, 0.525)], [0.02, 0.034, 0.032, 0.012], thick=0.5, normal=(s * 0.3, -1, 0)), edge))
    # no eyes: a mouth, wide and thin, and three teeth of dark in it
    items.append((g.tongue([(-0.05, -0.108, 0.6), (-0.022, -0.118, 0.585), (0.022, -0.118, 0.585), (0.05, -0.108, 0.6)], [0.004, 0.024, 0.024, 0.004], thick=0.3, normal=(0, -1, 0)), gk.field("mouth", 3.5)))
    # the second face: a mask on the back of the hood, brow, nose, two slits
    items.append((g.ico((0, 0.098, 0.63), 0.075, sub=1, scale=(0.82, 0.3, 1.12)), bone))
    items.append((g.tongue([(0, 0.122, 0.655), (0, 0.137, 0.62), (0, 0.124, 0.6)], [0.012, 0.022, 0.006], thick=0.7, normal=(1, 0, 0)), bone))
    slits = None
    for s in (1, -1):
        slits = g.merge(slits, g.ico((s * 0.03, 0.12, 0.655), 0.014, sub=1, scale=(1.3, 0.4, 0.45), rot=(0, s * 0.25, 0)))
    items.append((slits, gk.field("eyes", 3.0)))
    items.append((g.box((0, 0.118, 0.585), (0.034, 0.008, 0.006)), gk.mat("void")))
    # the hem: tatters, their tips a marking
    for i in range(9):
        a = 2 * math.pi * (i + 0.5) / 9
        d = Vector((math.cos(a), math.sin(a) * 0.75, 0))
        Lh = 0.12 + 0.04 * ((i * 7) % 3)
        mid, tip = d * 0.075 + Z * (0.225 - Lh * 0.5), d * (0.055 + 0.02 * (i % 2)) + Z * (0.225 - Lh)
        items.append((g.tongue([d * 0.064 + Z * 0.225, mid], [0.046, 0.036], thick=0.3, normal=d), ink if i % 2 else edge))
        items.append((g.tongue([mid, tip], [0.036, 0.003], thick=0.3, normal=d), gk.mark("hem", edge)))
    # sleeves: the left raised to cup the mouth, the right hanging
    for s, (el, wr) in ((1, (Vector((0.17, -0.07, 0.45)), Vector((0.1, -0.135, 0.56)))), (-1, (Vector((-0.185, -0.03, 0.34)), Vector((-0.2, -0.08, 0.25))))):
        sh = Vector((s * 0.12, 0.0, 0.44))
        items.append((g.tongue([sh, el, wr], [0.085, 0.08, 0.055], thick=0.5, normal=(s, 0, 0.3)), ink))
        fingers = None
        up = Vector((-0.012, -0.01, 0.05)) if s == 1 else Vector((0, -0.02, -0.06))
        for j, off in enumerate((-0.016, 0.0, 0.016)):
            side = Vector((0, off, 0)) if s == 1 else Vector((off, 0, 0))
            fingers = g.merge(fingers, g.tongue([wr, wr + up * 0.5 + side, wr + up * (1.0 + 0.12 * (j == 1)) + side * 1.5], [0.014, 0.011, 0.002], thick=0.5))
        items.append((fingers, edge))
    ob = g.join("whisper_body", [cloak, g.pieces("whisper_dress", items)])
    socks = gk._sockets({
        "socket_head": [(0, 0.02, 0.8)], "socket_eyes": [(0, -0.125, 0.64)], "socket_mouth": [(0, -0.124, 0.588)], "socket_grip": [(-0.2, -0.08, 0.23)],
        "socket_throat": [(0, -0.09, 0.5)], "socket_light": [(0, -0.14, 0.36)], "socket_back": [(0, 0.1, 0.45)], "socket_body": [(0, -0.1, 0.4)],
        "socket_tail": [(0, 0.06, 0.21)], "socket_arm_l": [(0.2, -0.05, 0.4)], "socket_arm_r": [(-0.2, -0.05, 0.4)],
        "socket_hand_l": [(0.1, -0.135, 0.56)], "socket_hand_r": [(-0.2, -0.08, 0.25)], "socket_limb_fl": [(0.045, 0, 0.09)], "socket_limb_fr": [(-0.045, 0, 0.09)],
        "socket_collar": collar_at((0, 0.0, 0.52), 0.086, 0.09),
    })
    return gk.Built([ob], socks)


# ======================================================================================
# Aspects
# ======================================================================================

def _crystal(base, tip, r, mats_, n=5, waist=0.28):
    """An ice crystal: a short root, a long faceted body, a point."""
    base, tip = Vector(base), Vector(tip)
    d = tip - base
    return g.tube([base, base + d * waist, base + d * 0.78, tip], [r * 0.45, r, r * 0.8, r * 0.03], n=n)


def rime_body():
    """Rime: a cold heart of the field in a crown of ice. Seven spars stand round it, clear,
    milky and dark by turns; splinters hang in the air about them; frost creeps out below."""
    ice, dark, pale = gk.mat("ice"), gk.mat("ice_dark"), gk.mat("ice_pale")
    items = [(g.ico((0, 0, 0.42), 0.06, sub=1, scale=(0.85, 0.85, 1.3)), gk.field("core", 5.0))]
    kinds = (ice, pale, dark)
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.2
        h = 0.62 + 0.09 * ((i * 3) % 4)
        lean = 0.05 + 0.03 * (i % 3)
        base = Vector((0.085 * math.cos(a), 0.085 * math.sin(a), 0.24))
        tip = Vector(((0.085 + lean) * 1.5 * math.cos(a + 0.15), (0.085 + lean) * 1.5 * math.sin(a + 0.15), h))
        items.append((_crystal(base, tip, 0.05 - 0.004 * (i % 3), None, n=5), kinds[i % 3]))
    # the root: a knot of short spars pointing down and out, and a floor of frost
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.7
        base = Vector((0.03 * math.cos(a), 0.03 * math.sin(a), 0.3))
        tip = Vector((0.17 * math.cos(a), 0.17 * math.sin(a), 0.15 + 0.03 * (i % 2)))
        items.append((_crystal(base, tip, 0.034, None, n=4), kinds[(i + 1) % 3]))
    frost = None
    for i in range(9):
        a = 2 * math.pi * i / 9
        frost = g.merge(frost, g.blade((0.05 * math.cos(a), 0.05 * math.sin(a), 0.135), (0.26 * math.cos(a + 0.12), 0.26 * math.sin(a + 0.12), 0.11 + 0.012 * (i % 3)), 0.07, normal=(0, 0, 1), belly=0.55))
    items.append((frost, pale))
    # splinters adrift, and motes of the field among them
    splint, motes = None, None
    for i, (a, rr, z) in enumerate(((0.3, 0.24, 0.5), (1.5, 0.27, 0.68), (2.6, 0.22, 0.38), (3.7, 0.26, 0.6), (4.9, 0.23, 0.76), (5.7, 0.28, 0.44))):
        c = Vector((rr * math.cos(a), rr * math.sin(a), z))
        splint = g.merge(splint, g.tube([c - Z * 0.035, c + Vector((0.006, 0.004, 0)), c + Z * 0.05], [0.002, 0.014, 0.002], n=4))
        if i % 2 == 0:
            motes = g.merge(motes, g.ico(c + Vector((0.03 * math.cos(a + 2), 0.03 * math.sin(a + 2), 0.07)), 0.009, sub=0))
    items += [(splint, ice), (motes, gk.field("cinder", 3.0))]
    # veins of the field in the two tallest spars
    for i in (1, 5):
        a = 2 * math.pi * i / 7 + 0.2
        p0 = Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 0.3))
        p1 = Vector((0.155 * math.cos(a + 0.12), 0.155 * math.sin(a + 0.12), 0.56))
        items.append((g.tube([p0, (p0 + p1) / 2 + Vector((0.01, 0.01, 0)), p1], [0.006, 0.008, 0.003], n=3), gk.field("crack", 2.5)))
    ob = g.pieces("rime_body", items)
    socks = gk._sockets({
        "socket_head": [(0, 0, 0.8)], "socket_eyes": [(0, -0.075, 0.45)], "socket_mouth": [(0, -0.08, 0.39)], "socket_grip": [(0.16, 0, 0.42)],
        "socket_throat": [(0, -0.08, 0.34)], "socket_light": [(0, 0, 0.42)], "socket_back": [(0, 0.12, 0.46)], "socket_body": [(0, -0.12, 0.38)],
        "socket_tail": [(0, 0.13, 0.28)], "socket_arm_l": [(0.18, 0, 0.45)], "socket_arm_r": [(-0.18, 0, 0.45)],
        "socket_limb_fl": [(0.09, -0.08, 0.2)], "socket_limb_fr": [(-0.09, -0.08, 0.2)], "socket_keepsake": [(0, -0.13, 0.3)],
    })
    return gk.Built([ob], socks)


def _wisp(c, r, turn, flame, wisp, tall=1.0):
    """One small flame: a heart, three tongues turning round it, two low ones."""
    c = Vector(c)
    out = [(g.ico(c, r * 0.5, sub=1, scale=(0.9, 0.9, 1.2)), gk.field("core", 5.0))]
    for i in range(3):
        a = 2 * math.pi * i / 3 + turn
        pts = [c + Vector((r * 0.45 * math.cos(a), r * 0.45 * math.sin(a), -r * 0.5)), c + Vector((r * 0.85 * math.cos(a + 0.3), r * 0.85 * math.sin(a + 0.3), r * 0.5)),
               c + Vector((r * 0.45 * math.cos(a + 0.8), r * 0.45 * math.sin(a + 0.8), r * 1.6 * tall)), c + Vector((r * 0.08 * math.cos(a + 1.2), r * 0.08 * math.sin(a + 1.2), r * (2.6 + 0.4 * i) * tall))]
        out.append((g.tongue(pts, [r * 0.6, r * 0.85, r * 0.5, r * 0.04], thick=0.42, normal=(math.cos(a), math.sin(a), 0)), flame))
    for i in range(2):
        a = math.pi * i + turn + 0.9
        pts = [c + Vector((r * 0.8 * math.cos(a), r * 0.8 * math.sin(a), -r * 0.7)), c + Vector((r * 1.25 * math.cos(a + 0.3), r * 1.25 * math.sin(a + 0.3), r * 0.1)), c + Vector((r * 0.95 * math.cos(a + 0.8), r * 0.95 * math.sin(a + 0.8), r * 1.0))]
        out.append((g.tongue(pts, [r * 0.5, r * 0.6, r * 0.04], thick=0.4, normal=(math.cos(a), math.sin(a), 0)), wisp))
    return out


def wisps_body():
    """The wisp-train: not one flame but a procession of five, the first carried in a little
    cage of brass like a lantern with no glass, the rest following in a rising curve, each
    smaller, a coal riding under the lead and a thread of smoke after the last."""
    flame, wisp, coal = gk.field("flame", 3.0), gk.field("wisp", 1.6), gk.mat("coal")
    brass = gk.mat("metal_brass")
    items = []
    train = [((0.0, -0.16, 0.42), 0.075), ((0.09, -0.02, 0.5), 0.055), ((0.03, 0.11, 0.57), 0.046), ((-0.08, 0.2, 0.63), 0.038), ((-0.13, 0.31, 0.7), 0.03)]
    for i, (c, r) in enumerate(train):
        items += _wisp(c, r, 0.7 * i, flame, wisp, tall=1.0 if i else 0.85)
    # the lead's cage: two hoops, four bars, a ring to carry it by
    c0 = Vector(train[0][0])
    items.append((g.merge(band(c0 + Z * -0.06, 0.085, 0.085, 0.007, n=10, v=Y, sides=3), band(c0 + Z * 0.1, 0.07, 0.07, 0.007, n=10, v=Y, sides=3)), brass))
    bars = None
    for k in range(4):
        a = math.pi / 4 + math.pi / 2 * k
        bars = g.merge(bars, g.tube([c0 + Vector((0.085 * math.cos(a), 0.085 * math.sin(a), -0.06)), c0 + Vector((0.07 * math.cos(a), 0.07 * math.sin(a), 0.1)), c0 + Vector((0, 0, 0.2))], [0.005, 0.005, 0.004], n=3))
    items.append((bars, brass))
    items.append((band(c0 + Z * 0.222, 0.022, 0.022, 0.005, n=8, sides=3), brass))
    coals = g.ico(c0 + Z * -0.085, 0.055, sub=0, scale=(1.1, 1.1, 0.5))
    for i in range(4):
        a = 2 * math.pi * i / 4 + 0.5
        coals = g.merge(coals, g.ico(c0 + Vector((0.055 * math.cos(a), 0.055 * math.sin(a), -0.075)), 0.03, sub=0, scale=(1.0, 0.8, 0.7), rot=(0.3 * i, 0.5 * i, a)))
    items.append((coals, coal))
    # cinders between the flames, smoke after the last
    cinders = None
    for i in range(len(train) - 1):
        a, b = Vector(train[i][0]), Vector(train[i + 1][0])
        cinders = g.merge(cinders, g.ico((a + b) / 2 + Vector((0.02, 0.0, 0.03)), 0.009, sub=0), g.ico(a * 0.3 + b * 0.7 + Vector((-0.02, 0.01, -0.02)), 0.007, sub=0))
    items.append((cinders, gk.field("cinder", 3.0)))
    last = Vector(train[-1][0])
    smoke = None
    for i, a in enumerate((0.9, 3.4)):
        pts = [last + Vector((0.01 * math.cos(a), 0.03, 0.08)), last + Vector((0.04 * math.cos(a + 0.6), 0.08, 0.14)), last + Vector((0.02 * math.cos(a + 1.4), 0.13, 0.2 + 0.02 * i))]
        smoke = g.merge(smoke, g.tongue(pts, [0.026, 0.03, 0.003], thick=0.4))
    items.append((smoke, gk.mat("shade_edge")))
    ob = g.pieces("wisps_body", items)
    socks = gk._sockets({
        "socket_head": [tuple(c0 + Z * 0.25)], "socket_eyes": [tuple(c0 + Vector((0, -0.07, 0.03)))], "socket_mouth": [tuple(c0 + Vector((0, -0.075, -0.03)))], "socket_grip": [tuple(c0 + Vector((0.12, 0, 0)))],
        "socket_throat": [tuple(c0 + Vector((0, -0.08, -0.07)))], "socket_light": [tuple(Vector(train[1][0]))], "socket_back": [tuple(Vector(train[2][0]) + Z * 0.02)], "socket_body": [tuple(c0 + Vector((0, -0.1, -0.02)))],
        "socket_tail": [tuple(last)], "socket_arm_l": [tuple(c0 + Vector((0.11, 0, 0.02)))], "socket_arm_r": [tuple(c0 + Vector((-0.11, 0, 0.02)))],
        "socket_limb_fl": [tuple(c0 + Vector((0.06, -0.04, -0.11)))], "socket_limb_fr": [tuple(c0 + Vector((-0.06, -0.04, -0.11)))], "socket_keepsake": [tuple(c0 + Vector((0, -0.085, -0.062)))],
    })
    return gk.Built([ob], socks)


# ======================================================================================
# Kith
# ======================================================================================

def fledgling_body():
    """The fledgling kith: the stooping kith before it has its feathers. A child of the field
    in a cloak of down too big for it, the hood fallen back, the heart-light bright."""
    p = gk.SmallPerson("f", 0.16, {"ear-shape-pointed": 1.0, "ear-scale": 0.8, "head-round": 0.7, "cheek-volume": 0.5, "eye-scale": 0.6, "nose-scale-vert": -0.4},
                       build=(0.4, 0.45), stand=0.52, keep_hands=False, head=1.55, legs=0.8, arms=0.95)
    hb, J = p.hb, p.hb.J
    mat, field = gk.mat, gk.field
    p.make_body(mat("hand_skin"))
    p.eyes(field("eyes_dim", 1.2), field("eyes", 3.5), field("eyes", 3.5))
    hipz, neckz = J["upperleg.l"].z, hb.trunk_z[9]
    p.shell("smock", p.trunk_mask(hipz - 0.26, neckz - 0.03), mat("leather"), 0.03)
    (x0, x1), (y0, y1), (z0, z1) = hb.head_box
    eye = hb.eye["l"]
    head = hb.is_head
    # a cap of down on the crown (a piece: garments cut from the body stop at the neck), a
    # tuft standing at the back of it
    cr = (x1 - x0) / 2 * 0.96
    p.piece("cap", g.ico((0, (y0 + y1) / 2 + 0.06, z1 - cr * 0.33), cr, sub=1, scale=(1.0, 1.05, 0.5)), mat("feather_dark"), "head")
    tuft = None
    for i, (dx, L) in enumerate(((-0.06, 0.16), (0.0, 0.24), (0.06, 0.17))):
        tuft = g.merge(tuft, g.blade((dx, (y0 + y1) / 2 + 0.06, z1 - 0.03), (dx * 1.6, (y0 + y1) / 2 + 0.16, z1 + L), 0.1, normal=(0, -1, 0.3), belly=0.45))
    p.piece("tuft", tuft, mat("feather_pale"), "head")
    # the cloak of down: three short rows, pale over mid over dark, open at the throat
    z, hw, hd, yo = hb.rings("trunk", "fit")[-1]
    for row, (n, L, out, m) in enumerate(((10, 0.24, 0.2, "feather_pale"), (11, 0.36, 0.2, "feather_mid"), (10, 0.5, 0.17, "feather_dark"))):
        geo = None
        for i in range(n):
            a = math.radians(24 + 312 * i / (n - 1)) - math.pi / 2
            d = Vector((math.cos(a), -math.sin(a), 0))
            base = Vector((d.x * (hw * 0.6), yo + d.y * (hd * 0.75), neckz + 0.03 - 0.025 * row))
            geo = g.merge(geo, g.blade(base, base + d * (out + 0.1 * abs(d.x)) + Vector((0, 0, -L)), 0.24, normal=d + Vector((0, 0, 0.6)), belly=0.55))
        p.piece("down_%d" % row, geo, mat(m), "chest")
    p.heart(field("heart", 3.5), drop=0.0)
    socks = p.common_sockets()
    return p.finish(socks, decimate=0.2)


def lamplighter_body():
    """The lamplighter: an old kith of the roads, long-coated and broad-hatted. The pole is
    strapped to his back and bends over his head, so the light hangs before him and before
    you. The lantern is his heart-light."""
    p = gk.SmallPerson("m", 0.6, {"head-age": 0.8, "eye-bag": 0.6, "nose-scale-vert": 0.5, "nose-hump": 0.5, "ear-shape-pointed": 0.8, "ear-scale": 0.6, "chin-prominent": 0.4,
                                 "cheek-volume": -0.5}, build=(0.4, 0.3), stand=0.62, keep_hands=True, head=1.25, legs=0.9, arms=1.0)
    hb, J = p.hb, p.hb.J
    mat, field = gk.mat, gk.field
    wool, darkc, lea = mat("cloth_wool"), mat("cloth_dark"), mat("leather")
    p.make_body(mat("hand_skin"))
    p.eyes(mat("eye_white"), field("eyes", 3.0), mat("eye_dark"))
    hipz, neckz = J["upperleg.l"].z, hb.trunk_z[9]
    footz = J["foot.l"].z
    arm, head = hb.is_arm, (hb.is_head | hb.is_neck)
    wx = abs(J["wrist.l"].x)
    # the long coat: from the collar to the shins, sleeves to the wrists
    p.shell("coat", lambda v: ~head & (v[:, 2] > footz + 0.42) & (v[:, 2] < neckz + 0.03) & (~arm | (abs(v[:, 0]) < wx - 0.05)), wool, 0.045)
    p.shell("boots", lambda v: ~arm & (v[:, 2] < footz + 0.5), darkc, 0.025)
    p.shell("belt", p.trunk_mask(hipz + 0.12, hipz + 0.2), lea, 0.065)
    # the hat: a low crown and a broad brim, a band of leather
    (x0, x1), (y0, y1), (z0, z1) = hb.head_box
    cy, eye = (y0 + y1) / 2, hb.eye["l"]
    bz = eye.z + 0.14
    p.piece("hat_brim", g.lathe([(0.1, bz + 0.012), (0.36, bz - 0.012), (0.37, bz + 0.002), (0.1, bz + 0.03)], n=10, centre=(0, cy, 0)), darkc, "head")
    p.piece("hat_crown", g.lathe([(0.2, bz + 0.012), (0.19, bz + 0.14), (0.12, bz + 0.2), (0.02, bz + 0.21)], n=10, centre=(0, cy, 0)), darkc, "head")
    p.piece("hat_band", g.lathe([(0.203, bz + 0.03), (0.207, bz + 0.05), (0.2, bz + 0.07)], n=10, centre=(0, cy, 0), caps=False), lea, "head")
    # a short beard
    mouth = hb.humans["fit"].joint("joint-mouth")
    my, mz = hb.front_y(0.0, float(mouth[2]) - 0.05), float(mouth[2])
    p.piece("beard", g.tongue([(0, my - 0.005, mz - 0.03), (0, my - 0.03, mz - 0.13), (0, my - 0.005, mz - 0.27)], [0.15, 0.13, 0.01], thick=0.5, normal=(0, -1, 0)), mat("hair_pale"), "head")
    # the pole: up his back from the belt, bending forward over the hat; the lantern on its hook
    by = hb.front_y(0.0, hipz + 0.3, back=True) + 0.04
    crook = [(0.0, by, hipz + 0.05), (0.0, by + 0.03, neckz), (0.0, by, z1 + 0.25), (0.0, cy - 0.12, z1 + 0.5), (0.0, y0 - 0.38, z1 + 0.42), (0.0, y0 - 0.52, z1 + 0.22)]
    p.piece("pole", g.tube(crook, [0.02, 0.02, 0.018, 0.016, 0.013, 0.011], n=5), mat("wood"), "chest")
    p.piece("pole_straps", g.merge(g.box((0, by - 0.01, hipz + 0.16), (0.3, 0.05, 0.035)), g.box((0, by + 0.0, neckz - 0.12), (0.34, 0.05, 0.035))), lea, "chest")
    lc = Vector((0.0, y0 - 0.52, z1 + 0.02))
    cage = g.merge(g.lathe([(0.03, 0.0), (0.088, 0.015), (0.088, 0.03)], n=6, centre=tuple(lc + Z * -0.115)), g.lathe([(0.094, 0.0), (0.05, 0.05), (0.012, 0.085)], n=6, centre=tuple(lc + Z * 0.085)))
    for k in range(6):
        a = math.radians(60 * k)
        cage = g.merge(cage, g.tube([lc + Vector((0.078 * math.cos(a), 0.078 * math.sin(a), -0.09)), lc + Vector((0.078 * math.cos(a), 0.078 * math.sin(a), 0.09))], [0.008, 0.008], n=3))
    cage = g.merge(cage, band(lc + Z * 0.185, 0.022, 0.022, 0.006, n=8, sides=3))
    p.piece("lantern_cage", cage, mat("metal_brass"), "chest")
    p.piece("lantern_light", g.ico(lc, 0.054, sub=1, scale=(0.85, 0.85, 1.25)), field("core", 4.5), "chest")
    socks = p.common_sockets()
    return p.finish(socks, decimate=0.15)
