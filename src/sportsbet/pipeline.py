"""Orchestration : matchs → recherche (pool d'agents) → sélections → coupons.

C'est la « chaîne de montage ». Elle relie découverte des matchs, récupération
des cotes, recherche concurrente et construction de coupon.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .agents.pool import run_pool
from .agents.research_agent import ResearchAgent, TeamRatings
from .coupon import build_coupon, build_multiple_coupons
from .models import Coupon, Match, Selection
from .responsible import format_with_disclaimer
from .scraping.odds import OddsBoard


@dataclass
class PipelineConfig:
    target_odds: float = 5.0
    max_total_odds: Optional[float] = 7.0   # plafond (fourchette cote ~5-7)
    n_coupons: int = 5
    max_legs: int = 6
    min_legs: int = 1                  # 1 => paris simples ; >=2 => combiné
    min_edge: Optional[float] = None   # None = mode « plus sûr » (max proba)
    max_workers: int = 12
    gather_signals: bool = False


@dataclass
class DailyReport:
    selections: List[Selection] = field(default_factory=list)
    coupons: List[Coupon] = field(default_factory=list)

    def render(self) -> str:
        parts = [f"{len(self.selections)} sélection(s) analysée(s).", ""]
        if not self.coupons:
            parts.append("Aucun coupon n'a atteint la cote cible avec les "
                         "données fournies.")
        for i, c in enumerate(self.coupons, 1):
            parts.append(f"=== COUPON {i} ===")
            parts.append(c.render())
            parts.append("")
        return format_with_disclaimer("\n".join(parts))


def run_daily(
    matches: List[Match],
    odds_by_match: Dict[str, OddsBoard],
    ratings: Optional[TeamRatings] = None,
    config: Optional[PipelineConfig] = None,
) -> DailyReport:
    """Exécute la chaîne complète et renvoie le rapport du jour."""
    cfg = config or PipelineConfig()
    agent = ResearchAgent(ratings=ratings or TeamRatings(),
                          gather_signals=cfg.gather_signals)

    def worker(m: Match) -> List[Selection]:
        board = odds_by_match.get(m.match_id or m.label())
        return agent.research(m, board)

    nested = run_pool(matches, worker, max_workers=cfg.max_workers)
    selections: List[Selection] = [s for group in nested for s in group]

    coupons = build_multiple_coupons(
        selections,
        n=cfg.n_coupons,
        target_odds=cfg.target_odds,
        max_total_odds=cfg.max_total_odds,
        max_legs=cfg.max_legs,
        min_legs=cfg.min_legs,
        min_edge=cfg.min_edge,
    )
    return DailyReport(selections=selections, coupons=coupons)
