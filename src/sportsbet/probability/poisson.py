"""Modèle de Poisson pour le football.

On modélise le nombre de buts de chaque équipe par une loi de Poisson dont la
moyenne est le « expected goals » (xG) de l'équipe. À partir de la matrice des
scores, on dérive les marchés 1X2, Over/Under et BTTS.

Références : Maher (1982), Dixon & Coles (1997). Ici on garde la version simple
(indépendance des deux Poisson) — suffisante comme base, à raffiner avec de
vraies données (xG scrapés, ajustement Dixon-Coles pour les faibles scores).
"""
from __future__ import annotations

import math
from typing import Dict, List


def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) pour X ~ Poisson(lam)."""
    if lam < 0:
        raise ValueError("lambda doit être >= 0")
    return math.exp(-lam) * lam**k / math.factorial(k)


def score_matrix(home_xg: float, away_xg: float, max_goals: int = 15) -> List[List[float]]:
    """Matrice (max_goals+1)x(max_goals+1) des probabilités de chaque score exact."""
    home = [poisson_pmf(i, home_xg) for i in range(max_goals + 1)]
    away = [poisson_pmf(j, away_xg) for j in range(max_goals + 1)]
    return [[home[i] * away[j] for j in range(max_goals + 1)] for i in range(max_goals + 1)]


def market_probs(home_xg: float, away_xg: float, max_goals: int = 15,
                 ou_line: float = 2.5) -> Dict[str, float]:
    """Probabilités des principaux marchés football à partir des xG.

    Retourne 1 / X / 2, Over/Under (ligne paramétrable) et BTTS Oui/Non.
    """
    m = score_matrix(home_xg, away_xg, max_goals)
    p_home = p_draw = p_away = 0.0
    p_over = p_btts = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = m[i][j]
            if i > j:
                p_home += p
            elif i == j:
                p_draw += p
            else:
                p_away += p
            if i + j > ou_line:
                p_over += p
            if i > 0 and j > 0:
                p_btts += p

    line = f"{ou_line:g}"
    return {
        "1": p_home,
        "X": p_draw,
        "2": p_away,
        f"Over {line}": p_over,
        f"Under {line}": 1.0 - p_over,
        "BTTS Yes": p_btts,
        "BTTS No": 1.0 - p_btts,
    }


def xg_from_ratings(home_rating: float, away_rating: float,
                    league_avg_goals: float = 2.6,
                    home_advantage: float = 60.0) -> tuple[float, float]:
    """Estime (home_xg, away_xg) à partir de notes de force type Elo.

    Heuristique de base : la différence de notes (avec avantage du terrain)
    décale la répartition des buts autour de la moyenne de la ligue. C'est une
    approximation grossière — à remplacer par des xG réels dès que possible.
    """
    diff = (home_rating + home_advantage) - away_rating
    # Facteur multiplicatif borné : +/- ~40% de buts selon l'écart de niveau.
    strength = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))  # dans (0,1), 0.5 si égal
    tilt = 0.8 * (strength - 0.5)                      # dans (-0.4, 0.4)
    half = league_avg_goals / 2.0
    home_xg = max(0.2, half * (1.0 + tilt) + 0.15)     # léger bonus domicile
    away_xg = max(0.2, half * (1.0 - tilt) - 0.05)
    return home_xg, away_xg
