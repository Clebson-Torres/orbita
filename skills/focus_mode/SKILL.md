# Skill: Modo foco / não perturbe

## Quando usar
Quando o usuário quiser entrar em um modo de foco: silenciar notificações, fechar apps
distrativos e configurar o ambiente para trabalho concentrado.

Exemplos de frases:
- "entra em modo foco"
- "ativa o não perturbe"
- "fecha as redes sociais e muta tudo"
- "modo pomodoro"
- "sai do modo foco"
- "desativa o não perturbe"

## Como usar

**Ativar modo foco (sequência de ações):**

1. Mutar o áudio do sistema:
```powershell
$wsh = New-Object -ComObject WScript.Shell
$wsh.SendKeys([char]173)  # tecla mute
```

2. Fechar apps distrativos (liste os que o usuário definir):
```powershell
@("chrome", "firefox", "discord", "telegram", "spotify") | ForEach-Object {
    Stop-Process -Name $_ -ErrorAction SilentlyContinue
}
```

3. Notificar que o modo foco está ativo:
Use `Notification(title="Modo Foco", message="Apps fechados. Bom trabalho!")`.

**Sair do modo foco:**
- Restaure o volume com a tecla de volume.
- Opcionalmente reabra os apps que o usuário desejar via `App(mode="launch", name="...")`.

**Modo Pomodoro:**
- Ative o foco.
- Use `Notification` para avisar quando acabar o ciclo (25 min trabalho / 5 min pausa).
- Oriente o bot a usar `Start-Sleep -Seconds 1500` (25 min) antes de disparar a notificação.

## Nível de risco
exec — fecha processos e altera configurações de áudio.
