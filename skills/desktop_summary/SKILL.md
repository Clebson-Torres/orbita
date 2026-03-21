# Skill: Resumo da área de trabalho

## Quando usar
Quando o usuário quiser um panorama geral do estado atual do PC: o que está aberto,
recursos em uso, e o que pode precisar de atenção.

Exemplos de frases:
- "o que está aberto no PC?"
- "dá um resumo do que está rodando"
- "status geral do sistema"
- "o PC está pesado?"
- "briefing do sistema"

## Como usar
Combine múltiplas fontes de informação em um resumo formatado:

```powershell
# Janelas abertas com título
$windows = Get-Process | Where-Object { $_.MainWindowTitle } |
  Select-Object Name, MainWindowTitle, @{N="RAM MB";E={[math]::Round($_.WorkingSet64/1MB,0)}} |
  Sort-Object "RAM MB" -Descending

# CPU e RAM do sistema
$os  = Get-CimInstance Win32_OperatingSystem
$cpu = (Get-CimInstance Win32_Processor).LoadPercentage
$ramTotal = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$ramFree  = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$ramUsed  = [math]::Round($ramTotal - $ramFree, 1)

# Disco C:
$disk = Get-PSDrive C
$diskFree = [math]::Round($disk.Free/1GB, 1)

"CPU: $cpu% | RAM: $ramUsed/$ramTotal GB | Disco C: $diskFree GB livre"
$windows | ForEach-Object { "  $($_.Name): $($_.MainWindowTitle) ($($_.`"RAM MB`") MB)" }
```

Apresente o resumo em linguagem natural, não como dump de tabela.
Destaque se CPU > 80%, RAM > 85% ou disco < 5 GB livres.

## Nível de risco
read — apenas leitura de estado do sistema.
