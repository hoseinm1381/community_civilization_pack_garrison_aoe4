# Garrison 0.7.10 implementation ledger

Authority: approved user plan in this chat, 2026-10-24. Baseline final 0.7.9 is user-tested and accepted. Garrison only; normal remains unchanged.

## Required outputs

- Sparse short fur on playable buffalo and all three Ministry decorations, native rig and lifecycle preserved.
- Distinct reinforced timber/bamboo/stone-base fortified Hideout, both branches and campaign variants; base art and gameplay preserved.
- Small steady owner-only active-supervision marker.
- Original gold Dai Viet dragon on deep red scoreboard icon, Vietnam players only.
- Vietnam living-buffalo/current-native-cap HUD counter; click cycles all living owned buffalo without orders.
- Influence-area boundary inward 2m, TC outward 2m, selection and placement, ONLY if presentation can be separated from gameplay. Explicit user fallback: omit and report if not achievable.
- Strict 0.7.10 ZIP, source/export/cook/readback/package evidence. No installation, publication or cleanup.

## Preservation and decisions

- Storage verification passed for all seven required junctions. Python 3.12.14 verified; native Garrison modules use configured Blender Python.
- Frozen exact accepted SGA f3e738f96e865f27b20d7d423bf3250b9a53dbea8b3414ecffe2d4ff040cc20d and ZIP 7d66c6eecfb57feac8e380d6a66d53f7fae55eb32dfc9e263fc962124562ee0e.
- `output/release_0710/baseline` contains immutable copies, 429 active input hashes, 300 normal asset hashes, and source.zip.
- Ruling: use immutable release snapshots instead of Git worktree. No Git repository exists in this workspace; preserve current project and external-storage architecture.
- Ruling: preserve historical `workspace.json` release value until final metadata integration; authoritative baseline is final 0.7.9 receipt, not stale 0.7.4 workspace version.
- Shared native-work lock serializes background Blender and native cooks. Live Blender scene is untouched.

## Work owners

- Buffalo and Ministry: buffalo_0710 worker, separate 0710 sources and media payload.
- Fortified Hideout: hideout_0710 worker, separate 0710 art and private visual bindings.
- HUD and supervision marker: hud_0710 worker, official UI-derived conditional overrides and presentation module.
- Main agent: influence investigation, preservation/package integration, release checks and review.

## Status

- Baseline: complete.
- Art, HUD, native cooks and package: complete; strict delivery is `output/release_0710/delivery/final-v1/community_civilization_pack-0.7.10.zip`.
- Final verification: 14 changed, 23 added and 1,378 untouched members; exact hashes/mounts, normal preservation and archive identity passed. See `docs/RELEASE_0710_REPORT.md`.
- Influence display resizing omitted under the user's approved fallback; gameplay ranges unchanged.
- Native fresh match/save-load/multiplayer: unverified; package proof will not be represented as gameplay proof.
