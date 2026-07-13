import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet import features as F
from sportsbet import model as M


def test_normalize_bounds():
    assert F.normalize(0, 0, 10) == 0.0
    assert F.normalize(10, 0, 10) == 1.0
    assert F.normalize(5, 0, 10) == 0.5
    assert F.normalize(-3, 0, 10) == 0.0   # borné bas
    assert F.normalize(99, 0, 10) == 1.0   # borné haut


def test_weights_sum_to_one():
    assert math.isclose(sum(F.DEFAULT_WEIGHTS.values()), 1.0, rel_tol=1e-9)


def test_stronger_team_scores_higher():
    strong = F.TeamStats(goals_for=2.2, xg=2.0, form_points=13, availability=1.0, is_home=True)
    weak = F.TeamStats(goals_for=0.8, xg=0.9, form_points=4, availability=0.7)
    assert F.team_score(strong, weak) > F.team_score(weak, strong)


def test_expected_goals_favours_stronger_home():
    home = F.TeamStats(goals_for=2.1, xg=1.9, goals_against=0.9, xga=1.0,
                       form_points=12, is_home=True)
    away = F.TeamStats(goals_for=1.0, xg=1.1, goals_against=1.8, xga=1.7,
                       form_points=5)
    hx, ax = M.expected_goals(home, away)
    assert hx > ax


def test_predict_football_normalised():
    home = F.TeamStats(is_home=True)
    away = F.TeamStats()
    p = M.predict_football(home, away)
    assert math.isclose(p["1"] + p["X"] + p["2"], 1.0, rel_tol=1e-6)


def test_predict_two_way_symmetry():
    a = F.TeamStats(form_points=10)
    b = F.TeamStats(form_points=10)
    p = M.predict_two_way(a, b)
    assert math.isclose(p["home"], 0.5, rel_tol=1e-6)
    assert math.isclose(p["home"] + p["away"], 1.0, rel_tol=1e-9)


def test_blend_and_value():
    blended = M.blend_probabilities(0.7, 0.5, weight_model=0.5)
    assert math.isclose(blended, 0.6, rel_tol=1e-9)
    assert M.value_vs_odds(0.60, 2.0) > 0
    assert M.value_vs_odds(0.40, 2.0) < 0


def test_market_probabilities_dispatch():
    home = F.TeamStats(is_home=True)
    away = F.TeamStats()
    foot = M.market_probabilities("football", home, away)
    assert {"1", "X", "2"} <= set(foot)
    tw = M.market_probabilities("tennis", home, away)
    assert set(tw) == {"home", "away"}


def test_blend_market_probs():
    model = {"1": 0.6, "X": 0.25, "2": 0.15}
    research = {"1": 0.4, "X": 0.25, "2": 0.35}
    blended = M.blend_market_probs(model, research, weight_model=0.5)
    assert math.isclose(blended["1"], 0.5, rel_tol=1e-9)
    # clé absente d'un côté -> valeur disponible
    b2 = M.blend_market_probs({"1": 0.6}, {"2": 0.4})
    assert b2["1"] == 0.6 and b2["2"] == 0.4


def test_weighted_recent_favours_recent():
    # même valeurs mais la tendance récente pèse plus
    montante = F.weighted_recent([0, 0, 3, 3, 3])   # récent bon
    descendante = F.weighted_recent([3, 3, 3, 0, 0])  # récent mauvais
    assert montante > descendante


def test_weighted_form_points_scale():
    fp = F.weighted_form_points(["W", "W", "W", "W", "W"])
    assert math.isclose(fp, 15.0, rel_tol=1e-9)   # 5 victoires -> 15/15
    fp0 = F.weighted_form_points(["L", "L", "L"])
    assert math.isclose(fp0, 0.0, abs_tol=1e-9)


def test_elo_1x2_sums_and_favours_stronger():
    e = M.elo_1x2(1800, 1500)
    assert math.isclose(e["1"] + e["X"] + e["2"], 1.0, rel_tol=1e-9)
    assert e["1"] > e["2"]


def test_two_way_elo_dominates_on_big_gap():
    # Outsider en super forme MAIS ELO bien inférieur -> proba capée par l'ELO.
    underdog = F.TeamStats(is_home=True, form_points=15, availability=1.0, elo=1560)
    favorite = F.TeamStats(form_points=6, availability=1.0, elo=1830)  # ~top niveau
    p = M.predict_two_way(underdog, favorite)
    # malgré sa forme, l'outsider reste minoritaire (l'ELO domine)
    assert p["home"] < 0.45
    assert math.isclose(p["home"] + p["away"], 1.0, rel_tol=1e-9)


def test_calibrate_to_market_pulls_more_when_unreliable_or_big_gap():
    base = M.calibrate_to_market(0.55, 0.29, reliability=1.0, level_gap=0.0)
    weak_comp = M.calibrate_to_market(0.55, 0.29, reliability=0.3, level_gap=0.0)
    big_gap = M.calibrate_to_market(0.55, 0.29, reliability=1.0, level_gap=300.0)
    # plus on est vers le marché (0.29), plus la proba baisse depuis 0.55
    assert base >= weak_comp >= 0.29
    assert base >= big_gap >= 0.29
    # compétition faible ET gros écart -> encore plus proche du marché
    assert weak_comp < 0.55 and big_gap < 0.55


def test_predict_football_elo_shifts_toward_stronger():
    base_home = F.TeamStats(is_home=True)
    base_away = F.TeamStats()
    p_no_elo = M.predict_football(base_home, base_away)
    strong = F.TeamStats(is_home=True, elo=1900)
    weak = F.TeamStats(elo=1400)
    p_elo = M.predict_football(strong, weak)
    assert p_elo["1"] > p_no_elo["1"]
    assert math.isclose(p_elo["1"] + p_elo["X"] + p_elo["2"], 1.0, rel_tol=1e-6)
