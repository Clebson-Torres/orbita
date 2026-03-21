# Skill: Monitoramento de temperatura da CPU/GPU

## Quando usar
Quando o usuário quiser saber se o PC está esquentando ou verificar temperaturas dos componentes.

Exemplos de frases:
- "qual a temperatura da CPU?"
- "o PC está esquentando?"
- "mostra a temperatura dos componentes"
- "está muito quente?"

## Como usar

O Windows não expõe temperaturas via WMI por padrão. Use as opções abaixo:

**Opção 1 — via WMI (nem sempre disponível):**
```powershell
Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace "root/wmi" |
  Select-Object InstanceName,
    @{N="Celsius";E={[math]::Round($_.CurrentTemperature / 10 - 273.15, 1)}}
```

**Opção 2 — via Open Hardware Monitor (se instalado):**
```powershell
# Requer que o serviço OpenHardwareMonitor esteja rodando
Get-WmiObject -Namespace "root/OpenHardwareMonitor" -Class Sensor |
  Where-Object { $_.SensorType -eq "Temperature" } |
  Select-Object Name, Value, Parent
```

**Opção 3 — recomende ao usuário:**
Se nenhuma opção acima funcionar, oriente a instalar o HWMonitor ou Core Temp,
e a usar `Snapshot` para ler os valores na interface.

Ao responder, apresente os valores em Celsius e indique se estão em faixa normal
(CPU: até 85°C em carga, GPU: até 90°C em carga).

## Nível de risco
read — apenas leitura de sensores do hardware.
