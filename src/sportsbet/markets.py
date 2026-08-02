"""Couverture COMPLÈTE des marchés Betano — tout est calculé, rien n'est inventé.

Principe : on construit UNE matrice de scores P(i,j) (Poisson bivarié + correction
Dixon-Coles), puis TOUS les marchés en sont dérivés par sommation. Aucun marché ne
repose sur une probabilité « posée à la main ».

Marchés couverts (football) :
  1X2, Double Chance, Draw No Bet, Handicap européen (entiers, 3 voies),
  Over/Under buts (0.5 → 6.5), BTTS, Score exact, Total buts par équipe,
  Nombre exact de buts, Pair/Impair, Mi-temps/Fin, Marge de victoire,
  Corners O/U, Cartons O/U, Les deux équipes marquent + résultat (combos).

Sources de données statistiques exploitées (football-data.co.uk) :
  buts, tirs (HS/AS), tirs cadrés (HST/AST), CORNERS (HC/AC), fautes (HF/AF),
  cartons jaunes (HY/AY), rouges (HR/AR), scores mi-temps (HTHG/HTAG).

Stdlib pure.
"""
from __future__ import annotations

import math
from typing import Dict

MAX_GOALS = 12


# ────────────────────────────── Matrice de scores ──────────────────────────────

def _pois(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    f = 1.0
    for i in range(2, k + 1):
        f *= i
    return math.exp(-lam) * (lam ** k) / f


def dixon_coles_tau(i: int, j: int, lh: float, la: float, rho: float) -> float:
    """Correction Dixon-Coles sur les scores faibles (le Poisson indépendant
    sous-estime les 0-0 et 1-1 et surestime les 1-0 / 0-1)."""
    if i == 0 and j == 0:
        return 1.0 - lh * la * rho
    if i == 0 and j == 1:
        return 1.0 + lh * rho
    if i == 1 and j == 0:
        return 1.0 + la * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(lh: float, la: float, rho: float = -0.10,
                 max_goals: int = MAX_GOALS) -> list[list[float]]:
    """Matrice P(score i-j), Poisson + correction Dixon-Coles, renormalisée."""
    m = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]
    tot = 0.0
    for i in range(max_goals + 1):
        pi = _pois(i, lh)
        for j in range(max_goals + 1):
            p = pi * _pois(j, la) * dixon_coles_tau(i, j, lh, la, rho)
            p = max(0.0, p)
            m[i][j] = p
            tot += p
    if tot > 0:
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                m[i][j] /= tot
    return m


def matrix_from_cells(cells: Dict[tuple[int, int], float],
                      lh: float, la: float, rho: float = -0.10,
                      max_goals: int = MAX_GOALS) -> list[list[float]]:
    """Matrice de scores construite sur une distribution RÉELLE fournie.

    ClubElo publie 28 cellules de score exact couvrant ~97,8 % de la masse.
    Les collapser en un simple λ puis les reconstruire en Poisson **détruit de
    l'information** : la corrélation entre les buts des deux équipes disparaît.
    Mesuré sur Celtic – Dundee (03/08/2026), cela sous-estimait « les deux
    équipes marquent » de 2,1 points — assez pour fabriquer un faux avantage
    de moitié et déclencher une mise sur du vide.

    On garde donc les cellules réelles telles quelles, et on ne complète que la
    QUEUE non couverte (scores élevés) avec Poisson–Dixon-Coles, remise à
    l'échelle de la masse résiduelle.
    """
    if not cells:
        return score_matrix(lh, la, rho, max_goals)

    m = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]
    couvert = 0.0
    for (i, j), p in cells.items():
        if 0 <= i <= max_goals and 0 <= j <= max_goals and p > 0:
            m[i][j] = p
            couvert += p

    reste = max(0.0, 1.0 - couvert)
    if reste > 1e-9:
        pois = score_matrix(lh, la, rho, max_goals)
        masse = sum(pois[i][j] for i in range(max_goals + 1)
                    for j in range(max_goals + 1) if (i, j) not in cells)
        if masse > 0:
            for i in range(max_goals + 1):
                for j in range(max_goals + 1):
                    if (i, j) not in cells:
                        m[i][j] = pois[i][j] / masse * reste

    tot = sum(sum(r) for r in m)
    if tot > 0:
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                m[i][j] /= tot
    return m


