==================================================================
AUDIT DU RUN — wf_5a41bd21-cd1
==================================================================
Agents lancés : 52 | terminés : 47 | en échec/incomplets : 5

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 23   Collecte des données (forme, xG, H2H, cotes…)
  🕵️ Vérificateur           × 9    Contrôle adversarial (match à venir ? cote ? logique ?)
  🧩 Desk éditeur           × 6    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 6    Tous les marchés → opportunités de value (modèle croisé)
  🔎 Découverte             × 3    Trouve les vrais matchs du jour (Betano.de)

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 64
  Agents spécialistes ........ 23  (données brutes + sources)
  Fiches de faits (desk) ..... 6  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 17  (value, modèle × recherche)
  Vérifiées → gardées ........ 2 🟢  / écartées 7 🔴
  Coordination ............... 0  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [football] France vs Spain (FIFA World Cup 2026 — Semi-final)
  • [football] The New Saints vs Sabah (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Shamrock Rovers vs Floriana (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Iberia 1999 Tbilisi vs Flora Tallinn (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Inter Club d'Escaldes vs Lincoln Red Imps (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Larne vs Tre Fiori (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Riga FC vs Ararat-Armenia (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] KuPS Kuopio vs Vardar (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Drita vs Kauno Žalgiris (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Levski Sofia vs Borac Banja Luka (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] ETO FC Győr vs Víkingur Reykjavík (UEFA Champions League 2026/27 — 1st qualifying round, 2nd leg)
  • [football] Zhejiang Professional vs Qingdao Hainiu (Chinese Super League 2026)
  • [football] Brora Rangers vs Aberdeen (Scottish Premier Sports Cup 2026/27 — Group stage)
  • [football] Brechin City vs Livingston (Scottish Premier Sports Cup 2026/27 — Group stage)
  • [football] Montrose vs Dundee United (Scottish Premier Sports Cup 2026/27 — Group stage)
  • [football] Kilmarnock vs Raith Rovers (Scottish Premier Sports Cup 2026/27 — Group stage)
  • [football] Falkirk vs Ayr United (Scottish Premier Sports Cup 2026/27 — Group stage)
  • [football] Annan Athletic vs Dundee (Scottish Premier Sports Cup 2026/27 — Group stage)
  • [football] The Spartans vs Stirling Albion (Scottish Premier Sports Cup 2026/27 — Group stage)
  • [football] Kelty Hearts vs Queen's Park (Scottish Premier Sports Cup 2026/27 — Group stage)

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.63) Fixture confirmed and UPCOMING: Shamrock Rovers v Floriana, UCL 1st qual round 2nd leg, 14 July 2026 20:00 Tal
  🔴 (conf 0.7) Fixture, date and status all verified: Shamrock Rovers vs Floriana, 2026/27 UCL 1st qual round 2nd leg, Tuesda
  🔴 (conf 0.8) Fixture and timing CONFIRMED and upcoming: Shamrock Rovers vs Floriana, CL 2026/27 Q1 2nd leg, Tue 14 July 202
  🔴 (conf 0.7) Fixture verified: Shamrock Rovers vs Floriana, UCL 1st qualifying round 2nd leg, Tallaght Stadium Dublin, Tues
  🔴 (conf 0.72) Fixture confirmed and upcoming: Shamrock Rovers vs Floriana, UCL 26/27 1st qual. round 2nd leg, Tue 14 July 20
  🔴 (conf 0.7) Fixture confirmed upcoming: Tue 14 July 2026, 20:00 UK, Tallaght Stadium, Dublin; first leg Floriana 2-0 Rover


PIPELINE & COMMENT LE COUPON EST CRÉÉ (version optimisée après audit) :
0. PRÉ-FILTRE : on retire AVANT analyse les amicaux et les compétitions peu fiables
   (fiabilité < 0,35 : ex. NBA Summer League 0,30 ❌) → moins de bruit, moins d'agents.
1. RECHERCHE : 4 spécialistes consolidés/match (stats+xG, effectif+tactique, contexte+H2H, cotes).
2. FUSION : 1 fiche de faits vérifiés + STATS chiffrées par match (desk).
3. MODÈLE : proba finale = BLEND(modèle Poisson/logistique, recherche).
4. VALUE : edge = proba × cote − 1, AJUSTÉ par la fiabilité (edge × fiabilité).
   Seuils : safe > 5 %, combiné > 6 %, agressif > 8 %. En-dessous = rejeté (pas de value « fake »).
5. VÉRIFICATION adversariale (allégée) : match à venir ? cote réelle ? cohérence ?
6. SOLVEUR : combinaison de jambes (matchs DISTINCTS) dans la fourchette (défaut 1,95–3),
   en MAXIMISANT la proba conjointe (le plus « sûr »).
7. COMBIEN : 1 coupon combiné/jour (+ jusqu'à 2 simples cote 5–7). Rien n'est forcé :
   si aucune combi ne rentre ou si rien ne passe → « rien à parier ».
