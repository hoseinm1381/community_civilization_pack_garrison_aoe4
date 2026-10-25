# Subscribed SGA tuning-pack boundary

Use this reference when the only available mod artifact is a subscribed `.sga` package.

## 2026-07-17 measured snapshot

- Archives inventoried: 342, totaling 1,575,723,666 bytes.
- Readable archives: 334; unreadable v11 variants: 8.
- Compiled tuning records: 48,315 `.rgd`.
- Editable tuning XML: 0 `.xml`.
- Other relevant contents: 1,588 `.scar`, 111 terrainlayout `.lua`, 413 `.ucs`, and 451 `.bin`.
- Selective source extraction produced exactly 1,699 files: 1,588 SCAR and 111 Lua, with no missing or extra files against the inventory.

The zero-XML result applies only to the readable set. The eight unreadable archives remain unknown.

## What the package proves

The inventory can prove:

- an archive's hash, size, detected version, readable/error state, and extension histogram;
- that compiled RGD tuning content exists;
- whether editable `.xml` was packaged in the readable archive;
- the presence of SCAR, terrainlayout Lua, localization, or other support categories;
- exact source paths and bytes for selectively extracted Lua/SCAR/XML.

The package does not by itself prove:

- the original Attribute Editor XML text;
- exact tag types, inheritance, list item identities, or editor serialization order;
- whether a record was cloned, overridden, or inherited before compilation;
- current official compatibility after the package's build date;
- behavior in Content Editor, multiplayer, AI, or runtime.

## Safe workflow

1. Inventory the archive with `$extract-aoe4-sga-sources`; preserve its JSON ledger.
2. Classify the package by extension counts and paths. Do not equate zero XML with zero tuning content.
3. Extract only Lua/SCAR/XML for source review. Keep RGD as compiled evidence.
4. Obtain the editable `.aoe4mod` project when the task requires faithful modification.
5. If source is unavailable, recreate only the requested behavior in a new/current project using the Attribute Editor and current official parents. Allocate fresh identities through the editor.
6. Compare the recreated behavior, not guessed serialized text, then run build/package/runtime gates.

## Prohibited inference

Do not invent an RGD-to-XML decompiler by mapping binary strings to familiar property names, and do not copy identifiers from package paths into new XML without current editor confirmation. Binary reverse engineering can be useful as a separate research task, but it is not reliable source recovery and must not silently enter the tuning-pack workflow.

Treat subscribed UGC as secondary behavioral evidence. Re-prove schema, identifiers, and parent/property ownership against current official data before editing.
