---
name: modify-aoe4-tuning-packs
description: Create, inspect, modify, debug, repair, review, and validate Age of Empires IV Attribute Editor tuning packs. Use for .aoe4mod projects, assets/attrib instance XML, EBPS/SBPS/weapons/abilities/upgrades, PBG IDs, inheritance, lists, variants, malformed or edited locdb CSVs, mod.rdo and RDO/localization failures, custom civilizations, balance changes, and Content Editor packaging. Prioritize current official Attribute Editor and official base data; use handmade mods only as secondary serialization evidence.
---

# Modify AoE4 Tuning Packs

## Objective

Produce the smallest evidence-backed tuning-pack change that survives static validation, current Content Editor build/package, and the relevant runtime matrix. Never promise crash-free behavior when an engine gate was not run.

## Scope boundaries

- `.aoe4mod`, `assets/attrib`, `assets/mod.rdo`, locdb, PBG IDs, and Attribute Editor data belong here.
- Match-time `.scar`, game-mode RDO, events, networking, and simulation/UI integration belong to `$aoe4-game-mode-skill`.
- Generated-map terrainlayout Lua belongs to `$create-aoe4-skirmish-map`.
- For mixed work, assign every file to an owner skill and validate the data/code handoff separately.

## Command root

Set `$skillRoot` to the directory containing this installed `SKILL.md` and `$python` to an absolute, verified Python interpreter path. In Codex desktop, resolve the bundled interpreter through workspace dependencies. Do not assume `py -3` or `python` is usable until its version command succeeds.

```powershell
$skillRoot = "<path-to-modify-aoe4-tuning-packs>"
$python = "<absolute-path-to-working-python.exe>"
& $python "$skillRoot\scripts\validate_tuning_pack.py" "C:\path\to\pack"
```

## Apply the evidence policy

Read [references/evidence-policy.md](references/evidence-policy.md) before planning or editing. Keep the authority order fixed:

1. Current Attribute Editor and current official `Attrib.sga`.
2. Current official AoE4 MCP base-data evidence.
3. Multiple consistent official/current analogues.
4. Handmade corpus examples as secondary evidence only.

When the input is a packaged subscribed `.sga`, read [references/subscribed-sga-packaging.md](references/subscribed-sga-packaging.md) before inferring source structure. Compiled `.rgd` entries are evidence that tuning content is packaged, but they are not editable Attribute Editor XML and must not be reverse-engineered into guessed XML.

Label unknown identifiers as unresolved. Do not convert an MCP miss or a locally unresolved official reference into a claim that it is invalid.

## Follow the workflow

### 1. Inspect the actual project

Read the requested `.aoe4mod`, direct attribute `<mod>` manifest, `assets/mod.rdo`, locdb metadata/CSVs, target instances, parents/callers that are present, and every referenced asset needed to understand the behavior. Re-read user-editable files immediately before editing.

If only built SGAs are available, inventory them first with `$extract-aoe4-sga-sources`. Distinguish editable sources, compiled tuning records, localization, map/game-mode source, and unrelated binary assets. Do not report "no tuning pack" merely because the package contains `.rgd` instead of `.xml`.

Ignore `.aoe4/`, `cache/`, `.tmp`, `~RF*.TMP`, UCS, RRTEX, BIN, and built SGA output. Do not treat generated files as source or include their churn in the review.

Read [references/project-contract.md](references/project-contract.md) when working on project structure, GUIDs, RDO, localization, packaging paths, or cross-mod references.

Read [references/rdo-csv-editing-and-repair.md](references/rdo-csv-editing-and-repair.md) before directly editing or repairing any `.csv` or `.rdo`. Use its baseline, quoting, GUID-part, object-identity, repair, and cross-file validation sequence even for a small localization change.

### 2. Define the behavior surface

Write down:

- requested gameplay behavior and exact numerical values;
- affected civilizations, units/buildings, ages, variants, modes, and locales;
- owning blueprint category and downstream references;
- new instance versus override intent;
- multiplayer, AI, save/load, and dependency risks;
- acceptance checks observable in the running game.

If the request mixes tuning data with SCAR, generated maps, UI, or art, separate the surfaces. Use the matching skill for those files and keep this workflow for the tuning pack.

