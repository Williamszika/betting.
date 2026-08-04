"""football-data.co.uk — fixtures ET cotes réelles de plusieurs bookmakers.

Ce que cette source apporte, et que rien d'autre ne nous donnait :

  • **Pinnacle** (colonnes PS*) — 2 à 3 % de marge, le bookmaker qui accepte les
    gagnants. Sa cote est la meilleure estimation publique de la probabilité
    réelle : c'est LA référence contre laquelle mesurer notre modèle.
  • **Moyenne du marché** (Avg*) — le consensus.
  • **Maximum disponible** (Max*) — la meilleure cote du marché, celle qui
    détermine la jouabilité.
  • **Betfair Exchange** (BFE*) et **bet365** (B365*).

Elle remplace les résumés de moteur de recherche, qui donnaient un chiffre sans
dire de quel opérateur il venait — et se trompaient : « bet365 à 1,20 » sur
Celtic, quand la donnée réelle disait 1,17.

Deux fichiers :
  fixtures.csv             grands championnats européens (E*, D*, SP*, I*, F*, SC*…)
  new_league_fixtures.csv  Roumanie, Pologne, Danemark, Suède, Norvège,
                           Argentine, Brésil, Mexique, USA, Autriche, Suisse…

Stdlib pure (curl en sous-processus).
"""
from __future__ import annotations

import csv
import datetime
import io
import re
import subprocess
from dataclasses import dataclass, field

from .devig import power

BASE = "https://www.football-data.co.uk/"
PRINCIPAL = BASE + "fixtures.csv"
AUTRES = BASE + "new_league_fixtures.csv"

#: Préfixes de colonnes, du plus fiable au moins fiable comme référence.
#: Pinnacle d'abord : marge la plus faible, donc probabilité la moins déformée.
SOURCES = [
    ("pinnacle", "PS"), ("avg", "Avg"), ("bfe", "BFE"),
    ("b365", "B365"), ("max", "Max"),
]

#: Codes de division du fichier principal → pays lisible.
DIVISIONS = {
    "E0": "Angleterre", "E1": "Angleterre D2", "E2": "Angleterre D3",
    "E3": "Angleterre D4", "EC": "Angleterre D5",
    "SC0": "Écosse", "SC1": "Écosse D2", "SC2": "Écosse D3", "SC3": "Écosse D4",
    "D1": "Allemagne", "D2": "Allemagne D2",
    "SP1": "Espagne", "SP2": "Espagne D2",
    "I1": "Italie", "I2": "Italie D2",
    "F1": "France", "F2": "France D2",
    "N1": "Pays-Bas", "B1": "Belgique", "P1": "Portugal",
    "T1": "Turquie", "G1": "Grèce",
}


@dataclass
class Fixture:
    pays: str
    ligue: str
    date: str                      # AAAA-MM-JJ
    heure: str                     # HH:MM (heure locale du championnat)
    domicile: str
    exterieur: str
    #: {"pinnacle": (cote1, coteX, cote2), …} — seulement les sources présentes.
    cotes: dict = field(default_factory=dict)

    @property
    def match(self) -> str:
        return f"{self.domicile} – {self.exterieur}"

    def reference(self) -> tuple[str, tuple] | None:
        """La meilleure référence de marché disponible, dans l'ordre de fiabilité."""
        for nom, _ in SOURCES:
            if nom in self.cotes:
                return nom, self.cotes[nom]
        return None

    def market_1x2(self, source: str | None = None) -> dict | None:
        """Probabilités 1X2 du marché, marge retirée par la méthode puissance.

        La méthode puissance et non proportionnelle : un bookmaker charge plus de
        marge sur les outsiders, et le proportionnel sous-estime donc le favori
        (mesuré : 5,1 points d'erreur sur Celtic – Dundee).
        """
        if source and source in self.cotes:
            nom, o = source, self.cotes[source]
        else:
            ref = self.reference()
            if not ref:
                return None
            nom, o = ref
        if not all(x and x > 1 for x in o):
            return None
        p = power(list(o))
        return {"source": nom, "1": p[0], "X": p[1], "2": p[2],
                "marge": round(sum(1 / x for x in o) - 1, 4)}

    def meilleure_cote(self, issue: str) -> tuple[float, str] | None:
        """La cote la PLUS HAUTE offerte sur cette issue, et par qui.

        C'est elle qui décide de la jouabilité : parier au prix moyen quand une
        meilleure cote existe, c'est jeter l'avantage qu'on cherche.
        """
        i = {"1": 0, "X": 1, "2": 2}.get(issue)
        if i is None:
            return None
        best, qui = 0.0, ""
        for nom, o in self.cotes.items():
            if nom == "max":                 # « max » n'est pas un opérateur
                continue
            if o[i] and o[i] > best:
                best, qui = o[i], nom
        if "max" in self.cotes and self.cotes["max"][i] > best:
            return self.cotes["max"][i], "marché (opérateur non nommé)"
        return (best, qui) if best > 1 else None


