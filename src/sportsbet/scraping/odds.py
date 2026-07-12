"""Récupération de cotes — sans clé API.

Comme pour les matchs, la voie fiable est le workflow de recherche (l'agent lit
les comparateurs de cotes publics). Ici on fournit :
  - `OddsBoard` : structure simple cote-par-issue.
  - `odds_from_file` : chargement local (YAML/CSV) des cotes récupérées.
  - `median_odds` : agrège plusieurs bookmakers en prenant la médiane (robuste).
"""
from __future__ import annotations

import csv
from pathlib import Path
from statistics import median
from typing import Dict, List


class OddsBoard:
    """Cotes décimales par issue pour un match/marché donné."""

    def __init__(self, market: str, prices: Dict[str, float], bookmaker: str = ""):
        self.market = market
        self.prices = prices  # ex. {"1": 2.10, "X": 3.40, "2": 3.60}
        self.bookmaker = bookmaker

    def best(self, pick: str) -> float:
        return self.prices[pick]


def odds_from_file(path: str | Path) -> Dict[str, OddsBoard]:
    """Charge des cotes locales. Clé = match_id. CSV : match_id,market,pick,odds,bookmaker."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        import yaml
        raw = yaml.safe_load(text) or []
    else:
        raw = list(csv.DictReader(text.splitlines()))

    boards: Dict[str, OddsBoard] = {}
    for row in raw:
        mid = str(row["match_id"])
        market = str(row.get("market", "1X2"))
        board = boards.get(mid) or OddsBoard(market, {}, str(row.get("bookmaker", "")))
        board.prices[str(row["pick"])] = float(row["odds"])
        boards[mid] = board
    return boards


def median_odds(prices_by_book: List[Dict[str, float]]) -> Dict[str, float]:
    """Médiane des cotes de plusieurs bookmakers, par issue.

    La médiane réduit l'impact d'une cote aberrante (erreur de scraping ou
    bookmaker isolé).
    """
    if not prices_by_book:
        return {}
    keys = set().union(*[set(d) for d in prices_by_book])
    out: Dict[str, float] = {}
    for k in keys:
        vals = [d[k] for d in prices_by_book if k in d]
        if vals:
            out[k] = float(median(vals))
    return out
