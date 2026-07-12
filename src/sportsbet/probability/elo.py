"""Modèle Elo pour les sports sans match nul (tennis, basket).

Elo transforme une différence de notes en probabilité de victoire. Pour le
basket on peut ajouter un avantage du terrain ; pour le tennis on peut partir
de notes par surface (dur / terre / gazon) si on les a scrapées.
"""
from __future__ import annotations

from typing import Dict


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probabilité que A batte B selon Elo (0..1)."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def win_probs(rating_home: float, rating_away: float,
              home_advantage: float = 0.0) -> Dict[str, float]:
    """Probabilités de victoire à deux issues (pas de nul).

    Pour le tennis, mettre home_advantage=0 et utiliser les notes des joueurs.
    Pour le basket (NBA ~ +100 Elo à domicile) passer home_advantage>0.
    """
    p_home = expected_score(rating_home + home_advantage, rating_away)
    return {"home": p_home, "away": 1.0 - p_home}


def update_rating(rating: float, actual: float, expected: float, k: float = 20.0) -> float:
    """Mise à jour Elo après un match. actual = 1 (gagné) / 0 (perdu)."""
    return rating + k * (actual - expected)
