"""WILDLINE genius lines, the wolf's kin: the Fox, the Stag and the Drake, each form a body of
its own on the wolf's rig (docs/genius-evolutions.md; genius_lines.py builds the Wolf and
calls this file's register).

    python tools/blender/genius_lines.py fox
    python tools/blender/genius_lines.py stag stag-fawn stag-twelve-point
    python tools/blender/genius_lines.py drake

Each is the wolf reshaped as the genius kit reshaped it for the base's old body (a species),
aged its own way (a fawn is all leg where a pup is all paw), and then grown from its `body`
in data/genius-bases. The wolf's slots still work on them (build, ears, eyes, maw, spine,
paws, armor, carry, aura and the rest); what is theirs alone is here:

  every line   pose     how it carries its head, put on last so that everything it has grown
                        goes with it: low, high, nod, back (over its shoulder), aside, tilt
               tail     up, over (arched over its back), wrap, low, loop (shapes of the tail)
               neck     what is worn round a neck as it lies: mane, bell, lamp, ivy, garland,
                        teeth, chains, ash, bands
  the Fox      whiskers, mouth (what it carries), tails (two, many), tip (what its tail-tips
               carry: light, white, ring, coal, flame, wisp), mask, face, back, feet, fins,
               claws, and in carry: panniers, pole, cape; in ruff: courtier
  the Stag     crown (the shape of its antlers), horn (what they are made of), hung (what
               is in them), throat, breath, hide, legs, flank, chest
  the Drake    horns, frill, ridge, wings, belly, throat, tailend, shell, jaw, breath,
               nostrils, claws, eye

A form's `coat` is still its partner's coat, shifted; the look's roles for each body
(data/genius-looks.json, bodies) are kept, so the coat goes on: fur_dark and fur_light on
the Fox and the Drake (whose ridge, wings and tail-tip are its markings), hide_red and
fur_cream on the Stag.
"""
import math
import os
import sys

import bpy  # noqa: F401  (Blender's module first: mathutils comes with it)
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z, V  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field, PALETTE, STAND  # noqa: E402
import beast_kit as bk  # noqa: E402

gl = None       # genius_lines as it is running (register sets it: run as a script it is __main__)
_S = {}         # what the form being built has so far (the tips of its tails, its rack...)

PALETTE.update({
    "leaf": ((0.15, 0.21, 0.1), 0.9, 0.0), "leaf_dry": ((0.24, 0.17, 0.09), 0.9, 0.0), "moss": ((0.2, 0.29, 0.12), 1.0, 0.0), "weed": ((0.1, 0.19, 0.13), 0.6, 0.0),
    "petal": ((0.78, 0.72, 0.62), 0.6, 0.0), "bark": ((0.13, 0.095, 0.065), 0.95, 0.0), "bark_light": ((0.27, 0.2, 0.13), 0.95, 0.0), "velvet": ((0.23, 0.16, 0.11), 1.0, 0.0),
    "mask_pale": ((0.82, 0.78, 0.68), 0.5, 0.0), "mask_red": ((0.4, 0.09, 0.07), 0.6, 0.0), "cape_red": ((0.3, 0.085, 0.07), 0.95, 0.0), "fin": ((0.19, 0.25, 0.27), 0.4, 0.0),
    "brass_old": ((0.4, 0.38, 0.16), 0.4, 0.8), "glaze": ((0.76, 0.72, 0.64), 0.2, 0.0), "slag": ((0.06, 0.052, 0.055), 0.6, 0.0), "ash": ((0.5, 0.49, 0.47), 1.0, 0.0),
    "ash_dark": ((0.26, 0.25, 0.25), 1.0, 0.0), "soot": ((0.03, 0.028, 0.032), 1.0, 0.0), "eggshell": ((0.8, 0.76, 0.66), 0.45, 0.0), "lichen": ((0.56, 0.6, 0.46), 0.9, 0.0),
    "ribbon_a": ((0.32, 0.1, 0.08), 0.9, 0.0), "ribbon_b": ((0.13, 0.19, 0.3), 0.9, 0.0), "ribbon_c": ((0.33, 0.27, 0.09), 0.9, 0.0), "tongue_ink": ((0.018, 0.018, 0.026), 0.4, 0.0),
    "earth": ((0.1, 0.075, 0.055), 1.0, 0.0), "wet": ((0.06, 0.055, 0.05), 0.25, 0.0), "knee": ((0.42, 0.41, 0.4), 0.9, 0.0),
})

NECK = ("Neck1", "Neck2", "Neck3")


def log(*a):
    print("[lines_wolfkin]", *a)


# ======================================================================================
# What the three share
# ======================================================================================

def _add(r, name, geo, weights, material, smooth=None):
    gl._add(r, name, geo, weights, material, smooth)


def _head(r):
    return r.family("Head", "Ear1.L", "Ear1.R")


def _tail(r):
    return r.family("Tail1")


def _tail_girth(r, s):
    tail = _tail(r)
    tz = sum(r.bone(b).z for b in tail) / len(tail)
    r.scale(tail, (0, 0, tz), s)


def _perp(d):
    """Across a direction: (to the left, to the back of it). For a neck these are its side
    and its nape, however it is carried."""
    d = V(d).normalized()
    u = X - d * X.dot(d)
    u = u.normalized() if u.length > 1e-4 else Y.copy()
    v = Z - d * Z.dot(d)
    v = v.normalized() if v.length > 0.2 else (Y - d * Y.dot(d)).normalized()
    return u, v


def _hoop(centre, normal, radius, thick=0.02, n=16, sides=4):
    """A ring about a point, facing along normal."""
    u, v = _perp(normal)
    pts = [V(centre) + (u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n)) * radius for i in range(n + 1)]
    return g.tube(pts, [thick] * (n + 1), n=sides, caps=False)


def _panel(pts, thick=0.014):
    """A flat skin through points (a membrane, a banner): seen from both sides."""
    pts = [V(p) for p in pts]
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    n = n.normalized() if n.length > 1e-8 else Z.copy()
    k = len(pts)
    verts = pts + [p - n * thick for p in pts]
    faces = [tuple(range(k)), tuple(range(2 * k - 1, k - 1, -1))]
    for i in range(k):
        j = (i + 1) % k
        faces.append((i, i + k, j + k, j))
    return verts, faces


def _ears(r, kx=1.0, kz=1.0, turn=None, only=None):
    """Reshape the ears themselves. They are the head's own flesh (their bones carry only the
    tips), so they are picked out by where they are: about each ear's own line, from its root.
    turn(side) gives an axis and an angle to lay them over by."""
    head = _head(r)
    for sg, tag in ((1, "L"), (-1, "R")):
        if only is not None and sg != only:
            continue
        base, tip = r.bone("Ear1." + tag), r.bone("Ear4." + tag)
        ax = (tip - base).normalized()
        R = None
        if turn is not None:
            axis, ang = turn(sg)
            R = Matrix.Rotation(ang, 3, axis)

        def T(p, base=base, ax=ax, sg=sg, R=R):
            if p.x * sg <= 0.02:
                return p
            v = p - base
            t = v.dot(ax)
            lat = v - ax * t
            if t < 0.0 or lat.length > 0.24:
                return p
            k = min(1.0, t / 0.1)
            q = base + ax * (t * (1 + (kz - 1) * k)) + lat * (1 + (kx - 1) * k)
            if R is not None:
                q = q.lerp(base + R @ (q - base), k)
            return q
        r.deform(head, T)


def _young_eyes(r, k=0.1):
    """The young have large round eyes."""
    e = kit._eye(r)
    eyes = None
    for sg in (1, -1):
        eyes = g.merge(eyes, g.ico((sg * (e.x + 0.02), e.y - 0.01, e.z - 0.01), k, sub=1, scale=(0.55, 1.0, 1.05)))
    _add(r, "young_eyes", eyes, "Head", field("eyes", 3.2))


def _paint_coat(r, pick, material):
    """Faces of its own skin (never its eyes, its nose or what it has grown) that pass
    pick(centre) take a material."""
    me = r.mesh.data
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    names = [m.name for m in me.materials]
    slot = names.index(material.name)
    skin = {i for i, nm in enumerate(names) if nm.startswith(("fur_", "mark_", "hide_"))}
    n = 0
    for p in me.polygons:
        if p.material_index in skin and pick(r.M @ p.center):
            p.material_index = slot
            n += 1
    return n


# what is round is shaded round, whatever it is made of (a beam, a cane, a link, a bead):
# only what has planes keeps them (plate, slate, ice, a book, a mask). It is also what keeps
# a body with a great deal on it inside its size.
ROUND = ("scar", "glaze", "slag", "bark", "bone", "metal_iron", "wax", "coal", "claw", "moss", "leaf", "weed", "petal", "lichen", "ash", "horn", "mark_ridge", "mark_wings",
         "mark_tailtip", "wood", "velvet", "brass_old", "whisker", "feather", "crow", "beak", "earth", "knee", "wet", "soot", "ribbon", "drake_horn", "wing")


def _round(r):
    me = r.mesh.data
    soft = {i for i, m in enumerate(me.materials) if m.name.startswith(ROUND)}
    for p in me.polygons:
        if p.material_index in soft:
            p.use_smooth = True


def _recoat(r, mapping):
    """What the wolf's styles made of the wolf's materials goes into this animal's own."""
    me = r.mesh.data
    names = [m.name for m in me.materials]
    for src, dst in mapping.items():
        if src in names and dst in names and src != dst:
            a, b = names.index(src), names.index(dst)
            for p in me.polygons:
                if p.material_index == a:
                    p.material_index = b


class Neck:
    """A neck as it lies, whichever way it is carried: along it from its root (0) to the
    skull (1), the point on its axis, the way it runs, and how far the flesh reaches from
    the axis in any direction across it."""

    def __init__(self, r):
        self.p = [r.bone(b) for b in NECK + ("Head",)]
        w = r._weights(list(NECK) + ["Head", "Torso3"])
        self.verts = [q for q, k in zip(r.world_verts(), w) if k > 0.3]

    def at(self, t):
        t = max(0.0, min(0.999, t))
        seg = int(t * 3)
        f = t * 3 - seg
        a, b = self.p[seg], self.p[seg + 1]
        return a.lerp(b, f), (b - a).normalized(), NECK[seg if f < 0.6 else min(seg + 1, 2)]

    def reach(self, p, d, radial, default=0.22):
        best = 0.0
        for q in self.verts:
            v = q - p
            if abs(v.dot(d)) > 0.16:
                continue
            w = v - d * v.dot(d)
            L = w.length
            if L > 1e-5 and w.dot(radial) / L > 0.8:
                best = max(best, w.dot(radial))
        return best or default

    def ring(self, t, off=0.0, n=12, along=0.0, grow=1.0):
        """Points round the neck at t, off its surface."""
        p, d, _ = self.at(t)
        u, v = _perp(d)
        out = []
        for i in range(n):
            a = 2 * math.pi * i / n
            radial = u * math.cos(a) + v * math.sin(a)
            out.append(p + d * along + radial * ((self.reach(p, d, radial) + off) * grow))
        return out

    def throat(self, t, off=0.03):
        p, d, _ = self.at(t)
        u, v = _perp(d)
        return p - v * (self.reach(p, d, -v) + off)

    def nape(self, t, off=0.0):
        p, d, _ = self.at(t)
        u, v = _perp(d)
        return p + v * (self.reach(p, d, v) + off)


class Skin:
    """The bare body as it was before anything was grown on it: its back, its belly and its
    flanks, asked for by place. (Asked of the body as it grows, each plate would be laid on
    the one before.)"""

    def __init__(self, r):
        self.v = [p.copy() for p in r.world_verts()]
        w = r._weights(list(bk.TORSO))
        self.torso = [p for p, k in zip(self.v, w) if k > 0.5]

    def _near(self, verts, pick, window):
        for _ in range(6):
            pts = [p for p in verts if pick(p, window)]
            if pts:
                return pts
            window *= 1.6
        return verts

    def top(self, y, half_width=0.18, window=0.14):
        return max(p.z for p in self._near(self.v, lambda p, w: abs(p.x) < half_width * (w / window) and abs(p.y - y) < w, window))

    def bottom(self, y, half_width=0.18, window=0.14):
        return min(p.z for p in self._near(self.torso, lambda p, w: abs(p.x) < half_width * (w / window) and abs(p.y - y) < w, window))

    def side(self, y, z, window=0.2):
        return max(abs(p.x) for p in self._near(self.torso, lambda p, w: abs(p.y - y) < w and abs(p.z - z) < w, window))


def _skin():
    return _S["skin"]


def _measure(r, A):
    """Readings the wolf's own do not get right on these: the crown of the head (between the
    ears, wherever the skull's points fall), and the front of the chest."""
    wh = r._weights(["Head"])
    crown = [p.z for p, k in zip(r.world_verts(), wh) if k > 0.5 and abs(p.x) < 0.13 and abs(p.y - A.head.y) < 0.3]
    if crown:
        A.skull = max(crown)
    wt = r._weights(["Torso3", "Neck1"])
    front = [p.y for p, k in zip(r.world_verts(), wt) if k > 0.3 and abs(p.x) < 0.3 and A.belly + 0.1 < p.z < A.withers - 0.15]
    if front:
        A.chest_y = max(min(front), A.n1.y - 0.7)
    _S["skin"] = Skin(r)
    _S["A"] = A


def _neck(r):
    if "neck" not in _S:
        _S["neck"] = Neck(r)
    return _S["neck"]


def _neck_blades(r, name, t, n, L, width, material, a0=0.0, a1=1.0, sweep=0.8, out=0.5, alt=None, wob=0.0, belly=0.3, drop=0.0, grow=0.86):
    """Blades standing round the neck at t, from a0 to a1 in half-turns (0 the left side, 0.5
    the nape, 1 the right, 1.5 the throat), swept toward the body."""
    nk = _neck(r)
    p, d, bone = nk.at(t)
    u, v = _perp(d)
    geo, geo2 = None, None
    for i in range(n):
        a = math.pi * (a0 + (a1 - a0) * i / max(1, n - 1))
        radial = u * math.cos(a) + v * math.sin(a)
        base = p + radial * (nk.reach(p, d, radial) * grow)
        Li = L * (1.0 + wob * math.sin(i * 2.4 + 0.7))
        tip = base + radial * (Li * out) - d * (Li * sweep) - Z * (drop * Li)
        bl = g.blade(base, tip, width * (1.0 + 0.2 * (i % 2)), normal=radial, belly=belly)
        if alt is not None and i % 2:
            geo2 = g.merge(geo2, bl)
        else:
            geo = g.merge(geo, bl)
    _add(r, name, geo, bone, material)
    if geo2:
        _add(r, name + "_b", geo2, bone, alt)


def _neck_band(r, name, t, material, wide=0.05, off=0.035):
    nk = _neck(r)
    _, _, bone = nk.at(t)
    _add(r, name, g.loft([nk.ring(t, off, along=-wide), nk.ring(t, off * 1.2, along=wide)], caps=False), bone, material)
    return bone


def _tailbones(r):
    return [r.bone("Tail%d" % i) for i in range(1, 9)]


def _tail_tip(r):
    """Where the tail ends, and the way it points there."""
    tb = _tailbones(r)
    d = tb[7] - tb[6]
    d = d.normalized() if d.length > 1e-4 else Y.copy()
    w = r._weights(["Tail8"])
    far = max([(q - tb[7]).dot(d) for q, k in zip(r.world_verts(), w) if k > 0.5] or [0.2])
    return tb[7] + d * max(0.05, far), d


def _tips(r):
    """Every tail-tip it has: its own, and those of the tails it has grown."""
    p, d = _tail_tip(r)
    return [(p, d, "Tail8")] + _S.get("tips", [])


def _pose_tail(r, angles, axis=X):
    """Turn the tail joint by joint (each turn carries everything beyond it)."""
    for i, a in enumerate(angles):
        if abs(a) > 1e-6:
            r.rotate(r.family("Tail%d" % (i + 1)), r.bone("Tail%d" % (i + 1)), axis, a)


def _pose(r, spec):
    """How it carries its head, put on last: everything grown on the head and neck goes too."""
    head, neck = _head(r), list(NECK)
    for style, size in gl.each(spec.get("pose")):
        if style == "low":            # the head low and forward
            r.rotate(neck + head, r.bone("Neck1"), X, 0.4 * size)
        elif style == "high":         # the head up
            r.rotate(neck + head, r.bone("Neck1"), X, -0.3 * size)
        elif style == "nod":          # the muzzle down (less than nothing lifts it)
            r.rotate(head, r.bone("Head"), X, 0.4 * size)
        elif style == "back":         # looking back over its shoulder
            for i, b in enumerate(neck):
                r.rotate(neck[i:] + head, r.bone(b), Z, -0.38 * size)
            r.rotate(head, r.bone("Head"), Z, -0.3 * size)
        elif style == "aside":        # looking somewhere else
            r.rotate(neck[1:] + head, r.bone("Neck2"), Z, -0.3 * size)
            r.rotate(head, r.bone("Head"), Z, -0.3 * size)
        elif style == "tilt":         # the head on one side
            r.rotate(head, r.bone("Head"), Y, -0.45 * size)


# what is put on in what order, where one thing stands on another
ORDER = ["build", "coat", "horn", "crown", "hung", "horns", "frill", "ridge", "wings", "tails", "tip"]


def _ordered(spec):
    first = [k for k in ORDER if k in spec]
    return {k: spec[k] for k in first + [k for k in spec if k not in first]}


