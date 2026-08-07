"""Lecture de pages web avec chaîne de repli — pour relever des cotes RÉELLES.

Le problème que cela résout : depuis ce serveur, Chromium tombe en
``ERR_CONNECTION_RESET`` sur toutes les cibles, et les sites de cotes bloquent
``curl`` (503 anti-bot, portail d'âge, rendu JavaScript). On en était réduit à
des **résumés de moteur de recherche** — qui donnent un chiffre sans dire de
quel bookmaker il vient. Or la cote 1,76 chez Netbet et la cote 1,82 chez Betano
n'ont pas le même sens : régime fiscal différent, disponibilité différente.

L'idée retenue du dépôt Agent-Reach : **plusieurs backends ordonnés, repli
automatique**. Jina Reader va chercher la page depuis SES serveurs et rend du
markdown propre — ce qui contourne à la fois notre blocage réseau et le rendu
JavaScript.

Vérifié le 03/08/2026 : Jina lit betexplorer, oddspedia et la presse spécialisée
là où curl et Chromium échouaient.

Stdlib pure (curl en sous-processus).
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

#: Backends essayés dans l'ordre. Le premier qui rend du contenu gagne.
JINA = "https://r.jina.ai/"

#: Signes que la page est revenue vide ou bloquée malgré un HTTP 200.
BLOCAGES = (
    "returned error 403", "returned error 503", "returned error 429",
    "Verificação de idade", "Age verification", "Just a moment",
    "Enable JavaScript", "Access denied",
)


@dataclass
class Page:
    url: str
    contenu: str = ""
    backend: str = ""
    erreur: str = ""

    @property
    def ok(self) -> bool:
        return len(self.contenu) > 500 and not self.bloquee

    @property
    def bloquee(self) -> bool:
        tete = self.contenu[:1500]
        return any(b.lower() in tete.lower() for b in BLOCAGES)


def _curl(url: str, timeout: int = 45) -> str:
    try:
        r = subprocess.run(
            ["curl", "-sSL", "-m", str(timeout), "-A", "Mozilla/5.0 (X11; Linux x86_64)", url],
            capture_output=True, timeout=timeout + 15)
        return r.stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def lire(url: str, timeout: int = 45) -> Page:
    """Lit une page via la chaîne de repli. Jina d'abord, curl direct ensuite."""
    txt = _curl(JINA + url, timeout)
    p = Page(url, txt, "jina")
    if p.ok:
        return p
    brut = _curl(url, timeout)
    if len(brut) > len(txt):
        p2 = Page(url, brut, "curl")
        if p2.ok:
            return p2
    if not p.contenu:
        p.erreur = "aucun backend n'a rendu de contenu"
    elif p.bloquee:
        p.erreur = "page bloquée (anti-bot, portail d'âge ou rendu JS)"
    return p


# ── Extraction de cotes ──────────────────────────────────────────────────────

#: Une cote plausible : 1.01 à 99.99. En dessous de 1.01, ce n'est pas une cote.
COTE = r"([1-9][0-9]?[.,][0-9]{2})"

#: Formulations rencontrées en roumain, allemand, anglais et français.
MOTIFS = [
    re.compile(rf"cot[ăa]\s*{COTE}", re.I),          # roumain : « cotă 1.76 »
    re.compile(rf"quote[nd]?\s*(?:von\s*)?{COTE}", re.I),   # allemand
    re.compile(rf"\bodds?\s*(?:of\s*)?{COTE}", re.I),       # anglais
    re.compile(rf"\bcote\s*(?:de\s*)?{COTE}", re.I),        # français
    re.compile(rf"@\s*{COTE}"),
]


@dataclass
class Cote:
    valeur: float
    contexte: str
    bookmaker: str = ""


#: Opérateurs dont la mention près d'une cote permet de l'attribuer.
BOOKS_CONNUS = ("betano", "bet365", "netbet", "superbet", "unibet", "tipico",
                "getsbet", "pinnacle", "bwin", "interwetten", "winamax")


def extraire_cotes(texte: str, fenetre: int = 220) -> list[Cote]:
    """Relève les cotes du texte, avec leur contexte et le bookmaker si nommé.

    On ne devine JAMAIS le bookmaker : s'il n'est pas écrit à proximité, le
    champ reste vide. Une cote sans opérateur identifié n'est pas exploitable
    (le régime fiscal change tout), mais elle reste affichée pour lecture
    humaine.
    """
    vues: dict[tuple, Cote] = {}
    for motif in MOTIFS:
        for m in motif.finditer(texte):
            try:
                v = float(m.group(1).replace(",", "."))
            except ValueError:
                continue
            if not (1.01 <= v <= 99.99):
                continue
            a = max(0, m.start() - fenetre)
            ctx = " ".join(texte[a:m.end() + 60].split())
            book = next((b for b in BOOKS_CONNUS if b in ctx.lower()), "")
            cle = (v, ctx[-80:])
            if cle not in vues:
                vues[cle] = Cote(v, ctx[-fenetre:], book)
    return list(vues.values())


@dataclass
class Releve:
    """Ce qu'on a réussi à lire pour un match donné."""
    sources_ok: list[str] = field(default_factory=list)
    sources_ko: list[tuple] = field(default_factory=list)
    cotes: list[Cote] = field(default_factory=list)


def relever(urls: list[str], timeout: int = 45) -> Releve:
    """Parcourt plusieurs sources et agrège les cotes lisibles."""
    r = Releve()
    for u in urls:
        p = lire(u, timeout)
        if p.ok:
            r.sources_ok.append(f"{u} [{p.backend}]")
            r.cotes.extend(extraire_cotes(p.contenu))
        else:
            r.sources_ko.append((u, p.erreur or "contenu trop court"))
    return r
