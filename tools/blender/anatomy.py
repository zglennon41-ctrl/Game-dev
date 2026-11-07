"""WILDLINE anatomy: one connected body grown from a skeleton graph with Blender's Skin
modifier (so the shoulders, elbows, hips and knees are continuous surfaces, not tubes meeting
at a seam), subdivided once, then carved by displacement points (pectorals, deltoids, the
spine's groove, eye sockets, cheekbones, the chin) that scale with the build and the home's
face. The graph's radii and the carving are the data; the body kit skins and exports it.

World space is Blender's: Z up, the face at -Y, a T-pose on the people kit's reshaped KayKit
rig (hips 1.113, knee 0.57, ankle 0.12, shoulder joint 1.817 at x 0.151, elbow 0.518, wrist
0.913, neck 2.028, crown 2.40).
"""
import math

import bpy
import bmesh
from mathutils import Vector


# ======================================================================================
# The graph: (name, position, radius x, radius y, parent). Radii are half-widths of the
# cross-section: x across, y front-to-back for the trunk; for limbs the frame follows the
# edge. Values are the fit masculine body; `scale` tables below reshape by sex and build.
# ======================================================================================

def graph(sex="m", build="fit"):
    fem = sex == "f"
    L = limb_k(build)       # limbs' girth by build
    T = trunk_k(build)      # trunk's girth by build
    S = 0.86 if fem else 1.0   # the feminine shoulder girdle
    H = 1.08 if fem else 1.0   # the feminine pelvis
    N = []

    def node(name, pos, rx, ry=None, parent=None):
        N.append((name, Vector(pos), rx, rx if ry is None else ry, parent))
        return name

    # the trunk, from the pelvis up the spine (girths from a 1.8 m frame scaled to 2.4)
    pelvis = node("pelvis", (0, 0.01, 1.02), 0.165 * T * H, 0.115 * T)
    node("hip_l", (0.11, 0.0, 1.09), 0.095 * T * H, 0.11 * T, pelvis)
    node("hip_r", (-0.11, 0.0, 1.09), 0.095 * T * H, 0.11 * T, pelvis)
    waist = node("waist", (0, 0.0, 1.24), (0.125 if fem else 0.145) * T, 0.105 * T, pelvis)
    belly = node("belly", (0, -0.005, 1.42), (0.14 if fem else 0.16) * T, 0.115 * T, waist)
    chest = node("chest", (0, 0.0, 1.62), (0.17 if fem else 0.19) * T, (0.135 if fem else 0.13) * T, belly)
    girdle = node("girdle", (0, 0.0, 1.8), 0.2 * T * S, 0.12 * T, chest)
    neck0 = node("neck0", (0, 0.015, 1.96), 0.075 * T, 0.075 * T, girdle)
    neck1 = node("neck1", (0, 0.015, 2.04), (0.052 if fem else 0.06), (0.058 if fem else 0.065), neck0)
    # the neck reaches up under the chin; the head itself is head.py's, set on it
    node("neck2", (0, 0.02, 2.1), (0.05 if fem else 0.058), (0.056 if fem else 0.062), neck1)
    # the arms, from the shoulder girdle: deltoid, upper arm, elbow, forearm, wrist, hand, fingers
    for side, sg in (("l", 1), ("r", -1)):
        delt = node("delt_" + side, (sg * 0.21 * S, 0.0, 1.835), 0.08 * L, 0.082 * L, girdle)
        ua = node("upperarm_" + side, (sg * 0.36, -0.005, 1.815), 0.062 * L, 0.066 * L, delt)
        el = node("elbow_" + side, (sg * 0.518, 0.0, 1.817), 0.05 * L, 0.054 * L, ua)
        fa = node("forearm_" + side, (sg * 0.68, -0.005, 1.817), 0.058 * L, 0.055 * L, el)
        wr = node("wrist_" + side, (sg * 0.913, 0.0, 1.817), 0.036, 0.03, fa)
        palm = node("palm_" + side, (sg * 0.99, 0.0, 1.815), 0.048, 0.02, wr)
        knuck = node("knuckles_" + side, (sg * 1.045, 0.0, 1.813), 0.046, 0.016, palm)
        for i, y in enumerate((-0.036, -0.012, 0.012, 0.036)):
            ln = (0.075, 0.085, 0.08, 0.065)[i]
            f0 = node("f%d_%s_0" % (i, side), (sg * (1.055 + ln * 0.5), y * 1.02, 1.81), 0.011, 0.01, knuck)
            node("f%d_%s_1" % (i, side), (sg * (1.055 + ln), y * 1.05, 1.806), 0.009, 0.008, f0)
        t0 = node("thumb_%s_0" % side, (sg * 0.995, -0.052, 1.808), 0.013, 0.011, palm)
        node("thumb_%s_1" % side, (sg * 1.03, -0.075, 1.8), 0.01, 0.009, t0)
    # the legs: thigh, knee, calf, ankle, heel, foot, toes
    for side, sg in (("l", 1), ("r", -1)):
        hip = "hip_" + side
        th = node("thigh_" + side, (sg * 0.121, 0.0, 0.86), 0.1 * L, 0.108 * L, hip)
        kn = node("knee_" + side, (sg * 0.121, -0.005, 0.57), 0.068 * L, 0.072 * L, th)
        ca = node("calf_" + side, (sg * 0.121, 0.012, 0.4), 0.074 * L, 0.084 * L, kn)
        an = node("ankle_" + side, (sg * 0.121, 0.0, 0.14), 0.044, 0.048, ca)
        node("heel_" + side, (sg * 0.121, 0.065, 0.05), 0.04, 0.04, an)
        fo = node("foot_" + side, (sg * 0.121, -0.07, 0.045), 0.048, 0.04, an)
        node("toes_" + side, (sg * 0.121, -0.2, 0.03), 0.045, 0.028, fo)
    return N


