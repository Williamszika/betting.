# SportPredix — Workflow de travail

> Chaîne déterministe, sans agent, exécutable en 10 secondes.
> `PYTHONPATH=src python3 scripts/daily_engine.py [AAAA-MM-JJ] --min 1.75 --max 3.0`

---

## Les 5 étapes

### [1] DONNÉES — `ClubElo /Fixtures`
`http://api.clubelo.com/Fixtures` (**HTTP obligatoire**, HTTPS non supporté ; WebFetch
échoue en 503, il faut `curl`). Fournit pour chaque match du jour :
- la distribution complète des **écarts de buts** (GD<-5 … GD>5)
- la distribution des **scores exacts** (R:0-0 … R:6-0)

Couverture réelle mesurée le 02/08 : **40 matchs, 17 pays** (Autriche, Bulgarie, Croatie,
Tchéquie, Danemark, Hongrie, Norvège, Pologne, Roumanie, Écosse, Serbie, Suisse,
Slovénie, Suède, Ukraine…). Retry automatique sur 503.

### [2] MODÈLE — λ → matrice → 146 marchés
On déduit **λ_domicile** et **λ_extérieur** des probabilités de score exact
(λ = Σ p(i,j)·i). Puis `markets.all_goal_markets()` construit la matrice de scores
(Poisson × correction **Dixon-Coles ρ = −0,10**) et en dérive **146 marchés** :
1X2, Double Chance, DNB, handicaps européens, Over/Under 0.5→6.5, BTTS, scores exacts,
buts par équipe, pair/impair, Mi-temps/Fin, combos, corners, cartons.

### [3] CONTRÔLE — accord avec la référence
Notre 1X2 est comparé à celui de ClubElo. **Écart > 6 points sur une issue → le match
est écarté entièrement.** C'est le garde-fou anti-emballement : si notre modèle diverge
d'un modèle professionnel calibré, c'est nous qui avons tort.

*Mesure du 02/08 : 35 matchs sur 40 à moins de 3 points d'écart.*

### [4] SÉLECTION — fourchette de cotes
On ne garde que les marchés dont la **cote juste** (1/p) tombe dans la fourchette
demandée (défaut **1,75–3,00**). Cela élimine à la fois les favoris évidents
(sous-payés) et les paris trop risqués.

### [5] COUPON — 1 à 2 prédictions, matchs distincts
Classement par probabilité décroissante, **un seul pari par match** (pas de corrélation).

---

## La règle économique intégrée : la cote minimale

Betano **répercute** la taxe allemande de 5,3 % sur les gains. Le moteur calcule donc
pour chaque prédiction :

```
cote minimale utile = 1 / (0,947 × probabilité)
```

**En dessous de ce seuil, le pari est perdant d'avance** — quelle que soit la qualité de
l'analyse. C'est la seule protection réelle contre la taxe, et elle est automatique.

Exemple : probabilité 57,1 % → cote juste **1,75**, mais cote minimale **1,85**.
Si Betano affiche 1,80, on passe.

---

## Marchés autorisés au coupon

Uniquement ceux que Betano propose **partout**, y compris sur les petits championnats
(les props Opta et marchés exotiques disparaissent hors top-ligues) :

`1` · `X` · `2` · `DC 1X/X2/12` · `DNB 1/2` · `Over/Under 1.5/2.5/3.5` · `BTTS Oui/Non` ·
`Domicile marque` · `Extérieur marque` · `Domicile/Extérieur 2+` · `1 & Over 2.5` ·
`1 & BTTS` · `2 & Over 2.5`

---

## Ce que le workflow ne fait PAS (et pourquoi)

| | Raison |
|---|---|
| Il ne lit pas les cotes Betano | Site **géobloqué** (403). Le moteur fournit la cote minimale, l'utilisateur compare |
| Il n'utilise pas d'agents pour les probabilités | Les agents fabriquaient des edges (7 rejets sur 7 le 29/07). Le code calcule, point |
| Il ne propose pas de combiné > 2 jambes | Chaque jambe multiplie le risque ; historiquement, une jambe faible faisait tout tomber |
| Il ne force jamais une prédiction | Si rien n'entre dans la fourchette : « rien à proposer » |

---

## Contrôles automatiques

- ✅ Partitions vérifiées (1+X+2 = 1, Over+Under = 1, MT/Fin = 1)
- ✅ Accord avec ClubElo (drop si écart > 6 pts)
- ✅ Cote minimale après taxe sur chaque ligne
- ✅ Matchs distincts dans le coupon
- ✅ 59 tests unitaires (`pytest tests/`)

*Mode PAPER — 0 € misé. ESTIMATIONS, pas des certitudes.
Aide au jeu : joueurs-info-service.fr, 09 74 75 13 13.*
