## The pulse: a looping bar of music that is also the clock. Beats are where the music puts
## them; the game reads the playback position (corrected for mixing and output latency), so
## what is heard, what is seen, and what is judged agree. Also the sound effects, synthesized.
class_name Pulse
extends Node

const RATE := 44100
const BEATS_PER_BAR := 4

var period := 0.6
var bar_len := 2.4
## Beat 0 is the first beat of the second bar: the first bar is a count-in.
var t0 := 2.4
## Player calibration in ms: positive if the player's inputs land late on this device.
var calibration_ms := 0.0

var _music := AudioStreamPlayer.new()
var _loop_len := 9.6
var _bar_stream: AudioStreamWAV = null
var _bar_period := -1.0
var _loops := 0
var _last_pos := 0.0
var _last_t := 0.0
var _running := false
var _dummy := false
var _start_ticks := 0
var _frame_ticks := 0
var _frame_t := 0.0
var _sfx: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next_player := 0

func _ready() -> void:
	_dummy = DisplayServer.get_name() == "headless"
	add_child(_music)
	for i in 12:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	_build_sfx()

func start(beat_period: float) -> void:
	period = beat_period
	bar_len = period * BEATS_PER_BAR
	t0 = bar_len
	_loop_len = bar_len * 4
	if _bar_stream == null or _bar_period != period:
		_bar_stream = _build_bar(4)
		_bar_period = period
	_music.stream = _bar_stream
	_music.volume_db = -4.0
	_loops = 0
	_last_pos = 0.0
	_last_t = 0.0
	_running = true
	_start_ticks = Time.get_ticks_usec()
	_music.play()

func stop() -> void:
	_running = false
	_music.stop()

## Game time now: seconds since the loop started, as heard.
func now() -> float:
	if not _running:
		return 0.0
	var t: float
	if _dummy:
		t = (Time.get_ticks_usec() - _start_ticks) / 1e6
	else:
		var pos := _music.get_playback_position() + AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()
		if pos < _last_pos - _loop_len * 0.5:
			_loops += 1
		_last_pos = pos
		t = _loops * _loop_len + pos
	# Never run backwards.
	t = maxf(t, _last_t)
	_last_t = t
	return t

## Call once a frame; inputs in that frame are timed from it.
func mark_frame() -> void:
	_frame_ticks = Time.get_ticks_usec()
	_frame_t = now()

## Game time of an input that arrived now, corrected by the player's calibration.
func input_time() -> float:
	var t := _frame_t + (Time.get_ticks_usec() - _frame_ticks) / 1e6
	return t - calibration_ms / 1000.0

func play(name: String, pitch := 1.0, volume_db := 0.0) -> void:
	if not _sfx.has(name):
		return
	var p := _players[_next_player]
	_next_player = (_next_player + 1) % _players.size()
	p.stream = _sfx[name]
	p.pitch_scale = pitch
	p.volume_db = volume_db
	p.play()

# --- Synthesis -------------------------------------------------------------

