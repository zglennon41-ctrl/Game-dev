// Keyboard and gamepad. Inputs carry their own timestamps so the beat is judged on when the
// key went down, not when the frame noticed.
import type { Action } from './fight';

export interface TimedInput { action: Action; perfMs: number }

const KEYS: Record<string, Action> = {
  KeyJ: 'strike', Space: 'strike', Enter: 'strike',
  KeyI: 'ground-strike', KeyU: 'ground-strike',
  KeyK: 'hold-down', ShiftLeft: 'hold-down', ShiftRight: 'hold-down',
  KeyL: 'stance', KeyE: 'stance',
};
const MOVE: Record<string, [number, number]> = {
  KeyW: [0, -1], ArrowUp: [0, -1], KeyS: [0, 1], ArrowDown: [0, 1],
  KeyA: [-1, 0], ArrowLeft: [-1, 0], KeyD: [1, 0], ArrowRight: [1, 0],
};
// Standard gamepad: A strike, X Ground Strike, B / RB Hold, Y stance.
const PAD: Record<number, Action> = { 0: 'strike', 2: 'ground-strike', 1: 'hold-down', 5: 'hold-down', 3: 'stance' };

export class Input {
  private queue: TimedInput[] = [];
  private down = new Set<string>();
  private padPrev: boolean[] = [];
  enabled = true;

  constructor() {
    window.addEventListener('keydown', (e) => {
      if (!this.enabled) return;
      if (KEYS[e.code] || MOVE[e.code]) e.preventDefault();
      if (e.repeat) return;
      this.down.add(e.code);
      const a = KEYS[e.code];
      if (a) this.queue.push({ action: a, perfMs: e.timeStamp });
    });
    window.addEventListener('keyup', (e) => {
      this.down.delete(e.code);
      if (KEYS[e.code] === 'hold-down' && !this.holdKeyDown()) this.queue.push({ action: 'hold-up', perfMs: e.timeStamp });
    });
    window.addEventListener('blur', () => this.down.clear());
  }

  private holdKeyDown() { return [...this.down].some((c) => KEYS[c] === 'hold-down'); }

  poll(): { inputs: TimedInput[]; move: { x: number; y: number } } {
    let x = 0, y = 0;
    for (const c of this.down) { const m = MOVE[c]; if (m) { x += m[0]; y += m[1]; } }
    const pads = navigator.getGamepads?.() ?? [];
    const pad = pads.find((p) => p && p.connected);
    if (pad) {
      const now = performance.now();
      const [ax, ay] = [pad.axes[0] ?? 0, pad.axes[1] ?? 0];
      if (Math.hypot(ax, ay) > 0.25) { x += ax; y += ay; }
      pad.buttons.forEach((b, i) => {
        const was = this.padPrev[i] ?? false;
        const a = PAD[i];
        if (a && b.pressed && !was) this.queue.push({ action: a, perfMs: now });
        if (a === 'hold-down' && !b.pressed && was) this.queue.push({ action: 'hold-up', perfMs: now });
        this.padPrev[i] = b.pressed;
      });
    }
    const inputs = this.queue;
    this.queue = [];
    return { inputs: this.enabled ? inputs : [], move: { x, y } };
  }
}
