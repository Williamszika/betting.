"""Structures de données du domaine.

Tout est en cotes décimales (ex. 2.50) et probabilités dans [0, 1].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import prod
from typing import Optional


class Sport(str, Enum):
    FOOTBALL = "football"
    TENNIS = "tennis"
    BASKETBALL = "basketball"


@dataclass(frozen=True)
class Match:
    sport: Sport
    league: str
    home: str          # équipe/joueur à domicile (ou joueur A au tennis)
    away: str          # équipe/joueur à l'extérieur (ou joueur B au tennis)
    start_time: Optional[datetime] = None
    match_id: Optional[str] = None

    def label(self) -> str:
        return f"{self.home} vs {self.away} [{self.league}]"


@dataclass
class Selection:
    """Un pari possible sur un match, avec la probabilité estimée par le modèle."""
    match: Match
    market: str            # ex. "1X2", "Over/Under 2.5", "Moneyline"
    pick: str              # ex. "1", "X", "2", "Over 2.5", "home"
    decimal_odds: float    # cote décimale du bookmaker (récupérée sur le web)
    model_prob: float      # probabilité estimée par le modèle, dans [0, 1]
    source_notes: str = "" # d'où viennent les infos (traçabilité)

    def __post_init__(self) -> None:
        if not 0.0 <= self.model_prob <= 1.0:
            raise ValueError(f"model_prob doit être dans [0,1], reçu {self.model_prob}")
        if self.decimal_odds <= 1.0:
            raise ValueError(f"decimal_odds doit être > 1.0, reçu {self.decimal_odds}")

    @property
    def implied_prob(self) -> float:
        """Probabilité implicite de la cote (marge du bookmaker incluse)."""
        return 1.0 / self.decimal_odds

    @property
    def edge(self) -> float:
        """Value (espérance par mise unitaire) : model_prob * cote - 1.

        > 0  → le modèle estime le pari « à valeur » (value bet).
        < 0  → cote défavorable selon le modèle.
        """
        return self.model_prob * self.decimal_odds - 1.0

    def summary(self) -> str:
        return (
            f"{self.match.label()} | {self.market}: {self.pick} @ {self.decimal_odds:.2f} "
            f"| p_modele={self.model_prob:.0%} p_implicite={self.implied_prob:.0%} "
            f"| value={self.edge:+.1%}"
        )


@dataclass
class Coupon:
    """Un coupon combiné (accumulateur) de plusieurs sélections indépendantes."""
    selections: list[Selection] = field(default_factory=list)

    @property
    def total_odds(self) -> float:
        return prod(s.decimal_odds for s in self.selections) if self.selections else 0.0

    @property
    def joint_prob(self) -> float:
        """Probabilité conjointe SOUS HYPOTHÈSE D'INDÉPENDANCE des sélections.

        Attention : c'est une approximation. Deux paris corrélés (même match,
        mêmes conditions) violent cette hypothèse et gonflent l'estimation.
        """
        return prod(s.model_prob for s in self.selections) if self.selections else 0.0

    @property
    def expected_value(self) -> float:
        """Espérance du coupon par mise unitaire : p_conjointe * cote_totale - 1."""
        if not self.selections:
            return 0.0
        return self.joint_prob * self.total_odds - 1.0

    def render(self) -> str:
        lines = [f"COUPON — {len(self.selections)} sélection(s)"]
        for i, s in enumerate(self.selections, 1):
            lines.append(f"  {i}. {s.summary()}")
        lines.append(
            f"  → Cote totale : {self.total_odds:.2f} | "
            f"Proba conjointe estimée : {self.joint_prob:.1%} | "
            f"Value : {self.expected_value:+.1%}"
        )
        return "\n".join(lines)
