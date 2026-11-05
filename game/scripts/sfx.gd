## Sound: a low tunnel ambience and synthesized combat sounds. No metronome: the timing layer
## is heard only in the Pattern's cues.
class_name Sfx
extends Node

const RATE := 44100
var _sfx: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _ambience := AudioStreamPlayer.new()

func _ready() -> void:
	for i in 16:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	add_child(_ambience)
	_build()

func start_ambience() -> void:
	if not _ambience.playing:
		_ambience.play()

func stop_ambience() -> void:
	_ambience.stop()

func play(name: String, pitch := 1.0, volume_db := 0.0) -> void:
	if not _sfx.has(name):
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _sfx[name]
	p.pitch_scale = pitch * randf_range(0.96, 1.04)
	p.volume_db = volume_db
	p.play()

func _wav(samples: PackedFloat32Array, loop := false) -> AudioStreamWAV:
	var bytes := PackedByteArray()
	bytes.resize(samples.size() * 2)
	for i in samples.size():
		bytes.encode_s16(i * 2, int(clampf(samples[i], -1.0, 1.0) * 32000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.data = bytes
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_end = samples.size()
	return w

func _buf(dur: float) -> PackedFloat32Array:
	var b := PackedFloat32Array()
	b.resize(int(dur * RATE))
	return b

func _tone(buf: PackedFloat32Array, at: float, freq: float, dur: float, gain: float, shape := "sine", sweep_to := -1.0) -> void:
	var start := int(at * RATE)
	var n := int(dur * RATE)
	var phase := 0.0
	for i in n:
		var idx := start + i
		if idx >= buf.size():
			break
		var x := float(i) / n
		phase += (freq if sweep_to < 0.0 else lerpf(freq, sweep_to, x)) / RATE
		var env := minf(1.0, i / (0.003 * RATE)) * pow(1.0 - x, 3.0)
		var v: float
		match shape:
			"square": v = 1.0 if fmod(phase, 1.0) < 0.5 else -1.0
			"saw": v = 2.0 * fmod(phase, 1.0) - 1.0
			"tri": v = 4.0 * absf(fmod(phase, 1.0) - 0.5) - 1.0
			_: v = sin(phase * TAU)
		buf[idx] += v * gain * env

func _noise(buf: PackedFloat32Array, at: float, dur: float, gain: float, smooth := 0.5, seed := 11) -> void:
	var start := int(at * RATE)
	var n := int(dur * RATE)
	var y := 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	for i in n:
		var idx := start + i
		if idx >= buf.size():
			break
		y = lerpf(y, rng.randf_range(-1.0, 1.0), smooth)
		buf[idx] += y * gain * pow(1.0 - float(i) / n, 2.0)

func _build() -> void:
	var b: PackedFloat32Array
	# Sword: a swish, and a meaty impact.
	b = _buf(0.25); _noise(b, 0, 0.22, 0.25, 0.35, 3); _sfx["swish"] = _wav(b)
	b = _buf(0.3); _noise(b, 0, 0.12, 0.6, 0.6, 5); _tone(b, 0, 180, 0.18, 0.5, "sine", 70); _sfx["hit"] = _wav(b)
	b = _buf(0.5); _tone(b, 0, 110, 0.4, 0.9, "sine", 35); _noise(b, 0, 0.4, 0.5, 0.12, 7); _sfx["heavy"] = _wav(b)
	b = _buf(0.7); _tone(b, 0, 1560, 0.6, 0.22); _tone(b, 0, 2340, 0.45, 0.14); _tone(b, 0, 3120, 0.25, 0.08); _noise(b, 0, 0.05, 0.4, 0.9, 9); _sfx["parry"] = _wav(b)
	b = _buf(0.25); _tone(b, 0, 320, 0.18, 0.3, "square"); _noise(b, 0, 0.08, 0.3, 0.7, 13); _sfx["block"] = _wav(b)
	b = _buf(0.45); _noise(b, 0, 0.35, 0.6, 0.12, 15); _tone(b, 0, 140, 0.3, 0.6, "sine", 50); _sfx["hurt"] = _wav(b)
	b = _buf(0.35); _noise(b, 0, 0.3, 0.2, 0.08, 17); _sfx["dodge"] = _wav(b)
	b = _buf(1.0); _tone(b, 0, 98, 0.9, 0.3, "saw"); _tone(b, 0, 147, 0.9, 0.18, "saw"); _sfx["stagger"] = _wav(b)
	b = _buf(0.5); _tone(b, 0, 220, 0.45, 0.2, "tri"); _tone(b, 0.06, 330, 0.4, 0.12, "tri"); _sfx["stance"] = _wav(b)
	b = _buf(0.9); _tone(b, 0, 75, 0.8, 0.25, "saw", 120); _noise(b, 0, 0.8, 0.08, 0.05, 19); _sfx["growl"] = _wav(b)
	b = _buf(0.3); _tone(b, 0, 300, 0.25, 0.25, "saw", 140); _noise(b, 0, 0.2, 0.2, 0.2, 21); _sfx["bark"] = _wav(b)
	b = _buf(1.4); _tone(b, 0, 196, 1.2, 0.2, "tri"); _tone(b, 0.15, 247, 1.0, 0.15, "tri"); _tone(b, 0.3, 294, 1.0, 0.15, "tri"); _sfx["fell"] = _wav(b)
	b = _buf(1.6); _tone(b, 0, 294, 1.5, 0.2, "tri"); _tone(b, 0.2, 392, 1.4, 0.15, "tri"); _sfx["done"] = _wav(b)
	b = _buf(0.12); _tone(b, 0, 880, 0.08, 0.25, "tri"); _sfx["cue"] = _wav(b)
	b = _buf(0.2); _tone(b, 0, 1320, 0.15, 0.3, "tri"); _tone(b, 0, 660, 0.15, 0.2, "sine"); _sfx["cue-hit"] = _wav(b)
	b = _buf(0.4); _tone(b, 0, 200, 0.35, 0.25, "saw", 90); _sfx["fizzle"] = _wav(b)
	b = _buf(1.2); _tone(b, 0, 55, 1.1, 0.8, "sine", 30); _noise(b, 0, 1.0, 0.5, 0.06, 23); _tone(b, 0.05, 440, 0.9, 0.12, "tri"); _tone(b, 0.05, 660, 0.9, 0.08, "tri"); _sfx["pattern"] = _wav(b)
	b = _buf(0.15); _tone(b, 0, 150, 0.1, 0.12, "square"); _sfx["deny"] = _wav(b)
	# Ambience: a low wind in the tunnel, looped.
	var amb := _buf(6.0)
	var y := 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 29
	for i in amb.size():
		y = lerpf(y, rng.randf_range(-1.0, 1.0), 0.02)
		var t := float(i) / RATE
		amb[i] = y * 0.5 * (0.7 + 0.3 * sin(t * TAU / 6.0)) + 0.03 * sin(TAU * 55.0 * t)
	_ambience.stream = _wav(amb, true)
	_ambience.volume_db = -10.0
