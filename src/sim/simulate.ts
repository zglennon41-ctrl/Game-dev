// The headless simulator: runs a scripted life day by day through the rules.
import { data, byId } from '../data';
import { buildPattern, chainBeats, formShape, type BuiltPattern } from '../rules/terms';
import { tierFor, resonance, payingTier, verses, shadowCap, geniusWill, isAccord, readingDue, instarRule } from '../rules/resonance';
import { rankFor, crossTitle, foundingEligible, gradeFor, type Rank } from '../rules/marks';
import { read, take, emptyTally, featuresOf, type GeniusForm, type ReadingResult, type Tally, type Candidate } from '../rules/reading';
import type { Life, LifeEvent, Phase } from './script';

const G = data.rules.genius;

export interface ReadingRecord {
  day: number;
  instar: number;
  unlockedBy: string;
  result: ReadingResult;
  picked: Candidate;
  settled: boolean;
  graftsOffered: Array<{ id: string; feature: string; source: string }>;
  graftsAccepted: Array<{ id: string; feature: string; source: string }>;
  adaptationsAtReading: string[];
  fixed: string[];
  tierAtReading: number;
  resonanceAtReading: number;
}

export interface Snapshot { day: number; month: number; instar: number; tier: number; resonance: number; uses: number; verses: number; geniusWill: number; shadowCap: number }

export interface ArchetypeRecord { archetype: string; marks: number; rank: Rank; takenDay: number; adeptDay: number | null; masterDay: number | null }

export interface SimResult {
  life: Life;
  log: Array<{ day: number; text: string }>;
  readings: ReadingRecord[];
  snapshots: Snapshot[];
  instarDays: Record<number, number>;
  tierDays: Record<number, number>;
  milestoneDays: Record<string, number>;
  archetypes: ArchetypeRecord[];
  crossTitle: { title: string; day: number } | null;
  foundingEligibleDay: number | null;
  stage: number;
  stage4Day: number | null;
  pattern: (BuiltPattern & { uses: number; builtDay: number; tier: number }) | null;
  genius: GeniusForm & { instar: number; focus: string | null; secondary: Array<{ id: string; day: number; vestigial: boolean }>; shadows: Array<{ pattern: string; uses: number }> };
  adaptationHistory: Array<{ id: string; gained: number; lost: number | null; how: string | null }>;
  graftsAvailable: Array<{ id: string; day: number }>;
  techniques: Array<{ id: string; uses: number; grade: string }>;
  warnings: string[];
}

class Acc {
  private a = new Map<string, number>();
  /** Deterministic: a rate of 0.4/day yields 0,0,1,0,1,... with no randomness. */
  take(key: string, rate: number): number {
    if (!rate) return 0;
    const v = (this.a.get(key) ?? 0) + rate;
    const n = Math.floor(v + 1e-9);
    this.a.set(key, v - n);
    return n;
  }
}

function add(o: Record<string, number>, k: string, n: number) {
  if (n) o[k] = (o[k] ?? 0) + n;
}

export function monthOf(day: number): number { return Math.floor(day / (365 / 12)) + 1; }
export function yearOf(day: number): number { return Math.floor(day / 365) + 1; }
export function seasonOf(day: number): string {
  const C = data.rules.calendar;
  return C.seasons[Math.floor(day / C.seasonDays) % C.seasons.length];
}
export function dateLabel(day: number): string {
  return `Y${yearOf(day)} ${seasonOf(day)} (day ${day}, month ${monthOf(day)})`;
}

