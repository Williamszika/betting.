# 🔍 Audit du fonctionnement — de la découverte à la création du coupon

_Audit honnête du système SportPredix tel qu'il tourne réellement (observé sur les runs des 12–13/07/2026). Statuts : 🟢 fiable · 🟠 fonctionne mais fragile · 🔴 point dur._

---

## 1. Verdict en une phrase

La **chaîne d'analyse fonctionne de bout en bout et sa force est la VÉRIFICATION** (elle refuse les matchs finis, les cotes non confirmées, les raisonnements faux). Ses **deux points durs** sont **externes au code** : (a) la **limite d'usage du compte** qui étrangle les runs profonds, et (b) l'**accès aux cotes réelles** (Betano illisible → consensus/Flashscore, à confirmer).

---

## 2. Le flux complet (7 phases + données/modèle)

```
[Betano.de : matchs de demain]
        │  (Découverte)
        ▼
  Fixtures (foot/tennis/basket, équilibrés par sport)
        │  (Recherche — 7 spécialistes / match)
        ▼
  Faits bruts (forme, effectif, xG/stats, H2H, tactique, contexte, cotes)
        │  (Consolidation — desk éditeur = échange inter-agents)
        ▼
  Fiche de faits VÉRIFIÉS / match  ──►  data/lessons.md (leçons passées) réinjectées
        │  (Marchés — tous les marchés → value ; cotes Betano→Flashscore/comparateur)
        ▼
  Opportunités de value (proba modèle vs cote)
        │  (Vérification — adversariale : match à venir ? cote réelle ? raisonnement ?)
        ▼
  Opportunités CONFIRMÉES
        │  (Table ronde — coordinateur : classe, dé-corrèle)
        ▼
  [Coupon 1,95–3] + [singles 5–7]  ──►  Registre (ledger) → suivi 🟢/🔴 → règlement → rétro
```

En parallèle, le **moteur** `src/sportsbet` (features pondérées → Poisson/logistique → blend → value) fournit une **probabilité modèle** à croiser avec la recherche.

---

## 3. Étape par étape

### Phase 1 — Découverte 🟢
- **Entrée** : date de demain + « matchs sur Betano.de ».
- **Fait** : 3 agents (1/sport) cherchent les vraies affiches ; entrelacement pour équilibrer foot/tennis/basket.
- **Observé (13/07)** : a trouvé de vrais matchs (Allsvenskan, Islande, ATP Gstaad, NBA Summer League). ✅
- **Faiblesse** : dépend de ce que les moteurs indexent ; le catalogue Betano.de exact n'est pas lu (on suppose qu'il propose ces ligues).

### Phase 2 — Recherche (7 spécialistes/match) 🟢
- **Fait** : forme+stats, effectif/compos, xG/avancé, H2H, tactique/enjeu, contexte/météo, cotes — données concrètes + source + confiance.
- **Observé** : recherche riche et sourcée (ex. « Bodø privé de 3 internationaux », « Sonego transition gazon→terre »). ✅
- **Coût** : c'est la phase la **plus lourde** (7 × N matchs) → principal consommateur de budget.

