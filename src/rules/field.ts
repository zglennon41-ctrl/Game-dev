// The field: Will, states, reach by Stage, affinity by wheel distance.
import { data, type ShapeId } from '../data';

const F = data.rules.field;

export type FieldState = 'open' | 'held' | 'shaped' | 'still' | 'folded' | 'fainted';

/** Steps around the wheel between two Shapes: 0 own, 1 adjacent, 2 two away, 3 opposite. */
export function wheelDistance(a: ShapeId, b: ShapeId, wheel = data.wheel): number {
  const i = wheel.indexOf(a);
  const j = wheel.indexOf(b);
  if (i < 0 || j < 0) throw new Error(`Unknown Shape: ${i < 0 ? a : b}`);
  const d = Math.abs(i - j);
  return Math.min(d, wheel.length - d);
}

export function opposite(shape: ShapeId, wheel = data.wheel): ShapeId {
  return wheel[(wheel.indexOf(shape) + wheel.length / 2) % wheel.length];
}

/** Output a character gets from a technique of another Shape: 100/80/60/40. */
export function affinity(own: ShapeId, technique: ShapeId): number {
  return F.affinityByDistance[wheelDistance(own, technique)];
}

/** Will cost multiplier for a technique of another Shape: x1, x1.25, x1.5, x2. */
export function costMultiplier(own: ShapeId, technique: ShapeId): number {
  return F.costMultiplierByDistance[wheelDistance(own, technique)];
}

/** A Pattern may only be built from the character's own Shape. */
export function canPattern(own: ShapeId, technique: ShapeId): boolean {
  return wheelDistance(own, technique) === 0;
}

/** Density: the field's output multiplier at a Stage (1–4). */
export function stageOutput(stage: number): number {
  if (stage < 1 || stage > 4) throw new Error(`Stage must be 1–4, got ${stage}`);
  return F.stageOutput[stage - 1];
}

/** How far past the skin the field reaches at a Stage. */
export function stageReach(stage: number): string {
  return F.stageReach[stage];
}

export interface WillState { will: number; state: FieldState }

/** Regenerate Will over dt seconds. Still regenerates nothing; a stance drains. A fainted field recovers at the open rate until faintRecoverAt. */
export function tickWill(s: WillState, dtSeconds: number): WillState {
  let will = s.will;
  let state = s.state;
  if (state === 'still') return s;
  if (state === 'shaped') will -= F.stanceCostPerSecond * dtSeconds;
  else will += F.regenOpen * dtSeconds;
  will = Math.max(0, Math.min(F.willMax, will));
  if (will === 0) state = 'fainted';
  if (state === 'fainted' && will >= F.faintRecoverAt) state = 'open';
  return { will, state };
}

/** Spend Will. Returns null if there is not enough or the field has fainted. */
export function spendWill(s: WillState, cost: number): WillState | null {
  if (s.state === 'fainted' || s.will < cost) return null;
  const will = s.will - cost;
  return { will, state: will === 0 ? 'fainted' : s.state };
}

export function perfectHold(s: WillState): WillState {
  return { will: Math.min(F.willMax, s.will + F.perfectHoldRefund), state: s.state };
}
