param([int[]]$WaitForProcessIds=@(),
      [ValidateSet('dialogue','recheck','compress','verify')][string]$StartPhase='dialogue')
$ErrorActionPreference='Stop'
$releaseRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $releaseRoot
$resumeConfig=Get-Content -LiteralPath 'workspace.json' -Raw|ConvertFrom-Json
& $resumeConfig.python -B -c "import sys;sys.path.insert(0,'tools/release_084');from pipeline import guard;guard()"
if($LASTEXITCODE -ne 0){throw 'Storage guard failed'}
$runStamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ').ToLowerInvariant()
$logRoot=Join-Path $releaseRoot ('output/release_084/local/continuations/'+$runStamp)
New-Item -ItemType Directory -Path $logRoot|Out-Null
$phases=@('dialogue','recheck','compress','verify')
$first=[Array]::IndexOf($phases,$StartPhase)
$statusPath=Join-Path $logRoot 'status.json'
@{stage='waiting_for_existing_worker';wait_for_process_ids=$WaitForProcessIds;attempt_ceiling=5;
  scheduled_automation=$false;log_root=$logRoot}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $statusPath
foreach($voiceWorkerId in $WaitForProcessIds){Wait-Process -Id $voiceWorkerId -ErrorAction SilentlyContinue}
for($phaseIndex=$first;$phaseIndex -lt $phases.Count;$phaseIndex++){
    if(Test-Path -LiteralPath 'output/release_084/local/generation/STOP'){
        @{stage='cooperative_stop';next_phase=$phases[$phaseIndex];attempt_ceiling=5;
          scheduled_automation=$false}|ConvertTo-Json|Set-Content -LiteralPath $statusPath
        Write-Output 'CONTINUATION_PAUSED_BY_STOP'
        return
    }
    $nextPhase=$phases[$phaseIndex]
    @{stage=$nextPhase;attempt_ceiling=5;scheduled_automation=$false;log_root=$logRoot}|
        ConvertTo-Json|Set-Content -LiteralPath $statusPath
    try{
        & "$PSScriptRoot/RESUME_LOCAL_084.ps1" -Phase $nextPhase -AttemptCeiling 5 *> (Join-Path $logRoot ($nextPhase+'.log'))
        if($LASTEXITCODE -ne 0){throw "Phase failed: $nextPhase"}
    }catch{
        @{stage='failed';phase=$nextPhase;diagnostics_retained=$true;log_root=$logRoot}|
            ConvertTo-Json|Set-Content -LiteralPath $statusPath
        throw
    }
}
$coverage=Get-Content -LiteralPath 'output/release_084/local/bank-verification.json' -Raw|ConvertFrom-Json
@{stage='verified_audio_snapshot';verified_jobs=$coverage.verified_jobs;required_jobs=$coverage.required_jobs;
  technical_coverage_complete=$coverage.technical_coverage_complete;full_mod_delivered=$false;
  scheduled_automation=$false;log_root=$logRoot}|ConvertTo-Json|Set-Content -LiteralPath $statusPath
Get-Content -LiteralPath $statusPath
