# Current editable workspace — 0.7.1

Gameplay/localization: `assets/` and `community_civilization_pack.aoe4mod`.
Art: `art/authoring/`, `art/recipes/`, and retained `art/exports/` inputs.
All 265 original Blender masters, both OBJ sources, FBX exports, and every
external image used by those masters retain their original bytes and paths.
Older numbered art families still provide current buildings/units; they are
required inputs, not obsolete releases. Editable authoring and mesh files retain
independent file identities.

`output/release_071/delivery/` is the current player delivery. The exact original
0.7.0 ZIP and SGA are in `archives/release_070_rollback/`. The normal edition is
preserved separately and is not part of the Garrison storage budget.

Run `tools/build_release_071.ps1` from PowerShell for the verified 0.7.1
preservation rebuild. It compiles the editable project in isolated staging,
checks instance validation and source hashes, then assembles and verifies every
native 0.7.0 resource and TOC mount before packaging strict version 0.7.1.
Compiled selector/lifecycle/producer fixes require this exact native preservation
step. A plain Content Editor source build is not the complete final visual pack.
The current entrypoint rejects source drift against the frozen 0.7.0 input set.
For future gameplay changes, update the release policy and supply an explicit
changed-member/native-overlay allowlist; do not bypass the frozen baseline check.

Large numeric donor/geometry JSON and the future voice preparation JSON are
losslessly gzip-packed in F: `resources_071`. Other native donor inputs and
historical diagnostic records share a lossless ZIP with duplicate payloads stored
once. The index records original paths, byte lengths and SHA-256 hashes. F: is
exFAT, with 256 KB allocation units, so grouped storage avoids tiny-file waste.
Every Blender image and required native unit template remains at its original
plain-file path. To inspect or restore any packed input or diagnostic:

```powershell
& (Get-Content .\workspace.json -Raw | ConvertFrom-Json).python -B .\tools\release_071\input_store.py list
& (Get-Content .\workspace.json -Raw | ConvertFrom-Json).python -B .\tools\release_071\input_store.py restore 'F/output/path/from/the/list.json'
```

Restoration creates the original exact bytes and refuses to overwrite edited
files. Restoring a large snapshot temporarily increases storage. Current unit
qualification automatically materializes its packed inputs into owned staging:

```powershell
& (Get-Content .\workspace.json -Raw | ConvertFrom-Json).python -B .\tools\release_071\qualify_assets.py unit --model archer2 --label next1
& (Get-Content .\workspace.json -Raw | ConvertFrom-Json).python -B .\tools\release_071\qualify_assets.py building --label next1
```

Each attempt uses a new label and preserves failed diagnostics. Old historical
release commands may refer to retired baseline archives/caches; use the current
entrypoints or restore a named packed input. Native reference aliases resolve to
one verified payload in the input ZIP; restoration creates an independent file.
Every E: file, plain authoring image/template, current delivery and rollback has
an independent file identity. No hardlinks or image-path migration are required.

The storage target counts all retained files across both owned volumes. Final
evidence records byte sizes and actual filesystem allocation units separately.
The target is below 3 GB of retained file bytes; the user accepts up to 6 GB
of actual disk allocation because F: is exFAT. Editable sources are not rewritten
or additionally compressed to force filesystem allocation below the earlier cap.
Verified cook/readback/staging payloads are disposable after compact receipts and
delivery hashes are saved; raw sources, recipes, unit rigs, required inputs,
diagnostics, current delivery and rollback remain protected. Do not recursively
clean junctions. Keep all seven configured storage links intact.

Archive equality and fresh source/asset cook proof do not establish client import,
lobby selection or native match behavior; these remain separate user tests.
