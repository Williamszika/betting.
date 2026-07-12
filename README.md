# sportsbet — moteur honnête d'analyse de paris sportifs

Football · Tennis · Basket. Découverte des matchs → recherche multi-agents →
modèles de probabilité → détection de **value** → construction de **coupons**
visant une cote cible (ex. 5.0).

> ### ⚠️ À lire avant tout
> Cet outil produit des **estimations statistiques**, **pas des certitudes**.
> **Aucun pari n'est « sûr ».** Un combiné multiplie les risques : il suffit
> qu'**une** jambe tombe pour tout perdre. Ne misez que ce que vous pouvez
> perdre. Le jeu peut créer une dépendance — interdit aux mineurs.
> Aide (France) : **joueurs-info-service.fr — 09 74 75 13 13**.
>
> Ce logiciel n'a **aucun moyen de prédire un résultat**. Son seul apport
> possible est de repérer des cotes que le modèle juge **sous-évaluées**
> (value). Cet avantage n'existe que si le modèle est bien calibré — ce qui
> est le point le plus difficile, et dépend de la qualité des données.

---

## Ce que fait (et ne fait pas) cet outil

| Fait | Ne fait pas |
|---|---|
| Estimer des probabilités par match (Poisson foot, Elo tennis/basket) | Garantir des gains ou des paris « safe » |
| Comparer probabilité estimée vs cote → **value** | Prédire l'avenir |
| Construire des coupons visant une cote (ex. 5) en maximisant la proba conjointe | Remplacer votre jugement |
| Récupérer des infos **sans clé API** (scraping web best-effort) | Scraper des sites qui l'interdisent |

## Architecture

```
src/sportsbet/
  models.py              Match, Selection, Coupon (+ value, proba conjointe)
  probability/
    poisson.py           foot : xG -> 1X2, Over/Under, BTTS
    elo.py               tennis & basket : proba de victoire
  value.py               edge (value), retrait de marge, Kelly borné
  coupon.py              solveur de coupon (cote cible, max proba conjointe)
  responsible.py         règles + avertissement jeu responsable
  scraping/              récupération SANS clé API (web, fixtures, odds)
  agents/
    pool.py              pool concurrent borné (le « 500+ agents » raisonnable)
    research_agent.py    un agent = 1 match analysé -> sélections
  pipeline.py            chaîne complète : matchs -> recherche -> coupons
  cli.py                 `python -m sportsbet.cli daily ...`
workflows/
  daily_coupon.js        workflow deep-research (fan-out recherches web réelles)
```

### Le « pool de 500+ agents », honnêtement

Lancer 500 scrapers **simultanés** sature les sites, se fait bannir et coûte
cher pour rien. La qualité d'une prédiction vient des **données** et des
**modèles**, pas du **nombre de robots**. Le pool (`agents/pool.py`) accepte
donc des centaines de tâches mais borne la concurrence (`max_workers`, défaut
12) pour rester efficace et courtois. Le **workflow deep-research** est la voie
recommandée pour la recherche web à grande échelle.

## Installation

```bash
pip install -r requirements.txt   # httpx, bs4, lxml, PyYAML (scraping) + pytest
```

Le **cœur** (modèles, value, coupon) ne dépend **que de la stdlib** — les
paquets ci-dessus ne servent qu'au scraping web.

## Utilisation rapide (données d'exemple fournies)

```bash
PYTHONPATH=src python -m sportsbet.cli daily \
  --fixtures data/fixtures.example.csv \
  --odds     data/odds.example.csv \
  --ratings  data/ratings.example.csv \
  --target-odds 5 --coupons 5 --min-legs 2 --max-legs 6
```

- `--target-odds 5` : cote totale visée par coupon.
- `--coupons 5` : jusqu'à 5 coupons du jour, sans match partagé.
- `--min-legs 2` : force un vrai **combiné** (>=2 matchs) plutôt qu'un simple.
- `--min-edge 0.05` (option) : ne garde que les sélections de value ≥ 5 %.
- `--signals` (option) : tente de récupérer des signaux web (plus lent).

### Brancher de vraies données (sans clé API)

1. Remplissez `data/fixtures.csv` (matchs du jour), `data/odds.csv` (cotes) et
   `data/ratings.csv` (notes de force). Le **workflow deep-research** peut
   produire ces fichiers en cherchant sur le web.
2. Ou implémentez un adaptateur dans `scraping/fixtures.py` / `scraping/odds.py`
   pour un site que vous avez le **droit** de scraper (respect robots.txt/CGU).

## Le point dur, dit franchement

Le maillon faible n'est pas le code : c'est la **calibration du modèle** et la
**qualité des données gratuites**. Les cotes des bookmakers intègrent
énormément d'information ; les battre durablement est très difficile. Traitez
les sorties comme une **aide à la décision**, jamais comme une vérité. Mesurez
vos résultats dans le temps (log des paris, Brier score) avant de faire
confiance au modèle.

## Tests

```bash
python -m pytest tests/ -q
```

## Licence & responsabilité

Fourni « tel quel », à des fins d'analyse personnelle et éducative. Vérifiez la
légalité des paris et du scraping dans votre juridiction. Les auteurs déclinent
toute responsabilité en cas de pertes.
