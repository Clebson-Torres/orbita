# Skill: Busca de arquivos

## Quando usar
Quando o usuário quiser encontrar um arquivo no PC sem saber onde ele está.

Exemplos de frases:
- "onde está o arquivo X?"
- "acha o PDF que eu baixei hoje"
- "qual o caminho do arquivo relatório.docx?"
- "lista os arquivos .py da minha área de trabalho"
- "acha imagens baixadas essa semana"
- "procura arquivos maiores que 1 GB"

## Como usar

```powershell
# Busca por nome (recursivo a partir de uma pasta)
Get-ChildItem -Path "C:\Users\$env:USERNAME" -Recurse -Filter "*.pdf" -ErrorAction SilentlyContinue |
  Select-Object FullName, LastWriteTime, @{N="MB";E={[math]::Round($_.Length/1MB,1)}} |
  Sort-Object LastWriteTime -Descending | Select-Object -First 10

# Arquivos modificados hoje
Get-ChildItem -Path "C:\Users\$env:USERNAME\Downloads" -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -gt (Get-Date).Date } |
  Select-Object FullName, LastWriteTime

# Arquivos maiores que 500 MB
Get-ChildItem -Path "C:\" -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -gt 500MB } |
  Select-Object FullName, @{N="GB";E={[math]::Round($_.Length/1GB,2)}} |
  Sort-Object Length -Descending
```

Ao apresentar resultados, mostre no máximo 10 arquivos com caminho completo, data e tamanho.

## Nível de risco
read — apenas leitura do sistema de arquivos.
