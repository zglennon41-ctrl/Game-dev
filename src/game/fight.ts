// The pulse combat room's logic, with no rendering. Time is in seconds on the beat clock.
// The renderer and the audio read `events`; tests drive it directly.
import { data, byId, type ShapeId } from '../data';
import roomJson from '../../data/combat-room.json';
import beastsJson from '../../data/beasts.json';
import { judge, beatWindowMs, BreakMeter, type Judgment } from '../rules/combat';
import { opposite } from '../rules/field';

export const room = roomJson;
export interface Beast {
  id: string; name: string; shape: ShapeId; molt: number; health: number; breakWindowBeats: number;
  strikeDamage: number; strikeReach: number; telegraphBeats: number; recoverBeats: number;
  circleBeats: { min: number; max: number }; circleRadius: number; approachSpeed: number; moveSpeed: number; knockback: number;
}
export const beasts = beastsJson as unknown as Beast[];

export type Action = 'strike' | 'ground-strike' | 'hold-down' | 'hold-up' | 'stance';

export type FightEvent =
  | { type: 'judged'; action: Action; j: Judgment; t: number }
  | { type: 'hit'; action: Action; perfect: boolean; damage: number; chain: number; staggered: boolean; t: number }
  | { type: 'whiff'; action: Action; perfect: boolean; t: number }
  | { type: 'fumble'; reason: string; t: number }
  | { type: 'break'; count: number; t: number }
  | { type: 'stagger'; beats: number; t: number }
  | { type: 'windup'; strikeBeat: number; t: number }
  | { type: 'parry'; t: number }
  | { type: 'block'; damage: number; t: number }
  | { type: 'hurt'; damage: number; t: number }
  | { type: 'dodge'; t: number }
  | { type: 'stance'; on: boolean; t: number }
  | { type: 'faint'; t: number }
  | { type: 'no-will'; t: number }
  | { type: 'wolf-down'; t: number }
  | { type: 'wolf-up'; t: number }
  | { type: 'player-down'; t: number }
  | { type: 'beat'; beat: number; t: number };

export type WolfMode = 'circle' | 'approach' | 'windup' | 'recover' | 'stagger' | 'down' | 'idle';

export interface Stats {
  inputs: number; perfect: number; offsets: number[]; hits: number; damageDealt: number; longestChain: number;
  parries: number; blocks: number; hurts: number; dodges: number; staggers: number; wolvesDown: number; fumbles: number;
}

export interface FightOptions {
  beast?: string;
  t0?: number;
  periodS?: number;
  windowMs?: number;
  seed?: number;
  arena?: { w: number; h: number };
  /** The tutorial's wolf: stands, never attacks, until told to. */
  passive?: boolean;
  respawn?: boolean;
}

