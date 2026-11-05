// Marks, archetype ranks, technique grades, cross titles, and founding eligibility.
import { data, byId, type LineColor } from '../data';

const M = data.rules.marks;

export function marksFor(color: LineColor, opts: { swornCharacter?: boolean; archivist?: boolean } = {}): number {
  let m = M.byColor[color];
  if (opts.swornCharacter) m *= M.swornMultiplier;
  if (opts.archivist) m *= M.archivistMultiplier;
  return m;
}

export type Rank = 'journeyman' | 'adept' | 'master';

/** Rank in one archetype. Adept needs Stage 4; Master needs a Pattern built in it. */
export function rankFor(x: { marks: number; stage: number; patternBuiltIn: boolean }): Rank {
  if (x.marks >= M.master && x.patternBuiltIn && x.stage >= 4) return 'master';
  if (x.marks >= M.adept && x.stage >= 4) return 'adept';
  return 'journeyman';
}

export function gradeFor(uses: number): string {
  let g = data.rules.grades[0].grade;
  for (const x of data.rules.grades) if (uses >= x.uses) g = x.grade;
  return g;
}

/** Adept or better in two archetypes: shown as both names, the earlier first (a Deadeye Draw-Cutter). */
export function crossTitle(ranked: Array<{ archetype: string; rank: Rank; since: number }>): string | null {
  const held = ranked.filter((r) => r.rank !== 'journeyman').sort((a, b) => a.since - b.since);
  if (held.length < 2) return null;
  return held.slice(0, 2).map((r) => byId(data.archetypes, r.archetype, 'archetype').name).join(' ');
}

export interface FoundingMember { account: string; guild: string; form: string; terms: string[]; witnessedUses: number }

/**
 * Three members of one guild, from three accounts, each with 10 witnessed uses of a Pattern
 * with the identical Form and Terms, may found. Terms are compared as a set.
 */
export function foundingEligible(members: FoundingMember[]): { eligible: boolean; reason: string } {
  const F = data.rules.founding;
  if (members.length < F.members) return { eligible: false, reason: `needs ${F.members} members` };
  const key = (m: FoundingMember) => `${m.form}|${[...m.terms].sort().join(',')}`;
  const k0 = key(members[0]);
  if (!members.every((m) => key(m) === k0)) return { eligible: false, reason: 'Form and Terms must be identical' };
  if (!members.every((m) => m.guild === members[0].guild)) return { eligible: false, reason: 'all from one guild' };
  if (new Set(members.map((m) => m.account)).size < F.accounts) return { eligible: false, reason: `needs ${F.accounts} accounts` };
  const short = members.filter((m) => m.witnessedUses < F.usesEach);
  if (short.length) return { eligible: false, reason: `each needs ${F.usesEach} witnessed uses` };
  return { eligible: true, reason: 'eligible' };
}