def _builder(species, ages, coat, marks, remap, ref_k=1.0, measure=None):
    def build(form_id, level, spec, base):
        _S.clear()
        _S["level"] = level
        spec = _ordered(spec)
        r, sockets = gl.wolf_form(form_id, level, spec, species=species, coat=coat, marks=marks, ages=ages, measure=measure or _measure)
        _recoat(r, remap)
        _round(r)
        _pose(r, spec)
        if ref_k != 1.0:
            sockets["ref_top"].matrix_world = Matrix.Translation((0, 0, STAND * ref_k))
        gl.export(r, sockets, os.path.join(gl.OUT, form_id + ".glb"))
    return build


# --- the tail, as it is carried (shapes) ----------------------------------------------------

def _shapes():
    S = gl.SHAPES
    S[("tail", "up")] = lambda r, s: _pose_tail(r, [0.95 * s, 0.25 * s, 0.12 * s, 0.05, -0.05, -0.1, -0.1])
    S[("tail", "over")] = lambda r, s: _pose_tail(r, [0.9, 0.5, 0.45, 0.42, 0.38, 0.32, 0.26, 0.2])
    S[("tail", "wrap")] = lambda r, s: (_pose_tail(r, [-0.25]), _pose_tail(r, [0.3, 0.5, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25], Z))
    S[("tail", "low")] = lambda r, s: _pose_tail(r, [-0.45 * s])
    S[("tail", "loop")] = lambda r, s: (_pose_tail(r, [-0.3]), _pose_tail(r, [0.25, 0.6, 0.65, 0.65, 0.65, 0.62, 0.58, 0.5], Z))
    S[("tails", "two")] = lambda r, s: (_pose_tail(r, [0.9]), r.rotate(_tail(r), r.bone("Tail1"), Z, 0.42))
    # the ears: great (large and cupped), long (narrow and tall), small, laid (back along the
    # neck), one (one to the front and one always turned behind), droop (hanging)
    S[("ears", "great")] = lambda r, s: _ears(r, 1.0 + 0.6 * s, 1.0 + 0.8 * s)
    S[("ears", "long")] = lambda r, s: _ears(r, 0.9, 1.0 + 0.9 * s)
    S[("ears", "small")] = lambda r, s: _ears(r, 0.8, 0.55 / max(0.5, s))
    S[("ears", "laid")] = lambda r, s: _ears(r, 0.9, 1.0 + 0.2 * s, turn=lambda sg: (X, -0.95))
    S[("ears", "one")] = lambda r, s: _ears(r, 1.1, 1.0 + 0.3 * s, turn=lambda sg: (X, 0.3 if sg > 0 else -1.05))
    S[("ears", "droop")] = lambda r, s: _ears(r, 1.2, 1.0 + 0.5 * s, turn=lambda sg: (Y, sg * 1.7))
    S[("ears", "torn")] = lambda r, s: _ears(r, 1.0, 0.5, only=-1)


# --- round the neck -------------------------------------------------------------------------

def neck_mane(r, A, size):
    """A mane down the nape and the sides of the neck, as it lies."""
    for i, (t, n, L) in enumerate(((0.85, 9, 0.34), (0.6, 11, 0.44), (0.35, 12, 0.52), (0.08, 13, 0.56))):
        _neck_blades(r, "nmane_%d" % i, t, n, L * size, 0.24, mat(_S.get("mane", "fur_ruff")), a0=-0.1, a1=1.1, sweep=0.7, out=0.42, drop=0.25, wob=0.12, belly=0.4)


def neck_bell(r, A, size):
    bone = _neck_band(r, "bellstrap", 0.3, mat("leather"))
    c = _neck(r).throat(0.3) + Vector((0, 0, -0.16 * size))
    _add(r, "bell", g.lathe([(0.03, 0.15), (0.1, 0.11), (0.15, -0.05), (0.2, -0.14)], n=7, centre=c), bone, mat("metal_brass"))
    _add(r, "bell_tongue", g.ico(c + Vector((0, 0, -0.16)), 0.05, sub=0), bone, mat("metal_iron"))


def neck_lamp(r, A, size):
    bone = _neck_band(r, "lampstrap", 0.3, mat("leather"))
    gl._add_items(r, "necklamp", gl._lantern(_neck(r).throat(0.3) + Vector((0, 0, 0.02)), 0.2 * size, "lamp", 3.4), bone)


def neck_ivy(r, A, size):
    for i, t in enumerate((0.2, 0.42)):
        _neck_blades(r, "ivy_%d" % i, t, 13, 0.24 * size, 0.2, mat("leaf"), a0=-0.45, a1=1.45, sweep=0.5, out=0.75, alt=mat("leaf_dry"), wob=0.3, belly=0.45)


def neck_garland(r, A, size):
    nk = _neck(r)
    for i, t in enumerate((0.2, 0.5)):
        _neck_blades(r, "garland_%d" % i, t, 10, 0.22 * size, 0.2, mat("leaf"), a0=-0.5, a1=1.5, sweep=0.4, out=0.8, wob=0.3, belly=0.45)
        geo, lit = None, None
        for k, p in enumerate(nk.ring(t, 0.07, n=6)):
            geo = g.merge(geo, g.ico(p, 0.085 * size, sub=0, scale=(1, 1, 0.6)))
            lit = g.merge(lit, g.ico(p + Vector((0, 0, 0.02)), 0.03 * size, sub=0))
        _add(r, "garland_fl_%d" % i, geo, nk.at(t)[2], mat("petal"))
        _add(r, "garland_c_%d" % i, lit, nk.at(t)[2], field("bloom", 2.0))


def neck_teeth(r, A, size):
    """A string of teeth, not its own, worn where a collar would be."""
    bone = _neck_band(r, "toothcord", 0.25, mat("cord"), wide=0.025)
    nk = _neck(r)
    p, d, _ = nk.at(0.25)
    u, v = _perp(d)
    geo = None
    for i in range(11):
        a = math.pi * (1.02 + 0.96 * i / 10)
        radial = u * math.cos(a) + v * math.sin(a)
        b0 = p + radial * (nk.reach(p, d, radial) + 0.04)
        geo = g.merge(geo, g.cone(b0, b0 + radial * 0.05 + Vector((0, 0, -(0.2 + 0.1 * math.sin(i * 1.9)) * size)), 0.05 * size, n=5))
    _add(r, "teeth_strung", geo, bone, mat("bone"))


def neck_chains(r, A, size):
    """Chains round the neck, with what hangs on them."""
    nk = _neck(r)
    for k, t in enumerate((0.2, 0.58)):
        _, _, bone = nk.at(t)
        geo = None
        for i, p in enumerate(nk.ring(t, 0.04, n=7)):
            geo = g.merge(geo, g.ico(p, 0.075 * size, sub=0, scale=(1.0, 0.6, 1.0) if i % 2 else (0.6, 1.0, 1.0)))
        _add(r, "chain_%d" % k, geo, bone, mat("metal_iron"), smooth=True)
    for k, (t, dx) in enumerate(((0.2, -0.1), (0.2, 0.1), (0.58, 0.0))):
        _, _, bone = nk.at(t)
        c = nk.throat(t, 0.05) + Vector((dx, 0, 0))
        strip = g.blade(c, c + Vector((dx * 0.5, -0.03, -0.36 * size)), 0.17 * size, normal=Y, belly=0.5)
        _add(r, "writ_%d" % k, strip, bone, mat("paper"))
        _add(r, "seal_%d" % k, g.ico(c + Vector((dx * 0.3, -0.05, -0.2 * size)), 0.05 * size, sub=0), bone, field("seal", 1.8))


def neck_ash(r, A, size):
    """Ash in a fine grey collar."""
    for i, t in enumerate((0.3, 0.5)):
        _neck_blades(r, "ashcollar_%d" % i, t, 16, 0.3 * size, 0.17, mat("ash"), a0=-0.5, a1=1.5, sweep=0.25, out=0.9, alt=mat("ash_dark"), wob=0.35, belly=0.4)


def neck_bands(r, A, size):
    """Pale bands round the neck, like a light on the coast."""
    for i, t in enumerate((0.2, 0.45, 0.7)):
        _neck_band(r, "neckband_%d" % i, t, mat("glaze"), wide=0.07 * size, off=0.012)


# ======================================================================================
# The Fox
# ======================================================================================

def fox_species(r):
    """Slight and quick: a narrow muzzle, tall ears, a brush as big as the rest of it."""
    head = _head(r)
    r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (0.8, 1.0, 0.82))
    r.leg_girth(0.7)
    r.leg_length(0.12)
    r.scale(head, r.bone("Neck3"), (0.9, 1.08, 0.92))
    eye = kit._eye(r)
    r.deform(head, lambda p: Vector((p.x * (0.74 + 0.26 * max(0.0, min(1.0, (p.y - (eye.y - 0.5)) / 0.4))), p.y, p.z)) if p.y < eye.y - 0.1 else p)
    _ears(r, 1.25, 1.5)
    r.lengthen_chain(_tail(r), [], 1.22)
    _tail_girth(r, (1.75, 1.0, 1.75))
    r.rotate(_tail(r), r.bone("Tail1"), X, math.radians(-18))
    kit._paint(r, ["Tail7", "Tail8"], mat("fur_light"))       # the tip of the brush, in its under-colour


def fox_ages(r, level):
    head, hb = _head(r), r.bone("Head")
    top = r.top(r.bone("Torso2").y)
    if level <= 1:                  # the kit: more tail than fox
        r.scale(head, hb, 1.3)
        eye = kit._eye(r)
        r.deform(head, lambda p: Vector((p.x, eye.y + (p.y - eye.y) * 0.62, p.z)) if p.y < eye.y - 0.04 else p)
        r.leg_length(0.36)
        r.leg_girth(1.3)
        r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, 0.76)
        zc = (r.top(r.bone("Torso2").y) + r.bottom(r.bone("Torso2").y, half_width=0.1)) / 2
        r.scale(bk.TORSO, (0, 0, zc), (1.15, 1.0, 1.1))
        r.scale(_tail(r), r.bone("Tail1"), (1.2, 1.0, 1.2))
        gl._feet(r, 1.4)
        _young_eyes(r, 0.105)
    elif level == 2:
        r.scale(head, hb, 1.12)
    elif level >= 4:
        r.scale(["Torso3", "Torso2"], (0, 0, top), (1.08, 1.0, 1.06))
        r.leg_length(-0.1)
        r.lengthen_chain(_tail(r), [], 1.1)
        r.scale(_tail(r), r.bone("Tail1"), (1.1, 1.0, 1.1))
    if level >= 2:                  # the pale tufts at a fox's cheeks
        e = kit._eye(r)
        geo = None
        k = 0.8 + 0.1 * level
        for sg in (1, -1):
            for i in range(4):
                b0 = Vector((sg * (e.x + 0.02), e.y + 0.1 + 0.05 * i, e.z - 0.16 - 0.03 * i))
                tip = b0 + Vector((sg * (0.2 + 0.03 * i), 0.16 + 0.04 * i, -0.12 - 0.04 * i)) * k
                geo = g.merge(geo, g.blade(b0, tip, 0.14, normal=Vector((sg * 0.6, -0.6, 0.4)), belly=0.35))
        _add(r, "cheeks", geo, "Head", mat("fur_light"))


def fox_whiskers(r, A, size):
    n = A.nose
    wh = None
    for sg in (1, -1):
        for dy, dz in ((0.06, 0.12), (0.16, 0.0), (0.12, -0.14)):
            b0 = Vector((sg * 0.12, n.y + 0.2, n.z - 0.05 + dz * 0.25))
            mid = b0 + Vector((sg * 0.3 * size, dy * 0.5, dz * 0.6))
            tip = b0 + Vector((sg * 0.6 * size, dy + 0.12, dz - 0.04))
            wh = g.merge(wh, g.tube([b0, mid, tip], [0.015, 0.011, 0.004], n=3))
    _add(r, "whiskers", wh, "Head", mat("whisker"))


def _fox_mouth(style):
    def fn(r, A, size):
        n = A.nose
        c = Vector((0, n.y + 0.12, n.z - 0.2))
        if style == "sack":           # something in its mouth, held very gently
            _add(r, "sack", g.ico(c + Vector((0, 0, -0.3 * size)), 0.27 * size, sub=1, scale=(1.0, 0.9, 1.2)), "Head", mat("paper"), smooth=True)
            _add(r, "sack_neck", g.tube([c + Vector((0, 0, -0.06 * size)), c + Vector((0, 0, 0.08))], [0.1 * size, 0.05 * size], n=6), "Head", mat("cord"))
            _add(r, "sack_tie", _hoop(c + Vector((0, 0, -0.06 * size)), Z, 0.085 * size, 0.022, n=8), "Head", mat("cape_red"))
        elif style == "prize":        # something bright that was somebody else's
            _add(r, "prize", g.ico(c + Vector((0, 0, -0.14 * size)), 0.13 * size, sub=1, scale=(1.1, 0.45, 1.3)), "Head", field("prize", 3.0))
            _add(r, "prize_rim", _hoop(c + Vector((0, 0, -0.14 * size)), Y, 0.16 * size, 0.022, n=10), "Head", mat("metal_brass"))
    return fn


def _brush(root, yaw, lift, L, fat, curl=0.22):
    """A fox's brush from root, turned yaw to the side and lifted: its body, its tip, the
    point it ends at and the way it runs there."""
    d = Vector((math.sin(yaw) * math.cos(lift), math.cos(yaw) * math.cos(lift), math.sin(lift)))
    pts = [V(root) + d * (L * i / 6) + Z * (curl * L * (i / 6) ** 2) for i in range(7)]
    radii = [fat * k for k in (0.3, 0.72, 1.0, 1.0, 0.8, 0.46, 0.06)]
    return g.tube(pts[:5], radii[:5], n=7), g.tube(pts[4:], radii[4:], n=7), pts[-1], (pts[-1] - pts[-2]).normalized()


def _fox_tails(yaws):
    def fn(r, A, size):
        tb = _tailbones(r)
        L = sum((tb[i + 1] - tb[i]).length for i in range(7)) * 1.12
        w = r._weights(["Tail3", "Tail4"])
        fat = max([abs(q.x) for q, k in zip(r.world_verts(), w) if k > 0.6] or [0.3]) if len(yaws) == 1 else 0.27
        body, tips = None, None
        _S.setdefault("tips", [])
        for yaw, lift in yaws:
            b, t, end, d = _brush(tb[0], yaw, lift, L * size, fat * size)
            body, tips = g.merge(body, b), g.merge(tips, t)
            _S["tips"].append((end, d, "Tail1"))
        _add(r, "brushes", body, "Tail1", mat("fur_dark"), smooth=True)
        _add(r, "brush_tips", tips, "Tail1", mat("fur_light"), smooth=True)
    return fn


def _fox_tip(style):
    def fn(r, A, size):
        for i, (p, d, bone) in enumerate(_tips(r)):
            if style == "light":      # a light riding at the tip
                _add(r, "tiplight_%d" % i, g.ico(p + d * 0.17, 0.125 * size, sub=1), bone, field("foxfire", 3.4))
            elif style == "white":    # a white tip that carries a light of its own
                _add(r, "tipmop_%d" % i, g.ico(p - d * 0.12, 0.36 * size, sub=1, scale=(0.9, 0.9, 1.15)), bone, mat("fur_pale"), smooth=True)
                _add(r, "tiplight_%d" % i, g.ico(p + d * 0.36 * size, 0.13 * size, sub=1), bone, field("foxfire", 3.6))
            elif style == "ring":     # a thin ring of light spinning round it
                _add(r, "tipring_%d" % i, _hoop(p - d * 0.2, d, 0.46 * size, 0.03), bone, field("ring", 3.2))
                _add(r, "tipring2_%d" % i, _hoop(p - d * 0.2, d + X * 0.5, 0.36 * size, 0.02), bone, field("ring", 3.2))
                _add(r, "tiplight_%d" % i, g.ico(p + d * 0.1, 0.09 * size, sub=1), bone, field("foxfire", 3.4))
            elif style == "flame":    # a small steady flame
                f0 = p + d * 0.05
                outer = g.tongue([f0, f0 + Vector((0.03, 0, 0.22 * size)), f0 + Vector((-0.02, 0, 0.56 * size))], [0.22 * size, 0.2 * size, 0.02], thick=0.7, normal=Y)
                _add(r, "tipflame_%d" % i, outer, bone, field("flame", 3.4))
                _add(r, "tipwick_%d" % i, g.ico(f0, 0.07 * size, sub=0), bone, mat("coal"))
            elif style == "wisp":     # a light that floats a little above where it should be
                c = p + Vector((0, 0, 0.42 * size))
                _add(r, "wisp_%d" % i, g.ico(c, 0.15 * size, sub=1, scale=(0.9, 0.9, 1.2)), bone, field("foxfire", 3.6))
                _add(r, "wisp_tail_%d" % i, g.tongue([c + Vector((0, 0, -0.1)), c + Vector((0.04, 0, -0.24)), c + Vector((-0.02, 0, -0.36))], [0.12, 0.07, 0.01], thick=0.6, normal=Y), bone, field("foxfire", 2.0))
    return fn