def _telecharger(url: str, timeout: int = 45) -> str:
    try:
        r = subprocess.run(["curl", "-sSL", "-m", str(timeout), url],
                           capture_output=True, timeout=timeout + 15)
        return r.stdout.decode("utf-8-sig", "replace")
    except Exception:
        return ""


def _f(v: str) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _date_iso(v: str) -> str:
    """« 03/08/2026 » → « 2026-08-03 ». Les autres formats sont ignorés."""
    m = re.match(r"(\d{2})/(\d{2})/(\d{2,4})$", (v or "").strip())
    if not m:
        return ""
    j, mo, a = m.groups()
    a = a if len(a) == 4 else ("20" + a)
    try:
        return datetime.date(int(a), int(mo), int(j)).isoformat()
    except ValueError:
        return ""


def _cotes_de(row: dict) -> dict:
    out = {}
    for nom, pref in SOURCES:
        t = tuple(_f(row.get(pref + s, "")) for s in ("H", "D", "A"))
        if all(x > 1 for x in t):
            out[nom] = t
    return out


def parse(texte: str) -> list[Fixture]:
    """Lit l'un ou l'autre des deux formats (colonnes Div ou Country/League)."""
    out = []
    for row in csv.DictReader(io.StringIO(texte)):
        row = {(k or "").strip(): v for k, v in row.items()}
        d = _date_iso(row.get("Date", ""))
        dom, ext = (row.get("Home") or row.get("HomeTeam") or "").strip(), \
                   (row.get("Away") or row.get("AwayTeam") or "").strip()
        if not (d and dom and ext):
            continue
        div = (row.get("Div") or "").strip()
        out.append(Fixture(
            pays=(row.get("Country") or DIVISIONS.get(div, div)).strip(),
            ligue=(row.get("League") or div).strip(),
            date=d, heure=(row.get("Time") or "").strip(),
            domicile=dom, exterieur=ext, cotes=_cotes_de(row)))
    return out


def charger(date: str | None = None, timeout: int = 45) -> list[Fixture]:
    """Télécharge les DEUX fichiers et fusionne. Filtre sur la date si fournie."""
    fx = []
    for url in (PRINCIPAL, AUTRES):
        t = _telecharger(url, timeout)
        if t.count(",") > 50:
            fx.extend(parse(t))
    return [f for f in fx if not date or f.date == date]


# ── Rapprochement avec les noms d'équipes d'une autre source ─────────────────

#: ClubElo utilise des noms historiques ou abrégés. Sans ce pont, « Steaua »
#: et « FCSB » sont deux clubs différents et le rapprochement échoue.
ALIAS = {
    "steaua": "fcsb", "viitorul": "farul", "dundee fc": "dundee",
    "sparta rotterdam": "sparta", "man united": "manchester united",
    "man city": "manchester city", "nott'm forest": "nottingham forest",
    "sheffield weds": "sheffield wednesday", "lok plovdiv": "lokomotiv plovdiv",
    "pogon": "pogon szczecin", "vaesteras": "vasteras",
}


def _norm(n: str) -> str:
    n = (n or "").lower().strip()
    n = re.sub(r"[.'’-]", " ", n)
    n = re.sub(r"\b(fc|sc|ac|as|cf|sv|fk|nk|bk|if|ff|cd|ud|us)\b", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return ALIAS.get(n, n)


def rapprocher(dom: str, ext: str, fixtures: list[Fixture]) -> Fixture | None:
    """Retrouve un match dans la liste, malgré les écarts de nommage."""
    a, b = _norm(dom), _norm(ext)
    for f in fixtures:                       # correspondance exacte après normalisation
        if _norm(f.domicile) == a and _norm(f.exterieur) == b:
            return f
    for f in fixtures:                       # repli : préfixe commun d'au moins 5 lettres
        fa, fb = _norm(f.domicile), _norm(f.exterieur)
        if ((fa.startswith(a[:5]) or a.startswith(fa[:5]))
                and (fb.startswith(b[:5]) or b.startswith(fb[:5]))
                and len(a) >= 4 and len(b) >= 4):
            return f
    return None
