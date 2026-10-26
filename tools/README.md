# Maintained source tools

- `verify_runtime_package.py`: read-only installed-SGA archive-ID and SCAR-source comparison. Requires `--package` and an existing `--runtime` (SGA-V10 reader); never builds, extracts, or downloads. BOM/line-ending differences are normalized. Exit codes: 0 match, 1 source/identity mismatch, 2 unreadable package or invalid arguments. Compiled tuning and native behavior remain separate gates.

- `generate_prematch_precache.py`: regenerates the private EBPS/SBPS loading hook from the current `VietnamMode.rdo`. Run it after deliberate RDO precache changes; it does not allocate identities or restore retired instances.
- `build.ps1`: user-run Content Editor build helper. The project owner controls builds and game tests.

Completed bootstrap, identity-allocation, migration, and description-replacement scripts were retired in cleanup batch 1. Their original contents are in the verified rollback archive described in `../docs/cleanup-stage1.md`. Historical migration records are not the active source inventory.
