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
// args peut arriver comme objet OU comme chaine JSON selon le harness : on normalise.
let A = args;
if (typeof A === 'string') { try { A = JSON.parse(A); } catch (e) { A = {}; } }
if (!A || typeof A !== 'object') A = {};

const DATE = A.date || "aujourd'hui"
const SINGLE_MIN = A.oddsMin || 5.0
const SINGLE_MAX = A.oddsMax || 7.0
const COUPON_TARGET = A.couponTargetOdds || 1.95
const COUPON_MAX = A.couponMaxOdds || 3.0
const MAX_PICKS = A.maxPicks || 2
const MAX_MATCHES = A.maxMatches || 12
const BOOKMAKER = A.bookmaker || "Betano"
const DOMAIN = A.domain || "betano.de"  // Betano Allemagne
const PREFILTER_FLOOR = A.prefilterFloor || 0.35  // fiabilité minimale d'une compétition (audit)

// ---------- MÉMOIRE branchée sur le moteur (correction Faille n°1) ----------
// Le script du workflow n'a PAS accès au disque : l'orchestrateur lit data/lessons.md,
// le parse (scripts/lessons_rules.py) et passe les règles via args.
//   hardRules : [{pattern, field, market, action:'exclude', note}] -> FILTRE en code
//   softBlock : texte injecté dans les prompts analyste-marchés & vérificateur
const HARD_RULES = Array.isArray(A.hardRules) ? A.hardRules : [];
const SOFT_BLOCK = A.softBlock ? `\n${String(A.softBlock)}\n` : '';

// Détecte le contexte d'un match par mots-clés sur la compétition (robuste, sans agent).
function detectContext(competition) {
  const c = (competition || '').toLowerCase();
  if (/finale|\bfinal\b|3e place|3rd place|troisi[eè]me place|classement|third place/.test(c)) return 'finale';
  if (/barrage|play-?off|playoff/.test(c)) return 'barrage';
  if (/derby|clasico|cl[aá]sico/.test(c)) return 'derby';
  return 'normal';
}

// Une opportunité est-elle interdite par une règle HARD ? Renvoie la raison, sinon null.
function droppedByHardRule(opp) {
  for (const r of HARD_RULES) {
    if (!r || r.action !== 'exclude') continue;
    const field = r.field === 'context_flag' ? (opp.context_flag || 'normal')
      : r.field === 'always' ? 'always' : String(opp[r.field] || '');
    let patOk = true, mktOk = true;
    try { patOk = new RegExp(r.pattern || '.*', 'i').test(field); } catch (e) { patOk = false; }
    if (r.market) { try { mktOk = new RegExp(r.market, 'i').test(opp.market || ''); } catch (e) { mktOk = false; } }
    if (patOk && mktOk) return r.note || r.pattern || 'règle mémoire';
  }
  return null;
}

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

