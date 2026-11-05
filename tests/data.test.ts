import { it, expect } from 'vitest';
import { validateData } from '../src/data/validate';

it('every data file matches its schema and every id resolves', () => {
  expect(validateData()).toEqual([]);
});
