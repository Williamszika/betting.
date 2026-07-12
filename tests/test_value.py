import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet import value


def test_edge_positive_when_prob_beats_implied():
    # cote 2.0 => implicite 50% ; modèle 60% => value positive
    assert value.edge(0.60, 2.0) > 0
    assert value.is_value(0.60, 2.0)


def test_edge_negative_when_prob_below_implied():
    assert value.edge(0.40, 2.0) < 0
    assert not value.is_value(0.40, 2.0)


def test_remove_margin_normalises():
    a, b = value.remove_margin_two_way(1.90, 1.90)  # bookmaker margé
    assert math.isclose(a + b, 1.0, rel_tol=1e-9)
    assert math.isclose(a, 0.5, rel_tol=1e-9)


def test_kelly_zero_without_value():
    assert value.kelly_fraction(0.40, 2.0) == 0.0


def test_kelly_positive_with_value_and_capped():
    f = value.kelly_fraction(0.60, 2.0, cap=0.25)
    assert 0 < f <= 0.25
