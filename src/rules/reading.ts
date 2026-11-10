// The Reading: score the lattice against the Tally, offer three candidates with heritage.
import { data, byId, type Expression, type Form, type Lean, type ReadingConfig } from '../data';
import { intentionKeys } from './terms';

/** The record of play since the last Reading. Counts, not shares. */
export interface Tally {
  families: Record<string, number>;
  range: Record<string, number>;
  orders: Record<string, number>;
  company: Record<string, number>;
  ground: Record<string, number>;
  discipline: Record<string, number>;
  bonds: Record<string, number>;
  intention: { form: string; terms: string[]; fires: number } | null;
  runsWith: Record<string, number>;
  /** Raw counters for adaptations ("fights.range.close", "runs.night", ...). */
  counters: Record<string, number>;
}

export function emptyTally(): Tally {
  return { families: {}, range: {}, orders: {}, company: {}, ground: {}, discipline: {}, bonds: {}, intention: null, runsWith: {}, counters: {} };
}

/** Who the genius belongs to: fixed facts that are read alongside play. */
export interface Origin { seed: string; blood: string; shape: string; /** Where the character grew up (a home of data/bodies.json). */ home?: string }

export interface GeniusForm {
  form: string;
  expression: Expression;
  /** The form's own parts. */
  own: string[];
  /** Parts carried from earlier forms. */
  heritage: string[];
  seedMark: string;
  grafts: Array<{ id: string; feature: string; source: string }>;
  adaptations: Array<{ id: string; lastFed: number }>;
}

export function featuresOf(g: GeniusForm): string[] {
  return unique([g.seedMark, ...g.own, ...g.heritage, ...g.grafts.map((x) => x.feature), ...g.adaptations.map((a) => a.id)]);
}

export interface Reason { line: string; key: string; share: number; contribution: number }

export interface Candidate {
  form: string;
  name: string;
  expression: Expression;
  silhouette: string;
  score: number;
  own: string[];
  heritage: string[];
  seedMark: string;
  features: string[];
  reasons: Reason[];
}

export interface ReadingResult {
  instar: number;
  crossingAllowed: boolean;
  lineLeads: Array<{ line: string; expression: Expression; weight: number }>;
  candidates: Candidate[];
}

type Lines = Record<string, Record<string, number>>;

/** Turn a Tally into per-line shares and per-line emphasis. */
export function linesOf(t: Tally, origin: Origin, cfg: ReadingConfig = data.reading): { shares: Lines; emphasis: Record<string, number> } {
  const shares: Lines = {};
  const emphasis: Record<string, number> = {};
  for (const line of ['families', 'range', 'orders', 'company', 'ground', 'discipline'] as const) {
    const counts = t[line];
    const total = sum(Object.values(counts));
    shares[line] = total > 0 ? mapValues(counts, (v) => v / total) : {};
    emphasis[line] = Math.min(1, total / (cfg.emphasis.reference[line] ?? 1));
  }
  // Bonds are presence, not share.
  shares.bonds = mapValues(t.bonds, (v) => (v > 0 ? 1 : 0));
  emphasis.bonds = Object.values(t.bonds).some((v) => v > 0) ? 1 : 0;
  if (t.intention) {
    shares.intention = intentionKeys(t.intention);
    emphasis.intention = cfg.emphasis.intentionBase + (1 - cfg.emphasis.intentionBase) * Math.min(1, t.intention.fires / cfg.emphasis.intentionFires);
  } else {
    shares.intention = {};
    emphasis.intention = 0;
  }
  shares.seed = { [origin.seed]: 1 };
  shares.blood = { [origin.blood]: 1 };
  shares.shape = { [origin.shape]: 1 };
  emphasis.seed = emphasis.blood = emphasis.shape = 1;
  return { shares, emphasis };
}

function leanFor(cfg: ReadingConfig, line: string, key: string): Lean | undefined {
  return cfg.leans[line]?.[key];
}

/** How much one key of one line points at a form: lean toward its Expression plus toward each of its parts. */
function keyFit(lean: Lean | undefined, expression: Expression, features: string[]): number {
  if (!lean) return 0;
  let v = lean.expression[expression] ?? 0;
  for (const f of features) v += lean.features[f] ?? 0;
  return v;
}

