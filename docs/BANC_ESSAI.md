# Banc d'essai historique — ce que 35 000 matchs ont répondu

> Le protocole en direct produira ~120 prédictions en 100 jours. Il en faudrait
> ~6 800 pour trancher sur le ROI. Les archives ont permis d'y répondre en une
> session — et la réponse est nette.

## Méthode

Rejeu chronologique strict sur les archives football-data.co.uk :

1. **prédire** avec les seules données antérieures au coup d'envoi
2. **décider** face à la cote d'**ouverture** (celle qu'on prend vraiment la veille)
3. **seulement ensuite**, intégrer le résultat à l'historique

Toute inversion fait fuir le futur dans le passé. La calibration est apprise sur
2015-2020 et appliquée sur **2021-2025 uniquement** : jamais sur ses propres données.

## Résultat 1 — la calibration est un vrai gain

Le modèle compressait ses probabilités vers le milieu : il annonçait 75 % là où
la réalité était 89,5 %. Biais systématique, donc corrigeable.

| | erreur absolue moyenne |
|---|---|
| modèle brut | 5,3 pts |
| **modèle calibré, hors échantillon, 11 championnats** | **0,8 pt** |

```
55 % annoncé → 57,1 % réel      65 % → 65,5 %      75 % → 76,3 %      85 % → 84,6 %
```

**Acquis.** Le modèle sait dire vrai sur les probabilités.

## Résultat 2 — bien calibré ≠ avantage

Sur 14 452 paris hors échantillon :

| Issue | Paris | ROI | CLV |
|---|---|---|---|
| Domicile | 6 232 | −8,97 % | −0,64 % |
| Nul | 4 061 | −5,77 % | +0,26 % |
| Extérieur | 4 159 | **−17,37 %** | −1,73 % |

L'écart est le constat central :

```
erreur sur TOUTES les prédictions        0,8 pt
erreur sur les paris SÉLECTIONNÉS       ~12 pts
```

Là où le modèle s'écarte assez du marché pour déclencher un pari, **il a tort**.
Cet écart de 11 points EST l'avantage informationnel du marché, mesuré.

## Résultat 3 — le nul était du bruit

Sur les 5 grands championnats, le nul ressortait à ROI +1,40 % et CLV +0,89 %
(z = 2,60, significatif). Stable sur trois seuils d'edge. Tentant.

Test sur **6 championnats jamais utilisés** (Pays-Bas, Portugal, Turquie,
Belgique, Écosse, Grèce) :

| | 5 grands | 6 autres |
|---|---|---|
| ROI | +1,40 % | **−11,40 %** |
| CLV | +0,89 % | **−0,26 %** |

Réfuté. Trois issues avaient été testées : en trouver une positive était le
résultat attendu du hasard. Le ROI n'était d'ailleurs pas significatif —
intervalle [−7,2 % ; +10,0 %], il aurait fallu ~19 000 paris.

## Résultat 4 — le favori à domicile est le moins mauvais

| Probabilité minimale | Paris | ROI | CLV |
|---|---|---|---|
| ≥ 45 % | 2 811 | −4,07 % | +0,28 % |
| ≥ 55 % | 1 048 | −2,04 % | +0,40 % |
| ≥ 65 % | 529 | −1,53 % | +0,30 % |

Le ROI remonte vers zéro et le CLV devient légèrement positif à mesure qu'on se
restreint aux favoris — la **direction** du résultat de Wilkens (10 % de ROI en
Bundesliga sur les victoires à domicile), sans en atteindre le niveau.

Différence la plus probable : Wilkens utilise les **xG réels**, nous une
approximation par les tirs cadrés. C'est l'hypothèse suivante à tester.

## Ce qui reste ouvert

- **xG réels** (understat, 5 grands championnats) au lieu du proxy tirs cadrés
- **cotes d'ouverture plus précoces** : nos archives donnent une ouverture déjà
  tardive ; la recherche situe l'inefficience en J-4 à J-6
- **météo** : absente des archives, nécessiterait une source par stade et par date

## Ce qui est clos

Le modèle glissant, même parfaitement calibré, **ne bat pas le marché** sur
11 championnats et 10 saisons. Ce n'est pas une question de réglage : c'est
mesuré, hors échantillon, sur des dizaines de milliers de paris.

*Mode PAPER. Aucun euro engagé.*
