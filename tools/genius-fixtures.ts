// Write reference trees and Readings from the tools' rules, for the game's own copy of them
// to match. They are made from the three test bases (game/tests/fixtures/bases; written by
// tools/genius-test-bases.py), never from the game's own, so that the parity test holds
// whatever the designer writes in data/genius-bases.
// Run: npx tsx tools/genius-fixtures.ts  (writes game/tests/fixtures/readings.json)
import { writeFileSync } from 'node:fs';
import { data, loadBases, useBases, formOf, hybridForms } from '../src/data';
import { read, take, emptyTally, type Tally, type GeniusForm, type Origin } from '../src/rules/reading';
import { resonance, payingTier, verses, shadowCap, geniusWill, tierFor } from '../src/rules/resonance';

useBases(loadBases('game/tests/fixtures/bases'));
// A home's lean, for the test: no real home leans on a test base.
const homes: Record<string, Record<string, number>> = { columbia: { tlamp: 1.8 }, edo: { tedge: 1.5, trun: 1.2 } };
data.homes = homes;

interface Case { name: string; instar: number; origin: Origin; tally: Tally; current: GeniusForm | null }
const cases: Case[] = [];

// The rite: by Seed, blood and Shape; and leaned by a home.
for (const [seed, blood, shape, home] of [
  ['i-can-hold', 'long-stride', 'cast', ''], ['never-alive', 'forgeborn', 'make', ''], ['stands-between', 'ridgefolk', 'anchor', ''],
  ['watches-from-above', '', 'read', ''], ['remembers', '', 'turn', ''], ['owes-me', 'demon-blooded', 'bind', ''],
  ['stands-between', 'ridgefolk', 'anchor', 'columbia'], ['i-can-hold', '', 'read', 'columbia'], ['never-alive', '', 'anchor', 'edo'], ['watches-from-above', 'long-stride', 'cast', 'edo'],
]) cases.push({ name: `the rite: ${seed} ${blood || 'no blood'} ${shape}${home ? ` of ${home}` : ''}`, instar: 1, origin: home ? { seed, blood, shape, home } : { seed, blood, shape }, tally: emptyTally(), current: null });

const runner: Origin = { seed: 'stands-between', blood: 'ridgefolk', shape: 'anchor' };
/** A genius standing at a form of a tree. */
const at = (id: string, more: Partial<GeniusForm> = {}): GeniusForm => {
  const f = formOf(id)!;
  return { form: f.id, base: f.base, expression: f.expression, own: f.features, heritage: [], seedMark: 'broad-guard', grafts: [], adaptations: [], ...more };
};
const tally = (t: Partial<Tally>): Tally => ({ ...emptyTally(), ...t });
const hunting = tally({ range: { close: 14, mid: 10 }, orders: { hunt: 22, guard: 4 }, ground: { wild: 9, ruin: 2 }, counters: { 'runs.party': 8, 'runs.alone': 3, 'fights.blocks': 3, 'fights.hurts': 5 } });
const guarding = tally({ range: { close: 20 }, orders: { guard: 18, hold: 3 }, families: { 'anchor.wall': 12, 'anchor.weight': 4 }, counters: { 'fights.blocks': 24, 'fights.parries': 6, 'runs.party': 4 }, runsWith: { c1: 3 } });
// Since it settled it has been played like a Test Edge: close, parrying, casting.
const edged = tally({ range: { close: 40, mid: 2 }, families: { 'cast.reach': 22, 'cast.speed': 6 }, counters: { 'fights.parries': 30, 'fights.dodges': 4, 'runs.alone': 6 }, intention: { form: 'cast.reach', terms: ['struck-first'], fires: 40, sworn: false } });
const quiet = tally({ orders: { hold: 16, guard: 2 }, ground: { night: 8, quiet: 5, post: 3 }, families: { 'read.sight': 9 }, bonds: { shade: 1 }, counters: { 'runs.quest.linework': 4, 'runs.quest.escort': 2, 'runs.party': 2 } });

