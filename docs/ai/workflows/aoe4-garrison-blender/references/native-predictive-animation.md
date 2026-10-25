# Native predictive animation: qualified cattle idle and full walk

Read for custom RHKA encoding, unsupported panel skeletons, full quadruped gait, or the claim that only English prototype clips can be replaced. This route is separate from the public Build Unit exporter. It preserves an existing native skeleton and animation graph, writes valid private native resources, and replaces already-consumed slots. It requires no new SCAR pose writer or ability for ordinary navigation.

## Evidence status — 2026-10-24

Community Civilization Pack Garrison Water Buffalo, unchanged native **45-bone cattle skeleton**:

| Stage | Evidence |
|---|---|
| Authoring | Editable Blender Actions; native rest binds preserved; baked four-leg IK |
| Encoding | Metadata-preserving Havok tagfile writer and independently developed predictive encoder |
| Decode | Installed Garrison native sampler accepted both replacements; public animation importer re-imported them on the buffalo rig |
| Rebuild | Independently installed project-owned Python dependencies reproduced both RHKA files byte-for-byte |
| Integration/package | Two strict pilot ZIPs; full archive member/mount/identity/embedded-SGA checks and independent review passed |
| Native idle | User explicitly confirmed the new idle worked, after being told to identify head lowering, ears and tail rather than merely absence of T-pose |
| Native walk | User subsequently reported “it works” for the walking candidate |
| Detailed transitions, every work/death state, LODs/colours, save/load, multiplayer | Not individually confirmed by that brief feedback; remain separate gates |

These reports qualify **custom cattle idle and full four-leg walking playback** for these packages. They do not prove all animal families, arbitrary animation names, new skeletons/bones, attack/death replacements, ability interruption semantics or a complete replacement set. Historical JSON receipts retain `gameplay_tested:false` because generated before the user test; the dated user report is later evidence, not a reason to silently rewrite immutable build receipts.

The earlier general writer's `hkFlags[hkUint32]`/`tag_format_flags=None` failure is historical, not a current blanket blocker. Copying the actual native TYPE section and retaining native indices resolved the cattle adapter's metadata gate. Public panel admission restrictions still apply to that panel; do not alter its flags or impersonate an English prototype.

## Locate the real animation owner

Trace the consumed EBPS/SBPS, visual attachment, `parent_animator`, RGM animation library path, RGO/native routing, RHKA bindings and root-motion resource. Skin compatibility does not identify the animation owner. Inventory actual packaged clips before editing; clip indices below belong to this fingerprint only.

Native stem: `art/civilizations/common/animals/archetypes/base_cattle/base_cattle`.

| Index | Clip | Pilot treatment |
|---|---|---|
| 0 | `death_pose_01` | Native |
| 1 | `death_01` | Native |
| 2 | `walk_to_stop_01` | Native |
| 3 | `navigation\walk_01` | New full four-leg cycle in pilot.2 |
| 4 | `trot_to_stop_01` | Native |
| 5 | `trot_01` | Native |
| 6 | `sprint_01` | Native |
| 7 | `run_01` | Native |
| 8 | `idle_grazing_01` | Native |
| 9 | `idle_02` | Native |
| 10 | `navigation\idle_01` | New idle in both pilots |

Idle: 297 samples, 9.866666793823242 seconds, two authored cycles, no horizontal reference travel. Walk: 129 samples, 4.266666889190674 seconds, four strides, reference travel 7.420065879821777 units. Other idle variants and faster movement can still look native by design. Inventory graph conditions and constituents before claiming full motion coverage.

## Author and sample without changing the skeleton

Preserve bone names, parents, rest/bind matrices, partitions and track bindings. Bake constraints to ordinary bone transforms; do not export IK targets or animated armature-object travel. Resolve names against **each clip's embedded skeleton and transformTrackToBoneIndices**; embedded ordering can differ between clips. The tested bindings were identity mappings for all 45 tracks, verified rather than assumed.

The source rig's stored `garrison_skeleton_records` contains native order/parents. Evaluated Blender pose matrices were converted to native space using the existing imported rig's convention:

