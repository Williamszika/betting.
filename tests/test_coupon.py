import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet.coupon import build_coupon, build_multiple_coupons
from sportsbet.models import Match, Selection, Sport


def _sel(idx, odds, prob):
    m = Match(sport=Sport.FOOTBALL, league="Test", home=f"H{idx}", away=f"A{idx}",
              match_id=str(idx))
    return Selection(match=m, market="1X2", pick="1", decimal_odds=odds, model_prob=prob)


def test_reaches_target_odds():
    sels = [_sel(i, 1.5, 0.7) for i in range(6)]
    c = build_coupon(sels, target_odds=5.0)
    assert c is not None
    assert c.total_odds >= 5.0


def test_prefers_higher_joint_probability():
    # Deux façons d'atteindre ~5.0 : une jambe très cotée peu probable,
    # ou plusieurs jambes plus probables. On veut la plus probable.
    risky = _sel(1, 5.2, 0.20)
    safe = [_sel(i, 1.75, 0.62) for i in range(2, 5)]  # 1.75^3 ≈ 5.36
    c = build_coupon([risky, *safe], target_odds=5.0)
    assert c is not None
    assert c.joint_prob > risky.model_prob


def test_returns_none_when_unreachable():
    sels = [_sel(i, 1.2, 0.85) for i in range(2)]  # max 1.44 < 5.0
    assert build_coupon(sels, target_odds=5.0, max_legs=2) is None


def test_distinct_matches_in_multiple_coupons():
    sels = [_sel(i, 1.6, 0.65) for i in range(12)]
    coupons = build_multiple_coupons(sels, n=3, target_odds=5.0, max_legs=4)
    used = [s.match.match_id for c in coupons for s in c.selections]
    assert len(used) == len(set(used))  # aucun match réutilisé


def test_expected_value_computed():
    c = build_coupon([_sel(i, 1.5, 0.7) for i in range(6)], target_odds=5.0)
    assert c is not None
    ev = c.expected_value
    assert math.isclose(ev, c.joint_prob * c.total_odds - 1.0, rel_tol=1e-9)
