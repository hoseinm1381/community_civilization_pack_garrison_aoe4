param([string]$Label = (Get-Date -Format 'MMddHHmmss'))
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$cfg = Get-Content -LiteralPath (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
& $cfg.python -B (Join-Path $PSScriptRoot 'verify_workspace.py') --storage-only
if ($LASTEXITCODE -ne 0) { throw 'Storage verification failed' }
& $cfg.python -B (Join-Path $PSScriptRoot 'release_073/check_identity.py')
if ($LASTEXITCODE -ne 0) { throw 'Identity preflight failed' }
& $cfg.python -B (Join-Path $PSScriptRoot 'check_extension_inheritance.py') --refresh --official-cache (Join-Path $root 'output/release_074/official-extensions.json') --output (Join-Path $root 'output/release_074/inheritance.json')
if ($LASTEXITCODE -ne 0) { throw 'Inheritance preflight failed' }
& $cfg.python -B (Join-Path $PSScriptRoot 'release_074/build.py') --label $Label
if ($LASTEXITCODE -ne 0) { throw '0.7.4 failed; diagnostic logs retained' }
Write-Output 'Verified 0.7.4 delivery: output/release_074/delivery'
