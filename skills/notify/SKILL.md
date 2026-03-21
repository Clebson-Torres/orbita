# Skill: Notificação no desktop

## Quando usar
Quando o usuário quiser que o bot envie um aviso visível na tela do PC — útil para lembretes,
alertas de reunião ou qualquer coisa que precise de atenção imediata.

Exemplos de frases:
- "me lembra daqui a 10 minutos"
- "manda uma notificação dizendo X"
- "avisa na tela quando terminar"
- "põe um lembrete de reunião às 14h"
- "notifica que o download acabou"

## Como usar
Use a ferramenta nativa `Notification` do Windows-MCP:

```
Notification(
    title="Lembrete",
    message="Reunião em 5 minutos!"
)
```

Para lembretes com atraso, use `PowerShell` com `Start-Sleep` antes da notificação:

```powershell
# Lembrete em 10 minutos (600 segundos)
Start-Sleep -Seconds 600
# Em seguida, dispare a Notification via Windows-MCP
```

⚠️ Nota: `Start-Sleep` bloqueia o PowerShell. Para lembretes longos, oriente o usuário
a usar o app Alarmes e Relógio do Windows, ou o Agendador de Tarefas.

## Nível de risco
read — apenas exibe informação, não altera o sistema.
