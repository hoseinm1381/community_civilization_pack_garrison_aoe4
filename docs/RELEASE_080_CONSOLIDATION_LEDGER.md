# Garrison 0.8.0 consolidation execution ledger

- 2026-10-24: User approved written consolidation design and the explicit
  retirement/rollback boundary. Work executes inline.
- Read-only inventory: 24,115,147,989 logical / 35,059,089,408 allocated bytes.
- Blender FILE image inspection: 339 masters, 1,009 images, zero missing/errors.
- Both 0.7.0 and 0.7.12 ZIP/SGA expected hashes, ZIP CRC and embedded equality pass.
- Normal 300 baseline asset hashes match. Seven storage links pass.
- Fresh design review added full external-dependency closure, per-family asset
  readiness, 5.7 GB projected budget margin and independent clean recovery gates.
- Ruling: preserve existing `0.8.0` voice work and `release_080` art preparation;
  new consolidation uses `tools/consolidation_080` and distinct external stores.
- Ruling: current pack remains byte-identical 0.7.12; native qualification does
  not authorize replacing compiled-only overlays with a source-only archive.
- Ruling: canonical ownership strips Windows extended prefix before path tests;
  all 1,009 image files are within the two owned roots after normalization.
- Complete Blend inspection: 339 opened read-only, no missing external paths or
  linked libraries. One installed Blender essential brush is an explicit shared
  tool dependency, not mod source. All model textures remain owned/plain.
- User's design approval authorizes implementation and exact qualified retirement;
  no original retirement has occurred yet.
- Initial single-process hash audit was interrupted before writing its final
  inventory. Restarted with a resumable SHA journal and four read workers; all
  54,088 non-transaction files hashed. The empty native lock is hashed as empty
  bytes without trying to read its locked range. New evidence is gzip-compacted.
- Probe: 12,800 distinct noncontainer F payloads compress to 1,175,316,161 bytes;
  eligible recovery payloads account for 1,116,716,560 bytes before ZIP overhead.
- Plain retention: 5,028 original files / 3,887,966,855 logical bytes /
  4,146,282,496 allocated bytes. Original retirement candidates: 49,060 F copies.
- `prepare.py` background process 19884 is assembling payloads-v1.zip; progress in
  `consolidation_080/prepare-v2.stdout.log`. It preserves 113 distinct native SGA
  contents and provenance before emitting final store/index and retirement map.
  No original inputs have been removed; generated readbacks are discarded only
  while the original SGA remains intact. Partial preparation failure log retained.
- 0.8.0 package final-v1 verified, unchanged 1,417 members/mounts. ZIP SHA:
  `58f57c1a09b2d7e5d2a3c986ac2a1ec3c390e07edaa212b4faf83a34b3702505`.
- Static pre2 validation passed: 377 tuning instances / zero errors, zero SCAR
  errors and fresh official inheritance. Gameplay tests17 passed. Recovery safety
  suite expanded after review and now passes16, including stop-on-change and
  interrupted unlink recovery. Source-only validation originally traversed too
  broad a root and raised MemoryError; it now scopes SCAR context to assets/scar.
- Native source pre3 passed377, unchanged active/staged inputs, pre/post namespace
  checks. pre1 incomplete and pre2 manually interrupted diagnostic attempts remain
  recorded; no success was inferred for them. Staging now uses short r80c paths.
- Asset qualification c8pre passed: older archer4 packed/predecessor three-LOD
  comparison; current furred buffalo and skirmisher native cooks/readback with rig
  contracts; stone fortified Hideout cook/readback. Active source stayed unchanged.
- Current model-family readiness index covers135 packaged RGM resources with
  retained master/export or exact donor routes; it does not claim every model was
  freshly recooked. Original v1 references remain classified as historical.
- Fresh review found queued deletion could continue after a failed validation;
  fixed with sequential retirement, durable NTFS intent/completion journaling and
  fail-path regression. Success receipt now follows the budget assertion. Strict
  projected5.7GB gate enforced; no original deletion before complete store review.
- New development guide, `development.json` and guarded PowerShell entrypoint
  created. Source-edited projects cannot silently use the frozen0.8.0 packager.
- Pending: finish store; run full `verify.py pre`; reviewer approves exact index,
  candidate manifest and projection; run `retire.py`; source post1 + assets c8post
  from empty staging/retained inputs; deterministic package reproduction; verify
  post; generate/review/apply exact transient/restored-input cleanup; empty dirs;
  final independent measurements and preservation checks; README/STORAGE/report.

## Qualified retirement checkpoint

- Recovery preparation completed: 83,710 recovery keys, 12,392 unique payloads,
  113 native archive inventories and 34,808 native-member recovery records.
  `resources_080/payloads-v1.zip` is 1,152,900,743 bytes. Full new and old store
  readback passed; the older 0.7.1 store remains protected.
- Retention amendment preserves two exact empty failed-native archives as plain
  diagnostics. Final original-copy sets: 5,030 plain files and 49,058 retirement
  candidates. The earlier counts above describe the pre-amendment checkpoint.
