# Rendez-vous automatiques SportPredix — prompts (mode PAPER, prédiction)

> Ces prompts remplacent les anciens (« coupon à jouer / mise »). Reframe :
> **prédiction**, mode **PAPER** (0 € misé), et **passage des règles de mémoire**
> au moteur (`lessons_rules.py --args` → `hardRules`/`softBlock`).
>
> Mettre à jour les triggers nécessite une approbation manuelle. En attendant,
> l'agent suit cette procédure à chaque déclenchement (les rendez-vous tombent
> dans la session).

## 🎯 Rendez-vous 20h — génération de prédiction (self-bind, cron `0 18 * * *`)

Trigger id : `trig_01Mjw8PuwLoXBFJfg2S9ZdvV`

```
[RENDEZ-VOUS AUTOMATIQUE 20h] Génère la PRÉDICTION SportPredix pour DEMAIN — mode PAPER (analyse seulement, 0 € misé, JAMAIS un feu vert pour parier). Football uniquement, catalogue Betano.de. Tu es déjà dans /home/user/betting..
1) git fetch origin && git checkout claude/sports-prediction-agents-wcwmiw && git pull origin claude/sports-prediction-agents-wcwmiw.
2) Détermine la date de DEMAIN. Charge la MÉMOIRE : lance `python3 scripts/lessons_rules.py --args` et récupère {hardRules, softBlock} (note les leçons orphelines signalées sur stderr).
3) Lance workflows/deep_research_coupon.js avec { date:"<demain>", bookmaker:"Betano", domain:"betano.de", couponTargetOdds:1.95, couponMaxOdds:3.0, oddsMin:5.0, oddsMax:7.0, maxPicks:2, maxMatches:3, prefilterFloor:0.35, hardRules:<hardRules>, softBlock:<softBlock> }. Le moteur consulte TOUS les marchés Betano et propose le MEILLEUR (pas forcément le 1X2) ; les règles hard excluent les combos interdits. Si la limite tombe, reprends (resumeFromRunId) après reset jusqu'au bout.
4) Journalise (scripts/log_coupon.py + scripts/build_dashboard.py), audite (scripts/audit_run.py <runId>), lance scripts/validate.py, écris data/coupon_<AAAA-MM-JJ>.md.
5) Commit + push (branche + main).
6) Résume la/les PRÉDICTION(S) football vérifiée(s) avec cote (à CONFIRMER sur Betano.de), le contexte, l'audit, l'état de la PORTE (PAPER). Si rien : « aucune prédiction crédible demain ». ESTIMATIONS, PAS des certitudes, PAS une invitation à miser ; jamais un match commencé.
```

## ⚖️ Rendez-vous 12h — règlement + validation (self-bind, cron `0 10 * * *`)

Trigger id : `trig_01GE4pwMa5T12Uvo514i84p7`

```
[RENDEZ-VOUS AUTOMATIQUE 12h] Règle les PRÉDICTIONS SportPredix dont les matchs sont terminés (mode PAPER, 0 € misé). Tu es déjà dans /home/user/betting..
1) git fetch origin && git checkout claude/sports-prediction-agents-wcwmiw && git pull.
2) Charge data/ledger.jsonl. Prends les prédictions status "pending" dont la date (id, AAAA-MM-JJ) est ANTÉRIEURE à aujourd'hui. Si aucune → « rien à régler », stop.
3) Vérifie les vrais résultats sur le web (score final ; gagné/perdu/void). Pour le CLV, récupère si possible la COTE DE CLÔTURE (dernière cote pré-match : Pinnacle/Oddspedia/betexplorer). RÉTRO honnête sur chaque perte.
4) Construis le JSON de règlement [{id, leg_results, settled, closing_odds:[...], retro}] puis scripts/apply_settlement.py + scripts/build_dashboard.py + scripts/validate.py.
5) Ajoute les leçons des rétros à data/lessons.md — AU FORMAT ```rule``` machine quand c'est une règle dure/douce (sinon en prose), sans doublon, daté. Vérifie via `python3 scripts/lessons_rules.py` qu'elle est bien chargée (pas orpheline). Commit + push (branche + main).
6) Résume : chaque prédiction 🟢/🔴 (score), le BILAN, la CALIBRATION + CLV + état de la PORTE. Factuel, sans complaisance. C'est de la validation, PAS une invitation à miser.
```

## Comment appliquer

Depuis une session interactive (les updates de trigger demandent une approbation) :
- soit copier ces prompts dans les triggers correspondants,
- soit approuver l'appel `update_trigger` quand l'agent le propose.
