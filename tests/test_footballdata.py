"""Tests du lecteur football-data.co.uk (parsing pur, hors réseau)."""
from __future__ import annotations

import pytest

from sportsbet import footballdata as FD

# Deux lignes réelles, l'une de chaque format.
CSV_PRINCIPAL = (
    "Div,Date,Time,HomeTeam,AwayTeam,Referee,"
    "B365H,B365D,B365A,BFDH,BFDD,BFDA,MaxH,MaxD,MaxA\n"
    "SC0,03/08/2026,19:30,Celtic,Dundee FC,M MacDermid,"
    "1.17,7.5,10,1.2,7,13,1.22,7.5,13.5\n"
)
CSV_AUTRES = (
    "Country,League,Date,Time,Home,Away,PSH,PSD,PSA,MaxH,MaxD,MaxA,"
    "AvgH,AvgD,AvgA,B365H,B365D,B365A\n"
    "Romania,Superliga,08/08/2026,21:30,Dinamo Bucuresti,Voluntari,"
    "1.80,3.60,4.50,1.85,3.75,4.70,1.78,3.55,4.40,1.82,3.75,4.40\n"
)


# ── Lecture ──────────────────────────────────────────────────────────────────

def test_lit_le_format_principal():
    f = FD.parse(CSV_PRINCIPAL)[0]
    assert f.domicile == "Celtic" and f.exterieur == "Dundee FC"
    assert f.date == "2026-08-03" and f.heure == "19:30"
    assert f.pays == "Écosse"                      # SC0 traduit


def test_lit_le_format_autres_championnats():
    f = FD.parse(CSV_AUTRES)[0]
    assert f.pays == "Romania" and f.ligue == "Superliga"
    assert f.date == "2026-08-08"
    assert "pinnacle" in f.cotes and f.cotes["pinnacle"] == (1.80, 3.60, 4.50)


def test_date_convertie_et_formats_invalides_ignores():
    assert FD._date_iso("03/08/2026") == "2026-08-03"
    assert FD._date_iso("2026-08-03") == ""
    assert FD._date_iso("") == ""
    assert FD._date_iso("32/13/2026") == ""


def test_ligne_sans_equipes_ignoree():
    assert FD.parse("Div,Date,HomeTeam,AwayTeam\nSC0,03/08/2026,,\n") == []


def test_cote_manquante_ou_invalide_ecartee():
    csv = ("Country,League,Date,Time,Home,Away,PSH,PSD,PSA\n"
           "Romania,L1,08/08/2026,20:00,A,B,,,\n")
    assert FD.parse(csv)[0].cotes == {}


# ── Référence de marché ──────────────────────────────────────────────────────

def test_pinnacle_prioritaire_comme_reference():
    """Pinnacle a la marge la plus faible : c'est la référence la moins déformée."""
    f = FD.parse(CSV_AUTRES)[0]
    assert f.reference()[0] == "pinnacle"
    assert f.market_1x2()["source"] == "pinnacle"


def test_marche_1x2_somme_a_un():
    m = FD.parse(CSV_AUTRES)[0].market_1x2()
    assert m["1"] + m["X"] + m["2"] == pytest.approx(1.0, abs=1e-6)


def test_marge_calculee_et_positive():
    m = FD.parse(CSV_AUTRES)[0].market_1x2()
    assert 0.0 < m["marge"] < 0.20


def test_source_explicite_respectee():
    f = FD.parse(CSV_AUTRES)[0]
    assert f.market_1x2(source="b365")["source"] == "b365"


def test_pas_de_marche_sans_cote():
    f = FD.Fixture("X", "Y", "2026-08-08", "20:00", "A", "B", {})
    assert f.market_1x2() is None and f.reference() is None


def test_meilleure_cote_retient_le_maximum():
    """Parier au prix moyen quand une meilleure cote existe jette l'avantage."""
    f = FD.parse(CSV_PRINCIPAL)[0]
    cote, _ = f.meilleure_cote("2")
    assert cote == 13.5                       # Max bat B365 (10) et Betfair (13)


def test_meilleure_cote_issue_inconnue():
    assert FD.parse(CSV_PRINCIPAL)[0].meilleure_cote("Z") is None


# ── Rapprochement des noms ───────────────────────────────────────────────────

def test_rapproche_malgre_le_suffixe_fc():
    fx = FD.parse(CSV_PRINCIPAL)
    assert FD.rapprocher("Celtic", "Dundee", fx) is not None


def test_alias_noms_historiques():
    """ClubElo dit « Steaua » et « Viitorul » ; le marché dit FCSB et Farul."""
    assert FD._norm("Steaua") == "fcsb"
    assert FD._norm("Viitorul") == "farul"


def test_ne_rapproche_pas_deux_matchs_differents():
    fx = FD.parse(CSV_PRINCIPAL)
    assert FD.rapprocher("Rangers", "Aberdeen", fx) is None


def test_rapprochement_insensible_a_la_ponctuation():
    csv = CSV_PRINCIPAL.replace("Dundee FC", "Queen's Park")
    assert FD.rapprocher("Celtic", "Queens Park", FD.parse(csv)) is not None
