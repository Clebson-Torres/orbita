# Script de instalação do Orbita
# Uso: irm https://raw.githubusercontent.com/Clebson-Torres/orbita/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  FAIL $msg" -ForegroundColor Red; exit 1 }

Write-Host @"

  ╔═══════════════════════════════╗
  ║   Orbita — Instalador         ║
  ╚═══════════════════════════════╝

"@ -ForegroundColor White

# ── 1. Verifica Python ────────────────────────────────────────────
Write-Step "Verificando Python..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Fail "Python não encontrado. Instale em https://python.org e tente novamente." }
$ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
Write-Ok "Python $ver encontrado"

if ([version]$ver -lt [version]"3.12") {
    Write-Fail "O Orbita requer Python 3.12+. Versão encontrada: $ver"
}

# ── 2. Instala o Orbita via pip ───────────────────────────────────
Write-Step "Instalando Orbita..."
& python -m pip install --quiet --disable-pip-version-check --no-warn-script-location --upgrade git+https://github.com/Clebson-Torres/orbita.git
if ($LASTEXITCODE -ne 0) { Write-Fail "Falha na instalação via pip." }
Write-Ok "Orbita instalado"

# ── 3. Verifica se o comando 'orbita' está acessível ─────────────
Write-Step "Verificando comando orbita..."
$orbita = Get-Command orbita -ErrorAction SilentlyContinue
$scriptsPath = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$orbitaExePath = Join-Path $scriptsPath "orbita.exe"
$setupCommand = "python -m orbita.cli setup"
$runCommand = "python -m orbita.cli run"

if (-not $orbita) {
    # Scripts do pip às vezes ficam fora do PATH — tenta adicionar
    $env:PATH += ";$scriptsPath"
    [Environment]::SetEnvironmentVariable(
        "PATH",
        [Environment]::GetEnvironmentVariable("PATH","User") + ";$scriptsPath",
        "User"
    )
    Write-Host "  INFO Scripts adicionados ao PATH: $scriptsPath" -ForegroundColor Yellow
    Write-Host "       O PATH do usuário foi atualizado; novos terminais já verão o comando 'orbita'."
    if (Test-Path $orbitaExePath) {
        Write-Host "       Neste terminal atual, você também pode usar:"
        Write-Host "         & `"$orbitaExePath`" setup"
        Write-Host "       ou, se preferir sem depender do PATH:"
        Write-Host "         $setupCommand"
    } else {
        Write-Host "       Se o comando 'orbita' ainda não aparecer neste terminal, use:"
        Write-Host "         $setupCommand"
    }
} else {
    Write-Ok "Comando 'orbita' disponível em $($orbita.Source)"
    $setupCommand = "orbita setup"
    $runCommand = "orbita run"
}

# ── 4. Cria o lançador sem janela (%APPDATA%\Orbita\orbita.vbs) ──
Write-Step "Criando lançador silencioso..."
$dataDir  = Join-Path $env:APPDATA "Orbita"
New-Item -ItemType Directory -Path $dataDir -Force | Out-Null

$pythonwPath = Join-Path (Split-Path (& python -c "import sys; print(sys.executable)")) "pythonw.exe"
$orbitaModule = & python -c "import orbita; import os; print(os.path.dirname(orbita.__file__))"

$vbsContent = @"
' Orbita — lançador silencioso (sem janela CMD)
' Gerado automaticamente pelo instalador
Set oShell = CreateObject("WScript.Shell")
oShell.Run """$pythonwPath"" -m orbita.main", 0, False
"@

$vbsPath = Join-Path $dataDir "orbita.vbs"
$vbsContent | Out-File -FilePath $vbsPath -Encoding utf8
Write-Ok "Lançador criado em $vbsPath"

# ── 5. Cria atalho na área de trabalho ───────────────────────────
Write-Step "Criando atalho na área de trabalho..."
$desktop  = [Environment]::GetFolderPath("Desktop")
$lnkPath  = Join-Path $desktop "Orbita.lnk"
$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($lnkPath)
$shortcut.TargetPath     = "wscript.exe"
$shortcut.Arguments      = """$vbsPath"""
$shortcut.WorkingDirectory = $dataDir
$shortcut.Description    = "Iniciar Orbita (sem janela)"
$shortcut.Save()
Write-Ok "Atalho criado em $lnkPath"

# ── 6. Cria atalho no Startup (inicia com Windows) ───────────────
$startupDir = [Environment]::GetFolderPath("Startup")
$startupLnk = Join-Path $startupDir "Orbita.lnk"
$ans = Read-Host "`n  Iniciar Orbita automaticamente com o Windows? [S/n]"
if ($ans -eq "" -or $ans -match "^[Ss]") {
    Copy-Item $lnkPath $startupLnk -Force
    Write-Ok "Adicionado ao Startup"
} else {
    Write-Host "  Pulado. Para adicionar depois, copie o atalho da área de trabalho para:"
    Write-Host "  $startupDir"
}

# ── 7. Concluído ──────────────────────────────────────────────────
Write-Host @"

  ══════════════════════════════════════
   Instalação concluída!

   Próximo passo — configure o Orbita:

     $setupCommand

   Para iniciar sem janela:
     Clique duas vezes em Orbita.lnk
     na área de trabalho.

   Para iniciar pelo terminal:
     $runCommand
  ══════════════════════════════════════
"@ -ForegroundColor Green

$runSetupNow = Read-Host "`n  Deseja executar a configuração agora? [S/n]"
if ($runSetupNow -eq "" -or $runSetupNow -match "^[Ss]") {
    Write-Step "Abrindo configuração do Orbita..."
    if ($orbita -or (Test-Path $orbitaExePath)) {
        if ($orbita) {
            & orbita setup
        } else {
            & $orbitaExePath setup
        }
    } else {
        & python -m orbita.cli setup
    }
}
