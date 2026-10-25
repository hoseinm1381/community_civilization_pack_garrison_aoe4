# Custom assets in an existing Content Editor mod

Read when replacing civilization models, age variants or equipment while preserving an existing project's gameplay and native motion. Search terms: private attachments, tier bodies, parent_animator, stock weights, UV atlas, graft, Buffer too small.

## Evidence and ownership

The 2026-10-11 Berber/Tuareg trials used Garrison extension 0.1.3 and Blender 5.2.2 LTS. Earlier custom bodies/shield/spear loaded in user-run native matches. The refined.1 candidate passed source checks, native cooks and archive readback; its improved art, materials, fitting and LODs await user acceptance. This demonstrates an isolated integration technique, not general Garrison synchronization with arbitrary Content Editor projects.

Retain the original `.aoe4mod` GUID, source hashes, prior working package and rollback instructions. A separate Garrison art project may have its own GUID; that is not the intended final civilization identity. Work in a separate candidate unless the user requested production-source edits. Preserve unrelated source and archive bytes and identify every deliberately changed resource.

## Build compatible art before changing bindings

- Decode the actual age bodies, animation owner and equipment recipes. Keep untouched reference meshes separately. Start model qualification with zero animation replacements.
- Check bone names, hierarchy, root, bind matrices and placement against the exact build prototype. The Tuareg fixture matched the 48-bone English spearman prototype; this does not admit other rigs by bone count alone.
- Reuse compatible stock weighted anatomy where useful; substantially redesigned clothing and equipment can retain native motion. Skin additions against the actual body and review deformation, rather than replacing anatomy with disconnected primitive limbs.
- The fixture verified normalized weights with at most four influences and skeletal LOD counts 48/32/26. Bone folding is not mesh decimation. Review all LOD distances in game.
- Use one bound mesh/material and a unique active UV atlas for the documented unit route. The refined fixture used 1024 maps; this is an example, not a universal resolution requirement. Bake stock detail and layered authored surfaces into explicit albedo, tangent RGB normal, roughness, metalness and pattern sources. Preserve original UV lookup while baking onto a new atlas; decoded packed game maps are not equivalent source maps.
- Pattern red controls owner colour; green/blue are skin/hair masks. Place owner colour on a visible fitted surface and test two player colours. Baking a blue preview into albedo is not dynamic team colour.
- Derive clothing contact from the weighted body's surface where flat straps/belts penetrate or float. In the fixture, ray-cast seating corrected belt, carrier and tabard fitting. A finite deformed vertex check does not prove all-motion intersection clearance.

Rigid equipment follows native hand sockets without a separate character skeleton. The verified Donso shield recipe used `MetaRig_LArmPalmSocket` across all four ages; the spear used `MetaRig_RArmPalmSocket`. Preserve the exact origin, orientation and recipe transforms; check actual grip/contact per age and action.

Change the shield shell relative to its fixed grip to adjust fitting. The refined fixture kept a 1.15 m tall shell and lowered it by 0.45 m with a 0.04 m lateral shift; these are fixture coordinates, not a general socket offset. Its 70 sampled height checks passed, but do not prove native collisions or hand contact throughout every action.

Lengthen a spear along its shaft axis while preserving practical head size, thickness and grip. The trial extended only the blade side by 1.875 m, from 2.50 to 4.375 m, leaving the butt unchanged. Uniform scaling or symmetric extension can enlarge the grip or drive the butt underground. Visual length does not automatically change attack reach, damage or hit timing.

## Wire private visual resources

Map every consuming reference before editing: all age/tier bodies, future upgrade bodies, default/expansion variants and weapon states. Ordinary spear, charge, brace/spearwall and torch are independent slots. A successful idle model does not cover them.

Create private attachment lists using the Content Editor's supported serialization where possible. Preserve their generated identities, list structure and owner-qualified references. For an established private list, change only the measured visual fields and verify compiled identities after cook.

For model-only replacement, compatible prototype geometry can be consumed while retaining the target's own animator, statemodel, speaker bindings, production and upgrade targets. Do not install generated English entity/squad/animator resources simply because Build Unit produced them. `base_spearman` and `base_spearshield` have compatible fixture rigs but different libraries/graphs; read [Animation research and ability diagnostics](animation-research.md).

