export const meta = {
  name: 'panel-predict',
  description: 'Panel d\'agents en 7 phases : découverte, contexte, filtre marché, contradiction, synthèse',
  whenToUse: "Prédiction quotidienne complète. Les agents n'apportent QUE des faits textuels datés et sourcés ; tout chiffre vient du code.",
  phases: [
    { title: 'Contexte', detail: '1 agent par match : absences, compos, enjeu, mouvement de cotes, conditions' },
    { title: 'Contradiction', detail: 'adversaire structuré, checklist fermée, mémoire des leçons injectée' },
    { title: 'Synthèse', detail: 'coupon final, corrélations entre jambes, justification écrite' },
  ],
}

// ─────────────────────────────────────────────────────────────────────────────
// PANEL DE PRÉDICTION — les 7 phases
//
// Phases 0, 1, 2, 4, 7 sont du CODE (hors de ce fichier) :
//   0  mémoire + porte papier    scripts/lessons_rules.py, scripts/protocol.py
//   1  découverte des matchs     scripts/daily_engine.py
//   2  chiffres déterministes    sportsbet.{footballdata, markets, rolling}
//   4  filtre de value           scripts/edge_scan.py
//   7  registre + CLV + leçons   scripts/protocol.py, data/lessons.md
//
// Ce fichier n'orchestre que les phases TEXTUELLES — 3, 5, 6 — parce que ce
// sont les seules où un agent apporte quelque chose qu'un programme ne sait
// pas faire : lire l'actualité, contredire, rédiger.
//
// LA RÈGLE QUI GOUVERNE TOUT : aucun agent ne produit de probabilité, de λ ni
// d'edge. Le 29/07, sept propositions sur sept ont été rejetées pour edges
// fabriqués (« λ Poisson rétro-ingénieré », « edge inversé au signe annoncé »).
// Un agent qui ne calcule pas ne peut pas fabriquer.
//
// CE QUE LES MESURES DISENT DE CETTE ARCHITECTURE (35 000 matchs backtestés) :
//   • la calibration du modèle est un acquis réel     0,8 pt d'erreur
//   • la sélection de paris reste adverse            ~12 pts sur les retenus
//   • le rétrécissement vers le marché AGGRAVE le ROI (il concentre l'erreur)
// Ce panel produit donc des PRÉDICTIONS fiables, pas un avantage démontré.
// ─────────────────────────────────────────────────────────────────────────────

let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}

const DATE = A.date || "aujourd'hui"
const BOOK = A.bookmaker || 'bet365'
const LIGNES = Array.isArray(A.shortlist) ? A.shortlist : []
const SOFT = A.softBlock || ''
const HARD = Array.isArray(A.hardRules) ? A.hardRules : []

if (!LIGNES.length) {
  return { date: DATE, note: "Rien à analyser — l'étage chiffré n'a produit aucune ligne.", coupon: [] }
}

// ── Phase 3 — l'agent contexte ───────────────────────────────────────────────
// Cinq catégories, pas une de plus. Chaque fait doit être DATÉ et SOURCÉ, sinon
// le code le rejette avant qu'il n'atteigne le modèle. Ce qui n'est pas demandé
// ici est activement nuisible : les séries narratives (« invaincu depuis 8
// matchs ») sont du cherry-picking, la possession corrèle mal avec les buts, et
// les déclarations d'avant-match sont du bruit pur. Chaque donnée inutile est un
// point d'ancrage de plus pour le contradicteur en aval.

const FAIT_SCHEMA = {
  type: 'object',
  properties: {
    categorie: {
      type: 'string',
      enum: ['absence', 'rotation', 'enjeu', 'mouvement_cote', 'conditions'],
    },
    fait: { type: 'string' },
    source: { type: 'string' },       // média nommé, pas « selon des rumeurs »
    date: { type: 'string' },         // AAAA-MM-JJ — non daté = rejeté
    equipe: { type: 'string', enum: ['domicile', 'exterieur', 'les_deux'] },
    poids: { type: 'string', enum: ['majeur', 'modere', 'mineur'] },
  },
  required: ['categorie', 'fait', 'source', 'date'],
}