// Grille de données par sport (chaque spécialiste récupère des données CONCRÈTES et chiffrées).
const DATA_SPEC = {
  football: {
    forme: "Forme 5-10 derniers matchs (dom/ext), bilan V-N-D, buts marqués/encaissés, MOYENNE de buts/match, clean sheets, série/momentum en cours.",
    effectif: "Blessures, suspensions, joueurs clés absents, forme des buteurs et du gardien, COMPO probable et FORMATION (4-3-3, 3-5-2...).",
    avance: "STATS AVANCÉES chiffrées : xG et xGA, possession moyenne, tirs cadrés/match, grosses occasions créées, force offensive et défensive.",
    h2h: "Confrontations directes récentes (scores, buts), style des duels (ouverts/fermés), tendances Over/Under et BTTS sur les H2H.",
    tactique: "Style de jeu (offensif/défensif, pressing haut/bloc bas), ENJEU (maintien, qualif, derby, titre), motivation, FATIGUE (calendrier serré), voyage/déplacement.",
    externe: "MÉTÉO (pluie/chaleur/vent), état du terrain, ARBITRE désigné et ses tendances (cartons/penalties).",
    marche: "Cotes sur " + "Betano (betano.de) — sinon Flashscore/Flashresultats ou comparateur (oddsportal, betexplorer, wincomparator)" + " si visibles + consensus public, cote d'ouverture vs actuelle, MOUVEMENTS de cotes, où va l'argent.",
  },
  tennis: {
    forme: "CLASSEMENT ATP/WTA + points + progression (en forme / en chute) ; forme 5-10 derniers matchs (V-D, NIVEAU des adversaires battus, scores faciles/serrés), série en cours.",
    effectif: "Condition physique / FATIGUE : matchs longs récents (5 sets), temps de jeu cumulé sur le tournoi, blessures/gênes, abandons récents, enchaînement des matchs.",
    avance: "SERVICE : % 1re balle, aces, doubles fautes, % points gagnés au service, HOLD%. RETOUR : % points gagnés en retour, balles de break converties, BREAK%. Elo PAR SURFACE, ratio winners/fautes directes.",
    h2h: "Head-to-Head : bilan des confrontations (global et sur la surface), qui domine, style qui gêne l'autre, scénarios (serrés / à sens unique).",
    tactique: "SURFACE = facteur clé (terre/dur/gazon) et niveau du joueur SUR cette surface ; style (gros serveur / défenseur / agressif) et matchup de styles.",
    externe: "Conditions (indoor/outdoor, altitude, balle, vitesse du court) ; CONTEXTE : niveau du tournoi (Grand Chelem / ATP 250...), pression, motivation.",
    marche: "Cotes " + "Betano (betano.de) — sinon Flashscore/Flashresultats ou comparateur (oddsportal, betexplorer, wincomparator)" + " si visibles + consensus, favori/outsider, MOUVEMENT des cotes (une cote qui chute = info possible).",
  },
  basketball: {
    forme: "Forme 5-10 derniers matchs, série V/D, performance CONTRE des équipes similaires, momentum ; points marqués/encaissés par match, écarts.",
    effectif: "PLAYER IMPACT : joueur clé/leader offensif, usage rate, PER, minutes, +/-, dépendance à une star ; blessures/absences (star OUT = impact énorme), repos/load management, rotation.",
    avance: "TEAM + ADVANCED chiffrés : offensive/defensive RATING, PACE, FG%/3PT%/FT%, rebonds off/def, turnovers ; TS%, eFG%, assist ratio, turnover ratio, NET RATING (attaque-défense).",
    h2h: "Confrontations directes récentes, écarts, tendances total points (Over/Under) et handicap.",
    tactique: "MATCHUPS individuels (ex. pivot vs pivot), style défensif (zone/individuel), systèmes (pick&roll, isolation, jeu rapide), qui contrôle le TEMPO, qui domine sous le panier, mismatches exploitables.",
    externe: "CONTEXTE : back-to-back/fatigue, domicile/extérieur, voyage, motivation (playoffs, revanche, seeding), match sans enjeu ; Summer League = échantillon bruité.",
    marche: "Cotes " + "Betano (betano.de) — sinon Flashscore/Flashresultats ou comparateur (oddsportal, betexplorer, wincomparator)" + " si visibles + consensus, favori/outsider, MOUVEMENT des cotes.",
  },
};
function spec(m, key) { return (DATA_SPEC[m.sport] && DATA_SPEC[m.sport][key]) || DATA_SPEC.football[key]; }

// 4 spécialistes CONSOLIDÉS (audit anti-surcollecte : moins d'agents, mêmes données).
const SPECIALISTS = [
  { key: 'stats',    ask: (m) => spec(m, 'forme') + ' ' + spec(m, 'avance') },
  { key: 'effectif', ask: (m) => spec(m, 'effectif') + ' ' + spec(m, 'tactique') },
  { key: 'contexte', ask: (m) => spec(m, 'h2h') + ' ' + spec(m, 'externe') },
  { key: 'marche',   ask: (m) => spec(m, 'marche') },
];

// ---------- Fiabilité par compétition + seuils (port JS de src/sportsbet/reliability.py) ----------
const COMP_RULES = [
  [["summer league"], 0.30],
  [["friendly", "amical", "testspiel", "exhibition", "pre-season", "preseason", "pré-saison"], 0.25],
  [["champions league", "europa league", "premier league", "la liga", "serie a", "bundesliga", "ligue 1"], 1.00],
  [["grand slam", "wimbledon", "roland", "us open", "australian open", "atp masters", "wta 1000"], 0.95],
  [["atp", "wta"], 0.90],
  [["eredivisie", "primeira", "liga portugal", "championship", "super lig", "allsvenskan", "eliteserien"], 0.85],
  [["euroleague", "eurocup"], 0.90],
  [["nba"], 1.00],
  [["challenger", "itf"], 0.75],
  [["besta deild", "1. deild", "2. deild", "islande", "iceland"], 0.65],
];
const SPORT_DEFAULT_REL = { football: 0.70, tennis: 0.85, basketball: 0.70 };
const BLACKLIST = ["friendly", "amical", "testspiel", "exhibition", "pre-season", "preseason", "pré-saison"];
const MIN_EDGE = { safe: 0.05, aggressive: 0.08, combine: 0.06 };

