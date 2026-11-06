#!/usr/bin/env python3
"""WILDLINE placeholder score: a small synthesizer and the pieces written for it.

Everything is made here, from numbers: no samples, no libraries beyond numpy. The pieces are
composed (a key, a chord progression, a melody written as notes, a bass, a form that loops),
then rendered through additive voices, a Schroeder reverb and a gentle compressor, and written
as 16-bit 44.1 kHz WAV. Loops carry a `smpl` chunk so Godot's importer loops them by itself.

    python3 tools/score/compose.py                 # render everything to game/assets/music/
    python3 tools/score/compose.py title fight     # only those pieces
    python3 tools/score/compose.py --out /tmp/x    # elsewhere
    python3 tools/score/compose.py --stereo        # twice the size, wider
    python3 tools/score/compose.py --ogg           # also write .ogg beside each .wav (needs ffmpeg)

The whole score shares one motif (MOTIF below), two tempos (60 and 120, one the double of the
other) and one key family around D minor, so the fight layer can play over any zone piece.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import wave

import numpy as np

SR = 44100
TWO_PI = 2.0 * math.pi
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(ROOT, "game", "assets", "music")

# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------


def midi_to_hz(m: float) -> float:
    return 440.0 * 2.0 ** ((m - 69.0) / 12.0)


def db(x: float) -> float:
    return 10.0 ** (x / 20.0)


def samples(seconds: float) -> int:
    return int(round(seconds * SR))


def time_axis(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) / SR


def adsr(n: int, a: float, d: float, s: float, r: float, curve: float = 1.0) -> np.ndarray:
    """An envelope of n sustained samples plus the release tail; total length n + r."""
    na, nd, nr = samples(a), samples(d), samples(r)
    na = max(na, 1)
    nd = max(nd, 1)
    env = np.ones(n + nr)
    att = np.linspace(0.0, 1.0, na, endpoint=False) ** curve
    if na >= n:
        env[:n] = att[:n]
    else:
        env[:na] = att
        dec = np.linspace(1.0, s, nd)
        end = min(na + nd, n)
        env[na:end] = dec[: end - na]
        env[end:n] = s if end >= na + nd else env[end - 1]
    last = env[n - 1] if n > 0 else 1.0
    env[n:] = last * np.exp(-np.linspace(0.0, 6.0, nr)) if nr else env[n:]
    return env


def fft_filter(x: np.ndarray, lo: float | None = None, hi: float | None = None, slope: float = 1.0) -> np.ndarray:
    """A smooth band-pass by spectral masking (no recursion, so it is fast and exact)."""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    mask = np.ones_like(f)
    eps = 1e-9
    if lo:
        mask *= 1.0 / (1.0 + (lo / (f + eps)) ** (2.0 * slope))
    if hi:
        mask *= 1.0 / (1.0 + (f / hi) ** (2.0 * slope))
    return np.fft.irfft(spec * mask, n)


def noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(n)


def pink(n: int, rng: np.random.Generator) -> np.ndarray:
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    spec[1:] /= np.sqrt(f[1:])
    spec[0] = 0.0
    y = np.fft.irfft(spec, n)
    return y / (np.max(np.abs(y)) + 1e-9)


# --------------------------------------------------------------------------------------
# Voices. Each returns a mono float array: the note and its tail.
# --------------------------------------------------------------------------------------


def fit_period(hz: float, period: float | None) -> float:
    """Round a frequency so whole cycles fit the period (a loop), when there is one."""
    if not period:
        return hz
    return max(round(hz * period), 1) / period


def partial_sum(freq: float, n: int, partials, detunes_cents=(0.0,), vibrato=(0.0, 0.0, 0.0), decay=None, bright_in=0.0, period=None):
    """Additive synthesis. partials: [(ratio, amp)]. decay: fn(ratio) -> per-second rate, or None.
    vibrato: (rate hz, depth fraction, onset s). bright_in: seconds for high partials to bloom.
    period: a loop length in seconds; every frequency is then fitted to it so the sound wraps."""
    t = time_axis(n)
    out = np.zeros(n)
    vib = np.zeros(n)
    if vibrato[1] > 0:
        rate, depth, onset = vibrato
        ramp = np.clip((t - onset) / max(onset, 0.05), 0.0, 1.0)
        if period:
            ramp = 1.0
        vib = depth * ramp * np.sin(TWO_PI * fit_period(rate, period) * t)
    for cents in detunes_cents:
        f0 = fit_period(freq * 2.0 ** (cents / 1200.0), period)
        phase_base = np.cumsum(TWO_PI * f0 * (1.0 + vib) / SR)
        for ratio, amp in partials:
            if f0 * ratio > SR * 0.45:
                continue
            a = amp
            wave_ = np.sin(phase_base * ratio)
            if decay is not None:
                wave_ *= np.exp(-decay(ratio) * t)
            if bright_in > 0 and ratio > 1.0:
                wave_ *= 1.0 - np.exp(-t / (bright_in * ratio ** 0.5))
            out += a * wave_
    return out / len(detunes_cents)


def harmonic_series(count: int, rolloff: float = 1.0, lowpass_k: float | None = None):
    ps = []
    for k in range(1, count + 1):
        a = 1.0 / k ** rolloff
        if lowpass_k:
            a /= 1.0 + (k / lowpass_k) ** 2
        ps.append((float(k), a))
    return ps


def v_organ(freq, dur, vel, rng):
    n = samples(dur)
    env = adsr(n, 0.09, 0.1, 0.9, 0.45)
    ps = [(1, 1.0), (2, 0.55), (3, 0.3), (4, 0.28), (6, 0.1), (8, 0.06)]
    y = partial_sum(freq, len(env), ps, detunes_cents=(-1.5, 1.5))
    t = time_axis(len(env))
    trem = 1.0 + 0.025 * np.sin(TWO_PI * 5.3 * t)
    return y * env * trem * vel * 0.25


def v_harmonium(freq, dur, vel, rng):
    n = samples(dur)
    env = adsr(n, 0.18, 0.2, 0.85, 0.5)
    ps = [(1, 1.0), (2, 0.35), (3, 0.5), (4, 0.15), (5, 0.3), (6, 0.08), (7, 0.14), (9, 0.07)]
    y = partial_sum(freq, len(env), ps, detunes_cents=(-2.5, 2.5))
    t = time_axis(len(env))
    trem = 1.0 + 0.04 * np.sin(TWO_PI * 4.2 * t)
    breath = fft_filter(noise(len(env), rng), 800, 3000) * 0.004
    return (y * trem + breath) * env * vel * 0.22


def v_pluck(freq, dur, vel, rng):
    """A harp or lute: harmonics that die faster the higher they are, and a pick transient."""
    n = samples(max(dur, 0.1))
    tail = samples(1.2)
    total = n + tail
    ps = harmonic_series(14, 1.15)
    y = partial_sum(freq, total, ps, decay=lambda k: 1.6 + 1.1 * k + 0.004 * freq)
    env = adsr(n, 0.003, 0.05, 1.0, 1.2)
    pick = fft_filter(noise(samples(0.008), rng), 1500, 6000) * 0.08
    y[: len(pick)] += pick * vel
    return y * env * vel * 0.5


def v_music_box(freq, dur, vel, rng):
    n = samples(max(dur, 0.1))
    tail = samples(1.6)
    total = n + tail
    ps = [(1.0, 1.0), (2.76, 0.22), (5.4, 0.08), (8.93, 0.03), (4.0, 0.12)]
    y = partial_sum(freq, total, ps, decay=lambda k: 2.0 + 1.5 * k)
    env = adsr(n, 0.001, 0.02, 1.0, 1.6)
    return y * env * vel * 0.5


def v_bell(freq, dur, vel, rng):
    n = samples(max(dur, 0.1))
    tail = samples(3.0)
    total = n + tail
    ps = [(0.5, 0.35), (1.0, 1.0), (1.183, 0.5), (1.506, 0.45), (2.0, 0.35), (2.514, 0.25),
          (2.662, 0.2), (3.011, 0.15), (4.166, 0.08), (5.433, 0.05)]
    y = partial_sum(freq, total, ps, decay=lambda k: 0.5 + 0.6 * k)
    env = adsr(n, 0.002, 0.05, 1.0, 3.0)
    strike = fft_filter(noise(samples(0.01), rng), 2000, 9000) * 0.06
    y[: len(strike)] += strike * vel
    return y * env * vel * 0.4


def v_drone(freq, dur, vel, rng, period=None):
    n = samples(dur)
    env = adsr(n, 1.5, 0.5, 1.0, 2.0)
    ps = harmonic_series(18, 1.0, lowpass_k=5.0)
    y = partial_sum(freq, len(env), ps, detunes_cents=(-7.0, -3.0, 0.0, 3.5, 7.5), period=period)
    t = time_axis(len(env))
    lfo = 1.0 + 0.06 * np.sin(TWO_PI * fit_period(0.11, period) * t) + 0.03 * np.sin(TWO_PI * fit_period(0.071, period) * t + 1.0)
    return y * env * lfo * vel * 0.35


def v_strings(freq, dur, vel, rng):
    n = samples(dur)
    env = adsr(n, 0.3, 0.25, 0.85, 0.7, curve=1.4)
    ps = harmonic_series(16, 1.0, lowpass_k=7.0)
    y = partial_sum(freq, len(env), ps, detunes_cents=(-6.0, 0.0, 6.5), vibrato=(5.1, 0.0035, 0.35))
    bow = fft_filter(noise(len(env), rng), 1500, 5000) * 0.006
    return (y + bow) * env * vel * 0.24


def v_cello(freq, dur, vel, rng):
    n = samples(dur)
    env = adsr(n, 0.08, 0.15, 0.8, 0.3, curve=1.2)
    ps = harmonic_series(20, 0.9, lowpass_k=6.0)
    y = partial_sum(freq, len(env), ps, detunes_cents=(-3.0, 3.0), vibrato=(4.6, 0.003, 0.25))
    bow = fft_filter(noise(len(env), rng), 600, 3000) * 0.01
    return (y + bow) * env * vel * 0.36


def v_brass(freq, dur, vel, rng):
    n = samples(dur)
    env = adsr(n, 0.07, 0.18, 0.8, 0.3, curve=0.8)
    ps = harmonic_series(18, 0.8, lowpass_k=9.0)
    y = partial_sum(freq, len(env), ps, detunes_cents=(-2.0, 2.0), vibrato=(4.7, 0.004, 0.5), bright_in=0.07)
    return np.tanh(y * 1.4 * env) * env * vel * 0.42


def v_horn(freq, dur, vel, rng):
    """A softer brass, for warmth rather than a call."""
    n = samples(dur)
    env = adsr(n, 0.12, 0.2, 0.8, 0.4, curve=1.0)
    ps = harmonic_series(12, 1.1, lowpass_k=5.0)
    y = partial_sum(freq, len(env), ps, detunes_cents=(-2.0, 2.0), vibrato=(4.4, 0.003, 0.5), bright_in=0.12)
    return y * env * vel * 0.44


def v_glass(freq, dur, vel, rng, period=None):
    """A high harmonic shimmer: a bowed glass or a far-off string harmonic."""
    n = samples(dur)
    env = adsr(n, 0.6, 0.3, 0.8, 1.2, curve=1.6)
    ps = [(1, 1.0), (2, 0.15), (3, 0.05)]
    y = partial_sum(freq, len(env), ps, detunes_cents=(-4.0, 4.0), vibrato=(3.8, 0.002, 0.8), period=period)
    return y * env * vel * 0.3


# Percussion


def p_kick(vel, rng, low=46.0, high=120.0):
    n = samples(0.45)
    t = time_axis(n)
    f = low + (high - low) * np.exp(-t / 0.045)
    phase = np.cumsum(TWO_PI * f / SR)
    y = np.sin(phase) * np.exp(-t / 0.13)
    click = fft_filter(noise(samples(0.005), rng), 1000, 5000) * 0.3
    y[: len(click)] += click
    return y * vel * 0.9


def p_taiko(vel, rng):
    n = samples(1.1)
    t = time_axis(n)
    f = 58.0 + 40.0 * np.exp(-t / 0.03)
    phase = np.cumsum(TWO_PI * f / SR)
    y = (np.sin(phase) + 0.3 * np.sin(2.01 * phase)) * np.exp(-t / 0.33)
    skin = fft_filter(noise(n, rng), 150, 1200) * np.exp(-t / 0.05) * 0.5
    return (y + skin) * vel * 0.9


def p_brush(vel, rng, attack=0.012, decay=0.17):
    n = samples(attack + decay * 6)
    t = time_axis(n)
    env = np.minimum(t / attack, 1.0) * np.exp(-np.maximum(t - attack, 0.0) / decay)
    y = fft_filter(noise(n, rng), 700, 6000) * env
    body = np.sin(TWO_PI * 185 * t) * np.exp(-t / 0.05) * 0.4
    return (y * 0.35 + body) * vel


def p_sweep(vel, rng):
    """A brush sweep across the head."""
    n = samples(0.5)
    t = time_axis(n)
    env = np.sin(np.pi * t / 0.5) ** 2
    return fft_filter(noise(n, rng), 1500, 8000) * env * vel * 0.12


def p_shaker(vel, rng, decay=0.045):
    n = samples(decay * 7)
    t = time_axis(n)
    env = np.minimum(t / 0.004, 1.0) * np.exp(-t / decay)
    return fft_filter(noise(n, rng), 5000, 14000) * env * vel * 0.25


def p_iron(vel, rng, base=1100.0, decay=0.35):
    """A hammer on rail iron: inharmonic, bright, short."""
    n = samples(decay * 6)
    t = time_axis(n)
    ps = [(1.0, 1.0), (1.71, 0.7), (2.93, 0.5), (4.37, 0.3), (6.12, 0.2), (8.4, 0.1)]
    y = partial_sum(base, n, ps, decay=lambda k: (1.0 / decay) * (0.5 + 0.5 * k))
    clank = fft_filter(noise(samples(0.012), rng), 2500, 12000) * 0.6
    y[: len(clank)] += clank
    return y * vel * 0.4


def p_tom(vel, rng, freq=110.0):
    n = samples(0.5)
    t = time_axis(n)
    f = freq * (1.0 + 0.6 * np.exp(-t / 0.03))
    phase = np.cumsum(TWO_PI * f / SR)
    y = np.sin(phase) * np.exp(-t / 0.18)
    skin = fft_filter(noise(n, rng), 300, 2000) * np.exp(-t / 0.03) * 0.3
    return (y + skin) * vel * 0.7


def p_cymbal(vel, rng, swell=1.5, ring=1.8):
    n = samples(swell + ring * 4)
    t = time_axis(n)
    env = np.where(t < swell, (t / swell) ** 2, np.exp(-(t - swell) / ring))
    return fft_filter(noise(n, rng), 2500, 12000) * env * vel * 0.2


def tex_water(n, rng):
    """Moving water: pink noise, a band of it bubbling, and a slow swell of the whole."""
    t = time_axis(n)
    base = fft_filter(pink(n, rng), 120, 2500)
    swell = 0.7 + 0.3 * np.sin(TWO_PI * 0.07 * t) * np.sin(TWO_PI * 0.043 * t + 0.7)
    bub = fft_filter(noise(n, rng), 350, 1400)
    mod = np.zeros(n)
    for r, ph in [(5.3, 0.1), (7.9, 1.2), (11.1, 2.3), (3.2, 0.5)]:
        mod += np.maximum(np.sin(TWO_PI * r * t + ph), 0.0) ** 6
    return base * swell + bub * mod * 0.25


def tex_wind(n, rng):
    t = time_axis(n)
    w = fft_filter(noise(n, rng), 180, 900)
    lfo = 0.5 + 0.5 * np.sin(TWO_PI * 0.05 * t) * np.sin(TWO_PI * 0.031 * t + 2.0)
    return w * (0.3 + 0.7 * lfo ** 2)


# --------------------------------------------------------------------------------------
# Effects: a Schroeder reverb (block-vectorised combs and allpasses), a compressor, a limiter.
# --------------------------------------------------------------------------------------


def comb(x: np.ndarray, delay: int, g: float) -> np.ndarray:
    y = np.zeros_like(x)
    n = len(x)
    for i in range(0, n, delay):
        seg = x[i : i + delay].copy()
        if i >= delay:
            seg += g * y[i - delay : i - delay + len(seg)]
        y[i : i + len(seg)] = seg
    return y


def allpass(x: np.ndarray, delay: int, g: float) -> np.ndarray:
    y = np.zeros_like(x)
    n = len(x)
    for i in range(0, n, delay):
        seg = -g * x[i : i + delay]
        if i >= delay:
            seg = seg + x[i - delay : i - delay + len(seg)] + g * y[i - delay : i - delay + len(seg)]
        y[i : i + len(seg)] = seg
    return y


def reverb(x: np.ndarray, size: float = 1.0, damp_hz: float = 5000.0, decay: float = 0.84, seed: int = 0) -> np.ndarray:
    """Four combs in parallel then two allpasses, on a darkened copy of the input. size scales the
    delays (1.0 is a hall, 0.5 a room). Returns the wet signal only."""
    inp = fft_filter(x, 90, damp_hz)
    combs = [1557, 1617, 1491, 1422]
    aps = [225, 556]
    offs = [0, 23, -17, 31][seed % 4]
    wet = np.zeros_like(x)
    for d in combs:
        dd = max(int(d * size) + offs, 50)
        wet += comb(inp, dd, decay)
    wet *= 0.25 * (1.0 - decay) * 5.0  # about 1.25x the input's level when it sustains
    for d in aps:
        wet = allpass(wet, max(int(d * size), 20), 0.5)
    return wet


def compress(x: np.ndarray, threshold_db=-14.0, ratio=2.5, attack=0.01, release=0.25, block=128) -> np.ndarray:
    """A gentle feed-forward compressor on block peaks, smoothed, then interpolated."""
    n = len(x)
    nb = (n + block - 1) // block
    pad = np.zeros(nb * block)
    pad[:n] = x
    peaks = np.max(np.abs(pad.reshape(nb, block)), axis=1) + 1e-9
    lvl = 20 * np.log10(peaks)
    over = np.maximum(lvl - threshold_db, 0.0)
    gain_db = -over * (1.0 - 1.0 / ratio)
    a = math.exp(-block / (attack * SR))
    r = math.exp(-block / (release * SR))
    g = 0.0
    sm = np.zeros(nb)
    for i in range(nb):
        target = gain_db[i]
        g = a * g + (1 - a) * target if target < g else r * g + (1 - r) * target
        sm[i] = g
    gain = np.interp(np.arange(n), np.arange(nb) * block + block / 2, 10 ** (sm / 20))
    return x * gain


def limiter(x: np.ndarray, ceiling_db=-1.5) -> np.ndarray:
    """Normalise the peak to the ceiling: every file leaves at the same peak, and the score's
    balance between pieces is set by the gain in data/music.json, not baked in."""
    c = db(ceiling_db)
    peak = np.max(np.abs(x)) + 1e-9
    return np.clip(x * (c / peak), -c, c)


# --------------------------------------------------------------------------------------
# The composition layer
# --------------------------------------------------------------------------------------

SCALES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "major": [0, 2, 4, 5, 7, 9, 11],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
}

# The motif the whole score shares, as (scale degree, beats). Degrees are 1-based; 8 is the
# octave; a degree below 1 goes under the tonic. In D minor it sings D F A D' | C A G F | E D.
MOTIF = [(1, 1), (3, 1), (5, 1), (8, 2), (7, 0.5), (5, 0.5), (4, 1), (3, 1), (2, 1), (1, 3)]
MOTIF_ANSWER = [(5, 1), (6, 1), (5, 1), (3, 2), (4, 0.5), (3, 0.5), (2, 1), (1, 1), (0, 1), (1, 3)]


def deg(scale: list[int], tonic_midi: int, degree: int) -> int:
    """Scale degree (1-based, any octave; 0 and negatives go below) to a midi note."""
    i = degree - 1
    octave, idx = divmod(i, 7)
    return tonic_midi + 12 * octave + scale[idx]


class Piece:
    """A score: notes placed on a beat grid, rendered into a mix with reverb sends."""

    def __init__(self, name: str, tempo: float, beats_per_bar: int, bars: float, seed: int, loop: bool = True, seconds: float | None = None):
        self.name = name
        self.tempo = tempo
        self.bpb = beats_per_bar
        self.bars = bars
        self.loop = loop
        self.rng = np.random.default_rng(seed)
        self.beat = 60.0 / tempo
        self.length = seconds if seconds else self.beat * beats_per_bar * bars  # seconds
        self.n = samples(self.length)
        self.tail = samples(5.0)
        self.dry = np.zeros(self.n + self.tail)
        self.wet = {}  # reverb name -> send buffer
        self.events = 0

    # -- placing sound ---------------------------------------------------------------
    def place(self, y: np.ndarray, at_seconds: float, gain: float = 1.0, send: dict | None = None, fade: bool = True):
        start = samples(at_seconds)
        if start < 0:
            y = y[-start:]
            start = 0
        end = min(start + len(y), len(self.dry))
        if end <= start:
            return
        seg = y[: end - start] * gain
        k = min(64, len(seg))  # every sound begins from silence: no clicks, and a clean seam
        if fade and k and abs(seg[0]) > 1e-6:
            seg = seg.copy()
            seg[:k] *= np.linspace(0.0, 1.0, k)
        self.dry[start:end] += seg
        for name, amt in (send or {}).items():
            buf = self.wet.setdefault(name, np.zeros_like(self.dry))
            buf[start:end] += seg * amt
        self.events += 1

    def note(self, voice, midi: float, beat: float, dur_beats: float, vel: float = 0.8, gain: float = 1.0, send=None, humanize=0.012):
        t = beat * self.beat + self.rng.uniform(-humanize, humanize)
        v = vel * self.rng.uniform(0.94, 1.0)
        y = voice(midi_to_hz(midi), dur_beats * self.beat, v, self.rng)
        self.place(y, max(t, 0.0), gain, send)

    def hit(self, drum, beat: float, vel: float = 0.8, gain: float = 1.0, send=None, humanize=0.006, **kw):
        t = beat * self.beat + self.rng.uniform(-humanize, humanize)
        self.place(drum(vel * self.rng.uniform(0.92, 1.0), self.rng, **kw), max(t, 0.0), gain, send)

    def melody(self, voice, notes, scale, tonic, start_beat, vel=0.8, gain=1.0, send=None, legato=0.95, swell=None):
        """notes: [(degree, beats)]; degree None is a rest. swell: fn(fraction) -> velocity factor."""
        b = start_beat
        total = sum(d for _, d in notes)
        for degree, beats in notes:
            if degree is not None:
                frac = (b - start_beat) / total
                v = vel * (swell(frac) if swell else 1.0)
                self.note(voice, deg(scale, tonic, degree), b, beats * legato, v, gain, send)
            b += beats
        return b

    def chord(self, voice, midis, beat, dur_beats, vel=0.6, gain=1.0, send=None, spread=0.0):
        for i, m in enumerate(midis):
            self.note(voice, m, beat + i * spread, dur_beats, vel, gain, send)

    def drone(self, voice, midi, gain=1.0, send=None, vel=0.6):
        """A sound that lasts the whole loop, its pitch quantised so whole cycles fit the loop."""
        hz = midi_to_hz(midi)
        if not self.loop:
            self.place(voice(hz, self.length, vel, self.rng), 0.0, gain, send)
            return
        # Render past the attack and take the steady middle, every frequency fitted to the loop.
        lead = 2.5
        y = voice(hz, self.length + lead + 1.0, vel, self.rng, period=self.length)
        self.place(y[samples(lead) : samples(lead) + self.n], 0.0, gain, send, fade=False)

    def texture(self, fn, gain=1.0, send=None):
        if not self.loop:
            self.place(fn(self.n, self.rng), 0.0, gain, send)
            return
        # A texture loops on itself: its last second is blended into its first.
        k = samples(1.0)
        y = fn(self.n + k, self.rng)
        w = np.linspace(0.0, 1.0, k)
        head = y[:k] * w + y[self.n : self.n + k] * (1.0 - w)
        y = y[: self.n].copy()
        y[:k] = head
        self.place(y, 0.0, gain, send, fade=False)

    # -- rendering ---------------------------------------------------------------------
    def render(self, reverbs: dict, master_db: float = 0.0, comp=(-14.0, 2.5)) -> np.ndarray:
        mix = self.dry.copy()
        wet_all = np.zeros_like(mix)
        for name, buf in self.wet.items():
            spec = reverbs[name]
            wet_all += reverb(buf, **spec)
        rms = lambda a: 20 * math.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
        print(f"  {self.name}: {self.events} events, dry {rms(self.dry):.1f} dB, wet {rms(wet_all):.1f} dB", flush=True)
        mix += wet_all
        if self.loop:
            out = mix[: self.n].copy()
            out[: self.tail] += mix[self.n : self.n + self.tail]  # the tail falls onto the start
            # Tails wrapped, the loop is a continuous process; notes that start at 0 begin from
            # silence, so the seam is the quiet of the last sample meeting the start of the first.
        else:
            # A stinger is cut to its length and ends in silence: its last 200 ms fade.
            out = mix[: self.n].copy()
            k = samples(0.2)
            out[-k:] *= np.linspace(1.0, 0.0, k) ** 1.5
        out = fft_filter(out, lo=24.0, slope=2.0)  # no rumble, no offset
        out -= np.mean(out)
        if self.loop:
            # The compressor settles over the loop once, then its second pass is kept: no gain step at the seam.
            out = compress(np.concatenate([out, out]), comp[0], comp[1])[len(out):]
        else:
            out = compress(out, comp[0], comp[1])
        out *= db(master_db)
        return limiter(out)


# --------------------------------------------------------------------------------------
# Keys, tempos and reverbs shared by the score
# --------------------------------------------------------------------------------------

D2, D3, D4, D5 = 38, 50, 62, 74
F3, F4 = 53, 65
HALL = {"hall": dict(size=1.0, damp_hz=5000.0, decay=0.86, seed=0),
        "room": dict(size=0.45, damp_hz=6000.0, decay=0.7, seed=1),
        "cavern": dict(size=1.6, damp_hz=3200.0, decay=0.9, seed=2),
        "plate": dict(size=0.7, damp_hz=8000.0, decay=0.8, seed=3)}


def tri(midis, scale, tonic, degree, kind=None):
    """A triad on a scale degree: midi notes for root, third, fifth from the scale."""
    return [deg(scale, tonic, degree), deg(scale, tonic, degree + 2), deg(scale, tonic, degree + 4)]


def chord_from(scale, tonic, degree, voicing=(0, 2, 4), octave=0):
    return [deg(scale, tonic, degree + v) + 12 * octave for v in voicing]


def arc(peak_at=0.6, floor=0.7):
    """A velocity swell over the form: rises to peak_at, relaxes to the loop's end."""
    def f(x):
        return floor + (1.0 - floor) * math.sin(math.pi * min(x / peak_at, 1.0) * 0.5) if x < peak_at else floor + (1.0 - floor) * (1.0 - (x - peak_at) / (1.0 - peak_at)) ** 0.8
    return f


