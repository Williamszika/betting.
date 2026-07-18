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

## 2026-07-17 — Match REPORTÉ gardé par erreur (Wings-Liberty) → veto fixture
Le seul pari de value du 17/07 (WNBA Dallas Wings-New York Liberty, Under 177.5 @1,91, edge +10,5 %) portait sur un match **REPORTÉ à lundi** (panne de l'avion charter du Liberty). Le vérificateur de CETTE sélection avait raté le report (`fixture_confirmed=true`, conf 0,78), alors que 2 autres vérificateurs du MÊME match l'avaient vu (`fixture_confirmed=false`, conf 0,96/0,97). La synthèse l'a quand même gardé.
- ➕ **VETO FIXTURE au niveau du match** (implémenté dans `deep_research_coupon.js`) : si UN SEUL vérificateur signale `fixture_confirmed=false` (report/annulation/déplacement) sur un match, **écarter TOUTES les sélections de ce match**. La vérification se fait par sélection, mais un report est un fait de match : il doit se propager à toutes les sélections.
- ➕ **Prompt de vérif** : demander explicitement de marquer REPORTÉ/ANNULÉ/déplacé comme `fixture_confirmed=false`.
- ➕ **Décalage de fuseau** : un match US du jeudi soir (ET/CT) tombe la nuit en Europe → remonte comme « lendemain » côté Betano.de. Toujours vérifier le statut réel du match, pas seulement son existence.

## 2026-07-17 — STRATÉGIE validée : SIMPLES par défaut (cap combinés)
Décision validée par l'utilisateur après le bilan 0/3 (les combinés tombaient toujours sur UNE jambe faible ; 3 jambes/6 gagnées individuellement).
- ✅ **Par défaut : présenter la MEILLEURE value du jour en pari SIMPLE** (la sélection vérifiée à plus haut edge/confiance), PAS de combiné forcé.
- ✅ **Ne PAS construire de combiné** sauf demande explicite de l'utilisateur. Combiner ajoute du risque non maîtrisé quand une seule jambe faible fait tout tomber.
- ✅ Rien n'est forcé : s'il n'y a aucune value nette (ou match reporté), **carton blanc** — mieux vaut ne pas parier.

## 2026-07-18 — EXIGENCE : le pari doit être JOUABLE sur Betano.de
Le run a proposé une WNBA (GSV −8.5, handicap US) introuvable sur Betano.de. Cause : betano.de bloque le scraping (403, même en vrai navigateur headless) → le workflow ne partait PAS de l'offre réelle de Betano, mais de matchs/cotes de comparateurs US.
- ➕ **CATALOGUE BETANO.de** (implémenté dans `deep_research_coupon.js`) : découverte + marchés + vérif cadrés sur ce que Betano.de propose vraiment. `BETANO_EXCLUDE` retire WNBA, Summer League, G League, NCAA, ligues mineures US, 3x3/beach. `BETANO_MARKETS` limite les marchés au menu Betano (foot : 1X2/DC/O-U/BTTS/handicap/corners ; tennis : vainqueur/set1/score sets/jeux ; basket : vainqueur/handicap pts/total pts/QT — PAS de props exotiques).
- ➕ **Contrôle final Betano** : le vérificateur doit confirmer via un comparateur affichant les cotes Betano.de (Oddspedia) que le match ET le marché sont jouables sur Betano ; sinon `drop`.
- ➕ **Conséquence assumée** : moins de paris (souvent 0-1/jour), mais 100 % jouables chez le parieur. Mieux vaut un carton blanc qu'un pari introuvable.

_(les prochaines leçons s'ajoutent ici automatiquement)_
