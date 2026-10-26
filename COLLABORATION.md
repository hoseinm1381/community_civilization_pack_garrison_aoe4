# Shared development handoff

## Current policy: one active workspace, 2026-10-26

This existing E: Garrison folder is now the active Git checkout on main. Make
changes and commit here; do not create per-version workspaces or mirror the
current milestone into F:. The F: repository retains historical Git objects
used by this checkout and must stay available. See AGENTS.md and
docs/PERSIA_GARRISON.md for the current 0.9.0 port and manual-push boundary.
Use tools/current_sync.py for the compact current delta. The older milestone
instructions below are historical and do not override this policy.

Continue editing this original workspace. The contributor/GitHub checkout is:

`F:\aoe_4_temp\community_civilization_pack_garrison_aoe4`

It contains readable source/tools/tests, current contributor and AI guides, and
lossless hash-indexed development data for 0.8.4. Its `docs/DEVELOPMENT.md` and
`docs/DISCOVERIES.md` explain tool installation, selective restore, exact package
reproduction, compiled-only owning-resource preservation and native acceptance limits.
Installed CUDA/Python/model caches are local dependencies, not shared mod source.

At a future milestone, explicitly request a handoff update. The incremental exporter
is `tools/collaboration/milestone.py`; consult the checkout's `docs/MILESTONE_SYNC.md`.
It adds new chunks/indexes and refuses unreviewed contributor edits. Do not overwrite
published packs, refresh historical freezes, mirror with deletion, or auto-push.

The selected 0.8.4 cache cleanup has an exact inventory and durable operation journal
under the external `consolidation_084_collaboration` directory. It does not authorize
deleting the remaining external root, installed voice runtime/models, editable art,
voice masters, current deliveries, diagnostics or recovery stores. Deleted final and
0.8.3 verification readbacks are regenerated from their retained SGA with the installed
archive tool, or restored from the shared data index. Current integration dependencies
and voice masters remain available in the original workspace.

No synchronization automation, new paid request, installation or publication was
created. Push readiness is reported separately; the shared checkout includes a
preview-first batch push script for its large initial data transfer.


## 0.8.5 owner boundary

Do not read or modify the contributor/GitHub checkout now: it is being size
reduced independently. No 0.8.5 synchronization or push is authorized. The owner
authorized an additional reduction of this original workspace; its independent
local recovery bundles and restore commands are documented in
`docs/DEVELOPMENT_085.md`. They do not depend on contributor data packs.


## 0.8.8 explicitly requested compact update

The owner authorized a minimum-size GitHub-folder update for the two 088 fixes.
Use its tools/compact/portable.py and docs/compact/UPDATE_088.md. Prior immutable
indexes and all 172 old packs remain; the new input pack is only 158,426 bytes.
Future updates must retain the compact policy rather than using the historical
full-history exporter. Push is left to the owner.
