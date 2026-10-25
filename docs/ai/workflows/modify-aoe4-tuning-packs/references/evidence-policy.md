# Evidence policy

## Authority order

Use evidence in this order:

1. The current AoE4 Attribute Editor and the current official `Attrib.sga` shipped with the game.
2. Current official base-data records returned by the AoE4 MCP.
3. Multiple consistent official/current examples for the same category, template, property path, and variant.
4. Handmade packs in the supplied corpus as implementation clues only.

Do not let a handmade pack override current official evidence. A handmade file can demonstrate XML serialization, but it can also contain stale parents, copied GUIDs, duplicate IDs, broken references, or values that only worked in an older game build.

## Evidence labels

Classify every important identifier or edit before relying on it:

- **Confirmed official**: visible in the current Attribute Editor, official archive, or an exact current official base-data record.
- **Corroborated**: appears consistently in multiple relevant examples and agrees with official structure.
- **Handmade-only**: appears in a mod but lacks current official confirmation.
- **Unresolved**: cannot be resolved in the pack or current official evidence. Preserve it only when the task requires it and call out the runtime gate.

An MCP miss is not proof that an identifier is invalid. The base-data index is useful but incomplete for some categories and upgrade names. Recheck the Attribute Editor and current parent instance.

## Supplied corpus

The stable scan excludes `.aoe4`, `.tmp`, and `~RF*.TMP` editor state. It covers 6,627 files, 504,876,508 bytes, 3,218,072 text lines, and 4,422 editable attribute instances with no XML or CSV parse failures.

- `official/Attrib.sga` is SGA version 10 with archive name `CardinalAttributes`.
- Handmade output archives are SGA version 11 and normally use the normalized project GUID as their archive name.
- Read [corpus-manifest.md](corpus-manifest.md) for the complete hashed file inventory.
- Search [instance-index.tsv](instance-index.tsv) for exact instance/category/parent/PBG analogues.
- Search [property-path-index.tsv](property-path-index.tsv) for property paths observed in the corpus.

The indexes prove what the corpus contains; they do not turn handmade values into official APIs.

The indexes contain handmade instance XML plus metadata for the official archive; they do not contain an extracted, current official XML tree. If the current Attribute Editor/archive cannot be inspected, preserve existing identifiers as unresolved, avoid structural invention, and make the missing editor/build gate explicit.

## Packaged subscribed archives

The separate 2026-07-17 subscribed-mod inventory covered 342 SGAs. Of 334 readable archives, the archive-wide histogram contained 48,315 `.rgd` files and zero `.xml` files. It also contained 1,588 `.scar`, 111 `.lua`, 413 `.ucs`, and 451 `.bin` files. Eight v11 archives were unreadable by the verified reader and remain unknown rather than empty.

This packaging evidence establishes that compiled tuning data can be present without editable XML. A `.rgd` count or path is useful for classifying a package, but it does not prove the current XML schema, property type, inheritance, list identity, or correct editor serialization. Do not decode binary RGD into speculative XML. Read [subscribed-sga-packaging.md](subscribed-sga-packaging.md) for the safe handoff.

## Decision rule

Prefer the smallest change that can be produced by the current Attribute Editor. If an edit requires inventing a property, template, enum, PBG ID, list identity, or parent path, stop and obtain official/current evidence first.
