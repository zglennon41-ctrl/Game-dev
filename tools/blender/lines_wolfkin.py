"""WILDLINE genius lines, the wolf's kin: the Fox, the Stag and the Drake, each form a body of
its own on the wolf's rig (docs/genius-lines.md; genius_lines.py builds the Wolf and
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
  the Drake    a body of its own on the wolf's bones (see "The Drake" below): crane, horns, frill, ridge,
               wings, membrane, belly, scales, throat, tailend, shell, lies, jaw, gape, breath, nostrils, eye

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
    "fur_grey": ((0.4, 0.39, 0.38), 0.9, 0.0),       # the grey of these three's age (a beard, a ghost): paler than the Wolf's
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
ROUND = ("scar", "hide_scar", "glaze", "slag", "bark", "bone", "metal_iron", "wax", "coal", "claw", "moss", "leaf", "weed", "petal", "lichen", "ash", "horn", "mark_ridge", "mark_wings",
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
#
# A true drake on the wolf's bones (docs/genius-lines.md, "The second pass", rule 5). Of the
# wolf it keeps the skeleton, the clips and the skin of its legs. Everything else is its own:
# one skin from the back of its skull to the end of its tail, laid along the wolf's bones (a
# long neck, a barrel of a body deep in the chest, a tail as thick as its loins where it
# leaves them); a wedge of a head with a brow, a jaw that is a piece of its own, nostrils and
# teeth; elbows and knees out from the body where a wolf stands square, and a heel on the
# ground; plates lapped under it from the chin to the tail; scales in rows along its back;
# three clawed toes and a spur on every foot. It has six limbs, and that is the choice made:
# its wings are a third pair, rooted above the shoulder, each an arm, a wrist and fingers
# with the skin between, and they ride the chest's bone as pieces of their own that the game
# moves.

PALETTE.update({
    "hide_wing": ((0.16, 0.2, 0.19), 0.6, 0.0), "drake_horn": ((0.72, 0.66, 0.5), 0.45, 0.0), "drake_claw": ((0.8, 0.75, 0.62), 0.35, 0.0),
    "drake_tooth": ((0.86, 0.82, 0.72), 0.35, 0.0), "eye_slit": ((0.012, 0.012, 0.016), 0.25, 0.0), "eye_socket": ((0.03, 0.028, 0.034), 0.5, 0.0),
    "stone_dust": ((0.56, 0.54, 0.5), 1.0, 0.0), "brass_coin": ((0.66, 0.5, 0.2), 0.35, 0.85), "iron_gate": ((0.2, 0.2, 0.23), 0.5, 0.75),
    "smoke_pale": ((0.14, 0.14, 0.16), 1.0, 0.0), "paper_ledger": ((0.76, 0.7, 0.56), 0.8, 0.0), "leather_book": ((0.24, 0.12, 0.07), 0.7, 0.0),
    "glaze_kiln": ((0.72, 0.74, 0.7), 0.15, 0.0), "slag_crust": ((0.07, 0.06, 0.062), 0.6, 0.0), "ash_fall": ((0.55, 0.54, 0.52), 1.0, 0.0),
})

D_NECK = ("Torso3", "Neck1", "Neck2", "Neck3", "Head")
D_TAIL = ("Back",) + tuple("Tail%d" % i for i in range(1, 9))
# how a drake carries its neck: how steeply each of its three lengths rises, and its head
# (degrees above the level; the head's is its snout's). The first is how it is made.
CRANES = {
    "swan": (62, 56, 28, 0), "low": (8, -6, -4, 2), "level": (24, 20, 14, 2), "reared": (86, 82, 58, 6), "hook": (96, 66, 4, -34),
    "down": (44, 8, -44, -62), "up": (66, 74, 84, 62), "ground": (-22, -10, 4, 6), "strike": (74, 40, -8, -14), "proud": (80, 84, 44, -6),
    "sky": (80, 88, 92, 84),
}


def _cr(pts, n=3):
    """A smooth line through points (Catmull-Rom), n steps to a span (or a list: steps for each)."""
    pts = [V(p) for p in pts]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        steps = n if isinstance(n, int) else n[i - 1]
        for k in range(steps):
            t = k / steps
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1].copy())
    return out


def _frames(line):
    """[(point, the way it runs, its left, its top)] along a line, the frame carried from each
    point to the next without a twist (a tail may curl right round)."""
    out, prev = [], None
    n = len(line)
    for i, p in enumerate(line):
        d = line[min(i + 1, n - 1)] - line[max(i - 1, 0)]
        d = d.normalized() if d.length > 1e-7 else (prev[0].copy() if prev else Y.copy())
        if prev is None:
            u, v = _perp(d)
        else:
            q = prev[0].rotation_difference(d)
            u = q @ prev[1]
            u = (u - d * u.dot(d)).normalized()
            v = q @ prev[2]
            v = (v - d * v.dot(d) - u * v.dot(u)).normalized()
        prev = (d, u, v)
        out.append((V(p), d, u, v))
    return out


def _chain_w(names, joints, p):
    """Which bones of a chain carry a point: names[i] runs from joints[i] to joints[i + 1].
    A point is its own bone's at the middle of that bone, and half its neighbour's at a joint."""
    best, s = 1e9, 0.0
    for i in range(len(joints) - 1):
        a, ab = joints[i], joints[i + 1] - joints[i]
        f = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
        dist = (p - (a + ab * f)).length
        if dist < best - 1e-7:
            best, s = dist, i + f
    ws = [(nm, max(0.0, 1.0 - abs(s - (j + 0.5)))) for j, nm in enumerate(names)]
    tot = sum(w for _, w in ws)
    if tot < 1e-6:
        return [(names[0] if s < 1 else names[-1], 1.0)]
    return [(nm, w / tot) for nm, w in ws if w > 1e-4]


def _ring(c, u, v, a, b, m=12, crest=0.0, keel=0.0):
    """Points round a section, from its left over its top: a across, b up and down; crest
    draws its top to a ridge and keel its underside."""
    out = []
    for j in range(m):
        th = 2 * math.pi * j / m
        cs, sn = math.cos(th), math.sin(th)
        up, dn = max(0.0, sn), max(0.0, -sn)
        k = 1.0 + crest * up ** 6 + keel * dn ** 6
        out.append(c + u * (a * cs * (1.0 - 0.25 * crest * up ** 2 - 0.3 * keel * dn ** 2)) + v * (b * sn * k))
    return out


def _added(r, n0, pick, material):
    """Of the faces added since there were n0, those that pass pick(centre, normal) take a material."""
    me = r.mesh.data
    if material.name not in [m.name for m in me.materials]:
        me.materials.append(material)
    slot = [m.name for m in me.materials].index(material.name)
    R = r.M.to_3x3()
    for p in list(me.polygons)[n0:]:
        if pick(r.M @ p.center, (R @ p.normal).normalized()):
            p.material_index = slot


def _face_out(r, n0, inside):
    """Faces added since there were n0 that lie on the body (a scale, a plate: not closed
    shapes) are turned to face away from it: inside(centre) is a point within the body there."""
    me = r.mesh.data
    R = r.M.to_3x3()
    for p in list(me.polygons)[n0:]:
        c = r.M @ p.center
        if (R @ p.normal).dot(c - inside(c)) < 0.0:
            p.flip()
    me.update()


def _faces(r):
    return len(r.mesh.data.polygons)


def _drake_legs(r, splay=1.0):
    """A drake's legs of a wolf's. Before: the upper bone twice as long and slanting out from
    the body to an elbow that stands clear of it, a short forearm under that. Behind: the knee
    out, and the hock brought down to the ground for a heel, so that it stands on the flat of
    a long foot. (The bones go with the flesh, so the clips still fit.)"""
    for tag in ("fl", "fr", "bl", "br"):
        sg = 1 if tag.endswith("l") else -1
        side = ".L" if sg > 0 else ".R"
        if tag[0] == "f":
            z = [r.bone("FrontUpperLeg" + side).z, r.bone("FrontLowerLeg" + side).z, 0.0]
            to = [z[0], z[0] * 0.52, 0.0]
            out = 0.42 * splay
        else:
            z = [r.bone("BackLeg" + side).z, r.bone("BackUpperLeg" + side).z, r.bone("BackLowerLeg" + side).z, 0.0]
            to = [z[0], z[0] * 0.6, z[0] * 0.26, 0.0]
            out = 0.34 * splay

        def T(p, z=z, to=to, out=out, sg=sg):
            if p.z >= z[0]:
                return p
            nz = p.z
            for i in range(len(z) - 1):
                if p.z >= z[i + 1]:
                    nz = to[i] + (to[i + 1] - to[i]) * (z[i] - p.z) / max(1e-6, z[i] - z[i + 1])
                    break
            t = max(0.0, min(1.0, (to[0] - nz) / max(1e-6, to[0] - to[1])))
            return Vector((p.x + sg * out * t, p.y, nz))
        r.deform(r.legs(tag), T)
        for low, k in ((("FrontLowerLeg" if tag[0] == "f" else "BackLowerLeg") + side, (1.24, 1.14, 1.0)), (("FrontLowerLeg" if tag[0] == "f" else "BackUpperLeg") + side, (1.1, 1.06, 1.0))):
            c = r.bone(low)
            r.scale([low], (c.x, c.y, 0), k)


def _crane(r, pitches, k=1.0):
    """Carry the neck so: each of its three lengths at its pitch, then the head (see CRANES).
    Everything on the neck and head goes with them. k: how far from where it is to there."""
    head = _head(r)
    carried = 0.0
    for i in range(3):
        a, b = r.bone(D_NECK[i + 1]), r.bone(D_NECK[i + 2])
        now = math.degrees(math.atan2(b.z - a.z, a.y - b.y))
        turn = (pitches[i] - now) * k
        if abs(turn) > 0.01:
            r.rotate(list(NECK[i:]) + head, a, X, -math.radians(turn))
        carried += turn
    turn = (pitches[3] - _S.get("head_pitch", 0.0)) * k - carried
    if abs(turn) > 0.01:
        r.rotate(head, r.bone("Head"), X, -math.radians(turn))
    _S["head_pitch"] = _S.get("head_pitch", 0.0) + carried + turn


def _trail(r, falls, floor=0.2, yaw=()):
    """Carry the tail so: each joint after the first as high as falls says, between the ground
    (0) and the root of the tail (1); then round to one side, joint by joint (yaw, degrees)."""
    root = r.bone("Tail1").z
    for i in range(7):
        a, b = r.bone("Tail%d" % (i + 1)), r.bone("Tail%d" % (i + 2))
        L = (b - a).length
        if L < 1e-5:
            continue
        want = floor + (root - floor) * falls[min(i, len(falls) - 1)]
        now = math.asin(max(-1.0, min(1.0, (b.z - a.z) / L)))
        to = math.asin(max(-0.97, min(0.97, (want - a.z) / L)))
        if abs(to - now) > 1e-4:
            r.rotate(r.family("Tail%d" % (i + 1)), a, X, to - now)
    for i, a in enumerate(yaw):
        if abs(a) > 1e-4:
            r.rotate(r.family("Tail%d" % (i + 1)), r.bone("Tail%d" % (i + 1)), Z, math.radians(a))


def _neck_curve(r):
    """The line of its neck as it lies: from within its chest, through the joints, and on."""
    J = [r.bone(nm) for nm in D_NECK[1:]]
    return _frames(_cr([_S["neck_base"]] + J + [J[3] + (J[3] - J[2]) * 0.5], 4))


def _recrane(r, pitches, k=1.0):
    """Carry the neck another way once it is made. Every point of the neck keeps its place
    along the neck's own line and across it, and the line is bent: so a long neck stays round
    however it is carried (turned bone by bone it would crease at each joint)."""
    wN = r._weights(list(NECK))
    was = r.world_verts()
    old = _neck_curve(r)
    _crane(r, pitches, k)
    new = _neck_curve(r)
    me = r.mesh.data

    def at(line, j, f):
        (p0, d0, u0, v0), (p1, d1, u1, v1) = line[j], line[j + 1]
        return p0.lerp(p1, f), d0.lerp(d1, f).normalized(), u0.lerp(u1, f).normalized(), v0.lerp(v1, f).normalized()
    for i, vert in enumerate(me.vertices):
        w = wN[i]
        if w < 0.02:
            continue
        p = was[i]
        best, bj, bf = 1e18, 0, 0.0
        for j in range(len(old) - 1):
            a, ab = old[j][0], old[j + 1][0] - old[j][0]
            f = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-12, ab.length_squared)))
            dd = (p - (a + ab * f)).length_squared
            if dd < best:
                best, bj, bf = dd, j, f
        c0, d0, u0, v0 = at(old, bj, bf)
        c1, d1, u1, v1 = at(new, bj, bf)
        off = p - c0
        q = c1 + d1 * off.dot(d0) + u1 * off.dot(u0) + v1 * off.dot(v0)
        vert.co = r.Minv @ (r.M @ vert.co).lerp(q, min(1.0, w))
    me.update()


HEAD_K = 1.5       # its head against the wolf's: a dragon is read by its head


def _rear(r, lift):
    """Stand it up before: the forelegs longer by lift, and everything before the hips raised
    with them (most at the shoulder and beyond), so that its back climbs to its withers."""
    ysh, yhip = r.bone("FrontUpperLeg.L").y, r.bone("BackLeg.L").y
    for tag in ("fl", "fr"):
        h = r.bone(bk.LEG_ROOTS[tag][0]).z
        r.scale(r.legs(tag), (0, 0, 0), (1, 1, (h + lift) / h))
    r.deform(r.body_bones(), lambda p: Vector((p.x, p.y, p.z + lift * max(0.0, min(1.0, (yhip - p.y) / (yhip - ysh))))))


def drake_species(r):
    """The wolf made a drake's frame: see the note above. What is laid over it is drake_measure's."""
    head = _head(r)
    top = r.top(r.bone("Torso2").y)
    # the trunk: longer than a wolf's and broader, and less deep
    r.scale(bk.TORSO, (0, 0, top), (1.16, 1.0, 1.0))
    r.stretch_y(-0.6, 0.4, 1.12)
    # the legs: thick, and long enough to carry its belly clear of the ground; the elbows and
    # the knees a little out, a heel on the ground
    r.leg_length(0.36)
    _drake_legs(r, 0.7)
    r.leg_girth(1.75)
    gl._feet(r, 1.2)
    # the neck and the tail are drawn out, and carried as a drake carries them (its own flesh
    # is laid along them when they have their shape: _drake_body)
    _S["ear0"] = (r.bone("Ear1.L") - r.bone("Ear1.R")).length
    r.lengthen_chain(list(NECK), head, 2.25)
    _S["head_pitch"] = 0.0
    _crane(r, CRANES["swan"])
    tb = _tailbones(r)

    def thin(p):
        best, q = 1e9, tb[0]
        for a, b in zip(tb, tb[1:]):
            ab = b - a
            f = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
            c = a + ab * f
            if (p - c).length < best:
                best, q = (p - c).length, c
        return q + (p - q) * 0.15
    r.deform(_tail(r), thin)
    r.lengthen_chain(_tail(r), [], 1.85)
    _trail(r, (0.84, 0.66, 0.5, 0.38, 0.3, 0.26, 0.3))


def drake_ages(r, level):
    head, hb = _head(r), r.bone("Head")
    top = r.top(r.bone("Torso2").y)
    _S["age"] = {}
    if level <= 1:                  # the hatchling: a head, feet and eyes it has not grown into
        r.scale(head, hb, 1.5)
        r.lengthen_chain(list(NECK), head, 0.46)
        r.leg_length(0.08)
        r.leg_girth(1.1)
        r.stretch_y(r.bone("Torso3").y, r.bone("Back").y, 0.72)
        zc = (r.top(r.bone("Torso2").y) + r.bottom(r.bone("Torso2").y, half_width=0.1)) / 2
        r.scale(bk.TORSO, (0, 0, zc), (1.1, 1.0, 1.08))
        r.lengthen_chain(_tail(r), [], 0.5)
        gl._feet(r, 1.3)
        _S["age"] = {"muzzle": 0.66, "eye": 1.5, "brow": 0.0, "teeth": 0.0, "neck": 1.15, "claw": 0.7}
    elif level == 2:                # half-grown: leggy, the head still a size large
        r.scale(head, hb, 1.14)
        r.lengthen_chain(list(NECK), head, 0.84)
        r.lengthen_chain(_tail(r), [], 0.88)
        _S["age"] = {"muzzle": 0.9, "eye": 1.15, "brow": 0.75, "teeth": 0.8, "claw": 0.9}
    elif level >= 4:                # in its prime: heavier before, longer behind
        r.scale(["Torso3", "Torso2"], (0, 0, top), (1.08, 1.0, 1.07))
        r.leg_girth(1.07)
        r.lengthen_chain(_tail(r), [], 1.1)
        _S["age"] = {"brow": 1.2, "teeth": 1.1}
    rear = float(_S.get("spec", {}).get("build", {}).get("rear", 0.0))
    if abs(rear) > 1e-4:
        _rear(r, rear)


def _horn_mat():
    return kit.mark("ridge", mat("drake_horn"))


def _hide2():
    """The second value of its hide (the coat's trim: its scales and the plates of its back)."""
    return kit.mark("ridge", mat("drake_horn"))


# --- pieces that ride a bone and are moved by the game (rule 6) ------------------------------

def _piece(kind, what, items, pivot, bone, side="", n=None):
    """A piece of this form that the game moves by its name, riding a bone: kept until the
    body has its size, then made (_ride). items: [(geometry, material, shaded round?)]."""
    items = [(geo, m, sm) for geo, m, sm in items if geo and geo[0]]
    if items:
        _S.setdefault("pieces", []).append(dict(kind=kind, what=what, items=items, pivot=V(pivot).copy(), bone=bone, side=side, n=n))


def _ride(r, sockets, k):
    """Make the pieces, at the body's size, each a mesh of its own parented to its bone with
    its origin at its pivot: the game finds it under the bone's attachment and moves it."""
    S = Matrix.Scale(k, 4)
    for pc in _S.get("pieces", []):
        name = "%s_%s%s%s" % (pc["kind"], pc["what"], "_" + pc["side"] if pc["side"] else "", "_%d" % pc["n"] if pc["n"] is not None else "")
        ob = g.join(name, [g.to_object("%s_%d" % (name, i), g.moved(geo, S), m, sm) for i, (geo, m, sm) in enumerate(pc["items"])])
        at = pc["pivot"] * k
        ob.data.transform(Matrix.Translation(-at))
        ob.parent = r.arm
        ob.parent_type = "BONE"
        ob.parent_bone = pc["bone"]
        bpy.context.view_layer.update()
        ob.matrix_world = Matrix.Translation(at)
        sockets[name] = ob


# --- the drake's own flesh, laid over the wolf's frame ----------------------------------------

def _strip_wolf(r):
    """Take the wolf's own trunk, neck, head and tail away (the drake's are laid in their
    place): only its legs are kept, open at the top inside the drake's body."""
    import bmesh
    me = r.mesh.data
    legs = {r.mesh.vertex_groups[b].index for b in r.legs() if b in r.mesh.vertex_groups and "Shoulder" not in b}
    bm = bmesh.new()
    bm.from_mesh(me)
    dl = bm.verts.layers.deform.verify()
    gone = [f for f in bm.faces if min(sum(w for gi, w in v[dl].items() if gi in legs) for v in f.verts) < 0.12]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()


def _on(s, deg, lift=0.0):
    """A point on its skin at one place along it (s, of _S["body"]), deg round from its left
    over its top (90 its back, 270 its belly), and the way the skin faces there."""
    p, d, u, v, a, b = s[:6]
    th = math.radians(deg)
    cs, sn = math.cos(th), math.sin(th)
    n = (u * (cs / max(1e-6, a)) + v * (sn / max(1e-6, b))).normalized()
    return p + u * (a * cs) + v * (b * sn) + n * lift, n


def _drake_body(r, A):
    """One skin from the back of its skull to the end of its tail: a neck as deep as its chest
    where it leaves it and slender under the skull; a barrel, keeled before; a tail as thick
    as its loins where it leaves them and a whip at its end."""
    wolf = _skin()                 # the wolf's own trunk, as the frame was shaped: the drake's is cut to it
    spec, age = _S["spec"], _S["age"]
    bd = spec.get("build", {})
    S = _S["S"]
    nape = float(bd.get("nape", 1.0)) * age.get("neck", 1.0)
    girth = float(bd.get("brush", 1.0))
    # the trunk: five places along it, from the shoulder to the hip (the wolf's own back gives
    # its top, the wolf's brisket the keel of its chest, the wolf's ribs its breadth, made a barrel's)
    ysh, yhip = r.bone("FrontUpperLeg.L").y, r.bone("BackLeg.L").y
    _S["ysh"], _S["yhip"] = ysh, yhip
    ys = [ysh - 0.08, ysh + 0.34, (ysh + yhip) / 2 + 0.08, yhip - 0.26, yhip + 0.06]
    zts = [wolf.top(y, window=0.22) + 0.03 for y in (ys[1], ys[1], ys[2], ys[3], ys[4])]
    zk = _S["brisket"] - 0.04
    zbs = [zk + 0.07, zk, zk + 0.06, zk + 0.13, zk + 0.2]
    aa = [wolf.side(y, zt - 0.4) * k for y, zt, k in zip(ys, zts, (1.16, 1.3, 1.52, 1.56, 1.5))]
    trunk = [(Vector((0, y, (zt + zb) / 2)), a, (zt - zb) / 2) for y, zt, zb, a in zip(ys, zts, zbs, aa)]
    # the neck: its joints, from the head down
    J = [r.bone(nm) for nm in D_NECK[1:]]
    L = sum((J[i + 1] - J[i]).length for i in range(3))
    aB, bB = trunk[0][1] * 0.72, trunk[0][2] * 0.66
    aH, bH = 0.2 * S * nape, 0.205 * S * nape
    fj = _frames(J)
    neck, acc = [], 0.0
    for i, (p, d, u, v) in enumerate(fj):
        if i:
            acc += (J[i] - J[i - 1]).length
        t = min(1.0, acc / L)
        e = (1.0 - t) ** 1.7
        a, b = aH + (aB * nape - aH) * e, bH + (bB * nape - bH) * e
        neck.append((p - v * (0.42 * b * (1.0 - 0.5 * t)), a, b))
    # the tail: its joints, to a point beyond the last
    tb = _tailbones(r)
    tip = tb[7] + (tb[7] - tb[6]) * 1.15
    aT, bT = trunk[4][1] * 0.84, trunk[4][2] * 0.8
    Lt = sum((tb[i + 1] - tb[i]).length for i in range(7)) + (tip - tb[7]).length
    tail, acc = [], 0.0
    for i, p in enumerate(tb + [tip]):
        if i:
            acc += (p - (tb + [tip])[i - 1]).length
        t = min(1.0, (acc + 0.06 * Lt) / (1.06 * Lt))
        k = (1.0 - t) ** 0.9 * (0.78 + 0.22 * (1.0 - t)) * girth + 0.012
        a, b = aT * k, bT * k
        c = p - Z * (b * 0.85 * max(0.0, 1.0 - t * 2.2))
        if c.z < b:                                    # it lies on the ground: never in it
            c = Vector((c.x, c.y, b))
        tail.append((c, a, b))
    ctrl = list(reversed(neck)) + trunk + tail
    steps = [3] * 3 + [2] + [2] * 4 + [2] + [2] * 8
    line = _cr([c for c, _, _ in ctrl], steps)
    size = []                                           # its girth runs evenly from each place to the next (a curve through them would overshoot)
    for i, n in enumerate(steps):
        for k in range(n):
            f = k / n
            size.append(Vector((ctrl[i][1] + (ctrl[i + 1][1] - ctrl[i][1]) * f, ctrl[i][2] + (ctrl[i + 1][2] - ctrl[i][2]) * f, 0)))
    size.append(Vector((ctrl[-1][1], ctrl[-1][2], 0)))
    zone = []
    for i, n in enumerate(steps):
        zone.extend(["neck" if i < 4 else "back" if i < 8 else "tail"] * n)
    zone.append("tail")
    base = trunk[0][0]
    hipc = trunk[4][0]
    nj = [base] + J + [J[3] + (J[3] - J[2]) * 0.4]
    tj = [hipc] + tb + [tip]
    _S["neck_base"] = base.copy()
    fr = _frames(line)
    rings, ws, body = [], [], []
    m = 12
    nn = zone.count("neck")
    nt = zone.count("tail")
    for i, (p, d, u, v) in enumerate(fr):
        a, b = max(0.01, size[i].x), max(0.01, size[i].y)
        z = zone[i]
        if z == "neck":
            w = _chain_w(D_NECK, nj, p)
            t = 1.0 - i / max(1, nn)
            crest, keel = 0.1, 0.0
        elif z == "tail":
            w = _chain_w(D_TAIL, tj, p)
            t = (i - (len(fr) - nt)) / max(1, nt - 1)
            crest, keel = 0.16, 0.0
        else:
            w = r.spine_weights(p.y)
            t = (i - nn) / max(1, len(fr) - nn - nt)
            crest, keel = 0.06, 0.14 * max(0.0, 1.0 - abs(p.y - ys[1]) / 0.9)
        if p.z - b * (1.0 + keel) < 0.0 and z == "tail":
            p = Vector((p.x, p.y, b))
        rings.append(_ring(p, u, v, a, b, m=m, crest=crest, keel=keel))
        ws.extend([w] * m)
        body.append((p, d, u, v, a, b, w, z, t))
    n0 = _faces(r)
    _add(r, "drake_body", g.loft(rings, caps=True), ws, mat("fur_dark"), smooth=True)

    def near(c):
        return min(body, key=lambda s: (s[0] - c).length_squared)
    _added(r, n0, lambda c, nm: nm.dot(near(c)[3]) < -0.5, mat("fur_light"))
    _added(r, n0, lambda c, nm: near(c)[7] == "back" and nm.z > 0.5, kit.mark("saddle", mat("fur_dark")))
    _S["body"] = body
    _S["neckline"] = [s for s in body if s[7] == "neck"]
    _S["tail"] = [s for s in body if s[7] == "tail"]
    # its skin, as everything grown on it will ask for it
    sk = Skin.__new__(Skin)
    sk.v = [q for ring in rings for q in ring]
    sk.torso = [q for ring, s in zip(rings, body) if s[7] == "back" for q in ring]
    _S["skin"] = sk
    A.withers, A.belly = sk.top(A.t3.y), sk.bottom(A.t2.y, half_width=0.1)
    A._tops = [sk.top(y) for y in A._ys]
    A._sides = [sk.side(y, t - 0.42) for y, t in zip(A._ys, A._tops)]


def _lerp_table(table, y):
    """A row of a table of (y, ...) rows at y (rows run from the back of the head forward)."""
    if y >= table[0][0]:
        return table[0]
    for a, b in zip(table, table[1:]):
        if b[0] <= y <= a[0]:
            t = (a[0] - y) / max(1e-9, a[0] - b[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))
    return table[-1]


# How its eyes are set: (size, how far the lid comes down, the slit's width, the brow's weight, its slant)
D_EYES = {
    "young": (1.0, 0.0, 0.5, 0.0, 0.0),
    "keen": (1.0, 0.12, 0.24, 1.0, 0.0),
    "counting": (0.95, 0.46, 0.3, 1.15, -0.3),     # half shut, one brow up: it is adding something
    "glare": (0.95, 0.24, 0.14, 1.35, 0.7),        # the brow drawn down toward the snout
    "far": (1.18, 0.0, 0.4, 0.85, -0.5),           # wide, round in the slit: it is looking a long way off
    "old": (0.9, 0.36, 0.22, 1.5, -0.6),
    "shut": (0.9, 0.86, 0.2, 1.1, -0.2),           # all but closed: it is listening
    "sly": (0.95, 0.5, 0.18, 1.0, 0.25),
}


def _drake_head(r, A):
    """Its head, in place of the wolf's: a long flat wedge, widest behind the eyes, a brow over
    each, a lower jaw of its own (so that it can hang open), nostrils on top of the snout's end,
    teeth along the lip, and eyes with lids and a slit that the game blinks."""
    spec, level, age = _S["spec"], _S["level"], _S["age"]
    b = spec.get("build", {})
    hb = r.bone("Head")
    S = _S["S"]
    mz = float(b.get("muzzle", 1.0)) * age.get("muzzle", 1.0)
    jw = float(b.get("jaw", 1.0))
    gape_style, gape_size = gl.opt(spec.get("gape"))
    gape = {None: 0.0, "open": 0.42, "glow": 0.5, "yawn": 0.78, "speak": 0.3, "taste": 0.24}[gape_style] * (gape_size or 1.0)

    def P(x, y, z):
        return hb + Vector((x, y, z)) * S
    ys = -0.42
    yn, yt = ys - 0.56 * mz, ys - 0.66 * mz
    # the skull and upper jaw, from the back forward: (y, top, half-width, lip)
    SK = [(0.16, 0.09, 0.15, -0.01), (0.06, 0.2, 0.275, -0.05), (-0.24, 0.225, 0.25, -0.055), (ys, 0.165, 0.2, -0.055),
          ((ys + yn) / 2, 0.118, 0.158, -0.05), (yn, 0.108, 0.14, -0.044), (yt, 0.045, 0.09, -0.02)]
    rings = []
    for y, zt, w, zl in SK:
        zm = zl + 0.42 * (zt - zl)
        half = [(0.0, zt), (0.6 * w, zt - 0.012), (w, zm), (0.9 * w, zl)]
        rings.append([P(x, y, z) for x, z in half] + [P(0, y, zl + 0.015)] + [P(-x, y, z) for x, z in reversed(half[1:])])
    n0 = _faces(r)
    _add(r, "drake_skull", g.loft(rings, caps=True), "Head", mat("fur_dark"), smooth=True)
    if gape > 0.05:
        _added(r, n0, lambda c, nm: nm.z < -0.6 and c.y < hb.y, mat("hide_maw"))
    # the lower jaw, hung from its hinge
    hinge = Vector((0, 0.05, -0.05))
    Rg = Matrix.Rotation(gape, 3, X)

    def Jp(x, y, z):
        return hb + (hinge + Rg @ (Vector((x, y, z)) - hinge)) * S
    JW = [(0.12, -0.02, -0.15 * jw, 0.22), (-0.05, -0.058, -0.24 * jw, 0.252), (-0.3, -0.062, -0.19 * jw, 0.215),
          ((ys + yn) / 2, -0.06, -0.14 * jw, 0.142), (yn + 0.04, -0.054, -0.1 * jw, 0.112), (yt + 0.05, -0.05, -0.066, 0.062)]
    rings = []
    for y, zt, zb, w in JW:
        zm = zb + 0.4 * (zt - zb)
        rings.append([Jp(0, y, zt - 0.012), Jp(w, y, zt), Jp(w * 0.82, y, zm), Jp(0, y, zb), Jp(-w * 0.82, y, zm), Jp(-w, y, zt)])
    n0 = _faces(r)
    _add(r, "drake_jaw", g.loft(rings, caps=True), "Head", mat("fur_light"), smooth=True)
    jaw_up = Rg @ Z
    if gape > 0.05:
        _added(r, n0, lambda c, nm: nm.dot(jaw_up) > 0.6, mat("hide_maw"))
        t0, t1, t2 = Jp(0, -0.02, -0.04), Jp(0, (ys + yn) / 2, -0.035), Jp(0, yn + 0.1, -0.03)
        _add(r, "tongue", g.tongue([t0, t1, t2], [0.2 * S, 0.17 * S, 0.07 * S], thick=0.3, normal=jaw_up), "Head", mat("hide_tongue"), smooth=True)
        if gape_style == "glow":
            _piece("pulse", "gullet", [(g.ico(P(0, 0.0, -0.07), 0.13 * S, sub=1, scale=(1.0, 1.2, 0.8)), field("throat", 3.6), True)], P(0, 0.0, -0.07), "Head")
    # teeth: along the upper lip, two of them fangs; and the lower jaw's when it is open
    kt = age.get("teeth", 1.0)
    fangs = gl.opt(spec.get("fangs"))[1] if spec.get("fangs") else 0.0
    if kt > 0.0:
        teeth = None
        for i in range(7):
            y = yt + 0.07 + (ys + 0.02 - yt - 0.07) * i / 6.0
            _, _, w, zl = _lerp_table(SK, y)
            Lt = (0.05 + 0.02 * math.sin(i * 2.1)) * kt
            if i == 1:
                Lt = (0.105 + 0.11 * fangs) * kt
            for sg in (1, -1):
                teeth = g.merge(teeth, g.cone(P(sg * 0.88 * w, y, zl + 0.012), P(sg * 0.9 * w, y - 0.012, zl - Lt), 0.017 * S * (1.5 if i == 1 else 1.0), n=4))
        if gape > 0.05:
            for i in range(5):
                y = yt + 0.12 + (ys - yt - 0.1) * i / 4.0
                w = _lerp_table([(q[0], q[3]) for q in JW], y)[1]
                Lt = (0.05 if i != 1 else 0.085) * kt
                for sg in (1, -1):
                    teeth = g.merge(teeth, g.cone(Jp(sg * 0.86 * w, y, -0.06), Jp(sg * 0.86 * w, y, -0.06 + Lt), 0.015 * S, n=4))
        _add(r, "teeth", teeth, "Head", mat("drake_tooth"), smooth=True)
    # nostrils: two dark slits on the top of the snout's end, each under a small hood
    for sg in (1, -1):
        c = P(sg * 0.068, yn + 0.015, 0.112)
        _add(r, "nostril_%d" % sg, g.ico(c + Vector((sg * 0.012, -0.012, 0.004)) * S, 0.03 * S, sub=1, scale=(0.7, 1.5, 0.6)), "Head", mat("nose"), smooth=True)
        _add(r, "nostril_hood_%d" % sg, g.ico(c + Vector((0, 0.03, 0.0)) * S, 0.048 * S, sub=1, scale=(0.85, 1.2, 0.62)), "Head", mat("fur_dark"), smooth=True)
    # the eyes: a socket, the eye with its slit (which the game blinks), a lid, a brow
    style, size = gl.opt(spec.get("eye"))
    style = style if style in D_EYES else ("young" if level <= 1 else "keen")
    ks, lidk, slit, brow, slant = D_EYES[style]
    ks *= (size or 1.0) * age.get("eye", 1.0)
    brow *= age.get("brow", 1.0)
    Re = 0.078 * S * ks
    one = gl.opt(spec.get("lid"))[0]
    for sg, side in ((1, "l"), (-1, "r")):
        c = P(sg * 0.202, -0.245, 0.118)
        out = Vector((sg * 0.86, -0.12, 0.42)).normalized()
        _add(r, "socket_%s" % side, g.ico(c - out * Re * 0.3, Re * 1.24, sub=1, scale=(0.5, 1.2, 1.0)), "Head", mat("eye_socket"), smooth=True)
        ball = g.ico(c, Re, sub=2, scale=(0.55, 1.15, 0.95))
        pup = g.ico(c + out * Re * 0.42, Re * 0.74, sub=1, scale=(0.3, slit, 1.0))
        _piece("blink", "eye", [(ball, field("eyes", 3.4), True), (pup, mat("eye_slit"), True)], c, "Head", side=side)
        lk = lidk
        if one == "shutter" and sg < 0:          # one eye never fully closes: the lid on that side gone thick as a shutter
            lk = 0.5
            sl = None
            for dz in (0.5, 0.05):
                sl = g.merge(sl, g.box(c + out * Re * 0.72 + Z * Re * dz, (0.022 * S, Re * 3.0, Re * 0.26), rot=(0.0, sg * 0.3, 0.0)))
            _add(r, "shutter_slats", sl, "Head", mat("metal_iron"))
            _add(r, "shutter", g.box(c + out * Re * 0.5 + Z * Re * 0.55, (0.05 * S, Re * 2.7, Re * 1.3), rot=(0.0, sg * 0.3, 0.0)), "Head", mat("slate"))
        if lk > 0.0:
            _add(r, "lid_%s" % side, g.ico(c + out * Re * 0.16 + Z * (Re * (1.02 - lk)), Re * 1.12, sub=1, scale=(0.6, 1.24, 0.62)), "Head", mat("fur_dark"), smooth=True)
        if brow > 0.0:
            up = (0.05 if sg > 0 else -0.01) * max(0.0, -slant)       # one brow a little higher: it is thinking
            pts = [P(sg * 0.125, ys - 0.03, 0.15 - 0.03 * max(0.0, slant)), P(sg * 0.2, -0.33, 0.212 + up * 0.5 - 0.02 * max(0.0, slant)),
                   P(sg * 0.238, -0.14, 0.246 + up), P(sg * 0.262, 0.06, 0.205 + up * 0.4)]
            _add(r, "brow_%s" % side, g.tube(pts, [0.02 * S * brow, 0.045 * S * brow, 0.05 * S * brow, 0.026 * S], n=6), "Head", mat("fur_dark"), smooth=True)
    # spines at the hinge of the jaw, swept back: the outline of a dragon's head from any side
    if level >= 2:
        ksp = 0.8 if level == 2 else 1.0
        sp = None
        for sg in (1, -1):
            for y0, z0, Ls in ((0.04, -0.02, 0.3), (0.0, -0.12, 0.22)):
                sp = g.merge(sp, _horn([P(sg * 0.24, y0, z0), P(sg * (0.3 + 0.12 * ksp), y0 + Ls * 0.6 * ksp, z0 - 0.02), P(sg * (0.3 + 0.1 * ksp), y0 + Ls * ksp * 1.15, z0 + 0.03)], 0.05 * S, n=5))
        _add(r, "jaw_spines", sp, "Head", _horn_mat(), smooth=True)
    # what the rest is built to
    _S["head"] = dict(hb=hb.copy(), S=S, P=P, J=Jp, ys=ys, yn=yn, yt=yt, SK=SK, JW=JW, gape=gape, jaw_up=jaw_up, eye=Vector((0.202, -0.245, 0.118)), Re=Re, jw=jw)
    A.eye = P(0.202, -0.245, 0.118)
    A.nose = P(0, yt, 0.07)
    A.skull = P(0, 0, 0.225).z


def _drake_feet(r, A):
    """Three clawed toes before and a spur behind on every foot; a point at each elbow."""
    kc = _S["age"].get("claw", 1.0) * (gl.opt(_S["spec"].get("claws"))[1] if _S["spec"].get("claws") else 1.0)
    big = gl.opt(_S["spec"].get("claws"))[0] == "talons"
    socks = kit.mark("socks", mat("fur_dark"))
    for tag, foot, bone in gl.FEET:
        f = r.bone(foot)
        sg = 1 if f.x > 0 else -1
        turn = math.radians(26 if tag[0] == "f" else 14) * sg
        toes, claws = None, None
        for k, deg in enumerate((-30, 0, 30)):
            a = math.radians(deg) + turn
            d = Vector((math.sin(a), -math.cos(a), 0.0))
            b0 = Vector((f.x, f.y + 0.04, 0.1)) + d * 0.1
            Lt = (0.3 if k == 1 else 0.25) * (0.9 + 0.1 * kc)
            kn, tp = b0 + d * Lt * 0.55 + Z * 0.035, b0 + d * Lt - Z * 0.04
            toes = g.merge(toes, g.tube([b0, kn, tp], [0.085, 0.075, 0.05], n=6))
            Lc = (0.2 if not big else 0.34) * kc
            claws = g.merge(claws, g.tube([tp + Z * 0.02, tp + d * Lc * 0.55 + Z * (0.05 if not big else 0.1), tp + d * Lc - Z * 0.045], [0.042 * kc, 0.032 * kc, 0.004], n=5))
        d = Vector((sg * 0.35, 1.0, 0.0)).normalized()
        b0 = Vector((f.x, f.y + 0.16, 0.1))
        toes = g.merge(toes, g.tube([b0, b0 + d * 0.14 - Z * 0.03], [0.07, 0.045], n=6))
        claws = g.merge(claws, g.tube([b0 + d * 0.14 - Z * 0.02, b0 + d * (0.14 + 0.14 * kc) - Z * 0.06], [0.036 * kc, 0.004], n=5))
        _add(r, "toes_" + tag, toes, bone, socks, smooth=True)
        _add(r, "claws_" + tag, claws, bone, mat("drake_claw"), smooth=True)
        j = r.bone(bone)
        side = ".L" if sg > 0 else ".R"
        hide = mat("fur_dark")
        if tag[0] == "f":           # the shoulder: a mass of muscle from the withers' side to the elbow, and a forearm
            top = r.bone("FrontUpperLeg" + side)
            Lb = (top - j).length
            mid = top.lerp(j, 0.42) + Vector((sg * 0.03, 0.02, 0.0))
            _add(r, "shoulder_" + tag, g.ico(mid, Lb * 0.56, sub=1, scale=(0.56, 0.74, 1.0)), "FrontUpperLeg" + side, hide, smooth=True)
            _add(r, "forearm_" + tag, g.tube([j + Z * 0.04, j.lerp(Vector((f.x, f.y, 0.16)), 0.5) + Y * 0.03, Vector((f.x, f.y + 0.02, 0.16))], [0.15, 0.125, 0.1], n=6), bone, hide, smooth=True)
        else:                        # the haunch: the thigh a great round, a shank under it
            hip, knee = r.bone("BackLeg" + side), r.bone("BackUpperLeg" + side)
            Lb = (hip - knee).length
            mid = hip.lerp(knee, 0.4) + Vector((sg * 0.02, 0.05, 0.02))
            _add(r, "haunch_" + tag, g.ico(mid, Lb * 0.74, sub=1, scale=(0.5, 0.86, 1.0)), "BackLeg" + side, hide, smooth=True)
            _add(r, "shank_" + tag, g.tube([knee, knee.lerp(j, 0.5) + Y * 0.04, j], [0.17, 0.14, 0.11], n=6), "BackUpperLeg" + side, hide, smooth=True)
        if tag[0] == "f":           # the point of the elbow, out and back
            _add(r, "elbow_" + tag, g.cone(j + Vector((sg * 0.04, 0.05, 0.0)), j + Vector((sg * 0.15, 0.3, 0.1)), 0.08, n=5), bone, _horn_mat(), smooth=True)


def _drake_under(r, A):
    """Its underside: broad plates lapped one on the next, from under the jaw down the throat,
    over the keel of the chest and along the belly to a third of the way down the tail. They
    are the Path's colour where it has one."""
    spec = _S["spec"]
    style, size = gl.opt(spec.get("belly"))
    if spec.get("accent"):
        m1, m2 = mat("accent"), mat("accent_light")
        if style == "dark":
            m1, m2 = mat("accent_dark"), mat("accent")
        elif style == "pale":
            m1, m2 = mat("accent_light"), mat("accent_pale")
        elif style == "banded":
            m1, m2 = mat("accent_dark"), mat("accent_pale")
    else:
        m1, m2 = mat("fur_light"), mat("fur_light")
    body = _S["body"]
    nt = len(_S["tail"])
    use = body[1:len(body) - nt + max(3, int(nt * 0.42))]
    wide = 80.0

    def arc(s, k, back=0.0, m=5):
        p, d, u, v, a, b = s[:6]
        pts = []
        for j in range(m):
            th = math.radians(270.0 - wide + 2 * wide * j / (m - 1))
            pts.append(p - d * back + u * (a * math.cos(th) * k) + v * (b * math.sin(th) * k))
        return pts
    g1, g2, w1, w2 = None, None, [], []
    for i in range(len(use) - 1):
        s0, s1 = use[i], use[i + 1]
        gap = (s1[0] - s0[0]).length
        front, back = arc(s0, 1.015), arc(s1, 1.075, back=gap * 0.1)
        plate = g.loft([front, back], caps=False, closed=False)
        ww = [s0[6]] * len(front) + [s1[6]] * len(back)
        if i % 2:
            g2, w2 = g.merge(g2, plate), w2 + ww
        else:
            g1, w1 = g.merge(g1, plate), w1 + ww

    def inside(c):
        return min(body, key=lambda s: (s[0] - c).length_squared)[0]
    for nm, geo, ws, m in (("scutes", g1, w1, m1), ("scutes_b", g2, w2, m2)):
        n0 = _faces(r)
        _add(r, nm, geo, ws, m, smooth=True)
        _face_out(r, n0, inside)


def _dorsal(r):
    """The line of its back, from behind the skull to the end of its tail:
    [(point on the skin, the way the line runs toward the tail, up from the skin, weights, where: neck/back/tail, how far along that)]"""
    if "dorsal" not in _S:
        _S["dorsal"] = [(s[0] + s[3] * s[5] * 1.04, s[1], s[3], s[6], s[7], s[8]) for s in _S["body"][1:]]
    return _S["dorsal"]


def _drake_scales(r, A):
    """Scales where the precision allows: two rows of them lapped along each side of its back
    from the nape to the tail, in the second value of its hide; and a row low on the flank in
    its Path's colour."""
    spec, level = _S["spec"], _S["level"]
    style, size = gl.opt(spec.get("scales"))
    if level <= 1 or style == "none":
        return
    size = size or 1.0
    body = _S["body"]
    geo, geo2, ws, ws2 = None, None, [], []

    def kite(s, deg, k, lift=0.045):
        """One scale: its point to the tail, its back edge standing off the skin."""
        p, n = _on(s, deg)
        d = s[1]
        fwd = (d - n * d.dot(n)).normalized()
        side = fwd.cross(n).normalized()
        w = k * 0.36
        return ([p - fwd * k * 0.5 + n * 0.012, p + side * w + n * (0.012 + lift * 0.4), p + fwd * k * 0.62 + n * (0.012 + lift), p - side * w + n * (0.012 + lift * 0.4)], [(0, 1, 2, 3)])
    for i, s in enumerate(body[2:-3]):
        a, b, z = s[4], s[5], s[7]
        k = max(0.07, min(0.34, a * 0.7)) * size
        for sg in (1, -1):
            rows = ((90 - sg * 34, 1.0), (90 - sg * 64, 0.9)) if z == "back" else ((90 - sg * 40, 1.0),)
            for ri, (deg, kk) in enumerate(rows):
                if (i + ri) % 2 and z == "back":
                    continue
                if (i + ri) % 4 < 2:
                    geo = g.merge(geo, kite(s, deg, k * kk))
                    ws.extend([s[6]] * 4)
                else:
                    geo2 = g.merge(geo2, kite(s, deg, k * kk))
                    ws2.extend([s[6]] * 4)

    def inside(c):
        return min(body, key=lambda s: (s[0] - c).length_squared)[0]
    coin = style == "coin" and spec.get("accent")
    for nm, gg, ww, m in (("scales", geo, ws, mat("accent") if coin else _hide2()), ("scales_b", geo2, ws2, mat("accent_light") if coin else _hide2())):
        if gg:
            n0 = _faces(r)
            _add(r, nm, gg, ww, m, smooth=False)
            _face_out(r, n0, inside)


def drake_measure(r, A):
    """The drake itself, laid over the frame once the frame has its shape (and read in the
    wolf's place: where its eyes, its snout and the crown of its head are)."""
    _measure(r, A)
    _S["S"] = (r.bone("Ear1.L") - r.bone("Ear1.R")).length / _S["ear0"] * HEAD_K
    # the wolf's brisket (the lowest of its chest, between the legs): the keel of the drake's is cut to it
    wl = r._weights([b for b in r.legs() if "Shoulder" not in b])
    ysh = r.bone("FrontUpperLeg.L").y
    _S["brisket"] = min([p.z for p, k in zip(r.world_verts(), wl) if k < 0.2 and ysh - 0.3 < p.y < ysh + 0.5] or [r.bone("FrontUpperLeg.L").z - 0.25])
    _strip_wolf(r)
    # what is left of the wolf is its legs: one hide all the way down (a wolf's pale inner leg
    # and its socks are a wolf's; the drake's toes carry its socks)
    me = r.mesh.data
    names = [m.name for m in me.materials]
    if "fur_dark" in names:
        slot = names.index("fur_dark")
        for p in me.polygons:
            p.material_index = slot
    _drake_body(r, A)
    _drake_head(r, A)
    _drake_feet(r, A)
    _drake_under(r, A)
    _drake_scales(r, A)


def _drake_round(r):
    """Flesh, horn and bone are shaded round; plates and scales keep their planes (they were
    made so)."""
    me = r.mesh.data
    soft = {i for i, m in enumerate(me.materials) if m.name.startswith(ROUND) and not m.name.startswith(("mark_ridge", "mark_wings", "mark_tailtip", "drake_horn"))}
    for p in me.polygons:
        if p.material_index in soft:
            p.use_smooth = True


def _drake_pose(r, spec):
    """How it carries itself, put on last (everything on its neck and head goes with them):
    its crane, then the looks every one of the wolf's kin has; and its head never under the ground."""
    for style, size in gl.each(spec.get("crane")):
        if style in CRANES:
            _recrane(r, CRANES[style], size)
    _pose(r, spec)
    wh = r._weights(["Head"])
    for _ in range(12):
        low = min([p.z for p, k in zip(r.world_verts(), wh) if k > 0.5] or [1.0])
        if low > 0.012:
            break
        r.rotate(list(NECK) + _head(r), r.bone("Neck1"), X, -0.05)


def drake_build(form_id, level, spec, base):
    _S.clear()
    _S["level"] = level
    spec = _ordered(spec)
    _S["spec"] = spec
    r, sockets = gl.wolf_form(form_id, level, spec, species=drake_species, coat=("fur_dark", "fur_light"), marks=("socks",),
                              ages=drake_ages, measure=drake_measure)
    _recoat(r, {"fur_ruff": "fur_dark"})
    _drake_round(r)
    _S["k"] = STAND / _S["A"].skull
    _S["neck_base"] = _S["neck_base"] * _S["k"]
    _ride(r, sockets, _S["k"])
    _drake_pose(r, spec)
    gl.export(r, sockets, os.path.join(gl.OUT, form_id + ".glb"))


# --- what a drake grows (its slots, in data/genius-bases/drake.json) ---------------------------

def _horn(points, r0, n=6, steps=2, r1=0.004):
    """A horn through points: round, drawn to a point."""
    line = _cr(points, steps)
    m = len(line)
    return g.tube(line, [r0 + (r1 - r0) * (i / (m - 1)) ** 0.8 for i in range(m)], n=n)


def _bone_of(w):
    """The bone that has most of a point (a piece rides one bone)."""
    return w if isinstance(w, str) else max(w, key=lambda bw: bw[1])[0]


def _at_y(y):
    """Its body at y along its back (between two of the places it was made at)."""
    body = [s for s in _S["body"] if s[7] == "back"]
    if y <= body[0][0].y:
        return body[0]
    for s0, s1 in zip(body, body[1:]):
        if s0[0].y <= y <= s1[0].y:
            t = (y - s0[0].y) / max(1e-6, s1[0].y - s0[0].y)
            return (s0[0].lerp(s1[0], t), s0[1].lerp(s1[1], t).normalized(), s0[2].lerp(s1[2], t).normalized(), s0[3].lerp(s1[3], t).normalized(),
                    s0[4] + (s1[4] - s0[4]) * t, s0[5] + (s1[5] - s0[5]) * t, s0[6] if t < 0.5 else s1[6], "back", s0[8] + (s1[8] - s0[8]) * t)
    return body[-1]


def _inside(c):
    return min(_S["body"], key=lambda s: (s[0] - c).length_squared)[0]


def _slab(pts, n, up, dn):
    """A thin flat piece through points, seen from both sides: from up above them along n to dn below."""
    pts = [V(p) for p in pts]
    k = len(pts)
    verts = [p + n * up for p in pts] + [p - n * dn for p in pts]
    faces = [tuple(range(k)), tuple(range(2 * k - 1, k - 1, -1))]
    for i in range(k):
        j = (i + 1) % k
        faces.append((i, i + k, j + k, j))
    return verts, faces


def _lie(r, name, geo, ws, material, smooth=False):
    """Add what lies on its skin (open shapes), turned to face away from it."""
    if geo and geo[0]:
        n0 = _faces(r)
        _add(r, name, geo, ws, material, smooth=smooth)
        _face_out(r, n0, _inside)


def _smoke(p0, h, drift, k=1.0, n=4):
    """A thread of smoke going up from a point: puffs, each larger than the one under it."""
    geo = None
    for i in range(n):
        f = i / (n - 1.0)
        c = V(p0) + Z * (h * (0.1 + 0.9 * f)) + V(drift) * f + X * (0.07 * k * math.sin(i * 2.1 + h))
        geo = g.merge(geo, g.ico(c, (0.06 + 0.12 * f) * k, sub=1, scale=(1.0, 1.0, 0.86)))
    return geo


def _drake_horns(style):
    def fn(r, A, size):
        H = _S["head"]
        P, S = H["P"], H["S"]
        geo, dark = None, None

        def curve(sg, pts, rad, at=(0.165, 0.03, 0.2), k=1.0):
            base = P(sg * at[0], at[1], at[2])
            Q = [base] + [base + Vector((sg * x, y, z)) * (S * size * k) for x, y, z in pts]
            return _horn(Q, rad * S * (0.75 + 0.25 * size)), Q
        swept = [(0.04, 0.2, 0.14), (0.07, 0.48, 0.22), (0.08, 0.74, 0.2)]
        for sg in (1, -1):
            if style == "nubs":
                geo = g.merge(geo, curve(sg, [(0.02, 0.07, 0.08)], 0.05)[0])
            elif style == "swept":
                geo = g.merge(geo, curve(sg, swept, 0.058)[0])
            elif style == "broad":      # heavy, out to the sides and round to the front, like a bull's
                geo = g.merge(geo, curve(sg, [(0.16, 0.08, 0.06), (0.36, 0.12, 0.12), (0.46, -0.04, 0.26), (0.42, -0.2, 0.4)], 0.09)[0])
            elif style == "long":       # one grown long, and nicked down its length
                if sg > 0:
                    geo = g.merge(geo, curve(sg, swept, 0.058)[0])
                else:
                    ge, Q = curve(sg, [(0.05, 0.28, 0.2), (0.09, 0.66, 0.42), (0.11, 1.02, 0.52), (0.1, 1.34, 0.48)], 0.075)
                    geo = g.merge(geo, ge)
                    for t in (0.22, 0.36, 0.5, 0.64, 0.78):
                        c = _along(Q, t)
                        dark = g.merge(dark, _hoop(c, _along(Q, t + 0.02) - c, (0.075 * (1 - 0.8 * t) + 0.014) * S, 0.014 * S, n=6, sides=3))
            elif style == "crown":      # a crown of them
                geo = g.merge(geo, curve(sg, [(0.04, 0.26, 0.26), (0.07, 0.6, 0.52)], 0.065)[0])
                geo = g.merge(geo, curve(sg, [(0.14, 0.18, 0.1), (0.26, 0.42, 0.2)], 0.05, at=(0.22, 0.03, 0.16))[0])
                geo = g.merge(geo, curve(sg, [(0.14, 0.06, -0.02), (0.3, 0.2, -0.04)], 0.045, at=(0.262, 0.02, 0.07))[0])
            elif style == "brow":       # horns over the brow as well, forward
                geo = g.merge(geo, curve(sg, [(0.05, 0.22, 0.22), (0.08, 0.52, 0.4)], 0.07)[0])
                geo = g.merge(geo, curve(sg, [(0.05, -0.18, 0.12), (0.09, -0.42, 0.32)], 0.05, at=(0.2, -0.3, 0.215))[0])
            elif style == "flat":       # laid flat for the fall
                geo = g.merge(geo, curve(sg, [(0.02, 0.3, 0.02), (0.03, 0.62, 0.0), (0.03, 0.92, -0.04)], 0.052)[0])
            elif style == "droop":      # heavy and gone down with age
                geo = g.merge(geo, curve(sg, [(0.1, 0.18, 0.08), (0.2, 0.42, -0.06), (0.24, 0.54, -0.3), (0.2, 0.5, -0.5)], 0.078)[0])
            elif style == "lyre":       # rising and turning in, like the horns of a flame
                geo = g.merge(geo, curve(sg, [(0.1, 0.1, 0.2), (0.15, 0.2, 0.46), (0.07, 0.28, 0.72)], 0.06)[0])
            elif style == "sights":     # two short behind and one on the end of its snout: it sights along them
                geo = g.merge(geo, curve(sg, [(0.0, 0.06, 0.14), (0.0, 0.1, 0.24)], 0.045, at=(0.08, 0.02, 0.2))[0])
        if style == "ring":       # a pale band round the base of one horn, worn like a ring
            c = P(0.175, 0.07, 0.25)
            _add(r, "horn_ring", _hoop(c, Vector((0.12, 0.7, 0.7)), 0.07 * S, 0.022 * S, n=8, sides=4), "Head", mat("glaze_kiln"), smooth=True)
            return
        if style == "sights":
            b0 = P(0, H["yn"] + 0.08, 0.1)
            geo = g.merge(geo, g.cone(b0, b0 + Vector((0, 0.03, 0.2)) * (S * size), 0.04 * S, n=5))
        _add(r, "horns", geo, "Head", _horn_mat(), smooth=True)
        _add(r, "horn_nicks", dark, "Head", mat("coal"), smooth=True)
    return fn


def _drake_frill(style):
    def fn(r, A, size):
        H = _S["head"]
        P, S = H["P"], H["S"]
        spec = _S["spec"]
        acc = bool(spec.get("accent"))
        if style == "gate":           # bars round its neck, like the teeth of a gate
            _neck_band(r, "gate_bar", 0.84, mat("iron_gate"), wide=0.05, off=0.03)
            _neck_blades(r, "gate_teeth", 0.84, 13, 0.5 * size, 0.1, mat("iron_gate"), a0=-0.35, a1=1.35, sweep=0.45, out=0.9, belly=0.15)
        elif style in ("herald", "ruff"):   # a frill round the back of its head that opens when it speaks
            n = 9
            ribs, skin, edge = None, None, None
            prev = None
            for i in range(n):
                a = math.radians(-112 + 224 * i / (n - 1))          # round the back of the skull, over the top
                d = Vector((math.sin(a), 0.0, math.cos(a)))
                b0 = P(d.x * 0.2, 0.1, 0.08 + d.z * 0.12)
                L = (0.62 + 0.2 * math.cos(a) + (0.06 if i % 2 else 0.0)) * S * size
                tip = b0 + (d + Vector((0, 0.55 if style == "herald" else 1.1, 0))).normalized() * L
                ribs = g.merge(ribs, g.tube([b0, tip], [0.028 * S, 0.008 * S], n=4))
                if prev is not None:
                    mid = (prev[1] + tip) / 2
                    hub = (prev[0] + b0) / 2
                    skin = g.merge(skin, _panel([prev[0], prev[1], mid.lerp(hub, 0.14), tip, b0], 0.012 * S))
                    e0, e1 = prev[1].lerp(prev[0], 0.26), tip.lerp(b0, 0.26)
                    edge = g.merge(edge, _panel([e0 + Y * 0.012 * S, prev[1].lerp(prev[0], 0.1) + Y * 0.012 * S, tip.lerp(b0, 0.1) + Y * 0.012 * S, e1 + Y * 0.012 * S], 0.03 * S))
                prev = (b0, tip)
            _add(r, "frill_skin", skin, "Head", mat("accent") if acc else mat("fur_light"), smooth=False)
            _add(r, "frill_edge", edge, "Head", mat("accent_pale") if acc else mat("fur_light"), smooth=False)
            _add(r, "frill_ribs", ribs, "Head", _horn_mat(), smooth=True)
        elif style == "crown":        # spines standing round the back of its head
            geo = None
            for i in range(7):
                a = math.radians(-90 + 180 * i / 6)
                d = Vector((math.sin(a), 0.0, math.cos(a)))
                b0 = P(d.x * 0.22, 0.1, 0.08 + d.z * 0.13)
                L = (0.4 + 0.16 * math.cos(a)) * S * size
                geo = g.merge(geo, _horn([b0, b0 + (d + Y * 0.5).normalized() * L * 0.6, b0 + (d * 0.8 + Y * 0.9).normalized() * L], 0.04 * S, n=5))
            _add(r, "crownfrill", geo, "Head", _horn_mat(), smooth=True)
        elif style == "crest":        # a crest that lifts and spreads, from its brow down its nape
            D = [q for q in _dorsal(r) if q[4] == "neck"]
            skin, ribs, lit, ws, wr = None, None, None, [], []
            prev = None
            for i, (pt, d, up, w, z, t) in enumerate(D):
                L = (0.5 + 0.55 * math.sin(math.pi * min(1.0, (i + 1.2) / (len(D) * 0.9)))) * size
                b0, tip = pt - up * 0.04, pt + up * L + d * L * 0.3
                rib = g.tube([b0, tip], [0.03, 0.009], n=4)
                ribs = g.merge(ribs, rib)
                wr.extend([w] * len(rib[0]))
                if i % 2 == 0:
                    lit = g.merge(lit, g.ico(tip, 0.04, sub=0))
                if prev is not None:
                    pn = _panel([prev[0], prev[1].lerp(prev[0], 0.06), ((prev[1] + tip) / 2).lerp((prev[0] + b0) / 2, 0.16), tip.lerp(b0, 0.06), b0], 0.012)
                    skin = g.merge(skin, pn)
                    ws.extend([w] * len(pn[0]))
                prev = (b0, tip)
            _add(r, "crest_skin", skin, ws, mat("accent") if acc else mat("fur_light"), smooth=False)
            _add(r, "crest_ribs", ribs, wr, _horn_mat(), smooth=True)
            _add(r, "crest_tips", lit, "Neck3", field("crest", 3.0))
        elif style == "beard":        # long whiskers and a beard, grey
            geo = None
            for sg in (1, -1):
                b0 = P(sg * 0.13, H["yn"] + 0.1, 0.02)
                geo = g.merge(geo, _horn([b0, b0 + Vector((sg * 0.3, 0.08, -0.08)) * S * size, b0 + Vector((sg * 0.44, 0.4, -0.4)) * S * size, b0 + Vector((sg * 0.36, 0.7, -0.8)) * S * size], 0.03 * S, n=4))
            _add(r, "whiskers", geo, "Head", mat("fur_grey"), smooth=True)
            J = H["J"]
            tuft = None
            for k in range(5):
                b0 = J(0.05 * (k - 2), H["ys"] - 0.3 + 0.05 * abs(k - 2), -0.12 * H["jw"])
                tuft = g.merge(tuft, g.blade(b0, b0 + Vector((0.03 * (k - 2), 0.12, -(0.5 - 0.08 * abs(k - 2)))) * S * size, 0.1 * S, normal=Y, belly=0.35))
            piv = J(0, H["ys"] - 0.26, -0.12 * H["jw"])
            _piece("sway", "beard", [(tuft, mat("fur_grey"), True)], piv, "Head")
    return fn


def _drake_ridge(style):
    def fn(r, A, size):
        m = _horn_mat()
        spec = _S["spec"]
        acc = bool(spec.get("accent"))
        D = _dorsal(r)
        back = [q for q in D if q[4] == "back"]

        def gap(i):
            return (D[min(i + 1, len(D) - 1)][0] - D[max(i - 1, 0)][0]).length / 2

        def plates(height, material, name, every=1, lean=0.38, wide=1.0, zones=("neck", "back", "tail"), tail_to=0.62, alt=None):
            geo, geo2, ws, ws2 = None, None, [], []
            for i, (pt, d, up, w, z, t) in enumerate(D):
                if z not in zones or (z == "tail" and t > tail_to) or i % every:
                    continue
                h = height(z, t, i)
                if h <= 0.0:
                    continue
                u = d.cross(up).normalized()
                bl = g.blade(pt - up * 0.05, pt + up * h + d * (h * lean), gap(i) * 1.5 * every * wide, normal=u, belly=0.34, thick=0.035)
                if alt is not None and (i // every) % 2:
                    geo2, ws2 = g.merge(geo2, bl), ws2 + [w] * 6
                else:
                    geo, ws = g.merge(geo, bl), ws + [w] * 6
            _add(r, name, geo, ws, material, smooth=False)
            if geo2:
                _add(r, name + "_b", geo2, ws2, alt, smooth=False)

        def std(z, t, i):
            return {"neck": 0.1 + 0.14 * (1.0 - t), "back": 0.24 + 0.1 * math.sin(t * math.pi), "tail": 0.26 * (1.0 - t / 0.62) + 0.04}[z] * size
        if style == "plates":
            plates(std, m, "ridge")
        elif style == "hoard":        # broad plates, two sizes turn about, in its Path's colour: a back like a row of shields
            a1, a2 = (mat("accent_light"), mat("accent")) if acc else (m, m)
            plates(lambda z, t, i: ({"neck": 0.24 + 0.24 * (1.0 - t), "back": 0.56 + 0.3 * math.sin(t * math.pi), "tail": 0.5 * (1.0 - t / 0.7) + 0.08}[z]) * size * (1.0 if i % 2 else 0.72),
                   a1, "ridge_hoard", lean=0.16, wide=1.25, alt=a2, tail_to=0.7)
        elif style == "young":        # a ridge it has not grown into: a few plates, too big for it
            plates(lambda z, t, i: (0.3 + 0.16 * math.sin(t * math.pi)) * size, m, "ridge", every=2, zones=("back",), lean=0.2, wide=0.8)
            plates(lambda z, t, i: 0.16 * size * (1.0 - t), m, "ridge_tail", every=2, zones=("tail",), tail_to=0.5)
        elif style == "spines":       # fine and swept: nothing to catch the wind
            geo, ws = None, []
            for i, (pt, d, up, w, z, t) in enumerate(D):
                if z == "tail" and t > 0.5:
                    continue
                h = (0.2 + 0.08 * math.sin(i * 1.7)) * size * (0.7 if z == "neck" else 1.0)
                sp = g.cone(pt - up * 0.03, pt + up * h * 0.7 + d * h * 0.9, 0.035, n=4)
                geo, ws = g.merge(geo, sp), ws + [w] * len(sp[0])
            _add(r, "ridge_spines", geo, ws, m, smooth=True)
        elif style == "flame":        # a ridge like a row of flames, in its Path's colour; here and there one is lit
            a1, a2 = (mat("accent"), mat("accent_light")) if acc else (m, m)
            plates(lambda z, t, i: ({"neck": 0.16 + 0.2 * (1.0 - t), "back": 0.4 + 0.16 * math.sin(t * math.pi), "tail": 0.34 * (1.0 - t / 0.62) + 0.05}[z]) * size * (1.0 + 0.22 * math.sin(i * 2.2)),
                   a1, "ridge_flame", lean=0.55, wide=0.9, alt=a2)
            for k, q in enumerate(back[1::3][:3]):
                pt, d, up, w = q[:4]
                u = d.cross(up).normalized()
                h = 0.62 * size
                outer = g.blade(pt - up * 0.04, pt + up * h + d * h * 0.3, 0.3, normal=u, belly=0.3, thick=0.05)
                core = g.blade(pt + up * 0.02, pt + up * h * 0.6 + d * h * 0.12, 0.15, normal=u, belly=0.3, thick=0.075)
                _piece("flick", "flame" + "abc"[k], [(outer, a2 if acc else m, False), (core, field("ember", 2.4), False)], pt, _bone_of(w))
        elif style == "sail":         # a ridge gone finned and ragged
            skin, ribs, ws, wr = None, None, [], []
            prev = None
            for i, (pt, d, up, w, z, t) in enumerate(D):
                if z == "tail" and t > 0.55:
                    break
                h = {"neck": 0.2 + 0.3 * (1.0 - t), "back": 0.5 + 0.4 * math.sin(t * math.pi), "tail": 0.42 * (1.0 - t / 0.55)}[z] * size * (0.82 + 0.18 * math.sin(i * 4.1))
                b0, tip = pt - up * 0.04, pt + up * h + d * h * 0.22
                if i % 2 == 0:
                    rib = g.tube([b0, tip], [0.028, 0.008], n=4)
                    ribs, wr = g.merge(ribs, rib), wr + [w] * len(rib[0])
                if prev is not None:
                    pn = _panel([prev[0], prev[1], tip, b0], 0.014)
                    skin, ws = g.merge(skin, pn), ws + [w] * len(pn[0])
                prev = (b0, tip)
            _add(r, "sail", skin, ws, mat("accent_light") if acc else mat("fur_light"), smooth=False)
            _add(r, "sail_ribs", ribs, wr, m, smooth=True)
        elif style == "beads":        # a row of beads on a wire, to count on
            pts, wts = [], []
            for (pt, d, up, w, z, t) in back:
                pts.append(pt + up * 0.2 * size)
                wts.append(w)
            line = _cr(pts, 2)
            wire = g.tube(line, [0.014] * len(line), n=3, caps=False)
            _add(r, "bead_wire", wire, [r.spine_weights(p.y) for p in wire[0]], mat("metal_iron"), smooth=True)
            posts, beads, bright, wp, wb, wc = None, None, None, [], [], []
            for i, p in enumerate(line):
                w = r.spine_weights(p.y)
                if i % 4 == 0:
                    post = g.tube([p, p - Z * 0.26 * size], [0.02, 0.03], n=4)
                    posts, wp = g.merge(posts, post), wp + [w] * len(post[0])
                if i % 4 != 3:
                    b = g.ico(p, 0.085 * size, sub=1, scale=(1.0, 0.7, 1.0))
                    if i % 4 == 1:
                        bright, wc = g.merge(bright, b), wc + [w] * len(b[0])
                    else:
                        beads, wb = g.merge(beads, b), wb + [w] * len(b[0])
            _add(r, "bead_posts", posts, wp, m, smooth=True)
            _add(r, "beads", beads, wb, mat("accent_dark") if acc else mat("wood"), smooth=True)
            _add(r, "beads_b", bright, wc, mat("accent_light") if acc else mat("metal_brass"), smooth=True)
        elif style == "pots":         # a row of chimney pots, smoking
            for i, q in enumerate(back[1::3][:3]):
                pt, d, up, w = q[:4]
                c = pt - Z * 0.08
                h = (0.46 - 0.06 * i) * size
                pot = g.lathe([(0.16, 0.0), (0.125, h * 0.8), (0.16, h * 0.84), (0.16, h), (0.09, h)], n=8, centre=c)
                _add(r, "pot_%d" % i, pot, [w] * len(pot[0]), mat("clay_dark"), smooth=True)
                band = g.lathe([(0.165, h * 0.84), (0.165, h)], n=8, centre=c, caps=False)
                _add(r, "pot_band_%d" % i, band, [w] * len(band[0]), mat("accent") if acc else mat("clay"), smooth=True)
                p0 = c + Z * h
                sm = _smoke(p0, 0.8 * size, Vector((0, 0.5, 0)), 1.25, n=3)
                _piece("sway", "potsmoke" + "abc"[i], [(sm, mat("smoke_pale"), True)], p0, _bone_of(w))
        elif style == "crumbled":     # a ridge burned down to stubs
            plates(lambda z, t, i: (0.06 + 0.1 * math.sin(i * 2.7) ** 2) * size, mat("ash_fall"), "ridge_ash", lean=0.1, wide=0.7)
        elif style == "lamps":        # every lamp it has kept, hung along its back
            plates(std, m, "ridge")
            for i, q in enumerate(back[1::3][:3]):
                pt, d, up, w = q[:4]
                sd = 1 if i % 2 else -1
                top = pt + Vector((0, 0.08, (0.66 - 0.06 * i) * size))
                arm = top + Vector((0.3 * sd, 0.0, 0.05))
                post = g.tube([pt - Z * 0.05, top, arm], [0.04, 0.035, 0.025], n=5)
                _add(r, "lamppost_%d" % i, post, [w] * len(post[0]), m, smooth=True)
                _piece("sway", "lamp" + "abc"[i], [(geo, mt, not mt.name.startswith("metal")) for geo, mt in gl._lantern(arm, 0.18 * size, "lamp", 3.4)], arm, _bone_of(w))
        elif style == "coins":        # scales like old coin, standing on edge down its back
            geo, geo2, ws, ws2 = None, None, [], []
            for i, (pt, d, up, w, z, t) in enumerate(D):
                if z == "tail" and t > 0.5:
                    continue
                rad = {"neck": 0.1, "back": 0.17 + 0.07 * math.sin(t * math.pi), "tail": 0.15 * (1.0 - t)}[z] * size
                u = d.cross(up).normalized()
                c = pt + up * rad * 0.55
                coin = g.tube([c - u * 0.022, c + u * 0.022], [rad, rad], n=8)
                if i % 2:
                    geo2, ws2 = g.merge(geo2, coin), ws2 + [w] * len(coin[0])
                else:
                    geo, ws = g.merge(geo, coin), ws + [w] * len(coin[0])
            _add(r, "coins", geo, ws, mat("accent_light") if acc else mat("brass_coin"), smooth=False)
            _add(r, "coins_b", geo2, ws2, mat("accent") if acc else mat("brass_coin"), smooth=False)
    return fn


# The shapes its wings may take. From the root at its shoulder: the arm's elbow and wrist; then
# where each finger ends, from the wrist; and where the skin's inner edge meets its flank,
# from the root. Each is (out from the body, back along it, up). move: how the game moves it.
WING_K = 1.3
WINGS = {
    "folded": dict(arm=[(0.14, 0.34, 0.42), (0.2, -0.12, 0.86)], fingers=[(0.05, 0.85, 0.2), (0.1, 1.2, -0.12), (0.13, 1.25, -0.5), (0.1, 0.85, -0.8)], inner=(0.05, 0.8, -0.1), move=None),
    "furled": dict(arm=[(0.12, 0.3, 0.3), (0.18, 0.0, 0.6)], fingers=[(0.05, 0.75, 0.1), (0.1, 1.0, -0.15), (0.12, 0.9, -0.5)], inner=(0.05, 0.7, -0.1), move=None, k=1.0),
    "rampant": dict(arm=[(0.7, -0.1, 0.9), (1.5, -0.35, 1.7)], fingers=[(1.1, -0.3, 1.0), (1.5, 0.7, 0.6), (1.3, 1.6, -0.2), (0.8, 2.0, -1.1), (0.2, 1.7, -1.6)], inner=(0.1, 1.3, -0.3), move="beat"),
    "nubs": dict(k=1.0, arm=[(0.12, 0.14, 0.14), (0.17, 0.36, 0.2)], fingers=[(0.07, 0.28, 0.1), (0.05, 0.36, -0.05), (0.02, 0.26, -0.18)], inner=(0.02, 0.4, -0.05), move=None),
    "half": dict(arm=[(0.34, 0.12, 0.7), (0.56, 0.42, 1.25)], fingers=[(0.62, 0.25, 0.9), (0.56, 1.05, 0.5), (0.34, 1.45, -0.1), (0.1, 1.45, -0.6)], inner=(0.05, 1.1, -0.2), move="glide"),
    "glide": dict(arm=[(0.8, -0.15, 0.75), (1.7, -0.1, 1.35)], fingers=[(1.4, 0.0, 0.8), (1.3, 0.95, 0.35), (0.8, 1.5, -0.1), (0.25, 1.6, -0.6)], inner=(0.1, 1.2, -0.05), move="glide"),
    "mantle": dict(arm=[(0.4, -0.05, 0.9), (0.7, -0.3, 1.75)], fingers=[(0.45, -0.25, 0.85), (0.75, 0.8, 0.55), (0.7, 1.5, -0.2), (0.45, 1.75, -1.0), (0.15, 1.45, -1.5)], inner=(0.1, 1.2, -0.3), move="beat"),
    "stoop": dict(arm=[(0.4, 0.3, 0.45), (0.62, 1.0, 0.76)], fingers=[(0.34, 1.5, 0.45), (0.17, 1.7, 0.1), (0.0, 1.35, -0.3)], inner=(0.05, 1.0, -0.1), move="glide"),
    "shadow": dict(arm=[(1.0, -0.4, 0.8), (2.1, -0.6, 1.35)], fingers=[(1.6, -0.6, 0.6), (1.7, 0.3, 0.1), (1.15, 1.25, -0.3), (0.5, 1.75, -0.6), (0.1, 1.85, -0.7)], inner=(0.1, 1.5, -0.4), move="glide"),
    "banner": dict(arm=[(0.6, 0.1, 0.9), (1.1, 0.4, 1.6)], fingers=[(0.5, 0.4, 1.0), (0.6, 1.5, 0.9), (0.5, 2.5, 0.3), (0.2, 1.6, -0.3)], inner=(0.05, 1.2, -0.2), move="beat"),
    "cloak": dict(arm=[(0.3, 0.05, 0.46), (0.48, 0.35, 0.52)], fingers=[(0.28, 0.3, -0.5), (0.22, 0.85, -0.92), (0.1, 1.45, -1.02), (0.0, 1.95, -0.84)], inner=(0.0, 1.6, -0.2), move="sway"),
    "brake": dict(arm=[(0.45, 0.2, 0.9), (0.85, -0.1, 1.7)], fingers=[(0.6, -0.15, 0.9), (0.8, 0.95, 0.5), (0.6, 1.65, -0.3), (0.2, 1.6, -1.0)], inner=(0.05, 1.1, -0.2), move="beat"),
}


def _wing_root(sg):
    y = _S["ysh"] + 0.12
    s = _at_y(y)
    return _on(s, 90 - sg * 36)[0]


def _wing(sg, root, W, size, skin):
    """One wing from its shoulder: [(geometry, material, shaded round?)]: the arm, the wrist's
    claw, the fingers, and the skin between them (and from the last of them to the flank)."""
    acc = bool(_S["spec"].get("accent"))
    bone_m = kit.mark("wings", mat("hide_wing"))
    size = size * W.get("k", WING_K)
    arm = [V(root)]
    for x, y, z in W["arm"]:
        arm.append(arm[0] + Vector((sg * x, y, z)) * size)
    wrist = arm[-1]
    tips = [wrist + Vector((sg * x, y, z)) * size for x, y, z in W["fingers"]]
    inner = arm[0] + Vector((sg * W["inner"][0], W["inner"][1], W["inner"][2])) * size
    bones = g.tube(arm, [0.12, 0.09, 0.066][:len(arm)], n=6)
    for t in tips:
        mid = wrist.lerp(t, 0.5) + (Z * 0.04 if abs(t.z - wrist.z) < 0.6 * size else Vector((sg * 0.04, 0, 0))) * size
        bones = g.merge(bones, g.tube([wrist, mid, t], [0.046, 0.034, 0.008], n=5))
    claw = g.tube([wrist, wrist + Vector((sg * 0.04, -0.12, 0.1)) * size, wrist + Vector((sg * 0.02, -0.24, 0.04)) * size], [0.04, 0.03, 0.004], n=5)
    edge = tips + [inner]
    base, band, vein = None, None, None
    ragged = skin == "ragged"

    def web(pts):
        n = (pts[1] - pts[0]).cross(pts[-1] - pts[0])
        n = n.normalized() if n.length > 1e-8 else Z.copy()
        return _slab(pts, n, 0.0, 0.014), n
    for k, (a, b) in enumerate(zip(edge, edge[1:])):
        pull = 0.82 if not ragged else (0.58 + 0.22 * (k % 2))
        m1, m2 = a.lerp(b, 0.33), a.lerp(b, 0.67)
        last = k == len(edge) - 2
        hub = arm[1] if last else wrist                 # the last web hangs from the elbow to the flank
        s1, s2 = hub.lerp(m1, pull), hub.lerp(m2, pull)
        sl, nrm = web([hub, a, s1, s2, b])
        base = g.merge(base, sl)
        if last:
            base = g.merge(base, web([arm[1], wrist, a])[0], web([arm[0], arm[1], b])[0])
        if skin in ("barred", "edge", "burn", "shadow"):          # a band across each web, part of the way out
            f0, f1 = (0.5, 0.66) if skin == "barred" else (0.8, 0.94)
            q = [hub.lerp(a, f0), hub.lerp(a, f1), hub.lerp(s1, f1), hub.lerp(s2, f1), hub.lerp(b, f1), hub.lerp(b, f0), hub.lerp(s2, f0), hub.lerp(s1, f0)]
            band = g.merge(band, _slab(q, nrm, 0.012, 0.026))
        elif skin == "eyes" and k < 2:                  # an eye on each of the outer webs
            c = hub.lerp((a + b) / 2, 0.56)
            ux = (a - b).normalized()
            uy = nrm.cross(ux).normalized()
            for rad, lift, which in ((0.26, 0.012, 0), (0.12, 0.022, 1)):
                disc = _slab([c + (ux * math.cos(2 * math.pi * j / 8) + uy * math.sin(2 * math.pi * j / 8)) * rad * size for j in range(8)], nrm, lift, lift + 0.014)
                if which:
                    vein = g.merge(vein, disc)
                else:
                    band = g.merge(band, disc)
    # and the web before the arm, from the shoulder to the wrist
    base = g.merge(base, web([arm[0], arm[0].lerp(wrist, 0.5) + Vector((0, -0.16, 0.0)) * size, wrist, arm[1]])[0])
    if acc:
        mb = {"dark": "accent_dark", "shadow": "accent_dark", "edge": "accent_dark", "pale": "accent_light"}.get(skin, "accent")
        m_base, m_band, m_vein = mat(mb), mat("accent_pale"), mat("accent_deep")
    else:
        m_base, m_band, m_vein = mat("fur_light"), mat("fur_light"), mat("fur_dark")
    items = [(bones, bone_m, True), (claw, mat("drake_claw"), True), (base, m_base, False), (band, m_band, False), (vein, m_vein, False)]
    if skin == "burn":          # wind-burn along the leading edge
        items.append((g.tube([p + Vector((0, -0.03, 0.03)) for p in arm] + [tips[0] + Vector((0, -0.03, 0.03))], [0.06] * (len(arm) + 1), n=4), mat("accent_pale") if acc else mat("fur_pale"), True))
    if skin == "shadow":        # a thread of light along the edge, so that the shadow has a shape
        items.append((g.tube([p + Vector((0, -0.05, 0.02)) for p in arm] + [tips[0] + Vector((0, -0.05, 0.02))], [0.024] * (len(arm) + 1), n=3, caps=False), field("edge", 2.0), True))
    return items


def _wing_folded(r, size, skin):
    """Wings shut along the flank: the wrist at the shoulder, the arm doubled back under it,
    the fingers laid together down the side with the skin pleated between them."""
    acc = bool(_S["spec"].get("accent"))
    bone_m = kit.mark("wings", mat("hide_wing"))
    y0 = _S["ysh"] - 0.1
    L = (_S["yhip"] - _S["ysh"]) * size
    for sg, tag in ((1, "l"), (-1, "r")):
        def at(y, deg, lift, sg=sg):
            return _on(_at_y(y), 90 - sg * deg, lift)[0]
        wrist = at(y0, 30, 0.1)
        elbow = at(y0 + 0.5 * L, 44, 0.08)
        bones = g.merge(g.tube([at(y0 + 0.2, 36, 0.05), elbow, wrist], [0.075, 0.06, 0.055], n=5),
                        g.tube([wrist, wrist + Vector((sg * 0.03, -0.14, 0.08)), wrist + Vector((sg * 0.02, -0.26, 0.0))], [0.04, 0.03, 0.004], n=5))
        webs, wsw, wsb = None, [], []
        wsb = [r.spine_weights(p.y) for p in bones[0]]
        lines = []
        for k, (deg1, reach) in enumerate(((34, 1.18), (54, 1.12), (74, 1.0), (92, 0.82))):
            pts = [wrist]
            for j in range(1, 5):
                f = j / 4.0
                pts.append(at(y0 + reach * L * f, 30 + (deg1 - 30) * f ** 0.7 + 8 * f, 0.05 + 0.03 * math.sin(f * math.pi)))
            lines.append(pts)
            fin = g.tube(pts, [0.036, 0.032, 0.026, 0.018, 0.006], n=4)
            bones = g.merge(bones, fin)
            wsb.extend([r.spine_weights(p.y) for p in fin[0]])
        for la, lb in zip(lines, lines[1:]):
            web = g.loft([[p - (p - _inside(p)).normalized() * 0.022 for p in la], [p - (p - _inside(p)).normalized() * 0.022 for p in lb]], caps=False, closed=False)
            webs = g.merge(webs, web)
            wsw.extend([r.spine_weights(p.y) for p in web[0]])
        _add(r, "wingfold_" + tag, bones, wsb, bone_m, smooth=True)
        mb = {"dark": "accent_dark", "shadow": "accent_deep", "pale": "accent_light"}.get(skin, "accent") if acc else "fur_light"
        _lie(r, "wingweb_" + tag, webs, wsw, mat(mb), smooth=False)


def _drake_wings(style):
    def fn(r, A, size):
        skin = gl.opt(_S["spec"].get("membrane"))[0] or "plain"
        if style == "flat":
            _wing_folded(r, size, skin)
            return
        W = WINGS[style]
        move = gl.opt(_S["spec"].get("flight"))[0] or W["move"]
        for sg, tag in ((1, "l"), (-1, "r")):
            root = _wing_root(sg)
            items = _wing(sg, root, W, size, skin)
            if move in ("beat", "glide", "sway"):
                _piece(move, "wing", items, root, "Torso3", side=tag)
            else:
                for i, (geo, m, sm) in enumerate(items):
                    if geo and geo[0]:
                        _add(r, "wing_%s_%d" % (tag, i), geo, "Torso3", m, smooth=sm)
    return fn


def _drake_throat(style):
    def fn(r, A, size):
        nl = _S["neckline"]          # from the head down

        def under(i, lift=0.0):
            return _on(nl[i], 270, lift)[0]
        if style == "ember":          # a coal under its jaw
            c = under(1, -0.03)
            _piece("pulse", "throat", [(g.ico(c, 0.09 * size, sub=1, scale=(1.0, 1.1, 0.8)), field("ember", 2.4), True)], c, "Neck3")
        elif style == "banked":       # the fire kept in: it shows between the plates down the front of its neck
            geo, ws = None, []
            for i in range(2, min(len(nl) - 2, 9)):
                s = nl[i]
                p, d, u, v, a, b = s[:6]
                arc = []
                for j in range(5):
                    th = math.radians(270 - 50 + 100 * j / 4)
                    arc.append(p + u * (a * math.cos(th) * 1.06) + v * (b * math.sin(th) * 1.06))
                seam = g.tube(arc, [0.02 * size] * 5, n=3, caps=False)
                geo, ws = g.merge(geo, seam), ws + [s[6]] * len(seam[0])
            _add(r, "throat_seams", geo, ws, field("ember", 2.2), smooth=True)
            c = under(1, -0.02)
            _piece("pulse", "throat", [(g.ico(c, 0.12 * size, sub=1, scale=(1.0, 1.2, 0.8)), field("ember", 3.0), True)], c, "Neck3")
        elif style == "lamp":         # a dull shine low on its throat, the colour of a post-flame
            i = len(nl) - 3
            c = under(i, 0.0)
            _piece("pulse", "throat", [(g.ico(c, 0.2 * size, sub=1, scale=(1.0, 0.7, 1.1)), field("lamp", 3.0), True)], c, _bone_of(nl[i][6]))
        elif style == "bulges":       # what it will spit, coming up its throat
            for k, i in enumerate((2, 5, 8)):
                if i >= len(nl) - 1:
                    break
                s = nl[i]
                p, d, u, v, a, b = s[:6]
                rings = [_ring(p - d * 0.12, u, v, a * 1.02, b * 1.02, m=10), _ring(p, u, v, a * 1.26, b * 1.3, m=10), _ring(p + d * 0.12, u, v, a * 1.02, b * 1.02, m=10)]
                bulge = g.loft(rings, caps=False)
                _add(r, "bulge_%d" % k, bulge, [s[6]] * len(bulge[0]), mat("accent_light") if _S["spec"].get("accent") else mat("fur_light"), smooth=True)
                c = _on(s, 270, 0.1 * b)[0]
                _add(r, "bulge_lit_%d" % k, g.ico(c, 0.07 * size, sub=1), [s[6]] * 12, field("ember", 2.6), smooth=True)
    return fn


def _drake_tailend(style):
    def fn(r, A, size):
        p, d, u, v = _S["tail"][-1][:4]
        tip = p
        horn = kit.mark("tailtip", mat("drake_horn"))
        acc = bool(_S["spec"].get("accent"))
        if style == "spade":
            _add(r, "spade", g.blade(tip - d * 0.08, tip + d * 0.42 * size, 0.34 * size, normal=u, belly=0.42, thick=0.035), "Tail8", horn, smooth=False)
        elif style == "club":         # a knot of bone, for knocking
            _add(r, "club", g.ico(tip + d * 0.06, 0.2 * size, sub=1, scale=(0.9, 1.25, 0.9)), "Tail8", horn, smooth=True)
            geo = None
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                dd = u * math.cos(a) + v * math.sin(a)
                geo = g.merge(geo, g.cone(tip + d * 0.06 + dd * 0.12 * size, tip + d * 0.1 + dd * 0.36 * size, 0.05 * size, n=4))
            _add(r, "club_spikes", geo, "Tail8", horn, smooth=True)
        elif style == "hammer":       # a head to it, like a smith's
            c = tip + d * 0.16
            _add(r, "tail_hammer", g.box(c, (0.52 * size, 0.26 * size, 0.26 * size)), "Tail8", mat("metal_iron"))
            _add(r, "tail_hammer_band", g.box(c, (0.15, 0.29 * size, 0.29 * size)), "Tail8", mat("metal_brass"))
        elif style == "rudder":       # a broad fin to steer by
            fin = g.blade(tip - d * 0.6, tip + d * 0.55 * size, 0.7 * size, normal=u, belly=0.55, thick=0.03)
            _add(r, "rudder", fin, "Tail8", mat("accent") if acc else mat("fur_light"), smooth=False)
            _add(r, "rudder_rib", g.tube([tip - d * 0.6, tip + d * 0.55 * size], [0.035, 0.008], n=4), "Tail8", horn, smooth=True)
        elif style == "banner":       # a long pennant
            tip, d, u, v = _S["tail"][-4][:4]
            tip = tip + v * 0.02
            p1, p2, p3 = tip + (d * 0.6 - v * 0.5) * size, tip + (d * 0.5 - v * 1.2) * size, tip + (d * 0.9 - v * 1.9) * size
            pen = g.tongue([tip, p1, p2, p3], [0.45 * size, 0.6 * size, 0.5 * size, 0.06], thick=0.06, normal=u)
            _piece("sway", "pennant", [(pen, mat("accent") if acc else mat("fur_light"), False)], tip, _bone_of(_S["tail"][-4][6]))
        elif style == "lamp":         # a lamp held in the loop of its tail
            top = tip + Vector((0, 0, 0.46 * size))
            _add(r, "taillamp_hook", g.tube([tip - d * 0.1, top], [0.035, 0.022], n=4), "Tail8", horn, smooth=True)
            _piece("sway", "taillamp", [(geo, mt, not mt.name.startswith("metal")) for geo, mt in gl._lantern(top, 0.2 * size, "lamp", 3.6)], top, "Tail8")
    return fn


def drake_shell(r, A, size):
    """A back like a strong-room, with its wheel."""
    back = [s for s in _S["body"] if s[7] == "back"]
    s = back[len(back) // 2]
    c = s[0] + Z * (s[5] * 0.2)
    iron, brass = mat("metal_iron"), mat("metal_brass")
    acc = bool(_S["spec"].get("accent"))
    a, b = s[4] * 1.2 * size, s[5] * 2.1 * size
    Ly = (back[-1][0].y - back[0][0].y) * 0.56 * size
    r.shell("vault", c, (a, Ly, b), "Torso2", mat("slate_light"), segments=12, rings=5)
    for k, dy in enumerate((-0.55, 0.0, 0.55)):
        kk = math.sqrt(max(0.05, 1 - dy * dy))
        band = g.loft([g.ring(c + Vector((0, dy * Ly - 0.05, 0)), a * kk * 1.02, b * kk * 1.02, n=12, u=X, v=Z), g.ring(c + Vector((0, dy * Ly + 0.05, 0)), a * kk * 1.02, b * kk * 1.02, n=12, u=X, v=Z)], caps=False)
        _add(r, "vault_band_%d" % k, band, "Torso2", mat("accent") if acc else brass, smooth=False)
    hub = c + Z * (b * 1.0)
    wheel = _hoop(hub + Z * 0.1, Z, 0.3 * size, 0.035, n=14)
    for k in range(3):
        dv = X * math.cos(k * math.pi / 3) + Y * math.sin(k * math.pi / 3)
        wheel = g.merge(wheel, g.tube([hub + Z * 0.1 - dv * 0.3 * size, hub + Z * 0.1 + dv * 0.3 * size], [0.024, 0.024], n=4))
    _piece("spin", "helm", [(wheel, mat("accent_light") if acc else brass, True), (g.tube([hub - Z * 0.05, hub + Z * 0.14], [0.06, 0.05], n=6), iron, True)], hub, "Torso2")
    _add(r, "vault_seal", g.ico(hub + Z * 0.16, 0.06 * size, sub=1), "Torso2", field("seal", 2.0), smooth=True)


def drake_rubble(r, A, size):
    """What has settled on something that sleeps in old places: stone, dust, and ivy."""
    back = [s for s in _S["body"] if s[7] == "back"]
    for i, (k, deg, sz) in enumerate(((1, 96, 0.3), (3, 74, 0.38), (5, 104, 0.3), (6, 80, 0.26))):
        s = back[min(k, len(back) - 1)]
        c = _on(s, deg, 0.06)[0]
        _add(r, "rubble_%d" % i, g.box(c, (sz * 1.3 * size, sz * size, sz * 0.6 * size), rot=(0.2 * i, 0.3 - 0.2 * i, 0.5 * i)), [s[6]] * 8, mat("slate" if i % 2 else "slate_light"))
    dust, ivy, wd, wi = None, None, [], []
    for i, s in enumerate(_S["body"][3:-6]):
        for sg in (1, -1):
            p, n = _on(s, 90 - sg * (22 + 14 * math.sin(i * 1.3)), 0.03)
            d = s[1]
            fl = g.ico(p, 0.15 * size * (0.8 + 0.3 * math.sin(i * 2.1 + sg)), sub=0, scale=(1.0, 1.3, 0.3))
            dust, wd = g.merge(dust, fl), wd + [s[6]] * len(fl[0])
        if i % 2 == 0 and s[7] == "back":
            sg = 1 if i % 4 else -1
            p, n = _on(s, 90 - sg * 60, 0.02)
            lf = g.blade(p, p + n * 0.1 - Z * 0.4 * size + s[1] * 0.1, 0.22, normal=n, belly=0.45)
            ivy, wi = g.merge(ivy, lf), wi + [s[6]] * 6
    _add(r, "dust", dust, wd, mat("stone_dust"), smooth=True)
    _add(r, "rubble_ivy", ivy, wi, mat("leaf"), smooth=False)


def drake_ashback(r, A, size):
    """Ash lying along its back and its tail, as it lies on a cold hearth."""
    dust, wd = None, []
    for i, s in enumerate(_S["body"][2:-4]):
        for sg in (1, -1):
            p, n = _on(s, 90 - sg * (20 + 16 * math.sin(i * 1.3) + (24 if i % 2 else 0)), 0.02)
            fl = g.ico(p, max(0.08, s[4] * 0.42) * size * (0.8 + 0.3 * math.sin(i * 2.1 + sg)), sub=0, scale=(1.0, 1.4, 0.28))
            dust, wd = g.merge(dust, fl), wd + [s[6]] * len(fl[0])
    _add(r, "ashback", dust, wd, mat("ash_fall"), smooth=True)


def drake_soot(r, A, size):
    """Soot-black along its spine, as if it had been up a flue."""
    geo, ws = None, []
    body = _S["body"]
    for s0, s1 in zip(body[2:-4], body[3:-3]):
        a0 = [_on(s0, deg, 0.016)[0] for deg in (50, 70, 90, 110, 130)]
        a1 = [_on(s1, deg, 0.016)[0] for deg in (50, 70, 90, 110, 130)]
        st = g.loft([a0, a1], caps=False, closed=False)
        geo, ws = g.merge(geo, st), ws + [s0[6]] * 5 + [s1[6]] * 5
    _lie(r, "soot", geo, ws, mat("soot"), smooth=True)


def drake_scars(r, A, size):
    """Healed lines across its hide, paler than the rest of it."""
    geo, ws = None, []
    back = [s for s in _S["body"] if s[7] == "back"]
    for i, (k, deg, L) in enumerate(((1, 40, 0.6), (2, 150, 0.5), (4, 30, 0.7), (5, 140, 0.45), (3, 60, 0.4))):
        s = back[min(k, len(back) - 1)]
        p, n = _on(s, deg, 0.012)
        d = (s[1] + Z * (0.5 if i % 2 else -0.4)).normalized()
        d = (d - n * d.dot(n)).normalized()
        bl = g.blade(p - d * L * size * 0.5, p + d * L * size * 0.5, 0.07, normal=n, belly=0.5, thick=0.014)
        geo, ws = g.merge(geo, bl), ws + [s[6]] * 6
    _add(r, "scars", geo, ws, mat("hide_scar"), smooth=False)


def _drake_jaw(style):
    def fn(r, A, size):
        H = _S["head"]
        P, J, S = H["P"], H["J"], H["S"]
        if style == "drips":          # something bright drips from the corner of its jaw
            for k, (sg, L, y) in enumerate(((1, 0.5, -0.5), (-1, 0.72, -0.4), (-1, 0.36, -0.62))):
                b0 = J(sg * 0.15, y, -0.07)
                drip = g.tube([b0, b0 - Z * L * 0.6 * S * size, b0 - Z * L * S * size], [0.03 * S, 0.02 * S, 0.034 * S], n=5)
                _piece("flick", "drip" + "abc"[k], [(drip, field("ember", 3.4), True)], b0, "Head")
            slag = None
            for k in range(4):
                slag = g.merge(slag, g.ico(J(0.06 * (k - 1.5), H["yt"] + 0.14 + 0.1 * k, -0.1 - 0.02 * (k % 2)), 0.07 * S * size, sub=0, scale=(1.2, 1.0, 0.7)))
            _add(r, "slag", slag, "Head", mat("slag_crust"), smooth=False)
        elif style == "tongue":       # a tongue stained black to the root, like a clerk's finger
            t0 = J(0, H["yt"] + 0.2, -0.045)
            pts = [t0, t0 + Vector((0, -0.2, -0.04)) * S, t0 + Vector((0.03, -0.36, -0.3 * size)) * S, t0 + Vector((0.0, -0.36, -0.72 * size)) * S]
            geo = g.tongue(pts, [0.17 * S, 0.16 * S, 0.13 * S, 0.06 * S], thick=0.3, normal=Y)
            for sg in (1, -1):
                geo = g.merge(geo, g.cone(pts[-1], pts[-1] + Vector((sg * 0.09, -0.02, -0.2 * size)) * S, 0.03 * S, n=4))
            _piece("sway", "tongue", [(geo, mat("tongue_ink"), True)], t0, "Head")
        elif style in ("glaze", "grey"):   # the scales round its mouth cracked and glazed, like the lip of a kiln: a cap of it over the snout (grey: a muzzle gone grey)
            SK, JW = H["SK"], H["JW"]
            ys, yt = H["ys"], H["yt"]
            rings = []
            for y in (ys + 0.04, (ys + H["yn"]) / 2, H["yn"], yt - 0.004):
                _, zt, w, zl = _lerp_table(SK, y)
                k = 1.07
                zm = zl + 0.42 * (zt - zl)
                rings.append([P(-0.9 * w * k, y, zl - 0.004), P(-w * k, y, zm), P(-0.6 * w * k, y, zt * k + 0.002), P(0, y, zt * k + 0.008), P(0.6 * w * k, y, zt * k + 0.002), P(w * k, y, zm), P(0.9 * w * k, y, zl - 0.004)])
            cap = g.loft(rings, caps=False, closed=False)
            n0 = _faces(r)
            _add(r, "glaze", cap, "Head", mat("glaze_kiln") if style == "glaze" else mat("fur_grey"), smooth=style == "grey")
            hb = H["hb"]
            _face_out(r, n0, lambda c: Vector((0, c.y, hb.z)))
            if style == "grey":
                return
            cracks = None
            for k, (y, x0, x1) in enumerate(((ys - 0.05, -0.12, 0.05), (ys - 0.2, 0.02, 0.13), (H["yn"] + 0.1, -0.1, -0.01), (ys - 0.33, -0.05, 0.1))):
                _, zt, w, zl = _lerp_table(SK, y)
                cracks = g.merge(cracks, g.tube([P(x0, y, zt * 1.07 + 0.012), P((x0 + x1) / 2, y - 0.05, zt * 1.07 + 0.014), P(x1, y + 0.02, zt * 1.07 + 0.012)], [0.008 * S] * 3, n=3, caps=False))
            _add(r, "glaze_cracks", cracks, "Head", mat("coal"), smooth=True)
    return fn


def _drake_breath(style):
    def fn(r, A, size):
        H = _S["head"]
        P, J, S = H["P"], H["J"], H["S"]
        m0 = P(0, H["yt"] + 0.04, -0.03)
        if style == "jet":            # narrow and bright, the way a smith wants it
            jet = g.tongue([m0, m0 + Vector((0, -0.5, -0.04)) * S * size, m0 + Vector((0, -1.3, -0.1)) * S * size, m0 + Vector((0, -1.9, -0.12)) * S * size], [0.09 * S, 0.14 * S, 0.09 * S, 0.01], thick=0.8, normal=Z)
            _piece("pulse", "jet", [(jet, field("jet", 3.8), True)], m0, "Head")
        elif style == "beacon":       # a steady flame at the back of its open mouth, in a cage
            c = (P(0, -0.3, -0.06) + J(0, -0.3, -0.06)) / 2
            _piece("pulse", "beacon", [(g.ico(c, 0.14 * S * size, sub=1, scale=(1.0, 1.0, 1.2)), field("flame", 4.0), True)], c, "Head")
            cage = g.merge(_hoop(c, X, 0.19 * S * size, 0.016 * S, n=10), _hoop(c, Y, 0.19 * S * size, 0.016 * S, n=10))
            _add(r, "beacon_cage", cage, "Head", mat("metal_iron"), smooth=True)
        elif style == "cinders":      # it breathes upward and lets the weather do the rest
            top = _S["A"].skull
            sparks, grey = None, None
            for i in range(14):
                c = Vector((0.5 * math.sin(i * 2.3), A.t3.y - 0.6 + 0.3 * i + 0.2 * math.sin(i * 1.3), top + 0.2 + 0.5 * math.sin(i * 1.7) ** 2))
                if i % 3:
                    sparks = g.merge(sparks, g.ico(c, 0.05 * size, sub=0))
                else:
                    grey = g.merge(grey, g.blade(c, c + Vector((0.05, 0.08, -0.16)), 0.1, normal=X, belly=0.5))
            piv = Vector((0, A.t3.y, top + 0.3))
            _piece("bob", "cinders", [(sparks, field("ember", 3.0), False), (grey, mat("ash_fall"), False)], piv, "Torso3")
    return fn


def _drake_nostrils(style):
    def fn(r, A, size):
        H = _S["head"]
        P, S = H["P"], H["S"]
        for sg, tag in ((1, "l"), (-1, "r")):
            p0 = P(sg * 0.08, H["yn"] + 0.005, 0.12)
            if style == "smoke":      # a thread of smoke from each nostril, constant
                sm = _smoke(p0, 1.1 * size, Vector((sg * 0.12, 0.7 * size, 0)), 0.9 * size)
                _piece("sway", "smoke", [(sm, mat("smoke_pale"), True)], p0, "Head", side=tag)
            elif style == "heat":     # a shimmer of heat over its nostrils
                ht = g.tongue([p0, p0 + Vector((0, -0.03, 0.16 * size)), p0 + Vector((0, 0.0, 0.34 * size))], [0.07, 0.065, 0.01], thick=0.8, normal=Y)
                _piece("flick", "heat", [(ht, field("ember", 2.6), True)], p0, "Head", side=tag)
    return fn


def drake_eggshell(r, A, size):
    """Still wearing a piece of the shell nobody found."""
    H = _S["head"]
    S = H["S"]
    c = H["P"](0, -0.08, 0.2)
    cap = g.lathe([(0.02 * S, 0.22 * S), (0.17 * S, 0.17 * S), (0.27 * S, 0.06 * S), (0.285 * S, -0.03 * S), (0.21 * S, -0.012 * S), (0.15 * S, 0.1 * S)], n=7, centre=c)
    _add(r, "eggshell", cap, "Head", mat("eggshell"), smooth=False)


def drake_browplate(r, A, size):
    """A plate across its brow, like a smith's shade."""
    H = _S["head"]
    P, S = H["P"], H["S"]
    geo = g.loft([[P(-0.27, -0.44, 0.19), P(-0.2, -0.46, 0.25), P(0.2, -0.46, 0.25), P(0.27, -0.44, 0.19)],
                  [P(-0.3, -0.1, 0.22), P(-0.2, -0.12, 0.29), P(0.2, -0.12, 0.29), P(0.3, -0.1, 0.22)]], caps=False, closed=False)
    n0 = _faces(r)
    _add(r, "browplate", geo, "Head", mat("metal_iron"), smooth=False)
    hb = H["hb"]
    _face_out(r, n0, lambda c: Vector((0, c.y, hb.z)))
    rv = None
    for sg in (1, -1):
        rv = g.merge(rv, g.ico(P(sg * 0.24, -0.28, 0.255), 0.022 * S, sub=0))
    _add(r, "browplate_rivets", rv, "Head", mat("metal_brass"), smooth=True)


def neck_ledger(r, A, size):
    """The book it keeps, hung under its throat on a strap."""
    nk = _neck(r)
    bone = _neck_band(r, "ledgerstrap", 0.22, mat("leather"))
    c = nk.throat(0.22, 0.02)
    book = g.box(c + Vector((0, -0.02, -0.26 * size)), (0.36 * size, 0.1 * size, 0.42 * size))
    pages = g.box(c + Vector((0, -0.02, -0.26 * size)), (0.31 * size, 0.07 * size, 0.44 * size))
    clasp = g.box(c + Vector((0, -0.075 * size, -0.26 * size)), (0.1 * size, 0.03, 0.08 * size))
    _piece("sway", "ledger", [(book, mat("leather_book"), False), (pages, mat("paper_ledger"), False), (clasp, mat("metal_brass"), False),
                              (g.tube([c, c + Vector((0, -0.02, -0.06 * size))], [0.02, 0.02], n=4), mat("leather"), True)], c, bone)


def drake_ashfeet(r, A, size):
    """Grey to the knee, as if it had walked through a cold hearth."""
    me = r.mesh.data
    names = [m.name for m in me.materials]
    ash = mat("ash_fall")
    if ash.name not in names:
        me.materials.append(ash)
        names.append(ash.name)
    slot = names.index(ash.name)
    skin = {i for i, nm in enumerate(names) if nm.startswith(("fur_", "mark_socks"))}
    wl = r._weights([b for leg in kit.LOWER_LEGS for b in r.family(leg)])
    for p in me.polygons:
        if p.material_index in skin and sum(wl[i] for i in p.vertices) / len(p.vertices) > 0.55:
            p.material_index = slot


def drake_inkfeet(r, A, size):
    """Ink to the wrist, like a clerk's cuffs."""
    me = r.mesh.data
    names = [m.name for m in me.materials]
    ink = mat("tongue_ink")
    if ink.name not in names:
        me.materials.append(ink)
        names.append(ink.name)
    slot = names.index(ink.name)
    skin = {i for i, nm in enumerate(names) if nm.startswith(("fur_", "mark_socks"))}
    wl = r._weights([b for leg in kit.LOWER_LEGS[:2] for b in r.family(leg)])
    for p in me.polygons:
        if p.material_index in skin and sum(wl[i] for i in p.vertices) / len(p.vertices) > 0.55 and (r.M @ p.center).z < 0.3:
            p.material_index = slot


def drake_smokeback(r, A, size):
    """Smoke standing off its back, where another would carry a ridge."""
    back = [q for q in _dorsal(r) if q[4] in ("back", "neck")]
    for k, q in enumerate(back[2::3][:4]):
        pt, d, up, w = q[:4]
        h = (0.7 + 0.2 * math.sin(k * 2.3)) * size
        sm = _smoke(pt, h, d * 0.5, 1.3, n=3)
        _piece("sway", "backsmoke" + "abcd"[k], [(sm, mat("smoke_pale"), True)], pt, _bone_of(w))


def drake_armor(r, A, size):
    """Plates lapped down each shoulder and haunch, cut flat: it is armoured where it is struck."""
    acc = bool(_S["spec"].get("accent"))
    m1, m2 = (mat("accent"), mat("accent_light")) if acc else (_horn_mat(), _horn_mat())
    g1, g2 = None, None
    for tag, foot, bone in gl.FEET:
        sg = 1 if r.bone(foot).x > 0 else -1
        side = ".L" if sg > 0 else ".R"
        if tag[0] == "f":
            top, low = r.bone("FrontUpperLeg" + side), r.bone(bone)
            R, bn = (top - low).length * 0.56, "FrontUpperLeg" + side
        else:
            top, low = r.bone("BackLeg" + side), r.bone("BackUpperLeg" + side)
            R, bn = (top - low).length * 0.7, "BackLeg" + side
        for k, (f, kk) in enumerate(((0.16, 1.0), (0.44, 0.86), (0.7, 0.66))):
            c = top.lerp(low, f) + Vector((sg * (R * 0.46 + 0.02), 0.03, R * 0.1))
            pl = g.ico(c, R * 0.62 * kk * size, sub=1, scale=(0.26, 1.0, 0.72))
            if k % 2:
                g2 = g.merge(g2, pl)
            else:
                g1 = g.merge(g1, pl)
        _add(r, "armor_" + tag, g1, bn, m1, smooth=False)
        _add(r, "armor_b_" + tag, g2, bn, m2, smooth=False)
        g1, g2 = None, None


def _drake_tail_shapes():
    S = gl.SHAPES
    # how it carries its tail (the shapes every one of the wolf's kin has work on it too)
    S[("tail", "drag")] = lambda r, s: _trail(r, (0.4, 0.08, 0.0, 0.0, 0.0, 0.0, 0.02), yaw=[0, 12 * s, 18 * s, 10 * s, -14 * s, -26 * s, -28 * s, -20 * s])
    S[("tail", "sweep")] = lambda r, s: _trail(r, (0.4, 0.08, 0.0, 0.0, 0.0, 0.0, 0.0), yaw=[0, 10 * s, 20 * s, 26 * s, 30 * s, 30 * s, 28 * s, 24 * s])
    S[("tail", "coil")] = lambda r, s: _trail(r, (0.5, 0.2, 0.06, 0.0, 0.0, 0.0, 0.0), yaw=[0, 24 * s, 40 * s, 46 * s, 50 * s, 52 * s, 54 * s, 54 * s])
    S[("tail", "level")] = lambda r, s: _trail(r, (0.96, 0.9, 0.86, 0.9, 1.0, 1.14, 1.3), yaw=[0, 8 * s, 14 * s, 10 * s, -8 * s, -20 * s, -24 * s, -18 * s])
    S[("tail", "high")] = lambda r, s: _trail(r, (1.2, 1.5, 1.8, 2.05, 2.2, 2.2, 2.05), yaw=[0, 6 * s, 10 * s, 6 * s, -8 * s, -16 * s, -16 * s, -10 * s])
    S[("tail", "hook")] = lambda r, s: _trail(r, (1.1, 1.3, 1.6, 2.0, 2.4, 2.6, 2.5))
    S[("tail", "lash")] = lambda r, s: _trail(r, (0.84, 0.66, 0.5, 0.38, 0.3, 0.26, 0.3), yaw=[0, -8 * s, -14 * s, -18 * s, 10 * s, 26 * s, 34 * s, 30 * s])


def _drake_styles():
    G = gl.GROWS
    for st in ("nubs", "swept", "broad", "long", "crown", "brow", "flat", "droop", "lyre", "sights", "ring"):
        G[("horns", st)] = _drake_horns(st)
    for st in ("gate", "herald", "ruff", "crown", "crest", "beard"):
        G[("frill", st)] = _drake_frill(st)
    for st in ("plates", "hoard", "young", "spines", "flame", "sail", "beads", "pots", "crumbled", "lamps", "coins"):
        G[("ridge", st)] = _drake_ridge(st)
    for st in list(WINGS) + ["flat"]:
        G[("wings", st)] = _drake_wings(st)
    for st in ("ember", "banked", "lamp", "bulges"):
        G[("throat", st)] = _drake_throat(st)
    for st in ("spade", "club", "hammer", "rudder", "banner", "lamp"):
        G[("tailend", st)] = _drake_tailend(st)
    G[("plating", "limbs")] = drake_armor
    G[("shell", "vault")] = drake_shell
    G[("lies", "rubble")] = drake_rubble
    G[("lies", "soot")] = drake_soot
    G[("lies", "smoke")] = drake_smokeback
    G[("lies", "ash")] = drake_ashback
    G[("hide", "scars")] = drake_scars
    for st in ("drips", "tongue", "glaze", "grey"):
        G[("jaw", st)] = _drake_jaw(st)
    for st in ("jet", "beacon", "cinders"):
        G[("breath", st)] = _drake_breath(st)
    for st in ("smoke", "heat"):
        G[("nostrils", st)] = _drake_nostrils(st)
    G[("head", "eggshell")] = drake_eggshell
    G[("head", "browplate")] = drake_browplate
    G[("neck", "ledger")] = neck_ledger
    G[("feet", "ash")] = drake_ashfeet
    G[("feet", "ink")] = drake_inkfeet
    _drake_tail_shapes()


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
    # (the Fox is built by lines_fox.py: a fox's body of its own)
    # (the Stag is built by lines_stag.py: a deer's body of its own)
    builders["drake"] = drake_build


# ======================================================================================
# The gifts: what a hybrid wears of these three (docs/genius-lines.md, "Hybrids")
# ======================================================================================
#
# A hybrid's form wears the body of the form it came from and its second base's gift as
# parts. "A tail" and "horns" are any genius's features, so a base's own make of its gift is
# a part of its own, gifts/<base>-<feature>.glb, which the game hangs for that base's gift
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


def _drake_gift(name, items):
    """A gift part of the Drake's: [(geometry, material, shaded round?)] as one object."""
    return [g.join(name, [g.to_object("%s_%d" % (name, i), geo, m, sm) for i, (geo, m, sm) in enumerate(items) if geo and geo[0]])]


def gift_horns_drake():
    """A drake's horns: two swept back and up, two spines at the corner of each jaw, a crown of
    short ones behind the skull, and a coal of the field between them."""
    horns, crown = None, None
    for sg in (1, -1):
        base = Vector((sg * 0.03, 0.0, -0.01))
        horns = g.merge(horns, _horn([base, base + Vector((sg * 0.022, 0.07, 0.075)), base + Vector((sg * 0.04, 0.17, 0.15)), base + Vector((sg * 0.045, 0.27, 0.2)), base + Vector((sg * 0.03, 0.35, 0.21))], 0.026, n=6))
        for k, ln in enumerate((0.1, 0.075)):
            b0 = Vector((sg * 0.052, 0.005, -0.03 - 0.032 * k))
            horns = g.merge(horns, g.cone(b0, b0 + Vector((sg * 0.04, ln, 0.006 - 0.012 * k)), 0.013, n=5))
    for i in range(7):
        a = math.pi * (0.08 + 0.84 * i / 6)
        d = Vector((math.cos(a), 0, math.sin(a)))
        b0 = Vector((d.x * 0.058, 0.055, d.z * 0.05 - 0.03))
        L = 0.085 + 0.045 * math.sin(a)
        crown = g.merge(crown, _horn([b0, b0 + (d * 0.7 + Y * 0.7).normalized() * L * 0.6, b0 + (d * 0.5 + Y * 0.9).normalized() * L], 0.013, n=4, steps=1))
    return _drake_gift("horns", [(horns, mat("drake_horn"), True), (crown, mat("drake_horn"), True), (g.ico((0, 0.012, 0.0), 0.017, sub=1), field("ember", 2.4), True)])


def gift_tail_drake():
    """A drake's tail: thick where it leaves the body and a whip at its end, plates standing
    down its back, plates lapped under it, a spade at the tip."""
    ctrl = [Vector((0, 0.0, 0.0)), Vector((0, 0.12, -0.012)), Vector((0, 0.27, 0.0)), Vector((0, 0.42, 0.045)), Vector((0, 0.55, 0.13)), Vector((0, 0.64, 0.24)), Vector((0, 0.68, 0.34))]
    line = _cr(ctrl, 2)
    fr = _frames(line)
    n = len(fr)
    rings, ridge, under = [], None, None
    for i, (pt, d, u, v) in enumerate(fr):
        t = i / (n - 1.0)
        rad = 0.056 * (1.0 - t) ** 0.85 * (0.78 + 0.22 * (1.0 - t)) + 0.003
        rings.append(_ring(pt, u, v, rad * 0.94, rad, m=8, crest=0.16))
        if 0 < i < n - 2:
            h = 0.075 * (1.0 - t) + 0.014
            ridge = g.merge(ridge, g.blade(pt + v * rad * 0.9, pt + v * (rad + h) + d * h * 0.4, 0.05 * (1.0 - 0.5 * t), normal=u, belly=0.34, thick=0.008))
        if 0 < i < n - 3 and i % 2:
            arc = [pt + u * (rad * 0.94 * math.cos(math.radians(a)) * 1.06) + v * (rad * math.sin(math.radians(a)) * 1.06) for a in (200, 235, 270, 305, 340)]
            arc2 = [q + d * 0.045 * (1.0 - 0.4 * t) + (q - pt) * 0.07 for q in arc]
            under = g.merge(under, g.loft([arc, arc2, [q - (q - pt) * 0.2 for q in arc2]], caps=False, closed=False), g.loft([[q - (q - pt) * 0.08 for q in arc], arc], caps=False, closed=False))
    pt, d, u, v = fr[-1]
    spade = g.blade(pt - d * 0.012, pt + d * 0.13, 0.11, normal=u, belly=0.44, thick=0.012)
    return _drake_gift("tail", [(g.loft(rings, caps=True), mat("drake_hide"), True), (ridge, mat("drake_horn"), False), (under, mat("drake_claw"), False), (spade, mat("drake_horn"), False)])


GIFTS = {"fox-tail": gift_tail_fox, "fox-glow": gift_glow_fox, "stag-horn-brow": gift_horn_brow_stag, "stag-long-legs": gift_long_legs_stag,
         "drake-horns": gift_horns_drake, "drake-tail": gift_tail_drake}


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