def _fox_mask(style):
    def fn(r, A, size):
        e, n, hb = A.eye, A.nose, A.head
        if style == "raised":         # pushed up on its head, for now
            tip, up = Vector((0, e.y + 0.02, e.z + 0.2)), Vector((0, 0.82, 0.57))
        else:
            tip, brow = Vector((0, n.y + 0.02, n.z + 0.03)), Vector((0, e.y + 0.14, e.z + 0.2))
            up = (brow - tip).normalized()
        out = X.cross(up).normalized()
        h = 0.66 * 1.3 * size
        lift = 0.1
        # a shell and not a board: over the muzzle and down the sides of the face, past the eyes
        we = (e.x + 0.08) * (0.9 + 0.1 * size)
        if style == "raised":
            be, de = 0.78, 0.22
        else:
            eye = Vector((0, e.y, e.z))
            be = (eye - tip).dot(up) / h
            de = (tip + up * (h * be) + out * lift - eye).dot(out) + 0.13
        rows = [(-0.05, 0.04, 0.02), (0.16, 0.12, 0.13), (be * 0.6, 0.6 * we + 0.05, 0.75 * de), (be - 0.02, we, de), (be + 0.2, we * 0.95, de * 0.55), (be + 0.32, we * 0.7, 0.08)]

        def at(b):
            """How wide the mask is at b, and how far down its sides come."""
            for (b0, w0, d0), (b1, w1, d1) in zip(rows, rows[1:]):
                if b <= b1:
                    t = max(0.0, min(1.0, (b - b0) / (b1 - b0)))
                    return w0 + (w1 - w0) * t, d0 + (d1 - d0) * t
            return rows[-1][1], rows[-1][2]

        def top(a, b, proud=0.012):
            """A point on the mask's brow and muzzle (a across, -1..1)."""
            w, d = at(b)
            return tip + up * (h * b) + X * (a * w * 0.9) + out * (lift + proud - 0.3 * d * abs(a))

        def wall(sg, b, t, proud=0.012):
            """A point on its side (t: 0 at the shoulder of the mask, 1 at its edge)."""
            w, d = at(b)
            return tip + up * (h * b) + X * (sg * (w + proud)) + out * (lift - d * (0.3 + 0.7 * t))
        half = style == "half"
        sides = (-1,) if half else (1, -1)
        cols = ((-1.0, 1.0), (-0.92, 0.3), (0.0, 0.0)) if half else ((-1.0, 1.0), (-0.92, 0.3), (0.0, 0.0), (0.92, 0.3), (1.0, 1.0))
        rings = []
        for b, w, d in rows:
            face = [tip + up * (h * b) + X * (c * w) + out * (lift - d * k) for c, k in cols]
            rings.append(face + [q - out * 0.03 - X * (0.03 * (1 if q.x > 0.01 else -1 if q.x < -0.01 else 0)) for q in reversed(face)])
        _add(r, "mask", g.loft(rings, caps=True), "Head", mat("mask_pale"), smooth=False)
        slits, sparks, marks, ears, cord = None, None, None, None, None
        for sg in sides:
            nx = Vector((sg, 0, 0))
            # the eyes it looks out of are the mask's: long and dark, a light far back in each
            slits = g.merge(slits, g.blade(wall(sg, be - 0.14, 0.48), wall(sg, be + 0.12, 0.28), 0.12 * size, normal=nx, belly=0.5))
            sparks = g.merge(sparks, g.ico(wall(sg, be - 0.01, 0.38, 0.03), 0.03 * size, sub=0))
            # red under each eye and down the cheek, and a stroke up the brow
            marks = g.merge(marks, g.blade(wall(sg, be - 0.2, 0.9), wall(sg, be + 0.04, 0.72), 0.06 * size, normal=nx, belly=0.5))
            marks = g.merge(marks, g.blade(wall(sg, be * 0.5, 0.75), wall(sg, be * 0.25, 0.55), 0.05 * size, normal=nx, belly=0.5))
            marks = g.merge(marks, g.blade(top(sg * 0.5, be + 0.02), top(sg * 0.62, be + 0.28), 0.07 * size, normal=out, belly=0.5))
            # the mask has ears of its own, a little wrong for the ears beneath
            ears = g.merge(ears, g.blade(top(sg * 0.6, be + 0.2, 0.0), top(sg * 0.85, be + 0.62, 0.2), 0.2 * size, normal=out, belly=0.3))
            if style != "raised":     # and a red cord ties it on
                cord = g.merge(cord, g.tube([wall(sg, be + 0.18, 0.5), Vector((sg * (e.x + 0.12), hb.y + 0.1, e.z)), Vector((sg * 0.06, hb.y + 0.32, e.z + 0.06)),
                                             Vector((sg * 0.14, hb.y + 0.44, e.z - 0.12)), Vector((sg * 0.18, hb.y + 0.48, e.z - 0.36))], [0.022, 0.022, 0.026, 0.02, 0.012], n=4))
        _add(r, "mask_ears", ears, "Head", mat("mask_pale"), smooth=False)
        _add(r, "mask_eyes", slits, "Head", mat("coal"))
        _add(r, "mask_sparks", sparks, "Head", field("eyes", 3.6))
        _add(r, "mask_marks", marks, "Head", mat("mask_red"))
        if cord:
            _add(r, "mask_cord", cord, "Head", mat("mask_red"), smooth=True)
        if not half:
            _add(r, "mask_brow", g.blade(top(0, be - 0.02), top(0, be + 0.2), 0.09 * size, normal=out, belly=0.5), "Head", field("brow", 2.6))
    return fn


def fox_two_faces(r, A, size):
    """Seen from the left and from the right it is not the same fox."""
    _paint_coat(r, lambda c: c.x < -0.004, mat("fur_mask"))


def _fox_back(style):
    def fn(r, A, size):
        geo, geo2, ws, ws2 = None, None, [], []
        if style == "leaves":         # leaves in its coat from the far side of things
            for i in range(12):
                t = i / 11
                y = A.n2.y * (1 - t) + (A.tail[1].y) * t
                x = 0.22 * math.sin(i * 2.3 + 0.5)
                b0 = Vector((x, y, _skin().top(y, half_width=0.3) - 0.5 * abs(x) - 0.02))
                bl = g.blade(b0, b0 + Vector((x * 0.9, 0.14, 0.2)) * size, 0.16 * size, normal=Vector((x, -0.3, 1)), belly=0.45)
                if i % 3 == 1:
                    geo2 = g.merge(geo2, bl)
                    ws2.extend([r.spine_weights(y)] * len(bl[0]))
                else:
                    geo = g.merge(geo, bl)
                    ws.extend([r.spine_weights(y)] * len(bl[0]))
            _add(r, "leaves", geo, ws, mat("leaf"))
            _add(r, "leaves_dry", geo2, ws2, mat("leaf_dry"))
        elif style == "feathers":     # there is usually a feather somewhere on it
            for i, (y, x, L) in enumerate(((A.n1.y, 0.12, 0.5), (A.t2.y, -0.16, 0.42), (A.tail[0].y, 0.08, 0.46))):
                b0 = Vector((x, y, _skin().top(y, half_width=0.25) - 0.04))
                bl = g.blade(b0, b0 + Vector((x * 1.5, 0.28, 0.42)) * (L / 0.5) * size, 0.13 * size, normal=Vector((1, 0, 0.2)), belly=0.5)
                _add(r, "feather_%d" % i, bl, [r.spine_weights(y)] * len(bl[0]), mat("feather_pale"))
    return fn


def _fox_carry(style):
    def fn(r, A, size):
        if style == "panniers":       # what the line dropped, in two bags
            y = A.t3.y + 0.62
            zt = _skin().top(y)
            gl._cape(r, A, "pannier_strap", y - 0.1, y + 0.1, 0.42, mat("leather"), steps=2, hem=0.0, flare=0.02)
            for sg in (1, -1):
                c = Vector((sg * (_skin().side(y, zt - 0.5) + 0.14), y, zt - 0.56))
                _add(r, "pannier_%d" % sg, g.ico(c, 1.0, sub=1, scale=(0.17 * size, 0.3 * size, 0.27 * size)), "Torso2", mat("leather"), smooth=True)
                _add(r, "pannier_flap_%d" % sg, g.box(c + Vector((sg * 0.1, 0, 0.13)), (0.16 * size, 0.5 * size, 0.2 * size), rot=(0, sg * 0.5, 0)), "Torso2", mat("leather_dark"))
                _add(r, "pannier_pin_%d" % sg, g.ico(c + Vector((sg * 0.18, 0, 0.04)), 0.045, sub=0), "Torso2", mat("metal_brass"))
        elif style == "pole":         # a ferryman's pole, and its lamp
            a = Vector((0.2, A.t3.y - 0.9, A.withers + 0.16))
            b = Vector((-0.24, A.back.y + 1.5, A.withers + 0.66))
            _add(r, "pole", g.tube([a, b], [0.045, 0.04], n=6), "Torso3", mat("wood"))
            for k, t in enumerate((0.36, 0.6)):
                c = a.lerp(b, t)
                _add(r, "pole_lash_%d" % k, _hoop(c, b - a, 0.06, 0.02, n=8), "Torso3", mat("cord"))
            gl._add_items(r, "pole_lamp", gl._lantern(b + Vector((0, 0.02, -0.02)), 0.2 * size, "lamp", 3.4), "Torso3")
        elif style == "cape":         # a short cape, as a storyteller wears
            gl._cape(r, A, "cape", A.n1.y - 0.05, A.t1.y + 0.1, 0.5 * size, mat("cape_red"), hem=0.03)
            _add(r, "cape_clasp", g.ico(Vector((0, A.chest_y - 0.02, A.sh.z + 0.42)), 0.075, sub=1, scale=(1, 0.5, 1)), "Torso3", mat("metal_brass"))
    return fn


def fox_courtier(r, A, size):
    """A stiff pale ruff, all the way round."""
    gl._ring_blades(r, "ruffc", A.neck["Neck2"], "Neck2", 18, 0.44 * size, 0.22, mat("fur_pale"), a0=-0.5, a1=1.5, sweep=0.14, out=1.0, lift=0.0, belly=0.5)
    gl._ring_blades(r, "ruffc2", A.neck["Neck2"], "Neck2", 16, 0.3 * size, 0.22, mat("fur_cream"), a0=-0.45, a1=1.55, sweep=0.3, out=1.0, lift=0.0, belly=0.5, grow=1.02)


def _fox_feet(style):
    def fn(r, A, size):
        if style == "webbed":         # webbed, and leaving rings
            pads, rings = None, None
            for tag, foot, bone in gl.FEET:
                f = r.bone(foot)
                pad = g.ico((f.x, f.y - 0.04, 0.04), 1.0, sub=1, scale=(0.21 * size, 0.28 * size, 0.035))
                _add(r, "web_" + tag, pad, bone, mat("fur_light"), smooth=True)
                _add(r, "ripple_" + tag, _hoop((f.x, f.y - 0.04, 0.02), Z, 0.36 * size, 0.014, n=12, sides=3), bone, field("ripple", 1.6))
        elif style == "snow":         # furred to the pad, and leaving no print
            gl._feet(r, 1.0 + 0.45 * size)
            gl._legs_painted(r, A, 0.34, mat("fur_pale"))
    return fn


def fox_fins(r, A, size):
    """A finned tail and a fin down the back, like something that crosses water for a living."""
    tb = _tailbones(r)
    geo = None
    for i in range(1, 8):
        d = (tb[i] - tb[i - 1]).normalized()
        up = Z - d * Z.dot(d)
        up = up.normalized() if up.length > 0.1 else X.copy()
        for sgn in (1, -1):
            b0 = tb[i] + up * (sgn * 0.12)
            geo = g.blade(b0, b0 + up * (sgn * (0.34 - 0.02 * i) * size) + d * 0.2, 0.34, normal=X, belly=0.4)
            _add(r, "tailfin_%d_%d" % (i, sgn), geo, "Tail%d" % (i + 1), mat("fin"), smooth=False)
    r.fin("backfin", A.t3.y + 0.1, A.back.y + 0.1, lambda t: (0.12 + 0.26 * math.sin(t * math.pi)) * size, mat("fin"), thickness=0.05, steps=14, sink=0.05, serrate=False)


def fox_dig(r, A, size):
    """Broad earth-stained forepaws, for going in after what is hidden."""
    for tag, foot, bone in gl.FEET[:2]:
        f = r.bone(foot)
        k = 1.0 + 0.55 * size
        r.deform(r.legs(tag), lambda p, f=f, k=k: Vector((f.x + (p.x - f.x) * k, f.y + 0.1 + (p.y - f.y - 0.1) * k, p.z)) if p.z < 0.34 else p)
        cl = None
        for dx in (-0.12, -0.04, 0.04, 0.12):
            b0 = Vector((f.x + dx * k, f.y - 0.04 * k, 0.08))
            cl = g.merge(cl, g.cone(b0, b0 + Vector((dx * 0.2, -0.3 * size, -0.07)), 0.045, n=5))
        _add(r, "digclaws_" + tag, cl, bone, mat("claw"))
    front = r._weights(r.legs("fl") + r.legs("fr"))
    me = r.mesh.data
    keep = {i for i, v in enumerate(me.vertices) if front[i] > 0.5}
    earth = mat("earth")
    if earth.name not in [m.name for m in me.materials]:
        me.materials.append(earth)
    slot = [m.name for m in me.materials].index(earth.name)
    for p in me.polygons:
        if all(i in keep for i in p.vertices) and (r.M @ p.center).z < 0.85:
            p.material_index = slot
    _add(r, "dirty_nose", g.ico(A.nose + Vector((0, 0.03, -0.02)), 0.09, sub=0), "Head", earth)


def fox_tail_rime(r, A, size):
    """White rime standing on its brush."""
    tb = _tailbones(r)
    for i in range(2, 8):
        d = (tb[i] - tb[i - 1]).normalized()
        u, v = _perp(d)
        geo = None
        for k in range(4):
            a = math.pi * (0.12 + 0.76 * k / 3 + (0.1 if i % 2 else 0.0))
            radial = u * math.cos(a) + v * math.sin(a)
            b0 = tb[i] + radial * 0.2
            geo = g.merge(geo, g.blade(b0, b0 + radial * (0.3 * size) + d * 0.12, 0.15, normal=radial, belly=0.2))
        _add(r, "tailrime_%d" % i, geo, "Tail%d" % (i + 1), mat("ice_pale") if i % 2 else mat("ice"), smooth=False)


def back_stripe(material):
    def fn(r, A, size):
        mid = (A.withers + A.belly) / 2
        _paint_coat(r, lambda c: abs(c.x) < 0.1 * size and c.z > mid, mat(material))
    return fn


def _fox_styles():
    G = gl.GROWS
    G[("back", "stripe")] = back_stripe("fur_pale")
    G[("back", "soot")] = back_stripe("soot")
    G[("whiskers", "long")] = fox_whiskers
    for st in ("sack", "prize"):
        G[("mouth", st)] = _fox_mouth(st)
    G[("tails", "two")] = _fox_tails([(0.42, 0.6)])
    G[("tails", "many")] = _fox_tails([(sg * a, lift) for a, lift in ((0.34, 0.92), (0.68, 0.72), (1.0, 0.5), (1.3, 0.26)) for sg in (1, -1)])
    for st in ("light", "white", "ring", "flame", "wisp"):
        G[("tip", st)] = _fox_tip(st)
    for st in ("worn", "raised", "half"):
        G[("mask", st)] = _fox_mask(st)
    G[("face", "two")] = fox_two_faces
    for st in ("leaves", "feathers"):
        G[("back", st)] = _fox_back(st)
    for st in ("panniers", "pole", "cape"):
        G[("carry", st)] = _fox_carry(st)
    G[("ruff", "courtier")] = fox_courtier
    for st in ("webbed", "snow"):
        G[("feet", st)] = _fox_feet(st)
    G[("fins", "fox")] = fox_fins
    G[("claws", "dig")] = fox_dig
    G[("tail", "rime")] = fox_tail_rime


# ======================================================================================
# The Stag
# ======================================================================================

def stag_species(r):
    """Tall on fine legs, the neck long and carried high, a narrow head, hooves."""
    head = _head(r)
    r.leg_length(-0.5)
    r.leg_girth(0.8)
    top = r.top(r.bone("Torso2").y)
    r.scale(bk.TORSO, (0, 0, top), (0.95, 1.0, 1.06))
    r.lengthen_chain(list(NECK), head, 1.35)
    r.rotate(list(NECK) + head, r.bone("Neck1"), X, math.radians(-24))
    r.rotate(head, r.bone("Neck3"), X, math.radians(20))
    r.scale(head, r.bone("Neck3"), (0.86, 1.0, 0.92))
    _ears(r, 1.15, 1.3, turn=lambda sg: (Y, sg * 0.85))
    r.scale(_tail(r), r.bone("Tail1"), 0.28)


def stag_ages(r, level):
    head, hb = _head(r), r.bone("Head")
    top = r.top(r.bone("Torso2").y)
    if level <= 1:                  # the fawn: all leg
        r.scale(head, hb, 1.22)
        eye = kit._eye(r)
        r.deform(head, lambda p: Vector((p.x, eye.y + (p.y - eye.y) * 0.72, p.z)) if p.y < eye.y - 0.04 else p)
        r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, 0.74)
        r.scale(bk.TORSO, (0, 0, top), (0.86, 1.0, 0.84))
        r.lengthen_chain(list(NECK), head, 0.8)
        r.leg_girth(0.92)
        _ears(r, 1.2, 1.3)
        _young_eyes(r, 0.1)
    elif level == 2:
        r.scale(head, hb, 1.08)
        r.scale(bk.TORSO, (0, 0, top), (0.94, 1.0, 0.95))
    elif level >= 4:
        r.scale(["Torso3", "Torso2"], (0, 0, top), (1.12, 1.0, 1.08))
        r.scale(list(NECK), r.bone("Neck2"), (1.18, 1.06, 1.0))
        r.leg_girth(1.08)
    kit._hooves(r, mat("horn"))


