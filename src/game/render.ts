// Placeholder art, real feel: shapes with tags, a beat ring, a beat track, hit feedback.
import { Application, Container, Graphics, Text } from 'pixi.js';
import type { Fight, FightEvent } from './fight';

const W = 1200;
const ARENA_H = 760;
const TRACK_H = 120;
const H = ARENA_H + TRACK_H;

const COLORS = {
  floor: 0x1b1714, rail: 0x2c2620, tie: 0x231e19, player: 0x8a6f4e, playerEdge: 0xd9c3a0, stance: 0xd9a441,
  wolf: 0x6c7a89, wolfEdge: 0xc6d2de, windup: 0xd9483b, stagger: 0xf2d16b, perfect: 0x9fe08a, off: 0xe0975a,
  ring: 0xe8dcc8, text: 0xe8dcc8, dim: 0x9a8c78, guard: 0x9fc6e8,
};

interface Floater { t: Text; born: number; life: number; vy: number }
interface Spark { g: Graphics; born: number; life: number; vx: number; vy: number }
interface Mark { t: number; perfect: boolean }

export class Renderer {
  app = new Application();
  private root = new Container();
  private world = new Container();
  private floor = new Graphics();
  private ring = new Graphics();
  private player = new Graphics();
  private wolf = new Graphics();
  private fx = new Container();
  private track = new Graphics();
  private trackLabels = new Container();
  private playerLabel = new Text({ text: 'ANCHOR', style: { fill: COLORS.text, fontSize: 12, fontFamily: 'Georgia', letterSpacing: 2 } });
  private wolfLabel = new Text({ text: '', style: { fill: COLORS.dim, fontSize: 12, fontFamily: 'Georgia', letterSpacing: 1 } });
  private strikeText = new Text({ text: 'STRIKE', style: { fill: COLORS.windup, fontSize: 12, fontFamily: 'Georgia', fontWeight: 'bold' } });
  private floaters: Floater[] = [];
  private sparks: Spark[] = [];
  private marks: Mark[] = [];
  private shake = 0;
  private flash = 0;
  private hitstopUntil = 0;
  private frozen: { px: number; py: number; wx: number; wy: number } | null = null;
  showWolf = true;
  showTrack = true;

  async init(parent: HTMLElement) {
    await this.app.init({ background: 0x14110f, antialias: true, resizeTo: parent, autoDensity: true, resolution: Math.min(2, window.devicePixelRatio || 1) });
    parent.appendChild(this.app.canvas);
    this.app.stage.addChild(this.root);
    this.root.addChild(this.world, this.track, this.trackLabels);
    this.world.addChild(this.floor, this.ring, this.wolf, this.player, this.playerLabel, this.wolfLabel, this.fx);
    this.trackLabels.addChild(this.strikeText);
    this.playerLabel.anchor.set(0.5, 0);
    this.wolfLabel.anchor.set(0.5, 1);
    this.strikeText.anchor.set(0.5, 1);
    this.playerLabel.visible = this.wolfLabel.visible = this.strikeText.visible = false;
    this.drawFloor();
    this.layout();
    window.addEventListener('resize', () => this.layout());
  }

  private layout() {
    const s = Math.min(this.app.screen.width / W, this.app.screen.height / H);
    this.root.scale.set(s);
    this.root.x = (this.app.screen.width - W * s) / 2;
    this.root.y = (this.app.screen.height - H * s) / 2;
    this.track.y = ARENA_H;
    this.trackLabels.y = ARENA_H;
  }

  private drawFloor() {
    const g = this.floor;
    g.rect(0, 0, W, ARENA_H).fill(COLORS.floor);
    // The Cut: rail ties and two rails, a tunnel floor.
    for (let x = 20; x < W; x += 46) g.rect(x, ARENA_H * 0.5 - 70, 18, 140).fill(COLORS.tie);
    g.rect(0, ARENA_H * 0.5 - 52, W, 6).fill(COLORS.rail);
    g.rect(0, ARENA_H * 0.5 + 46, W, 6).fill(COLORS.rail);
    g.rect(0, 0, W, 30).fill(0x0f0c0a);
    g.rect(0, ARENA_H - 30, W, 30).fill(0x0f0c0a);
  }

