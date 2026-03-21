# Skill: Controle de volume

## Quando usar
Quando o usuário quiser ajustar, mutar ou verificar o volume do sistema.

Exemplos de frases:
- "aumenta o volume"
- "coloca no mudo"
- "tira o mudo"
- "volume em 50%"
- "qual o volume atual?"
- "abaixa o som"

## Como usar
Use `PowerShell` com o objeto COM de áudio do Windows:

```powershell
# Mutar
$obj = New-Object -ComObject WScript.Shell
$obj.SendKeys([char]173)

# Aumentar volume (pressiona tecla de volume algumas vezes)
$obj = New-Object -ComObject WScript.Shell
1..5 | ForEach-Object { $obj.SendKeys([char]175) }

# Abaixar volume
$obj = New-Object -ComObject WScript.Shell
1..5 | ForEach-Object { $obj.SendKeys([char]174) }

# Definir volume exato (requer módulo AudioDeviceCmdlets ou script direto)
$volume = 50  # valor de 0 a 100
$wshShell = New-Object -ComObject WScript.Shell
Add-Type -TypeDefinition @"
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int f(); int g(); int h(); int i();
    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
    int j();
    int GetMasterVolumeLevelScalar(out float pfLevel);
}
[Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumerator {}
"@
```

Para verificar volume atual use `Snapshot` e leia o ícone da bandeja do sistema, ou sugira ao usuário que verifique manualmente.

## Nível de risco
write — altera configurações de áudio do sistema.
