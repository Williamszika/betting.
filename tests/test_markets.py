import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet import markets as M
from sportsbet import model as MO
from sportsbet import features as F


def test_score_matrix_sums_to_one():
    m = M.score_matrix(1.5, 1.2)
    tot = sum(sum(r) for r in m)
    assert abs(tot - 1.0) < 1e-9


def test_1x2_partition():
    mk = M.all_goal_markets(1.6, 1.1)
    assert abs(mk["1"] + mk["X"] + mk["2"] - 1.0) < 1e-9


def test_double_chance_identities():
    mk = M.all_goal_markets(1.4, 1.3)
    assert abs(mk["DC 1X"] - (mk["1"] + mk["X"])) < 1e-12
    assert abs(mk["DC X2"] - (mk["X"] + mk["2"])) < 1e-12
    assert abs(mk["DC 12"] - (mk["1"] + mk["2"])) < 1e-12


def test_over_under_complementary_and_monotone():
    mk = M.all_goal_markets(1.5, 1.2)
    for t in (0.5, 1.5, 2.5, 3.5):
        assert abs(mk[f"Over {t}"] + mk[f"Under {t}"] - 1.0) < 1e-12
    assert mk["Over 0.5"] > mk["Over 1.5"] > mk["Over 2.5"] > mk["Over 3.5"]


def test_dnb_sums_to_one():
    mk = M.all_goal_markets(1.7, 0.9)
    assert abs(mk["DNB 1"] + mk["DNB 2"] - 1.0) < 1e-9


def test_dixon_coles_raises_draws():
    """La correction DC (rho<0) doit augmenter 0-0 et 1-1 vs Poisson pur."""
    plain = M.all_goal_markets(1.3, 1.2, rho=0.0)
    dc = M.all_goal_markets(1.3, 1.2, rho=-0.12)
    assert dc["CS 0-0"] > plain["CS 0-0"]
    assert dc["CS 1-1"] > plain["CS 1-1"]


def test_european_handicap_partition():
    mk = M.all_goal_markets(1.8, 1.0)
    for h in (-2, -1, 1, 2):
        s = mk[f"EH {h:+d} 1"] + mk[f"EH {h:+d} X"] + mk[f"EH {h:+d} 2"]
        assert abs(s - 1.0) < 1e-9


def test_htft_partition():
    hf = M.halftime_fulltime(1.5, 1.1)
    s = sum(hf[f"{a}/{b}"] for a in "1X2" for b in "1X2")
    assert abs(s - 1.0) < 1e-9


def test_corners_from_real_rates_not_possession():
    """Une équipe qui prend beaucoup de corners doit produire un lambda plus élevé."""
    lots = M.corners_markets(7.5, 4.0, 6.0, 5.0)
    few = M.corners_markets(3.0, 4.0, 2.5, 5.0)
    assert lots["_lambda_home"] > few["_lambda_home"]
    assert lots["Corners Over 9.5"] > few["Corners Over 9.5"]


def test_cards_referee_severity_increases_overs():
    lenient = M.cards_markets(2.0, 2.0, referee_factor=0.85)
    strict = M.cards_markets(2.0, 2.0, referee_factor=1.30)
    assert strict["Cards Over 4.5"] > lenient["Cards Over 4.5"]


def test_all_markets_broad_coverage():
    mk = M.all_markets(1.5, 1.2,
                       corners={"home_corners_for": 6.0, "home_corners_against": 4.5,
                                "away_corners_for": 5.0, "away_corners_against": 5.5},
                       cards={"home_cards": 2.0, "away_cards": 2.2})
    assert len(mk) > 100                      # couverture réellement large
    for k in ("1", "DC 1X", "DNB 1", "Over 2.5", "BTTS Yes", "CS 1-1",
              "EH -1 1", "1/1", "Corners Over 9.5", "Cards Over 3.5"):
        assert k in mk


def test_home_advantage_is_symmetric():
    """Correctif majeur : le bonus domicile doit s'accompagner d'un malus extérieur."""
    a = F.TeamStats(goals_for=1.4, xg=1.4, goals_against=1.3, xga=1.3, is_home=True)
    b = F.TeamStats(goals_for=1.4, xg=1.4, goals_against=1.3, xga=1.3)
    hx, ax = MO.expected_goals(a, b)
    # équipes identiques : le seul écart vient de l'avantage du terrain
    ratio = hx / ax
    expected = MO.math.exp(MO.HOME_ADV_GAMMA)     # exp(+g/2)/exp(-g/2) = exp(g)
    assert abs(ratio - expected) < 1e-9
    # et la moyenne des deux lambdas reste centrée (pas d'inflation globale)
    assert abs((hx * ax) ** 0.5 - (1.4 * (1.3 / 1.35)) * 1.0) < 0.35
