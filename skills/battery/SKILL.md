# Skill: Bateria e energia

## Quando usar
Quando o usuário quiser saber o estado da bateria ou configurar o plano de energia.

Exemplos de frases:
- "qual a bateria agora?"
- "quanto tempo de bateria resta?"
- "estou na tomada?"
- "muda para modo economia de energia"
- "muda para modo de alto desempenho"
- "qual o plano de energia ativo?"

## Como usar

```powershell
# Status da bateria
$bat = Get-WmiObject Win32_Battery
"Carga: $($bat.EstimatedChargeRemaining)% | Status: $($bat.BatteryStatus) | Tempo restante: $([math]::Round($bat.EstimatedRunTime / 60, 1))h"

# Plano de energia atual
powercfg /getactivescheme

# Listar planos disponíveis
powercfg /list

# Mudar para economia (substitua o GUID pelo correto retornado em /list)
# powercfg /setactive SCHEME_MAX        # economia de energia
# powercfg /setactive SCHEME_BALANCED   # balanceado
# powercfg /setactive SCHEME_MIN        # alto desempenho
```

Se o equipamento for desktop (sem bateria), informe isso claramente ao usuário.

## Nível de risco
read — leitura de status. Mudar plano de energia é write.