function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class Fight {
  readonly t0: number;
  readonly period: number;
  readonly windowMs: number;
  readonly arena: { w: number; h: number };
  readonly beast: Beast;
  readonly playerShape: ShapeId = room.player.shape as ShapeId;
  readonly rand: () => number;
  passive: boolean;
  respawn: boolean;
  events: FightEvent[] = [];
  stats: Stats = { inputs: 0, perfect: 0, offsets: [], hits: 0, damageDealt: 0, longestChain: 0, parries: 0, blocks: 0, hurts: 0, dodges: 0, staggers: 0, wolvesDown: 0, fumbles: 0 };

  player = { x: 0, y: 0, hp: room.player.health, will: data.rules.field.willMax, stance: false, guard: false, fainted: false, down: false, chain: 0, lastActionBeat: -999, lastHoldBeat: -999, parryBeat: -999, stancePendingBeat: -1, facing: 0 };
  wolf = { x: 0, y: 0, hp: 0, mode: 'circle' as WolfMode, until: 0, strikeBeat: -1, angle: 0, readyToWindup: false, pendingStrike: -1 };
  breaks = new BreakMeter();
  lastBeat: number;
  now: number;

  constructor(o: FightOptions = {}) {
    this.t0 = o.t0 ?? 0;
    this.period = o.periodS ?? byId(data.shapes, room.player.shape).pulseMs / 1000;
    this.windowMs = o.windowMs ?? beatWindowMs(room.line as 'green');
    this.arena = o.arena ?? { w: 1200, h: 760 };
    this.beast = byId(beasts, o.beast ?? 'cut-wolf', 'beast');
    this.rand = rng(o.seed ?? 7);
    this.passive = !!o.passive;
    this.respawn = o.respawn ?? true;
    this.player.x = this.arena.w * 0.4;
    this.player.y = this.arena.h * 0.55;
    this.spawnWolf(-1);
    this.lastBeat = Math.floor((this.t0 - this.t0) / this.period) - 1;
    this.now = this.t0;
  }

  beatTime(k: number) { return this.t0 + k * this.period; }
  get breaksBeast(): boolean { return opposite(this.playerShape) === this.beast.shape; }
  get halfWindowS() { return this.windowMs / 2000; }

  private emit(e: FightEvent) { this.events.push(e); }
  drain(): FightEvent[] { const e = this.events; this.events = []; return e; }

  spawnWolf(k: number) {
    this.wolf.hp = this.beast.health;
    this.wolf.angle = this.rand() * Math.PI * 2;
    this.wolf.x = this.player.x + Math.cos(this.wolf.angle) * this.beast.circleRadius * 1.4;
    this.wolf.y = this.player.y + Math.sin(this.wolf.angle) * this.beast.circleRadius * 1.4;
    this.clampWolf();
    this.setCircle(k);
    this.wolf.pendingStrike = -1;
    if (k >= 0) this.emit({ type: 'wolf-up', t: this.now });
  }

  private setCircle(k: number) {
    const { min, max } = this.beast.circleBeats;
    this.wolf.mode = this.passive ? 'idle' : 'circle';
    this.wolf.until = k + min + Math.floor(this.rand() * (max - min + 1));
  }

  dist() { return Math.hypot(this.wolf.x - this.player.x, this.wolf.y - this.player.y); }
  private canAct() { return !this.player.down && !this.player.fainted; }

  /** Advance to time t. `move` is the stick direction (-1..1 each axis). */
  update(t: number, move: { x: number; y: number } = { x: 0, y: 0 }) {
    const dt = Math.max(0, Math.min(0.1, t - this.now));
    this.now = t;
    const p = this.player;
    const F = data.rules.field;

    // Will: regen open, drain in stance and while guarding.
    if (!p.down) {
      let dw = 0;
      if (p.stance) dw -= F.stanceCostPerSecond;
      if (p.guard) dw -= room.player.holdDrainPerSecond;
      if (!p.stance && !p.guard) dw += F.regenOpen;
      p.will = Math.max(0, Math.min(F.willMax, p.will + dw * dt));
      if (p.will === 0 && !p.fainted && (p.stance || p.guard)) {
        p.fainted = true;
        p.stance = false;
        p.guard = false;
        this.emit({ type: 'faint', t });
      }
      if (p.fainted && p.will >= F.faintRecoverAt) p.fainted = false;
    }

    // Movement.
    if (!p.down) {
      const len = Math.hypot(move.x, move.y);
      if (len > 0.05) {
        const s = room.player.moveSpeed * (p.stance ? room.player.stanceMoveFactor : 1) * (p.guard ? 0.5 : 1);
        p.x += (move.x / Math.max(1, len)) * s * dt;
        p.y += (move.y / Math.max(1, len)) * s * dt;
        p.x = clamp(p.x, 40, this.arena.w - 40);
        p.y = clamp(p.y, 40, this.arena.h - 40);
      }
      p.facing = Math.atan2(this.wolf.y - p.y, this.wolf.x - p.x);
    }

    this.moveWolf(dt);
    this.separate();

    // Beats crossed.
    const k = Math.floor((t - this.t0) / this.period + 1e-9);
    while (this.lastBeat < k) {
      this.lastBeat++;
      this.onBeat(this.lastBeat);
    }
    // A strike resolves half a window after its beat, so a late parry still counts.
    if (this.wolf.pendingStrike >= 0 && t >= this.beatTime(this.wolf.pendingStrike) + this.halfWindowS) this.resolveStrike(this.wolf.pendingStrike);
  }

  private moveWolf(dt: number) {
    const w = this.wolf;
    const b = this.beast;
    const p = this.player;
    if (w.mode === 'circle') {
      w.angle += (b.moveSpeed / b.circleRadius) * dt;
      const tx = p.x + Math.cos(w.angle) * b.circleRadius;
      const ty = p.y + Math.sin(w.angle) * b.circleRadius;
      this.stepToward(tx, ty, b.moveSpeed * 1.6 * dt);
    } else if (w.mode === 'approach') {
      if (this.dist() > b.strikeReach * 0.75) this.stepToward(p.x, p.y, b.approachSpeed * dt);
      else w.readyToWindup = true;
    } else if (w.mode === 'idle') {
      // The chained yard-wolf drifts to a spot a little in front of the player.
      if (this.dist() > b.strikeReach * 0.8) this.stepToward(p.x + 80, p.y - 20, b.moveSpeed * dt);
    }
    this.clampWolf();
  }

  /** Bodies do not overlap: the wolf is pushed out of the Anchor's space. */
  private separate() {
    const min = room.player.radius + 34;
    const dx = this.wolf.x - this.player.x;
    const dy = this.wolf.y - this.player.y;
    const d = Math.hypot(dx, dy);
    if (d >= min) return;
    const a = d > 1e-6 ? Math.atan2(dy, dx) : 0;
    this.wolf.x = this.player.x + Math.cos(a) * min;
    this.wolf.y = this.player.y + Math.sin(a) * min;
    this.clampWolf();
  }

  private stepToward(x: number, y: number, step: number) {
    const dx = x - this.wolf.x;
    const dy = y - this.wolf.y;
    const d = Math.hypot(dx, dy);
    if (d < 1e-6) return;
    const s = Math.min(step, d);
    this.wolf.x += (dx / d) * s;
    this.wolf.y += (dy / d) * s;
  }

  private clampWolf() {
    this.wolf.x = clamp(this.wolf.x, 40, this.arena.w - 40);
    this.wolf.y = clamp(this.wolf.y, 40, this.arena.h - 40);
  }

  private onBeat(k: number) {
    const t = this.beatTime(k);
    this.emit({ type: 'beat', beat: k, t });
    const p = this.player;
    const w = this.wolf;
    if (p.stancePendingBeat === k && !p.stance && this.canAct()) {
      p.stance = true;
      p.stancePendingBeat = -1;
      this.emit({ type: 'stance', on: true, t });
    }
    switch (w.mode) {
      case 'circle':
        if (k >= w.until) w.mode = 'approach';
        break;
      case 'approach':
        if (w.readyToWindup) {
          w.readyToWindup = false;
          w.mode = 'windup';
          w.strikeBeat = k + this.beast.telegraphBeats;
          this.emit({ type: 'windup', strikeBeat: w.strikeBeat, t });
        }
        break;
      case 'windup':
        if (k === w.strikeBeat) w.pendingStrike = k;
        break;
      case 'recover':
      case 'stagger':
        if (k >= w.until) this.setCircle(k);
        break;
      case 'down':
        if (this.respawn && k >= w.until) this.spawnWolf(k);
        break;
      case 'idle':
        break;
    }
  }

  /** The tutorial asks the yard-wolf to attack now. */
  provoke() {
    if (this.wolf.mode === 'idle' || this.wolf.mode === 'circle') {
      this.wolf.mode = 'approach';
      this.wolf.readyToWindup = false;
    }
  }

  private resolveStrike(k: number) {
    const w = this.wolf;
    const p = this.player;
    const t = this.beatTime(k);
    w.pendingStrike = -1;
    if (w.mode !== 'windup') return;
    w.mode = 'recover';
    w.until = k + this.beast.recoverBeats;
    if (this.passive) w.until = k + this.beast.recoverBeats;
    if (p.down) return;
    if (this.dist() > this.beast.strikeReach) {
      this.stats.dodges++;
      this.emit({ type: 'dodge', t });
      return;
    }
    if (p.parryBeat === k) {
      p.will = Math.min(data.rules.field.willMax, p.will + data.rules.field.perfectHoldRefund);
      w.mode = 'stagger';
      w.until = k + 1 + this.beast.recoverBeats;
      this.stats.parries++;
      this.emit({ type: 'parry', t });
      return;
    }
    let dmg = this.beast.strikeDamage;
    if (p.guard) {
      dmg *= room.player.blockDamageFactor;
      p.will = Math.max(0, p.will - room.player.blockWillCost);
      this.stats.blocks++;
      this.emit({ type: 'block', damage: dmg, t });
    } else {
      this.stats.hurts++;
      this.emit({ type: 'hurt', damage: dmg, t });
      // Knocked back, unless the Anchor is in stance.
      if (!p.stance) {
        const a = Math.atan2(p.y - w.y, p.x - w.x);
        p.x = clamp(p.x + Math.cos(a) * this.beast.knockback, 40, this.arena.w - 40);
        p.y = clamp(p.y + Math.sin(a) * this.beast.knockback, 40, this.arena.h - 40);
      }
    }
    p.chain = 0;
    this.breaks.slip();
    p.hp = Math.max(0, p.hp - dmg);
    if (p.hp === 0) {
      p.down = true;
      p.stance = false;
      p.guard = false;
      this.emit({ type: 'player-down', t });
    }
  }

  /** An input at time t (already corrected for latency). */
  input(action: Action, t: number) {
    const p = this.player;
    if (p.down) return;
    if (action === 'hold-up') { p.guard = false; return; }
    const j = judge(t, this.t0, this.period, this.windowMs);
    this.emit({ type: 'judged', action, j, t });
    this.stats.inputs++;
    this.stats.offsets.push(j.offsetMs);
    if (j.perfect) this.stats.perfect++;

    if (action === 'hold-down') {
      if (p.fainted) { this.emit({ type: 'no-will', t }); return; }
      p.guard = true;
      if (j.perfect && j.beat !== p.lastHoldBeat) p.parryBeat = j.beat;
      p.lastHoldBeat = j.beat;
      return;
    }
    if (action === 'stance') {
      if (p.stance) { p.stance = false; this.emit({ type: 'stance', on: false, t }); return; }
      if (!this.canAct()) { this.emit({ type: 'no-will', t }); return; }
      if (j.perfect) { p.stance = true; this.emit({ type: 'stance', on: true, t }); }
      else p.stancePendingBeat = j.beat + room.stance.offBeatEntryDelayBeats;
      return;
    }

    // Project: one per beat. A second press in the same beat is a fumble.
    if (j.beat <= p.lastActionBeat) {
      p.chain = 0;
      this.breaks.slip();
      this.stats.fumbles++;
      this.emit({ type: 'fumble', reason: j.beat === p.lastActionBeat ? 'twice in one beat' : 'still recovering', t });
      return;
    }
    const a = room.actions[action];
    if (a.will > 0) {
      if (p.fainted || p.will < a.will) { this.emit({ type: 'no-will', t }); return; }
      p.will -= a.will;
    }
    p.lastActionBeat = j.beat + a.recoveryBeats;
    const w = this.wolf;
    const staggered = w.mode === 'stagger';
    const perfect = j.perfect || staggered;
    if (w.mode === 'down' || this.dist() > room.player.reach + 40) {
      if (!perfect) p.chain = 0;
      this.emit({ type: 'whiff', action, perfect, t });
      return;
    }
    if (perfect) p.chain = Math.min(room.chain.maxLinks, p.chain + 1);
    else { p.chain = 0; this.breaks.slip(); }
    this.stats.longestChain = Math.max(this.stats.longestChain, p.chain);
    let dmg = a.damage * (perfect ? 1 : data.rules.combat.offBeatOutput);
    if (p.stance) dmg *= room.stance.damageFactor;
    dmg *= 1 + room.chain.perLink * Math.max(0, p.chain - 1);
    if (staggered) dmg *= room.staggerDamageFactor;
    dmg = Math.round(dmg);
    w.hp = Math.max(0, w.hp - dmg);
    this.stats.hits++;
    this.stats.damageDealt += dmg;
    this.emit({ type: 'hit', action, perfect, damage: dmg, chain: p.chain, staggered, t });

    if ('knockback' in a && a.knockback) {
      const ang = Math.atan2(w.y - p.y, w.x - p.x);
      w.x += Math.cos(ang) * a.knockback;
      w.y += Math.sin(ang) * a.knockback;
      this.clampWolf();
      if (perfect && w.mode === 'windup') { w.mode = 'recover'; w.until = j.beat + this.beast.recoverBeats; w.pendingStrike = -1; }
    }
    // Breaks come from techniques of the Shape opposite the beast's, landed on the beat.
    if (!staggered && j.perfect && 'technique' in a) {
      const opened = this.breaks.hit(this.breaksBeast);
      if (this.breaksBeast) this.emit({ type: 'break', count: opened ? this.breaks.needed : this.breaks.count, t });
      if (opened) {
        w.mode = 'stagger';
        w.until = j.beat + opened + 1;
        w.pendingStrike = -1;
        this.stats.staggers++;
        this.emit({ type: 'stagger', beats: opened, t });
      }
    }
    if (w.hp === 0) {
      w.mode = 'down';
      w.until = j.beat + 4;
      w.pendingStrike = -1;
      this.stats.wolvesDown++;
      this.emit({ type: 'wolf-down', t });
    }
  }
}

function clamp(x: number, a: number, b: number) { return Math.max(a, Math.min(b, x)); }
