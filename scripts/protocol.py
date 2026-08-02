#!/usr/bin/env python3
"""Protocole 100 jours — suivi complet : prédictions, résultats, bankroll.

  init     démarre l'expérience (remet tout à zéro, bankroll de départ)
  add      enregistre la prédiction du jour (avec mise calculée)
  settle   enregistre le résultat d'une prédiction (won/lost/void)
  report   état du protocole : jour N/100, bilan, bankroll, calibration

Usage :
  PYTHONPATH=src python3 scripts/protocol.py init --bankroll 10 --start 2026-08-03
  PYTHONPATH=src python3 scripts/protocol.py add --file pred.json
  PYTHONPATH=src python3 scripts/protocol.py settle --id 2026-08-03 --result won
  PYTHONPATH=src python3 scripts/protocol.py report
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sportsbet import bankroll as BK  # noqa: E402

STATE = ROOT / "data" / "protocol.json"
DAYS = 100


def _load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def _save(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_init(argv: list[str]) -> None:
    bk = float(argv[argv.index("--bankroll") + 1]) if "--bankroll" in argv else 10.0
    start = argv[argv.index("--start") + 1] if "--start" in argv else \
        datetime.date.today().isoformat()
    end = (datetime.date.fromisoformat(start) + datetime.timedelta(days=DAYS - 1)).isoformat()
    st = {
        "protocol": "100 jours", "start": start, "end": end, "days": DAYS,
        "bankroll_start": bk, "bankroll": bk, "mode": "PAPER",
        "tax_mode": "gross", "kelly_fraction": BK.DEFAULT_KELLY_FRACTION,
        "predictions": [], "bankroll_history": [
            {"date": start, "event": "démarrage", "amount": bk, "balance": bk}],
    }
    _save(st)
    print(f"Protocole initialisé : {start} → {end} ({DAYS} jours)")
    print(f"Bankroll de départ : {bk:.2f} € | mode PAPER | Kelly 1/"
          f"{round(1/BK.DEFAULT_KELLY_FRACTION)} | taxe {BK.TAX_RATE*100:.1f} %")


def cmd_add(argv: list[str]) -> None:
    """Ajoute la prédiction du jour. JSON attendu :
    {id, date, match, competition, market, label, prob, odds}"""
    st = _load()
    if not st:
        print("Protocole non initialisé (lancer `init`)."); return
    src = argv[argv.index("--file") + 1]
    p = json.loads(Path(src).read_text(encoding="utf-8"))
    if any(x["id"] == p["id"] for x in st["predictions"]):
        print(f"La prédiction {p['id']} existe déjà."); return

    plan = BK.plan_stake(st["bankroll"], float(p["prob"]), float(p["odds"]),
                         fraction=st.get("kelly_fraction", 0.20),
                         mode=st.get("tax_mode", "gross"))
    rec = {
        "id": p["id"], "date": p["date"], "match": p["match"],
        "competition": p.get("competition", ""), "market": p["market"],
        "label": p.get("label", p["market"]),
        "prob": round(float(p["prob"]), 4), "odds": float(p["odds"]),
        "eff_odds": round(plan.eff_odds, 3), "min_odds": round(plan.min_odds, 2),
        "edge": round(plan.edge, 4), "kelly_full": round(plan.kelly_full, 4),
        "stake": plan.stake, "playable": plan.playable, "stake_reason": plan.reason,
        "result": "pending", "settled": None, "payout": 0.0,
    }
    st["predictions"].append(rec)
    if plan.playable and plan.stake > 0:
        st["bankroll"] = round(st["bankroll"] - plan.stake, 2)
        st["bankroll_history"].append({"date": p["date"], "event": f"mise {p['match']}",
                                       "amount": -plan.stake, "balance": st["bankroll"]})
    _save(st)
    flag = f"MISE {plan.stake:.2f} €" if plan.playable else "NON JOUABLE"
    print(f"[{rec['id']}] {rec['match']} — {rec['label']}")
    print(f"  proba {rec['prob']*100:.1f}% | cote {rec['odds']:.2f} (min {rec['min_odds']:.2f}) "
          f"| edge {rec['edge']*100:+.1f}% | {flag}")
    print(f"  {plan.reason}")


def cmd_settle(argv: list[str]) -> None:
    st = _load()
    if not st:
        print("Protocole non initialisé."); return
    pid = argv[argv.index("--id") + 1]
    res = argv[argv.index("--result") + 1]
    score = argv[argv.index("--score") + 1] if "--score" in argv else ""
    rec = next((x for x in st["predictions"] if x["id"] == pid), None)
    if not rec:
        print(f"Prédiction {pid} introuvable."); return
    if rec["result"] != "pending":
        print(f"{pid} déjà réglée ({rec['result']})."); return

    rec["result"] = res
    rec["settled"] = datetime.date.today().isoformat()
    rec["score"] = score
    if rec["playable"] and rec["stake"] > 0:
        if res == "won":
            payout = round(rec["stake"] * rec["eff_odds"], 2)
            rec["payout"] = payout
            st["bankroll"] = round(st["bankroll"] + payout, 2)
            st["bankroll_history"].append({"date": rec["settled"],
                                           "event": f"gagné {rec['match']}",
                                           "amount": payout, "balance": st["bankroll"]})
        elif res == "void":
            st["bankroll"] = round(st["bankroll"] + rec["stake"], 2)
            st["bankroll_history"].append({"date": rec["settled"],
                                           "event": f"annulé {rec['match']}",
                                           "amount": rec["stake"], "balance": st["bankroll"]})
        else:
            st["bankroll_history"].append({"date": rec["settled"],
                                           "event": f"perdu {rec['match']}",
                                           "amount": 0.0, "balance": st["bankroll"]})
    _save(st)
    icon = {"won": "🟢", "lost": "🔴", "void": "⚪"}.get(res, "?")
    print(f"{icon} {pid} {rec['match']} — {res} {score} | bankroll {st['bankroll']:.2f} €")


def cmd_report(argv: list[str]) -> None:
    st = _load()
    if not st:
        print("Protocole non initialisé."); return
    preds = st["predictions"]
    settled = [p for p in preds if p["result"] in ("won", "lost")]
    played = [p for p in settled if p["playable"] and p["stake"] > 0]
    won = [p for p in settled if p["result"] == "won"]

    d0 = datetime.date.fromisoformat(st["start"])
    day = (datetime.date.today() - d0).days + 1
    entete = (f"jour {min(day, DAYS)}/{DAYS}" if day >= 1
              else f"démarrage le {st['start']}")

    print(f"╔══ PROTOCOLE 100 JOURS — {entete} ══╗")
    print(f"  Période      : {st['start']} → {st['end']}   (mode {st['mode']})")
    print(f"  Bankroll     : {st['bankroll']:.2f} € (départ {st['bankroll_start']:.2f} €)")
    prof = round(st["bankroll"] - st["bankroll_start"], 2)
    roi = (st["bankroll"] / st["bankroll_start"] - 1) * 100 if st["bankroll_start"] else 0
    print(f"  Profit       : {prof:+.2f} €  ({roi:+.1f} %)")
    print()
    print(f"  Prédictions  : {len(preds)} émises | {len(settled)} réglées | "
          f"{len(preds)-len(settled)} en attente")
    if settled:
        print(f"  Résultats    : {len(won)} 🟢 / {len(settled)-len(won)} 🔴  "
              f"({len(won)/len(settled)*100:.0f} % de réussite)")
    print(f"  Jouables     : {len(played)} misées sur {len(settled)} réglées "
          f"({len([p for p in preds if not p['playable']])} sous le seuil de rentabilité)")

    if settled:
        print("\n  ── CALIBRATION (le modèle dit-il vrai ?) ──")
        buckets: dict[int, list] = {}
        for p in settled:
            b = min(90, int(p["prob"] * 10) * 10)
            buckets.setdefault(b, []).append(p)
        for b in sorted(buckets):
            g = buckets[b]
            pred = sum(x["prob"] for x in g) / len(g) * 100
            real = sum(1 for x in g if x["result"] == "won") / len(g) * 100
            print(f"    {b}-{b+10}% | n={len(g):3d} | prédit {pred:5.1f}% | "
                  f"réel {real:5.1f}% | écart {real-pred:+5.1f} pts")

    if preds:
        print("\n  ── 10 DERNIÈRES ──")
        for p in preds[-10:]:
            ic = {"won": "🟢", "lost": "🔴", "void": "⚪", "pending": "⏳"}[p["result"]]
            st_txt = f"{p['stake']:.2f}€" if p["playable"] else "  —  "
            print(f"    {ic} {p['date']} {p['match'][:34]:34s} {p['label'][:24]:24s} "
                  f"@{p['odds']:.2f} {st_txt}")


def main(argv: list[str]) -> None:
    cmd = argv[1] if len(argv) > 1 else "report"
    {"init": cmd_init, "add": cmd_add, "settle": cmd_settle,
     "report": cmd_report}.get(cmd, cmd_report)(argv)


if __name__ == "__main__":
    main(sys.argv)