# --------------------------------------------------------------------------------------
# The pieces
# --------------------------------------------------------------------------------------


def piece_title():
    """The title: slow, wide, the motif alone over a drone, then with strings and a far horn."""
    p = Piece("title", 60, 4, 10, seed=1)
    sc = SCALES["minor"]
    p.drone(v_drone, D2, gain=0.55, send={"cavern": 0.5})
    p.drone(v_glass, D5 + 12, gain=0.07, send={"cavern": 0.9})
    prog = [1, 6, 3, 7, 1, 4, 6, 7, 1, 5]  # Dm Bb F C Dm Gm Bb C Dm A(sus)
    for bar, degree in enumerate(prog):
        notes = chord_from(sc, D3, degree)
        if bar == 9:
            notes = [deg(sc, D3, 5), deg(sc, D3, 8), deg(sc, D3, 9)]  # A sus: A D E
        vel = 0.45 if bar < 4 else 0.6
        p.chord(v_strings, notes, bar * 4, 4.0, vel=vel, send={"hall": 0.6}, spread=0.04)
        if bar >= 4:
            p.chord(v_strings, [m + 12 for m in notes[:2]], bar * 4, 4.0, vel=0.3, send={"hall": 0.7}, spread=0.06)
    # The motif: a horn alone the first time, horn and strings the second.
    p.melody(v_horn, MOTIF, sc, D4, 0, vel=0.55, send={"hall": 0.75}, swell=arc(0.4, 0.75))
    p.melody(v_horn, MOTIF, sc, D4 + 12, 16, vel=0.6, send={"hall": 0.7}, swell=arc(0.5, 0.8))
    p.melody(v_strings, MOTIF, sc, D4, 16, vel=0.4, send={"hall": 0.7})
    p.melody(v_horn, MOTIF_ANSWER, sc, D4 + 12, 28, vel=0.5, send={"hall": 0.7}, swell=arc(0.3, 0.7))
    # A harp answers at the bars' turns.
    for bar in (1, 3, 5, 7):
        notes = chord_from(sc, D4, prog[bar])
        for i, m in enumerate(notes + [notes[0] + 12]):
            p.note(v_pluck, m, bar * 4 + 2 + i * 0.5, 1.5, vel=0.35, send={"hall": 0.6})
    for bar in (0, 4, 8):
        p.hit(p_taiko, bar * 4, vel=0.45, send={"cavern": 0.5})
    return p.render(HALL, master_db=0.0)