# The shapes a crown may take. beam: the points of the main beam from its root, each (out,
# back, up) against the head; tines: (how far along the beam, the way it points, how long);
# thick: against a plain antler; palm: (from which beam point, how broad) for a palmate one;
# cut: {side: how far along} for a beam that is broken off.
ANTLERS = {
    "spikes": dict(beam=[(0.05, -0.12, 0.2), (0.1, -0.36, 0.42)], tines=[(0.3, (0.4, -1, 0.2), 0.22)], thick=1.5),
    "lock": dict(beam=[(0.2, -0.05, 0.35), (0.42, -0.3, 0.6), (0.4, -0.72, 0.72)], tines=[(0.2, (0.2, -1, 0.3), 0.4), (0.5, (0.5, -0.6, 0.8), 0.42), (0.8, (-0.5, -0.3, 1), 0.36)], thick=1.6),
    "royal": dict(beam=[(0.18, 0.12, 0.5), (0.42, 0.2, 1.0), (0.5, 0.1, 1.5), (0.4, -0.1, 1.95)],
                  tines=[(0.08, (0.2, -1, 0.4), 0.5), (0.3, (0.4, -1, 0.5), 0.46), (0.5, (0.5, -0.9, 0.6), 0.44), (0.7, (0.5, -0.6, 0.9), 0.4), (0.88, (-0.4, 0.3, 1), 0.34)], thick=1.1),
    "broken": dict(beam=[(0.18, 0.12, 0.5), (0.42, 0.2, 1.0), (0.5, 0.1, 1.5), (0.4, -0.1, 1.95)],
                   tines=[(0.08, (0.2, -1, 0.4), 0.5), (0.3, (0.4, -1, 0.5), 0.46), (0.5, (0.5, -0.9, 0.6), 0.44), (0.7, (0.5, -0.6, 0.9), 0.4), (0.88, (-0.4, 0.3, 1), 0.34)], thick=1.3, cut={-1: 0.4}),
    "swept": dict(beam=[(0.14, 0.3, 0.25), (0.26, 0.9, 0.42), (0.3, 1.5, 0.5)], tines=[(0.35, (0.3, 0.6, 0.8), 0.3), (0.7, (0.2, 0.7, 0.7), 0.25)]),
    "plough": dict(beam=[(0.3, -0.2, 0.2), (0.55, -0.6, 0.3), (0.6, -1.0, 0.2)], tines=[(0.5, (0.3, -1, 0.5), 0.3), (0.75, (0.6, -0.8, 0.3), 0.3), (1.0, (0, -1, 0.1), 0.25)], thick=1.5, palm=(1, 0.5)),
    "wisp": dict(beam=[(0.12, 0.35, 0.3), (0.22, 1.0, 0.55), (0.24, 1.8, 0.7), (0.2, 2.5, 0.75)], tines=[(0.4, (0.2, 0.5, 0.9), 0.3)], thick=0.7),
    "lyre": dict(beam=[(0.3, 0.05, 0.5), (0.5, 0.1, 1.0), (0.3, 0.1, 1.5), (0.12, 0.05, 1.9)], tines=[(0.15, (0.2, -1, 0.5), 0.4), (0.45, (0.8, -0.5, 0.5), 0.35), (0.7, (0.6, -0.4, 0.7), 0.3)]),
    "pillar": dict(beam=[(0.14, 0.08, 0.7), (0.2, 0.12, 1.4), (0.22, 0.12, 2.1)], tines=[(0.2, (0.3, -1, 0.4), 0.35), (0.5, (0.7, -0.6, 0.4), 0.3), (0.75, (0.7, -0.4, 0.6), 0.28), (0.95, (-0.6, 0, 0.8), 0.24)], thick=1.2),
    "wide": dict(beam=[(0.5, 0.0, 0.4), (1.0, 0.05, 0.75), (1.35, 0.0, 1.2), (1.45, -0.1, 1.65)],
                 tines=[(0.2, (0, -1, 0.6), 0.45), (0.45, (0.2, -0.8, 0.8), 0.45), (0.7, (0, -0.5, 1), 0.42), (0.9, (-0.5, 0, 1), 0.35)], thick=1.3),
    "branch": dict(beam=[(0.2, 0.1, 0.45), (0.3, 0.3, 0.85), (0.55, 0.25, 1.2), (0.5, 0.5, 1.55)],
                   tines=[(0.2, (0.6, -0.7, 0.5), 0.35), (0.4, (-0.3, 0.6, 0.8), 0.3), (0.6, (0.8, 0.2, 0.6), 0.4), (0.8, (0.2, -0.6, 0.9), 0.3), (0.9, (0.7, 0.6, 0.5), 0.25)]),
    "palm": dict(beam=[(0.35, 0.0, 0.3), (0.75, 0.1, 0.55), (1.15, 0.15, 0.75)],
                 tines=[(0.6, (0.3, -1, 0.6), 0.3), (0.75, (0.6, -0.6, 0.8), 0.32), (0.9, (0.8, 0, 0.8), 0.32), (1.0, (0.6, 0.7, 0.6), 0.3)], thick=1.3, palm=(1, 0.55)),
    "slim": dict(beam=[(0.12, 0.1, 0.6), (0.25, 0.15, 1.2), (0.22, 0.05, 1.75)], tines=[(0.25, (0.2, -1, 0.6), 0.36), (0.6, (0.6, -0.5, 0.8), 0.3)], thick=0.75),
    "eye": dict(beam=[(0.3, 0.05, 0.35), (0.55, 0.08, 0.8), (0.55, 0.08, 1.3), (0.3, 0.05, 1.75), (0.06, 0.02, 1.9)], tines=[(0.1, (0.2, -1, 0.4), 0.3), (0.3, (1, 0, 0.2), 0.22), (0.55, (1, 0, 0.6), 0.2)], thick=0.9),
    "droop": dict(beam=[(0.4, 0.1, 0.3), (0.8, 0.2, 0.4), (1.1, 0.3, 0.25), (1.3, 0.4, 0.0)], tines=[(0.35, (0, 0, 1), 0.25), (0.65, (0.2, 0, 1), 0.2)], thick=0.9),
    "gnarl": dict(beam=[(0.22, 0.0, 0.3), (0.4, -0.1, 0.6), (0.38, 0.1, 0.9)], tines=[(0.3, (0.8, -0.5, 0.3), 0.25), (0.6, (-0.4, 0.6, 0.7), 0.25), (0.9, (0.7, 0.3, 0.6), 0.22)], thick=2.0),
    "briar": dict(beam=[(0.3, 0.0, 0.4), (0.6, -0.05, 0.85), (0.7, 0.15, 1.3), (0.55, 0.3, 1.7)],
                  tines=[(0.2, (0.8, -0.6, 0.3), 0.4), (0.45, (-0.4, 0.7, 0.6), 0.35), (0.65, (0.9, 0.1, 0.5), 0.4), (0.85, (0.3, -0.7, 0.7), 0.3)], thick=1.7),
    "rime": dict(beam=[(0.25, 0.1, 0.5), (0.55, 0.15, 0.95), (0.65, 0.05, 1.45), (0.5, -0.1, 1.9)],
                 tines=[(0.1, (0.2, -1, 0.4), 0.45), (0.35, (0.6, -0.8, 0.5), 0.4), (0.6, (0.7, -0.3, 0.8), 0.38), (0.85, (-0.4, 0.3, 1), 0.3)]),
    "watch": dict(beam=[(0.15, 0.1, 0.5), (0.3, 0.15, 0.95), (0.28, 0.05, 1.35)], tines=[(0.3, (0.3, -1, 0.5), 0.32), (0.7, (0.7, -0.3, 0.7), 0.26)]),
    "crook": dict(beam=[(0.4, 0.05, 0.4), (0.85, 0.1, 0.7), (1.05, 0.05, 1.1), (0.9, -0.1, 1.4), (0.65, -0.15, 1.3)], tines=[(0.15, (0.1, -1, 0.5), 0.4), (0.45, (0.3, -0.8, 0.7), 0.35)], thick=1.2),
    "roof": dict(beam=[(0.5, -0.05, 0.25), (1.1, -0.1, 0.4), (1.7, -0.1, 0.35), (2.1, 0.0, 0.15)],
                 tines=[(0.3, (0.1, -1, 0.3), 0.4), (0.55, (0.2, -1, 0.2), 0.4), (0.8, (0.3, -1, 0.1), 0.35), (0.5, (0.1, 1, 0.2), 0.35)], thick=1.4, palm=(1, 0.7)),
    "bracket": dict(beam=[(0.14, 0.1, 0.55), (0.26, 0.15, 1.05), (0.24, 0.1, 1.5)], tines=[(0.12, (0.15, -1, 0.25), 0.75), (0.6, (0.7, -0.4, 0.6), 0.28)], thick=1.05),
    "cradle": dict(beam=[(0.35, 0.05, 0.4), (0.6, 0.08, 0.85), (0.5, 0.08, 1.3), (0.25, 0.05, 1.55)], tines=[(0.15, (0.2, -1, 0.4), 0.5), (0.5, (1, -0.2, 0.4), 0.3), (0.75, (0.8, 0.2, 0.7), 0.28)], thick=1.1),
    "stone": dict(beam=[(0.25, 0.05, 0.4), (0.5, 0.1, 0.8), (0.55, 0.1, 1.25)], tines=[(0.3, (0.3, -1, 0.4), 0.35), (0.7, (0.8, 0, 0.6), 0.3)], thick=2.2),
    "candles": dict(beam=[(0.3, 0.0, 0.3), (0.6, 0.0, 0.45), (0.9, 0.0, 0.5)], tines=[(0.33, (0, 0, 1), 0.45), (0.66, (0, 0, 1), 0.5), (1.0, (0, 0, 1), 0.55)], thick=0.8),
    "rack": dict(beam=[(0.45, 0.0, 0.45), (0.9, 0.05, 0.95), (1.1, 0.0, 1.5)],
                 tines=[(0.15, (0.1, -1, 0.4), 0.45), (0.4, (0.5, -0.7, 0.6), 0.45), (0.65, (0.6, -0.3, 0.9), 0.42), (0.85, (0.3, 0.4, 1), 0.38)], thick=1.3),
    "elder": dict(beam=[(0.4, 0.1, 0.4), (0.85, 0.2, 0.75), (1.1, 0.25, 1.2), (1.05, 0.2, 1.6)],
                  tines=[(0.12, (0.1, -1, 0.3), 0.5), (0.4, (0.4, -0.8, 0.5), 0.4), (0.7, (0.8, -0.2, 0.7), 0.35), (0.9, (0.6, 0.5, 0.7), 0.3)], thick=1.5, palm=(2, 0.45)),
}
HORN = {"bone": "bone", "velvet": "velvet", "stone": "slate_light", "ice": "ice", "dark": "horn", "wood": "bark_light", "pale": "mask_pale"}


def _along(pts, t):
    """The point a share t of the way along a line through points."""
    lens = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    want = max(0.0, min(1.0, t)) * sum(lens)
    for i, L in enumerate(lens):
        if want <= L or i == len(lens) - 1:
            return pts[i].lerp(pts[i + 1], want / L if L > 1e-9 else 0.0)
        want -= L
    return pts[-1]


def _antler(sg, base, P, size):
    """One antler from its root: its geometry, its points, its beam, its tines (root, tip)."""
    beam = [V(base)] + [V(base) + Vector((sg * x, y, z)) * size for x, y, z in P["beam"]]
    cut = P.get("cut", {}).get(sg)
    rb = 0.078 * P.get("thick", 1.0) * (0.75 + 0.25 * size)
    tines = []
    for t, (x, y, z), L in P.get("tines", ()):
        if cut is not None and t > cut:
            continue
        a = _along(beam, t)
        tines.append((a, a + Vector((sg * x, y, z)).normalized() * (L * size), rb * (0.72 - 0.36 * t)))
    n = len(beam)
    radii = [rb * (1.0 - 0.78 * i / (n - 1)) for i in range(n)]
    if cut is not None:
        end = _along(beam, cut)
        m = max(1, int(cut * (n - 1)) + 1)
        beam, radii = beam[:m] + [end], radii[:m] + [radii[min(m, n - 1)] * 1.15]
    geo = g.tube(beam, radii, n=5)
    tips = [] if cut is not None else [beam[-1]]
    for a, b, rt in tines:
        geo = g.merge(geo, g.tube([a, a.lerp(b, 0.55) + Vector((0, 0, 0.05 * size)), b], [rt, rt * 0.72, rt * 0.2], n=5))
        tips.append(b)
    palm = P.get("palm")
    if palm and cut is None:
        i0, w = palm
        pts = beam[i0:]
        d = (pts[-1] - pts[0]).normalized()
        nrm = d.cross(Y)
        nrm = nrm.normalized() if nrm.length > 0.1 else Z.copy()
        geo = g.merge(geo, g.tongue(pts, [w * 1.5 * size * k for k in ([0.7] + [1.0] * (len(pts) - 2) + [0.55])], thick=0.12, normal=nrm))
    return geo, tips, beam, [(a, b) for a, b, _ in tines]


def _stag_horn(kind):
    def fn(r, A, size):
        _S["horn"] = HORN[kind]
    return fn


def _stag_crown(shape):
    def fn(r, A, size):
        hb = A.head
        top = _skin().top(hb.y + 0.08, half_width=0.13, window=0.12)
        m = mat(_S.get("horn", "bone"))
        rack = {"tips": [], "beams": [], "tines": [], "mid": Vector((0, hb.y + 0.1, top)), "size": size}
        if shape == "bumps":          # two soft bumps where the crown will be
            geo = None
            for sg in (1, -1):
                c = Vector((sg * 0.13, hb.y + 0.1, top - 0.02))
                geo = g.merge(geo, g.ico(c, 0.085 * size, sub=1, scale=(1, 1, 1.25)))
                rack["tips"].append((c + Vector((0, 0, 0.1)), sg))
            _add(r, "bumps", geo, "Head", mat("velvet"), smooth=True)
        else:
            geo = None
            for sg in (1, -1):
                ge, tips, beam, tines = _antler(sg, Vector((sg * 0.13, hb.y + 0.1, top - 0.06)), ANTLERS[shape], size)
                geo = g.merge(geo, ge)
                rack["tips"] += [(p, sg) for p in tips]
                rack["beams"].append((sg, beam))
                rack["tines"] += [(a, b, sg) for a, b in tines]
            _add(r, "antlers", geo, "Head", m, smooth=True)
        _S["rack"] = rack
    return fn