// ---------- Catalogue Betano.de : ne cibler QUE des matchs/marchés jouables sur Betano Allemagne ----------
// betano.de bloque le scraping direct (403, même en vrai navigateur). On cadre donc les
// agents sur son OFFRE RÉELLE ; un contrôle final via comparateur Betano.de (Oddspedia)
// confirme la dispo avant de présenter un pari. But : 0 pari « introuvable sur Betano ».
const BETANO_EXCLUDE = [
  "wnba",                                   // couverture absente/marginale sur Betano.de
  "summer league",                          // offre pauvre + échantillon bruité
  "g league", "g-league", "nba g",          // ligues mineures US
  "ncaa", "cba", "wcba", "kbl", "wkbl",     // niches basket non couvertes
  "liga femenina", "beach", "3x3", "indoor",// variantes non standard
];
function betanoExcluded(comp) { const c = (comp || '').toLowerCase(); return BETANO_EXCLUDE.some(k => c.includes(k)); }

// Menu des marchés RÉELLEMENT proposés par Betano.de (par sport). Les agents ne doivent
// proposer QUE ces marchés — pas de props US exotiques ni de handicaps introuvables chez Betano.
const BETANO_MARKETS = {
  football: "1X2 (Résultat), Double Chance, Over/Under buts (0.5/1.5/2.5/3.5), Les deux marquent (BTTS), Handicap européen, Mi-temps/Fin, Total corners O/U, Vainqueur",
  tennis: "Vainqueur du match, Vainqueur du 1er set, Score en sets (2-0/2-1...), Handicap de jeux, Total de jeux O/U",
  basketball: "Vainqueur (avec prolongations), Handicap de points, Total de points O/U, Vainqueur mi-temps, Handicap/total par quart-temps — AUCUN prop joueur exotique",
};
function betanoMarkets(sport) { return BETANO_MARKETS[sport] || BETANO_MARKETS.football; }
function compReliability(comp, sport) {
  const c = (comp || '').toLowerCase();
  for (const [kws, coef] of COMP_RULES) if (kws.some(k => c.includes(k))) return coef;
  return SPORT_DEFAULT_REL[sport] || 0.70;
}
function isBlacklisted(comp) { const c = (comp || '').toLowerCase(); return BLACKLIST.some(k => c.includes(k)); }
function passesPrefilter(comp, sport, floor) { if (isBlacklisted(comp) || betanoExcluded(comp)) return false; return compReliability(comp, sport) >= (floor || 0.35); }