def piece_academy_quad():
    """The quad in the evening: a harp over a harmonium, the motif in F major, unhurried."""
    p = Piece("academy_quad", 60, 4, 9, seed=2)
    sc = SCALES["major"]
    T = F3
    p.drone(v_drone, F3 - 12, gain=0.25, send={"hall": 0.4})
    prog = [1, 4, 6, 5, 1, 3, 4, 2, 5]  # F Bb Dm C F Am Bb Gm C7
    for bar, degree in enumerate(prog):
        notes = chord_from(sc, T, degree)
        if bar == 8:
            notes = chord_from(sc, T, 5, voicing=(0, 2, 4, 6))
        p.chord(v_harmonium, notes, bar * 4, 4.0, vel=0.42, send={"room": 0.5, "hall": 0.3}, spread=0.03)
        # The harp: a broken chord in eighths, with its own small shape.
        pat = [0, 1, 2, 3, 2, 1, 0, 2]
        arp = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[0] + 24]
        for i, idx in enumerate(pat):
            v = 0.42 if i in (0, 4) else 0.3
            p.note(v_pluck, arp[idx], bar * 4 + i * 0.5, 0.6, vel=v, send={"room": 0.4, "hall": 0.3})
        if bar % 2 == 1:
            p.hit(p_sweep, bar * 4 + 3, vel=0.4, send={"room": 0.3})
    # The motif in the major, on a soft horn, starting the third bar.
    p.melody(v_horn, MOTIF, sc, F4, 8, vel=0.42, send={"hall": 0.6}, swell=arc(0.5, 0.8))
    p.melody(v_pluck, [(3, 1), (5, 1), (6, 1), (5, 1), (3, 1), (2, 1), (1, 2)], sc, F4 + 12, 24, vel=0.4, send={"hall": 0.6})
    return p.render(HALL, master_db=-1.0)


