# Working with the compact repository

Current release is **0.8.7**. See [the compact update proof](compact/UPDATE_087.md).

## Supported entry points

Use `tools/compact/portable.py` from this checkout. Older `tools/release_*` files and historical guides retain experimental procedures; not every old release script is a supported current command. Frozen receipts keep their original paths and hashes. Source art and required donor/recovery inputs are bundled, not external links.

Existing dialogue is the **exact shipped Ogg bank**. Reproducing the current release never needs omitted WAVs, AI models, cloud credentials or the owner's disks. WAV-dependent historical production validation remains historical evidence, not a prerequisite for the compact build.

## Restore current editable work

Python 3.12+ and Windows are used for native workspace configuration. Put the source on NTFS so it can hold junctions; large external data can be on another drive. Use new empty destinations and short paths. Example paths are yours to choose:

```powershell
python tools/compact/portable.py restore --destination D:/ccp-work --source-parent C:/ccp-work
python tools/compact/portable.py configure --destination D:/ccp-work --source-parent C:/ccp-work --tools .local/tools.json
```

This restores `C:/ccp-work/source` and `D:/ccp-work/external`. Copy `workspace.example.json` to `.local/tools.json` and enter your installed executable paths before configuring. The default profile restores all editable source/art, exports, recovery stores, stock cache and Garrison registrations. `--profile voices` restores compressed clips/manifests; `--profile all` restores every retained input. `--prefix external/staging/release_084/` can restore a narrow additional tree. Existing different files are refused.

Configuration updates **working copies** of recipes and script paths, appends hashes to `source/relocation-proof.json`, writes `workspace.compact.json`, and recovers the verified 1,005-key art-input closure from direct or nested stores. Original packed evidence remains byte-identical. Optional old normal-edition/donor preservation comparisons are not distributed; their configured defaults stay inside the new workspace rather than reading the owner's folders.

Edit restored artwork there; do not edit binary pack files. Change readable gameplay/scripts deliberately in the checkout or transfer reviewed changes back from the working source. Keep one authoritative copy for each change.

## Edit art in Blender/Garrison

Use the installed compatible Blender/Garrison versions. Qualified authoring used Blender 5.2. Preserve the original GUID and the owning resources. Read the bundled workflow guides under `docs/ai/workflows/aoe4-garrison-blender` and `blender-superskill`, and the installed Garrison guide.

Blender files can contain original absolute texture/library paths. Repair a **new copy**, in a separate background process with auto-execution disabled, before opening it for editing:

```powershell
blender --background --disable-autoexec C:/ccp-work/source/art/authoring/PATH/model.blend --python tools/compact/prepare_blend.py -- --workspace C:/ccp-work/source/workspace.compact.json --destination C:/ccp-work/model-portable.blend
```

The helper remaps recorded owner roots to the restored roots, requires every external image/library to exist, leaves packed textures intact, and refuses to overwrite an existing file. Its `.paths.json` receipt lists resolution. All 387 retained Blender files were checked against this restored image closure. To check another milestone, run the background `audit_blends.py` helper; any unresolved references can be restored with `recover_inputs.py --workspace PATH/workspace.compact.json --blend-report REPORT.json --proof PROOF.json`. It does not change a live Blender scene or claim an asset cook. Missing inputs fail visibly; restore their indexed prefix/recovery payload before continuing. Garrison registration recipes receive the same working-path relocation.

Editable masters from historical release directories are retained because current art originated across those releases. Do not delete them based on version numbers. The approved buffalo r4 editable deviation is retained; the shipped archive deliberately keeps its accepted compiled 0.8.3 resources.

## Compile gameplay source

After tuning changes, refresh the full official/private variant inheritance check:

```powershell
python tools/compact/audit_inheritance.py --root C:/ccp-work/source --official-archive "C:/Games/Age of Empires IV/cardinal/archives/ReferenceAttributes.sga" --archive-tool "C:/path/to/sga-archiver.exe" --output .local/inheritance.json
powershell -NoProfile -File C:/ccp-work/source/tools/build.ps1
```

Run the bundled tuning validator as well after attribute edits. Read the actual completed Content Editor burn log; process exit zero alone is insufficient. A broad source cook can omit compiled-only art/voice/lifecycle repairs. Use the resulting changed resources as a selective overlay on the current owning archive, not as an unverified complete replacement. Gameplay values and simulation behavior were not edited for this handoff.

## Reproduce the exact current package

```powershell
python tools/compact/portable.py rebuild-087 --archive-tool "C:/path/to/sga-archiver.exe" --destination C:/ccp-rebuild-087
```

`release` with the same arguments is an alias for current-package reconstruction. The command reuses the retained 0.8.4 ZIP, applies the dispatcher and seven compiled gameplay deltas, preserves the original ZIP entry metadata, then verifies the exact 0.8.7 SGA and ZIP hashes plus every member and mount. No new audio/art payloads or full ZIP are stored. `development.json` selects the 0.8.7 delta index; its baseline index and packs remain immutable.