```python
projection = Matrix(((-1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
axes = Matrix(((0,1,0,0),(1,0,0,0),(0,0,1,0),(0,0,0,1)))
native_global[name] = projection.inverted() @ evaluated_bone.matrix @ axes.inverted()
local = native_global[parent].inverted() @ native_global[name]  # root: native_global[name]
t, q, scale = local.decompose()
q.normalize()
row = [*t, 0, q.x, q.y, q.z, q.w, 1, 1, 1, 0]
```

This is the tested rig's axis convention, not a universal transformation for arbitrary Blender imports. Check imported bind records and re-import agreement before reuse. Reject shear/non-unit scale and non-finite samples. One sample contains 12 floats per bone: translation xyz + padding, quaternion xyzw, scale xyz + padding. Match quaternion hemisphere before interpolation; normalize interpolated quaternions.

The new walk used a 32-frame period at 30 FPS (33 samples including duplicated endpoint), four-beat phase offsets hind-left 0, fore-left .25, hind-right .5, fore-right .75. Per-stride distance is native travel / 4 = 1.85501647. Stance duty .55, swing lift .16 units, body settling -.18 units plus .01 vertical bounce, no horizontal root-bone/object travel. These are accepted buffalo fixture choices, not mandatory values for another animal. Forelegs used four-bone IK chains and hindlegs three, orientation enabled, stretch off; poses were baked and constraints/targets removed. The earlier .60 stance/-.12 settling candidate missed IK targets by .065 units and was rejected. Selected source maximum IK error: .000131607 units.

Idle source has 121 samples at 30 FPS, with neck/head lowering, ears and tail; it is repeated twice to the original native duration. The walk repeats four times to its original duration. The native clip's frame count, duration, extracted motion and annotation/event data remain exact. Native travel supplies displacement: do not add the same horizontal movement to the authored root and double it.

## Native tagfile adapter

Tested format: Havok SDK `20180200`, custom `_HavokAnimSet` root, custom binding/skeleton wrapper, `hkaPredictiveCompressedAnimation`. Use the source-declared type definitions and actual native TYPE bytes. The proven adapter is `tools/release_082_animation/native_codec.py` in the evidence project (absolute root below).

Important adapter mechanics:

1. Read type metadata with `TagFileUnpacker.unpack(..., types_only=True)`. Parse existing section lengths as big-endian uint32 masked with `0x3fffffff`; retain the entire original TYPE section verbatim.
2. For missing/mismatched hk2018 classes, generate declarations from the source type info (`get_new_type_module_and_import`), resolve dependencies, and run `check_py_class_match`. This is source-derived reflection, not invented ABI metadata.
3. Treat the custom `_HavokAnimSet` pointer root as its own class, not an assumed `hkRootLevelContainer`. Resolve ConstCharArray items using the native data type.
4. Preserve allocated empty strings: the library's falsey empty-string shortcut needed an adapter whose `NativeString.__bool__` returns true. Dropping empty strings changes native structure.
5. Build the packer's type dictionary in **original type index order**. Duplicate generic type names must retain separate native indices; use unique dictionary keys without changing serialized type definitions.
6. Override only this adapter process's TYPE packing to append the exact original section. Refuse any output item type absent from the source metadata. Do not manufacture type flags, hashes, sizes or checksums.
7. Write the modified data with its real binding/root structures. Reparse it, compare every untouched clip field recursively, and independently decode with Garrison. Python parsing alone is insufficient.

Soulstruct's warning that the root is `_HavokAnimSet` rather than `hkRootLevelContainer` is expected for this file family after the adapter is applied; it is not proof of failure or success. Shift-JIS decoding may display ASCII backslash as U+00A5: normalize lookup where needed while preserving serialized names.

## Predictive packet encoder

The reusable standard-library-only implementation is [scripts/native_predictive.py](../scripts/native_predictive.py), copied from the native-tested encoder. Import it with Python; `replace(animation, rows)` mutates a compatible native animation object and returns encoding metrics. It does not itself read/write tagfiles, retarget a skeleton, or validate another format. Keep the wrapper and independent decoder checks.

