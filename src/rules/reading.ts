// The Readings on the genius tree (docs/genius-tree.md): the rite offers three bases; a
// refinement offers the children of the form the genius is, and once, a turning.
import { data, byId, baseOf, formOf, childrenOf, hybridForms, type Form, type Leans, type ReadingConfig } from '../data';
import { alike, hybridId, hybridName } from '../data/tree';

/** The record of play since the last Reading. Counts, not shares. */
export interface Tally {
  families: Record<string, number>;
  range: Record<string, number>;
  orders: Record<string, number>;
  company: Record<string, number>;
  ground: Record<string, number>;
  discipline: Record<string, number>;
  bonds: Record<string, number>;
  intention: { form: string; terms: string[]; fires: number; sworn?: boolean } | null;
  runsWith: Record<string, number>;
  /** Raw counters ("fights.parries", "runs.party", "runs.quest.hunt", "fights.range.close", ...). */
  counters: Record<string, number>;
}

export function emptyTally(): Tally {
  return { families: {}, range: {}, orders: {}, company: {}, ground: {}, discipline: {}, bonds: {}, intention: null, runsWith: {}, counters: {} };
}

/** Who the genius belongs to: fixed facts that are read alongside play. */
export interface Origin { seed: string; blood: string; shape: string; /** Where the character grew up (a home of data/bodies.json). */ home?: string }

export interface GeniusForm {
  form: string;
  /** Its base, or first+second for a hybrid. */
  base: string;
  expression: string;
  /** The parts of the form it is: its own and those of the forms above it on its path. */
  own: string[];
  /** Adaptations it kept at a refinement. */
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
  base: string;
  name: string;
  text: string;
  expression: string;
  silhouette: string;
  level: number;
  score: number;
  own: string[];
  heritage: string[];
  seedMark: string;
  features: string[];
  reasons: Reason[];
}

export interface Turning {
  /** The base the play has turned toward, and the hybrid it makes. */
  second: string;
  base: string;
  name: string;
  /** How well the play fits its own base's nature, and the other's. */
  own: number;
  other: number;
  /** The lines of the Tally that speak for the other base. */
  reasons: Reason[];
  candidates: Candidate[];
}

export interface ReadingResult {
  instar: number;
  /** The level of the forms offered: 1 at the rite, 2 to 4 at a refinement. */
  level: number;
  candidates: Candidate[];
  turning: Turning | null;
  /** No new form: the finished form grows (instars five and six). The one candidate is the form it is, with what it kept. */
  grows: boolean;
}

type Lines = Record<string, Record<string, number>>;

const SHAPES = ['anchor', 'turn', 'cast', 'read', 'bind', 'make'];
const ORDERS = ['guard', 'hunt', 'hold', 'free'];
const FIGHTS = ['parries', 'blocks', 'hurts', 'dodges'];
const QUESTS = ['linework', 'salvage', 'hunt', 'escort', 'writ', 'deep-run'];
/** Where a run was, in the tree's words. */
export const GROUND: Record<string, string> = { tunnel: 'line', line: 'line', post: 'line', junction: 'line', river: 'water', sky: 'wild', wild: 'wild', water: 'water', ruin: 'ruin', night: 'night', quiet: 'quiet' };
/** The lines a refinement reads, in order. */
export const PLAY_LINES = ['range', 'orders', 'shape', 'fights', 'company', 'ground', 'pattern', 'bonds', 'quests'];

