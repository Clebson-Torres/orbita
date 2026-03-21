"""Cliente de web scraping — RSS e HTTP puro.

Não usa browser. Faz requisições HTTP diretas e parseia o conteúdo.
É a forma mais rápida e leve de extrair informações de sites.

Dependências extras necessárias:
    pip install beautifulsoup4 lxml

Adicione ao pyproject.toml:
    "beautifulsoup4>=4.12,<5",
    "lxml>=5.0,<6",
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


@dataclass
class NewsItem:
    title: str
    link: str
    description: str = ""
    published: str = ""

    def __str__(self) -> str:
        parts = [f"• {self.title}"]
        if self.description:
            parts.append(f"  {self.description[:180]}")
        if self.link:
            parts.append(f"  {self.link}")
        return "\n".join(parts)


class WebScraperClient:
    """Busca e parseia conteúdo de sites via HTTP puro (sem browser)."""

    def __init__(self, timeout: float = 15.0) -> None:
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=HEADERS,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # RSS — feed XML estruturado
    # ------------------------------------------------------------------

    async def fetch_rss(self, url: str, max_items: int = 8) -> list[NewsItem]:
        """Busca e parseia um feed RSS/Atom. Retorna lista de NewsItem."""
        response = await self._client.get(url)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        ns = self._detect_ns(root)
        items = self._parse_rss(root, ns, max_items)

        if not items:
            items = self._parse_atom(root, ns, max_items)

        logger.debug("RSS %s — %d itens encontrados", url, len(items))
        return items

    # ------------------------------------------------------------------
    # Scraping HTML genérico (sem browser)
    # ------------------------------------------------------------------

    async def fetch_page_text(self, url: str) -> str:
        """Baixa uma página e retorna o texto limpo (sem HTML).

        Requer beautifulsoup4 instalado. Se não estiver disponível,
        retorna o HTML bruto truncado.
        """
        response = await self._client.get(url)
        response.raise_for_status()

        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(response.content, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            lines = [ln for ln in text.splitlines() if ln.strip()]
            return "\n".join(lines[:200])
        except ImportError:
            logger.warning("beautifulsoup4 não instalado — retornando HTML bruto truncado")
            return response.text[:4000]

    async def fetch_headlines(self, url: str, max_items: int = 10) -> list[NewsItem]:
        """Extrai manchetes de qualquer página HTML (heurística).

        Tenta encontrar títulos dentro de tags <h1>, <h2>, <h3> e
        links com texto longo. Funciona bem para portais de notícias.
        """
        response = await self._client.get(url)
        response.raise_for_status()

        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(response.content, "lxml")
            items: list[NewsItem] = []

            for tag in soup.find_all(["h1", "h2", "h3"], limit=max_items * 2):
                title = tag.get_text(strip=True)
                if len(title) < 20:
                    continue
                anchor = tag.find("a") or tag.find_parent("a")
                link = anchor.get("href", "") if anchor else ""
                if link and not link.startswith("http"):
                    from urllib.parse import urljoin
                    link = urljoin(url, link)
                items.append(NewsItem(title=title, link=link))
                if len(items) >= max_items:
                    break

            return items
        except ImportError:
            logger.warning("beautifulsoup4 não instalado")
            return []

    # ------------------------------------------------------------------
    # Feeds conhecidos — atalhos prontos
    # ------------------------------------------------------------------

    KNOWN_FEEDS: dict[str, dict[str, str]] = {
        "g1": {
            "principais": "https://g1.globo.com/rss/g1/",
            "economia":   "https://g1.globo.com/rss/g1/economia/",
            "politica":   "https://g1.globo.com/rss/g1/politica/",
            "mundo":      "https://g1.globo.com/rss/g1/mundo/",
            "tecnologia": "https://g1.globo.com/rss/g1/tecnologia/",
        },
        "uol": {
            "principais": "https://rss.uol.com.br/feed/noticias.xml",
        },
        "folha": {
            "principais": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
            "poder":      "https://feeds.folha.uol.com.br/poder/rss091.xml",
            "mercado":    "https://feeds.folha.uol.com.br/mercado/rss091.xml",
        },
        "bbc_brasil": {
            "principais": "https://feeds.bbci.co.uk/portuguese/rss.xml",
        },
    }

    async def fetch_known(
        self, portal: str, section: str = "principais", max_items: int = 8
    ) -> list[NewsItem]:
        """Busca feed de um portal conhecido pelo apelido.

        Exemplo: fetch_known("g1", "economia")
        """
        portal_feeds = self.KNOWN_FEEDS.get(portal.lower())
        if not portal_feeds:
            raise ValueError(f"Portal desconhecido: {portal}. Disponíveis: {list(self.KNOWN_FEEDS)}")
        url = portal_feeds.get(section.lower()) or portal_feeds.get("principais")
        if not url:
            raise ValueError(f"Seção '{section}' não encontrada para '{portal}'")
        return await self.fetch_rss(url, max_items=max_items)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_ns(root: ET.Element) -> dict[str, str]:
        ns: dict[str, str] = {}
        tag = root.tag
        if tag.startswith("{"):
            uri = tag[1 : tag.index("}")]
            ns["atom"] = uri
        return ns

    @staticmethod
    def _parse_rss(root: ET.Element, ns: dict[str, Any], max_items: int) -> list[NewsItem]:
        items: list[NewsItem] = []
        channel = root.find("channel")
        if channel is None:
            return items
        for item in channel.findall("item")[:max_items]:
            title_el = item.find("title")
            link_el  = item.find("link")
            desc_el  = item.find("description")
            pub_el   = item.find("pubDate")

            title = WebScraperClient._cdata_or_text(title_el)
            link  = WebScraperClient._cdata_or_text(link_el)
            if not link:
                link = item.findtext("guid") or ""
            desc  = WebScraperClient._cdata_or_text(desc_el)[:200]
            pub   = WebScraperClient._cdata_or_text(pub_el)

            if title or link:
                items.append(NewsItem(title=title, link=link, description=desc, published=pub))
        return items

    @staticmethod
    def _parse_atom(root: ET.Element, ns: dict[str, Any], max_items: int) -> list[NewsItem]:
        items: list[NewsItem] = []
        atom = ns.get("atom", "http://www.w3.org/2005/Atom")
        pfx = f"{{{atom}}}"
        for entry in root.findall(f"{pfx}entry")[:max_items]:
            title = entry.findtext(f"{pfx}title") or ""
            link_el = entry.find(f"{pfx}link")
            link = link_el.get("href", "") if link_el is not None else ""
            summary = entry.findtext(f"{pfx}summary") or ""
            published = entry.findtext(f"{pfx}published") or ""
            items.append(NewsItem(title=title.strip(), link=link, description=summary[:200], published=published))
        return items

    @staticmethod
    def _cdata_or_text(el: ET.Element | None) -> str:
        if el is None:
            return ""
        return (el.text or "").strip()
