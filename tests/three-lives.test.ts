// Acceptance: docs/three-lives.md. These expectations are the owner's; if one fails after a
// change to data/reading.json or data/rules.json, that is a design change to raise with the
// owner, not a test to edit.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { simulate, stateOn, monthOf, yearOf, type SimResult, type ReadingRecord } from '../src/sim/simulate';
import type { Life } from '../src/sim/script';
import { data } from '../src/data';

const load = (id: string) => simulate(JSON.parse(readFileSync(`data/lives/${id}.json`, 'utf8')) as Life);
const mira = load('mira');
const tobiah = load('tobiah');
const sable = load('sable');

const reading = (r: SimResult, instar: number): ReadingRecord => {
  const x = r.readings.find((rd) => rd.instar === instar);
  if (!x) throw new Error(`${r.life.name} never reached instar ${instar}`);
  return x;
};
const hasTag = (featureIds: string[], tags: string[]) =>
  featureIds.some((f) => (data.features.find((x) => x.id === f)?.tags ?? []).some((t) => tags.includes(t)));
const WORN = ['relic-mask', 'relic-coat', 'relic-gauntlet'];

describe('Mira — says ranged, fights close', () => {
  it('First Form: a Beast with wings and far-eyes', () => {
    const c = reading(mira, 1).picked;
    expect(c.expression).toBe('beast');
    expect(c.features).toContain('wings');
    expect(c.seedMark).toBe('far-eyes');
  });

  it('Gate Reading: at least one Kith and one Relic, all carry far-eyes, set-feet present and fixable', () => {
    const rd = reading(mira, 2);
    const xs = rd.result.candidates.map((c) => c.expression);
    expect(xs).toContain('kith');
    expect(xs).toContain('relic');
    for (const c of rd.result.candidates) expect(c.features).toContain('far-eyes');
    expect(rd.adaptationsAtReading).toContain('set-feet');
    expect(data.features.find((f) => f.id === 'set-feet')?.fixable).toBe(true);
    expect(rd.result.candidates.some((c) => c.heritage.includes('set-feet'))).toBe(true);
  });

  it('Third Form Reading, at the Pattern, offers a worn Relic in the top three', () => {
    const rd = reading(mira, 3);
    expect(rd.unlockedBy).toBe('pattern-built');
    expect(rd.result.candidates.some((c) => c.expression === 'relic' && WORN.includes(c.silhouette))).toBe(true);
  });

  it('Kin-form offered at the first Reading after 100 runs beside Oona', () => {
    const avail = mira.graftsAvailable.find((g) => g.id === 'kin:oona');
    expect(avail).toBeDefined();
    expect(monthOf(avail!.day)).toBeLessThanOrEqual(10);
    const next = mira.readings.find((rd) => rd.day >= avail!.day && rd.instar >= 2)!;
    expect(next.graftsOffered.map((g) => g.id)).toContain('kin:oona');
  });

  it('Cross title Deadeye Draw-Cutter by month 18, Adept in both', () => {
    expect(mira.crossTitle?.title).toBe('Deadeye Draw-Cutter');
    expect(monthOf(mira.crossTitle!.day)).toBeLessThanOrEqual(18);
    for (const id of ['deadeye', 'draw-cutter']) expect(mira.archetypes.find((a) => a.archetype === id)?.adeptDay).not.toBeNull();
  });

  it('Accord in year 3, after swearing Stoop, with Master Draw-Cutter', () => {
    const accord = mira.milestoneDays.accord;
    expect(yearOf(accord)).toBe(3);
    const swear = mira.life.events.find((e) => e.type === 'swear')!.day;
    const master = mira.archetypes.find((a) => a.archetype === 'draw-cutter')!.masterDay!;
    expect(accord).toBeGreaterThanOrEqual(swear);
    expect(accord).toBeGreaterThanOrEqual(master);
    expect(mira.pattern?.archetype).toBe('draw-cutter');
  });

  it('Founding eligible once two other accounts match Form + Terms with 10 uses each', () => {
    const lastPeerAtTen = Math.max(...mira.life.events.filter((e) => e.type === 'peer-uses' && e.uses >= 10).map((e) => e.day));
    expect(mira.foundingEligibleDay).toBe(lastPeerAtTen);
  });
});

