# Vietnamese land units 0.6.0

Implementation follows `docs/RELEASE_060_PLAN.md`. This directory currently holds
preparation, donor tracing, authoring and qualification tools. It does not yet
contain a qualified final integration/build entrypoint.

Run from the Garrison project root with the Python runtime recorded in
`workspace.json`. Every write must pass the project's storage guard. Shared
Blender sessions and native builds must be serialized with the existing claims
and native-build lock.

## Reproducible checks

```powershell
& $python tools/verify_workspace.py --storage-only
& $python tools/release_060/verify_preparation.py
& $python tools/release_060/baseline.py
& $python -m unittest discover -s tools/release_060 -p 'test_*.py'
```

Set `$python` to the actual bundled Python executable before running these
commands. `baseline.py` only evaluates available final ZIP candidates and writes
readiness evidence; when a final freeze exists, it verifies that owned snapshot.
It does not establish native acceptance or integrate resources. Diagnostic ZIPs
are refused. `pin_final053.py` froze the user-finalized 0.5.3 ZIP, SGA, all 314
source files and SHA-256 values for all 811 archive members. Re-running it verifies
the existing freeze. See `output/release_060/baseline/final053/freeze.json`.

`prepare.py` creates the preparation snapshot once and preserves an existing
freeze. Its snapshot is not the final landmark-release baseline. Do not refresh
it to hide concurrent changes. `verify_preparation.py` reports drift for explicit
attribution; it never restores older files over current work.

## Artifact ownership

- Editable art: `art/authoring/release_060`.
- Export inputs: `art/exports/release_060`.
- Recipes and historical evidence: `art/recipes/release_060`.
- Reports, decoded references, qualification and previews:
  `output/release_060` (project-managed junction to F:).
- Frozen preparation source: external `staging/release_060/preparation-source`.

`inventory/land_units.json` and its official supplement distinguish reachable
units, excluded/candidate records, and unresolved references. Attachment lists,
body geometry and equipment have separate donor receipts. Cache identities
include source archive/member information; existence alone is not validation.

## Qualification boundaries

Blender imports and rendered previews are authoring evidence. A source FBX export
is not a native cook. Installed Garrison Build Unit prototypes do not establish
support for every decoded stock rig. Preserve stronger geometry drafts while
testing compatible private material variants and supported equipment routes.

The Rattan switch is a separate native qualification gate. Preserve the existing
six-entity eligibility and +1 ranged armor behavior. No conversion-based visual
switch, replacement squad, or new public gameplay interface is authorized.

Obtain representative sample approval before expanding the style. The final
0.5.3 baseline is now pinned separately from preparation. Its three compiled
landmark material fixes and compiled villager stealth update must be preserved;
source alone does not reproduce the material changes. Apply only expected-value
visual deltas and compare every unrelated archive member with that baseline.
The final-source reconciliation records the sole authorized source change from
preparation, leaving the other 313 assets byte-identical.

## User priority: roster completion and gameplay-distance review

Use Blender MCP, AoE4 MCP and file/CLI tools for this task. The user requests
working without computer use; do not operate browser/native UI for review or
testing. Deliver review artifacts directly and keep unsupported native outcomes
explicitly unverified.

Use stock AoE4 detail levels and judge representative designs at normal gameplay
distance. Accept minor cosmetic imperfections. Fix noticeable silhouette,
equipment, animation, player-color or LOD problems; stop small Archer refinements.
Reuse qualified routes, complete the seven representative designs for approval,
then extend the approved style across the complete obtainable land roster and
build 0.6.0 from the pinned final 0.5.3 baseline. Do not expand approval gates to
minor details. Imperial Officials are user-confirmed unavailable and excluded;
preserve their unused source records.

The user confirms Worker Elephants have no rider. Both local
`vn_unit_war_elephant_1_vit` and `vn_unit_war_elephant_2_vit` squads use
`screen_name=2023` (Worker Elephant) and `workerelephanticon`; their inherited
blueprint names do not make them combat-elephant designs. Their private visual
must be riderless, with work equipment and native behavior preserved. The stock
combined elephant/mahout pilot is a donor reference, not the finished worker
appearance. The handcannon elephant remains a separate crewed combat family.

## Rollback and preservation

No active gameplay integration has been performed by these preparation tools.
Earlier releases, the normal edition and the other AI's source remain the
rollback/reference inputs. Do not copy the preparation snapshot wholesale into
the active source: it predates concurrent landmark work.

Before final integration, retain the chosen final-baseline ZIP/SGA and an exact
source snapshot. The future integration receipt must enumerate each changed
source/resource with before/after hashes so an inverse change can refuse later
edits rather than overwrite them. Native installation/import remains a separate
user gate. Do not delete diagnostic or authoring files as part of rollback.

After a verified 0.6.0 package, clean only proven regenerable 0.6.0 caches and
recheck deliverable hashes. Current unfinished qualification outputs are retained.
