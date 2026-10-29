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
$nativeLogRoot = Join-Path $buildRoot 'native-logs'
$intermediate = Join-Path $buildRoot 'intermediate'
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $nativeLogRoot | Out-Null
New-Item -ItemType Directory -Force -Path $intermediate | Out-Null
# These options were verified in the installed BuildApplet/BuildOptions.
# The native parser uses double-dash flags. A single-dash invocation may exit
# successfully without running BuildApplet. Keep generated output inside output/.
$arguments = @('-rtm', '--safe_settings', '--do_not_restore', '--quiet_crash_report',
    '--no_source_control', '--log_path', ('"' + $nativeLogRoot + '"'),
    '--build_mod', ('"' + $project + '"'), '--build_path', ('"' + $buildRoot + '"'),
    '--intermediate_path', ('"' + $intermediate + '"'), '--burn_cache_type', 'Local',
    '--burn_max_threads', '1', '--no_burn_window', '--burn_platform', 'PC',
    '--burn_log_path', ('"' + $log + '"'))
$started = Get-Date
$process = Start-Process -FilePath (Join-Path $EditorRoot 'EssenceEditor.exe') -WorkingDirectory $EditorRoot -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
Write-Output ('Content Editor exit code: ' + $process.ExitCode)
Write-Output ('Verify the completed native burn and errors in ' + $log)
if ($process.ExitCode -ne 0) { exit $process.ExitCode }
if (-not (Test-Path -LiteralPath $log) -or (Get-Item -LiteralPath $log).LastWriteTime -lt $started) {
    throw 'No fresh native burn log was produced; exit code zero is not build proof.'
}
$installedOutput = Join-Path $buildRoot 'extension\Community_Civilization_Pack_Normal'
$archives = @(Get-ChildItem -LiteralPath $installedOutput -Filter '*.sga' -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt 0 -and $_.LastWriteTime -ge $started })
if ($archives.Count -ne 1) {
    throw 'Expected one fresh, nonempty Normal SGA in the build output; inspect the native logs.'
}
if (Select-String -LiteralPath $log -Pattern '^\(E\)' -Quiet) {
    throw 'Native burn log contains errors; inspect it before packaging.'
}
Write-Output ('Fresh native archive: ' + $archives[0].FullName)
