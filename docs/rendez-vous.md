# Rendez-vous automatiques — PROTOCOLE 100 JOURS

> Deux rendez-vous quotidiens, un seul objectif : produire 100 jours de
> prédictions **datées, chiffrées et vérifiées**, avec une bankroll suivie au
> centime. Mode **PAPER** — 0 € réellement misé, la bankroll de 10 € est simulée.
>
> Période : **3 août 2026 → 10 novembre 2026**.

| Heure locale | Rôle | Cron UTC (été) | Trigger |
|---|---|---|---|
| **20h00** | prédiction du LENDEMAIN | `0 18 * * *` | `trig_01Mjw8PuwLoXBFJfg2S9ZdvV` |
| **08h00** | vérification des résultats de la VEILLE | `0 6 * * *` | `trig_01GE4pwMa5T12Uvo514i84p7` |

> ⚠️ **Changement d'heure du 25 octobre 2026** (CEST → CET) : les crons doivent
> passer à `0 19 * * *` et `0 7 * * *` pour rester à 20h00 / 08h00 locales.
> Ce basculement tombe au **jour 84** du protocole.

---

## 🎯 20h00 — prédiction du lendemain

```
[RENDEZ-VOUS 20h — PROTOCOLE 100 JOURS] Produis la prédiction SportPredix pour DEMAIN. Football uniquement, mode PAPER (bankroll simulée de 10 €, 0 € réellement misé). Opérateur de référence : bet365 (il ABSORBE la taxe de 5,3 % depuis janvier 2024, ce qui divise par deux l'écart à créer face au marché). Tu es dans /home/user/betting..

1) git fetch origin && git checkout claude/sports-prediction-agents-wcwmiw && git pull origin claude/sports-prediction-agents-wcwmiw
2) `PYTHONPATH=src python3 scripts/protocol.py report` — jour N/100 et bankroll courante.
3) MÉMOIRE : `python3 scripts/lessons_rules.py --args` → {hardRules, softBlock}.

4) ÉCART MODÈLE / MARCHÉ — LE POINT DE DÉPART :
   `PYTHONPATH=src python3 scripts/edge_scan.py <DEMAIN> --book bet365 --min-gap 3`
   Croise notre modèle (ClubElo → Dixon-Coles) et les VRAIES cotes de
   football-data.co.uk (Pinnacle, moyenne, Betfair, bet365, maximum), marge retirée
   par la méthode PUISSANCE. C'est la seule mesure fiable d'un avantage.
   • Aucune ligne « ✅ » → il n'y a rien à jouer. Passer au point 5 pour la
     prédiction (calibration) mais AUCUNE mise ne sera possible.
   • Écart > 5 points → RÈGLE DURE : chercher un événement récent sur les 10 derniers
     jours (élimination européenne, changement d'entraîneur, cascade de blessures)
     sur les DEUX équipes. Sans explication trouvée ET vérifiée, la ligne n'est PAS
     jouable : le marché intègre l'information plus vite qu'un classement Elo.
     (Leçon FCSB : 7 points d'écart, éliminé 7-3 par Auda quatre jours avant → 2-2.)

5) ÉTAGE 1 (moteur déterministe) :
   `PYTHONPATH=src python3 scripts/daily_engine.py <DEMAIN> --min 1.75 --max 3.0 --json --shortlist 3`
   Chaîne d'accès : direct → Jina Reader → cache disque. ClubElo est en HTTP simple
   et le proxy ne fait que du HTTPS : le repli Jina n'est pas optionnel.
   Shortlist vide → « aucune prédiction crédible demain », rien à enregistrer.

6) ÉTAGE 2 (agents, contexte SEULEMENT) : Workflow scriptPath "workflows/cascade_verify.js"
   args { date:"<demain>", bookmaker:"bet365", domain:"bet365.de", shortlist:<étage 1>,
          softBlock:<softBlock> }
   Les agents ne produisent AUCUNE probabilité : fixture, blessures, enjeu, cote réelle.

7) SÉLECTION : au plus 2 lignes validées, matchs distincts, cote dans [1,75 – 3,00].
   Éviter les marchés à DEUX conditions (« 1 & Over 2.5 », « 1 & BTTS ») : ce sont des
   combinés déguisés en simples. La réponse à un favori trop court n'est pas d'y
   accoler une condition pour gonfler la cote — c'est de ne pas jouer le match.
   Une ligne validée dont la cote est sous le seuil reste enregistrée : la calibration
   se mesure sur TOUTES les prédictions, la bankroll seulement sur les jouables.

8) ENREGISTREMENT — un JSON par ligne :
   {id, date, match, competition, market, label, prob, odds, kickoff,
    market_prob, market_ref}
   • id = "<AAAA-MM-JJ>-<n>"
   • odds = MEILLEURE cote relevée (edge_scan la donne, avec l'opérateur), à défaut 0
   • kickoff = ISO AVEC SON FUSEAU D'ORIGINE, ex. "2026-08-08T21:30:00+03:00".
     Il détermine la date de vérification : un match à 22h45 finit après minuit.
   • market_prob / market_ref = probabilité de marché dévigorishée + sa source.
     NE JAMAIS l'inventer : sans référence, mettre 0.
   Puis `PYTHONPATH=src python3 scripts/protocol.py add --file <fichier>`
   (ajouter `--veto "<raison>"` si le contexte contredit le calcul).
   Mise calculée automatiquement : Kelly 1/5, taxe, plafond 5 %, minimum opérateur.

9) COUPON : `PYTHONPATH=src python3 scripts/coupon.py --date <DEMAIN>`
   Produit data/coupons/coupon_<DEMAIN>.html ET .png. Ne PAS utiliser --combine
   sauf demande explicite.

10) ⚠️ ENVOI OBLIGATOIRE — l'utilisateur ne voit PAS les fichiers du dépôt.
    SendUserFile({ files:["data/coupons/coupon_<DEMAIN>.png"], display:"render",
                   status:"proactive",
                   caption:"Coupon du <DEMAIN> — <ACTION> · bankroll <X,XX> €" })
    À faire MÊME si aucune mise n'est possible : un coupon « NE RIEN MISER » est
    une information, et son absence ressemble à une panne.

11) commit + push sur la branche.

12) RÉPONDRE DANS LA CONVERSATION — c'est le livrable, pas le commit. Structure :
    • titre : jour N/100, date, et l'ACTION en clair (miser X € / ne rien miser)
    • un bloc par prédiction : match, heure locale, marché, probabilité, cote,
      cote minimale, écart au marché, MISE ou raison du refus
    • les lignes ÉCARTÉES avec leur motif (fixture, veto contexte, seuil)
    • bankroll avant → après
    • ce qui a été appris ou constaté d'inhabituel
    ESTIMATIONS, pas des certitudes. Pas d'incitation à miser ; jamais un match
    déjà commencé. Si rien n'est jouable, le dire franchement en une phrase.
```

