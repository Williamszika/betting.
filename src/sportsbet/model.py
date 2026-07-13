"""Modèle SportPredix : features pondérées → probabilités, croisées avec la recherche.

Deux voies, selon le sport :
- **Football** : on estime les buts attendus (xG ajustés) de chaque équipe à
  partir des features, puis on passe par Poisson pour 1X2 / Over-Under / BTTS.
- **Tennis / Basket** (2 issues) : on convertit l'écart de score pondéré en
  probabilité de victoire via une logistique.

Enfin, `blend_probabilities` **croise** la proba du modèle avec celle issue de
la recherche (avis d'experts, marché) — c'est le « comparer / vérifier » du
projet.
"""
from __future__ import annotations

import math
from typing import Dict

from .features import (
    DEFAULT_WEIGHTS,
    TeamStats,
    defensive_weakness,
    form_index,
    offensive_strength,
    team_score,
)
from .probability import elo as elo_mod, poisson


def elo_1x2(home_elo: float, away_elo: float, home_adv: float = 65.0) -> Dict[str, float]:
    """1X2 dérivé des notes ELO (avec un modèle de nul).

    ELO donne P(domicile | hors nul) ; on répartit ensuite une probabilité de nul
    qui augmente quand les deux équipes sont proches (matchs serrés = plus de nuls).
    """
    p_home_excl = elo_mod.expected_score(home_elo + home_adv, away_elo)
    diff = abs((home_elo + home_adv) - away_elo)
    draw = 0.30 * math.exp(-diff / 300.0)      # ~0.30 si égal, décroît avec l'écart
    return {"1": p_home_excl * (1.0 - draw), "X": draw, "2": (1.0 - p_home_excl) * (1.0 - draw)}


def expected_goals(home: TeamStats, away: TeamStats,
                   league_avg: float = 1.35) -> tuple[float, float]:
    """Buts attendus (home_xg, away_xg) à partir des stats, ajustés par forme,
    disponibilité et avantage du terrain.

    La base est la moyenne (buts marqués + xG)/2 de chaque équipe, modulée par
    la faiblesse défensive adverse (relative à la moyenne de la ligue) et par
    des facteurs forme/effectif/domicile.
    """
    def base_attack(s: TeamStats) -> float:
        return max(0.2, (s.goals_for + s.xg) / 2.0)

    def opp_def_factor(opp: TeamStats) -> float:
        # >1 si l'adversaire encaisse plus que la moyenne, <1 sinon.
        conceded = (opp.goals_against + opp.xga) / 2.0
        return max(0.5, min(1.6, conceded / league_avg))

    def form_factor(s: TeamStats) -> float:
        return 0.85 + 0.30 * form_index(s)          # 0.85 – 1.15

    def avail_factor(s: TeamStats) -> float:
        return 0.80 + 0.20 * max(0.0, min(1.0, s.availability))  # 0.80 – 1.00

    home_xg = (base_attack(home) * opp_def_factor(away)
               * form_factor(home) * avail_factor(home) * 1.10)  # bonus domicile
    away_xg = (base_attack(away) * opp_def_factor(home)
               * form_factor(away) * avail_factor(away))
    return max(0.2, home_xg), max(0.2, away_xg)


def predict_football(home: TeamStats, away: TeamStats,
                     league_avg: float = 1.35, weight_elo: float = 0.35) -> Dict[str, float]:
    """Probabilités football : xG (glissant) → Poisson, 1X2 CROISÉ avec l'ELO.

    Over/Under et BTTS restent Poisson. Le 1X2 est un mélange Poisson × ELO
    (poids `weight_elo`) quand les deux ELO sont connus (≠ 1500 par défaut).
    """
    hx, ax = expected_goals(home, away, league_avg)
    probs = poisson.market_probs(hx, ax)
    has_elo = (home.elo and away.elo and (home.elo != 1500.0 or away.elo != 1500.0))
    if has_elo:
        e = elo_1x2(home.elo, away.elo)
        for k in ("1", "X", "2"):
            probs[k] = (1.0 - weight_elo) * probs[k] + weight_elo * e[k]
        tot = probs["1"] + probs["X"] + probs["2"]
        if tot > 0:
            for k in ("1", "X", "2"):
                probs[k] /= tot
    return probs


def predict_two_way(home: TeamStats, away: TeamStats,
                    weights: dict | None = None, scale: float = 6.0) -> Dict[str, float]:
    """Probabilité de victoire à 2 issues (tennis/basket) via logistique sur
    l'écart des scores pondérés des deux camps."""
    w = weights or DEFAULT_WEIGHTS
    diff = team_score(home, away, w) - team_score(away, home, w)
    p_home = 1.0 / (1.0 + math.exp(-scale * diff))
    return {"home": p_home, "away": 1.0 - p_home}


def blend_probabilities(model_prob: float, research_prob: float,
                        weight_model: float = 0.5) -> float:
    """Croise la proba du MODÈLE avec la proba issue de la RECHERCHE.

    weight_model dans [0,1] : 0.5 = moyenne équilibrée. C'est l'étape où l'on
    « compare et vérifie » les deux sources avant de décider.
    """
    w = max(0.0, min(1.0, weight_model))
    return w * model_prob + (1.0 - w) * research_prob


def value_vs_odds(prob: float, decimal_odds: float) -> float:
    """Value (edge) de la proba finale face à la cote : p * cote - 1."""
    return prob * decimal_odds - 1.0


def market_probabilities(sport: str, home: TeamStats, away: TeamStats,
                         league_avg: float = 1.35) -> Dict[str, float]:
    """Dispatcher : renvoie les probabilités des marchés du modèle selon le sport.

    - football : 1 / X / 2, Over/Under 2.5, BTTS (via Poisson).
    - tennis / basket : home / away (via logistique).
    """
    if sport == "football":
        return predict_football(home, away, league_avg)
    return predict_two_way(home, away)


def blend_market_probs(model_map: Dict[str, float], research_map: Dict[str, float],
                       weight_model: float = 0.5) -> Dict[str, float]:
    """Croise deux jeux de probabilités marché par marché.

    Pour chaque clé présente des deux côtés, on blend ; sinon on garde la valeur
    disponible. C'est le « comparer/vérifier modèle vs recherche » au niveau des
    marchés.
    """
    out: Dict[str, float] = {}
    for k in set(model_map) | set(research_map):
        if k in model_map and k in research_map:
            out[k] = blend_probabilities(model_map[k], research_map[k], weight_model)
        else:
            out[k] = model_map.get(k, research_map.get(k, 0.0))
    return out
