"""Registre (ledger) des coupons : historique, règlement, bilan 🟢/🔴, ROI.

Chaque coupon généré est enregistré (statut « pending »). Après les matchs, le
règlement marque chaque jambe gagnée/perdue, le coupon est 🟢 (toutes gagnées)
ou 🔴 (au moins une perdue), et on suit le bilan cumulé.

Format : un fichier JSONL (une ligne = un coupon). Aucune dépendance externe.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Leg:
    match: str
    market: str
    pick: str
    odds: float
    result: str = "pending"   # pending | won | lost | void
    note: str = ""


@dataclass
class CouponRecord:
    id: str                       # ex. date des matchs "2026-07-14" (+ suffixe si plusieurs)
    created: str                  # ISO
    legs: List[dict] = field(default_factory=list)
    total_odds: float = 0.0
    joint_prob: float = 0.0
    stake: float = 1.0
    status: str = "pending"       # pending | won | lost | void
    settled: Optional[str] = None
    retro: Optional[dict] = None  # analyse rétro en cas de perte


def add_coupon(rec: CouponRecord, path: str | Path) -> None:
    """Ajoute un coupon au registre (append JSONL)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(rec) if isinstance(rec, CouponRecord) else rec,
                           ensure_ascii=False) + "\n")


def load(path: str | Path) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def save_all(entries: List[dict], path: str | Path) -> None:
    """Réécrit tout le registre (après règlement)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def settle_coupon(entry: dict, leg_results: List[str]) -> dict:
    """Applique les résultats de jambes (won/lost/void) et fixe le statut.

    - 🔴 lost si AU MOINS une jambe perdue ;
    - 🟢 won si toutes les jambes non-void sont gagnées ;
    - void si toutes void.
    """
    legs = entry.get("legs", [])
    for leg, res in zip(legs, leg_results):
        leg["result"] = res
    outcomes = [l.get("result", "pending") for l in legs]
    if any(o == "pending" for o in outcomes):
        entry["status"] = "pending"
    elif any(o == "lost" for o in outcomes):
        entry["status"] = "lost"
    elif all(o == "void" for o in outcomes):
        entry["status"] = "void"
    else:
        entry["status"] = "won"
    return entry


def record(entries: List[dict]) -> dict:
    """Bilan cumulé : nombres, taux de réussite, profit et ROI (mise unitaire)."""
    won = [e for e in entries if e.get("status") == "won"]
    lost = [e for e in entries if e.get("status") == "lost"]
    pending = [e for e in entries if e.get("status") == "pending"]
    settled = won + lost
    staked = sum(e.get("stake", 1.0) for e in settled)
    returns = sum(e.get("stake", 1.0) * e.get("total_odds", 0.0) for e in won)
    profit = returns - staked
    return {
        "total": len(entries),
        "won": len(won),
        "lost": len(lost),
        "pending": len(pending),
        "win_rate": (len(won) / len(settled)) if settled else 0.0,
        "staked": staked,
        "profit": profit,
        "roi": (profit / staked) if staked else 0.0,
    }


def _emoji(status: str) -> str:
    return {"won": "🟢", "lost": "🔴", "void": "⚪", "pending": "⏳"}.get(status, "❔")


def render_text(entries: List[dict]) -> str:
    """Rendu texte du suivi (🟢 gagné / 🔴 perdu)."""
    lines = ["SUIVI DES COUPONS", "=" * 60]
    for e in entries:
        lines.append(f"{_emoji(e.get('status'))} {e.get('id')} — cote {e.get('total_odds'):.2f} "
                     f"({e.get('status')})")
        for l in e.get("legs", []):
            lines.append(f"     {_emoji(l.get('result'))} {l.get('match')} : "
                         f"{l.get('pick')} @ {l.get('odds')}")
    r = record(entries)
    lines.append("-" * 60)
    lines.append(f"Bilan : {r['won']}🟢 / {r['lost']}🔴 / {r['pending']}⏳ | "
                 f"réussite {r['win_rate']:.0%} | ROI {r['roi']:+.1%} "
                 f"(profit {r['profit']:+.2f} u)")
    return "\n".join(lines)
