// The rules simulator page (Step 0): run the three scripted lives in the browser.
import { simulate } from '../sim/simulate';
import { report } from '../sim/report';
import type { Life } from '../sim/script';
import mira from '../../data/lives/mira.json';
import tobiah from '../../data/lives/tobiah.json';
import sable from '../../data/lives/sable.json';

const lives = [mira, tobiah, sable] as unknown as Life[];
const nav = document.getElementById('lives')!;
const out = document.getElementById('out')!;

function show(i: number) {
  try {
    out.textContent = report(simulate(lives[i]), { log: true });
  } catch (e) {
    out.textContent = `The rules could not run this life:\n${(e as Error).message}`;
  }
  nav.querySelectorAll('button').forEach((b, j) => b.classList.toggle('on', i === j));
}

lives.forEach((l, i) => {
  const b = document.createElement('button');
  b.textContent = l.name;
  b.onclick = () => show(i);
  nav.appendChild(b);
});
show(0);