### Components and quaternion representation

- Treat rows as `12 * numBones` parent-local component arrays.
- Use **native W-drop**, not four independently quantized quaternion components. For each quaternion xyzw, negate all components if w < 0, divide by `abs(x)+abs(y)+abs(z)+abs(w)`, and omit the w component at `bone*12+7`. Store every omitted bone in the W-drop table. The native decoder reconstructs the signed L1 quaternion and normalizes it.
- Dynamic component: max-min > 1e-7, excluding omitted w. Others are constants.
- Quantize each dynamic component to integer 0..4096: offset=min, scale=(max-min)/4096, q=clamp(round((value-offset)/scale)). Constant float data stores each constant's first value.
- Independent four-component quantization produced slightly non-unit quaternions; the public importer rejected the prior candidate. Normalizing only an error metric does not repair the encoded representation. W-drop produces unit decoded quaternions (~1e-7 norm error here).

### Packet layout

Each block samples **16 frames with stride 15**, including a one-frame overlap. Iterate `range(0, numFrames, 15)` and clamp samples beyond the endpoint to the final sample. Use `ceil(numFrames/15)` blocks; `ceil((numFrames-1)/15)` omitted a required native block in the first probe.

Group up to 16 dynamic component lanes; pad missing lanes with zeros. One packet is 528 bytes: 16 bytes `0xff`, then 32 bytes for each of 16 lanes. Each lane contains 16 integer samples. Predictor residual with pre-lane negative indices zero:

```text
r[i] = q[i] - 3*q[i-1] + 3*q[i-2] - q[i-3]
signed14(r) = (r + 8192) % 16384 - 8192
```

Split the 16 residuals into two 8-value windows. Each window is a 128-bit integer built at increasing low-bit positions, serialized as **16 bytes big-endian**. For each consecutive pair, emit a 4-bit width (0..14), then the two signed two's-complement residuals at that width. Width zero encodes two zeros. Choose the minimum signed width fitting both values. Window size must remain <=128 bits. It is a **third-order finite-difference predictor**, not raw positions, first differences or ordinary little-endian byte fields.

### Native arrays for the tested profile

`intData` is concatenated tables; `intArrayOffsets` holds each table's uint16-entry offset in this order:

1. Cumulative compressed block end byte offsets, each uint32 split low/high uint16.
2. Empty.
3. Bone presence bitmasks, 16 bones per word.
4. Zero seed flags, one per group of 16 dynamic components.
5. Dynamic component indices.
6. Empty.
7. Constant component indices.
8. Empty.
9. W-drop bone indices, all bones in this fixture.

Append eight zero integer padding entries. `floatData` is constants, dynamic scales, dynamic offsets/minima, then four zero padding floats. `floatArrayOffsets = (0, constant_count, constant_count+dynamic_count)`. `firstFloatBlockScaleAndOffsetIndex = (dynamic_count//16)*16`. Preserve unrelated native fields. This is a validated profile, not an exhaustive encoder for every predictive flag/table arrangement.

Selected output: idle 55 dynamic components, 20 blocks, 42,240 compressed bytes; walk 126 dynamic components, 9 blocks, 38,016 compressed bytes. Random/smooth controlled translation probes were independently decoded before these full candidates.

## Independent decode and deformation checks

Use the installed core's actual interface (recheck help after updates):

```powershell
& $core -m src.core.animation_clip --source $candidateRhka --clip-index 10 --output $idleSamples
& $core -m src.core.animation_clip --source $candidateRhka --clip-index 3 --output $walkSamples
```

Check decoder exit status and retain logs. Match every expected sample/track, translation, quaternion orientation and quaternion norm. In this fixture maximum errors were idle 6.04e-8 translation / 3.67e-5 radians; walk 1.31e-6 / .0008374 radians. Both were asserted below .001 translation and .001 radians, with quaternion component/norm assertions. Always compare orientations using normalized dot products, while checking raw quaternion norm independently.

