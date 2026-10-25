# Community Civilization Pack 0.2.1

Two scratch pit traps replace the above-ground stake arrangements. The Ministry
retains its hall and storage wing with stock-inspired worn timber/plaster,
weathering, varied tile surfaces and a larger outdoor yard containing three
full-size static stock worker elephants. Its placement area changes from 8x8
to 16x16, explicitly approved by the user; costs, research and production stay
unchanged. Pit depth is modeled above the terrain plane; terrain is not excavated.

## Delivery

- ZIP: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_021\community_civilization_pack-0.2.1.zip` (29,474,814 bytes).
- ZIP SHA-256: `01e034c8ce692ff34b050bc443c71f2cdcad751cb9a1fb3fa4c87e996449216b`.
- SGA SHA-256: `e9ae2e1f61a05c37fac96b932578e1f6121ee8bf131e2123495a96fd5e764821`.
- GUID: `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`; key `community_civilization_pack`; strict `garrison.mod/v1`, version **0.2.1**.
- Accepted 0.2.0 remains in `archives/release_020_user_accepted`; user reports
  it good without specifying scenario coverage. The earlier warning was caused
  by a different tuning-pack selection; no gameplay repair was made.

## Sources and rebuilding

Editable root: `E:\age of empires 4 mods\01_Custom_Civilizations\Community_Civilization_pack\Community_civilization_pack_garrison`. New blends/textures: `art/authoring/traps_021` and
`art/authoring/buildings_021/ministry`. Matching `art/exports` folders retain FBX
and maps. Recipes: `art/recipes/release_021`. Scripts: `tools/release_021`.
Heavy data and evidence: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_021`. See STORAGE.md for ownership.

Run `tools/build_release_021.ps1` from the editable root for a fresh cook and
release. Use `-VerifyOnly` for existing-package verification. Both require F:
and the seven expected junctions. Authoring regeneration commands and stock donor
hashes are recorded in worker handoffs/recipes; old editable assets are retained.

## Verification

- Fresh Garrison art cook: `321b7dfa90825502de648997e549ab629214798f7fdf78fb79e79cf0f79fb594`; generated mode/Live Reload off.
- Fresh isolated Content Editor source build validated 255 instances:
  `f3a42268631a7245765b071dd0d25cee95eb3c74ccfb9ace77e98e4bd20bb6f7`. Only its measured Ministry actor is integrated.
- Fresh exact-model native reference cook and readback: `integration/reference-cook.json`.
- Archive baseline: 475 members; final: 484.
- Exactly 10 existing members changed: nine visual
  model/geometry/material resources and the Ministry actor's footprint scalars;
  9 approved texture members added; 465 prior members byte-identical.
- The only gameplay exception is the Ministry site footprint x/y (normal and
  campaign) from 8 to 16. All other active source/compiled gameplay, SCAR,
  localization, bindings, stamps and lifecycle RGO owners remain identical to
  0.2.0. A typed native actor comparison proves the exact scalar delta. Normal edition
  and prior editable art are checked against frozen hashes.
- 68 tests; exactly 2 inherited donor-comparison failures,
  no additional failures, skips or errors. Static tuning validation passes.
- ZIP CRC, unique manifest and embedded SGA hash verified before/after cleanup.
- Removed 161,245,531 bytes of regenerable readback output;
  rebuild inputs, cook evidence, previews, deliverables and rollback preserved.

## Installation and native test gates

Import the ZIP into Garrison with AoE4 closed. Enable it and select Community
Civilization Pack in **both** Game Mode and Tuning Pack. Choose China, then Vietnam
in the opening selector. Do not select companion_tuning_pack or Vietnam v2.

Test both traps on different terrain/slopes, upgrades, construction, attacks,
destruction and four-second expiry. Test Ministry construction, repair/damage,
research, worker-elephant emergence, yard clearance, enlarged placement near
other buildings and worker paths, two player colours, near/far views, and
unchanged Chinese buildings. All three yard elephants are decorative/static.

Client import, lobby selection and native appearance/matches have not been run
for 0.2.1 by this build. Multiplayer remains unverified. Reimport accepted 0.2.0
with AoE4 closed to roll back.
