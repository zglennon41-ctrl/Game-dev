import { defineConfig, configDefaults } from 'vitest/config';

// The rules' tests are in tests/. Working copies under .claude/ are other checkouts of this
// repository and are not this one's tests.
export default defineConfig({
  test: { exclude: [...configDefaults.exclude, '.claude/**', 'build/**'] },
});
