param(
    [string]$EditorRoot = 'E:\Games\steamapps\common\Age of Empires IV',
    [string]$PythonPath = 'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
& $PythonPath (Join-Path $PSScriptRoot 'check_extension_inheritance.py') --refresh
if ($LASTEXITCODE -ne 0) { throw 'Inherited extension validation failed; Content Editor build was not started.' }
$project = Join-Path $projectRoot 'Vietnam_v2.aoe4mod'
$buildRoot = Join-Path $projectRoot 'output\editor-build'
$log = Join-Path $projectRoot 'output\editor-burn.log'
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
# These options were verified in the installed BuildApplet/BuildOptions.
# build_path contains all installed output inside this new workspace.
$arguments = @('-build_mod', ('"' + $project + '"'), '-build_path', ('"' + $buildRoot + '"'),
    '-no_burn_window', '-burn_platform', 'PC', '-burn_log_path', ('"' + $log + '"'))
$process = Start-Process -FilePath (Join-Path $EditorRoot 'EssenceEditor.exe') -WorkingDirectory $EditorRoot -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
Write-Output ('Content Editor exit code: ' + $process.ExitCode)
if ($process.ExitCode -ne 0) { exit $process.ExitCode }
