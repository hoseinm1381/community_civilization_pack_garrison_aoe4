# Validation, build, and runtime gates

## Static validation

Set `$skillRoot` to the installed skill directory, then run the bundled validator from any project directory:

```powershell
& $python "$skillRoot\scripts\validate_tuning_pack.py" "C:\path\to\pack"
& $python "$skillRoot\scripts\validate_tuning_pack.py" "C:\path\to\corpus" --json tuning-validation.json
& $python "$skillRoot\scripts\validate_tuning_pack.py" "C:\path\to\pack" --json -
```

Use only a Python interpreter whose absolute path and version were verified in the current environment.

It ignores `.aoe4`, `cache`, `.tmp`, and `~RF*.TMP` state. It checks:

- project, attribute-manifest, locdb, and RDO GUID/path consistency;
- locale files, CSV schemas, duplicate localization IDs, and locale ID drift;
- XML parsing, root/template/category structure, scalar types, and instance versions;
- one root PBG ID per instance and duplicate root PBG IDs within a pack;
- list item identity and append requirements inside each list;
- variant PBG consistency;
- custom locstring GUIDs and IDs;
- missing references that explicitly claim the current pack GUID;
- external mod dependencies and references unresolved inside the pack.

It also warns when localization text appears to contain pasted attribute XML. It cannot prove inherited list-parent identities against the official archive, validate gameplay semantics, or replace a current editor build.

Exit code `1` means errors; `--strict` also fails on warnings. An unresolved-reference summary is informational because most official parents and references are not stored in a tuning pack.

Only for an intentional, verified foreign localization dependency, pass `--allow-external-loc-guid <GUID>`. This suppresses the owning-GUID error for that GUID; it cannot verify the foreign pack's loc ID, availability, or load order.

For a supplied or newly updated corpus, use `$skillRoot\scripts\analyze_tuning_corpus.py` to rebuild auditable indexes in an editable skill source copy. Do not run it for a routine one-file edit unless the corpus itself changed.

## Review gate

Before building:

1. Reopen every edited instance in the current Attribute Editor.
2. Confirm parent, template, PBG ID, changed property paths, lists, and relevant variants.
3. Diff editable source only; exclude `.aoe4`, `cache`, and built outputs.
4. Resolve every validator error. Explain warnings and unresolved identifiers instead of silently treating them as valid.
5. Check that localization text fits the gameplay values and that every custom loc ID exists in all intended locales.

## Content Editor gate

Use the current AoE4 Content Editor to save, build, and package the tuning pack. A zero-error Python validation does not prove that Essence templates, official references, state trees, or generated archives compile.

After building, confirm:

- no Content Editor errors or missing dependencies;
- the produced archive belongs to the current project GUID;
- only expected source changes generated new output;
- the mod can be enabled and selected in a clean game profile.

## Runtime matrix

Test the smallest matrix that covers the feature, then expand for high-risk work:

- single player and multiplayer host/client;
- every affected civilization, age, and game mode;
- train/build/research/activate/cancel paths;
- save/load or reconnect if the feature persists state;
- AI use when AI references were changed;
- UI name, help text, icon, cost, requirements, hotkeys, and tech-tree visibility;
- long matches and repeated activation for stacking, leaks, or stale modifiers;
- old saves only when compatibility is a requirement.

For balance edits, verify the actual runtime stat before and after every relevant modifier and technology. For new references or cross-mod dependencies, test with only the declared dependency set enabled.

## Crash-prevention rule

Do not call a tuning pack safe because XML parses. Completion requires separate evidence for static structure, Content Editor build/package, and runtime behavior. State explicitly which gates were not run.
