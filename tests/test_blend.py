"""Tests du mélange modèle/marché et des ajustements bornés."""
from __future__ import annotations

import pytest

from sportsbet import blend as BL


def test_poids_croit_avec_l_historique():
    peu = BL.Fiabilite(matchs_historique=2, a_xg=True, actualite_verifiee=True, ligue_majeure=True)
    beaucoup = BL.Fiabilite(matchs_historique=10, a_xg=True, actualite_verifiee=True, ligue_majeure=True)
    assert peu.poids() < beaucoup.poids()


def test_poids_jamais_hors_bornes():
    for h in (0, 3, 10, 50):
        for flags in ((True, True, True), (False, False, False)):
            f = BL.Fiabilite(h, *flags)
            assert BL.POIDS_MIN <= f.poids() <= BL.POIDS_MAX


def test_le_modele_ne_depasse_jamais_la_moitie():
    """Prétendre en savoir plus que l'ensemble des parieurs professionnels
    n'est justifié par aucune de nos mesures."""
    parfait = BL.Fiabilite(100, True, True, True)
    assert parfait.poids() <= 0.50


def test_actualite_non_verifiee_reduit_le_poids():
    """Cas FCSB : 7 points d'écart qui ne mesuraient que notre retard."""
    avec = BL.Fiabilite(10, True, True, True).poids()
    sans = BL.Fiabilite(10, True, False, True).poids()
    assert sans < avec


def test_melange_borne_et_monotone():
    assert BL.melanger(0.8, 0.4, 1.0) == pytest.approx(0.8)
    assert BL.melanger(0.8, 0.4, 0.0) == pytest.approx(0.4)
    assert BL.melanger(0.8, 0.4, 0.5) == pytest.approx(0.6)
    assert 0.0 <= BL.melanger(1.5, -0.2, 0.5) <= 1.0


def test_melange_1x2_somme_a_un():
    modele = {"1": 0.55, "X": 0.25, "2": 0.20}
    marche = {"1": 0.45, "X": 0.30, "2": 0.25}
    for w in (0.0, 0.3, 0.5, 1.0):
        r = BL.melanger_1x2(modele, marche, w)
        assert sum(r.values()) == pytest.approx(1.0, abs=1e-9)


def test_melange_1x2_renormalise_une_entree_tronquee():
    r = BL.melanger_1x2({"1": 0.5, "X": 0.2, "2": 0.1}, {"1": 0.4, "X": 0.3, "2": 0.3}, 0.5)
    assert sum(r.values()) == pytest.approx(1.0)


# ── Ajustements textuels ─────────────────────────────────────────────────────

def test_ajustement_neutre_sans_fait():
    assert BL.ajustement([]) == pytest.approx(1.0)


def test_fait_inconnu_ignore():
    """Un agent ne peut pas inventer une catégorie d'effet."""
    assert BL.ajustement(["le_gardien_a_mal_dormi"]) == pytest.approx(1.0)


def test_buteur_absent_reduit():
    a = BL.ajustement(["buteur_principal_absent"])
    assert 0.85 < a < 1.0


def test_plafond_absolu_respecte():
    """Un agent enthousiaste transformerait cinq absences en catastrophe."""
    beaucoup = ["buteur_principal_absent"] * 5 + ["rotation_annoncee"] * 3
    assert BL.ajustement(beaucoup) == pytest.approx(1.0 - BL.PLAFOND_AJUSTEMENT)


def test_plafond_parametrable():
    assert BL.ajustement(["buteur_principal_absent"] * 5, plafond=0.05) == pytest.approx(0.95)


def test_explication_lisible():
    txt = BL.Fiabilite(8, False, True, False).explication()
    assert "8 matchs" in txt and "proxy" in txt and "vérifiée" in txt
