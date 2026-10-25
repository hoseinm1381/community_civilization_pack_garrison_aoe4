# Developing from Garrison 0.8.0

0.8.0 is the storage/rebuild consolidation of 0.7.12. Its game archive is exact
0.7.12: `e54fad91112350c70dab1c8cc826da26aa5c6ae9a6754244ed9141fe75d75eb1`.
Version changes are in the Garrison package metadata. All prior gameplay, HUD,
models and native animation resources remain. Credits: hosein81 and chilly5.

Work from the active `Community_civilization_pack_garrison` root. The normal
edition is independent and must stay untouched. Keep the seven configured links
to owned F: storage. Do not recreate a missing link as a normal E: directory.

## What remains editable

- All 339 existing Blender masters and every retained source/export/texture/rig
  stay byte-identical. All 1,009 external image files retain their paths. Unrelated
  open Blender work was not saved or altered.
- `art/authoring`, `art/exports`, `art/recipes`, `assets` and `tools` retain the
  project. Historical alternatives remain; don't overwrite old revisions.
- `consolidation_080/asset-readiness.json.gz` on owned F: maps all 135 packaged
  model resources to editing/donor families, source/export paths and owning native
  payloads. These are family/recipe routes; each family can contain alternative
  revisions. Use the selected revision's export receipt before integration.
- Exact native donors, decoded geometry, earlier source snapshots, diagnostic
  failures, old native member payloads and receipts remain in indexed recovery
  stores. Packed inputs must be restored before a historical consumer reads them.
- An earlier absent v1 recipe path does not identify the current master. The
  readiness index lists retained later revisions. No claim is made that every
  retired historical release command can be rerun unchanged.

The old `0.8.0/` voice research and `tools/release_080` asset preparation are
preserved prior work. This consolidation uses `tools/consolidation_080` and the
entrypoint below. `workspace.json.version` retains its historical value for
frozen release compatibility; `development.json` and the package manifest identify
the current development/release baseline.

## Verify and recover

Run from PowerShell in the Garrison root:

```powershell
.\tools\build_consolidated_080.ps1 -Action Verify
.\tools\build_consolidated_080.ps1 -Action Readiness
.\tools\build_consolidated_080.ps1 -Action Validate -Label checks1
```

Recovery stores are owned F: `resources_071` and `resources_080`. Do not delete
them or `consolidation_071` / `consolidation_080`; they are required inputs and
compact proof. The recovery tool and public index live outside their own ZIP.
Every restored payload is length/SHA-256 checked; edited destinations are refused.
Aliases restore independent files and preserve original predecessor hierarchy.
Validate restores the three exact 0.7.12 comparison fixtures before running the
unchanged historical regressions, plus current tuning/SCAR/inheritance checks.
Its restored-input receipt tracks those temporary fixture copies for later
verified cleanup; the recovery store remains their preserved source.

```powershell
$taskPython = (Get-Content .\workspace.json -Raw | ConvertFrom-Json).python
& $taskPython -B .\tools\consolidation_080\store.py list |
    Select-String 'buffalo|hideout|archer4'
.\tools\build_consolidated_080.ps1 -Action Restore -Key 'F/output/exact/path/from/the/list.json'
```

For older 0.7.1 inputs:

```powershell
& $taskPython -B .\tools\release_071\input_store.py list
& $taskPython -B .\tools\release_071\input_store.py restore 'F/output/exact/old/key.json'
```

`resources_080/native-archives.json` records former archive hashes, namespaces,
member hashes and TOC mounts. Native recovery keys are under
`F/resources_080/recovered_native/<archive-sha>/<member>`. These restore member
payloads, not an identical retired SGA container. Designated rollback ZIPs/SGAs
are preserved independently and exactly. `retired-deliveries.json` accounts for
retired ZIP contents. Compacted audit JSON transparently loads through the new
helpers; standalone inspection can decompress the matching `.gz`.

