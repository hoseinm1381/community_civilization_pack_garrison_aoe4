# PAUSED at user request — 2026-10-18

User requested immediate pause because internet is being cut off for about two hours. Do not resume until the user asks. Workers were told to stop new jobs and save their own PAUSE-*-20261018.md checkpoints here. Preserve running atomic writes and all diagnostics; do not kill unrelated processes.

## Binding user decisions

- Overall seven representative designs APPROVED: "everything is good , but worker elephant need an update , put some wooden crate and stick on it".
- Worker Elephant must have NO rider. Both vn_unit_war_elephant_1_vit and _2_vit are workers; combat handcannon elephant crews are separate.
- Cargo authoring DONE and root visually accepted close/game views: art/authoring/release_060/representatives/elephant/elephant_finish_v3.blend SHA256 9dce4c9d30270cf6fb91b7644b4b1149667aabf8ff065f2c10de9b1b79c0cc9b. Open wooden crate + three sticks, 96 cargo triangles, stock wood UV region, spine1_m weighting. Native export/integration still pending.
- Full roster soon at highly acceptable AoE4 detail. Leave minor close-only flaws; fix defects even slightly recognizable at normal game distance. No Archer microdetail loops.
- NO computer use/browser/native UI automation. Blender MCP, AoE4 MCP, CLI/files only.
- Officials unavailable/excluded; preserve unused source. All eight villager gender/age bodies ARE active, including Age IV.
- Finish full roster then package 0.6.0 from exact FINAL 0.5.3. Credits exact: hosein81 and chilly5. No ships/buildings/gameplay changes.
- Native Rattan visual switch unqualified; may defer, retain art and existing +1 ranged armor behavior.

## Preservation / environment

Root: E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison
External: F:/aoe_4_temp/Community_civilization_pack_garrison_temp
Read STORAGE.md/workspace.json and run tools/release_060/common.guard before file operations. Only six release_060 roots owned. Normal edition, older releases, landmark/voice work protected. No Git repo.

Final baseline frozen under external output/release_060/baseline/final053:
- ZIP SHA256 8f5bca3e884e26012518dbdfcada4fc3e31d8a9025b44e3e88c0a08d9f6e1bb1
- SGA SHA256 af202bcb644b4a8c74ff4a598a5374fff7c7a3df47457f3eee5c2195509b6456
- Freeze SHA256 13309fc3c4d971f192f9c5eaf083e65ca9641d22611866ce3f3789cd0918f18d
- 811 native archive members, 314 frozen source files. Preserve all FOUR protected 053 payloads (three landmark RRMaterials and villager stealth ability RGD). Start exact archive, never source-only rebuild losing landmark fixes.

Shared native lock external output/release_020/native-build.lock: msvcrt first-byte lock, never delete. Serialize live/background Blender and serialize native cooks. Bundled Python in workspace.json; compiled Garrison APIs require py -3.13. Blender E:/Blender5.2/blender.exe.

Last fresh live MCP instance af802e4b-654b-4d5e-836a-c29941ae1a52, PID1928, initially Untitled clean. Ignore stale 5b28447b and d4a3c8d0 records. Rediscover before use; claims/file sessions can change. Artists owned exclusive Blender lease until pause; check PAUSE-ART checkpoint/processes. Last native pipeline reports lock released, no root native cook running.

## Completed this continuation

