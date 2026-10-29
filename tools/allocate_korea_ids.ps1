param([string]$EditorRoot = '')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$config = Get-Content -LiteralPath (Join-Path $root 'workspace.local.json') -Raw | ConvertFrom-Json
if (-not $EditorRoot) { $EditorRoot = $config.editor_root }
$work = Join-Path $root 'work/korea_port'
$receipt = Join-Path $work 'identities.json'
if (Test-Path -LiteralPath $receipt) { throw 'Reuse the Korea identity receipt; do not allocate again.' }
$assemblyPath = Join-Path $EditorRoot 'Essence.Editor.Modding.dll'
$assembly = [Reflection.Assembly]::LoadFrom($assemblyPath)
$domainType = $assembly.GetType('Essence.Editor.Modding.Wizards.AttributePrerequisite+InitialUniqueIDDomain', $true)
$domain = $domainType.GetConstructor([Reflection.BindingFlags]'Public,NonPublic,Instance', $null, [type[]]@([bool]), $null).Invoke(@($true))
foreach ($id in (Get-Content -LiteralPath (Join-Path $work 'reserved-ids.json') -Raw | ConvertFrom-Json)) {
    $domain.OnGenerated('ebps', [int]$id)
}
$generator = [Activator]::CreateInstance($assembly.GetType('Essence.Editor.Modding.Attributes.UniqueIDGenerator', $true))
$ids = [Collections.Generic.List[int]]::new()
foreach ($slot in 1..512) {
    $id = $generator.GenerateNext($domain, 'ebps')
    $domain.OnGenerated('ebps', $id)
    $ids.Add($id)
}
[ordered]@{
    generator = 'Essence.Editor.Modding.Attributes.UniqueIDGenerator.GenerateNext'
    assembly_sha256 = (Get-FileHash -LiteralPath $assemblyPath -Algorithm SHA256).Hash.ToLower()
    ids = @($ids)
    scope = 'Private Korean PBGs and any necessary new list items. No Content Editor burn.'
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receipt -Encoding utf8
Write-Output ('Allocated ' + $ids.Count + ' identities into ' + $receipt)
