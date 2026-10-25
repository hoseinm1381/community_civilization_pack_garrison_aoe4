# Vietnamese 0.7.0 — Imperial architecture and monk repair

Credits: **hosein81 and chilly5**.

Implementation is in progress. This report does not yet identify a verified
delivery ZIP. The exact immutable input is final 0.6.1 SGA
`9e797ab14faf293ec1570c6dc38f1e7cab2ffda9df7d5078b7a0ecf564233c85`.

## Architecture and editable sources

The user approved all four blockouts for detailed production. The current full
editable scene is `art/authoring/buildings_070/architecture-final-r3.blend`.
Its source manifest is `output/release_070/art/final-source-manifest.json`.
Earlier blockouts, detail revisions, exports and failed cooks remain available.

| Asset | Qualified source collection | Final export folder | Healthy new triangles |
| --- | --- | --- | ---: |
| Imperial Garden | `CCP070_Imperial_Garden_Detailed_r4` | `garden-r5` | 32,066 |
| Trung Foundaries | `CCP070_Trung_Foundries_Detailed_r3` | `foundry` | 19,784 |
| Wonder | `CCP070_Kinh_Thien_Detailed_r3` | `wonder` | 54,728 |
| University additions | `CCP070_University_Detailed_Overlay_r6` | `university-r6` | 4,996 |

Export folders are under `art/exports/buildings_070`. University retains the
exact native main model and its layered materials; the additions replace one
small decorative water pot in its private stamp. The four imported stock mesh
groups have exact original vertex positions. No stock main roof is reexported.
The final remix is the scholarly court, gate, steles, benches and reading table;
the earlier isolated roof strips and intersecting joinery were rejected.
The approximate 50% ceiling is a qualitative visual limit, not a mesh statistic.

Each model has seven distinct lifecycle parts, with healthy parts 0/1/4/5/6,
heavy damage 0/3, and ruins 2. Original native animation owners, functional
markers and stamp transforms are retained; the University addition has zero
duplicate native markers. Static selector evaluation is not repair/rebuild
or destruction proof in a native match.

The Garden pond and Foundry pits are real mesh recesses within raised solid
bases. Their floors remain above unmodified terrain. No terrain excavation or
footprint change is introduced. Tile pans and roof ornaments were seated against
their actual supporting surfaces and independently read back. Source UVs,
finite coordinates, nonzero face areas and measured stock triangle budgets pass.

## History and interpretation

The research inventory is
`tools/release_070/inventory/architecture_and_historical_findings.md`, with
downloaded reference receipts under `output/release_070/inventory/references`.

- The Wonder uses the surviving [Kính Thiên platform and dragon stairs](https://hoangthanhthanglong.vn/dien-kinh-thien/)
  as its measured anchor. Its lost timber superstructure is an interpretation
  informed by a modern reconstruction model, not a claimed surviving Lê palace.
- The Garden draws on [documented Thăng Long lotus ponds and royal gardens](https://hoangthanhthanglong.vn/ho-sen-trong-hoang-thanh-thang-long-qua-tu-lieu-lich-su-va-khao-co-hoc/).
  Its elephant-service yard layout is plausible reconstruction for the existing
  production function, rather than an excavated historical plan.
- The Foundry is a reconstructed workshop arrangement with period cannon,
  furnace mouths, casting recesses, tiled workshops and a separate store.
- University references Văn Miếu–Quốc Tử Giám. The 1805 Khuê Văn pavilion and
  later additions are excluded; the gate is a restrained interpretation.

## Monk and voice preparation

The screenshot showed a loading/precache placeholder. The minimal repair adds
the actual private monk EBPS and SBPS IDs to the existing loading-time precache
hook. The isolated candidate changes one SCAR member and preserves 1,201 other
0.6.1 members byte for byte. No monk mesh, animation or ability is replaced.
Native idle, movement, healing, conversion and relic actions still need testing.

Voice preparation is now `0.8.0`. Eight text/path/version files were relabelled;
authored lines, scripts, original receipts and previously reported preservation
drift are retained. The original dossier is archived losslessly under
`output/release_070/voices`. No audio was produced or integrated.

## Explicit rendering and proof limits

The supported seven-part object-PBR route produces one native LOD, matching the
measured owners' per-mesh LOD structure. Editable lower-detail alternatives are
included in `*_LOD1_AUTHORING_ONLY` and `*_LOD2_AUTHORING_ONLY` collections;
native camera-distance switching is not qualified or claimed. The retained
University native body owns its original rendering behavior independently.

New building bodies use neutral albedo and have no qualified dynamic owner mask
in this supported cook route. Existing native outskirts banners/decorations and
the University's original layered owner material remain. Two-player-colour
appearance must be checked in game. Source material screenshots are Blender
previews; University's stock body is a neutral placeholder in those screenshots.

Keep source checks, art review, fresh native cook/readback, package verification,
Garrison import, native appearance/gameplay and multiplayer as separate gates.
No native import or match proof is claimed. Use the release native checklist.
