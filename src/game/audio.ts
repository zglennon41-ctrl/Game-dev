// The pulse clock and the sound. The audio hardware is the master clock: beats are scheduled
// on it, visuals read "what is being heard now", and inputs are mapped onto the same timeline.

export class Pulse {
  readonly ctx: AudioContext;
  t0 = 0;
  period = 0.6;
  /** Player calibration in ms: positive if the player's inputs land late on this device. */
  calibrationMs = 0;
  private scheduledTo = -1;
  private timer: number | null = null;
  private master: GainNode;
  private noise: AudioBuffer;
  beatsPerBar = 4;
  music = true;

  constructor() {
    this.ctx = new AudioContext({ latencyHint: 'interactive' });
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.7;
    this.master.connect(this.ctx.destination);
    this.noise = this.ctx.createBuffer(1, this.ctx.sampleRate, this.ctx.sampleRate);
    const d = this.noise.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  }

  /** Start the pulse: beat 0 lands `leadIn` seconds from now. */
  async start(periodS: number, leadIn = 1.2) {
    await this.ctx.resume();
    this.period = periodS;
    this.t0 = this.ctx.currentTime + leadIn;
    this.scheduledTo = -1;
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = window.setInterval(() => this.schedule(), 25);
    this.schedule();
  }

  stop() {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
  }

  /** Context time of what is reaching the speakers at performance time `perfMs`. */
  heardAt(perfMs: number): number {
    const ctx = this.ctx as AudioContext & { getOutputTimestamp?: () => AudioTimestamp };
    const ts = ctx.getOutputTimestamp?.();
    if (ts && ts.contextTime !== undefined && ts.performanceTime) return ts.contextTime + (perfMs - ts.performanceTime) / 1000;
    const lat = (this.ctx as AudioContext & { outputLatency?: number }).outputLatency ?? this.ctx.baseLatency ?? 0;
    return this.ctx.currentTime - lat + (perfMs - performance.now()) / 1000;
  }

  /** Game time now (seconds on the beat clock), as heard. */
  now(): number { return this.heardAt(performance.now()); }
  /** Game time of an input event, corrected by the player's calibration. */
  inputTime(perfMs: number): number { return this.heardAt(perfMs) - this.calibrationMs / 1000; }

  private schedule() {
    const horizon = this.ctx.currentTime + 0.15;
    let k = this.scheduledTo + 1;
    while (this.t0 + k * this.period < horizon) {
      const t = this.t0 + k * this.period;
      if (t >= this.ctx.currentTime - 0.01) this.beatSound(t, k);
      this.scheduledTo = k;
      k++;
    }
  }

  private beatSound(t: number, k: number) {
    const downbeat = ((k % this.beatsPerBar) + this.beatsPerBar) % this.beatsPerBar === 0;
    // The click: a wooden knock.
    this.tone(t, downbeat ? 1180 : 880, 0.05, downbeat ? 0.32 : 0.2, 'triangle');
    this.thump(t, downbeat ? 0.55 : 0.32);
    if (this.music) {
      // A low string drone on the bar, moving through a minor Appalachian figure.
      const bar = Math.floor(k / this.beatsPerBar);
      const roots = [55, 55, 49, 41.2];
      if (downbeat) this.pad(t, roots[((bar % 4) + 4) % 4], this.period * this.beatsPerBar);
      if (k % 2 === 1) this.tone(t, roots[((bar % 4) + 4) % 4] * 4, 0.12, 0.05, 'sawtooth', 900);
    }
  }

