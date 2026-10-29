# Maintained source tools

- `verify_runtime_package.py`: read-only installed-SGA archive-ID and SCAR-source comparison. Requires `--package` and an existing `--runtime` (SGA-V10 reader); never builds, extracts, or downloads. BOM/line-ending differences are normalized. Exit codes: 0 match, 1 source/identity mismatch, 2 unreadable package or invalid arguments. Compiled tuning and native behavior remain separate gates.

- `generate_prematch_precache.py`: regenerates Vietnam's private EBPS/SBPS roster from editable `vn_*.xml` definitions. Preserves roster gating and does not repopulate the empty unconditional RDO list.
- `build.ps1`: native Content Editor build helper. Uses the documented double-dash BuildApplet options and requires a fresh burn log and nonempty archive. Build output stays under `output/`; this does not install the mod.
- `prepare_normal_distribution.py`: verifies the final native SGA with an explicitly supplied archive utility, compares every packaged SCAR file, reads back the 27 Korean construction repairs, checks Literature/action caps, then creates and CRC-checks the local-play ZIP. See `--help`. No game installation is modified.

Completed bootstrap, identity-allocation, migration, and description-replacement scripts were retired in cleanup batch 1. Their original contents are in the verified rollback archive described in `../docs/cleanup-stage1.md`. Historical migration records are not the active source inventory.