  /** React to the fight's events with feedback. */
  feedback(events: FightEvent[], nowPerf: number) {
    for (const e of events) {
      switch (e.type) {
        case 'beat': this.flash = 1; break;
        case 'judged':
          if (e.action !== 'hold-up') this.marks.push({ t: e.t, perfect: e.j.perfect });
          if (!e.j.perfect && e.action !== 'stance') this.float(this.lastP.x, this.lastP.y - 70, `${e.j.offsetMs < 0 ? 'early' : 'late'} ${Math.abs(Math.round(e.j.offsetMs))} ms`, COLORS.off, 15, nowPerf);
          break;
        case 'hit':
          this.float(this.lastW.x + rand(-10, 10), this.lastW.y - 50, `${e.damage}`, e.perfect ? COLORS.perfect : COLORS.off, e.perfect ? 30 : 20, nowPerf);
          if (e.perfect) this.float(this.lastW.x, this.lastW.y - 86, e.staggered ? 'STAGGERED' : e.chain > 1 ? `PERFECT ×${e.chain}` : 'PERFECT', COLORS.perfect, 16, nowPerf);
          this.burst(this.lastW.x, this.lastW.y, e.perfect ? COLORS.perfect : COLORS.off, e.perfect ? 14 : 6, nowPerf);
          this.shake = Math.max(this.shake, e.perfect ? 7 : 3);
          if (e.perfect) this.hitstop(nowPerf, e.action === 'ground-strike' ? 110 : 70);
          break;
        case 'whiff': this.float(this.lastP.x, this.lastP.y - 50, 'out of reach', COLORS.dim, 13, nowPerf); break;
        case 'fumble': this.float(this.lastP.x, this.lastP.y - 50, `fumble — ${e.reason}`, COLORS.off, 14, nowPerf); break;
        case 'break': this.float(this.lastW.x, this.lastW.y + 50, `break ${e.count}/3`, COLORS.stagger, 15, nowPerf); break;
        case 'stagger': this.float(this.lastW.x, this.lastW.y - 120, 'BROKEN — STAGGER', COLORS.stagger, 24, nowPerf); this.shake = 14; this.hitstop(nowPerf, 160); break;
        case 'parry':
          this.float(this.lastP.x, this.lastP.y - 80, 'PARRY  +10 Will', COLORS.guard, 24, nowPerf);
          this.burst((this.lastP.x + this.lastW.x) / 2, (this.lastP.y + this.lastW.y) / 2, COLORS.guard, 20, nowPerf);
          this.hitstop(nowPerf, 120);
          this.shake = 8;
          break;
        case 'block': this.float(this.lastP.x, this.lastP.y - 70, `blocked −${e.damage}`, COLORS.guard, 16, nowPerf); this.shake = 6; break;
        case 'hurt': this.float(this.lastP.x, this.lastP.y - 70, `−${e.damage}`, COLORS.windup, 26, nowPerf); this.shake = 14; break;
        case 'dodge': this.float(this.lastP.x, this.lastP.y - 70, 'dodged', COLORS.dim, 15, nowPerf); break;
        case 'stance': this.float(this.lastP.x, this.lastP.y + 50, e.on ? 'ANCHOR STANCE' : 'stance off', COLORS.stance, 15, nowPerf); break;
        case 'faint': this.float(this.lastP.x, this.lastP.y - 70, 'FIELD FAINTS — no Will', COLORS.windup, 18, nowPerf); break;
        case 'no-will': this.float(this.lastP.x, this.lastP.y - 50, 'not enough Will', COLORS.off, 14, nowPerf); break;
        case 'wolf-down': this.float(this.lastW.x, this.lastW.y - 60, 'THE WOLF FALLS', COLORS.text, 26, nowPerf); this.shake = 12; break;
        case 'wolf-up': this.float(this.lastW.x, this.lastW.y - 60, 'another comes out of the dark', COLORS.dim, 15, nowPerf); break;
      }
    }
  }

  private lastP = { x: 0, y: 0 };
  private lastW = { x: 0, y: 0 };

  private hitstop(nowPerf: number, ms: number) { this.hitstopUntil = Math.max(this.hitstopUntil, nowPerf + ms); }

  private float(x: number, y: number, text: string, color: number, size: number, nowPerf: number) {
    const t = new Text({ text, style: { fill: color, fontSize: size, fontFamily: 'Georgia', fontWeight: 'bold', stroke: { color: 0x000000, width: 3 } } });
    t.anchor.set(0.5);
    t.x = x;
    t.y = y;
    this.fx.addChild(t);
    this.floaters.push({ t, born: nowPerf, life: 900, vy: -40 });
  }

  private burst(x: number, y: number, color: number, n: number, nowPerf: number) {
    for (let i = 0; i < n; i++) {
      const g = new Graphics().circle(0, 0, rand(2, 4)).fill(color);
      g.x = x; g.y = y;
      const a = rand(0, Math.PI * 2), s = rand(120, 420);
      this.fx.addChild(g);
      this.sparks.push({ g, born: nowPerf, life: rand(250, 500), vx: Math.cos(a) * s, vy: Math.sin(a) * s });
    }
  }

