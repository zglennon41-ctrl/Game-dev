import { describe, it, expect } from 'vitest';
import { data } from '../src/data';
import { affinity, costMultiplier, opposite, wheelDistance, tickWill, spendWill, perfectHold, stageOutput } from '../src/rules/field';
import { buildPattern, patternMultiplier, chainBeats, judgeUse, triggerPredicates, barConditions, tollEffects, PatternError } from '../src/rules/terms';
import { tierFor, resonance, verses, payingTier, shadowCap, geniusWill, isAccord, readingDue } from '../src/rules/resonance';
import { marksFor, rankFor, crossTitle, foundingEligible, gradeFor } from '../src/rules/marks';
import { read, emptyTally } from '../src/rules/reading';

describe('field', () => {
  it('wheel distance, opposites, affinity 100/80/60/40', () => {
    expect(wheelDistance('anchor', 'anchor')).toBe(0);
    expect(wheelDistance('anchor', 'make')).toBe(1);
    expect(wheelDistance('anchor', 'cast')).toBe(2);
    expect(opposite('anchor')).toBe('read');
    expect(opposite('bind')).toBe('turn');
    expect(opposite('make')).toBe('cast');
    expect([affinity('cast', 'cast'), affinity('cast', 'read'), affinity('cast', 'bind'), affinity('cast', 'make')]).toEqual([1, 0.8, 0.6, 0.4]);
    expect(costMultiplier('cast', 'make')).toBe(2);
  });
  it('Will: regen 4/s open, 0 Still, stance drains 2/s, faint at 0 until 20, perfect Hold refunds 10', () => {
    expect(tickWill({ will: 50, state: 'open' }, 1).will).toBe(54);
    expect(tickWill({ will: 50, state: 'still' }, 10).will).toBe(50);
    expect(tickWill({ will: 50, state: 'shaped' }, 1).will).toBe(48);
    const fainted = spendWill({ will: 10, state: 'open' }, 10)!;
    expect(fainted.state).toBe('fainted');
    expect(spendWill(fainted, 1)).toBeNull();
    expect(tickWill(fainted, 4).state).toBe('fainted');
    expect(tickWill(fainted, 5).state).toBe('open');
    expect(perfectHold({ will: 95, state: 'held' }).will).toBe(100);
    expect([1, 2, 3, 4].map(stageOutput)).toEqual([1, 2, 3, 4]);
  });
});

