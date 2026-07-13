==================================================================
AUDIT DU RUN — wf_eaac61ac-ea2
==================================================================
Agents lancés : 109 | terminés : 95 | en échec/incomplets : 14

--- QUI A TRAVAILLÉ (par rôle) ---
  📚 Spécialiste recherche  × 82   Collecte des données (forme, xG, H2H, cotes…)
  🧩 Desk éditeur           × 9    Réconcilie/vérifie les faits + stats chiffrées
  🔎 Découverte             × 3    Trouve les vrais matchs du jour (Betano.de)
  • Autre                  × 1    
  📊 Analyste marchés       × 0    Tous les marchés → opportunités de value (modèle croisé)
  🕵️ Vérificateur           × 0    Contrôle adversarial (match à venir ? cote ? logique ?)

--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---
  Matchs découverts .......... 21
  Agents spécialistes ........ 82  (données brutes + sources)
  Fiches de faits (desk) ..... 9  (réconciliées + stats chiffrées)
  Opportunités de marché ..... 0  (value, modèle × recherche)
  Vérifiées → gardées ........ 0 🟢  / écartées 0 🔴
  Coordination ............... 0  → construction du coupon

--- MATCHS ANALYSÉS ---
  • [tennis] Lorenzo Sonego vs Joel Schwaerzler (ATP 250 EFG Swiss Open Gstaad)
  • [tennis] Kilian Feldbausch vs Miomir Kecmanovic (ATP 250 EFG Swiss Open Gstaad)
  • [tennis] Dominic Stricker vs Jaume Munar (ATP 250 EFG Swiss Open Gstaad)
  • [tennis] Clement Tabur vs Jurij Rodionov (ATP 250 EFG Swiss Open Gstaad)
  • [tennis] Raphael Collignon vs Timofey Skatov (ATP 250 EFG Swiss Open Gstaad)
  • [tennis] Damir Dzumhur vs Henrique Rocha (ATP 250 Plava Laguna Croatia Open Umag)
  • [tennis] Dusan Lajovic vs Luca Van Assche (ATP 250 Plava Laguna Croatia Open Umag)
  • [tennis] Vit Kopriva vs Dino Prizmic (ATP 250 Plava Laguna Croatia Open Umag)
  • [tennis] Kyrian Jacquet vs Marco Trungelliti (ATP 250 Plava Laguna Croatia Open Umag)
  • [tennis] Jesper de Jong vs Vilius Gaubas (ATP 250 Nordea Open Bastad)
  • [football] Djurgårdens IF vs Halmstads BK (Allsvenskan (Suède, 1re division))
  • [football] Breiðablik (Kópavogur) vs Keflavík ÍF (Besta deild karla (Islande, 1re division) — 14e journée)
  • [football] Vestri vs Fylkir (1. deild karla (Islande, 2e division))
  • [basketball] Detroit Pistons vs New York Knicks (NBA Summer League (Las Vegas))
  • [basketball] Toronto Raptors vs Indiana Pacers (NBA Summer League (Las Vegas))
  • [basketball] Atlanta Hawks vs Boston Celtics (NBA Summer League (Las Vegas))
  • [basketball] Dallas Mavericks vs Memphis Grizzlies (NBA Summer League (Las Vegas))
  • [basketball] Miami Heat vs Cleveland Cavaliers (NBA Summer League (Las Vegas))
  • [basketball] Chicago Bulls vs Utah Jazz (NBA Summer League (Las Vegas))
  • [basketball] Phoenix Suns vs Milwaukee Bucks (NBA Summer League (Las Vegas))


COMMENT LE COUPON EST CRÉÉ (algorithme) :
1. Chaque opportunité a : cote (Betano.de/Flashscore) + proba finale = BLEND(modèle Poisson, recherche).
2. VALUE = proba × cote − 1. On ne garde que value > 0.
3. VÉRIFICATION adversariale : match encore à venir ? cote réelle ? raisonnement solide ? (sinon écarté)
4. Le solveur choisit la combinaison de jambes (matchs DISTINCTS) dont la cote totale
   tombe dans la fourchette (défaut 1,95–3) en MAXIMISANT la proba conjointe (le plus « sûr »).
5. COMBIEN : 1 coupon combiné par jour (+ jusqu'à 2 paris simples cote 5–7 en option).
   Rien n'est forcé : si aucune combi ne rentre ou si rien ne passe la vérif → « rien à parier ».
