# Community Civilization Pack 0.1.0 test release

Built Garrison edition with four remodeled Vietnamese house ages and two distinct
scratch stake trap visuals. Final GUID: `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`. Current Vietnam
gameplay, names/icons, lobby options and China/Vietnam choice are preserved.

## Deliverables and editable roots

- ZIP: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_010\community_civilization_pack-0.1.0.zip`
- ZIP SHA-256: `bd37ac9b79a9f07c127abd1c32abcb4f4f8cb450f0bda22ab10988c9ef0e2f93`
- Combined tuning/game-mode SGA: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_010\package\community_civilization_pack.sga`
- SGA SHA-256: `c04280a8b2293e7e9c92832b3608d7033cba0a8ed1c807b8e37a457180482546`
- Editable source root: `E:\age of empires 4 mods\01_Custom_Civilizations\Community_Civilization_pack\Community_civilization_pack_garrison`
- House blends/textures: `art/authoring/houses_010`; retained inputs: `art/exports/houses_010`.
- Trap blends/textures: `art/authoring/traps_010`; retained inputs: `art/exports/traps_010`.
- Recipes/frozen baseline: `art/recipes/release_010`.
- House comparisons: `output/release_010/houses/houses-before-after.png`.
- Trap previews: `output/release_010/traps/stake_thicket` and `stake_fan`.
- Garrison family project map: `art/GARRISON_PROJECTS.json`.
- Storage links/retention/recovery: `STORAGE.md`; current tools: `workspace.json`.

## Evidence

- Normal edition: all 484 original files unchanged.
- Source preservation: only 4 existing actor XMLs
  rebound to private visual lists; all other original asset bytes unchanged.
  7 generator-owned private identity source files added.
- Native baseline compile, Garrison art cooks and isolated native reference validation:
  exact commands, fresh logs, source/config hashes and results under
  `output/release_010/integration`; final candidate receipt `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_010\integration\runs\r010proof\candidate.json`.
- Archive: 269 baseline members, 355 final;
  265 baseline members byte-identical, exactly four
  actor RGDs changed, 86 approved private visual members added.
  No baseline member removed. Both archives passed CRC/SHA1-block verification;
  every decoded member was compared by SHA-256.
- Compiled closure: four actor RGDs, seven private lists and six private stamps
  resolved through model/material/texture resources. The independent archive
  checker reran the typed reader on its own final readback and covered every new
  archive member. Official unchanged dependencies terminate at inventoried native
  resources, with extracted hashes and archive fingerprints.
- Static tuning validation: 244 instances,
  0 errors, 7
  warnings (new private version2 identity stubs absent from validator corpus),
  1 informational native-reference summary;
  exit 0. Native compile validates the actual stubs.
  Raw suite
  68 tests, exit 1, exactly the
  two inherited weapon donor-comparison failing subcases and no additional failures,
  errors or skips. Raw log: `output/release_010/release-tests.log`.
- ZIP readable, exactly one strict `garrison.mod/v1` manifest, measured archive hash.
  Receipt: `output/release_010/package-verification.json`.

The retained donor failures are `vn_weapon_outpost_handcannon_bambo_alarm_chi` and
`vn_weapon_outpost_handcannon_bambo_chi` in the original native-tuning parity test.
Gameplay was not changed to silence those findings. Preparation-only receipts and
checks remain historical and are not rewritten as release/runtime evidence.

## Build and verification commands

From the editable root:

```powershell
& .\tools\build_release.ps1 -VerifyOnly
& .\tools\build_release.ps1
```

The full command uses a new unique cook label, the installed Garrison core/prepared
art editor, isolated Content Editor reference validation and selective archive
integration. Generated Garrison mode ownership and Live Reload remain off. Native
cooks are serialized. No normal-edition build or client installation is performed.

Independent script entry points: `tools/release_010/release_checks.py`,
`verify_archive.py`, `package_release.py`, `cleanup_release.py --apply`.
Run them using the Python paths in `workspace.json` (integration uses Blender's
Python for the installed Garrison compiled helpers). Reports pin the candidate and
source hashes; changing either requires verification again.

## Historical interpretation and limitations

House progression draws on northern Vietnamese/Kinh village forms, with later
traditional examples as analogues and medieval timber/brick/tile archaeology as
material context. It is an artistic progression, not four dated reconstructions.
The requested 10–70% redesign range is qualitative; no measured mesh percentage is
claimed. Actual Chinese A age01–04 donors, before/after previews and hashes remain.

References: [North Delta houses](https://journal.vnuf.edu.vn/vi/article/view/1397),
[Thang Long archaeology](https://hoangthanhthanglong.vn/en/initial-findings-of-the-kinh-thien-area/),
[Bach Dang stake evidence](https://whc.unesco.org/document/211490).
The trap timber motif uses medieval river-stake evidence. The portable infantry
arrangements are artistic interpretations, not documented historical mechanisms.

## User installation and native test gates

Close AoE4 completely, import the ZIP into Garrison, enable it and select both
**Tuning Pack: Community Civilization Pack** and **Game Mode: Community Civilization
Pack**. Choose China, then Vietnam in the existing opening choice. Keep other
civilization pack editions disabled for the first isolated test. The ZIP's
`START-HERE.txt` includes the same instructions. Disable/remove this client copy
to roll back; retained source and frozen baseline are separate from client state.

Native import, lobby selection, appearance, culling/LOD, lifecycle and multiplayer
are **not tested** by this build. In a fresh match check:

- Existing and new houses through all four age-ups, both normal/faster commands.
- Construction, repair, cancel/delete, damage and destruction, near/far views.
- Both traps before/after upgrades, attacks/effects and preserved four-second expiry.
- Two player colours; China and Vietnam selection; stock Chinese isolation.

No new trigger animation, terrain-hole mechanic or trap age progression was added.
Private native resources retain the existing lifecycle owners, markers and flags.

Material limits: the traps use one freshly cooked geometry LOD; lower-LOD activation
is not claimed. House bounds/culling must be checked in game. The larger trap keeps
the original tent door/roof skeleton and cloth-owner bytes while explicit selectors
select only scratch parts; default native cloth drawing/physics remain unmeasured.
Final private stamps reuse native binary structures with typed reference/identity
edits and decoded graph checks; the seven final model resources were native-reference
compiled, while a full source round-trip of those final stamp binaries was not run.
Owner masks/markers are retained, but two-colour appearance still requires the match.

## Cleanup

Initial cleanup removed 121135565 bytes of explicitly regenerable intermediates/readbacks. Repeated verification may regenerate readbacks which are cleaned again; aggregate pass totals are not a cumulative net-space claim. Delivery hashes were unchanged afterward. Required sources, recipes, inputs, native cook archives, rollback artifacts, comparisons and diagnostic evidence were retained. See `output/release_010/cleanup-verification.json` for the exact inventory/restoration commands.
