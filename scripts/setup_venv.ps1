<#
.SYNOPSIS
  Phase 0 - create the Python 3.12 virtual environment and install dependencies.
.USAGE
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_venv.ps1
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_venv.ps1 -CpuTorch   # smaller CPU-only torch
#>
param([switch]$CpuTorch)
# Native tools (docker, psql) write progress/NOTICEs to stderr. With "Stop", Windows PowerShell 5.1
# turns that into a terminating error, so use "Continue" and check $LASTEXITCODE explicitly instead.
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false   # PowerShell 7.3+
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# ---------- Log everything to logs\setup_venv.log (timestamped, appended) ----------
New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null
Start-Transcript -Path (Join-Path $root "logs\setup_venv.log") -Append -IncludeInvocationHeader | Out-Null
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] START setup_venv"
trap { Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR $_" -ForegroundColor Red; Stop-Transcript | Out-Null; break }

# 1. Locate Python 3.12 via the Windows launcher (falls back to 'python')
$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = @("py", "-3.12") }
}
if (-not $py) {
    $ver = & python -c "import sys;print(f'{sys.version_info[0]}.{sys.version_info[1]}')"
    if ($ver -ne "3.12") { Write-Warning "Python 3.12 not found (found $ver). Continuing, but 3.12 is the tested version." }
    $py = @("python")
}
Write-Host "Using Python: $($py -join ' ')" -ForegroundColor Cyan

# 2. Create .venv (idempotent)
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    if ($py.Length -gt 1) { & $py[0] $py[1..($py.Length-1)] -m venv .venv } else { & $py[0] -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
}
$venvPy = Join-Path $root ".venv\Scripts\python.exe"

# 3. Apply optional proxy settings from .env for pip
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*(HTTP_PROXY|HTTPS_PROXY|NO_PROXY)\s*=\s*(.+)\s*$') {
            Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
        }
    }
}

# 4. Install packages
& $venvPy -m pip install --upgrade pip
if ($CpuTorch) {
    & $venvPy -m pip install torch --index-url https://download.pytorch.org/whl/cpu
}
& $venvPy -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed - check proxy settings in .env" }

# 5. Create .env from template if missing
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Warning ".env created from .env.example - edit the <...> values before running db_docker.ps1"
}

Write-Host "`nDone. Activate with:  .\.venv\Scripts\Activate.ps1" -ForegroundColor Green

Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] END setup_venv"
Stop-Transcript | Out-Null
