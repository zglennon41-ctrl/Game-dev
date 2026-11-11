// The genius tree (docs/genius-tree.md): a base is a tree of thirty-one forms; a hybrid is a
// tree composed from two bases by rule. Pure: the bases and the rule are passed in.
export type Leans = Record<string, Record<string, number>>;

export interface TreeNode {
  id: string; name: string; text: string; features: string[];
  /** What in its partner the form is the picture of (levels 2 to 4). */
  of?: string;
  /** What a stranger would notice about it; what it does when nothing is happening. */
  sign?: string; habit?: string;
  leans?: Leans; silhouette?: string; prongs?: TreeNode[]; finishes?: TreeNode[];
  /** The form whose own model it wears, where that is not itself (a form carried into a hybrid). */
  wears?: string;
}
export interface Base {
  id: string; name: string; class: string; expression: string; silhouette: string; toBuild?: string[];
  /** Whose soul settles as this. */
  soul?: string;
  spark: string; nature: Leans;
  calls: { seed?: Record<string, number>; shape?: Record<string, number>; blood?: Record<string, number> };
  hybrid: { adj: string; gift: string[]; text: string };
  settled: TreeNode; paths: TreeNode[];
  newFeatures?: Array<{ id: string; slot: string; label: string }>;
}
/** A form: one node of a tree, with everything a caller asks of a form. */
export interface Form {
  id: string; name: string; text: string;
  /** What in its partner it is the picture of ('' for a settled form), its sign and its habit. */
  of: string; sign: string; habit: string;
  /** Its base's id, or first+second for a hybrid. */
  base: string;
  /** What kind of thing it is, by name: its base's, or the hybrid's ("Edged Wolf"). */
  kind: string;
  /** 1 settled, 2 a path, 3 a prong, 4 a finish. */
  level: number;
  parent: string;
  expression: string; class: string;
  /** Its body: its own where it names one, or that of the nearest form above it that does, or its base's. */
  silhouette: string;
  /** The silhouette whose palette of coats it wears (a hybrid wears its second base's). */
  coatOf: string;
  /** The form whose own model it wears: its own; or, carried into a hybrid from its second base, the form of the first it took the place of. */
  wears: string;
  /** What this form adds. */
  own: string[];
  /** Its own and those of every form above it on its path. */
  features: string[];
  leans: Leans;
  children: string[];
  instars: { min: number; max: number };
}
export interface Said { name?: string; text?: string; of?: string; sign?: string; habit?: string }
export interface Hybrids {
  rule: { margin: number; min: number; bend: number; kind: string; path: string; carried: string; of: string; sign: string };
  pairs: Record<string, { name?: string; text?: string; nodes?: Record<string, Said> }>;
}

const uniq = <T>(xs: T[]): T[] => [...new Set(xs)];
const kids = (n: TreeNode): TreeNode[] => n.prongs ?? n.finishes ?? [];
const round = (x: number, places: number) => { const k = Math.pow(10, places); return Math.round(x * k) / k; };
/** Fill a pattern's {words}; tidy the spaces an empty word leaves. */
export function fill(pattern: string, words: Record<string, string>): string {
  let s = pattern;
  for (const [k, v] of Object.entries(words)) s = s.split(`{${k}}`).join(v);
  return s.replace(/ +/g, ' ').trim();
}

interface Ctx { base: string; kind: string; expression: string; class: string; coatOf: string; id: (n: TreeNode) => string }

function grow(parent: { id: string; features: string[] }, nodes: TreeNode[], level: number, silhouette: string, c: Ctx, out: Form[]): string[] {
  const ids: string[] = [];
  for (const n of nodes) {
    // a form wears its own body where it names one; the forms below it on that road wear it too
    const sil = n.silhouette ?? silhouette;
    const f: Form = {
      id: c.id(n), name: n.name, text: n.text, of: n.of ?? '', sign: n.sign ?? '', habit: n.habit ?? '',
      base: c.base, kind: c.kind, level, parent: parent.id,
      expression: c.expression, class: c.class, silhouette: sil, coatOf: c.coatOf || sil, wears: n.wears ?? n.id,
      own: [...n.features], features: uniq([...parent.features, ...n.features]), leans: n.leans ?? {}, children: [],
      instars: { min: level, max: level >= 4 ? 6 : level },
    };
    out.push(f);
    ids.push(f.id);
    f.children = grow(f, kids(n), level + 1, sil, c, out);
  }
  return ids;
}

