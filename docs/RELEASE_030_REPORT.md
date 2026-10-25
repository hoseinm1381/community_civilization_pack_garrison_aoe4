# Community Civilization Pack 0.3.0

Built and independently ZIP-verified on 2026-10-17. Import and native matches
remain user acceptance gates.

## Delivery

- ZIP: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_030\community_civilization_pack-0.3.0.zip`
- Size: 34,761,605 bytes.
- ZIP SHA-256: `7e0ec19ed66f9bc72c35fe4f28e34113c107d70d7e841c060f960620f6dea3df`.
- SGA SHA-256: `d83fac3eedfc5b2802fd7c8a94752238e46d1323bee52208a62330c856c519b3`.
- Four ZIP entries: one `garrison.json`, one combined SGA, `START-HERE.txt`,
  `EVIDENCE.json`. Strict `garrison.mod/v1`, version 0.3.0, same package key/GUID.

## Changes

The Ministry placement returns to 8x8 in normal and campaign variants. Its hall,
yard, three elephants and every visual resource remain byte-identical to 0.2.1.
Only its four footprint floats change; compiled actor hash returns to the original
0.2.0 value. The visual compound extends beyond the reserved placement area by
explicit user request.

Both traps now use low irregular earth, woven bamboo and leaf cover, with small
broken stake openings. Neither has a continuous black surrounding rim or broad
black cavity. The actual final archive material/texture readback references only
the new v030 maps. Cooked 1024x1024 albedo mean luminance is 89.14 versus 43.25 in
0.2.1; near-black fraction is 0% versus 4.10%. These are texture statistics, not
native terrain-blending or enemy-visibility proof. Each trap has 1,474 triangles.

The two Feudal advancement landmarks are scratch-built historical interpretations:
Phổ Minh's stone/brick tower and modest rear temple court, and One Pillar's raised
timber shrine, column, modeled lotus pond and small supporting hall. Existing
names, icons, Feudal unlocks and all mechanics stay intact. The alternate One
Pillar/headquarters actor and normal/campaign variants share the appropriate art.
Phổ Minh has 10,016 triangles; One Pillar has 9,200. Stock completed healthy LOD0
drawgraph benchmarks are Academy 59,496, Zhengyangmen 98,762 and Aachen 90,258;
our assets remain below the measured median and maximum without padding geometry.
Historical sources and geometry methodology are in RELEASE_030_RESEARCH.md.

## Authoring and verification

Editable root is `E:\age of empires 4 mods\01_Custom_Civilizations\Community_Civilization_pack\Community_civilization_pack_garrison`.
Retained art lives under `art/authoring/traps_030`, `art/authoring/landmarks_030`,
matching exports and `art/recipes/release_030`. Seven landmark and eight trap
rendered views per design, validation and handoffs live under `output/release_030`.

- F: guard and all seven junctions passed. The 0.2.1 ZIP/SGA rollback is in
  `archives/release_021_user_accepted` with verified hashes.
- All 484 normal-edition files and 797 prior art/export/recipe files unchanged.
- Source policy proves exactly two new private attachment lists, six principal
  visual-reference changes across three actors, and the four Ministry floats.
- Blender/Garrison preflight passes; no non-manifold or degenerate faces.
  Recorded landmark contacts pass 33/33 and 13/13. Live MCP trap audits prove
  valid winding, UVs, stage ownership, one material/UV layer and no modifiers.
  Source/export hashes remained unchanged after inspection. The desktop viewport
  bridge returned black captures; visual review used the saved rendered views.
- Fresh Content Editor validation/build: 257 instances. Typed compiled checks
  preserve all other gameplay, SCAR, localization and lifecycle fields.
- Fresh Garrison cook and native reference cook/readback passed for all four
  models. Final cooked landmark bounds fit the existing 8x8 placement budget,
  including the conservative 112% animator-scale check.
- Archive: 484 accepted members -> 508 final. Exactly 10 old members changed,
  24 private members added, 474 old members byte-identical. Ministry art and all
  unrelated visuals are unchanged. Dependency/reference and loading coverage pass.
- 68 raw tests: exactly the two inherited donor-comparison failures; no additional
  failures, errors or skips. Static tuning validation exits 0.
- ZIP CRC, manifest uniqueness, embedded SGA SHA and post-cleanup delivery hashes
  passed. Repeat `-VerifyOnly` passed. Initial cleanup removed 177,652,716 bytes
  of proven regenerable readbacks; the receipt is retained in cleanup-history.
  Repeat verification regenerated/read/removed some data; those bytes are not an
  additional net saving. Sources, registered inputs, archives and logs remain.

Repeat commands, run from the editable root:

```powershell
.\tools\build_release_030.ps1 -VerifyOnly
.\tools\build_release_030.ps1 -Label r030rebuild1
```

The first verifies the existing delivery; the second performs the guarded fresh
identity/source/art/reference/candidate/package pipeline. Existing different
same-version delivery files are deliberately protected against silent replacement.
Stage switches and all exact invocation receipts remain in the release scripts
and `output/release_030/logs`.

## Installation and native tests

Close AoE4, import the ZIP in Garrison and enable it. Select **Community
Civilization Pack** in both Game Mode and Tuning Pack. Choose China and then
Vietnam in the opening selector. Do not select companion_tuning_pack or Vietnam v2.

Test both Feudal landmark choices through advancement, construction, cancel,
repair, attacks, damage/destruction/rebuild and later ages. Test Phổ Minh garrison
and Hideout training bonuses; One Pillar research, discounts and existing
production; all alternate consumers and worker access. Test Ministry adjacency,
worker paths and produced-elephant emergence with the restored 8x8 placement.
Test both traps on grass/dirt/snow and slopes, at near/far views, before/after
upgrades, attacks and four-second expiry. Check two player colours and unchanged
Chinese buildings. No import, fresh native-match, appearance or multiplayer pass
is claimed by this build report.
