# SportPredix — Méthode de travail du cabinet

> Document de référence. Établi le 2026-08-02 après audit par un panel de 4 experts
> (données, marchés/trading, modélisation, bookmaker). Mode **PAPER** : 0 € misé.

---

## 1. Le verdict économique — à lire avant tout le reste

Le panel a établi l'arithmétique de rentabilité sur Betano.de. Elle est sans appel.

| Poste | Valeur | Source |
|---|---|---|
| Marge Betano 1X2 | **4,11 %** | 365BettingTips, n≈2 100 |
| Taxe allemande (§ 18 RennwLottG) | **5,3 %**, **NON absorbée** par Betano | Betano : *« Nur im Gewinnfall wird eine Gebühr von 5,3 % vom Gewinn abgezogen »* |
| **Coût total à battre** | **≈ 9–10 %** | |
| Edge réaliste d'un modèle amateur vs clôture | **0 %** | Calibration des cotes r = 0,995 (52 411 cotes) ; pente CLV→EV = 1,00 (87 960 paires) |

**Conséquence : il faut prendre des prix ≥ +5,6 % au-dessus du juste prix rien que pour
être à l'équilibre**, alors que le prix moyen de Betano est déjà ~4 % en dessous.
Un système rentable sur Betano.de seul est **arithmétiquement impossible**.

### Les trois preuves qui ferment le débat

1. **Les cotes sont quasi parfaitement calibrées** : corrélation 0,995 entre probabilité
   implicite et fréquence réalisée (52 411 cotes).
2. **Les pros ne battent pas ça non plus** : 8 tipsters classés « PRO » à +6,7 % sur
   11 233 paris → **−2,2 % sur les 3 687 suivants**. Corrélation passé/futur : **0,00077**.
3. **La seule stratégie documentée qui gagne (+2-3 %) est illégale ici** : elle exige de
   scanner 20-30 books simultanément, or le **§ 6h GlüStV interdit d'être actif chez
   plus d'un opérateur allemand à la fois**. Pinnacle a quitté l'Allemagne en 2016.

---

## 2. Ce que nous visons désormais

Le projet **n'est pas** une machine à profit — cette voie est fermée, chiffres à l'appui.
Le projet est un **moteur de prédiction calibré, honnête et mesurable**, validé
scientifiquement, en mode PAPER.

**Objectif mesurable :** que notre modèle brut atteigne un **RPS comparable aux
bookmakers** sur les compétitions couvertes, et une **CLV moyenne > 0** contre la clôture
dé-margée. Si on y arrive, on aura construit quelque chose de réel. Sinon, on l'aura
prouvé — sans avoir misé un centime.

---

## 3. Le cabinet — 4 pôles

| Pôle | Responsabilité | Livrable |
|---|---|---|
| 📊 **Données** | Alimenter le moteur en données brutes vérifiées | Elo, xG, calendriers, **cotes de clôture** |
| 🔬 **Modélisation** | Produire des probabilités calibrées | λ par équipe, distribution de scores |
| 💹 **Marchés** | Dé-margeage correct, détection de value, CLV | prix justes, edge net |
| ⚖️ **Contrôle** | Vérification adversariale, garde-fous, mémoire | verdicts keep/drop, leçons exécutables |

---

## 4. Les sources — testées, pas supposées

### ✅ Ce qui fonctionne (vérifié HTTP 200)

| Source | URL | Apport | Piège |
|---|---|---|---|
| **football-data.co.uk** | `/mmz4281/2526/E0.csv` | **COTES DE CLÔTURE** (10 books), 32 divisions + fichiers `/new/` (Brésil, Argentine, USA, Japon, Scandinavie…) | Pinnacle absent en 25/26 → **ancrer sur `AvgC*`**, pas `PSC*` |
| **ClubElo** | `http://api.clubelo.com/Fixtures` | Elo + **probabilités par score exact** = modèle de référence gratuit | **HTTP obligatoire** (WebFetch force HTTPS → 503) ; utiliser `curl` |
| **ESPN (API cachée)** | `site.api.espn.com/.../soccer/eng.1/scoreboard` | Cotes DraftKings open/close, temps réel | Écrasées après le match → snapshot uniquement |
| **OpenLigaDB** | `api.openligadb.de/getmatchdata/bl1/2026` | Calendrier/résultats Bundesliga | — |
| **Understat** | POST `/main/getPlayersStats/` | xG, xA, npxG par joueur | GET des pages ligue vidé de ses données |
| **Betano Help Center** | `support.betano.de/api/v2/help_center/de/articles.json` | 296 articles officiels (règles, limites, taxe) | Seule source Betano non géobloquée |

