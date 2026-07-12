export const meta = {
  name: 'deep-research-coupon',
  description: 'Deep-research multi-agents avec échange de faits vérifiés : recherche approfondie tous détails + tous marchés (foot/tennis/basket), sélection des meilleures opportunités, puis coupon cote ~5 (+ singles cote 5-7). Estimations, PAS des garanties.',
  phases: [
    { title: 'Découverte', detail: 'Recherche web des matchs du jour' },
    { title: 'Recherche', detail: 'Spécialistes par match : forme, compos/blessures, H2H, experts/réseaux, mouvements de cotes' },
    { title: 'Consolidation', detail: 'Desk éditeur : réconcilie et vérifie les faits (échange inter-agents)' },
    { title: 'Marchés', detail: 'Analyse de TOUS les marchés -> opportunités de value' },
    { title: 'Vérification', detail: 'Contrôle adversarial de chaque opportunité' },
    { title: 'Table ronde', detail: 'Coordinateur global : partage des faits, dé-corrélation, classement' },
    { title: 'Synthèse', detail: 'Construction du coupon cote ~5 + singles + rédaction' },
  ],
}

// ---------- Paramètres ----------
const DATE = (args && args.date) || "aujourd'hui"
const SINGLE_MIN = (args && args.oddsMin) || 5.0
const SINGLE_MAX = (args && args.oddsMax) || 7.0
const COUPON_TARGET = (args && args.couponTargetOdds) || 1.95
const COUPON_MAX = (args && args.couponMaxOdds) || 3.0
const MAX_PICKS = (args && args.maxPicks) || 2
const MAX_MATCHES = (args && args.maxMatches) || 12

const DISCLAIMER =
  "ESTIMATIONS statistiques, PAS des certitudes. Aucun pari n'est « sûr » : " +
  "un simple à cote 5 reste ~1 chance sur 5, un combiné cote 5 encore moins. " +
  "Ne miser que ce qu'on peut perdre. Interdit aux mineurs — " +
  "aide : joueurs-info-service.fr, 09 74 75 13 13.";

// Marchés à couvrir, par sport (recherche exhaustive)
const MARKETS = {
  football: "1X2, Double Chance, Draw No Bet, Over/Under (0.5 à 4.5), BTTS, " +
    "Handicap asiatique/européen, Total par équipe, Corners, Cartons, Mi-temps/Fin, " +
    "Score exact, Buteur (à tout moment/premier)",
  tennis: "Vainqueur du match, Handicap de jeux/sets, Total de jeux O/U, " +
    "Score en sets (set betting), Vainqueur set 1, Total de sets, " +
    "Total de jeux par joueur, Tie-break oui/non",
  basketball: "Vainqueur (moneyline), Handicap (spread), Total de points O/U, " +
    "Total par équipe, Marchés par quart-temps/mi-temps, " +
    "Props joueurs (points/rebonds/passes), Course aux X points",
};

// Spécialistes déployés sur chaque match
const SPECIALISTS = [
  { key: 'forme', ask: (m) => `Forme récente des deux camps (5-10 derniers résultats, à domicile/extérieur ou par surface), dynamique, série en cours.` },
  { key: 'compos', ask: (m) => `Compositions probables, blessures, suspensions, absences confirmées, rotations, repos. Vérifie les annonces les plus récentes.` },
  { key: 'h2h', ask: (m) => `Confrontations directes (H2H) récentes, styles de jeu, matchups favorables/défavorables, tendances (over/under, BTTS, sets).` },
  { key: 'experts', ask: (m) => `AVIS D'EXPERTS et pronostics : presse sportive, tipsters, réseaux sociaux (X/Twitter, YouTube), consensus et divergences. Distingue fait vérifié et opinion.` },
  { key: 'marche', ask: (m) => `Cotes actuelles chez plusieurs bookmakers, mouvements de cotes, cote d'ouverture vs actuelle, où est l'argent, marchés où la cote a bougé.` },
];

