# Asset and unit workflows

Use this reference for Garrison's **Game Library**, **Create / Encode Asset**, **Mod Project visual resources**, and **Rig & Animation** panels. Initial evidence used Blender 5.2.2/Garrison 0.1.0 on 2026-10-09; installed 0.1.4 guide details were reconciled on 2026-10-11 without new asset builds or native tests. Recheck current panels/guide after updates.

For the 0.1.3 Tuareg workflow—stock weighted anatomy, fitted cloth, unique atlases, native sockets, all-age/private attachment integration, fresh archive proof and cook failures—read [Custom asset integration](asset-integration.md). Earlier custom art loaded in user-run matches; refined.1 passed builds/readback and awaits native visual acceptance.

## Find and decode game assets

- **AoE Assets → Game Library** searches the installed game's objects and models, including unit, building, prop, texture, and geometry resources. Choose a result to decode it into ordinary Blender meshes, materials, and textures at the 3D cursor. A whole unit can include a deform skeleton, skinned meshes, three LODs, and Pose Controls. Stock animation owners and offered clips can be inspected or previewed when a binding exists.
- Decoded parts are editable copies. Deleting, sculpting, moving, or repainting them does not alter installed game files. A static remix exports the pose and geometry left in Blender; it does not retain the unit's rig or animations.
- Search **Objects** for a whole unit and **Models** for loose model resources. Whole-unit decoding includes primary plus hidden lower LODs and, where available, a second Pose Controls armature. A mesh/rig does not require animation binding; **Imported Model -> Animation -> Search Stock Owners Again** can discover offered owners after an initially unbound import.
- **New Model Variant** is different from a remix: it changes selected material texture/parameter slots of a stock model while keeping the stock mesh, skeleton, and animations. The consuming attachment or blueprint must point to the variant.
- To replace an existing game's visuals in ordinary play, its blueprint and attachment references must be changed separately. The inspected guide says there is no general Blender button that performs arbitrary stock visual replacement.

## Make a static model

1. In **Create / Encode Asset → 1 Asset**, select the intended visible mesh objects, set a name and optional identity, and Create / Update Asset. The asset becomes a named Garrison collection; multiple selected meshes may remain separate and editable. Clear the current Container when making a *new* asset; leaving it selected updates that asset.
2. Check Meshes/Check Asset. Blocking findings include missing UV maps or materials in used slots, missing source images, mirrored scale, and invalid closed-surface orientation. Open surfaces such as cloth can be warnings. A deliberately inward-facing closed surface can be marked accordingly. The check reports findings and does not repair meshes.
3. In **2 Material**, Adopt a simple Principled BSDF's base colour, normal, roughness, and metalness from values or images. Refresh after editing its sources. Use Bake for layered/procedural/decoded game shaders that Adopt cannot read. Bake works on private copies and applies only when all required texture outputs complete. Blender Viewport Display colour is not the Principled Base Color used for export. Preserve intended UVs and texture colour spaces.
4. In **3 Build**, Add Asset to Mod. Check its generated name and parts, then cook the Mod Project. The game draws one material per entity; a multi-material model becomes multiple mesh/blueprint parts sharing an origin. A script or consuming blueprint must place or reference all needed parts. The player-colour setting on a decoded model is a preview; baking it into albedo does not produce a dynamic team-colour mask.

The separate **Build This Asset Alone** and preparation controls exist in the installed panel, but do not substitute their result for adding, cooking, packaging, and testing the intended mod.

Check Asset/Add Asset can bake still-unadopted materials before continuing. A manual row Bake or **Bake Unadopted** provides explicit resolution/preview control. Static source units are Blender metres; place the intended ground/grip origin correctly and review scale in game. Thin planes can disappear from the back: supply intentional thickness/two-sided geometry where needed, rather than treating an open-surface warning as a game-rendering guarantee. For neutral static remixes set decoded Player Colour preview strength to zero before baking.

