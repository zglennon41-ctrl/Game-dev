"""What the small people give a hybrid (docs/genius-tree.md, "Hybrids"; a base's hybrid.gift):
the parts a genius of another base wears when it has turned toward the Imp, the Sprite or
the Homunculus. Each is bold enough to say whose it is at a glance, and each is its own
file, named for the base that gives it, because other bases give horns, a tail, a glow and
small hands too and theirs are not these:

    game/assets/genius/gifts/<base>-<feature>.glb

The game hangs a hybrid's gift from the giver's own part where there is one, and the common
part (parts/<feature>.glb) where there is not (game/scripts/genius/genius_body.gd).

    python tools/blender/people_gifts.py

A part is modelled at its socket's origin, at the kit's size, for the character's left where
it is one of a pair (genius_kit.py)."""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genius_geo as g  # noqa: E402
from genius_geo import X, Y, Z  # noqa: E402
import genius_kit as kit  # noqa: E402
from genius_kit import mat, field  # noqa: E402
import lines_people as lp  # noqa: E402

OUT = os.path.join(kit.ROOT, "game", "assets", "genius", "gifts")


def _hoop(c, rx, rz, r, u=X, v=Z, n=12, sides=3):
    return lp._hoop(c, rx, rz, r, u=u, v=v, n=n, sides=sides)


def imp_horns():
    """The Imp's horns: thick, pale, coming forward, each ruled twice with its ledger's light."""
    left = g.tube([(0.036, 0.0, -0.014), (0.078, -0.012, 0.05), (0.104, -0.05, 0.12), (0.094, -0.1, 0.19)], [0.03, 0.025, 0.016, 0.003], n=6)
    rings = g.merge(_hoop((0.05, -0.002, 0.008), 0.032, 0.032, 0.006, u=X, v=Y, n=8), _hoop((0.085, -0.022, 0.07), 0.026, 0.026, 0.005, u=Vector((0.8, 0, -0.5)).normalized(), v=Y, n=8))
    return [(g.merge(left, g.mirrored(left)), mat("bone")), (g.merge(rings, g.mirrored(rings)), field("script", 2.2))]


def imp_tail():
    """The Imp's tail: long, curling up to a spade, with what it is owed on tags along it."""
    # thick enough, and red enough, to be seen on any body in any light; banded with brass
    pts = [Vector(p) for p in ((0, 0.0, 0.0), (0, 0.1, -0.06), (0.01, 0.22, -0.08), (0.03, 0.34, -0.02), (0.05, 0.4, 0.1), (0.05, 0.36, 0.22), (0.03, 0.27, 0.27))]
    radii = [0.036, 0.033, 0.029, 0.025, 0.021, 0.017, 0.014]
    d = (pts[-1] - pts[-2]).normalized()
    items = [(g.tube(pts, radii, n=6), mat("welt")),
             (g.blade(pts[-1] - d * 0.02, pts[-1] + d * 0.2, 0.15, normal=(1, 0, 0), belly=0.36, thick=0.022), field("barb", 2.2))]
    bands = None
    for i in (1, 2, 3, 4, 5):
        u = (pts[i + 1] - pts[i - 1]).normalized()
        a = u.cross(Vector((1, 0, 0))).normalized()
        bands = g.merge(bands, _hoop(pts[i], radii[i] + 0.006, radii[i] + 0.006, 0.006, u=Vector((1, 0, 0)), v=a, n=8, sides=3))
    items.append((bands, mat("metal_brass")))
    tags, links = None, None
    for i, k in enumerate((1, 2, 3)):
        p = pts[k] + Vector((0, 0, -radii[k]))
        links = g.merge(links, g.tube([p, p + Vector((0, 0, -0.04))], 0.005, n=3))
        tags = g.merge(tags, g.box(p + Vector((0, 0, -0.08)), (0.012, 0.055, 0.075), rot=(0, 0, 0.3 * (i - 1))))
    items += [(links, mat("metal_iron_light")), (tags, mat("paper"))]
    return items


def sprite_glow():
    """The Sprite's light: a lantern no bigger than a thumb, with wings of its own and a ring of
    its afterglow round it."""
    c = Vector((0, 0, -0.06))
    items = [(geo, lp.Person.material(_Roles(), m)) for geo, m in lp.lantern(c, 0.05, "round", "lamp", 4.2)]
    wings = None
    for s in (1, -1):
        root = c + Vector((s * 0.02, 0.03, 0.03))
        wings = g.merge(wings, g.blade(root, root + Vector((s * 0.15, 0.05, 0.1)), 0.06, normal=(0, -1, 0.2), belly=0.55, thick=0.004), g.blade(root, root + Vector((s * 0.12, 0.05, -0.04)), 0.05, normal=(0, -1, -0.2), belly=0.55, thick=0.004))
    items.append((wings, field("wing", 1.2)))
    items.append((_hoop(c, 0.16, 0.16, 0.006, u=X, v=Vector((0, 0.94, 0.34)), n=16), field("glow", 2.2)))
    motes = None
    for i in range(3):
        a = 0.6 + i * 2.1
        motes = g.merge(motes, g.ico(c + X * 0.16 * math.cos(a) + Vector((0, 0.94, 0.34)) * 0.16 * math.sin(a), 0.011, sub=0))
    items.append((motes, field("mote", 3.2)))
    return items


