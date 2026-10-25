# Garrison 0.8.5

Current package: `output/release_085/final-v2/community_civilization_pack-0.8.5.zip`.

- ZIP: **284,922,956 bytes**, below 400,000,000 bytes.
- ZIP SHA-256: `241a74a32dc6d9299614fbf30bc2111751947fc3a9144215c955fdfd73017749`.
- SGA SHA-256: `8a89cca8b9854a766baa9249171107b94f45e3f1dfcced9a776a66243c243d6b`.
- Stable GUID, bundle and runtime archive namespace retained.
- Exactly one changed existing member: `scar/vietnam/voices_084.scar`.
- All 11,973 members/mounts verified by fresh extraction. No additions or deletions. Every audio/art/attribute/gameplay member is byte-identical to 0.8.4.

Selection/order/activity replies share a five-second successful-playback gate.
Movement, sailing and generic/default acknowledgements wait eight seconds.
Under-attack dialogue waits fifteen seconds. Command/activity correlation survives
travel and queued delays; it suppresses movement toward a build/gather/attack and
the resulting duplicate activity reply. Pain/death media and existing effort
scheduling are unchanged. No voice generation or download was performed.

## Verification

112 inherited voice tests and 23 new dispatcher/storage tests passed. SCAR static
validation has zero errors; eight warnings concern existing Garrison methods,
loader/PLAYERS context, squad-event removal and group lifetime. Existing APIs and
imports were retained; no new engine call was introduced. MCP reported no
low-confidence APIs or missing localization. The skill self-test passed.

Archive namespace checked before and after one-member assembly; fresh member
hashes/mounts, ZIP CRC/exact members/manifest and embedded SGA hashes passed.
This is a SCAR overlay on the accepted owning archive, not a new native compile.
Import, audible response timing/quality, right-click command classification,
save/load and multiplayer remain independent acceptance gates. 084 pronunciation
exceptions and stock effort timing/female fallback limitations are unchanged.

## Storage and continuation

See `docs/DEVELOPMENT_085.md` for local lossless bundles and selective restoration.
The contributor/GitHub folder is excluded from this work at the owner's request;
no milestone sync or push was performed. Cleanup is complete; exact byte/allocation counts and operation journals are
recorded in `consolidation_085/summary.json`.

The earlier `final-v1` candidate exposed a delayed build/activity echo during
independent review. The corrected final-v2 passed new delayed build/gather and
generic acknowledgement regressions (observed failing before the fix). Runtime
streamed restoration also passed an observed failing-then-passing bounded-memory
regression. Use final-v2 for delivery.

## Completed storage result

The measured external folder fell from **72.14 GB to 33.29 GB of allocated file
space**, a net reduction of **38.85 GB**. Logical file contents fell from
33.93 GB to 29.24 GB. Totals include the new recovery bundles, both 085 candidate
packages and compact evidence; empty-directory allocation is additional and
excluded from these conservative file-allocation figures. Drive free-space
changes were not used as proof because another project was working on F:.

Independent lossless bundles retain 117,960 voice development files, 34,562
installed voice-tool/model files, and 7,347 historical development files. Their
combined ZIP size is 18.53 GB. Original editable masters and paid recordings
remain recoverable; current gameplay uses the original compressed Ogg media.
No voice regeneration, new download, installation, native compilation,
publication, paid request or GitHub modification was performed. The contributor
reader was stopped when the owner prohibited further access; no indexed-store
retirement occurred. Current recovery depends only on local bundles.

Post-cleanup: all seven links passed; 7,846 frozen protected files were unchanged
and the one previously approved editable buffalo deviation was retained, with
zero preservation errors. Final ZIP CRC, manifest version, namespace and embedded
SGA hashes passed again after retirement. The 112 inherited voice tests passed
with the compact working set. Native import/audible/save/load/multiplayer tests
remain pending.
