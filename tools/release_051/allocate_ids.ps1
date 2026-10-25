$ErrorActionPreference='Stop'
$root051=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$cfg051=Get-Content -LiteralPath (Join-Path $root051 'workspace.json') -Raw | ConvertFrom-Json
$identityRoot051=Join-Path $cfg051.external_root 'output/release_051/traps'
$target051=Join-Path $identityRoot051 'identities.json'
if (Test-Path -LiteralPath $target051) { throw 'Identity receipt exists; do not allocate again.' }
& $cfg051.python -B (Join-Path $root051 'tools/verify_workspace.py') --storage-only
if ($LASTEXITCODE -ne 0) { throw 'Storage check failed.' }
$asmRoot051=Split-Path $cfg051.content_editor -Parent
$modding051=[Reflection.Assembly]::LoadFrom((Join-Path $asmRoot051 'Essence.Editor.Modding.dll'))
$domainType051=$modding051.GetType('Essence.Editor.Modding.Wizards.AttributePrerequisite+InitialUniqueIDDomain',$true)
$domain051=$domainType051.GetConstructor([Reflection.BindingFlags]'Public,NonPublic,Instance',$null,[type[]]@([bool]),$null).Invoke(@($true))
foreach ($id051 in (Get-Content -LiteralPath (Join-Path $identityRoot051 'reserved-pbg.json') -Raw | ConvertFrom-Json)) { $domain051.OnGenerated('ebps',[int]$id051) }
$generator051=[Activator]::CreateInstance($modding051.GetType('Essence.Editor.Modding.Attributes.UniqueIDGenerator',$true))
$new051=[Collections.Generic.List[int]]::new()
foreach ($slot051 in 1,2) { $id051=$generator051.GenerateNext($domain051,'ebps');$domain051.OnGenerated('ebps',$id051);$new051.Add($id051) }
$editor051=[Reflection.Assembly]::LoadFrom($cfg051.content_editor)
$reflect051=[Activator]::CreateInstance($editor051.GetType('Essence.Editor.Burning.DataObjectDeterministicUniqueIdGenerator',$true))
$reserved051=[Collections.Generic.HashSet[UInt64]]::new()
foreach ($id051 in (Get-Content -LiteralPath (Join-Path $identityRoot051 'reserved-reflect.json') -Raw | ConvertFrom-Json)) { [void]$reserved051.Add([UInt64]$id051) }
$reflectIds051=[Collections.Generic.List[string]]::new()
while ($reflectIds051.Count -lt 4) { $id051=$reflect051.Next();if ($reserved051.Add($id051)) { $reflectIds051.Add($id051.ToString()) } }
[ordered]@{project_guid=$cfg051.project_guid;pbg_ids=@($new051);reflect_ids=@($reflectIds051);pbg_generator='Essence.Editor.Modding.Attributes.UniqueIDGenerator.GenerateNext';reflect_generator='Essence.Editor.Burning.DataObjectDeterministicUniqueIdGenerator.Next';scope='headless allocation only, all current Garrison/normal source IDs reserved'} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $target051 -Encoding utf8
Get-Content -LiteralPath $target051
