# Vietnamese Castle Age — 0.5.0 asset and release handoff

Built from the exact completed 0.4.0 delivery. This supersedes the earlier
asset-only packaging boundary at the user's explicit request. Import and native
match acceptance remain pending.

## Delivery and preservation

- [0.5.0 ZIP](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_050/community_civilization_pack-0.5.0.zip>) — 73,221,547 bytes.
- ZIP SHA-256: `be5e3ac2e6b859ce2d4efdf591c3fa94b11af0e6a4e8e870ce723bcd53dfdb01`.
- Embedded SGA SHA-256: `78b90561306f6874872b5f88a5f82c3354e14fceebdf52cf0f0ffba28cbf1e80`.
- Frozen 0.4.0 SGA SHA-256: `b33168a31409c57096678bcda7fdd929e08c2ecc8b31de4148bb20f7f44898b6`.
- Final archive: 809 unique resource paths;
  6 existing resources changed and 114 added.
  All 689 other 0.4.0 resources are byte-identical.
- Final project GUID: `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`;
  credits: **hosein81 and chilly5**.
- [0.4.0 rollback](<E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison/archives/release_040_user_accepted>) is preserved.

## Editable assets and comparisons

Seven building variants are delivered: Imperial Citadel, Resistance Headquarters,
Castle/Imperial monasteries, Castle/Imperial siege workshops, and the shared keep.
The five ordinary variants use the actual Chinese donor geometry and native
owners. Visible redesign targets remain qualitative: monastery 65–80%, siege
30–40%, keep 25–35%; changed vertex percentages are not artistic change measures.

- [Editable Blender roots](<E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison/art/authoring/castle_next>).
- [Exports and textures](<E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison/art/exports/castle_next>).
- [Recipes and asset-stage integration manifest](<E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison/art/recipes/castle_next>).
- [Stock/remodel six-side and textured comparisons](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/castle_next/buildings/previews>).
- [Healthy, ruins and damaged landmark previews](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/castle_next/landmarks>).

The unapplied asset-stage manifest is retained as a historical handoff. The later
authorized applied operations, exact resource hashes and intended consumers are
recorded in [0.5.0 private bindings](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_050/integration/private-bindings.json>)
and [native source receipt](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_050/native-source/runs/rsrc4/receipt.json>). No Chinese
consumer is redirected to Vietnamese art. Functional markers, footprints,
gameplay and native lifecycle owners are preserved.

## Historical direction

