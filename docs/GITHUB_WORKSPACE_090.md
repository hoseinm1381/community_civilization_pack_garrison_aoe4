# Sole GitHub workspace and independent 0.9.0 build

Owner instruction, 2026-10-26: develop Garrison exclusively in this repository,
F:/aoe_4_temp/community_civilization_pack_garrison_aoe4. E: is the independent
base-game/Normal edition and may only be read as a reference. Temporary work is
confined to F:/aoe_4_temp/Temp_before_github_push and is removed after a verified
successful push. Retain current delivery and compact evidence inside the repo.

Plan:
1. Fast-forward the existing main checkout to the verified functional 0.9.0
   source and compact inputs; replace the superseded E: workspace instructions.
2. Build from tracked source with the installed Content Editor and reconstruct
   the exact owning SGA/ZIP from tracked immutable inputs. Block Python reads
   of both former owner roots. Compare newly compiled Persian resources with
   retained current payloads; keep Vietnam compiled-only resources intact.
3. Verify store, voices and the editable-art input closure. Inventory the old
   external root without following junctions; identify build dependencies and
   optional voice production tools separately. Do not delete that old root
   merely because the packaged release reconstructs.
4. Review, commit and push main normally; confirm the remote SHA. Keep compact
   verification evidence, move final SGA/ZIP into output/current, then remove
   only the approved temporary root after confirming the push.

Ruling: exact package reconstruction is distinct from a native source/art cook.
Run the native source burn as well. Full art recooking and new speech generation
are outside this functional build test; stored editable inputs get a closure
check. A wrong closure conclusion could lose future authoring inputs, so the
old external root remains until uncovered dependencies are resolved.

Progress: existing F: main fast-forwarded from 1df2bb8 to 898faa7; old E: source
was read only to transfer its two verified commits. No old external input read
is permitted during the isolated build. Current implementation proceeds here.

Verified input closure:
- All 58,916 stored files / 43,843 chunks / 176 packs verified with both former
  owner roots blocked; shipped Ogg-bank verification passed.
- All 1,005 current art closure keys (2,520,087,829 bytes) read/hash-checked from
  Git packs and nested retained recovery stores; zero unresolved keys.
- Current official inheritance: 390 private / 5,758 official, zero errors.
- The old external root holds 33,997,913,853 logical bytes. Its 13,240,868,685-byte
  local-voice-tools.zip and 4,109,171,668-byte voice-development.zip are not used
  to rebuild existing speech. They retain optional model/runtime and original
  production/WAV/history inputs omitted from Git; do not silently discard them.
- No old external root deletion is part of this test. Exact current rebuilding
  establishes build independence, not permission to erase optional originals.

Ruling: F: is exFAT. Git-backed input reads use a command-scoped safe.directory
for the selected workspace only; global Git trust is unchanged. The regression
failed on F: before that fix and passed afterward.

Final review fixes (RED -> GREEN):
- Deleted or untracked native source inputs now fail exact inventory equality;
  the complete source snapshot must also match after compilation.
- A successful exit plus instance validation no longer qualifies: the native
  archive-completion marker and non-empty output archive are required.
- Git-backed reads honor workspace.local.json; Git trust is command-scoped for
  both input reads and the build's tracked-file lookup. No global trust changes.
- Final suite after fixes: 47 Persia/build checks plus 12 compact checks passed.

Isolation scope: Python open auditing resolves paths and denies both former
owner roots. Content Editor and archive/Git subprocesses are not OS-sandboxed
or I/O-traced; their explicit inputs/outputs use this repository, approved temp
and installed tools/game data. A static scan found no former-owner path strings
in the native source inputs. This is input-closure/build evidence, not an OS
isolation certification.

Final delivery verification:
- Native source burn completed in 449.392 seconds and validated 658 instances.
  All 751 source inputs remained unchanged; 309 fresh Persia compiled resources
  match the current release. The F: Git object database has no external alternate.
- The independently reconstructed SGA has 12,284 verified member hashes/mounts.
  Its SHA-256 is b1f59231d5b83d7414f4b3f3271eda13bef047b69ea611a2467dc67a7b23c7a3.
- ZIP: 286,406,635 bytes; SHA-256
  967e05a22a36a92c3f0757ffa18376c20c1b7ade402ae1b61ba4d926b4e27aef.
- Final SGA/ZIP and compact build evidence are retained in output/current.
  The tracked BUILD_090.json and INPUT_CLOSURE_090.json retain compact findings.
  No new full delivery, media bank or historical workspace is added to Git.
- Push and post-push cleanup confirmation are generated afterward in
  output/current/push-confirmation.json and cleanup-confirmation.json.
