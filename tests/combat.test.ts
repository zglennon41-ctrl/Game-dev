import { describe, it, expect } from 'vitest';
import { judge, beatWindowMs, BreakMeter, ChordTracker } from '../src/rules/combat';
import { Fight, type FightEvent } from '../src/game/fight';

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

/** Run a fight at 60 fps for `seconds`, with an input policy called once per frame. */
function run(seconds: number, policy: (f: Fight, t: number, frame: number) => void, opts = {}) {
  const f = new Fight({ seed: 3, ...opts });
  const all: FightEvent[] = [];
  for (let frame = 0; frame < seconds * 60; frame++) {
    const t = frame / 60;
    policy(f, t, frame);
    // Stay in reach: step toward the wolf.
    const dx = f.wolf.x - f.player.x, dy = f.wolf.y - f.player.y;
    const d = Math.hypot(dx, dy);
    f.update(t, d > 90 ? { x: dx / d, y: dy / d } : { x: 0, y: 0 });
    all.push(...f.drain());
  }
  return { f, all };
}

describe('the fight', () => {
  it('a player on the beat fells a wolf faster than one mashing off it, and takes less', () => {
    const onBeat = run(120, (f, t) => {
      const k = Math.round(t / f.period);
      const onTime = Math.abs(t - k * f.period) < 1 / 120;
      if (!onTime) return;
      if (f.wolf.mode === 'windup' && f.wolf.strikeBeat === k) f.input('hold-down', t), f.input('hold-up', t + 0.01);
      else if (f.dist() < 140 && k > f.player.lastActionBeat) f.input(f.player.will > 60 ? 'ground-strike' : 'strike', t);
    });
    const masher = run(120, (f, t, frame) => {
      if (frame % 11 === 0 && f.dist() < 140) f.input('strike', t);
    });
    expect(onBeat.f.stats.wolvesDown).toBeGreaterThan(masher.f.stats.wolvesDown);
    expect(onBeat.f.stats.parries).toBeGreaterThan(0);
    expect(onBeat.f.stats.staggers).toBeGreaterThan(0);
    expect(onBeat.f.stats.hurts).toBeLessThan(masher.f.stats.hurts);
    expect(masher.f.stats.fumbles).toBeGreaterThan(0);
  });

  it('a perfect Hold on the strike beat parries: no damage, 10 Will back', () => {
    const f = new Fight({ seed: 1 });
    f.wolf.mode = 'windup';
    f.wolf.strikeBeat = 5;
    f.wolf.x = f.player.x + 60; f.wolf.y = f.player.y;
    f.player.will = 50;
    f.update(4.9 * f.period);
    f.input('hold-down', 5 * f.period - 0.05);
    f.update(5 * f.period + 0.2);
    const ev = f.drain().map((e) => e.type);
    expect(ev).toContain('parry');
    expect(f.player.hp).toBe(100);
    expect(f.player.will).toBeGreaterThan(55);
    expect(f.wolf.mode).toBe('stagger');
  });

  it('a late Hold, still inside the window, parries', () => {
    const f = new Fight({ seed: 1 });
    f.wolf.mode = 'windup'; f.wolf.strikeBeat = 5; f.wolf.x = f.player.x + 60; f.wolf.y = f.player.y;
    f.update(5 * f.period + 0.01);
    f.input('hold-down', 5 * f.period + 0.08);
    f.update(5 * f.period + 0.3);
    expect(f.drain().map((e) => e.type)).toContain('parry');
  });

  it('a held guard off the beat blocks for half; nothing takes the full hit', () => {
    const f = new Fight({ seed: 1 });
    f.wolf.mode = 'windup'; f.wolf.strikeBeat = 5; f.wolf.x = f.player.x + 60; f.wolf.y = f.player.y;
    f.input('hold-down', 4.5 * f.period);
    f.update(5 * f.period + 0.2);
    expect(f.player.hp).toBe(94);
    const g = new Fight({ seed: 1 });
    g.wolf.mode = 'windup'; g.wolf.strikeBeat = 5; g.wolf.x = g.player.x + 60; g.wolf.y = g.player.y;
    g.update(5 * g.period + 0.2);
    expect(g.player.hp).toBe(88);
  });

  it('two Projects in one beat fumble and break the chain', () => {
    const f = new Fight({ seed: 1, passive: true });
    f.wolf.x = f.player.x + 60; f.wolf.y = f.player.y;
    f.input('strike', 1 * f.period);
    f.input('strike', 1 * f.period + 0.05);
    const ev = f.drain().map((e) => e.type);
    expect(ev).toContain('hit');
    expect(ev).toContain('fumble');
    expect(f.player.chain).toBe(0);
  });

  it('saber strikes do not break; three on-beat Ground Strikes (an Anchor technique vs a Read beast) do', () => {
    const f = new Fight({ seed: 1, passive: true });
    f.wolf.x = f.player.x + 60; f.wolf.y = f.player.y;
    for (const k of [1, 2, 3]) f.input('strike', k * f.period);
    expect(f.wolf.mode).not.toBe('stagger');
    for (const k of [4, 6, 8]) { f.wolf.x = f.player.x + 60; f.wolf.y = f.player.y; f.input('ground-strike', k * f.period); }
    expect(f.wolf.mode).toBe('stagger');
    expect(f.drain().map((e) => e.type)).toContain('stagger');
  });

  it('stance hits harder and drains Will; on the beat it enters at once', () => {
    const f = new Fight({ seed: 1, passive: true });
    f.wolf.x = f.player.x + 60; f.wolf.y = f.player.y;
    f.input('stance', 1 * f.period);
    expect(f.player.stance).toBe(true);
    f.update(2 * f.period);
    expect(f.player.will).toBeLessThan(100);
    f.drain();
    f.input('strike', 3 * f.period);
    const hit = f.drain().find((e) => e.type === 'hit') as { damage: number };
    expect(hit.damage).toBe(15);
  });
});