// ---------- Modèle Poisson/logistique (port JS de src/sportsbet/model.py) ----------
function _clamp01(v) { return Math.max(0, Math.min(1, v)); }
function _norm(v, lo, hi) { if (hi <= lo) return 0.5; return _clamp01((v - lo) / (hi - lo)); }
function _num(v, d) { return (v === null || v === undefined || isNaN(Number(v))) ? d : Number(v); }
function _poisPmf(k, lam) { let f = 1; for (let i = 2; i <= k; i++) f *= i; return Math.exp(-lam) * Math.pow(lam, k) / f; }
function _footProbs(hx, ax, maxG = 10) {
  const H = [], Aw = [];
  for (let i = 0; i <= maxG; i++) { H[i] = _poisPmf(i, hx); Aw[i] = _poisPmf(i, ax); }
  let pH = 0, pD = 0, pA = 0, over = 0, btts = 0;
  for (let i = 0; i <= maxG; i++) for (let j = 0; j <= maxG; j++) {
    const p = H[i] * Aw[j];
    if (i > j) pH += p; else if (i === j) pD += p; else pA += p;
    if (i + j > 2.5) over += p;
    if (i > 0 && j > 0) btts += p;
  }
  return { "1": pH, "X": pD, "2": pA, "Over 2.5": over, "Under 2.5": 1 - over, "BTTS Yes": btts, "BTTS No": 1 - btts };
}
function _expGoals(h, a, avg = 1.35) {
  const base = s => Math.max(0.2, (_num(s.goals_for, 1.3) + _num(s.xg, 1.3)) / 2);
  const oppDef = o => Math.max(0.5, Math.min(1.6, ((_num(o.goals_against, 1.3) + _num(o.xga, 1.3)) / 2) / avg));
  const form = s => 0.85 + 0.30 * _norm(_num(s.form_points, 7), 0, 15);
  const avail = s => 0.80 + 0.20 * _clamp01(_num(s.availability, 1));
  return [Math.max(0.2, base(h) * oppDef(a) * form(h) * avail(h) * 1.10),
          Math.max(0.2, base(a) * oppDef(h) * form(a) * avail(a))];
}
function _elo1x2(he, ae, adv = 65) {
  const p = 1 / (1 + Math.pow(10, ((ae) - (he + adv)) / 400));
  const diff = Math.abs((he + adv) - ae);
  const draw = 0.30 * Math.exp(-diff / 300);
  return { "1": p * (1 - draw), "X": draw, "2": (1 - p) * (1 - draw) };
}
function modelProbs(sport, stats) {
  if (!stats || !stats.home || !stats.away) return null;
  if (sport === 'football') {
    const g = _expGoals(stats.home, stats.away);
    const probs = _footProbs(g[0], g[1]);
    const he = _num(stats.home.elo, 0), ae = _num(stats.away.elo, 0);
    if (he > 1000 && ae > 1000) {                      // ELO connu -> croiser 1X2
      const e = _elo1x2(he, ae), w = 0.35;
      for (const k of ['1', 'X', '2']) probs[k] = (1 - w) * probs[k] + w * e[k];
      const tot = probs['1'] + probs['X'] + probs['2'];
      if (tot > 0) for (const k of ['1', 'X', '2']) probs[k] /= tot;
    }
    return probs;
  }
  const score = (t, home) => 0.45 * _norm(_num(t.form_points, 7), 0, 15) + 0.25 * _clamp01(_num(t.availability, 1))
    + 0.15 * _clamp01(_num(t.h2h_score, 0.5)) + 0.15 * (home ? 1 : 0);
  const diff = score(stats.home, true) - score(stats.away, false);
  let pH = 1 / (1 + Math.exp(-6 * diff));
  const he = _num(stats.home.elo, 0), ae = _num(stats.away.elo, 0);
  if (he > 1000 && ae > 1000) {                       // GARDE-FOU écart de niveau
    const pElo = 1 / (1 + Math.pow(10, (ae - he) / 400));
    const gap = Math.abs(he - ae);
    const wElo = Math.min(0.9, 0.55 + gap / 500);     // ELO domine ; + si gros écart
    pH = wElo * pElo + (1 - wElo) * pH;
  }
  return { "home": pH, "away": 1 - pH };
}
function blendP(m, r, w) { return w * m + (1 - w) * r; }
// Calibrage vers le MARCHÉ selon la compétition (fiabilité) et l'écart de niveau (ELO).
function calibrateToMarket(model, implied, reliability, levelGap) {
  let wM = (1 - Math.max(0, Math.min(1, reliability))) * 0.6 + Math.min(0.45, (levelGap || 0) / 350);
  wM = Math.max(0, Math.min(0.85, wM));
  return (1 - wM) * model + wM * implied;
}
function modelKeyFor(sport, market, pick) {
  const mk = (market || '').toLowerCase(), pk = (pick || '').toLowerCase();
  if (sport !== 'football') return null;
  if (mk.includes('1x2') || mk.includes('resultat') || mk.includes('résultat')) {
    if (pk === '1' || pk.includes('domicile') || pk.includes('(1)')) return '1';
    if (pk === 'x' || pk.includes('nul') || pk.includes('draw')) return 'X';
    if (pk === '2' || pk.includes('exterieur') || pk.includes('extérieur') || pk.includes('(2)')) return '2';
  }
  if (pk.includes('over 2.5') || pk.includes('over 2,5') || (mk.includes('2.5') && pk.includes('over'))) return 'Over 2.5';
  if (pk.includes('under 2.5') || pk.includes('moins de 2,5') || (mk.includes('2.5') && (pk.includes('under') || pk.includes('moins')))) return 'Under 2.5';
  if (mk.includes('btts') || mk.includes('deux equipes') || mk.includes('deux équipes')) {
    if (pk.includes('oui') || pk.includes('yes')) return 'BTTS Yes';
    if (pk.includes('non') || pk.includes('no')) return 'BTTS No';
  }
  return null;
}

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
    stats: { type: 'object', properties: { home: { type: 'object', properties: { goals_for: { type: 'number' }, goals_against: { type: 'number' }, xg: { type: 'number' }, xga: { type: 'number' }, form_points: { type: 'number' }, availability: { type: 'number' }, h2h_score: { type: 'number' }, elo: { type: 'number' } } }, away: { type: 'object', properties: { goals_for: { type: 'number' }, goals_against: { type: 'number' }, xg: { type: 'number' }, xga: { type: 'number' }, form_points: { type: 'number' }, availability: { type: 'number' }, h2h_score: { type: 'number' }, elo: { type: 'number' } } } } },
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
const SEED = (A.matches && A.matches.length) ? A.matches : null;
let matches;
if (SEED) {
  // Matchs FOURNIS (ex. captures Betano) — on saute la découverte web ; ils seront quand même VÉRIFIÉS plus loin.
  matches = SEED.map(m => ({ sport: m.sport, competition: m.competition || '', home: m.home, away: m.away, start_local: m.start_local || '' }));
  log(`${matches.length} match(s) fourni(s) — découverte web ignorée (ils passent par la vérification comme d'habitude).`);
} else {
  // FOOTBALL UNIQUEMENT (choix utilisateur 18/07) — TOUS les championnats couverts par Betano.de.
  const sports = [
    { key: 'football', hint: "TOUS les championnats de FOOTBALL couverts par Betano.de, le plus large possible : UEFA (C1/C3/C4 + qualifs), toutes les grandes ligues européennes ET leurs 2e/3e divisions, MLS, Liga MX, Brésil (Série A/B), Argentine, ligues nordiques (Allsvenskan, Eliteserien, Veikkausliiga, etc.), Europe de l'Est, ligues asiatiques (J-League, K-League...), Australie, Afrique, sélections et grandes coupes — du moment que c'est LISTÉ sur Betano.de. EXCLUS : amicaux obscurs, matchs de jeunes/U19/U21, équipes réserves, futsal/beach." },
  ];
  const discovered = await parallel(sports.map(s => () =>
    agent(
      `Recherche sur le web (WebSearch/WebFetch) les matchs de ${s.key} programmés ${DATE} ` +
      `qui sont RÉELLEMENT PROPOSÉS SUR ${BOOKMAKER} Allemagne (${DOMAIN}). ` +
      `Couvre : ${s.hint}. Ne retiens que des matchs listés par ${BOOKMAKER} ET pour lesquels ` +
      `${BOOKMAKER} propose les marchés standards (${betanoMarkets(s.key)}). ` +
      `EXCLUS tout ce que Betano.de ne couvre pas de façon fiable (WNBA, ligues mineures US, exhibitions, variantes 3x3/beach). ` +
      `Sources fiables (${BOOKMAKER}, comparateur affichant les cotes Betano.de type Oddspedia, sites officiels, presse). ` +
      `Rends UNIQUEMENT des matchs réels et vérifiables avec l'URL source. ` +
      `Au moindre doute sur la présence du match OU de ses marchés sur ${BOOKMAKER}, ne l'inclus pas.`,
      { label: `discover:${s.key}`, phase: 'Découverte', schema: FIXTURES_SCHEMA }
    )
  ));
  matches = discovered.filter(Boolean).flatMap(d => d.matches || []);
}
const seen = new Set();
matches = matches.filter(m => {
  const k = `${m.sport}|${(m.home || '').toLowerCase()}|${(m.away || '').toLowerCase()}`;
  if (seen.has(k)) return false; seen.add(k); return true;
});
// PRÉ-FILTRE (audit) : retire amicaux + compétitions peu fiables AVANT l'analyse coûteuse.
const _beforePF = matches.length;
matches = matches.filter(m => passesPrefilter(m.competition, m.sport, PREFILTER_FLOOR));
if (_beforePF - matches.length > 0) log(`Pré-filtre : ${_beforePF - matches.length} match(s) écarté(s) (amicaux / compétitions peu fiables).`);
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
matches = inter.map((m, i) => ({ ...m, key: `${i}:${m.home} vs ${m.away}`, context_flag: detectContext(m.competition) }));
log(`Mémoire : ${HARD_RULES.length} règle(s) hard chargée(s)${SOFT_BLOCK ? ' + bloc soft actif' : ''}.`);
const _atyp = matches.filter(m => m.context_flag !== 'normal');
if (_atyp.length) log(`Contexte : ${_atyp.length} match(s) atypique(s) -> ${_atyp.map(m => m.context_flag + ':' + m.home).join(', ')}`);
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
    `Voici les faits rapportés par 4 spécialistes (stats, effectif/tactique, contexte/H2H, marché) :\n` +
    JSON.stringify(r.facts).slice(0, 6000) + `\n\n` +
    `Réconcilie-les : garde les faits corroborés (idéalement 2+ sources), signale les ` +
    `contradictions, isole blessures/absences, résume la forme, et dégage les vrais ` +
    `angles (key_edges). Recoupe/vérifie sur le web les faits douteux mais décisifs.\n` +
    `Renseigne AUSSI 'stats' par équipe (home/away) : goals_for, goals_against, ` +
    `xg, xga (par match — utilise un xG GLISSANT pondéré vers les matchs RÉCENTS), ` +
    `form_points (0-15, forme PONDÉRÉE récent>ancien), availability (0-1), h2h_score (0-1), ` +
    `elo (note de force RÉALISTE : top10~2000, top30~1920, top50~1870, top100~1750, top150~1650, top200~1580, top300~1470 ; au foot/basket ~1300-1900). ` +
    `Au tennis/basket, approxime : form_points = niveau/forme, availability = fraîcheur.`,
    { label: `desk:${r.m.home}-${r.m.away}`, phase: 'Consolidation', schema: FACTSHEET_SCHEMA }
  ).then(sheet => ({ m: r.m, sheet })),

  // 4) Analyse de TOUS les marchés à partir de la fiche partagée, ANCRÉE sur le modèle
  (r) => {
    const mm = modelProbs(r.m.sport, r.sheet && r.sheet.stats);
    const rounded = mm ? Object.fromEntries(Object.entries(mm).map(([k, v]) => [k, Math.round(v * 100) / 100])) : null;
    const grounding = mm
      ? `\nMODÈLE (Poisson/logistique, ancré sur les stats de la fiche) : ${JSON.stringify(rounded)}. ` +
        `CROISE ces probabilités avec ta recherche : ton est_probability doit être un compromis raisonné ` +
        `entre le modèle et tes infos (ne t'en écarte pas sans raison forte et explicite).\n`
      : '';
    return agent(
      `Tu es l'ANALYSTE MARCHÉS pour ${r.m.home} vs ${r.m.away} (${r.m.sport}). ` +
      `Base-toi sur cette fiche de faits vérifiés :\n` +
      JSON.stringify(r.sheet).slice(0, 5500) + `\n` + grounding + `\n` +
      `CONSULTE TOUS les marchés RÉELLEMENT PROPOSÉS PAR ${BOOKMAKER} (${DOMAIN}) pour ce match : ` +
      `${betanoMarkets(r.m.sport)}. ` +
      `Puis PROPOSE LE(S) MEILLEUR(S) — celui/ceux avec la value la plus FIABLE, PAS forcément le 1X2 ` +
      `(souvent un marché buts, double chance ou handicap est plus solide qu'un vainqueur sec). ` +
      `INTERDIT : props joueur exotiques, handicaps/lignes US introuvables sur Betano.de. ` +
      `Pour chaque marché intéressant, récupère la COTE RÉELLE : d'abord ${BOOKMAKER} (${DOMAIN}) si visible, ` +
      `SINON un comparateur affichant les cotes Betano.de (Oddspedia) ou Flashscore / comparateur (oddsportal, betexplorer). ` +
      `Indique la source ET confirme que le marché est bien listé par ${BOOKMAKER} (le parieur doit pouvoir le jouer). ` +
      `Garde uniquement les opportunités de VALUE (proba > implicite). ` +
      `Privilégie les cotes exploitables (simple ${SINGLE_MIN}-${SINGLE_MAX} ou jambe de combiné). ` +
      `N'invente JAMAIS une cote : cite toujours une source réelle. ` +
      `Compare aussi à un book SHARP (Pinnacle) et au consensus : un écart net = possible erreur de marché (value réelle) ou piège.` +
      `\nCONTEXTE du match : ${r.m.context_flag || 'normal'}.` + SOFT_BLOCK,
      { label: `markets:${r.m.home}-${r.m.away}`, phase: 'Marchés', schema: MARKETS_SCHEMA }
    ).then(mk => ({ m: r.m, sheet: r.sheet, markets: (mk && mk.opportunities) || [], modelMap: mm }));
  }
);