const CONTEXTE_SCHEMA = {
  type: 'object',
  properties: {
    fixture_confirmee: { type: 'boolean' },
    fixture_note: { type: 'string' },
    context_flag: {
      type: 'string',
      enum: ['normal', 'finale', 'barrage', 'sans_enjeu', 'tie_plie', 'derby'],
    },
    faits: { type: 'array', items: FAIT_SCHEMA },
    cote_relevee: { type: 'number' },
    cote_source: { type: 'string' },
    cote_a_bouge: { type: 'boolean' },
    donnees_minces: { type: 'boolean' },   // championnat mal couvert ?
  },
  required: ['fixture_confirmee', 'context_flag', 'faits'],
}

phase('Contexte')
log(`Phase 3 — ${LIGNES.length} agent(s) contexte, un par match.`)

const contextes = (await parallel(LIGNES.map((s) => () =>
  agent(
    `Tu collectes des FAITS sur un match de football. Tu ne calcules RIEN : ` +
    `aucune probabilité, aucun λ, aucun edge, aucun pronostic. Ces chiffres ` +
    `viennent du code et t'affichent seulement le contexte de ta recherche.\n\n` +
    `MATCH (${DATE}) : ${s.home} vs ${s.away} — ${s.country}\n` +
    `Le moteur a chiffré : ${s.label} à ${(s.prob * 100).toFixed(1)} %, ` +
    `cote minimale utile ${s.min_odds}.\n\n` +
    `TES CINQ CATÉGORIES, aucune autre :\n` +
    `1) ABSENCE — blessés, suspendus, sélections internationales. NOMME le joueur ` +
    `et son rôle : perdre un buteur titulaire n'est pas perdre un remplaçant.\n` +
    `2) ROTATION — turnover annoncé, gardien n°2, échéance européenne proche.\n` +
    `3) ENJEU — renseigne context_flag. Un match sans enjeu, une finale, un ` +
    `barrage ou un tie déjà plié cassent les hypothèses du modèle.\n` +
    `4) MOUVEMENT DE COTE — si la cote a bougé de plus de 10 %, cherche POURQUOI. ` +
    `Un mouvement inexpliqué signale une information que le marché a et que nous ` +
    `n'avons pas.\n` +
    `5) CONDITIONS — météo violente, terrain impraticable, huis clos. UNIQUEMENT ` +
    `si exceptionnel ; une météo ordinaire n'est pas un fait.\n\n` +
    `FIXTURE : le match a-t-il bien lieu ? Report, annulation, déplacement, ` +
    `forfait → fixture_confirmee=false. C'est un veto à lui seul.\n` +
    `COTE : relève la cote réelle de ce marché chez ${BOOK} ou un comparateur. ` +
    `Introuvable → cote_relevee=0. Ne devine JAMAIS un prix.\n\n` +
    `RÈGLES DE FORME, strictes :\n` +
    `• chaque fait porte une SOURCE nommée et une DATE. Sans les deux, ne le ` +
    `rapporte pas — le code le rejettera.\n` +
    `• un fait d'absence de plus de 7 jours est périmé : re-vérifie ou écarte.\n` +
    `• NE RAPPORTE PAS : les séries (« invaincu depuis 8 matchs »), la ` +
    `possession, les corners historiques, les déclarations d'entraîneur. Ce sont ` +
    `des ancrages sans valeur prédictive.\n` +
    `• en l'absence de fait dans une catégorie, ne remplis rien. Le silence est ` +
    `une information ; l'invention n'en est pas une.`,
    { label: `contexte:${s.home}`, phase: 'Contexte', schema: CONTEXTE_SCHEMA }
  ).then((v) => ({ ...s, ctx: v }))
))).filter(Boolean)

// ── Filtres CODE entre phase 3 et phase 5 ────────────────────────────────────
// Les faits non datés ou non sourcés n'atteignent jamais le contradicteur.
const nonDate = (f) => !f || !f.date || !f.source || !/\d{4}-\d{2}-\d{2}/.test(f.date)

for (const c of contextes) {
  const bruts = (c.ctx && c.ctx.faits) || []
  c.faitsRetenus = bruts.filter((f) => !nonDate(f))
  c.faitsRejetes = bruts.length - c.faitsRetenus.length
  if (c.faitsRejetes) log(`  ⌫ ${c.home} : ${c.faitsRejetes} fait(s) sans date ou sans source, rejeté(s)`)
}

// VETOS — mêmes règles que la cascade, appliquées ici avant toute discussion.
const MARCHES_BUTS = /over|under|btts|goal|but|total/i
const MARCHES_1X2 = /^(1|X|2|DC |DNB )/

