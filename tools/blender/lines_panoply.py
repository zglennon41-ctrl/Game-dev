"""WILDLINE genius lines, the Living Armor (docs/genius-lines.md, "The Living Armor").

The soul of someone who keeps themselves to themselves, dressed to leave, warm to very few:
an empty suit of armor that walks, and stands between. A small person on the small people's
kit (lines_people.py, with the Angel's pieces that move: lines_angel.Angel), of which nothing
is left but the plate: the body's own skin is pushed out into plates where it is armored and
drawn in to a thread everywhere else, so the plates hang in the air with nothing joining
them, and the helm stands over an empty collar with the field's light in its visor.

    python tools/blender/genius_lines.py panoply
    python tools/blender/genius_lines.py panoply panoply-squire panoply-sworn-plate
    python tools/blender/lines_panoply.py body       # game/assets/genius/bodies/relic-panoply.glb (the clips its forms move by)
    python tools/blender/lines_panoply.py gifts      # game/assets/genius/gifts/panoply-helm.glb, panoply-pauldrons.glb

What a `body` may say, here (a slot holds a style, [style, size], or a list of them):

    build      the small people's: age, head, legs, arms, wide, deep, belly, bow, neck, hands, feet...
    helm       pot (a child's, too big), armet, armet-open (its visor up), great, kettle (a brimmed
               iron hat over an open dark), sallet, hood, lamp (a lantern where the helm was),
               none (an empty collar, and two lights over it)
    brow       level, stern, raised, soft (the edge of the visor: its face)
    eyes       two, one              gaze   -1 to 1: where the lights in the visor look
    crest      tuft, plume, comb, fin, ram, horns, crenels, candle, cairn
    plate      child (a breastplate, mitts and boots), full, heavy, lamellar
    chest      keel, hoops, prow, hole, grate, barred-door, shut-door
    fauld      tassets, apron, skirt
    pauldrons  cups, great, slab, slab-one, spikes, towers, tiles, lames
    left, right   lid, heater, tower, wall, door, sword-down, sword-up, staff, crook, lamp-staff,
               dark-lamp, spear, glaive, standard
    back       cape, cloak, wrap, torn, moss, banner, pennons, slung, stack, stacks, shafts, flag,
               roll, pack
    over       sash, tabard, scarf, ribbons       belt   keys
    pose       offer (a hand held out)
    coat       how its partner's metal is worn (a shift of data/genius-looks.json)
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE  # noqa: E402
import lines_people as lp  # noqa: E402
from lines_people import Person, each, _hoop, _disc  # noqa: E402
import lines_angel as la  # noqa: E402
from lines_angel import opt, _c  # noqa: E402
import people_dress as pd  # noqa: E402

GL = None           # genius_lines, whichever way it was started (set in register)
ROOT = kit.ROOT
OUT = os.path.join(ROOT, "game", "assets", "genius", "forms")
SIL = "relic-panoply"
pi = math.pi

# The Living Armor's own colours. Its plate is its partner's choice of metal (iron_plate,
# iron_plate_light, brass_trim: the roles of data/genius-looks.json); the rest are its own.
OWN = {
    "iron_plate": (_c("#616169"), 0.45, 0.8), "iron_plate_light": (_c("#84848B"), 0.4, 0.8), "brass_trim": (_c("#CEAF6C"), 0.35, 0.85),
    "iron_plate_dark": (_c("#3A3A40"), 0.5, 0.8), "wood_shield": (_c("#7A5A3A"), 0.8, 0.0), "wood_door": (_c("#6A4A2E"), 0.85, 0.0),
    "wood_pole": (_c("#5A3D22"), 0.8, 0.0), "leather_strap": (_c("#4A3020"), 0.75, 0.0), "stone_cairn": (_c("#8A8782"), 0.95, 0.0),
    "moss_way": (_c("#5E6B3C"), 0.95, 0.0), "horn_ram": (_c("#C8B894"), 0.6, 0.0), "smoke_kiln": (_c("#6E6C70"), 1.0, 0.0),
    "steel_edge": (_c("#B8BEC8"), 0.3, 0.85),
}
PALETTE.update(OWN)

# how it stands at each stage: a child's harness, a youth's, a grown one, one in its prime
lp.STAGE["panoply"] = [dict(age=0.2, head=1.4, legs=0.72, arms=0.95, limbs=1.2, hands=1.4, feet=1.45), dict(age=0.42, head=1.16, legs=0.96, arms=1.0, limbs=1.12, hands=1.18, feet=1.2),
                       dict(age=0.5, head=1.1, legs=1.0, arms=1.0, limbs=1.12, hands=1.18, feet=1.2), dict(age=0.56, head=1.04, legs=1.04, arms=1.02, limbs=1.14, hands=1.18, feet=1.2)]
lp.FACE["panoply"] = {"ear-scale": -1.0}
lp.SKIN["panoply"] = "void"
# how it may stand otherwise than at ease (lines_angel.Angel.repose)
la.STANCES.update({
    # a gauntlet held out, low and open: for one person
    "offer": [("upperarm.r", (-0.3, -0.7, -0.64), 0), ("lowerarm.r", (-0.12, -0.96, 0.24), 0), ("hand.r", (-0.05, -0.98, 0.2), 0)],
})


def log(*a):
    print("[lines_panoply]", *a)


def _roles():
    with open(os.path.join(ROOT, "data", "genius-looks.json")) as f:
        looks = json.load(f)
    return {role: name for name, role in looks["bodies"].get(SIL, {}).get("roles", {}).items()}


def spun(profile, c, n=12, sy=1.0, bulge=None, tilt=None):
    """A profile of (radius, height above c) spun about the upright through c; sy squashes it
    front to back; bulge(angle, ring) scales a ring's radius by where round it is (the front
    is at -pi/2); tilt turns the whole about c."""
    c = V(c)
    rings = []
    for i, (r, z) in enumerate(profile):
        ring = []
        for k in range(n):
            a = 2 * pi * k / n
            rr = r * (bulge(a, i) if bulge else 1.0)
            p = Vector((rr * math.cos(a), rr * sy * math.sin(a), z))
            ring.append(c + (tilt @ p if tilt else p))
        rings.append(ring)
    return g.loft(rings, caps=True)


def front(a):
    return max(0.0, -math.sin(a))


def slab(outline, o, u, v, w, thick):
    """A flat plate cut to an outline of (along u, along v) about o, `thick` along w."""
    o, u, v, w = V(o), V(u), V(v), V(w)
    r0 = [o + u * a + v * b for a, b in outline]
    return g.loft([r0, [p + w * thick for p in r0]], caps=True)


def shrunk(outline, k):
    cx = sum(p[0] for p in outline) / len(outline)
    cz = sum(p[1] for p in outline) / len(outline)
    return [(cx + (a - cx) * k, cz + (b - cz) * k) for a, b in outline]


def turned(geo, c, M):
    c = V(c)
    return [c + M @ (V(p) - c) for p in geo[0]], geo[1]


# ======================================================================================
# The body: plate, and nothing
# ======================================================================================

class Armor(la.Angel):
    """A small person of which only the plate is left (lines_angel.Angel gives the pieces the
    game moves, and a body that may stand otherwise than at ease)."""

    def __init__(self, form_id, level, spec):
        Person.__init__(self, "panoply", form_id, level, spec, _roles())
        self.silhouette = SIL
        self.movers = []
        self.L = 1.0
        self.kept = np.zeros(len(self.v0), dtype=bool)
        self.thick = 0.06
        x = self.v0[:, 0]
        self.side = {"l": x > 0, "r": x < 0}
        self.trunkv = ~self.arm & ~self.headv & ~self.leg
        self.waist = self.hipz + 0.2 * self.t
        self.yc = self.J["chest"].y

    def plate(self, mask, material, thick):
        self.wear(mask, material, thick)
        self.kept |= mask

    def hollow(self):
        """What is not plate is nothing: drawn in to a thread along its own bone, so the plates
        are joined by nothing that can be seen and close at their ends on the dark inside."""
        v0, J = self.v0, self.J
        rest = ~self.kept
        self.dead = rest[self.fa].all(axis=1)       # the faces that are nothing at all: they are not made

        def to_line(mask, pts, k):
            idx = np.nonzero(mask)[0]
            if not len(idx):
                return
            p = v0[idx]
            best, bd = None, None
            for a, b in zip(pts[:-1], pts[1:]):
                a, b = np.array(a, dtype=float), np.array(b, dtype=float)
                d = b - a
                tt = np.clip(((p - a) @ d) / max(1e-9, float(d @ d)), 0.0, 1.0)
                q = a + tt[:, None] * d
                dist = ((p - q) ** 2).sum(axis=1)
                if best is None:
                    best, bd = q, dist
                else:
                    m = dist < bd
                    best[m], bd[m] = q[m], dist[m]
            self.v[idx] = best + (p - best) * k
        for s in ("l", "r"):
            to_line(rest & self.arm & self.side[s], [J["upperarm." + s], J["lowerarm." + s], J["wrist." + s], J["handslot." + s]], 0.004)
            f = J["foot." + s]
            to_line(rest & self.leg & self.side[s], [J["upperleg." + s], J["lowerleg." + s], f, (f.x, f.y - 0.1, 0.03)], 0.004)
        to_line(rest & self.headv, [(0, self.yc, self.neckz - 0.08), (0, self.yc, self.neckz - 0.04)], 0.004)
        to_line(rest & self.trunkv, [(0, self.yc, self.hipz - 0.1), (0, self.yc, self.neckz - 0.06)], 0.004)

    def finish(self, path, clips=False):
        hb = self.hb
        faces, keep = hb.faces, ~self.dead
        hb.faces = [f for f, k in zip(faces, keep) if k]
        self.fmat = self.fmat[keep]
        try:
            la.Angel.finish(self, path, clips=clips)
        finally:
            hb.faces = faces

    def yf(self, z, x=0.0):
        """The front of its plate at a height."""
        return self.front(z, x) - self.thick

    def yb(self, z, x=0.0):
        return self.rear(z, x) + self.thick


def plates(P, spec):
    """child (a breastplate, two mitts, two boots), full (a whole harness), heavy (thick, for
    the Siege-plate), lamellar (thin, and laced in rows)."""
    kind, size, _ = opt(spec.get("plate") or "full")
    v, t = P.v0, P.t
    main, light = P.material("main"), P.material("under")
    ax, z = np.abs(v[:, 0]), v[:, 2]
    P.thick = thick = {"child": 0.05, "full": 0.06, "heavy": 0.1, "lamellar": 0.05}.get(kind, 0.06) * size
    low = P.waist + (0.03 * t if kind == "child" else 0.0)
    P.plate(P.trunkv & (z > low), light if kind == "child" else main, thick * (1.5 if kind == "child" else 1.0))
    P.plate(P.hand, light if kind == "child" else main, {"child": 0.05, "heavy": 0.05}.get(kind, 0.025))
    P.plate(P.leg & (z < P.footz + (0.16 if kind == "child" else 0.04) * t), light if kind == "child" else main, {"child": 0.06, "heavy": 0.07}.get(kind, 0.04))
    if kind != "child":
        arm = P.arm & ~P.hand
        P.plate(arm & (ax > P.sx + 0.1 * t) & (ax < P.ex - 0.06 * t), main, thick * 0.7)
        P.plate(arm & (ax > P.ex + 0.05 * t) & (ax < P.wx + 0.02), light, thick * 0.9)
        P.plate(P.leg & (z > P.kneez + 0.08 * t) & (z < P.hipz - 0.14 * t), main, thick * 0.8)
        P.plate(P.leg & (z > P.footz + 0.1 * t) & (z < P.kneez - 0.05 * t), light, thick * 0.9)
        # the cops of its knees and elbows: a small plate over each, with nothing behind it
        for s, tag in ((1, "l"), (-1, "r")):
            k = P.J["lowerleg." + tag]
            P.add("knee_" + tag, g.ico((k.x, k.y - 0.1 * t, k.z), 0.11 * t * (1.3 if kind == "heavy" else 1.0), sub=1, scale=(1.0, 0.6, 1.15)), light, "lowerleg." + tag, smooth=False)
            e = P.J["lowerarm." + tag]
            P.add("elbow_" + tag, g.ico((e.x, e.y + 0.07 * t, e.z), 0.085 * t * (1.3 if kind == "heavy" else 1.0), sub=1, scale=(1.1, 0.7, 1.0)), light, "lowerarm." + tag, smooth=False)
    P.hollow()
    # the collar, and the dark in it
    c = pd.neck_c(P)
    rr = 0.105 * t + 0.03
    P.add("collar", pd.wall((c.x, c.y, 0), (rr + 0.1, rr + 0.09), (rr + 0.03, rr + 0.03), P.neckz - 0.09 * t, P.neckz + 0.05 * t, thick=0.02, n=10), light, "chest", smooth=False)
    P.add("collar_dark", _disc((c.x, c.y, P.neckz + 0.0), rr + 0.02, normal=Z, thick=0.012, n=10), mat("void"), "chest", smooth=False)
    if kind == "child":         # the straps of a breastplate cut for someone larger
        hw, hd, yo = P.ring(low + 0.02)
        P.add("strap", _hoop((0, yo, low + 0.03), hw + thick + 0.01, hd + thick + 0.01, 0.025 * t, u=X, v=Y, n=12, sides=4), mat("leather_strap"), "chest", smooth=True)
        P.add("rim", _hoop((0, yo, low), hw + thick + 0.015, hd + thick + 0.015, 0.02 * t, u=X, v=Y, n=12, sides=3), P.material("trim"), "chest", smooth=False)
    if kind == "lamellar":      # rows of small plates, laced in its Path's colour
        n = 4
        for i in range(n):
            zz = P.waist + (P.chestz + 0.1 * t - P.waist) * (i + 0.5) / n
            hw, hd, yo = P.ring(zz)
            P.add("lace_%d" % i, _hoop((0, yo, zz), hw + thick + 0.012, hd + thick + 0.012, 0.022 * t, u=X, v=Y, n=14, sides=3), mat("accent_dark" if i % 2 else "accent"), "chest", smooth=False)
    return kind


# ======================================================================================
# The helm: its face is the visor
# ======================================================================================

def helm(P, spec):
    kind, size, _ = opt(spec.get("helm") or "pot")
    hr, e = P.hr, P.eye
    main, light, trim = P.material("main"), P.material("under"), P.material("trim")
    c = Vector((0, P.hcy, (P.chin + P.crown) / 2))
    k = 1.2 * size * (1.22 if kind == "pot" else 1.0)
    rx, ry, rz = hr * k, (P.hy1 - P.hy0) / 2 * k, P.hh / 2 * k
    sy = ry / rx
    ez = e.z - c.z
    H = dict(c=c, rx=rx, ry=ry, rz=rz, top=c + Z * rz, kind=kind, sy=sy)
    a = 0.2 * hr * {"armet-open": 2.4, "sallet": 0.72, "kettle": 1.0, "hood": 1.5}.get(kind, 1.0)       # half the height of the slit
    tilt = Matrix.Rotation(0.2, 3, "Y") @ Matrix.Rotation(-0.08, 3, "X") if kind == "pot" else None
    H["tilt"] = tilt

    def put(name, geo, material, smooth=False):
        P.add(name, turned(geo, c, tilt) if tilt else geo, material, "head", smooth=smooth)

    def band(z0, z1, open_=0.68, k=1.03, material=None):
        """What joins the skull to the chin round the back, leaving the front open."""
        put("helm_band", pd.drape((c.x, c.y, 0), lambda t_: (rx * k, ry * k), [c.z + z1, c.z + z0], -pi * open_, pi * open_, thick=0.05 * hr, n=11), material or main)
    eyes_at = None
    if kind == "none":          # no helm: two lights over an empty collar
        eyes_at = (c.y - ry * 0.5, e.z, 1.7)
    elif kind == "lamp":        # a lantern where its helm was: six panes of the field in a frame of brass
        R, Hh = rx * 1.05 * size, rz * 0.78 * size
        ph = pi / 6
        panes = g.lathe([(R * 0.86, -Hh), (R * 0.98, -Hh * 0.2), (R * 0.98, Hh * 0.5), (R * 0.84, Hh)], n=6, centre=c, phase=ph)
        bars = None
        for i in range(6):
            aa = ph + pi / 3 * i
            d = Vector((math.cos(aa), math.sin(aa), 0))
            bars = g.merge(bars, g.tube([c + d * R * 0.9 - Z * Hh, c + d * R * 1.03 - Z * Hh * 0.2, c + d * R * 1.03 + Z * Hh * 0.5, c + d * R * 0.88 + Z * Hh], R * 0.075, n=4))
        for zz, kk in ((-Hh, 0.9), (Hh, 0.88), (-Hh * 0.2, 1.03)):
            bars = g.merge(bars, _hoop(c + Z * zz, R * kk, R * kk, R * 0.065, u=X, v=Y, n=6, sides=4))
        P.add("lamp_frame", bars, trim, "head", smooth=False)
        P.add("lamp_roof", g.lathe([(R * 1.2, Hh), (R * 0.62, Hh * 1.42), (R * 0.16, Hh * 1.7), (R * 0.22, Hh * 1.9), (0.0, Hh * 2.0)], n=6, centre=c, phase=ph), mat("accent"), "head", smooth=False)
        P.add("lamp_foot", g.lathe([(R * 0.5, -Hh * 1.5), (R * 0.95, -Hh * 1.12), (R * 0.9, -Hh)], n=6, centre=c, phase=ph), main, "head", smooth=False)
        P.move("pulse", "lamp", [(panes, field("lamp", 2.6), True)], c, "head")
        H["top"] = c + Z * Hh * 2.0
        # its eyes: two darker flecks in the front pane, that shut
        for s, tag in ((1, "l"), (-1, "r")):
            q = Vector((s * R * 0.3, c.y - R * 0.9, c.z + Hh * 0.2))
            P.move("blink", "eye", [(g.ico(q, R * 0.13, sub=1, scale=(1.0, 0.4, 1.3)), mat("eye_white"), True)], q, "head", side=tag)
        return H
    else:
        # the dark inside it
        P.add("helm_dark", g.ico(c, 1.0, sub=2, scale=(rx * 0.9, ry * 0.9, rz * 0.9)), mat("void"), "head", smooth=True)
        skull_low = ez + a
        if kind in ("pot", "armet", "armet-open"):
            put("helm_skull", spun([(rx, skull_low), (rx * 1.03, skull_low + 0.3 * hr), (rx * 0.92, rz * 0.6), (rx * 0.58, rz * 0.93), (0.0, rz * 1.02)], c, n=12, sy=sy), main)
            if kind == "pot":
                put("helm_chin", spun([(rx * 0.88, -rz * 0.98), (rx * 1.02, -rz * 0.55), (rx * 1.03, ez - a)], c, n=12, sy=sy), main)
                band(ez - a, skull_low)
                put("helm_rim", _hoop(c + Z * (-rz * 0.98), rx * 0.9, ry * 0.9, 0.05 * hr, u=X, v=Y, n=12, sides=3), trim)
            elif kind == "armet":       # a visor drawn to a point: it leads with it
                put("helm_visor", spun([(rx * 0.5, -rz * 1.02), (rx * 0.86, -rz * 0.72), (rx * 0.98, (ez - a - rz) / 2), (rx * 0.99, ez - a)], c, n=12, sy=sy,
                                       bulge=lambda aa, i: 1.0 + (0.0, 0.22, 0.5, 0.16)[i] * front(aa) ** 4), light)
                band(ez - a, skull_low)
            else:                       # the visor up, over nothing
                put("helm_bevor", spun([(rx * 0.5, -rz * 1.02), (rx * 0.9, -rz * 0.72), (rx * 0.98, ez - a)], c, n=12, sy=sy), main)
                band(ez - a, skull_low, open_=0.6)
                b0 = c + Vector((0, -ry * 0.98, skull_low + 0.1 * hr))
                put("helm_visor", g.tongue([b0, b0 + Vector((0, -0.55 * hr, 0.4 * hr)), b0 + Vector((0, -1.2 * hr, 0.5 * hr))], [1.5 * hr, 1.3 * hr, 0.3 * hr], thick=0.16, normal=Z), light)
        elif kind == "great":           # a barrel, flat on top
            put("helm_skull", spun([(rx * 0.98, skull_low), (rx * 1.0, rz * 0.72), (rx * 0.9, rz * 0.98), (0.0, rz * 1.0)], c, n=12, sy=sy), main)
            put("helm_chin", spun([(rx * 0.86, -rz * 1.2), (rx * 0.98, ez - a)], c, n=12, sy=sy), main)
            band(ez - a, skull_low, k=1.0)
            put("helm_nasal", g.box(c + Vector((0, -ry * 1.0, ez - 0.3 * hr)), (0.16 * hr, 0.1 * hr, 2 * a + 1.3 * hr)), trim)
            put("helm_brace", _hoop(c + Z * (skull_low + 0.02 * hr), rx * 1.0, ry * 1.0, 0.055 * hr, u=X, v=Y, n=12, sides=3), trim)
        elif kind == "kettle":          # a brimmed iron hat, and an open dark under it
            zb = skull_low + 0.12 * hr
            put("helm_skull", spun([(rx * 0.98, zb), (rx * 0.97, zb + 0.3 * hr), (rx * 0.7, rz * 0.82), (0.0, rz * 1.0)], c, n=12, sy=sy), main)
            put("helm_brim", spun([(rx * 1.85, zb - 0.2 * hr), (rx * 1.88, zb - 0.14 * hr), (rx * 0.98, zb + 0.12 * hr)], c, n=14, sy=1.0), light)
            band(-rz * 0.9, zb, open_=0.62, k=0.99, material=light)
        elif kind == "sallet":          # smooth and shut, with a tail behind
            put("helm_skull", spun([(rx * 1.0, skull_low - 0.02 * hr), (rx * 1.03, skull_low + 0.3 * hr), (rx * 0.9, rz * 0.62), (rx * 0.5, rz * 0.94), (0.0, rz * 1.0)], c, n=12, sy=sy,
                                   bulge=lambda aa, i: 1.0 + (0.1, 0.05, 0, 0, 0)[i] * front(aa) ** 2), main)
            put("helm_bevor", spun([(rx * 0.6, -rz * 1.05), (rx * 0.92, -rz * 0.6), (rx * 1.0, ez - a)], c, n=12, sy=sy, bulge=lambda aa, i: 1.0 + (0, 0.1, 0.12)[i] * front(aa) ** 2), light)
            band(ez - a, skull_low)
            t0 = c + Vector((0, ry * 0.9, ez))
            put("helm_tail", g.tongue([t0, t0 + Vector((0, 0.5 * hr, -0.5 * hr)), t0 + Vector((0, 1.3 * hr, -0.75 * hr))], [1.7 * hr, 1.5 * hr, 0.5 * hr], thick=0.14, normal=Z), main)
        elif kind == "hood":            # a hood of its Path's colour drawn over the helm
            cloth = mat("accent_dark")
            put("hood", spun([(rx * 1.1, skull_low), (rx * 1.14, skull_low + 0.3 * hr), (rx * 1.0, rz * 0.7), (rx * 0.5, rz * 1.04), (0.0, rz * 1.12)], c, n=12, sy=sy * 1.06,
                             bulge=lambda aa, i: 1.0 + (0.2, 0.1, 0, 0, 0)[i] * front(aa) ** 2), cloth, True)
            put("hood_fall", pd.drape((c.x, c.y, 0), lambda t_: (rx * (1.1 + 0.25 * t_), ry * (1.12 + 0.3 * t_)), [c.z + skull_low + 0.05, c.z - rz * 0.4, P.armz + 0.02], -pi * 0.7, pi * 0.7, thick=0.04, n=11), cloth, True)
            put("helm_chin", spun([(rx * 0.7, -rz * 1.0), (rx * 0.96, ez - a)], c, n=12, sy=sy), main)
            put("hood_edge", _hoop(c + Vector((0, -ry * 0.2, skull_low + 0.02 * hr)), rx * 1.12, ry * 1.1, 0.05 * hr, u=X, v=Y, n=12, sides=3), mat("accent"), True)
            H["top"] = c + Z * rz * 1.12
    # its eyes: the field's light, in the dark; and its brow, which is the edge of the visor
    one = spec.get("eyes") == "one"
    gaze = float(spec.get("gaze", 0.25))
    if eyes_at:
        y_eye, z_eye, big = eyes_at
    else:
        y_eye, z_eye, big = None, e.z, {"armet-open": 1.3, "kettle": 1.2, "hood": 1.15}.get(kind, 1.0)
    r = 0.2 * hr * big * (1.15 if P.level == 1 else 1.0)
    ex = e.x * (1.25 if kind != "none" else 1.3)
    for s, tag in ((1, "l"), (-1, "r")):
        x = 0.0 if one else s * ex + gaze * 0.28 * ex
        if one and s < 0:
            break
        if y_eye is None:
            q = 1.0 - (x / (rx * 0.9)) ** 2 - ((z_eye - c.z) / (rz * 0.9)) ** 2
            y = c.y - ry * 0.9 * math.sqrt(max(0.05, q)) - r * 0.2
        else:
            y = y_eye
        p = Vector((x, y, z_eye))
        P.move("blink", "eye", [(g.ico(p, r * (1.5 if one else 1.0), sub=1, scale=(1.5 if one else 1.0, 0.5, 1.0)), field("eyes", 3.6), True)], p, "head", side=tag)
    brow = spec.get("brow") or "level"
    if kind not in ("none", "kettle") and brow != "none":
        thm = 0.95
        pts = []
        for i in range(7):
            th = -thm + 2 * thm * i / 6
            u = abs(th) / thm
            dz = {"stern": 0.3 * u - 0.16, "raised": 0.26 * (1 - u) - 0.02, "soft": -0.14 * u + 0.08}.get(brow, 0.0) * hr
            kk = 1.12 if kind == "hood" else 1.045
            pts.append(c + Vector((rx * kk * math.sin(th), -ry * kk * math.cos(th), ez + a + dz)))
        put("helm_brow", g.tube(pts, [0.05 * hr, 0.075 * hr, 0.085 * hr, 0.09 * hr, 0.085 * hr, 0.075 * hr, 0.05 * hr], n=4), trim if kind != "hood" else mat("accent_light"))
    return H


def crest(P, spec, H):
    c, rx, ry, rz, top, hr = H["c"], H["rx"], H["ry"], H["rz"], H["top"], P.hr
    tilt = H.get("tilt")
    for kind, size, word in each(spec.get("crest")):
        if kind in ("tuft", "plume"):
            items = []
            n = 3 if kind == "tuft" else 5
            L = hr * (0.55 if kind == "tuft" else 0.95) * size
            for i in range(n):
                dx = (i - (n - 1) / 2) / max(1, n - 1)
                lift = 1.0 - 0.5 * abs(dx)
                pts = [top - Z * 0.05 * hr, top + Vector((dx * 0.3, 0.3, 0.95 * lift)) * L, top + Vector((dx * 0.7, 1.05, 1.05 * lift)) * L, top + Vector((dx * 0.9, 1.9, 0.35 * lift)) * L, top + Vector((dx, 2.3, -0.3)) * L]
                items.append((g.tongue(pts, [0.22 * L, 0.5 * L, 0.56 * L, 0.4 * L, 0.05 * L], thick=0.3, normal=X), mat("accent" if i % 2 == 0 else "accent_light"), True))
            P.move("sway", "plume", items, top, "head")
            P.add("plume_cup", turned(g.lathe([(0.1 * hr, -0.05 * hr), (0.14 * hr, 0.1 * hr), (0.08 * hr, 0.2 * hr)], n=6, centre=top), c, tilt) if tilt else
                  g.lathe([(0.1 * hr, -0.05 * hr), (0.14 * hr, 0.1 * hr), (0.08 * hr, 0.2 * hr)], n=6, centre=top), P.material("trim"), "head", smooth=False)
        elif kind in ("comb", "fin"):
            # a plate standing along the crown, front to back
            h = hr * (0.3 if kind == "comb" else 0.62) * size
            pts, ws = [], []
            for i in range(6):
                th = -0.9 + 2.5 * i / 5          # from over the brow, back over the crown
                rr = 1.0 + (h / 2) / rz
                pts.append(c + Vector((0, ry * rr * math.sin(th), rz * rr * math.cos(th))))
                ws.append(h * (0.4, 0.9, 1.0, 1.0, 0.8, 0.2)[i] * (1.0 if kind == "comb" else (0.5, 0.8, 1.1, 1.4, 1.2, 0.3)[i]))
            P.add("crest_" + kind, g.tongue(pts, ws, thick=0.16, normal=X), P.material("under") if kind == "comb" else mat("accent"), "head", smooth=False)
        elif kind == "ram":         # a ram's horns, curled at the sides of the helm
            geo = None
            for s in (1, -1):
                pts = g.spiral(c + Vector((s * (rx + 0.3 * hr), 0.25 * hr, 0.0)), 0.8 * hr * size, 0.3 * hr * size, 1.2, s * 0.6 * hr * size, n=12, axis=X * s, start=pi * 0.5)
                geo = g.merge(geo, g.tube(pts, [0.34 * hr * size * (1.0 - 0.85 * i / 12) for i in range(13)], n=6))
            P.add("horns", geo, mat("horn_ram"), "head", smooth=True)
        elif kind == "horns":       # great horns, swung forward
            geo = None
            for s in (1, -1):
                b0 = c + Vector((s * rx * 0.85, 0, 0.3 * hr))
                pts = [b0, b0 + Vector((s * 0.7, -0.1, 0.35)) * hr * size, b0 + Vector((s * 1.0, -0.9, 0.6)) * hr * size, b0 + Vector((s * 0.8, -1.9, 0.72)) * hr * size, b0 + Vector((s * 0.5, -2.7, 1.0)) * hr * size]
                geo = g.merge(geo, g.tube(pts, [0.3 * hr, 0.27 * hr, 0.2 * hr, 0.12 * hr, 0.02 * hr], n=6))
            P.add("horns", geo, mat("horn_ram"), "head", smooth=True)
        elif kind == "crenels":     # battlements round the crown
            geo = None
            for i in range(8):
                aa = 2 * pi * (i + 0.5) / 8
                geo = g.merge(geo, g.box(c + Vector((rx * 0.9 * math.cos(aa), ry * 0.9 * math.sin(aa), rz * 1.08)), (0.4 * hr, 0.26 * hr, 0.44 * hr), rot=(0, 0, aa + pi / 2)))
            P.add("crenels", geo, P.material("under"), "head", smooth=False)
        elif kind == "candle":      # one small flame of the field where a plume was
            P.add("candle_cup", g.lathe([(0.2 * hr, -0.04 * hr), (0.24 * hr, 0.1 * hr), (0.12 * hr, 0.14 * hr)], n=6, centre=top), P.material("trim"), "head", smooth=False)
            P.move("flick", "flame", [(g.blade(top + Z * 0.1 * hr, top + Z * 0.95 * hr * size, 0.42 * hr, normal=Y, belly=0.34, thick=0.14 * hr), field("flame", 3.4), True)], top + Z * 0.1 * hr, "head")
        elif kind == "cairn":       # flat stones, left on its hat by people passing
            geo = None
            for i, (dx, dy, rr) in enumerate(((0.0, 0.0, 0.62), (0.1, 0.05, 0.5), (-0.06, -0.04, 0.4), (0.04, 0.02, 0.3), (0.0, 0.0, 0.2))):
                geo = g.merge(geo, g.ico(top + Vector((dx * hr, dy * hr, (0.1 + 0.26 * i) * hr * size)), rr * hr * size, sub=1, scale=(1.0, 0.9, 0.3), rot=(0.1 * i, 0.07 * i, 0.9 * i)))
            P.add("cairn", geo, mat("stone_cairn"), "head", smooth=False)


# ======================================================================================
# What is on its breast, at its hips, on its shoulders
# ======================================================================================

def chest(P, spec):
    kind, size, _ = opt(spec.get("chest"))
    if not kind:
        return
    t, th = P.t, P.thick
    main, light, trim = P.material("main"), P.material("under"), P.material("trim")
    z0, z1 = P.waist + 0.05 * t, P.neckz - 0.12 * t
    zm = (z0 + z1) / 2
    if kind == "keel":          # the ridge down a knight's breastplate
        P.add("keel", g.tongue([(0, P.yf(z1) + 0.0, z1), (0, P.yf(zm + 0.1 * t) - 0.05 * t, zm + 0.1 * t), (0, P.yf(z0) - 0.0, z0)], [0.08 * t, 0.2 * t, 0.06 * t], thick=0.5, normal=X), light, "chest", smooth=False)
    elif kind == "hoops":       # banded like a barrel, in its Path's colour
        for i, zz in enumerate((z0 + 0.03 * t, zm, z1 - 0.06 * t)):
            hw, hd, yo = P.ring(zz)
            P.add("hoop_%d" % i, _hoop((0, yo, zz), hw + th + 0.015, hd + th + 0.015, 0.05 * t, u=X, v=Y, n=14, sides=4), mat("accent" if i != 1 else "accent_dark"), "chest", smooth=False)
    elif kind == "prow":        # a wedge of iron standing from the breastplate
        w = 0.55 * t * size
        pts = [(0, P.yf(z1) - w * 0.1, z1 + 0.05 * t), (0, P.yf(zm) - w * 0.42, zm + 0.12 * t), (0, P.yf(z0) - w * 0.3, z0 - 0.05 * t), (0, P.yf(z0) + 0.0, z0 - 0.3 * t)]
        P.add("prow", g.tongue(pts, [w * 0.4, w, w * 0.8, w * 0.1], thick=0.8, normal=X), main, "chest", smooth=False)
        edge = [Vector(p) + Vector((0, -w * (0.2, 0.47, 0.37, 0.05)[i], 0)) for i, p in enumerate(pts)]
        P.add("prow_edge", g.tube(edge, [0.03 * t, 0.05 * t, 0.045 * t, 0.02 * t], n=4), mat("accent"), "chest", smooth=False)
        for i, zz in enumerate((z0 + 0.03 * t, z1 - 0.06 * t)):
            hw, hd, yo = P.ring(zz)
            P.add("hoop_%d" % i, _hoop((0, yo, zz), hw + th + 0.015, hd + th + 0.015, 0.05 * t, u=X, v=Y, n=14, sides=4), mat("accent"), "chest", smooth=False)
    elif kind == "hole":        # torn open, and nobody was ever in it
        x = 0.16 * t
        zz = zm + 0.12 * t
        p = Vector((x, P.yf(zz, x) - 0.012, zz))
        P.add("hole", g.ico(p, 0.2 * t, sub=1, scale=(1.0, 0.12, 0.85), rot=(0, 0.4, 0)), mat("void"), "chest", smooth=True)
        P.move("pulse", "heart", [(g.ico(p + Vector((0, -0.02, 0)), 0.075 * t, sub=1, scale=(1, 0.5, 1)), field("heart", 3.2), True)], p, "chest")
        tear = None
        for i in range(6):
            aa = 2 * pi * i / 6 + 0.3
            d = Vector((math.cos(aa), 0, math.sin(aa)))
            tear = g.merge(tear, g.blade(p + d * 0.17 * t, p + d * 0.3 * t + Vector((0, -0.07 * t, 0)), 0.14 * t, normal=Y, belly=0.3))
        P.add("tear", tear, light, "chest", smooth=False)
        for i, zz in enumerate((z0 + 0.03 * t,)):
            hw, hd, yo = P.ring(zz)
            P.add("hoop_%d" % i, _hoop((0, yo, zz), hw + th + 0.015, hd + th + 0.015, 0.05 * t, u=X, v=Y, n=14, sides=4), mat("accent_dark"), "chest", smooth=False)
        # and the dents of every blow it kept
        dent = None
        for dx, dz in ((-0.2, 0.2), (-0.12, -0.12), (0.22, -0.16)):
            zz = zm + dz * t
            dent = g.merge(dent, g.ico((dx * t, P.yf(zz, dx * t) - 0.005, zz), 0.08 * t, sub=1, scale=(1.0, 0.1, 0.8)), )
        P.add("dents", dent, mat("iron_plate_dark"), "chest", smooth=True)
    elif kind in ("grate", "shut-door"):
        zz = z0 + 0.2 * t
        w, h = 0.56 * t * size, 0.4 * t * size
        y = P.yf(zz) - 0.05 * t
        frame = None
        for dx, dz, sx_, sz_ in ((0, h / 2, w + 0.08 * t, 0.07 * t), (0, -h / 2, w + 0.08 * t, 0.07 * t), (w / 2, 0, 0.07 * t, h), (-w / 2, 0, 0.07 * t, h)):
            frame = g.merge(frame, g.box((dx, y, zz + dz), (sx_, 0.1 * t, sz_)))
        P.add("grate_frame", frame, trim, "chest", smooth=False)
        if kind == "grate":     # a fire of the field in the empty of it, behind bars
            P.add("grate_dark", g.box((0, y + 0.02 * t, zz), (w, 0.06 * t, h)), mat("void"), "chest", smooth=False)
            P.move("pulse", "fire", [(g.ico((0, y + 0.0, zz - h * 0.08), 1.0, sub=1, scale=(w * 0.4, 0.02 * t, h * 0.36)), field("fire", 3.0), True)], (0, y, zz), "chest")
            bars = None
            for i in range(4 if size < 1.3 else 5):
                x = -w / 2 + w * (i + 0.5) / (4 if size < 1.3 else 5)
                bars = g.merge(bars, g.tube([(x, y - 0.04 * t, zz - h / 2), (x, y - 0.04 * t, zz + h / 2)], 0.028 * t, n=4))
            P.add("grate_bars", bars, mat("iron_plate_dark"), "chest", smooth=False)
        else:                   # shut, and a thread of light round the door
            P.add("door_plate", g.box((0, y - 0.01 * t, zz), (w * 0.9, 0.08 * t, h * 0.86)), light, "chest", smooth=False)
            seam = None
            for dx, dz, sx_, sz_ in ((0, h * 0.45, w * 0.94, 0.03 * t), (0, -h * 0.45, w * 0.94, 0.03 * t), (w * 0.47, 0, 0.03 * t, h * 0.9), (-w * 0.47, 0, 0.03 * t, h * 0.9)):
                seam = g.merge(seam, g.box((dx, y - 0.0, zz + dz), (sx_, 0.07 * t, sz_)))
            P.move("pulse", "seam", [(seam, field("seam", 3.0), False)], (0, y, zz), "chest")
            P.add("door_latch", g.box((w * 0.3, y - 0.06 * t, zz), (0.16 * t, 0.05 * t, 0.06 * t)), mat("accent"), "chest", smooth=False)
        for i, zz2 in enumerate((z1 - 0.06 * t,)):
            hw, hd, yo = P.ring(zz2)
            P.add("hoop_%d" % i, _hoop((0, yo, zz2), hw + th + 0.015, hd + th + 0.015, 0.05 * t, u=X, v=Y, n=14, sides=4), mat("accent"), "chest", smooth=False)
    elif kind == "barred-door":     # one great door across its whole front, barred, a light in the keyhole
        w = 2 * (P.sx + 0.22 * t)
        zb, zt = P.kneez + 0.02, P.neckz + 0.12 * t
        y = min(P.yf(zm), P.yf(z0)) - 0.2 * t
        zc = (zb + zt) / 2
        P.add("door", g.box((0, y, zc), (w, 0.1 * t, zt - zb)), mat("wood_door"), "chest", smooth=False)
        P.add("door_paint", g.box((0, y - 0.035 * t, zc), (w * 0.86, 0.05 * t, (zt - zb) * 0.9)), mat("accent"), "chest", smooth=False)
        iron = None
        for zz in (zb + 0.12 * t, zt - 0.12 * t):
            iron = g.merge(iron, g.box((0, y - 0.05 * t, zz), (w * 1.02, 0.06 * t, 0.12 * t)))
        iron = g.merge(iron, g.box((0, y - 0.05 * t, zc), (0.07 * t, 0.06 * t, zt - zb)))
        P.add("door_iron", iron, mat("iron_plate_dark"), "chest", smooth=False)
        P.add("door_bar", g.box((0, y - 0.1 * t, zc + 0.16 * t), (w * 1.12, 0.1 * t, 0.16 * t)), mat("wood_pole"), "chest", smooth=False)
        for s in (1, -1):
            P.add("door_staple_%d" % s, g.box((s * w * 0.4, y - 0.11 * t, zc + 0.16 * t), (0.1 * t, 0.14 * t, 0.26 * t)), trim, "chest", smooth=False)
        kp = Vector((0.0, y - 0.085 * t, zc - 0.2 * t))
        P.add("lock", g.box(kp + Vector((0, 0.01 * t, 0)), (0.3 * t, 0.06 * t, 0.36 * t)), trim, "chest", smooth=False)
        P.move("pulse", "keyhole", [(g.merge(g.ico(kp + Vector((0, -0.03 * t, 0.05 * t)), 0.05 * t, sub=1, scale=(1, 0.4, 1)), g.box(kp + Vector((0, -0.03 * t, -0.04 * t)), (0.045 * t, 0.02 * t, 0.14 * t))), field("keyhole", 3.4), True)], kp, "chest")


def fauld(P, spec):
    kind, size, _ = opt(spec.get("fauld"))
    if not kind:
        return
    t, th = P.t, P.thick
    main, light = P.material("main"), P.material("under")
    hw, hd, yo = P.ring(P.waist)
    hw, hd = hw + th, hd + th

    def tier(z0, z1, k0, k1, material, name):
        P.add(name, spun([(hw * k0, z0), (hw * k1, z1), (hw * k1 * 0.96, z1)], (0, yo, 0), n=14, sy=hd / hw), material, "hips")
    tier(P.waist + 0.04 * t, P.hipz - 0.1 * t, 1.0, 1.14, main, "fauld")
    P.add("belt", _hoop((0, yo, P.waist + 0.02 * t), hw * 1.02, hd * 1.02, 0.04 * t, u=X, v=Y, n=14, sides=4), mat("leather_strap"), "hips", smooth=True)
    if kind == "tassets":       # a plate hung over each thigh
        for s, tag in ((1, "l"), (-1, "r")):
            x = abs(P.J["upperleg." + tag].x) * s
            zt, zb = P.hipz - 0.08 * t, P.kneez + 0.3 * (P.hipz - P.kneez)
            y = yo - hd * 1.12
            out = [(-0.17, 0.0), (0.17, 0.0), (0.19, -0.6), (0.0, -1.0), (-0.19, -0.6)]
            P.add("tasset_" + tag, slab([(a * t, b * (zt - zb)) for a, b in out], (x, y, zt), X, Z, -Y, 0.035 * t), light, "upperleg." + tag)
            P.add("tasset_edge_" + tag, slab([(a * t, b * (zt - zb)) for a, b in shrunk(out, 0.6)], (x, y - 0.035 * t, zt - 0.06 * t), X, Z, -Y, 0.012 * t), mat("accent"), "upperleg." + tag)
    elif kind == "apron":       # one heavy plate before its legs
        zt, zb = P.waist - 0.02 * t, P.kneez + 0.0
        y = yo - hd * 1.16
        w = hw * 0.8
        out = [(-w, 0.0), (w, 0.0), (w * 0.9, -(zt - zb) * 0.8), (0.0, -(zt - zb)), (-w * 0.9, -(zt - zb) * 0.8)]
        P.add("apron", slab(out, (0, y, zt), X, Z, -Y, 0.07 * t), main, "hips")
        P.add("apron_band", slab(shrunk(out, 0.7), (0, y - 0.07 * t, zt - 0.08 * t), X, Z, -Y, 0.015 * t), mat("accent"), "hips")
    elif kind == "skirt":       # skirts of laced plates, a tier wider than the last
        n = 3
        zt, zb = P.hipz - 0.06 * t, P.kneez + (0.35 - 0.25 * (size - 1.0)) * (P.hipz - P.kneez)
        for i in range(n):
            za, zc = zt + (zb - zt) * i / n, zt + (zb - zt) * (i + 1) / n
            k0 = 1.1 + 0.16 * i * size
            tier(za + 0.03 * t, zc, k0, k0 + 0.2 * size, light if i % 2 else main, "skirt_%d" % i)
            P.add("skirt_lace_%d" % i, _hoop((0, yo, zc + 0.02 * t), hw * (k0 + 0.2 * size) * 1.0, hd * (k0 + 0.2 * size) * 1.0, 0.03 * t, u=X, v=Y, n=14, sides=3), mat("accent" if i % 2 == 0 else "accent_light"), "hips", smooth=False)


def pauldrons(P, spec):
    kind, size, _ = opt(spec.get("pauldrons"))
    if not kind:
        return
    t = P.t
    main, light, trim = P.material("main"), P.material("under"), P.material("trim")
    for s, tag in ((1, "l"), (-1, "r")):
        cs = Vector((s * (P.sx + 0.05 * t), P.army, P.armz + 0.09 * t))
        if kind in ("cups", "great"):
            R = 0.2 * t * size
            P.add("pauldron_" + tag, g.ico(cs, R, sub=1, scale=(1.3, 1.15, 0.72), rot=(0, s * -0.4, 0)), main, "chest", smooth=False)
            P.add("pauldron_rim_" + tag, _hoop(cs + Vector((s * 0.04 * t, 0, -0.05 * t)), R * 1.22, R * 1.1, 0.03 * t, u=Y, v=Vector((s * 0.8, 0, -0.55)).normalized(), n=10, sides=3), mat("accent"), "chest", smooth=False)
            if kind == "great":     # guards that stand from its shoulders to the helm
                b0 = cs + Vector((-s * 0.02 * t, 0, 0.08 * t))
                P.add("guard_" + tag, g.tongue([b0, b0 + Vector((-s * 0.02, 0, 0.3)) * t * size, b0 + Vector((s * 0.06, 0, 0.62)) * t * size], [0.36 * t * size, 0.44 * t * size, 0.2 * t * size], thick=0.12, normal=X), light, "chest", smooth=False)
                P.add("guard_edge_" + tag, g.tube([b0 + Vector((s * 0.06, -0.1, 0.62)) * t * size, b0 + Vector((s * 0.06, 0.1, 0.62)) * t * size], 0.03 * t, n=4), mat("accent"), "chest", smooth=False)
        elif kind in ("slab", "slab-one", "spikes"):
            if kind == "slab-one" and s < 0:
                continue
            R = Matrix.Rotation(s * 0.5, 3, "Y")
            b = cs + Vector((s * 0.0 * t, 0, 0.0))
            rr = 0.33 * t * size
            P.add("pauldron_" + tag, g.ico(b, rr, sub=1, scale=(1.05, 1.2, 0.86), rot=(0, s * 0.5, 0)), main, "chest", smooth=False)
            P.add("pauldron_rim_" + tag, _hoop(b + R @ Vector((s * 0.06 * t, 0, -0.1 * t)), rr * 1.16, rr * 1.0, 0.05 * t, u=Y, v=R @ Vector((s * 0.55, 0, -0.84)), n=10, sides=4), mat("accent"), "chest", smooth=False)
            P.add("pauldron_rivets_" + tag, g.merge(*[g.ico(b + R @ Vector((s * 0.1 * t, dy * t * size, rr * 0.74)), 0.045 * t, sub=0) for dy in (-0.16, 0.0, 0.16)]), trim, "chest", smooth=False)
            if kind == "spikes":
                P.add("spike_" + tag, g.cone(b + R @ Vector((0, 0, 0.1 * t)), b + R @ Vector((s * 0.12 * t, 0, 0.62 * t * size)), 0.13 * t, n=5), light, "chest", smooth=False)
        elif kind == "towers":      # a round turret on each shoulder
            b = cs + Vector((s * 0.08 * t, 0, -0.02 * t))
            r_, h = 0.25 * t * size, 0.5 * t * size
            P.add("turret_" + tag, g.lathe([(r_ * 0.9, 0.0), (r_, h * 0.75), (r_ * 1.15, h * 0.8), (r_ * 1.15, h), (r_ * 0.8, h)], n=8, centre=b), main, "chest", smooth=False)
            geo = None
            for i in range(4):
                aa = 2 * pi * i / 4 + pi / 4
                geo = g.merge(geo, g.box(b + Vector((r_ * 0.98 * math.cos(aa), r_ * 0.98 * math.sin(aa), h * 1.12)), (0.17 * t, 0.12 * t, 0.16 * t), rot=(0, 0, aa + pi / 2)))
            P.add("turret_top_" + tag, geo, light, "chest", smooth=False)
            P.add("turret_band_" + tag, _hoop(b + Z * h * 0.4, r_ * 0.98, r_ * 0.98, 0.035 * t, u=X, v=Y, n=8, sides=3), mat("accent"), "chest", smooth=False)
        elif kind == "tiles":       # roof tiles in its Path's colour, laid over each shoulder
            geo = None
            for i in range(3):
                R = Matrix.Rotation(s * -(0.25 + 0.3 * i), 3, "Y")
                geo = g.merge(geo, g.box(cs + Vector((s * (0.02 + 0.17 * i) * t * size, 0, (0.16 - 0.1 * i) * t)), (0.3 * t * size, (0.66 - 0.04 * i) * t * size, 0.07 * t), rot=R))
            P.add("tiles_" + tag, geo, mat("accent"), "chest", smooth=False)
            P.add("tiles_ridge_" + tag, g.tube([cs + Vector((s * -0.1 * t, -0.34 * t * size, 0.2 * t)), cs + Vector((s * -0.1 * t, 0.34 * t * size, 0.2 * t))], 0.06 * t, n=5), mat("accent_dark"), "chest", smooth=False)
        elif kind == "lames":       # flat laced plates, hung from the shoulder
            for i in range(3):
                R = Matrix.Rotation(s * (0.75 + 0.22 * i), 3, "Y")
                b = cs + Vector((s * (-0.02 + 0.09 * i) * t * size, 0, (0.06 - 0.16 * i) * t * size))
                P.add("lame_%s_%d" % (tag, i), g.box(b, (0.3 * t * size, (0.46 + 0.03 * i) * t * size, 0.05 * t), rot=R), light if i % 2 else main, "chest", smooth=False)
                P.add("lame_lace_%s_%d" % (tag, i), g.box(b + R @ Vector((s * 0.14 * t * size, 0, 0.0)), (0.05 * t, (0.48 + 0.03 * i) * t * size, 0.06 * t), rot=R), mat("accent" if i % 2 == 0 else "accent_light"), "chest", smooth=False)


# ======================================================================================
# What it carries (drawn as the hand hangs: the fist at the origin, up +Z, forward -Y, away
# from the body +X, for either hand)
# ======================================================================================

def hands(P, spec):
    t = P.t
    for side, key in (("l", "left"), ("r", "right")):
        kind, size, word = opt(spec.get(key))
        if not kind:
            continue
        k = (0.5 + 0.5 * t) * size
        slot = P.J["handslot." + side]
        gz = -(P.armz - (abs(slot.x) - P.sx)) + 0.03        # the ground, as the hand hangs
        mid = -(P.sx + 0.04)                               # the middle of its body, as the hand hangs
        acc, pale, dark = "accent", "accent_pale", "accent_dark"
        main, light, trim = P.material("main"), P.material("under"), P.material("trim")
        if kind == "lid":           # a pot-lid for a shield
            c = Vector((0.1 * k, -0.3 * k, 0.1 * k))
            P.grip(side, kind, [(_disc(c, 0.46 * k, normal=Y, thick=0.06 * k, n=12), "wood_shield", False), (_hoop(c + Y * -0.02 * k, 0.46 * k, 0.46 * k, 0.045 * k, u=X, v=Z, n=12, sides=4), light, False),
                                (g.ico(c + Y * -0.07 * k, 0.12 * k, sub=1, scale=(1, 0.7, 1)), trim, False)])
        elif kind == "door":
            # half an oak door before each arm: it stands on the ground, painted its Path's colour between straps of iron
            s = 1.0 if side == "l" else -1.0
            th = 0.1 * k
            zt = P.armz + 0.12 * t
            y = min(P.yf(P.chestz), P.yf(P.waist)) - 0.4 * t
            x0, x1 = 0.012 * t, P.sx + 0.62 * t
            cx, w = s * (x0 + x1) / 2, x1 - x0
            P.add("door_" + side, g.box((cx, y, zt / 2 + 0.015), (w, th, zt - 0.03)), mat("wood_door"), "chest", smooth=False)
            P.add("door_paint_" + side, g.box((cx, y - th / 2 - 0.012 * k, zt / 2 + 0.015), (w * 0.86, 0.03 * k, zt * 0.9)), mat(acc), "chest", smooth=False)
            iron = None
            for zz in (0.14 * zt, 0.5 * zt, 0.86 * zt):
                iron = g.merge(iron, g.box((cx, y - th / 2 - 0.03 * k, zz), (w * 1.02, 0.05 * k, 0.13 * k)))
            P.add("door_iron_" + side, iron, mat("iron_plate_dark"), "chest", smooth=False)
            P.add("door_ring_" + side, _hoop((s * (x0 + 0.2 * t), y - th / 2 - 0.07 * k, zt * 0.42), 0.09 * k, 0.09 * k, 0.022 * k, u=X, v=Z, n=8, sides=3), trim, "chest", smooth=False)
        elif kind in ("tower", "wall"):
            # a shield taller than itself, planted before it: it stands on the ground, and the hand rests on its rim
            s = 1.0 if side == "l" else -1.0
            th = 0.08 * k
            zt = P.armz + (0.1 if kind == "tower" else 0.3) * t
            y = min(P.yf(P.chestz), P.yf(P.waist)) - 0.42 * t
            if kind == "tower":
                x0, x1 = 0.02 * t, P.sx + 0.62 * t
                out = [(x0, 0.03), (x1, 0.03), (x1, zt - 0.22 * t), (x1 - 0.25 * t, zt), (x0 + 0.25 * t, zt), (x0, zt - 0.22 * t)]
            else:
                x0, x1 = 0.012 * t, P.sx + 0.7 * t
                out = [(x0, 0.03), (x1, 0.03), (x1, zt), (x0 + 0.3 * t, zt), (x0 + 0.3 * t, zt - 0.42 * t), (x0, zt - 0.42 * t)]
            out = [(s * a, b) for a, b in out]
            cx = sum(a for a, b in out) / len(out)
            P.add(kind + "_" + side, slab(out, (0, y, 0), X, Z, -Y, th), light, "chest", smooth=False)
            P.add(kind + "_face_" + side, slab(shrunk(out, 0.8), (0, y - th, 0), X, Z, -Y, 0.02 * k), mat(acc), "chest", smooth=False)
            if kind == "tower":     # a stripe down the middle of its face
                P.add("tower_stripe", g.box((cx, y - th - 0.025 * k, zt / 2), (0.2 * k, 0.02 * k, zt * 0.7)), mat(pale), "chest", smooth=False)
                P.add("tower_boss", g.ico((cx, y - th - 0.04 * k, zt * 0.6), 0.14 * k, sub=1, scale=(1, 0.6, 1)), trim, "chest", smooth=False)
            else:                   # bands across both leaves, and battlements along the top
                geo = None
                for zz in (zt * 0.3, zt * 0.62):
                    geo = g.merge(geo, g.box((cx, y - th - 0.025 * k, zz), (abs(x1 - x0) * 0.8, 0.02 * k, 0.14 * k)))
                P.add("wall_bands_" + side, geo, mat(pale), "chest", smooth=False)
                cr = None
                w = x1 - x0 - 0.3 * t
                for i in range(3):
                    cr = g.merge(cr, g.box((s * (x0 + 0.3 * t + w * (i + 0.5) / 3), y - th / 2, zt + 0.1 * k), (w / 5, th, 0.2 * k)))
                P.add("wall_crenels_" + side, cr, light, "chest", smooth=False)
        elif kind == "heater":
            y = -0.34 * k
            if kind == "heater":
                out = [(-0.72, 0.62), (0.4, 0.62), (0.42, 0.05), (0.22, -0.55), (-0.16, -0.95), (-0.54, -0.55), (-0.74, 0.05)]
                out = [(a * k, b * k) for a, b in out]
                th = 0.06 * k
            elif kind == "tower":
                x0, x1, zt = -0.95 * k, 0.4 * k, 1.05 * k
                out = [(x0, gz), (x1, gz), (x1, zt - 0.2 * k), (x1 - 0.25 * k, zt), (x0 + 0.25 * k, zt), (x0, zt - 0.2 * k)]
                th = 0.07 * k
            elif kind == "wall":
                x0, x1, zt = mid, 0.5 * k, 1.5 * k
                out = [(x0, gz), (x1, gz), (x1, zt), (x0 + 0.34 * k, zt), (x0 + 0.34 * k, zt - 0.5 * k), (x0, zt - 0.5 * k)]
                th = 0.08 * k
            else:
                x0, x1, zt = mid, 0.42 * k, 1.3 * k
                out = [(x0, gz), (x1, gz), (x1, zt), (x0, zt)]
                th = 0.1 * k
            body = "wood_door" if kind == "door" else light
            items = [(slab(out, (0, y, 0), X, Z, -Y, th), body, False)]
            cz = sum(b for a, b in out) / len(out)
            cx = sum(a for a, b in out) / len(out)
            if kind == "door":
                # painted its Path's colour between straps of iron
                x0_, x1_ = out[0][0], out[1][0]
                items.append((g.box(((x0_ + x1_) / 2, y - th - 0.012 * k, (gz + zt) / 2), ((x1_ - x0_) * 0.86, 0.03 * k, (zt - gz) * 0.92)), acc, False))
                iron = None
                for zz in (gz + 0.18 * k, (gz + zt) / 2, zt - 0.18 * k):
                    iron = g.merge(iron, g.box(((x0_ + x1_) / 2, y - th - 0.03 * k, zz), ((x1_ - x0_) * 1.02, 0.05 * k, 0.13 * k)))
                items.append((iron, "iron_plate_dark", False))
                items.append((_hoop((x0_ + 0.16 * k, y - th - 0.07 * k, (gz + zt) / 2 - 0.2 * k), 0.09 * k, 0.09 * k, 0.022 * k, u=X, v=Z, n=8, sides=3), trim, False))
            else:
                items.append((slab(shrunk(out, 0.8), (0, y - th, 0), X, Z, -Y, 0.02 * k), acc, False))
                if kind == "tower":     # a stripe down the middle of its face
                    items.append((g.box((cx, y - th - 0.025 * k, (gz + zt) / 2), (0.2 * k, 0.02 * k, (zt - gz) * 0.74)), pale, False))
                if kind == "wall":      # bands across both leaves, and battlements along the top
                    for zz in (gz + 0.5 * k, zt - 0.72 * k):
                        items.append((g.box((cx, y - th - 0.025 * k, zz), ((x1 - x0) * 0.8, 0.02 * k, 0.14 * k)), pale, False))
                    cr = None
                    for i in range(3):
                        cr = g.merge(cr, g.box((x0 + 0.34 * k + (x1 - x0 - 0.34 * k) * (i + 0.5) / 3, y - th / 2, zt + 0.1 * k), ((x1 - x0 - 0.34 * k) / 5, th, 0.2 * k)))
                    items.append((cr, light, False))
                items.append((g.ico((cx, y - th - 0.03 * k, cz + (0.1 * k if kind == "heater" else 0.0)), 0.13 * k, sub=1, scale=(1, 0.6, 1)), trim, False))
            P.grip(side, kind, items)
        elif kind in ("sword-down", "sword-up"):
            d = Vector((0, -0.06, -1)).normalized() if kind == "sword-down" else Vector((0.0, -0.22, 0.97)).normalized()
            g0 = Vector((0, -0.14 * k, 0)) + d * (0.16 * k)
            L = min(2.3 * k, -gz - 0.2 * k) if kind == "sword-down" else 2.5 * k
            flat = d.cross(X).normalized()
            items = [(g.tube([g0 - d * 0.42 * k, g0], 0.04 * k, n=6), "leather_strap"), (g.ico(g0 - d * 0.47 * k, 0.08 * k, sub=1), trim),
                     (g.tube([g0 - X * 0.36 * k, g0 + X * 0.36 * k], 0.045 * k, n=4), trim),
                     (g.tongue([g0, g0 + d * L * 0.5, g0 + d * L * 0.9, g0 + d * L], [0.2 * k, 0.17 * k, 0.13 * k, 0.01 * k], thick=0.2, normal=flat), "steel_edge"),
                     (g.tongue([g0 + flat * 0.014, g0 + flat * 0.014 + d * L * 0.6], [0.06 * k, 0.02 * k], thick=0.3, normal=flat), acc)]
            P.grip(side, kind, items)
        elif kind in ("staff", "crook", "lamp-staff", "spear", "glaive", "standard"):
            H = {"staff": 2.0, "crook": 2.2, "lamp-staff": 2.5, "spear": 2.9, "glaive": 3.1, "standard": 3.0}[kind] * k
            foot = Vector((0, -0.12 * k, gz))
            top = Vector((0, -0.12 * k, H))
            items = [(g.tube([foot, top], 0.04 * k, n=5), "wood_pole", False), (g.tube([foot, foot + Z * 0.14 * k], 0.05 * k, n=5), trim, False)]
            for zz in (0.3, 0.72):
                items.append((_hoop(foot + (top - foot) * zz, 0.05 * k, 0.05 * k, 0.018 * k, u=X, v=Y, n=6, sides=3), acc, False))
            if kind == "staff":
                items.append((g.ico(top, 0.08 * k, sub=1), trim, False))
            if kind in ("crook", "lamp-staff"):
                crook = [top, top + Vector((0.12, 0, 0.2)) * k, top + Vector((0.34, 0, 0.26)) * k, top + Vector((0.5, 0, 0.1)) * k]
                items.append((g.tube(crook, [0.036 * k, 0.03 * k, 0.026 * k, 0.02 * k], n=4), "wood_pole" if kind == "crook" else trim, False))
                if kind == "lamp-staff":
                    hook = crook[-1]
                    lc = hook + Z * -0.36 * k
                    lamp = [(g.tube([hook, lc + Z * 0.2 * k], 0.012 * k, n=3), trim, False), (g.lathe([(0.1 * k, -0.17 * k), (0.15 * k, -0.1 * k), (0.15 * k, 0.1 * k), (0.1 * k, 0.17 * k)], n=6, centre=lc), field("lamp", 2.8), True),
                            (g.lathe([(0.19 * k, 0.16 * k), (0.06 * k, 0.3 * k), (0.0, 0.32 * k)], n=6, centre=lc), acc, False), (g.lathe([(0.12 * k, -0.24 * k), (0.17 * k, -0.17 * k)], n=6, centre=lc), trim, False)]
                    P.hold_move(side, "sway", "lamp", lamp, hook)
            if kind in ("spear", "glaive"):
                if kind == "spear":
                    items.append((g.blade(top, top + Z * 0.55 * k, 0.2 * k, normal=Y, belly=0.3, thick=0.03 * k), "steel_edge", False))
                else:
                    items.append((g.tongue([top - Z * 0.1 * k, top + Vector((0.1, 0, 0.35)) * k, top + Vector((0.06, 0, 0.75)) * k, top + Vector((-0.12, 0, 1.05)) * k], [0.2 * k, 0.34 * k, 0.26 * k, 0.02 * k], thick=0.12, normal=Y), "steel_edge", False))
                p0 = top - Z * 0.12 * k
                Lp = (0.9 if kind == "spear" else 1.5) * k
                flag = g.tongue([p0, p0 + Vector((Lp * 0.5, 0, -0.1 * k)), p0 + Vector((Lp, 0, -0.34 * k))], [0.34 * k, 0.3 * k, 0.03 * k], thick=0.06, normal=Y)
                P.hold_move(side, "sway", "pennon", [(flag, acc, True)], p0)
            if kind == "standard":      # a long flag with two tails, and no device on it
                p0 = top - Z * 0.5 * k
                w = 0.9 * k
                out = [(0.0, w / 2), (1.0 * k, w / 2 - 0.06 * k), (1.6 * k, w / 2 - 0.02 * k), (1.2 * k, 0.0), (1.6 * k, -w / 2 + 0.02 * k), (1.0 * k, -w / 2 + 0.06 * k), (0.0, -w / 2)]
                flag = [(slab(out, p0 + Y * 0.01, X, Z, Y, 0.03 * k), acc, True), (g.box(p0 + Vector((0.55 * k, 0.02 * k, 0)), (1.0 * k, 0.045 * k, 0.16 * k)), pale, True)]
                P.hold_move(side, "sway", "flag", flag, p0)
                items.append((g.blade(top, top + Z * 0.3 * k, 0.14 * k, normal=Y, belly=0.4, thick=0.03 * k), trim, False))
            P.grip(side, kind, items)
        elif kind == "dark-lamp":   # a shuttered lamp, held out from under its cloak: one slit of light
            s = 1.0 if side == "l" else -1.0
            hook = Vector((s * (P.sx + 0.5 * t), min(P.yf(P.chestz), P.yf(P.waist)) - 0.3 * t, P.waist + 0.1 * t))
            lc = hook + Z * -0.42 * k
            P.add("lamp_arm", g.tube([hook + Vector((-s * 0.5 * t, 0.3 * t, 0.05 * t)), hook], 0.07 * t, n=5), light, "chest", smooth=False)
            P.add("lamp_fist", g.ico(hook, 0.11 * t, sub=1), main, "chest", smooth=False)
            lamp = [(g.tube([hook, lc + Z * 0.24 * k], 0.014 * k, n=3), trim, False), (g.lathe([(0.17 * k, -0.2 * k), (0.2 * k, -0.14 * k), (0.2 * k, 0.14 * k), (0.15 * k, 0.2 * k)], n=6, centre=lc), "iron_plate_dark", False),
                    (g.lathe([(0.23 * k, 0.19 * k), (0.07 * k, 0.34 * k), (0.0, 0.36 * k)], n=6, centre=lc), acc, False),
                    (g.box(lc + Vector((0, -0.19 * k, 0)), (0.07 * k, 0.05 * k, 0.24 * k)), field("lamp", 3.2), False)]
            P.move("sway", "lamp", lamp, hook, "chest")


# ======================================================================================
# What is on its back, over its plate, at its belt
# ======================================================================================

def back(P, spec):
    t = P.t
    c = pd.neck_c(P)
    sw = P.sx + 0.1 * t
    main, light, trim = P.material("main"), P.material("under"), P.material("trim")
    styles = [e[0] for e in each(spec.get("back"))]
    for kind, size, word in each(spec.get("back")):
        yb = P.yb(P.chestz)
        if kind in ("cape", "cloak", "wrap", "torn"):
            z0 = P.neckz + 0.0
            z1 = {"cape": P.hipz - 0.05 * t, "cloak": P.footz + 0.1, "wrap": P.footz + (0.22 if "moss" not in styles else 0.0), "torn": P.kneez - 0.1 * t}[kind]
            zs = [z0, P.armz - 0.12 * t, (P.armz + z1) / 2, z1]
            a1 = pi * {"cape": 0.62, "cloak": 0.66, "wrap": 0.985, "torn": 0.6}[kind]
            grow = 0.16 if kind != "wrap" else 0.3
            hem = (lambda aa: 0.16 * t * math.sin(aa * 5.0) - 0.1 * t * max(0.0, math.sin(aa))) if kind == "torn" else None
            geo = pd.drape((0, c.y + 0.03, 0), lambda u: (0.15 + (sw + grow * u - 0.15) * min(1.0, u * 3.0) ** 0.7, 0.15 + (sw * 0.82 + (grow + 0.06) * u - 0.15) * min(1.0, u * 3.0) ** 0.7),
                            zs, -a1, a1, thick=0.035, n=13, hem=hem, trail=0.35 if kind == "torn" else (0.12 if kind == "cloak" else 0.0))
            items = [(geo, mat("accent"), True)]
            if kind in ("cloak", "wrap"):       # a band of the pale of its colour at the hem
                rx_, ry_ = sw + grow, sw * 0.82 + grow + 0.06
                band = pd.drape((0, c.y + 0.03, 0), lambda u: (rx_ + 0.012, ry_ + 0.012), [z1 + 0.16 * t, z1 + 0.05 * t], -a1, a1, thick=0.02, n=13, trail=0.12 if kind == "cloak" else 0.0)
                items.append((band, mat("accent_pale"), True))
            P.move("sway", "cloak", items, (0, c.y, P.neckz), "chest")
            P.add("cloak_clasp", g.ico((0.0, P.yf(P.neckz - 0.08 * t) - 0.02, P.neckz - 0.08 * t), 0.06 * t, sub=1, scale=(1.2, 0.5, 1)), trim, "chest", smooth=False)
        elif kind == "moss":        # moss, come up the hem of what has stood still
            geo = None
            for i in range(9):
                aa = 2 * pi * i / 9 + 0.3
                rr = sw + 0.34
                geo = g.merge(geo, g.ico((rr * math.sin(aa), c.y + 0.03 + rr * 0.95 * math.cos(aa), 0.1 + 0.07 * (i % 3)), (0.16 + 0.05 * (i % 2)) * t, sub=1, scale=(1.0, 1.0, 0.6)))
            P.add("moss", geo, mat("moss_way"), "hips", smooth=True)
        elif kind in ("banner", "flag"):
            if kind == "banner":    # a pole from its backplate, and a banner with no device
                foot = Vector((0, yb + 0.06, P.hipz + 0.1 * t))
                top = Vector((0, yb + 0.1, P.crown + 1.45 * t))
                w, h = 0.86 * t, 1.0 * t
            else:                   # a small flag on a turret
                foot = Vector((P.sx + 0.13 * t, P.army, P.armz + 0.5 * t))
                top = foot + Z * 0.9 * t
                w, h = 0.5 * t, 0.3 * t
            P.add(kind + "_pole", g.tube([foot, top], 0.035 * t if kind == "banner" else 0.022 * t, n=5), mat("wood_pole"), "chest", smooth=False)
            P.add(kind + "_finial", g.ico(top, 0.07 * t if kind == "banner" else 0.04 * t, sub=1), trim, "chest", smooth=False)
            p0 = top - Z * 0.08 * t
            if kind == "banner":
                out = [(0.0, 0.0), (w, 0.0), (w, -h), (w * 0.5, -h * 0.8), (0.0, -h)]
                items = [(slab(out, p0, X, Z, Y, 0.03 * t), mat("accent"), True), (g.box(p0 + Vector((w / 2, 0.015 * t, -0.2 * t)), (w * 0.98, 0.045 * t, 0.12 * t)), mat("accent_pale"), True),
                         (g.tube([p0, p0 + X * w], 0.025 * t, n=4), mat("wood_pole"), False)]
            else:
                items = [(g.tongue([p0, p0 + Vector((w * 0.5, 0, -0.03 * t)), p0 + Vector((w, 0, -0.1 * t))], [h, h * 0.8, 0.02 * t], thick=0.08, normal=Y), mat("accent"), True)]
            P.move("sway", kind, items, p0, "chest")
        elif kind == "pennons":     # a fan of small flags, one for each of its few
            root = Vector((0, yb + 0.06, P.chestz - 0.1 * t))
            poles, flags = None, []
            n = 6
            for i in range(n):
                aa = math.radians(-58 + 116 * i / (n - 1))
                d = Vector((math.sin(aa), 0.12, math.cos(aa))).normalized()
                L = (P.crown - root.z) + (0.75 - 0.3 * abs(i - (n - 1) / 2) / n) * t
                tip = root + d * L
                poles = g.merge(poles, g.tube([root, tip], 0.02 * t, n=4))
                sgn = 1.0 if aa >= 0 else -1.0
                p0 = tip - d * 0.04 * t
                p1 = tip - d * 0.4 * t
                fl = slab([(0.0, 0.0), (0.36 * t, 0.0), (0.0, 1.0)], p0, Vector((sgn * d.z, 0, -sgn * d.x)), (p1 - p0), Y, 0.025 * t)
                flags.append((fl, mat("accent" if i % 2 == 0 else "accent_light"), True))
            P.add("pennon_poles", poles, mat("wood_pole"), "chest", smooth=False)
            P.move("sway", "pennons", flags, root, "chest")
        elif kind == "slung":       # the great shield, slung on its back
            zb, zt = P.hipz - 0.25 * t, P.crown - 0.2 * t
            w = 0.66 * t
            out = [(-w, zb), (w, zb), (w, zt - 0.2 * t), (w - 0.25 * t, zt), (-w + 0.25 * t, zt), (-w, zt - 0.2 * t)]
            P.add("slung", slab(out, (0, yb + 0.1 * t, 0), X, Z, Y, 0.07 * t), light, "chest", smooth=False)
            P.add("slung_face", slab(shrunk(out, 0.8), (0, yb + 0.17 * t, 0), X, Z, Y, 0.02 * t), mat("accent"), "chest", smooth=False)
        elif kind in ("stack", "stacks"):   # a chimney from its back
            for j, sx_ in enumerate(((0.0,) if kind == "stack" else (0.3, -0.3))):
                x = sx_ * t
                foot = Vector((x, yb + 0.1 * t, P.chestz - 0.2 * t))
                top = Vector((x, yb + 0.2 * t, P.crown + (0.25 if kind == "stack" else 0.55 - 0.2 * j) * t))
                P.add("stack_%d" % j, g.tube([foot, top], 0.14 * t, n=7), mat("iron_plate_dark"), "chest", smooth=False)
                P.add("stack_cap_%d" % j, _hoop(top - Z * 0.03 * t, 0.16 * t, 0.16 * t, 0.04 * t, u=X, v=Y, n=7, sides=4), mat("accent"), "chest", smooth=False)
                P.add("stack_band_%d" % j, _hoop(top - Z * 0.4 * t, 0.145 * t, 0.145 * t, 0.03 * t, u=X, v=Y, n=7, sides=3), trim, "chest", smooth=False)
                if kind == "stacks":
                    for i in range(2):
                        q = top + Vector((0.04 * i * t, 0.1 * i * t, (0.26 + 0.34 * i) * t))
                        P.move("bob", "smoke%d" % j, [(g.ico(q, (0.17 + 0.07 * i) * t, sub=1, scale=(1.0, 1.0, 0.8)), mat("smoke_kiln"), True)], q, "chest", n=i)
        elif kind == "shafts":      # what was meant for someone else, still standing in it
            geo, fl = None, None
            for i, (x, z, dx, dz) in enumerate(((0.2, 0.3, 0.5, 0.9), (-0.3, 0.2, -0.75, 0.7), (-0.1, 0.42, -0.2, 1.0), (0.42, 0.0, 0.95, 0.35), (-0.45, -0.1, -0.9, 0.1))):
                p0 = Vector((x * t, yb + 0.0, P.chestz + z * t))
                d = Vector((dx, 0.5, dz)).normalized()
                L = (0.7 + 0.14 * (i % 3)) * t
                geo = g.merge(geo, g.tube([p0, p0 + d * L], 0.022 * t, n=4))
                if i % 2 == 0:
                    fl = g.merge(fl, g.blade(p0 + d * L * 0.7, p0 + d * L * 1.02, 0.14 * t, normal=Y, belly=0.5))
            P.add("shafts", geo, mat("wood_pole"), "chest", smooth=False)
            P.add("fletch", fl, mat("accent_light"), "chest", smooth=True)
        elif kind == "roll":        # a bedroll across its back
            zc = P.chestz + 0.1 * t
            P.add("roll", g.tube([(-0.62 * t, yb + 0.2 * t, zc), (0.62 * t, yb + 0.2 * t, zc)], 0.18 * t, n=8), mat("accent_dark"), "chest", smooth=True)
            for s in (1, -1):
                P.add("roll_strap_%d" % s, _hoop((s * 0.34 * t, yb + 0.2 * t, zc), 0.19 * t, 0.19 * t, 0.025 * t, u=Y, v=Z, n=8, sides=3), mat("leather_strap"), "chest", smooth=True)
        elif kind == "pack":        # a small pack and a coil of rope
            zc = P.chestz - 0.05 * t
            P.add("pack", g.box((0, yb + 0.16 * t, zc), (0.5 * t, 0.26 * t, 0.5 * t)), mat("leather_strap"), "chest", smooth=True)
            P.add("pack_rope", _hoop((0.0, yb + 0.31 * t, zc), 0.17 * t, 0.17 * t, 0.045 * t, u=X, v=Z, n=10, sides=4), mat("accent_pale"), "chest", smooth=True)


def over(P, spec):
    t, th = P.t, P.thick
    c = pd.neck_c(P)
    for kind, size, word in each(spec.get("over")):
        if kind == "sash":          # a band of its Path's colour, shoulder to hip
            zc = (P.armz + P.waist) / 2
            hw, hd, yo = P.ring(zc)
            dz = (P.armz - P.waist) * 0.5
            u = Vector((hw + th, 0, -dz)).normalized()
            P.add("sash", _hoop((0, yo, zc), math.hypot(hw + th + 0.03, dz), hd + th + 0.04, 0.055 * t, u=u, v=Y, n=12, sides=4), mat("accent"), "chest", smooth=True)
        elif kind == "tabard":      # a cloth over the breastplate, before and behind, with one pale stripe
            zt, zb = P.neckz - 0.1 * t, P.kneez + 0.12 * t
            w = P.ring(P.chestz)[0] * 0.74
            out = [(-w, zt), (w, zt), (w * 1.12, zb + 0.14 * t), (0.0, zb), (-w * 1.12, zb + 0.14 * t)]
            yfr = min(P.yf(P.chestz), P.yf(P.waist)) - 0.05 * t
            P.add("tabard", slab(out, (0, yfr, 0), X, Z, -Y, 0.03 * t), mat("accent"), "chest", smooth=True)
            P.add("tabard_stripe", g.box((0, yfr - 0.035 * t, (zt + zb) / 2 + 0.1 * t), (0.16 * t, 0.02 * t, (zt - zb) * 0.72)), mat("accent_pale"), "chest", smooth=True)
            ybk = max(P.yb(P.chestz), P.yb(P.waist)) + 0.05 * t
            P.add("tabard_back", slab(out, (0, ybk, 0), X, Z, Y, 0.03 * t), mat("accent_dark"), "chest", smooth=True)
            hw, hd, yo = P.ring(P.waist)
            P.add("tabard_belt", _hoop((0, yo, P.waist + 0.02 * t), hw + th + 0.08 * t, hd + th + 0.1 * t, 0.04 * t, u=X, v=Y, n=12, sides=4), mat("leather_strap"), "chest", smooth=True)
        elif kind == "scarf":       # wound at the collar, and one end flying
            rr = 0.105 * t + 0.1
            P.add("scarf", _hoop((c.x, c.y, P.neckz + 0.0), rr, rr, 0.085 * t, u=X, v=Y, n=10, sides=5), mat("accent_light"), "chest", smooth=True)
            k0 = Vector((-0.1 * t, c.y + rr, P.neckz))
            L = 0.6 * t * size
            pts = [k0, k0 + Vector((-0.3, 0.35, -0.2)) * L, k0 + Vector((-0.62, 0.6, -0.62)) * L, k0 + Vector((-1.05, 0.75, -0.9)) * L, k0 + Vector((-1.3, 0.8, -1.4)) * L]
            P.move("sway", "scarf", [(g.tongue(pts, [0.16 * t, 0.22 * t, 0.22 * t, 0.2 * t, 0.06 * t], thick=0.18, normal=Y), mat("accent_light"), True)], k0, "chest")
        elif kind == "ribbons":     # tied at each elbow
            for s, tag in ((1, "l"), (-1, "r")):
                e = P.J["lowerarm." + tag]
                p0 = Vector((e.x, e.y + 0.1 * t, e.z))
                items = [(g.tongue([p0, p0 + Vector((0.0, 0.2, -0.2)) * t, p0 + Vector((0.02 * s, 0.34, -0.5)) * t], [0.1 * t, 0.12 * t, 0.03 * t], thick=0.2, normal=X), mat("accent_pale"), True)]
                P.move("sway", "ribbon", items, p0, "lowerarm." + tag, side=tag)


def belt(P, spec):
    kind, size, _ = opt(spec.get("belt"))
    if kind == "keys":          # a ring of keys at its hip
        t = P.t
        hw, hd, yo = P.ring(P.waist)
        hook = Vector((-(hw + P.thick + 0.06 * t), yo - 0.1 * t, P.waist - 0.02 * t))
        items = [(_hoop(hook - Z * 0.14 * t, 0.12 * t, 0.12 * t, 0.02 * t, u=Y, v=Z, n=8, sides=3), P.material("trim"), False)]
        for i in range(3):
            p0 = hook + Vector((0, (i - 1) * 0.08 * t, -0.26 * t))
            items.append((g.merge(g.tube([p0, p0 - Z * 0.3 * t], 0.018 * t, n=4), g.box(p0 + Vector((0, 0.03 * t, -0.27 * t)), (0.03 * t, 0.08 * t, 0.06 * t))), P.material("trim"), False))
        P.move("sway", "keys", items, hook, "hips")


# ======================================================================================
# One form
# ======================================================================================

def armor_form(form_id, level, spec, path=None, clips=False):
    P = Armor(form_id, level, spec)
    plates(P, spec)
    H = helm(P, spec)
    crest(P, spec, H)
    chest(P, spec)
    fauld(P, spec)
    pauldrons(P, spec)
    hands(P, spec)
    back(P, spec)
    over(P, spec)
    belt(P, spec)
    P.finish(path or os.path.join(OUT, form_id + ".glb"), clips=clips)
    return P


def build(form_id, level, spec, base):
    PALETTE.update(lp.OWN)
    PALETTE.update(la.OWN)
    PALETTE.update(OWN)
    try:
        armor_form(form_id, level, spec)
    except Exception:
        if not os.environ.get("WILDLINE_KEEP_GOING"):     # while the line is being worked on: say which form failed, and go on
            raise
        import traceback
        log("!! %s failed" % form_id)
        traceback.print_exc()


def register(builders):
    global GL
    for name in ("genius_lines", "__main__"):
        m = sys.modules.get(name)
        if m is not None and getattr(m, "BUILDERS", None) is builders:
            GL = m
    if GL is None:
        import genius_lines
        GL = genius_lines
    builders["panoply"] = build


# ======================================================================================
# The base's own body, and what it gives a hybrid
# ======================================================================================

def base_body():
    """game/assets/genius/bodies/relic-panoply.glb: the Starter, with the three clips every
    form of the line moves by (a form has none of its own: the game fits these to it)."""
    with open(os.path.join(ROOT, "data", "genius-bases", "panoply.json")) as f:
        base = json.load(f)
    spec = base["settled"]["body"]
    GL._palette_of("panoply")
    GL.accent(spec)
    PALETTE.update(lp.OWN)
    PALETTE.update(la.OWN)
    PALETTE.update(OWN)
    armor_form("relic-panoply", 1, spec, path=os.path.join(ROOT, "game", "assets", "genius", "bodies", SIL + ".glb"), clips=True)


def gift_helm():
    """The Living Armor's helm, on the head of whatever wears it: an open-faced helm that sits
    like a cap, a plume of the wearer's Path's colour, and a brow of brass."""
    c = Vector((0, 0.0, 0.03))
    R = 0.115
    items = [(spun([(R, -0.01), (R * 1.03, 0.03), (R * 0.9, 0.085), (R * 0.5, 0.125), (0.0, 0.135)], c, n=12, sy=1.1), mat("iron_plate"), False),
             (_hoop(c + Z * -0.008, R * 1.02, R * 1.12, 0.011, u=X, v=Y, n=12, sides=3), mat("brass_trim"), False),
             (g.tongue([c + Vector((0, -R * 1.12, 0.0)), c + Vector((0, -R * 1.2, -0.05)), c + Vector((0, -R * 1.22, -0.1))], [0.05, 0.035, 0.012], thick=0.3, normal=Y), mat("iron_plate_light"), False),
             (g.tongue([c + Vector((0, -R * 0.5, 0.15)), c + Vector((0, 0.0, 0.17)), c + Vector((0, R * 0.9, 0.12))], [0.02, 0.05, 0.02], thick=0.2, normal=X), mat("iron_plate_light"), False)]
    top = c + Z * 0.135
    plume = []
    for i in range(3):
        dx = (i - 1) * 0.5
        pts = [top, top + Vector((dx * 0.03, 0.03, 0.09)), top + Vector((dx * 0.07, 0.11, 0.1)), top + Vector((dx * 0.1, 0.2, 0.02))]
        plume.append((g.tongue(pts, [0.02, 0.05, 0.055, 0.005], thick=0.3, normal=X), mat("accent" if i != 1 else "accent_light"), True))
    return [la._still("helm", items), la._piece("sway", "plume", plume, top)]


def gift_pauldrons():
    """The Living Armor's shoulder plates, across the back of whatever wears them, with nobody
    under them: two cups of iron rimmed in the wearer's Path's colour, and a strap between."""
    items = []
    for s in (1, -1):
        cs = Vector((s * 0.115, 0.0, 0.03))
        items.append((g.ico(cs, 0.085, sub=1, scale=(1.25, 1.2, 0.7), rot=(0, s * -0.5, 0)), mat("iron_plate"), False))
        items.append((_hoop(cs + Vector((s * 0.03, 0, -0.025)), 0.1, 0.098, 0.013, u=Y, v=Vector((s * 0.75, 0, -0.66)).normalized(), n=10, sides=3), mat("accent"), False))
        items.append((g.ico(cs + Vector((s * -0.02, 0, 0.055)), 0.018, sub=0), mat("brass_trim"), False))
    items.append((g.tube([(-0.08, 0, 0.06), (0, 0, 0.075), (0.08, 0, 0.06)], 0.016, n=4, flat=0.5), mat("leather_strap"), True))
    return [la._still("pauldrons", items)]


GIFTS = {"panoply-helm": gift_helm, "panoply-pauldrons": gift_pauldrons}


def build_gifts():
    out = os.path.join(ROOT, "game", "assets", "genius", "gifts")
    GL._palette_of("panoply")
    GL.accent({"accent": "gold"})
    PALETTE.update(la.OWN)
    PALETTE.update(OWN)
    for name, make in GIFTS.items():
        kit.reset()
        objs = make()
        path = os.path.join(out, name + ".glb")
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        tris = sum(sum(len(q.vertices) - 2 for q in o.data.polygons) for o in objs)
        log("wrote", os.path.relpath(path, ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


if __name__ == "__main__":
    import genius_lines  # noqa: F401   (it registers every family, this one among them, as lines_panoply)
    me = sys.modules["lines_panoply"]
    what = sys.argv[1:] or ["body", "gifts"]
    if "body" in what:
        me.base_body()
    if "gifts" in what:
        me.build_gifts()
