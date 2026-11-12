"""WILDLINE wardrobe: each home's dress (data/bodies.json, dress) built on a body of the body
kit (docs/bodies-plan.md, "Dress as culture"). A home's dress is a silhouette of its own, a
colour chord of its own (two colours and a metal, from the style's ramps) and a signature
piece that says what the home does.

The data is the design. `colors` names each colour by a ramp and a step ("indigo:1.5"), `stuff`
says what each is made of (wool, linen, robe, leather: the game's grain follows the name),
`under` what is painted on the body beneath (a shirt and legs in a colour, or bare), and
`pieces` lists what is worn. A piece may be for one sex (`sex`) and for some of the three
ways of wearing the dress (`in`: plain, formal, master): a first-year's dress is plain, an
Instructor's is the same culture grown rich.

Soft pieces are shells cut on the body's own rings, laid on its surface, folded where they
hang, and given the body's weights; a piece that stands off the body (a cloak, a mantle)
hangs from the trunk; a hard piece (a buckle, a holster, a roll on the back) rides one bone.
Everything a body wears ends as one mesh for each way of wearing it, so a crowd is cheap to
draw. The headgear (one mesh) hangs from the head.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import people_kit as pk
import style

TAGS = ("plain", "formal", "master")
# What the body is dressed in beneath everything else: a piece laid on the body is seated on
# whichever of these is worn with it (seat, below).
GARMENTS = ("tunic", "vest", "jacket", "coat", "robe", "kaftan", "kilt", "wrapskirt", "cuirass", "hakama", "trousers", "apron")
# Pieces seated after everything is cut: a band is let out until it clears the cloth under it,
# a solid thing is moved out until it rests on it.
SEAT_SOFT = ("belt", "sash", "obi", "strap", "wrap", "patch", "collar", "scarf", "furcollar", "beads", "chain", "tabard", "panel")
SEAT_HARD = ("buttons", "badge", "sashknot", "toolloop", "pteruges", "coil", "roll", "disc", "satchel", "bow", "tassel", "brooch", "wings")
# What lies over what: a piece is seated on, and must stay outside, every piece of a lower
# layer worn with it (the fit check reads the same table).
LAYER = {"trousers": 1, "hakama": 1, "boots": 1, "greaves": 1, "sandals": 1, "puttees": 1, "gloves": 1, "shoes": 1,
         "tunic": 2, "jacket": 2, "kilt": 2, "wrapskirt": 2,
         "coat": 2.5, "robe": 2.5, "kaftan": 2.5,
         "cuirass": 3, "vest": 3, "apron": 3, "panel": 3, "tabard": 3, "patch": 3, "wrap": 3,
         "belt": 4, "sash": 4, "obi": 4, "collar": 4, "scarf": 4, "strap": 4, "furcollar": 4.5,
         "mantle": 6, "cloak": 7, "cape": 7}
HARD_LAYER = 5          # buttons, a badge, a holster, a roll, a string of beads: the small things on top
OVER_COAT = 5.5         # a coat worn only sometimes, over the home's everyday dress and all that is on it
LIMBS = ("boots", "greaves", "sandals", "puttees", "gloves", "shoes")       # on a leg or an arm: nothing on the trunk sits on them


def layer_of(D, sex, piece):
    t = piece["type"]
    if piece.get("under"):      # worn beneath the body garment by design (a gun belt under an open coat)
        return 1.5
    if t in ("coat", "robe", "kaftan") and "in" in piece and any(q["type"] in ("tunic", "jacket", "coat", "robe", "kaftan") and "in" not in q for q in pieces_for(D, sex)):
        return OVER_COAT
    return LAYER.get(t, HARD_LAYER)


def worn_together(a, b):
    """Whether two kinds of piece are ever shown at once: the game shows one cloak at a time
    (the creator's cloak replaces the home's cloak and its shoulder cape), and what is slung
    on the back is under a cloak, unseen (world.gd, _dress_home)."""
    for x, y in ((a, b), (b, a)):
        if x == "cape" and y in ("cloak", "mantle", "roll"):
            return False
        if x == "cloak" and y == "roll":
            return False
    return True


# Hard pieces that hang below the hip: they swing with the thigh beside them (weigh, "dangle").
DANGLE = ("sashknot", "toolloop", "pteruges", "coil", "disc", "satchel", "tassel")
METALS = ("metal", "brass", "gold", "bronze", "steel", "iron", "copper")


# ======================================================================================
# The data
# ======================================================================================

WITH_CUT = False        # the fit check may build what is cut from the game, to see whether it fits yet


def pieces_for(D, sex):
    """What one sex wears of a home's dress. A piece marked `cut` (with the reason) is out of
    the game until it fits (docs/dress-fit.md): the cutter is kept, the piece is not built."""
    return [p for p in D.get("pieces", []) if p.get("sex", sex) == sex and (WITH_CUT or not p.get("cut"))]


def headgear_for(D, sex):
    hg = D.get("headgear")
    if not hg:
        return []
    if isinstance(hg, dict):
        hg = [hg]
    return [h for h in hg if h.get("sex", sex) == sex and (WITH_CUT or not h.get("cut"))]


def under_for(D, sex):
    """What is painted on the body beneath the dress: shirt, legs, feet (a colour's name, or bare)."""
    u = dict(D.get("under", {}))
    u.update(u.pop(sex, {}) if isinstance(u.get(sex), dict) else {})
    for s in ("m", "f"):
        u.pop(s, None)
    return u


def goes_bare(D, sex):
    """No shoes: the home goes in sandals, or barefoot."""
    return under_for(D, sex).get("feet") == "bare" or any(p.get("type") == "sandals" for p in pieces_for(D, sex))


def suffix(piece):
    tags = [t for t in TAGS if t in piece.get("in", [])]
    return ("__in_" + "_".join(tags)) if tags and len(tags) < len(TAGS) else ""


def color_of(c):
    """A colour of the data as a Blender colour: "ramp:step" (a step may lie between two), or
    three numbers."""
    if isinstance(c, str):
        name, _, step = c.partition(":")
        s = max(0.0, min(4.0, float(step or 2)))
        lo = int(math.floor(s))
        hi = min(4, lo + 1)
        a, b = style.to_srgb(style.ramp(name, lo)), style.to_srgb(style.ramp(name, hi))
        return tuple(style.to_linear([x + (y - x) * (s - lo) for x, y in zip(a, b)]))
    return tuple(c)


def material_name(home, D, cname):
    stuff = D.get("stuff", {}).get(cname, "")
    return "dress_%s_%s" % (home, cname) + ("_" + stuff if stuff and stuff not in cname else "")


def material(home, D, cname):
    name = material_name(home, D, cname)
    c = color_of(D.get("colors", {}).get(cname, [0.3, 0.3, 0.3]))
    return pk._material(name, tuple(c) + (1,), rough=0.45 if any(w in name for w in METALS) else 0.9)


# ======================================================================================
# Shapes
# ======================================================================================

def _ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _sphere_bm(c, r, seg=10):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(4, seg // 2 + 1), radius=r)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return bm


def _ring_bm(c, r, thick, n=16):
    """A ring in the x-z plane (facing -y) about c: goggles, buckles."""
    pts = [c + Vector((r * math.cos(2 * math.pi * k / n), 0, r * math.sin(2 * math.pi * k / n))) for k in range(n + 1)]
    return pk._tube_bm(pts, [thick] * (n + 1), segments=6)


def _loop_bm(c, u, v, thick, n=20, seg=6):
    """A closed ring through c + u cos + v sin: an armlet, a coil, a fur collar."""
    pts = [c + u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n) for k in range(n + 1)]
    return pk._tube_bm(pts, [thick] * (n + 1), segments=seg)


def _cyl_bm(a, b, r0, r1=None, seg=10):
    """A capped cylinder (or a cone) from a to b."""
    r1 = r0 if r1 is None else r1
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix()
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts)
    bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return bm


def _box(lo, hi, taper=(1.0, 1.0), rot=None, about=None):
    bm = pk._box_bm(Vector(lo), Vector(hi), taper=taper)
    if rot is not None:
        bmesh.ops.rotate(bm, cent=about if about is not None else (Vector(lo) + Vector(hi)) / 2, matrix=rot, verts=bm.verts)
    return bm


def _star_bm(c, r, depth=0.012, points=5):
    """A star lying in the x-z plane, facing -y."""
    bm = bmesh.new()
    vs = []
    for i in range(points * 2):
        a = math.pi / 2 + math.pi * i / points
        rr = r if i % 2 == 0 else r * 0.45
        vs.append(bm.verts.new(c + Vector((rr * math.cos(a), 0, rr * math.sin(a)))))
    f = bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=[f])
    if f.normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=[f])
    bmesh.ops.solidify(bm, geom=[f], thickness=depth)
    return bm


