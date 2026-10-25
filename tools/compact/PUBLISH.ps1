param([switch]$Execute)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$expected = 'https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4.git'
$remote = & git -c "safe.directory=$repo" -C $repo remote get-url origin
if ($LASTEXITCODE -ne 0 -or $remote -ne $expected) { throw 'Unexpected publication destination.' }
$commits = (Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/compact/push-commits.json') | ConvertFrom-Json).commits
Write-Host "Destination: $remote"
Write-Host "Reviewed initial batches: $($commits.Count)"
if (-not $Execute) { Write-Host 'Preview only. No push performed. Use -Execute only when publishing is explicitly intended.'; return }
$dirty = & git -c "safe.directory=$repo" -C $repo status --porcelain
if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Commit/review local changes before publication.' }
$remoteLine = & git -c "safe.directory=$repo" -C $repo ls-remote origin refs/heads/main
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect remote; nothing pushed.' }
$remoteHead = $null
if ($remoteLine) {
    & git -c "safe.directory=$repo" -C $repo fetch origin main
    if ($LASTEXITCODE -ne 0) { throw 'Cannot fetch remote.' }
    $remoteHead = (& git -c "safe.directory=$repo" -C $repo rev-parse refs/remotes/origin/main).Trim()
    & git -c "safe.directory=$repo" -C $repo merge-base --is-ancestor $remoteHead HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Remote contains a different history. Review it; this script never force-pushes.' }
}
foreach ($commit in $commits) {
    & git -c "safe.directory=$repo" -C $repo merge-base --is-ancestor $commit HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Reviewed batch is not part of the current history.' }
    if ($remoteHead) {
        & git -c "safe.directory=$repo" -C $repo merge-base --is-ancestor $commit $remoteHead
        if ($LASTEXITCODE -eq 0) { continue }
        if ($LASTEXITCODE -ne 1) { throw 'Cannot compare publication progress.' }
    }
    & git -c "safe.directory=$repo" -C $repo push origin "${commit}:refs/heads/main"
    if ($LASTEXITCODE -ne 0) { throw "Publication stopped at $commit. Earlier successful batches remain; retry safely after inspection." }
    $remoteHead = $commit
}
& git -c "safe.directory=$repo" -C $repo push -u origin HEAD:refs/heads/main
if ($LASTEXITCODE -ne 0) { throw 'Final publication failed.' }