/** The Tally as the tree reads it: for each line, the share of each key and how much the line counts. */
export function playLines(t: Tally, cfg: ReadingConfig = data.reading): { shares: Lines; emphasis: Record<string, number> } {
  const counts: Lines = { range: {}, orders: {}, shape: {}, fights: {}, company: {}, ground: {}, quests: {} };
  for (const k of ['close', 'mid', 'far']) if (t.range[k]) counts.range[k] = t.range[k];
  for (const k of ORDERS) if (t.orders[k]) counts.orders[k] = t.orders[k];
  for (const [k, v] of Object.entries(t.families)) {
    const s = k.split('.')[0];
    if (SHAPES.includes(s) && v) counts.shape[s] = (counts.shape[s] ?? 0) + v;
  }
  for (const k of FIGHTS) if (t.counters[`fights.${k}`]) counts.fights[k] = t.counters[`fights.${k}`];
  for (const k of ['alone', 'party']) if (t.counters[`runs.${k}`]) counts.company[k] = t.counters[`runs.${k}`];
  for (const [k, v] of Object.entries(t.ground)) if (v) { const g = GROUND[k] ?? 'wild'; counts.ground[g] = (counts.ground[g] ?? 0) + v; }
  for (const k of QUESTS) if (t.counters[`runs.quest.${k}`]) counts.quests[k] = t.counters[`runs.quest.${k}`];
  const shares: Lines = {};
  const emphasis: Record<string, number> = {};
  for (const line of Object.keys(counts)) {
    const total = sum(Object.values(counts[line]));
    shares[line] = total > 0 ? mapValues(counts[line], (v) => v / total) : {};
    emphasis[line] = Math.min(1, total / (cfg.refine.reference[line] ?? 1));
  }
  shares.pattern = t.intention ? { fires: Math.min(1, t.intention.fires / cfg.refine.patternFires), sworn: t.intention.sworn ? 1 : 0 } : {};
  emphasis.pattern = t.intention ? 1 : 0;
  const bonds: Record<string, number> = {
    classmate: (t.bonds.classmate ?? 0) > 0 || Object.values(t.runsWith).some((v) => v > 0) ? 1 : 0,
    shade: (t.bonds.shade ?? 0) > 0 || (t.bonds.hearth ?? 0) > 0 ? 1 : 0,
    named: (t.bonds.named ?? 0) > 0 ? 1 : 0,
  };
  shares.bonds = bonds;
  emphasis.bonds = Object.values(bonds).some((v) => v > 0) ? 1 : 0;
  return { shares, emphasis };
}

/** How well the play fits a set of leans, 0 to 1 or so, and the lines that speak for it. */
export function fit(leans: Leans, lines: { shares: Lines; emphasis: Record<string, number> }, cfg: ReadingConfig = data.reading): { score: number; reasons: Reason[] } {
  let num = 0;
  let den = 0;
  const reasons: Reason[] = [];
  for (const [line, keys] of Object.entries(leans)) {
    const w = (cfg.refine.weights[line] ?? 0) * (lines.emphasis[line] ?? 0);
    for (const [key, lean] of Object.entries(keys)) {
      den += lean;
      const share = lines.shares[line]?.[key] ?? 0;
      const c = w * lean * share;
      if (c > 0) { num += c; reasons.push({ line, key, share, contribution: c }); }
    }
  }
  if (den > 0) for (const r of reasons) r.contribution /= den;
  reasons.sort((a, b) => b.contribution - a.contribution || cmp(a.line, b.line) || cmp(a.key, b.key));
  return { score: den > 0 ? num / den : 0, reasons: reasons.slice(0, 3) };
}

export interface ReadingInput {
  instar: number;
  tally: Tally;
  origin: Origin;
  current: GeniusForm | null;
  cfg?: ReadingConfig;
  rules?: typeof data.rules;
}

function candidate(f: Form, score: number, reasons: Reason[], seedMark: string, heritage: string[], grafts: string[]): Candidate {
  return {
    form: f.id, base: f.base, name: f.name, text: f.text, expression: f.expression, silhouette: f.silhouette, level: f.level, score: round(score),
    own: f.features, heritage, seedMark, features: unique([seedMark, ...f.features, ...heritage, ...grafts].filter((x) => x !== '')),
    reasons: reasons.map((r) => ({ ...r, share: round(r.share), contribution: round(r.contribution) })),
  };
}

/** The rite: three bases, read from the Seed, the blood and the Shape, leaned by the home. */
function rite(input: ReadingInput, cfg: ReadingConfig, seedMark: string): ReadingResult {
  const o = input.origin;
  const own: Record<string, string> = { seed: o.seed, blood: o.blood, shape: o.shape };
  const lean = data.homes[o.home ?? ''] ?? {};
  const scored = data.bases.map((b) => {
    let raw = 0;
    const reasons: Reason[] = [];
    for (const line of ['seed', 'blood', 'shape'] as const) {
      const c = (cfg.rite.weights[line] ?? 0) * (b.calls[line]?.[own[line]] ?? 0);
      if (c > 0) { raw += c; reasons.push({ line, key: own[line], share: 1, contribution: c }); }
    }
    reasons.sort((x, y) => y.contribution - x.contribution || cmp(x.line, y.line));
    return { b, raw, leaned: raw * (lean[b.id] ?? 1), reasons };
  });
  const picked: typeof scored = [];
  const pool = [...scored];
  while (picked.length < 3 && pool.length) {
    let bestI = 0;
    let bestV = -Infinity;
    pool.forEach((c, i) => {
      const same = picked.filter((p) => p.b.class === c.b.class).length;
      // the best fit is the field's own; the home leans only what is offered beside it
      const v = (picked.length === 0 ? c.raw : c.leaned) * Math.pow(cfg.rite.sameClass, same);
      if (v > bestV) { bestV = v; bestI = i; }
    });
    const got = pool.splice(bestI, 1)[0];
    if (picked.length > 0 && got.leaned > got.raw) got.reasons = [...got.reasons, { line: 'home', key: o.home ?? '', share: 1, contribution: got.leaned - got.raw }];
    picked.push(got);
  }
  return {
    instar: 1, level: 1, turning: null, grows: false,
    candidates: picked.map((p) => candidate(formOf(p.b.settled.id)!, p.raw, p.reasons, seedMark, [], [])),
  };
}

