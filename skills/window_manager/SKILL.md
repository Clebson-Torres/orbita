# Skill: Gerenciamento de janelas

## Quando usar
Quando o usuário quiser organizar, mover, redimensionar ou alternar entre janelas abertas.

Exemplos de frases:
- "coloca a janela em tela cheia"
- "minimiza tudo"
- "mostra a área de trabalho"
- "coloca o VS Code na metade esquerda da tela"
- "alterna para o Chrome"
- "lista as janelas abertas"
- "organiza as janelas lado a lado"

## Como usar

```powershell
# Listar janelas abertas com título
Get-Process | Where-Object { $_.MainWindowTitle } |
  Select-Object Name, MainWindowTitle, Id

# Mostrar área de trabalho (minimiza tudo)
$shell = New-Object -ComObject Shell.Application
$shell.MinimizeAll()

# Restaurar janelas
$shell.UndoMinimizeAll()
```

Para mover/redimensionar janelas individualmente, use a ferramenta `App` do Windows-MCP:
```
App(mode="resize", window_size=[1280, 720], window_loc=[0, 0])
App(mode="switch", name="chrome")
```

Para atalhos de snap do Windows:
- Use `Shortcut` com `win+left`, `win+right`, `win+up` para encaixar janelas.

Sempre use `Snapshot` antes de tentar interagir com uma janela específica para confirmar
que ela está visível e ativa.

## Nível de risco
write — move e redimensiona janelas ativas.