def limb_k(build):
    return {"lean": 0.88, "fit": 1.0, "heavy": 1.18}[build]


def trunk_k(build):
    return {"lean": 0.92, "fit": 1.0, "heavy": 1.12}[build]


# ======================================================================================
# The carving: displacement points (position, radius, strength [, anisotropy]) pushed along
# the vertex normal with a smooth falloff. Positive is out, negative in. Each is scaled by
# the build (muscle) or the home's face parameters.
# ======================================================================================

def carving(sex="m", build="fit", face=None):
    face = face or {}
    fp = lambda k: float(face.get(k, 1.0))  # noqa: E731
    m = {"lean": 0.6, "fit": 1.0, "heavy": 1.5}[build]   # how much the muscle shows
    fem = sex == "f"
    P = []

    def pt(pos, r, s, aniso=(1, 1, 1)):
        P.append((Vector(pos), r, s, Vector(aniso)))

    for sg in (1, -1):
        pt((sg * 0.075, -0.11, 1.66), 0.085, (0.006 if fem else 0.012) * m, (1.2, 1, 0.8))   # pectoral
        if fem:
            pt((sg * 0.065, -0.12, 1.63), 0.06, 0.03, (1, 1, 1))                            # bust
        pt((sg * 0.205, -0.02, 1.85), 0.075, 0.012 * m, (1, 1, 1.1))                         # deltoid
        pt((sg * 0.34, -0.045, 1.825), 0.06, 0.009 * m, (1.5, 1, 1))                         # biceps
        pt((sg * 0.66, 0.0, 1.83), 0.06, 0.006 * m, (1.6, 1, 1))                             # forearm
        pt((sg * 0.1, 0.06, 1.92), 0.08, 0.008 * m, (1.2, 1, 1))                             # trapezius
        pt((sg * 0.08, 0.1, 1.06), 0.08, 0.012, (1, 1, 1.1))                                 # glute
        pt((sg * 0.121, 0.07, 0.42), 0.06, 0.01 * m, (1, 1, 1.5))                            # calf
        pt((sg * 0.13, -0.06, 0.78), 0.08, 0.006 * m, (1, 1, 1.8))                           # quadriceps
        pt((sg * 0.165, 0.0, 1.3), 0.07, -0.008, (1, 1, 1.4))                                # the waist's sides
        # the face
        pt((sg * 0.036, -0.1, 2.25), 0.036, -0.022, (1.3, 1, 0.9))                           # eye socket
        pt((sg * 0.075, -0.06, 2.21), 0.038, 0.012 * fp("cheek"), (1, 1, 1))                 # cheekbone
        pt((sg * 0.09, -0.01, 2.3), 0.045, -0.01, (1, 1, 1.2))                               # temple
        pt((sg * 0.065, -0.02, 2.12), 0.04, 0.012 * (fp("jaw") - 0.5), (1, 1, 1))           # jaw corner
        pt((sg * 0.05, -0.088, 2.145), 0.032, -0.008, (1, 1, 1))                             # the cheek's hollow
        pt((sg * 0.045, 0.02, 2.14), 0.04, -0.012, (1, 1, 1.2))                              # under the ear, the jaw's turn
    pt((0, -0.105, 2.295), 0.05, 0.012 * fp("brow"), (2.0, 1, 0.6))                           # brow ridge
    pt((0, -0.095, 2.085), 0.032, 0.016, (1, 1, 1))                                           # chin
    pt((0, -0.105, 2.165), 0.024, -0.008, (1.6, 1, 0.5))                                      # the mouth's line
    pt((0, -0.1, 2.185), 0.02, 0.007 * fp("lips"), (1.4, 1, 0.6))                             # upper lip
    pt((0, -0.102, 2.15), 0.02, 0.008 * fp("lips"), (1.4, 1, 0.6))                            # lower lip
    pt((0, -0.09, 2.22), 0.03, 0.01 * fp("nose"), (0.7, 1, 1.6))                              # the nose's bridge and ridge
    pt((0, 0.09, 2.2), 0.06, 0.01, (1, 1, 1.2))                                               # the back of the skull
    pt((0, 0.07, 1.55), 0.05, -0.012, (0.5, 1, 3.0))                                          # the spine's groove
    pt((0, -0.09, 1.5), 0.05, 0.004 * m, (0.6, 1, 2.0))                                       # abdomen
    return P


