# Skill: Histórico de comandos e automação rápida

## Quando usar
Quando o usuário quiser executar um bloco de PowerShell diretamente, ver o que foi executado
recentemente, ou criar um script rápido para automatizar uma tarefa repetitiva.

Exemplos de frases:
- "roda esse comando PowerShell: ..."
- "cria um script que faz X"
- "automatiza essa tarefa"
- "salva esse script como tarefa agendada"
- "executa o script da área de trabalho"
- "cria uma tarefa que roda todo dia às 8h"

## Como usar

**Executar comando direto:**
Use `PowerShell` com o comando fornecido pelo usuário. Sempre exiba o output.

**Criar e salvar script:**
Use `FileSystem.write` para criar o arquivo `.ps1`:
```powershell
# Caminho sugerido para scripts do usuário
$path = "$env:USERPROFILE\Scripts\minha_tarefa.ps1"
```

**Criar tarefa agendada:**
```powershell
# Tarefa que roda todo dia às 08:00
$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Users\$env:USERNAME\Scripts\minha_tarefa.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
Register-ScheduledTask -TaskName "MinhaTarefa" -Action $action -Trigger $trigger -RunLevel Highest
```

**Listar tarefas agendadas do usuário:**
```powershell
Get-ScheduledTask | Where-Object { $_.TaskPath -eq "\" } |
  Select-Object TaskName, State, @{N="Próxima execução";E={($_ | Get-ScheduledTaskInfo).NextRunTime}}
```

⚠️ Sempre mostre o código ao usuário antes de executar ou salvar. Peça confirmação para
operações de escrita ou agendamento.

## Nível de risco
exec — executa código arbitrário. Exige confirmação e revisão do conteúdo antes de rodar.
