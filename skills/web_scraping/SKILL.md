# Skill: Scraping de páginas web (sem browser)

## Quando usar
Quando o usuário quiser extrair informações de um site que não tem RSS,
ou quando precisar do conteúdo de uma página específica.

Exemplos de frases:
- "abre esse site e me diz o que tem"
- "lê o conteúdo desta URL: ..."
- "extrai as manchetes de [site]"
- "o que está escrito em [URL]?"
- "pega o preço do produto nessa página"
- "qual o conteúdo desse artigo?"

## Como usar
O bot usa `WebScraperClient` direto em Python — NÃO abre browser:

```python
# Para texto geral da página:
text = await scraper.fetch_page_text(url)

# Para manchetes/títulos:
items = await scraper.fetch_headlines(url, max_items=10)
```

## Limitações importantes
- Não funciona em sites que carregam conteúdo só via JavaScript no cliente
  (ex: SPAs sem SSR, alguns dashboards, sistemas bancários)
- Para esses casos, use a skill `browser_control` com Playwright
- Sites com paywall ou login não são acessíveis

## Quando NÃO usar esta skill
- Sites que exigem login (use browser_control)
- Apps bancários ou sistemas internos corporativos
- Sites que bloqueiam requests sem JavaScript

## Nível de risco
read — apenas leitura de páginas públicas.
