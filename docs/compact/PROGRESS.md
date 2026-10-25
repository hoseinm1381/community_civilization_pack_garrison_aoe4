# Compact publishing ledger

Spec: docs/COMPACT_WORKSPACE_DESIGN_20261025.md plus owner steering: keep shipped Ogg instead of WAV originals.

Ruling: use a new independent repository instead of a linked worktree because the owner explicitly requires fresh Git history; retain old history in the untouched original repository.
Ruling: exclude WAV masters from the upload only; originals remain in the original snapshot. Do not weaken historical audio proof. Current bank verification will validate retained Ogg directly.
Ruling: keep all editable art and resource-recovery stores until exact active dependency closure supports narrower retention. A small unsupported package is not a successful reduction.

Task 1: in progress.

Task 1: complete â€” compact selection/repack tests passed.
Task 2: complete â€” 58,048 files / 42,964 chunks / 171 packs verified, packed bytes 5,957,859,850. All 10,529 shipped Ogg hashes verified.
Task 3: complete â€” supported compact CLI, fresh official inheritance audit, optional new offline voice helper, Blender path repair and nested art-input recovery.
Task 4: in progress â€” exact isolated 0.8.4 archive reconstruction passed (11,973 members/mounts); all 387 Blender files / 2,893 external images resolved. Native source invocation exercised 377 full-burn instances; explicit completed-burn marker still absent from captured log.
Review: independent reviewer found no archive-integrity blocker; relocation receipts now append and missing donor references were mapped/recovered from retained stores.

Task 4: complete — 22 tests passed; exact isolated archive reconstruction and selective integration passed; repeated configure preserves relocation history and restores all 1,005 input keys; all 387 Blender image references resolve. Original-source native invocation and remaining unconfirmed gates are explicitly bounded in READINESS.md.
Task 5: in progress — independent review clean; fresh source commit and bounded input batches being written. No push.

Publication preflight: remote heads listing is empty (read-only check); release_073 identity checker passed against the rebuilt final SGA. New Git storage is independent, with no alternates. Global Git trust settings are unchanged; publisher uses exact per-command trust for this exFAT repository.
Ruling: keep fresh main locally under the approved ready-for-publishing scope; no merge, PR or push is requested.

Task 5: complete — fresh source commit plus nine input batches prepared; bounded largest input batch 744,750,967 bytes. Final verification evidence and publisher list added. No publication performed.