The Citadel is an original fortified royal compound informed by medieval Thăng Long
archaeology: brick/stone foundations, timber halls, tiled roofs and selective
terracotta ornament. Sources: [UNESCO](https://whc.unesco.org/en/list/1328/)
and [Vietnam National Museum architectural materials](https://baotanglichsu.vn/vi/Articles/3101/69653/vat-lieu-kien-truc-bang-djat-nung-tai-di-tich-hoang-thanh-thang-long.html).
The Headquarters is an original timber/bamboo command and supply compound with
[Lam Sơn resistance context](https://baotanglichsuquocgia.vn/vi/Articles/3091/14734/hoi-thao-khoa-hoc-hoi-the-lung-nhai-trong-khoi-nghia-lam-son.html).
Monastery forms draw on northern Đại Việt Buddhist and
[Trúc Lâm context](https://whc.unesco.org/en/list/1732/), distinguishing later
reconstructions from medieval evidence. These are AoE4 interpretations, with
owner colour, restrained dirt and readable game-distance decoration.

## Full-compound triangle limits

All fourteen requested stock Castle choices were inventoried. Unresolved numeric
and randomized scenery predicates leave a stock arithmetic mean interval of
80,519.5–112,464.64 triangles. The user's revised maximum is guaranteed by using
1.5 × the proven lower mean: **120,779.25 triangles**, below the stock maximum cap.
Neither the exact stock mean nor exact native debris visibility is claimed.

| Landmark | Authored healthy | Healthy including all retained debris | Authored ruins | Ruins including all retained debris |
|---|---:|---:|---:|---:|
| Imperial Citadel | 90,894 | 110,488 | 1,968 | 21,562 |
| Resistance Headquarters | 92,234 | 103,505 | 1,452 | 12,723 |

The bounds include 29 Citadel debris instances and 15 Headquarters instances.
Campaign/default branches and mutually exclusive lifecycle states are counted
separately. Both healthy upper bounds satisfy the revised stock-average maximum.
See [dependency-closed debris counts](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/castle_next/landmarks/retained-debris-budget.json>)
and [stock benchmark](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/castle_next/budget/castle-stock-landmark-budget.json>).

## Verification and limits

Native Content Editor compiled and validated **278 instances**.
Six compiled actor comparisons permit only the visual reference changes; nine
private attachment identities are registered and checked. Native art cooks and
reference readback cover ten ordinary base/detail models, two landmark models,
and the separate campaign branch. Source/export contacts, lifecycle selectors,
texture references, owner-mask resources and both UV channels were verified.

Five actors have explicit source XML visual rewires. Current editor list-item
IDs are unavailable for the inherited monastery tier extension, so its XML stays
byte-identical to frozen 0.4.0. A reproducible Garrison integration operation
changes exactly its four default/campaign age-3/age-4 compiled attachment-name
references. The raw native compiled actor is retained; restoring just these
references must reproduce the baseline compiled fields exactly. This operation
is recorded with hashes in the native source receipt and runs in the guarded
release pipeline. The obsolete sparse-override experiments are diagnostic only.

The monastery's separate native outskirts group is intentionally retained:
five Chinese clearable stamps in the default variant and five English stamps
in campaign. It can coexist with the remodeled hall; it is not an age-exclusive
fallback. These clearable surroundings are preserved donor content, and their
visual fit and access still need native inspection. The explicit keep policy and
stock hashes are in the package evidence and
[retained visual recipe](<E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison/art/recipes/release_050/retained-native-visuals.json>).

The landmark Essence cook succeeded, but Garrison's packaging wrapper rejected
duplicate auxiliary texture names in its prototype SGA. That diagnostic archive
is retained. The final pack uses a unique-resource selective composition;
auxiliary atlas encodings come from an independently successful native cook of
the identical PNG inputs. The final archive has no duplicate paths. Provenance
is explicit in the landmark cook/media receipts. Blender background startup
stalled during final re-export; FBX partitioning and UV1 duplication used a
lossless, verified binary-format postprocess. Editable original blends and
original diagnostic exports are preserved.

The regression suite ran 68 tests with the same two inherited
weapon-parity failures as 0.4.0, no new failures/errors/skips. Static tuning source,
preload coverage, strict four-member ZIP, archive integrity, changed-resource
allowlist, exact payload hashes and untouched-resource preservation passed.
No fixes to unrelated gameplay were included. See [release checks](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_050/release-checks.json>)
and [archive verification](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_050/archive-verification.json>).

The historical identity-only migration test now uses the unchanged wood camp;
its previous keep fixture has authorized Castle visual bindings. Both its exact
comparison and deliberate nonidentity-mutation rejection remain unchanged. The
original test is preserved under the 0.5.0 baseline; no normalization allowance
was added to hide art or gameplay differences.

Another task's concurrent normal-edition trap changes were observed and bounded
in the preservation check. This work did not write that edition or include its
changes; [observation](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_050/baseline/normal-concurrent-observation.json>).

Pending native acceptance: import the ZIP, verify lobby selection, inspect all
tiers and distances/LODs in two player colours, adjacency, production and attack
origins, access and construction. For both landmarks: destroy, wait past collapse
cleanup, select persistent ruins, repair, interrupt/resume, destroy again, and
check landmark victory accounting. No in-game or multiplayer success is claimed.

## Rebuild and cleanup

The guarded entrypoint is `tools/build_release_050.ps1`; `-VerifyOnly` checks the
current candidate without recooking. Fresh native runs require a new label and
the shared native lock. Existing registered authoring, source, exports, texture
inputs, recipes, donor manifests, cook archives/readbacks and failure diagnostics
remain available.

After verifying the final ZIP, only reproducible full baseline/final SGA readback
caches were deleted: **273,918,460 bytes reclaimed** in this pass.
Delivery hashes were rechecked afterward. [Cleanup inventory and restoration](<F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_050/cleanup-verification.json>).