  /** Draw a frame. `t` is the beat clock as heard; `nowPerf` is performance.now(). */
  draw(f: Fight, t: number, nowPerf: number, dtS: number) {
    const stopped = nowPerf < this.hitstopUntil;
    if (stopped && !this.frozen) this.frozen = { px: f.player.x, py: f.player.y, wx: f.wolf.x, wy: f.wolf.y };
    if (!stopped) this.frozen = null;
    const P = this.frozen ? { x: this.frozen.px, y: this.frozen.py } : f.player;
    const Wf = this.frozen ? { x: this.frozen.wx, y: this.frozen.wy } : f.wolf;
    this.lastP = { x: P.x, y: P.y };
    this.lastW = { x: Wf.x, y: Wf.y };

    // Screen shake.
    this.shake *= Math.pow(0.001, dtS);
    this.world.x = rand(-1, 1) * this.shake;
    this.world.y = rand(-1, 1) * this.shake;
    this.flash *= Math.pow(0.0005, dtS);

    // Beat phase: 0 on the beat, rising to 1 just before the next.
    const ph = (((t - f.t0) / f.period) % 1 + 1) % 1;
    const beforeStart = t < f.t0;

    // The pulse ring at the Anchor's feet: the outer ring closes on the base ring at the beat.
    const r0 = 44;
    const ring = this.ring;
    ring.clear();
    const ringColor = f.player.stance ? COLORS.stance : COLORS.ring;
    // The window: a band around the base ring.
    const winFrac = f.windowMs / 1000 / f.period;
    ring.circle(P.x, P.y, r0).stroke({ width: 3 + winFrac * 40, color: ringColor, alpha: 0.12 });
    ring.circle(P.x, P.y, r0).stroke({ width: 3, color: ringColor, alpha: 0.5 + 0.5 * this.flash });
    if (!beforeStart || ph > 0.0) {
      const closing = r0 + 90 * (1 - ph);
      ring.circle(P.x, P.y, closing).stroke({ width: 2, color: ringColor, alpha: 0.25 + 0.6 * ph });
    }
    if (this.flash > 0.05) ring.circle(P.x, P.y, r0 + 6 + 30 * (1 - this.flash)).stroke({ width: 4, color: ringColor, alpha: this.flash * 0.7 });

    // The Anchor: broad, low, a guard arc when Holding.
    const pl = this.player;
    pl.clear();
    if (f.player.stance) pl.circle(P.x, P.y, 34).fill({ color: COLORS.stance, alpha: 0.18 });
    pl.circle(P.x, P.y, 26).fill(f.player.down ? 0x3a2f24 : COLORS.player).stroke({ width: 3, color: COLORS.playerEdge });
    const fa = f.player.facing;
    pl.moveTo(P.x + Math.cos(fa) * 18, P.y + Math.sin(fa) * 18).lineTo(P.x + Math.cos(fa) * 36, P.y + Math.sin(fa) * 36).stroke({ width: 4, color: COLORS.playerEdge });
    if (f.player.guard) pl.arc(P.x, P.y, 40, fa - 1.1, fa + 1.1).stroke({ width: 6, color: COLORS.guard, alpha: 0.9 });
    this.playerLabel.visible = true;
    this.playerLabel.x = P.x;
    this.playerLabel.y = P.y + 30;
    this.playerLabel.text = f.player.down ? 'DOWN' : f.player.fainted ? 'ANCHOR · fainted' : 'ANCHOR';

    // The wolf: a pointed body facing the Anchor; red as it winds up; gold when broken.
    const w = this.wolf;
    w.clear();
    this.wolfLabel.visible = this.showWolf;
    if (this.showWolf) {
      const mode = f.wolf.mode;
      const a = Math.atan2(P.y - Wf.y, P.x - Wf.x);
      let body = COLORS.wolf;
      let glow = 0;
      if (mode === 'windup') {
        const beatsLeft = f.wolf.strikeBeat - (t - f.t0) / f.period;
        glow = Math.max(0, Math.min(1, 1 - beatsLeft / f.beast.telegraphBeats));
        body = lerpColor(COLORS.wolf, COLORS.windup, 0.3 + 0.7 * glow);
        w.circle(Wf.x, Wf.y, 34 + 16 * glow).fill({ color: COLORS.windup, alpha: 0.15 + 0.25 * glow });
        // Reach: where the strike lands.
        w.circle(Wf.x, Wf.y, f.beast.strikeReach).stroke({ width: 2, color: COLORS.windup, alpha: 0.15 + 0.35 * glow });
      }
      if (mode === 'stagger') body = COLORS.stagger;
      const alpha = mode === 'down' ? 0.25 : 1;
      const pts = [0, -18, 0, 18].length;
      void pts;
      const tip = { x: Wf.x + Math.cos(a) * 36, y: Wf.y + Math.sin(a) * 36 };
      const l = { x: Wf.x + Math.cos(a + 2.5) * 26, y: Wf.y + Math.sin(a + 2.5) * 26 };
      const r = { x: Wf.x + Math.cos(a - 2.5) * 26, y: Wf.y + Math.sin(a - 2.5) * 26 };
      const tail = { x: Wf.x - Math.cos(a) * 34, y: Wf.y - Math.sin(a) * 34 };
      w.poly([tip.x, tip.y, l.x, l.y, tail.x, tail.y, r.x, r.y]).fill({ color: body, alpha }).stroke({ width: 2, color: COLORS.wolfEdge, alpha });
      // Health and break pips.
      if (mode !== 'down') {
        const hp = f.wolf.hp / f.beast.health;
        w.rect(Wf.x - 40, Wf.y - 56, 80, 6).fill(0x000000);
        w.rect(Wf.x - 40, Wf.y - 56, 80 * hp, 6).fill(COLORS.windup);
        for (let i = 0; i < f.breaks.needed; i++) {
          w.circle(Wf.x - 16 + i * 16, Wf.y + 44, 5).fill({ color: i < f.breaks.count ? COLORS.stagger : 0x000000, alpha: 0.9 }).stroke({ width: 1, color: COLORS.stagger });
        }
      }
      this.wolfLabel.text = `${f.beast.name.toUpperCase()} · ${cap(f.beast.shape)} · first molt${mode === 'stagger' ? ' · STAGGERED' : mode === 'windup' ? ' · winding up' : ''}`;
      this.wolfLabel.x = Wf.x;
      this.wolfLabel.y = Wf.y - 62;
    }

    // Floaters and sparks.
    for (const fl of [...this.floaters]) {
      const age = nowPerf - fl.born;
      fl.t.y += fl.vy * dtS;
      fl.t.alpha = 1 - age / fl.life;
      if (age > fl.life) { fl.t.destroy(); this.floaters.splice(this.floaters.indexOf(fl), 1); }
    }
    for (const s of [...this.sparks]) {
      const age = nowPerf - s.born;
      if (!stopped) { s.g.x += s.vx * dtS; s.g.y += s.vy * dtS; s.vx *= 0.9; s.vy *= 0.9; }
      s.g.alpha = 1 - age / s.life;
      if (age > s.life) { s.g.destroy(); this.sparks.splice(this.sparks.indexOf(s), 1); }
    }

    this.drawTrack(f, t);
  }

