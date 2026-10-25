# 0.6.0 authored geometry pause checkpoint — 2026-10-18

Pause requested by user. No job or cook remains running from this worker; no
PID to resume or stop. The shared `F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_020/native-build.lock`
first-byte lock was released after each completed cook. No Blender claim is held.
Do not start further work until the user resumes.

## Completed evidence

- Archer II approved visible art: explicit-triangle v3 export at
  `art/exports/release_060/ranged_roster/archer2/v3`. Fresh private `a62t`
  cook/readback and all three authored LODs passed at
  `output/release_060/authored-geometry/archer2-v3/comparison.json`.
  Triangles 1484/522/155; archive SHA-256
  `c91e75fb0f2391fe12799c705f564ddf324986ffee7e2467c6065c7f9c3b6aac`.
  Its supported albedo-only private variant `v60a2` passed
  `output/release_060/qualification/albedo-variants/v60a2/material-verification.json`.
  Read-only pair admission passed for final private model path
  `art/scenario/garrison/v60a2/body/body.rgm`, with replacement geometry
  target `art/scenario/garrison/v60a2/body/body.rrgeom`. No final archive graft
  or gameplay binding has occurred.
- Archer II v1/v2 are preserved failed source-snapshot/triangulation diagnostics;
  never promote their geometry cook.
- Archer III v4 private `a63r` geometry cook/readback/comparison passed at
  `output/release_060/authored-geometry/archer3/comparison.json`, archive SHA-256
  `bb0b29a702f96d3925731c6d4671d22787972a39773c1e7c6d761ba49df61b57`.
  Root visual review found a visible front owner-patch sawtooth edge, so this
  art is diagnostic only and must not enter final integration.
- Five non-Archer-II ranged tiers await artist v5 correction/export:
  Archer III/IV, Crossbow III/IV, Handcannoneer IV. Prior v4 exports are
  retained and must not be overwritten or cooked as final art.
- `tools/release_060/authored_geometry_060.py` provides guarded
  prepare/cook/readback/compare; `ranged_media_pairs_060.py` is the six-model
  read-only final pair gate. `test_authored_geometry_060.py -v` last passed
  9 tests. The detailed report is `tools/release_060/authored-geometry-report.md`.

## Resume commands after user authorization and explicit native cook-slot handoff

From the Garrison root, first run:

```powershell
python tools/verify_workspace.py --storage-only
```

For each **new** v5 tier, pin a fresh attempt spec under
`output/release_060/authored-geometry/<tier>-v5/spec.json` (new private key;
do not reuse v4 projects). Validate the actual v5 export receipt hashes,
stock donor, one atlas, and three Skin/Cluster FBX records. Then, one tier at
a time with the shared native cook slot granted:

```powershell
python tools/release_060/authored_geometry_060.py prepare --spec output/release_060/authored-geometry/<tier>-v5/spec.json
python tools/release_060/authored_geometry_060.py cook --spec output/release_060/authored-geometry/<tier>-v5/spec.json
python tools/release_060/authored_geometry_060.py readback --spec output/release_060/authored-geometry/<tier>-v5/spec.json
python tools/release_060/authored_geometry_060.py compare --spec output/release_060/authored-geometry/<tier>-v5/spec.json
```

For each qualified v5 albedo atlas, run the existing supported
`cook_unit_albedo_variant.py` with a fresh `v60...` key, actual stock logical
model path, v5 `albedo.png`, and its SHA-256; then run
`verify_unit_albedo_variant.py --cook <cook.json> --donor <stock decoded-static.json>`
under Python 3.13. Do not pair neutral diagnostic manual RRMaterial/RGO.
Create an owned six-tier variant map selecting `geometry_slug` and
`material_verification` per canonical tier; run
`python tools/release_060/ranged_media_pairs_060.py --variant-map <map.json>`.
This produces inputs for separate final integration only; no final SGA or active
gameplay edit is authorized by this checkpoint.
