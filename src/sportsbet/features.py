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
    xg: float = 1.3               # expected goals / match
    xga: float = 1.3              # expected goals against / match
    form_points: float = 7.0      # points sur les 5 derniers (0–15)
    availability: float = 1.0     # 1.0 = effectif complet ; <1 si absents clés
    h2h_score: float = 0.5        # domination H2H vs l'adversaire (0–1)
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
