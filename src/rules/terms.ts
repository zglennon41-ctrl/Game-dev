// Terms and Patterns: build a Pattern, compute its multiplier and chain, judge a use.
import { data, byId, type ShapeId, type Term } from '../data';
import { canPattern } from './field';

const P = data.rules.pattern;

export interface PatternSpec {
  name: string;
  /** "<shape>.<family>", e.g. "cast.reach". */
  form: string;
  technique?: string;
  terms: string[];
  sworn: boolean;
  /** The archetype equipped when it was built (Master needs a Pattern built in it). */
  archetype?: string;
}

export interface BuiltPattern extends PatternSpec {
  multiplier: number;
  chainBeats: number;
  /** Stage 4 output on the Form times the Terms multiplier. */
  output: number;
}

export class PatternError extends Error {}

export function formShape(form: string): ShapeId {
  return form.split('.')[0] as ShapeId;
}

export function termsOf(ids: string[]): Term[] {
  return ids.map((id) => byId(data.terms, id, 'Term'));
}

/**
 * Validate and price a Pattern. One Form from the character's own Shape; at most one Term
 * of each kind, up to three; a Sworn character may take a fourth Term of any kind.
 */
export function buildPattern(spec: PatternSpec, character: { shape: ShapeId; swornCharacter?: boolean }): BuiltPattern {
  if (!canPattern(character.shape, formShape(spec.form))) {
    throw new PatternError(`A Pattern's Form must be of the character's own Shape (${character.shape}); got ${spec.form}`);
  }
  const terms = termsOf(spec.terms);
  const max = character.swornCharacter ? P.maxTermsSworn : P.maxTermsPerPattern;
  if (terms.length > max) throw new PatternError(`At most ${max} Terms; got ${terms.length}`);
  const kinds = terms.map((t) => t.kind);
  const dupes = kinds.filter((k, i) => kinds.indexOf(k) !== i);
  // The fourth Term of a Sworn character may repeat a kind; nobody else may.
  if (dupes.length > (character.swornCharacter && terms.length === 4 ? 1 : 0)) {
    throw new PatternError(`At most one Term of each kind (repeated: ${dupes.join(', ')})`);
  }
  for (const t of terms) {
    if (t.swornOnly && !character.swornCharacter) throw new PatternError(`${t.id} is for Sworn characters only`);
  }
  const multiplier = patternMultiplier(spec.terms, spec.sworn);
  return { ...spec, multiplier, chainBeats: chainBeats(spec.terms.length), output: P.stage4FormOutput * multiplier };
}

/** Product of the Terms' multipliers, doubled if sworn, capped at the ceiling (x9). */
export function patternMultiplier(termIds: string[], sworn: boolean): number {
  let m = termsOf(termIds).reduce((acc, t) => acc * t.multiplier, 1);
  if (sworn) m *= P.swornMultiplier;
  return Math.min(m, P.multiplierCeiling);
}

/** Beats in the chain: three for the Form, one per Term, plus one per verse. */
export function chainBeats(termCount: number, verses = 0): number {
  return P.chainBaseBeats + P.beatsPerTerm * termCount + verses;
}

/** What is true about the moment a Pattern is fired. Predicates and bars read these. */
export interface FireContext {
  wasStruckThisFight?: boolean; health?: number; healthMax?: number; will?: number; willMax?: number;
  beatOfFight?: number; isNight?: boolean; memberBehind?: boolean; geniusDown?: boolean; geniusBeside?: boolean;
  foeDownedMember?: boolean; standingAllies?: number; foes?: number; allies?: number; underground?: boolean;
  foeNamedAloud?: boolean; afterPerfectHold?: boolean; usesThisExcursion?: number; allySees?: boolean;
  bloodBared?: boolean; outOfStill?: boolean; pastThePost?: boolean;
  target?: { unarmed?: boolean; sharedMeal?: boolean; struckByPattern?: boolean; person?: boolean; beast?: boolean; cohort?: boolean };
  inHall?: boolean; line?: 'green' | 'amber' | 'red' | 'black'; guildMarkCovered?: boolean; isSunday?: boolean;
  toSaveSelf?: boolean; borrowedWeapon?: boolean; declared?: boolean; memberFallenThisRun?: boolean; inQuiet?: boolean;
}

type Pred = (c: FireContext) => boolean;

