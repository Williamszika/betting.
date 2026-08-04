"""Modèle glissant sans fuite temporelle — forces d'équipes, forme, enjeu.

Chaque prédiction est faite avec les SEULES données disponibles avant le coup
d'envoi. C'est la contrainte qui fait la différence entre un backtest utile et
une illusion : un modèle qui a vu le résultat obtient toujours d'excellents
chiffres et ne rapporte rien en réel.

Ce que le modèle utilise, tout calculé sur la fenêtre passée :

  attaque / défense   buts marqués et encaissés, rapportés à la moyenne de la ligue
  qualité de jeu      tirs cadrés pour et contre — approximation des xG, dont la
                      recherche (Wilkens, 11 saisons de Bundesliga) montre qu'ils
                      captent un signal absent des prix du marché
  avantage du terrain estimé SUR LA LIGUE, pas supposé
  repos               jours depuis le dernier match
  enjeu               position au classement et distance au titre / à la
                      relégation / à l'Europe, au moment du match

Stdlib pure.
"""
from __future__ import annotations

import datetime
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field

#: Fenêtre glissante par équipe (matchs). ~10 = un bon compromis entre
#: réactivité et bruit sur une saison de 34 journées.
FENETRE = 10

#: Poids du proxy xG (tirs cadrés) face aux buts réels. Les buts sont bruités
#: sur 10 matchs ; les tirs cadrés le sont moins et prédisent mieux la suite.
POIDS_XG = 0.5

#: Buts par tir cadré, moyenne du football professionnel. Sert à convertir les
#: tirs cadrés en buts attendus.
BUTS_PAR_TIR_CADRE = 0.31


@dataclass
class FormeEquipe:
    """Historique récent d'une équipe, alimenté match après match."""
    buts_pour: deque = field(default_factory=lambda: deque(maxlen=FENETRE))
    buts_contre: deque = field(default_factory=lambda: deque(maxlen=FENETRE))
    tirs_cadres_pour: deque = field(default_factory=lambda: deque(maxlen=FENETRE))
    tirs_cadres_contre: deque = field(default_factory=lambda: deque(maxlen=FENETRE))
    derniere_date: datetime.date | None = None
    points: int = 0
    joues: int = 0

    @property
    def pret(self) -> bool:
        """Assez d'historique pour prédire ? En dessous, on s'abstient."""
        return len(self.buts_pour) >= 5

    def attaque(self) -> float:
        """Buts attendus marqués par match, buts réels et tirs cadrés mêlés."""
        if not self.buts_pour:
            return 1.35
        reels = sum(self.buts_pour) / len(self.buts_pour)
        if not self.tirs_cadres_pour:
            return reels
        proxy = sum(self.tirs_cadres_pour) / len(self.tirs_cadres_pour) * BUTS_PAR_TIR_CADRE
        return (1 - POIDS_XG) * reels + POIDS_XG * proxy

    def defense(self) -> float:
        if not self.buts_contre:
            return 1.35
        reels = sum(self.buts_contre) / len(self.buts_contre)
        if not self.tirs_cadres_contre:
            return reels
        proxy = sum(self.tirs_cadres_contre) / len(self.tirs_cadres_contre) * BUTS_PAR_TIR_CADRE
        return (1 - POIDS_XG) * reels + POIDS_XG * proxy


@dataclass
class Ligue:
    """État d'un championnat à un instant donné — jamais au-delà."""
    equipes: dict = field(default_factory=lambda: defaultdict(FormeEquipe))
    buts_dom: list = field(default_factory=list)
    buts_ext: list = field(default_factory=list)

    def moyennes(self) -> tuple[float, float]:
        """Buts moyens domicile / extérieur DANS CETTE LIGUE.

        L'avantage du terrain est mesuré, pas supposé : il vaut ~1,45 contre
        ~1,15 en Bundesliga, mais bien moins ailleurs. Le fixer à une constante
        universelle est une erreur silencieuse.
        """
        n = len(self.buts_dom)
        if n < 30:
            return 1.50, 1.20
        return sum(self.buts_dom) / n, sum(self.buts_ext) / n

    def classement(self) -> list[tuple[str, int]]:
        return sorted(((n, f.points) for n, f in self.equipes.items()),
                      key=lambda x: -x[1])


