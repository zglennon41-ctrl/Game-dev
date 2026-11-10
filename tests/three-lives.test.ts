// Acceptance: docs/three-lives.md. The lives are the owner's; what they must show is what the
// rules promise, on whatever bases the genius tree has. No test here names a base, a form or a
// lean: those are the designer's, in data/genius-bases, and change. If one of these fails
// after a change to data/reading.json, data/genius-hybrids.json or data/rules.json, that is a
// design change to raise with the owner, not a test to edit.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { simulate, stateOn, monthOf, yearOf, type SimResult, type ReadingRecord } from '../src/sim/simulate';
import type { Life } from '../src/sim/script';
import { data, formOf, baseOf } from '../src/data';

const load = (id: string) => simulate(JSON.parse(readFileSync(`data/lives/${id}.json`, 'utf8')) as Life);
const mira = load('mira');
const tobiah = load('tobiah');
const sable = load('sable');

const reading = (r: SimResult, instar: number): ReadingRecord => {
  const x = r.readings.find((rd) => rd.instar === instar);
  if (!x) throw new Error(`${r.life.name} never reached instar ${instar}`);
  return x;
};

// What every life on the tree shows, whoever lives it.
for (const [name, life] of [['Mira', mira], ['Tobiah', tobiah], ['Sable', sable]] as const) {
  describe(`${name} — a life on the genius tree`, () => {
    it('the rite offers three bases, read from Seed, blood and Shape, and one settles', () => {
      const rd = reading(life, 1);
      expect(rd.result.level).toBe(1);
      expect(rd.result.candidates).toHaveLength(Math.min(3, data.bases.length));
      expect(new Set(rd.result.candidates.map((c) => c.base)).size).toBe(rd.result.candidates.length);
      // the best fit is called by something of theirs
      expect(rd.result.candidates[0].score).toBeGreaterThan(0);
      expect(rd.result.candidates[0].reasons.every((x) => ['seed', 'blood', 'shape'].includes(x.line))).toBe(true);
      expect(rd.picked.seedMark).toBe(data.seeds.find((s) => s.id === life.life.seed)!.seedMark);
      expect(baseOf(rd.picked.base)!.settled.id).toBe(rd.picked.form);
    });

    it('three refinements: a path, a prong, a finish, each one of the children of the form before', () => {
      let was = reading(life, 1).picked.form;
      for (const n of [2, 3, 4]) {
        const rd = reading(life, n);
        expect(rd.result.level).toBe(n);
        expect(rd.result.grows).toBe(false);
        expect(rd.result.candidates.map((c) => c.form).sort()).toEqual([...formOf(was)!.children].sort());
        expect(rd.result.candidates).toHaveLength(n === 4 ? 2 : 3);
        const offered = [...rd.result.candidates, ...(rd.result.turning?.candidates ?? [])];
        expect(offered.map((c) => c.form)).toContain(rd.picked.form);
        for (const c of offered) expect(c.features).toContain(rd.picked.seedMark);
        // a turning only at the first refinement, and always toward another base
        if (n > 2) expect(rd.result.turning).toBeNull();
        if (rd.result.turning) expect(rd.result.turning.second).not.toBe(reading(life, 1).picked.base);
        was = rd.picked.form;
      }
    });

    it('instars five and six: no new form; it grows as what it finished as', () => {
      const finish = reading(life, 4).picked.form;
      for (const n of [5, 6]) {
        const rd = reading(life, n);
        expect(rd.result.grows).toBe(true);
        expect(rd.picked.form).toBe(finish);
      }
      expect(life.genius.form).toBe(finish);
      expect(life.genius.instar).toBe(6);
      expect(formOf(finish)!.level).toBe(4);
      // it wears the whole road: the settled form's parts, its path's, its prong's, its own
      let f = formOf(finish);
      while (f) { for (const x of f.own) expect(life.genius.own).toContain(x); f = f.parent ? formOf(f.parent) : undefined; }
    });

    it('an adaptation it has at a refinement and can keep becomes heritage; heritage is never lost', () => {
      let kept: string[] = [];
      for (const rd of life.readings.filter((x) => x.instar >= 2)) {
        for (const a of rd.adaptationsAtReading) if (data.features.find((f) => f.id === a)?.fixable && kept.length < data.rules.genius.heritageMax) expect(rd.picked.heritage, `instar ${rd.instar}`).toContain(a);
        for (const h of kept) expect(rd.picked.heritage).toContain(h);
        kept = rd.picked.heritage;
      }
    });
  });
}

describe('Mira — says ranged, fights close', () => {
  it('fights close from the first week: set-feet by the Gate, kept as heritage', () => {
    const rd = reading(mira, 2);
    expect(rd.adaptationsAtReading).toContain('set-feet');
    expect(data.features.find((f) => f.id === 'set-feet')?.fixable).toBe(true);
    expect(rd.picked.heritage).toContain('set-feet');
    expect(mira.genius.heritage).toContain('set-feet');
  });

  it('at the Gate, if her play has turned from what the bowl read, she lets it turn', () => {
    const rd = reading(mira, 2);
    expect(mira.life.picks?.['2']?.turn).toBe(true);
    if (rd.result.turning) {
      expect(rd.picked.base).toBe(rd.result.turning.base);
      expect(rd.settled).toBe(false);
      expect(mira.genius.base).toBe(`${reading(mira, 1).picked.base}+${rd.result.turning.second}`);
    } else {
      expect(rd.settled).toBe(true);
      expect(mira.genius.base).toBe(reading(mira, 1).picked.base);
    }
  });

  it('the Third Form is read when the Pattern is built', () => {
    expect(reading(mira, 3).unlockedBy).toBe('pattern-built');
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

  it('he never chooses: every form his genius takes is the one the Tally read', () => {
    for (const rd of tobiah.readings) { expect(rd.settled).toBe(true); expect(rd.picked.form).toBe(rd.result.candidates[0].form); }
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
