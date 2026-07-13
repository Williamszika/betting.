export const meta = {
  name: 'settle-coupons',
  description: 'Regle les coupons apres les matchs : des agents verifient le resultat reel de chaque jambe (gagne/perdu), marquent le coupon, et tiennent une RETRO sur chaque perte (causes + donnees a ajouter).',
  phases: [
    { title: 'Resultats', detail: 'Verification web du resultat reel de chaque jambe' },
    { title: 'Retro', detail: 'Reunion post-perte : causes + features a ajouter' },
  ],
}

let A = args;
if (typeof A === 'string') { try { A = JSON.parse(A); } catch (e) { A = {}; } }
if (!A || typeof A !== 'object') A = {};
const COUPONS = A.coupons || [];

const LEG_SCHEMA = {
  type: 'object',
  properties: {
    outcome: { type: 'string', enum: ['won', 'lost', 'void'] },
    final_result: { type: 'string' },
    note: { type: 'string' },
    source: { type: 'string' },
  }, required: ['outcome', 'final_result'],
};
const RETRO_SCHEMA = {
  type: 'object',
  properties: {
    what_happened: { type: 'string' },
    root_causes: { type: 'array', items: { type: 'string' } },
    features_to_add: { type: 'array', items: { type: 'string' } },
    confidence_next_time: { type: 'string' },
  }, required: ['what_happened', 'features_to_add'],
};

if (!COUPONS.length) return { settled: [], note: 'Aucun coupon a regler.' };

const settled = await pipeline(
  COUPONS,
  // 1) Verifier le resultat reel de chaque jambe
  (c) => parallel((c.legs || []).map((leg, i) => () =>
    agent(
      "Verifie le RESULTAT REEL et DEFINITIF de ce pari (le match est termine) :\n" +
      "Match : " + leg.match + "\n" +
      "Pari : " + leg.market + " / " + leg.pick + " (cote " + leg.odds + ")\n" +
      "Cherche le score/resultat final sur le web (sites de resultats fiables). " +
      "Puis juge si CE pari precis est GAGNE (won), PERDU (lost) ou ANNULE (void). " +
      "Donne le resultat final exact et la source. Sois factuel et sans complaisance.",
      { label: ("res:" + leg.match + ":" + leg.pick).slice(0, 55), phase: 'Resultats', schema: LEG_SCHEMA }
    ).then(r => ({ i, leg, ...r }))
  )).then(outcomes => {
    outcomes.sort((a, b) => a.i - b.i);
    const leg_results = outcomes.map(o => o.outcome);
    let status = 'won';
    if (leg_results.some(o => o === 'pending')) status = 'pending';
    else if (leg_results.some(o => o === 'lost')) status = 'lost';
    else if (leg_results.every(o => o === 'void')) status = 'void';
    return { c, outcomes, leg_results, status };
  }),
  // 2) RETRO si le coupon est perdu
  (r) => {
    if (r.status !== 'lost') return { id: r.c.id, leg_results: r.leg_results, status: r.status, retro: null,
      legs_detail: r.outcomes.map(o => ({ pick: o.leg.pick, outcome: o.outcome, final: o.final_result })) };
    const legsTxt = r.outcomes.map(o => `- ${o.leg.match} : ${o.leg.pick} @ ${o.leg.odds} => ${o.outcome} (${o.final_result})`).join("\n");
    return agent(
      "REUNION RETRO (le coupon a PERDU). Analyse honnete, sans complaisance.\n" +
      "Coupon " + r.c.id + " (cote " + (r.c.total_odds || '?') + "), jambes et resultats :\n" + legsTxt + "\n\n" +
      "Reponds : (1) what_happened = ce qui a fait perdre (la/les jambe(s) fautive(s) et pourquoi) ; " +
      "(2) root_causes = causes profondes (donnee manquee, blessure, surface, fatigue, marche mal lu...) ; " +
      "(3) features_to_add = quelles INFORMATIONS/donnees CONCRETES ajouter aux prochaines analyses pour eviter cette erreur.",
      { label: ("retro:" + r.c.id).slice(0, 55), phase: 'Retro', schema: RETRO_SCHEMA }
    ).then(retro => ({ id: r.c.id, leg_results: r.leg_results, status: r.status, retro,
      legs_detail: r.outcomes.map(o => ({ pick: o.leg.pick, outcome: o.outcome, final: o.final_result })) }));
  }
);

const clean = settled.filter(Boolean);
const losses = clean.filter(s => s.status === 'lost');
log(clean.length + " coupon(s) regle(s) ; " + losses.length + " perte(s) analysee(s) en retro.");
// Agrege les nouvelles features a ajouter (dedoublonnage simple)
const newFeatures = [];
for (const s of losses) for (const f of (s.retro && s.retro.features_to_add) || [])
  if (!newFeatures.includes(f)) newFeatures.push(f);

return { settled: clean, lessons: newFeatures };
