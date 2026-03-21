# Skill: Mapeamento e controle de drives de rede

## Quando usar
Quando o usuário quiser conectar, desconectar ou listar unidades de rede mapeadas.

Exemplos de frases:
- "lista os drives mapeados"
- "mapeia o drive Z: no caminho \\servidor\pasta"
- "desconecta o drive X:"
- "não consigo acessar o drive de rede"
- "qual o caminho do drive Y:?"

## Como usar

```powershell
# Listar drives mapeados
Get-PSDrive -PSProvider FileSystem |
  Where-Object { $_.DisplayRoot -like "\\*" } |
  Select-Object Name, DisplayRoot, @{N="Livre GB";E={[math]::Round($_.Free/1GB,1)}}

# Mapear drive de rede (pede credenciais se necessário)
New-PSDrive -Name "Z" -PSProvider FileSystem -Root "\\servidor\pasta" -Persist

# Mapear com credenciais específicas
$cred = Get-Credential
New-PSDrive -Name "Z" -PSProvider FileSystem -Root "\\servidor\pasta" -Persist -Credential $cred

# Desconectar drive
Remove-PSDrive -Name "Z" -Force

# Verificar conectividade com o servidor
Test-Connection -ComputerName "servidor" -Count 1 -Quiet
```

⚠️ Peça confirmação antes de desconectar drives — pode haver arquivos abertos.

## Nível de risco
write — conecta e desconecta unidades de rede.
