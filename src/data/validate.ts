// Schema-check every file in data/, then check that ids refer to things that exist.
import Ajv from 'ajv';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';
import { signature, compose, type Base, type Hybrids } from './tree';

export interface Problem { file: string; message: string }

/** The lines of the Tally a form of the tree may lean on, and their keys (docs/genius-tree.md). */
export const TREE_LEANS: Record<string, string[]> = {
  range: ['close', 'mid', 'far'], orders: ['guard', 'hunt', 'hold', 'free'], shape: ['anchor', 'turn', 'cast', 'read', 'bind', 'make'],
  fights: ['parries', 'blocks', 'hurts', 'dodges'], company: ['alone', 'party'], ground: ['line', 'wild', 'water', 'ruin', 'night', 'quiet'],
  pattern: ['fires', 'sworn'], bonds: ['classmate', 'shade', 'named'], quests: ['linework', 'salvage', 'hunt', 'escort', 'writ', 'deep-run'],
};
/** The bases the specification names. */
export const TREE_ROSTER = ['wolf', 'hawk', 'stag', 'tortoise', 'fox', 'imp', 'lurker', 'fiend', 'drake', 'sprite', 'homunculus', 'ember', 'fog', 'lantern', 'astrolabe', 'bell', 'blade', 'gun', 'bow', 'shield', 'gauntlet', 'coat', 'moth', 'octopus', 'carp', 'elemental'];

const read = (f: string) => JSON.parse(readFileSync(f, 'utf8'));

/** What a base file must say of the soul (docs/genius-tree.md, "The soul outside the body"). */
const SOUL_FIELDS = ['soul', 'sign', 'habit', 'of'];

/**
 * Check every file in data/. opts.basesDir: check the bases of another folder in place of
 * data/genius-bases (the tests keep small bases of their own).
 */
