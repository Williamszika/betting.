==================================================================
AUDIT DU RUN — wf_37ac7f2b-d09
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
  Matchs découverts .......... 28
  Agents spécialistes ........ 12  (données brutes + sources)
  Fiches de faits (desk) ..... 3  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 12  (value, modèle × recherche)
  Vérifiées → gardées ........ 4 🟢  / écartées 3 🔴
  Coordination ............... 1  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [football] France vs Angleterre (Coupe du Monde 2026 - Match pour la 3e place)
  • [football] HamKam (Hamarkameratene) vs Tromsø (Eliteserien (Norvège))
  • [football] Kristiansund BK vs Sarpsborg 08 (Eliteserien (Norvège))
  • [football] Lillestrøm vs KFUM Oslo (Eliteserien (Norvège))
  • [football] IK Start vs Rosenborg (Eliteserien (Norvège))
  • [football] Molde FK vs SK Brann (Eliteserien (Norvège))
  • [football] Viking FK vs Sandefjord (Eliteserien (Norvège))
  • [football] AIK vs GAIS (Allsvenskan (Suède))
  • [football] HJK Helsinki vs VPS (Veikkausliiga (Finlande))
  • [football] AC Oulu vs IF Gnistan (Veikkausliiga (Finlande))
  • [football] SJK Seinäjoki vs KuPS (Veikkausliiga (Finlande))
  • [football] IK Oddevold vs Varbergs BoIS (Superettan (Suède, D2))
  • [football] Östersunds FK vs Landskrona BoIS (Superettan (Suède, D2))
  • [football] Östers IF vs IK Brage (Superettan (Suède, D2))
  • [football] Þór Akureyri vs Víkingur Reykjavík (Besta deild karla (Islande))
  • [football] Valur vs Fram Reykjavík (Besta deild karla (Islande))
  • [football] Pumas UNAM vs Pachuca (Liga MX - Apertura 2026, Jornada 1 (Mexique))
  • [football] Guadalajara (Chivas) vs Toluca (Liga MX - Apertura 2026, Jornada 1 (Mexique))
  • [football] Monterrey vs Santos Laguna (Liga MX - Apertura 2026, Jornada 1 (Mexique))
  • [football] Querétaro vs Club América (Liga MX - Apertura 2026, Jornada 1 (Mexique))

--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---
  🔴 (conf 0.9) PREMISSE INVERSEE (fatal): l'argument prete a HamKam une prob de victoire de base (0,41) SUPERIEURE a Tromso (
  🔴 (conf 0.82) Fixture OK: France vs Angleterre, match pour la 3e place WM 2026, samedi 18/07/2026, Miami, coup d'envoi 21h00
  🔴 (conf 0.7) Fixture confirmed and still upcoming: France vs England, WC 2026 third-place playoff, Sat 18 July 2026, 5pm ET


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
