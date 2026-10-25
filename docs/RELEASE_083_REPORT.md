# Community Civilization Pack Garrison 0.8.3

Credits: **hosein81 and chilly5**. Release date: 2026-10-24.

The selected delivery is `output/release_083/delivery/final-v2/community_civilization_pack-0.8.3.zip`. It rebuilds all three Vietnamese skirmisher tiers and their matched javelin/projectile visuals, with broad player-colour cloth. The accepted buffalo model and custom idle/walk remain byte-identical to 0.8.2-pilot.2. Gameplay, native skirmisher animations and the normal edition remain unchanged.

## Delivery and preservation

| Item | Verified result |
| --- | --- |
| ZIP SHA-256 | `08f7129c7f200b47f83b48a8a33bc1a46a4923c70c01b9237d4fa91da8cccd2c` |
| SGA SHA-256 | `85abef75f6c0ea5ccb1236140e97895232b061fbf1e50db81d7edc90252ac034` |
| Owning baseline SGA SHA-256 | `9dc759f9a34d6500a771c436a7a48e0fe1cf362b01b2e5084b68c347a310cca4` |
| Project GUID | `b7fcea91-257b-408f-b9e8-ae4d8bc402e1` |
| Final archive namespace | `b7fcea91257b408fb9e8ae4d8bc402e1` |
| Bundle key | `community_civilization_pack` |
| Archive members | 1,421; 48 existing media members changed; zero additions/deletions |
| Untouched members | 1,373 byte-identical; every original mount preserved |
| Source preservation | 504 frozen normal-edition files and 227 protected prior art/export files rehashed unchanged |

Only private `art/scenario/garrison/cc076/{skirmisher,javelin,projectile}{2,3,4}` mesh, material and texture members may change. All compiled gameplay, SCAR, abilities, identity, animation libraries and other visuals retain the baseline bytes. Native actor/control chunks including BANA, MSBP and body SKLN are retained; fresh SKMS body and STMS static mesh chunks are preserved from the cook.

## Artwork and offline evidence

| Body | Near / middle / far triangles | Owner-mask surface fraction near / middle / far |
| --- | --- | --- |
| Age II: layered cloth and headwrap | 7,116 / 3,700 / 1,921 | 38.04% / 38.14% / 38.50% |
| Age III: padded reinforcement | 7,460 / 3,878 / 2,013 | 34.52% / 34.63% / 34.90% |
| Age IV: flat overlapping armour | 10,200 / 5,304 / 2,753 | 27.68% / 28.08% / 28.56% |

The masks cover cloth independently of skin, armour and weapons. Fractions are mesh-surface measurements from native decoded UVs, not visible screen coverage. Red/yellow source previews and six orthographic views for every LOD are under `output/release_083/qa-v6`. These simulate owner colour and are not native game screenshots.

All nine native-decoded model families match the source triangle counts and materials, with no decoder blockers or missing textures. Body skeleton order, hierarchy, partitions and lower-LOD weights pass. Native bind-transform blocks are byte-identical to the working baseline. Maximum source/native vertex quantization distance is 0.001397 m. Actual decoded mask pixels agree after the paired DDS-row/UV-V convention is accounted for.

Inherited idle, walk, throw, reload, stop and death were sampled on all three source LODs. Mesh vertices remain finite and within the bounded extent. The correctly transformed weapon grip stays within 0.053376 m of a weighted hand vertex for the five held states. Death retains deformation checks; its released/stowed weapon does not have an in-hand contact requirement. Native visibility and transitions still need testing.

Javelins retain their throwing tip toward -Z; projectiles retain the separate -Y flight axis. Decoded geometry bounds and grip surfaces are measured independently. The held-state donor, native attachment socket and selector/control resources are unchanged. This does not establish in-game release timing or flight appearance.

## Build and reproducibility

Selected editable sources: `art/authoring/release_083/<family>/r12/model.blend`; retained FBX/PNG/rig inputs: `art/exports/release_083/<family>/r12`. Selection and hash-pinned integration recipe: `art/recipes/release_083`.

Native art cook v3 completed using Garrison's prepared Essence editor. Its actual completion log records the intermediate SGA copied to the final output, followed by verified listing and extraction. This is a real native **art** cook; no new gameplay-source Content Editor burn was needed or claimed. Logs and failed attempts remain under `output/release_083/cooks` and owned `staging/r83`.

Commands from the Garrison root, with configured Blender Python `E:/Blender5.2/5.2/python/bin/python.exe`:

```powershell
& tools/build_release_083.ps1 -Action Verify
& 'E:/Blender5.2/5.2/python/bin/python.exe' -B tools/release_083/test_policy.py
```

The following commands produced the selected cook, QA, assembly and final archive decode. Their immutable destinations intentionally reject overwriting; for another cook/QA use new labels. A new delivery requires a new explicitly selected destination rather than replacing this release.

```powershell
& 'E:/Blender5.2/5.2/python/bin/python.exe' -B tools/release_083/cook.py v3
& 'E:/Blender5.2/5.2/python/bin/python.exe' -B tools/release_083/decode.py v3
& 'E:/Blender5.2/blender.exe' -b --python-exit-code 1 --python tools/release_083/qa.py -- v3 qa-v6
& 'E:/Blender5.2/5.2/python/bin/python.exe' -B tools/release_083/package.py v3
& 'E:/Blender5.2/5.2/python/bin/python.exe' -B tools/release_083/decode.py v3 --final
```

Evidence: `source-qa.json`, `cooks/v3/receipt.json`, `delivery/final-v2/verification.json`, `delivery/final-v2/native-decode/decoded-proof.json`, `final-recheck.json` and `RELEASE_083_PROGRESS.md`. Final verification freshly extracts the owning archive and rechecks every member hash/mount, preserved sources, ZIP CRC, exact metadata and embedded SGA digest. Three allowlist regression tests pass.

The independent review caught an initial assembly policy that preserved SKMS but incorrectly restored static STMS geometry metadata. The rejected `delivery/final-v1` remains diagnostic and must not be imported. Final-v2 preserves both fresh geometry chunk types and has a separate successful final native decode of all nine families. All non-geometry actor data remains exact.

## Native acceptance and rollback

Import final-v2 manually into Garrison, enable one version, and select its tuning pack and Vietnam game mode. Restart the game and use a fresh match. Test ages/upgrades, ordinary and tower training, two player colours, near/far LODs, idle/movement/turn/stop, throw/grip/release/projectile flight and death. Check that other units and the accepted buffalo remain unchanged.

Client import, new skirmisher native appearance, save/load and multiplayer are unverified. The user's prior acceptance establishes the buffalo idle/walk result only; byte preservation carries those assets forward without broadening that acceptance.

0.8.1 and both 0.8.2 pilot deliveries remain available for rollback. No installation, publication, deletion or storage reclamation was performed. The unrelated live Blender scene was not modified.