## ⚖️ 08h00 — vérification des résultats de la veille

```
[RENDEZ-VOUS 8h — PROTOCOLE 100 JOURS] Vérifie les résultats des prédictions dont le match est terminé. Mode PAPER. Tu es dans /home/user/betting..

1) git fetch origin && git checkout claude/sports-prediction-agents-wcwmiw && git pull
2) `PYTHONPATH=src python3 scripts/protocol.py pending` — la commande liste ce qui est
   PRÊT à vérifier et ce qui doit encore attendre. On vérifie le lendemain de la FIN du
   match (coup d'envoi + 2 h), PAS le lendemain de la date affichée : un match à 22h45
   se termine après minuit, donc un jour calendaire plus tard. Si rien n'est prêt →
   « rien à vérifier », stop.
3) Vérifie le VRAI résultat sur le web (score final, source nommée). Détermine
   won / lost / void pour le marché exact. En cas de doute sur le score : ne règle pas,
   redemande demain. Ne devine jamais.
4) `PYTHONPATH=src python3 scripts/protocol.py settle --id <id> --result won|lost|void --score "<score>"`
   La bankroll est mise à jour à la cote EFFECTIVE (après taxe 5,3 %).
5) RÉTRO honnête sur chaque perte : le modèle avait-il tort, ou le résultat était-il
   dans la variance annoncée ? Une prédiction à 55 % qui perd n'est PAS une erreur.
   N'ajoute une leçon à data/lessons.md que s'il y a une CAUSE identifiée et corrigeable,
   au format ```rule``` machine quand c'est une règle dure/douce. Vérifie avec
   `python3 scripts/lessons_rules.py` qu'elle n'est pas orpheline.
6) COUPON : `PYTHONPATH=src python3 scripts/coupon.py --date <date des matchs réglés>`
   MÊME commande qu'à 20h : le statut passe de ⏳ à 🟢/🔴 avec les scores, HTML et
   PNG régénérés au même emplacement.

7) ⚠️ ENVOI OBLIGATOIRE du coupon réglé :
   SendUserFile({ files:["data/coupons/coupon_<date>.png"], display:"render",
                  status:"proactive",
                  caption:"Résultats du <date> — <N> 🟢 / <N> 🔴 · bankroll <X,XX> €" })

8) `PYTHONPATH=src python3 scripts/protocol.py report` — commit + push.

9) RÉPONDRE DANS LA CONVERSATION :
   • chaque résultat 🟢/🔴/⚪ avec le score réel et la source
   • bankroll avant → après, et le bilan jour N/100
   • la CALIBRATION (écart entre probabilité annoncée et réussite réelle)
   • la section FACE AU MARCHÉ (sur les désaccords ≥3 points, le modèle a-t-il
     eu raison ?)
   • pour chaque perte : le modèle avait-il tort, ou était-ce la variance annoncée ?
   Factuel, sans complaisance.
```

