param(
    [ValidateSet('Verify','CookBuffalo','CookMinistry','Package')]
    [string]$Action='Verify',
    [ValidatePattern('^[a-z0-9-]{1,12}$')][string]$Label=''
)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskConfig=Get-Content -LiteralPath (Join-Path $taskRoot 'workspace.json') -Raw | ConvertFrom-Json
Push-Location -LiteralPath $taskRoot
try {
    & $taskConfig.python -B tools/verify_workspace.py --storage-only
    if ($LASTEXITCODE -ne 0) { throw 'Storage guard failed' }
    switch ($Action) {
        'Verify' {
            & $taskConfig.python -B tools/release_081/test_policy.py
            if ($LASTEXITCODE -ne 0) { throw 'Preservation policies failed' }
            & $taskConfig.python -B tools/release_081/verify_release.py
        }
        'CookBuffalo' {
            if (-not $Label) { throw 'Supply a new immutable -Label for the cook attempt' }
            & $taskConfig.blender_python -B tools/release_081/run.py cook $Label r6
            if ($LASTEXITCODE -ne 0) { throw 'Native buffalo cook failed' }
            & $taskConfig.blender_python -B tools/release_081/run.py decode $Label
        }
        'CookMinistry' {
            if (-not $Label) { throw 'Supply a new immutable -Label for the cook attempt' }
            & $taskConfig.blender_python -B tools/release_081/cook_ministry.py ministry --label $Label --revision r2
            if ($LASTEXITCODE -ne 0) { throw 'Native Ministry cook failed' }
            & $taskConfig.blender_python -B tools/release_081/assemble_ministry.py ministry --label $Label
        }
        'Package' {
            # Frozen selection, immutable delivery. Later edits require a new policy.
            & $taskConfig.blender_python -B tools/release_081/package.py v3 r6
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "0.8.1 action failed: $Action" }
}
finally { Pop-Location }
