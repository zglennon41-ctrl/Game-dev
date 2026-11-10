// What the rite's bowl offers for every Seed and Shape (no blood, no chance): a designer's check
// that the First Forms vary and that every Expression has a way in.
// Run: npx tsx tools/genius-offers.ts
import { readFileSync } from 'node:fs';
import { read, emptyTally } from '../src/rules/reading';

const seeds: Array<{ id: string }> = JSON.parse(readFileSync('data/seeds.json', 'utf8'));
const shapes = ['anchor', 'turn', 'cast', 'read', 'bind', 'make'];
const seen = new Map<string, number>();
for (const s of seeds) {
  console.log(s.id);
  for (const shape of shapes) {
    const r = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood: '', shape }, current: null });
    for (const c of r.candidates) seen.set(c.form, (seen.get(c.form) ?? 0) + 1);
    console.log(`  ${shape.padEnd(7)} ${r.candidates.map((c) => `${c.name} (${c.expression}, ${c.score.toFixed(2)})`).join('  ·  ')}`);
  }
}
const forms: Array<{ id: string; name: string; expression: string; instars: { min: number } }> = JSON.parse(readFileSync('data/forms.json', 'utf8'));
const firsts = forms.filter((f) => f.instars.min === 1);
console.log(`\nFirst Forms: ${firsts.length}. Offered somewhere above: ${firsts.filter((f) => seen.has(f.id)).length}.`);
const never = firsts.filter((f) => !seen.has(f.id)).map((f) => f.name);
if (never.length) console.log(`Never among the three without blood or the bowl's chance: ${never.join(', ')}`);
