==================================================================
AUDIT DU RUN — wf_dc2ab3ba-092
==================================================================
Agents lancés : 19 | terminés : 19 | en échec/incomplets : 0

--- QUI A TRAVAILLÉ (par rôle) ---
  🕵️ Vérificateur           × 10   Contrôle adversarial (match à venir ? cote ? logique ?)
  📊 Analyste marchés       × 8    Tous les marchés → opportunités de value (modèle croisé)
  📝 Synthèse/rédaction     × 1    Construit le coupon + note finale
  🔎 Découverte             × 0    Trouve les vrais matchs du jour (Betano.de)
  📚 Spécialiste recherche  × 0    Collecte des données (forme, xG, H2H, cotes…)
  🧩 Desk éditeur           × 0    Réconcilie/vérifie les faits + stats chiffrées

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 0
  Agents spécialistes ........ 0  (données brutes + sources)
  Fiches de faits (desk) ..... 0  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 24  (value, modèle × recherche)
  Vérifiées → gardées ........ 4 🟢  / écartées 6 🔴
  Coordination ............... 0  → construction du coupon

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.78) Odds implausible/unconfirmed: 1.80 for Schwaerzler +5.5 is inconsistent with the market moneyline Sonego 1.49 
  🔴 (conf 0.7) Fixture confirmed upcoming: Pistons vs Knicks, NBA Summer League Las Vegas, July 13 2026 4:00PM ET (8:00PM UTC
  🔴 (conf 0.82) Il s'agit d'un match de NBA Summer League (Las Vegas), pas de saison reguliere: echantillon minuscule et tres 
  🔴 (conf 0.7) Fixture confirmee et A VENIR: Djurgardens IF vs Halmstads BK, Allsvenskan J12, 13 juillet 2026 19:00 CEST (17:
  🔴 (conf 0.8) Odds inconsistency: the argument cites a documented reference ML of Detroit -118 (~1.85) but bets at 1.55. Bet
  🔴 (conf 0.68) Edge illusoire: estimation 40% placee AU-DESSUS de l'implicite marche (36.4% a 2.75 Bet365, 38.3% a 2.61 Melbe


COMMENT LE COUPON EST CRÉÉ (algorithme) :
1. Chaque opportunité a : cote (Betano.de/Flashscore) + proba finale = BLEND(modèle Poisson, recherche).
2. VALUE = proba × cote − 1. On ne garde que value > 0.
3. VÉRIFICATION adversariale : match encore à venir ? cote réelle ? raisonnement solide ? (sinon écarté)
4. Le solveur choisit la combinaison de jambes (matchs DISTINCTS) dont la cote totale
   tombe dans la fourchette (défaut 1,95–3) en MAXIMISANT la proba conjointe (le plus « sûr »).
5. COMBIEN : 1 coupon combiné par jour (+ jusqu'à 2 paris simples cote 5–7 en option).
   Rien n'est forcé : si aucune combi ne rentre ou si rien ne passe la vérif → « rien à parier ».
