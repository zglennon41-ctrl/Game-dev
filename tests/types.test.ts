// The three types of genius (docs/genius-types.md): data/genius-types.json is held to the bases.
import { describe, it, expect } from 'vitest';
import { cpSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { validateData } from '../src/data/validate';

const read = (f: string) => JSON.parse(readFileSync(f, 'utf8'));

/** A copy of data/ with genius-types.json changed, validated. */
function withTypes(change: (t: any) => void) {
  const dir = mkdtempSync(join(tmpdir(), 'wildline-types-'));
  cpSync('data', dir, { recursive: true });
  const t = read(join(dir, 'genius-types.json'));
  change(t);
  writeFileSync(join(dir, 'genius-types.json'), JSON.stringify(t));
  return validateData(dir).filter((p) => p.file === 'genius-types.json').map((p) => p.message).join('\n');
}

describe('the three types of genius, as data', () => {
  const T = read('data/genius-types.json');
  const bases = ['wolf', 'hawk', 'stag', 'tortoise', 'fox', 'imp', 'lurker', 'fiend', 'drake', 'sprite', 'homunculus', 'ember', 'fog', 'lantern', 'astrolabe', 'bell', 'blade', 'gun', 'bow', 'shield', 'gauntlet', 'coat', 'moth', 'octopus', 'carp']
    .map((id) => read(`data/genius-bases/${id}.json`));

  it('gives every class of base one type', () => {
    const typeOf = (cls: string) => Object.entries<any>(T.types).filter(([k, t]) => !k.startsWith('$') && t.classes.includes(cls)).map(([k]) => k);
    for (const b of bases) expect(typeOf(b.class), `${b.id} (${b.class})`).toHaveLength(1);
  });

  it('writes what every base does, and what each of its three paths changes', () => {
    for (const b of bases) {
      const entry = T.weapon.bases[b.id] ?? T.items[b.id] ?? T.companions[b.id];
      expect(entry, b.id).toBeTruthy();
      expect(Object.keys(entry.paths).sort(), b.id).toEqual(b.paths.map((p: any) => p.id).sort());
    }
  });

  it('gives every role a companion, and every companion a path that keeps to its role', () => {
    const roles = new Set<string>();
    for (const [id, c] of Object.entries<any>(T.companions)) {
      if (id.startsWith('$')) continue;
      roles.add(c.role);
      expect(Object.values<any>(c.paths).some((p) => p.shade === c.role), `${id} has no path that keeps to ${c.role}`).toBe(true);
    }
    expect([...roles].sort()).toEqual(['bulwark', 'harrier', 'hunter', 'keeper', 'lookout']);
  });

  it('gives every item something always true and one thing done with the key, each a different thing', () => {
    const effects = new Set<string>();
    for (const [id, it] of Object.entries<any>(T.items)) {
      if (id.startsWith('$')) continue;
      expect(it.always.text.length, id).toBeGreaterThan(10);
      effects.add(it.use.effect);
    }
    expect(effects.size).toBe(Object.keys(T.items).filter((k) => !k.startsWith('$')).length);
  });

  it('a genius has more of its function at every age', () => {
    const ages = ['young', 'half-grown', 'grown', 'prime', 'great', 'apex'];
    for (let i = 1; i < ages.length; i++) {
      expect(T.ages[ages[i]].worth).toBeGreaterThanOrEqual(T.ages[ages[i - 1]].worth);
      expect(T.weapon.inHand[ages[i]]).toBeGreaterThan(T.weapon.inHand[ages[i - 1]]);
      expect(T.ages[ages[i]].wait).toBeLessThanOrEqual(T.ages[ages[i - 1]].wait);
    }
  });

  it('is checked against the bases: a base with nothing written, a path misnamed, a base that is not there', () => {
    expect(validateData().filter((p) => p.file === 'genius-types.json')).toEqual([]);
    expect(withTypes((t) => { delete t.companions.wolf; })).toMatch(/wolf is a companion/);
    expect(withTypes((t) => { t.weapon.bases.blade.paths['blade-nonesuch'] = t.weapon.bases.blade.paths['blade-scored']; delete t.weapon.bases.blade.paths['blade-scored']; })).toMatch(/blade-nonesuch/);
    expect(withTypes((t) => { t.items.nonesuch = t.items.bell; })).toMatch(/items\.nonesuch: there is no such base/);
    expect(withTypes((t) => { t.weapon.bases.gun.style = 'cannon'; })).toMatch(/cannon is not a weapon type/);
  });
});
