# Current editable workspace — 0.7.2

Gameplay/localization: `assets/` and `community_civilization_pack.aoe4mod`.
This is the complete normal v12 gameplay port under the existing Garrison GUID
`b7fcea91-257b-408f-b9e8-ae4d8bc402e1`. Normal source remains separately preserved.
Further Garrison work belongs here; neither edition synchronizes automatically.

Existing building/unit models, equipment, materials, lifecycle selectors and
stamps remain the exact 0.7.1 resources. All editable masters, images, exports,
recipes and packed rebuild inputs remain available at their original paths.
New normal units without existing compatible custom art keep their normal art.
No new modeling, audio, Live Reload or generated game-mode template was introduced.

## Build and verification

Run `tools/build_release_072.ps1 -Label <new-label>` from PowerShell. Use a new
lowercase alphanumeric/hyphen label of at most 16 characters for each attempt.
The supported runner refreshes official inheritance evidence, checks active
source against the verified policy, performs a real isolated Content Editor
build, assembles the exact custom native resource layer over fresh gameplay,
reads back every member/mount, then packages strict version 0.7.2.

The verified source candidate is `staging/r72/ported-source` on owned F:.
`output/release_072/source-port.json` records source fields and hashes;
`overlay-v5.json` records native attachment/identity overlays; `assembly-v5.json`
and `independent-native.json` record package readback and preservation.
The successful source burn is `native-source-v3.json`; final assembly is v5.
An assembly label is an evidence revision, not the player-facing release version.

A plain source build is incomplete visually: private attachment media, market,
monastery and retained unit identity bindings include native-only preservation
overlays. Never graft an old gameplay actor or squad wholesale. The assembler
patches render references and donor-proven equivalent identities only, and
reverting its fields must recover the exact newly compiled bytes. Normal v12
production changes take priority over an older spawner's list position.

The 0.7.2 policy is reproducible and deliberately rejects unexpected source drift.
For the next gameplay change, create an explicit new candidate/release policy
and update its gameplay/art allowlist; do not weaken historical 0.7.1 checks or
silently refresh this release's source freeze. Art changes require the normal
editable-source/export/cook qualification route before integration.

## Tests and recovery

Verified Python paths and all seven junctions remain in `workspace.json`.
`tools/release_072/regressions.py` runs the existing normal behavioral fixtures
against the Garrison candidate with only archive identity adapted in memory.
`verify_source.py` independently compares all 246 normal gameplay definitions;
`test_activation_graph.py v5` proves private squads/crews spawn custom actors;
`verify_native.py --label v5` checks native media, SCAR and PBG identities.
Use the configured Blender Python for the native RGD codec tools.

The full pre-port Garrison assets/project/workspace and normal snapshot are
hash-verified in `output/release_072/freeze`. Original 0.7.1 player files and exact
0.7.0 rollback remain unchanged. To roll back in the client, reimport 0.7.1.
Do not extract a source freeze over later user edits without comparing hashes.
Do not rerun the one-shot `port.py` or `activate.py` against future edited source.

No broad cleanup was performed. Current release diagnostics and staged native
proof remain available. Older art/input stores remain protected under STORAGE.md.

Package/import, native appearance/gameplay, save/load and multiplayer are separate
gates. The 0.7.2 build/readback does not qualify old saves or native match behavior.
