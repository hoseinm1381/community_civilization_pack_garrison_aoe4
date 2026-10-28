# Persia asset development and acceptance workflow

Owner instruction: 2026-10-26. This policy supersedes earlier instructions to
develop new assets directly in the permanent GitHub folder. The functional 0.9.0
build records remain historical evidence.

## Locations and current scope

- Permanent repository/main destination:
  `F:/aoe_4_temp/community_civilization_pack_garrison_aoe4`.
- Reusable dirty development/review workspace:
  `F:/aoe_4_temp/Temp_before_github_push`.
- First asset: **Gundeshapur**, Persia's Feudal landmark, chosen by the owner.
  The Grand Caravanserai and other Persian assets are outside this first asset.
- Establish the visual references/design before modeling. This document records
  the working arrangement; it does not claim an approved appearance or finished art.

## Develop and review in temp

1. Record the permanent repository's starting commit, source/package hashes and
   existing local changes. Inspect current storage configuration and tool versions.
2. Put new/modified Blender sources, source textures, scripts, Garrison recipes,
   candidate visual bindings, exports, cooks, previews and diagnostics in temp.
   Read unchanged permanent inputs in place where supported. Stage only what the
   tools require; avoid full repository/history/media-bank copies and extra
   milestone workspaces. Record any required candidate staging explicitly.
3. Trace Gundeshapur's actual blueprint, all affected variants and native visual
   owners before integration. Preserve gameplay, footprint, selection markers,
   identities and construction/ruin/repair behavior; do not replace native owners
   with generated prototype actors or add scripted mechanics for an art request.
4. Keep trial changes out of the permanent asset/gameplay files until acceptance.
   Workflow documentation may be updated there immediately to record owner policy.
   Keep Normal, the original Persia donor and unrelated Vietnam assets unchanged.
5. Present the candidate appearance and exact validation scope to the owner.
   Static/source, art export/cook/readback, Content Editor burn, archive/package,
   client import, native appearance/repair, save/load and multiplayer are separate
   gates. Missing native tests must be stated explicitly.

## Accept, promote and push

The owner's explicit acceptance of the reviewed asset result is required before
promotion and pushing. Approval of this workflow alone is not asset acceptance.

1. Transfer only accepted art/integration changes plus complete editable and
   rebuild inputs into the permanent repository. Recheck its current Git state
   before transferring; preserve unrelated local work and avoid deletion mirroring.
2. Retain editable `.blend` files, source textures/media, required donor/rig data,
   recipes, scripts, configuration, attribution and any indispensable compiled-only
   resources. Verify linked/packed dependencies, including ignored files. Anything
   unique inside temp must acquire a documented durable home before deletion.
3. Preserve existing immutable packs. Add a small deduplicated delta for new
   required inputs instead of another complete media bank, full SGA or history
   dump. Keep final delivery and compact evidence under `output/current` and the
   applicable tracked release documentation. Use lossless storage where suitable.
4. Update the changed-resource allowlist, rebuild delta and documentation. Existing
   `tools/compact/github_build.py native` / `package` checks pin the current 0.9.0
   source/payload pair; changed art requires an explicit new delta. Do not bypass
   stale-input checks or present the old package as the new art build.
5. Verify identity, dependencies, untouched member bytes/mounts, actual build and
   package results. Check the preserved accepted inputs against the staged hashes
   and verify reconstruction from their permanent homes without relying on temp.
6. Review the final diff, commit and push to `main` normally, as authorized by the
   owner after acceptance. Confirm the remote commit. No force push or rewriting
   old history for storage reduction.

## Cleanup after verified preservation and push

Delete `F:/aoe_4_temp/Temp_before_github_push` only when acceptance, promotion,
input preservation, reconstruction verification and the confirmed push all pass.
If any gate fails, keep temp and its diagnostics until resolved.

Before deletion, verify the resolved absolute path and any reparse points; never
follow a link into protected storage. Preserve compact hashes, build diagnostics,
the accepted delivery and rollback information outside temp. Required ignored
inputs need verified preservation independently of Git. A playable ZIP alone is
not an editable-source backup.

Remove regenerable cook/cache/readback/preview duplicates. Keep every important
editable input and dependency. Do not delete legacy recovery stores or existing
immutable packs under this temp-cleanup authorization. Measure retained and removed
bytes, recheck delivery hashes and report actual reclaimed space after cleanup.

## Current status

On 2026-10-28 the owner confirmed that 1.0.6 worked and authorized minimal
editable/rebuild promotion, main push and a GitHub release containing its ZIP.
The initial Gundeshapur-only scope above is historical. See RELEASE_106.md for
the accepted complete scope and verification. Future asset changes still follow
this review/acceptance workflow. This publication does not delete temp inputs.
