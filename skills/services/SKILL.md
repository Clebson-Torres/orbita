# Skill: Serviços do Windows

## Quando usar
Quando o usuário quiser verificar, iniciar ou parar serviços do Windows.

Exemplos de frases:
- "o serviço X está rodando?"
- "inicia o serviço de impressão"
- "para o serviço do SQL Server"
- "lista os serviços parados"
- "reinicia o serviço de áudio"
- "quais serviços estão em execução?"

## Como usar

```powershell
# Listar todos os serviços em execução
Get-Service | Where-Object { $_.Status -eq "Running" } |
  Select-Object Name, DisplayName, Status | Sort-Object DisplayName

# Listar serviços parados
Get-Service | Where-Object { $_.Status -eq "Stopped" -and $_.StartType -ne "Disabled" } |
  Select-Object Name, DisplayName

# Verificar status de um serviço específico
Get-Service -Name "Spooler" | Select-Object Name, DisplayName, Status, StartType

# Iniciar serviço
Start-Service -Name "Spooler"

# Parar serviço
Stop-Service -Name "Spooler" -Force

# Reiniciar serviço
Restart-Service -Name "Spooler" -Force
```

⚠️ IMPORTANTE: sempre confirme com o usuário antes de parar ou reiniciar qualquer serviço.
Mostrar o nome e a descrição do serviço antes de executar a ação.

## Nível de risco
exec — iniciar/parar serviços pode afetar o funcionamento do sistema.
