# Garrison preparation report — 2026-10-16

Workspace preparation is complete. No new asset or gameplay was added. Content
Editor compilation, Garrison cooking, ZIP creation/import, lobby selection and
native testing were deliberately not performed.

## Editable entry points

- Project directory:
  `E:\age of empires 4 mods\01_Custom_Civilizations\Community_Civilization_pack\Community_civilization_pack_garrison`
- Open `community_civilization_pack.aoe4mod` there for later owner-run Content
  Editor work. Its displayed pack and game-mode name is **Community Civilization Pack**.
- New independent GUID: `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`.
- Package key: `community_civilization_pack`; reserved first version: `0.1.0`.
- Empty Garrison art project:
  `art/garrison_library/Mods/community_civilization_pack/mod-project.json`.
  Physically it is under
  `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\garrison-library`.
- Rules: shared-root `AGENTS.md`. Storage/recovery: `STORAGE.md`. Future integration:
  `docs/GARRISON_WORKFLOW.md`. Current configuration: `workspace.json`.

The old project GUID `a743d7d1-d753-4cf7-8817-e29d8ded7366` belongs to the preserved
normal edition. The installed Garrison 0.1.4 CLI allocated the new GUID; all
existing editor-generated PBG, Reflect object and localization IDs were retained.
The combined Content Editor project remains the sole gameplay authority.

## Changes and preservation evidence

- Seven Windows junctions direct caches, local test dependencies, output, rollback
  storage, the Garrison library, stock cache and staging to the authorized F: root.
  Active gameplay source, editable-art directories, scripts/tests and docs stay E:.
- Copied active source and required Lupa 2.6/Python 3.12 test dependencies only.
  No normal caches, probes, old packages or archives were copied into active input.
- Renamed project/attribute/locale filenames and build target. Rekeyed all owned
  XML/SCAR/localization references, RDO GUID parts, tuning linkage and archive GUID.
  Changed localization row 1001 to the collection name; other locale text is preserved.
- Preserved Vietnam modules/blueprint names, all gameplay, option/default values,
  icons, PBG/Reflect/locale IDs and foreign references. No generic multi-civilization
  selection functionality was introduced.
- Full normal-edition snapshot: **484 files unchanged**, including originals of
  its tools, caches and archives. All **272 protected copied source files** match
  after reversing only approved identity changes. All **47 copied historical docs**
  match unchanged; copied test assertions are unchanged after identity/path adaptation.
- Historical documents intentionally retain old names, GUIDs and paths; they are
  not active regeneration inputs. `docs/editor-identity.json` records current
  identity with source provenance. The old README is retained separately.

## Verification results

| Gate | Result |
| --- | --- |
| External links / storage guards | Seven exact targets verified; missing storage and ordinary-directory fallback rejected by tests |
| Identity / private references | Correct new GUID, 237 instances, 485 English locale rows, valid private references and mode linkage |
| Tuning validator | 237 instances; zero errors, zero warnings; 1,042 external/stock reference values remain informational evidence, unchanged from baseline |
| SCAR and mode-RDO static checks | All 12 checks exit 0; zero errors; 13 inherited warnings match when both editions are scoped to active assets |
| MCP layout | New GUID and English localization resolved, no missing locale CSV, 11 active SCAR modules |
| MCP checks of three identity-edited SCAR files | Zero unknown calls or missing localization references; three inherited calls in the mode remain low-confidence usage-index findings |
| Workspace guard tests | 5/5 pass |
| Original suite with donor path corrected in memory only | 59 tests, two failing weapon-comparison subcases, zero errors/skips; raw exit 1 |
| Copied suite | 64 tests including five new guards; exactly the same two subcase failures, zero errors/skips; raw exit 1 |
| Garrison preparation repeatability | Two consecutive runs leave configuration byte-identical; SHA-256 `81489ae43cb43440937cd00ed2cf5b968da7f34f041eb2cb8360b1b67bb82925` |
| Build helper / PowerShell | Validate-only command passes, all three scripts parse, editor not launched |
| Independent final read-only review | No Critical, Important or Minor findings within preparation scope |
| Editor/cook/package/import/native/multiplayer | Not run; not established by these checks |

The two preserved failing subcases are
`vn_weapon_outpost_handcannon_bambo_alarm_chi` and
`vn_weapon_outpost_handcannon_bambo_chi` in
`test_native_tunneling_and_weapon_data_match_original`. Assertions were not
weakened, skipped or marked expected-failure. They compare the already-existing
normal source against the currently located Real_Vietnam_1 donor. Fixing gameplay
or changing the donor comparison is outside preparation.

The 13 inherited static warnings cover squad-group lifetime/counting, the loader's
PLAYERS contract, a helper/API lookup and table-method definitions. The baseline's
archived `.tools` official files can mask the helper warning if scanned as runtime
source; the recorded comparison uses `assets` in both editions. The MCP flags
`Player_GetEntitiesEGroup`, `UI_MessageBoxHide` and `UI_MessageBoxReset` as low
confidence by usage evidence; all are inherited, unchanged calls. This milestone
adds no engine calls and does not qualify those runtime contracts.

## Commands and evidence

From the editable Garrison directory:

```powershell
$workspace = Get-Content .\workspace.json -Raw | ConvertFrom-Json
& $workspace.python -B .\tools\verify_workspace.py --preservation
& $workspace.python -B -m unittest discover -s tests -p test_workspace.py -q
& $workspace.python -B -m unittest discover -s tests -q
& .\tools\prepare_garrison.ps1 -CheckOnly
& .\tools\build.ps1 -ValidateOnly
```

The full suite command intentionally returns 1 for the two baseline failures.
Do not describe it as all passing. `tools/prepare_garrison.ps1` without CheckOnly
reapplies preparation settings only; it never cooks or packages. The plain build
helper is for a later owner-run Content Editor build.

Audit reproduction (runs offline tests/static validation, writes owned reports):

```powershell
& $workspace.python -B 'F:\aoe_4_temp\Community_civilization_pack_garrison_temp\provenance\run_acceptance.py'
```

This transcript compares the precise known baseline failures and returns 0 only
when there are no additional failures/errors and all 13 static invocations exit 0.
Raw suite results remain visible. Detailed logs/results are under linked
`output/preparation`; compact receipts are retained in `docs/preparation`.
`docs/migration-provenance.json` and `docs/preparation/normal-before.json` retain
identity mapping and the original complete normal-edition hash inventory.

## Remaining gates

Before a future release, follow `GARRISON_WORKFLOW.md`: authorize the asset scope,
preflight/export, fresh cook with Live Reload off, explicit private binding and
resource integration, final archive readback/member comparison, strict manifest
with real hashes, ZIP validation, client import, required lobby selections and a
fresh native match. Test the new GUID's China/Vietnam selection and regressions;
historical solo-selection evidence does not qualify this new edition. No native
or multiplayer readiness is claimed. Keep F: connected and back up its persistent
Garrison recipes and rollback inputs with E: source.
