# Community Civilization Pack 0.4.0 — build report

Built on 2026-10-17. Authors: **hosein81 and chilly5**.

## Delivery and hashes

Final ZIP: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_040\community_civilization_pack-0.4.0.zip`

- Size: **49,994,813 bytes**.
- ZIP SHA-256: `23e3f815fcfe47a4c373ab8a4154b84e7adb457492aa7688bf1ab33b58f60f30`.
- Packaged SGA SHA-256: `b33168a31409c57096678bcda7fdd929e08c2ecc8b31de4148bb20f7f44898b6`.
- Strict `garrison.mod/v1`, version `0.4.0`, author metadata `hosein81 and chilly5`.
- Exactly four root members: `garrison.json`, `community_civilization_pack.sga`,
  `START-HERE.txt`, `EVIDENCE.json`; no duplicate manifest. Root independently
  checked ZIP CRCs, manifest identity/author/version, embedded SGA hash and ZIP hash
  after final cleanup.
- Existing package key `community_civilization_pack` and project GUID
  `b7fcea91-257b-408f-b9e8-ae4d8bc402e1` retained. Generated Garrison game mode and
  Live Reload remain disabled.

The accepted030 ZIP/SGA remain under `archives/release_030_user_accepted`.
Earlier unpublished040 candidates remain in `output/release_040/packaging-history`;
only the root versioned ZIP above is the final delivery.

## Implemented changes

Blacksmith, stable, archery range and market each have three private Ages II–IV
models, using the actual active Chinese donor geometry. Remodels change roof/eave
forms; separate private Garrison detail compounds add low clay-tile frontages,
timber structures and family-specific details. Stock texture/owner masks, native
damage/construction fragments, useful surroundings and destruction resources remain.
Qualitative visible-redesign targets are recorded in the plan; moved-vertex counts
are not a numerical measurement of artistic redesign percentages.

Vietnam's market inherits the exact Chinese-HA01 actor through a private child;
only its three visual tiers and four Vietnamese villager build references change.
Blacksmith/stable/range use their existing private Vietnamese actors. Exact source,
compiled gameplay and identity proofs protect donor mechanics and Chinese isolation.

One Pillar's healthy geometry and its eleven retained decorative stamp visuals
scale uniformly 2.5x. Footprint remains8x8, functional stamp objects and native
markers remain unchanged. Its court therefore extends beyond reserved placement;
adjacent-building overlap is an explicit user-accepted tradeoff requiring testing.

The disappearance diagnosis was missing custom ruins geometry: Garrison's previous
house-derived custom models selected no drawable parts for `life_cycle_state=ruins`.
Both landmarks now contain an explicit third ruin mesh selected only in that state;
healthy foundation/superstructure remain selected for healthy and damage1–5 states.
Original landmark RGO collapse/ruins/repair actions and native repair/entity-persistence
flags are retained. Phổ Minh has low broken masonry and cornices; One Pillar retains
a broken column, pond, timbers and roof debris. This implements the native visual
repair path; actual post-collapse clickability and repair have not been tested here.

## Verification evidence

- Storage guard: all seven junctions passed; no E: fallback directories.
- Immutable freeze:291 prior source files,484 normal-edition files and843 prior
  editable-art files protected. All prior editable inputs and rollback hashes pass.
- Exact old-source change allowlist:9 files, plus12 private identity source files.
  Private source IDs/parents, Content Editor compiled identity, final market actor
  gameplay equivalence and all three private market tier PBGIDs are checked.
- Fresh Content Editor build:269 instances validated. Existing actor/squad compiled
  nonvisual fields remain identical. Only visual references, private-market builder
  references and English author-credit text differ as approved.
- Fresh Garrison landmark cook and native reference readback:2 combined models.
  Fresh corrected detail cook/reference readback:12 models. Donor-model native
  topology/UV/index/material/owner bytes are protected separately from remodeled
  position/normal/tangent bytes.
- Final archive:695 members =508 prior +187 new. Exactly9 old members changed;
  all499 other old members are byte-identical, including houses, traps and Ministry.
- Test suite:68 tests, exactly the two inherited bamboo handcannon donor-comparison
  failures; no additional failures, errors or skips. Static tuning validator exit0.
- Contact QA:12 detail compounds pass actual roof-underside ray-fit support checks,
  with0.015m support overlaps. A stock-roof intersection at the stable awning was
  corrected before the final cook. Nearby stock-footing comparisons are proximity
  checks and do not prove terrain contact at every post.
- Visual evidence: paired donor/remodel solids across12 tiers; full-material game/
  facade composite previews for the four AgeII representatives (8 images). Landmark
  healthy/ruin views include six orthographic sides and isometric views. These are
  offline previews, not game captures. Blender MCP structural inspection of enlarged
  One Pillar found3 meshes, one material, finite UVs,0 nonmanifold/degenerate faces,
  0 missing dependencies; no blend was saved during inspection and claim released.
  Worker MCP viewport capture was black, so it is not visual acceptance evidence.
- Repeat package preserves identical member contents and final ZIP hash.

Compact receipts live in `output/release_040`: `archive-verification.json`,
`package-verification.json`, `release-checks.json`, `landmark-lifecycle-contract.json`,
`cleanup-verification.json` and packaged `EVIDENCE.json`. Detail contact/texture
receipts are bound to the current exports/blend hashes in the package evidence.

## Editable inputs and commands

Editable root:
`E:\age of empires 4 mods\01_Custom_Civilizations\Community_Civilization_pack\Community_civilization_pack_garrison`.
Art is under `art/authoring/{landmarks_040,buildings_040}` with corresponding
`art/exports`, recipes under `art/recipes/release_040`, scripts under
`tools/release_040`. Research is in `RELEASE_040_RESEARCH.md`.

From that editable root:

```powershell
.\tools\build_release_040.ps1 -VerifyOnly -Label rverify040
.\tools\build_release_040.ps1 -Label rrebuild040
```

Full builds use retained exports and recipes, pinned tool paths in `workspace.json`,
the guarded F: output and shared exclusive native cook lock. A different candidate
does not silently replace a same-version ZIP: preserve/hash an unpublished candidate
before deliberately repackaging. Existing identical package content is idempotent.

Landmark art generation uses the configured background Blender and
`tools/release_040/landmark_art.py -- pho_minh` or `-- one_pillar`; building generation
and contact/texture QA scripts remain beside it. Serialize all Blender operations.
Do not run Blender generation into an unrelated unsaved scene.

Cleanup removed only hash-verified regenerable readbacks; the final pass records
199,827,520 bytes removed. Earlier passes regenerated some of the same readbacks,
so their numbers are not additive net savings. Required native cook archives,
registered inputs, donor decodes, editable art/recipes, previews, failure evidence,
current delivery and rollback artifacts remain. Final delivery hashes were rechecked.

## Installation and native acceptance

Close AoE4, import the final ZIP through Garrison, and select **Community Civilization
Pack** for both **Game Mode** and **Tuning Pack**. Select China in the lobby, then
Vietnam in the opening choice; isolate the test from other editions.

Destroy each Feudal landmark, wait beyond collapse cleanup, click its remains,
order villagers to repair, interrupt/resume, complete restoration and destroy again.
Check victory counter/ownership and both One Pillar consumers where applicable.
Check AgesII–IV building transitions, construction/repair/cancel/destruction,
blacksmith research, stable/range production exits, market trading, two player
colours, near/far views, Chinese isolation, terrain/slopes and enlarged Pagoda access.

Client import, lobby selection, native ruin persistence/click bounds/repair, terrain
contact, final visual judgement and multiplayer behavior remain unverified until
those user-run tests. No runtime acceptance is inferred from the cook or package.
