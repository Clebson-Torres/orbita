# Skill: Clipboard

## Quando usar
Use esta skill quando o usuário quiser ler ou escrever na área de transferência do Windows.

Exemplos de frases que ativam esta skill:
- "o que tem na área de transferência?"
- "copia esse texto para o clipboard"
- "me diz o que está copiado"
- "cola X no clipboard"

## Como usar
Use a ferramenta `Clipboard` do Windows-MCP:
- Para ler: `Clipboard.get()`
- Para escrever: `Clipboard.set(text="...")` — exige confirmação antes de executar.

## Nível de risco
write — pode sobrescrever conteúdo que o usuário tinha copiado.