function scoreForm(form: Pick<Form, 'expression' | 'features'>, shares: Lines, emphasis: Record<string, number>, weights: Record<string, number>, cfg: ReadingConfig): { score: number; reasons: Reason[] } {
  let score = 0;
  const reasons: Reason[] = [];
  for (const [line, w] of Object.entries(weights)) {
    const e = emphasis[line] ?? 0;
    if (!w || !e) continue;
    for (const [key, share] of Object.entries(shares[line] ?? {})) {
      const c = w * e * share * keyFit(leanFor(cfg, line, key), form.expression, form.features);
      if (c > 0) {
        score += c;
        reasons.push({ line, key, share, contribution: c });
      }
    }
  }
  reasons.sort((a, b) => b.contribution - a.contribution);
  return { score, reasons: reasons.slice(0, 3) };
}

/** Score a single feature (used to choose heritage): how much the Tally wants this part. */
function scoreFeature(feature: string, shares: Lines, emphasis: Record<string, number>, weights: Record<string, number>, cfg: ReadingConfig): number {
  let s = 0;
  for (const [line, w] of Object.entries(weights)) {
    const e = emphasis[line] ?? 0;
    for (const [key, share] of Object.entries(shares[line] ?? {})) s += w * e * share * (leanFor(cfg, line, key)?.features[feature] ?? 0);
  }
  return s;
}

const EXPRESSIONS: Expression[] = ['beast', 'kith', 'engine', 'relic', 'daemon', 'aspect'];

/** For each line, which Expression it points at most, and how hard. */
function lineLeads(shares: Lines, emphasis: Record<string, number>, weights: Record<string, number>, cfg: ReadingConfig) {
  const out: Array<{ line: string; expression: Expression; weight: number }> = [];
  for (const [line, w] of Object.entries(weights)) {
    const e = emphasis[line] ?? 0;
    if (!w || !e) continue;
    let best: Expression | null = null;
    let bestV = 0;
    for (const x of EXPRESSIONS) {
      let v = 0;
      for (const [key, share] of Object.entries(shares[line] ?? {})) v += share * (leanFor(cfg, line, key)?.expression[x] ?? 0);
      if (v > bestV) { bestV = v; best = x; }
    }
    if (best) out.push({ line, expression: best, weight: w * e * bestV });
  }
  return out.sort((a, b) => b.weight - a.weight);
}

export interface ReadingInput {
  instar: number;
  tally: Tally;
  origin: Origin;
  current: GeniusForm | null;
  lattice?: Form[];
  cfg?: ReadingConfig;
  rules?: typeof data.rules;
}

/**
 * Score every eligible form in the lattice and offer three. The First Form reads only the
 * Seed, the blood and the Shape. Every candidate carries the Seed-mark; later candidates
 * carry one to three heritage parts chosen from the old form's parts and adaptations.
 */
