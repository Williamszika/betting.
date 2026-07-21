#!/usr/bin/env python3
"""Applique un règlement au registre puis régénère le tableau de bord.

Usage : PYTHONPATH=src python3 scripts/apply_settlement.py settlement.json
JSON : [{ "id": "...", "leg_results": ["won","lost",...], "retro": {..} (optionnel) }, ...]
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sportsbet import ledger as L  # noqa

LEDGER = ROOT / "data" / "ledger.jsonl"

def main(argv):
    settlements = json.loads(Path(argv[1]).read_text(encoding="utf-8")) if len(argv) > 1 else json.load(sys.stdin)
    by_id = {s["id"]: s for s in settlements}
    entries = L.load(LEDGER)
    for e in entries:
        s = by_id.get(e.get("id"))
        if not s or e.get("status") not in (None, "pending"):
            continue
        L.settle_coupon(e, s.get("leg_results", []))
        e["settled"] = s.get("settled", "")
        if s.get("retro"):
            e["retro"] = s["retro"]
        # Cote de CLÔTURE optionnelle (pour le CLV) : liste alignée sur les jambes.
        co = s.get("closing_odds") or []
        for i, lg in enumerate(e.get("legs", [])):
            if i < len(co) and co[i]:
                lg["closing_odds"] = float(co[i])
    L.save_all(entries, LEDGER)
    print(L.render_text(entries))

if __name__ == "__main__":
    main(sys.argv)