// ---------- Schémas ----------
const FIXTURES_SCHEMA = {
  type: 'object',
  properties: {
    matches: { type: 'array', items: { type: 'object', properties: {
      sport: { type: 'string', enum: ['football', 'tennis', 'basketball'] },
      competition: { type: 'string' }, home: { type: 'string' }, away: { type: 'string' },
      start_local: { type: 'string' }, source_url: { type: 'string' },
    }, required: ['sport', 'competition', 'home', 'away'] } },
    notes: { type: 'string' },
  }, required: ['matches'],
};

const FACT_SCHEMA = {
  type: 'object',
  properties: {
    facts: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, evidence: { type: 'string' },
      source_url: { type: 'string' }, confidence: { type: 'number' },
    }, required: ['claim', 'confidence'] } },
    summary: { type: 'string' },
    data_quality: { type: 'string', enum: ['high', 'medium', 'low'] },
  }, required: ['facts', 'data_quality'],
};

const FACTSHEET_SCHEMA = {
  type: 'object',
  properties: {
    verified_facts: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, confidence: { type: 'number' },
      sources: { type: 'array', items: { type: 'string' } },
    }, required: ['claim', 'confidence'] } },
    disputed_or_unverified: { type: 'array', items: { type: 'string' } },
    injuries_absences: { type: 'array', items: { type: 'string' } },
    form_summary: { type: 'string' },
    key_edges: { type: 'array', items: { type: 'string' } },
    data_quality: { type: 'string', enum: ['high', 'medium', 'low'] },
  }, required: ['verified_facts', 'form_summary', 'data_quality'],
};

const MARKETS_SCHEMA = {
  type: 'object',
  properties: {
    opportunities: { type: 'array', items: { type: 'object', properties: {
      market: { type: 'string' }, pick: { type: 'string' },
      bookmaker: { type: 'string' }, decimal_odds: { type: 'number' },
      est_probability: { type: 'number' }, rationale: { type: 'string' },
      based_on: { type: 'array', items: { type: 'string' } },
      sources: { type: 'array', items: { type: 'string' } },
    }, required: ['market', 'pick', 'decimal_odds', 'est_probability'] } },
  }, required: ['opportunities'],
};

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    fixture_confirmed: { type: 'boolean' }, odds_plausible: { type: 'boolean' },
    reasoning_sound: { type: 'boolean' }, confidence: { type: 'number' },
    issues: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string', enum: ['keep', 'drop'] },
  }, required: ['verdict', 'confidence'],
};

const COORD_SCHEMA = {
  type: 'object',
  properties: {
    ranked: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'number' }, rank: { type: 'number' },
      reason: { type: 'string' },
      correlation_warning: { type: 'string' },
    }, required: ['id', 'rank'] } },
    notes: { type: 'string' },
  }, required: ['ranked'],
};

// ---------- Helpers coupon (JS pur, miroir de coupon.py) ----------
function* combos(arr, r, start = 0, acc = []) {
  if (acc.length === r) { yield acc.slice(); return; }
  for (let i = start; i < arr.length; i++) { acc.push(arr[i]); yield* combos(arr, r, i + 1, acc); acc.pop(); }
}
function prod(xs) { return xs.reduce((a, b) => a * b, 1); }
function distinctMatches(combo) {
  const keys = combo.map(c => c.matchKey); return new Set(keys).size === keys.length;
}
function buildCoupon(cands, tMin, tMax, minLegs, maxLegs, poolSize = 16) {
  const pool = cands.slice().sort((a, b) => b.prob - a.prob).slice(0, poolSize);
  let best = null, bestKey = null;
  for (let r = Math.max(1, minLegs); r <= maxLegs; r++) {
    for (const combo of combos(pool, r)) {
      if (!distinctMatches(combo)) continue;
      const total = prod(combo.map(c => c.odds));
      if (total < tMin) continue;
      if (tMax && total > tMax) continue;
      const joint = prod(combo.map(c => c.prob));
      const key = [joint, -r, -(total - tMin)];
      if (!best || key[0] > bestKey[0] ||
        (key[0] === bestKey[0] && key[1] > bestKey[1]) ||
        (key[0] === bestKey[0] && key[1] === bestKey[1] && key[2] > bestKey[2])) {
        best = combo; bestKey = key;
      }
    }
  }
  return best;
}