def _stag_hung(style):
    def fn(r, A, size):
        rack = _S.get("rack")
        if not rack:
            return
        tips, beams, tines, mid, cs = rack["tips"], rack["beams"], rack["tines"], rack["mid"], rack["size"]
        H = "Head"
        if style == "points":         # the field at every point
            geo = None
            for p, _ in tips:
                geo = g.merge(geo, g.ico(p, 0.045 * size, sub=0))
            _add(r, "points", geo, H, field("points", 3.0))
        elif style == "moss":         # moss on the brow-tines
            geo, hang = None, None
            for sg, beam in beams:
                for k, t in enumerate((0.12, 0.3, 0.5, 0.72)):
                    c = _along(beam, t)
                    geo = g.merge(geo, g.ico(c + Vector((0, 0, 0.04)), (0.11 - 0.015 * k) * size, sub=1, scale=(1.2, 1.2, 0.7)))
                    hang = g.merge(hang, g.blade(c, c + Vector((sg * 0.03, 0.02, -0.26 * size)), 0.1, normal=Y, belly=0.5))
            _add(r, "crown_moss", geo, H, mat("moss"), smooth=True)
            _add(r, "crown_moss_hang", hang, H, mat("moss"))
        elif style == "leaves":
            geo = None
            for i, (p, sg) in enumerate(tips):
                for k in range(2):
                    geo = g.merge(geo, g.blade(p, p + Vector((sg * (0.12 + 0.1 * k), 0.1 - 0.2 * k, 0.16)) * size, 0.14 * size, normal=Vector((0, 0.5, 1)), belly=0.45))
            _add(r, "crown_leaves", geo, H, mat("leaf"))
        elif style == "flowers":      # its crown flowers by midsummer
            petals, hearts = None, None
            spots = [p for p, _ in tips]
            for sg, beam in beams:
                spots += [_along(beam, t) + Vector((sg * 0.05, -0.05, 0.05)) for t in (0.25, 0.5, 0.75)]
            for p in spots:
                petals = g.merge(petals, g.ico(p, 0.1 * size, sub=0, scale=(1, 1, 0.55)))
                hearts = g.merge(hearts, g.ico(p + Vector((0, 0, 0.03 * size)), 0.04 * size, sub=0))
            _add(r, "crown_petals", petals, H, mat("petal"), smooth=True)
            _add(r, "crown_hearts", hearts, H, field("bloom", 2.4))
        elif style == "weed":         # river weed in its tines
            geo = None
            for i, (p, sg) in enumerate(tips):
                L = (0.5 + 0.3 * math.sin(i * 1.7) ** 2) * size
                geo = g.merge(geo, g.tongue([p, p + Vector((sg * 0.03, 0.03, -L * 0.5)), p + Vector((sg * -0.02, 0.06, -L))], [0.1, 0.12, 0.02], thick=0.25, normal=Y))
            _add(r, "crown_weed", geo, H, mat("weed"))
        elif style == "briar":        # briar grown through it, in flower
            canes, thorns, flowers = None, None, None
            for side in (1, -1):
                ts = [p for p, sg in tips if sg == side]
                for a, b in zip(ts, ts[1:] + ts[:1]):
                    top = (a + b) / 2 + Vector((side * 0.16, 0.0, 0.28)) * size
                    pts = [a, a.lerp(top, 0.6) + Vector((0, 0, 0.05)), top, b.lerp(top, 0.6) + Vector((0, 0, 0.05)), b]
                    canes = g.merge(canes, g.tube(pts, [0.02] * 5, n=4, caps=False))
                    for q in pts[1:4]:
                        thorns = g.merge(thorns, g.cone(q, q + Vector((side * 0.08, -0.05, 0.07)), 0.022, n=4))
                    flowers = g.merge(flowers, g.ico(top, 0.07 * size, sub=1, scale=(1, 1, 0.6)))
            _add(r, "briar", canes, H, mat("bark"))
            _add(r, "briar_thorns", thorns, H, mat("bark_light"))
            _add(r, "briar_flowers", flowers, H, mat("petal"), smooth=True)
        elif style == "birds":        # small birds nest in it
            for k, (sg, beam) in enumerate(beams):
                c = _along(beam, 0.5 + 0.2 * k) + Vector((0, 0, 0.1))
                body = g.merge(g.ico(c, 0.085, sub=1, scale=(0.8, 1.2, 0.85)), g.ico(c + Vector((0, -0.09, 0.06)), 0.055, sub=1),
                               g.blade(c + Vector((0, 0.07, 0.0)), c + Vector((0, 0.22, 0.05)), 0.08, normal=Z))
                _add(r, "bird_%d" % k, body, H, mat("crow_pale" if k else "feather_mid"), smooth=True)
                _add(r, "bird_beak_%d" % k, g.cone(c + Vector((0, -0.13, 0.06)), c + Vector((0, -0.19, 0.05)), 0.018, n=4), H, mat("beak"))
        elif style == "lamp":         # a lamp hangs from one brow-tine
            right = [b for a, b, sg in tines if sg == -1] or [p for p, _ in tips]
            gl._add_items(r, "crownlamp", gl._lantern(right[0] + Vector((0, 0, 0.0)), 0.2 * size, "lamp", 3.6), H)
        elif style == "flame":        # a small flame sits in the fork of its crown
            c = mid + Vector((0, 0, 0.55 * cs))
            _add(r, "crown_dish", g.lathe([(0.03, -0.1), (0.16, -0.06), (0.2, 0.0)], n=7, centre=c), H, mat("metal_dark"))
            fl = None
            for dx, h in ((0.0, 0.5), (0.08, 0.32), (-0.07, 0.36)):
                f0 = c + Vector((dx, 0, 0.0))
                fl = g.merge(fl, g.tongue([f0, f0 + Vector((dx * 0.4, 0, h * 0.45 * size)), f0 + Vector((-dx * 0.3, 0, h * size))], [0.17 * size, 0.15 * size, 0.02], thick=0.7, normal=Y))
            _add(r, "crown_flame", fl, H, field("flame", 3.6))
        elif style == "ring":         # a pale ring hangs in its crown
            _add(r, "crown_ring", _hoop(mid + Vector((0, 0.08, 0.78 * cs)), Vector((0, 0.25, 1)), 0.28 * size, 0.026), H, field("crown", 3.5))
        elif style == "halo":         # the air rings round its head
            c = mid + Vector((0, 0.0, 0.5 * cs))
            _add(r, "halo", _hoop(c, Y, 1.0 * size, 0.032, n=22), H, field("ring", 3.2))
            _add(r, "halo2", _hoop(c + Vector((0, -0.5, -0.3)), Y, 0.56 * size, 0.024, n=18), H, field("ring", 2.6))
            _add(r, "halo3", _hoop(c + Vector((0, -0.95, -0.5)), Y, 0.3 * size, 0.018, n=14), H, field("ring", 2.2))
        elif style == "script":       # lines of small writing cut into the beam
            geo = None
            for sg, beam in beams:
                for t in (0.16, 0.26, 0.36, 0.46, 0.56, 0.66, 0.76):
                    c = _along(beam, t)
                    d = _along(beam, t + 0.02) - c
                    geo = g.merge(geo, _hoop(c, d, 0.085 * (1.0 - 0.6 * t), 0.014, n=8, sides=3))
            _add(r, "script", geo, H, field("script", 2.8))
        elif style == "ribbons":      # a ribbon for each of the cohort
            for i, (p, sg) in enumerate(tips):
                L = (0.42 + 0.24 * math.sin(i * 2.3) ** 2) * size
                strip = g.tongue([p, p + Vector((sg * 0.05, 0.05, -L * 0.5)), p + Vector((sg * -0.03, 0.1, -L))], [0.09, 0.09, 0.07], thick=0.2, normal=Y)
                _add(r, "ribbon_%d" % i, strip, H, mat(("ribbon_a", "ribbon_b", "ribbon_c")[i % 3]))
        elif style == "tokens":       # teeth, tags and bits of collar, on wire
            wire, hung, bright = None, None, None
            for side in (1, -1):
                ts = [p for p, sg in tips if sg == side]
                for a, b in zip(ts, ts[1:]):
                    sag = (a + b) / 2 + Vector((0, 0, -0.12))
                    wire = g.merge(wire, g.tube([a, sag, b], [0.008] * 3, n=3, caps=False))
                    for k, t in enumerate((0.25, 0.5, 0.75)):
                        q = a.lerp(sag, t * 2) if t < 0.5 else sag.lerp(b, t * 2 - 1)
                        tok = g.blade(q, q + Vector((0, 0.0, -(0.16 + 0.05 * k) * size)), 0.09 * size, normal=Y, belly=0.55)
                        if k == 1:
                            bright = g.merge(bright, tok)
                        else:
                            hung = g.merge(hung, tok)
            _add(r, "token_wire", wire, H, mat("metal_iron"))
            _add(r, "tokens", hung, H, mat("bone"))
            _add(r, "tokens_b", bright, H, mat("metal_brass"))
        elif style == "icicles":      # frost on every tine
            geo = None
            for i, (p, sg) in enumerate(tips):
                geo = g.merge(geo, g.cone(p, p + Vector((0, 0, -(0.24 + 0.12 * math.sin(i * 1.3) ** 2) * size)), 0.04, n=5))
            for sg, beam in beams:
                for t in (0.3, 0.5, 0.7, 0.85):
                    c = _along(beam, t)
                    geo = g.merge(geo, g.cone(c, c + Vector((0, 0, -0.2 * size)), 0.035, n=5))
            _add(r, "icicles_crown", geo, H, mat("ice_pale"))
        elif style == "lichen":       # lichen on its crown
            geo = None
            for sg, beam in beams:
                for k, t in enumerate((0.2, 0.42, 0.63, 0.85)):
                    c = _along(beam, t)
                    geo = g.merge(geo, g.ico(c + Vector((sg * 0.05, -0.04, 0.03)), 0.1 * size, sub=1, scale=(1, 1, 0.35), rot=(0.6, 0.3 * k, 0)))
            _add(r, "lichen", geo, H, mat("lichen"), smooth=True)
        elif style == "candles":      # small cold lights at its points
            wax, lit = None, None
            for p, sg in tips:
                wax = g.merge(wax, g.tube([p, p + Vector((0, 0, 0.1 * size))], 0.03, n=5))
                f0 = p + Vector((0, 0, 0.1 * size))
                lit = g.merge(lit, g.tongue([f0, f0 + Vector((0, 0, 0.1 * size)), f0 + Vector((0, 0, 0.24 * size))], [0.08 * size, 0.075 * size, 0.01], thick=0.8, normal=Y))
            _add(r, "candle_wax", wax, H, mat("wax"))
            _add(r, "candle_flames", lit, H, field("flame", 3.4))
        elif style == "eye":          # the crown closes round an eye of light
            c = mid + Vector((0, 0.06, 1.05 * cs))
            _add(r, "crown_eye", g.ico(c, 0.17 * size, sub=1, scale=(1.0, 0.45, 1.5)), H, field("eyes", 3.8))
            _add(r, "crown_eyelid", g.blade(c + Vector((0, 0.03, -0.36 * size)), c + Vector((0, 0.03, 0.36 * size)), 0.52 * size, normal=Y, belly=0.5), H, mat("fur_pale"))
        elif style == "cloth":        # old pale strips hanging from it, like lichen from a branch
            geo = None
            for sg, beam in beams:
                for k in range(7):
                    c = _along(beam, 0.2 + 0.12 * k)
                    L = (0.32 + 0.22 * math.sin(k * 1.9) ** 2) * size
                    geo = g.merge(geo, g.tongue([c, c + Vector((0, 0.03, -L * 0.5)), c + Vector((sg * 0.02, 0.05, -L))], [0.1, 0.1, 0.03], thick=0.2, normal=Y))
            _add(r, "crown_cloth", geo, H, mat("lichen"))
        elif style == "fawnlight":    # whoever is smallest is walking under it
            c = Vector((0.0, A.head.y - 0.45, A.sh.z - 0.2))
            _add(r, "fawnlight", g.ico(c, 0.13 * size, sub=1, scale=(0.8, 1.2, 1.0)), "Torso3", field("mote", 3.0))
            _add(r, "fawnlight_head", g.ico(c + Vector((0, -0.16, 0.12)), 0.08 * size, sub=1), "Torso3", field("mote", 3.0))
    return fn


def stag_throat(r, A, size):
    """A throat that swells before it calls."""
    nk = _neck(r)
    c = nk.throat(0.55, -0.1)
    _add(r, "throat_sac", g.ico(c, 0.34 * size, sub=1, scale=(0.9, 0.9, 1.25)), "Neck2", mat("fur_cream"), smooth=True)
    _add(r, "throat_seam", g.blade(c + Vector((0, -0.32 * size, 0.2 * size)), c + Vector((0, -0.3 * size, -0.3 * size)), 0.09, normal=Y, belly=0.5), "Neck2", field("voice", 2.2))


def _stag_breath(style):
    def fn(r, A, size):
        n = A.nose
        geo = None
        if style == "wisp":           # you see its breath before you see it: it leaves it in puffs, and they rise
            for d, rad, dx, dz in ((0.16, 0.055, 0.02, -0.03), (0.4, 0.085, -0.04, 0.02), (0.7, 0.115, 0.05, 0.12), (0.98, 0.075, -0.03, 0.26)):
                c = n + Vector((dx, -d * size, -0.05 + dz * size))
                geo = g.merge(geo, g.ico(c, rad * size, sub=2, scale=(1.0, 1.3, 0.8)))
        else:                         # breath that hangs behind it
            for k, (dx, L) in enumerate(((0.3, 1.5), (-0.3, 1.2), (0.36, 2.2))):
                p0 = n + Vector((dx * 0.4, 0.2, 0.05))
                geo = g.merge(geo, g.tongue([p0, p0 + Vector((dx, L * 0.3, 0.2)) * size, p0 + Vector((dx * 1.3, L * 0.7, 0.3)) * size, p0 + Vector((dx, L, 0.2)) * size],
                                            [0.08, 0.2, 0.18, 0.02], thick=0.5, normal=X))
        _add(r, "breath", geo, "Head", mat("ash"), smooth=True)
    return fn


def stag_bark(r, A, size):
    """Its hide stands in thick overlapping plates along the flank, like bark."""
    sk = _skin()
    zmid = (A.withers + A.belly) / 2
    dark, pale, wd, wp = None, None, [], []
    for row, (dz, sc) in enumerate(((0.3, 1.0), (-0.04, 1.12), (-0.36, 0.9))):
        for i in range(5):
            y = A.t3.y - 0.2 + 0.4 * i + 0.14 * (row % 2)
            z = zmid + dz
            for sg in (1, -1):
                c = Vector((sg * (sk.side(y, z) + 0.02), y, z))
                geo = g.ico(c, 1.0, sub=0, scale=(0.09 * size, 0.27 * sc, 0.25 * sc), rot=(0.0, 0.0, sg * -0.16))
                if (i + row) % 2:
                    dark = g.merge(dark, geo)
                    wd.extend([r.spine_weights(y)] * len(geo[0]))
                else:
                    pale = g.merge(pale, geo)
                    wp.extend([r.spine_weights(y)] * len(geo[0]))
    _add(r, "bark", dark, wd, mat("bark"), smooth=False)
    _add(r, "bark_b", pale, wp, mat("bark_light"), smooth=False)


