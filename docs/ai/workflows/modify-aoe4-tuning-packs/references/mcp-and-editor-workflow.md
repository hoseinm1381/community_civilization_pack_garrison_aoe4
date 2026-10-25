# AoE4 MCP and Attribute Editor workflow

## Use the Attribute Editor as the schema authority

Open the current official instance in the Attribute Editor before creating or changing a blueprint. Capture its category, template, parent, exact property path, serialized type, variant coverage, and referenced assets. Create instances, PBG IDs, and list entries through the editor.

Use the official `Attrib.sga` as the current archive source. Do not hand-edit or redistribute the official archive as part of a tuning pack.

## Use AoE4 MCP as supplemental official evidence

When available:

1. Run `doctor` and require the database to be ready and sanitized.
2. Use `find_base_data` with the exact unit, building, technology, ability, or upgrade name.
3. Request details when comparing official gameplay values or referenced weapons/upgrades.
4. Cross-check the returned official name/PBG ID with the current Attribute Editor instance.
5. Record MCP misses as unresolved, then check the Attribute Editor and official parent.

Example intent:

```text
find_base_data(category="units", query="unit_knight_4_eng", include_details=true)
```

The supplied live index confirmed official unit `unit_knight_4_eng` with PBG ID `166402`. A lookup for one plausible ranged-damage upgrade name returned no result, demonstrating why an MCP miss cannot reject an Attribute Editor identifier. MCP gameplay records also do not prove current `List.ItemID`, `List.ParentItemID`, hardpoint serialization, variant XML, or charge-weapon routing; confirm those in the Attribute Editor.

SCAR-oriented tools such as `check_code` do not validate Attribute Editor XML property paths, PBG identity, enums, or tuning references. Use the bundled tuning-pack validator plus Content Editor build/runtime gates.

## Safe edit loop

1. Inspect the actual project and current editable source.
2. Resolve the official owning blueprint and downstream references.
3. Find two to four close corpus analogues for serialization only.
4. Make the smallest edit in the Attribute Editor.
5. Re-read and diff the serialized XML.
6. Run `validate_tuning_pack.py`.
7. Build/package in the Content Editor.
8. Run the feature-specific runtime matrix.

If official data, editor serialization, and a handmade example disagree, preserve the current official/editor contract and explain why the handmade pattern was rejected.
