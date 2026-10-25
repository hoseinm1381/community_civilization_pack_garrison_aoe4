# 0.6.0 geometry continuation — 2026-10-18

## Boundary and evidence

`tools/verify_workspace.py --storage-only` passed before writes. Work stayed in 060
geometry scripts/tests and 060 authored-geometry/qualification evidence. The
normal edition, active gameplay source, prior releases, and Blender scenes were
not edited. Native cooks use the inherited `release_020/native-build.lock`
first-byte lock; the bindings worker currently owns the next native batch. All source
snapshots and donor manifests were hash-pinned before native preparation.

## Retained comparison findings

- Archer II v3, Archer III v5b, and Spear I–IV v3 remain selected qualified
  geometry; unchanged inputs were not recooked.
- Crossbow III v5b: retained cook/readback comparison initially failed only
  on the appended 24-triangle panel's native 8-bit skin weight normalization.
  The existing panel-only rule verified 59 changed corners within two counts;
  all preexisting body corners, topology, UVs, normals, rig, LOD records and
  material group identities remained checked. New qualified receipt:
  `output/release_060/authored-geometry/crossbow3-v5b/comparison-qualified.json`.
- Archer IV v5b: LOD1 is the same bounded panel rounding (70 corners); LOD2
  fails at four source corner normals at two positions. Their lengths are
  0.1593, 0.1648, 0.1954, 0.6114; native emits unit vectors. Positions,
  topology, weights and UVs match. The original failed receipts remain. Artist
  supplied separate v5c snapshot/FBX changing exactly those four normals.
  Fresh native cook/readback and all three LODs qualified at
  `output/release_060/authored-geometry/archer4-v5c/comparison.json`.
- Crossbow IV v5b: fresh cook/readback found two authored position pairs per
  LOD collapse to single native grid coordinates. Each pair is at most
  0.03586 mm apart. A regression-tested comparison projects only those two
  measured pairs per LOD and still requires complete triangle, weight, UV,
  normal, rig, LOD and material identity proof. Altering a UV corner fails.
  New qualified receipt:
  `output/release_060/authored-geometry/crossbow4-v5b/comparison-qualified.json`.

## Final continuation result

Handcannon IV v5b, MAA III/IV v1, and Repeater IV v1 each pass fresh native
cook/readback/three-LOD comparison at their respective
`output/release_060/authored-geometry/<slug>/comparison.json` paths.
Female villager III v2 and monk IV v1 had one non-unit source normal each;
the artist supplied separate corrected v3/v2 sources. The originals remain
diagnostic evidence. Source preflight now rejects non-unit corner normals.

All eight corrected 73-bone civilians now pass fresh native
cook/readback/three-LOD comparison.
Female I/III/IV and male I–IV receipts are at
`output/release_060/authored-geometry/<slug>-r73/comparison.json`; female II
uses `villager-female2-v2-r73-retry1/comparison.json`. Monk IV uses
`monk4-v2-r73-retry1/comparison.json` and also passes. The previous female II
and monk IV attempts were externally interrupted while their cook receipts
said `running_under_shared_lock`; their partial build evidence is preserved
and was never promoted.

Female MAA III/IV v1 pass fresh native cook/readback/three-LOD comparison
against their exact 48-bone/45-palette donors at
`maa3_female-v1/comparison.json` and `maa4_female-v1/comparison.json`.
Monk III v2 passes against its exact 73-bone/46-palette donor at
`monk3-v2/comparison.json`.

The tug worker v8 FBX and v9 snapshot pass the source contract:
24 native-named groups, 140 ordered bones, eight exact palettes, 24 Skin and
3360 Cluster nodes, with only the three approved 96-triangle basket groups
changed. Its private 140-bone rig and stock RGO were cooked with the shared
byte lock, and the archive passed CRC and fresh decode. Native output retains
140 full bones but emits only 18 groups and one 52-bone palette. In particular,
left/right cargo groups with the same material are merged, e.g. two distinct
328-triangle wheat-base LOD1 groups become one 656-triangle group, and every
compiled group gets the basket mesh name. The exact stock 24-group RGM/RGO
cannot be paired with that RRGeom. The preserved failure is
`output/release_060/authored-geometry/tug-worker-v8/comparison.json` with
status `native_worker_control_incompatible`; no source-defect allowance or
packed patch was used. A new native-authored route that retains 24 groups and
eight palettes would be required before worker geometry qualification.

`python tools/release_060/test_authored_geometry_060.py -q`: 23 tests passed.
`python tools/verify_workspace.py --storage-only` and `python -m py_compile`
for the three geometry helpers passed. These receipts prove source and native
cook/readback geometry only; they do not prove import, appearance, animation,
or native match behavior. Diagnostic materials are excluded from final pairing.
