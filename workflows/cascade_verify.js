export const meta = {
  name: 'cascade-verify',
  description: 'Étage 2 : vérification contextuelle des lignes déjà chiffrées par le moteur',
  whenToUse: "Après scripts/daily_engine.py --json. Les agents ne calculent RIEN : ils vérifient le contexte réel (fixture, blessures, enjeu) et la cote Betano.",
  phases: [
    { title: 'Vérification', detail: '1 agent par ligne : fixture, contexte, cote Betano' },
    { title: 'Verdict', detail: 'synthèse : ce qui survit, ce qui tombe' },
  ],
}

// ─────────────────────────────────────────────────────────────────────────────
// CASCADE — ÉTAGE 2
//
// L'étage 1 (scripts/daily_engine.py) a déjà fait tout le calcul :
//   40 matchs balayés, 146 marchés, probabilités issues du code (Poisson +
//   Dixon-Coles), contrôlées contre ClubElo, filtrées par fourchette de cotes.
//
// Les agents ici ne produisent AUCUNE probabilité. Interdiction absolue.
// Leur seul rôle : ce que le code ne peut pas savoir —
//   • le match a-t-il vraiment lieu (report, huis clos, forfait) ?
//   • une info de dernière minute invalide-t-elle la ligne (blessure, turnover) ?
//   • l'enjeu est-il atypique (match sans enjeu, tie déjà plié, finale) ?
//   • quelle est la COTE RÉELLE chez Betano, et dépasse-t-elle le seuil ?
// ─────────────────────────────────────────────────────────────────────────────

let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}

const DATE = A.date || "aujourd'hui"
const BOOK = A.bookmaker || 'Betano'
const DOMAIN = A.domain || 'betano.de'
const SHORTLIST = Array.isArray(A.shortlist) ? A.shortlist : []
const SOFT = A.softBlock ? `\n${A.softBlock}\n` : ''

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['keep', 'drop'] },
    confidence: { type: 'number' },
    fixture_confirmed: { type: 'boolean' },
    context_flag: { type: 'string', enum: ['normal', 'finale', 'barrage', 'sans_enjeu', 'tie_plie', 'derby'] },
    betano_odds: { type: 'number' },          // cote relevée (0 si introuvable)
    odds_source: { type: 'string' },
    beats_min_odds: { type: 'boolean' },      // cote relevée >= min_odds du moteur ?
    // Probabilité IMPLICITE DU MARCHÉ, marge retirée. C'est le seul chiffre qui
    // dise si le modèle apporte une information ou s'il récite le consensus.
    market_prob: { type: 'number' },          // 0 si aucune cote de référence
    market_ref: { type: 'string' },           // bookmaker + cotes brutes + marge
    context_notes: { type: 'array', items: { type: 'string' } },
    issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'confidence', 'fixture_confirmed'],
}

if (!SHORTLIST.length) {
  return { date: DATE, note: "Shortlist vide — l'étage 1 n'a rien produit.", verified: [] }
}

phase('Vérification')
log(`Étage 2 : vérification contextuelle de ${SHORTLIST.length} ligne(s) déjà chiffrée(s).`)