## Reproduce the historical 0.8.4 package

```powershell
python tools/compact/portable.py rebuild-084 --archive-tool "C:/path/to/sga-archiver.exe" --destination C:/ccp-rebuild-084
```

The immutable 0.8.3 final-v2 baseline is retained because this command needs it. It overlays preserved current payloads, requires the original 0.8.4 SGA hash/namespace, freshly reads back every member and mount, and exports the original matching ZIP. This is actual archive reconstruction from compiled inputs, not a native source/art cook. It requires no original owner folder.

## Integrate a deliberate change

Extract the current owning SGA from the exported delivery ZIP. Create a JSON map of exact archive member names to local replacement files; paths are relative to the map. Example:

```json
{"data/scar/example.scar":"payload/example.scar"}
```

Use real paths from `sga-archiver list`; that example is a placeholder, not a required existing member. Then:

```powershell
python tools/compact/portable.py integrate --base .local/delivery/community_civilization_pack.sga --manifest changes.json --archive-tool "C:/path/to/sga-archiver.exe" --destination .local/change-085
```

The command checks namespace, applies only the map, then freshly verifies every changed and untouched member and mount. It refuses an existing output directory. This produces a verified SGA and change receipt; make a new Garrison package with a new semantic version using the installed supported packaging route. Do not label edited content with the existing 0.8.7 version or overwrite frozen receipts. Native appearance, audible routing, behavior and multiplayer still need acceptance.

## Add new local speech, optionally

Existing compressed sound needs no local AI. For new speech, install the pinned dependencies separately: Python 3.11, VieNeu 3.8.3, Torch/torchaudio 2.8.0+cu128, Transformers 4.57.6, SoundFile, and a compatible ffmpeg with libvorbis. Use the pinned VieNeu/MOSS public model revisions and their publisher/download receipts retained in the store. The source SDK revision is `04044e1b8f822f946bafb2c88b716459f4164152`; the model pins are in `new_voice.py`. Existing installed software/model weights are deliberately not shipped.

Restore the retained local model/SDK lockfiles and publisher receipts with `portable.py restore --prefix external/tool-cache/local-voices-084/ --destination D:/ccp-work --source-parent C:/ccp-work`. This restores recipes/receipts, not weights or an executable environment. Install the SDK at the documented revision and explicitly download the pinned public model payloads into your selected model root before using `--check`. The relocated historical `download_local_models.py --only vieneu` / `--only moss` can perform those two model downloads when you explicitly choose to run them in the configured working source; do not run it without `--only`, which would request optional ASR models as well. No such download is part of normal restoration or package rebuilding.

After explicitly installing local dependencies, use that environment's Python:

```powershell
C:/tts/venv/Scripts/python.exe tools/compact/new_voice.py --models C:/tts/models --ffmpeg C:/tts/ffmpeg.exe --check
C:/tts/venv/Scripts/python.exe tools/compact/new_voice.py --models C:/tts/models --ffmpeg C:/tts/ffmpeg.exe --text "TEXT" --voice "PRESET" --destination .local/new-audition
```

`--check` hashes the pinned local inputs and checks dependencies/CUDA without loading the model or synthesizing. Generation is offline and writes a new audition folder, a temporary WAV and 64 kbps Ogg. No cloud calls or model downloads occur. Listen and qualify pronunciation/acting, then update the voice-bank routing and selective member policy deliberately. New auditions are not automatically accepted or inserted into the delivered bank. Use new job labels; do not resume the historical WAV-dependent finalization workflow.

## Update after a new main-workspace build

The main authoring folder remains authoritative. For a milestone update, export reviewed changed source/art/recipes, the final Ogg bank, current owning resources and required inputs. Apply the compact policy in `compact_export.py`; do not run the old full-history handoff exporter into this repository. Historical 0.8.4 reconstruction is intentionally fixed to its retained evidence; current 0.8.7 uses an additional small index layer. A later milestone gets its own index, package hash, changed-resource policy, dependency closure and reproduction command. Reuse unchanged content-addressed chunks and add only changed payloads.

Before committing: run the compact tests, full store/audio verification, isolated restore, relevant source/art builds, and the new milestone's package reconstruction. Review deletions and contributor edits. Never copy a broad output/cache tree or WAV bank into Git. Future binary revisions increase Git history; the initial approximately 6 GB figure is not a permanent lifetime cap.

Four older Castle-next donor/diagnostic input references in historical construction recipes are superseded by the retained editable scenes and later native resources; those frozen historical recipes are not current rebuild entry points. Preview image output references are not required authoring inputs. See `docs/compact/art-inputs.json` for the explicit historical exceptions.
