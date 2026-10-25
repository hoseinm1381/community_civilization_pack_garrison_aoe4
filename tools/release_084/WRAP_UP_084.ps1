$ErrorActionPreference='Stop'
$releaseRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $releaseRoot
$cfg=Get-Content workspace.json -Raw|ConvertFrom-Json
& $cfg.python -B -c "import sys;sys.path.insert(0,'tools/release_084');from pipeline import guard;guard()"
if($LASTEXITCODE -ne 0){throw 'Storage guard failed'}
. "$PSScriptRoot/local_env.ps1"
$voicePython="$localVoiceRoot/venv/Scripts/python.exe"
$logs='output/release_084/local/wrap-up-v1'
New-Item -ItemType Directory -Path $logs -ErrorAction Stop|Out-Null
$bank=Join-Path $releaseRoot 'output/release_084/integration/bank-wrap-up-v1'
$overlay=Join-Path $releaseRoot 'output/release_084/integration/overlay-wrap-up-v1'
Set-Content "$logs/status.txt" 'Verifying complete compressed bank'
& $voicePython -B tools/release_084/voice_bank.py --compressed --label bank-wrap-up-v1 *> "$logs/bank.log"
if($LASTEXITCODE -ne 0){throw 'Complete bank failed; retain diagnostics'}
Set-Content "$logs/status.txt" 'Creating reversible compiled voice overlay'
& $cfg.blender_python -B tools/release_084/voice_overlay.py --label overlay-wrap-up-v1 --bank $bank *> "$logs/overlay.log"
if($LASTEXITCODE -ne 0){throw 'Overlay failed; retain diagnostics'}
Set-Content "$logs/status.txt" 'Assembling ordinary ZIP and checking fresh archive extraction'
& $voicePython -B tools/release_084/assemble_release.py --label final-v1 --bank $bank --overlay $overlay *> "$logs/package.log"
if($LASTEXITCODE -ne 0){throw 'Assembly failed; retain diagnostics'}
Set-Content "$logs/status.txt" 'Package verified; native game acceptance remains pending'
Get-Content "$logs/package.log" -Tail 8
