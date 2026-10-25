# Garrison 0.8.3 skirmisher redesign implementation plan

> Execute inline with executing-plans; independent final review. This checkout is not Git-managed. Isolate all new work under release_083 and retain all prior sources and deliveries.

**Goal:** Rebuild Vietnamese skirmishers IIâ€“IV and their matched held/throw/projectile visuals, make owner colour readable, and deliver strict version 0.8.3.

**Spec:** `docs/SKIRMISHER_VISUAL_ANALYSIS_20261024.md`, expressly approved by the user's request for all ages and 0.8.3.

**Architecture:** New authored meshes, UVs and material atlas on unchanged native 48-bone rigs; retain native humanoid motions and actor/gameplay. Start from accepted 0.8.2-pilot.2 owning archive so the confirmed buffalo idle/walk and 0.8.1 artwork survive exactly. Native art cook is separate from final owning-archive assembly.

**Tech stack:** Blender 5.2, installed Garrison export/native art cooker, archive tool, Python 3.13.

## Constraints and design

- Garrison GUID b7fcea91-257b-408f-b9e8-ae4d8bc402e1; archive namespace b7fcea91257b408fb9e8ae4d8bc402e1; bundle community_civilization_pack.
- Normal edition, gameplay, localization, abilities, footprints, selection/collision, archive mounts and compiled-only overlays unchanged.
- All new scripts/source/export/recipe/evidence use release_083. No install/publication or deletion. Preserve unrelated live Blender scene; serialized isolated Blender/native cook operations.
- Broad owner-coloured tunic/sleeve/headcloth areas, neutral masked albedo, independent skin/leather/wood/metal. Native pattern red drives owner colour; test packed output and offline two-colour previews.
- Age II layered cloth, headwrap and practical leg wraps. Age III padded reinforcement and restrained leather. Age IV flatter overlapping armour plates and stronger head/shoulder distinction. Consistent Vietnamese light-infantry identity, light warm skin, readable face/hands and measured weapon contacts.
- Three LODs; near body <=20,000 triangles, middle <=10,000, far <=5,000; spend geometry on silhouette and deformation rather than tiny disconnected pieces.
- Preserve donor bind matrices, hierarchy, native skeletal partitions and per-LOD weight folding. Weapon origins/orientations are state-specific. Preserve buffalo animation resources byte-for-byte.

## Tasks and evidence ledger

- [x] Freeze baseline archive/ZIP, editable masters, normal files and identity; record source references and anatomy ratios.
- [x] Build and inspect age-II model/atlas; verify mask coverage, interfaces, UVs and rig. Iterate from previews before tier propagation.
- [x] Build ages III/IV and consistent weapon variants; inspect six directions, all LODs and two owner colours; save sources/recipes.
- [x] Run fresh native art cook, decode all nine resources and compare geometry/material/rig/weights; sample inherited motion for deformation/contact checks.
- [x] Assemble strict 0.8.3 with an explicit media-only allowlist, unchanged mounts/members, identity before/after, fresh full readback and ZIP/metadata/embedded-SGA checks.
- [x] Independent review, resolve important findings, deliver editable sources/previews/package/report. Report native appearance/import/save-load/multiplayer pending user verification.

## Review focus

Owner mask must survive packing and LODs; mask texel coverage is not screen coverage. Skinned lower LODs must not reference excluded fingers. Weapon held, release and flight axes must be independently verified. No native motion/graph changes are required for skirmishers. A verified cook/package is not new in-game artwork acceptance.
