<#
.SYNOPSIS
  Docker-based PostgreSQL 16 + pgvector for k8s-rag-rls.
  Creates the container, database, roles, tables, RLS and demo users if they are missing,
  otherwise verifies that everything is present.

.USAGE
  powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1                  # = -Action ensure
  powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action verify    # check only, change nothing
  powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action status
  powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action stop      # stop container, keep data
  powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action reset     # DELETE volume, rebuild all
  powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action psql      # interactive psql as superuser
  powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action logs

.ACTIONS
  ensure : start container (create if missing) -> wait healthy ->
           if database missing  : run sql\00..05 (create everything)
           if database present  : run sql\20_verify.sql; if any check FAILS,
                                  re-apply sql\00..05 (all idempotent) and verify again
#>
param(
    [ValidateSet("ensure", "verify", "status", "stop", "reset", "psql", "logs")]
    [string]$Action = "ensure",
    [int]$TimeoutSec = 120
)
# Native tools (docker, psql) write progress/NOTICEs to stderr. With "Stop", Windows PowerShell 5.1
# turns that into a terminating error, so use "Continue" and check $LASTEXITCODE explicitly instead.
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false   # PowerShell 7.3+
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# ---------- logging ----------
New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null
Start-Transcript -Path (Join-Path $root "logs\db_docker.log") -Append -IncludeInvocationHeader | Out-Null
function Stamp([string]$m, [string]$c = "Cyan") { Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m" -ForegroundColor $c }
trap { Stamp "ERROR: $_" "Red"; Stop-Transcript | Out-Null; exit 1 }
Stamp "START db_docker -Action $Action"

# ---------- load .env ----------
if (-not (Test-Path ".env")) { throw ".env not found. Run: Copy-Item .env.example .env  and fill in values." }
$cfg = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') { $cfg[$Matches[1]] = $Matches[2] }
}
foreach ($k in "PG_PORT", "PG_DATABASE", "PG_SUPERUSER", "PG_SUPERUSER_PASSWORD",
               "INGEST_DB_USER", "INGEST_DB_PASSWORD", "READER_DB_USER", "READER_DB_PASSWORD") {
    if (-not $cfg[$k] -or $cfg[$k] -like "<*>") { throw "Missing or placeholder value for $k in .env" }
}
$container = if ($cfg.PG_CONTAINER) { $cfg.PG_CONTAINER } else { "k8s-rag-pg" }

# ---------- docker available? ----------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "docker not found. Install Docker Desktop (WSL2 backend) and start it." }
& docker info --format "{{.ServerVersion}}" *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker engine is not running. Start Docker Desktop and retry." }

function Compose([string[]]$CArgs) {
    & docker compose --env-file .env -f docker-compose.yml @CArgs
    if ($LASTEXITCODE -ne 0) { throw "docker compose $($CArgs -join ' ') failed" }
}

# Run psql INSIDE the container (no local PostgreSQL client needed)
function Psql([string]$user, [string]$pw, [string]$db, [string[]]$extra, [switch]$Quiet) {
    $base = @("exec", "-i", "-e", "PGPASSWORD=$pw", $container,
              "psql", "-h", "127.0.0.1", "-U", $user, "-d", $db, "-v", "ON_ERROR_STOP=1",
              "-v", "db_name=$($cfg.PG_DATABASE)",
              "-v", "ingest_user=$($cfg.INGEST_DB_USER)",
              "-v", "reader_user=$($cfg.READER_DB_USER)")
    if ($Quiet) { $base += "-q" }
    $out = & docker @base @extra 2>&1
    $code = $LASTEXITCODE
    return @{ Code = $code; Out = ($out | Out-String) }
}

function RunSql([string]$user, [string]$pw, [string]$db, [string]$file, [string[]]$more = @()) {
    Stamp "  >> [$user@$db] sql/$file"
    $r = Psql $user $pw $db (@("-f", "/sql/$file") + $more) -Quiet
    if ($r.Out.Trim()) { Write-Host $r.Out.TrimEnd() }
    if ($r.Code -ne 0) { throw "sql/$file failed (exit $($r.Code))" }
}

function Wait-Healthy {
    Stamp "Waiting for container '$container' to become healthy (max ${TimeoutSec}s)"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $h = (& docker inspect -f "{{.State.Health.Status}}" $container 2>$null)
        if ($h -eq "healthy") { Stamp "Container healthy" "Green"; return }
        Start-Sleep -Seconds 3
    }
    & docker logs --tail 40 $container
    throw "Container did not become healthy in ${TimeoutSec}s"
}

function Db-Exists {
    $r = Psql $cfg.PG_SUPERUSER $cfg.PG_SUPERUSER_PASSWORD "postgres" @("-tAc",
         "SELECT 1 FROM pg_database WHERE datname = '$($cfg.PG_DATABASE)'")
    if ($r.Code -ne 0) { throw "Cannot query server: $($r.Out)" }
    return ($r.Out.Trim() -eq "1")
}

