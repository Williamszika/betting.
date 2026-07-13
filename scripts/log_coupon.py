#!/usr/bin/env python3
"""Journalise un coupon dans le registre puis régénère le tableau de bord.

Usage : PYTHONPATH=src python3 scripts/log_coupon.py coupon.json
Le JSON doit contenir : id, total_odds, joint_prob, legs[{match,market,pick,odds}]
(created/stake/status ajoutés par défaut si absents).
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sportsbet import ledger as L  # noqa

LEDGER = ROOT / "data" / "ledger.jsonl"

def main(argv):
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8")) if len(argv) > 1 else json.load(sys.stdin)
    for lg in data.get("legs", []):
        lg.setdefault("result", "pending")
    rec = {
        "id": data["id"],
        "created": data.get("created", ""),
        "legs": data.get("legs", []),
        "total_odds": float(data.get("total_odds", 0)),
        "joint_prob": float(data.get("joint_prob", 0)),
        "stake": float(data.get("stake", 1.0)),
        "status": "pending", "settled": None, "retro": None,
    }
    L.add_coupon(rec, LEDGER)
    print(f"Coupon {rec['id']} journalisé ({len(rec['legs'])} jambes, cote {rec['total_odds']:.2f}).")

if __name__ == "__main__":
    main(sys.argv)