def carve(ob, points):
    """Displace the mesh's vertices by the points, along their normals."""
    me = ob.data
    normals = [n.vector.copy() for n in me.vertex_normals]
    moved = 0
    for v, n in zip(me.vertices, normals):
        p = ob.matrix_world @ v.co
        d = 0.0
        for c, r, s, a in points:
            q = p - c
            q = Vector((q.x / a.x, q.y / a.y, q.z / a.z))
            t = q.length / r
            if t < 1.0:
                w = 1.0 - t * t
                d += s * w * w
        if d != 0.0:
            v.co = v.co + n * d
            moved += 1
    return moved


# ======================================================================================
# Growing the mesh
# ======================================================================================

def grow(name, nodes, subdiv=1, smooth=2):
    """A skin-modifier body from the graph, subdivided, with modifiers applied: one object."""
    bm = bmesh.new()
    layer = bm.verts.layers.skin.verify()
    verts = {}
    for n, pos, rx, ry, parent in nodes:
        v = bm.verts.new(pos)
        v[layer].radius = (rx, ry)
        if parent is None:
            v[layer].use_root = True
        verts[n] = v
        if parent is not None:
            bm.edges.new((verts[parent], v))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    sk = ob.modifiers.new("Skin", "SKIN")
    sk.use_smooth_shade = True
    sk.branch_smoothing = 0.6
    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = subdiv
    sub.render_levels = subdiv
    if smooth > 0:
        cs = ob.modifiers.new("Smooth", "SMOOTH")
        cs.factor = 0.5
        cs.iterations = smooth
    # Apply by evaluating: the evaluated mesh replaces the base.
    dg = bpy.context.evaluated_depsgraph_get()
    eva = ob.evaluated_get(dg)
    new_me = bpy.data.meshes.new_from_object(eva)
    ob.modifiers.clear()
    old = ob.data
    ob.data = new_me
    bpy.data.meshes.remove(old)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def body_mesh(name, sex, build, face=None, subdiv=1):
    ob = grow(name, graph(sex, build), subdiv=subdiv)
    carve(ob, carving(sex, build, face))
    return ob
