# Garrison 0.8.1 — Vietnamese working buffalo

Delivered artwork: a completely rebuilt natural working buffalo with short warm grey-brown fur, darker lower legs/muzzle, new anatomy, swept horns, a padded farm pack, wooden hoe, woven baskets, and owner-coloured saddlecloth. The Ministry has three distinct unladen poses with the same new anatomy and fur.

Current ZIP: `output/release_081/delivery/final-v1/community_civilization_pack-0.8.1.zip`.

ZIP SHA-256: `75963810d5b241680fad90ff5b4c4f81cb0ba37f550c3b2e65b103f0250fd3e0`.

Embedded SGA SHA-256: `a295752f63ad8bcf62b1ca323d0a60c1084d6f6c3c4f380ab52421324ca17a10`.

## Preserved baseline and integration

- Exact 0.8.0/0.7.12 native baseline: `e54fad91112350c70dab1c8cc826da26aa5c6ae9a6754244ed9141fe75d75eb1`. The original 0.8.0 delivery remains intact.
- Final archive: 1,417 members, 11 changed visual members, zero added/deleted members. All 1,406 other member bytes and every existing mount match the baseline. All actors, gameplay, native animation owners/libraries, `.rgo` resources, namespace/GUID and normal-edition editable inputs are unchanged.
- Only buffalo mesh/texture resources and the Ministry mesh/texture resources changed. Ministry selector bytes, native lifecycle, markers, architecture, production and footprints are preserved. All 750 non-herd source meshes/UVs and architectural atlas-half pixels remain exact.
- The new authoring armature object's label generated a different MRKS name. Final integration restores the original marker chunk verbatim. All buffalo RGM chunks except SKMS are now byte-identical to the baseline, including the exact SKLN skeleton/binds/partitions.

## Editable inputs and rebuild

- Playable master: `art/authoring/release_081/buffalo/r6/model.blend`; exports under the matching `art/exports` family. Earlier 081 checkpoints remain available.
- Ministry master: `art/authoring/release_081/ministry/r2/ministry.blend`; exports under the matching `art/exports` family.
- Animation trial: `art/authoring/release_081/animation/buffalo-trial.blend`; source-only idle and four-beat walking Actions, with MP4 previews and measured diagnostics in `output/release_081/art/animation`.
- `tools/release_081` contains the deterministic anatomy/atlas/gear scripts, texture refinement, solid gear finalization, native material-name repair, source checks, cook/decode adapters, strict integration policy, package/verification and readback recovery tools.
- Source construction sequence is retained as r1–r6 checkpoints. `author.py anatomy r3` then `author.py finish r3` constructs the corrected base in an empty release-owned revision; `refine_textures.py`, `finalize_mesh.py`, and `repair_material_names.py` produce the later selected inputs. Existing masters/exports are immutable: restore/copy into an isolated owned working tree before replaying authoring stages; never delete an accepted checkpoint to make a script rerun.
- The exact selected r6 FBX/rig/five PNGs and r2 building FBX/JSON/four PNGs are the supported native rebuild inputs. `CookBuffalo` and `CookMinistry` use a new immutable label and do not rerun authoring or change the baseline.

```powershell
.\tools\build_release_081.ps1 -Action Verify
.\tools\build_release_081.ps1 -Action CookBuffalo -Label check1
.\tools\build_release_081.ps1 -Action CookMinistry -Label check1
```

The guarded Package action is pinned to qualified buffalo cook v3/r6 and Ministry cook v2/r2. It refuses an existing final delivery. Future edits need a new immutable cook selection/delivery policy. Generated baseline/final readback caches can be recovered with configured Python and `tools/release_081/restore_readback.py baseline` or `final`; preserved SGA files and their SHA-256 inventories are the authority.

## Evidence and limits

| Gate | Result |
| --- | --- |
| Source | 18,308 / 9,800 / 4,798 triangles; one 2K atlas/material; 45 exact native rest matrices; normalized maximum-four weights; cloth-only owner mask |
| Native buffalo cook/readback | Completed archive build; exact LOD counts, official bone hierarchy and partitions; maximum bind-component delta 0.000003458; no blockers, missing textures, unweighted or non-normalized vertices |
| Native Ministry cook/assembly | Completed native archive build; three distinct posed animals; exact original selectors, functional markers and nongeometry metadata |
| Source animation trial | Idle and four-beat walk authored on a copy; zero loop-endpoint mismatch, stationary root, unit scale, finite/nonzero deformation; cloth-border distance drift 0 / 0.000543 model units |
| Package | Namespace checked before/after assembly; fresh cooked archive extraction matched payload readback; all final member hashes/mounts, strict 0.8.1 metadata, ZIP CRC and embedded SGA hash passed |
| Preservation policy | Nine regression tests pass, including stale cook/texture, LOD drift and unauthorized gameplay/animation changes; previous masters, normal editable inputs and 0.8.0 archive preserved |
| Import/native appearance and behaviour | Unverified |
| Save/load, multiplayer, runtime performance | Unverified |

The actual active animation owner is official `base_cattle`; Worker Elephant is gameplay ancestry. Eleven native cattle clips were inventoried, but the full inherited state graph remains unresolved. Installed Garrison 0.1.4 has no animal Action replacement contract or validated cattle RHKA encoder roundtrip. Consequently **the delivered mod retains native animations**. The authored Actions and MP4s demonstrate Blender source motion only; no unsupported diagnostic animation package was fabricated.

Source previews cover six directions, equipment contacts and simulated red/blue cloth masks. The material-name repair from r5 to r6 proves the same geometry/UV/weight fingerprints, so r5 presentation renders remain representative of the final geometry. These are not in-game screenshots or native player-colour proof. Photographic-reference links and direct-download limitations are recorded beside the editable reference notes.

Two failed buffalo cooks and the accepted-art control are retained. The failure was narrowed to a real FBX material identity mismatch (`lod2.001`/`lod3.001` versus `lod2`/`lod3`); an actual saved-source regression fails before repair and passes afterward. Completed burn evidence is captured in stdout, with editor logs retained separately.

Cleanup: the two hash-verified full extraction caches contain 593,106,554 logical bytes. Automatic approval review rejected their recursive removal with "blocked by policy" before execution. Both caches remain; zero files were removed and no reclaimed space is claimed. The preserved SGA files, inventories and recovery helper provide a restoration route, but no empty-target restoration trial was performed after that rejection.

## Focused native acceptance

Import the ZIP manually, enable/select the correct tuning pack and Vietnam game mode, and start a fresh match. Check two contrasting player colours, near/far LODs, idle/move/turn/stop, construction, Paddy Work/Leave and income, death, and all Ministry construction/healthy/ruin consumers. Inspect harness/cloth contact during native movement. Treat save/load and multiplayer as additional gates. No installation or publication was performed.
