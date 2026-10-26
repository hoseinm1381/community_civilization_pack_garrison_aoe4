$ErrorActionPreference = 'Stop'
$work = Join-Path $PSScriptRoot '../../work/persia_port_20261026'
$receipt = Join-Path $work 'identities.json'
if (Test-Path -LiteralPath $receipt) { throw 'Identity receipt exists; preserve and reuse it.' }
$editorRoot = 'E:\Games\steamapps\common\Age of Empires IV'
$assembly = [Reflection.Assembly]::LoadFrom((Join-Path $editorRoot 'Essence.Editor.Modding.dll'))
$domainType = $assembly.GetType('Essence.Editor.Modding.Wizards.AttributePrerequisite+InitialUniqueIDDomain', $true)
$domain = $domainType.GetConstructor([Reflection.BindingFlags]'Public,NonPublic,Instance', $null, [type[]]@([bool]), $null).Invoke(@($true))
foreach ($reserved in (Get-Content -LiteralPath (Join-Path $work 'reserved-ids.json') -Raw | ConvertFrom-Json)) {
    $domain.OnGenerated('ebps', [int]$reserved)
}
$generator = [Activator]::CreateInstance($assembly.GetType('Essence.Editor.Modding.Attributes.UniqueIDGenerator', $true))
$generated = [Collections.Generic.List[int]]::new()
foreach ($slot in 1..6) {
    $id = $generator.GenerateNext($domain, 'ebps')
    $domain.OnGenerated('ebps', $id)
    $generated.Add($id)
}
[ordered]@{
    project_guid = 'a743d7d1-d753-4cf7-8817-e29d8ded7366'
    generator = 'Essence.Editor.Modding.Attributes.UniqueIDGenerator.GenerateNext'
    assembly_sha256 = (Get-FileHash -LiteralPath (Join-Path $editorRoot 'Essence.Editor.Modding.dll') -Algorithm SHA256).Hash.ToLower()
    pbg_ids = @($generated)
    scope = 'Stage 1 conversion probe only; headless editor identity allocation, no build.'
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receipt -Encoding utf8
Get-Content -LiteralPath $receipt