/** Trigger predicates, by the name in data/terms.json. */
export const triggerPredicates: Record<string, Pred> = {
  wasStruckThisFight: (c) => !!c.wasStruckThisFight,
  belowHalfHealth: (c) => (c.health ?? 100) < (c.healthMax ?? 100) / 2,
  fullWill: (c) => (c.will ?? 0) >= (c.willMax ?? 100),
  onSeventhBeat: (c) => c.beatOfFight === 7,
  isNight: (c) => !!c.isNight,
  isDay: (c) => !c.isNight,
  memberBehind: (c) => !!c.memberBehind,
  geniusDown: (c) => !!c.geniusDown,
  geniusBeside: (c) => !!c.geniusBeside,
  foeDownedMember: (c) => !!c.foeDownedMember,
  lastStanding: (c) => c.standingAllies === 0,
  outnumbered: (c) => (c.foes ?? 0) > (c.allies ?? 1),
  underground: (c) => !!c.underground,
  foeNamedAloud: (c) => !!c.foeNamedAloud,
  afterPerfectHold: (c) => !!c.afterPerfectHold,
  firstUseThisExcursion: (c) => (c.usesThisExcursion ?? 0) === 0,
  allySees: (c) => !!c.allySees,
  bloodBared: (c) => !!c.bloodBared,
  outOfStill: (c) => !!c.outOfStill,
  pastThePost: (c) => !!c.pastThePost,
};

/** Bar conditions: true means the Bar forbids this use. */
export const barConditions: Record<string, Pred> = {
  targetUnarmed: (c) => !!c.target?.unarmed,
  targetSharedMeal: (c) => !!c.target?.sharedMeal,
  targetAlreadyStruckByPattern: (c) => !!c.target?.struckByPattern,
  inHall: (c) => !!c.inHall,
  targetPerson: (c) => !!c.target?.person,
  targetBeast: (c) => !!c.target?.beast,
  onGreenLine: (c) => c.line === 'green',
  guildMarkCovered: (c) => !!c.guildMarkCovered,
  isSunday: (c) => !!c.isSunday,
  toSaveSelf: (c) => !!c.toSaveSelf,
  targetCohort: (c) => !!c.target?.cohort,
  borrowedWeapon: (c) => !!c.borrowedWeapon,
  undeclared: (c) => !c.declared,
  memberFallenThisRun: (c) => !!c.memberFallenThisRun,
  inQuiet: (c) => !!c.inQuiet,
};

/** Toll effects, by name. The simulator and the game apply these; the rules only list them. */
export const tollEffects = new Set([
  'disarmForRun', 'geniusSitsOut', 'burnMark', 'silenceUntilLamp', 'halveHealth', 'emptyWill', 'infirmaryNight',
  'spendFavor', 'noStanceSeason', 'speakTerms', 'geniusClock', 'doubleCostNext3', 'tithe', 'spendStanding', 'scar',
  'forfeitLoot', 'leakForRun', 'forgetShadow', 'noDuetSeason', 'yearOfLife',
]);

export type UseVerdict =
  | { kind: 'unavailable'; reason: string }
  | { kind: 'warn-bar'; bars: string[] }
  | { kind: 'fires'; tolls: string[] }
  | { kind: 'breach'; bars: string[]; tolls: string[]; consequence: BreachConsequence };

export type BreachConsequence = 'lost-forever' | 'lost-for-season' | 'death';

/**
 * Judge one use. A Trigger not met makes the Pattern unavailable (it cannot be breached).
 * A Bar that covers the moment makes the Pattern refuse with a warning; firing anyway
 * (override) is the breach. Tolls are always taken.
 */
export function judgeUse(p: PatternSpec, ctx: FireContext, opts: { override?: boolean; swornCharacter?: boolean } = {}): UseVerdict {
  const terms = termsOf(p.terms);
  for (const t of terms.filter((t) => t.kind === 'trigger')) {
    const pred = triggerPredicates[t.predicate!];
    if (!pred(ctx)) return { kind: 'unavailable', reason: t.text };
  }
  const tolls = terms.filter((t) => t.kind === 'toll').map((t) => t.apply!);
  const bars = terms.filter((t) => t.kind === 'bar' && barConditions[t.forbids!](ctx)).map((t) => t.id);
  if (bars.length === 0) return { kind: 'fires', tolls };
  if (!opts.override) return { kind: 'warn-bar', bars };
  return { kind: 'breach', bars, tolls, consequence: breachConsequence(p.sworn, !!opts.swornCharacter) };
}

/** Sworn breach: the Pattern is gone for good (for a Sworn character, death). Unsworn: gone a season. */
export function breachConsequence(sworn: boolean, swornCharacter: boolean): BreachConsequence {
  if (!sworn) return 'lost-for-season';
  return swornCharacter ? 'death' : 'lost-forever';
}

/** Intention keys the Reading reads from a Pattern: its Form family and its Terms' tags. */
export function intentionKeys(p: Pick<PatternSpec, 'form' | 'terms'>): Record<string, number> {
  const keys: Record<string, number> = { [`family:${p.form}`]: 1 };
  const tags = termsOf(p.terms).flatMap((t) => t.tags);
  for (const tag of tags) keys[`tag:${tag}`] = (keys[`tag:${tag}`] ?? 0) + 1 / tags.length;
  return keys;
}
