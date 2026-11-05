import { validateData } from './validate';

const problems = validateData();
if (problems.length) {
  for (const p of problems) console.log(`✗ data/${p.file}: ${p.message}`);
  console.log(`\n${problems.length} problem(s).`);
  process.exit(1);
}
console.log('✓ every file in data/ matches its schema and every id refers to something that exists.');
