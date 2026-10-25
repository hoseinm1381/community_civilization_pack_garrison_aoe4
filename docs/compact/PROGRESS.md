# Compact publishing ledger

Spec: docs/COMPACT_WORKSPACE_DESIGN_20261025.md plus owner steering: keep shipped Ogg instead of WAV originals.

Ruling: use a new independent repository instead of a linked worktree because the owner explicitly requires fresh Git history; retain old history in the untouched original repository.
Ruling: exclude WAV masters from the upload only; originals remain in the original snapshot. Do not weaken historical audio proof. Current bank verification will validate retained Ogg directly.
Ruling: keep all editable art and resource-recovery stores until exact active dependency closure supports narrower retention. A small unsupported package is not a successful reduction.

Task 1: in progress.

Task 1: complete — compact selection/repack tests passed.
Task 2: complete — 58,048 files / 42,964 chunks / 171 packs verified, packed bytes 5,957,859,850. All 10,529 shipped Ogg hashes verified.
Task 3: complete — supported compact CLI, fresh official inheritance audit, optional new offline voice helper, Blender path repair and nested art-input recovery.
Task 4: in progress — exact isolated 0.8.4 archive reconstruction passed (11,973 members/mounts); all 387 Blender files / 2,893 external images resolved. Native source invocation exercised 377 full-burn instances; explicit completed-burn marker still absent from captured log.
Review: independent reviewer found no archive-integrity blocker; relocation receipts now append and missing donor references were mapped/recovered from retained stores.