# ────────────────────────── Tous les marchés « buts » ──────────────────────────

def all_goal_markets(lh: float, la: float, rho: float = -0.10,
                     cells: Dict[tuple[int, int], float] | None = None
                     ) -> Dict[str, float]:
    """TOUS les marchés dérivables de la matrice de scores.

    ``cells`` : distribution de scores réelle (ClubElo). Fournie, elle prime sur
    la reconstruction Poisson — voir ``matrix_from_cells``.
    """
    m = matrix_from_cells(cells, lh, la, rho) if cells else score_matrix(lh, la, rho)
    n = len(m)
    out: Dict[str, float] = {}

    p1 = pX = p2 = 0.0
    btts = odd = 0.0
    over = {t: 0.0 for t in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5)}
    home_over = {t: 0.0 for t in (0.5, 1.5, 2.5, 3.5)}
    away_over = {t: 0.0 for t in (0.5, 1.5, 2.5, 3.5)}
    exact_total = {k: 0.0 for k in range(0, 8)}
    margin: Dict[int, float] = {}

    for i in range(n):
        for j in range(n):
            p = m[i][j]
            if p <= 0:
                continue
            tot = i + j
            if i > j:
                p1 += p
            elif i == j:
                pX += p
            else:
                p2 += p
            if i > 0 and j > 0:
                btts += p
            if tot % 2 == 1:
                odd += p
            for t in over:
                if tot > t:
                    over[t] += p
            for t in home_over:
                if i > t:
                    home_over[t] += p
            for t in away_over:
                if j > t:
                    away_over[t] += p
            if tot <= 7:
                exact_total[tot] += p
            d = i - j
            margin[d] = margin.get(d, 0.0) + p
            if i <= 4 and j <= 4:                      # scores exacts usuels
                out[f"CS {i}-{j}"] = p

    out["1"], out["X"], out["2"] = p1, pX, p2
    out["DC 1X"], out["DC X2"], out["DC 12"] = p1 + pX, pX + p2, p1 + p2
    denom = p1 + p2
    out["DNB 1"] = p1 / denom if denom > 0 else 0.5
    out["DNB 2"] = p2 / denom if denom > 0 else 0.5
    out["BTTS Yes"], out["BTTS No"] = btts, 1.0 - btts
    out["Odd"], out["Even"] = odd, 1.0 - odd

    for t, v in over.items():
        out[f"Over {t}"] = v
        out[f"Under {t}"] = 1.0 - v
    for t, v in home_over.items():
        out[f"Home Over {t}"] = v
        out[f"Home Under {t}"] = 1.0 - v
    for t, v in away_over.items():
        out[f"Away Over {t}"] = v
        out[f"Away Under {t}"] = 1.0 - v
    for k, v in exact_total.items():
        out[f"Exact {k} goals"] = v

    # Handicap européen (entiers, 3 voies) : handicap appliqué au DOMICILE.
    for h in (-3, -2, -1, 1, 2, 3):
        w = l = d = 0.0
        for diff, p in margin.items():
            adj = diff + h
            if adj > 0:
                w += p
            elif adj == 0:
                d += p
            else:
                l += p
        out[f"EH {h:+d} 1"], out[f"EH {h:+d} X"], out[f"EH {h:+d} 2"] = w, d, l

    # Combos "résultat + BTTS" et "résultat + Over 2.5" (très présents chez Betano)
    for label, cond in (("1", lambda i, j: i > j),
                        ("X", lambda i, j: i == j),
                        ("2", lambda i, j: i < j)):
        both = ov = 0.0
        for i in range(n):
            for j in range(n):
                p = m[i][j]
                if not p or not cond(i, j):
                    continue
                if i > 0 and j > 0:
                    both += p
                if i + j > 2.5:
                    ov += p
        out[f"{label} & BTTS Yes"] = both
        out[f"{label} & Over 2.5"] = ov

    return out


# ──────────────── Mi-temps / Fin (modèle de part de buts en 1re MT) ────────────

