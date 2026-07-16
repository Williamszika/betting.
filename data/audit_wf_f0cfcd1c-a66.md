==================================================================
AUDIT DU RUN — wf_f0cfcd1c-a66
==================================================================
Agents lancés : 24 | terminés : 24 | en échec/incomplets : 0

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 12   Collecte des données (forme, xG, H2H, cotes…)
  🔎 Découverte             × 3    Trouve les vrais matchs du jour (Betano.de)
  🧩 Desk éditeur           × 3    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 3    Tous les marchés → opportunités de value (modèle croisé)
  🕵️ Vérificateur           × 3    Contrôle adversarial (match à venir ? cote ? logique ?)

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 60
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 9  (value, modèle × recherche)
  Vérifiées → gardées ........ 0 🟢  / écartées 3 🔴
  Coordination ............... 0  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [tennis] Nikoloz Basilashvili vs Thiago Tirante (ATP Bastad - Swedish Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Andrey Rublev vs Andrea Pellegrino (ATP Bastad - Swedish Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Alejandro Tabilo vs Lautaro Midon (ATP Bastad - Swedish Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Jesper De Jong vs Sebastian Baez (ATP Bastad - Swedish Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Juan Manuel Cerundolo vs Miomir Kecmanovic (ATP Gstaad - Swiss Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Jaime Faria vs Casper Ruud (ATP Gstaad - Swiss Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Jerome Kym vs Stefanos Tsitsipas (ATP Gstaad - Swiss Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Alexander Bublik vs Quentin Halys (ATP Gstaad - Swiss Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Aleksandr Shevchenko vs Dominic Stricker (ATP Gstaad - Swiss Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Daniel Merida vs Titouan Droguet (ATP Umag - Croatia Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Damir Dzumhur vs Matteo Arnaldi (ATP Umag - Croatia Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Roman Burruchaga vs Camilo Ugo Carabelli (ATP Umag - Croatia Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Alex Molcan vs Alejandro Davidovich Fokina (ATP Umag - Croatia Open (ATP 250, terre battue), 1/4 de finale)
  • [tennis] Tereza Valentova vs Aliaksandra Sasnovich (WTA Athens - Vanda Pharmaceuticals Athens Open (WTA 250, terre battue), 1/8 de finale)
  • [tennis] Alina Korneeva vs Ann Li (WTA Athens - Vanda Pharmaceuticals Athens Open (WTA 250, terre battue), 1/8 de finale)
  • [tennis] Barbora Krejcikova vs Carole Monnet (WTA Athens - Vanda Pharmaceuticals Athens Open (WTA 250, terre battue), 1/8 de finale)
  • [tennis] Clara Tauson vs Miriana Tona (WTA Athens - Vanda Pharmaceuticals Athens Open (WTA 250, terre battue), 1/8 de finale)
  • [tennis] Mayar Sherif vs Kaitlin Quevedo (WTA Iasi - UniCredit Iasi Open (WTA 250, terre battue), 1/8 de finale)
  • [tennis] Oleksandra Oliynykova vs Elena Pridankina (WTA Iasi - UniCredit Iasi Open (WTA 250, terre battue), 1/8 de finale)
  • [tennis] Alevtina Ibragimova vs Paula Badosa (WTA Iasi - UniCredit Iasi Open (WTA 250, terre battue), 1/8 de finale)

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.88) Value is illusory: market 1X2 (Dynamo 1.58, Draw 4.00, Cluj 5.00 at 1xBet; corroborated by Betsson/Bwin) impli
  🔴 (conf 0.6) Match, date and status all check out: U Cluj vs Dynamo Kyiv, UEL 2026/27 1st qualifying round 2nd leg, Thu 16 
  🔴 (conf 0.8) Fixture is real and still upcoming: U Cluj vs Dynamo Kyiv, Europa League 2026/27 1QR 2nd leg, Cluj Arena, Thu 


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
