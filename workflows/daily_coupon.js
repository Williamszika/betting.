export const meta = {
  name: 'daily-singles-research',
  description: 'Deep-research: trouve les matchs du jour sur le web, vérifie, et propose au plus 2 paris SIMPLES à cote ~5-7 (estimations, pas des garanties)',
  phases: [
    { title: 'Découverte', detail: 'Recherche web des matchs du jour (foot/tennis/basket)' },
    { title: 'Recherche', detail: 'Un agent par match : forme, blessures, avis experts, cote' },
    { title: 'Vérification', detail: 'Contrôle adversarial de chaque pari candidat' },
    { title: 'Synthèse', detail: 'Sélection d\'au plus 2 simples cote ~5-7 + avertissements' },
  ],
}

// ---- Paramètres (surchargées via `args`) ----
const DATE = (args && args.date) || 'aujourd\'hui'
const TARGET_MIN = (args && args.oddsMin) || 5.0
const TARGET_MAX = (args && args.oddsMax) || 7.0
const MAX_PICKS = (args && args.maxPicks) || 2
const MAX_MATCHES = (args && args.maxMatches) || 12

const DISCLAIMER =
  'ESTIMATIONS statistiques, PAS des certitudes. Aucun pari n\'est « sûr » : ' +
  'un simple à cote 5 reste ~1 chance sur 5. Ne miser que ce qu\'on peut perdre. ' +
  'Jeu interdit aux mineurs — aide : joueurs-info-service.fr, 09 74 75 13 13.'

