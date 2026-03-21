import httpx
import pytest

from orbita.clients.web_scraper import WebScraperClient


def build_client(handler):
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


@pytest.mark.anyio
async def test_fetch_page_text_uses_builtin_html_parser():
    html = b"""
    <html>
      <body>
        <header>ignore me</header>
        <main>
          <h1>Titulo principal</h1>
          <p>Texto importante</p>
        </main>
      </body>
    </html>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=html)

    client = WebScraperClient()
    original_client = client._client
    client._client = build_client(handler)
    await original_client.aclose()

    text = await client.fetch_page_text("https://example.com")

    assert "Titulo principal" in text
    assert "Texto importante" in text
    await client.close()


@pytest.mark.anyio
async def test_fetch_headlines_works_without_lxml_dependency():
    html = b"""
    <html>
      <body>
        <h1><a href="/news/a">Manchete muito importante de tecnologia</a></h1>
        <h2><a href="/news/b">Outra manchete bastante relevante do dia</a></h2>
      </body>
    </html>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=html)

    client = WebScraperClient()
    original_client = client._client
    client._client = build_client(handler)
    await original_client.aclose()

    items = await client.fetch_headlines("https://example.com", max_items=2)

    assert len(items) == 2
    assert items[0].title == "Manchete muito importante de tecnologia"
    assert items[0].link == "https://example.com/news/a"
    await client.close()
