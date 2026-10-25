param([string]$Label='final-v1',[string]$NativeLabel='v2')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$releaseConfig=Get-Content workspace.json -Raw | ConvertFrom-Json
& $releaseConfig.python tools/verify_workspace.py --storage-only
if ($LASTEXITCODE -ne 0) {throw 'Storage guard failed'}
& $releaseConfig.blender_python -B tools/release_0712/validate.py
if ($LASTEXITCODE -ne 0) {throw 'Source/static validation failed'}
$releasePolicy=Get-Content output/release_0712/source-policy.json -Raw | ConvertFrom-Json
$releaseXml=@($releasePolicy.changed) | Where-Object { $_ -match '\.(xml|xaml)$' }
foreach ($releaseFile in $releaseXml) {
  $releaseReader=[System.Xml.XmlReader]::Create((Join-Path (Get-Location) $releaseFile))
  try {while ($releaseReader.Read()) {}} finally {$releaseReader.Dispose()}
}
@{passed=$true;files=$releaseXml;source_policy_sha256=(Get-FileHash output/release_0712/source-policy.json -Algorithm SHA256).Hash.ToLower();parser='System.Xml.XmlReader'} | ConvertTo-Json | Set-Content output/release_0712/validation/dotnet-xml.json
& $releaseConfig.blender_python -B tools/release_0712/package.py --label $Label --native-label $NativeLabel
if ($LASTEXITCODE -ne 0) {throw 'Package verification failed'}