def _stag_back(style):
    def fn(r, A, size):
        geo, ws = None, []
        sk = _skin()
        if style == "moss":           # moss on its back
            for i in range(9):
                t = i / 8
                y = A.t3.y - 0.1 + (A.back.y - A.t3.y + 0.4) * t
                x = 0.16 * math.sin(i * 2.1)
                b = g.ico((x, y, sk.top(y, half_width=0.25) - 0.3 * abs(x) + 0.01), (0.2 - 0.05 * (i % 2)) * size, sub=1, scale=(1.1, 1.3, 0.42))
                geo = g.merge(geo, b)
                ws.extend([r.spine_weights(y)] * len(b[0]))
            _add(r, "back_moss", geo, ws, mat("moss"), smooth=True)
        elif style == "spots":        # a fawn's dappled back
            for i in range(14):
                t = (i // 2) / 6
                sg = 1 if i % 2 else -1
                y = A.t3.y + 0.05 + (A.back.y - A.t3.y + 0.2) * t + 0.08 * sg
                z = sk.top(y, half_width=0.3) - 0.2 - 0.16 * ((i // 2) % 2)
                c = Vector((sg * (sk.side(y, z) + 0.01), y, z))
                b = g.ico(c, 0.11 * size, sub=1, scale=(0.35, 1.0, 1.0))
                geo = g.merge(geo, b)
                ws.extend([r.spine_weights(y)] * len(b[0]))
            _add(r, "spots", geo, ws, mat("fur_cream"), smooth=True)
    return fn


def _stag_legs(style):
    def fn(r, A, size):
        if style == "mould":          # leaf-mould to the hock
            gl._legs_painted(r, A, 0.75 * size, mat("earth"))
        elif style == "knees":        # its knees are grey with standing
            legs = r._weights(r.legs())
            me = r.mesh.data
            keep = {i for i, v in enumerate(me.vertices) if legs[i] > 0.5}
            knee = mat("knee")
            if knee.name not in [m.name for m in me.materials]:
                me.materials.append(knee)
            slot = [m.name for m in me.materials].index(knee.name)
            for p in me.polygons:
                z = (r.M @ p.center).z
                if all(i in keep for i in p.vertices) and 0.62 < z < 1.05:
                    p.material_index = slot
        elif style == "wet":          # wet to the chest
            line = A.sh.z + 0.05
            _paint_coat(r, lambda c: c.z < line, mat("wet"))
        elif style == "feather":      # broad hooves, feathered at the fetlock
            gl._feet(r, 1.0 + 0.45 * size, height=0.26)
            for tag, foot, bone in gl.FEET:
                f = r.bone(foot)
                geo = None
                for k in range(6):
                    a = k * math.pi / 3
                    b0 = Vector((f.x + 0.09 * math.cos(a), f.y + 0.1 + 0.09 * math.sin(a), 0.34))
                    geo = g.merge(geo, g.blade(b0, b0 + Vector((0.14 * math.cos(a), 0.14 * math.sin(a), -0.24)) * size, 0.13, normal=Vector((math.cos(a), math.sin(a), 0.3)), belly=0.4))
                _add(r, "fetlock_" + tag, geo, bone, mat("fur_cream"))
    return fn


def stag_hands(r, A, size):
    """One flank worn smooth and faintly bright where twelve hands have touched it."""
    zmid = (A.withers + A.belly) / 2 + 0.12
    for sg in (1, -1):
        geo = None
        for k, (dy, dz) in enumerate(((0.0, 0.0), (0.42, 0.14), (0.26, -0.26), (-0.3, -0.12), (0.66, -0.1))):
            y = A.t2.y + dy
            z = zmid + dz
            x = sg * (_skin().side(y, z) + 0.012)
            geo = g.merge(geo, g.ico((x, y, z), 0.1 * size, sub=1, scale=(0.18, 1.0, 1.1)))
            for f in range(4):
                geo = g.merge(geo, g.ico((x, y - 0.09 + 0.06 * f, z + 0.14 + 0.02 * math.sin(f * 1.6)), 0.035 * size, sub=0, scale=(0.3, 1.0, 1.8)))
        _add(r, "hands_%d" % sg, geo, "Torso2", field("hands", 1.5))


def stag_plough(r, A, size):
    """A plough before its chest, like the one on the front of the car."""
    apex = Vector((0, A.chest_y - 0.75 * size, 0.42))
    geo = g.tube([apex, apex + Vector((0, 0.1, 0.55))], [0.05, 0.05], n=5)
    for sg in (1, -1):
        for k in range(5):
            t = k / 4
            a = apex + Vector((0, 0.02, 0.1 + 0.5 * t))
            b = Vector((sg * (0.5 + 0.1 * t), A.chest_y + 0.25, 0.5 + 0.75 * t))
            geo = g.merge(geo, g.tube([a, b], [0.04, 0.04], n=4))
        geo = g.merge(geo, g.tube([Vector((sg * 0.5, A.chest_y + 0.25, 0.5)), Vector((sg * 0.6, A.chest_y + 0.25, 1.25)), Vector((sg * 0.3, A.chest_y + 0.2, A.sh.z + 0.25))], [0.05, 0.05, 0.05], n=5))
    _add(r, "plough", geo, "Torso3", mat("metal_iron"))
    _add(r, "plough_lamp", g.ico(apex + Vector((0, 0.0, 0.66)), 0.09, sub=1), "Torso3", field("lamp", 3.2))


def _stag_styles():
    G = gl.GROWS
    for k in HORN:
        G[("horn", k)] = _stag_horn(k)
    for shape in list(ANTLERS) + ["bumps"]:
        G[("crown", shape)] = _stag_crown(shape)
    for st in ("points", "moss", "leaves", "flowers", "weed", "briar", "birds", "lamp", "flame", "ring", "halo", "script", "ribbons", "tokens", "icicles", "lichen", "candles", "eye", "cloth", "fawnlight"):
        G[("hung", st)] = _stag_hung(st)
    G[("throat", "sac")] = stag_throat
    for st in ("wisp", "trail"):
        G[("breath", st)] = _stag_breath(st)
    G[("hide", "bark")] = stag_bark
    for st in ("moss", "spots"):
        G[("back", st)] = _stag_back(st)
    for st in ("mould", "knees", "wet", "feather"):
        G[("legs", st)] = _stag_legs(st)
    G[("flank", "hands")] = stag_hands
    G[("chest", "plough")] = stag_plough


# ======================================================================================
# The Drake
# ======================================================================================

def drake_species(r):
    """Long in the neck and longer in the tail, low on thick legs, a wedge of a head."""
    head = _head(r)
    r.scale(bk.TORSO, (0, 0, r.top(r.bone("Torso2").y)), (0.9, 1.0, 0.9))
    r.stretch_y(-0.6, 0.4, 1.12)
    r.leg_length(0.36)
    r.leg_girth(1.18)
    r.lengthen_chain(list(NECK), head, 1.9)
    r.scale(list(NECK), r.bone("Neck1"), (0.8, 1.0, 0.8))
    r.rotate(list(NECK) + head, r.bone("Neck1"), X, math.radians(-52))
    r.rotate(head, r.bone("Neck3"), X, math.radians(50))
    r.scale_along(head, r.bone("Neck3"), r.bone("Head") - r.bone("Neck3"), 1.3)
    r.scale(head, r.bone("Neck3"), (1.04, 1.0, 0.72))
    _ears(r, 0.3, 0.08)
    e = kit._eye(r)
    lid = e.z + 0.05

    def flat(p):
        q = p.copy()
        if q.z > lid:                 # the dome of a dog's skull comes down to a flat crown
            q.z = lid + (q.z - lid) * 0.62
        t = min(1.0, max(0.0, (q.y - (e.y + 0.1)) / 0.3))
        q.x *= 1.0 - 0.14 * t * t * (3 - 2 * t)      # and the ruff at its cheeks goes
        return q
    r.deform(head, flat)
    r.lengthen_chain(_tail(r), [], 1.6)
    _tail_girth(r, (1.35, 1.0, 1.35))
    r.scale(r.family("Tail5"), r.bone("Tail5"), (0.5, 1.0, 0.5))
    r.rotate(_tail(r), r.bone("Tail1"), X, math.radians(16))


def drake_ages(r, level):
    head, hb = _head(r), r.bone("Head")
    top = r.top(r.bone("Torso2").y)
    if level <= 1:                  # the hatchling: a head and a ridge it has not grown into
        r.scale(head, hb, 1.34)
        r.lengthen_chain(list(NECK), head, 0.6)
        r.leg_length(0.2)
        r.leg_girth(1.2)
        r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, 0.78)
        zc = (r.top(r.bone("Torso2").y) + r.bottom(r.bone("Torso2").y, half_width=0.1)) / 2
        r.scale(bk.TORSO, (0, 0, zc), (1.14, 1.0, 1.1))
        r.lengthen_chain(_tail(r), [], 0.62)
        gl._feet(r, 1.35)
        _young_eyes(r, 0.115)
    elif level == 2:
        r.scale(head, hb, 1.1)
        r.lengthen_chain(list(NECK), head, 0.88)
    elif level >= 4:
        r.scale(["Torso3", "Torso2"], (0, 0, top), (1.12, 1.0, 1.1))
        r.leg_girth(1.1)
        r.lengthen_chain(_tail(r), [], 1.1)


def _horn_mat():
    return kit.mark("ridge", mat("drake_horn"))


def drake_measure(r, A):
    """A drake's face is no dog's: no button of a nose; the pale of its underside kept to the
    lower jaw; its mask a stripe back from the eye along the side of the head; and a brow
    over each eye, heavier as it ages."""
    _measure(r, A)
    me = r.mesh.data
    names = [m.name for m in me.materials]
    slot = lambda nm: names.index(nm) if nm in names else -1  # noqa: E731
    dark, light, nose, mask = slot("fur_dark"), slot("fur_light"), slot("nose"), slot("mark_mask")
    wh = r._weights(_head(r))
    R = r.M.to_3x3()
    e, n = A.eye, A.nose
    lip = n.z - 0.07
    for p in me.polygons:
        if sum(wh[i] for i in p.vertices) / len(p.vertices) < 0.55:
            continue
        c, up = r.M @ p.center, (R @ p.normal).normalized().z
        was = p.material_index
        stripe = mask >= 0 and up <= 0.5 and e.y - 0.12 < c.y < e.y + 0.45 and e.z - 0.13 < c.z < e.z + 0.05
        if was == nose:
            p.material_index = dark
        elif was in (dark, light, mask):
            if stripe and (was != light or c.z > lip):
                p.material_index = mask
            elif was == mask or (was == light and c.z > lip and c.y < e.y + 0.3):
                p.material_index = dark
    level = _S.get("level", 3)
    if level >= 2:
        k = 0.8 if level == 2 else 1.0
        geo = None
        for sg in (1, -1):
            pts = [Vector((sg * (e.x - 0.08), e.y - 0.24, e.z)), Vector((sg * e.x, e.y - 0.04, e.z + 0.075)),
                   Vector((sg * (e.x + 0.05), e.y + 0.18, e.z + 0.1)), Vector((sg * (e.x + 0.06), e.y + 0.36, e.z + 0.07))]
            geo = g.merge(geo, g.tube(pts, [0.02 * k, 0.055 * k, 0.05 * k, 0.015], n=4))
        _add(r, "brows", geo, "Head", mat("fur_dark"), smooth=True)


def _drake_horns(style):
    def fn(r, A, size):
        hb = A.head
        crown = _skin().top(hb.y + 0.06, half_width=0.2, window=0.12)
        geo, dark = None, None

        def curve(sg, pts, rad, off=(0.0, 0.0, 0.0), k=1.0):
            base = Vector((sg * (0.1 + off[0]), hb.y + 0.1 + off[1], crown - 0.05 + off[2]))
            P = [base] + [base + Vector((sg * x, y, z)) * (size * k) for x, y, z in pts]
            return g.tube(P, [rad * 1.25 * (0.7 + 0.3 * size) * (1 - 0.86 * i / (len(P) - 1)) for i in range(len(P))], n=5), P

        swept = [(0.05, 0.24, 0.2), (0.07, 0.56, 0.32)]
        for sg in (1, -1):
            if style == "nubs":
                geo = g.merge(geo, curve(sg, [(0.02, 0.07, 0.07)], 0.05)[0])
            elif style == "swept":
                geo = g.merge(geo, curve(sg, swept, 0.055)[0])
            elif style == "broad":      # heavy, out to the sides and back, like a bull's
                geo = g.merge(geo, curve(sg, [(0.14, 0.12, 0.1), (0.32, 0.34, 0.12), (0.4, 0.6, 0.02)], 0.1)[0])
            elif style == "long":       # one grown long, and nicked down its length
                if sg > 0:
                    geo = g.merge(geo, curve(sg, swept, 0.055)[0])
                else:
                    ge, P = curve(sg, [(0.05, 0.3, 0.25), (0.08, 0.7, 0.5), (0.1, 1.1, 0.62)], 0.075)
                    geo = g.merge(geo, ge)
                    for t in (0.2, 0.35, 0.5, 0.65, 0.8):
                        c = _along(P, t)
                        dark = g.merge(dark, _hoop(c, _along(P, t + 0.02) - c, 0.075 * (1 - 0.8 * t) + 0.012, 0.014, n=6, sides=3))
            elif style == "crown":      # a crown of them
                geo = g.merge(geo, curve(sg, [(0.05, 0.3, 0.3), (0.08, 0.68, 0.58)], 0.065)[0])
                geo = g.merge(geo, curve(sg, [(0.14, 0.2, 0.12), (0.26, 0.48, 0.22)], 0.05, off=(0.06, 0.02, -0.05))[0])
                geo = g.merge(geo, curve(sg, [(0.14, 0.06, -0.02), (0.32, 0.22, -0.04)], 0.045, off=(0.1, -0.02, -0.12))[0])
            elif style == "brow":       # horns over the brow as well, forward
                geo = g.merge(geo, curve(sg, [(0.06, 0.24, 0.24), (0.08, 0.56, 0.4)], 0.07)[0])
                geo = g.merge(geo, curve(sg, [(0.06, -0.2, 0.14), (0.1, -0.48, 0.32)], 0.055, off=(0.02, -0.22, -0.03))[0])
            elif style == "flat":       # laid flat for the fall
                geo = g.merge(geo, curve(sg, [(0.03, 0.34, 0.03), (0.04, 0.7, 0.02)], 0.055)[0])
            elif style == "droop":      # heavy and gone down with age
                geo = g.merge(geo, curve(sg, [(0.1, 0.2, 0.1), (0.2, 0.46, -0.05), (0.24, 0.6, -0.32)], 0.075)[0])
            if style != "nubs":         # two shorter spines behind each cheek
                for k, (dz, ln) in enumerate(((-0.1, 0.24), (-0.2, 0.18))):
                    b0 = Vector((sg * 0.15, hb.y + 0.06, crown + dz))
                    geo = g.merge(geo, g.cone(b0, b0 + Vector((sg * 0.1, ln, 0.02 - 0.03 * k)) * size, 0.035, n=4))
        _add(r, "horns", geo, "Head", _horn_mat(), smooth=True)
        _add(r, "horn_nicks", dark, "Head", mat("coal"))
    return fn


def _drake_frill(style):
    def fn(r, A, size):
        if style == "gate":           # bars round its neck, like the teeth of a gate
            _neck_band(r, "gate_bar", 0.86, mat("metal_iron"), wide=0.05, off=0.03)
            _neck_blades(r, "gate_teeth", 0.86, 13, 0.52 * size, 0.1, mat("metal_iron"), a0=-0.35, a1=1.35, sweep=0.45, out=0.9, belly=0.15)
        elif style == "herald":       # a frill that opens when it speaks
            _neck_blades(r, "frill", 0.9, 11, 0.7 * size, 0.42, mat("fur_light"), a0=-0.3, a1=1.3, sweep=0.15, out=1.0, belly=0.6)
            _neck_blades(r, "frill_ribs", 0.9, 11, 0.74 * size, 0.06, _horn_mat(), a0=-0.3, a1=1.3, sweep=0.15, out=1.0, belly=0.3, grow=0.9)
        elif style == "crown":        # spines standing round the back of its head
            _neck_blades(r, "crownfrill", 0.93, 9, 0.56 * size, 0.1, _horn_mat(), a0=0.0, a1=1.0, sweep=0.3, out=0.95, belly=0.2)
        elif style == "crest":        # a crest that lifts and spreads
            nk = _neck(r)
            skin, ribs, lit = None, None, None
            prev = None
            for i in range(7):
                t = 1.0 - 0.1 * i
                p, d, _ = nk.at(t)
                u, v = _perp(d)
                b0 = nk.nape(t) - v * 0.03
                L = (1.0 + 0.5 * math.sin(math.pi * (i + 0.6) / 7.2)) * size
                tip = b0 + v * L - d * (0.25 * L * (i - 2) / 3)
                ribs = g.merge(ribs, g.tube([b0, tip], [0.035, 0.01], n=4))
                lit = g.merge(lit, g.ico(tip, 0.045, sub=0))
                if prev is not None:
                    skin = g.merge(skin, _panel([prev[0], prev[1].lerp(prev[0], 0.08), tip.lerp(b0, 0.08), b0], 0.012))
                prev = (b0, tip)
            _add(r, "crest_skin", skin, "Neck3", mat("fur_light"), smooth=False)
            _add(r, "crest_ribs", ribs, "Neck3", _horn_mat())
            _add(r, "crest_tips", lit, "Neck3", field("crest", 3.0))
        elif style == "beard":        # long whiskers and a beard, grey
            n = A.nose
            geo = None
            for sg in (1, -1):
                b0 = Vector((sg * 0.16, n.y + 0.22, n.z - 0.02))
                geo = g.merge(geo, g.tube([b0, b0 + Vector((sg * 0.34, 0.1, -0.1)) * size, b0 + Vector((sg * 0.5, 0.5, -0.5)) * size, b0 + Vector((sg * 0.4, 0.9, -1.0)) * size], [0.035, 0.03, 0.02, 0.006], n=4))
            zb, _ = gl._jaw_line(r, A)
            for k in range(5):
                b0 = Vector((0.07 * (k - 2), n.y + 0.34 + 0.05 * abs(k - 2), zb + 0.03))
                geo = g.merge(geo, g.blade(b0, b0 + Vector((0.03 * (k - 2), 0.14, -(0.5 - 0.08 * abs(k - 2)) * size)), 0.11, normal=Y, belly=0.35))
            _add(r, "beard", geo, "Head", mat("fur_pale"))
    return fn


def _drake_ridge(style):
    def fn(r, A, size):
        m = _horn_mat()
        y0, y1 = r.bone("Neck3").y, r.bone("Tail1").y
        tb = _tailbones(r)
        if style in ("plates", "young"):
            k = 1.9 if style == "young" else 1.0
            r.fin("ridge", y0, y1, lambda t: (0.1 + 0.08 * math.sin(t * math.pi)) * size * k, m, thickness=0.07, steps=24 if style == "plates" else 12, sink=0.05, serrate=True)
            r.fin("tail_ridge", y1 + 0.05, tb[4].y, lambda t: 0.1 * (1.0 - t) * size, m, thickness=0.05, steps=12, sink=0.04, serrate=True)
        elif style == "flame":        # a ridge like a row of flames
            geo, lit, ws, wl = None, None, [], []
            for i in range(15):
                t = i / 14
                y = y0 + (y1 - y0) * t
                L = (0.3 + 0.22 * math.sin(t * math.pi)) * size * (1.0 + 0.2 * math.sin(i * 2.2))
                b0 = Vector((0, y, _skin().top(y, half_width=0.12) - 0.05))
                bl = g.blade(b0, b0 + Vector((0, L * 0.55, L)), 0.26, normal=X, belly=0.3, curl=0.0)
                geo = g.merge(geo, bl)
                ws.extend([r.spine_weights(y)] * len(bl[0]))
                if i % 2 == 0:
                    b2 = g.blade(b0 + Vector((0, 0.04, 0.02)), b0 + Vector((0, L * 0.3, L * 0.6)), 0.13, thick=0.1, normal=X, belly=0.3)
                    lit = g.merge(lit, b2)
                    wl.extend([r.spine_weights(y)] * len(b2[0]))
            _add(r, "ridge_flame", geo, ws, m, smooth=False)
            _add(r, "ridge_lit", lit, wl, field("ember", 2.4))
        elif style == "sail":         # a ridge gone finned and ragged
            r.fin("sail", y0 + 0.1, y1, lambda t: (0.3 + 0.62 * math.sin(t * math.pi)) * size * (0.82 + 0.18 * math.sin(t * 41.0)), mat("fur_light"), thickness=0.035, steps=26, sink=0.05)
            r.fin("tail_fin", y1 + 0.05, tb[5].y, lambda t: 0.32 * (1.0 - t) * size, mat("fur_light"), thickness=0.03, steps=12, sink=0.04)
        elif style == "beads":        # a row of beads on a wire, to count on
            geo, beads, bright, ws, wb, wc = None, None, None, [], [], []
            pts = []
            for i in range(13):
                t = i / 12
                y = y0 + 0.3 + (y1 - y0 - 0.3) * t
                pts.append(Vector((0, y, _skin().top(y, half_width=0.12) + 0.2 * size)))
            wire = g.tube(pts, [0.014] * len(pts), n=3, caps=False)
            _add(r, "bead_wire", wire, [r.spine_weights(p.y) for p in wire[0]], mat("metal_iron"))
            for i, p in enumerate(pts):
                if i % 2 == 0:
                    post = g.tube([p, Vector((0, p.y, p.z - 0.24 * size))], [0.02, 0.03], n=4)
                    geo = g.merge(geo, post)
                    ws.extend([r.spine_weights(p.y)] * len(post[0]))
                if i % 4 != 3:
                    b = g.ico(p, 0.085 * size, sub=1, scale=(1.0, 0.7, 1.0))
                    if i % 4 == 1:
                        bright = g.merge(bright, b)
                        wc.extend([r.spine_weights(p.y)] * len(b[0]))
                    else:
                        beads = g.merge(beads, b)
                        wb.extend([r.spine_weights(p.y)] * len(b[0]))
            _add(r, "bead_posts", geo, ws, m)
            _add(r, "beads", beads, wb, mat("wood"), smooth=True)
            _add(r, "beads_b", bright, wc, mat("metal_brass"), smooth=True)
        elif style == "pots":         # a row of chimney pots, smoking
            for i, t in enumerate((0.3, 0.52, 0.74)):
                y = y0 + (y1 - y0) * t
                c = Vector((0, y, _skin().top(y, half_width=0.12) - 0.06))
                h = (0.42 - 0.06 * i) * size
                pot = g.lathe([(0.15, 0.0), (0.12, h * 0.8), (0.15, h * 0.84), (0.15, h), (0.09, h)], n=8, centre=c)
                _add(r, "pot_%d" % i, pot, [r.spine_weights(y)] * len(pot[0]), mat("clay_dark"))
                p0 = c + Vector((0, 0, h))
                sm = g.tongue([p0, p0 + Vector((0.05, 0.14, 0.3)), p0 + Vector((-0.08, 0.4, 0.62)), p0 + Vector((0.04, 0.7, 0.9))], [0.18, 0.24, 0.2, 0.03], thick=0.6, normal=X)
                _add(r, "pot_smoke_%d" % i, sm, [r.spine_weights(y)] * len(sm[0]), mat("smoke"))
        elif style == "crumbled":     # a ridge burned down to stubs
            geo, ws = None, []
            for i in range(11):
                t = i / 10
                y = y0 + (y1 - y0) * t
                L = (0.08 + 0.1 * math.sin(i * 2.7) ** 2) * size
                b0 = Vector((0, y, _skin().top(y, half_width=0.12) - 0.04))
                bl = g.blade(b0, b0 + Vector((0, 0.04, L)), 0.16, normal=X, belly=0.5)
                geo = g.merge(geo, bl)
                ws.extend([r.spine_weights(y)] * len(bl[0]))
            _add(r, "ridge_ash", geo, ws, mat("ash"), smooth=False)
        elif style == "lamps":        # every lamp it has kept, hung along its back
            r.fin("ridge", y0, y1, lambda t: (0.1 + 0.08 * math.sin(t * math.pi)) * size, m, thickness=0.07, steps=24, sink=0.05, serrate=True)
            for i, t in enumerate((0.32, 0.58, 0.82)):
                y = y0 + (y1 - y0) * t
                b0 = Vector((0, y, _skin().top(y, half_width=0.12) - 0.04))
                topp = b0 + Vector((0, 0.1, (0.62 - 0.06 * i) * size))
                arm = topp + Vector((0.26 * (1 if i % 2 else -1), 0.0, 0.06))
                bone = max(r.spine_weights(y), key=lambda bw: bw[1])[0]
                _add(r, "lamppost_%d" % i, g.tube([b0, topp, arm], [0.04, 0.035, 0.025], n=5), bone, m)
                gl._add_items(r, "ridgelamp_%d" % i, gl._lantern(arm, 0.17 * size, "lamp", 3.4), bone)
        elif style == "coins":        # scales like old coin, standing on edge down its back and lying on its flanks
            sk = _skin()
            brass = mat("brass_old")
            geo, ws = None, []
            for i in range(10):
                t = i / 9
                y = y0 + (y1 - y0) * t
                rad = (0.15 + 0.08 * math.sin(t * math.pi)) * size
                c = Vector((0, y, sk.top(y, half_width=0.12) + rad * 0.5))
                coin = g.tube([c - X * 0.025, c + X * 0.025], [rad, rad], n=8)
                geo = g.merge(geo, coin)
                ws.extend([r.spine_weights(y)] * len(coin[0]))
            zmid = (A.withers + A.belly) / 2
            for row, dz in enumerate((0.22, -0.12)):
                for i in range(5):
                    y = A.t3.y + 0.42 * i + 0.2 * (row % 2)
                    for sg in (1, -1):
                        z = zmid + dz
                        c = Vector((sg * (sk.side(y, z) + 0.01), y, z))
                        coin = g.tube([c, c + Vector((sg * 0.04, 0, 0.0))], [0.2 * size, 0.2 * size], n=8)
                        geo = g.merge(geo, coin)
                        ws.extend([r.spine_weights(y)] * len(coin[0]))
            _add(r, "coins", geo, ws, brass, smooth=False)
    return fn


# The shapes its wings may take: arm (shoulder to elbow to wrist) and fingers from the wrist,
# each point (out, back, up) from the one before it for the arm and from the wrist for the
# fingers; inner is where the skin meets the body, from the shoulder.
WINGS = {
    "nubs": dict(arm=[(0.1, 0.12, 0.18), (0.14, 0.34, 0.24)], fingers=[(0.06, 0.26, 0.1), (0.05, 0.36, -0.06), (0.02, 0.26, -0.2)], inner=(0.02, 0.4, -0.05)),
    "folded": dict(arm=[(0.12, -0.2, 0.42)], fingers=[(0.09, 1.5, -0.08), (0.06, 1.38, -0.32), (0.03, 1.12, -0.56), (0.0, 0.8, -0.72)], inner=(0.0, 0.5, -0.3)),
    "half": dict(arm=[(0.35, 0.1, 0.75), (0.55, 0.5, 1.25)], fingers=[(0.55, 0.3, 0.95), (0.5, 1.05, 0.5), (0.32, 1.45, -0.1), (0.1, 1.45, -0.62)], inner=(0.05, 1.1, -0.2)),
    "glide": dict(arm=[(0.95, -0.1, 0.5), (2.0, 0.1, 0.72)], fingers=[(1.7, 0.1, 0.26), (1.35, 0.85, 0.05), (0.72, 1.25, -0.05), (0.2, 1.35, -0.1)], inner=(0.1, 1.2, -0.05)),
    "mantle": dict(arm=[(0.5, 0.0, 1.05), (0.95, 0.2, 2.0)], fingers=[(0.65, 0.0, 1.15), (0.95, 0.72, 0.82), (0.82, 1.25, 0.2), (0.4, 1.45, -0.5)], inner=(0.1, 1.2, -0.3)),
    "stoop": dict(arm=[(0.4, 0.3, 0.5), (0.6, 1.05, 0.82)], fingers=[(0.3, 1.5, 0.5), (0.15, 1.7, 0.1), (0.0, 1.35, -0.3)], inner=(0.05, 1.0, -0.1)),
    "shadow": dict(arm=[(1.0, -0.4, 0.9), (2.1, -0.6, 1.55)], fingers=[(1.6, -0.6, 0.62), (1.7, 0.3, 0.1), (1.15, 1.25, -0.3), (0.5, 1.75, -0.6), (0.1, 1.85, -0.7)], inner=(0.1, 1.5, -0.4)),
    "banner": dict(arm=[(0.6, 0.1, 0.9), (1.1, 0.4, 1.65)], fingers=[(0.5, 0.4, 1.05), (0.6, 1.5, 0.95), (0.5, 2.6, 0.3), (0.2, 1.6, -0.3)], inner=(0.05, 1.2, -0.2)),
    "cloak": dict(arm=[(0.3, 0.05, 0.5), (0.46, 0.35, 0.56)], fingers=[(0.26, 0.3, -0.52), (0.2, 0.85, -0.95), (0.1, 1.45, -1.05), (0.0, 1.95, -0.85)], inner=(0.0, 1.6, -0.2)),
}


def _wing(sg, root, P, size):
    """One wing from its shoulder: (its bones, its skin, its leading edge)."""
    arm = [V(root)]
    for x, y, z in P["arm"]:
        arm.append(arm[0] + Vector((sg * x, y, z)) * size)
    wrist = arm[-1]
    tips = [wrist + Vector((sg * x, y, z)) * size for x, y, z in P["fingers"]]
    bones = g.tube(arm, [0.075, 0.058, 0.042][:len(arm)], n=5)
    for t in tips:
        bones = g.merge(bones, g.tube([wrist, t], [0.034, 0.008], n=4))
    bones = g.merge(bones, g.cone(wrist, wrist + Vector((sg * 0.03, -0.12, 0.12)) * size, 0.03, n=4))
    edge = tips + [arm[0] + Vector((sg * P["inner"][0], P["inner"][1], P["inner"][2])) * size]
    skin = None
    for a, b in zip(edge, edge[1:]):
        skin = g.merge(skin, _panel([wrist, a, wrist.lerp((a + b) / 2, 0.84), b], 0.012))
    if len(arm) > 2:
        skin = g.merge(skin, _panel([arm[0], arm[1], wrist, edge[-1]], 0.012))
    return bones, skin, arm


def _drake_wings(style):
    def fn(r, A, size):
        sh = A.sh
        y0 = sh.y + 0.02
        z0 = _skin().top(y0) - 0.1
        bones, skin, pale = None, None, None
        for sg in (1, -1):
            root = Vector((sg * (_skin().side(y0, z0) + 0.01), y0, z0))
            b, s, arm = _wing(sg, root, WINGS[style], size)
            bones, skin = g.merge(bones, b), g.merge(skin, s)
            if style == "glide":      # wind-burn along the leading edge
                pale = g.merge(pale, g.tube([p + Vector((0, -0.03, 0.03)) for p in arm], [0.05] * len(arm), n=4))
        membrane = mat("shade") if style == "shadow" else mat("fur_light")
        _add(r, "wing_bones", bones, "Torso3", kit.mark("wings", mat("wing")), smooth=True)
        _add(r, "wing_skin", skin, "Torso3", membrane, smooth=False)
        _add(r, "wing_burn", pale, "Torso3", mat("fur_pale"))
        if style == "shadow":         # a thread of light along the edge, so the shadow has a shape
            lit = None
            for sg in (1, -1):
                root = Vector((sg * (_skin().side(y0, z0) + 0.01), y0, z0))
                _, _, arm = _wing(sg, root, WINGS[style], size)
                lit = g.merge(lit, g.tube([p + Vector((0, -0.04, 0.02)) for p in arm], [0.022] * len(arm), n=3, caps=False))
            _add(r, "wing_edge", lit, "Torso3", field("edge", 2.0))
    return fn


def _drake_belly(style):
    def fn(r, A, size):
        fy, by = r.bone("FrontUpperLeg.L").y, r.bone("BackUpperLeg.L").y
        if style == "plates":
            r.fin("belly", fy + (by - fy) * 0.24, fy + (by - fy) * 0.74, 0.03, mat("fur_light"), thickness=0.34, steps=10, sink=0.06, under=True)
        else:                         # belly plates scuffed flat and bright, like the brass of a door
            sk = _skin()
            brass = mat("metal_brass")
            geo, ws = None, []
            for i in range(5):
                y = fy + 0.05 + (by - fy - 0.1) * i / 4
                zb = sk.bottom(y, half_width=0.1)
                w = sk.side(y, zb + 0.25)
                pl = g.box((0, y, zb + 0.01), (w * 1.5 * size, 0.42, 0.07), rot=(0.1, 0, 0))
                geo = g.merge(geo, pl)
                ws.extend([r.spine_weights(y)] * 8)
                for sg in (1, -1):
                    sp = g.box((sg * (w * 0.9 + 0.02), y, zb + 0.2), (0.06, 0.42, 0.4 * size), rot=(0.0, sg * 0.5, 0))
                    geo = g.merge(geo, sp)
                    ws.extend([r.spine_weights(y)] * 8)
            _add(r, "bellyplates", geo, ws, brass)
            # and up the front of the chest and throat
            nk = _neck(r)
            for k, t in enumerate((0.0, 0.25, 0.5)):
                c = nk.throat(t, 0.03)
                p, d, bone = nk.at(t)
                u, v = _perp(d)
                rot = Matrix((u, d, v)).transposed()
                _add(r, "throatplate_%d" % k, g.box(c, (0.36 * size * (1 - 0.15 * k), 0.36, 0.06), rot=rot), bone, brass)
    return fn


def _drake_throat(style):
    def fn(r, A, size):
        nk = _neck(r)
        if style in ("ember", "banked"):
            c = nk.throat(0.82, 0.0)
            _add(r, "throat", g.ico(c, (0.07 if style == "ember" else 0.12) * size, sub=1, scale=(0.9, 1.0, 1.0)), "Neck3", field("ember", 2.4 if style == "ember" else 3.0))
            if style == "banked":     # the fire kept in: it shows down the front of the neck
                geo = None
                for t in (0.2, 0.36, 0.52, 0.68):
                    a, b = nk.throat(t, 0.012), nk.throat(t + 0.1, 0.012)
                    geo = g.merge(geo, g.blade(a, b, 0.2 * size, thick=0.03, normal=(a - nk.at(t)[0]).normalized(), belly=0.5))
                _add(r, "throat_seams", geo, "Neck2", field("ember", 2.2))
        elif style == "blue":         # a dull shine under its throat, the colour of a post-flame
            c = nk.throat(0.1, 0.02)
            _add(r, "chest_glow", g.ico(c + Vector((0, 0, -0.1)), 0.24 * size, sub=1, scale=(1.0, 0.5, 1.3)), "Torso3", field("lamp", 3.0))
            geo = None
            for t in (0.25, 0.45, 0.65, 0.85):
                geo = g.merge(geo, g.ico(nk.throat(t, 0.0), 0.1 * size, sub=1, scale=(1.0, 0.6, 1.0)))
            _add(r, "throat_glow", geo, "Neck2", field("lamp", 2.6))
        elif style == "bulges":       # what it will spit, coming up its throat
            for k, t in enumerate((0.25, 0.5, 0.75)):
                p, d, bone = nk.at(t)
                _add(r, "bulge_%d" % k, g.loft([nk.ring(t, 0.02, along=-0.1), nk.ring(t, 0.09, along=0.0), nk.ring(t, 0.02, along=0.1)], caps=False), bone, mat("fur_light"), smooth=True)
                _add(r, "bulge_lit_%d" % k, g.ico(nk.throat(t, 0.08), 0.07 * size, sub=1), bone, field("ember", 2.6))
    return fn


def _drake_tailend(style):
    def fn(r, A, size):
        tip, d = _tail_tip(r)
        horn = kit.mark("tailtip", mat("drake_horn"))
        up = Z - d * Z.dot(d)
        up = up.normalized() if up.length > 0.1 else X.copy()
        if style == "spade":
            _add(r, "spade", g.blade(tip - d * 0.05, tip + d * 0.3 * size, 0.24 * size, normal=up, belly=0.45, thick=0.03), "Tail8", horn)
        elif style == "hammer":       # a head to it, like a smith's
            c = tip + d * 0.14
            _add(r, "tail_hammer", g.box(c, (0.5 * size, 0.24 * size, 0.24 * size)), "Tail8", mat("metal_iron"))
            _add(r, "tail_hammer_band", g.box(c, (0.14, 0.27 * size, 0.27 * size)), "Tail8", mat("metal_brass"))
        elif style == "rudder":       # a broad fin to steer by
            _add(r, "rudder", g.blade(tip - d * 0.5, tip + d * 0.5 * size, 0.62 * size, normal=X, belly=0.55, thick=0.03), "Tail8", kit.mark("wings", mat("wing")))
            _add(r, "rudder_rib", g.tube([tip - d * 0.5, tip + d * 0.5 * size], [0.03, 0.008], n=4), "Tail8", horn)
        elif style == "banner":       # a long pennant
            p1, p2, p3 = tip + d * 0.5 * size + up * 0.1, tip + d * 1.1 * size - up * 0.05, tip + d * 1.7 * size + up * 0.12
            _add(r, "pennant", g.tongue([tip, p1, p2, p3], [0.3 * size, 0.36 * size, 0.28 * size, 0.04], thick=0.08, normal=X), "Tail8", kit.mark("wings", mat("wing")))
        elif style == "lamp":         # a lamp held in the loop of its tail
            gl._add_items(r, "taillamp", gl._lantern(tip + Vector((0, 0, 0.5 * size)), 0.2 * size, "lamp", 3.6), "Tail8")
            _add(r, "taillamp_hook", g.tube([tip, tip + Vector((0, 0, 0.5 * size))], [0.03, 0.02], n=4), "Tail8", horn)
    return fn


def drake_shell(r, A, size):
    """A back like a strong-room, with its wheel."""
    y = (A.t3.y + A.back.y) / 2 + 0.1
    top = _skin().top(y)
    c = Vector((0, y, top - 0.42))
    iron, brass = mat("metal_iron"), mat("metal_brass")
    r.shell("vault", c, (0.7 * size, 1.15 * size, 0.74 * size), "Torso2", mat("slate_light"), segments=10, rings=4)
    for k, dy in enumerate((-0.6, 0.0, 0.6)):
        band = g.loft([g.ring(c + Vector((0, dy * size - 0.04, 0)), 0.68 * size, 0.68 * size * math.sqrt(max(0.05, 1 - (dy / 1.15) ** 2)), n=12, u=X, v=Z),
                       g.ring(c + Vector((0, dy * size + 0.04, 0)), 0.68 * size, 0.68 * size * math.sqrt(max(0.05, 1 - (dy / 1.15) ** 2)), n=12, u=X, v=Z)], caps=False)
        _add(r, "vault_band_%d" % k, band, "Torso2", brass)
    for sg in (1, -1):
        hub = c + Vector((sg * 0.6 * size, 0.0, 0.26 * size))
        nrm = Vector((sg * 0.9, 0, 0.42)).normalized()
        wheel = _hoop(hub + nrm * 0.07, nrm, 0.26 * size, 0.03, n=14)
        u, v = _perp(nrm)
        for a in range(4):
            dirv = u * math.cos(a * math.pi / 4) + v * math.sin(a * math.pi / 4)
            wheel = g.merge(wheel, g.tube([hub + nrm * 0.07 - dirv * 0.26 * size, hub + nrm * 0.07 + dirv * 0.26 * size], [0.02, 0.02], n=4))
        _add(r, "vault_wheel_%d" % sg, wheel, "Torso2", brass)
        _add(r, "vault_hub_%d" % sg, g.ico(hub + nrm * 0.08, 0.07 * size, sub=1), "Torso2", field("seal", 2.0))


def drake_rubble(r, A, size):
    """What has settled on something that sleeps in old places."""
    spots = ((0.1, A.t3.y + 0.1, 0.3), (-0.14, A.t3.y + 0.6, 0.36), (0.05, A.t2.y + 0.5, 0.28), (-0.06, A.back.y, 0.24))
    for i, (x, y, s) in enumerate(spots):
        c = Vector((x, y, _skin().top(y, half_width=0.2) + 0.05))
        _add(r, "rubble_%d" % i, g.box(c, (s * 1.3 * size, s * size, s * 0.6 * size), rot=(0.2 * i, 0.3 - 0.2 * i, 0.5 * i)), [r.spine_weights(y)] * 8, mat("slate" if i % 2 else "slate_light"))
    geo, ws = None, []
    for i in range(10):
        y = A.t3.y - 0.1 + 0.26 * i
        sg = 1 if i % 2 else -1
        z = _skin().top(y, half_width=0.3) - 0.15
        b0 = Vector((sg * _skin().side(y, z) * 0.9, y, z))
        bl = g.blade(b0, b0 + Vector((sg * 0.12, 0.1, -0.36 * size)), 0.2, normal=Vector((sg, 0, 0.3)), belly=0.45)
        geo = g.merge(geo, bl)
        ws.extend([r.spine_weights(y)] * len(bl[0]))
    _add(r, "rubble_ivy", geo, ws, mat("leaf"))


def _drake_jaw(style):
    def fn(r, A, size):
        n = A.nose
        zb, zt = gl._jaw_line(r, A)
        if style == "drips":          # something bright drips from the corner of its jaw
            geo = None
            for sg, L in ((1, 0.5), (-1, 0.72), (-1, 0.36)):
                b0 = Vector((sg * 0.14, n.y + 0.34 + 0.1 * L, zb + 0.06))
                geo = g.merge(geo, g.tube([b0, b0 + Vector((0, 0.0, -L * 0.6 * size)), b0 + Vector((0, 0, -L * size))], [0.05, 0.03, 0.045], n=5))
            _add(r, "drips", geo, "Head", field("ember", 3.4))
            slag = None
            for k in range(4):
                c = Vector((0.1 * (k - 1.5), n.y + 0.3 + 0.08 * k, zb - 0.02))
                slag = g.merge(slag, g.ico(c, 0.1 * size, sub=0, scale=(1.2, 1.0, 0.7)))
            _add(r, "slag", slag, "Head", mat("slag"))
        elif style == "tongue":       # a tongue stained black to the root
            t0 = Vector((0, n.y + 0.36, zb + 0.1))
            pts = [t0, t0 + Vector((0, -0.34, -0.06)), t0 + Vector((0.03, -0.6, -0.36 * size)), t0 + Vector((0.0, -0.62, -0.8 * size))]
            _add(r, "ink_tongue", g.tongue(pts, [0.2, 0.18, 0.14, 0.05], thick=0.3, normal=Z), "Head", mat("tongue_ink"), smooth=True)
            fork = None
            for sg in (1, -1):
                fork = g.merge(fork, g.cone(pts[-1], pts[-1] + Vector((sg * 0.1, -0.03, -0.2 * size)), 0.03, n=4))
            _add(r, "ink_fork", fork, "Head", mat("tongue_ink"))
        elif style == "glaze":        # the scales round its mouth cracked and glazed like a kiln's lip
            geo = None
            for sg in (1, -1):
                for k in range(4):
                    y = n.y + 0.08 + 0.16 * k
                    c = Vector((sg * (0.12 + 0.03 * k), y, (zb + zt) / 2 + 0.02))
                    geo = g.merge(geo, g.ico(c, 0.1 * size, sub=0, scale=(0.5, 1.0, 1.0)))
            geo = g.merge(geo, g.ico(Vector((0, n.y + 0.06, zt - 0.02)), 0.13 * size, sub=0, scale=(1.2, 1.0, 0.5)))
            _add(r, "glaze", geo, "Head", mat("glaze"))
    return fn


def _drake_breath(style):
    def fn(r, A, size):
        n = A.nose
        zb, zt = gl._jaw_line(r, A)
        m0 = Vector((0, n.y + 0.1, (zb + zt) / 2 - 0.02))
        if style == "jet":            # narrow and blue, the way a smith wants it
            _add(r, "jet", g.tongue([m0, m0 + Vector((0, -0.5, -0.02)) * size, m0 + Vector((0, -1.3, -0.05)) * size, m0 + Vector((0, -1.9, -0.06)) * size], [0.1, 0.16, 0.1, 0.01], thick=0.8, normal=Z), "Head", field("jet", 3.8))
        elif style == "beacon":       # a steady flame at the back of its open mouth, in a cage
            c = m0 + Vector((0, -0.16, 0.0))
            _add(r, "beacon", g.ico(c, 0.2 * size, sub=1, scale=(1.0, 1.0, 1.2)), "Head", field("flame", 4.0))
            cage = g.merge(_hoop(c, X, 0.3 * size, 0.022, n=12), _hoop(c, Y, 0.3 * size, 0.022, n=12), _hoop(c, Z, 0.3 * size, 0.022, n=12))
            _add(r, "beacon_cage", cage, "Head", mat("metal_iron"))
        elif style == "cinders":      # it breathes upward and lets the weather do the rest
            geo, grey = None, None
            for i in range(14):
                c = Vector((0.5 * math.sin(i * 2.3), A.t3.y - 0.4 + 0.3 * i + 0.2 * math.sin(i * 1.3), A.skull + 0.25 + 0.5 * math.sin(i * 1.7) ** 2))
                if i % 3:
                    geo = g.merge(geo, g.ico(c, 0.05 * size, sub=0))
                else:
                    grey = g.merge(grey, g.blade(c, c + Vector((0.05, 0.08, -0.16)), 0.1, normal=X, belly=0.5))
            _add(r, "cinders", geo, "Torso3", field("ember", 3.0))
            _add(r, "ashfall", grey, "Torso3", mat("ash"))
    return fn


def _drake_nostrils(style):
    def fn(r, A, size):
        n = A.nose
        for sg in (1, -1):
            p0 = Vector((sg * 0.09, n.y + 0.06, n.z + 0.04))
            if style == "smoke":      # a thread of dark smoke from each nostril, constant
                pts = [p0, p0 + Vector((sg * 0.05, -0.05, 0.36)) * size, p0 + Vector((sg * -0.04, 0.2, 0.86)) * size, p0 + Vector((sg * 0.08, 0.6, 1.4)) * size, p0 + Vector((sg * 0.0, 1.1, 1.9)) * size]
                _add(r, "nose_smoke_%d" % sg, g.tongue(pts, [0.06, 0.12, 0.17, 0.2, 0.03], thick=0.6, normal=X), "Head", mat("smoke"), smooth=True)
            elif style == "heat":     # a shimmer of heat over its nostrils
                _add(r, "nose_heat_%d" % sg, g.tongue([p0, p0 + Vector((0, -0.03, 0.14 * size)), p0 + Vector((0, 0.0, 0.3 * size))], [0.08, 0.07, 0.01], thick=0.8, normal=Y), "Head", field("ember", 2.6))
    return fn


def drake_talons(r, A, size):
    """Talons out of proportion to the rest of it, and kept very clean."""
    for tag, foot, bone in gl.FEET:
        f = r.bone(foot)
        cl = None
        for dx in (-0.12, 0.0, 0.12):
            b0 = Vector((f.x + dx, f.y - 0.02, 0.16))
            cl = g.merge(cl, g.tube([b0, b0 + Vector((dx * 0.3, -0.24 * size, 0.02)), b0 + Vector((dx * 0.4, -0.42 * size, -0.16))], [0.06, 0.05, 0.008], n=5))
        cl = g.merge(cl, g.tube([Vector((f.x, f.y + 0.2, 0.16)), Vector((f.x, f.y + 0.34 * size, 0.1)), Vector((f.x, f.y + 0.42 * size, -0.02))], [0.05, 0.04, 0.008], n=5))
        _add(r, "talons_" + tag, cl, bone, mat("bone"))


def drake_shutter(r, A, size):
    """One eye never fully closes: the lid on that side has gone thick as a shutter."""
    e = A.eye
    c = Vector((-(e.x + 0.03), e.y - 0.01, e.z + 0.05))
    _add(r, "shutter", g.box(c, (0.07, 0.34 * size, 0.2 * size), rot=(0.0, 0.25, 0.0)), "Head", mat("slate"))
    _add(r, "shutter_slats", g.merge(g.box(c + Vector((-0.03, 0, 0.04)), (0.03, 0.36 * size, 0.03)), g.box(c + Vector((-0.03, 0, -0.03)), (0.03, 0.36 * size, 0.03))), "Head", mat("metal_iron"))


def drake_eggshell(r, A, size):
    """Still wearing a piece of the shell nobody found."""
    c = Vector((0, A.head.y + 0.05, A.skull + 0.02))
    cap = g.lathe([(0.02, 0.2), (0.16, 0.16), (0.26, 0.05), (0.27, -0.03), (0.2, -0.01), (0.14, 0.1)], n=7, centre=c)
    _add(r, "eggshell", cap, "Head", mat("eggshell"))


def _drake_styles():
    G = gl.GROWS
    for st in ("nubs", "swept", "broad", "long", "crown", "brow", "flat", "droop"):
        G[("horns", st)] = _drake_horns(st)
    for st in ("gate", "herald", "crown", "crest", "beard"):
        G[("frill", st)] = _drake_frill(st)
    for st in ("plates", "young", "flame", "sail", "beads", "pots", "crumbled", "lamps", "coins"):
        G[("ridge", st)] = _drake_ridge(st)
    for st in WINGS:
        G[("wings", st)] = _drake_wings(st)
    for st in ("plates", "brass"):
        G[("belly", st)] = _drake_belly(st)
    for st in ("ember", "banked", "blue", "bulges"):
        G[("throat", st)] = _drake_throat(st)
    for st in ("spade", "hammer", "rudder", "banner", "lamp"):
        G[("tailend", st)] = _drake_tailend(st)
    G[("shell", "vault")] = drake_shell
    G[("back", "rubble")] = drake_rubble
    for st in ("drips", "tongue", "glaze"):
        G[("jaw", st)] = _drake_jaw(st)
    for st in ("jet", "beacon", "cinders"):
        G[("breath", st)] = _drake_breath(st)
    for st in ("smoke", "heat"):
        G[("nostrils", st)] = _drake_nostrils(st)
    G[("claws", "talons")] = drake_talons
    G[("eye", "shutter")] = drake_shutter
    G[("head", "eggshell")] = drake_eggshell


# ======================================================================================
# The families' doors
# ======================================================================================

def register(builders):
    global gl
    for name in ("genius_lines", "__main__"):
        m = sys.modules.get(name)
        if m is not None and getattr(m, "BUILDERS", None) is builders:
            gl = m
    _shapes()
    G = gl.GROWS
    for st, fn in (("mane", neck_mane), ("bell", neck_bell), ("lamp", neck_lamp), ("ivy", neck_ivy), ("garland", neck_garland), ("teeth", neck_teeth),
                   ("chains", neck_chains), ("ash", neck_ash), ("bands", neck_bands)):
        G[("neck", st)] = fn
    _fox_styles()
    _stag_styles()
    _drake_styles()
    builders["fox"] = _builder(fox_species, fox_ages, ("fur_dark", "fur_light"), ("socks", "mask", "saddle", "tailtip"), {"fur_ruff": "fur_dark"})
    # a stag's head stands a fifth under the height it is stood to: its crown is above that
    builders["stag"] = _builder(stag_species, stag_ages, ("hide_red", "fur_cream"), ("socks", "mask", "saddle", "tailtip"),
                                {"fur_dark": "hide_red", "fur_light": "fur_cream", "fur_ruff": "hide_red"}, ref_k=1.2)
    builders["drake"] = _builder(drake_species, drake_ages, ("fur_dark", "fur_light"), ("socks", "mask", "saddle"), {"fur_ruff": "fur_dark"}, measure=drake_measure)


# ======================================================================================
# The gifts: what a hybrid wears of these three (docs/genius-evolutions.md, "Hybrids")
# ======================================================================================
#
# A hybrid's form wears the body of the form it came from and its second base's gift as
# parts. "A tail" and "horns" are any genius's features, so a base's own make of its gift is
# a part of its own, gifts/<feature>-<base>.glb, which the game hangs for that base's gift
# and for nothing else. Made the genius kit's way: at the socket's origin, in the kit's size
# (a body 0.72 tall), for the left where it is one of a pair.
#
#     python tools/blender/lines_wolfkin.py gifts

PALETTE.update({"fox_red": ((0.4, 0.17, 0.08), 0.9, 0.0), "drake_hide": ((0.19, 0.26, 0.22), 0.5, 0.0)})


def _small(geo, k):
    return g.moved(geo, Matrix.Scale(k, 4))


def gift_tail_fox():
    """A fox's brush, carried high, a light riding at its tip."""
    pts = [Vector((0, 0.0, 0.0)), Vector((0, 0.09, 0.04)), Vector((0, 0.2, 0.12)), Vector((0, 0.3, 0.24)), Vector((0, 0.36, 0.38)), Vector((0, 0.37, 0.52)), Vector((0, 0.35, 0.6))]
    radii = [0.03, 0.07, 0.1, 0.105, 0.085, 0.05, 0.008]
    return [kit._part("tail", [(g.tube(pts[:5], radii[:5], n=7), mat("fox_red")), (g.tube(pts[4:], radii[4:], n=7), mat("fur_cream")),
                               (g.ico(pts[-1] + Vector((0, -0.01, 0.06)), 0.04, sub=1), field("foxfire", 3.4))])]


def gift_glow_fox():
    """Foxfire: a small flame that keeps a little way off."""
    c = Vector((0, -0.02, -0.07))
    flame = None
    for dx, h in ((0.0, 0.16), (0.03, 0.1), (-0.028, 0.11)):
        f0 = c + Vector((dx, 0, 0.0))
        flame = g.merge(flame, g.tongue([f0, f0 + Vector((dx * 0.4, 0, h * 0.5)), f0 + Vector((-dx * 0.3, 0, h))], [0.06, 0.055, 0.008], thick=0.7, normal=Y))
    tail = g.tongue([c + Vector((0, 0, -0.03)), c + Vector((0.015, 0.03, -0.09)), c + Vector((-0.01, 0.07, -0.14))], [0.045, 0.03, 0.004], thick=0.6, normal=Y)
    return [kit._part("glow", [(g.ico(c, 0.05, sub=1, scale=(1, 1, 1.15)), field("foxfire", 3.6)), (flame, field("foxfire", 3.0)), (tail, field("foxfire", 2.0))])]


def gift_horn_brow_stag():
    """A stag's crown: six points a side, the field at every one."""
    beams, points = None, None
    for sg in (1, -1):
        geo, tips, _, _ = _antler(sg, Vector((sg * 0.13, 0.0, -0.1)), ANTLERS["royal"], 0.8)
        beams = g.merge(beams, _small(geo, 0.3))
        for p in tips:
            points = g.merge(points, g.ico(p * 0.3, 0.014, sub=0))
    return [kit._part("horn_brow", [(beams, mat("bone")), (points, field("points", 3.0))])]


def gift_long_legs_stag():
    """A stag's foot: a cloven hoof, feathered at the fetlock."""
    hoof = None
    for sx in (0.012, -0.012):
        hoof = g.merge(hoof, g.lathe([(0.02, 0.012), (0.026, -0.012), (0.03, -0.036)], n=5, centre=(sx, -0.01, 0.0)))
    feather = None
    for k in range(6):
        a = k * math.pi / 3
        b0 = Vector((0.022 * math.cos(a), 0.022 * math.sin(a), 0.03))
        feather = g.merge(feather, g.blade(b0, b0 + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), -0.055)), 0.04, normal=Vector((math.cos(a), math.sin(a), 0.3)), belly=0.4))
    return [kit._part("long_legs", [(hoof, mat("horn")), (feather, mat("fur_cream"))])]