def piece_academy_yard():
    """The training yard: a steady pulse, brushed drums, a low string ostinato, the motif in fragments."""
    p = Piece("academy_yard", 120, 4, 16, seed=3)
    sc = SCALES["dorian"]
    p.drone(v_drone, D2, gain=0.3, send={"room": 0.3})
    ost = [1, 1, 5, 1, 7, 1, 3, 1]  # D D A D C D F D, eighths
    for bar in range(16):
        for i, d in enumerate(ost):
            v = 0.7 if i == 0 else 0.5 if i % 2 == 0 else 0.42
            m = deg(sc, D3 - 12, d) if d != 7 else deg(sc, D3 - 12, 7)
            if bar in (7, 15) and i >= 4:
                m = deg(sc, D3 - 12, [6, 5, 4, 5][i - 4])  # a turn at the phrase end
            p.note(v_cello, m, bar * 4 + i * 0.5, 0.45, vel=v, send={"room": 0.35}, humanize=0.004)
        # Drums: kick 1 and 3, brush 2 and 4, shaker eighths with a lift.
        p.hit(p_kick, bar * 4, vel=0.7, high=100.0)
        p.hit(p_kick, bar * 4 + 2, vel=0.6, high=100.0)
        if bar % 4 == 3:
            p.hit(p_kick, bar * 4 + 3.5, vel=0.35, high=100.0)
        p.hit(p_brush, bar * 4 + 1, vel=0.55, send={"room": 0.4})
        p.hit(p_brush, bar * 4 + 3, vel=0.6, send={"room": 0.4})
        for e in range(8):
            p.hit(p_shaker, bar * 4 + e * 0.5, vel=0.3 if e % 2 else 0.45)
        if bar % 4 == 3:
            p.hit(p_sweep, bar * 4 + 3, vel=0.5, send={"room": 0.4})
    # Chords in strings, one per two bars.
    prog = [1, 1, 7, 7, 6, 6, 5, 5]  # Dm, C, Bm(b5)? in dorian degree 6 is B: use 4 instead
    prog = [1, 1, 7, 7, 4, 4, 5, 5]  # Dm C G Am
    for i, degree in enumerate(prog):
        notes = chord_from(sc, D3, degree)
        p.chord(v_strings, notes, i * 8, 7.6, vel=0.36, send={"hall": 0.45}, spread=0.05)
    # The motif's head on brass, in two calls, and a reply.
    frag = [(1, 1), (3, 1), (5, 1), (8, 2), (7, 0.5), (5, 0.5), (4, 2)]
    p.melody(v_brass, frag, sc, D4, 16, vel=0.5, send={"hall": 0.5})
    p.melody(v_brass, frag, sc, D4 + 12, 32, vel=0.55, send={"hall": 0.5})
    p.melody(v_brass, [(5, 1), (4, 1), (3, 1), (2, 1), (1, 4)], sc, D4 + 12, 48, vel=0.5, send={"hall": 0.5})
    p.melody(v_brass, [(5, 1), (7, 1), (8, 2)], sc, D4, 56, vel=0.45, send={"hall": 0.5})
    return p.render(HALL, master_db=-0.5, comp=(-12.0, 3.0))