// Aplatir toutes les opportunités
let opps = [];
let idc = 0;
for (const r of perMatch.filter(Boolean)) {
  const mm = r.modelMap;
  for (const o of r.markets) {
    const research = Number(o.est_probability) || 0;
    const d = Number(o.decimal_odds) || 0;
    if (research <= 0 || d <= 1) continue;
    // Croisement modèle x recherche quand le marché est couvert par le modèle
    let model_prob = null, prob = research;
    if (mm) {
      let key = modelKeyFor(r.m.sport, o.market, o.pick);
      if (!key && r.m.sport !== 'football') {
        const pk = (o.pick || '').toLowerCase();
        const hw = (r.m.home || '').toLowerCase().split(' ')[0];
        const aw = (r.m.away || '').toLowerCase().split(' ')[0];
        if (hw && pk.includes(hw)) key = 'home';
        else if (aw && pk.includes(aw)) key = 'away';
      }
      if (key && mm[key] != null) { model_prob = mm[key]; prob = blendP(model_prob, research, 0.5); }
    }
    // CALIBRAGE marché : considérer la compétition (fiabilité) + l'écart de niveau (ELO).
    const rel0 = compReliability(r.m.competition, r.m.sport);
    const st = r.sheet && r.sheet.stats;
    let eloGap = 0;
    if (st && st.home && st.away && st.home.elo && st.away.elo) eloGap = Math.abs(Number(st.home.elo) - Number(st.away.elo));
    prob = calibrateToMarket(prob, 1 / d, rel0, eloGap);
    const rel = compReliability(r.m.competition, r.m.sport);
    const edgeRaw = prob * d - 1;
    opps.push({
      id: idc++, matchKey: r.m.key, match: `${r.m.home} vs ${r.m.away}`,
      sport: r.m.sport, competition: r.m.competition, reliability: rel,
      context_flag: r.m.context_flag || 'normal',
      market: o.market, pick: o.pick, odds: d,
      prob, research_prob: research, model_prob,
      edge: edgeRaw, eff_edge: edgeRaw * rel, rationale: o.rationale || '',
      sources: o.sources || [], data_quality: (r.sheet && r.sheet.data_quality) || 'low',
    });
  }
}
log(`${opps.length} opportunité(s) de marché détectée(s) sur ${perMatch.length} match(s).`);

