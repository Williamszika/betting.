==================================================================
AUDIT DU RUN — wf_eb4ba415-b8d
==================================================================
Agents lancés : 23 | terminés : 23 | en échec/incomplets : 0

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 12   Collecte des données (forme, xG, H2H, cotes…)
  🧩 Desk éditeur           × 3    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 3    Tous les marchés → opportunités de value (modèle croisé)
  🕵️ Vérificateur           × 2    Contrôle adversarial (match à venir ? cote ? logique ?)
  🔎 Découverte             × 1    Trouve les vrais matchs du jour (Betano.de)
  🎯 Coordinateur           × 1    Classe et dé-corrèle les opportunités
  📝 Synthèse/rédaction     × 1    Construit le coupon + note finale

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 14
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 7  (value, modèle × recherche)
  Vérifiées → gardées ........ 2 🟢  / écartées 0 🔴
  Coordination ............... 1  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [football] Spain vs Argentina (FIFA World Cup 2026 - Final)
  • [football] Elfsborg vs Sirius (Sweden - Allsvenskan)
  • [football] Halmstad vs Hacken (Sweden - Allsvenskan)
  • [football] Hammarby vs Degerfors (Sweden - Allsvenskan)
  • [football] Jaro vs Inter Turku (Finland - Veikkausliiga)
  • [football] Vestmannaeyjar (IBV) vs KA Akureyri (Iceland - Besta deild karla)
  • [football] KR Reykjavik vs Stjarnan (Iceland - Besta deild karla)
  • [football] Kuressaare vs Nomme Kalju (Estonia - Meistriliiga)
  • [football] Harju JK Laagri vs Paide (Estonia - Meistriliiga)
  • [football] Nomme United vs Narva Trans (Estonia - Meistriliiga)
  • [football] Ogre United vs BFC Daugavpils (Latvia - Virsliga)
  • [football] Altai vs Aktobe (Kazakhstan - Premier League)
  • [football] Ordabasy vs Yelimay Semey (Kazakhstan - Premier League)
  • [football] Ulytau vs Ertis Pavlodar (Kazakhstan - Premier League)


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
