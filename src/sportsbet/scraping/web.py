"""Primitives HTTP + recherche web, sans clé API.

Dépend de httpx et beautifulsoup4 (voir requirements.txt). Les imports sont
faits paresseusement pour que le reste du paquet fonctionne même si ces
bibliothèques ne sont pas installées.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus, urlparse, parse_qs

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 20.0
POLITE_DELAY = 1.0  # secondes entre requêtes vers un même hôte (courtoisie)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""


def _client():
    import httpx  # import paresseux
    return httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "fr,en;q=0.8"},
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
    )


def fetch(url: str, retries: int = 2) -> Optional[str]:
    """Récupère le HTML d'une page. None en cas d'échec."""
    import httpx
    last_exc = None
    for attempt in range(retries + 1):
        try:
            with _client() as c:
                r = c.get(url)
                r.raise_for_status()
                return r.text
        except httpx.HTTPError as e:  # réseau, 4xx/5xx, timeout
            last_exc = e
            time.sleep(POLITE_DELAY * (attempt + 1))
    return None


def parse(html: str):
    """Retourne un objet BeautifulSoup (parser lxml)."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "lxml")


def search(query: str, max_results: int = 10) -> List[SearchResult]:
    """Recherche web via l'endpoint HTML de DuckDuckGo (pas de clé API).

    Best-effort : si DuckDuckGo change son HTML ou bloque, retourne [].
    Pour un usage à grande échelle, préférer l'outil de recherche de l'agent
    (le workflow deep-research) plutôt que ce scraper.
    """
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    html = fetch(url)
    if not html:
        return []
    soup = parse(html)
    results: List[SearchResult] = []
    for a in soup.select("a.result__a"):
        href = a.get("href", "")
        # DuckDuckGo enveloppe l'URL dans un redirect uddg=
        real = href
        try:
            qs = parse_qs(urlparse(href).query)
            if "uddg" in qs:
                real = qs["uddg"][0]
        except Exception:
            pass
        snippet_el = a.find_parent("div", class_="result__body")
        snippet = ""
        if snippet_el:
            s = snippet_el.select_one(".result__snippet")
            snippet = s.get_text(" ", strip=True) if s else ""
        results.append(SearchResult(title=a.get_text(" ", strip=True), url=real, snippet=snippet))
        if len(results) >= max_results:
            break
    return results
