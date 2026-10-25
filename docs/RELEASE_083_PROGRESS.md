# Garrison 0.8.3 execution ledger

Plan: `docs/RELEASE_083_PLAN.md`. Spec: `docs/SKIRMISHER_VISUAL_ANALYSIS_20261024.md` and the user's approval to redesign all ages and package 0.8.3.

## Recovered checkpoint

The chat "Assess Garrison 0.8.0 buffalo" authorized the full skirmisher II-IV and weapon redesign. The accepted buffalo idle/walk pilot is the owning baseline. Resume selected r12 exports and successful native cook v3; do not rebuild the earlier pilots or alter normal source.

- Baseline and protected/normal hashes: `output/release_083/baseline`.
- Selected nine source/export revisions: `art/recipes/release_083/selection.json`.
- Native completion: `output/release_083/cooks/v3/native-cook.log` records intermediate SGA copied to final output; receipt pins its hash.
- All nine native decodes passed: `output/release_083/cooks/v3/decoded-proof.json`.
- Existing failed cook and QA logs are preserved as diagnostics.

## Rulings and repairs

- This checkout uses isolated release paths rather than Git worktrees. No historical sources or deliverables are rewritten.
- DDS projection reverses image rows and decoded mesh UV V together. The old QA compared source UVs/pixels directly with native DDS rows and failed at error 1.0. Pixel comparison must reflect rows; coverage must use actual decoded mesh UVs. The prior native-mask probe independently measured approximately 38% Age-II surface coverage on all three LODs.
- The preview importer may replace its placeholder object. QA removes any remaining placeholder by name instead of dereferencing an object the importer removed.
- Native weapon socket origin is not the grip. The source socket-to-hand assertion failed by 0.578 m during idle while rest contact was 0.013 m. Validate transformed grip and unchanged native actor transforms; do not edit the rig to force the socket onto the palm.
- Bind matrices must be checked in addition to names/partitions. QA compares the entire native SKLN bind-transform block against the working baseline.
- Independent review uses the configured Blender Python 3.13. Its `garrison_shared.relic_chunky` import succeeds; another interpreter's failure is not a packaging blocker.

## Remaining gates

Complete selected-source QA and previews, assemble final 0.8.3, independently recheck archive/ZIP preservation, resolve review findings, and write the final report. Client import, new skirmisher native appearance, save/load and multiplayer remain separate acceptance gates.

## Completion checkpoint

Selected delivery: `output/release_083/delivery/final-v2/community_civilization_pack-0.8.3.zip`. Cook v3, QA v6, final nine-family native decode and fresh full-archive/ZIP verification all passed. Three allowlist tests passed. Final archive has 1,421 members: 48 existing media members changed, 1,373 exact, no additions/deletions and unchanged mounts.

Ruling: preserve both native SKMS and STMS geometry chunks. Independent review detected the old SKMS-only graft before delivery; rejected final-v1 is diagnostic. Final-v2 geometry equals the fresh cook and all other actor/control chunks equal the baseline.

QA now measures transformed weapon grip in five held states, with maximum distance 0.053376 m; death remains deformation-only because its native socket releases/stows the weapon. Bind blocks are byte-exact. Consistent preview lighting uses one light set per LOD.

Evidence and SHA-256s are in `docs/RELEASE_083_REPORT.md`, `art/recipes/release_083/integration.json`, `output/release_083/completion.json` and `final-recheck.json`. No installation, publication, deletion, normal edit or live-scene mutation occurred. Native skirmisher appearance/import/save-load/multiplayer remain unverified.