export function validateData(dir = 'data', opts: { basesDir?: string } = {}): Problem[] {
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
  const baseCheck = ajv.compile(read(join(dir, 'schemas', 'genius-base.schema.json')));
  const basesDir = opts.basesDir ?? join(dir, 'genius-bases');
  const baseFiles = existsSync(basesDir) ? readdirSync(basesDir).filter((f) => f.endsWith('.json')).sort() : [];
  if (problems.length) return problems;
  // A base that only lacks what it must say of the soul is still a tree: its other rules are
  // checked too. One that is not the shape of a base is left out of the checks between files.
  const broken = new Set<string>();
  for (const f of baseFiles) {
    if (baseCheck(read(join(basesDir, f)))) continue;
    const lacking: Record<string, number> = {};
    for (const e of baseCheck.errors ?? []) {
      const missing = e.keyword === 'required' ? (e.params as { missingProperty?: string }).missingProperty ?? '' : '';
      if (SOUL_FIELDS.includes(missing)) { lacking[missing] = (lacking[missing] ?? 0) + 1; continue; }
      problems.push({ file: `genius-bases/${f}`, message: `${e.instancePath || '/'} ${e.message}` });
      broken.add(f);
    }
    // said once a base, not once a form
    if (Object.keys(lacking).length) problems.push({ file: `genius-bases/${f}`, message: `it does not yet say all it must of the soul (docs/genius-tree.md): ${SOUL_FIELDS.filter((k) => lacking[k]).map((k) => (k === 'soul' ? 'no soul' : `${lacking[k]} forms without ${k}`)).join(', ')}` });
  }

  // References between files.
  const D = (n: string) => read(join(dir, `${n}.json`));
  const ids = (n: string) => new Set<string>(D(n).map((x: { id: string }) => x.id));
  const features = ids('features');
  const need = (file: string, set: Set<string>, id: string, what: string) => { if (!set.has(id)) problems.push({ file, message: `unknown ${what}: ${id}` }); };
  // The genius tree (docs/genius-tree.md): every base is a tree of thirty-one forms.
  const bases: any[] = baseFiles.filter((f) => !broken.has(f)).map((f) => ({ file: `genius-bases/${f}`, ...read(join(basesDir, f)) }));
  for (const b of bases) for (const nf of b.newFeatures ?? []) features.add(nf.id);
  const seedIds = ids('seeds');
  const bloodIds = ids('bloods');
  const SHAPES = new Set(['anchor', 'turn', 'cast', 'read', 'bind', 'make']);
  const bodyDir = join(dir, '..', 'game', 'assets', 'genius', 'bodies');
  const hasBody = (sil: string) => !existsSync(bodyDir) || existsSync(join(bodyDir, `${sil}.glb`));
  const formIds = new Set<string>();
  const formNames = new Map<string, string>();
  const signatures = new Map<string, string>();   // a path's two heaviest leans -> the path that has them
  const firsts = new Map<string, string[]>();     // a path's heaviest lean -> the paths that lean on it first
  for (const b of bases) {
    const say = (message: string) => problems.push({ file: b.file, message });
    if (b.file !== `genius-bases/${b.id}.json`) say('the file is not named for its id');
    if (!hasBody(b.silhouette) && !(b.toBuild ?? []).includes(b.silhouette)) say(`no body ${b.silhouette} in game/assets/genius/bodies (name it in toBuild if it is still to be built)`);
    for (const k of Object.keys(b.calls.seed ?? {})) if (!seedIds.has(k)) say(`calls.seed.${k} is not a Seed`);
    for (const k of Object.keys(b.calls.blood ?? {})) if (!bloodIds.has(k)) say(`calls.blood.${k} is not a blood`);
    for (const k of Object.keys(b.calls.shape ?? {})) if (!SHAPES.has(k)) say(`calls.shape.${k} is not a Shape`);
    for (const f of b.hybrid.gift) if (!features.has(f)) say(`hybrid.gift: unknown feature ${f}`);
    const leansOk = (where: string, leans: Record<string, Record<string, number>>) => {
      for (const [line, keys] of Object.entries(leans)) for (const k of Object.keys(keys)) if (!(TREE_LEANS[line] ?? []).includes(k)) say(`${where} leans on ${line}.${k}; ${line} has ${(TREE_LEANS[line] ?? []).join(', ')}`);
    };
    leansOk('nature', b.nature);
    const node = (n: any, level: number) => {
      if (!n.id.startsWith(`${b.id}-`)) say(`${n.id}: an id begins with its base's (${b.id}-)`);
      if (formIds.has(n.id)) say(`${n.id} is used twice`);
      formIds.add(n.id);
      if (formNames.has(n.name)) say(`the name ${n.name} is used twice (by ${n.id} and ${formNames.get(n.name)})`);
      formNames.set(n.name, n.id);
      for (const f of n.features) if (!features.has(f)) say(`${n.id}: feature ${f} is not in features.json nor in this base's newFeatures`);
      if (n.silhouette && !hasBody(n.silhouette)) say(`${n.id}: no body ${n.silhouette}`);
      if (level > 1) leansOk(n.id, n.leans ?? {});
      for (const c of n.prongs ?? n.finishes ?? []) node(c, level + 1);
    };
    node({ ...b.settled, prongs: b.paths }, 1);
    // Every path is unique in play: its signature is the two things it leans on most.
    const firstLines: string[] = [];
    for (const p of b.paths) {
      const { first, sig } = signature(p.leans ?? {});
      if (sig.length < 2) { say(`${p.id} leans on fewer than two things: a path's signature is its two heaviest leans`); continue; }
      const key = sig.join(' and ');
      if (signatures.has(key)) say(`${p.id} is earned by the same play as ${signatures.get(key)} (${key}): every path in the game is unique`);
      signatures.set(key, p.id);
      const same = firsts.get(first) ?? [];
      firsts.set(first, [...same, p.id]);
      if (same.length >= 3) say(`${p.id} leans first on ${first}, as ${same.join(', ')} already do: no more than three paths in the game may`);
      firstLines.push(first.split('.')[0]);
    }
    if (new Set(firstLines).size < firstLines.length) say(`two of its paths lean first on the same line of the Tally (${firstLines.join(', ')}): three paths, three different lines`);
  }
  // A hybrid's three paths are each earned by their own play too, whichever two bases make it.
  const hybridRule = D('genius-hybrids') as Hybrids;
  for (const a of bases) for (const b of bases) {
    if (a.id === b.id) continue;
    const paths = compose(a as Base, b as Base, hybridRule).filter((f) => f.level === 2);
    const sigs = paths.map((f) => signature(f.leans).sig.join(' and '));
    if (new Set(sigs).size < sigs.length) problems.push({ file: 'genius-hybrids.json', message: `${a.id}+${b.id}: two of its paths are earned by the same play (${sigs.join('; ')}); write the pair by hand or change the rule` });
  }
  // A home's lean names a home and bases; a pair written by hand names two bases.
  const baseIds = new Set<string>(bases.map((b) => b.id));
  // The three types of genius (docs/genius-types.md): every base of the game has its type
  // written, by its class, with what each of its three paths changes. (The tests' own bases
  // are given theirs by the tests.)
  if (!opts.basesDir) {
    const T = D('genius-types');
    const tsay = (message: string) => problems.push({ file: 'genius-types.json', message });
    const typeOf = (cls: string) => Object.entries<{ classes?: string[] }>(T.types).find(([k, t]) => !k.startsWith('$') && (t.classes ?? []).includes(cls))?.[0] ?? '';
    const styles = new Set(Object.keys(D('combat-room').styles));
    const moves = new Set(Object.keys(D('genius').fight.moves));
    for (const b of bases) {
      const type = typeOf(b.class);
      const paths: string[] = b.paths.map((p: { id: string }) => p.id).sort();
      const pathsOk = (where: string, named: string[]) => { if (JSON.stringify([...named].sort()) !== JSON.stringify(paths)) tsay(`${where}.paths names ${named.join(', ')}; the paths of ${b.id} are ${paths.join(', ')}`); };
      if (type === 'weapon') {
        const w = T.weapon.bases[b.id];
        if (!w) { tsay(`${b.id} is a weapon, and weapon.bases does not say what it is in the hand`); continue; }
        if (!styles.has(w.style)) tsay(`weapon.bases.${b.id}: ${w.style} is not a weapon type of combat-room.json`);
        pathsOk(`weapon.bases.${b.id}`, Object.keys(w.paths));
      } else if (type === 'defense' || type === 'ritual') {
        const it = T.items[b.id];
        if (!it) { tsay(`${b.id} is an item, and items does not say what it does`); continue; }
        if (it.type !== type) tsay(`items.${b.id} says it is a ${it.type} item; its class (${b.class}) makes it a ${type} one`);
        pathsOk(`items.${b.id}`, Object.keys(it.paths));
      } else if (type === 'companion') {
        const c = T.companions[b.id];
        if (!c) { tsay(`${b.id} is a companion, and companions does not give it a role`); continue; }
        pathsOk(`companions.${b.id}`, Object.keys(c.paths));
      } else tsay(`${b.id}: no type takes the class ${b.class}`);
    }
    for (const k of Object.keys(T.weapon.bases)) if (!baseIds.has(k)) tsay(`weapon.bases.${k}: there is no such base`);
    for (const k of Object.keys(T.items)) if (!k.startsWith('$') && !baseIds.has(k)) tsay(`items.${k}: there is no such base`);
    for (const k of Object.keys(T.companions)) if (!k.startsWith('$') && !baseIds.has(k)) tsay(`companions.${k}: there is no such base`);
    for (const [rid, r] of Object.entries<{ favours?: string[] }>(T.roles)) for (const m of r.favours ?? []) if (!moves.has(m)) tsay(`roles.${rid} favours ${m}, which is not a move of genius.json`);
  }
  const homeIds = new Set(Object.keys(D('bodies').homes));
  for (const [home, leans] of Object.entries<Record<string, number>>(D('genius-homes'))) {
    if (home.startsWith('$')) continue;
    if (!homeIds.has(home)) problems.push({ file: 'genius-homes.json', message: `${home} is not a home in bodies.json` });
    // checking another folder of bases (a test's own), a lean may name one of the game's that is not in it
    for (const [k, x] of Object.entries(leans)) {
      if (!baseIds.has(k) && !(opts.basesDir && TREE_ROSTER.includes(k))) problems.push({ file: 'genius-homes.json', message: `${home}: ${k} is not a base` });
      if (!(x > 1)) problems.push({ file: 'genius-homes.json', message: `${home}: its lean on ${k} is ${x}; a lean raises a base (above 1)` });
    }
  }
  for (const [pair, written] of Object.entries<{ nodes?: Record<string, unknown> }>(D('genius-hybrids').pairs)) {
    // checking another folder of bases (a test's own), a pair of the game's bases is not in it
    if (opts.basesDir && pair.split('+').every((k) => TREE_ROSTER.includes(k) && !baseIds.has(k))) continue;
    for (const k of pair.split('+')) if (!baseIds.has(k)) problems.push({ file: 'genius-hybrids.json', message: `${pair}: ${k} is not a base` });
    for (const [id, said] of Object.entries<{ name?: string }>((written.nodes ?? {}) as Record<string, { name?: string }>)) {
      if (!formIds.has(id) || !pair.split('+').includes(id.split('-')[0])) problems.push({ file: 'genius-hybrids.json', message: `${pair}: ${id} is not a form of either base` });
      if (said.name && formNames.has(said.name)) problems.push({ file: 'genius-hybrids.json', message: `${pair}: the name ${said.name} is already ${formNames.get(said.name)}'s` });
    }
    const names = Object.values<{ name?: string }>((written.nodes ?? {}) as Record<string, { name?: string }>).map((x) => x.name).filter(Boolean);
    if (new Set(names).size < names.length) problems.push({ file: 'genius-hybrids.json', message: `${pair}: two of its forms are given the same name` });
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
  const forms = bases.flatMap((b) => { const out: Array<{ id: string; silhouette: string }> = []; const walk = (n: any, worn: string) => { const sil = n.silhouette ?? worn; out.push({ id: n.id, silhouette: sil }); for (const c of n.prongs ?? n.finishes ?? []) walk(c, sil); }; walk({ ...b.settled, prongs: b.paths }, b.silhouette); return out; });
  // Every silhouette in the lattice can be assembled, and every slot has sockets.
  const bodies = D('genius-bodies');
  for (const f of forms) if (!bodies.silhouettes[f.silhouette] && hasBody(f.silhouette)) problems.push({ file: 'genius-bodies.json', message: `no body for silhouette ${f.silhouette} (form ${f.id})` });
  const looked = D('genius-looks').bodies;
  const coated = new Set<string>();
  for (const f of forms) {
    if (coated.has(f.silhouette) || !hasBody(f.silhouette) || !existsSync(bodyDir)) continue;
    coated.add(f.silhouette);
    if (!looked[f.silhouette]) problems.push({ file: 'genius-looks.json', message: `no coats for the body ${f.silhouette} (worn by ${f.id})` });
  }
  for (const ft of D('features')) if (ft.slot !== 'surface' && !bodies.slotSockets[ft.slot]) problems.push({ file: 'genius-bodies.json', message: `no sockets for slot ${ft.slot}` });
  for (const [sil, sp] of Object.entries(bodies.silhouettes as Record<string, { kind: string }>)) if (!bodies.kinds[sp.kind]) problems.push({ file: 'genius-bodies.json', message: `${sil}: unknown kind ${sp.kind}` });
  // What a genius may look like: every body named is a silhouette, has a palette that exists,
  // and every form's own palette exists; a keepsake's colours and an eye's ids are unique.
  const looks = D('genius-looks');
  for (const [sil, b] of Object.entries(looks.bodies as Record<string, { coats: string }>)) {
    if (!bodies.silhouettes[sil]) problems.push({ file: 'genius-looks.json', message: `bodies.${sil} is not a silhouette in genius-bodies.json` });
    if (!looks.palettes[b.coats]) problems.push({ file: 'genius-looks.json', message: `bodies.${sil}: no palette "${b.coats}"` });
  }
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
