# 0.7.7 Ministry buffalo replacement

The three decorative Worker Elephants embedded in the Economic Ministry mesh are replaced with static copies of the 0.7.6 water buffalo. Their yard centers and orientations are retained. The replacement removes 7,482 elephant faces; the building atlas's architectural half remains unchanged. New buffalo texture data occupies the former elephant half. Existing architecture, flags and gameplay remain preserved.

Baseline: `output/release_076/delivery/final-v1/community_civilization_pack.sga`, SHA256 `65b7e601df5d649be90e0dc8f7a1b28812ef5482e65cddbad1d3a83c860e56fc`.

Editable source: `art/authoring/release_077/ministry/r1/ministry.blend`. Export source: `art/exports/release_077/ministry/r1`. Review views and source receipt: `output/release_077/art`. The unrelated live Blender scene was not opened or saved; authoring used an isolated background process.

Cook: `output/release_077/cooks/ministry-v1`. Payload and native-selector proof: `output/release_077/payloads/ministry-v1/receipt.json`. The fresh supported Garrison cook and readback passed. Model geometry/materials are integrated under the existing Ministry resource key. All nongeometry model chunks, construction selectors, markers and original lifecycle RGO are exact. Temporary generated building actors are excluded. Source preflight uses local finite-coordinate/face checks; the installed Garrison Python preflight wrapper failed to import, so no successful Garrison source-preflight claim is made.

Delivery: `output/release_077/delivery/final-v1/community_civilization_pack-0.7.7.zip`, with exact hashes in `delivery-proof.json`. Final archive verification checks every member's extracted hash and all original mounts, plus Garrison identity before and after assembly. Only the three Ministry model/geometry/material members change and three private texture resources are added. Active gameplay source, normal edition and 0.7.6 rollback hashes are checked and preserved. No installation or cleanup occurs.

Rebuild from the Garrison root with `E:\Blender5.2\5.2\python\bin\python.exe -B`:

1. `tools/release_077/blender_runner.py tools/release_077/author.py` creates the immutable source/export revision. It refuses to overwrite the saved blend.
2. `tools/release_077/cook.py ministry --revision r1 --label v1` creates the isolated native cook. Use a fresh label for a new attempt.
3. `tools/release_077/assemble_media.py ministry --label v1` verifies and prepares the private payload.
4. `tools/release_077/package.py` assembles and verifies 0.7.7 from the explicit 0.7.6 baseline. It refuses an existing delivery directory.

Existing source/cook/payload/delivery directories are immutable rebuild inputs; do not rerun against populated labels. Keep the 0.7.6 ZIP for rollback. Future versions should consume the selected final 0.7.7 SGA and its hash rather than a source-only historical build.

Native acceptance remains pending: inspect all three buffalo at normal zoom, confirm Ministry construction/completion, damage/destruction/ruins/repair and flags, then production and access. These animals are decorative static mesh, not extra game entities. The 0.7.6 supervision animation remains source-only.