Re-import **actual native-decoded samples**, not original Actions, using installed `garrison.unit_animation.import_clip_action`. The proof compared resulting bone-head positions with authored source (<.000534 units), exact loop endpoints, finite evaluated vertices on all three LODs, pack/cloth seating and planted-foot proxies. World ankle drift under the preserved reference travel was .000452708 units maximum; weighted-toe-region lowest-vertex stance-height variation was <=.000246784. These offline measurements are not engine ground-collision proof.

## Private integration and package preservation

Create a new private animator stem and copy its native RGM/RGO/RHKA/rootmotion resource family. In the tested clone, only the RGM BANA self-path changes; native RGO and rootmotion are byte-exact copies. `garrison.model_variants.rewrite_model_path` required **backslash-form** old/new paths for RGM; applying it blindly to RGO/rootmotion failed because they contain no matching self-path. Verify changed leaves rather than assuming all four files need path edits.

Repoint only the playable buffalo's actual attachment `parent_animator` fields (default and xp3 here). Verify binary RGD read/write roundtrip before mutation and compare every primitive field afterward. Keep the existing model geometry attachment, actor identity, animation tree, gameplay and Ministry's static buffalo untouched. A new animator filename alone does not activate a replacement.

Tested attachment: `attrib/attachments/attachment_lists/vietnam/release_076/vn076_water_buffalo.rgd`. New stem: `art/scenario/garrison/cc082/buffalo_animator/animator`. Final each: 1,421 members, exactly one changed existing attachment, four added private resources, zero deleted, 1,416 untouched originals exact, all original mounts exact. New art members mount under data; compiled attachment retains attrib mount.

Assemble over the verified owning 0.8.1 archive, preserving its compiled-only overlays, GUID, archive namespace and bundle key. New allowlist/version policy is required; do not relax a frozen historical packaging action. Verify archive identity before/after, full extracted member hashes/mounts, ZIP CRC, metadata and embedded SGA hash. A fresh Content Editor or FBX model cook was **not** performed for this animation-only native-resource update; previously verified geometry is retained. Report direct native encoding/readback distinctly from a model cook or Content Editor burn. Package alone never exports changed Blender Actions.

Ship idle-only first and idle+walk second. Restart the game after candidate changes to avoid cached private resource paths. Detect the new motion itself, not merely absence of a T-pose. Test movement interruption, return to idle, ordinary walk vs unchanged trot/run, starts/stops/turns, equipment, work/death and relevant consumers. Do not broaden a brief “works” report to every acceptance item.

## Reproducibility and exact local evidence

Project root **P**:
`E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison`

Owned required inputs **R**:
`F:/aoe_4_temp/Community_civilization_pack_garrison_temp/resources_082_animation`

Tested interpreter: `E:/Blender5.2/5.2/python/bin/python.exe` (Python 3.13). General Codex Python had a different ABI. R contains independent PyPI wheels, installed runtime, `manifest.json` wheel SHA-256s and `requirements.lock.txt`; retain these as rebuild inputs. Restore into a new runtime directory with Python 3.13 pip `--no-index --find-links <R/wheels> --target <runtime> -r <R/requirements.lock.txt>`. Do not depend on another mod's cached runtime. Pin actual wheel hashes and inspect source APIs after upgrades. Lock generation must parse METADATA **headers only**: a package's long-description text can contain additional `Name:`/`Version:` examples and corrupt a naive whole-file parser.

Codec versions: soulstruct-havok 1.5.0, soulstruct 2.6.0, constrata 1.3.3, numpy 2.5.4, scipy 1.18.1; the complete lock also pins rich/typer and their transitive dependencies. Isolated target use avoids changing Blender/global packages; unrelated global resolver conflict warnings are not a substitute for testing this isolated interpreter.

