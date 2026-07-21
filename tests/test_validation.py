import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet import validation as V


def _entry(legs, status="lost"):
    return {"id": "2026-07-18", "legs": legs, "status": status}


def test_iter_predictions_only_settled():
    e = _entry([
        {"match": "A vs B", "market": "1X2", "pick": "1", "est_prob": 0.6, "odds": 1.9, "result": "won"},
        {"match": "C vs D", "market": "Over", "pick": "Over", "est_prob": 0.5, "odds": 2.0, "result": "pending"},
    ])
    preds = V.iter_predictions([e])
    assert len(preds) == 1
    assert preds[0]["won"] is True


def test_calibration_buckets():
    preds = [
        {"est_prob": 0.62, "won": True, "context": "normal", "closing_odds": None},
        {"est_prob": 0.64, "won": False, "context": "normal", "closing_odds": None},
    ]
    cal = V.calibration(preds)
    assert len(cal) == 1                       # les deux tombent dans 60-70%
    assert cal[0]["tranche"] == "60-70%"
    assert cal[0]["n"] == 2
    assert cal[0]["reel"] == 50.0              # 1 gagné / 2


def test_clv_positive_when_beating_closing():
    preds = [{"odds": 2.10, "closing_odds": 2.00, "est_prob": 0.5, "won": True, "context": "normal"}]
    rep = V.clv_report(preds)
    assert rep["n"] == 1
    assert rep["clv_moyen"] > 0                # 2.10/2.00 - 1 = +0.05
    assert rep["clv_positifs"] == "1/1"


def test_gate_stays_paper_on_small_sample():
    entries = [_entry([{"match": "A vs B", "market": "1X2", "pick": "1",
                        "est_prob": 0.6, "odds": 1.9, "result": "won"}], status="won")]
    g = V.gate(entries)
    assert g["mode"] == "PAPER"                # jamais REVIEW sous le seuil
    assert g["mode"] != "MISER"               # ne dit JAMAIS miser


def test_by_context_separates_finale():
    preds = [
        {"est_prob": 0.5, "won": False, "context": "finale", "closing_odds": None},
        {"est_prob": 0.5, "won": True, "context": "normal", "closing_odds": None},
    ]
    ctx = {r["contexte"]: r for r in V.by_context(preds)}
    assert ctx["finale"]["reussite"] == 0.0
    assert ctx["normal"]["reussite"] == 100.0