## Buildings and attachments

- **Use as Building** chooses a base construction profile and inherited gameplay/footprint. The guide qualifies English House construction and healthy geometry; English Barracks is experimental. Assign every mesh an explicit **First visible** construction stage; parts from earlier stages remain visible later. At least one part must begin at 0%. One shared atlas material is the documented house route.
- **Build Building → Available through: Map or script** creates a private entity for placement. **Existing build command** replaces one stock builder command after selecting its builder squad and command. It preserves the inherited command structure and does not create a new menu slot, icon, prerequisite, or gameplay family. Custom damage/destroyed geometry is unqualified. Test placement, all construction stages, the completed appearance, and inherited gameplay in a match.
- A prototype unit may replace selected weapon attachment models. Make a complete weapon as one Garrison model part with its grip at the correct origin; inspect the stock weapon's orientation. Each combat slot is independent: ordinary weapon, charge, brace/spearwall, and torch may use different attachments. No automatic socket-fitting or offset editor is supplied. Statistics and attachment rules remain inherited.

For a prototype attachment, use **Replace -> Choose Model from Mod** in each relevant slot; **Inherited** restores that slot, retaining the reusable model. Rebuild Unit/Cook/Package after choices change. For buildings, reload **Load Build Commands** after changing the builder squad. Stage-name prefixes are selection aids only: explicit First visible properties control construction. The guide's Cow House and weapon acceptance are particular fixtures; their exact part counts/material settings are not generic requirements.

## Animated unit route and limits

The documented route is **Game Prototype → Fit Character → Retarget Motion or Edit Actions → Animation Replacements → Build Unit → Cook → Package**.

- Read [Animation contracts and qualification](animations.md) for the inspected prototype catalogue, exact supported slots, character fitting versus motion import, timing rules, exporter refusals, documented example acceptance and the pending native test workflow. Authoring or previewing an Action does not establish a supported gameplay replacement.
- **Build Unit** uses one bound mesh, one material/UV atlas, and required albedo PNG. Optional source PNGs are normal, roughness, metalness, and pattern. Pattern red is owner-colour mask, green skin, blue hair; it is not an arbitrary player-ID palette. A decoded game's packed normal/PBR image is not interchangeable with these source maps. The build generates a private entity/squad and a three-LOD skinned model. It does **not** add a production-menu command.
- When spawning a generated unit through a map/mode script, that consumer must reference it and arrange loading-phase precache; selecting the Tuning Pack alone does not verify the script consumer. Model-only replacement can instead consume the cooked model through an existing unit's private attachments, without a new generated-unit consumer. Rebuilds can replace generated sources only when their expected originals are unchanged; preserve editable `.blend` and Action files.
- In-game checks should cover two player colours for a pattern mask, idle/walk transitions, all replaced weapon states, LODs, scale, animation contact, and death/respawn where relevant. The guide's examples qualify particular fixtures, not every humanoid or model.

### Unit texture inputs and defaults

Reconciled directly with installed `guide/rig-and-animation.html` on 2026-10-11. Under **Build Unit -> Optional Texture Maps**, choose source PNGs explicitly; the unit builder does not infer inputs from Blender nodes or static-asset material adoption. Save painted images before validation. Each supplied file is checked/copied; missing or damaged inputs are refused rather than silently replaced.

| Field | Source input | When blank |
|---|---|---|
| Albedo PNG | Surface colour using the unit's UV layout | Required |
| Normal PNG | Tangent-space RGB normal | Flat normal `(128, 128, 255)` |
| Roughness PNG | Grayscale: black smooth, white rough | `190/255` |
| Metalness PNG | Grayscale: black non-metal, white metal | Black |
| Pattern PNG | Red owner-colour mask, green skin mask, blue hair mask | No pattern map |

