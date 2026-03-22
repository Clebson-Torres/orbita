# Script de instalação do Orbita
# Uso: irm https://raw.githubusercontent.com/Clebson-Torres/orbita/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  FAIL $msg" -ForegroundColor Red; exit 1 }

Write-Host @"

  Orbita - Instalador

"@ -ForegroundColor White

# 1. Verifica Python
Write-Step "Verificando Python..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Fail "Python nao encontrado. Instale em https://python.org e tente novamente." }
$ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
Write-Ok "Python $ver encontrado"

if ([version]$ver -lt [version]"3.12") {
    Write-Fail "O Orbita requer Python 3.12+. Versao encontrada: $ver"
}

# 2. Instala o Orbita via pip
Write-Step "Instalando Orbita..."
& python -m pip install --quiet --disable-pip-version-check --no-warn-script-location --upgrade "git+https://github.com/Clebson-Torres/orbita.git"
if ($LASTEXITCODE -ne 0) { Write-Fail "Falha na instalacao via pip." }
Write-Ok "Orbita instalado"

# 3. Verifica PATH
Write-Step "Verificando comando orbita..."
$scriptsPath     = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$userScriptsPath = & python -c "import os, site; print(os.path.join(site.getuserbase(), 'Python314', 'Scripts') if os.name == 'nt' else os.path.join(site.getuserbase(), 'bin'))" 2>$null
if (-not (Test-Path $userScriptsPath)) {
    $userScriptsPath = Join-Path $env:APPDATA "Python\Python314\Scripts"
}
$scriptPaths = @($scriptsPath)
if ($userScriptsPath -and $userScriptsPath -ne $scriptsPath) {
    $scriptPaths += $userScriptsPath
}
$orbitaExePath = $null
foreach ($candidatePath in $scriptPaths) {
    $candidateExe = Join-Path $candidatePath "orbita.exe"
    if (Test-Path $candidateExe) {
        $orbitaExePath = $candidateExe
        break
    }
}
$orbita        = Get-Command orbita -ErrorAction SilentlyContinue

if (-not $orbita) {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    foreach ($candidatePath in $scriptPaths) {
        if (-not $candidatePath) { continue }
        if ($currentPath -notlike "*$candidatePath*") {
            $currentPath = "$currentPath;$candidatePath"
        }
        if ($env:PATH -notlike "*$candidatePath*") {
            $env:PATH += ";$candidatePath"
        }
    }
    [Environment]::SetEnvironmentVariable("PATH", $currentPath, "User")
    Write-Host "  INFO Scripts adicionados ao PATH do usuario." -ForegroundColor Yellow
    Write-Host "       Abra um novo terminal para usar o comando 'orbita' diretamente."
    $setupCommand = "orbita"
} else {
    Write-Ok "Comando 'orbita' disponivel em $($orbita.Source)"
    $setupCommand = "orbita"
}

# 4. Cria o lançador silencioso (sem janela CMD)
Write-Step "Criando lancador silencioso..."
$dataDir     = Join-Path $env:APPDATA "Orbita"
New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
$pythonDir   = Split-Path (& python -c "import sys; print(sys.executable)")
$pythonwPath = Join-Path $pythonDir "pythonw.exe"
$vbsPath     = Join-Path $dataDir "orbita.vbs"

# Escreve em ASCII puro — VBScript nao aceita BOM nem Unicode
$vbsLines = @(
    "Set oShell = CreateObject(""WScript.Shell"")",
    "oShell.Run """"$pythonwPath"""" -m orbita.main"", 0, False"
)
[System.IO.File]::WriteAllLines($vbsPath, $vbsLines, [System.Text.Encoding]::ASCII)
Write-Ok "Lancador criado em $vbsPath"

# 5. Cria atalho na area de trabalho
Write-Step "Criando atalho na area de trabalho..."
$desktop  = [Environment]::GetFolderPath("Desktop")
$lnkPath  = Join-Path $desktop "Orbita.lnk"
$wsh      = New-Object -ComObject WScript.Shell
$sc       = $wsh.CreateShortcut($lnkPath)
$sc.TargetPath      = "wscript.exe"
$sc.Arguments       = """$vbsPath"""
$sc.WorkingDirectory = $dataDir
$sc.Description     = "Iniciar Orbita sem janela"
$sc.Save()
Write-Ok "Atalho criado em $lnkPath"

# 6. Startup opcional
$startupDir = [Environment]::GetFolderPath("Startup")
$ans = Read-Host "`n  Iniciar Orbita automaticamente com o Windows? [S/n]"
if ($ans -eq "" -or $ans -match "^[Ss]") {
    Copy-Item $lnkPath (Join-Path $startupDir "Orbita.lnk") -Force
    Write-Ok "Adicionado ao Startup"
} else {
    Write-Host "  Pulado. Copie o atalho da area de trabalho para $startupDir se quiser depois."
}

# 7. Concluido
Write-Host @"

  ============================================
   Instalacao concluida!

   Configure o Orbita abrindo um novo terminal
   e executando:

     orbita setup

   Para iniciar sem janela:
     Clique duas vezes em Orbita.lnk
     na area de trabalho.
  ============================================

"@ -ForegroundColor Green

$ans2 = Read-Host "  Deseja executar 'orbita setup' agora neste terminal? [S/n]"
if ($ans2 -eq "" -or $ans2 -match "^[Ss]") {
    if (Test-Path $orbitaExePath) {
        & $orbitaExePath setup
    } else {
        & python -m orbita.cli setup
    }
}