function Apply-All {
    $su = $cfg.PG_SUPERUSER; $suPw = $cfg.PG_SUPERUSER_PASSWORD
    $ing = $cfg.INGEST_DB_USER; $ingPw = $cfg.INGEST_DB_PASSWORD
    $pwVars = @("-v", "ingest_pw=$ingPw", "-v", "reader_pw=$($cfg.READER_DB_PASSWORD)")
    RunSql $su  $suPw  "postgres"          "00_roles_and_db.sql" $pwVars
    RunSql $su  $suPw  $cfg.PG_DATABASE    "01_extensions.sql"
    RunSql $ing $ingPw $cfg.PG_DATABASE    "02_schema.sql"
    RunSql $ing $ingPw $cfg.PG_DATABASE    "03_rls.sql"
    RunSql $ing $ingPw $cfg.PG_DATABASE    "04_grants.sql"
    RunSql $ing $ingPw $cfg.PG_DATABASE    "05_seed_users.sql"
}

# returns number of failed checks
function Verify {
    Stamp "Verifying database '$($cfg.PG_DATABASE)'"
    $r = Psql $cfg.PG_SUPERUSER $cfg.PG_SUPERUSER_PASSWORD $cfg.PG_DATABASE @("-f", "/sql/20_verify.sql")
    Write-Host $r.Out.TrimEnd()
    if ($r.Code -ne 0) { return 99 }
    $fails = ([regex]::Matches($r.Out, '\|\s*FAIL\s*\|')).Count
    if ($fails -eq 0) { Stamp "All checks PASS" "Green" } else { Stamp "$fails check(s) FAIL" "Yellow" }
    return $fails
}

function Container-State { (& docker inspect -f "{{.State.Status}}" $container 2>$null) }

# ---------- actions ----------
switch ($Action) {
    "status" {
        Compose @("ps")
        $s = Container-State
        Stamp "Container '$container': $(if ($s) { $s } else { 'not created' })"
        if ($s -eq "running") { if (Db-Exists) { Stamp "Database '$($cfg.PG_DATABASE)' exists" "Green" } else { Stamp "Database '$($cfg.PG_DATABASE)' missing" "Yellow" } }
    }
    "stop"  { Compose @("stop"); Stamp "Stopped (data kept in volume k8s-rag-pgdata)" "Green" }
    "logs"  { & docker logs --tail 100 $container }
    "psql"  { & docker exec -it -e "PGPASSWORD=$($cfg.PG_SUPERUSER_PASSWORD)" $container psql -h 127.0.0.1 -U $cfg.PG_SUPERUSER -d $cfg.PG_DATABASE }
    "verify" {
        if ((Container-State) -ne "running") { throw "Container '$container' is not running. Run -Action ensure." }
        if (-not (Db-Exists)) { throw "Database '$($cfg.PG_DATABASE)' does not exist. Run -Action ensure." }
        $f = Verify
        if ($f -ne 0) { throw "Verification failed ($f)" }
    }
    { $_ -in "ensure", "reset" } {
        if ($Action -eq "reset") {
            Stamp "RESET: removing container and volume (all data deleted)" "Yellow"
            Compose @("down", "-v")
        }
        $state = Container-State
        if ($state -eq "running") { Stamp "Container '$container' already running" }
        else {
            Stamp "Starting container '$container' (image $(if ($cfg.PG_IMAGE) { $cfg.PG_IMAGE } else { 'pgvector/pgvector:pg16' }), port 127.0.0.1:$($cfg.PG_PORT))"
            Compose @("up", "-d")
        }
        Wait-Healthy

        if (-not (Db-Exists)) {
            Stamp "Database '$($cfg.PG_DATABASE)' not found -> creating roles, database, tables, RLS, users" "Yellow"
            Apply-All
        } else {
            Stamp "Database '$($cfg.PG_DATABASE)' exists -> verifying objects"
            $f = Verify
            if ($f -ne 0) {
                Stamp "Repairing: re-applying idempotent SQL scripts" "Yellow"
                Apply-All
            } else {
                # passwords may have changed in .env -> re-apply them (cheap, idempotent)
                $pwVars = @("-v", "ingest_pw=$($cfg.INGEST_DB_PASSWORD)", "-v", "reader_pw=$($cfg.READER_DB_PASSWORD)")
                RunSql $cfg.PG_SUPERUSER $cfg.PG_SUPERUSER_PASSWORD "postgres" "00_roles_and_db.sql" $pwVars
            }
        }
        $f = Verify
        if ($f -ne 0) { throw "Database is not complete after setup ($f failing checks)" }
        Stamp "Database ready on localhost:$($cfg.PG_PORT)/$($cfg.PG_DATABASE). Next: python -m src.check_setup" "Green"
    }
}

Stamp "END db_docker"
Stop-Transcript | Out-Null
