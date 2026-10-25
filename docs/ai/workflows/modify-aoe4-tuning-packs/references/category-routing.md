# Category routing and analogue search

## Route by owning blueprint

Start from the behavior's owning blueprint, then trace referenced assets. Common categories in the supplied corpus are:

| Category | Instances | Typical role |
| --- | ---: | --- |
| `ebps` | 2,164 | Entity blueprints: units, buildings, resources, projectiles |
| `sbps` | 902 | Squad blueprints and squad-level composition/behavior |
| `upgrade` | 592 | Technologies and upgrade actions/requirements |
| `weapon` | 480 | Damage, targeting, cooldown, range, accuracy |
| `abilities` | 214 | Ability activation, requirements, actions, UI |
| `army` | 28 | Civilization/army setup and starting configuration |
| `racebps` | 2 | Race-level data |

The corpus also contains smaller `ai`, `map_gen`, `menu`, `paint`, `relic_radial_menu`, and `trade_route_tuning` categories. Use the exact template shown by the current Attribute Editor; do not force an uncommon template into a common category.

## Trace the complete behavior chain

Avoid editing the first plausible number. Trace all consumers relevant to the request:

```text
army/race
  -> ebps entity
     -> sbps squad
     -> weapon(s)
     -> abilities
     -> upgrades/requirements
     -> UI locstrings/icons
```

A unit balance request can span entity cost/health, squad composition, multiple age weapons, charge weapons, abilities, technologies, production lists, requirements, AI data, and variants. Identify all affected age and civilization variants before editing.

## Search the corpus efficiently

Use [instance-index.tsv](instance-index.tsv) to find two to four complete analogues matching the same category, template, civilization/age role, parent pattern, and feature. Prefer analogues that are closest to current official data.

Examples:

```powershell
rg -n "unit_knight_4_eng|weapon_knight" references/instance-index.tsv
rg -n "\tweapon\t.*weapon_spearman" references/instance-index.tsv
rg -n "target_type_table|production" references/property-path-index.tsv
```

Use [property-path-index.tsv](property-path-index.tsv) to confirm that a property path and serialized tag type were actually observed. The index's sample values are discovery evidence, not safe values for a new design.

If no close analogue exists, inspect the current Attribute Editor and official parent rather than generalizing from a distant handmade example.

## Route packaged archive contents

| Packaged extension | Meaning for this workflow |
| --- | --- |
| `.rgd` | Compiled tuning data; classify and preserve provenance, but do not treat as editable XML. |
| `.xml` | Potential editable/source metadata; inspect schema and project context before using. |
| `.ucs` | Localization payload; it can corroborate names but not tuning schema. |
| `.scar` | Route match-time behavior to `$aoe4-game-mode-skill`. |
| terrainlayout `.lua` | Route generated-map behavior to `$create-aoe4-skirmish-map`. |
| `.bin`, `.rrtex`, `.events`, `.scenario` | Packaged support data; do not reinterpret as Attribute Editor XML. |

An SGA that contains RGD and no XML can still be a tuning pack. Modification requires an editable project or a new editor-authored implementation from current official evidence.

## Compare before and after

Record the exact owning instance, parent, property path, original value, intended value, affected variants, and downstream references. After editing, diff only editable source. Unexpected broad XML churn usually means the wrong object was cloned, the parent changed, or the editor serialized unrelated data.
