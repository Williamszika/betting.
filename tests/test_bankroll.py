"""Tests du calcul de mise — la partie qui touche l'argent réel."""
from __future__ import annotations

import math

import pytest

from sportsbet import bankroll as BK


# ── Taxe ─────────────────────────────────────────────────────────────────────

def test_cote_effective_inferieure_a_la_cote_affichee():
    """Betano répercute la taxe : on touche moins que la cote affichée."""
    assert BK.effective_odds(2.00, "gross") == pytest.approx(1.894, abs=1e-3)
    assert BK.effective_odds(2.00, "net") == pytest.approx(1.947, abs=1e-3)
    assert BK.effective_odds(2.00, "none") == 2.00
    assert BK.effective_odds(2.00, "gross") < BK.effective_odds(2.00, "net")


def test_seuil_de_rentabilite_coherent_avec_la_cote_effective():
    """À la cote minimale exacte, l'edge doit être nul (à l'arrondi près)."""
    for p in (0.30, 0.45, 0.571, 0.70):
        for mode in ("gross", "net", "none"):
            mo = BK.min_odds_for_breakeven(p, mode)
            assert BK.edge(p, mo, mode) == pytest.approx(0.0, abs=1e-9)


def test_seuil_sans_taxe_est_la_cote_juste():
    assert BK.min_odds_for_breakeven(0.50, "none") == pytest.approx(2.0)
    # avec taxe, il faut toujours PLUS que la cote juste
    assert BK.min_odds_for_breakeven(0.50, "gross") > 2.0


def test_probabilite_nulle_ne_casse_pas():
    assert BK.min_odds_for_breakeven(0.0) == math.inf
    assert BK.kelly_fraction(0.0, 3.0) == 0.0


# ── Kelly ────────────────────────────────────────────────────────────────────

def test_kelly_nul_sans_avantage():
    """Sous le seuil de rentabilité, Kelly = 0, jamais négatif."""
    assert BK.kelly_fraction(0.50, 1.90, "gross") == 0.0
    assert BK.kelly_fraction(0.30, 2.00, "gross") == 0.0


def test_kelly_croit_avec_la_cote():
    a = BK.kelly_fraction(0.45, 2.50)
    b = BK.kelly_fraction(0.45, 3.00)
    c = BK.kelly_fraction(0.45, 4.00)
    assert 0 < a < b < c


def test_kelly_formule_exacte_sans_taxe():
    """p=0.60, cote 2.00 → f* = (0.6·1 − 0.4)/1 = 0.20."""
    assert BK.kelly_fraction(0.60, 2.00, "none") == pytest.approx(0.20)


def test_kelly_taxe_reduit_la_mise():
    assert BK.kelly_fraction(0.60, 2.00, "gross") < BK.kelly_fraction(0.60, 2.00, "none")


# ── Décision de mise ─────────────────────────────────────────────────────────

def test_refus_si_cote_sous_le_seuil():
    """57,1 % exige 1,85 après taxe : à 1,80 le pari est perdant d'avance."""
    plan = BK.plan_stake(100.0, 0.571, 1.80)
    assert plan.stake == 0.0 and not plan.playable
    assert "seuil" in plan.reason
    assert plan.edge < 0


def test_refus_si_edge_trop_faible():
    """Un edge de 1 % est du bruit de modèle, pas un avantage."""
    p = 0.50
    odds = 1.01 / (BK.effective_odds(1.0, "gross") * p)   # edge ≈ +1 %
    plan = BK.plan_stake(100.0, p, odds, min_edge=0.02)
    assert not plan.playable and "minimum requis" in plan.reason


def test_refus_si_mise_sous_le_minimum_betano():
    """Cas réel avec 10 € : edge valide mais mise trop petite pour être posée."""
    plan = BK.plan_stake(10.0, 0.571, 1.95)
    assert plan.edge > 0.02          # l'avantage EXISTE
    assert not plan.playable         # mais il n'est pas jouable
    assert plan.stake == 0.0
    assert "minimum Betano" in plan.reason


def test_meme_pari_devient_jouable_avec_une_bankroll_plus_grande():
    petit = BK.plan_stake(10.0, 0.571, 1.95)
    grand = BK.plan_stake(100.0, 0.571, 1.95)
    assert not petit.playable and grand.playable
    assert grand.stake >= BK.MIN_STAKE


def test_mise_proportionnelle_a_la_bankroll():
    """La FRACTION est identique ; la mise ne diffère que par l'arrondi au centime."""
    a = BK.plan_stake(100.0, 0.45, 3.00)
    b = BK.plan_stake(1000.0, 0.45, 3.00)
    assert a.kelly_used == pytest.approx(b.kelly_used)
    assert b.stake == pytest.approx(a.stake * 10, abs=0.10)


def test_plafond_absolu_respecte():
    """Même une quasi-certitude ne dépasse pas le plafond de bankroll."""
    plan = BK.plan_stake(1000.0, 0.95, 3.00, max_share=0.05)
    assert plan.stake <= 1000.0 * 0.05 + 1e-9


def test_fraction_de_kelly_reduit_bien_la_mise():
    plein = BK.plan_stake(1000.0, 0.45, 3.00, fraction=1.0, max_share=1.0).stake
    cinq = BK.plan_stake(1000.0, 0.45, 3.00, fraction=0.20, max_share=1.0).stake
    assert cinq == pytest.approx(plein * 0.20, rel=1e-6)


def test_bankroll_epuisee():
    plan = BK.plan_stake(0.0, 0.45, 3.00)
    assert not plan.playable and "épuisée" in plan.reason


def test_plan_tracable():
    """Toute décision doit être reconstituable à partir du plan seul."""
    plan = BK.plan_stake(100.0, 0.45, 3.00)
    assert plan.prob == 0.45 and plan.odds == 3.00
    assert plan.eff_odds == pytest.approx(BK.effective_odds(3.00))
    assert plan.min_odds == pytest.approx(BK.min_odds_for_breakeven(0.45))
    assert plan.edge == pytest.approx(BK.edge(0.45, 3.00))
    assert plan.bankroll == 100.0
    assert plan.reason


# ── Suivi du capital ─────────────────────────────────────────────────────────

def test_cycle_complet_gagnant():
    bk = BK.Bankroll(start=10.0, current=10.0)
    bk.bet("2026-08-03", "A–B", 0.30)
    assert bk.current == pytest.approx(9.70)
    bk.win("2026-08-04", "A–B", 0.30, 3.00)
    assert bk.current == pytest.approx(9.70 + 0.30 * 0.947 * 3.00)
    assert bk.profit > 0 and bk.roi > 0
    assert len(bk.history) == 2


def test_cycle_complet_perdant():
    bk = BK.Bankroll(start=10.0, current=10.0)
    bk.bet("2026-08-03", "A–B", 0.50)
    bk.lose("2026-08-04", "A–B")
    assert bk.current == pytest.approx(9.50)
    assert bk.profit == pytest.approx(-0.50)


def test_serie_perdante_ne_ruine_pas_la_bankroll():
    """Kelly fractionnaire : 10 pertes d'affilée laissent encore du capital."""
    bank = 100.0
    for _ in range(10):
        plan = BK.plan_stake(bank, 0.45, 3.00)
        if not plan.playable:
            break
        bank = round(bank - plan.stake, 2)
    assert bank > 70.0    # la ruine est impossible en fractionnaire
