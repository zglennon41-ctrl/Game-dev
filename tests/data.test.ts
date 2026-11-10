import { it, expect } from 'vitest';
import { validateData } from '../src/data/validate';

it('every data file matches its schema and every id resolves', () => {
  // The bases of the genius tree are held to their own page by `npm run validate` (and
  // tools/genius-base-check.py): what a base says is the designer's, and is being written.
  // Everything else must be whole here.
  expect(validateData().filter((p) => !p.file.startsWith('genius-bases/'))).toEqual([]);
});
