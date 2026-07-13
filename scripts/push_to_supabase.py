#!/usr/bin/env python3
"""Bridge (mode hybride) : pousse le registre local vers Supabase.

Le job quotidien Claude Code appelle ce script pour synchroniser
data/ledger.jsonl (coupons + jambes) + data/lessons.md vers la base Supabase
que lit le dashboard Next.js.

Env requis :
  SUPABASE_URL         = https://xxxx.supabase.co
  SUPABASE_SERVICE_KEY = service_role key (contourne la RLS ; NE JAMAIS exposer côté client)

Usage : SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python3 scripts/push_to_supabase.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger.jsonl"


def _client():
    import httpx  # dépendance déjà dans requirements.txt
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("SUPABASE_URL / SUPABASE_SERVICE_KEY manquants.", file=sys.stderr)
        sys.exit(2)
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    return httpx.Client(base_url=url.rstrip("/") + "/rest/v1", headers=headers, timeout=30)


def push():
    if not LEDGER.exists():
        print("Aucun registre à pousser.")
        return
    entries = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not entries:
        print("Registre vide.")
        return

    with _client() as c:
        for e in entries:
            coupon = {
                "id": e["id"],
                "created_at": e.get("created") or None,
                "match_date": e["id"][:10] if len(e.get("id", "")) >= 10 else None,
                "bookmaker": e.get("bookmaker", "Betano"),
                "total_odds": e.get("total_odds"),
                "joint_prob": e.get("joint_prob"),
                "stake": e.get("stake", 1),
                "status": e.get("status", "pending"),
                "out_of_range": e.get("out_of_range", False),
                "settled_at": e.get("settled"),
                "retro": e.get("retro"),
            }
            # upsert du coupon (merge sur la PK id)
            r = c.post("/coupons", params={"on_conflict": "id"},
                       headers={"Prefer": "resolution=merge-duplicates"},
                       json=coupon)
            r.raise_for_status()
            # remplace les jambes (idempotent)
            c.delete("/coupon_legs", params={"coupon_id": f"eq.{e['id']}"})
            legs = [{
                "coupon_id": e["id"],
                "match": l.get("match"), "sport": l.get("sport"),
                "competition": l.get("competition"), "market": l.get("market"),
                "pick": l.get("pick"), "odds": l.get("odds"),
                "est_prob": l.get("est_prob"), "reliability": l.get("reliability"),
                "result": l.get("result", "pending"), "note": l.get("note"),
            } for l in e.get("legs", [])]
            if legs:
                c.post("/coupon_legs", json=legs).raise_for_status()
        print(f"{len(entries)} coupon(s) synchronisé(s) vers Supabase.")


if __name__ == "__main__":
    push()