### 3. Resolve official ownership and schema

Open the current official parent/instance in the Attribute Editor. Confirm category, template, parent, PBG ID, property path, XML tag type, enum/reference value, list identity, and variants.

Read [references/category-routing.md](references/category-routing.md) to trace entity, squad, weapon, ability, upgrade, army/race, UI, and AI consumers. Inspect the whole chain instead of editing the first matching number.

Use AoE4 MCP when available as supplemental official evidence. Read [references/mcp-and-editor-workflow.md](references/mcp-and-editor-workflow.md) before relying on MCP results.

### 4. Select close analogues

Search [references/instance-index.tsv](references/instance-index.tsv) for two to four complete analogues with the same category, template, feature, age/civilization role, and parent pattern. Search [references/property-path-index.tsv](references/property-path-index.tsv) for observed property paths and serialized types.

Do not load the full indexes when a targeted search is enough. Do not copy a value, PBG ID, list item ID, GUID, or parent merely because it appears in a handmade pack.

Use [references/corpus-manifest.md](references/corpus-manifest.md) only when auditing corpus coverage or locating source files. It is a complete hashed inventory, not an API specification.

### 5. Plan the minimal change

Prefer an override of the exact existing property over a cloned full blueprint. Enumerate every file and property path that must change. Explain how official evidence supports each new identifier or structure.

Stop before editing when any of these remain unconfirmed:

- owning blueprint or receiving property;
- template/category or parent path;
- new PBG ID or list identity source;
- enum, state-tree node, extension, or reference target;
- custom localization GUID/ID;
- cross-mod dependency and load order.

### 6. Edit through the Attribute Editor

Create new instances, PBG IDs, list items, and parent relationships in the current Attribute Editor. Let the editor serialize the XML. Use direct text edits only when the user requests them, the exact schema is already confirmed, and the change preserves editor-generated identity.

Read [references/instance-semantics.md](references/instance-semantics.md) before changing inheritance, `overrideParent`, lists, `List.ItemID`, `List.ParentItemID`, `List.ListAction`, variants, references, PBG IDs, or scalar types.

Keep changes narrow. Preserve unrelated variants and inherited values. Never hand-edit the official archive or generated cache.

### 7. Keep localization and GUIDs coherent

Use one project GUID across `.aoe4mod`, the attribute manifest, custom locstrings, and RDO GUID parts. Give every custom loc ID a unique numeric row in every intended locale. Keep mod name/description RDO keys present in the locale sources.

Preserve the existing CSV schema, encoding/BOM, quoting, placeholder tokens, and locale ID sets. Preserve editor-generated RDO object IDs and hierarchy. If either file is already broken, restore a parseable baseline and follow the symptom-specific repair table in [references/rdo-csv-editing-and-repair.md](references/rdo-csv-editing-and-repair.md) instead of rebuilding the file from a handmade example.

Treat `locstring mod="..."` with another pack's GUID as an error unless the user explicitly requested a foreign localization dependency and the runtime supports it. Treat other cross-mod references as declared dependency risks, not ordinary official references.

### 8. Re-read, diff, and statically validate

Re-read the serialized files and diff editable source only. Investigate broad or unrelated XML churn.

Run:

```powershell
$skillRoot = "<path-to-modify-aoe4-tuning-packs>"
& $python "$skillRoot\scripts\validate_tuning_pack.py" "C:\path\to\pack"
```

For machine-readable output:

```powershell
$skillRoot = "<path-to-modify-aoe4-tuning-packs>"
& $python "$skillRoot\scripts\validate_tuning_pack.py" "C:\path\to\pack" --json tuning-validation.json
```

Resolve every error. Review every warning. An informational unresolved-reference count means those values are absent from the local pack; verify changed references in the current official data.

Run the bundled fixture smoke test before delivery:

```powershell
& $python "$skillRoot\scripts\self_test.py"
```

Read [references/validation-and-runtime.md](references/validation-and-runtime.md) for the full validator scope and engine gates.

### 9. Build and run the engine gates

Save, build, and package with the current AoE4 Content Editor. Confirm no editor errors, missing dependencies, or wrong-GUID output. Then run the behavior-specific matrix across all affected ages, variants, civilizations, modes, and multiplayer roles.

