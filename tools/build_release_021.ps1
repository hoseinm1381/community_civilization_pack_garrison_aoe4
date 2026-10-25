param([switch]$VerifyOnly, [string]$Label = ('r' + (Get-Date -Format 'yyMMddHHmmss')))
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cfg = Get-Content -LiteralPath (Join-Path $root 'workspace.json') -Raw | ConvertFrom-Json
if ($Label -notmatch '^r[a-z0-9-]{2,15}$') { throw 'Use r followed by 2–15 lowercase letters/digits/hyphens.' }
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "0.2.1 command failed ($LASTEXITCODE): $Executable" }
}
$nativeLock = $null
$oldLocation = Get-Location
$oldBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    Set-Location -LiteralPath $root
    $env:PYTHONDONTWRITEBYTECODE = '1'
    Invoke-Checked $cfg.python @('-B', 'tools\verify_workspace.py', '--storage-only')
    Invoke-Checked $cfg.blender_python @('-B', 'tools\release_021\footprint.py', 'verify-source')
    if ($VerifyOnly) {
        Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_021\release.py', 'verify-only')
    } else {
        $nativeLock = [System.IO.File]::Open((Join-Path $cfg.external_root 'output\release_020\native-build.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
        Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_021\footprint.py', 'compile', $Label)
        Invoke-Checked $cfg.blender_python @('-u', '-B', 'tools\release_021\release.py', 'rebuild', $Label)
    }
    Invoke-Checked $cfg.python @('-B', 'tools\release_021\finalize.py')
} finally {
    if ($null -ne $nativeLock) { $nativeLock.Dispose() }
    if ($null -eq $oldBytecode) { Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue }
    else { $env:PYTHONDONTWRITEBYTECODE = $oldBytecode }
    Set-Location -LiteralPath $oldLocation
}