Essence packs normal/PBR channels during cook; decoded packed game PNGs are not these source maps. Preview normal/roughness/metalness/pattern as data rather than colour. Keep one material/UV atlas over the whole unit. For a player-coloured shirt, use white in pattern red where owner colour should appear and black over skin, numbers, badges and trim; leave green/blue black when no skin/hair mask is intended. Check mask edges with two owners in game.

Older albedo-only scenes keep neutral defaults. Clearing a field and rebuilding removes that generated map and restores its default without changing original PNGs or Blender materials. Cook/readback establishes resource generation; new texture combinations still need game review.

## Other visual resources

- **Mod Project → Blueprints** can derive an entity, squad, ability, or attachment blueprint from stock and set fields/text, add/remove list entries, or copy a field/table from another stock blueprint. `@name` references a resource in the same Garrison mod. A CSV table can generate many related blueprints from one recipe.
- **Model variants** repaint stock models without geometry changes. **Lights** author named coloured effect-light resources for scripted use; the guide does not offer arbitrary continuous runtime RGB/intensity changes. **Icons and files** packages custom icons or loose resources at their stated archive paths.

### Blueprint and CSV recipes

**New from it** creates a named mod recipe. When a stock blueprint has been copied exactly once, Garrison rewires references to that copy, such as a derived squad/entity/body-list trio. Verify compiled consumers after cook; this rule does not replace deliberate integration into an existing civilization.

`Set` edits scalar fields, `Text` sets player-facing names/tooltips, **Add to list** appends entries, **Remove** removes a field/table, and **Copy from stock** imports a field/table from another stock blueprint. Stock field paths omit the variant prefix (`health_ext/hitpoints`, not `default/health_ext/hitpoints`). Cook rebuilds full stock files from the installed game, applies changes across base/expansion/campaign variants and reports stock-value drift after patches.

Derived-blueprint values beginning `@name` resolve a mod-owned blueprint/model variant. Models, variants, blueprints, lights and units must not collide by name; an entity/squad pair may share a name. **Stock blueprint Set does not expand `@name`**: use full `<owner>:<resource>` strings. The footballer fixture reads project `mod_id`, strips UUID hyphens for its 32-character owner, then records one animator and four tier-body references. Inspect actual target fields and owner before copying those English-villager edits.

For row-generated variants, select a derived recipe, choose **Rows -> Use** with a CSV containing `name` plus columns named by field paths. Each row produces its own named blueprint; the original becomes the shared recipe rather than a separate generated blueprint. Empty cells retain recipe values and derived `@name` references still work. Garrison copies the CSV to `tables/<name>.csv` in the mod folder: edit that copy and cook again. The X removes table use and restores the single blueprint. Do not assume every blueprint family or arbitrary CSV schema is qualified; check current validation.

Model variants accept texture images or stock `.rrtex` paths and numeric parameter slots, retaining mesh/skeleton/animations. The guide's ram example uses `maskTex5` and `secondaryMaskStrength567`; these are that model's slots, not universal material fields. Authored light flicker is bounded 0-0.25, with zero steady; rebuild for changes. [Runtime contracts](runtime-contracts.md) separates effect followers from native Point control.

**Add Icon** gives the native icon reference for UI blueprint fields. **Files** preserves relative paths exactly, so a file such as `ui/hud/pages/cardinalhudpage.xaml` can override that native resource; confirm the intended scope. UI images/fonts use [Scenario tools](scenario-tools.md), while covers/minimaps have separate [packaging rules](packaging-and-catalog.md).

## Installed guide chapters

Open `guide/editor-tour.html`, `guide/look-inside-a-unit.html`, `guide/make-an-asset.html`, `guide/remix-a-game-model.html`, `guide/rig-and-animation.html`, `guide/mod-project.html`, and `guide/new-units-and-maps.html` beside the current extension's `blender_manifest.toml`. The bundled guide is the primary detail source; Blender's official manual covers the underlying modeling, UV, shader, and weight-paint operations.
