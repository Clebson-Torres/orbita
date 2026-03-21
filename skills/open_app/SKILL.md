# Skill: Abre aplicativo

## Quando usar
Use esta skill quando o usuário pedir para abrir um programa ou aplicativo no Windows.

Exemplos de frases que ativam esta skill:
- "abre o Notepad"
- "abre o Chrome"
- "abre o explorador de arquivos"
- "inicia o VS Code"

## Como usar
Use a ferramenta `App` do Windows-MCP no modo `launch`:
- `App(mode="launch", name="notepad")`
- `App(mode="launch", name="chrome")`
- `App(mode="launch", name="explorer")`

Antes de abrir qualquer app, use `Snapshot` para verificar se ele já está aberto e em qual estado.

## Nível de risco
exec — abre processos no sistema do usuário.
