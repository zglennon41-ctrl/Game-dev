// npm run sim -- --life data/lives/mira.json [--log]
// With no --life, runs all three lives in data/lives/.
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { simulate } from './simulate';
import { report } from './report';
import type { Life } from './script';

const args = process.argv.slice(2);
const lifeIdx = args.indexOf('--life');
const files = lifeIdx >= 0 ? [args[lifeIdx + 1]] : readdirSync('data/lives').filter((f) => f.endsWith('.json')).map((f) => join('data/lives', f));
for (const f of files) {
  const life = JSON.parse(readFileSync(f, 'utf8')) as Life;
  console.log(report(simulate(life), { log: args.includes('--log') }));
  console.log();
}
