param(
    [ValidateSet('Verify','Validate','Source','Assets','Package','Restore','Readiness')]
    [string]$Action = 'Verify',
    [string]$Label = 'manual1',
    [string]$Key = ''
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskConfig = Get-Content -LiteralPath (Join-Path $taskRoot 'workspace.json') -Raw | ConvertFrom-Json
$taskPython = $taskConfig.python
Push-Location -LiteralPath $taskRoot
try {
    & $taskPython -B tools/verify_workspace.py --storage-only
    if ($LASTEXITCODE -ne 0) { throw 'Storage guard failed' }
    switch ($Action) {
        'Verify' { & $taskPython -B tools/consolidation_080/verify.py post }
        'Validate' { & $taskPython -B tools/consolidation_080/build.py validate $Label }
        'Source' { & $taskPython -B tools/consolidation_080/build.py source $Label }
        'Assets' { & $taskPython -B tools/consolidation_080/qualify.py $Label }
        'Package' { & $taskPython -B tools/consolidation_080/package.py $Label }
        'Restore' {
            if (-not $Key) { throw 'Supply an exact original E/ or F/ key with -Key' }
            & $taskPython -B tools/consolidation_080/store.py restore $Key
        }
        'Readiness' { & $taskPython -B tools/consolidation_080/readiness.py }
    }
    if ($LASTEXITCODE -ne 0) { throw "Consolidation action failed: $Action" }
}
finally { Pop-Location }