describe('terms', () => {
  it('worked examples from the Terms tab', () => {
    expect(patternMultiplier(['struck-first', 'no-weapon', 'never-unarmed'], false)).toBe(4.5); // Last Word
    expect(patternMultiplier(['with-member-behind', 'season-no-stance'], true)).toBe(6); // Ridgeback
    expect(patternMultiplier(['seventh-beat', 'genius-sits-out'], false)).toBe(3); // Eleven Bells
    expect(patternMultiplier(['blood-bared', 'year-of-life', 'never-save-myself'], true)).toBe(9); // Cold Mother
  });
  it('x9 is the ceiling', () => {
    expect(patternMultiplier(['blood-bared', 'year-of-life', 'never-save-myself', 'half-health'], true)).toBe(9);
  });
  it('chain: 3 beats + 1 per Term + verses', () => {
    expect(chainBeats(0)).toBe(3);
    expect(chainBeats(3)).toBe(6);
    expect(chainBeats(3, 2)).toBe(8);
  });
  it('a Pattern is built from the own Shape, one Term per kind, up to three', () => {
    expect(() => buildPattern({ name: 'x', form: 'cast.reach', terms: [], sworn: false }, { shape: 'anchor' })).toThrow(PatternError);
    expect(() => buildPattern({ name: 'x', form: 'anchor.wall', terms: ['struck-first', 'below-half'], sworn: false }, { shape: 'anchor' })).toThrow(/one Term of each kind/);
    expect(() => buildPattern({ name: 'x', form: 'anchor.wall', terms: ['year-of-life'], sworn: false }, { shape: 'anchor' })).toThrow(/Sworn characters only/);
    const p = buildPattern({ name: 'Ridgeback', form: 'anchor.wall', terms: ['with-member-behind', 'season-no-stance'], sworn: true }, { shape: 'anchor' });
    expect(p.multiplier).toBe(6);
    expect(p.chainBeats).toBe(5);
    expect(p.output).toBe(24);
  });
  it('a Sworn character may take a fourth Term of any kind', () => {
    const p = buildPattern({ name: 'x', form: 'anchor.wall', terms: ['struck-first', 'below-half', 'no-weapon', 'never-unarmed'], sworn: true }, { shape: 'anchor', swornCharacter: true });
    expect(p.terms.length).toBe(4);
  });
  it('a Trigger unmet makes it unavailable; a Bar warns; an override is the breach', () => {
    const p = { name: 'Stoop', form: 'cast.reach', terms: ['after-perfect-hold', 'genius-sits-out', 'never-unarmed'], sworn: false };
    expect(judgeUse(p, {}).kind).toBe('unavailable');
    expect(judgeUse(p, { afterPerfectHold: true })).toEqual({ kind: 'fires', tolls: ['geniusSitsOut'] });
    expect(judgeUse(p, { afterPerfectHold: true, target: { unarmed: true } })).toEqual({ kind: 'warn-bar', bars: ['never-unarmed'] });
    const b = judgeUse(p, { afterPerfectHold: true, target: { unarmed: true } }, { override: true });
    expect(b.kind === 'breach' && b.consequence).toBe('lost-for-season');
    expect((judgeUse({ ...p, sworn: true }, { afterPerfectHold: true, target: { unarmed: true } }, { override: true }) as { consequence: string }).consequence).toBe('lost-forever');
    expect((judgeUse({ ...p, sworn: true }, { afterPerfectHold: true, target: { unarmed: true } }, { override: true, swornCharacter: true }) as { consequence: string }).consequence).toBe('death');
  });
  it('the grammar is 20 Triggers, 20 Tolls, 15 Bars, and every one is implemented', () => {
    const k = (kind: string) => data.terms.filter((t) => t.kind === kind);
    expect([k('trigger').length, k('toll').length, k('bar').length]).toEqual([20, 20, 15]);
    for (const t of k('trigger')) expect(triggerPredicates[t.predicate!], t.id).toBeTypeOf('function');
    for (const t of k('bar')) expect(barConditions[t.forbids!], t.id).toBeTypeOf('function');
    for (const t of k('toll')) expect(tollEffects.has(t.apply!), t.id).toBe(true);
  });
});

describe('resonance', () => {
  const base = { built: true, sworn: false, masterInArchetype: false, stage4Days: 0 };
  it('tier thresholds are exact', () => {
    expect(tierFor({ ...base, built: false, uses: 1000 })).toBe(0);
    expect(tierFor({ ...base, uses: 0 })).toBe(1);
    expect(tierFor({ ...base, uses: 49 })).toBe(1);
    expect(tierFor({ ...base, uses: 50 })).toBe(2);
    expect(tierFor({ ...base, uses: 149 })).toBe(2);
    expect(tierFor({ ...base, uses: 150 })).toBe(3);
    expect(tierFor({ ...base, uses: 400, stage4Days: 364 })).toBe(3);
    expect(tierFor({ ...base, uses: 399, stage4Days: 365 })).toBe(3);
    expect(tierFor({ ...base, uses: 400, stage4Days: 365 })).toBe(4);
    expect(tierFor({ ...base, uses: 400, stage4Days: 365, sworn: true })).toBe(4);
    expect(tierFor({ ...base, uses: 400, stage4Days: 365, sworn: true, masterInArchetype: true })).toBe(5);
  });
  it('Resonance, verses, shadow cap, genius Will', () => {
    expect(resonance(2, 3)).toBe(4);
    expect(resonance(5, 1)).toBe(5);
    expect(resonance(1, 0)).toBe(1);
    expect(verses(payingTier(4, 1))).toBe(2);
    expect(verses(payingTier(5, 0))).toBe(2);
    expect(verses(payingTier(6, 5))).toBe(3);
    expect([2, 3, 4].map(shadowCap)).toEqual([1, 2, 3]);
    expect(geniusWill(1)).toBe(40);
    expect(geniusWill(6)).toBe(90);
    expect(isAccord(5, 5)).toBe(true);
    expect(isAccord(5, 4)).toBe(false);
  });
  it('a Reading needs its unlock and the minimum days', () => {
    expect(readingDue(3, 20, new Set(['pattern-built']), 1)).toBeNull();
    expect(readingDue(3, 30, new Set(['pattern-built']), 1)).toBe('pattern-built');
    expect(readingDue(4, 100, new Set(), 4)).toBe('tier:4');
    expect(readingDue(6, 600, new Set(['master']), 5)).toBeNull();
  });
});