const checked = (await parallel(SHORTLIST.map((s) => () =>
  agent(
    `Tu VÉRIFIES une prédiction déjà calculée par notre moteur statistique. ` +
    `Tu ne recalcules RIEN et tu ne proposes AUCUNE probabilité — ce n'est pas ton rôle.\n\n` +
    `LIGNE À VÉRIFIER (${DATE}) :\n` +
    `  Match   : ${s.home} vs ${s.away} (${s.country})\n` +
    `  Marché  : ${s.label} [${s.market}]\n` +
    `  Moteur  : probabilité ${(s.prob * 100).toFixed(1)}% | cote juste ${s.fair_odds} | ` +
    `COTE MINIMALE UTILE ${s.min_odds} (taxe 5,3 % incluse)\n` +
    `  λ estimés : ${s.lambda_home} – ${s.lambda_away} | écart avec ClubElo : ${(s.clubelo_gap * 100).toFixed(1)} pts\n\n` +
    `TES 4 CONTRÔLES, sur le web :\n` +
    `1) FIXTURE : le match a-t-il bien lieu le ${DATE} et est-il ENCORE À VENIR ? ` +
    `Reporté, annulé, déplacé, huis clos, forfait → fixture_confirmed=false et verdict=drop.\n` +
    `2) CONTEXTE : une information de dernière minute invalide-t-elle cette ligne ? ` +
    `Blessures/suspensions majeures, gardien remplaçant, turnover annoncé, météo extrême. ` +
    `Renseigne context_flag (match sans enjeu, tie déjà plié, finale = contextes atypiques qui ` +
    `cassent les probabilités du modèle).\n` +
    `3) COTE ${BOOK} : relève la cote RÉELLE de ce marché sur ${BOOK} (${DOMAIN} est géobloqué : ` +
    `passe par un comparateur affichant les cotes ${BOOK}, ou la presse spécialisée allemande). ` +
    `Renseigne betano_odds et odds_source. Puis beats_min_odds = (cote relevée >= ${s.min_odds}). ` +
    `Si la cote est INTROUVABLE, mets betano_odds=0 et signale-le — ne devine pas.\n` +
    `4) COHÉRENCE : le marché « ${s.label} » est-il bien proposé par ${BOOK} sur cette compétition ? ` +
    `(sur les petits championnats, l'offre se limite souvent à 1X2/DC/O-U/BTTS).\n` +
    `5) RÉFÉRENCE DE MARCHÉ — LE CONTRÔLE LE PLUS IMPORTANT. Relève les cotes 1X2 ` +
    `d'un bookmaker à faible marge (Pinnacle en priorité, sinon Bet365) sur ce match. ` +
    `RETIRE LA MARGE : somme des probabilités brutes (1/cote), puis divise chaque ` +
    `probabilité par cette somme. Déduis-en la probabilité de marché du marché « ${s.label} » ` +
    `si elle est déductible du 1X2 (1, X, 2, doubles chances, DNB le sont ; ` +
    `BTTS et Over/Under ne le sont PAS — dans ce cas relève directement la cote de ce marché). ` +
    `Renseigne market_prob (0 si aucune référence trouvée) et market_ref ` +
    `(bookmaker + cotes brutes + marge calculée). NE DEVINE JAMAIS ce chiffre : ` +
    `un market_prob inventé est pire qu'un market_prob absent, car il ferait croire ` +
    `à un avantage inexistant. Sans cote de référence : market_prob=0.\n` +
    SOFT +
    `\nSois sceptique et FACTUEL. Au moindre doute sérieux sur la tenue du match ou sur ` +
    `l'existence du marché : verdict=drop. Une cote sous le minimum n'est PAS un drop en soi ` +
    `(la prédiction reste juste, elle n'est simplement pas jouable) : mets keep avec ` +
    `beats_min_odds=false.`,
    { label: `verify:${s.home}-${s.away}`, phase: 'Vérification', schema: VERDICT_SCHEMA }
  ).then((v) => ({ ...s, check: v }))
))).filter(Boolean)

// VETO FIXTURE : une seule alerte suffit à écarter la ligne (leçon Wings-Liberty).
const kept = checked.filter((c) =>
  c.check && c.check.verdict === 'keep' && c.check.fixture_confirmed !== false)
const dropped = checked.filter((c) => !kept.includes(c))

for (const d of dropped) {
  const why = (d.check && (d.check.issues || [])[0]) || 'fixture non confirmée'
  log(`  ✂ ${d.home} – ${d.away} [${d.market}] : ${String(why).slice(0, 110)}`)
}

