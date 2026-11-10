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
  // Every home with a body has a palette of tones the creator knows, and every city answer a home.
  const tones = new Set(Object.keys(D('creation').look.skinTones));
  for (const [hid, h] of Object.entries<any>(D('bodies').homes)) for (const t of h.palette) need('bodies.json', tones, t, `tone of ${hid}`);
  // Every detail of a home's form names a MakeHuman target the kit has, and the ancestry sums to one.
  const targetDir = join(dir, '..', 'tools', 'blender', 'makehuman', 'targets');
  if (existsSync(targetDir)) {
    const stems = new Set<string>();
    const walk = (d: string) => { for (const e of readdirSync(d, { withFileTypes: true })) { if (e.isDirectory()) walk(join(d, e.name)); else if (e.name.endsWith('.target.gz')) stems.add(e.name.slice(0, -'.target.gz'.length)); } };
    walk(targetDir);
    const ends = ['decr', 'incr', 'down', 'up', 'in', 'out', 'backward', 'forward', 'concave', 'convex', 'compress', 'uncompress'];
    const known = (k: string) => [k, `l-${k}`].some((n) => stems.has(n) || ends.some((e) => stems.has(`${n}-${e}`)));
    for (const [hid, h] of Object.entries<any>(D('bodies').homes)) {
      const sum = Object.values<number>(h.form.ancestry).reduce((a, b) => a + b, 0);
      if (Math.abs(sum - 1) > 0.02) problems.push({ file: 'bodies.json', message: `${hid}: the ancestry sums to ${sum.toFixed(2)}, not 1` });
      for (const part of ['details', 'm', 'f']) for (const k of Object.keys(h.form[part] ?? {})) if (!known(k)) problems.push({ file: 'bodies.json', message: `${hid}: no MakeHuman target for the detail ${k}` });
    }
  }
  const homes = new Set(Object.keys(D('bodies').homes));
  for (const an of D('creation').questions[0].answers) if (an.city) need('creation.json', homes, an.city, 'home body');
  // Every mark a blood shows is a feature the body can take.
  const peopleFeatures = new Set(Object.keys(D('people-features').features));
  for (const b of D('bloods')) for (const m of b.marks ?? []) need('bloods.json', peopleFeatures, m, `mark of ${b.id}`);
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
  // Every silhouette in the lattice can be assembled, and every slot has sockets.
  const bodies = D('genius-bodies');
  for (const f of forms) if (!bodies.silhouettes[f.silhouette]) problems.push({ file: 'genius-bodies.json', message: `no body for silhouette ${f.silhouette} (form ${f.id})` });
  for (const ft of D('features')) if (ft.slot !== 'surface' && !bodies.slotSockets[ft.slot]) problems.push({ file: 'genius-bodies.json', message: `no sockets for slot ${ft.slot}` });
  for (const [sil, sp] of Object.entries(bodies.silhouettes as Record<string, { kind: string }>)) if (!bodies.kinds[sp.kind]) problems.push({ file: 'genius-bodies.json', message: `${sil}: unknown kind ${sp.kind}` });
  // What a genius may look like: every body named is a silhouette, has a palette that exists,
  // and every form's own palette exists; a keepsake's colours and an eye's ids are unique.
  const looks = D('genius-looks');
  for (const [sil, b] of Object.entries(looks.bodies as Record<string, { coats: string }>)) {
    if (!bodies.silhouettes[sil]) problems.push({ file: 'genius-looks.json', message: `bodies.${sil} is not a silhouette in genius-bodies.json` });
    if (!looks.palettes[b.coats]) problems.push({ file: 'genius-looks.json', message: `bodies.${sil}: no palette "${b.coats}"` });
  }
  const formIds = new Set<string>(forms.map((f: { id: string }) => f.id));
  for (const [fid, f] of Object.entries(looks.forms as Record<string, { coats: string }>)) {
    need('genius-looks.json', formIds, fid, 'form with its own coats');
    if (!looks.palettes[f.coats]) problems.push({ file: 'genius-looks.json', message: `forms.${fid}: no palette "${f.coats}"` });
  }
  for (const [pid, coats] of Object.entries(looks.palettes as Record<string, Array<{ id: string }>>)) {
    if (new Set(coats.map((c) => c.id)).size !== coats.length) problems.push({ file: 'genius-looks.json', message: `palettes.${pid}: two coats share an id` });
    if (coats.length < looks.born.coatsOffered) problems.push({ file: 'genius-looks.json', message: `palettes.${pid}: fewer coats than are offered (${looks.born.coatsOffered})` });
  }
  // Zones: their beasts exist, their doors lead somewhere, their libraries are not empty; the
  // Academy's lessons travel to places that exist, of the Academy or of a zone.
  const beasts = ids('beasts');
  const zones = D('zones');
  const zoneAreas = new Set<string>();
  for (const z of zones) {
    need('zones.json', beasts, z.beasts.common, `common beast of ${z.id}`);
    need('zones.json', beasts, z.beasts.elite, `elite beast of ${z.id}`);
    for (const n of z.beasts.named ?? []) need('zones.json', beasts, n.beast, `named beast ${n.id} of ${z.id}`);
    const areaIds = new Set<string>(z.areas.map((a: { id: string }) => a.id));
    for (const a of z.areas) {
      zoneAreas.add(`${z.id}/${a.id}`);
      for (const d of a.doors) if (d.to !== 'extraction' && !areaIds.has(d.to)) problems.push({ file: 'zones.json', message: `${z.id}/${a.id}: door to unknown area ${d.to}` });
      if (a.beast && !['common', 'elite'].includes(a.beast)) need('zones.json', beasts, a.beast, `beast of ${z.id}/${a.id}`);
      if (a.pack && a.pack.min > a.pack.max) problems.push({ file: 'zones.json', message: `${z.id}/${a.id}: pack.min > max` });
    }
    for (const k of ['floor', 'edge'] as const) if (!z.tiles[k].length) problems.push({ file: 'zones.json', message: `${z.id}: no ${k} tiles` });
  }
  // Weapons: every weapon names a type the room knows, every discipline's weapons exist, every
  // instructor's and every creation answer's style keys exist.
  const styleIds = new Set<string>(Object.keys(D('combat-room').styles).filter((k) => !k.startsWith('$')));
  const weaponIds = ids('weapons');
  for (const w of D('weapons')) {
    if (!styleIds.has(w.style)) problems.push({ file: 'weapons.json', message: `${w.id}: unknown weapon type ${w.style}` });
    if (!D('disciplines').some((d: { city: string }) => d.city === w.city)) problems.push({ file: 'weapons.json', message: `${w.id}: no discipline for city ${w.city}` });
  }
  for (const d of D('disciplines')) for (const w of d.weapons) need('disciplines.json', weaponIds, w, `weapon of ${d.id}`);
  for (const [sh, kit] of Object.entries(D('shape-kits') as Record<string, { styles?: Record<string, number> }>)) if (kit.styles) for (const st of Object.keys(kit.styles)) if (!styleIds.has(st)) problems.push({ file: 'shape-kits.json', message: `${sh}: unknown weapon type ${st} in styles` });
  for (const q of D('creation').questions) for (const an of q.answers) for (const st of Object.keys(an.style ?? {})) if (!styleIds.has(st)) problems.push({ file: 'creation.json', message: `${q.id}: unknown weapon type ${st}` });
  // Every creation answer carries a title and an emblem the game can draw.
  const emblems = new Set(Object.keys(D('emblems').emblems));
  for (const q of D('creation').questions) for (const an of q.answers) {
    if (!an.title) problems.push({ file: 'creation.json', message: `${q.id}: an answer without a title` });
    if (!emblems.has(an.emblem)) problems.push({ file: 'creation.json', message: `${q.id}: unknown emblem ${an.emblem}` });
  }
  for (const ins of D('academy').instructors) if (ins.weapon) need('academy.json', weaponIds, ins.weapon, `weapon of instructor ${ins.id}`);
  for (const st of styleIds) if (!D('academy').cohort.fighting.weapons[st]) problems.push({ file: 'academy.json', message: `cohort.fighting.weapons has no entry for ${st}` });
  // Every Discipline has a kit of nine techniques whose effects the fight knows, with the keys each reads.
  const effectKeys: Record<string, string[]> = { heavy: ['damage', 'reach', 'arc'], burst: ['damage', 'reach', 'arc', 'burnSeconds'], dash: ['damage', 'reach', 'arc', 'dash'],
    tether: ['damage', 'range', 'slowSeconds', 'slow'], ward: ['wardSeconds', 'damage', 'reach', 'arc'], volley: ['damage', 'range'], mark: ['range', 'markSeconds', 'markFactor'],
    finisher: ['damage', 'range'], sound: ['range', 'slowSeconds', 'slow'], pull: ['damage', 'range', 'pullTo'], quake: ['damage', 'reach', 'arc'], 'bolt-crit': ['damage', 'range', 'critSeconds'] };
  const kitsAll = D('discipline-kits');
  for (const d of D('disciplines')) {
    const kit = kitsAll[d.id];
    if (!kit || typeof kit !== 'object') { problems.push({ file: 'discipline-kits.json', message: `no kit for ${d.id}` }); continue; }
    if (kit.techniques.length !== 9) problems.push({ file: 'discipline-kits.json', message: `${d.id}: ${kit.techniques.length} techniques, not nine` });
    const tids = new Set<string>(kit.techniques.map((t: { id: string }) => t.id));
    for (const t of d.techniques) if (!tids.has(t)) problems.push({ file: 'disciplines.json', message: `${d.id}: taught technique ${t} is not in its kit` });
    for (const t of kit.techniques) {
      if (!effectKeys[t.effect]) problems.push({ file: 'discipline-kits.json', message: `${d.id}: ${t.id} has an effect the fight does not know (${t.effect})` });
      else for (const key of effectKeys[t.effect]) if (t[key] === undefined) problems.push({ file: 'discipline-kits.json', message: `${d.id}: ${t.id} (${t.effect}) lacks ${key}` });
    }
    if (!D('academy').instructors.some((i: { discipline?: string }) => i.discipline === d.id)) problems.push({ file: 'academy.json', message: `no instructor teaches ${d.id}` });
  }
  const gear = D('gear');
  for (const [z, n] of Object.entries(gear.named as Record<string, { trait: string }>)) {
    if (!gear.traits[n.trait]) problems.push({ file: 'gear.json', message: `named weapon of ${z}: unknown trait ${n.trait}` });
    if (!zones.some((zz: { id: string }) => zz.id === z)) problems.push({ file: 'gear.json', message: `named weapon for unknown zone ${z}` });
  }
  if (!gear.traits[gear.archive.trait]) problems.push({ file: 'gear.json', message: `the Archive's weapon has an unknown trait` });
  need('gear.json', weaponIds, gear.smith.weapon, 'the smith\'s weapon');
  for (const z of zones) if (!gear.named[z.id]) problems.push({ file: 'gear.json', message: `no named weapon for the zone ${z.id}` });
  const questTypes = new Set<string>(Object.keys(D('quests').types));
  for (const c of D('crises')) {
    for (const [k, l] of Object.entries(c.ledgers as Record<string, { serves: string[] }>)) for (const t of l.serves) if (!questTypes.has(t)) problems.push({ file: 'crises.json', message: `${c.id}: ledger ${k} served by unknown quest type ${t}` });
    if (!c.ledgers[c.default]) problems.push({ file: 'crises.json', message: `${c.id}: default ending ${c.default} is not a ledger` });
    for (const k of Object.keys(c.ledgers)) if (!c.endings[k]) problems.push({ file: 'crises.json', message: `${c.id}: ledger ${k} has no ending` });
    for (const q of c.crisisQuests) {
      if (!questTypes.has(q.type)) problems.push({ file: 'crises.json', message: `${c.id}: crisis quest of unknown type ${q.type}` });
      if (!zones.some((z: { id: string }) => z.id === q.zone)) problems.push({ file: 'crises.json', message: `${c.id}: crisis quest in unknown zone ${q.zone}` });
      if (!c.ledgers[q.ledger]) problems.push({ file: 'crises.json', message: `${c.id}: crisis quest serves unknown ledger ${q.ledger}` });
    }
  }
  const academy = D('academy');
  const placeKnown = (p: string) => Boolean(academy.places[p]) || zoneAreas.has(p);
  for (const l of academy.lessons) {
    if (!placeKnown(l.place)) problems.push({ file: 'academy.json', message: `lesson ${l.id}: unknown place ${l.place}` });
    for (const st of l.steps) {
      if (st.place && !placeKnown(st.place)) problems.push({ file: 'academy.json', message: `lesson ${l.id}, ${st.title}: unknown place ${st.place}` });
      if (st.goal?.to && !placeKnown(st.goal.to)) problems.push({ file: 'academy.json', message: `lesson ${l.id}, ${st.title}: travels to unknown place ${st.goal.to}` });
      if (st.goal?.place && !placeKnown(st.goal.place)) problems.push({ file: 'academy.json', message: `lesson ${l.id}, ${st.title}: unknown goal place ${st.goal.place}` });
    }
  }
  for (const [pid, p] of Object.entries(academy.places as Record<string, { doors: { to: string }[] }>)) {
    // A door that never opens (locked, no opensWhen) may lead to a place that is only a name.
    for (const d of p.doors as { to: string; locked?: string; opensWhen?: string }[]) if (d.to !== 'extraction' && !(d.locked && !d.opensWhen) && !placeKnown(d.to)) problems.push({ file: 'academy.json', message: `${pid}: door to unknown place ${d.to}` });
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
