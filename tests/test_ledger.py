import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet import ledger as L


def _coupon(cid, odds, legs):
    return {"id": cid, "created": "2026-07-13T18:00:00", "legs": legs,
            "total_odds": odds, "joint_prob": 0.5, "stake": 1.0, "status": "pending",
            "settled": None, "retro": None}


def test_settle_won_when_all_legs_won():
    c = _coupon("d1", 2.06, [{"match": "A", "market": "m", "pick": "p", "odds": 1.43},
                              {"match": "B", "market": "m", "pick": "p", "odds": 1.44}])
    L.settle_coupon(c, ["won", "won"])
    assert c["status"] == "won"


def test_settle_lost_when_one_leg_lost():
    c = _coupon("d2", 2.06, [{"match": "A", "market": "m", "pick": "p", "odds": 1.43},
                              {"match": "B", "market": "m", "pick": "p", "odds": 1.44}])
    L.settle_coupon(c, ["won", "lost"])
    assert c["status"] == "lost"


def test_record_roi():
    won = _coupon("w", 2.0, [{"match": "A", "market": "m", "pick": "p", "odds": 2.0}])
    won["status"] = "won"
    lost = _coupon("l", 3.0, [{"match": "B", "market": "m", "pick": "p", "odds": 3.0}])
    lost["status"] = "lost"
    r = L.record([won, lost])
    # mise 2 u, retour 2.0 (le gagnant) -> profit 0, ROI 0
    assert r["won"] == 1 and r["lost"] == 1
    assert abs(r["staked"] - 2.0) < 1e-9
    assert abs(r["profit"] - 0.0) < 1e-9
    assert abs(r["win_rate"] - 0.5) < 1e-9


def test_roundtrip_file(tmp_path):
    p = tmp_path / "ledger.jsonl"
    rec = L.CouponRecord(id="x", created="2026-07-13T18:00:00",
                         legs=[{"match": "A", "market": "m", "pick": "p", "odds": 2.0,
                                "result": "pending"}],
                         total_odds=2.0, joint_prob=0.5)
    L.add_coupon(rec, p)
    entries = L.load(p)
    assert len(entries) == 1 and entries[0]["id"] == "x"


def test_render_contains_markers():
    c = _coupon("d", 2.0, [{"match": "A", "market": "m", "pick": "p", "odds": 2.0,
                            "result": "won"}])
    c["status"] = "won"
    out = L.render_text([c])
    assert "🟢" in out and "Bilan" in out
