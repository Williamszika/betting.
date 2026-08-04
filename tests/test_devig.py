"""Tests du retrait de marge — le module qui décide si un avantage est réel.

C'est le calcul le plus dangereux du système : une méthode inadaptée fabrique
un avantage là où il n'y en a pas. Mesuré sur Celtic – Dundee (bet365
1,20 / 7,50 / 10,00), le proportionnel annonçait 78,1 % pour le favori contre
81,6 % en puissance — soit 5,1 points de faux écart, assez pour déclencher une
mise sur du vide.
"""
from __future__ import annotations

import pytest

from sportsbet import devig as D

#: Cotes réelles bet365 relevées le 03/08/2026 sur Celtic – Dundee.
CELTIC = [1.20, 7.50, 10.00]
#: Marché équilibré à deux issues.
BTTS = [1.80, 1.95]


# ── Marge ────────────────────────────────────────────────────────────────────

def test_marge_positive_sur_un_marche_reel():
    assert D.overround(CELTIC) == pytest.approx(0.0667, abs=1e-4)


def test_marge_nulle_sur_un_marche_juste():
    assert D.overround([2.0, 2.0]) == pytest.approx(0.0, abs=1e-12)


def test_probabilites_brutes():
    assert D.raw_probs([2.0, 4.0]) == [0.5, 0.25]
    assert D.raw_probs([0.0])[0] == 0.0        # cote invalide, pas de division par zéro


# ── Les trois méthodes somment à 1 ───────────────────────────────────────────

@pytest.mark.parametrize("methode", ["multiplicative", "power", "shin"])
@pytest.mark.parametrize("cotes", [CELTIC, BTTS, [2.10, 3.40, 3.60], [1.05, 15.0, 30.0]])
def test_partition_vaut_un(methode, cotes):
    assert sum(D.devig(cotes, methode)) == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("methode", ["multiplicative", "power", "shin"])
def test_probabilites_dans_les_bornes(methode):
    assert all(0.0 < p < 1.0 for p in D.devig(CELTIC, methode))


# ── Le cœur : le proportionnel sous-estime le favori ─────────────────────────

def test_proportionnel_sous_estime_le_favori():
    """Le biais favori-outsider : le bookmaker charge plus de marge sur les
    cotes élevées. Ignorer cela fabrique de l'avantage sur les favoris."""
    prop = D.multiplicative(CELTIC)[0]
    pow_ = D.power(CELTIC)[0]
    assert prop < pow_
    assert (pow_ - prop) * 100 > 3          # l'écart dépasse 3 points, il compte


def test_shin_entre_les_deux():
    prop, sh, pw = (m(CELTIC)[0] for m in (D.multiplicative, D.shin, D.power))
    assert prop < sh < pw


def test_les_methodes_convergent_sur_deux_issues_equilibrees():
    """À deux issues de cotes voisines, le biais disparaît : les trois méthodes
    doivent donner presque la même chose. Sinon, l'une d'elles est fausse."""
    v = [m(BTTS)[0] for m in (D.multiplicative, D.power, D.shin)]
    assert max(v) - min(v) < 0.005


def test_ordre_des_issues_preserve():
    """Le favori reste le favori, quelle que soit la méthode."""
    for m in (D.multiplicative, D.power, D.shin):
        p = m(CELTIC)
        assert p[0] > p[1] > p[2]


# ── Robustesse ───────────────────────────────────────────────────────────────

def test_marche_deja_juste_inchange():
    """Sans marge à retirer, il n'y a rien à corriger."""
    assert D.power([2.0, 2.0]) == pytest.approx([0.5, 0.5])
    assert D.shin([2.0, 2.0]) == pytest.approx([0.5, 0.5])


def test_methode_inconnue_retombe_sur_puissance():
    assert D.devig(CELTIC, "n_importe_quoi") == pytest.approx(D.power(CELTIC))


def test_defaut_est_puissance():
    assert D.DEFAULT == "power"
    assert D.devig(CELTIC) == pytest.approx(D.power(CELTIC))


def test_forte_marge_supportee():
    """Certains petits championnats affichent 15 % de marge."""
    grosse = [1.60, 3.20, 4.00]
    assert D.overround(grosse) > 0.10
    assert sum(D.power(grosse)) == pytest.approx(1.0, abs=1e-6)


def test_comparaison_expose_les_trois():
    c = D.compare_methods(CELTIC)
    assert set(c) == {"multiplicative", "power", "shin"}
    assert all(len(v) == 3 for v in c.values())


def test_ecart_entre_methodes_est_l_incertitude():
    """Un avantage qui n'existe QUE dans une méthode n'existe pas.
    Sur ce marché, l'écart entre méthodes atteint plusieurs points : toute
    conclusion sous ce seuil est du bruit de calcul."""
    c = D.compare_methods(CELTIC)
    favori = [v[0] for v in c.values()]
    assert (max(favori) - min(favori)) * 100 > 3
