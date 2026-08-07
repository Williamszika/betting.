"""Mélange modèle / marché — l'humilité statistique, codée.

Le banc d'essai a mesuré ceci sur 11 championnats et 14 452 paris hors
échantillon :

    erreur de calibration sur TOUTES les prédictions      0,8 point
    erreur sur les paris SÉLECTIONNÉS                    ~12 points

Le modèle est excellent tant qu'on ne lui demande pas de choisir. Dès qu'il
s'écarte assez du marché pour déclencher un pari, il a tort. Cet écart de
11 points est l'avantage informationnel du marché — mesuré, pas supposé.

La réponse n'est pas de mieux régler le modèle : c'est de **l'ancrer sur le
marché** d'autant plus fort que nos données sont minces. Quand on sait peu, le
marché sait mieux.

    p_finale = w × p_modèle + (1 − w) × p_marché

Le poids w n'est pas un réglage arbitraire : il dépend de ce qu'on sait
réellement du match. Championnat bien couvert, historique complet, actualité
vérifiée → w monte. Ligue exotique aux données minces → w s'effondre et le
marché reprend la main.

Stdlib pure.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Poids maximal accordé au modèle, même dans les meilleures conditions.
#: Au-delà, on prétendrait en savoir plus que l'ensemble des parieurs
#: professionnels — ce que rien dans nos mesures ne justifie.
POIDS_MAX = 0.50

#: Poids plancher : en dessous, autant ne pas avoir de modèle du tout.
POIDS_MIN = 0.15


@dataclass
class Fiabilite:
    """Ce qu'on sait vraiment de ce match. Chaque critère est vérifiable."""
    matchs_historique: int = 0        # matchs joués par la moins fournie des deux équipes
    a_xg: bool = False                # xG réels disponibles (5 grands championnats)
    actualite_verifiee: bool = False  # compos, absences, enjeu — datés et sourcés
    ligue_majeure: bool = False       # championnat dense en données

    def poids(self) -> float:
        """Poids à accorder au MODÈLE. Le reste va au marché."""
        # Base : la quantité d'historique. 10 matchs = plein régime.
        w = POIDS_MIN + (POIDS_MAX - POIDS_MIN) * min(1.0, self.matchs_historique / 10.0)
        # Les xG réels prédisent mieux que les buts : ils valent une prime.
        if not self.a_xg:
            w *= 0.80
        # Sans actualité vérifiée, on ignore les absences — le marché, lui, les
        # connaît. C'est exactement le cas FCSB : 7 points d'écart qui ne
        # mesuraient que notre retard d'information.
        if not self.actualite_verifiee:
            w *= 0.70
        if not self.ligue_majeure:
            w *= 0.85
        return max(POIDS_MIN, min(POIDS_MAX, w))

    def explication(self) -> str:
        m = []
        m.append(f"{self.matchs_historique} matchs d'historique")
        m.append("xG réels" if self.a_xg else "pas de xG (proxy tirs cadrés)")
        m.append("actualité vérifiée" if self.actualite_verifiee else "actualité NON vérifiée")
        m.append("championnat majeur" if self.ligue_majeure else "championnat secondaire")
        return " · ".join(m)


def melanger(p_modele: float, p_marche: float, poids: float) -> float:
    """Mélange linéaire, borné aux probabilités valides."""
    p = poids * p_modele + (1.0 - poids) * p_marche
    return max(0.0, min(1.0, p))


def melanger_1x2(modele: dict, marche: dict, poids: float) -> dict:
    """Mélange les trois issues PUIS renormalise.

    Sans renormalisation, deux distributions valides mélangées peuvent ne plus
    sommer à 1 dès que l'une est tronquée — et un marché dont la somme dérive
    fabrique de l'avantage sur l'issue la plus mal estimée.
    """
    out = {k: melanger(modele.get(k, 0.0), marche.get(k, 0.0), poids)
           for k in ("1", "X", "2")}
    s = sum(out.values())
    return {k: v / s for k, v in out.items()} if s > 0 else out


# ── Ajustements textuels bornés ──────────────────────────────────────────────

#: Plafond absolu d'un ajustement issu du contexte, en proportion de λ.
#: Un agent enthousiaste transformerait « trois absents » en −40 % ; la
#: littérature ne justifie rien de tel. L'agent propose, le code borne.
PLAFOND_AJUSTEMENT = 0.15

#: Effet unitaire par catégorie de fait, avant plafonnement global.
EFFETS = {
    "buteur_principal_absent": -0.10,
    "titulaire_majeur_absent": -0.04,
    "gardien_titulaire_absent": -0.03,     # sur λ adverse, en négatif
    "rotation_annoncee": -0.06,
    "match_a_haute_charge": -0.03,          # 3 matchs en 8 jours
}


def ajustement(faits: list[str], plafond: float = PLAFOND_AJUSTEMENT) -> float:
    """Multiplicateur de λ issu des faits textuels, strictement borné.

    Rend un facteur dans [1 − plafond, 1 + plafond]. Les faits inconnus sont
    ignorés : un agent ne peut pas inventer une catégorie d'effet.
    """
    total = sum(EFFETS.get(f, 0.0) for f in faits)
    total = max(-plafond, min(plafond, total))
    return 1.0 + total
