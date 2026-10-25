# Shared development handoff

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
