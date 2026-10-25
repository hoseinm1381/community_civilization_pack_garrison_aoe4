# Animation contracts and qualification

Use for Rig & Animation, Game Prototype, Fit Character, Retarget Motion, Edit Actions, Animation Replacements and Build Unit. Search terms: full-body idle, Mixamo, pelvis walk, inherited only, private animation library, Donso, camel, precache, Rigid to One Bone, Source FPS, Auto-Rig Pro, legacy manifests.

For ability-driven posture, moving delays, Shrek/native cheer, forced-tree calls, Havok writer research and per-motion coverage, read [Native animation research and diagnostics](animation-research.md). For compatible model-only integration into an existing civilization, read [Custom asset integration](asset-integration.md).

For the **2026-10-24 native-tested buffalo idle and full four-leg walk**, read [Native predictive encoding and private integration](native-predictive-animation.md). That separate metadata-preserving route includes a reusable encoder, native decoder commands and exact evidence. The panel restrictions below remain panel restrictions; they no longer imply that cattle authored-motion encoding is unavailable.

## Evidence and scope

Inspected on 2026-10-10: installed Garrison 0.1.0 guide and panel/export Python, plus its live catalogue and timing helpers in Blender 5.2.2 LTS. No new animation source was built, cooked or tested in AoE4 during that investigation. This reference records current authoring/export contracts and a qualification procedure; it is not finalized runtime acceptance.

