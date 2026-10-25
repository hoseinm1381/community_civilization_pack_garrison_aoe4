# Water Buffalo native animation trial — 0.8.2 pilots

The playable buffalo now has authored idle and walking motions encoded into native RHKA. These are isolated test candidates over the preserved 0.8.1 artwork. Installation and publication were not performed.

**Later user acceptance, 2026-10-24:** the user confirmed the new idle worked, then confirmed the walk worked. This establishes user-reported native playback for both pilots. Detailed transition, work/death, LOD/colour, save/load and multiplayer checks were not individually reported. The build-time pending statuses below and immutable JSON receipts predate that feedback; preserve their provenance. Reusable implementation details are now in the installed `aoe4-garrison-blender/references/native-predictive-animation.md` skill reference.

## Test candidates

- `output/release_082_animation/delivery-v1/idle/community_civilization_pack-0.8.2-pilot.1.zip`: idle only. Test first.
- `output/release_082_animation/delivery-v1/idle-walk/community_civilization_pack-0.8.2-pilot.2.zip`: idle and walk. Test after accepting idle.

Import manually into Garrison, enable one version, restart the game between candidates and start a fresh Vietnam match. The bundle and GUID remain the Garrison identities. Roll back by importing the original 0.8.1 ZIP and restarting.

The idle lowers the neck/head and moves the ears and tail. The walk is a new four-beat, planted-foot cycle. Only `navigation\idle_01` and, in pilot.2, `navigation\walk_01` change. Other idle variants, trot/run, work, stopping and death clips remain native. This is not a complete animation replacement set.

Watch idle, move, stop and resume; test a long ordinary walk, turns and start/stop transitions. Check two contrasting player colours, the normal camera, LOD changes, pack stability, Paddy Work/Leave, death and the Ministry herd. Faster locomotion may select the unchanged native clips. Check save/load and multiplayer separately.

## Authoring and verification

- Editable source: `art/authoring/release_082_animation/v2/buffalo-idle-walk.blend`. The original 0.8.1 model masters remain unchanged.
- Native-decoded previews: `output/release_082_animation/preview-v1/idle.mp4` and `walk.mp4`.
- Source samples/proof: `output/release_082_animation/source-v2`.
- Selected encoding: `output/release_082_animation/encoded-v3/receipt.json`.
- Deformation checks: `output/release_082_animation/qa-v2/proof.json`.
- Integration recipe: `output/release_082_animation/integration-v2/recipe.json`.
- Final package receipts: `output/release_082_animation/delivery-v1/receipts.json` and each candidate's `verification.json`.

The encoder preserves the native TYPE metadata verbatim and uses validated predictive packets with the native W-drop quaternion representation. It does not bypass exporter admission or label the cattle skeleton as a supported humanoid. Independent Garrison native decoding and the public animation importer accepted both motions on the unchanged 45-bone skeleton. Every untouched clip, skeleton, annotation and extracted root-motion field compares equal. Native clip durations and frame counts are retained: idle 297 frames / 9.866666794 seconds; walk 129 frames / 4.266666889 seconds with four strides and 7.42006588 units of reference travel.

Both loops close exactly in decoded pose matrices. All three LODs have finite deformed vertices. The offline walking ankle-target drift during stance is at most 0.000453 units under the retained reference travel. Lowest weighted-toe-region vertex height varies by at most 0.000247 units during stance. These are offline pose/reference checks, not engine ground-contact proof. Cloth-border seating drift is zero in these sampled motions.

Each archive has 1,421 members: one existing buffalo attachment edited, four private animator resources added, 1,416 original members byte-identical, none removed. Every original mount is retained. The attachment's default/xp3 parent animator fields alone change. Private RGO and root-motion files are exact native copies; the RGM changes only its animation self-path. No shared stock animator is overridden. Before/after archive namespace checks, full decoded archive readback, ZIP CRC, metadata and embedded SGA hashes passed. Normal edition and protected 0.8.1 inputs compare unchanged. Independent review confirmed the final ZIPs and complete member preservation.

## Rebuild inputs and commands

Use Blender's Python 3.13: `E:\Blender5.2\5.2\python\bin\python.exe`. The general Codex Python has a different ABI and is unsuitable for these wheels.

Project-owned required codec inputs are preserved at `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\resources_082_animation`. Keep both `wheels` and `runtime`, and the generated `manifest.json` and `requirements.lock.txt`. They are rebuild inputs, not disposable caches. Restore the runtime with Python 3.13 pip using `--no-index --find-links <wheels> --target <runtime> -r <requirements.lock.txt>` into a new directory when necessary. This trial has no dependency on another mod's runtime.

The completed rebuild using this owned runtime produced byte-identical RHKA for both candidates and passed the native decoder checks again. See `output/release_082_animation/encoded-rebuild-v1/receipt.json`, `completion.json`, and `art/recipes/release_082_animation/recipe.json`. A final independent ZIP CRC/metadata/embedded-SGA hash check also passed.

From the Garrison root, run the scripts under `tools/release_082_animation` with Blender Python. `author.py` runs inside background Blender and writes the selected v2 source; inspect its output-path constants before rerunning. `encode.py --output-label encoded-REBUILD_NAME` creates a new encoding and native decoder readback. The default selected directory intentionally refuses overwrite. `prepare_integration.py` and `package.py` likewise use versioned, non-overwriting outputs; preserve the pinned selected directories and use new output labels for a subsequent trial. `preview.py` and `qa.py` run inside background Blender against native-decoded samples. Serialize Blender and native operations.

## Acceptance gates

| Gate | Result |
| --- | --- |
| Authored source and decoded deformation | Passed offline |
| Native RHKA encoding and independent native decoder readback | Passed |
| Fresh Content Editor/model cook | Not run; existing 0.8.1 geometry retained, native animation resources written directly |
| Final archive identity, full member readback and ZIP | Passed |
| Garrison client import | Pending user test |
| Native game playback, interruption and transitions | Pending user test |
| Save/load | Pending |
| Multiplayer | Pending |

Expand to other consumed animations only after idle and walk pass native acceptance. Preserve failed probes and earlier trial diagnostics. Credits: hosein81 and chilly5.
