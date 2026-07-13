import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sportsbet import reliability as R


def test_reliability_scale():
    assert R.competition_reliability("Premier League", "football") == 1.0
    assert R.competition_reliability("NBA Summer League (Las Vegas)", "basketball") == 0.30
    assert R.competition_reliability("ATP 250 Gstaad", "tennis") == 0.90
    # inconnu -> défaut du sport
    assert R.competition_reliability("Coupe régionale X", "football") == 0.70


def test_blacklist_friendlies():
    assert R.is_blacklisted("Club Friendly")
    assert R.is_blacklisted("Match amical")
    assert not R.is_blacklisted("Allsvenskan")


def test_prefilter_removes_summer_league_and_friendlies():
    assert not R.passes_prefilter("NBA Summer League", "basketball")      # 0.30 < 0.35
    assert not R.passes_prefilter("Club Friendly", "football")            # blacklist
    assert R.passes_prefilter("Allsvenskan", "football")                  # 0.85
    assert R.passes_prefilter("ATP 250 Gstaad", "tennis")                 # 0.90


def test_effective_edge_and_thresholds():
    # edge 15% sur Summer League (0.30) -> 4.5% effectif -> sous le seuil safe (5%)
    assert R.effective_edge(0.15, 0.30) < R.MIN_EDGE["safe"]
    assert not R.qualifies(0.15, 0.30, "safe")
    # edge 8% sur top ligue (1.0) -> passe le seuil combiné (6%)
    assert R.qualifies(0.08, 1.0, "combine")
