# Le panel — comment les agents travaillent ensemble

> **Un agent par tâche textuelle, du code pour tout ce qui est numérique,
> un adversaire structuré avant toute sortie.**

## Les 7 phases

| # | Phase | Qui | Où |
|---|---|---|---|
| 0 | Mémoire + porte papier | code | `lessons_rules.py`, `protocol.py` |
| 1 | Découverte des matchs | code | `daily_engine.py` |
| 2 | Chiffres déterministes | code | `footballdata`, `rolling`, `markets` |
| 3 | **Contexte terrain** | **agents** | `panel_predict.js` |
| 4 | Filtre de value | code | `edge_scan.py` |
| 5 | **Contradiction** | **agent** | `panel_predict.js` |
| 6 | **Synthèse** | **agent** | `panel_predict.js` |
| 7 | Registre + CLV + leçons | code | `protocol.py`, `lessons.md` |

Cinq phases sur sept sont du **code**. Les agents n'interviennent que là où un
programme échoue : lire l'actualité, contredire, rédiger.

---

## Phase 2 — les chiffres (code, jamais un agent)

| Donnée | Source | Fenêtre | Pourquoi |
|---|---|---|---|
| Distribution de scores | ClubElo | courante | force intrinsèque, mise à jour après chaque match |
| Buts + tirs cadrés | football-data.co.uk | 10 matchs | proxy xG, meilleur prédicteur que les buts seuls |
| Cotes ouverture + clôture | Pinnacle, bet365, Betfair, max | depuis l'ouverture | probabilité implicite et direction du mouvement |
| Moyennes de ligue | calculées | saison | base de régression pour petits échantillons |
| Repos et congestion | calendrier | 14 jours | la fatigue se mesure sur les buts de seconde période |
| Enjeu de fin de saison | classement au moment du match | — | titre, Europe, relégation |

Le **H2H historique** est délibérément absent : les effectifs changent, deux
confrontations de 2023 ne disent presque rien sur samedi.

### Traitement, dans l'ordre

1. **Forces** — attaque de A × faiblesse de B × moyenne de la ligue, chaque terme
   normalisé. Une ligue à 3,2 buts et une à 2,3 ne peuvent pas être traitées pareil.
2. **Rétrécissement** — sur 10 matchs, une équipe à 2,4 xG/match est probablement
   en surperformance. On ramène vers la moyenne d'un facteur `n/(n+10)`.
   *L'anti-recency-bias est codé, pas laissé au jugement d'un agent.*
3. **Ajustements textuels bornés** — les faits des agents deviennent des
   multiplicateurs **plafonnés à 15 %**, catégories fermées, faits inconnus ignorés.
   *L'agent propose, le code borne.*
4. **Matrice unique** — Poisson + Dixon-Coles. Tous les marchés dérivent de la
   **même** matrice : c'est ce qui garantit qu'un Over 2.5 à 58 % et un BTTS à
   61 % ne se contredisent jamais.
5. **Calibration** — courbe apprise sur une période, appliquée sur une autre.
   Mesuré : **erreur de 5,3 pts → 0,8 pt**.

---

## Phase 3 — l'agent contexte

Un agent par match. **Cinq catégories, pas une de plus :**

1. **Absences** — nom du joueur et rôle. Perdre un buteur titulaire n'est pas
   perdre un remplaçant.
2. **Rotation** — turnover annoncé, gardien n°2, échéance européenne proche.
3. **Enjeu** — le `context_flag` : `normal`, `finale`, `barrage`, `sans_enjeu`,
   `tie_plie`, `derby`.
4. **Mouvement de cote** — si elle a bougé de plus de 10 %, *pourquoi* ? Un
   mouvement inexpliqué signale une information que le marché a et nous pas.
5. **Conditions extrêmes** — météo violente, terrain, huis clos. **Uniquement si
   exceptionnel** : une météo ordinaire n'est pas un fait.

Chaque fait sort au format `{catégorie, fait, source, date, équipe, poids}`.
**Non daté ou non sourcé → rejeté par le code**, avant d'atteindre le modèle.
Une absence datant de plus de 7 jours est périmée.

### Ce qu'il ne faut surtout PAS chercher

Les **séries narratives** (« invaincu à domicile depuis 8 matchs ») sont du
cherry-picking sans valeur prédictive. La **possession** corrèle mal avec les buts.
Les **corners et cartons historiques** sont très bruités. Les **déclarations
d'avant-match** sont du bruit pur.

*Chaque donnée inutile rapportée est un point d'ancrage de plus pour le
contradicteur en aval.*

---

## Phase 5 — le contradicteur

**Checklist fermée, pas de critique libre.** Une critique libre produit des
objections décoratives ; une liste de questions fermées produit des réponses
vérifiables.

① Chaque fait porte-t-il source **et** date de moins de 7 jours ?
② Le `context_flag` autorise-t-il **ce** marché ?
③ Une règle de la mémoire s'y oppose-t-elle ?
④ La cote relevée est-elle plausible et sourcée ?

**Un seul échec suffit.** Ne rien proposer coûte zéro ; proposer à tort coûte la
mise *et* la confiance.

C'est ici que `data/lessons.md` entre dans le prompt — le seul endroit où le
système parle à ses agents de ce qu'il a appris de ses pertes.

---

## Les vetos, appliqués par le code

| Drapeau | Interdit | Leçon |
|---|---|---|
| `sans_enjeu` | 1X2, DC, DNB | France 6-4 — favori à 57 % balayé |
| `finale`, `barrage` | 1X2 90 min | Espagne 0-0 à 90, but en prolongation |
| `tie_plie` | marchés de buts | Craiova 1-0, tie plié 4-1 |
| fixture non confirmée | **tout** | Wings-Liberty, puis Larne |

La finesse compte : `sans_enjeu` écarte le 1X2 mais **garde l'Over** — ce jour-là
l'Over aurait gagné avec 10 buts.

---

## Ce que les mesures disent de cette architecture

Backtest sur **35 000 matchs**, 11 championnats, hors échantillon :

| | |
|---|---|
| Calibration du modèle | **0,8 pt d'erreur** ✅ |
| Erreur sur les paris sélectionnés | **~12 pts** ❌ |
| ROI toutes issues | négatif |
| Rétrécissement vers le marché | **aggrave** le ROI |

Le modèle est excellent tant qu'on ne lui demande pas de **choisir**. Là où il
s'écarte assez du marché pour déclencher un pari, il a tort — ces 11 points
d'écart sont l'avantage informationnel du marché, mesuré.

> Ce panel produit des **prédictions honnêtes**, pas un avantage démontré.
> La porte papier reste fermée tant que le registre n'affiche pas 100+
> prédictions à CLV positif.

*Mode PAPER — 0 € misé.*
