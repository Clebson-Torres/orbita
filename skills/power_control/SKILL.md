# Skill: Controle de energia do PC

## Quando usar
Quando o usuário quiser desligar, reiniciar, hibernar ou bloquear o PC remotamente pelo Telegram.

Exemplos de frases:
- "desliga o PC"
- "reinicia o computador"
- "hiberna"
- "bloqueia a tela"
- "cancela o desligamento"
- "desliga em 30 minutos"

## Como usar

```powershell
# Bloquear a tela (mais seguro — não perde trabalho)
rundll32.exe user32.dll,LockWorkStation

# Hibernar
shutdown /h

# Desligar agora
shutdown /s /t 0

# Desligar em X segundos (ex: 1800 = 30 min)
shutdown /s /t 1800

# Reiniciar
shutdown /r /t 0

# Cancelar desligamento agendado
shutdown /a

# Suspender (sleep)
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::SetSuspendState("Suspend", $false, $false)
```

⚠️ REGRAS OBRIGATÓRIAS:
1. Para `desligar` e `reiniciar`: sempre peça confirmação com o texto exato da ação e um aviso
   de que arquivos não salvos serão perdidos.
2. Para `hibernar` e `bloquear`: confirmação é opcional, mas recomendada.
3. Nunca execute desligamento sem o usuário ter confirmado explicitamente.
4. Após confirmar desligamento, envie uma última mensagem: "Desligando em X segundos..."

## Nível de risco
exec — pode encerrar o sistema. Exige confirmação obrigatória e dupla verificação.
