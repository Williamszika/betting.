==================================================================
AUDIT DU RUN — wf_322d01fb-594
==================================================================
Agents lancés : 32 | terminés : 32 | en échec/incomplets : 0

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 16   Collecte des données (forme, xG, H2H, cotes…)
  🧩 Desk éditeur           × 4    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 4    Tous les marchés → opportunités de value (modèle croisé)
  🔎 Découverte             × 3    Trouve les vrais matchs du jour (Betano.de)
  🕵️ Vérificateur           × 3    Contrôle adversarial (match à venir ? cote ? logique ?)
  🎯 Coordinateur           × 1    Classe et dé-corrèle les opportunités
  📝 Synthèse/rédaction     × 1    Construit le coupon + note finale

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 125
  Agents spécialistes ........ 16  (données brutes + sources)
  Fiches de faits (desk) ..... 4  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 11  (value, modèle × recherche)
  Vérifiées → gardées ........ 3 🟢  / écartées 0 🔴
  Coordination ............... 1  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [tennis] Budkov Kjaer N. vs Pellegrino A. (ATP 250 Bastad (Nordea Open))
  • [tennis] Ofner S. vs Tirante T. (ATP 250 Bastad (Nordea Open))
  • [tennis] Diaz Acosta F. vs Midon L. (ATP 250 Bastad (Nordea Open))
  • [tennis] Vallejo A. vs Damas M. (ATP 250 Bastad (Nordea Open))
  • [tennis] Svrcina D. vs Dimitrov G. (ATP 250 Bastad (Nordea Open))
  • [tennis] Van De Zandschulp B. vs Daniel T. (ATP 250 Bastad (Nordea Open))
  • [tennis] Choinski J. vs Basilashvili N. (ATP 250 Bastad (Nordea Open))
  • [tennis] Travaglia S. vs Krumich M. (ATP 250 Bastad (Nordea Open))
  • [tennis] Borges N. vs Kouame M. (ATP 250 Bastad (Nordea Open))
  • [tennis] Altmaier D. vs Gaston H. (ATP 250 Bastad (Nordea Open))
  • [tennis] Dahlin M. vs Baez S. (ATP 250 Bastad (Nordea Open))
  • [tennis] Martinez P. vs Hanfmann Y. (ATP 250 Gstaad (EFG Swiss Open))
  • [tennis] Cerundolo J. vs Kolar Z. (ATP 250 Gstaad (EFG Swiss Open))
  • [tennis] Kym J. vs Dietrich D. (ATP 250 Gstaad (EFG Swiss Open))
  • [tennis] Cina F. vs Halys Q. (ATP 250 Gstaad (EFG Swiss Open))
  • [tennis] Muller A. vs Shevchenko A. (ATP 250 Gstaad (EFG Swiss Open))
  • [tennis] Tsitsipas S. vs Buse I. (ATP 250 Gstaad (EFG Swiss Open))
  • [tennis] Faria J. vs Wawrinka S. (ATP 250 Gstaad (EFG Swiss Open))
  • [tennis] Dodig M. vs Carreno-Busta P. (ATP 250 Umag (Plava Laguna Croatia Open))
  • [tennis] Molcan A. vs Royer V. (ATP 250 Umag (Plava Laguna Croatia Open))


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
