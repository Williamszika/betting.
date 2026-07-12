import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet.probability import poisson


def test_pmf_sums_to_one():
    total = sum(poisson.poisson_pmf(k, 2.3) for k in range(0, 40))
    assert math.isclose(total, 1.0, rel_tol=1e-9)


def test_market_probs_normalised():
    probs = poisson.market_probs(1.6, 1.1)
    # 1X2 doit sommer à ~1
    assert math.isclose(probs["1"] + probs["X"] + probs["2"], 1.0, rel_tol=1e-6)
    # Over + Under = 1
    assert math.isclose(probs["Over 2.5"] + probs["Under 2.5"], 1.0, rel_tol=1e-6)
    # BTTS Oui + Non = 1
    assert math.isclose(probs["BTTS Yes"] + probs["BTTS No"], 1.0, rel_tol=1e-6)


def test_stronger_home_more_likely():
    strong = poisson.market_probs(2.4, 0.7)
    assert strong["1"] > strong["2"]


def test_xg_from_ratings_favours_higher_rated():
    hx, ax = poisson.xg_from_ratings(1800, 1500)
    assert hx > ax