  private tone(t: number, freq: number, dur: number, gain: number, type: OscillatorType = 'sine', lowpass?: number) {
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(gain, t + 0.004);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    let node: AudioNode = o;
    if (lowpass) {
      const f = this.ctx.createBiquadFilter();
      f.type = 'lowpass';
      f.frequency.value = lowpass;
      o.connect(f);
      node = f;
    }
    node.connect(g).connect(this.master);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  private thump(t: number, gain: number) {
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.frequency.setValueAtTime(130, t);
    o.frequency.exponentialRampToValueAtTime(45, t + 0.12);
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
    o.connect(g).connect(this.master);
    o.start(t);
    o.stop(t + 0.2);
  }

  private pad(t: number, freq: number, dur: number) {
    for (const [mult, gain] of [[1, 0.07], [1.5, 0.035], [2, 0.03]] as const) {
      const o = this.ctx.createOscillator();
      const g = this.ctx.createGain();
      const f = this.ctx.createBiquadFilter();
      o.type = 'sawtooth';
      o.frequency.value = freq * mult;
      f.type = 'lowpass';
      f.frequency.value = 420;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(gain, t + 0.08);
      g.gain.setValueAtTime(gain, t + dur - 0.1);
      g.gain.linearRampToValueAtTime(0, t + dur);
      o.connect(f).connect(g).connect(this.master);
      o.start(t);
      o.stop(t + dur + 0.05);
    }
  }

  private noiseBurst(t: number, dur: number, gain: number, freq: number, q = 1) {
    const s = this.ctx.createBufferSource();
    s.buffer = this.noise;
    const f = this.ctx.createBiquadFilter();
    f.type = 'bandpass';
    f.frequency.value = freq;
    f.Q.value = q;
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    s.connect(f).connect(g).connect(this.master);
    s.start(t);
    s.stop(t + dur + 0.02);
  }

  // Event sounds, played now.
  private get t() { return this.ctx.currentTime; }
  hitPerfect(chain: number) { this.tone(this.t, 660 * Math.pow(2, Math.min(chain, 6) / 12), 0.12, 0.25, 'square', 2400); this.noiseBurst(this.t, 0.08, 0.35, 3000, 2); }
  hitOff() { this.noiseBurst(this.t, 0.1, 0.25, 700, 1); }
  heavy() { this.thump(this.t, 0.9); this.noiseBurst(this.t, 0.25, 0.4, 300, 0.7); }
  parry() { this.tone(this.t, 1560, 0.5, 0.25); this.tone(this.t, 2340, 0.35, 0.15); this.tone(this.t, 3120, 0.2, 0.08); }
  block() { this.tone(this.t, 300, 0.15, 0.25, 'square', 800); }
  hurt() { this.noiseBurst(this.t, 0.3, 0.6, 220, 0.8); this.thump(this.t, 0.7); }
  fumble() { this.tone(this.t, 180, 0.12, 0.15, 'sawtooth', 500); }
  whiff() { this.noiseBurst(this.t, 0.12, 0.12, 1800, 0.6); }
  stagger() { this.tone(this.t, 98, 0.8, 0.35, 'sawtooth', 600); this.tone(this.t, 147, 0.8, 0.2, 'sawtooth', 600); }
  stance(on: boolean) { this.tone(this.t, on ? 220 : 165, 0.4, 0.2, 'triangle'); if (on) this.tone(this.t + 0.06, 330, 0.35, 0.12, 'triangle'); }
  growl() {
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    const f = this.ctx.createBiquadFilter();
    o.type = 'sawtooth';
    o.frequency.setValueAtTime(70, this.t);
    o.frequency.linearRampToValueAtTime(110, this.t + this.period * 1.6);
    f.type = 'lowpass';
    f.frequency.setValueAtTime(200, this.t);
    f.frequency.linearRampToValueAtTime(900, this.t + this.period * 1.6);
    g.gain.setValueAtTime(0.0001, this.t);
    g.gain.linearRampToValueAtTime(0.18, this.t + this.period);
    g.gain.exponentialRampToValueAtTime(0.0001, this.t + this.period * 1.8);
    o.connect(f).connect(g).connect(this.master);
    o.start(this.t);
    o.stop(this.t + this.period * 2);
  }
  fell() { this.tone(this.t, 196, 1.2, 0.2, 'triangle'); this.tone(this.t + 0.15, 247, 1.0, 0.15, 'triangle'); this.tone(this.t + 0.3, 294, 1.0, 0.15, 'triangle'); }
  done() { this.tone(this.t, 294, 1.5, 0.2, 'triangle'); this.tone(this.t + 0.2, 392, 1.5, 0.15, 'triangle'); }
}
