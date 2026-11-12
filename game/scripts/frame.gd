## A person's frame: what a build does to the joints.
##
## A shape key reshapes a body and cannot move a joint. A broad frame sets the shoulders wider
## and age carries the head and the shoulders forward, so those are given back here: every time
## the skeleton is posed, the bones a look's frame names are moved by its measure on top of
## whatever the animation set (data/creation.json, look.frame.bones; World.frame_moves). The
## engine takes the moves off again after the skin is drawn, so they never add up.
class_name Frame
extends SkeletonModifier3D

var _moves := {}      # bone index -> how far it is moved, in its parent's space

## `moves`: bone name -> how far, in the body's own space at rest (to its left, up, forward).
func set_moves(moves: Dictionary) -> void:
	_moves.clear()
	var skel := get_skeleton()
	if skel == null:
		return
	for bone in moves:
		var i := skel.find_bone(String(bone))
		if i < 0 or (moves[bone] as Vector3).is_zero_approx():
			continue
		var parent := skel.get_bone_parent(i)
		var basis := skel.get_bone_global_rest(parent).basis.orthonormalized() if parent >= 0 else Basis.IDENTITY
		_moves[i] = basis.inverse() * (moves[bone] as Vector3)
	active = not _moves.is_empty()
	# posed again at once, also where nothing is playing
	if skel.get_bone_count() > 0:
		skel.set_bone_pose_position(0, skel.get_bone_pose_position(0))

func _process_modification() -> void:
	var skel := get_skeleton()
	if skel == null:
		return
	for i in _moves:
		skel.set_bone_pose_position(i, skel.get_bone_pose_position(i) + _moves[i])
