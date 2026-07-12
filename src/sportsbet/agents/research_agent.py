"""Agent de recherche : transforme un match + cotes en sélections évaluées.

Chaque agent :
  1. (optionnel) récupère des SIGNAUX sur le web — forme récente, blessures,
     avis d'experts — via recherche (best-effort, sans clé API) ;
  2. estime les probabilités du match avec le modèle adapté au sport ;
  3. produit des `Selection` (paris possibles) là où on a des cotes.

Sans données réelles branchées, l'agent utilise des notes de force par défaut :
les probabilités sont alors NEUTRES et peu informatives. C'est volontaire —
mieux vaut un modèle honnêtement incertain qu'un faux air de certitude.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..models import Match, Selection, Sport
from ..probability import elo, poisson
from ..scraping.odds import OddsBoard


@dataclass
class TeamRatings:
    """Notes de force (Elo) par équipe/joueur. Alimentez-les avec des données
    scrapées (classements, Elo publics par surface au tennis, etc.)."""
    ratings: Dict[str, float] = field(default_factory=dict)
    default: float = 1500.0

    def get(self, name: str) -> float:
        return self.ratings.get(name, self.default)

    @classmethod
    def from_file(cls, path) -> "TeamRatings":
        """Charge des notes depuis un CSV (colonnes: name,rating) ou YAML (name: rating)."""
        import csv
        from pathlib import Path
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        ratings: Dict[str, float] = {}
        if p.suffix.lower() in (".yaml", ".yml"):
            import yaml
            ratings = {str(k): float(v) for k, v in (yaml.safe_load(text) or {}).items()}
        else:
            for row in csv.DictReader(text.splitlines()):
                ratings[str(row["name"])] = float(row["rating"])
        return cls(ratings=ratings)


@dataclass
class ResearchAgent:
    ratings: TeamRatings = field(default_factory=TeamRatings)
    gather_signals: bool = False  # mettre True pour tenter des recherches web

    def _signals(self, match: Match) -> str:
        """Récupère (best-effort) quelques signaux textuels sur le match."""
        if not self.gather_signals:
            return ""
        try:
            from ..scraping import web
            q = f"{match.home} vs {match.away} {match.league} preview forme blessures pronostic"
            hits = web.search(q, max_results=5)
            return " | ".join(f"{h.title}: {h.snippet}" for h in hits)[:1000]
        except Exception:
            return ""

    def research(self, match: Match, odds: Optional[OddsBoard] = None) -> List[Selection]:
        notes = self._signals(match)
        probs = self._model_probs(match)
        selections: List[Selection] = []
        if odds is None:
            return selections
        for pick, dec in odds.prices.items():
            if pick not in probs:
                continue
            try:
                selections.append(
                    Selection(
                        match=match,
                        market=odds.market,
                        pick=pick,
                        decimal_odds=float(dec),
                        model_prob=probs[pick],
                        source_notes=notes,
                    )
                )
            except ValueError:
                continue  # cote/proba invalide
        return selections

    def _model_probs(self, match: Match) -> Dict[str, float]:
        rh = self.ratings.get(match.home)
        ra = self.ratings.get(match.away)
        if match.sport == Sport.FOOTBALL:
            hx, ax = poisson.xg_from_ratings(rh, ra)
            return poisson.market_probs(hx, ax)
        if match.sport == Sport.TENNIS:
            p = elo.win_probs(rh, ra, home_advantage=0.0)
            return {"home": p["home"], "away": p["away"], "1": p["home"], "2": p["away"]}
        if match.sport == Sport.BASKETBALL:
            p = elo.win_probs(rh, ra, home_advantage=100.0)
            return {"home": p["home"], "away": p["away"], "1": p["home"], "2": p["away"]}
        return {}
