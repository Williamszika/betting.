#!/usr/bin/env python3
"""SportPredix — MOTEUR QUOTIDIEN (workflow déterministe, sans agent).

Chaîne complète, chaque étape vérifiable :

  [1] DONNÉES    ClubElo /Fixtures  → matchs du jour + distribution de scores
  [2] MODÈLE     λ domicile/extérieur → matrice Dixon-Coles → 146 marchés
  [3] CONTRÔLE   accord avec ClubElo (écart 1X2) ; désaccord fort = drop
  [4] SÉLECTION  ne garder que les marchés dont la cote JUSTE tombe dans la
                 fourchette voulue (défaut 1.75–3.00)
  [5] COUPON     1 à 2 prédictions, matchs DISTINCTS, classées par confiance

La cote juste est calculée APRÈS la taxe allemande de 5,3 % répercutée par
Betano : cote_min = 1 / (0.947 × p). En dessous, le pari est perdant d'avance.

Usage :
  PYTHONPATH=src python3 scripts/daily_engine.py [AAAA-MM-JJ] [--min 1.75] [--max 3.0]
"""
from __future__ import annotations

import csv
import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sportsbet import markets as M  # noqa: E402

TAX_FACTOR = 0.947          # Betano répercute 5,3 % sur le gain
FIXTURES_URL = "http://api.clubelo.com/Fixtures"   # HTTP obligatoire (pas de HTTPS)

# Marchés autorisés au coupon : uniquement ceux que Betano propose partout,
# y compris sur les petits championnats (leçon catalogue Betano).
COUPON_MARKETS = [
    "1", "X", "2", "DC 1X", "DC X2", "DC 12", "DNB 1", "DNB 2",
    "Over 1.5", "Over 2.5", "Over 3.5", "Under 1.5", "Under 2.5", "Under 3.5",
    "BTTS Yes", "BTTS No",
    "Home Over 0.5", "Home Over 1.5", "Away Over 0.5", "Away Over 1.5",
    "1 & Over 2.5", "1 & BTTS Yes", "2 & Over 2.5",
]

LABELS = {
    "1": "Victoire domicile", "X": "Match nul", "2": "Victoire extérieur",
    "DC 1X": "Domicile ou nul", "DC X2": "Extérieur ou nul", "DC 12": "Pas de nul",
    "DNB 1": "Domicile (nul remboursé)", "DNB 2": "Extérieur (nul remboursé)",
    "BTTS Yes": "Les deux équipes marquent", "BTTS No": "Une équipe ne marque pas",
    "Home Over 0.5": "Le domicile marque", "Away Over 0.5": "L'extérieur marque",
    "Home Over 1.5": "Domicile marque 2+", "Away Over 1.5": "Extérieur marque 2+",
    "1 & Over 2.5": "Domicile gagne + plus de 2,5 buts",
    "2 & Over 2.5": "Extérieur gagne + plus de 2,5 buts",
    "1 & BTTS Yes": "Domicile gagne + les deux marquent",
}


CACHE = ROOT / "data" / "cache" / "clubelo_fixtures.csv"


def fetch_fixtures(retries: int = 6) -> list[dict]:
    """ClubElo renvoie fréquemment 503 : on réessaie, puis on retombe sur le
    cache disque. Le workflow ne doit jamais dépendre d'un appel unique."""
    import time
    for attempt in range(retries):
        try:
            out = subprocess.run(
                ["curl", "-sS", "-m", "30", "-A", "Mozilla/5.0", FIXTURES_URL],
                capture_output=True, timeout=45,
            ).stdout.decode("utf-8", "replace")
            if len(out) > 1000 and out.startswith("Date,"):
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                CACHE.write_text(out, encoding="utf-8")
                return list(csv.DictReader(io.StringIO(out)))
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    if CACHE.exists():                       # repli : dernier téléchargement réussi
        print(f"[info] ClubElo indisponible — utilisation du cache {CACHE.name}",
              file=sys.stderr)
        return list(csv.DictReader(io.StringIO(CACHE.read_text(encoding="utf-8"))))
    return []


def lambdas(row: dict) -> tuple[float, float]:
    """λ domicile / extérieur déduits de la distribution de scores ClubElo."""
    lh = la = tot = 0.0
    for k, v in row.items():
        if not k.startswith("R:"):
            continue
        try:
            p = float(v)
        except (TypeError, ValueError):
            continue
        i, j = map(int, k[2:].split("-"))
        lh += p * i
        la += p * j
        tot += p
    return (lh / tot, la / tot) if tot > 0 else (1.30, 1.10)


def clubelo_1x2(row: dict) -> tuple[float, float, float]:
    """1X2 de référence ClubElo (via la distribution d'écart de buts)."""
    h = sum(float(row[k]) for k in row if k.startswith("GD=") and int(k[3:]) > 0)
    h += float(row.get("GD>5") or 0)
    d = float(row["GD=0"])
    a = sum(float(row[k]) for k in row if k.startswith("GD=-"))
    a += float(row.get("GD<-5") or 0)
    s = h + d + a
    return (h / s, d / s, a / s) if s else (0.34, 0.33, 0.33)


