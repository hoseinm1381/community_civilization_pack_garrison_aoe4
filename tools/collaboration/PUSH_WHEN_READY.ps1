param([switch]$Execute)
& (Join-Path $PSScriptRoot '../compact/PUBLISH.ps1') -Execute:$Execute
exit $LASTEXITCODE
