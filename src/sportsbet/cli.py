"""Interface en ligne de commande.

Exemples :
  # À partir de fichiers locaux (matchs + cotes récupérés au préalable) :
  python -m sportsbet.cli daily \
      --fixtures data/fixtures.csv --odds data/odds.csv \
      --target-odds 5 --coupons 5

Le mode « daily » construit jusqu'à N coupons visant la cote cible, en
maximisant la probabilité conjointe estimée (les « plus sûrs » qui atteignent
la cote demandée). Rappel : « plus sûr » n'est pas « sûr ».
"""
from __future__ import annotations

import argparse
import sys
from typing import Dict

from .agents.research_agent import TeamRatings
from .pipeline import PipelineConfig, run_daily
from .scraping.fixtures import fixtures_from_file
from .scraping.odds import OddsBoard, odds_from_file


def _index_odds(matches, boards: Dict[str, OddsBoard]) -> Dict[str, OddsBoard]:
    """Réindexe les cotes par la clé utilisée par le pipeline (match_id|label)."""
    out: Dict[str, OddsBoard] = {}
    for m in matches:
        key = m.match_id or m.label()
        if m.match_id and m.match_id in boards:
            out[key] = boards[m.match_id]
    return out


def cmd_daily(args: argparse.Namespace) -> int:
    matches = fixtures_from_file(args.fixtures)
    boards = odds_from_file(args.odds) if args.odds else {}
    odds_by_match = _index_odds(matches, boards)

    ratings = TeamRatings.from_file(args.ratings) if args.ratings else TeamRatings()
    cfg = PipelineConfig(
        target_odds=args.target_odds,
        max_total_odds=args.max_odds,
        n_coupons=args.coupons,
        max_legs=args.max_legs,
        min_legs=args.min_legs,
        min_edge=args.min_edge,
        max_workers=args.workers,
        gather_signals=args.signals,
    )
    report = run_daily(matches, odds_by_match, ratings=ratings, config=cfg)
    print(report.render())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sportsbet", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("daily", help="Construire les coupons du jour")
    d.add_argument("--fixtures", required=True, help="CSV/YAML des matchs")
    d.add_argument("--odds", help="CSV/YAML des cotes (clé match_id)")
    d.add_argument("--ratings", help="CSV/YAML des notes de force (name,rating)")
    d.add_argument("--target-odds", type=float, default=5.0,
                   help="Cote totale minimale visée. Défaut: 5.0")
    d.add_argument("--max-odds", type=float, default=7.0,
                   help="Cote totale maximale (fourchette). Défaut: 7.0")
    d.add_argument("--coupons", type=int, default=2,
                   help="Nombre de paris/coupons à sortir. Défaut: 2")
    d.add_argument("--max-legs", type=int, default=6)
    d.add_argument("--min-legs", type=int, default=1,
                   help="Jambes minimum. 1 = paris simples ; >=2 = combiné. Défaut: 1.")
    d.add_argument("--min-edge", type=float, default=None,
                   help="Filtrer par value minimale (ex. 0.05). Défaut: mode 'plus sûr'.")
    d.add_argument("--workers", type=int, default=12)
    d.add_argument("--signals", action="store_true",
                   help="Tenter la recherche web de signaux (plus lent).")
    d.set_defaults(func=cmd_daily)
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
