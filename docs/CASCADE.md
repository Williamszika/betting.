# La cascade — le workflow complet en 2 étages

> Le calcul au code, le contexte aux agents. Chacun fait ce qu'il sait faire.

```
┌─ ÉTAGE 1 — MOTEUR (déterministe, 10 s, ~0 token) ─────────────────────────┐
│  scripts/daily_engine.py --json --shortlist 3                             │
│                                                                            │
│  ClubElo /Fixtures (+ cache disque)                                        │
│    → 40 matchs, 17 pays                                                    │
│    → λ domicile/extérieur depuis les scores exacts                         │
│    → matrice Dixon-Coles → 146 marchés par match                           │
│    → contrôle d'accord avec ClubElo (écart 1X2 > 6 pts = match écarté)     │
│    → filtre fourchette de cotes (1,75–3,00)                                │
│    → SHORTLIST : les 3 meilleures lignes, matchs distincts                 │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │  JSON
┌───────────────────────────────▼────────────────────────────────────────────┐
│ ÉTAGE 2 — AGENTS (contextuel, ~200 k tokens, 3 agents)                     │
│  workflows/cascade_verify.js                                               │
│                                                                            │
│  1 agent PAR LIGNE — interdiction absolue de produire une probabilité :    │
│    ① FIXTURE   le match a-t-il lieu ? reporté / annulé / huis clos ?       │
│    ② CONTEXTE  blessure, suspension, turnover, enjeu atypique, météo       │
│    ③ COTE      relever la cote RÉELLE Betano, comparer au seuil            │
│    ④ MARCHÉ    ce marché existe-t-il sur cette compétition chez Betano ?   │
│                                                                            │
│  VETO FIXTURE : une seule alerte écarte la ligne                           │
│    → note finale : VALIDÉ (le pari tient) vs JOUABLE (+ cote suffisante)   │
└────────────────────────────────────────────────────────────────────────────┘
```

## Pourquoi deux étages

| | Étage 1 seul | Étage 2 seul (ancien workflow) | **Cascade** |
|---|---|---|---|
| Durée | 10 s | 60-90 min | **~15 min** |
| Coût | ~0 | ~1,7 M tokens | **~200 k tokens** |
| Matchs balayés | 40 | 3-5 | **40** |
| Marchés | 146 | 6 | **146** |
| Probabilités | calculées ✅ | inventées ❌ | **calculées** ✅ |
| Contexte terrain | ❌ | ✅ | **✅** |
| Vérification fixture | ❌ | ✅ | **✅** |
| Cote Betano réelle | ❌ | ✅ | **✅** |

**Le gain de 8× sur le coût** vient du fait que les agents ne travaillent plus que sur
**3 lignes déjà sélectionnées**, au lieu de rechercher, consolider et coter 5 matchs entiers.

## Le principe qui gouverne tout

> **Le code calcule. Les agents constatent.**

Les agents ne produisent aucune probabilité, aucun λ, aucun edge. C'est la correction
directe du 29/07, où 7 propositions sur 7 ont été rejetées pour edges fabriqués
(« λ Poisson rétro-ingénieré », « edge inversé au signe annoncé », « corrélation à
l'envers »). Un agent qui ne calcule pas ne peut pas fabriquer.

## Lancer la cascade

```bash
# Étage 1 — shortlist
PYTHONPATH=src python3 scripts/daily_engine.py 2026-08-03 \
    --min 1.75 --max 3.0 --json --shortlist 3

# Étage 2 — passer la shortlist au workflow
Workflow({ scriptPath: "workflows/cascade_verify.js",
           args: { date: "3 août 2026", bookmaker: "Betano", domain: "betano.de",
                   shortlist: <shortlist de l'étage 1>,
                   softBlock: <sortie de scripts/lessons_rules.py --args> } })
```

## Les deux notions à ne pas confondre

- **VALIDÉE** : le match a lieu, aucune info ne casse le raisonnement, le marché existe.
  → la prédiction est bonne.
- **JOUABLE** : validée **et** la cote Betano dépasse la cote minimale
  (`1 / (0,947 × p)`, taxe 5,3 % incluse).
  → seulement là, il y a un intérêt économique.

Une prédiction peut être **excellente et injouable** : c'est le cas le plus fréquent sur
les favoris, systématiquement sous-payés. Le dire est un résultat, pas un échec.

*Mode PAPER — 0 € misé.*
