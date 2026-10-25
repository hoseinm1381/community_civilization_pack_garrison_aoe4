param([string]$Label = (Get-Date -Format 'MMddHHmmss'))
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$cfg = Get-Content -LiteralPath (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
& $cfg.python -B (Join-Path $PSScriptRoot 'verify_workspace.py') --storage-only
if ($LASTEXITCODE -ne 0) { throw 'Storage verification failed' }
& $cfg.python -B (Join-Path $PSScriptRoot 'release_071\build.py') source --label $Label
if ($LASTEXITCODE -ne 0) { throw 'Native source qualification failed; diagnostics retained' }
& $cfg.python -B (Join-Path $PSScriptRoot 'release_071\build.py') assemble --label $Label
if ($LASTEXITCODE -ne 0) { throw 'Native preservation rebuild failed; diagnostics retained' }
Write-Output 'Verified 0.7.1 delivery: output\release_071\delivery'