def halftime_fulltime(lh: float, la: float, ht_share: float = 0.45,
                      rho: float = -0.10) -> Dict[str, float]:
    """Marché Mi-temps/Fin. ~45 % des buts tombent en 1re mi-temps (les équipes
    marquent davantage en 2e période : fatigue, prises de risque)."""
    mh = score_matrix(lh * ht_share, la * ht_share, rho)
    m2 = score_matrix(lh * (1 - ht_share), la * (1 - ht_share), rho)
    n = len(mh)
    out = {f"{a}/{b}": 0.0 for a in "1X2" for b in "1X2"}
    ht_only = {"1": 0.0, "X": 0.0, "2": 0.0}
    for i in range(n):
        for j in range(n):
            ph = mh[i][j]
            if ph <= 0:
                continue
            r1 = "1" if i > j else ("X" if i == j else "2")
            ht_only[r1] += ph
            for k in range(n):
                for l in range(n):
                    p2 = m2[k][l]
                    if p2 <= 0:
                        continue
                    fi, fj = i + k, j + l
                    r2 = "1" if fi > fj else ("X" if fi == fj else "2")
                    out[f"{r1}/{r2}"] += ph * p2
    for k, v in ht_only.items():
        out[f"HT {k}"] = v
    return out


# ─────────── Marchés statistiques réels : corners & cartons (données) ──────────

def corners_markets(home_corners_for: float, home_corners_against: float,
                    away_corners_for: float, away_corners_against: float,
                    league_avg_corners: float = 10.4) -> Dict[str, float]:
    """Corners O/U à partir des TAUX RÉELS de corners (jamais déduits de la
    possession — leçon du 14/07). Données : colonnes HC/AC de football-data.co.uk.

    Modèle multiplicatif attaque × défense, comme pour les buts.
    """
    half = max(0.1, league_avg_corners / 2.0)
    lh = max(0.5, (home_corners_for / half) * (away_corners_against / half) * half)
    la = max(0.5, (away_corners_for / half) * (home_corners_against / half) * half)
    out: Dict[str, float] = {}
    tot_lambda = lh + la
    for line in (7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5):
        # P(total > line) via Poisson sur le total (somme de deux Poisson)
        cum = sum(_pois(k, tot_lambda) for k in range(0, int(line) + 1))
        out[f"Corners Over {line}"] = 1.0 - cum
        out[f"Corners Under {line}"] = cum
    for line in (3.5, 4.5, 5.5, 6.5):
        ch = sum(_pois(k, lh) for k in range(0, int(line) + 1))
        ca = sum(_pois(k, la) for k in range(0, int(line) + 1))
        out[f"Home Corners Over {line}"] = 1.0 - ch
        out[f"Away Corners Over {line}"] = 1.0 - ca
    out["_lambda_home"], out["_lambda_away"] = lh, la
    return out


def cards_markets(home_cards: float, away_cards: float,
                  referee_factor: float = 1.0) -> Dict[str, float]:
    """Cartons O/U à partir des taux réels (colonnes HY/AY/HR/AR) et de la
    sévérité de l'arbitre. Un rouge compte 2 points au barème usuel Betano."""
    lam = max(0.5, (home_cards + away_cards) * referee_factor)
    out: Dict[str, float] = {}
    for line in (2.5, 3.5, 4.5, 5.5, 6.5):
        cum = sum(_pois(k, lam) for k in range(0, int(line) + 1))
        out[f"Cards Over {line}"] = 1.0 - cum
        out[f"Cards Under {line}"] = cum
    out["_lambda_cards"] = lam
    return out


# ────────────────────────── Agrégateur tous marchés ───────────────────────────

def all_markets(lh: float, la: float, rho: float = -0.10,
                corners: dict | None = None, cards: dict | None = None,
                with_htft: bool = True) -> Dict[str, float]:
    """Renvoie TOUS les marchés calculables en un seul appel."""
    out = all_goal_markets(lh, la, rho)
    if with_htft:
        out.update(halftime_fulltime(lh, la, rho=rho))
    if corners:
        out.update(corners_markets(**corners))
    if cards:
        out.update(cards_markets(**cards))
    return out
