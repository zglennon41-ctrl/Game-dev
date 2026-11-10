// Print a tree of the genius tree (docs/genius-tree.md), to read what the data and the rule
// make: a base's own, or the hybrid the rule composes from two.
// Run: npx tsx tools/genius-tree.ts wolf            the wolf's thirty-one forms
//      npx tsx tools/genius-tree.ts wolf blade      the Edged Wolf: the hybrid of wolf, then blade
//      npx tsx tools/genius-tree.ts --turnings      which play turns which base, and how often
import { data, baseOf, hybridForms, type Form, type Leans } from '../src/data';
import { hybridName, signature } from '../src/data/tree';
import { read, emptyTally, type Tally, type GeniusForm } from '../src/rules/reading';

const words = (data.reading.words ?? {}) as Record<string, Record<string, string>>;
const say = (leans: Leans, most = 4) => Object.entries(leans).flatMap(([line, keys]) => Object.entries(keys).map(([k, w]) => ({ w, t: `${words[line]?.[k] ?? `${line}.${k}`} ${w}` })))
  .sort((a, b) => b.w - a.w).slice(0, most).map((x) => x.t).join(', ');
const label = (id: string) => data.features.find((f) => f.id === id)?.label ?? id;

function print(forms: Form[]) {
  for (const f of forms) {
    const pad = '  '.repeat(f.level - 1);
    console.log(`${pad}${['', 'SETTLED', 'PATH', 'prong', 'finish'][f.level]}  ${f.name}   [${f.id}]`);
    if (f.of) console.log(`${pad}    the picture of: ${f.of}`);
    if (f.level >= 2) console.log(`${pad}    comes of: ${say(f.leans)}${f.level === 2 ? `   (signature: ${signature(f.leans).sig.join(' + ')})` : ''}`);
    console.log(`${pad}    adds: ${f.own.map(label).join(', ')}`);
    if (f.sign) console.log(`${pad}    sign: ${f.sign}`);
    if (f.habit) console.log(`${pad}    habit: ${f.habit}`);
  }
}

/** Play made of exactly what some leans lean on, in their own proportions. */
export function playOf(leans: Leans, n = 40): Tally {
  const t = emptyTally();
  for (const [line, keys] of Object.entries(leans)) for (const [k, w] of Object.entries(keys)) {
    const c = Math.max(1, Math.round(w * n));
    if (line === 'range') t.range[k] = c;
    else if (line === 'orders') t.orders[k] = c;
    else if (line === 'shape') t.families[`${k}.x`] = c;
    else if (line === 'fights') t.counters[`fights.${k}`] = c;
    else if (line === 'company') t.counters[`runs.${k}`] = c;
    else if (line === 'ground') t.ground[k] = c;
    else if (line === 'quests') t.counters[`runs.quest.${k}`] = c;
    else if (line === 'bonds') t.bonds[k] = 1;
    else if (line === 'pattern') t.intention = { form: 'x.y', terms: [], fires: k === 'fires' ? 1000 : (t.intention?.fires ?? 0), sworn: k === 'sworn' ? true : t.intention?.sworn };
  }
  return t;
}

const args = process.argv.slice(2);
if (args[0] === '--turnings') {
  // Every base, settled, then played purely as each base's nature until the first refinement.
  const origin = { seed: data.seeds[0].id, blood: '', shape: 'anchor' };
  const settled = (id: string): GeniusForm => { const b = baseOf(id)!; return { form: b.settled.id, base: id, expression: b.expression, own: b.settled.features, heritage: [], seedMark: '', grafts: [], adaptations: [] }; };
  let own = 0, toward = 0, elsewhere = 0, none = 0;
  const odd: string[] = [];
  for (const a of data.bases) for (const b of data.bases) {
    const t = read({ instar: 2, tally: playOf(b.nature), origin, current: settled(a.id) }).turning;
    if (a.id === b.id) { if (t) { own++; odd.push(`${a.name} played as itself turns toward ${t.second}`); } continue; }
    if (!t) { none++; odd.push(`${a.name} played as ${b.name}: no turning`); } else if (t.second === b.id) toward++; else { elsewhere++; odd.push(`${a.name} played as ${b.name} turns toward ${t.second} (${t.other} against ${t.own})`); }
  }
  const pairs = data.bases.length * (data.bases.length - 1);
  console.log(`THE TURNING (least fit ${data.hybrids.rule.min}, margin ${data.hybrids.rule.margin}): ${pairs} ordered pairs`);
  console.log(`played purely as another base's nature: a turning toward that base in ${toward}, toward a third base in ${elsewhere}, none in ${none}`);
  console.log(`played as its own nature: a turning in ${own} of ${data.bases.length}`);
  for (const o of odd.slice(0, 30)) console.log(`  ${o}`);
} else if (args.length === 2) {
  const [a, b] = args.map((id) => baseOf(id));
  if (!a || !b) throw new Error(`no such base: ${args.join(', ')}`);
  console.log(`${hybridName(a, b, data.hybrids).toUpperCase()}  [${a.id}+${b.id}]  the body of the ${a.name} (${a.silhouette}), wearing ${b.hybrid.gift.map(label).join(' and ')}, in a coat of the ${b.name}'s`);
  console.log(`under ${a.settled.name} [${a.settled.id}]${data.hybrids.pairs[`${a.id}+${b.id}`] ? '   (a pair with words written by hand)' : ''}`);
  print(hybridForms(a.id, b.id));
} else if (args.length === 1) {
  const b = baseOf(args[0]);
  if (!b) throw new Error(`no such base: ${args[0]}`);
  console.log(`${b.name.toUpperCase()}  [${b.id}]  ${b.class}, ${b.expression}, ${b.silhouette}`);
  if (b.soul) console.log(`whose soul: ${b.soul}`);
  console.log(`its nature: ${say(b.nature)}`);
  print(data.forms.filter((f) => f.base === b.id));
} else {
  console.log(`bases: ${data.bases.map((b) => b.id).join(', ')}\nusage: npx tsx tools/genius-tree.ts <base> [<second base>] | --turnings`);
}
