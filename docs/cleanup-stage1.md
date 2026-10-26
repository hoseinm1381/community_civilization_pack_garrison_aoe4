# Vietnam source simplification, batch 1 — 2026-10-15

## Implemented source changes

Active attribute instances decreased from **297 to 235**:

| Retired family | Files | Replacement |
| --- | ---: | --- |
| Tower-only unit EBPS/SBPS | 42 | Existing regular Vietnamese squads; tower SCAR owns timing and the Pho Minh pause |
| Remaining Rattan unit EBPS/SBPS | 13 | Regular units, including the regular discounted handcannon squad; SCAR owns +1 ranged armor |
| Feasibility probes | 7 | Current private starting roster and archery range; obsolete probe research removed |

Removed the Rattan-only tier groups, duplicate production entries, and squad requirements that previously hid regular squads after research. Kept ordinary age upgrades, the 100-wood/200-gold Rattan research, the distinct Lam Sơn archers, and the existing Trung Foundries discount requirements. No new engine API or gameplay modifier was introduced by this batch.

The handcannon's shared tier group retains its requirement-free default and campaign tiers, including visual attachments and initialization. Review caught that these baseline tiers must survive when the Rattan-dependent tier is removed; the manifest and prepared source check record their full original structure.

Removed the unused `catalog.scar` and its import. Nine completed one-time bootstrap/migration scripts were removed from active `tools`; their exact source remains in the rollback archive. The maintained tools are the private precache generator and the user-run build helper.

The RDO now contains **674 entity entries and 43 squad entries**. All **583 foreign/stock entity entries** remain unchanged. The generated prematch hook contains all **91 private entities and 43 private squads**. This is source coverage, not proof that all models/effects render in game.

## Rollback and evidence

- Rollback archive: `../../Vietnam_v2_cleanup_backups/Vietnam_v2_before_cleanup_20261015-153444.zip` relative to this document.
- SHA-256: `5a8ce79e8c3885525f6c549a6396e4b88f8eacb1aa8768f6704d45aafa9ee1bd`.
- All 370 archived files were read back and compared with source SHA-256 before removal. `ROLLBACK_HASHES.json` inside the archive identifies every original member.
- `cleanup-stage1-manifest.json` records every removed file, former PBG ID, replacement, hashes, retired RDO IDs, and preserved age progression.
- Readback comparison found all 235 surviving root PBG IDs unchanged, all retained RDO IDs unchanged, all local GUID-qualified references resolving, and the non-Rattan tier requirements/targets in 35 files unchanged.
- Rattan versus regular unit comparison found matching weapons, movement, ability data, and visible unit names. The retired armor variants had explicit zero-armor overrides and different loadout/tier references; the ordinary unit definitions remain the source of base stats.
- `Real_Vietnam_1`, packaged archives, caches, and localization source were not changed.

No test suite, Content Editor build, or native match was executed for this batch. The updated checks are prepared for the user in `tests`, including retired-reference detection, producer duplication, age progression, discount requirements, and the real Rattan research identity.

Historical migration maps, identity allocations, and `precache-inventory.json` describe earlier snapshots. Do not regenerate current assets from those records. Use the active files, current RDO, and cleanup manifest for the current inventory.

## User acceptance and later batches

Follow `next-user-build-check.md`. Reload the source project in Content Editor before rebuilding so source deletions are noticed; verify the resulting package does not retain retired private RGDs. If the editor retains stale entries, use its clean-rebuild workflow. Keep the rollback archive and existing packages.

Check Rattan research both before and after ordinary unit age upgrades, on units already present and on newly trained units. Confirm the same roster and single production buttons remain available; test normal and discounted handcannons with Trung Foundries alive and destroyed. Confirm +1 ranged armor and no unintended melee armor change. Test Pho Minh destruction/reconstruction and ordinary building production separately.

Only after native acceptance, audit these later batches without preemptively deleting them:

1. Landmark-dependent discount/free variants: verify cost display, charging, cancellation/refunds, queues, and landmark destruction before replacing their native requirements.
2. Faster-house and other economy variants: separate construction-time effects from model, population, and ability differences.
3. Garrison/building variants: preserve occupants, weapon attachments, ongoing construction, and ownership when researching or reverting effects.
4. Existing siege-production duplicates and stale associated-building metadata: inspect native requirements before classifying them as redundant. The unchanged siege building currently serializes repeated Springald/Bombard entries; this batch does not alter them.

No new full-army polling was added. Save/load and old-save compatibility remain outside the supported scope; use fresh matches.