def enjeu(ligue: Ligue, equipe: str, journee_estimee: float) -> dict:
    """Ce qui se joue pour cette équipe, à ce moment de la saison.

    Un match sans enjeu casse les probabilités : l'intensité défensive
    s'effondre et le favori perd son avantage (perte France 6-4). Mais l'enjeu
    n'existe qu'en FIN de saison — en journée 5, tout le monde joue pour
    quelque chose.
    """
    cl = ligue.classement()
    if not cl or journee_estimee < 0.6:
        return {"phase": "saison_ouverte", "position": 0, "sans_enjeu": False}
    noms = [n for n, _ in cl]
    if equipe not in noms:
        return {"phase": "inconnu", "position": 0, "sans_enjeu": False}
    pos = noms.index(equipe) + 1
    n = len(noms)
    pts = dict(cl)[equipe]
    restants = max(0, round((1 - journee_estimee) * (n - 1) * 2))
    max_gain = restants * 3

    titre = pos <= 3 and (cl[0][1] - pts) <= max_gain
    europe = 3 < pos <= 8 and abs(dict(cl)[noms[min(5, n - 1)]] - pts) <= max_gain
    releg = pos > n - 5 and (pts - cl[-1][1]) <= max_gain
    return {
        "phase": "fin_de_saison" if journee_estimee > 0.85 else "seconde_moitie",
        "position": pos,
        "sans_enjeu": journee_estimee > 0.88 and not (titre or europe or releg),
    }


#: Constante de rétrécissement. Sur 10 matchs, la force d'une équipe est
#: mesurée avec un bruit considérable, et un modèle naïf prend ce bruit pour du
#: signal : il annonçait 64,6 % là où la réalité était 50,0 % sur 17 790 paris.
#: On ramène donc chaque force vers la moyenne de la ligue d'un facteur
#: n / (n + K) — pur James-Stein. K = 10 divise l'écart par deux à 10 matchs.
K_RETRECISSEMENT = 10.0


def _retrecir(ratio: float, n: int, k: float = K_RETRECISSEMENT) -> float:
    """Ramène un ratio vers 1 d'autant plus fort que l'échantillon est petit."""
    return 1.0 + (ratio - 1.0) * (n / (n + k))


def lambdas(ligue: Ligue, dom: str, ext: str,
            k: float = K_RETRECISSEMENT) -> tuple[float, float]:
    """λ domicile / extérieur, forces relatives à la ligue et rétrécies.

    λ_dom = attaque(dom) × faiblesse(ext) × moyenne_dom, chaque terme normalisé
    par la moyenne du championnat — une ligue à 3,2 buts et une ligue à 2,3 buts
    ne peuvent pas être traitées pareil.
    """
    a, b = ligue.equipes[dom], ligue.equipes[ext]
    m_dom, m_ext = ligue.moyennes()
    moy = (m_dom + m_ext) / 2 or 1.35
    na, nb = len(a.buts_pour), len(b.buts_pour)

    att_dom = _retrecir(a.attaque() / moy, na, k)
    def_ext = _retrecir(b.defense() / moy, nb, k)
    att_ext = _retrecir(b.attaque() / moy, nb, k)
    def_dom = _retrecir(a.defense() / moy, na, k)

    lh = max(0.15, att_dom * def_ext * m_dom)
    la = max(0.15, att_ext * def_dom * m_ext)
    return lh, la


def jours_de_repos(f: FormeEquipe, date: datetime.date) -> int | None:
    return (date - f.derniere_date).days if f.derniere_date else None


def enregistrer(ligue: Ligue, dom: str, ext: str, bd: int, be: int,
                stats: dict, date: datetime.date) -> None:
    """Intègre un match TERMINÉ. À n'appeler qu'APRÈS avoir prédit."""
    a, b = ligue.equipes[dom], ligue.equipes[ext]
    a.buts_pour.append(bd); a.buts_contre.append(be)
    b.buts_pour.append(be); b.buts_contre.append(bd)
    if "HST" in stats and "AST" in stats:
        a.tirs_cadres_pour.append(stats["HST"]); a.tirs_cadres_contre.append(stats["AST"])
        b.tirs_cadres_pour.append(stats["AST"]); b.tirs_cadres_contre.append(stats["HST"])
    a.derniere_date = b.derniere_date = date
    a.joues += 1; b.joues += 1
    if bd > be:
        a.points += 3
    elif bd == be:
        a.points += 1; b.points += 1
    else:
        b.points += 3
    ligue.buts_dom.append(bd); ligue.buts_ext.append(be)
