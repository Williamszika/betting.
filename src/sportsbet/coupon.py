"""Construction de coupon combiné visant une cote cible (ex. 5.0).

Objectif : parmi les sélections candidates, choisir la combinaison dont la cote
totale atteint la cible tout en MAXIMISANT la probabilité conjointe estimée
(donc le coupon « le plus sûr » qui atteint la cote demandée). On préfère aussi
moins de jambes (chaque jambe supplémentaire ajoute du risque).

Rappel honnête : « plus sûr » n'est pas « sûr ». Un combiné multiplie les
risques — il suffit qu'UNE jambe tombe pour tout perdre.
"""
from __future__ import annotations

from itertools import combinations
from math import prod
from typing import Optional, Sequence

from .models import Coupon, Selection


def _match_key(s: Selection) -> str:
    return s.match.match_id or s.match.label()


def _distinct_matches(combo: Sequence[Selection]) -> bool:
    """True si toutes les jambes portent sur des matchs différents.

    On refuse deux jambes du même match dans un coupon : elles sont corrélées,
    ce qui casse l'hypothèse d'indépendance de la probabilité conjointe.
    """
    keys = [_match_key(s) for s in combo]
    return len(keys) == len(set(keys))


def build_coupon(
    selections: Sequence[Selection],
    target_odds: float = 5.0,
    max_total_odds: Optional[float] = None,
    max_legs: int = 6,
    min_legs: int = 1,
    min_edge: Optional[float] = None,
    pool_size: int = 20,
) -> Optional[Coupon]:
    """Construit le coupon le plus probable dans la fourchette de cote visée.

    Args:
        selections: sélections candidates (une ou plusieurs par match).
        target_odds: cote totale minimale visée (ex. 5.0).
        max_total_odds: cote totale MAXIMALE (ex. 7.0). None = pas de plafond.
            Utile pour un pari simple « cote ~5-7 » sans dérive vers des cotes
            extrêmes.
        max_legs: nombre maximum de jambes.
        min_legs: nombre minimum de jambes. Mettre >= 2 pour forcer un vrai
            combiné plutôt qu'un pari simple à cote élevée.
        min_edge: si fourni, ne garde que les sélections de value >= min_edge.
        pool_size: on ne combine que les `pool_size` sélections les plus
            probables (borne l'explosion combinatoire).

    Returns:
        Le meilleur Coupon trouvé, ou None si aucune combinaison n'atteint la
        cible.
    """
    pool = list(selections)
    if min_edge is not None:
        pool = [s for s in pool if s.edge >= min_edge]
    # On privilégie les sélections les plus probables (les « plus sûres »).
    pool.sort(key=lambda s: s.model_prob, reverse=True)
    pool = pool[:pool_size]

    best: Optional[tuple[Selection, ...]] = None
    best_key: tuple = ()

    for r in range(max(1, min_legs), max_legs + 1):
        for combo in combinations(pool, r):
            if not _distinct_matches(combo):
                continue  # pas deux jambes du même match
            total = prod(s.decimal_odds for s in combo)
            if total < target_odds:
                continue
            if max_total_odds is not None and total > max_total_odds:
                continue
            joint = prod(s.model_prob for s in combo)
            # Maximiser proba conjointe, puis préférer moins de jambes,
            # puis cote totale la plus proche de la cible (moins de surplus).
            key = (joint, -r, -(total - target_odds))
            if best is None or key > best_key:
                best, best_key = combo, key

    return Coupon(list(best)) if best else None


def build_multiple_coupons(
    selections: Sequence[Selection],
    n: int = 5,
    target_odds: float = 5.0,
    max_total_odds: Optional[float] = None,
    max_legs: int = 4,
    min_legs: int = 1,
    min_edge: Optional[float] = None,
) -> list[Coupon]:
    """Construit jusqu'à `n` coupons distincts (ex. 5 coupons du jour).

    Approche gloutonne : on construit un coupon, on retire ses matchs du pool,
    puis on recommence — pour que les coupons ne partagent pas de match.
    """
    remaining = list(selections)
    coupons: list[Coupon] = []
    for _ in range(n):
        c = build_coupon(remaining, target_odds=target_odds,
                         max_total_odds=max_total_odds,
                         max_legs=max_legs, min_legs=min_legs, min_edge=min_edge)
        if c is None or not c.selections:
            break
        coupons.append(c)
        used = {s.match.match_id or s.match.label() for s in c.selections}
        remaining = [s for s in remaining
                     if (s.match.match_id or s.match.label()) not in used]
    return coupons
