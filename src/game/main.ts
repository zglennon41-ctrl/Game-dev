// The pulse combat room (Step 1): a title screen, the tutorial, two minutes with a cut-wolf.
import { Fight, room, type FightEvent } from './fight';
import { Pulse } from './audio';
import { Input } from './input';
import { Renderer } from './render';
import { Tutorial } from './tutorial';
import { beatWindowMs } from '../rules/combat';
import { data, byId } from '../data';

const $ = (id: string) => document.getElementById(id)!;
const store = {
  get(k: string, d: number) { try { const v = localStorage.getItem(`wildline.${k}`); return v === null ? d : Number(v); } catch { return d; } },
  set(k: string, v: number) { try { localStorage.setItem(`wildline.${k}`, String(v)); } catch { /* private window */ } },
};

let pulse: Pulse | null = null;
const input = new Input();
const renderer = new Renderer();
let rendererReady: Promise<void> | null = null;
let fight: Fight | null = null;
let tutorial: Tutorial | null = null;
let mode: 'menu' | 'tutorial' | 'fight' | 'results' = 'menu';
let windowMs = store.get('windowMs', beatWindowMs(room.line as 'green'));
let lastPerf = performance.now();
let fightEnd = 0;

const period = byId(data.shapes, room.player.shape).pulseMs / 1000;

function showScreen(html: string) {
  $('screenbox').innerHTML = html;
  $('screen').style.display = 'flex';
  $('hud').style.display = 'none';
  $('prompt').style.display = 'none';
  $('keys').style.display = 'none';
  input.enabled = false;
  const first = $('screenbox').querySelector('button') as HTMLButtonElement | null;
  first?.focus();
}
function hideScreen() {
  $('screen').style.display = 'none';
  $('hud').style.display = 'flex';
  $('keys').style.display = 'block';
  input.enabled = true;
}

function menu() {
  mode = 'menu';
  pulse?.stop();
  const cal = Math.round(store.get('calibrationMs', 0));
  showScreen(`
    <h1>WILDLINE</h1>
    <h2>The pulse room · an Anchor, a cut-wolf, the beat</h2>
    <button class="primary" id="b-tut">Learn the pulse <small>(tutorial, about three minutes)</small></button><br>
    <button id="b-fight">Fight the cut-wolf <small>(two minutes)</small></button><br>
    <button id="b-win">Beat window: ${windowMs} ms ${windowMs === 200 ? '(Green line)' : '(Amber and up)'}</button>
    <button id="b-cal">Timing calibration: ${cal} ms${cal ? ' · reset' : ''}</button>
    <p><small>Sound on: the beat is in the music. Keyboard or a gamepad. <a href="/sim.html">The rules simulator (Step 0)</a></small></p>`);
  $('b-tut').onclick = () => start('tutorial');
  $('b-fight').onclick = () => start('fight');
  $('b-win').onclick = () => { windowMs = windowMs === 200 ? 150 : 200; store.set('windowMs', windowMs); menu(); };
  $('b-cal').onclick = () => { store.set('calibrationMs', 0); menu(); };
}

async function start(which: 'tutorial' | 'fight') {
  if (!pulse) pulse = new Pulse();
  rendererReady ??= renderer.init($('stage'));
  await rendererReady;
  pulse.calibrationMs = store.get('calibrationMs', 0);
  await pulse.start(period, 1.6);
  fight = new Fight({ beast: which === 'tutorial' ? 'yard-wolf' : 'cut-wolf', t0: pulse.t0, periodS: period, windowMs, seed: Math.floor(Math.random() * 1e9), passive: which === 'tutorial', respawn: true });
  renderer.showWolf = true;
  hideScreen();
  if (which === 'tutorial') {
    mode = 'tutorial';
    $('prompt').style.display = 'block';
    const host = {
      fight,
      setCalibration: (ms: number) => { const v = Math.max(-200, Math.min(200, ms)); pulse!.calibrationMs = v; store.set('calibrationMs', v); },
      calibration: () => pulse!.calibrationMs,
      showWolf: (v: boolean) => { renderer.showWolf = v; },
      done: () => tutorialDone(),
    };
    tutorial = new Tutorial(host, { title: $('ptitle'), text: $('ptext'), progress: $('pprog'), note: $('pnote') });
  } else {
    mode = 'fight';
    tutorial = null;
    fightEnd = pulse.t0 + room.sessionSeconds;
  }
}

function tutorialDone() {
  pulse?.done();
  const note = $('pnote').textContent;
  mode = 'results';
  showScreen(`
    <h1>THE PULSE</h1>
    <h2>That is the whole of it: the beat, the stance, the strike, the technique that breaks, the parry.</h2>
    <p>${note ? `${note}<br><br>` : ''}A cut-wolf is coming out of the Cut. It circles, it commits, it bites on the beat. It does not stand still for you.</p>
    <button class="primary" id="b-fight">Fight it (two minutes)</button>
    <button id="b-again">The tutorial again</button>
    <button id="b-menu">Menu</button>`);
  $('b-fight').onclick = () => start('fight');
  $('b-again').onclick = () => start('tutorial');
  $('b-menu').onclick = menu;
}

