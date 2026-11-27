<#
.SYNOPSIS
  Run the whole pipeline end-to-end on a Windows machine that ALREADY has
  Python 3.12, Docker Desktop and Git installed (see README).
.USAGE
  powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1               # full run
  powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -Preflight    # only check prerequisites
  powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -ResetDb      # rebuild DB from scratch first
  powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -SkipFetch -SkipSemantic
#>
param([switch]$Preflight, [switch]$ResetDb, [switch]$SkipFetch, [switch]$SkipSemantic, [switch]$RawFetch)
# Native tools (docker, psql) write progress/NOTICEs to stderr. With "Stop", Windows PowerShell 5.1
# turns that into a terminating error, so use "Continue" and check $LASTEXITCODE explicitly instead.
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false   # PowerShell 7.3+
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null
Start-Transcript -Path (Join-Path $root "logs\run_all.log") -Append -IncludeInvocationHeader | Out-Null
function Stamp([string]$m, [string]$c = "Cyan") { Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m" -ForegroundColor $c }
trap { Stamp "ERROR: $_" "Red"; Stop-Transcript | Out-Null; exit 1 }

# ---------------- 0. Preflight: verify required software (installs NOTHING) ----------------
Stamp "Preflight checks"
$fail = 0
function Need([string]$label, [bool]$ok, [string]$hint) {
    if ($ok) { Write-Host "  [OK]   $label" -ForegroundColor Green }
    else { Write-Host "  [MISS] $label  -> $hint" -ForegroundColor Red; $script:fail++ }
}
$py312 = $false
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3.12 -c "import sys" 2>$null; $py312 = ($LASTEXITCODE -eq 0) }
Need "Python 3.12"      $py312 "install Python 3.12 x64"
Need "Git"              ([bool](Get-Command git -ErrorAction SilentlyContinue)) "install Git for Windows (or use -RawFetch)"
Need ".env present"     (Test-Path ".env") "Copy-Item .env.example .env and fill in values"

$dockerOk = [bool](Get-Command docker -ErrorAction SilentlyContinue)
Need "Docker CLI"       $dockerOk "install Docker Desktop (WSL2 backend)"
if ($dockerOk) { & docker info --format "{{.ServerVersion}}" *> $null; Need "Docker engine running" ($LASTEXITCODE -eq 0) "start Docker Desktop" }
if ($fail -gt 0) { throw "$fail prerequisite(s) missing - see README section 'Prerequisites'" }
if ($Preflight) { Stamp "Preflight passed" "Green"; Stop-Transcript | Out-Null; exit 0 }

$py = Join-Path $root ".venv\Scripts\python.exe"
function Step([string]$name, [scriptblock]$cmd) {
    Stamp ">>> $name"
    $t = Get-Date
    & $cmd
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
    Stamp "<<< $name done in $([int]((Get-Date) - $t).TotalSeconds)s" "Green"
}

# ---------------- Pipeline ----------------
Step "Phase 0 - venv + packages" { & powershell -ExecutionPolicy Bypass -File .\scripts\setup_venv.ps1 -CpuTorch }
Step "Network check"             { & $py -m src.check_network }
if ($ResetDb) { Step "Phase 1 - database (reset)" { & powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action reset } }
else          { Step "Phase 1 - database"         { & powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action ensure } }
Step "Phase 1 - verify DB"       { & $py -m src.check_setup }
if (-not $SkipFetch) {
    if ($RawFetch) { Step "Phase 2 - dataset (raw)" { & $py -m src.fetch_docs --mode raw } }
    else           { Step "Phase 2 - dataset (git)" { & $py -m src.fetch_docs } }
}
if ($SkipSemantic) { Step "Phase 3 - chunking (3 methods)" { & $py -m src.compare_chunking --skip-semantic } }
else               { Step "Phase 3 - chunking (4 methods)" { & $py -m src.compare_chunking } }
Step "Phase 4 - ingest + embeddings" { & $py -m src.ingest }
Step "Phase 5 - sample retrieval"    { & $py -m src.retrieve --user priya --q "How does a Kubernetes Deployment manage application replicas?" }
Step "Phase 6 - test matrix (Ex D)"  { & $py -m src.run_matrix }
Step "Phase 7 - negative tests (Ex E)" { & $py -m src.negative_tests }

Stamp "ALL PHASES COMPLETE. Evidence in .\evidence, logs in .\logs" "Green"
Stop-Transcript | Out-Null
