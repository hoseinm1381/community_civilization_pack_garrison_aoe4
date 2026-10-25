# Community Civilization Pack 0.2.0 test release

Garrison edition: four barracks ages, four town-center ages, shared rice-paddy farm
boundaries, shared Hideout design with both native upgrade states, and a scratch
Economy Ministry hall, store and elephant-handling yard. Original UI names/icons,
research and elephant production are preserved. No lumber/mining camps were added.

## Delivery

- ZIP: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_020\community_civilization_pack-0.2.0.zip`
- ZIP SHA-256: `b30c6972843c5bc6922e50e8c3b2e82de6a36b4dfb06fc07498f6a8674a5dd93`
- Combined tuning/game-mode SGA: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_020\package\community_civilization_pack.sga`
- SGA SHA-256: `05a03f4cded716be3a89997aa5739fd651227e400472ee80019aedced8933d85`
- GUID: `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`; key `community_civilization_pack`; version **0.2.0**.
- Exactly one strict `garrison.mod/v1` manifest and measured archive hashes.
- Candidate receipt: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_020\integration\runs\c020r020proof2\candidate.json`.

## Editable sources and rebuild

Editable root: `E:\age of empires 4 mods\01_Custom_Civilizations\Community_Civilization_pack\Community_civilization_pack_garrison`.
Blends and private textures: `art/authoring/buildings_020`.
Required exports: `art/exports/buildings_020`; recipes: `art/recipes/release_020`.
Native inventory and cook/reference receipts: `output/release_020`.
Donor caches and heavy generated data are under guarded F: storage; see `STORAGE.md`.
The separate accepted 0.1.0 rollback is `archives/release_010_user_accepted`.
Do not regenerate the immutable starting baseline from edited current source.

From the editable root:

```powershell
& .\tools\build_release_020.ps1 -VerifyOnly
& .\tools\build_release_020.ps1
```

The full command uses a new run label, fresh art cooks, isolated source compile,
native model reference validation and selective integration over the accepted
0.1.0 archive. Verification-only checks the existing delivery without a native cook.
Garrison-generated game-mode ownership and Live Reload remain off. Shared Blender
authoring and native cooks are serialized; unrelated live Blender work is untouched.

## Preservation and verification

- Normal edition: 484 original files unchanged.
- Accepted house/trap editable sources and exports: 214 files unchanged.
- Frozen 0.1.0 source: only ten approved actor visual attachment references change;
  eleven private visual attachment identity stubs added. Gameplay XML and compiled
  actor comparisons allow no nonvisual changes.
- Archive: 355 accepted members -> 475 final;
  10 existing actor members changed,
  345 existing members byte-identical,
  120 private members added. No original member removed.
- Native source compile validates 255 instances.
- Static validation: 255 instances, 0 errors,
  18 warnings, 1 info. Instance-version warnings
  cover the seven accepted and eleven new private identity stubs; native compilation
  accepts their serialization. The informational stock-reference summary is retained.
- Raw unit suite: 68 tests, exit 1, exactly two
  inherited weapon donor-comparison failures, no additional failures/errors/skips.
  Names: `vn_weapon_outpost_handcannon_bambo_alarm_chi` and
  `vn_weapon_outpost_handcannon_bambo_chi`. No gameplay or assertions changed to hide them.
- Final typed graph checks compiled actors, private lists/stamps/models/materials,
  textures and official terminals; all new members must be visited. Actual assembled
  media hashes are bound to successful native reference-cook inputs. CRC/member
  hashes and ZIP readability are checked independently.

Raw receipts: `source-preservation.json`, `release-checks.json`,
`archive-verification.json`, `package-verification.json` under `output/release_020`.

## Art evidence and limits

- Barracks/town-center source handoff and comparisons:
  `output/release_020/barracks_tc/ART_HANDOFF.md`. Eight donor remodels preserve
  topology/index/UV/owner-related bytes; source geometry and roof albedo changes
  are separately audited. Age I has textured comparisons; all four ages have
  solid donor/remodel comparisons. These are authoring views, not game screenshots.
- Ministry/farm/Hideout authoring evidence:
  `output/release_020/ministry_farm_hideout`. Shared farm edges retain native
  clearability; central rice crop, harvesting animator and terrain remain unchanged.
  Offline context previews may use labeled crop/terrain proxies, not the engine.
- Hideout preserves default/stone states and campaign scaffolding. Its added
  shelter uses a typed private native attachment-list graft; removing added nodes
  and reverting approved fields reproduces the original donor serialization.
- Historical material vocabulary draws on Thang Long timber/brick/tile evidence.
  The Ministry arrangement, elephant yard and age progression are artistic
  interpretations, not exact dated reconstructions. Later vernacular buildings
  are analogues. Requested percentages are qualitative visible redesign ranges.

References: [Thang Long excavation](https://hoangthanhthanglong.vn/en/initial-findings-of-the-excavation-of-the-kinh-thien-area/),
[Kinh Thien hall](https://hoangthanhthanglong.vn/en/kinh-thien-palace-the-heart-of-the-imperial-citadel-of-thang-long/),
[North Delta houses](https://journal.vnuf.edu.vn/vi/article/view/1397).

The user reported 0.1.0 tested and good; individual scenarios were not specified.
This new 0.2.0 ZIP has not been imported or tested in a native match by this build.
Native culling/LOD, flags/colours, animation/lifecycle presentation, firing origins,
elephant emergence and multiplayer behavior remain user-test gates. A successful
reference compile/readback does not prove engine rendering of every native state.

## Install and test

Close AoE4, import this ZIP into Garrison, enable it, and select both **Tuning Pack**
and **Game Mode: Community Civilization Pack**. Select China, then Vietnam in the
opening choice. Disable other editions for the initial isolated test.

- Existing/new barracks and all town-center variants through Ages I–IV.
- Construction, repair, cancel/delete, damage and destruction of all new visuals.
- Both farm variants: worker harvesting, isolated fields, adjacent fields and shared edges.
- Both Hideouts before/after upgrades: garrisoning, attacks, effects and scaffold states.
- Ministry: economic research, worker-elephant production and unobstructed visual emergence.
- Two player colours, near/far views, stock China isolation and 0.1.0 house/trap regression.

Roll back by using the preserved 0.1.0 ZIP; no client installation was performed.

## Cleanup

Verified cleanup removed 114689297 bytes of explicitly regenerable data; delivery hashes were checked before and after. Exact paths and restore commands are in `output/release_020/cleanup-verification.json`. Repeated cleanup totals are removal activity, not an assertion of cumulative net free space.