export function read(input: ReadingInput): ReadingResult {
  const cfg = input.cfg ?? data.reading;
  const rules = input.rules ?? data.rules;
  const lattice = input.lattice ?? data.forms;
  const first = input.instar === 1 || !input.current;
  const weights = first ? cfg.firstFormWeights : cfg.weights;
  const { shares, emphasis } = linesOf(input.tally, input.origin, cfg);
  const leads = lineLeads(shares, emphasis, weights, cfg);
  const seedMark = byId(data.seeds, input.origin.seed, 'Seed').seedMark;

  const current = input.current;
  const top = leads.slice(0, 3);
  const crossingAllowed = !current || top.filter((l) => l.expression !== current.expression).length >= cfg.crossing.linesAway;

  // A home's kinds come only at the rite (after it they are kept, by keeping its kind). There,
  // a kind of another home counts for less everywhere; a kind of the character's own home
  // counts for more, but only for the second and third offers: the best fit is the field's.
  const hcfg = cfg.home;
  const home = input.origin.home ?? '';
  const ownHome = (f: Form) => first && !!f.home && f.home === home;
  const scored = lattice
    .filter((f) => f.instars.min <= input.instar && input.instar <= f.instars.max && f.id !== current?.form)
    .filter((f) => first || !f.home)
    .map((f) => {
      const s = scoreForm(f, shares, emphasis, weights, cfg);
      const stay = current && !crossingAllowed && f.expression === current.expression ? 1 + cfg.crossing.stayBonus : 1;
      const away = first && f.home && f.home !== home && !hcfg.open.includes(f.home) ? hcfg.away : 1;
      const score = s.score * stay * away;
      return { f, score, lean: ownHome(f) ? score * (1 + hcfg.bonus) + hcfg.floor : score, reasons: s.reasons };
    })
    .sort((a, b) => b.score - a.score || a.f.id.localeCompare(b.f.id));

  // Greedy pick of three, discounting repeats of an Expression so three bodies are offered.
  const picked: typeof scored = [];
  const pool = [...scored];
  while (picked.length < 3 && pool.length) {
    let bestI = -1;
    let bestV = -Infinity;
    const homes = picked.filter((p) => ownHome(p.f)).length;
    pool.forEach((c, i) => {
      if (ownHome(c.f) && homes >= hcfg.most) return;
      const same = picked.filter((p) => p.f.expression === c.f.expression).length;
      const v = (picked.length === 0 ? c.score : c.lean) * Math.pow(cfg.diversity.sameExpression, same);
      if (v > bestV) { bestV = v; bestI = i; }
    });
    if (bestI < 0) break;
    const got = pool.splice(bestI, 1)[0];
    // The score stays the Reading's own; a kind offered for the home's sake says so in its reasons.
    if (picked.length > 0 && ownHome(got.f)) got.reasons = [...got.reasons, { line: 'home', key: home, share: 1, contribution: got.lean - got.score }];
    picked.push(got);
  }

  const heritagePool = current
    ? unique([...current.own, ...current.heritage, ...current.adaptations.map((a) => a.id)]).filter(
        (x) => x !== current.seedMark && !current.grafts.some((g) => g.feature === x),
      )
    : [];

  const candidates: Candidate[] = picked.map(({ f, score, reasons }) => {
    let heritage: string[] = [];
    if (current) {
      const options = heritagePool
        .filter((x) => !f.features.includes(x))
        .filter((x) => !isAdaptation(x) || isFixable(x))
        .map((x) => ({ x, s: scoreFeature(x, shares, emphasis, weights, cfg) }))
        .sort((a, b) => b.s - a.s || a.x.localeCompare(b.x));
      heritage = options.filter((o) => o.s >= cfg.heritage.minScore).slice(0, rules.genius.heritageMax).map((o) => o.x);
      if (heritage.length < rules.genius.heritageMin && options.length) heritage = options.slice(0, rules.genius.heritageMin).map((o) => o.x);
    }
    const grafts = current?.grafts.map((g) => g.feature) ?? [];
    return {
      form: f.id, name: f.name, expression: f.expression, silhouette: f.silhouette, score: round(score),
      own: f.features, heritage, seedMark, features: unique([seedMark, ...f.features, ...heritage, ...grafts]),
      reasons: reasons.map((r) => ({ ...r, share: round(r.share), contribution: round(r.contribution) })),
    };
  });

  return { instar: input.instar, crossingAllowed, lineLeads: leads, candidates };
}

/** The new genius after a candidate is taken. Fixed adaptations become heritage; the rest are lost. */
export function take(current: GeniusForm | null, c: Candidate, acceptedGrafts: GeniusForm['grafts'] = []): GeniusForm {
  return {
    form: c.form, expression: c.expression, own: c.own, heritage: c.heritage, seedMark: c.seedMark,
    grafts: [...(current?.grafts ?? []), ...acceptedGrafts], adaptations: [],
  };
}

export function isAdaptation(id: string): boolean {
  return !!data.features.find((f) => f.id === id)?.adaptation;
}
function isFixable(id: string): boolean {
  return !!data.features.find((f) => f.id === id)?.fixable;
}

function unique<T>(xs: T[]): T[] { return [...new Set(xs)]; }
function sum(xs: number[]): number { return xs.reduce((a, b) => a + b, 0); }
function mapValues<T, U>(o: Record<string, T>, fn: (v: T) => U): Record<string, U> {
  return Object.fromEntries(Object.entries(o).map(([k, v]) => [k, fn(v)]));
}
function round(x: number): number { return Math.round(x * 1000) / 1000; }
