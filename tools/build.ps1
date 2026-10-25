param([string]$EditorRoot = '', [switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'workspace.ps1')
$configuration = Get-PreparedWorkspace -Identity
$projectRoot = Split-Path -Parent $PSScriptRoot
$project = Join-Path $projectRoot $configuration.project_file
$editor = $configuration.content_editor
if ($EditorRoot) { $editor = Join-Path $EditorRoot 'EssenceEditor.exe' }
if (-not (Test-Path -LiteralPath $editor -PathType Leaf)) { throw "Content Editor unavailable: $editor" }
$buildRoot = Join-Path $projectRoot 'output\editor-build'
$log = Join-Path $projectRoot 'output\editor-burn.log'
$arguments = @('-rtm', '--safe_settings', '--do_not_restore', '--quiet_crash_report', '--no_source_control',
    '--build_mod', ('"' + $project + '"'), '--build_path', ('"' + $buildRoot + '"'),
    '--no_burn_window', '--burn_platform', 'PC', '--burn_log_path', ('"' + $log + '"'))
if ($ValidateOnly) {
    [PSCustomObject]@{status='validated-only'; editor=$editor; project=$project;
        output=$buildRoot; log=$log; arguments=$arguments; editor_launched=$false} | ConvertTo-Json
    return
}
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
$process = Start-Process -FilePath $editor -WorkingDirectory (Split-Path -Parent $editor) -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
Write-Output ('Content Editor exit code: ' + $process.ExitCode)
if ($process.ExitCode -ne 0) { exit $process.ExitCode }
