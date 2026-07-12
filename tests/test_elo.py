import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet.probability import elo


def test_equal_ratings_is_fifty_fifty():
    p = elo.win_probs(1500, 1500)
    assert math.isclose(p["home"], 0.5, rel_tol=1e-9)


def test_probs_sum_to_one():
    p = elo.win_probs(1700, 1500)
    assert math.isclose(p["home"] + p["away"], 1.0, rel_tol=1e-9)


def test_home_advantage_helps():
    without = elo.win_probs(1500, 1500)["home"]
    with_adv = elo.win_probs(1500, 1500, home_advantage=100)["home"]
    assert with_adv > without


def test_update_moves_toward_result():
    exp = elo.expected_score(1500, 1500)  # 0.5
    r = elo.update_rating(1500, actual=1, expected=exp, k=20)
    assert r > 1500
