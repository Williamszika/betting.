"""Fiabilité par compétition + seuils de value + pré-filtre anti-bruit.

Idée (audit) : ne pas traiter une NBA Summer League comme une Premier League.
On attribue un COEFFICIENT DE FIABILITÉ à chaque compétition, on l'applique à
l'edge (pas de value « fake » sur données pourries), on impose des SEUILS de
value minimaux, et on PRÉ-FILTRE les matchs peu fiables AVANT l'analyse coûteuse.
"""
from __future__ import annotations

# Règles par mots-clés (ordre = priorité). Coefficient dans [0, 1].
COMP_RULES = [
    (["summer league"], 0.30),                       # ❌ data très bruitée
    (["friendly", "amical", "testspiel", "exhibition",
      "pre-season", "preseason", "pré-saison"], 0.25),
    (["champions league", "europa league", "premier league", "la liga",
      "serie a", "bundesliga", "ligue 1"], 1.00),     # top football
    (["grand slam", "wimbledon", "roland", "us open", "australian open",
      "atp masters", "wta 1000"], 0.95),
    (["atp", "wta"], 0.90),                            # ATP/WTA standard
    (["eredivisie", "primeira", "liga portugal", "championship",
      "super lig", "allsvenskan", "eliteserien"], 0.85),
    (["euroleague", "eurocup"], 0.90),
    (["nba"], 1.00),                                   # NBA saison (SL déjà capté)
    (["challenger", "itf"], 0.75),
    (["besta deild", "1. deild", "2. deild", "islande", "iceland"], 0.65),
]

SPORT_DEFAULT = {"football": 0.70, "tennis": 0.85, "basketball": 0.70}

BLACKLIST_KEYWORDS = ["friendly", "amical", "testspiel", "exhibition",
                      "pre-season", "preseason", "pré-saison"]

# Seuils de value minimaux par type de pari (edge = proba*cote - 1).
MIN_EDGE = {"safe": 0.05, "aggressive": 0.08, "combine": 0.06}


def competition_reliability(competition: str, sport: str = "football") -> float:
    """Coefficient de fiabilité [0,1] d'une compétition."""
    c = (competition or "").lower()
    for kws, coef in COMP_RULES:
        if any(k in c for k in kws):
            return coef
    return SPORT_DEFAULT.get(sport, 0.70)


def is_blacklisted(competition: str) -> bool:
    """Matchs à exclure d'office (amicaux, exhibitions…)."""
    c = (competition or "").lower()
    return any(k in c for k in BLACKLIST_KEYWORDS)


def passes_prefilter(competition: str, sport: str = "football",
                     floor: float = 0.35) -> bool:
    """True si le match mérite l'analyse coûteuse (pas blacklisté et fiabilité >= floor)."""
    if is_blacklisted(competition):
        return False
    return competition_reliability(competition, sport) >= floor


def effective_edge(edge: float, reliability: float) -> float:
    """Edge ajusté par la fiabilité : une value sur données pourries vaut moins."""
    return edge * reliability


def qualifies(edge: float, reliability: float, kind: str = "combine") -> bool:
    """Le pari passe-t-il le seuil de value (après ajustement fiabilité) ?"""
    return effective_edge(edge, reliability) >= MIN_EDGE.get(kind, 0.06)
