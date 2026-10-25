param([ValidateSet('status','dialogue','effort','stock','recheck','compress','verify','listen')][string]$Phase='status',
      [ValidateSet(3,5)][int]$AttemptCeiling=3)
$ErrorActionPreference='Stop'
$releaseRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $releaseRoot
$resumeConfig=Get-Content -LiteralPath 'workspace.json' -Raw | ConvertFrom-Json
& $resumeConfig.python -B -c "import sys;sys.path.insert(0,'tools/release_084');from pipeline import guard;guard()"
if ($LASTEXITCODE -ne 0) { throw 'Storage preflight failed' }
if ($Phase -eq 'status') {
    $voiceStatusCode=@'
import sys,json
sys.path.insert(0,'tools/release_084')
from providers import OUT
from voice_scope import delivery_manifest
from local_bank_validation import coverage
bank=OUT/'local'
manifest=delivery_manifest(json.loads((bank/'recording-manifest.json').read_text()))
state=json.loads((bank/'generation/state.json').read_text())
result=coverage(manifest,set(state))
result.pop('missing_jobs')
result['note']='Accepted checkpoint counts; this is not a fresh audio or native-game audit.'
result['cooperative_stop_present']=(bank/'generation/STOP').exists()
print(json.dumps(result,indent=2))
'@
    & $resumeConfig.python -B -c $voiceStatusCode
    if($LASTEXITCODE -ne 0){throw 'Current status read failed'}
    return
}
if ($Phase -eq 'effort' -and (Test-Path -LiteralPath 'output/release_084/local/delivery-scope.json')) {
    throw 'Custom effort generation is outside the approved spoken-only scope. Use -Phase stock for existing stock effort media.'
}
. "$PSScriptRoot\local_env.ps1"
$voicePython="$localVoiceRoot\venv\Scripts\python.exe"
if ($Phase -in @('dialogue','effort')) {
    $stopMarker=Join-Path $releaseRoot 'output/release_084/local/generation/STOP'
    if (Test-Path -LiteralPath $stopMarker) {
        Move-Item -LiteralPath $stopMarker -Destination ($stopMarker+'.resumed-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
    }
}
switch ($Phase) {
    'dialogue' { & $voicePython "$PSScriptRoot\local_batch.py" --kind dialogue --limit 10000 --max-attempts 30000 --attempt-ceiling $AttemptCeiling }
    'effort' { & $voicePython "$PSScriptRoot\local_batch.py" --kind effort --limit 1000 --max-attempts 2500 }
    'stock' { & $voicePython "$PSScriptRoot\stock_export.py" }
    'recheck' { & $voicePython "$PSScriptRoot\local_recheck.py" --attempt-ceiling $AttemptCeiling }
    'compress' { & $voicePython "$PSScriptRoot\local_compress.py" }
    'verify' { & $voicePython "$PSScriptRoot\local_bank_validation.py" }
    'listen' {
        $listenLabel='all-local-compressed-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ').ToLowerInvariant()
        & $voicePython "$PSScriptRoot\local_listening_package.py" --all --compressed --label $listenLabel
    }
}
if ($LASTEXITCODE -ne 0) { throw "Resume phase failed: $Phase. Preserve diagnostics and checkpoint." }
