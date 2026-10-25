param(
    [switch]$PrepareOnly,
    [switch]$CookOnly,
    [switch]$ResumeCandidate,
    [switch]$PackageOnly,
    [switch]$VerifyOnly,
    [string]$Label = ('r' + (Get-Date -Format 'yyMMddHHmmss'))
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cfg = Get-Content -LiteralPath (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
if ($Label -notmatch '^r[a-z0-9-]{2,15}$') { throw 'Use r followed by 2-15 lowercase letters, digits, or hyphens.' }
if (([int][bool]$PrepareOnly + [int][bool]$CookOnly + [int][bool]$ResumeCandidate + [int][bool]$PackageOnly + [int][bool]$VerifyOnly) -gt 1) {
    throw 'Choose one release stage switch.'
}
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "0.4.0 command failed ($LASTEXITCODE): $Executable" }
}
$nativeLock = $null
$oldLocation = Get-Location
$oldBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    Set-Location -LiteralPath $root
    $env:PYTHONDONTWRITEBYTECODE = '1'
    Invoke-Checked $cfg.python @('-B','tools\verify_workspace.py','--storage-only')
    Invoke-Checked $cfg.blender_python @('-B','tools\release_040\freeze_baseline.py','--verify-post-edit')
    if ($VerifyOnly) {
        Invoke-Checked $cfg.blender_python @('-B','tools\release_040\source_policy.py')
        Invoke-Checked $cfg.blender_python @('-B','tools\release_040\release.py','verify')
    } elseif ($PackageOnly) {
        Invoke-Checked $cfg.blender_python @('-B','tools\release_040\release.py','package')
        Invoke-Checked $cfg.blender_python @('-B','tools\release_040\finalize.py')
    } elseif ($ResumeCandidate) {
        Invoke-Checked $cfg.blender_python @('-B','tools\release_040\release.py','compose',$Label)
        Invoke-Checked $cfg.blender_python @('-B','tools\release_040\release.py','verify')
    } else {
        Invoke-Checked $cfg.blender_python @('-B','tools\release_040\bindings.py','prepare')
        if (-not $PrepareOnly) {
            $nativeLock = [System.IO.File]::Open((Join-Path $cfg.external_root 'output\release_020\native-build.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_040\bindings.py','cook-identities',$Label)
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\bindings.py','bind')
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\bindings.py','bind-buildings')
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\credits.py')
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\source_policy.py')
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\checks.py')
            # Qualify the two native ruined landmarks before the 12-building batch.
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_040\landmark_media.py','cook',$Label)
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\landmark_media.py','assemble')
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_040\reference.py',$Label)
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_040\native_source.py','compile',$Label)
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\lifecycle_contract.py')
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\building_media.py')
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_040\detail_media.py','cook',$Label)
            Invoke-Checked $cfg.blender_python @('-B','tools\release_040\detail_media.py','assemble')
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_040\reference.py',$Label,'details')
            if (-not $CookOnly) {
                Invoke-Checked $cfg.blender_python @('-B','tools\release_040\release.py','compose',$Label)
                Invoke-Checked $cfg.blender_python @('-B','tools\release_040\release.py','package')
                Invoke-Checked $cfg.blender_python @('-B','tools\release_040\finalize.py')
            }
        }
    }
} finally {
    if ($null -ne $nativeLock) { $nativeLock.Dispose() }
    if ($null -eq $oldBytecode) { Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue }
    else { $env:PYTHONDONTWRITEBYTECODE = $oldBytecode }
    Set-Location -LiteralPath $oldLocation
}
