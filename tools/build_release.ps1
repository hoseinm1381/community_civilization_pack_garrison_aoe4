param(
    [switch]$VerifyOnly,
    [string]$CandidatePath,
    [string]$Label = ('r' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cfg = Get-Content (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
$releaseOutput = Join-Path $cfg.external_root 'output\release_010'
if ($Label -notmatch '^[a-z][a-z0-9-]{1,24}$') { throw 'Label must be 2-25 lowercase letters/digits/hyphens, beginning with a letter.' }
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Release command failed ($LASTEXITCODE): $Executable $($Arguments -join ' ')" }
}
$previousLocation = Get-Location
$buildLock = $null
try {
    Set-Location $root
    Invoke-Checked $cfg.python @('-B', 'tools\verify_workspace.py')
    Invoke-Checked $cfg.python @('-B', 'tools\release_010\freeze_baseline.py')
    $pointer = Join-Path $releaseOutput 'current-candidate.json'
    if ($CandidatePath) {
        $candidate = $CandidatePath
    } elseif ($VerifyOnly) {
        $candidate = if (Test-Path -LiteralPath $pointer) {
            (Get-Content -LiteralPath $pointer -Raw | ConvertFrom-Json).candidate
        } else { Join-Path $releaseOutput 'integration\candidate.json' }
    } else {
        # FileShare.None prevents another invocation of this native build helper.
        # Direct Blender/Garrison cooks must also remain serialized by the operator.
        $buildLock = [System.IO.File]::Open((Join-Path $releaseOutput 'native-build.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
        Invoke-Checked $cfg.blender_python @('-B', 'tools\release_010\integration.py', 'rebuild', $Label)
        $rebuild = Get-Content (Join-Path $releaseOutput "rebuild-$Label.json") -Raw | ConvertFrom-Json
        if ($rebuild.status -ne 'passed') { throw 'Native release rebuild did not pass.' }
        $candidate = $rebuild.candidate
    }
    Invoke-Checked $cfg.python @('-B', 'tools\release_010\release_checks.py', '--candidate', $candidate)
    Invoke-Checked $cfg.python @('-B', 'tools\release_010\verify_archive.py', '--candidate', $candidate)
    $packageArgs = @('-B', 'tools\release_010\package_release.py', '--candidate', $candidate)
    if ($VerifyOnly) { $packageArgs += '--verify-only' }
    Invoke-Checked $cfg.python $packageArgs
    if (-not $VerifyOnly) {
        @{candidate=$candidate; label=$Label; status='passed'} | ConvertTo-Json | Set-Content -LiteralPath $pointer -Encoding utf8
        Invoke-Checked $cfg.python @('-B', 'tools\release_010\cleanup_release.py', '--apply')
        Invoke-Checked $cfg.python @('-B', 'tools\release_010\report_release.py', '--candidate', $candidate)
    }
    Write-Output "Garrison 0.1.0 release checks passed: $candidate"
} finally {
    if ($null -ne $buildLock) { $buildLock.Dispose() }
    Set-Location $previousLocation
}