cases.push({ name: 'the first refinement: a runner that hunted the wild', instar: 2, origin: runner, tally: hunting, current: at('trun-small') });
cases.push({ name: 'the first refinement: a runner that guarded and blocked', instar: 2, origin: runner, tally: guarding, current: at('trun-small') });
cases.push({ name: 'the first refinement: nothing played', instar: 2, origin: runner, tally: emptyTally(), current: at('trun-small') });
cases.push({ name: 'the first refinement: a runner played like an edge (it turns)', instar: 2, origin: runner, tally: edged, current: at('trun-small') });
cases.push({ name: 'the first refinement: a runner played like a lamp (it turns)', instar: 2, origin: runner, tally: quiet, current: at('trun-small') });
cases.push({ name: 'the first refinement: an edge played like an edge (no turning)', instar: 2, origin: { seed: 'i-can-hold', blood: '', shape: 'cast' }, tally: edged, current: at('tedge-small', { seedMark: 'grip' }) });
cases.push({ name: 'the first refinement: what it kept fed becomes heritage', instar: 2, origin: runner, tally: hunting, current: at('trun-small', { adaptations: [{ id: 'set-feet', lastFed: 3 }, { id: 'scorched', lastFed: 3 }] }) });
cases.push({ name: 'the second refinement: a path, with a graft', instar: 3, origin: runner, tally: guarding, current: at('trun-a', { heritage: ['set-feet'], grafts: [{ id: 'shade:x', feature: 'lantern', source: 'shade:x' }] }) });
cases.push({ name: 'the second refinement: a path with a sworn Pattern', instar: 3, origin: runner, tally: tally({ ...quiet, intention: { form: 'anchor.wall', terms: [], fires: 120, sworn: true }, bonds: { named: 2, classmate: 1 } }), current: at('tedge-b', { seedMark: 'grip' }) });
cases.push({ name: 'the last refinement: a prong', instar: 4, origin: runner, tally: hunting, current: at('trun-a2') });
cases.push({ name: 'the fifth instar: a finished form grows', instar: 5, origin: runner, tally: hunting, current: at('trun-a2x', { adaptations: [{ id: 'set-feet', lastFed: 3 }] }) });
cases.push({ name: 'the second refinement of a hybrid', instar: 3, origin: runner, tally: edged, current: at('trun+tedge:trun-a') });
cases.push({ name: 'the last refinement of a hybrid, on a carried prong', instar: 4, origin: runner, tally: quiet, current: at(hybridForms('trun', 'tlamp').find((f) => f.level === 3 && f.id.includes(':tlamp-'))!.id) });
// An old save catching up: past its fourth instar and still only settled.
cases.push({ name: 'the fifth instar of a genius still only settled: it is still offered its paths', instar: 5, origin: runner, tally: guarding, current: at('trun-small') });

// The whole of a life on the tree, taking the best fit each time.
let g: GeniusForm | null = null;
const life: string[] = [];
for (let n = 1; n <= 6; n++) {
  const r = read({ instar: n, tally: n === 1 ? emptyTally() : hunting, origin: runner, current: g });
  g = take(g, r.candidates[0]);
  life.push(g.form);
}

const ids = data.bases.map((b) => b.id);
const out = {
  bases: ids,
  homes,
  trees: Object.fromEntries(data.bases.map((b) => [b.id, data.forms.filter((f) => f.base === b.id)])),
  hybrids: Object.fromEntries(ids.flatMap((a) => ids.filter((b) => b !== a).map((b) => [`${a}+${b}`, hybridForms(a, b)]))),
  readings: cases.map((c) => ({ ...c, result: read({ instar: c.instar, tally: c.tally, origin: c.origin, current: c.current }) })),
  life,
  resonance: [[1, 0], [1, 2], [2, 1], [3, 3], [5, 5], [6, 1]].map(([i, t]) => ({ instar: i, tier: t, resonance: resonance(i, t), paying: payingTier(resonance(i, t), t), verses: verses(payingTier(resonance(i, t), t)), shadowCap: shadowCap(resonance(i, t)), will: geniusWill(resonance(i, t)) })),
  tiers: [0, 49, 50, 150, 400].map((uses) => ({ uses, tier: tierFor({ uses, built: true, sworn: false, masterInArchetype: false, stage4Days: 0 }) })),
};
writeFileSync('game/tests/fixtures/readings.json', JSON.stringify(out, null, 1) + '\n');
const turned = out.readings.filter((r) => r.result.turning).length;
console.log(`wrote ${out.readings.length} readings (${turned} with a turning), ${Object.keys(out.trees).length} trees and ${Object.keys(out.hybrids).length} hybrids; a life: ${life.join(' > ')}`);
