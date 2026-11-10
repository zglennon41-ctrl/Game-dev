// The genius tree (docs/genius-tree.md): the shape of a tree, the Readings on it, hybrids.
// Two kinds of test here. Those on the three test bases (game/tests/fixtures/bases; written
// by tools/genius-test-bases.py) say exactly what the rules do. Those on the game's own bases
// hold for whatever the designer has written there: they name no base, form or lean.
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { mkdtempSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { data, loadBases, useBases, formOf, childrenOf, hybridForms, baseOf, type Base, type Form } from '../src/data';
import { flatten, compose, signature, alike, bend } from '../src/data/tree';
import { read, take, fit, playLines, emptyTally, PLAY_LINES, type GeniusForm, type Tally } from '../src/rules/reading';
import { validateData, TREE_LEANS } from '../src/data/validate';

const TEST = 'game/tests/fixtures/bases';
const game = loadBases();
const test = loadBases(TEST);
const homes = data.homes;
afterAll(() => { useBases(game); data.homes = homes; });

const at = (id: string, more: Partial<GeniusForm> = {}): GeniusForm => {
  const f = formOf(id)!;
  return { form: f.id, base: f.base, expression: f.expression, own: f.features, heritage: [], seedMark: 'far-eyes', grafts: [], adaptations: [], ...more };
};
const tally = (t: Partial<Tally>): Tally => ({ ...emptyTally(), ...t });
const runner = { seed: 'stands-between', blood: 'ridgefolk', shape: 'anchor' };
/** Play made of exactly what some leans lean on, in their own proportions. */
function playOf(leans: Record<string, Record<string, number>>): Tally {
  const t = emptyTally();
  for (const [line, keys] of Object.entries(leans)) for (const [k, w] of Object.entries(keys)) {
    const n = Math.max(1, Math.round(w * 60));
    if (line === 'range') t.range[k] = n;
    else if (line === 'orders') t.orders[k] = n;
    else if (line === 'shape') t.families[`${k}.x`] = n;
    else if (line === 'fights') t.counters[`fights.${k}`] = n;
    else if (line === 'company') t.counters[`runs.${k}`] = n;
    else if (line === 'ground') t.ground[k] = n;
    else if (line === 'quests') t.counters[`runs.quest.${k}`] = n;
    else if (line === 'bonds') t.bonds[k] = 1;
    else if (line === 'pattern') t.intention = { form: 'x.y', terms: [], fires: k === 'fires' ? 1000 : (t.intention?.fires ?? 0), sworn: k === 'sworn' ? true : t.intention?.sworn };
  }
  return t;
}

/** A tree is 1 settled form, 3 paths, 9 prongs, 18 finishes; each form wears its own and its road's features. */
function expectTree(forms: Form[], rootLevel: number) {
  const byLevel = (n: number) => forms.filter((f) => f.level === n);
  if (rootLevel === 1) expect(byLevel(1)).toHaveLength(1);
  expect([byLevel(2).length, byLevel(3).length, byLevel(4).length]).toEqual([3, 9, 18]);
  expect(new Set(forms.map((f) => f.id)).size).toBe(forms.length);
  const ids = new Map(forms.map((f) => [f.id, f]));
  for (const f of forms) {
    expect(f.children).toHaveLength(f.level === 1 || f.level === 2 ? 3 : f.level === 3 ? 2 : 0);
    for (const c of f.children) expect(ids.get(c)!.parent).toBe(f.id);
    const parent = ids.get(f.parent);
    if (parent) for (const x of parent.features) expect(f.features, `${f.id} wears its road`).toContain(x);
    for (const x of f.own) expect(f.features).toContain(x);
  }
}

describe('the game\'s own bases, whatever they are', () => {
  beforeEach(() => { useBases(game); data.homes = homes; });

  it('every base is a tree of thirty-one forms, each asked for by its id', () => {
    expect(data.bases.length).toBeGreaterThan(0);
    for (const b of data.bases) {
      const forms = data.forms.filter((f) => f.base === b.id);
      expect(forms, b.id).toHaveLength(31);
      expectTree(forms, 1);
      expect(forms[0].id).toBe(b.settled.id);
      for (const f of forms) { expect(formOf(f.id)).toBe(f); expect(f.kind).toBe(b.name); }
      expect(childrenOf(b.settled.id).map((f) => f.id)).toEqual(b.paths.map((p) => p.id));
    }
  });

  it('a form wears its own body, or that of the nearest form above it that names one, or its base\'s', () => {
    for (const b of data.bases) {
      const walk = (n: any, worn: string) => {
        const sil = n.silhouette ?? worn;
        expect(formOf(n.id)!.silhouette, n.id).toBe(sil);
        for (const c of n.prongs ?? n.finishes ?? []) walk(c, sil);
      };
      walk({ ...b.settled, prongs: b.paths }, b.silhouette);
    }
  });

  it('every lean is on a line and key the Tally answers', () => {
    for (const f of data.forms) for (const [line, keys] of Object.entries(f.leans)) for (const k of Object.keys(keys)) expect(TREE_LEANS[line], `${f.id}: ${line}.${k}`).toContain(k);
    // and the Tally answers every one of them
    const full = tally({
      range: { close: 1, mid: 1, far: 1 }, orders: { guard: 1, hunt: 1, hold: 1, free: 1 },
      families: { 'anchor.wall': 1, 'turn.element': 1, 'cast.reach': 1, 'read.sight': 1, 'bind.contract': 1, 'make.ward': 1 },
      ground: { tunnel: 1, wild: 1, water: 1, ruin: 1, night: 1, quiet: 1 }, bonds: { classmate: 1, shade: 1, named: 1 },
      intention: { form: 'cast.reach', terms: [], fires: 10, sworn: true },
      counters: { 'fights.parries': 1, 'fights.blocks': 1, 'fights.hurts': 1, 'fights.dodges': 1, 'runs.alone': 1, 'runs.party': 1,
        'runs.quest.linework': 1, 'runs.quest.salvage': 1, 'runs.quest.hunt': 1, 'runs.quest.escort': 1, 'runs.quest.writ': 1, 'runs.quest.deep-run': 1 },
    });
    const lines = playLines(full);
    expect(Object.keys(TREE_LEANS).sort()).toEqual([...PLAY_LINES].sort());
    for (const [line, keys] of Object.entries(TREE_LEANS)) for (const k of keys) expect(lines.shares[line][k], `${line}.${k}`).toBeGreaterThan(0);
  });

  it('the rite offers three bases to every Seed and Shape, each carrying the Seed-mark, the same every time', () => {
    for (const s of data.seeds) for (const shape of ['anchor', 'turn', 'cast', 'read', 'bind', 'make']) {
      const origin = { seed: s.id, blood: '', shape };
      const r = read({ instar: 1, tally: emptyTally(), origin, current: null });
      expect(r.candidates).toHaveLength(Math.min(3, data.bases.length));
      expect(new Set(r.candidates.map((c) => c.base)).size).toBe(r.candidates.length);
      for (const c of r.candidates) { expect(c.level).toBe(1); expect(c.features).toContain(s.seedMark); expect(baseOf(c.base)!.settled.id).toBe(c.form); }
      expect(read({ instar: 1, tally: emptyTally(), origin, current: null })).toEqual(r);
    }
  });

  it('a home leans the second and third offers and never moves the best fit', () => {
    let leaned = 0;
    for (const home of Object.keys(data.homes)) for (const s of data.seeds) for (const shape of ['anchor', 'cast', 'read']) {
      const here = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood: '', shape, home }, current: null });
      const nowhere = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood: '', shape }, current: null });
      expect(here.candidates[0].form).toBe(nowhere.candidates[0].form);
      for (const c of here.candidates) if (c.reasons.some((r) => r.line === 'home')) { leaned++; expect(data.homes[home][c.base]).toBeGreaterThan(1); expect(c).not.toBe(here.candidates[0]); }
    }
    // a lean that names a base that exists shows somewhere
    if (Object.values(data.homes).some((l) => Object.keys(l).some((k) => baseOf(k)))) expect(leaned).toBeGreaterThan(0);
  });

  it('a refinement offers the children of the form it is and nothing else, down every road', () => {
    const play = tally({ range: { close: 30, far: 4 }, orders: { hunt: 20, guard: 6 }, families: { 'cast.reach': 14 }, ground: { wild: 8 }, counters: { 'fights.parries': 12, 'runs.party': 6 } });
    for (const b of data.bases) for (const f of data.forms.filter((x) => x.base === b.id)) {
      const r = read({ instar: f.level + 1, tally: play, origin: runner, current: at(f.id) });
      if (f.level === 4) { expect(r.grows).toBe(true); expect(r.candidates.map((c) => c.form)).toEqual([f.id]); continue; }
      expect(r.grows).toBe(false);
      expect(r.candidates.map((c) => c.form).sort()).toEqual([...f.children].sort());
      for (let i = 1; i < r.candidates.length; i++) expect(r.candidates[i - 1].score).toBeGreaterThanOrEqual(r.candidates[i].score);
      if (f.level !== 1) expect(r.turning).toBeNull();
    }
  });

  it('play made of what a form leans on speaks for that form, in its own words', () => {
    for (const f of data.forms.filter((x) => x.level >= 2)) {
      const r = read({ instar: f.level, tally: playOf(f.leans), origin: runner, current: at(f.parent) });
      const own = r.candidates.find((c) => c.form === f.id)!;
      expect(own.score, f.id).toBeGreaterThan(0);
      for (const why of own.reasons) expect(f.leans[why.line]?.[why.key], `${f.id}: ${why.line}.${why.key}`).toBeGreaterThan(0);
    }
  });

  it('every ordered pair makes a hybrid with a tree of its own, its three paths each earned by their own play', () => {
    for (const a of data.bases) for (const b of data.bases) {
      if (a.id === b.id) { expect(hybridForms(a.id, b.id)).toEqual([]); continue; }
      const forms = hybridForms(a.id, b.id);
      expect(forms, `${a.id}+${b.id}`).toHaveLength(30);
      expectTree(forms, 2);
      const paths = forms.filter((f) => f.level === 2);
      expect(new Set(paths.map((f) => signature(f.leans).sig.join('|'))).size, `${a.id}+${b.id}: its paths' signatures`).toBe(3);
      for (const f of forms) {
        expect(f.id.startsWith(`${a.id}+${b.id}:`)).toBe(true);
        expect(formOf(f.id)).toBe(f);
        expect(f.base).toBe(`${a.id}+${b.id}`);
        // the first's body, the second's gift, a coat of the second's
        expect(f.expression).toBe(a.expression);
        expect(f.coatOf).toBe(b.silhouette);
        for (const g of b.hybrid.gift) expect(f.features).toContain(g);
        for (const x of a.settled.features) expect(f.features).toContain(x);
      }
      for (const p of paths) expect(p.parent).toBe(a.settled.id);
      // in every path one prong is the second's, carried across with its finishes
      for (const p of paths) {
        const prongs = p.children.map((c) => formOf(c)!);
        const carried = prongs.filter((q) => q.id.startsWith(`${a.id}+${b.id}:${b.id}-`));
        expect(carried, p.id).toHaveLength(1);
        for (const c of carried[0].children) expect(c.startsWith(`${a.id}+${b.id}:${b.id}-`)).toBe(true);
      }
    }
  });
});

