// Schema-check every file in data/, then check that ids refer to things that exist.
import Ajv from 'ajv';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';

export interface Problem { file: string; message: string }

const read = (f: string) => JSON.parse(readFileSync(f, 'utf8'));

export function validateData(dir = 'data'): Problem[] {
  const problems: Problem[] = [];
  const ajv = new Ajv({ allErrors: true, strict: false });
  const files = readdirSync(dir).filter((f) => f.endsWith('.json'));
  for (const f of files) {
    const schemaPath = join(dir, 'schemas', `${basename(f, '.json')}.schema.json`);
    if (!existsSync(schemaPath)) { problems.push({ file: f, message: 'no schema in data/schemas/' }); continue; }
    const check = ajv.compile(read(schemaPath));
    if (!check(read(join(dir, f)))) for (const e of check.errors ?? []) problems.push({ file: f, message: `${e.instancePath || '/'} ${e.message}` });
  }
  const lifeCheck = ajv.compile(read(join(dir, 'schemas', 'life.schema.json')));
  const lives = existsSync(join(dir, 'lives')) ? readdirSync(join(dir, 'lives')).filter((f) => f.endsWith('.json')) : [];
  for (const f of lives) {
    if (!lifeCheck(read(join(dir, 'lives', f)))) for (const e of lifeCheck.errors ?? []) problems.push({ file: `lives/${f}`, message: `${e.instancePath || '/'} ${e.message}` });
  }
  if (problems.length) return problems;

  // References between files.
  const D = (n: string) => read(join(dir, `${n}.json`));
  const ids = (n: string) => new Set<string>(D(n).map((x: { id: string }) => x.id));
  const features = ids('features');
  const need = (file: string, set: Set<string>, id: string, what: string) => { if (!set.has(id)) problems.push({ file, message: `unknown ${what}: ${id}` }); };
  for (const f of D('forms')) {
    for (const x of f.features) need('forms.json', features, x, `feature on ${f.id}`);
    if (f.instars.min > f.instars.max) problems.push({ file: 'forms.json', message: `${f.id}: instars.min > max` });
  }
  for (const s of D('seeds')) need('seeds.json', features, s.seedMark, `seed-mark of ${s.id}`);
  for (const a of D('adaptations')) need('adaptations.json', features, a.id, 'adaptation feature');
  for (const s of D('shades')) need('shades.json', features, s.graftFeature, `graft of ${s.id}`);
  for (const b of D('bloods')) if (b.graft) need('bloods.json', features, b.graft, `graft of ${b.id}`);
  const disciplines = ids('disciplines');
  for (const a of D('archetypes')) need('archetypes.json', disciplines, a.discipline, `discipline of ${a.id}`);
  const reading = D('reading');
  for (const [line, keys] of Object.entries(reading.leans as Record<string, Record<string, { features: Record<string, number> }>>)) {
    for (const [key, lean] of Object.entries(keys)) for (const f of Object.keys(lean.features)) need('reading.json', features, f, `feature in leans.${line}.${key}`);
  }
  const tags = new Set<string>(D('terms').flatMap((t: { tags: string[] }) => t.tags));
  for (const t of tags) if (!reading.leans.intention[`tag:${t}`]) problems.push({ file: 'reading.json', message: `Term tag "${t}" has no lean in leans.intention (add "tag:${t}")` });
  // Every instar must have at least three forms to offer.
  const forms = D('forms');
  for (let n = 1; n <= 6; n++) {
    const count = forms.filter((f: { instars: { min: number; max: number } }) => f.instars.min <= n && n <= f.instars.max).length;
    if (count < 4) problems.push({ file: 'forms.json', message: `only ${count} forms for instar ${n}; a Reading needs three besides the current form` });
  }
  const archetypes = ids('archetypes');
  const shades = ids('shades');
  const terms = ids('terms');
  for (const f of lives) {
    const L = read(join(dir, 'lives', f));
    const file = `lives/${f}`;
    need(file, ids('bloods'), L.blood, 'blood');
    need(file, ids('seeds'), L.seed, 'seed');
    need(file, archetypes, L.archetype, 'archetype');
    for (const e of L.events) {
      if (e.archetype) need(file, archetypes, e.archetype, 'archetype');
      if (e.shade) need(file, shades, e.shade, 'shade');
      for (const t of e.terms ?? []) need(file, terms, t, 'Term');
    }
    for (const p of L.phases) for (const q of p.quests ?? []) if (q.archetype !== 'none') need(file, archetypes, q.archetype, 'archetype');
  }
  return problems;
}