---

## Ce que le protocole mesure vraiment

Sur 100 jours et ~100-150 prédictions, ce qu'on peut **statistiquement** conclure :

| Indicateur | Lisible à 100 jours ? | Pourquoi |
|---|---|---|
| **Calibration** (55 % annoncé → 55 % réalisé ?) | ✅ oui | converge vite, c'est le vrai test du modèle |
| **CLV** (cote battue vs cote de clôture) | ✅ oui | ~90-350 paris suffisent |
| **Bilan 🟢/🔴** | ⚠️ indicatif | la variance domine sur 100 paris |
| **ROI / bankroll finale** | ❌ non | il faudrait ~6 800 paris pour trancher |

Une bankroll finale à 12 € ne prouve rien. Une calibration juste sur 120 prédictions,
si. **C'est la calibration qu'on regarde**, pas le solde.

## La contrainte des 10 €

Kelly fractionnaire sur 10 € donne des mises de 0,20 à 0,50 €. Betano refuse en
dessous de **0,20 €** : un avantage réel mais modeste (edge de 5 % sur une cote à
1,95, par exemple) produit une mise de 0,12 € — **injouable**. Le protocole
l'enregistre quand même comme prédiction (pour la calibration) mais avec
`playable: false` et mise 0 €.

Conséquence : avec 10 €, seules les lignes à **fort edge** (>12 %) ou à **cote
élevée** franchissent le minimum. C'est une contrainte du capital, pas du modèle.

---

## 🎟️ Le coupon téléchargeable

Généré juste après le workflow, régénéré après les résultats :

```bash
# après la prédiction (20h) — statut « en attente »
PYTHONPATH=src python3 scripts/coupon.py --date 2026-08-03

# combiné plutôt que simples séparés
PYTHONPATH=src python3 scripts/coupon.py --date 2026-08-03 --combine

# après la vérification (8h) — MÊME commande, le statut se met à jour
PYTHONPATH=src python3 scripts/coupon.py --date 2026-08-03
```

Deux fichiers sont produits à chaque fois :

| Fichier | Usage |
|---|---|
| `data/coupons/coupon_<date>.html` | consultation, impression, clair/sombre |
| `data/coupons/coupon_<date>.png` | **partage WhatsApp / Telegram / SMS** |

Le PNG est capturé par Chromium en mode headless puis **recadré à la hauteur du
contenu** (sans ce recadrage, le coupon flotterait au sommet d'une image trois
fois trop haute). Largeur 1400 px, lisible sur téléphone.
`--no-png` saute la capture si seule la version HTML est voulue.

| Statut | Signification |
|---|---|
| ⏳ EN ATTENTE | match(s) pas encore joué(s) |
| 🟢 GAGNÉ | toutes les sélections passent |
| 🔴 PERDU | au moins une sélection tombe |
| ⚪ ANNULÉ | match annulé, mise rendue |
| 🚫 AUCUNE MISE | prédictions émises mais aucune jouable |

**Simple ou combiné.** En combiné, les cotes se multiplient — les probabilités
aussi. Deux paris à 55 % font un combiné à 30 %, pas à 55 %. Le coupon l'affiche
en toutes lettres pour que ce ne soit jamais une surprise.
