# Execution ledger — plan: docs/RELEASE_071_CONSOLIDATION_PLAN.md

- 2026-10-19: User explicitly approved consolidation, 0.7.1 rebuild, verification
  before deletion, retirement of old versions/duplicates and a 3 GB retained budget.
- Pre-flight: resource index is shared by build, Blender migration and cleanup;
  all consumers must use the same hash/alias model. Cleanup consumes successful
  rebuilt-package, rollback, source and editable-resource receipts.
- Ruling: no Git repository exists at this workspace, so Git task/worktree helpers
  are inapplicable. Existing owning roots are the authorized in-place workspace.
- Ruling: historical preservation instructions are superseded only for this
  explicitly authorized latest-version consolidation, after retention/rebuild gates.
- Ruling: package/resource preservation, native source compilation and fresh asset
  cook proof must be reported independently; no import or match proof is inferred.
- Task 1: resource API test initially failed with missing module; implementation
  then passed 7/7 tests for integrity, gzip, alias cycles, traversal and cleanup gates.
- Task 2: exact 070 ZIP/SGA copied and hash-verified in `archives/release_070_rollback`.
  Fresh native source build v1 passed: 369/369 instances, no build errors, active
  and staged source hashes unchanged. Current building cook is a separate gate.
- Ruling: preserve original paths and bytes for all editable Blender masters and
  image dependencies if the expanded budget permits. This avoids any geometry,
  UV, skinning or image-path migration. Only derived immutable duplicate files
  may share same-volume hard links; editable masters, OBJ/FBX and authoring files
  keep independent identities. Numeric JSON is gzip-packed with a verified loader.
- Ruling: no broad F scan is needed during preparation; cleanup is restricted to
  the exact audited paths, with metadata checks. Unknown/concurrent files stay.
- Task 2: 0.7.1 native assembly/readback passed, 1243/1243 payload hashes and
  native TOC mounts identical to 070; four-member strict ZIP verified, 131964527 B.
  Fresh Garden cook/readback and weighted archer2 three-LOD native geometry
  comparison passed. Unit v1 direct launch failed before logging; compact failed
  receipt remains. Unit v2 uses the supported core runner and passed.
- Task 3: all 265 masters and complete image dependency closure fit. Original
  bytes and paths stay untouched; no Blender edit or semantic migration needed.
  Independent reviewer rehashed all 265 masters and checked image availability.
- Review correction: every E: file and editable PNG/template stays independent;
  sharing is limited to immutable native donor references on F:. Original 070
  output copies retire after proof; exact designated rollback stays independent.
  This prevents future export edits from altering another variant or rollback.
- Diagnostics: preserve all 1752 audited .log files, including failed attempts.
  Also preserve the historical castle donor aggregate losslessly in the store.
  An interrupted newly written gzip was detected by verification and regenerated
  before any original input was removed; store writes now use verified atomic
  replacement. No deletion has occurred at this point.
- Retirement phase 1: independently approved exact plan
  `2fe14bfa9e40cd96c3b10e6958e6248f8e945f8651f67cdfa9a1ac29013c0900`
  began. It stopped at its first hardlink before removing that original file.
  F: is exFAT with 262144-byte allocation units; hardlinks are unsupported.
  Filesystem capability should have been qualified before selecting that method.
  Previously retired paths were already verified obsolete or packed; every
  editable master, image, rebuild input, delivery and rollback remains preserved.
- Corrective policy: no hardlinks. Keep all original Blender images and required
  unit templates plain at original paths. Pack other F native donor inputs and
  diagnostics losslessly into one hash-indexed ZIP with SHA/length verification.
  This also avoids exFAT per-file cluster waste. Preserve phase-1 plan and stop
  evidence losslessly; generate/review a new exact remaining retirement plan.
- Qualifier correction: preserve v4/v5b/v5c hierarchy when materializing compressed
  ranged-unit inputs. Tests RED then GREEN (10/10 including bundled input codec).
  Fresh archer4 tree1 native cook/readback and special three-LOD comparison passed;
  v4/v5b predecessors and corrected-normal branch were exercised. Reviewer found
  no remaining issue in that correction. This changes no packaged native resource.
- User steering: up to 6 GB of actual allocation is acceptable if exFAT cluster
  overhead causes it. Keep the 3 GB file-byte target and measure both separately;
  no extra NTFS compression or editable-source rewriting is needed solely to
  force allocation below 3 GB.
- Final exFAT retirement: reviewed plan
  `a00d9e6184e63b6e9754b3a9e374b6cb7587bed957c8c3af60487da15277721f`
  completed 76573 operations successfully, using no hardlinks. Full ledger and
  review/hash evidence are retained losslessly. No protected input was targeted.
- Post-retirement rebuild: `tools/build_release_071.ps1 -Label post1` passed.
  Native source validated 369 instances without errors and reproduced source SGA
  `d319188a01a2faf192c25927b3585814a4d60fe1ce4bc8c2f3f6848859e307ca`.
  Full 1243-member/mount assembly and four-member ZIP reproduced exact delivery
  SGA `d622e6e1b045d595a059f48646b32a0303ea66bb1631eca96ab4baa4e8290f0c`
  and ZIP `6782ab9af99aad362b3bf14b6af09cb6ba9224fbea961597aa92d7383d521d8f`.
- Final scratch cleanup: independently approved exact plan
  `32b9a01b45f202e9f7a1fbccef22df0fbfe8bdcaf3e10c59f5d14c0c5a85b2c0`
  removed 2933 regenerated post1 files only. Cleared 24076 empty plain directories;
  preserved every junction and target container. Rechecked protected sources,
  normal baseline, 9649 resource keys, masters/images, rollback, delivery and all
  seven storage links afterward: passed. Focused tests: 12/12 passed.
- Completion: measured about 2.89 GB retained file bytes /3.10 GB allocated file
  storage, below 3 GB data and user-approved 6 GB exFAT allocation. About 23.66 GB
  less file data than the audit baseline. See `CONSOLIDATION_071_REPORT.md` and
  protected `consolidation_071/final-storage.json` for final measurements. No game
  import, lobby selection or native-match acceptance is claimed.