const FIXTURES_SCHEMA = {
  type: 'object',
  properties: {
    matches: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          sport: { type: 'string', enum: ['football', 'tennis', 'basketball'] },
          competition: { type: 'string' },
          home: { type: 'string' },
          away: { type: 'string' },
          start_local: { type: 'string' },
          source_url: { type: 'string' },
        },
        required: ['sport', 'competition', 'home', 'away'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['matches'],
}

const PICK_SCHEMA = {
  type: 'object',
  properties: {
    has_pick: { type: 'boolean' },
    market: { type: 'string' },
    pick: { type: 'string' },
    bookmaker_odds: { type: 'number' },
    est_probability: { type: 'number' },
    rationale: { type: 'string' },
    key_factors: { type: 'array', items: { type: 'string' } },
    red_flags: { type: 'array', items: { type: 'string' } },
    data_quality: { type: 'string', enum: ['high', 'medium', 'low'] },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['has_pick', 'data_quality'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    odds_in_range: { type: 'boolean' },
    reasoning_sound: { type: 'boolean' },
    fixture_confirmed: { type: 'boolean' },
    confidence: { type: 'number' },
    issues: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string', enum: ['keep', 'drop'] },
  },
  required: ['verdict', 'confidence'],
}

// ---- Phase 1 : Découverte des matchs du jour ----
phase('Découverte')
const sports = [
  { key: 'football', hint: 'toutes ligues actives ce jour : championnats d\'été, MLS, Brésil, Scandinavie, coupes, internationaux, amicaux' },
  { key: 'tennis', hint: 'tournois ATP/WTA/Challenger en cours, order of play du jour' },
  { key: 'basketball', hint: 'NBA (ou Summer League), EuroLeague, ligues nationales, internationaux' },
]

const discovered = await parallel(sports.map(s => () =>
  agent(
    `Recherche sur le web les matchs de ${s.key} programmés ${DATE}. ` +
    `Cible : ${s.hint}. Utilise WebSearch/WebFetch sur des sources fiables ` +
    `(sites officiels de ligues, agrégateurs de résultats, presse sportive). ` +
    `Rends une liste de matchs RÉELS et vérifiables avec l'URL source. ` +
    `Ne rends AUCUN match inventé ; si tu n'es pas sûr, ne l'inclus pas.`,
    { label: `discover:${s.key}`, phase: 'Découverte', schema: FIXTURES_SCHEMA }
  )
))

let matches = discovered.filter(Boolean).flatMap(d => d.matches || [])
// Dédoublonnage simple par (home,away)
const seen = new Set()
matches = matches.filter(m => {
  const k = `${m.sport}|${(m.home||'').toLowerCase()}|${(m.away||'').toLowerCase()}`
  if (seen.has(k)) return false
  seen.add(k)
  return true
}).slice(0, MAX_MATCHES)

log(`${matches.length} match(s) réel(s) découvert(s) pour la recherche approfondie.`)
if (matches.length === 0) {
  return { picks: [], disclaimer: DISCLAIMER,
    note: 'Aucun match du jour n\'a pu être confirmé sur le web. Rien à proposer.' }
}

// ---- Phases 2+3 : Recherche puis vérification, en pipeline ----
const researched = await pipeline(
  matches,
  // Étape 2 : recherche approfondie d'un pari simple cote ~5-7
  (m) => agent(
    `Analyse en profondeur ce match : ${m.home} vs ${m.away} (${m.competition}, ${m.sport}). ` +
    `Cherche sur le web : forme récente, confrontations directes, blessures/absences, ` +
    `contexte (enjeu, calendrier, météo), et AVIS D'EXPERTS (presse, réseaux sociaux). ` +
    `Trouve UN pari à cote décimale entre ${TARGET_MIN} et ${TARGET_MAX} chez un bookmaker ` +
    `(marché au choix : 1X2, handicap, over/under, vainqueur set, etc.). ` +
    `Estime honnêtement sa probabilité réelle et n'affirme JAMAIS une certitude. ` +
    `Si aucun pari raisonnable dans cette fourchette, mets has_pick=false. ` +
    `Cite tes sources (URLs).`,
    { label: `research:${m.home}-${m.away}`, phase: 'Recherche', schema: PICK_SCHEMA }
  ),
  // Étape 3 : vérification adversariale du candidat
  (pick, m) => {
    if (!pick || !pick.has_pick) return { pick, m, verdict: { verdict: 'drop', confidence: 0 } }
    return agent(
      `Vérifie de façon adversariale ce pari : ${m.home} vs ${m.away} — ` +
      `${pick.market} / ${pick.pick} @ ${pick.bookmaker_odds}. ` +
      `Contrôle sur le web : (1) le match a-t-il bien lieu ${DATE} ? ` +
      `(2) la cote ${pick.bookmaker_odds} est-elle plausible/réelle et dans [${TARGET_MIN},${TARGET_MAX}] ? ` +
      `(3) le raisonnement tient-il (pas de blessure majeure ignorée, match à enjeu, etc.) ? ` +
      `Sois sceptique : en cas de doute, verdict=drop.`,
      { label: `verify:${m.home}-${m.away}`, phase: 'Vérification', schema: VERDICT_SCHEMA }
    ).then(v => ({ pick, m, verdict: v }))
  }
)

const kept = researched
  .filter(Boolean)
  .filter(r => r.pick && r.pick.has_pick && r.verdict && r.verdict.verdict === 'keep')
  .map(r => ({
    match: `${r.m.home} vs ${r.m.away}`,
    sport: r.m.sport,
    competition: r.m.competition,
    market: r.pick.market,
    pick: r.pick.pick,
    odds: r.pick.bookmaker_odds,
    est_probability: r.pick.est_probability,
    edge: (r.pick.est_probability || 0) * (r.pick.bookmaker_odds || 0) - 1,
    rationale: r.pick.rationale,
    red_flags: r.pick.red_flags || [],
    data_quality: r.pick.data_quality,
    confidence: r.verdict.confidence,
    sources: r.pick.sources || [],
  }))
  // Classer par (confiance de vérif, value, probabilité)
  .sort((a, b) =>
    (b.confidence - a.confidence) ||
    (b.edge - a.edge) ||
    ((b.est_probability||0) - (a.est_probability||0))
  )

// ---- Phase 4 : Synthèse ----
phase('Synthèse')
const finalists = kept.slice(0, MAX_PICKS)
log(`${kept.length} pari(s) validé(s) ; ${finalists.length} retenu(s) (max ${MAX_PICKS}).`)

return {
  date: DATE,
  odds_band: [TARGET_MIN, TARGET_MAX],
  picks: finalists,
  considered: matches.length,
  validated: kept.length,
  disclaimer: DISCLAIMER,
}
