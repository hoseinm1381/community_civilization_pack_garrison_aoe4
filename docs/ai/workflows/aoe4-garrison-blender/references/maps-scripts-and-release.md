# Maps, scripts, project integration, and release

Use this reference for Garrison **Mod Project**, **Game Mode**, **Map Creation**, integration and cook ownership. Initial guide inspection was 2026-10-09; the installed 0.1.4 guide was reconciled on 2026-10-11 without a new build/game test. Read [Script development](script-development.md) for diagnostics, Live Reload and current-match Script Runner; [Runtime contracts](runtime-contracts.md) for native helpers; [Packaging and catalogs](packaging-and-catalog.md) for release/install/preview details.

For commands/interactions, bounded effects and AI work, local UI/fonts, surface recipes and the separate ragdoll backend, read [Scenario tools and qualification](scenario-tools.md). The 0.1.4 release extends prepared-rig duration/travel requests; it does not finalize native map/movement limits below.

## Mod Project and gameplay resources

- **Mod Project** can begin without a Blender mesh. Its Edit sections cover Contents, Blueprints, Model variants, Lights, Sounds, Crafted maps, Icons and files, and Build & Package. Use the same Asset Library and Mod across separate `.blend` files; save the source scenes and the mod project. A Garrison project lives under the chosen library's `Mods/<key>/`, not automatically beside the current `.blend`.
- **Stock blueprint field changes** can target units/entities (`ebps`), squads (`sbps`), upgrades, abilities, and weapons. The cook rebuilds a full game blueprint from the installed stock source plus the recorded recipe; the chosen Tuning Pack applies it. Search/field types are constrained by the panel, and changed stock values may be reported as drift after a game patch.
- **Derived blueprints** copy a stock recipe under a mod name. Garrison rewires references to stock blueprints copied exactly once; inspect the actual result and remaining consumers rather than assuming every relationship was remapped. A derived resource/model is inert until the match uses it. See [Blueprint and CSV recipe details](assets-and-units.md#blueprint-and-csv-recipes) for reference syntax, uniqueness and table ownership.

## Crafted versus generated maps

| Route | Documented output | Scope to verify |
|---|---|
| **Mod Project → Crafted maps** | A fixed lobby map inside the mod archive. Start with a sculptable height grid, ground texture, player-start markers (up to eight), playable size, and a scenario script. Player markers hold civilization, team, and no-randomize settings; advanced declarations include status, difficulty, and flags. | Save Map and `.blend` after editing markers. Marker name order controls player numbering; duplication copies slot settings. Terrain details expose patches, road curves, and water guides, with preservation of certain imported authored layers. Cook/readback does not prove rendered terrain, water, pathfinding, lobby roster, or multiplayer. Native blocker Paint is unfinished; elevated/moving walkable surfaces are unqualified. |
| **Blender Map Creation workspace** | A separate generated-map `.sga` from painted plains/hills/mountains/water and placed player starts. Check Map precedes Build Map. Package the built map alongside a companion tuning archive when needed. | Height, Scatter, Regions, and River are preview-only in the inspected guide, not exported into the built map. Do not equate a visible node/preview control with a shipped rule. |
| **Handwritten terrainlayout Lua or editor-authored map** | Separately owned map source and cook. | Use its own map workflow. Garrison's map selector is not a general importer for arbitrary editor source projects. A separately cooked map and companion tuning SGA need explicit roles in the package and separate lobby choices. |

An internal Crafted map and a separate generated map are different ownership choices. Decide which map the project packages. A mod icon is not automatically a minimap or overhead map preview; inspect and retain authored overview textures when changing previews.

### Crafted-map editing and preservation

**New map** creates terrain, player starts and playable boundary; playable size limits reach without resizing the donor terrain grid. Height zero is normal game ground. In the Getting Started fixture, Blender start `(X=0,Y=12,Z=0)` records game `(0,-12)`; verify the current map's conversion before placing markers from game coordinates.

**Open Map Script** uses a path relative to `project/source/scar/`, without a leading `scar/`; a new path creates a comment-only file and an existing file is opened intact. Author outside generated `garrison/`, save the script, then Save Map to record its path. This operation does not create a Game Mode.

For older scenes, **Edit Player Slots** captures saved declarations before marker edits. Teams are zero-based. Markers retain unedited native status/difficulty/flags; rename order changes numbering and duplication copies slot choices. Initialized markers do not automatically refresh from external recipe edits. **Reload Saved Slots** explicitly replaces unsaved marker slot edits with saved declarations in displayed order. Ordinary selection/Save Map retains current scene choices. Save both Map and `.blend`.

Shared `mod_project.set_crafted_map` accepts `lobby_slots`, one dictionary per start: `status` (0 open, 1 closed, 2 AI), `team`, `difficulty`, `race`, `do_not_randomize`, `flags`. Omitted fields use open-slot defaults; `lobby_slots=[]` clears declarations. Keep declaration count aligned with starts and use bitmasks only from a qualified scenario. `scripted_ai=True` supplies `has_scripted_ai`, not an AI implementation. Check actual lobby/runtime roster.

Captured maps preserve opaque layers, authored objects and known companion files so a moved project need not retain its donor. Empty Ground preserves authored material layers; explicit Ground replaces them. Terrain details capture evaluated/boundary metre-grid heights, raster masks, patches, road curves, water polygons/grid surfaces and atmosphere settings. Move water guides in Z for level; Save Map then Cook runs an isolated native editor batch. Native blocker Paint remains unfinished: normal cook refuses its recipes while preserving them. These exports do not qualify appearance/navigation; use [preview/minimap rules](packaging-and-catalog.md#preview-minimap-and-cover-are-distinct) for overview changes.

### Generated-map build transactions

**Start Blank Map** opens a separate library `Maps/untitled-map-.../` `.blend`, asking first when the current file is dirty. Terrain strokes save automatically. Use Project & Size to name it, match Player Start count, then Check Map and Build Map. Output is `build/<name>.sga` beside that map's `.blend`.

Build runs in the background and prevents a second concurrent build. Failure preserves the last successful build; failed candidate logs are in `.build-candidate-...`. Success keeps the preceding build in `.build-previous-...`. If saved rules change while cooking, the candidate cannot replace the old build: build again from the intended saved input. Package the explicitly selected built map beside its companion tuning archive. Height/Scatter/Regions/River previews still do not imply exported rules.

## Game modes, SCAR, and runtime helpers

- **Game Mode** can create an ordinary or asset-preview starter entry script, a lobby title/description, numeric/checkbox/dropdown options, preloaded resources, and generated typed option access. Asset preview places static assets for inspection; it does not place custom units or buildings. Authored SCAR belongs outside Garrison's regenerated `scar/<key>/` and `scar/garrison/` folders. Changing a template preserves an edited script; **Regenerate Script** explicitly replaces it.
- Garrison's script workspace configures a Lua language server with installed-game SCAR definitions, generated APIs and project symbols. Read [Script development](script-development.md) for refresh/check commands, trust and diagnostics. Imported resources need the generated loader and loading-phase precache; `Entity_*`, `World_*`, `Rule_*` remain stock functions.
- **Live Reload** loads authored imports at a new match's start; **0.1.4 Script Runner** separately executes a selected file again in the current prepared solo match. Neither rebuilds models, generated helpers, entry scripts or lobby options. Follow [their distinct lifecycle/error contracts](script-development.md). Turn Live Reload off and cook before distribution.
- Experimental pure Lua modules include `Garrison.scene`, `.ai`, `.physics`, `.presentation`, `.lights` and `.audio.events`; the caller supplies scenario adapters and policy. Native transport provides lossy one-way audio submission and a separate experimental synchronous RPC route. [Runtime contracts](runtime-contracts.md) explains activation, return values and limits. Neither successful send/ping nor an RPC response establishes playback or may determine gameplay rules.

## Sound and light limits

For music, looping/track transitions, independent volume controls and audio session lifecycle, read [Music and external audio](music-and-audio.md).

For native unit voice replacement or silent private speakers, use [Native voice implementation](native-voices.md). It covers the separately qualified SPD/WEM route; the Sounds controls below provide external audio.

- **Sounds** can package WAV clips and configure automatic movement, damage, construction-progress, and construction-completion cues for entity types. The documented automatic route polls from a Game Mode or Crafted map script. Scripted calls can play positional one-shots, event variants, or a looping music bed.
- Audio plays through Garrison's external Windows backend, not a native AoE4 soundbank. It needs the matching installed client/backend, an audio-bearing archive, and a started session. Logs and an audible solo match verify playback; SCAR submission alone does not.
- Authored coloured lights are effect resources whose follower/on-off behavior a scenario controls. A separate bounded native adapter switches **existing** declared Point lights after descriptor matching; read [its declaration/revision/duplicate restrictions](runtime-contracts.md#existing-point-lights). It does not create/move lights or expose continuous brightness/colour editing; the guide qualifies only a particular inventory.

## Build and delivery sequence

| Stage | Output / check |
|---|---|
| Author or change recipe | Updated `.blend`, Garrison Mod Project record, authored SCAR, images, audio, or map sources. Re-export/Build the affected asset or unit after Blender edits. |
| Cook | Latest successful `dist/<key>.sga` (or separately built map `.sga`). Inspect current result and logs; a failed cook can leave the preceding archive in place. |
| Package | Versioned ZIP, `garrison.json` with archive roles/hashes, instructions, and optional cover. Requires saved version and summary; uses the last cooked output and does not cook later edits. |
| Install and launch | Import the newest ZIP in the Garrison client, enable it, launch through its supported route. Installing/enabling does not select lobby components. |
| Native check | Select the correct Map, Tuning Pack, and/or Game Mode; verify visible geometry/materials, construction/animations, stats, scripts, and audio in a solo match. The guide does not generally qualify multiplayer. |

Garrison calls installed Content Editor/Essence conversion tools in the background for supported cooks. Model cooking may prepare a local copy of required editor tools; the ordinary editor window alone does not extend the supported model/rig pipeline. Never package local cook tools, game binaries, caches, or credentials. Preserve `.blend`, library project folder, source scripts/textures, and any separately owned Content Editor source; the installed client copy and ZIP are built outputs, not source backups.

For first-failure diagnosis of memory exhaustion, the native texture writer's `StringToPtrUTF8: Buffer too small`, process interruption and stale archives, read [Custom asset integration](asset-integration.md#diagnose-cook-failures-by-their-first-failing-stage). The 2026-10-11 fixture cooked from an unchanged short-path copy after a long-path texture failure; do not infer that cause solely from an exception message on another mod.

The current play guide retains the 0.1.3 permission to leave Essence Editor/GPUBurner open during game launch, and 0.1.2 startup sequencing/on-demand audio. Finish cook and import the new package to update the independent client-library copy. Close AoE4 and complete cleanup before replacing installed mods or launching another process; then refresh the list. A running session can hold an older prepared-tool DLL open during tool replacement. The guide reports repeated-match audio fixtures; those do not qualify every mod's repeated-match cleanup.

## Existing Content Editor mods

An existing `.aoe4mod` or Extension project is not automatically a Garrison Mod Project. Garrison can adopt a project identity or package separately cooked archives in certain workflows, but its guide makes **no general import/synchronization promise for arbitrary Content Editor edits**. Inspect the existing mod's identity, source ownership, archive roles, and references before planning an integration. Test a new asset in a separate Garrison project or map first when production integration is uncertain; only then design the exact blueprint/attachment or packaging connection to the existing mod. Do not silently overwrite its generated files or identity.

The isolated Tuareg integration retained the original Content Editor GUID and animator, compiled only private visual-list changes, and used verified archive graft/readback to preserve unrelated gameplay, voice bindings and SCAR bytes. See [Custom asset integration](asset-integration.md) for this bounded technique; it does not establish automatic project synchronization.

## Installed guide chapters

Open `guide/tools-and-pipeline.html`, `guide/new-units-and-maps.html`, `guide/make-a-map.html`, `guide/mod-project.html`, `guide/garrison-audio.html`, `guide/garrison-api.html`, `guide/garrison-modules.html`, `guide/live-reload.html`, `guide/script-runner.html`, `guide/check-your-scripts.html`, `guide/cook-and-package.html`, and `guide/mods-catalog.html` beside `blender_manifest.toml`. Also read `guide/release-0.1.4.html`, `guide/release-0.1.3.html` and `guide/scenario-contracts.html`. `print.html` duplicates the chapters; shipped CSS/JS/fonts are book infrastructure rather than additional workflow contracts.
