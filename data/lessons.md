# Leçons apprises (amélioration continue)

> Rempli après chaque PERTE par la rétro des agents. Le workflow d'analyse
> quotidien lit ce fichier et intègre ces leçons AVANT de bâtir le coupon.

## 2026-07-13 — Échec tennis Feldbausch @3.40 (perdu 6-1, 6-3 vs Kecmanovic)
- ➕ **TENNIS — garde-fou écart de classement** : si l'écart au classement > ~150 places, **plafonner la proba de l'outsider** et se ranger sur le marché. Une forme en Challenger ≠ niveau ATP.
- ➕ **Pondérer la QUALITÉ des adversaires** dans la forme (des victoires contre des joueurs faibles ne se transposent pas vers le haut).
- ➕ **Vérifier la narrative « rouille/méforme »** avec les VRAIS derniers résultats avant de l'utiliser (ici « Kecmanovic rouillé » était faux : il avait poussé Sinner à 5 sets à Wimbledon).
- ➕ **Divergence modèle vs marché** : quand ils s'écartent de > 20 points sur un favori net, **shrink vers le marché** (le modèle sortait 0,88, la réalité ~0,75+ pour Kecmanovic).
- ➕ **Domicile/wildcard** au tennis : poids **faible** face à un grand écart de niveau.

## Rappel transverse
Le foot (Ningbo @1.68) a gagné : le lean « forme écrasante + adversaire qui ne marque plus » était juste. L'erreur venait **uniquement** de la sur-confiance sur l'outsider tennis.

## 2026-07-16 — Règlement 14/07 & 15/07 : 2 coupons perdus (bilan 0/3)
**Coupon 14/07 perdu sur les CORNERS** (KuPS Over 2.5 ✅ mais Espagne Over 4.5 corners ❌ : Espagne gagne 2-0 en dominant la possession... mais la France menait les corners 3-1 à la MT).
- ➕ **CORNERS ≠ POSSESSION** : ne PAS déduire les corners de la possession. Utiliser le **taux de corners réel** de l'équipe + l'**état du match** (l'équipe qui mène prend MOINS de corners ; celle qui court après en prend plus).

**Coupon 15/07 perdu sur un TIE DÉJÀ DÉCIDÉ** (Angleterre-Argentine BTTS ✅ mais Craiova-Vitebsk Over 1.5 ❌ : Craiova gagne 1-0, tie plié 4-1 → match fermé). Le pari « le plus sûr » (~82 %) est tombé.
- ➕ **TIE DÉJÀ DÉCIDÉ** (gros écart agrégé, remontée quasi impossible) : **discount la thèse Over/match ouvert**. Les 2es manches pliées sont souvent **fermées et basses** → prudence/éviter les marchés de buts dans les ties décidés (même famille que la leçon « game management »).

**Constat transverse (0/3) :** le modèle **surestime les buts/corners** quand l'ÉTAT DE MATCH les supprime (équipe qui mène, tie décidé). Priorité : intégrer l'état de match / l'enjeu réel dans les marchés de buts et corners.

_(les prochaines leçons s'ajoutent ici automatiquement)_
