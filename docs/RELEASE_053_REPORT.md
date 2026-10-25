# Community Civilization Pack 0.5.3

Final release requested by the user on 2026-10-18 without another in-game test.
This supersedes the proposed 0.5.2 native acceptance gate. No final 0.5.2 was made.

- [Final ZIP](F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_053/community_civilization_pack-0.5.3.zip), 73,100,361 bytes.
- ZIP SHA-256: `8f5bca3e884e26012518dbdfcada4fc3e31d8a9025b44e3e88c0a08d9f6e1bb1`.
- SGA SHA-256: `af202bcb644b4a8c74ff4a598a5374fff7c7a3df47457f3eee5c2195509b6456`.
- Identity remains `community_civilization_pack`, GUID
  `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`; credits `hosein81 and chilly5`.

## Changes and preservation

The compiled archive is exactly the 052 Test C payload, with final 0.5.3 manifest
and release documentation. Relative to frozen 0.5.1, exactly four of 811 archive
members changed; 807 remain byte-identical, with no additions or removals:

| Resource | Change |
| --- | --- |
| `art/scenario/cccastle/imperial_citadel/model.rrmaterial` | Structure material `options.z` from 0 to 1 |
| `art/scenario/cc050/imperial_citadel_campaign/model.rrmaterial` | Same material update for campaign consumer |
| `art/scenario/cccastle/resistance_hq/model.rrmaterial` | Same material update |
| `attrib/abilities/vietnam/vn_activate_stealth_forvills_vit.rgd` | Passive self-disable false, recharge zero, passive queue false |

Custom landmark designs, geometry/triangle counts, actors, stamps, lifecycle
bindings and victory owners remain unchanged from 0.5.1. Archer activated stealth,
traps and both monastery tiers are byte-identical to 0.5.1. The native stealth tree,
ten-second duration, 33 m range and existing carriers remain unchanged.

The active Garrison villager ability XML now matches the compiled source overlay.
Its prior bytes are retained under `output/release_053/baseline`. Every unrelated
active source, normal-edition file, identity and frozen historical art/tool/test
input passed preservation checks. Separate 060 authoring was neither changed nor
included. Previous release ZIPs and diagnostic A/B/C packages remain preserved.

## Evidence and limits

The retained source cook exited normally with code 0, validated 280 instances and
compiled exactly the three intended ability fields. The final archive's CRC,
identity, member set, four-resource allowlist, payload hashes, one root manifest,
ZIP readability and manifest/embedded-SGA agreement passed. No additional native
cook was needed because the SGA bytes did not change from Test C. Live Reload was
disabled for the source cook; no Blender scene was changed in final packaging.

The user's Diagnostic A result confirms that the stock landmark models render.
The custom-material change and automatic stealth continuity have not been tested
in-game. Finalizing this release does not turn those unknown outcomes into passes;
the user explicitly removed another test as a delivery requirement.

## Editable inputs and future builds

- `art/recipes/release_053/integration.json` identifies the frozen 0.5.1 archive,
  four retained native payloads and source/cook/material recipes.
- `output/release_053/source-overlay` retains the final gameplay XML, also applied
  to active `assets/attrib/instances/abilities/vietnam/`.
- `output/release_052/stealth/native/rsc03` retains the successful cook, logs,
  compiled ability and receipt; prior failed runs remain diagnostic evidence.
- Original editable landmark assets and the 052 material recipe remain required
  dependencies. No geometry was recreated for 0.5.3.
- For later release work, start from the 0.5.3 archive or reapply all four payloads;
  rebuilding gameplay source alone does not include the material patch.

Read-only verification command, from the Garrison root:

```powershell
& 'E:\Blender5.2\5.2\python\bin\python.exe' 'tools/release_053/verify.py'
```

No new regenerable 053 cook/readback caches were produced. Reclaimed bytes: zero.
Retained 052 readbacks and native records are used by the rebuild/allowlist checks,
so they were preserved with all authoring assets and rollback releases.

Close AoE4 before importing the final ZIP into Garrison. Enable it and select
Community Civilization Pack as both Game Mode and Tuning Pack; choose China,
then Vietnam. Client installation and publication were not performed by this task.
