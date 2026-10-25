param([switch]$VerifyOnly, [switch]$PrepareOnly, [switch]$CookOnly, [switch]$ResumeCandidate, [switch]$PackageOnly, [string]$Label = ('r' + (Get-Date -Format 'yyMMddHHmmss')))
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cfg = Get-Content -LiteralPath (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
if ($Label -notmatch '^r[a-z0-9-]{2,15}$') { throw 'Use r followed by 2-15 lowercase letters/digits/hyphens.' }
if (([int][bool]$VerifyOnly + [int][bool]$PrepareOnly + [int][bool]$CookOnly + [int][bool]$ResumeCandidate + [int][bool]$PackageOnly) -gt 1) { throw 'Choose only one release stage switch.' }
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "0.3.0 command failed ($LASTEXITCODE): $Executable" }
}
$nativeLock = $null
$oldLocation = Get-Location
$oldBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    Set-Location -LiteralPath $root
    $env:PYTHONDONTWRITEBYTECODE = '1'
    Invoke-Checked $cfg.python @('-B', 'tools\verify_workspace.py', '--storage-only')
    Invoke-Checked $cfg.blender_python @('-B', 'tools\release_030\freeze_baseline.py', '--verify-only')
    if ($VerifyOnly -or $PackageOnly) {
        Invoke-Checked $cfg.blender_python @('-B', 'tools\release_030\source_policy.py', 'verify')
        if ($VerifyOnly) { Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\release.py', 'verify-only') }
        else { Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\release.py', 'package') }
    } else {
        $nativeLock = [System.IO.File]::Open((Join-Path $cfg.external_root 'output\release_020\native-build.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
        if ($ResumeCandidate) {
            Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\release.py', 'qualify', $Label)
            Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\release.py', 'compose', $Label)
        } else {
        Invoke-Checked $cfg.blender_python @('-B', 'tools\release_030\inventory.py')
        Invoke-Checked $cfg.blender_python @('-B', 'tools\release_030\bindings.py', 'prepare')
        Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\bindings.py', 'cook-identities', $Label)
        Invoke-Checked $cfg.blender_python @('-B', 'tools\release_030\bindings.py', 'bind')
        Invoke-Checked $cfg.blender_python @('-B', 'tools\release_030\footprint.py', 'prepare')
        Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\footprint.py', 'compile', $Label)
        if ($CookOnly) {
            Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\release.py', 'candidate', $Label)
        } elseif (-not $PrepareOnly) {
            Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_030\release.py', 'rebuild', $Label)
        }
        }
    }
    if (-not $PrepareOnly -and -not $CookOnly -and -not $ResumeCandidate) { Invoke-Checked $cfg.blender_python @('-B', 'tools\release_030\finalize.py') }
} finally {
    if ($null -ne $nativeLock) { $nativeLock.Dispose() }
    if ($null -eq $oldBytecode) { Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue }
    else { $env:PYTHONDONTWRITEBYTECODE = $oldBytecode }
    Set-Location -LiteralPath $oldLocation
}