Test actual runtime stats after requirements, technologies, auras, abilities, and modifiers. Exercise creation, research, activation, cancel, destruction, replacement, repeated-use, and long-match paths as relevant.

Do not present static XML/MCP checks as Content Editor or runtime validation.

## Handle common task types

### Change an existing stat

Trace all age/variant weapons, upgrades, requirements, and modifiers that contribute to the displayed or runtime stat. Override only the owning property. Verify the final runtime value, not just the serialized base value.

When an official weapon is shared by several civilizations but the change is civilization-specific, create an editor-allocated child weapon for the target civilization and retarget only that civilization's owning EBPS/hardpoint entry. Do not override the shared weapon globally. Mounted and siege units can carry separate regular, charge, torch, emplacement, or ability weapons; identify and preserve every entry outside the requested change.

### Add a unit, building, ability, or technology

Create it from the closest current official parent in the Attribute Editor. Trace production, UI, requirements, costs, AI, upgrades, weapons/abilities, and civilization availability. Let the editor allocate all identities.

### Create or replace a civilization package

Audit the complete army/race package, starting setup, production buildings, age progression, landmark choices, roster, technologies, AI, UI traits, water support, and variants. Replacing an official civilization can leave many official references active; test the replaced and replacement paths explicitly.

### Copy behavior between packs

Recreate the behavior under the destination project's GUID. Do not copy source PBG IDs, list item IDs, custom loc GUIDs, cache, or archive outputs blindly. Resolve every cross-mod reference either to current official data or to a declared dependency.

### Review or debug a pack

Start with validator results, then trace each failure to current official/editor evidence. Report findings by crash/data-loss/desync risk first. Separate confirmed defects, warnings, unresolved contracts, and unrun engine tests.

### Inspect a packaged subscribed mod

Use the SGA inventory for classification and provenance. Extract readable `.scar`, `.lua`, and `.xml` through `$extract-aoe4-sga-sources`, but treat `.rgd` as compiled tuning output. Safe package-level inferences include archive version, extension counts, relative RGD paths when the reader exposes them, localization presence, and whether editable XML was packaged. Unsafe inferences include exact XML tags, inherited values, list identities, parent contracts, editor GUID semantics, or a reconstructed PBG/property path from binary data.

To modify the behavior, obtain an editable `.aoe4mod` project or recreate the intended change from current official Attribute Editor parents and data. Never emit guessed XML as a decompilation result.

## Rebuild corpus indexes only when needed

When the supplied corpus changes, run:

```powershell
$skillRoot = "<path-to-modify-aoe4-tuning-packs>"
$editableSkillRoot = "<path-to-editable-skill-source>"
& $python "$skillRoot\scripts\analyze_tuning_corpus.py" "C:\path\to\Tuning_packs" `
  --markdown "$editableSkillRoot\references\corpus-manifest.md" `
  --instances "$editableSkillRoot\references\instance-index.tsv" `
  --properties "$editableSkillRoot\references\property-path-index.tsv"
```

This reads and hashes the stable corpus while excluding editor/temp state. Update an editable source copy of the skill, not the installed copy, when regenerating bundled references; then reinstall the validated copy. Review the generated timestamp, source root, summary, and parse-error counts before trusting the indexes.

This analyzer indexes editable project XML. It does not decode packaged `.rgd`. For an SGA-only corpus, preserve the extractor inventory as the packaging ledger and keep it separate from the editable-instance indexes.

## Handoff requirements

State:

- exact editable files and behaviors changed;
- official evidence and secondary analogues used;
- validator errors/warnings and how they were resolved;
- Content Editor build/package result;
- runtime configurations actually tested;
- unresolved identifiers, dependencies, assumptions, and unrun gates.
- whether evidence came from editable XML or only compiled packaged `.rgd`.

Use this evidence ledger for every delivery: `official/editor`, `MCP`, `corpus analogue`, `project source`, `unresolved contracts`, `validator result`, `Content Editor result`, and `runtime matrix`.

Never claim that a tuning pack "always works" from example matching alone. Make reliability auditable through official evidence, minimal edits, validation, engine build, and runtime testing.
