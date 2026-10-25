# Garrison 0.8.0 consolidation report

Status: consolidation and final preservation checks completed, 2026-10-24.
The retained Garrison workspace is below the approved 6 GB allocated-file budget.

## Scope

Strict 0.8.0 package metadata wraps the exact accepted 0.7.12 SGA. All 1,417 native
member bytes and mounts remain unchanged. Normal Vietnam is untouched. Existing
0.8.0 voice research and release_080 art preparation are preserved independent
work; this release uses tools/consolidation_080.

This follows 0.7.1's lossless indexed-input consolidation approach. F: uses
262,144-byte allocation units, so reducing repeated small files saves substantial
allocated space as well as removing repeated large archives. Moving files between
E: and F: is not counted as a saving.

## Preservation and recovery

- All 339 editable Blender masters and 1,009 external images remain at their
  original paths with matching hashes. Full read-only Blender dependency checks
  found no missing files or linked libraries. One installed essential brush is a
  shared Blender tool dependency outside project storage.
- Source, rigs, authored exports, textures, recipes and tools remain available.
  The readiness map covers all 135 packaged model resources by retained asset
  family or exact native donor. Family routes can include alternate revisions;
  this does not claim every model was freshly recooked.
- resources_080 preserves 83,710 recovery keys in 12,392 unique payloads, including
  113 native archive inventories and 34,808 native-member recovery records. Its
  payload ZIP is 1,152,900,743 bytes. resources_071/consolidation_071 remain intact.
- Exact independent 0.7.12 and 0.7.0 ZIP/SGA rollbacks remain plain. Other old
  deliveries retain their useful unique content and provenance in recovery; their
  original container bytes are not promised.
- Historical recipes retain their original paths/hashes. Retired previews and
  absent predecessor names are classified rather than silently rewritten. The
  current family index and recovery helpers are the supported starting point.

## Delivery hashes

0.8.0 ZIP SHA-256:
`58f57c1a09b2d7e5d2a3c986ac2a1ec3c390e07edaa212b4faf83a34b3702505`.

Embedded SGA SHA-256 (exact 0.7.12):
`e54fad91112350c70dab1c8cc826da26aa5c6ae9a6754244ed9141fe75d75eb1`.

Recovery payload ZIP SHA-256:
`d00f31fc13bb3cc70304f1421adb9a8f1c64335d4cf92b3697278d77ceebbb1a`.

## Verification gates

Pre-retirement checks passed: fresh official inheritance, 377 tuning instances
with zero errors, SCAR validation, 17 gameplay regressions and 19 recovery safety
tests. A real Content Editor source build validated 377 instances and retained
the Garrison archive identity. Representative older archer, current buffalo and
skirmisher, and stone fortified Hideout native cook/readback checks passed.

After retirement, a second real Content Editor build validated 377 instances with
unchanged source and correct identity. The older archer4, recent furred buffalo
and skirmisher, and stone fortified Hideout again passed fresh cook/readback.
Package reproduction produced the exact same ZIP hash. Static post2 passed all
22 recovery safety tests, 17 gameplay regressions and current validators with no
inheritance errors. Full protected-file and old/new store readback also passed.

Static post1 initially failed because three historical comparison fixtures were
packed. Their exact bytes are now restored by the supported validation helper
before running the unchanged historical tests. Failure logs remain preserved.
The helper refuses edited fixture files and records newly restored copies.

The final 2,341-file generated cleanup manifest received independent review, with
zero protected overlap. Its 1,819 saved metadata/log entries passed full ZIP CRC
and hash checks. All listed copies were retired; the final full preservation check
passed afterward. The generated duplicate ZIP was removed after exact comparison;
its receipt, metadata and verification remain. All seven storage links pass.

| Gate | Result |
| --- | --- |
| Source/static | 377 tuning instances, zero SCAR/inheritance errors, 22 safety and 17 gameplay regressions passed |
| Content Editor source compilation | Real completed pre3 and post1 builds; source unchanged, identity passed |
| Asset cook/readback | Older archer4, current buffalo/skirmisher and stone fortified Hideout passed before and after retirement |
| Package | Strict 0.8.0 ZIP, CRC, embedded hash, identity, 1,417 unchanged members/mounts and deterministic reproduction passed |
| Preservation | 5,030 original plain files, normal 300 baseline hashes, 12,392 new unique payloads and old 9,649 recovery keys passed |
| Client import | Unverified |
| Fresh-match appearance/behavior | Unverified |
| Save/load | Unverified |
| Multiplayer | Unverified |

Import, fresh-match appearance/behavior, save/load and multiplayer have not been
observed for 0.8.0. No installation or publication is included.

## Storage

The final measurement counts all retained files, including stores, rollbacks,
delivery, operation journals and evidence, without generated-output exclusions.
It counts the seven junction targets once. Normal Vietnam and shared installed
tools/game data are outside this approved Garrison budget. Values below are file
bytes; filesystem directory metadata is not included.

| Measurement | Logical bytes | Allocated file bytes |
| --- | ---: | ---: |
| Before | 24,115,147,989 | 35,059,089,408 |
| Retained | 5,393,552,209 | 5,695,193,088 |
| Net reclaimed | 18,721,595,780 | 29,363,896,320 |

Main retirement removed 49,058 redundant copies. Separately reviewed generated
cleanup removed 2,341 copies. Empty-directory cleanup removed 14,949 directories;
all configured link targets remained. Gross retired bytes are not substituted for
the measured net reduction, which includes new recovery stores and evidence.

The planning gate passed below 5.7 GB including 50 MB reserve before original
retirement. Post checks count the actual journal/evidence and retain an extra
50 MB against the hard 6 GB cap. Actual final measurement uses no reserve
subtraction. Temporary future builds/restores can exceed the retained budget.

## Continue development

Read README_080.md and docs/DEVELOPMENT_080.md. The guarded entrypoint is
tools/build_consolidated_080.ps1. Source/Assets actions qualify retained inputs;
Package reproduces the frozen preservation release and rejects source drift.
Future gameplay/art releases need their own explicit changed-member integration
policy carrying forward the compiled-only owning-resource overlays.

Detailed receipts and retirement manifests live under owned F: consolidation_080
and output/consolidation_080. Failed native/validation attempts remain evidence.
