"""Pool d'agents de recherche concurrent.

L'idée « 500+ agents » est ici un POOL à concurrence bornée : on peut soumettre
des centaines de tâches de recherche, mais seules `max_workers` s'exécutent en
même temps. C'est ce qu'il faut faire en pratique :

  - lancer 500 scrapers *simultanés* sature les sites, se fait bannir, et coûte
    cher pour rien ;
  - la qualité d'une prédiction vient des DONNÉES et des MODÈLES, pas du nombre
    de robots.

Donc on parallélise raisonnablement (I/O réseau) tout en restant courtois.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def run_pool(
    items: Iterable[T],
    worker: Callable[[T], R],
    max_workers: int = 12,
    on_error: str = "skip",
) -> List[R]:
    """Exécute `worker` sur chaque item en parallèle (bornée à max_workers).

    Args:
        items: éléments à traiter (ex. matchs).
        worker: fonction appliquée à chaque item.
        max_workers: concurrence maximale (défaut 12 — raisonnable et courtois).
        on_error: "skip" ignore les tâches en échec, "raise" propage.

    Returns:
        Liste des résultats non-nuls, dans l'ordre d'achèvement.
    """
    items = list(items)
    results: List[R] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(worker, it): it for it in items}
        for fut in as_completed(futures):
            try:
                res = fut.result()
            except Exception:
                if on_error == "raise":
                    raise
                continue
            if res is not None:
                results.append(res)
    return results
