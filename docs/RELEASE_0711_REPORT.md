# Garrison 0.7.11

Built 2026-10-24 from the exact delivered 0.7.10 archive. Credits: hosein81 and chilly5.

## Changes

- Farm supervision now uses a static 14px icon at 65% opacity. Its private UI branch bypasses the tutorial TagAdorner, including its animated arrow, entrance animation and edge clamping. The local presentation helper removes the marker when the farm leaves the camera view and recreates it when visible again. Owner-only visibility, replay suppression and work-end cleanup remain intact.
- The buffalo counter displays whole-number text such as `8/15`. It reads generated presentation data from the existing native default/campaign buffalo squad requirement, not the medic population pool. Living-owned count and click cycling remain unchanged.
- The existing Dai Viet dragon is applied as the civilization badge for all 177 private Vietnamese blueprints with UI information: 100 entity definitions and 77 squad definitions. These include units and buildings, their private tiers and campaign variants. Portraits remain their original unit/building images. Shared Chinese/other-civilization blueprints are not overridden.

## Root causes and official contracts

The prior marker changed only its body template. CardinalHUDPage's PositionTags template independently supplied `TagArrowDataTemplate`, `ClampMode=Custom` and animated `TagDataTemplate`; those continued to draw attention off screen. The new private boolean in the tag data routes supervision through a direct ContentControl. Normal tutorial tags retain their original branch. `TagData.Data[...]` follows the current official template's `Data[Message]` dictionary contract.

The previous counter used `Player_GetCurrentPopulationCap(..., CT_Medic)`. That population channel is not the active buffalo training cap. The current mode does not import the legacy `buffalo.scar` medic-cap module. Actual training uses `required_squad/max_squad_cap=15` in both buffalo variants. Preparation reads that XML requirement; packaging also verifies both values in the actual frozen native squad RGD. The UI contains no separate hand-maintained limit. `%d/%d` formatting avoids floating-point display text.

Current installed ScarDoc explicitly supports `UI_OverrideUIProperty(pbg, "flag_icon", value)` for entity and squad UI information, called at script loading. Official `missionomatic/missionomatic.scar:1088-1093` supplies matching unit flag examples. The generated badge module uses the same path convention and only destination-GUID-qualified private blueprints. The cap and badge modules are imported by the existing presentation module during script loading.

The camera gate uses official `Misc_IsPosOnScreen(position, 0.90)`. Official `camera.scar` and `scarutil.scar` provide matching usage. Its nondeterministic result affects marker presentation only; no income, assignment, command or population decision depends on camera state.

## Verification

- Regression tests first reproduced the old failures, then all 13 focused tests passed. Tests cover medic cap zero, integer count/cap text, cap-source changes, stable buffalo cycling, death/ownership filtering, zero-unit clicks, local player/restore/cleanup, camera pans, owner/replay/work-end marker removal and all 177 private flag override calls.
- Current inheritance audit: 198 local and 5,758 official blueprints, zero errors. No tuning extension or XML value changed.
- Installed tuning validator: 377 instances, zero errors; 131 existing warnings and one unresolved-reference summary retained.
- Four SCAR static checks: zero errors. Existing warnings remain: one presentation loader-contract warning and two Paddy warnings. The generated modules have no static warnings. Their loader/import chain and the borrowed squad observer ownership were inspected; no group-lifetime change was introduced.
- MCP check_code: no low-confidence APIs or missing localization IDs. Reported unknowns are same-file helper functions and the parser's `and`/`or` tokens. Current installed API records and official UI donors are preserved under `output/release_0711/validation`.
- Both changed XAML files pass .NET XmlReader and ElementTree. Current official donor bytes match the frozen official 0.7.10 donors.
- Isolated Content Editor build `native/v1` completed successfully, validated 377 instances and passed archive identity checks. All four final SCAR files match native cooked readback. XAML uses the established Garrison loose-UI package route; the source burner does not compile those templates into its source SGA.
- Final package: four existing data members changed, two added, all 1,411 untouched member hashes and original mounts preserved. All tuning/model/animation/texture bytes match 0.7.10. All 300 frozen normal source hashes and 72 protected 0.7.10 rebuild inputs remain unchanged.
- Final ZIP CRC/readability, exact three-file layout, strict version `0.7.11`, embedded SGA hash and namespace `b7fcea91257b408fb9e8ae4d8bc402e1` passed.

## Delivery

ZIP: `output/release_0711/delivery/final-v1/community_civilization_pack-0.7.11.zip`

ZIP SHA-256: `d1c8731f762b6605ab14f2a626f3a430a39cf65743bad8aa4220f536d709b323`

SGA SHA-256: `dde327956440da9d99fcdfaf1a5253f84bb2f94f89841dbaf4a561eb708bf6b8`

See `delivery-proof.json`, `verification.json`, `art/recipes/release_0711/integration.json`, the source policy, native receipt and validation logs for complete hashes. Exact 0.7.10 ZIP/SGA and active source snapshot are frozen under `output/release_0711/baseline`.

## Reproduction

Version-owned tools are in `tools/release_0711`. Preparation generates cap data and badge inventory from native gameplay XML and the full current inheritance chain. `patch.py` applies exactly the four allowed presentation edits over the frozen source snapshot. `source_policy.py` rejects every other active-source change.

Run configured Blender Python with `native_compile.py <new-attempt-label>` for a fresh isolated source build under the shared native lock. Keep the generated native receipts and inputs. Run `validate.py`; the changed templates also need the .NET XmlReader check recorded in `validation/dotnet-xml.json`. Then run `tools/build_release_0711.ps1 -Label <new-delivery-label> -NativeLabel <completed-attempt-label>` to validate and reassemble. Existing delivery/build labels are never overwritten. The integration recipe pins all final scripts, tests, source members and proof receipts.

The existing editable dragon/buffalo artwork and its native textures are reused unchanged from 0.7.10. Blender scenes were not modified. No installation, publication or cleanup was performed.

## Remaining native acceptance

Fresh-match UI rendering, camera-pan behavior, flag appearance in all unit/building information and production panels, HUD scales, save/load and multiplayer are unverified in game. Build and package proof do not establish those outcomes. Test mixed China/Vietnam players, `0/15` and `8/15`, repeated buffalo cycling including working buffalo, Work/Leave, camera movement away and back, and both unit/building civilization badges. The existing keyboard/mouse HUD scope remains; the Xbox counter layout is not overridden.
