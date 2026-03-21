# Skill: Brilho da tela

## Quando usar
Quando o usuário quiser ajustar o brilho do monitor.

Exemplos de frases:
- "aumenta o brilho"
- "diminui o brilho"
- "coloca o brilho em 70%"
- "brilho máximo"
- "brilho mínimo"
- "tá muito claro / escuro"

## Como usar
Use `PowerShell` via WMI (funciona em monitores internos — notebooks):

```powershell
# Ver brilho atual
(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness

# Definir brilho (0–100)
$brightness = 70
(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, $brightness)
```

Para monitores externos via DisplayLink ou HDMI puro, o WMI pode não funcionar.
Nesse caso, oriente o usuário a usar os botões físicos do monitor ou o painel de controle da placa de vídeo.

## Nível de risco
write — altera configurações de exibição do sistema.
