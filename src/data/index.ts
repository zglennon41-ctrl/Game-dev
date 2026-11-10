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
import homesJson from '../../data/genius-homes.json';
import hybridsJson from '../../data/genius-hybrids.json';
import secondaryJson from '../../data/secondary-forms.json';
import shadesJson from '../../data/shades.json';
import rosterJson from '../../data/roster.json';
import techniquesJson from '../../data/techniques.json';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { flatten, compose, type Base, type Form, type Hybrids } from './tree';

export type { Base, Form, Hybrids, Leans, TreeNode } from './tree';

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

export interface ReadingConfig {
  /** The rite: the weight of each line of the character's own (Seed, blood, Shape), and what a second base of a class already offered counts for. */
  rite: { weights: Record<string, number>; sameClass: number };
  /** A refinement: the weight of each line of the Tally, the play a line needs to count in full, and the fires a Pattern needs. */
  refine: { weights: Record<string, number>; reference: Record<string, number>; patternFires: number };
  /** How a line of the Tally is said in plain words. */
  words?: Record<string, Record<string, string> | string>;
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
  /** The bases of the genius tree (data/genius-bases), by id. */
  bases: Base[];
  /** Every form of every base, each base's settled form first. Hybrids are asked for with formOf. */
  forms: Form[];
  /** Each home's lean on the bases at the rite (data/genius-homes.json). */
  homes: Record<string, Record<string, number>>;
  hybrids: Hybrids;
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
  features: [],
  adaptations: adaptationsJson as Adaptation[],
  bases: [],
  forms: [],
  homes: Object.fromEntries(Object.entries(homesJson).filter(([k]) => !k.startsWith('$'))) as unknown as Record<string, Record<string, number>>,
  hybrids: hybridsJson as unknown as Hybrids,
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

const dataDir = fileURLToPath(new URL('../../data/', import.meta.url));

/** Read every base in a folder (data/genius-bases by default), in the order of their ids. */
export function loadBases(dir = dataDir + 'genius-bases'): Base[] {
  return readdirSync(dir).filter((f) => f.endsWith('.json')).sort().map((f) => JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')) as Base);
}

let formIndex = new Map<string, Form>();
const hybridCache = new Map<string, Form[]>();

/** Set the bases the rules run on (the game's own by default; a test may add its own). */
export function useBases(bases: Base[]): void {
  data.bases = [...bases].sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  data.forms = data.bases.flatMap(flatten);
  formIndex = new Map(data.forms.map((f) => [f.id, f]));
  hybridCache.clear();
  const extra = data.bases.flatMap((b) => b.newFeatures ?? []).map((f) => ({ bonus: {}, ...f })) as Feature[];
  const known = new Set((featuresJson as Feature[]).map((f) => f.id));
  data.features = [...(featuresJson as Feature[]), ...extra.filter((f) => !known.has(f.id))];
}
useBases(loadBases());

export function baseOf(id: string): Base | undefined {
  return data.bases.find((b) => b.id === id);
}

/** The thirty forms of the hybrid of two bases (docs/genius-tree.md, Hybrids). */
export function hybridForms(first: string, second: string): Form[] {
  const key = `${first}+${second}`;
  if (!hybridCache.has(key)) {
    const a = baseOf(first);
    const b = baseOf(second);
    hybridCache.set(key, a && b && a.id !== b.id ? compose(a, b, data.hybrids, Object.fromEntries(data.features.map((f) => [f.id, f.label]))) : []);
  }
  return hybridCache.get(key)!;
}

/** A form by its id: a form of a base, or of a hybrid (first+second:form). */
export function formOf(id: string): Form | undefined {
  const pure = formIndex.get(id);
  if (pure || !id.includes(':')) return pure;
  const [first, second] = id.split(':')[0].split('+');
  return hybridForms(first, second).find((f) => f.id === id);
}

/** The forms a form may become. */
export function childrenOf(id: string): Form[] {
  return (formOf(id)?.children ?? []).map((c) => formOf(c)!).filter(Boolean);
}
