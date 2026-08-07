"""Tests de la lecture de pages et de l'extraction de cotes (hors réseau)."""
from __future__ import annotations

from sportsbet import fetch as F


# ── Détection de pages bloquées ──────────────────────────────────────────────

def test_page_bloquee_par_portail_age():
    p = F.Page("u", "Verificação de idade obrigatória " + "x" * 900)
    assert p.bloquee and not p.ok


def test_page_bloquee_par_anti_bot():
    p = F.Page("u", "Warning: Target URL returned error 503: Service Unavailable" + "y" * 900)
    assert p.bloquee and not p.ok


def test_page_trop_courte_nest_pas_ok():
    assert not F.Page("u", "trois mots seulement").ok


def test_page_valide():
    p = F.Page("u", "Contenu réel de la page. " * 60, backend="jina")
    assert p.ok and not p.bloquee


# ── Extraction de cotes ──────────────────────────────────────────────────────

def test_extrait_cote_roumaine_avec_bookmaker():
    t = "Pont secundar 2: FCSB înscrie peste 1.5 goluri, cotă 1.79 la Netbet"
    c = F.extraire_cotes(t)
    assert len(c) == 1
    assert c[0].valeur == 1.79
    assert c[0].bookmaker == "netbet"


def test_extrait_cote_allemande():
    c = F.extraire_cotes("Der Sieg von Bayern wird bei Tipico mit Quote 1.45 angeboten")
    assert any(x.valeur == 1.45 and x.bookmaker == "tipico" for x in c)


def test_extrait_cote_anglaise_et_arobase():
    assert any(x.valeur == 2.05 for x in F.extraire_cotes("Celtic to win, odds of 2.05"))
    assert any(x.valeur == 3.40 for x in F.extraire_cotes("Over 2.5 @ 3.40"))


def test_virgule_decimale_acceptee():
    c = F.extraire_cotes("am pariat peste 2,5 goluri, cotă 1,76 la Netbet")
    assert any(x.valeur == 1.76 for x in c)


def test_bookmaker_vide_si_non_nomme():
    c = F.extraire_cotes("Le pari est proposé à la cote 2.10 ce soir")
    assert c and c[0].bookmaker == ""


def test_valeurs_hors_bornes_ignorees():
    """Un score « 1.00 » ou un pourcentage « 99.99 » ne sont pas des cotes."""
    assert not [x for x in F.extraire_cotes("cote 1.00") if x.valeur == 1.00]
    assert not F.extraire_cotes("cotă 0.85")


def test_pas_de_cote_dans_un_texte_neutre():
    assert F.extraire_cotes("Le match aura lieu lundi soir au stade municipal.") == []


def test_doublons_du_meme_contexte_fusionnes():
    """Le même chiffre au même endroit ne doit pas être compté deux fois,
    même s'il est capté par plusieurs motifs de langue."""
    t = "odds of 1.90 " * 1
    assert len(F.extraire_cotes(t)) == 1


def test_deux_cotes_distinctes_conservees():
    t = ("Pont principal: peste 2.5 goluri, cotă 1.76 la Netbet. "
         "Pont secundar: peste 3.5 goluri, cotă 2.90 la Netbet.")
    vals = sorted(x.valeur for x in F.extraire_cotes(t))
    assert vals == [1.76, 2.90]


def test_contexte_conserve_pour_lecture_humaine():
    c = F.extraire_cotes("FCSB înscrie peste 1.5 goluri, cotă 1.79 la Netbet")
    assert "peste 1.5" in c[0].contexte
