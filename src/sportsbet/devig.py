"""Retirer la marge du bookmaker — la méthode change la conclusion.

Un bookmaker n'applique PAS sa marge uniformément. Le biais favori-outsider
(favourite-longshot bias) fait qu'il en charge davantage sur les cotes élevées :
un outsider à 10,00 est surpayé en marge par rapport à un favori à 1,20.

La méthode **proportionnelle** (diviser chaque probabilité brute par leur somme)
ignore ce fait et **sous-estime systématiquement le favori**. Elle fabrique donc
des avantages sur les favoris là où il n'y en a pas — surestimation de l'edge
d'environ 35 % dans la littérature.

Mesuré sur Celtic – Dundee (03/08/2026), bet365 à 1,20 / 7,50 / 10,00 :
  proportionnel → favori 78,1 %  ⇒ écart de 5,1 pts avec ClubElo = faux edge
  puissance     → favori 81,7 %  ⇒ écart de 1,5 pt   = rien à jouer

Stdlib pure.
"""
from __future__ import annotations


def raw_probs(odds: list[float]) -> list[float]:
    return [1.0 / o if o > 0 else 0.0 for o in odds]


def overround(odds: list[float]) -> float:
    """Marge du bookmaker : 0.067 = 6,7 %."""
    return sum(raw_probs(odds)) - 1.0


def multiplicative(odds: list[float]) -> list[float]:
    """Méthode proportionnelle — la plus simple, la plus fausse sur les favoris."""
    p = raw_probs(odds)
    s = sum(p)
    return [x / s for x in p] if s > 0 else p


def power(odds: list[float], tol: float = 1e-10, iters: int = 200) -> list[float]:
    """Méthode puissance : trouve k tel que Σ pᵢᵏ = 1.

    k > 1 comprime les petites probabilités plus que les grandes — ce qui
    reproduit le biais favori-outsider observé chez les bookmakers. C'est la
    méthode à utiliser par défaut sur un marché 1X2.
    """
    p = [x for x in raw_probs(odds) if x > 0]
    if not p or abs(sum(p) - 1.0) < tol:
        return raw_probs(odds)
    lo, hi = 0.5, 5.0
    for _ in range(iters):
        k = (lo + hi) / 2.0
        s = sum(x ** k for x in p)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = k          # somme trop grande → comprimer davantage
        else:
            hi = k
    return [(x ** k) if x > 0 else 0.0 for x in raw_probs(odds)]


def shin(odds: list[float], tol: float = 1e-10, iters: int = 200) -> list[float]:
    """Méthode de Shin : modélise une fraction z de parieurs informés.

    Le bookmaker se protège d'initiés supposés ; z est cette fraction. Donne des
    résultats proches de la méthode puissance, avec une interprétation
    économique explicite. Utile comme second avis.
    """
    p = raw_probs(odds)
    s = sum(p)
    if s <= 1.0 or len(p) < 2:
        return p

    def probs(z: float) -> list[float]:
        out = []
        for x in p:
            disc = z * z + 4.0 * (1.0 - z) * (x * x) / s
            out.append((max(0.0, disc) ** 0.5 - z) / (2.0 * (1.0 - z)))
        return out

    lo, hi = 0.0, 0.5
    for _ in range(iters):
        z = (lo + hi) / 2.0
        t = sum(probs(z))
        if abs(t - 1.0) < tol:
            break
        if t > 1.0:
            lo = z
        else:
            hi = z
    q = probs(z)
    t = sum(q)
    return [x / t for x in q] if t > 0 else q


#: Méthode par défaut. Le proportionnel n'est gardé que pour comparaison.
DEFAULT = "power"

METHODS = {"multiplicative": multiplicative, "power": power, "shin": shin}


def devig(odds: list[float], method: str = DEFAULT) -> list[float]:
    return METHODS.get(method, power)(odds)


def compare_methods(odds: list[float]) -> dict[str, list[float]]:
    """Les trois méthodes côte à côte — l'écart entre elles EST l'incertitude.

    Si un « avantage » n'existe qu'avec la méthode proportionnelle, il n'existe
    pas : c'est un artefact de la façon dont on a retiré la marge.
    """
    return {name: [round(x, 4) for x in fn(odds)] for name, fn in METHODS.items()}
