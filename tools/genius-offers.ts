// What the rite's bowl offers (docs/genius-tree.md): a designer's check that every base is
// offered to somebody, that the offers vary, and that a home leans the bowl without owning it.
// With no chance: for every Seed, Shape and blood (and none), at no home and at each of the
// thirteen.
// Run: npx tsx tools/genius-offers.ts            the census
//      npx tsx tools/genius-offers.ts --bowls    and what each Seed and Shape is offered
import { data } from '../src/data';
import { read, emptyTally } from '../src/rules/reading';

const shapes = ['anchor', 'turn', 'cast', 'read', 'bind', 'make'];
const bloods = ['', ...data.bloods.map((b) => b.id)];
const homes = Object.keys(data.homes);
const name = (id: string) => data.bases.find((b) => b.id === id)!.name;

if (process.argv.includes('--bowls')) {
  for (const s of data.seeds) {
    console.log(s.id);
    for (const shape of shapes) {
      const r = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood: '', shape }, current: null });
      console.log(`  ${shape.padEnd(7)} ${r.candidates.map((c) => `${c.name} (${name(c.base)}, ${c.score.toFixed(2)})`).join('  ·  ')}`);
    }
  }
  console.log();
}

// With no home: how often each base is the best fit, and how often among the three.
const first = new Map<string, number>();
const among = new Map<string, number>();
let bowls = 0;
const trios = new Set<string>();
for (const s of data.seeds) for (const shape of shapes) for (const blood of bloods) {
  const r = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood, shape }, current: null });
  bowls++;
  trios.add(r.candidates.map((c) => c.base).join(','));
  first.set(r.candidates[0].base, (first.get(r.candidates[0].base) ?? 0) + 1);
  for (const c of r.candidates) among.set(c.base, (among.get(c.base) ?? 0) + 1);
}
console.log(`THE BOWL, AT NO HOME: ${bowls} characters (every Seed, Shape and blood), ${trios.size} different offers of three`);
console.log(`${'base'.padEnd(12)} ${'class'.padEnd(9)} best fit   among the three`);
for (const b of data.bases) console.log(`${b.name.padEnd(12)} ${b.class.padEnd(9)} ${String(first.get(b.id) ?? 0).padStart(5)} ${(((100 * (first.get(b.id) ?? 0)) / bowls).toFixed(1) + '%').padStart(6)}   ${String(among.get(b.id) ?? 0).padStart(5)} ${(((100 * (among.get(b.id) ?? 0)) / bowls).toFixed(1) + '%').padStart(6)}`);
const never = data.bases.filter((b) => !among.has(b.id)).map((b) => b.name);
const neverFirst = data.bases.filter((b) => !first.has(b.id)).map((b) => b.name);
console.log(never.length ? `Never among the three: ${never.join(', ')}` : 'Every base is among the three for somebody.');
console.log(neverFirst.length ? `Never the best fit: ${neverFirst.join(', ')}` : 'Every base is the best fit for somebody.');

// At each home: what its lean does to the second and third offers.
console.log(`\nTHE HOMES' LEANS (how often a base is among the three for a child of that home, against a child of nowhere)`);
let moved = 0;
for (const home of homes) {
  const here = new Map<string, number>();
  const nowhere = new Map<string, number>();
  let n = 0;
  for (const s of data.seeds) for (const shape of shapes) for (const blood of bloods) {
    const a = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood, shape, home }, current: null });
    const b = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood, shape }, current: null });
    n++;
    if (a.candidates[0].form !== b.candidates[0].form) moved++;
    for (const c of a.candidates) here.set(c.base, (here.get(c.base) ?? 0) + 1);
    for (const c of b.candidates) nowhere.set(c.base, (nowhere.get(c.base) ?? 0) + 1);
  }
  const pc = (m: Map<string, number>, k: string) => `${Math.round((100 * (m.get(k) ?? 0)) / n)}%`;
  console.log(`${home.padEnd(11)} ${Object.entries(data.homes[home]).map(([k, x]) => `${name(k)} x${x}: ${pc(nowhere, k)} to ${pc(here, k)}`).join('   ')}`);
}
console.log(moved ? `A home moved the best fit ${moved} times: it must never.` : 'No home moved the best fit of any bowl.');
