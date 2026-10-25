param(
    [Parameter(Mandatory=$true)][string]$AedtExe,
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\config\hfss_config.json'),
    [switch]$Gui
)
$ErrorActionPreference = 'Stop'
$exePath = (Resolve-Path -LiteralPath $AedtExe).Path
$scriptPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'hfss_automation.py')).Path
$env:LORA_HFSS_CONFIG = (Resolve-Path -LiteralPath $ConfigPath).Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$cfg = Get-Content -LiteralPath $env:LORA_HFSS_CONFIG -Raw | ConvertFrom-Json
$outputPath = $cfg.output_project
if (-not [System.IO.Path]::IsPathRooted($outputPath)) { $outputPath = Join-Path $repoRoot $outputPath }
$outputFolder = Split-Path -Parent $outputPath
New-Item -ItemType Directory -Force -Path $outputFolder | Out-Null
$launchArgs = @('-RunScriptAndExit', ('"' + $scriptPath + '"'), '-LogFile', ('"' + (Join-Path $outputFolder 'aedt_batch.log') + '"'))
if (-not $Gui) { $launchArgs = @('-ng') + $launchArgs }
$startedAt = Get-Date
$process = Start-Process -FilePath $exePath -ArgumentList $launchArgs -WindowStyle Hidden -PassThru -Wait
if ($process.ExitCode -ne 0) { throw "AEDT exited with code $($process.ExitCode). Inspect AEDT messages and build/hfss_validation.log." }
$statusPath = Join-Path $outputFolder 'run_status.json'
if (-not (Test-Path -LiteralPath $statusPath)) { throw 'No script completion marker. Inspect aedt_batch.log and build/script_failure.log.' }
if ((Get-Item -LiteralPath $statusPath).LastWriteTime -lt $startedAt) { throw 'Stale script completion marker. Inspect aedt_batch.log and build/script_failure.log.' }
Get-Content -LiteralPath $statusPath
Write-Output 'Script completed. Confirm mesh convergence and RF acceptance before accepting results.'