/**
 * Read for instar n. The rite (no genius yet) offers three bases. A refinement offers the
 * children of the form the genius is, best fit first; the first refinement may also offer a
 * turning. From the fifth instar nothing is offered: the finished form grows.
 */
export function read(input: ReadingInput): ReadingResult {
  const cfg = input.cfg ?? data.reading;
  const rules = input.rules ?? data.rules;
  const seedMark = byId(data.seeds, input.origin.seed, 'Seed').seedMark;
  const current = input.current;
  if (!current || input.instar === 1) return rite(input, cfg, seedMark);
  const kids = childrenOf(current.form);
  // What it kept fed becomes part of it.
  const heritage = unique([...current.heritage, ...current.adaptations.map((a) => a.id).filter(isFixable)]).slice(0, rules.genius.heritageMax);
  const grafts = current.grafts.map((g) => g.feature);
  // A finished form is offered nothing new: it grows, as itself, an age on.
  const self = formOf(current.form);
  if (!kids.length) return { instar: input.instar, level: self?.level ?? 4, candidates: self ? [candidate(self, 0, [], seedMark, heritage, grafts)] : [], turning: null, grows: true };
  const lines = playLines(input.tally, cfg);
  const offer = (forms: Form[]) => forms
    .map((f, i) => ({ f, i, ...fit(f.leans, lines, cfg) }))
    .sort((a, b) => round(b.score) - round(a.score) || a.i - b.i)   // of equal fits, the one written first
    .map((x) => candidate(x.f, x.score, x.reasons, seedMark, heritage, grafts));
  const candidates = offer(kids);
  let turning: Turning | null = null;
  const mine = baseOf(current.base);
  if (kids[0].level === 2 && mine) {
    const own = fit(mine.nature, lines, cfg).score;
    let best: { id: string; score: number; reasons: Reason[] } | null = null;
    for (const b of data.bases) {
      if (b.id === mine.id) continue;
      const s = fit(b.nature, lines, cfg);
      if (!best || s.score > best.score) best = { id: b.id, score: s.score, reasons: s.reasons };
    }
    if (best && best.score >= data.hybrids.rule.min && best.score >= own * (1 + data.hybrids.rule.margin)) {
      const other = baseOf(best.id)!;
      const paths = hybridForms(mine.id, other.id).filter((f) => f.level === 2);
      turning = { second: other.id, base: hybridId(mine.id, other.id), name: hybridName(mine, other, data.hybrids), own: round(own), other: round(best.score), reasons: best.reasons.map((r) => ({ ...r, share: round(r.share), contribution: round(r.contribution) })), candidates: offer(paths) };
    }
  }
  return { instar: input.instar, level: kids[0].level, candidates, turning, grows: false };
}

/** The genius after a candidate is taken: its form, what it kept, and its grafts. Adaptations start again. */
export function take(current: GeniusForm | null, c: Candidate, acceptedGrafts: GeniusForm['grafts'] = []): GeniusForm {
  return {
    form: c.form, base: c.base, expression: c.expression, own: c.own, heritage: c.heritage, seedMark: c.seedMark,
    grafts: [...(current?.grafts ?? []), ...acceptedGrafts], adaptations: [],
  };
}

export function isAdaptation(id: string): boolean {
  return !!data.features.find((f) => f.id === id)?.adaptation;
}
function isFixable(id: string): boolean {
  return !!data.features.find((f) => f.id === id)?.fixable;
}

/** How alike a form's leans are to a base's nature (for the tools). */
export function nearness(f: Form, baseId: string): number {
  const b = baseOf(baseId);
  return b ? alike(f.leans, b.nature) : 0;
}

function cmp(a: string, b: string): number { return a < b ? -1 : a > b ? 1 : 0; }
function unique<T>(xs: T[]): T[] { return [...new Set(xs)]; }
function sum(xs: number[]): number { return xs.reduce((a, b) => a + b, 0); }
function mapValues<T, U>(o: Record<string, T>, fn: (v: T) => U): Record<string, U> {
  return Object.fromEntries(Object.entries(o).map(([k, v]) => [k, fn(v)]));
}
function round(x: number): number { return Math.round(x * 1000) / 1000; }