- Fresh full preservation verification passed, including current strict 0.8.0
  delivery, exact rollbacks, all protected source/art and normal hashes. Projected
  retained allocation with 50,000,000-byte reserve: 5,676,871,808 bytes.
- Independent reviewer `/root/review_080_retirement` passed the amended manifest
  SHA-256 `6863c9b3d31059a14b40671699d1873d0a21183872be6a4a36656ddd65cbe1eb`.
  The exact review and tool hashes are pinned in `retirement-review.json`.
- Main retirement started with per-file fresh hash/identity checks and durable
  intent/completion journaling. Source/post-retirement qualification and final
  physical measurement remain pending at this checkpoint.
- Recovery safety suite now contains 19 passing tests. The original READMEs and
  STORAGE.md remain byte-identical preservation inputs; new 0.8.0 entry documents
  provide the current guidance instead of changing the frozen originals.

## Main retirement complete; post qualification

- All 49,058 original candidates retired successfully. Fresh per-file hashes and
  durable operation records account for 20,227,179,811 logical bytes and
  30,912,020,480 allocated bytes of redundant representations. These are gross
  retired bytes, not final net reclaimed storage; recovery/evidence was added.
- Main operation ledger SHA-256:
  `bcef0e475e3312343932ff37933e7890f8375888c8faa9f7fa54915f51613d44`.
- Native source post1 started only after the main completion receipt. It uses
  empty isolated staging and the preserved active inputs.
- Follow-up review identified the deterministic post1 ZIP as a temporary exact
  duplicate. Only its full exact path is eligible for generated cleanup, with
  pinned ZIP/SGA verification before projection exclusion and cleanup planning;
  its receipt/manifest/verification stay plain. Other delivery paths are excluded
  from this rule.
- The reviewed pre gate remains 5.7 GB including 50 MB reserve. Post verification
  counts the actual existing operation journal and keeps an additional 50 MB
  reserve against the 6 GB cap; the earlier 5.7 GB planning target is informational
  after that reserve has been spent. Final measurement counts all retained files
  without exclusions or reserve subtraction.
- Two new safety regressions first failed as expected, then the minimal post
  helper changes passed all 21 tests. Main retirement code/scope did not change.

## Post-retirement rebuild results

- Native source post1 completed successfully: 377 instances, unchanged staged
  and active source, namespace checks passed. The source-only qualification
  archive remains distinct from the compiled-overlay preservation release.
- Asset c8post passed older archer4 three-LOD recovery/cook/comparison, current
  furred buffalo and skirmisher fresh native cook/readback/rig contracts, and stone
  fortified Hideout native cook/readback. It restored 24 named historical inputs.
- Package post1 exactly reproduced final-v1 ZIP SHA-256 and its embedded accepted
  SGA. All 1,417 member bytes/mounts are unchanged.
- Static post1 failed because three historical test fixtures had been packed.
  Failure logs remain plain evidence. The frozen tests were not changed.
  ResourceStore.restore_required and the Validate action now restore exactly
  official/ui.scar, range-inventory.json and baseline/source.zip from 0.7.12
  recovery before tests, verify existing files/refuse edits, and record new copies.
- The fixture-preparation regression failed before implementation; all 22 safety
  tests then passed. Static post2 passed 17 gameplay regressions, tuning and SCAR
  validation, plus a freshly refreshed official inheritance audit with zero
  errors. All three restored fixtures are tracked for exact generated cleanup.
- Independent follow-up review passed both post-phase accounting and fixture
  preparation changes, with no important findings. Full post preservation and
  separately reviewed exact generated cleanup remain pending at this checkpoint.

## Completion

- Full post-retirement preservation passed before generated cleanup and again
  afterward: all 5,030 protected originals, active source, 300 normal baseline
  hashes, current delivery, both exact rollbacks, all 12,392 new unique payloads
  and 9,649 old recovery keys. All seven configured links pass.
- Independent review passed exact generated manifest SHA-256
  `7671bd54979025d0888fa714a2ff3bd6741854c96c49c69c5b9409c6c147a046`.
  All 2,341 copies retired successfully, including 27 restored original duplicates.
  The saved evidence ZIP contains 1,819 CRC/hash-verified metadata/log entries.
- Removed 14,949 empty owned directories using rmdir only. No configured link or
  protected input was removed. The actual final measurement includes all retained
  files without generated exclusions or reserve subtraction.
- Final independent review passed strict current ZIP, exact rollback integrity,
  actual allocation and development handoff. Initial stabilized measurement was
  5,694,930,944 allocated bytes; the report/final-storage.json include the final
  review receipt and documentation after that checkpoint.
- All five implementation tasks completed. Current entry: README_080.md and
  docs/DEVELOPMENT_080.md; exact totals and gates: docs/RELEASE_080_REPORT.md.
- Import, fresh-match appearance/behavior, save/load and multiplayer remain
  explicitly unverified. No installation or publication occurred.