def piece_academy_hearth():
    """The hearth hall: an organ alone, hushed, the motif in the minor, a drone under it."""
    p = Piece("academy_hearth", 60, 4, 9, seed=4)
    sc = SCALES["minor"]
    p.drone(v_drone, D2, gain=0.35, send={"hall": 0.5})
    prog = [1, 4, 1, 6, 1, 4, 5, 1, 5]  # Dm Gm Dm Bb Dm Gm A Dm A7sus
    for bar, degree in enumerate(prog):
        notes = chord_from(sc, D3, degree)
        if degree == 5:
            notes = [deg(sc, D3, 5), deg(sc, D3, 7) + 1, deg(sc, D3, 9)]  # A C# E: the leading tone
        if bar == 8:
            notes = [deg(sc, D3, 5), deg(sc, D3, 8), deg(sc, D3, 9), deg(sc, D3, 11)]  # A D E G
        p.chord(v_organ, notes, bar * 4, 3.9, vel=0.5, send={"hall": 0.7}, spread=0.02)
        p.note(v_organ, notes[0] - 12, bar * 4, 3.9, vel=0.45, send={"hall": 0.6})
    p.melody(v_organ, MOTIF, sc, D4 + 12, 4, vel=0.5, send={"hall": 0.75}, swell=arc(0.5, 0.85))
    p.melody(v_organ, MOTIF_ANSWER, sc, D4 + 12, 20, vel=0.45, send={"hall": 0.75}, swell=arc(0.4, 0.8))
    p.melody(v_glass, [(5, 4), (4, 4), (3, 4), (2, 2), (1, 2)], sc, D5 + 12, 16, vel=0.2, send={"hall": 0.9})
    return p.render(HALL, master_db=-2.0)


def piece_academy_dorm():
    """The dormitory at night: a music box over a drone, in three, nearly nothing."""
    p = Piece("academy_dorm", 60, 3, 10, seed=5)
    sc = SCALES["minor"]
    p.drone(v_drone, D2, gain=0.22, send={"cavern": 0.5})
    p.drone(v_glass, deg(sc, D5, 5), gain=0.05, send={"cavern": 0.9})
    p.texture(tex_wind, gain=0.025, send={"cavern": 0.5})
    # The music box: the motif in three, slowly, with a bass note at each bar.
    box = [(1, 1), (3, 1), (5, 1), (8, 3), (7, 1), (5, 1), (4, 1), (3, 2), (2, 1), (1, 3),
           (None, 3), (5, 1), (6, 1), (5, 1), (3, 3), (2, 1), (1, 1), (0, 1), (1, 3), (None, 3)]
    p.melody(v_music_box, box, sc, D5 + 12, 0, vel=0.45, send={"hall": 0.6, "cavern": 0.3}, legato=1.0)
    roots = [1, 6, 3, 7, 1, 4, 6, 5, 1, 1]
    for bar, degree in enumerate(roots):
        p.note(v_music_box, deg(sc, D4, degree), bar * 3, 2.5, vel=0.3, send={"hall": 0.6})
        if bar % 2 == 1:
            p.note(v_music_box, deg(sc, D4, degree + 2), bar * 3 + 1, 1.5, vel=0.22, send={"hall": 0.6})
    return p.render(HALL, master_db=-6.0, comp=(-18.0, 2.0))


def piece_zone_green():
    """The Green hills at night: moonlit strings, a high harmonic, a distant pulse."""
    p = Piece("zone_green", 60, 4, 9, seed=6)
    sc = SCALES["dorian"]
    p.drone(v_drone, D2, gain=0.4, send={"cavern": 0.5})
    p.texture(tex_wind, gain=0.04, send={"cavern": 0.4})
    prog = [1, 4, 1, 2, 1, 4, 5, 1, 7]  # Dm7 G Dm7 Em7 Dm G Am7 Dm C/D
    for bar, degree in enumerate(prog):
        notes = chord_from(sc, D3, degree, voicing=(0, 2, 4, 6))
        if bar == 8:
            notes = [D3, deg(sc, D3, 7), deg(sc, D3, 9), deg(sc, D3, 11)]
        p.chord(v_strings, notes, bar * 4, 4.0, vel=0.42, send={"hall": 0.7}, spread=0.08)
    # A distant pulse: a soft low drum every two beats, barely there, and a far iron ping.
    for b in range(0, 36, 2):
        p.hit(p_kick, b, vel=0.22, low=40.0, high=70.0, send={"cavern": 0.6})
    for b in (7, 15, 23, 31):
        p.hit(p_iron, b + 0.5, vel=0.08, base=2400.0, decay=0.8, send={"cavern": 0.9})
    # A high line, the motif thinned to its bones, on glass.
    line = [(8, 4), (7, 2), (5, 2), (4, 4), (3, 2), (2, 2), (1, 8), (None, 4), (5, 4), (6, 4)]
    p.melody(v_glass, line, sc, D5, 0, vel=0.3, send={"hall": 0.8, "cavern": 0.3}, swell=arc(0.5, 0.7))
    p.melody(v_pluck, [(1, 0.5), (5, 0.5), (8, 0.5), (12, 2.5)], sc, D4, 14, vel=0.3, send={"hall": 0.7})
    p.melody(v_pluck, [(1, 0.5), (5, 0.5), (9, 0.5), (12, 2.5)], sc, D4, 30, vel=0.3, send={"hall": 0.7})
    return p.render(HALL, master_db=-2.5)


