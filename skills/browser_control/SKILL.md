# Skill: Controle de browser (Playwright)

## Quando usar
APENAS quando scraping HTTP puro não funcionar. Casos reais:
- Site carrega conteúdo via JavaScript (SPA sem SSR)
- Precisa fazer login antes de acessar conteúdo
- Precisa preencher formulário e submeter
- Precisa clicar em elementos dinâmicos
- Sistemas internos corporativos

Exemplos de frases:
- "entra no [sistema] e baixa o relatório de hoje"
- "abre o [site] e faz login com minhas credenciais"
- "preenche o formulário em [URL]"
- "acessa o sistema interno e pega o dado X"

## Pré-requisito
Playwright precisa estar instalado:
```powershell
pip install playwright
playwright install chromium
```

## Como usar

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()

    # Navegar
    await page.goto("https://exemplo.com")

    # Esperar conteúdo carregar
    await page.wait_for_load_state("networkidle")

    # Extrair texto
    content = await page.inner_text("body")

    # Clicar em elemento
    await page.click("button#login")

    # Preencher campo
    await page.fill("input[name=email]", "usuario@email.com")

    # Screenshot (para debug)
    await page.screenshot(path="debug.png")

    await browser.close()
```

## Regras de segurança
- NUNCA armazene senhas em código ou no histórico do chat
- Sempre peça credenciais no momento do uso via prompt
- Confirme com o usuário ANTES de submeter qualquer formulário
- Use `headless=False` se o usuário quiser acompanhar visualmente

## Nível de risco
exec — controla o browser e pode submeter formulários. Exige confirmação.
