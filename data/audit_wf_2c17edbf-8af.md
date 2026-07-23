==================================================================
AUDIT DU RUN — wf_2c17edbf-8af
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
  Matchs découverts .......... 16
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 8  (value, modèle × recherche)
  Vérifiées → gardées ........ 1 🟢  / écartées 1 🔴
  Coordination ............... 1  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [football] Radomiak Radom vs Wieczysta Kraków (Pologne - Ekstraklasa (1re journée 2026/27))
  • [football] Pogoń Szczecin vs Legia Warszawa (Pologne - Ekstraklasa (1re journée 2026/27))
  • [football] Tigres UANL vs Atlético San Luis (Mexique - Liga MX (Apertura 2026, Jornada 2))
  • [football] Club Tijuana vs León (Mexique - Liga MX (Apertura 2026, Jornada 2))
  • [football] Atlante vs Club América (Mexique - Liga MX (Apertura 2026, Jornada 2))
  • [football] Gimnasia y Esgrima (Mendoza) vs Central Córdoba (SdE) (Argentine - Liga Profesional (Torneo Clausura 2026, Fecha 1))
  • [football] Racing Club vs Gimnasia y Esgrima (La Plata) (Argentine - Liga Profesional (Torneo Clausura 2026, Fecha 1))
  • [football] Vélez Sarsfield vs Instituto (Argentine - Liga Profesional (Torneo Clausura 2026, Fecha 1))
  • [football] Huracán vs Banfield (Argentine - Liga Profesional (Torneo Clausura 2026, Fecha 1))
  • [football] Platense vs Unión (Argentine - Liga Profesional (Torneo Clausura 2026, Fecha 1))
  • [football] Llaneros vs Deportivo Pereira (Colombie - Liga BetPlay Dimayor (II-2026, Fecha 1))
  • [football] Deportivo Cali vs Jaguares (Colombie - Liga BetPlay Dimayor (II-2026, Fecha 1))
  • [football] Västerås SK vs Örgryte IS (Suède - Allsvenskan)
  • [football] FF Jaro vs SJK Seinäjoki (Finlande - Veikkausliiga (20e journée))
  • [football] Galway United vs Waterford (Irlande - League of Ireland Premier Division)
  • [football] Víkingur Reykjavík vs Keflavík (Islande - Besta deild karla)

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.9) FIXTURE DEPLACE (motif du drop): le match a ete deplace du vendredi 24 juillet (creneau initial 19:00) au SAME


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