def piece_zone_shenandoah():
    """The drowned ruin: water, bells, a slow dissonance that never quite resolves."""
    p = Piece("zone_shenandoah", 60, 4, 9, seed=7)
    sc = SCALES["phrygian"]
    p.texture(tex_water, gain=0.12, send={"cavern": 0.35})
    p.drone(v_drone, D2, gain=0.38, send={"cavern": 0.6})
    p.drone(v_drone, D2 + 1, gain=0.1, send={"cavern": 0.6})  # the Eb against the D, slow beating
    # Bells: D, Ab (the tritone), Eb (the flat second), G, C; slow, each ringing into the next.
    bells = [(D5, 0), (D5 + 6, 5), (D5 + 1, 9), (D5 + 5, 13), (D5 - 2, 17), (D5 + 6, 21), (D5, 25), (D5 + 1, 29), (D5 + 7, 33)]
    for m, b in bells:
        p.note(v_bell, m, b, 1.0, vel=0.42, send={"cavern": 0.8, "hall": 0.3})
    for m, b in [(D4 - 2, 3), (D4 + 1, 11), (D4 - 4, 19), (D4 + 6, 27)]:
        p.note(v_bell, m, b, 1.0, vel=0.28, send={"cavern": 0.8})
    # Strings hold a cluster that leans and returns: D-Eb-G, then D-F-Ab, then D-E-G...
    clusters = [[D3, D3 + 1, D3 + 5], [D3, D3 + 3, D3 + 6], [D3, D3 + 1, D3 + 7], [D3 - 2, D3 + 3, D3 + 5],
                [D3, D3 + 1, D3 + 5], [D3, D3 + 6, D3 + 8], [D3, D3 + 3, D3 + 7], [D3, D3 + 5, D3 + 10], [D3, D3 + 1, D3 + 6]]
    for bar, notes in enumerate(clusters):
        p.chord(v_strings, notes, bar * 4, 4.0, vel=0.3, send={"cavern": 0.7}, spread=0.12)
    # The motif's first four notes, bent to the phrygian, far off, once.
    p.melody(v_glass, [(1, 2), (3, 2), (5, 2), (8, 6)], sc, D4 + 12, 20, vel=0.22, send={"cavern": 0.9})
    return p.render(HALL, master_db=-2.5)


def piece_zone_harpers_cut():
    """The dark junction: iron percussion, a tense ostinato on D and Eb, brass stabs."""
    p = Piece("zone_harpers_cut", 120, 4, 16, seed=8)
    sc = SCALES["phrygian"]
    p.drone(v_drone, D2, gain=0.42, send={"room": 0.3})
    ost = [1, 1, 2, 1, 3, 1, 2, 1, 1, 1, 2, 1, 5, 4, 3, 2]  # sixteenths: D D Eb D F D Eb D ...
    for bar in range(16):
        for i, d in enumerate(ost):
            v = 0.62 if i % 4 == 0 else 0.45
            m = deg(sc, D3 - 12, d)
            if bar % 8 == 7 and i >= 8:
                m = deg(sc, D3 - 12, [6, 5, 4, 3, 2, 1, 2, 1][i - 8])  # the phrase closes
            p.note(v_cello, m, bar * 4 + i * 0.25, 0.22, vel=v, send={"room": 0.3}, humanize=0.003)
        # Iron: a hammer on the off-beats, a heavier one at the bar, a rail ring now and then.
        p.hit(p_kick, bar * 4, vel=0.75, low=42.0, high=110.0)
        p.hit(p_kick, bar * 4 + 2.5, vel=0.5, low=42.0, high=110.0)
        p.hit(p_iron, bar * 4 + 1, vel=0.5, base=900.0, decay=0.25, send={"plate": 0.5})
        p.hit(p_iron, bar * 4 + 3, vel=0.55, base=1300.0, decay=0.3, send={"plate": 0.5})
        if bar % 2 == 1:
            p.hit(p_iron, bar * 4 + 3.5, vel=0.3, base=1900.0, decay=0.2, send={"plate": 0.6})
        if bar % 4 == 3:
            p.hit(p_iron, bar * 4 + 3.75, vel=0.4, base=600.0, decay=0.9, send={"cavern": 0.7})
        for e in range(8):
            p.hit(p_shaker, bar * 4 + e * 0.5, vel=0.2 if e % 2 else 0.3, decay=0.03)
    # The harmony leans from Dm to Eb and back, every two bars, in low strings.
    for i in range(8):
        notes = [D3, D3 + 3, D3 + 7] if i % 2 == 0 else [D3 + 1, D3 + 5, D3 + 8]
        if i == 7:
            notes = [D3 + 1, D3 + 5, D3 + 7]  # Eb with the D's fifth: the pull home
        p.chord(v_strings, notes, i * 8, 7.8, vel=0.3, send={"hall": 0.4}, spread=0.05)
    # Brass stabs: the motif's first three notes, hard, and a long held call.
    for b in (8, 24, 40):
        p.melody(v_brass, [(1, 0.5), (3, 0.5), (5, 1)], sc, D4, b, vel=0.6, send={"plate": 0.4}, legato=0.8)
    p.melody(v_brass, [(8, 3), (7, 1), (5, 2), (2, 2)], sc, D4, 48, vel=0.55, send={"hall": 0.5})
    p.melody(v_brass, [(2, 1.5), (1, 2.5)], sc, D4 + 12, 60, vel=0.5, send={"hall": 0.5})
    return p.render(HALL, master_db=-1.0, comp=(-12.0, 3.0))


def piece_zone_cahokia_river():
    """The river line: amber, a current of plucked strings, one long melody over it."""
    p = Piece("zone_cahokia_river", 60, 4, 9, seed=9)
    sc = SCALES["major"]
    T = F3
    p.texture(tex_water, gain=0.05, send={"hall": 0.3})
    p.drone(v_drone, F3 - 12, gain=0.3, send={"hall": 0.4})
    prog = [1, 5, 6, 4, 1, 2, 4, 5, 5]  # F C Dm Bb F Gm Bb C C7
    for bar, degree in enumerate(prog):
        notes = chord_from(sc, T, degree)
        if bar == 8:
            notes = chord_from(sc, T, 5, voicing=(0, 2, 4, 6))
        # The current: sixteenth-note broken chords that never stop, two octaves up and down.
        arp = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[0] + 24, notes[2] + 12, notes[1] + 12]
        pat = [0, 1, 2, 3, 4, 5, 2, 1, 0, 1, 2, 3, 4, 5, 2, 1]
        for i, idx in enumerate(pat):
            v = 0.34 if i % 4 == 0 else 0.22
            p.note(v_pluck, arp[idx], bar * 4 + i * 0.25, 0.35, vel=v, send={"room": 0.3, "hall": 0.25}, humanize=0.004)
        p.chord(v_harmonium, notes, bar * 4, 4.0, vel=0.32, send={"hall": 0.5}, spread=0.03)
        p.note(v_cello, notes[0] - 12, bar * 4, 3.8, vel=0.4, send={"hall": 0.3})
        p.note(v_cello, notes[2] - 12, bar * 4 + 2, 1.8, vel=0.3, send={"hall": 0.3})
    # A long melody on a horn: the motif stretched, then its answer, over all nine bars.
    long_line = [(1, 2), (3, 2), (5, 2), (8, 4), (7, 1), (5, 1), (4, 2), (3, 2), (2, 2), (1, 4),
                 (5, 2), (6, 2), (5, 2), (3, 2), (4, 1), (3, 1), (2, 2), (1, 0.5)]
    p.melody(v_horn, long_line, sc, F4, 0, vel=0.48, send={"hall": 0.6}, swell=arc(0.55, 0.78))
    return p.render(HALL, master_db=-1.0)


