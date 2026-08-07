"""Gestion de bankroll et calcul de mise — Kelly fractionnaire, taxe intégrée.

Le critère de Kelly maximise la croissance géométrique du capital. Il exige la
**vraie** probabilité : surestimer p de 10 % suffit à transformer Kelly en ruine.
On applique donc systématiquement une **fraction** (défaut 1/5) — pratique
standard chez les professionnels, qui divise la volatilité par ~5 en ne coûtant
qu'~20 % de la croissance théorique.

Particularité allemande : Betano **répercute** la taxe de 5,3 % sur les gains.
La cote effectivement touchée est donc inférieure à la cote affichée, et Kelly
doit travailler sur la cote EFFECTIVE, jamais sur l'affichée.

Stdlib pure.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: Taux de la Sportwettensteuer allemande (§ 18 RennwLottG).
TAX_RATE = 0.053

#: Mise minimale acceptée par Betano.de (source : centre d'aide officiel).
MIN_STAKE = 0.20

#: Fraction de Kelly appliquée par défaut (1/5 = prudent).
DEFAULT_KELLY_FRACTION = 0.20


def effective_odds(odds: float, mode: str = "gross") -> float:
    """Cote réellement touchée après répercussion de la taxe.

    - ``gross`` (défaut, conservateur) : 5,3 % prélevés sur le RETOUR TOTAL
      → cote_eff = 0,947 × cote.  Cote 2,00 → 1,894.
    - ``net`` : 5,3 % prélevés sur le GAIN NET seulement
      → cote_eff = 1 + 0,947 × (cote − 1).  Cote 2,00 → 1,947.
    - ``none`` : opérateur qui absorbe la taxe (bet365, Tipico…) → cote inchangée.

    L'assiette exacte de Betano n'est pas confirmée (le centre d'aide dit
    « 5,3 % vom Gewinn ») : on retient ``gross`` par prudence.
    """
    if mode == "none":
        return odds
    if mode == "net":
        return 1.0 + (1.0 - TAX_RATE) * (odds - 1.0)
    return (1.0 - TAX_RATE) * odds


def min_odds_for_breakeven(prob: float, mode: str = "gross") -> float:
    """Cote AFFICHÉE minimale pour que le pari ne soit pas perdant d'avance."""
    if prob <= 0:
        return float("inf")
    if mode == "none":
        return 1.0 / prob
    if mode == "net":
        # 1 + 0.947(o-1) = 1/p  →  o = 1 + (1/p - 1)/0.947
        return 1.0 + (1.0 / prob - 1.0) / (1.0 - TAX_RATE)
    return 1.0 / ((1.0 - TAX_RATE) * prob)


def edge(prob: float, odds: float, mode: str = "gross") -> float:
    """Espérance nette par unité misée : p × cote_effective − 1."""
    return prob * effective_odds(odds, mode) - 1.0


def kelly_fraction(prob: float, odds: float, mode: str = "gross") -> float:
    """Fraction de Kelly PLEINE (0 si pas d'avantage).

    f* = (p·b − q) / b   avec b = cote_effective − 1 (gain net par unité).
    """
    oe = effective_odds(odds, mode)
    b = oe - 1.0
    if b <= 0 or prob <= 0:
        return 0.0
    f = (prob * b - (1.0 - prob)) / b
    return max(0.0, f)


@dataclass
class StakePlan:
    """Décision de mise, entièrement traçable."""
    stake: float                 # mise recommandée (€), 0 = ne pas jouer
    playable: bool               # y a-t-il un avantage exploitable ?
    reason: str                  # pourquoi cette décision
    prob: float = 0.0
    odds: float = 0.0
    eff_odds: float = 0.0
    min_odds: float = 0.0
    edge: float = 0.0
    kelly_full: float = 0.0
    kelly_used: float = 0.0
    bankroll: float = 0.0


def plan_stake(bankroll: float, prob: float, odds: float,
               fraction: float = DEFAULT_KELLY_FRACTION,
               mode: str = "gross",
               max_share: float = 0.05,
               min_edge: float = 0.02) -> StakePlan:
    """Calcule la mise à partir de la bankroll, de la probabilité et de la cote.

    Garde-fous cumulés :
      • edge minimal requis (défaut 2 %) — sous ce seuil, c'est du bruit ;
      • Kelly fractionnaire (défaut 1/5) ;
      • plafond absolu (défaut 5 % de la bankroll) ;
      • mise minimale du bookmaker (0,20 €) : si la mise calculée est inférieure,
        **on ne joue pas** — arrondir vers le haut serait sur-miser.
    """
    oe = effective_odds(odds, mode)
    mo = min_odds_for_breakeven(prob, mode)
    e = edge(prob, odds, mode)
    kf = kelly_fraction(prob, odds, mode)
    base = dict(prob=prob, odds=odds, eff_odds=oe, min_odds=mo,
                edge=e, kelly_full=kf, bankroll=bankroll)

    if bankroll <= 0:
        return StakePlan(0.0, False, "bankroll épuisée", **base)
    if odds < mo:
        return StakePlan(0.0, False,
                         f"cote {odds:.2f} sous le seuil de rentabilité {mo:.2f} "
                         f"(taxe {TAX_RATE*100:.1f} % incluse)", **base)
    if e < min_edge:
        return StakePlan(0.0, False,
                         f"edge {e*100:.1f} % sous le minimum requis {min_edge*100:.0f} %",
                         **base)

    used = kf * fraction
    stake = bankroll * min(used, max_share)
    if stake < MIN_STAKE:
        return StakePlan(0.0, False,
                         f"mise calculée {stake:.2f} € sous le minimum Betano "
                         f"{MIN_STAKE:.2f} € — bankroll trop faible pour cet edge",
                         kelly_used=used, **base)
    return StakePlan(round(stake, 2), True,
                     f"Kelly {kf*100:.1f} % × {fraction:.2f} = {used*100:.1f} % de la bankroll",
                     kelly_used=used, **base)


@dataclass
class Bankroll:
    """Suivi du capital dans le temps (historique complet)."""
    start: float = 10.0
    current: float = 10.0
    history: list = field(default_factory=list)   # [{date, event, amount, balance}]

    def bet(self, date: str, label: str, stake: float) -> None:
        self.current -= stake
        self.history.append({"date": date, "event": f"mise {label}",
                             "amount": -stake, "balance": round(self.current, 2)})

    def win(self, date: str, label: str, stake: float, odds: float,
            mode: str = "gross") -> float:
        payout = stake * effective_odds(odds, mode)
        self.current += payout
        self.history.append({"date": date, "event": f"gagné {label}",
                             "amount": round(payout, 2), "balance": round(self.current, 2)})
        return payout

    def lose(self, date: str, label: str) -> None:
        self.history.append({"date": date, "event": f"perdu {label}",
                             "amount": 0.0, "balance": round(self.current, 2)})

    @property
    def profit(self) -> float:
        return round(self.current - self.start, 2)

    @property
    def roi(self) -> float:
        return round((self.current / self.start - 1.0) * 100, 2) if self.start else 0.0