// Jouable = survit à la vérif ET la cote relevée dépasse le seuil après taxe.
const playable = kept.filter((c) => c.check.beats_min_odds === true && (c.check.betano_odds || 0) > 1)
log(`${kept.length}/${SHORTLIST.length} ligne(s) validée(s) — dont ${playable.length} au-dessus de la cote minimale.`)

phase('Verdict')
const writeup = await agent(
  `Rédige en français une note COURTE et honnête pour ${DATE}.\n` +
  `Lignes VALIDÉES par la vérification : ${JSON.stringify(kept.map((k) => ({
    match: `${k.home} – ${k.away}`, pays: k.country, marche: k.label,
    proba: `${(k.prob * 100).toFixed(1)}%`, cote_min: k.min_odds,
    cote_betano: k.check.betano_odds || 'introuvable',
    au_dessus_du_seuil: k.check.beats_min_odds === true,
    proba_marche: k.check.market_prob || 'non relevée', reference: k.check.market_ref || '',
    contexte: k.check.context_flag, notes: (k.check.context_notes || []).slice(0, 3),
  }))).slice(0, 4000)}\n` +
  `Lignes ÉCARTÉES : ${JSON.stringify(dropped.map((d) => ({
    match: `${d.home} – ${d.away}`, raison: (d.check && (d.check.issues || [])[0]) || 'fixture',
  }))).slice(0, 1500)}\n\n` +
  `RÈGLES DE RÉDACTION :\n` +
  `- Les probabilités viennent du MOTEUR (Poisson/Dixon-Coles contrôlé contre ClubElo), ` +
  `pas d'une opinion. Ne les modifie pas, ne les réinterprète pas.\n` +
  `- Distingue clairement : prédiction VALIDÉE (le match a lieu, le raisonnement tient) ` +
  `et prédiction JOUABLE (en plus, la cote dépasse le seuil de rentabilité).\n` +
  `- Si aucune cote ne dépasse son seuil, dis-le franchement : « rien de jouable aujourd'hui, ` +
  `les cotes offertes sont sous le seuil de rentabilité » — c'est un résultat utile.\n` +
  `- Rappelle que la cote minimale intègre la taxe allemande de 5,3 %.\n` +
  `- ÉCART AU MARCHÉ : quand une proba de marché a été relevée, compare-la à celle du ` +
  `moteur et dis-le franchement. Moins de 1,5 point d'écart = le modèle récite le ` +
  `consensus, il ne peut structurellement pas battre la marge. C'est le constat le ` +
  `plus utile de la journée, ne l'enterre pas.\n` +
  `- Mode PAPER, 0 € misé. ESTIMATIONS, pas des certitudes. Pas d'incitation à miser.`,
  { label: 'redaction', phase: 'Verdict' }
)

return {
  date: DATE,
  checked: checked.length,
  verified: kept.map((k) => ({
    country: k.country, match: `${k.home} – ${k.away}`,
    market: k.market, label: k.label,
    prob: k.prob, fair_odds: k.fair_odds, min_odds: k.min_odds,
    betano_odds: k.check.betano_odds || null,
    beats_min_odds: k.check.beats_min_odds === true,
    market_prob: k.check.market_prob || null,
    market_ref: k.check.market_ref || '',
    // Écart au consensus : < 1,5 pt = le modèle récite le marché.
    market_gap: k.check.market_prob
      ? Math.round((k.prob - k.check.market_prob) * 1000) / 10 : null,
    context_flag: k.check.context_flag || 'normal',
    confidence: k.check.confidence,
    notes: k.check.context_notes || [],
  })),
  dropped: dropped.map((d) => ({
    match: `${d.home} – ${d.away}`,
    reason: (d.check && (d.check.issues || [])[0]) || 'fixture non confirmée',
  })),
  playable: playable.length,
  writeup,
  disclaimer: "ESTIMATIONS statistiques, PAS des certitudes. Mode PAPER : 0 € misé. " +
    "La cote minimale intègre la taxe allemande de 5,3 %. Aide : joueurs-info-service.fr, 09 74 75 13 13.",
}
