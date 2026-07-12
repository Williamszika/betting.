"""Jeu responsable — affiché partout où un pronostic est produit.

Ce module n'est pas décoratif : il encode des règles minimales que l'outil
respecte, et un texte d'avertissement obligatoire.
"""
from __future__ import annotations

DISCLAIMER_FR = (
    "AVERTISSEMENT — Ces pronostics sont des ESTIMATIONS statistiques, pas des "
    "certitudes. Aucun pari n'est « sûr » : vous pouvez tout perdre. Ne misez "
    "que de l'argent que vous pouvez vous permettre de perdre, jamais d'argent "
    "emprunté. Le jeu peut créer une dépendance. Interdit aux moins de 18 ans. "
    "Aide : joueurs-info-service.fr (France) — 09 74 75 13 13."
)


def stake_is_reasonable(stake: float, bankroll: float, max_fraction: float = 0.05) -> bool:
    """Une mise raisonnable ne dépasse pas une petite fraction de la bankroll."""
    if bankroll <= 0:
        return False
    return 0 < stake <= bankroll * max_fraction


def format_with_disclaimer(text: str) -> str:
    bar = "-" * 72
    return f"{text}\n\n{bar}\n{DISCLAIMER_FR}\n{bar}"
