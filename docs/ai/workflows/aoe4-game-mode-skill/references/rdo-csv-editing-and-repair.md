# Safe RDO and localization CSV editing

Use this reference whenever a task reads, edits, generates, or repairs an AoE4 `.rdo` or localization `.csv`. These files are fragile cross-file contracts. Validate the current baseline before editing and validate again after every structural change.

## Contents

1. Classify the files before editing
2. Establish a clean baseline
3. Edit localization CSV safely
4. Edit RDO safely
5. Use a safe edit sequence
6. Repair common failures
7. Validate with the owning skill

## 1. Classify the files before editing

Do not treat every RDO as interchangeable.

- `assets/mod.rdo` is package metadata. Its `util::ReflectLocString` objects normally point to the mod name and description.
- `assets/scar/winconditions/*.rdo` exposes a game mode or win condition, connects it to SCAR, and may contain lobby option descriptors.
- Map, scenario, tuning, and UI RDOs can use different object types and fields. Preserve their editor-generated structure and resolve ownership before changing them.
- Locale CSV files are declared by a sibling `.locdb`. The CSV filename, locale, and schema must match that metadata.
- `.aoe4`, `cache`, compiled `.bin`, `.ucs`, and built SGA files are outputs. Never repair source by editing those files.

Inspect the project first with AoE4 MCP `inspect_project_layout`. For game-mode RDOs also use `explain_rdo_config` and `explain_rdo_options`. For localization use `explain_locdb_usage`.

## 2. Establish a clean baseline

Before editing:

1. Re-read the live RDO, `.locdb`, every declared locale CSV, project manifest, and the SCAR or data file that consumes the values.
2. Record file hashes or preserve a known-good copy outside generated/cache directories.
3. Parse the RDO and `.locdb` as XML and the localization file with a real CSV parser.
4. Run the owning skill validator. If the baseline already fails, record the pre-existing diagnostics instead of attributing them to the new edit.
5. Identify the project GUID, localization IDs in use, RDO object type, option keys, defaults, and deployed entry path.

Do not start by copying an RDO or CSV from another mod. Use another project only as secondary serialization evidence.

## 3. Edit localization CSV safely

Preserve the existing header exactly. Common schemas include:

```text
ID,Pipeline,PipelineStage,Notes,TranslationNotes,Tags,Text
```

and:

```text
ID,SourceText,TranslatedText
```

Apply these rules:

- Keep every ID an integer accepted by the project, unique within each CSV, and aligned across all declared locales.
- Never renumber existing IDs merely to make the file look sequential.
- Add the localization row before adding a new RDO or SCAR reference to it.
- Preserve the file's encoding, UTF-8 BOM state, and newline convention.
- Use a CSV-aware writer or a narrow `apply_patch`. Never split rows by counting commas.
- Quote a field containing a comma, quote, carriage return, or newline. Inside a quoted field, represent `"` as `""`.
- Preserve formatting tokens exactly, including placeholders such as `%1PLAYER%`, `%2COUNT%`, markup, escaped newlines, and leading/trailing spaces that are intentional.
- Do not let spreadsheet software convert IDs into dates, floating-point values, or scientific notation.
- Keep one logical CSV record per localization entry. Multiline text is valid only when correctly quoted.
- Update every locale required by the `.locdb`. When translation is unavailable, preserve the ID and use an explicitly approved source-language fallback rather than omitting the row.
- After editing, verify the parsed column count, duplicate IDs, empty IDs, missing text column, and locale ID drift.

A safe parser audit is:

```powershell
@'
import csv, collections, pathlib, sys
path = pathlib.Path(sys.argv[1])
with path.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.reader(handle))
header = rows[0]
bad_width = [(index + 1, len(row)) for index, row in enumerate(rows) if len(row) != len(header)]
ids = [row[0] for row in rows[1:] if row]
duplicates = [key for key, count in collections.Counter(ids).items() if count > 1]
empty = [index + 2 for index, value in enumerate(ids) if value == ""]
print({"header": header, "rows": len(rows) - 1, "bad_width": bad_width,
       "duplicates": duplicates, "empty_ids": empty})
raise SystemExit(1 if bad_width or duplicates or empty else 0)
'@ | & $python - path\to\locale.csv
```

This audit checks CSV structure only. The owning AoE4 validator must still verify IDs, locales, GUIDs, and references.

## 4. Edit RDO safely

Prefer the current AoE4 Content Editor for creating DataObjects, nested descriptors, generated IDs, and new object graphs. Direct text editing is appropriate only for a narrow change whose surrounding schema and identity are already proven.

Always preserve:

- XML well-formedness and the existing root/object hierarchy;
- `DataObject` types;
- opaque object IDs and nested descriptor identities;
- property names, serialized value types, and required wrapper objects;
- the project GUID and foreign-mod dependency GUIDs;
- unrelated options, variants, defaults, images, paths, and localization references.

Never invent, increment, or recycle opaque RDO object IDs. If an ID or nested object is corrupt, recreate that object through the Content Editor and transplant only the understood values into the editor-generated structure.

### Package mod.rdo

For `util::ReflectLocString`:

