param([string]$Label = 'final-v1')
$ErrorActionPreference = 'Stop'
$releaseRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $releaseRoot
$config = Get-Content workspace.json -Raw | ConvertFrom-Json
& $config.python tools/verify_workspace.py --storage-only
if ($LASTEXITCODE -ne 0) { throw 'Storage verification failed' }
& $config.blender_python -B tools/release_0710/test_package_policy.py
if ($LASTEXITCODE -ne 0) { throw 'Package regression failed' }
& $config.python -B tests/test_hud_0710.py
if ($LASTEXITCODE -ne 0) { throw 'HUD regression failed' }
& $config.blender_python -B tools/release_0710/source_policy.py
if ($LASTEXITCODE -ne 0) { throw 'Source preservation failed' }
& $config.blender_python -B tools/release_0710/validate_source.py
if ($LASTEXITCODE -ne 0) { throw 'Current official/static validation failed' }
# Consumes reviewed immutable art cooks and UI payloads. Reproduction commands
# are retained in docs/RELEASE_0710_REPORT.md and each family receipt.
& $config.blender_python -B tools/release_0710/package_final.py --label $Label
if ($LASTEXITCODE -ne 0) { throw 'Final package verification failed' }