// FILTRE HARD (mémoire) : retire AVANT vérification les opportunités interdites par une
// leçon exécutable (ex. favori 1X2 sur finale/dead rubber). Économise des agents ET
// applique enfin la mémoire dans le moteur (correction Faille n°1).
if (HARD_RULES.length) {
  const _before = opps.length;
  const _kept = [], _dropped = [];
  for (const o of opps) { const why = droppedByHardRule(o); if (why) _dropped.push({ o, why }); else _kept.push(o); }
  opps = _kept;
  if (_dropped.length) {
    log(`Règles hard : ${_dropped.length}/${_before} opportunité(s) EXCLUE(S) par la mémoire :`);
    for (const d of _dropped) log(`  ✂ ${d.o.match} — ${d.o.market} / ${d.o.pick} [${d.why}]`);
  }
}

// ================= PHASE 5 : Vérification adversariale =================
phase('Vérification')
// On vérifie en priorité les meilleures value (borne le coût).
// Seuil de value (audit) : ne vérifier que les opportunités dont l'edge AJUSTÉ par la
// fiabilité dépasse le seuil combiné (élimine la value "fake" et le bruit Summer League).
const toVerify = opps.filter(o => o.eff_edge >= MIN_EDGE.combine).sort((a, b) => b.eff_edge - a.eff_edge).slice(0, 12);
log(`${toVerify.length} opportunité(s) au-dessus du seuil de value ajusté (>=${Math.round(MIN_EDGE.combine * 100)}%).`);
const allVerdicts = (await parallel(toVerify.map(o => () =>
  agent(
    `Vérifie de façon ADVERSARIALE cette opportunité :\n` +
    `${o.match} (${o.competition}) — ${o.market} / ${o.pick} @ ${o.odds}.\n` +
    `Argument : ${o.rationale}\n` +
    `Contrôle sur le web : (1) le match a-t-il lieu ${DATE} et est-il encore À VENIR ? ` +
    `S'il est déjà commencé/terminé, ou surtout REPORTÉ / ANNULÉ / déplacé à une autre date, ` +
    `mets fixture_confirmed=false (un pari sur un match reporté est nul). ` +
    `(2) la cote ${o.odds} est-elle réelle/plausible, ET ce marché est-il RÉELLEMENT PROPOSÉ par ${BOOKMAKER} (${DOMAIN}) ? ` +
    `Vérifie via un comparateur affichant les cotes Betano.de (Oddspedia) : si le match OU ce marché n'est PAS jouable sur ${BOOKMAKER}, verdict=drop (odds_plausible=false). ` +
    `(3) le raisonnement tient-il (blessure majeure ignorée ? enjeu ? piège ?). ` +
    `CONTEXTE du match : ${o.context_flag || 'normal'}.` + SOFT_BLOCK +
    `\nQUESTION OBLIGATOIRE : une des leçons ci-dessus s'applique-t-elle à cette prédiction ? ` +
    `Si oui et que l'argument ne la traite pas, verdict=drop. ` +
    `Sois sceptique : au moindre doute sérieux, ou si non jouable sur ${BOOKMAKER}, verdict=drop.`,
    { label: `verify:${o.id}`, phase: 'Vérification', schema: VERDICT_SCHEMA }
  ).then(v => ({ ...o, verdict: v }))
))).filter(Boolean);

