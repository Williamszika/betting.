export const meta = {
  name: 'markets-verify-build',
  description: 'Finisseur leger : a partir de fiches de faits deja etablies (via args), analyse les marches Betano, verifie, et batit le coupon 1,95-3 + singles 5-7. ~20 agents, tient dans une fenetre de budget.',
  phases: [
    { title: 'Marches', detail: 'Un agent par match : opportunites de value sur Betano' },
    { title: 'Verification', detail: 'Controle adversarial (match a venir, cote Betano reelle)' },
    { title: 'Synthese', detail: 'Coupon 1,95-3 + singles 5-7 + redaction' },
  ],
}

let A = args;
if (typeof A === 'string') { try { A = JSON.parse(A); } catch (e) { A = {}; } }
if (!A || typeof A !== 'object') A = {};

const DATE = A.date || "13 juillet 2026"
const BOOKMAKER = A.bookmaker || "Betano"
const MATCHES = A.matches || []
const SINGLE_MIN = A.oddsMin || 5.0
const SINGLE_MAX = A.oddsMax || 7.0
const COUPON_TARGET = A.couponTargetOdds || 1.95
const COUPON_MAX = A.couponMaxOdds || 3.0
const MAX_PICKS = A.maxPicks || 2
const VERIFY_CAP = A.verifyCap || 12

const MARKETS = {
  football: "1X2, Double Chance, Draw No Bet, Over/Under (0.5-4.5), BTTS, Handicap asiatique, Total par equipe, Corners, Cartons",
  tennis: "Vainqueur, Handicap jeux/sets, Total jeux O/U, Score en sets, Vainqueur set 1, Total sets",
  basketball: "Vainqueur, Handicap (spread), Total points O/U, Total par equipe, Quart-temps/mi-temps",
};

const DISCLAIMER =
  "ESTIMATIONS statistiques, PAS des certitudes. Aucun pari n est sur. " +
  "Ne miser que ce qu on peut perdre. Interdit aux mineurs — aide : joueurs-info-service.fr, 09 74 75 13 13.";

const MARKETS_SCHEMA = {
  type: 'object',
  properties: {
    opportunities: { type: 'array', items: { type: 'object', properties: {
      market: { type: 'string' }, pick: { type: 'string' },
      decimal_odds: { type: 'number' }, est_probability: { type: 'number' },
      rationale: { type: 'string' }, sources: { type: 'array', items: { type: 'string' } },
    }, required: ['market', 'pick', 'decimal_odds', 'est_probability'] } },
  }, required: ['opportunities'],
};
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    fixture_upcoming: { type: 'boolean' }, odds_on_bookmaker: { type: 'boolean' },
    reasoning_sound: { type: 'boolean' }, confidence: { type: 'number' },
    issues: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string', enum: ['keep', 'drop'] },
  }, required: ['verdict', 'confidence'],
};

function* combos(arr, r, start = 0, acc = []) {
  if (acc.length === r) { yield acc.slice(); return; }
  for (let i = start; i < arr.length; i++) { acc.push(arr[i]); yield* combos(arr, r, i + 1, acc); acc.pop(); }
}
const prod = xs => xs.reduce((a, b) => a * b, 1);
const distinct = c => new Set(c.map(x => x.matchKey)).size === c.length;
function buildCoupon(cands, tMin, tMax, minLegs, maxLegs, poolSize = 16) {
  const pool = cands.slice().sort((a, b) => b.prob - a.prob).slice(0, poolSize);
  let best = null, bk = null;
  for (let r = Math.max(1, minLegs); r <= maxLegs; r++)
    for (const c of combos(pool, r)) {
      if (!distinct(c)) continue;
      const total = prod(c.map(x => x.odds));
      if (total < tMin || (tMax && total > tMax)) continue;
      const joint = prod(c.map(x => x.prob));
      const key = [joint, -r, -(total - tMin)];
      if (!best || key[0] > bk[0] || (key[0] === bk[0] && key[1] > bk[1]) ||
        (key[0] === bk[0] && key[1] === bk[1] && key[2] > bk[2])) { best = c; bk = key; }
    }
  return best;
}

phase('Marches')
if (!MATCHES.length) return { error: "Aucune fiche fournie via args.matches", disclaimer: DISCLAIMER };

const perMatch = await parallel(MATCHES.map(m => () =>
  agent(
    "Tu es l ANALYSTE MARCHES pour " + m.match + " (" + m.sport + ", " + DATE + ").\n" +
    "Fiche de faits verifies :\n" + JSON.stringify(m).slice(0, 3500) + "\n\n" +
    "Passe en revue les marches : " + (MARKETS[m.sport] || "principaux marches") + ".\n" +
    "Pour la cote : cherche d abord " + BOOKMAKER + " ; sinon la cote REELLE sur Flashscore/Flashresultats " +
    "ou un comparateur (oddsportal, betexplorer, wincomparator, previews presse). " +
    "Indique la source dans 'sources' (le parieur confirmera le prix exact sur " + BOOKMAKER + "). " +
    "Estime honnetement la probabilite et garde 2 a 5 opportunites de VALUE (proba estimee > proba implicite de la cote). " +
    "Ne rends une liste VIDE que si le match n a AUCUNE value credible. " +
    "Verifie sur le web que le match est ENCORE A VENIR le " + DATE + ". N invente jamais une cote : cite toujours une source.",
    { label: ("markets:" + m.match).slice(0, 55), phase: 'Marches', schema: MARKETS_SCHEMA }
  ).then(r => ({ m, opps: (r && r.opportunities) || [] }))
));