def _ob(name, bm, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    return ob


def _merge(name, bms):
    """Several shapes as one object, the faces of bms[i] in material slot slots[i]."""
    bm = bmesh.new()
    for part, slot in bms:
        tmp = bpy.data.meshes.new("tmp")
        for _ in range(8):
            tmp.materials.append(None)
        for f in part.faces:
            f.material_index = slot
            f.smooth = True
        part.to_mesh(tmp)
        part.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    return _ob(name, bm, smooth=False)


def _arc_panel(name, table, a0, a1, narrow=None, cols=None, trim_rows=()):
    """A sheet over part of the way round the body: `table` is rows of (z, half-width,
    half-depth, y) from the hem up; the arc runs from a0 to a1 degrees (0 the left side, 90
    the back, 270 the front). narrow(t) is the share of the arc a row keeps (t: 0 at the hem,
    1 at the top)."""
    n = cols or max(4, int(round(abs(a1 - a0) / 20.0)))
    bm = bmesh.new()
    rows = []
    m = len(table)
    for i, (z, hw, hd, yo) in enumerate(table):
        s = narrow(i / max(1, m - 1)) if narrow else 1.0
        mid, half = (a0 + a1) / 2.0, (a1 - a0) / 2.0 * s
        row = []
        for j in range(n + 1):
            a = math.radians(mid - half + 2 * half * j / n)
            row.append(bm.verts.new(Vector((hw * math.cos(a), yo + hd * math.sin(a), z))))
        rows.append(row)
    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        for j in range(n):
            f = bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
            f.material_index = 1 if i in trim_rows else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    yo_mid = sum(r[3] for r in table) / m
    if sum(f.normal.dot(Vector((f.calc_center_median().x, f.calc_center_median().y - yo_mid, 0))) for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return _ob(name, bm)


def _slots(ob, mats):
    """A mesh's materials set slot by slot (clearing them would put every face back in the first)."""
    me = ob.data
    while len(me.materials) < len(mats):
        me.materials.append(None)
    for i, m in enumerate(mats):
        me.materials[i] = m
    while len(me.materials) > len(mats):
        me.materials.pop(index=len(me.materials) - 1)


def _thicken(ob, t=0.012):
    """A sheet given its thickness, so its edge and its inside are there to see."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=t)
    bm.to_mesh(ob.data)
    bm.free()
    for poly in ob.data.polygons:
        poly.use_smooth = True


def _line(ob, t=0.012):
    """A shell given an inside: every vertex doubled a cloth's thickness in along its normal,
    and the edge closed. (A solidify scales the offset by the fold of the faces round a vertex,
    and throws a vertex of a shell that has been let out far away.)"""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    verts = bm.verts[:]
    faces = bm.faces[:]
    rim = [(e, e.link_faces[0]) for e in bm.edges if len(e.link_faces) == 1]
    inner = {v: bm.verts.new(v.co - v.normal * t) for v in verts}
    for f in faces:
        nf = bm.faces.new([inner[v] for v in reversed(f.verts)])
        nf.material_index = f.material_index
    for e, f in rim:
        a, b = e.verts
        try:
            q = bm.faces.new((a, b, inner[b], inner[a]))
            q.material_index = f.material_index
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    for poly in ob.data.polygons:
        poly.use_smooth = True


def _folds(ob, z_top, z_hem, amp, n, phase=0.0, yo=0.0, cx=0.0):
    """Folds that open toward the hem: below z_top each vertex is pushed in and out from the
    garment's axis by a wave round it, more the lower it hangs."""
    if amp <= 0.0 or z_top <= z_hem:
        return
    for v in ob.data.vertices:
        p = v.co
        if p.z >= z_top:
            continue
        t = _ease((z_top - p.z) / (z_top - z_hem))
        dx, dy = p.x - cx, p.y - yo
        r = math.hypot(dx, dy)
        if r < 1e-5:
            continue
        d = amp * t * math.sin(n * math.atan2(dy, dx) + phase)
        p.x += dx / r * d
        p.y += dy / r * d


def _cut(ob, keep, edge=None, t=0.012, memo=None):
    """Faces cut out of a garment (an open front, a vent behind), the cloth beside the cut in
    the trim (edge), and the whole given a thickness so the opening has an inside. `memo`
    keeps which faces went on the first build, so every build is cut alike (the builds are
    one mesh's shape keys)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    if memo is not None and "gone" in memo:
        gone = [bm.faces[i] for i in memo["gone"]]
        for i in memo["edge"]:
            bm.faces[i].material_index = 1
    else:
        gone, edged = [], []
        for f in bm.faces:
            c = f.calc_center_median()
            if not keep(c, f.normal):
                gone.append(f)
            elif edge and edge(c, f.normal):
                f.material_index = 1
                edged.append(f.index)
        if memo is not None:
            memo["gone"] = [f.index for f in gone]
            memo["edge"] = edged
    if gone:
        bmesh.ops.delete(bm, geom=gone, context="FACES")
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=t)
    bm.to_mesh(ob.data)
    bm.free()
    for poly in ob.data.polygons:
        poly.use_smooth = True


def _band(ob, where):
    """The faces `where` picks, in the trim: a placket, a crossed front, a border."""
    for poly in ob.data.polygons:
        if where(poly.center, poly.normal):
            poly.material_index = 1


def _seat(ob, under, tr, hard, memo, human, margin=0.008, drape=False):
    """Seat a piece on the cloth beneath it. Each vertex looks outward from the trunk's axis:
    how far under the cloth is it? A band (soft) is let out by that much all round; a solid
    thing (hard) is moved out until only its back is in the cloth. The fit build decides which
    way a solid thing moves; every build measures its own distance."""
    M = ob.matrix_world
    pts = [M @ v.co for v in ob.data.vertices]
    if not pts:
        return
    dirs, deep = [], []
    R = M.to_3x3()
    for i, p in enumerate(pts):
        if drape:       # a shell cut from the body looks out along its own surface's normal
            d = (R @ ob.data.vertices[i].normal).normalized()
        else:
            yo = human._row(tr, p.z)[3]
            d = Vector((p.x, p.y - yo, 0.0))
            d = d.normalized() if d.length > 1e-5 else Vector((0, -1, 0))
        o, far, left = p + d * 1e-4, 0.0, 0.14
        while left > 0.0:
            hit = under.ray_cast(o, d, left)
            if hit[0] is None:
                break
            far += hit[3] + 1e-4
            left -= hit[3] + 1e-4
            o = hit[0] + d * 1e-4
        dirs.append(d)
        deep.append(far)
    if max(deep) <= 0.0:
        return
    Mi = M.inverted()
    if drape:
        # a shell that lies on the body (a cloak's yoke, a shoulder cape): each vertex let out
        # over what is under it there, and its neighbours eased out with it
        off = [x + margin if x > 0.0 else 0.0 for x in deep]
        near = [[] for _ in pts]
        for e in ob.data.edges:
            a, b = e.vertices
            near[a].append(b)
            near[b].append(a)
        need = list(off)
        for _ in range(4):          # spread what one vertex needs to those round it
            off = [max(o, max(off[j] for j in nb) * 0.8) if nb else o for o, nb in zip(off, near)]
        for _ in range(8):          # and even it out, never below what is needed
            off = [max(nd, (o + sum(off[j] for j in nb)) / (len(nb) + 1)) if nb else o for o, nd, nb in zip(off, need, near)]
        for v, p, d, o in zip(ob.data.vertices, pts, dirs, off):
            v.co = Mi @ (p + d * o)
        ob.data.update()
        return
    if hard:
        c = sum(pts, Vector()) / len(pts)
        yo = human._row(tr, c.z)[3]
        d = Vector((c.x, c.y - yo, 0.0))
        d = d.normalized() if d.length > 1e-5 else Vector((0, -1, 0))
        span = max(p.dot(d) for p in pts) - min(p.dot(d) for p in pts)
        move = max(deep) - min(0.016, span * 0.4)
        if move <= 0.0:
            return
        for v, p in zip(ob.data.vertices, pts):
            v.co = Mi @ (p + d * move)
    else:
        under_n = sorted(x for x in deep if x > 0.0)
        if len(under_n) < 0.04 * len(deep):
            return
        move = under_n[int(len(under_n) * 0.9)] + margin
        for v, p, d in zip(ob.data.vertices, pts, dirs):
            v.co = Mi @ (p + d * move)
    ob.data.update()


# ======================================================================================
# The dress
# ======================================================================================

def dress_pieces(body, objs, build, slot):
    """The garments of one build into objs (Dress_<n>_<type>, with __in_<tags> where a piece
    is not always worn); how each is weighted into body.dress_weights."""
    import body_kit as bk
    D = bk.home_dress(body.home)
    if not D:
        return
    sex = body.sex
    home = body.home
    mats = {cname: material(home, D, cname) for cname in D.get("colors", {})}
    tr = body.rings("trunk", build)
    ar = body.rings("arm", build)
    lr = body.rings("leg", build)
    human = body.human
    z_arm = body.joint("upperarm.l", "z")
    y_arm = body.joint("upperarm.l", "y")
    x_sh = body.joint("upperarm.l", "x")
    x_leg = body.joint("upperleg.l", "x")
    top_i = 9
    k = body.k
    if not hasattr(body, "chains"):
        body.chains = {}
    if not hasattr(body, "dress_weights"):
        body.dress_weights = {}
    trunk_bvh = human.bvh("trunk", build)
    n = 0
    sfx = ""
    made = []           # what was cut, for the seating: name, ob, type, tags, hard, layer
    deferred = []       # the shoulder capes and the cloaks: cut last, over everything else
    now = {"type": "", "tags": TAGS, "layer": 0}
    nf = human.normals("fit")
    trf = body.rings("trunk", "fit")
    is_arm = np.asarray(human.is_arm, dtype=bool)
    y_neck = float(human.humans["fit"].joint("joint-neck")[1])
    if not hasattr(body, "dress_memo"):
        body.dress_memo = {}

    def low(z):
        """A height written on a body 2.4 tall with its knee at 0.57 and its hip at 1.11 (a hem), on this body's legs."""
        return human.map_z(z / k)

    def surf(x, z, back=False):
        """The trunk's front (or back) at (x, z), on this build."""
        d = -1.0 if back else 1.0
        hit = trunk_bvh.ray_cast(Vector((x, -2.0 * d, z)), Vector((0, d, 0)))[0]
        return hit.y if hit is not None else None

    def front(x, z, off=0.0, back=False):
        y = None
        for i in range(8):          # past the shoulder's slope the ray misses: look a little lower
            y = surf(x, z - 0.015 * i, back)
            if y is not None:
                break
        if y is None:
            y = tr[3][3] + (tr[3][2] if back else -tr[3][2])
        return y + (off if back else -off)

    def rear(x, z, off=0.0):
        return front(x, z, off, True)

    def put(name, ob, chain, cname, trim=None, fit=True, weights=None, finish=None, third=None):
        name += sfx
        ob.name = name
        base = mats.get(cname, body.mats["tunic"])
        _slots(ob, [base, mats.get(trim, base)] + ([mats.get(third, base)] if third else []))
        objs[name] = ob
        body.chains[name] = chain
        if weights is not None:
            body.dress_weights[name] = weights
        if fit:
            human.refine(ob)
            human.conform(ob, chain, build)
        if finish:
            finish(ob)
        made.append({"name": name, "ob": ob, "type": now["type"], "tags": now["tags"], "layer": now["layer"],
                     "hard": isinstance(weights, str) or (isinstance(weights, tuple) and weights[0] == "dangle")})
        return ob

    def hard(name, bms, bone, cname, trim=None, soft=False):
        """A hard piece of several shapes, each in the main colour (0) or the trim (1), on one
        bone; one that hangs below the hip swings with the thigh beside it; a soft one (a
        string of beads) lies on the body and takes its weights."""
        ob = _merge(name, bms)
        w = None if soft else (("dangle", 0.85) if (bone == "hips" and now["type"] in DANGLE) else bone)
        return put(name, ob, "trunk", cname, trim, fit=False, weights=w)

    def trim_edge(ob, key, below=None, band=0.035):
        """The faces along a shell's lower edge in the trim: chosen on the first build, the
        same faces on the others."""
        memo = body.dress_memo.setdefault(ob.name + key, {})
        if "faces" not in memo:
            zs = [p.center.z for p in ob.data.polygons]
            z0 = min(zs) if below is None else below
            memo["faces"] = [i for i, z in enumerate(zs) if z < z0 + band]
        for i in memo["faces"]:
            ob.data.polygons[i].material_index = 1

    def beneath(hard_too=False, with_body=False):
        """What is worn under the piece being cut (now), as one surface: every piece of a lower
        layer worn with it that lies on the trunk."""
        pts, faces = [], []
        if with_body:
            v = human.humans[build].body()
            fa = human.face_idx
            keep = ~is_arm[fa].all(axis=1)
            pts += [tuple(p) for p in v]
            faces += [tuple(f) for f in fa[keep]]
        for m in made:
            if m["layer"] >= now["layer"] or (m["hard"] and not hard_too) or m["type"] in LIMBS or "_sleeve_" in m["name"]:
                continue
            if not set(m["tags"]) & set(now["tags"]) or not worn_together(now["type"], m["type"]):
                continue
            if m["layer"] == OVER_COAT and now["layer"] < OVER_COAT:
                continue
            gob = m["ob"]
            base_i = len(pts)
            pts += [tuple(gob.matrix_world @ v.co) for v in gob.data.vertices]
            faces += [tuple(base_i + i for i in poly.vertices) for poly in gob.data.polygons]
        return BVHTree.FromPolygons(pts, faces) if faces else None

    def seat_on(ob, margin=0.008, hard=False, drape=False):
        """Seat a piece on what is worn beneath it."""
        under = beneath()
        if under is not None:
            _seat(ob, under, tr, hard, {}, human, margin, drape)

    def mantle(base, piece, cname, trim):
        """A short cape over both shoulders, cut from the body itself: the shoulders, the top
        of the arms, the breast and the back down to its hem, stood off over the dress beneath;
        it moves as the shoulders and the arms under it move."""
        drop = float(piece.get("drop", 0.2)) * k
        clear = float(piece.get("clear", 0.03)) * k
        z_lo = trf[7][0] - drop
        z_nb = trf[9][0] - 0.012 * k

        def mask(v):
            r = np.hypot(v[:, 0], v[:, 1] - y_neck)
            reach = body.joint("upperarm.l", "x") + drop * 0.8          # the arms are level in the body's rest
            return (v[:, 2] > z_lo) & (np.abs(v[:, 0]) < reach) & (v[:, 2] < z_nb + 0.03 * k * np.clip(1.0 - r / (0.12 * k), 0.0, 1.0)) & (nf[:, 2] > -0.2)
        ob = human.shell(base, mask, build, clear)
        put(base, ob, "trunk", cname, trim, fit=False,
            finish=lambda ob: (seat_on(ob, 0.012, drape=True), (trim_edge(ob, "hem", band=0.045 * k) if trim else None), _line(ob, 0.012)))

    def cloak(base, piece, cname, trim, mat=None):
        """A cloak that hangs from the shoulders: a yoke cut from the body's own upper back and
        shoulders (so it lies on them and moves as they move), and under its edge a fall down
        the back that hangs plumb from whatever of the back stands out most, clear of the
        dress beneath, to a hem above the knee; below the hips each side swings with its leg."""
        g_hem = float(piece.get("out", 0.09)) * k
        a0, a1 = piece.get("span", [38, 142])
        z_y = trf[6][0]                      # the yoke's lower edge: under the shoulder blades
        z_nb = trf[9][0] - 0.012 * k
        x_in = body.joint("upperarm.l", "x") + 0.01 * k

        def mask(v):
            back = nf[:, 1] > 0.05
            top = (nf[:, 2] > 0.55) & (v[:, 1] > y_neck - 0.035 * k)
            one = (v[:, 0] > -0.03 * k) if piece.get("side") == "l" else ((v[:, 0] < 0.03 * k) if piece.get("side") == "r" else True)
            return (v[:, 2] > z_y) & (v[:, 2] < z_nb) & (np.abs(v[:, 0]) < x_in) & (back | top) & ~is_arm & one
        dressed = beneath(hard_too=True, with_body=True)
        yoke = human.shell(base + "_0", mask, build, 0.02 * k)
        put(base + "_0", yoke, "trunk", cname, trim, fit=False, finish=lambda ob: (seat_on(ob, 0.014, drape=True), _line(ob, 0.012)))
        if mat is not None:
            _slots(yoke, [mat, mat])
        # the fall: rows from under the yoke's edge to the hem, columns round the back
        hem_z = low(float(piece.get("fall", 0.84)) * k)
        z_top = tr[6][0] + 0.05 * k
        rows_n = 9
        cols_n = 12
        bm = bmesh.new()
        grid = []
        prev = None
        for i in range(rows_n + 1):
            t = i / rows_n
            z = z_top + (hem_z - z_top) * t
            yo = human._row(tr, z)[3]
            c_i = 0.012 * k + (g_hem - 0.012 * k) * _ease(t)
            rs = []
            for j in range(cols_n + 1):
                a = math.radians(a0 + (a1 - a0) * j / cols_n)
                d = Vector((math.cos(a), math.sin(a), 0.0))
                hit = dressed.ray_cast(Vector((0, yo, z)) + d * 2.0, -d)[0]
                r_s = (hit - Vector((0, yo, z))).length if hit is not None else 0.0
                rs.append(r_s + c_i)
            rs = [max(r, (rs[max(0, j - 1)] + rs[min(cols_n, j + 1)]) / 2) for j, r in enumerate(rs)]
            if prev is not None:        # plumb: never back in under what stands out above it
                rs = [max(r, pr[0] - (yo - pr[1]) * math.sin(math.radians(a0 + (a1 - a0) * j / cols_n))) for j, (r, pr) in enumerate(zip(rs, prev))]
            prev = [(r, yo) for r in rs]
            row = []
            for j, r in enumerate(rs):
                a = math.radians(a0 + (a1 - a0) * j / cols_n)
                fold = 0.012 * k * _ease(t) * (1.0 + math.sin(j * math.pi * 6 / cols_n + 0.6)) / 2      # folds that only open outward
                row.append(bm.verts.new(Vector(((r + fold) * math.cos(a), yo + (r + fold) * math.sin(a), z))))
            grid.append(row)
        border = float(piece.get("border", 0.05)) * k
        for i in range(rows_n):
            for j in range(cols_n):
                f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
                f.material_index = 1 if (trim and grid[i + 1][j].co.z < hem_z + border - 1e-4) else 0
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if sum(f.normal.y for f in bm.faces) < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        fall = _ob(base + "_1", bm)
        put(base + "_1", fall, "trunk", cname, trim, fit=False, finish=lambda ob: _thicken(ob, 0.012),
            weights=("cloak", float(piece.get("swing", 0.6)), z_top))
        if mat is not None:
            _slots(fall, [mat, mat])

    def band_loft(name, rings, trim_rings=()):
        return bk.loft(name, rings, (lambda i: 1 if i in trim_rings else 0))

    def hem_rings(top, hem, flare, piece, lip=True):
        """The rings of a skirt from its hem up to (not with) `top`, and which bands are trim:
        a border at the hem (a broad band, or with band2 a broad band and a line above it)."""
        z2, hw2, hd2, yo2 = top
        back = float(piece.get("train", 0.0))

        def at(z):
            t = (z2 - z) / max(1e-6, z2 - hem)
            f = 1.0 + (flare - 1.0) * t
            return (z, hw2 * f, hd2 * f, yo2 + back * t * t)
        steps = int(piece.get("steps", 4))
        zs = [z2 + (hem - z2) * i / steps for i in range(1, steps + 1)]
        trims = set()
        border = []
        if piece.get("trim"):
            b = float(piece.get("border", 0.07)) * k
            border = [hem + b]
            if piece.get("band2"):
                border += [hem + b + 0.03 * k, hem + b + 0.05 * k]
            zs = [z for z in zs if z > border[-1] + 0.03 * k] + border + [hem]
        zs = sorted(set(zs))
        rings = [at(z) for z in zs]
        if piece.get("trim"):
            trims.add(0)
            if piece.get("band2"):
                trims.add(2)
        if lip:
            z0, hw0, hd0, yo0 = rings[0]
            rings = [(z0 + 0.012, hw0 - 0.03, hd0 - 0.03, yo0)] + rings
            trims = {i + 1 for i in trims} | ({0} if piece.get("trim") else set())
        return rings, trims

    def sleeves(kk, cname, piece, trim=None):
        kk = min(6, int(kk))
        if kk <= 0:
            return
        bell = float(piece.get("bell", 0.04 if piece.get("wide") else 0.0))
        cuffs, roll = piece.get("cuffs"), piece.get("roll")
        from_i = int(piece.get("bellFrom", 1))
        for side, sign in (("l", 1), ("r", -1)):
            rings = []
            for i, (x, hd, hz) in enumerate(ar[:kk + 1]):
                g = 0.02 + bell * _ease(max(0.0, (i - from_i) / max(1.0, kk - from_i))) ** 1.5
                rings.append((x, hd + g, hz + g))
            x_e, hd_e, hz_e = rings[-1]
            tb = ()
            if roll:        # the sleeve turned back in a thick roll
                rings += [(x_e + 0.004, hd_e + 0.022, hz_e + 0.022), (x_e + 0.05, hd_e + 0.022, hz_e + 0.022), (x_e + 0.054, hd_e - 0.012, hz_e - 0.012)]
                tb = (len(rings) - 4, len(rings) - 3, len(rings) - 2)
            elif cuffs or trim or bell > 0.0:
                w = 0.05 if bell > 0.05 else 0.03
                rings += [(x_e + w, hd_e + 0.006, hz_e + 0.006), (x_e + w, max(0.02, hd_e - 0.03), max(0.02, hz_e - 0.03))]
                tb = (len(rings) - 3, len(rings) - 2) if (cuffs or trim) else ()
            ob = band_loft("Dress_%d_sleeve_%s" % (n, side), bk.rings_x(rings, z_arm, sign, y_arm), tb)
            put("Dress_%d_sleeve_%s" % (n, side), ob, "arm." + side, cname, roll or cuffs or trim)

    def strip(bm, path, w, behind, off):
        """A band laid on the trunk along `path` (points (x, z)), w wide, standing `off` from the
        body before it (or behind it): three vertices across, each on the body's own surface."""
        rows = []
        for i, (x, z) in enumerate(path):
            ax, az = path[max(0, i - 1)]
            bx, bz = path[min(len(path) - 1, i + 1)]
            ln = math.hypot(bx - ax, bz - az) or 1.0
            nx, nz = -(bz - az) / ln, (bx - ax) / ln
            row = []
            for j in (-1, 0, 1):
                px, pz = x + nx * j * w / 2, z + nz * j * w / 2
                y = surf(px, pz, behind)
                if y is None:
                    y = surf(x, z, behind)
                if y is None:
                    y = (tr[3][3] + tr[3][2]) if behind else (tr[3][3] - tr[3][2])
                row.append(bm.verts.new(Vector((px, y + (off if behind else -off), pz))))
            rows.append(row)
        faces = []
        for a, b in zip(rows, rows[1:]):
            for j in range(2):
                faces.append(bm.faces.new((a[j], a[j + 1], b[j + 1], b[j])))
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        if (sum(f.normal.y for f in faces) > 0) != behind:
            bmesh.ops.reverse_faces(bm, faces=faces)

    def trunk_weights(share):
        """Weights for cloth that hangs from the trunk: share(p) of the body's own under it."""
        return ("hang", share)

    for piece in pieces_for(D, sex):
        n += 1
        t, cname = piece["type"], piece["color"]
        trim = piece.get("trim")
        sfx = suffix(piece)
        now = {"type": t, "tags": tuple(piece.get("in", TAGS)), "layer": layer_of(D, sex, piece)}
        hem = low(float(piece.get("hem", 0.5)) * k)
        z_waist = tr[3][0]
        z_neck = tr[9][0]
        if t in ("tunic", "vest", "jacket", "coat", "robe", "kaftan"):
            long = t in ("coat", "robe", "kaftan") or "hem" in piece
            lo = int(piece.get("lo", {"tunic": 1, "vest": 1, "jacket": 3}.get(t, 2)))
            grow = float(piece.get("grow", 0.026 if long else 0.024))
            top = bk._shell(tr, grow, lo, top_i)
            trims = set()
            rings = list(top)
            if long:
                flare = float(piece.get("flare", {"coat": 1.25, "robe": 1.15, "kaftan": 1.3}.get(t, 1.12)))
                skirt, trims = hem_rings(top[0], hem, flare, piece)
                rings = skirt + top
            elif trim:
                trims = {0}
            collar = piece.get("collar")
            if collar:      # a standing collar (stand), or one turned up to the jaw (high)
                z9, hw9, hd9, yo9 = rings[-1]
                up = (0.06 if collar == "stand" else 0.11) * k
                out = 0.0 if collar == "stand" else 0.025
                z10, hw10, hd10, yo10 = tr[10]
                rings.append((z9 + up, hw10 + grow + out, hd10 * 0.8 + grow + out, yo10 * 0.5 + yo9 * 0.5))
                trims.add(len(rings) - 2)
            nm = "Dress_%d_%s" % (n, t)
            ob = band_loft(nm, bk.rings_z(rings), trims)
            z_open = {"chest": tr[5][0], "neck": z_neck + 0.2}.get(piece.get("openTo", "waist"), z_waist)
            open_w = float(piece.get("open", 0.0))
            vent = float(piece.get("vent", 0.0))
            frontband = piece.get("front")
            yo_w = tr[3][3]

            def finish(ob, long=long, hem=hem, open_w=open_w, vent=vent, z_open=z_open, frontband=frontband, piece=piece, z_waist=z_waist, z_neck=z_neck, yo_w=yo_w, top=top):
                if long:
                    _folds(ob, top[0][0] + 0.04, hem, float(piece.get("folds", 0.014)), int(piece.get("pleats", 7)), 0.6, yo_w)
                if frontband == "placket":
                    _band(ob, lambda c, nr: nr.y < -0.2 and abs(c.x) < 0.03)
                if open_w > 0.0 or vent > 0.0:
                    def gap(z):
                        return open_w * (0.25 + 0.75 * _ease((z_open - z) / max(1e-6, z_open - hem)))

                    def keep(c, nr):
                        if open_w > 0.0 and c.y < yo_w and c.z < z_open and abs(c.x) < gap(c.z):
                            return False
                        if vent > 0.0 and c.y > yo_w and c.z < z_waist - 0.12 and abs(c.x) < vent * _ease((z_waist - 0.12 - c.z) / max(1e-6, z_waist - 0.12 - hem)):
                            return False
                        return True
                    if not hasattr(body, "dress_cuts"):
                        body.dress_cuts = {}
                    _cut(ob, keep, None,
                         memo=body.dress_cuts.setdefault(ob.name, {}))
            put(nm, ob, "trunk", cname, trim, finish=finish)
            if frontband == "cross":
                cb = bmesh.new()
                strip(cb, [(0.1 - 0.25 * (i / 8.0), (z_neck - 0.02) * (1 - i / 8.0) + z_waist * (i / 8.0)) for i in range(9)], 0.055, False, grow + 0.016)
                bmesh.ops.solidify(cb, geom=cb.faces[:], thickness=0.01)
                put(nm + "_cross", _ob(nm + "_cross", cb), "trunk", trim or cname, fit=False)
            if t != "vest":
                sleeves(piece.get("sleeves", 6 if long else 2), cname, piece, trim if piece.get("cuffTrim", True) else None)
        elif t in ("kilt", "wrapskirt"):
            ring_i = int(piece.get("from", 1))
            z2, hw2, hd2, yo2 = tr[ring_i]
            flare = float(piece.get("flare", 1.2))
            stripes = piece.get("stripes")
            nm = "Dress_%d_%s" % (n, t)
            above = bk._shell(tr, 0.022, ring_i, ring_i + 1)[1:] if piece.get("band") else []
            if stripes:
                rings = bk._skirt(z2, hw2 + 0.016, hd2 + 0.016, yo2, hem, flare, steps=6)[::-1]
                ob = bk.loft(nm, bk.rings_z(rings), (lambda i: i % 2))
            else:
                skirt, trims = hem_rings((z2, hw2 + 0.016, hd2 + 0.016, yo2), hem, flare, piece)
                rings = skirt + [(z2, hw2 + 0.016, hd2 + 0.016, yo2)] + above
                if above and piece.get("band"):
                    trims.add(len(rings) - 2)
                ob = band_loft(nm, bk.rings_z(rings), trims)
            put(nm, ob, "trunk", cname, stripes or trim or piece.get("band"),
                finish=lambda ob, z2=z2, hem=hem, piece=piece, yo2=yo2: _folds(ob, z2, hem, float(piece.get("folds", 0.014)), int(piece.get("pleats", 8)), 0.3, yo2))
        elif t == "cuirass":
            lo = int(piece.get("lo", 4))
            rings = bk._shell(tr, 0.03, lo, top_i)
            # a waist that turns out, like a breastplate's lower edge
            z0, hw0, hd0, yo0 = rings[0]
            rings = [(z0 - 0.03, hw0 + 0.022, hd0 + 0.022, yo0)] + rings
            ob = band_loft("Dress_%d_cuirass" % n, bk.rings_z(rings), (0,) if trim else ())
            put("Dress_%d_cuirass" % n, ob, "trunk", cname, trim)
        elif t == "apron":
            # A bib over the chest and a skirt to the shin: the front of a coat's shell, cut at the sides.
            bib = piece.get("bib", True)
            top = bk._shell(tr, 0.036, 2, 6 if bib else 3)
            z2, hw2, hd2, yo2 = top[0]
            skirt = bk._skirt(z2, hw2, hd2, yo2, low(float(piece.get("hem", 0.6)) * k), 1.08)
            table = skirt[::-1][:-1] + top
            m = len(table)
            wi = len(skirt) - 1
            ob = _arc_panel("Dress_%d_apron" % n, table, 270 - 70, 270 + 70,
                            narrow=(lambda u, m=m, wi=wi: 1.0 if u * (m - 1) <= wi else 1.0 - 0.45 * min(1.0, (u * (m - 1) - wi) / 2.0)))
            put("Dress_%d_apron" % n, ob, "trunk", cname, trim, finish=lambda ob: _thicken(ob, 0.014))
        elif t in ("cloak", "mantle"):
            deferred.append((t, "Dress_%d_%s" % (n, t), piece, cname, trim, sfx, now))
        elif t in ("panel", "tabard"):
            # A sheet over part of the body: a cloak behind, a tabard before and behind, a loincloth's front.
            arcs = {"cloak": [[piece.get("arc", [15, 165])]], "tabard": [[[236, 304]], [[56, 124]]]}.get(t, [[piece.get("arc", [240, 300])]])
            top_ring = int(piece.get("top", 8))
            bot_ring = int(piece.get("bottom", 2))
            g = piece.get("grow", [0.035, 0.1] if t == "cloak" else [0.04, 0.045])
            g = g if isinstance(g, list) else [g, g]
            flare = float(piece.get("flare", 1.18 if t == "cloak" else 1.05))
            part = bk._shell(tr, 0.0, min(bot_ring, top_ring), top_i)[: top_ring - min(bot_ring, top_ring) + 1]
            m0 = len(part)
            part = [(z, hw + g[1] + (g[0] - g[1]) * (i / max(1, m0 - 1)), hd + g[1] + (g[0] - g[1]) * (i / max(1, m0 - 1)), yo) for i, (z, hw, hd, yo) in enumerate(part)]
            z2, hw2, hd2, yo2 = part[0]
            table = part
            trims = ()
            if hem < z2 - 0.02:
                skirt, tset = hem_rings(part[0], hem, flare, piece, lip=False)
                table = skirt + part
                trims = tuple(tset)
            nar = piece.get("narrow")
            for ai, arc in enumerate(arcs):
                a0, a1 = arc[0]
                nm = "Dress_%d_%s_%d" % (n, t, ai)
                ob = _arc_panel(nm, table, a0, a1, trim_rows=trims,
                                narrow=(lambda u, nar=nar: 1.0 + (float(nar) - 1.0) * u) if nar else None)

                def finish(ob, z2=z2, hem=hem, piece=piece, yo2=yo2, t=t):
                    _folds(ob, z2 + (0.3 if t == "cloak" else 0.0), hem, float(piece.get("folds", 0.02 if t == "cloak" else 0.008)), int(piece.get("pleats", 9)), 1.1, yo2)
                    _thicken(ob, 0.012)
                put(nm, ob, "trunk", cname, trim, finish=finish, weights=trunk_weights(float(piece.get("follow", 0.35))) if t == "cloak" else None)
        elif t in ("hakama", "trousers"):
            cut = piece.get("cut", "wide" if t == "hakama" else "loose")
            prof = {"wide": [0.03, 0.05, 0.09, 0.12, 0.15, 0.17],
                    "baggy": [0.03, 0.07, 0.11, 0.12, 0.11, 0.08, 0.012],
                    "jodhpur": [0.03, 0.075, 0.085, 0.02],
                    "loose": [0.025, 0.03, 0.035, 0.035, 0.035, 0.035, 0.03]}[cut]
            for side, sign in (("l", 1), ("r", -1)):
                rings = [(z, hw + prof[i], hd + prof[i]) for i, (z, hw, hd) in enumerate(lr[:len(prof)])]
                tb = ()
                if cut == "wide":
                    z5, hw5, hd5 = rings[-1]
                    rings.append((low(0.2 * k), hw5 + 0.02, hd5 + 0.02))
                    rings.append((low(0.2 * k) + 0.012, hw5 - 0.02, hd5 - 0.02))
                elif cut == "baggy":
                    z6, hw6, hd6 = rings[-1]
                    rings.append((z6 - 0.04, hw6, hd6))
                    tb = (len(rings) - 2,) if trim else ()
                nm = "Dress_%d_%s_%s" % (n, t, side)
                ob = band_loft(nm, [(Vector((sign * x_leg, 0, 0)) + c, u, v) for c, u, v in bk.rings_z(rings)], tb)
                put(nm, ob, "leg." + side, cname, trim,
                    finish=(lambda ob, sign=sign: _folds(ob, lr[0][0], lr[5][0], 0.012, 8, 0.0, 0.0, sign * x_leg)) if cut == "wide" else None)
        elif t in ("greaves", "boots", "sandals", "puttees"):
            for side, sign in (("l", 1), ("r", -1)):
                lo_i = int(piece.get("top", {"sandals": 5, "puttees": 3}.get(t, 4)))
                rings = [(z, hw + 0.012, hd + 0.012) for z, hw, hd in lr[lo_i:]]
                if t == "puttees":      # wound bands: more of them than the leg has rings
                    za, zb = lr[lo_i][0], lr[-1][0]
                    rings = [(lambda r: (r[0], r[1] + 0.012, r[2] + 0.012))(human._row(lr, za + (zb - za) * i / 8.0)) for i in range(9)]
                cuffs = piece.get("cuffs")
                banded = t == "boots" and bool(trim or cuffs)
                tb = ()
                if banded:
                    z_top, hw_t, hd_t = rings[0]
                    fl = float(piece.get("flare", 0.01))
                    rings = [(z_top + 0.07 * k, hw_t + fl, hd_t + fl), (z_top, hw_t + fl * 0.6 + 0.004, hd_t + fl * 0.6 + 0.004)] + rings
                    tb = (0,)
                nm = "Dress_%d_%s_%s" % (n, t, side)
                table = [(Vector((sign * x_leg, 0, 0)) + c, u, v) for c, u, v in bk.rings_z(rings)]
                ob = bk.loft(nm, table, (lambda i: i % 2)) if t == "puttees" else band_loft(nm, table, tb)
                put(nm, ob, "leg." + side, cname, trim or cuffs)
        elif t in ("belt", "sash", "obi"):
            at = piece.get("at", 3)
            z2, hw2, hd2, yo2 = tr[int(at)] if float(at) == int(at) else tuple(a + (b - a) * (float(at) % 1.0) for a, b in zip(tr[int(at)], tr[int(at) + 1]))
            h = float(piece.get("height", {"belt": 0.03, "sash": 0.07, "obi": 0.09}[t]))
            tilt = float(piece.get("tilt", 0.0))
            stripes = piece.get("stripes")
            rings = [(Vector((0, yo2, z2 - h + (2 * h) * i / 4.0)), Vector((hw2 + 0.02, 0, tilt)), Vector((0, hd2 + 0.02, 0))) for i in range(5)]
            ob = bk.loft("Dress_%d_%s" % (n, t), rings, (lambda i: i % 2) if stripes else ((lambda i: 1 if i in (0, 3) else 0) if trim else None))
            put("Dress_%d_%s" % (n, t), ob, "trunk", cname, stripes or trim)
        elif t == "collar":
            w = piece.get("wide", 1.0)
            wide = (1.8 if w else 1.0) if isinstance(w, bool) else float(w)
            # cut from the body: a band at the neck's base, out over the shoulders when it is broad
            z2, hw2 = body.rings("trunk", "fit")[9][:2]      # the cut is the fit body's, on every build
            ob = human.shell("Dress_%d_collar" % n, human.neck_mask(z2 - 0.045 * wide * k, z2 + 0.03 * k, hw2 + 0.035 * k + 0.11 * (wide - 1) * k), build, 0.014 * k)
            put("Dress_%d_collar" % n, ob, "trunk", cname, fit=False)
        elif t == "scarf":
            zf, hwf = body.rings("trunk", "fit")[9][:2]
            ring = human.shell("Dress_%d_scarf" % n, human.neck_mask(zf - 0.05 * k, zf + 0.035 * k, hwf + 0.05 * k), build, 0.02 * k)
            put("Dress_%d_scarf" % n, ring, "trunk", cname, fit=False)
            z9 = tr[9][0]
            # the ends: bands laid on the body (down the back over one shoulder, or down the breast)
            behind = piece.get("tails", "front") == "back"
            tb = bmesh.new()
            for dx, ln in (((-0.07, 0.5), (0.03, 0.4)) if behind else ((0.055, 0.3),)):
                z_a = z9 - 0.03 * k
                path = [(dx, z_a - ln * k * i / 6.0) for i in range(7)]
                strip(tb, path, 0.085 if behind else 0.075, behind, 0.02)
            bmesh.ops.solidify(tb, geom=tb.faces[:], thickness=0.012)
            put("Dress_%d_scarf_tail" % n, _ob("Dress_%d_scarf_tail" % n, tb), "trunk", cname, fit=False)
        elif t in ("wrap", "strap"):
            # A band laid on the body from one shoulder to the other hip, before and (back) behind:
            # a cloth across the chest, a satchel's strap, a harness.
            w = float(piece.get("width", 0.12 if t == "wrap" else 0.045))
            sides = [1.0, -1.0] if piece.get("cross") else [-1.0 if piece.get("flip") else 1.0]
            z_hi, z_lo = tr[8][0] - 0.02, tr[int(piece.get("to", 2))][0]
            off = float(piece.get("off", 0.014))
            bm = bmesh.new()
            for sgn in sides:
                path = [(sgn * (0.13 * (1 - i / 10.0) - (tr[2][1] - 0.035) * (i / 10.0)), z_hi * (1 - i / 10.0) + z_lo * (i / 10.0)) for i in range(11)]
                for behind in ([False, True] if piece.get("back", True) else [False]):
                    strip(bm, path, w, behind, off)
            bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012)
            ob = _ob("Dress_%d_%s" % (n, t), bm)
            put("Dress_%d_%s" % (n, t), ob, "trunk", cname, fit=False)
        elif t == "patch":
            # A square of needlework on the breast and the back, its middle in a second value.
            sz = float(piece.get("size", 0.2))
            poff = float(piece.get("off", 0.014))
            zc = tr[5][0] + 0.03
            bm = bmesh.new()
            g = 5
            for behind in (False, True):
                grid = []
                for i in range(g + 1):
                    row = []
                    for j in range(g + 1):
                        px, pz = -sz / 2 + sz * j / g, zc - sz / 2 + sz * i / g
                        y = surf(px, pz, behind)
                        y = y if y is not None else 0.0
                        row.append(bm.verts.new(Vector((px, y + (poff if behind else -poff), pz))))
                    grid.append(row)
                for i in range(g):
                    for j in range(g):
                        f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
                        f.material_index = 0 if (0 < i < g - 1 and 0 < j < g - 1) else 1
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            for f in bm.faces:
                c = f.calc_center_median()
                if (f.normal.y > 0) != (c.y > tr[5][3]):
                    f.normal_flip()
            bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.008)
            ob = _ob("Dress_%d_patch" % n, bm)
            put("Dress_%d_patch" % n, ob, "trunk", cname, trim, fit=False)
        elif t == "gloves":
            x_w = body.joint("wrist.l", "x")
            fl = float(piece.get("flare", 0.0))
            for side, sign in (("l", 1), ("r", -1)):
                rings = [(x_w - 0.03, 0.045, 0.04), (x_w + 0.03, 0.05, 0.03), (x_w + 0.13, 0.055, 0.028), (x_w + 0.18, 0.035, 0.02)]
                tb = ()
                if fl > 0.0:      # a gauntlet's cuff up the forearm
                    rings = [(x_w - 0.17, 0.05 + fl, 0.05 + fl), (x_w - 0.165, 0.062 + fl, 0.062 + fl), (x_w - 0.03, 0.05, 0.045)] + rings
                    tb = (0, 1)
                ob = band_loft("Dress_%d_glove_%s" % (n, side), bk.rings_x(rings, z_arm, sign, y_arm), tb)
                put("Dress_%d_glove_%s" % (n, side), ob, "arm." + side, cname, trim)
        # --- hard pieces, each on one bone ---
        elif t == "buttons":
            z_top, z_bot = tr[7][0], tr[int(piece.get("to", 3))][0]
            count = int(piece.get("count", 5))
            bms = {"chest": [], "spine": []}
            for xo in ((-0.055, 0.055) if int(piece.get("rows", 1)) == 2 else (0.0,)):
                for i in range(count):
                    u = i / max(1, count - 1)
                    z = z_top * (1 - u) + z_bot * u
                    bms["chest" if u < 0.5 else "spine"].append((_sphere_bm(Vector((xo, front(xo, z, 0.03), z)), 0.016, 8), 0))
            for bone, parts in bms.items():
                if parts:
                    hard("Dress_%d_buttons_%s" % (n, bone), parts, bone, cname)
        elif t == "badge":
            x, z2 = float(piece.get("x", 0.09)), tr[6][0]
            if piece.get("shape") == "star":
                bm = _star_bm(Vector((x, front(x, z2, 0.034), z2)), 0.045)
            else:
                bm = _cyl_bm(Vector((x, front(x, z2, 0.04), z2)), Vector((x, front(x, z2, 0.026), z2)), 0.03, seg=12)
            hard("Dress_%d_badge" % n, [(bm, 0)], "chest", cname)
        elif t == "sashknot":
            z2, hw2, hd2, yo2 = tr[int(piece.get("at", 3))]
            ln = float(piece.get("length", 0.3)) * k
            side = piece.get("side", "l")
            bms = []
            if side in ("l", "r"):
                sg = 1.0 if side == "l" else -1.0
                bms.append((_box((sg * hw2 - 0.035, yo2 - 0.035, z2 - 0.035), (sg * hw2 + 0.045, yo2 + 0.045, z2 + 0.04)), 0))
                for i, dx in enumerate((0.0, 0.04)):
                    x0 = sg * (hw2 + dx)
                    bms.append((_box((x0 - 0.018, yo2 - 0.02 + 0.03 * i, z2 - ln - 0.07 * i), (x0 + 0.018, yo2 + 0.02 + 0.03 * i, z2 - 0.02), taper=(1.3, 1.6)), 1 if (trim and i) else 0))
            else:       # in front (the ends hang down the middle) or behind
                yf = front(0.0, z2, 0.03) if side == "front" else rear(0.0, z2, 0.03)
                d = -1.0 if side == "front" else 1.0
                bms.append((_box((-0.05, yf - 0.03, z2 - 0.04), (0.05, yf + 0.03, z2 + 0.04)), 0))
                for i, dx in enumerate((-0.035, 0.035)):
                    bms.append((_box((dx - 0.03, yf + d * 0.005 - 0.012, z2 - ln - 0.06 * i), (dx + 0.03, yf + d * 0.005 + 0.012, z2), taper=(1.25, 1.0)), 1 if (trim and i) else 0))
            hard("Dress_%d_knot" % n, bms, "hips", cname, trim)
        elif t == "toolloop":
            z2, hw2, hd2, yo2 = tr[3]
            x0 = -hw2 - 0.03
            bms = [(_cyl_bm(Vector((x0, yo2 - 0.02, z2 - 0.24)), Vector((x0, yo2 - 0.02, z2 + 0.02)), 0.012), 0),
                   (_box((x0 - 0.028, yo2 - 0.07, z2 - 0.3), (x0 + 0.028, yo2 + 0.03, z2 - 0.23)), 1),
                   (_box((x0 - 0.008, yo2 + 0.04, z2 - 0.2), (x0 + 0.012, yo2 + 0.075, z2)), 1)]
            hard("Dress_%d_tools" % n, bms, "hips", cname, trim)
        elif t == "pauldrons":
            layers = int(piece.get("layers", 1))
            for side, sign in (("l", 1), ("r", -1)):
                if piece.get("side", side) != side:
                    continue
                bms = []
                for i in range(layers):
                    bm = bmesh.new()
                    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.125 - 0.012 * i)
                    bmesh.ops.scale(bm, vec=(1.0, 0.95, 0.7), verts=bm.verts)
                    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, -0.01), plane_no=(0, 0, 1), clear_inner=True)
                    bmesh.ops.translate(bm, vec=Vector((sign * (x_sh + 0.05 + 0.05 * i), y_arm, z_arm + 0.035 - 0.03 * i)), verts=bm.verts)
                    bms.append((bm, 1 if (trim and i % 2) else 0))
                hard("Dress_%d_pauldron_%s" % (n, side), bms, "upperarm." + side, cname, trim)
        elif t == "pteruges":
            z2, hw2, hd2, yo2 = tr[2]
            count = int(piece.get("count", 10))
            ln = float(piece.get("length", 0.3)) * k
            bms = []
            for i in range(count):
                a = 2 * math.pi * (i + 0.5) / count
                cx, cy = (hw2 + 0.03) * math.cos(a), (hd2 + 0.03) * math.sin(a) + yo2
                rot = Matrix.Rotation(math.atan2(math.cos(a), -math.sin(a)) + math.pi / 2, 3, "Z")
                bm = _box((-0.03, -0.007, -ln), (0.03, 0.007, 0.0), taper=(0.9, 1.0), rot=rot, about=Vector((0, 0, 0)))
                bmesh.ops.translate(bm, vec=Vector((cx, cy, z2 + 0.02)), verts=bm.verts)
                bms.append((bm, 0))
                if trim:
                    stud = _sphere_bm(Vector((cx * 1.03, (cy - yo2) * 1.03 + yo2, z2 + 0.02 - ln + 0.04)), 0.014, 6)
                    bms.append((stud, 1))
            hard("Dress_%d_pteruges" % n, bms, "hips", cname, trim)
        elif t == "holster":
            # a gun on the thigh: the holster, the grip above it, the strap round the leg
            z1 = lr[1][0]
            x0 = -(tr[1][1] + 0.035)
            bms = [(_box((x0 - 0.03, -0.055, z1 - 0.3), (x0 + 0.03, 0.045, z1 - 0.02), taper=(0.7, 0.6)), 0),
                   (_box((x0 - 0.018, -0.02, z1 - 0.03), (x0 + 0.018, 0.035, z1 + 0.09), rot=Matrix.Rotation(-0.35, 3, "X")), 1),
                   (_loop_bm(Vector((-x_leg, 0.0, z1 - 0.2)), Vector((lr[1][1] + 0.02, 0, 0)), Vector((0, lr[1][2] + 0.02, 0)), 0.012), 0)]
            hard("Dress_%d_holster" % n, bms, "upperleg.r", cname, trim)
        elif t == "coil":
            # a coiled line at the hip
            z2, hw2, hd2, yo2 = tr[2]
            x0 = hw2 + 0.04
            bms = [(_loop_bm(Vector((x0 + 0.012 * i, yo2 + 0.01 * i, z2 - 0.12)), Vector((0, 0.085, 0)), Vector((0, 0, 0.11)), 0.02, n=14, seg=5), 0) for i in range(3)]
            bms.append((_box((x0 - 0.02, yo2 - 0.02, z2 - 0.03), (x0 + 0.04, yo2 + 0.03, z2 + 0.05)), 1))
            hard("Dress_%d_coil" % n, bms, "hips", cname, trim)
        elif t == "roll":
            # a roll slung across the back: a tool roll, a bedroll, a case of scrolls, a quiver
            z_hi, z_lo = tr[7][0] + 0.03, tr[int(piece.get("to", 4))][0]
            r = float(piece.get("radius", 0.055))
            sg = -1.0 if piece.get("flip") else 1.0
            yb = rear(0.0, (z_hi + z_lo) / 2, r + 0.02)
            a, b = Vector((sg * 0.2, yb, z_hi)), Vector((-sg * 0.19, yb, z_lo))
            bms = [(_cyl_bm(b, a, r, r * float(piece.get("taper", 1.0)), seg=12), 0)]
            for u in (0.12, 0.88):
                p = b + (a - b) * u
                bms.append((_cyl_bm(p - (a - b).normalized() * 0.02, p + (a - b).normalized() * 0.02, r + 0.008, seg=12), 1))
            if piece.get("arrows"):
                d = (a - b).normalized()
                for i in range(4):
                    off = Vector((0.022 * (i % 2 * 2 - 1), 0.02 * (i // 2 * 2 - 1), 0))
                    bms.append((_cyl_bm(a + off, a + off + d * 0.16, 0.006, seg=5), 1))
                    bms.append((_box(a + off + d * 0.1 - Vector((0.014, 0.003, 0.03)), a + off + d * 0.1 + Vector((0.014, 0.003, 0.04))), 0))
            hard("Dress_%d_roll" % n, bms, "chest", cname, trim)
        elif t == "armlets":
            bms = {"l": [], "r": []}
            for at_i in piece.get("at", [2]):
                x, hd, hz = ar[int(at_i)]
                for side, sign in (("l", 1), ("r", -1)):
                    bms[side].append((_loop_bm(Vector((sign * x, y_arm, z_arm)), Vector((0, hd + 0.012, 0)), Vector((0, 0, hz + 0.012)), 0.014, n=16, seg=6), 0))
            for side in ("l", "r"):
                hard("Dress_%d_armlet_%s" % (n, side), bms[side], ("upperarm." if max(piece.get("at", [2])) <= 3 else "lowerarm.") + side, cname)
        elif t in ("beads", "chain"):
            # a string of beads, or a chain of office with its medal, from the neck to the breast
            z_hi, z_lo = tr[8][0] + 0.02, tr[int(piece.get("to", 5))][0] + 0.03
            hw = tr[8][1] * float(piece.get("spread", 0.75))
            count = int(piece.get("count", 16))
            pts = []
            for i in range(count + 1):
                a = math.pi * i / count            # from one shoulder round the front to the other
                x = hw * math.cos(a)
                z = z_hi - (z_hi - z_lo) * math.sin(a) ** 1.3
                pts.append(Vector((x, front(x, z, 0.022), z)))
            bms = []
            if t == "beads":
                for i, p in enumerate(pts):
                    bms.append((_sphere_bm(p, 0.017 if i != count // 2 else 0.026, 6), 1 if (trim and i == count // 2) else 0))
            else:
                bms.append((pk._tube_bm(pts, [0.013] * len(pts), segments=5), 0))
                mid = pts[count // 2]
                bms.append((_cyl_bm(mid + Vector((0, -0.012, -0.03)), mid + Vector((0, 0.004, -0.03)), 0.042, seg=12), 1 if trim else 0))
            # and behind the neck
            back = [Vector((hw * math.cos(math.pi * i / 6), rear(hw * math.cos(math.pi * i / 6) * 0.8, z_hi, 0.02), z_hi + 0.03 * math.sin(math.pi * i / 6))) for i in range(7)]
            bms.append((pk._tube_bm(back, [0.011] * 7, segments=5), 0))
            hard("Dress_%d_%s" % (n, t), bms, "chest", cname, trim, soft=True)
        elif t == "disc":
            # an instrument hung from the belt: a brass disc with its rule (an astrolabe), on a chain
            z2, hw2, hd2, yo2 = tr[2]
            x, zc = float(piece.get("x", -0.12)), z2 - 0.13
            y = front(x, z2, 0.045)
            bms = [(_cyl_bm(Vector((x, y - 0.006, zc)), Vector((x, y + 0.008, zc)), 0.065, seg=14), 0),
                   (_ring_bm(Vector((x, y - 0.01, zc)), 0.05, 0.007, n=14), 1),
                   (_box((x - 0.05, y - 0.016, zc - 0.006), (x + 0.05, y - 0.008, zc + 0.006), rot=Matrix.Rotation(0.6, 3, "Y")), 1),
                   (_cyl_bm(Vector((x, y, zc + 0.06)), Vector((x, y + 0.01, z2 + 0.04)), 0.006, seg=5), 1)]
            hard("Dress_%d_disc" % n, bms, "hips", cname, trim)
        elif t == "satchel":
            z2, hw2, hd2, yo2 = tr[2]
            sg = -1.0 if piece.get("flip") else 1.0
            x0 = -sg * (hw2 + 0.045)
            bms = [(_box((x0 - 0.045, yo2 - 0.1, z2 - 0.2), (x0 + 0.045, yo2 + 0.1, z2 - 0.02)), 0),
                   (_box((x0 - 0.05, yo2 - 0.105, z2 - 0.1), (x0 + 0.05, yo2 + 0.105, z2 - 0.01)), 1)]
            if piece.get("scroll"):
                bms.append((_cyl_bm(Vector((x0, yo2 - 0.13, z2 + 0.0)), Vector((x0, yo2 + 0.13, z2 + 0.0)), 0.028, seg=8), 1))
            hard("Dress_%d_satchel" % n, bms, "hips", cname, trim)
        elif t == "bow":
            # the sash tied behind in a great flat bow
            z2, hw2, hd2, yo2 = tr[3]
            yb = rear(0.0, z2, 0.02)
            bms = [(_box((-0.14, yb, z2 - 0.08), (0.14, yb + 0.075, z2 + 0.1)), 0),
                   (_box((-0.045, yb + 0.01, z2 - 0.1), (0.045, yb + 0.09, z2 + 0.12)), 1 if trim else 0)]
            if piece.get("tails", True):
                for dx in (-0.06, 0.06):
                    bms.append((_box((dx - 0.04, yb + 0.01, z2 - 0.34), (dx + 0.04, yb + 0.035, z2 - 0.06), taper=(1.2, 1.0)), 0))
            hard("Dress_%d_bow" % n, bms, "spine", cname, trim)
        elif t == "tassel":
            z2, hw2, hd2, yo2 = tr[3]
            x = float(piece.get("x", 0.1))
            y = front(x, z2 - 0.05, 0.04)
            bms = [(_ring_bm(Vector((x, y, z2 - 0.1)), 0.03, 0.01, n=12), 0),
                   (_cyl_bm(Vector((x, y, z2 - 0.34)), Vector((x, y, z2 - 0.13)), 0.02, 0.008, seg=8), 1),
                   (_cyl_bm(Vector((x, y, z2 - 0.07)), Vector((x, y, z2)), 0.005, seg=5), 1)]
            hard("Dress_%d_tassel" % n, bms, "hips", cname, trim)
        elif t == "furcollar":
            # a thick roll of fleece or fur laid round the neck, out on the shoulders
            z8, hw8, hd8, yo8 = tr[8]
            r = float(piece.get("radius", 0.05))
            # cut from the body round the neck's base and out on the shoulders, and stood well off: a
            # roll of fleece that lies on them (it was a stiff ring that hung in the air round the neck)
            zf, hwf = trf[9][:2]
            ob = human.shell("Dress_%d_furcollar" % n, human.neck_mask(zf - 0.075 * k, zf + 0.02 * k, hwf + 0.085 * k), build, r * 0.7 * k)
            put("Dress_%d_furcollar" % n, ob, "trunk", cname, fit=False)
        elif t == "wings":
            # stiff shoulders that stand out past the arms, and the two bands down to the sash
            z7 = tr[7][0]
            reach = float(piece.get("reach", 0.14))
            bms = []
            zt, zb = z7 + 0.075, tr[3][0] + 0.03
            for sign in (1, -1):
                for behind in (False, True):
                    y = (rear(0.0, tr[6][0], 0.045) if behind else front(0.0, tr[6][0], 0.05))
                    bm = bmesh.new()
                    vs = [bm.verts.new(Vector((sign * 0.045, y, zt))), bm.verts.new(Vector((sign * (x_sh + reach), y + (0.03 if not behind else -0.03), z7 + 0.06))),
                          bm.verts.new(Vector((sign * (x_sh + reach * 0.5), y, z7 - 0.14))), bm.verts.new(Vector((sign * 0.07, y, zb))), bm.verts.new(Vector((sign * 0.02, y, zb)))]
                    f = bm.faces.new(vs)
                    bmesh.ops.solidify(bm, geom=[f], thickness=0.016)
                    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
                    bms.append((bm, 0))
                # and the ridge over the shoulder that joins them
                yf, yb = front(0.0, tr[6][0], 0.05), rear(0.0, tr[6][0], 0.045)
                bms.append((_box((min(sign * 0.045, sign * (x_sh + reach)), yf + 0.02, z7 + 0.05), (max(sign * 0.045, sign * (x_sh + reach)), yb - 0.02, z7 + 0.07),
                                 rot=Matrix.Rotation(-sign * 0.06, 3, "Y")), 0))
            hard("Dress_%d_wings" % n, bms, "chest", cname, trim)
        elif t == "brooch":
            x, z = float(piece.get("x", 0.14)), tr[8][0] - 0.03
            hard("Dress_%d_brooch" % n, [(_sphere_bm(Vector((x, front(x, z, 0.012), z)), 0.03, 8), 0)], "chest", cname, soft=True)
    sfx = ""

    # --- seated: every band and every solid thing on what is worn under it, the lowest first --
    for m in sorted(made, key=lambda m: (m["layer"], m["hard"])):
        if m["type"] not in SEAT_SOFT and m["type"] not in SEAT_HARD:
            continue
        now = {"type": m["type"], "tags": m["tags"], "layer": m["layer"]}
        seat_on(m["ob"], hard=m["type"] in SEAT_HARD)

    # --- then the shoulder capes and the cloaks, over all of it -----------------------------
    for t, base, piece, cname, trim, sfx, now in sorted(deferred, key=lambda d: d[0] != "mantle"):
        (mantle if t == "mantle" else cloak)(base, piece, cname, trim)
    # and the cloak the creator offers every body (look.cape), in the colour the look names
    sfx = ""
    now = {"type": "cape", "tags": ("plain", "formal"), "layer": LAYER["cape"]}
    cloak("Dress_99_cape", {"type": "cloak"}, None, None, mat=pk._material("cape", (0.5, 0.42, 0.36, 1), rough=0.95))

    # --- shoes: over the feet unless the home goes in sandals or barefoot ---------------
    if not goes_bare(D, sex):
        cname = next((p["color"] for p in pieces_for(D, sex) if p.get("type") in ("boots", "greaves")), under_for(D, sex).get("shoes"))
        for name, ob in human.shoes(build, mats.get(cname, body.mats["boots"])).items():
            objs[name] = ob
            body.chains[name] = "leg." + name[-1]


def join_dress(body, objs):
    """Every piece of one way of wearing the dress as one mesh (Dress_all, and Dress_some__in_<tags>
    for what is not always worn); body.dress_ranges remembers which vertices want which weights."""
    groups = {}
    for name in sorted(n for n in objs if n.startswith("Dress_")):
        tag = name[name.index("__in_"):] if "__in_" in name else ""
        # a cloak, a shoulder cape and the creator's cloak are meshes of their own: the game
        # shows one at a time (a cloak over a shoulder cape, or two cloaks, do not fit)
        own = next((w for w in ("cape", "cloak", "mantle", "roll") if name.split("_")[2] == w), "")
        groups.setdefault((tag, own), []).append(name)
    body.dress_ranges = {}
    body.dress_spans = {}       # every piece's vertices in the joined mesh, for the fit check (fit_check.py)
    for (tag, own), names in groups.items():
        joined = "Cape" if own == "cape" else (("Dress_" + own + tag) if own else ("Dress_some" + tag if tag else "Dress_all"))
        mats = []
        bm = bmesh.new()
        ranges = []
        spans = []
        for name in names:
            ob = objs.pop(name)
            me = ob.data
            me.transform(ob.matrix_world)
            remap = []
            for m in me.materials:
                if m not in mats:
                    mats.append(m)
                remap.append(mats.index(m))
            for poly in me.polygons:
                poly.material_index = remap[poly.material_index] if poly.material_index < len(remap) else 0
            start = len(bm.verts)
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            w = getattr(body, "dress_weights", {}).get(name)
            if w is not None:
                ranges.append((start, len(bm.verts), w))
            spans.append((name, start, len(bm.verts), body.chains.get(name, "trunk")))
            bpy.data.objects.remove(ob)
            body.chains.pop(name, None)
        me = bpy.data.meshes.new(joined)
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(joined, me)
        bpy.context.collection.objects.link(ob)
        objs[joined] = ob
        body.chains[joined] = "trunk"
        body.dress_ranges[joined] = ranges
        body.dress_spans[joined] = spans


def weigh(body, name, ob):
    """After a dress mesh has the body's weights: the vertices of what hangs from the trunk
    (a cloak, a mantle) or rides one bone (a buckle, a roll) are weighted again."""
    import body_kit as bk
    ranges = getattr(body, "dress_ranges", {}).get(name, [])
    if not ranges:
        return
    k = body.k
    trunk = ["hips", "spine", "chest"]
    zj = [body.joint(b, "z") for b in trunk]
    x_sh = body.joint("upperarm.l", "x")
    verts = ob.data.vertices

    def group(bone):
        return ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    for start, end, w in ranges:
        idx = list(range(start, end))
        if isinstance(w, str):          # one bone
            for g in ob.vertex_groups:
                g.remove(idx)
            group(w).add(idx, 1.0, "REPLACE")
            continue
        kind, share = w[0], w[1]
        z_hip = body.joint("upperleg.l", "z")
        for i in idx:
            p = verts[i].co
            mine = {ob.vertex_groups[g.group].name: g.weight for g in verts[i].groups}
            for g in ob.vertex_groups:
                g.remove([i])
            hang = bk._chain_weights(p.z, zj, trunk, bk.BLENDS["trunk"][:2])
            if kind == "dangle":
                # on the hips, and below the hip more and more the thigh beside it
                s = share * bk._s01((z_hip + 0.02 * k - p.z) / (0.2 * k))
                wl = max(0.0, min(1.0, 0.5 + p.x / (0.12 * k)))
                out = {"hips": 1.0 - s, "upperleg.l": s * wl, "upperleg.r": s * (1.0 - wl)}
            elif kind == "cloak":
                # under the yoke the body's own (it lies on the back); then the trunk's; below
                # the hips each side takes a share of its leg, so a stride swings it clear
                top = 1.0 - bk._s01((w[2] - p.z) / (0.14 * k))
                s = share * bk._s01((z_hip + 0.06 * k - p.z) / (0.3 * k))
                wl = max(0.0, min(1.0, 0.5 + p.x / (0.16 * k)))
                out = bk._mix(hang, mine, top)
                out = bk._mix(out, {"upperleg.l": wl, "upperleg.r": 1.0 - wl}, s)
            elif kind == "mantle":
                # on the chest, and past the shoulder's joint a share of the arm that lifts it
                side = "l" if p.x > 0 else "r"
                s = share * bk._s01((abs(p.x) - (x_sh - 0.06)) / 0.1)
                out = {"chest": 1.0 - s, "upperarm." + side: s}
            else:
                # the trunk's, with a share of whatever of the body lies under it (a leg that pushes it)
                s = share * bk._s01((zj[0] + 0.1 * k - p.z) / (0.5 * k))
                out = bk._mix(hang, mine, s)
            total = sum(out.values()) or 1.0
            for b, wt in out.items():
                if wt > 1e-4:
                    group(b).add([i], wt / total, "REPLACE")


# ======================================================================================
# What is worn on the head
# ======================================================================================

def headgear(body):
    """The home's headgear, hung from the head bone: one mesh for each, Headgear_<type> (with
    __in_<tags> where it is not always worn)."""
    import body_kit as bk
    D = bk.home_dress(body.home)
    out = []
    for hg in headgear_for(D, body.sex):
        out.append(_headgear(body, D, hg))
    return out


def _headgear(body, D, hg):
    (x0, x1), (y0, y1), (z0, z1) = body.head_extents()
    hw, hd, hh = (x1 - x0) / 2, (y1 - y0) / 2, z1 - z0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c = Vector((cx, cy, z0 + hh * 0.62))
    home = body.home
    metal = hg.get("metal", "metal")
    names = [hg["color"]] + [n for n in (hg.get("trim"), hg.get("third"), metal if hg.get("jewel") or hg.get("goggles") else None) if n]
    names = list(dict.fromkeys(n for n in names if n in D.get("colors", {}) or n == hg["color"]))
    slot = {n: i for i, n in enumerate(names)}
    M = slot[hg["color"]]
    T = slot.get(hg.get("trim"), M)
    J = slot.get(metal, slot.get(hg.get("third"), T))
    t = hg["type"]
    parts = []

    def ring(z, rx, ry, thick, s, seg=8):
        return (_loop_bm(Vector((cx, cy, z)), Vector((rx, 0, 0)), Vector((0, ry, 0)), thick, n=24, seg=seg), s)

    def dome(centre, rx, ry, rz, cut_z, tilt, s):
        return (pk._cap_bm(centre, rx, ry, rz, cut_z, tilt), s)

    if t == "cap":
        parts.append(dome(c, hw * 1.12, hd * 1.1, hh * 0.46, z0 + hh * 0.72, 0.1, M))
        if hg.get("peak", False):
            parts.append((_box((cx - hw * 0.8, y0 - 0.08, z0 + hh * 0.7), (cx + hw * 0.8, y0 + 0.02, z0 + hh * 0.72), taper=(0.6, 1.0)), T))
        if hg.get("roll", False):       # a knit cap's turned-up edge
            parts.append(ring(z0 + hh * 0.74, hw * 1.12, hd * 1.1, 0.022, T))
    elif t == "hat":
        brim = float(hg.get("brim", 1.9))
        parts.append(dome(Vector((cx, cy, c.z + hh * 0.05)), hw * 1.1, hd * 1.08, hh * 0.55, z0 + hh * 0.7, 0.0, M))
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=hw * brim, radius2=hw * brim * 0.96, depth=0.014)
        bmesh.ops.scale(bm, vec=(1.0, max(1.0, hd / hw), 1.0), verts=bm.verts)
        for v in bm.verts:      # the brim curls up at the sides
            v.co.z += 0.5 * (v.co.x / (hw * brim)) ** 2 * 0.07
        bmesh.ops.translate(bm, vec=Vector((cx, cy, z0 + hh * 0.7)), verts=bm.verts)
        parts.append((bm, M))
        parts.append(ring(z0 + hh * 0.76, hw * 1.11, hd * 1.09, 0.014, T))
    elif t == "kasa":
        # the broad shallow cone of straw
        r = hw * float(hg.get("brim", 2.6))
        parts.append((_cyl_bm(Vector((cx, cy, z0 + hh * 0.72)), Vector((cx, cy, z1 + 0.07)), r, 0.01, seg=20), M))
        parts.append(ring(z0 + hh * 0.72, r, r, 0.01, T, seg=5))
    elif t == "turban":
        big = float(hg.get("size", 1.0))
        for i, (r, dz) in enumerate(((1.25, 0.7), (1.3, 0.82), (1.14, 0.94))):
            parts.append(ring(z0 + hh * dz, hw * r * 0.9 * big, hd * r * 0.9 * big, hw * 0.32 * big, M if i != 1 else T))
        parts.append(dome(Vector((cx, cy, c.z + hh * 0.1)), hw * 1.05 * big, hd * 1.02 * big, hh * 0.47, z0 + hh * 0.9, 0.0, M))
        if hg.get("jewel", False):
            parts.append((_sphere_bm(Vector((cx, y0 - hw * 0.3 * big, z0 + hh * 0.84)), 0.024), J))
        if hg.get("tail", False):       # the end of the cloth, down behind one shoulder
            parts.append((_box((cx + 0.02, y1 - 0.02, z0 - hh * 0.55), (cx + 0.1, y1 + 0.012, z0 + hh * 0.7), taper=(1.3, 1.0)), M))
    elif t == "tagelmust":
        # the wound cloth of the desert road: high on the head, round under the chin, an end behind
        for i, (r, dz) in enumerate(((1.2, 0.72), (1.26, 0.84), (1.16, 0.96), (0.95, 1.05))):
            parts.append(ring(z0 + hh * dz, hw * r * 0.9, hd * r * 0.9, hw * 0.3, M if i != 2 else T))
        parts.append(dome(Vector((cx, cy, c.z + hh * 0.14)), hw * 1.0, hd * 1.0, hh * 0.45, z0 + hh * 0.9, 0.0, M))
        parts.append((_loop_bm(Vector((cx, cy + hd * 0.1, z0 + hh * 0.34)), Vector((hw * 1.16, 0, 0)), Vector((0, hd * 0.5, hh * 0.44)), hw * 0.2, n=20, seg=6), M))
        parts.append((_box((cx - 0.09, y1 - 0.03, z0 - hh * 0.75), (cx + 0.0, y1 + 0.0, z0 + hh * 0.6), taper=(1.4, 1.0)), M))
    elif t == "gele":
        # the head-tie: a tall flare of stiff cloth, knotted in front
        parts.append(dome(c, hw * 1.12, hd * 1.1, hh * 0.44, z0 + hh * 0.7, 0.15, M))
        bm = _cyl_bm(Vector((cx, cy + hd * 0.1, z0 + hh * 0.78)), Vector((cx, cy + hd * 0.25, z1 + hh * 0.42)), hw * 1.1, hw * 1.95, seg=14)
        bmesh.ops.scale(bm, vec=(1.0, 0.8, 1.0), space=Matrix.Translation((0, -cy, 0)), verts=bm.verts)
        parts.append((bm, M))
        parts.append((_box((cx - 0.07, y0 - 0.03, z0 + hh * 0.76), (cx + 0.07, y0 + 0.04, z0 + hh * 0.98)), T))
    elif t == "furhat":
        tall = float(hg.get("tall", 0.62))
        parts.append(dome(Vector((cx, cy, c.z + hh * 0.22)), hw * 1.22, hd * 1.16, hh * tall, z0 + hh * 0.66, 0.0, T if hg.get("crown") else M))
        parts.append(ring(z0 + hh * 0.72, hw * 1.3, hd * 1.24, 0.05, M))
        if hg.get("point", False):
            parts.append((_cyl_bm(Vector((cx, cy, z1 + hh * 0.1)), Vector((cx, cy, z1 + hh * 0.5)), hw * 0.75, 0.012, seg=10), T if hg.get("crown") else M))
        if hg.get("flaps", False):
            for sg in (1, -1):
                parts.append((_box((cx + sg * hw * 1.02 - 0.02, cy - 0.06, z0 + hh * 0.2), (cx + sg * hw * 1.02 + 0.03, cy + 0.07, z0 + hh * 0.72), taper=(0.7, 0.8)), M))
            parts.append((_box((cx - hw, y1 - 0.01, z0 + hh * 0.15), (cx + hw, y1 + 0.04, z0 + hh * 0.72), taper=(0.8, 1.0)), M))
    elif t == "scholarcap":
        parts.append(dome(c, hw * 1.1, hd * 1.08, hh * 0.42, z0 + hh * 0.74, 0.0, M))
        parts.append((_box((cx - hw * 1.25, cy - hd * 1.05, z1 - 0.012), (cx + hw * 1.25, cy + hd * 1.05, z1 + 0.012)), T))
    elif t == "wingcap":
        # the examiner's black cap: a low crown before, a tall block behind, and two long wings
        parts.append(dome(c, hw * 1.1, hd * 1.08, hh * 0.42, z0 + hh * 0.74, 0.0, M))
        parts.append((_box((cx - hw * 0.8, cy + hd * 0.05, z1 - 0.04), (cx + hw * 0.8, y1 + 0.005, z1 + hh * 0.3), taper=(1.0, 1.0)), M))
        span = float(hg.get("span", 0.3))
        for sg in (1, -1):
            lo, hi = (cx + sg * hw * 0.8, y1 - 0.035, z0 + hh * 0.86), (cx + sg * (hw + span), y1 - 0.02, z0 + hh * 0.86 + 0.07)
            lo, hi = (min(lo[0], hi[0]), lo[1], lo[2]), (max(lo[0], hi[0]), hi[1], hi[2])
            parts.append((_box(lo, hi), T))
    elif t == "hood":
        parts.append(dome(Vector((cx, cy + 0.01, c.z)), hw * 1.25, hd * 1.2, hh * 0.6, z0 + hh * 0.3, 0.5, M))
    elif t in ("veil", "kerchief"):
        # a cloth over the hair: tied at the nape (kerchief), or falling down the back (veil)
        parts.append(dome(Vector((cx, cy + 0.012, c.z)), hw * 1.16, hd * 1.12, hh * 0.47, z0 + hh * 0.62, 0.45, M))
        if t == "veil":
            ln = float(hg.get("length", 0.9))
            bm = _box((cx - hw * 1.15, y1 - 0.045, z0 - hh * ln), (cx + hw * 1.15, y1 + 0.02, z0 + hh * 0.72), taper=(1.5, 1.0))
            parts.append((bm, M))
            if hg.get("band", False):
                parts.append(ring(z0 + hh * 0.78, hw * 1.17, hd * 1.13, 0.012, T))
        else:
            parts.append((_box((cx - 0.05, y1 - 0.01, z0 + hh * 0.28), (cx + 0.05, y1 + 0.05, z0 + hh * 0.46)), M))
            parts.append((_box((cx - 0.07, y1 + 0.0, z0 - hh * 0.05), (cx + 0.07, y1 + 0.03, z0 + hh * 0.34), taper=(0.3, 1.0)), M))
    elif t == "headcloth":
        # the linen head-cloth of the black fields: banded at the brow, two lappets to the breast, a fall behind
        parts.append(dome(Vector((cx, cy + 0.01, c.z)), hw * 1.18, hd * 1.12, hh * 0.48, z0 + hh * 0.66, 0.2, M))
        parts.append(ring(z0 + hh * 0.74, hw * 1.17, hd * 1.12, 0.014, T))
        for sg in (1, -1):
            lo = (cx + sg * hw * 1.0 - 0.045, cy - hd * 0.75, z0 - hh * 0.45)
            hi = (cx + sg * hw * 1.0 + 0.045, cy - hd * 0.75 + 0.03, z0 + hh * 0.7)
            parts.append((_box(lo, hi, taper=(1.0, 1.0)), M))
            for i in range(3):
                zz = z0 - hh * 0.38 + i * hh * 0.3
                parts.append((_box((lo[0] - 0.003, lo[1] - 0.003, zz), (hi[0] + 0.003, hi[1] + 0.003, zz + hh * 0.08)), T))
        parts.append((_box((cx - hw * 1.1, y1 - 0.03, z0 - hh * 0.3), (cx + hw * 1.1, y1 + 0.02, z0 + hh * 0.7), taper=(1.25, 1.0)), M))
    elif t == "headband":
        parts.append(ring(z0 + hh * 0.72, hw * 1.08, hd * 1.06, 0.016, M))
        if hg.get("jewel", False):
            parts.append((_sphere_bm(Vector((cx, y0 - 0.012, z0 + hh * 0.72)), 0.02, 8), J))
        if hg.get("tails", False):
            for dx in (-0.02, 0.03):
                parts.append((_box((cx + dx - 0.014, y1 + 0.0, z0 + hh * 0.2), (cx + dx + 0.014, y1 + 0.014, z0 + hh * 0.72)), M))
    elif t == "helm":
        parts.append(dome(c, hw * 1.15, hd * 1.12, hh * 0.5, z0 + hh * 0.6, 0.0, M))
        parts.append(ring(z0 + hh * 0.6, hw * 1.18, hd * 1.15, 0.012, M))
        for sg in (1, -1):      # cheek pieces
            parts.append((_box((cx + sg * hw * 1.05 - 0.012, cy - hd * 0.75, z0 + hh * 0.18), (cx + sg * hw * 1.05 + 0.012, cy - hd * 0.1, z0 + hh * 0.62), taper=(0.6, 0.6)), M))
        crest = hg.get("crest", False)
        if crest:
            across = crest == "across"
            pts = []
            for u in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
                s = math.sin(math.pi * u)
                if across:
                    pts.append(Vector((cx - hw * 1.25 + hw * 2.5 * u, cy, z0 + hh * 0.78 + hh * 0.42 * s)))
                else:
                    pts.append(Vector((cx, cy + hd * 0.95 - hd * 1.9 * u, z1 + 0.02 + 0.1 * s)))
            bm = pk._tube_bm(pts, [0.03, 0.05, 0.06, 0.06, 0.05, 0.03], segments=6)
            parts.append((bm, T))
    elif t == "flightcap":
        # a leather flying cap with flaps over the ears
        parts.append(dome(Vector((cx, cy + 0.008, c.z)), hw * 1.14, hd * 1.1, hh * 0.47, z0 + hh * 0.66, 0.25, M))
        for sg in (1, -1):
            parts.append((_box((cx + sg * hw * 1.04 - 0.014, cy - 0.06, z0 + hh * 0.22), (cx + sg * hw * 1.04 + 0.014, cy + 0.06, z0 + hh * 0.7), taper=(0.6, 0.7)), M))
    if hg.get("goggles", False):
        G = slot.get(hg.get("trim"), M)
        parts.append(ring(z0 + hh * 0.76, hw * 1.14, hd * 1.12, 0.009, G, seg=5))
        for sg in (1, -1):
            parts.append((_ring_bm(Vector((cx + sg * hw * 0.45, y0 - 0.016, z0 + hh * 0.78)), 0.034, 0.01), J))
    name = "Headgear_%s%s" % (t, suffix(hg))
    ob = _merge(name, parts)
    _slots(ob, [material(home, D, nme) for nme in names])
    return ob
