param([string]$Label='final-v1',[string]$NativeLabel='v1')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$releaseConfig=Get-Content workspace.json -Raw | ConvertFrom-Json
& $releaseConfig.python tools/verify_workspace.py --storage-only
if ($LASTEXITCODE -ne 0) {throw 'Storage guard failed'}
& $releaseConfig.blender_python -B tools/release_0711/validate.py
if ($LASTEXITCODE -ne 0) {throw 'Source/static validation failed'}
# Consumes the completed immutable native_compile.py attempt named NativeLabel.
& $releaseConfig.blender_python -B tools/release_0711/package.py --label $Label --native-label $NativeLabel
if ($LASTEXITCODE -ne 0) {throw 'Package verification failed'}