- Keep `m_locStringKey` numeric and present in every required locale CSV.
- Derive `m_modPart0` through `m_modPart3` from the project GUID's little-endian byte layout. Do not visually split the GUID into four chunks.
- Keep the same project GUID across the `.aoe4mod`, attribute manifest, custom locstrings, and RDO GUID parts.
- Use the tuning-pack validator to calculate and check the expected GUID parts.

### Game-mode and win-condition RDO

Treat these fields as code contracts:

- `m_scarWinConditionFile` must resolve to the deployed SCAR entry using the project's path and extension convention.
- Section, option, and enum-item `m_key` values become the tables and fields read by `Setup_GetWinConditionOptions`.
- Renaming a key requires updating and validating every SCAR access.
- Boolean defaults belong to the boolean descriptor.
- Enumeration defaults belong to enum items; normally exactly one item is the default.
- Every `m_feName`, `m_feDescriptionTooltip`, and `m_feSummaryName` localization reference must resolve.
- Do not copy a complete options descriptor from an old mod without re-proving every type, key, default, loc reference, and object identity.

### Map-package handoff

When a map task needs a display name, description, map entry, terrain type, or distribution RDO:

- Route creation of new editor objects and localization ownership to `$modify-aoe4-tuning-packs`.
- Keep terrainlayout Lua names, archive-qualified terrain identifiers, package entries, and RDO references synchronized.
- Do not repair a missing map data object by inventing an RDO in Lua or by renaming the Lua file alone.

## 5. Use a safe edit sequence

1. Validate the untouched baseline.
2. Add or repair localization rows and validate all locale CSVs.
3. Make the smallest RDO value change while preserving object identity.
4. Parse the RDO as XML immediately.
5. Validate RDO localization references and GUID parts.
6. For game modes, compare all RDO option keys and enum items with SCAR reads.
7. For maps, compare RDO/package entry names with the terrainlayout Lua and map data.
8. Re-read the exact edited region and inspect the diff for unrelated churn.
9. Run the owning validator, AoE4 MCP inspection, Content Editor compile/package, and the relevant runtime test as separate gates.

Do not combine CSV repair, RDO reconstruction, option redesign, and gameplay changes into one unreviewed patch.

## 6. Repair common failures

| Symptom | Diagnose | Repair |
| --- | --- | --- |
| Editor rejects or empties a CSV | Parse with Python; inspect header, unmatched quotes, row widths, encoding, duplicate/empty IDs | Restore the last parseable file, preserve its header/encoding, then reapply rows with CSV quoting |
| Text after a comma moves into another column | The text field was not quoted | Quote the entire field and double embedded quotes |
| Localization displays as a key or blank text | Check `.locdb` locale declaration, CSV filename, ID presence, GUID, and RDO/SCAR reference | Repair the missing or mismatched contract; do not create a second unrelated ID |
| Only some languages work | Compare ID sets across every declared locale | Add the missing IDs without renumbering existing entries |
| RDO is invalid XML | Use the parser's first error line; inspect unescaped `&`, quotes, truncated tags, or bad nesting | Restore the smallest valid parent object and escape values; preserve IDs |
| RDO opens but the option is absent | Inspect descriptor type, parent list, `m_key`, localization, dev-only state, and defaults | Compare with a fresh editor-generated object of the same type and reapply only known values |
| Lobby option exists but SCAR ignores it | Compare section/option/enum keys from MCP with `Setup_GetWinConditionOptions` reads | Make the keys identical and retain a guarded SCAR default |
| Wrong enum item is selected by default | Count `m_isDefaultValue` items | Set exactly the intended item as default and clear the others |
| Mod name/description is blank | Validate `m_locStringKey` and all four GUID parts | Restore the correct loc ID and calculate GUID parts from the owning project GUID |
| Editor rewrites or deletes a hand-built object | The graph, ID, type, or parent relationship is unsupported or stale | Recreate it in the current editor and migrate values into the fresh serialized object |
| Source looks fixed but the game uses old data | Inspect package timestamps/hashes and generated cache | Leave cache untouched; rebuild/package only after editable source validates |
| An RDO was copied from another mod | Check project GUID parts, foreign loc GUIDs, object IDs, paths, and dependencies | Recreate under the destination project and remove accidental cross-mod identity |

If the only known-good evidence is a compiled `.bin` or `.rgd`, do not reverse-engineer guessed editable RDO/XML. Obtain editable source or recreate the intended object from a current editor parent.

## 7. Validate with the owning skill

For a game-mode RDO:

```powershell
& $python "$gameModeSkill\scripts\validate_scar.py" path\to\wincondition.rdo
```

Then run AoE4 MCP `inspect_project_layout`, `explain_rdo_config`, and `explain_rdo_options`.

For `assets/mod.rdo`, locdb, and tuning-pack localization:

```powershell
& $python "$tuningSkill\scripts\validate_tuning_pack.py" path\to\project
```

For a generated map:

```powershell
& $python "$mapSkill\scripts\validate_map.py" path\to\map.lua --project-root path\to\project --corpus path\to\corpus
```

The map validator does not replace tuning-pack validation for editor-owned RDO/locdb data. Run both skills when the map package changes those files.

Static parsing proves structure, not editor acceptance or runtime behavior. Report Content Editor and in-game results separately.
