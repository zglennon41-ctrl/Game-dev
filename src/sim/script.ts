// The shape of a scripted life (data/lives/*.json). Rates are per day unless named otherwise.
import type { LineColor, ShapeId } from '../data';
import type { PatternSpec } from '../rules/terms';

export interface Phase {
  /** First day (inclusive) and last day (exclusive). Day 0 is the rite, on the first day of a Thaw. */
  from: number;
  to: number;
  label?: string;
  runsPerDay?: number;
  /** Fights per day outside runs (the Academy yard, sparring). */
  fightsPerDay?: number;
  fightsPerRun?: number;
  /** Share of fights at each range. */
  range?: Partial<Record<'close' | 'mid' | 'far', number>>;
  /** Technique uses per fight, by "<shape>.<family>" or "<discipline>.school". */
  families?: Record<string, number>;
  ordersPerDay?: number;
  /** Share of orders by kind. */
  orders?: Partial<Record<'guard' | 'hunt' | 'hold' | 'free' | 'duet', number>>;
  /** Share of runs with a member of each Shape in the party. */
  company?: Partial<Record<ShapeId, number>>;
  /** Share of runs beside a named member. */
  runsWith?: Record<string, number>;
  /** Share of runs by ground. */
  ground?: Partial<Record<'tunnel' | 'ruin' | 'water' | 'sky' | 'wild' | 'quiet', number>>;
  /** Share of runs after dark. */
  night?: number;
  /** Share of runs by quest type (linework, salvage, hunt, escort, writ). */
  questTypes?: Record<string, number>;
  /** How the partner meets a blow, per fight: parries, blocks, hurts, dodges. */
  meets?: Partial<Record<'parries' | 'blocks' | 'hurts' | 'dodges', number>>;
  /** The Pattern's fires per day (only once built). */
  patternFiresPerDay?: number;
  /** Uses of techniques in the genius's field by anyone, per day ("make.ward"). */
  fieldUses?: Record<string, number>;
  /** Posted quests that count for Marks, per day, by archetype and line color. */
  quests?: Array<{ archetype: string; color: LineColor; perDay: number }>;
  /** Technique uses per day, by technique id, for grades. */
  techniques?: Record<string, number>;
  /** Sunday at the hearth. */
  hearthSundays?: boolean;
  kitchenHigh?: boolean;
}

export type LifeEvent =
  | { day: number; type: 'take-archetype'; archetype: string }
  | { day: number; type: 'equip'; archetype: string }
  | ({ day: number; type: 'build-pattern' } & PatternSpec)
  | { day: number; type: 'swear' }
  | { day: number; type: 'shade-accept'; shade: string }
  | { day: number; type: 'named-kill'; beast: string; features?: string[] }
  | { day: number; type: 'rally-won' }
  | { day: number; type: 'peer-uses'; account: string; character: string; uses: number };

export interface Life {
  id: string;
  name: string;
  account: string;
  guild: string;
  blood: string;
  seed: string;
  shape: ShapeId;
  city: string;
  discipline: string;
  swornCharacter?: boolean;
  days: number;
  gateDay: number;
  /** The archetype equipped at the Gate. */
  archetype: string;
  phases: Phase[];
  events: LifeEvent[];
  /** What the player picks at a Reading, by instar. Absent: settle on the best fit. */
  picks?: Record<string, { expression?: string; form?: string; /** At the rite: the base to settle as. */ base?: string; /** At the first refinement: take the turning if one is offered. */ turn?: boolean }>;
  focus?: string;
  grafts?: 'accept' | 'decline';
  /** Feature each companion's genius gives in a Kin-form, for companions not in data/roster.json. */
  companions?: Record<string, { kinFeature: string }>;
}
