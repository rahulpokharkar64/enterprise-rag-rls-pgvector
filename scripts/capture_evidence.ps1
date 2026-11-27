<#
.SYNOPSIS
  Run a command, save its full output to evidence\screenshots\<Name>.txt,
  then take a PNG screenshot of the primary screen as evidence\screenshots\<Name>.png.
.USAGE
  .\scripts\capture_evidence.ps1 -Name 06_negative_tests -Command "python -m src.negative_tests"
  .\scripts\capture_evidence.ps1 -Name 05_run_matrix     -Command "python -m src.run_matrix"
  .\scripts\capture_evidence.ps1 -Name 09_nobody -Command "python -m src.retrieve --user nobody --q 'What are the main Kubernetes components?'"
.NOTES
  Maximise the terminal first. Run with the .venv activated (.\.venv\Scripts\Activate.ps1).
#>
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Command,
    [int]$DelaySec = 1
)
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$outDir = Join-Path $root "evidence\screenshots"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$txt = Join-Path $outDir "$Name.txt"
$png = Join-Path $outDir "$Name.png"

Clear-Host
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[$stamp] PS> $Command" -ForegroundColor Cyan

# Run and show output live, while also saving it to the .txt file
"[$stamp] PS> $Command" | Out-File -FilePath $txt -Encoding utf8
Invoke-Expression $Command 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $txt -Append
$code = $LASTEXITCODE
Write-Host "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] exit code: $code" -ForegroundColor $(if ($code -eq 0) { "Green" } else { "Red" })

# Screenshot of the primary screen
Start-Sleep -Seconds $DelaySec
try {
    Add-Type -AssemblyName System.Windows.Forms, System.Drawing
    $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
    $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Host "Saved: $png" -ForegroundColor Green
} catch {
    Write-Warning "Screenshot failed ($_). Use Win+Shift+S instead. Text saved to $txt"
}
Write-Host "Saved: $txt" -ForegroundColor Green
