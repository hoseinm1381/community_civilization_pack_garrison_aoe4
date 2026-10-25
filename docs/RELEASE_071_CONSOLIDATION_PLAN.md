# 0.7.1 workspace consolidation implementation plan

Approved specification: the user's 2026-10-19 instruction and the measured
`garrison-071-retention-audit/deep-audit-summary.json` from this conversation.

Goal: preserve every 0.7.0 resource, current editable assets and exact 0.7.0
rollback; build and independently verify 0.7.1 before retiring old copies; leave
combined E:/F: retained file data below 3,000,000,000 bytes; the user later approved up to 6,000,000,000 allocated bytes for exFAT.

Architecture: active gameplay and editable masters stay on E:. An owned F:
resource store holds one hash-addressed copy of shared native/texture inputs and
losslessly compressed numeric JSON snapshots. An index maps original paths to
retained resources. 0.7.1 starts from the pinned 0.7.0 native resource inventory,
preserving its compiled-only selector/producer changes. Fresh source validation,
resource assembly/readback and supported asset cook checks are separate receipts.

Tech stack: bundled Python standard library, PowerShell native literal-path
cleanup, installed Garrison core/archiver, model-capable Content Editor and a
serialized background Blender process. No Git repository is present; use an
append-only migration ledger and hash manifests instead of Git task scripts.

## Constraints and review focus

- Normal edition, foreign mods, installed game and unrelated Blender scenes stay untouched.
- Final project GUID, PBG IDs, SCAR, abilities, gameplay, art and native TOC mounts stay preserved.
- All resource reads verify hashes; compressed inputs recover identical bytes.
- Reject traversal, missing inputs, changed/junction cleanup targets, alias cycles and unverified release deletion.
- New/changed files after the audit are preserved unless separately accounted for.
- Keep source images of every retained Blender master; validate geometry, weights,
  UVs, transforms, bones and image identities across image-path migration.
- Cleanup uses a frozen exact-file allowlist, never an unexamined recursive root deletion.
- Future modifications must use the current source/asset helpers, not rerun retired historical releases.
- Native import/match testing remains separate from byte-preserving rebuild proof.

## Task 1: Freeze and resource API

- [x] Freeze current active source, exact 070 ZIP/SGA, normal edition and audited inputs.
- [x] Add tests for path traversal, gzip integrity, alias resolution and cleanup gate failure.
- [x] Run tests red, implement `tools/release_071/resources.py`, run tests green.
- [x] Build the expanded retention inventory; preserve all existing .blend masters
  if the measured budget permits, plus their complete image dependencies.
- [x] Write/copy and verify the canonical store and original-path index, without deleting originals.

## Task 2: Rebuild workflow

- [x] Implement current 071 native source validation, strict package build and
  full resource readback comparison, with exact separate native TOC mounts.
- [x] Provide asset input materialization and supported building/unit cook entry points.
- [x] Exercise a fresh native source compile and serialized representative asset cooks.
- [x] Assemble fresh owning archive bytes from retained 070 member payloads;
  verify every native member and TOC against exact 070, then package strict 0.7.1.

## Task 3: Editable-source migration

- [x] Preserve original Blender files in transaction backup until verification.
- [x] Repoint only external image paths to shared retained files in a background
  process; compare semantic fingerprints before/after each saved file.
- [x] Independently reopen migrated masters and verify all external dependencies.
- [x] Preserve OBJ/FBX/current source media and original-path recovery metadata.

## Task 4: Review and retirement gate

- [x] Run focused tests, complete resource/source/asset checks and independent review.
- [x] Reject cleanup unless 071 ZIP/readback, 070 rollback, retained resources,
  active source, normal edition and editable dependency checks all pass.
- [x] Save exact retirement manifests and copy/hash verification first.

## Task 5: Cleanup and final acceptance

- [x] Use native PowerShell on verified literal owned targets; remove only
  inventoried retired files and empty regular directories, preserving junctions.
- [x] Update storage/workspace/entrypoint documentation for 0.7.1.
- [x] Repeat the consolidated rebuild with old folders unavailable, verify ZIP
  and full native resource identity, then remove only verified generated scratch.
- [x] Recheck 070 rollback hashes and protected normal/source state.
- [x] Independently measure final E:/F: unique-file bytes, require <3 GB, and
  report reclaimed bytes, package location and remaining native acceptance gates.

Completion ruling: Task 3 image-path migration and transaction Blender backups were unnecessary: every original master and image path was retained byte-identical, with no saves. Immutable inputs use the exFAT-compatible lossless indexed ZIP/gzip store, not hardlinks. All gates completed; see CONSOLIDATION_071_REPORT.md.