def piece_fight():
    """The fight layer: drums and a low ostinato on D, A and C, to play over any zone piece."""
    p = Piece("fight", 120, 4, 12, seed=10)
    sc = SCALES["minor"]
    for bar in range(12):
        # Kick: 1, the and-of-2, 3; snare on 2 and 4; hats in eighths with sixteenth fills.
        for b, v in [(0, 0.9), (1.5, 0.6), (2, 0.85), (3.5, 0.5)]:
            p.hit(p_kick, bar * 4 + b, vel=v)
        p.hit(p_brush, bar * 4 + 1, vel=0.8, attack=0.004, decay=0.14)
        p.hit(p_brush, bar * 4 + 3, vel=0.85, attack=0.004, decay=0.14)
        for e in range(8):
            p.hit(p_shaker, bar * 4 + e * 0.5, vel=0.5 if e % 2 == 0 else 0.3, decay=0.03)
        if bar % 4 == 3:
            for s in range(4):
                p.hit(p_tom, bar * 4 + 3 + s * 0.25, vel=0.6, freq=[140, 120, 100, 85][s])
            p.hit(p_shaker, bar * 4 + 3.75, vel=0.6, decay=0.12)
        if bar % 2 == 1:
            p.hit(p_iron, bar * 4 + 2.5, vel=0.3, base=1500.0, decay=0.2, send={"plate": 0.4})
        # The ostinato: D D A D | C D G D in eighths, on cello and a brass doubling now and then.
        ost = [1, 1, 5, 1, 7, 1, 4, 1] if bar % 4 != 3 else [1, 1, 5, 1, 7, 7, 8, 5]
        for i, d in enumerate(ost):
            v = 0.75 if i == 0 else 0.55
            p.note(v_cello, deg(sc, D3 - 12, d), bar * 4 + i * 0.5, 0.4, vel=v, send={"room": 0.2}, humanize=0.003)
            if bar >= 4:
                p.note(v_cello, deg(sc, D3, d), bar * 4 + i * 0.5, 0.4, vel=v * 0.6, send={"room": 0.2}, humanize=0.003)
    # Brass: fifths on D and A, hard and short, at the phrase heads; the motif's head once.
    for b in (0, 16, 32):
        p.chord(v_brass, [D3, D3 + 7, D3 + 12], b, 0.9, vel=0.55, send={"plate": 0.4})
        p.chord(v_brass, [D3, D3 + 7, D3 + 12], b + 2.5, 0.4, vel=0.5, send={"plate": 0.4})
    p.melody(v_brass, [(1, 0.5), (3, 0.5), (5, 0.5), (8, 1.5), (7, 0.5), (5, 0.5)], sc, D4, 24, vel=0.55, send={"plate": 0.4}, legato=0.85)
    p.melody(v_brass, [(5, 0.5), (4, 0.5), (3, 0.5), (1, 2.5)], sc, D4, 44, vel=0.5, send={"plate": 0.4}, legato=0.85)
    return p.render(HALL, master_db=0.0, comp=(-10.0, 3.5))


def piece_gate():
    """The Gate and Commencement: the motif grand, brass over organ, drums and a cymbal."""
    p = Piece("gate", 60, 4, 10, seed=11)
    sc = SCALES["major"]
    T = D3
    p.drone(v_drone, D2, gain=0.4, send={"hall": 0.5})
    prog = [1, 4, 1, 5, 6, 4, 1, 5, 1, 5]  # D G D A Bm G D A D A7sus
    for bar, degree in enumerate(prog):
        notes = chord_from(sc, T, degree)
        if bar == 9:
            notes = [deg(sc, T, 5), deg(sc, T, 8), deg(sc, T, 9), deg(sc, T, 11)]
        p.chord(v_organ, notes, bar * 4, 3.9, vel=0.5, send={"hall": 0.65}, spread=0.02)
        p.note(v_organ, notes[0] - 12, bar * 4, 3.9, vel=0.5, send={"hall": 0.6})
        p.chord(v_strings, [m + 12 for m in notes], bar * 4, 4.0, vel=0.38, send={"hall": 0.7}, spread=0.05)
        p.hit(p_taiko, bar * 4, vel=0.6 if bar % 2 == 0 else 0.45, send={"hall": 0.5})
        p.hit(p_taiko, bar * 4 + 2, vel=0.35, send={"hall": 0.5})
        if bar in (3, 7):
            p.hit(p_taiko, bar * 4 + 3, vel=0.4, send={"hall": 0.5})
            p.hit(p_taiko, bar * 4 + 3.5, vel=0.5, send={"hall": 0.5})
    # The motif, grand: brass in octaves, horn underneath, twice; a cymbal into the second.
    p.melody(v_brass, MOTIF, sc, D4, 0, vel=0.6, send={"hall": 0.6}, swell=arc(0.5, 0.8))
    p.melody(v_horn, MOTIF, sc, D4 - 12, 0, vel=0.5, send={"hall": 0.6})
    p.hit(p_cymbal, 13.5, vel=0.5, swell=2.5, ring=2.0, send={"hall": 0.6})
    p.melody(v_brass, MOTIF, sc, D4 + 12, 16, vel=0.65, send={"hall": 0.6}, swell=arc(0.5, 0.85))
    p.melody(v_brass, MOTIF, sc, D4, 16, vel=0.5, send={"hall": 0.6})
    p.melody(v_horn, MOTIF_ANSWER, sc, D4 + 12, 28, vel=0.55, send={"hall": 0.6}, swell=arc(0.3, 0.75))
    p.melody(v_brass, [(3, 2), (2, 2), (1, 0.5)], sc, D4, 36, vel=0.45, send={"hall": 0.6})
    p.hit(p_cymbal, 36.5, vel=0.35, swell=2.0, ring=1.5, send={"hall": 0.6})
    return p.render(HALL, master_db=0.0, comp=(-12.0, 3.0))


# Stingers: short, no loop, ending in silence.


def sting_pattern():
    """The Pattern fires: a rising harp, a bright brass hit, a shimmer."""
    p = Piece("sting_pattern", 120, 4, 1.25, seed=12, loop=False, seconds=2.5)
    sc = SCALES["minor"]
    for i, d in enumerate([1, 5, 8, 10, 12, 15]):
        p.note(v_pluck, deg(sc, D4, d), i * 0.22, 1.0, vel=0.5, send={"plate": 0.5}, humanize=0.0)
    p.chord(v_brass, [D4, D4 + 7, D4 + 12, D4 + 15], 1.3, 1.4, vel=0.5, send={"plate": 0.5})
    p.note(v_glass, D5 + 12, 1.3, 1.5, vel=0.4, send={"plate": 0.7})
    p.hit(p_iron, 1.3, vel=0.4, base=2200.0, decay=0.4, send={"plate": 0.5})
    return p.render(HALL, master_db=0.0)


def sting_rite():
    """The genius takes form: an organ swell from the minor into the major, bells over it."""
    p = Piece("sting_rite", 60, 4, 1.0, seed=13, loop=False, seconds=4.0)
    sc = SCALES["minor"]
    p.chord(v_organ, [D3, D3 + 3, D3 + 7, D4], 0, 1.6, vel=0.5, send={"hall": 0.7}, spread=0.03)
    p.chord(v_organ, [D3, D3 + 4, D3 + 7, D4 + 2], 1.6, 2.0, vel=0.6, send={"hall": 0.7}, spread=0.03)
    p.note(v_drone, D2, 0, 3.6, vel=0.5, send={"hall": 0.5})
    for i, m in enumerate([D5, D5 + 3, D5 + 7, D5 + 12]):
        p.note(v_bell, m, 0.2 + i * 0.4, 1.0, vel=0.35, send={"hall": 0.8})
    p.note(v_bell, D5 + 16, 1.8, 1.0, vel=0.4, send={"hall": 0.8})  # the major third, high
    p.hit(p_cymbal, 0.0, vel=0.3, swell=1.6, ring=1.0, send={"hall": 0.6})
    return p.render(HALL, master_db=-1.0)