class _Roles:
    """Enough of a Person for lp.Person.material: a part has no partner's coat to wear."""
    roles = {}


def _hand(skin, k, decimate=0.3):
    """The kit's own small hand, at k times its size, in another skin; without its cuff."""
    ob = kit.small_hands_part()[0]
    me = ob.data
    names = [m.name for m in me.materials]
    slot = names.index("hand_skin")
    me.materials[slot] = skin
    # drop the kit's brass cuff and bead: these hands wear their own
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    doomed = [f for f in bm.faces if f.material_index != slot]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    for v in bm.verts:
        v.co *= k
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    return ob


def sprite_small_hands():
    """The Sprite's hands: small, quick, in a cuff of petals, the fingertips alight."""
    hand = _hand(mat("fey_skin"), 1.2)
    petals = None
    for i in range(6):
        a = 2 * math.pi * i / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        petals = g.merge(petals, g.blade(d * 0.016 + Z * -0.004, d * 0.05 + Z * 0.03, 0.036, normal=d, belly=0.45))
    cuff = g.to_object("petal_cuff", petals, mat("cloth_petal"), smooth=True)
    tips = g.to_object("fingertips", g.ico((0, -0.004, -0.058 * 1.2), 0.012, sub=0), field("palms", 2.8))
    return [g.join("sprite_small_hands", [hand, cuff, tips])]


def homunculus_small_hands():
    """The Homunculus's hands: a maker's, larger than the arm they are on, better finished than
    anything else it has, a ring of brass at the wrist and a thumbprint of light in the palm."""
    hand = _hand(mat("fired"), 1.7)
    ring = g.to_object("wrist_ring", lp._hoop((0, 0, 0.004), 0.03, 0.03, 0.01, u=X, v=Y, n=10, sides=4), mat("metal_brass"))
    slip = g.to_object("wrist_clay", g.lathe([(0.026, 0.012), (0.034, 0.03), (0.03, 0.05)], n=8), mat("clay"), smooth=True)
    whorl = g.to_object("palm_print", g.merge(lp._hoop((-0.014, -0.004, -0.04), 0.012, 0.016, 0.0025, u=Y, v=Z, n=8), g.ico((-0.014, -0.004, -0.04), 0.004, sub=0)), field("seam", 2.2))
    return [g.join("homunculus_small_hands", [hand, ring, slip, whorl])]


def homunculus_brush():
    """The Homunculus's brush: as long as a forearm, the bristles heavy with slip and the
    light of the field in the slip."""
    items = [(g.tube([(0, 0, 0.2), (0, 0, -0.06)], [0.01, 0.014], n=6), mat("wood")),
             (g.tube([(0, 0, -0.05), (0, 0, -0.085)], [0.018, 0.02], n=6), mat("metal_brass")),
             (g.tongue([(0, 0, -0.08), (0, 0, -0.125), (0, 0, -0.18)], [0.04, 0.05, 0.024], thick=1.0, normal=(0, 1, 0)), mat("bristle")),
             (g.tongue([(0, 0, -0.165), (0, 0, -0.22)], [0.03, 0.002], thick=1.0, normal=(0, 1, 0)), field("ink", 2.6)),
             (g.ico((0, 0, 0.206), 0.014, sub=0), mat("metal_brass")),
             (g.ico((0.006, -0.008, -0.105), 0.022, sub=0, scale=(1, 0.6, 1.2)), mat("clay"))]
    return items


GIFTS = {"imp-horns": imp_horns, "imp-tail": imp_tail, "sprite-glow": sprite_glow, "sprite-small-hands": sprite_small_hands,
         "homunculus-small-hands": homunculus_small_hands, "homunculus-brush": homunculus_brush}


def build(name):
    kit.reset()
    made = GIFTS[name]()
    objs = made if made and not isinstance(made[0], tuple) else [g.pieces(name.replace("-", "_"), made)]
    path = os.path.join(OUT, name + ".glb")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    print("[people_gifts] wrote", os.path.relpath(path, kit.ROOT), "%d triangles, %d KB" % (tris, os.path.getsize(path) // 1024))


if __name__ == "__main__":
    for name in (sys.argv[1:] or list(GIFTS)):
        build(name)