| Under P | Purpose |
|---|---|
| `tools/release_082_animation/{native_codec,predictive,encode}.py` | Proven full writer, packet encoder and clip replacement/readback wrapper |
| `tools/release_082_animation/{probe_packets,probe_fields,test_packets}.py` | Controlled codec discovery and qualification |
| `tools/release_082_animation/{author,preview,qa}.py` | Authoring, actual-decoded preview and quantitative deformation checks |
| `tools/release_082_animation/{prepare_integration,package,finalize}.py` | Native owning attachment/private resources, strict packages, rebuild/ZIP receipts |
| `tools/release_081/animation_source.py` | Reused idle authoring helpers; its older walk is not the selected new IK gait |
| `art/authoring/release_082_animation/v2/buffalo-idle-walk.blend` | Editable accepted source |
| `art/recipes/release_082_animation/recipe.json` | Source/script hashes, selected encoding, runtime, integration/QA/package pointers |
| `output/release_082_animation/{source-v2,encoded-v3,encoded-rebuild-v1,preview-v1,qa-v2,integration-v2}` | Selected evidence; earlier failed variants remain diagnostic, not delivery |
| `output/release_082_animation/delivery-v1/{idle,idle-walk}` | Pilot ZIPs and full member verification receipts |
| `output/release_082_animation/completion.json` | Byte-identical owned-runtime rebuild and final ZIP recheck |
| `docs/BUFFALO_ANIMATION_082_TRIAL.md` | Original handoff; pre-test pending status must be read alongside later user confirmation |

Run `encode.py --output-label encoded-NEW_LABEL` with Blender Python from P; output directories intentionally refuse overwrite. Other scripts have versioned output constants: inspect them and use new paths when rebuilding rather than overwriting selected artifacts. Serialize Blender/native operations and preserve unrelated live work. The skill's pure packet helper is reusable; project wrapper paths and cattle indices must be adapted from verified new inputs, not copied blindly.

Native source RHKA SHA-256: `01faed8fd3db588867b8a6d9539246bf9c5ef3734d5248c32adf7a249ef48fab`.

| Artifact | SHA-256 |
|---|---|
| Selected source blend | `efa0de527194f8ae94ea7f04b0ec236f47daad28646237b5ef9693d3e86a33d9` |
| Idle RHKA | `0e0c8b296a582c518eb99d4fd19cfef4a702410f9d84a9cba5cd4806c44d9324` |
| Idle+walk RHKA | `8ace8feb7f5a76b45e7aff44bf7a8800ac968476a076bc5fe2fa5b674b2bc55e` |
| Pilot.1 idle ZIP | `5faeabf213fa138fd499b9bc9a0df0120da1291d7819ed2e6cece1db945bf024` |
| Pilot.2 idle+walk ZIP | `aac388ee772a52fa089b1dd866998faaef80033b545ddc2b422b83f21b69fc12` |
| Preserved 0.8.1 ZIP | `75963810d5b241680fad90ff5b4c4f81cb0ba37f550c3b2e65b103f0250fd3e0` |

Do not substitute an earlier encoded-v2 file: it lacked native W-drop quaternion normalization. encoded-v3 and the independent owned-runtime rebuild are the selected bytes.

## Shrek mechanism corroboration

The installed **Modding Showcase 0.1.1 by overbait** provided a concrete private-slot replacement example. Its Shrek squad has private `dance_once` → `ability_activate_entity_tree=cheer_toggle` → native infantry routing → private Shrek animator → eight replaced `cheering\idle_calm_cheering_01` … `_08` slots. Each uses the same new 225-frame / 7.466666698-second 48-bone dance; the library has 210 clips vs the matching stock base_spearman's 182. The mode SCAR spawns demonstration units; it does not write bone poses per frame. Interruption settings are packaged evidence, not newly observed runtime behavior.

This demonstrates private native clip replacement behind an existing graph trigger. It did not disclose the creator's source encoder and its human motion is not directly compatible with cattle. Ordinary buffalo idle/walk needs its existing navigation slots, not a dance ability. Exact inspection: `P/docs/SHREK_SHOWCASE_ANIMATION_MECHANISM.md` and `P/output/release_081_animation/showcase-inspection-20261024`. The later independent cattle encoder above supplies the formerly missing encoding step.
