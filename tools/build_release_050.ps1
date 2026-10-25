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
if ($Label -notmatch '^r[a-z0-9-]{2,15}$') { throw 'Invalid fresh run label.' }
if (([int][bool]$PrepareOnly + [int][bool]$CookOnly + [int][bool]$ResumeCandidate + [int][bool]$PackageOnly + [int][bool]$VerifyOnly) -gt 1) { throw 'Choose one stage.' }
function Invoke-Checked {
    param([string]$Executable,[string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "0.5.0 command failed ($LASTEXITCODE): $Executable" }
}
$oldLocation = Get-Location
$oldBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    Set-Location -LiteralPath $root
    $env:PYTHONDONTWRITEBYTECODE = '1'
    Invoke-Checked $cfg.python @('-B','tools\verify_workspace.py','--storage-only')
    Invoke-Checked $cfg.blender_python @('-B','tools\release_050\freeze_baseline.py','--verify-post-edit')
    if ($VerifyOnly) {
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\release.py','verify')
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\checks.py')
    } elseif ($PackageOnly) {
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\release.py','package')
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\finalize.py')
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\report.py')
    } elseif ($ResumeCandidate) {
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\release.py','compose',$Label)
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\release.py','verify')
    } else {
        # Castle authoring/export/art qualification is a separate serialized
        # stage. Require its exact frozen media before binding or compiling.
        Invoke-Checked $cfg.blender_python @('-B','tools\castle_next\checks.py')
        Invoke-Checked $cfg.blender_python @('-B','tools\release_050\bindings.py','prepare')
        if (-not $PrepareOnly) {
            # Each native child acquires the shared lock itself. An outer
            # FileShare.None handle would prevent that child's open on Windows.
            if (-not (Test-Path -LiteralPath (Join-Path $cfg.external_root 'output\release_050\integration\identity-cook-pointer.json'))) {
                Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_050\bindings.py','cook-identities',$Label)
            }
            Invoke-Checked $cfg.blender_python @('-B','tools\release_050\bindings.py','bind-sources')
            Invoke-Checked $cfg.blender_python @('-B','tools\release_050\bindings.py','assemble')
            Invoke-Checked $cfg.blender_python @('-B','tools\release_050\source_policy.py')
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\release_050\native_source.py','compile',$Label)
            Invoke-Checked $cfg.blender_python @('-u','-B','tools\castle_next\cook.py','reference','landmarks',$Label,'--with-branches')
            if (-not $CookOnly) {
                Invoke-Checked $cfg.blender_python @('-B','tools\release_050\release.py','compose',$Label)
                Invoke-Checked $cfg.blender_python @('-B','tools\release_050\release.py','package')
                Invoke-Checked $cfg.blender_python @('-B','tools\release_050\finalize.py')
                Invoke-Checked $cfg.blender_python @('-B','tools\release_050\report.py')
            }
        }
    }
} finally {
    if ($null -eq $oldBytecode) { Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue }
    else { $env:PYTHONDONTWRITEBYTECODE = $oldBytecode }
    Set-Location -LiteralPath $oldLocation
}
