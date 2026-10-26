# Current Garrison workspace handoff

## Owner-approved single-workspace policy — 2026-10-26

Develop in this existing Garrison folder. Reuse its source and current tooling;
do not create per-version checkouts/worktrees/full source copies or backup ZIPs.
Use Git commits for tracked-source history and rollback, a reusable
`staging/current` for native build products, and `output/current` for the current
delivery and compact receipts. Keep immutable Git/content-addressed rebuild
inputs and required ignored art/audio/recovery assets: Git alone does not cover
ignored data. Do not delete those stores or old deliveries as an incidental
part of implementation.

The current authorized task is a functional Persia port with existing visuals,
followed by local GitHub readiness. Full Persian art is the next milestone.
Preserve Garrison identity, Vietnam's current art/voices/compiled fixes and the
Normal/original-Persia source. Do not push; tell the owner when the Garrison
branch is ready for their manual push. This supersedes historical requirements
to create fresh per-version source/staging trees. Keep source/static, actual
native burn, archive/package proof and game acceptance as separate gates.

Parent instructions still apply. Current packaged milestone is **0.8.8**; read
`docs/DEVELOPMENT_085.md`, `docs/RELEASE_088_DELIVERY.md`, and `COLLABORATION.md` before resuming. Historical
release commands/freezes are provenance, not instructions to rebuild old milestones.

The owner continues developing in this E: workspace. Shared contributor checkout:
`F:\aoe_4_temp\community_civilization_pack_garrison_aoe4`.

When the owner requests a milestone sync, use its `docs/MILESTONE_SYNC.md`, retain
previous immutable indexes/packs, export changed source/art/rebuild inputs, update
discoveries and AI guides, verify restoration/package preservation, and report push
readiness. Do not push or install a synchronization automation without instruction.
Do not mirror with deletion or overwrite a contributor's unreviewed edit.

The shared data contains lossless editable art, voice masters, recovery inputs,
diagnostics and releases; installed tools/models are separate local dependencies.
Do not interpret either temporary-folder names or installed-cache names as permission
to delete. The completed cleanup is narrowly journaled under external
`consolidation_084_collaboration`. Do not rerun historical retirement commands.

Keep the existing GUID/bundle/NiceName, compiled-only owning-resource fixes, normal
edition isolation, editable buffalo deviation and current rollback. Future packages
start from the final owning archive with an explicit member-change policy. Report
source/static, native compilation, cook/readback, package and game acceptance as
separate gates. No further voice generation or extra model download is pending.

The historical 085 hold on contributor-folder access was superseded for the
explicitly requested minimal 088 update. Future synchronization still requires
an owner request and must use the compact current-work policy. 085 cleanup uses independent local
lossless ZIP bundles under external `resources_085`, with per-file restore hashes
and operation journals in `consolidation_085`. Restore only needed prefixes using
`tools/release_085/cold_storage.py`; never delete these recovery bundles. Current
compressed playback audio remains embedded in the owning release archive.

087 changes only Phổ Minh Tower resource drop-off and the three-age Skirmisher
selection group. Use the 087 source-change policy and typed deltas; retain the
086 dispatcher, compressed playback bank and all unrelated owning resources.
Native build staging is restored from 087-native-development.zip if needed.

088 repairs the Flooded Citadel moving_ext assertion and adds Phổ Minh’s explicit
resource_drop_off interaction. The mobility admission generator normalizes
comma-space removedIds; regenerate after unit additions or game updates. Keep
all existing art/audio/cooldowns and use the current owning archive. The compact
GitHub folder now has an 088 delta index; do not run the broad historical exporter.
