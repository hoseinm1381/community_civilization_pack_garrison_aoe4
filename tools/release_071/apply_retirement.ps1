param([Parameter(Mandatory=$true)][string]$Plan)
$ErrorActionPreference = 'Stop'
$manifest = Get-Content -LiteralPath $Plan -Raw | ConvertFrom-Json
$proof = Get-Content -LiteralPath $manifest.proof -Raw | ConvertFrom-Json
foreach ($gate in @('package','rollback','native_source','asset_cooks','resources','editable','normal_unchanged','review')) {
    if ($proof.$gate -ne $true) { throw "Cleanup blocked: $gate" }
}
if ($proof.retained_bytes -le 0 -or $proof.retained_bytes -ge 3000000000) { throw 'Storage budget failed' }
if ((Get-FileHash -LiteralPath $Plan -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.retirement_plan_sha256) { throw 'Retirement plan changed after review' }
if (@($manifest.operations | Where-Object action -eq 'hardlink').Count) { throw 'Current exFAT retirement plans must not contain hardlinks' }

function Assert-OwnedPlainPath([string]$Path) {
    $absolute = [IO.Path]::GetFullPath($Path)
    $owner = $null
    foreach ($candidate in $manifest.roots) {
        $root = [IO.Path]::GetFullPath($candidate).TrimEnd('\')
        if ($absolute.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { $owner = $root; break }
    }
    if ($null -eq $owner) { throw "Outside owned roots: $absolute" }
    $check = $absolute
    while ($check.Length -ge $owner.Length) {
        if ([IO.File]::Exists($check) -or [IO.Directory]::Exists($check)) {
            $attributes = [IO.File]::GetAttributes($check)
            if (($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Unexpected link: $check" }
        }
        if ($check -eq $owner) { break }
        $check = [IO.Path]::GetDirectoryName($check)
    }
    return $absolute
}

$count = 0
$removed = [long]0
foreach ($row in $manifest.operations) {
    $path = Assert-OwnedPlainPath $row.path
    if (-not [IO.File]::Exists($path)) { continue }
    $item = [IO.FileInfo]::new($path)
    if (($item.Attributes -band [IO.FileAttributes]::Directory) -ne 0) { throw "Not a file: $path" }
    $ns = [long](([decimal]$item.LastWriteTimeUtc.Ticks - [decimal]621355968000000000) * 100)
    if ($item.Length -ne $row.bytes -or $ns -ne $row.mtime_ns) { throw "Concurrent file change preserved: $path" }
    if ($row.action -eq 'hardlink') {
        $canonical = Assert-OwnedPlainPath $row.canonical
        if ([IO.Path]::GetPathRoot($canonical) -ne [IO.Path]::GetPathRoot($path)) { throw 'Cross-volume hardlink refused' }
        $hash = (Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($hash -ne $row.sha256 -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Duplicate hash mismatch: $path" }
        $temporary = $path + '.071-link'
        if (Test-Path -LiteralPath $temporary) { throw "Unexpected pending link: $temporary" }
        New-Item -ItemType HardLink -Path $temporary -Target $canonical | Out-Null
        Remove-Item -LiteralPath $path -Force
        Move-Item -LiteralPath $temporary -Destination $path
    } elseif ($row.action -in @('retire','packed')) {
        Remove-Item -LiteralPath $path -Force
    } else { throw "Unknown operation: $($row.action)" }
    $removed += $row.bytes
    $count++
    if (($count % 1000) -eq 0) { Write-Output "Completed $count verified file operations" }
}
[pscustomobject]@{ operations=$count; removed_logical_bytes=$removed; completed_utc=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $manifest.result -Encoding utf8
Write-Output "Completed $count verified file operations"