func _wav(samples: PackedFloat32Array, loop := false) -> AudioStreamWAV:
	var bytes := PackedByteArray()
	bytes.resize(samples.size() * 2)
	for i in samples.size():
		bytes.encode_s16(i * 2, int(clampf(samples[i], -1.0, 1.0) * 32000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = bytes
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = samples.size()
	return w

func _add_tone(buf: PackedFloat32Array, at: float, freq: float, dur: float, gain: float, shape := "sine", sweep_to := -1.0) -> void:
	var start := int(at * RATE)
	var n := int(dur * RATE)
	var phase := 0.0
	for i in n:
		var idx := start + i
		if idx < 0 or idx >= buf.size():
			continue
		var x := float(i) / n
		var f := freq if sweep_to < 0.0 else lerpf(freq, sweep_to, x)
		phase += f / RATE
		var env := minf(1.0, i / (0.004 * RATE)) * pow(1.0 - x, 3.0)
		var v: float
		match shape:
			"square": v = 1.0 if fmod(phase, 1.0) < 0.5 else -1.0
			"saw": v = 2.0 * fmod(phase, 1.0) - 1.0
			"tri": v = 4.0 * absf(fmod(phase, 1.0) - 0.5) - 1.0
			_: v = sin(phase * TAU)
		buf[idx] += v * gain * env

func _add_noise(buf: PackedFloat32Array, at: float, dur: float, gain: float, smooth := 0.5) -> void:
	var start := int(at * RATE)
	var n := int(dur * RATE)
	var y := 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for i in n:
		var idx := start + i
		if idx >= buf.size():
			break
		y = lerpf(y, rng.randf_range(-1.0, 1.0), smooth)
		buf[idx] += y * gain * pow(1.0 - float(i) / n, 2.0)

## One bar of the pulse: a wooden knock on every beat (accented on the one), a low thump,
## and a drone in a minor Appalachian figure across four bars.
func _build_bar(bars: int) -> AudioStreamWAV:
	var total := bar_len * bars
	var buf := PackedFloat32Array()
	buf.resize(int(total * RATE))
	var roots := [55.0, 55.0, 49.0, 41.2]
	for b in bars:
		var root: float = roots[b % 4]
		var bt := b * bar_len
		# Drone: a sawtooth softened by summing a few detuned partials.
		for i in int(bar_len * RATE):
			var t := float(i) / RATE
			var env := minf(1.0, t / 0.08) * minf(1.0, (bar_len - t) / 0.1)
			var v := 0.0
			for h in [1.0, 1.5, 2.0]:
				v += sin(TAU * root * h * t) / h + 0.3 * sin(TAU * root * h * 2.0 * t) / (h * 2.0)
			buf[int(bt * RATE) + i] += v * 0.045 * env
		for k in BEATS_PER_BAR:
			var at := bt + k * period
			var down := k == 0
			_add_tone(buf, at, 1180.0 if down else 880.0, 0.05, 0.32 if down else 0.2, "tri")
			_add_tone(buf, at, 130.0, 0.16, 0.55 if down else 0.32, "sine", 45.0)
			if k % 2 == 1:
				_add_tone(buf, at, root * 4.0, 0.14, 0.05, "saw")
	return _wav(buf, true)

func _build_sfx() -> void:
	var mk := func(dur: float) -> PackedFloat32Array:
		var b := PackedFloat32Array()
		b.resize(int(dur * RATE))
		return b
	var b: PackedFloat32Array
	b = mk.call(0.2); _add_tone(b, 0, 660, 0.14, 0.3, "square"); _add_noise(b, 0, 0.08, 0.25, 0.9); _sfx["hit"] = _wav(b)
	b = mk.call(0.15); _add_noise(b, 0, 0.12, 0.35, 0.25); _sfx["hit-off"] = _wav(b)
	b = mk.call(0.4); _add_tone(b, 0, 130, 0.3, 0.9, "sine", 40); _add_noise(b, 0, 0.3, 0.4, 0.15); _sfx["heavy"] = _wav(b)
	b = mk.call(0.6); _add_tone(b, 0, 1560, 0.5, 0.25); _add_tone(b, 0, 2340, 0.35, 0.15); _add_tone(b, 0, 3120, 0.2, 0.08); _sfx["parry"] = _wav(b)
	b = mk.call(0.2); _add_tone(b, 0, 300, 0.15, 0.25, "square"); _sfx["block"] = _wav(b)
	b = mk.call(0.4); _add_noise(b, 0, 0.3, 0.6, 0.12); _add_tone(b, 0, 130, 0.25, 0.7, "sine", 45); _sfx["hurt"] = _wav(b)
	b = mk.call(0.15); _add_tone(b, 0, 180, 0.12, 0.15, "saw"); _sfx["fumble"] = _wav(b)
	b = mk.call(0.15); _add_noise(b, 0, 0.12, 0.12, 0.6); _sfx["whiff"] = _wav(b)
	b = mk.call(0.9); _add_tone(b, 0, 98, 0.8, 0.35, "saw"); _add_tone(b, 0, 147, 0.8, 0.2, "saw"); _sfx["stagger"] = _wav(b)
	b = mk.call(0.5); _add_tone(b, 0, 220, 0.4, 0.2, "tri"); _add_tone(b, 0.06, 330, 0.35, 0.12, "tri"); _sfx["stance"] = _wav(b)
	b = mk.call(1.1); _add_tone(b, 0, 70, 1.0, 0.25, "saw", 110); _add_noise(b, 0, 1.0, 0.06, 0.05); _sfx["growl"] = _wav(b)
	b = mk.call(1.4); _add_tone(b, 0, 196, 1.2, 0.2, "tri"); _add_tone(b, 0.15, 247, 1.0, 0.15, "tri"); _add_tone(b, 0.3, 294, 1.0, 0.15, "tri"); _sfx["fell"] = _wav(b)
	b = mk.call(1.6); _add_tone(b, 0, 294, 1.5, 0.2, "tri"); _add_tone(b, 0.2, 392, 1.4, 0.15, "tri"); _sfx["done"] = _wav(b)
