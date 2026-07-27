==================================================================
AUDIT DU RUN — wf_1f327ed3-424
==================================================================
Agents lancés : 25 | terminés : 25 | en échec/incomplets : 0

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 12   Collecte des données (forme, xG, H2H, cotes…)
  🕵️ Vérificateur           × 6    Contrôle adversarial (match à venir ? cote ? logique ?)
  🧩 Desk éditeur           × 3    Réconcilie/vérifie les faits + stats chiffrées
  📊 Analyste marchés       × 3    Tous les marchés → opportunités de value (modèle croisé)
  🔎 Découverte             × 1    Trouve les vrais matchs du jour (Betano.de)

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 22
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 7  (value, modèle × recherche)
  Vérifiées → gardées ........ 0 🟢  / écartées 6 🔴
  Coordination ............... 0  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [football] Heart of Midlothian vs Sturm Graz (UEFA Champions League - 2e tour de qualification (retour))
  • [football] Dinamo Zagreb vs FC Thun (UEFA Champions League - 2e tour de qualification (retour))
  • [football] NK Celje vs KF Egnatia (UEFA Champions League - 2e tour de qualification (retour))
  • [football] Shamrock Rovers vs Ararat-Armenia (UEFA Champions League - 2e tour de qualification (retour))
  • [football] KuPS Kuopio vs Sabah FK (UEFA Champions League - 2e tour de qualification (retour))
  • [football] Lincoln Red Imps vs Mjallby AIF (UEFA Champions League - 2e tour de qualification (retour))
  • [football] Drita Gjilan vs Floriana FC (UEFA Conference League - 2e tour de qualification (retour))
  • [football] Apollon Limassol vs Dila Gori (UEFA Conference League - 2e tour de qualification (retour))
  • [football] Riga FC vs Vardar Skopje (UEFA Conference League - 2e tour de qualification (retour))
  • [football] CSKA 1948 Sofia vs Spartak Trnava (UEFA Conference League - 2e tour de qualification (retour))
  • [football] Landskrona BoIS vs IFK Norrkoping (Suede - Superettan (J16))
  • [football] Helsingborgs IF vs Nordic United FC (Suede - Superettan (J16))
  • [football] Nasaf Qarshi vs Qizilqum Zarafshon (Ouzbekistan - Superliga)
  • [football] Xorazm Urganch vs Surkhon Termez (Ouzbekistan - Superliga)
  • [football] Neftchi Fergana vs Navbahor Namangan (Ouzbekistan - Superliga)
  • [football] Philippines vs Myanmar (ASEAN Championship (Hyundai Cup) - Groupe B)
  • [football] Malaysia vs Laos (ASEAN Championship (Hyundai Cup) - Groupe B)
  • [football] Hapoel Haifa vs Ironi Tiberias (Israel - Toto Cup (Ligat ha'Al))
  • [football] Hapoel Ironi Kiryat Shmona vs Maccabi Haifa (Israel - Toto Cup (Ligat ha'Al))
  • [football] B36 Torshavn vs AB Argir (Iles Feroe - Betri deildin)

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.82) FIXTURE OK: Hearts v Sturm Graz confirme le 28/07/2026 19:45 GMT a Tynecastle (2e tour qual. UCL, retour). All
  🔴 (conf 0.72) FIXTURE CONFIRMEE (3 sources independantes) : Heart of Midlothian vs Sturm Graz, mardi 28 juillet 2026, 20:45 
  🔴 (conf 0.86) FAIT OMIS DECISIF — L'ALLER S'EST TERMINE STURM GRAZ 4-0 HEARTS (21/07/2026, doublé de Jon Gorenc Stankovic, 2
  🔴 (conf 0.78) FIXTURE CONFIRMEE : BetExplorer (liste des fixtures UCL 2026/27) affiche 'Tomorrow 20:15 - Celje vs Egnatia' ;
  🔴 (conf 0.85) FIXTURE OK — Dinamo Zagreb vs FC Thun, UCL Q2 retour, mardi 28/07/2026 18:00 UTC (20:00 CEST) au Maksimir. Sof
  🔴 (conf 0.82) ERREUR ARITHMETIQUE QUI DETRUIT L'EDGE : le 'fair' sharp annonce est faux. 0,551 (Thoune marque, Pinnacle) x 0


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