def gift_horns_drake():
    """A drake's horns: two swept back, a spine behind each cheek, and a crown of them behind the skull."""
    geo = None
    for sg in (1, -1):
        base = Vector((sg * 0.03, 0.0, -0.01))
        pts = [base, base + Vector((sg * 0.02, 0.09, 0.09)), base + Vector((sg * 0.03, 0.2, 0.17)), base + Vector((sg * 0.03, 0.3, 0.2))]
        geo = g.merge(geo, g.tube(pts, [0.024, 0.02, 0.012, 0.002], n=5))
        for k, (dz, ln) in enumerate(((-0.03, 0.09), (-0.06, 0.07))):
            b0 = Vector((sg * 0.05, 0.0, dz))
            geo = g.merge(geo, g.cone(b0, b0 + Vector((sg * 0.035, ln, 0.0)), 0.012, n=4))
    frill = None
    for i in range(7):
        a = math.pi * (0.1 + 0.8 * i / 6)
        d = Vector((math.cos(a), 0, math.sin(a)))
        b0 = Vector((d.x * 0.06, 0.06, d.z * 0.05 - 0.03))
        frill = g.merge(frill, g.blade(b0, b0 + Vector((d.x * 0.12, 0.08, d.z * 0.12)), 0.035, normal=d, belly=0.2))
    return [kit._part("horns", [(geo, mat("drake_horn")), (frill, mat("drake_horn")), (g.ico((0, 0.01, 0.0), 0.016, sub=0), field("ember", 2.4))])]