// ================= PHASE 1 : Découverte =================
phase('Découverte')
const sports = [
  { key: 'football', hint: "toutes ligues actives : championnats d'été, MLS, Brésil, Scandinavie, Asie, coupes, sélections, amicaux de préparation" },
  { key: 'tennis', hint: "tournois ATP/WTA/Challenger/ITF en cours, order of play du jour" },
  { key: 'basketball', hint: "NBA/Summer League, EuroLeague, ligues nationales, compétitions internationales" },
];
const discovered = await parallel(sports.map(s => () =>
  agent(
    `Recherche sur le web (WebSearch/WebFetch) les matchs de ${s.key} programmés ${DATE}. ` +
    `Couvre : ${s.hint}. Sources fiables uniquement (sites officiels, agrégateurs, presse). ` +
    `Rends UNIQUEMENT des matchs réels et vérifiables avec l'URL source. ` +
    `En cas de doute sur l'existence d'un match, ne l'inclus pas.`,
    { label: `discover:${s.key}`, phase: 'Découverte', schema: FIXTURES_SCHEMA }
  )
));
let matches = discovered.filter(Boolean).flatMap(d => d.matches || []);
const seen = new Set();
matches = matches.filter(m => {
  const k = `${m.sport}|${(m.home || '').toLowerCase()}|${(m.away || '').toLowerCase()}`;
  if (seen.has(k)) return false; seen.add(k); return true;
});
// Entrelacement par sport pour une couverture equilibree (le foot ne monopolise plus les places).
const bySport = { football: [], tennis: [], basketball: [] };
for (const m of matches) { (bySport[m.sport] || (bySport[m.sport] = [])).push(m); }
const inter = [];
let added = true;
while (inter.length < MAX_MATCHES && added) {
  added = false;
  for (const s of ['football', 'tennis', 'basketball']) {
    if (bySport[s] && bySport[s].length) {
      inter.push(bySport[s].shift()); added = true;
      if (inter.length >= MAX_MATCHES) break;
    }
  }
}
matches = inter.map((m, i) => ({ ...m, key: `${i}:${m.home} vs ${m.away}` }));
log(`${matches.length} match(s) réel(s) retenu(s) pour analyse approfondie.`);
if (matches.length === 0) {
  return { picks: [], coupon: null, disclaimer: DISCLAIMER,
    note: "Aucun match du jour confirmé sur le web. Rien à proposer." };
}

