"""Banc d'essai historique — rejouer un modèle contre les VRAIES cotes.

Le protocole de 100 jours produira ~120 prédictions. Il en faudrait ~6 800 pour
trancher sur le ROI. Les archives de football-data.co.uk contiennent, elles, des
dizaines de milliers de matchs AVEC les cotes d'ouverture ET de clôture — de quoi
répondre aujourd'hui à la question que l'expérience en direct ne tranchera pas.

Ce que les archives apportent, par match :
  • résultat complet (score final, mi-temps)
  • cotes d'OUVERTURE   (PSH, B365H, MaxH, AvgH…)
  • cotes de CLÔTURE    (PSCH, B365CH, MaxCH, AvgCH…) — suffixe C
  • tirs, tirs cadrés, corners, fautes, cartons

Avoir ouverture ET clôture permet de mesurer le **CLV** : notre sélection
voit-elle sa cote se resserrer d'ici au coup d'envoi ? C'est le seul indicateur
qui prédise la rentabilité future, et il converge en quelques centaines de paris
là où le ROI en demande des milliers.

⚠️ RÈGLE ABSOLUE : aucune information postérieure au coup d'envoi ne doit entrer
dans une prédiction. Toutes les fonctions de ce module travaillent sur des
fenêtres strictement antérieures. Un backtest qui triche est pire qu'aucun
backtest : il donne une confiance fausse.

Stdlib pure.
"""
from __future__ import annotations

import csv
import datetime
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from .fetch import lire

BASE = "https://www.football-data.co.uk/mmz4281/"
CACHE = Path(__file__).resolve().parents[2] / "data" / "cache" / "histo"

#: Championnats des archives principales. Le xG d'understat ne couvre que les
#: cinq grands ; les autres restent exploitables sans xG.
LIGUES = {
    "E0": ("Angleterre", "Premier League", 1),
    "E1": ("Angleterre", "Championship", 2),
    "D1": ("Allemagne", "Bundesliga", 1),
    "D2": ("Allemagne", "2. Bundesliga", 2),
    "SP1": ("Espagne", "La Liga", 1),
    "I1": ("Italie", "Serie A", 1),
    "F1": ("France", "Ligue 1", 1),
    "N1": ("Pays-Bas", "Eredivisie", 1),
    "B1": ("Belgique", "Pro League", 1),
    "P1": ("Portugal", "Primeira Liga", 1),
    "SC0": ("Écosse", "Premiership", 1),
    "T1": ("Turquie", "Süper Lig", 1),
    "G1": ("Grèce", "Super League", 1),
}

#: Bookmakers présents dans les archives, du plus fiable au moins fiable.
#: Pinnacle d'abord : marge la plus faible, donc probabilité la moins déformée.
BOOKS = [("pinnacle", "PS"), ("avg", "Avg"), ("max", "Max"),
         ("b365", "B365"), ("bf", "BF")]