### Phase 3 — Consolidation / desk 🟢
- **Fait** : un éditeur réconcilie les 7 spécialistes, résout les contradictions, isole blessures, dégage les angles → **fiche de faits partagée** (c'est là que les agents « communiquent »).
- **Observé** : 9/9 fiches produites même quand les phases suivantes ont manqué de budget. ✅

### Phase 4 — Marchés 🟠
- **Fait** : lit la fiche partagée, passe en revue TOUS les marchés, prend la cote (Betano.de sinon Flashscore/comparateur), calcule la **value**.
- **Observé** : 24 opportunités générées (13/07). Mais 1re tentative « Betano only » → **0 opportunité** (cotes Betano introuvables). Corrigé en autorisant Flashscore/consensus. 🟠
- **Point dur** : la **cote réelle** est le maillon faible (voir §4).

### Phase 5 — Vérification adversariale 🟢 (le point fort)
- **Fait** : pour chaque opportunité, un sceptique vérifie sur le web : match encore à venir ? cote plausible ? raisonnement solide ? → keep/drop.
- **Observé (12/07)** : a **écarté des matchs déjà finis** (KFUM 0-2) et des **raisonnements faux** (« Brann 1 but/match » alors que 2,0/match). (13/07) : **24 → 4 retenues** seulement. ✅✅
- **C'est ce qui empêche le système de mentir.**

### Phase 6 — Table ronde 🟢
- **Fait** : un coordinateur voit toutes les opportunités confirmées, les classe, signale les corrélations (2 jambes du même match).

### Phase 7 — Synthèse / coupon 🟠
- **Fait** : solveur qui maximise la proba conjointe dans la fourchette de cote, matchs distincts.
- **Observé** : parfois **aucun coupon ne rentre dans 1,95–3** (jambes toutes ~1,9 → simple <1,95 ou double ~3,6). Le système le dit honnêtement au lieu de forcer. 🟠 (limite de construction, pas un bug).

### Transverse — Modèle & Suivi 🟢
- **Modèle** : features normalisées/pondérées → Poisson/logistique → blend → value (30 tests OK). Aujourd'hui il tourne **à côté** de la recherche ; le croisement systématique (brancher les chiffres scrapés dans le modèle) reste à automatiser. 🟠
- **Suivi** : registre 🟢/🔴, ROI, règlement par agents, rétro sur perte → `lessons.md`. Cadre en place, **pas encore de données réelles** (aucun coupon encore réglé).

---

## 4. Ce qui bloque vraiment (constaté, honnête)

| # | Problème | Impact | Statut |
|---|---|---|---|
| 1 | **Limite d'usage du compte** (~2,5 M tokens/run profond) | Les runs profonds n'atteignent pas toujours la phase Coupon ; besoin de reprises après reset | 🔴 externe |
| 2 | **Cotes live Betano.de illisibles** (JS/geo) | On passe par Flashscore/consensus → **à confirmer sur Betano** | 🔴 externe |
| 3 | **Fraîcheur / timing** | Un « coupon du jour » lancé trop tard = matchs déjà commencés (d'où le passage à J+1) | 🟠 géré (job 20h pour demain) |
| 4 | **Fourchette 1,95–3 parfois vide** | Selon les cotes du jour, aucune combi ne rentre | 🟠 par nature |
| 5 | **Modèle pas encore branché sur la recherche** | La proba vient surtout de l'estimation des agents, pas du modèle Poisson | 🟠 à faire |

---

## 5. Points forts 🟢
- **Honnêteté structurelle** : la vérification écarte finis/faux/non confirmés ; le système dit « rien à parier » plutôt que d'inventer.
- **Couverture** : 3 sports équilibrés, grille de données complète (toute ta checklist), tous les marchés.
- **Communication inter-agents réelle** (desk + table ronde).
- **Traçabilité** : sources citées, rapports commités, suivi 🟢/🔴 + rétro d'apprentissage.
- **Reprise cumulative** : rien n'est perdu quand la limite tombe.

## 6. Points faibles 🔴🟠
- Dépend d'un **budget** que les runs profonds épurent vite.
- **Cotes** non officielles (consensus) → écart possible avec Betano.
- **Calibration du modèle** non prouvée (aucun historique réglé encore) — c'est le suivi 🟢/🔴 qui la validera dans le temps.
- « Value » sur petites ligues / Summer League = **haute variance** (les paris retenus le 13/07 étaient surtout des UNDER Summer League, à confiance moyenne).

---

## 7. Recommandations concrètes (par ordre d'impact)
1. **Alléger les runs** (moins de matchs OU moins de spécialistes par run) pour finir dans une fenêtre de budget → coupon livré chaque soir sans reprise. 
2. **Brancher le modèle Poisson sur les chiffres scrapés** (xG, forme…) et faire `blend()` systématiquement → proba plus robuste que l'estimation libre des agents.
3. **Laisser tourner le suivi** quelques semaines : c'est la seule façon de savoir si le système a une vraie value (ROI réel), et la rétro améliorera les leçons.
4. Éventuellement un **compte à quota plus élevé** si tu veux la couverture « tous les matchs » sans throttling.

> ⚠️ Rappel : tout ceci reste de l'aide à la décision. Aucun pari n'est sûr ; le seul juge de paix est le suivi 🟢/🔴 dans le temps.