export function simulate(life: Life): SimResult {
  const acc = new Acc();
  const log: SimResult['log'] = [];
  const say = (day: number, text: string) => log.push({ day, text });
  const warnings: string[] = [];
  const blood = byId(data.bloods, life.blood, 'blood');
  const origin = { seed: life.seed, blood: life.blood, shape: life.shape };

  let tally: Tally = emptyTally();
  const lifetime: Record<string, number> = {};
  const runsWithLife: Record<string, number> = {};
  const milestones = new Set<string>();
  const milestoneDays: Record<string, number> = {};
  const mark = (m: string, day: number) => {
    if (!milestones.has(m)) { milestones.add(m); milestoneDays[m] = day; say(day, `Milestone: ${m}`); }
  };

  let stage = 1;
  let stage4Day: number | null = null;
  let questsSinceGate = 0;
  let equipped = life.archetype;
  const archetypes = new Map<string, ArchetypeRecord>();
  let pattern: SimResult['pattern'] = null;
  let pendingBuild: (LifeEvent & { type: 'build-pattern' }) | null = null;
  const peers = new Map<string, number>();
  let foundingEligibleDay: number | null = null;
  let cross: SimResult['crossTitle'] = null;

  // The genius.
  let instar = 0;
  let genius: GeniusForm | null = null;
  let focus: string | null = null;
  const secondary: SimResult['genius']['secondary'] = [];
  const shadows: SimResult['genius']['shadows'] = [];
  const witnessed: Record<string, number> = {};
  const adaptationHistory: SimResult['adaptationHistory'] = [];
  const instarDays: Record<number, number> = {};
  const tierDays: Record<number, number> = {};
  const readings: ReadingRecord[] = [];
  const pendingGrafts: Array<{ id: string; feature: string; source: string }> = [];
  const graftsSeen = new Set<string>();
  const graftsAvailable: SimResult['graftsAvailable'] = [];
  const namedKills: Record<string, number> = {};
  /** Count since the last Reading at which an adaptation faded: it regrows only from new play. */
  let fadedAt: Record<string, number> = {};
  const techniqueUses: Record<string, number> = {};
  const snapshots: Snapshot[] = [];
  let lastTier = 0;

  const offerGraft = (day: number, g: { id: string; feature: string; source: string }) => {
    if (graftsSeen.has(g.id)) return;
    graftsSeen.add(g.id);
    pendingGrafts.push(g);
    graftsAvailable.push({ id: g.id, day });
    say(day, `Graft available at the next Reading: ${g.feature} (${g.source})`);
  };

  const takeArchetype = (day: number, id: string) => {
    if (archetypes.has(id)) return;
    byId(data.archetypes, id, 'archetype');
    archetypes.set(id, { archetype: id, marks: 0, rank: 'journeyman', takenDay: day, adeptDay: null, masterDay: null });
    say(day, `Takes ${byId(data.archetypes, id).name} (Journeyman)`);
  };

  const doReading = (day: number, n: number, unlockedBy: string) => {
    const tier = pattern?.tier ?? 0;
    const result = read({ instar: n, tally, origin, current: genius });
    const pick = life.picks?.[String(n)];
    let picked = result.candidates[0];
    let settled = true;
    if (pick) {
      const m = result.candidates.find((c) => (pick.form ? c.form === pick.form : true) && (pick.expression ? c.expression === pick.expression : true));
      if (m) { picked = m; settled = false; } else warnings.push(`Day ${day}: pick for instar ${n} (${JSON.stringify(pick)}) not among candidates; settled`);
    }
    const offered = n >= 2 ? pendingGrafts.splice(0) : [];
    const room = Math.max(0, G.graftSlots - (genius?.grafts.length ?? 0));
    const accepted = life.grafts === 'decline' ? [] : offered.slice(0, room);
    const adaptationsAtReading = genius?.adaptations.map((a) => a.id) ?? [];
    const fixed = picked.heritage.filter((h) => adaptationsAtReading.includes(h));
    for (const a of adaptationsAtReading) {
      const h = adaptationHistory.find((x) => x.id === a && x.lost === null);
      if (h) { h.lost = day; h.how = fixed.includes(a) ? 'fixed as heritage' : 'lost at the Reading'; }
    }
    genius = take(genius, picked, accepted);
    instar = n;
    instarDays[n] = day;
    if (n === 4 && life.focus) focus = life.focus;
    readings.push({ day, instar: n, unlockedBy, result, picked, settled, graftsOffered: offered, graftsAccepted: accepted, adaptationsAtReading, fixed, tierAtReading: tier, resonanceAtReading: resonance(n, tier) });
    say(day, `Reading → ${instarRule(n).name}: ${picked.name} (${picked.expression})${settled ? ', settled' : ', picked'}; unlocked by ${unlockedBy}`);
    // The Tally is since the last Reading; the Pattern stays the intention.
    tally = emptyTally();
    fadedAt = {};
    if (pattern) tally.intention = { form: pattern.form, terms: pattern.terms, fires: 0 };
    // Secondary forms that no longer fit go vestigial.
    for (const s of secondary) s.vestigial = !meets(byId(data.secondaryForms, s.id).requires.filter((r) => r.kind === 'expression'), day);
  };

  const meets = (reqs: typeof data.secondaryForms[number]['requires'], _day: number): boolean =>
    reqs.every((r) => {
      switch (r.kind) {
        case 'expression': return !!genius && r.in.includes(genius.expression);
        case 'counter': return (lifetime[r.metric] ?? 0) >= r.atLeast;
        case 'patternFamily': return pattern?.form === r.family;
        case 'instar': return instar >= r.atLeast;
        case 'accord': return milestones.has('accord');
        case 'rank': return [...archetypes.values()].some((a) => byId(data.archetypes, a.archetype).discipline === r.archetypeDiscipline && (r.rank === 'adept' ? a.rank !== 'journeyman' : a.rank === 'master'));
      }
    });

  const applyEvent = (day: number, e: LifeEvent) => {
    switch (e.type) {
      case 'take-archetype': takeArchetype(day, e.archetype); break;
      case 'equip': equipped = e.archetype; say(day, `Equips ${byId(data.archetypes, e.archetype).name}`); break;
      case 'build-pattern': pendingBuild = e; break;
      case 'swear':
        if (!pattern) { warnings.push(`Day ${day}: swear with no Pattern`); break; }
        pattern = { ...pattern, ...buildPattern({ ...pattern, sworn: true }, { shape: life.shape, swornCharacter: life.swornCharacter }), uses: pattern.uses, builtDay: pattern.builtDay, tier: pattern.tier };
        say(day, `Swears ${pattern.name} at the hearth: x${pattern.multiplier}`);
        break;
      case 'shade-accept': {
        const s = byId(data.shades, e.shade, 'shade');
        add(lifetime, 'shades.accepted', 1);
        add(tally.bonds, 'shade', 1);
        say(day, `Accepted by a shade: ${s.name}`);
        offerGraft(day, { id: `shade:${s.id}`, feature: s.graftFeature, source: `shade:${s.id}` });
        break;
      }
      case 'named-kill': {
        namedKills[e.beast] = (namedKills[e.beast] ?? 0) + 1;
        if (namedKills[e.beast] >= G.namedBeastKills && e.features?.[0]) offerGraft(day, { id: `beast:${e.beast}`, feature: e.features[0], source: `beast:${e.beast}` });
        break;
      }
      case 'rally-won': add(lifetime, 'rallies.won', 1); break;
      case 'peer-uses': peers.set(e.account, e.uses); break;
    }
  };

  // Day 0: the rite. The First Form is read from Seed, blood and Shape.
  stage = 2;
  doReading(0, 1, 'rite');
  mark('rite', 0);
  takeArchetype(0, life.archetype);

  for (let day = 0; day < life.days; day++) {
    if (day === life.gateDay) { stage = 3; mark('gate', day); }
    for (const e of life.events.filter((x) => x.day === day)) applyEvent(day, e);

    const ph: Phase | undefined = life.phases.find((p) => p.from <= day && day < p.to);
    if (ph) {
      const runsRate = ph.runsPerDay ?? 0;
      const fightRate = (ph.fightsPerDay ?? 0) + runsRate * (ph.fightsPerRun ?? 0);
      const runs = acc.take('runs', runsRate);
      add(lifetime, 'runs', runs);
      for (const [r, s] of Object.entries(ph.range ?? {})) {
        const n = acc.take(`range.${r}`, fightRate * (s ?? 0));
        add(tally.range, r, n);
        add(tally.counters, `fights.range.${r}`, n);
      }
      for (const [f, perFight] of Object.entries(ph.families ?? {})) {
        const n = acc.take(`fam.${f}`, fightRate * perFight);
        add(tally.families, f, n);
        add(tally.counters, `fieldUses.${f}`, n);
        add(lifetime, `fieldUses.${f}`, n);
      }
      for (const [o, s] of Object.entries(ph.orders ?? {})) {
        const n = acc.take(`ord.${o}`, (ph.ordersPerDay ?? 0) * (s ?? 0));
        add(tally.orders, o, n);
        add(lifetime, `orders.${o}`, n);
      }
      for (const [c, s] of Object.entries(ph.company ?? {})) {
        const n = acc.take(`comp.${c}`, runsRate * (s ?? 0));
        add(tally.company, c, n);
        add(tally.counters, `runs.company.${c}`, n);
      }
      for (const [w, s] of Object.entries(ph.runsWith ?? {})) {
        const n = acc.take(`with.${w}`, runsRate * s);
        add(tally.runsWith, w, n);
        add(runsWithLife, w, n);
      }
      for (const [g, s] of Object.entries(ph.ground ?? {})) {
        const n = acc.take(`ground.${g}`, runsRate * (s ?? 0));
        add(tally.ground, g, n);
        add(tally.counters, `runs.ground.${g}`, n);
      }
      const nightRuns = acc.take('night', runsRate * (ph.night ?? 0));
      add(tally.ground, 'night', nightRuns);
      add(tally.counters, 'runs.night', nightRuns);
      add(lifetime, 'runs.night', nightRuns);
      for (const [q, s] of Object.entries(ph.questTypes ?? {})) {
        const n = acc.take(`qt.${q}`, runsRate * s);
        add(tally.counters, `runs.quest.${q}`, n);
        add(lifetime, `runs.quest.${q}`, n);
      }
      const disc = byId(data.archetypes, equipped).discipline;
      add(tally.discipline, disc, acc.take('disc', runsRate));
      for (const [f, rate] of Object.entries(ph.fieldUses ?? {})) {
        const n = acc.take(`fu.${f}`, rate);
        add(tally.counters, `fieldUses.${f}`, n);
        add(lifetime, `fieldUses.${f}`, n);
      }
      for (const q of ph.quests ?? []) {
        const n = acc.take(`q.${q.archetype}.${q.color}`, q.perDay);
        if (!n) continue;
        questsSinceGate += day >= life.gateDay ? n : 0;
        if (q.archetype === 'none') continue;
        const a = archetypes.get(q.archetype);
        if (!a) { warnings.push(`Day ${day}: quest in ${q.archetype}, which is not taken`); continue; }
        const per = data.rules.marks.byColor[q.color] * (life.swornCharacter ? data.rules.marks.swornMultiplier : 1);
        a.marks += n * per;
      }
      for (const [t, rate] of Object.entries(ph.techniques ?? {})) add(techniqueUses, t, acc.take(`tech.${t}`, rate));
      if (ph.hearthSundays && day % 7 === 6) add(tally.bonds, 'hearth', 1);
      if (ph.kitchenHigh) add(tally.counters, 'days.kitchenHigh', 1);
      if (pattern) {
        const fires = acc.take('fires', ph.patternFiresPerDay ?? 0);
        if (fires) {
          pattern.uses += fires;
          if (tally.intention) tally.intention.fires += fires;
          witnessed[pattern.name] = (witnessed[pattern.name] ?? 0) + fires;
        }
      }
    }

    // A Pattern is built at Stage 4: 10 witnessed quests since the Gate, and a Term.
    if (pendingBuild && questsSinceGate >= data.rules.marks.stage4Quests && stage >= 3) {
      const b: LifeEvent & { type: 'build-pattern' } = pendingBuild;
      const built = buildPattern(b, { shape: life.shape, swornCharacter: life.swornCharacter });
      pattern = { ...built, uses: 0, builtDay: day, tier: 1 };
      if (b.archetype) takeArchetype(day, b.archetype);
      stage = 4;
      stage4Day = day;
      pendingBuild = null;
      tally.intention = { form: built.form, terms: built.terms, fires: 0 };
      say(day, `Stage 4. Builds ${built.name}: ${built.form} + ${built.terms.join(', ')}; x${built.multiplier}${built.sworn ? ' sworn' : ''}; ${built.chainBeats}-beat chain`);
      mark('pattern-built', day);
    }

    // Ranks.
    for (const a of archetypes.values()) {
      const r = rankFor({ marks: a.marks, stage, patternBuiltIn: pattern?.archetype === a.archetype });
      if (r !== a.rank) {
        a.rank = r;
        if (r === 'adept' && a.adeptDay === null) { a.adeptDay = day; mark('adept', day); }
        if (r === 'master') { a.adeptDay ??= day; a.masterDay = day; mark('adept', day); mark('master', day); }
        say(day, `${r === 'master' ? 'Master' : 'Adept'} ${byId(data.archetypes, a.archetype).name}`);
      }
    }
    if (!cross) {
      const t = crossTitle([...archetypes.values()].map((a) => ({ archetype: a.archetype, rank: a.rank, since: a.adeptDay ?? Infinity })));
      if (t) { cross = { title: t, day }; say(day, `Cross title: ${t}`); }
    }

    // Tier.
    if (pattern) {
      pattern.tier = tierFor({
        uses: pattern.uses, built: true, sworn: pattern.sworn,
        masterInArchetype: !!pattern.archetype && archetypes.get(pattern.archetype)?.rank === 'master',
        stage4Days: stage4Day === null ? 0 : day - stage4Day,
      });
      for (let t = lastTier + 1; t <= pattern.tier; t++) { tierDays[t] = day; say(day, `Intention tier ${roman(t)} (${pattern.uses} uses)`); }
      lastTier = Math.max(lastTier, pattern.tier);
    }
    const tier = pattern?.tier ?? 0;
    if (isAccord(instar, tier)) mark('accord', day);

    // Founding.
    if (pattern && foundingEligibleDay === null && peers.size >= 2) {
      const me = { account: life.account, guild: life.guild, form: pattern.form, terms: pattern.terms, witnessedUses: pattern.uses };
      const others = [...peers.entries()].map(([account, uses]) => ({ ...me, account, witnessedUses: uses }));
      if (foundingEligible([me, ...others]).eligible) { foundingEligibleDay = day; say(day, `Founding eligible: ${pattern.name}`); }
    }

    // Adaptations: gained at thresholds since the last Reading; fade after a season unfed.
    if (genius) {
      const gen: GeniusForm = genius;
      for (const ad of data.adaptations) {
        const have = gen.adaptations.find((a) => a.id === ad.id);
        const count = tally.counters[ad.metric] ?? 0;
        if (have) {
          if ((tally.counters[`__last.${ad.metric}`] ?? -1) !== count) have.lastFed = day;
        } else if (count - (fadedAt[ad.id] ?? 0) >= ad.threshold && gen.adaptations.length < G.adaptationSlots && !featuresOf(gen).includes(ad.id)) {
          gen.adaptations.push({ id: ad.id, lastFed: day });
          adaptationHistory.push({ id: ad.id, gained: day, lost: null, how: null });
          say(day, `Adaptation: ${ad.id}`);
        }
        tally.counters[`__last.${ad.metric}`] = count;
      }
      for (const a of [...gen.adaptations]) {
        if (day - a.lastFed > G.adaptationFadeDays) {
          gen.adaptations = gen.adaptations.filter((x) => x !== a);
          const h = adaptationHistory.find((x) => x.id === a.id && x.lost === null);
          if (h) { h.lost = day; h.how = 'faded'; }
          const metric = data.adaptations.find((x) => x.id === a.id)?.metric;
          if (metric) fadedAt[a.id] = tally.counters[metric] ?? 0;
          say(day, `Adaptation faded: ${a.id}`);
        }
      }
    }

    // Grafts that become available.
    for (const [who, n] of Object.entries(runsWithLife)) {
      if (n >= G.kinRuns) {
        const feature = data.roster.find((r) => r.id === who)?.genius.kinFeature ?? life.companions?.[who]?.kinFeature;
        if (feature) offerGraft(day, { id: `kin:${who}`, feature, source: `kin:${who}` });
      }
    }
    if (blood.graft && instar >= G.bloodGraftFromInstar) offerGraft(day, { id: `blood:${blood.id}`, feature: blood.graft, source: `blood:${blood.id}` });

    // Readings due today.
    for (let next = instar + 1; next <= 6; next = instar + 1) {
      const reason = readingDue(next, day, milestones, tier);
      if (!reason) break;
      doReading(day, next, reason);
      if (isAccord(instar, tier)) mark('accord', day);
    }

    // Secondary forms, from the Third Form.
    if (instar >= G.secondaryFromInstar && secondary.length < G.secondarySlots) {
      for (const sf of data.secondaryForms) {
        if (secondary.length >= G.secondarySlots || secondary.some((s) => s.id === sf.id)) continue;
        if (meets(sf.requires, day)) { secondary.push({ id: sf.id, day, vestigial: false }); say(day, `Secondary form: ${sf.name}`); }
      }
    }

    // Shadows: ten witnessed uses, up to the cap at Resonance.
    const res = resonance(instar, tier);
    for (const [p, uses] of Object.entries(witnessed)) {
      const s = shadows.find((x) => x.pattern === p);
      if (s) s.uses = uses;
      else if (uses >= G.shadowUses && shadows.length < shadowCap(res)) { shadows.push({ pattern: p, uses }); say(day, `Shadow: ${p}`); }
    }

    if (day % 30 === 0 || day === life.days - 1) {
      snapshots.push({ day, month: monthOf(day), instar, tier, resonance: res, uses: pattern?.uses ?? 0, verses: pattern ? verses(payingTier(res, tier)) : 0, geniusWill: geniusWill(res), shadowCap: shadowCap(res) });
    }
  }

  const g = genius as GeniusForm | null;
  if (!g) throw new Error('no genius');
  return {
    life, log, readings, snapshots, instarDays, tierDays, milestoneDays,
    archetypes: [...archetypes.values()], crossTitle: cross, foundingEligibleDay, stage, stage4Day,
    pattern, genius: { ...g, instar, focus, secondary, shadows }, adaptationHistory, graftsAvailable,
    techniques: Object.entries(techniqueUses).map(([id, uses]) => ({ id, uses, grade: gradeFor(uses) })),
    warnings,
  };
}

/** Resonance and the Pattern's pay on a given day, from the snapshots' rules. */
export function stateOn(r: SimResult, day: number) {
  const instar = Math.max(0, ...Object.entries(r.instarDays).filter(([, d]) => d <= day).map(([n]) => Number(n)));
  const tier = Math.max(0, ...Object.entries(r.tierDays).filter(([, d]) => d <= day).map(([n]) => Number(n)));
  const res = resonance(instar, tier);
  const pay = payingTier(res, tier);
  return { instar, tier, resonance: res, verses: tier ? verses(pay) : 0, chainBeats: tier && r.pattern ? chainBeats(r.pattern.terms.length, verses(pay)) : 0 };
}

export function roman(n: number): string { return ['', 'I', 'II', 'III', 'IV', 'V'][n] ?? String(n); }
export { formShape };