def build(date: str, odds_min: float, odds_max: float, max_legs: int = 2) -> dict:
    rows = [r for r in fetch_fixtures() if r.get("Date") == date]
    if not rows:
        return {"date": date, "matches": 0, "candidates": [], "coupon": []}

    cands = []
    for r in rows:
        lh, la = lambdas(r)
        mk = M.all_goal_markets(lh, la, rho=-0.10)
        ch, cd, ca = clubelo_1x2(r)
        # [3] CONTRÔLE : désaccord fort avec la référence => on écarte le match
        gap = max(abs(mk["1"] - ch), abs(mk["X"] - cd), abs(mk["2"] - ca))
        if gap > 0.06:
            continue
        for key in COUPON_MARKETS:
            p = mk.get(key)
            if not p or p <= 0:
                continue
            fair = 1.0 / p                      # cote juste (sans marge)
            need = 1.0 / (TAX_FACTOR * p)       # cote minimale APRÈS taxe
            if odds_min <= fair <= odds_max:    # [4] fourchette demandée
                cands.append({
                    "country": r["Country"], "home": r["Home"], "away": r["Away"],
                    "match": f"{r['Home']} – {r['Away']}",
                    "market": key, "label": LABELS.get(key, key),
                    "prob": p, "fair": fair, "need": need,
                    "lh": lh, "la": la, "gap": gap,
                })

    # [5] COUPON : les plus probables d'abord, matchs distincts
    cands.sort(key=lambda c: -c["prob"])
    coupon, used = [], set()
    for c in cands:
        if c["match"] in used:
            continue
        coupon.append(c)
        used.add(c["match"])
        if len(coupon) >= max_legs:
            break
    return {"date": date, "matches": len(rows), "candidates": cands, "coupon": coupon}


def main(argv: list[str]) -> None:
    date = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else None
    if not date:
        import datetime
        date = datetime.date.today().isoformat()
    omin = float(argv[argv.index("--min") + 1]) if "--min" in argv else 1.75
    omax = float(argv[argv.index("--max") + 1]) if "--max" in argv else 3.00
    n_short = int(argv[argv.index("--shortlist") + 1]) if "--shortlist" in argv else 3

    res = build(date, omin, omax)

    # --json : sortie machine pour l'ÉTAGE 2 (agents de vérification contextuelle).
    # On ne transmet que la SHORTLIST : les agents ne travaillent que sur ces lignes.
    if "--json" in argv:
        import json
        short, used = [], set()
        for c in res["candidates"]:
            if c["match"] in used:
                continue
            used.add(c["match"])
            short.append({
                "country": c["country"], "home": c["home"], "away": c["away"],
                "market": c["market"], "label": c["label"],
                "prob": round(c["prob"], 4), "fair_odds": round(c["fair"], 2),
                "min_odds": round(c["need"], 2),
                "lambda_home": round(c["lh"], 2), "lambda_away": round(c["la"], 2),
                "clubelo_gap": round(c["gap"], 4),
            })
            if len(short) >= n_short:
                break
        print(json.dumps({"date": date, "matches": res["matches"],
                          "candidates": len(res["candidates"]),
                          "shortlist": short}, ensure_ascii=False, indent=2))
        return
    print(f"=== MOTEUR SPORTPREDIX — {date} ===")
    print(f"Matchs ClubElo : {res['matches']} | candidats dans [{omin}–{omax}] : {len(res['candidates'])}\n")

    if res["candidates"]:
        print(f"{'Proba':>6s} {'Juste':>6s} {'Min*':>6s}  {'Pays':4s} {'Match':40s} Marché")
        print("-" * 108)
        for c in res["candidates"][:15]:
            print(f"{c['prob']*100:5.1f}% {c['fair']:6.2f} {c['need']:6.2f}  {c['country']:4s} "
                  f"{c['match'][:40]:40s} {c['label']}")

    print("\n=== COUPON PROPOSÉ ===")
    if not res["coupon"]:
        print("Aucune prédiction dans la fourchette — rien à proposer.")
        return
    total_fair = 1.0
    total_prob = 1.0
    for i, c in enumerate(res["coupon"], 1):
        print(f"  {i}. [{c['country']}] {c['match']}")
        print(f"     → {c['label']}  ({c['market']})")
        print(f"     proba {c['prob']*100:.1f}% | cote juste {c['fair']:.2f} | "
              f"cote MINIMALE utile {c['need']:.2f} | λ {c['lh']:.2f}-{c['la']:.2f}")
        total_fair *= c["fair"]
        total_prob *= c["prob"]
    if len(res["coupon"]) > 1:
        print(f"\n  COMBINÉ : cote juste {total_fair:.2f} | proba conjointe {total_prob*100:.1f}% "
              f"| cote minimale utile {1/(TAX_FACTOR*total_prob):.2f}")
    print("\n* Min = cote sous laquelle le pari est perdant d'avance (taxe 5,3 % incluse).")
    print("  ESTIMATIONS, PAS des certitudes. Mode PAPER.")


if __name__ == "__main__":
    main(sys.argv)