// VETO FIXTURE au niveau du MATCH (leçon 17/07 : Wings-Liberty reporté — panne
// de l'avion charter du Liberty — mais gardé car le vérificateur DE CETTE
// sélection avait raté le report). Un pari sur un match REPORTÉ/ANNULÉ est nul.
// Donc si UN SEUL vérificateur signale fixture_confirmed=false sur un match, on
// invalide TOUTES les sélections de ce match (sécurité d'abord).
const fixtureVeto = new Set();
for (const o of allVerdicts) {
  if (o.verdict && o.verdict.fixture_confirmed === false) fixtureVeto.add(o.matchKey);
}
if (fixtureVeto.size) log(`⚠️ ${fixtureVeto.size} match(s) à fixture NON confirmée (report/annulation) : toutes leurs sélections écartées.`);

const verified = allVerdicts
  .filter(o => o.verdict && o.verdict.verdict === 'keep' && !fixtureVeto.has(o.matchKey))
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
// Degradation propre : si le coordinateur a echoue (null, ex. limite), on garde
// l ordre par confiance/edge sans planter le run.
const rankById = new Map(((coord && coord.ranked) || []).map(x => [x.id, x.rank]));
for (const o of verified) o.rank = rankById.has(o.id) ? rankById.get(o.id) : 999;
verified.sort((a, b) => a.rank - b.rank || b.confidence - a.confidence || b.edge - a.edge);

