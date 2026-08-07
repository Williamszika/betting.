"""Opérateurs allemands : régime fiscal, marge, et ce qu'ils font des gagnants.

La différence entre deux bookmakers ne se joue pas sur les cotes affichées mais
sur **qui paie la taxe de 5,3 %**. Betano la répercute, bet365 l'absorbe depuis
janvier 2024. Sur une cote à 1,76, cela déplace le seuil de rentabilité de 1,85
à 1,76 — soit la moitié de l'écart à créer. C'est le plus gros levier gratuit
du marché allemand.

Le second facteur, jamais annoncé : la **limitation**. Un compte qui gagne est
restreint. Ce n'est pas un accident, c'est le modèle économique des « square
books ». Toute stratégie qui fonctionne a donc une durée de vie finie.

Stdlib pure.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bankroll import min_odds_for_breakeven


@dataclass(frozen=True)
class Book:
    """Un opérateur, avec ce qui détermine réellement la rentabilité."""
    key: str
    name: str
    tax_mode: str          # "none" = absorbe la taxe | "gross" = la répercute
    margin: float          # marge typique sur le football (1X2)
    ggl: bool              # présent sur la whitelist GGL (légal en Allemagne)
    min_stake: float
    limits: str            # politique de limitation observée
    note: str


#: Marges : bet365 94–96 % de retour sur le football, Betano ~4–5 % sur 1X2.
#: Les petits opérateurs absorbent la taxe pour recruter, mais leur marge est
#: mal documentée et leur présence sur la whitelist GGL reste À VÉRIFIER.
BOOKS: dict[str, Book] = {
    "bet365": Book(
        "bet365", "bet365", "none", 0.050, True, 0.10,
        "limite les marchés puis le compte entier",
        "absorbe la taxe depuis janvier 2024 — seuil de rentabilité = cote juste"),
    "betano": Book(
        "betano", "Betano.de", "gross", 0.045, True, 0.20,
        "limitation signalée sur les comptes gagnants",
        "répercute la taxe : il faut créer 5,6 % d'écart EN PLUS de la marge"),
    "tipico": Book(
        "tipico", "Tipico", "gross", 0.055, True, 0.10,
        "limites à 2–5 € par pari, sans préavis",
        "limitation la plus agressive du marché allemand"),
    "interwetten": Book(
        "interwetten", "Interwetten", "gross", 0.050, True, 0.20,
        "limitation modérée", "opérateur historique, licence GGL"),
    "scored": Book(
        "scored", "Scored", "none", 0.060, False, 0.20,
        "inconnue", "absorbe la taxe — licence GGL À VÉRIFIER avant tout dépôt"),
    "betovo": Book(
        "betovo", "Betovo", "none", 0.060, False, 0.20,
        "inconnue", "absorbe la taxe — licence GGL À VÉRIFIER avant tout dépôt"),
}

DEFAULT_BOOK = "bet365"


def get(key: str) -> Book:
    return BOOKS.get(key.lower(), BOOKS[DEFAULT_BOOK])


def min_odds(prob: float, book: str = DEFAULT_BOOK) -> float:
    """Cote AFFICHÉE minimale pour ne pas être perdant chez cet opérateur."""
    return min_odds_for_breakeven(prob, get(book).tax_mode)


def expected_odds(prob: float, book: str = DEFAULT_BOOK) -> float:
    """Cote que cet opérateur affichera VRAISEMBLABLEMENT si son prix est juste.

    Estimation à partir de la marge typique — sert à savoir s'il vaut la peine
    d'aller relever la cote, PAS à décider d'une mise. Une mise se décide
    toujours sur une cote réellement observée.
    """
    if prob <= 0:
        return 0.0
    return (1.0 / prob) * (1.0 - get(book).margin)


def required_gap(prob: float, book: str = DEFAULT_BOOK) -> float:
    """Écart à créer face au marché pour être rentable, en points de probabilité.

    C'est LA question : de combien notre probabilité doit-elle dépasser celle du
    marché pour que le pari devienne gagnant chez cet opérateur ? Réponse en
    points (0.05 = 5 points de probabilité).
    """
    mo = min_odds(prob, book)
    if mo <= 0 or mo == float("inf"):
        return float("inf")
    # Probabilité qu'il faudrait pour que la cote AFFICHÉE atteigne le seuil.
    b = get(book)
    p_affichee = (1.0 - b.margin) / mo      # proba implicite de la cote offerte
    return prob - p_affichee


def compare(prob: float, books: list[str] | None = None) -> list[dict]:
    """Classe les opérateurs pour une probabilité donnée, du plus au moins exigeant."""
    keys = books or list(BOOKS)
    rows = []
    for k in keys:
        b = get(k)
        rows.append({
            "book": b.name, "key": b.key, "ggl": b.ggl,
            "tax": "absorbée" if b.tax_mode == "none" else "répercutée",
            "min_odds": round(min_odds(prob, k), 2),
            "expected_odds": round(expected_odds(prob, k), 2),
            "gap_needed": round(required_gap(prob, k) * 100, 1),
            "min_stake": b.min_stake, "limits": b.limits,
        })
    return sorted(rows, key=lambda r: r["gap_needed"])