describe('Tobiah — fires the Pattern, ignores the genius', () => {
  // OWNER QUESTION 1 (docs/decisions-needed.md). Under the Systems unlock table, building the
  // Pattern unlocks the Third Form at day 30; tier III needs 150 fires (day ~73 at the scripted
  // rate). The expectation cannot hold while "first Pattern built" unlocks the Third Form.
  it.skip('Intention tier III before the genius reaches the Third Form; the tier unlocks a Reading at day >= 30', () => {
    const rd = reading(tobiah, 3);
    expect(tobiah.tierDays[3]).toBeLessThanOrEqual(rd.day);
    expect(rd.unlockedBy).toBe('tier:3');
    expect(rd.day).toBeGreaterThanOrEqual(30);
  });

  it('Resonance at month 6 >= 4 while instar <= 3', () => {
    const s = stateOn(tobiah, 182);
    expect(s.resonance).toBeGreaterThanOrEqual(4);
    expect(s.instar).toBeLessThanOrEqual(3);
  });

  it('every candidate set after tier III has at least two Engine/Relic forms with wall or shield features', () => {
    const after = tobiah.readings.filter((rd) => rd.day >= tobiah.tierDays[3]);
    expect(after.length).toBeGreaterThan(0);
    for (const rd of after) {
      const n = rd.result.candidates.filter((c) => ['engine', 'relic'].includes(c.expression) && hasTag(c.features, ['wall', 'shield'])).length;
      expect(n, `instar ${rd.instar} on day ${rd.day}`).toBeGreaterThanOrEqual(2);
    }
  });

  it('Tier IV at 400 uses, month 10–14', () => {
    const d = tobiah.tierDays[4];
    expect(monthOf(d)).toBeGreaterThanOrEqual(10);
    expect(monthOf(d)).toBeLessThanOrEqual(14);
  });

  it('Accord reachable from the Pattern side in year 3 once sworn and Master Bulwark', () => {
    const accord = tobiah.milestoneDays.accord;
    expect(yearOf(accord)).toBe(3);
    expect(tobiah.tierDays[5]).toBe(accord);
    expect(tobiah.pattern?.sworn).toBe(true);
    expect(tobiah.archetypes.find((a) => a.archetype === 'bulwark')?.rank).toBe('master');
  });

  it('Grafts: only the Kin-form; no beast or shade grafts', () => {
    const offered = tobiah.readings.flatMap((rd) => rd.graftsOffered.map((g) => g.id));
    expect(offered.length).toBeGreaterThan(0);
    for (const id of offered) expect(id.startsWith('kin:')).toBe(true);
  });
});

describe('Sable — bonds with everything, rarely fires', () => {
  it('First Form: a Daemon', () => {
    expect(reading(sable, 1).picked.expression).toBe('daemon');
  });

  it('Shade graft offered at the first Reading after acceptance; Shade-walker unlocked from the Third Form', () => {
    const accepted = sable.life.events.find((e) => e.type === 'shade-accept')!.day;
    const next = sable.readings.find((rd) => rd.day >= accepted)!;
    expect(next.graftsOffered.some((g) => g.id.startsWith('shade:'))).toBe(true);
    const sw = sable.genius.secondary.find((s) => s.id === 'shade-walker');
    expect(sw).toBeDefined();
    expect(sw!.day).toBeGreaterThanOrEqual(reading(sable, 3).day);
  });

  it('Resonance from the genius side: two verses by the Fourth Form while tier is still I or II', () => {
    const s = stateOn(sable, reading(sable, 4).day);
    expect(s.tier).toBeGreaterThanOrEqual(1);
    expect(s.tier).toBeLessThanOrEqual(2);
    expect(s.verses).toBe(2);
  });

  it('Fifth Form in year 3 by the Master milestone', () => {
    const rd = reading(sable, 5);
    expect(yearOf(rd.day)).toBe(3);
    expect(rd.unlockedBy).toBe('master');
  });

  it('Accord blocked until tier V (400 uses); the Hearth War burst reaches it', () => {
    const burst = sable.life.phases.find((p) => (p.patternFiresPerDay ?? 0) > 5)!;
    const accord = sable.milestoneDays.accord;
    expect(accord).toBeGreaterThanOrEqual(burst.from);
    expect(accord).toBeLessThanOrEqual(burst.to);
    expect(sable.tierDays[5]).toBe(accord);
    expect(reading(sable, 5).day).toBeLessThan(burst.from);
  });

  it('Own-blood graft (second-face) available from the Third Form', () => {
    const g = sable.graftsAvailable.find((x) => x.id === 'blood:demon-blooded')!;
    expect(g).toBeDefined();
    expect(g.day).toBeGreaterThanOrEqual(reading(sable, 3).day);
    expect(sable.readings.flatMap((rd) => rd.graftsOffered.map((x) => x.feature))).toContain('second-face');
  });
});

describe('all three lives', () => {
  it('run without warnings', () => {
    for (const r of [mira, tobiah, sable]) expect(r.warnings, r.life.name).toEqual([]);
  });
  it('are deterministic', () => {
    expect(JSON.stringify(load('mira').readings)).toBe(JSON.stringify(mira.readings));
  });
});
