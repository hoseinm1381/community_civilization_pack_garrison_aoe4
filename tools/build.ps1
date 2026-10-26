param(
    [string]$EditorRoot = '',
    [string]$PythonPath = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $projectRoot 'workspace.local.json'
$config = if (Test-Path -LiteralPath $configPath) { Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json } else { $null }
if (-not $EditorRoot -and $config) { $EditorRoot = $config.editor_root }
if (-not $PythonPath) { $PythonPath = if ($config -and $config.python_path) { $config.python_path } else { 'python' } }
if (-not $EditorRoot) { throw 'Set editor_root in workspace.local.json or pass -EditorRoot.' }
& $PythonPath (Join-Path $PSScriptRoot 'verify_source.py')
if ($LASTEXITCODE -ne 0) { throw 'Portable source validation failed; no build was started.' }
$previousEditorRoot = $env:AOE4_EDITOR_ROOT
try {
    $env:AOE4_EDITOR_ROOT = $EditorRoot
    & $PythonPath (Join-Path $PSScriptRoot 'check_extension_inheritance.py') --refresh
    if ($LASTEXITCODE -ne 0) { throw 'Inherited extension validation failed; no build was started.' }
} finally { $env:AOE4_EDITOR_ROOT = $previousEditorRoot }
$project = Join-Path $projectRoot 'Community_Civilization_Pack_Normal.aoe4mod'
$buildRoot = Join-Path $projectRoot 'output\editor-build'
$log = Join-Path $projectRoot 'output\editor-burn.log'
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
# These options were verified in the installed BuildApplet/BuildOptions.
# build_path contains all installed output inside this new workspace.
$arguments = @('-build_mod', ('"' + $project + '"'), '-build_path', ('"' + $buildRoot + '"'),
    '-no_burn_window', '-burn_platform', 'PC', '-burn_log_path', ('"' + $log + '"'))
$process = Start-Process -FilePath (Join-Path $EditorRoot 'EssenceEditor.exe') -WorkingDirectory $EditorRoot -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
Write-Output ('Content Editor exit code: ' + $process.ExitCode)
Write-Output ('Verify the completed native burn and errors in ' + $log)
if ($process.ExitCode -ne 0) { exit $process.ExitCode }