@dataclass
class Match:
    """Un match joué, avec tout ce qu'on savait avant et ce qu'on a su après."""
    ligue: str
    pays: str
    niveau: int
    date: datetime.date
    heure: str
    domicile: str
    exterieur: str
    # Résultat — INTERDIT en entrée de modèle, réservé à l'évaluation.
    buts_dom: int
    buts_ext: int
    #: cotes d'ouverture {"pinnacle": (1, X, 2), …}
    ouverture: dict = field(default_factory=dict)
    #: cotes de clôture, mêmes clés
    cloture: dict = field(default_factory=dict)
    #: statistiques du match (tirs, tirs cadrés, corners…) — postérieures au
    #: coup d'envoi, donc utilisables SEULEMENT comme historique des matchs
    #: précédents, jamais pour le match lui-même.
    stats: dict = field(default_factory=dict)

    @property
    def issue(self) -> str:
        if self.buts_dom > self.buts_ext:
            return "1"
        return "X" if self.buts_dom == self.buts_ext else "2"

    @property
    def total_buts(self) -> int:
        return self.buts_dom + self.buts_ext

    def cote(self, issue: str, book: str = "pinnacle", cloture: bool = True):
        """Cote d'une issue. ``cloture=True`` = prix au coup d'envoi."""
        src = self.cloture if cloture else self.ouverture
        i = {"1": 0, "X": 1, "2": 2}.get(issue)
        if i is None:
            return None
        o = src.get(book)
        return o[i] if o and o[i] > 1 else None

    def meilleure_cote(self, issue: str, cloture: bool = True):
        """La cote la plus haute du marché — celle qui décide de la jouabilité."""
        src = self.cloture if cloture else self.ouverture
        i = {"1": 0, "X": 1, "2": 2}.get(issue)
        if i is None:
            return None
        vals = [o[i] for o in src.values() if o and o[i] > 1]
        return max(vals) if vals else None


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _i(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _date(v: str):
    m = re.match(r"(\d{2})/(\d{2})/(\d{2,4})$", (v or "").strip())
    if not m:
        return None
    j, mo, a = m.groups()
    a = a if len(a) == 4 else ("20" + a if int(a) < 70 else "19" + a)
    try:
        return datetime.date(int(a), int(mo), int(j))
    except ValueError:
        return None


def _cotes(row: dict, suffixe: str) -> dict:
    """suffixe '' = ouverture, 'C' = clôture."""
    out = {}
    for nom, pref in BOOKS:
        t = tuple(_f(row.get(f"{pref}{suffixe}{s}", "")) for s in ("H", "D", "A"))
        if all(x > 1 for x in t):
            out[nom] = t
    return out


def parse_saison(texte: str, code: str) -> list[Match]:
    i = texte.find("Div,Date")
    if i < 0:
        return []
    pays, _, niveau = LIGUES.get(code, ("?", "?", 1))
    out = []
    for row in csv.DictReader(io.StringIO(texte[i:])):
        row = {(k or "").strip(): v for k, v in row.items()}
        d = _date(row.get("Date", ""))
        dom, ext = (row.get("HomeTeam") or "").strip(), (row.get("AwayTeam") or "").strip()
        if not (d and dom and ext) or row.get("FTR") not in ("H", "D", "A"):
            continue
        out.append(Match(
            ligue=code, pays=pays, niveau=niveau, date=d,
            heure=(row.get("Time") or "").strip(),
            domicile=dom, exterieur=ext,
            buts_dom=_i(row.get("FTHG")), buts_ext=_i(row.get("FTAG")),
            ouverture=_cotes(row, ""), cloture=_cotes(row, "C"),
            stats={k: _i(row.get(k)) for k in
                   ("HS", "AS", "HST", "AST", "HC", "AC", "HY", "AY", "HR", "AR")
                   if row.get(k) not in (None, "")},
        ))
    return out


def saison_code(debut: int) -> str:
    """2024 → « 2425 » (saison 2024/25)."""
    return f"{debut % 100:02d}{(debut + 1) % 100:02d}"


def charger(ligues: list[str], saisons: list[int], timeout: int = 45) -> list[Match]:
    """Télécharge (ou relit du cache) et rend les matchs, triés par date.

    Le cache disque est indispensable : recharger 40 fichiers à chaque essai
    rendrait toute itération sur le modèle insupportablement lente.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    tous: list[Match] = []
    for lig in ligues:
        for an in saisons:
            s = saison_code(an)
            f = CACHE / f"{lig}_{s}.csv"
            if f.exists():
                txt = f.read_text(encoding="utf-8", errors="replace")
            else:
                p = lire(f"{BASE}{s}/{lig}.csv", timeout=timeout)
                txt = p.contenu
                if "Div,Date" in txt:
                    f.write_text(txt[txt.find("Div,Date"):], encoding="utf-8")
            tous.extend(parse_saison(txt, lig))
    tous.sort(key=lambda m: (m.date, m.ligue, m.domicile))
    return tous


# ── Évaluation ───────────────────────────────────────────────────────────────

@dataclass
class Calibrateur:
    """Corrige un modèle qui dit « 65 % » quand la réalité est 74 %.

    Le modèle glissant compresse ses probabilités vers le milieu : mesuré sur
    18 011 matchs, il annonçait 75 % là où la réalité était 89,5 %. Ce défaut
    n'est pas du bruit, c'est un biais systématique — donc corrigeable.

    Méthode : on découpe les prédictions d'ENTRAÎNEMENT en tranches, on relève
    la fréquence réelle de chacune, puis on interpole. C'est une régression
    isotonique du pauvre, mais elle capte l'essentiel — et elle a l'avantage
    d'être lisible : on peut afficher la courbe de correction.

    ⚠️ À entraîner sur une période et à appliquer sur une AUTRE. Calibrer et
    tester sur les mêmes matchs revient à connaître les résultats d'avance.
    """
    seuils: list = field(default_factory=list)     # centres des tranches
    reels: list = field(default_factory=list)      # fréquence observée
    n_entraine: int = 0

    def entrainer(self, obs: list, n_tranches: int = 20, mini: int = 50) -> None:
        """obs = [(probabilité prédite, l'événement s'est-il produit)]"""
        seaux: dict = {}
        for p, ok in obs:
            seaux.setdefault(min(n_tranches - 1, int(p * n_tranches)), []).append(ok)
        self.seuils, self.reels = [], []
        for b in sorted(seaux):
            g = seaux[b]
            if len(g) < mini:
                continue
            self.seuils.append((b + 0.5) / n_tranches)
            self.reels.append(sum(g) / len(g))
        self.n_entraine = len(obs)
        # Monotonie : une probabilité plus haute ne peut pas donner une
        # fréquence plus basse. On lisse les inversions dues au bruit.
        for i in range(1, len(self.reels)):
            if self.reels[i] < self.reels[i - 1]:
                self.reels[i] = self.reels[i - 1]

    @property
    def pret(self) -> bool:
        return len(self.seuils) >= 3

    def corriger(self, p: float) -> float:
        """Applique la correction, par interpolation linéaire entre tranches."""
        if not self.pret:
            return p
        if p <= self.seuils[0]:
            return self.reels[0]
        if p >= self.seuils[-1]:
            return self.reels[-1]
        for i in range(1, len(self.seuils)):
            if p <= self.seuils[i]:
                x0, x1 = self.seuils[i - 1], self.seuils[i]
                y0, y1 = self.reels[i - 1], self.reels[i]
                t = (p - x0) / (x1 - x0) if x1 > x0 else 0.0
                return y0 + t * (y1 - y0)
        return p

    def courbe(self) -> list[tuple[float, float]]:
        return list(zip(self.seuils, self.reels))


@dataclass
class Pari:
    """Une décision prise par un modèle, et ce qu'elle a rapporté."""
    match: Match
    issue: str
    prob: float
    cote: float
    gagne: bool
    mise: float = 1.0

    @property
    def profit(self) -> float:
        return (self.cote - 1.0) * self.mise if self.gagne else -self.mise

    @property
    def clv(self) -> float | None:
        """Valeur de fermeture : notre prix comparé au prix final.

        Positif = on a pris une cote MEILLEURE que la clôture, donc le marché
        s'est déplacé vers nous. C'est le signe le plus fiable qu'une méthode
        capte un vrai signal, bien avant que le ROI ne soit lisible.
        """
        fin = self.match.cote(self.issue, "pinnacle", cloture=True)
        return (self.cote / fin - 1.0) if fin else None


def evaluer(paris: list[Pari]) -> dict:
    """Bilan d'une série de paris : ROI, CLV, calibration, réussite."""
    if not paris:
        return {"n": 0}
    mise = sum(p.mise for p in paris)
    profit = sum(p.profit for p in paris)
    clvs = [p.clv for p in paris if p.clv is not None]
    buckets: dict[int, list[Pari]] = {}
    for p in paris:
        buckets.setdefault(min(90, int(p.prob * 10) * 10), []).append(p)
    calib = []
    for b in sorted(buckets):
        g = buckets[b]
        calib.append({
            "tranche": f"{b}-{b+10}%", "n": len(g),
            "predit": sum(x.prob for x in g) / len(g),
            "reel": sum(1 for x in g if x.gagne) / len(g),
        })
    return {
        "n": len(paris),
        "mise": round(mise, 2),
        "profit": round(profit, 2),
        "roi": round(profit / mise * 100, 2) if mise else 0.0,
        "reussite": round(sum(1 for p in paris if p.gagne) / len(paris) * 100, 1),
        "clv_moyen": round(sum(clvs) / len(clvs) * 100, 2) if clvs else None,
        "clv_positif": round(sum(1 for c in clvs if c > 0) / len(clvs) * 100, 1) if clvs else None,
        "calibration": calib,
    }
