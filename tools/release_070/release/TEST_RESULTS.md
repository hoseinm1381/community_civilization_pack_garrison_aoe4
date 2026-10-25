# Focused validation checkpoint — 2026-10-19

Initial interpreter: `C:/Users/RS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` (3.12.14).
Working directory: the active Garrison root. No native match, Blender operation,
native asset cook, package assembly or cleanup was performed by this review.

| Command arguments after interpreter | Result |
| --- | --- |
| `tools/verify_workspace.py --storage-only` | Passed all seven configured junction targets |
| `-m unittest discover -s tools/release_060 -p 'test*.py'` | Ran 56 tests in 11.206 seconds; failed with four import errors |
| `-m unittest discover -s tools/release_061 -p 'test*.py'` | Ran 6 tests; OK |
| `-m unittest discover -s tools/release_070/release -p 'test*.py'` | Ran 10 tests in 0.009 seconds; OK |

The complete historical suite was then rerun with the configured qualified
`E:/Blender5.2/5.2/python/bin/python.exe` (3.13.13):

| Command arguments after Blender Python | Result |
| --- | --- |
| `-m unittest discover -s tools/release_060 -p 'test*.py'` | Ran **93 tests** in 16.906 seconds; **OK** |
| `-m unittest discover -s tools/release_061 -p 'test*.py'` | Ran **6 tests**; **OK** |

The four historical060 import failures are `test_authored_geometry_060` and
`test_media_pairing_060` importing missing `garrison_shared.model_variants`,
`test_compiled_visual_delta_060` importing missing `garrison_shared.rgd`, and
`test_material_components_060` importing missing `garrison_shared.relic_chunky`.
The extension contains `garrison_shared.cp313-win_amd64.pyd` (4,874,752 bytes).
The bundled modules are present; Python 3.12 cannot load this CPython 3.13 binary
and instead sees the leftover `garrison_shared/scar_modules` namespace directory.
The `.py` wrappers delegate to compiled modules. This was an interpreter ABI
mismatch, resolved by using the existing configured Blender Python. No extension,
historical test, freeze or dependency was modified or installed.

The 070 tests check exact allowlist completeness, per-family actor/art coverage,
unsafe and foreign paths, incorrect mounts/identity/CRC/collisions, unlisted byte
deltas, incomplete family evidence, strict semantic version and truthful unrun
native gates. Full real archive verification remains a separate package step.

After combined qualified evidence became available, read-only validation passed
all **46 payloads** and **12 qualification/payload/UV receipts**. UV geometry hashes
match actual payloads; numerical V-flipped UV coverage meets 0.999 for each family.
The focused suite was expanded to **12 tests, all passing**, including the private
070 attachment-list boundary and exact externally observed normal-inventory guard.
Normal frozen preservation is explicitly false due to independently observed
three-path drift; source/art and final archive checks remain separate.

Assembly `v1` succeeded. Verification attempts are preserved: `v1` hit an incorrect
JSON-output assumption after successful unpack; `v2` correctly rejected unpack's
395 generated XML/RDO sidecars as unexpected files; `v3` established that raw
extract requires an explicit selection. The new verifier uses `extract --filter
''` to read every native member without generated sidecars. These are tool
corrections; the assembled SGA remains unchanged. The focused suite now contains
**13 passing tests**, including successful plain-output and failed unpack handling.

Final `verification-v4/receipt.json` passed full raw extraction of **1,243 native
members**, native TOCs, archive identity and exact byte closure. There are five
modified baseline members (four actors and monk SCAR), 41 additions and **1,197
unchanged baseline members**, with no removals. All 46 deltas match the qualified
allowlist. Active source has 403 files; 1,870 prior art and 68 frozen voice files
remain protected. Normal observed inventory contains exactly 522 files.

Strict package `package-v1` passed manifest/version/credits, four unique members,
ZIP CRC and embedded SGA SHA-256. A fresh `inspect_zip` rerun also passed.

- Final ZIP: `output/release_070/release/community_civilization_pack-0.7.0.zip`
- ZIP bytes: `132581536`
- ZIP SHA-256: `d44688715b6116e4cb0d4e1527dc01837d2e13f0dbd4655460d8e62c93a9faeb`
- SGA: `output/release_070/release/assembly-v1/community_civilization_pack.sga`
- SGA SHA-256: `63e148ab21f0f2e157bee99a414b39c53284ceb9584812026cadfa47cc5accd2`
- Package receipt: `output/release_070/release/package-verification-v1.json`

Final focused rerun: **13 tests in 0.014 seconds, OK**. Import, native appearance,
native gameplay and multiplayer are still unrun. No cache cleanup was performed.
