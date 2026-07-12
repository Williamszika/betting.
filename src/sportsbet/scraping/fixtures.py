"""Découverte des matchs du jour — sans clé API.

Deux voies :
  1. `fixtures_from_file` : charge une liste de matchs depuis un YAML/CSV local
     (utile pour tester, ou quand vous collez les matchs à la main / depuis le
     workflow de recherche).
  2. `discover_fixtures_web` : tente une découverte par recherche web. Best-effort ;
     les résultats doivent être vérifiés. Retourne [] plutôt que de casser.

Le workflow deep-research (workflows/daily_coupon.js) est la voie recommandée
pour trouver les vrais matchs du jour de façon fiable, car il utilise l'outil
de recherche de l'agent.
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..models import Match, Sport


def fixtures_from_file(path: str | Path) -> List[Match]:
    """Charge des matchs depuis un fichier YAML ou CSV.

    Format CSV attendu : sport,league,home,away[,start_time][,match_id]
    Format YAML : liste de mappings avec les mêmes clés.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    rows: list[dict]
    if p.suffix.lower() in (".yaml", ".yml"):
        import yaml  # import paresseux
        rows = yaml.safe_load(text) or []
    else:
        rows = list(csv.DictReader(text.splitlines()))

    matches: List[Match] = []
    for row in rows:
        st: Optional[datetime] = None
        if row.get("start_time"):
            try:
                st = datetime.fromisoformat(str(row["start_time"]))
            except ValueError:
                st = None
        matches.append(
            Match(
                sport=Sport(str(row["sport"]).lower()),
                league=str(row["league"]),
                home=str(row["home"]),
                away=str(row["away"]),
                start_time=st,
                match_id=str(row["match_id"]) if row.get("match_id") else None,
            )
        )
    return matches


def discover_fixtures_web(sport: Sport, date: Optional[str] = None,
                          max_matches: int = 30) -> List[Match]:
    """Tente de découvrir les matchs du jour via recherche web (best-effort).

    NOTE : cette fonction ne parse pas un site précis (ils changent sans cesse
    et chargent souvent en JS). Elle sert de point d'extension : implémentez ici
    l'adaptateur du site que VOUS avez le droit de scraper (robots.txt/CGU).
    Par défaut, elle retourne [] et journalise l'intention.
    """
    from . import web
    day = date or datetime.now().strftime("%Y-%m-%d")
    query = {
        Sport.FOOTBALL: f"matchs football aujourd'hui {day} calendrier",
        Sport.TENNIS: f"tennis ATP WTA order of play {day}",
        Sport.BASKETBALL: f"basketball games today {day} schedule NBA EuroLeague",
    }[sport]
    # On récupère des pistes de sources ; l'extraction structurée reste à
    # brancher sur une source autorisée.
    _ = web.search(query, max_results=max_matches)
    return []
