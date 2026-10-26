param([string]$EditorRoot = 'E:\Games\steamapps\common\Age of Empires IV')
$ErrorActionPreference = 'Stop'
$work = Join-Path $PSScriptRoot '../work/persia_full_20261026'
$receipt = Join-Path $work 'identities.json'
if (Test-Path -LiteralPath $receipt) { throw 'Reuse the preserved identity receipt; do not allocate again.' }
$assembly = [Reflection.Assembly]::LoadFrom((Join-Path $EditorRoot 'Essence.Editor.Modding.dll'))
$domainType = $assembly.GetType('Essence.Editor.Modding.Wizards.AttributePrerequisite+InitialUniqueIDDomain', $true)
$domain = $domainType.GetConstructor([Reflection.BindingFlags]'Public,NonPublic,Instance', $null, [type[]]@([bool]), $null).Invoke(@($true))
foreach ($id in (Get-Content -LiteralPath (Join-Path $work 'reserved-ids.json') -Raw | ConvertFrom-Json)) { $domain.OnGenerated('ebps', [int]$id) }
$generator = [Activator]::CreateInstance($assembly.GetType('Essence.Editor.Modding.Attributes.UniqueIDGenerator', $true))
$ids = [Collections.Generic.List[int]]::new()
foreach ($slot in 1..282) {
    $id = $generator.GenerateNext($domain, 'ebps')
    $domain.OnGenerated('ebps', $id)
    $ids.Add($id)
}
[ordered]@{
    generator = 'Essence.Editor.Modding.Attributes.UniqueIDGenerator.GenerateNext'
    assembly_sha256 = (Get-FileHash -LiteralPath (Join-Path $EditorRoot 'Essence.Editor.Modding.dll') -Algorithm SHA256).Hash.ToLower()
    pbg_ids = @($ids.GetRange(0,281))
    requirement_item_id = $ids[281]
    scope = '280 private source clones, one lifecycle marker, one native requirement-list item. No native compile.'
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receipt -Encoding utf8
Write-Output ('Allocated 281 PBG IDs and one requirement item identity into ' + $receipt)
