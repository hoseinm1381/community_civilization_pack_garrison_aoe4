# Community Civilization Pack agent instructions

## IMPORTANT: normal-to-Garrison archive identity regression (0.7.3, 2026-10-23)

Normal and Garrison are independent mods. When porting normal source, translate
ALL identity-bearing build inputs, including `assets/_default.burnproj`.
Its ArchiveParameters `NiceName` becomes the SGA header's runtime namespace.
It MUST equal the destination `.aoe4mod` ID normalized without hyphens.
Do not assume that updating `.aoe4mod`, the attrib manifest, RDO/locstrings and
SCAR prefixes also updates this burn-project setting. Include `.burnproj` in
identity translation; the historical 0.7.2 translator omitted that extension.

0.7.2 compiled successfully but kept normal archive NiceName
`a743d7d1d7534cf78817e29d8ded7366` while SCAR requested Garrison blueprints under
`b7fcea91257b408fb9e8ae4d8bc402e1`. Vietnam selection then fatally failed at
`initialization.scar:50` looking up `vn_building_town_center_capital_chi`.
The Garrison 0.7.3 fix changes only that burn-project NiceName and release metadata;
all 1,267 packaged member bytes and mounts must remain identical to 0.7.2.

Before and AFTER compilation/assembly, run Garrison
`tools/release_073/check_identity.py --archive <final.sga>` with configured Python.
The source and the FINAL SGA `list --verify` archive `name` must agree with the
destination GUID. Member existence, matching basenames, internal `$PBGNAME`
references, validator success and a completed burn are insufficient namespace proof.
Preserve the destination GUID, stable bundle key, custom art and compiled-only
owning-resource overlays. Never "fix" this by changing Garrison SCAR back to the
normal GUID or by making the two editions share an ID.

Current focused release entrypoint: Garrison `tools/build_release_073.ps1`.
Evidence/recovery: `output/release_073`, including original source, screenshot,
warnings log, native burn logs and exact member comparison. See
`docs/RELEASE_073_IDENTITY_FIX.md`. Normal source stays untouched. Native import
and fresh-match Vietnam selection must be reported separately from package proof.

## Mandatory inherited-extension check (2026-10-22 build regression)

The normal-edition runtime repairs are explicitly authorized by later user
requests. Preserve the Garrison edition while repairing normal source.

Content Editor twice rejected duplicate singleton extensions after agents appended
an extension already supplied by a parent. The second incident affected
`district_generator_ext` on fortified Hideouts, Dock and Monastery/Pagoda children.
Checking only the XML file's direct children did NOT catch the inherited copies.

- Before adding any EBPS/SBPS extension, resolve the full private AND current
  official parent chain for default and every affected variant. Absence from the
  child XML is not evidence that the extension is absent from the effective unit.
- When the extension is inherited, override its exact variant-specific native
  `List.ItemID` with matching `List.ParentItemID`; do not use `Append` or allocate
  a fresh identity. Default and campaign IDs often differ. Append only after
  proving the extension absent throughout that variant's parent chain.
- After normal-edition tuning edits, run `tools/check_extension_inheritance.py
  --refresh` from the normal root with the verified Python runtime, as well as
  the installed tuning validator. Resolve inheritance errors before handoff.
  `tools/build.ps1` also runs this preflight. Its current official archive evidence
  must be refreshed after a game update; a frozen test fixture alone is not enough.
- Keep a failing regression using the actual pre-repair source and a preservation
  check showing that identity-only fixes do not alter gameplay values. Never
  declare duplicate extensions absent based only on direct XML uniqueness or the
  generic tuning validator's zero-error result.
- Content Editor burn success remains a separate gate: report it as unverified
  unless a real completed burn log confirms it. Do not equate process exit0,
  successful project loading, mocked tests or static validation with a build.

Evidence and regression: normal `work/vietnam_redesign/district_build_repair_20261022/`
and `tests/test_extension_inheritance.py`.

## Current authorized milestone: 0.7.1 consolidation (2026-10-19)

The user explicitly approved a verified 0.7.1 preservation rebuild, retirement of
obsolete versions/duplicates afterward, exact independent 0.7.0 rollback, and a
combined development storage target below 3,000,000,000 bytes. This supersedes
historical requirements below to retain every prior delivery/cache. Preserve all
0.7.0 native members/mounts and current editable assets/rebuild inputs; keep the
normal edition untouched. See the Garrison root's `docs/DEVELOPMENT_071.md`,
`docs/RELEASE_071_CONSOLIDATION_PLAN.md` and `docs/RELEASE_071_LEDGER.md`.
`resources_071` and `consolidation_071` on owned F: are protected inputs/evidence.
Current build entrypoint is `tools/build_release_071.ps1`; native source compile
alone does not preserve compiled-only owning-resource fixes. Historical milestone
sections below are provenance. Do not rerun retired historical cleanup/build
commands or delete packed inputs, editable masters, unit rigs, or rollback.

