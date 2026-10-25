# 0.7.0 release tools

Credits: **hosein81 and chilly5**.

This folder assembles qualified payloads over the exact frozen 0.6.1 SGA, reads
back every archive member, then creates the strict four-member 0.7.0 ZIP.
It performs no Blender work, native asset cook, client import or native match.

Run from the Garrison project root with the Python recorded in `workspace.json`.
Historical060/061 tools importing the installed compiled `garrison_shared` must
use its configured `blender_python` (CPython 3.13), rather than bundled CPython
3.12. Release assembly tools in this folder use only the standard library.
Before assembly, the integration owner must finish all four families and write
the combined qualified receipt. Coordinate a single packager; never assemble an
incomplete Wonder or overwrite an earlier attempt. Use fresh immutable labels.

```powershell
& $python tools/verify_workspace.py --storage-only
& $python -m unittest discover -s tools/release_070/release -p 'test*.py'
& $python tools/release_070/release/assemble_release.py --combined '<combined-receipt>' --label v1
& $python tools/release_070/release/verify_release.py --assembly 'F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/release/assembly-v1/assembly.json' --label v4
& $python tools/release_070/release/package_release.py --verification 'F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/release/verification-v4/receipt.json' --label v1
```

The final ZIP lives under external `output/release_070/release` and contains
exactly `garrison.json`, `community_civilization_pack.sga`, `START-HERE.txt`, and
`EVIDENCE.json`. It requires strict version `0.7.0` and the exact credits.
Keep archive-byte qualification separate from all native acceptance gates.

The source guard accepts either frozen 0.6.1 source or the exact qualified source
overlay pinned by `activate_source.py` and its applied receipt. No arbitrary
receipt-listed path is accepted. Compiled archive deltas remain independently
restricted to the combined native payload allowlist.

The normal edition has a separately observed external three-path delta from its
frozen inventory. `external-normal-drift.json` pins the complete observed inventory
and the original freeze hash. Release guards require that exact inventory and
reject further drift. Final evidence explicitly reports frozen normal preservation
as false and observed-inventory preservation as true. The package uses frozen
0.6.1 archive bytes; no normal-edition file is a package input.

See [REBUILD_ROLLBACK.md](REBUILD_ROLLBACK.md),
[NATIVE_TEST_CHECKLIST.md](NATIVE_TEST_CHECKLIST.md), and
[TEST_RESULTS.md](TEST_RESULTS.md).
