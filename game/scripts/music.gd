## The score: a theme per place and zone, a fight layer over it, and stingers for the big
## moments (data/music.json; tracks in game/assets/music). Two players crossfade the theme;
## the fight layer rises when foes are up and falls when they are not.
class_name Music
extends Node

var _a := AudioStreamPlayer.new()
var _b := AudioStreamPlayer.new()
var _fight := AudioStreamPlayer.new()
var _sting := AudioStreamPlayer.new()
var _cur := ""          # the track id playing
var _front: AudioStreamPlayer = null
var _fight_on := false
var _data: Dictionary = {}
var _cache: Dictionary = {}
var enabled := true

func _ready() -> void:
	for p in [_a, _b, _fight, _sting]:
		add_child(p)
		p.bus = "Master"
	_a.volume_db = -80.0
	_b.volume_db = -80.0
	_fight.volume_db = -80.0
	_data = Data.music if "music" in Data and Data.music is Dictionary else {}
	if _data.is_empty():
		var f := FileAccess.open("res://data/music.json", FileAccess.READ)
		if f:
			var parsed: Variant = JSON.parse_string(f.get_as_text())
			if parsed is Dictionary:
				_data = parsed

func _stream(track: String) -> AudioStream:
	if _cache.has(track):
		return _cache[track]
	var t: Dictionary = _data.get("tracks", {}).get(track, {})
	var path := "res://game/assets/music/%s" % String(t.get("file", track + ".wav"))
	if not ResourceLoader.exists(path):
		return null
	var st: AudioStream = load(path)
	if st is AudioStreamOggVorbis:
		(st as AudioStreamOggVorbis).loop = t.get("kind", "loop") == "loop"
	if st is AudioStreamWAV:
		(st as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD if t.get("kind", "loop") == "loop" else AudioStreamWAV.LOOP_DISABLED
		if t.get("kind", "loop") == "loop":
			(st as AudioStreamWAV).loop_end = int((st as AudioStreamWAV).data.size() / 2 / (2 if (st as AudioStreamWAV).stereo else 1))
	_cache[track] = st
	return st

func _gain(track: String) -> float:
	return float(_data.get("tracks", {}).get(track, {}).get("gain", -8.0))

## The theme for a place of the Academy or a zone ("green", "cut", "quad"...).
func play_for(place_id: String) -> void:
	var track := ""
	if _data.get("places", {}).has(place_id):
		track = String(_data["places"][place_id])
	elif Zones.is_zone(place_id) and _data.get("zones", {}).has(Zones.zone_of(place_id)):
		track = String(_data["zones"][Zones.zone_of(place_id)])
	play_track(track)

func play_track(track: String) -> void:
	if not enabled or track == _cur:
		return
	var st := _stream(track) if track != "" else null
	var next: AudioStreamPlayer = _b if _front == _a else _a
	var old := _front
	_cur = track
	if st:
		next.stream = st
		next.volume_db = -40.0
		next.play()
		var tw := create_tween()
		tw.tween_property(next, "volume_db", _gain(track), 2.2)
		_front = next
	else:
		_front = null
	if old:
		var tw2 := create_tween()
		tw2.tween_property(old, "volume_db", -40.0, 1.8)
		tw2.tween_callback(old.stop)

## The fight layer over the theme, while foes are up.
func set_fight(on: bool) -> void:
	if not enabled or on == _fight_on:
		return
	_fight_on = on
	var track := String(_data.get("fight", "fight"))
	var st := _stream(track)
	if st == null:
		return
	if on:
		if not _fight.playing:
			_fight.stream = st
			_fight.volume_db = -40.0
			_fight.play()
		var tw := create_tween()
		tw.tween_property(_fight, "volume_db", _gain(track), 1.2)
	else:
		var tw2 := create_tween()
		tw2.tween_property(_fight, "volume_db", -40.0, 2.5)
		tw2.tween_callback(_fight.stop)

## A stinger: the Pattern, the rite, the Reckoning, a quest done or lost.
func sting(name: String) -> void:
	if not enabled:
		return
	var track := String(_data.get("stingers", {}).get(name, "sting_" + name))
	var st := _stream(track)
	if st == null:
		return
	_sting.stream = st
	_sting.volume_db = _gain(track)
	_sting.play()

func stop_all() -> void:
	_cur = ""
	for p in [_a, _b, _fight]:
		var tw := create_tween()
		tw.tween_property(p, "volume_db", -40.0, 1.0)
		tw.tween_callback(p.stop)
	_fight_on = false
	_front = null