// ========= PHASES 2->4 : Recherche -> Consolidation -> Marchés (pipeline par match) =========
const perMatch = await pipeline(
  matches,
  // 2) Spécialistes en parallèle (barrière interne au match) -> faits
  (m) => parallel(SPECIALISTS.map(sp => () =>
    agent(
      `Match : ${m.home} vs ${m.away} (${m.competition}, ${m.sport}, ${DATE}).\n` +
      `Ton rôle : SPÉCIALISTE "${sp.key}". ${sp.ask(m)}\n` +
      `Recherche sur le web, distingue FAIT VÉRIFIÉ (avec source) et opinion, ` +
      `attribue une confiance [0..1] à chaque fait.`,
      { label: `${sp.key}:${m.home}-${m.away}`, phase: 'Recherche', schema: FACT_SCHEMA }
    ).then(r => ({ specialist: sp.key, ...(r || {}) }))
  )).then(facts => ({ m, facts: facts.filter(Boolean) })),

  // 3) Desk éditeur : les agents "échangent" -> réconciliation + vérification
  (r) => agent(
    `Tu es le DESK ÉDITEUR pour ${r.m.home} vs ${r.m.away} (${r.m.competition}). ` +
    `Voici les faits rapportés par 5 spécialistes (forme, compos, h2h, experts, marché) :\n` +
    JSON.stringify(r.facts).slice(0, 6000) + `\n\n` +
    `Réconcilie-les : garde les faits corroborés (idéalement 2+ sources), signale les ` +
    `contradictions, isole blessures/absences, résume la forme, et dégage les vrais ` +
    `angles (key_edges). Recoupe/vérifie sur le web les faits douteux mais décisifs.`,
    { label: `desk:${r.m.home}-${r.m.away}`, phase: 'Consolidation', schema: FACTSHEET_SCHEMA }
  ).then(sheet => ({ m: r.m, sheet })),

  // 4) Analyse de TOUS les marchés à partir de la fiche de faits partagée
  (r) => agent(
    `Tu es l'ANALYSTE MARCHÉS pour ${r.m.home} vs ${r.m.away} (${r.m.sport}). ` +
    `Base-toi UNIQUEMENT sur cette fiche de faits vérifiés :\n` +
    JSON.stringify(r.sheet).slice(0, 6000) + `\n\n` +
    `Passe en revue TOUS les marchés pertinents : ${MARKETS[r.m.sport]}. ` +
    `Pour chaque marché intéressant, récupère la cote réelle chez un bookmaker, ` +
    `estime honnêtement la probabilité, et ne garde que les opportunités de VALUE ` +
    `(proba estimée > proba implicite de la cote). Privilégie les cotes exploitables ` +
    `pour un simple (${SINGLE_MIN}-${SINGLE_MAX}) ou une jambe de combiné. ` +
    `Cite les sources. N'invente aucune cote.`,
    { label: `markets:${r.m.home}-${r.m.away}`, phase: 'Marchés', schema: MARKETS_SCHEMA }
  ).then(mk => ({ m: r.m, sheet: r.sheet, markets: (mk && mk.opportunities) || [] }))
);

// Aplatir toutes les opportunités
let opps = [];
let idc = 0;
for (const r of perMatch.filter(Boolean)) {
  for (const o of r.markets) {
    const p = Number(o.est_probability) || 0;
    const d = Number(o.decimal_odds) || 0;
    if (p <= 0 || d <= 1) continue;
    opps.push({
      id: idc++, matchKey: r.m.key, match: `${r.m.home} vs ${r.m.away}`,
      sport: r.m.sport, competition: r.m.competition,
      market: o.market, pick: o.pick, odds: d, prob: p,
      edge: p * d - 1, rationale: o.rationale || '',
      sources: o.sources || [], data_quality: (r.sheet && r.sheet.data_quality) || 'low',
    });
  }
}
log(`${opps.length} opportunité(s) de marché détectée(s) sur ${perMatch.length} match(s).`);

// ================= PHASE 5 : Vérification adversariale =================
phase('Vérification')
// On vérifie en priorité les meilleures value (borne le coût).
const toVerify = opps.filter(o => o.edge > 0).sort((a, b) => b.edge - a.edge).slice(0, 12);
const verified = (await parallel(toVerify.map(o => () =>
  agent(
    `Vérifie de façon ADVERSARIALE cette opportunité :\n` +
    `${o.match} (${o.competition}) — ${o.market} / ${o.pick} @ ${o.odds}.\n` +
    `Argument : ${o.rationale}\n` +
    `Contrôle sur le web : (1) le match a-t-il lieu ${DATE} ? ` +
    `(2) la cote ${o.odds} est-elle réelle et plausible ? ` +
    `(3) le raisonnement tient-il (blessure majeure ignorée ? enjeu ? piège ?). ` +
    `Sois sceptique : au moindre doute sérieux, verdict=drop.`,
    { label: `verify:${o.id}`, phase: 'Vérification', schema: VERDICT_SCHEMA }
  ).then(v => ({ ...o, verdict: v }))
))).filter(Boolean).filter(o => o.verdict && o.verdict.verdict === 'keep')
  .map(o => ({ ...o, confidence: o.verdict.confidence || 0 }));
log(`${verified.length} opportunité(s) survivante(s) après vérification.`);

if (verified.length === 0) {
  return { date: DATE, picks: [], coupon: null, considered: matches.length,
    disclaimer: DISCLAIMER,
    note: "Aucune opportunité n'a passé la vérification. Mieux vaut ne pas parier." };
}

