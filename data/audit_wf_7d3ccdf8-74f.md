==================================================================
AUDIT DU RUN — wf_7d3ccdf8-74f
==================================================================
Agents lancés : 28 | terminés : 28 | en échec/incomplets : 0

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 12   Collecte des données (forme, xG, H2H, cotes…)
  🕵️ Vérificateur           × 7    Contrôle adversarial (match à venir ? cote ? logique ?)
  🧩 Desk éditeur           × 3    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 3    Tous les marchés → opportunités de value (modèle croisé)
  🔎 Découverte             × 1    Trouve les vrais matchs du jour (Betano.de)
  🎯 Coordinateur           × 1    Classe et dé-corrèle les opportunités
  📝 Synthèse/rédaction     × 1    Construit le coupon + note finale

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 19
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 10  (value, modèle × recherche)
  Vérifiées → gardées ........ 2 🟢  / écartées 5 🔴
  Coordination ............... 1  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [football] Levski Sofia vs Universitatea Craiova (UEFA Champions League - 2e tour de qualification (aller))
  • [football] Egnatia Rrogozhinë vs Celje (UEFA Champions League - 2e tour de qualification (aller))
  • [football] Omonia Nicosie vs Kairat Almaty (UEFA Champions League - 2e tour de qualification (aller))
  • [football] Coritiba vs Palmeiras (Brésil - Série A (Brasileirão Betano))
  • [football] São Paulo vs Athletico Paranaense (Brésil - Série A (Brasileirão Betano))
  • [football] Internacional vs Cruzeiro (Brésil - Série A (Brasileirão Betano))
  • [football] Chapecoense vs Flamengo (Brésil - Série A (Brasileirão Betano))
  • [football] Operário-PR vs Ponte Preta (Brésil - Série B)
  • [football] Ceará vs CRB (Brésil - Série B)
  • [football] Goiás vs Sport Recife (Brésil - Série B)
  • [football] FC Cincinnati vs Vancouver Whitecaps (États-Unis - MLS)
  • [football] Charlotte FC vs Atlanta United (États-Unis - MLS)
  • [football] Sporting Kansas City vs Minnesota United (États-Unis - MLS)
  • [football] LA Galaxy vs St. Louis City (États-Unis - MLS)
  • [football] FC Seoul vs Pohang Steelers (Corée du Sud - K League 1 (19e journée))
  • [football] Gwangju FC vs Gimcheon Sangmu (Corée du Sud - K League 1 (19e journée))
  • [football] Bodø/Glimt vs HamKam (Norvège - Eliteserien (match reprogrammé))
  • [football] Lillestrøm vs Viking (Norvège - Eliteserien (match reprogrammé))
  • [football] Independiente del Valle vs Técnico Universitario (Équateur - LigaPro Serie A (21e journée))

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.6) Fixture OK: Omonia vs Kairat Almaty confirmed for Wed 22 July 2026, 17:00 UTC, Neo GSP Nicosia, CL 2026/27 QR2
  🔴 (conf 0.8) Fixture confirmed and upcoming: Omonia Nicosia vs Kairat Almaty, GSP Stadium, 22 July 2026 17:00 UTC, CL 2026/
  🔴 (conf 0.62) Fixture CONFIRMED: Omonia Nicosia vs Kairat Almaty, Wed 22 July 2026 17:00 UTC, GSP Stadium Nicosia, UCL 2nd q
  🔴 (conf 0.6) Fixture confirmee: Egnatia vs Celje, UCL 2e tour qualif. aller, mercredi 22/07/2026 19:00 UTC / 21:00 CEST au 
  🔴 (conf 0.8) Value illusoire: le +10% a 2.20 provient uniquement du modele qui note Kairat a 32% alors que le marche sharp 


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
