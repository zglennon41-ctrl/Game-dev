// Write reference Readings from the tools' rules, for the game's own copy of them to match.
// Run: npx tsx tools/genius-fixtures.ts  (writes game/tests/fixtures/readings.json)
import { writeFileSync } from 'node:fs';
import { read, take, emptyTally, type Tally, type GeniusForm } from '../src/rules/reading';
import { resonance, payingTier, verses, shadowCap, geniusWill, tierFor } from '../src/rules/resonance';

const cases: Array<{ name: string; instar: number; origin: { seed: string; blood: string; shape: string; home?: string }; tally: Tally; current: GeniusForm | null }> = [];

const first = (seed: string, blood: string, shape: string) => ({ name: `first ${seed} ${blood} ${shape}`, instar: 1, origin: { seed, blood, shape }, tally: emptyTally(), current: null });
cases.push(first('watches-from-above', 'aerie-born', 'cast'));
cases.push(first('stands-between', 'ridgefolk', 'anchor'));
cases.push(first('owes-me', 'demon-blooded', 'bind'));
cases.push(first('that-burns', 'fogborn', 'turn'));
cases.push(first('remembers', 'eyes-heat', 'read'));
cases.push(first('never-alive', 'forgeborn', 'make'));
// A home leans the bowl's second and third offers toward its own kinds.
const atHome = (seed: string, blood: string, shape: string, home: string) => ({ name: `first ${seed} ${blood} ${shape} of ${home}`, instar: 1, origin: { seed, blood, shape, home }, tally: emptyTally(), current: null });
cases.push(atHome('watches-from-above', 'long-stride', 'cast', 'columbia'));
cases.push(atHome('never-alive', 'forgeborn', 'make', 'colonia'));
cases.push(atHome('remembers', 'eyes-heat', 'read', 'jiangnan'));
cases.push(atHome('i-can-hold', '', 'cast', 'edo'));
cases.push(atHome('stands-between', 'ridgefolk', 'anchor', 'alexandria'));

// The Guide's worked example: a hawk, fighting close with a saber, Hold and Guard orders.
const hawkFirst = read({ instar: 1, tally: emptyTally(), origin: { seed: 'watches-from-above', blood: 'aerie-born', shape: 'cast' }, current: null });
const hawk = take(null, hawkFirst.candidates.find((c) => c.form === 'hawk') ?? hawkFirst.candidates[0]);
const close: Tally = { ...emptyTally(), families: { 'cast.reach': 14, 'anchor.wall': 6 }, range: { close: 30, mid: 6 }, orders: { hold: 12, guard: 9 }, company: { anchor: 6, read: 4 }, ground: { tunnel: 8, ruin: 3 }, discipline: { marshal: 10 } };
cases.push({ name: 'gate: the hawk that fights close', instar: 2, origin: { seed: 'watches-from-above', blood: 'aerie-born', shape: 'cast' }, tally: close, current: hawk });
const pattern: Tally = { ...emptyTally(), families: { 'bind.contract': 20 }, range: { mid: 12, far: 8 }, orders: { hunt: 20 }, intention: { form: 'bind.contract', terms: ['struck-first', 'below-half'], fires: 60 }, bonds: { shade: 1 } };
cases.push({ name: 'third: a contract Pattern', instar: 3, origin: { seed: 'owes-me', blood: 'demon-blooded', shape: 'bind' }, tally: pattern, current: hawk });

const out = {
  readings: cases.map((c) => ({ ...c, result: read({ instar: c.instar, tally: c.tally, origin: c.origin, current: c.current }) })),
  resonance: [[1, 0], [1, 2], [2, 1], [3, 3], [5, 5], [6, 1]].map(([i, t]) => ({ instar: i, tier: t, resonance: resonance(i, t), paying: payingTier(resonance(i, t), t), verses: verses(payingTier(resonance(i, t), t)), shadowCap: shadowCap(resonance(i, t)), will: geniusWill(resonance(i, t)) })),
  tiers: [0, 49, 50, 150, 400].map((uses) => ({ uses, tier: tierFor({ uses, built: true, sworn: false, masterInArchetype: false, stage4Days: 0 }) })),
};
writeFileSync('game/tests/fixtures/readings.json', JSON.stringify(out, null, 1));
console.log(`wrote ${out.readings.length} readings`);
