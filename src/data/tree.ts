// The genius tree (docs/genius-tree.md): a base is a tree of thirty-one forms; a hybrid is a
// tree composed from two bases by rule. Pure: the bases and the rule are passed in.
export type Leans = Record<string, Record<string, number>>;

export interface TreeNode {
  id: string; name: string; text: string; features: string[];
  leans?: Leans; silhouette?: string; prongs?: TreeNode[]; finishes?: TreeNode[];
}
export interface Base {
  id: string; name: string; class: string; expression: string; silhouette: string; toBuild?: string[];
  spark: string; nature: Leans;
  calls: { seed?: Record<string, number>; shape?: Record<string, number>; blood?: Record<string, number> };
  hybrid: { adj: string; gift: string[]; text: string };
  settled: TreeNode; paths: TreeNode[];
  newFeatures?: Array<{ id: string; slot: string; label: string }>;
}
/** A form: one node of a tree, with everything a caller asks of a form. */
export interface Form {
  id: string; name: string; text: string;
  /** Its base's id, or first+second for a hybrid. */
  base: string;
  /** What kind of thing it is, by name: its base's, or the hybrid's ("Edged Wolf"). */
  kind: string;
  /** 1 settled, 2 a path, 3 a prong, 4 a finish. */
  level: number;
  parent: string;
  expression: string; class: string; silhouette: string;
  /** The silhouette whose palette of coats it wears (a hybrid wears its second base's). */
  coatOf: string;
  /** What this form adds. */
  own: string[];
  /** Its own and those of every form above it on its path. */
  features: string[];
  leans: Leans;
  children: string[];
  instars: { min: number; max: number };
}
export interface Hybrids {
  rule: { margin: number; min: number; bend: number; kind: string; path: string; carried: string };
  pairs: Record<string, { name?: string; text?: string; nodes?: Record<string, { name?: string; text?: string }> }>;
}

const uniq = <T>(xs: T[]): T[] => [...new Set(xs)];
const kids = (n: TreeNode): TreeNode[] => n.prongs ?? n.finishes ?? [];
const fill = (pattern: string, adj: string, name: string) => pattern.replace('{adj}', adj).replace('{name}', name);
const round = (x: number, places: number) => { const k = Math.pow(10, places); return Math.round(x * k) / k; };

interface Ctx { base: string; kind: string; expression: string; class: string; silhouette: string; coatOf: string; id: (n: TreeNode) => string }

function grow(parent: { id: string; features: string[] }, nodes: TreeNode[], level: number, c: Ctx, out: Form[]): string[] {
  const ids: string[] = [];
  for (const n of nodes) {
    const f: Form = {
      id: c.id(n), name: n.name, text: n.text, base: c.base, kind: c.kind, level, parent: parent.id,
      expression: c.expression, class: c.class, silhouette: n.silhouette ?? c.silhouette, coatOf: c.coatOf || (n.silhouette ?? c.silhouette),
      own: [...n.features], features: uniq([...parent.features, ...n.features]), leans: n.leans ?? {}, children: [],
      instars: { min: level, max: level >= 4 ? 6 : level },
    };
    out.push(f);
    ids.push(f.id);
    f.children = grow(f, kids(n), level + 1, c, out);
  }
  return ids;
}

/** A base's thirty-one forms, the settled one first. */
export function flatten(b: Base): Form[] {
  const out: Form[] = [];
  const c: Ctx = { base: b.id, kind: b.name, expression: b.expression, class: b.class, silhouette: b.silhouette, coatOf: '', id: (n) => n.id };
  grow({ id: '', features: [] }, [{ ...b.settled, prongs: b.paths }], 1, c, out);
  return out;
}

/** How alike two sets of leans are, 0 to 1 (the cosine of the two as vectors). */
export function alike(a: Leans, b: Leans): number {
  let dot = 0, na = 0, nb = 0;
  for (const [line, keys] of Object.entries(a)) for (const [k, w] of Object.entries(keys)) { na += w * w; dot += w * (b[line]?.[k] ?? 0); }
  for (const keys of Object.values(b)) for (const w of Object.values(keys)) nb += w * w;
  return na > 0 && nb > 0 ? round(dot / Math.sqrt(na * nb), 6) : 0;
}

/** Leans part of the way from one to another. */
export function bend(a: Leans, b: Leans, t: number): Leans {
  const out: Leans = {};
  for (const line of uniq([...Object.keys(a), ...Object.keys(b)])) {
    for (const k of uniq([...Object.keys(a[line] ?? {}), ...Object.keys(b[line] ?? {})])) {
      const w = round((1 - t) * (a[line]?.[k] ?? 0) + t * (b[line]?.[k] ?? 0), 3);
      if (w > 0) (out[line] ??= {})[k] = w;
    }
  }
  return out;
}

export const hybridId = (first: string, second: string) => `${first}+${second}`;

/** The hybrid's name: a pair written by hand, or the rule's. */
export function hybridName(a: Base, b: Base, hy: Hybrids): string {
  return hy.pairs[hybridId(a.id, b.id)]?.name ?? fill(hy.rule.kind, b.hybrid.adj, a.name);
}

/**
 * The tree of the hybrid of two bases: thirty forms (three paths, three prongs each, two
 * finishes each) under the first base's settled form. Its paths are the first's, bent toward
 * the second's nature; in each, the prong furthest from that nature gives way to the second's
 * prong nearest the path, carried across with its finishes.
 */
export function compose(a: Base, b: Base, hy: Hybrids): Form[] {
  const h = hybridId(a.id, b.id);
  const pair = hy.pairs[h] ?? {};
  const said = (n: TreeNode): TreeNode => ({ ...n, name: pair.nodes?.[n.id]?.name ?? n.name, text: pair.nodes?.[n.id]?.text ?? n.text });
  const used = new Set<string>();
  const theirs = b.paths.flatMap((p) => p.prongs ?? []);
  const paths = a.paths.map((P) => {
    let best = theirs.find((q) => !used.has(q.id))!;
    let bestS = -1;
    for (const q of theirs) {
      if (used.has(q.id)) continue;
      const s = alike(q.leans ?? {}, P.leans ?? {});
      if (s > bestS) { bestS = s; best = q; }
    }
    used.add(best.id);
    let drop = 0;
    let dropS = Infinity;
    (P.prongs ?? []).forEach((q, i) => { const s = alike(q.leans ?? {}, b.nature); if (s <= dropS) { dropS = s; drop = i; } });
    const carried: TreeNode = said({
      id: best.id, name: fill(hy.rule.carried, a.hybrid.adj, best.name), text: best.text, features: best.features, leans: best.leans,
      finishes: (best.finishes ?? []).map((f) => said({ id: f.id, name: fill(hy.rule.carried, a.hybrid.adj, f.name), text: f.text, features: f.features, leans: f.leans })),
    });
    return said({
      ...P, name: fill(hy.rule.path, b.hybrid.adj, P.name), text: `${P.text} ${b.hybrid.text}`, leans: bend(P.leans ?? {}, b.nature, hy.rule.bend),
      prongs: (P.prongs ?? []).map((q, i) => (i === drop ? carried : { ...said(q), finishes: (q.finishes ?? []).map(said) })),
    });
  });
  const out: Form[] = [];
  const c: Ctx = { base: h, kind: hybridName(a, b, hy), expression: a.expression, class: a.class, silhouette: a.silhouette, coatOf: b.silhouette, id: (n) => `${h}:${n.id}` };
  grow({ id: a.settled.id, features: uniq([...a.settled.features, ...b.hybrid.gift]) }, paths, 2, c, out);
  return out;
}