def gift_tail_drake():
    """A drake's tail: long, ridged, a spade at its end."""
    pts = [Vector((0, 0.0, 0.0)), Vector((0, 0.13, 0.0)), Vector((0, 0.28, 0.03)), Vector((0, 0.43, 0.09)), Vector((0, 0.56, 0.18)), Vector((0, 0.64, 0.28))]
    body = g.tube(pts, [0.045, 0.042, 0.034, 0.024, 0.014, 0.006], n=6)
    ridge = None
    for i in range(1, 5):
        d = (pts[i + 1] - pts[i - 1]).normalized()
        up = (Z - d * Z.dot(d)).normalized()
        b0 = pts[i] + up * 0.02
        ridge = g.merge(ridge, g.blade(b0, b0 + up * (0.07 - 0.008 * i) + d * 0.03, 0.06, normal=X, belly=0.35))
    d = (pts[-1] - pts[-2]).normalized()
    spade = g.blade(pts[-1] - d * 0.01, pts[-1] + d * 0.12, 0.1, normal=X, belly=0.45, thick=0.012)
    return [kit._part("tail", [(body, mat("drake_hide")), (ridge, mat("drake_horn")), (spade, mat("drake_horn"))])]


GIFTS = {"tail-fox": gift_tail_fox, "glow-fox": gift_glow_fox, "horn-brow-stag": gift_horn_brow_stag, "long-legs-stag": gift_long_legs_stag,
         "horns-drake": gift_horns_drake, "tail-drake": gift_tail_drake}


def gifts():
    import bpy
    for name, fn in GIFTS.items():
        kit.reset()
        objs = fn()
        path = os.path.join(kit.OUT, "gifts", name + ".glb")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        log("wrote", os.path.relpath(path, kit.ROOT), "%d KB" % (os.path.getsize(path) // 1024))


if __name__ == "__main__":
    if sys.argv[1:] == ["gifts"]:
        import genius_lines  # noqa: F401  (it registers the families, this one among them)
        import lines_wolfkin
        lines_wolfkin.gifts()
    else:
        print(__doc__)
