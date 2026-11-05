// The guided tutorial: the pulse, then each verb, on a chained yard-wolf. It also calibrates
// timing to the player's screen and speakers.
import type { Fight, FightEvent } from './fight';

export interface TutorialHost {
  fight: Fight;
  setCalibration(ms: number): void;
  calibration(): number;
  showWolf(v: boolean): void;
  done(): void;
}

interface Step {
  title: string;
  text: string;
  enter?(h: TutorialHost): void;
  on(e: FightEvent, h: TutorialHost, s: StepState): boolean;
  progress?(s: StepState): string;
}
interface StepState { n: number; offsets: number[]; note: string }

const median = (xs: number[]) => { const s = [...xs].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : 0; };

const STEPS: Step[] = [
  {
    title: 'Your field beats',
    text: 'Listen. The ring at your feet closes on every beat, and the track below carries the beats to the line. Tap <b>J</b> (or Space) with the click, eight times. This also tunes the game to your screen and speakers.',
    enter: (h) => h.showWolf(false),
    on: (e, h, s) => {
      if (e.type !== 'judged' || e.action !== 'strike') return false;
      s.offsets.push(e.j.offsetMs);
      s.n = s.offsets.length;
      if (s.n < 8) return false;
      const m = median(s.offsets.slice(-8));
      if (Math.abs(m) > 15) {
        h.setCalibration(h.calibration() + m);
        s.note = `You tap ${Math.abs(Math.round(m))} ms ${m > 0 ? 'late' : 'early'} on this device; the beat has been adjusted to you.`;
      } else s.note = 'Your timing sits right on the beat on this device.';
      return true;
    },
    progress: (s) => `${s.n} / 8`,
  },
  {
    title: 'On the beat',
    text: 'Inputs on the beat are <b>perfect</b>. Off it, everything you do is worth 70%. Land four <b>J</b> taps on the beat in a row. The marks under the track show where you landed: green on the beat, orange off it.',
    on: (e, _h, s) => {
      if (e.type !== 'judged' || e.action !== 'strike') return false;
      s.n = e.j.perfect ? s.n + 1 : 0;
      return s.n >= 4;
    },
    progress: (s) => `${s.n} / 4 in a row`,
  },
  {
    title: 'Shape: the stance',
    text: 'Press <b>L</b> on the beat. Your field takes the Anchor\'s Shape: you hit half again as hard, you cannot be knocked back, you move slower, and it drains Will while you hold it. Off the beat, the stance comes a beat late. Press <b>L</b> again to leave it.',
    on: (e) => e.type === 'stance' && e.on,
  },
  {
    title: 'Project: strike',
    text: 'A yard-wolf on a chain. Walk to it (<b>WASD</b> or arrows) and strike with <b>J</b> on the beat. On-beat strikes in a row build a chain that hits harder; one press per beat, because a second press in the same beat fumbles. Build a chain of four.',
    enter: (h) => { h.showWolf(true); h.fight.passive = true; h.fight.wolf.mode = 'idle'; },
    on: (e, _h, s) => {
      if (e.type === 'hit') s.n = Math.max(s.n, e.chain);
      if (e.type === 'fumble' || (e.type === 'hit' && !e.perfect)) s.n = 0;
      return s.n >= 4;
    },
    progress: (s) => `chain ${s.n} / 4`,
  },
  {
    title: 'A technique: Ground Strike',
    text: '<b>I</b> is Ground Strike, an Anchor technique. It costs 18 Will and hits hard. A beast breaks under techniques of the Shape opposite its own, and this wolf is a <b>Read</b>, the Anchor\'s opposite. Three Ground Strikes on the beat in a row break it: the gold pips fill, and it staggers. Wait a beat between strikes.',
    on: (e, _h, s) => {
      if (e.type === 'no-will') s.note = 'Out of Will. Leave the stance (L) and let it fill: open, the field regenerates 4 a second.';
      if (e.type === 'hit' && e.action === 'ground-strike' && !e.perfect) s.note = 'Off the beat: that strike does not break. Land all three on the beat.';
      return e.type === 'stagger';
    },
  },
  {
    title: 'Hold: the parry',
    text: 'Now it will bite. When it winds up, it glows red and a red mark rides the track toward the line. Press <b>K</b> on that beat: a <b>parry</b>. No damage, 10 Will back, and the wolf reels. Holding K early only blocks, for half. Parry it twice.',
    enter: (h) => { h.fight.passive = true; h.fight.wolf.mode = 'idle'; },
    on: (e, h, s) => {
      if (e.type === 'parry') s.n++;
      if (e.type === 'block') s.note = 'Blocked: that was a guard held early. Tap K exactly on the strike beat.';
      if (e.type === 'hurt' || e.type === 'dodge') s.note = 'Watch the red mark on the track; tap K as it crosses the line.';
      if (s.n >= 2) return true;
      void h;
      return false;
    },
    progress: (s) => `${s.n} / 2`,
  },
];

export class Tutorial {
  i = 0;
  state: StepState = { n: 0, offsets: [], note: '' };
  private betweenUntil = 0;
  private lastNote = '';
  constructor(private h: TutorialHost, private ui: { title: HTMLElement; text: HTMLElement; progress: HTMLElement; note: HTMLElement }) {
    this.enter();
  }

  private enter() {
    const s = STEPS[this.i];
    s.enter?.(this.h);
    this.state = { n: 0, offsets: [], note: '' };
    this.ui.title.textContent = `${this.i + 1}/${STEPS.length} · ${s.title}`;
    this.ui.text.innerHTML = s.text;
    this.render();
  }

  private render() {
    const s = STEPS[this.i];
    this.ui.progress.textContent = s.progress?.(this.state) ?? '';
    this.ui.note.textContent = this.state.note || this.lastNote;
  }

  /** Called every frame with the fight's events. */
  update(events: FightEvent[], nowPerf: number) {
    if (this.i >= STEPS.length) return;
    // The parry step keeps provoking the yard-wolf.
    if (STEPS[this.i].title.startsWith('Hold') && (this.h.fight.wolf.mode === 'idle')) this.h.fight.provoke();
    if (nowPerf < this.betweenUntil) return;
    for (const e of events) {
      if (STEPS[this.i].on(e, this.h, this.state)) {
        this.lastNote = this.state.note;
        this.i++;
        if (this.i >= STEPS.length) { this.h.done(); return; }
        this.betweenUntil = nowPerf + 600;
        this.enter();
        return;
      }
    }
    this.render();
  }
}
