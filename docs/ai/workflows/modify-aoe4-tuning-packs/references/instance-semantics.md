# Attribute instance semantics

## Root identity and inheritance

Editable instance XML normally has this shape:

```xml
<instance version="6" template="weapon">
  <uniqueid name="pbgid" value="1073741903" />
  <instance_reference name="parent_pbg" value="weapon\races\common\melee\weapon_spearman_2" />
  ...
</instance>
```

The supplied corpus uses instance versions `4` and `6`. Every one of its 4,422 instances has exactly one direct root `pbgid`. The directory immediately below `instances/` must agree with the template; a nested template such as `ai\ai_economy` belongs under category `ai`.

Do not invent a PBG ID. Let the Attribute Editor create new instances and IDs. Within one pack, root PBG IDs must be unique. An official-sized ID is not automatically wrong: an override can retain official identity. Determine intent from how the instance was created.

`parent_pbg` is optional for some templates and can be empty. Do not add one merely because other categories use it. When a parent exists, verify it against the current official source and preserve its category-qualified path.

## Overrides

`overrideParent="True"` marks a serialized override of inherited data. Prefer changing only the required properties in the Attribute Editor. Avoid copying a whole parent instance: broad copies freeze unrelated official values and make patches brittle after game updates.

Keep scalar types and exact spelling:

- `bool`: `True` or `False`.
- `int`, `uniqueid`, and `locstring`: decimal integers.
- `float`: finite decimal/scientific numbers.
- `colour`: a decimal value or the Attribute Editor's `*` sentinel.
- `enum`, `file`, `string`, references, and state-tree nodes: values confirmed for the exact property path.

Never guess enum names, extension templates, state-tree nodes, or modifier property paths from their English meaning.

## Lists and item identity

List entries use signed 32-bit `List.ItemID` values. An inherited item often has both `List.ItemID` and `List.ParentItemID`; the parent ID identifies the inherited item being overridden. A new item commonly uses `List.ListAction="Append"` plus a new `List.ItemID` and no parent ID.

Follow these rules:

1. Create or append list items through the Attribute Editor whenever possible.
2. Keep every direct child `List.ItemID` unique within its containing `<list>`.
3. Do not copy an item ID from another list, variant, instance, or mod.
4. Do not add `Append` to an inherited-item override or add `List.ParentItemID` to a genuinely new item.
5. Preserve list order when order affects UI position, action evaluation, production, or requirements.

The same numeric item ID in different lists is not automatically a collision. Validate identity in the containing list, not globally.

## Variants

Variants such as `<variant name="campaign">` can repeat selected root data. If a variant serializes its own `pbgid`, it must match the root PBG ID. A missing variant PBG is not automatically invalid. A property absent from a variant may inherit root/default data; a serialized variant override can replace that inheritance. Inspect the current editor result and repeat a property only when the editor serializes a required variant-specific override.

Do not add a variant merely to make files look uniform.

## References

`instance_reference`, `template_reference`, and `state_tree_node` values may resolve to the official archive instead of the current pack. A static validator can report them as not locally resolved, but that is not an error by itself.

For each changed reference:

- Confirm the full value in the current Attribute Editor or official data.
- Confirm its expected category/template at the receiving property.
- Confirm the `mod` GUID only when it intentionally belongs to another pack.
- Treat an empty reference as intentional only when supported by the parent/property behavior.

A reference carrying the current pack's own `mod` GUID must resolve to a local instance. A reference with no `mod` commonly resolves to official data. A reference with another mod GUID is a declared external dependency.

References that remain unresolved after official inspection are runtime risks, not confirmed APIs.
