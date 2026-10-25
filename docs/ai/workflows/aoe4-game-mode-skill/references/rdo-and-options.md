# RDO and option contract

## Contents

1. Role of the RDO
2. Required cross-file checks
3. SCAR option shapes
4. Localization and tuning references
5. Validation workflow

## Role of the RDO

A game-mode `.rdo` is XML-like DataWarehouse data. It exposes a WinCondition to the front end and connects it to SCAR. Create or edit it through the AoE4 Content Editor when possible; generated object IDs and nested descriptors are not safe to invent.

Important properties seen in the corpus include:

- `m_scarWinConditionFile`: deployed SCAR entry path without the `.scar` extension.
- `m_name`: internal WinCondition name.
- `m_feName`, `m_feDescriptionTooltip`, and image/icon properties: front-end presentation.
- `m_tuningModGUID`: tuning-pack dependency when used.
- `m_optionsUIDescriptor`: option sections and descriptors.
- `m_key`: keys that become fields in the table populated by `Setup_GetWinConditionOptions`.

The supplied RDO files are unofficial examples. Use them to understand shape, then confirm fields with AoE4 MCP `explain_rdo_config` and `explain_rdo_options` or with a Content Editor export.

## Required cross-file checks

Before accepting an RDO/SCAR pair:

1. Resolve `m_scarWinConditionFile` to the deployed SCAR file and confirm case/path conventions.
2. Confirm `m_name`, module name, file name, localization, and package entry all refer to the intended mode.
3. Extract every RDO `m_key` and every SCAR option access.
4. Reject SCAR keys absent from the RDO unless they belong to an imported standard section that is proven present.
5. Reject duplicate keys within one descriptor scope.
6. Confirm defaults produce a valid match without optional UI interaction.
7. Confirm enum values used by SCAR exist in the RDO descriptor.

## SCAR option shapes

Populate the table during game setup:

```lua
function ExampleMode_OnGameSetup()
	Setup_GetWinConditionOptions(_example_mode.options)
end
```

Boolean options are read directly after guarding the section:

```lua
local enabled = _example_mode.options.section_rules
	and _example_mode.options.section_rules.option_example
```

Enumeration options use the selected `enum_value` and declared `enum_items`:

```lua
local speed = _example_mode.options.section_starting_conditions
	and _example_mode.options.section_starting_conditions.option_speed

if speed and speed.enum_value == speed.enum_items.option_speed_2x then
	-- Apply the verified 2x behavior.
end
```

Never assume a section exists merely because an unofficial RDO has it. Keep a safe default when the section, option, or enum item is absent.

## Localization and tuning references

- Player-facing strings should resolve through locdb rather than hard-coded text.
- Validate every `$guid:id` or numeric loc reference against the project locdb.
- Confirm the RDO tuning GUID matches the package that supplies referenced blueprints and upgrades.
- Do not use a blueprint name from SCAR until official base data or the current tuning pack proves it exists.

## Validation workflow

1. Run `& $python "$skillRoot\scripts\validate_scar.py" mode.rdo` to catch XML, entry, name, and duplicate-key problems.
   Treat duplicate-key warnings as conservative: the static validator scans the file globally, while correctness depends on descriptor scope.
2. Run AoE4 MCP `inspect_project_layout` and `explain_rdo_config` on the project.
3. Run `explain_rdo_options` and compare the returned keys with SCAR accesses.
4. Validate locdb references and tuning dependencies.
5. Re-export or inspect the RDO in Content Editor.
6. Launch a match with defaults and each nontrivial option branch.