The tested integration staged the freshly cooked art resources into the isolated Content Editor candidate before native reference validation, cooked that candidate, then selectively grafted the intended compiled attachment RGDs and media into the working archive. Use this only with a compatible, verified archive tool: preserve the final GUID, inventory both archives, extract/read back every changed resource and compare untouched bytes. It is not a substitute for a new source cook or native testing.

Discover the installed Garrison extension's `bin/sga-archiver.exe`, inspect its current help and supported archive version, then test `list --verify` and extraction on the actual baseline/donor. The tested 0.3.0 tool exposed these forms (paths and members are examples to substitute, not permission to graft whole donors):

```powershell
& $garrisonArchiver list $baselineArchive --verify
& $garrisonArchiver graft $baselineArchive $donorArchive $newArchive 'attrib/attachments/example.rgd'
& $garrisonArchiver extract-member $newArchive 'attrib/attachments/example.rgd' $extractedMember
& $garrisonArchiver decode-rgd $extractedMember $decodedXml
```

Use a new destination, exact inventory-derived member spelling and an explicit allowlist. Verify final inventory, project GUID, all dependencies and extracted unchanged bytes before packaging. If the installed tool lacks these operations, retain separate cooked outputs and identify the missing integration contract instead of guessing a binary edit.

## Diagnose cook failures by their first failing stage

| Signature | Interpretation and measured next step |
|---|---|
| Allocation failure, sometimes followed by AccessViolation or a misleading validation refusal | Inspect the underlying editor/archiver log, available memory and task-owned lingering processes. Free unused heavy apps with the user's cooperation; retry the unchanged source. Do not change rig fingerprints because a helper reported an indirect failure. |
| `StringToPtrUTF8: Buffer too small` in `RRTextureBurnerImpl.Save` | A distinct texture-writer failure. Record source/output path lengths and test a byte-identical isolated project copy at a shorter path. In this fixture the long-path cook failed and `E:/trf1` succeeded with exit 0, supporting a path-length limitation. The exception text alone is not proof of that cause on another project. |
| External process termination / interrupted tool session | Separate it from asset validation. Retain native logs/exit status; retry from unchanged source only after classifying the interruption. A hidden task-owned detached worker can survive tool-session teardown, but record its PID, command and logs. |
| Failed cook with an older SGA still present | Never package that stale output as the new build. Require fresh successful cook metadata, archive hash and source-to-staged export comparisons. |

Use Garrison's prepared model-capable editor for model cook; an ordinary Steam editor alone does not extend that route. Already cooked media can then be validated in the existing Content Editor candidate. Do not kill unrelated user apps or assume all Blender/editor processes belong to the task.

## Delivery proof

Check current FBX/PNG hashes against the staged art, successful cook/live-reload-off records, model/resource dependencies and final GUID. Decode compiled private attachment RGDs to confirm only intended attachment model-resource fields (`animator`, `parent_animator`, or mesh reference fields) changed and PBG/list identities remain. Preserve the unit's separate animation-owner binding. Freshly extract and hash untouched gameplay, ability, entity, squad, weapon, upgrade, SCAR and speaker-binding members. Preserved voice bindings do not by themselves prove audible output.

The refined.1 archive contained 363 members: nine changed visual lists, 46 new media files and 308 prior members byte-preserved; all 266 production source files stayed unchanged. These are regression evidence for that package, not counts to require of other mods.

Package the actual verified archive with version, hashes, logs, install/lobby choices and rollback. Retain editable Blender sources, packed/source textures, scripts and untouched references separately. In a fresh native match test each age, training/upgrades, idle, directional movement/turn/stop, attacks, charge, brace, torch switching, reactions, death, near/far views and two colours. Review stock-unit isolation and gameplay separately. A better mesh or different socket fit does not fix delayed graph switching.

## Local provenance

Berber workspace: `E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai`. Discover equivalent paths on another machine; the workflow does not require this project.

- Editable/reproducible source and integration helpers: `art/tuareg_refined/`.
- Source rig/texture/deformation pass: `output/tuareg_refined_trial/source-validation.json`; fitting: `shield-fit.json`.
- Successful Garrison/native builds: `garrison-art-build.json`, `candidate-build.json`; final fresh readback: `validation-summary.json`, `delivery.json` in the same output directory.
- Refined package: `berber_future_kingdom-0.1.5-tuareg-refined.1.zip`; native art acceptance remains pending as recorded on 2026-10-11.
