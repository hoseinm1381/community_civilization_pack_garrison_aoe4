# 0.7.8 visibility and Ministry placement repair

The 0.7.6 integration added fourteen private attachment/projectile RGDs with `set-members --alias data`. Existing tuning records were mounted as `attrib`, but these new records remained on `data` through 0.7.7. The private buffalo/skirmisher visual references therefore pointed at records outside the tuning mount. Archive readability, correct record bytes and reference-name existence did not check runtime mount ownership. This is a confirmed packaging defect consistent with the invisible units reported by the user. Native visibility after correction still requires a fresh-match retest.

The 0.7.8 packager reconstructs the exact selected 0.7.7 member bytes from the verified 0.7.5 archive, adds those fourteen tuning records under `attrib`, then overlays all retained 0.7.6/0.7.7 art and the new Ministry geometry. It checks every final member hash against 0.7.7 plus the narrow Ministry payload, checks identity before/after assembly, and permits only the fourteen intentional mount changes. Every final `attrib/` member must have TOC alias `attrib`. `delivery/final-v1/mount-regression.json` records the actual failing 0.7.7 case and the required mount.

The Ministry's static buffalo were placed using a donor mesh origin that was offset from its full bounds. The 0.7.8 source recenters each complete rotated buffalo inside its pen and seats its lowest geometry at yard height. All three full bounding boxes must clear each fence by at least 0.25 model units. The editable objects record `pen_clearance_verified`. Architectural geometry and the architectural half of the texture atlas are preserved; construction selectors, native markers and RGO lifecycle owner are preserved exactly by the existing typed integration checks.

Inputs and commands, from the Garrison root, using `E:\Blender5.2\5.2\python\bin\python.exe -B`:

- `tools/release_078/blender_runner.py tools/release_078/author.py`: immutable `art/authoring/release_078/ministry/r1/ministry.blend`, exports and source views under `output/release_078/art`.
- `tools/release_078/cook.py ministry --revision r1 --label v1`: isolated supported native cook/readback under `output/release_078/cooks/ministry-v1`.
- `tools/release_078/assemble_media.py ministry --label v1`: native-selector-preserving model/material payload under `output/release_078/payloads/ministry-v1`.
- `tools/release_078/package.py`: fresh final SGA and strict 0.7.8 ZIP, full member/mount readback, identity and ZIP checks. Exact delivery hashes are in `output/release_078/delivery/final-v1/delivery-proof.json`.

Existing revision, cook and delivery paths are immutable and refuse overwrites. Preserve 0.7.7 and the earlier sources. Normal-edition and active gameplay source hashes are checked. No installation, publication or cleanup is performed. The separate custom supervision clip remains source-only.

Native acceptance: import 0.7.8, start a fresh match and check starting buffalo visibility, movement and rice-paddy supervision. Train and upgrade normal/tower skirmishers through Ages II–IV, test throwing, projectiles, torch switching, death, player colours and LODs. Build the Ministry and view all three animals from multiple sides for fence/bench clearance and ground contact; test construction, destruction/repair and production. Save/load and multiplayer remain separate tests. A successful package is not native acceptance.
