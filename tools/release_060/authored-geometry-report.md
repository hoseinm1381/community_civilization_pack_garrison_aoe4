# 0.6.0 authored native geometry route

`authored_geometry_060.py` is a reusable private three-LOD model route for the
qualified 48/46-bone infantry and 73/46-bone villager families. It does not run
Blender, replace gameplay actors, install a generated prototype, or pair the
diagnostic native material with a final body. The existing archer UV-fix
`three-lod-comparison.json` is the 48-bone control. Both retained villager
manual geometry qualifications are 73-bone controls. Their only all-bone
rest exception is `metarig_pelvissocket`, a childless, unskinned leaf with a
measured 0.0013527423 local scalar delta. The route permits that exact leaf
up to 0.0014; every other bone and all active palette/bind records retain
the strict 0.0002 tolerance. This exception does not prove native animation
or equipment visuals.

## Source handoff

The artist must supply a 0.6.0-owned JSON spec with schema
`ccp-060-authored-native-geometry-spec/v1`, and these fields:

```json
{
  "schema": "ccp-060-authored-native-geometry-spec/v1",
  "slug": "spear1",
  "project_key": "a601",
  "skeleton_bones": 48,
  "group_name": "chi_infantry_light_age01",
  "fbx": "E:/.../art/exports/release_060/.../model.fbx",
  "action": "E:/.../art/exports/release_060/.../action.json",
  "albedo": "E:/.../art/exports/release_060/.../albedo.png",
  "authored_snapshot": "F:/.../output/release_060/.../authored-snapshot.json",
  "export_receipt": "F:/.../output/release_060/.../export.json",
  "stock_manifest": "F:/.../output/release_060/.../decoded-static.json",
  "stock_manifest_sha256": "<actual SHA-256>",
  "template_project": "F:/.../staging/release_060/.../Mods/<existing-key>",
  "template_body": "F:/.../staging/release_060/.../Mods/<existing-key>/project/source/art/scenario/garrison/<existing-key>/units/<generated>/body",
  "template_rig_sha256": "<actual SHA-256>",
  "template_rgo_sha256": "<actual SHA-256>",
  "template_rgotemplate_sha256": "<actual SHA-256>"
}
```

The exporter receipt must pin `source_blend`, `source_blend_sha256`,
`fbx_sha256`, `action_sha256`, `albedo_sha256`, and
`authored_snapshot_sha256` (top level or `authored_snapshot.sha256`). The
action must be a neutral matching Garrison
prototype with no overrides or attachments. The authored snapshot uses the
decoded-static JSON skeleton/geometry layout, including three actual authored
LOD positions, triangles, normals, weights, palettes, strides and `lod1` through
`lod3` material names. Each group may include `corner_uvs` as one array of three
UV pairs per triangle and optional `corner_normals` in the same order. With
`corner_uvs`, set `uv_basis` to `native_intended_before_export_preflip`.
Those UVs are the intended final native values: the known export procedure
preflips Blender V and the native burner restores this orientation. Corner data
is expanded into split vertices for comparison, so an edited face UV seam is
measured without confusing neighboring corners. The export receipt ties the
snapshot to the exact FBX; the native comparison uses authored shape, not stock
mesh topology. Stock is used only for skeleton/skin/LOD identity and format.

For the four spear tiers, the donor manifest and actual stock group names are
listed in `art/recipes/release_060/representative-foot-tier-batch.json`.
Use one 0.6.0-owned spec/slug/private project per tier. Villagers use their
respective 73-bone donor and generated body template, with the bounded leaf
exception above disclosed in each comparison receipt.

## Stages after artist handoff

From the Garrison root, with a concrete spec path:

```powershell
python tools/verify_workspace.py --storage-only
python tools/release_060/authored_geometry_060.py prepare --spec <spec.json>
python tools/release_060/authored_geometry_060.py cook --spec <spec.json>
python tools/release_060/authored_geometry_060.py readback --spec <spec.json>
python tools/release_060/authored_geometry_060.py compare --spec <spec.json>
```

`prepare` requires at least three binary FBX Skin and Cluster records before
creating its blank short private project. It copies only the enumerated body
inputs and the four installed native model burn rules. The generated RGO and
three neutral `unit` materials are diagnostic only. `cook` uses the existing
`output/release_020/native-build.lock` first-byte `msvcrt` lock and retains it;
the root owner must grant the shared native cook slot before running this stage.
`readback` verifies the archive, extracts the four model resources, rejects any
actor or RHKA member, and decodes through a private index and empty game root.
`compare` checks the authored three-LOD weighted topology, intended UV corners,
normals, positions, 48/46 or 73/46 ordered rig/bind records, LOD palettes,
strides, and `lod1`/`lod2`/`lod3` names. A qualified geometry still requires
later exact stock RGO preservation and a stock or private albedo-only RRMaterial
pair, followed by separate integration and native match gates.

