// Resonance: Intention tier from uses, Resonance from (instar, tier), what each milestone unlocks.
import { data } from '../data';

const R = data.rules;

export interface TierInputs {
  uses: number;
  built: boolean;
  sworn: boolean;
  /** Master in the archetype the Pattern was built in. */
  masterInArchetype: boolean;
  /** Days since the character reached Stage 4. */
  stage4Days: number;
}

/** Intention tier, 0 if no Pattern. Thresholds are exact. */
export function tierFor(x: TierInputs): number {
  if (!x.built) return 0;
  let tier = 0;
  for (const t of R.tiers as Array<{ tier: number; uses: number; stage4Days?: number; sworn?: boolean; masterInArchetype?: boolean }>) {
    if (x.uses < t.uses) break;
    if (t.stage4Days !== undefined && x.stage4Days < t.stage4Days) break;
    if (t.sworn && !x.sworn) break;
    if (t.masterInArchetype && !x.masterInArchetype) break;
    tier = t.tier;
  }
  return tier;
}

/** Resonance, on the instar scale: the higher of the genius's instar and the Pattern's tier (offset). */
export function resonance(instar: number, tier: number): number {
  const tierSide = tier > 0 ? tier + R.resonance.tierOffset : 0;
  return Math.min(6, Math.max(instar, tierSide));
}

/** The tier the Pattern pays at, given Resonance. */
export function payingTier(res: number, tier: number): number {
  return Math.max(tier, res - R.resonance.tierOffset);
}

/** Verses (extra beats) the Pattern carries when it pays at a tier. */
export function verses(payTier: number): number {
  let v = 0;
  for (const [t, n] of Object.entries(R.verses.byTierEquivalent)) if (payTier >= Number(t)) v = Math.max(v, n);
  return v;
}

export function shadowCap(res: number): number {
  return (R.genius.shadowCapByResonance as Record<string, number>)[String(res)] ?? 0;
}

export function geniusWill(res: number): number {
  return R.genius.willBase + R.genius.willPerInstar * (Math.max(1, res) - 1);
}

export function isAccord(instar: number, tier: number): boolean {
  return instar >= R.accord.instar && tier >= R.accord.tier;
}

export type Milestone = 'rite' | 'gate' | 'pattern-built' | 'adept' | 'master' | 'accord';

export interface InstarRule { instar: number; name: string; minDay: number; unlockedBy: string[] }

export function instarRule(n: number): InstarRule {
  const r = (R.instars as InstarRule[]).find((x) => x.instar === n);
  if (!r) throw new Error(`No instar ${n}`);
  return r;
}

/** Which condition (if any) has unlocked instar n, given milestones reached and the current tier. */
export function unlockReason(n: number, milestones: ReadonlySet<string>, tier: number): string | null {
  if (n > 6) return null;
  for (const u of instarRule(n).unlockedBy) {
    if (u.startsWith('tier:')) {
      if (tier >= Number(u.slice(5))) return u;
    } else if (milestones.has(u)) return u;
  }
  return null;
}

/** May the Reading for instar n happen today? Unlocked, and the genius old enough. */
export function readingDue(n: number, day: number, milestones: ReadonlySet<string>, tier: number): string | null {
  if (n > 6) return null;
  const reason = unlockReason(n, milestones, tier);
  if (!reason) return null;
  return day >= instarRule(n).minDay ? reason : null;
}
