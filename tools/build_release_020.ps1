param(
    [switch]$VerifyOnly,
    [string]$CandidatePath,
    [string]$Label = ('r' + (Get-Date -Format 'yyMMddHHmmss'))
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cfg = Get-Content -LiteralPath (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
if ($VerifyOnly -and $CandidatePath) { throw 'Choose VerifyOnly or CandidatePath, not both.' }
if ($Label -notmatch '^[a-z][a-z0-9-]{1,15}$') {
    throw 'Label must be 2–16 lowercase letters/digits/hyphens, beginning with a letter.'
}
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "0.2.0 release command failed ($LASTEXITCODE): $Executable $($Arguments -join ' ')"
    }
}
$previousLocation = Get-Location
$previousNoBytecode = $env:PYTHONDONTWRITEBYTECODE
$nativeLock = $null
try {
    Set-Location -LiteralPath $root
    $env:PYTHONDONTWRITEBYTECODE = '1'
    # Availability/junction checks precede every build/cache/output operation.
    Invoke-Checked $cfg.python @('-B', 'tools\verify_workspace.py', '--storage-only')
    Invoke-Checked $cfg.python @('-B', 'tools\release_020\freeze_art.py', '--verify-only')
    if ($VerifyOnly) {
        Invoke-Checked $cfg.blender_python @('-B', 'tools\release_020\release_pipeline.py', 'verify-only')
    } else {
        $outputRoot = Join-Path $cfg.external_root 'output\release_020'
        if (-not (Test-Path -LiteralPath (Join-Path $outputRoot 'baseline-freeze.json'))) {
            throw 'The immutable 0.2.0 baseline receipt is missing; do not regenerate it from edited source.'
        }
        $nativeLock = [System.IO.File]::Open((Join-Path $outputRoot 'native-build.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
        if ($CandidatePath) {
            Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_020\release_pipeline.py', 'resume', $CandidatePath)
        } else {
            Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_020\release_pipeline.py', 'rebuild', $Label)
        }
    }
    Write-Output 'Garrison 0.2.0 release verification passed. Native appearance remains a separate user test.'
} finally {
    if ($null -ne $nativeLock) { $nativeLock.Dispose() }
    if ($null -eq $previousNoBytecode) {
        Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue
    } else {
        $env:PYTHONDONTWRITEBYTECODE = $previousNoBytecode
    }
    Set-Location -LiteralPath $previousLocation
}
