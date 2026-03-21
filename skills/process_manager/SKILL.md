# Skill: Gerenciador de processos

## Quando usar
Use esta skill quando o usuário perguntar sobre processos rodando no Windows, quiser fechar um programa ou verificar o que está consumindo recursos.

Exemplos de frases que ativam esta skill:
- "quais processos estão rodando?"
- "fecha o Chrome"
- "mata o processo X"
- "o que está usando mais CPU?"

## Como usar
Use a ferramenta `PowerShell` do Windows-MCP para listar processos:

```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet
```

Para encerrar um processo:
```powershell
Stop-Process -Name "chrome" -Force
```

⚠️ IMPORTANTE: encerrar processos é uma ação destrutiva. Sempre mostre ao usuário o que será encerrado e aguarde confirmação explícita antes de executar `Stop-Process`.

## Nível de risco
exec — pode encerrar processos e causar perda de dados não salvos.
