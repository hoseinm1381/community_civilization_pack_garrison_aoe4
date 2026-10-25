# Garrison 0.7.10

Release scope: Garrison Vietnam only, built over the exact user-accepted final 0.7.9. No installation, publication, or cleanup is authorized or performed. Credits: hosein81 and chilly5.

## Changes

- Sparse short coat fur and small tufts on the playable buffalo and three Ministry decorations. Native buffalo skeleton, weights, animation bindings and non-mesh actor chunks are preserved. Ministry architecture and pen clearance are checked separately.
- Fortified Hideout shelter uses heavier timber, denser bamboo defenses and stone footings. Both fortified branches and their campaign variants receive the new private visual attachment. The basic Hideout and native tower/lifecycle resources remain unchanged.
- Active buffalo supervision uses a small steady farm icon. Existing work, owner visibility, replay suppression and removal logic remain intact.
- Vietnam scoreboard rows receive an original gold dragon on deep red. This is an original emblem, not a historical-accuracy claim.
- Vietnam's keyboard/mouse Official HUD position shows living owned buffalo/current native cap. Click cycles by stable squad ID and wraps, issuing selection only. China retains its original widget. The native cap is read through CT_Medic, not duplicated as a UI constant.

## Authorized omission

The requested influence-boundary offsets (-2m generally, +2m Town Centers) are omitted. Current official district-generator data exposes gameplay range; inspected world-display settings are global appearance controls. No supported Vietnam-specific visual offset for both placement and selection was qualified. Actual influence calculations and effects remain unchanged. Evidence: `output/release_0710/influence-audit.json`.

## Evidence and acceptance boundaries

Source checks, completed native cooks, archive readback and package integrity are separate from a running-game test. Fresh-match appearance, buffalo motion, in-game near/far LOD transitions, fortified upgrade transitions, construction/destruction/repair, UI binding and scales, save/load and multiplayer are unverified until observed in game.

The focused HUD tests run Lua 5.1 with mocked official APIs and inspect current official-derived XAML. They cover living ownership counts, cap reads, zero units, death between clicks, stable selection/wrap, China/replay/observer/defeat guards, local-player switch, restore and cleanup. They do not prove native renderer or networking behavior. The Xbox controller HUD layout is not overridden.

The installed UI texture decoder cannot export native internal format 28. Both files parse as Chunky, and their completed native RRTextureBurner outputs and input hashes are preserved; source PNG previews are not presented as decoded native texture previews. See `output/release_0710/hud/native-texture-decoding.json`.

Static tuning validation reports 0 errors, 131 warnings and one unresolved-reference summary. The SCAR checks report 0 errors with one loader-contract warning for presentation, two existing Paddy warnings and six existing mode/helper warnings. These diagnostics remain in `output/release_0710/validation`; they are not silently suppressed. The actual Content Editor validation and compiled-field comparisons provide separate native build evidence.

The fortified actors' native v2 compile proves six intended visual reference changes. Reversing those values restores the complete original ordered typed trees; the editor also reordered the unchanged KEYS table. Final integration copies only the six compiled visual values into baseline actor documents, retaining baseline metadata order and compiled-only content. Original native readbacks remain available as evidence.

## Preserved inputs and rebuild

- `output/release_0710/baseline`: exact accepted ZIP/SGA/manifest, source snapshot and original member hashes/mounts.
- `art/authoring/release_0710`: editable Blender models and HUD SVG masters.
- `art/exports/release_0710`: native art export inputs.
- `art/recipes/release_0710`: rebuild recipes and reviewed integration hash pins.
- `output/release_0710/{buffalo,hideout,hud}`: native cook/readback receipts, proof hashes and previews.
- `tools/release_0710`: version-owned authoring, validation and assembly scripts. Historical scripts/donors used as dependencies remain preserved.

Preview files: `output/release_0710/buffalo/art/buffalo/r1/views/threequarter.png`,
`output/release_0710/buffalo/art/ministry/r1/iso.png`,
`output/release_0710/hideout/compound-default-grounded/iso.png`,
`output/release_0710/hideout/compound-stone-grounded/iso.png`, and
`output/release_0710/hud/flag_preview.png`. The Hideout ground plane is preview-only;
it is not exported. Buried native foundation geometry is preserved.

