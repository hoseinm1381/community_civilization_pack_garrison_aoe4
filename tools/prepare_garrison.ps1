param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'workspace.ps1')
$configuration = Get-PreparedWorkspace
$projectRoot = Split-Path -Parent $PSScriptRoot
$project = Join-Path $projectRoot $configuration.garrison_project
$recordPath = Join-Path $project 'mod-project.json'
if ($CheckOnly) {
    $null = Get-PreparedWorkspace -Identity
    & $configuration.garrison_core mod-project show --project $project
    if ($LASTEXITCODE -ne 0) { throw 'Garrison project inspection failed' }
    return
}
if (Test-Path -LiteralPath $recordPath) {
    $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
    if ($record.key -ne $configuration.package_key -or $record.mod_id -ne $configuration.project_guid) {
        throw 'Existing Garrison project identity differs; refusing to overwrite it'
    }
} else {
    if (Test-Path -LiteralPath $project) { throw 'Incomplete Garrison project exists; preserve it for inspection' }
    & $configuration.garrison_core mod-project create --library (Join-Path $projectRoot 'art\garrison_library') --name $configuration.package_key
    if ($LASTEXITCODE -ne 0) { throw 'Garrison project creation failed' }
}
& $configuration.garrison_core mod-project settings --project $project --mod-id $configuration.project_guid --live-reload off --game-mode off --version $configuration.version --summary 'Community civilization collection; Vietnam baseline, prepared for future Garrison assets.' --description 'Community Civilization Pack. Existing Vietnam gameplay is owned by the Content Editor source; this project owns future art only.'
if ($LASTEXITCODE -ne 0) { throw 'Garrison project settings failed' }
$null = Get-PreparedWorkspace -Identity
Write-Output 'Garrison workspace prepared. No cook, package, install, or Blender edit was performed.'