/** A base's thirty-one forms, the settled one first. */
export function flatten(b: Base): Form[] {
  const out: Form[] = [];
  const c: Ctx = { base: b.id, kind: b.name, expression: b.expression, class: b.class, coatOf: '', id: (n) => n.id };
  grow({ id: '', features: [] }, [{ ...b.settled, prongs: b.paths }], 1, b.silhouette, c, out);
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

/**
 * What play earns a path: `first` is the thing it leans on most ("orders.hunt"), `sig` its two
 * heaviest leans in the order of their names. Of equal leans the one written first counts first.
 */
export function signature(leans: Leans): { first: string; sig: string[] } {
  let a = '', b = '';
  let wa = -1, wb = -1;
  for (const [line, keys] of Object.entries(leans)) for (const [k, w] of Object.entries(keys)) {
    const id = `${line}.${k}`;
    if (w > wa) { b = a; wb = wa; a = id; wa = w; } else if (w > wb) { b = id; wb = w; }
  }
  return { first: a, sig: [a, b].filter((x) => x !== '').sort() };
}

export const hybridId = (first: string, second: string) => `${first}+${second}`;

/** A name made of another's word and a form's name: a Winged Mantler; The Winged Last Word. */
export function rename(pattern: string, adj: string, name: string): string {
  return name.startsWith('The ') ? `The ${fill(pattern, { adj, name: name.slice(4) })}` : fill(pattern, { adj, name });
}

/** The hybrid's name: a pair written by hand, or the rule's. */
export function hybridName(a: Base, b: Base, hy: Hybrids): string {
  return hy.pairs[hybridId(a.id, b.id)]?.name ?? fill(hy.rule.kind, { adj: b.hybrid.adj, name: a.name });
}

/**
 * The tree of the hybrid of two bases: thirty forms (three paths, three prongs each, two
 * finishes each) under the first base's settled form. Its paths are the first's, bent toward
 * the second's nature (less far where two of them would otherwise be earned by the same play);
 * in each, the prong furthest from that nature gives way to the second's prong nearest the
 * path, carried across with its finishes. Every form says what it is the picture of, carries
 * the second's gift as its sign, and keeps a habit of the first's. labels: a feature's words.
 */
export function compose(a: Base, b: Base, hy: Hybrids, labels: Record<string, string> = {}): Form[] {
  const h = hybridId(a.id, b.id);
  const pair = hy.pairs[h] ?? {};
  const rule = hy.rule;
  const words = { first: a.name.toLowerCase(), second: b.name.toLowerCase(), gift: b.hybrid.gift.map((g) => labels[g] ?? g.replace(/-/g, ' ')).join(' and ') };
  const said = (n: TreeNode): TreeNode => {
    const o = pair.nodes?.[n.id] ?? {};
    return { ...n, name: o.name ?? n.name, text: o.text ?? n.text, of: o.of ?? n.of ?? '', sign: o.sign ?? fill(rule.sign, { ...words, sign: n.sign ?? '' }), habit: o.habit ?? n.habit ?? '' };
  };
  const used = new Set<string>();
  const theirs = b.paths.flatMap((p) => p.prongs ?? []);
  const taken: string[] = [];
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
    const mine = P.prongs ?? [];
    mine.forEach((q, i) => { const s = alike(q.leans ?? {}, b.nature); if (s <= dropS) { dropS = s; drop = i; } });
    const gone = mine[drop];
    const carried: TreeNode = said({
      id: best.id, name: rename(rule.carried, a.hybrid.adj, best.name), text: best.text, of: best.of, sign: '', habit: gone?.habit || best.habit,
      features: best.features, leans: best.leans, wears: gone?.id ?? best.id,
      finishes: (best.finishes ?? []).map((f, j) => said({
        id: f.id, name: rename(rule.carried, a.hybrid.adj, f.name), text: f.text, of: f.of, sign: '', habit: gone?.finishes?.[j]?.habit || f.habit, features: f.features, leans: f.leans,
        wears: gone?.finishes?.[j]?.id ?? gone?.id ?? f.id,
      })),
    });
    // every path of a hybrid is earned by its own play: bend less far while two would share a signature
    let leans = bend(P.leans ?? {}, b.nature, rule.bend);
    for (const t of [rule.bend / 2, rule.bend / 4, 0]) {
      if (!taken.includes(signature(leans).sig.join('|'))) break;
      leans = bend(P.leans ?? {}, b.nature, t);
    }
    taken.push(signature(leans).sig.join('|'));
    return said({
      ...P, name: rename(rule.path, b.hybrid.adj, P.name), text: `${P.text} ${b.hybrid.text}`, of: P.of ? fill(rule.of, { ...words, of: P.of }) : '', leans,
      prongs: mine.map((q, i) => (i === drop ? carried : { ...said(q), finishes: (q.finishes ?? []).map(said) })),
    });
  });
  const out: Form[] = [];
  const c: Ctx = { base: h, kind: hybridName(a, b, hy), expression: a.expression, class: a.class, coatOf: b.silhouette, id: (n) => `${h}:${n.id}` };
  grow({ id: a.settled.id, features: uniq([...a.settled.features, ...b.hybrid.gift]) }, paths, 2, a.silhouette, c, out);
  return out;
}