On 2026-10-11, installed Garrison **0.1.4** `guide/rig-and-animation.html` was compared directly with this reference to add binding, import timing, external retarget setup, source export and older-project update details. Its documented prototypes/replacement slots retain the earlier catalogue contract; no new live catalogue query, Blender build or native trial was performed. Unit texture inputs/defaults are in [Asset and unit workflows](assets-and-units.md#unit-texture-inputs-and-defaults).

The subsequent 0.1.3 inspection on 2026-10-10 rechecked the live catalogue: `english-villager-1` still has 22 replacement slots and `english-spearman-2` one. Its animation guide retains the same contracts. The release describes a Jolt-backed ragdoll facility, with stock-animation fallback; the inspected Lua helper only computes cosmetic impact direction. Read [Scenario tools and qualification](scenario-tools.md) for the 0.1.4 duration/travel addition and its separate rig/backend gate. Do not infer new authored death/attack replacement support from ragdoll availability.

The 2026-10-11 Tuareg trials add fixture evidence: custom skinned art/equipment loaded, native cheer blocked movement for the trial interval then restored it, and stock guard selection changed promptly at idle but after 3–5 seconds while moving. Model cooks/readback passed; immediate moving Q and a full custom motion set did not. The refined.1 art package is build-verified with native art acceptance pending. These results supersede the earlier inspection-only status only for their exercised fixtures.

Prefer the current installed guide and actual contracts over this version snapshot. The guide notes that some local authoring additions were absent from the October 3 stable package; the extension version string alone does not prove another installation has the same features. Inspect controls/catalogue and keep the authoring and player components compatible.

Separate evidence as follows:

| Evidence | What it establishes |
|---|---|
| Guide and panel inspection | Documented behavior and exposed controls |
| Live catalogue/timing helper | Installed prototype choices and admitted replacement slots |
| Scene preview and mapping/validation | That candidate's authoring checks, not native playback |
| Build, cook and archive readback | Resource generation and wiring, not correct game appearance |
| Fresh solo match | Only the exercised fixture, transitions and behavior |

The guide reports operator acceptance of Eric/Mesh2Motion Jumping Jacks on villager and spearman fixtures, multiple villager idle overrides/restoration, and a footballer/Macarena solo example. The Eric result was repeated using Garrison alone for fitting and retargeting. These are guide-reported tests, not this workspace's new native verification. An earlier pelvis-walk route was accepted; the current prototype walk path still needs its own game check. No general multiplayer acceptance follows.

## Installed build catalogue

| Prototype key | Skeleton / skeletal LOD counts | Replacement contract | Status |
|---|---|---|---|
| `english-villager-1` | 73 bones; 73/50/32 | 16 full-body calm unarmed idles; 6 restricted calm walks | Catalogue says Build supported; each new result needs game review |
| `english-spearman-2` | 48 bones; 48/32/26 | `navigation\idle_calm_basic_01` only | Experimental; game review required |

Villager idles are under `navigation\idles\`: `idle_calm`, `idle_calm_yawn`, `idle_calm_wipe_nose`, `idle_calm_stretch`, `idle_calm_shift`, `idle_calm_scratch_side`, `idle_calm_scratch_head_lean`, `idle_calm_look_up`, `idle_calm_look_sun`, `idle_calm_look_right_02`, `idle_calm_look_right`, `idle_calm_look_left`, `idle_calm_look_around2`, `idle_calm_look_around`, `idle_calm_headscratch`, `idle_calm_adjust_clothing`.

Villager walks are `navigation\walks\calm_walk_0N_f_fast_slide` for N = 1, 2, 3, 4, 5, 7. They admit only vertical `metarig_pelvis` bounce; every other bone stays at rest. This does not replace a complete arm/leg gait. Spearman locomotion stays inherited.

No Donso, archer, cavalry or camel prototype was listed. A decoded native humanoid can be a retarget authoring target when stock hierarchy/bind records, game root and role chains validate; that does not admit it to Build Unit. Bone count or similar names alone do not establish compatibility.

The English prototype's `base_spearman` owner and Tuareg's `base_spearshield` owner are not interchangeable libraries. Compatible skin can be consumed while retaining the target's animator; a prototype calm-idle replacement does not automatically bind to Tuareg Q or shield-specific motion.

## Choose the authoring operation

Open **3D View -> N -> AoE IV -> Rig & Animation**; the panel is available without a selected skinned mesh. Choose **Rig** or use the selected model's eyedropper. **Select Animation Rig** selects generated Pose Controls when available, otherwise the deform armature. Guide screenshots show an earlier panel revision; use the current text and controls for manual mapping and optional textures.

- **Fit Character:** import an already skinned FBX/GLB character, detect/check its character mapping, then Create Bound Copy. The character and motion source may have different rigs and need separate mappings. Fitting preserves originals, UVs and materials, folds unmapped descendant weights to mapped ancestors and normalizes the strongest four influences. Unmapped weighted roots are refused. Prepare shape keys, extra modifiers and mirrored/nonuniform scales on a working copy first.
- **Keep Named Weights:** use only for a mesh already compatible with the exact target skeleton, bind pose and placement. It does not retarget weights or automatically fit proportions. An unrigged mesh needs skin weights; these controls do not provide automatic skinning.
- **Rigid to One Bone:** under **Bind a Mesh**, choose the mesh, this method and the target bone, then **Bind Mesh to Rig**. Every vertex receives full weight on that bone; deformation weights are replaced while unrelated mask groups remain. Use for a simple prop or initial animation test. Both binding methods preserve mesh placement, provide Blender Undo and do not resize or fit the mesh.
- **Import Motion / Retarget to New Action:** FBX or GLB/glTF on a different humanoid source. Detect naming independently for each lane: Renderpeople Human, Mesh2Motion Human or Mixamo Human, including namespace prefixes. Detection refuses uncovered naming and reports missing roles. Otherwise **Start Manual Mapping** creates empty rows only when that lane has no mapping; existing rows remain editable under **Bone Mapping**. Fill all 22 required Source bone/Game bone pairs; leave unused optional finger rows entirely blank, since partially filled rows can refuse the operation. Under **Joint Endpoints and Corrections**, set paired landmarks and rotation corrections in degrees. **Create Bound Copy** and **Retarget to New Action** require a passing **Check Mapping** for the current rigs and mapping; recheck after any pair/rig edit, detection or preset load. Save/load each lane's mapping as Garrison JSON presets and retain the per-rig settings in the `.blend`. Fit the character once and reuse its prepared mesh for later motions.
- **Import FBX Animation:** transfer takes from one already equivalent animated skeleton. Names, parentage and rest transforms must match; namespace matching does not make unrelated rigs equivalent. Each compatible take becomes a separate Action, the first is activated, existing Actions remain, and temporary imported meshes/materials/rigs are removed. Clips are sampled at the import scene's frame rate into editable quaternion transform curves. Put travel on the root bone; animated armature-object transforms are refused. This authoring import does not expand the stationary-root idle or bounded-walk export contracts.
- **Edit Actions:** **Prepare Animation**, then **Copy Active Action** or **New Rest Action**. Edit keys, choose **Authored Action -> Activate Authored Action**, and set Start/End/FPS. **Browse Stock Clips (Keep Action)** releases the Action for stock preview without deleting it; reactivate it to return. Blender authoring is not limited to build prototypes, and a mesh is optional. Export support is determined later by the target prototype and slot; unit-model export also needs a stock animation owner.

For **Retarget Motion**, choose the source rig, take, range and FPS. GLB timestamps use the selected **Source FPS** during import; FBX uses its imported timing. Only the chosen take is evaluated, without NLA blending. Fractional source ranges become whole output frames with adjusted FPS to preserve duration. Inspect the baked result before assigning it to a slot.

Garrison retargeting uses FK, with no automatic foot locking/IK. In Place removes horizontal pelvis travel while retaining height. Match Last Pose to First replaces the final sample; it does not guarantee a smooth loop. Inspect feet, wrists, palms and grip. Index/middle finger landmarks help resolve palm twist. Auto-Rig Pro is optional and separate; external solver constraints must be baked into an exportable Action, and do not expand Garrison's clip contracts.

### Optional external retargeting

For **Auto-Rig Pro -> Remap**, import the external animated rig (GLB, FBX or BVH), use it as Source and the unchanged villager prototype as Target. Fit/skin the mesh separately: animation transfer does not transfer skin weights. Map pelvis, spine, neck, head and both limbs; stock arm twist segments are not extra elbows. Set the pelvis as motion root and match T/A poses through the source's preserved rest-pose correction, keeping the game skeleton intact.

The installed guide provides `guide/assets/mesh2motion-civilian.bmap`, a **40-bone Mesh2Motion Human -> Civilian** preset for **Mapping Presets -> Import**. Review the mappings and rest-pose correction before baking; the preset does not fit the mesh or replace that correction. Auto-Rig Pro is separately installed. Mesh2Motion Explore can supply motion; its experimental **Use Your Rigged Model** output must still pass Garrison's unchanged-rig checks.

Bake constraints to a bone Action, then **Edit Actions -> Copy Active Action**, set range/source FPS and inspect feet, shoulders and the loop seam. Keep `metarig_root` at rest and jump height on the pelvis. Assign via **Check Supported Idles -> Assign to Checked**, then **Validate Unit -> Build Unit -> Cook -> Package** and test idle/move/stop in a solo match. External tools do not replace Garrison's cook/package steps or add replacement slots.

## Timing, export and gameplay boundaries

- Assign only rows marked **Supported**. The UI rejects inherited-only assignments; export checks them again. Read-only `clip_timing` checks of representative attack, spearman walk and death names returned `replacement timing is not qualified`. This is an installed-route limit, not proof that the engine can never support them.
- **Assign to This Clip** affects one row; **Assign to Checked** includes checked rows hidden by the list filter. Each row keeps its own Action/range/FPS. **Restore This Clip to Inherited** removes the override while retaining the Action; each build starts from the original library so restoration leaves no stale replacement.
- Full-body idle replacements may include limb movement, gestures, dances or jumps on the unchanged skeleton. Keep `metarig_root` stationary and bone scale at 1; put jump height on the pelvis. Endpoints must match. `repeat_idle_cycle` fills the original duration with whole cycles, adjusting speed; one Action may play at different speeds in different slots.
- `fit_walk_cycle` resamples one pelvis cycle to the stock walk duration and retains stock root travel, events and speed. Every replacement loops. Do not apply a full-body walk or change native root travel through this restricted route.
- Export samples one assigned bone Action with a valid range/FPS. The inspected sampler admits 1–240 FPS and 2–10000 samples, refuses object-motion channels, NLA/drivers, shear and unsupported constraints, and supports generated Pose Controls. Bake other controls on a prepared copy; do not silently strip motion to force validation.
- Skin FBX export uses `bake_anim=False`. Replacement animation is sampled separately into the unit build document and private animation library. **Export Unit Model** is the separate civilian-template source route: it writes `model.fbx`, `model.rig` and `unit-model.json` into the Mod Project's `units` folder. The `.rig` contains ordered bone names and one named-endpoint block per partition. All three files update together, with rollback on a failed write. This export does not itself add a playable unit and is not automatically consumed by Cook. Use **Build Unit** for the supported route.
- Browseable Attack/Death/Cheer categories are inferred from names, not an established command-to-animation map. Only the inspected default binding is verified from the actual blueprint. Replacing an idle changes that idle's motion; it does not create an ability/button or arbitrary animation trigger. The historical Shrek cheer used a separate experimental runtime recipe and does not qualify generic cheer-slot export. Generic presentation modules do not add native bone-pose support.

Attack/death replacements, full locomotion, extra bones and new skeletons remain outside the inspected panel's contract. A separate [native predictive route](native-predictive-animation.md) now qualifies cattle idle and full walking playback on its unchanged skeleton; it does not add panel prototypes or qualify those other motion families. Investigate other unsupported routes separately without editing admission flags or inventing fingerprints.

Decoded Game Library retarget targets need complete saved stock hierarchy records and decoded local bind-transform status. Checks cover every bone/parent, unchanged `metarig_root` and required humanoid role chains; missing or changed records refuse retargeting while preserving the scene. Passing these checks does not grant an English prototype identity or Build Unit eligibility.

## Update an existing rig project

Install the current extension ZIP and restart Blender to update its bundled core; changing checkout Python alone does not update the installed extension. Keep copies of the `.blend` and Mod Project before rebuilding. Choose the update matching the actual problem:

| Existing condition | Guide-documented update |
|---|---|
| Animator-scale correction only | **Cook -> Package** inherits prototype animator scale. Do not also multiply mesh size manually. This exception does not export geometry or Action edits. |
| Old Renderpeople mapping lacks fingers | **Detect Mapping**, re-enter custom corrections, then **Check Mapping -> Create Bound Copy** and rebuild affected units; source meshes and Actions remain. |
| Updated motion calibration | **Retarget to New Action**, reassign supported clips, then **Build Unit -> Cook -> Package**. |
| Red "not precached" boxes in a scripted project | **Cook -> Package** adds the prematch helper; import the generated loader during loading and test the new package in a fresh game process. A timer after `Squad_Precache` does not establish completion. |
| Previous prototype manifest omitted clip timing | Timing is resolved in memory from the qualified clip name and prototype; Actions, assignments and the saved manifest remain intact. |
| Previous civilian build record | Preserve generated sources; recooking requires rebuilding a copied candidate through **Game Prototype**, without inventing a prototype fingerprint. |

For a unit mod without a generated map or Game Mode, **Share** and `START-HERE.txt` provide a precache reminder. Add an authored SCAR script importing `<project_key>/garrison.scar`, cook again to generate the loader/unit helper, and have the existing map/mode load that script before the match. An `OnGameSetup` timer is too late; selecting a scriptless Tuning Pack does not execute the helper. Verify the external consumer in game. Use `aoe4-game-mode-skill` when implementing the SCAR integration.

Switching **Rig** restores per-unit prototype, character/motion mappings and clip overrides saved in the `.blend`. Loading another prototype creates a separate candidate while retaining previous meshes, rigs, Actions and assignments; refit/review for the new skeleton. A changed game-source fingerprint stops the build and requires a new candidate. Hand-edited generated sources require a new unit name rather than overwriting those edits.

## Qualification when testing is requested

1. Inspect the live file/dirty state, installed guide, prototype choices and player/tool versions. Preserve existing user work. Choose a separate probe project/candidate and a supported stock control before production integration; retain editable source and project identity.
2. First test the bound custom mesh with **zero replacements**. Preview original clips, validate it, then Build Unit with one mesh/material/UV atlas and explicit source textures. Verify generated private entity/squad, inherited animator/equipment and skeletal LODs. Build does not add a production command.
3. When qualifying animation replacements, start with one supported idle override. Record the exact source rig/take, mapping, range/FPS, target prototype, slot and assignment. Preview the loop, then Validate Unit → Build Unit → Cook → Package. Expand to multiple overrides and restore one only after the control and first override pass. Model-only integration retains zero replacements; do not add an idle override merely to deliver a new mesh.
4. Read back the latest successful cooked resources and blueprint/attachment references. Package alone does not rebuild scene changes. When consuming generated units or Garrison helpers through a script, load generated `<project_key>/garrison.scar` during the consumer's loading phase, before simulation; immediate spawn after `Squad_Precache` or a later timer is not proof resources finished loading. Use the existing authorized map/mode consumer when suitable. Replacing model resources through an existing unit's private attachments does not inherently require a generated-unit loader or a new Game Mode.
5. In a fresh solo match select required lobby components. Observe inherited control versus override: idle → move → stop → idle, complete loop/seam, scale/orientation, deformation, hand/foot contact, equipment changes and relevant combat/death/respawn. Check two player colours when using a pattern map, and visible behavior across LOD distances. A working override should leave stock controls and other clips behaving correctly.
6. If requested, qualify the restricted villager walk separately: inherited comparison, only vertical pelvis motion, start/stop/turn transitions and unchanged travel speed. Do not promote the earlier walk fixture's acceptance to this new prototype path.
7. Treat replacement of an existing civilization unit as another gate. The guide's footballer example rewires one animator and four tier body references using the explicit mod owner; it does not automatically convert a Donso or all units/ages. Verify the actual target's animator, tier bodies, statemodel and weapon slots before wiring. Test training, age/tier upgrades and relevant commands in the intended mod.
8. Record each gate as passed, failed, unverified or not exercised, with exact build/package identity, readback/log paths and native observation provenance. Classify a failure by authoring, export, cook, loading/wiring or runtime before choosing a correction. Change only the affected guidance after evidence; keep untested families pending. If a request is documentation-only or postpones testing, update the reference now and leave these execution gates pending.

## Sources to recheck

Within the installed extension, read `guide/rig-and-animation.html`, `guide/look-inside-a-unit.html`, `guide/first-custom-mod.html` (Macarena and stock-villager wiring), and `guide/tools-and-pipeline.html`. Corroborating source: `unit_prototype_panel.py`, `unit_action_export.py`, `unit_export.py`, `external_animation.py`, `humanoid_retarget.py`, `retarget_panel.py` and `animation_catalog.py`. Core prototype/profile modules are compiled in this installation; query their exposed read-only catalogue, `qualified_timings` and role definitions rather than claiming unavailable source was reviewed. Further tool help: [Auto-Rig Pro Remap](https://www.lucky3d.fr/auto-rig-pro/doc/remap_doc.html).
