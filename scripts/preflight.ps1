# RATISS LABS AGENT — preflight Windows (PROMPT GLM étape A)
# Vérifie les prérequis de l'hôte SANS installer quoi que ce soit et SANS démarrer de service.
# Usage : powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1
# Notes Windows : Docker passe par Docker Desktop + WSL2 ; gVisor/runsc n'y est PAS disponible
# (isolation Docker standard, plus faible) — signalé ci-dessous.

$ErrorActionPreference = "SilentlyContinue"
$script:Ok = 0
$script:Fail = 0
$script:Info = 0

function Write-Ok($m)   { Write-Host "  [OK]    $m"; $script:Ok++ }
function Write-Fail($m) { Write-Host "  [ÉCHEC] $m"; $script:Fail++ }
function Write-Info($m) { Write-Host "  [INFO]  $m"; $script:Info++ }

function Test-VersionGe([string]$a, [string]$b) {
    $va = $a.Split('.') | ForEach-Object { [int]$_ }
    $vb = $b.Split('.') | ForEach-Object { [int]$_ }
    for ($i = 0; $i -lt [Math]::Max($va.Count, $vb.Count); $i++) {
        $x = if ($i -lt $va.Count) { $va[$i] } else { 0 }
        $y = if ($i -lt $vb.Count) { $vb[$i] } else { 0 }
        if ($x -gt $y) { return $true }
        if ($x -lt $y) { return $false }
    }
    return $true
}

Write-Host "== Docker =="
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Fail "Docker absent — installer Docker Desktop (avec backend WSL2)"
} else {
    Write-Ok "Docker présent : $(docker --version)"
    docker info *> $null
    if ($LASTEXITCODE -eq 0) { Write-Ok "Docker daemon démarré" }
    else { Write-Fail "Docker présent mais daemon NON démarré — lancer Docker Desktop" }
    docker compose version *> $null
    if ($LASTEXITCODE -eq 0) { Write-Ok "Docker Compose v2 : $(docker compose version)" }
    else { Write-Fail "Docker Compose v2 absent" }
}

Write-Host "== Python =="
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) { $pyCmd = Get-Command python3 -ErrorAction SilentlyContinue }
if ($pyCmd) {
    $pyv = (& $pyCmd.Source -c "import sys; print('%d.%d' % sys.version_info[:2])")
    if (Test-VersionGe $pyv "3.12") { Write-Ok "Python $pyv (requis : 3.12, VERSIONS.md)" }
    else { Write-Fail "Python $pyv — 3.12 requis (ContextForge : >= 3.12 et < 3.14)" }
} else {
    Write-Fail "python absent"
}

Write-Host "== Node.js =="
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    $nv = (node --version) -replace '^v',''
    if (Test-VersionGe $nv "22.19") { Write-Ok "Node $nv (requis : >= 22.19, MCP Inspector 2.9.0)" }
    else { Write-Fail "Node $nv — >= 22.19 requis" }
} else {
    Write-Fail "node absent (requis >= 22.19)"
}

Write-Host "== Ressources =="
$os = Get-CimInstance Win32_OperatingSystem
$memFreeGo = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
if ($memFreeGo -ge 8) { Write-Ok "Mémoire disponible : $memFreeGo Go (>= 8 Go)" }
else { Write-Fail "Mémoire disponible : $memFreeGo Go (< 8 Go) — fermer des applications" }

$drive = Get-PSDrive -Name (Get-Location).Drive.Name
$diskFreeGo = [math]::Round($drive.Free / 1GB, 1)
if ($diskFreeGo -ge 20) { Write-Ok "Disque disponible : $diskFreeGo Go (>= 20 Go)" }
else { Write-Fail "Disque disponible : $diskFreeGo Go (< 20 Go)" }

Write-Host "== Ports (5432, 6379, 9000, 9001) =="
foreach ($p in 5432, 6379, 9000, 9001) {
    $listener = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($listener) { Write-Fail "Port $p OCCUPÉ — libérer le port ou changer la variable dans .env" }
    else { Write-Ok "Port $p libre" }
}

Write-Host "== Spécifique Windows =="
Write-Info "gVisor/runsc : NON disponible sur Windows/macOS — étape G : Docker standard (isolation plus faible), signalé au chef"
Write-Info "KVM : N/A (technologie Linux) — rien de requis en V1"
$wsl = wsl --status *> $null
if ($LASTEXITCODE -eq 0) { Write-Ok "WSL2 présent" }
else { Write-Info "WSL2 non détecté via 'wsl --status' — Docker Desktop peut néanmoins fonctionner" }

Write-Host ""
Write-Host "== Résumé =="
Write-Host ("  OK: {0}   ÉCHEC: {1}   INFO: {2}" -f $script:Ok, $script:Fail, $script:Info)
if ($script:Fail -gt 0) {
    Write-Host "  -> preflight : ÉCHEC. Corriger les points en ÉCHEC avant 'make up'."
    exit 1
}
Write-Host "  -> preflight : PASS. Aucun service n'a été démarré ni installé par ce script."
