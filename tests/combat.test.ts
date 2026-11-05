import { describe, it, expect } from 'vitest';
import { judge, beatWindowMs, BreakMeter, ChordTracker } from '../src/rules/combat';

describe('beat judgment', () => {
  it('perfect within half the window either side; 70% off the beat', () => {
    expect(beatWindowMs('green')).toBe(200);
    expect(beatWindowMs('amber')).toBe(150);
    const j = judge(1.27, 0, 0.6, 150);
    expect(j.beat).toBe(2);
    expect(Math.round(j.offsetMs)).toBe(70);
    expect(j.perfect).toBe(true);
    expect(judge(1.28, 0, 0.6, 150).perfect).toBe(false);
    expect(judge(1.28, 0, 0.6, 150).output).toBe(0.7);
    expect(judge(1.125, 0, 0.6, 150).perfect).toBe(true);
    expect(judge(1.12, 0, 0.6, 150).perfect).toBe(false);
  });
  it('three breaks open three beats of stagger; a slip resets', () => {
    const b = new BreakMeter();
    expect([b.hit(true), b.hit(true)]).toEqual([0, 0]);
    b.slip();
    expect([b.hit(true), b.hit(true), b.hit(true)]).toEqual([0, 0, 3]);
    expect(b.hit(false)).toBe(0);
  });
  it('Chord after eight shared perfect beats, for three beats', () => {
    const c = new ChordTracker();
    for (let i = 0; i < 8; i++) expect(c.beat(true)).toBe(false);
    expect([c.beat(false), c.beat(false), c.beat(false), c.beat(true)]).toEqual([true, true, true, false]);
  });
});

