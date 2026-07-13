"""Ingénierie de features : normalisation + pondération (méthode SportPredix).

On transforme les données brutes de la recherche (buts, xG, forme, absences…)
en **features comparables** (échelle 0–1), puis on les **pondère** selon leur
importance. C'est l'étape « collecter → nettoyer → normaliser → pondérer →
features » décrite dans le projet.

Aucune dépendance externe (stdlib pure) : testable hors-ligne.
"""
from __future__ import annotations

from dataclasses import dataclass


def normalize(value: float, lo: float, hi: float) -> float:
    """Ramène `value` dans [0, 1] par min-max, borné."""
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def weighted_recent(values: list[float], decay: float = 0.85) -> float:
    """Moyenne pondérée exponentiellement vers le PLUS RÉCENT.

    `values` est ordonné ancien -> récent. Le dernier élément a le poids le plus
    fort. Sert au xG GLISSANT (rolling) et à la forme pondérée.
    """
    if not values:
        return 0.0
    n = len(values)
    num = den = 0.0
    for i, v in enumerate(values):
        w = decay ** (n - 1 - i)   # i grand (récent) -> poids ~1
        num += w * v
        den += w
    return num / den if den else 0.0


def weighted_form_points(results: list[str], decay: float = 0.85) -> float:
    """Forme PONDÉRÉE (récent > ancien) ramenée sur /15 (échelle 5 matchs).

    `results` : liste de 'W'/'D'/'L' (ancien -> récent). Compatible avec le champ
    `form_points` (0–15) utilisé partout.
    """
    pts = {"W": 3.0, "D": 1.0, "L": 0.0}
    vals = [pts.get((r or "").strip().upper()[:1], 0.0) for r in results]
    return weighted_recent(vals, decay) * 5.0   # points/match pondérés × 5


# Poids par défaut (repris de la grille SportPredix). Somme = 1.0.
DEFAULT_WEIGHTS = {
    "form": 0.30,          # forme récente
    "attack": 0.25,        # force offensive (buts + xG)
    "availability": 0.20,  # effectif dispo (absences)
    "home": 0.15,          # avantage du terrain
    "h2h": 0.10,           # historique des confrontations
}


@dataclass
class TeamStats:
    """Données brutes d'une équipe (par match), alimentées par la recherche."""
    goals_for: float = 1.3        # buts marqués / match
    goals_against: float = 1.3    # buts encaissés / match
    xg: float = 1.3               # expected goals / match (idéalement GLISSANT/pondéré)
    xga: float = 1.3              # expected goals against / match
    form_points: float = 7.0      # points sur les 5 derniers (0–15, idéalement pondéré)
    availability: float = 1.0     # 1.0 = effectif complet ; <1 si absents clés
    h2h_score: float = 0.5        # domination H2H vs l'adversaire (0–1)
    elo: float = 1500.0           # note ELO (0 ou 1500 = inconnu -> ignoré)
    is_home: bool = False


# --- Features normalisées (0–1) ---

def offensive_strength(s: TeamStats) -> float:
    """Force offensive = mix buts marqués + xG (0–1)."""
    return 0.5 * normalize(s.goals_for, 0.5, 2.5) + 0.5 * normalize(s.xg, 0.5, 2.5)


def defensive_weakness(s: TeamStats) -> float:
    """Faiblesse défensive = mix buts encaissés + xGA (0–1). Plus haut = plus faible."""
    return 0.5 * normalize(s.goals_against, 0.5, 2.5) + 0.5 * normalize(s.xga, 0.5, 2.5)


def form_index(s: TeamStats) -> float:
    """Forme = points sur 5 matchs, normalisée (0–1)."""
    return normalize(s.form_points, 0.0, 15.0)


def team_score(s: TeamStats, opponent: TeamStats, weights: dict | None = None) -> float:
    """Score global pondéré d'une équipe FACE à un adversaire (0–1).

    Combine : forme, force offensive (vs faiblesse défensive adverse),
    disponibilité, avantage terrain, H2H — selon les poids fournis.
    """
    w = weights or DEFAULT_WEIGHTS
    attack_vs_def = 0.5 * offensive_strength(s) + 0.5 * defensive_weakness(opponent)
    home = 1.0 if s.is_home else 0.0
    return (
        w["form"] * form_index(s)
        + w["attack"] * attack_vs_def
        + w["availability"] * s.availability
        + w["home"] * home
        + w["h2h"] * s.h2h_score
    )
