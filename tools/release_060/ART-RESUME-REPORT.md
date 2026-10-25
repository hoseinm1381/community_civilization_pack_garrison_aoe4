# 0.6.0 unit art resume report — 2026-10-18

## Scope and preservation

Resumed the explicitly authorized unit art work after `PAUSE-ART-20261018.md` and `RESUME_CHECKPOINT.md`. `common.guard()` passed before writing. The only preexisting Blender process was interactive PID 6484; all background jobs below ran serially and exited. This worker did not operate the interactive scene, run a native cook, change an active actor or attachment, edit the normal edition, or modify an earlier release.

The output roots below are all release 0.6.0 owned. Each final export folder has `model.fbx`, `albedo.png`, `action.json`, and `authored-snapshot.json`. Its receipt contains the exact source blend, donor manifest, file sizes, SHA-256 hashes, and review images. The body FBXs preserve their native rig and all three weighted LODs. Their saved authored meshes were explicitly triangulated before export, and each uses one saved native atlas. Action sources leave native weapons, tools, tasks, and attachments in their existing owners.

## Final source exports

| Family | Final version | Models | FBX Skin / Cluster nodes | Native rig / exact donor palette |
|---|---|---|---|---|
| Spear | `v3` | `chi_infantry_light_age01`–`age04` | 3 / 144 each | 48 / 46 |
| Ranged correction | `v5b` | `archer3`, `archer4`, `crossbow3`, `crossbow4`, `handcannon4` | 3 / 144 each | 48 / 46 |
| Villager | `v2` | `chi_villager_male_age01`–`age04`, `chi_villager_female_age01`–`age04` | 3 / 219 each | 73 / see below |

Spear exact folder: `art/exports/release_060/spear_roster/<model>/v3`; receipt: `F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_060/qualification/spear_roster/<model>/v3/export.json`. These four exports join the approved v1 weighted tunic/chest pieces into the corresponding native donor LOD, retain each age's original saved atlas, and produce corner snapshots. `chi_infantry_light_age01` partial v2 remains a diagnostic. No original approved v1 blend was edited.

Ranged exact folder: `art/exports/release_060/ranged_roster/<slug>/v5b`; receipt under external `output/release_060/qualification/ranged_roster/<slug>/v5b/export.json`. The shared correction removes the v4 centroid-selected triangle UV patch that formed a visible front sawtooth. One fitted, skin-weighted front panel has straight edges; underlying native armor, headgear, quiver, and other UVs remain as imported. The first `archer3/v5` trial saved partial files but Garrison rejected more than four bone influences at panel vertices. It remains a diagnostic; v5b limits the panel to four normalized influences and all five exports passed exporter preflight. Five v4 outputs remain intact and are superseded. Approved Archer II v3 was already native qualified by the pipeline worker and was not reauthored.

Villager exact folder: `art/exports/release_060/civilian_roster/<model>/v2`; receipt under external `output/release_060/qualification/civilian_roster/<model>/v2/export.json`. Each exact Age I–IV gender donor has a modest flared work garment and age-progressive ochre to red-brown cloth on neutral native atlas pixels. Native faces, UVs, tools, task attachments, and animations remain in their original bindings. The first male Age I v1 trial saved a blend and review but failed export because Blender made the copied atlas path relative; that partial diagnostic remains. All eight v2 exports use absolute owned atlas paths for exporter preflight.

**Donor correction:** live `decoded-static.json` manifests show female Ages III and IV have 73 skeleton bones and a **58-bone skin palette**. The other six villagers have 73/46. The 58-bone palettes were preserved exactly. The earlier checkpoint's blanket 73/46 description was inaccurate for those two donors. All eight FBXs have 219 Cluster records because the source exporter records every rig bone in each LOD; native palette compatibility remains a separate cook/readback gate.

## Art verification and limits

The serial Blender jobs wrote 17 final editable blends, FBXs, atlases, snapshots, actions, receipts, and stock/finish game, close, red, and blue review images. A fresh verification read all 17 receipts and recomputed every listed export file hash and byte count; there were **zero mismatches**. It also recomputed all 17 source blend hashes, checked three snapshot geometry groups per export, matching vertex/skin and triangle arrays, and confirmed three FBX Skin nodes for each. Garrison exporter preflight accepted all 17 final FBXs. The native pipeline worker was given the exact receipt paths for independent cook/readback qualification.

The sampled close reviews show the ranged sawtooth removed and the Age IV female villager's work cloth visible. Blender images remain art review, not in-game appearance proof. Native cook/readback, final archive integration, package/import, and match appearance remain separate gates owned by other workers/root.

After this art handoff, the pipeline worker reported an Archer III v5b LOD1 native weight-corner comparison failure on 69 of 3,648 corners. Positions and topology matched; the reported differences were 1–2 native 8-bit weight counts with the same bone IDs on the newly fitted panel. The pipeline worker is diagnosing compiler normalization. This report does not claim v5b native qualification, and the v5b source/export is preserved pending that diagnosis.