## Working roots and scope

- Active Garrison source root: `Community_civilization_pack_garrison`.
- `Community_civilization_pack_normal` is the preserved source baseline. Do not edit,
  build, clean, or regenerate anything there for this migration. A later explicit
  user request may change that boundary.
- Berber reference only: `E:\age of empires 4 mods\AI_Assisted_modding\Berber_future_kingdom_ai`.
  Inspect its workflow; never change or borrow its GUID, caches, bindings, or assets.
- External storage owned by this project:
  `F:\aoe_4_temp\Community_civilization_pack_garrison_temp`.
  Read the Garrison root's `STORAGE.md` and `workspace.json` before file operations.
  Some external directories contain required authoring inputs, not disposable temp.

## Current milestone and preservation

Current authorized milestone: **0.4.0 Vietnamese workshops and landmark repair**.
The approved plan supersedes the historical milestone descriptions below. Freeze
0.3.0 delivery/source/art before edits. Add exact credits `hosein81 and chilly5`;
scale One Pillar's entire visual compound 2.5x while retaining its footprint and
functional markers; remodel all existing active blacksmith/stable/range/market
tiers using actual stock donors and Northern Dai Viet architecture. Preserve
unrelated gameplay/art. Repair both Feudal landmarks through native persistent,
selectable ruins and repair/rebuild selectors, not scripted replacement entities.
Use new `release_040` scripts/evidence and `*_040` art; preserve earlier inputs.
Isolate the market with a mechanically equivalent private native actor and only
Vietnamese builder references. Use Luna inventory/check workers and Sol modeling/
integration workers. Serialize Blender and native cooks, qualify landmark ruins
first, and deliver strict version 0.4.0 ZIP. Native repair/selection, appearance,
and import remain separate acceptance gates. See `docs/RELEASE_040_PLAN.md`.

Current authorized milestone: **0.3.0 Feudal landmarks and camouflage**. Freeze
0.2.1 ZIP/SGA, source and all prior editable art before changes. Restore the
Ministry's four normal/campaign footprint floats from 16 to 8; its model, yard,
three elephants, materials and transforms remain byte-identical. Build new private
Phổ Minh Tower and One Pillar Pagoda visual compounds, including alternate and
campaign consumers. Camouflage both traps with shallow irregular earth/leaf/bamboo
cover, small exposed stake openings, and NO black surrounding rim or broad black
cavity. No stealth mechanic or terrain excavation. Preserve all other gameplay.
Use separate `release_030` / `*_030` authoring, exports, recipes and build evidence;
never overwrite earlier inputs or weaken historical release verification.
Measure complete simultaneously visible highest-detail stock Feudal landmarks
before detailing: target their median triangle count, cap at their maximum.
Use Luna inventory/check workers and Sol art/integration workers; serialize live
and background Blender operations and native cooks. Deliver strict version 0.3.0
ZIP through the supported Garrison route. Client import/native tests are separate.

The following 0.2.1 milestone description is historical context:

Current milestone (2026-10-17): **0.2.1 pit traps and Ministry refinement**.
The user confirms 0.2.0 is good; the reported missing-blueprints issue was a lobby
selection mistake, so no gameplay repair or diagnostic bypass is authorized.
Freeze accepted 0.2.0 under `archives/release_020_user_accepted`. Preserve all prior
art and active gameplay source. Build two scratch pit-trap visuals and weather the
Ministry, adding three large static stock worker elephants in an outside yard.
Keep the existing private model keys, bindings and native lifecycle owners;
enlarge only its placement footprint as authorized below. Preserve production
access and all other mechanics. New authoring/exports/recipes use `*_021` or
`release_021`; scripts and receipts use `tools/release_021` and `output/release_021`.
`tools/build_release_021.ps1` is the separate guarded release entrypoint. Its
verification compares against frozen 0.2.0; historical 0.1.0/0.2.0 tests and
receipts remain unchanged. No terrain excavation, trap animation or gameplay
elephant is added. Client import and native tests remain separate user gates.

0.2.1 user steering: replace the miniature pen with an outside yard containing
**three large static stock elephants**. The user explicitly approved enlarging
the Ministry placement area to fit the compound while preserving costs and
production. Only its normal/campaign `site_ext/footprint_scale` x/y values may
change in gameplay source/compiled actor. The 0.2.1 policy must compare that
explicit exception against the immutable 0.2.0 baseline; historical preparation
and 0.2.0 preservation checks remain intact and will reject this intended edit.

The following 0.2.0 milestone description is historical context:

