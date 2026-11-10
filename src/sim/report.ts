// Plain-language report of a simulated life, for the owner.
import { data, byId, formOf, baseOf } from '../data';
import { dateLabel, roman, stateOn, type SimResult } from './simulate';

const label = (id: string) => data.features.find((f) => f.id === id)?.label ?? id;

export function report(r: SimResult, opts: { log?: boolean } = {}): string {
  const out: string[] = [];
  const L = r.life;
  const p = (s = '') => out.push(s);
  p(`=== ${L.name} ===`);
  p(`${byId(data.bloods, L.blood).name} (${byId(data.bloods, L.blood).tier}) · Seed: "${byId(data.seeds, L.seed).text}" · Shape: ${L.shape} · ${L.city} / ${L.discipline}`);
  p();
  p('THE GENIUS, READING BY READING');
  const LEVELS = ['', 'settles as a base', 'takes a path', 'takes a prong', 'takes its finish'];
  for (const rd of r.readings) {
    const res = rd.result;
    if (res.grows) {
      p(`  ${dateLabel(rd.day)} — instar ${rd.instar}, unlocked by ${rd.unlockedBy}: it grows, the same form an age on (${rd.picked.name})`);
    } else {
      p(`  ${dateLabel(rd.day)} — ${rd.instar === 1 ? 'the rite' : `instar ${rd.instar}, unlocked by ${rd.unlockedBy}`}: it ${LEVELS[res.level] ?? 'is read'}`);
      const line = (c: typeof rd.picked, i: number) => {
        const mark = c.form === rd.picked.form ? (rd.settled ? '→ settled' : '→ picked ') : '         ';
        const why = c.reasons.map((x) => `${x.line}:${x.key}${['seed', 'blood', 'shape', 'home', 'pattern', 'bonds'].includes(x.line) ? '' : ` ${Math.round(x.share * 100)}%`}`).join(', ');
        p(`    ${mark} ${i + 1}. ${c.name} (${formOf(c.form)?.kind ?? c.base}) [${c.expression}] fit ${c.score}`);
        if (formOf(c.form)?.of) p(`              the picture of: ${formOf(c.form)!.of}`);
        p(`              read from: ${why || 'nothing in the Tally'}`);
      };
      res.candidates.forEach(line);
      if (res.turning) {
        p(`    the play has turned toward the ${byId(data.bases, res.turning.second).name} (it fits ${res.turning.other}; its own nature ${res.turning.own}): ${res.turning.name} is offered`);
        res.turning.candidates.forEach(line);
      }
      if (rd.picked.heritage.length) p(`    it keeps: ${rd.picked.heritage.map(label).join('; ')}`);
    }
    if (rd.graftsOffered.length) p(`    grafts offered: ${rd.graftsOffered.map((g) => `${label(g.feature)} (${g.source})`).join('; ')}${rd.graftsAccepted.length ? ' — accepted' : ' — declined'}`);
    if (rd.adaptationsAtReading.length) p(`    adaptations at the Reading: ${rd.adaptationsAtReading.join(', ')}${rd.fixed.length ? `; fixed as heritage: ${rd.fixed.join(', ')}` : ''}`);
  }
  p();
  const g = r.genius;
  p(`  Now: ${formOf(g.form)?.name ?? g.form} (${formOf(g.form)?.kind ?? g.base}) [${g.expression}], instar ${g.instar}${g.focus ? `, Focus ${g.focus}` : ''}`);
  const now = formOf(g.form);
  const whose = baseOf(g.base.split('+')[0])?.soul;
  if (whose) p(`  Whose soul: ${whose}`);
  if (now?.of) p(`  The picture of: ${now.of}`);
  if (now?.sign) p(`  Its sign: ${now.sign}`);
  if (now?.habit) p(`  Its habit: ${now.habit}`);
  p(`  Wears: ${[...new Set([g.seedMark, ...g.own, ...g.heritage, ...g.grafts.map((x) => x.feature)])].map(label).join('; ')}`);
  p(`  Secondary forms: ${g.secondary.length ? g.secondary.map((s) => `${s.id}${s.vestigial ? ' (vestigial)' : ''} from ${dateLabel(s.day)}`).join('; ') : 'none'}`);
  p(`  Shadows: ${g.shadows.length ? g.shadows.map((s) => `${s.pattern} (${s.uses} witnessed)`).join('; ') : 'none'}`);
  p(`  Adaptations over the life: ${r.adaptationHistory.map((a) => `${a.id} day ${a.gained}${a.lost !== null ? `→${a.lost} ${a.how}` : ' (held)'}`).join('; ') || 'none'}`);
  p();
  p('THE PATTERN');
  if (r.pattern) {
    const pt = r.pattern;
    p(`  ${pt.name}: ${pt.form} + ${pt.terms.map((t) => byId(data.terms, t).text).join(' / ')}`);
    p(`  x${pt.multiplier}${pt.sworn ? ' (sworn)' : ''}, built ${dateLabel(pt.builtDay)}, ${pt.uses} uses`);
    for (const [t, d] of Object.entries(r.tierDays)) p(`  Tier ${roman(Number(t))}: ${dateLabel(d)}`);
  } else p('  none built');
  p();
  p('RESONANCE OVER TIME (every three months)');
  for (const s of r.snapshots.filter((_, i) => i % 3 === 0)) {
    const st = stateOn(r, s.day);
    p(`  month ${String(s.month).padStart(2)}: instar ${s.instar} · tier ${roman(s.tier) || '—'} · Resonance ${s.resonance} · Pattern pays ${st.verses} verse(s), ${st.chainBeats}-beat chain · genius Will ${s.geniusWill}`);
  }
  p();
  p('JOBS');
  p(`  Stage ${r.stage}${r.stage4Day !== null ? ` (Stage 4 from ${dateLabel(r.stage4Day)})` : ''}`);
  for (const a of r.archetypes) p(`  ${byId(data.archetypes, a.archetype).name}: ${a.rank}, ${a.marks} Marks${a.adeptDay !== null ? `; Adept ${dateLabel(a.adeptDay)}` : ''}${a.masterDay !== null ? `; Master ${dateLabel(a.masterDay)}` : ''}`);
  if (r.crossTitle) p(`  Cross title: ${r.crossTitle.title}, ${dateLabel(r.crossTitle.day)}`);
  if (r.milestoneDays.accord !== undefined) p(`  ACCORD: ${dateLabel(r.milestoneDays.accord)}`);
  if (r.foundingEligibleDay !== null) p(`  Founding eligible: ${dateLabel(r.foundingEligibleDay)}`);
  if (r.techniques.length) p(`  Techniques: ${r.techniques.map((t) => `${t.id} ${t.grade} (${t.uses})`).join('; ')}`);
  if (r.warnings.length) { p(); p('WARNINGS'); r.warnings.forEach((w) => p(`  ${w}`)); }
  if (opts.log) { p(); p('LOG'); r.log.forEach((l) => p(`  ${dateLabel(l.day)}: ${l.text}`)); }
  return out.join('\n');
}
