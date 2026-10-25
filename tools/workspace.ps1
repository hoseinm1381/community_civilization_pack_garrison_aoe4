$ErrorActionPreference = 'Stop'

function Get-PreparedWorkspace {
    param([switch]$Identity)
    $workspaceRoot = Split-Path -Parent $PSScriptRoot
    $configuration = Get-Content -LiteralPath (Join-Path $workspaceRoot 'workspace.json') -Raw | ConvertFrom-Json
    if (-not (Test-Path -LiteralPath $configuration.external_root -PathType Container)) {
        throw "External storage unavailable: $($configuration.external_root). Connect F:; no folders were created."
    }
    if (-not (Test-Path -LiteralPath $configuration.python -PathType Leaf)) {
        throw "Configured Python unavailable: $($configuration.python). Resolve workspace dependencies before continuing."
    }
    $verificationArguments = @('-B', (Join-Path $PSScriptRoot 'verify_workspace.py'))
    if (-not $Identity) { $verificationArguments += '--storage-only' }
    $verificationOutput = & $configuration.python @verificationArguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($verificationOutput -join [Environment]::NewLine) }
    return $configuration
}
