# Skill: Informações do sistema

## Quando usar
Quando o usuário quiser saber especificações do hardware ou do sistema operacional.

Exemplos de frases:
- "qual meu processador?"
- "quanto de RAM eu tenho?"
- "qual versão do Windows estou usando?"
- "mostra as specs do PC"
- "qual minha placa de vídeo?"
- "uptime do sistema"
- "há quanto tempo o PC está ligado?"

## Como usar

```powershell
# Resumo completo do sistema
$os  = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$gpu = Get-CimInstance Win32_VideoController
$ram = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$up  = (Get-Date) - $os.LastBootUpTime

"SO: $($os.Caption) $($os.OSArchitecture)
CPU: $($cpu.Name)
GPU: $($gpu.Name)
RAM total: $ram GB
Uptime: $([math]::Floor($up.TotalHours))h $($up.Minutes)m"

# Disco
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used } |
  Select-Object Name,
    @{N="Total GB";E={[math]::Round(($_.Used+$_.Free)/1GB,1)}},
    @{N="Livre GB";E={[math]::Round($_.Free/1GB,1)}}

# Número de série do equipamento
(Get-CimInstance Win32_BIOS).SerialNumber
```

Formate a resposta de forma legível. Não exiba logs brutos do PowerShell.

## Nível de risco
read — apenas leitura de informações do hardware.
