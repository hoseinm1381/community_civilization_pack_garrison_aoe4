# Corpus pattern catalog

## Contents

1. Official game-mode analogues
2. Official supporting systems
3. Unofficial secondary examples
4. Files outside SCAR game-mode scope

## Official game-mode analogues

Select two to four complete analogues that match the requested mechanic. Read each selected file completely, including imports, lifecycle, cleanup, and helper definitions.

Paths below are relative to the supplied `Scar_learning` corpus. If that corpus is not present in the active workspace, retrieve the same official module with AoE4 MCP `find_module`/`find_usage` rather than substituting a guessed example.

| Need | Strong official analogues |
| --- | --- |
| Standard skirmish shell and options | `Official/scar/gamemodes/standard_mode.scar` |
| Minimal module | `Official/scar/gamemodes/none_mode.scar`, `Official/scar/gamemodes/sandbox_mode.scar` |
| Capture-point mode | `Official/scar/gamemodes/king_of_the_hill_mode.scar`, `Official/scar/gamemodes/combat_mode.scar` |
| Periodic environmental mode | `Official/scar/gamemodes/chaotic_climate_mode.scar`, `Official/scar/gamemodes/full_moon_mode.scar`, `Official/scar/gamemodes/seasons_feast_mode.scar` |
| Selection/network/UI mode | `Official/scar/gamemodes/chart_a_course.scar` |
| Spawned neutral enemies | `Official/scar/gamemodes/map_monsters_mode.scar` |
| Landmark elimination | `Official/scar/winconditions/conquest.scar` |
| Sacred victory | `Official/scar/winconditions/religious.scar` |
| Wonder victory | `Official/scar/winconditions/wonder.scar` |
| King/regicide | `Official/scar/winconditions/regicide.scar` |
| Player elimination and surrender | `Official/scar/winconditions/elimination.scar`, `Official/scar/winconditions/annihilation.scar`, `Official/scar/winconditions/surrender.scar` |

## Official supporting systems

| Need | Source |
| --- | --- |
| Player/team framework and delegates | `Official/scar/cardinal.scar`, `Official/scar/team.scar` |
| Game setup/options | `Official/scar/gamesetup.scar` |
| Objectives | `Official/scar/objectives.scar` |
| Network wrappers | `Official/scar/network.scar` |
| Event cues | `Official/scar/gameplay/event_cues.scar` |
| Score | `Official/scar/gameplay/score.scar` |
| Diplomacy | `Official/scar/gameplay/diplomacy.scar` |
| Vision | `Official/scar/gameplay/vision.scar` |
| Dynamic spawning | `Official/scar/gameplay/dynamic_spawning.scar` |
| Classic starts | `Official/scar/startconditions/classic_start.scar` |
| Entity/squad deployment | `Official/scar/unitentry.scar`, `Official/scar/unitexit.scar`, `Official/scar/unit_trainer.scar` |
| Mission-scale waves | `Official/scar/ai/wave_generator.scar`, `Official/scar/missionomatic/missionomatic_wave.scar` |
| Inline XAML/data context | `Official/scar/gameplay/xbox_diplomacy_menus.scar`, `Official/scar/gamemodes/chaotic_climate_mode.scar` |

The official source corpus contains 2761 SCAR/Lua function definitions. Search `scar-symbol-provenance.tsv` first, then open the defining file and its importers.

## Unofficial secondary examples

Use these only after the source-policy checks:

| Idea | Unofficial examples |
| --- | --- |
| Full custom mode plus RDO | `Age_of_noob_GM`, `Card_unit_selection`, `Korea_civ_by_hossein_and_chilly`, `Keep_win_condition` |
| Randomized tuning/gameplay | `aoe4_randomiser.scar` |
| Nomad variant | `nomad.scar` |
| Shared helper library | `global_function.scar`, `initial_setup.scar` |
| Construction/landmark hooks | `building/`, `landmark/` |
| Upgrade manipulation | `senobi/`, `senobi_new/`, `unit_sepcial_upgrades.scar` |
| Unit mechanics | `unique_unit/`, `show_kill_count_on_unit.scar` |
| Custom UI | `chinese_dynasty_ui.scar`, `seowon_v3/new_resource_ui.scar`, `ui_kill_count_korea.scar` |
| Water mechanics | `water_mechanics.scar` |

Several unofficial helpers are defined only in other unofficial files. Copying one function without its dependency graph will fail. Search the definition and all call sites before reuse.

## Files outside SCAR game-mode scope

- `Official/scar/terrainlayout/**/*.lua` is generated-map terrain code, not match-time SCAR. Do not copy terrain-layout helpers into a game-mode `.scar` file.
- `.bin` files are compiled artifacts and are not source evidence for signatures.
- ScarDoc `.htm` pages and `.api` files document engine functions and constants; prefer the `.api` signature for exact offline search.
- `.rdo` files configure game-mode discovery/options; they do not implement simulation behavior.

`corpus-manifest.md` lists and hashes all 390 supplied files so corpus coverage is auditable.