function results(reason: 'time' | 'down') {
  if (!fight) return;
  pulse?.stop();
  pulse?.done();
  mode = 'results';
  const s = fight.stats;
  const pct = s.inputs ? Math.round((100 * s.perfect) / s.inputs) : 0;
  const avg = s.offsets.length ? s.offsets.reduce((a, b) => a + b, 0) / s.offsets.length : 0;
  showScreen(`
    <h1>${reason === 'down' ? 'DOWN' : 'TWO MINUTES'}</h1>
    <h2>${reason === 'down' ? 'The wolf put you on the ties. On the line, the party would have sixty seconds to stand on you.' : `${s.wolvesDown} cut-wolf${s.wolvesDown === 1 ? '' : 's'} felled.`}</h2>
    <table>
      <tr><td>On the beat</td><td>${pct}% of ${s.inputs} inputs</td></tr>
      <tr><td>Your timing</td><td>${Math.abs(Math.round(avg))} ms ${avg >= 0 ? 'late' : 'early'} on average</td></tr>
      <tr><td>Parries / blocks / bitten / dodged</td><td>${s.parries} / ${s.blocks} / ${s.hurts} / ${s.dodges}</td></tr>
      <tr><td>Breaks into stagger</td><td>${s.staggers}</td></tr>
      <tr><td>Longest chain</td><td>${s.longestChain}</td></tr>
      <tr><td>Damage dealt</td><td>${s.damageDealt}</td></tr>
      <tr><td>Fumbles</td><td>${s.fumbles}</td></tr>
      <tr><td>Health left</td><td>${Math.round(fight.player.hp)}</td></tr>
    </table>
    <button class="primary" id="b-again">Again</button>
    <button id="b-tut">Tutorial</button>
    <button id="b-menu">Menu</button>`);
  $('b-again').onclick = () => start('fight');
  $('b-tut').onclick = () => start('tutorial');
  $('b-menu').onclick = menu;
}

function sounds(events: FightEvent[]) {
  if (!pulse) return;
  for (const e of events) {
    switch (e.type) {
      case 'hit': if (e.action === 'ground-strike') pulse.heavy(); if (e.perfect) pulse.hitPerfect(e.chain); else pulse.hitOff(); break;
      case 'whiff': pulse.whiff(); break;
      case 'fumble': pulse.fumble(); break;
      case 'parry': pulse.parry(); break;
      case 'block': pulse.block(); break;
      case 'hurt': pulse.hurt(); break;
      case 'windup': pulse.growl(); break;
      case 'stagger': pulse.stagger(); break;
      case 'stance': pulse.stance(e.on); break;
      case 'wolf-down': pulse.fell(); break;
    }
  }
}

function hud() {
  if (!fight || !pulse) return;
  const p = fight.player;
  $('hp').style.width = `${(p.hp / room.player.health) * 100}%`;
  $('hpv').textContent = `${Math.round(p.hp)}`;
  $('will').style.width = `${p.will}%`;
  $('willv').textContent = `${Math.round(p.will)}`;
  $('state').textContent = p.fainted ? '· FAINTED' : p.stance ? '· ANCHOR STANCE (−2/s)' : p.guard ? '· HOLDING (−3/s)' : '';
  $('chain').textContent = p.chain > 1 ? `Chain ×${p.chain}` : '';
  if (mode === 'fight') {
    const left = Math.max(0, fightEnd - pulse.now());
    $('timer').textContent = `${Math.floor(left / 60)}:${String(Math.floor(left % 60)).padStart(2, '0')}`;
    $('score').textContent = `wolves felled: ${fight.stats.wolvesDown}`;
  } else {
    $('timer').textContent = '';
    $('score').textContent = 'the yard';
  }
}

function frame() {
  const nowPerf = performance.now();
  const dt = Math.min(0.1, (nowPerf - lastPerf) / 1000);
  lastPerf = nowPerf;
  if (!fight || !pulse || (mode !== 'tutorial' && mode !== 'fight')) return;
  const { inputs, move } = input.poll();
  for (const i of inputs) fight.input(i.action, pulse.inputTime(i.perfMs));
  const t = pulse.now();
  fight.update(t, move);
  const events = fight.drain();
  sounds(events);
  renderer.feedback(events, nowPerf);
  tutorial?.update(events, nowPerf);
  renderer.draw(fight, t, nowPerf, dt);
  hud();
  if (mode === 'fight') {
    if (fight.player.down) results('down');
    else if (t >= fightEnd) results('time');
  }
}

window.addEventListener('keydown', (e) => { if (e.code === 'Escape' && (mode === 'fight' || mode === 'tutorial')) menu(); });
(async () => {
  rendererReady = renderer.init($('stage'));
  await rendererReady;
  renderer.app.ticker.add(frame);
  menu();
})();
// For automated checks.
(window as unknown as { __wildline: unknown }).__wildline = { get fight() { return fight; }, get pulse() { return pulse; }, get mode() { return mode; }, get tutorial() { return tutorial; } };
