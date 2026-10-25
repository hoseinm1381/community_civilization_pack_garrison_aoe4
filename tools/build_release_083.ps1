param(
    [ValidateSet('Verify','Cook','QA','Package')][string]$Action='Verify',
    [ValidatePattern('^[a-z0-9-]{1,24}$')][string]$Label='v3',
    [ValidatePattern('^[a-z0-9-]{1,24}$')][string]$QALabel='qa-new'
)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskConfig=Get-Content -LiteralPath (Join-Path $taskRoot 'workspace.json') -Raw | ConvertFrom-Json
Push-Location -LiteralPath $taskRoot
try {
    & $taskConfig.python -B tools/verify_workspace.py --storage-only
    if ($LASTEXITCODE -ne 0) { throw 'Storage guard failed' }
    & $taskConfig.blender_python -B tools/release_083/test_policy.py
    if ($LASTEXITCODE -ne 0) { throw '0.8.3 policy failed' }
    switch ($Action) {
        'Verify' { & $taskConfig.blender_python -B tools/release_083/verify.py }
        'Cook' {
            & $taskConfig.blender_python -B tools/release_083/cook.py $Label
            if ($LASTEXITCODE -ne 0) { throw 'Native art cook failed' }
            & $taskConfig.blender_python -B tools/release_083/decode.py $Label
        }
        'QA' { & $taskConfig.blender -b --python-exit-code 1 --python tools/release_083/qa.py -- $Label $QALabel }
        'Package' { & $taskConfig.blender_python -B tools/release_083/package.py $Label }
    }
    if ($LASTEXITCODE -ne 0) { throw "0.8.3 action failed: $Action" }
}
finally { Pop-Location }