  /** The beat track: beats ride in from the right to the line. A strike is marked red. */
  private drawTrack(f: Fight, t: number) {
    const g = this.track;
    g.clear();
    this.strikeText.visible = false;
    if (!this.showTrack) return;
    g.rect(0, 0, W, TRACK_H).fill(0x0f0c0a);
    const lineX = 180;
    const pxPerBeat = 130;
    const y = TRACK_H / 2;
    const toX = (bt: number) => lineX + ((bt - t) / f.period) * pxPerBeat;
    // Window band at the line.
    const half = (f.windowMs / 2000 / f.period) * pxPerBeat;
    g.rect(lineX - half, 14, half * 2, TRACK_H - 28).fill({ color: COLORS.ring, alpha: 0.08 });
    g.rect(lineX - 1.5, 10, 3, TRACK_H - 20).fill({ color: COLORS.ring, alpha: 0.8 });
    const kNow = Math.floor((t - f.t0) / f.period);
    for (let k = kNow - 2; k <= kNow + 9; k++) {
      if (k < 0) continue;
      const x = toX(f.beatTime(k));
      if (x < 0 || x > W) continue;
      const downbeat = k % 4 === 0;
      g.circle(x, y, downbeat ? 9 : 6).fill({ color: COLORS.ring, alpha: x < lineX ? 0.2 : 0.75 });
    }
    // The wolf's strike.
    if (this.showWolf && f.wolf.mode === 'windup') {
      const x = toX(f.beatTime(f.wolf.strikeBeat));
      g.poly([x, y - 22, x + 16, y, x, y + 22, x - 16, y]).fill({ color: COLORS.windup, alpha: 0.85 });
      this.strikeText.visible = true;
      this.strikeText.x = x;
      this.strikeText.y = y - 26;
      this.strikeText.text = 'STRIKE — Hold (K)';
    }
    // The player's inputs.
    this.marks = this.marks.filter((m) => t - m.t < f.period * 3);
    for (const m of this.marks) {
      const x = toX(m.t);
      g.rect(x - 2, y + 18, 4, 22).fill({ color: m.perfect ? COLORS.perfect : COLORS.off });
    }
  }
}

function rand(a: number, b: number) { return a + Math.random() * (b - a); }
function cap(s: string) { return s[0].toUpperCase() + s.slice(1); }
function lerpColor(a: number, b: number, t: number) {
  const ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
  const br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;
  return (Math.round(ar + (br - ar) * t) << 16) | (Math.round(ag + (bg - ag) * t) << 8) | Math.round(ab + (bb - ab) * t);
}