describe('the rules, on the three test bases', () => {
  beforeEach(() => { useBases(test); data.homes = { columbia: { tlamp: 1.8 } }; });

  it('the test bases keep every rule of the specification', () => {
    expect(validateData('data', { basesDir: TEST }).filter((p) => p.file.startsWith('genius-'))).toEqual([]);
  });

  it('the validator says what is wrong with a base', () => {
    // the three test bases, one of them broken: no soul, a path that says nothing of what it is
    // the picture of, and two paths earned by the same play
    const dir = mkdtempSync(join(tmpdir(), 'bases-'));
    for (const f of readdirSync(TEST)) {
      const b = JSON.parse(readFileSync(join(TEST, f), 'utf8'));
      if (b.id === 'trun') { delete b.soul; delete b.paths[2].of; b.paths[1].leans = b.paths[0].leans; b.paths[0].prongs[0].leans = { range: { near: 1 } }; b.settled.features = ['no-such-part']; }
      writeFileSync(join(dir, f), JSON.stringify(b));
    }
    const said = validateData('data', { basesDir: dir }).filter((p) => p.file === 'genius-bases/trun.json').map((p) => p.message).join('\n');
    expect(said).toContain('no soul');
    expect(said).toContain('1 forms without of');
    expect(said).toContain('trun-b is earned by the same play as trun-a');
    expect(said).toContain('three paths, three different lines');
    expect(said).toContain('trun-a1 leans on range.near');
    expect(said).toContain('feature no-such-part');
    expect(validateData('data', { basesDir: dir }).filter((p) => p.file.startsWith('genius-bases/t') && !p.file.endsWith('trun.json'))).toEqual([]);
  });

  it('play that is all one path\'s leans is read as that path, and then as one of its prongs', () => {
    for (const b of data.bases) for (const p of b.paths) {
      const r = read({ instar: 2, tally: playOf(p.leans!), origin: runner, current: at(b.settled.id) });
      expect(r.candidates[0].form, p.id).toBe(p.id);
      for (const q of p.prongs!) expect(read({ instar: 3, tally: playOf(q.leans!), origin: runner, current: at(p.id) }).candidates[0].score).toBe(read({ instar: 3, tally: playOf(q.leans!), origin: runner, current: at(p.id) }).candidates.find((c) => c.form === q.id)!.score);
    }
  });

  it('flatten: ids, levels, parents, features down the road, the soul\'s fields', () => {
    const b = baseOf('tedge')!;
    const forms = flatten(b);
    expectTree(forms, 1);
    const fin = formOf('tedge-a1x')!;
    expect([fin.level, fin.parent, formOf(fin.parent)!.parent, formOf('tedge-a')!.parent, formOf('tedge-small')!.parent]).toEqual([4, 'tedge-a1', 'tedge-a', 'tedge-small', '']);
    expect(fin.features).toEqual([...new Set([...b.settled.features, ...b.paths[0].features, ...b.paths[0].prongs![0].features, ...b.paths[0].prongs![0].finishes![0].features])]);
    expect(fin.of).toBe('one who is like Test Edge Finish A1X');
    expect(fin.sign).toContain('Test Edge Finish A1X');
    expect(fin.habit).toContain('counts to itself');
    expect(formOf('tedge-small')!.of).toBe('');
    expect(b.soul).toContain('soul');
    expect(fin.instars).toEqual({ min: 4, max: 6 });
    expect(formOf('tedge-a')!.instars).toEqual({ min: 2, max: 2 });
  });

  it('a prong that names its own body is worn by its finishes too', () => {
    expect(formOf('tedge-b')!.silhouette).toBe('relic-knife');
    expect(['tedge-b1', 'tedge-b1x', 'tedge-b1y'].map((id) => formOf(id)!.silhouette)).toEqual(['relic-blade', 'relic-blade', 'relic-blade']);
    expect(formOf('tedge-b2')!.silhouette).toBe('relic-knife');
    expect(formOf('tedge-b1x')!.coatOf).toBe('relic-blade');
  });

  it('the rite: the calls of Seed, blood and Shape, by their weights', () => {
    const r = read({ instar: 1, tally: emptyTally(), origin: { seed: 'i-can-hold', blood: 'long-stride', shape: 'cast' }, current: null });
    // tedge: seed 1.0 x 1 + blood 0.3 x 1 + shape 0.6 x 0.6
    expect(r.candidates[0]).toMatchObject({ form: 'tedge-small', base: 'tedge', level: 1, score: 1.66 });
    expect(r.candidates[0].reasons.map((x) => x.line)).toEqual(['seed', 'shape', 'blood']);
    expect(r.level).toBe(1);
    expect(r.turning).toBeNull();
  });

  it('the rite: a home raises a base for the second and third offers only', () => {
    const o = { seed: 'i-can-hold', blood: '', shape: 'read' };
    const here = read({ instar: 1, tally: emptyTally(), origin: { ...o, home: 'columbia' }, current: null });
    const nowhere = read({ instar: 1, tally: emptyTally(), origin: o, current: null });
    expect(here.candidates.map((c) => c.form)).toEqual(['tedge-small', 'tlamp-small', 'trun-small']);
    expect(here.candidates[0]).toEqual(nowhere.candidates[0]);
    // the score stays the Reading's own; the offer says it is for the home's sake
    expect(here.candidates[1].score).toBe(nowhere.candidates[1].score);
    expect(here.candidates[1].reasons[here.candidates[1].reasons.length - 1]).toMatchObject({ line: 'home', key: 'columbia' });
    // a lean can change which base is offered second
    const w = { seed: 'watches-from-above', blood: '', shape: 'read' };   // trun 0.5, tlamp 0.36, tedge 0.18
    expect(read({ instar: 1, tally: emptyTally(), origin: w, current: null }).candidates.map((c) => c.base)).toEqual(['trun', 'tlamp', 'tedge']);
    data.homes = { columbia: { tedge: 5 } };
    expect(read({ instar: 1, tally: emptyTally(), origin: { ...w, home: 'columbia' }, current: null }).candidates.map((c) => c.base)).toEqual(['trun', 'tedge', 'tlamp']);
  });

  it('a refinement: the fit of a path is the play on what it leans on (the worked example)', () => {
    // trun-a leans orders.hunt 1.0 and ground.wild 0.6. Orders: hunt 22 of 26, line heard in
    // full (26 of 20). Ground: wild 9 of 11, heard in full (11 of 10), weight 0.7.
    const t = tally({ orders: { hunt: 22, guard: 4 }, ground: { wild: 9, ruin: 2 } });
    const want = (1.0 * 1 * 1.0 * (22 / 26) + 0.7 * 1 * 0.6 * (9 / 11)) / 1.6;
    const f = fit(formOf('trun-a')!.leans, playLines(t));
    expect(f.score).toBeCloseTo(want, 10);
    expect(f.reasons.map((r) => `${r.line}.${r.key}`)).toEqual(['orders.hunt', 'ground.wild']);
    const r = read({ instar: 2, tally: t, origin: runner, current: at('trun-small') });
    expect(r.candidates[0]).toMatchObject({ form: 'trun-a', score: Math.round(want * 1000) / 1000 });
    expect(r.candidates.map((c) => c.form).sort()).toEqual(['trun-a', 'trun-b', 'trun-c']);
    expect(r.level).toBe(2);
  });

  it('a line with little play on it counts for little', () => {
    const little = fit(formOf('trun-a')!.leans, playLines(tally({ orders: { hunt: 2 } })));
    const much = fit(formOf('trun-a')!.leans, playLines(tally({ orders: { hunt: 40 } })));
    expect(little.score).toBeCloseTo(much.score * 0.1, 10);
  });

  it('with nothing played the paths come in the order they are written, and it may settle on the first', () => {
    const r = read({ instar: 2, tally: emptyTally(), origin: runner, current: at('trun-small') });
    expect(r.candidates.map((c) => [c.form, c.score])).toEqual([['trun-a', 0], ['trun-b', 0], ['trun-c', 0]]);
    expect(r.turning).toBeNull();
  });

  it('what it kept fed becomes part of it at a refinement; a graft is carried', () => {
    const cur = at('trun-small', { adaptations: [{ id: 'set-feet', lastFed: 3 }], grafts: [{ id: 'shade:x', feature: 'lantern', source: 'shade:x' }] });
    const r = read({ instar: 2, tally: tally({ orders: { hunt: 30 } }), origin: runner, current: cur });
    const mark = data.seeds.find((s) => s.id === runner.seed)!.seedMark;
    for (const c of r.candidates) { expect(c.heritage).toEqual(['set-feet']); expect(c.seedMark).toBe(mark); expect(c.features).toEqual(expect.arrayContaining([mark, 'set-feet', 'lantern'])); }
    const g = take(cur, r.candidates[0]);
    expect(g).toMatchObject({ form: 'trun-a', base: 'trun', heritage: ['set-feet'], adaptations: [] });
    expect(g.grafts).toHaveLength(1);
  });

  it('a finished form is offered nothing new: it grows, keeping what it kept fed', () => {
    const r = read({ instar: 5, tally: tally({ orders: { hunt: 30 } }), origin: runner, current: at('trun-a2x', { adaptations: [{ id: 'set-feet', lastFed: 1 }] }) });
    expect(r.grows).toBe(true);
    expect(r.candidates).toHaveLength(1);
    expect(r.candidates[0]).toMatchObject({ form: 'trun-a2x', heritage: ['set-feet'] });
    expect(take(at('trun-a2x'), r.candidates[0]).form).toBe('trun-a2x');
  });

  it('a whole life on the tree: settled, a path, a prong, a finish, then two ages as itself', () => {
    let g: GeniusForm | null = null;
    const road: string[] = [];
    for (let n = 1; n <= 6; n++) {
      const r = read({ instar: n, tally: n === 1 ? emptyTally() : tally({ orders: { hunt: 30 }, ground: { wild: 12 } }), origin: runner, current: g });
      g = take(g, r.candidates[0]);
      road.push(g.form);
      expect(r.grows).toBe(n >= 5);
    }
    expect(road.slice(0, 2)).toEqual(['trun-small', 'trun-a']);
    expect(formOf(road[2])!.parent).toBe('trun-a');
    expect(formOf(road[3])!.parent).toBe(road[2]);
    expect(road.slice(3)).toEqual([road[3], road[3], road[3]]);
  });

  describe('the turning', () => {
    // Since it settled it has been played like a Test Edge: close, parrying, casting.
    const edged = tally({ range: { close: 40, mid: 2 }, families: { 'cast.reach': 22 }, counters: { 'fights.parries': 30, 'fights.dodges': 4 } });

    it('is offered at the first refinement when another base\'s nature fits the play better by the margin', () => {
      const r = read({ instar: 2, tally: edged, origin: runner, current: at('trun-small') });
      expect(r.turning).not.toBeNull();
      const t = r.turning!;
      expect(t).toMatchObject({ second: 'tedge', base: 'trun+tedge', name: 'Edged Test Runner' });
      expect(t.other).toBeGreaterThanOrEqual(data.hybrids.rule.min);
      expect(t.other).toBeGreaterThanOrEqual(t.own * (1 + data.hybrids.rule.margin));
      expect(t.reasons.map((x) => `${x.line}.${x.key}`)).toEqual(['range.close', 'fights.parries', 'shape.cast']);
      // offered beside its own three paths, never in place of them
      expect(r.candidates.map((c) => c.form).sort()).toEqual(['trun-a', 'trun-b', 'trun-c']);
      expect(t.candidates.map((c) => c.form).sort()).toEqual(['trun+tedge:trun-a', 'trun+tedge:trun-b', 'trun+tedge:trun-c']);
      // taking it makes the genius the hybrid, on the hybrid's own tree from there
      const g = take(at('trun-small'), t.candidates[0]);
      expect(g.base).toBe('trun+tedge');
      expect(g.own).toEqual(expect.arrayContaining(['edge', ...baseOf('trun')!.settled.features]));
      const next = read({ instar: 3, tally: edged, origin: runner, current: g });
      expect(next.turning).toBeNull();
      expect(next.candidates.map((c) => c.form).sort()).toEqual([...formOf(g.form)!.children].sort());
    });

    it('is not offered to play that fits its own nature, nor below the least fit, nor after the first refinement', () => {
      const own = read({ instar: 2, tally: edged, origin: { seed: 'i-can-hold', blood: '', shape: 'cast' }, current: at('tedge-small') });
      expect(own.turning).toBeNull();
      const faint = read({ instar: 2, tally: tally({ range: { close: 3 } }), origin: runner, current: at('trun-small') });
      expect(faint.turning).toBeNull();
      expect(read({ instar: 3, tally: edged, origin: runner, current: at('trun-a') }).turning).toBeNull();
    });

    it('the margin and the least fit are data', () => {
      const rule = data.hybrids.rule;
      const kept = { ...rule };
      const reads = () => read({ instar: 2, tally: edged, origin: runner, current: at('trun-small') }).turning;
      rule.min = 0.99;
      const tooFaint = reads();
      rule.min = kept.min;
      // a runner played half as itself: its own nature fits too, so a wide margin refuses
      const half = tally({ ...edged, orders: { hunt: 30 }, ground: { wild: 12 }, counters: { ...edged.counters, 'runs.party': 10 } });
      const offered = read({ instar: 2, tally: half, origin: runner, current: at('trun-small') });
      rule.margin = 0.05;
      const narrow = read({ instar: 2, tally: half, origin: runner, current: at('trun-small') }).turning;
      Object.assign(rule, kept);
      expect(tooFaint).toBeNull();
      expect(offered.turning).toBeNull();
      expect(narrow === null).toBe(fit(baseOf('tedge')!.nature, playLines(half)).score < fit(baseOf('trun')!.nature, playLines(half)).score * 1.05);
    });
  });

  describe('a hybrid, composed by rule', () => {
    it('trun+tedge in full: names, the carried prongs, the bent leans, the soul\'s fields', () => {
      const a = baseOf('trun')!, b = baseOf('tedge')!;
      const forms = hybridForms('trun', 'tedge');
      expectTree(forms, 2);
      const paths = forms.filter((f) => f.level === 2);
      expect(paths.map((f) => f.name)).toEqual(['Edged Test Runner Path A', 'Edged Test Runner Path B', 'Edged Test Runner Path C']);
      expect(paths.every((f) => f.kind === 'Edged Test Runner')).toBe(true);
      // a path's leans are half its own and half the second's nature
      expect(paths[0].leans).toEqual(bend(a.paths[0].leans!, b.nature, data.hybrids.rule.bend));
      expect(paths[0].leans).toEqual({ orders: { hunt: 0.5 }, ground: { wild: 0.3 }, range: { close: 0.5 }, fights: { parries: 0.4 }, shape: { cast: 0.25 } });
      expect(paths[0].text).toBe(`${a.paths[0].text} ${b.hybrid.text}`);
      // what it is the picture of, its sign (the second's gift), its habit (the first's)
      expect(paths[0].of).toBe('one who is like Test Runner Path A, turned toward the test edge\'s way');
      expect(paths[0].sign).toBe(`${a.paths[0].sign} It wears an edge, the test edge's.`);
      expect(paths[0].habit).toBe(a.paths[0].habit);
      for (let i = 0; i < 3; i++) {
        const P = a.paths[i];
        const prongs = paths[i].children.map((c) => formOf(c)!);
        // the prong furthest from the second's nature gave way (of equal ones, the last)
        const scores = P.prongs!.map((q) => alike(q.leans!, b.nature));
        const drop = scores.lastIndexOf(Math.min(...scores));
        prongs.forEach((q, j) => {
          if (j !== drop) { expect(q.id).toBe(`trun+tedge:${P.prongs![j].id}`); expect(q.name).toBe(P.prongs![j].name); expect(q.habit).toBe(P.prongs![j].habit); return; }
          expect(q.id.startsWith('trun+tedge:tedge-')).toBe(true);
          expect(q.name.startsWith('Running Test Edge Prong')).toBe(true);
          expect(q.of).toBe(formOf(q.id.split(':')[1])!.of);              // it is still the picture of what it was
          expect(q.sign).toBe('It wears an edge, the test edge\'s.');
          expect(q.habit).toBe(P.prongs![drop].habit);                     // and does what the prong it replaced did
          expect(q.children.map((c) => formOf(c)!.habit)).toEqual(P.prongs![drop].finishes!.map((f) => f.habit));
          expect(q.silhouette).toBe(a.silhouette);
        });
      }
      // each of the second's prongs is carried once
      const carried = forms.filter((f) => f.level === 3 && f.id.includes(':tedge-')).map((f) => f.id);
      expect(new Set(carried).size).toBe(3);
    });

    it('the other way round is another genius', () => {
      const ab = hybridForms('trun', 'tedge'), ba = hybridForms('tedge', 'trun');
      expect(ba[0].kind).toBe('Running Test Edge');
      expect(ba[0].expression).toBe('relic');
      expect(ba[0].coatOf).toBe('beast-runner');
      expect(ab[0].coatOf).toBe('relic-knife');
      expect(ba.map((f) => f.id)).not.toEqual(ab.map((f) => f.id));
    });

    it('two paths are never earned by the same play: a path that would be bends less far', () => {
      // a second base whose nature outweighs every path of the first
      const heavy: Base = { ...baseOf('tedge')!, id: 'theavy', nature: { range: { close: 1 }, fights: { parries: 1 } } };
      const light: Base = { ...baseOf('trun')!, paths: baseOf('trun')!.paths.map((p, i) => ({ ...p, leans: [{ orders: { hunt: 0.4 }, ground: { wild: 0.3 } }, { orders: { guard: 0.4 }, ground: { ruin: 0.3 } }, { bonds: { named: 0.4 }, ground: { night: 0.3 } }][i] })) };
      const paths = compose(light, heavy, data.hybrids).filter((f) => f.level === 2);
      const sigs = paths.map((f) => signature(f.leans).sig.join('|'));
      expect(sigs[0]).toBe('fights.parries|range.close');      // the first is bent all the way the rule says
      expect(new Set(sigs).size).toBe(3);                       // the others less far, so each keeps a play of its own
    });

    it('a pair written by hand says its own words', () => {
      const hy = { rule: data.hybrids.rule, pairs: { 'trun+tedge': { name: 'Knife-Runner', nodes: { 'trun-a': { name: 'Knife-Courser', of: 'one who closes the distance', sign: 'A blade where its teeth were.', habit: 'It whets itself.' }, 'tedge-b3': { name: 'Borrowed Edge' } } } } };
      const forms = compose(baseOf('trun')!, baseOf('tedge')!, hy);
      const p = forms.find((f) => f.id === 'trun+tedge:trun-a')!;
      expect(p).toMatchObject({ name: 'Knife-Courser', kind: 'Knife-Runner', of: 'one who closes the distance', sign: 'A blade where its teeth were.', habit: 'It whets itself.' });
      expect(forms.find((f) => f.id === 'trun+tedge:tedge-b3')!.name).toBe('Borrowed Edge');
      // what is not written by hand is still the rule's
      expect(forms.find((f) => f.id === 'trun+tedge:trun-b')!.name).toBe('Edged Test Runner Path B');
    });

    it('signature: the two heaviest leans; of equal ones the first written', () => {
      expect(signature({ orders: { hunt: 1 }, range: { close: 0.6, far: 0.2 } })).toEqual({ first: 'orders.hunt', sig: ['orders.hunt', 'range.close'] });
      expect(signature({ range: { close: 0.5 }, orders: { hunt: 1, guard: 0.5 } })).toEqual({ first: 'orders.hunt', sig: ['orders.hunt', 'range.close'] });
      expect(signature({ range: { close: 1 } }).sig).toEqual(['range.close']);
    });
  });
});