let opps = [];
let id = 0;
for (const r of perMatch.filter(Boolean))
  for (const o of r.opps) {
    const d = Number(o.decimal_odds), p = Number(o.est_probability);
    if (!(d > 1) || !(p > 0)) continue;
    opps.push({ id: id++, matchKey: r.m.match, match: r.m.match, sport: r.m.sport,
      market: o.market, pick: o.pick, odds: d, prob: p, edge: p * d - 1,
      rationale: o.rationale || '', sources: o.sources || [] });
  }
log(opps.length + " opportunite(s) Betano detectee(s) sur " + perMatch.length + " match(s).");

phase('Verification')
const toVerify = opps.filter(o => o.edge > 0).sort((a, b) => b.edge - a.edge).slice(0, VERIFY_CAP);
const verified = (await parallel(toVerify.map(o => () =>
  agent(
    "Verifie de facon ADVERSARIALE ce pari pour le " + DATE + " :\n" +
    o.match + " — " + o.market + " / " + o.pick + " @ " + o.odds + " (proba estimee " + Math.round(o.prob * 100) + "%).\n" +
    "Argument : " + (o.rationale || 'n/a') + "\n" +
    "Controle sur le web : (1) le match est-il ENCORE A VENIR le " + DATE + " (pas commence/fini) ? " +
    "(2) la cote " + o.odds + " est-elle plausible (sur " + BOOKMAKER + " ou en consensus marche) ? " +
    "(3) le raisonnement tient-il ? Sois sceptique : au moindre doute serieux, verdict=drop.",
    { label: ("verify:" + o.id), phase: 'Verification', schema: VERDICT_SCHEMA }
  ).then(v => ({ ...o, verdict: v }))
))).filter(Boolean).filter(o => o.verdict && o.verdict.verdict === 'keep')
  .map(o => ({ ...o, confidence: o.verdict.confidence || 0 }))
  .sort((a, b) => b.confidence - a.confidence || (b.prob * b.odds) - (a.prob * a.odds));
log(verified.length + "/" + toVerify.length + " opportunite(s) confirmee(s).");
if (!verified.length)
  return { date: DATE, bookmaker: BOOKMAKER, coupon: null, singles: [], considered: MATCHES.length,
    opportunities: opps.length, disclaimer: DISCLAIMER,
    note: "Aucune opportunite confirmee — mieux vaut ne pas parier." };

phase('Synthese')
const singles = [];
const used = new Set();
for (const o of verified)
  if (o.odds >= SINGLE_MIN && o.odds <= SINGLE_MAX && !used.has(o.matchKey)) {
    singles.push(o); used.add(o.matchKey); if (singles.length >= MAX_PICKS) break;
  }
const legs = buildCoupon(verified, COUPON_TARGET, COUPON_MAX, 2, 4);
const coupon = legs ? {
  legs: legs.map(c => ({ match: c.match, sport: c.sport, market: c.market, pick: c.pick, odds: c.odds, est_prob: c.prob, confidence: c.confidence })),
  total_odds: Number(prod(legs.map(c => c.odds)).toFixed(2)),
  joint_prob: Number(prod(legs.map(c => c.prob)).toFixed(3)),
} : null;

const writeup = await agent(
  "Redige en francais une note claire et HONNETE (pas de survente, pas de safe) pour un parieur " + BOOKMAKER + ", a partir de :\n" +
  "COUPON (cote " + COUPON_TARGET + "-" + COUPON_MAX + "): " + JSON.stringify(coupon) + "\n" +
  "SINGLES (cote " + SINGLE_MIN + "-" + SINGLE_MAX + ", plus risques): " +
  JSON.stringify(singles.map(s => ({ match: s.match, market: s.market, pick: s.pick, odds: s.odds, est_prob: s.prob, confidence: s.confidence }))) + "\n" +
  "Rappelle la vraie probabilite de gain, la gestion de mise (1-2%), et integre : " + JSON.stringify(DISCLAIMER),
  { label: 'redaction', phase: 'Synthese' }
);

const verified_picks = verified.map(o => ({ match: o.match, sport: o.sport, market: o.market,
  pick: o.pick, odds: o.odds, est_prob: o.prob, edge: Number(o.edge.toFixed(3)), confidence: o.confidence }));
return { date: DATE, bookmaker: BOOKMAKER, considered: MATCHES.length, opportunities: opps.length,
  verified: verified.length, verified_picks, coupon, singles, writeup, disclaimer: DISCLAIMER };
