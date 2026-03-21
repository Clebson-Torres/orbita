# Skill: Notícias via RSS (sem browser)

## Quando usar
Quando o usuário pedir notícias de portais de notícias. Esta skill usa RSS —
não abre browser, é instantânea e funciona offline para os sites configurados.

Exemplos de frases:
- "quais as notícias de hoje?"
- "notícias do G1"
- "o que está acontecendo no mundo?"
- "notícias de economia"
- "manchetes do dia"
- "notícias de política do G1"
- "últimas do G1 tecnologia"
- "resumo das notícias"

## Portais disponíveis (sem precisar de URL)
Use `WebScraperClient.fetch_known(portal, section)`:

| portal      | seções disponíveis                                        |
|-------------|-----------------------------------------------------------|
| g1          | principais, economia, politica, mundo, tecnologia         |
| folha       | principais, poder, mercado                                |
| bbc_brasil  | principais                                                |
| uol         | principais                                                |

## Como o bot usa
O bot chama `WebScraperClient.fetch_known()` diretamente em Python —
NÃO use PowerShell nem abra browser para isso.

O retorno é uma lista de `NewsItem` com título, link e descrição.
Formate como lista numerada e pergunte ao usuário se quer abrir alguma.

## Exemplo de resposta ideal
"Aqui estão as principais notícias do G1 agora:

1. [título] — [link curto]
2. [título] — [link curto]
...

Quer que eu abra alguma delas ou leia o conteúdo completo?"

## Nível de risco
read — apenas leitura de feeds públicos.
