# 0.6.1 Berber native-building pattern comparison

Read-only targeted comparison, 2026-10-18. Workspace storage guard had passed before archive inspection. No Berber files, CCP source/assets, Blender scenes, or native cook outputs were modified. The Berber Ribat/Funduq media below were inspected from the latest retained 0.9 archive using temporary extraction only.

## Resource family and descriptors

The latest working Berber archive packages each actor's RGD under `attrib` and its RGM/RGO/RRGeom/RRMaterial under `data`. For Ribat, the actor is `attrib/ebps/races/malian/buildings/landmarks/ribat_of_sanhaja/building_landmark_age1_landmarka_mal.rgd`; its model resources are under `art/scenario/garrison/br027_ribat/buildings/ribat_lod0/`. For Funduq, the actor is `attrib/ebps/races/malian/buildings/landmarks/funduq/building_landmark_age1_landmarkb_mal.rgd`; its model resources are under `art/scenario/garrison/bf027_funduq/buildings/funduq_lod0/`.

Both Berber RRGeom headers identify `object_collection`. Their RRMaterials each have paired GMat descriptors `object` and `object_collection` (Ribat GMat names `berberribat_originalatlas2048` and `berberribat_originalatlas2048_collection`; Funduq `funduqoriginalatlas` and `funduqoriginalatlas_collection`). This is distinct from CCP 0.5.1 Citadel/HQ readbacks: RRGeom `structure_collection`, RRMaterial descriptors `structure` plus `structure_collection`. Thus a model/media family mismatch exists in the Castle resources relative to the working Berber buildings. It is a concrete difference, not by itself proof of the engine's rejection reason.

## Selector and lifecycle composition

Berber Ribat/Funduq RGM MSCL each declare six source parts, `garrison_part_0000` through `garrison_part_0005`, and 11 paired MSD/CNBP selectors: `sel_construct_00`, `_10`, `_20`, `_30`, `_40`, `_50`, `_60`, `_70`, `_80`, `_90`, and `sel_healthy`. The nonempty stage membership is:

| Selector | Selected part |
| --- | --- |
| `sel_construct_00` | `garrison_part_0000` |
| `sel_construct_20` | `garrison_part_0001` |
| `sel_construct_40` | `garrison_part_0002` |
| `sel_construct_60` | `garrison_part_0003` |
| `sel_construct_80` | `garrison_part_0004` |
| `sel_healthy` | `garrison_part_0005` |

The odd 10/30/50/70/90 selectors have empty membership and state predicates for the transition intervals. Predicate sets use `life_cycle_state`; each selector's state list is length-prefixed string data. The paired RGO DTBP lifecycle list has 29 names: `preview`, `targeting`, `construct_00` through `construct_95` in 5-point increments, `healthy`, `damage_1` through `damage_5`, and `ruins`.

CCP 0.5.1 Citadel/HQ readbacks instead have seven source parts (`_0000`…`_0006`) and six paired selectors. Their composition is identical on both landmarks: `sel_construct_00` selects `_0000`; `sel_construct_20` selects `_0001`, `_0004`, `_0005`, `_0006`; `sel_healthy` selects `_0000`, `_0001`, `_0004`, `_0005`, `_0006`; `sel_construct_60` is empty; `sel_damaged` selects `_0000`, `_0003`; and `sel_ruins` selects `_0002`. Here `_0002` is the dedicated ruin part and `_0003` the damage part; the healthy compound uses `_0000`, `_0001`, `_0004`–`_0006`.

Both CCP RGO DTBP lists contain the same 29 lifecycle names as Berber. Both encode RGM CNBP predicate property/value names as strings. Within the inspected RGM/RGO pairs, there is no differing lifecycle state-name set or evidence of a String-versus-Enum serialization mismatch. The measurable lifecycle difference is selector topology and part count: CCP's 7-part compound with 6 selectors (including dedicated damaged/ruin geometry) versus Berber's 6-part age progression with 11 selectors (including empty transition selectors).

## Interpretation and limits

The smallest evidence-supported static distinction for the parent repair decision is to align the Castle model resource family with its actual native owner/template, then verify the cooked quartet's descriptors and lifecycle readback. Berber's `object` / `object_collection` descriptor pairing offers a working native pattern, while CCP's accepted/retained Castle resources are currently `structure` / `structure_collection`; the parent's authorized native Castle owner-specific paired cook should determine compatibility. Selector topology is another concrete difference but does not establish that changing it will restore rendering. This audit performed no cook and no native match test; it makes no claim that either difference alone explains invisibility.

Evidence sources: latest retained Berber 0.9 SGA listing and temporary member readbacks for Ribat/Funduq; CCP 0.5.2 Test C retained readbacks of the embedded 0.5.1 Citadel/HQ model quartet. The corresponding CCP material/model static audit is in `tools/release_061/material_audit_061.md`.