function veto(c) {
  if (c.ctx && c.ctx.fixture_confirmee === false)
    return `fixture non confirmée — ${(c.ctx.fixture_note || '').slice(0, 90)}`
  const f = (c.ctx && c.ctx.context_flag) || 'normal'
  const m = c.market || ''
  if (f === 'sans_enjeu' && MARCHES_1X2.test(m))
    return 'match sans enjeu — le favori 1X2 perd son avantage (leçon France 6-4)'
  if ((f === 'finale' || f === 'barrage') && MARCHES_1X2.test(m))
    return 'finale ou barrage — le 1X2 90 min est un piège (leçon Espagne 0-0 à 90)'
  if (f === 'tie_plie' && MARCHES_BUTS.test(m))
    return 'tie déjà décidé — les marchés de buts s\'effondrent (leçon Craiova 1-0)'
  return ''
}

const survivants = [], ecartes = []
for (const c of contextes) {
  const v = veto(c)
  if (v) ecartes.push({ ...c, raison: v })
  else survivants.push(c)
}
for (const e of ecartes) log(`  ✂ ${e.home} – ${e.away} [${e.market}] : ${e.raison}`)

if (!survivants.length) {
  return {
    date: DATE, coupon: [], ecartes: ecartes.map((e) => ({ match: `${e.home} – ${e.away}`, raison: e.raison })),
    writeup: `Aucune ligne ne survit à la vérification du ${DATE}. Rien à proposer — c'est un résultat, pas un échec.`,
  }
}

// ── Phase 5 — le contradicteur ───────────────────────────────────────────────
// Checklist FERMÉE. Une critique libre produit des objections décoratives ; une
// liste de questions fermées produit des réponses vérifiables. La mémoire des
// leçons entre ici — c'est le seul endroit où le système parle à ses agents de
// ce qu'il a appris de ses pertes.

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    tient: { type: 'boolean' },
    faits_dates: { type: 'boolean' },
    flag_compatible: { type: 'boolean' },
    lecons_respectees: { type: 'boolean' },
    cote_credible: { type: 'boolean' },
    objection_principale: { type: 'string' },
    confiance: { type: 'number' },
  },
  required: ['tient', 'faits_dates', 'flag_compatible', 'lecons_respectees'],
}

phase('Contradiction')
log(`Phase 5 — contradiction adversariale sur ${survivants.length} ligne(s).`)

const juges = (await parallel(survivants.map((c) => () =>
  agent(
    `Tu es le CONTRADICTEUR. Ton rôle n'est pas d'approuver : c'est de chercher ` +
    `ce qui cloche. Une sélection qui te paraît correcte doit quand même être ` +
    `attaquée sur chaque point de la liste.\n\n` +
    `SÉLECTION : ${c.home} vs ${c.away} — ${c.label}\n` +
    `Probabilité du moteur : ${(c.prob * 100).toFixed(1)} % · cote minimale ${c.min_odds} · ` +
    `cote relevée ${(c.ctx && c.ctx.cote_relevee) || 'introuvable'}\n` +
    `Contexte déclaré : ${(c.ctx && c.ctx.context_flag) || 'normal'}\n` +
    `Faits retenus : ${JSON.stringify(c.faitsRetenus || []).slice(0, 1200)}\n\n` +
    (HARD.length ? `RÈGLES DURES ACTIVES :\n${JSON.stringify(HARD).slice(0, 1500)}\n\n` : '') +
    (SOFT ? `MÉMOIRE DES PERTES PASSÉES :\n${SOFT}\n\n` : '') +
    `TA CHECKLIST — réponds à CHAQUE point, aucune critique libre :\n` +
    `① faits_dates : chaque fait porte-t-il une source nommée et une date de ` +
    `moins de 7 jours ?\n` +
    `② flag_compatible : le context_flag déclaré autorise-t-il CE marché ? ` +
    `(sans_enjeu interdit le 1X2 ; finale/barrage interdit le 1X2 90 min ; ` +
    `tie_plie interdit les marchés de buts)\n` +
    `③ lecons_respectees : une règle de la mémoire ci-dessus s'oppose-t-elle à ` +
    `cette sélection ? Cite-la si oui.\n` +
    `④ cote_credible : la cote relevée est-elle plausible pour cette probabilité, ` +
    `et vient-elle d'une source nommée ?\n\n` +
    `tient=false dès qu'UN point échoue. Au moindre doute sérieux, tient=false : ` +
    `ne rien proposer coûte zéro, proposer à tort coûte la mise ET la confiance.`,
    { label: `contradiction:${c.home}`, phase: 'Contradiction', schema: VERDICT_SCHEMA }
  ).then((v) => ({ ...c, jug: v }))
))).filter(Boolean)

