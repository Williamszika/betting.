==================================================================
AUDIT DU RUN — wf_c6150fd8-563
==================================================================
Agents lancés : 34 | terminés : 34 | en échec/incomplets : 0

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 12   Collecte des données (forme, xG, H2H, cotes…)
  🕵️ Vérificateur           × 11   Contrôle adversarial (match à venir ? cote ? logique ?)
  🔎 Découverte             × 3    Trouve les vrais matchs du jour (Betano.de)
  🧩 Desk éditeur           × 3    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 3    Tous les marchés → opportunités de value (modèle croisé)
  🎯 Coordinateur           × 1    Classe et dé-corrèle les opportunités
  📝 Synthèse/rédaction     × 1    Construit le coupon + note finale

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 36
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 14  (value, modèle × recherche)
  Vérifiées → gardées ........ 7 🟢  / écartées 4 🔴
  Coordination ............... 1  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [football] Angleterre vs Argentine (Coupe du Monde FIFA 2026 - Demi-finale)
  • [football] Universitatea Craiova vs ML Vitebsk (UEFA Champions League 2026-27 - 1er tour de qualification (retour))
  • [football] Atert Bissen vs KI Klaksvik (UEFA Champions League 2026-27 - 1er tour de qualification (retour))
  • [football] Egnatia vs Petrocub Hincesti (UEFA Champions League 2026-27 - 1er tour de qualification (retour))
  • [football] Sutjeska Niksic vs Kairat Almaty (UEFA Champions League 2026-27 - 1er tour de qualification (retour))
  • [football] Decic vs FK Liepaja (UEFA Conference League 2026-27 - 1er tour de qualification (retour))
  • [tennis] Tomas Martin Etcheverry vs Daniel Merida (ATP Umag (Croatia Open) - ATP 250)
  • [tennis] Federico Gomez vs Matteo Arnaldi (ATP Umag (Croatia Open) - ATP 250)
  • [tennis] Pablo Carreno Busta vs Camilo Ugo Carabelli (ATP Umag (Croatia Open) - ATP 250)
  • [tennis] Flavio Cobolli vs Roman Andres Burruchaga (ATP Umag (Croatia Open) - ATP 250)
  • [tennis] Marco Trungelliti vs Alejandro Davidovich Fokina (ATP Umag (Croatia Open) - ATP 250)
  • [tennis] Luca Van Assche vs Titouan Droguet (ATP Umag (Croatia Open) - ATP 250)
  • [tennis] Dino Prizmic vs Alex Molcan (ATP Umag (Croatia Open) - ATP 250)
  • [tennis] Raphael Collignon vs Lorenzo Sonego (ATP Gstaad (Swiss Open) - ATP 250)
  • [tennis] Arthur Rinderknech vs Clement Tabur (ATP Gstaad (Swiss Open) - ATP 250)
  • [tennis] Yannick Hanfmann vs Valentin Vacherot (ATP Gstaad (Swiss Open) - ATP 250)
  • [tennis] Jerome Kym vs Stefanos Tsitsipas (ATP Gstaad (Swiss Open) - ATP 250)
  • [tennis] Botic van de Zandschulp vs Adolfo Vallejo (ATP Bastad (Nordea Open) - ATP 250)
  • [tennis] Nuno Borges vs Grigor Dimitrov (ATP Bastad (Nordea Open) - ATP 250)
  • [tennis] Stefano Travaglia vs Mariano Navone (ATP Bastad (Nordea Open) - ATP 250)

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.9) ODDS MISREPRESENTED: The real consensus market for Bellingham anytime goalscorer is ~3.60 (13/5) to 3.80 (1xBe
  🔴 (conf 0.68) Match reel et bien programme mercredi 15 juillet 2026 (17:30 UTC / 20:30 local, Ion Oblemenco), statut 'Not st
  🔴 (conf 0.82) Match confirme et a venir: Universitatea Craiova vs ML Vitebsk, UCL 2026-27 1er tour qualif, MANCHE RETOUR, me
  🔴 (conf 0.82) Fixture is real and upcoming: England vs Argentina, WC 2026 semi-final, Wed 15 July 2026, Atlanta, KO 3pm ET /


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
