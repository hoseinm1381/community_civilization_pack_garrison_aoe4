# Project, GUID, and localization contract

## Editable project structure

Treat these as source:

```text
<pack>/
  <pack>.aoe4mod
  assets/
    attrib/<pack>.xml
    attrib/instances/<category>/.../*.xml
    locdb/<pack>.locdb
    locdb/<pack>_<locale>.csv
    mod.rdo
    mod.png
    ui/...                       # optional source assets
```

Treat `.aoe4/`, `cache/`, `*.ucs`, `*.rrtex`, `*.bin`, and built `*.sga` files as editor/build output. Do not hand-edit them. Do not copy a different pack's cache into a project.

## Project manifest

The `.aoe4mod` XML normally declares:

- `DataGenericPath`: usually `assets`.
- `DataIntermediatePath`: usually `cache`.
- `ID`: the hyphenated project GUID.
- `LocDBPath`: relative to `DataGenericPath`, such as `locdb\my_pack.locdb`.
- `Type`: `Extension` for a tuning pack.

Resolve paths from the manifest; do not assume the filename is identical to the folder name.

## Attribute manifest

The direct XML file under `assets/attrib/` has a `<mod>` root. Its normalized `guid` must equal the `.aoe4mod` ID. Its `locdb_path` is relative to the attribute manifest directory and must resolve to the same locdb as the project manifest. Tuning packs normally set `override_instances="True"`.

Use one project GUID consistently. Do not reuse another mod's GUID when cloning source.

## RDO localization GUID parts

`assets/mod.rdo` represents a `util::ReflectLocString` GUID as four unsigned 32-bit fields named `m_modPart0` through `m_modPart3`. They come from the GUID's little-endian byte layout, grouped into four little-endian integers. Do not calculate them by visually splitting the normalized GUID.

Run `& $python "$skillRoot\scripts\validate_tuning_pack.py"`; it derives and checks the parts. Every `m_locStringKey` used for the mod name or description must exist in the locale CSV source.

## Locdb and locale CSVs

The `.locdb` XML declares each locale using `<Locale><Name>...</Name></Locale>`. Each declared locale needs a sibling `<locdb-stem>_<locale>.csv`.

The source locale commonly uses:

```text
ID,Pipeline,PipelineStage,Notes,TranslationNotes,Tags,Text
```

Translated locales may instead use:

```text
ID,SourceText,TranslatedText
```

Keep IDs numeric, unique within each file, and aligned across locales. A `<locstring mod="..." value="N">` is custom only when `mod` is present; its normalized GUID must be the owning pack GUID and `N` must exist in the locale CSVs. Official locstrings normally omit `mod`.

An `instance_reference mod="..."` can intentionally target another mod, but it creates a dependency and load-order contract. Verify that contract explicitly.
