param([string]$CookLabel = 'prod-v2')
$ErrorActionPreference = 'Stop'
$releaseRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $releaseRoot
$config = Get-Content workspace.json -Raw | ConvertFrom-Json
& $config.python tools/verify_workspace.py --storage-only
if ($LASTEXITCODE -ne 0) { throw 'Storage verification failed' }
# Garrison ships version-specific Python modules: use its matching Blender runtime.
& $config.blender_python tools/release_079/test_rig_contract.py
if ($LASTEXITCODE -ne 0) { throw 'Rig regression failed' }
& $config.blender_python tools/release_079/decode_pilot.py $CookLabel
if ($LASTEXITCODE -ne 0) { throw 'Cook readback failed' }
& $config.blender_python tools/release_079/package_final.py $CookLabel
if ($LASTEXITCODE -ne 0) { throw 'Final package verification failed' }
