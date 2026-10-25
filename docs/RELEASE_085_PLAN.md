# 0.8.5 chatter and working-set consolidation

User-approved scope: shared five second selection/order/activity speech gate,
eight second movement reply gate (land and naval), fifteen second under-attack
gate. Suppress command/activity echoes. Preserve existing effort media/timing and
gameplay. No synthesis, download, install or push.

1. Inventory logical/allocated external bytes and validate links.
2. Add failing Lua behavior regressions; implement isolated 085 dispatcher;
   run inherited and new tests.
3. Overlay only the dispatcher in exact 084 owning SGA. Update ZIP metadata;
   verify namespace, all member bytes/mounts and unchanged audio.
4. Retire only hash-verified recoverable cold material after restoration checks.
   Keep sources, current/rollback releases and restoration guides. Losslessly
   archive unique installed dependencies before retirement if worthwhile.
5. Verify links/packages, record reclaimed allocation, review and deliver.

Interfaces: dispatcher to assembly uses canonical UTF-8 bytes. 084 archive and
verification to 085 policy allow one existing SCAR member. Cleanup to immutable
contributor store requires exact hashes and isolated restore, never deleting Git
packs. Historical 084 templates and evidence remain untouched.

Native import, audible behavior, save/load and multiplayer remain separate gates.

## Completion evidence

All five steps complete. Final-v2 package integrity is in
`output/release_085/final-integrity.json`; exact one-member policy and original
mounts are in its verification.json. 112 inherited + 23 new tests pass. Protected
source/art/normal edition audit passed 7,846 unchanged, one prior approved edit,
zero errors. Independent review findings and fixes are recorded in
`output/release_085/review-notes.json`. The owner subsequently prohibited
contributor-folder access; indexed preparation stopped before deletion.
Independent local bundles were fully reconstructed/read back and isolated
restoration tested before original-file hash checks and retirement.
`consolidation_085/summary.json` reports net allocated-file savings of 38.85 GB
after accounting for the bundles and new packages. No native game acceptance
was claimed, and no further operation is pending.