describe('marks', () => {
  it('Marks by color, Sworn x2, Archivist x1.25', () => {
    expect(['green', 'amber', 'red', 'black'].map((c) => marksFor(c as 'green'))).toEqual([1, 2, 3, 5]);
    expect(marksFor('red', { swornCharacter: true })).toBe(6);
    expect(marksFor('amber', { archivist: true })).toBe(2.5);
  });
  it('ranks', () => {
    expect(rankFor({ marks: 9, stage: 4, patternBuiltIn: false })).toBe('journeyman');
    expect(rankFor({ marks: 10, stage: 3, patternBuiltIn: false })).toBe('journeyman');
    expect(rankFor({ marks: 10, stage: 4, patternBuiltIn: false })).toBe('adept');
    expect(rankFor({ marks: 50, stage: 4, patternBuiltIn: false })).toBe('adept');
    expect(rankFor({ marks: 50, stage: 4, patternBuiltIn: true })).toBe('master');
  });
  it('grades', () => {
    expect([0, 99, 100, 499, 500].map(gradeFor)).toEqual(['learned', 'learned', 'practiced', 'practiced', 'perfected']);
  });
  it('cross title, earlier name first', () => {
    expect(crossTitle([{ archetype: 'draw-cutter', rank: 'adept', since: 300 }, { archetype: 'deadeye', rank: 'adept', since: 200 }])).toBe('Deadeye Draw-Cutter');
    expect(crossTitle([{ archetype: 'deadeye', rank: 'adept', since: 200 }, { archetype: 'draw-cutter', rank: 'journeyman', since: 0 }])).toBeNull();
  });
  it('founding: three accounts, one guild, identical Form and Terms, 10 uses each', () => {
    const m = (account: string, uses = 10, terms = ['a', 'b']) => ({ account, guild: 'g', form: 'cast.reach', terms, witnessedUses: uses });
    expect(foundingEligible([m('1'), m('2'), m('3')]).eligible).toBe(true);
    expect(foundingEligible([m('1'), m('2', 10, ['b', 'a']), m('3')]).eligible).toBe(true);
    expect(foundingEligible([m('1'), m('2'), m('2')]).eligible).toBe(false);
    expect(foundingEligible([m('1'), m('2'), m('3', 9)]).eligible).toBe(false);
    expect(foundingEligible([m('1'), m('2'), m('3', 10, ['a'])]).eligible).toBe(false);
  });
});

describe('reading', () => {
  it('offers three candidates, every one with the Seed-mark, deterministically', () => {
    const t = emptyTally();
    const r1 = read({ instar: 1, tally: t, origin: { seed: 'watches-from-above', blood: 'long-stride', shape: 'cast' }, current: null });
    const r2 = read({ instar: 1, tally: t, origin: { seed: 'watches-from-above', blood: 'long-stride', shape: 'cast' }, current: null });
    expect(r1.candidates).toHaveLength(3);
    expect(r1).toEqual(r2);
    for (const c of r1.candidates) expect(c.features).toContain('far-eyes');
  });
  it('never offers the current form', () => {
    const t = emptyTally();
    t.range.close = 50;
    const current = { form: 'stooping-kith', expression: 'kith' as const, own: ['wing-cloak', 'short-blade', 'beak'], heritage: [], seedMark: 'far-eyes', grafts: [], adaptations: [] };
    const r = read({ instar: 3, tally: t, origin: { seed: 'watches-from-above', blood: 'long-stride', shape: 'cast' }, current });
    expect(r.candidates.map((c) => c.form)).not.toContain('stooping-kith');
  });
});
