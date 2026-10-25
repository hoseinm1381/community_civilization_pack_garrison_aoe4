param([string]$Label = (Get-Date -Format 'MMddHHmmss'))
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$cfg = Get-Content -LiteralPath (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
& $cfg.python -B (Join-Path $PSScriptRoot 'verify_workspace.py') --storage-only
if ($LASTEXITCODE -ne 0) { throw 'Storage verification failed' }
& $cfg.python -B (Join-Path $PSScriptRoot 'release_072\check_active.py')
if ($LASTEXITCODE -ne 0) { throw 'Active source differs from the verified 0.7.2 policy' }
& $cfg.python -B (Join-Path $PSScriptRoot 'check_extension_inheritance.py') --refresh
if ($LASTEXITCODE -ne 0) { throw 'Inheritance preflight failed' }
& $cfg.python -B (Join-Path $PSScriptRoot 'release_072\build.py') source --label $Label
if ($LASTEXITCODE -ne 0) { throw 'Native source build failed; logs retained' }
& $cfg.blender_python -B (Join-Path $PSScriptRoot 'release_072\native.py') --label $Label
if ($LASTEXITCODE -ne 0) { throw 'Native visual assembly failed; logs retained' }
& $cfg.python -B (Join-Path $PSScriptRoot 'release_072\package.py') --label $Label
if ($LASTEXITCODE -ne 0) { throw 'Package verification failed' }
Write-Output 'Verified 0.7.2 delivery: output\release_072\delivery'