1. Approved style preserved in art/recipes/release_060/representative-style-approval.json. Historical approval selection unchanged. New representative-review-current.json switches only elephant to cargo v3. representative_review.py now accepts --selection; external output/release_060/review/representatives.html regenerated. Root visual finding at representatives/elephant/v3/root-visual-review.json. No computer use.
2. Six ranged tiers authored/exported, own exact donors, three LODs, real saved albedo rather than preview-only tint. See ranged-production-report.md, ranged_roster_060.py, export_archer2_approved_060.py. Five non-II tiers v4 under art/authoring/release_060/ranged_roster; Archer II derived from approved v3l input (input hash unchanged). FBXs three Skin /144 Cluster records. Native weapons/animations untouched.
3. Root visual review found ONE shared noticeable issue in five v4 non-II tiers: triangular sawteeth on right edge of front owner-color patch, caused by centroid-selected triangle UV remap. Artist told ONE shared v5 corrective pass, clean fitted owner panel/sash, preserve equipment/armor/owner readability, no further tiny polish. HOLD native cooks of those five v4 exports. Archer III v4 native qualified as route diagnostic only, not final art selection.
4. Archer II v1/v2 snapshot triangulation mismatch diagnosed (98 quads alternate diagonals). Artist exported explicit triangulated v3 copies, preserving approved source/appearance. Pipeline confirms NEW Archer II v3 fresh native cook/readback/compare QUALIFIED: 1484/522/155 triangles, exact topology/weights/UV within tolerances, 48/46 bones/palette. Native albedo-only variant v60a2 also verified: exactly three albedoTexture changes; all other material chunks/maps exact, stock RRGeom preserved before replacement. Read-only media admission at art/scenario/garrison/v60a2/body/body.rgm. No active source or final archive graft.
5. Generic authored pipeline tools/release_060/authored_geometry_060.py, test_authored_geometry_060.py, authored-geometry-report.md. Tests six passed. Captures authored geometry expectations rather than demanding edited model equal stock shape; UV preflip, weights, bind, three native LODs. Blank scaffold descriptor attrib/<key>.rgd allowed as diagnostic; no actor/RHKA integration. New ranged_media_pairs_060.py checks stock native RGM except private logical path, native RGO, albedo-only RRMat, qualified authored RRGeom/group/material/LOD binding compatibility. Final pairing batch not finished.
6. Villager 73/46 route previously qualified for deforming geometry; only unskinned childless metarig_pelvissocket local rest delta 1.3527423 mm disclosed/accepted. Do not recook all rigs to fix this invisible leaf. Pipeline narrowly allows <=.0014 for this measured unskinned childless leaf while enforcing active palette/bind/all other bones .0002.
7. Four Spear age I-IV authored blends already exist in art/authoring/release_060/representatives/foot_tiers/chi_infantry_light_age0N/..._v1.blend. They cover ordinary AND fire spears. Artist assigned export-ready join/real native albedo/three native LODs/corner snapshots next, then ALL EIGHT civilian bodies. Check PAUSE-ART checkpoint for actual completed exports since this file was written.
8. Luna completed 19/19 clean remaining actual donor decodes, including both active Age IV villagers. Strict exact index: external output/release_060/inventory/remaining-donors/run-004/batch-report-exact-index-v2.json. Exactly217 referenced RRtex,293 provider rows/16archives, index SHA256 96d5fe3c89a4403be72bc1d8796847eb2618745c49b2a9015edc4c1b7ef664cd. Existing run001/run004 receipts preserved. tools/release_060/remaining-donors-report.md. Siege tower construction stages, NOT normal LODs. Luna next resolving nine inherited stock consumers' actual render bodies (monk/trader etc); generic base_* animation owners are not render bodies and not proof of rigid geometry. See PAUSE-INVENTORY.
9. Private first ten foot body identities prepared/cooked/registered. New unit_binding_plan.py, cook_unit_identities.py, readback_unit_identities.py. Exact slot/consumer plan art/recipes/release_060/foot-body-private-binding-plan.json, SHA ebcff81c201ead2b3521f025387359d99e33ca0fa3a5b02b00d5b27d6f055acb. Native project external staging/release_060/i/Mods/v60ids. Successful SGA SHA1b10809679ffdfc6964acda34cd22f36ed915fb6434692df0659ab00f6be74be. Wrapper initially rejected expected attrib/v60ids.rgd; failed cook.json preserved, no recook. Readback registered10unique native PBGIDs at output/release_060/integration/private-foot-identities/registered-identities.json. Garrison clears parent_pbg identity metadata and changes ALL variant pbgids; after reversing only identity metadata, generated list bytes exactly stock. FINAL assembly must copy ORIGINAL native list and change private PBGIDs/render slots only, preserving original parent metadata/native animation owners. Do not integrate generated scaffolding.
10. Source overlay ONLY staged by prepare_foot_source_delta.py under output/release_060/integration/private-foot-source-overlay: 15 actors +10private attachment identityXMLs. Exact original XML node paths/count/mod/hash checks and byte-reversible narrow tag edits; active source untouched. Includes attached crew body consumer naturally through the shared TierIV HC body, not Rattan behavior. Three narrow source tests and four body plan tests PASS. Luna reviewed against frozen053: all15 source hashes exact/current,10newIDs no custom-source collision, no unexpected source issues. Full art/compiled binding/final SGA still pending.
11. inspect_variant_material_scope.py proves supported single albedoTexture variant overrides EVERY material: horse2twoatlases, combinedelephanttwo, nativeworkerelephantsix. Do not apply one image across mount+rider. Mangonel uses Structure albedoTex etc, not albedoTexture. Read-only report output/release_060/qualification/multi-material-variant-scope.json. No material patches integrated.