`resources_080/qualification-evidence-v1.zip` preserves this consolidation's new
staging metadata and native logs before temporary outputs are retired. Its
original-path member hashes are listed in
`consolidation_080/generated-retirement-v1.json`. Inspect that ZIP directly;
it is separate from the original-input recovery index.

## Prove rebuilds after a restore

Use a new alphanumeric/hyphen label, at most eight characters for asset runs:

```powershell
.\tools\build_consolidated_080.ps1 -Action Source -Label check1
.\tools\build_consolidated_080.ps1 -Action Assets -Label check1
.\tools\build_consolidated_080.ps1 -Action Package -Label check1
```

Source qualification runs the real Content Editor in isolated owned staging and
checks source hashes and archive namespace. Asset qualification restores named
donor/receipt/template inputs, exercises the old archer4 packed/predecessor path,
cooks the current furred buffalo and skirmisher with rig checks, and cooks the
stone fortified Hideout. The historical default Hideout cook allocates/writes a
PBG ID; do not use that authoring branch as a read-only qualification command.

Native qualification serializes through `output/release_020/native-build.lock`.
Do not run simultaneous Blender authoring/native cooks or save unrelated scenes.
Temporary builds/restores need additional disk space and can exceed the retained
6 GB budget while work is active. Their receipts name the owner paths. Do not
blanket-clean `output` or `staging`; use a reviewed exact generated-output list.

The Package action is frozen for 0.8.0 preservation: it rejects source drift and
recreates the unchanged game archive with strict 0.8.0 metadata. It cannot package
future gameplay/model changes. It never installs or publishes.

## Modify an existing asset or create a new one

1. Start from the readiness family's current selected master/exports and recipe.
   Copy to a new version-owned authoring/export/recipe directory, for example
   `art/authoring/release_081/<family>`. Preserve original masters and textures.
   Restore exact donor/decoded/template keys when needed; keep native skeleton,
   weights, LODs and functional marker contracts for animated/building assets.
2. Author/export using the installed Garrison guide and the family's qualified
   recipe. For a new asset, create a separate owned Garrison project with its own
   temporary key, Live Reload off and generated game mode disabled. Register the
   asset and cook through the supported Garrison route. Keep editable inputs,
   export receipts, native logs, decoded readback and source hashes.
3. Trace every consuming blueprint/attachment/tier/campaign variant before binding
   the asset. A successful cook alone does not activate a model. Use current
   official donor/schema evidence; resolve full inherited extension chains before
   adding or overriding tuning extensions.
4. Create the next release's explicit changed-member policy, starting from the
   exact 0.8.0/0.7.12 owning archive. Preserve compiled-only selector/lifecycle/
   producer fixes and original member mounts when replacing actors. Never replace
   the whole current pack with a plain source compile or a generated art project.
5. Run current static checks, real native cook/compile, resource readback,
   untouched-member/hash/mount comparisons and the identity checker before and
   after assembly. Package under the next strict semantic version. Retain compact
   rebuild evidence before retiring that release's generated attempts.

For SCAR/tuning/UI edits, modify current editable source under a new release
policy, run the relevant validators and fresh official inheritance check, compile
in isolated staging, and integrate only authorized resources while carrying the
owning overlays. Keep the Garrison GUID/bundle key/archive namespace unchanged.

## Release and rollback locations

- Current: `output/consolidation_080/delivery/final-v1/community_civilization_pack-0.8.0.zip`.
- Exact 0.7.12: `output/release_0712/delivery/final-v1/` (ZIP, SGA and proof).
- Exact 0.7.0: `archives/release_070_rollback/`.
- 0.8.0 receipts, original-path retention maps and operation ledger:
  owned F: `consolidation_080/`, plus the temporary NTFS operation journal under
  the Garrison root's `.consolidation_080`.

Source/static, Content Editor compilation, art cook/readback, package, import,
fresh-match appearance/behavior, save/load and multiplayer are separate gates.
Identical archive bytes and rebuild proof do not establish unobserved game tests.
