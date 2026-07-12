export const meta = {
  name: 'verify-and-build',
  description: 'Finition robuste : verifie adversarialement une liste d opportunites deja recherchees (passees via args) puis batit le coupon cote 1,95-3 + singles 5-7. Leger, independant du cache d un gros run.',
  phases: [
    { title: 'Verification', detail: 'Controle adversarial de chaque opportunite' },
    { title: 'Synthese', detail: 'Coupon cote 1,95-3 + singles 5-7 + redaction' },
  ],
}

// args peut arriver comme objet OU comme chaine JSON selon le harness : on normalise.
let A = args;
if (typeof A === 'string') { try { A = JSON.parse(A); } catch (e) { A = {}; } }
if (!A || typeof A !== 'object') A = {};

const DATE = A.date || "12 juillet 2026"
const OPPS = A.opportunities || []
const SINGLE_MIN = A.oddsMin || 5.0
const SINGLE_MAX = A.oddsMax || 7.0
const COUPON_TARGET = A.couponTargetOdds || 1.95
const COUPON_MAX = A.couponMaxOdds || 3.0
const MAX_PICKS = A.maxPicks || 2
const VERIFY_CAP = A.verifyCap || 14

const DISCLAIMER =
  "ESTIMATIONS statistiques, PAS des certitudes. Aucun pari n est sur. " +
  "Ne miser que ce qu on peut perdre. Interdit aux mineurs — " +
  "aide : joueurs-info-service.fr, 09 74 75 13 13.";

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    fixture_confirmed: { type: 'boolean' }, odds_plausible: { type: 'boolean' },
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

phase('Verification')
if (!OPPS.length) return { error: "Aucune opportunite fournie via args.opportunities", disclaimer: DISCLAIMER };

const cand = OPPS
  .map((o, i) => ({ ...o, id: i, matchKey: o.match, odds: o.decimal_odds, prob: o.est_probability }))
  .filter(o => o.odds > 1 && o.prob > 0)
  .sort((a, b) => (b.prob * b.odds - 1) - (a.prob * a.odds - 1))
  .slice(0, VERIFY_CAP);

const verified = (await parallel(cand.map(o => () =>
  agent(
    "Verifie de facon ADVERSARIALE ce pari pour le " + DATE + " :\n" +
    o.match + " — " + o.market + " / " + o.pick + " @ " + o.odds +
    " (proba estimee " + Math.round(o.prob * 100) + "%).\n" +
    "Argument initial : " + (o.rationale || 'n/a') + "\n" +
    "Controle sur le web (WebSearch/WebFetch) : (1) le match a-t-il bien lieu ce jour ? " +
    "(2) la cote " + o.odds + " est-elle reelle/plausible aujourd hui ? " +
    "(3) le raisonnement tient-il (blessure de derniere minute, compo, enjeu, piege) ? " +
    "Sois sceptique : au moindre doute serieux, verdict=drop.",
    { label: ("verify:" + o.match + ":" + o.pick).slice(0, 60), phase: 'Verification', schema: VERDICT_SCHEMA }
  ).then(v => ({ ...o, verdict: v }))
))).filter(Boolean).filter(o => o.verdict && o.verdict.verdict === 'keep')
  .map(o => ({ ...o, confidence: o.verdict.confidence || 0 }))
  .sort((a, b) => b.confidence - a.confidence || (b.prob * b.odds) - (a.prob * a.odds));

log(verified.length + "/" + cand.length + " opportunite(s) confirmee(s) apres verification.");
if (!verified.length)
  return { date: DATE, coupon: null, singles: [], disclaimer: DISCLAIMER,
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
  legs: legs.map(c => ({ match: c.match, market: c.market, pick: c.pick, odds: c.odds, est_prob: c.prob, confidence: c.confidence })),
  total_odds: Number(prod(legs.map(c => c.odds)).toFixed(2)),
  joint_prob: Number(prod(legs.map(c => c.prob)).toFixed(3)),
} : null;

const writeup = await agent(
  "Redige en francais une note claire et HONNETE (pas de survente, pas de safe) a partir de :\n" +
  "COUPON (cote " + COUPON_TARGET + "-" + COUPON_MAX + "): " + JSON.stringify(coupon) + "\n" +
  "SINGLES (cote " + SINGLE_MIN + "-" + SINGLE_MAX + ", plus risques): " +
  JSON.stringify(singles.map(s => ({ match: s.match, market: s.market, pick: s.pick, odds: s.odds, est_prob: s.prob, confidence: s.confidence }))) + "\n" +
  "Integre l avertissement : " + JSON.stringify(DISCLAIMER) + ". Rappelle la vraie probabilite de gain et la gestion de mise.",
  { label: 'redaction', phase: 'Synthese' }
);

return { date: DATE, verified: verified.length, coupon, singles, writeup, disclaimer: DISCLAIMER };
