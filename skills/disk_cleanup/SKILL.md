# Skill: Limpeza de arquivos temporários

## Quando usar
Quando o usuário quiser liberar espaço em disco limpando arquivos desnecessários.

Exemplos de frases:
- "limpa os temporários"
- "libera espaço no disco"
- "limpa o cache do Windows"
- "quanto espaço eu tenho?"
- "limpa a lixeira"
- "mostra o espaço em disco"

## Como usar

```powershell
# Ver espaço em disco
Get-PSDrive C | Select-Object Used, Free |
  ForEach-Object { "Usado: $([math]::Round($_.Used/1GB,1)) GB | Livre: $([math]::Round($_.Free/1GB,1)) GB" }

# Tamanho da pasta Temp do usuário
$size = (Get-ChildItem $env:TEMP -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
"Temporários: $([math]::Round($size/1MB,1)) MB"

# Limpar Temp do usuário (peça confirmação antes)
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue

# Esvaziar Lixeira (peça confirmação antes)
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# Executar Limpeza de Disco do Windows (interativo)
cleanmgr /d C:
```

⚠️ IMPORTANTE: sempre mostre ao usuário o quanto será liberado ANTES de deletar qualquer coisa.
Peça confirmação explícita antes de executar `Remove-Item` ou `Clear-RecycleBin`.

## Nível de risco
exec — deleta arquivos do sistema. Exige confirmação obrigatória.
