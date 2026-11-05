// The rules, as data. Code reads these; designers edit the JSON in data/.
import rulesJson from '../../data/rules.json';
import readingJson from '../../data/reading.json';
import shapesJson from '../../data/shapes.json';
import wheelJson from '../../data/wheel.json';
import disciplinesJson from '../../data/disciplines.json';
import archetypesJson from '../../data/archetypes.json';
import termsJson from '../../data/terms.json';
import seedsJson from '../../data/seeds.json';
import bloodsJson from '../../data/bloods.json';
import featuresJson from '../../data/features.json';
import adaptationsJson from '../../data/adaptations.json';
import formsJson from '../../data/forms.json';
import secondaryJson from '../../data/secondary-forms.json';
import shadesJson from '../../data/shades.json';
import rosterJson from '../../data/roster.json';
import techniquesJson from '../../data/techniques.json';

export type ShapeId = 'anchor' | 'turn' | 'cast' | 'read' | 'bind' | 'make';
export type Expression = 'beast' | 'kith' | 'engine' | 'relic' | 'daemon' | 'aspect';
export type TermKind = 'trigger' | 'toll' | 'bar';
export type LineColor = 'green' | 'amber' | 'red' | 'black';

export interface Shape { id: ShapeId; name: string; families: string[]; pulseMs: number; bowlSign: string; palette: string }
export interface Discipline { id: string; name: string; city: string; weapons: string[]; stanceModifier: string; techniques: string[]; rite: string; launch: boolean }
export interface Archetype { id: string; name: string; shape: ShapeId; discipline: string }
export interface Term {
  id: string; n: number; kind: TermKind; text: string; multiplier: number;
  predicate?: string; apply?: string; forbids?: string; tags: string[]; swornOnly?: boolean;
}
export interface Seed { id: string; text: string; seedMark: string; leansToward: string }
export interface Blood { id: string; tier: 'mark' | 'kindred' | 'bloodline'; name: string; gift: string; gap: string; house?: string; shapeLean?: Record<string, number>; graft?: string }
export interface Feature { id: string; slot: string; label: string; bonus: Record<string, unknown>; fixable?: boolean; adaptation?: boolean; tags?: string[] }
export interface Adaptation { id: string; metric: string; threshold: number }
export interface Form { id: string; name: string; expression: Expression; silhouette: string; features: string[]; instars: { min: number; max: number } }
export type Requirement =
  | { kind: 'rank'; archetypeDiscipline: string; rank: 'adept' | 'master' }
  | { kind: 'expression'; in: Expression[] }
  | { kind: 'counter'; metric: string; atLeast: number }
  | { kind: 'patternFamily'; family: string }
  | { kind: 'instar'; atLeast: number }
  | { kind: 'accord' };
export interface SecondaryForm { id: string; name: string; does: string; requires: Requirement[] }
export interface Shade { id: string; name: string; discipline: string; expression: Expression; features: string[]; graftFeature: string; pattern: { name: string; form: string } }
export interface RosterMember { id: string; name: string; shape: ShapeId; genius: { form: string; expression: Expression; features: string[]; kinFeature: string } }
export interface Technique { id: string; name: string; shape: ShapeId; family: string; beats: number; will: number; stage: number; placeholder?: boolean }

export interface Lean { expression: Partial<Record<Expression, number>>; features: Record<string, number> }
export interface ReadingConfig {
  weights: Record<string, number>;
  firstFormWeights: Record<string, number>;
  emphasis: { reference: Record<string, number>; intentionBase: number; intentionFires: number };
  diversity: { sameExpression: number };
  crossing: { linesAway: number; stayBonus: number };
  heritage: { sharedBonus: number; minScore: number };
  leans: Record<string, Record<string, Lean>>;
}

export type Rules = typeof rulesJson;

export interface GameData {
  rules: Rules;
  reading: ReadingConfig;
  shapes: Shape[];
  wheel: ShapeId[];
  disciplines: Discipline[];
  archetypes: Archetype[];
  terms: Term[];
  seeds: Seed[];
  bloods: Blood[];
  features: Feature[];
  adaptations: Adaptation[];
  forms: Form[];
  secondaryForms: SecondaryForm[];
  shades: Shade[];
  roster: RosterMember[];
  techniques: Technique[];
}

export const data: GameData = {
  rules: rulesJson,
  reading: readingJson as unknown as ReadingConfig,
  shapes: shapesJson as Shape[],
  wheel: wheelJson.order as ShapeId[],
  disciplines: disciplinesJson as Discipline[],
  archetypes: archetypesJson as Archetype[],
  terms: termsJson as Term[],
  seeds: seedsJson as Seed[],
  bloods: bloodsJson as Blood[],
  features: featuresJson as Feature[],
  adaptations: adaptationsJson as Adaptation[],
  forms: formsJson as Form[],
  secondaryForms: secondaryJson as SecondaryForm[],
  shades: shadesJson as Shade[],
  roster: rosterJson as RosterMember[],
  techniques: techniquesJson as Technique[],
};

export function byId<T extends { id: string }>(list: T[], id: string, what = 'item'): T {
  const found = list.find((x) => x.id === id);
  if (!found) throw new Error(`Unknown ${what}: ${id}`);
  return found;
}