## Actual offline validation, 2026-10-18

- `python tools/verify_workspace.py --storage-only`: passed; all expected F:
  junction targets resolved.
- `python -m py_compile tools/release_060/authored_geometry_060.py`: passed.
- `python tools/release_060/test_authored_geometry_060.py -v`: nine tests passed.
  They cover the real three-skin villager FBX, unskinned rejection, qualified
  archer and villager rigs, rejection of a skinned or parent socket exception,
  authored shape comparison instead of stock-shape comparison, and a per-corner
  edited UV seam, the actual Archer III native readback, and Archer II v3
  geometry plus albedo material pair admission.
- `python tools/release_060/authored_geometry_060.py prepare --spec output/release_060/authored-geometry/archer3/spec.json`: passed on the actual Archer III v4 export. It verified the artist's authored snapshot, 48/46 donor rig, action/albedo/FBX hashes, FBX's three Skin and 144 Cluster records, and three LOD material names. It created the blank private `a63r` model source and retained `output/release_060/authored-geometry/archer3/prepare.json`.
- `python tools/release_060/authored_geometry_060.py cook --spec output/release_060/authored-geometry/archer3/spec.json`: exit 0 under the shared byte lock; SGA SHA-256 `bb0b29a702f96d3925731c6d4671d22787972a39773c1e7c6d761ba49df61b57`.
- `python tools/release_060/authored_geometry_060.py readback --spec output/release_060/authored-geometry/archer3/spec.json`: archive verification passed for 11 members; four model resources extracted and decoded through the private index. The one `attrib/a63r.rgd` is the blank scaffold descriptor, with no actor or RHKA members.
- `python tools/release_060/authored_geometry_060.py compare --spec output/release_060/authored-geometry/archer3/spec.json`: `authored_three_lod_geometry_qualified`. The three LODs have 1192/525/157 triangles, exact weighted topology, UV corner keys/counts, native palette and material names. Maximum position distance is 0.0009765625 m; maximum UV scalar delta 0.0004844069; maximum normal vector delta 0.0157803. The 48/46 rig's maximum active inverse bind delta is 0.000126213.
- No Blender scene, final material pair, gameplay source, or earlier release
  input was changed by this pipeline work. Import, native appearance and
  motion remain separate gates.

The integration owner should verify the exporter receipt/snapshot against each
new artifact before preparing another tier. Archer III geometry has native
cook/readback qualification; its stock RGO and final RRMaterial pair, gameplay
integration, and in-game appearance remain outstanding.

## Ranged batch continuation

`register_authored_ranged_060.py` pinned six 0.6.0-owned private specs from the
artist exports. Archer II v1 then completed its private native cook and archive
readback. Its 48/46 rig, all material names, and LOD2/3 pass, but LOD1's exact
weighted topology and UV corner identity do not: 196 of 1484 authored
triangles have no compiled counterpart within 1 mm at all three corners. The
source and cooked LOD1 both have 966 unique positions and identical bounds.
This localized the mismatch to 98 quads receiving different FBX/native
diagonals, including stock-body and added-garment faces. The failed
`output/release_060/authored-geometry/archer2/comparison.json` remains evidence;
v1/v2 artist inputs remain untouched. The artist's v3 export physically
triangulated the export mesh before both snapshot and FBX writing. Its fresh
private `a62t` native cook/readback/comparison passed: 1484/522/155 triangles,
exact weighted topology and UV corner identities; maximum position delta
0.0009765625 m, UV scalar delta 0.000487417 and normal vector delta 0.0151691.
Its SGA SHA-256 is `c91e75fb0f2391fe12799c705f564ddf324986ffee7e2467c6065c7f9c3b6aac`.
The old Archer II cook remains a failed diagnostic.

Archer II's separate `v60a2` supported stock variant completed native cook
and `verify_unit_albedo_variant.py` readback. Its report is
`output/release_060/qualification/albedo-variants/v60a2/material-verification.json`:
exactly three LOD `albedoTexture` references changed, all other material chunks
match stock, and its stock RRGeom is byte-identical. The private RGM differs
from stock only by its logical path and the three expected length/header
fields; the private RGO is retained. The v3 geometry and v60a2 variant together
pass read-only pair admission at `art/scenario/garrison/v60a2/body/body.rgm`.

`ranged_media_pairs_060.py` is the final read-only admission gate for six
models. It verifies the exact native RGM/RGO, albedo-only RRMaterial/RRTex,
qualified authored RRGeom, group/material/rig records and variant logical
stem, then writes a compact six-model media input manifest. It does not graft
an archive or alter a gameplay consumer. It will run only after all six
geometry and material receipts pass. The root owner has the native cook slot
while the artist prepares corrected exports.
