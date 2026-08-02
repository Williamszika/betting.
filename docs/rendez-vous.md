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
[RENDEZ-VOUS 20h — PROTOCOLE 100 JOURS] Produis la prédiction SportPredix pour DEMAIN. Football uniquement, marchés jouables sur Betano.de, mode PAPER (bankroll simulée de 10 €, 0 € réellement misé). Tu es dans /home/user/betting..

1) git fetch origin && git checkout claude/sports-prediction-agents-wcwmiw && git pull origin claude/sports-prediction-agents-wcwmiw
2) `PYTHONPATH=src python3 scripts/protocol.py report` — situe le jour N/100 et la bankroll courante.
3) MÉMOIRE : `python3 scripts/lessons_rules.py --args` → {hardRules, softBlock}.
4) ÉTAGE 1 (moteur, déterministe) :
   `PYTHONPATH=src python3 scripts/daily_engine.py <DEMAIN> --min 1.75 --max 3.0 --json --shortlist 3`
   Si la shortlist est vide → « aucune prédiction crédible demain », enregistre rien, stop après le point 8.
5) ÉTAGE 2 (agents, contexte seulement) : Workflow scriptPath "workflows/cascade_verify.js"
   args { date:"<demain>", bookmaker:"Betano", domain:"betano.de", shortlist:<étage 1>, softBlock:<softBlock> }
   Les agents ne produisent AUCUNE probabilité — fixture, blessures, enjeu, cote Betano réelle.
6) SÉLECTION : garde AU PLUS 2 lignes validées, matchs distincts, cote dans [1,75 – 3,00].
   Une ligne validée mais dont la cote Betano est SOUS la cote minimale reste enregistrée —
   elle sera marquée non jouable par le calcul de mise. C'est voulu : la calibration
   se mesure sur toutes les prédictions, la bankroll seulement sur les jouables.
7) ENREGISTREMENT — pour chaque ligne, écris un JSON {id, date, match, competition, market, label, prob, odds}
   (id = "<AAAA-MM-JJ>-<n>", odds = cote Betano relevée, à défaut la cote juste), puis :
   `PYTHONPATH=src python3 scripts/protocol.py add --file <fichier>`
   La mise est calculée automatiquement (Kelly 1/5, taxe 5,3 %, plafond 5 %, minimum 0,20 €).
8) Écris data/coupon_<AAAA-MM-JJ>.md, commit + push sur la branche.
9) Résume : jour N/100, la/les prédiction(s) avec proba, cote, cote minimale, MISE ou
   « non jouable » + raison, et la bankroll. ESTIMATIONS, pas des certitudes.
   Pas d'incitation à miser.
```

## ⚖️ 08h00 — vérification des résultats de la veille

```
[RENDEZ-VOUS 8h — PROTOCOLE 100 JOURS] Vérifie les résultats des prédictions dont le match est terminé. Mode PAPER. Tu es dans /home/user/betting..

1) git fetch origin && git checkout claude/sports-prediction-agents-wcwmiw && git pull
2) Ouvre data/protocol.json. Prends les prédictions result="pending" dont la date est
   ANTÉRIEURE à aujourd'hui. Si aucune → « rien à vérifier », stop.
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
6) `PYTHONPATH=src python3 scripts/protocol.py report` — commit + push.
7) Résume : chaque résultat 🟢/🔴/⚪ avec le score, la bankroll, le bilan jour N/100,
   et la CALIBRATION (écart entre probabilité annoncée et réussite réelle).
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