// ================= PHASE 6 : Table ronde (échange global) =================
phase('Table ronde')
const coord = await agent(
  `Tu es le COORDINATEUR. Voici les opportunités vérifiées de tous les matchs du jour :\n` +
  JSON.stringify(verified.map(o => ({
    id: o.id, match: o.match, sport: o.sport, market: o.market, pick: o.pick,
    odds: o.odds, est_prob: o.prob, edge: Number(o.edge.toFixed(3)),
    confidence: o.confidence, dq: o.data_quality,
  }))).slice(0, 8000) + `\n\n` +
  `Classe-les de la meilleure à la moins bonne pour bâtir : (a) au plus ${MAX_PICKS} ` +
  `paris SIMPLES cote ${SINGLE_MIN}-${SINGLE_MAX} (option plus risquée), et (b) un ` +
  `COUPON combiné cote totale ${COUPON_TARGET}-${COUPON_MAX} (option plus sûre : ` +
  `privilégie les sélections à HAUTE probabilité). ` +
  `Pénalise les data_quality basses et signale toute CORRÉLATION entre sélections ` +
  `(même match, même compétition, issues liées) à éviter dans un combiné.`,
  { label: 'coordinateur', phase: 'Table ronde', schema: COORD_SCHEMA }
);
const rankById = new Map((coord.ranked || []).map(x => [x.id, x.rank]));
for (const o of verified) o.rank = rankById.has(o.id) ? rankById.get(o.id) : 999;
verified.sort((a, b) => a.rank - b.rank || b.confidence - a.confidence || b.edge - a.edge);

// ================= PHASE 7 : Synthèse (coupon + singles) =================
phase('Synthèse')
// Singles cote 5-7, matchs distincts
const singles = [];
const usedForSingles = new Set();
for (const o of verified) {
  if (o.odds >= SINGLE_MIN && o.odds <= SINGLE_MAX && !usedForSingles.has(o.matchKey)) {
    singles.push(o); usedForSingles.add(o.matchKey);
    if (singles.length >= MAX_PICKS) break;
  }
}
// Coupon combiné cote ~COUPON_TARGET : privilégie les sélections les plus probables
const couponLegs = buildCoupon(
  verified.map(o => ({ matchKey: o.matchKey, odds: o.odds, prob: o.prob, ref: o })),
  COUPON_TARGET, COUPON_MAX, 2, 5
);
const coupon = couponLegs ? {
  legs: couponLegs.map(c => ({
    match: c.ref.match, market: c.ref.market, pick: c.ref.pick,
    odds: c.ref.odds, est_prob: c.ref.prob, confidence: c.ref.confidence,
  })),
  total_odds: Number(prod(couponLegs.map(c => c.odds)).toFixed(2)),
  joint_prob: Number(prod(couponLegs.map(c => c.prob)).toFixed(3)),
} : null;

const writeup = await agent(
  `Rédige en français une note claire et HONNÊTE pour le parieur, à partir de ces données :\n` +
  `SINGLES (cote ${SINGLE_MIN}-${SINGLE_MAX}, option plus risquée): ${JSON.stringify(singles.map(s => ({ match: s.match, market: s.market, pick: s.pick, odds: s.odds, est_prob: s.prob, edge: Number(s.edge.toFixed(3)), confidence: s.confidence, why: s.rationale })))}\n` +
  `COUPON (cote totale ${COUPON_TARGET}-${COUPON_MAX}, option plus sûre): ${JSON.stringify(coupon)}\n` +
  `Rappels obligatoires : proba réelle de gain, aucune garantie, gestion de mise ` +
  `raisonnable, et l'avertissement suivant intégré : "${DISCLAIMER}". ` +
  `Ton factuel, pas de survente, pas de "safe".`,
  { label: 'redaction', phase: 'Synthèse' }
);

return {
  date: DATE,
  considered: matches.length,
  opportunities: opps.length,
  verified: verified.length,
  singles,
  coupon,
  writeup,
  disclaimer: DISCLAIMER,
};
