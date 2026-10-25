# Garrison 0.7.9 unit rebuild

Scope: new skirmisher bodies for Ages II-IV, water buffalo, javelin throwing/projectile meshes, and three static Ministry buffalo. Normal edition, gameplay, GUID and native animation owners remain preserved.

## Selected source and reproduction

- `art/authoring/release_079`: buffalo/r3, skirmisher2-4/r3, javelin2-4/r3, projectile2-4/r3; Ministry/r1. Ministry uses the same highest-detail buffalo form from r2; r3 makes export triangulation explicit without redesigning the form.
- `art/exports/release_079`: retained FBX, native rig definitions, 2048-pixel material maps and building parts metadata.
- `art/recipes/release_079/production-source-v1` and `production-source-v2`: immutable script snapshots. v1 owns original artwork; v2 adds explicit buffalo triangulation and final assembly.
- `tools/release_079/blender_runner.py` runs isolated authoring/review scripts with the shared native-work lock. The unsaved live Blender scene is untouched.
- Use workspace.json's **blender_python** for Garrison Python modules; its compiled modules do not load in the bundled general Python version.

Commands from the Garrison root (with the configured Blender Python):

```
python tools/release_079/test_rig_contract.py
python tools/release_079/cook_units.py <fresh-label>
python tools/release_079/decode_pilot.py <fresh-label>
python tools/release_079/cook_ministry.py ministry --label <fresh-label> --revision r1
python tools/release_079/assemble_ministry.py ministry --label <fresh-label>
```

Final assembly entrypoint: `tools/build_release_079.ps1 -CookLabel prod-v2`, consuming the already verified Ministry v1 payload. Output labels are immutable; it intentionally refuses to overwrite an existing final delivery. Historical source snapshots and failed attempts remain evidence.

## Evidence and limits

- User-confirmed pilot: both units animate; throwing weapon reversed. Final weapon geometry follows observed donor throwing/projectile axes. Corrected final weapon behavior still requires native testing.
- Donor control `output/release_079/cooks/c3`: native cook, decoded geometry and partition checks passed for cattle and Javelin Thrower.
- `prod-v1`: completed native unit cook; strict decoder caught one buffalo far-LOD triangle discrepancy. Retained as diagnostic evidence.
- `prod-v2`: explicit triangle export resolves that discrepancy. All ten assets pass exact LOD/material triangle counts; all four skinned bodies pass exact donor hierarchy/partition contracts, bind tolerances and decoded normalized weights, with no missing textures or decoder blockers.
- Four rig regression tests pass, including rejection of the actual old broken rig definitions.
- Ministry v1: native cook/readback passes; three decorations have measured minimum 0.25 model-unit pen clearance and seated bottoms. Assembly preserves native selectors, markers and nongeometry model chunks.
- Source appearance previews are Blender renders, not game screenshots. Material response, joints through native motion, weapon hand contact, two player colors, near/far LOD transitions and gameplay-scale appearance need final native acceptance.
- Final import/fresh match, save/load, multiplayer and comparative performance are unverified. Pilot acceptance does not qualify final artwork.
- No installation, publication or cleanup is authorized or performed.

The final delivery-proof.json and verification.json are the authoritative completion receipts; do not infer package success from this document alone.

## Verified delivery

ZIP: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_079\delivery\final-v1\community_civilization_pack-0.7.9.zip`

ZIP SHA-256: `7d66c6eecfb57feac8e380d6a66d53f7fae55eb32dfc9e263fc962124562ee0e`

SGA SHA-256: `f3e738f96e865f27b20d7d423bf3250b9a53dbea8b3414ecffe2d4ff040cc20d`

1,392 members: 57 changed visual members, 3 added Ministry textures, and 1,332 unchanged members byte-identical. All existing mounts preserved. All frozen gameplay/normal source files unchanged. ZIP readability, strict version and embedded SGA hash passed.
