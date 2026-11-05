// Combat rules that are pure: beat judgment, break counting, Chord detection.
import { data, type LineColor } from '../data';

const C = data.rules.combat;

/** The beat window for a line color: 150 ms, 200 ms on Green. */
export function beatWindowMs(line: LineColor): number {
  return line === 'green' ? C.beatWindowMsGreen : C.beatWindowMs;
}

export interface Judgment {
  /** The index of the nearest beat. */
  beat: number;
  /** Signed: negative is early, positive is late. */
  offsetMs: number;
  perfect: boolean;
  output: number;
}

/**
 * Judge an input at time t (seconds) against a pulse that beats at t0 + k * period.
 * Perfect within half the window either side of the beat; off-beat is 70% output.
 */
export function judge(t: number, t0: number, periodS: number, windowMs: number): Judgment {
  const k = Math.round((t - t0) / periodS);
  const offsetMs = (t - (t0 + k * periodS)) * 1000;
  const perfect = Math.abs(offsetMs) <= windowMs / 2;
  return { beat: k, offsetMs, perfect, output: perfect ? 1 : C.offBeatOutput };
}

/** Three breaks from the Shape opposite the beast's open a stagger of three beats. */
export class BreakMeter {
  count = 0;
  constructor(readonly needed = C.breaksToStagger, readonly staggerBeats = C.staggerBeats) {}
  /** Record a hit. Returns the number of stagger beats opened (0 if none). */
  hit(breaks: boolean): number {
    if (!breaks) return 0;
    this.count++;
    if (this.count >= this.needed) {
      this.count = 0;
      return this.staggerBeats;
    }
    return 0;
  }
  /** An off-beat input or a hit taken lets the break slip. */
  slip() { this.count = 0; }
}

/**
 * Chord: when every member of the party lands a perfect input on the same beat eight beats
 * in a row, the next three beats are Chord. Feed one call per beat with whether all landed.
 */
export class ChordTracker {
  streak = 0;
  chordBeatsLeft = 0;
  beat(allPerfect: boolean): boolean {
    if (this.chordBeatsLeft > 0) {
      this.chordBeatsLeft--;
      return true;
    }
    this.streak = allPerfect ? this.streak + 1 : 0;
    if (this.streak >= C.chordPerfectBeats) {
      this.streak = 0;
      this.chordBeatsLeft = C.chordBeats;
    }
    return false;
  }
  get inChord(): boolean { return this.chordBeatsLeft > 0; }
}