def sting_reckoning():
    """The Reckoning read: three tolls, a low drone, the motif's head on brass, a question left."""
    p = Piece("sting_reckoning", 60, 4, 1.25, seed=14, loop=False, seconds=5.0)
    sc = SCALES["minor"]
    p.note(v_drone, D2, 0, 4.5, vel=0.6, send={"cavern": 0.6})
    for i in range(3):
        p.note(v_bell, D4 - 12 + 12, i * 1.1, 1.0, vel=0.5, send={"cavern": 0.8})
    p.melody(v_brass, [(1, 1), (3, 1), (5, 1), (8, 1.5)], sc, D4, 0.5, vel=0.5, send={"hall": 0.6}, legato=1.0)
    p.chord(v_strings, [D3, D3 + 3, D3 + 7, D3 + 10 + 12], 1.0, 3.0, vel=0.35, send={"cavern": 0.6}, spread=0.1)
    p.note(v_glass, D5 + 11, 3.2, 1.2, vel=0.25, send={"cavern": 0.9})  # C#: the question
    p.hit(p_taiko, 0.0, vel=0.6, send={"cavern": 0.6})
    p.hit(p_taiko, 3.3, vel=0.45, send={"cavern": 0.6})
    return p.render(HALL, master_db=-1.0)


def sting_done():
    """A quest done: a bright plucked rise into the major, a bell on top."""
    p = Piece("sting_done", 120, 4, 1.0, seed=15, loop=False, seconds=2.0)
    sc = SCALES["major"]
    for i, d in enumerate([1, 3, 5, 8]):
        p.note(v_pluck, deg(sc, D4, d), i * 0.12, 0.8, vel=0.5, send={"plate": 0.4}, humanize=0.0)
    p.note(v_bell, D5 + 12, 0.45, 1.0, vel=0.3, send={"plate": 0.6})
    p.chord(v_harmonium, [D3 + 12, D3 + 16, D3 + 19], 0.4, 1.0, vel=0.35, send={"plate": 0.5})
    return p.render(HALL, master_db=-1.0)


def sting_lost():
    """A quest lost: a falling minor line, a dull low drum, nothing resolved."""
    p = Piece("sting_lost", 60, 4, 0.625, seed=16, loop=False, seconds=2.5)
    sc = SCALES["minor"]
    p.melody(v_cello, [(5, 0.4), (4, 0.4), (3, 0.4), (2, 1.0)], sc, D3, 0, vel=0.55, send={"hall": 0.5}, legato=1.0)
    p.chord(v_strings, [D3 - 12 + 12, D3 + 3, D3 + 8], 0.3, 1.6, vel=0.35, send={"hall": 0.6}, spread=0.05)  # Dm with the flat sixth
    p.hit(p_taiko, 0.0, vel=0.5, send={"cavern": 0.5})
    p.hit(p_taiko, 1.2, vel=0.35, send={"cavern": 0.5})
    return p.render(HALL, master_db=-1.5)


PIECES = {
    "title": (piece_title, "loop", 60, "D minor", -4.0),
    "academy_quad": (piece_academy_quad, "loop", 60, "F major", -5.0),
    "academy_yard": (piece_academy_yard, "loop", 120, "D dorian", -5.0),
    "academy_hearth": (piece_academy_hearth, "loop", 60, "D minor", -6.0),
    "academy_dorm": (piece_academy_dorm, "loop", 60, "D minor", -8.0),
    "zone_green": (piece_zone_green, "loop", 60, "D dorian", -6.0),
    "zone_shenandoah": (piece_zone_shenandoah, "loop", 60, "D phrygian", -6.0),
    "zone_harpers_cut": (piece_zone_harpers_cut, "loop", 120, "D phrygian", -5.0),
    "zone_cahokia_river": (piece_zone_cahokia_river, "loop", 60, "F major", -5.0),
    "fight": (piece_fight, "loop", 120, "D minor", -6.0),
    "gate": (piece_gate, "loop", 60, "D major", -4.0),
    "sting_pattern": (sting_pattern, "stinger", 120, "D minor", -3.0),
    "sting_rite": (sting_rite, "stinger", 60, "D minor to D major", -3.0),
    "sting_reckoning": (sting_reckoning, "stinger", 60, "D minor", -3.0),
    "sting_done": (sting_done, "stinger", 120, "D major", -3.0),
    "sting_lost": (sting_lost, "stinger", 60, "D minor", -3.0),
}


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------


def to_stereo(y: np.ndarray, width: float, rng: np.random.Generator) -> np.ndarray:
    """A cheap widener: the signal plus a short, dark, decorrelated copy on each side."""
    n = len(y)
    d = samples(0.011)
    side = np.zeros(n)
    side[d:] = y[:-d]
    side = fft_filter(side, 150, 4000) * width
    return np.stack([y + side, y - side], axis=1)


def write_wav(path: str, y: np.ndarray, loop: bool):
    """16-bit PCM; loops carry a smpl chunk (forward loop over the whole file) for Godot's importer."""
    if y.ndim == 1:
        y = y[:, None]
    channels = y.shape[1]
    frames = y.shape[0]
    pcm = np.clip(np.round(y * 32767.0), -32768, 32767).astype("<i2").tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    if loop:
        # Append a smpl chunk and fix the RIFF size.
        smpl = struct.pack("<IIIIIIIII", 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack("<IIIIII", 0, 0, 0, frames - 1, 0, 0)
        chunk = b"smpl" + struct.pack("<I", len(smpl)) + smpl
        with open(path, "r+b") as f:
            f.seek(0, 2)
            f.write(chunk)
            size = f.tell() - 8
            f.seek(4)
            f.write(struct.pack("<I", size))


def analyse(y: np.ndarray, loop: bool) -> dict:
    mono = y if y.ndim == 1 else y.mean(axis=1)
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(mono ** 2)))
    info = {
        "peak_dbfs": round(20 * math.log10(peak + 1e-12), 2),
        "rms_dbfs": round(20 * math.log10(rms + 1e-12), 2),
        "dc": round(float(np.mean(mono)), 6),
        "clipped": int(np.sum(np.abs(mono) >= 0.999)),
    }
    if loop:
        # The step across the seam against the steps the music takes anyway (its 99.9th percentile).
        body = np.percentile(np.abs(np.diff(mono)), 99.9)
        info["seam"] = round(float(abs(mono[-1] - mono[0])), 5)
        info["seam_vs_body"] = round(float(abs(mono[-1] - mono[0]) / (body + 1e-9)), 2)
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pieces", nargs="*", help="which to render (default: all)")
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--stereo", action="store_true")
    ap.add_argument("--ogg", action="store_true", help="also write .ogg next to each .wav with ffmpeg")
    ap.add_argument("--report", default=None, help="write a JSON report of levels and lengths here")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    names = args.pieces or list(PIECES)
    report = {}
    for name in names:
        if name not in PIECES:
            sys.exit(f"unknown piece {name}; known: {', '.join(PIECES)}")
        fn, kind, tempo, key, gain = PIECES[name]
        y = fn()
        loop = kind == "loop"
        if args.stereo:
            y = to_stereo(y, 0.35 if loop else 0.2, np.random.default_rng(99))
            y = limiter(y)
        path = os.path.join(args.out, f"{name}.wav")
        write_wav(path, y, loop)
        if args.ogg and shutil.which("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-c:a", "libvorbis", "-q:a", "5", path[:-4] + ".ogg"], check=True)
        info = analyse(y, loop)
        info.update(seconds=round(len(y) / SR, 3), bytes=os.path.getsize(path), tempo=tempo, key=key, kind=kind)
        report[name] = info
        print(f"{name:20s} {info['seconds']:6.2f}s {info['bytes']/1e6:5.2f}MB peak {info['peak_dbfs']:6.2f} rms {info['rms_dbfs']:6.2f} dc {info['dc']:+.5f} clip {info['clipped']}"
              + (f" seam {info['seam']:.5f} ({info['seam_vs_body']:.2f}x a normal step)" if loop else ""), flush=True)
    if args.report:
        with open(args.report, "w") as f:
            json.dump(report, f, indent=1)
    return report


if __name__ == "__main__":
    main()
