# Skill: Status da rede e IP

## Quando usar
Quando o usuário quiser saber informações sobre a conexão de rede atual.

Exemplos de frases:
- "qual meu IP?"
- "estou conectado na internet?"
- "qual a rede Wi-Fi que estou usando?"
- "mostra meu IP público"
- "qual meu IP local?"
- "teste de conectividade"
- "ping no Google"

## Como usar

```powershell
# IP local e adaptador ativo
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } |
  Select-Object InterfaceAlias, IPAddress, PrefixLength

# Nome da rede Wi-Fi atual
netsh wlan show interfaces | Select-String "SSID" | Select-String -NotMatch "BSSID"

# IP público (requer internet)
(Invoke-RestMethod -Uri "https://api.ipify.org?format=json").ip

# Teste de conectividade
Test-Connection -ComputerName 8.8.8.8 -Count 2 -Quiet
```

Combine os comandos para dar um resumo completo: adaptador, IP local, SSID (se Wi-Fi), e IP público.

## Nível de risco
read — apenas leitura de informações de rede.
