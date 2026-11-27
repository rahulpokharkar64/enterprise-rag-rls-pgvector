<#
.SYNOPSIS
  ALTERNATIVE (no Docker). Default path is scripts\db_docker.ps1.
  Phase 1 - create roles, database, pgvector extension, schema, RLS and demo users
  on a NATIVE Windows PostgreSQL 16 server that already has pgvector installed.
.USAGE
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_db.ps1          # create / update (idempotent)
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_db.ps1 -Reset   # DROP database + roles, then recreate
#>
param([switch]$Reset)
# Native tools (docker, psql) write progress/NOTICEs to stderr. With "Stop", Windows PowerShell 5.1
# turns that into a terminating error, so use "Continue" and check $LASTEXITCODE explicitly instead.
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false   # PowerShell 7.3+
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# ---------- Log everything to logs\setup_db.log (timestamped, appended) ----------
New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null
Start-Transcript -Path (Join-Path $root "logs\setup_db.log") -Append -IncludeInvocationHeader | Out-Null
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] START setup_db"
trap { Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR $_" -ForegroundColor Red; Stop-Transcript | Out-Null; break }

# ---------- Load .env ----------
if (-not (Test-Path ".env")) { throw ".env not found. Run: Copy-Item .env.example .env  and fill in values." }
$cfg = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') { $cfg[$Matches[1]] = $Matches[2] }
}
foreach ($k in "PG_HOST","PG_PORT","PG_DATABASE","PG_SUPERUSER","PG_SUPERUSER_PASSWORD",
               "INGEST_DB_USER","INGEST_DB_PASSWORD","READER_DB_USER","READER_DB_PASSWORD") {
    if (-not $cfg[$k] -or $cfg[$k] -like "<*>") { throw "Missing or placeholder value for $k in .env" }
}

# ---------- Locate psql ----------
$psql = "psql"
if ($cfg["PG_BIN"] -and (Test-Path (Join-Path $cfg["PG_BIN"] "psql.exe"))) { $psql = Join-Path $cfg["PG_BIN"] "psql.exe" }
elseif (-not (Get-Command psql -ErrorAction SilentlyContinue)) { throw "psql.exe not found. Set PG_BIN in .env." }

$common = @("-h", $cfg.PG_HOST, "-p", $cfg.PG_PORT, "-v", "ON_ERROR_STOP=1", "-q",
            "-v", "db_name=$($cfg.PG_DATABASE)",
            "-v", "ingest_user=$($cfg.INGEST_DB_USER)",
            "-v", "reader_user=$($cfg.READER_DB_USER)")

function Invoke-Psql([string]$user, [string]$pw, [string]$db, [string]$file, [string[]]$extra = @()) {
    Write-Host ">> [$user@$db] $file" -ForegroundColor Cyan
    $env:PGPASSWORD = $pw
    try {
        & $psql @common -U $user -d $db @extra -f $file
        if ($LASTEXITCODE -ne 0) { throw "psql failed on $file (exit $LASTEXITCODE)" }
    } finally { Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue }
}

$su = $cfg.PG_SUPERUSER; $suPw = $cfg.PG_SUPERUSER_PASSWORD
$ing = $cfg.INGEST_DB_USER; $ingPw = $cfg.INGEST_DB_PASSWORD
$pwVars = @("-v", "ingest_pw=$ingPw", "-v", "reader_pw=$($cfg.READER_DB_PASSWORD)")

if ($Reset) { Invoke-Psql $su $suPw "postgres" "sql\99_reset.sql" }

# 1. Roles + database (superuser, maintenance DB)
Invoke-Psql $su $suPw "postgres" "sql\00_roles_and_db.sql" $pwVars
# 2. pgvector extension (superuser, target DB)
Invoke-Psql $su $suPw $cfg.PG_DATABASE "sql\01_extensions.sql"
# 3-6. Objects owned by the ingestion role
Invoke-Psql $ing $ingPw $cfg.PG_DATABASE "sql\02_schema.sql"
Invoke-Psql $ing $ingPw $cfg.PG_DATABASE "sql\03_rls.sql"
Invoke-Psql $ing $ingPw $cfg.PG_DATABASE "sql\04_grants.sql"
Invoke-Psql $ing $ingPw $cfg.PG_DATABASE "sql\05_seed_users.sql"

Write-Host "`nDatabase ready. Verify with:  .\.venv\Scripts\python.exe -m src.check_setup" -ForegroundColor Green

Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] END setup_db"
Stop-Transcript | Out-Null
