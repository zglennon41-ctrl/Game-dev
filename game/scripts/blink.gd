class_name Blink
extends Node
## A person blinks. Every body carries a closed lid inside each eye, out of sight; its shape
## key `blink` brings it out over the eye (tools/blender/faces.py). This closes both for a
## moment, now and then, and sometimes twice. World.dress gives one to everyone with lids.

const SHUT := 0.11          # seconds the eyes stay closed
const BETWEEN := Vector2(2.4, 6.0)

var _lids: Array = []       # [MeshInstance3D, the key's index]
var _wait := 1.5
var _shut := 0.0
var _again := false

func _ready() -> void:
	_wait = randf_range(0.6, BETWEEN.y)
	for a in get_parent().find_children("Lid_*", "BoneAttachment3D", true, false):
		for m in a.find_children("*", "MeshInstance3D", true, false):
			var mi: MeshInstance3D = m
			var k := mi.find_blend_shape_by_name("blink")
			if k >= 0:
				_lids.append([mi, k])
	set_process(not _lids.is_empty())

## Close the eyes now (the creator does, when a face is chosen: the new one opens its eyes).
func now() -> void:
	_wait = 0.0

func _process(dt: float) -> void:
	if _shut > 0.0:
		_shut -= dt
		if _shut <= 0.0:
			_lids_to(0.0)
			_wait = 0.16 if _again else randf_range(BETWEEN.x, BETWEEN.y)
			_again = false
		return
	_wait -= dt
	if _wait <= 0.0:
		_shut = SHUT
		_again = not _again and randf() < 0.18
		_lids_to(1.0)

func _lids_to(v: float) -> void:
	for l in _lids:
		if is_instance_valid(l[0]):
			(l[0] as MeshInstance3D).set_blend_shape_value(l[1], v)
