#!/usr/bin/env python3
"""Croise NOTRE modèle et le VRAI marché — l'outil qui cherche un avantage.

Jusqu'ici on comparait notre probabilité à une cote relevée dans un résumé de
moteur de recherche, sans savoir de quel bookmaker elle venait. Ce script
compare deux sources primaires :

  modèle   ClubElo, distribution de scores exacts → Dixon-Coles → 1X2
  marché   football-data.co.uk, cotes réelles (Pinnacle, moyenne, Betfair,
           bet365, maximum), marge retirée par la méthode puissance

Pour chaque match des deux sources, il affiche l'écart et dit si la MEILLEURE
cote disponible dépasse le seuil de rentabilité. Un écart de moins de ~5 points
ne peut structurellement rien rapporter : la marge du bookmaker le mange.

Usage :
  PYTHONPATH=src python3 scripts/edge_scan.py [AAAA-MM-JJ] [--book bet365] [--min-gap 3]
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sportsbet import bankroll as BK, books as B, footballdata as FD, markets as M  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from daily_engine import (drop_duplicate_fixtures, fetch_fixtures,  # noqa: E402
                          lambdas, score_cells)

ISSUES = [("1", "Victoire domicile"), ("X", "Match nul"), ("2", "Victoire extérieur")]


def scan(date: str, book: str, min_gap: float) -> list[dict]:
    rows, _ = drop_duplicate_fixtures(
        [r for r in fetch_fixtures() if r.get("Date") == date])
    marche = FD.charger(date)
    if not rows:
        print(f"[!] Aucun match ClubElo pour le {date}.", file=sys.stderr)
    if not marche:
        print(f"[!] Aucune cote football-data pour le {date}.", file=sys.stderr)

    out = []
    for r in rows:
        f = FD.rapprocher(r["Home"], r["Away"], marche)
        if not f:
            continue
        m = f.market_1x2()
        if not m:
            continue
        lh, la = lambdas(r)
        mk = M.all_goal_markets(lh, la, cells=score_cells(r))
        for cle, libelle in ISSUES:
            nous, eux = mk[cle], m[cle]
            gap = nous - eux
            if abs(gap) * 100 < min_gap:
                continue
            best = f.meilleure_cote(cle)
            if not best:
                continue
            cote, qui = best
            seuil = BK.min_odds_for_breakeven(nous, B.get(book).tax_mode)
            out.append({
                "match": f.match, "pays": f.pays, "heure": f.heure,
                "issue": libelle, "cle": cle,
                "nous": nous, "marche": eux, "gap": gap,
                "source": m["source"], "marge": m["marge"],
                "cote": cote, "qui": qui, "seuil": seuil,
                "jouable": cote >= seuil and gap > 0,
            })
    out.sort(key=lambda x: -x["gap"])
    return out


def main(argv: list[str]) -> None:
    date = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else None
    if not date:
        import datetime
        date = datetime.date.today().isoformat()
    book = argv[argv.index("--book") + 1] if "--book" in argv else "bet365"
    min_gap = float(argv[argv.index("--min-gap") + 1]) if "--min-gap" in argv else 3.0

    b = B.get(book)
    print(f"=== ÉCART MODÈLE / MARCHÉ — {date} ===")
    print(f"Opérateur de référence : {b.name} (taxe {b.tax_mode}) | "
          f"écart minimal affiché : {min_gap:.0f} pts\n")

    res = scan(date, book, min_gap)
    if not res:
        print("Aucun match commun aux deux sources, ou aucun écart significatif.")
        return

    print(f"{'Écart':>7s} {'Nous':>6s} {'Marché':>7s} {'Cote':>6s} {'Seuil':>6s}  "
          f"{'Match':34s} Issue")
    print("-" * 104)
    for r in res[:20]:
        flag = "✅" if r["jouable"] else "  "
        print(f"{r['gap']*100:+6.1f} {r['nous']*100:5.1f}% {r['marche']*100:6.1f}% "
              f"{r['cote']:6.2f} {r['seuil']:6.2f} {flag}{r['match'][:33]:33s} {r['issue']}")

    jouables = [r for r in res if r["jouable"]]
    print(f"\n{len(res)} écart(s) ≥ {min_gap:.0f} pts | {len(jouables)} au-dessus du seuil "
          f"de rentabilité chez {b.name}")
    if jouables:
        print("\nRAPPEL : un écart n'est un avantage QUE si rien d'extérieur ne l'explique.")
        print("Règle dure : au-delà de 5 points, chercher un événement récent sur les")
        print("10 derniers jours (élimination, entraîneur, blessures) AVANT de conclure.")
    else:
        print("\nRien de jouable : les cotes offertes sont sous le seuil, ou le modèle")
        print("ne s'écarte pas assez du marché. C'est un résultat, pas un échec.")


if __name__ == "__main__":
    main(sys.argv)
