# Compact 0.8.8 update â€” 2026-10-26

The owner requested the Castle landmark moving_ext crash repair, a further Phá»•
Minh drop-off fix, and the smallest GitHub update for a manual push.

## Exact scoped change

- Flooded Citadel calls BP_GetEntityBPDefaultSpeed only for a generated set of
  1,938 names verified to retain moving_ext through current official/private
  inheritance and variants. No new engine call or catch-and-continue workaround.
  Its 30% slow, geometry/range, overlap and removal logic are preserved.
- Phá»• Minh already had the Hideout resource flags. Add the explicit native
  resource_drop_off interaction (corroborated by current Town Center/lumber camp)
  to its existing default/campaign interaction lists. No new extension or PBG.
- Exactly two members change from 087; every other member, art/Ogg file and
  independent voice cooldown is unchanged. Nine distinct current members differ
  from the retained 084 baseline; the final tower replacement supersedes 087's.

## Minimum input update

Keep all 172 previous packs and both prior indexes immutable. Add only
`pack-00173.zip` (**158,426 bytes**) and
`index-088-v1.json.gz` (**5,772 bytes**), plus changed readable
source/tests/guides. No full new SGA/ZIP, art or sound payload is stored. Sparse
verification reuses the prior full member map and replaces the current metadata
and two hashes, avoiding another large verification JSON. The controller rejects
unexpected members or mount changes. Data steps carry each member's final bytes.

Current commands: `python tools/compact/portable.py release --archive-tool ...
--destination ...` or `rebuild-088` with the same arguments. The older command
name remains an alias for current reconstruction; 084 has its historical command.

## Verified result

- Exact SGA: `a341dfb4ceec21c42f795502de5e3017a490ac83c66a7056eb8aa33d81c6b09a`.
- Exact ZIP: `ca7ff19b1da774666f6f8e1dc3d6d9a4357dc8aa97dc99578dc5f776f9d63e2a`.
- ZIP size: 284,935,545 bytes; 11,973 member hashes and all mounts freshly verified.
- Rebuild succeeded while Python access to both original owner roots was blocked;
  no attempted access. Native subprocess inputs used only temporary paths.
- All twelve source/Lua regressions also pass after isolated restoration, using
  an existing copied Lupa test runtime. No dependency installation/download.
- Compact tests: 12 passed, including sparse verification's failing-then-passing
  immutability and member/mount tests. Contributor smoke tests: 15 passed (39 portable/source/compact/contributor tests total).
- Temporary NTFS reconstruction files were removed automatically. Raw diagnostics,
  warning screenshot/full log and native staging history remain in the owner
  workspace; only compact sanitized crash evidence enters this checkout.

Main-workspace actual native tuning reference compilation validated 377 instances.
The portable rebuild is archive reconstruction, not another native burn. Import,
fresh Castle completion/field behavior, Phá»• Minh manual/automatic resource return,
pathing, repair, save/load and multiplayer remain native acceptance gates.

## Development notes for AIs

Re-run tools/release_088/generate_mobility.py after unit additions/game updates,
using a refreshed 088 official extension cache and the retained voice identity
metadata. Unknown blueprints fail closed until regenerated. The generator trims
comma-space removedIds before inheritance resolution: ignoring those spaces can
falsely admit stock visual actors whose moving_ext was deleted. A compiled-data
cross-check covers 1,872 admitted default records, with zero missing movement.
Frozen historical evidence is not changed to hide this distinction.

Use the current owning archive for further selective integrations. Retain the
084/087 indexes and packs; do not rerun broad historical exporters. No new voice
synthesis, model download, installation, scheduled synchronization or push.

Existing readable files retain their tracked line endings for a focused Git diff.
New readable files use LF. Frozen indexed source, evidence and packaged payload
bytes retain their exact original hashes; current working-copy hashes and line
endings are recorded in evidence/088-readable-normalization.json.
