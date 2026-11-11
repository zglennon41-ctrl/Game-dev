## A person's shape keys (the build, the face, the brow, the blink), kept small.
##
## Godot stores each shape key as a whole second copy of the mesh, so a body of 13,000 points
## with fourteen keys is fourteen bodies on disk: 264 MB over the twenty-six people. Most of a
## key is nothing (a nose's key moves the nose). So at import (people_import.gd) each mesh is
## saved without its keys, and the keys are kept beside it as only the points that move and
## how far (`pack`). When a person is put in the world the keys are put back (`wake`), once a
## mesh, and every later person of that home and sex shares the result.
class_name Shapes
extends RefCounted

const META := "shapes"
const STEP := 0.00002  # deltas are kept in fiftieths of a millimetre
const KEEP := ArrayMesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS

static var _woken := {}

## The mesh without its shape keys, the keys kept in its metadata. A mesh with none is itself.
static func pack(mesh: ArrayMesh) -> ArrayMesh:
	var count := mesh.get_blend_shape_count()
	if count == 0 or mesh.has_meta(META):
		return mesh
	# Without a display (godot --headless) the engine keeps no shape keys to read, so the mesh
	# is left whole: right, only large. tools/build-web.sh imports with a display for this.
	for s in mesh.get_surface_count():
		if mesh.surface_get_blend_shape_arrays(s).size() != count:
			return mesh
	var out := ArrayMesh.new()
	out.resource_name = mesh.resource_name
	var names := PackedStringArray()
	for b in count:
		names.append(String(mesh.get_blend_shape_name(b)))
	var surfaces := []
	for s in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(s)
		var base: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var keys := []
		var shapes := mesh.surface_get_blend_shape_arrays(s)
		for b in count:
			var moved: PackedVector3Array = shapes[b][Mesh.ARRAY_VERTEX]
			var at := PackedInt32Array()
			var by := PackedInt32Array()
			for i in base.size():
				var d := (moved[i] - base[i]) / STEP
				var x := roundi(d.x)
				var y := roundi(d.y)
				var z := roundi(d.z)
				if x != 0 or y != 0 or z != 0:
					at.append(i)
					by.append(x)
					by.append(y)
					by.append(z)
			keys.append([at, by])
		surfaces.append(keys)
		out.add_surface_from_arrays(mesh.surface_get_primitive_type(s), arrays, [], {}, mesh.surface_get_format(s) & KEEP | Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES)
		out.surface_set_name(s, mesh.surface_get_name(s))
		out.surface_set_material(s, mesh.surface_get_material(s))
	out.set_meta(META, { "names": names, "surfaces": surfaces })
	return out

## Every packed mesh under `root` given its shape keys back. Returns `root`.
static func wake(root: Node) -> Node:
	for m in root.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		if mi.mesh is ArrayMesh and mi.mesh.has_meta(META):
			mi.mesh = woken(mi.mesh)
	return root

## The mesh with its shape keys, built once and shared.
static func woken(mesh: ArrayMesh) -> ArrayMesh:
	if _woken.has(mesh):
		return _woken[mesh]
	var kept: Dictionary = mesh.get_meta(META)
	var out := ArrayMesh.new()
	out.resource_name = mesh.resource_name
	for n in kept["names"]:
		out.add_blend_shape(n)
	out.blend_shape_mode = Mesh.BLEND_SHAPE_MODE_NORMALIZED
	for s in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(s)
		var base: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var shapes := []
		for key in kept["surfaces"][s]:
			var at: PackedInt32Array = key[0]
			var by: PackedInt32Array = key[1]
			var moved := base.duplicate()
			for k in at.size():
				moved[at[k]] += Vector3(by[3 * k], by[3 * k + 1], by[3 * k + 2]) * STEP
			var shape := []
			shape.resize(Mesh.ARRAY_MAX)
			shape[Mesh.ARRAY_VERTEX] = moved
			shape[Mesh.ARRAY_NORMAL] = arrays[Mesh.ARRAY_NORMAL]
			shape[Mesh.ARRAY_TANGENT] = arrays[Mesh.ARRAY_TANGENT]
			shapes.append(shape)
		out.add_surface_from_arrays(mesh.surface_get_primitive_type(s), arrays, shapes, {}, mesh.surface_get_format(s) & KEEP)
		out.surface_set_name(s, mesh.surface_get_name(s))
		out.surface_set_material(s, mesh.surface_get_material(s))
	_woken[mesh] = out
	return out