const retenus = juges.filter((j) => j.jug && j.jug.tient === true)
const rejetes = juges.filter((j) => !retenus.includes(j))
for (const r of rejetes)
  log(`  ✂ ${r.home} [contradiction] : ${((r.jug && r.jug.objection_principale) || 'échec checklist').slice(0, 100)}`)

log(`${retenus.length}/${LIGNES.length} ligne(s) survivent aux deux filtres.`)

// ── Phase 6 — synthèse ───────────────────────────────────────────────────────
phase('Synthèse')

const writeup = await agent(
  `Rédige en français la note de prédiction du ${DATE}. Mode PAPER : 0 € misé.\n\n` +
  `RETENUES : ${JSON.stringify(retenus.map((r) => ({
    match: `${r.home} – ${r.away}`, pays: r.country, marche: r.label,
    proba_moteur: `${(r.prob * 100).toFixed(1)}%`, cote_min: r.min_odds,
    cote: (r.ctx && r.ctx.cote_relevee) || 'introuvable',
    contexte: (r.ctx && r.ctx.context_flag) || 'normal',
    faits: (r.faitsRetenus || []).slice(0, 4),
    confiance_contradicteur: r.jug && r.jug.confiance,
  }))).slice(0, 4000)}\n` +
  `ÉCARTÉES : ${JSON.stringify([...ecartes, ...rejetes].map((e) => ({
    match: `${e.home} – ${e.away}`,
    raison: e.raison || (e.jug && e.jug.objection_principale) || 'checklist',
  }))).slice(0, 1200)}\n\n` +
  `RÈGLES DE RÉDACTION :\n` +
  `- Les probabilités viennent du MOTEUR. Ne les modifie pas, ne les réinterprète pas.\n` +
  `- CORRÉLATIONS : si plusieurs sélections portent sur des matchs liés (même ` +
  `compétition à la même heure, ou deux marchés de buts sur des affiches ` +
  `comparables), signale-le. Deux paris corrélés présentés comme deux paris ` +
  `distincts est une fausse diversification.\n` +
  `- Distingue VALIDÉE (le match a lieu, le raisonnement tient) et JOUABLE ` +
  `(en plus, la cote dépasse le seuil de rentabilité, taxe comprise).\n` +
  `- Si rien n'est jouable, dis-le franchement. C'est un résultat utile.\n` +
  `- Rappelle ce que le banc d'essai a mesuré : sur 35 000 matchs, ce type de ` +
  `modèle est bien calibré (0,8 point d'erreur) mais n'a PAS démontré d'avantage ` +
  `sur le marché. Ces prédictions sont des estimations honnêtes, pas des signaux ` +
  `de profit.\n` +
  `- ESTIMATIONS, pas des certitudes. Aucune incitation à miser.`,
  { label: 'synthese', phase: 'Synthèse' }
)

return {
  date: DATE,
  analysees: LIGNES.length,
  coupon: retenus.map((r) => ({
    country: r.country, match: `${r.home} – ${r.away}`,
    market: r.market, label: r.label, prob: r.prob,
    min_odds: r.min_odds,
    odds: (r.ctx && r.ctx.cote_relevee) || null,
    odds_source: (r.ctx && r.ctx.cote_source) || '',
    jouable: !!(r.ctx && r.ctx.cote_relevee >= r.min_odds),
    context_flag: (r.ctx && r.ctx.context_flag) || 'normal',
    faits: r.faitsRetenus || [],
    confiance: r.jug && r.jug.confiance,
  })),
  ecartes: [...ecartes, ...rejetes].map((e) => ({
    match: `${e.home} – ${e.away}`,
    raison: e.raison || (e.jug && e.jug.objection_principale) || 'checklist',
  })),
  faits_rejetes: contextes.reduce((n, c) => n + (c.faitsRejetes || 0), 0),
  writeup,
  disclaimer: "ESTIMATIONS statistiques, PAS des certitudes. Mode PAPER : 0 € misé. " +
    "Sur 35 000 matchs backtestés, ce modèle est bien calibré mais n'a pas démontré " +
    "d'avantage sur le marché. Aide : joueurs-info-service.fr, 09 74 75 13 13.",
}