### ❌ Ce qui ne fonctionne pas
FBref (403) · Sofascore (403) · Pinnacle (403) · Betfair (451) · oddsportal & betexplorer
(200 mais coquilles JS sans cotes) · **navigateur headless : bloqué sur TOUTES les cibles**
(`ERR_CONNECTION_RESET`, même example.com) · **betano.de : géobloqué** (pas anti-bot —
une IP allemande suffirait).

---

## 5. Le workflow professionnel — 6 phases

```
[0] SOCLE DONNÉES     (déterministe, sans agent)
     ↓ football-data.co.uk + ClubElo + OpenLigaDB → base locale
[1] MODÈLE            (code pur, aucune probabilité "à la main")
     ↓ forces attaque/défense normalisées par ligue (IPF) → λ, μ → Dixon-Coles
[2] PRIX JUSTE        (dé-margeage power/Shin, JAMAIS proportionnel)
     ↓ cotes marché → probabilités justes
[3] DÉTECTION         edge = p_modèle × cote − 1, seuil ajusté au coût réel
     ↓
[4] CONTRÔLE          vérification adversariale + règles mémoire (hard/soft)
     ↓
[5] VALIDATION        RPS / log-loss / Brier / ECE + CLV vs clôture dé-margée
```

**Le changement de nature :** les agents ne produisent plus de probabilités. Ils
**collectent du contexte factuel** (blessures, enjeu, rotation) et **vérifient**.
Les probabilités viennent du code.

---

## 6. Mode de travail — règles non négociables

### R1 — Aucun paramètre inventé
Pas de λ Poisson « choisi », pas de probabilité posée pour arriver au résultat voulu.
Toute probabilité est calculée par le code à partir de données sourcées.
*(Origine : 7 propositions sur 7 rejetées le 29/07 pour edges fabriqués.)*

### R2 — Dé-margeage power/Shin, jamais proportionnel
La méthode proportionnelle **surestime l'edge de ~35 %** et fabrique de la fausse value
sur les outsiders (cote moyenne du portefeuille 4,15 vs 3,31). Gain mesuré du passage à
power : **+0,9 à +2,4 points de yield**. Coût : 20 lignes.

### R3 — Piloter par la CLV, pas par le P&L
Prouver un edge de +2 % demande **~6 800 paris** par le P&L, mais **~90-350 paris** par
la CLV. Rapport **20× à 80×**. Le P&L sur 5 paris ne dit strictement rien.

### R4 — Un book soft n'est jamais une référence de probabilité
Utiliser Betano (ou une moyenne incluant des books soft) comme « vrai prix » est
structurellement faux. Référence = clôture dé-margée du consensus (`AvgC*`).

### R5 — Évaluer le modèle BRUT séparément
Si le modèle brut est à RPS 0,215 et que la fusion marché le ramène à 0,194,
**nous n'avons pas de modèle, nous avons un lisseur de cotes**. La porte doit exiger que
le **modèle brut** batte un benchmark avant tout.

### R6 — Jamais un match commencé, jamais un match reporté
Veto fixture au niveau du match (une seule alerte suffit à écarter toutes ses sélections).

### R7 — Toute leçon doit être exécutable
Une leçon sans bloc `rule` machine est décorative. Le compteur d'orphelines est affiché
à chaque run.

---

## 7. Métriques et seuils

| Métrique | Rôle | Repère |
|---|---|---|
| **Log-loss** | **Arbitre des décisions** (sélection de modèle, ξ, ρ, γ) | local, le plus efficient en données |
| **RPS** | Comparaison à la littérature | Books clôture : **0,182–0,193** (grands championnats), **0,209–0,219** (divisions inférieures). Un bon gradient boosting : 0,2156 |
| **Brier + ECE** | Calibration (fiabilité / résolution) | segmenté **par marché** |
| **CLV** | **Validation de l'edge** | < +0,5 % = bruit · +1 à +2 % = edge réel mince · > +5 % durable = suspect |