## Nonhumanoid unresolved routes (preserve diagnostics)

- Horse127-bone native control compiler changes58+46 palettes to103 and eight groups; not admitted as stock-RGM geometry pair. Elephant140 control ordered140/110 palette nearcompatible but group labels differ; no final admission. Mangonel14bone: generic exporter dropsUV2, direct twoUV exporter zeroSkin; NEVER nativecook zeroSkin FBX again. Genuine native riderless worker donor tug_elephant_worker_age01 exists,140 ordered skeleton same within<1e-6, but multipalettes/materials/cargo activation needs qualifying. All prior controls under output/release_060/qualification/nonhumanoid-route-preflight.
- Potential next research (NOT implemented/authorized as proof): preserve per-material native cooked variant components rather than global albedo override; installed model_variants.rewrite_material and relic_chunky native codec APIs available. No raw packed-map rebake or unverified binary patches. No arbitrary material replacement.

## Resume order

1. Read this and worker PAUSE checkpoints; inspect processes, MCP claims and shared lock without changing unrelated work.
2. Finish four spear exports + single shared ranged v5 owner-panel fix +eight civilians; no new style approval needed. Use actual supported donors and same-LOD weights.
3. Qualify actual final art geometry/materials through prepared pipeline; other five ranged awaitv5, ArcherIIv3 qualified. Keep cook/readback/import/appearance/gameplay/multiplayer evidence separate.
4. Finish MAA/repeater/monk/trader/scout/mounted/elephant/siege/crew/equipment families and all alternative consumers. Reduced geometry stock remixes allowed only with explicit scope disclosure and compatible proof.
5. Integrate visual-only delta into EXACT053SGA, expected-value allowlist/private resources, byte-preserve unrelated811members and4protectedpayloads. No060ZIP exists yet. No native-game/import/multiplayer acceptance claimed or performed.

Workers at pause: /root/ranged_production_060 (Sol art), /root/foot_export_pipeline_060 (Sol pipeline), /root/remaining_inventory_060 (Luna checks). User authorized these model roles and parallel owned work, shared Blender/cooks serialized. No other chats messaged.

## Pause confirmed by all three workers

All three PAUSE checkpoints are saved. No worker job remains running; Blender lease and native lock released. Only existing interactive Blender PID1928 remains, untouched. Spear I v2 export trial failed before FBX because of relative albedo path; partial files preserved. spear_export_060.py v3 fixes the path but is UNRUN. Ranged v5 shared edge fix and civilian authoring have NOT started. Inventory traced direct English body overrides for ram/tower/springald/both trebuchets; monk/trader attachment PBGs and siege-cart concrete crew route remain unresolved. Read worker checkpoints for exact commands and latest evidence.
