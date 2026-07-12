"""Calcul de value et dimensionnement de mise (Kelly).

La value est le seul « avantage » réel possible en paris : miser uniquement
quand la probabilité estimée dépasse la probabilité implicite de la cote.
Cela ne garantit RIEN sur un pari donné — seulement une espérance positive
SI le modèle est bien calibré (ce qui est le point dur).
"""
from __future__ import annotations


def edge(model_prob: float, decimal_odds: float) -> float:
    """Value par mise unitaire : p * cote - 1."""
    return model_prob * decimal_odds - 1.0


def is_value(model_prob: float, decimal_odds: float, min_edge: float = 0.0) -> bool:
    return edge(model_prob, decimal_odds) >= min_edge


def implied_prob(decimal_odds: float) -> float:
    return 1.0 / decimal_odds


def remove_margin_two_way(odds_a: float, odds_b: float) -> tuple[float, float]:
    """Retire la marge du bookmaker sur un marché à 2 issues (normalisation)."""
    ia, ib = 1.0 / odds_a, 1.0 / odds_b
    total = ia + ib
    return ia / total, ib / total


def kelly_fraction(model_prob: float, decimal_odds: float, cap: float = 0.25) -> float:
    """Fraction de Kelly (bornée). 0 si pas de value.

    Kelly complet est volatil : on plafonne (cap, défaut 25% du Kelly « brut »
    via bornage) et on recommande en pratique un demi- ou quart-Kelly.
    """
    b = decimal_odds - 1.0
    q = 1.0 - model_prob
    f = (b * model_prob - q) / b
    return max(0.0, min(f, cap))