**Taille d'échantillon (CLV, σ = 0,114) :** +1 % → 352 paris · +2 % → 88 paris.

---

## 8. Plan d'implémentation priorisé

| # | Action | Impact | Effort |
|---|---|---|---|
| **1** | **Métriques propres** (RPS, log-loss, Brier, ECE) sur **tous** les matchs prédits, pas seulement les paris pris | ★★★★★ | ★ |
| **2** | **Corriger l'avantage terrain** : `exp(±γ/2)` au lieu de `×1.10` unilatéral | ★★★★★ | ★ |
| **3** | **Dé-margeage power/Shin** en remplacement du proportionnel | ★★★★★ | ★ |
| **4** | **Forces att/déf normalisées par ligue** (IPF, ~150 lignes stdlib, convergence 40 itérations) | ★★★★★ | ★★★ |
| **5** | **CLV réel** via football-data.co.uk (`AvgC*`) | ★★★★★ | ★★ |
| 6 | Dixon-Coles τ (ρ ≈ −0,08 à −0,13) | ★★★ | ★ |
| 7 | Pondération temporelle **en jours** (ξ ≈ 0,0025, demi-vie ~9 mois) | ★★★ | ★★ |
| 8 | γ estimé par ligue (sortie gratuite de l'IPF) | ★★★ | ★ |
| 9 | xG intégré au niveau des coefficients (mélange géométrique w≈0,65) | ★★★ | ★★ |
| ❌ | Poisson bivarié | ~0 | ★★★★ |

### 🐛 Le bug le plus coûteux, déjà quantifié

`model.py:65` applique `×1.10` au domicile **et rien à l'extérieur**, alors que
`base_attack` mélange déjà domicile et extérieur :

```
              référence     notre code      écart
   1            44,38 %       40,52 %      −3,86 pt
   X            27,42 %       25,04 %      −2,39 pt
   2            28,19 %       34,44 %      +6,25 pt   ← +12,5 % de λ extérieur
```

**Nous sur-cotons structurellement toutes les victoires à l'extérieur de ~6 points.**
Cela explique directement les pertes Mirassol (2), Espagne (1X2) et France (1X2).

---

## 9. Ce que nous ciblons / ce que nous nous interdisons

### Cibles
- **Fenêtre début de semaine (J-4 à J-6)** : Betano ouvre tôt et bouge peu ; les
  concurrents convergent ensuite. La brèche est **précoce**, pas près du coup d'envoi.
- **SuperQuoten** (0 % de marge, 1X2 pré-match, ~1/jour) : seul segment à parité.
- **Divisions inférieures nordiques/est-européennes** (Superettan, Ettan, 1. divisjon,
  I Liga, D3 grecque) : couverture rare, retour ~92-95 %.
- **Props joueurs Opta** : les plus durs à pricer.

### Interdits
- ❌ **Ligues exotiques** (Éthiopie, EAU, Asie du Sud-Est) : 91 % → **86 % net de taxe**.
- ❌ **Cotes élevées / petits marchés** : limites de mise documentées **sous 1 €**.
- ❌ **Regionalliga/Oberliga** : ouverture à J-0/J-1, aucune fenêtre.
- ❌ **Stratégies multi-books en direct** : interdites par le § 6h GlüStV.
- ❌ **Handicap asiatique** tant que sa présence sur le produit DE n'est pas confirmée
  (absent des 592 articles d'aide).

---

## 10. Honnêteté du cabinet

Nous ne promettons pas de gains. Les données que nous avons réunies disent l'inverse :
sur Betano.de, avec la taxe répercutée, **la rentabilité est arithmétiquement hors
d'atteinte**. Ce que nous pouvons construire — et mesurer — c'est un moteur de prédiction
**calibré et validé**, dont nous saurons dire, chiffres à l'appui, s'il vaut quelque chose.

C'est un projet d'ingénierie et de méthode. Pas une source de revenus.

*Mode PAPER — 0 € misé. Aide au jeu : joueurs-info-service.fr, 09 74 75 13 13.*
