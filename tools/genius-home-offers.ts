// How often the rite's bowl offers a character a kind of their own home (data/forms.json, home;
// data/reading.json, home): for every home, every Seed and every Shape, with no blood and no
// chance. A designer's check that the home leans the bowl without owning it.
// Run: npx tsx tools/genius-home-offers.ts
import { readFileSync } from 'node:fs';
import { read, emptyTally } from '../src/rules/reading';

const seeds: Array<{ id: string }> = JSON.parse(readFileSync('data/seeds.json', 'utf8'));
const forms: Array<{ id: string; name: string; home?: string; instars: { min: number } }> = JSON.parse(readFileSync('data/forms.json', 'utf8'));
const homes: string[] = Object.keys(JSON.parse(readFileSync('data/bodies.json', 'utf8')).homes);
const shapes = ['anchor', 'turn', 'cast', 'read', 'bind', 'make'];
const homeOf = new Map(forms.map((f) => [f.id, f.home ?? '']));
let all = 0, withHome = 0, first = 0, away = 0, three = 0;
for (const home of homes) {
  let n = 0, got = 0;
  const seen = new Map<string, number>();
  for (const s of seeds) for (const shape of shapes) {
    const r = read({ instar: 1, tally: emptyTally(), origin: { seed: s.id, blood: '', shape, home }, current: null });
    const own = r.candidates.filter((c) => homeOf.get(c.form) === home);
    n++; all++;
    if (own.length) { got++; withHome++; }
    if (own.length >= 3) three++;
    if (homeOf.get(r.candidates[0].form) === home) first++;
    for (const c of r.candidates) {
      const h = homeOf.get(c.form);
      if (h && h !== home && h !== 'alexandria') away++;
      if (h === home) seen.set(c.name, (seen.get(c.name) ?? 0) + 1);
    }
  }
  console.log(`${home.padEnd(11)} a kind of home among the three in ${got} of ${n}  (${[...seen].map(([k, v]) => `${k} ${v}`).join(', ') || 'none'})`);
}
console.log(`\nAll homes: ${withHome} of ${all} bowls (${Math.round((100 * withHome) / all)}%) offer a kind of the character's home; it is the best fit in ${first}; another home's kind is offered ${away} times; all three are of home in ${three}.`);
