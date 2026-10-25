# Vietnam HUD 0.7.10

This Garrison-only payload adds an original gold winding Dai Viet dragon on deep
red to Vietnam player rows, a living Water Buffalo/current native cap widget, and
a small steady buffalo supervision marker. Normal edition is untouched.

## Official contracts and preservation

Current official UI.sga supplies the three source XAML files, frozen under
`output/release_0710/hud/official`. CardinalHUDPage imports
`../../Resources/HUDResources.xaml` and
`/WPFGUI;component/HUD/Controls/PlayerScores.xaml`; these establish the resource
paths. PlayerScores uses row `RaceIcon`. Its native image remains intact, with
the Vietnam image layered over it only for that row's `ScarModel[vietnam_hud]`.

The original ChineseImperialOfficers template, click behavior, population values,
and Chinese/HistoricChinese/Song visibility expression are preserved. Only its
parent ContentTemplate selects VietnamBuffaloCounter for a Vietnam player.
`UI_SetPlayerDataContext(player.id, player.scarModel)` follows official
chaotic_climate_mode.scar:283 and chart_a_course.scar:272, preserving unrelated
keys. `UI_CreateCommand` is defined by official ui.scar:796 and used by
current_dynasty_ui.scar; presentation imports ui.scar explicitly.

The count enumerates spawned, living owned squads of the exact private buffalo
blueprint; queued units, other unit blueprints and decorations do not qualify.
`Player_GetCurrentPopulationCap(player, CT_Medic)` reads the current native cap,
not a fixed limit. Spawned-only traversal avoids unsafe stale/despawned handles.
Squad ownership uses numeric Player_GetID comparisons. Selection sorts numeric
Squad_GetID values, rechecks fresh ownership/liveness on every click and wraps.
Only Misc_ClearSelection/Misc_SelectSquad are called; zero is a no-op. UI replay
and observer bindings disable clicks; callback also rejects replay, missing,
nonhuman, defeated and non-Vietnam local players.

Refresh uses the existing 0.5-second Dynasty UI rule, with no new rules/events.
Commands are cached until restore/cleanup. Local-player changes reset cycling;
restore recreates presentation context; game over clears keys and command.
The supervision patch changes only its template and comment, retaining the
existing active/owner/replay checks and cleanup paths. Its new 20-pixel template
contains no animation and cannot intercept clicks.

## Payload and reproduction

Installed Garrison 0.1.4 guide `new-units-and-maps.html`, Icons and loose files,
documents HUD replacement at `files/ui/hud/pages/cardinalhudpage.xaml`. The live
compiled `garrison_shared.mod_project.files_folder(root)` returns
`root/project/source/files`. A narrowly scoped `_loose_files` probe returned
the original PNG bytes under `Contribution.members[ui/images/vietnam_0710/dai_viet_dragon.png]`;
see `output/release_0710/hud/loose-contract.json`. This establishes transport only,
not image-loader support. The supported `ui_assets.add_image` probe instead wrote
PNG to `project/source/ui/icons/garrison/<key>/presentation/` and returned a
`.png` WPFGUI reference (`ui-import-contract.json`). Its generated burn project,
and our active native burn project, route `ui/icons/**` and `ui/images/**` through
`RRTextureBurner` with `UI Textures` parameters. Official UIArt.sga stores native
`.rrtex` resources even though XAML uses `.png` URIs. Accordingly, the final
payload requires the two freshly compiled `.rrtex` companions; it does not rely
on raw PNG runtime loading. UI XAML and compiled textures belong in SGA `data`
members, not ZIP siblings. No extra archive or identity change.

Production paths (source prefix `assets/` is removed):

- `ui/hud/controls/playerscores.xaml`
- `ui/hud/pages/cardinalhudpage.xaml`
- `ui/resources/hudresources.xaml`
- `ui/images/vietnam_0710/dai_viet_dragon.rrtex`
- `ui/images/vietnam_0710/buffalo.rrtex`
- `scar/vietnam/presentation.scar`
- `scar/vietnam/paddy_wood.scar`
- `scar/winconditions/vietnammode.scar`

Editable SVGs live in `art/authoring/release_0710/hud`; PNG native burner inputs
remain in `assets/ui/images/vietnam_0710`. SVG masters are outside the native
burner's wildcard input tree and are preservation inputs, not runtime files.
`hud_prepare.py` rereads the official archive and refuses changed frozen donors.
Run it with workspace `blender_python`. `hud_render.cjs` uses bundled Node/sharp
to rasterize the SVGs. `hud_receipt.py` uses workspace Python to run
`tests/test_hud_0710.py` and records exact paths/hashes for package assembly.
It requires `--native-receipt <hideout/compile-VERSION.json>`, validates completed
compile evidence/archive hashes and matching staged PNG input hashes, and refuses
delivery if either native texture readback is absent. Shared source compilation
provides the textures; no parallel or redundant HUD cook is necessary.
The 32x18 flag preview was inspected at scoreboard size; the gold winding body,
horned head and deep-red field remain distinct.

## Verification and remaining native gates

Twelve focused tests pass: count filtering, dynamic cap, context preservation,
stable wrap, death between clicks, zero no-op, replay/invalid player/China/defeat,
local switch, restore, cleanup, XML parse, exact China template and native
visibility preservation, and native texture-input/master placement. MCP check_code reports no low-confidence APIs or
missing localization; its three unknown calls are functions defined in this
same source (`collect`, `VietnamPresentation_Start`, `VietnamPresentation_Update`).

Source/static and native texture compile/readback are separate gates. The final
receipt supplies texture compile evidence; native XAML loading, texture rendering, resource lookup,
observer/replay switching, current HUD scales, selection without orders,
active supervision, save/load and multiplayer have not been exercised.
The counter targets keyboard/mouse CardinalHUDPage; Xbox layout is not changed.
Because three complete official files are overridden, revisit them after game
updates. Runtime acceptance must include China and Vietnam in one match, every
player row, zero/one/many buffalo, changing cap, death/transfer during cycling,
local-player switching, restore, replay and observer mode.

Native source compile `hideout/compile-v1.json` completed with 377 validated
instances and produced both required textures. Their source PNG hashes match
the active authoring inputs. Both native files parse through Garrison's Chunky
reader. Installed `rrtex_decoder.decode_rrtex(validate_stream=True)` cannot export
their native UI internal format 28; both exact failures are retained in
`hud/native-texture-decoding.json`. This decoder limitation does not replace or
invalidate native completed-burn/readback evidence; pixel-level native texture
preview and in-game image rendering remain unverified.