Run `tools/build_release_0710.ps1 -Label <new-unique-label>` from this root to validate current source and reassemble the reviewed immutable payloads. It verifies storage first, runs HUD/package regressions, refreshes official inheritance, validates tuning and SCAR, checks source/SGA identity, assembles over frozen 0.7.9, compares every member hash and mount, and verifies the strict ZIP's embedded SGA hash. Existing delivery labels are never overwritten.

For recooking, use the exact commands saved in family native logs and recipes with fresh attempt labels. Serialize all Blender and native editor work through `output/release_020/native-build.lock`. `hideout_run.py` provides author/cook/compile/composite operations; buffalo has its version-owned runner and Ministry assembly. Native Garrison modules require the configured Blender Python. HUD PNGs are native RRTextureBurner inputs; the release requires the compiled `.rrtex` outputs. SVG masters are kept outside the native UI wildcard subtree.

After recooking, regenerate family payload receipts, review changed visuals/contracts, run `pin_integration.py`, and build with a new delivery label. Do not reuse a stale review pin after edits. Preserve `workspace.json`'s historical value: strict release version is owned by the final Garrison manifest.

## Native acceptance checklist

Use a fresh mixed China/Vietnam match and multiple Vietnam players. Verify scoreboard rows and original China widget, cap/count across births/deaths/ownership changes, zero-unit clicks, repeated click cycling including working buffalo with unchanged income, and marker start/end/replay behavior. Inspect near/far buffalo and Ministry fur/clearance, fortified branches, upgrade/construction/destruction/repair and unchanged base Hideout. Repeat with HUD scales, local-player changes, save/load and multiplayer. Retain accepted 0.7.9 as rollback.

## Verified delivery

Package: `output/release_0710/delivery/final-v1/community_civilization_pack-0.7.10.zip`.

- ZIP SHA-256: `d9ef1a082a1fc63a50c3ac01810d65c9d63d658ff07a9be282c0c3e2564055db`
- Embedded SGA SHA-256: `2a885792537347f52ea9e971e01c91b80493a59cdc9fa1e354ac330e199d781b`
- 1,415 final members: 14 existing members changed, 23 added; all 1,378 untouched member bytes and all original mounts preserved.
- Source policy: four existing files changed, seven added; nonvisual fortified values, Paddy gameplay and mode gameplay compare exactly after removing approved presentation changes.
- Fresh official inheritance: 198 local and 5,758 official blueprints, zero errors. Six changed XML/XAML files pass .NET XmlReader.
- Twelve HUD tests, seven package-policy regressions and four rig regressions passed. Independent asset and integration reviews found no remaining assembly blockers.
- Native buffalo, Ministry and both Hideout media cooks passed. Final source binding build validated 377 instances. HUD PNGs compiled through native RRTextureBurner. Readbacks and proof hashes passed.
- All 300 frozen normal source hashes and 289 protected 0.7.9 inputs remain unchanged. Exact accepted 0.7.9 ZIP/SGA are preserved.
- Source and final SGA namespace: `b7fcea91257b408fb9e8ae4d8bc402e1`. GUID and bundle key preserved.
- Final ZIP readability, exact three-file strict package layout, version `0.7.10`, and embedded SGA SHA-256 passed.

Assembly commands executed: configured Blender Python ran `tools/release_0710/pin_integration.py` then `tools/release_0710/package_final.py --label final-v1`, after the source policy/current-official validators and focused tests. It pinned 37 payload members and 72 rebuild input files. See `delivery-proof.json`, `verification.json`, `art/recipes/release_0710/integration.json` and the family receipts for complete hashes.

| Gate | Result |
| --- | --- |
| Source/static preservation | Passed, warnings disclosed above |
| Native art cook and source compile | Passed |
| Cooked resource readback/contracts | Passed; UI format-28 preview decoder limitation disclosed |
| Final SGA/ZIP and identity | Passed |
| Client import/installation | Not performed |
| Fresh-match appearance and behavior | Unverified |
| Native save/load | Unverified |
| Multiplayer | Unverified |

Influence display resizing is the only approved feature omission. No installation, publication or cleanup was performed.
