# Garrison 0.7.6 build and rollback

The user authorized final assembly and packaging after completion of 0.7.5. This supersedes the preparation-only restriction in RELEASE_076_HANDOFF.md; that document remains the source-art preparation record.

## Selected baseline and delivery

Baseline: `output/release_075/candidates/review-v1/community_civilization_pack.sga`, SHA-256 `aaca1bd8cb3d09a44cbe091816817e5bb247944f204affa5b04e6af52f56b022`. The completed 0.7.5 ZIP and every building update are preserved. No active source or normal-edition source was modified.

Selected delivery: `output/release_076/delivery/final-v1/community_civilization_pack-0.7.6.zip`. Exact ZIP/SGA hashes are in its sibling `delivery-proof.json`. The output directory is a verified junction into the project-owned F: root. The package has not been installed or published.

Selected inputs: all ten source assets are revision r3, art cook v5, integration recipe `output/release_076/integration/v1/recipe.json`. The earlier candidate-v1 is retained as verification history; use final-v1 for delivery. The art selection, editable sources, export textures, all cook attempts and source-only buffalo action remain preserved.

## Changes and verification

- New buffalo body, three skirmisher bodies, three held javelins and three matching projectile visuals, with three geometric LODs.
- Seven existing compiled records changed: three skirmisher EBPS, three weapon records and the water buffalo EBPS. Every edit is a visual-reference CString. Reversing the edits restores the exact original bytes, including all numerical gameplay values.
- Fourteen private attachment/projectile records were cloned through the installed typed Garrison RGD serializer. Their IDs were checked against all current official Attrib records and all baseline records. No EBPS/SBPS extension was added. No SCAR was changed.
- Buffalo default/campaign presentation uses the native cattle animator with the new skin. Every serialized elephant tier visual on the buffalo is redirected to a private empty visual list, preserving tier mechanics and the Worker Elephant-derived game identity. The shared Worker Elephant attachments remain untouched.
- Age body tiers, age-up conversion selectors, tower squad consumers, held javelin bindings and private projectile references are covered. The native throwing RGO is byte-identical to the official source; native selector conditions are exact, with only the geometry target renamed to the new body mesh. Torch references remain unchanged.
- Native art cook v5 completed with 78 outputs and zero cached outputs. All ten assets decoded without blockers/missing textures. The 74 selected art files exclude generated scaffold gameplay identities.
- Integration has 95 payload files: seven changed existing records and 88 additions. All 1,288 other baseline members and every original mount remain exact. Final archive total: 1,383 members.
- Identity checks ran before and after assembly. Project GUID/runtime namespace and stable bundle key remain Garrison's own identity.
- ZIP readability, exactly one manifest, strict version 0.7.6 and embedded SGA SHA-256 are verified. Seven overlay rejection/acceptance tests pass. Media conflict checking passes against the actual selected 0.7.5 baseline.
- Independent review found no mapping/balance blocker. Its cache-provenance concern was resolved by exact-path fresh extraction from current Attrib and art archives. `integration/v1/qualification/proof.json` records the matches and archive hashes; packaging requires this proof.

These reference edits use authoritative compiled records and the installed typed serializer with exact reversal/readback checks. A new Attribute Editor source compile was not performed. Native art cooking, compiled-reference integrity, final archive verification and in-game acceptance are separate gates. No native gameplay result is claimed.

## Repeatable commands

Run from the Garrison root. The compiled Garrison codec requires **Blender's Python**; the ordinary bundled Python does not load that compiled module. No separate PYTHONPATH is needed: each helper loads the configured extension path.

```powershell
$py = 'E:\Blender5.2\5.2\python\bin\python.exe'
$base = 'output/release_075/candidates/review-v1/community_civilization_pack.sga'
$hash = 'aaca1bd8cb3d09a44cbe091816817e5bb247944f204affa5b04e6af52f56b022'
& $py -B tools/verify_workspace.py --storage-only
& $py -B tools/release_073/check_identity.py --archive $base
& $py -B tools/release_076/test_overlay.py
& $py -B tools/release_076/overlay.py --baseline $base --baseline-sha256 $hash --manifest output/release_076/manifest.json
# Use unused labels. Existing attempts are deliberately not overwritten.
& $py -B tools/release_076/integrate.py --baseline $base --baseline-sha256 $hash --label rebuild-v2
& $py -B tools/release_076/qualify_integration.py output/release_076/integration/rebuild-v2/recipe.json
& $py -B tools/release_076/package.py output/release_076/integration/rebuild-v2/recipe.json --label rebuild-v2
& $py -B tools/release_073/check_identity.py --archive output/release_076/delivery/rebuild-v2/community_civilization_pack.sga
```

Authoring/cooking commands remain in RELEASE_076_HANDOFF.md. Blender and native cooks use the existing project lock; this integration only reads already-cooked art and writes isolated overlay/delivery directories. Do not rerun a historical source-only build as a replacement for this package: it would omit compiled-only owning-resource overlays. Future versions should explicitly select this completed archive/hash and preserve or deliberately replace its integration recipe, rather than choose whichever file is newest.

## Remaining native gates and rollback

The supervision animation remains editable source-only and disabled. Native bovine construction-response motion, supervision income, skirmisher deformation/hand contact/throw-hide/player colours/LODs, save/load and multiplayer await testing. Use RELEASE_076_NATIVE_ACCEPTANCE.md. The 0.7.5 building candidate's pending visual/native acceptance is inherited, not promoted to success by this build.

Rollback is the unchanged `output/release_075/candidates/review-v1/community_civilization_pack-0.7.5.zip`. No installation or cleanup was performed. Keep editable sources, recipes, native cook/readback evidence and both release ZIPs.
