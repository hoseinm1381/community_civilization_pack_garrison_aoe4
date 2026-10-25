# Garrison 0.8.0 Consolidation Implementation Plan

> Execute inline using the executing-plans skill. Fresh review before retirement
> and completion. No Git repository is present; preserve snapshots and receipts.

**Goal:** An unchanged-gameplay 0.8.0 release and editable Garrison development
workspace below 6,000,000,000 allocated bytes across both owned roots.

**Architecture:** Plain source/masters and linked textures; independent exact
0.7.0/0.7.12 rollbacks; hash-indexed original-path recovery store; fail-closed
allowlisted retirement; reproducible package and asset qualification.

**Tech stack:** Existing Windows Python/Blender/Garrison/Content Editor runtimes,
ZIP/gzip, SHA-256, existing native recipes and archive identity checker.

**Spec:** `docs/RELEASE_080_CONSOLIDATION_DESIGN.md`, approved by the user.

## Constraints and review focus

Preserve identity, all current source/art, normal source and protected stores.
Normalize extended paths/case/junctions. Never overwrite edited restoration
targets. Account for current compiled-only overlays and unique historical native
payloads. Do not mistake frozen historical recipes for current editability.
Plan for 5.7 GB allocated; final retained storage must be below 6 GB. Exclude
temporary attempts only after verified retirement, never from reported totals.

## Tasks

- [x] **1. Inventory, closure and freeze.** Finish `consolidation_080` audit.
  Inspect linked libraries/media; map current asset families and unresolved
  historical references. Freeze active/normal/source/master/rollback hashes.
  Output a retention manifest and readiness index. Reject input drift.
- [x] **2. Recovery store and safety tests.** Create `tools/consolidation_080`
  with `common.py`, `store.py`, `prepare.py`, `retire.py`, `verify.py`,
  `package.py`, and `build.py`; keep historical 080 tools unchanged. Original
  E/F keys map to SHA-256/length and one content-addressed ZIP payload. Native
  archive recovery keys also retain member/mount provenance. Add
  `tests/test_consolidation_080.py` for traversal, extended paths, corruption,
  aliases, no-overwrite and stale/unknown retirement failures. Observe failing
  tests, implement, then require passing tests and full store readback.
- [x] **3. Package and qualification.** Produce strict 0.8.0 ZIP with exact
  delivered 0.7.12 SGA. Run identity checker and complete member/mount proof.
  Add `tools/build_consolidated_080.ps1` and development handoff. Run fresh
  tuning/SCAR/inheritance checks and native source compilation; qualify an
  older packed-input unit/building and recent native assets. Use shared lock.
  Preserve failures and reports. Compute projected retained allocation.
- [x] **4. Review and retire.** Fresh reviewer checks exact manifests, budget,
  source/texture/rig closure, independent recovery and qualification. Resolve
  important findings. Rehash every approved file immediately before retiring
  its redundant representation; reject new/edited/unclassified paths. Preserve
  compact operation ledger and all designated plain input paths.
- [x] **5. Post-retirement verification.** Restore/rebuild from empty staging
  with retained inputs only, compare package, verify all source/normal/rollback
  hashes and storage links, measure allocated and logical totals independently.
  Remove only newly qualified transient attempts through their own allowlist.
  Add current README/storage guidance without changing frozen original documents;
  update development/report with exact results and native limits.

## Stable helper interfaces

`canonical(path)` resolves owned paths safely. `ResourceStore.read(key)` verifies
length and SHA-256; `restore(key, destination=None)` refuses edited files and
preserves original hierarchy. `prepare.py` creates immutable retention and
retirement manifests plus store/index hashes. `retire.py` requires those hashes,
all qualification gates and projected budget; it logs each exact path operation.
`verify.py` checks protected plain inputs, every packed blob, rollback/package,
normal source and final allocation. `package.py` produces and verifies only the
version metadata change. `build.py` runs preparation, native validation and
qualification with an attempt label; future asset changes require a new explicit
changed-member integration policy.
