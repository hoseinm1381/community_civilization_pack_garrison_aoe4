# Castle 0.7.5 art handoff

Completed source/export refinement only. No cook, package, native game, or dynamic owner-colour acceptance is claimed.

Run `E:\Blender5.2\blender.exe --background --factory-startup --python tools/release_075/castle_art/upgrade.py -- citadel` and then `-- hq` from the Garrison root, while holding the project Blender slot. Never use this script against the live unsaved file. `baseline_recipe.py` is a release-owned copy of the old recipe with only its root lookup adjusted; the new runner overrides its specific behaviors. Historical scripts and blends remain unchanged and their hashes are checked at the end.

## Outputs and contracts

- `art/authoring/release_075/citadel/imperial_citadel.blend`, `art/authoring/release_075/hq/resistance_hq.blend`: joined runtime source, selected healthy state. Their `_components.blend` siblings preserve separately editable pieces; `baseline.blend` is an exact copy of the historical source. Baseline and alternate-state geometry remains hidden in the new scenes for inspection.
- `art/exports/release_075/{citadel,hq}`: required six inputs are `model.fbx`, `building.json`, `albedo.png`, `normal.png`, `roughness.png`, `metalness.png`. The extra `pattern.png` is carried source evidence only, not a claim of native dynamic colour. Root owns the native attachment pilot.
- `output/release_075/art/{citadel,hq}/receipt.json`: old-source hashes, native-part order, construction stage sequence, triangle counts, lifecycle geometry digests, exact export hashes, measured contacts and clearances.
- `preflight.json`: Garrison model preflight passed, zero findings, four lifecycle objects each. Before/after/ruins/heavy_damage directories contain six orthographic and near/gameplay PBR views. `orthographic-review.png` is a six-view inspection sheet.

Part sequence remains foundation, healthy chunk 0, ruins, damage, healthy chunks 1–3; first stages `[0,20,0,80,20,20,20]`. No actor transform, RGO, footprint, marker, selector, native resource, gameplay source or release metadata changed. Ruin/damage meshes are loaded from the historical blend, and their exact vertex/topology digests match. They use the refreshed shared atlas, so texture bytes intentionally differ.

## Decisions and criticism

Citadel: retained gate/hall/gallery silhouette and 2x source Z convention. Changed the broad red terrace to warm stone, galleries to plaster/stone walls, reduced saturation and roof repetition, oriented timber grain along the long axis, thickened return walls inward from .22m to .35m, and added measured .08m coping and seated piers. Healthy triangles fell from 90,894 to 64,774. All original access clearances were retained; new coping underside equals wall top 1.20m before Z scaling, pier bottoms overlap terrace by .01m intentionally. Final six-side inspection shows closed perimeter and unchanged open central approaches. Remaining limitation: masonry texture scale and roof repetition are improved but still procedural; end galleries remain symmetrical. This is an improvement candidate, not a substantiated 9/10 asset.

HQ: replaced ceramic crown/tile geometry with closed, connected layered reed roof skins anchored to the old roof profile; added restrained grain, lighter command-hall roofing relative to support shelters, and small deterministic stake height/diameter differences. Preserved compound locations and gate opening. Healthy triangles fell from 92,234 to 20,346. First panel prototype had visible overlap striping; replacing disconnected overlaps with connected watertight skins fixed the visible defect. Final six-side views show coherent roofs, supports and gate access. Remaining limitation: thatch is clearly different from ceramic but still reads as controlled reed matting rather than fully organic bundles; palisade spacing and post silhouettes remain regular. Supplies retain prior organization; no arbitrary clutter was added. This is not a substantiated 9/10 asset.

## Reference boundary

Root supplied verified Thang Long archaeology/architecture sources: https://hoangthanhthanglong.com/di-tich/di-tich-khao-co-hoc/?lang=en and https://hoangthanhthanglong.vn/hoang-thanh-thang-long/kien-truc/ . Brick courts, stone column foundations, timber halls and ceramic roofs inform the Citadel interpretation. This is not an archaeological reconstruction of a known medieval superstructure. HQ remains an interpretive practical timber/bamboo compound, not a documented excavated plan.

Historical official Chinese Great Wall/HQ decoded-model pointers remain context only. The old 50%-over-stock budget is not used as qualification. Geometry is below the prior custom assets; refreshed complete simultaneously visible official-compound comparison is still root-owned and required before a final quality/performance claim. Native material readability, two player colours, construction, damage, ruins and repair remain pending final candidate testing.
