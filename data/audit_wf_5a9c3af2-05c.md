==================================================================
AUDIT DU RUN — wf_5a9c3af2-05c
==================================================================
Agents lancés : 45 | terminés : 27 | en échec/incomplets : 18

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 12   Collecte des données (forme, xG, H2H, cotes…)
  🕵️ Vérificateur           × 4    Contrôle adversarial (match à venir ? cote ? logique ?)
  🔎 Découverte             × 3    Trouve les vrais matchs du jour (Betano.de)
  🧩 Desk éditeur           × 3    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 3    Tous les marchés → opportunités de value (modèle croisé)
  🎯 Coordinateur           × 1    Classe et dé-corrèle les opportunités
  📝 Synthèse/rédaction     × 1    Construit le coupon + note finale

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 29
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 10  (value, modèle × recherche)
  Vérifiées → gardées ........ 1 🟢  / écartées 3 🔴
  Coordination ............... 1  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [tennis] Raphael Collignon vs Valentin Vacherot (ATP 250 Gstaad (Swiss Open) - Quarterfinal)
  • [tennis] Juan Manuel Cerundolo vs Casper Ruud (ATP 250 Gstaad (Swiss Open) - Quarterfinal)
  • [tennis] Arthur Rinderknech vs Stefanos Tsitsipas (ATP 250 Gstaad (Swiss Open) - Quarterfinal)
  • [tennis] A. Vallejo vs Stefano Travaglia (ATP 250 Bastad (Nordea Open) - Quarterfinal)
  • [tennis] Nuno Borges vs Luciano Darderi (ATP 250 Bastad (Nordea Open) - Quarterfinal)
  • [tennis] Yulia Putintseva vs Mayar Sherif (WTA 250 Iasi (UniCredit Iasi Open) - Quarterfinal)
  • [tennis] Oleksandra Oliynykova vs Clara Burel (WTA 250 Iasi (UniCredit Iasi Open) - Quarterfinal)
  • [tennis] Tamara Zidansek vs Petra Marcinko (WTA 250 Iasi (UniCredit Iasi Open) - Quarterfinal)
  • [tennis] Tereza Valentova vs Alina Korneeva (WTA 250 Athens (Vanda Pharmaceuticals Athens Open))
  • [tennis] Alycia Parks vs Maria Sakkari (WTA 250 Athens (Vanda Pharmaceuticals Athens Open))
  • [tennis] Francesca Jones vs Noma Noha Akugue (WTA 125 Rome (ATV Bancomat Tennis Open))
  • [football] Nashville SC vs Atlanta United (MLS (Matchday 16, USA))
  • [football] LA Galaxy vs Los Angeles FC (MLS (Matchday 16, USA) - El Trafico)
  • [football] Atletico San Luis vs Cruz Azul (Liga MX Apertura 2026 (Jornada 1, Mexico))
  • [football] Club Leon vs Atlas (Liga MX Apertura 2026 (Jornada 1, Mexico))
  • [football] FC Juarez (Bravos) vs Puebla (Liga MX Apertura 2026 (Jornada 1, Mexico))
  • [football] Bahia vs Chapecoense (Brasileirao Serie A (jogo atrasado 4a rodada, Brazil))
  • [football] Bodo/Glimt vs Fredrikstad (Eliteserien (Norway))
  • [football] Mjallby AIF vs Vasteras SK (Allsvenskan (omgang 13, Sweden))
  • [football] Beijing Guoan vs Liaoning Tieren (Chinese Super League (Round 19, China))

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.62) DATE MISLABELED: the game is Thursday July 16, 2026 (9 PM ET / 8 PM CT, College Park Center, Arlington), NOT F
  🔴 (conf 0.97) DECISIVE: Game postponed. The Dallas Wings vs New York Liberty game scheduled Thursday July 16 2026, 8pm CT (=
  🔴 (conf 0.96) DECISIVE: The Wings-Liberty game was POSTPONED on July 16, 2026 due to mechanical issues with the New York Lib


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