// ================= PHASE 7 : Synthèse (coupon + singles) =================
phase('Synthèse')
// Toujours remonter les paris VÉRIFIÉS (même hors fourchette de coupon) = les prédictions du jour.
const verified_picks = verified.slice()
  .sort((a, b) => (b.eff_edge || 0) - (a.eff_edge || 0) || b.prob - a.prob)
  .map(o => ({
    match: o.match, sport: o.sport, competition: o.competition, market: o.market, pick: o.pick,
    odds: o.odds, est_prob: o.prob, edge: Number((o.edge || 0).toFixed(3)),
    reliability: o.reliability, confidence: o.confidence, rationale: o.rationale,
  }));

// Singles cote 5-7, matchs distincts
const singles = [];
const usedForSingles = new Set();
for (const o of verified) {
  if (o.odds >= SINGLE_MIN && o.odds <= SINGLE_MAX && !usedForSingles.has(o.matchKey)) {
    singles.push(o); usedForSingles.add(o.matchKey);
    if (singles.length >= MAX_PICKS) break;
  }
}

// Coupon dans la fourchette cible ; SINON repli : meilleur combiné 2 jambes hors fourchette.
const pool = verified.map(o => ({ matchKey: o.matchKey, odds: o.odds, prob: o.prob, ref: o }));
let couponLegs = buildCoupon(pool, COUPON_TARGET, COUPON_MAX, 2, 5);
let couponOutOfRange = false;
if (!couponLegs) {
  couponLegs = buildCoupon(pool, 1.01, 1e9, 2, 5);   // n'importe quelle cote, juste 2 jambes distinctes
  couponOutOfRange = !!couponLegs;
}
const coupon = couponLegs ? {
  legs: couponLegs.map(c => ({
    match: c.ref.match, market: c.ref.market, pick: c.ref.pick,
    odds: c.ref.odds, est_prob: c.ref.prob, confidence: c.ref.confidence,
  })),
  total_odds: Number(prod(couponLegs.map(c => c.odds)).toFixed(2)),
  joint_prob: Number(prod(couponLegs.map(c => c.prob)).toFixed(3)),
  out_of_range: couponOutOfRange,
} : null;

// Meilleur pari le plus sûr (proba la plus haute) et meilleure value (edge le plus haut).
const safest = verified.slice().sort((a, b) => b.prob - a.prob)[0] || null;
const bestValue = verified.slice().sort((a, b) => (b.eff_edge || 0) - (a.eff_edge || 0))[0] || null;

const writeup = verified_picks.length ? await agent(
  `Rédige en français une note claire et HONNÊTE pour un parieur ${BOOKMAKER}, à partir de ces données VÉRIFIÉES par les agents.\n` +
  `PARIS VÉRIFIÉS (présente-les TOUS — ce sont les prédictions du jour) : ${JSON.stringify(verified_picks)}\n` +
  `LE PLUS SÛR (proba max) : ${JSON.stringify(safest && { match: safest.match, pick: safest.pick, odds: safest.odds, est_prob: safest.prob })}\n` +
  `MEILLEURE VALUE : ${JSON.stringify(bestValue && { match: bestValue.match, pick: bestValue.pick, odds: bestValue.odds, est_prob: bestValue.prob, edge: Number((bestValue.edge || 0).toFixed(3)) })}\n` +
  `SINGLES cote ${SINGLE_MIN}-${SINGLE_MAX} : ${JSON.stringify(singles.map(s => ({ match: s.match, pick: s.pick, odds: s.odds, est_prob: s.prob })))}\n` +
  `COUPON (cible ${COUPON_TARGET}-${COUPON_MAX}${couponOutOfRange ? " — AUCUN dans la fourchette : voici le meilleur combiné HORS fourchette, à signaler comme tel" : ""}) : ${JSON.stringify(coupon)}\n` +
  `IMPÉRATIF : ne dis JAMAIS "aucune sélection" s'il y a des paris vérifiés — présente-les (le plus sûr ET la meilleure value). ` +
  `Rappels : proba réelle de gain, aucune garantie, gestion de mise 1-2%, cotes à CONFIRMER sur ${BOOKMAKER}. Intègre l'avertissement : "${DISCLAIMER}".`,
  { label: 'redaction', phase: 'Synthèse' }
) : ("Aucune opportunité n'a passé la vérification aujourd'hui — rien à parier. " + DISCLAIMER);

return {
  date: DATE,
  considered: matches.length,
  opportunities: opps.length,
  verified: verified.length,
  verified_picks,
  singles,
  coupon,
  writeup,
  disclaimer: DISCLAIMER,
};