The user reports the 0.1.0 houses/traps release tested and good, without specifying
individual test coverage. Preserve its ZIP, archive, editable sources and receipts.
The current authorized milestone is Vietnamese buildings 0.2.0: four barracks ages
(10–35% visible stock redesign), four town-center ages (10–30%), one shared rice
paddy farm (20–40%), one shared low-lookout Hideout (30–50%), and a scratch-built
Economy Ministry administrative hall, storage wing and elephant-handling yard.
No lumber/mining camps. Existing age-selection rules and all gameplay stay unchanged.
Percentages are qualitative art targets, not claimed measured mesh percentages.
Native Content Editor builds, Garrison art cooks, private selective integration and
the strict 0.2.0 ZIP are authorized. Client import/installation, publication and
native match testing remain outside this milestone. Preparation receipts are historical.
Use Luna agents for research/inventories/routine checks and Sol agents for modeling
and integration. Serialize shared Blender access and native cooks; each worker owns
separate source/recipe/output paths. Read docs/RELEASE_020_PLAN.md and its release ledger.

The copied Content Editor source owns gameplay, localization, and the Vietnam mode.
Garrison owns future art authoring/export/cook. Its generated game mode and Live Reload
remain off. Never overwrite the Vietnam SCAR entry with a Garrison template.

Identity changes must cover project/attribute/locdb filenames, custom references,
RDO localization GUID parts, tuning linkage, SCAR prefixes, and archive identity.
Preserve PBG IDs, RDO object IDs, locale IDs, blueprint names, Vietnam module names,
options/defaults, native gameplay, icons, foreign references, and historical evidence.
Use `docs/migration-provenance.json` for the exact old/new identity and hash records.
Existing donor-comparison failures are evidence; do not change gameplay to silence them.

## Skills and tools

Use the installed `aoe4-game-mode-skill`, `modify-aoe4-tuning-packs`,
`aoe4-garrison-blender`, and `blender-superskill` for their respective surfaces.
Read their current SKILL.md and applicable references before changes. Prefer the
installed Garrison guide and supported CLI to remembered operator names.

Verified on 2026-10-16 (recheck on another machine or after updates):

- Garrison extension 0.1.4:
  `%APPDATA%\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com\garrison`.
- Core: that directory's `bin\core\garrison-core.exe`.
- Archive tool: that directory's `bin\sga-archiver.exe`.
- Content Editor: `E:\Games\steamapps\common\Age of Empires IV\EssenceEditor.exe`.
- Garrison art editor: `%LOCALAPPDATA%\Garrison\Kit\tools\essence-object-editor\EssenceEditor.exe`.
- Resolve bundled Python with `load_workspace_dependencies`; current absolute paths
  are recorded in `workspace.json`. Never expose credentials or install dependencies
  into the normal edition. Never save an unrelated live Blender scene.

## Future asset integration

Read `docs/GARRISON_WORKFLOW.md`. Follow editable source -> Garrison export/cook ->
approved private resource/binding changes -> final owning archive. A model cook does
not activate a model. Trace each consuming blueprint, attachment, tier, and stamp.
Before integration, freeze dependencies and hashes, inventory both archives, state
an explicit changed-resource allowlist, and compare all untouched members afterward.
Keep the final pack GUID; never treat a generated prototype actor as an approved
replacement for the existing civilization actor. Add no implicit Berber dependency.

## Storage and cleanup

Run workspace storage verification before preparation/build/generation commands.
Fail if F: or any expected junction/target is unavailable or changed. Never create
an ordinary E: directory in place of a missing link, and never recurse blindly
through junctions. Validate resolved absolute targets stay inside owned roots.

After a future verified release ZIP, cleanup is part of release completion. First
verify ZIP readability, expected members, packaged SGA SHA-256, and save compact
results. Inventory rebuild dependencies before removing only release-owned,
regenerable cook/readback/staging/preview/donor caches. Preserve editable blends,
textures/audio/source media, Garrison recipes, required inputs, scripts/config,
deliverables, current release, designated rollback files, reports, and hashes.
Do not delete decoded manifests unless regeneration works; otherwise preserve a
lossless compressed rebuild bundle and restore instructions. Share donor caches by
identity/hash, avoid redundant copies, and recheck delivery hashes after cleanup.
Report reclaimed bytes and anything retained. A failed build's diagnostic evidence
must remain available. Moving a cache to F: is not a reduction in total storage.

## Evidence and completion

Keep static/offline checks, Content Editor build, Garrison export/cook/readback,
package/import, lobby selection, and native match behavior as separate gates.
Do not promote preparation checks to runtime or multiplayer proof. Report exact
commands/results, preserved-baseline checks, remaining gates, and material limits.
