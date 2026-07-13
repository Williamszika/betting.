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
from .probability import poisson


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
                     league_avg: float = 1.35) -> Dict[str, float]:
    """Probabilités des marchés football via le modèle (features → xG → Poisson)."""
    hx, ax = expected_goals(home, away, league_avg)
    return poisson.market_probs(hx, ax)


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
