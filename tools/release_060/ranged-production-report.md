# 0.6.0 ranged roster authoring and source export

Six Vietnamese ranged tiers now have separate editable Blender files, tier-specific saved albedo PNGs, weighted three-LOD FBXs, authored geometry snapshots, and stock-distance/close/red/blue Blender previews. Archer II starts from the approved `archer-base-v3l-owner-tunic.blend` (SHA-256 `0092ebe4a428f12f3a0770d21cdde1a1758876ad16ecf3944ee2f432e5a6125c`); its five visible weighted outfit pieces form LOD1. Its far LODs come from its own exact Archer II donor. Every other tier starts from its exact pinned native donor in `art/recipes/release_060/ranged-roster-060.json`. No cross-tier body was reused.

Logical source/export roots are `art/authoring/release_060/ranged_roster/<slug>/` and `art/exports/release_060/ranged_roster/<slug>/<revision>/`. Receipts and six Blender review PNGs per tier are under `F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_060/qualification/ranged_roster/<slug>/<revision>/`. Each export folder has `model.fbx`, `albedo.png`, `action.json`, and `authored-snapshot.json`. `action.json` has no animation overrides or attachment replacements. Native weapon assets and actor/gameplay source were not touched.

| Tier | Revision | Authored LOD vertex/triangle counts | FBX Skin / Cluster | Tinted atlas pixels |
| --- | --- | --- | --- | ---: |
| Archer II | v1 | 1169/1484, 490/522, 187/155 | 3 / 144 | 33713 |
| Archer III | v4 | 956/1192, 495/525, 193/157 | 3 / 144 | 21594 |
| Archer IV | v4 | 921/1146, 470/514, 202/165 | 3 / 144 | 16379 |
| Crossbow III | v4 | 1164/1475, 543/567, 207/179 | 3 / 144 | 18341 |
| Crossbow IV | v4 | 1253/1499, 582/575, 264/217 | 3 / 144 | 12085 |
| Handcannon IV | v4 | 819/1198, 395/506, 185/180 | 3 / 144 | 16374 |

The atlas edit changes only the albedo image. It selects pixels covered by actual tier garment UVs and leaves the stock normal, metal, pattern/player-color, and skin LUT images untouched. LOD material names are `lod1`, `lod2`, and `lod3`, one atlas reference per material; the exporter receives `v := 1-v` copies while the editable blends and snapshots retain intended native UVs. The snapshots include actual authored positions, triangles, corner UVs/normals, skin indices/weights, and the donor 48-bone skeleton and 46-bone palette. Archer II LOD1 records its newly joined weighted outfit topology.

| Tier | Blend SHA-256 | FBX SHA-256 | Albedo SHA-256 | Snapshot SHA-256 |
| --- | --- | --- | --- | --- |
| Archer II | `b45d2c6c4704adb1a110d18bdb582ef2fb8418b8ff41e8af35ac8ea070118028` | `6f022302905f8fdd408766ade7aaa39c1dc1e6ceed8e87a0e1f8136c2487a9a2` | `f0485f6d03aa693ed0b0ec72004067e2f2ad54c27739b3d9ae7260a951359156` | `392962551de8a4a5c93b0b53fc688d708df6911efc4114fd01361fb15aa63c61` |
| Archer III | `7468ba5805028ea5c1b02d93d6582b4790cfb3d2b900de19441f15ce5a5ab18e` | `0447c888a5bf1e4c8ac5ad39a3ae22a5f9ecaab1d4dc96f59b36d003c425053a` | `393724f45a2373ff6bc183a92aba039983dfb066899c7f7069a17a1ba5d5575d` | `12644b2705def88e29532bd2156f4a553d8fb318b0f2766e0d0283d278dfce7a` |
| Archer IV | `b967fea0388cb77b04821483d46dad4004931ad2bdcb07c48b9c805fb13ebeb5` | `fc41acdbeddc96b033f9e4fcf2cc94489ec9559404178e615de025ac534ce7cb` | `7ed386032d73725505d69d28e88c23c396bab98368ccb663f3a6b7f68c117904` | `a4e235489f86a343fe8893f38d7b88abd7391cd7806a72615cabc16714830d1b` |
| Crossbow III | `6c6bebd7f5db97aa889c089d710bead8e18ec9e561ca179d43834126b0d3f9c0` | `becea484cf1bd64e776d87684ebdb237fb469a03f7b1803e10ccb0a8617ed84b` | `81d7655d8a20ff9e60c9802d8a80783e3bc29ca7039c2398649cbfec813d8e6b` | `0285c355ad8cd79d183566a411fa6937cf6df6b6779552056ebd7b3f45ecfdd6` |
| Crossbow IV | `044f39f26c68f7560cd93691bfb7d28e22e07debc2e9f0f66d00efa8f36fe183` | `a32b574b78deee06052dfe953e4e45a976c23b9fab3eba7512372125f54048f0` | `9921066d1b08eedab3bde87eb690491e85be07b18c7fd8db04a916c051f9a271` | `e90b0d2084b5a7a204023ca4dd98bb032e935b06c034fba09cc02c6da11068b5` |
| Handcannon IV | `2ef9b7dba3ab73869961784beacb0d04efcdb7298f9c62c5d9815acc9385039c` | `3febc8612035bc0fa9414a98098ae3579fcf6fa60e2b2831728d7da1350cb289` | `e480858a02abc1d872a4824915c4c75bf2e93f29b26ee644a18bbc6dd583537c` | `3ca496eaad60800bef675b53523f6fb5aca5c885edbd0e135b1a8ab31e96d007` |

**Checks run.** `common.guard()` verified the E:/F: storage map before authoring. Each Blender run used `E:/Blender5.2/blender.exe -b --python tools/release_060/ranged_roster_060.py -- --tier <slug>`; Archer II used `-b art/authoring/release_060/archer/archer-base-v3l-owner-tunic.blend --python tools/release_060/export_archer2_approved_060.py`, then resumed the owned v1 snapshot from its saved output blend. Post-export Python assertions rehashed every receipt-listed file, checked all six source blends, 48 bones, three geometry groups, corner and skin array lengths, and the unchanged approved Archer II v3l source; all passed. All six actual FBXs contain 3 `Skin` and 144 `Cluster` records. At matched Blender stock-distance size, teal clothing and red/blue owner panels remain legible. Close views retain each donor's headgear and equipment. Crossbow III's dark circular chest feature also appears in its stock donor render; this authoring pass did not create it.

The native art cook/readback and material/resource binding remain pending. These are source export and Blender appearance results only. Client import, native appearance, animation, gameplay, and multiplayer are separate gates. Earlier Archer III v1 stock-albedo preview and incomplete v2, plus v3 exports superseded by v4 snapshots, remain as diagnostic history and were not promoted.
